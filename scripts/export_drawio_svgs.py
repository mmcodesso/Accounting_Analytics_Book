#!/usr/bin/env python3
"""Export Draw.io source diagrams to SVG files for the Quarto book."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC_DIR = REPO_ROOT / "visuals" / "src"
DEFAULT_OUT_DIR = REPO_ROOT / "visuals" / "svg"
DEFAULT_PADDING = 0.5


class ExportError(RuntimeError):
    """Raised when diagram export cannot continue."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export every visuals/src/*.drawio file to visuals/svg/*.svg."
    )
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=DEFAULT_SRC_DIR,
        help="Directory containing .drawio source files.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Directory where exported .svg files should be written.",
    )
    parser.add_argument(
        "--drawio-bin",
        type=Path,
        default=None,
        help="Path to draw.io/diagrams.net executable. Overrides DRAWIO_BIN and PATH.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Export all diagrams even when the SVG output is newer than the source.",
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=DEFAULT_PADDING,
        help=f"Transparent padding to add around exported SVGs. Defaults to {DEFAULT_PADDING}.",
    )
    parser.add_argument(
        "--border",
        type=float,
        dest="padding",
        help="Deprecated alias for --padding.",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate_single_page_drawio(path: Path) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ExportError(f"{path} is not valid Draw.io XML: {exc}") from exc

    diagrams = [element for element in root.iter() if local_name(element.tag) == "diagram"]
    if len(diagrams) != 1:
        raise ExportError(
            f"{path} contains {len(diagrams)} diagram pages; expected exactly one. "
            "Split multi-page Draw.io files into one source file per book figure."
        )


def find_drawio_executable(explicit_path: Path | None) -> Path:
    if explicit_path:
        path = explicit_path.expanduser()
        if path.is_file():
            return path
        raise ExportError(f"Draw.io executable passed with --drawio-bin does not exist: {path}")

    candidates: list[str | Path] = []

    env_path = os.environ.get("DRAWIO_BIN")
    if env_path:
        path = Path(env_path).expanduser()
        if path.is_file():
            return path
        raise ExportError(f"Draw.io executable set in DRAWIO_BIN does not exist: {path}")

    for command_name in ("drawio", "draw.io", "draw.io.exe", "diagrams.net", "diagrams.net.exe"):
        resolved = shutil.which(command_name)
        if resolved:
            candidates.append(resolved)

    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        candidates.extend(
            [
                Path(r"C:\Program Files\draw.io\draw.io.exe"),
                Path(r"C:\Program Files (x86)\draw.io\draw.io.exe"),
                Path(r"C:\Program Files\diagrams.net\diagrams.net.exe"),
                Path(r"C:\Program Files (x86)\diagrams.net\diagrams.net.exe"),
            ]
        )
        if local_app_data:
            candidates.extend(
                [
                    Path(local_app_data) / "Programs" / "draw.io" / "draw.io.exe",
                    Path(local_app_data) / "Programs" / "diagrams.net" / "diagrams.net.exe",
                ]
            )

    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_file():
            return path

    searched = ", ".join(str(Path(candidate).expanduser()) for candidate in candidates)
    raise ExportError(
        "Could not find the Draw.io executable. Install Draw.io/diagrams.net, add it to PATH, "
        "set DRAWIO_BIN, or pass --drawio-bin. "
        f"Searched: {searched or 'no candidate paths'}"
    )


def is_output_current(source: Path, output: Path) -> bool:
    return output.exists() and output.stat().st_mtime >= source.stat().st_mtime


def format_number(value: float) -> str:
    return f"{value:g}"


def parse_svg_length(value: str) -> tuple[float, str]:
    stripped = value.strip()
    for suffix in ("px", "pt", "in", "cm", "mm", "pc", "%"):
        if stripped.endswith(suffix):
            return float(stripped[: -len(suffix)]), suffix
    return float(stripped), ""


def replace_or_add_svg_attr(svg_tag: str, name: str, value: str) -> str:
    pattern = re.compile(rf'(\s{name}=)(["\'])(.*?)(\2)')
    if pattern.search(svg_tag):
        return pattern.sub(rf'\1"{value}"', svg_tag, count=1)
    return svg_tag.replace(">", f' {name}="{value}">', 1)


def add_svg_padding(path: Path, padding: float) -> None:
    if padding == 0:
        return

    text = path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ExportError(f"Draw.io created invalid SVG XML: {path}: {exc}") from exc

    view_box = root.attrib.get("viewBox")
    if view_box:
        parts = view_box.replace(",", " ").split()
        if len(parts) != 4:
            raise ExportError(f"SVG has an unsupported viewBox for padding insertion: {path}")
        min_x, min_y, width, height = (float(part) for part in parts)
    else:
        min_x = min_y = 0.0
        width, _ = parse_svg_length(root.attrib["width"])
        height, _ = parse_svg_length(root.attrib["height"])

    new_view_box = " ".join(
        format_number(value)
        for value in (
            min_x - padding,
            min_y - padding,
            width + (padding * 2),
            height + (padding * 2),
        )
    )

    svg_match = re.search(r"<svg\b[^>]*>", text)
    if not svg_match:
        raise ExportError(f"SVG is missing its opening <svg> tag: {path}")

    svg_tag = svg_match.group(0)
    svg_tag = replace_or_add_svg_attr(svg_tag, "viewBox", new_view_box)

    for attr_name in ("width", "height"):
        if attr_name in root.attrib:
            length, unit = parse_svg_length(root.attrib[attr_name])
            svg_tag = replace_or_add_svg_attr(
                svg_tag,
                attr_name,
                f"{format_number(length + (padding * 2))}{unit}",
            )

    path.write_text(
        f"{text[: svg_match.start()]}{svg_tag}{text[svg_match.end():]}",
        encoding="utf-8",
    )


def export_svg(
    drawio_bin: Path,
    source: Path,
    output: Path,
    padding: float,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_name(f".{output.stem}.tmp.svg")
    if temp_output.exists():
        temp_output.unlink()

    command = [
        str(drawio_bin),
        "-x",
        "-f",
        "svg",
        "-o",
        str(temp_output),
        str(source),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        if temp_output.exists():
            temp_output.unlink()
        details = "\n".join(
            part.strip()
            for part in (result.stdout, result.stderr)
            if part and part.strip()
        )
        if details:
            details = f"\n{details}"
        raise ExportError(f"Draw.io export failed for {source}.{details}")

    if not temp_output.exists() or temp_output.stat().st_size == 0:
        raise ExportError(f"Draw.io reported success but did not create a non-empty SVG: {temp_output}")

    add_svg_padding(temp_output, padding)
    temp_output.replace(output)


def run() -> int:
    args = parse_args()
    src_dir = args.src_dir.resolve()
    out_dir = args.out_dir.resolve()
    force_export = args.force or os.environ.get("GITHUB_ACTIONS") == "true"

    if args.padding < 0:
        raise ExportError(f"Padding must be greater than or equal to 0: {args.padding}")

    if not src_dir.is_dir():
        raise ExportError(f"Draw.io source directory does not exist: {src_dir}")

    sources = sorted(src_dir.glob("*.drawio"))
    if not sources:
        print(f"No .drawio files found in {src_dir}")
        return 0

    drawio_bin = find_drawio_executable(args.drawio_bin)
    print(f"Using Draw.io executable: {drawio_bin}")
    print(f"Using transparent SVG padding: {format_number(args.padding)}")
    if force_export and not args.force:
        print("GitHub Actions detected; exporting all diagrams because checkout timestamps are not reliable.")
    out_dir.mkdir(parents=True, exist_ok=True)

    exported = 0
    skipped = 0
    for source in sources:
        validate_single_page_drawio(source)
        output = out_dir / f"{source.stem}.svg"

        if not force_export and is_output_current(source, output):
            print(f"skip   {source.relative_to(REPO_ROOT)} -> {output.relative_to(REPO_ROOT)}")
            skipped += 1
            continue

        export_svg(drawio_bin, source, output, args.padding)
        print(f"export {source.relative_to(REPO_ROOT)} -> {output.relative_to(REPO_ROOT)}")
        exported += 1

    print(f"Done: {exported} exported, {skipped} skipped.")
    return 0


def main() -> int:
    try:
        return run()
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
