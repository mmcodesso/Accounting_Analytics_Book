"""Check the slide decks and their rendered artifacts without opening the dataset.

Source checks (no Quarto needed): every cited book figure, table and tutorial exists, every
slide has notes, no deck names the author, and no deck carries private-material wording.
Artifact checks: slide counts, notes and native tables in PowerPoint, local links in Reveal,
and the wording scan of the assembled site. They do not replace looking at the slides.
"""
from __future__ import annotations

import argparse
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
# Everything is public (author's decision, 2026-10-05): the solutions and the instructor notes are release files, and
# the Downloads page lists them by name, so the wording check skips that one page of the assembled site.
SOLUTION_PAGES = {"front-matter/downloads.html"}
COMMENT = re.compile(r"<!--(.*?)-->", re.S)
INCLUDE =re.compile(r"\{\{<\s*include\s+[\"']?([^\s>\"']+)[\"']?\s*>\}\}")
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
    """Read a JSON or YAML configuration file, rejecting duplicate keys instead of silently overriding."""
    text = path.read_text(encoding="utf-8-sig")

    def unique_mapping(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate key '{key}'")
            result[key] = value
        return result

    # JSON is a strict YAML subset. A broken JSON document must not fall
    # through to YAML and obscure its original location and error.
    if text.lstrip().startswith(("{", "[")):
        try:
            result = json.loads(text, object_pairs_hook=unique_mapping)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}") from exc
    else:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("Install the slide requirements (PyYAML) to read YAML files.") from exc

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


def safe_path(root: Path, value: str, *, public: bool = False) -> Path:
    """Resolve a repository path with the same safety rules on Windows and Linux."""
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


def audit_text(text: str, label: str, *, comments: bool = True, markers: bool = True) -> list[str]:
    errors = []
    match = PRIVATE_TEXT.search(text) if markers else None
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


NOTES = re.compile(r"^:{3,}\s*\{?\.notes\}?\s*$", re.M)
SLIDE_HEADING = re.compile(r"^(#{1,2})\s+(.+?)\s*(?:\{[^}]*\})?\s*$", re.M)
AUTHOR_NAME = re.compile(r"\b(?:Codesso|Mauricio)\b", re.I)
CITATION = re.compile(r"\{\{<\s*book-(figure|table|steps|checkpoint)\s+([\w.-]+)")
STEP_RANGE = re.compile(r"\{\{<\s*book-steps\s+([\w.]+)\s+(\d+)-(\d+)\s*>\}\}")
CHECKPOINT_RANGE = re.compile(r"\{\{<\s*book-checkpoint\s+([\w.]+)\s+(\d+)-(\d+)[\s>]")
TABLE_RANGE = re.compile(r"\{\{<\s*book-table\s+([\w-]+)\s+(\d+)-(\d+)[\s>]")
FIGURE_CITE = re.compile(r"\{\{<\s*book-figure\s+([\w-]+)([^>]*)>\}\}")
CROP = re.compile(r'crop\s*=\s*"([^"]*)"')


def parse_crop(text: str) -> tuple[float, float, float, float]:
    """A figure crop as fractions of the figure: left, top, width, height, all inside 0 to 1."""
    try:
        left, top, width, height = (float(part) for part in text.split(","))
    except ValueError as exc:
        raise ValueError(f'crop="{text}" needs four numbers: left, top, width, height') from exc
    if (min(left, top) < 0 or width <= 0 or height <= 0
            or left + width > 1 + 1e-9 or top + height > 1 + 1e-9):
        raise ValueError(f'crop="{text}" must lie inside the figure (fractions from 0 to 1)')
    return left, top, width, height


def crop_key(crop: tuple[float, float, float, float]) -> str:
    """The crop's part of a staged file name, as the shortcode writes it: 0,0,1,0.56 -> 0-0-1-0p56."""
    return "-".join(f"{value:g}".replace(".", "p") for value in crop)


def cited_figures_in(text: str) -> list[tuple[str, tuple[float, float, float, float] | None]]:
    """Each figure a deck cites, with its crop if it has one."""
    found = []
    for identifier, arguments in FIGURE_CITE.findall(text):
        crop = CROP.search(arguments)
        found.append((identifier, parse_crop(crop.group(1)) if crop else None))
    return found


def deck_text(text: str) -> str:
    """The deck without fenced code, so a heading or note inside an example does not count."""
    return re.sub(r"(?ms)^(`{3,}|~{3,}).*?^\1\s*$", "", text)


def slide_headings(text: str) -> list[tuple[int, str]]:
    return [(len(level), title) for level, title in SLIDE_HEADING.findall(deck_text(text))]


def verify_sources(root: Path, decks: list[str], index: dict) -> tuple[list[str], list[str]]:
    """Errors and warnings for every deck source; nothing here depends on chapter text changing."""
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    for deck in decks:
        source = root / "slides" / deck / "index.qmd"
        label = str(source.relative_to(root))
        chapter = index["chapters"].get(deck)
        if chapter is None:
            errors.append(f"{label}: no matching chapter in the book")
            continue
        text = source.read_text(encoding="utf-8-sig")
        errors.extend(audit_text(text, label))
        if text.lstrip().startswith("---"):
            errors.append(f"{label}: decks carry no YAML; the title and footer come from the book")
        if AUTHOR_NAME.search(text):
            errors.append(f"{label}: names the author; slides carry no author name")
        for include in INCLUDE.findall(text):
            target = ((root / "slides" / include.lstrip("/")) if include.startswith("/")
                      else source.parent / include).resolve()
            if not target.is_relative_to(root / "slides"):
                errors.append(f"{label}: include must use the staged slide inputs: {include}")
        try:
            cited_figures_in(text)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
        for kind, identifier in CITATION.findall(text):
            if kind == "figure" and identifier not in index["figures"]:
                errors.append(f"{label}: no figure {identifier} in the book")
            elif kind == "table" and identifier not in index["tables"]:
                errors.append(f"{label}: no table {identifier} in the book")
            elif kind in {"steps", "checkpoint"} and not any(
                    tutorial["id"] == identifier for tutorial in chapter["tutorials"]):
                errors.append(f"{label}: no Guided Tutorial {identifier} in {deck}")
        for identifier, first, last in STEP_RANGE.findall(text):
            numbers = next(({step["number"] for step in tutorial["steps"]}
                            for tutorial in chapter["tutorials"] if tutorial["id"] == identifier), set())
            if numbers and not (int(first) <= int(last) and {int(first), int(last)} <= numbers):
                errors.append(f"{label}: Guided Tutorial {identifier} has no steps {first}-{last}")
        for identifier, first, last in CHECKPOINT_RANGE.findall(text):
            items = next((len(tutorial["checkpoint"]["items"]) for tutorial in chapter["tutorials"]
                          if tutorial["id"] == identifier), 0)
            if items and not 1 <= int(first) <= int(last) <= items:
                errors.append(f"{label}: Guided Tutorial {identifier} has no checkpoint items {first}-{last}")
        for identifier, first, last in TABLE_RANGE.findall(text):
            table = index["tables"].get(identifier)
            if table and not 1 <= int(first) <= int(last) <= len(table["rows"]):
                errors.append(f"{label}: {identifier} has no rows {first}-{last}")
        body = deck_text(text)
        # Every ## slide has notes for the speaker. # module dividers and the title slide are exempt.
        for section in re.split(r"(?m)^##\s+", body)[1:]:
            title = section.splitlines()[0]
            section = re.split(r"(?m)^#\s+", section)[0]
            notes = re.search(r"(?ms)^:{3,}\s*\{?\.notes\}?\s*$(.*?)^:{3,}\s*$", section)
            if not notes:
                errors.append(f"{label}: slide '{title}' has no notes")
            elif len(" ".join(notes.group(1).split())) <= 20:
                errors.append(f"{label}: slide '{title}' has notes too short to be useful")
        sections = {section["title"].casefold() for section in chapter["sections"]}
        for level, title in slide_headings(text):
            if level == 1 and title.casefold() not in sections and not title.startswith("Guided Tutorial"):
                warnings.append(f"{label}: divider '{title}' matches no section of the chapter, so it is not numbered")
    return errors, warnings


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


def verify_outputs(root: Path, decks: list[str], site: Path | None = None,
                   build_root: Path | None = None, book_url: str = "", pptx: bool = True,
                   reveal: bool = True) -> list[str]:
    """Check the rendered decks (staged, or in the assembled site) and the site's pages.

    The PowerPoint files are checked where they are built; they are assets of the revision's release, not part of
    the site, so a site is checked without them, as is a build that renders no PowerPoint (pptx=False). A build of
    the release's files renders no Reveal decks (reveal=False)."""
    errors: list[str] = []
    staging = build_root or root / "slides/_build"
    html_root = Path(site) if site else staging / "revealjs"
    deck_root = html_root / "slides" if site else html_root
    pptx_root = staging / "pptx"
    pptx = pptx and not site
    for deck in decks:
        html_path = deck_root / deck / "index.html"
        pptx_path = pptx_root / deck / f"{deck}.pptx"
        source = (root / "slides" / deck / "index.qmd").read_text(encoding="utf-8-sig")
        body = deck_text(source)
        expected_notes = len(NOTES.findall(body))
        if reveal and not html_path.is_file():
            errors.append(f"Missing Reveal deck: {html_path}")
        elif reveal:
            text = html_path.read_text(encoding="utf-8-sig")
            errors.extend(audit_text(text, str(html_path), comments=False))
            parser = ResourceParser()
            parser.feed(text)
            if parser.notes < expected_notes:
                errors.append(f"{deck}: Reveal has {parser.notes} notes; expected {expected_notes}")
        if pptx and not pptx_path.is_file():
            errors.append(f"Missing PowerPoint deck: {pptx_path}")
        elif pptx:
            errors.extend(verify_pptx(pptx_path, expected_notes=expected_notes,
                                      expected_slides=1 + len(slide_headings(source)),
                                      require_table=bool(re.search(r"book-table|^\|", body, re.M)),
                                      require_media=bool(re.search(r"book-figure|!\[", body))))
    if reveal and html_root.exists():
        errors.extend(verify_local_links(html_root, book_url=book_url))
    if site:
        if deck_root.exists():
            for directory in deck_root.glob("chapter-*"):
                if directory.is_dir() and directory.name not in decks:
                    errors.append(f"Deck in the assembled site has no source: {directory.name}")
        for path in html_root.rglob("*.html"):
            listed = path.relative_to(html_root).as_posix() in SOLUTION_PAGES
            errors.extend(audit_text(path.read_text(encoding="utf-8-sig"), str(path), comments=False, markers=not listed))
    return errors


def main() -> int:
    from scripts.slides import book_index
    from scripts.slides.prepare import deck_ids
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--outputs", action="store_true")
    parser.add_argument("--site", type=Path)
    args = parser.parse_args()
    decks = deck_ids(args.root)
    errors, warnings = verify_sources(args.root, decks, book_index.build(args.root))
    if args.outputs or args.site:
        errors.extend(verify_outputs(args.root, decks, site=args.site))
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("Slide checks passed; looking at the slides remains a separate step.")
    return bool(errors)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    raise SystemExit(main())
