"""Chapter 17's instructor guides (the capstone case "Financial Statements for a Lender"): the values the guides state, and
the claims their wording makes.

The case (chapters/17-statements-for-a-lender/chapter.qmd) is an independent final-project option with nine requirements
in four phases (four milestones) and no tutorials.  Its model answer is three files, one for each tool the case names:

- LenderPackage.sql, the SQL part (outputs/companion/solutions/Chapter17-capstone-sql/),
- Charles River Lender Package.xlsx, the Excel part (outputs/companion/solutions/Chapter17-capstone-excel/),
- Charles River Lender Review, the Power BI project of Requirements 2 and 6 (outputs/companion/solutions/Chapter17-capstone-pbi/).

The registered notes ch17.r1 to ch17.r9 and ch17.m1 to ch17.m4 (facts/notes/ch17.py) already supply the expected values of
the requirements and milestones.  These contexts add what the model paths need beyond them:

- the text of each model file the guides quote (SQL from the script, Excel formulas from the workbook, DAX and M from the
  Power BI project), read from the file itself, so a quote cannot drift from the file the instructor opens,
- the symptom of every wrong version a guide names (a trial balance that leaves out every close, a balance that nets an
  overbilled accrual, a payroll cutoff by calendar days, a 2026 effect that keeps the 2025 reversal out, ...), computed
  read-only on the dataset, on the model script's own text with one change where the wrong version is a change to a query,
- the deck's slide numbers, the titles of the report's visuals, and claims on every table and column the guides name.

What the Power BI project proves and what only Desktop shows: the project encodes the model and the structure of every page,
and its Checks tab (DAX query view) recomputes the values of Requirements 2 and 6 and of Milestones 1 and 3, so a result is
"proved" when a Checks row names it.  How a visual renders (the matrix's expanded rows, the drill-through button, the slicer
state) is visible only in Desktop.

Keys:
- ch17.g0: the case note (slides, the model files, counts);
- ch17.g1 to ch17.g5: Requirements 1 to 5, each used next to the note ch17.r1 to ch17.r5 that supplies the values of the
  requirement's instructor note.  The next agent adds ch17.g6 to ch17.g9 to this file and reuses its helpers:
  script(), quote(), sub(), temp_view(), formula(), adjustment_line(), measure_table(), dax(), step(), check_expr(),
  title(), has_visual(), test_block(), deck_titles(), at(), span().
"""

from __future__ import annotations

import base64
import json
import re
import zlib
from collections import Counter
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch13 import _block
from notes import ch17 as n17
from notes.case4 import xr
from notes.ch08 import BUCKETS
from notes.ch12 import invoices_by_delivery

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "17-statements-for-a-lender" / "chapter.qmd"
DECK = REPO / "slides" / "chapter-17" / "index.qmd"
DOWNLOADS = REPO / "front-matter" / "downloads.qmd"
SOLUTIONS = REPO / "outputs" / "companion" / "solutions"
SQL = SOLUTIONS / "Chapter17-capstone-sql" / "LenderPackage.sql"
XLSX = SOLUTIONS / "Chapter17-capstone-excel" / "Charles River Lender Package.xlsx"
PROJECT = SOLUTIONS / "Chapter17-capstone-pbi" / "Charles River Lender Review"
MODEL = PROJECT / "Charles River Lender Review.SemanticModel"
REPORT = PROJECT / "Charles River Lender Review.Report"

SCHEMA = {
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "SourceDocumentID",
                "SourceLineID", "FiscalYear"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType", "NormalBalance", "IsActive"],
    "JournalEntry": ["JournalEntryID", "EntryNumber", "EntryType", "PostingDate", "ReversesJournalEntryID", "Description",
                     "TotalAmount"],
    "PurchaseInvoiceLine": ["PILineID", "PurchaseInvoiceID", "AccrualJournalEntryID", "LineTotal"],
    "PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "ReceivedDate", "DueDate", "GrandTotal", "SupplierID"],
    "Shipment": ["ShipmentID", "ShipmentNumber", "ShipmentDate", "DeliveryDate", "FreightCost"],
    "ShipmentLine": ["ShipmentLineID", "ShipmentID", "SalesOrderLineID", "QuantityShipped", "ExtendedStandardCost"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SubTotal", "TaxAmount", "FreightAmount"],
    "SalesInvoiceLine": ["SalesInvoiceID", "SalesInvoiceLineID", "ShipmentLineID", "LineTotal"],
    "SalesOrderLine": ["SalesOrderLineID", "UnitPrice", "Discount"],
    "PayrollPeriod": ["PayrollPeriodID", "PeriodNumber", "PeriodStartDate", "PeriodEndDate", "PayDate", "Status"],
    "PayrollRegister": ["PayrollPeriodID", "CostCenterID", "GrossPay", "EmployerPayrollTax", "EmployerBenefits"],
    "WorkCenterCalendar": ["WorkCenterID", "CalendarDate", "IsWorkingDay"],
    "DebtAgreement": ["DebtAgreementID", "AgreementNumber", "OriginationDate", "PrincipalAmount", "FixedAssetID",
                      "AnnualInterestRate", "TermMonths", "PaymentStartDate", "ScheduledPaymentAmount"],
    "DebtScheduleLine": ["DebtAgreementID", "PaymentDate", "PrincipalAmount", "InterestAmount", "PaymentAmount", "Status",
                         "JournalEntryID"],
    "SalesReturn": ["SalesReturnID", "ReturnDate", "ReasonCode"],
    "SalesReturnLine": ["SalesReturnID", "ShipmentLineID", "ExtendedStandardCost"],
    "CreditMemo": ["SalesReturnID", "OriginalSalesInvoiceID", "CreditMemoDate", "SubTotal", "GrandTotal", "Status"],
    "CashReceiptApplication": ["SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "DisbursementPayment": ["PaymentDate", "Amount", "PurchaseInvoiceID"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
    # the tables Requirements 6 to 9 name
    "FixedAsset": ["FixedAssetID", "AssetCode", "AssetAccountID", "AccumulatedDepreciationAccountID", "InServiceDate",
                   "DisposalDate", "UsefulLifeMonths", "OriginalCost", "ResidualValue"],
    "FixedAssetEvent": ["FixedAssetID", "EventType", "EventDate", "Amount", "FinancingType", "ProceedsAmount"],
    "ServiceEngagement": ["ServiceEngagementID", "Status", "EndDate", "PlannedHours"],
    "ServiceTimeEntry": ["ServiceEngagementID", "WorkDate", "BillableHours"],
    "ServiceBillingLine": ["ServiceEngagementID", "BilledHours"],
}
PAGES = ["review", "postings", "sources", "questions", "validation", "packageTests", "notes"]
GUIDES = REPO / "facts" / "instructor" / "guides" / "chapter-17-statements-for-a-lender"
# The student time of each requirement in minutes, and its weight in the case rubric (the weights add up to 100).  The
# requirement guides' front matter must agree; g0 claims it for every guide written so far.
PLAN = {1: 90, 2: 150, 3: 150, 4: 150, 5: 180, 6: 180, 7: 150, 8: 90, 9: 120}
WEIGHTS = {1: 8, 2: 10, 3: 12, 4: 12, 5: 14, 6: 12, 7: 10, 8: 7, 9: 15}


def need(d, claim, *tables: str) -> None:
    schema(d, claim, {t: SCHEMA[t] for t in (tables or SCHEMA)})


# --- the SQL model script ---------------------------------------------------------------------------------------------

def norm(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().rstrip(";").strip())


def sub(sql: str, old: str, new: str) -> str:
    """The statement with `old` replaced by `new`, ignoring differences in whitespace; the text must be there."""
    pattern = r"\s+".join(re.escape(w) for w in old.split())
    if not re.search(pattern, sql):
        raise ValueError(f"the text to change is not in the statement: {old[:70]}")
    return re.sub(pattern, lambda m: new, sql, count=1)


@lru_cache(maxsize=None)
def script() -> tuple[tuple[str, str, str], ...]:
    """(first comment line, second comment line, statement) of every query of LenderPackage.sql, in order; the trailing
    result comment is dropped and the closing notes block is left out."""
    body = SQL.read_text(encoding="utf-8").split("\n/* Model answer", 1)[0]
    out = []
    for chunk in re.split(r"(?m)^(?=-- (?:Requirement|Milestone) \d+:)", body):
        if not re.match(r"-- (?:Requirement|Milestone) \d+:", chunk):
            continue
        lines = chunk.rstrip().split("\n")
        stmt = re.sub(r";[ \t]*-- Result:[^\n]*$", ";", "\n".join(lines[2:]), flags=re.M)
        out.append((lines[0], lines[1], stmt.strip()))
    return tuple(out)


def quote(key: str) -> str:
    """The statement of the one query whose first comment line starts with `key`."""
    hits = [s for first, _, s in script() if first.removeprefix("-- ").startswith(key)]
    if len(hits) != 1:
        raise KeyError(f"{len(hits)} queries of LenderPackage.sql start with {key!r}")
    return hits[0]


def run(d, sql: str) -> list:
    return d.q(sql.strip().rstrip(";"))


def summary(rows: list) -> dict:
    """A trial-balance result (AccountNumber, AccountName, AccountType, AccountSubType, Balance, DebitBalance,
    CreditBalance, Postings) in a few numbers."""
    return dict(accounts=len(rows), zero=sum(1 for r in rows if r[4] == 0), debits=round(sum(r[5] for r in rows), 2),
                credits=round(sum(r[6] for r in rows), 2), by={int(r[0]): r[4] for r in rows},
                assets=round(sum(r[4] for r in rows if r[2] == "Asset"), 2))


@contextmanager
def temp_view(d, name: str, new_name: str | None = None, *changes: tuple[str, str]):
    """A saved view of the model script created as a TEMP view (for the length of the block), optionally under another name
    and with changes to its text; the Data object is shared, so the view is dropped again."""
    new_name = new_name or name
    stmt = next((s for first, _, s in script() if re.match(rf"(?s)DROP VIEW IF EXISTS {name};", s)), None)
    if stmt is None:
        raise KeyError(f"LenderPackage.sql does not save the view {name}")
    text = re.match(rf"(?s)DROP VIEW IF EXISTS {name};\s*(CREATE VIEW {name} AS.*)", stmt).group(1).rstrip().rstrip(";")
    for old, new in changes:
        text = sub(text, old, new)
    text = text.replace(f"CREATE VIEW {name} AS", f"CREATE TEMP VIEW {new_name} AS", 1)
    d.con.execute(f"DROP VIEW IF EXISTS temp.{new_name}")
    d.con.execute(text)
    try:
        yield
    finally:
        d.con.execute(f"DROP VIEW IF EXISTS temp.{new_name}")


# --- the Excel model workbook -----------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def workbook():
    import openpyxl
    return openpyxl.load_workbook(XLSX, read_only=False, data_only=False)


def sheets() -> list[str]:
    return list(workbook().sheetnames)


def clean(text) -> str:
    """A formula as the formula bar reads it: the file's prefixes and the stored spill references written the way a person
    types them."""
    t = str(getattr(text, "text", text))
    t = re.sub(r"_xl(?:fn|pm|ws)\.", "", t)
    t = re.sub(r"ANCHORARRAY\(((?:'[^']+'!)?\$?[A-Z]+\$?\d+)\)", r"\1#", t)
    t = re.sub(r"(\w+)\[\[#This Row\],\[([^\]]+)\]\]", r"[@\2]", t)
    return t


def formula(claim, sheet: str, cell: str) -> str:
    value = workbook()[sheet][cell].value
    ok = isinstance(value, str) and value.startswith("=") or hasattr(value, "text")
    claim(ok, f"the cell {sheet}!{cell} of the model workbook holds a formula")
    return clean(value) if ok else ""


def split_args(text: str) -> list[str]:
    """The top-level arguments of a function call's body, split on commas outside parentheses and quotes."""
    out, depth, cur, quoted = [], 0, "", False
    for ch in text:
        if ch == '"':
            quoted = not quoted
        if not quoted:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append(cur)
                cur = ""
                continue
        cur += ch
    return out + [cur]


def mapping_formula(claim) -> str:
    """The StatementLine column's LET and IFS formula of Working TB, one test and its line to a row of text."""
    f = formula(claim, "Working TB", "H2")
    m = re.match(r"^=LET\((.*?),IFS\((.*)\)\)$", f)
    claim(m is not None, "the StatementLine formula of Working TB is a LET with an IFS")
    if not m:
        return f
    pairs = split_args(m.group(2))
    claim(len(pairs) % 2 == 0, "the IFS of the StatementLine formula holds test and result pairs")
    lines = [",".join(pairs[i:i + 2]) for i in range(0, len(pairs), 2)]
    return f"=LET({m.group(1)},\n    IFS(\n        " + ",\n        ".join(lines) + "))"


def adjustment_line(claim, no: str, year: int, account: int) -> str:
    """The Amount formula of the AdjustmentLines row of one entry, year-end and account."""
    ws = workbook()["Adjustments"]
    for r in range(54, ws.max_row + 1):
        if ws.cell(r, 1).value == no and str(ws.cell(r, 3).value).endswith(f"{year}") and ws.cell(r, 4).value == account:
            return clean(ws.cell(r, 6).value)
    claim(False, f"AdjustmentLines has the line {no} at {year} to account {account}")
    return ""


# --- the Power BI model answer -------------------------------------------------------------------------------------------

def _model_text(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def table_m(name: str) -> list[str]:
    return _block(_model_text(f"tables/{name}.tmdl"), "source =")


def step(claim, lines: list[str], *names: str) -> str:
    """The named steps of an M query as the formula bar reads them."""
    out = []
    for n in names:
        found = [l for l in lines if l.startswith(f'#"{n}" =') or l.startswith(f"{n} =")]
        claim(len(found) == 1, f"the solution project's query has the step {n}")
        out += ["    " + l.rstrip(",") for l in found]
    return "\n".join(out)


@lru_cache(maxsize=None)
def measure_table() -> dict[str, str]:
    """Every measure of every table of the project as the formula bar reads it: `Name = expression`, the body dedented."""
    out: dict[str, str] = {}
    for path in sorted((MODEL / "definition" / "tables").glob("*.tmdl")):
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = re.match(r"^\tmeasure (?:'([^']+)'|(\S+)) =(.*)$", line)
            if not m:
                continue
            name, first = m.group(1) or m.group(2), m.group(3).strip()
            body, j = [], i + 1
            while j < len(lines) and lines[j].startswith("\t\t\t"):
                body.append(lines[j][3:].rstrip())
                j += 1
            out[name] = f"{name} = {first}" if first and not body else f"{name} =\n" + "\n".join(body)
    return out


def dax(claim, *names: str) -> str:
    table = measure_table()
    for n in names:
        claim(n in table, f"the solution project has the measure {n}")
    return "\n\n".join(table.get(n, "") for n in names)


def check_expr(claim, label: str) -> str:
    """The DAX expression of one row of the project's Checks tab (DAX query view), found by its label."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    m = re.search(r'"Check", "' + re.escape(label) + r'", "Expected", .*?, "Actual", (.*?), "Agrees"', text)
    claim(m is not None, f"the Checks tab has the row {label!r}")
    return m.group(1) if m else ""


def check_sections() -> dict[str, int]:
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for sec in re.findall(r'ROW \( "Section", "([^"]*)"', text):
        counts[sec] = counts.get(sec, 0) + 1
    return counts


def title(claim, page: str, name: str) -> str:
    """The title of a visual of the solution project's report page, as Desktop shows it."""
    try:
        v = json.loads((REPORT / "definition" / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))
        text = v["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"].strip("'")
        text = text.replace("''", "'")
    except (OSError, KeyError, IndexError, ValueError):
        text = ""
    claim(text != "", f"the visual {name} of page {page} in the solution project has a title")
    return text


def has_visual(claim, page: str, *names: str) -> None:
    for n in names:
        claim((REPORT / "definition" / "pages" / page / "visuals" / n / "visual.json").is_file(),
              f"the page {page} of the solution project has the visual {n}")


def test_block(claim, n: int) -> str:
    """Test n of the Tests tab, comment line first."""
    text = (MODEL / "DAXQueries" / "Tests.dax").read_text(encoding="utf-8").strip()
    found = [p.strip() for p in re.split(r"(?m)^(?=// Test \d)", text) if p.startswith(f"// Test {n}:")]
    claim(len(found) == 1, f"the Tests tab holds Test {n}")
    return found[0] if found else ""


def questions_table() -> list[list]:
    """The rows of the Questions table the project types with Enter data, decoded from the M the project holds."""
    text = _model_text("tables/Questions.tmdl")
    blob = re.search(r'Binary\.FromText\("([^"]+)"', text).group(1)
    return json.loads(zlib.decompress(base64.b64decode(blob), -15).decode("utf-8"))


# --- the deck ------------------------------------------------------------------------------------------------------------------

def deck_titles() -> list[str]:
    titles = ["(title slide)"]
    for line in DECK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,2} (.+?)\s*(\{[^}]*\})?\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    return titles


def at(titles: list[str], first: str, nth: int = 1) -> int:
    hits = [n for n, t in enumerate(titles, 1) if t.startswith(first)]
    return hits[nth - 1]


def span(titles: list[str], first: str, after: str, nth: int = 1, after_nth: int = 1) -> str:
    start, end = at(titles, first, nth), at(titles, after, after_nth) - 1
    return str(start) if end <= start else f"{start} to {end}"


# --- the case note -----------------------------------------------------------------------------------------------------------

@context("ch17.g0")
def g0(d, claim):
    need(d, claim)
    t = deck_titles()
    claim(len(t) == 63, "the case's deck has 63 slides")
    text = CHAPTER.read_text(encoding="utf-8")
    n_req = len(re.findall(r"^\*\*Requirement \d+:", text, re.M))
    claim(n_req == 9, "the case has nine requirements")
    n_ms = len(re.findall(r"^\d+\. \*\*[^*]+\*\* \(Requirements? ", text, re.M))
    claim(n_ms == 4, "the case has four milestones, one for each phase")
    claim("## Tutorial" not in text and "Guided Tutorial" not in text, "the case has no tutorials")
    downloads = DOWNLOADS.read_text(encoding="utf-8")
    claim(all(z in downloads for z in ("Chapter17-capstone-excel.zip", "Chapter17-capstone-pbi.zip", "Chapter17-capstone-sql.zip")),
          "the Downloads page lists the three solution files of the case")
    claim(SQL.is_file() and XLSX.is_file() and MODEL.is_dir() and REPORT.is_dir(),
          "the three model files of the case are in outputs/companion/solutions")
    queries = script()
    claim(len(queries) > 60, "the model script holds the queries of all nine requirements and of the milestones")
    per = {}
    for first, _, _ in queries:
        k = re.match(r"-- (Requirement|Milestone) (\d+):", first)
        per[f"{k.group(1)[0]}{k.group(2)}"] = per.get(f"{k.group(1)[0]}{k.group(2)}", 0) + 1
    wb = sheets()
    claim("Solution Notes" in wb and "Working TB" in wb and "Adjustments" in wb, "the model workbook has its Solution Notes, Working TB and Adjustments worksheets")
    pages = json.loads((REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    claim(sorted(pages) == sorted(PAGES), "the solution project has the seven pages the guides name")
    hidden = [p for p in pages if '"visibility": "HiddenInViewMode"' in
              (REPORT / "definition" / "pages" / p / "page.json").read_text(encoding="utf-8")]
    sections = check_sections()
    claim(set(sections) == {"Requirement 2", "Requirement 6", "Milestone 1", "Milestone 3"},
          "the Checks tab holds the rows of Requirements 2 and 6 and of Milestones 1 and 3")
    # the data conditions of the at-a-glance table
    claim(n17.no_tax_account(d), "the chart has no income tax account")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE PostingDate > ?", f"{d.C}-12-31") > 0
          and d.one("SELECT COUNT(*) FROM GLEntry WHERE PostingDate > ? AND SourceDocumentType <> 'DisbursementPayment'", f"{d.C}-12-31") == 0,
          "the only postings after the last fiscal year are supplier payments")
    last = d.one("SELECT MAX(PostingDate) FROM GLEntry")
    pay_end = d.one("SELECT MAX(PostingDate) FROM GLEntry WHERE SourceDocumentType IN ('PayrollSummary', 'PayrollPayment')")
    claim(pay_end < f"{d.C}-12-31" < last, "payroll postings end before the year-end and the ledger runs past it")
    claim(sum(WEIGHTS.values()) == 100, "the rubric weights of the nine requirements add up to 100")
    for path in sorted(GUIDES.glob("req-*.md")):
        n = int(re.match(r"req-(\d+)-", path.name).group(1))
        m = re.search(r"(?m)^minutes: (\d+)", path.read_text(encoding="utf-8"))
        claim(not m or int(m.group(1)) in (0, PLAN[n]), f"requirement {n}'s guide gives its student time as {PLAN[n]} minutes")
    s = dict(
        kick=span(t, "A lender needs statements", "The Situation"), situation=span(t, "The Situation", "The Data You Will Use"),
        data=span(t, "The Data You Will Use", "Getting Started"), setup=span(t, "Getting Started", "Phase 1: The Ledger"),
        tool_check=span(t, "Check your understanding", "Phase 1: The Ledger"), handin=at(t, "What you will hand in"),
        criteria=span(t, "How your work will be judged", "The Situation"), watch=span(t, "Watch out: every balance", "Getting Started"),
        milestones=at(t, "Four milestones"), tools=at(t, "Choose the tool for each step"),
        p1=span(t, "Phase 1: The Ledger", "Phase 2: The Adjustments"), r1=at(t, "One query, three trial balances"),
        r2=at(t, "Review the statements before adjusting them"), m1=at(t, "Milestone 1"),
        p2=span(t, "Phase 2: The Adjustments", "Phase 3: The Statements"), r3=span(t, "Rebuild accrued expenses", "Test cutoff at every year-end"),
        r4=at(t, "Test cutoff at every year-end"), r5=span(t, "Classify, measure and judge", "Check your understanding", after_nth=2),
        err=span(t, "A missed cutoff item", "Check your understanding", after_nth=2),
        check2=span(t, "Check your understanding", "Milestone 2", nth=2), m2=at(t, "Milestone 2"),
        p3=span(t, "Phase 3: The Statements", "Phase 4: What the Data Cannot Settle"), st=span(t, "Prepare the four statements", "Build each note from the records"),
        notes=at(t, "Build each note from the records"), m3=at(t, "Milestone 3"),
        p4=span(t, "Phase 4: What the Data Cannot Settle", "Deliverables and Checklist"), r8=at(t, "Look past the year-end"),
        r9=at(t, "Assemble the package"), check3=span(t, "Check your understanding", "Milestone 4", nth=3), m4=at(t, "Milestone 4"),
        deliver=at(t, "Deliverables and Checklist"), before=at(t, "Before you submit"),
        ahead=span(t, "Looking Ahead", "About these slides"))
    return dict(plan=PLAN, weights=WEIGHTS, student_minutes=sum(PLAN.values()), student_hours=sum(PLAN.values()) // 60,
                n_req=n_req, n_ms=n_ms, slides=len(t), s=s, n_queries=len(queries), per=per, n_sheets=len(wb), n_pages=len(pages),
                n_hidden=len(hidden), checks=sum(sections.values()), per_section=sections, n_measures=len(measure_table()),
                last=last, pay_end=pay_end, thru=f"{d.C}-12-31")


# --- Requirement 1: the trial balances and the recorded statements ----------------------------------------------------------

@context("ch17.g1")
def g1(d, claim):
    need(d, claim)
    claim(sheets()[:5] == ["Documentation", "TB 2024", "TB 2025", "TB 2026", "Working TB"],
          "the model workbook starts with Documentation, the three trial balances and Working TB")
    claim("Recorded" in sheets(), "the model workbook has the Recorded worksheet")
    q = quote("Requirement 1: the trial balance at 2026-12-31")
    base = summary(run(d, q))
    C = d.C
    claim("Params" in q and "Closes" in q, "the model's trial balance has a Params and a Closes CTE")
    # four wrong versions of the query, each the quoted text with one change
    asof = "gl.PostingDate <= (SELECT AsOfDate FROM Params)"
    close_out = ("AND NOT (gl.VoucherNumber IN (SELECT EntryNumber FROM Closes) "
                 "AND gl.PostingDate = (SELECT AsOfDate FROM Params))")
    strict = summary(run(d, sub(q, asof, "gl.PostingDate < (SELECT AsOfDate FROM Params)")))
    every = summary(run(d, sub(q, close_out, "AND gl.VoucherNumber NOT IN (SELECT EntryNumber FROM Closes)")))
    none = summary(run(d, sub(q, close_out, "")))
    year = summary(run(d, sub(q, asof, f"gl.FiscalYear = {C}")))
    claim(strict["debits"] < base["debits"] and abs(strict["debits"] - strict["credits"]) < 0.005,
          "a strict less-than leaves out the postings of the last day and the trial balance still balances")
    claim(every["accounts"] == base["accounts"] - 1 and every["zero"] == base["zero"] - 1 and every["debits"] > base["debits"],
          "leaving out every close leaves 70 accounts, one fewer at zero, and larger totals")
    claim(none["zero"] > base["zero"] and none["debits"] < base["debits"], "leaving every close in zeroes the revenue and expense accounts")
    claim(year["accounts"] < base["accounts"] and abs(year["by"][1010] - n17.activity(d, ["1010"], C)) < 0.005,
          "a trial balance of the year's postings alone shows cash as the year's change")
    chart = n17.chart(d)
    nb_assets = round(sum((-v if chart[str(n)]["normal"] == "Credit" else v) for n, v in base["by"].items()
                          if chart[str(n)]["type"] == "Asset"), 2)
    claim(nb_assets > base["assets"], "signing assets by each account's normal balance adds the contra assets to the total")
    ni = n17.net_income(d, C)
    le = -sum(v for n, v in base["by"].items() if chart[str(n)]["type"] in ("Liability", "Equity"))
    claim(abs((base["assets"] - le) - ni) < 0.005, "before the year's close, assets less liabilities and equity equal the year's net income")
    # the anti-join and its wrong versions
    anti = quote("Requirement 1: the accounts never posted")
    no_hdr = len(run(d, sub(anti, "AND a.AccountSubType <> 'Header'", "")))
    inner = len(run(d, sub(anti, "LEFT JOIN GLEntry", "INNER JOIN GLEntry")))
    rows_anti = len(run(d, anti))
    claim(no_hdr > rows_anti and inner == 0, "without the header filter the anti-join lists the headers, and an inner join lists nothing")
    taxes = len(run(d, quote("Requirement 1: the accounts named for taxes")))
    have_hdr = d.one("SELECT COUNT(*) FROM Account WHERE AccountSubType = 'Header'")
    claim(have_hdr > 0 and no_hdr - rows_anti == have_hdr, "the chart has header accounts, and none of them ever posts")
    # the statement line mapping and the recorded statements, from the workbook
    f_map = mapping_formula(claim)
    f_re = formula(claim, "Recorded", "D23")
    claim("D41" in f_re, "the retained earnings line of the Recorded worksheet adds the year's net income")
    return dict(
        base=base, strict=strict, every=every, none=none, year=year, shortfall=round(base["debits"] - strict["debits"], 2),
        cash_change=year["by"][1010], re_every=-every["by"][3030], re_base=-base["by"][3030], rev_every=-every["by"][4010],
        rev_base=-base["by"][4010], nb_assets=nb_assets, ta=base["assets"], nb_extra=round(nb_assets - base["assets"], 2),
        gap=round(base["assets"] - le, 2), no_hdr=no_hdr, inner=inner, n_anti=rows_anti, taxes=taxes, headers=have_hdr,
        f_map=f_map, f_re=f_re, n_q1=sum(1 for first, _, _ in script() if first.startswith("-- Requirement 1:")),
        t_ni=ni)


# --- Requirement 2: the Review file ------------------------------------------------------------------------------------------

def _tb_at(d, asof: str, mode: str = "correct") -> dict[str, float]:
    """Debits less credits by account at a date: the case's rule, every close left out, or no close left out."""
    closes = "SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%'"
    cond = {"correct": f"(g.VoucherNumber NOT IN ({closes}) OR g.PostingDate < '{asof}')",
            "every": f"g.VoucherNumber NOT IN ({closes})", "none": "1 = 1"}[mode]
    return {str(n): v for n, v in d.q(f"SELECT a.AccountNumber, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON "
                                      f"a.AccountID = g.AccountID WHERE g.PostingDate <= ? AND {cond} GROUP BY a.AccountID", asof)}


def _flagged(d, mode: str, mat: float) -> list[tuple[str, float]]:
    p, c = _tb_at(d, n17.ye(d.P), mode), _tb_at(d, n17.ye(d.C), mode)
    ch = [(n, round(c.get(n, 0.0) - p.get(n, 0.0), 2)) for n in set(p) | set(c) if n != "3030"]
    return sorted([x for x in ch if abs(x[1]) > mat], key=lambda x: (-abs(x[1]), x[0]))


@context("ch17.g2")
def g2(d, claim):
    need(d, claim)
    P, C = d.P, d.C
    mat = n17.materiality(d, C)
    chart = n17.chart(d)
    right = _flagged(d, "correct", mat)
    named = lambda nums: ", ".join(f"{n} {chart[n]['name']}" for n in nums)                  # noqa: E731
    every = _flagged(d, "every", mat)
    closed = _flagged(d, "none", mat)
    claim(len(every) > 3 * len(right), "leaving out every close flags many times as many accounts")
    claim(set(n for n, _ in closed) < set(n for n, _ in right) and len(right) - len(closed) == 3,
          "leaving every close in drops the revenue and expense accounts that moved from the flagged list")
    lost = [n for n, _ in right if n not in {m for m, _ in closed}]
    signed = [n for n, v in right if v > 0]
    missed = [n for n, v in right if not v > 0]
    claim(len(missed) >= 3 and "1010" in missed, "a test of the signed change misses the accounts that fell or are credits, cash among them")
    # a balance taken at the ledger's last date
    last = d.one("SELECT MAX(PostingDate) FROM GLEntry")
    at_last = _tb_at(d, last)
    at_ye = _tb_at(d, n17.ye(C))
    claim(abs(at_ye["1010"] - at_last["1010"]) > 1000 and last > n17.ye(C), "cash at the ledger's last date differs from the year-end balance")
    # balances that rest on journal entries alone, and that have not moved since the opening entry
    op = n17.opening_entry(d)
    only_je = [str(n) for (n,) in d.q("SELECT a.AccountNumber FROM Account a JOIN GLEntry g ON g.AccountID = a.AccountID WHERE "
                                      "a.AccountType IN ('Asset', 'Liability', 'Equity') GROUP BY a.AccountID HAVING "
                                      "SUM(g.SourceDocumentType <> 'JournalEntry') = 0 ORDER BY 1")]
    opening = {n: v for n, v in ((str(n), v) for n, v in d.q(
        "SELECT a.AccountNumber, SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        "WHERE g.VoucherNumber = ? AND g.SourceDocumentType = 'JournalEntry' GROUP BY 1", op))}
    unmoved = sorted(n for n, v in opening.items() if abs(at_ye.get(n, 0.0) - v) < 0.005)
    claim(unmoved == ["1050", "1110", "2030", "3010"], f"the balances unchanged since the opening entry ({unmoved})")
    posts_2030 = d.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = 2030")
    claim(posts_2030 > 1000, "2030 has thousands of postings, all but the opening line payroll postings that net to zero")
    claim(set(unmoved) - set(only_je) == {"2030"}, "1050, 1110 and 3010 are posted by journal entries alone; 2030 is not")
    single = [n for n in unmoved if d.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = ?", int(n)) == 1]
    claim(single == ["1050", "1110", "3010"], "1050, 1110 and 3010 each carry a single posting")
    # the report as the solution project holds it
    gl = table_m("GLEntry")
    wt = table_m("WorkingTB")
    wb = formula(claim, "Documentation", "B8")
    has_visual(claim, "review", "threshold", "materiality", "reviewMatrix", "aboveTable")
    has_visual(claim, "postings", "bySource", "postingList", "changeCards")
    has_visual(claim, "sources", "sourceMatrix", "openingTable", "journalOnly")
    has_visual(claim, "questions", "questionTable")
    has_visual(claim, "validation", "tbTotals", "chartCards")
    claim("GENERATESERIES ( 0, 1000000, 25000 )" in _model_text("tables/Threshold.tmdl"), "the what-if series runs from zero to one million in steps of 25,000")
    claim("SELECTEDVALUE ( 'Threshold'[Threshold], [Materiality 2026] )" in measure_table()["Threshold Value"],
          "the threshold defaults to the controller's materiality")
    qs = questions_table()
    by_req = Counter(r[3] for r in qs)
    claim(len(qs) == 12 and set(by_req) == {"Requirement 3", "Requirement 4", "Requirement 5", "Requirement 9"},
          "the Questions table holds twelve questions, each answered by Requirement 3, 4, 5 or 9")
    sections = check_sections()
    check = ('EVALUATE\nROW (\n    "Materiality 2026", ' + check_expr(claim, "materiality 2026") +
             ',\n    "Threshold", ' + check_expr(claim, "the threshold until the slider is moved (the controller's materiality)") +
             ',\n    "Accounts flagged", ' + check_expr(claim, "accounts above the threshold (with 3030)") +
             ',\n    "1045 change", ' + check_expr(claim, "1045 Inventory - Materials and Packaging: change 2025 to 2026 (debits less credits)") +
             "\n)")
    tp, tc = _tb_at(d, n17.ye(P)), _tb_at(d, n17.ye(C))
    re_change = xr(-(tc["3030"] - tp["3030"]))
    gl_rows = d.one("SELECT COUNT(*) FROM GLEntry")
    close_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber IN (SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%')")
    flag_text = "; ".join(f"{n} {chart[n]['name']} {'-' if v < 0 else '+'}${abs(v):,.2f}" for n, v in right)
    return dict(
        flag_text=flag_text, lost_text=named(lost), missed_text=named(missed), signed_text=named(signed),
        unmoved_text=named(unmoved), only_je_text=named(only_je), rec_c=n17.recorded(d, C), gl_rows=gl_rows,
        close_rows=close_rows, re_change=re_change, n_closes=len(d.closes),
        mat=mat, right=right, n_right=len(right), every=every, n_every=len(every), closed=closed, n_closed=len(closed),
        lost=lost, signed=signed, missed=missed, last=last, cash_last=round(at_last["1010"], 2),
        cash_ye=round(at_ye["1010"], 2), ap_last=round(-at_last["2010"], 2), ap_ye=round(-at_ye["2010"], 2),
        after=round(at_ye["1010"] - at_last["1010"], 2), only_je=only_je, unmoved=unmoved, posts_2030=posts_2030,
        m_gl=step(claim, gl, "Merged Queries", "Expanded JournalEntry", "Added Custom"),
        m_wt=step(claim, wt, "Source", "WorkingTB_Table", "Filtered Rows"),
        d_balance=dax(claim, "Balance"), d_change=dax(claim, "Balance 2026", "Change 2025 to 2026", "Absolute Change"),
        d_mat=dax(claim, "Materiality", "Materiality 2026"),
        d_flag=dax(claim, "Threshold Value", "Is Above Threshold", "Flag"),
        d_open=dax(claim, "Opening Entry Amount", "Postings after Opening", "Moved since Opening"),
        d_je=dax(claim, "Document Postings", "Journal Entries Only"),
        series="GENERATESERIES ( 0, 1000000, 25000 )", dax_check=check, test2=test_block(claim, 2),
        t_threshold=title(claim, "review", "threshold"), t_card=title(claim, "review", "materiality"),
        t_matrix=title(claim, "review", "reviewMatrix"), t_above=title(claim, "review", "aboveTable"),
        t_source=title(claim, "sources", "sourceMatrix"), t_opening=title(claim, "sources", "openingTable"),
        t_journal=title(claim, "sources", "journalOnly"), t_questions=title(claim, "questions", "questionTable"),
        t_by_source=title(claim, "postings", "bySource"), t_list=title(claim, "postings", "postingList"),
        n_checks=sections["Requirement 2"], opening_lines=len(opening), n_questions=len(qs), q_text=", ".join(f"{n17.word(v)} for {k}" for k, v in sorted(by_req.items())), workbook_ref=wb)


# --- Requirement 3: accrued expenses --------------------------------------------------------------------------------------------

@context("ch17.g3")
def g3(d, claim):
    need(d, claim)
    P, C, F = d.P, d.C, d.F
    comps = [n17.composition(d, y) for y in (F, P, C)]
    acc = n17.accruals(d)
    window = acc["window"]
    ye = lambda y: n17.ye(y)                                                         # noqa: E731
    with temp_view(d, "OpenAccruals"):
        old_q = quote("Requirement 3: the accruals older than the window")
        never_q = quote("Requirement 3: accruals young at")
        two_q = quote("Requirement 3: the accruals a rule of older than the last two month-ends")
        old_rows, never_rows, two_rows = len(run(d, old_q)), len(run(d, never_q)), len(run(d, two_q))
        by_ye = {r[0]: r for r in d.q("SELECT AsOfDate, SUM(CASE WHEN IsOld = 0 THEN OpenAmount ELSE 0 END), SUM(CASE WHEN IsOld = 1 THEN "
                                      "OpenAmount ELSE 0 END), SUM(IsOld) FROM OpenAccruals GROUP BY 1")}
        for y, c in zip((F, P, C), comps):
            claim(abs(by_ye[ye(y)][2] - c["old"]) < 0.005 and by_ye[ye(y)][3] == c["n_old"], f"the view's old items at {ye(y)} are the note's")
    # the wrong versions, each the saved view with one change
    with temp_view(d, "OpenAccruals", "OpenAccrualsInvoiceTotals", ("gl.Debit AS Amount, 'Invoice' AS Kind",
                                                                       "pil.LineTotal AS Amount, 'Invoice' AS Kind"),
                   ("WHERE ROUND(ac.Amount - c.Cleared, 2) > 0", "WHERE 1 = 1")):
        net = {r[0]: r[1] for r in d.q("SELECT AsOfDate, SUM(OpenAmount) FROM OpenAccrualsInvoiceTotals GROUP BY 1")}
    netted = [round(net[ye(y)] - (c["young"] + c["old"]), 2) for y, c in zip((F, P, C), comps)]
    claim(all(x < 0 for x in netted) and netted[0] > netted[1] > netted[2],
          "measuring what cleared an accrual by its invoice line's total, and netting the overbilled ones, understates the open accruals more each year")
    with temp_view(d, "OpenAccruals", "OpenAccruals30", ("> (SELECT MAX(LagDays) FROM Lags)", "> 30")):
        thirty = {r[0]: (r[1], r[2]) for r in d.q("SELECT AsOfDate, SUM(CASE WHEN IsOld = 1 THEN OpenAmount ELSE 0 END), SUM(IsOld) "
                                                  "FROM OpenAccruals30 GROUP BY 1")}
    t30 = [(round(thirty[ye(y)][0], 2), thirty[ye(y)][1]) for y in (F, P, C)]
    claim(t30[2][0] > comps[2]["old"] + 50000 and t30[2][0] > n17.materiality(d, C) and t30[2][1] > comps[2]["n_old"],
          "a round 30-day rule flags more old items than the longest observed wait does, more than materiality at the last year-end")
    a2040 = d.account("2040")
    ids = d.q("SELECT COUNT(*), SUM(g.Credit) FROM JournalEntry je JOIN GLEntry g ON g.SourceDocumentID = je.JournalEntryID "
              "AND g.AccountID = ? WHERE je.EntryType = 'Accrual'", a2040)[0]
    typed = d.q("SELECT COUNT(*), SUM(g.Credit) FROM JournalEntry je JOIN GLEntry g ON g.SourceDocumentType = 'JournalEntry' "
                "AND g.SourceDocumentID = je.JournalEntryID AND g.AccountID = ? WHERE je.EntryType = 'Accrual'", a2040)[0]
    claim(ids[0] == 2 * typed[0] and ids[1] > typed[1], "a join on the document ID alone doubles the rows, because shipments' freight credits share the numbers")
    adj = n17.adjustments(d)
    comp = comps[-1]
    only_last = comp["old"]
    claim(only_last > n17.materiality(d, C) * 0.5 and only_last > adj["a"]["A3"]["C"] * 2, "reversing the old accruals only at the last year-end puts far more into its income")
    with_opening = xr(comp["old"] + comp["opening"])
    claim(comp["opening"] > 0, "2040's opening line is a credit")
    cells = {k: formula(claim, "Accrued Expenses", c) for k, c in (("window", "G20"), ("pop", "G5"))}
    open_f = formula(claim, "Accrued Expenses", "M72")
    claim("SUMIFS(AccrualClearing[Debit]" in open_f and "ReversesEntryNumber" in open_f, "the workbook's open amount subtracts the invoice debits to 2040 and the adjustment entries")
    return dict(
        comps=comps, window=window, old_rows=old_rows, never_rows=never_rows, two_rows=two_rows, netted=netted, t30=t30,
        ids_rows=ids[0], ids_amount=round(ids[1], 2), typed_rows=typed[0], typed_amount=round(typed[1], 2),
        extra=round(ids[1] - typed[1], 2), only_last=only_last, with_opening=with_opening, opening=comp["opening"],
        a3=adj["a"]["A3"], mat_c=n17.materiality(d, C), n_q3=sum(1 for first, _, _ in script() if first.startswith("-- Requirement 3:")),
        f_open=open_f, f_window=cells["window"])


# --- Requirement 4: cutoff -----------------------------------------------------------------------------------------------------

@context("ch17.g4")
def g4(d, claim):
    need(d, claim)
    F, P, C = d.F, d.P, d.C
    inv = invoices_by_delivery(d)
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE substr(ShipmentDate, 1, 4) <> substr(DeliveryDate, 1, 4)") == 0,
          "every shipment is delivered in the year it ships")
    by_date = {y: [i for i in inv if i["date"][:4] != i["delivered"][:4] and i["delivered"][:4] == str(y)] for y in (F, P, C)}
    by_posting = {y: [i for i in inv if i["late"] and int(i["delivered"][:4]) == y] for y in (F, P, C)}
    claim(len(by_date[P]) != len(by_posting[P]) and len(by_date[C]) > len(by_posting[C]),
          "dating the cutoff test by the invoice date finds a different list, and invoices the ledger has right, at the last year-end")
    claim(all(not i["late"] for i in by_date[C]) and any(not i["late"] for i in by_date[P]),
          "invoices dated before their shipment, which the ledger posted in the year of delivery, are in the invoice-date list and not in the posting-date one")
    claim(any(i["late"] and i["number"] not in {j["number"] for j in by_date[P]} for i in inv if int(i["delivered"][:4]) == P),
          "an invoice dated in the year of delivery and posted in the next is in the posting-date list and not in the invoice-date one")
    cut = {y: n17.cutoff(d, y) for y in (F, P, C)}
    only_inv = {y: xr(sum(i["sub"] for i in cut[y]["invoices"])) for y in (F, P, C)}
    claim(only_inv[C] == 0 and cut[C]["total"] > 0, "a test of invoices alone finds nothing to adjust at the last year-end, where only shipment lines were never invoiced")
    a2 = n17.adjustments(d)["a"]["A2"]
    no_unbilled_effect = xr(only_inv[C] - only_inv[P])
    claim(no_unbilled_effect < 0 < a2["C"], "without the shipments never invoiced, the last year's revenue effect turns negative")
    # payroll variants
    pf, pp, pc = n17.payroll(d, F), n17.payroll(d, P), n17.payroll(d, C)
    claim(pf["method"] == "registers" and pp["method"] == "registers" and pc["method"] == "processed", "the earlier year-ends use registers, the last the processed periods")
    cal = []
    for y, p in ((F, pf), (P, pp)):
        c = p["cross"]
        cost = n17.register_cost(d, d.one("SELECT PayrollPeriodID FROM PayrollPeriod WHERE PeriodStartDate = ?", c["start"]))["total"]
        from datetime import date as _date
        days = (_date.fromisoformat(c["end"]) - _date.fromisoformat(c["start"])).days + 1
        inside = (_date(y, 12, 31) - _date.fromisoformat(c["start"])).days + 1
        cal.append(xr(p["full"]["cost"] + cost * inside / days))
    claim(cal[0] < pf["total"] and cal[1] < pp["total"], "prorating the crossing period by calendar days understates the payroll at both year-ends")
    open_none = xr(0 - pp["total"])
    claim(not pc["registered"] and open_none < 0, "the last pay periods have no registers, so an accrual from registers alone is zero")
    last = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate FROM PayrollPeriod WHERE Status = 'Processed' ORDER BY PeriodEndDate DESC LIMIT 1")[0]
    from notes.case3 import working_days
    one_cost = n17.register_cost(d, last[0])["total"]
    single = xr(one_cost / working_days(d, last[1], last[2]) * pc["p"]["left"])
    claim(single > pc["total"], "one pay period's cost per working day, applied to the days left, overstates the accrual")
    # interest
    ints = [n17.interest(d, y) for y in (F, P, C)]
    full_next = [xr(sum(i["interest"] for i in x["items"])) for x in ints]
    claim(full_next[2] > ints[2]["total"] and full_next[0] == ints[0]["total"], "accruing the whole next payment's interest overstates it at the last year-end, where a payment's period runs past the year-end")
    # the model script's queries and the workbook's formulas
    l6 = quote("Requirement 4: test L6")
    claim(len(run(d, l6)) == cut[C]["n_lines"], "the unbilled-lines query returns the shipment lines the note counts")
    l7_rows = run(d, quote("Requirement 4: test L7 of Audit.sql rerun"))
    l7 = len(l7_rows)
    claim(sum(1 for r in l7_rows if r[5] > 0) == 4 and sum(1 for r in l7_rows if r[5] == 0) == 2,
          "of the six pay periods that cross a year-end, four have registers and the last year's two have none")
    l8 = [(r[0], r[1]) for r in run(d, quote("Requirement 4: test L8 of Audit.sql rerun"))]
    f = {k: formula(claim, "Cutoff", c) for k, c in (("days_in", "B37"), ("share", "B38"), ("owed", "B47"), ("manuf", "B51"),
                                                      ("eight", "F31"), ("d_days", "D43"), ("d_cost", "D44"), ("d_daily", "D45"),
                                                      ("d_left", "D46"), ("d_owed", "D47"), ("accrued", "I77"), ("prev", "D77"), ("next", "E77"),
                                                      ("late", "B5"), ("unb", "B8"))}
    return dict(
        by_date=by_date, by_posting=by_posting, n_date={y: len(v) for y, v in by_date.items()},
        s_date={y: xr(sum(i["sub"] for i in v)) for y, v in by_date.items()}, only_inv=only_inv, no_unbilled=no_unbilled_effect,
        a2=a2, cal=cal, cal_short=[xr(pf["total"] - cal[0]), xr(pp["total"] - cal[1])], open_none=-open_none,
        single=single, single_over=xr(single - pc["total"]), full_next=full_next, ints=ints, l7=l7, l8=l8, f=f,
        std_c=cut[C]["std"], n_q4=sum(1 for first, _, _ in script() if first.startswith("-- Requirement 4:")),
        mat_c=n17.materiality(d, C))


# --- Requirement 5: the adjustments ---------------------------------------------------------------------------------------------

@context("ch17.g5")
def g5(d, claim):
    need(d, claim)
    F, P, C = d.F, d.P, d.C
    adj = n17.adjustments(d)
    a, total = adj["a"], adj["total"]
    mat_c, mat_p = n17.materiality(d, C), n17.materiality(d, P)
    # each year-end's amount taken as that year's effect (no reversal)
    no_reversal = xr(-adj["pay"][C]["total"] + adj["cut"][C] - adj["intr"][C] + adj["old"][C])
    claim(abs(no_reversal - adj["equity"][C]) < 0.005 and no_reversal < 0 < total["C"],
          "taking the year-end amounts as the year's effect gives the equity effect, negative where the year's effect is positive")
    whole_a1 = adj["pay"][C]["total"]
    claim(whole_a1 > 10 * abs(a["A1"]["C"]), "booking the whole accrual in the last year overstates its effect many times")
    opening = n17.opening_line(d, "1020")
    allowance = n17.allowance(d)
    claim(BUCKETS[-1][1] == 0.40, "the allowance rate for balances more than 90 days past due is 40%")
    with_opening = xr(allowance + BUCKETS[-1][1] * opening)
    with_interest = xr(d.one("SELECT SUM(PaymentAmount) FROM DebtScheduleLine dl JOIN DebtAgreement da ON da.DebtAgreementID = dl.DebtAgreementID "
                             "WHERE dl.PaymentDate > ? AND dl.PaymentDate <= ? AND da.OriginationDate <= ?", n17.ye(C), n17.ye(C + 1), n17.ye(C)))
    cur = n17.current_portion(d, C)
    claim(with_interest > cur, "the next year's scheduled payments, with their interest, exceed the principal due")
    adjusted_mat = xr(adj["adj_ni"][C] * 0.05)
    claim(abs(adjusted_mat - mat_c) > 1000, "materiality on adjusted income differs from materiality on recorded income")
    r5 = n17.r5(d, claim)
    claim(r5["agg_share"] > 0.4 and r5["share"] < 0.35, "the passed items are close to half of materiality, and the recorded adjustments' effect on income about a third")
    # the saved views and queries of the model script
    with temp_view(d, "OpenReceivables"):
        p1 = run(d, quote("Requirement 5: passed item P1"))
        claim(len(p1) == 2 and abs(p1[1][1] - allowance) < 0.005, "the allowance query returns the note's allowance at the last year-end")
    r1q = run(d, quote("Requirement 5: reclassification R1"))
    claim(len(r1q) == 2 and abs(r1q[1][1] - cur) < 0.005, "the current portion query returns the note's current portion")
    f = dict(
        a1_p=formula(claim, "Cutoff", "C67"), a1_c=formula(claim, "Cutoff", "D67"), cogs=formula(claim, "Cutoff", "D68"),
        sched_p=formula(claim, "Adjustments", "F5"), eq_c=formula(claim, "Adjustments", "I5"),
        p1=formula(claim, "Adjustments", "I15"), r1=formula(claim, "Adjustments", "I12"),
        adj=formula(claim, "Working TB", "O2"), adjusted=formula(claim, "Working TB", "R2"),
        line_re=adjustment_line(claim, "A1", C, 3030), line_cogs=adjustment_line(claim, "A1", C, 5080),
        line_liab=adjustment_line(claim, "A1", C, 2030), line_rev=adjustment_line(claim, "A2", C, 1020),
        mat=formula(claim, "Review", "C7"), share=formula(claim, "Adjustments", "C24"), cl=formula(claim, "Adjustments", "C26"))
    ws = workbook()["Adjustments"]
    claim(all(ws.cell(4, k).value for k in range(1, 12)), "the schedule of the model workbook has the eleven columns of the case's layout")
    lines = [r for r in range(55, ws.max_row + 1) if ws.cell(r, 1).value in ("A1", "A2", "A3", "A4", "R1", "R2")]
    return dict(
        no_reversal=no_reversal, whole_a1=whole_a1, with_opening=with_opening, allowance=allowance, with_interest=with_interest,
        cur=cur, adjusted_mat=adjusted_mat, f=f, n_lines=len(lines), opening=opening, mat_c=mat_c, mat_p=mat_p,
        trivial=xr(mat_c * 0.05), a3_share=a["A3"]["C"] / mat_c, rate_top=BUCKETS[-1][1], n_q5=sum(1 for first, _, _ in script() if first.startswith("-- Requirement 5:")),
        cogs_c=a["A1"]["C"])


# --- the cached values of the model workbook ---------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def cached():
    """The model workbook with its saved values, for the cells whose value a guide states."""
    import openpyxl
    return openpyxl.load_workbook(XLSX, read_only=False, data_only=True)


def adjustment_table() -> dict:
    """The AdjustmentLines Table of the model workbook: its header, how many lines it has, and what its totals row holds."""
    ws = cached()["Adjustments"]
    first, last = (int(re.sub(r"\D", "", x)) for x in ws.tables["AdjustmentLines"].ref.split(":"))
    head = [c.value for c in ws[first]]
    total = {h: ws.cell(last, k + 1).value for k, h in enumerate(head)}
    return dict(head=head, lines=last - first - 1, debit=round(total["Debit"], 2), credit=round(total["Credit"], 2),
                entries=len({(ws.cell(r, 1).value, ws.cell(r, 3).value) for r in range(first + 1, last)}))


# --- Requirement 6: the statements ----------------------------------------------------------------------------------------------

@context("ch17.g6")
def g6(d, claim):
    need(d, claim, "GLEntry", "Account", "JournalEntry", "FixedAsset", "FixedAssetEvent", "DebtScheduleLine")
    F, P, C = d.F, d.P, d.C
    adj = n17.adjustments(d)
    cf = {y: n17.cash_flows(d, y) for y in (P, C)}
    inc = {y: n17.income(d, y) for y in (P, C)}
    aj = {y: n17.adjusted_income(d, y) for y in (P, C)}
    rec_ni = {y: n17.net_income(d, y) for y in (P, C)}
    claim("Statements" in sheets() and "AdjustmentLines" in workbook()["Adjustments"].tables,
          "the model workbook has the Statements worksheet and the AdjustmentLines Table")
    # a cash flow statement that starts from recorded net income while the balances are adjusted
    start = {y: xr(adj["adj_ni"][y] - rec_ni[y]) for y in (P, C)}
    claim(start[C] > 0 > start[P], f"the adjustments raise {C} income and lower {P} income")
    dep_1090 = {y: xr(n17.depreciation_debits(d, "1090", y)) for y in (P, C)}
    dep_6130 = {y: xr(n17.depreciation_debits(d, "6130", y)) for y in (P, C)}
    claim(all(dep_1090[y] > 0 and dep_6130[y] > 0 for y in (P, C)),
          "each year's depreciation is charged partly to an expense account and partly to 1090")
    loss = {y: inc[y]["loss"] for y in (P, C)}
    claim(all(v > 0 for v in loss.values()), "each year has a loss on a disposal")
    claim(cf[C]["notes_financed"] > 0 and cf[P]["notes_financed"] == 0, f"only {C} has equipment financed by a note")
    claim(abs(aj[C]["intr"] - cf[C]["interest_paid"] - (-adj["a"]["A4"]["C"])) < 0.005,
          f"the adjusted interest expense of {C} is the interest paid plus the accrual's effect (A4)")
    claim(abs(cf[P]["proceeds"]) > 0 and cf[C]["proceeds"] == 0, f"the {P} disposal had proceeds and the {C} one none")
    events = d.q("SELECT strftime('%Y', fe.EventDate), fe.EventType, fe.FinancingType, fa.AssetCode, fe.Amount, fe.ProceedsAmount "
                 "FROM FixedAssetEvent fe INNER JOIN FixedAsset fa ON fa.FixedAssetID = fe.FixedAssetID "
                 "WHERE fe.FinancingType IN ('Note', 'None') ORDER BY fe.EventDate")
    claim(len(events) == 4 and [e[2] for e in events] == ["Note", "None", "Note", "None"],
          "the noncash query returns two acquisitions financed by notes and two disposals")
    interest_gap = xr(aj[C]["intr"] - cf[C]["interest_paid"])
    # the Review file
    lines = adjustment_table()
    claim(lines["head"] == ["No", "Adjustment", "YearEnd", "Account", "Presentation", "Amount", "Type", "Evidence",
                            "AccountName", "StatementLine", "Debit", "Credit"],
          "the AdjustmentLines Table has the twelve columns the Review file reads")
    claim(lines["entries"] == 4 * 3 + 2 * 2, "the Table holds A1 to A4 at three year-ends and R1 and R2 at two")
    claim(abs(lines["debit"] - lines["credit"]) < 0.005 and lines["debit"] > 0, "the totals row holds equal debits and credits")
    page = [title(claim, "packageTests", v) for v in ("testCards", "entryMatrix", "agreeTable", "assetTable", "incomeMatrix")]
    has_visual(claim, "packageTests", "packageAnswer")
    sections = check_sections()
    adj_m = table_m("AdjustmentLines")
    ck = ('EVALUATE\nROW (\n    "Entries out of Balance", ' + check_expr(claim, "every entry nets to zero: entries out of balance") +
          ',\n    "Lines on Cash", ' + check_expr(claim, "lines on 1010 Cash") +
          ',\n    "Net income difference 2026", ' + check_expr(claim, "adjusted net income 2026: difference") +
          ',\n    "Adjusted accounts disagreeing 2026", ' + check_expr(claim, "accounts whose adjusted balance at 2026-12-31 differs from the workbook's") +
          "\n)")
    f = dict(
        cash=formula(claim, "Statements", "B5"), accounts_payable=formula(claim, "Statements", "B13"),
        loss=formula(claim, "Statements", "B37"), before_tax=formula(claim, "Statements", "B39"),
        re_reported=formula(claim, "Statements", "C54"), re_correction=formula(claim, "Statements", "C55"),
        re_restated=formula(claim, "Statements", "C56"), dep=formula(claim, "Statements", "B69"),
        other=formula(claim, "Statements", "B75"), purchases=formula(claim, "Statements", "B77"),
        proceeds=formula(claim, "Statements", "B78"), principal=formula(claim, "Statements", "B80"),
        check=formula(claim, "Statements", "B85"), same=formula(claim, "Statements", "B86"),
        interest=formula(claim, "Statements", "B89"), noncash=formula(claim, "Statements", "B91"))
    return dict(
        start=start, dep_1090=dep_1090, dep_6130=dep_6130, loss=loss, loss_double={y: xr(2 * loss[y]) for y in (P, C)},
        noted=cf[C]["notes_financed"], equity_gap=xr(-adj["total"]["re"]), interest_gap=interest_gap,
        interest_adjusted=aj[C]["intr"], sign_gap={y: xr(2 * abs(adj["total"][k])) for y, k in ((P, "P"), (C, "C"))},
        effect={y: xr(abs(adj["total"][k])) for y, k in ((P, "P"), (C, "C"))},
        n_lines=lines["lines"], n_entries=lines["entries"], totals_debit=lines["debit"],
        n_checks=sections["Requirement 6"], f=f, d_amount=dax(claim, "Adjustment Amount", "Adjusted P&L Amount", "Adjusted Net Income"),
        d_balance=dax(claim, "Largest Entry Imbalance", "Lines on Cash"),
        m_adj=step(claim, adj_m, "Removed Other Columns", "Filtered Rows", "Changed Type1"),
        test3=test_block(claim, 3), test4=test_block(claim, 4), test5=test_block(claim, 5), dax_check=ck,
        t_cards=page[0], t_entries=page[1], t_agree=page[2], t_assets=page[3], t_income=page[4],
        n_events=len(events), tests=sections)


# --- Requirement 7: the notes ---------------------------------------------------------------------------------------------------

@context("ch17.g7")
def g7(d, claim):
    need(d, claim, "GLEntry", "Account", "JournalEntry", "FixedAsset", "FixedAssetEvent", "DebtAgreement", "DebtScheduleLine",
         "SalesInvoice", "SalesInvoiceLine", "ServiceEngagement", "ServiceTimeEntry", "ServiceBillingLine", "CreditMemo")
    F, P, C = d.F, d.P, d.C
    reg = n17.register(d)
    claim("Notes" in sheets() and "Fixed Assets" in sheets() and "FixedAssets" in workbook()["Fixed Assets"].tables,
          "the model workbook has the Notes worksheet and the FixedAssets Table")

    def register_dep(year: int, through_disposal_month: bool = False) -> float:
        total = 0.0
        for a in reg:
            first, last = n17.month_index(a["service"]) + 1, n17.month_index(a["service"]) + a["life"]
            if a["disposal"]:
                last = min(last, n17.month_index(a["disposal"]) - (0 if through_disposal_month else 1))
            total += sum(1 for m in range(first, last + 1) if m // 12 == year) * xr(a["cost"] / a["life"])
        return xr(total)

    ledger_dep = {y: xr(sum(n17.depreciation_by_contra(d, k, y) for k in n17.CLASSES)) for y in (P, C)}
    claim(all(abs(register_dep(y) - ledger_dep[y]) < 0.005 for y in (P, C)), "the register, month by month, reproduces the ledger's depreciation")
    over = {y: xr(register_dep(y, True) - ledger_dep[y]) for y in (P, C)}
    claim(all(v > 0 for v in over.values()), "counting the month of disposal depreciates each disposed asset one month more")
    # the maturities by payment amount, which include interest
    five = d.q("SELECT SUM(PrincipalAmount), SUM(PaymentAmount) FROM DebtScheduleLine WHERE PaymentDate > ? AND PaymentDate <= ?",
               n17.ye(C), n17.ye(C + 5))[0]
    next_year = d.q("SELECT SUM(PrincipalAmount), SUM(PaymentAmount) FROM DebtScheduleLine WHERE substr(PaymentDate, 1, 4) = ?", str(C + 1))[0]
    claim(five[1] > five[0] and next_year[1] > next_year[0], "the scheduled payments exceed the principal they repay")
    claim(d.one("SELECT COUNT(*) FROM DebtScheduleLine WHERE PaymentDate > ?", n17.ye(C + 5)) == 0,
          f"no note payment falls after {C + 5}")
    # revenue
    ledger_opr = {y: n17.income(d, y)["opr"] for y in (P, C)}
    adjusted_opr = {y: n17.adjusted_income(d, y)["opr"] for y in (P, C)}
    a2 = n17.adjustments(d)["a"]["A2"]
    claim(abs(adjusted_opr[C] - ledger_opr[C] - a2["C"]) < 0.005 and abs(adjusted_opr[P] - ledger_opr[P] - a2["P"]) < 0.005,
          "adjusted operating revenue differs from the ledger's by the revenue adjustment's effect on income")
    claim(adjusted_opr[C] > ledger_opr[C] and adjusted_opr[P] < ledger_opr[P],
          f"the cutoff adjustment raises {C} revenue and lowers {P} revenue")
    # services
    eng = d.q("SELECT ServiceEngagementID, PlannedHours FROM ServiceEngagement WHERE Status <> 'Billed'")
    claim(len(eng) == 1, "one engagement is not Billed")
    billed_e = d.one("SELECT COALESCE(SUM(BilledHours), 0) FROM ServiceBillingLine WHERE ServiceEngagementID = ?", eng[0][0])
    worked_e = d.one("SELECT COALESCE(SUM(BillableHours), 0) FROM ServiceTimeEntry WHERE ServiceEngagementID = ?", eng[0][0])
    claim(abs(billed_e - worked_e) < 0.005 and eng[0][1] > worked_e, "that engagement billed every hour worked, and planned more")
    short_hours = round(eng[0][1] - billed_e, 2)
    # accrued liabilities
    s_c, s_p = n17.statement(d, C), n17.statement(d, P)
    opening_2030 = n17.opening_line(d, "2030")
    claim(abs(s_c["payroll"] - n17.adjustments(d)["pay"][C]["total"] - opening_2030) < 0.005,
          "payroll and related is the wages owed plus the opening line of 2030")
    claim(abs(s_c["inv"] - (s_c["fg"] + s_c["mat"] + s_c["wip"])) < 0.005, "inventories are finished goods, materials and work in process")
    # the workbook's formulas
    f = dict(
        cost_open=formula(claim, "Notes", "B5"), cost_disp=formula(claim, "Notes", "D6"),
        acc_dep=formula(claim, "Notes", "C13"), roll=formula(claim, "Notes", "I6"), register=formula(claim, "Notes", "J6"),
        note_bal=formula(claim, "Notes", "J36"), due=formula(claim, "Notes", "B42"), revenue=formula(claim, "Notes", "B54"),
        segment=formula(claim, "Notes", "B73"), payroll=formula(claim, "Notes", "B100"), inventories=formula(claim, "Notes", "B111"),
        first_month=formula(claim, "Fixed Assets", "R2"), last_month=formula(claim, "Fixed Assets", "S2"),
        monthly=formula(claim, "Fixed Assets", "T2"), dep_year=formula(claim, "Fixed Assets", f"W2"))
    # cost of every asset in the register, disposed ones included
    all_cost = xr(sum(a["cost"] for a in reg))
    disposed = xr(sum(a["cost"] for a in reg if a["disposal"] and a["disposal"] <= n17.ye(C)))
    cost_c = xr(n17.bal(d, n17.accounts_of(d, "Fixed Asset"), n17.ye(C)))
    claim(abs(all_cost - disposed - cost_c) < 0.005 and disposed > 0, "the register's cost less the disposed assets' is the ledger's cost")
    interest_paid = {y: n17.cash_flows(d, y)["interest_paid"] for y in (P, C)}
    money = lambda x: f"${x:,.2f}"                                                        # noqa: E731
    r7 = n17.r7(d, claim)
    rev_text = "; ".join(f"{x['label']} {money(x['c'])} ({money(x['p'])})" for x in r7["revenue"])
    seg_text = "; ".join(f"{x['name']} {money(x['c'])} ({money(x['p'])})" for x in r7["segments"])
    mat_text = "; ".join(f"{y} {money(v)}" for y, v in r7["maturities"])
    return dict(
        all_cost=all_cost, disposed=disposed, interest_paid=interest_paid, rev_text=rev_text, seg_text=seg_text,
        mat_text=mat_text, class_text=", ".join(f"{c['name']} {money(c['c'])}" for c in r7["classes"]),
        over=over, five_total=xr(five[1]), five_principal=xr(five[0]), interest_left=xr(five[1] - five[0]),
        next_payments=xr(next_year[1]), next_principal=xr(next_year[0]),
        ledger_opr=ledger_opr, adjusted_opr=adjusted_opr, revenue_gap={y: xr(adjusted_opr[y] - ledger_opr[y]) for y in (P, C)},
        short_hours=short_hours, payroll_only=xr(s_c["payroll"] - opening_2030),
        f=f, n_q7=sum(1 for first, _, _ in script() if first.startswith("-- Requirement 7:")),
        n_sheet=len(sheets()))


# --- Requirement 8: past the balance-sheet date -----------------------------------------------------------------------------------------

@context("ch17.g8")
def g8(d, claim):
    need(d, claim, "GLEntry", "Account", "DisbursementPayment", "PurchaseInvoice", "PayrollPeriod", "PayrollRegister", "DebtScheduleLine")
    F, P, C = d.F, d.P, d.C
    after = n17.ye(C)
    claim("Later Events" in sheets(), "the model workbook has the Later Events worksheet")
    n_pay, paid = d.q("SELECT COUNT(*), SUM(Amount) FROM DisbursementPayment WHERE PaymentDate > ?", after)[0]
    last = d.one("SELECT MAX(PostingDate) FROM GLEntry")
    same_n, same_amount = d.q("SELECT COUNT(*), SUM(Amount) FROM DisbursementPayment WHERE PaymentDate BETWEEN ? AND ?",
                              f"{C}-01-01", f"{C}{last[4:]}")[0]
    share = paid / same_amount
    claim(share < 0.2, f"the {d.N} payments are a small share of the same weeks of {C}")
    split = d.one("SELECT COUNT(*) FROM (SELECT PurchaseInvoiceID FROM DisbursementPayment WHERE PaymentDate > ? "
                  "GROUP BY PurchaseInvoiceID HAVING COUNT(*) > 1)", after)
    n_inv = d.one("SELECT COUNT(DISTINCT PurchaseInvoiceID) FROM DisbursementPayment WHERE PaymentDate > ?", after)
    claim(n_pay - n_inv == split and split > 0, "the payments outnumber the invoices they pay only because some invoices are paid in parts")
    cash_ye = xr(_tb_at(d, after)["1010"])
    cash_last = xr(_tb_at(d, last)["1010"])
    claim(abs((cash_ye - cash_last) - paid) < 0.005, "cash at the ledger's last date is the year-end cash less the later payments")
    s_c, s_p = n17.statement(d, C), n17.statement(d, P)
    claim(s_c["cr"] > 2 and s_c["qr"] < 1, "the current ratio is comfortable and the quick ratio is below one")
    mat, issues = s_c["mat"], n17.materials_issues(d, C)
    months = round(mat / issues * 12, 1)
    claim(months > 12, "materials on hand exceed twelve months of issues")
    f = dict(payments=formula(claim, "Later Events", "B12"), due=formula(claim, "Later Events", "B25"),
             periods=formula(claim, "Later Events", "B26"), notes=formula(claim, "Later Events", "B28"),
             full=formula(claim, "Later Events", "B22"), issues=formula(claim, "Later Events", "B37"))
    ledger_after = d.q("SELECT COUNT(*) FROM GLEntry WHERE PostingDate > ?", after)[0][0]
    return dict(share=share, split=split, split_word=n17.word(split), cash_ye=cash_ye, cash_last=cash_last, months=months, f=f,
                cr_c=s_c["cr"], cr_p=s_p["cr"], qr_c=s_c["qr"], qr_p=s_p["qr"], ledger_after=ledger_after,
                n_q8=sum(1 for first, _, _ in script() if first.startswith("-- Requirement 8:")), last=last)


# --- Requirement 9: the package and the memo ---------------------------------------------------------------------------------------------

@context("ch17.g9")
def g9(d, claim):
    need(d, claim, "GLEntry", "Account", "JournalEntry")
    F, P, C = d.F, d.P, d.C
    adj = n17.adjustments(d)
    claim("Memo" in sheets(), "the model workbook has the Memo worksheet")
    adj_ni = adj["adj_ni"][C]
    mat = n17.materiality(d, C)
    provision = round(adj_ni * n17.FEDERAL, -4)
    o = dict(ar=n17.opening_line(d, "1020"), prepaid=n17.opening_line(d, "1050"), ap=n17.opening_line(d, "2010"),
             payroll=n17.opening_line(d, "2030"), accrued=n17.opening_line(d, "2040"))
    equity = xr(o["ap"] + o["payroll"] + o["accrued"] - o["ar"] - o["prepaid"])
    payables_only = xr(o["ap"] - equity)
    claim(payables_only > 0, "counting the payables alone as the equity effect overstates it")
    stax = xr(-n17.bal(d, n17.SALES_TAX, n17.ye(C)))
    # the model memo's length
    ws = cached()["Memo"]
    paragraphs = [str(ws.cell(r, 1).value) for r in range(31, ws.max_row + 1) if ws.cell(r, 1).value]
    words = sum(len(re.findall(r"\S+", p)) for p in paragraphs)
    claim(len(paragraphs) >= 9 and 500 < words < 1100, "the model memo has about nine paragraphs and fits two pages")
    qs = [r for r in questions_table() if r[3] == "Requirement 9"]
    claim(len(qs) == 5, "five questions of the Review file's Questions table are answered by Requirement 9")
    r5 = n17.r5(d, claim)
    f = dict(provision=formula(claim, "Memo", "C6"), multiple=formula(claim, "Memo", "C7"),
             rent=formula(claim, "Memo", "C11"), leases=formula(claim, "Memo", "C12"), stax=formula(claim, "Memo", "C13"),
             memo_debits=formula(claim, "Memo", "C14"), remittances=formula(claim, "Memo", "C15"),
             assets=formula(claim, "Memo", "C21"), liabilities=formula(claim, "Memo", "C22"), equity=formula(claim, "Memo", "C23"),
             passed=formula(claim, "Memo", "C27"))
    return dict(provision=provision, multiple=provision / mat, payables_only=payables_only, memo_words=words,
                memo_paragraphs=len(paragraphs), questions=[dict(n=r[0], text=r[1], accounts=r[2]) for r in qs], f=f,
                passed=r5["aggregate"], passed_share=r5["agg_share"], mat=mat, stax=stax, equity=equity, o=o,
                adj_ni=adj_ni, n_matters=8)
