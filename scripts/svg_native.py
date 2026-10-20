#!/usr/bin/env python3
"""Smaller Draw.io SVG exports: redundant markup out, single-line labels as native SVG text.

Draw.io 29.6.6 writes every label as an HTML foreignObject plus, in a <switch>, a fallback for viewers without
foreignObject support. By default that fallback is a PNG of the label drawn at four times the size, which made 165
diagrams 101 MB (90.7% of it PNG). This module holds the pieces that the export and the lab (scripts/svg_lab.py) share:

    strip_svg_metadata    drops markup that no viewer needs: a style that repeats the fill and stroke attributes, the
                          pointer-events of shapes, an empty <defs/>, the DOCTYPE (and, only if asked, data-cell-id)
    labels / label_runs   reads every label of an export (HTML or native) as styled text runs, per Draw.io cell
    single_line_cells     the cells whose HTML label fits on one line, measured with Arial against the width Draw.io
                          gave the label (checked against the heights of the old PNG fallbacks: no label that wraps is
                          ever taken for one line)
    native_labels_copy    a copy of a .drawio text in which those cells carry convertToSvg=1, Draw.io's own "Convert
                          labels to SVG"; the source file is never touched

Draw.io's conversion (the checkbox in Format > Text, style convertToSvg) does not wrap text and does not read <br>, so
a label that wraps must stay a foreignObject; the converted copy would put it on one long line.
"""

from __future__ import annotations

import html
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
# Passed to `drawio -x -f svg`: without embedded fonts Draw.io keeps its own plain-text fallback instead of replacing
# it with a PNG (Editor.foreignObjectImages only runs when fonts are embedded). The diagrams use only Helvetica.
DRAWIO_NO_RASTER_FALLBACK = ("--embed-svg-fonts", "false")
# A label counts as one line only when its text is this much narrower than its box (px): Chromium and Pillow
# disagree by a fraction of a pixel (kerning), and a label wrongly kept as HTML costs bytes, never fidelity.
FIT_MARGIN = 2.0
SHAPE_TAGS = "rect|path|ellipse|circle|polygon|polyline|line"


class FontMissing(RuntimeError):
    """No Arial-compatible font was found to measure labels with."""


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


# ----------------------------------------------------------------------------------------------- colors and styles

_RGB = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")
_LIGHT_DARK = re.compile(r"light-dark\(\s*((?:[^(),]|\([^()]*\))+?)\s*,")


def normalize_color(value: str | None) -> str | None:
    """#rrggbb in lower case for hex and rgb() colors (the light value of light-dark()); other words in lower case."""
    if value is None:
        return None
    text = value.strip().lower()
    light = _LIGHT_DARK.match(text)
    if light:
        text = light.group(1).strip()
    rgb = _RGB.fullmatch(text)
    if rgb:
        return "#" + "".join(f"{int(part):02x}" for part in rgb.groups())
    if re.fullmatch(r"#[0-9a-f]{3}", text):
        return "#" + "".join(ch * 2 for ch in text[1:])
    return text


def parse_style(style: str | None) -> dict[str, str]:
    """A CSS declaration list as a dict (the colon inside rgb() or light-dark() values is not a separator)."""
    declarations: dict[str, str] = {}
    for part in (style or "").split(";"):
        name, colon, value = part.partition(":")
        if colon and name.strip():
            declarations[name.strip().lower()] = value.strip()
    return declarations


# ---------------------------------------------------------------------------------------------- stripping metadata


@dataclass(frozen=True)
class StripOptions:
    redundant_styles: bool = True   # style="fill: rgb(..); stroke: rgb(..)" that repeats fill= and stroke=
    pointer_events: bool = True     # pointer-events on shapes: a picture used through <img> takes no pointer events
    empty_defs: bool = True         # <defs/>
    doctype: bool = True            # the SVG 1.1 DOCTYPE, whose DTD no viewer fetches
    cell_ids: bool = False          # data-cell-id: only Draw.io's cell ids, but the lab and the tests read them


_SHAPE = re.compile(rf"<({SHAPE_TAGS})\b([^<>]*?)(/?)>")
_ATTR = re.compile(r'\s([\w:.-]+)="([^"]*)"')


def _strip_shape(match: re.Match[str], options: StripOptions) -> str:
    tag, attributes, close = match.groups()
    pairs = _ATTR.findall(attributes)
    if "".join(f' {name}="{value}"' for name, value in pairs) != attributes:
        return match.group(0)  # not in the canonical form Draw.io writes: leave it alone
    kept = []
    values = dict(pairs)
    for name, value in pairs:
        if name == "pointer-events" and options.pointer_events:
            continue
        if name == "style" and options.redundant_styles:
            declarations = parse_style(value)
            if declarations and all(
                    prop in ("fill", "stroke") and prop in values
                    and normalize_color(values[prop]) == normalize_color(text) for prop, text in declarations.items()):
                continue
        kept.append((name, value))
    return f"<{tag}" + "".join(f' {name}="{value}"' for name, value in kept) + close + ">"


def strip_svg_metadata(text: str, options: StripOptions = StripOptions()) -> str:
    """The same drawing without markup that no viewer needs. Never changes a drawn color, position or label."""
    if options.redundant_styles or options.pointer_events:
        text = _SHAPE.sub(lambda match: _strip_shape(match, options), text)
    if options.empty_defs:
        text = text.replace("<defs/>", "")
    if options.doctype:
        text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", text, count=1)
    if options.cell_ids:
        text = re.sub(r' data-cell-id="[^"]*"', "", text)
    return text


# ------------------------------------------------------------------------------------------------ reading labels


@dataclass(frozen=True)
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    size: float = 0.0
    color: str | None = None


@dataclass
class Label:
    cell: str
    kind: str                       # "html" (foreignObject) or "native" (<text>)
    runs: list[Run]
    size: float                     # the label's base font size, px
    width: float | None = None      # html: the width Draw.io gave the text, px
    nowrap: bool = False
    has_br: bool = False
    background: bool = False        # html: the label has a background color or a border (an edge label over a line)
    rotated: bool = False           # drawn inside a rotate() transform
    fallback: str | None = None     # the text of the <switch> fallback, if there is one
    image_box: tuple[float, float, float, float] | None = None  # x, y, w, h of a PNG fallback (the label's box)

    @property
    def text(self) -> str:
        return collapse("".join(run.text for run in self.runs))

    def signature(self) -> list[tuple]:
        """(character, bold, italic, color) for every visible character: what a reader sees, apart from layout."""
        chars = []
        previous_space = True
        for run in self.runs:
            for ch in run.text.replace("\r", "").replace("\n", " ").replace("\t", " "):
                if ch == " ":
                    if previous_space:
                        continue
                    previous_space = True
                    chars.append((" ", False, False, None))
                else:
                    previous_space = False
                    chars.append((ch, run.bold, run.italic, run.color))
        while chars and chars[-1][0] == " ":
            chars.pop()
        return chars


def collapse(text: str) -> str:
    """HTML whitespace rules: runs of space, tab and newline become one space (a no-break space is kept)."""
    return re.sub(r"[ \t\r\n]+", " ", text).strip(" ")


def _walk(element: ET.Element, state: dict, runs: list[Run], flags: dict) -> None:
    name = local(element.tag).lower()
    style = parse_style(element.get("style"))
    state = dict(state)
    if name in ("b", "strong") or style.get("font-weight") in ("bold", "700", "600"):
        state["bold"] = True
    if name in ("i", "em") or style.get("font-style") == "italic":
        state["italic"] = True
    if name == "u" or "underline" in style.get("text-decoration", ""):
        state["underline"] = True
    color = normalize_color(style.get("color") or (element.get("color") if name == "font" else None))
    if color:
        state["color"] = color
    size = re.fullmatch(r"([\d.]+)px", style.get("font-size", ""))
    if size:
        state["size"] = float(size.group(1))
    if name == "br":
        flags["br"] = True
        runs.append(Run("\n", **state))
    if element.text:
        runs.append(Run(element.text, **state))
    for child in element:
        _walk(child, state, runs, flags)
        if child.tail:
            runs.append(Run(child.tail, **state))


def html_runs(text_div: ET.Element) -> tuple[list[Run], bool, float, str | None, bool]:
    """The runs of an HTML label's innermost div, with its has-<br> flag, base size, base color and nowrap."""
    style = parse_style(text_div.get("style"))
    size = float(re.sub(r"[^\d.]", "", style.get("font-size", "0")) or 0)
    base = {"bold": style.get("font-weight") in ("bold", "700"), "italic": style.get("font-style") == "italic",
            "underline": False, "size": size, "color": normalize_color(style.get("color"))}
    runs: list[Run] = []
    flags = {"br": False}
    if text_div.text:
        runs.append(Run(text_div.text, **base))
    for child in text_div:
        _walk(child, base, runs, flags)
        if child.tail:
            runs.append(Run(child.tail, **base))
    return runs, flags["br"], size, base["color"], "nowrap" in style.get("white-space", "")


def _native_runs(text_element: ET.Element, state: dict, runs: list[Run]) -> None:
    name = local(text_element.tag)
    state = dict(state)
    if text_element.get("font-weight") == "bold" or parse_style(text_element.get("style")).get("font-weight") == "bold":
        state["bold"] = True
    if text_element.get("font-style") == "italic" or parse_style(text_element.get("style")).get("font-style") == "italic":
        state["italic"] = True
    decoration = text_element.get("text-decoration", "")
    if "underline" in decoration:
        state["underline"] = True
    fill = normalize_color(text_element.get("fill") or parse_style(text_element.get("style")).get("fill"))
    if fill:
        state["color"] = fill
    if name in ("text", "tspan") and text_element.text:
        runs.append(Run(text_element.text, **state))
    for child in text_element:
        _native_runs(child, state, runs)
        if child.tail:
            runs.append(Run(child.tail, **state))


def labels(svg_text: str) -> list[Label]:
    """Every label of an export, in drawing order: HTML labels (foreignObject) and native <text> labels."""
    root = ET.fromstring(svg_text)
    found: list[Label] = []

    def visit(element: ET.Element, cell: str, group: dict, rotated: bool = False) -> None:
        tag = local(element.tag)
        cell = element.get("data-cell-id", cell) if tag == "g" else cell
        rotated = rotated or "rotate" in element.get("transform", "")
        if tag == "switch":
            fo = next((child for child in element if local(child.tag) == "foreignObject"), None)
            if fo is not None:
                label = _html_label(cell, element, fo)
                label.rotated = rotated
                found.append(label)
                return
        if tag == "text":
            runs: list[Run] = []
            _native_runs(element, {**group, "size": group.get("size", 0.0)}, runs)
            found.append(Label(cell, "native", runs, group.get("size", 0.0), rotated=rotated))
            return
        if tag == "g" and element.get("fill") and (element.get("font-size") or element.get("font-family")):
            size = re.sub(r"[^\d.]", "", element.get("font-size", "")) or "0"
            group = {"size": float(size), "color": normalize_color(element.get("fill")),
                     "bold": element.get("font-weight") == "bold", "italic": element.get("font-style") == "italic"}
        for child in element:
            visit(child, cell, group, rotated)

    visit(root, "", {})
    return found


def _html_label(cell: str, switch: ET.Element, fo: ET.Element) -> Label:
    flex = next((child for child in fo if local(child.tag) == "div"), None)
    box = next((child for child in flex if local(child.tag) == "div"), None) if flex is not None else None
    text_div = next((child for child in box if local(child.tag) == "div"), None) if box is not None else None
    if text_div is None:
        return Label(cell, "html", [], 0.0)
    runs, has_br, size, _, nowrap = html_runs(text_div)
    width = re.search(r"(?:^|;)\s*width:\s*([\d.]+)px", flex.get("style", ""))
    label = Label(cell, "html", runs, size, float(width.group(1)) if width else None, nowrap, has_br)
    label.background = any(re.search(r"(?:^|;)\s*(?:background|border)[\w-]*\s*:", div.get("style") or "")
                           for div in (flex, box, text_div))
    for child in switch:
        if local(child.tag) == "text":
            label.fallback = "".join(child.itertext())
        elif local(child.tag) == "image":
            try:
                label.image_box = tuple(float(child.get(key, "0")) for key in ("x", "y", "width", "height"))  # type: ignore
            except ValueError:
                pass
    return label


# -------------------------------------------------------------------------------------- measuring and classifying

_FONT_FILES = {
    (False, False): ("arial.ttf", "LiberationSans-Regular.ttf", "Arimo-Regular.ttf", "Arial.ttf"),
    (True, False): ("arialbd.ttf", "LiberationSans-Bold.ttf", "Arimo-Bold.ttf", "Arial Bold.ttf"),
    (False, True): ("ariali.ttf", "LiberationSans-Italic.ttf", "Arimo-Italic.ttf", "Arial Italic.ttf"),
    (True, True): ("arialbi.ttf", "LiberationSans-BoldItalic.ttf", "Arimo-BoldItalic.ttf", "Arial Bold Italic.ttf"),
}
_FONT_DIRS = (r"C:\Windows\Fonts", "/usr/share/fonts/truetype/msttcorefonts", "/usr/share/fonts/truetype/liberation",
              "/usr/share/fonts/truetype/liberation2", "/usr/share/fonts/truetype/croscore", "/Library/Fonts",
              "/System/Library/Fonts/Supplemental")


def _in_arial(ch: str) -> bool:
    """Characters Arial (and its metric twins) draw: Latin, Greek, general punctuation, the minus sign and the
    multiplication sign. Others (✓ ▶ ◀ ▾ ▸ ⋮) come from another font in the browser, so they are measured as 1 em."""
    code = ord(ch)
    return code < 0x250 or 0x370 <= code <= 0x3FF or 0x2010 <= code <= 0x2027 or code in (0x2212, 0x20AC, 0x2122)


class TextMeter:
    """Text widths in px, from Arial or a font with its metrics (Liberation Sans, Arimo)."""

    SCALE = 16  # measure at 16x the size, so hinting does not round the advances to whole pixels

    def __init__(self, font_dir: str | os.PathLike | None = None):
        from PIL import ImageFont
        self._ImageFont = ImageFont
        self._fonts: dict[tuple, object] = {}
        directories = [Path(d) for d in ([font_dir] if font_dir else [])
                       + ([os.environ["AA_SVG_FONTS"]] if os.environ.get("AA_SVG_FONTS") else []) + list(_FONT_DIRS)]
        self._paths: dict[tuple[bool, bool], Path] = {}
        for style, names in _FONT_FILES.items():
            for directory in directories:
                found = next((directory / name for name in names if (directory / name).is_file()), None)
                if found:
                    self._paths[style] = found
                    break
            else:
                raise FontMissing(f"No Arial-compatible font for {'bold ' if style[0] else ''}"
                                  f"{'italic' if style[1] else 'regular'} was found (looked for Arial, Liberation Sans "
                                  f"and Arimo in {', '.join(map(str, directories))}). Set AA_SVG_FONTS to a folder with one.")
        self.description = ", ".join(sorted({path.name for path in self._paths.values()}))

    def _font(self, bold: bool, italic: bool, size: float):
        key = (bold, italic, round(size * self.SCALE))
        if key not in self._fonts:
            self._fonts[key] = self._ImageFont.truetype(str(self._paths[(bold, italic)]), round(size * self.SCALE))
        return self._fonts[key]

    def width(self, runs: list[Run], base_size: float) -> float:
        total = 0.0
        for run in runs:
            if run.text == "\n":
                continue
            size = run.size or base_size
            text = re.sub(r"[ \t\r\n]+", " ", run.text)
            known = "".join(ch for ch in text if _in_arial(ch))
            total += self._font(run.bold, run.italic, size).getlength(known) / self.SCALE
            total += size * (len(text) - len(known))
        return total


def stays_html_because(label: Label, meter: TextMeter, margin: float = FIT_MARGIN) -> str | None:
    """Why an HTML label cannot become native text without a change: no <br>, a box wide enough for its text (or
    nowrap), no background or border (Draw.io's conversion drops them, and an edge label would show the line through
    its text), not rotated. None when it can."""
    if label.kind != "html":
        return "not html"
    if not label.runs or label.width is None:
        return "empty"
    if label.has_br:
        return "br"
    if label.background:
        return "background"
    if label.rotated:
        return "rotated"
    if not label.nowrap and meter.width(label.runs, label.size) > label.width - margin:
        return "wraps"
    return None


def fits_on_one_line(label: Label, meter: TextMeter, margin: float = FIT_MARGIN) -> bool:
    """True when this HTML label can become native text without any change (see stays_html_because)."""
    return stays_html_because(label, meter, margin) is None


def single_line_cells(svg_text: str, meter: TextMeter, margin: float = FIT_MARGIN) -> set[str]:
    """The Draw.io cell ids of an export (whose labels are HTML) whose label fits on one line."""
    return {label.cell for label in labels(svg_text) if label.cell and fits_on_one_line(label, meter, margin)}


# ----------------------------------------------------------------------------------------- the converted source


def native_labels_copy(drawio_text: str, cells: set[str] | frozenset[str]) -> str:
    """The .drawio text with Draw.io's "Convert labels to SVG" switched on for the given cells (their ids), so that
    their labels are exported as <text>. Only html=1 cells with a label are changed; the wrap style is copied to
    svgWhiteSpace as Draw.io's own checkbox does. Everything else is byte for byte as it was."""
    def change(match: re.Match[str]) -> str:
        tag = match.group(0)
        identifier = re.search(r'\sid="([^"]*)"', tag)
        style = re.search(r'\sstyle="([^"]*)"', tag)
        value = re.search(r'\svalue="([^"]*)"', tag)
        if not (identifier and style and value and value.group(1)):
            return tag
        tokens = style.group(1).split(";")
        if html.unescape(identifier.group(1)) not in cells or "html=1" not in tokens                 or any(token.startswith("convertToSvg=") for token in tokens):
            return tag
        extra = "convertToSvg=1;" + ("svgWhiteSpace=wrap;" if "whiteSpace=wrap" in tokens else "")
        text = style.group(1) if style.group(1).endswith(";") else style.group(1) + ";"
        return tag.replace(f'style="{style.group(1)}"', f'style="{text}{extra}"', 1)

    return re.sub(r"<mxCell\b[^>]*>", change, drawio_text)
