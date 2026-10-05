"""Validate public slide inputs and assembled artifacts without opening the dataset.

These checks establish packaging and disclosure invariants. They do not substitute
for browser, accessibility, or native PowerPoint visual review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


PRIVATE_PARTS = {".git", ".agents", ".codex", "datasets", "drafts", "facts", "companion"}
PRIVATE_TEXT = re.compile(
    r"\b(?:instructor[ _-]+(?:answers?|solutions?|only|notes?|keys?)|"
    r"answer[ _-]+key|private[ _-]+(?:facts|answers?|solutions?))\b", re.I
)
COMMENT = re.compile(r"<!--(.*?)-->", re.S)
INCLUDE = re.compile(r"\{\{<\s*include\s+[\"']?([^\s>\"']+)[\"']?\s*>\}\}")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\((<?[^\s)>]+>?)")
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
# Exact upstream descriptors observed in the pinned Quarto 1.9.36 distribution.
# Updating Quarto requires reviewing this small vendor metadata allowlist too.
REVEAL_PLUGIN_METADATA = {
    "pdf-export": ("name: PdfExport\nscript: pdfexport.js", ("pdfexport.js",)),
    "quarto-line-highlight": (
        "# adapted from https://github.com/hakimel/reveal.js/tree/master/plugin/highlight\n"
        "name: QuartoLineHighlight\nscript: line-highlight.js\nstylesheet: line-highlight.css",
        ("line-highlight.js", "line-highlight.css")),
    "quarto-support": (
        "name: QuartoSupport\nscript: support.js\nstylesheet: footer.css\nconfig:\n  smaller: false",
        ("support.js", "footer.css")),
    "reveal-menu": (
        'name: RevealMenu\nscript: [menu.js, quarto-menu.js]\nstylesheet: [menu.css, quarto-menu.css]\n'
        'config:\n  menu:\n    side: "left"\n    useTextContentForMissingTitles: true\n'
        '    markers: false\n    loadIcons: false',
        ("menu.js", "quarto-menu.js", "menu.css", "quarto-menu.css")),
}


def load_manifest(path: Path) -> dict:
    """Read JSON-format manifests or YAML configuration without silent overrides."""
    text = path.read_text(encoding="utf-8-sig")

    def unique_mapping(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate key '{key}'")
            result[key] = value
        return result

    # Our manifest is JSON (a strict YAML subset). A broken JSON document must
    # not fall through to YAML and obscure its original location and error.
    if text.lstrip().startswith(("{", "[")):
        try:
            result = json.loads(text, object_pairs_hook=unique_mapping)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}") from exc
    else:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("Install the slide requirements to read YAML manifests.") from exc

        class UniqueLoader(yaml.SafeLoader):
            def construct_mapping(self, node, deep=False):
                keys = set()
                for key_node, _ in node.value:
                    if key_node.tag == "tag:yaml.org,2002:merge":
                        continue
                    key = self.construct_object(key_node, deep=deep)
                    try:
                        if key in keys:
                            mark = key_node.start_mark
                            raise ValueError(f"{path}:{mark.line + 1}:{mark.column + 1}: duplicate key '{key}'")
                        keys.add(key)
                    except TypeError as exc:
                        raise ValueError(f"{path}: mapping keys must be scalar values") from exc
                return super().construct_mapping(node, deep=deep)

        try:
            result = yaml.load(text, Loader=UniqueLoader)
        except yaml.YAMLError as exc:
            raise ValueError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{path}: expected a top-level mapping")
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha256(path: Path) -> str:
    """Review provenance survives Git CRLF/LF conversion across platforms."""
    return hashlib.sha256(path.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()


def safe_path(root: Path, value: str, *, public: bool = False) -> Path:
    """Resolve a manifest path with the same safety rules on Windows and Linux."""
    value = str(value).replace("\\", "/")
    path = PurePosixPath(value)
    if not value or path.is_absolute() or re.match(r"^[a-zA-Z]:", value) or ".." in path.parts:
        raise ValueError(f"Expected a repository-relative path without traversal: {value}")
    if public and any(part.lower() in PRIVATE_PARTS or part.lower().startswith("_instructor")
                      for part in path.parts):
        raise ValueError(f"Private path cannot be a public input: {value}")
    target = (root / Path(*path.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"Input resolves outside the repository: {value}")
    return target


def active_chapters(manifest: dict, *, public_only: bool = False) -> list[dict]:
    states = {"approved"} if public_only else {"pilot", "approved"}
    return [chapter for chapter in manifest.get("chapters", []) if chapter.get("status") in states]


def is_reveal_runtime_metadata(path: Path, output_root: Path) -> bool:
    """Allow only the known Quarto 1.9.36 Reveal plugin descriptors.

    These vendor descriptors travel with runtime JS/CSS. A generic YAML extension
    exception would also publish arbitrary authoring metadata, so both the exact
    runtime location and complete descriptor contents are checked here.
    """
    relative = path.relative_to(output_root).as_posix()
    match = re.fullmatch(r"chapter-\d{2}/index_files/libs/revealjs/plugin/([^/]+)/plugin\.yml", relative)
    if not match or match[1] not in REVEAL_PLUGIN_METADATA:
        return False
    descriptor, resources = REVEAL_PLUGIN_METADATA[match[1]]
    return (path.read_text(encoding="utf-8-sig").strip() == descriptor
            and all((path.parent / name).is_file() for name in resources))


def audit_text(text: str, label: str, *, comments: bool = True) -> list[str]:
    errors = []
    match = PRIVATE_TEXT.search(text)
    if match:
        errors.append(f"{label}: private-material marker '{match.group(0)}'")
    references = INCLUDE.findall(text) + MARKDOWN_LINK.findall(text)
    references += re.findall(r"(?:src|href)\s*=\s*['\"]([^'\"]+)", text)
    for reference in references:
        reference = reference.strip("<>")
        # Remote release links are allowed; local authoring files are not.
        parsed = urlsplit(reference)
        if parsed.scheme in {"http", "https", "mailto", "data"}:
            continue
        if parsed.scheme == "file" or re.match(r"^[a-zA-Z]:[\\/]", reference):
            errors.append(f"{label}: machine-local source reference {reference}")
        parts = unquote(parsed.path).replace("\\", "/").split("/")
        if any(part.lower() in PRIVATE_PARTS for part in parts):
            errors.append(f"{label}: private source reference {reference}")
    # Accept only generated bookkeeping, never a general author comment.
    if comments:
        for match in COMMENT.finditer(text):
            if not re.match(r"^\s*(?:quarto(?:[- :]|$)|generated(?:[- :]|$))", match.group(1), re.I):
                errors.append(f"{label}: unreviewed raw HTML comment")
                break
    return errors


def verify_sources(root: Path, manifest: dict) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    if manifest.get("version") != 1:
        errors.append("Unsupported slide manifest version; expected 1")
    ids: set[str] = set()
    for chapter in manifest.get("chapters", []):
        identifier = chapter.get("id", "")
        if not re.fullmatch(r"chapter-\d{2}", identifier) or identifier in ids:
            errors.append(f"Invalid or duplicate chapter id: {identifier}")
        ids.add(identifier)
        if chapter.get("status") not in {"pilot", "approved", "planned", "draft", "deferred"}:
            errors.append(f"{identifier}: invalid approval status")
    for chapter in active_chapters(manifest):
        identifier = chapter["id"]
        try:
            source = safe_path(root / "slides", chapter["source"], public=True)
        except (KeyError, ValueError) as exc:
            errors.append(f"{identifier}: {exc}")
            continue
        if not source.is_file():
            errors.append(f"Missing slide source: {source}")
            continue
        text = source.read_text(encoding="utf-8-sig")
        errors.extend(audit_text(text, str(source.relative_to(root))))
        for include in INCLUDE.findall(text):
            target = ((root / "slides" / include.lstrip("/")) if include.startswith("/")
                      else source.parent / include).resolve()
            if not target.is_relative_to(root / "slides"):
                errors.append(f"{identifier}: include must use prepared public slide inputs: {include}")
        # Every level-two teaching slide has public narration. Level-one module
        # dividers and the metadata-driven title slide are intentionally exempt.
        for section in re.split(r"(?m)^##\s+", text)[1:]:
            title = section.splitlines()[0]
            section = re.split(r"(?m)^#\s+", section)[0]
            if not re.search(r"^:{3,}\s*\{?\.notes\}?\s*$", section, re.M):
                errors.append(f"{identifier}: teaching slide '{title}' has no public notes")
        hashes = chapter.get("reviewed_source_hashes", {})
        for rel in chapter.get("book_sources", []):
            try:
                path = safe_path(root, rel, public=True)
                if not path.is_file():
                    errors.append(f"{identifier}: missing book review input {rel}")
                elif hashes.get(rel) != source_sha256(path):
                    errors.append(f"{identifier}: editorial review required after change to {rel}")
            except ValueError as exc:
                errors.append(str(exc))
    for field in ("public_assets", "public_fragments"):
        for rel in manifest.get(field, []):
            try:
                path = safe_path(root, rel, public=True)
                if not path.is_file():
                    errors.append(f"Missing {field} input: {rel}")
                elif path.suffix.lower() in {".qmd", ".md", ".txt", ".json", ".svg", ".drawio"}:
                    errors.extend(audit_text(path.read_text(encoding="utf-8-sig"), rel))
            except ValueError as exc:
                errors.append(str(exc))
    return errors


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.notes = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "aside" and "notes" in (values.get("class") or "").split():
            self.notes += 1
        for attr in ("src", "href", "data-src", "data-background-image", "poster"):
            if values.get(attr):
                self.links.append(values[attr])
        if values.get("srcset") and not values["srcset"].startswith("data:"):
            self.links.extend(part.strip().split()[0] for part in values["srcset"].split(",") if part.strip())
        if values.get("style"):
            self.links.extend(css_resources(values["style"]))


def css_resources(text: str) -> list[str]:
    return re.findall(r"url\(\s*['\"]?([^\s)'\"]+)", text)


def verify_local_links(directory: Path, *, book_url: str = "") -> list[str]:
    """Check on-disk HTML/CSS resources; external URLs are not fetched."""
    directory = directory.resolve()
    errors: list[str] = []
    prefix = urlsplit(book_url).path.rstrip("/")
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".html", ".css"}:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() == ".html":
            parser = ResourceParser()
            parser.feed(text)
            links = parser.links
        else:
            links = css_resources(text)
        for link in links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            link_path = unquote(parsed.path).replace("\\", "/")
            if link_path.startswith("/"):
                if prefix and link_path.startswith(prefix + "/"):
                    link_path = link_path[len(prefix):]
                target = directory / link_path.lstrip("/")
            else:
                target = path.parent / link_path
            target = target.resolve()
            if not target.is_relative_to(directory):
                errors.append(f"{path.relative_to(directory)}: resource escapes output tree: {link}")
            elif not target.exists():
                errors.append(f"{path.relative_to(directory)}: missing local resource {link}")
    return errors


def verify_pptx(path: Path, *, expected_notes: int = 1, expected_slides: int | None = None,
                require_table: bool = False, require_media: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            slides = sorted(name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name))
            notes = sorted(name for name in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name))
            if not slides:
                errors.append(f"{path.name}: no slide XML")
            if expected_slides is not None and len(slides) != expected_slides:
                errors.append(f"{path.name}: {len(slides)} slides; expected {expected_slides}. "
                              "Check for unintended slides after tables or figures.")
            texts: list[str] = []
            tables = 0
            meaningful_notes = 0
            for name in slides + notes:
                doc = ET.fromstring(archive.read(name))
                text = " ".join(node.text or "" for node in doc.findall(".//a:t", NS))
                errors.extend(audit_text(text, f"{path.name}:{name}", comments=False))
                if name in slides:
                    texts.append(text)
                    tables += len(doc.findall(".//a:tbl", NS))
                elif len(text.strip()) > 20:
                    meaningful_notes += 1
            if not any(text.strip() for text in texts):
                errors.append(f"{path.name}: no native editable text")
            if meaningful_notes < expected_notes:
                errors.append(f"{path.name}: {meaningful_notes} populated notes; expected at least {expected_notes}")
            if require_table and not tables:
                errors.append(f"{path.name}: financial table is missing as a native editable table")
            if require_media and not any(name.startswith("ppt/media/") for name in names):
                errors.append(f"{path.name}: expected embedded graphics are missing")
            for name in sorted(names):
                if not name.endswith(".rels"):
                    continue
                # foo/_rels/bar.xml.rels describes targets relative to foo/.
                base = posixpath.dirname(posixpath.dirname(name))
                for rel in ET.fromstring(archive.read(name)):
                    target = rel.get("Target", "")
                    if rel.get("TargetMode") == "External":
                        if target.lower().startswith("file:") or re.match(r"^[a-zA-Z]:[\\/]", target):
                            errors.append(f"{path.name}: machine-local PowerPoint hyperlink {target}")
                        continue
                    resolved = posixpath.normpath(posixpath.join(base, unquote(target)))
                    if target.startswith("/"):
                        resolved = target.lstrip("/")
                    if resolved not in names:
                        errors.append(f"{path.name}:{name}: broken package relationship {target}")
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        errors.append(f"Cannot inspect {path}: {exc}")
    return errors


def verify_outputs(root: Path, manifest: dict, site: Path | None = None,
                   build_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    staging = build_root or root / "slides/_build"
    html_root = Path(site) if site else staging / "revealjs"
    deck_root = html_root / "slides" if site else html_root
    pptx_root = deck_root if site else staging / "pptx"
    for chapter in active_chapters(manifest, public_only=site is not None):
        identifier = chapter["id"]
        html_path = deck_root / identifier / "index.html"
        pptx_path = pptx_root / identifier / f"{identifier}.pptx"
        source = safe_path(root / "slides", chapter["source"]).read_text(encoding="utf-8-sig")
        expected_notes = len(re.findall(r"(?m)^:{3,}\s*\{?\.notes\}?\s*$", source))
        if not html_path.is_file():
            errors.append(f"Missing Reveal deck: {html_path}")
        else:
            text = html_path.read_text(encoding="utf-8-sig")
            errors.extend(audit_text(text, str(html_path), comments=False))
            parser = ResourceParser()
            parser.feed(text)
            if parser.notes < expected_notes:
                errors.append(f"{identifier}: Reveal has {parser.notes} notes; expected {expected_notes}")
        if not pptx_path.is_file():
            errors.append(f"Missing PowerPoint deck: {pptx_path}")
        else:
            requirements = chapter.get("artifact_checks", {})
            errors.extend(verify_pptx(pptx_path, expected_notes=expected_notes,
                                      expected_slides=1 + len(re.findall(r'(?m)^#{1,2}\s+', source)),
                                      require_table=requirements.get("native_table", identifier == "chapter-01"),
                                      require_media=requirements.get("embedded_media", True)))
    if html_root.exists():
        errors.extend(verify_local_links(html_root, book_url=manifest.get("book_url", "")))
    if site:
        approved = {item["id"] for item in active_chapters(manifest, public_only=True)}
        if deck_root.exists():
            for directory in deck_root.glob("chapter-*"):
                if directory.is_dir() and directory.name not in approved:
                    errors.append(f"Unapproved or removed deck in assembled site: {directory.name}")
        for path in html_root.rglob("*.html"):
            errors.extend(audit_text(path.read_text(encoding="utf-8-sig"), str(path), comments=False))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--outputs", action="store_true")
    parser.add_argument("--site", type=Path)
    args = parser.parse_args()
    manifest = load_manifest(args.root / "slides/manifest.yml")
    errors = verify_sources(args.root, manifest)
    if args.outputs or args.site:
        errors.extend(verify_outputs(args.root, manifest, site=args.site))
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("Slide packaging checks passed; native/browser visual review remains separate.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
