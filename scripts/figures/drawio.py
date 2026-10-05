"""Draw.io writer that applies the book's figure design standard.

Every figure sits on a fixed 860 px frame with a white background, so all
figures print at the same scale (about 0.61 pt per px in the PDF and 0.93 px
per px in the HTML column). The palette, font sizes, and line weights below are
the standard described in CONTRIBUTING.md under "Figures".
"""

from __future__ import annotations

import html
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

# Text and dark fills. White text is allowed only on BLUE, TEAL, GRAY, CORAL, and AMBER.
INK = "#2C3E50"
WHITE = "#FFFFFF"
BLUE = "#1A5276"
TEAL = "#117A65"
GRAY = "#5D6D7E"
CORAL = "#B03A2E"
AMBER = "#8A5D00"

# Light fills, used with INK text only.
BLUE_TINT = "#EAF2F8"
TEAL_TINT = "#E8F6F3"
AMBER_TINT = "#FEF5E7"
CORAL_TINT = "#FDEDEC"
GRAY_TINT = "#F2F3F4"

# HIGHLIGHT is a fill for INK text; RULE draws cell borders and dividers.
HIGHLIGHT = "#F39C12"
RULE = "#D5D8DC"

PALETTE = {
    INK, WHITE, BLUE, TEAL, GRAY, CORAL, AMBER,
    BLUE_TINT, TEAL_TINT, AMBER_TINT, CORAL_TINT, GRAY_TINT,
    HIGHLIGHT, RULE,
}

FONT_FAMILY = "Helvetica"
BODY = 13
HEAD = 14
SMALL = 12

FRAME_WIDTH = 860
MAX_HEIGHT = 980
ROW_H = 24
HEADER_H = 30
LINE_WIDTH = 1.5
CROSS_WIDTH = 2.5  # links to another table group: heavier, so they differ in grayscale too
MARKER_SIZE = 10

FONT = f"fontFamily={FONT_FAMILY};"


def esc(value: object) -> str:
    """Escape a data value for use inside an HTML label."""
    return html.escape(str(value), quote=False)


def money(value: float) -> str:
    return f"${value:,.2f}"


def is_number(value: object) -> bool:
    text = str(value).replace(",", "").replace(".", "").replace("$", "").replace("-", "")
    return text.isdigit()


@dataclass
class Table:
    """Geometry and cell ids of an ER table drawn by Diagram.table()."""

    name: str
    x: float
    y: float
    w: float
    id: str
    header: str
    rows: dict[str, str] = field(default_factory=dict)
    row_centers: dict[str, float] = field(default_factory=dict)
    h: float = 0

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def right(self) -> float:
        return self.x + self.w

    def cy(self, column: str) -> float:
        """Vertical center of a column's row."""
        return self.row_centers[column]

    def fy(self, column: str) -> float:
        """A column's row center as a fraction of the table height (for exit and entry points)."""
        return round((self.row_centers[column] - self.y) / self.h, 4)


class Diagram:
    def __init__(self, name: str):
        self.name = name
        self.cells: list[str] = []
        self.front: list[str] = []  # drawn after every other cell, such as emphasis outlines
        self.count = 0
        self.bottom = 0.0
        self.right = 0.0

    # -- low-level cells ------------------------------------------------------

    def _id(self, prefix: str = "c") -> str:
        self.count += 1
        return f"{prefix}{self.count}"

    def _track(self, x: float, y: float, w: float = 0, h: float = 0) -> None:
        self.bottom = max(self.bottom, y + h)
        self.right = max(self.right, x + w)
        if x < 0 or y < 0:
            raise ValueError(f"{self.name}: content at ({x}, {y}) lies outside the frame")

    def vertex(self, value: str, style: str, x: float, y: float, w: float, h: float,
               cid: str | None = None, front: bool = False) -> str:
        cid = cid or self._id()
        self._track(x, y, w, h)
        (self.front if front else self.cells).append(
            f'<mxCell id="{cid}" value="{html.escape(value, quote=True)}" style="{style}" '
            f'vertex="1" parent="1"><mxGeometry x="{x:g}" y="{y:g}" width="{w:g}" '
            f'height="{h:g}" as="geometry"/></mxCell>'
        )
        return cid

    def text(self, value: str, x: float, y: float, w: float, h: float, size: int = BODY,
             color: str = INK, align: str = "left", valign: str = "top", bold: bool = False,
             italic: bool = False) -> str:
        style = (
            f"text;html=1;whiteSpace=wrap;align={align};verticalAlign={valign};fontSize={size};"
            f"fontColor={color};fontStyle={int(bold) + 2 * int(italic)};{FONT}spacing=2;"
            "fillColor=none;strokeColor=none;"
        )
        return self.vertex(value, style, x, y, w, h)

    def box(self, value: str, x: float, y: float, w: float, h: float, fill: str = WHITE,
            stroke: str = RULE, color: str = INK, size: int = BODY, bold: bool = False,
            align: str = "center", valign: str = "middle", rounded: bool = True,
            dashed: bool = False, stroke_width: float = 1, cid: str | None = None) -> str:
        style = (
            f"rounded={int(rounded)};arcSize=6;whiteSpace=wrap;html=1;fillColor={fill};"
            f"strokeColor={stroke};strokeWidth={stroke_width:g};fontColor={color};fontSize={size};"
            f"fontStyle={int(bold)};align={align};verticalAlign={valign};{FONT}"
            f"spacingLeft=6;spacingRight=6;{'dashed=1;dashPattern=6 3;' if dashed else ''}"
        )
        return self.vertex(value, style, x, y, w, h, cid)

    def anchor(self, x: float, y: float) -> str:
        """An invisible point for drawing free-standing line samples."""
        return self.vertex("", "text;html=1;strokeColor=none;fillColor=none;", x, y, 1, 1)

    def outline(self, x: float, y: float, w: float, h: float, color: str, width: float = 3,
                front: bool = False) -> str:
        """An unfilled rectangle. front=True draws it above every other cell, so cells
        created later can never cover part of it."""
        return self.vertex(
            "", f"rounded=0;html=1;fillColor=none;strokeColor={color};strokeWidth={width:g};",
            x, y, w, h, front=front,
        )

    def marker(self, label: str, x: float, y: float, fill: str = BLUE, color: str = WHITE,
               size: float = 24) -> str:
        """A numbered circle used to key callouts to a legend."""
        return self.vertex(
            f"<b>{esc(label)}</b>",
            f"ellipse;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={fill};fontColor={color};"
            f"fontSize={SMALL};{FONT}align=center;verticalAlign=middle;",
            x, y, size, size,
        )

    def container(self, x: float, y: float, w: float, h: float) -> str:
        """An invisible box that edges can attach to."""
        return self.vertex("", "rounded=0;html=1;fillColor=none;strokeColor=none;", x, y, w, h)

    # -- composite shapes -----------------------------------------------------

    def header_box(self, title: str, x: float, y: float, w: float, h: float = HEADER_H,
                   fill: str = BLUE, color: str = WHITE, align: str = "center",
                   size: int = HEAD) -> str:
        return self.box(f"<b>{title}</b>", x, y, w, h, fill=fill, stroke=fill, color=color,
                        size=size, rounded=False, align=align)

    def table(self, name: str, x: float, y: float, rows: list[tuple[str, str]], w: float = 240,
              focus: bool = True, group: str | None = None, caption_below: bool = False) -> Table:
        """An ER table. rows are (marker, column) with marker 'PK', 'FK', 'PK FK', or ''.

        Tables from other groups get a gray header and, when group is given, a caption
        naming the group. The caption sits in the 19 px above the header, or below the
        table when caption_below is set (for tables whose top edge carries lines).
        """
        fill = BLUE if focus else GRAY
        if group and not caption_below:
            self.text(f"<i>{esc(group)}</i>", x, y - 19, w, 18, size=SMALL, color=GRAY,
                      valign="bottom")
        header = self.header_box(esc(name), x, y, w, fill=fill)
        table = Table(name=name, x=x, y=y, w=w, id="", header=header)
        for i, (mark, column) in enumerate(rows):
            tags = []
            if "PK" in mark:
                tags.append(f'<font color="{BLUE}">PK</font>')
            if "FK" in mark:
                tags.append(f'<font color="{AMBER}">FK</font>')
            prefix = f"<b>{' '.join(tags)}</b>&nbsp;&nbsp;" if tags else ""
            label = f"{prefix}{esc(column)}"
            row_y = y + HEADER_H + i * ROW_H
            cid = self.box(label, x, row_y, w, ROW_H, fill=WHITE if i % 2 == 0 else GRAY_TINT,
                           stroke=RULE, size=BODY, bold="PK" in mark, align="left",
                           rounded=False)
            table.rows[column] = cid
            table.row_centers[column] = row_y + ROW_H / 2
        table.h = HEADER_H + len(rows) * ROW_H
        table.id = self.container(x, y, w, table.h)
        if group and caption_below:
            self.text(f"<i>{esc(group)}</i>", x, y + table.h + 1, w, 18, size=SMALL, color=GRAY)
        return table

    def grid(self, x: float, y: float, headers: list[str], widths: list[float],
             rows: list[tuple], header_fill: str = GRAY, highlight: set | None = None,
             row_h: float = ROW_H, header_size: int = SMALL) -> dict[tuple[int, int], str]:
        """A grid of sample rows. highlight holds (row, column) pairs, with rows from 1."""
        ids: dict[tuple[int, int], str] = {}
        xs = [x]
        for width in widths[:-1]:
            xs.append(xs[-1] + width)
        for c, (head, cx, width) in enumerate(zip(headers, xs, widths)):
            ids[(0, c)] = self.box(f"<b>{head}</b>", cx, y, width, row_h, fill=header_fill,
                                   stroke=RULE, color=WHITE, size=header_size, rounded=False)
        for r, row in enumerate(rows, 1):
            for c, (value, cx, width) in enumerate(zip(row, xs, widths)):
                marked = bool(highlight) and (r, c) in highlight
                ids[(r, c)] = self.box(
                    f"<b>{esc(value)}</b>" if marked else esc(value),
                    cx, y + r * row_h, width, row_h,
                    fill=CORAL_TINT if marked else (WHITE if r % 2 else GRAY_TINT),
                    stroke=CORAL if marked else RULE,
                    stroke_width=2 if marked else 1,
                    color=CORAL if marked else INK,
                    size=BODY, rounded=False,
                    align="right" if is_number(value) else "left",
                )
        return ids

    # -- edges ----------------------------------------------------------------

    def edge(self, src: str, tgt: str, start: str = "none", end: str = "none",
             color: str = GRAY, dashed: bool = False, label: str | None = None,
             exit: tuple[float, float] | None = None, entry: tuple[float, float] | None = None,
             points: list[tuple[float, float]] | None = None, width: float = LINE_WIDTH,
             meta: str = "", label_color: str = INK, marker_size: int = MARKER_SIZE) -> str:
        style = (
            f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;startArrow={start};endArrow={end};"
            f"startFill={int(start.startswith('block'))};endFill={int(end.startswith('block'))};startSize={marker_size};"
            f"endSize={marker_size};strokeColor={color};strokeWidth={width:g};fontSize={SMALL};"
            f"fontColor={label_color};{FONT}labelBackgroundColor={WHITE};"
            f"{'dashed=1;dashPattern=6 3;' if dashed else ''}{meta}"
        )
        if exit:
            style += f"exitX={exit[0]:g};exitY={exit[1]:g};exitDx=0;exitDy=0;"
        if entry:
            style += f"entryX={entry[0]:g};entryY={entry[1]:g};entryDx=0;entryDy=0;"
        pts = ""
        if points:
            for px, py in points:
                self._track(px, py)
            pts = '<Array as="points">' + "".join(
                f'<mxPoint x="{px:g}" y="{py:g}"/>' for px, py in points) + "</Array>"
        eid = self._id("e")
        value = html.escape(label, quote=True) if label else ""
        self.cells.append(
            f'<mxCell id="{eid}" value="{value}" style="{style}" edge="1" parent="1" '
            f'source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry">{pts}'
            "</mxGeometry></mxCell>"
        )
        return eid

    def arrow(self, src: str, tgt: str, color: str = GRAY, dashed: bool = False,
              label: str | None = None, **kwargs) -> str:
        return self.edge(src, tgt, start="none", end="blockThin", color=color, dashed=dashed,
                         label=label, **kwargs)

    def line_sample(self, x: float, y: float, length: float = 50, color: str = GRAY,
                    dashed: bool = False, end: str = "none", width: float = LINE_WIDTH) -> None:
        a, b = self.anchor(x, y), self.anchor(x + length, y)
        self.edge(a, b, start="none", end=end, color=color, dashed=dashed, width=width)

    # -- output ---------------------------------------------------------------

    def save(self, path: Path) -> None:
        if self.right > FRAME_WIDTH:
            raise ValueError(f"{self.name}: content reaches x={self.right:g}, beyond {FRAME_WIDTH}")
        height = round(self.bottom + 2)
        if height > MAX_HEIGHT:
            raise ValueError(f"{self.name}: height {height} exceeds {MAX_HEIGHT}")
        frame = (
            '<mxCell id="frame" value="" style="rounded=0;html=1;fillColor=none;strokeColor=none;" '
            f'vertex="1" parent="1"><mxGeometry x="0" y="0" width="{FRAME_WIDTH}" '
            f'height="{height}" as="geometry"/></mxCell>'
        )
        body = "\n        ".join([frame, *self.cells, *self.front])
        xml = (
            '<mxfile host="Electron" version="29.6.6">\n'
            f'  <diagram name="{html.escape(self.name, quote=True)}" id="{path.stem}">\n'
            '    <mxGraphModel dx="1000" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" '
            'connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{FRAME_WIDTH}" pageHeight="{height}" background="{WHITE}" math="0" '
            'shadow="0">\n'
            '      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n'
            f"        {body}\n"
            "      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n"
        )
        # Preserve mtime when source content is unchanged, keeping incremental
        # SVG/PDF exports and authoring previews from doing unnecessary work.
        if path.is_file() and path.read_text(encoding="utf-8") == xml:
            return
        # Editors and file watchers on Windows can hold the file briefly, so retry the swap.
        temp = path.with_name(f".{path.name}.tmp")
        temp.write_text(xml, encoding="utf-8", newline="\n")
        for attempt in range(10):
            try:
                os.replace(temp, path)
                return
            except OSError:
                if attempt == 9:
                    raise
                time.sleep(0.3)
