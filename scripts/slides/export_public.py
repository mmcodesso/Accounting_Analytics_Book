"""Create an allowlisted, reviewable source bundle for the manual public transfer.

The output is an overlay for an existing public book checkout, not a new copy of
the entire authoring repository. No copy, commit, push, or deployment is performed
against the public repository by this command.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

try:
    from .verify import (COMMENT, INCLUDE, active_chapters, audit_text, load_manifest,
                         safe_path, sha256, source_sha256, verify_sources)
except ImportError:
    from verify import (COMMENT, INCLUDE, active_chapters, audit_text, load_manifest,
                        safe_path, sha256, source_sha256, verify_sources)


OWNED_DIRECTORIES = ("slides", "scripts/slides", "shared")
DEFAULT_BUILD_FILES = (
    "scripts/build_all.py", "scripts/slides/prepare.py", "scripts/slides/verify.py",
    "scripts/slides/export_public.py", "scripts/slides/requirements.txt",
    "scripts/export_drawio_svgs.py", "visuals/export-manifest.json", "_variables.yml", "LICENSE",
    "visuals/cover/accounting_analytics_cover.drawio", "visuals/cover/cover-web.png",
    "visuals/cover/cover.png", "visuals/cover/cover.pdf", "styles/book-pdf.tex",
)
TEXT_DOCUMENTS = {".qmd", ".md", ".txt"}
STRUCTURED_TEXT = {".py", ".ps1", ".lua", ".yml", ".yaml", ".json", ".csv", ".svg", ".drawio", ".scss"}
# These exact regression modules intentionally contain protected-material marker
# fixtures. They never import private authoring helpers or package private data.
AUDIT_FIXTURES = {"tests/test_slide_build.py", "tests/test_slide_publication.py", "tests/test_slide_public_assets.py"}
MARKDOWN_RESOURCE = re.compile(r"!?\[[^\]]*\]\((<?[^\s)>]+>?)(?:\s+[^)]*)?\)")


def sanitize_public_document(text: str) -> str:
    """Strip raw author comments before copying any public Markdown source."""
    return COMMENT.sub("", text)


def _references(path: Path, text: str) -> list[str]:
    references = INCLUDE.findall(text)
    references += [match.strip("<>").split("#", 1)[0].split("?", 1)[0]
                   for match in MARKDOWN_RESOURCE.findall(text)]
    return [reference for reference in references
            if reference and not re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|#|\{)", reference)]


def _add_document_closure(root: Path, rel: str, files: set[str]) -> None:
    """Follow book includes/assets after comment sanitization, never the private text."""
    path = safe_path(root, rel, public=True)
    if not path.is_file():
        raise ValueError(f"Missing public bundle input: {rel}")
    if rel in files:
        return
    files.add(rel)
    # Public book figures retain the editable authority and their print export.
    if rel.startswith("visuals/svg/") and path.suffix == ".svg":
        for sibling in (f"visuals/src/{path.stem}.drawio", f"visuals/pdf/{path.stem}.pdf"):
            if (root / sibling).is_file():
                _add_document_closure(root, sibling, files)
    if path.suffix.lower() not in TEXT_DOCUMENTS:
        return
    text = sanitize_public_document(path.read_text(encoding="utf-8-sig"))
    for reference in _references(path, text):
        # These are assembled-site artifacts, not source dependencies.
        if reference.startswith(("/downloads/", "/slides/")) and reference not in INCLUDE.findall(text):
            continue
        resolved = ((root / reference.lstrip("/")) if reference.startswith("/") else path.parent / reference).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"{rel}: dependency escapes repository: {reference}")
        dependency = resolved.relative_to(root).as_posix()
        safe_path(root, dependency, public=True)
        # Book links do not mean that the linked chapter is an implementation
        # dependency. Includes and non-page assets must be copied.
        if reference not in INCLUDE.findall(text) and resolved.suffix == ".qmd":
            continue
        if resolved.is_file():
            _add_document_closure(root, dependency, files)
        elif reference in INCLUDE.findall(text) or resolved.suffix not in {".html", ""}:
            raise ValueError(f"{rel}: missing local dependency {reference}")


def _validate_destination(root: Path, destination: Path) -> None:
    outputs = (root / "outputs").resolve()
    if destination == outputs or not destination.is_relative_to(outputs):
        raise ValueError("Public bundles must be in a named directory inside this repository's outputs/.")
    if destination.exists() and any(destination.iterdir()):
        marker = destination / "export-manifest.json"
        if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")).get("bundle_type") != "chapter-slides-overlay":
            raise ValueError(f"Refusing to replace a directory not owned by the exporter: {destination}")
        previous = json.loads(marker.read_text(encoding="utf-8"))
        owned = {entry["path"] for entry in previous.get("files", [])}
        owned.update({"export-manifest.json", "TRANSFER.md"})
        unexpected = [path.relative_to(destination).as_posix() for path in destination.rglob("*")
                      if path.is_file() and path.relative_to(destination).as_posix() not in owned
                      and not ("__pycache__" in path.parts and path.suffix == ".pyc")]
        if unexpected:
            raise ValueError(f"Untracked files in existing export; preserve them before rebuilding: {unexpected}")


def export_public(root: Path, manifest: dict, destination: Path | None = None, *,
                  include_pilot: bool = False, previous_manifest: Path | None = None,
                  public_checkout: Path | None = None) -> Path:
    root = root.resolve()
    destination = (destination or root / "outputs/public-export").resolve()
    _validate_destination(root, destination)
    selected = active_chapters(manifest, public_only=not include_pilot)
    selected_ids = {chapter["id"] for chapter in selected}
    exported_manifest = copy.deepcopy(manifest)
    # Planned inventory is useful in public sources, but pilot sources and their
    # unapproved render registration cannot accidentally enter ordinary releases.
    for chapter in exported_manifest.get("chapters", []):
        if chapter["id"] not in selected_ids and chapter.get("status") in {"pilot", "approved"}:
            chapter["status"] = "draft"
    errors = verify_sources(root, {**manifest, "chapters": selected})
    if errors:
        raise ValueError("Public input validation failed:\n" + "\n".join(errors))
    files: set[str] = set()
    required = ["slides/_quarto.yml", "slides/manifest.yml", *DEFAULT_BUILD_FILES]
    required += manifest.get("public_build_files", [])
    required += manifest.get("public_assets", []) + manifest.get("public_fragments", [])
    required += manifest.get("public_book_files", [])
    for theme in (root / "slides/theme").glob("*"):
        if theme.is_file() and theme.suffix.lower() in {".yml", ".scss", ".pptx"}:
            required.append(theme.relative_to(root).as_posix())
    for chapter in selected:
        required.append("slides/" + chapter["source"])
        required.extend(chapter.get("book_sources", []))
    # Optional package markers have no user-authored state.
    for marker in ("scripts/slides/__init__.py", "shared/__init__.py", "shared/calculations/__init__.py"):
        if (root / marker).exists():
            required.append(marker)
    for rel in sorted(set(required)):
        if rel.startswith("slides/"):
            path = safe_path(root, rel, public=True)
            if not path.is_file():
                raise ValueError(f"Missing public bundle input: {rel}")
            files.add(rel)
        else:
            _add_document_closure(root, rel, files)
    errors = []
    for rel in sorted(files):
        if Path(rel).suffix.lower() in TEXT_DOCUMENTS:
            sanitized = sanitize_public_document((root / rel).read_text(encoding="utf-8-sig"))
            errors.extend(audit_text(sanitized, rel))
        elif Path(rel).suffix.lower() in STRUCTURED_TEXT:
            text = (root / rel).read_text(encoding="utf-8-sig")
            # This known filter's header describes the material it removes. Its
            # executable body is still audited, while deck content gets no such
            # exemption. Preserve the explanatory header in the copied source.
            audited = re.sub(r"(?m)^--[^\n]*", "", text) if rel == "filters/strip-comments.lua" else text
            if rel not in AUDIT_FIXTURES:
                errors.extend(audit_text(audited, rel, comments=False))
            if Path(rel).suffix.lower() == ".py" and re.search(
                r"(?m)^\s*(?:from|import)\s+(?:scripts\.)?(?:facts|companion)(?:[.\s]|$)", text
            ):
                errors.append(f"{rel}: build dependency imports private authoring machinery")
    if errors:
        raise ValueError("Public prose audit failed:\n" + "\n".join(errors))
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Python 3.13's mkdtemp applies a private ACL on Windows. This directory is a
    # shareable artifact, and a Quarto process launched by the desktop user must
    # be able to traverse it after the atomic rename. Inherit the workspace ACL.
    stage = destination.parent / f".public-export-{uuid.uuid4().hex}"
    stage.mkdir()
    try:
        for rel in sorted(files):
            src = safe_path(root, rel, public=True)
            dst = stage / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix.lower() in TEXT_DOCUMENTS:
                dst.write_text(sanitize_public_document(src.read_text(encoding="utf-8-sig")), encoding="utf-8")
            else:
                shutil.copy2(src, dst)
        config = load_manifest(stage / "slides/_quarto.yml")
        config.setdefault("project", {})["render"] = [chapter["source"] for chapter in selected]
        # JSON is a strict YAML subset; emitting it avoids an extra YAML writer.
        (stage / "slides/_quarto.yml").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        for chapter in exported_manifest.get("chapters", []):
            for rel in chapter.get("reviewed_source_hashes", {}):
                if (stage / rel).is_file():
                    chapter["reviewed_source_hashes"][rel] = source_sha256(stage / rel)
        (stage / "slides/manifest.yml").write_text(json.dumps(exported_manifest, indent=2) + "\n", encoding="utf-8")
        errors = verify_sources(stage, exported_manifest)
        if errors:
            raise ValueError("Dataset-free source validation failed:\n" + "\n".join(errors))
        inventory = [{"path": rel, "sha256": sha256(stage / rel)} for rel in sorted(files)]
        old_paths: set[str] = set()
        if previous_manifest:
            old = json.loads(previous_manifest.read_text(encoding="utf-8"))
            old_paths = {entry["path"] for entry in old.get("files", [])}
            for rel in old_paths:
                safe_path(root, rel, public=True)
        deletions = sorted(old_paths - files)
        report = {
            "version": 1, "bundle_type": "chapter-slides-overlay",
            "review_only": include_pilot and any(chapter.get("status") == "pilot" for chapter in selected),
            "chapter_ids": sorted(selected_ids), "files": inventory,
            "replace_directories": list(OWNED_DIRECTORIES),
            "merge_files": sorted(rel for rel in files if not any(rel.startswith(owned + "/") for owned in OWNED_DIRECTORIES)),
            "remove_files": deletions,
            "validation": {"source_audit": "passed", "dataset_free_source_inventory": "passed",
                           "clean_public_checkout": "not run", "browser_review": "not run", "powerpoint_review": "not run"},
        }
        if public_checkout:
            _validate_public_overlay(stage, public_checkout.resolve(), report)
            report["validation"]["clean_public_checkout"] = "passed (--check in temporary overlay)"
        (stage / "export-manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        status = "REVIEW ONLY: this bundle contains an unapproved pilot. Do not publish it.\n\n" if report["review_only"] else ""
        (stage / "TRANSFER.md").write_text(
            "# Manual public transfer\n\n" + status +
            "This is an overlay for the existing public book repository. Review export-manifest.json and its SHA-256 inventory. "
            "Replace the export-owned slides/, scripts/slides/, and shared/ directories as units; remove an owned directory even "
            "when this export contains no files for it. Review and merge other files individually. Apply remove_files only after "
            "reviewing each obsolete path. Do not copy datasets, author notes, or other authoring checkout files.\n\n"
            "Install scripts/slides/requirements.txt, then run python scripts/build_all.py --check and the complete build in the "
            "public checkout. Inspect both presentation formats before promoting a pilot to approved. "
            "The source-inventory check does not assert a successful Quarto render or native visual review.\n",
            encoding="utf-8",
        )
        # Both locations are verified descendants of the export output directory.
        # Never replace an arbitrary caller-supplied location or unowned contents.
        _validate_destination(root, destination)
        if destination.exists():
            shutil.rmtree(destination)
        stage.replace(destination)
        return destination
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _validate_public_overlay(stage: Path, checkout: Path, report: dict) -> None:
    """Apply only to a disposable copy, never to the supplied public checkout."""
    if not (checkout / "_quarto.yml").is_file():
        raise ValueError("--public-checkout must name an existing public book checkout")
    with tempfile.TemporaryDirectory(prefix="slides-public-check-") as temp:
        sandbox = Path(temp) / "book"
        shutil.copytree(checkout, sandbox, ignore=shutil.ignore_patterns(
            ".git", ".agents", ".codex", "CLAUDE.md", "AGENTS.md", "datasets", "drafts", "facts", "companion",
            "outputs", "_book", "_build", "_shared", ".quarto", ".venv", "__pycache__"))
        for rel in OWNED_DIRECTORIES:
            owned = safe_path(sandbox, rel)
            if owned.exists():
                shutil.rmtree(owned)
        for rel in report["remove_files"]:
            removed = safe_path(sandbox, rel, public=True)
            if removed.is_file():
                removed.unlink()
        shutil.copytree(stage, sandbox, dirs_exist_ok=True)
        result = subprocess.run([sys.executable, "scripts/build_all.py", "--check"], cwd=sandbox,
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError(f"Clean public checkout validation failed:\n{result.stdout}\n{result.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--include-pilot", action="store_true", help="Create a review-only bundle, never a public release")
    parser.add_argument("--previous-manifest", type=Path)
    parser.add_argument("--public-checkout", type=Path)
    args = parser.parse_args()
    try:
        result = export_public(args.root, load_manifest(args.root / "slides/manifest.yml"), args.destination,
                               include_pilot=args.include_pilot, previous_manifest=args.previous_manifest,
                               public_checkout=args.public_checkout)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
