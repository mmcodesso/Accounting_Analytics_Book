"""Instructor figures of Chapter 10 (guides in facts/instructor/guides/chapter-10-joining-and-summarizing/).

Nine figures are DB Browser for SQLite mocks of the Execute SQL tab and one is a chooser.  A mock quotes its query from
the model answer script (outputs/companion/solutions/Chapter10-exercises-sql/Ex 10.N.sql, the text the guide quotes), at
the editor line where it sits in that script, and runs it read-only, so the grid and the row count come from the data.
The values in the notes come from the grid or from the guide contexts (ch10.chapter, ch10.g1 to ch10.g6 and the
registered notes ch10.ex1 to ch10.ex6).  DB Browser keeps only the last statement's grid, so each mock runs one query.
"""

from __future__ import annotations

import re

import ctx
import dbbrowser as db
import excel as xl
import kit
from check_figures import text_width
from drawio import CORAL, GRAY, ROW_H, SMALL, WHITE, Diagram, esc

SOLUTIONS = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter10-exercises-sql"
GRID_W = 820            # the 860 px frame less the row-number column of the result grid
CELL_PAD = 20           # a cell wraps its text within about 12 px of its width, so leave room


# -- the model answers ------------------------------------------------------------------------------------------------

def _solution(n: int, wanted: str) -> tuple[str, str, int]:
    """The comment lines, the SQL and the editor line of the first comment line of the query of Ex 10.n.sql whose
    comment contains `wanted`.  The `-- Result: N rows` remark that the model answer appends to a query's last line is
    left out: a student types the query without it."""
    path = SOLUTIONS / f"Ex 10.{n}.sql"
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
        raise SystemExit(f"Ex 10.{n}.sql: {len(found)} queries have a comment containing {wanted!r} (expected one)")
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
        return _fit([round(w * scale) for w in natural], total)
    widths = list(natural)
    floor = [text_width(f"<b>{esc(h)}</b>", SMALL, True) + CELL_PAD + 2 for h in headers]
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


def _mock(d: Diagram, n: int, wanted: str, shown: slice | None = None, blank_rows: int = 0) -> dict:
    """The Execute SQL tab with the query of Ex 10.n.sql whose comment contains `wanted`, as a reader sees it after
    selecting the query and clicking Execute all/selected SQL.  The editor is scrolled to the query: it shows the
    comment lines and the query at their line numbers in the script.  `shown` draws only some rows of the result, as a
    grid scrolled to them (the rows keep their numbers); `blank_rows` leaves that many empty grid rows for a result
    with no rows.  Returns the grid and editor geometry."""
    comment, sql, line = _solution(n, wanted)
    headers, rows = db.run(sql)
    widths = _widths(headers, rows if not shown else rows[shown])
    y = db.window(d)
    editor_top = y
    text = f"{comment}\n{sql}"
    shown_lines = text.split("\n")
    n_comment = comment.count("\n") + 1
    y = db.editor(d, 0, y, 860, text, tab=f"Ex 10.{n}.sql", first_line=line,
                  selection=slice(n_comment, None)) + 8
    visible = rows[shown] if shown else rows
    clipped = [tuple(_clip(v, w) if isinstance(v, str) else v for v, w in zip(row, widths)) for row in visible]
    first = (shown.start or 0) + 1 if shown else 1
    geometry = db.results(d, 0, y, headers, widths, clipped, first=first)
    if blank_rows and not visible:
        d.box("", 0, y + ROW_H, 40 + sum(widths), blank_rows * ROW_H, fill=WHITE, stroke=db.RULE, rounded=False)
    y += (len(visible) + 1 + blank_rows) * ROW_H + 8
    message_top = y
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0], line=line + n_comment)
    return dict(headers=headers, rows=rows, geometry=geometry, bottom=bottom, sql_lines=shown_lines,
                n_comment=n_comment, editor_top=editor_top, message_top=message_top)


def _line_top(mock: dict, i: int) -> float:
    """The y of line i (from 0) of the text in the editor, below the editor's toolbar and tab."""
    return mock["editor_top"] + 32 + 24 + 4 + i * db.LINE_H


def _outline_lines(d: Diagram, mock: dict, first: int, last: int) -> None:
    """A coral outline around lines first..last of the editor, inset so that neighbors do not touch."""
    top = _line_top(mock, first)
    d.outline(db.GUTTER + 3, top + 1.5, 860 - db.GUTTER - 6, (last - first + 1) * db.LINE_H - 3, CORAL, width=2.5,
              front=True)


def _find(mock: dict, text: str) -> int:
    """The index of the one editor line that contains `text`."""
    hits = [i for i, line in enumerate(mock["sql_lines"]) if text in line]
    assert len(hits) == 1, (text, hits)
    return hits[0]


def _column(d: Diagram, mock: dict, name: str) -> None:
    """Outline a result column, heading and every drawn value, as a screenshot's red box would."""
    c = mock["headers"].index(name)
    rows = [r for (r, col) in mock["geometry"] if col == c and r >= 0]
    db.emphasize_cells(d, mock["geometry"], [(-1, c), (max(rows), c)])


def _note(d: Diagram, text: str, y: float) -> None:
    height = kit.lines_for(text, 860, SMALL) * 15 + 12
    d.text(f"<i>{text}</i>", 0, y + 8, 860, height, size=SMALL, color=GRAY)


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _ordinal(n: int) -> str:
    """21 as 21st, 8 as 8th."""
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _date(value: str) -> str:
    """A date that must not break at its hyphens in a note."""
    return f'<span style="white-space:nowrap">{esc(value)}</span>'


def _word(n: int) -> str:
    """A small count as a word, as the guides write it."""
    return {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}.get(n, str(n))


# -- IF-10-0-B: the fan-out demonstration -------------------------------------------------------------------------------

def if_10_0_b() -> Diagram:
    """The fan-out demonstration: one total over a join and from the header alone (Chapter 10 note)."""
    year = ctx.data().C
    sql = (f"SELECT ROUND(SUM(si.GrandTotal), 2) AS JoinedTotal,\n"
           f"    (SELECT ROUND(SUM(GrandTotal), 2) FROM SalesInvoice\n"
           f"     WHERE InvoiceDate BETWEEN '{year}-01-01' AND '{year}-12-31') AS HeaderTotal\n"
           f"FROM SalesInvoice si\n"
           f"JOIN SalesInvoiceLine sil ON sil.SalesInvoiceID = si.SalesInvoiceID\n"
           f"WHERE si.InvoiceDate BETWEEN '{year}-01-01' AND '{year}-12-31';")
    d = Diagram("The Fan-Out Demonstration")
    shot = db.execute_sql(d, "-- Fan-out: the same total over a join and from the header alone\n" + sql, [200, 200], tab="SQL 1")
    joined, header = shot["rows"][0]
    chapter = ctx.values("ch10.chapter")
    assert (joined, header) == (chapter["fan_total"], chapter["true_total"]), "the grid differs from the guide's totals"
    db.emphasize_cells(d, shot["geometry"], [(-1, 0), (0, 0)])
    d.text(f"<i>Outlined: the total summed over the join, {joined / header:.2f} times the header total, because each "
           f"invoice's GrandTotal repeats on every one of its lines. The pane shows one result: DB Browser keeps only the "
           f"last statement's grid, so the two totals are returned by one query.</i>", 0, shot["bottom"] + 8, 860, 56,
           size=SMALL, color=GRAY)
    return d


# -- IF-10-1-A: the two totals side by side ---------------------------------------------------------------------------------

def if_10_1_a() -> Diagram:
    """Exercise 10.1, Step 7: the ledger and the invoice lines in one row, and the difference."""
    ex = ctx.values("ch10.ex1")
    d = Diagram("The Ledger and the Invoice Lines, Side by Side")
    mock = _mock(d, 1, "the ledger against the invoice lines, side by side")
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["Ledger", "InvoiceLines", "Difference"] and len(rows) == 1, (headers, rows)
    ledger, lines, diff = rows[0]
    assert [round(v, 2) for v in (ledger, lines, diff)] == [ex["ledger_total"], ex["lines_total"], ex["diff"]], rows
    by_posting = _find(mock, "gl.FiscalYear")
    by_invoice = _find(mock, "si.InvoiceDate BETWEEN")
    _outline_lines(d, mock, by_posting, by_posting)
    _outline_lines(d, mock, by_invoice, by_invoice)
    db.emphasize_cells(d, mock["geometry"], [(-1, 2), (0, 2)])
    _note(d, f"Outlined: the difference, {_money(diff)}, and the two lines that select the year. The ledger is selected "
             f"by FiscalYear, which follows the posting date, and the invoice lines by InvoiceDate. Two selections by "
             f"different dates can disagree without either being wrong; the next figure lists the invoices that fall "
             f"on one side only.", mock["bottom"])
    return d


# -- IF-10-1-B: the invoices that explain the difference -------------------------------------------------------------------------

def if_10_1_b() -> Diagram:
    """Exercise 10.1, Step 8: the revenue postings of the year whose invoices are dated before it."""
    ex = ctx.values("ch10.ex1")
    d = Diagram("The Invoices Behind the Difference")
    mock = _mock(d, 1, "fiscal 2026 revenue postings of invoices dated before")
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["InvoiceNumber", "InvoiceDate", "PostingDate", "AccountNumber", "Revenue"], headers
    cutoff = ex["cutoff"]
    assert [r[0] for r in rows] == [c["number"] for c in cutoff], rows
    assert [r[1] for r in rows] == [c["date"] for c in cutoff], rows
    assert {r[2] for r in rows} == {ex["posted"]}, rows
    total = round(sum(r[4] for r in rows), 2)
    assert total == ex["diff"], (total, ex["diff"])
    _column(d, mock, "InvoiceDate")
    dates = sorted(r[1] for r in rows)
    _note(d, f"Outlined: InvoiceDate. All {_word(len(rows))} invoices are dated before the year, {_date(dates[0])} to {_date(dates[-1])}, and "
             f"all post on {_date(rows[0][2])}, so the ledger counts their {_money(total)} in the year and the invoice lines, "
             f"selected by InvoiceDate, count it in the year before. The three amounts add up to the difference of the "
             f"previous figure; Exercises&nbsp;5.2 and 6.1 decide, from the shipments, which side is right.", mock["bottom"])
    return d


# -- IF-10-2-A: the four ledger rows of the traced sale -----------------------------------------------------------------------------

def if_10_2_a() -> Diagram:
    """Exercise 10.2, Step 1: the rows SI-2025-007947 posted, joined to the invoice and the accounts."""
    ex = ctx.values("ch10.ex2")
    d = Diagram("The Ledger Rows of the Traced Sale")
    mock = _mock(d, 2, "the ledger rows posted by")
    headers, rows = mock["headers"], mock["rows"]
    assert len(rows) == 4 and [r[0] for r in rows] == [r["id"] for r in ex["rows"]], rows
    line = headers.index("SourceLineID")
    filled = [r for r, row in enumerate(rows) if row[line] is not None]
    assert len(filled) == 1 and rows[filled[0]][line] == ex["line"]["id"], rows
    account = headers.index("AccountNumber")
    assert rows[filled[0]][account] == next(r["number"] for r in ex["rows"] if r["line"]), rows
    debit, credit = headers.index("Debit"), headers.index("Credit")
    debits, credits = round(sum(r[debit] for r in rows), 2), round(sum(r[credit] for r in rows), 2)
    assert debits == credits == ex["debits"], (debits, credits)
    db.emphasize_cells(d, mock["geometry"], [(filled[0], line)])
    others = [r[account] for r in rows if r[line] is None]
    _note(d, f"Outlined: the SourceLineID of the revenue posting, {rows[filled[0]][line]}, the line of the invoice that "
             f"posted {rows[filled[0]][account]}. The other {_word(len(others))} rows ({', '.join(str(a) for a in others)}) are NULL, "
             f"because the receivable, the freight and the tax belong to the invoice header, not to a line. The "
             f"{_word(len(rows))} rows balance: debits and credits are each {_money(debits)}, the invoice's GrandTotal.",
          mock["bottom"])
    return d


# -- IF-10-2-B: an anti-join that returns no rows ------------------------------------------------------------------------------------

def if_10_2_b() -> Diagram:
    """Exercise 10.2, Step 7: the anti-join of the year's postings to their lines returns nothing."""
    ex = ctx.values("ch10.ex2")
    d = Diagram("An Anti-Join That Returns No Rows")
    mock = _mock(d, 2, "anti-join, postings whose SourceLineID matches no invoice line", blank_rows=2)
    assert mock["rows"] == [], mock["rows"]
    heads = [box for (r, c), box in mock["geometry"].items() if r == -1]
    right = max(x + w for x, y, w, h in heads)
    xl.emphasis(d, 0, heads[0][1], right, ROW_H * 3)
    _note(d, f"Outlined: the empty grid, the column headings with no rows, and the pane below it reports 0 rows returned. "
             f"The test covers the {ex['tested']:,} postings of the year that carry a SourceLineID (Step 6): every one "
             f"points to an existing invoice line. An empty result is a result, and it runs in one direction only: it "
             f"does not show that every invoice line was posted, that the amounts agree or that the documents are "
             f"genuine.", mock["bottom"])
    return d


# -- IF-10-3-A: the grouping by name ------------------------------------------------------------------------------------------------

def if_10_3_a() -> Diagram:
    """Exercise 10.3, Step 3: grouped by CustomerName, the two Brown LLCs merge into one row."""
    ex, g = ctx.values("ch10.ex3"), ctx.values("ch10.g3")
    merged = ex["merged"]
    comment, sql, _ = _solution(3, "grouped by CustomerName")
    names = [row[0] for row in db.run(sql)[1]]
    at = names.index(merged["name"])
    assert at + 1 == g["name_rank"] and len(names) == g["n_by_name"], (at, len(names))
    shown = slice(at - 3, at + 4)
    d = Diagram("Grouping by Name Merges Two Customers")
    mock = _mock(d, 3, "grouped by CustomerName", shown=shown)
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["CustomerName", "Orders", "TotalOrdered", "AverageOrder"], headers
    row = rows[at]
    assert row[1] == merged["n"] and round(row[3], 2) == round(merged["avg"], 2), row
    assert sum(c["n"] for c in merged["customers"]) == merged["n"]
    db.emphasize_cells(d, mock["geometry"], [(3, 0), (3, len(headers) - 1)])
    first, second = merged["customers"]
    _note(d, f"Outlined: the {merged['name']} row, {row[1]} orders averaging {row[3]:,.2f}, one row for two customers: "
             f"customer {first['id']} ({first['segment']}, {first['n']} orders, {first['avg']:,.2f}) and customer "
             f"{second['id']} ({second['segment']}, {second['n']} orders, {second['avg']:,.2f}). The pane reports "
             f"{len(rows)} rows, one fewer than the {ex['customers']} of the grouping by CustomerID, and the grid is "
             f"scrolled to rows {shown.start + 1} to {shown.stop}, where the merged row ranks {_ordinal(g['name_rank'])}; by key "
             f"the two customers rank {_ordinal(g['id_ranks'][0])} and {_ordinal(g['id_ranks'][1])}.", mock["bottom"])
    return d


# -- IF-10-4-A: the variance by year ----------------------------------------------------------------------------------------------------

def if_10_4_a() -> Diagram:
    """Exercise 10.4, Step 6: the amount invoiced against orders and the variance by year."""
    ex = ctx.values("ch10.ex4")
    d = Diagram("The Purchase Price Variance by Year")
    mock = _mock(d, 4, "amount invoiced against orders and variance by year")
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["InvoiceYear", "InvoiceLines", "AmountInvoiced", "LineTotals", "PriceVariance",
                       "VariancePct"], headers
    years = ex["years"]
    assert [int(r[0]) for r in rows] == [y["year"] for y in years], rows
    for row, y in zip(rows, years):
        assert abs(row[2] - y["amount"]) < 0.01 and abs(row[4] - y["variance"]) < 0.01, (row, y)
        assert abs(row[5] - round(100 * y["rate"], 2)) < 1e-9, (row, y)
    rates = [r[5] for r in rows]
    amounts = [r[2] for r in rows]
    assert amounts == sorted(amounts) and 0.4 <= min(rates) and max(rates) <= 0.6, (amounts, rates)
    _column(d, mock, "VariancePct")
    growth = amounts[-1] / amounts[0] - 1
    _note(d, f"Outlined: VariancePct, {rates[0]:.2f}%, {rates[1]:.2f}% and {rates[2]:.2f}%, a near-steady share of what "
             f"is invoiced against orders while that amount grows {growth:.0%} from {rows[0][0]} to {rows[-1][0]}. The "
             f"variance grows with the amount invoiced. AmountInvoiced mixes quantity, order prices and mix, so the "
             f"comparison cannot say how much of the growth is more buying. LineTotals differs from the amount by the "
             f"rounding of each line.", mock["bottom"])
    return d


# -- IF-10-5-A: ledger rows that point to no payroll payment ------------------------------------------------------------------------------

def if_10_5_a() -> Diagram:
    """Exercise 10.5, Step 2: the six ledger rows whose payroll payment does not exist."""
    ex, g = ctx.values("ch10.ex5"), ctx.values("ch10.g5")
    d = Diagram("Ledger Rows That Point to No Payroll Payment")
    mock = _mock(d, 5, "ledger rows that point to no payroll payment")
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["GLEntryID", "PostingDate", "SourceDocumentID", "Debit", "Credit", "Description"], headers
    assert len(rows) == g["anti"] == 2 * len(ex["pairs"]), (len(rows), g["anti"])
    assert [r[0] for r in rows] == sorted(i for p in ex["pairs"] for i in p["ids"]), rows
    debit, credit = headers.index("Debit"), headers.index("Credit")
    for k in range(0, len(rows), 2):
        assert rows[k][debit] == rows[k + 1][credit] == ex["amount"], rows[k:k + 2]
    _column(d, mock, "SourceDocumentID")
    docs = [rows[k][2] for k in range(0, len(rows), 2)]
    _note(d, f"Outlined: SourceDocumentID. The {_word(len(rows))} rows are {_word(len(rows) // 2)} pairs of {_money(ex['amount'])}, a "
             f"debit \"{rows[0][5]}\" and a credit \"{rows[1][5]}\", posted on {_date(rows[0][1])}, {_date(rows[2][1])} and "
             f"{_date(rows[4][1])}. They name payroll payments {docs[0]}, {docs[1]} and {docs[2]}, which are not in "
             f"PayrollPayment. This is an integrity failure: the database declares no foreign keys, so nothing stopped "
             f"these rows from naming a payment that is not there.", mock["bottom"])
    return d


# -- IF-10-6-A: the fan-out of invoices joined to payments ---------------------------------------------------------------------------------

def if_10_6_a() -> Diagram:
    """Exercise 10.6, Step 4: a supplier's invoices joined to its payments on the supplier alone."""
    ex, g = ctx.values("ch10.ex6"), ctx.values("ch10.g6")
    d = Diagram("The Fan-Out of Invoices Joined to Payments")
    mock = _mock(d, 6, "the fan-out of joining invoices to payments")
    headers, rows = mock["headers"], mock["rows"]
    assert headers == ["JoinedRows"] and len(rows) == 1, (headers, rows)
    joined = rows[0][0]
    assert joined == ex["fan"] == g["one_n"] == g["inv_n"] * g["pay_n"], (joined, g["inv_n"], g["pay_n"])
    db.emphasize_cells(d, mock["geometry"], [(-1, 0), (0, 0)])
    _note(d, f"Outlined: {joined:,} rows, which is {g['inv_n']:,} invoices times {g['pay_n']:,} payments of supplier "
             f"{ex['first']}: the two tables share only SupplierID, so every invoice meets every payment. Summing "
             f"GrandTotal over this join gives {_money(g['one_total'])} where the invoices total {_money(g['inv_total'])}. "
             f"Total each table on its own, then join the totals.", mock["bottom"])
    return d


# -- IF-10-0-A: choosing the join or the summary ---------------------------------------------------------------------------------------------

def _nb(reference: str) -> str:
    """A reference such as 'Tutorial 10.1, Step 6' with no line break inside 'Tutorial 10.1,' or 'Step 6'."""
    return ", ".join(part.replace(" ", "&nbsp;") for part in reference.split(", "))


def if_10_0_a() -> Diagram:
    """A chooser: what the question asks of two or more tables, the join or summary that fits, its row-count test and
    where the chapter practices it, and the fan-out warning for any total over a join."""
    ch = ctx.values("ch10.chapter")
    t1, ex1, ex2, g3 = ch["t1"], ctx.values("ch10.ex1"), ctx.values("ch10.ex2"), ctx.values("ch10.g3")
    ex3, ex6, g5, g6 = ctx.values("ch10.ex3"), ctx.values("ch10.ex6"), ctx.values("ch10.g5"), ctx.values("ch10.g6")
    d = Diagram("Choosing the Join or the Summary")
    rows = [
        ("Only the rows that match in both tables", "Each close with its work order and item",
         "INNER JOIN on the logical key",
         "For the ledger, name SourceDocumentType and SourceDocumentID in ON.",
         f"the join returns as many rows as the child table: {t1['n_close']:,} closes after each join, "
         f"{ex1['rows']:,} invoice lines in Exercise 10.1.",
         ("Tutorial 10.1, Steps 1 and 2", "Exercises 10.1 (1) and 10.2 (1)")),
        ("Every row of the first table, matched or not", "Every manufactured item, with its closes if it has any",
         "LEFT JOIN",
         "A condition on the second table goes in ON; in WHERE it turns the join back into an inner join.",
         f"the rows equal the first table's: {t1['step6_on']} items with the date in ON, {t1['step6_where']} with it "
         f"in WHERE.",
         ("Tutorial 10.1, Step 6",)),
        ("Only the rows of the first table that match nothing", "Ledger rows with no payroll payment",
         "Anti-join: LEFT JOIN, then IS NULL on the second table's key",
         f"Or NOT EXISTS. NOT IN returns {ch['not_in']} of {ch['n_employees']} employees where NOT EXISTS finds "
         f"{ch['not_exists']}, because the list holds a NULL.",
         f"report the rows tested and the exceptions: {ex2['tested']:,} postings and none in Exercise 10.2, "
         f"{_word(g5['anti'])} in Exercise 10.5.",
         ("Tutorial 10.3, Step 7", "Exercises 10.2 (3) and 10.5 (2) to (5)")),
        ("One row per group: a total, a count or an average", "The variance by item group and year",
         "GROUP BY the key, and HAVING for a condition on the total",
         "Group by the key, not the name.",
         f"grouped by the key there are {ex3['customers']} customers, grouped by the name {g3['n_by_name']}; and the "
         f"groups add up to the control total, ${t1['ledger']:,.2f} of variance by item group, the ledger's.",
         ("Tutorial 10.1, Steps 3 to 5", "Exercises 10.1 (2) and 10.3")),
    ]
    root_w, q_w, gap, row_gap = 150, 220, 30, 10
    leaf_w = 860 - root_w - q_w - 2 * gap
    leaf_x, q_x = root_w + gap + q_w + gap, root_w + gap
    questions = [f"<b>{q}</b><br>{example}" for q, example, *_ in rows]
    leaves = [f"<b>{title}</b><br>{how}<br><b>Row-count test:</b> {test}<br><i>Practiced: "
              f"{'; '.join(_nb(r) for r in where)}</i>" for _, _, title, how, test, where in rows]
    heights = [max(kit.height_for(q, q_w, SMALL, pad=14), kit.height_for(lf, leaf_w, SMALL, pad=14))
               for q, lf in zip(questions, leaves)]
    blue, blue_stroke = kit.tint("blue")
    teal, teal_stroke = kit.tint("teal")
    total = sum(heights) + row_gap * (len(rows) - 1)
    root = d.box("<b>A question about two or more tables</b><br>What should the result hold?", 0, 0, root_w, total,
                 fill=blue, stroke=blue_stroke, size=SMALL, stroke_width=1.5)
    y = 0.0
    for q, leaf, h in zip(questions, leaves, heights):
        qid = d.box(q, q_x, y, q_w, h, fill=blue, stroke=blue_stroke, size=SMALL, stroke_width=1.5)
        lid = d.box(leaf, leaf_x, y, leaf_w, h, fill=teal, stroke=teal_stroke, size=SMALL, stroke_width=1.5,
                    align="left")
        d.arrow(root, qid, exit=(1, (y + h / 2) / total), entry=(0, 0.5), meta="edgeStyle=none;")
        d.arrow(qid, lid, exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
        y += h + row_gap
    warning = (f"<b>Before any total over a join, ask at what level each amount is recorded.</b> A header amount repeats on "
               f"every line it is joined to: the year's GrandTotal sums to {_money(ch['fan_total'])} over the join of "
               f"invoices to lines, against {_money(ch['true_total'])} from SalesInvoice alone, and supplier "
               f"{ex6['first']}'s invoices joined to its payments return {g6['one_n']:,} rows. Sum the line's "
               f"own column, or total each table in a derived table before joining. <i>Practiced: "
               f"{_nb('Tutorial 10.3, Step 6')}; {_nb('Exercise 10.6 (2)')}.</i>")
    bottom = kit.callout(d, warning, 0, total + 16, 860, color="amber")
    d.text("<i>Blue boxes ask the question; teal boxes give the join or summary that fits, the row-count test that "
           "checks it and where the chapter practices it.</i>", 0, bottom + 6, 860, 20, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "IF-10-0-A": if_10_0_a,
    "IF-10-0-B": if_10_0_b,
    "IF-10-1-A": if_10_1_a,
    "IF-10-1-B": if_10_1_b,
    "IF-10-2-A": if_10_2_a,
    "IF-10-2-B": if_10_2_b,
    "IF-10-3-A": if_10_3_a,
    "IF-10-4-A": if_10_4_a,
    "IF-10-5-A": if_10_5_a,
    "IF-10-6-A": if_10_6_a,
}
