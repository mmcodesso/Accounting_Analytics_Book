"""Charles River Lender Package.xlsx: the Excel part of the solution to the Chapter 17 capstone case, "Financial
Statements for a Lender".

The case keeps three files: LenderPackage.sql (queries), Charles River Lender Package.xlsx (this workbook), and
Charles River Lender Review.pbix (a ledger model). This module builds the workbook from a blank one, as the case's
Getting Started tells the reader to, and answers every requirement the workbook takes part in:

- Requirement 1: the three trial balances (one worksheet each, driven by an as-of date the way the SQL query's Params
  CTE is), the account-to-line mapping, the recorded statements, their validation against Chapter 6's control totals,
  and the accounts never posted;
- Requirement 2: the controller's materiality, the changes the Review file flags, the balances that rest on the
  opening entry, and the Questions table (a model answer; the case keeps it in the Review file);
- Requirement 3: Accrued Expenses rebuilt from its postings at each year-end;
- Requirement 4: revenue, payroll, and interest cutoff, with the proration as visible formulas;
- Requirement 5: the schedule of adjustments, the entry lines as an Excel Table (AdjustmentLines) for the Review file,
  materiality, and the passed items;
- Requirement 6: the adjusted statements (balance sheets, income, changes in equity, cash flows) and their tests;
- Requirement 7: the note schedules and the text of the required notes;
- Requirement 8: the records after the year-end and the going-concern conditions;
- Requirement 9: the memo to the CFO (a model answer, with its numbers live where the workbook holds them).

Inputs. Power Query reads CharlesRiver.xlsx wherever the computation is reasonable in M, so the workbook refreshes:
the ledger is summarized once (LedgerSummary: GLEntry by account, year, source document type, and journal entry), the
supplier-invoice postings to 2040 are read once more (AccrualClearing), and the small document tables (payroll
registers, calendar, debt, fixed assets, returns, credit memos, services, supplier invoices and payments, shipments)
load as Tables. What a query in LenderPackage.sql finds better (the cutoff populations, revenue by segment by posting
year, the receivables aging at two dates, the returns of the year after delivery, and two account mappings) is pasted
as values on the SQL Results worksheet, computed read-only from CharlesRiver.sqlite when the workbook is built, each
with a cell note naming the query's purpose, so that the SQL solution can supply the same query.

Expected values for the checks come from facts/notes/ch17.py (the functions that generate the case's instructor notes),
called directly; the notes package needs jinja2 only to render, so it is loaded here without it when jinja2 is missing.
"""

from __future__ import annotations

import importlib
import importlib.util
import math
import sys
import types
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache

from paths import REPO
from xlbuild import pq, xl
from xlbuild.solutions import COUNT, MONEY, PCT, RATIO, ExerciseBuild

FACTS = REPO / "facts"
NOTES = "Solution Notes"
DATE = "yyyy-mm-dd"
STMT = '#,##0.00;(#,##0.00);"-"'
GENERAL = "General"
XL_MANUAL, XL_AUTOMATIC = -4135, -4105
SQL_FILE = "LenderPackage.sql"
MA = "Model answer"
BLUE = 0xFF0000                 # input cells (BGR)
GREEN_FILL = 0xDAEFE2           # pasted SQL results (BGR of #E2EFDA)
GROUP_ORDER = ["Furniture", "Lighting", "Textiles", "Accessories"]
DATA_SOURCES = ["SalesInvoice", "CashReceiptApplication", "PurchaseInvoice", "DisbursementPayment", "GoodsReceipt",
                "MaterialIssue", "Shipment"]
RATES = [0.005, 0.02, 0.05, 0.15, 0.40]          # Exercise 8.1's loss rates, by bucket
BUCKET_NAMES = ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]
WRITE_DOWN = ("Damaged", "Quality Concern")
FEDERAL = 0.21

# The statement lines, in the order the statements show them.
CA_LINES = ["Cash", "Receivables", "Inventories", "Prepaid expenses and other current assets"]
CL_LINES = ["Accounts payable", "Goods received not invoiced", "Accrued liabilities", "Sales tax payable",
            "Customer credits", "Current portion of notes payable"]
REVENUE_LINES = ["Operating revenue", "Sales returns and allowances"]
EXPENSE_LINES = ["Cost of goods sold", "Operating expenses"]
OTHER_LINES = ["Interest expense", "Loss on disposal of equipment", "Other income"]

MAPPING = ('=LET(n,[@AccountNumber],s,[@AccountSubType],t,[@AccountType],IFS('
           'n=1010,"Cash",OR(n=1020,n=1030),"Receivables",OR(n=1040,n=1045,n=1046,n=1090),"Inventories",'
           'OR(s="Current Asset",s="Contra Current Asset"),"Prepaid expenses and other current assets",'
           'OR(s="Fixed Asset",s="Contra Fixed Asset",s="Noncurrent Asset"),"Property and equipment, net",'
           'n=2010,"Accounts payable",n=2020,"Goods received not invoiced",n=2050,"Sales tax payable",'
           'n=2060,"Customer credits",s="Current Liability","Accrued liabilities",'
           's="Long-Term Liability","Notes payable, less current portion",OR(n=3010,n=3020),"Common stock",'
           't="Equity","Retained earnings",s="Operating Revenue","Operating revenue",'
           's="Contra Revenue","Sales returns and allowances",s="COGS","Cost of goods sold",'
           's="Operating Expense","Operating expenses",n=7030,"Interest expense",'
           'n=7020,"Loss on disposal of equipment",TRUE,"Other income"))')


# --- the instructor notes' values (facts/notes/ch17.py), and the inputs pasted from SQL ----------------------------

def _notes_package() -> None:
    """Make facts/notes importable as the package `notes` its modules import from. Without jinja2 (the template engine
    the package needs only to render), a stand-in package gives them the same modules and a no-op @note."""
    have = sys.modules.get("notes")
    if have is not None:
        if not hasattr(have, "__path__"):
            raise SystemExit("a module named notes is loaded that is not the facts/notes package")
        return
    try:
        import jinja2  # noqa: F401
    except ImportError:
        pkg = types.ModuleType("notes")
        pkg.__path__ = [str(FACTS / "notes")]
        pkg.__file__ = str(FACTS / "notes" / "__init__.py")
        pkg.note = lambda key, file, template=None: (lambda fn: fn)
        sys.modules["notes"] = pkg
        return
    sys.path.insert(0, str(FACTS))
    importlib.import_module("notes")


@lru_cache(maxsize=None)
def data():
    spec = importlib.util.spec_from_file_location("facts_db_cap17", FACTS / "db.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Data()


@lru_cache(maxsize=None)
def ch17():
    _notes_package()
    return importlib.import_module("notes.ch17")


@lru_cache(maxsize=None)
def facts(key: str) -> dict:
    """A note's values, as facts/notes/ch17.py computes them; its claims must hold."""
    failed = []
    out = getattr(ch17(), key)(data(), lambda ok, text: ok or failed.append(text))
    if failed:
        raise SystemExit(f"ch17.{key}: the instructor note's claims fail on this dataset: {failed}")
    return out


def xr(x: float, places: int = 2) -> float:
    return ch17().xr(x, places)


def money(x: float) -> str:
    return f"{xr(x):,.2f}"


def pct(x: float, places: int = 1) -> str:
    return f"{xr(100 * x, places):.{places}f}%"


def serial(iso: str) -> int:
    return (date.fromisoformat(iso[:10]) - date(1899, 12, 30)).days


def years() -> tuple[int, int, int]:
    d = data()
    return d.F, d.P, d.C


def ye(year: int) -> str:
    return f"{year}-12-31"


def days(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


@lru_cache(maxsize=None)
def late_invoices() -> tuple[dict, ...]:
    """Test L5's population: invoices posted in another year than the latest delivery of the goods they bill."""
    rows = sorted(ch17().late(data()), key=lambda i: (i["posted"], i["number"]))
    return tuple(rows)


@lru_cache(maxsize=None)
def cutoff_groups() -> list[str]:
    groups = {g for i in late_invoices() for g in i["groups"]} | {u[5] for u in unbilled_lines()}
    return [g for g in GROUP_ORDER if g in groups] + sorted(g for g in groups if g not in GROUP_ORDER)


@lru_cache(maxsize=None)
def unbilled_lines() -> tuple[tuple, ...]:
    """Test L6's population: shipment lines never invoiced, with the order price and discount that value them."""
    return tuple(data().q(
        "SELECT sl.ShipmentLineID, s.ShipmentNumber, s.ShipmentDate, s.DeliveryDate, i.ItemCode, i.ItemGroup, "
        "c.CustomerSegment, sl.QuantityShipped, sol.UnitPrice, sol.Discount, sl.ExtendedStandardCost, "
        "ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2) FROM ShipmentLine sl "
        "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN SalesOrderLine sol ON sol.SalesOrderLineID = sl.SalesOrderLineID "
        "JOIN Item i ON i.ItemID = sl.ItemID JOIN SalesOrder so ON so.SalesOrderID = s.SalesOrderID "
        "JOIN Customer c ON c.CustomerID = so.CustomerID LEFT JOIN SalesInvoiceLine sil ON sil.ShipmentLineID = sl.ShipmentLineID "
        "WHERE sil.SalesInvoiceLineID IS NULL ORDER BY sl.ShipmentLineID"))


@lru_cache(maxsize=None)
def segment_revenue() -> tuple[tuple, ...]:
    """Invoice lines by customer segment and the year their invoice was posted (the ledger's basis)."""
    F, P, C = years()
    return tuple(data().q(
        "SELECT c.CustomerSegment, CAST(substr(p.pd, 1, 4) AS INTEGER), ROUND(SUM(sil.LineTotal), 2) FROM SalesInvoiceLine sil "
        "JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID JOIN Customer c ON c.CustomerID = si.CustomerID "
        "JOIN (SELECT SourceDocumentID AS id, MIN(PostingDate) AS pd FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' "
        "GROUP BY 1) p ON p.id = si.SalesInvoiceID WHERE substr(p.pd, 1, 4) IN (?, ?) GROUP BY 1, 2 ORDER BY 1, 2",
        str(P), str(C)))


@lru_cache(maxsize=None)
def aging(year: int) -> tuple[list[float], list[int]]:
    """Exercise 8.1's buckets at a year-end: each invoice dated by then, less the receipts applied and the credit memos
    dated by then, rounded and kept if greater than zero, aged by days past its due date."""
    asof = ye(year)
    from notes.ch08 import bucket_of
    amounts, counts = [0.0] * 5, [0] * 5
    for due, balance in data().q(
            "SELECT si.DueDate, si.GrandTotal - COALESCE((SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a "
            "WHERE a.SalesInvoiceID = si.SalesInvoiceID AND a.ApplicationDate <= ?1), 0) - COALESCE((SELECT SUM(c.GrandTotal) "
            "FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID AND c.CreditMemoDate <= ?1), 0) "
            "FROM SalesInvoice si WHERE si.InvoiceDate <= ?1", asof):
        balance = xr(balance)
        if balance > 0:
            k = bucket_of(days(due, asof))
            amounts[k] += balance
            counts[k] += 1
    return [xr(a) for a in amounts], counts


@lru_cache(maxsize=None)
def payroll_accounts() -> tuple[tuple[str, int], ...]:
    """The account each cost center's gross pay is debited to (PayrollSummary postings of the current year)."""
    d = data()
    return tuple(d.q("SELECT c.CostCenterName, a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                     "JOIN CostCenter c ON c.CostCenterID = g.CostCenterID WHERE g.SourceDocumentType = 'PayrollSummary' "
                     "AND g.Debit > 0 AND a.AccountNumber <> 6060 AND g.FiscalYear = ? GROUP BY 1, 2 ORDER BY 1", d.C))


@lru_cache(maxsize=None)
def old_accounts() -> list[str]:
    """The expense accounts of the accruals older than the clearing window at any year-end (A3's lines)."""
    out = set()
    for y in years():
        out |= {i["account"] for i in ch17().composition(data(), y)["old_items"]}
    return sorted(out)


# --- workbook helpers ---------------------------------------------------------------------------------------------

def col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def put(ws, cells: dict[str, object]) -> None:
    for addr, v in cells.items():
        prop = "Formula2" if isinstance(v, str) and v.startswith("=") else "Value"
        xl.retry(lambda a=addr, x=v, k=prop: setattr(ws.Range(a), k, x))


def bold(ws, addr: str) -> None:
    ws.Range(addr).Font.Bold = True


def heading(ws, addr: str, text: str, size: int = 12) -> None:
    ws.Range(addr).Value = text
    ws.Range(addr).Font.Bold = True
    ws.Range(addr).Font.Size = size


def title(ws, text: str, sub: str = "") -> None:
    ws.Range("A1").Value = text
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 14
    if sub:
        ws.Range("A2").Value = sub
        ws.Range("A2").Font.Italic = True


def name(b: ExerciseBuild, nm: str, ws, addr: str) -> str:
    xl.retry(lambda: b.wb.Names.Add(Name=nm, RefersTo=f"='{ws.Name}'!{ws.Range(addr).Address}"))
    return nm


def note(ws, addr: str, text: str) -> None:
    def run():
        rng = ws.Range(addr)
        if rng.Comment is not None:
            rng.Comment.Delete()
        rng.AddComment(text)
    xl.retry(run)


def widths(ws, spec: dict[str, float]) -> None:
    for cols, w in spec.items():
        ws.Columns(cols).ColumnWidth = w


def model_answer(ws, row: int, label: str, paragraphs: list[str], last_col: int = 8, note_text: str | None = None) -> int:
    """A labeled model answer: one merged, wrapped cell per paragraph across columns A to last_col, each tall enough
    for its text. Returns the next free row."""
    ws.Cells(row, 1).Value = label
    ws.Cells(row, 1).Font.Bold = True
    if note_text:
        ws.Cells(row, 1).AddComment(note_text)
    width = sum(ws.Columns(c).ColumnWidth for c in range(1, last_col + 1))
    r = row + 1
    for text in paragraphs:
        rng = ws.Range(ws.Cells(r, 1), ws.Cells(r, last_col))
        rng.Merge()
        rng.WrapText = True
        rng.VerticalAlignment = -4160                       # top
        ws.Cells(r, 1).Value = text
        lines = math.ceil(len(text) / max(20.0, width * 1.05)) + 1
        ws.Rows(r).RowHeight = min(409, 15 * lines)
        r += 1
    return r + 1


def first_data_sheet(b: ExerciseBuild):
    first = b.found.get("first_data")
    if first:
        return b.wb.Worksheets(first)
    return next((ws for ws in b.wb.Worksheets if ws.Name == NOTES), None)


def analysis_sheet(b: ExerciseBuild, sheet_name: str):
    """A worksheet of the package, placed before the data worksheets."""
    before = first_data_sheet(b)
    ws = xl.sheet(b.wb, sheet_name, before=before) if before is not None else xl.sheet(b.wb, sheet_name)
    b.found.setdefault("sheets", {})[sheet_name] = b.found.get("describe", {}).get(sheet_name, "")
    return ws


def data_sheet(b: ExerciseBuild, sheet_name: str):
    """A worksheet that holds loaded data, placed after the package's worksheets."""
    notes_ws = next((ws for ws in b.wb.Worksheets if ws.Name == NOTES), None)
    ws = xl.sheet(b.wb, sheet_name, before=notes_ws) if notes_ws is not None else xl.sheet(b.wb, sheet_name)
    b.found.setdefault("first_data", sheet_name)
    return ws


def nav(b: ExerciseBuild, number: int, table: str, corrections: dict | None = None, extra=()) -> str:
    return pq.navigator_query(b.src, number, table, list(pq.detected_types(b.xlsx, table)), corrections, list(extra))


def ready(app, timeout: float = 600.0) -> None:
    """Wait until Excel accepts calls. Unlike xl.wait_ready, this does not wait for the calculation to finish: under
    the manual calculation the requirements are built in, the calculation stays pending until it is switched back."""
    import time
    deadline = time.time() + timeout
    while not xl.retry(lambda: app.Ready):
        if time.time() > deadline:
            raise TimeoutError("Excel stayed busy")
        time.sleep(0.25)


def load_to(wb, query: str, ws, cell: str = "A1"):
    """Load a query as an Excel Table at a cell of an existing worksheet (Close & Load To, Existing worksheet)."""
    connection = (f"OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location={query};"
                  "Extended Properties=\"\"")
    lo = ws.ListObjects.Add(xl.XL_SRC_EXTERNAL, connection, None, xl.XL_YES, ws.Range(cell))
    qt = lo.QueryTable
    qt.CommandType = xl.XL_CMD_SQL
    qt.CommandText = [f"SELECT * FROM [{query}]"]
    qt.RowNumbers = False
    qt.FillAdjacentFormulas = False
    qt.PreserveFormatting = True
    qt.RefreshOnFileOpen = False
    qt.BackgroundQuery = False
    qt.AdjustColumnWidth = True
    qt.PreserveColumnInfo = True
    xl.retry(lambda: qt.Refresh(False))
    ready(wb.Application)
    lo.Name = query
    conn = qt.WorkbookConnection
    conn.Name = f"Query - {query}"
    conn.Description = f"Connection to the '{query}' query in the workbook."
    return lo


def loaded(b: ExerciseBuild, query: str, m: str, sheet_name: str, description: str, formats: dict | None = None):
    """Add a query and load it to a data worksheet of its own, named after it."""
    xl.add_query(b.wb, query, m, description)
    ws = data_sheet(b, sheet_name)
    lo = load_to(b.wb, query, ws)
    for column, fmt in (formats or {}).items():
        lo.ListColumns(column).DataBodyRange.NumberFormat = fmt
    b.found.setdefault("queries", []).append((query, description))
    b.found.setdefault("data_sheets", {})[sheet_name] = description
    return lo


def connection_only(b: ExerciseBuild, query: str, m: str, description: str) -> None:
    xl.add_query(b.wb, query, m, description)
    b.found.setdefault("queries", []).append((query, description + " (connection only)"))


def range_table(ws, top_left: str, header: list[str], rows: list[list], table_name: str, formats: dict | None = None):
    """Values (and per-row formulas) written as one block, then made an Excel Table. Writing the block at once keeps
    Excel from turning a column's first formula into a calculated column."""
    r0, c0 = ws.Range(top_left).Row, ws.Range(top_left).Column
    block = [header] + rows
    rng = ws.Range(ws.Cells(r0, c0), ws.Cells(r0 + len(block) - 1, c0 + len(header) - 1))
    rng.Formula2 = [[("" if v is None else v) for v in row] for row in block]
    lo = ws.ListObjects.Add(1, rng, None, xl.XL_YES)
    lo.Name = table_name
    for column, fmt in (formats or {}).items():
        lo.ListColumns(column).DataBodyRange.NumberFormat = fmt
    return lo


def pasted(b: ExerciseBuild, ws, top_left: str, header: list[str], rows: list[list], table_name: str, purpose: str,
           formats: dict | None = None):
    """A query's result pasted as values (Copy with Headers), with a note naming the query it comes from."""
    lo = range_table(ws, top_left, header, rows, table_name, formats)
    lo.HeaderRowRange.Interior.Color = GREEN_FILL
    note(ws, top_left, f"Pasted from {SQL_FILE}, query: {purpose}. Values computed read-only from CharlesRiver.sqlite "
                       "when this workbook was built (dataset release in Solution Notes).")
    b.found.setdefault("pasted", []).append((table_name, purpose))
    return lo


def line_sum(column: str, line: str) -> str:
    return f'SUMIFS(WorkingTB[{column}],WorkingTB[StatementLine],"{line}")'


def adj_sum(line: str, year: int) -> str:
    return f'SUMIFS(AdjustmentLines[Amount],AdjustmentLines[StatementLine],"{line}",AdjustmentLines[YearEnd],YE_{year})'


def ledger(field: str, **criteria) -> str:
    """SUMIFS over LedgerSummary; criteria by column, as formula text (strings are quoted here)."""
    parts = []
    for column, value in criteria.items():
        if isinstance(value, str) and not value.startswith(("YE_", '"', "'", "$", "\"")) and not value[:1].isdigit() \
                and not value.startswith(("<", ">")) and value not in ("TRUE", "FALSE"):
            value = f'"{value}"'
        elif isinstance(value, str) and value.startswith(("<", ">")):
            value = f'"{value}"'
        parts.append(f"LedgerSummary[{column}],{value}")
    return f"SUMIFS(LedgerSummary[{field}]," + ",".join(parts) + ")"


# --- Power Query: the inputs ----------------------------------------------------------------------------------------

def date_types(columns: list[str]) -> str:
    return pq.transform_types([(c, "type date") for c in columns])


def load_inputs(b: ExerciseBuild) -> None:
    """The queries of Requirement 1: the chart, the journal entries, and the ledger summary."""
    F, P, C = years()
    connection_only(b, "ChartOfAccounts", nav(b, 1, "Account", extra=[
        ("Removed Other Columns", pq.select_columns(["AccountID", "AccountNumber", "AccountName", "AccountType",
                                                     "AccountSubType", "NormalBalance", "IsActive"]))]),
        "T1_Account, the chart of accounts")
    loaded(b, "JournalEntries", nav(b, 2, "JournalEntry", corrections={"ReversesJournalEntryID": "Int64.Type"}, extra=[
        ("Removed Other Columns", pq.select_columns(["JournalEntryID", "EntryNumber", "PostingDate", "EntryType",
                                                     "Description", "TotalAmount", "ReversesJournalEntryID"])),
        ("Merged Queries", 'Table.NestedJoin({prev}, {"ReversesJournalEntryID"}, {prev}, {"JournalEntryID"}, '
                           '"Reversed", JoinKind.LeftOuter)'),
        ("Expanded Reversed", 'Table.ExpandTableColumn({prev}, "Reversed", {"EntryNumber"}, {"ReversesEntryNumber"})'),
        ("Changed Type1", date_types(["PostingDate"])),
        ("Sorted Rows", 'Table.Sort({prev},{{"EntryNumber", Order.Ascending}})')]),
        "Journal Entries", "T2_JournalEntry, with the number of the entry each Accrual Adjustment reverses",
        {"PostingDate": DATE, "TotalAmount": MONEY})
    group = ('Table.Group({prev}, {"AccountID", "Year", "SourceDocumentType", "EntryNumber"}, '
             '{{"Debit", each List.Sum([Debit]), type number}, {"Credit", each List.Sum([Credit]), type number}, '
             '{"Rows", each Table.RowCount(_), Int64.Type}, {"FirstPostingDate", each List.Min([PostingDate]), type datetime}, '
             '{"LastPostingDate", each List.Max([PostingDate]), type datetime}})')
    loaded(b, "LedgerSummary", nav(b, 3, "GLEntry", extra=[
        ("Removed Other Columns", pq.select_columns(["PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber",
                                                     "SourceDocumentType"])),
        ("Inserted Year", 'Table.AddColumn({prev}, "Year", each Date.Year([PostingDate]), Int64.Type)'),
        ("Added EntryNumber", 'Table.AddColumn({prev}, "EntryNumber", each if [SourceDocumentType] = "JournalEntry" '
                              'then [VoucherNumber] else null, type text)'),
        ("Grouped Rows", group),
        ("Merged Queries", pq.merge("JournalEntries", "EntryNumber", "EntryNumber", "JournalEntries")),
        ("Expanded JournalEntries", 'Table.ExpandTableColumn({prev}, "JournalEntries", {"EntryType", "PostingDate", '
                                    '"ReversesEntryNumber"}, {"EntryType", "EntryDate", "ReversesEntryNumber"})'),
        ("Merged Queries1", pq.merge("ChartOfAccounts", "AccountID", "AccountID", "ChartOfAccounts")),
        ("Expanded ChartOfAccounts", pq.expand("ChartOfAccounts", ["AccountNumber", "AccountName", "AccountType",
                                                                   "AccountSubType"])),
        ("Added IsYearEndClose", 'Table.AddColumn({prev}, "IsYearEndClose", each [EntryType] <> null and '
                                 'Text.StartsWith([EntryType], "Year-End Close"), type logical)'),
        ("Added Net", 'Table.AddColumn({prev}, "Net", each [Debit] - [Credit], type number)'),
        ("Changed Type1", date_types(["EntryDate", "FirstPostingDate", "LastPostingDate"])),
        ("Sorted Rows", 'Table.Sort({prev},{{"AccountNumber", Order.Ascending}, {"Year", Order.Ascending}, '
                        '{"SourceDocumentType", Order.Ascending}, {"EntryNumber", Order.Ascending}})')]),
        "Ledger", "T3_GLEntry (Transform Data) grouped by account, year, source document type, and journal entry, "
                  "with the entry type and date, the reversed entry, and the account's attributes",
        {"Debit": MONEY, "Credit": MONEY, "Net": MONEY, "EntryDate": DATE, "FirstPostingDate": DATE,
         "LastPostingDate": DATE})
    loaded(b, "WorkingTB", pq.steps_query([
        ("Source", "ChartOfAccounts"),
        ("Filtered Rows", pq.select_rows('[AccountSubType] <> "Header"')),
        ("Sorted Rows", 'Table.Sort({prev},{{"AccountNumber", Order.Ascending}})')]),
        "Working TB", "the chart of accounts without its headers: the working trial balance's rows")


# --- the Documentation worksheet ----------------------------------------------------------------------------------

DESCRIBE = {
    "Documentation": "purpose, sources, the date through which the data run, conventions, and the workbook's contents",
    "TB 2024": "the trial balance at the first year-end, driven by its as-of date (the SQL query's Params CTE)",
    "TB 2025": "the trial balance at the prior year-end",
    "TB 2026": "the trial balance at the current year-end",
    "Working TB": "WorkingTB: every account, its statement line, recorded balances, adjustments, adjusted balances",
    "Recorded": "Requirement 1: the recorded statements, their validation, and the accounts never posted",
    "Review": "Requirement 2: materiality, the changes above it, the opening-entry balances, the Questions table",
    "Accrued Expenses": "Requirement 3: account 2040 rebuilt from its postings at each year-end",
    "Cutoff": "Requirement 4: revenue, payroll, and interest cutoff at each year-end",
    "Adjustments": "Requirement 5: the schedule of adjustments, AdjustmentLines, materiality, and the passed items",
    "Statements": "Requirement 6: the adjusted statements and their tests",
    "Notes": "Requirement 7: the note schedules and the text of the required notes",
    "Later Events": "Requirement 8: the records after the year-end and the going-concern conditions",
    "Memo": "Requirement 9: the memo to the CFO",
    "SQL Results": "query results pasted from LenderPackage.sql (green headers, each with a note naming its query)",
}


def documentation_header(b: ExerciseBuild) -> None:
    F, P, C = years()
    ws = b.wb.Worksheets("Documentation")
    title(ws, "Charles River Lender Package", "Charles River Lender Package.xlsx: financial statements for the bank's "
                                              "credit committee (instructor solution, the Excel part of the case)")
    put(ws, {"A4": "Purpose",
             "B4": f"Turn the ledger into GAAP statements for fiscal {C} with fiscal {P} for comparison: trial balances, "
                   "the adjustments with their evidence, the adjusted statements, and the required notes. Nothing is "
                   "posted to the ledger; every adjustment is a numbered entry here, for the CFO's approval.",
             "A5": "Prepared by", "B5": "Staff accountant (model solution); reviewed by the controller",
             "A6": "Sources",
             "B6": "CharlesRiver.xlsx through Power Query (refresh with Data > Refresh All); query results pasted from "
                   "LenderPackage.sql run on CharlesRiver_Capstone.sqlite (the SQL Results worksheet).",
             "A7": "Data run through",
             "B7": "=MIN(MAXIFS(LedgerSummary[LastPostingDate],LedgerSummary[SourceDocumentType],{" +
                   ",".join(f'"{s}"' for s in DATA_SOURCES) + "}))",
             "C7": "the earliest of the last posting dates of sales invoices, receipts applied, supplier invoices and "
                   "payments, goods receipts, material issues, and shipments",
             "A8": "Ledger extract ends", "B8": "=MAX(LedgerSummary[LastPostingDate])",
             "C8": '="supplier payments only after "&TEXT(B7,"yyyy-mm-dd")&"; payroll postings end on "&'
                   'TEXT(MAXIFS(LedgerSummary[LastPostingDate],LedgerSummary[SourceDocumentType],"PayrollSummary"),'
                   '"yyyy-mm-dd")',
             "A9": "Year-ends", "B9": f"=DATE({F},12,31)", "C9": f"=DATE({P},12,31)", "D9": f"=DATE({C},12,31)",
             "A10": "Materiality", "B10": "5% of income before income taxes for the year, as the ledger records it "
                                          "(Adjustments worksheet)"})
    ws.Range("B7:B9").NumberFormat = DATE
    ws.Range("C9:D9").NumberFormat = DATE
    ws.Range("B9:D9").Font.Color = BLUE
    for y, c in zip((F, P, C), "BCD"):
        name(b, f"YE_{y}", ws, f"{c}9")
    name(b, "DataThrough", ws, "B7")
    name(b, "LedgerEnds", ws, "B8")
    ws.Range("A4:A10").Font.Bold = True
    widths(ws, {"A": 26, "B": 70, "C": 60, "D": 14})
    ws.Range("B4:B6").WrapText = True
    ws.Range("C7:C8").WrapText = True


def documentation(b: ExerciseBuild) -> None:
    """The lists below the header: worksheets, queries, pasted inputs, and conventions (rewritten as the workbook grows)."""
    ws = b.wb.Worksheets("Documentation")
    ws.Range("A12:D200").Clear()
    rows: list[tuple[str, str]] = [("Worksheets", "")]
    for s in b.wb.Worksheets:
        if s.Name in DESCRIBE:
            rows.append((s.Name, DESCRIBE[s.Name]))
        elif s.Name in b.found.get("data_sheets", {}):
            rows.append((s.Name, "data: " + b.found["data_sheets"][s.Name]))
        elif s.Name == NOTES:
            rows.append((s.Name, "the requirements, the checks of every result against the dataset, and the "
                                 "instructor notes"))
    rows += [("", ""), ("Queries", "")] + [(q, d) for q, d in b.found.get("queries", [])]
    rows += [("", ""), ("Pasted from LenderPackage.sql", "")] + [(t, p) for t, p in b.found.get("pasted", [])]
    rows += [("", ""), ("Conventions", ""),
             ("Balances", "Debits less credits in the trial balances; statements show assets, liabilities, equity, "
                          "revenue, and expenses as positive amounts."),
             ("As-of rule", "A trial balance holds the postings on or before its as-of date and leaves out a year-end "
                            "close only when the close is dated on that date (the ledger summary is by year, so the "
                            "as-of dates are year-ends)."),
             ("Flows", "A year's activity leaves out the year-end closes."),
             ("Adjustments", "Numbered A (recorded), R (reclassification), P (passed), T (trivial); entry lines in the "
                             "AdjustmentLines Table, one row per account and year-end, as debits less credits."),
             ("Inputs", "Blue: typed parameters. Green headers: results pasted from LenderPackage.sql."),
             ("Checks", "The Solution Notes worksheet compares every result with the dataset after a refresh.")]
    for i, (a, t) in enumerate(rows, start=12):
        ws.Cells(i, 1).Value = a
        ws.Cells(i, 2).Value = t
        if a and not t or a in ("Worksheets", "Queries", "Conventions", "Pasted from LenderPackage.sql"):
            ws.Cells(i, 1).Font.Bold = True
    ws.Range(f"B12:B{11 + len(rows)}").WrapText = True


# --- Requirement 1: the trial balances and the recorded statements ---------------------------------------------------

def trial_balance_sheet(b: ExerciseBuild, year: int) -> None:
    ws = analysis_sheet(b, f"TB {year}")
    title(ws, f"Trial balance at {ye(year)}", "One query rerun with a parameter: change the as-of date in B3 "
                                              "(a year-end) and the list recomputes.")
    put(ws, {"A3": "As-of date", "B3": f"=YE_{year}",
             "A4": "Rule", "B4": "Postings on or before the as-of date; a year-end close left out only when dated on it"})
    ws.Range("B3").NumberFormat = DATE
    ws.Range("B3").Font.Color = BLUE
    heads = ["AccountNumber", "AccountName", "AccountType", "AccountSubType", "Balance", "DebitBalance",
             "CreditBalance", "Postings"]
    for i, h in enumerate(heads, start=1):
        ws.Cells(6, i).Value = h
    bold(ws, "A6:H6")
    keep = ("(LedgerSummary[Year]<=YEAR($B$3))*NOT(LedgerSummary[IsYearEndClose]*"
            "(LedgerSummary[EntryDate]=$B$3))")
    sum_of = lambda field: (f"SUMIFS(LedgerSummary[{field}],LedgerSummary[AccountNumber],A7#,LedgerSummary[Year],"
                            f'"<="&YEAR($B$3))-SUMIFS(LedgerSummary[{field}],LedgerSummary[AccountNumber],A7#,'
                            f"LedgerSummary[IsYearEndClose],TRUE,LedgerSummary[EntryDate],$B$3)")
    put(ws, {"A7": f"=SORT(UNIQUE(FILTER(LedgerSummary[AccountNumber],{keep})))",
             "B7": "=XLOOKUP(A7#,WorkingTB[AccountNumber],WorkingTB[AccountName])",
             "C7": "=XLOOKUP(A7#,WorkingTB[AccountNumber],WorkingTB[AccountType])",
             "D7": "=XLOOKUP(A7#,WorkingTB[AccountNumber],WorkingTB[AccountSubType])",
             "E7": f"=ROUND({sum_of('Net')},2)",
             "F7": "=IF(E7#>0,E7#,0)", "G7": "=IF(E7#<0,-E7#,0)",
             "H7": f"={sum_of('Rows')}"})
    ws.Range("E7:G200").NumberFormat = MONEY
    ws.Range("H7:H200").NumberFormat = COUNT
    put(ws, {"J6": "Summary", "J7": "Accounts with postings", "K7": "=ROWS(A7#)",
             "J8": "Accounts at zero", "K8": "=SUM(--(E7#=0))",
             "J9": "Debit balances", "K9": "=SUM(F7#)", "J10": "Credit balances", "K10": "=SUM(G7#)",
             "J11": "Debits less credits", "K11": "=ROUND(K9-K10,2)"})
    bold(ws, "J6")
    ws.Range("K7:K8").NumberFormat = COUNT
    ws.Range("K9:K11").NumberFormat = MONEY
    for nm, addr in (("Accounts", "K7"), ("Zero", "K8"), ("Debits", "K9"), ("Credits", "K10")):
        name(b, f"TB{year}_{nm}", ws, addr)
    note(ws, "A6", f"The trial-balance query of {SQL_FILE} (Params CTE with AsOfDate) gives the same rows; here the "
                   "LedgerSummary query plays its part, so the worksheet refreshes with the workbook.")
    widths(ws, {"A": 15, "B": 44, "C": 12, "D": 22, "E": 18, "F": 18, "G": 18, "H": 10, "I": 3, "J": 24, "K": 18})


def working_tb(b: ExerciseBuild) -> None:
    F, P, C = years()
    lo = xl.table(b.wb, "WorkingTB")
    xl.add_column(lo, "StatementLine", MAPPING)
    xl.add_column(lo, "Statement", '=IF(OR([@AccountType]="Revenue",[@AccountType]="Expense"),"Income statement",'
                                   '"Balance sheet")')
    for y in (F, P, C):
        xl.add_column(lo, f"Recorded{y}", f"=XLOOKUP([@AccountNumber],'TB {y}'!$A$7#,'TB {y}'!$E$7#,0)", MONEY)
    lo.ShowTotals = True
    lo.TotalsRowRange.Cells(1, 1).Value = "Total"
    for y in (F, P, C):
        lo.ListColumns(f"Recorded{y}").TotalsCalculation = 1          # Sum
    lo.TotalsRowRange.NumberFormat = MONEY
    ws = lo.Range.Worksheet
    ws.Columns("A:Z").AutoFit()
    note(ws, "A1", "WorkingTB: the chart of accounts (ChartOfAccounts without its headers). StatementLine maps each "
                   "account to a line of the statements by AccountSubType and account number; the Recorded columns "
                   "read the three trial-balance worksheets.")


TSE = "Total stockholders' equity"
TLSE = "Total liabilities and stockholders' equity"


def statement_block(ws, top: int, columns: list[tuple[str, str, int | None]]) -> dict[str, int]:
    """A balance sheet and an income statement, one column per (header, value column of WorkingTB, adjustment year or
    None). Returns the row of each line. Amounts are positive on their normal side; the loss on disposal, a debit on a
    revenue-type account, shows in parentheses."""
    rows: dict[str, int] = {}
    n = len(columns)
    r = top

    def value(line: str, column: str, adj_year: int | None, sign: int) -> str:
        f = line_sum(column, line)
        if adj_year is not None:
            f += "+" + adj_sum(line, adj_year)
        return f"{'-' if sign < 0 else ''}({f})"

    def write(label: str, cells: list[str], style: str = "") -> None:
        nonlocal r
        ws.Cells(r, 1).Value = label
        for k, f in enumerate(cells):
            ws.Cells(r, 2 + k).Formula2 = f
        if style == "bold":
            ws.Range(ws.Cells(r, 1), ws.Cells(r, 1 + n)).Font.Bold = True
        rows[label] = r
        r += 1

    def lines(line: str, sign: int) -> None:
        write(line, ["=" + value(line, c, a, sign) for _, c, a in columns])

    def total(label: str, expr) -> None:
        write(label, ["=" + expr(col(2 + k)) for k in range(n)], "bold")

    def header(text: str, prefix: str = "") -> None:
        nonlocal r
        ws.Cells(r, 1).Value = text
        ws.Cells(r, 1).Font.Bold = True
        for k, (h, _, _) in enumerate(columns):
            cell = ws.Cells(r, 2 + k)
            cell.Value = prefix + h
            cell.Font.Bold = True
            cell.HorizontalAlignment = -4152
        r += 1

    header("Balance sheet")
    for line in CA_LINES:
        lines(line, 1)
    total("Total current assets", lambda c: f"SUM({c}{rows[CA_LINES[0]]}:{c}{rows[CA_LINES[-1]]})")
    lines("Property and equipment, net", 1)
    total("Total assets", lambda c: f"{c}{rows['Total current assets']}+{c}{rows['Property and equipment, net']}")
    r += 1
    for line in CL_LINES:
        lines(line, -1)
    total("Total current liabilities", lambda c: f"SUM({c}{rows[CL_LINES[0]]}:{c}{rows[CL_LINES[-1]]})")
    lines("Notes payable, less current portion", -1)
    total("Total liabilities", lambda c: f"{c}{rows['Total current liabilities']}+"
                                         f"{c}{rows['Notes payable, less current portion']}")
    lines("Common stock", -1)
    re_row = r
    write("Retained earnings", ["" for _ in columns])
    total(TSE, lambda c: f"{c}{rows['Common stock']}+{c}{re_row}")
    total(TLSE, lambda c: f"{c}{rows['Total liabilities']}+{c}{rows[TSE]}")
    write("Assets less liabilities and equity",
          [f"=ROUND({col(2 + k)}{rows['Total assets']}-{col(2 + k)}{rows[TLSE]},2)" for k in range(n)])
    r += 1
    header("Income statement", "Year to ")
    lines("Operating revenue", -1)
    lines("Sales returns and allowances", 1)
    total("Net revenue", lambda c: f"{c}{rows['Operating revenue']}-{c}{rows['Sales returns and allowances']}")
    lines("Cost of goods sold", 1)
    total("Gross margin", lambda c: f"{c}{rows['Net revenue']}-{c}{rows['Cost of goods sold']}")
    lines("Operating expenses", 1)
    total("Operating income", lambda c: f"{c}{rows['Gross margin']}-{c}{rows['Operating expenses']}")
    lines("Interest expense", 1)
    lines("Loss on disposal of equipment", -1)
    lines("Other income", -1)
    total("Income before income taxes", lambda c: f"{c}{rows['Operating income']}-{c}{rows['Interest expense']}+"
                                                  f"{c}{rows['Loss on disposal of equipment']}+{c}{rows['Other income']}")
    write("Income taxes", ["=0" for _ in columns])
    total("Net income", lambda c: f"{c}{rows['Income before income taxes']}-{c}{rows['Income taxes']}")
    for k, (_, c, a) in enumerate(columns):
        ws.Cells(re_row, 2 + k).Formula2 = f"={value('Retained earnings', c, a, -1)}+{col(2 + k)}{rows['Net income']}"
    ws.Range(ws.Cells(top, 2), ws.Cells(r, 1 + n)).NumberFormat = STMT
    return rows


def r1(b: ExerciseBuild) -> None:
    F, P, C = years()
    assert b.year == C, (b.year, C)
    ws = b.wb.Worksheets(1)
    ws.Name = "Documentation"
    b.found["describe"] = DESCRIBE
    load_inputs(b)
    documentation_header(b)
    for y in (F, P, C):
        trial_balance_sheet(b, y)
    working_tb(b)
    # the Working TB worksheet sits after the trial balances, before the data
    wt = b.wb.Worksheets("Working TB")
    wt.Move(None, b.wb.Worksheets(f"TB {C}"))
    b.found["first_data"] = "Journal Entries"

    ws = analysis_sheet(b, "Recorded")
    title(ws, "The ledger as it stands: recorded statements",
          "Requirement 1. Lines by AccountSubType and account number (WorkingTB[StatementLine]); amounts as recorded.")
    rows = statement_block(ws, 4, [(ye(y), f"Recorded{y}", None) for y in (F, P, C)])
    b.found["recorded_rows"] = rows
    for y, c in zip((F, P, C), "BCD"):
        name(b, f"RecTA_{y}", ws, f"{c}{rows['Total assets']}")
        name(b, f"RecCA_{y}", ws, f"{c}{rows['Total current assets']}")
        name(b, f"RecCL_{y}", ws, f"{c}{rows['Total current liabilities']}")
        name(b, f"RecNI_{y}", ws, f"{c}{rows['Net income']}")
    r = max(rows.values()) + 2
    heading(ws, f"A{r}", "Other recorded balances")
    put(ws, {f"A{r + 1}": "Notes payable (2110, all classified long-term)",
             f"A{r + 2}": "Retained earnings before the year's close (3030)",
             f"A{r + 3}": "Common stock (3010)",
             f"A{r + 4}": "Close to retained earnings (Income Summary close, credit to 3030)",
             f"A{r + 5}": "Net income less the close"})
    for y, c in zip((F, P, C), "BCD"):
        put(ws, {f"{c}{r + 1}": f'=-SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],2110)',
                 f"{c}{r + 2}": f'=-SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],3030)',
                 f"{c}{r + 3}": f'=-SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],3010)',
                 f"{c}{r + 4}": (f'=SUMIFS(LedgerSummary[Credit],LedgerSummary[AccountNumber],3030,'
                                 f'LedgerSummary[IsYearEndClose],TRUE,LedgerSummary[EntryDate],YE_{y})-'
                                 f'SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],3030,'
                                 f'LedgerSummary[IsYearEndClose],TRUE,LedgerSummary[EntryDate],YE_{y})'),
                 f"{c}{r + 5}": f"=ROUND({c}{rows['Net income']}-{c}{r + 4},2)"})
        name(b, f"RecNotes_{y}", ws, f"{c}{r + 1}")
        name(b, f"RecRE_{y}", ws, f"{c}{r + 2}")
        name(b, f"RecStock_{y}", ws, f"{c}{r + 3}")
        name(b, f"CloseToRE_{y}", ws, f"{c}{r + 4}")
    ws.Range(f"B{r + 1}:D{r + 5}").NumberFormat = STMT

    r += 7
    heading(ws, f"A{r}", "Validation against control totals already trusted")
    rec = facts("m1")["rec"]
    put(ws, {f"A{r + 1}": f"Chapter 6: pre-closing trial balance at {ye(C)}, debit and credit balances",
             f"B{r + 1}": xr(rec[-1]["debits"]), f"C{r + 1}": f"=TB{C}_Debits", f"D{r + 1}": f"=ROUND(C{r + 1}-B{r + 1},2)",
             f"A{r + 2}": f"Chapter 6: net income of fiscal {C}",
             f"B{r + 2}": xr(facts("m1")["ni"][-1]), f"C{r + 2}": f"=RecNI_{C}", f"D{r + 2}": f"=ROUND(C{r + 2}-B{r + 2},2)",
             f"A{r + 3}": "Every trial balance balances (debits less credits, three year-ends)",
             f"C{r + 3}": f"=ROUND(TB{F}_Debits-TB{F}_Credits,2)+ROUND(TB{P}_Debits-TB{P}_Credits,2)+"
                          f"ROUND(TB{C}_Debits-TB{C}_Credits,2)",
             f"A{r + 4}": "Every balance sheet balances once the year's income is in retained earnings",
             f"C{r + 4}": f"=SUM(B{rows['Assets less liabilities and equity']}:D{rows['Assets less liabilities and equity']})",
             f"A{r + 5}": "Net income equals the close to retained earnings at each year-end",
             f"C{r + 5}": f"=SUM(B{r - 2}:D{r - 2})"})
    for k in (1, 2):
        ws.Range(f"B{r + k}").Font.Color = BLUE
    note(ws, f"B{r + 1}", "Typed from Chapter 6 (the pre-closing trial balance and income statement of fiscal "
                          f"{C}), the control totals the case names.")
    ws.Range(f"B{r + 1}:D{r + 5}").NumberFormat = STMT
    put(ws, {f"B{r}": "Control total", f"C{r}": "Workbook", f"D{r}": "Difference"})
    bold(ws, f"B{r}:D{r}")
    name(b, "Ch6Difference", ws, f"D{r + 1}")
    name(b, "Ch6NIDifference", ws, f"D{r + 2}")
    name(b, "TBDifference", ws, f"C{r + 3}")
    name(b, "BSDifference", ws, f"C{r + 4}")
    name(b, "CloseDifference", ws, f"C{r + 5}")

    r += 7
    heading(ws, f"A{r}", "Accounts never posted (an anti-join of the chart and the ledger), headers aside")
    put(ws, {f"A{r + 1}": "AccountNumber", f"B{r + 1}": "AccountName", f"C{r + 1}": "IsActive",
             f"A{r + 2}": ("=LET(n,WorkingTB[AccountNumber],never,COUNTIFS(LedgerSummary[AccountNumber],n)=0,"
                           "FILTER(HSTACK(n,WorkingTB[AccountName],WorkingTB[IsActive]),never))"),
             f"E{r + 1}": "Never posted", f"F{r + 1}": f"=ROWS(A{r + 2}#)",
             f"E{r + 2}": "Active", f"F{r + 2}": f"=SUM(CHOOSECOLS(A{r + 2}#,3))",
             f"E{r + 3}": "Inactive", f"F{r + 3}": f"=F{r + 1}-F{r + 2}",
             f"E{r + 4}": "Accounts named for income tax", f"F{r + 4}": '=COUNTIFS(WorkingTB[AccountName],"*income tax*")',
             f"E{r + 5}": "Accounts named for any tax", f"F{r + 5}": '=TEXTJOIN("; ",TRUE,FILTER(WorkingTB[AccountName],'
                                                                     'ISNUMBER(SEARCH("tax",WorkingTB[AccountName]))))'})
    bold(ws, f"A{r + 1}:C{r + 1}")
    name(b, "NeverPosted", ws, f"F{r + 1}")
    name(b, "NeverActive", ws, f"F{r + 2}")
    name(b, "NeverInactive", ws, f"F{r + 3}")
    name(b, "IncomeTaxAccounts", ws, f"F{r + 4}")
    note(ws, f"A{r}", f"The anti-join of {SQL_FILE} (Account LEFT JOIN GLEntry ... WHERE GLEntry is NULL) returns the "
                      "same list; here COUNTIFS on the ledger summary plays its part.")
    r += 2 + len(ch17().never_posted(data())) + 1
    r = model_answer(ws, r, MA + ": what the chart lacks", [
        "The chart has no income tax account at all, neither an expense nor a payable: the accounts named for taxes "
        "are sales tax and payroll taxes. A company like Charles River would need one, or evidence that it does not "
        "pay income tax (Requirement 9).",
        "Several unused accounts each lead to a later requirement: 2080 Interest Payable (interest accrued at the "
        "year-end, Requirement 4), 2120 Lease Liability and 1140 Leasehold Improvements (rent paid from cash while no "
        "lease is recorded, Requirement 9), 1030 Allowance for Doubtful Accounts (the allowance, Requirement 5), and "
        "7010 Interest Income (no interest on more than eight million of cash, Requirement 9)."], last_col=5)
    widths(ws, {"A": 52, "B": 19, "C": 19, "D": 19, "E": 30, "F": 40})
    documentation(b)


def checks_r1(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 1"
    m1, f1 = facts("m1"), facts("r1")
    b.check(e, "data run through (Documentation)", serial(_data_through()), "=DataThrough", 0, DATE)
    for k, y in enumerate((F, P, C)):
        rec = m1["rec"][k]
        b.check(e, f"accounts in the trial balance at {ye(y)}", rec["n"], f"=TB{y}_Accounts", 0, COUNT)
        b.check(e, f"accounts at zero at {ye(y)}", rec["zero"], f"=TB{y}_Zero", 0, COUNT)
        b.check(e, f"debit balances at {ye(y)}", rec["debits"], f"=TB{y}_Debits")
        b.check(e, f"credit balances at {ye(y)}", rec["credits"], f"=TB{y}_Credits")
        b.check(e, f"recorded net income {y}", m1["ni"][k], f"=RecNI_{y}")
        b.check(e, f"close to retained earnings at {ye(y)}", m1["ni"][k], f"=CloseToRE_{y}")
        b.check(e, f"recorded total assets at {ye(y)}", rec["ta"], f"=RecTA_{y}")
        b.check(e, f"recorded current assets at {ye(y)}", rec["ca"], f"=RecCA_{y}")
        b.check(e, f"recorded current liabilities at {ye(y)}", rec["cl"], f"=RecCL_{y}")
        b.check(e, f"notes payable (2110) at {ye(y)}", rec["notes"], f"=RecNotes_{y}")
        b.check(e, f"retained earnings before the close at {ye(y)}", rec["re"], f"=RecRE_{y}")
        b.check(e, f"common stock at {ye(y)}", rec["stock"], f"=RecStock_{y}")
    rows = b.found["recorded_rows"]
    labels = [("opr", "Operating revenue"), ("ret", "Sales returns and allowances"), ("net_rev", "Net revenue"),
              ("cogs", "Cost of goods sold"), ("gm", "Gross margin"), ("opx", "Operating expenses"),
              ("op", "Operating income"), ("intr", "Interest expense"), ("loss", "Loss on disposal of equipment"),
              ("ni", "Net income")]
    for k, y in enumerate((P, C)):
        inc = f1["inc"][k]
        c = "CD"[k]
        for key, line in labels:
            value = -inc[key] if key == "loss" else inc[key]
            b.check(e, f"recorded {line.lower()} {y} (Recorded!{c}{rows[line]})", value, f"=Recorded!{c}{rows[line]}")
    b.check(e, "Chapter 6's pre-closing trial balance less the workbook's", 0, "=Ch6Difference")
    b.check(e, "Chapter 6's net income less the workbook's", 0, "=Ch6NIDifference")
    b.check(e, "trial balances out of balance (three year-ends)", 0, "=TBDifference")
    b.check(e, "recorded balance sheets out of balance (three year-ends)", 0, "=BSDifference")
    b.check(e, "net income less the close to retained earnings (three years)", 0, "=CloseDifference")
    b.check(e, "accounts never posted", f1["n_never"], "=NeverPosted", 0, COUNT)
    b.check(e, "never posted and active", f1["n_active"], "=NeverActive", 0, COUNT)
    b.check(e, "never posted and inactive", f1["n_inactive"], "=NeverInactive", 0, COUNT)
    b.check(e, "accounts named for income tax", 0, "=IncomeTaxAccounts", 0, COUNT)


def _data_through() -> str:
    d = data()
    marks = ",".join("?" * len(DATA_SOURCES))
    return min(day for _, day in d.q(f"SELECT SourceDocumentType, MAX(PostingDate) FROM GLEntry "
                                     f"WHERE SourceDocumentType IN ({marks}) GROUP BY 1", *DATA_SOURCES))


# --- Requirement 2: the review before adjusting ----------------------------------------------------------------------

def load_fixed_assets(b: ExerciseBuild) -> None:
    def acct(key: str, new: str) -> list[tuple[str, str]]:
        return [(f"Merged {new}", f'Table.NestedJoin({{prev}}, {{"{key}"}}, ChartOfAccounts, {{"AccountID"}}, '
                                  f'"{new}", JoinKind.LeftOuter)'),
                (f"Expanded {new}", f'Table.ExpandTableColumn({{prev}}, "{new}", {{"AccountNumber"}}, {{"{new}"}})')]
    loaded(b, "FixedAssets", nav(b, 40, "FixedAsset", extra=[
        ("Removed Other Columns", pq.select_columns(["FixedAssetID", "AssetCode", "AssetDescription", "AssetCategory",
                                                     "AssetAccountID", "AccumulatedDepreciationAccountID",
                                                     "DepreciationDebitAccountID", "InServiceDate", "UsefulLifeMonths",
                                                     "OriginalCost", "OpeningAccumulatedDepreciation", "ResidualValue",
                                                     "Status", "DisposalDate"])),
        *acct("AssetAccountID", "AssetAccount"), *acct("AccumulatedDepreciationAccountID", "ContraAccount"),
        *acct("DepreciationDebitAccountID", "ExpenseAccount"),
        ("Changed Type1", date_types(["InServiceDate", "DisposalDate"])),
        ("Sorted Rows", 'Table.Sort({prev},{{"AssetCode", Order.Ascending}})')]),
        "Fixed Assets", "T40_FixedAsset, the property register, with its account numbers",
        {"InServiceDate": DATE, "DisposalDate": DATE, "OriginalCost": MONEY, "OpeningAccumulatedDepreciation": MONEY})


QUESTIONS = [
    ("Why did 2040 Accrued Expenses grow, and which of its accruals are still owed?", "2040", "Requirement 3"),
    ("Was revenue recorded in the year of delivery, and is any December shipment unbilled?", "4010-4040, 1020",
     "Requirement 4"),
    ("Is the payroll of each year's last days, paid in January, missing at every year-end?", "2030-2033, 1090",
     "Requirement 4"),
    ("Is interest on the notes accrued at the year-ends? (2080 has never been used)", "2080, 7030", "Requirement 4"),
    ("Why does 1090 carry a credit balance inside current assets?", "1090, 1046", "Requirement 5"),
    ("Is an allowance for credit losses needed? (1030 is unused)", "1030, 1020", "Requirement 5"),
    ("Which part of the notes is due within a year? (all of 2110 is classified long-term)", "2110", "Requirement 5"),
    ("Why does 2050 have no debits except credit memos? Has sales tax ever been remitted?", "2050", "Requirement 9"),
    ("Rent is paid monthly from cash while 2120 and 1140 are unused: are there leases to record?",
     "6070, 6080, 2120, 1140", "Requirement 9"),
    ("There is no income tax account: what is the company's tax status?", "none", "Requirement 9"),
    ("Why does 7010 show no interest income on more than eight million of cash?", "7010, 1010", "Requirement 9"),
    ("Do the opening balances that no document supports (1020, 1050, 2010, 2030, 2040) exist?",
     "1020, 1050, 2010, 2030, 2040", "Requirement 9")]


def r2(b: ExerciseBuild) -> None:
    F, P, C = years()
    load_fixed_assets(b)
    ws = analysis_sheet(b, "Review")
    title(ws, "Reviewing the recorded statements", "Requirement 2. The Review file's matrix and drill-through do this "
                                                   "interactively; this worksheet keeps the results the package needs.")
    ibt = b.found["recorded_rows"]["Income before income taxes"]
    heading(ws, "A4", "The controller's materiality: 5% of income before income taxes, as recorded")
    put(ws, {"B5": f"Fiscal {P}", "C5": f"Fiscal {C}",
             "A6": "Income before income taxes as recorded (no income tax is recorded)",
             "B6": f"=Recorded!C{ibt}", "C6": f"=Recorded!D{ibt}",
             "A7": "Materiality (5%)", "B7": "=ROUND(B6*5%,2)", "C7": "=ROUND(C6*5%,2)",
             "A8": "Clearly trivial (5% of materiality)", "B8": "=ROUND(B7*5%,2)", "C8": "=ROUND(C7*5%,2)"})
    bold(ws, "B5:C5")
    ws.Range("B6:C8").NumberFormat = MONEY
    name(b, f"Materiality_{P}", ws, "B7")
    name(b, f"Materiality_{C}", ws, "C7")
    name(b, f"Trivial_{C}", ws, "C8")

    heading(ws, "A10", f"Changes from {ye(P)} to {ye(C)} above materiality (retained earnings aside)")
    put(ws, {"A11": "AccountNumber", "B11": "AccountName", "C11": "Change, debits less credits",
             "D11": "Change on the normal side", "E11": "Normal balance",
             "A12": (f"=LET(n,WorkingTB[AccountNumber],c,WorkingTB[Recorded{C}]-WorkingTB[Recorded{P}],"
                     f"keep,(n<>3030)*(ABS(c)>Materiality_{C}),"
                     "SORTBY(HSTACK(FILTER(n,keep),FILTER(WorkingTB[AccountName],keep),FILTER(c,keep)),"
                     "FILTER(ABS(c),keep),-1))"),
             "D12": ('=LET(c,CHOOSECOLS(A12#,3),nb,XLOOKUP(CHOOSECOLS(A12#,1),WorkingTB[AccountNumber],'
                     'WorkingTB[NormalBalance]),IF(nb="Credit",-c,c))'),
             "E12": "=XLOOKUP(CHOOSECOLS(A12#,1),WorkingTB[AccountNumber],WorkingTB[NormalBalance])"})
    bold(ws, "A11:E11")
    ws.Range("C12:D40").NumberFormat = MONEY
    note(ws, "A10", "At a year-end a revenue or expense account's balance is that year's activity (the prior close "
                    "zeroed it), so its change is this year's activity less last year's.")
    n_above = len(facts("r2")["above"])
    r = 12 + n_above + 1
    put(ws, {f"A{r}": "Changes above materiality", f"C{r}": "=ROWS(A12#)",
             f"A{r + 1}": "Next largest (account and absolute change)",
             f"B{r + 1}": (f"=LET(n,WorkingTB[AccountNumber],c,ABS(WorkingTB[Recorded{C}]-WorkingTB[Recorded{P}]),"
                           f"keep,(n<>3030)*(c<=Materiality_{C}),TAKE(SORTBY(HSTACK(FILTER(n,keep),FILTER(c,keep)),"
                           "FILTER(c,keep),-1),2))"),
             f"A{r + 3}": "Retained earnings moves by the prior year's net income, closed into it",
             f"C{r + 3}": (f"=-(SUMIFS(WorkingTB[Recorded{C}],WorkingTB[AccountNumber],3030)-"
                           f"SUMIFS(WorkingTB[Recorded{P}],WorkingTB[AccountNumber],3030))"),
             f"D{r + 3}": f"=RecNI_{P}"})
    ws.Range(f"C{r}").NumberFormat = COUNT
    ws.Range(f"B{r + 1}:B{r + 2}").NumberFormat = "0"
    ws.Range(f"C{r + 1}:D{r + 3}").NumberFormat = MONEY
    name(b, "ChangesAbove", ws, f"C{r}")
    b.found["next_row"] = r + 1
    b.found["re_row"] = r + 3

    r += 5
    heading(ws, f"A{r}", "Balances that rest on the opening entry (EntryType Opening)")
    put(ws, {f"A{r + 1}": "AccountNumber", f"B{r + 1}": "AccountName", f"C{r + 1}": "Opening line, debits less credits",
             f"D{r + 1}": f"Balance at {ye(C)}", f"E{r + 1}": "Other postings (rows)", f"F{r + 1}": "Other postings, net",
             f"A{r + 2}": ('=LET(n,UNIQUE(FILTER(LedgerSummary[AccountNumber],LedgerSummary[EntryType]="Opening")),'
                           'HSTACK(n,XLOOKUP(n,WorkingTB[AccountNumber],WorkingTB[AccountName])))'),
             f"C{r + 2}": (f'=SUMIFS(LedgerSummary[Net],LedgerSummary[AccountNumber],CHOOSECOLS(A{r + 2}#,1),'
                           'LedgerSummary[EntryType],"Opening")'),
             f"D{r + 2}": f"=XLOOKUP(CHOOSECOLS(A{r + 2}#,1),WorkingTB[AccountNumber],WorkingTB[Recorded{C}])",
             f"E{r + 2}": (f'=SUMIFS(LedgerSummary[Rows],LedgerSummary[AccountNumber],CHOOSECOLS(A{r + 2}#,1))-'
                           f'SUMIFS(LedgerSummary[Rows],LedgerSummary[AccountNumber],CHOOSECOLS(A{r + 2}#,1),'
                           'LedgerSummary[EntryType],"Opening")'),
             f"F{r + 2}": (f"=ROUND(SUMIFS(LedgerSummary[Net],LedgerSummary[AccountNumber],CHOOSECOLS(A{r + 2}#,1))-"
                           f"C{r + 2}#,2)")})
    bold(ws, f"A{r + 1}:F{r + 1}")
    lines = data().q("SELECT COUNT(DISTINCT AccountID) FROM GLEntry WHERE VoucherNumber = ? "
                     "AND SourceDocumentType = 'JournalEntry'", ch17().opening_entry(data()))[0][0]
    ws.Range(f"C{r + 2}:D{r + 2 + lines}").NumberFormat = MONEY
    ws.Range(f"F{r + 2}:F{r + 2 + lines}").NumberFormat = MONEY
    ws.Range(f"E{r + 2}:E{r + 2 + lines}").NumberFormat = COUNT
    b.found["opening_row"] = r + 2
    r += 3 + lines
    opening = lambda n: f'SUMIFS(LedgerSummary[Net],LedgerSummary[AccountNumber],{n},LedgerSummary[EntryType],"Opening")'
    put(ws, {f"A{r}": "Opening lines with no document behind them (normal side)",
             f"A{r + 1}": "1050 Prepaid Expenses (its only posting)", f"C{r + 1}": f"={opening(1050)}",
             f"A{r + 2}": "2030 Accrued Payroll (every payroll posting to it nets to zero)", f"C{r + 2}": f"=-{opening(2030)}",
             f"A{r + 3}": "1020 Accounts Receivable", f"C{r + 3}": f"={opening(1020)}",
             f"A{r + 4}": "2010 Accounts Payable", f"C{r + 4}": f"=-{opening(2010)}",
             f"A{r + 5}": "2040 Accrued Expenses", f"C{r + 5}": f"=-{opening(2040)}",
             f"A{r + 6}": "Opening cash (1010), which the opening payables equal to the cent", f"C{r + 6}": f"={opening(1010)}",
             f"A{r + 7}": "Postings to 1050 other than the opening line",
             f"C{r + 7}": ("=SUMIFS(LedgerSummary[Rows],LedgerSummary[AccountNumber],1050)-"
                           'SUMIFS(LedgerSummary[Rows],LedgerSummary[AccountNumber],1050,LedgerSummary[EntryType],"Opening")'),
             f"A{r + 8}": "Net of the postings to 2030 other than the opening line",
             f"C{r + 8}": f"=ROUND(SUMIFS(LedgerSummary[Net],LedgerSummary[AccountNumber],2030)-{opening(2030)},2)",
             f"A{r + 9}": "Postings to 1110 (a single posting)",
             f"C{r + 9}": "=SUMIFS(LedgerSummary[Rows],LedgerSummary[AccountNumber],1110)",
             f"A{r + 10}": "The register's asset on 1110, its cost, and the ledger balance",
             f"B{r + 10}": '=TEXTJOIN(", ",TRUE,FILTER(FixedAssets[AssetCode],FixedAssets[AssetAccount]=1110))',
             f"C{r + 10}": "=SUMIFS(FixedAssets[OriginalCost],FixedAssets[AssetAccount],1110)",
             f"D{r + 10}": f"=SUMIFS(WorkingTB[Recorded{C}],WorkingTB[AccountNumber],1110)",
             f"A{r + 11}": f"Growth of 2040 Accrued Expenses in {C} (credit)",
             f"C{r + 11}": (f"=-(SUMIFS(WorkingTB[Recorded{C}],WorkingTB[AccountNumber],2040)-"
                            f"SUMIFS(WorkingTB[Recorded{P}],WorkingTB[AccountNumber],2040))"),
             f"A{r + 12}": f"1090 Manufacturing Cost Clearing at {ye(C)}, inside current assets",
             f"C{r + 12}": f"=SUMIFS(WorkingTB[Recorded{C}],WorkingTB[AccountNumber],1090)"})
    bold(ws, f"A{r}")
    ws.Range(f"C{r + 1}:D{r + 12}").NumberFormat = MONEY
    ws.Range(f"C{r + 7}").NumberFormat = COUNT
    ws.Range(f"C{r + 9}").NumberFormat = COUNT
    for k, nm in enumerate(["Open1050", "Open2030", "Open1020", "Open2010", "Open2040", "Open1010", "Other1050",
                            "Other2030", "Posts1110", "Register1110", "Grew2040", "Balance1090"], start=1):
        name(b, nm, ws, f"C{r + k}")
    name(b, "Ledger1110", ws, f"D{r + 10}")
    r += 14
    heading(ws, f"A{r}", f"{MA}: the Questions table (the Review file keeps it, entered with Enter data)")
    range_table(ws, f"A{r + 1}", ["Question", "Accounts", "Answered by"], [list(x) for x in QUESTIONS], "QuestionsModel")
    ws.Range(f"A{r + 2}:A{r + 1 + len(QUESTIONS)}").WrapText = True
    widths(ws, {"A": 70, "B": 40, "C": 22, "D": 22, "E": 16, "F": 18})
    documentation(b)


def checks_r2(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 2"
    f = facts("r2")
    b.check(e, f"materiality {C}", f["mat_c"], f"=Materiality_{C}")
    b.check(e, f"materiality {P}", f["mat_p"], f"=Materiality_{P}")
    b.check(e, "changes above materiality", len(f["above"]), "=ChangesAbove", 0, COUNT)
    for k, a in enumerate(f["above"]):
        b.check(e, f"change {k + 1}: account", int(a["n"]), f"=INDEX(Review!A12#,{k + 1},1)", 0, "0")
        b.check(e, f"change {k + 1}: account {a['n']} on its normal side", a["v"], f"=INDEX(Review!D12#,{k + 1})")
    nr = b.found["next_row"]
    for k, a in enumerate(f["following"]):
        b.check(e, f"next largest {k + 1}: account", int(a["n"]), f"=INDEX(Review!B{nr}#,{k + 1},1)", 0, "0")
        b.check(e, f"next largest {k + 1}: account {a['n']}", a["v"], f"=INDEX(Review!B{nr}#,{k + 1},2)")
    b.check(e, f"retained earnings change less {P} net income", 0,
            f"=ROUND(Review!C{b.found['re_row']}-Review!D{b.found['re_row']},2)")
    for nm, key in (("Open1050", "prepaid"), ("Open2030", "payroll"), ("Open1020", "receivable"),
                    ("Open2010", "payable"), ("Open2040", "accrued")):
        b.check(e, f"opening line of {nm[4:]}", f[key], f"={nm}")
    b.check(e, "opening payables less opening cash", 0, "=ROUND(Open2010-Open1010,2)")
    b.check(e, "postings to 1050 besides the opening line", 0, "=Other1050", 0, COUNT)
    b.check(e, "net of the other postings to 2030", 0, "=Other2030")
    b.check(e, "postings to 1110", 1, "=Posts1110", 0, COUNT)
    b.check(e, f"register asset on 1110 ({f['asset']}), cost", f["asset_cost"], "=Register1110")
    b.check(e, "register cost less the 1110 balance", 0, "=ROUND(Register1110-Ledger1110,2)")
    b.check(e, f"growth of 2040 in {C}", f["grew"], "=Grew2040")
    b.check(e, f"1090 at {ye(C)} (a credit balance)", xr(ch17().bal(data(), ["1090"], ye(C))), "=Balance1090")


# --- Requirement 3: Accrued Expenses rebuilt from its postings ----------------------------------------------------

def load_accruals(b: ExerciseBuild) -> None:
    connection_only(b, "PurchaseInvoiceLines", nav(b, 38, "PurchaseInvoiceLine",
                                                   corrections={"AccrualJournalEntryID": "Int64.Type"}, extra=[
        ("Removed Other Columns", pq.select_columns(["PILineID", "PurchaseInvoiceID", "AccrualJournalEntryID",
                                                     "LineTotal"])),
        ("Filtered Rows", pq.select_rows("[AccrualJournalEntryID] <> null"))]),
        "T38_PurchaseInvoiceLine, the invoice lines that refer to an accrual")
    loaded(b, "AccrualClearing", nav(b, 3, "GLEntry", corrections={"SourceLineID": "Int64.Type"}, extra=[
        ("Removed Other Columns", pq.select_columns(["GLEntryID", "PostingDate", "AccountID", "Debit", "VoucherNumber",
                                                     "SourceDocumentType", "SourceLineID"])),
        ("Filtered Rows", pq.select_rows('[SourceDocumentType] = "PurchaseInvoice" and [Debit] > 0')),
        ("Merged Queries", pq.merge("ChartOfAccounts", "AccountID", "AccountID", "ChartOfAccounts")),
        ("Expanded ChartOfAccounts", pq.expand("ChartOfAccounts", ["AccountNumber"])),
        ("Filtered Rows1", pq.select_rows("[AccountNumber] = 2040")),
        ("Merged Queries1", pq.merge("PurchaseInvoiceLines", "SourceLineID", "PILineID", "PurchaseInvoiceLines")),
        ("Expanded PurchaseInvoiceLines", pq.expand("PurchaseInvoiceLines", ["AccrualJournalEntryID", "LineTotal"])),
        ("Merged Queries2", pq.merge("JournalEntries", "AccrualJournalEntryID", "JournalEntryID", "JournalEntries")),
        ("Expanded JournalEntries", 'Table.ExpandTableColumn({prev}, "JournalEntries", {"EntryNumber", "PostingDate"}, '
                                    '{"AccrualEntryNumber", "AccrualDate"})'),
        ("Added Excess", 'Table.AddColumn({prev}, "Excess", each [LineTotal] - [Debit], type number)'),
        ("Inserted Year", 'Table.AddColumn({prev}, "Year", each Date.Year([PostingDate]), Int64.Type)'),
        ("Changed Type1", date_types(["PostingDate", "AccrualDate"])),
        ("Sorted Rows", 'Table.Sort({prev},{{"AccrualEntryNumber", Order.Ascending}})')]),
        "Accrual Clearing", "T3_GLEntry (Transform Data): the supplier-invoice debits to 2040, each with the accrual "
                            "its invoice line refers to (AccrualJournalEntryID) and the excess charged to expense",
        {"PostingDate": DATE, "AccrualDate": DATE, "Debit": MONEY, "LineTotal": MONEY, "Excess": MONEY})
    loaded(b, "ShipmentFreight", nav(b, 14, "Shipment", extra=[
        ("Removed Other Columns", pq.select_columns(["ShipmentDate", "FreightCost"])),
        ("Added YearMonth", 'Table.AddColumn({prev}, "YearMonth", each Date.ToText(Date.From([ShipmentDate]), "yyyy-MM"), '
                            'type text)'),
        ("Grouped Rows", 'Table.Group({prev}, {"YearMonth"}, {{"Shipments", each Table.RowCount(_), Int64.Type}, '
                         '{"Freight", each List.Sum([FreightCost]), type number}})'),
        ("Sorted Rows", 'Table.Sort({prev},{{"YearMonth", Order.Ascending}})')]),
        "Freight", "T14_Shipment: the freight accrued on shipments (FreightCost, which each shipment credits to 2040), "
                   "by month", {"Freight": MONEY})


def r3(b: ExerciseBuild) -> None:
    F, P, C = years()
    load_accruals(b)
    ws = analysis_sheet(b, "Accrued Expenses")
    title(ws, "Rebuilding 2040 Accrued Expenses at each year-end", "Requirement 3. The opening line, the freight "
          "accrued on shipments and not yet settled, and the service accruals not yet cleared, aged against the "
          "longest wait observed.")
    L = 72                                   # first row of the accrual list
    cols = {"entry": "A", "date": "B", "account": "C", "amount": "D", "first": "E", "lag": "F"}
    ycols = {F: ("G", "H", "I"), P: ("J", "K", "L"), C: ("M", "N", "O")}           # open, age, class
    acc = f"{cols['entry']}{L}#"

    # the composition at each year-end
    put(ws, {"A4": "Composition of 2040 (credit balances)", "B4": ye(F), "C4": ye(P), "D4": ye(C)})
    bold(ws, "A4:D4")
    labels = ["Opening line (JE of 1 January, no document)", "Freight accrued on shipments to date",
              "Freight settled to date (Freight Settlement entries)", "Freight not yet settled",
              "  of which December's freight", "  of which estimates above settlements",
              "Service accruals open, within the clearing window", "Service accruals open, older than the window",
              "  number of old accruals", "Total", "2040 in the trial balance", "Total less the ledger"]
    for k, text in enumerate(labels):
        ws.Cells(5 + k, 1).Value = text
    for y, c in zip((F, P, C), "BCD"):
        o, a, kl = ycols[y]
        put(ws, {f"{c}5": '=-SUMIFS(LedgerSummary[Net],LedgerSummary[AccountNumber],2040,LedgerSummary[EntryType],"Opening")',
                 f"{c}6": (f'=SUMIFS(LedgerSummary[Credit],LedgerSummary[AccountNumber],2040,'
                           f'LedgerSummary[SourceDocumentType],"Shipment",LedgerSummary[Year],"<="&YEAR(YE_{y}))'),
                 f"{c}7": (f'=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],2040,'
                           f'LedgerSummary[EntryType],"Freight Settlement",LedgerSummary[Year],"<="&YEAR(YE_{y}))'),
                 f"{c}8": f"=ROUND({c}6-{c}7,2)",
                 f"{c}9": f'=ROUND(SUMIFS(ShipmentFreight[Freight],ShipmentFreight[YearMonth],YEAR(YE_{y})&"-12"),2)',
                 f"{c}10": f"=ROUND({c}8-{c}9,2)",
                 f"{c}11": f'=ROUND(SUMIFS({o}{L}#,{kl}{L}#,"Young"),2)',
                 f"{c}12": f'=ROUND(SUMIFS({o}{L}#,{kl}{L}#,"Old"),2)',
                 f"{c}13": f'=COUNTIFS({kl}{L}#,"Old")',
                 f"{c}14": f"={c}5+{c}8+{c}11+{c}12",
                 f"{c}15": f"=-SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],2040)",
                 f"{c}16": f"=ROUND({c}14-{c}15,2)"})
        for nm, row in (("Open2040", 5), ("Freight", 8), ("December", 9), ("FreightExcess", 10), ("Young", 11),
                        ("Old", 12), ("OldCount", 13), ("Total2040", 14), ("Diff2040", 16)):
            name(b, f"{nm}_{y}", ws, f"{c}{row}")
    ws.Range("B5:D16").NumberFormat = MONEY
    ws.Range("B13:D13").NumberFormat = COUNT
    bold(ws, "A14:D14")

    # the populations and the clearing lag
    put(ws, {"F4": "Populations", "G4": "Count", "H4": "Amount",
             "F5": "Accrual entries (credits to 2040)",
             "G5": '=COUNTIFS(LedgerSummary[EntryType],"Accrual",LedgerSummary[AccountNumber],2040)',
             "H5": '=SUMIFS(LedgerSummary[Credit],LedgerSummary[EntryType],"Accrual",LedgerSummary[AccountNumber],2040)',
             "F6": "Invoice lines that clear an accrual (debits to 2040)",
             "G6": "=ROWS(AccrualClearing[GLEntryID])", "H6": "=SUM(AccrualClearing[Debit])",
             "F7": "Most invoice lines on one accrual", "G7": f"=MAX(COUNTIFS(AccrualClearing[AccrualEntryNumber],{acc}))",
             "F8": "Accrual Adjustment entries (debits to 2040)",
             "G8": '=COUNTIFS(LedgerSummary[EntryType],"Accrual Adjustment",LedgerSummary[AccountNumber],2040)',
             "H8": ('=SUMIFS(LedgerSummary[Debit],LedgerSummary[EntryType],"Accrual Adjustment",'
                    'LedgerSummary[AccountNumber],2040)'),
             "F9": "Accruals they reverse (distinct)",
             "G9": ('=ROWS(UNIQUE(FILTER(LedgerSummary[ReversesEntryNumber],(LedgerSummary[EntryType]="Accrual Adjustment")*'
                    '(LedgerSummary[AccountNumber]=2040))))'),
             "F10": "Freight Settlement entries",
             "G10": '=COUNTIFS(LedgerSummary[EntryType],"Freight Settlement",LedgerSummary[AccountNumber],2040)',
             "H10": ('=SUMIFS(LedgerSummary[Debit],LedgerSummary[EntryType],"Freight Settlement",'
                     'LedgerSummary[AccountNumber],2040)'),
             "F11": "Shipment credits to 2040, all dates",
             "H11": '=SUMIFS(LedgerSummary[Credit],LedgerSummary[AccountNumber],2040,LedgerSummary[SourceDocumentType],"Shipment")',
             "F12": "Freight-out (5050) debits, closes left out",
             "H12": "=SUMIFS(LedgerSummary[Net],LedgerSummary[AccountNumber],5050,LedgerSummary[IsYearEndClose],FALSE)",
             "F14": "Excess of invoices over their accruals, to expense", "G14": ye(F)[:4], "H14": ye(P)[:4], "I14": ye(C)[:4],
             "F15": "Amount", "F16": "Invoice lines",
             "F18": "Clearing lag (accrual date to invoice posting), days", "G18": "Days",
             "F19": "Shortest", "G19": f"=MIN(FILTER({cols['lag']}{L}#,{cols['lag']}{L}#<>\"\"))",
             "F20": "Longest: the clearing window", "G20": f"=MAX(FILTER({cols['lag']}{L}#,{cols['lag']}{L}#<>\"\"))",
             "F21": "Median", "G21": f"=MEDIAN(FILTER({cols['lag']}{L}#,{cols['lag']}{L}#<>\"\"))",
             "F22": "Accruals cleared at exactly the longest lag", "G22": f"=COUNTIFS({cols['lag']}{L}#,G20)"})
    for y, c in zip((F, P, C), "GHI"):
        put(ws, {f"{c}15": f"=SUMIFS(AccrualClearing[Excess],AccrualClearing[Year],{y})",
                 f"{c}16": f'=COUNTIFS(AccrualClearing[Excess],">0.005",AccrualClearing[Year],{y})'})
        name(b, f"Excess_{y}", ws, f"{c}15")
        name(b, f"ExcessLines_{y}", ws, f"{c}16")
    bold(ws, "F4:I4")
    bold(ws, "F14:I14")
    bold(ws, "F18:G18")
    ws.Range("H5:H12").NumberFormat = MONEY
    ws.Range("G15:I15").NumberFormat = MONEY
    ws.Range("G5:G10").NumberFormat = COUNT
    for nm, addr in (("Accruals", "G5"), ("AccrualAmount", "H5"), ("ClearingLines", "G6"), ("ClearedAmount", "H6"),
                     ("MostLines", "G7"), ("Adjustments", "G8"), ("AdjustmentAmount", "H8"), ("AdjTargets", "G9"),
                     ("Settlements", "G10"), ("Settled", "H10"), ("ShippedFreight", "H11"), ("FreightOut", "H12"),
                     ("LagLow", "G19"), ("ClearingWindow", "G20"), ("LagMedian", "G21"), ("AtWindow", "G22")):
        name(b, nm, ws, addr)

    # the old items at the current year-end, and the young items never invoiced
    put(ws, {"A18": f"Old accruals at {ye(C)}", "B18": "Amount", "C18": "Count"})
    bold(ws, "A18:C18")
    r = 19
    for y in (F, P, C):
        put(ws, {f"A{r}": f"Recorded in {y}",
                 f"B{r}": f'=SUMPRODUCT((YEAR(B{L}#)={y})*(O{L}#="Old"),M{L}#)',
                 f"C{r}": f'=SUMPRODUCT((YEAR(B{L}#)={y})*(O{L}#="Old"))'})
        name(b, f"OldFrom_{y}", ws, f"B{r}")
        name(b, f"OldFromCount_{y}", ws, f"C{r}")
        r += 1
    put(ws, {f"A{r}": "Never invoiced", f"B{r}": f'=SUMPRODUCT((O{L}#="Old")*(E{L}#=""),M{L}#)',
             f"C{r}": f'=SUMPRODUCT((O{L}#="Old")*(E{L}#=""))',
             f"A{r + 1}": '"Partial cleanup" adjustments with no invoice',
             f"B{r + 1}": '=TEXTJOIN(", ",TRUE,FILTER(JournalEntries[EntryNumber],LEFT(JournalEntries[Description],15)="Partial cleanup"))',
             f"C{r + 1}": '=ROWS(FILTER(JournalEntries[EntryNumber],LEFT(JournalEntries[Description],15)="Partial cleanup"))'})
    name(b, "OldNeverInvoiced", ws, f"C{r}")
    name(b, "Cleanups", ws, f"C{r + 1}")
    ws.Range(f"B19:B{r}").NumberFormat = MONEY
    r += 3
    put(ws, {f"A{r}": "Young accruals never invoiced", f"B{r}": "Open at that year-end",
             f"C{r}": f"Still open at {ye(C)}", f"D{r}": "Entries"})
    bold(ws, f"A{r}:D{r}")
    for y, (o, a, kl) in ((F, ycols[F]), (P, ycols[P])):
        r += 1
        never = f'({kl}{L}#="Young")*(E{L}#="")'
        put(ws, {f"A{r}": f"Within the window at {ye(y)}", f"B{r}": f"=SUMPRODUCT({never},{o}{L}#)",
                 f"C{r}": f"=SUMPRODUCT({never},M{L}#)",
                 f"D{r}": f'=TEXTJOIN(", ",TRUE,FILTER(A{L}#,{never}))'})
        name(b, f"YoungNever_{y}", ws, f"C{r}")
        ws.Range(f"B{r}:C{r}").NumberFormat = MONEY

    # old accruals by expense account (A3's lines) and the A3 effects
    r += 2
    put(ws, {f"A{r}": "Old accruals by expense account", f"B{r}": ye(F), f"C{r}": ye(P), f"D{r}": ye(C)})
    bold(ws, f"A{r}:D{r}")
    b.found["old_rows"] = {}
    for acct in old_accounts():
        r += 1
        ws.Cells(r, 1).Value = int(acct)
        ws.Cells(r, 1).HorizontalAlignment = -4131
        for y, c in zip((F, P, C), "BCD"):
            o, a, kl = ycols[y]
            ws.Range(f"{c}{r}").Formula2 = f'=SUMIFS({o}{L}#,{kl}{L}#,"Old",C{L}#,{acct})'
        b.found["old_rows"][acct] = r
    r += 1
    put(ws, {f"A{r}": "Total (equals the old accruals above)", f"B{r}": f"=SUM(B{r - len(old_accounts())}:B{r - 1})",
             f"C{r}": f"=SUM(C{r - len(old_accounts())}:C{r - 1})", f"D{r}": f"=SUM(D{r - len(old_accounts())}:D{r - 1})"})
    ws.Range(f"B{r - len(old_accounts())}:D{r}").NumberFormat = MONEY
    for y, c in zip((F, P, C), "BCD"):
        name(b, f"OldByAccount_{y}", ws, f"{c}{r}")
    r += 2
    put(ws, {f"A{r}": "A3: old accruals reversed at each year-end (corrections of errors)",
             f"B{r}": f"Retained earnings, 1 January {P}", f"C{r}": f"Income {P}", f"D{r}": f"Income {C}",
             f"A{r + 1}": "Effect", f"B{r + 1}": f"=Old_{F}", f"C{r + 1}": f"=Old_{P}-Old_{F}", f"D{r + 1}": f"=Old_{C}-Old_{P}"})
    bold(ws, f"A{r}:D{r}")
    ws.Range(f"B{r + 1}:D{r + 1}").NumberFormat = MONEY
    name(b, "AdjA3_RE", ws, f"B{r + 1}")
    name(b, f"AdjA3_{P}", ws, f"C{r + 1}")
    name(b, f"AdjA3_{C}", ws, f"D{r + 1}")

    # the accrual list
    heads = ["EntryNumber", "PostingDate", "ExpenseAccount", "Amount", "FirstInvoiceDate", "LagDays",
             f"Open {F}", f"Age {F}", f"Class {F}", f"Open {P}", f"Age {P}", f"Class {P}", f"Open {C}", f"Age {C}",
             f"Class {C}"]
    heading(ws, f"A{L - 2}", "The accrual entries, what had cleared them by each year-end, and their age")
    for k, h in enumerate(heads, start=1):
        ws.Cells(L - 1, k).Value = h
    bold(ws, f"A{L - 1}:O{L - 1}")
    put(ws, {f"A{L}": '=SORT(FILTER(LedgerSummary[EntryNumber],(LedgerSummary[EntryType]="Accrual")*'
                      '(LedgerSummary[AccountNumber]=2040)))',
             f"B{L}": f"=XLOOKUP({acc},JournalEntries[EntryNumber],JournalEntries[PostingDate])",
             f"C{L}": (f'=XLOOKUP({acc}&"|Expense",LedgerSummary[EntryNumber]&"|"&LedgerSummary[AccountType],'
                       'LedgerSummary[AccountNumber])'),
             f"D{L}": f"=SUMIFS(LedgerSummary[Credit],LedgerSummary[EntryNumber],{acc},LedgerSummary[AccountNumber],2040)",
             f"E{L}": f'=LET(m,MINIFS(AccrualClearing[PostingDate],AccrualClearing[AccrualEntryNumber],{acc}),IF(m=0,"",m))',
             f"F{L}": f'=IF(E{L}#="","",E{L}#-B{L}#)'})
    for y in (F, P, C):
        o, a, kl = ycols[y]
        put(ws, {f"{o}{L}": (f'=IF(B{L}#<=YE_{y},ROUND(D{L}#-SUMIFS(AccrualClearing[Debit],'
                             f'AccrualClearing[AccrualEntryNumber],{acc},AccrualClearing[PostingDate],"<="&YE_{y})-'
                             f'SUMIFS(LedgerSummary[Debit],LedgerSummary[ReversesEntryNumber],{acc},'
                             f'LedgerSummary[AccountNumber],2040,LedgerSummary[EntryDate],"<="&YE_{y}),2),0)'),
                 f"{a}{L}": f"=YE_{y}-B{L}#",
                 f"{kl}{L}": f'=IF({o}{L}#>0.004,IF({a}{L}#>ClearingWindow,"Old","Young"),"")'})
    for c in ("B", "E"):
        ws.Range(f"{c}{L}:{c}{L + 450}").NumberFormat = DATE
    for c in ("D", "G", "J", "M"):
        ws.Range(f"{c}{L}:{c}{L + 450}").NumberFormat = MONEY
    note(ws, f"A{L - 1}", "What cleared each accrual is measured from the ledger's postings, as the case's Watch out "
                          "says: the invoice lines' debits to 2040 (AccrualClearing) and the Accrual Adjustment entries' "
                          "debits to 2040 (LedgerSummary, by the entry each one reverses), dated by each year-end.")
    r = model_answer(ws, r + 3, MA + ": which open accruals are still liabilities", [
        f"The longest wait for an invoice was {facts('r3')['window']} days, and several accruals cleared at exactly "
        f"that lag, so an accrual older than {facts('r3')['window']} days at a year-end is past the invoicing window. "
        "Those accruals should have been reversed at that year-end, because the facts existed then: they are "
        "corrections of errors at each year-end (A3), not changes in estimate. A rule of \"older than the last two "
        "month-ends\" would wrongly flag an accrual that an invoice cleared on the first day of the next year.",
        "An accrual within the window is an estimate; if it later proves unneeded, that is a change in estimate in the "
        f"year it goes stale. Keep the {money(facts('r3')['young_c'])} of young {C} accruals as liabilities, and leave "
        f"the {money(facts('r3')['opening'])} opening line to the memo (Requirement 9). Allocating the old items by "
        "year of origin is acceptable if argued, but it uses hindsight on the November and December items of "
        f"{F} and {P} that it cannot apply to {C}."], last_col=4)
    assert r < L - 2, f"the accrual list must start below row {r}"
    widths(ws, {"A": 46, "B": 15, "C": 15, "D": 15, "E": 15, "F": 44, "G": 14, "H": 15, "I": 12, "J": 13, "K": 9,
                "L": 9, "M": 13, "N": 9, "O": 9})
    documentation(b)


def checks_r3(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 3"
    f = facts("r3")
    acc = ch17().accruals(data())
    b.check(e, "accrual entries", f["n"], "=Accruals", 0, COUNT)
    b.check(e, "accrual entries, amount", f["amount"], "=AccrualAmount")
    b.check(e, "invoice lines that clear an accrual", f["n_lines"], "=ClearingLines", 0, COUNT)
    b.check(e, "cleared through their 2040 debits", f["cleared"], "=ClearedAmount")
    b.check(e, "most invoice lines on one accrual", 1, "=MostLines", 0, COUNT)
    b.check(e, "Accrual Adjustment entries", f["n_adj"], "=Adjustments", 0, COUNT)
    b.check(e, "accruals they reverse", f["targets"], "=AdjTargets", 0, COUNT)
    b.check(e, "Accrual Adjustment entries, amount", f["adj_amount"], "=AdjustmentAmount")
    for k, y in enumerate((F, P, C)):
        b.check(e, f"excess of invoices over accruals to expense, {y}", f["excess"][k], f"=Excess_{y}")
        b.check(e, f"invoice lines with an excess, {y}", f["excess_lines"][k], f"=ExcessLines_{y}", 0, COUNT)
    b.check(e, "clearing lag, shortest (days)", f["lag_low"], "=LagLow", 0, COUNT)
    b.check(e, "clearing lag, longest (days): the window", f["window"], "=ClearingWindow", 0, COUNT)
    b.check(e, "clearing lag, median (days)", f["median"], "=LagMedian", 0, COUNT)
    b.check(e, "accruals cleared at exactly the longest lag", acc["lags"].count(acc["window"]), "=AtWindow", 0, COUNT)
    b.check(e, "freight settlements", f["settlements"], "=Settlements", 0, COUNT)
    b.check(e, "freight settled", f["settled"], "=Settled")
    b.check(e, "shipment credits to 2040", f["shipped"], "=ShippedFreight")
    b.check(e, "shipment credits to 2040 less the 5050 debits", 0, "=ROUND(ShippedFreight-FreightOut,2)")
    for k, y in enumerate((F, P, C)):
        c = f["comp"][k]
        b.check(e, f"2040 opening line ({ye(y)})", c["opening"], f"=Open2040_{y}")
        b.check(e, f"freight not yet settled at {ye(y)}", c["freight"], f"=Freight_{y}")
        b.check(e, f"December's freight {y}", c["december"], f"=December_{y}")
        b.check(e, f"freight estimates above settlements at {ye(y)}", c["excess"], f"=FreightExcess_{y}")
        b.check(e, f"open accruals within the window at {ye(y)}", c["young"], f"=Young_{y}")
        b.check(e, f"open accruals older than the window at {ye(y)}", c["old"], f"=Old_{y}")
        b.check(e, f"number of old accruals at {ye(y)}", c["n_old"], f"=OldCount_{y}", 0, COUNT)
        b.check(e, f"2040 rebuilt at {ye(y)}", c["total"], f"=Total2040_{y}")
        b.check(e, f"2040 rebuilt less the ledger at {ye(y)}", 0, f"=Diff2040_{y}")
        b.check(e, f"old accruals by expense account add up at {ye(y)}", c["old"], f"=OldByAccount_{y}")
    for y, v, k in f["by_year"]:
        b.check(e, f"old accruals at {ye(C)} recorded in {y}", v, f"=OldFrom_{y}")
        b.check(e, f"old accruals at {ye(C)} recorded in {y}, count", k, f"=OldFromCount_{y}", 0, COUNT)
    b.check(e, f"old accruals at {ye(C)} never invoiced (count)", f["n_old"], "=OldNeverInvoiced", 0, COUNT)
    b.check(e, '"Partial cleanup" adjustments', f["cleanups"], "=Cleanups", 0, COUNT)
    for acct, v in f["by_account"]:
        b.check(e, f"old accruals at {ye(C)}, account {acct}", v, f"='Accrued Expenses'!D{b.found['old_rows'][acct]}")
    b.check(e, f"young accruals at {ye(F)} never invoiced", f["young_f"]["left"], f"=YoungNever_{F}")
    b.check(e, f"young accruals at {ye(P)} never invoiced, still open at {ye(C)}", f["young_p"]["left"], f"=YoungNever_{P}")
    b.check(e, f"A3 effect on retained earnings at 1 January {P}", f["a3"]["re"], "=AdjA3_RE")
    b.check(e, f"A3 effect on {P} income", f["a3"]["P"], f"=AdjA3_{P}")
    b.check(e, f"A3 effect on {C} income", f["a3"]["C"], f"=AdjA3_{C}")


# --- Requirement 4: cutoff at each year-end ------------------------------------------------------------------------

def sql_results(b: ExerciseBuild):
    """The SQL Results worksheet, and the next free row on it."""
    if "sql_row" not in b.found:
        ws = data_sheet(b, "SQL Results")
        title(ws, "Query results pasted from LenderPackage.sql",
              "Each Table is a query's result pasted with Copy with Headers; its header carries a note naming the query.")
        b.found["sql_row"] = 4
        b.found.setdefault("data_sheets", {})["SQL Results"] = DESCRIBE["SQL Results"]
    return b.wb.Worksheets("SQL Results"), b.found["sql_row"]


def paste_inputs_r4(b: ExerciseBuild) -> None:
    ws, r = sql_results(b)
    groups = cutoff_groups()
    rows = []
    for i in late_invoices():
        rows.append([i["number"], serial(i["date"]), serial(i["posted"]), serial(i["delivered"]), i["segment"], i["sub"],
                     i["tax"], i["freight"]]
                    + [i["groups"].get(g, 0.0) for g in groups])
    heading(ws, f"A{r}", "Test L5: invoices posted in another year than the latest delivery of the goods they bill")
    lo = pasted(b, ws, f"A{r + 1}", ["InvoiceNumber", "InvoiceDate", "PostingDate", "DeliveryDate", "CustomerSegment",
                                     "SubTotal", "TaxAmount", "FreightAmount"] + groups, rows, "LateInvoices",
                "invoices posted in another year than the latest delivery they bill (test L5: the latest DeliveryDate "
                "of each invoice's shipments against the year of its first posting), with SubTotal, tax, freight, and "
                "the line totals by item group",
                {**{c: DATE for c in ("InvoiceDate", "PostingDate", "DeliveryDate")},
                 **{c: MONEY for c in ["SubTotal", "TaxAmount", "FreightAmount"] + groups}})
    xl.add_column(lo, "DeliveryYear", "=YEAR([@DeliveryDate])", "0")
    xl.add_column(lo, "PostingYear", "=YEAR([@PostingDate])", "0")
    r += len(rows) + 4
    heading(ws, f"A{r}", "Test L6: shipment lines never invoiced")
    rows = [[k, sn, serial(sd), serial(dd), code, g, seg, qty, price, disc, std, value]
            for k, sn, sd, dd, code, g, seg, qty, price, disc, std, value in unbilled_lines()]
    lo = pasted(b, ws, f"A{r + 1}", ["ShipmentLineID", "ShipmentNumber", "ShipmentDate", "DeliveryDate", "ItemCode",
                                     "ItemGroup", "CustomerSegment", "QuantityShipped", "UnitPrice", "Discount",
                                     "ExtendedStandardCost", "Value"], rows, "UnbilledLines",
                "shipment lines with no invoice line (test L6: ShipmentLine LEFT JOIN SalesInvoiceLine), with the order "
                "line's UnitPrice and Discount and their value, ROUND(QuantityShipped * UnitPrice * (1 - Discount), 2)",
                {"ShipmentDate": DATE, "DeliveryDate": DATE, "UnitPrice": MONEY, "ExtendedStandardCost": MONEY,
                 "Discount": "0.00", "Value": MONEY})
    xl.add_column(lo, "DeliveryYear", "=YEAR([@DeliveryDate])", "0")
    xl.add_column(lo, "ValueHalfUp", "=ROUND([@QuantityShipped]*[@UnitPrice]*(1-[@Discount]),2)", MONEY)
    xl.add_column(lo, "RoundingDifference", "=ROUND([@ValueHalfUp]-[@Value],2)", MONEY)
    note(ws, f"L{r + 1}", "Value is the query's: SQLite's ROUND works on the binary double, so a product that is exactly "
                          "half a cent can round down (shipment line 27337: 12.25 x 843.86 = 10,337.285 gives 10,337.28). "
                          "Excel's ROUND, and the dataset's own LineTotal (10,337.29 on that order line), round half up. "
                          "The package uses the query's value, as LenderPackage.sql returns it; ValueHalfUp shows the "
                          "difference.")
    r += len(rows) + 4
    heading(ws, f"A{r}", "The revenue account of each item group")
    accounts = ch17().revenue_accounts(data())
    rows = [[g, int(accounts[g])] for g in GROUP_ORDER + sorted(set(accounts) - set(GROUP_ORDER)) if g in accounts]
    pasted(b, ws, f"A{r + 1}", ["ItemGroup", "RevenueAccount"], rows, "GroupAccounts",
           "the revenue account each item group's invoice lines are credited to (GLEntry SalesInvoice rows joined to "
           "their invoice line and item)")
    r += len(rows) + 4
    heading(ws, f"A{r}", "The account each cost center's gross pay is debited to")
    rows = [[c, int(a)] for c, a in payroll_accounts()]
    lo = pasted(b, ws, f"A{r + 1}", ["CostCenterName", "PayrollAccount"], rows, "PayrollAccounts",
                "the account each cost center's gross pay is debited to (PayrollSummary debits other than 6060, the "
                "employer taxes and benefits of the cost centers outside manufacturing)")
    xl.add_column(lo, "AdjustmentAccount", "=IF([@PayrollAccount]=1090,5080,[@PayrollAccount])", "0")
    note(ws, f"C{r + 1}", "Manufacturing payroll is debited to 1090; with no completion to absorb the accrued part, it "
                          "ends in 5080 Manufacturing Variance and cost of goods sold, so the adjustment posts it there.")
    b.found["sql_row"] = r + len(rows) + 4
    ws.Columns("A:N").AutoFit()


def load_payroll(b: ExerciseBuild) -> None:
    connection_only(b, "CostCenters", nav(b, 75, "CostCenter", extra=[
        ("Removed Other Columns", pq.select_columns(["CostCenterID", "CostCenterName"]))]), "T75_CostCenter")
    loaded(b, "PayrollPeriods", nav(b, 59, "PayrollPeriod", extra=[
        ("Removed Other Columns", pq.select_columns(["PayrollPeriodID", "PeriodNumber", "PeriodStartDate",
                                                     "PeriodEndDate", "PayDate", "FiscalYear", "Status"])),
        ("Changed Type1", date_types(["PeriodStartDate", "PeriodEndDate", "PayDate"]))]),
        "Pay Periods", "T59_PayrollPeriod", {"PeriodStartDate": DATE, "PeriodEndDate": DATE, "PayDate": DATE})
    loaded(b, "PayrollCost", nav(b, 69, "PayrollRegister", extra=[
        ("Removed Other Columns", pq.select_columns(["PayrollPeriodID", "CostCenterID", "GrossPay", "EmployerPayrollTax",
                                                     "EmployerBenefits"])),
        ("Grouped Rows", 'Table.Group({prev}, {"PayrollPeriodID", "CostCenterID"}, {{"Registers", each Table.RowCount(_), '
                         'Int64.Type}, {"GrossPay", each List.Sum([GrossPay]), type number}, {"EmployerPayrollTax", '
                         'each List.Sum([EmployerPayrollTax]), type number}, {"EmployerBenefits", each '
                         'List.Sum([EmployerBenefits]), type number}})'),
        ("Added Cost", pq.add_custom("Cost", "[GrossPay] + [EmployerPayrollTax] + [EmployerBenefits]")),
        ("Merged Queries", pq.merge("CostCenters", "CostCenterID", "CostCenterID", "CostCenters")),
        ("Expanded CostCenters", pq.expand("CostCenters", ["CostCenterName"])),
        ("Changed Type1", pq.transform_types([("Cost", "type number")])),
        ("Sorted Rows", 'Table.Sort({prev},{{"PayrollPeriodID", Order.Ascending}, {"CostCenterID", Order.Ascending}})')]),
        "Payroll", "T69_PayrollRegister by pay period and cost center: gross pay, employer taxes, benefits",
        {"GrossPay": MONEY, "EmployerPayrollTax": MONEY, "EmployerBenefits": MONEY, "Cost": MONEY})
    loaded(b, "WorkingDays", nav(b, 48, "WorkCenterCalendar", extra=[
        ("Removed Other Columns", pq.select_columns(["WorkCenterID", "CalendarDate", "IsWorkingDay"])),
        ("FirstWorkCenter", "List.Min({prev}[WorkCenterID])"),
        ("Filtered Rows", 'Table.SelectRows(#"Removed Other Columns", each [WorkCenterID] = FirstWorkCenter)'),
        ("Changed Type1", date_types(["CalendarDate"]))]),
        "Calendar", "T48_WorkCenterCalendar of the first work center (every work center has the same working days)",
        {"CalendarDate": DATE})


def load_debt(b: ExerciseBuild) -> None:
    loaded(b, "DebtAgreements", nav(b, 42, "DebtAgreement", corrections={"PrincipalAmount": "type number"}, extra=[
        ("Removed Other Columns", pq.select_columns(["DebtAgreementID", "AgreementNumber", "FixedAssetID",
                                                     "OriginationDate", "PrincipalAmount", "AnnualInterestRate",
                                                     "TermMonths", "PaymentStartDate", "ScheduledPaymentAmount",
                                                     "Status"])),
        ("Merged Queries", pq.merge("FixedAssets", "FixedAssetID", "FixedAssetID", "FixedAssets")),
        ("Expanded FixedAssets", pq.expand("FixedAssets", ["AssetCode"])),
        ("Changed Type1", date_types(["OriginationDate", "PaymentStartDate"]))]),
        "Debt", "T42_DebtAgreement with the asset each note is linked to",
        {"OriginationDate": DATE, "PaymentStartDate": DATE, "PrincipalAmount": MONEY, "ScheduledPaymentAmount": MONEY,
         "AnnualInterestRate": "0.00%"})
    lo = xl.table(b.wb, "DebtAgreements")
    ws = lo.Range.Worksheet
    xl.add_query(b.wb, "DebtSchedule", nav(b, 43, "DebtScheduleLine", extra=[
        ("Removed Other Columns", pq.select_columns(["DebtScheduleLineID", "DebtAgreementID", "PaymentSequence",
                                                     "PaymentDate", "BeginningPrincipal", "PrincipalAmount",
                                                     "InterestAmount", "PaymentAmount", "EndingPrincipal",
                                                     "JournalEntryID", "Status"])),
        ("Changed Type1", date_types(["PaymentDate"])),
        ("Sorted Rows", 'Table.Sort({prev},{{"DebtAgreementID", Order.Ascending}, {"PaymentDate", Order.Ascending}})')]),
        "T43_DebtScheduleLine")
    b.found.setdefault("queries", []).append(("DebtSchedule", "T43_DebtScheduleLine, the payment schedule of each note"))
    sched = load_to(b.wb, "DebtSchedule", ws, f"A{lo.Range.Rows.Count + 4}")
    for c in ("BeginningPrincipal", "PrincipalAmount", "InterestAmount", "PaymentAmount", "EndingPrincipal"):
        sched.ListColumns(c).DataBodyRange.NumberFormat = MONEY
    sched.ListColumns("PaymentDate").DataBodyRange.NumberFormat = DATE


def r4(b: ExerciseBuild) -> None:
    F, P, C = years()
    paste_inputs_r4(b)
    load_payroll(b)
    load_debt(b)
    ws = analysis_sheet(b, "Cutoff")
    title(ws, "Cutoff at each year-end", "Requirement 4. Queries find the populations; the proration is done here, in "
                                         "formulas a reviewer can see. One method at every year-end.")
    yc = list(zip((F, P, C), "BCD"))
    # revenue
    put(ws, {"A4": "Revenue: recognized in the year of delivery", "B4": ye(F), "C4": ye(P), "D4": ye(C)})
    bold(ws, "A4:D4")
    rows = ["Invoices for the year's deliveries, posted the next year", "  their SubTotal",
            "Shipment lines delivered in the year, never invoiced", "  their value at order price less discount",
            "Revenue that belongs to the year, recorded later or never", "Sales tax on those invoices (not adjusted)",
            "Freight billed on those invoices", "Standard cost of the lines never invoiced (already in cost of goods sold)"]
    for k, t in enumerate(rows):
        ws.Cells(5 + k, 1).Value = t
    for y, c in yc:
        put(ws, {f"{c}5": f"=COUNTIFS(LateInvoices[DeliveryYear],{y})",
                 f"{c}6": f"=SUMIFS(LateInvoices[SubTotal],LateInvoices[DeliveryYear],{y})",
                 f"{c}7": f"=COUNTIFS(UnbilledLines[DeliveryYear],{y})",
                 f"{c}8": f"=SUMIFS(UnbilledLines[Value],UnbilledLines[DeliveryYear],{y})",
                 f"{c}9": f"=ROUND({c}6+{c}8,2)",
                 f"{c}10": f"=SUMIFS(LateInvoices[TaxAmount],LateInvoices[DeliveryYear],{y})",
                 f"{c}11": f"=SUMIFS(LateInvoices[FreightAmount],LateInvoices[DeliveryYear],{y})",
                 f"{c}12": f"=SUMIFS(UnbilledLines[ExtendedStandardCost],UnbilledLines[DeliveryYear],{y})"})
        for nm, row in (("LateCount", 5), ("LateAmount", 6), ("UnbilledCount", 7), ("UnbilledValue", 8),
                        ("Cutoff", 9), ("LateTax", 10), ("UnbilledStd", 12)):
            name(b, f"{nm}_{y}", ws, f"{c}{row}")
    ws.Range("B5:D12").NumberFormat = MONEY
    for row in (5, 7):
        ws.Range(f"B{row}:D{row}").NumberFormat = COUNT
    bold(ws, "A9:D9")
    put(ws, {"A13": "Late invoices not posted in the year after delivery",
             "B13": "=SUMPRODUCT(--(LateInvoices[PostingYear]-LateInvoices[DeliveryYear]<>1))"})
    name(b, "LateNotNextYear", ws, "B13")
    segments = sorted({i["segment"] for i in late_invoices()} | {u[6] for u in unbilled_lines()})
    r = 15
    put(ws, {f"A{r}": "By customer segment"})
    bold(ws, f"A{r}")
    b.found["segment_rows"] = {}
    for s in segments:
        r += 1
        ws.Cells(r, 1).Value = s
        for y, c in yc:
            ws.Range(f"{c}{r}").Formula2 = (f'=SUMIFS(LateInvoices[SubTotal],LateInvoices[DeliveryYear],{y},'
                                            f'LateInvoices[CustomerSegment],"{s}")+SUMIFS(UnbilledLines[Value],'
                                            f'UnbilledLines[DeliveryYear],{y},UnbilledLines[CustomerSegment],"{s}")')
        b.found["segment_rows"][s] = r
    r += 2
    put(ws, {f"A{r}": "By item group (and its revenue account)"})
    bold(ws, f"A{r}")
    b.found["group_rows"] = {}
    for g in cutoff_groups():
        r += 1
        ws.Cells(r, 1).Value = g
        ws.Cells(r, 5).Formula2 = f'=XLOOKUP("{g}",GroupAccounts[ItemGroup],GroupAccounts[RevenueAccount])'
        for y, c in yc:
            ws.Range(f"{c}{r}").Formula2 = (f'=SUMIFS(LateInvoices[{g}],LateInvoices[DeliveryYear],{y})+'
                                            f'SUMIFS(UnbilledLines[Value],UnbilledLines[DeliveryYear],{y},'
                                            f'UnbilledLines[ItemGroup],"{g}")')
        b.found["group_rows"][g] = r
    ws.Range(f"B16:D{r}").NumberFormat = MONEY
    r += 1
    put(ws, {f"A{r}": "Total by item group (equals the revenue above)"})
    first = min(b.found["group_rows"].values())
    for y, c in yc:
        ws.Range(f"{c}{r}").Formula2 = f"=ROUND(SUM({c}{first}:{c}{r - 1}),2)"
        name(b, f"CutoffByGroup_{y}", ws, f"{c}{r}")
    ws.Range(f"B{r}:D{r}").NumberFormat = MONEY
    r += 2
    put(ws, {f"A{r}": "A2: revenue recognized by delivery date", f"B{r}": f"Retained earnings, 1 January {P}",
             f"C{r}": f"Income {P}", f"D{r}": f"Income {C}",
             f"A{r + 1}": "Effect", f"B{r + 1}": f"=Cutoff_{F}", f"C{r + 1}": f"=Cutoff_{P}-Cutoff_{F}",
             f"D{r + 1}": f"=Cutoff_{C}-Cutoff_{P}"})
    bold(ws, f"A{r}:D{r}")
    ws.Range(f"B{r + 1}:D{r + 1}").NumberFormat = MONEY
    name(b, "AdjA2_RE", ws, f"B{r + 1}")
    name(b, f"AdjA2_{P}", ws, f"C{r + 1}")
    name(b, f"AdjA2_{C}", ws, f"D{r + 1}")

    # payroll
    r += 4
    pr = r
    put(ws, {f"A{r}": "Payroll: the work of each year's last days, paid in the next year", f"B{r}": ye(F),
             f"C{r}": ye(P), f"D{r}": ye(C)})
    bold(ws, f"A{r}:D{r}")
    labels = ["Pay period ending in the year and paid in the next", "  its pay date",
              "Pay period crossing the year-end", "  its first day", "  its last day",
              "  its working days", "  its working days within the year", "  share within the year",
              "Registers of the period paid in the next year (gross pay, employer taxes, benefits)",
              "Registers of the crossing period, times the share",
              "Last eight processed pay periods: first and last", "  their first and last day",
              "  their working days", "  their cost (registers)", "  cost per working day",
              "  working days left in the year after the last processed period",
              "Payroll owed at the year-end", "  gross pay", "  employer payroll taxes", "  employer benefits",
              "  manufacturing (to 1090, ends in 5080)", "  other cost centers (salary accounts and 6060)"]
    for k, t in enumerate(labels, start=1):
        ws.Cells(r + k, 1).Value = t
    wd = lambda a, z: (f'COUNTIFS(WorkingDays[CalendarDate],">="&{a},WorkingDays[CalendarDate],"<="&{z},'
                       'WorkingDays[IsWorkingDay],1)')
    look = lambda pid, field: f"XLOOKUP({pid},PayrollPeriods[PayrollPeriodID],PayrollPeriods[{field}])"
    for y, c in yc[:2]:
        full, cross = f"{c}{r + 1}", f"{c}{r + 3}"
        put(ws, {f"{c}{r + 1}": (f"=XLOOKUP(1,(PayrollPeriods[PeriodEndDate]<=YE_{y})*(PayrollPeriods[PayDate]>YE_{y}),"
                                 "PayrollPeriods[PayrollPeriodID])"),
                 f"{c}{r + 2}": f"={look(full, 'PayDate')}",
                 f"{c}{r + 3}": (f"=XLOOKUP(1,(PayrollPeriods[PeriodStartDate]<=YE_{y})*"
                                 f"(PayrollPeriods[PeriodEndDate]>YE_{y}),PayrollPeriods[PayrollPeriodID])"),
                 f"{c}{r + 4}": f"={look(cross, 'PeriodStartDate')}",
                 f"{c}{r + 5}": f"={look(cross, 'PeriodEndDate')}",
                 f"{c}{r + 6}": f"={wd(f'{c}{r + 4}', f'{c}{r + 5}')}",
                 f"{c}{r + 7}": f"={wd(f'{c}{r + 4}', f'YE_{y}')}",
                 f"{c}{r + 8}": f"={c}{r + 7}/{c}{r + 6}",
                 f"{c}{r + 9}": f"=ROUND(SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{full}),2)",
                 f"{c}{r + 10}": f"=ROUND(SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{cross})*{c}{r + 8},2)",
                 f"{c}{r + 17}": (f"=ROUND(SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{full})+"
                                  f"SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{cross})*{c}{r + 8},2)")})
        for k, field in ((18, "GrossPay"), (19, "EmployerPayrollTax"), (20, "EmployerBenefits")):
            ws.Range(f"{c}{r + k}").Formula2 = (f"=ROUND(SUMIFS(PayrollCost[{field}],PayrollCost[PayrollPeriodID],{full})+"
                                                f"SUMIFS(PayrollCost[{field}],PayrollCost[PayrollPeriodID],{cross})*"
                                                f"{c}{r + 8},2)")
        ws.Range(f"{c}{r + 21}").Formula2 = (f'=ROUND(SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{full},'
                                             f'PayrollCost[CostCenterName],"Manufacturing")+SUMIFS(PayrollCost[Cost],'
                                             f'PayrollCost[PayrollPeriodID],{cross},PayrollCost[CostCenterName],'
                                             f'"Manufacturing")*{c}{r + 8},2)')
        ws.Range(f"{c}{r + 22}").Formula2 = f"={c}{r + 17}-{c}{r + 21}"
        for nm, k in (("PayFull", 1), ("PayCross", 3), ("CrossDays", 6), ("CrossInside", 7), ("FullCost", 9),
                      ("CrossShare", 10)):
            name(b, f"{nm}_{y}", ws, f"{c}{r + k}")
    # the current year-end: the processed periods' cost per working day
    c, y = "D", C
    ids = f"F{r + 1}#"
    first_day = f"MIN({look(ids, 'PeriodStartDate')})"
    last_day = f"MAX({look(ids, 'PeriodEndDate')})"
    put(ws, {f"F{r}": "Last eight processed periods",
             f"F{r + 1}": ('=TAKE(SORTBY(FILTER(PayrollPeriods[PayrollPeriodID],PayrollPeriods[Status]="Processed"),'
                           'FILTER(PayrollPeriods[PeriodEndDate],PayrollPeriods[Status]="Processed"),1),-8)'),
             f"G{r}": "Cost", f"G{r + 1}": f"=SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{ids})",
             f"{c}{r + 11}": f'=MIN({ids})&"-"&MAX({ids})',
             f"{c}{r + 12}": f'=TEXT({first_day},"yyyy-mm-dd")&" to "&TEXT({last_day},"yyyy-mm-dd")',
             f"{c}{r + 13}": f"={wd(first_day, last_day)}",
             f"{c}{r + 14}": f"=SUM(SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{ids}))",
             f"{c}{r + 15}": f"={c}{r + 14}/{c}{r + 13}",
             f"{c}{r + 16}": f"={wd(last_day + '+1', f'YE_{y}')}",
             f"{c}{r + 17}": f"=ROUND({c}{r + 14}/{c}{r + 13}*{c}{r + 16},2)"})
    for k, field in ((18, "GrossPay"), (19, "EmployerPayrollTax"), (20, "EmployerBenefits")):
        ws.Range(f"{c}{r + k}").Formula2 = (f"=ROUND(SUM(SUMIFS(PayrollCost[{field}],PayrollCost[PayrollPeriodID],{ids}))/"
                                            f"{c}{r + 13}*{c}{r + 16},2)")
    ws.Range(f"{c}{r + 21}").Formula2 = (f'=ROUND(SUM(SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],{ids},'
                                         f'PayrollCost[CostCenterName],"Manufacturing"))/{c}{r + 13}*{c}{r + 16},2)')
    ws.Range(f"{c}{r + 22}").Formula2 = f"={c}{r + 17}-{c}{r + 21}"
    for nm, k in (("ProcessedDays", 13), ("ProcessedCost", 14), ("DailyCost", 15), ("DaysLeft", 16)):
        name(b, f"{nm}_{y}", ws, f"{c}{r + k}")
    name(b, "ProcessedIDs", ws, f"F{r + 1}")
    for y2, c2 in yc:
        for nm, k in (("Payroll", 17), ("PayGross", 18), ("PayTax", 19), ("PayBen", 20), ("PayMfg", 21),
                      ("PayOther", 22)):
            name(b, f"{nm}_{y2}", ws, f"{c2}{r + k}")
    ws.Range(f"B{r + 1}:D{r + 22}").NumberFormat = MONEY
    for k in (1, 3, 6, 7):
        ws.Range(f"B{r + k}:D{r + k}").NumberFormat = "0"
    for k in (2, 4, 5):
        ws.Range(f"B{r + k}:D{r + k}").NumberFormat = DATE
    ws.Range(f"B{r + 8}:D{r + 8}").NumberFormat = "0.0000"
    ws.Range(f"D{r + 13}").NumberFormat = "0"
    ws.Range(f"D{r + 16}").NumberFormat = "0"
    ws.Range(f"G{r + 1}:G{r + 8}").NumberFormat = MONEY
    bold(ws, f"A{r + 17}:D{r + 17}")
    bold(ws, f"F{r}:G{r}")
    note(ws, f"A{r + 11}", "The last pay periods of the current year have no registers (their status is Open), so "
                           "the accrual multiplies the cost per working day of the last eight processed periods by the "
                           "working days left in the year. Working days come from WorkCenterCalendar.")
    # the accrual by cost center: the A1 entry lines
    r += 24
    put(ws, {f"A{r}": "Payroll owed by cost center (gross pay; employer taxes and benefits)", f"B{r}": f"Gross {F}",
             f"C{r}": f"Gross {P}", f"D{r}": f"Gross {C}", f"E{r}": f"Taxes and benefits {F}",
             f"F{r}": f"Taxes and benefits {P}", f"G{r}": f"Taxes and benefits {C}", f"H{r}": "Account"})
    bold(ws, f"A{r}:H{r}")
    b.found["center_rows"] = {}
    for center, _ in payroll_accounts():
        r += 1
        ws.Cells(r, 1).Value = center
        q = f'"{center}"'
        for k, (y, c) in enumerate(yc[:2]):
            full, cross, share = f"PayFull_{y}", f"PayCross_{y}", f"(CrossInside_{y}/CrossDays_{y})"
            for col_, fields in ((("B", "C")[k], ["GrossPay"]), (("E", "F")[k], ["EmployerPayrollTax", "EmployerBenefits"])):
                parts = []
                for fld in fields:
                    parts.append(f"SUMIFS(PayrollCost[{fld}],PayrollCost[PayrollPeriodID],{full},PayrollCost[CostCenterName],{q})+"
                                 f"SUMIFS(PayrollCost[{fld}],PayrollCost[PayrollPeriodID],{cross},PayrollCost[CostCenterName],{q})*{share}")
                ws.Range(f"{col_}{r}").Formula2 = "=ROUND(" + "+".join(parts) + ",2)"
        for col_, fields in (("D", ["GrossPay"]), ("G", ["EmployerPayrollTax", "EmployerBenefits"])):
            parts = [f"SUM(SUMIFS(PayrollCost[{fld}],PayrollCost[PayrollPeriodID],ProcessedIDs#,PayrollCost[CostCenterName],{q}))"
                     for fld in fields]
            ws.Range(f"{col_}{r}").Formula2 = f"=ROUND(({'+'.join(parts)})/ProcessedDays_{C}*DaysLeft_{C},2)"
        ws.Range(f"H{r}").Formula2 = f'=XLOOKUP({q},PayrollAccounts[CostCenterName],PayrollAccounts[AdjustmentAccount])'
        b.found["center_rows"][center] = r
    ws.Range(f"B{r - len(payroll_accounts()) + 1}:G{r}").NumberFormat = MONEY
    r += 2
    put(ws, {f"A{r}": "A1: payroll accrued at each year-end", f"B{r}": f"Retained earnings, 1 January {P}",
             f"C{r}": f"Income {P}", f"D{r}": f"Income {C}",
             f"A{r + 1}": "Effect", f"B{r + 1}": f"=-Payroll_{F}", f"C{r + 1}": f"=-(Payroll_{P}-Payroll_{F})",
             f"D{r + 1}": f"=-(Payroll_{C}-Payroll_{P})",
             f"A{r + 2}": "  cost of goods sold (5080)", f"C{r + 2}": f"=PayMfg_{P}-PayMfg_{F}", f"D{r + 2}": f"=PayMfg_{C}-PayMfg_{P}",
             f"A{r + 3}": "  operating expenses", f"C{r + 3}": f"=PayOther_{P}-PayOther_{F}",
             f"D{r + 3}": f"=PayOther_{C}-PayOther_{P}"})
    bold(ws, f"A{r}:D{r}")
    ws.Range(f"B{r + 1}:D{r + 3}").NumberFormat = MONEY
    name(b, "AdjA1_RE", ws, f"B{r + 1}")
    name(b, f"AdjA1_{P}", ws, f"C{r + 1}")
    name(b, f"AdjA1_{C}", ws, f"D{r + 1}")
    for y, c in ((P, "C"), (C, "D")):
        name(b, f"AdjA1COGS_{y}", ws, f"{c}{r + 2}")
        name(b, f"AdjA1OPX_{y}", ws, f"{c}{r + 3}")
    r = model_answer(ws, r + 5, MA + ": the payroll method and where it ends up", [
        "One working-day method at every year-end: for the earlier year-ends, the registers of the period paid in the "
        "next year in full, plus the share of the period that crosses the year-end by its working days; for the "
        "current year-end, whose last pay periods have no registers, the cost per working day of the last eight "
        "processed periods times the working days left. Exercise 12.1's hour-based allocation (about 296,000 and "
        "335,000 at the earlier year-ends) is acceptable if it is applied at every year-end and the current estimate "
        "uses the same method.",
        "The manufacturing part would have been debited to 1090 Manufacturing Cost Clearing; with no completion to "
        "absorb it, it ends in 5080 Manufacturing Variance, part of cost of goods sold. The rest goes to each cost "
        "center's salary account (gross pay) and 6060 Payroll Taxes and Benefits (employer taxes and benefits). The "
        "credits are 2030 (gross pay), 2032 (employer taxes), and 2033 (benefits)."], last_col=4)

    # interest
    put(ws, {f"A{r}": "Interest accrued on the notes at each year-end (2080 has never been used)"})
    bold(ws, f"A{r}")
    r += 1
    heads = ["Year-end", "Note", "Originated by then", "Previous payment (or origination)", "Next payment",
             "Days in its period", "Days to the year-end, counted inclusive", "Interest of the next payment",
             "Accrued", "Accrued, day of the previous payment left out"]
    for k, h in enumerate(heads, start=1):
        ws.Cells(r, k).Value = h
    bold(ws, f"A{r}:J{r}")
    ws.Rows(r).WrapText = True
    notes_ = ch17().notes_payable(data())
    b.found["interest_rows"] = {}
    for y in (F, P, C):
        for k, n in enumerate(notes_, start=1):
            r += 1
            i = n["id"]
            put(ws, {f"A{r}": f"=YE_{y}", f"B{r}": i,
                     f"C{r}": f"=XLOOKUP(B{r},DebtAgreements[DebtAgreementID],DebtAgreements[OriginationDate])<=A{r}",
                     f"D{r}": (f'=MAX(MAXIFS(DebtSchedule[PaymentDate],DebtSchedule[DebtAgreementID],B{r},'
                               f'DebtSchedule[PaymentDate],"<="&A{r}),XLOOKUP(B{r},DebtAgreements[DebtAgreementID],'
                               'DebtAgreements[OriginationDate]))'),
                     f"E{r}": f'=MINIFS(DebtSchedule[PaymentDate],DebtSchedule[DebtAgreementID],B{r},DebtSchedule[PaymentDate],">"&A{r})',
                     f"F{r}": f"=E{r}-D{r}", f"G{r}": f"=A{r}-D{r}+1",
                     f"H{r}": f"=SUMIFS(DebtSchedule[InterestAmount],DebtSchedule[DebtAgreementID],B{r},DebtSchedule[PaymentDate],E{r})",
                     f"I{r}": f"=IF(C{r},ROUND(H{r}*MIN(G{r},F{r})/F{r},2),0)",
                     f"J{r}": f"=IF(C{r},ROUND(H{r}*IF(G{r}>=F{r},1,(G{r}-1)/F{r}),2),0)"})
            b.found["interest_rows"][(y, k)] = r
    first = min(b.found["interest_rows"].values())
    ws.Range(f"A{first}:A{r}").NumberFormat = DATE
    ws.Range(f"D{first}:E{r}").NumberFormat = DATE
    ws.Range(f"H{first}:J{r}").NumberFormat = MONEY
    r += 1
    put(ws, {f"A{r}": "Interest accrued", f"B{r}": ye(F), f"C{r}": ye(P), f"D{r}": ye(C), f"E{r}": "Alternative day count"})
    bold(ws, f"A{r}:E{r}")
    for y, c in yc:
        ws.Range(f"{c}{r + 1}").Formula2 = f"=SUMIFS(I{first}:I{r - 1},A{first}:A{r - 1},YE_{y})"
        name(b, f"Interest_{y}", ws, f"{c}{r + 1}")
    ws.Range(f"E{r + 1}").Formula2 = f"=SUMIFS(J{first}:J{r - 1},A{first}:A{r - 1},YE_{C})"
    name(b, f"InterestAlt_{C}", ws, f"E{r + 1}")
    ws.Range(f"B{r + 1}:E{r + 1}").NumberFormat = MONEY
    r += 3
    put(ws, {f"A{r}": "A4: interest accrued at each year-end", f"B{r}": f"Retained earnings, 1 January {P}",
             f"C{r}": f"Income {P}", f"D{r}": f"Income {C}",
             f"A{r + 1}": "Effect", f"B{r + 1}": f"=-Interest_{F}", f"C{r + 1}": f"=Interest_{F}-Interest_{P}",
             f"D{r + 1}": f"=Interest_{P}-Interest_{C}"})
    bold(ws, f"A{r}:D{r}")
    ws.Range(f"B{r + 1}:D{r + 1}").NumberFormat = MONEY
    name(b, "AdjA4_RE", ws, f"B{r + 1}")
    name(b, f"AdjA4_{P}", ws, f"C{r + 1}")
    name(b, f"AdjA4_{C}", ws, f"D{r + 1}")
    model_answer(ws, r + 3, MA + ": the day-count convention", [
        "Each payment's interest covers the period since the payment before it, so the interest accrued at a "
        "year-end is the next payment's interest times the days from the previous payment (counted inclusive) to the "
        "year-end over the days between the two payments. A payment due on 1 January carries a full month of "
        "December interest. Leaving out the day of the previous payment gives the alternative column; either is "
        "acceptable with the convention stated."], last_col=6)
    widths(ws, {"A": 58, "B": 16, "C": 16, "D": 16, "E": 16, "F": 16, "G": 16, "H": 16, "I": 14, "J": 18})
    documentation(b)


def checks_r4(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 4"
    f = facts("r4")
    for y, x in ((F, f["cf"]), (P, f["cp"]), (C, f["cc"])):
        b.check(e, f"invoices for {y} deliveries posted later", x["n"], f"=LateCount_{y}", 0, COUNT)
        b.check(e, f"lines delivered in {y} never invoiced", x["n_lines"], f"=UnbilledCount_{y}", 0, COUNT)
        b.check(e, f"revenue that belongs to {y}", x["total"], f"=Cutoff_{y}")
        b.check(e, f"revenue that belongs to {y}, by item group", x["total"], f"=CutoffByGroup_{y}")
        b.check(e, f"sales tax on those invoices ({y})", x["tax"], f"=LateTax_{y}")
        b.check(e, f"standard cost of the lines never invoiced ({y})", x["std"], f"=UnbilledStd_{y}")
        col_ = {F: "B", P: "C", C: "D"}[y]
        for s, v in x["segments"]:
            b.check(e, f"{y} cutoff, segment {s}", v, f"=Cutoff!{col_}{b.found['segment_rows'][s]}")
        for g, v in x["groups"]:
            b.check(e, f"{y} cutoff, {g}", v, f"=Cutoff!{col_}{b.found['group_rows'][g]}")
    b.check(e, "late invoices not posted in the year after delivery", 0, "=LateNotNextYear", 0, COUNT)
    half_up = sum(xr(q * p_ * (1 - dsc)) for *_, q, p_, dsc, _std, _v in unbilled_lines())
    b.check(e, "unbilled lines rounded half up less the query's ROUND", xr(half_up - sum(v for *_, v in unbilled_lines())),
            "=SUM(UnbilledLines[RoundingDifference])")
    for y, x in ((F, f["pf"]), (P, f["pp"])):
        b.check(e, f"{y}: period paid in the next year", x["full"]["id"], f"=PayFull_{y}", 0, "0")
        b.check(e, f"{y}: its registers", x["full"]["cost"], f"=FullCost_{y}")
        b.check(e, f"{y}: period crossing the year-end", x["cross"]["id"], f"=PayCross_{y}", 0, "0")
        b.check(e, f"{y}: its working days", x["cross"]["days"], f"=CrossDays_{y}", 0, COUNT)
        b.check(e, f"{y}: its working days within the year", x["cross"]["inside"], f"=CrossInside_{y}", 0, COUNT)
        b.check(e, f"{y}: its share", x["cross"]["share"], f"=CrossShare_{y}")
    pc = f["pc"]
    b.check(e, f"{C}: first processed period of the eight", pc["p"]["ids"][0], "=MIN(ProcessedIDs#)", 0, "0")
    b.check(e, f"{C}: last processed period", pc["p"]["ids"][-1], "=MAX(ProcessedIDs#)", 0, "0")
    b.check(e, f"{C}: their working days", pc["p"]["wd"], f"=ProcessedDays_{C}", 0, COUNT)
    b.check(e, f"{C}: their cost", xr(pc["p"]["cost"]), f"=ProcessedCost_{C}")
    b.check(e, f"{C}: cost per working day", xr(pc["p"]["daily"]), f"=ROUND(DailyCost_{C},2)")
    b.check(e, f"{C}: working days left", pc["p"]["left"], f"=DaysLeft_{C}", 0, COUNT)
    for y, x in ((F, f["pf"]), (P, f["pp"]), (C, pc)):
        b.check(e, f"payroll owed at {ye(y)}", x["total"], f"=Payroll_{y}")
        b.check(e, f"payroll owed at {ye(y)}, gross pay", x["gross"], f"=PayGross_{y}")
        b.check(e, f"payroll owed at {ye(y)}, employer taxes", x["tax"], f"=PayTax_{y}")
        b.check(e, f"payroll owed at {ye(y)}, benefits", x["ben"], f"=PayBen_{y}")
        b.check(e, f"payroll owed at {ye(y)}, manufacturing", x["mfg"], f"=PayMfg_{y}")
        b.check(e, f"payroll owed at {ye(y)}, other cost centers", x["other"], f"=PayOther_{y}")
    for x in f["ints"]:
        y = x["year"]
        b.check(e, f"interest accrued at {ye(y)}", x["total"], f"=Interest_{y}")
        for i in x["items"]:
            row = b.found["interest_rows"][(y, i["note"])]
            b.check(e, f"interest accrued at {ye(y)}, note {i['note']}", i["amount"], f"=Cutoff!I{row}")
    b.check(e, f"interest at {ye(C)}, alternative day count", f["ints"][-1]["alt"], f"=InterestAlt_{C}")
    r5 = facts("r5")["a"]
    for key, nm in (("A1", "AdjA1"), ("A2", "AdjA2"), ("A4", "AdjA4")):
        b.check(e, f"{key} effect on retained earnings at 1 January {P}", r5[key]["re"], f"={nm}_RE")
        b.check(e, f"{key} effect on {P} income", r5[key]["P"], f"={nm}_{P}")
        b.check(e, f"{key} effect on {C} income", r5[key]["C"], f"={nm}_{C}")


# --- Requirement 5: classify, measure, and judge the adjustments -------------------------------------------------------

def paste_inputs_r5(b: ExerciseBuild) -> None:
    F, P, C = years()
    ws, r = sql_results(b)
    heading(ws, f"A{r}", "Exercise 8.1's aging of the open receivables at two year-ends")
    ap, kp = aging(P)
    ac, kc = aging(C)
    rows = [[BUCKET_NAMES[k], ap[k], kp[k], ac[k], kc[k]] for k in range(5)]
    pasted(b, ws, f"A{r + 1}", ["Bucket", f"Balance{P}", f"Invoices{P}", f"Balance{C}", f"Invoices{C}"], rows,
           "ReceivableAging",
           "open receivables at each year-end (each invoice dated by then less the receipts applied and the credit "
           "memos dated by then, rounded and kept if greater than zero), aged by days past the due date in Exercise "
           "8.1's buckets", {f"Balance{P}": MONEY, f"Balance{C}": MONEY, f"Invoices{P}": COUNT, f"Invoices{C}": COUNT})
    r += len(rows) + 4
    heading(ws, f"A{r}", "Returns made in a later fiscal year than the delivery of the goods returned")
    by = ch17().returns_across(data())
    rows = [[ry, dy, by["by_year"][ry]["n"], by["by_year"][ry]["rev"], by["by_year"][ry]["cost"]]
            for ry, dy in sorted(by["pairs"])]
    pasted(b, ws, f"A{r + 1}", ["ReturnYear", "DeliveryYear", "Returns", "CreditMemoRevenue", "StandardCost"], rows,
           "ReturnsAfterYearEnd",
           "returns made in a later year than the delivery of the goods returned (each return dated by the delivery of "
           "its first line), with the credit memos' SubTotal and the returned lines' standard cost",
           {"CreditMemoRevenue": MONEY, "StandardCost": MONEY, "Returns": COUNT})
    b.found["sql_row"] = r + len(rows) + 4


def load_returns(b: ExerciseBuild) -> None:
    connection_only(b, "SalesReturns", nav(b, 21, "SalesReturn", extra=[
        ("Removed Other Columns", pq.select_columns(["SalesReturnID", "ReturnNumber", "ReturnDate", "ReasonCode"]))]),
        "T21_SalesReturn")
    loaded(b, "ReturnLines", nav(b, 22, "SalesReturnLine", extra=[
        ("Removed Other Columns", pq.select_columns(["SalesReturnLineID", "SalesReturnID", "ShipmentLineID", "ItemID",
                                                     "QuantityReturned", "ExtendedStandardCost"])),
        ("Merged Queries", pq.merge("SalesReturns", "SalesReturnID", "SalesReturnID", "SalesReturns")),
        ("Expanded SalesReturns", pq.expand("SalesReturns", ["ReturnNumber", "ReturnDate", "ReasonCode"])),
        ("Inserted Year", 'Table.AddColumn({prev}, "Year", each Date.Year([ReturnDate]), Int64.Type)'),
        ("Changed Type1", date_types(["ReturnDate"]))]),
        "Returns", "T22_SalesReturnLine with its return's date and reason (restocked at full standard cost)",
        {"ReturnDate": DATE, "ExtendedStandardCost": MONEY})


def adjustment_lines(b: ExerciseBuild) -> list[list]:
    """The entry lines at each year-end: [No, Adjustment, YearEnd, Account, Presentation, Amount, Type, Evidence]."""
    F, P, C = years()
    cut = b.found["center_rows"]
    gcol = {F: "B", P: "C", C: "D"}
    old_rows, group_rows = b.found["old_rows"], b.found["group_rows"]
    out = []
    prior = {F: None, P: F, C: P}
    centers = [(c, a) for c, a in payroll_accounts() if a != 1090]
    pay_ev = ("Cutoff worksheet, payroll: PayrollRegister by pay period and cost center (registers of the periods paid "
              "after the year-end, prorated by WorkCenterCalendar working days; the last eight processed periods at "
              f"{ye(C)})")
    for y in (F, P, C):
        q = prior[y]
        ye_ = f"=YE_{y}"
        typ = "Correction of an error"
        lines = []
        if q:
            lines.append((3030, "", f"=Payroll_{q}"))
        lines.append((5080, "", f"=PayMfg_{y}" + (f"-PayMfg_{q}" if q else "")))
        for center, acct in centers:
            row = cut[center]
            lines.append((acct, "", f"=Cutoff!{gcol[y]}{row}" + (f"-Cutoff!{gcol[q]}{row}" if q else "")))
        lines.append((6060, "", f"=(PayOther_{y}-GrossOther_{y})" + (f"-(PayOther_{q}-GrossOther_{q})" if q else "")))
        lines += [(2030, "", f"=-PayGross_{y}"), (2032, "", f"=-PayTax_{y}"), (2033, "", f"=-PayBen_{y}")]
        out += [["A1", "Payroll owed for the last days of the year", ye_, a, p, f, typ, pay_ev] for a, p, f in lines]
        lines = [(1020, "", f"=Cutoff_{y}")]
        if q:
            lines.append((3030, "", f"=-Cutoff_{q}"))
        for g, row in group_rows.items():
            acct = int(ch17().revenue_accounts(data())[g])
            lines.append((acct, "", f"=-(Cutoff!{gcol[y]}{row}" + (f"-Cutoff!{gcol[q]}{row})" if q else ")")))
        out += [["A2", "Revenue recognized in the year of delivery", ye_, a, p, f, typ,
                 f"{SQL_FILE}: tests L5 and L6 (LateInvoices, UnbilledLines); Cutoff worksheet, revenue"]
                for a, p, f in lines]
        lines = [(2040, "", f"=Old_{y}")]
        if q:
            lines.append((3030, "", f"=-Old_{q}"))
        for acct, row in old_rows.items():
            lines.append((int(acct), "", f"=-('Accrued Expenses'!{gcol[y]}{row}" +
                          (f"-'Accrued Expenses'!{gcol[q]}{row})" if q else ")")))
        out += [["A3", "Accruals past the invoicing window reversed", ye_, a, p, f, typ,
                 "Accrued Expenses worksheet: the Accrual entries, AccrualClearing (invoice debits to 2040) and the "
                 "Accrual Adjustment entries; old = open longer than the longest clearing lag"] for a, p, f in lines]
        lines = []
        if q:
            lines.append((3030, "", f"=Interest_{q}"))
        lines += [(7030, "", f"=Interest_{y}" + (f"-Interest_{q}" if q else "")), (2080, "", f"=-Interest_{y}")]
        out += [["A4", "Interest accrued on the notes", ye_, a, p, f, typ,
                 "Cutoff worksheet, interest: DebtScheduleLine (the next payment's interest, prorated by days)"]
                for a, p, f in lines]
        if y != F:
            out += [["R1", "Current portion of the notes payable", ye_, 2110, "Notes payable, less current portion",
                     f"=CurPortion_{y}", "Reclassification", "DebtScheduleLine: principal due in the next year"],
                    ["R1", "Current portion of the notes payable", ye_, 2110, "Current portion of notes payable",
                     f"=-CurPortion_{y}", "Reclassification", "DebtScheduleLine: principal due in the next year"],
                    ["R2", "Credit balance of 1090 netted into work in process", ye_, 1090, "",
                     f"=-SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],1090)", "Reclassification",
                     "Trial balance: 1090 Manufacturing Cost Clearing"],
                    ["R2", "Credit balance of 1090 netted into work in process", ye_, 1046, "",
                     f"=SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],1090)", "Reclassification",
                     "Trial balance: 1090 Manufacturing Cost Clearing"]]
    return out


def r5(b: ExerciseBuild) -> None:
    F, P, C = years()
    paste_inputs_r5(b)
    load_returns(b)
    # the gross pay of the cost centers outside manufacturing, for 6060's line (taxes, benefits, and the cents)
    cw = b.wb.Worksheets("Cutoff")
    rows = b.found["center_rows"]
    last = max(rows.values()) + 1
    cw.Range(f"A{last}").Value = "Gross pay outside manufacturing"
    for y, c in ((F, "B"), (P, "C"), (C, "D")):
        cw.Range(f"{c}{last}").Formula2 = (f"=SUM({c}{min(rows.values())}:{c}{max(rows.values())})-"
                                           f"{c}{rows['Manufacturing']}")
        cw.Range(f"{c}{last}").NumberFormat = MONEY
        name(b, f"GrossOther_{y}", cw, f"{c}{last}")

    ws = analysis_sheet(b, "Adjustments")
    title(ws, "The schedule of adjustments", "Requirement 5. Numbered entries for the CFO's approval; nothing is posted. "
                                              "Effects on income before income taxes (positive = more income) and on "
                                              "equity at each year-end.")
    heads = ["No.", "Adjustment", "Accounts", "Evidence", f"Retained earnings, 1 January {P}", f"Income {P}",
             f"Income {C}", f"Balance {ye(P)}", f"Balance {ye(C)}", "Type", "Decision"]
    for k, h in enumerate(heads, start=1):
        ws.Cells(4, k).Value = h
    bold(ws, "A4:K4")
    ws.Rows(4).WrapText = True
    sched = [
        ("A1", "Payroll owed for the last days of each year (gross pay, employer taxes, benefits)",
         "Dr 5080, salary accounts, 6060 (and retained earnings); Cr 2030, 2032, 2033",
         "Payroll registers and WorkCenterCalendar (Cutoff worksheet)",
         "=AdjA1_RE", f"=AdjA1_{P}", f"=AdjA1_{C}", f"=-Payroll_{P}", f"=-Payroll_{C}",
         "Correction of an error: the facts existed at each year-end",
         "Record. The liability exceeds materiality, and the missing accrual recurs every year."),
        ("A2", "Revenue recognized in the year of delivery (invoices posted in the next year; lines never invoiced)",
         "Dr 1020; Cr 4010-4040 (and retained earnings)", "Tests L5 and L6 (Cutoff worksheet)",
         "=AdjA2_RE", f"=AdjA2_{P}", f"=AdjA2_{C}", f"=Cutoff_{P}", f"=Cutoff_{C}",
         "Correction of an error", "Record."),
        ("A3", "Accruals open longer than the clearing window, reversed at each year-end",
         "Dr 2040; Cr expense accounts (and retained earnings)", "Accrual entries, AccrualClearing, Accrual Adjustments",
         "=AdjA3_RE", f"=AdjA3_{P}", f"=AdjA3_{C}", f"=Old_{P}", f"=Old_{C}",
         "Correction of an error (an accrual within the window that later proves unneeded is a change in estimate)",
         "Record."),
        ("A4", "Interest accrued on the notes since the last payment",
         "Dr 7030 (and retained earnings); Cr 2080", "DebtScheduleLine (Cutoff worksheet)",
         "=AdjA4_RE", f"=AdjA4_{P}", f"=AdjA4_{C}", f"=-Interest_{P}", f"=-Interest_{C}",
         "Correction of an error", "Record."),
    ]
    r = 5
    for row in sched:
        put(ws, {f"{col(k)}{r}": v for k, v in enumerate(row, start=1)})
        r += 1
    put(ws, {f"A{r}": "A1-A4", f"B{r}": "Total of the recorded adjustments",
             **{f"{c}{r}": f"=ROUND(SUM({c}5:{c}{r - 1}),2)" for c in "EFGHI"}})
    bold(ws, f"A{r}:K{r}")
    for nm, c in (("AdjTotal_RE", "E"), (f"AdjTotal_{P}", "F"), (f"AdjTotal_{C}", "G"), (f"EquityEffect_{P}", "H"),
                  (f"EquityEffect_{C}", "I")):
        name(b, nm, ws, f"{c}{r}")
    tot = r
    r += 1
    put(ws, {f"A{r}": "Adjusted net income", f"F{r}": f"=RecNI_{P}+AdjTotal_{P}", f"G{r}": f"=RecNI_{C}+AdjTotal_{C}"})
    name(b, f"AdjNI_{P}", ws, f"F{r}")
    name(b, f"AdjNI_{C}", ws, f"G{r}")
    r += 2
    # the current portion of the notes, for R1
    cur = lambda y: ("=SUMPRODUCT(DebtSchedule[PrincipalAmount]*(YEAR(DebtSchedule[PaymentDate])=YEAR(YE_{0})+1)*"
                     "(XLOOKUP(DebtSchedule[DebtAgreementID],DebtAgreements[DebtAgreementID],"
                     "DebtAgreements[OriginationDate])<=YE_{0}))").format(y)
    put(ws, {f"A{r}": "R1", f"B{r}": "Current portion of the notes payable (principal due in the next year)",
             f"C{r}": "Dr 2110 (long-term); Cr current portion", f"D{r}": "DebtScheduleLine",
             f"H{r}": cur(P), f"I{r}": cur(C), f"J{r}": "Reclassification",
             f"K{r}": "Record: all of 2110 is classified long-term in the ledger.",
             f"A{r + 1}": "R2", f"B{r + 1}": "Credit balance of 1090 Manufacturing Cost Clearing netted into work in process",
             f"C{r + 1}": "Dr 1090; Cr 1046", f"D{r + 1}": "Trial balance",
             f"H{r + 1}": f"=-SUMIFS(WorkingTB[Recorded{P}],WorkingTB[AccountNumber],1090)",
             f"I{r + 1}": f"=-SUMIFS(WorkingTB[Recorded{C}],WorkingTB[AccountNumber],1090)", f"J{r + 1}": "Reclassification",
             f"K{r + 1}": "Record: a credit balance cannot sit among current assets."})
    name(b, f"CurPortion_{P}", ws, f"H{r}")
    name(b, f"CurPortion_{C}", ws, f"I{r}")
    name(b, f"Reclass2_{P}", ws, f"H{r + 1}")
    name(b, f"Reclass2_{C}", ws, f"I{r + 1}")
    r += 3
    passed = r
    put(ws, {f"A{r}": "P1", f"B{r}": "Allowance for credit losses at Exercise 8.1's rates",
             f"C{r}": "Dr 6170; Cr 1030", f"D{r}": "ReceivableAging (SQL Results)",
             f"G{r}": f"=I{r}-H{r}", f"H{r}": f"=-SUMPRODUCT(ROUND(ReceivableAging[Balance{P}]*LossRates,2))",
             f"I{r}": f"=-SUMPRODUCT(ROUND(ReceivableAging[Balance{C}]*LossRates,2))",
             f"J{r}": "Change in estimate", f"K{r}": "Pass; list for the CFO's approval.",
             f"A{r + 1}": "P2", f"B{r + 1}": "Returns expected after the year-end on the year's deliveries",
             f"C{r + 1}": "Dr 4060, Dr 1040; Cr 1020", f"D{r + 1}": "ReturnsAfterYearEnd (SQL Results)",
             f"G{r + 1}": f"=I{r + 1}-H{r + 1}",
             f"H{r + 1}": (f"=-(SUMIFS(ReturnsAfterYearEnd[CreditMemoRevenue],ReturnsAfterYearEnd[ReturnYear],{P})-"
                           f"SUMIFS(ReturnsAfterYearEnd[StandardCost],ReturnsAfterYearEnd[ReturnYear],{P}))"),
             f"I{r + 1}": (f"=-(SUMIFS(ReturnsAfterYearEnd[CreditMemoRevenue],ReturnsAfterYearEnd[ReturnYear],{C})-"
                           f"SUMIFS(ReturnsAfterYearEnd[StandardCost],ReturnsAfterYearEnd[ReturnYear],{C}))"),
             f"J{r + 1}": "Change in estimate", f"K{r + 1}": "Pass; list for the CFO's approval.",
             f"A{r + 2}": "P3", f"B{r + 2}": "Write-down of Damaged and Quality Concern returns restocked at full cost",
             f"C{r + 2}": "Dr 5070; Cr 1040", f"D{r + 2}": "ReturnLines (SalesReturn, SalesReturnLine)",
             f"G{r + 2}": f"=I{r + 2}", f"I{r + 2}": f"=-DamagedRestocked_{C}",
             f"J{r + 2}": "Estimate (valuation of inventory)", f"K{r + 2}": "Pass; list for the CFO's approval.",
             f"A{r + 3}": "P1-P3", f"B{r + 3}": "Passed items, in aggregate",
             f"G{r + 3}": f"=SUM(G{r}:G{r + 2})", f"I{r + 3}": f"=SUM(I{r}:I{r + 2})",
             f"A{r + 4}": "T1", f"B{r + 4}": "Freight estimates above the carriers' settlements",
             f"C{r + 4}": "Dr 2040; Cr 5050", f"D{r + 4}": "Accrued Expenses worksheet", f"I{r + 4}": f"=-FreightExcess_{C}",
             f"J{r + 4}": "Change in estimate", f"K{r + 4}": f'="Clearly trivial (below "&TEXT(Trivial_{C},"#,##0.00")&"); listed."'})
    bold(ws, f"A{r + 3}:K{r + 3}")
    for nm, c, k in (("PassedP1", "I", 0), ("PassedP1Prior", "H", 0), ("PassedP1Income", "G", 0), ("PassedP2", "I", 1),
                     ("PassedP2Prior", "H", 1), ("PassedP2Income", "G", 1), ("PassedP3", "I", 2),
                     ("PassedAggregate", "I", 3), ("PassedIncome", "G", 3), ("TrivialT1", "I", 4)):
        name(b, nm, ws, f"{c}{r + k}")
    ws.Range(f"E5:I{r + 4}").NumberFormat = STMT
    ws.Range(f"B5:D{r + 4}").WrapText = True
    ws.Range(f"J5:K{r + 4}").WrapText = True
    r += 6

    # materiality and the judgment
    put(ws, {f"A{r}": "Materiality and the judgment", f"B{r}": f"Fiscal {P}", f"C{r}": f"Fiscal {C}",
             f"A{r + 1}": "Materiality (5% of income before income taxes as recorded)", f"B{r + 1}": f"=Materiality_{P}",
             f"C{r + 1}": f"=Materiality_{C}",
             f"A{r + 2}": "Effect of A1-A4 on income", f"B{r + 2}": f"=AdjTotal_{P}", f"C{r + 2}": f"=AdjTotal_{C}",
             f"A{r + 3}": "  as a share of materiality", f"B{r + 3}": f"=ABS(B{r + 2})/B{r + 1}", f"C{r + 3}": f"=ABS(C{r + 2})/C{r + 1}",
             f"A{r + 4}": "Payroll owed at the year-end (A1's liability)", f"B{r + 4}": f"=Payroll_{P}", f"C{r + 4}": f"=Payroll_{C}",
             f"A{r + 5}": "Current liabilities understated, before the reclassification",
             f"B{r + 5}": f"=Payroll_{P}+Interest_{P}-Old_{P}", f"C{r + 5}": f"=Payroll_{C}+Interest_{C}-Old_{C}",
             f"A{r + 6}": "Working capital overstated, after the reclassification",
             f"B{r + 6}": f"=B{r + 5}+CurPortion_{P}-Cutoff_{P}", f"C{r + 6}": f"=C{r + 5}+CurPortion_{C}-Cutoff_{C}",
             f"A{r + 7}": "Passed items in aggregate, at the year-end", f"C{r + 7}": "=PassedAggregate",
             f"A{r + 8}": "  as a share of materiality", f"C{r + 8}": f"=ABS(C{r + 7})/C{r + 1}",
             f"A{r + 9}": f"Passed items on {C} income", f"C{r + 9}": "=PassedIncome"})
    bold(ws, f"A{r}:C{r}")
    ws.Range(f"B{r + 1}:C{r + 9}").NumberFormat = MONEY
    for k in (3, 8):
        ws.Range(f"B{r + k}:C{r + k}").NumberFormat = "0%"
    name(b, "EffectShare", ws, f"C{r + 3}")
    name(b, f"CLRise_{C}", ws, f"C{r + 5}")
    name(b, f"CLRise_{P}", ws, f"B{r + 5}")
    name(b, f"WCFall_{C}", ws, f"C{r + 6}")
    name(b, "PassedShare", ws, f"C{r + 8}")
    r += 11
    f5 = facts("r5")
    r = model_answer(ws, r, MA + ": what to record, what to pass, and how to present 2025", [
        f"Record A1 to A4, R1, and R2. In {C} their effect on income ({money(f5['total']['C'])}) is only "
        f"{pct(f5['share'], 0)} of materiality ({money(f5['mat_c'])}), but size on income is not the whole test: the "
        f"payroll liability alone ({money(f5['pay_c']['total'])}) exceeds materiality, current liabilities at "
        f"{ye(C)} rise by {money(f5['rise'])} before the reclassification, and working capital falls by "
        f"{money(f5['wc_fall'])} after it. At {ye(P)} current liabilities were understated by {money(f5['under_p'])}, "
        f"above that year's materiality ({money(f5['mat_p'])}), and the missing payroll accrual recurs every year, "
        "the kind of error that deserves attention even when each year's effect on income is small.",
        f"Present {P} as restated, with the disclosures of ASC Topic 250, because the shareholders received {P} "
        f"statements prepared from the ledger: retained earnings at 1 January {P} fall by "
        f"{money(-f5['total']['re'])}, {P} income by {money(-f5['total']['P'])}, and the statement of changes in "
        "equity shows the correction of the opening balance. A reasoned \"revised\" presentation is acceptable.",
        f"Pass P1 to P3 and list them for the CFO's approval: in aggregate {money(f5['aggregate'])} at the year-end, "
        f"{pct(f5['agg_share'], 0)} of materiality, and {money(f5['agg_income'])} on {C} income. List T1, the freight "
        f"residual of {money(f5['residual'])}, as clearly trivial, since the controller wants every adjustment listed. "
        "No adjustment touches cash."], last_col=6)

    # the loss rates and the damaged returns
    put(ws, {f"A{r}": "Inputs to the passed items", f"A{r + 1}": "Exercise 8.1's loss rates, by bucket"})
    bold(ws, f"A{r}")
    for k, (bucket, rate) in enumerate(zip(BUCKET_NAMES, RATES)):
        ws.Cells(r + 2 + k, 1).Value = bucket
        ws.Cells(r + 2 + k, 2).Value = rate
    ws.Range(f"B{r + 2}:B{r + 6}").NumberFormat = "0.0%"
    ws.Range(f"B{r + 2}:B{r + 6}").Font.Color = BLUE
    xl.retry(lambda: b.wb.Names.Add(Name="LossRates", RefersTo=f"='Adjustments'!$B${r + 2}:$B${r + 6}"))
    r += 8
    put(ws, {f"A{r}": "Returns restocked at full standard cost", f"B{r}": "Damaged and Quality Concern",
             f"C{r}": "All reasons", f"D{r}": "Debits to 1040 from returns (ledger)"})
    bold(ws, f"A{r}:D{r}")
    reasons = "{" + ",".join(f'"{x}"' for x in WRITE_DOWN) + "}"
    for k, y in enumerate((F, P, C), start=1):
        put(ws, {f"A{r + k}": y,
                 f"B{r + k}": (f"=SUMPRODUCT(ReturnLines[ExtendedStandardCost]*(ReturnLines[Year]={y})*"
                               f"ISNUMBER(MATCH(ReturnLines[ReasonCode],{reasons},0)))"),
                 f"C{r + k}": f"=SUMIFS(ReturnLines[ExtendedStandardCost],ReturnLines[Year],{y})",
                 f"D{r + k}": (f'=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],1040,'
                               f'LedgerSummary[SourceDocumentType],"SalesReturn",LedgerSummary[Year],{y})')})
        name(b, f"DamagedRestocked_{y}", ws, f"B{r + k}")
    put(ws, {f"A{r + 4}": "Total", f"B{r + 4}": f"=SUM(B{r + 1}:B{r + 3})",
             f"A{r + 5}": "Restocked less the ledger (three years)", f"C{r + 5}": f"=ROUND(SUM(C{r + 1}:C{r + 3})-SUM(D{r + 1}:D{r + 3}),2)"})
    name(b, "DamagedTotal", ws, f"B{r + 4}")
    name(b, "RestockDifference", ws, f"C{r + 5}")
    ws.Range(f"B{r + 1}:D{r + 5}").NumberFormat = MONEY
    r += 8

    # the entry lines
    heading(ws, f"A{r}", "AdjustmentLines: the entry lines, one row per account and year-end (debits less credits)")
    note(ws, f"A{r}", "The Review file loads this Table beside the ledger and tests it: each entry balances, no entry "
                      "touches cash, and adjusted net income agrees with this workbook. Lines at the first year-end "
                      "restate the opening balances of the comparative year.")
    lines = adjustment_lines(b)
    header = ["No", "Adjustment", "YearEnd", "Account", "Presentation", "Amount", "Type", "Evidence"]
    lo = range_table(ws, f"A{r + 1}", header, lines, "AdjustmentLines", {"YearEnd": DATE, "Amount": MONEY})
    lo.ListColumns("Account").DataBodyRange.NumberFormat = "0"
    xl.add_column(lo, "AccountName", '=XLOOKUP([@Account],WorkingTB[AccountNumber],WorkingTB[AccountName],"?")')
    xl.add_column(lo, "StatementLine", '=IF([@Presentation]<>"",[@Presentation],XLOOKUP([@Account],'
                                       'WorkingTB[AccountNumber],WorkingTB[StatementLine],"?"))')
    xl.add_column(lo, "Debit", "=MAX([@Amount],0)", MONEY)
    xl.add_column(lo, "Credit", "=MAX(-[@Amount],0)", MONEY)
    lo.ShowTotals = True
    lo.TotalsRowRange.Cells(1, 1).Value = "Total"
    for c in ("Amount", "Debit", "Credit"):
        lo.ListColumns(c).TotalsCalculation = 1
    lo.TotalsRowRange.NumberFormat = MONEY
    b.found["adj_first_row"] = r + 2
    r += len(lines) + 4
    # each entry balances
    put(ws, {f"A{r}": "Each entry balances", f"B{r}": "Year-end", f"C{r}": "Debits", f"D{r}": "Credits",
             f"E{r}": "Debits less credits"})
    bold(ws, f"A{r}:E{r}")
    pairs = sorted({(x[0], x[2]) for x in lines}, key=lambda t: (t[1], t[0]))
    first = r + 1
    for k, (no, yref) in enumerate(pairs, start=1):
        put(ws, {f"A{r + k}": no, f"B{r + k}": yref,
                 f"C{r + k}": f'=SUMIFS(AdjustmentLines[Debit],AdjustmentLines[No],A{r + k},AdjustmentLines[YearEnd],B{r + k})',
                 f"D{r + k}": f'=SUMIFS(AdjustmentLines[Credit],AdjustmentLines[No],A{r + k},AdjustmentLines[YearEnd],B{r + k})',
                 f"E{r + k}": f"=ROUND(C{r + k}-D{r + k},2)"})
    last = r + len(pairs)
    ws.Range(f"B{first}:B{last}").NumberFormat = DATE
    ws.Range(f"C{first}:E{last}").NumberFormat = MONEY
    put(ws, {f"A{last + 1}": "Largest imbalance", f"E{last + 1}": f"=MAX(ABS(E{first}:E{last}))",
             f"A{last + 2}": "Lines on cash (1010)", f"E{last + 2}": "=COUNTIFS(AdjustmentLines[Account],1010)"})
    name(b, "EntryImbalance", ws, f"E{last + 1}")
    name(b, "CashLines", ws, f"E{last + 2}")
    b.found["entry_rows"] = {p: r + k for k, p in enumerate(pairs, start=1)}
    widths(ws, {"A": 34, "B": 44, "C": 30, "D": 34, "E": 16, "F": 16, "G": 16, "H": 16, "I": 16, "J": 30, "K": 34})

    # the working trial balance: adjustments and adjusted balances
    wt = xl.table(b.wb, "WorkingTB")
    for y in (F, P, C):
        xl.add_column(wt, f"Adj{y}", f"=SUMIFS(AdjustmentLines[Amount],AdjustmentLines[Account],[@AccountNumber],"
                                     f"AdjustmentLines[YearEnd],YE_{y})", MONEY)
    for y in (F, P, C):
        xl.add_column(wt, f"Adjusted{y}", f"=ROUND([@Recorded{y}]+[@Adj{y}],2)", MONEY)
    for y in (F, P, C):
        wt.ListColumns(f"Adj{y}").TotalsCalculation = 1
        wt.ListColumns(f"Adjusted{y}").TotalsCalculation = 1
    wt.TotalsRowRange.NumberFormat = MONEY
    wt.Range.Worksheet.Columns("A:Z").AutoFit()
    documentation(b)


def checks_r5(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 5"
    f = facts("r5")
    for k in ("A1", "A2", "A3", "A4"):
        row = 5 + ["A1", "A2", "A3", "A4"].index(k)
        b.check(e, f"{k}: retained earnings at 1 January {P}", f["a"][k]["re"], f"=Adjustments!E{row}")
        b.check(e, f"{k}: {P} income", f["a"][k]["P"], f"=Adjustments!F{row}")
        b.check(e, f"{k}: {C} income", f["a"][k]["C"], f"=Adjustments!G{row}")
    b.check(e, f"A1-A4: retained earnings at 1 January {P}", f["total"]["re"], "=AdjTotal_RE")
    b.check(e, f"A1-A4: {P} income", f["total"]["P"], f"=AdjTotal_{P}")
    b.check(e, f"A1-A4: {C} income", f["total"]["C"], f"=AdjTotal_{C}")
    b.check(e, f"equity effect at {ye(P)}", f["equity_p"], f"=EquityEffect_{P}")
    b.check(e, f"equity effect at {ye(C)}", f["equity_c"], f"=EquityEffect_{C}")
    b.check(e, f"adjusted net income {P}", f["adj_ni_p"], f"=AdjNI_{P}")
    b.check(e, f"adjusted net income {C}", f["adj_ni_c"], f"=AdjNI_{C}")
    for y, sp in ((P, f["split_p"]), (C, f["split_c"])):
        b.check(e, f"A1 {y}: cost of goods sold", sp["cogs"], f"=AdjA1COGS_{y}")
        b.check(e, f"A1 {y}: operating expense", sp["opx"], f"=AdjA1OPX_{y}")
    for acct, v in f["a2_accounts"]:
        b.check(e, f"A2 {C}: revenue account {acct}", v, f"=-SUMIFS(AdjustmentLines[Amount],AdjustmentLines[No],\"A2\","
                                                           f"AdjustmentLines[Account],{acct},AdjustmentLines[YearEnd],YE_{C})")
    groups = {"retained earnings": ("Account", "3030"), "operating expense": ("StatementLine", '"Operating expenses"'),
              "revenue": ("StatementLine", '"Operating revenue"')}
    for k, lines in f["entries"].items():
        for side, label, amount in lines:
            column, value = groups.get(label, ("Account", label))
            sign = "" if side == "Dr" else "-"
            b.check(e, f"{k} at {ye(C)}: {side} {label}", amount,
                    f'={sign}SUMIFS(AdjustmentLines[Amount],AdjustmentLines[No],"{k}",AdjustmentLines[{column}],{value},'
                    f'AdjustmentLines[YearEnd],YE_{C})')
    b.check(e, f"R1: current portion at {ye(P)}", f["cur_p"], f"=CurPortion_{P}")
    b.check(e, f"R1: current portion at {ye(C)}", f["cur_c"], f"=CurPortion_{C}")
    b.check(e, f"R2: 1090 credit netted at {ye(P)}", -f["c1090_p"], f"=Reclass2_{P}")
    b.check(e, f"R2: 1090 credit netted at {ye(C)}", -f["c1090_c"], f"=Reclass2_{C}")
    b.check(e, f"1046 at {ye(P)}", f["wip_p"], f"=SUMIFS(WorkingTB[Recorded{P}],WorkingTB[AccountNumber],1046)")
    b.check(e, f"1046 at {ye(C)}", f["wip_c"], f"=SUMIFS(WorkingTB[Recorded{C}],WorkingTB[AccountNumber],1046)")
    b.check(e, f"income effect as a share of materiality ({C})", f["share"], "=EffectShare", 0.00005, PCT)
    b.check(e, f"current liabilities rise at {ye(C)}, before the reclassification", f["rise"], f"=CLRise_{C}")
    b.check(e, f"working capital falls at {ye(C)}, after it", f["wc_fall"], f"=WCFall_{C}")
    b.check(e, f"current liabilities understated at {ye(P)}", f["under_p"], f"=CLRise_{P}")
    b.check(e, f"P1 allowance at {ye(C)}", f["p1"], "=PassedP1")
    b.check(e, f"P1 allowance at {ye(P)}", f["p1_prior"], "=PassedP1Prior")
    b.check(e, f"P1 on {C} income", f["p1_income"], "=PassedP1Income")
    b.check(e, f"P2 expected returns at {ye(C)}", f["p2"]["effect"], "=PassedP2")
    b.check(e, f"P2 on {C} income", f["p2"]["income"], "=PassedP2Income")
    b.check(e, f"P2 basis: returns in {C} of {P} deliveries", f["p2"]["n"],
            f"=SUMIFS(ReturnsAfterYearEnd[Returns],ReturnsAfterYearEnd[ReturnYear],{C})", 0, COUNT)
    b.check(e, f"P3 write-down at {ye(C)}", f["p3"]["effect"], "=PassedP3")
    for y, v in zip((F, P, C), f["p3"]["years"]):
        b.check(e, f"P3 basis: damaged and quality-concern returns restocked in {y}", v, f"=DamagedRestocked_{y}")
    b.check(e, "P3 basis: restocked since the first year", f["p3"]["total"], "=DamagedTotal")
    b.check(e, "returns restocked less the debits to 1040 from returns", 0, "=RestockDifference")
    b.check(e, "passed items in aggregate", f["aggregate"], "=PassedAggregate")
    b.check(e, f"passed items on {C} income", f["agg_income"], "=PassedIncome")
    b.check(e, "passed items as a share of materiality", f["agg_share"], "=PassedShare", 0.00005, PCT)
    b.check(e, "T1 freight residual", -f["residual"], "=TrivialT1")
    b.check(e, "largest imbalance of an entry", 0, "=EntryImbalance")
    b.check(e, "entry lines on cash", 0, "=CashLines", 0, COUNT)
    for y in (F, P, C):
        b.check(e, f"adjusted trial balance at {ye(y)}, debits less credits", 0, f"=ROUND(WorkingTB[[#Totals],[Adjusted{y}]],2)")
        b.check(e, f"adjustments at {ye(y)}, debits less credits", 0, f"=ROUND(WorkingTB[[#Totals],[Adj{y}]],2)")


# --- Requirement 6: the statements ----------------------------------------------------------------------------------

BS_KEYS = {"cash": "Cash", "recv": "Receivables", "inv": "Inventories", "prepaid": "Prepaid expenses and other current assets",
           "ca": "Total current assets", "ppe": "Property and equipment, net", "ta": "Total assets",
           "ap": "Accounts payable", "grni": "Goods received not invoiced", "accrued": "Accrued liabilities",
           "stax": "Sales tax payable", "credits": "Customer credits", "cur": "Current portion of notes payable",
           "cl": "Total current liabilities", "lt": "Notes payable, less current portion", "tl": "Total liabilities",
           "stock": "Common stock", "re": "Retained earnings", "equity": TSE}
IS_KEYS = {"opr": "Operating revenue", "ret": "Sales returns and allowances", "net_rev": "Net revenue",
           "cogs": "Cost of goods sold", "gm": "Gross margin", "opx": "Operating expenses", "op": "Operating income",
           "intr": "Interest expense", "loss": "Loss on disposal of equipment", "ni": "Net income"}


def r6(b: ExerciseBuild) -> None:
    F, P, C = years()
    ws = analysis_sheet(b, "Statements")
    title(ws, "Charles River: financial statements (adjusted)",
          f"Requirement 6. From the adjusted trial balances (WorkingTB) and the reclassifications; {P} restated. "
          f"The third column is the restated balance sheet at {ye(F)}, the opening balances of {P}.")
    rows = statement_block(ws, 4, [(ye(C), f"Recorded{C}", C), (f"{ye(P)} (restated)", f"Recorded{P}", P),
                                   (f"{ye(F)} (restated)", f"Recorded{F}", F)])
    b.found["statement_rows"] = rows
    cols = {C: "B", P: "C", F: "D"}
    for y, c in cols.items():
        for key, line in BS_KEYS.items():
            name(b, f"S_{key}_{y}", ws, f"{c}{rows[line]}")
        if y != F:
            for key, line in IS_KEYS.items():
                name(b, f"I_{key}_{y}", ws, f"{c}{rows[line]}")
    r = max(rows.values()) + 2
    put(ws, {f"A{r}": "Ratios and measures", f"B{r}": ye(C), f"C{r}": ye(P)})
    bold(ws, f"A{r}:C{r}")
    labels = [("Working capital", "S_ca_{y}-S_cl_{y}", MONEY, "WC"), ("Current ratio", "S_ca_{y}/S_cl_{y}", "0.00", "CR"),
              ("Quick ratio (cash and receivables)", "(S_cash_{y}+S_recv_{y})/S_cl_{y}", "0.000", "QR"),
              ("Cash net of sales tax payable", "S_cash_{y}-S_stax_{y}", MONEY, "CashNet"),
              ("Inventories as a share of current assets", "S_inv_{y}/S_ca_{y}", "0.0%", "InvShare"),
              ("Adjusted net income agrees with the schedule of adjustments", "ROUND(I_ni_{y}-AdjNI_{y},2)", MONEY, "NICheck"),
              ("Adjusted total assets less recorded total assets and the revenue cutoff",
               "ROUND(S_ta_{y}-RecTA_{y}-Cutoff_{y},2)", MONEY, "TACheck")]
    for k, (label, expr, fmt, nm) in enumerate(labels, start=1):
        ws.Cells(r + k, 1).Value = label
        for y, c in ((C, "B"), (P, "C")):
            ws.Range(f"{c}{r + k}").Formula2 = "=" + expr.format(y=y)
            ws.Range(f"{c}{r + k}").NumberFormat = fmt
            name(b, f"{nm}_{y}", ws, f"{c}{r + k}")

    # the statement of changes in stockholders' equity
    r += len(labels) + 3
    put(ws, {f"A{r}": "Statement of changes in stockholders' equity", f"B{r}": "Common stock",
             f"C{r}": "Retained earnings", f"D{r}": "Total"})
    bold(ws, f"A{r}:D{r}")
    eq = [(f"Balance, 1 January {P}, as previously reported", f"=RecStock_{F}", f"=RecRE_{F}+RecNI_{F}"),
          (f"Correction of errors in prior periods (note)", "=0", "=AdjTotal_RE"),
          (f"Balance, 1 January {P}, as restated", f"=B{r + 1}+B{r + 2}", f"=C{r + 1}+C{r + 2}"),
          (f"Net income {P} (restated)", "=0", f"=I_ni_{P}"),
          ("Distributions", "=0", f"=-(SUMIFS(WorkingTB[Recorded{P}],WorkingTB[AccountSubType],\"Contra Equity\")-"
                                  f"SUMIFS(WorkingTB[Recorded{F}],WorkingTB[AccountSubType],\"Contra Equity\"))"),
          (f"Balance, 31 December {P}", f"=SUM(B{r + 3}:B{r + 5})", f"=SUM(C{r + 3}:C{r + 5})"),
          (f"Net income {C}", "=0", f"=I_ni_{C}"),
          ("Distributions", "=0", f"=-(SUMIFS(WorkingTB[Recorded{C}],WorkingTB[AccountSubType],\"Contra Equity\")-"
                                  f"SUMIFS(WorkingTB[Recorded{P}],WorkingTB[AccountSubType],\"Contra Equity\"))"),
          (f"Balance, 31 December {C}", f"=SUM(B{r + 6}:B{r + 8})", f"=SUM(C{r + 6}:C{r + 8})")]
    for k, (label, stock, re_) in enumerate(eq, start=1):
        put(ws, {f"A{r + k}": label, f"B{r + k}": stock, f"C{r + k}": re_, f"D{r + k}": f"=B{r + k}+C{r + k}"})
    for k in (3, 6, 9):
        bold(ws, f"A{r + k}:D{r + k}")
    ws.Range(f"B{r + 1}:D{r + 9}").NumberFormat = STMT
    name(b, "RE_Reported", ws, f"C{r + 1}")
    name(b, "RE_Correction", ws, f"C{r + 2}")
    name(b, "RE_Restated", ws, f"C{r + 3}")
    name(b, f"RE_End_{P}", ws, f"C{r + 6}")
    name(b, f"RE_End_{C}", ws, f"C{r + 9}")
    put(ws, {f"A{r + 10}": "Retained earnings at the year-ends less the balance sheets",
             f"C{r + 10}": f"=ROUND(C{r + 6}-S_re_{P},2)+ROUND(C{r + 9}-S_re_{C},2)",
             f"A{r + 11}": "Retained earnings as previously reported less the ledger's at the start of the year",
             f"C{r + 11}": f"=ROUND(C{r + 1}-RecRE_{P},2)"})
    ws.Range(f"C{r + 10}:C{r + 11}").NumberFormat = MONEY
    name(b, "EquityCheck", ws, f"C{r + 10}")
    name(b, "ReportedCheck", ws, f"C{r + 11}")

    # the statement of cash flows, indirect method, adjusted and as recorded
    r += 14
    put(ws, {f"A{r}": "Statement of cash flows (indirect method)", f"B{r}": f"{C}", f"C{r}": f"{P} (restated)",
             f"D{r}": f"{C} as recorded", f"E{r}": f"{P} as recorded"})
    bold(ws, f"A{r}:E{r}")
    srow = lambda line: rows[line]
    rrow = lambda line: b.found["recorded_rows"][line]
    rec_col = {F: "B", P: "C", C: "D"}

    def adj(line: str, y: int) -> str:
        return f"Statements!{cols[y]}{srow(line)}"

    def rec(line: str, y: int) -> str:
        return f"Recorded!{rec_col[y]}{rrow(line)}"

    def other(get, y: int) -> str:
        return (f"({get('Accrued liabilities', y)}+{get('Customer credits', y)}-"
                f"{get('Prepaid expenses and other current assets', y)})")

    dep = lambda y: (f"SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],6130)+SUMIFS(LedgerSummary[Debit],"
                     f'LedgerSummary[AccountNumber],1090,LedgerSummary[EntryType],"Depreciation",LedgerSummary[Year],{y})')
    adds = lambda y: (f'SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountSubType],"Fixed Asset",LedgerSummary[Year],{y})+'
                      f'SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountSubType],"Noncurrent Asset",LedgerSummary[Year],{y})')
    noted = lambda y: (f'SUMIFS(LedgerSummary[Credit],LedgerSummary[AccountNumber],2110,LedgerSummary[EntryType],'
                       f'"Debt Reclass",LedgerSummary[Year],{y})')
    proceeds = lambda y: (f'SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],1010,LedgerSummary[EntryType],'
                          f'"Asset Disposal",LedgerSummary[Year],{y})')
    principal = lambda y: (f'SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],2110,LedgerSummary[EntryType],'
                           f'"Debt Principal Payment",LedgerSummary[Year],{y})')
    interest_paid = lambda y: (f'SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],7030,LedgerSummary[EntryType],'
                               f'"Interest Payment",LedgerSummary[Year],{y})')
    cf_lines = [
        ("Net income", lambda get, y: f"={get('Net income', y)}", "ni"),
        ("Depreciation", lambda get, y: f"={dep(y)}", "dep"),
        ("Loss on disposal of equipment", lambda get, y: f"=-{get('Loss on disposal of equipment', y)}", "loss"),
        ("Change in receivables", lambda get, y: f"=-({get('Receivables', y)}-{get('Receivables', y - 1)})", "recv"),
        ("Change in inventories (with 1090)", lambda get, y: f"=-({get('Inventories', y)}-{get('Inventories', y - 1)})", "inv"),
        ("Change in accounts payable and goods received not invoiced",
         lambda get, y: (f"=({get('Accounts payable', y)}+{get('Goods received not invoiced', y)})-"
                         f"({get('Accounts payable', y - 1)}+{get('Goods received not invoiced', y - 1)})"), "pay"),
        ("Change in sales tax payable", lambda get, y: f"={get('Sales tax payable', y)}-{get('Sales tax payable', y - 1)}", "stax"),
        ("Change in accrued and other current items", lambda get, y: f"={other(get, y)}-{other(get, y - 1)}", "other")]
    b.found["cf_rows"] = {}
    k = 1
    for label, fn, key in cf_lines:
        ws.Cells(r + k, 1).Value = label
        for y, c in ((C, "B"), (P, "C")):
            ws.Range(f"{c}{r + k}").Formula2 = fn(adj, y)
        for y, c in ((C, "D"), (P, "E")):
            ws.Range(f"{c}{r + k}").Formula2 = fn(rec, y)
        b.found["cf_rows"][key] = r + k
        k += 1
    op = r + k
    put(ws, {f"A{op}": "Net cash from operating activities", **{f"{c}{op}": f"=SUM({c}{r + 1}:{c}{op - 1})" for c in "BCDE"}})
    b.found["cf_rows"]["operating"] = op
    inv_rows = [("Purchases of property and equipment, paid in cash", lambda y: f"=-(({adds(y)})-{noted(y)})", "paid"),
                ("Proceeds from disposals", lambda y: f"={proceeds(y)}", "proceeds")]
    k = op + 1
    for label, fn, key in inv_rows:
        ws.Cells(k, 1).Value = label
        for y, c in ((C, "B"), (P, "C"), (C, "D"), (P, "E")):
            ws.Range(f"{c}{k}").Formula2 = fn(y)
        b.found["cf_rows"][key] = k
        k += 1
    put(ws, {f"A{k}": "Net cash from investing activities", **{f"{c}{k}": f"={c}{k - 2}+{c}{k - 1}" for c in "BCDE"}})
    b.found["cf_rows"]["investing"] = k
    k += 1
    put(ws, {f"A{k}": "Principal payments on notes payable",
             **{f"{c}{k}": f"=-{principal(y)}" for y, c in ((C, "B"), (P, "C"), (C, "D"), (P, "E"))}})
    put(ws, {f"A{k + 1}": "Net cash from financing activities", **{f"{c}{k + 1}": f"={c}{k}" for c in "BCDE"}})
    b.found["cf_rows"]["financing"] = k + 1
    k += 2
    put(ws, {f"A{k}": "Change in cash",
             **{f"{c}{k}": f"={c}{op}+{c}{b.found['cf_rows']['investing']}+{c}{k - 1}" for c in "BCDE"},
             f"A{k + 1}": "Cash at the beginning of the year",
             f"B{k + 1}": f"=S_cash_{P}", f"C{k + 1}": f"=S_cash_{F}", f"D{k + 1}": f"=S_cash_{P}", f"E{k + 1}": f"=S_cash_{F}",
             f"A{k + 2}": "Cash at the end of the year",
             f"B{k + 2}": f"=S_cash_{C}", f"C{k + 2}": f"=S_cash_{P}", f"D{k + 2}": f"=S_cash_{C}", f"E{k + 2}": f"=S_cash_{P}",
             f"A{k + 3}": "Change in cash less the balance sheets", **{f"{c}{k + 3}": f"=ROUND({c}{k}-({c}{k + 2}-{c}{k + 1}),2)"
                                                                       for c in "BCDE"},
             f"A{k + 4}": "Adjusted less recorded (the adjustments change no total)",
             f"B{k + 4}": f"=ROUND(B{op}-D{op},2)", f"C{k + 4}": f"=ROUND(C{op}-E{op},2)"})
    b.found["cf_rows"]["cash"] = k
    for nm, row in (("CF_Check", k + 3), ("CF_AdjVsRec", k + 4)):
        name(b, f"{nm}_{C}", ws, f"B{row}")
        name(b, f"{nm}_{P}", ws, f"C{row}")
    k += 6
    put(ws, {f"A{k}": "Supplemental information", f"B{k}": f"{C}", f"C{k}": f"{P}",
             f"A{k + 1}": "Interest paid", f"B{k + 1}": f"={interest_paid(C)}", f"C{k + 1}": f"={interest_paid(P)}",
             f"A{k + 2}": "Income taxes paid (none recorded; a matter for the CFO)", f"B{k + 2}": "=0", f"C{k + 2}": "=0",
             f"A{k + 3}": "Equipment acquired with a note payable (no cash)", f"B{k + 3}": f"={noted(C)}", f"C{k + 3}": f"={noted(P)}"})
    bold(ws, f"A{k}:C{k}")
    for nm, row in (("InterestPaid", k + 1), ("NoteFinanced", k + 3)):
        name(b, f"{nm}_{C}", ws, f"B{row}")
        name(b, f"{nm}_{P}", ws, f"C{row}")
    ws.Range(f"B{r}:E{k + 3}").NumberFormat = STMT
    for c, y in (("B", C), ("C", P)):
        for key, row in b.found["cf_rows"].items():
            name(b, f"CF_{key}_{y}", ws, f"{c}{row}")
    widths(ws, {"A": 58, "B": 20, "C": 20, "D": 20, "E": 20})
    note(ws, f"A{r}", "Investing and financing leave out what moved no cash: the equipment financed by a note (the "
                      "Debt Reclass entry moved the supplier invoice from payables to notes) and the disposals' cost "
                      "and depreciation written off. Operating activities are the change in cash less the other two "
                      "sections, and the indirect lines above reconcile net income to that amount.")
    documentation(b)


def checks_r6(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 6"
    f = facts("r6")
    for y, s in ((C, f["s_c"]), (P, f["s_p"])):
        for key in BS_KEYS:
            b.check(e, f"balance sheet {ye(y)}: {BS_KEYS[key].lower()}", s[key], f"=S_{key}_{y}")
        b.check(e, f"working capital at {ye(y)}", s["wc"], f"=WC_{y}")
        b.check(e, f"current ratio at {ye(y)}", s["cr"], f"=CR_{y}", 0.00005, "0.0000")
        b.check(e, f"quick ratio at {ye(y)}", s["qr"], f"=QR_{y}", 0.00005, "0.0000")
        b.check(e, f"cash net of sales tax at {ye(y)}", s["cash_net"], f"=CashNet_{y}")
        b.check(e, f"adjusted total assets less recorded and cutoff at {ye(y)}", 0, f"=TACheck_{y}")
        b.check(e, f"adjusted net income agrees with the schedule ({y})", 0, f"=NICheck_{y}")
    for y, i in ((P, f["i_p"]), (C, f["i_c"])):
        for key in IS_KEYS:
            value = -i[key] if key == "loss" else i[key]
            b.check(e, f"income statement {y}: {IS_KEYS[key].lower()}", value, f"=I_{key}_{y}")
    b.check(e, f"retained earnings at 1 January {P}, as previously reported", f["reported"], "=RE_Reported")
    b.check(e, "correction of prior periods", f["correction"], "=RE_Correction")
    b.check(e, f"retained earnings at 1 January {P}, as restated", f["restated"], "=RE_Restated")
    b.check(e, f"retained earnings at {ye(P)}", f["s_p"]["re"], f"=RE_End_{P}")
    b.check(e, f"retained earnings at {ye(C)}", f["s_c"]["re"], f"=RE_End_{C}")
    b.check(e, "equity statement less the balance sheets", 0, "=EquityCheck")
    b.check(e, "as previously reported less the ledger", 0, "=ReportedCheck")
    for y, cf in ((C, f["cf_c"]), (P, f["cf_p"])):
        for key in ("ni", "dep", "loss", "recv", "inv", "pay", "stax", "other", "operating", "investing", "financing",
                    "cash", "proceeds"):
            b.check(e, f"cash flows {y}: {key}", cf[key], f"=CF_{key}_{y}")
        b.check(e, f"cash flows {y}: purchases paid in cash", -cf["paid"], f"=CF_paid_{y}")
        b.check(e, f"cash flows {y}: interest paid", cf["interest_paid"], f"=InterestPaid_{y}")
        b.check(e, f"cash flows {y}: equipment financed by a note", cf["notes_financed"], f"=NoteFinanced_{y}")
        b.check(e, f"cash flows {y}: operating as recorded", cf["recorded_operating"],
                f"=Statements!{'D' if y == C else 'E'}{b.found['cf_rows']['operating']}")
        b.check(e, f"cash flows {y}: change in cash less the balance sheets", 0, f"=CF_Check_{y}")
        b.check(e, f"cash flows {y}: adjusted less recorded operating", 0, f"=CF_AdjVsRec_{y}")


# --- Requirement 7: the note schedules ------------------------------------------------------------------------------

PPE_CLASSES = [("Furniture and fixtures", 1110, 1150), ("Warehouse equipment", 1120, 1160),
               ("Office equipment", 1130, 1170), ("Manufacturing equipment", 1185, 1186)]


def load_r7(b: ExerciseBuild) -> None:
    F, P, C = years()
    ws, r = sql_results(b)
    heading(ws, f"A{r}", "Revenue by customer segment and the year the invoice was posted (the ledger's basis)")
    rows = [[s, y, v] for s, y, v in segment_revenue()]
    pasted(b, ws, f"A{r + 1}", ["CustomerSegment", "PostingYear", "Revenue"], rows, "SegmentRevenue",
           "invoice lines by customer segment and the year of their invoice's first posting (SalesInvoiceLine, "
           "SalesInvoice, Customer, and GLEntry's SalesInvoice postings)", {"Revenue": MONEY})
    b.found["sql_row"] = r + len(rows) + 4
    loaded(b, "CreditMemos", nav(b, 23, "CreditMemo", extra=[
        ("Removed Other Columns", pq.select_columns(["CreditMemoID", "CreditMemoNumber", "CreditMemoDate",
                                                     "OriginalSalesInvoiceID", "SubTotal", "TaxAmount", "GrandTotal",
                                                     "Status"])),
        ("Changed Type1", date_types(["CreditMemoDate"]))]),
        "Credit Memos", "T23_CreditMemo", {"CreditMemoDate": DATE, "SubTotal": MONEY, "TaxAmount": MONEY, "GrandTotal": MONEY})
    connection_only(b, "ServiceHours", nav(b, 13, "ServiceTimeEntry", extra=[
        ("Grouped Rows", 'Table.Group({prev}, {"ServiceEngagementID"}, {{"BillableHours", each List.Sum([BillableHours]), '
                         'type number}, {"LastWorkDate", each List.Max([WorkDate]), type datetime}})')]),
        "T13_ServiceTimeEntry by engagement")
    connection_only(b, "ServiceBilled", nav(b, 18, "ServiceBillingLine", extra=[
        ("Grouped Rows", 'Table.Group({prev}, {"ServiceEngagementID"}, {{"BilledHours", each List.Sum([BilledHours]), '
                         'type number}, {"BilledThrough", each List.Max([BillingPeriodEndDate]), type datetime}})')]),
        "T18_ServiceBillingLine by engagement")
    loaded(b, "ServiceEngagements", nav(b, 11, "ServiceEngagement", extra=[
        ("Removed Other Columns", pq.select_columns(["ServiceEngagementID", "EngagementNumber", "StartDate", "EndDate",
                                                     "PlannedHours", "Status"])),
        ("Merged Queries", pq.merge("ServiceHours", "ServiceEngagementID", "ServiceEngagementID", "ServiceHours")),
        ("Expanded ServiceHours", pq.expand("ServiceHours", ["BillableHours", "LastWorkDate"])),
        ("Merged Queries1", pq.merge("ServiceBilled", "ServiceEngagementID", "ServiceEngagementID", "ServiceBilled")),
        ("Expanded ServiceBilled", pq.expand("ServiceBilled", ["BilledHours", "BilledThrough"])),
        ("Changed Type1", date_types(["StartDate", "EndDate", "LastWorkDate", "BilledThrough"])),
        ("Sorted Rows", 'Table.Sort({prev},{{"ServiceEngagementID", Order.Ascending}})')]),
        "Services", "T11_ServiceEngagement with its billable hours (T13_ServiceTimeEntry) and billed hours "
                    "(T18_ServiceBillingLine)",
        {"StartDate": DATE, "EndDate": DATE, "LastWorkDate": DATE, "BilledThrough": DATE})
    fa = xl.table(b.wb, "FixedAssets")
    xl.add_column(fa, "FirstMonth", "=YEAR([@InServiceDate])*12+MONTH([@InServiceDate])", "0")
    xl.add_column(fa, "LastMonth", "=LET(e,YEAR([@InServiceDate])*12+MONTH([@InServiceDate])-1+[@UsefulLifeMonths],"
                                   "IF(ISNUMBER([@DisposalDate]),MIN(e,YEAR([@DisposalDate])*12+MONTH([@DisposalDate])-2),e))",
                  "0")
    xl.add_column(fa, "Monthly", "=ROUND([@OriginalCost]/[@UsefulLifeMonths],2)", MONEY)
    for y in (F, P, C):
        xl.add_column(fa, f"Dep{y}", f"=MAX(0,MIN([@LastMonth],{y}*12+11)-MAX([@FirstMonth],{y}*12)+1)*[@Monthly]", MONEY)
    note(fa.Range.Worksheet, "A1", "Depreciation by the register: straight line, each asset's cost over its life in "
                                   "months (rounded to the cent a month), from the month after it is placed in service "
                                   "through the month before disposal. Months are counted as year x 12 + month.")


def r7(b: ExerciseBuild) -> None:
    F, P, C = years()
    load_r7(b)
    ws = analysis_sheet(b, "Notes")
    title(ws, "Notes to the financial statements: schedules", "Requirement 7. Each schedule is built from the records "
                                                               "and tied to a line of the statements.")
    yc3 = [(F, "B"), (P, "C"), (C, "D")]
    led = lambda field, acct, kind, y: (f'SUMIFS(LedgerSummary[{field}],LedgerSummary[AccountNumber],{acct},'
                                        f'LedgerSummary[EntryType],"{kind}",LedgerSummary[Year],{y})')
    # property and equipment: cost
    r = 4
    heads = ["Property and equipment: cost", f"1 January {P}", f"Additions {P}", f"Disposals {P}", f"31 December {P}",
             f"Additions {C}", f"Disposals {C}", f"31 December {C}", "Roll-forward less the ledger",
             f"Additions {P}-{C} by the register less the ledger"]
    for k, h in enumerate(heads, start=1):
        ws.Cells(r, k).Value = h
    bold(ws, f"A{r}:J{r}")
    ws.Rows(r).WrapText = True
    tb = lambda acct, y: f"SUMIFS(WorkingTB[Recorded{y}],WorkingTB[AccountNumber],{acct})"
    reg_add = lambda acct, y: (f'SUMIFS(FixedAssets[OriginalCost],FixedAssets[AssetAccount],{acct},'
                               f'FixedAssets[InServiceDate],">="&DATE({y},1,1),FixedAssets[InServiceDate],"<="&YE_{y})')
    for k, (label, cost, contra) in enumerate(PPE_CLASSES, start=1):
        row = r + k
        put(ws, {f"A{row}": label, f"B{row}": f"={tb(cost, F)}",
                 f"C{row}": f"=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],{cost},LedgerSummary[Year],{P})",
                 f"D{row}": f"=-{led('Credit', cost, 'Asset Disposal', P)}", f"E{row}": f"={tb(cost, P)}",
                 f"F{row}": f"=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],{cost},LedgerSummary[Year],{C})",
                 f"G{row}": f"=-{led('Credit', cost, 'Asset Disposal', C)}", f"H{row}": f"={tb(cost, C)}",
                 f"I{row}": f"=ROUND(B{row}+C{row}+D{row}-E{row},2)+ROUND(E{row}+F{row}+G{row}-H{row},2)",
                 f"J{row}": f"=ROUND({reg_add(cost, P)}-C{row},2)+ROUND({reg_add(cost, C)}-F{row},2)"})
    tr = r + len(PPE_CLASSES) + 1
    put(ws, {f"A{tr}": "Total", **{f"{c}{tr}": f"=SUM({c}{r + 1}:{c}{tr - 1})" for c in "BCDEFGHIJ"}})
    bold(ws, f"A{tr}:J{tr}")
    for nm, c in ((f"PPECost_{F}", "B"), (f"PPEAdd_{P}", "C"), (f"PPEDisp_{P}", "D"), (f"PPECost_{P}", "E"),
                  (f"PPEAdd_{C}", "F"), (f"PPEDisp_{C}", "G"), (f"PPECost_{C}", "H"), ("PPERollCheck", "I"),
                  ("PPERegisterCheck", "J")):
        name(b, nm, ws, f"{c}{tr}")
    # accumulated depreciation
    r = tr + 2
    heads = ["Accumulated depreciation", f"1 January {P}", f"Depreciation {P}", f"Disposals {P}", f"31 December {P}",
             f"Depreciation {C}", f"Disposals {C}", f"31 December {C}", "Roll-forward less the ledger",
             f"Register's depreciation {P}-{C} less the ledger", f"Net book value {ye(C)}"]
    for k, h in enumerate(heads, start=1):
        ws.Cells(r, k).Value = h
    bold(ws, f"A{r}:K{r}")
    ws.Rows(r).WrapText = True
    reg_dep = lambda contra, y: f"SUMIFS(FixedAssets[Dep{y}],FixedAssets[ContraAccount],{contra})"
    for k, (label, cost, contra) in enumerate(PPE_CLASSES, start=1):
        row = r + k
        put(ws, {f"A{row}": label, f"B{row}": f"=-{tb(contra, F)}",
                 f"C{row}": f"={led('Credit', contra, 'Depreciation', P)}-{led('Debit', contra, 'Depreciation', P)}",
                 f"D{row}": f"=-{led('Debit', contra, 'Asset Disposal', P)}", f"E{row}": f"=-{tb(contra, P)}",
                 f"F{row}": f"={led('Credit', contra, 'Depreciation', C)}-{led('Debit', contra, 'Depreciation', C)}",
                 f"G{row}": f"=-{led('Debit', contra, 'Asset Disposal', C)}", f"H{row}": f"=-{tb(contra, C)}",
                 f"I{row}": f"=ROUND(B{row}+C{row}+D{row}-E{row},2)+ROUND(E{row}+F{row}+G{row}-H{row},2)",
                 f"J{row}": f"=ROUND({reg_dep(contra, P)}-C{row},2)+ROUND({reg_dep(contra, C)}-F{row},2)",
                 f"K{row}": f"={tb(cost, C)}+{tb(contra, C)}"})
        name(b, f"DepClass{k}_{P}", ws, f"C{row}")
        name(b, f"DepClass{k}_{C}", ws, f"F{row}")
        name(b, f"NBVClass{k}", ws, f"K{row}")
    tr2 = r + len(PPE_CLASSES) + 1
    put(ws, {f"A{tr2}": "Total", **{f"{c}{tr2}": f"=SUM({c}{r + 1}:{c}{tr2 - 1})" for c in "BCDEFGHIJK"}})
    bold(ws, f"A{tr2}:K{tr2}")
    for nm, c in ((f"AccDep_{F}", "B"), (f"Dep_{P}", "C"), (f"AccDep_{P}", "E"), (f"Dep_{C}", "F"),
                  (f"AccDep_{C}", "H"), ("AccRollCheck", "I"), ("DepRegisterCheck", "J"), ("NBV", "K")):
        name(b, nm, ws, f"{c}{tr2}")
    ws.Range(f"B5:K{tr2}").NumberFormat = STMT
    r = tr2 + 2
    put(ws, {f"A{r}": "Depreciation charged to", f"B{r}": f"{P}", f"C{r}": f"{C}",
             f"A{r + 1}": "6130 Depreciation Expense (operating expenses)",
             f"B{r + 1}": f"={led('Debit', 6130, 'Depreciation', P)}", f"C{r + 1}": f"={led('Debit', 6130, 'Depreciation', C)}",
             f"A{r + 2}": "1090 Manufacturing Cost Clearing (product cost)",
             f"B{r + 2}": f"={led('Debit', 1090, 'Depreciation', P)}", f"C{r + 2}": f"={led('Debit', 1090, 'Depreciation', C)}",
             f"A{r + 3}": "Total less the depreciation of the classes", f"B{r + 3}": f"=ROUND(B{r + 1}+B{r + 2}-Dep_{P},2)",
             f"C{r + 3}": f"=ROUND(C{r + 1}+C{r + 2}-Dep_{C},2)",
             f"A{r + 5}": "Disposals", f"B{r + 5}": f"{P}", f"C{r + 5}": f"{C}",
             f"A{r + 6}": "Asset disposed of (register)",
             f"B{r + 6}": f'=TEXTJOIN(", ",TRUE,FILTER(FixedAssets[AssetCode],YEAR(FixedAssets[DisposalDate])={P},"none"))',
             f"C{r + 6}": f'=TEXTJOIN(", ",TRUE,FILTER(FixedAssets[AssetCode],YEAR(FixedAssets[DisposalDate])={C},"none"))',
             f"A{r + 7}": "Cost removed", f"B{r + 7}": f"=-PPEDisp_{P}", f"C{r + 7}": f"=-PPEDisp_{C}",
             f"A{r + 8}": "Accumulated depreciation written off", f"B{r + 8}": f"=-SUM(D{tr2 - 4}:D{tr2 - 1})",
             f"C{r + 8}": f"=-SUM(G{tr2 - 4}:G{tr2 - 1})",
             f"A{r + 9}": "Proceeds", f"B{r + 9}": f"={led('Debit', 1010, 'Asset Disposal', P)}",
             f"C{r + 9}": f"={led('Debit', 1010, 'Asset Disposal', C)}",
             f"A{r + 10}": "Loss on disposal", f"B{r + 10}": f"=I_loss_{P}*-1", f"C{r + 10}": f"=I_loss_{C}*-1",
             f"A{r + 11}": "Cost less depreciation less proceeds less the loss",
             f"B{r + 11}": f"=ROUND(B{r + 7}-B{r + 8}-B{r + 9}-B{r + 10},2)", f"C{r + 11}": f"=ROUND(C{r + 7}-C{r + 8}-C{r + 9}-C{r + 10},2)",
             f"A{r + 13}": "Useful lives (months), shortest and longest", f"B{r + 13}": "=MIN(FixedAssets[UsefulLifeMonths])",
             f"C{r + 13}": "=MAX(FixedAssets[UsefulLifeMonths])",
             f"A{r + 14}": "Residual values in the register", f"B{r + 14}": "=SUM(FixedAssets[ResidualValue])"})
    bold(ws, f"A{r}:C{r}")
    bold(ws, f"A{r + 5}:C{r + 5}")
    ws.Range(f"B{r + 1}:C{r + 3}").NumberFormat = MONEY
    ws.Range(f"B{r + 7}:C{r + 11}").NumberFormat = MONEY
    for nm, row in (("To6130", r + 1), ("To1090", r + 2), ("DepSplitCheck", r + 3), ("DispCost", r + 7),
                    ("DispWritten", r + 8), ("DispProceeds", r + 9), ("DispLoss", r + 10), ("DispCheck", r + 11)):
        name(b, f"{nm}_{P}", ws, f"B{row}")
        name(b, f"{nm}_{C}", ws, f"C{row}")
    name(b, "LifeLow", ws, f"B{r + 13}")
    name(b, "LifeHigh", ws, f"C{r + 13}")
    name(b, "Residuals", ws, f"B{r + 14}")

    # notes payable
    r += 17
    heads = ["Notes payable", "Agreement", "Asset financed", "Principal", "Annual rate", "Term (months)", "Payment",
             "First payment", f"Balance {ye(P)}", f"Balance {ye(C)}"]
    for k, h in enumerate(heads, start=1):
        ws.Cells(r, k).Value = h
    bold(ws, f"A{r}:J{r}")
    ws.Rows(r).WrapText = True
    out = lambda y, row: (f'=IF(XLOOKUP(B{row},DebtAgreements[AgreementNumber],DebtAgreements[OriginationDate])<=YE_{y},'
                          f'SUMIFS(DebtSchedule[PrincipalAmount],DebtSchedule[DebtAgreementID],XLOOKUP(B{row},'
                          f'DebtAgreements[AgreementNumber],DebtAgreements[DebtAgreementID]),DebtSchedule[PaymentDate],'
                          f'">"&YE_{y}),0)')
    notes_ = ch17().notes_payable(data())
    for k, n in enumerate(notes_, start=1):
        row = r + k
        lk = lambda field: f"=XLOOKUP(B{row},DebtAgreements[AgreementNumber],DebtAgreements[{field}])"
        put(ws, {f"A{row}": f"Note {k}", f"B{row}": n["number"], f"C{row}": lk("AssetCode"),
                 f"D{row}": lk("PrincipalAmount"), f"E{row}": lk("AnnualInterestRate"), f"F{row}": lk("TermMonths"),
                 f"G{row}": lk("ScheduledPaymentAmount"), f"H{row}": lk("PaymentStartDate"),
                 f"I{row}": out(P, row), f"J{row}": out(C, row)})
        name(b, f"NoteBal{k}_{P}", ws, f"I{row}")
        name(b, f"NoteBal{k}_{C}", ws, f"J{row}")
    tr3 = r + len(notes_) + 1
    put(ws, {f"A{tr3}": "Total", f"I{tr3}": f"=SUM(I{r + 1}:I{tr3 - 1})", f"J{tr3}": f"=SUM(J{r + 1}:J{tr3 - 1})",
             f"A{tr3 + 1}": "Total less 2110 in the trial balance",
             f"I{tr3 + 1}": f"=ROUND(I{tr3}+{tb(2110, P)},2)", f"J{tr3 + 1}": f"=ROUND(J{tr3}+{tb(2110, C)},2)"})
    bold(ws, f"A{tr3}:J{tr3}")
    ws.Range(f"D{r + 1}:D{tr3}").NumberFormat = MONEY
    ws.Range(f"G{r + 1}:G{tr3}").NumberFormat = MONEY
    ws.Range(f"I{r + 1}:J{tr3 + 1}").NumberFormat = MONEY
    ws.Range(f"E{r + 1}:E{tr3}").NumberFormat = "0.00%"
    ws.Range(f"H{r + 1}:H{tr3}").NumberFormat = DATE
    name(b, f"NotesTotal_{C}", ws, f"J{tr3}")
    name(b, "NotesCheck", ws, f"J{tr3 + 1}")
    r = tr3 + 3
    put(ws, {f"A{r}": "Principal due", f"B{r}": "Amount"})
    bold(ws, f"A{r}:B{r}")
    for k in range(1, 6):
        y = C + k
        put(ws, {f"A{r + k}": y, f"B{r + k}": (f'=SUMIFS(DebtSchedule[PrincipalAmount],DebtSchedule[PaymentDate],'
                                               f'">="&DATE({y},1,1),DebtSchedule[PaymentDate],"<="&DATE({y},12,31))')})
        ws.Range(f"A{r + k}").HorizontalAlignment = -4131
        name(b, f"Due_{y}", ws, f"B{r + k}")
    put(ws, {f"A{r + 6}": "Later", f"B{r + 6}": f'=SUMIFS(DebtSchedule[PrincipalAmount],DebtSchedule[PaymentDate],">"&DATE({C + 5},12,31))',
             f"A{r + 7}": "Total less the notes' balance", f"B{r + 7}": f"=ROUND(SUM(B{r + 1}:B{r + 6})-NotesTotal_{C},2)",
             f"A{r + 8}": "Current portion (R1) less the principal due next year", f"B{r + 8}": f"=ROUND(CurPortion_{C}-B{r + 1},2)",
             f"A{r + 9}": "Interest paid", f"B{r + 9}": f"=InterestPaid_{C}", f"C{r + 9}": f"=InterestPaid_{P}",
             f"D{r + 9}": f"({C} and {P})"})
    ws.Range(f"B{r + 1}:C{r + 9}").NumberFormat = MONEY
    name(b, "MaturityCheck", ws, f"B{r + 7}")
    name(b, "CurrentCheck", ws, f"B{r + 8}")

    # revenue
    r += 12
    put(ws, {f"A{r}": "Revenue, adjusted (year of delivery)", f"B{r}": f"{C}", f"C{r}": f"{P}", f"D{r}": "Account"})
    bold(ws, f"A{r}:D{r}")
    rev = lambda acct, y: f"-SUMIFS(WorkingTB[Adjusted{y}],WorkingTB[AccountNumber],{acct})"
    accounts = ch17().revenue_accounts(data())
    freight = ch17().freight_account(data())[0]
    lines = [(g, accounts[g]) for g in GROUP_ORDER if g in accounts] + [("Design services", accounts["Services"]),
                                                                         ("Freight billed", freight)]
    b.found["revenue_rows"] = {}
    for k, (label, acct) in enumerate(lines, start=1):
        put(ws, {f"A{r + k}": label, f"B{r + k}": f"={rev(acct, C)}", f"C{r + k}": f"={rev(acct, P)}", f"D{r + k}": int(acct)})
        b.found["revenue_rows"][label] = r + k
    tr4 = r + len(lines) + 1
    put(ws, {f"A{tr4}": "Operating revenue", f"B{tr4}": f"=SUM(B{r + 1}:B{tr4 - 1})", f"C{tr4}": f"=SUM(C{r + 1}:C{tr4 - 1})",
             f"A{tr4 + 1}": "Less the income statement", f"B{tr4 + 1}": f"=ROUND(B{tr4}-I_opr_{C},2)",
             f"C{tr4 + 1}": f"=ROUND(C{tr4}-I_opr_{P},2)",
             f"A{tr4 + 2}": "Product revenue (the four product lines)",
             f"B{tr4 + 2}": f"=SUM(B{r + 1}:B{r + 4})", f"C{tr4 + 2}": f"=SUM(C{r + 1}:C{r + 4})",
             f"A{tr4 + 3}": "Timing: at a point in time (goods and freight)",
             f"B{tr4 + 3}": f"=B{tr4}-B{r + 5}", f"C{tr4 + 3}": f"=C{tr4}-C{r + 5}",
             f"A{tr4 + 4}": "Timing: over time (design services)", f"B{tr4 + 4}": f"=B{r + 5}", f"C{tr4 + 4}": f"=C{r + 5}"})
    bold(ws, f"A{tr4}:C{tr4}")
    name(b, "RevenueCheck", ws, f"B{tr4 + 1}")
    name(b, "RevenueCheckPrior", ws, f"C{tr4 + 1}")
    for nm, row in (("Product", tr4 + 2), ("PointInTime", tr4 + 3), ("OverTime", tr4 + 4)):
        name(b, f"{nm}_{C}", ws, f"B{row}")
        name(b, f"{nm}_{P}", ws, f"C{row}")
    r7f = facts("r7")
    put(ws, {f"A{tr4 + 6}": "Cross-check with Exercise 14.2's revenue by ship date", f"B{tr4 + 6}": f"{C}",
             f"C{tr4 + 6}": f"{P}",
             f"A{tr4 + 7}": "Revenue by ship date (Exercise 14.2's control total)", f"B{tr4 + 7}": r7f["ship_c"],
             f"C{tr4 + 7}": r7f["ship_p"],
             f"A{tr4 + 8}": "  plus the shipment lines never invoiced", f"B{tr4 + 8}": f"=UnbilledValue_{C}", f"C{tr4 + 8}": f"=UnbilledValue_{P}",
             f"A{tr4 + 9}": "Product revenue less the ship-date revenue and the unbilled lines",
             f"B{tr4 + 9}": f"=ROUND(Product_{C}-B{tr4 + 7}-B{tr4 + 8},2)", f"C{tr4 + 9}": f"=ROUND(Product_{P}-C{tr4 + 7}-C{tr4 + 8},2)"})
    bold(ws, f"A{tr4 + 6}:C{tr4 + 6}")
    ws.Range(f"B{tr4 + 7}:C{tr4 + 7}").Font.Color = BLUE
    note(ws, f"B{tr4 + 7}", "Typed from Exercise 14.2 (revenue by ship date through the inactive ShipmentDate "
                            "relationship), a control total the book already trusts.")
    name(b, f"ShipCheck_{C}", ws, f"B{tr4 + 9}")
    name(b, f"ShipCheck_{P}", ws, f"C{tr4 + 9}")
    ws.Range(f"B{r + 1}:C{tr4 + 9}").NumberFormat = STMT
    # by segment
    r = tr4 + 12
    put(ws, {f"A{r}": "Revenue by customer segment, adjusted (products and services)", f"B{r}": f"{C}", f"C{r}": f"{P}"})
    bold(ws, f"A{r}:C{r}")
    segs = sorted({s for s, _, _ in segment_revenue()}, key=lambda s: -sum(v for x, y, v in segment_revenue()
                                                                           if x == s and y == C))
    seg_rows = b.found["segment_rows"]
    cut_col = {F: "B", P: "C", C: "D"}
    b.found["segment_note_rows"] = {}
    for k, s in enumerate(segs, start=1):
        cells = {}
        for y, c in ((C, "B"), (P, "C")):
            f = f'=SUMIFS(SegmentRevenue[Revenue],SegmentRevenue[CustomerSegment],"{s}",SegmentRevenue[PostingYear],{y})'
            if s in seg_rows:
                f += f"+Cutoff!{cut_col[y]}{seg_rows[s]}-Cutoff!{cut_col[y - 1]}{seg_rows[s]}"
            cells[f"{c}{r + k}"] = f
        put(ws, {f"A{r + k}": s, **cells})
        b.found["segment_note_rows"][s] = r + k
    tr5 = r + len(segs) + 1
    put(ws, {f"A{tr5}": "Total less product and design-services revenue",
             f"B{tr5}": f"=ROUND(SUM(B{r + 1}:B{tr5 - 1})-Product_{C}-OverTime_{C},2)",
             f"C{tr5}": f"=ROUND(SUM(C{r + 1}:C{tr5 - 1})-Product_{P}-OverTime_{P},2)"})
    ws.Range(f"B{r + 1}:C{tr5}").NumberFormat = STMT
    name(b, f"SegmentCheck_{C}", ws, f"B{tr5}")
    name(b, f"SegmentCheck_{P}", ws, f"C{tr5}")
    # contract balances and services
    r = tr5 + 3
    put(ws, {f"A{r}": "Contract balances", f"B{r}": f"1 January {P}", f"C{r}": ye(P), f"D{r}": ye(C),
             f"A{r + 1}": "Receivables (adjusted; each includes the opening line that no document supports)",
             f"B{r + 1}": f"=S_recv_{F}", f"C{r + 1}": f"=S_recv_{P}", f"D{r + 1}": f"=S_recv_{C}",
             f"A{r + 2}": "Contract assets", f"B{r + 2}": "=0", f"C{r + 2}": "=0", f"D{r + 2}": "=0",
             f"A{r + 3}": "Contract liabilities (2070 Deferred Revenue)",
             f"B{r + 3}": f"=-{tb(2070, F)}", f"C{r + 3}": f"=-{tb(2070, P)}", f"D{r + 3}": f"=-{tb(2070, C)}",
             f"A{r + 4}": "Customer credits awaiting refund (2060)",
             f"B{r + 4}": f"=S_credits_{F}", f"C{r + 4}": f"=S_credits_{P}", f"D{r + 4}": f"=S_credits_{C}",
             f"A{r + 5}": "Postings to 2070 ever", f"D{r + 5}": "=COUNTIFS(LedgerSummary[AccountNumber],2070)",
             f"A{r + 6}": "Credit memos with status Issued: count and total",
             f"C{r + 6}": '=COUNTIFS(CreditMemos[Status],"Issued")',
             f"D{r + 6}": '=SUMIFS(CreditMemos[GrandTotal],CreditMemos[Status],"Issued")'})
    bold(ws, f"A{r}:D{r}")
    ws.Range(f"B{r + 1}:D{r + 4}").NumberFormat = STMT
    ws.Range(f"D{r + 6}").NumberFormat = MONEY
    for y, c in yc3:
        name(b, f"Recv_{y}", ws, f"{c}{r + 1}")
        name(b, f"Credits_{y}", ws, f"{c}{r + 4}")
    name(b, "Postings2070", ws, f"D{r + 5}")
    name(b, "IssuedCount", ws, f"C{r + 6}")
    name(b, "IssuedTotal", ws, f"D{r + 6}")
    r += 8
    put(ws, {f"A{r}": "Design services: billable hours worked and billed",
             f"A{r + 1}": "Billable hours worked (ServiceTimeEntry)", f"B{r + 1}": "=SUM(ServiceEngagements[BillableHours])",
             f"A{r + 2}": "Hours billed (ServiceBillingLine)", f"B{r + 2}": "=SUM(ServiceEngagements[BilledHours])",
             f"A{r + 3}": "Worked less billed", f"B{r + 3}": f"=ROUND(B{r + 1}-B{r + 2},2)",
             f"A{r + 4}": "Last day of work recorded", f"B{r + 4}": "=MAX(ServiceEngagements[LastWorkDate])",
             f"A{r + 5}": "Engagements not yet Billed: number, status, end date, planned, worked, billed, worked through",
             f"A{r + 6}": ('=LET(t,ServiceEngagements,keep,ServiceEngagements[Status]<>"Billed",FILTER(HSTACK('
                           'ServiceEngagements[EngagementNumber],ServiceEngagements[Status],ServiceEngagements[EndDate],'
                           'ServiceEngagements[PlannedHours],ServiceEngagements[BillableHours],ServiceEngagements[BilledHours],'
                           'ServiceEngagements[LastWorkDate]),keep,"none"))')})
    bold(ws, f"A{r}")
    ws.Range(f"B{r + 1}:B{r + 3}").NumberFormat = "#,##0.00"
    ws.Range(f"B{r + 4}").NumberFormat = DATE
    ws.Range(f"C{r + 6}:C{r + 8}").NumberFormat = DATE
    ws.Range(f"G{r + 6}:G{r + 8}").NumberFormat = DATE
    name(b, "BillableHours", ws, f"B{r + 1}")
    name(b, "UnbilledHours", ws, f"B{r + 3}")
    b.found["engagement_row"] = r + 6
    # accrued liabilities and inventories
    r += 10
    tba = lambda accts, y: "+".join(f"SUMIFS(WorkingTB[Adjusted{y}],WorkingTB[AccountNumber],{a})" for a in accts)
    put(ws, {f"A{r}": "Accrued liabilities", f"B{r}": ye(C), f"C{r}": ye(P),
             f"A{r + 1}": "Payroll and related (2030-2033: wages owed, withholdings and employer taxes not yet remitted)",
             f"B{r + 1}": f"=-({tba([2030, 2031, 2032, 2033], C)})", f"C{r + 1}": f"=-({tba([2030, 2031, 2032, 2033], P)})",
             f"A{r + 2}": "  of which the opening line of 2030, unchanged since the opening entry",
             f"B{r + 2}": "=Open2030", f"C{r + 2}": "=Open2030",
             f"A{r + 3}": "  of which the wages owed for the last days of the year (A1)",
             f"B{r + 3}": f"=Payroll_{C}", f"C{r + 3}": f"=Payroll_{P}",
             f"A{r + 4}": "Sales commissions (2034)", f"B{r + 4}": f"=-({tba([2034], C)})", f"C{r + 4}": f"=-({tba([2034], P)})",
             f"A{r + 5}": "Accrued expenses (2040, after A3)", f"B{r + 5}": f"=-({tba([2040], C)})", f"C{r + 5}": f"=-({tba([2040], P)})",
             f"A{r + 6}": "Interest (2080, A4)", f"B{r + 6}": f"=-({tba([2080], C)})", f"C{r + 6}": f"=-({tba([2080], P)})",
             f"A{r + 7}": "Other (2070, 2090)", f"B{r + 7}": f"=-({tba([2070, 2090], C)})", f"C{r + 7}": f"=-({tba([2070, 2090], P)})",
             f"A{r + 8}": "Total", f"B{r + 8}": f"=B{r + 1}+SUM(B{r + 4}:B{r + 7})", f"C{r + 8}": f"=C{r + 1}+SUM(C{r + 4}:C{r + 7})",
             f"A{r + 9}": "Total less the balance sheet", f"B{r + 9}": f"=ROUND(B{r + 8}-S_accrued_{C},2)",
             f"C{r + 9}": f"=ROUND(C{r + 8}-S_accrued_{P},2)"})
    bold(ws, f"A{r}:C{r}")
    bold(ws, f"A{r + 8}:C{r + 8}")
    ws.Range(f"B{r + 1}:C{r + 9}").NumberFormat = STMT
    for nm, row in (("AccPayroll", r + 1), ("AccComm", r + 4), ("AccExp", r + 5), ("AccInt", r + 6), ("AccCheck", r + 9)):
        name(b, f"{nm}_{C}", ws, f"B{row}")
        name(b, f"{nm}_{P}", ws, f"C{row}")
    r += 11
    put(ws, {f"A{r}": "Inventories", f"B{r}": ye(C), f"C{r}": ye(P),
             f"A{r + 1}": "Finished goods, at standard cost (1040)", f"B{r + 1}": f"={tba([1040], C)}", f"C{r + 1}": f"={tba([1040], P)}",
             f"A{r + 2}": "Materials and packaging, at purchase-order cost (1045; price variances to cost of goods sold)",
             f"B{r + 2}": f"={tba([1045], C)}", f"C{r + 2}": f"={tba([1045], P)}",
             f"A{r + 3}": "Work in process, net of the 1090 credit (1046 and 1090, after R2)",
             f"B{r + 3}": f"={tba([1046, 1090], C)}", f"C{r + 3}": f"={tba([1046, 1090], P)}",
             f"A{r + 4}": "Total", f"B{r + 4}": f"=SUM(B{r + 1}:B{r + 3})", f"C{r + 4}": f"=SUM(C{r + 1}:C{r + 3})",
             f"A{r + 5}": "Total less the balance sheet", f"B{r + 5}": f"=ROUND(B{r + 4}-S_inv_{C},2)",
             f"C{r + 5}": f"=ROUND(C{r + 4}-S_inv_{P},2)",
             f"A{r + 6}": "1090 after R2", f"B{r + 6}": f"={tba([1090], C)}", f"C{r + 6}": f"={tba([1090], P)}"})
    bold(ws, f"A{r}:C{r}")
    bold(ws, f"A{r + 4}:C{r + 4}")
    ws.Range(f"B{r + 1}:C{r + 6}").NumberFormat = STMT
    for nm, row in (("InvFG", r + 1), ("InvMat", r + 2), ("InvWIP", r + 3), ("InvCheck", r + 5), ("Inv1090", r + 6)):
        name(b, f"{nm}_{C}", ws, f"B{row}")
        name(b, f"{nm}_{P}", ws, f"C{row}")
    widths(ws, {"A": 60, "B": 18, "C": 18, "D": 18, "E": 16, "F": 16, "G": 16, "H": 16, "I": 18, "J": 18, "K": 18})
    r += 8
    r = model_answer(ws, r, MA + ": the text of the required notes", note_texts(), last_col=8)
    documentation(b)


def note_texts() -> list[str]:
    F, P, C = years()
    f7, f6, f5 = facts("r7"), facts("r6"), facts("r5")
    cls = f7["classes"]
    n1, n2 = f7["notes"][0], f7["notes"][-1]
    mats = "; ".join(f"{y} {money(v)}" for y, v in f7["maturities"])
    segs = "; ".join(f"{s['name']} {money(s['c'])} ({money(s['p'])})" for s in f7["segments"])
    lines = "; ".join(f"{x['label']} {money(x['c'])} ({money(x['p'])})" for x in f7["revenue"])
    return [
        f"Property and equipment. Property and equipment are stated at cost less accumulated depreciation, computed on "
        f"the straight-line method over useful lives of {f7['life_low']} to {f7['life_high']} months with no residual "
        "value, from the month after an asset is placed in service through the month before its disposal. Cost was "
        f"{money(f7['cost_f'])} at 1 January {P}; additions of {money(f7['add_p']['total'])} and the disposal of "
        f"{f7['disp_p']['code']} (cost {money(f7['disp_p']['cost'])}, accumulated depreciation "
        f"{money(f7['disp_p']['written'])}, proceeds {money(f7['disp_p']['proceeds'])}, loss {money(f7['disp_p']['loss'])}) "
        f"brought it to {money(f7['cost_p'])}; in {C}, {', '.join(f7['add_c']['codes'])} was acquired for "
        f"{money(f7['add_c']['total'])} with a note payable (a noncash transaction), and {f7['disp_c']['code']} was "
        f"disposed of with no proceeds (cost {money(f7['disp_c']['cost'])}, accumulated depreciation "
        f"{money(f7['disp_c']['written'])}, loss {money(f7['disp_c']['loss'])}), for a cost of {money(f7['cost_c'])}. "
        f"Accumulated depreciation was {money(f7['acc_p'])} and {money(f7['acc_c'])}. Depreciation was "
        f"{money(f7['dep_p'])} in {P} and {money(f7['dep_c'])} in {C} (" +
        ", ".join(f"{c['name']} {money(c['c'])}" for c in cls) + f" in {C}); {money(f7['to1090_c'])} of it was "
        "charged to manufacturing cost and the rest to operating expenses.",
        f"Notes payable. Note 1, {money(n1['principal'])} at {n1['rate']}, is repayable in {n1['term']} monthly "
        f"payments of {money(n1['payment'])} from {n1['start']} and financed equipment {n1['asset']}; note 2, "
        f"{money(n2['principal'])} at {n2['rate']}, is repayable in {n2['term']} monthly payments of "
        f"{money(n2['payment'])} from {n2['start']} and financed equipment {n2['asset']}. The balances at {ye(C)} were "
        f"{money(n1['c'])} and {money(n2['c'])}, {money(f7['notes_total'])} in all ({money(n1['p'])} at {ye(P)}), of "
        f"which {money(f5['cur_c'])} is due within a year and shown as current. Principal due: {mats}. Interest paid "
        f"was {money(f6['cf_c']['interest_paid'])} in {C} and {money(f6['cf_p']['interest_paid'])} in {P}. The records "
        "link each note to the asset it financed; they do not show a security interest, so the note claims none.",
        f"Revenue. Revenue from goods and freight is recognized at a point in time, when the goods are delivered; "
        f"design services are recognized over time, as the hours are worked and billed monthly. Revenue by product "
        f"line, {C} ({P}): {lines}; design services {money(f7['svc_c'])} ({money(f7['svc_p'])}); freight "
        f"{money(f7['fr_c'])} ({money(f7['fr_p'])}). By customer segment: {segs}. At a point in time "
        f"{money(f7['point_c'])} ({money(f7['point_p'])}); over time {money(f7['svc_c'])} ({money(f7['svc_p'])}). "
        f"Receivables were {money(f7['recv_f'])} at 1 January {P}, {money(f7['recv_p'])}, and {money(f7['recv_c'])}; "
        "there are no contract assets and no contract liabilities; customer credits awaiting refund were "
        f"{money(f7['credits'][0])}, {money(f7['credits'][1])}, and {money(f7['credits'][2])}. No service work was "
        "done and not billed at a year-end. The revenue of each year includes the shipments delivered in it and "
        "invoiced later or not yet invoiced (note on the correction of the 2025 statements).",
        f"Accrued liabilities. At {ye(C)} ({ye(P)}): payroll and related {money(f7['s_c']['payroll'])} "
        f"({money(f7['s_p']['payroll'])}), including wages owed for the last days of the year and "
        f"{money(f7['opening_2030'])} carried from the opening balances; sales commissions {money(f7['s_c']['comm'])} "
        f"({money(f7['s_p']['comm'])}); accrued expenses {money(f7['s_c']['accexp'])} ({money(f7['s_p']['accexp'])}); "
        f"interest {money(f7['s_c']['intr'])} ({money(f7['s_p']['intr'])}); total {money(f7['s_c']['accrued'])} "
        f"({money(f7['s_p']['accrued'])}).",
        f"Correction of the {P} statements. The {P} statements given to the shareholders were prepared from the ledger "
        "without year-end adjustments. They have been restated to accrue the payroll owed for the last days of each "
        "year, to recognize revenue in the year of delivery, to reverse accruals open longer than the invoicing window, "
        "and to accrue interest on the notes payable. The correction reduced retained earnings at 1 January "
        f"{P} by {money(-f5['total']['re'])} (from {money(f6['reported'])} to {money(f6['restated'])}) and {P} net "
        f"income by {money(-f5['total']['P'])}, to {money(f5['adj_ni_p'])}; it increased {C} net income by "
        f"{money(f5['total']['C'])}, to {money(f5['adj_ni_c'])}. Current liabilities at {ye(P)} increased by "
        f"{money(f5['under_p'])} before the current portion of the notes was reclassified. No adjustment affected "
        "cash or the totals of the statements of cash flows."]


def checks_r7(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 7"
    f = facts("r7")
    b.check(e, f"cost at 1 January {P}", f["cost_f"], f"=PPECost_{F}")
    b.check(e, f"additions {P}", f["add_p"]["total"], f"=PPEAdd_{P}")
    b.check(e, f"disposals {P} (cost)", -f["disp_p"]["cost"], f"=PPEDisp_{P}")
    b.check(e, f"cost at {ye(P)}", f["cost_p"], f"=PPECost_{P}")
    b.check(e, f"additions {C}", f["add_c"]["total"], f"=PPEAdd_{C}")
    b.check(e, f"disposals {C} (cost)", -f["disp_c"]["cost"], f"=PPEDisp_{C}")
    b.check(e, f"cost at {ye(C)}", f["cost_c"], f"=PPECost_{C}")
    b.check(e, "cost roll-forward less the ledger", 0, "=PPERollCheck")
    b.check(e, "additions by the register less the ledger", 0, "=PPERegisterCheck")
    b.check(e, f"accumulated depreciation at 1 January {P}", f["acc_f"], f"=AccDep_{F}")
    b.check(e, f"accumulated depreciation at {ye(P)}", f["acc_p"], f"=AccDep_{P}")
    b.check(e, f"accumulated depreciation at {ye(C)}", f["acc_c"], f"=AccDep_{C}")
    b.check(e, "accumulated depreciation roll-forward less the ledger", 0, "=AccRollCheck")
    b.check(e, "the register's depreciation less the ledger's", 0, "=DepRegisterCheck")
    b.check(e, f"depreciation {P}", f["dep_p"], f"=Dep_{P}")
    b.check(e, f"depreciation {C}", f["dep_c"], f"=Dep_{C}")
    for k, c in enumerate(f["classes"], start=1):
        b.check(e, f"depreciation {P}, {c['name']}", c["p"], f"=DepClass{k}_{P}")
        b.check(e, f"depreciation {C}, {c['name']}", c["c"], f"=DepClass{k}_{C}")
    for k, v in enumerate(f["nbv"], start=1):
        b.check(e, f"net book value at {ye(C)}, {PPE_CLASSES[k - 1][0].lower()}", v, f"=NBVClass{k}")
    for y, key in ((P, "p"), (C, "c")):
        b.check(e, f"depreciation to 6130, {y}", f[f"to6130_{key}"], f"=To6130_{y}")
        b.check(e, f"depreciation to 1090, {y}", f[f"to1090_{key}"], f"=To1090_{y}")
        b.check(e, f"depreciation split less the classes, {y}", 0, f"=DepSplitCheck_{y}")
        d = f[f"disp_{key}"]
        b.check(e, f"disposal {y}: accumulated depreciation written off", d["written"], f"=DispWritten_{y}")
        b.check(e, f"disposal {y}: proceeds", d["proceeds"], f"=DispProceeds_{y}")
        b.check(e, f"disposal {y}: loss", d["loss"], f"=DispLoss_{y}")
        b.check(e, f"disposal {y}: cost less depreciation, proceeds, and loss", 0, f"=DispCheck_{y}")
    b.check(e, "useful lives, shortest (months)", f["life_low"], "=LifeLow", 0, COUNT)
    b.check(e, "useful lives, longest (months)", f["life_high"], "=LifeHigh", 0, COUNT)
    b.check(e, "residual values", 0, "=Residuals")
    for k, n in enumerate(f["notes"], start=1):
        b.check(e, f"note {k} balance at {ye(C)}", n["c"], f"=NoteBal{k}_{C}")
        if n["p"] is not None:
            b.check(e, f"note {k} balance at {ye(P)}", n["p"], f"=NoteBal{k}_{P}")
    b.check(e, f"notes payable at {ye(C)}", f["notes_total"], f"=NotesTotal_{C}")
    b.check(e, "notes less 2110", 0, "=NotesCheck")
    for y, v in f["maturities"]:
        if y <= C + 5:
            b.check(e, f"principal due in {y}", v, f"=Due_{y}")
    b.check(e, "maturities less the notes' balance", 0, "=MaturityCheck")
    b.check(e, "current portion less the principal due next year", 0, "=CurrentCheck")
    for x in f["revenue"]:
        row = b.found["revenue_rows"][x["label"]]
        b.check(e, f"revenue {C}, {x['label']}", x["c"], f"=Notes!B{row}")
        b.check(e, f"revenue {P}, {x['label']}", x["p"], f"=Notes!C{row}")
    for y, key, c in ((C, "c", "B"), (P, "p", "C")):
        b.check(e, f"revenue {y}, design services", f[f"svc_{key}"], f"=Notes!{c}{b.found['revenue_rows']['Design services']}")
        b.check(e, f"revenue {y}, freight", f[f"fr_{key}"], f"=Notes!{c}{b.found['revenue_rows']['Freight billed']}")
        b.check(e, f"revenue {y}, at a point in time", f[f"point_{key}"], f"=PointInTime_{y}")
        b.check(e, f"revenue {y}, over time", f[f"svc_{key}"], f"=OverTime_{y}")
        b.check(e, f"revenue by product line less the income statement, {y}", 0,
                "=RevenueCheck" if y == C else "=RevenueCheckPrior")
        b.check(e, f"revenue by segment less product and services, {y}", 0, f"=SegmentCheck_{y}")
        b.check(e, f"product revenue less ship-date revenue and unbilled lines, {y}", 0, f"=ShipCheck_{y}")
    b.check(e, f"product revenue {P}", f["product_p"], f"=Product_{P}")
    for s in f["segments"]:
        row = b.found["segment_note_rows"][s["name"]]
        b.check(e, f"revenue {C}, segment {s['name']}", s["c"], f"=Notes!B{row}")
        b.check(e, f"revenue {P}, segment {s['name']}", s["p"], f"=Notes!C{row}")
    for y, key in ((F, "recv_f"), (P, "recv_p"), (C, "recv_c")):
        b.check(e, f"receivables (contract balance) at {ye(y)}", f[key], f"=Recv_{y}")
    for y, v in zip((F, P, C), f["credits"]):
        b.check(e, f"customer credits (2060) at {ye(y)}", v, f"=Credits_{y}")
    b.check(e, "postings to 2070 Deferred Revenue", 0, "=Postings2070", 0, COUNT)
    b.check(e, "Issued credit memos", f["issued_n"], "=IssuedCount", 0, COUNT)
    b.check(e, "Issued credit memos, total (the 2060 balance)", f["credits"][-1], "=IssuedTotal")
    b.check(e, "billable hours worked", f["billable"], "=BillableHours", 0.005, "#,##0.00")
    b.check(e, "billable hours not billed", 0, "=UnbilledHours", 0.005, "#,##0.00")
    for k, g in enumerate(f["engs"]):
        row = b.found["engagement_row"] + k
        b.check(e, f"engagement {g['id']} not yet Billed: billed hours", g["billed"], f"=Notes!F{row}", 0.005, "#,##0.00")
        b.check(e, f"engagement {g['id']} not yet Billed: planned hours", g["planned"], f"=Notes!D{row}", 0.005, "#,##0.00")
    for y, s in ((C, f["s_c"]), (P, f["s_p"])):
        b.check(e, f"accrued payroll and related at {ye(y)}", s["payroll"], f"=AccPayroll_{y}")
        b.check(e, f"accrued commissions at {ye(y)}", s["comm"], f"=AccComm_{y}")
        b.check(e, f"accrued expenses at {ye(y)}", s["accexp"], f"=AccExp_{y}")
        b.check(e, f"accrued interest at {ye(y)}", s["intr"], f"=AccInt_{y}")
        b.check(e, f"accrued liabilities less the balance sheet at {ye(y)}", 0, f"=AccCheck_{y}")
        b.check(e, f"finished goods at {ye(y)}", s["fg"], f"=InvFG_{y}")
        b.check(e, f"materials and packaging at {ye(y)}", s["mat"], f"=InvMat_{y}")
        b.check(e, f"work in process net of 1090 at {ye(y)}", s["wip"], f"=InvWIP_{y}")
        b.check(e, f"inventories less the balance sheet at {ye(y)}", 0, f"=InvCheck_{y}")
        b.check(e, f"1090 after R2 at {ye(y)}", 0, f"=Inv1090_{y}")


# --- Requirement 8: past the balance-sheet date ------------------------------------------------------------------------

def load_r8(b: ExerciseBuild) -> None:
    F, P, C = years()
    end = f"#datetime({C}, 12, 31, 0, 0, 0)"
    connection_only(b, "Payments", nav(b, 39, "DisbursementPayment", extra=[
        ("Removed Other Columns", pq.select_columns(["DisbursementID", "PaymentDate", "SupplierID", "PurchaseInvoiceID",
                                                     "Amount"]))]), "T39_DisbursementPayment")
    connection_only(b, "PaymentsByInvoice", pq.steps_query([
        ("Source", "Payments"),
        ("Added PaidByYearEnd", pq.add_custom("PaidByYearEnd", f"if [PaymentDate] <= {end} then [Amount] else 0")),
        ("Added PaidAfterYearEnd", pq.add_custom("PaidAfterYearEnd", f"if [PaymentDate] > {end} then [Amount] else 0")),
        ("Added PaymentAfterYearEnd", pq.add_custom("PaymentAfterYearEnd", f"if [PaymentDate] > {end} then 1 else 0")),
        ("Grouped Rows", 'Table.Group({prev}, {"PurchaseInvoiceID"}, {{"PaidByYearEnd", each List.Sum([PaidByYearEnd]), '
                         'type number}, {"PaidAfterYearEnd", each List.Sum([PaidAfterYearEnd]), type number}, '
                         '{"PaymentsAfterYearEnd", each List.Sum([PaymentAfterYearEnd]), Int64.Type}})')]),
        "payments by supplier invoice, by the year-end and after it")
    loaded(b, "PaymentsByDate", pq.steps_query([
        ("Source", "Payments"),
        ("Filtered Rows", f"Table.SelectRows({{prev}}, each [PaymentDate] >= #datetime({C}, 1, 1, 0, 0, 0))"),
        ("Grouped Rows", 'Table.Group({prev}, {"PaymentDate"}, {{"Payments", each Table.RowCount(_), Int64.Type}, '
                         '{"Amount", each List.Sum([Amount]), type number}})'),
        ("Changed Type", date_types(["PaymentDate"])),
        ("Sorted Rows", 'Table.Sort({prev},{{"PaymentDate", Order.Ascending}})')]),
        "Payments", f"T39_DisbursementPayment from 1 January {C}, by payment date",
        {"PaymentDate": DATE, "Amount": MONEY})
    loaded(b, "SupplierInvoices", nav(b, 37, "PurchaseInvoice", extra=[
        ("Removed Other Columns", pq.select_columns(["PurchaseInvoiceID", "InvoiceNumber", "SupplierID", "InvoiceDate",
                                                     "ReceivedDate", "DueDate", "GrandTotal"])),
        ("Filtered Rows", f"Table.SelectRows({{prev}}, each [ReceivedDate] >= #datetime({C}, 7, 1, 0, 0, 0))"),
        ("Merged Queries", pq.merge("PaymentsByInvoice", "PurchaseInvoiceID", "PurchaseInvoiceID", "PaymentsByInvoice")),
        ("Expanded PaymentsByInvoice", pq.expand("PaymentsByInvoice", ["PaidByYearEnd", "PaidAfterYearEnd",
                                                                       "PaymentsAfterYearEnd"])),
        ("Replaced Value", 'Table.ReplaceValue({prev},null,0,Replacer.ReplaceValue,{"PaidByYearEnd", "PaidAfterYearEnd", '
                           '"PaymentsAfterYearEnd"})'),
        ("Changed Type1", date_types(["InvoiceDate", "ReceivedDate", "DueDate"]))]),
        "Supplier Invoices", f"T37_PurchaseInvoice received from 1 July {C}, with what was paid by the year-end and after",
        {"InvoiceDate": DATE, "ReceivedDate": DATE, "DueDate": DATE, "GrandTotal": MONEY, "PaidByYearEnd": MONEY,
         "PaidAfterYearEnd": MONEY})


def r8(b: ExerciseBuild) -> None:
    F, P, C = years()
    N = C + 1
    load_r8(b)
    ws = analysis_sheet(b, "Later Events")
    title(ws, f"After {ye(C)}: the records, later events, and going concern",
          "Requirement 8. What the records after the year-end contain and cannot contain, the search for unrecorded "
          "liabilities, and the conditions a going-concern evaluation weighs.")
    after = f'">"&YEAR(YE_{C})'
    put(ws, {"A4": "The records after the year-end", "B4": "Value",
             "A5": "Ledger rows", "B5": f"=SUMIFS(LedgerSummary[Rows],LedgerSummary[Year],{after})",
             "A6": "Source document types", "B6": f'=TEXTJOIN(", ",TRUE,UNIQUE(FILTER(LedgerSummary[SourceDocumentType],'
                                                  f'LedgerSummary[Year]>YEAR(YE_{C}))))',
             "A7": "Accounts", "B7": f'=TEXTJOIN(", ",TRUE,UNIQUE(FILTER(LedgerSummary[AccountNumber],'
                                     f'LedgerSummary[Year]>YEAR(YE_{C}))))',
             "A8": "Debits to 2010 Accounts Payable",
             "B8": f"=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],2010,LedgerSummary[Year],{after})",
             "A9": "Credits to 1010 Cash", "B9": f"=SUMIFS(LedgerSummary[Credit],LedgerSummary[AccountNumber],1010,LedgerSummary[Year],{after})",
             "A10": "First posting date", "B10": f"=MINIFS(LedgerSummary[FirstPostingDate],LedgerSummary[Year],{after})",
             "A11": "Last posting date", "B11": f"=MAXIFS(LedgerSummary[LastPostingDate],LedgerSummary[Year],{after})",
             "A12": "Supplier payments", "B12": f'=SUMIFS(PaymentsByDate[Payments],PaymentsByDate[PaymentDate],">"&YE_{C})',
             "A13": "  their amount", "B13": f'=SUMIFS(PaymentsByDate[Amount],PaymentsByDate[PaymentDate],">"&YE_{C})',
             "A14": "Supplier payments in the same weeks of the year before",
             "B14": (f'=SUMIFS(PaymentsByDate[Payments],PaymentsByDate[PaymentDate],">="&DATE({C},1,1),'
                     f'PaymentsByDate[PaymentDate],"<="&DATE({C},MONTH(B11),DAY(B11)))'),
             "A15": "  their amount",
             "B15": (f'=SUMIFS(PaymentsByDate[Amount],PaymentsByDate[PaymentDate],">="&DATE({C},1,1),'
                     f'PaymentsByDate[PaymentDate],"<="&DATE({C},MONTH(B11),DAY(B11)))')})
    bold(ws, "A4:B4")
    ws.Range("B5").NumberFormat = COUNT
    ws.Range("B8:B9").NumberFormat = MONEY
    ws.Range("B10:B11").NumberFormat = DATE
    ws.Range("B12").NumberFormat = COUNT
    ws.Range("B14").NumberFormat = COUNT
    ws.Range("B13").NumberFormat = MONEY
    ws.Range("B15").NumberFormat = MONEY
    for nm, row in (("AfterRows", 5), ("AfterTypes", 6), ("AfterDebits2010", 8), ("AfterCredits1010", 9),
                    ("AfterFirst", 10), ("AfterLast", 11), ("AfterPayments", 12), ("AfterPaid", 13), ("SameWeeks", 14),
                    ("SameWeeksPaid", 15)):
        name(b, nm, ws, f"B{row}")
    paid = "SupplierInvoices[PaidAfterYearEnd]"
    put(ws, {"A17": "Search for unrecorded liabilities", "B17": "Value",
             "A18": "Supplier invoices the payments settle", "B18": f'=COUNTIFS({paid},">0")',
             "A19": "  their suppliers", "B19": f"=ROWS(UNIQUE(FILTER(SupplierInvoices[SupplierID],{paid}>0)))",
             "A20": "  received from", "B20": f'=MINIFS(SupplierInvoices[ReceivedDate],{paid},">0")',
             "A21": "  received to", "B21": f'=MAXIFS(SupplierInvoices[ReceivedDate],{paid},">0")',
             "A22": "  paid in full after the year-end", "B22": f"=SUMPRODUCT(({paid}>0)*(ROUND({paid}-SupplierInvoices[GrandTotal],2)=0))",
             "A23": "  payments matched to these invoices less all payments after the year-end",
             "B23": f"=ROUND(SUM({paid})-AfterPaid,2)",
             "A24": "Supplier invoices received after the year-end",
             "B24": f'=COUNTIFS(SupplierInvoices[ReceivedDate],">"&YE_{C})',
             "A25": f"Payables at the year-end due in the months of the extract",
             "B25": (f"=SUMPRODUCT((SupplierInvoices[ReceivedDate]<=YE_{C})*(SupplierInvoices[DueDate]>=DATE({N},1,1))*"
                     f"(SupplierInvoices[DueDate]<=EOMONTH(AfterLast,0))*(SupplierInvoices[GrandTotal]-"
                     "SupplierInvoices[PaidByYearEnd]))"),
             "A26": "Pay periods paid in the extract's weeks (their registers)",
             "B26": (f'=TEXTJOIN(", ",TRUE,FILTER(PayrollPeriods[PayrollPeriodID]&" (paid "&TEXT(PayrollPeriods[PayDate],'
                     f'"yyyy-mm-dd")&", "&SUMIFS(PayrollCost[Registers],PayrollCost[PayrollPeriodID],'
                     f'PayrollPeriods[PayrollPeriodID])&" registers)",(PayrollPeriods[PayDate]>YE_{C})*'
                     '(PayrollPeriods[PayDate]<=AfterLast)))'),
             "A27": "Registers of those periods",
             "B27": (f"=SUMPRODUCT(SUMIFS(PayrollCost[Registers],PayrollCost[PayrollPeriodID],FILTER(PayrollPeriods"
                     f"[PayrollPeriodID],(PayrollPeriods[PayDate]>YE_{C})*(PayrollPeriods[PayDate]<=AfterLast))))"),
             "A28": "Note payments due in the extract's weeks, and their status",
             "B28": (f'=TEXTJOIN(", ",TRUE,FILTER(TEXT(DebtSchedule[PaymentDate],"yyyy-mm-dd")&" "&DebtSchedule[Status],'
                     f'(DebtSchedule[PaymentDate]>YE_{C})*(DebtSchedule[PaymentDate]<=AfterLast)))'),
             "A29": "  of them recorded (with a journal entry)",
             "B29": (f'=SUMPRODUCT((DebtSchedule[PaymentDate]>YE_{C})*(DebtSchedule[PaymentDate]<=AfterLast)*'
                     '(DebtSchedule[JournalEntryID]<>""))')})
    bold(ws, "A17:B17")
    ws.Range("B18:B19").NumberFormat = COUNT
    ws.Range("B20:B21").NumberFormat = DATE
    ws.Range("B22").NumberFormat = COUNT
    ws.Range("B23").NumberFormat = MONEY
    ws.Range("B24").NumberFormat = COUNT
    ws.Range("B25").NumberFormat = MONEY
    for nm, row in (("PaidInvoices", 18), ("PaidSuppliers", 19), ("PaidReceivedFrom", 20), ("PaidReceivedTo", 21),
                    ("PaidInFull", 22), ("PaidCoverage", 23), ("ReceivedAfter", 24), ("DueInExtract", 25),
                    ("ExtractRegisters", 27), ("NotePaymentsRecorded", 29)):
        name(b, nm, ws, f"B{row}")
    put(ws, {"A31": "Going-concern conditions (adjusted statements)", "B31": ye(C), "C31": ye(P),
             "A32": "Cash net of sales tax payable", "B32": f"=CashNet_{C}", "C32": f"=CashNet_{P}",
             "A33": "Quick ratio (cash and receivables)", "B33": f"=QR_{C}", "C33": f"=QR_{P}",
             "A34": "Net cash from operating activities", "B34": f"=CF_operating_{C}", "C34": f"=CF_operating_{P}",
             "A35": "Inventories as a share of current assets", "B35": f"=InvShare_{C}", "C35": f"=InvShare_{P}",
             "A36": "Materials and packaging on hand", "B36": f"=InvMat_{C}", "C36": f"=InvMat_{P}",
             "A37": "Twelve months of material issues (MaterialIssue credits to 1045)",
             "B37": (f'=SUMIFS(LedgerSummary[Credit],LedgerSummary[AccountNumber],1045,LedgerSummary[SourceDocumentType],'
                     f'"MaterialIssue",LedgerSummary[Year],{C})-SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],'
                     f'1045,LedgerSummary[SourceDocumentType],"MaterialIssue",LedgerSummary[Year],{C})'),
             "A38": "Opening payables unchanged since the opening entry", "B38": "=Open2010",
             "A40": "Mitigating factors", "A41": "Net income (adjusted)", "B41": f"=AdjNI_{C}", "C41": f"=AdjNI_{P}",
             "A42": "Working capital", "B42": f"=WC_{C}", "C42": f"=WC_{P}",
             "A43": "Notes payable (all the debt)", "B43": f"=NotesTotal_{C}"})
    bold(ws, "A31:C31")
    bold(ws, "A40")
    ws.Range("B32:C43").NumberFormat = MONEY
    ws.Range("B33:C33").NumberFormat = "0.00"
    ws.Range("B35:C35").NumberFormat = "0%"
    for nm, row in (("Issues12", 37),):
        name(b, f"{nm}_{C}", ws, f"B{row}")
    f8 = facts("r8")
    model_answer(ws, 45, MA + ": later events and going concern", [
        f"The records after {ye(C)} are {f8['n_pay']} supplier payments ({money(f8['paid'])}) from {f8['first_day']} to "
        f"{f8['last_day']} {N}, {f8['rows']} ledger rows that debit 2010 and credit 1010. They pay {f8['n_inv']} "
        f"invoices of {f8['n_sup']} suppliers, all received in {f8['recv_first']} and {f8['recv_last']} {C} and "
        f"recorded in payables at the year-end ({f8['full']} paid in full); no supplier invoice was received after "
        f"the year-end, so the search finds no unrecorded liability. The same weeks of {C} had {f8['same_n']:,} "
        f"payments ({money(f8['same_amount'])}), and payables at the year-end due in {f8['due_months']} {N} were "
        f"{money(f8['due'])}.",
        "The extract cannot be complete: it has no payroll for the pay periods paid in its weeks, no note payments "
        "(those due are still Scheduled), no December freight settlement, and no rent, sales, or receipts. It is an "
        "extract that ends, not evidence that the company stopped paying.",
        "Events the CFO must evaluate up to the date the statements are available to be issued (which the package "
        "must disclose): the credit line itself, if obtained before then; the sales tax position; and anything learned "
        "about the opening balances that no document supports.",
        f"Conditions: cash net of sales tax payable is {money(f8['cash_net'])}; the quick ratio fell to "
        f"{f8['qr_c']:.2f} from {f8['qr_p']:.2f}; operating cash flow was {money(f8['op_c'])} against "
        f"{money(f8['op_p'])}; inventories are {pct(f8['inv_share'], 0)} of current assets, with materials "
        f"({money(f8['mat'])}) above twelve months of issues ({money(f8['issues'])}); and "
        f"{money(f8['opening_ap'])} of opening payables has not changed in {f8['years']} years. Mitigating: the "
        f"company is profitable, working capital is {f8['wc_m']} million, and debt is only {money(f8['debt'])}. "
        "The ledger alone does not establish substantial doubt, but the sales tax and the opening payables could "
        "change that, so the CFO's evaluation needs evidence from outside the database."], last_col=6)
    widths(ws, {"A": 62, "B": 30, "C": 18, "D": 14, "E": 14, "F": 14})
    documentation(b)


def checks_r8(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 8"
    f = facts("r8")
    d = data()
    first, last = d.q("SELECT MIN(PostingDate), MAX(PostingDate) FROM GLEntry WHERE PostingDate > ?", ye(C))[0]
    b.check(e, f"ledger rows after {ye(C)}", f["rows"], "=AfterRows", 0, COUNT)
    b.check(e, "their source document types", "DisbursementPayment", "=AfterTypes", 0, GENERAL)
    b.check(e, "debits to 2010 after the year-end less the payments", 0, "=ROUND(AfterDebits2010-AfterPaid,2)")
    b.check(e, "credits to 1010 after the year-end less the payments", 0, "=ROUND(AfterCredits1010-AfterPaid,2)")
    b.check(e, "first posting date after the year-end", serial(first), "=AfterFirst", 0, DATE)
    b.check(e, "last posting date", serial(last), "=AfterLast", 0, DATE)
    b.check(e, "supplier payments after the year-end", f["n_pay"], "=AfterPayments", 0, COUNT)
    b.check(e, "their amount", f["paid"], "=AfterPaid")
    b.check(e, "payments in the same weeks of the year before", f["same_n"], "=SameWeeks", 0, COUNT)
    b.check(e, "their amount", f["same_amount"], "=SameWeeksPaid")
    b.check(e, "invoices the payments settle", f["n_inv"], "=PaidInvoices", 0, COUNT)
    b.check(e, "their suppliers", f["n_sup"], "=PaidSuppliers", 0, COUNT)
    b.check(e, "invoices paid in full after the year-end", f["full"], "=PaidInFull", 0, COUNT)
    b.check(e, "payments matched to invoices less all payments after the year-end", 0, "=PaidCoverage")
    b.check(e, "supplier invoices received after the year-end", 0, "=ReceivedAfter", 0, COUNT)
    b.check(e, f"payables at {ye(C)} due in the extract's months", f["due"], "=DueInExtract")
    b.check(e, "registers of the pay periods paid in the extract's weeks", 0, "=ExtractRegisters", 0, COUNT)
    b.check(e, "note payments in the extract's weeks with a journal entry", 0, "=NotePaymentsRecorded", 0, COUNT)
    b.check(e, f"twelve months of material issues ({C})", f["issues"], f"=Issues12_{C}")
    b.check(e, "materials on hand", f["mat"], f"=InvMat_{C}")
    b.check(e, "opening payables", f["opening_ap"], "=Open2010")
    b.check(e, "inventories as a share of current assets", f["inv_share"], f"=InvShare_{C}", 0.00005, PCT)


# --- Requirement 9: the memo to the CFO ---------------------------------------------------------------------------

def r9(b: ExerciseBuild) -> None:
    F, P, C = years()
    ws = analysis_sheet(b, "Memo")
    title(ws, "Memo to the CFO: what the records cannot settle", "Requirement 9. The matters, with the numbers the "
                                                               "ledger supports (live), and the memo (a model answer).")
    rent = lambda y: (f'SUMIFS(LedgerSummary[Debit],LedgerSummary[EntryType],"Rent",LedgerSummary[Year],{y})')
    put(ws, {"A4": "Matter", "B4": "Measure", "C4": "Value",
             "A5": "1. Tax status", "B5": f"Adjusted income before income taxes, {C}", "C5": f"=AdjNI_{C}",
             "B6": "Federal tax at 21% if a C corporation (rounded)", "C6": f"=ROUND(C5*{FEDERAL},-4)",
             "B7": "  as a multiple of materiality", "C7": f"=C6/Materiality_{C}",
             "B8": "Accounts named for income tax", "C8": "=IncomeTaxAccounts",
             "A9": "2. Leases", "B9": f"Rent paid from cash, {F}", "C9": f"={rent(F)}",
             "B10": f"Rent paid from cash, {P}", "C10": f"={rent(P)}",
             "B11": f"Rent paid from cash, {C}", "C11": f"={rent(C)}",
             "B12": "Postings to 2120 Lease Liability and 1140 Leasehold Improvements",
             "C12": "=COUNTIFS(LedgerSummary[AccountNumber],2120)+COUNTIFS(LedgerSummary[AccountNumber],1140)",
             "A13": "3. Sales tax collected", "B13": f"Sales tax payable (2050) at {ye(C)}", "C13": f"=S_stax_{C}",
             "B14": "Debits to 2050 from credit memos (the only debits)",
             "C14": f'=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],2050,LedgerSummary[SourceDocumentType],"CreditMemo",LedgerSummary[Year],"<="&{C})',
             "B15": "Debits to 2050 from any other source (remittances)",
             "C15": f'=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],2050,LedgerSummary[Year],"<="&{C})-C14',
             "A16": "4. Balances no document supports", "B16": "Receivables (1020)", "C16": "=Open1020",
             "B17": "Prepaid expenses (1050)", "C17": "=Open1050",
             "B18": "Accounts payable (2010), equal to the opening cash to the cent", "C18": "=Open2010",
             "B19": "Accrued payroll (2030)", "C19": "=Open2030", "B20": "Accrued expenses (2040)", "C20": "=Open2040",
             "B21": "If none is real: assets fall by", "C21": "=C16+C17",
             "B22": "  liabilities fall by", "C22": "=C18+C19+C20", "B23": "  and equity rises by", "C23": "=C22-C21",
             "A24": "5. Cash", "B24": "Postings to 7010 Interest Income", "C24": "=COUNTIFS(LedgerSummary[AccountNumber],7010)",
             "A25": "6. Inventories", "B25": f"Inventories at {ye(C)}", "C25": f"=S_inv_{C}",
             "A26": "7. Later events and going concern", "B26": "Later Events worksheet",
             "A27": "8. Passed adjustments for approval", "B27": "P1-P3 in aggregate (Adjustments worksheet)",
             "C27": "=PassedAggregate"})
    bold(ws, "A4:C4")
    ws.Range("C5:C27").NumberFormat = MONEY
    ws.Range("C7").NumberFormat = "0.0"
    ws.Range("C8").NumberFormat = COUNT
    ws.Range("C12").NumberFormat = COUNT
    ws.Range("C24").NumberFormat = COUNT
    for nm, row in (("Provision", 6), ("Rent_F", 9), ("Rent_P", 10), ("Rent_C", 11), ("LeasePostings", 12),
                    ("SalesTax", 13), ("MemoDebits2050", 14), ("Remittances", 15), ("OpeningAssets", 21),
                    ("OpeningLiabilities", 22), ("OpeningEquity", 23), ("InterestIncomePostings", 24)):
        name(b, nm, ws, f"C{row}")
    widths(ws, {"A": 32, "B": 62, "C": 18, "D": 14, "E": 14, "F": 14, "G": 14, "H": 14})
    f9, f5, f6, f8 = facts("r9"), facts("r5"), facts("r6"), facts("r8")
    o = f9["o"]
    memo = [
        f"To: Chief Financial Officer. From: Staff accountant. Date: July {C + 1}. Subject: The lender package for "
        f"fiscal {C}: what it required and what remains open.",
        f"What the package required. The ledger was turned into GAAP statements by four recorded adjustments and two "
        f"reclassifications (Adjustments worksheet): the payroll owed for each year's last days (A1), revenue "
        f"recognized in the year of delivery (A2), accruals past the invoicing window reversed (A3), and interest "
        f"accrued on the notes (A4); the current portion of the notes (R1) and the credit balance of 1090 netted into "
        f"work in process (R2). Net income becomes {money(f5['adj_ni_c'])} in {C} and {money(f5['adj_ni_p'])} in {P}; "
        f"{P} is presented as restated, and retained earnings at 1 January {P} fall by {money(-f5['total']['re'])}. "
        "Cash and the totals of the statements of cash flows do not change.",
        f"1. Tax status. The chart has no income tax account and no tax has been recorded in {f9['years']} years; "
        "equity is common stock with no distributions. The legal form or tax election, the returns, and the payments "
        "would settle it. If the company is a C corporation, the omitted provision is several times materiality "
        f"(21% federal on {money(f9['adj_ni'])} alone is about {f9['provision']:,.0f}). I propose stating the matter "
        "and recording nothing until the evidence is in hand.",
        "2. Leases. Office and warehouse rent is paid from cash on the first weekday of each month ("
        + " / ".join(money(x) for x in f9["rent"]) + "), in amounts that vary slightly; 2120 and 1140 are unused and "
        "no lessor appears among the suppliers. The agreements (term, options, escalation, discount rate) would settle "
        "it; recognizing right-of-use assets and lease liabilities would move the bank's ratios.",
        f"3. Sales tax. 2050 holds {money(f9['stax'])} collected with no remittance recorded (its only debits are "
        f"credit memos, {money(f9['memo_debits'])}). The returns, the bank statements, and the tax authority's account "
        "would settle it: either the liability is overstated because the tax was paid outside the ledger (which would "
        "also overstate cash), or penalties and interest may be owed (ASC Topic 450).",
        f"4. Opening balances. Receivables {money(o['ar'])}, prepaid {money(o['prepaid'])}, payables {money(o['ap'])} "
        f"(equal to the opening cash to the cent), accrued payroll {money(o['payroll'])}, and accrued expenses "
        f"{money(o['accrued'])} have not changed in {f9['years']} years and no document supports them. If none is "
        f"real, equity rises by {money(f9['equity'])} (assets {money(-f9['assets'])}, liabilities "
        f"{money(-f9['liabilities'])}); if the payables are real, they are three years past due.",
        "5. Cash: there is no interest income and no bank reconciliation in the records; confirm the balance with the "
        "bank. 6. Inventories: a physical count and a net realizable value review are needed, and standards unchanged "
        f"since {F} need a cost study: at a standard rebuilt on normal capacity, manufactured finished goods would be "
        f"about {f9['reval_c']:,.0f} higher at the end of {C} and {f9['reval_p']:,.0f} at the end of {P}. "
        "7. Later events and going concern: see the Later Events worksheet; the evaluation needs evidence from "
        "outside the database.",
        f"8. Passed adjustments for your approval: P1 an allowance for credit losses ({money(f5['p1'])}), P2 expected "
        f"returns ({money(f5['p2']['effect'])}), and P3 a write-down of damaged returns restocked at full cost "
        f"({money(f5['p3']['effect'])}); in aggregate {money(f5['aggregate'])}, {pct(f5['agg_share'], 0)} of "
        "materiality.",
        "Changes to the year-end close: accrue payroll for the days worked and not yet paid; review open accruals "
        "monthly and reverse those past the invoicing window; cut revenue off by delivery date; accrue interest on the "
        "notes at each month-end.",
        "Recommendation: record A1 to A4 and R1 to R2, and do not send the package to the bank until matters 1 to 4 "
        "are settled, because each could change the statements by more than materiality."]
    model_answer(ws, 30, MA + ": the memo to the CFO (two pages at most; exhibits from this workbook)", memo, last_col=6)
    documentation(b)


def checks_r9(b: ExerciseBuild) -> None:
    F, P, C = years()
    e = "Requirement 9"
    f = facts("r9")
    b.check(e, f"federal tax at 21% on {C} adjusted income (rounded)", f["provision"], "=Provision", 0)
    for nm, v, y in (("Rent_F", f["rent"][0], F), ("Rent_P", f["rent"][1], P), ("Rent_C", f["rent"][2], C)):
        b.check(e, f"rent paid from cash, {y}", v, f"={nm}")
    b.check(e, "postings to 2120 and 1140", 0, "=LeasePostings", 0, COUNT)
    b.check(e, f"sales tax payable at {ye(C)}", f["stax"], "=SalesTax")
    b.check(e, "debits to 2050 from credit memos", f["memo_debits"], "=MemoDebits2050")
    b.check(e, "debits to 2050 from any other source", 0, "=Remittances")
    b.check(e, "opening balances: assets that would fall", f["assets"], "=OpeningAssets")
    b.check(e, "opening balances: liabilities that would fall", f["liabilities"], "=OpeningLiabilities")
    b.check(e, "opening balances: equity that would rise", f["equity"], "=OpeningEquity")
    b.check(e, "postings to 7010 Interest Income", 0, "=InterestIncomePostings", 0, COUNT)


# --- the milestones' checkpoints -----------------------------------------------------------------------------------

def m1(b: ExerciseBuild) -> None:
    F, P, C = years()
    f = facts("m1")
    for k, y in enumerate((F, P, C)):
        rec = f["rec"][k]
        b.check("Milestone 1", f"trial balance accounts at {ye(y)}", rec["n"], f"=TB{y}_Accounts", 0, COUNT)
        b.check("Milestone 1", f"debit and credit balances at {ye(y)}", rec["debits"], f"=TB{y}_Debits")
        b.check("Milestone 1", f"recorded net income {y}", f["ni"][k], f"=RecNI_{y}")
        b.check("Milestone 1", f"recorded total assets at {ye(y)}", rec["ta"], f"=RecTA_{y}")
    b.check("Milestone 1", "accounts never posted", f["never"], "=NeverPosted", 0, COUNT)
    b.check("Milestone 1", "income tax accounts", 0, "=IncomeTaxAccounts", 0, COUNT)


def m2(b: ExerciseBuild) -> None:
    F, P, C = years()
    f = facts("m2")
    for k, y in enumerate((F, P, C)):
        c = f["comp"][k]
        b.check("Milestone 2", f"2040 freight at {ye(y)}", c["freight"], f"=Freight_{y}")
        b.check("Milestone 2", f"2040 young accruals at {ye(y)}", c["young"], f"=Young_{y}")
        b.check("Milestone 2", f"2040 old accruals at {ye(y)}", c["old"], f"=Old_{y}")
        b.check("Milestone 2", f"2040 rebuilt at {ye(y)}", c["total"], f"=Total2040_{y}")
        b.check("Milestone 2", f"revenue cutoff {y}", f["cut"][k], f"=Cutoff_{y}")
        b.check("Milestone 2", f"payroll owed at {ye(y)}", f["pay"][k], f"=Payroll_{y}")
        b.check("Milestone 2", f"interest accrued at {ye(y)}", f["intr"][k], f"=Interest_{y}")
    b.check("Milestone 2", "2040 opening line", f["opening"], f"=Open2040_{F}")
    b.check("Milestone 2", f"A1-A4: retained earnings at 1 January {P}", f["total"]["re"], "=AdjTotal_RE")
    b.check("Milestone 2", f"A1-A4: {P} income", f["total"]["P"], f"=AdjTotal_{P}")
    b.check("Milestone 2", f"A1-A4: {C} income", f["total"]["C"], f"=AdjTotal_{C}")
    b.check("Milestone 2", f"materiality {C}", f["mat_c"], f"=Materiality_{C}")
    b.check("Milestone 2", f"materiality {P}", f["mat_p"], f"=Materiality_{P}")


def m3(b: ExerciseBuild) -> None:
    F, P, C = years()
    f = facts("m3")
    b.check("Milestone 3", f"adjusted net income {P}", f["adj_ni"][P], f"=I_ni_{P}")
    b.check("Milestone 3", f"adjusted net income {C}", f["adj_ni"][C], f"=I_ni_{C}")
    b.check("Milestone 3", f"total assets at {ye(C)}", f["s_c"]["ta"], f"=S_ta_{C}")
    b.check("Milestone 3", f"total assets at {ye(P)}", f["s_p"]["ta"], f"=S_ta_{P}")
    b.check("Milestone 3", f"current ratio at {ye(C)}", f["s_c"]["cr"], f"=CR_{C}", 0.00005, "0.0000")
    b.check("Milestone 3", f"current ratio at {ye(P)}", f["s_p"]["cr"], f"=CR_{P}", 0.00005, "0.0000")
    b.check("Milestone 3", f"retained earnings at 1 January {P}, as previously reported", f["reported"], "=RE_Reported")
    b.check("Milestone 3", f"retained earnings at 1 January {P}, as restated", f["restated"], "=RE_Restated")
    b.check("Milestone 3", f"retained earnings at {ye(C)}", f["s_c"]["re"], f"=RE_End_{C}")
    b.check("Milestone 3", f"operating cash flow {C}", f["cf"]["operating"], f"=CF_operating_{C}")
    b.check("Milestone 3", f"investing cash flow {C}", f["cf"]["investing"], f"=CF_investing_{C}")
    b.check("Milestone 3", f"financing cash flow {C}", f["cf"]["financing"], f"=CF_financing_{C}")
    b.check("Milestone 3", f"property and equipment cost at {ye(C)}", f["cost"], f"=PPECost_{C}")
    b.check("Milestone 3", f"accumulated depreciation at {ye(C)}", f["accumulated"], f"=AccDep_{C}")
    b.check("Milestone 3", f"notes payable at {ye(C)}", f["s_c"]["notes"], f"=NotesTotal_{C}")
    b.check("Milestone 3", f"current portion at {ye(C)}", f["s_c"]["cur"], f"=CurPortion_{C}")


def m4(b: ExerciseBuild) -> None:
    F, P, C = years()
    f = facts("m4")
    b.check("Milestone 4", "supplier payments after the year-end", f["payments"], "=AfterPayments", 0, COUNT)
    b.check("Milestone 4", "their amount", f["amount"], "=AfterPaid")
    b.check("Milestone 4", "supplier invoices received after the year-end (unrecorded liabilities)", 0,
            "=ReceivedAfter", 0, COUNT)
    b.check("Milestone 4", f"sales tax payable at {ye(C)}", f["stax"], "=SalesTax")
    b.check("Milestone 4", "equity if no opening balance is real", f["equity"], "=OpeningEquity")


class Retrying:
    """A COM object whose attribute reads, writes, and calls are retried while Excel rejects them as busy (xl.retry),
    and whose results are wrapped the same way. The requirements are built through it: Excel can reject any call while
    it digests a long formula or a query load, and wrapping every call by hand would hide the workbook's logic."""
    __slots__ = ("_o",)

    def __init__(self, obj):
        object.__setattr__(self, "_o", obj)

    def __getattr__(self, attr):
        return _wrap(xl.retry(lambda: getattr(self._o, attr)))

    def __setattr__(self, attr, value):
        xl.retry(lambda: setattr(self._o, attr, _unwrap(value)))

    def __call__(self, *args, **kwargs):
        args = [_unwrap(a) for a in args]
        kwargs = {k: _unwrap(v) for k, v in kwargs.items()}
        return _wrap(xl.retry(lambda: self._o(*args, **kwargs)))

    def __iter__(self):
        for item in xl.retry(lambda: list(self._o)):
            yield _wrap(item)


def _wrap(value):
    if value is None or isinstance(value, (str, int, float, bool, tuple, list, dict, Retrying)):
        return value
    if type(value).__module__.startswith(("datetime", "pywintypes")):
        return value
    return Retrying(value)


def _unwrap(value):
    return object.__getattribute__(value, "_o") if isinstance(value, Retrying) else value


def _with_checks(apply, checks):
    """A requirement's build, under manual calculation (Excel stays responsive while hundreds of formulas go in) and
    through a retrying workbook object, and its checks. Calculation is automatic again before the Solution Notes
    recalculate and before the file is saved."""
    def run(b: ExerciseBuild) -> None:
        app = b.wb.Application
        xl.wait_ready(app)
        xl.retry(lambda: setattr(app, "Calculation", XL_MANUAL))
        real = b.wb
        b.wb = Retrying(real)
        try:
            apply(b)
        finally:
            b.wb = real
            xl.retry(lambda: setattr(app, "Calculation", XL_AUTOMATIC))
            xl.wait_ready(app)
        checks(b)
    run.__name__ = apply.__name__
    return run


EXERCISES = [("Requirement 1", _with_checks(r1, checks_r1)), ("Requirement 2", _with_checks(r2, checks_r2)),
             ("Requirement 3", _with_checks(r3, checks_r3)),
             ("Requirement 4", _with_checks(r4, checks_r4)),
             ("Requirement 5", _with_checks(r5, checks_r5)),
             ("Requirement 6", _with_checks(r6, checks_r6)),
             ("Requirement 7", _with_checks(r7, checks_r7)),
             ("Requirement 8", _with_checks(r8, checks_r8)),
             ("Requirement 9", _with_checks(r9, checks_r9)),
             ("Milestone 1", m1), ("Milestone 2", m2), ("Milestone 3", m3), ("Milestone 4", m4)]
