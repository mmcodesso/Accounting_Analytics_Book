"""The Part IV case's instructor notes (finding the cash behind the profit): the values each note states, and the
claims its wording makes.

The case is set in the middle of d.N, and the report runs through Data Through, the earliest of the last posting
dates of the documents behind the working-capital accounts (the end of d.C). Every value is the SQL twin of the DAX
and Power Query of the case's reference model: balances follow Exercise 14.1's Balance measure (postings on or before
the as-of date, the year-end closes left out only when dated on it), flows leave the closes out, and the working-capital
measures divide a quarter-end balance by the ledger flow of the twelve months that end on that date, times 365. Amounts
are rounded half away from zero, as DAX's ROUND and Number.Round do.

Two statements are worded more loosely than the data: Requirement 3's "receivables run about a week beyond terms" holds
for days sales outstanding without the opening line (as recorded it is about eleven days), and Requirement 5's
negative receivable balances were "credited to 2060 and refunded" except for the few still awaiting a refund at the
year-end (the balance of 2060). The claims test the wording on those readings.

One note is not registered, because its comment states a value the data do not give; its context function renders
the corrected text, so register it once the comment is fixed:
- r4 gives the purchase order lines not fully received at the year-end as 617,265.17, the sum of its two parts each
  rounded (other items 208,680.287 and materials 408,584.875); the lines total 617,265.162, which rounds to 617,265.16.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

from notes import note
from notes.case3 import processed

CASE = "cases/part-4-case.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
MATERIALS = ("Raw Materials", "Packaging")
SHORTFALL = "WO-COMPONENT-SHORTFALL"
CHANNEL = ("CASE WHEN r.Justification LIKE 'WO-COMPONENT-SHORTFALL%' THEN 'Shortfall' "
           "WHEN r.Justification LIKE 'Supply plan%' THEN 'Supply plan' ELSE 'Other' END")
# The documents behind the working-capital accounts, whose last posting dates Data Through takes the earliest of.
DATA_SOURCES = ("SalesInvoice", "CashReceiptApplication", "PurchaseInvoice", "DisbursementPayment", "GoodsReceipt",
                "MaterialIssue", "Shipment")
# The bridge's steps in their order (the Step column of Account), and the operating ones.
STEPS = ["net_income", "depreciation", "receivables", "inventories", "other_ca", "payables", "sales_tax", "other_cl",
         "fixed", "debt_equity"]
OPERATING = STEPS[:8]
WORKING_CAPITAL = STEPS[2:8]
# Requirement 4's what-if targets, the days of materials supply the requirement asks to test.
TARGETS = (28, 60, 90)
FG_TARGET = 28          # the finished goods target the note tests, in days of shipments
# Requirement 5's roll-forward: each working-capital account's sources, in the order the note lists them.
ROLL = {"1020": ["SalesInvoice", "CashReceiptApplication", "CreditMemo", "JournalEntry"],
        "1045": ["GoodsReceipt", "MaterialIssue", "JournalEntry"],
        "1040": ["JournalEntry", "GoodsReceipt", "ProductionCompletion", "SalesReturn", "Shipment"],
        "2010": ["PurchaseInvoice", "DisbursementPayment", "JournalEntry"],
        "2020": ["GoodsReceipt", "PurchaseInvoice"],
        "2050": ["SalesInvoice", "CreditMemo"]}
SHORT_TITLES = {"Chief Financial Officer": "CFO"}


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def xr(x: float, places: int = 2) -> float:
    """Round half away from zero, as DAX's ROUND does (and without a negative zero)."""
    return float(Decimal(repr(round(x, 9))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)) + 0.0


def year_end(year: int) -> str:
    return f"{year}-12-31"


# --- the ledger, summarized once -----------------------------------------------------------------

@lru_cache(maxsize=None)
def opening_entry(d) -> str:
    return d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")


@lru_cache(maxsize=None)
def accounts(d) -> dict[str, tuple[str, str]]:
    return {str(n): (t, s) for n, t, s in d.q("SELECT AccountNumber, AccountType, AccountSubType FROM Account")}


@lru_cache(maxsize=None)
def ledger(d) -> dict[str, list[tuple]]:
    """GLEntry by account number: (source type, posting date, is a close, is the opening entry, debits, credits, rows)."""
    closes = ",".join(f"'{c}'" for c in d.closes)
    rows = d.q(f"SELECT a.AccountNumber, g.SourceDocumentType, g.PostingDate, g.VoucherNumber IN ({closes}), "
               f"g.VoucherNumber = ?, SUM(g.Debit), SUM(g.Credit), COUNT(*) FROM GLEntry g JOIN Account a "
               f"ON a.AccountID = g.AccountID GROUP BY 1, 2, 3, 4, 5", opening_entry(d))
    out = defaultdict(list)
    for n, *rest in rows:
        out[str(n)].append(tuple(rest))
    return out


def numbers(d, pred) -> list[str]:
    return [n for n, (t, s) in accounts(d).items() if pred(n, t, s)]


def balance(d, nums, asof: str, opening: bool = True) -> float:
    """Exercise 14.1's Balance (debits less credits): postings on or before the as-of date, the closes left out
    only when dated on it."""
    total = 0.0
    for n in nums:
        for src, day, close, op, dr, cr, k in ledger(d).get(n, ()):
            if day <= asof and not (close and day == asof) and (opening or not op):
                total += dr - cr
    return total


def flow(d, nums, first: str, last: str, src: str | None = None) -> tuple[float, float]:
    """Debits and credits posted between two dates, the closes left out."""
    dr_total = cr_total = 0.0
    for n in nums:
        for s, day, close, op, dr, cr, k in ledger(d).get(n, ()):
            if first <= day <= last and not close and (src is None or s == src):
                dr_total += dr
                cr_total += cr
    return dr_total, cr_total


def step_of(n: str, t: str, s: str) -> str:
    """Requirement 2's Step column, the if-then-else chain on AccountSubType and account numbers."""
    if n == "1010":
        return "cash"
    if t in ("Revenue", "Expense"):
        return "net_income"
    if s == "Contra Fixed Asset":
        return "depreciation"
    if n in ("1020", "1030"):
        return "receivables"
    if n in ("1040", "1045", "1046"):
        return "inventories"
    if s in ("Current Asset", "Contra Current Asset"):
        return "other_ca"
    if n in ("2010", "2020"):
        return "payables"
    if n == "2050":
        return "sales_tax"
    if s == "Current Liability":
        return "other_cl"
    if s in ("Fixed Asset", "Noncurrent Asset"):
        return "fixed"
    return "debt_equity"


@lru_cache(maxsize=None)
def bridge(d, year: int, opening: bool = True) -> dict[str, float]:
    """Each step's effect on cash in a fiscal year (credits less debits of its accounts, the closes left out), the
    change in cash, and the activities as recorded."""
    out = dict.fromkeys(STEPS + ["cash"], 0.0)
    for n, (t, s) in accounts(d).items():
        step = step_of(n, t, s)
        for src, day, close, op, dr, cr, k in ledger(d).get(n, ()):
            if day[:4] == str(year) and not close and (opening or not op):
                out[step] += cr - dr
    out["cash"] = -out["cash"]
    out = {k: xr(v) for k, v in out.items()}
    out.update(operating=xr(sum(out[k] for k in OPERATING)), investing=out["fixed"], financing=out["debt_equity"],
               wc=xr(sum(out[k] for k in WORKING_CAPITAL)))
    return out


@lru_cache(maxsize=None)
def data_through(d) -> str:
    marks = ",".join("?" * len(DATA_SOURCES))
    return min(day for _, day in d.q(f"SELECT SourceDocumentType, MAX(PostingDate) FROM GLEntry "
                                     f"WHERE SourceDocumentType IN ({marks}) GROUP BY 1", *DATA_SOURCES))


@lru_cache(maxsize=None)
def opening_line(d, number: str) -> float:
    """The opening entry's line to an account, debits less credits."""
    return sum(dr - cr for src, day, close, op, dr, cr, k in ledger(d).get(number, ()) if op)


# --- the working-capital measures ------------------------------------------------------------------

def window_start(end: str) -> str:
    """The first day of DATESINPERIOD ( 'Date'[Date], end, -12, MONTH ) at a month-end."""
    e = date.fromisoformat(end)
    return (date(e.year - 1, e.month, e.day) + timedelta(days=1)).isoformat()


def cogs_accounts(d) -> list[str]:
    return numbers(d, lambda n, t, s: s == "COGS")


@lru_cache(maxsize=None)
def quarters(d) -> tuple[dict, ...]:
    """The quarter-end measures where the twelve-month window is full and ends by Data Through."""
    out = []
    for y in range(d.F, d.N + 1):
        for m, last in ((3, 31), (6, 30), (9, 30), (12, 31)):
            end = f"{y}-{m:02d}-{last}"
            first = window_start(end)
            if first < f"{d.F}-01-01" or end > data_through(d):
                continue
            ar, ar_x = balance(d, ["1020"], end), balance(d, ["1020"], end, opening=False)
            bill = flow(d, ["1020"], first, end, "SalesInvoice")[0]
            inv = balance(d, ["1040", "1045", "1046"], end)
            dr, cr = flow(d, cogs_accounts(d), first, end)
            cogs = dr - cr
            mat = balance(d, ["1045"], end)
            dr, cr = flow(d, ["1045"], first, end, "MaterialIssue")
            issues = cr - dr
            fg = balance(d, ["1040"], end)
            dr, cr = flow(d, ["1040"], first, end, "Shipment")
            ships = cr - dr
            ap, ap_x = -balance(d, ["2010"], end), -balance(d, ["2010"], end, opening=False)
            dr, cr = flow(d, ["2010"], first, end, "PurchaseInvoice")
            purchases = cr - dr
            dso, dso_x, dio = ar / bill * 365, ar_x / bill * 365, inv / cogs * 365
            dpo, dpo_x = ap / purchases * 365, ap_x / purchases * 365
            out.append(dict(end=end, label=f"{y}-Q{m // 3}", dso=xr(dso, 1), dso_x=xr(dso_x, 1), dio=xr(dio, 1),
                            mat=xr(mat / issues * 365, 1), fg=xr(fg / ships * 365, 1), dpo=xr(dpo, 1), dpo_x=xr(dpo_x, 1),
                            ccc=xr(dso + dio - dpo, 1), ccc_x=xr(dso_x + dio - dpo_x, 1), purchases=purchases,
                            inv=inv, mat_balance=mat, fg_balance=fg, issues=issues))
    return tuple(out)


def quarter(d, end: str) -> dict:
    return next(q for q in quarters(d) if q["end"] == end)


@lru_cache(maxsize=None)
def averages(d) -> tuple[dict, ...]:
    """The average-balance versions by fiscal year; the beginning balance of the first year is the opening entry."""
    out = []
    for y in d.years:
        first, last = f"{y}-01-01", year_end(y)

        def avg(nums):
            begin = sum(opening_line(d, n) for n in nums) if y == d.F else balance(d, nums, year_end(y - 1))
            return (begin + balance(d, nums, last)) / 2
        bill = flow(d, ["1020"], first, last, "SalesInvoice")[0]
        dr, cr = flow(d, cogs_accounts(d), first, last)
        idr, icr = flow(d, ["1045"], first, last, "MaterialIssue")
        pdr, pcr = flow(d, ["2010"], first, last, "PurchaseInvoice")
        out.append(dict(year=y, dso=xr(avg(["1020"]) / bill * 365, 1), dio=xr(avg(["1040", "1045", "1046"]) / (dr - cr) * 365, 1),
                        mat=xr(avg(["1045"]) / (icr - idr) * 365, 1), dpo=xr(-avg(["2010"]) / (pcr - pdr) * 365, 1)))
    return tuple(out)


# --- documents ---------------------------------------------------------------------------------------

def capital_invoices(d, through: str) -> list[dict]:
    """The supplier invoices moved to notes payable by the Debt Reclass entries (each entry's description names the
    invoice's PurchaseInvoiceID), in posting order."""
    out = []
    for number, posted, total, text in d.q("SELECT EntryNumber, PostingDate, TotalAmount, Description FROM JournalEntry "
                                           "WHERE EntryType = 'Debt Reclass' AND PostingDate <= ? ORDER BY PostingDate",
                                           through):
        pid = int(re.search(r"invoice (\d+)", text).group(1))
        inv = d.q("SELECT InvoiceNumber, GrandTotal, DueDate, ReceivedDate FROM PurchaseInvoice WHERE PurchaseInvoiceID = ?", pid)[0]
        paid = d.one("SELECT COALESCE(SUM(Amount), 0) FROM DisbursementPayment WHERE PurchaseInvoiceID = ? AND PaymentDate <= ?",
                     pid, through)
        lines = d.q("SELECT a.AccountNumber, g.Debit, g.Credit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                    "WHERE g.SourceDocumentType = 'JournalEntry' AND g.VoucherNumber = ?", number)
        receipts = [r[0] for r in d.q("SELECT DISTINCT gr.ReceiptNumber FROM PurchaseInvoiceLine l JOIN GoodsReceiptLine grl "
                                      "ON grl.GoodsReceiptLineID = l.GoodsReceiptLineID JOIN GoodsReceipt gr ON gr.GoodsReceiptID = "
                                      "grl.GoodsReceiptID WHERE l.PurchaseInvoiceID = ?", pid)]
        out.append(dict(entry=number, posted=posted, amount=total, id=pid, number=inv[0], total=inv[1], due=inv[2],
                        received=inv[3], paid=paid, lines=[(str(a), dr, cr) for a, dr, cr in lines], receipts=receipts))
    return out


def disposals(d, year: int) -> list[dict]:
    """The Asset Disposal entries of a fiscal year: the cost removed, the depreciation written off, the loss (debit to
    a Revenue account) and the proceeds (debit to cash)."""
    out = []
    for (number,) in d.q("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Asset Disposal' AND substr(PostingDate, 1, 4) = ? "
                         "ORDER BY PostingDate", str(year)):
        lines = [(str(n), t, s, dr, cr) for n, t, s, dr, cr in d.q(
            "SELECT a.AccountNumber, a.AccountType, a.AccountSubType, g.Debit, g.Credit FROM GLEntry g JOIN Account a "
            "ON a.AccountID = g.AccountID WHERE g.SourceDocumentType = 'JournalEntry' AND g.VoucherNumber = ?", number)]
        cost = [l for l in lines if l[2] == "Fixed Asset" and l[4] > 0]
        written = [l for l in lines if l[2] == "Contra Fixed Asset" and l[3] > 0]
        loss = [l for l in lines if l[1] in ("Revenue", "Expense")]
        cash = [l for l in lines if l[0] == "1010"]
        out.append(dict(entry=number, lines=lines, cost_account=cost[0][0] if cost else "?", cost=sum(l[4] for l in cost),
                        written_account=written[0][0] if written else "?", written=sum(l[3] for l in written),
                        loss_account=loss[0][0] if loss else "?", loss=sum(l[3] - l[4] for l in loss),
                        proceeds=sum(l[3] - l[4] for l in cash)))
    return out


def depreciation_entries(d, year: int) -> float:
    return d.one("SELECT COALESCE(SUM(g.Credit - g.Debit), 0) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                 "JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber WHERE g.SourceDocumentType = 'JournalEntry' "
                 "AND j.EntryType = 'Depreciation' AND a.AccountSubType = 'Contra Fixed Asset' AND g.FiscalYear = ?", year)


def principal(d, year: int) -> tuple[int, float]:
    """The Debt Principal Payment entries of a fiscal year and their debits to 2110."""
    return d.q("SELECT COUNT(DISTINCT g.VoucherNumber), COALESCE(SUM(g.Debit), 0) FROM GLEntry g JOIN JournalEntry j "
               "ON j.EntryNumber = g.VoucherNumber WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryType = "
               "'Debt Principal Payment' AND g.AccountID = ? AND g.FiscalYear = ?", d.account("2110"), year)[0]


@lru_cache(maxsize=None)
def restated(d, year: int) -> dict:
    """The indirect method's sections: the recorded steps with the entries that moved no cash taken out (equipment
    financed by a note, and disposals with their write-offs and losses)."""
    b = bridge(d, year)
    notes_financed = sum(c["amount"] for c in capital_invoices(d, year_end(year)) if c["posted"][:4] == str(year))
    disp = disposals(d, year)
    written, loss = sum(x["written"] for x in disp), sum(x["loss"] for x in disp)
    cost, proceeds = sum(x["cost"] for x in disp), sum(x["proceeds"] for x in disp)
    return dict(operating=xr(b["operating"] + written + loss), investing=xr(b["investing"] + notes_financed - cost + proceeds),
                financing=xr(b["financing"] - notes_financed), notes_financed=notes_financed, disposals=disp,
                written=written, loss=loss, cost=cost, proceeds=proceeds, depreciation=xr(depreciation_entries(d, year)))


@lru_cache(maxsize=None)
def unordered(d) -> list[tuple]:
    """Requisitions on no purchase order line: (status, channel, request date, estimated value)."""
    return d.q(f"SELECT r.Status, {CHANNEL}, r.RequestDate, r.Quantity * r.EstimatedUnitCost FROM PurchaseRequisition r "
               f"LEFT JOIN (SELECT DISTINCT RequisitionID FROM PurchaseOrderLine) p ON p.RequisitionID = r.RequisitionID "
               f"WHERE p.RequisitionID IS NULL")


@lru_cache(maxsize=None)
def policies(d) -> dict:
    rows = d.q("SELECT i.ItemGroup, i.ItemType, i.SupplyMode, p.PolicyType, p.TargetDaysSupply, p.EffectiveEndDate "
               "FROM InventoryPolicy p JOIN Item i ON i.ItemID = p.ItemID")
    return dict(rows=rows, ends=sorted({r[5] for r in rows}))


def materials_issues(d, year: int) -> float:
    dr, cr = flow(d, ["1045"], f"{year}-01-01", year_end(year), "MaterialIssue")
    return cr - dr


def open_receivables(d, asof: str) -> list[tuple]:
    """Exercise 16.1's rebuild: each invoice dated by the as-of date less the cash applied and the credit memos dated
    by it, rounded to cents."""
    rows = d.q("SELECT si.SalesInvoiceID, si.GrandTotal - COALESCE((SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a "
               "WHERE a.SalesInvoiceID = si.SalesInvoiceID AND a.ApplicationDate <= ?1), 0) - COALESCE((SELECT SUM(c.GrandTotal) "
               "FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID AND c.CreditMemoDate <= ?1), 0) "
               "FROM SalesInvoice si WHERE si.InvoiceDate <= ?1", asof)
    return [(i, xr(b)) for i, b in rows]


def cross_year(d, year: int) -> list[dict]:
    """Sales invoices dated in a year and posted in a later one."""
    rows = d.q("SELECT si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate, MIN(g.PostingDate), si.GrandTotal FROM SalesInvoice si "
               "JOIN GLEntry g ON g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID = si.SalesInvoiceID "
               "WHERE substr(si.InvoiceDate, 1, 4) = ? GROUP BY si.SalesInvoiceID HAVING substr(MIN(g.PostingDate), 1, 4) > ? "
               "ORDER BY si.InvoiceNumber", str(year), str(year))
    out = []
    for sid, number, dated, posted, total in rows:
        shipped = d.one("SELECT MAX(s.ShipmentDate) FROM SalesInvoiceLine l JOIN ShipmentLine sl ON sl.ShipmentLineID = "
                        "l.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE l.SalesInvoiceID = ?", sid)
        out.append(dict(number=number, dated=dated, posted=posted, total=total, shipped=shipped))
    return out


def number_range(invoices: list[dict]) -> str:
    """'SI-2025-006733 to 006735' for consecutive numbers."""
    first, last = invoices[0]["number"], invoices[-1]["number"]
    return first if first == last else f"{first} to {last.rsplit('-', 1)[1]}"


def consecutive(invoices: list[dict]) -> bool:
    seqs = [int(i["number"].rsplit("-", 1)[1]) for i in invoices]
    return seqs == list(range(seqs[0], seqs[0] + len(seqs)))


# --- Requirement 1 -------------------------------------------------------------------------------

@note("case4.r1", CASE)
def r1(d, claim):
    gl_rows = d.one("SELECT COUNT(*) FROM GLEntry")
    closes = []
    for y in d.years:
        entries = d.closes_of(y)
        claim(len(entries) == 2, f"fiscal {y} has two year-end closes")
        closes.append(entries[0] + "".join(f" and -{e.rsplit('-', 1)[1]}" for e in entries[1:]))
    claim(sum(len(d.closes_of(y)) for y in d.years) == len(d.closes), "every close is dated at a year-end of the window")
    close_rows = sum(k for rows in ledger(d).values() for src, day, close, op, dr, cr, k in rows if close)
    channels = dict(d.q(f"SELECT {CHANNEL}, COUNT(*) FROM PurchaseRequisition r GROUP BY 1"))
    item_ok, n_short = d.q("SELECT SUM(CAST(substr(Justification, instr(Justification, 'ITEM=') + 5) AS INTEGER) = ItemID), "
                           "COUNT(*) FROM PurchaseRequisition WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%'")[0]
    claim(item_ok == n_short, "the ITEM in a shortfall justification always equals ItemID")
    no_rec = d.one("SELECT COUNT(*) FROM PurchaseRequisition WHERE Justification LIKE 'Supply plan%' "
                   "AND SupplyPlanRecommendationID IS NULL")
    claim(0 < no_rec < channels["Supply plan"], "all but a few supply-plan requisitions carry a SupplyPlanRecommendationID")
    other_groups = {r[0] for r in d.q(f"SELECT i.ItemGroup FROM PurchaseRequisition r JOIN Item i ON i.ItemID = r.ItemID "
                                      f"WHERE {CHANNEL} = 'Other'")}
    claim(other_groups == {"Capex"}, "the other requisitions are capital requests")
    receipt_lines, orphan_receipts = d.q("SELECT COUNT(*), SUM(p.POLineID IS NULL) FROM GoodsReceiptLine l LEFT JOIN "
                                         "PurchaseOrderLine p ON p.POLineID = l.POLineID")[0]
    claim(orphan_receipts == 0, "every receipt line has its order line")
    po_lines, no_req = d.q("SELECT COUNT(*), SUM(r.RequisitionID IS NULL) FROM PurchaseOrderLine p LEFT JOIN PurchaseRequisition r "
                           "ON r.RequisitionID = p.RequisitionID")[0]
    claim(no_req == 0, "every order line has exactly one requisition")
    blank_header = d.one("SELECT COUNT(*) FROM PurchaseOrder WHERE RequisitionID IS NULL")
    issue_lines, issues_with_lines = d.q("SELECT COUNT(*), COUNT(DISTINCT MaterialIssueID) FROM MaterialIssueLine")[0]
    claim(d.one("SELECT COUNT(*) FROM MaterialIssue m LEFT JOIN WorkOrder w ON w.WorkOrderID = m.WorkOrderID "
                "WHERE w.WorkOrderID IS NULL") == 0, "every issue has its work order")
    claim(d.one("SELECT COUNT(*) FROM MaterialIssueLine l LEFT JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID "
                "WHERE m.MaterialIssueID IS NULL") == 0, "every issue line has its issue")
    empty_issues = d.one("SELECT COUNT(*) FROM MaterialIssue m LEFT JOIN (SELECT DISTINCT MaterialIssueID FROM MaterialIssueLine) l "
                         "ON l.MaterialIssueID = m.MaterialIssueID WHERE l.MaterialIssueID IS NULL")
    requisitions = d.one("SELECT COUNT(*) FROM PurchaseRequisition")
    no_approver = d.one("SELECT COUNT(*) FROM PurchaseRequisition WHERE ApprovedByEmployeeID IS NULL")
    never = unordered(d)
    claim(all(r[0] == "Approved" for r in never), "the requisitions never ordered are Approved")
    claim(all(r[1] == "Shortfall" and r[2][:7] == f"{d.C}-12" for r in never),
          f"the requisitions never ordered are all work-order shortfall requisitions of December {d.C}")
    # Validation.
    ni = [bridge(d, y)["net_income"] for y in d.years]
    assets = [xr(balance(d, numbers(d, lambda n, t, s: t == "Asset"), year_end(y))) for y in d.years]
    marks = ",".join("?" * len(MATERIALS))
    received = dict(d.q(f"SELECT substr(g.ReceiptDate, 1, 4), SUM(l.ExtendedStandardCost) FROM GoodsReceiptLine l "
                        f"JOIN GoodsReceipt g ON g.GoodsReceiptID = l.GoodsReceiptID JOIN Item i ON i.ItemID = l.ItemID "
                        f"WHERE i.ItemGroup IN ({marks}) GROUP BY 1", *MATERIALS))
    issued = dict(d.q("SELECT substr(m.IssueDate, 1, 4), SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l "
                      "JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID GROUP BY 1"))
    received = [xr(received.get(str(y), 0.0)) for y in d.years]
    issued = [xr(issued.get(str(y), 0.0)) for y in d.years]
    for y, rec, iss in zip(d.years, received, issued):
        gr = flow(d, ["1045"], f"{y}-01-01", year_end(y), "GoodsReceipt")[0]
        mi = flow(d, ["1045"], f"{y}-01-01", year_end(y), "MaterialIssue")[1]
        claim(abs(gr - rec) < 0.005 and abs(mi - iss) < 0.005,
              f"the materials received and issued in {y} equal the GoodsReceipt debits and MaterialIssue credits to 1045")
    # Data Through and what follows it.
    thru = data_through(d)
    last = d.one("SELECT MAX(PostingDate) FROM GLEntry")
    after = d.q("SELECT g.SourceDocumentType, a.AccountNumber, SUM(g.Debit), SUM(g.Credit), COUNT(*) FROM GLEntry g "
                "JOIN Account a ON a.AccountID = g.AccountID WHERE g.PostingDate > ? GROUP BY 1, 2", thru)
    claim({(r[0], str(r[1])) for r in after} == {("DisbursementPayment", "2010"), ("DisbursementPayment", "1010")}
          and all((r[3] == 0) if str(r[1]) == "2010" else (r[2] == 0) for r in after),
          "the postings after Data Through are supplier payments, Dr 2010 and Cr 1010")
    n_pay, pay_amount, first_invoice, last_invoice = d.q(
        "SELECT COUNT(*), SUM(p.Amount), MIN(pi.InvoiceDate), MAX(pi.InvoiceDate) FROM DisbursementPayment p "
        "JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate > ?", thru)[0]
    claim(first_invoice[:4] == last_invoice[:4] == str(d.C), f"the payments after Data Through pay invoices of {d.C}")
    rows_after = sum(r[4] for r in after)
    claim(abs(sum(r[2] for r in after if str(r[1]) == "2010") - pay_amount) < 0.005, "the payments' debits to 2010 equal their amount")
    fall = -bridge(d, d.N)["cash"]
    claim(abs(fall - pay_amount) < 0.005, f"the bridge for {d.N} shows a fall of exactly the payments")
    payroll_end = d.one("SELECT MAX(PostingDate) FROM GLEntry WHERE SourceDocumentType IN ('PayrollSummary', 'PayrollPayment')")
    open_periods = d.q("SELECT PayrollPeriodID, PeriodStartDate FROM PayrollPeriod WHERE Status = 'Open' AND PeriodStartDate <= ? "
                       "ORDER BY 1", year_end(d.C))
    later = d.one("SELECT COUNT(*) FROM PayrollPeriod WHERE Status <> 'Open' AND PayrollPeriodID > ?",
                  min((p[0] for p in open_periods), default=0))
    claim(open_periods and later == 0, "the open pay periods are the last ones")
    claim(payroll_end < thru and payroll_end < year_end(d.C),
          "payroll postings end before Data Through, so including them would blank the last quarter")
    return dict(gl_rows=gl_rows, n_closes=word(len(d.closes)), closes=closes, close_rows=close_rows,
                shortfall=channels["Shortfall"], supply=channels["Supply plan"], no_rec=no_rec,
                n_other=word(channels.get("Other", 0)), receipt_lines=receipt_lines, po_lines=po_lines,
                blank_header=blank_header, issue_lines=issue_lines, issues_with_lines=issues_with_lines,
                empty_issues=empty_issues, requisitions=requisitions, no_approver=no_approver, unordered=len(never),
                ni=ni, assets=assets, received=received, issued=issued, thru=thru, last=last, n_pay=n_pay,
                rows_after=rows_after, pay_amount=xr(pay_amount), cash_last=xr(balance(d, ["1010"], last)),
                ap_last=xr(-balance(d, ["2010"], last)), fall=xr(fall), payroll_end=payroll_end,
                n_open=word(len(open_periods)))


# --- Requirement 2 -------------------------------------------------------------------------------

@note("case4.r2", CASE)
def r2(d, claim):
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE CAST(substr(PostingDate, 1, 4) AS INTEGER) <> FiscalYear") == 0,
          "every posting's fiscal year is its calendar year")
    current = numbers(d, lambda n, t, s: s in ("Current Asset", "Contra Current Asset"))
    liabilities = numbers(d, lambda n, t, s: s == "Current Liability")
    ye = []
    for y in d.years:
        ca, cl = balance(d, current, year_end(y)), -balance(d, liabilities, year_end(y))
        quick = balance(d, ["1010", "1020"], year_end(y))
        inv = balance(d, ["1040", "1045", "1046"], year_end(y))
        ye.append(dict(ca=xr(ca), cl=xr(cl), wc=xr(ca - cl), current=xr(ca / cl, 2), quick=xr(quick / cl, 2), inv_share=inv / ca))
    ratios, quicks = [y["current"] for y in ye], [y["quick"] for y in ye]
    claim(max(ratios) - min(ratios) < 0.05, "the current ratio is flat")
    claim(all(a > b for a, b in zip(quicks, quicks[1:])) and quicks[0] - quicks[-1] > 0.2, "the quick ratio falls every year")
    a1090 = xr(balance(d, ["1090"], year_end(d.C)))
    claim(a1090 < 0, f"1090 has a credit balance at the end of {d.C}")
    claim(all(accounts(d)[n][1] in ("Current Asset", "Contra Current Asset") for n in ("1090", "8020")),
          "1090 and 8020 are current assets, so they fall in other current assets")
    claim(accounts(d)["1030"][1] == "Contra Current Asset" and accounts(d)["2110"][1] == "Long-Term Liability",
          "1030 is a contra current asset and 2110 a long-term liability")
    years = {y: bridge(d, y) for y in d.years}
    cur, pri = years[d.C], years[d.P]
    for y, b in years.items():
        claim(abs(sum(b[k] for k in STEPS) - b["cash"]) < 0.01, f"the steps of {y} add up to the change in cash")
    cash = [xr(balance(d, ["1010"], year_end(y))) for y in d.years]
    claim(abs(cash[-1] - cash[-2] - cur["cash"]) < 0.01, f"the change in cash of {d.C} is the difference of the year-end balances")
    claim(bool(d.closes_of(d.P)), f"the {d.P} close moved that year's net income into retained earnings")
    claim(cur["cash"] < 0 < pri["cash"], f"cash fell in {d.C} after growing in {d.P}")
    # The first year: the opening entry.
    entry = opening_entry(d)
    entry_date, entry_lines = d.q("SELECT MIN(PostingDate), COUNT(*) FROM GLEntry WHERE VoucherNumber = ?", entry)[0]
    claim(entry_date[:4] == str(d.F), f"the opening entry is a {d.F} posting")
    claim(d.one("SELECT MIN(PostingDate) FROM GLEntry") == entry_date, "no posting precedes the opening entry, so cash starts at zero")
    first, first_x = years[d.F], bridge(d, d.F, opening=False)
    open_cash, open_ar = xr(opening_line(d, "1010")), xr(opening_line(d, "1020"))
    claim(abs(open_cash + first_x["cash"] - cash[0]) < 0.01, f"the change without the opening entry runs from its cash line to the {d.F} year-end")
    claim(abs(-first_x["receivables"] - (balance(d, ["1020", "1030"], year_end(d.F)) - open_ar)) < 0.01,
          "receivables without the opening entry only fill the ledger from its opening line")
    # Noncash entries of the current and prior year.
    capital = [c for c in capital_invoices(d, year_end(d.C)) if c["posted"][:4] == str(d.C)]
    claim(len(capital) == 1, f"one invoice was moved to notes payable in {d.C}")
    c = capital[0]
    claim(sorted((a, dr > 0) for a, dr, cr in c["lines"]) == [("2010", True), ("2110", False)],
          "the reclass moves the invoice from 2010 to 2110")
    claim(len(c["receipts"]) == 1, "the financed equipment came in on one receipt")
    gr = d.q("SELECT a.AccountNumber, a.AccountSubType, g.Debit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
             "WHERE g.SourceDocumentType = 'GoodsReceipt' AND g.VoucherNumber = ? AND g.Debit > 0", c["receipts"][0])
    claim(len(gr) == 1 and gr[0][1] == "Fixed Asset" and abs(gr[0][2] - c["amount"]) < 0.005,
          "the receipt debits one fixed asset account with the amount financed")
    rc, rp = restated(d, d.C), restated(d, d.P)
    claim(len(rc["disposals"]) == 1 and len(rp["disposals"]) == 1, f"one disposal in each of {d.P} and {d.C}")
    disp, disp_p = rc["disposals"][0], rp["disposals"][0]
    claim(disp["proceeds"] == 0 and disp["loss"] > 0, f"the {d.C} disposal had no proceeds and a loss")
    claim(disp_p["proceeds"] > 0 and disp_p["loss"] > 0, f"the {d.P} disposal had proceeds and a loss")
    claim(abs(cur["depreciation"] - (rc["depreciation"] - disp["written"])) < 0.01,
          "the depreciation step is the depreciation entries net of the write-off")
    n_principal, paid = principal(d, d.C)
    claim(abs(rc["financing"] + paid) < 0.01, f"the restated financing of {d.C} is the principal paid")
    claim(abs(rp["financing"] + principal(d, d.P)[1]) < 0.01, f"the restated financing of {d.P} is the principal paid")
    claim(abs(paid - d.one("SELECT SUM(PrincipalAmount) FROM DebtScheduleLine WHERE Status = 'Paid' AND substr(PaymentDate, 1, 4) = ?",
                           str(d.C))) < 0.01, "the principal paid equals the schedule's paid lines")
    for y, r in ((d.C, rc), (d.P, rp)):
        claim(abs(r["operating"] + r["investing"] + r["financing"] - years[y]["cash"]) < 0.01,
              f"the restated sections of {y} add up to the change in cash")
    claim(abs(rc["operating"] - (cur["net_income"] + rc["depreciation"] + rc["loss"] + cur["wc"])) < 0.01,
          "restated operating = net income + depreciation + loss + changes in working capital")
    claim(abs(rp["operating"] - (pri["net_income"] + rp["depreciation"] + rp["loss"] + pri["wc"])) < 0.01,
          f"restated operating of {d.P} = net income + depreciation + loss + changes in working capital")
    claim(rp["notes_financed"] == 0, f"no equipment was financed by a note in {d.P}")
    capex = d.q("SELECT g.VoucherNumber, g.Debit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                "WHERE g.SourceDocumentType = 'GoodsReceipt' AND a.AccountSubType IN ('Fixed Asset', 'Noncurrent Asset') "
                "AND g.FiscalYear = ? ORDER BY g.PostingDate", d.P)
    paid_capex = d.q("SELECT DISTINCT pi.PurchaseInvoiceID, pi.GrandTotal, (SELECT SUM(p.Amount) FROM DisbursementPayment p WHERE "
                     "p.PurchaseInvoiceID = pi.PurchaseInvoiceID AND substr(p.PaymentDate, 1, 4) = ?) FROM GLEntry g "
                     "JOIN Account a ON a.AccountID = g.AccountID JOIN GoodsReceipt gr ON gr.GoodsReceiptID = g.SourceDocumentID "
                     "JOIN GoodsReceiptLine grl ON grl.GoodsReceiptID = gr.GoodsReceiptID JOIN PurchaseInvoiceLine l "
                     "ON l.GoodsReceiptLineID = grl.GoodsReceiptLineID JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = "
                     "l.PurchaseInvoiceID WHERE g.SourceDocumentType = 'GoodsReceipt' AND a.AccountSubType IN ('Fixed Asset', "
                     "'Noncurrent Asset') AND g.FiscalYear = ? ORDER BY pi.ReceivedDate", str(d.P), d.P)
    capex_total = sum(r[1] for r in capex)
    claim(all(p is not None and abs(p - t) < 0.005 for _, t, p in paid_capex) and abs(sum(r[1] for r in paid_capex) - capex_total) < 0.005,
          f"the equipment received in {d.P} was invoiced and paid in cash within the year")
    claim(abs(rp["investing"] - (-capex_total + disp_p["proceeds"])) < 0.01,
          f"restated investing of {d.P} = equipment paid less proceeds")
    # Sales tax, notes.
    tax = [xr(balance(d, ["1010", "2050"], year_end(y))) for y in d.years]
    tax_c = xr(-balance(d, ["2050"], year_end(d.C)))
    claim(all(years[y]["sales_tax"] > 0 for y in d.years), "the unremitted tax added cash every year")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND Debit > 0 AND SourceDocumentType <> 'CreditMemo'",
                d.account("2050")) == 0, "no remittance of the sales tax is recorded")
    outstanding = xr(-balance(d, ["2110"], year_end(d.C)))
    schedule = [xr(r[1]) for r in d.q(
        "SELECT DebtAgreementID, (SELECT s.EndingPrincipal FROM DebtScheduleLine s WHERE s.DebtAgreementID = x.DebtAgreementID "
        "AND s.PaymentDate <= ? ORDER BY s.PaymentDate DESC LIMIT 1) FROM DebtScheduleLine x WHERE x.PaymentDate <= ? "
        "GROUP BY 1 ORDER BY 1", year_end(d.C), year_end(d.C))]
    claim(abs(outstanding - sum(schedule)) < 0.01, "the notes in 2110 equal the schedule, so all of them sit in 2110")
    due_next = xr(d.one("SELECT SUM(PrincipalAmount) FROM DebtScheduleLine WHERE substr(PaymentDate, 1, 4) = ?", str(d.N)))
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID JOIN JournalEntry j ON j.EntryNumber = "
                "g.VoucherNumber WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryType LIKE 'Debt%' "
                "AND a.AccountSubType = 'Current Liability' AND g.Credit > 0") == 0,
          "no entry moved any of the notes to a current liability")
    return dict(ye=ye, inv_share=ye[-1]["inv_share"], a1090=-a1090, cur=cur, pri=pri, cash_from=cash[-2], cash_to=cash[-1],
                entry=entry, entry_lines=entry_lines, first=first, first_x=first_x, open_cash=open_cash, open_ar=open_ar,
                gr=c["receipts"][0], gr_account=str(gr[0][0]) if gr else "?", reclass=c["entry"], reclass_invoice=c["id"],
                financed=c["amount"], disp=disp, disp_p=disp_p, rc=rc, rp=rp, n_principal=n_principal,
                capex_total=capex_total, capex_invoices=[r[0] for r in paid_capex],
                tax_c=tax_c, net=tax, tax_steps=[years[y]["sales_tax"] for y in d.years],
                without_tax=xr(rc["operating"] - cur["sales_tax"]), outstanding=outstanding, schedule=schedule,
                due_next=due_next)


# --- Requirement 3 -------------------------------------------------------------------------------

@note("case4.r3", CASE)
def r3(d, claim):
    names = {r[0] for r in d.q("SELECT AccountName FROM Account WHERE AccountSubType = 'COGS'")}
    claim({"Freight-Out Expense", "Purchase Price Variance", "Manufacturing Variance"} <= names,
          "COGS includes freight-out, purchase price variance, and manufacturing variance")
    marks = ",".join(f"'{n}'" for n in cogs_accounts(d))
    cogs_closes = d.q(f"SELECT g.VoucherNumber, SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = "
                      f"g.AccountID WHERE a.AccountNumber IN ({marks}) AND g.SourceDocumentType = 'JournalEntry' AND "
                      f"g.PostingDate = ? AND g.VoucherNumber IN ({','.join('?' * len(d.closes_of(d.C)))}) GROUP BY 1 "
                      f"HAVING SUM(g.Credit) > 0", year_end(d.C), *d.closes_of(d.C))
    claim(len(cogs_closes) == 1, f"one close of {d.C} credits COGS")
    with_close = d.one(f"SELECT SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                       f"WHERE a.AccountNumber IN ({marks}) AND g.FiscalYear = ?", d.C)
    claim(abs(with_close) < 0.005, "a window that includes a close reads zero")
    for n, src, side in (("1020", "SalesInvoice", 1), ("1045", "MaterialIssue", 0), ("1040", "Shipment", 0),
                         ("2010", "PurchaseInvoice", 0)):
        dr, cr = flow(d, [n], f"{d.F}-01-01", f"{d.N}-12-31", src)
        claim((cr if side else dr) == 0, f"{src} only {'debits' if side else 'credits'} {n}")
    qs = quarters(d)
    thru = data_through(d)
    claim(qs[0]["end"] == year_end(d.F) and qs[-1]["end"] == year_end(d.C) and len(qs) == 4 * (len(d.years) - 1) + 1,
          f"the measures run from {d.F}-Q4 to {d.C}-Q4")
    claim(thru < f"{d.N}-03-31", f"every {d.N} quarter is blank")
    first, last = qs[0], qs[-1]
    ends = [quarter(d, year_end(y)) for y in d.years]
    avg = averages(d)
    claim(avg[-1]["mat"] < last["mat"], f"the average-balance version lags the build in {d.C}")
    claim(avg[0]["mat"] > first["mat"], f"in {d.F} the average-balance version overstates the year-end days")
    # Policy targets.
    pol = policies(d)
    rows = pol["rows"]
    raw = sorted({r[4] for r in rows if r[0] == "Raw Materials"})
    pack = sorted({r[4] for r in rows if r[0] == "Packaging"})
    claim(len(raw) == 1 and len(pack) == 1, "raw materials and packaging each have one target")
    made = [r for r in rows if r[1] == "Finished Good" and r[2] == "Manufactured"]
    bought = [r for r in rows if r[1] == "Finished Good" and r[2] == "Purchased"]
    claim({r[3] for r in made} == {"Lot-for-Lot"} and {r[3] for r in rows if r[3] == "Lot-for-Lot"} and
          all(r[2] == "Manufactured" for r in rows if r[3] == "Lot-for-Lot"), "the manufactured finished goods are lot-for-lot")
    claim({r[3] for r in bought} == {"Min-Max"}, "the purchased finished goods are min-max")
    claim(pol["ends"] == [year_end(d.C)], f"every policy ends {d.C}-12-31")
    customers = d.one("SELECT SUM(si.GrandTotal * CAST(REPLACE(c.PaymentTerms, 'Net ', '') AS REAL)) / SUM(si.GrandTotal) "
                      "FROM SalesInvoice si JOIN Customer c ON c.CustomerID = si.CustomerID")
    suppliers = d.one("SELECT SUM(pi.GrandTotal * CAST(REPLACE(s.PaymentTerms, 'Net ', '') AS REAL)) / SUM(pi.GrandTotal) "
                      "FROM PurchaseInvoice pi JOIN Supplier s ON s.SupplierID = pi.SupplierID")
    claim(4 <= last["dso_x"] - customers <= 10, "receivables (without the opening line) run about a week beyond terms")
    claim(21 <= last["dpo_x"] - suppliers < 28, "payables without the opening line run almost four weeks beyond terms")
    claim(abs(last["dso"] - first["dso"]) < 10 and abs(last["dpo_x"] - first["dpo_x"]) < 5,
          "receivables and payables barely moved")
    claim(last["dio"] - first["dio"] >= last["ccc_x"] - first["ccc_x"] > 0, "the cycle grew entirely through inventory")
    claim(last["mat_balance"] - first["mat_balance"] > (last["inv"] - first["inv"]) / 2
          and last["mat"] - first["mat"] > last["fg"] - first["fg"], "materials above all")
    claim(last["dpo"] < first["dpo"], "DPO as recorded fell")
    claim(last["purchases"] > first["purchases"] and abs(last["dpo_x"] - first["dpo_x"]) < 2,
          "the fall is the constant opening payables diluted by growing purchases")
    opening_ap = -opening_line(d, "2010")
    return dict(close=cogs_closes[0][0] if cogs_closes else "?", close_millions=(cogs_closes[0][1] if cogs_closes else 0) / 1e6,
                entry=opening_entry(d), qs=qs, ends=ends, avg=avg, raw=raw[0], pack=pack[0], made=(min(r[4] for r in made), max(r[4] for r in made)),
                bought=(min(r[4] for r in bought), max(r[4] for r in bought)), customers=customers, suppliers=suppliers,
                build_avg=avg[-1]["mat"], build_end=last["mat"], first_avg=avg[0]["mat"], first_end=first["mat"],
                dpo_from=first["dpo"], dpo_to=last["dpo"], opening_ap=opening_ap / 1e6)


# --- Requirement 4 -------------------------------------------------------------------------------

# Not registered: the comment states the purchase order lines not fully received as 617,265.17, the sum of its two
# rounded parts (208,680.29 + 408,584.88); the lines total 617,265.162, so 617,265.16. Register it once the comment is fixed.
@note("case4.r4", CASE)
def r4(d, claim):
    marks = ",".join("?" * len(MATERIALS))
    rows = d.q(f"SELECT substr(g.ReceiptDate, 1, 4), {CHANNEL}, COUNT(*), SUM(l.ExtendedStandardCost) FROM GoodsReceiptLine l "
               f"JOIN GoodsReceipt g ON g.GoodsReceiptID = l.GoodsReceiptID JOIN Item i ON i.ItemID = l.ItemID "
               f"JOIN PurchaseOrderLine p ON p.POLineID = l.POLineID LEFT JOIN PurchaseRequisition r ON r.RequisitionID = "
               f"p.RequisitionID WHERE i.ItemGroup IN ({marks}) GROUP BY 1, 2", *MATERIALS)
    claim({r[1] for r in rows} == {"Supply plan", "Shortfall"}, "materials come in through the supply plan and the shortfall channel only")
    receipts = {(int(y), ch): (n, xr(v)) for y, ch, n, v in rows}
    by_year = [dict(year=y, plan=receipts.get((y, "Supply plan"), (0, 0.0)), short=receipts.get((y, "Shortfall"), (0, 0.0)))
               for y in d.years]
    issues = {y: materials_issues(d, y) for y in d.years}
    claim(all(abs(v / 1e7 - 1) < 0.1 for v in issues.values()), "issues stayed near 10 million")
    groups = dict(d.q(f"SELECT i.ItemGroup, SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l JOIN MaterialIssue m "
                      f"ON m.MaterialIssueID = l.MaterialIssueID JOIN Item i ON i.ItemID = l.ItemID "
                      f"WHERE substr(m.IssueDate, 1, 4) = ? GROUP BY 1", str(d.C)))
    plans = [y["plan"][1] for y in by_year]
    shorts = [y["short"][1] for y in by_year]
    claim(max(plans) / min(plans) < 1.3 and max(issues.values()) / min(issues.values()) < 1.1,
          "the supply plan's receipts and production's use are flat")
    claim(all(y["plan"][1] < issues[y["year"]] for y in by_year) and all(a < b for a, b in zip(shorts, shorts[1:])),
          "the supply plan alone stays below use every year while shortfall receipts grow: the shortfall channel carries the build")
    build_rows = d.q(f"WITH r AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM GoodsReceiptLine l JOIN GoodsReceipt g "
                     f"ON g.GoodsReceiptID = l.GoodsReceiptID WHERE substr(g.ReceiptDate, 1, 4) = ?1 GROUP BY 1), "
                     f"s AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM MaterialIssueLine l JOIN MaterialIssue m "
                     f"ON m.MaterialIssueID = l.MaterialIssueID WHERE substr(m.IssueDate, 1, 4) = ?1 GROUP BY 1) "
                     f"SELECT i.ItemCode, i.ItemName, i.ItemGroup, COALESCE(r.v, 0) - COALESCE(s.v, 0) FROM Item i "
                     f"LEFT JOIN r ON r.ItemID = i.ItemID LEFT JOIN s ON s.ItemID = i.ItemID WHERE i.ItemGroup IN ('Raw Materials', "
                     f"'Packaging') ORDER BY 4 DESC", str(d.C))
    build = xr(sum(r[3] for r in build_rows))
    top = build_rows[:6]
    claim(all(r[2] == "Raw Materials" for r in top), "the six largest builds are raw materials")
    share = sum(r[3] for r in top) / build
    names = Counter(r[1] for r in top)
    top_items = []
    for i, r in enumerate(top):
        repeated = names[r[1]] > 1
        last_of_name = repeated and all(x[1] != r[1] for x in top[i + 1:])
        top_items.append(dict(code=r[0], name=None if repeated else r[1], amount=xr(r[3]),
                              plural=r[1] + "s" if last_of_name else None))
    packaging = xr(sum(r[3] for r in build_rows if r[2] == "Packaging"))
    claim(abs(build - (xr(sum(receipts.get((d.C, ch), (0, 0.0))[1] for ch in ("Supply plan", "Shortfall"))) - issues[d.C])) < 0.01,
          "the build by item adds up to the year's receipts less issues")
    opening_materials = xr(opening_line(d, "1045"))
    # Shortfall requisitions.
    yearly = d.q("SELECT substr(RequestDate, 1, 4), COUNT(*), SUM(Quantity * EstimatedUnitCost) FROM PurchaseRequisition "
                 "WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%' GROUP BY 1 ORDER BY 1")
    claim([int(r[0]) for r in yearly] == d.years, "the shortfall requisitions fall in the window's years")
    pairs = d.q("SELECT Justification, COUNT(*), SUM(Quantity), SUM(Quantity * EstimatedUnitCost), MIN(RequestDate), "
                "MAX(RequestDate) FROM PurchaseRequisition WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%' GROUP BY 1")
    repeated = [p for p in pairs if p[1] > 1]
    most = max(p[1] for p in pairs)
    top_pairs = [p for p in pairs if p[1] == most]
    claim(len(top_pairs) == 1, "one pair has the most requisitions")
    tp = top_pairs[0]
    wo_id, item_id = int(re.search(r"WO=(\d+)", tp[0]).group(1)), int(re.search(r"ITEM=(\d+)", tp[0]).group(1))
    wo = d.q("SELECT WorkOrderNumber, DueDate, CompletedDate FROM WorkOrder WHERE WorkOrderID = ?", wo_id)[0]
    item_code = d.one("SELECT ItemCode FROM Item WHERE ItemID = ?", item_id)
    dates = [r[0] for r in d.q("SELECT RequestDate FROM PurchaseRequisition WHERE Justification = ? ORDER BY 1", tp[0])]
    months = sorted({x[:7] for x in dates})
    span = (int(months[-1][:4]) - int(months[0][:4])) * 12 + int(months[-1][5:]) - int(months[0][5:]) + 1
    claim(len(months) == span and max(Counter(x[:7] for x in dates).values()) <= 2, "the pair was requisitioned monthly")
    claim(tp[5] > wo[1] and wo[2] > tp[5], "the pair was requisitioned long after the work order was due, and completed after the last one")
    issued = {k: (q, c) for k, q, c in d.q("SELECT 'WO-COMPONENT-SHORTFALL | WO=' || m.WorkOrderID || ' | ITEM=' || l.ItemID, "
                                           "SUM(l.QuantityIssued), SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l "
                                           "JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID GROUP BY 1")}
    matched = [p for p in pairs if p[0] in issued]
    short_receipts = xr(d.one(f"SELECT SUM(l.ExtendedStandardCost) FROM GoodsReceiptLine l JOIN PurchaseOrderLine p ON p.POLineID = "
                              f"l.POLineID JOIN PurchaseRequisition r ON r.RequisitionID = p.RequisitionID WHERE {CHANNEL} = 'Shortfall'"))
    claim(abs(short_receipts - sum(y["short"][1] for y in by_year)) < 0.01, "every shortfall receipt is a materials receipt of the window")
    # Approvals.
    approvers = d.q(f"SELECT {CHANNEL}, r.ApprovedByEmployeeID, e.JobTitle, COUNT(*), SUM(r.RequestedByEmployeeID = "
                    f"r.ApprovedByEmployeeID) FROM PurchaseRequisition r LEFT JOIN Employee e ON e.EmployeeID = "
                    f"r.ApprovedByEmployeeID GROUP BY 1, 2, 3 ORDER BY 1, 4 DESC")
    short_app = [r for r in approvers if r[0] == "Shortfall"]
    claim(len(short_app) == 1 and short_app[0][1] is not None, "one employee approved every shortfall requisition")
    approver, approver_title, n_short, self_requested = short_app[0][1], short_app[0][2], short_app[0][3], short_app[0][4]
    requesters = d.q("SELECT e.JobTitle, c.CostCenterName, COUNT(*) FROM PurchaseRequisition r JOIN Employee e ON e.EmployeeID = "
                     "r.RequestedByEmployeeID LEFT JOIN CostCenter c ON c.CostCenterID = e.CostCenterID WHERE r.Justification "
                     "LIKE 'WO-COMPONENT-SHORTFALL%' AND r.RequestedByEmployeeID <> ? GROUP BY 1, 2 ORDER BY 3 DESC", approver)
    claim(all(r[1] == "Manufacturing" for r in requesters), "production staff requested the rest")
    claim(sum(r[2] for r in requesters[:3]) > 0.9 * sum(r[2] for r in requesters),
          "the three titles listed made nearly all of the other shortfall requisitions")
    plan_app = {r[2]: r[3] for r in approvers if r[0] == "Supply plan"}
    claim(set(plan_app) <= {"Chief Financial Officer", None}, "the CFO approved every supply-plan requisition with an approver")
    other_app = [(SHORT_TITLES.get(r[2], r[2]), r[3]) for r in approvers if r[0] == "Other"]
    claim(all(r[2] is not None for r in approvers if r[0] == "Other"), "every capital request has an approver")
    # What-if.
    ttm = issues[d.C]
    materials = balance(d, ["1045"], year_end(d.C))
    whatif = []
    for days in TARGETS:
        allowed = ttm / 365 * days
        whatif.append(dict(days=days, allowed=xr(allowed), excess=xr(materials - allowed), months=xr((materials - allowed) / (ttm / 12), 2)))
    fall = -bridge(d, d.C)["cash"]
    claim(fall > 0 and 9 <= whatif[-1]["excess"] / fall <= 11, "even at 90 days the excess is about ten times the year's fall in cash")
    fg = balance(d, ["1040"], year_end(d.C))
    dr, cr = flow(d, ["1040"], f"{d.C}-01-01", year_end(d.C), "Shipment")
    never = unordered(d)
    claim(all(r[0] == "Approved" and r[1] == "Shortfall" for r in never), "the unordered requisitions are approved shortfall requisitions")
    open_lines = {bool(m): (n, v) for m, n, v in d.q(
        f"WITH rec AS (SELECT l.POLineID, SUM(l.QuantityReceived) q FROM GoodsReceiptLine l JOIN GoodsReceipt g ON g.GoodsReceiptID = "
        f"l.GoodsReceiptID WHERE g.ReceiptDate <= ?1 GROUP BY 1) SELECT i.ItemGroup IN ({marks}), COUNT(*), "
        f"SUM((p.Quantity - COALESCE(rec.q, 0)) * p.UnitCost) FROM PurchaseOrderLine p JOIN PurchaseOrder o "
        f"ON o.PurchaseOrderID = p.PurchaseOrderID JOIN Item i ON i.ItemID = p.ItemID LEFT JOIN rec ON rec.POLineID = p.POLineID "
        f"WHERE o.OrderDate <= ?1 AND p.Quantity - COALESCE(rec.q, 0) > 0.0001 GROUP BY 1", year_end(d.C), *MATERIALS)}
    claim(policies(d)["ends"] == [year_end(d.C)], f"every inventory policy ends {d.C}-12-31")
    late = d.q("SELECT substr(r.RequestDate, 1, 4), COUNT(*), SUM(r.Quantity * r.EstimatedUnitCost) FROM PurchaseRequisition r "
               "JOIN WorkOrder w ON w.WorkOrderID = CAST(substr(r.Justification, instr(r.Justification, 'WO=') + 3, "
               "instr(r.Justification, ' | ITEM') - instr(r.Justification, 'WO=') - 3) AS INTEGER) "
               "WHERE r.Justification LIKE 'WO-COMPONENT-SHORTFALL%' AND r.RequestDate > w.DueDate GROUP BY 1 ORDER BY 1")
    claim([int(r[0]) for r in late] == d.years, "the late requisitions are counted for every year of the window")
    return dict(by_year=by_year, raw_issued=xr(groups.get("Raw Materials", 0.0)), pack_issued=xr(groups.get("Packaging", 0.0)),
                build=build, share=share, top_items=top_items, packaging=packaging, opening_materials=opening_materials,
                short_counts=[n for _, n, _ in yearly], short_values=[xr(v) for _, _, v in yearly], pairs=len(pairs), repeated=len(repeated),
                in_repeated=sum(p[1] for p in repeated), most=most, wo=wo[0], item=item_code, first_request=tp[4],
                last_request=tp[5], due=wo[1], completed=wo[2], matched=len(matched), unmatched=len(pairs) - len(matched),
                units=xr(sum(p[2] for p in pairs), 1), estimated=xr(sum(p[3] for p in pairs)),
                units_issued=xr(sum(issued[p[0]][0] for p in matched), 1), issued_cost=xr(sum(issued[p[0]][1] for p in matched)),
                short_receipts=short_receipts, n_years=word(len(d.years)), n_short=n_short, approver=approver,
                approver_title=approver_title, self_requested=self_requested,
                requester_titles=[r[0] + "s" for r in requesters[:3]], cfo_plan=plan_app.get("Chief Financial Officer", 0),
                no_plan=plan_app.get(None, 0), n_other=word(sum(n for _, n in other_app)), other_app=other_app,
                ttm=xr(ttm), whatif=whatif, fg_target=xr((cr - dr) / 365 * FG_TARGET), fg=xr(fg), n_never=len(never),
                never_value=xr(sum(r[3] for r in never)), open_lines=sum(v[0] for v in open_lines.values()),
                open_value=xr(sum(v[1] for v in open_lines.values())), open_materials=xr(open_lines.get(True, (0, 0.0))[1]),
                late=[(n, xr(v)) for _, n, v in late])


# --- Requirement 5 -------------------------------------------------------------------------------

@note("case4.r5", CASE)
def r5(d, claim):
    asof = year_end(d.C)
    roll = {}
    for n, order in ROLL.items():
        parts = defaultdict(float)
        for src, day, close, op, dr, cr, k in ledger(d).get(n, ()):
            if day <= asof and not close:
                parts[src] += dr - cr
        claim(set(parts) == set(order), f"account {n}'s balance comes only from {', '.join(order)}")
        roll[n] = dict(parts={s: xr(parts.get(s, 0.0)) for s in order}, total=xr(sum(parts.values())))
    entry = opening_entry(d)
    capital = capital_invoices(d, asof)
    claim(len(capital) == 2 and all(c["paid"] == 0 for c in capital), "two note-financed invoices, never paid")
    open_ap_line = -opening_line(d, "2010")
    claim(abs(roll["2010"]["parts"]["JournalEntry"] - (-open_ap_line + sum(c["amount"] for c in capital))) < 0.01,
          "the 2010 journal entries are the opening line plus the reclasses to notes")
    # Receivables.
    ar = open_receivables(d, asof)
    pos, neg = [b for _, b in ar if b > 0], [(i, b) for i, b in ar if b < 0]
    open_ar = xr(sum(pos))
    opening_ar = xr(opening_line(d, "1020"))
    claim(abs(roll["1020"]["total"] - open_ar - opening_ar) < 0.01, "the receivables difference is the opening line")
    ids = ",".join(str(i) for i, _ in neg) or "NULL"
    a2060 = d.account("2060")
    memos = d.q(f"SELECT c.CreditMemoID, c.OriginalSalesInvoiceID, c.GrandTotal, (SELECT COALESCE(SUM(g.Credit), 0) FROM GLEntry g "
                f"WHERE g.SourceDocumentType = 'CreditMemo' AND g.SourceDocumentID = c.CreditMemoID AND g.AccountID = {a2060}), "
                f"(SELECT COALESCE(SUM(r.Amount), 0) FROM CustomerRefund r WHERE r.CreditMemoID = c.CreditMemoID AND r.RefundDate <= ?) "
                f"FROM CreditMemo c WHERE c.OriginalSalesInvoiceID IN ({ids}) AND c.CreditMemoDate <= ?", asof, asof)
    to_2060 = defaultdict(float)
    for m in memos:
        to_2060[m[1]] += m[3]
    claim(all(to_2060[i] + 0.005 >= -b for i, b in neg), "the negative balances are credit memos credited to 2060")
    applied = dict(d.q(f"SELECT SalesInvoiceID, SUM(AppliedAmount) FROM CashReceiptApplication WHERE SalesInvoiceID IN ({ids}) "
                       f"AND ApplicationDate <= ? GROUP BY 1", asof))
    claim(all(applied.get(i, 0) > 0 for i, _ in neg), "the negative balances are on paid invoices")
    pending = sum(m[3] - m[4] for m in memos)
    claim(abs(pending - balance(d, ["2060"], asof) * -1) < 0.01 and pending < 0.05 * sum(m[3] for m in memos),
          "the credits to 2060 were refunded, except the few still in 2060 at the year-end")
    rebuilt = []
    for y in d.years[:-1]:
        diff = xr(balance(d, ["1020"], year_end(y)) - sum(b for _, b in open_receivables(d, year_end(y)) if b > 0))
        cutoff = sum(i["total"] for i in cross_year(d, y))
        claim(abs(diff - (opening_ar - cutoff)) < 0.01, f"the {y} rebuild differs by the opening line less the cutoff invoices")
        rebuilt.append(diff)
    # Payables.
    ap = d.q("SELECT pi.PurchaseInvoiceID, pi.GrandTotal - COALESCE((SELECT SUM(p.Amount) FROM DisbursementPayment p "
             "WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID AND p.PaymentDate <= ?1), 0), pi.DueDate FROM PurchaseInvoice pi "
             "WHERE pi.ReceivedDate <= ?1", asof)
    open_ap = [(i, xr(b), due) for i, b, due in ap if xr(b) > 0]
    note_ids = {c["id"] for c in capital}
    ap_total = xr(sum(b for _, b, _ in open_ap))
    ap_diff = xr(-roll["2010"]["total"] - ap_total)
    claim(abs(ap_diff - (open_ap_line - sum(c["amount"] for c in capital))) < 0.01,
          "the payables difference is the opening payables less the note invoices")
    claim(note_ids <= {i for i, _, _ in open_ap}, "the subledger still shows the note invoices open")
    claim(all(c["due"] < asof for c in capital), "the note invoices are past due")
    past_due = xr(sum(b for _, b, due in open_ap if due < asof))
    past_due_x = xr(sum(b for i, b, due in open_ap if due < asof and i not in note_ids))
    total_x = xr(sum(b for i, b, _ in open_ap if i not in note_ids))
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = g.SourceDocumentID "
                "WHERE g.SourceDocumentType = 'PurchaseInvoice' AND g.PostingDate <> pi.ReceivedDate") == 0,
          "the ledger posts supplier invoices on their ReceivedDate")
    crossing = {y: d.q("SELECT InvoiceNumber, GrandTotal FROM PurchaseInvoice WHERE InvoiceDate <= ? AND ReceivedDate > ?",
                       year_end(y), year_end(y)) for y in d.years}
    claim([y for y, v in crossing.items() if v] == [d.P] and len(crossing[d.P]) == 1,
          f"on InvoiceDate only the {d.P} year-end differs, by one invoice")
    asv = crossing[d.P][0] if crossing[d.P] else ("?", 0.0)
    # Billing by invoice date less the ledger.
    billing = []
    for y in d.years:
        gl = flow(d, ["1020"], f"{y}-01-01", year_end(y), "SalesInvoice")[0]
        docs = d.one("SELECT COALESCE(SUM(GrandTotal), 0) FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) = ?", str(y))
        billing.append(xr(docs - gl))
    out_f, out_p = cross_year(d, d.F), cross_year(d, d.P)
    claim(not cross_year(d, d.C) and d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate < ?", f"{d.F}-01-01") == 0,
          "only invoices of the first two years cross into the next")
    claim(abs(billing[0] - sum(i["total"] for i in out_f)) < 0.01 and abs(billing[-1] + sum(i["total"] for i in out_p)) < 0.01
          and abs(billing[1] - (sum(i["total"] for i in out_p) - sum(i["total"] for i in out_f))) < 0.01,
          "the billing differences are the invoices posted in the next year")
    claim(out_f and out_p and consecutive(out_f) and consecutive(out_p), "the crossing invoices are consecutive numbers")
    claim(len({i["posted"] for i in out_f}) == 1 and len({i["posted"] for i in out_p}) == 1, "each group posted on one date")
    shipped_in_year = [i for i in out_f + out_p if i["shipped"][:4] == i["dated"][:4]]
    claim(len(shipped_in_year) == 1 and shipped_in_year[0] in out_p, f"only one of them shipped in its invoice year, in {d.P}")
    claim(all(i["shipped"][:4] == i["posted"][:4] for i in out_f + out_p if i not in shipped_in_year),
          "the others shipped in the year they were posted, so their dates are wrong, not the ledger")
    f_months = sorted({int(i["dated"][5:7]) for i in out_f})
    # Sales tax.
    tax_rows = {src: (dr, cr) for src, dr, cr in d.q("SELECT g.SourceDocumentType, SUM(g.Debit), SUM(g.Credit) FROM GLEntry g "
                                                     "WHERE g.AccountID = ? GROUP BY 1", d.account("2050"))}
    claim(set(tax_rows) == {"SalesInvoice", "CreditMemo"} and tax_rows["SalesInvoice"][0] == 0 and tax_rows["CreditMemo"][1] == 0,
          "2050 holds only SalesInvoice credits and CreditMemo debits: no payment and no journal entry")
    tax = []
    for y in d.years:
        gl = flow(d, ["2050"], f"{y}-01-01", year_end(y), "SalesInvoice")[1]
        docs = d.one("SELECT SUM(si.TaxAmount) FROM SalesInvoice si WHERE si.SalesInvoiceID IN (SELECT g.SourceDocumentID FROM GLEntry g "
                     "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.AccountID = ? AND g.FiscalYear = ?)", d.account("2050"), y)
        claim(abs(gl - docs) < 0.01, f"the {y} sales tax credits equal the invoices' TaxAmount")
        tax.append(xr(gl))
    thru = data_through(d)
    after_rows, after_amount = d.q("SELECT COUNT(*), SUM(Debit) FROM GLEntry WHERE PostingDate > ?", thru)[0]
    claim(all(abs(sum(bridge(d, y)[k] for k in STEPS) - bridge(d, y)["cash"]) < 0.01 for y in (d.P, d.C)),
          f"the bridge equals the change in cash in {d.P} and {d.C}")
    claim(thru < f"{d.N}-03-31", f"every measure is blank in {d.N}")
    return dict(roll=roll, opening_ap=xr(open_ap_line), capital=capital, n_ar=len(pos), open_ar=open_ar, n_neg=len(neg),
                neg=xr(sum(b for _, b in neg)), ar_diff=xr(roll["1020"]["total"] - open_ar), entry=entry, rebuilt=rebuilt,
                n_ap=len(open_ap), ap_total=ap_total, ap_diff=ap_diff, notes_total=xr(sum(c["amount"] for c in capital)),
                past_due=past_due, past_due_x=past_due_x, total_x=total_x, past_due_share=past_due_x / total_x,
                asv=dict(number=asv[0], total=asv[1]), billing=billing,
                out_f=dict(range=number_range(out_f), first=MONTHS[f_months[0] - 1], last=MONTHS[f_months[-1] - 1],
                           posted=out_f[0]["posted"]) if out_f else {},
                out_p=dict(range=number_range(out_p), posted=out_p[0]["posted"]) if out_p else {},
                shipped=shipped_in_year[0]["number"] if shipped_in_year else "?", tax=tax, opening_ar=opening_ar,
                tax_balance=xr(-balance(d, ["2050"], asof)), current_portion=xr(d.one(
                    "SELECT SUM(PrincipalAmount) FROM DebtScheduleLine WHERE substr(PaymentDate, 1, 4) = ?", str(d.N))),
                after_amount=xr(after_amount), after_rows=after_rows, accrual=processed(d)["accrual"])


# --- Requirement 6 -------------------------------------------------------------------------------

@note("case4.r6", CASE)
def r6(d, claim):
    b = bridge(d, d.C)
    claim(b["net_income"] > 0 and b["inventories"] < 0 and -b["inventories"] > b["net_income"],
          "the profit was real but went into inventories")
    first, last = quarter(d, year_end(d.P)), quarter(d, year_end(d.C))
    claim(last["mat_balance"] - first["mat_balance"] > -b["inventories"] / 2, "materials above all")
    claim(b["sales_tax"] > 0 and b["payables"] > 0, "unremitted sales tax and growing payables held cash up")
    claim(balance(d, ["1010", "2050"], year_end(d.C)) < balance(d, ["1010"], year_end(d.C)),
          "the cash on the balance sheet overstates what the company can use")
    claim(d.one("SELECT COUNT(*) FROM (SELECT Justification FROM PurchaseRequisition WHERE Justification LIKE "
                "'WO-COMPONENT-SHORTFALL%' GROUP BY 1 HAVING COUNT(*) > 1)") > 0, "requisitions repeated for one work order and item")
    claim(policies(d)["ends"] == [year_end(d.C)], f"the policies ended with {d.C}")
    claim(last["mat_balance"] > last["issues"], "the materials on hand exceed a year of issues")
    return dict(n_never=len(unordered(d)))
