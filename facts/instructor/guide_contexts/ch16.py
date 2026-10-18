"""Chapter 16's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 16 monitors exceptions and audits the reports themselves, so the guides do the same four jobs as Chapters 13 to 15:

- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll flags the wording instead of leaving it stale,
- they supply what each exercise's steps need beyond its registered note (ch16.ex1 to ch16.ex6): above all the symptom
  of each wrong version a guide names (nulls left in the receivables merge, a Group By that counts distinct rows, a
  KEEPFILTERS left out, a first digit read from the text of the amount, a self-merge without its filters, a share
  whose denominator moves with the employee), computed read-only on the dataset the way the model would show it,
- they quote the M, the DAX and the visual titles of the model answer from the solution project itself
  (outputs/companion/solutions/Chapter16-exercises-pbi), so a quoted step cannot drift from the file the instructor
  opens: a quote that is not found in the project is a failed claim,
- they supply the chapter note's counts (exercises, questions, slides, tutorial steps, checks) from the chapter's files.

Keys: ch16.chapter (the chapter note) and ch16.g1 to ch16.g6 (the exercises; each is used next to the registered note
ch16.ex1 to ch16.ex6 that supplies the values of the exercise's instructor note). The tutorials' values come from the
registered notes ch16.t1 to ch16.t3.

What the project proves and what only Desktop shows: the project encodes the model, the Power Query steps and the
visual structure, and its Checks tab (DAX query view) recomputes every value of the tutorials and exercises, so a
result is "proved" when a Checks row names it. A visual's rendering (the heat map's shading, the drill-through click,
the edited interactions as a reader meets them, the Data Through card with a slicer) is visible only in Desktop.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list
from guide_contexts.ch13 import _block, steps, version
from notes import ch16 as n16

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "16-audit-monitoring"
DECK = REPO / "slides" / "chapter-16" / "index.qmd"
PROJECT = REPO / "outputs" / "companion" / "solutions" / "Chapter16-exercises-pbi" / "Chapter 16 Exercises - Solutions"
MODEL = PROJECT / "Chapter 16 Exercises - Solutions.SemanticModel"
REPORT = PROJECT / "Chapter 16 Exercises - Solutions.Report"

SCHEMA = {
    "JournalEntry": ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount", "CreatedByEmployeeID",
                     "CreatedDate", "ApprovedByEmployeeID"],
    "Employee": ["EmployeeID", "EmployeeName", "JobTitle", "CostCenterID", "MaxApprovalAmount", "TerminationDate"],
    "PurchaseOrder": ["PONumber", "OrderDate", "OrderTotal", "CreatedByEmployeeID", "ApprovedByEmployeeID"],
    "PayrollRegister": ["PayrollRegisterID", "EmployeeID", "NetPay", "ApprovedByEmployeeID"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "CustomerID", "InvoiceDate", "DueDate", "SubTotal", "GrandTotal"],
    "SalesInvoiceLine": ["SalesInvoiceID", "ShipmentLineID"],
    "CashReceiptApplication": ["SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "CreditMemo": ["OriginalSalesInvoiceID", "CreditMemoDate", "GrandTotal"],
    "GLEntry": ["AccountID", "PostingDate", "Debit", "Credit", "VoucherNumber", "SourceDocumentType"],
    "Account": ["AccountID", "AccountNumber"],
    "Shipment": ["ShipmentID", "ShipmentDate", "DeliveryDate"],
    "ShipmentLine": ["ShipmentLineID", "ShipmentID", "ExtendedStandardCost"],
    "TimeClockEntry": ["EmployeeID", "WorkDate", "RegularHours", "OvertimeHours"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
    "DisbursementPayment": ["DisbursementID", "PaymentDate", "SupplierID", "PurchaseInvoiceID", "Amount"],
    "PurchaseInvoice": ["PurchaseInvoiceID", "GrandTotal"],
}
PAGES = ["journalEntries", "entryLines", "validation", "monitoring", "exceptionDetail", "review", "ex161", "ex162",
         "ex163", "ex164", "ex165", "ex166", "notes"]
BUCKETS = ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]


# --- helpers ---------------------------------------------------------------------------------------------------------

def need(d, claim, *tables: str) -> None:
    """Claims that each table and the columns the guides name are in the database."""
    schema(d, claim, {t: SCHEMA[t] for t in (tables or SCHEMA)})


def _model_text(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def table_m(name: str) -> list[str]:
    """The M of a loaded table's partition in the solution project, one stripped line per step."""
    return _block(_model_text(f"tables/{name}.tmdl"), "source =")


def expression_m(name: str) -> list[str]:
    """The M of a query that does not load (Enable load cleared), from expressions.tmdl."""
    quoted = f"'{name}'" if " " in name else name
    return _block(_model_text("expressions.tmdl"), f"expression {quoted} =")


def measure_table() -> dict[str, str]:
    """Every measure of the project as the formula bar reads it: `Name = expression`, the body dedented."""
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


def measure(claim, name: str) -> str:
    found = measure_table().get(name)
    claim(found is not None, f"the solution project has the measure {name}")
    return found or ""


def check_expr(claim, section: str, label: str) -> str:
    """The DAX expression of one row of the project's Checks tab (DAX query view), found by its section and label."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    m = re.search(r'"Section", "' + re.escape(section) + r'", "Check", "' + re.escape(label)
                  + r'", "Expected", .*?, "Actual", (.*?), "Agrees"', text)
    claim(m is not None, f"the Checks tab has the row {label!r} of {section}")
    return m.group(1) if m else ""


def _visual(page: str, name: str) -> dict:
    return json.loads((REPORT / "definition" / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))


def visual_title(claim, page: str, name: str) -> str:
    """The title of a visual of the solution project's report page, as Desktop shows it."""
    try:
        title = _visual(page, name)["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
        title = title.strip("'").replace("''", "'")
    except (OSError, KeyError, IndexError, ValueError):
        title = ""
    claim(title != "", f"the visual {name} of page {page} in the solution project has a title")
    return title


def column_line(claim, table: str, column: str) -> str:
    m = re.search(r"^\tcolumn " + re.escape(column) + r" = (.+)$", _model_text(f"tables/{table}.tmdl"), re.M)
    claim(m is not None, f"the table {table} of the solution project has the calculated column {column}")
    return f"{column} = {m.group(1)}" if m else ""


def source_of(claim, table: str) -> str:
    """The DAX of a calculated table's partition: the first and last lines flush, the lines between indented."""
    lines = _block(_model_text(f"tables/{table}.tmdl"), "source =")
    claim(bool(lines), f"the table {table} of the solution project is a calculated table")
    if len(lines) > 2 and lines[-1] in (")", "}"):
        return "\n".join([lines[0]] + ["    " + l for l in lines[1:-1]] + [lines[-1]])
    return "\n".join(lines)


def custom_expr(claim, lines: list[str], column: str) -> str:
    """The expression of a Custom Column step of the project, alone: what the Custom Column dialog takes."""
    found = [l for l in lines if "Table.AddColumn(" in l and f'"{column}", each ' in l]
    claim(len(found) == 1, f"the solution project's query has the custom column {column}")
    m = re.search(r'"' + re.escape(column) + r'", each (.*)\),?$', found[0]) if found else None
    claim(m is not None, f"the step of {column} is a Table.AddColumn with an expression")
    expr = m.group(1) if m else ""
    return re.sub(r" else ", "\nelse ", expr) if len(expr) > 60 else expr


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise \d+\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import package
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/16-audit-monitoring/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 16\b")
    letters, _ = package.answer_key(comment)
    key = {i: a for i, a in enumerate(letters, 1)}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


def step_counts() -> dict[int, int]:
    return {k: len(re.findall(r"^\*\*Step \d+\.", (CHAPTER / f"_tutorial-0{k}.qmd").read_text(encoding="utf-8"), re.M))
            for k in (1, 2, 3)}


def check_sections() -> dict[str, int]:
    """The rows of the Checks tab by section (Tutorial 16.1 ... Exercise 16.6)."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for sec in re.findall(r'ROW \( "Section", "([^"]*)"', text):
        counts[sec] = counts.get(sec, 0) + 1
    return counts


def first_digit(amount: float) -> int:
    """The first significant digit, from scientific notation (the model answer's FORMAT with 0.00000000E+00)."""
    return int(f"{amount:.8E}"[0])


def mad(digits: list[int], denominator: int | None = None) -> float:
    c = Counter(digits)
    n = denominator or len(digits)
    return sum(abs(c[k] / n - math.log10(1 + 1 / k)) for k in range(1, 10)) / 9


def clock_days(d) -> dict[str, list[tuple]]:
    """Every clock entry by work date: (employee, regular, overtime, total, cost center)."""
    out: dict[str, list[tuple]] = {}
    for emp, day, regular, overtime, center in d.q("SELECT tc.EmployeeID, tc.WorkDate, tc.RegularHours, tc.OvertimeHours, e.CostCenterID "
                                                   "FROM TimeClockEntry tc JOIN Employee e ON e.EmployeeID = tc.EmployeeID"):
        out.setdefault(day, []).append((emp, regular, overtime, regular + overtime, center))
    return out


# --- the chapter note --------------------------------------------------------------------------------------------------

@context("ch16.chapter")
def chapter(d, claim):
    need(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 14, "the chapter has fourteen multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    claim(version() != "", "Tutorial 13.1 names the Power BI Desktop version")
    claim(MODEL.is_dir() and REPORT.is_dir(), "the solution project of Chapter 16 is in outputs/companion/solutions")
    pages = json.loads((REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    claim(pages == PAGES, "the project's pages are the tutorials' six, Ex 16.1 to Ex 16.6 and Notes")
    tabs = json.loads((MODEL / ".pbi" / "daxQueries.json").read_text(encoding="utf-8"))["tabOrder"]
    claim(tabs == ["Tests", "Checks"], "the project's DAX query tabs are Tests and Checks")
    sections = check_sections()
    claim(set(sections) == {"Tutorial 16.1", "Tutorial 16.2", "Tutorial 16.3"} | {f"Exercise 16.{k}" for k in range(1, 7)},
          "the Checks tab has a section for each tutorial and each exercise")
    claim(len(n16.TESTS) == 11, "the register has eleven tests")
    # Tutorial 16.1 wrong versions
    total_je = d.one("SELECT COUNT(*) FROM JournalEntry")
    weekend = d.one("SELECT COUNT(*) FROM JournalEntry WHERE strftime('%w', CreatedDate) IN ('0', '6')")
    sunday_first = d.one("SELECT COUNT(*) FROM JournalEntry WHERE strftime('%w', CreatedDate) IN ('5', '6')")
    claim(weekend == sum(e["flags"]["Weekend"] for e in n16.entries(d)), "the weekend test counts the entries created on a Saturday or Sunday")
    claim(sunday_first > weekend, "a week that starts on Sunday, with the same threshold, flags more entries than the weekend holds (Friday)")
    claim(d.one("SELECT COUNT(*) FROM JournalEntry WHERE length(CreatedDate) > 10") == total_je,
          "every journal entry's CreatedDate carries a time of day")
    created_after = d.one("SELECT COUNT(*) FROM JournalEntry WHERE datetime(CreatedDate) > datetime(PostingDate)")
    claim(created_after == total_je, "every entry was created on or after its posting date, so a datetime compared with midnight is always later")
    # Tutorial 16.3 wrong versions
    ex_rows = n16.register(d)
    reviewed = sum(1 for e in ex_rows if e["disposition"])
    by_test = Counter(e["test"] for e in ex_rows)
    with_disposition = Counter(e["test"] for e in ex_rows if e["disposition"])
    test_only = len(ex_rows) - sum(by_test[t] for t in with_disposition) + sum(by_test[t] * with_disposition[t] for t in with_disposition)
    last = dict(JE=max(e["date"] for e in n16.entries(d)), PO=max(o["date"] for o in n16.orders(d)),
                PR=max(r["date"] for r in n16.registers(d)))
    claim(min(last.values()) < max(last.values()), "the populations end on different dates")
    jepo = [e for e in ex_rows if e["process"] in ("JE", "PO")]
    for yr in d.years:
        by_month = Counter(e["date"][5:7] for e in jepo if e["date"][:4] == str(yr))
        claim(by_month.most_common(1)[0][0] == "01", f"January holds the most journal entry and purchase order exceptions of {yr}")
    jan_jepo = sum(1 for e in jepo if e["date"][5:7] == "01")
    claim(jan_jepo > len(jepo) / 2, "more than half of the journal entry and purchase order exceptions fall in January")
    self_months = Counter(e["date"][:7] for e in ex_rows if e["test"] == "PR SelfApproved")
    claim(len(self_months) == 12 * len(d.years), "registers approved by their own employee appear in every month of the window")
    return dict(jan_jepo=jan_jepo, n_jepo=len(jepo), y=d.C, f=d.F, p=d.P, n=d.N, version=version(), slides=slide_count(), n_exercises=sum(ex.values()),
                per_perspective=ex.get("financial", 0), n_questions=n_q, n_longest=len(longest), longest_correct=and_list(longest),
                steps=step_counts(), n_checks=sum(sections.values()), n_pages=len(pages), n_tests=len(n16.TESTS),
                n_register=len(ex_rows), n_dispositions=reviewed, weekend=weekend, sunday_first=sunday_first, created_after=created_after,
                total_je=total_je, test_only_rows=test_only, mistyped_reviewed=reviewed - 1, mistyped_open=len(ex_rows) - reviewed + 1,
                twice_rows=len(ex_rows) + 1, twice_dispositions=reviewed + 1, through_max=max(last.values()), through_min=min(last.values()),
                last_je=last["JE"], last_po=last["PO"], last_pr=last["PR"],
                m_closing=" and ".join(d.closes_of(d.C)))


# --- Exercise 16.1 -----------------------------------------------------------------------------------------------------

@context("ch16.g1")
def g1(d, claim):
    need(d, claim, "SalesInvoice", "CashReceiptApplication", "CreditMemo", "GLEntry", "Account", "JournalEntry")
    end = n16.asof(d)
    rows = d.q("WITH Applied AS (SELECT SalesInvoiceID, SUM(AppliedAmount) AS Applied FROM CashReceiptApplication "
               "WHERE ApplicationDate <= ?1 GROUP BY SalesInvoiceID), "
               "Credited AS (SELECT OriginalSalesInvoiceID AS SalesInvoiceID, SUM(GrandTotal) AS Credited FROM CreditMemo "
               "WHERE CreditMemoDate <= ?1 GROUP BY OriginalSalesInvoiceID) "
               "SELECT ROUND(si.GrandTotal - COALESCE(a.Applied, 0) - COALESCE(c.Credited, 0), 2), "
               "julianday(?1) - julianday(si.DueDate), a.Applied IS NULL AND c.Credited IS NULL, "
               "a.Applied IS NOT NULL AND c.Credited IS NOT NULL, si.SalesInvoiceID, si.GrandTotal, COALESCE(a.Applied, 0), si.InvoiceNumber FROM SalesInvoice si "
               "LEFT JOIN Applied a ON a.SalesInvoiceID = si.SalesInvoiceID LEFT JOIN Credited c ON c.SalesInvoiceID = si.SalesInvoiceID "
               "WHERE si.InvoiceDate <= ?1", end)
    positive = [r for r in rows if r[0] > 0]
    negative = [r for r in rows if r[0] < 0]
    # with both merged totals left null, a null in either drops the row, so only the invoices with both survive
    kept = [r for r in positive if r[3]]
    claim(len(kept) < len(positive) / 2, "few open invoices have both an application and a credit memo, so leaving the nulls drops most of the aging")
    due_today = [r for r in positive if r[1] == 0]
    claim(bool(due_today), "some open invoices fall due on the as-of date itself")
    ledger = d.balance(["1020"], end)
    net = sum(r[0] for r in positive) + sum(r[0] for r in negative)
    claim(abs((ledger - net) - (ledger - sum(r[0] for r in positive))) > 1,
          "netting the credit balances into the open balance changes the difference the student reports")
    max_account = d.one("SELECT MAX(AccountID) FROM Account")
    account_id = d.account("1020")
    claim(max_account < 1020 and account_id != 1020, "no AccountID equals 1020, so a filter on AccountID = 1020 finds no postings")
    by_source = d.q("SELECT SourceDocumentType, SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ? "
                    "GROUP BY 1 ORDER BY 2 DESC", account_id, end)
    journal = [s for s in by_source if s[0] == "JournalEntry"]
    claim(len(journal) == 1 and abs(journal[0][1] - (ledger - sum(r[0] for r in positive))) < 0.005,
          "the journal entry source of account 1020 is exactly the unreconciled difference")
    claim(d.one("SELECT COUNT(*) FROM CashReceiptApplication WHERE ApplicationDate > ?", end) == 0
          and d.one("SELECT COUNT(*) FROM CreditMemo WHERE CreditMemoDate > ?", end) == 0,
          "no application and no credit memo is dated after the as-of date, so the two date filters change nothing on this data")
    credit_acct = "2060"
    credit_name = d.one("SELECT AccountName FROM Account WHERE AccountNumber = ?", credit_acct)
    claim(credit_name is not None, "account 2060 exists")
    # the invoices with a negative balance: what applied cash and the credit memos did to them, and where the credit posted
    ids = ",".join(str(r[4]) for r in negative)
    full = [r for r in negative if abs(r[6] - r[5]) < 0.005]
    part = [r for r in negative if r[6] < r[5] - 0.005]
    claim(len(full) + len(part) == len(negative) and full and part,
          "every invoice with a negative balance has applied cash equal to its total or less, and both kinds exist")
    post = {(inv, str(acct)): amount for inv, acct, amount in d.q(
        "SELECT cm.OriginalSalesInvoiceID, a.AccountNumber, SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        "JOIN CreditMemo cm ON cm.CreditMemoID = g.SourceDocumentID "
        f"WHERE g.SourceDocumentType = 'CreditMemo' AND cm.OriginalSalesInvoiceID IN ({ids}) AND a.AccountNumber IN ('1020', '2060') GROUP BY 1, 2")}
    to_2060 = sum(v for (inv, acct), v in post.items() if acct == "2060")
    to_1020 = sum(v for (inv, acct), v in post.items() if acct == "1020")
    claim(abs(to_2060 + sum(r[0] for r in negative)) < 0.005,
          "the credits posted to account 2060 equal the negative balances: the customer credit is the excess over the invoice")
    claim(all(abs(post.get((r[4], "1020"), 0) + post.get((r[4], "2060"), 0)
                  - d.one("SELECT SUM(GrandTotal) FROM CreditMemo WHERE OriginalSalesInvoiceID = ? AND CreditMemoDate <= ?", r[4], end)) < 0.005
              for r in negative),
          "each credit memo on these invoices posts wholly to accounts 1020 and 2060")
    claim(all((r[4], "1020") not in post for r in full) and all((r[4], "1020") in post for r in part),
          "the credit memos of the invoices paid in full credit only account 2060, and those of the partly paid ones also credit 1020")
    after_app = d.q("SELECT COUNT(DISTINCT ap.SalesInvoiceID), COUNT(DISTINCT ap.CashReceiptApplicationID) FROM CashReceiptApplication ap "
                    "WHERE ap.SalesInvoiceID IN (%s) AND ap.ApplicationDate > (SELECT MIN(cm.CreditMemoDate) FROM CreditMemo cm "
                    "WHERE cm.OriginalSalesInvoiceID = ap.SalesInvoiceID)" % ids)[0]
    receipt_after = d.one("SELECT COUNT(*) FROM (SELECT ap.SalesInvoiceID, MIN(cr.ReceiptDate) AS first_receipt FROM CashReceiptApplication ap "
                          "JOIN CashReceipt cr ON cr.CashReceiptID = ap.CashReceiptID "
                          "WHERE ap.SalesInvoiceID IN (%s) GROUP BY ap.SalesInvoiceID) r "
                          "WHERE r.first_receipt > (SELECT MIN(cm.CreditMemoDate) FROM CreditMemo cm WHERE cm.OriginalSalesInvoiceID = r.SalesInvoiceID)" % ids)
    claim(0 < after_app[0] < len(negative) and 0 < receipt_after < len(negative),
          "some, not all, of the invoices with a negative balance have an application, or even their first receipt, dated after the credit memo, so "
          "the order of payment and credit is not the same for all")
    # a worked example: the first partly paid invoice (lowest ID) whose credit memo precedes its first receipt
    example = None
    for r in sorted(part, key=lambda r: r[4]):
        cm_date, cm_no, cm_total = d.q("SELECT MIN(CreditMemoDate), MIN(CreditMemoNumber), SUM(GrandTotal) FROM CreditMemo "
                                       "WHERE OriginalSalesInvoiceID = ?", r[4])[0]
        rc = d.q("SELECT MIN(cr.ReceiptDate), MIN(ap.ApplicationDate) FROM CashReceiptApplication ap JOIN CashReceipt cr ON cr.CashReceiptID = ap.CashReceiptID "
                 "WHERE ap.SalesInvoiceID = ?", r[4])[0]
        if rc[0] and cm_date <= rc[0] and cm_date <= rc[1]:
            example = dict(number=r[7], total=r[5], applied=r[6], memo=cm_no, memo_total=cm_total, residual=-r[0], to_1020=post[(r[4], "1020")],
                           to_2060=post[(r[4], "2060")], posted=cm_date, receipt=rc[0], applied_on=rc[1])
            break
    claim(example is not None, "a partly paid invoice has its credit memo dated before its first receipt and application")
    order = sorted(BUCKETS)
    claim(order != BUCKETS, "sorted as text the buckets are out of order")
    ar = table_m("ARInvoices")
    return dict(credit_acct=credit_acct, credit_name=credit_name, end=end, kept_n=len(kept), kept_total=sum(r[0] for r in kept), due_today_n=len(due_today),
                due_today_total=sum(r[0] for r in due_today), net_difference=ledger - net, account_id=account_id,
                max_account=max_account, gl_rows=d.one("SELECT COUNT(*) FROM GLEntry"), by_source=[dict(kind=k, amount=v) for k, v in by_source], text_order=order,
                m_apps=steps(claim, expression_m("ARApplications"), "Filtered Rows", "Grouped Rows"),
                m_ar=steps(claim, ar, "Replaced Value", "Added Custom", "Filtered Rows"),
                m_bucket=steps(claim, ar, "Added Custom1", "Added Custom2"),
                m_ledger=steps(claim, table_m("ARLedger"), "Filtered Rows"),
                m_neg=steps(claim, table_m("ARCreditBalances"), "Filtered Rows"),
                n_full_applied=len(full), n_part_applied=len(part), to_2060=to_2060, to_1020=to_1020, after_app_n=after_app[0],
                after_app_rows=after_app[1], receipt_after_n=receipt_after, example=example,
                e_days=custom_expr(claim, ar, "DaysPastDue"), e_bucket=custom_expr(claim, ar, "Bucket"),
                e_order=custom_expr(claim, ar, "BucketOrder"), e_open=custom_expr(claim, ar, "OpenBalance"),
                m_open=measure(claim, "Open Balance"), m_open_n=measure(claim, "Open Invoices"), m_ledger_m=measure(claim, "Ledger Receivables"),
                m_credit=measure(claim, "Credit Balances"), m_credit_n=measure(claim, "Credit Balance Invoices"),
                m_diff=measure(claim, "Unreconciled Difference"),
                t_aging=visual_title(claim, "ex161", "aging"), t_source=visual_title(claim, "ex161", "ledgerBySource"),
                dax_open=check_expr(claim, "Exercise 16.1", "open balance"),
                dax_diff=check_expr(claim, "Exercise 16.1", "the difference is JE-2024-000001's receivables line"),
                dax_bucket=check_expr(claim, "Exercise 16.1", "bucket Over 90 days"))


# --- Exercise 16.2 -----------------------------------------------------------------------------------------------------

@context("ch16.g2")
def g2(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "ShipmentLine", "Shipment", "GLEntry")
    inv = d.q("SELECT si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate, si.SubTotal, s.DeliveryDate FROM SalesInvoice si "
              "JOIN SalesInvoiceLine l ON l.SalesInvoiceID = si.SalesInvoiceID JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID "
              "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID")
    lines = [r for r in inv if r[4][:4] < r[2][:4]]
    invoices = {r[0]: r for r in lines}
    claim(len(lines) > len(invoices), "an invoice for prior-year deliveries has more than one line, so a filter on lines repeats it")
    by_invoice: dict[int, list[str]] = {}
    for r in inv:
        by_invoice.setdefault(r[0], []).append(r[4][:4])
    mixed = [i for i, ys in by_invoice.items() if len(set(ys)) > 1]
    claim(not mixed, "no invoice has lines delivered in two different years, so testing the earliest line gives the same invoices as the latest")
    note = n16.ex2(d, lambda c, t: None)
    odd = note["odd"]
    delivery = d.one("SELECT MAX(s.DeliveryDate) FROM SalesInvoice si JOIN SalesInvoiceLine l ON l.SalesInvoiceID = si.SalesInvoiceID "
                     "JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                     "WHERE si.InvoiceNumber = ?", odd["number"])
    claim(delivery[:4] == odd["shipped"][:4], "the extra invoice is delivered in the year it shipped")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE substr(ShipmentDate, 1, 4) <> substr(DeliveryDate, 1, 4)") == 0,
          "every shipment is delivered in the year it ships")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID WHERE l.ShipmentLineID IS NULL AND i.ItemGroup <> 'Services'") == 0
          and d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ShipmentLineID IS NULL") > 0,
          "the invoice lines with no shipment line are all services")
    end = n16.asof(d)
    paid = d.one("SELECT COUNT(*) FROM SalesInvoice si WHERE si.SalesInvoiceID IN (%s) AND ROUND(si.GrandTotal - COALESCE((SELECT SUM(AppliedAmount) "
                 "FROM CashReceiptApplication a WHERE a.SalesInvoiceID = si.SalesInvoiceID AND a.ApplicationDate <= ?1), 0) - COALESCE((SELECT SUM(GrandTotal) "
                 "FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID AND c.CreditMemoDate <= ?1), 0), 2) <= 0" % ",".join(map(str, invoices)), end)
    claim(paid > 0, "some of the invoices for prior-year deliveries are already paid, so an open-invoices query would not hold them")
    register_rows = len(n16.register(d))
    return dict(line_rows=len(lines), line_subtotal=sum(r[3] for r in lines), blank_test_rows=note["n_prior"] + note["unbilled"],
                posted_rule=note["n_prior"] + 1, delivered=delivery, not_open=paid, old_total=register_rows,
                rows_162=register_rows + note["n_prior"] + note["unbilled"], tests_rows=len(n16.TESTS) + 2,
                m_ships=steps(claim, expression_m("CutoffShipmentLines"), "Merged Queries", "Expanded CutoffShipments"),
                m_inv=steps(claim, table_m("CutoffInvoiceLines"), "Merged Queries", "Expanded CutoffInvoices", "Merged Queries1",
                            "Expanded CutoffShipmentLines"),
                m_si=steps(claim, expression_m("SI DeliveredPriorYear"), "Grouped Rows", "Filtered Rows"),
                m_sl=steps(claim, expression_m("SL NotInvoiced"), "Merged Queries"),
                m_append=steps(claim, table_m("Exceptions 16.2"), "Source"),
                m_count=measure(claim, "Exceptions 16.2"),
                t_month=visual_title(claim, "ex162", "cutoffByMonth"), t_docs=visual_title(claim, "ex162", "cutoffDocs"),
                dax_si=check_expr(claim, "Exercise 16.2", "SI DeliveredPriorYear exceptions"),
                dax_sl=check_expr(claim, "Exercise 16.2", "SL NotInvoiced exceptions"),
                dax_posted=check_expr(claim, "Exercise 16.2", "SI-2026-013742 posted (ARLedger)"))


# --- Exercise 16.3 -----------------------------------------------------------------------------------------------------

@context("ch16.g3")
def g3(d, claim):
    need(d, claim, "TimeClockEntry", "Employee", "CostCenter")
    center = d.one("SELECT CostCenterID FROM CostCenter WHERE CostCenterName = 'Manufacturing'")
    model_m = table_m("ClockEntries")
    claim(any(l.startswith("#\"Filtered Rows\"") and f"[CostCenterID] = {center}" in l for l in model_m),
          "the solution project filters ClockEntries to the Manufacturing cost center's ID")
    days = clock_days(d)
    plant = {day: [r for r in rs if r[4] == center] for day, rs in days.items()}
    plant = {day: rs for day, rs in plant.items() if rs}

    def found(table, employees, hours):
        return [day for day, rs in table.items() if employees(rs) and hours(rs)]

    right = found(plant, lambda rs: len({r[0] for r in rs}) > 1, lambda rs: len({r[3] for r in rs}) == 1)
    distinct_rows = found(plant, lambda rs: len(set(rs)) > 1, lambda rs: len(set(rs)) == 1)
    all_centers = found(days, lambda rs: len({r[0] for r in rs}) > 1, lambda rs: len({r[3] for r in rs}) == 1)
    row_count = found(plant, lambda rs: len(rs) > 1, lambda rs: len({r[3] for r in rs}) == 1)
    one_entry = found(plant, lambda rs: len({r[0] for r in rs}) >= 1, lambda rs: len({r[3] for r in rs}) == 1)
    claim(len(right) > 0, "the plant has surge days")
    claim(len(distinct_rows) == 0, "counting distinct rows for both columns finds no surge day, because the rows of a day differ by employee")
    claim(len(all_centers) == 0, "leaving the cost center filter out finds no surge day, because other cost centers clock other hours")
    claim(sorted(row_count) == sorted(right), "counting rows in place of distinct employees finds the same surge days, because no surge day has an employee twice")
    claim(len(one_entry) == len(right), "no plant day has a single clock entry, so the guard on the number of employees changes nothing today")
    on_surge = sum(r[2] for day in right for r in plant[day])
    plant_overtime = sum(r[2] for rs in plant.values() for r in rs)
    claim(on_surge < plant_overtime, "surge days hold only part of the plant's overtime")
    years = d.years
    top_year = {y: sum(r[2] for day in right if day[:4] == str(y) for r in plant[day]) for y in years}
    return dict(center=center, n_plant_days=len(plant), n_distinct_rows=len(distinct_rows), n_all_centers=len(all_centers),
                n_one_entry=len(one_entry) - len(right), top_year=top_year,
                m_clock=steps(claim, model_m, "Filtered Rows", "Added Custom"),
                m_group=steps(claim, table_m("SurgeDays"), "Grouped Rows", "Filtered Rows"),
                m_days=measure(claim, "Surge Days"), m_surge=measure(claim, "Surge Overtime Hours"),
                m_plant=measure(claim, "Plant Overtime Hours"), m_share=measure(claim, "Surge Share of Overtime"),
                t_month=visual_title(claim, "ex163", "surgeDaysByMonth"), t_combo=visual_title(claim, "ex163", "surgeOvertime"),
                t_year=visual_title(claim, "ex163", "surgeByYear"),
                dax_days=check_expr(claim, "Exercise 16.3", "surge days in all"),
                dax_share=check_expr(claim, "Exercise 16.3", f"surge share of overtime {d.C}"),
                dax_hours=check_expr(claim, "Exercise 16.3", "total hours of the surge entries (MIN)"))


# --- Exercise 16.4 -----------------------------------------------------------------------------------------------------

@context("ch16.g4")
def g4(d, claim):
    ex = n16.register(d)
    pops = {p: n16.per_year(d, dates) for p, dates in n16.populations(d).items()}
    y = d.C
    in_year = [e for e in ex if e["date"][:4] == str(y)]
    unexplained_year = [e for e in in_year if e["disposition"] != "Expected" and e["test"] != "PR SelfApproved"]
    probe = "JE Weekend"
    own = sum(1 for e in in_year if e["test"] == probe)
    claim(own > 0, f"{probe} has exceptions in the current year, so its row of the table is not empty")
    self_year = sum(1 for e in in_year if e["test"] == "PR SelfApproved")
    claim(self_year > 0, "PR SelfApproved has exceptions in the current year, so a missing KEEPFILTERS shows a number where the right answer is blank")
    open_ = [e for e in ex if not e["disposition"] and e["test"] != "PR SelfApproved"]
    open_years = {p: n16.per_year(d, [e["date"] for e in open_ if e["process"] == p]) for p in n16.PROCESSES}
    unexplained_years = {p: n16.per_year(d, [e["date"] for e in ex if e["process"] == p and e["disposition"] != "Expected"
                                             and e["test"] != "PR SelfApproved"]) for p in n16.PROCESSES}
    claim(open_years["PR"] != unexplained_years["PR"] and open_years["PO"] != unexplained_years["PO"]
          and open_years["JE"] == unexplained_years["JE"],
          "the open exceptions differ from the unexplained ones for payroll and for purchase orders (the reviewed deficiencies and follow-ups stay in), and not for journal entries")
    claim(sum(open_years["PR"]) == 0,
          "every payroll exception outside the recurring test is reviewed, so an open-exceptions numerator finds none")
    blend = 1000 * len(in_year) / sum(pops[p][-1] for p in n16.PROCESSES)
    return dict(blend_rate=blend, probe=probe, probe_rate=1000 * own / pops["JE"][-1], probe_wrong=1000 * len(unexplained_year) / pops["JE"][-1],
                self_wrong=1000 * len(unexplained_year) / pops["PR"][-1], n_unexplained_year=len(unexplained_year),
                open_years=open_years, unexplained_years=unexplained_years,
                m_unexplained=measure(claim, "Unexplained Rate per 1,000"), m_population=measure(claim, "Population"),
                m_rate=measure(claim, "Rate per 1,000"),
                t_matrix=visual_title(claim, "ex164", "ratesMatrix"), t_line0=visual_title(claim, "ex164", "rateLine0"),
                t_line1=visual_title(claim, "ex164", "rateLine1"), t_table=visual_title(claim, "ex164", "ratesTable"),
                dax_rate=check_expr(claim, "Exercise 16.4", f"JE {d.C} unexplained rate per 1,000"),
                dax_blank=check_expr(claim, "Exercise 16.4", "the unexplained rate with PR SelfApproved selected (blank: KEEPFILTERS intersects)"),
                dax_total=check_expr(claim, "Exercise 16.4", "the total row's rate (blank)"))


# --- Exercise 16.5 -----------------------------------------------------------------------------------------------------

@context("ch16.g5")
def g5(d, claim):
    need(d, claim, "DisbursementPayment", "PurchaseInvoice")
    end = n16.asof(d)
    pay = d.q("SELECT p.Amount, pi.GrandTotal FROM DisbursementPayment p JOIN PurchaseInvoice pi "
              "ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate <= ?", end)
    amounts = [a for a, _ in pay]
    exact_full = sum(1 for a, g in pay if a == g)
    exact_part = sum(1 for a, g in pay if a < g)
    claim(exact_full + exact_part == len(pay), "an exact comparison of the amount with the invoice total splits the payments as the half-cent tolerance does")
    sci = [first_digit(a) for a in amounts]
    claim(min(sci) >= 1 and max(sci) <= 9, "the first significant digit of every payment is 1 to 9")
    text = [int(repr(a)[0]) for a in amounts]
    below = sum(1 for a in amounts if a < 1)
    claim(sum(1 for t in text if t == 0) == below and below > 0,
          "the payments whose text begins with 0 are exactly the payments below one dollar")
    whole = [int(str(Decimal(str(a)).quantize(Decimal(1), rounding=ROUND_HALF_UP))[0]) for a in amounts]
    differs = sum(1 for a, b in zip(sci, whole) if a != b)
    claim(differs > 0, "rounding the amount to a whole number before taking the first digit changes the digit of some payments")
    claim(abs(mad(sci) - n16.ex5(d, lambda c, t: None)["mad"]["all"]) < 1e-9, "the guide's MAD agrees with the note's")
    digit1 = abs(sum(1 for k in sci if k == 1) / len(sci) - math.log10(2))
    claim(digit1 > mad(sci), "one digit's deviation, read without REMOVEFILTERS, differs from the nine-digit MAD")
    after = d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PaymentDate > ?", end)
    claim(after > 0, "some payments are dated after the as-of date, so the date filter matters")
    ranges = n16.MAD_RANGES
    wrong_text = mad(text, len(amounts))
    claim(n16.conformity(wrong_text) == n16.conformity(mad(sci)), "the text-based first digit lands in the same conformity class, so only the digit-0 payments show the error")
    return dict(mad_digit1=digit1, below=below, share_text=sum(1 for t in text if t > 0) / len(amounts), mad_text=wrong_text, differs=differs,
                zeros_whole=sum(1 for w in whole if w == 0), mad_related=sum(1 - math.log10(1 + 1 / k) for k in range(1, 10)) / 9,
                after=after, all_payments=len(amounts) + after, ranges=ranges,
                m_pay=steps(claim, table_m("Payments"), "Filtered Rows", "Added Custom"),
                c_digit=column_line(claim, "Payments", "FirstDigit"), t_digits=source_of(claim, "Digits"),
                m_counted=measure(claim, "Payments Counted"), m_observed=measure(claim, "Observed Share"), m_mad=measure(claim, "Benford MAD"),
                m_expected=measure(claim, "Benford Share"),
                t_chart=visual_title(claim, "ex165", "digits"), t_slicer=visual_title(claim, "ex165", "kindSlicer"),
                t_table=visual_title(claim, "ex165", "madByKind"),
                dax_mad=check_expr(claim, "Exercise 16.5", "MAD, partial payments"),
                dax_zero=check_expr(claim, "Exercise 16.5", "payments with a first digit of 0"),
                dax_text=check_expr(claim, "Exercise 16.5", "payments whose text begins with 0 (below $1)"))


# --- Exercise 16.6 -----------------------------------------------------------------------------------------------------

@context("ch16.g6")
def g6(d, claim):
    need(d, claim, "DisbursementPayment", "PurchaseOrder", "JournalEntry", "PayrollRegister", "Employee")
    end = n16.asof(d)
    merged = d.q("SELECT a.DisbursementID, b.DisbursementID, a.PaymentDate, b.PaymentDate FROM DisbursementPayment a "
                 "JOIN DisbursementPayment b ON b.SupplierID = a.SupplierID AND b.Amount = a.Amount "
                 "WHERE a.PaymentDate <= ?1 AND b.PaymentDate <= ?1", end)
    right = [r for r in merged if r[0] < r[1] and r[2] != r[3]]
    date_only = [r for r in merged if r[2] != r[3]]
    id_only = [r for r in merged if r[0] < r[1]]
    self_pairs = [r for r in merged if r[0] == r[1]]
    claim(len(date_only) == 2 * len(right), "a filter on the dates alone keeps every pair in both orders")
    claim(len(id_only) == len(right), "no two payments of one supplier and one amount share a date, so the filter on the keys alone gives the same pairs")
    orders = d.one("SELECT COUNT(*) FROM PurchaseOrder")
    registers = d.one("SELECT COUNT(*) FROM PayrollRegister")
    approvers = {r[0] for r in d.q("SELECT ApprovedByEmployeeID FROM PurchaseOrder UNION SELECT ApprovedByEmployeeID FROM JournalEntry "
                                   "UNION SELECT ApprovedByEmployeeID FROM PayrollRegister")}
    claim(0 < len(approvers) < 20, "only a handful of employees approve any document, so the table of shares is short")
    days = [abs(d.one("SELECT julianday(?) - julianday(?)", r[3], r[2])) for r in right]
    pairs14 = sum(1 for x in days if x <= 14)
    claim(pairs14 > 0, "some pairs fall within two weeks")
    note = n16.ex6(d, lambda c, t: None)
    # a relationship from Employee to PayrollRegister on the payee's EmployeeID would intersect with the approver
    top = d.q("SELECT ApprovedByEmployeeID, COUNT(*) FROM PayrollRegister GROUP BY 1 ORDER BY 2 DESC LIMIT 1")[0]
    paid_to_self = d.one("SELECT COUNT(*) FROM PayrollRegister WHERE ApprovedByEmployeeID = ?1 AND EmployeeID = ?1", top[0])
    claim(0 < paid_to_self < top[1], "the employee who approves the most registers was paid on only some of them, so a relationship on the payee would cut the count")
    return dict(merge_rows=len(merged), approver_n=top[1], payee_n=paid_to_self, self_pairs=len(self_pairs), date_only=len(date_only), id_only=len(id_only), orders=orders,
                registers=registers, n_approvers=len(approvers), n_employees=d.one("SELECT COUNT(*) FROM Employee"),
                within14=pairs14, shortest=min(days), longest=max(days), total_orders=orders,
                m_pairs=steps(claim, table_m("PaymentPairs"), "Merged Queries", "Filtered Rows"),
                e_days_apart=custom_expr(claim, table_m("PaymentPairs"), "DaysApart"), e_same=custom_expr(claim, table_m("PaymentPairs"), "SameInvoice"),
                m_pair_count=measure(claim, "Pairs"), m_within30=measure(claim, "Pairs Within 30 Days"),
                m_orders_share=measure(claim, "Orders Share"), m_registers_share=measure(claim, "Registers Share"),
                m_orders=measure(claim, "Orders Approved"), m_entries=measure(claim, "Entries Approved"),
                m_registers=measure(claim, "Registers Approved"), m_entries_share=measure(claim, "Entries Share"),
                m_pairs_same=measure(claim, "Pairs on the Same Invoice"),
                t_shares=visual_title(claim, "ex166", "approvalShares"), t_days=visual_title(claim, "ex166", "pairsByDays"),
                dax_pairs=check_expr(claim, "Exercise 16.6", "near-duplicate pairs"),
                dax_cfo=check_expr(claim, "Exercise 16.6", "Orders Share, Chief Financial Officer"),
                dax_others=check_expr(claim, "Exercise 16.6", "orders approved by others than the CFO"))
