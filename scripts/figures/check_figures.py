#!/usr/bin/env python3
"""Check every figure source against the book's figure design standard.

For each visuals/src/*.drawio file this reports the frame size, the smallest
font and its printed size, the lowest text contrast, and any rule violations:

- the 860 px frame and the 980 px height limit;
- Helvetica only, and nothing smaller than 12 px;
- palette colors only, and every text/background pair at 4.5:1 or better;
- every ER endpoint (edges tagged er= or trace=) matches the data.

With --exports it also checks visuals/svg (light color scheme, no light-dark(), white background)
and visuals/pdf (a vector PDF for every source).

Usage:
    python scripts/figures/check_figures.py [--exports] [name-prefix ...]
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data import REPO_ROOT, cardinality, trace_card  # noqa: E402
from drawio import FONT_FAMILY, FRAME_WIDTH, MAX_HEIGHT, PALETTE, SMALL, WHITE  # noqa: E402

SRC_DIR = REPO_ROOT / "visuals" / "src"
SVG_DIR = REPO_ROOT / "visuals" / "svg"
PDF_DIR = REPO_ROOT / "visuals" / "pdf"
PDF_TEXT_WIDTH_PT = 522   # letter paper with 0.75 in and 0.5 in margins
HTML_COLUMN_PX = 800
MIN_CONTRAST = 4.5
ALLOWED = {c.upper() for c in PALETTE} | {"NONE", "DEFAULT"}


def style_map(style: str) -> dict[str, str]:
    out = {}
    for part in style.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key] = value
        elif part:
            out[part] = ""
    return out


def luminance(color: str) -> float:
    color = color.lstrip("#")
    channels = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def text_of(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value.replace("&nbsp;", " "))).strip()


def inline_colors(value: str) -> list[str]:
    return [c.upper() for c in re.findall(r'color(?:="|:\s*)(#[0-9A-Fa-f]{6})', value)]


def inline_sizes(value: str) -> list[int]:
    return [int(s) for s in re.findall(r"font-size:\s*(\d+)px", value)]


# Helvetica advance widths per 1000 em (Arial and Liberation Sans share them), used to
# flag single-line labels that are too wide for their cell.
_REGULAR = dict(zip(
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278, *[556] * 10,
     278, 278, 584, 584, 584, 556, 1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667,
     556, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278,
     469, 556, 333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
     556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]))
_BOLD = dict(_REGULAR, **dict(zip(
    "ABJKLabcdfghijklmnopqrstuvwxyz:'\"",
    [722, 722, 556, 722, 611, 556, 611, 556, 611, 333, 611, 611, 278, 278, 556, 278, 889, 611,
     611, 611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 333, 238, 474])))


def text_width(value: str, size: float, bold: bool) -> float:
    """Approximate rendered width of an HTML label in px."""
    total, is_bold = 0.0, bold
    for token in re.split(r"(<[^>]+>)", value.replace("&nbsp;", " ")):
        if token.startswith("<"):
            if re.match(r"<b\b", token):
                is_bold = True
            elif token.startswith("</b"):
                is_bold = bold
            continue
        table = _BOLD if is_bold else _REGULAR
        total += sum(table.get(ch, 556) for ch in html.unescape(token)) * size / 1000
    return total


def check_source(path: Path) -> tuple[dict, list[str]]:
    root = ET.parse(path).getroot()
    model = root.find("diagram/mxGraphModel")
    problems: list[str] = []
    if model is None:
        return {}, ["compressed or unreadable diagram (rebuild it with build.py)"]
    if (model.get("background") or "").upper() != WHITE:
        problems.append("background is not white")
    cells = list(model.iter("mxCell"))
    frame = next((c for c in cells if c.get("id") == "frame"), None)
    if frame is None or frame.find("mxGeometry").get("width") != str(FRAME_WIDTH):
        problems.append(f"missing the {FRAME_WIDTH} px frame")

    boxes = []   # (x, y, w, h, fill) of filled vertices in drawing order
    min_size, min_ratio, er_checked = 99, 99.0, 0
    width = height = 0.0
    for cell in cells:
        style = style_map(cell.get("style") or "")
        value = cell.get("value") or ""
        geo = cell.find("mxGeometry")
        is_edge = cell.get("edge") == "1"
        for key in ("fillColor", "strokeColor", "fontColor", "labelBackgroundColor"):
            color = style.get(key)
            if color and color.upper() not in ALLOWED:
                problems.append(f"{cell.get('id')}: {key} {color} is not in the palette")
        for color in inline_colors(value):
            if color not in ALLOWED:
                problems.append(f"{cell.get('id')}: inline color {color} is not in the palette")

        if not is_edge and geo is not None and cell.get("vertex") == "1":
            x, y = float(geo.get("x", 0)), float(geo.get("y", 0))
            w, h = float(geo.get("width", 0)), float(geo.get("height", 0))
            width, height = max(width, x + w), max(height, y + h)
            fill = style.get("fillColor", "none")
            if fill.lower() != "none" and "text" not in style:
                boxes.append((x, y, w, h, fill.upper()))
        if is_edge and geo is not None:
            for point in geo.iter("mxPoint"):
                width = max(width, float(point.get("x", 0)))
                height = max(height, float(point.get("y", 0)))

        label = text_of(value)
        if label:
            if style.get("fontFamily") != FONT_FAMILY:
                problems.append(f"{cell.get('id')}: font {style.get('fontFamily')!r} ({label[:30]})")
            sizes = [int(float(style.get("fontSize", 11)))] + inline_sizes(value)
            min_size = min(min_size, *sizes)
            if not is_edge and "<br" not in value and float(geo.get("height", 0)) <= 32:
                # Draw.io lets text run into the cell padding, so measure against the border.
                room = float(geo.get("width", 0)) - 6
                needed = text_width(value, sizes[0], style.get("fontStyle") in ("1", "3"))
                if needed > room:
                    problems.append(f"{cell.get('id')}: text needs about {needed:.0f} px but the "
                                    f"cell leaves {room:.0f} px ({label[:30]})")
            if min(sizes) < SMALL:
                problems.append(f"{cell.get('id')}: {min(sizes)} px text ({label[:30]})")
            if is_edge:
                background = style.get("labelBackgroundColor", WHITE).upper()
            else:
                background = style.get("fillColor", "none").upper()
                if background == "NONE":
                    background = WHITE
                    cx = float(geo.get("x", 0)) + float(geo.get("width", 0)) / 2
                    cy = float(geo.get("y", 0)) + float(geo.get("height", 0)) / 2
                    for bx, by, bw, bh, bfill in boxes:
                        if bx <= cx <= bx + bw and by <= cy <= by + bh:
                            background = bfill
            for color in [style.get("fontColor", "#000000").upper()] + inline_colors(value):
                ratio = contrast(color, background)
                min_ratio = min(min_ratio, ratio)
                if ratio < MIN_CONTRAST:
                    problems.append(f"{cell.get('id')}: {color} on {background} is "
                                    f"{ratio:.2f}:1 ({label[:30]})")

        if is_edge and ("er" in style or "trace" in style):
            er_checked += 1
            if "er" in style:
                parent, child = style["er"].split(">")
                expected = cardinality(*parent.split("."), *child.split("."))
            else:
                expected = trace_card(*style["trace"].split("."))
            drawn = (style.get("startArrow"), style.get("endArrow"))
            if drawn != expected:
                problems.append(f"{cell.get('id')}: {style.get('er') or style.get('trace')} drawn "
                                f"{drawn}, data says {expected}")

    if width > FRAME_WIDTH + 0.5:
        problems.append(f"content reaches x={width:g}")
    if height > MAX_HEIGHT:
        problems.append(f"height {height:g} exceeds {MAX_HEIGHT}")
    return {"width": width, "height": height, "min_px": min_size, "contrast": min_ratio,
            "er": er_checked}, problems


def svg_width(path: Path) -> float | None:
    match = re.search(r'<svg\b[^>]*\swidth="([\d.]+)px"', path.read_text(encoding="utf-8")[:2000])
    return float(match.group(1)) if match else None


def check_exports(stem: str) -> tuple[float | None, list[str]]:
    problems = []
    svg = SVG_DIR / f"{stem}.svg"
    width = None
    if not svg.exists():
        problems.append("SVG export missing")
    else:
        text = svg.read_text(encoding="utf-8")
        if "light-dark(" in text:
            problems.append("SVG still uses light-dark() colors")
        if "color-scheme: light;" not in text:
            problems.append("SVG is not forced to the light color scheme")
        if "background-color: #FFFFFF;" not in text[:3000]:
            problems.append("SVG has no white background")
        width = svg_width(svg)
    if not (PDF_DIR / f"{stem}.pdf").exists():
        problems.append("vector PDF export missing")
    return width, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prefix", nargs="*", help="Only check figures whose name starts with this.")
    parser.add_argument("--exports", action="store_true", help="Also check the SVG and PDF exports.")
    args = parser.parse_args()

    sources = sorted(p for p in SRC_DIR.glob("*.drawio")
                     if not args.prefix or any(p.stem.startswith(x) for x in args.prefix))
    failures = 0
    print(f"{'figure':44} {'size':>9} {'min px':>6} {'PDF pt':>6} {'HTML px':>7} "
          f"{'contrast':>8} {'ER':>3}")
    for path in sources:
        stats, problems = check_source(path)
        width = stats.get("width", FRAME_WIDTH)
        if args.exports:
            exported, more = check_exports(path.stem)
            problems += more
            width = exported or width
        min_px = stats.get("min_px", 0)
        pdf_pt = min_px * PDF_TEXT_WIDTH_PT / max(width, PDF_TEXT_WIDTH_PT / 0.75)
        html_px = min_px * HTML_COLUMN_PX / max(width, HTML_COLUMN_PX)
        if pdf_pt < 7:
            problems.append(f"smallest text prints at {pdf_pt:.1f} pt")
        print(f"{path.stem:44} {stats.get('width', 0):>4.0f}x{stats.get('height', 0):<4.0f} "
              f"{min_px:>6} {pdf_pt:>6.1f} {html_px:>7.1f} {stats.get('contrast', 0):>7.1f}:1 "
              f"{stats.get('er', 0):>3}")
        for problem in problems:
            print(f"    - {problem}")
        failures += bool(problems)
    print(f"\n{len(sources)} figures checked, {failures} with problems.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
