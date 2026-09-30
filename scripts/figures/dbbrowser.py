"""Building blocks for DB Browser for SQLite mock figures (Part III).

Each mock runs the SQL it displays against the dataset (read-only, through data.q)
and draws the result, so the grid, the row count, and the message pane stay
correct when the dataset changes. Everything is drawn in the book's figure style:
palette colors and Helvetica only, with no text below 12 px.
"""

from __future__ import annotations

import re
from collections.abc import Callable

import excel as xl
from check_figures import text_width
from data import q
from drawio import (BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, ROW_H, RULE, SMALL, TEAL,
                    WHITE, Diagram, esc)

FILE = "CharlesRiver_Work.sqlite"
PATH = "C:\\Users\\you\\Documents\\" + FILE   # the title bar shows the full path of the open file
TABS = ["Database Structure", "Browse Data", "Edit Pragmas", "Execute SQL"]
LINE_H = 20
GUTTER = 34
KEYWORDS = {
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "IS", "NULL", "AS", "ORDER", "BY",
    "ASC", "DESC", "LIMIT", "BETWEEN", "LIKE", "DISTINCT", "ROUND", "JOIN", "INNER", "LEFT",
    "ON", "GROUP", "HAVING", "SUM", "COUNT", "AVG", "MIN", "MAX", "CASE", "WHEN", "THEN",
    "ELSE", "END", "WITH", "OVER", "PARTITION", "CREATE", "VIEW", "COALESCE", "UNION", "ALL",
    "EXISTS", "DROP", "IF", "TEMP", "WINDOW", "ROWS", "RANGE", "PRECEDING", "FOLLOWING",
    "UNBOUNDED", "CURRENT", "ROW", "RANK", "DENSE_RANK", "ROW_NUMBER", "LAG", "LEAD",
    "STRFTIME", "DATE", "JULIANDAY",
}
_TOKEN = re.compile(r"(--.*$)|('(?:[^']|'')*')|(\b[A-Za-z_]+\b)|(\s+)|(.)")


def highlight(line: str, in_comment: bool = False) -> tuple[str, bool]:
    """HTML for one line of SQL: keywords in bold blue, text values in teal, comments in
    italic gray. in_comment carries a /* ... */ comment over from the previous line."""
    if in_comment or line.lstrip().startswith("/*"):
        closed = "*/" in line
        lead = len(line) - len(line.lstrip(" "))
        text = "&nbsp;" * lead + esc(line.lstrip(" "))
        return f'<i><font color="{GRAY}">{text}</font></i>', not closed
    out = []
    for comment, string, word, space, other in _TOKEN.findall(line):
        if comment:
            out.append(f'<i><font color="{GRAY}">{esc(comment)}</font></i>')
        elif string:
            out.append(f'<font color="{TEAL}">{esc(string)}</font>')
        elif word:
            out.append(f'<b><font color="{BLUE}">{word}</font></b>' if word.upper() in KEYWORDS
                       and word.isupper() else esc(word))
        else:
            out.append((space or other).replace(" ", "&nbsp;") if space else esc(other))
    return "".join(out), False


def window(d: Diagram, y: float = 0, active: str = "Execute SQL", w: float = 860) -> float:
    """Title bar, main toolbar, and main tabs. Returns the y below the tabs."""
    xl.title_bar(d, 0, y, w, f"DB Browser for SQLite - {PATH}")
    y += 34
    x = 0
    # Write Changes and Revert Changes stay grayed out while no change is pending, which is
    # always the case when only SELECT statements have run.
    for label, width, enabled in [("New Database", 116, True), ("Open Database ▾", 132, True),
                                  ("Write Changes", 122, False), ("Revert Changes", 128, False)]:
        if enabled:
            xl.button(d, x, y, width, label)
        else:
            d.box(esc(label), x, y, width, 26, fill=GRAY_TINT, stroke=RULE, color=GRAY,
                  size=SMALL, rounded=True)
        x += width + 8
    y += 34
    x = 0
    for name in TABS:
        width = max(96, text_width(name, SMALL, True) + 24)
        on = name == active
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), x, y, width, 26,
              fill=WHITE if on else GRAY_TINT, stroke=BLUE if on else RULE,
              stroke_width=2 if on else 1, color=BLUE if on else INK, size=SMALL, rounded=False)
        x += width + 2
    return y + 32


def editor(d: Diagram, x: float, y: float, w: float, sql: str, tab: str = "SQL 1",
           toolbar: bool = True, first_line: int = 1) -> float:
    """The SQL editor of the Execute SQL tab, with line numbers starting at first_line (a
    script scrolled to the query shown). Returns the bottom y. The real toolbar shows icons
    whose names appear as tooltips; the mock writes the names on the buttons."""
    if toolbar:
        bx = x
        for label, width, primary in [("Open SQL file(s)", 124, False),
                                      ("Save SQL file ▾", 124, False),
                                      ("▶ Execute all/selected SQL", 196, True)]:
            xl.button(d, bx, y, width, label, primary=primary)
            bx += width + 8
        y += 32
    d.box(f"<b>{esc(tab)}</b>", x, y, 110, 24, fill=WHITE, stroke=RULE, size=SMALL,
          align="left", rounded=False)
    y += 24
    lines = sql.strip("\n").split("\n")
    height = len(lines) * LINE_H + 8
    d.box("", x, y, GUTTER, height, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.box("", x + GUTTER, y, w - GUTTER, height, fill=WHITE, stroke=RULE, rounded=False)
    in_comment = False
    for i, line in enumerate(lines):
        ly = y + 4 + i * LINE_H
        d.text(str(first_line + i), x, ly, GUTTER - 4, LINE_H, size=SMALL, color=GRAY, align="right",
               valign="middle")
        label, in_comment = highlight(line, in_comment)
        needed = text_width(label, SMALL, False)
        assert needed <= w - GUTTER - 12, f"{d.name}: SQL line too wide ({needed:.0f} px): {line}"
        d.text(label or " ", x + GUTTER + 4, ly, w - GUTTER - 8, LINE_H, size=SMALL,
               valign="middle")
    return y + height


def cell(value: object) -> tuple[str, str, str]:
    """Label, alignment, and color of a result value as DB Browser shows it."""
    if value is None:
        return "<i>NULL</i>", "left", GRAY
    if isinstance(value, float):
        text = f"{value:.15g}"   # SQLite writes a REAL with 15 significant digits,
        if not any(ch in text for ch in ".en"):   # and keeps ".0" on a whole number
            text += ".0"
        return esc(text), "right", INK
    if isinstance(value, int):
        return esc(str(value)), "right", INK
    return esc(value), "left", INK


def results(d: Diagram, x: float, y: float, headers: list[str], widths: list[float],
            rows: list[tuple], first: int = 1,
            style: Callable[[int, int, object], dict] | None = None) -> dict:
    """The result grid: a row-number column, a header row, and one row per result row.
    Returns the geometry (x, y, w, h) of every cell, keyed (row, column) from 0, with
    row -1 for the headers."""
    geometry: dict[tuple[int, int], tuple] = {}
    xs = [x + 40]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    d.box("", x, y, 40, ROW_H, fill=GRAY_TINT, stroke=RULE, rounded=False)
    for c, (head, cx, width) in enumerate(zip(headers, xs, widths)):
        d.box(f"<b>{esc(head)}</b>", cx, y, width, ROW_H, fill=GRAY_TINT, stroke=RULE,
              size=SMALL, align="left", rounded=False)
        geometry[(-1, c)] = (cx, y, width, ROW_H)
    for r, row in enumerate(rows):
        ry = y + (r + 1) * ROW_H
        d.box(str(first + r), x, ry, 40, ROW_H, fill=GRAY_TINT, stroke=RULE, color=GRAY,
              size=SMALL, rounded=False)
        for c, (value, cx, width) in enumerate(zip(row, xs, widths)):
            label, align, color = cell(value)
            kwargs = dict(fill=WHITE, stroke=RULE, color=color, size=SMALL, align=align,
                          rounded=False)
            if style:
                kwargs.update(style(r, c, value) or {})
            d.box(label, cx, ry, width, ROW_H, **kwargs)
            geometry[(r, c)] = (cx, ry, width, ROW_H)
    return geometry


def message(d: Diagram, x: float, y: float, w: float, count: int, first_line: str,
            line: int = 1, error: str | None = None) -> float:
    """The message pane under the result, as DB Browser 3.13 words it: the row count without a
    thousands separator, and always "rows". The real pane adds the time the query took ("in
    9ms"), which the mock leaves out so that rebuilt figures stay stable. line is the editor
    line where the statement starts. With error, the pane is drawn as DB Browser shows a failed
    statement. Returns the bottom y."""
    if error:
        text = (f"Execution finished with errors.<br>Result: {esc(error)}"
                f"<br>At line {line}:<br>{esc(first_line)}")
        d.box(text, x, y, w, 84, fill=CORAL, stroke=CORAL, color=WHITE, size=SMALL,
              align="left", valign="top", rounded=False)
    else:
        text = (f"Execution finished without errors.<br>Result: {count} rows returned"
                f"<br>At line {line}:<br>{esc(first_line)}")
        d.box(text, x, y, w, 84, fill=WHITE, stroke=RULE, size=SMALL, align="left",
              valign="top", rounded=False)
    return y + 84


def run(sql: str) -> tuple[list[str], list[tuple]]:
    """Run the displayed SQL read-only and return its column names and rows."""
    from data import connection
    cursor = connection().execute(sql)
    return [c[0] for c in cursor.description], cursor.fetchall()


def execute_sql(d: Diagram, sql: str, widths: list[float], shown: slice | None = None,
                style: Callable[[int, int, object], dict] | None = None,
                y: float = 0, tab: str = "SQL 1", first_line: int = 1) -> dict:
    """A whole Execute SQL tab: window, editor, result grid, and message pane.
    shown selects the result rows to draw (all of them by default); tab and first_line show
    the query where it sits in a saved script."""
    headers, rows = run(sql)
    y = window(d, y)
    y = editor(d, 0, y, 860, sql, tab=tab, first_line=first_line) + 8
    first = (shown.start or 0) + 1 if shown else 1
    visible = rows[shown] if shown else rows
    geometry = results(d, 0, y, headers, widths, visible, first=first, style=style)
    y += (len(visible) + 1) * ROW_H + 8
    bottom = message(d, 0, y, 860, len(rows), sql.strip().split("\n")[0],
                     line=first_line)
    return dict(headers=headers, rows=rows, geometry=geometry, bottom=bottom)


def emphasize_cells(d: Diagram, geometry: dict, cells: list[tuple[int, int]]) -> None:
    """Outline the bounding box of the given cells, as a screenshot's red box would."""
    boxes = [geometry[c] for c in cells]
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[0] + b[2] for b in boxes)
    bottom = max(b[1] + b[3] for b in boxes)
    xl.emphasis(d, left, top, right - left, bottom - top)


def structure_row(d: Diagram, x: float, y: float, widths: list[float], values: list[str],
                  indent: int = 0, bold: bool = False, fill: str = WHITE) -> None:
    """One row of the Database Structure tree (Name, Type, Schema)."""
    cx = x
    for i, (value, width) in enumerate(zip(values, widths)):
        pad = "&nbsp;" * (4 * indent) if i == 0 else ""
        label = f"<b>{esc(value)}</b>" if bold and i == 0 else esc(value)
        d.box(pad + label, cx, y, width, ROW_H, fill=fill, stroke=RULE, size=SMALL,
              align="left", rounded=False)
        cx += width


class Script:
    """A chapter's saved script as its tutorials build it: a header comment, then each query
    at the end of the script under a one-line comment. queries holds (key, comment, sql)
    tuples. The tutorial mocks show each query where it sits in the script, so the tutorial
    text and these queries must stay identical."""

    def __init__(self, header: str, queries: list[tuple[str, str, str]], tab: str):
        self.header, self.queries, self.tab = header, queries, tab

    def text(self) -> str:
        """The whole script."""
        return "\n\n".join([self.header] + [f"{c}\n{sql}" for _, c, sql in self.queries])

    def location(self, key: str) -> tuple[str, str, int]:
        """The comment, the query, and the editor line of the comment for one query."""
        line = self.header.count("\n") + 3     # the header, a blank line, the first comment
        for k, comment, sql in self.queries:
            if k == key:
                return comment, sql, line
            line += 1 + sql.count("\n") + 2    # comment, query lines, blank line
        raise KeyError(key)

    def mock(self, d: Diagram, key: str, widths: list[float], shown: slice | None = None,
             sql: str | None = None) -> dict:
        """An Execute SQL mock of one query, shown with its comment where it sits in the
        script. sql replaces the saved query, for a step that shows an earlier version."""
        comment, saved, line = self.location(key)
        text = sql or saved
        headers, rows = run(text)
        y = window(d)
        y = editor(d, 0, y, 860, f"{comment}\n{text}", tab=self.tab, first_line=line) + 8
        first = (shown.start or 0) + 1 if shown else 1
        visible = rows[shown] if shown else rows
        geometry = results(d, 0, y, headers, widths, visible, first=first)
        y += (len(visible) + 1) * ROW_H + 8
        bottom = message(d, 0, y, 860, len(rows), text.split("\n")[0], line=line + 1)
        return dict(headers=headers, rows=rows, geometry=geometry, bottom=bottom)


__all__ = ["FILE", "PATH", "TABS", "Script", "highlight", "window", "editor", "results", "message", "run",
           "execute_sql", "emphasize_cells", "structure_row", "BLUE_TINT", "q"]
