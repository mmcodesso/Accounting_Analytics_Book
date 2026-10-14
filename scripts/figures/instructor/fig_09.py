"""Instructor figures of Chapter 9 (guides in facts/instructor/guides/chapter-09-sql-essentials/).

Five figures are DB Browser for SQLite mocks of the Execute SQL tab and one is a decision path.  A mock quotes its query
from the model answer script (outputs/companion/solutions/Chapter09-exercises-sql/Ex 9.N.sql, the text the guide quotes),
at the editor line where it sits in that script, and runs it read-only, so the grid and the row count come from the data.
The values in the notes come from the grid or from the guide contexts (ch09.chapter, ch09.g1 to ch09.g6).
"""

from __future__ import annotations

import re

import ctx
import dbbrowser as db
import kit
from check_figures import text_width
from drawio import CORAL, GRAY, ROW_H, SMALL, Diagram, esc

SOLUTIONS = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter09-exercises-sql"
GRID_W = 820            # the 860 px frame less the row-number column of the result grid
CELL_PAD = 20           # a cell wraps its text within about 12 px of its width, so leave room


# -- the model answers ------------------------------------------------------------------------------------------------

def _solution(n: int, wanted: str) -> tuple[str, str, int]:
    """The comment lines, the SQL and the editor line of the first comment line of the query of Ex 9.n.sql whose
    comment contains `wanted`.  The `-- Result: N rows` remark that the model answer appends to a query's last line is
    left out: a student types the query without it."""
    path = SOLUTIONS / f"Ex 9.{n}.sql"
    if not path.is_file():
        raise SystemExit(f"Model answer not found: {path} (build the solutions first)")
    lines = path.read_text(encoding="utf-8").split("\n")
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
        raise SystemExit(f"Ex 9.{n}.sql: {len(found)} queries have a comment containing {wanted!r} (expected one)")
    return found[0]


# -- the Execute SQL mock -----------------------------------------------------------------------------------------------

def _clip(text: str, width: float) -> str:
    """Cut a cell's text with an ellipsis, as DB Browser elides text wider than its column."""
    room = width - CELL_PAD
    if text_width(esc(text), SMALL, False) <= room:
        return text
    while text and text_width(esc(text + "…"), SMALL, False) > room:
        text = text[:-1]
    return text.rstrip() + "…"


def _widths(headers: list[str], rows: list[tuple], total: float = GRID_W, stretch: float = 1.5) -> list[float]:
    """Column widths that fit each heading and value, shrunk (the widest column first, its text then clipped) to fit
    the frame, or stretched a little when the result is narrow."""
    natural = []
    for c, head in enumerate(headers):
        w = text_width(f"<b>{esc(head)}</b>", SMALL, True)
        for row in rows:
            w = max(w, text_width(db.cell(row[c])[0], SMALL, False))
        natural.append(w + CELL_PAD + 2)
    if sum(natural) <= total:
        scale = min(total / sum(natural), stretch)
        return [round(w * scale) for w in natural]
    widths = list(natural)
    floor = [text_width(f"<b>{esc(h)}</b>", SMALL, True) + CELL_PAD + 2 for h in headers]
    while sum(widths) > total:
        i = max(range(len(widths)), key=lambda c: widths[c] - floor[c])
        assert widths[i] > floor[i], "the result does not fit the frame"
        widths[i] = max(floor[i], widths[i] - min(8, sum(widths) - total))
    return [round(w) for w in widths]


def _mock(d: Diagram, n: int, wanted: str, shown: slice | None = None, tab: str | None = None) -> dict:
    """The Execute SQL tab with the query of Ex 9.n.sql whose comment contains `wanted`, as a reader sees it after
    selecting the query and clicking Execute all/selected SQL.  The editor is scrolled to the query: it shows the
    comment lines and the query at their line numbers in the script.  Returns the grid and editor geometry."""
    comment, sql, line = _solution(n, wanted)
    headers, rows = db.run(sql)
    widths = _widths(headers, rows if not shown else rows[shown])
    y = db.window(d)
    editor_top = y
    text = f"{comment}\n{sql}"
    shown_lines = text.split("\n")
    n_comment = comment.count("\n") + 1
    y = db.editor(d, 0, y, 860, text, tab=tab or f"Ex 9.{n}.sql", first_line=line,
                  selection=slice(n_comment, None)) + 8
    visible = rows[shown] if shown else rows
    clipped = [tuple(_clip(v, w) if isinstance(v, str) else v for v, w in zip(row, widths)) for row in visible]
    first = (shown.start or 0) + 1 if shown else 1
    geometry = db.results(d, 0, y, headers, widths, clipped, first=first)
    y += (len(visible) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0], line=line + n_comment)
    return dict(headers=headers, rows=rows, geometry=geometry, bottom=bottom, sql_lines=shown_lines,
                n_comment=n_comment, editor_top=editor_top)


def _line_top(mock: dict, i: int) -> float:
    """The y of line i (from 0) of the text in the editor, below the editor's toolbar and tab."""
    return mock["editor_top"] + 32 + 24 + 4 + i * db.LINE_H


def _outline_lines(d: Diagram, mock: dict, first: int, last: int) -> None:
    """A coral outline around lines first..last of the editor, inset so that neighbors do not touch."""
    top = _line_top(mock, first)
    d.outline(db.GUTTER + 3, top + 1.5, 860 - db.GUTTER - 6, (last - first + 1) * db.LINE_H - 3, CORAL, width=2.5,
              front=True)


def _note(d: Diagram, text: str, y: float) -> None:
    height = kit.lines_for(text, 860, SMALL) * 15 + 12
    d.text(f"<i>{text}</i>", 0, y + 8, 860, height, size=SMALL, color=GRAY)


# -- IF-09-0-B: the statement with no table --------------------------------------------------------------------------

def if_09_0_b() -> Diagram:
    """The in-class calculator: a SELECT with no FROM that tests three expressions (question 15)."""
    year = ctx.data().C
    comment = "-- A SELECT with no table: check an expression before using it"
    sql = f"SELECT 7 / 2, 7 / 2.0, '{year}' = {year};"
    headers, rows = db.run(sql)
    assert len(rows) == 1 and len(headers) == 3, (headers, rows)
    assert list(rows[0]) == ctx.values("ch09.chapter")["q15"], "the grid differs from question 15's answer"
    d = Diagram("The Calculator Demonstration")
    widths = [120, 140, 170]
    y = db.window(d)
    y = db.editor(d, 0, y, 860, f"{comment}\n{sql}", tab="SQL 1", first_line=1, selection=slice(1, None)) + 8
    geometry = db.results(d, 0, y, headers, widths, rows)
    y += 2 * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql, line=2)
    db.emphasize_cells(d, geometry, [(0, 0), (0, 2)])
    whole, decimal, text = (db.cell(v)[0] for v in rows[0])
    _note(d, f"Outlined: the three values SQLite returns: {whole}, because two whole numbers divide as whole numbers; "
             f"{decimal}, because one decimal keeps the decimals; and {text}, because the text '{year}' is not equal to "
             f"the number {year}, so the comparison is false and SQLite writes false as 0. The statement is question 15, "
             f"and a SELECT with no FROM tests any expression before a query uses it.", bottom)
    return d


# -- IF-09-1-A: the opposite normal balances -----------------------------------------------------------------------------

def if_09_1_a() -> Diagram:
    """Exercise 9.1, Step 6: the two parenthesized groups and the contra accounts they find."""
    g, ex = ctx.values("ch09.g1"), ctx.values("ch09.ex1")
    d = Diagram("Accounts with an Opposite Normal Balance")
    mock = _mock(d, 1, "accounts whose normal balance is opposite")
    lines = mock["sql_lines"]
    where = next(i for i, text in enumerate(lines) if text.startswith("WHERE"))
    order = next(i for i, text in enumerate(lines) if text.startswith("ORDER BY"))
    groups = [i for i in range(where, order) if lines[i].lstrip().startswith(("WHERE (", "OR ("))]
    assert len(groups) == 2, lines
    _outline_lines(d, mock, groups[0], groups[1] - 1)
    _outline_lines(d, mock, groups[1], order - 1)
    rows = mock["rows"]
    normal = mock["headers"].index("NormalBalance")
    credit = sum(1 for r in rows if r[normal] == "Credit")
    debit = sum(1 for r in rows if r[normal] == "Debit")
    assert (len(rows), credit, debit) == (ex["n_opposite"], g["credit_half"], g["debit_half"]), (len(rows), credit, debit)
    _note(d, f"Outlined: the two parenthesized groups. Each pairs the account types with the normal balance that is "
             f"opposite to them, and the OR joins two complete tests. The {len(rows)} rows are the contra accounts: "
             f"{credit} with a credit balance under an Asset or Expense type and {debit} with a debit balance under a "
             f"Liability, Equity or Revenue type.", mock["bottom"])
    return d


# -- IF-09-2-A: the ten largest unfavorable purchase variances -------------------------------------------------------------

def if_09_2_a() -> Diagram:
    """Exercise 9.2, Step 5: the ranking, with the two postings that share an amount and the tie-break that orders them."""
    g = ctx.values("ch09.g2")
    d = Diagram("The Ten Largest Unfavorable Purchase Variances")
    mock = _mock(d, 2, "the ten largest unfavorable purchase variances")
    rows, headers = mock["rows"], mock["headers"]
    debit = headers.index("Debit")
    tied = [r for r, row in enumerate(rows) if row[debit] == g["tie"]]
    assert len(rows) == 10 and len(tied) == 2 and tied[1] == tied[0] + 1, (g["tie"], tied)
    assert rows[tied[0]][headers.index("PostingDate")] < rows[tied[1]][headers.index("PostingDate")], \
        "the tied postings are ordered by PostingDate, the first tie-break"
    db.emphasize_cells(d, mock["geometry"], [(tied[0], 0), (tied[1], len(headers) - 1)])
    _note(d, f"Outlined: the two postings that share ${g['tie']:,.2f}. The ORDER BY puts them in order by PostingDate "
             f"and then VoucherNumber, so every student lists them in the same order.", mock["bottom"])
    return d


# -- IF-09-4-A: the oldest past-due work orders --------------------------------------------------------------------------------

def if_09_4_a() -> Diagram:
    """Exercise 9.4, Step 5: the open work orders due on or before the last day, oldest first."""
    ex = ctx.values("ch09.ex4")
    shown = slice(0, 9)
    d = Diagram("The Oldest Past-Due Work Orders")
    mock = _mock(d, 4, "the open work orders due on or before", shown=shown)
    rows, headers = mock["rows"], mock["headers"]
    number, status = headers.index("WorkOrderNumber"), headers.index("Status")
    assert len(rows) == ex["due"], (len(rows), ex["due"])
    assert rows[0][number] == ex["oldest"]["number"] and rows[0][status] == "Released", rows[0]
    db.emphasize_cells(d, mock["geometry"], [(0, 0), (0, len(headers) - 1)])
    _note(d, f"Outlined: the oldest past-due work order, {rows[0][number]}, which the table still calls {rows[0][status]}. "
             f"The grid is scrolled to the top and shows the first {shown.stop} of the {len(rows)} rows the pane reports; "
             f"the text not completed in the Completed column is the label that COALESCE gives a missing CompletedDate.",
          mock["bottom"])
    return d


# -- IF-09-6-A: the time clock entries with no clock-out ---------------------------------------------------------------------------

def if_09_6_a() -> Diagram:
    """Exercise 9.6, Step 5: COALESCE makes the missing clock-out visible, and every such entry is Pending."""
    g = ctx.values("ch09.g6")
    ex = ctx.values("ch09.ex6")
    d = Diagram("Time Clock Entries with No Clock-Out")
    mock = _mock(d, 6, "time clock entries with no ClockOutTime")
    rows, headers = mock["rows"], mock["headers"]
    out, status = headers.index("ClockOut"), headers.index("ClockStatus")
    regular, overtime = headers.index("RegularHours"), headers.index("OvertimeHours")
    employee = headers.index("EmployeeID")
    assert len(rows) == g["missing"] and all(r[out] == "missing" for r in rows), rows
    assert {r[employee] for r in rows} == {ex["clock_employee"]} and {r[status] for r in rows} == {"Pending"}, rows
    hours = [round(r[regular] + r[overtime], 2) for r in rows]
    assert [min(hours), max(hours)] == list(g["hours"]), (hours, g["hours"])
    db.emphasize_cells(d, mock["geometry"], [(0, out), (len(rows) - 1, out)])
    _note(d, f"Outlined: the word missing, which COALESCE shows where ClockOutTime is NULL. All {len(rows)} entries are "
             f"for employee {rows[0][employee]} and all are {rows[0][status]}, yet each records {min(hours):g} to "
             f"{max(hours):g} hours. Pending is a related test, not the same one: {g['pending']} entries are Pending "
             f"and {g['pending_out']} of them have a clock-out.", mock["bottom"])
    return d


# -- IF-09-0-A: from a wrong result to its cause ---------------------------------------------------------------------------------------

def _nb(reference: str) -> str:
    """A reference such as 'Tutorial 9.2, Step 6' with no line break inside 'Tutorial 9.2,' or 'Step 6', so that a
    narrow card breaks it only after the comma."""
    return ", ".join(part.replace(" ", "&nbsp;") for part in reference.split(", "))


def if_09_0_a() -> Diagram:
    """A decision path for logical errors: what the result shows, the usual cause, the check, and where it is practiced."""
    chapter, g3, g4 = ctx.values("ch09.chapter"), ctx.values("ch09.g3"), ctx.values("ch09.g4")
    t2, year = chapter["t2"], ctx.data().C
    d = Diagram("From a Wrong Result to Its Cause")
    n_leaf, gap = 6, 10
    leaf_w = (860 - gap * (n_leaf - 1)) / n_leaf
    xs = [i * (leaf_w + gap) for i in range(n_leaf)]
    leaves = [
        ("A comparison with NULL",
         f"ClosedDate = NULL returns {g4['eq_null']} rows where {g4['open_n']} work orders are open",
         "IS NULL", ("Tutorial 9.2, Step 6",)),
        ("Text in the wrong case",
         f"'In progress' returns {g4['lower']} rows",
         "DISTINCT shows the stored text", ("Exercise 9.4, Steps 3 and 4",)),
        ("A text year compared with a number",
         f"A year from SUBSTR = {year} keeps {g4['substr_num']} of {g4['open_n']}",
         "quotes or CAST", ("Tutorial 9.2, Step 8",)),
        ("AND and OR without parentheses",
         f"The chapter's example returns {t2['wrong']:,} rows, not the {t2['right']:,} intended",
         "parentheses, then the row count", ("Exercise 9.1, Step 6", "Exercise 9.6, Step 8")),
        ("A missing comma",
         "The second name becomes an alias",
         "the headings: an alias, not a column", ("Question 11", "Tutorial 9.3, Step 2")),
        ("A NULL in a calculation",
         f"Dividing by zero hours gives NULL: {g3['no_filter_null']} blank rates",
         "COALESCE labels the NULL", ("Exercise 9.3, Step 5", "Tutorial 9.2, Step 7")),
    ]
    texts = [f"<b>{title}</b><br>{evidence}<br><b>Check:</b> {check}<br><i>Practiced: {'; '.join(_nb(r) for r in where)}</i>"
             for title, evidence, check, where in leaves]
    leaf_h = max(kit.height_for(t, leaf_w - 10, SMALL, pad=16) for t in texts) + 10
    symptoms = [
        ("<b>The result has no rows</b><br>The pane reports 0 rows returned", 0, 3),
        ("<b>Far too many rows</b><br>More than the count you expect", 3, 1),
        ("<b>One column, not two</b><br>Two names were written", 4, 1),
        ("<b>Blank cells</b><br>Where numbers belong", 5, 1),
    ]
    spans = [(xs[a], (leaf_w + gap) * b - gap) for _, a, b in symptoms]
    sym_h = max(kit.height_for(t, w, SMALL, pad=14) for (t, _, _), (_, w) in zip(symptoms, spans))
    root_text = ("<b>The query ran without an error. Is it the right query?</b><br>Compare the result with what it "
                 "should be: the row count, the first rows, a control total. If it does not match, start from what "
                 "the result shows.")
    root_w = 600
    root_h = kit.height_for(root_text, root_w, SMALL, pad=14)
    blue, blue_stroke = kit.tint("blue")
    teal, teal_stroke = kit.tint("teal")
    root = d.box(root_text, (860 - root_w) / 2, 0, root_w, root_h, fill=blue, stroke=blue_stroke, size=SMALL,
                 stroke_width=1.5)
    sym_y = root_h + 38
    leaf_y = sym_y + sym_h + 34
    leaf_ids = []
    for i, text in enumerate(texts):
        leaf_ids.append(d.box(text, xs[i], leaf_y, leaf_w, leaf_h, fill=teal, stroke=teal_stroke, size=SMALL,
                              stroke_width=1.5, align="left", valign="top"))
    for (text, a, b), (x, w) in zip(symptoms, spans):
        sid = d.box(text, x, sym_y, w, sym_h, fill=blue, stroke=blue_stroke, size=SMALL, stroke_width=1.5)
        d.arrow(root, sid, exit=(0.5, 1), entry=(0.5, 0))
        for k in range(a, a + b):
            d.arrow(sid, leaf_ids[k], exit=(0.5, 1), entry=(0.5, 0))
    kit.callout(d, "Blue boxes are what the student sees; teal boxes are the usual cause, the check that confirms it "
                   "and where the chapter practices it. None of the six stops the query with an error: each runs and "
                   "returns a result, which is why the check is a comparison with what the result should be.",
                0, leaf_y + leaf_h + 16, 860, color="gray")
    return d


FIGURES = {
    "IF-09-0-A": if_09_0_a,
    "IF-09-0-B": if_09_0_b,
    "IF-09-1-A": if_09_1_a,
    "IF-09-2-A": if_09_2_a,
    "IF-09-4-A": if_09_4_a,
    "IF-09-6-A": if_09_6_a,
}
