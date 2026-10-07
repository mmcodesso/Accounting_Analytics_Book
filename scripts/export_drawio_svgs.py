#!/usr/bin/env python3
"""Export Draw.io source diagrams and the book cover for the Quarto book.

Each visuals/src/*.drawio file is exported twice:

- visuals/svg/<name>.svg, forced to the light theme on a white background, for
  HTML, EPUB, and DOCX;
- visuals/pdf/<name>.pdf, a cropped vector PDF that filters/pdf-figures.lua
  substitutes for the SVG in the PDF build, so figure text stays vector text.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC_DIR = REPO_ROOT / "visuals" / "src"
DEFAULT_OUT_DIR = REPO_ROOT / "visuals" / "svg"
DEFAULT_PDF_DIR = REPO_ROOT / "visuals" / "pdf"
DEFAULT_COVER_SOURCE = REPO_ROOT / "visuals" / "cover" / "accounting_analytics_cover.drawio"
DEFAULT_COVER_OUTPUT = REPO_ROOT / "visuals" / "cover" / "cover.png"
DEFAULT_PADDING = 0.5
# Match the raster background's native resolution while preserving 17:22.
# Print uses the separate vector PDF, so this PNG need not be 300 DPI.
DEFAULT_COVER_WIDTH = 1105
DEFAULT_COVER_HEIGHT = 1430
DEFAULT_COVER_WEB_WIDTH = 510
DEFAULT_COVER_WEB_HEIGHT = 660
# Bump when the export recipe changes in a way that requires new outputs.
EXPORT_RECIPE_VERSION = 1
DRAWIO_TEXT_WARNING_PATTERN = re.compile(
    r"<switch>\s*"
    r'<g\s+requiredFeatures="http://www\.w3\.org/TR/SVG11/feature#Extensibility"\s*/>\s*'
    r'<a\b[^>]*(?:xlink:)?href="https://www\.drawio\.com/doc/faq/svg-export-text-problems"[^>]*>\s*'
    r"<text\b[^>]*>\s*Text is not SVG - cannot display\s*</text>\s*"
    r"</a>\s*</switch>\s*(?=</svg>)"
)
# light-dark(<light>, <dark>), where either value may itself be rgb(...).
CSS_COLOR = r"(?:[^(),]|\([^()]*\))+"
LIGHT_DARK_PATTERN = re.compile(rf"light-dark\(\s*({CSS_COLOR}?)\s*,\s*{CSS_COLOR}\)")
EMBEDDED_PNG_PATTERN = re.compile(rb"data:image/png;base64,([A-Za-z0-9+/]+={0,2})")


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
        "--pdf-dir",
        type=Path,
        default=DEFAULT_PDF_DIR,
        help="Directory where exported vector .pdf files should be written.",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Do not export the vector PDF copies or PDF cover used by the PDF build.",
    )
    parser.add_argument(
        "--drawio-bin",
        type=Path,
        default=None,
        help="Path to draw.io/diagrams.net executable. Overrides DRAWIO_BIN and PATH.",
    )
    parser.add_argument(
        "--pre-render",
        action="store_true",
        help="Reuse exports prepared by build_all.py when running as a Quarto hook.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO_ROOT / "visuals" / "export-manifest.json",
        help="Tracked source/output checksums used to reuse exports after checkout.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Export every requested output even when its recorded checksums match.",
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
    parser.add_argument(
        "--cover-source",
        type=Path,
        default=DEFAULT_COVER_SOURCE,
        help="Draw.io source file for the book cover.",
    )
    parser.add_argument(
        "--cover-output",
        type=Path,
        default=DEFAULT_COVER_OUTPUT,
        help="Ebook PNG path; also writes <stem>-web.png and <stem>.pdf beside it.",
    )
    parser.add_argument(
        "--cover-width",
        type=int,
        default=DEFAULT_COVER_WIDTH,
        help=f"Cover PNG width in pixels. Defaults to {DEFAULT_COVER_WIDTH}.",
    )
    parser.add_argument(
        "--cover-height",
        type=int,
        default=DEFAULT_COVER_HEIGHT,
        help=f"Cover PNG height in pixels. Defaults to {DEFAULT_COVER_HEIGHT}.",
    )
    parser.add_argument(
        "--skip-cover",
        action="store_true",
        help="Do not export any of the book cover variants.",
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
    return (output.is_file() and output.stat().st_size > 0
            and output.stat().st_mtime_ns >= source.stat().st_mtime_ns)


def export_digest(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in {".drawio", ".svg"}:
        # Git can convert text line endings between Windows and Linux.
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


class ExportManifest:
    """Persist export freshness across clones without trusting checkout mtimes."""

    def __init__(self, path: Path):
        self.path = path
        self.entries = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("version") != 1 or not isinstance(data.get("outputs"), dict):
                    raise ValueError("unsupported manifest structure")
                self.entries = data["outputs"]
            except (ValueError, AttributeError) as exc:
                raise ExportError(f"Invalid export manifest {path}: {exc}") from exc

    def record(self, source: Path, output: Path, settings: dict) -> dict:
        return {"source": source.relative_to(REPO_ROOT).as_posix(),
                "source_sha256": export_digest(source),
                "output_sha256": export_digest(output),
                "recipe": EXPORT_RECIPE_VERSION, "settings": settings}

    def current(self, source: Path, output: Path, settings: dict) -> bool:
        if not output.is_file() or output.stat().st_size == 0:
            return False
        key = output.relative_to(REPO_ROOT).as_posix()
        previous = self.entries.get(key)
        if previous is not None:
            # A changed source cannot be hidden by touching the output file.
            return previous == self.record(source, output, settings)
        # Bootstrap existing local exports once, using the old timestamp rule.
        # Never infer freshness from timestamps on a GitHub Actions checkout.
        defaults = {".svg": {"padding": DEFAULT_PADDING}, ".pdf": {},
                    ".png": {"width": DEFAULT_COVER_WIDTH, "height": DEFAULT_COVER_HEIGHT}}
        return (os.environ.get("GITHUB_ACTIONS") != "true"
                and settings == defaults.get(output.suffix)
                and is_output_current(source, output))

    def remember(self, source: Path, output: Path, settings: dict) -> None:
        self.entries[output.relative_to(REPO_ROOT).as_posix()] = self.record(source, output, settings)

    def save(self) -> None:
        text = json.dumps({"version": 1, "outputs": self.entries}, indent=2, sort_keys=True) + "\n"
        if self.path.is_file() and self.path.read_text(encoding="utf-8") == text:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(self.path)


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


def remove_drawio_text_warning(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    cleaned, replacements = DRAWIO_TEXT_WARNING_PATTERN.subn("", text)
    if replacements:
        path.write_text(cleaned, encoding="utf-8")


def add_white_background(path: Path) -> None:
    """Paint the SVG white so dark reader themes do not show through transparent areas."""
    text = path.read_text(encoding="utf-8")
    svg_match = re.search(r"<svg\b[^>]*>", text)
    view_box = re.search(r'viewBox="([^"]+)"', svg_match.group(0)) if svg_match else None
    if not view_box:
        return
    min_x, min_y, width, height = (float(v) for v in view_box.group(1).replace(",", " ").split())
    svg_tag = svg_match.group(0).replace(
        "background: transparent; background-color: transparent;", "background-color: #FFFFFF;"
    )
    rect = (
        f'<rect x="{format_number(min_x)}" y="{format_number(min_y)}" '
        f'width="{format_number(width)}" height="{format_number(height)}" fill="#FFFFFF"/>'
    )
    path.write_text(
        f"{text[: svg_match.start()]}{svg_tag}{rect}{text[svg_match.end():]}", encoding="utf-8"
    )


def force_light_colors(path: Path) -> None:
    """Replace light-dark() with its light value for renderers that lack it."""
    text = path.read_text(encoding="utf-8")
    cleaned, replacements = LIGHT_DARK_PATTERN.subn(r"\1", text)
    if replacements:
        path.write_text(cleaned, encoding="utf-8")


def compress_png_losslessly(data: bytes) -> bytes:
    """Recompress IDAT only; preserve exact scanlines and all other PNG chunks.

    Draw.io's SVG label fallbacks use fast PNG compression. Keep those fallbacks
    for Word/EPUB readers, but compress their existing data more efficiently.
    Unsupported or malformed images are left untouched, as are larger results.
    """
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        return data
    chunks = []
    position = len(signature)
    while position < len(data):
        if position + 12 > len(data):
            return data
        size = struct.unpack_from(">I", data, position)[0]
        end = position + size + 12
        if end > len(data):
            return data
        kind = data[position + 4:position + 8]
        chunk = data[position:end]
        if zlib.crc32(chunk[4:-4]) != struct.unpack(">I", chunk[-4:])[0]:
            return data
        chunks.append((kind, chunk))
        position = end
    kinds = [kind for kind, _ in chunks]
    if (not kinds or kinds[0] != b"IHDR" or kinds[-1] != b"IEND"
            or b"IDAT" not in kinds or b"acTL" in kinds):
        return data
    first, last = kinds.index(b"IDAT"), len(kinds) - 1 - kinds[::-1].index(b"IDAT")
    if any(kind != b"IDAT" for kind in kinds[first:last + 1]):
        return data
    try:
        scanlines = zlib.decompress(b"".join(chunk[8:-4] for _, chunk in chunks[first:last + 1]))
    except zlib.error:
        return data
    compressed = zlib.compress(scanlines, level=9)
    payload = b"IDAT" + compressed
    replacement = struct.pack(">I", len(compressed)) + payload + struct.pack(">I", zlib.crc32(payload))
    result = (signature + b"".join(chunk for _, chunk in chunks[:first])
              + replacement + b"".join(chunk for _, chunk in chunks[last + 1:]))
    return result if len(result) < len(data) else data


def optimize_svg(path: Path) -> int:
    """Shrink embedded PNGs without rewriting SVG markup; return bytes saved."""
    original = path.read_bytes()

    def replace(match: re.Match[bytes]) -> bytes:
        try:
            data = base64.b64decode(match[1], validate=True)
        except ValueError:
            return match[0]
        compressed = compress_png_losslessly(data)
        if compressed == data:
            return match[0]
        return b"data:image/png;base64," + base64.b64encode(compressed)

    optimized = EMBEDDED_PNG_PATTERN.sub(replace, original)
    if len(optimized) < len(original):
        path.write_bytes(optimized)
    return len(original) - len(optimized)


def run_drawio(command: list[str], source: Path, temp_output: Path, kind: str) -> None:
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
        raise ExportError(f"Draw.io {kind} export failed for {source}.{details}")

    if not temp_output.exists() or temp_output.stat().st_size == 0:
        raise ExportError(
            f"Draw.io reported success but did not create a non-empty {kind}: {temp_output}"
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
        "--svg-theme",
        "light",
        "-o",
        str(temp_output),
        str(source),
    ]
    run_drawio(command, source, temp_output, "SVG")

    add_svg_padding(temp_output, padding)
    remove_drawio_text_warning(temp_output)
    force_light_colors(temp_output)
    add_white_background(temp_output)
    optimize_svg(temp_output)
    temp_output.replace(output)


def export_pdf(drawio_bin: Path, source: Path, output: Path, *, crop: bool = True) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_name(f".{output.stem}.tmp.pdf")
    if temp_output.exists():
        temp_output.unlink()

    command = [
        str(drawio_bin),
        "-x",
        "-f",
        "pdf",
        *(["--crop"] if crop else []),
        "-o",
        str(temp_output),
        str(source),
    ]
    run_drawio(command, source, temp_output, "PDF")
    temp_output.replace(output)


def read_png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        header = file.read(24)

    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ExportError(f"Draw.io created an invalid PNG file: {path}")

    return struct.unpack(">II", header[16:24])


def export_cover_png(
    drawio_bin: Path,
    source: Path,
    output: Path,
    width: int,
    height: int,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_name(f".{output.stem}.tmp.png")
    if temp_output.exists():
        temp_output.unlink()

    command = [
        str(drawio_bin),
        "-x",
        "-f",
        "png",
        "--width",
        str(width),
        "--height",
        str(height),
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
        raise ExportError(f"Draw.io cover export failed for {source}.{details}")

    if not temp_output.exists() or temp_output.stat().st_size == 0:
        raise ExportError(f"Draw.io reported success but did not create a non-empty cover PNG: {temp_output}")

    actual_width, actual_height = read_png_dimensions(temp_output)
    if (actual_width, actual_height) != (width, height):
        temp_output.unlink()
        raise ExportError(
            f"Cover export has dimensions {actual_width}x{actual_height}; "
            f"expected {width}x{height}. Check the cover Draw.io page aspect ratio."
        )

    temp_output.write_bytes(compress_png_losslessly(temp_output.read_bytes()))
    temp_output.replace(output)


def export_png(drawio_bin: Path, source: Path, output: Path, *, scale: float = 2, border: int = 8) -> None:
    """A raster copy of one figure for the PowerPoint slides, which cannot draw the SVG's HTML labels."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_name(f".{output.stem}.tmp.png")
    if temp_output.exists():
        temp_output.unlink()

    command = [
        str(drawio_bin),
        "-x",
        "-f",
        "png",
        "--scale",
        format_number(scale),
        "--border",
        str(border),
        "-o",
        str(temp_output),
        str(source),
    ]
    run_drawio(command, source, temp_output, "PNG")
    read_png_dimensions(temp_output)
    temp_output.write_bytes(compress_png_losslessly(temp_output.read_bytes()))
    temp_output.replace(output)


def cover_targets(output: Path, width: int, height: int, skip_pdf: bool) -> list[tuple[Path, dict]]:
    targets = [
        (output, {"width": width, "height": height}),
        (output.with_name(f"{output.stem}-web.png"),
         {"width": DEFAULT_COVER_WEB_WIDTH, "height": DEFAULT_COVER_WEB_HEIGHT}),
    ]
    if not skip_pdf:
        targets.append((output.with_suffix(".pdf"), {"crop": False}))
    return targets


def run() -> int:
    args = parse_args()
    if args.pre_render and not args.force and os.environ.get("AA_DRAWIO_EXPORTS_READY") == "1":
        print("Reusing Draw.io SVG, PDF, and cover exports prepared for this build.")
        return 0

    src_dir = args.src_dir.resolve()
    out_dir = args.out_dir.resolve()
    pdf_dir = args.pdf_dir.resolve()
    cover_source = args.cover_source.resolve()
    cover_output = args.cover_output.resolve()
    force_export = args.force

    if args.padding < 0:
        raise ExportError(f"Padding must be greater than or equal to 0: {args.padding}")
    if args.cover_width <= 0 or args.cover_height <= 0:
        raise ExportError(
            f"Cover dimensions must be positive: {args.cover_width}x{args.cover_height}"
        )

    if not src_dir.is_dir():
        raise ExportError(f"Draw.io source directory does not exist: {src_dir}")
    if not args.skip_cover and not cover_source.is_file():
        raise ExportError(f"Cover Draw.io source file does not exist: {cover_source}")

    sources = sorted(src_dir.glob("*.drawio"))
    if not sources:
        print(f"No .drawio files found in {src_dir}")

    manifest = ExportManifest(args.manifest.resolve())
    drawio_bin = None

    def executable() -> Path:
        nonlocal drawio_bin
        if drawio_bin is None:
            drawio_bin = find_drawio_executable(args.drawio_bin)
            print(f"Using Draw.io executable: {drawio_bin}")
        return drawio_bin

    print(f"Using transparent SVG padding: {format_number(args.padding)}")
    if not args.skip_cover:
        print(f"Using ebook cover PNG size: {args.cover_width}x{args.cover_height} pixels")
    print("Checking recorded source/output checksums for existing exports.")
    out_dir.mkdir(parents=True, exist_ok=True)

    exported = 0
    skipped = 0
    for source in sources:
        validate_single_page_drawio(source)
        targets = [out_dir / f"{source.stem}.svg"]
        if not args.skip_pdf:
            targets.append(pdf_dir / f"{source.stem}.pdf")

        for output in targets:
            settings = {"padding": args.padding} if output.suffix == ".svg" else {}
            if not force_export and manifest.current(source, output, settings):
                manifest.remember(source, output, settings)
                print(f"skip   {source.relative_to(REPO_ROOT)} -> {output.relative_to(REPO_ROOT)}")
                skipped += 1
                continue

            if output.suffix == ".svg":
                export_svg(executable(), source, output, args.padding)
            else:
                export_pdf(executable(), source, output)
            manifest.remember(source, output, settings)
            print(f"export {source.relative_to(REPO_ROOT)} -> {output.relative_to(REPO_ROOT)}")
            exported += 1

    if not args.skip_cover:
        validate_single_page_drawio(cover_source)
        for output, settings in cover_targets(cover_output, args.cover_width, args.cover_height, args.skip_pdf):
            if not force_export and manifest.current(cover_source, output, settings):
                print(f"skip   {cover_source.relative_to(REPO_ROOT)} -> {output.relative_to(REPO_ROOT)}")
                skipped += 1
            else:
                if output.suffix == ".pdf":
                    export_pdf(executable(), cover_source, output, crop=False)
                else:
                    export_cover_png(executable(), cover_source, output, settings["width"], settings["height"])
                print(f"export {cover_source.relative_to(REPO_ROOT)} -> {output.relative_to(REPO_ROOT)}")
                exported += 1
            manifest.remember(cover_source, output, settings)

    manifest.save()
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
