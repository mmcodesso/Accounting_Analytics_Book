"""Instructor figures of Chapter 17 (guides in facts/instructor/guides/chapter-17-statements-for-a-lender/).

Chapter 17, "Financial Statements for a Lender", is the first capstone case.  Its model answer is three files: the script
LenderPackage.sql, the workbook Charles River Lender Package.xlsx and the Power BI project Charles River Lender Review
(outputs/companion/solutions/Chapter17-capstone-*).  The three SQL mocks quote their query from the script, at the editor line
where it sits, and run it read-only (a saved view the query reads is created as a TEMP view for the length of the run), so
the grid and the message pane come from the data.  The three Excel mocks draw blocks of the workbook: their values come from
the guides' own contexts (ch17.r4 to ch17.r6) and the registered notes behind them, and each is asserted against the value the
workbook holds in the cell it draws, so a stale workbook fails the build.  The Power BI mock draws the Review page from the
project's report definition (page, visuals, titles, columns) with values from the same notes.  The diagrams take their
structure from the case text and from the guides' tables.
"""

from __future__ import annotations

import json
import re
from datetime import date

import ctx
import dbbrowser as db
import excel as xl
import kit
import powerbi as pbi
from check_figures import text_width
from data import connection
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, FONT, GRAY, GRAY_TINT, INK, ROW_H, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc)

REPO = ctx.REPO
SOLUTIONS = REPO / "outputs" / "companion" / "solutions"
SQL = SOLUTIONS / "Chapter17-capstone-sql" / "LenderPackage.sql"
PROJECT = SOLUTIONS / "Chapter17-capstone-pbi" / "Charles River Lender Review"
MODEL = PROJECT / "Charles River Lender Review.SemanticModel"
REPORT = PROJECT / "Charles River Lender Review.Report" / "definition"
CHAPTER = REPO / "chapters" / "17-statements-for-a-lender" / "chapter.qmd"
GUIDES = REPO / "facts" / "instructor" / "guides" / "chapter-17-statements-for-a-lender"
GRID_W = 820            # the 860 px frame less the row-number column of the result grid
CELL_PAD = 20           # a cell wraps its text within about 12 px of its width, so leave room
MINUS = "−"
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
               "December"]
STRAIGHT = "edgeStyle=none;"


# -- shared helpers -----------------------------------------------------------------------------------------------------

def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def _money(x: float) -> str:
    return f"{x:,.2f}"


def _g():
    """guide_contexts.ch17: the helpers that read the model answers."""
    from guide_contexts import ch17
    return ch17


def _n():
    from notes import ch17
    return ch17


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A value cut to its column with an ellipsis, as a narrow column shows it."""
    if not text or text_width(esc(text), size, bold) <= width - margin:
        return text
    while text and text_width(esc(text + "…"), size, bold) > width - margin:
        text = text[:-1]
    return text.rstrip() + "…"


def _nowrap(text: str) -> str:
    return f'<span style="white-space:nowrap">{esc(text)}</span>'


# -- SQL mocks: the model script, a read-only run and the Execute SQL tab -----------------------------------------------

def _script_lines() -> list[str]:
    if not SQL.is_file():
        raise SystemExit(f"Model answer not found: {SQL} (build the solutions first)")
    return SQL.read_text(encoding="utf-8").split("\n")


def _solution(key: str) -> tuple[list[str], str, int]:
    """The two comment lines, the SQL and the editor line of the one query of LenderPackage.sql whose first comment line
    starts with `-- key`.  The `-- Result: ...` remark that the model answer appends to a query's last line is left out: a
    student types the query without it."""
    lines = _script_lines()
    hits = [i for i, line in enumerate(lines) if line.startswith(f"-- {key}")]
    if len(hits) != 1:
        raise SystemExit(f"LenderPackage.sql: {len(hits)} queries start with {key!r} (expected one)")
    i = hits[0]
    assert lines[i + 1].startswith("-- Population"), lines[i + 1]
    j = i + 2
    while not re.search(r";\s*(--.*)?$", lines[j]):
        j += 1
    sql = lines[i + 2:j + 1]
    sql[-1] = re.sub(r"\s*--\s*Result:.*$", "", sql[-1])
    return lines[i:i + 2], "\n".join(sql), i + 1


def _temp_view(name: str) -> str:
    """The CREATE VIEW statement of LenderPackage.sql for `name`, as a TEMP view: the model answer writes the view into the
    working copy, the figure's read-only run keeps it in the connection's temporary database."""
    m = re.search(rf"CREATE VIEW {name} AS\n(.*?);\s*--\s*Result", "\n".join(_script_lines()), re.S)
    if not m:
        raise SystemExit(f"LenderPackage.sql: no CREATE VIEW {name}")
    return f"CREATE TEMP VIEW {name} AS\n{m.group(1)}"


class _Views:
    """The saved views of LenderPackage.sql created as TEMP views for the length of a block, and dropped again (the
    connection is shared with other units' figures, which create views of the same names)."""

    def __init__(self, *names: str):
        self.names = names

    def __enter__(self):
        con = connection()
        for name in self.names:
            con.execute(f"DROP VIEW IF EXISTS temp.{name}")
            con.execute(_temp_view(name))
        return self

    def __exit__(self, *exc):
        con = connection()
        for name in reversed(self.names):
            con.execute(f"DROP VIEW IF EXISTS temp.{name}")


def _run(sql: str) -> tuple[list[str], list[tuple]]:
    cursor = connection().execute(sql)
    return [c[0] for c in cursor.description], cursor.fetchall()


GUTTER = 42             # the gutter of the book's editor is 34 px, too narrow for a four-digit line number


def _editor(d: Diagram, x: float, y: float, w: float, sql: str, tab: str, first_line: int, selection: slice | None) -> float:
    """db.editor with a gutter wide enough for four-digit line numbers and a tab as wide as the file's name.  Returns the bottom y."""
    bx = x
    for label, width, primary in [("Open SQL file(s)", 124, False), ("Save SQL file ▾", 124, False), ("▶ Execute all/selected SQL", 196, True)]:
        xl.button(d, bx, y, width, label, primary=primary)
        bx += width + 8
    y += 32
    d.box(f"<b>{esc(tab)}</b>", x, y, max(110, text_width(f"<b>{esc(tab)}</b>", SMALL, True) + 30), 24, fill=WHITE, stroke=RULE, size=SMALL,
          align="left", rounded=False)
    y += 24
    lines = sql.strip("\n").split("\n")
    height = len(lines) * db.LINE_H + 8
    d.box("", x, y, GUTTER, height, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.box("", x + GUTTER, y, w - GUTTER, height, fill=WHITE, stroke=RULE, rounded=False)
    if selection:
        first, last = selection.start or 0, (selection.stop or len(lines)) - 1
        d.box("", x + GUTTER + 1, y + 4 + first * db.LINE_H, w - GUTTER - 2, (last - first + 1) * db.LINE_H, fill=BLUE_TINT, stroke=BLUE_TINT,
              rounded=False)
    in_comment = False
    for i, line in enumerate(lines):
        ly = y + 4 + i * db.LINE_H
        d.text(str(first_line + i), x, ly, GUTTER - 4, db.LINE_H, size=SMALL, color=GRAY, align="right", valign="middle")
        label, in_comment = db.highlight(line, in_comment)
        assert text_width(label, SMALL, False) <= w - GUTTER - 12, f"SQL line too wide: {line}"
        d.text(label or " ", x + GUTTER + 4, ly, w - GUTTER - 8, db.LINE_H, size=SMALL, valign="middle")
    return y + height


def _fit_comment(line: str) -> str:
    """A long comment line cut at the editor's edge with an ellipsis (the real editor scrolls sideways; the mock shows its
    first part)."""
    limit = 860 - GUTTER - 12 - 8
    if text_width(db.highlight(line)[0], SMALL, False) <= limit:
        return line
    while line and text_width(db.highlight(line.rstrip() + "…")[0], SMALL, False) > limit:
        line = line[:-1]
    return line.rstrip() + "…"


def _widths(headers: list[str], rows: list[tuple], total: float = GRID_W, stretch: float = 1.5,
            pad: float = CELL_PAD + 2) -> list[float]:
    """Column widths that fit each heading and value, shrunk (the widest column first, its text then clipped) to fit the
    frame, or stretched a little when the result is narrow."""
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
    """A grid cell with a chosen margin beside its text (Diagram.box keeps 6 px, so a cell wraps within about 12 px of its
    width; a dense grid passes a smaller spacing and keeps its columns narrow)."""
    style = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={RULE};strokeWidth=1;fontColor={color};"
             f"fontSize={SMALL};fontStyle=0;align={align};verticalAlign=middle;{FONT}spacingLeft={spacing:g};"
             f"spacingRight={spacing:g};")
    d.vertex(label, style, x, y, w, h)


def _results(d: Diagram, y: float, headers: list[str], widths: list[float], rows: list[tuple], first: int = 1,
             spacing: float = 6, number_w: float = 40) -> dict:
    """db.results with a smaller margin in each cell and a narrower row-number column.  Returns the geometry (x, y, w, h) of
    every cell, keyed (row, column) from 0, with row -1 for the headings."""
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


def _mock(d: Diagram, key: str, lines: slice | None = None, shown: slice | None = None, tight: bool = False) -> dict:
    """The Execute SQL tab with the query of LenderPackage.sql whose first comment line starts with `-- key`, as a reader sees
    it after selecting the query and clicking Execute all/selected SQL.  The editor shows the comment lines and the query at
    their line numbers in the script, or only `lines` of them (an editor scrolled to part of a long query, the line numbers
    kept); `shown` draws only some rows of the result, as a grid scrolled to them (the rows keep their numbers); `tight` keeps
    a smaller margin in each cell, for a result of many columns.  Returns the grid and editor geometry."""
    comment, sql, line = _solution(key)
    headers, rows = _run(sql)
    spacing, pad, number_w = (3, 10, 32) if tight else (6, CELL_PAD + 2, 40)
    saved, db.PATH = db.PATH, "C:\\Users\\you\\Documents\\CharlesRiver_Capstone.sqlite"    # the case works in a copy of that name
    try:
        y = db.window(d)
    finally:
        db.PATH = saved
    editor_top = y
    full = [_fit_comment(c) for c in comment] + sql.split("\n")
    n_comment = len(comment)
    start = (lines.start or 0) if lines else 0
    drawn = full[lines] if lines else full
    y = _editor(d, 0, y, 860, "\n".join(drawn), "LenderPackage.sql", line + start, slice(max(n_comment - start, 0), None)) + 8
    visible = rows[shown] if shown else rows
    first = (shown.start or 0) + 1 if shown else 1
    widths = _widths(headers, visible, total=860 - number_w, pad=pad)
    clipped = [tuple(_clip(v, w, margin=pad) if isinstance(v, str) else v for v, w in zip(row, widths)) for row in visible]
    if tight:
        geometry = _results(d, y, headers, widths, clipped, first=first, spacing=spacing, number_w=number_w)
    else:
        geometry = db.results(d, 0, y, headers, widths, clipped, first=first)
    y += (len(visible) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0], line=line + n_comment)
    return dict(headers=headers, rows=rows, geometry=geometry, bottom=bottom, sql_lines=drawn, sql=sql, n_comment=n_comment,
                editor_top=editor_top, first_line=line + start, widths=widths)


def _line_top(mock: dict, i: int) -> float:
    """The y of line i (from 0) of the text drawn in the editor, below the editor's toolbar and tab."""
    return mock["editor_top"] + 32 + 24 + 4 + i * db.LINE_H


def _find(mock: dict, text: str) -> int:
    hits = [i for i, line in enumerate(mock["sql_lines"]) if text in line]
    assert len(hits) == 1, (text, hits)
    return hits[0]


def _outline_lines(d: Diagram, mock: dict, first: int, last: int, color: str = TEAL) -> None:
    """An outline around lines first..last of the drawn editor text, inset so that neighbors do not touch."""
    top = _line_top(mock, first)
    d.outline(GUTTER + 3, top + 1.5, 860 - GUTTER - 6, (last - first + 1) * db.LINE_H - 3, color, width=2.5, front=True)


def _outline_row(d: Diagram, mock: dict, first: int, last: int | None = None, color: str = CORAL, inset: float = 0) -> None:
    """Outline rows first..last of the grid (indexes into the drawn rows), every column."""
    last = first if last is None else last
    geo, c_last = mock["geometry"], len(mock["headers"]) - 1
    x0, y0, _, _ = geo[(first, 0)]
    x1, y1, w1, h1 = geo[(last, c_last)]
    left, right = x0 - 1 + inset, min(860.0, x1 + w1 + 1 - inset)
    d.outline(left, y0 - 1 + inset, right - left, y1 + h1 - y0 + 2 - 2 * inset, color, width=2.5, front=True)


def _outline_column(d: Diagram, mock: dict, column: int, rows: int, color: str = CORAL) -> None:
    """Outline one column of the grid, from its heading down through `rows` drawn rows."""
    geo = mock["geometry"]
    x, y, w, _ = geo[(-1, column)]
    _, y_last, _, h_last = geo[(rows - 1, column)]
    right = min(860.0, x + w + 1)
    d.outline(x - 1, y - 1, right - x + 1, y_last + h_last - y + 2, color, width=2.5, front=True)


# -- IF-17-1-A: the trial balance at the last year-end ------------------------------------------------------------------

def if_17_1_a() -> Diagram:
    """Requirement 1's query for the last year-end: the editor from the comment lines to the NOT test, and the first accounts of
    its 71 rows with the cash row outlined."""
    r1 = ctx.values("ch17.r1")
    C = ctx.data().C
    d = Diagram("The Trial Balance at the Last Year-End")
    key = f"Requirement 1: the trial balance at {C}-12-31"
    mock = _mock(d, key, lines=slice(0, 25), shown=slice(0, 5), tight=True)
    rows = mock["rows"]
    rec = r1["rec"][2]
    assert len(rows) == rec["n"] and sum(1 for r in rows if r[4] == 0) == rec["zero"], "the row count and the accounts at zero are the guide's"
    assert abs(sum(r[5] for r in rows) - rec["debits"]) < 0.005 and abs(sum(r[6] for r in rows) - rec["debits"]) < 0.005, "debits equal credits"
    assert rows[0][0] == 1010 and rows[0][1] == "Cash and Cash Equivalents", rows[0]
    asof = _find(mock, "SELECT '")                                    # the date in the Params CTE
    assert str(C) in mock["sql_lines"][asof]
    _outline_row(d, mock, 0)
    not_test = _find(mock, "AND NOT (gl.VoucherNumber")
    _outline_lines(d, mock, not_test, not_test + 1, TEAL)
    _note(d, f"Outlined in teal: the test that leaves out a close only when it is dated on the as-of date. Outlined in coral: the cash row. "
             f"The grid shows the first {len(mock['geometry']) // len(mock['headers']) - 1} of {len(rows)} rows; the debit balances add up to "
             f"{_money(rec['debits'])}, equal to the credit balances. The query's GROUP BY and ORDER BY lines are below the part of the editor drawn; "
             "the second comment line is cut at the editor's edge.", mock["bottom"] + 6)
    return d


# -- IF-17-3-A: the reconciliation of account 2040 ------------------------------------------------------------------------

def if_17_3_a() -> Diagram:
    """Requirement 3's reconciliation: the closing SELECT of the query, scrolled into view, and its three rows, with the
    Difference cells outlined."""
    r3 = ctx.values("ch17.r3")
    d = Diagram("The Reconciliation of Accrued Expenses")
    key = "Requirement 3: account 2040 at each year-end split into its parts and reconciled to the ledger"
    comment, sql, line = _solution(key)
    n = len(comment) + len(sql.split("\n"))
    start = next(i for i, text in enumerate(comment + sql.split("\n")) if text.startswith("SELECT pa.AsOfDate"))
    with _Views("OpenAccruals"):
        mock = _mock(d, key, lines=slice(start, n), tight=True)
    rows = mock["rows"]
    comp = r3["comp"]
    assert mock["headers"] == ["AsOfDate", "Opening", "FreightNotSettled", "DecemberFreight", "YoungAccruals", "OldAccruals", "Parts",
                               "Ledger", "Difference"], mock["headers"]
    assert len(rows) == 3
    for r, c in zip(rows, comp):
        assert abs(r[1] - c["opening"]) < 0.005 and abs(r[4] - c["young"]) < 0.005 and abs(r[5] - c["old"]) < 0.005
        assert abs(r[6] - c["total"]) < 0.005 and abs(r[7] - c["total"]) < 0.005 and abs(r[8]) < 0.005, "the parts equal the ledger"
    _outline_column(d, mock, 8, 3)
    _note(d, "Outlined in coral: the Difference of each year-end, the parts less the ledger, which is zero at all three (-0.0 is a rounding residue). The editor is scrolled to the "
             "closing SELECT; its CTEs sum the opening entry, the freight and the ledger, and the view OpenAccruals holds the accruals still open.",
          mock["bottom"] + 6)
    return d


# -- IF-17-8-A: the search for unrecorded liabilities -----------------------------------------------------------------------

def if_17_8_a() -> Diagram:
    """Requirement 8's search: the query of the 2027 payments and the invoices they paid, and its one row."""
    r8 = ctx.values("ch17.r8")
    d = Diagram("The Search for Unrecorded Liabilities")
    mock = _mock(d, "Requirement 8: the 2027 supplier payments and the invoices they paid")
    rows = mock["rows"]
    assert len(rows) == 1 and mock["headers"] == ["Payments", "Amount", "Invoices", "Suppliers", "FirstReceived", "LastReceived", "PaidInFull",
                                                  "ReceivedAfterYearEnd"], mock["headers"]
    pay, amount, inv, sup, first, last, full, after = rows[0]
    month = lambda iso: MONTH_NAMES[int(iso[5:7]) - 1]
    assert (pay, inv, sup, month(first), month(last), full) == (r8["n_pay"], r8["n_inv"], r8["n_sup"], r8["recv_first"], r8["recv_last"], r8["full"])
    assert abs(amount - r8["paid"]) < 0.005 and after == 0, "no invoice was received after the year-end"
    _outline_column(d, mock, 7, 1)
    split = ctx.values("ch17.g8")["split"]
    assert split == pay - inv and split > 0, "the payments outnumber the invoices by the invoices paid in parts"
    split_text = f"{ctx.values('ch17.g8')['split_word']} invoice was" if split == 1 else f"{ctx.values('ch17.g8')['split_word']} invoices were"
    _note(d, f"Outlined in coral: the invoices received after the year-end, none, which is the finding. The {pay} payments settle {inv} invoices that the "
             f"ledger already held at the year-end, and the payments outnumber the invoices only because {split_text} paid in two parts.",
          mock["bottom"] + 6)
    return d


# -- the case text -----------------------------------------------------------------------------------------------------

def _case_text() -> str:
    return CHAPTER.read_text(encoding="utf-8")


def _requirements() -> list[dict]:
    """Each requirement of the case text: number, title, chapters and the phase it belongs to."""
    found, phase = [], None
    for line in _case_text().split("\n"):
        m = re.match(r"^### Phase (\d): (.+)$", line)
        if m:
            phase = (int(m.group(1)), m.group(2).strip())
        m = re.match(r"^\*\*Requirement (\d+): (.+?) \((Chapters? [^)]+)\)\.\*\*", line)
        if m:
            found.append(dict(n=int(m.group(1)), title=m.group(2), chapters=m.group(3), phase=phase))
    assert [r["n"] for r in found] == list(range(1, 10)), found
    assert [r["phase"][0] for r in found] == [1, 1, 2, 2, 2, 3, 3, 4, 4], found
    return found


def _tools() -> dict[int, list[str]]:
    """The tools of each requirement as the case notes' table 'Using the requirements' lists them."""
    text = (GUIDES / "00-case-notes.md").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^\| (\d)\. [^|]+\| \w+ \| ([^|]+?) \|", text, re.M):
        tags = [t.strip() for t in m.group(2).split(" and ")]
        out[int(m.group(1))] = ["Memo" if t == "a written memo" else t for t in tags]
    assert sorted(out) == list(range(1, 10)), out
    return out


def _milestones() -> list[dict]:
    found = [dict(n=int(m.group(1)), title=m.group(2), reqs=m.group(3), body=m.group(4))
             for m in re.finditer(r"^(\d)\. \*\*([^*]+)\*\* \(Requirements? ([^)]+)\): (.+?)\.$", _case_text(), re.M)]
    assert [x["n"] for x in found] == [1, 2, 3, 4], found
    return found


def _tool_files() -> list[dict]:
    """The rows of the case's table of tools and files: tool, file, what it holds and how it hands results on."""
    rows = []
    for m in re.finditer(r"^\| (SQL|Excel|Power BI) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", _case_text(), re.M):
        rows.append(dict(tool=m.group(1), file=m.group(2), holds=m.group(3), handoff=m.group(4)))
    assert [r["tool"] for r in rows] == ["SQL", "Excel", "Power BI"], rows
    return rows


TOOL_COLORS = {"SQL": (TEAL, TEAL_TINT), "Excel": (BLUE, BLUE_TINT), "Power BI": (AMBER, AMBER_TINT), "Memo": (GRAY, GRAY_TINT)}


# -- IF-17-0-A: the requirements, the files and the milestones ---------------------------------------------------------------

def if_17_0_a() -> Diagram:
    """Nine requirement cards in four phase columns with their tool tags, a milestone under each column, the three files with the
    hand-offs between them, and the memo they all feed."""
    reqs, tools, miles, files = _requirements(), _tools(), _milestones(), _tool_files()
    assert [m["reqs"] for m in miles] == ["1 and 2", "3 to 5", "6 and 7", "8 and 9"], miles
    d = Diagram("How the Requirements, Files and Milestones Fit Together")
    W, GAP = 200.0, 20.0
    xs = [i * (W + GAP) for i in range(4)]
    bottoms = []
    for p in range(1, 5):
        phase = [r for r in reqs if r["phase"][0] == p]
        d.box(f"<b>Phase {p}</b><br><b>{esc(phase[0]['phase'][1])}</b>", xs[p - 1], 0, W, 40, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL,
              rounded=False)
        y = 48.0
        for r in phase:
            text = f"<b>Requirement {r['n']}</b><br>{esc(r['title'])}<br><i>{esc(r['chapters'])}</i>"
            h = kit.height_for(text, W - 4, SMALL, pad=10) + 4 + 30
            d.box(text, xs[p - 1], y, W, h, fill=WHITE, stroke=GRAY, stroke_width=1.5, size=SMALL, align="left", valign="top", rounded=False)
            tx = xs[p - 1] + 6
            for tag in tools[r["n"]]:
                fill, _ = TOOL_COLORS[tag]
                tw = text_width(f"<b>{tag}</b>", SMALL, True) + 16
                d.box(f"<b>{tag}</b>", tx, y + h - 27, tw, 22, fill=fill, stroke=fill, color=WHITE, size=SMALL)
                tx += tw + 6
            y += h + 8
        bottoms.append(y - 8)
    top = max(bottoms) + 14
    # the milestones, one under each column
    labels = [f"<b>Milestone {m['n']}</b>: {esc(m['title'])}<br>{esc(m['body'][0].upper() + m['body'][1:])}" for m in miles]
    mh = max(kit.height_for(t, W - 10, SMALL, pad=12) for t in labels)
    for m, text in zip(miles, labels):
        d.box(text, xs[m["n"] - 1], top, W, mh, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, size=SMALL, align="left", valign="top", rounded=False)
        d.box("", xs[m["n"] - 1], top, 5, mh, fill=TEAL, stroke=TEAL, rounded=False)
    # the files and their hand-offs
    fy = top + mh + 40
    FW, FG = 220.0, 100.0
    fxs = [i * (FW + FG) for i in range(3)]
    fh = max(kit.height_for(f"<b>{esc(f['file'])}</b><br>{esc(f['holds'])}", FW, SMALL, pad=12) for f in files) + 8
    fids = []
    for f, fx in zip(files, fxs):
        fill, tint_ = TOOL_COLORS[f["tool"]]
        fids.append(d.box(f"<br><b>{esc(f['file'])}</b><br>{esc(f['holds'])}", fx, fy, FW, fh, fill=tint_, stroke=fill, stroke_width=1.5, size=SMALL,
                          align="left", valign="top", rounded=False))
        tw = text_width(f"<b>{f['tool']}</b>", SMALL, True) + 16
        d.box(f"<b>{f['tool']}</b>", fx + 6, fy - 11, tw, 22, fill=fill, stroke=fill, color=WHITE, size=SMALL)
    for i in (0, 1):
        d.arrow(fids[i], fids[i + 1], exit=(1, 0.5), entry=(0, 0.5), meta=STRAIGHT)
        d.text(f"<i>{esc(files[i]['handoff'])}</i>", fxs[i] + FW + 2, fy + fh / 2 - 50, FG - 4, 46, size=SMALL, color=GRAY, align="center",
               valign="bottom")
    # the memo
    my = fy + fh + 50
    memo = d.box("<b>The memo to the CFO</b> (Requirement 9): two pages and an appendix of three; the PDF of the statements and notes goes with it.<br>"
                 "Every number in it traces to one of the three files.", 0, my, 860, 52, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5, size=SMALL,
                 rounded=False)
    for fid, fx in zip(fids, fxs):
        d.arrow(fid, memo, exit=(0.5, 1), entry=((fx + FW / 2) / 860, 0), meta=STRAIGHT)
    _note(d, "Each card is a requirement of the case, in the order of its four phases; the tags name the tools it uses. The teal boxes are the four "
             "milestones an instructor may collect and check. Arrows show how results move: Copy with Headers or Export to CSV from the script into the "
             "workbook, the workbook's Table of adjustment lines into the Review file, and all three files into the memo.", my + 62)
    return d


# -- IF-17-0-B: the dates of the case -------------------------------------------------------------------------------------------

def _day(iso: str) -> int:
    return date.fromisoformat(iso).toordinal()


def _mark(d: Diagram, x: float, y: float, color: str) -> None:
    d.box("", x, y, 12, 12, fill=color, stroke=WHITE, stroke_width=1.5, rounded=False)


def if_17_0_b() -> Diagram:
    """The ledger's dates on one strip: the opening entry and the three year-ends with their closes; enlarged below, the last pay
    date, the last day of the year and the ledger's last posting, with the stretch of supplier payments alone bracketed."""
    data = ctx.data()
    g0, r2, r8 = ctx.values("ch17.g0"), ctx.values("ch17.r2"), ctx.values("ch17.r8")
    F, P, C = data.F, data.P, data.C
    opening = data.q("SELECT EntryNumber, PostingDate FROM JournalEntry WHERE EntryType = 'Opening'")
    first, last = data.q("SELECT MIN(PostingDate), MAX(PostingDate) FROM GLEntry")[0]
    assert len(opening) == 1 and opening[0][0] == r2["entry"] and opening[0][1] == first == f"{F}-01-01", opening
    closes = {}
    for number, kind, day in data.q("SELECT EntryNumber, EntryType, PostingDate FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' "
                                    "ORDER BY PostingDate, EntryNumber"):
        closes.setdefault(day, []).append((number, kind))
    year_ends = [f"{y}-12-31" for y in (F, P, C)]
    assert sorted(closes) == year_ends and all(len(v) == 2 for v in closes.values()), closes
    assert all(v[0][1].endswith("P&L to Income Summary") and v[1][1].endswith("Income Summary to Retained Earnings") for v in closes.values())
    pay_end, thru = g0["pay_end"], g0["thru"]
    assert thru == year_ends[-1] and last == g0["last"] and pay_end < thru < last, (pay_end, thru, last)
    assert data.one("SELECT COUNT(*) FROM GLEntry WHERE PostingDate > ? AND SourceDocumentType <> 'DisbursementPayment'", thru) == 0
    d = Diagram("The Dates of the Case")
    # the whole ledger, to scale
    x0, x1 = 40.0, 820.0
    start, end = _day(first), _day(last)
    xt = lambda iso: x0 + (_day(iso) - start) * (x1 - x0) / (end - start)                       # noqa: E731
    ay, ah = 96.0, 26.0
    bounds = [first] + year_ends
    for k, (a, b) in enumerate(zip(bounds, bounds[1:])):
        d.box(f"<b>Fiscal {[F, P, C][k]}</b>", xt(a), ay, xt(b) - xt(a), ah, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL, rounded=False)
    # the opening entry
    d.box(f"<b>Opening entry</b><br>{_nowrap(r2['entry'])}<br>{first}, {r2['lines']} lines", 0, 0, 150, 56, fill=WHITE, stroke=BLUE, stroke_width=1.5,
          size=SMALL, rounded=False)
    d.box("", x0 - 0.75, 56, 1.5, ay - 56 - 12, fill=BLUE, stroke=BLUE, rounded=False)
    _mark(d, x0 - 6, ay - 14, BLUE)
    # the year-ends and their two closes
    for day in year_ends:
        x = xt(day)
        (n1, _), (n2, _) = closes[day]
        d.box(f"<b>Year-end</b> {day}<br>two closes<br>{_nowrap(n1)}<br>{_nowrap(n2)}", min(x - 72, 860 - 144), 0, 144, 72, fill=WHITE, stroke=CORAL,
              stroke_width=1.5, size=SMALL, rounded=False)
        d.box("", x - 0.75, 72, 1.5, ay - 72 - 12, fill=CORAL, stroke=CORAL, rounded=False)
        for dx in (-13, 1):
            _mark(d, x + dx, ay - 14, CORAL)
    # the zoom: the stretch from December of the last fiscal year to the ledger's last day
    z0, z1 = f"{C}-12-01", f"{C + 1}-03-01"
    tail_x = (xt(thru) + xt(last)) / 2
    d.box("<b>" + str(C + 1) + "</b>", xt(thru), ay, xt(last) - xt(thru), ah, fill=CORAL_TINT, stroke=CORAL, stroke_width=1.5, size=SMALL, rounded=False,
          dashed=True)
    _mark(d, 40, 136, CORAL)
    _mark(d, 54, 136, CORAL)
    d.text("a year-end's two closing entries: the P&amp;L to Income Summary, then Income Summary to Retained Earnings", 74, 132, 600, 20, size=SMALL,
           valign="middle")
    py = 176.0
    d.box("", 0, py, 860, 240, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False, dashed=True)
    a1, a2 = d.anchor(tail_x, ay + ah + 8), d.anchor(tail_x, py)
    d.edge(a1, a2, color=GRAY, width=1.5, end="blockThin", meta=STRAIGHT)
    d.text("<i>enlarged below</i>", tail_x - 110, ay + ah + 24, 100, 18, size=SMALL, color=GRAY, align="right")
    d.text(f"<i>Enlarged, to scale: {z0} to {z1}</i>", 8, py + 4, 420, 20, size=SMALL, color=GRAY)
    zy = py + 130.0
    zs, ze = _day(z0), _day(z1)
    zt = lambda iso: x0 + (_day(iso) - zs) * (x1 - x0) / (ze - zs)                                  # noqa: E731
    d.box(f"<b>Fiscal {C}</b>", zt(z0), zy, zt(thru) - zt(z0), ah, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL, rounded=False)
    d.box(f"<b>{C + 1}: supplier payments only</b>", zt(thru), zy, zt(last) - zt(thru), ah, fill=CORAL_TINT, stroke=CORAL, stroke_width=1.5, size=SMALL,
          rounded=False, dashed=True)
    for iso in (z0, f"{C + 1}-01-01", f"{C + 1}-02-01", z1):
        d.box("", zt(iso) - 0.5, zy + ah, 1, 6, fill=GRAY, stroke=GRAY, rounded=False)
        d.text(iso, zt(iso) - 40, zy + ah + 6, 80, 18, size=SMALL, color=GRAY, align="center")
    marks = [(pay_end, ["Last pay date", "with registers", pay_end], 150, -75), (thru, ["Last day of the year,", "the data-through date", thru], 180, -30),
             (last, ["Ledger's last posting", last], 160, -80)]
    for iso, lines, w_, off in marks:
        x = zt(iso)
        text = f"<b>{esc(lines[0])}</b>" + "".join(f"<br>{esc(t)}" for t in lines[1:])
        h_ = 15 * len(lines) + 12
        top = zy - 18 - 12 - h_ - 4
        bx = min(x + off, 860 - w_ - 4)
        d.box(text, bx, top, w_, h_, fill=WHITE, stroke=INK, stroke_width=1.5, size=SMALL, rounded=False)
        d.box("", x - 0.75, top + h_, 1.5, zy - top - h_ - 12, fill=INK, stroke=INK, rounded=False)
        _mark(d, x - 6, zy - 14, INK)
    # the bracket after the data-through date
    by = zy + ah + 40
    xa, xb = zt(thru), zt(last)
    d.box("", xa, by, xb - xa, 1.5, fill=INK, stroke=INK, rounded=False)
    d.box("", xa - 0.75, by - 8, 1.5, 9.5, fill=INK, stroke=INK, rounded=False)
    d.box("", xb - 0.75, by - 8, 1.5, 9.5, fill=INK, stroke=INK, rounded=False)
    d.box(f"<b>Supplier payments only:</b> {r8['n_pay']} payments, {_money(r8['paid'])}", xa + 20, by + 8, xb - xa - 40, 22, fill=WHITE, stroke=WHITE,
          size=SMALL, rounded=False)
    gap = _day(thru) - _day(pay_end)
    _note(d, f"The upper strip is to scale from {first} to {last}; the lower strip enlarges {z0} to {z1}. Payroll posts through {pay_end}, {gap} days before "
             f"the last year-end, and the ledger runs {_day(last) - _day(thru)} days past it with supplier payments alone, so a balance at the ledger's "
             f"last date is not a year-end balance. The data-through date is the last year-end itself, where the last pair of closes sits.", py + 250)
    return d


# -- Excel pieces: the model workbook's worksheets ----------------------------------------------------------------------------

def _book(sheet: str):
    """One worksheet of the model workbook with its saved values (the guides' own reader)."""
    return _g().cached()[sheet]


def _us_date(iso: str) -> str:
    """An ISO date as Excel's short date shows it."""
    y, m, dd = iso.split("-")
    return f"{int(m)}/{int(dd)}/{y}"


def _acct(x: float | None, places: int = 2) -> str:
    """The workbook's number format #,##0.00;(#,##0.00);"-": negatives in parentheses, zero as a dash, a blank cell empty."""
    if x is None:
        return ""
    if abs(x) < 0.005:
        return "-"
    text = f"{abs(x):,.{places}f}"
    return f"({text})" if x < 0 else text


def _wrap(text: str, width: float, size: int = SMALL, bold: bool = False) -> list[str]:
    """A greedy word wrap measured with text_width."""
    out, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if not cur or text_width(trial, size, bold) <= width:
            cur = trial
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    return out


def _wrapped(text: str, width: float, bold: bool = False, **kw) -> dict:
    """A cell that wraps its text over as many lines as the column needs (the cell's lines are kept in "lines")."""
    lines = _wrap(text, width - 16, bold=bold)
    html = "<br>".join(esc(line) for line in lines)
    return dict(html=f"<b>{html}</b>" if bold else html, lines=len(lines), **kw)


def _gap(d: Diagram, x: float, y: float, w: float, text: str, h: float = 22) -> float:
    """A band that stands for the rows of a worksheet that the figure leaves out."""
    d.box(f"<i>{esc(text)}</i>", x, y, w, h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, rounded=False, dashed=True)
    return y + h


def _ws(d: Diagram, x: float, y: float, letters: list[str], widths: list[float], rows: list[dict], number_color: str = GRAY,
        show_letters: bool = True, row_h: float = 22) -> dict:
    """A worksheet with a letter row and rows of any height.  widths[0] is the row-number column; a row is {"n": row number,
    "cells": [cell, ...], "h": height}, its cells taken in order from the first column (a cell with span uses that many columns); a
    cell is a string or a dict: text, bold, italic, align, color, fill, stroke, html (a ready label), span, clip (False keeps a long
    text whole), valign.  A cell made by _wrapped() sets the row's height when the row has no "h".  Returns {(row index, column):
    (x, y, w, h)} and "bottom"."""
    xs = [x]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    top = 22 if show_letters else 0
    if show_letters:
        for cx, w, letter in zip(xs, widths, ["", *letters]):
            d.box(esc(letter), cx, y, w, 22, fill=GRAY_TINT, stroke=RULE, color=GRAY, size=SMALL, rounded=False)
    geo: dict = {}
    ry = y + top
    for i, row in enumerate(rows):
        lines = max([c.get("lines", 1) for c in row["cells"] if isinstance(c, dict)] or [1])
        h = row.get("h", max(row_h, lines * 15 + 8))
        d.box(esc(row["n"]), xs[0], ry, widths[0], h, fill=GRAY_TINT, stroke=RULE, color=number_color, size=SMALL, rounded=False)
        cells = list(row["cells"])
        c = idx = 0
        while c < len(widths) - 1:
            cell = cells[idx] if idx < len(cells) else ""
            idx += 1
            if isinstance(cell, str):
                cell = {"text": cell}
            span = cell.get("span", 1)
            cx = xs[c + 1]
            cw = sum(widths[c + 1:c + 1 + span])
            text = cell.get("text", "")
            numeric = text[:1].isdigit() or text[:1] in "-$(" and (text[1:2].isdigit() or text == "-")
            align = cell.get("align", "right" if numeric else "left")
            bold = cell.get("bold", False)
            if "html" in cell:
                label = cell["html"]
            else:
                lead = len(text) - len(text.lstrip(" "))                      # leading spaces are the workbook's indent
                body = text.lstrip(" ")
                shown = _clip(body, cw - 3.5 * lead, bold=bold, margin=cell.get("margin", 26)) if cell.get("clip", not numeric) else body
                label = "&nbsp;" * lead + esc(shown)
                if bold:
                    label = f"<b>{label}</b>"
                if cell.get("italic"):
                    label = f"<i>{label}</i>"
            d.box(label, cx, ry, cw, h, fill=cell.get("fill", WHITE), stroke=cell.get("stroke", RULE), color=cell.get("color", INK), size=SMALL,
                  rounded=False, align=align, valign=cell.get("valign", "middle"))
            geo[(i, c)] = (cx, ry, cw, h)
            c += span
        ry += h
    geo["bottom"] = ry
    return geo


def _outline(d: Diagram, geo: dict, first: tuple[int, int], last: tuple[int, int], color: str = CORAL, inset: float = 0) -> None:
    """An outline around the cells from first to last (row index, column) of a worksheet drawn by _ws, inset so that outlines on
    neighboring cells do not touch."""
    x0, y0, _, _ = geo[first]
    x1, y1, w1, h1 = geo[last]
    left, top = max(0, x0 - 2 + inset), max(0, y0 - 2 + inset)
    right = min(860, x1 + w1 + 2 - inset)
    d.outline(left, top, right - left, y1 + h1 + 2 - inset - top, color, width=2.5, front=True)


def _formula_bar(d: Diagram, x: float, y: float, w: float, name: str, formula: str) -> None:
    """The Name Box, the fx label and the formula bar."""
    d.box(esc(name), x, y, 90, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<i>fx</i>", x + 94, y, 30, 28, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(esc(formula), x + 128, y, w - 128, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)


def _agree(ws, ref: str, expected, tol: float = 0.006) -> None:
    """The model workbook holds in this cell the value the figure draws."""
    value = ws[ref].value
    if hasattr(value, "date"):
        value = value.date().isoformat()
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        assert isinstance(value, (int, float)) and abs(value - expected) < tol, f"{ws.title}!{ref} holds {value!r}, the figure draws {expected!r}"
    else:
        assert value == expected, f"{ws.title}!{ref} holds {value!r}, the figure draws {expected!r}"


def _tabs(d: Diagram, y: float, active: str, names: list[str]) -> float:
    wb = _g().cached().sheetnames
    assert all(n in wb for n in names) and active in names, names
    xl.sheet_tabs(d, 0, y, names, active)
    return y + 26


# -- IF-17-4-A: the payroll block of the Cutoff worksheet ---------------------------------------------------------------------

def if_17_4_a() -> Diagram:
    """Rows 30 to 52 of Cutoff: the payroll owed at each year-end, with the proration of the earlier year-ends and the last
    year-end's estimate from the eight processed periods."""
    n = _n()
    r4, g4 = ctx.values("ch17.r4"), ctx.values("ch17.g4")
    data = ctx.data()
    F, P, C = data.F, data.P, data.C
    pf, pp, pc = r4["pf"], r4["pp"], r4["pc"]
    ws = _book("Cutoff")
    p = pc["p"]
    per_period = [n.register_cost(data, i)["total"] for i in p["ids"]]
    assert abs(sum(per_period) - p["cost"]) < 0.005
    shares = [pf["cross"]["inside"] / pf["cross"]["days"], pp["cross"]["inside"] / pp["cross"]["days"]]
    for ref, v in (("B31", pf["full"]["id"]), ("C31", pp["full"]["id"]), ("B32", pf["full"]["pay"]), ("C32", pp["full"]["pay"]),
                   ("B33", pf["cross"]["id"]), ("C33", pp["cross"]["id"]), ("B34", pf["cross"]["start"]), ("C34", pp["cross"]["start"]),
                   ("B35", pf["cross"]["end"]), ("C35", pp["cross"]["end"]), ("B36", pf["cross"]["days"]), ("C36", pp["cross"]["days"]),
                   ("B37", pf["cross"]["inside"]), ("C37", pp["cross"]["inside"]), ("B38", shares[0]), ("C38", shares[1]),
                   ("B39", pf["full"]["cost"]), ("C39", pp["full"]["cost"]), ("B40", pf["cross"]["share"]), ("C40", pp["cross"]["share"]),
                   ("D41", f"{p['ids'][0]}-{p['ids'][-1]}"), ("D42", f"{p['start']} to {p['end']}"), ("D43", p["wd"]), ("D44", p["cost"]),
                   ("D45", p["daily"]), ("D46", p["left"]), ("B47", pf["total"]), ("C47", pp["total"]), ("D47", pc["total"]),
                   ("B48", pf["gross"]), ("C48", pp["gross"]), ("D48", pc["gross"]), ("B49", pf["tax"]), ("C49", pp["tax"]), ("D49", pc["tax"]),
                   ("B50", pf["ben"]), ("C50", pp["ben"]), ("D50", pc["ben"]), ("B51", pf["mfg"]), ("C51", pp["mfg"]), ("D51", pc["mfg"]),
                   ("B52", pf["other"]), ("C52", pp["other"]), ("D52", pc["other"])):
        _agree(ws, ref, v)
    for k, (pid, cost) in enumerate(zip(p["ids"], per_period)):
        _agree(ws, f"F{31 + k}", pid)
        _agree(ws, f"G{31 + k}", cost)
    widths = [28, 316, 96, 96, 96, 18, 130, 80]                       # row numbers, then A to G
    letters = list("ABCDEFG")
    ye = [f"{y}-12-31" for y in (F, P, C)]
    d = Diagram("The Payroll Block of the Cutoff Worksheet")
    formula = g4["f"]["d_owed"]
    assert formula == "=ROUND(D44/D43*D46,2)", formula
    _formula_bar(d, 0, 0, 860, "D47", formula)
    sy = 40.0
    _ws(d, 0, sy, letters, widths, [], show_letters=True)
    y = _gap(d, 0, sy + 22, sum(widths), "Rows 1 to 29: revenue by delivery year, the invoices posted late and the lines never invoiced")
    money = lambda v: "" if v is None else f"{v:,.2f}"                    # noqa: E731
    H = 316
    rows = [dict(n="30", cells=[_wrapped("Payroll: the work of each year's last days, paid in the next year", H, bold=True)]
                 + [dict(text=_us_date(x), bold=True, align="right") for x in ye] + [dict(), _wrapped("Last eight processed periods", widths[6], bold=True),
                                                                                  dict(text="Cost", bold=True, align="right")])]
    sheet_rows = [
        ("31", "Pay period ending in the year and paid in the next", [str(pf["full"]["id"]), str(pp["full"]["id"]), ""]),
        ("32", "  its pay date", [_us_date(pf["full"]["pay"]), _us_date(pp["full"]["pay"]), ""]),
        ("33", "Pay period crossing the year-end", [str(pf["cross"]["id"]), str(pp["cross"]["id"]), ""]),
        ("34", "  its first day", [_us_date(pf["cross"]["start"]), _us_date(pp["cross"]["start"]), ""]),
        ("35", "  its last day", [_us_date(pf["cross"]["end"]), _us_date(pp["cross"]["end"]), ""]),
        ("36", "  its working days", [str(pf["cross"]["days"]), str(pp["cross"]["days"]), ""]),
        ("37", "  its working days within the year", [str(pf["cross"]["inside"]), str(pp["cross"]["inside"]), ""]),
        ("38", "  share within the year", [f"{shares[0]:.4f}", f"{shares[1]:.4f}", ""]),
        ("39", "Registers of the period paid in the next year (gross pay, employer taxes, benefits)", [money(pf["full"]["cost"]), money(pp["full"]["cost"]), ""]),
        ("40", "Registers of the crossing period, times the share", [money(pf["cross"]["share"]), money(pp["cross"]["share"]), ""]),
        ("41", "Last eight processed pay periods: first and last", ["", "", f"{p['ids'][0]}-{p['ids'][-1]}"]),
        ("42", "  their first and last day", ["", "", ""]),
        ("43", "  their working days", ["", "", str(p["wd"])]),
        ("44", "  their cost (registers)", ["", "", money(p["cost"])]),
        ("45", "  cost per working day", ["", "", money(p["daily"])]),
        ("46", "  working days left in the year after the last processed period", ["", "", str(p["left"])]),
        ("47", "Payroll owed at the year-end", [money(pf["total"]), money(pp["total"]), money(pc["total"])]),
        ("48", "  gross pay", [money(pf["gross"]), money(pp["gross"]), money(pc["gross"])]),
        ("49", "  employer payroll taxes", [money(pf["tax"]), money(pp["tax"]), money(pc["tax"])]),
        ("50", "  employer benefits", [money(pf["ben"]), money(pp["ben"]), money(pc["ben"])]),
        ("51", "  manufacturing (to 1090, ends in 5080)", [money(pf["mfg"]), money(pp["mfg"]), money(pc["mfg"])]),
        ("52", "  other cost centers (salary accounts and 6060)", [money(pf["other"]), money(pp["other"]), money(pc["other"])]),
    ]
    for k, (num, label, vals) in enumerate(sheet_rows):
        bold = num == "47"
        cells = [dict(text=label, bold=bold)] + [dict(text=v, bold=bold, align="left" if num == "41" else "right") for v in vals] + [dict()]
        if k < len(p["ids"]):
            cells += [dict(text=str(p["ids"][k]), align="left"), dict(text=money(per_period[k]), align="right")]
        if num == "42":
            cells[3] = dict(text=f"{p['start']} to {p['end']}", span=3, align="left", clip=False)       # a long text overflows into empty cells
        rows.append(dict(n=num, cells=cells))
    geo = _ws(d, 0, y, [], widths, rows, show_letters=False)
    row = lambda num: int(num) - 30                                                                            # noqa: E731
    _outline(d, geo, (row("36"), 1), (row("38"), 2), TEAL, inset=1.5)
    _outline(d, geo, (row("43"), 3), (row("46"), 3), CORAL, inset=1.5)
    _outline(d, geo, (row("30"), 5), (row("38"), 6), CORAL, inset=1.5)
    xl.select(d, *geo[(row("47"), 3)])
    bottom = _gap(d, 0, geo["bottom"], sum(widths), "Rows 53 to 90: payroll owed by cost center, A1, the interest on the notes and A4")
    bottom = _tabs(d, bottom + 8, "Cutoff", ["Accrued Expenses", "Cutoff", "Adjustments"])
    _note(d, f"Outlined in teal: the proration of the crossing period at the two earlier year-ends, by working days ({pf['cross']['inside']} of "
             f"{pf['cross']['days']} and {pp['cross']['inside']} of {pp['cross']['days']}). Outlined in coral: the last year-end's estimate, the cost per working "
             f"day of the eight processed periods times the {p['left']} working days left, and the eight periods it uses. D47 is selected. A long label is cut at "
             "its column's edge, as Excel shows it.", bottom + 4)
    return d


# -- IF-17-5-A: the schedule of adjustments ----------------------------------------------------------------------------------

def if_17_5_a() -> Diagram:
    """The top block of Adjustments in two panes: rows A1 to A4 with their total and the adjusted net income, R1 and R2, and P1
    to P3 with the passed items in aggregate; the text columns in the first pane and the effects in the second."""
    r5 = ctx.values("ch17.r5")
    ws = _book("Adjustments")
    a, tot = r5["a"], r5["total"]
    pay_p, pay_c = r5["pay_p"]["total"], r5["pay_c"]["total"]
    num = {}                                                                         # row -> [E, F, G, H, I] as the workbook holds them
    num[5] = [a["A1"]["re"], a["A1"]["P"], a["A1"]["C"], -pay_p, -pay_c]
    num[6] = [a["A2"]["re"], a["A2"]["P"], a["A2"]["C"], r5["cut_p"], r5["cut_c"]]
    num[7] = [a["A3"]["re"], a["A3"]["P"], a["A3"]["C"], r5["old_p"], r5["old_c"]]
    num[8] = [a["A4"]["re"], a["A4"]["P"], a["A4"]["C"], -r5["intr_p"], -r5["intr_c"]]
    num[9] = [tot["re"], tot["P"], tot["C"], r5["equity_p"], r5["equity_c"]]
    num[10] = [None, r5["adj_ni_p"], r5["adj_ni_c"], None, None]
    num[12] = [None, None, None, r5["cur_p"], r5["cur_c"]]
    num[13] = [None, None, None, -r5["c1090_p"], -r5["c1090_c"]]
    num[15] = [None, None, r5["p1_income"], r5["p1_prior"], r5["p1"]]
    num[16] = [None, None, r5["p2"]["income"], -(r5["p2"]["rev_prior"] - r5["p2"]["cost_prior"]), r5["p2"]["effect"]]
    num[17] = [None, None, r5["p3"]["effect"], None, r5["p3"]["effect"]]
    num[18] = [None, None, r5["agg_income"], None, r5["aggregate"]]
    for r, vals in num.items():
        for col, v in zip("EFGHI", vals):
            if v is not None:
                _agree(ws, f"{col}{r}", v)
            else:
                assert ws[f"{col}{r}"].value in (None, 0), f"{col}{r} holds {ws[f'{col}{r}'].value!r}"
    heads = [ws.cell(4, c).value for c in range(1, 12)]
    assert heads[:5] == ["No.", "Adjustment", "Accounts", "Evidence", "Retained earnings, 1 January 2025"] and heads[9:] == ["Type", "Decision"], heads
    shown = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    text = lambda r, c: "" if ws.cell(r, c).value is None else str(ws.cell(r, c).value)                          # noqa: E731
    bold_rows = {9, 18}
    letters1, widths1 = list("ABCD"), [30, 64, 300, 246, 220]
    letters2, widths2 = list("EFGHIJK"), [30, 100, 96, 96, 100, 100, 170, 168]
    rows1, rows2 = [], []
    for r in shown:
        h = 20 if r in (11, 14) else None
        kw = dict(h=h) if h else {}
        if r == 4:
            rows1.append(dict(n="4", cells=[dict(text=heads[0], bold=True), dict(text=heads[1], bold=True), dict(text=heads[2], bold=True),
                                            dict(text=heads[3], bold=True)], h=26))
            rows2.append(dict(n="4", cells=[_wrapped(heads[4], widths2[1], bold=True, align="right"), _wrapped(heads[5], widths2[2], bold=True, align="right"),
                                            _wrapped(heads[6], widths2[3], bold=True, align="right"), _wrapped(heads[7], widths2[4], bold=True, align="right"),
                                            _wrapped(heads[8], widths2[5], bold=True, align="right"), dict(text=heads[9], bold=True),
                                            dict(text=heads[10], bold=True)]))
            continue
        b = r in bold_rows
        cells1 = [dict(text=text(r, c), bold=b) for c in (1, 2, 3, 4)]
        if r == 10:
            cells1 = [dict(text=text(r, 1), span=2, clip=False)]                         # the label overflows into the empty cell beside it
        rows1.append(dict(n=str(r), cells=cells1, **kw))
        vals = num.get(r)
        cells = [dict(text=_acct(v), bold=b, align="right", clip=False) for v in vals] if vals else [dict()] * 5
        cells += [dict(text=text(r, 10)), dict(text=text(r, 11))]
        rows2.append(dict(n=str(r), cells=cells, **kw))
    d = Diagram("The Schedule of Adjustments")
    d.text("<i>Columns A to D</i>", 0, 0, 300, 18, size=SMALL, color=GRAY)
    geo1 = _ws(d, 0, 20, letters1, widths1, rows1, show_letters=True)
    y2 = geo1["bottom"] + 12
    d.text("<i>The same rows after scrolling right: columns E to K</i>", 0, y2, 520, 18, size=SMALL, color=GRAY)
    _formula_bar(d, 0, y2 + 22, 860, "G10", _g().clean(_g().workbook()["Adjustments"]["G10"].value))
    geo2 = _ws(d, 0, y2 + 58, letters2, widths2, rows2, show_letters=True)
    idx = {r: k for k, r in enumerate(shown)}
    for geo, last in ((geo1, 3), (geo2, 6)):
        _outline(d, geo, (idx[9], 0), (idx[9], last), CORAL, inset=1.5)
        _outline(d, geo, (idx[10], 0), (idx[10], last), TEAL, inset=1.5)
    xl.select(d, *geo2[(idx[10], 2)])
    bottom = _tabs(d, geo2["bottom"] + 8, "Adjustments", ["Cutoff", "Adjustments", "Statements"])
    _note(d, f"Outlined in coral: the total of A1 to A4 on retained earnings, on each year's income and on the year-end balances. Outlined in teal: the adjusted net "
             f"income, recorded income plus that total, with G10 selected. A text cell shows its first line, as a row of fixed height does; rows 11 and 14 are blank and "
             f"row 19, the clearly trivial freight estimate, is below the block drawn.", bottom + 4)
    return d


# -- IF-17-6-A: the statement of cash flows ----------------------------------------------------------------------------------

def _recorded_flows(n, data, year: int) -> dict:
    """The working-capital changes of a year taken from the recorded balances, with no adjustment (the workbook's 'as recorded'
    columns): the same lines as wc_lines in the notes."""
    special = set(n.CASH + n.RECEIVABLES + n.INVENTORIES + n.PAYABLES + ["2020"] + n.SALES_TAX)
    other_assets = [x for x in n.accounts_of(data, "Current Asset", "Contra Current Asset") if x not in special]
    other_liabilities = [x for x in n.accounts_of(data, "Current Liability") if x not in special]

    def lines(y: int) -> dict:
        t = lambda nums: n.bal(data, nums, n.ye(y))                                                            # noqa: E731
        return dict(recv=t(n.RECEIVABLES), inv=t(n.INVENTORIES), pay=-t(n.PAYABLES + ["2020"]), stax=-t(n.SALES_TAX),
                    other=-t(other_liabilities) - t(other_assets))

    a, b = lines(year - 1), lines(year)
    return dict(recv=-(b["recv"] - a["recv"]), inv=-(b["inv"] - a["inv"]), pay=b["pay"] - a["pay"], stax=b["stax"] - a["stax"],
                other=b["other"] - a["other"])


def if_17_6_a() -> Diagram:
    """Rows 67 to 86 of Statements: the cash flows of the last year and of the comparative year restated, beside each year as
    recorded, with the operating totals outlined and the two check rows."""
    n = _n()
    r6 = ctx.values("ch17.r6")
    data = ctx.data()
    P, C = data.P, data.C
    ws = _book("Statements")
    cf = {C: r6["cf_c"], P: r6["cf_p"]}
    rec = {y: _recorded_flows(n, data, y) for y in (C, P)}
    ni_rec = {y: n.net_income(data, y) for y in (C, P)}
    cash = {y: (n.bal(data, n.CASH, n.ye(y - 1)), n.bal(data, n.CASH, n.ye(y))) for y in (C, P)}
    rows_spec = []                                                                  # (sheet row, label, [B, C, D, E] values or None, bold)
    cols = [(C, "adj"), (P, "adj"), (C, "rec"), (P, "rec")]
    pick = lambda key, y, kind: (cf[y][key] if kind == "adj" or key in ("dep", "loss") else {"ni": ni_rec[y], **rec[y]}[key])    # noqa: E731
    line = lambda row, label, key, bold=False: rows_spec.append((row, label, [pick(key, y, k) for y, k in cols], bold))      # noqa: E731
    line(68, "Net income", "ni")
    line(69, "Depreciation", "dep")
    line(70, "Loss on disposal of equipment", "loss")
    line(71, "Change in receivables", "recv")
    line(72, "Change in inventories (with 1090)", "inv")
    line(73, "Change in accounts payable and goods received not invoiced", "pay")
    line(74, "Change in sales tax payable", "stax")
    line(75, "Change in accrued and other current items", "other")
    op = [sum(v[i] for _, _, v, _ in rows_spec) for i in range(4)]
    rows_spec.append((76, "Net cash from operating activities", op, True))
    rows_spec.append((77, "Purchases of property and equipment, paid in cash", [-cf[y]["paid"] for y, _ in cols], False))
    rows_spec.append((78, "Proceeds from disposals", [cf[y]["proceeds"] for y, _ in cols], False))
    rows_spec.append((79, "Net cash from investing activities", [cf[y]["investing"] for y, _ in cols], True))
    rows_spec.append((80, "Principal payments on notes payable", [cf[y]["financing"] for y, _ in cols], False))
    rows_spec.append((81, "Net cash from financing activities", [cf[y]["financing"] for y, _ in cols], True))
    change = [op[i] + cf[y]["investing"] + cf[y]["financing"] for i, (y, _) in enumerate(cols)]
    rows_spec.append((82, "Change in cash", change, False))
    rows_spec.append((83, "Cash at the beginning of the year", [cash[y][0] for y, _ in cols], False))
    rows_spec.append((84, "Cash at the end of the year", [cash[y][1] for y, _ in cols], False))
    rows_spec.append((85, "Change in cash less the balance sheets", [round(change[i] - (cash[y][1] - cash[y][0]), 2) for i, (y, _) in enumerate(cols)], False))
    rows_spec.append((86, "Adjusted less recorded (the adjustments change no total)", [round(op[0] - op[2], 2), round(op[1] - op[3], 2), None, None], False))
    for row, label, vals, _ in rows_spec:
        assert ws.cell(row, 1).value == label, (row, ws.cell(row, 1).value, label)
        for col, v in zip("BCDE", vals):
            if v is None:
                assert ws[f"{col}{row}"].value is None
            else:
                _agree(ws, f"{col}{row}", v, tol=0.01)
    assert abs(op[0] - cf[C]["operating"]) < 0.01 and abs(op[1] - cf[P]["operating"]) < 0.01 and abs(op[2] - op[0]) < 0.01 and abs(op[3] - op[1]) < 0.01, \
        "the adjusted and recorded operating totals agree"
    assert abs(change[0] - cf[C]["cash"]) < 0.01 and abs(change[1] - cf[P]["cash"]) < 0.01
    heads = [ws.cell(67, c).value for c in range(1, 6)]
    assert heads == ["Statement of cash flows (indirect method)", C, f"{P} (restated)", f"{C} as recorded", f"{P} as recorded"], heads
    widths = [28, 380, 113, 113, 113, 113]
    d = Diagram("The Statement of Cash Flows")
    formula = _g().clean(_g().workbook()["Statements"]["B76"].value)
    assert formula == "=SUM(B68:B75)", formula
    _formula_bar(d, 0, 0, 860, "B76", formula)
    sy = 40.0
    _ws(d, 0, sy, list("ABCDE"), widths, [], show_letters=True)
    y = _gap(d, 0, sy + 22, sum(widths), f"Rows 1 to 66: the balance sheets, the statements of income, the ratios and the statement of changes in equity")
    rows = [dict(n="67", cells=[dict(text=heads[0], bold=True)] + [_wrapped(str(h), widths[k + 2], bold=True, align="right") for k, h in enumerate(heads[1:])])]
    for row, label, vals, bold in rows_spec:
        rows.append(dict(n=str(row), cells=[dict(text=label, bold=bold)] + [dict(text=_acct(v), bold=bold, align="right") for v in vals]))
    geo = _ws(d, 0, y, [], widths, rows, show_letters=False)
    op_row = 76 - 67
    for col, color in ((1, CORAL), (3, CORAL), (2, TEAL), (4, TEAL)):
        _outline(d, geo, (op_row, col), (op_row, col), color, inset=1.5)
    bottom = _gap(d, 0, geo["bottom"], sum(widths), "Rows 87 to 91: supplemental information, the interest paid and the equipment acquired with a note")
    bottom = _tabs(d, bottom + 8, "Statements", ["Adjustments", "Statements", "Notes"])
    _note(d, f"Outlined: the net cash from operating activities, coral for {C} (adjusted, then as recorded) and teal for {P}. Each pair is equal, so row 86 reads a "
             f"dash: no adjustment moves cash, though the lines above the total differ. The change in cash of {_acct(cf[C]['cash'])} in {C} agrees with the balance "
             f"sheets (row 85), and a zero is shown as a dash, as the workbook's number format does.", bottom + 4)
    return d


# -- Power BI pieces: the Review page of the model answer --------------------------------------------------------------------

def _page_ids() -> list[str]:
    return json.loads((REPORT / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]


def _page(page: str) -> dict:
    return json.loads((REPORT / "pages" / page / "page.json").read_text(encoding="utf-8"))


def _hidden(page: str) -> bool:
    return _page(page).get("visibility") == "HiddenInViewMode"


def _visual(page: str, name: str) -> dict:
    return json.loads((REPORT / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))


def _title(page: str, name: str) -> str:
    v = _visual(page, name)["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
    return v.strip("'").replace("''", "'")


def _projections(page: str, name: str, role: str) -> list[str]:
    return [p["nativeQueryRef"] for p in _visual(page, name)["visual"]["query"]["queryState"][role]["projections"]]


def _page_tabs(active: str, d: Diagram, y: float) -> None:
    """The page tabs under the canvas: the visible pages around the active one, as the report orders them."""
    order = [p for p in _page_ids() if not _hidden(p)]
    i = order.index(active)
    shown = order[max(i - 1, 0):i + 2]
    pbi.page_tabs(d, 4, y, [_page(p)["displayName"] for p in shown], _page(active)["displayName"])


def _frame(d: Diagram, x: float, y: float, w: float, h: float, title: str | None, lines: int | None = None) -> tuple[float, float, float, float]:
    """A visual's container with its title.  Returns the inner area."""
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    if not title:
        return x + 6, y + 6, w - 12, h - 12
    label = f"<b>{esc(title)}</b>"
    lines = lines or kit.lines_for(label, w - 12, SMALL, bold=True)
    th = 16 * lines + 4
    d.text(label, x + 6, y + 4, w - 12, th, size=SMALL)
    return x + 6, y + 4 + th + 2, w - 12, h - th - 12


def _signed(x: float) -> str:
    """A balance as the measures' format #,0.00 shows it, with a true minus sign."""
    return (MINUS if x < 0 else "") + f"{abs(x):,.2f}"


def _slider_unset(d: Diagram, x: float, y: float, w: float, h: float, title: str, low: str, high: str) -> None:
    """A slicer in the Single style over a what-if parameter with no value chosen: the track and its two ends."""
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 20, size=SMALL)
    t0, t1, ty = x + 22, x + w - 22, y + h - 38
    d.box("", t0, ty - 2, t1 - t0, 4, fill=RULE, stroke=RULE, rounded=False)
    d.text(low, t0 - 12, ty + 8, 60, 18, size=SMALL, color=GRAY)
    d.text(high, t1 - 62, ty + 8, 74, 18, size=SMALL, color=GRAY, align="right")


def _cards(d: Diagram, x: float, y: float, w: float, h: float, title: str, items: list[tuple[str, str]]) -> None:
    """A card visual with one field per card: the value above its label."""
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 18, size=SMALL)
    gap = 6
    cw = (w - 12 - gap * (len(items) - 1)) / len(items)
    for i, (label, value) in enumerate(items):
        cx = x + 6 + i * (cw + gap)
        d.box("", cx, y + 26, cw, h - 32, fill=WHITE, stroke=RULE, rounded=True)
        d.text(f"<b>{esc(value)}</b>", cx + 2, y + 32, cw - 4, 24, size=15, align="center")
        d.text(esc(label), cx + 2, y + 58, cw - 4, 20, size=SMALL, color=GRAY, align="center")


def _matrix(d: Diagram, x: float, y: float, title: str, row_w: float, cols: list[tuple[str, float]], row_heads: list[str], cells: list[list[str]],
            row_h: float = 19, bold_rows: set[int] | None = None, levels: list[int] | None = None, fills: dict | None = None) -> dict:
    """A matrix visual: a title, the column headings and the rows (a level indents a row under its parent).  Returns the cell
    geometry keyed (row, column) and the visual's bottom edge."""
    inner = row_w + sum(w for _, w in cols)
    w = inner + 12
    hh = 26
    label = f"<b>{esc(title)}</b>"
    th = 16 * kit.lines_for(label, w - 12, SMALL, bold=True) + 4
    h = th + 12 + hh + len(row_heads) * row_h
    ix, iy, _, _ = _frame(d, x, y, w, h, title)
    bold_rows, levels, fills = bold_rows or set(), levels or [0] * len(row_heads), fills or {}
    xs, cx = [], ix + row_w
    for head, wd in cols:
        xs.append(cx)
        d.text(f"<b>{esc(head)}</b>", cx, iy, wd - 4, hh, size=SMALL, align="right", valign="bottom")
        cx += wd
    d.box("", ix, iy + hh - 1, inner, 1, fill=INK, stroke=INK, rounded=False)
    geometry = {}
    for r, head in enumerate(row_heads):
        ry = iy + hh + r * row_h
        bold = r in bold_rows
        text = "&nbsp;" * (5 * levels[r]) + esc(head)
        d.text(f"<b>{text}</b>" if bold else text, ix + 4, ry, row_w - 4, row_h, size=SMALL, align="left", valign="middle")
        for c, ((_, wd), vx) in enumerate(zip(cols, xs)):
            value = cells[r][c]
            assert not value or text_width(value, SMALL, bold) + 6 <= wd, f"{title}: {value!r} does not fit its {wd:.0f} px column"
            fill = fills.get((r, c), WHITE)
            d.box(f"<b>{esc(value)}</b>" if bold else esc(value), vx, ry, wd, row_h, fill=fill, stroke=fill, size=SMALL, align="right", rounded=False)
            geometry[(r, c)] = (vx, ry, wd, row_h)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, width=inner)


def _table(d: Diagram, x: float, y: float, title: str, headers: list[str], widths: list[float], rows: list[list[str]], aligns: list[str],
           row_h: float = 19) -> dict:
    """A table visual: a title, a header row and banded rows."""
    w = sum(widths) + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * kit.lines_for(label, w - 12, SMALL, bold=True) + 4
    h = th + 12 + row_h + len(rows) * row_h
    ix, iy, _, _ = _frame(d, x, y, w, h, title)
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    for head, cx, wd, al in zip(headers, xs, widths, aligns):
        d.box(f"<b>{esc(_clip(head, wd, margin=8, bold=True))}</b>", cx, iy, wd, row_h, fill=WHITE, stroke=WHITE, size=SMALL, align=al, rounded=False)
    d.box("", ix, iy + row_h - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    geometry = {}
    for r, row in enumerate(rows):
        ry = iy + row_h * (r + 1)
        for c, (value, cx, wd, al) in enumerate(zip(row, xs, widths, aligns)):
            fill = WHITE if r % 2 == 0 else GRAY_TINT
            d.box(esc(_clip(value, wd, margin=8 if al == "right" else 16)), cx, ry, wd, row_h, fill=fill, stroke=fill, size=SMALL, align=al, rounded=False)
            geometry[(r, c)] = (cx, ry, wd, row_h)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix)


# -- IF-17-2-A: the Review page ---------------------------------------------------------------------------------------------

def if_17_2_a() -> Diagram:
    """The Review page of the model answer with the threshold at its default: the what-if slicer, the card of the threshold and the two
    materialities, the matrix of statement lines (Inventories expanded to its accounts) with its Flag, and the table of the changes
    above the threshold."""
    n = _n()
    r2, g2 = ctx.values("ch17.r2"), ctx.values("ch17.g2")
    data = ctx.data()
    F, P, C = data.F, data.P, data.C
    page = "review"
    titles = {k: _title(page, v) for k, v in (("slicer", "threshold"), ("card", "materiality"), ("matrix", "reviewMatrix"), ("table", "aboveTable"))}
    assert titles == {"slicer": g2["t_threshold"], "card": g2["t_card"], "matrix": g2["t_matrix"], "table": g2["t_above"]}, titles
    cards = _projections(page, "materiality", "Data")
    assert cards == ["Threshold Value", "Materiality 2026", "Materiality 2025"], cards
    assert _projections(page, "reviewMatrix", "Rows") == ["StatementLine", "AccountLabel"]
    mcols = _projections(page, "reviewMatrix", "Values")
    assert mcols == ["Balance 2024", "Balance 2025", "Balance 2026", "Change 2025 to 2026", "Flag"], mcols
    tcols = _projections(page, "aboveTable", "Values")
    assert tcols == ["AccountLabel", "Change 2025 to 2026", "Absolute Change"], tcols
    assert "GENERATESERIES ( 0, 1000000, 25000 )" in (MODEL / "definition" / "tables" / "Threshold.tmdl").read_text(encoding="utf-8")
    mat_c, mat_p = n.materiality(data, C), n.materiality(data, P)
    assert abs(mat_c - r2["mat_c"]) < 0.005 and abs(mat_p - r2["mat_p"]) < 0.005
    threshold = mat_c                                               # the slider has no value chosen, so Threshold Value is the 2026 materiality
    tb = {y: n.tb(data, n.ye(y)) for y in (F, P, C)}
    chart = n.chart(data)
    # the statement lines, in the order the model sorts them, and the accounts under each
    ws = _g().cached()["Working TB"]
    line_of = {str(ws.cell(r, 2).value): ws.cell(r, 8).value for r in range(2, ws.max_row + 1) if ws.cell(r, 2).value is not None}
    order = re.findall(r'"([^"]+)"', re.search(r"List\.PositionOf\(\{(.*?)\}, \[StatementLine\]\)",
                                                  (MODEL / "definition" / "tables" / "WorkingTB.tmdl").read_text(encoding="utf-8")).group(1))
    accounts = {line: sorted((a for a, l in line_of.items() if l == line), key=int) for line in order}

    def balances(nums: list[str]) -> list[float | None]:
        out = []
        for y in (F, P, C):
            present = [tb[y][a] for a in nums if a in tb[y]]
            out.append(sum(present) if present else None)
        return out

    def cells_of(vals: list[float | None]) -> list[str]:
        change = (vals[2] or 0.0) - (vals[1] or 0.0)
        return [("" if v is None else _signed(v)) for v in vals] + [_signed(change), "Above threshold" if abs(change) > threshold else ""]

    expand = "Inventories"
    heads, cells, levels, bold, fills, flagged_lines = [], [], [], set(), {}, []
    for line in order:
        vals = balances(accounts[line])
        if all(v is None for v in vals):
            continue
        row = cells_of(vals)
        heads.append(("– " if line == expand else "+ ") + line)
        cells.append(row)
        levels.append(0)
        if row[4]:
            fills[(len(heads) - 1, 4)] = AMBER_TINT
            flagged_lines.append(line)
        if line == expand:
            bold.add(len(heads) - 1)
            for a in accounts[line]:
                if not any(a in tb[y] for y in (F, P, C)):
                    continue
                avals = balances([a])
                arow = cells_of(avals)
                heads.append(f"{a} {chart[a]['name']}")
                cells.append(arow)
                levels.append(1)
                if arow[4]:
                    fills[(len(heads) - 1, 4)] = AMBER_TINT
    # the table of the changes above the threshold
    change = {a: tb[C].get(a, 0.0) - tb[P].get(a, 0.0) for a in set(tb[P]) | set(tb[C])}
    above = sorted([(a, v) for a, v in change.items() if abs(v) > threshold], key=lambda t: (-abs(t[1]), t[0]))
    assert [a for a, _ in above if a != "3030"] == [x["n"] for x in r2["above"]] and "3030" in [a for a, _ in above] and len(above) == g2["n_right"] + 1
    assert abs(change["3030"] + g2["re_change"]) < 0.005, "retained earnings moves by the 2025 net income closed into it"
    trows = [[f"{a} {chart[a]['name']}", _signed(v), _signed(abs(v))] for a, v in above]
    no_account = [ln for ln in flagged_lines if not any(abs(change[a]) > threshold for a in accounts[ln] if a in change)]
    pad = 16
    d_probe = Diagram("probe")
    row_w, cw = 268.0, [96, 96, 96, 140, 116]

    def draw(d: Diagram) -> tuple[dict, dict, float]:
        _slider_unset(d, pad, pad, 200, 100, titles["slicer"], "0", _signed(1000000).replace(".00", ""))
        _cards(d, pad + 212, pad, 860 - 2 * pad - 212, 100, titles["card"],
               [("Threshold Value", _signed(threshold)), ("Materiality 2026", _signed(mat_c)), ("Materiality 2025", _signed(mat_p))])
        m = _matrix(d, pad, pad + 112, titles["matrix"], row_w, list(zip(mcols, cw)), heads, cells, levels=levels, bold_rows=bold, fills=fills)
        t = _table(d, pad, m["bottom"] + 10, titles["table"], ["Account", "Change 2025 to 2026", "Absolute Change"], [250, 140, 124], trows,
                   ["left", "right", "right"])
        call_text = (f"<b>{len(above) - 1} accounts and retained earnings are above the threshold.</b> Retained earnings moves by "
                     f"{_signed(abs(change['3030']))}, the {P} net income closed into it. A line is flagged on its own change: "
                     + (f"{no_account[0]} is above the threshold as a line, though none of its accounts is." if len(no_account) == 1 else
                        f"{', '.join(no_account)} are above the threshold as lines, though none of their accounts is."))
        bottom = kit.callout(d, call_text, t["right"] + 12, m["bottom"] + 10, 860 - pad - t["right"] - 12, "amber")
        return m, t, max(t["bottom"], bottom)

    probe_bottom = draw(d_probe)[2] + pad
    d = Diagram("The Review Page")
    pbi.canvas(d, 0, 0, 860, probe_bottom)
    draw(d)
    _page_tabs(page, d, probe_bottom + 4)
    _note(d, f"Report view, page Review, with the Threshold slider as it opens: no value is chosen, so Threshold Value is the {C} materiality. Inventories is "
             "expanded to its accounts; a + marks a line with accounts under it. A flagged cell reads Above threshold and is tinted. The page's text box is "
             "not drawn.", probe_bottom + 34)
    return d


# -- IF-17-9-A: the memo and its appendix -----------------------------------------------------------------------------------------

def _memo_outline() -> dict:
    """What Requirement 9 asks for, read from the case text and from the requirement's guide: the page limits, the columns of the
    table of the four required matters and the matters themselves."""
    case = _case_text()
    m = re.search(r"memorandum of no more than (\w+) pages[^.]*?appendix of exhibits of no more than (\w+) pages", case)
    words = {"one": 1, "two": 2, "three": 3, "four": 4}
    pages, appendix = words[m.group(1)], words[m.group(2)]
    guide = (GUIDES / "req-9-assemble-the-package-and-write-the-memo-to-the.md").read_text(encoding="utf-8")
    head = re.search(r"^\| (Matter) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", guide, re.M)
    cols = [c.strip() for c in head.groups()]
    block = guide[head.end():guide.index("Then the other matters")]
    matters = [m_.group(1) for m_ in re.finditer(r"^\| ([A-Z][A-Za-z ]+) \|", block, re.M) if m_.group(1) != "Matter"]
    exhibits = re.split(r", | and ", re.search(r"appendix of three pages holds ([^.]+)\.", guide).group(1))
    return dict(pages=pages, appendix=appendix, cols=cols, matters=matters, exhibits=exhibits)


def _bars(d: Diagram, x: float, y: float, w: float, lines: int = 2, last: float = 0.6) -> None:
    """Gray bars that stand for lines of text."""
    for k in range(lines):
        d.box("", x, y + k * 11, w * (last if k == lines - 1 else 1.0), 5, fill=RULE, stroke=RULE, rounded=False)


def if_17_9_a() -> Diagram:
    """The memo's two pages and the appendix of three exhibits, as outlines: the opening with the recommendation and the table of the
    four required matters on page one; the other matters, the passed items, the close changes and the closing recommendation on page
    two; the three exhibits under them."""
    o = _memo_outline()
    assert (o["pages"], o["appendix"], len(o["matters"]), len(o["cols"])) == (2, 3, 4, 4), o
    assert o["matters"] == ["Tax status", "Leases", "Sales tax", "Opening balances"], o["matters"]
    assert len(o["exhibits"]) == 3, o["exhibits"]
    d = Diagram("The Memo and Its Appendix")
    PW, PH, GAPX = 410.0, 520.0, 40.0
    top = 26.0
    xs = [0.0, PW + GAPX]
    d.text("<b>The memo to the CFO</b>: at most two pages", 0, 0, 500, 22, size=SMALL)
    for k, x in enumerate(xs):
        d.box("", x, top, PW, PH, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
        d.text(f"Page {k + 1} of {o['pages']}", x, top + PH - 22, PW, 18, size=SMALL, color=GRAY, align="center")
    ix, iw = 14.0, PW - 28
    # page one: the header, the opening with the recommendation, and the four required matters
    x = xs[0] + ix
    y = top + 14
    d.box("<b>Header</b><br>To the CFO, from the staff accountant, date, subject", x, y, iw, 44, fill=GRAY_TINT, stroke=GRAY, size=SMALL, align="left",
          valign="top", rounded=False)
    y += 52
    d.box("<b>Opening</b>, readable alone<br>What the package required and what it changed<br>The effect on income, on the comparative year and on cash"
          "<br><b>The recommendation</b>: record some, hold one, do not release yet", x, y, iw, 92, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, size=SMALL,
          align="left", valign="top", rounded=False)
    d.box("", x, y, 5, 92, fill=TEAL, stroke=TEAL, rounded=False)
    y += 104
    d.text(f"<b>The {['zero', 'one', 'two', 'three', 'four'][len(o['matters'])]} required matters</b>, each in {['zero', 'one', 'two', 'three', 'four'][len(o['cols'])]} parts", x, y, iw, 20, size=SMALL)
    y += 24
    cw = [80, 96, 100, iw - 276]
    hh = 38
    cx = x
    for head, w_ in zip(o["cols"], cw):
        d.box(f"<b>{esc(head)}</b>", cx, y, w_, hh, fill=GRAY, stroke=WHITE, color=WHITE, size=SMALL, rounded=False)
        cx += w_
    y += hh
    for matter in o["matters"]:
        cx = x
        for c, w_ in enumerate(cw):
            d.box(f"<b>{esc(matter)}</b>" if c == 0 else "", cx, y, w_, 50, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
            if c:
                _bars(d, cx + 7, y + 13, w_ - 14, 3, 0.55)
            cx += w_
        y += 50
    # page two: the other matters, the passed items, the close changes and the closing recommendation
    x = xs[1] + ix
    y = top + 14
    d.box("<b>The other matters</b> the records point to, briefly<br>Cash: confirm the balance with the bank<br>Inventories: a count, a net realizable value "
          "review and a cost study<br>Later events and going concern, from Requirement 8", x, y, iw, 96, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL,
          align="left", valign="top", rounded=False)
    d.box("", x, y, 5, 96, fill=BLUE, stroke=BLUE, rounded=False)
    y += 108
    d.box("<b>The passed items</b> for the CFO's approval<br>Their total and its share of materiality", x, y, iw, 56, fill=AMBER_TINT, stroke=AMBER,
          stroke_width=1.5, size=SMALL, align="left", valign="top", rounded=False)
    d.box("", x, y, 5, 56, fill=AMBER, stroke=AMBER, rounded=False)
    y += 68
    d.box("<b>The changes to the year-end close</b><br>Accrue payroll for the days worked<br>Review the open accruals every month<br>Cut revenue off by the "
          "delivery date<br>Accrue the interest every month", x, y, iw, 96, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5, size=SMALL, align="left", valign="top",
          rounded=False)
    y += 108
    d.box("<b>The closing recommendation</b><br>Record the adjustments the records settle and the reclassifications; record the old accruals once the suppliers' "
          "evidence supports it; do not release the package until the four required matters are settled", x, y, iw, 96, fill=TEAL_TINT, stroke=TEAL,
          stroke_width=1.5, size=SMALL, align="left", valign="top", rounded=False)
    d.box("", x, y, 5, 96, fill=TEAL, stroke=TEAL, rounded=False)
    # the appendix
    ay = top + PH + 22
    d.text(f"<b>The appendix of exhibits</b>: at most {['', 'one', 'two', 'three'][o['appendix']]} pages, one page for each exhibit", 0, ay, 700, 22, size=SMALL)
    ew, eg = 270.0, 25.0
    for k, text in enumerate(o["exhibits"]):
        ex = k * (ew + eg)
        label = text[0].upper() + text[1:]
        d.box("", ex, ay + 28, ew, 96, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
        d.box(f"<b>Exhibit {k + 1}</b><br>{esc(label)}", ex, ay + 28, ew, 52, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5, size=SMALL, align="left",
              valign="top", rounded=False)
        _bars(d, ex + 10, ay + 92, ew - 20, 2, 0.7)
    _note(d, "Boxes stand for the parts of the memo in the order the requirement gives them; the gray bars stand for text. The two pages and the three exhibits "
             "are the limits the requirement sets, and the table of the four required matters is the one the guide's model memo uses.", ay + 136)
    return d


FIGURES = {
    "IF-17-1-A": if_17_1_a,
    "IF-17-3-A": if_17_3_a,
    "IF-17-8-A": if_17_8_a,
    "IF-17-0-A": if_17_0_a,
    "IF-17-0-B": if_17_0_b,
    "IF-17-4-A": if_17_4_a,
    "IF-17-5-A": if_17_5_a,
    "IF-17-6-A": if_17_6_a,
    "IF-17-2-A": if_17_2_a,
    "IF-17-9-A": if_17_9_a,
}
