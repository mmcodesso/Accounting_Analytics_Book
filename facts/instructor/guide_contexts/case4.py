"""The Part IV case's instructor guides: the values the guides state, and the claims their wording makes.

The case (cases/part-4-case.qmd, "Finding the Cash Behind the Profit") is worked in one Power BI file, Charles River Cash
Case.pbix, whose model answer is the project outputs/companion/solutions/PartIV-case (twelve pages, a Tests tab and a
Checks tab of several hundred rows, read from the project).  The registered notes case4.r1 to case4.r6 (facts/notes/case4.py) already supply the expected
values of the requirements, as the SQL twins of the model's DAX and Power Query.  These contexts add what the guides'
model paths need beyond them:

- the Power Query M and the DAX of the model answer, quoted from the project itself, so a quoted step cannot drift from the
  file the instructor opens (a quote the project does not hold is a failed claim),
- the symptom of every wrong version a guide names (a profile of the first thousand rows, an Item merge that is not
  grouped, a receipt merged through the order header, a balance divided by a quarter's flow, a cost of goods sold that
  keeps the closes, a null that swallows an open balance, ...), computed read-only on the dataset the way the model would
  show it,
- the titles of the visuals the guides name (read from the report files) and the case's deck, with its slide numbers,
- claims on every table and column the guides name and on every statement about the data that another dataset could falsify.

What the project proves and what only Desktop shows: the project encodes the model and the structure of every page, and its
Checks tab (DAX query view) recomputes the values of the requirements, so a result is "proved" when a Checks row names it.
How a visual renders (the waterfall's colors, the icons, the tooltip, the drill-through button) is visible only in Desktop.

Keys: case4.chapter (the case note) and case4.g1 to case4.g6 (the requirements; Requirements 1 to 5 are each used next to
the note case4.r1 to case4.r5 that supplies the values of the requirement's instructor note, Requirement 6 next to case4.r6).
"""

from __future__ import annotations

import base64
import json
import re
import zlib
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch13 import _block
from notes import case4 as n4

REPO = Path(__file__).resolve().parents[3]
CASE = REPO / "cases" / "part-4-case.qmd"
DECK = REPO / "slides" / "case-part-4" / "index.qmd"
DOWNLOADS = REPO / "front-matter" / "downloads.qmd"
PROJECT = REPO / "outputs" / "companion" / "solutions" / "PartIV-case" / "Charles River Cash Case"
MODEL = PROJECT / "Charles River Cash Case.SemanticModel"
REPORT = PROJECT / "Charles River Cash Case.Report"

SCHEMA = {
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "SourceDocumentID", "FiscalYear"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"],
    "JournalEntry": ["EntryNumber", "EntryType", "PostingDate"],
    "PurchaseRequisition": ["RequisitionID", "RequestDate", "RequestedByEmployeeID", "ItemID", "Quantity", "EstimatedUnitCost",
                            "Justification", "ApprovedByEmployeeID", "Status", "SupplyPlanRecommendationID"],
    "GoodsReceipt": ["GoodsReceiptID", "ReceiptDate"],
    "GoodsReceiptLine": ["GoodsReceiptLineID", "GoodsReceiptID", "POLineID", "ItemID", "QuantityReceived", "ExtendedStandardCost"],
    "PurchaseOrder": ["PurchaseOrderID", "OrderDate", "RequisitionID"],
    "PurchaseOrderLine": ["POLineID", "PurchaseOrderID", "RequisitionID", "ItemID", "Quantity", "UnitCost"],
    "MaterialIssue": ["MaterialIssueID", "IssueDate", "WorkOrderID"],
    "MaterialIssueLine": ["MaterialIssueLineID", "MaterialIssueID", "ItemID", "QuantityIssued", "ExtendedStandardCost"],
    "InventoryPolicy": ["ItemID", "TargetDaysSupply", "EffectiveEndDate"],
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "SupplyMode"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "CustomerID", "TaxAmount", "GrandTotal"],
    "CashReceiptApplication": ["SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "CreditMemo": ["OriginalSalesInvoiceID", "CreditMemoDate", "GrandTotal"],
    "PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "ReceivedDate", "DueDate", "SupplierID", "GrandTotal"],
    "DisbursementPayment": ["PurchaseInvoiceID", "PaymentDate", "Amount"],
    "DebtScheduleLine": ["DebtAgreementID", "PaymentDate", "PrincipalAmount", "EndingPrincipal", "Status"],
    "WorkOrder": ["WorkOrderID", "WorkOrderNumber", "DueDate", "CompletedDate"],
    "Employee": ["EmployeeID", "JobTitle"],
}
PAGES = ["about", "validation", "balanceSheet", "cashBridge", "bridgeDetail", "workingCapital", "wcTooltip", "materialsBuild",
         "materialsTarget", "reconciliations", "memo", "notes"]
EXHIBITS = ["the cash bridge for fiscal {P} and {C}", "the restated cash flow sections", "the working-capital measures by quarter",
            "the materials build by channel with the {N} target", "the findings with their dispositions"]


# --- the project --------------------------------------------------------------------------------------------------------

def _model_text(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def table_m(name: str) -> list[str]:
    """The M of a loaded table's partition in the solution project, one stripped line per step."""
    return _block(_model_text(f"tables/{name}.tmdl"), "source =")


def expression_m(name: str) -> list[str]:
    """The M of a query that does not load (Enable load cleared), from expressions.tmdl."""
    return _block(_model_text("expressions.tmdl"), f"expression {name} =")


def step(claim, lines: list[str], *names: str, split: bool = False) -> str:
    """The named steps of an M query as the formula bar reads them; `split` breaks an if-then-else chain after each else."""
    out = []
    for n in names:
        found = [l for l in lines if l.startswith(f'#"{n}" =') or l.startswith(f"{n} =")]
        claim(len(found) == 1, f"the solution project's query has the step {n}")
        for l in found:
            out.append("    " + (l.rstrip(",").replace(" else if ", "\n        else if ") if split else l.rstrip(",")))
    return "\n".join(out)


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
    """The DAX of the named measures, one block per measure, as the project holds it."""
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


def query_tab(name: str) -> str:
    return (MODEL / "DAXQueries" / f"{name}.dax").read_text(encoding="utf-8").strip()


def test_block(claim, n: int) -> str:
    """Test n of the Tests tab, comment line first."""
    parts = re.split(r"(?m)^(?=// Test \d)", query_tab("Tests"))
    found = [p.strip() for p in parts if p.startswith(f"// Test {n}:")]
    claim(len(found) == 1, f"the Tests tab holds Test {n}")
    return found[0] if found else ""


def table_source(claim, table: str) -> str:
    """The DAX of a calculated table's partition (the field parameter and the what-if series)."""
    lines = _block(_model_text(f"tables/{table}.tmdl"), "source =")
    claim(bool(lines), f"the table {table} of the solution project is a calculated table")
    if len(lines) > 2 and lines[0] == "{":
        return "\n".join([lines[0]] + ["    " + l for l in lines[1:-1]] + [lines[-1]])
    return "\n".join(lines)


def findings_table() -> list[list[str]]:
    """The rows of the Findings table the project types with Enter data, decoded from the M the project holds."""
    text = _model_text("tables/Findings.tmdl")
    blob = re.search(r'Binary\.FromText\("([^"]+)"', text).group(1)
    return json.loads(zlib.decompress(base64.b64decode(blob), -15).decode("utf-8"))


def need(d, claim, *tables: str) -> None:
    schema(d, claim, {t: SCHEMA[t] for t in (tables or SCHEMA)})


def deck_titles() -> list[str]:
    """The slide titles of the case's deck in order, the title slide first."""
    titles = ["(title slide)"]
    for line in DECK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,2} (.+?)\s*(\{[^}]*\})?\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    return titles


def at(titles: list[str], first: str, nth: int = 1) -> int:
    hits = [n for n, t in enumerate(titles, 1) if t.startswith(first)]
    return hits[nth - 1]


def span(titles: list[str], first: str, after: str) -> str:
    start, end = at(titles, first), at(titles, after) - 1
    return str(start) if end <= start else f"{start} to {end}"


def check_sections() -> dict[str, int]:
    """The rows of the Checks tab by section (Requirement 1 ... Requirement 6)."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for sec in re.findall(r'ROW \( "Section", "([^"]*)"', text):
        counts[sec] = counts.get(sec, 0) + 1
    return counts


# --- the case note -------------------------------------------------------------------------------------------------------

@context("case4.chapter")
def chapter(d, claim):
    need(d, claim)
    titles = deck_titles()
    claim(len(titles) == 34, "the case's deck has 34 slides")
    text = CASE.read_text(encoding="utf-8")
    n_req = len(re.findall(r"^\*\*Requirement \d+:", text, re.M))
    claim(n_req == 6, "the case has six requirements")
    claim("Milestone" not in text, "the case has no milestones")
    downloads = DOWNLOADS.read_text(encoding="utf-8")
    claim("PartIV-case.zip" in downloads, "the Downloads page lists the Part IV solution, PartIV-case.zip")
    claim(MODEL.is_dir() and REPORT.is_dir(), "the solution project of the Part IV case is in outputs/companion/solutions")
    claim(sorted(p.name for p in (REPORT / "definition" / "pages").iterdir() if p.is_dir()) == sorted(PAGES),
          "the solution project has the twelve pages the guides name")
    pages = json.loads((REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    hidden = [p for p in PAGES if '"visibility": "HiddenInViewMode"' in
              (REPORT / "definition" / "pages" / p / "page.json").read_text(encoding="utf-8")]
    claim(pages == PAGES and sorted(hidden) == ["bridgeDetail", "wcTooltip"], "two of the twelve pages are hidden: the drill-through and the tooltip")
    sections = check_sections()
    claim(sum(sections.values()) > 400 and len(sections) == 6, "the Checks tab holds several hundred rows in six sections")
    tables = sorted(p.stem for p in (MODEL / "definition" / "tables").glob("*.tmdl"))
    n_measures = len(measure_table())
    claim(n_measures > 100, "the Key Measures table holds over a hundred measures, each with its definition as a description")
    thru = n4.data_through(d)
    claim(thru == f"{d.C}-12-31", "Data Through is the last day of the current fiscal year")
    pay_end = d.one("SELECT MAX(PostingDate) FROM GLEntry WHERE SourceDocumentType IN ('PayrollSummary', 'PayrollPayment')")
    last = d.one("SELECT MAX(PostingDate) FROM GLEntry")
    claim(pay_end < thru < last, "payroll ends before Data Through and the ledger runs past it: three dates, not one")
    b = n4.bridge(d, d.C)
    first_year = n4.bridge(d, d.F)
    return dict(
        n_req=n_req, slides=len(titles), checks=sum(sections.values()), per_req=sections, n_pages=len(PAGES), n_hidden=len(hidden),
        n_tables=len(tables), n_measures=n_measures, thru=thru, pay_end=pay_end, last=last, y=d.C, f=d.F, p=d.P, n=d.N,
        ni=b["net_income"], cash=b["cash"], inv=b["inventories"], first_cash=first_year["cash"],
        slide=dict(
            intro=at(titles, "In this case"), question=at(titles, "Where did the cash go"), handin=at(titles, "What you will hand in"),
            criteria=span(titles, "How your work will be judged", "The Situation"),
            situation=span(titles, "A profit, and less cash", "The Data You Will Use"),
            questions=at(titles, "Four questions"), evidence=at(titles, "The report must carry"),
            data=span(titles, "A new file for the case", "Requirements"), queries=at(titles, "The queries the case builds"),
            watch1=at(titles, "Watch out: rows"), watch2=at(titles, "Watch out: a ratio"),
            flow_check=at(titles, "Each balance has its flow") - 1, flow_answer=at(titles, "Each balance has its flow"),
            six=at(titles, "Six requirements"), r1=at(titles, "Build and validate"), r2=at(titles, "Explain where the cash went"),
            cash_check=at(titles, "Only cash goes in the statement") - 1, cash_answer=at(titles, "Only cash goes in the statement"),
            r3=at(titles, "Measure how fast"), r4=at(titles, "Trace the materials"), r5=at(titles, "Test the balances behind"),
            disp_check=at(titles, "Each exception has its disposition") - 1, disp_answer=at(titles, "Each exception has its disposition"),
            r6=at(titles, "Write the decision memo"), before=at(titles, "Before you submit"),
            ahead=span(titles, "From one tool to all of them", "About these slides")))


# --- requirement 1: the file, the profiles, Validation, Data Through ---------------------------------------------------------

@context("case4.g1")
def g1(d, claim):
    need(d, claim)
    y = d.C
    ch = n4.CHANNEL
    # the profile of the first 1,000 rows (Power Query's default), against the entire data set
    top = {r[0]: (r[1], r[2]) for r in d.q(f"SELECT {ch}, COUNT(*), SUM(r.ApprovedByEmployeeID IS NULL) FROM "
                                           "(SELECT * FROM PurchaseRequisition ORDER BY RequisitionID LIMIT 1000) r GROUP BY 1")}
    allr = {r[0]: (r[1], r[2]) for r in d.q(f"SELECT {ch}, COUNT(*), SUM(r.ApprovedByEmployeeID IS NULL) FROM PurchaseRequisition r GROUP BY 1")}
    top_approved = d.one("SELECT COUNT(*) FROM (SELECT * FROM PurchaseRequisition ORDER BY RequisitionID LIMIT 1000) WHERE Status = 'Approved'")
    all_approved = d.one("SELECT COUNT(*) FROM PurchaseRequisition WHERE Status = 'Approved'")
    claim(top_approved == 0 < all_approved, "the first thousand requisitions are all converted to orders, so none of the approved ones is in the profile")
    top_no_app = sum(v[1] for v in top.values())
    all_no_app = sum(v[1] for v in allr.values())
    claim(top_no_app < all_no_app, "the profile of the first thousand rows shows fewer requisitions without an approver than the entire data set")
    claim(top["Shortfall"][0] < 0.2 * 1000 < top["Supply plan"][0], "in the first thousand requisitions the shortfall channel is a small share, against most of the data set")
    # the Item merge with the policy rows not grouped
    items = d.one("SELECT COUNT(*) FROM Item")
    ungrouped = d.one("SELECT COUNT(*) FROM Item i LEFT JOIN InventoryPolicy p ON p.ItemID = i.ItemID")
    claim(ungrouped > items, "merging the policy rows without grouping them by item makes some items appear twice")
    claim(d.one("SELECT COUNT(*) FROM (SELECT ItemID FROM InventoryPolicy GROUP BY ItemID HAVING MIN(TargetDaysSupply) <> MAX(TargetDaysSupply))") == 0,
          "an item's policy rows (one for each warehouse) carry the same target, so grouping by item and taking the maximum loses nothing")
    # the receipt merged through the order header
    hdr = d.q("SELECT COUNT(*), SUM(l.ExtendedStandardCost) FROM GoodsReceiptLine l JOIN PurchaseOrderLine p ON p.POLineID = l.POLineID "
              "JOIN PurchaseOrder o ON o.PurchaseOrderID = p.PurchaseOrderID WHERE o.RequisitionID IS NULL")[0]
    hdr_mat = d.q("SELECT COUNT(*), SUM(l.ExtendedStandardCost) FROM GoodsReceiptLine l JOIN Item i ON i.ItemID = l.ItemID "
                  "JOIN PurchaseOrderLine p ON p.POLineID = l.POLineID JOIN PurchaseOrder o ON o.PurchaseOrderID = p.PurchaseOrderID "
                  "WHERE o.RequisitionID IS NULL AND i.ItemGroup IN ('Raw Materials', 'Packaging')")[0]
    lines = d.one("SELECT COUNT(*) FROM GoodsReceiptLine")
    claim(hdr[0] > 0.3 * lines, "the order header's RequisitionID is blank on lines that carry over a third of the receipt lines")
    # materials against all receipt lines, by year
    by_year = d.q("SELECT substr(g.ReceiptDate, 1, 4), SUM(l.ExtendedStandardCost), SUM(CASE WHEN i.ItemGroup IN ('Raw Materials', 'Packaging') "
                  "THEN l.ExtendedStandardCost ELSE 0 END) FROM GoodsReceiptLine l JOIN GoodsReceipt g ON g.GoodsReceiptID = l.GoodsReceiptID "
                  "JOIN Item i ON i.ItemID = l.ItemID GROUP BY 1 ORDER BY 1")
    claim([int(r[0]) for r in by_year] == d.years and all(r[1] > r[2] for r in by_year), "every year's receipts of all items exceed its receipts of materials")
    # net income with the closes left in
    ni_closes = [d.one("SELECT SUM(g.Credit - g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                       "WHERE a.AccountType IN ('Revenue', 'Expense') AND g.FiscalYear = ?", yy) for yy in d.years]
    claim(all(abs(x) < 0.005 for x in ni_closes), "with the closes left in, each year's revenue and expenses net to zero")
    # an AccountID typed where an account number belongs
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountID = 1045") == 0, "no account has the AccountID 1045: the number 1045 is an AccountNumber")
    # the dates
    through, last = n4.data_through(d), d.one("SELECT MAX(PostingDate) FROM GLEntry")
    pay_end = d.one("SELECT MAX(PostingDate) FROM GLEntry WHERE SourceDocumentType IN ('PayrollSummary', 'PayrollPayment')")
    claim(pay_end < through, "including payroll in Data Through would move it before the year-end")
    claim(pay_end < f"{y}-12-31", "the last payroll posting is before the last day of the year, so the fourth quarter would go blank")
    thru_sources = n4.DATA_SOURCES
    # the quoted project
    gl, req, rec, item, iss = table_m("GLEntry"), table_m("Requisitions"), table_m("Receipts"), table_m("Item"), table_m("Issues")
    m_close = step(claim, gl, "Added Custom")
    m_channel = step(claim, req, "Added Custom", "Added Custom2", split=True)
    m_receipts = step(claim, rec, "Merged Queries1", "Expanded OrderLines", "Merged Queries2", "Expanded Requisitions")
    m_policy = step(claim, expression_m("InventoryPolicy"), "Grouped Rows")
    m_item = step(claim, item, "Merged Queries", "Expanded InventoryPolicy")
    m_pair = step(claim, iss, "Added Custom")
    claim("Text.StartsWith" in m_channel and "WO-COMPONENT-SHORTFALL" in m_channel, "the channel is read from the start of the justification")
    claim(not any("Table.SelectRows" in l for l in gl), "GLEntry keeps all its rows: the project's query has no filter step")
    d_through = dax(claim, "Data Through")
    d_received = dax(claim, "Receipts to 1045")
    d_close = dax(claim, "GL Amount", "Net Income")
    d_balance = dax(claim, "Balance", "Total Assets")
    check = (f"EVALUATE\nROW (\n    \"Data Through\", FORMAT ( [Data Through], \"yyyy-mm-dd\" ),\n"
             f"    \"Net Income {y}\", ROUND ( CALCULATE ( [Net Income], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Total Assets {y}\", ROUND ( CALCULATE ( [Total Assets], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Received less 1045 {y}\", ROUND ( CALCULATE ( [Materials Received] - [Receipts to 1045], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Receipts without a Requisition\", [Receipts without a Requisition]\n)")
    for label in (f"{y} Net Income", f"{y} total assets at the year-end", f"{y} materials received", "Data Through", "receipt lines without a requisition"):
        check_expr(claim, label)
    has_visual(claim, "validation", "controlTotals", "linkCards", "profileAnswer")
    has_visual(claim, "about", "aboutText", "dataThrough")
    t = n4.opening_entry(d)
    return dict(
        y=y, f=d.F, p=d.P, n=d.N, top_n=1000, label_top="Column profiling based on top 1000 rows", top=top, allr=allr, top_no_app=top_no_app, all_no_app=all_no_app, top_approved=top_approved,
        all_approved=all_approved, n_items=items, ungrouped=ungrouped, hdr_lines=hdr[0], hdr_value=hdr[1], hdr_mat_lines=hdr_mat[0],
        hdr_mat_value=hdr_mat[1], receipt_lines=lines, by_year=by_year, through=through, last=last, pay_end=pay_end,
        n_sources=len(thru_sources), sources=thru_sources, entry=t,
        m_close=m_close, m_channel=m_channel, m_receipts=m_receipts, m_policy=m_policy, m_item=m_item, m_pair=m_pair,
        d_through=d_through, d_received=d_received, d_close=d_close, d_balance=d_balance, dax_check=check,
        t_control=title(claim, "validation", "controlTotals"), t_links=title(claim, "validation", "linkCards"),
        t_data=title(claim, "about", "dataThrough"), test1=test_block(claim, 1), test2=test_block(claim, 2),
        n_checks=check_sections()["Requirement 1"])


# --- requirement 2: the balance sheet, the bridge, the restated sections -----------------------------------------------------

def balance_bridge(d, year: int) -> dict:
    """The bridge from differences of Balance (year-end less the year before), the way a student might build it."""
    out = {}
    for stp in n4.STEPS:
        nums = n4.numbers(d, lambda n, t, s, st=stp: n4.step_of(n, t, s) == st)
        out[stp] = n4.xr(-(n4.balance(d, nums, f"{year}-12-31") - n4.balance(d, nums, f"{year - 1}-12-31")))
    return out


@context("case4.g2")
def g2(d, claim):
    need(d, claim)
    y, P, F, N = d.C, d.P, d.F, d.N
    cur, pri, first = n4.bridge(d, y), n4.bridge(d, P), n4.bridge(d, F)
    rc, rp = n4.restated(d, y), n4.restated(d, P)
    diff = balance_bridge(d, y)
    claim(abs(sum(diff.values()) - cur["cash"]) < 0.01, "a bridge built from the differences of balances still adds up to the change in cash")
    claim(abs(diff["net_income"] - (cur["net_income"] - pri["net_income"])) < 0.01,
          "built from balance differences, the net income step is the year's net income less the year before's")
    claim(abs(diff["debt_equity"] - (cur["debt_equity"] + pri["net_income"])) < 0.01,
          "the year before's net income, closed into retained earnings, moves into the debt and equity step")
    claim(all(abs(diff[k] - cur[k]) < 0.01 for k in n4.STEPS if k not in ("net_income", "debt_equity")),
          "the other steps agree whichever way they are built")
    # the debt schedule filtered through the Date table
    after = d.one("SELECT SUM(PrincipalAmount) FROM DebtScheduleLine WHERE PaymentDate > ?", f"{y}-12-31")
    inside = d.one("SELECT SUM(PrincipalAmount) FROM DebtScheduleLine WHERE PaymentDate > ? AND PaymentDate <= ?", f"{y}-12-31", f"{N}-12-31")
    beyond_n, beyond_lines = d.q("SELECT SUM(PrincipalAmount), COUNT(*) FROM DebtScheduleLine WHERE PaymentDate > ?", f"{N}-12-31")[0]
    claim(beyond_lines > 0 and abs(after - inside - beyond_n) < 0.01, "the debt schedule runs past the last day of the Date table")
    claim(abs(inside - n4.xr(d.one("SELECT SUM(PrincipalAmount) FROM DebtScheduleLine WHERE substr(PaymentDate, 1, 4) = ?", str(N)))) < 0.01,
          "what the Date table keeps of the schedule is exactly the principal due in the next year")
    # the first year
    claim(first["cash"] > 0 and first["financing"] > 10_000_000, "the first year's bridge, with the opening entry, starts from zero cash and shows a large financing step")
    # the sections as recorded and restated
    claim(cur["financing"] > 0 > rc["financing"], "the financing section changes sign when the note that financed equipment is taken out")
    claim(cur["investing"] < 0 and abs(rc["investing"]) < 0.01, "the investing section as recorded is negative and the restated one is zero")
    claim(abs(rc["operating"] - rc["notes_financed"] * 0 - (cur["operating"] + rc["written"] + rc["loss"])) < 0.01,
          "restated operating = recorded operating + the write-off + the loss")
    # a schema check on the project
    acct = table_m("Account")
    m_step = step(claim, acct, "Added Custom", split=True)
    m_activity = step(claim, acct, "Added Custom1")
    claim("Step" in m_step and m_step.count("else if") >= 8, "the project's Step column is an if-then-else chain on account numbers and subtypes")
    dx = dax(claim, "Statement Balance")
    dax(claim, "Current Ratio", "Quick Ratio", "Disposal Write-off", "Disposal Loss", "Disposal Cost", "Disposal Proceeds", "Financed by Notes",
        "Cash Net of Sales Tax", "Sales Tax Payable", "Notes Payable", "Scheduled Principal Outstanding")
    d_cash = dax(claim, "Cash Effect", "Change in Cash")
    d_restated = dax(claim, "Restated Cash Flow")
    d_due = dax(claim, "Principal Due within a Year")
    d_opening = dax(claim, "Cash Effect without Opening")
    kf = check_expr(claim, f"without KEEPFILTERS, the Inventories step of {y} shows the change in cash")
    bd = check_expr(claim, f"a bridge from Balance differences: its {y} net income step is {y}'s less {P}'s")
    check = (f"EVALUATE\nROW (\n    \"Change in cash {y}\", ROUND ( CALCULATE ( [Change in Cash], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Sum of the steps\", ROUND ( CALCULATE ( [Cash Effect], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Restated financing\", ROUND ( CALCULATE ( [Restated Cash Flow], 'Date'[Year] = {y}, Account[Activity] = \"Financing\" ), 2 )\n)")
    for label in (f"{y} step Inventories", f"{y} financing restated", f"{y} cash net of sales tax payable", f"principal due in {N}",
                  f"{F} change in cash without the opening entry"):
        check_expr(claim, label)
    has_visual(claim, "balanceSheet", "bsMatrix", "ratios", "bsAnswer")
    has_visual(claim, "cashBridge", "waterfall", "bridgeMatrix", "restated", "cashCards", "cashByYear", "bridgeAnswer", "bridgeYear")
    has_visual(claim, "bridgeDetail", "postings", "backButton")
    return dict(
        y=y, f=F, p=P, n=N, diff_ni=diff["net_income"], diff_fin=diff["debt_equity"], kf_value=cur["cash"], after=after, inside=inside,
        beyond=beyond_n, beyond_lines=beyond_lines, fin_rec=cur["financing"], fin_res=rc["financing"], inv_rec=cur["investing"],
        inv_res=rc["investing"], op_rec=cur["operating"], op_res=rc["operating"], dep_entries=rc["depreciation"], dep_step=cur["depreciation"],
        m_step=m_step, m_activity=m_activity, d_balance=dx, d_cash=d_cash, d_restated=d_restated, d_due=d_due,
        d_opening=d_opening, dax_check=check, kf_check=kf, bd_check=bd,
        t_matrix=title(claim, "balanceSheet", "bsMatrix"), t_ratios=title(claim, "balanceSheet", "ratios"),
        t_waterfall=title(claim, "cashBridge", "waterfall"), t_bridge=title(claim, "cashBridge", "bridgeMatrix"),
        t_restated=title(claim, "cashBridge", "restated"), t_cards=title(claim, "cashBridge", "cashCards"),
        t_cash=title(claim, "cashBridge", "cashByYear"), t_postings=title(claim, "bridgeDetail", "postings"),
        test3=test_block(claim, 3), n_checks=check_sections()["Requirement 2"])


# --- requirement 3: how fast working capital turns -------------------------------------------------------------------------

@context("case4.g3")
def g3(d, claim):
    need(d, claim)
    y, F, N = d.C, d.F, d.N
    end = f"{y}-12-31"
    first = n4.window_start(end)
    qs = n4.quarters(d)
    q0, q1 = qs[0], qs[-1]
    ar = n4.balance(d, ["1020"], end)
    bill = n4.flow(d, ["1020"], first, end, "SalesInvoice")[0]
    rev_accts = n4.numbers(d, lambda n, t, s: t == "Revenue")
    rdr, rcr = n4.flow(d, rev_accts, first, end)
    dso_rev = ar / (rcr - rdr) * 365
    qbill = n4.flow(d, ["1020"], f"{y}-10-01", end, "SalesInvoice")[0]
    dso_quarter = ar / qbill * 365
    claim(abs(dso_rev - q1["dso"]) > 1 and dso_quarter > 3 * q1["dso"], "billing and revenue differ enough to move the days, and a quarter's flow overstates them about fourfold")
    cogs = n4.cogs_accounts(d)
    # a cost of goods sold that keeps the closes: the twelve months' debits less credits on the COGS accounts
    def with_closes(e):
        f = n4.window_start(e)
        return d.one("SELECT SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                     "WHERE a.AccountSubType = 'COGS' AND g.PostingDate BETWEEN ? AND ?", f, e)
    q3 = f"{y}-09-30"
    c3 = with_closes(q3)
    inv3 = n4.balance(d, ["1040", "1045", "1046"], q3)
    dio_q3 = inv3 / c3 * 365
    claim(abs(with_closes(end)) < 0.005, "a window that ends on the year-end and keeps its close has no cost of goods sold at all")
    claim(dio_q3 > 5000, "a window that keeps an earlier close reads thousands of days")
    # materials against COGS, payables against COGS
    cdr, ccr = n4.flow(d, cogs, first, end)
    mat = n4.balance(d, ["1045"], end)
    mat_cogs = mat / (cdr - ccr) * 365
    ap = -n4.balance(d, ["2010"], end)
    dpo_cogs = ap / (cdr - ccr) * 365
    claim(mat_cogs < q1["mat"] / 1.5, "materials measured against cost of goods sold look like a normal stock")
    claim(dpo_cogs > q1["dpo"], "payables measured against cost of goods sold read longer than against supplier invoices")
    # no twelve-month guard
    def unguarded(e):
        start = max(n4.window_start(e), f"{F}-01-01")
        b = n4.flow(d, ["1020"], start, e, "SalesInvoice")[0]
        return n4.balance(d, ["1020"], e) / b * 365
    early, late = unguarded(f"{F}-03-31"), unguarded(f"{N}-03-31")
    claim(early > 4 * q0["dso"] and late > q1["dso"], "without the guard, the first quarter reads several times the real days and a quarter after Data Through reads a value")
    dx = lambda k: round(q1[k] - q0[k], 1)                                                        # noqa: E731
    claim(dx("dio") >= dx("ccc_x") > 0 and abs(dx("dso_x")) < 10 and abs(dx("dpo_x")) < 5, "the inventory days account for all of the cycle's growth")
    # the quoted project
    d_flows = dax(claim, "Full Twelve Months", "Billing TTM")
    dax(claim, "COGS TTM", "Issues TTM", "Shipments TTM", "Supplier Invoices TTM")
    d_days = dax(claim, "DSO", "DIO", "DPO", "Cash Conversion Cycle", "Materials Days")
    dax(claim, "Finished Goods Days")
    d_open = dax(claim, "DSO without Opening", "DSO on Average Balance")
    dax(claim, "Opening Balance", "Average Balance")
    dax(claim, "Materials Target Days", "Materials Days to Target", "Component Balance")
    matrix_json = (REPORT / "definition" / "pages" / "workingCapital" / "visuals" / "wcMatrix" / "visual.json").read_text(encoding="utf-8")
    cuts = sorted({float(x) for x in re.findall(r'"Value": "([\d.]+)D"', matrix_json)})
    claim(len(cuts) == 2 and "GreyArrowUp" in matrix_json and "GreyArrowDown" in matrix_json and "CircleMedium" in matrix_json,
          "the matrix's icons are rules with two cut-offs: an up arrow, a circle and a down arrow")
    param = table_source(claim, "WC Measure")
    claim(param.count("NAMEOF") == 6, "the field parameter lists six measures")
    check = (f"EVALUATE\nROW (\n    \"DSO {q1['label']}\", ROUND ( CALCULATE ( [DSO], 'Date'[YearQuarter] = \"{q1['label']}\" ), 1 ),\n"
             f"    \"Cycle {q1['label']}\", ROUND ( CALCULATE ( [Cash Conversion Cycle], 'Date'[YearQuarter] = \"{q1['label']}\" ), 1 ),\n"
             f"    \"DSO {F}-Q1\", CALCULATE ( [DSO], 'Date'[YearQuarter] = \"{F}-Q1\" ),\n"
             f"    \"DSO {N}-Q1\", CALCULATE ( [DSO], 'Date'[YearQuarter] = \"{N}-Q1\" ),\n"
             f"    \"Materials target\", CALCULATE ( [Materials Target Days], 'Date'[Year] = {y} )\n)")
    for label in (f"{q1['label']} DSO (1 decimal)", f"{q1['label']} Cash Conversion Cycle (1 decimal)", f"{F}-Q1 DSO (blank)", f"{N}-Q1 DSO (blank)",
                  f"{y} DIO on the average balance (1 decimal)"):
        check_expr(claim, label)
    has_visual(claim, "workingCapital", "wcMeasure", "wcLine", "wcMatrix", "wcAverage", "wcAnswer")
    has_visual(claim, "wcTooltip", "tipTable")
    return dict(
        y=y, f=F, n=N, label=q1["label"], first_label=q0["label"], bill=bill, rev_flow=rcr - rdr, dso_rev=dso_rev, dso_quarter=dso_quarter,
        qbill=qbill, dio_q3=dio_q3, q3_label=f"{y}-Q3", mat_cogs=mat_cogs, dpo_cogs=dpo_cogs, early=early, late=late,
        early_label=f"{F}-Q1", late_label=f"{N}-Q1",
        d_dso=dx("dso"), d_dio=dx("dio"), d_dpo=dx("dpo"), d_ccc=dx("ccc"), d_dso_x=dx("dso_x"), d_dpo_x=dx("dpo_x"), d_ccc_x=dx("ccc_x"),
        d_mat=dx("mat"), d_fg=dx("fg"),
        d_flows=d_flows, d_days=d_days, d_open=d_open, param=param, dax_check=check, icon_up=cuts[1], icon_down=cuts[0],
        t_line=title(claim, "workingCapital", "wcLine"), t_matrix=title(claim, "workingCapital", "wcMatrix"),
        t_average=title(claim, "workingCapital", "wcAverage"), t_slicer=title(claim, "workingCapital", "wcMeasure"),
        n_checks=check_sections()["Requirement 3"], test5=test_block(claim, 5))


# --- requirement 4: the materials build and a target for the next year ----------------------------------------------------

@context("case4.g4")
def g4(d, claim):
    need(d, claim)
    y, N = d.C, d.N
    rows = d.q("SELECT Justification, Quantity, EstimatedUnitCost FROM PurchaseRequisition WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%'")
    pairs: dict[str, list] = {}
    wos: dict[str, int] = {}
    for j, q, c in rows:
        pairs.setdefault(j, []).append((q, c))
        wo = re.search(r"WO=(\d+)", j).group(1)
        wos[wo] = wos.get(wo, 0) + 1
    issued = {k for (k,) in d.q("SELECT DISTINCT 'WO-COMPONENT-SHORTFALL | WO=' || m.WorkOrderID || ' | ITEM=' || l.ItemID FROM MaterialIssueLine l "
                                "JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID")}
    matched = [j for j in pairs if j in issued]
    units_all = sum(q for v in pairs.values() for q, _ in v)
    units_inner = sum(q for j in matched for q, _ in pairs[j])
    claim(len(matched) < len(pairs) and units_inner < units_all, "an inner join to the issues drops the pairs that nothing was issued for")
    item_unit = dict(d.q("SELECT ItemID, UnitOfMeasure FROM Item"))
    main_unit = d.one("SELECT i.UnitOfMeasure FROM PurchaseRequisition r JOIN Item i ON i.ItemID = r.ItemID WHERE r.Justification "
                      "LIKE 'WO-COMPONENT-SHORTFALL%' GROUP BY 1 ORDER BY SUM(r.Quantity) DESC LIMIT 1")
    unit_of = lambda j: item_unit[int(re.search(r"ITEM=(\d+)", j).group(1))]          # noqa: E731
    main_inner = sum(q for j in matched if unit_of(j) == main_unit for q, _ in pairs[j])
    main_all = sum(q for j in pairs if unit_of(j) == main_unit for q, _ in pairs[j])
    claim(main_inner < main_all, "the inner join also lowers the quantity requisitioned in the main unit of measure")
    by_wo_groups, by_wo_repeated, by_wo_most = len(wos), sum(1 for v in wos.values() if v > 1), max(wos.values())
    claim(by_wo_groups < len(pairs) and by_wo_most > max(len(v) for v in pairs.values()),
          "grouping by work order alone gives fewer groups and a larger maximum than grouping by work order and item")
    # the excess against all the inventories, and against a default of the series' first value
    ttm = n4.materials_issues(d, y)
    mat = n4.balance(d, ["1045"], f"{y}-12-31")
    inv = n4.balance(d, ["1040", "1045", "1046"], f"{y}-12-31")
    allowed28 = ttm / 365 * n4.TARGETS[0]
    all_inv_excess = inv - allowed28
    claim(all_inv_excess > 1.5 * (mat - allowed28), "measured against all the inventories, the excess is far larger than against the materials")
    first_day = 7
    claim(d.one("SELECT MIN(TargetDaysSupply) FROM InventoryPolicy") >= first_day, "the series starts below every policy target")
    low = ttm / 365 * first_day
    series = table_source(claim, "Target Days")
    claim("GENERATESERIES" in series, "the what-if table is a GENERATESERIES")
    rng = [int(x) for x in re.findall(r"\d+", series)]
    claim(rng[:3] == [7, 120, 1], "the what-if parameter runs from 7 to 120 days in steps of one")
    n_series = rng[1] - rng[0] + 1
    sp = d.q("SELECT i.ItemGroup, MIN(p.TargetDaysSupply), MAX(p.TargetDaysSupply) FROM InventoryPolicy p JOIN Item i ON i.ItemID = p.ItemID "
             "WHERE i.ItemGroup IN ('Raw Materials', 'Packaging') GROUP BY 1")
    targets = {r[0]: (r[1], r[2]) for r in sp}
    claim(targets["Raw Materials"][0] == targets["Raw Materials"][1] and targets["Packaging"][0] == targets["Packaging"][1],
          "each of raw materials and packaging has one target")
    # the quoted project
    pairs_m = step(claim, table_m("ShortfallPairs"), "Filtered Rows", "Grouped Rows", "Merged Queries", "Expanded IssuedByPair")
    issued_m = step(claim, expression_m("IssuedByPair"), "Grouped Rows")
    key_m = step(claim, table_m("Issues"), "Added Custom")
    d_build = dax(claim, "Materials Build", "Supply Plan Receipts", "Shortfall Receipts")
    dax(claim, "Shortfall Requisitions", "Self-requested")
    d_pairs = dax(claim, "Pairs", "Repeated Pairs", "Pairs with Issues", "Requisitioned Units", "Issued Units")
    d_target = dax(claim, "Target Days Value", "Allowed Materials", "Excess Materials", "Months of Issues in Excess")
    d_out = dax(claim, "Open Requisitions", "Finished Goods at Target", "Open Order Value")
    check = (f"EVALUATE\nROW (\n    \"Pairs\", [Pairs],\n    \"Repeated pairs\", [Repeated Pairs],\n    \"Pairs with issues\", [Pairs with Issues],\n"
             f"    \"Excess at 28 days\", ROUND ( CALCULATE ( [Excess Materials], 'Date'[Year] = {y}, 'Target Days'[Target Days] = 28 ), 2 ),\n"
             f"    \"Open requisitions\", [Open Requisitions]\n)")
    for label in (f"{y} build", "pairs", "repeated pairs", "pairs matched to issues", "28 days: excess", "approved, unordered requisitions"):
        check_expr(claim, label)
    has_visual(claim, "materialsBuild", "receiptsIssues", "channelByYear", "buildMatrix", "approvals", "requesters", "buildAnswer")
    has_visual(claim, "materialsTarget", "pairCards", "topPairs", "targetSlider", "whatIfCards", "whatIfTable", "leftOut", "targetAnswer")
    return dict(
        y=y, n=N, pairs_all=len(pairs), pairs_matched=len(matched), units_all=units_all, units_inner=units_inner, main_inner=main_inner,
        wo_groups=by_wo_groups,
        wo_repeated=by_wo_repeated, wo_most=by_wo_most, inv=inv, mat=mat, all_inv_excess=all_inv_excess, allowed28=allowed28, low_days=first_day,
        low_excess=mat - low, series=series, n_series=n_series, raw_target=targets["Raw Materials"][0], pack_target=targets["Packaging"][0],
        pairs_m=pairs_m, issued_m=issued_m, key_m=key_m, d_build=d_build, d_pairs=d_pairs, d_target=d_target, d_out=d_out, dax_check=check,
        t_receipts=title(claim, "materialsBuild", "receiptsIssues"), t_build=title(claim, "materialsBuild", "buildMatrix"),
        t_approvals=title(claim, "materialsBuild", "approvals"), t_cards=title(claim, "materialsTarget", "pairCards"),
        t_pairs=title(claim, "materialsTarget", "topPairs"), t_slider=title(claim, "materialsTarget", "targetSlider"),
        t_tested=title(claim, "materialsTarget", "whatIfTable"), t_left=title(claim, "materialsTarget", "leftOut"),
        t_requesters=title(claim, "materialsBuild", "requesters"), n_checks=check_sections()["Requirement 4"])


# --- requirement 5: the roll-forward, the reconciliations, the findings ---------------------------------------------------

@context("case4.g5")
def g5(d, claim):
    need(d, claim)
    y, P = d.C, d.P
    asof = f"{y}-12-31"
    r5 = n4.r5(d, claim)
    rows = d.q("SELECT si.GrandTotal, (SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a WHERE a.SalesInvoiceID = si.SalesInvoiceID AND a.ApplicationDate <= ?1), "
               "(SELECT SUM(c.GrandTotal) FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID AND c.CreditMemoDate <= ?1) "
               "FROM SalesInvoice si WHERE si.InvoiceDate <= ?1", asof)
    wrong = [n4.xr(g - a - c) for g, a, c in rows if a is not None and c is not None]
    wrong_open = [b for b in wrong if b > 0]
    no_credit = sum(1 for _, a, c in rows if c is None)
    claim(len(wrong_open) < 20 and sum(wrong_open) < 0.01 * r5["open_ar"], "a null in either column makes the open balance null, and almost every open invoice has no credit memo")
    neither = sum(1 for g, a, c in rows if a is None and c is None and n4.xr(g) > 0)
    # the findings with the note invoices' sign wrong
    notes_total = r5["notes_total"]
    open_line = r5["opening_ap"]
    right_find = n4.xr(open_line - notes_total)
    wrong_find = n4.xr(open_line + notes_total)
    claim(abs(right_find - r5["ap_diff"]) < 0.01, "the payables findings, with the note invoices negative, equal the difference")
    # payables including 2020 (the Payables step of the bridge)
    gr_ni = r5["roll"]["2020"]["total"]
    claim(gr_ni < 0, "account 2020 holds a credit balance: goods received and not yet invoiced")
    step_diff = n4.xr(r5["ap_diff"] - gr_ni)
    # received date against invoice date
    crossing = r5["crossing"]
    claim(len(crossing) == 1 and crossing[0]["year"] == P, "one supplier invoice crosses a year-end, at the end of the prior year")
    at_cur = d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE InvoiceDate <= ? AND ReceivedDate > ?", asof, asof)
    claim(at_cur == 0, "at the end of the current year no supplier invoice is dated before it and received after it")
    # decode the Findings table the project types
    found = findings_table()
    claim(len(found) >= 7, "the project's Findings table holds the reconciling items and the other findings")
    disp = [r[3] for r in found]
    claim(set(disp) == {"Follow up", "Expected", "Misstatement"}, "the findings carry three dispositions: follow up, expected and misstatement")
    amounts = {r[0] + "|" + r[1][:20]: float(r[2]) for r in found}
    claim(any(abs(float(r[2]) + notes_total) < 0.01 for r in found), "the note invoices' finding is recorded as a negative amount")
    # the quoted project
    ar_m = step(claim, table_m("ARInvoices"), "Added Custom")
    ap_m = step(claim, table_m("APInvoices"), "Added Custom4")
    dax(claim, "Open Receivables", "Receivables Difference", "Open Payables", "Payables Difference")
    dax(claim, "Past Due Payables", "Past Due Share without Notes", "Billing Difference")
    d_find = dax(claim, "Payables Findings", "Unexplained Payables")
    dax(claim, "Receivables Findings", "Unexplained Receivables")
    claim(n4.data_through(d) < f"{d.N}-01-01", "Data Through is before the next year, so all four quarters of the next year follow it")
    check = (f"EVALUATE\nROW (\n    \"Receivables difference\", ROUND ( CALCULATE ( [Receivables Difference], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Unexplained receivables\", ROUND ( CALCULATE ( [Unexplained Receivables], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Payables difference\", ROUND ( CALCULATE ( [Payables Difference], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Unexplained payables\", ROUND ( CALCULATE ( [Unexplained Payables], 'Date'[Year] = {y} ), 2 ),\n"
             f"    \"Sales tax debits\", [Sales Tax Debits] - CALCULATE ( [Sales Tax Debits], GLEntry[SourceDocumentType] = \"CreditMemo\" )\n)")
    for label in ("receivables difference", "payables difference", "Test 4: the receivables difference equals its findings",
                  "Test 4: the payables difference equals its findings", "Test 5: quarters after Data Through with a value"):
        check_expr(claim, label)
    has_visual(claim, "reconciliations", "rollForward", "reconCards", "billing", "aging", "salesTax", "findings", "reconAnswer")
    acc = d.q("SELECT a.AccountNumber, a.AccountName FROM Account a WHERE a.AccountNumber IN (1020, 1040, 1045, 2010, 2020, 2050) ORDER BY 1")
    names = {str(n): nm for n, nm in acc}
    claim(len(names) == 6, "the roll-forward's six accounts exist")
    return dict(
        y=y, p=P, wrong_n=len(wrong_open), wrong_sum=sum(wrong_open), no_credit=no_credit, rows=len(rows), neither=neither, right_find=right_find,
        wrong_find=wrong_find, wrong_gap=n4.xr(wrong_find - r5["ap_diff"]), gr_ni=gr_ni, step_diff=step_diff, crossing=crossing[0],
        names=names, n_findings=len(found), findings=found, ar_m=ar_m, ap_m=ap_m, d_find=d_find, later_quarters=4,
        dax_check=check, test4=test_block(claim, 4), test5=test_block(claim, 5),
        t_roll=title(claim, "reconciliations", "rollForward"), t_cards=title(claim, "reconciliations", "reconCards"),
        t_billing=title(claim, "reconciliations", "billing"), t_aging=title(claim, "reconciliations", "aging"),
        t_tax=title(claim, "reconciliations", "salesTax"), t_findings=title(claim, "reconciliations", "findings"),
        n_checks=check_sections()["Requirement 5"], total_checks=sum(check_sections().values()))


# --- requirement 6: the memo -----------------------------------------------------------------------------------------------

@context("case4.g6")
def g6(d, claim):
    need(d, claim)
    text = CASE.read_text(encoding="utf-8")
    exhibits = [e.format(P=d.P, C=d.C, N=d.N) for e in EXHIBITS]
    for e in exhibits:
        claim(e in text, f"the case's Deliverable lists the exhibit: {e}")
    claim("no more than two pages" in text and "one-page appendix" in text, "the memo is at most two pages with a one-page appendix")
    words = 0
    for name in ("memoLeft", "memoRight"):
        v = json.loads((REPORT / "definition" / "pages" / "memo" / "visuals" / name / "visual.json").read_text(encoding="utf-8"))
        paragraphs = v["visual"]["objects"]["general"][0]["properties"]["paragraphs"]
        words += len(re.findall(r"\S+", " ".join(r["value"] for p in paragraphs for r in p["textRuns"])))
    claim(words > 300, "the model memo has substance")
    claim(sum(check_sections().values()) > 400, "the Checks tab holds several hundred rows")
    b = n4.bridge(d, d.C)
    inv_over = n4.xr(-b["inventories"] - b["net_income"])
    claim(inv_over > 0, "the inventories absorbed more cash than the year's net income")
    return dict(y=d.C, p=d.P, n=d.N, exhibits=exhibits, n_exhibits=len(exhibits), model_words=round(words, -1), inv_over=inv_over,
                titles=dict(bridge=title(claim, "cashBridge", "bridgeMatrix"), restated=title(claim, "cashBridge", "restated"),
                            wc=title(claim, "workingCapital", "wcMatrix"), channels=title(claim, "materialsBuild", "channelByYear"),
                            tested=title(claim, "materialsTarget", "whatIfTable"), findings=title(claim, "reconciliations", "findings")))
