"""Instructor figures of Chapter 11 (guides in facts/instructor/guides/chapter-11-analytical-queries/).

Six figures are DB Browser for SQLite mocks of the Execute SQL tab, two are charts and one is a chooser.  A mock quotes
its query from the model answer script (outputs/companion/solutions/Chapter11-exercises-sql/Ex 11.N.sql, the text the
guide quotes), at the editor line where it sits in that script, and runs it read-only, so the grid and the row count come
from the data.  A query that reads a view runs after the view is created as a TEMP view on the read-only connection, as
the verification scripts do.  A long query is drawn as an editor scrolled to part of it; the query still runs in full.
The values in the notes come from the grid or from the guide contexts (ch11.chapter, ch11.g1 to ch11.g6 and the registered
notes ch11.ex1 to ch11.ex6).  DB Browser keeps only the last statement's grid, so each mock runs one query.

Two mocks (IF-11-0-B, IF-11-3-A) show tied rows, and the order in which a window numbers rows that tie is the engine's:
the grid is what SQLite returns on the machine that builds the figure.
"""

from __future__ import annotations

import re

import ctx
import dbbrowser as db
import kit
from check_figures import text_width
from data import connection
from drawio import (AMBER, AMBER_TINT, BLUE, CORAL, FONT, GRAY, GRAY_TINT, INK, ROW_H, RULE, SMALL, TEAL, WHITE, Diagram,
                    esc)
from kit import T

SOLUTIONS = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter11-exercises-sql"
GRID_W = 820            # the 860 px frame less the row-number column of the result grid
CELL_PAD = 20           # a cell wraps its text within about 12 px of its width, so leave room


# -- the model answers ------------------------------------------------------------------------------------------------

def _script(n: int) -> str:
    path = SOLUTIONS / f"Ex 11.{n}.sql"
    if not path.is_file():
        raise SystemExit(f"Model answer not found: {path} (build the solutions first)")
    return path.read_text(encoding="utf-8")


def _solution(n: int, wanted: str) -> tuple[str, str, int]:
    """The comment lines, the SQL and the editor line of the first comment line of the query of Ex 11.n.sql whose
    comment contains `wanted`.  The `-- Result: N rows` remark that the model answer appends to a query's last line is
    left out: a student types the query without it."""
    lines = _script(n).split("\n")
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    for number, line in enumerate(lines + [""], 1):
        if line.strip():
            if not current:
                start = number
            current.append(line)
        elif current:
            blocks.append((start, current))
            current = []
    found = []
    for first, block in blocks:
        if block[0].lstrip().startswith("/*"):
            continue
        k = 0
        while k < len(block) and block[k].startswith("--"):
            k += 1
        comment, sql = block[:k], block[k:]
        if k and sql and wanted in "\n".join(comment):
            sql[-1] = re.sub(r"\s*--\s*Result:.*$", "", sql[-1])
            found.append(("\n".join(comment), "\n".join(sql), first))
    if len(found) != 1:
        raise SystemExit(f"Ex 11.{n}.sql: {len(found)} queries have a comment containing {wanted!r} (expected one)")
    return found[0]


def _temp_view(n: int, name: str) -> str:
    """The CREATE VIEW statement of Ex 11.n.sql for `name`, as a TEMP view: the model answer writes the view into the
    working copy, the figure's read-only run keeps it in the connection's temporary database."""
    m = re.search(rf"CREATE VIEW {name} AS\n(.*?);\s*--\s*Result", _script(n), re.S)
    if not m:
        raise SystemExit(f"Ex 11.{n}.sql: no CREATE VIEW {name}")
    return f"CREATE TEMP VIEW {name} AS\n{m.group(1)}"


def _run(sql: str, setup: tuple | list = ()) -> tuple[list[str], list[tuple]]:
    """Run the displayed SQL on a read-only connection after the setup statements (TEMP views)."""
    con = connection()
    for statement in setup:
        con.execute(statement)
    cursor = con.execute(sql)
    return [c[0] for c in cursor.description], cursor.fetchall()


# -- the Execute SQL mock -----------------------------------------------------------------------------------------------

def _clip(text: str, width: float, pad: float = CELL_PAD) -> str:
    """Cut a cell's text with an ellipsis, as DB Browser elides text wider than its column."""
    room = width - pad
    if text_width(esc(text), SMALL, False) <= room:
        return text
    while text and text_width(esc(text + "…"), SMALL, False) > room:
        text = text[:-1]
    return text.rstrip() + "…"


def _widths(headers: list[str], rows: list[tuple], total: float = GRID_W, stretch: float = 1.5,
            pad: float = CELL_PAD + 2) -> list[float]:
    """Column widths that fit each heading and value, shrunk (the widest column first, its text then clipped) to fit
    the frame, or stretched a little when the result is narrow.  pad is the room a cell keeps beside its text."""
    natural = []
    for c, head in enumerate(headers):
        w = text_width(f"<b>{esc(head)}</b>", SMALL, True)
        for row in rows:
            w = max(w, text_width(db.cell(row[c])[0], SMALL, False))
        natural.append(w + pad)
    if sum(natural) <= total:
        scale = min(total / sum(natural), stretch)
        return _fit([round(w * scale) for w in natural], total)
    widths = list(natural)
    floor = [text_width(f"<b>{esc(h)}</b>", SMALL, True) + pad for h in headers]
    while sum(widths) > total:
        i = max(range(len(widths)), key=lambda c: widths[c] - floor[c])
        assert widths[i] > floor[i], "the result does not fit the frame"
        widths[i] = max(floor[i], widths[i] - min(8, sum(widths) - total))
    return _fit([round(w) for w in widths], total)


def _fit(widths: list[int], total: float) -> list[int]:
    """Take any excess left by rounding off the widest column, so the grid never passes the frame."""
    excess = sum(widths) - total
    if excess > 0:
        widths[max(range(len(widths)), key=lambda c: widths[c])] -= int(excess + 0.999)
    return widths


def _cell(d: Diagram, label: str, x: float, y: float, w: float, h: float, fill: str = WHITE, color: str = INK,
          align: str = "left", spacing: float = 6) -> None:
    """A grid cell with a chosen margin beside its text (Diagram.box keeps 6 px, so a cell wraps within about 12 px of
    its width; a dense grid passes a smaller spacing and keeps its columns narrow)."""
    style = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={RULE};strokeWidth=1;fontColor={color};"
             f"fontSize={SMALL};fontStyle=0;align={align};verticalAlign=middle;{FONT}spacingLeft={spacing:g};"
             f"spacingRight={spacing:g};")
    d.vertex(label, style, x, y, w, h)


def _results(d: Diagram, y: float, headers: list[str], widths: list[float], rows: list[tuple], first: int = 1,
             spacing: float = 6, number_w: float = 40) -> dict:
    """db.results with a smaller margin in each cell and a narrower row-number column.  Returns the geometry (x, y, w, h)
    of every cell, keyed (row, column) from 0, with row -1 for the headings."""
    geometry: dict[tuple[int, int], tuple] = {}
    xs = [number_w]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    _cell(d, "", 0, y, number_w, ROW_H, fill=GRAY_TINT, spacing=spacing)
    for c, (head, cx, width) in enumerate(zip(headers, xs, widths)):
        _cell(d, f"<b>{esc(head)}</b>", cx, y, width, ROW_H, fill=GRAY_TINT, spacing=spacing)
        geometry[(-1, c)] = (cx, y, width, ROW_H)
    for r, row in enumerate(rows):
        ry = y + (r + 1) * ROW_H
        _cell(d, str(first + r), 0, ry, number_w, ROW_H, fill=GRAY_TINT, color=GRAY, align="center", spacing=spacing)
        for c, (value, cx, width) in enumerate(zip(row, xs, widths)):
            label, align, color = db.cell(value)
            _cell(d, label, cx, ry, width, ROW_H, color=color, align=align, spacing=spacing)
            geometry[(r, c)] = (cx, ry, width, ROW_H)
    return geometry


def _mock(d: Diagram, n: int, wanted: str, shown: slice | None = None, lines: slice | None = None, setup=(),
          edit: tuple[str, str] | None = None, comment: str | None = None, tight: bool = False,
          panes: list[slice] | None = None, room: float | None = None) -> dict:
    """The Execute SQL tab with the query of Ex 11.n.sql whose comment contains `wanted`, as a reader sees it after
    selecting the query and clicking Execute all/selected SQL.  The editor is scrolled to the query: it shows the
    comment lines and the query at their line numbers in the script, or only `lines` of them (an editor scrolled
    through a long query, the line numbers kept).  `shown` draws only some rows of the result, as a grid scrolled to
    them (the rows keep their numbers).  `edit` (old, new) replaces one piece of the query, for a variant a guide
    describes, and `comment` the comment lines that go with it.  `tight` keeps a smaller margin in each cell, for a
    result of many columns; `panes` draws a result wider than the frame as one grid for each slice of its columns, the
    later ones after scrolling right.  `room` is the width left for the columns.  Returns the grid and editor geometry
    (`geometry` and `headers` of the first pane, `panes` all of them)."""
    comment_text, sql, line = _solution(n, wanted)
    if comment is not None:
        comment_text = comment
    if edit:
        assert sql.count(edit[0]) == 1, edit
        sql = sql.replace(*edit)
    headers, rows = _run(sql, setup)
    spacing, pad, number_w = (3, 10, 32) if tight else (6, CELL_PAD + 2, 40)
    room = room or 860 - number_w
    y = db.window(d)
    editor_top = y
    full = f"{comment_text}\n{sql}".split("\n")
    n_comment = comment_text.count("\n") + 1
    start = (lines.start or 0) if lines else 0
    drawn = full[lines] if lines else full
    y = db.editor(d, 0, y, 860, "\n".join(drawn), tab=f"Ex 11.{n}.sql", first_line=line + start,
                  selection=slice(max(n_comment - start, 0), None)) + 8
    visible = rows[shown] if shown else rows
    first = (shown.start or 0) + 1 if shown else 1
    built = []
    for k, cols in enumerate(panes or [slice(0, len(headers))]):
        heads, part = headers[cols], [row[cols] for row in visible]
        widths = _widths(heads, part, total=room, pad=pad)
        clipped = [tuple(_clip(v, w, pad) if isinstance(v, str) else v for v, w in zip(row, widths)) for row in part]
        if k:
            d.text("<i>The same rows after scrolling right</i>", 0, y, 860, 18, size=SMALL, color=GRAY)
            y += 22
        if tight or panes or room != 860 - number_w:
            geometry = _results(d, y, heads, widths, clipped, first=first, spacing=spacing, number_w=number_w)
        else:
            geometry = db.results(d, 0, y, heads, widths, clipped, first=first)
        built.append(dict(geometry=geometry, headers=heads, cols=cols))
        y += (len(visible) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0], line=line + n_comment)
    return dict(headers=headers, rows=rows, geometry=built[0]["geometry"], panes=built, bottom=bottom, sql_lines=drawn,
                sql=sql, n_comment=n_comment, editor_top=editor_top, first_line=line + start)


def _line_top(mock: dict, i: int) -> float:
    """The y of line i (from 0) of the text drawn in the editor, below the editor's toolbar and tab."""
    return mock["editor_top"] + 32 + 24 + 4 + i * db.LINE_H


def _outline_lines(d: Diagram, mock: dict, first: int, last: int) -> None:
    """A coral outline around lines first..last of the drawn editor text, inset so that neighbors do not touch."""
    top = _line_top(mock, first)
    d.outline(db.GUTTER + 3, top + 1.5, 860 - db.GUTTER - 6, (last - first + 1) * db.LINE_H - 3, CORAL, width=2.5,
              front=True)


def _find(mock: dict, text: str) -> int:
    """The index of the one drawn editor line that contains `text`."""
    hits = [i for i, line in enumerate(mock["sql_lines"]) if text in line]
    assert len(hits) == 1, (text, hits)
    return hits[0]


def _row(d: Diagram, mock: dict, first: int, last: int | None = None, inset: float = 0, pane: int = 0) -> None:
    """Outline rows first..last of a grid (indexes into the drawn rows), every column of the pane, inset so that two
    outlines on rows with one row between them stay apart."""
    last = first if last is None else last
    geo, c_last = mock["panes"][pane]["geometry"], len(mock["panes"][pane]["headers"]) - 1
    x0, y0, _, _ = geo[(first, 0)]
    x1, y1, w1, h1 = geo[(last, c_last)]
    left, right = x0 - 1 + inset, min(860.0, x1 + w1 + 1 - inset)       # the grid can fill the frame to its edge
    d.outline(left, y0 - 1 + inset, right - left, y1 + h1 - y0 + 2 - 2 * inset, CORAL, width=2.5, front=True)


def _note(d: Diagram, text: str, y: float) -> float:
    height = kit.lines_for(text, 860, SMALL) * 15 + 12
    d.text(f"<i>{text}</i>", 0, y + 8, 860, height, size=SMALL, color=GRAY)
    return y + 8 + height


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _date(value: str) -> str:
    """A date that must not break at its hyphens in a note."""
    return f'<span style="white-space:nowrap">{esc(value)}</span>'


def _word(n: int) -> str:
    """A small count as a word, as the guides write it."""
    return {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
            10: "ten", 11: "eleven", 12: "twelve"}.get(n, str(n))


def _nb(reference: str) -> str:
    """A reference such as 'Tutorial 11.2, Steps 1 and 2' with no line break inside 'Tutorial 11.2,' or 'Steps 1 and 2'."""
    return ", ".join(part.replace(" ", "&nbsp;") for part in reference.split(", "))


# -- IF-11-0-B: tied rows and the two running totals ---------------------------------------------------------------------

def if_11_0_b() -> Diagram:
    """The demonstration of tied rows (the chapter's section on ranking and frames, slide 27, question 11)."""
    peers = ctx.values("ch11.chapter")["peers"]
    comment = ("-- Tied rows: the default window against ROWS UNBOUNDED PRECEDING\n"
               "-- Population: the Furniture items, ten rows; expected: a tied pair shares a rank and a default total")
    sql = ("SELECT ItemCode, StandardLaborHoursPerUnit AS Hours,\n"
           "    RANK() OVER w AS RankNum,\n"
           "    ROW_NUMBER() OVER w AS RowNum,\n"
           "    ROUND(SUM(StandardLaborHoursPerUnit) OVER w, 2) AS DefaultTotal,\n"
           "    ROUND(SUM(StandardLaborHoursPerUnit) OVER\n"
           "        (w ROWS UNBOUNDED PRECEDING), 2) AS FrameTotal\n"
           "FROM Item\n"
           "WHERE ItemGroup = 'Furniture'\n"
           "WINDOW w AS (ORDER BY StandardLaborHoursPerUnit DESC)\n"
           "ORDER BY StandardLaborHoursPerUnit DESC, ItemCode\n"
           "LIMIT 10;")
    headers, rows = _run(sql)
    assert headers == ["ItemCode", "Hours", "RankNum", "RowNum", "DefaultTotal", "FrameTotal"] and len(rows) == 10, headers
    a = peers["pair_row"]                                           # the index of the second row of the first tied pair
    hours = [r[1] for r in rows]
    tied = [i for i in range(1, len(rows)) if hours[i] == hours[i - 1]]
    assert tied[0] == a and tied[1] == tied[0] + 2, (tied, a)
    first, second = rows[a - 1], rows[a]
    assert first[1] == second[1] == peers["pair_hours"] and first[4] == second[4] == peers["pair_default"], (first, second)
    assert first[2] == second[2] == peers["pair_rank"], (first, second)
    assert (first[3], second[3]) == tuple(peers["pair_nums"]) and (first[5], second[5]) == tuple(peers["pair_frame"]), \
        "the grid differs from the guide's tied pair"
    d = Diagram("Tied Rows Under the Default Window")
    widths = _widths(headers, rows)
    y = db.window(d)
    editor_top = y
    y = db.editor(d, 0, y, 860, f"{comment}\n{sql}", tab="SQL 1", first_line=1, selection=slice(2, None)) + 8
    geometry = db.results(d, 0, y, headers, widths, rows)
    y += (len(rows) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0], line=3)
    mock = dict(geometry=geometry, headers=headers, editor_top=editor_top)
    # outline the pair's rows, every column
    x0, y0, _, _ = geometry[(a - 1, 0)]
    x1, y1, w1, h1 = geometry[(a, len(headers) - 1)]
    d.outline(x0 - 1, y0 - 1, x1 + w1 - x0 + 2, y1 + h1 - y0 + 2, CORAL, width=2.5, front=True)
    c = len(rows)
    _note(d, f"Outlined: the first tied pair, {first[0]} and {second[0]}, both {first[1]:g} hours. They share rank {first[2]} and "
             f"the default running total {first[4]:.2f}, because the default window runs through the peers of the current row; "
             f"ROW_NUMBER gives them {first[3]} and {second[3]}, and the ROWS frame totals {first[5]:.2f} and {second[5]:.2f}, in the order "
             f"the window met the pair, which is not the order of the result and can differ between SQLite versions. The grid is the "
             f"first {c} rows of the Furniture items.", bottom)
    return d


# -- IF-11-1-A: the view in statement order -----------------------------------------------------------------------------------

def if_11_1_a() -> Diagram:
    """Exercise 11.1, Step 7: the saved view queried with a CASE in ORDER BY, the statement lines in order."""
    ex, g = ctx.values("ch11.ex1"), ctx.values("ch11.g1")
    shown_lines = 9
    d = Diagram("The Statements in Statement Order")
    mock = _mock(d, 1, "the view in statement order", lines=slice(0, shown_lines),
                 setup=[_temp_view(1, "Ex11_1_IncomeStatement")])
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["StatementLine", "Amount"] and len(rows) == g["n_view_lines"], (headers, len(rows))
    order = re.findall(r"WHEN '([^']+)' THEN \d+", mock["sql"])
    assert [r[0] for r in rows] == order and len(order) == len(rows), "the grid is in the order of the CASE"
    value = {r[0]: r[1] for r in rows}
    ni, assets, total = value["Net income"], value["Total assets"], value["Liabilities, equity, and net income"]
    assert round(ni, 2) == round(ex["ni"], 2) == g["retained"] and round(assets, 2) == round(ex["assets"], 2), (ni, assets)
    assert round(total, 2) == round(ex["le_total"], 2) == round(assets, 2), (total, assets)
    for name in ("Net income", "Total assets"):
        i = [r[0] for r in rows].index(name)
        db.emphasize_cells(d, mock["geometry"], [(i, 0), (i, 1)])
    n_when = sum(1 for line in mock["sql_lines"] if line.lstrip().startswith("WHEN"))
    _note(d, f"Outlined: Net income, {_money(ni)}, the credit of {ex['close2']} to retained earnings, and Total assets, {_money(assets)}, "
             f"which equals the last line, liabilities, equity, and net income. The {len(rows)} lines come back in statement order "
             f"because the CASE in ORDER BY numbers each label from 1 to {len(order)}. The editor is scrolled to the top of the "
             f"query and shows the first {n_when} of its {len(order)} WHEN branches; the rest continue below.", mock["bottom"])
    return d


# -- IF-11-2-A: Furniture's months ranked by the change -------------------------------------------------------------------------

def if_11_2_a() -> Diagram:
    """Exercise 11.2, Step 5: Furniture's twelve months of the last year ranked by the change against the year before."""
    ex, g = ctx.values("ch11.ex2"), ctx.values("ch11.g2")
    d = Diagram("Furniture's Months Ranked by the Change")
    sql_text = _solution(2, "Furniture's months of fiscal")[1]
    n_sql = sql_text.count("\n") + 1
    mock = _mock(d, 2, "Furniture's months of fiscal", lines=slice(2 + n_sql - 10, None))
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["FiscalPeriod", "Revenue", "PriorYear", "PctChange", "DeclineRank"] and len(rows) == 12, (headers, len(rows))
    assert [r[4] for r in rows] == list(range(1, 13)), "twelve distinct ranks"
    down, up = ex["down"], ex["up"]
    first, last = rows[0], rows[-1]
    assert (first[1], first[2], round(first[3] / 100, 3)) == (down["now"], down["before"], round(down["pct"], 3)), first
    assert (last[1], last[2], round(last[3] / 100, 3)) == (up["now"], up["before"], round(up["pct"], 3)), last
    assert first[0] == 10 and last[0] == 11 and down["month"] == "October" and up["month"] == "November"
    _row(d, mock, 0)
    _row(d, mock, 11)
    spct = lambda v: ("−" if v < 0 else "+") + f"{abs(v):.1f}%"
    _note(d, f"Outlined: rank 1, period {first[0]} ({down['month']}), {_money(first[1])} against {_money(first[2])}, {spct(first[3])}, "
             f"the largest decline; and rank {last[4]}, period {last[0]} ({up['month']}), {_money(last[1])} against {_money(last[2])}, "
             f"{spct(last[3])}, the largest increase. The RANK is in the same SELECT as the filter on Furniture and the last year, which is safe "
             f"because the LAG was calculated in the Compared CTE; the editor is scrolled to the foot of the query.", mock["bottom"])
    return d


# -- IF-11-3-A: three ranking functions on tied percentages ----------------------------------------------------------------------

def if_11_3_a() -> Diagram:
    """Exercise 11.3, Step 3: the Requirement (2) query ranked by the rounded margin percentage, where the functions disagree."""
    g = ctx.values("ch11.g3")
    comment = ("-- Requirement (2), variant: the three ranks ordered by the rounded margin percentage\n"
               "-- Population: items with a list price; expected: tied percentages, so the ranks differ")
    edit = ("WINDOW w AS (PARTITION BY ItemGroup ORDER BY UnitMargin DESC)",
            "WINDOW w AS (PARTITION BY ItemGroup ORDER BY MarginPct DESC)")
    _, sql, _ = _solution(3, "Requirement (2), step 1")
    start = next(i for i, line in enumerate(sql.split("\n")) if line.startswith("Ranked AS ("))
    _, rows_all = _run(sql.replace(*edit))
    first_furniture = next(i for i, r in enumerate(rows_all) if r[0] == "Furniture")
    shown = slice(first_furniture, first_furniture + 10)
    d = Diagram("Three Rankings on Tied Percentages")
    mock = _mock(d, 3, "Requirement (2), step 1", shown=shown, lines=slice(2 + start, None), edit=edit, comment=comment,
                 room=808)
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["ItemGroup", "ItemCode", "UnitMargin", "MarginPct", "MarginRank", "MarginDenseRank", "MarginRowNumber"], headers
    assert len(rows) == g["n"] == 223
    differ = sum(1 for r in rows if not (r[4] == r[5] == r[6]))
    assert differ == g["differ"], (differ, g["differ"])
    top3 = sum(1 for r in rows if r[4] <= 3)
    top3_row = sum(1 for r in rows if r[6] <= 3)
    assert (top3, top3_row) == (g["top3_rank"], g["top3_row"]), (top3, top3_row)
    visible = rows[shown]
    pct = [r[3] for r in visible]
    runs, i = [], 0
    while i < len(visible):                                         # the runs of equal percentages among the rows shown
        j = i
        while j + 1 < len(visible) and pct[j + 1] == pct[i]:
            j += 1
        if j > i:
            runs.append((i, j))
        i = j + 1
    longest = max(runs, key=lambda r: r[1] - r[0])
    a, b = longest
    run = visible[a:b + 1]
    assert len({r[4] for r in run}) == 1 and len({r[5] for r in run}) == 1 and len({r[6] for r in run}) == b - a + 1, run
    assert run[0][4] != run[0][5], "RANK and DENSE_RANK differ after an earlier tie"
    assert visible[0][3] == visible[1][3] and visible[0][3] > visible[2][3], "the top two items tie, above the third"
    _row(d, mock, a, b)
    _outline_lines(d, mock, _find(mock, "WINDOW w AS"), _find(mock, "WINDOW w AS"))
    _note(d, f"Outlined: the WINDOW line, the one change from the model script (MarginPct in place of UnitMargin), and the run of "
             f"{_word(b - a + 1)} Furniture items at {run[0][3]:.1f}%: all share RANK {run[0][4]} and DENSE_RANK {run[0][5]}, while ROW_NUMBER "
             f"counts {run[0][6]} to {run[-1][6]}, in an order the query does not control. The top two items tie as well, at "
             f"{visible[0][3]:.1f}%. Over the "
             f"{len(rows)} items the three columns disagree on {differ}, and RANK keeps {top3} rows for the top three where ROW_NUMBER keeps "
             f"{top3_row}. The grid is scrolled to rows {shown.start + 1} to {shown.stop}, the first rows of Furniture, and the editor to "
             f"the Ranked CTE.", mock["bottom"])
    return d


# -- IF-11-5-A: the entries to review --------------------------------------------------------------------------------------------

def if_11_5_a() -> Diagram:
    """Exercise 11.5, Step 4: the journal entries scoring two or more, ranked by score and amount."""
    ex, g = ctx.values("ch11.ex5"), ctx.values("ch11.g5")
    d = Diagram("The Journal Entries to Review First")
    sql_text = _solution(5, "Requirement (4)")[1]
    n_sql = sql_text.count("\n") + 1
    mock = _mock(d, 5, "Requirement (4)", lines=slice(2 + n_sql - 7, None), tight=True, panes=[slice(0, 6), slice(5, 11)])
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["ReviewRank", "EntryNumber", "EntryType", "PostingDate", "TotalAmount", "RiskScore", "Weekend", "Backdated",
                       "SelfApproved", "AboveLimit", "RoundAmount"], headers
    assert len(rows) == g["n_ranked"] and [r[1] for r in rows] == [r[1] for r in g["ranked"]], rows
    assert [r[0] for r in rows] == list(range(1, len(rows) + 1)), "no ties in the review rank"
    assert all(r[5] == sum(r[6:]) and r[5] >= 2 for r in rows)
    top = rows[0]
    assert top[1] == ex["top_entry"] and top[5] == ex["top_score"] == max(r[5] for r in rows), top
    assert [r[5] for r in rows] == sorted((r[5] for r in rows), reverse=True)
    _row(d, mock, 0, pane=0)
    _row(d, mock, 0, pane=1)
    flags = [name for name, v in zip(headers[6:], top[6:]) if v]
    others = sum(1 for r in rows[1:] if r[5] == 2)
    _note(d, f"Outlined: the first row, {top[1]}, the {top[2].lower()} entry, {_money(top[4])}, posted {_date(top[3])}, score {top[5]}: it "
             f"fails {_word(len(flags))} of the five tests ({', '.join(flags)}). The other {_word(len(rows) - 1)} entries score "
             f"{'2' if others == len(rows) - 1 else 'less'} and are ranked by amount; no entry scores 3, so no row has that score. "
             f"A flag is a reason to look, not a finding. The result is wider than the window, so the flag columns are drawn after "
             f"scrolling right; the editor is scrolled to the foot of the query.", mock["bottom"])
    return d


# -- IF-11-6-A: the two runs of equal requisitions ---------------------------------------------------------------------------------

def if_11_6_a() -> Diagram:
    """Exercise 11.6, Step 3: the six requisitions of the two runs of three equal amounts."""
    ex, g = ctx.values("ch11.ex6"), ctx.values("ch11.g6")
    d = Diagram("Two Runs of Three Equal Requisitions")
    sql_text = _solution(6, "each run of three consecutive requisitions")[1]
    n_sql = sql_text.count("\n") + 1
    mock = _mock(d, 6, "each run of three consecutive requisitions", lines=slice(2 + n_sql - 11, None), tight=True)
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["MiddleID", "RequisitionID", "RequisitionNumber", "RequestDate", "Amount", "RequestedByEmployeeID",
                       "ApprovedByEmployeeID", "Status"], headers
    assert len(rows) == g["joined"] == 6 and {r[4] for r in rows} == {ex["amount"]}, rows
    assert [r[0] for r in rows] == [ex["middles"][0]] * 3 + [ex["middles"][1]] * 3, rows
    approver = headers.index("ApprovedByEmployeeID")
    empty = [i for i, r in enumerate(rows) if r[approver] is None]
    assert [rows[i][1] for i in empty] == ex["unapproved"] and len(empty) == 4, empty
    assert {rows[i][approver] for i in range(6) if i not in empty} == {ex["cfo"]}, rows
    assert {r[7] for r in rows} == {"Converted to PO"}
    assert empty == [0, 1, 3, 4], empty
    for pair in ((0, 1), (3, 4)):
        db.emphasize_cells(d, mock["geometry"], [(pair[0], approver), (pair[1], approver)])
    dates = sorted({r[3] for r in rows})
    _note(d, f"Outlined: the four ApprovedByEmployeeID cells that are NULL. Each run of three requisitions for {_money(ex['amount'])} has "
             f"two with no approver, and the third was approved by employee {ex['cfo']}, the chief financial officer; the runs are dated "
             f"{_date(dates[0])} and {_date(dates[1])}, and all six are Converted to PO. MiddleID names the one row that LAG and LEAD flag "
             f"({rows[0][0]} and {rows[3][0]}); the join back lists the neighbors on each side. The editor is scrolled to the foot of the query.",
          mock["bottom"])
    return d


# -- IF-11-0-C: the monthly ratio against the trailing twelve months ----------------------------------------------------------------

def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str = BLUE, width: float = 3, dashed: bool = False) -> None:
    """One edge through the points, drawn straight between them (separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, dashed=dashed, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _dot(d: Diagram, x: float, y: float, size: float, fill: str, stroke: str, width: float = 1.5) -> None:
    d.vertex("", f"ellipse;html=1;fillColor={fill};strokeColor={stroke};strokeWidth={width};", x - size / 2, y - size / 2, size, size)


def if_11_0_c() -> Diagram:
    """The view MonthlyLaborEfficiency: the monthly ratio swings while the trailing figures move slowly (Tutorial 11.3)."""
    from guide_contexts.ch11 import measure
    ch = ctx.values("ch11.chapter")
    t1, t3 = ch["t1"], ch["t3"]
    view = measure(ctx.data())                                      # Month, monthly ratio, TTM direct, indirect, total, overtime share
    assert len(view) == t3["n_view"] and view[0][0] == t3["first_full"], (len(view), view[0])
    months = [r[0] for r in view]
    monthly, direct, indirect, total = ([r[k] for r in view] for k in (1, 2, 3, 4))
    peak_i = max(range(len(view)), key=lambda i: total[i])
    assert months[peak_i] == t3["peak"][0] and total[peak_i] == t3["peak"][4], "the peak of the trailing total"
    assert tuple(view[-1]) == tuple(t3["last"]) and [r for r in view if r[0].endswith("-12")] == [tuple(r) for r in t3["decs"]]
    last = len(view) - 1
    assert t1["last"] > months[last] + "-01" and t1["last"][:7] == months[last], "the last month has records only to the last work date"
    # the largest one-month fall of the monthly ratio and what the trailing total did that month
    fall_i = min(range(1, len(view)), key=lambda i: monthly[i] - monthly[i - 1])
    fall, drift = monthly[fall_i] - monthly[fall_i - 1], total[fall_i] - total[fall_i - 1]
    assert abs(drift) < 0.05 < abs(fall), (fall, drift)
    d = Diagram("The Monthly Ratio Against the Trailing Twelve Months")
    d.text(f"<b>Each month and the trailing twelve months, {months[0]} to {months[-1]}</b>", 0, 0, 860, 20, size=SMALL)
    plot = kit.Plot(d, 0, 26, 650, 396, None, y_ticks=[0, 0.5, 1.0, 1.5, 2.0], x_ticks=[-1, 0, 6, 12, 18, 24, 25],
                    x_fmt=lambda i: months[int(i)] if 0 <= i <= last else "", y_fmt=lambda v: f"{v:.1f}",
                    y_title="Hours per standard hour", bottom=26)
    x_of, y_of = plot.x_of, plot.y_of
    band_x = x_of(last - 0.5)
    d.box("", band_x, plot.py, x_of(last + 0.5) - band_x, plot.ph, fill=AMBER_TINT, stroke=AMBER_TINT, rounded=False)
    series = [("Monthly ratio", monthly, GRAY, 1.5, False), ("Trailing direct", direct, TEAL, 3, False),
              ("Trailing indirect", indirect, AMBER, 3, True), ("Trailing total", total, BLUE, 3.5, False)]
    for name, values, color, width, dashed in series:
        _polyline(d, [(x_of(i), y_of(v)) for i, v in enumerate(values)], color, width, dashed)
    for i, v in enumerate(monthly):
        _dot(d, x_of(i), y_of(v), 6, GRAY, WHITE, 1)
    for name, values, color, width, dashed in series:                # the last point of each series, hollow: provisional
        _dot(d, x_of(last), y_of(values[last]), 13, WHITE, color, 2.5)
    _dot(d, x_of(peak_i), y_of(total[peak_i]), 15, CORAL, WHITE, 1.5)
    right = x_of(last + 0.5)
    d.box(f"<b>Provisional month:</b> records stop on {t1['last']}", right - 292, y_of(0.03) - 24, 292, 24, fill=WHITE, stroke=AMBER,
          stroke_width=1.5, size=SMALL, align="right", rounded=False)
    px, py = x_of(peak_i), y_of(total[peak_i])                      # the peak's label, in the clear space below-left of its point
    d.box(f"<b>Peak {total[peak_i]:.2f}</b>", px + 6 - 70, py + 14, 70, 22, fill=WHITE, stroke=CORAL, stroke_width=1.5, size=SMALL,
          rounded=False)
    # the right-hand labels, one for each line, spread so that none overlaps its neighbor
    wanted = sorted(((y_of(values[last]), name, values[last], color, dashed, width) for name, values, color, width, dashed in series))
    ys = []
    for y, *_ in wanted:
        ys.append(max(y, ys[-1] + 24) if ys else y)
    label_x = 650 + 4
    for y, (_, name, v, color, dashed, width) in zip(ys, wanted):
        d.line_sample(label_x, y, 26, color=color, dashed=dashed, width=width)
        d.text(f"<b>{name}</b> {v:.2f}", label_x + 32, y - 10, 860 - label_x - 32, 20, size=SMALL, valign="middle")
    ly = 26 + 396 + 10
    _dot(d, 7, ly + 10, 14, CORAL, WHITE, 1)
    peak_text = f"Peak of the trailing total: {total[peak_i]:.2f} in {months[peak_i]}"
    d.text(peak_text, 20, ly, text_width(peak_text, SMALL, False) + 8, 20, size=SMALL, valign="middle")
    sx = 20 + text_width(peak_text, SMALL, False) + 8 + 24
    d.box("", sx, ly + 3, 14, 14, fill=AMBER_TINT, stroke=AMBER, rounded=False)
    d.text("Provisional month, drawn with hollow points", sx + 20, ly, 330, 20, size=SMALL, valign="middle")
    _note(d, f"The monthly ratio swings from {min(monthly):.2f} to {max(monthly):.2f}, while the trailing total moves from {total[0]:.2f} to "
             f"its peak and ends at {total[last]:.2f}. In {months[fall_i]} the monthly ratio fell by {abs(fall):.2f}, from {monthly[fall_i - 1]:.2f} to "
             f"{monthly[fall_i]:.2f}, and the trailing total moved by {abs(drift):.2f}: the trailing figure is steady and slow to react. The first "
             f"window includes the start-up month of January 2024. The axis starts at zero.", ly + 24)
    return d


# -- IF-11-4-A: the running share of overtime by rank -----------------------------------------------------------------------------

def if_11_4_a() -> Diagram:
    """Exercise 11.4, Step 2: the cumulative share of the year's manufacturing overtime by the employee's rank."""
    ex, g = ctx.values("ch11.ex4"), ctx.values("ch11.g4")
    comment, sql, _ = _solution(4, "the employees ranked, with a running share")
    headers, rows = _run(sql)
    assert headers == ["EmployeeID", "JobTitle", "OvertimeHours", "OvertimeRank", "RunningShare"] and len(rows) == ex["employees"], headers
    n = len(rows)
    share = [r[4] for r in rows]
    assert share[-1] == 1.0 and share == sorted(share) and [(r[0], r[2]) for r in rows[:5]] == [(t[0], round(t[2], 1)) for t in ex["top"]]
    half = next(i for i, s in enumerate(share, 1) if s >= 0.5)
    assert half == ex["half"] and share[half - 1] == round(g["at_half"], 3) and share[half - 2] == round(g["before_half"], 3), half
    gap = max(s - (i / n) for i, s in enumerate(share, 1))
    top5, top10 = share[4], share[9]
    assert abs(top5 - g["top5"]) < 0.0006 and abs(top10 - g["top10"]) < 0.0006, (top5, top10)
    d = Diagram("The Running Share of Overtime by Rank")
    d.text(f"<b>Cumulative share of the year's manufacturing overtime, employees ranked from the highest total</b>", 0, 0, 860, 20, size=SMALL)
    plot = kit.Plot(d, 0, 26, 840, 420, None, y_ticks=[0, 0.25, 0.5, 0.75, 1.0], x_ticks=[0, 8, 16, 24, 32, 40, 48, 56, 64],
                    x_fmt=lambda v: f"{v:g}", y_fmt=lambda v: f"{v * 100:.0f}%", x_title="Employee's rank by overtime hours (1 = the most)",
                    y_title="Share of all overtime hours", left=60, bottom=48)
    diagonal = [(plot.x_of(0), plot.y_of(0)), (plot.x_of(n), plot.y_of(1))]
    _polyline(d, diagonal, GRAY, 2, dashed=True)
    pts = [(plot.x_of(0), plot.y_of(0))] + [(plot.x_of(i), plot.y_of(s)) for i, s in enumerate(share, 1)]
    _polyline(d, pts, BLUE, 3.5)
    # the rank where the running share passes one half: drop lines to both axes, a marker and its label
    hx, hy = plot.x_of(half), plot.y_of(share[half - 1])
    for a, b in (((hx, hy), (hx, plot.y_of(0))), ((plot.x_of(0), hy), (hx, hy))):
        _polyline(d, [a, b], CORAL, 1.5, dashed=True)
    _dot(d, hx, hy, 16, CORAL, WHITE, 1.5)
    label = d.box(f"<b>Rank {half} of {n} passes one half:</b><br>{share[half - 1] * 100:.1f}% of the overtime ({share[half - 2] * 100:.1f}% one rank earlier)",
                  hx + 34, plot.y_of(0.36), 300, 40, fill=WHITE, stroke=CORAL, stroke_width=1.5, size=SMALL, rounded=False)
    d.edge(label, d.anchor(hx + 8, hy + 8), end="blockThin", color=CORAL, width=1.5, exit=(0, 0.5), meta="edgeStyle=none;")
    ly = 26 + 420 + 10
    cx = kit.legend(d, 0, ly, [("Running share of the year's overtime", BLUE, "line"),
                               ("A perfectly even spread: every employee the same total", GRAY, "dashed")])
    _dot(d, cx + 7, ly + 10, 14, CORAL, WHITE, 1)
    d.text("Where the share passes one half", cx + 20, ly, 220, 20, size=SMALL, valign="middle")
    _note(d, f"{n} employees recorded {ex['total']:,.0f} hours of manufacturing overtime by work date. The curve stays within {gap * 100:.1f} points of "
             f"the diagonal: the five largest totals hold {top5 * 100:.1f}% (an even spread would give {5 / n * 100:.1f}%) and the ten largest "
             f"{top10 * 100:.1f}% ({10 / n * 100:.1f}%). A concentrated pattern would rise steeply and pass one half within a handful of names.",
          ly + 24)
    return d


# -- IF-11-0-A: choosing the SQL feature -----------------------------------------------------------------------------------------------

def if_11_0_a() -> Diagram:
    """A chooser from a question about rows to the SQL feature that answers it (Chapter 11 note)."""
    d = Diagram("Choosing the SQL Feature")
    tree = T("What does the question ask of the rows?", [
        ("", T("Which group does each row belong in?", [
            ("", T("<b>CASE</b><br>Check: every row falls in one category and the categories tie to the ledger.<br>"
                   f"<i>{_nb('Tutorial 11.1, Step 1')}</i>"))])),
        ("", T("How much of a measure for each category, side by side?", [
            ("", T("<b>SUM with CASE</b><br>Check: one row for each month, one column for each source.<br>"
                   f"<i>{_nb('Tutorial 11.1, Step 2')}</i>"))])),
        ("", T("Which period is a row in, and where do the dates stop?", [
            ("", T("<b>Date functions</b><br>Check: the last work date against the month end.<br>"
                   f"<i>{_nb('Tutorial 11.1, Step 3')}</i>"))])),
        ("", T("How does a row compare with the rows around it?", [
            ("", T("<b>Window: partition, order, frame</b><br>Check: the first row has no earlier row; ties share a rank.<br>"
                   f"<i>{_nb('Tutorial 11.2, Steps 1 and 2')}</i>"))])),
        ("", T("Can the steps be named and reused?", [
            ("", T("<b>CTE chain or view</b><br>Check: each step returns every month before the next builds on it.<br>"
                   f"<i>{_nb('Tutorial 11.3, Steps 1 to 4 and 6')}</i>"))])),
    ])
    shot = kit.decision_tree(d, tree, level_gap=34)
    kit.callout(d, "Blue boxes are the questions a student asks of the data; teal boxes are the feature that answers "
                   "and the check that proves it worked.", 0, shot["bottom"] + 14, 860, color="gray")
    return d


FIGURES = {
    "IF-11-0-A": if_11_0_a,
    "IF-11-0-B": if_11_0_b,
    "IF-11-0-C": if_11_0_c,
    "IF-11-1-A": if_11_1_a,
    "IF-11-2-A": if_11_2_a,
    "IF-11-3-A": if_11_3_a,
    "IF-11-4-A": if_11_4_a,
    "IF-11-5-A": if_11_5_a,
    "IF-11-6-A": if_11_6_a,
}
