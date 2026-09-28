"""Building blocks for Excel-style mock figures.

The book prefers mocks drawn from the dataset to screenshots: a mock is rebuilt
from the data on every run of build.py, so its values stay correct when the
dataset changes. These helpers draw the parts of an Excel or Power Query window
in the book's figure style (palette colors, Helvetica, 12 px minimum).
"""

from __future__ import annotations

import re
import zipfile
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

from data import REPO_ROOT
from drawio import (BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, ROW_H, RULE, SMALL, WHITE,
                    Diagram, esc)

BAR_H = 28
XLSX = REPO_ROOT / "datasets" / "CharlesRiver.xlsx"


@lru_cache(maxsize=1)
def workbook_sheets() -> list[str]:
    """Worksheet names of CharlesRiver.xlsx in tab order (read-only, from the file's XML)."""
    with zipfile.ZipFile(XLSX) as z:
        return re.findall(r'<sheet [^>]*name="([^"]+)"', z.read("xl/workbook.xml").decode())


@lru_cache(maxsize=1)
def workbook_tables() -> dict[str, str]:
    """Map each database table to its Excel Table name in CharlesRiver.xlsx (read-only)."""
    names = {}
    with zipfile.ZipFile(XLSX) as z:
        for part in z.namelist():
            if part.startswith("xl/tables/") and part.endswith(".xml"):
                m = re.search(r'displayName="(T\d+_(\w+))"', z.read(part)[:800].decode("utf-8"))
                if m:
                    names[m.group(2)] = m.group(1)
    return names


def tabs_around(active: str, before: int = 3, after: int = 3) -> list[str]:
    """The worksheet tabs near the active one, as Excel shows them when scrolled to it."""
    sheets = workbook_sheets()
    i = sheets.index(active)
    return sheets[max(0, i - before): i + after + 1]


def xround(value: float, places: int = 2) -> float:
    """Round half away from zero, as Excel's ROUND does (Python's round() does not)."""
    text = repr(float(f"{value:.15g}"))
    return float(Decimal(text).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def percentile_inc(values: list[float], p: float) -> float:
    """Excel's PERCENTILE.INC: linear interpolation between closest ranks."""
    ordered = sorted(values)
    h = (len(ordered) - 1) * p
    lo = int(h)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (h - lo) * (ordered[hi] - ordered[lo])


def num(value: float, places: int = 2) -> str:
    return f"{value:,.{places}f}"


def title_bar(d: Diagram, x: float, y: float, w: float, title: str) -> str:
    """The title strip of a window or dialog (part of the mock, not a figure title)."""
    return d.box(f"<b>{esc(title)}</b>", x, y, w, BAR_H, fill=GRAY, stroke=GRAY, color=WHITE,
                 size=SMALL, align="left", rounded=False)


def formula_bar(d: Diagram, x: float, y: float, w: float, name: str, formula: str) -> None:
    """Name Box, the fx label, and the formula."""
    d.box(esc(name), x, y, 90, BAR_H, fill=WHITE, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    d.box("<i>fx</i>", x + 94, y, 30, BAR_H, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL,
          rounded=False)
    d.box(esc(formula), x + 128, y, w - 128, BAR_H, fill=WHITE, stroke=RULE, size=SMALL,
          align="left", rounded=False)


def status_bar(d: Diagram, x: float, y: float, w: float, text: str) -> str:
    return d.box(esc(text), x, y, w, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left",
                 rounded=False)


def sheet_tabs(d: Diagram, x: float, y: float, names: list[str], active: str,
               widths: dict[str, float] | None = None, max_right: float = 860) -> float:
    """Worksheet tabs along the bottom of a workbook window, stopping at max_right.
    Returns the right edge."""
    for name in names:
        w = (widths or {}).get(name, max(70, 8 * len(name) + 20))
        if x + w > max_right:
            assert name != active and active in names[:names.index(name)], (name, active)
            break
        on = name == active
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), x, y, w, 24,
              fill=WHITE if on else GRAY_TINT, stroke=BLUE if on else RULE,
              stroke_width=2 if on else 1, color=BLUE if on else INK, size=SMALL, rounded=False)
        x += w + 2
    return x


def button(d: Diagram, x: float, y: float, w: float, label: str, primary: bool = False) -> str:
    return d.box(f"<b>{esc(label)}</b>" if primary else esc(label), x, y, w, 26,
                 fill=BLUE if primary else WHITE, stroke=BLUE if primary else GRAY,
                 color=WHITE if primary else INK, size=SMALL, rounded=True)


def checkbox(d: Diagram, x: float, y: float, checked: bool) -> None:
    """A 14 px check box; a checked box is filled and carries a check mark."""
    d.vertex("<b>✓</b>" if checked else "",
             f"rounded=0;whiteSpace=wrap;html=1;fillColor={BLUE if checked else WHITE};"
             f"strokeColor={BLUE if checked else GRAY};fontColor={WHITE};fontSize={SMALL};"
             "fontFamily=Helvetica;align=center;verticalAlign=middle;spacing=0;",
             x, y, 14, 14)


def item_icon(d: Diagram, x: float, y: float, kind: str) -> None:
    """Navigator icons: a Table has a colored header strip, a worksheet a plain frame."""
    if kind == "table":
        d.box("", x, y, 16, 12, fill=WHITE, stroke=BLUE, rounded=False)
        d.box("", x, y, 16, 4, fill=BLUE, stroke=BLUE, rounded=False)
    else:
        d.box("", x, y, 16, 12, fill=WHITE, stroke=GRAY, rounded=False)
        d.box("", x + 5, y, 1, 12, fill=GRAY, stroke=GRAY, rounded=False)


CellStyle = Callable[[int, int, str], dict]


def sheet(d: Diagram, x: float, y: float, letters: list[str], widths: list[float],
          rows: list[tuple[str, list[str]]], style: CellStyle | None = None,
          row_h: float = ROW_H, number_color: str = GRAY,
          show_letters: bool = True) -> dict[tuple[int, int], tuple]:
    """A worksheet grid. letters label the columns (widths[0] is the row-number column);
    rows are (row number, cell values). style(r, c, value) may return box() keyword overrides
    for a data cell, where r counts data rows from 0 and c counts columns from 0.
    Returns the geometry (x, y, w, h) of every data cell."""
    xs = [x]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    top = 22 if show_letters else 0
    if show_letters:
        for cx, w, letter in zip(xs, widths, ["", *letters]):
            d.box(esc(letter), cx, y, w, 22, fill=GRAY_TINT, stroke=RULE, color=GRAY,
                  size=SMALL, rounded=False)
    geometry: dict[tuple[int, int], tuple] = {}
    for r, (number, values) in enumerate(rows):
        ry = y + top + r * row_h
        d.box(esc(number), xs[0], ry, widths[0], row_h, fill=GRAY_TINT, stroke=RULE,
              color=number_color, size=SMALL, rounded=False)
        for c, (value, cx, w) in enumerate(zip(values, xs[1:], widths[1:])):
            numeric = value[:1].isdigit() or value[:1] in "-$" and value[1:2].isdigit()
            kwargs = dict(fill=WHITE, stroke=RULE, color=INK, size=SMALL, rounded=False,
                          align="right" if numeric else "left")
            if style:
                kwargs.update(style(r, c, value) or {})
            label = kwargs.pop("label", esc(value))
            d.box(label, cx, ry, w, row_h, **kwargs)
            geometry[(r, c)] = (cx, ry, w, row_h)
    return geometry


def emphasis(d: Diagram, x: float, y: float, w: float, h: float) -> str:
    """The coral outline that marks what a step asks you to look at (a screenshot's red box).
    It sits 2 px outside the marked area, clamped to the 860 px frame."""
    left, top = max(0, x - 2), max(0, y - 2)
    right, bottom = min(860, x + w + 2), y + h + 2
    return d.outline(left, top, right - left, bottom - top, CORAL, width=2.5, front=True)


def select(d: Diagram, x: float, y: float, w: float, h: float) -> str:
    """Excel's selected-cell border, drawn above the grid."""
    return d.outline(x, y, w, h, BLUE, width=2.5, front=True)


def table_view(d: Diagram, x: float, y: float, letters: list[str], widths: list[float],
               headers: list[str], rows: list[tuple[str, list[str]]], row_h: float = ROW_H,
               number_color: str = GRAY, extra: CellStyle | None = None) -> dict:
    """An Excel Table on a worksheet: column letters, row 1 as the blue header row, and banded
    data rows. rows are (row number, values). extra(r, c, value) may add box() overrides for
    data rows, where r counts data rows from 0."""
    body = [("1", headers), *rows]

    def style(r: int, c: int, value: str) -> dict:
        if r == 0:
            return dict(fill=BLUE, stroke=BLUE, color=WHITE, align="left",
                        label=f"<b>{esc(value)}</b>")
        out = dict(fill=WHITE if r % 2 else BLUE_TINT)
        if extra:
            out.update(extra(r - 1, c, value) or {})
        return out

    return sheet(d, x, y, letters, widths, body, style, row_h=row_h, number_color=number_color)


def column_box(geometry: dict, column: int, rows: int) -> tuple[float, float, float, float]:
    """The bounding box of one column of a sheet() grid, from the letter row down."""
    x, y, w, _ = geometry[(0, column)]
    _, y_last, _, h_last = geometry[(rows - 1, column)]
    return x, y - 22, w, y_last + h_last - (y - 22)
