"""Package rebuilt slide outputs and the reviewed public source overlay.

Run after scripts/build_all.py and its --export-public mode. Previous ZIPs,
review screenshots, and reports from earlier builds are never required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid
import zipfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.build_all import source_checks
from scripts.slides.verify import (active_chapters, load_manifest, safe_path,
                                  sha256, verify_outputs)


def _require_clean(errors: list[str]) -> None:
    if errors:
        raise ValueError("Release validation failed:\n" + "\n".join(errors))


def _public_inventory(root: Path, approved_ids: set[str]) -> list[tuple[Path, str]]:
    export = safe_path(root, "outputs/public-export")
    if not (export / "export-manifest.json").is_file():
        raise ValueError("Rebuild the public source bundle: python scripts/build_all.py --export-public")
    report = load_manifest(export / "export-manifest.json")
    if report.get("review_only") or report.get("validation", {}).get("source_audit") != "passed":
        raise ValueError("A reviewed public source bundle is required; pilot bundles cannot be packaged.")
    if set(report.get("chapter_ids", [])) != approved_ids:
        raise ValueError("Public bundle chapter inventory changed; regenerate --export-public.")
    files = []
    for entry in report.get("files", []):
        relative = entry["path"]
        path = safe_path(export, relative, public=True)
        if not path.is_file() or sha256(path) != entry["sha256"]:
            raise ValueError(f"Public bundle input changed: {relative}; regenerate --export-public.")
        files.append((path, relative))
    names = [name for _, name in files]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate file in public bundle inventory.")
    _require_clean(source_checks(export, load_manifest(export / "slides/manifest.yml")))
    # Only allowlisted inputs and the exporter's transfer instructions enter the
    # ZIP. Scratch files beside those inputs do not become publication inputs.
    files += [(export / name, name) for name in ("export-manifest.json", "TRANSFER.md")]
    return files


def _write_zip(root: Path, name: str, files: list[tuple[Path, str]]) -> dict:
    output = safe_path(root, "outputs")
    output.mkdir(parents=True, exist_ok=True)
    target = safe_path(root, "outputs/" + name)
    temporary = output / f".{name}-{uuid.uuid4().hex}.pending"
    try:
        with zipfile.ZipFile(temporary, "x", zipfile.ZIP_DEFLATED) as archive:
            for path, relative in sorted(files, key=lambda entry: entry[1]):
                archive.write(path, relative)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError(f"Corrupt release ZIP: {name}")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": target.relative_to(root).as_posix(), "files": len(files),
            "bytes": target.stat().st_size, "sha256": sha256(target)}


def package_release(root: Path) -> list[dict]:
    root = root.resolve()
    manifest = load_manifest(root / "slides/manifest.yml")
    _require_clean(source_checks(root, manifest))
    build_report = safe_path(root, "outputs/build/build-report.json")
    if not build_report.is_file():
        raise ValueError("Run python scripts/build_all.py before packaging the assembled site.")
    build = load_manifest(build_report)
    if build.get("mode") != "book-and-slides" or build.get("automated_artifact_checks") != "passed":
        raise ValueError("A complete validated site build is required before packaging.")
    if build.get("includes_pilot"):
        raise ValueError("A pilot review site cannot be packaged as a public release.")
    approved_ids = {chapter["id"] for chapter in active_chapters(manifest, public_only=True)}
    if not approved_ids:
        raise ValueError("There are no approved decks to package.")
    _require_clean(verify_outputs(root, manifest, site=root / "_book"))
    source_files = _public_inventory(root, approved_ids)
    site = safe_path(root, "_book/slides")
    rendered_files = []
    for path in sorted(site.rglob("*")):
        if path.is_file():
            relative = path.relative_to(root / "_book").as_posix()
            safe_path(root, path.relative_to(root).as_posix(), public=True)
            rendered_files.append((path, relative))
    packages = [_write_zip(root, "chapter-slides.zip", rendered_files),
                _write_zip(root, "chapter-slides-public-source.zip", source_files)]
    report = safe_path(root, "outputs/build/release-packages.json")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")
    return packages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        print(json.dumps(package_release(args.root), indent=2))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
