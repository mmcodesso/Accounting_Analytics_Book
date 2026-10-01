"""Building blocks for Power BI Desktop mock figures (Part IV).

The mocks follow Power BI Desktop 2.158 (September 2026): the views Report, Table, Model,
DAX query and TMDL on the left rail; the Filters, Visualizations and Data panes; and visuals
drawn on the report canvas. Everything is drawn in the book's figure style (palette colors and
Helvetica only, no text below 12 px), so a mock shows Power BI's layout and labels but the
book's colors and type. Where the real interface shows an icon only, the mock writes its name,
as the DB Browser mocks do. Every value a mock shows is passed in by the chapter module, which
computes it from the dataset with data.q, so a rebuild keeps the figures current.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import excel as xl
from check_figures import text_width
from drawio import (AMBER, BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL, WHITE,
                    Diagram, esc)

FILE = "Charles River Reports"
VIEWS = ["Report", "Table", "Model", "DAX query", "TMDL"]
# The position of the Design tab, added in September 2026, is not documented; the author
# checks it against the installed release.
TABS = ["File", "Home", "Insert", "Modeling", "Design", "View", "Optimize", "Help"]
SERIES = [BLUE, AMBER, TEAL, CORAL, GRAY]   # data colors, in order; each pairs with a label
RAIL_W = 72
TAB_H = 26
ROW = 22


# -- numbers --------------------------------------------------------------------------------

def amount(value: float, places: int = 2) -> str:
    """A value in a column formatted with a thousands separator, as Tutorial 13.1 sets it."""
    return f"{value:,.{places}f}"


def units(value: float, unit: str) -> str:
    """An axis or data label with Power BI's display units: K for thousands, M for millions."""
    if unit == "M":
        return f"{value / 1e6:.1f}M"
    if unit == "K":
        return f"{value / 1e3:.0f}K"
    return f"{value:,.0f}"


def nice_ticks(low: float, high: float, count: int = 5) -> list[float]:
    """Round tick values covering low..high, about count of them, as a charting tool picks them."""
    span = max(high - low, 1e-9)
    raw = span / count
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw)
    start = math.floor(low / step) * step
    ticks = []
    value = start
    while value <= high + step * 0.999:
        ticks.append(round(value, 6))
        value += step
    return ticks


# -- window chrome --------------------------------------------------------------------------

@dataclass
class Window:
    """Geometry of a mocked Desktop window: the canvas area and the right-hand panes."""
    top: float
    bottom: float
    canvas_x: float
    canvas_w: float
    panes_x: float = 860
    extra: dict = field(default_factory=dict)


def ribbon(d: Diagram, x: float, y: float, w: float, tab: str, buttons: list[str]) -> float:
    """The ribbon tabs and the buttons of the active tab. Returns the bottom y."""
    cx = x
    for name in TABS:
        width = text_width(esc(name), SMALL, name == tab) + 18
        on = name == tab
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), cx, y, width, TAB_H, fill=WHITE,
              stroke=WHITE, color=BLUE if on else INK, size=SMALL, rounded=False)
        if on:
            d.box("", cx + 4, y + TAB_H - 3, width - 8, 3, fill=BLUE, stroke=BLUE, rounded=False)
        cx += width
    d.box("", x, y + TAB_H, w, 1, fill=RULE, stroke=RULE, rounded=False)
    by = y + TAB_H + 6
    bx = x + 6
    for label in buttons:
        width = text_width(esc(label), SMALL, False) + 20
        if bx + width > x + w:
            break
        xl.button(d, bx, by, width, label)
        bx += width + 6
    d.box("", x, by + 32, w, 1, fill=RULE, stroke=RULE, rounded=False)
    return by + 34


def rail(d: Diagram, x: float, y: float, h: float, active: str) -> None:
    """The bar of views down the left side; the real bar shows icons with tooltips."""
    d.box("", x, y, RAIL_W, h, fill=GRAY_TINT, stroke=RULE, rounded=False)
    for i, name in enumerate(VIEWS):
        on = name == active
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), x + 3, y + 6 + i * 34, RAIL_W - 6, 28,
              fill=WHITE if on else GRAY_TINT, stroke=BLUE if on else GRAY_TINT,
              stroke_width=2 if on else 1, color=BLUE if on else INK, size=SMALL, rounded=True)


def page_tabs(d: Diagram, x: float, y: float, pages: list[str], active: str) -> float:
    """The page tabs below the canvas, with the plus sign that adds a page."""
    cx = x
    for name in pages:
        width = text_width(esc(name), SMALL, name == active) + 22
        on = name == active
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), cx, y, width, 24,
              fill=WHITE, stroke=BLUE if on else RULE, stroke_width=2 if on else 1,
              color=BLUE if on else INK, size=SMALL, rounded=False)
        cx += width + 2
    d.box("<b>+</b>", cx, y, 26, 24, fill=WHITE, stroke=RULE, size=SMALL, rounded=False)
    return cx + 26


def window(d: Diagram, height: float, view: str = "Report", tab: str = "Home",
           buttons: list[str] | None = None, panes: list[str] | None = None,
           pane_w: float = 128, y: float = 0) -> Window:
    """Title bar, ribbon, left rail, and the frames of the right-hand panes. Returns the
    geometry of the canvas area; the caller draws the canvas, the pane contents, and the
    page tabs."""
    xl.title_bar(d, 0, y, 860, f"{FILE} - Power BI Desktop")
    top = ribbon(d, 0, y + 30, 860, tab, buttons or [
        "Get data ▾", "Transform data", "Refresh", "New visual", "Text box", "New measure",
        "Publish"])
    bottom = y + height
    rail(d, 0, top, bottom - top, view)
    panes = panes or []
    panes_x = 860 - pane_w * len(panes)
    for i, name in enumerate(panes):
        px = panes_x + i * pane_w
        d.box("", px, top, pane_w, bottom - top, fill=WHITE, stroke=RULE, rounded=False)
        d.box(f"<b>{esc(name)}</b>", px, top, pane_w, 26, fill=GRAY_TINT, stroke=RULE,
              size=SMALL, align="left", rounded=False)
    return Window(top=top, bottom=bottom, canvas_x=RAIL_W, canvas_w=panes_x - RAIL_W,
                  panes_x=panes_x)


def canvas(d: Diagram, x: float, y: float, w: float, h: float) -> None:
    """The gray area around the report page and the white page itself."""
    d.box("", x, y, w, h, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.box("", x + 8, y + 8, w - 16, h - 16, fill=WHITE, stroke=RULE, rounded=False)


# -- visuals --------------------------------------------------------------------------------

def frame(d: Diagram, x: float, y: float, w: float, h: float, title: str | None,
          selected: bool = False) -> tuple[float, float, float, float]:
    """A visual's container and title. Returns the area inside, below the title."""
    d.box("", x, y, w, h, fill=WHITE, stroke=BLUE if selected else RULE,
          stroke_width=2 if selected else 1, rounded=False)
    if title:
        d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 20, size=SMALL)
        return x + 6, y + 26, w - 12, h - 30
    return x + 6, y + 6, w - 12, h - 12


def card(d: Diagram, x: float, y: float, w: float, h: float, label: str, value: str) -> None:
    """One card of a card visual: the callout value above its label."""
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=True)
    d.text(f"<b>{esc(value)}</b>", x + 4, y + 8, w - 8, 24, size=15, align="center")
    d.text(esc(label), x + 4, y + h - 26, w - 8, 20, size=SMALL, color=GRAY, align="center")


def _value_axis(d: Diagram, x: float, top: float, height: float, ticks: list[float], unit: str,
                label_x: float, align: str = "right", grid_w: float = 0) -> callable:
    """Ticks and gridlines of a vertical value axis. Returns the function from value to y."""
    low, high = ticks[0], ticks[-1]
    y_of = lambda v: top + (high - v) * height / (high - low)
    for t in ticks:
        if grid_w:
            d.box("", x, y_of(t), grid_w, 1, fill=RULE, stroke=RULE, rounded=False)
        d.text(units(t, unit), label_x, y_of(t) - 10, 44, 20, size=SMALL, color=GRAY,
               align=align, valign="middle")
    return y_of


def _category_labels(d: Diagram, xs: list[float], labels: list[str], y: float, every: int,
                     width: float) -> None:
    for i, (cx, label) in enumerate(zip(xs, labels)):
        if i % every == 0:
            d.text(esc(label), cx - width / 2, y, width, 20, size=SMALL, color=GRAY, align="center")


def line_chart(d: Diagram, x: float, y: float, w: float, h: float, title: str | None,
               categories: list[str], series: list[tuple[str, list[float], str]], unit: str,
               ticks: list[float], every: int = 1, legend: bool = False,
               selected: bool = False) -> dict:
    """A line chart: series are (name, values, color); ticks set the value axis, whose first
    tick is where the axis starts. Returns the plot geometry and the y mapping."""
    ix, iy, iw, ih = frame(d, x, y, w, h, title, selected)
    if legend:
        lx = ix
        for name, _, color in series:
            d.box("", lx, iy + 6, 14, 3, fill=color, stroke=color, rounded=False)
            d.text(esc(name), lx + 18, iy - 2, text_width(esc(name), SMALL, False) + 8, 20, size=SMALL)
            lx += text_width(esc(name), SMALL, False) + 34
        iy += 20
        ih -= 20
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 8, ih - 34
    y_of = _value_axis(d, left, top, plot_h, ticks, unit, ix, grid_w=plot_w)
    step = plot_w / len(categories)
    xs = [left + step * (i + 0.5) for i in range(len(categories))]
    for name, values, color in series:
        anchors = [d.anchor(cx, y_of(v)) for cx, v in zip(xs, values)]
        for a, b in zip(anchors, anchors[1:]):
            d.edge(a, b, color=color, width=2.5, meta="edgeStyle=none;")
        for cx, v in zip(xs, values):
            d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={color};", cx - 3,
                     y_of(v) - 3, 6, 6)
    _category_labels(d, xs, categories, top + plot_h + 4, every, step * every)
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of,
                axis_box=(ix, top - 10, 46, plot_h + 20))


def column_chart(d: Diagram, x: float, y: float, w: float, h: float, title: str | None,
                 categories: list[str], values: list[float], unit: str, ticks: list[float],
                 color: str = BLUE, labels: bool = False, every: int = 1) -> dict:
    """A clustered column chart of one series, with an optional data label on each column."""
    ix, iy, iw, ih = frame(d, x, y, w, h, title)
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 8, ih - 34
    y_of = _value_axis(d, left, top, plot_h, ticks, unit, ix, grid_w=plot_w)
    step = plot_w / len(categories)
    xs = []
    for i, v in enumerate(values):
        cx = left + step * i + step * 0.2
        xs.append(cx + step * 0.3)
        d.box("", cx, y_of(v), step * 0.6, y_of(ticks[0]) - y_of(v), fill=color, stroke=color,
              rounded=False)
        if labels:
            d.text(units(v, unit), cx - 10, y_of(v) - 20, step * 0.6 + 20, 20, size=SMALL,
                   align="center")
    _category_labels(d, xs, categories, top + plot_h + 4, every, step * every)
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of)


def bar_chart(d: Diagram, x: float, y: float, w: float, h: float, title: str | None,
              categories: list[str], values: list[float], unit: str, ticks: list[float],
              color: str = BLUE, label_w: float = 90, highlight: str | None = None) -> dict:
    """A clustered bar chart of one series; categories run down the side, sorted as given."""
    ix, iy, iw, ih = frame(d, x, y, w, h, title)
    left, plot_w = ix + label_w, iw - label_w - 10
    top, plot_h = iy + 4, ih - 28
    x_of = lambda v: left + (v - ticks[0]) * plot_w / (ticks[-1] - ticks[0])
    for t in ticks:
        d.box("", x_of(t), top, 1, plot_h, fill=RULE, stroke=RULE, rounded=False)
        d.text(units(t, unit), x_of(t) - 24, top + plot_h + 4, 48, 20, size=SMALL, color=GRAY,
               align="center")
    slot = plot_h / len(categories)
    for i, (name, v) in enumerate(zip(categories, values)):
        by = top + slot * i + slot * 0.2
        d.text(esc(name), ix, by - 2, label_w - 6, 20, size=SMALL, align="right", valign="middle")
        fill = color if highlight in (None, name) else BLUE_TINT
        d.box("", left, by, max(x_of(v) - left, 1), slot * 0.6, fill=fill,
              stroke=color if highlight in (None, name) else RULE, rounded=False)
    return dict(left=left, top=top, width=plot_w, height=plot_h, x_of=x_of)


def combo_chart(d: Diagram, x: float, y: float, w: float, h: float, title: str | None,
                categories: list[str], columns: tuple[str, list[float]],
                line: tuple[str, list[float]], unit: str, ticks: list[float],
                line_unit: str, line_ticks: list[float], every: int = 1) -> dict:
    """A line and clustered column chart with the line on a secondary axis on the right."""
    ix, iy, iw, ih = frame(d, x, y, w, h, title)
    # Legend: the columns and the line, each named.
    d.box("", ix, iy + 4, 12, 12, fill=BLUE, stroke=BLUE, rounded=False)
    d.text(esc(columns[0]), ix + 16, iy - 2, 140, 20, size=SMALL)
    d.box("", ix + 150, iy + 9, 14, 3, fill=AMBER, stroke=AMBER, rounded=False)
    d.text(esc(line[0]), ix + 168, iy - 2, 200, 20, size=SMALL)
    iy += 20
    ih -= 20
    left, plot_w = ix + 48, iw - 104
    top, plot_h = iy + 8, ih - 34
    y_of = _value_axis(d, left, top, plot_h, ticks, unit, ix, grid_w=plot_w)
    y2_of = _value_axis(d, left, top, plot_h, line_ticks, line_unit, left + plot_w + 6,
                        align="left")
    step = plot_w / len(categories)
    xs = []
    for i, v in enumerate(columns[1]):
        cx = left + step * i + step * 0.2
        xs.append(cx + step * 0.3)
        d.box("", cx, y_of(v), step * 0.6, y_of(ticks[0]) - y_of(v), fill=BLUE, stroke=BLUE,
              rounded=False)
    anchors = [d.anchor(cx, y2_of(v)) for cx, v in zip(xs, line[1])]
    for a, b in zip(anchors, anchors[1:]):
        d.edge(a, b, color=AMBER, width=2.5, meta="edgeStyle=none;")
    for cx, v in zip(xs, line[1]):
        d.vertex("", f"rhombus;html=1;fillColor={AMBER};strokeColor={AMBER};", cx - 4,
                 y2_of(v) - 4, 8, 8)
    _category_labels(d, xs, categories, top + plot_h + 4, every, step * every)
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of,
                y2_of=y2_of, right_axis=(left + plot_w + 2, top - 10, 50, plot_h + 20))


def table_visual(d: Diagram, x: float, y: float, headers: list[str], widths: list[float],
                 rows: list[list[str]], total: list[str] | None = None,
                 title: str | None = None) -> dict:
    """A table visual: a header row, the rows, and an optional bold total row. Text columns
    are left-aligned and numbers right-aligned, as Power BI shows them. Returns the geometry
    of every cell, keyed (row, column) with row -1 for the headers."""
    w = sum(widths) + 12
    n = len(rows) + 1 + (1 if total else 0)
    h = n * ROW + (30 if title else 12)
    ix, iy, _, _ = frame(d, x, y, w, h, title)
    geometry = {}
    xs = [ix]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    is_num = lambda v: v[:1].isdigit() or v[:1] == "-" and v[1:2].isdigit()
    for c, (head, cx, width) in enumerate(zip(headers, xs, widths)):
        # A header aligns with its values: right over numbers, left over text.
        right = bool(rows) and is_num(rows[0][c])
        d.box(f"<b>{esc(head)}</b>", cx, iy, width, ROW, fill=WHITE, stroke=WHITE, size=SMALL,
              align="right" if right else "left", rounded=False)
        geometry[(-1, c)] = (cx, iy, width, ROW)
    d.box("", ix, iy + ROW - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, row in enumerate(rows + ([total] if total else [])):
        ry = iy + ROW * (r + 1)
        is_total = total is not None and r == len(rows)
        if is_total:
            d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
        for c, (value, cx, width) in enumerate(zip(row, xs, widths)):
            numeric = value[:1].isdigit() or value[:1] == "-" and value[1:2].isdigit()
            d.box(f"<b>{esc(value)}</b>" if is_total else esc(value), cx, ry, width, ROW,
                  fill=WHITE if r % 2 == 0 or is_total else GRAY_TINT,
                  stroke=WHITE if r % 2 == 0 or is_total else GRAY_TINT, size=SMALL,
                  align="right" if numeric else "left", rounded=False)
            geometry[(r, c)] = (cx, ry, width, ROW)
    return dict(geometry=geometry, bottom=y + h, right=x + w)


def matrix_visual(d: Diagram, x: float, y: float, headers: list[str], widths: list[float],
                  rows: list[tuple[int, str, list[str], str]], title: str | None = None) -> dict:
    """A matrix visual. rows are (level, label, values, state) where level 0 is a top row and
    1 a row under an expanded parent, state is '+' (collapsed), '-' (expanded), or '' (no
    children), and a label of 'Total' marks the bold total row."""
    w = sum(widths) + 12
    h = (len(rows) + 1) * ROW + (30 if title else 12)
    ix, iy, _, _ = frame(d, x, y, w, h, title)
    xs = [ix]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    for c, (head, cx, width) in enumerate(zip(headers, xs, widths)):
        d.box(f"<b>{esc(head)}</b>", cx, iy, width, ROW, fill=WHITE, stroke=WHITE, size=SMALL,
              align="left" if c == 0 else "right", rounded=False)
    d.box("", ix, iy + ROW - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, (level, label, values, state) in enumerate(rows):
        ry = iy + ROW * (r + 1)
        bold = label == "Total" or (level == 0 and state == "-")
        glyph = {"+": "+ ", "-": "– ", "": ""}[state]
        text = "&nbsp;" * (5 * level) + esc(glyph + label)
        d.box(f"<b>{text}</b>" if bold else text, xs[0], ry, widths[0], ROW, fill=WHITE,
              stroke=WHITE, size=SMALL, align="left", rounded=False)
        for value, cx, width in zip(values, xs[1:], widths[1:]):
            d.box(f"<b>{esc(value)}</b>" if bold else esc(value), cx, ry, width, ROW, fill=WHITE,
                  stroke=WHITE, size=SMALL, align="right", rounded=False)
        if label == "Total":
            d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    return dict(bottom=y + h, right=x + w)


def slicer_tiles(d: Diagram, x: float, y: float, title: str, options: list[str],
                 selected: str | None, tile_w: float = 64) -> float:
    """A slicer in the Tile style. Returns its right edge."""
    w = max(len(options) * (tile_w + 4) + 8, text_width(esc(title), SMALL, True) + 16)
    frame(d, x, y, w, 56, title)
    for i, option in enumerate(options):
        on = option == selected
        d.box(f"<b>{esc(option)}</b>" if on else esc(option), x + 6 + i * (tile_w + 4), y + 26,
              tile_w, 24, fill=BLUE if on else WHITE, stroke=BLUE if on else GRAY,
              color=WHITE if on else INK, size=SMALL, rounded=False)
    return x + w


def slicer_dropdown(d: Diagram, x: float, y: float, w: float, title: str, value: str) -> float:
    """A slicer in the Dropdown style. Returns its right edge."""
    frame(d, x, y, w, 56, title)
    d.box(f"{esc(value)}", x + 6, y + 26, w - 12, 24, fill=WHITE, stroke=GRAY, size=SMALL,
          align="left", rounded=False)
    d.text("▾", x + w - 26, y + 28, 18, 20, size=SMALL, color=GRAY, align="center")
    return x + w


# -- Model view -----------------------------------------------------------------------------

@dataclass
class ModelTable:
    name: str
    x: float
    y: float
    w: float
    h: float
    rows: dict[str, float]

    def left(self, column: str | None = None) -> tuple[float, float]:
        return self.x, self.rows[column] if column else self.y + self.h / 2

    def right(self, column: str | None = None) -> tuple[float, float]:
        return self.x + self.w, self.rows[column] if column else self.y + self.h / 2


def model_table(d: Diagram, name: str, x: float, y: float, columns: list[str],
                w: float = 170) -> ModelTable:
    """A table card of Model view: the table name and its columns, without key markers."""
    d.box(f"<b>{esc(name)}</b>", x, y, w, 28, fill=BLUE_TINT, stroke=BLUE, size=SMALL,
          align="left", rounded=False)
    rows = {}
    for i, column in enumerate(columns):
        ry = y + 28 + i * ROW
        d.box(esc(column), x, ry, w, ROW, fill=WHITE, stroke=RULE, size=SMALL, align="left",
              rounded=False)
        rows[column] = ry + ROW / 2
    h = 28 + len(columns) * ROW
    d.box("", x, y, w, h, fill="none", stroke=BLUE, rounded=False)
    return ModelTable(name, x, y, w, h, rows)


def relationship(d: Diagram, one: tuple[float, float], many: tuple[float, float],
                 points: list[tuple[float, float]] | None = None) -> None:
    """A one-to-many relationship as Model view draws it: a line with 1 at the table that holds
    the key, an asterisk at the table that refers to it, and an arrow in the middle pointing in
    the direction the filter flows, from the one side to the many side."""
    path = [one, *(points or []), many]
    # Split the longest segment at its midpoint and put the arrowhead there.
    lengths = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:])]
    k = lengths.index(max(lengths))
    (ax, ay), (bx, by) = path[k], path[k + 1]
    mid = ((ax + bx) / 2, (ay + by) / 2)
    first = [d.anchor(px, py) for px, py in path[:k + 1]] + [d.anchor(*mid)]
    second = [d.anchor(*mid)] + [d.anchor(px, py) for px, py in path[k + 1:]]
    for a, b in zip(first, first[1:]):
        last = b == first[-1]
        d.edge(a, b, color=GRAY, end="blockThin" if last else "none", meta="edgeStyle=none;")
    for a, b in zip(second, second[1:]):
        d.edge(a, b, color=GRAY, meta="edgeStyle=none;")

    def tag(point: tuple[float, float], nxt: tuple[float, float], text: str) -> None:
        dx = 10 if nxt[0] > point[0] else -26 if nxt[0] < point[0] else 4
        dy = -22 if nxt[0] != point[0] else (6 if nxt[1] > point[1] else -24)
        d.text(f"<b>{text}</b>", point[0] + dx, point[1] + dy, 18, 20, size=SMALL, align="center")

    tag(one, path[1], "1")
    tag(many, path[-2], "*")


__all__ = ["FILE", "VIEWS", "TABS", "SERIES", "Window", "amount", "units", "nice_ticks", "ribbon",
           "rail", "page_tabs", "window", "canvas", "frame", "card", "line_chart", "column_chart",
           "bar_chart", "combo_chart", "table_visual", "matrix_visual", "slicer_tiles",
           "slicer_dropdown", "ModelTable", "model_table", "relationship", "ROW", "RAIL_W"]
