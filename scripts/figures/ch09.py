"""Chapter 9 figures."""

from __future__ import annotations

from functools import lru_cache

import dbbrowser as db
import excel as xl
from data import one, q, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, ROW_H,
                    RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

VARIANCE_ACCOUNT = 5080
CLEARING_ACCOUNT = 1090


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
    d = Diagram("Exporting Data Compared with Querying It")
    tables = one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' "
                 "AND name NOT LIKE 'sqlite_%'")[0]
    assert tables > 50
    w, xs = 170, (0, 345, 690)
    # Upper path: whole tables copied into a workbook.
    d.text("<b>Exporting or importing tables</b>", 0, 0, 860, 22, size=14, color=INK)
    src1 = d.box("<b>Charles River database</b><br>every table, every row", xs[0], 34, w, 70,
                 fill=GRAY_TINT, stroke=GRAY)
    wb = d.box("<b>Workbook</b><br>whole tables copied in", xs[1], 34, w, 70, fill=GRAY_TINT,
               stroke=GRAY)
    out1 = d.box("<b>Result</b><br>filtered, merged, and summarized by hand", xs[2], 34, w, 70,
                 fill=GRAY_TINT, stroke=GRAY)
    d.arrow(src1, wb, label="export or import")
    d.arrow(wb, out1, label="work in the workbook")
    d.text("The steps live in the workbook, and every table copied in must be refreshed.",
           0, 112, 860, 22, size=SMALL, color=INK)
    # Lower path: a saved query.
    d.text("<b>Querying the database</b>", 0, 158, 860, 22, size=14, color=INK)
    sql = d.box("<b>Saved SQL query</b><br>SELECT … FROM … WHERE …", xs[0], 192, w, 70,
                fill=BLUE_TINT, stroke=BLUE)
    src2 = d.box("<b>Charles River database</b><br>the query runs where the data is", xs[1], 192,
                 w, 70, fill=BLUE_TINT, stroke=BLUE)
    out2 = d.box("<b>Result</b><br>only the rows and columns asked for", xs[2], 192, w, 70,
                 fill=BLUE_TINT, stroke=BLUE)
    d.arrow(sql, src2, label="sent to")
    d.arrow(src2, out2, label="returns")
    d.text("The query text documents the extraction and runs again when the data changes.",
           0, 270, 860, 22, size=SMALL, color=INK)
    return d


def fig_09_02() -> Diagram:
    d = Diagram("The Database Structure Tab of DB Browser for SQLite")
    columns = q("PRAGMA table_info(GLEntry)")
    names = [r[0] for r in q("SELECT name FROM sqlite_master WHERE type = 'table' "
                             "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    i = names.index("GLEntry")
    y = db.window(d, active="Database Structure")
    widths = [300, 120, 440]
    db.structure_row(d, 0, y, widths, ["Name", "Type", "Schema"], bold=True, fill=GRAY_TINT)
    y += ROW_H
    db.structure_row(d, 0, y, widths, ["▾ Tables", "", ""], bold=True)
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
    types = {kind for _, _, kind, *_ in columns}
    assert types == {"INTEGER", "REAL", "TEXT"}, types
    note(d, "Outlined: the GLEntry table expanded to show its columns and their declared types. "
            "The list of tables is shortened.", y + 10, 22)
    return d


def fig_09_03() -> Diagram:
    d = Diagram("Choosing Columns from the Account Table")
    ids = account_ids()
    sql = ("SELECT AccountID, AccountNumber, AccountName,\n"
           "    AccountType, AccountSubType\n"
           "FROM Account;")
    headers, rows = db.run(sql)
    start = [r[0] for r in rows].index(ids[1090]) - 4
    out = db.execute_sql(d, sql, [90, 120, 290, 110, 210], shown=slice(start, start + 9))
    marked = [r for r, row in enumerate(out["rows"][start:start + 9]) if row[0] in ids.values()]
    db.emphasize_cells(d, out["geometry"], [(marked[0], 0), (marked[-1], 4)])
    note(d, "Outlined: accounts 1090 and 5080, whose AccountIDs differ from their account numbers. "
            "The grid is scrolled to the manufacturing accounts.", out["bottom"] + 8, 40)
    return d


def fig_09_04() -> Diagram:
    d = Diagram("A Calculated Check on the Variance Records")
    sql = ("SELECT WorkOrderCloseID, CloseDate,\n"
           "    MaterialVarianceAmount AS Material,\n"
           "    ConversionVarianceAmount AS Conversion,\n"
           "    TotalVarianceAmount AS Total,\n"
           "    ROUND(MaterialVarianceAmount + ConversionVarianceAmount\n"
           "        - TotalVarianceAmount, 2) AS CheckDifference\n"
           "FROM WorkOrderClose;")
    headers, rows = db.run(sql)
    assert all(r[5] == 0 for r in rows), "every close's parts add up to its total"
    out = db.execute_sql(d, sql, [150, 110, 110, 120, 110, 180], shown=slice(0, 8))
    db.emphasize_cells(d, out["geometry"], [(-1, 5), (7, 5)])
    note(d, "Outlined: the calculated CheckDifference column, zero in every row shown. "
            "The first eight of the result's rows are shown.", out["bottom"] + 8, 40)
    return d


def fig_09_05() -> Diagram:
    d = Diagram("The Source Document Types Behind the Variance Account")
    account_ids()
    sql = ("SELECT DISTINCT SourceDocumentType\n"
           "FROM GLEntry\n"
           "WHERE AccountID = 93 AND FiscalYear = 2026;")
    headers, rows = db.run(sql)
    assert [r[0] for r in rows] == ["WorkOrderClose", "JournalEntry"], rows
    out = db.execute_sql(d, sql, [260])
    db.emphasize_cells(d, out["geometry"], [(1, 0)])
    note(d, "Outlined: the JournalEntry row, which Step 4 examines.", out["bottom"] + 8, 22)
    return d


def fig_09_06() -> Diagram:
    d = Diagram("The Ten Largest Work-Order Variances of Fiscal 2026")
    sql = ("SELECT WorkOrderCloseID, WorkOrderID, CloseDate,\n"
           "    MaterialVarianceAmount AS Material,\n"
           "    DirectLaborVarianceAmount AS Labor,\n"
           "    OverheadVarianceAmount AS Overhead,\n"
           "    TotalVarianceAmount AS Total\n"
           "FROM WorkOrderClose\n"
           "WHERE CloseDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
           "ORDER BY TotalVarianceAmount DESC\n"
           "LIMIT 10;")
    headers, rows = db.run(sql)
    assert len(rows) == 10 and all(r[5] > r[3] + r[4] for r in rows), \
        "overhead is larger than material and labor together in each of the ten"
    out = db.execute_sql(d, sql, [150, 110, 110, 100, 100, 110, 100])
    db.emphasize_cells(d, out["geometry"], [(-1, 5), (9, 5)])
    note(d, "Outlined: the Overhead column, which holds most of each total.", out["bottom"] + 8, 22)
    return d


def fig_09_07() -> Diagram:
    d = Diagram("A Documented Script of the Chapter's Queries")
    script = (
        "/* Chapter 9: manufacturing variance, first look\n"
        "   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)\n"
        "   Prepared by: your name, date\n"
        "   Checks: the variance parts add up to the total in every close;\n"
        "           the 2026 ledger postings exclude closing entry JE-2026-000296 */\n"
        "\n"
        "-- Tutorial 9.1: the manufacturing accounts and their AccountIDs\n"
        "SELECT AccountID, AccountNumber, AccountName,\n"
        "    AccountType, AccountSubType\n"
        "FROM Account;\n"
        "\n"
        "-- Tutorial 9.2: the source document types of the 2026 variance postings\n"
        "SELECT DISTINCT SourceDocumentType\n"
        "FROM GLEntry\n"
        "WHERE AccountID = 93 AND FiscalYear = 2026;\n"
        "\n"
        "-- Tutorial 9.2: work orders whose variance has not yet been recorded\n"
        "SELECT WorkOrderNumber, Status, ReleasedDate, DueDate, CompletedDate\n"
        "FROM WorkOrder\n"
        "WHERE ClosedDate IS NULL;\n"
        "\n"
        "-- Tutorial 9.3: the ten largest variances of fiscal 2026\n"
        "SELECT WorkOrderCloseID, WorkOrderID, CloseDate, TotalVarianceAmount\n"
        "FROM WorkOrderClose\n"
        "WHERE CloseDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
        "ORDER BY TotalVarianceAmount DESC\n"
        "LIMIT 10;")
    close = one("SELECT VoucherNumber FROM GLEntry WHERE AccountID = 93 AND FiscalYear = 2026 "
                "AND SourceDocumentType = 'JournalEntry'")[0]
    assert close == "JE-2026-000296"
    for block in [b for b in script.split(";") if "SELECT" in b]:
        db.run(block[block.index("SELECT"):])     # every query in the script runs
    y = db.window(d)
    bottom = db.editor(d, 0, y, 860, script, tab="Chapter09.sql")
    note(d, "The header comment records the purpose, source, preparer, and checks, and a comment "
            "above each query says what it answers. Only some of the chapter's queries are shown.",
         bottom + 8, 40)
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
        d.box(code, 0, y, 520, h, fill=GRAY_TINT if i == 0 else WHITE, stroke=RULE, size=SMALL,
              align="left", valign="middle", rounded=False)
        d.box(esc(label), 540, y, 320, h, fill=BLUE_TINT, stroke=BLUE_TINT, size=SMALL,
              align="left", valign="middle", rounded=False)
        y += h + 6
    note(d, "The clauses must be written in this order. Only SELECT is always required; the others "
            "appear when a query uses them.", y + 4, 22)
    return d


FIGURES = {
    "fig-09-01-export-vs-query": fig_09_01,
    "fig-09-02-database-structure": fig_09_02,
    "fig-09-03-account-columns": fig_09_03,
    "fig-09-04-variance-check": fig_09_04,
    "fig-09-05-variance-sources": fig_09_05,
    "fig-09-06-top-variances": fig_09_06,
    "fig-09-07-saved-script": fig_09_07,
    "fig-09-08-query-anatomy": fig_09_08,
}
