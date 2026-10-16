"""Instructor figures of Chapter 12 (guides in facts/instructor/guides/chapter-12-sql-audit-analytics/).

Seven figures are DB Browser for SQLite mocks of the Execute SQL tab, two are charts and one is a flow.  A mock quotes its
query from the model answer script (outputs/companion/solutions/Chapter12-exercises-sql/Ex 12.N.sql, the text the guide
quotes), at the editor line where it sits in that script, and runs it read-only, so the grid and the row count come from
the data.  IF-12-0-B quotes test L4 from Audit.sql as the tutorials leave it (outputs/companion/start-files).  The values
in the notes come from the grid or from the guide contexts (ch12.chapter, ch12.g1 to ch12.g6 and the registered notes
ch12.ex1 to ch12.ex6).  DB Browser keeps only the last statement's grid, so each mock runs one query.  A long query is
drawn as an editor scrolled to its last lines; the query still runs in full.
"""

from __future__ import annotations

import re

import ctx
import dbbrowser as db
import kit
from check_figures import text_width
from data import connection
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, FONT, GRAY, GRAY_TINT, HIGHLIGHT, INK, ROW_H,
                    RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)
from kit import T

SOLUTIONS = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter12-exercises-sql"
AUDIT = ctx.REPO / "outputs" / "companion" / "start-files" / "Chapter12" / "End of Chapter 12" / "Audit.sql"
GRID_W = 820            # the 860 px frame less the row-number column of the result grid
CELL_PAD = 20           # a cell wraps its text within about 12 px of its width, so leave room


# -- the model answers ------------------------------------------------------------------------------------------------

def _blocks(text: str) -> list[tuple[int, list[str]]]:
    """The blank-line separated blocks of a script, each with the editor line of its first line."""
    lines = text.split("\n")
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
    return blocks


def _query(text: str, wanted: str, where: str) -> tuple[str, str, int]:
    """The comment lines, the SQL and the editor line of the first comment line of the one query of the script whose
    comment contains `wanted`.  The `-- Result: N rows` remark that the model answer appends to a query's last line is
    left out: a student types the query without it."""
    found = []
    for first, block in _blocks(text):
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
        raise SystemExit(f"{where}: {len(found)} queries have a comment containing {wanted!r} (expected one)")
    return found[0]


def _solution(n: int, wanted: str) -> tuple[str, str, int]:
    path = SOLUTIONS / f"Ex 12.{n}.sql"
    if not path.is_file():
        raise SystemExit(f"Model answer not found: {path} (build the solutions first)")
    return _query(path.read_text(encoding="utf-8"), wanted, f"Ex 12.{n}.sql")


def _run(sql: str, setup: tuple | list = ()) -> tuple[list[str], list[tuple]]:
    """Run the displayed SQL on a read-only connection after the setup statements."""
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


def _results(d: Diagram, x: float, y: float, headers: list[str], widths: list[float], rows: list[tuple], first: int = 1,
             spacing: float = 6, number_w: float = 40) -> dict:
    """db.results with a smaller margin in each cell and a narrower row-number column, drawn from x.  Returns the
    geometry (x, y, w, h) of every cell, keyed (row, column) from 0, with row -1 for the headings."""
    geometry: dict[tuple[int, int], tuple] = {}
    xs = [x + number_w]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    _cell(d, "", x, y, number_w, ROW_H, fill=GRAY_TINT, spacing=spacing)
    for c, (head, cx, width) in enumerate(zip(headers, xs, widths)):
        _cell(d, f"<b>{esc(head)}</b>", cx, y, width, ROW_H, fill=GRAY_TINT, spacing=spacing)
        geometry[(-1, c)] = (cx, y, width, ROW_H)
    for r, row in enumerate(rows):
        ry = y + (r + 1) * ROW_H
        _cell(d, str(first + r), x, ry, number_w, ROW_H, fill=GRAY_TINT, color=GRAY, align="center", spacing=spacing)
        for c, (value, cx, width) in enumerate(zip(row, xs, widths)):
            label, align, color = db.cell(value)
            _cell(d, label, cx, ry, width, ROW_H, color=color, align=align, spacing=spacing)
            geometry[(r, c)] = (cx, ry, width, ROW_H)
    return geometry


def _mock(d: Diagram, n: int, wanted: str, shown: slice | None = None, lines: slice | None = None, setup=(),
          tight: bool = False, panes: list[slice] | None = None, room: float | None = None) -> dict:
    """The Execute SQL tab with the query of Ex 12.n.sql whose comment contains `wanted`, as a reader sees it after
    selecting the query and clicking Execute all/selected SQL.  The editor is scrolled to the query: it shows the
    comment lines and the query at their line numbers in the script, or only `lines` of them (an editor scrolled
    through a long query, the line numbers kept).  `shown` draws only some rows of the result, as a grid scrolled to
    them (the rows keep their numbers).  `tight` keeps a smaller margin in each cell, for a result of many columns;
    `panes` draws a result wider than the frame as one grid for each slice of its columns, the later ones after
    scrolling right.  `room` is the width left for the columns.  Returns the grid and editor geometry (`geometry` and
    `headers` of the first pane, `panes` all of them)."""
    comment_text, sql, line = _solution(n, wanted)
    headers, rows = _run(sql, setup)
    spacing, pad, number_w = (3, 10, 32) if tight else (6, CELL_PAD + 2, 40)
    room = room or 860 - number_w
    y = db.window(d)
    editor_top = y
    full = f"{comment_text}\n{sql}".split("\n")
    n_comment = comment_text.count("\n") + 1
    start = (lines.start or 0) if lines else 0
    drawn = full[lines] if lines else full
    y = db.editor(d, 0, y, 860, "\n".join(drawn), tab=f"Ex 12.{n}.sql", first_line=line + start,
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
            geometry = _results(d, 0, y, heads, widths, clipped, first=first, spacing=spacing, number_w=number_w)
        else:
            geometry = db.results(d, 0, y, heads, widths, clipped, first=first)
        built.append(dict(geometry=geometry, headers=heads, cols=cols))
        y += (len(visible) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0], line=line + n_comment)
    return dict(headers=headers, rows=rows, geometry=built[0]["geometry"], panes=built, bottom=bottom, sql_lines=drawn,
                sql=sql, n_comment=n_comment, editor_top=editor_top, first_line=line + start)


def _tail(n: int, wanted: str, count: int) -> slice:
    """The lines of the editor that show only the last `count` lines of the query of Ex 12.n.sql."""
    sql = _solution(n, wanted)[1]
    return slice(2 + sql.count("\n") + 1 - count, None)


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


def _column(d: Diagram, mock: dict, name: str, color: str = CORAL, pane: int = 0, inset: float = 0) -> None:
    """Outline a result column, heading and every drawn value, as a screenshot's red box would."""
    geo = mock["panes"][pane]["geometry"]
    c = mock["panes"][pane]["headers"].index(name)
    rows = [r for (r, col) in geo if col == c and r >= 0]
    x0, y0, w0, _ = geo[(-1, c)]
    x1, y1, w1, h1 = geo[(max(rows), c)]
    d.outline(x0 - 1 + inset, y0 - 1 + inset, w0 + 2 - 2 * inset, y1 + h1 - y0 + 2 - 2 * inset, color, width=2.5, front=True)


def _row(d: Diagram, mock: dict, first: int, last: int | None = None, inset: float = 0, pane: int = 0,
         color: str = CORAL) -> None:
    """Outline rows first..last of a grid (indexes into the drawn rows), every column of the pane, inset so that two
    outlines on rows with one row between them stay apart."""
    last = first if last is None else last
    geo, c_last = mock["panes"][pane]["geometry"], len(mock["panes"][pane]["headers"]) - 1
    x0, y0, _, _ = geo[(first, 0)]
    x1, y1, w1, h1 = geo[(last, c_last)]
    left, right = x0 - 1 + inset, min(860.0, x1 + w1 + 1 - inset)       # the grid can fill the frame to its edge
    d.outline(left, y0 - 1 + inset, right - left, y1 + h1 - y0 + 2 - 2 * inset, color, width=2.5, front=True)


def _cells(d: Diagram, mock: dict, cells: list[tuple[int, int]], pane: int = 0, color: str = CORAL) -> None:
    """Outline the bounding box of some cells of a pane (rows and columns from 0, row -1 for the headings)."""
    geo = mock["panes"][pane]["geometry"]
    boxes = [geo[c] for c in cells]
    left, top = min(b[0] for b in boxes), min(b[1] for b in boxes)
    right, bottom = max(b[0] + b[2] for b in boxes), max(b[1] + b[3] for b in boxes)
    d.outline(left - 1, top - 1, right - left + 2, bottom - top + 2, color, width=2.5, front=True)


def _note(d: Diagram, text: str, y: float) -> float:
    height = kit.lines_for(text, 860, SMALL) * 15 + 12
    d.text(f"<i>{text}</i>", 0, y + 8, 860, height, size=SMALL, color=GRAY)
    return y + 8 + height


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _signed(value: float) -> str:
    """-$1,234.50 or +$1,234.50."""
    return ("-" if value < 0 else "+") + f"${abs(value):,.2f}"


def _date(value: str) -> str:
    """A date that must not break at its hyphens in a note."""
    return f'<span style="white-space:nowrap">{esc(value)}</span>'


def _word(n: int) -> str:
    """A small count as a word, as the guides write it."""
    return {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
            10: "ten", 11: "eleven", 12: "twelve"}.get(n, str(n))


def _article(noun: str) -> str:
    return "an" if noun[:1].upper() in "AEIOU" else "a"


def _nb(reference: str) -> str:
    """A reference such as 'Tutorial 12.2, Steps 1 and 2' with no line break inside 'Tutorial 12.2,' or 'Steps 1 and 2'."""
    return ", ".join(part.replace(" ", "&nbsp;") for part in reference.split(", "))


# -- IF-12-1-A: the net effect of cutoff on each year ---------------------------------------------------------------------

def if_12_1_a() -> Diagram:
    """Exercise 12.1, Step 3: test C3, the net effect of revenue cutoff on each fiscal year."""
    ex, g = ctx.values("ch12.ex1"), ctx.values("ch12.g1")
    d = Diagram("The Net Effect of Cutoff on Each Year")
    mock = _mock(d, 1, "test C3:", lines=_tail(1, "test C3:", 14))
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["FiscalYear", "FromYearBefore", "ToNextYear", "NeverInvoiced", "NetEffect"] and len(rows) == g["c3_rows"] == 3, headers
    assert [r[0] for r in rows] == [g["f"], g["p"], g["y"]], rows
    for r in rows:                                                  # the column of the net effect is the three before it
        assert abs(r[4] - (r[1] - r[2] - r[3])) < 0.005, r
    assert abs(rows[0][4]) == ex["eff1"] and abs(rows[1][4] - ex["eff2"]) < 0.005 and abs(abs(rows[2][4]) - ex["eff3"]) < 1, rows
    assert rows[0][4] < 0 < rows[1][4] and rows[2][4] < 0, "understated, overstated, understated"
    assert abs(rows[2][1] - g["no_unbilled"]) < 0.005 and rows[2][3] > rows[2][1], "without the unbilled shipments the last year reads positive"
    _column(d, mock, "NetEffect")
    a, b, c = rows
    _note(d, f"Outlined: the NetEffect column, revenue received from the year before, less revenue moved on, less revenue never billed: "
             f"{_signed(a[4])} in {a[0]}, {_signed(b[4])} in {b[0]} and {_signed(c[4])} in {c[0]}. A negative figure is revenue recorded below the "
             f"year's deliveries. The last sign comes from the unbilled shipments: without them {c[0]} would read {_signed(c[1])}. "
             f"The editor is scrolled to the foot of the query: the end of the Effects CTE and the final SELECT.", mock["bottom"])
    return d


# -- IF-12-2-A: the open invoices against account 1020 ------------------------------------------------------------------------

def if_12_2_a() -> Diagram:
    """Exercise 12.2, Step 3: test A3, the open invoices reconciled to account 1020."""
    ex, g = ctx.values("ch12.ex2"), ctx.values("ch12.g2")
    d = Diagram("The Open Invoices Against Account 1020")
    mock = _mock(d, 2, "test A3:", lines=_tail(2, "test A3:", 16))
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["OpenInvoices", "Account1020", "Difference", "OpeningEntryLine"] and len(rows) == 1, (headers, len(rows))
    open_, ledger, diff, opening = rows[0]
    assert (round(open_, 2), round(ledger, 2)) == (round(ex["total"], 2), round(ex["ledger"], 2)) and round(open_, 2) == round(g["a3"][0], 2), rows
    assert diff == opening == round(ex["difference"], 2) and round(ledger - open_, 2) == diff, "the difference is the opening line"
    _cells(d, mock, [(-1, 2), (0, 3)])
    _note(d, f"Outlined: Difference and OpeningEntryLine, both {_money(diff)}. The {g['n_a1']:,} open invoices total {_money(open_)} and account 1020 "
             f"holds {_money(ledger)}; the whole difference is one line of {ex['entry']}, the opening balance that no invoice supports, a finding "
             f"to investigate and not an error to correct. The editor is scrolled to the Ledger CTE and the final SELECT.", mock["bottom"])
    return d


# -- IF-12-3-A: the two work-center ratios -------------------------------------------------------------------------------------

def if_12_3_a() -> Diagram:
    """Exercise 12.3, Step 2: test T2, recorded per planned hour on all hours and on the time recorded while open."""
    ex, g = ctx.values("ch12.ex3"), ctx.values("ch12.g3")
    comment, sql, _ = _solution(3, "test T2:")
    _, rows_all = _run(sql)
    first_last = next(i for i, r in enumerate(rows_all) if r[0] == str(g["y"]))
    shown = slice(first_last, first_last + 5)
    d = Diagram("Recorded and Open Hours per Planned Hour")
    mock = _mock(d, 3, "test T2:", shown=shown, lines=_tail(3, "test T2:", 15))
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["EndYear", "WorkCenterName", "Planned", "Recorded", "WhileOpen", "RecordedPerPlanned", "OpenPerPlanned"], headers
    assert len(rows) == g["n_t2"] == 15 and [r[0] for r in rows[shown]] == [str(g["y"])] * 5, rows
    last = rows[shown]
    packing = next(i for i, r in enumerate(last) if r[1].startswith("Packing"))
    qa = next(i for i, r in enumerate(last) if r[1].startswith("Quality"))
    assert [r[1] for r in last] == [r[1] for r in g["last"]] and [r[5] for r in last] == [r[5] for r in g["last"]], last
    assert last[packing][5] == round(ex["now_all"][3], 2) and last[packing][6] == round(ex["now"][3], 2), last[packing]
    assert all(r[6] < 1 for r in last) and last[packing][5] > 4 and last[packing][6] < 0.25, "Packing: far above plan on all hours, below it while open"
    _row(d, mock, packing)
    p, q = last[packing], last[qa]
    _note(d, f"Outlined: the Packing row. In {p[0]} it recorded {p[3]:,.0f} hours against {p[2]:,.0f} planned, {p[5]:.2f} times the plan, but only "
             f"{p[4]:,.0f} of them while its operations were open: {p[6]:.2f} times. Every work center is below plan on that second ratio; Quality "
             f"Assurance, with {q[2]:,.0f} planned hours, {q[3]:,.0f} recorded and {q[4]:,.0f} while open, reads {q[5]:.2f} and {q[6]:.2f}. The grid is "
             f"scrolled to rows {shown.start + 1} to {shown.stop}, the work centers of {p[0]}; the editor to the derived table and the final GROUP BY.",
          mock["bottom"])
    return d


# -- IF-12-4-A: overtime on surge days and on other days --------------------------------------------------------------------------

def if_12_4_a() -> Diagram:
    """Exercise 12.4, Step 5: test O5, manufacturing overtime on surge days and on other days, by year."""
    ex, g = ctx.values("ch12.ex4"), ctx.values("ch12.g4")
    d = Diagram("Overtime on Surge Days and Other Days")
    mock = _mock(d, 4, "test O5:", lines=_tail(4, "test O5:", 13))
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["WorkYear", "SurgeDayOvertime", "OtherDayOvertime", "Overtime"] and len(rows) == 3, headers
    assert [r[1] for r in rows] == [round(v) for v in ex["surge"]] and [r[2] for r in rows] == [round(v) for v in ex["other"]], rows
    assert all(r[3] == r[1] + r[2] for r in rows) and rows[0][1] < rows[1][1] < rows[2][1], "the surge-day overtime rises"
    assert max(r[2] for r in rows) - min(r[2] for r in rows) < 0.1 * rows[0][2], "the other-day overtime is flat"
    _column(d, mock, "SurgeDayOvertime", CORAL, inset=1.5)
    _column(d, mock, "OtherDayOvertime", TEAL, inset=1.5)
    s, o = [r[1] for r in rows], [r[2] for r in rows]
    _note(d, f"Outlined: SurgeDayOvertime (coral), {s[0]:,.0f}, {s[1]:,.0f} and {s[2]:,.0f} hours in {rows[0][0]}, {rows[1][0]} and {rows[2][0]}, and "
             f"OtherDayOvertime (teal), {o[0]:,.0f}, {o[1]:,.0f} and {o[2]:,.0f}. Overtime on surge days grew by {s[2] - s[0]:,.0f} hours while overtime on "
             f"other days moved by {o[2] - o[0]:+,.0f}: all the growth sits on days that one approver, the {g['o4'][0]}, approved. The LEFT JOIN to "
             f"SurgeDays keeps the other days; the editor is scrolled to the final SELECT.", mock["bottom"])
    return d


# -- IF-12-5-A: the registers paid after the termination date ----------------------------------------------------------------------

def if_12_5_a() -> Diagram:
    """Exercise 12.5, Step 1: test R1, the registers paid after the employee's termination date."""
    ex, g = ctx.values("ch12.ex5"), ctx.values("ch12.g5")
    d = Diagram("Registers Paid After Termination")
    mock = _mock(d, 5, "test R1:", lines=_tail(5, "test R1:", 14), tight=True, panes=[slice(0, 6), slice(5, 12)])
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["PayrollRegisterID", "EmployeeID", "JobTitle", "EmployeeCenter", "RegisterCenter", "TerminationDate", "PeriodStartDate",
                       "PeriodEndDate", "PayDate", "GrossPay", "UsualGrossPay", "Payments"], headers
    assert len(rows) == g["r1_rows"] == 3 and [r[0] for r in rows] == [a["id"] for a in ex["after"]], rows
    assert {r[1] for r in rows} == {ex["emp"]} and {r[5] for r in rows} == {ex["terminated"]} and {r[9] for r in rows} == {ex["gross"]}, rows
    assert {r[10] for r in rows} == {ex["usual"]} and all(r[8] > r[5] for r in rows), rows
    assert [r[3] for r in rows] == [ex["center"]] * 3 and {r[4] for r in rows} == {ex["charged"]}, rows
    assert [r[11] for r in rows] == [1, 0, 0] and rows[0][6] < rows[0][5] < rows[0][7], "register 840's period holds the termination date"
    gross, usual = headers.index("GrossPay"), headers.index("UsualGrossPay")
    pane2 = mock["panes"][1]["headers"]
    _cells(d, mock, [(0, pane2.index("GrossPay")), (0, pane2.index("UsualGrossPay"))], pane=1)
    first, times = rows[0], rows[0][9] / rows[0][10]
    _note(d, f"Outlined: GrossPay and UsualGrossPay of the first row, register {first[0]}: {_money(first[9])} against {_money(first[10])}, "
             f"{times:.1f} times the usual pay, for employee {first[1]}, {_article(first[2])} {first[2]} of the {first[3]} cost center, terminated {_date(first[5])} "
             f"and paid on {_date(first[8])}. All {_word(len(rows))} registers pay the same {_money(first[9])}, charged to the {first[4]} cost center, "
             f"and only the first has a payment record. The result is wider than the window, so the later columns are drawn after scrolling "
             f"right; the editor is scrolled to the foot of the query.", mock["bottom"])
    return d


# -- IF-12-6-A: the first-digit result for three groups ----------------------------------------------------------------------------

MAD_READING = [(0.006, "close conformity"), (0.012, "acceptable conformity"), (0.015, "marginally acceptable conformity"),
               (float("inf"), "nonconformity")]          # the bands of the first-digit table of Chapter 8


def _reading(mad: float) -> str:
    return next(name for limit, name in MAD_READING if mad <= limit)


def if_12_6_a() -> Diagram:
    """Exercise 12.6, Step 7: test B1, the first-digit mean absolute deviation of three groups of payments."""
    ex, g = ctx.values("ch12.ex6"), ctx.values("ch12.g6")
    d = Diagram("First Digits of the Supplier Payments")
    mock = _mock(d, 6, "test B1:", lines=_tail(6, "test B1:", 16))
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["PaymentGroup", "Payments", "Digits", "MAD"] and [tuple(r) for r in rows] == [tuple(r) for r in g["b1"]], (headers, rows)
    assert [r[0] for r in rows] == ["All payments", "Full payments", "Partial payments"] and all(r[2] == 9 for r in rows), rows
    assert [r[3] for r in rows] == [round(ex["mad_all"], 5), round(ex["mad_full"], 5), round(ex["mad_partial"], 5)], rows
    assert rows[0][1] == rows[1][1] + rows[2][1], "the two groups make up all the payments"
    partial = [r[0] for r in rows].index("Partial payments")
    assert _reading(rows[partial][3]) == "nonconformity" and all(_reading(r[3]) != "nonconformity" for r in rows[:partial]), rows
    data = ctx.data()
    smallest = data.one("SELECT MIN(pi.GrandTotal) FROM DisbursementPayment AS dp INNER JOIN PurchaseInvoice AS pi "
                        "ON pi.PurchaseInvoiceID = dp.PurchaseInvoiceID WHERE dp.Amount < pi.GrandTotal AND dp.PaymentDate <= ?", f"{data.C}-12-31")
    full_min = data.one("SELECT MIN(pi.GrandTotal) FROM DisbursementPayment AS dp INNER JOIN PurchaseInvoice AS pi "
                        "ON pi.PurchaseInvoiceID = dp.PurchaseInvoiceID WHERE dp.Amount = pi.GrandTotal AND dp.PaymentDate <= ?", f"{data.C}-12-31")
    assert smallest >= 1000 > full_min, (smallest, full_min)         # only invoices of $1,000 or more are paid in parts
    _column(d, mock, "MAD", TEAL)
    _row(d, mock, partial, inset=1.5)
    a, f, p = rows
    _note(d, f"Outlined: the MAD column (teal) and the partial-payment row (coral). The values are Tutorial 8.1's: all payments {a[3]:.5f}, "
             f"{_reading(a[3])}; full payments (Amount = GrandTotal) {f[3]:.5f}, {_reading(f[3])}; partial payments {p[3]:.5f}, {_reading(p[3])}, "
             f"plausibly because only invoices of $1,000 or more are paid in parts (the smallest, {_money(smallest)}), a selection by size. Each group has {a[2]} digits, so none is missing. "
             f"The editor is scrolled to the last branch of the Groups CTE, the Observed CTE and the final SELECT.", mock["bottom"])
    return d


# -- IF-12-0-B: the anti-join written two ways ---------------------------------------------------------------------------------------

def _audit_l4() -> tuple[str, str, int]:
    """The comment lines, the SQL and the editor line of test L4 in Audit.sql as Tutorial 12.1 leaves it."""
    if not AUDIT.is_file():
        raise SystemExit(f"Audit.sql not found: {AUDIT} (build the companion files first)")
    return _query(AUDIT.read_text(encoding="utf-8"), "test L4:", "Audit.sql")


def _keyword_box(d: Diagram, top: float, x: float, line: str, keyword: str, color: str) -> None:
    """A coral outline around `keyword` in an editor line drawn at y = top (the line's top), in a pane that starts at x."""
    lead = len(line) - len(line.lstrip(" "))
    start = x + db.GUTTER + 4 + 2 + text_width("&nbsp;" * lead, SMALL, False)
    width = text_width(f"<b>{keyword}</b>", SMALL, True)
    d.outline(start - 3, top + 1.5, width + 6, db.LINE_H - 3, color, width=2.5, front=True)


def if_12_0_b() -> Diagram:
    """The anti-join of test L4 written with LEFT JOIN and with INNER JOIN (the chapter note's pitfall, Tutorial 12.1, Step 4)."""
    import guide_contexts.ch12 as g12
    t1 = ctx.values("ch12.chapter")["t1"]
    comment, sql, line = _audit_l4()
    assert sql.rstrip(";") == g12.tutorial_sql("L4"), "Audit.sql and the chapter's test L4 differ"
    inner_sql = g12.sub(sql, "LEFT JOIN PayrollPayment AS pay", "INNER JOIN PayrollPayment AS pay")
    n_comment = comment.count("\n") + 1
    left_head, left_rows = _run(sql)
    inner_head, inner_rows = _run(inner_sql)
    assert len(left_rows) == t1["n_l4"] == 3 and not inner_rows and inner_head == left_head, (len(left_rows), len(inner_rows))
    assert [r[0] for r in left_rows] == [r[0] for r in t1["l4"]], left_rows
    shown = 3                                                       # the last lines of the query: the join to the payments
    lines = sql.split("\n")
    first_no = line + n_comment + len(lines) - shown
    cols = slice(0, 3)                                              # each grid is scrolled to its first three columns
    pad, spacing, number_w = 10, 3, 32
    pane_w, gap = 426, 8
    widths = _widths(left_head[cols], [r[cols] for r in left_rows], total=pane_w - number_w, stretch=1.15, pad=pad)
    d = Diagram("The Anti-Join Written Two Ways")
    panes = [(0, "LEFT JOIN", sql, left_rows, TEAL, f"LEFT JOIN: {len(left_rows)} rows, the unpaid registers"),
             (pane_w + gap, "INNER JOIN", inner_sql, inner_rows, CORAL,
              f"INNER JOIN: {len(inner_rows)} rows, a clean result that means nothing")]
    bottoms = []
    for x, keyword, text, rows, color, caption in panes:
        d.box(f"<b>{esc(caption)}</b>", x, 0, pane_w, 30, fill=color, stroke=color, color=WHITE, size=SMALL, rounded=False)
        ey = 38
        drawn = text.split("\n")[-shown:]
        assert keyword in drawn[0], drawn
        y = db.editor(d, x, ey, pane_w, "\n".join(drawn), tab="Audit.sql", toolbar=False, first_line=first_no,
                      selection=slice(0, None)) + 8
        _keyword_box(d, ey + 24 + 4, x, drawn[0], keyword, CORAL)
        clipped = [tuple(_clip(v, w, pad) if isinstance(v, str) else v for v, w in zip(r[cols], widths)) for r in rows]
        _results(d, x, y, left_head[cols], widths, clipped, spacing=spacing, number_w=number_w)
        if not rows:                                                # an empty grid keeps the height of the other one
            d.box("", x, y + ROW_H, number_w + sum(widths), 3 * ROW_H, fill=WHITE, stroke=RULE, rounded=False)
        y += 4 * ROW_H + 8
        bottoms.append(db.message(d, x, y, pane_w, len(rows), text.split("\n")[0], line=line + n_comment))
    ids = ", ".join(str(r[0]) for r in left_rows[:-1]) + f" and {left_rows[-1][0]}"
    _note(d, f"Outlined: the join keyword, the only difference between the two tabs. Both show lines {first_no} to {first_no + shown - 1} of "
             f"test L4 in Audit.sql, the join to the payments; the query selects the approved registers that have no payment. With LEFT JOIN it returns "
             f"registers {ids}. With INNER JOIN no register can lack a payment, so the same test returns no rows, the answer a clean population would "
             f"give. Each grid is scrolled to its first three columns.", max(bottoms))
    return d


# -- IF-12-0-A: the audit cycle -----------------------------------------------------------------------------------------------------------

def if_12_0_a() -> Diagram:
    """The cycle of the chapter: population, reconcile and profile, test, exceptions list, disposition, with the positive control."""
    d = Diagram("The Audit Cycle")
    n, gap = 5, 30
    bw = (860 - gap * (n - 1)) / n
    stages = [("Population", "the rows the test must cover"),
              ("Reconcile and profile", "agree it with a second record"),
              ("Test", "anti-join, match or expectation"),
              ("Exceptions list", "one row for each failure, by test"),
              ("Disposition", "explain, accept or follow up")]
    practiced = [[("Population comment", "Tutorial 12.1, Step 3"), ("As-of date", "Exercise 12.2, Step 1")],
                 [("Entries and payroll", "Tutorial 12.1, Steps 1 and 2"), ("Time records", "Tutorial 12.3, Steps 1 and 2"),
                  ("Open balances", "Exercise 12.2, Step 3")],
                 [("Anti-join", "Tutorial 12.1, Step 3"), ("Match", "Tutorial 12.2, Step 1"), ("Expectation", "Tutorial 12.3, Step 5")],
                 [("UNION ALL", "Tutorial 12.1, Step 3"), ("Orders behind them", "Tutorial 12.2, Step 5")],
                 [("Memo", "Exercise 12.1, Step 9"), ("Findings", "Exercise 12.5, Step 6"), ("Each test", "Exercise 12.6, Step 8")]]
    texts = [f"<b>{t}</b><br>{b}" for t, b in stages]
    main_h = max(kit.height_for(t, bw) for t in texts)
    ref_texts = ["<br>".join(f"<b>{label}</b><br>{_nb(ref)}" for label, ref in items) for items in practiced]
    ref_h = max(kit.height_for(t, bw, SMALL) for t in ref_texts) + 4
    control_text = (f"<b>Positive control: a planted known exception</b><br>Plant one that the test must return. "
                    f"{_nb('Tutorial 12.1, Steps 4 and 6')}: a test that cannot fail. {_nb('Exercise 12.6, Step 5')}: a planted gap.")
    control_w = 3 * bw + 2 * gap
    control_h = kit.height_for(control_text, control_w, SMALL, pad=14) + 6
    main_y = control_h + 70
    xs = [i * (bw + gap) for i in range(n)]
    control = d.box(control_text, 0, 0, control_w, control_h, fill=CORAL_TINT, stroke=CORAL, stroke_width=1.5, size=SMALL)
    ids = []
    for i, text in enumerate(texts):
        fill, stroke = kit.tint("teal" if i == 2 else "blue")
        ids.append(d.box(text, xs[i], main_y, bw, main_h, fill=fill, stroke=stroke, stroke_width=1.5))
    for i in range(n - 1):
        d.arrow(ids[i], ids[i + 1], exit=(1, 0.5), entry=(0, 0.5))
    for i, text in enumerate(ref_texts):
        d.box(text, xs[i], main_y + main_h + 12, bw, ref_h, fill=GRAY_TINT, stroke=RULE, size=SMALL, valign="top", align="left")
    # the loop: the planted exception goes into the population, and the test must return it
    a, b = 0.5 * bw / control_w, (xs[2] + 0.5 * bw) / control_w
    d.arrow(control, ids[0], color=CORAL, width=2, exit=(a, 1), entry=(0.5, 0))
    d.arrow(ids[2], control, color=CORAL, width=2, exit=(0.5, 0), entry=(b, 1))
    mid = control_h + 35
    d.box("plant it in the population", 0.5 * bw + 8, mid - 10, 160, 20, fill=WHITE, stroke=WHITE, size=SMALL, align="left", rounded=False)
    d.box("the test must return it", xs[2] + 0.5 * bw + 8, mid - 10, 150, 20, fill=WHITE, stroke=WHITE, size=SMALL, align="left", rounded=False)
    bottom = main_y + main_h + 12 + ref_h
    _note(d, "Read left to right. The gray boxes name where the chapter practices each stage. A test that returns no rows is evidence only if the "
             "planted exception would have come back from the same test; the loop is the check on the test itself.", bottom)
    return d


# -- IF-12-0-C: surge days by month ----------------------------------------------------------------------------------------------------------

def _surge_by_month() -> list[tuple[str, int]]:
    """The PlantDays query of test H8 (Tutorial 12.3), grouped by month in place of year: the surge days of each month."""
    import guide_contexts.ch12 as g12
    sql = g12.tutorial_sql("H8")
    head = sql.split("\nSELECT strftime")[0]
    assert head.startswith("WITH PlantDays AS (") and head.rstrip().endswith(")"), "the H8 test no longer starts with PlantDays"
    case = "CASE WHEN HourPatterns = 1 AND Employees > 1 THEN 1 ELSE 0 END"
    assert case in re.sub(r"\s+", " ", sql), "the surge day rule of test H8 changed"
    return [(m, n) for m, n in ctx.data().q(f"{head}\nSELECT strftime('%Y-%m', WorkDate) AS WorkMonth, SUM({case}) AS SurgeDays "
                                            f"FROM PlantDays GROUP BY WorkMonth ORDER BY WorkMonth")]


def _month_letter(month: str) -> str:
    return "JFMAMJJASOND"[int(month[5:7]) - 1]


def if_12_0_c() -> Diagram:
    """The surge days of each month (test H8), for the chapter's central finding."""
    ch = ctx.values("ch12.chapter")
    h8, end = ch["t3"]["h8"], ch["t3"]["h1"][5]
    months = _surge_by_month()
    n = len(months)
    years = sorted({m[:4] for m, _ in months})
    by_year = {y: [c for m, c in months if m[:4] == y] for y in years}
    assert [(y, sum(by_year[y])) for y in years] == [(r[0], r[1]) for r in h8], "the monthly counts add up to the guide's year totals"
    assert all(len(v) == 12 for v in by_year.values()), "whole calendar years"
    first_i = next(i for i, (_, c) in enumerate(months) if c)
    assert months[first_i][0] == ch["first_surge"][:7], (months[first_i], ch["first_surge"])
    top = max(c for _, c in months)
    top_i = max(i for i, (_, c) in enumerate(months) if c == top)
    ticks = list(range(0, top + 2 if top % 2 == 0 else top + 3, 2))
    d = Diagram("Surge Days Each Month")
    d.text(f"<b>Surge days in each month, {months[0][0]} to {months[-1][0]}</b>", 0, 0, 860, 20, size=SMALL)
    strip_y, plot_y, plot_h = 26, 82, 330
    plot = kit.Plot(d, 0, plot_y, 860, plot_h, None, y_ticks=ticks, categories=[""] * n, y_fmt=lambda v: f"{v:g}",
                    y_title="Surge days in the month", bottom=44)
    slot = plot.pw / n
    base = plot.py + plot.ph
    for k in range(1, len(years)):                                  # a faint line between the years
        d.box("", plot.px + k * 12 * slot - 0.5, plot.py, 1, plot.ph, fill=GRAY, stroke=GRAY, rounded=False)
    for i, (month, count) in enumerate(months):
        cx = plot.px + i * slot
        d.text(_month_letter(month), cx, base + 4, slot, 18, size=SMALL, color=GRAY, align="center")
        if not count:
            continue
        color = CORAL if i == first_i else BLUE
        y = plot.y_of(count)
        d.box("", cx + slot * 0.15, y, slot * 0.7, base - y, fill=color, stroke=color, rounded=False)
        if i != first_i:
            d.text(str(count), cx - 2, y - 22, slot + 4, 20, size=SMALL, align="center", valign="bottom")
    for k, year in enumerate(years):                                # the year totals above the plot, and the year under the months
        x0 = plot.px + k * 12 * slot
        _, days, _, hours, share = h8[k]
        d.box(f"<b>{year}: {days} surge days</b><br>{hours:,.0f} overtime hours, {share * 100:.1f}% of the year's", x0 + 2, strip_y, 12 * slot - 4,
              44, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL)
        d.text(f"<b>{year}</b>", x0, base + 22, 12 * slot, 18, size=SMALL, color=INK, align="center")
    # the first surge day, marked on its bar
    fx = plot.px + first_i * slot + slot / 2
    call_y = plot.y_of(ticks[-1] - 0.5) + 8
    d.box(f"<b>First surge day: {_date(ch['first_surge'])}</b><br>one surge day in that month", plot.px + 8, call_y, 196, 40,
          fill=WHITE, stroke=CORAL, stroke_width=1.5, size=SMALL, align="left")
    a, b = d.anchor(fx, call_y + 40), d.anchor(fx, plot.y_of(months[first_i][1]) - 3)
    d.edge(a, b, end="blockThin", color=CORAL, width=1.5, meta="edgeStyle=none;")
    ly = plot_y + plot_h + 10
    d.box("", 0, ly + 3, 14, 14, fill=BLUE, stroke=BLUE, rounded=False)
    d.text("Surge days in the month (the count is above each bar)", 20, ly, 330, 20, size=SMALL, valign="middle")
    d.box("", 370, ly + 3, 14, 14, fill=CORAL, stroke=CORAL, rounded=False)
    d.text("The month of the first surge day", 390, ly, 250, 20, size=SMALL, valign="middle")
    total = sum(c for _, c in months)
    last_month = months[top_i][0]
    _note(d, f"{total} surge days in all, none before {_date(ch['first_surge'])}. A surge day is a manufacturing day on which every employee who clocked in "
             f"recorded the same hours (test H8). The most in a month rose from {max(by_year[years[0]])} in {years[0]} to {top} in {pd_month(last_month)} {last_month[:4]}, and the "
             f"share of the year's manufacturing overtime that falls on surge days rose from {h8[0][4] * 100:.1f}% to {h8[-1][4] * 100:.1f}%. A month with "
             f"no bar had no surge day. The time records end on {_date(end)}, so the last month is partial.", ly + 20)
    return d


# -- IF-12-3-B: the first-year stock build ---------------------------------------------------------------------------------------------------

def if_12_3_b() -> Diagram:
    """Exercise 12.3, Steps 4 and 5: units completed and shipped from January to July of the first year, and the late share."""
    ex, g = ctx.values("ch12.ex3"), ctx.values("ch12.g3")
    t4_head, t4 = _run(_solution(3, "test T4:")[1])
    t5_head, t5 = _run(_solution(3, "test T5:")[1])
    assert t4_head[:5] == ["Month", "WorkOrdersReleased", "UnitsCompleted", "UnitsShipped", "UnitsToStock"] and len(t4) == 7, t4_head
    assert t5_head == ["WorkMonth", "ShareAfterEnd"] and [r[0] for r in t5][:7] == [r[0] for r in t4], t5_head
    months = [r[0] for r in t4]
    completed, shipped, to_stock = [r[2] for r in t4], [r[3] for r in t4], [r[4] for r in t4]
    share = {r[0]: r[1] for r in t5}
    build = [i for i, v in enumerate(to_stock) if v > 0]
    assert build == list(range(build[0], build[-1] + 1)) and len(build) == 5, build
    stock = sum(to_stock[i] for i in build)
    assert stock == g["stock"] and abs(stock - ex["surplus"]) < 100, (stock, g["stock"], ex["surplus"])
    names = [pd_month(m) for m in months]
    assert names[build[0]] == ex["build_from"] and names[build[-1]] == ex["build_to"], names
    quarter = next(m for m in months if share[m] > 0.25)
    assert quarter == g["quarter_month"] and names[months.index(quarter)] == ex["first"] and all(share[m] <= 0.25 for m in months[:months.index(quarter)])
    assert [r[1] for r in t5][:7] == [r[1] for r in g["t5"]][:7], "the shares of the guide"
    d = Diagram("The First-Year Stock Build")
    d.text(f"<b>Units completed and manufactured units shipped, {months[0]} to {months[-1]}</b>", 0, 0, 860, 20, size=SMALL)
    plot_y, plot_h = 66, 330
    top_value = max(completed + shipped)
    ticks = [0, 2000, 4000, 6000, 8000] if top_value <= 8000 else list(range(0, int(top_value) + 2000, 2000))
    plot = kit.Plot(d, 0, plot_y, 860, plot_h, None, y_ticks=ticks, categories=names, y_fmt=lambda v: f"{v:,.0f}", y_title="Units", bottom=26)
    slot = plot.pw / len(months)
    base = plot.py + plot.ph
    band_x = plot.px + build[0] * slot
    d.vertex("", f"rounded=0;html=1;fillColor={CORAL_TINT};strokeColor=none;fillOpacity=70;", band_x, plot.py, len(build) * slot, plot.ph)
    for i in range(len(months)):
        x = plot.px + i * slot
        for k, (value, fill, stroke) in enumerate([(completed[i], BLUE, BLUE), (shipped[i], AMBER_TINT, AMBER)]):
            bx, y = x + slot * (0.13 + 0.38 * k), plot.y_of(value)
            d.box("", bx, y, slot * 0.34, base - y, fill=fill, stroke=stroke, stroke_width=1.5 if k else 1, rounded=False)
            d.text(f"{value:,.0f}", bx - 8, y - 22, slot * 0.34 + 16, 20, size=SMALL, align="center", valign="bottom")
    d.box(f"<b>Stock build, {names[build[0]]} to {names[build[-1]]}</b>: {stock:,.0f} more units completed than shipped", band_x + 2, 26,
          len(build) * slot - 4, 34, fill=CORAL_TINT, stroke=CORAL, stroke_width=1.5, size=SMALL)
    ly = plot_y + plot_h + 14
    d.text(f"<b>Share of direct time recorded after its operation ended</b> (test T5)", 0, ly, 860, 20, size=SMALL)
    for i, month in enumerate(months):
        x = plot.px + i * slot
        marked = month == quarter
        d.box(f"<b>{share[month]:.2f}</b><br>above 0.25" if marked else f"{share[month]:.2f}", x + slot * 0.1, ly + 24, slot * 0.8, 40,
              fill=HIGHLIGHT if marked else WHITE, stroke=CORAL if marked else RULE, stroke_width=2 if marked else 1, size=SMALL, rounded=False)
    ly += 84
    d.box("", 0, ly + 3, 14, 14, fill=BLUE, stroke=BLUE, rounded=False)
    d.text("Units completed", 20, ly, 120, 20, size=SMALL, valign="middle")
    d.box("", 160, ly + 3, 14, 14, fill=AMBER_TINT, stroke=AMBER, stroke_width=1.5, rounded=False)
    d.text("Manufactured units shipped", 180, ly, 190, 20, size=SMALL, valign="middle")
    d.box("", 390, ly + 3, 14, 14, fill=CORAL_TINT, stroke=CORAL, stroke_width=1.5, rounded=False)
    d.text("Months of the stock build: completed above shipped", 410, ly, 360, 20, size=SMALL, valign="middle")
    before_q = months[months.index(quarter) - 1]
    direct, indirect = [r[5] for r in t4], [r[6] for r in t4]
    quiet = [i for i in build if indirect[i] < 0.05 * direct[i]]
    assert quiet == list(range(quiet[0], quiet[-1] + 1)) and names[quiet[0]] == "February" and names[quiet[-1]] == "May", quiet
    q = months.index(quarter)
    last_build = build[-1]
    assert indirect[last_build] > 0.2 * direct[last_build], "the last month of the build already had much indirect time"
    _note(d, f"From {names[build[0]]} to {names[build[-1]]} the plant completed {stock:,.0f} more units than it shipped, an inventory build consistent with "
             f"the little indirect time from {names[quiet[0]]} to {names[quiet[-1]]}, {', '.join(f'{indirect[i]:,.0f}' for i in quiet[:-1])} and "
             f"{indirect[quiet[-1]]:,.0f} hours against {sum(direct[i] for i in quiet):,.0f} direct (test T4), although {names[last_build]} already had "
             f"{indirect[last_build]:,.0f}. A plausible explanation, to confirm with the production schedules. In {names[q]} completions "
             f"({completed[q]:,.0f}) fell below shipments ({shipped[q]:,.0f}) and the share of direct time recorded after its operation ended rose "
             f"from {share[before_q]:.2f} in {names[q - 1]} to {share[quarter]:.2f}, the first month above a quarter.", ly + 20)
    return d


def pd_month(month: str) -> str:
    """2024-02 as February."""
    import calendar
    return calendar.month_name[int(month[5:7])]


FIGURES = {
    "IF-12-0-A": if_12_0_a,
    "IF-12-0-B": if_12_0_b,
    "IF-12-0-C": if_12_0_c,
    "IF-12-3-B": if_12_3_b,
    "IF-12-1-A": if_12_1_a,
    "IF-12-2-A": if_12_2_a,
    "IF-12-3-A": if_12_3_a,
    "IF-12-4-A": if_12_4_a,
    "IF-12-5-A": if_12_5_a,
    "IF-12-6-A": if_12_6_a,
}
