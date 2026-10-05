"""Chapter 9 figures."""

from __future__ import annotations

import sqlite3
from functools import lru_cache

import dbbrowser as db
import excel as xl
from data import connection, one, q
from drawio import (BLUE, BLUE_TINT, GRAY, GRAY_TINT, INK, ROW_H, RULE, SMALL, Diagram, esc)
from shared.calculations.sql_ch09 import (
    HEADER, QUERIES
)

VARIANCE_ACCOUNT = 5080
CLEARING_ACCOUNT = 1090
SCRIPT_TAB = "Chapter09.sql"

# The chapter's script, Chapter09.sql, as the three tutorials build it: a header comment, then
# each query at the end of the script under a one-line comment. The tutorial mocks show each
# query at the line where it sits in this script, and fig-09-10 shows the top of the script.


CHAPTER09 = db.Script(HEADER, QUERIES, SCRIPT_TAB)


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


@lru_cache(maxsize=1)
def account_ids() -> dict[int, int]:
    rows = dict((n, i) for i, n in q("SELECT AccountID, AccountNumber FROM Account "
                                     "WHERE AccountNumber IN (?, ?)", CLEARING_ACCOUNT,
                                     VARIANCE_ACCOUNT))
    assert rows == {1090: 92, 5080: 93}, rows   # the text names both AccountIDs
    return rows


# -- figures ----------------------------------------------------------------------------

def fig_09_01() -> Diagram:
    d = Diagram("Importing Data Compared with Querying It")
    tables = one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' "
                 "AND name NOT LIKE 'sqlite_%'")[0]
    assert tables > 50
    w, xs = 170, (0, 345, 690)
    # Upper path: Part II's Power Query imports into a workbook.
    d.text("<b>Importing tables into a workbook (Part II)</b>", 0, 0, 860, 22, size=14, color=INK)
    src1 = d.box("<b>CharlesRiver.xlsx</b><br>every table, every row", xs[0], 34, w, 70,
                 fill=GRAY_TINT, stroke=GRAY)
    wb = d.box("<b>Analysis workbook</b><br>the chosen tables copied in", xs[1], 34, w, 70,
               fill=GRAY_TINT, stroke=GRAY)
    out1 = d.box("<b>Result</b><br>merged and summarized from the copies", xs[2], 34, w, 70,
                 fill=GRAY_TINT, stroke=GRAY)
    d.arrow(src1, wb, label="Power Query")
    d.arrow(wb, out1, label="merge, then analyze")
    d.text("The steps are recorded and can be refreshed, but every table is copied into the "
           "workbook, and each question across tables needs a merge first.",
           0, 112, 860, 40, size=SMALL, color=INK)
    # Lower path: a saved query.
    d.text("<b>Querying the database (Part III)</b>", 0, 170, 860, 22, size=14, color=INK)
    sql = d.box("<b>Saved SQL query</b><br>SELECT … FROM … WHERE …", xs[0], 204, w, 70,
                fill=BLUE_TINT, stroke=BLUE)
    src2 = d.box("<b>CharlesRiver.sqlite</b><br>the query runs where the data is", xs[1], 204,
                 w, 70, fill=BLUE_TINT, stroke=BLUE)
    out2 = d.box("<b>Result</b><br>only the rows and columns asked for", xs[2], 204, w, 70,
                 fill=BLUE_TINT, stroke=BLUE)
    d.arrow(sql, src2, label="sent to")
    d.arrow(src2, out2, label="returns")
    d.text("Nothing is copied until the query asks for it. The query text documents the "
           "extraction and runs again when the data changes.", 0, 282, 860, 40, size=SMALL,
           color=INK)
    return d


def fig_09_02() -> Diagram:
    d = Diagram("The Database Structure Tab of DB Browser for SQLite")
    columns = q("PRAGMA table_info(GLEntry)")
    names = [r[0] for r in q("SELECT name FROM sqlite_master WHERE type = 'table' "
                             "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    counts = dict(q("SELECT type, COUNT(*) FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' "
                    "GROUP BY type"))
    i = names.index("GLEntry")
    y = db.window(d, active="Database Structure")
    widths = [300, 120, 440]
    db.structure_row(d, 0, y, widths, ["Name", "Type", "Schema"], bold=True, fill=GRAY_TINT)
    y += ROW_H
    db.structure_row(d, 0, y, widths, [f"▾ Tables ({len(names)})", "", ""], bold=True)
    y += ROW_H
    for name in names[:3]:
        db.structure_row(d, 0, y, widths, [f"▸ {name}", "", f'CREATE TABLE "{name}" (…)'],
                         indent=1)
        y += ROW_H
    db.structure_row(d, 0, y, widths, ["…", "", ""], indent=1)
    y += ROW_H
    db.structure_row(d, 0, y, widths, [f"▸ {names[i - 1]}", "", f'CREATE TABLE "{names[i - 1]}" (…)'],
                     indent=1)
    y += ROW_H
    top = y
    db.structure_row(d, 0, y, widths, ["▾ GLEntry", "", 'CREATE TABLE "GLEntry" (…)'],
                     indent=1, bold=True, fill=BLUE_TINT)
    y += ROW_H
    for _, name, kind, notnull, _, pk in columns:
        schema = f'"{name}" {kind}' + (" NOT NULL" if notnull else "")
        db.structure_row(d, 0, y, widths, [name, kind, schema], indent=2)
        y += ROW_H
    xl.emphasis(d, 0, top, 420, y - top)
    for name in names[i + 1:i + 3]:
        db.structure_row(d, 0, y, widths, [f"▸ {name}", "", f'CREATE TABLE "{name}" (…)'],
                         indent=1)
        y += ROW_H
    db.structure_row(d, 0, y, widths, ["…", "", ""], indent=1)
    y += ROW_H
    for label, kind in [("Indices", "index"), ("Views", "view"), ("Triggers", "trigger")]:
        db.structure_row(d, 0, y, widths, [f"▸ {label} ({counts.get(kind, 0)})", "", ""],
                         bold=True)
        y += ROW_H
    types = {kind for _, _, kind, *_ in columns}
    assert types == {"INTEGER", "REAL", "TEXT"}, types
    assert counts.get("view", 0) == 0 and counts.get("trigger", 0) == 0, counts
    note(d, "Outlined: the GLEntry table expanded to show its columns and their declared types. "
            "The list of tables is shortened.", y + 10, 22)
    return d


def fig_09_03() -> Diagram:
    d = Diagram("Choosing Columns from the Account Table")
    ids = account_ids()
    _, sql, _ = CHAPTER09.location("account_columns")
    rows = db.run(sql)[1]
    start = [r[0] for r in rows].index(ids[1090]) - 4
    out = CHAPTER09.mock(d, "account_columns", [90, 120, 290, 110, 210],
                         shown=slice(start, start + 9), selection=slice(1, None))
    marked = [r for r, row in enumerate(out["rows"][start:start + 9]) if row[0] in ids.values()]
    db.emphasize_cells(d, out["geometry"], [(marked[0], 0), (marked[-1], 4)])
    # Numbered labels for the parts of the Execute SQL tab, placed in empty space beside each part:
    # the editor toolbar sits at editor_top, and the row below it holds only the editor tab.
    top, tab_row = out["editor_top"], out["editor_top"] + 32
    badges = [(116, tab_row + 2), (184, tab_row + 2), (352, tab_row + 2),
              (830, tab_row + 24 + 4 + db.LINE_H), (830, out["grid_top"] + 2), (830, out["message_top"] + 6)]
    assert top > 0
    for k, (x, y) in enumerate(badges, 1):
        d.marker(str(k), x, y, size=20)
    y = out["bottom"] + 8
    note(d, "Outlined: accounts 1090 and 5080, whose AccountIDs differ from their account numbers. "
            "The grid is scrolled to the manufacturing accounts.", y, 22)
    legend = ["the editor tab, named after the saved script",
              "Open SQL file(s) and Save SQL file, icons on the real toolbar",
              "Execute all/selected SQL (Ctrl+Return): runs the selected lines",
              "the query, selected before it is run",
              "the result grid",
              "the message pane: errors, rows returned, and the starting line"]
    y += 30
    for k, text in enumerate(legend):
        col, row = divmod(k, 3)
        x, ly = col * 430, y + row * 26
        d.marker(str(k + 1), x, ly, size=20)
        d.text(text, x + 26, ly - 1, 400, 22, size=SMALL, valign="middle")
    return d


def fig_09_04() -> Diagram:
    d = Diagram("A Syntax Error in the Message Pane")
    comment, sql, line = CHAPTER09.location("account_columns")
    wrong = sql.replace("AccountNumber", "AccountNumbr", 1)
    assert wrong != sql
    try:
        connection().execute(wrong)
        raise AssertionError("the misspelled query should fail")
    except sqlite3.OperationalError as exc:
        error = str(exc)
    assert error == "no such column: AccountNumbr", error
    y = db.window(d)
    y = db.editor(d, 0, y, 860, f"{comment}\n{wrong}", tab=SCRIPT_TAB, first_line=line) + 8
    bottom = db.message(d, 0, y, 860, 0, wrong.split("\n")[0], line=line + 1, error=error)
    note(d, "The message pane turns red and names the column it cannot find, at the line where "
            "the statement starts. The result grid between the editor and the pane is not shown.",
         bottom + 8, 40)
    return d


def fig_09_05() -> Diagram:
    d = Diagram("A Calculated Check on the Variance Records")
    _, sql, _ = CHAPTER09.location("variance_check")
    rows = db.run(sql)[1]
    assert all(r[5] == 0 for r in rows), "every close's parts add up to its total"
    out = CHAPTER09.mock(d, "variance_check", [150, 110, 110, 120, 110, 180], shown=slice(0, 8))
    db.emphasize_cells(d, out["geometry"], [(-1, 5), (7, 5)])
    note(d, "Outlined: the calculated CheckDifference column, zero in every row shown. "
            "The first eight of the result's rows are shown.", out["bottom"] + 8, 40)
    return d


def fig_09_06() -> Diagram:
    d = Diagram("How WHERE Treats a Missing Value")
    picks = []
    for status, n in [("Closed", 2), ("Completed", 2), ("Released", 2)]:
        picks += q("SELECT WorkOrderID, WorkOrderNumber, Status, ClosedDate FROM WorkOrder "
                   "WHERE ReleasedDate BETWEEN '2026-11-01' AND '2026-11-30' AND Status = ? "
                   "ORDER BY WorkOrderID LIMIT ?", status, n)
    picks.sort()
    assert len(picks) == 6
    assert all((r[3] is None) == (r[2] != "Closed") for r in picks), picks
    # Each test as SQLite evaluates it: = NULL is NULL for every row, IS NULL is 1 or 0.
    tests = q("SELECT WorkOrderID, ClosedDate = NULL, ClosedDate IS NULL, "
              "COALESCE(ClosedDate, 'open') FROM WorkOrder WHERE WorkOrderID IN "
              f"({', '.join(str(r[0]) for r in picks)}) ORDER BY WorkOrderID")
    assert all(t[1] is None for t in tests)
    rows = []
    for (_, number, status, closed), (_, _, isnull, coalesced) in zip(picks, tests):
        rows.append((number, status, closed or "NULL",
                     "NULL: not kept",
                     "true: kept" if isnull else "false: not kept",
                     coalesced))
    headers = ["WorkOrderNumber", "Status", "ClosedDate", "ClosedDate = NULL",
               "ClosedDate IS NULL", "COALESCE(ClosedDate, 'open')"]
    widths = [140, 100, 100, 150, 150, 220]
    d.text("<b>Six work orders released in November 2026, and three expressions evaluated for "
           "each</b>", 0, 0, 860, 20, size=SMALL)
    d.grid(0, 24, headers, widths, rows)
    y = 24 + ROW_H * (len(rows) + 1) + 12
    note(d, "A comparison with NULL is never true, so = NULL keeps no row, closed or open. IS NULL "
            "is true for the work orders with no ClosedDate, and COALESCE shows a stand-in value "
            "where the date is missing.", y, 40)
    return d


def fig_09_07() -> Diagram:
    d = Diagram("The Source Document Types Behind the Variance Account")
    account_ids()
    _, sql, _ = CHAPTER09.location("source_types")
    rows = db.run(sql)[1]
    assert {r[0] for r in rows} == {"WorkOrderClose", "JournalEntry"}, rows
    out = CHAPTER09.mock(d, "source_types", [260])
    journal = [r for r, row in enumerate(out["rows"]) if row[0] == "JournalEntry"][0]
    db.emphasize_cells(d, out["geometry"], [(journal, 0)])
    note(d, "Outlined: the JournalEntry row, which Step 4 examines.", out["bottom"] + 8, 22)
    return d


def fig_09_08() -> Diagram:
    d = Diagram("The Anatomy of a SQL Query")
    parts = [
        (["-- The ten largest variances of fiscal 2026"],
         "A comment says what the query answers. It is ignored when the query runs."),
        (["SELECT WorkOrderCloseID, CloseDate,",
          "    ROUND(OverheadVarianceAmount / TotalVarianceAmount, 2)",
          "        AS OverheadShare"],
         "The columns to return, including a calculated column with an alias."),
        (["FROM WorkOrderClose"], "The table the rows come from."),
        (["WHERE CloseDate BETWEEN '2026-01-01' AND '2026-12-31'"],
         "The condition a row must meet to be kept: the closes of fiscal 2026."),
        (["ORDER BY TotalVarianceAmount DESC"], "The sort: the largest variance first."),
        (["LIMIT 10;"], "How many rows to keep, and the semicolon that ends the statement."),
    ]
    sql = " ".join(line for lines, _ in parts[1:] for line in lines)
    assert len(q(sql.rstrip(";"))) == 10
    y = 0
    for i, (lines, label) in enumerate(parts):
        h = max(20 * len(lines) + 12, 44)
        code = "<br>".join(db.highlight(line)[0] for line in lines)
        d.box(code, 0, y, 520, h, fill=GRAY_TINT if i == 0 else "#FFFFFF", stroke=RULE,
              size=SMALL, align="left", valign="middle", rounded=False)
        d.box(esc(label), 540, y, 320, h, fill=BLUE_TINT, stroke=BLUE_TINT, size=SMALL,
              align="left", valign="middle", rounded=False)
        y += h + 6
    note(d, "The clauses must be written in this order. Only SELECT is always required; the others "
            "appear when a query uses them.", y + 4, 22)
    return d


def fig_09_09() -> Diagram:
    d = Diagram("The Ten Largest Work-Order Variances of Fiscal 2026")
    _, saved, _ = CHAPTER09.location("top_ten")
    # Step 1 of Tutorial 9.3 runs the query before Step 2 adds the OverheadShare column.
    step1 = saved.replace("    TotalVarianceAmount AS Total,\n"
                          "    ROUND(OverheadVarianceAmount / TotalVarianceAmount, 2)\n"
                          "        AS OverheadShare\n", "    TotalVarianceAmount AS Total\n")
    assert step1 != saved
    rows = db.run(step1)[1]
    assert len(rows) == 10 and all(r[5] > r[3] + r[4] for r in rows), \
        "overhead is larger than material and labor together in each of the ten"
    shares = [r[6] for r in db.run(saved)[1]]
    assert sum(s > 0.8 for s in shares) >= 6, shares     # "most of them more than four-fifths"
    out = CHAPTER09.mock(d, "top_ten", [150, 110, 110, 100, 100, 110, 100], sql=step1)
    db.emphasize_cells(d, out["geometry"], [(-1, 5), (9, 5)])
    note(d, "Outlined: the Overhead column, which holds most of each total.", out["bottom"] + 8, 22)
    return d


def fig_09_10() -> Diagram:
    d = Diagram("The Chapter's Script After Tutorial 9.3")
    close = one("SELECT VoucherNumber FROM GLEntry WHERE AccountID = 93 AND FiscalYear = 2026 "
                "AND SourceDocumentType = 'JournalEntry'")[0]
    assert close == "JE-2026-000296" and close in HEADER
    for _, _, sql in QUERIES:
        db.run(sql)                                     # every query in the script runs
    lines = CHAPTER09.text().split("\n")
    cut = max(i for i, text in enumerate(lines) if text == "" and i <= 22)   # end at a whole query
    shown = "\n".join(lines[:cut])
    y = db.window(d)
    bottom = db.editor(d, 0, y, 860, shown, tab=SCRIPT_TAB)
    note(d, "The header comment records the purpose, the database, the preparer, and the checks, "
            "and a comment above each query says what it answers. The script continues below the "
            f"lines shown, {len(lines)} lines in all.", bottom + 8, 40)
    return d


FIGURES = {
    "fig-09-01-import-vs-query": fig_09_01,
    "fig-09-02-database-structure": fig_09_02,
    "fig-09-03-account-columns": fig_09_03,
    "fig-09-04-syntax-error": fig_09_04,
    "fig-09-05-variance-check": fig_09_05,
    "fig-09-06-where-null": fig_09_06,
    "fig-09-07-variance-sources": fig_09_07,
    "fig-09-08-query-anatomy": fig_09_08,
    "fig-09-09-top-variances": fig_09_09,
    "fig-09-10-saved-script": fig_09_10,
}
