"""Shared primitives for the instructor figures: layouts the book's generators do not have.

The book's helpers draw interfaces (excel.py, dbbrowser.py, powerbi.py) and ER tables (drawio.Diagram.table).  The
instructor guides also need process flows, boards of cards, decision trees, timelines, labeled matrices and plain
charts.  Every function here draws on a drawio.Diagram in the book's figure style (palette colors, Helvetica, nothing
below 12 px, a 860 px frame) and returns what the caller needs to connect or annotate (cell ids, the bottom y).

Text arguments are HTML labels, as in Diagram.box: pass plain text, or wrap data values with drawio.esc(); <b> and
<br> work.  Geometry is in px on the 860 px frame; nothing may reach x < 0, x > 860 or y > 980.

    flow(d, nodes, ...)             boxes joined by arrows, in a row or a column
    board(d, columns, ...)          columns of cards under colored headers
    decision_tree(d, root, ...)     a question tree: T("question?", [("yes", T("leaf")), ("no", T(...))])
    timeline(d, events, ...)        dated events on an axis
    matrix(d, ...)                  a grid with row and column headings and colored cells
    Plot(d, ...)                    axes, gridlines, points, lines, bars, bands and reference lines
    callout(d, ...), legend(d, ...) a highlighted note and a key
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_figures import text_width  # noqa: E402
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, BODY, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HEAD,  # noqa: E402
                    HIGHLIGHT, INK, RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

LINE_H = 16          # px per line of 13 px text
TINTS = {"blue": (BLUE_TINT, BLUE), "teal": (TEAL_TINT, TEAL), "amber": (AMBER_TINT, AMBER),
         "coral": (CORAL_TINT, CORAL), "gray": (GRAY_TINT, GRAY), "white": (WHITE, RULE)}


def lines_for(value: str, width: float, size: int = BODY, bold: bool = False) -> int:
    """How many lines a label of this width needs (explicit <br> breaks count)."""
    usable = max(width - 16, 20)
    return sum(max(1, math.ceil(text_width(part, size, bold) / usable)) for part in re.split(r"<br\s*/?>", value))


def height_for(value: str, width: float, size: int = BODY, bold: bool = False, pad: float = 12) -> float:
    return lines_for(value, width, size, bold) * (LINE_H if size >= BODY else 15) + pad


def tint(name: str) -> tuple[str, str]:
    """(fill, stroke) of a named tint: blue, teal, amber, coral, gray or white."""
    return TINTS[name]


# -- flows --------------------------------------------------------------------------------------------------------

def node_label(node) -> str:
    if isinstance(node, str):
        return node
    title, *rest = node if isinstance(node, (tuple, list)) else (node["title"], node.get("body", ""))
    body = rest[0] if rest else ""
    return f"<b>{title}</b>" + (f"<br>{body}" if body else "")


def flow(d: Diagram, nodes: list, x: float = 0, y: float = 0, w: float = 860, gap: float = 44,
         vertical: bool = False, node_w: float | None = None, fills: list[str] | None = None,
         labels: list[str | None] | None = None, dashed_links: set[int] | None = None,
         min_h: float = 50, link_color: str = GRAY, widths: list[float] | None = None) -> dict:
    """Boxes joined by arrows.  A node is "text", ("Title", "body") or {"title", "body"}; fills name a tint
    for each node (blue, teal, amber, coral, gray, white); labels[i] sits on the arrow from node i to i + 1;
    dashed_links holds the indexes of arrows drawn dashed (a posting to the ledger, in the book's convention);
    widths sets each box's width in a row (their sum plus the gaps must fit in w).
    Returns {"ids", "boxes" (x, y, w, h each), "bottom"}."""
    n = len(nodes)
    labels = labels or [None] * (n - 1)
    fills = fills or ["blue"] * n
    if vertical:
        bw = node_w or w
    else:
        bw = node_w or (w - gap * (n - 1)) / n
    texts = [node_label(node) for node in nodes]
    ws = widths or [bw] * n
    bh = max([min_h] + [height_for(t, ws[i], BODY) for i, t in enumerate(texts)])
    ids, boxes = [], []
    cursor = x
    for i, text in enumerate(texts):
        bx = x if vertical else cursor
        by = y + i * (bh + gap) if vertical else y
        cursor += ws[i] + gap
        fill, stroke = tint(fills[i])
        ids.append(d.box(text, bx, by, ws[i], bh, fill=fill, stroke=stroke, stroke_width=1.5))
        boxes.append((bx, by, ws[i], bh))
    for i in range(n - 1):
        exit_, entry = ((0.5, 1), (0.5, 0)) if vertical else ((1, 0.5), (0, 0.5))
        d.arrow(ids[i], ids[i + 1], color=link_color, dashed=i in (dashed_links or set()), label=labels[i],
                exit=exit_, entry=entry)
    bottom = boxes[-1][1] + bh if vertical else y + bh
    return {"ids": ids, "boxes": boxes, "bottom": bottom}


def board(d: Diagram, columns: list[tuple[str, list[str], str]], x: float = 0, y: float = 0, w: float = 860,
          gap: float = 14, card_gap: float = 8, header_h: float = 32) -> dict:
    """Columns of cards.  columns are (header, [card text, ...], tint name).  Returns {"cards": [[id]], "bottom"}."""
    n = len(columns)
    cw = (w - gap * (n - 1)) / n
    cards, bottom = [], y
    for c, (head, items, name) in enumerate(columns):
        fill, stroke = tint(name)
        cx = x + c * (cw + gap)
        d.box(f"<b>{head}</b>", cx, y, cw, header_h, fill=stroke if name != "white" else GRAY, stroke=stroke,
              color=WHITE, size=HEAD, rounded=False)
        cy = y + header_h + card_gap
        ids = []
        for text in items:
            h = height_for(text, cw, BODY)
            ids.append(d.box(text, cx, cy, cw, h, fill=fill, stroke=stroke, align="left", rounded=False))
            cy += h + card_gap
        cards.append(ids)
        bottom = max(bottom, cy - card_gap)
    return {"cards": cards, "bottom": bottom}


@dataclass
class T:
    """A node of a decision tree: its text and its branches, each (label on the arrow, child)."""
    text: str
    branches: list[tuple[str, "T"]] = field(default_factory=list)


def _leaves(node: T) -> int:
    return 1 if not node.branches else sum(_leaves(child) for _, child in node.branches)


def _depth(node: T) -> int:
    return 1 + max((_depth(child) for _, child in node.branches), default=0)


def decision_tree(d: Diagram, root: T, x: float = 0, y: float = 0, w: float = 860, level_gap: float = 56,
                  node_w: float | None = None, min_h: float = 44) -> dict:
    """A top-down question tree: questions are blue, leaves (answers) teal.  Leaves share the width equally and
    each parent sits over its children.  Returns {"bottom"}."""
    slot = w / _leaves(root)
    bw = node_w or max(min(slot - 10, 200), 96)
    heights: dict[int, float] = {}

    def measure(node: T, level: int) -> None:
        heights[level] = max(heights.get(level, min_h), height_for(node.text, bw, BODY))
        for _, child in node.branches:
            measure(child, level + 1)

    measure(root, 0)
    tops = [y]
    for level in range(1, _depth(root)):
        tops.append(tops[-1] + heights[level - 1] + level_gap)
    counter = [0]
    bottom = [y]

    def place(node: T, level: int) -> tuple[str, float]:
        if not node.branches:
            cx = x + slot * (counter[0] + 0.5)
            counter[0] += 1
        else:
            kids = [place(child, level + 1) for _, child in node.branches]
            cx = sum(k[1] for k in kids) / len(kids)
        fill, stroke = tint("teal" if not node.branches else "blue")
        h = heights[level]
        cid = d.box(node.text, cx - bw / 2, tops[level], bw, h, fill=fill, stroke=stroke, stroke_width=1.5)
        bottom[0] = max(bottom[0], tops[level] + h)
        if node.branches:
            for (label, _), (child_id, _) in zip(node.branches, kids):
                d.arrow(cid, child_id, label=label, exit=(0.5, 1), entry=(0.5, 0))
        return cid, cx

    place(root, 0)
    return {"bottom": bottom[0]}


# -- timelines ------------------------------------------------------------------------------------------------------

def timeline(d: Diagram, events: list[dict], start: float, end: float, x: float = 0, y: float = 0,
             w: float = 860, ticks: list[tuple[float, str]] | None = None, label_w: float = 150,
             above: float = 110, below: float = 110) -> dict:
    """Events on a horizontal axis from start to end (any numeric scale, for example date ordinals).  An event is
    {"label", "at", "color" (blue, teal, amber, coral), "side" ("above" or "below"; alternates when omitted),
    "level" (0, 1 or 2: how far from the axis)}.  Returns {"x_of", "axis_y", "bottom"}."""
    margin = label_w / 2
    x_of = lambda v: x + margin + (v - start) * (w - 2 * margin) / (end - start)
    axis_y = y + above
    d.box("", x + margin - 10, axis_y - 1, w - 2 * margin + 20, 3, fill=INK, stroke=INK, rounded=False)
    for value, text in ticks or []:
        d.box("", x_of(value) - 0.5, axis_y - 5, 1, 11, fill=INK, stroke=INK, rounded=False)
        d.text(text, x_of(value) - 40, axis_y + 8, 80, 18, size=SMALL, color=GRAY, align="center")
    for i, event in enumerate(events):
        side = event.get("side") or ("above" if i % 2 == 0 else "below")
        level = event.get("level", 0)
        fill, stroke = tint(event.get("color", "blue"))
        ex = x_of(event["at"])
        h = height_for(event["label"], label_w, SMALL)
        if side == "above":
            ly = axis_y - 26 - level * 42 - h
            d.box("", ex - 0.5, ly + h, 1, axis_y - ly - h, fill=stroke, stroke=stroke, rounded=False)
        else:
            ly = axis_y + 34 + level * 42
            d.box("", ex - 0.5, axis_y, 1, ly - axis_y, fill=stroke, stroke=stroke, rounded=False)
        lx = min(max(ex - label_w / 2, x), x + w - label_w)
        d.box(event["label"], lx, ly, label_w, h, fill=fill, stroke=stroke, size=SMALL, stroke_width=1.5)
        d.vertex("", f"ellipse;html=1;fillColor={stroke};strokeColor={WHITE};strokeWidth=1.5;", ex - 6, axis_y - 5,
                 12, 12)
    return {"x_of": x_of, "axis_y": axis_y, "bottom": axis_y + 34 + below}


# -- matrices -------------------------------------------------------------------------------------------------------

def matrix(d: Diagram, col_heads: list[str], row_heads: list[str], cells: list[list[str]], x: float = 0,
           y: float = 0, widths: list[float] | None = None, corner: str = "", colors: dict | None = None,
           row_h: float | None = None, head_fill: str = GRAY) -> dict:
    """A grid with a heading row and a heading column.  widths covers the heading column first; colors maps
    (row, column) to a tint name for a highlighted cell (rows and columns from 0, headings excluded).  A row is as
    tall as its tallest cell.  Returns {"ids": {(r, c): id}, "bottom", "right"}."""
    n = len(col_heads)
    widths = widths or [180] + [(860 - 180 - x) / n] * n
    xs = [x]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    head_h = max(26, max(height_for(f"<b>{t}</b>", widths[c + 1], SMALL) for c, t in enumerate(col_heads)))
    d.box(f"<b>{corner}</b>" if corner else "", xs[0], y, widths[0], head_h, fill=head_fill, stroke=RULE, color=WHITE,
          size=SMALL, rounded=False)
    for c, text in enumerate(col_heads):
        d.box(f"<b>{text}</b>", xs[c + 1], y, widths[c + 1], head_h, fill=head_fill, stroke=RULE, color=WHITE,
              size=SMALL, rounded=False)
    ids, cy = {}, y + head_h
    for r, head in enumerate(row_heads):
        h = row_h or max([26, height_for(f"<b>{head}</b>", widths[0], SMALL)]
                         + [height_for(cells[r][c], widths[c + 1], SMALL) for c in range(n)])
        d.box(f"<b>{head}</b>", xs[0], cy, widths[0], h, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left",
              rounded=False)
        for c in range(n):
            name = (colors or {}).get((r, c))
            fill, stroke = tint(name) if name else (WHITE, RULE)
            ids[(r, c)] = d.box(cells[r][c], xs[c + 1], cy, widths[c + 1], h, fill=fill, stroke=stroke,
                                stroke_width=2 if name else 1, size=SMALL, align="left", rounded=False)
        cy += h
    return {"ids": ids, "bottom": cy, "right": xs[-1] + widths[-1]}


# -- charts ---------------------------------------------------------------------------------------------------------

def compact(value: float) -> str:
    """12,345 as 12K and 1,234,567 as 1.2M; small values keep their digits."""
    a = abs(value)
    if a >= 1e6:
        return f"{value / 1e6:.1f}M".replace(".0M", "M")
    if a >= 1e4:
        return f"{value / 1e3:.0f}K"
    if a >= 1e3:
        return f"{value / 1e3:.1f}K".replace(".0K", "K")
    return f"{value:g}"


class Plot:
    """A chart frame with a value axis, gridlines and tick labels, and the marks that go on it.

    Numeric x (a scatter or a line): pass x_ticks.  Categorical x (columns): pass categories.  y_ticks always sets
    the value axis, whose first and last tick bound the plot.  Draw bands before marks, marks before labels."""

    def __init__(self, d: Diagram, x: float, y: float, w: float, h: float, title: str | None = None,
                 y_ticks: list[float] | None = None, x_ticks: list[float] | None = None,
                 categories: list[str] | None = None, x_fmt: Callable = compact, y_fmt: Callable = compact,
                 x_title: str = "", y_title: str = "", left: float = 58, bottom: float | None = None):
        self.d, self.x, self.y, self.w, self.h = d, x, y, w, h
        d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
        top = y + 14
        if title:
            d.text(f"<b>{title}</b>", x + 8, y + 4, w - 16, 20, size=SMALL)
            top = y + 30
        if y_title:
            d.text(y_title, x + 8, top - 4, w - 16, 18, size=SMALL, color=GRAY)
            top += 26
        bottom = bottom if bottom is not None else (44 if x_title else 26)
        self.px, self.pw = x + left, w - left - 16
        self.py, self.ph = top, y + h - top - bottom
        y_ticks = y_ticks or [0, 1]
        self.ymin, self.ymax = y_ticks[0], y_ticks[-1]
        self.categories = categories
        if categories:
            self.xmin, self.xmax = 0, len(categories)
        else:
            x_ticks = x_ticks or [0, 1]
            self.xmin, self.xmax = x_ticks[0], x_ticks[-1]
        for t in y_ticks:
            ty = self.y_of(t)
            d.box("", self.px, ty, self.pw, 1, fill=RULE, stroke=RULE, rounded=False)
            d.text(y_fmt(t), x + 4, ty - 10, left - 10, 20, size=SMALL, color=GRAY, align="right", valign="middle")
        if categories:
            for i, name in enumerate(categories):
                d.text(name, self.x_of(i) - self.pw / len(categories) / 2, self.py + self.ph + 4,
                       self.pw / len(categories), 18 * lines_for(name, self.pw / len(categories), SMALL) // 1, size=SMALL,
                       color=GRAY, align="center")
        else:
            for t in x_ticks:
                d.text(x_fmt(t), self.x_of(t) - 36, self.py + self.ph + 4, 72, 18, size=SMALL, color=GRAY, align="center")
        if x_title:
            d.text(x_title, self.px, y + h - 22, self.pw, 18, size=SMALL, color=GRAY, align="center")

    def x_of(self, v: float) -> float:
        if self.categories:
            return self.px + (v + 0.5) * self.pw / len(self.categories)
        return self.px + (v - self.xmin) * self.pw / (self.xmax - self.xmin)

    def y_of(self, v: float) -> float:
        return self.py + (self.ymax - v) * self.ph / (self.ymax - self.ymin)

    def band(self, low: float, high: float, color: str = AMBER_TINT) -> None:
        self.d.box("", self.px, self.y_of(high), self.pw, self.y_of(low) - self.y_of(high), fill=color, stroke=color,
                   rounded=False)

    def bars(self, values: list[float], color: str = BLUE, colors: list[str] | None = None,
             labels: list[str] | None = None, ratio: float = 0.6) -> None:
        slot = self.pw / len(values)
        for i, v in enumerate(values):
            c = (colors or [color] * len(values))[i]
            top, base = self.y_of(max(v, 0)), self.y_of(min(v, 0) if self.ymin < 0 else self.ymin)
            self.d.box("", self.px + slot * i + slot * (1 - ratio) / 2, top, slot * ratio, max(base - top, 1),
                       fill=c, stroke=c, rounded=False)
            if labels:
                self.d.text(labels[i], self.px + slot * i, top - 20, slot, 20, size=SMALL, align="center")

    def points(self, pts: list[tuple[float, float]], color: str = BLUE, size: float = 9, shape: str = "ellipse") -> list[str]:
        return [self.d.vertex("", f"{shape};html=1;fillColor={color};strokeColor={WHITE};strokeWidth=1;",
                              self.x_of(px) - size / 2, self.y_of(py) - size / 2, size, size) for px, py in pts]

    def line(self, pts: list[tuple[float, float]], color: str = BLUE, width: float = 2.5, dashed: bool = False) -> None:
        anchors = [self.d.anchor(self.x_of(px), self.y_of(py)) for px, py in pts]
        for a, b in zip(anchors, anchors[1:]):
            self.d.edge(a, b, color=color, width=width, dashed=dashed, meta="edgeStyle=none;")

    def hline(self, value: float, label: str = "", color: str = CORAL, dashed: bool = True) -> None:
        self.line([(self.xmin, value), (self.xmax, value)], color=color, width=2, dashed=dashed)
        if label:
            self.d.text(label, self.px + self.pw - 260, self.y_of(value) - 20, 256, 18, size=SMALL, color=color,
                        align="right", bold=True)

    def vline(self, value: float, label: str = "", color: str = CORAL, dashed: bool = True) -> None:
        self.line([(value, self.ymin), (value, self.ymax)], color=color, width=2, dashed=dashed)
        if label:
            self.d.text(label, self.x_of(value) + 4, self.py, 220, 18, size=SMALL, color=color, bold=True)

    def label(self, text: str, xv: float, yv: float, dx: float = 8, dy: float = -10, w: float = 150,
              color: str = INK, align: str = "left") -> None:
        self.d.text(text, self.x_of(xv) + dx, self.y_of(yv) + dy, w, 18, size=SMALL, color=color, align=align)


# -- notes and keys ---------------------------------------------------------------------------------------------------

def callout(d: Diagram, text: str, x: float, y: float, w: float, color: str = "amber") -> float:
    """A highlighted note with a colored bar on its left.  Returns the bottom y."""
    fill, stroke = tint(color)
    h = height_for(text, w - 8, SMALL, pad=14)
    d.box(text, x, y, w, h, fill=fill, stroke=fill, size=SMALL, align="left", rounded=False)
    d.box("", x, y, 5, h, fill=stroke, stroke=stroke, rounded=False)
    return y + h


def legend(d: Diagram, x: float, y: float, items: list[tuple[str, str, str]], gap: float = 22) -> float:
    """A key.  items are (label, color, kind) with kind box, line or dashed.  Returns the right edge."""
    cx = x
    for label, color, kind in items:
        if kind == "box":
            d.box("", cx, y + 3, 14, 14, fill=color, stroke=color, rounded=False)
            cx += 20
        else:
            d.line_sample(cx, y + 10, 28, color=color, dashed=kind == "dashed", width=2.5)
            cx += 34
        width = text_width(label, SMALL, False) + 8
        d.text(label, cx, y, width, 20, size=SMALL, valign="middle")
        cx += width + gap
    return cx
