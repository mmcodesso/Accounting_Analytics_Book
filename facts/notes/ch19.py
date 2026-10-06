"""Chapter 19's instructor notes (auditing the customer credits cycle): the values each note states, and the claims
its wording makes.

The case is set in d.N, after fiscal d.C has closed; the analytics and the tests of controls cover the whole window,
and the conclusions on controls are drawn for d.C. Every value is the SQL twin of the case's queries
(scripts/verify/twins/ch19_twins.py): documents are assigned to fiscal years by their own dates (the credit memo's
CreditMemoDate, the refund's RefundDate) and ledger postings by PostingDate. The control tests follow the case's
definitions: a credit or refund above authority exceeds the approver's MaxApprovalAmount; the credit approver handled
cash if they applied a receipt to the credited invoice; a refund precedes the customer's payment if its date is before
the last application on the credited invoice; a customer is past due on the refund date if an invoice dated by then,
less the applications and credits dated by then, is still open with its DueDate before the refund date. Materiality is
5% of the income before income taxes the ledger records for d.C (the chart has no income tax account), and the
sampling statistics come from the binomial (beta) and hypergeometric distributions, as the case's workbook computes them.

Rounding: a clawback's amount is base x rate rounded half up from the exact product, and a credit line's LineTotal is
SQLite's ROUND(Q x P x (1 - D), 2) except on a few exact half-cent products, rounded the other way. Where SQLite's ROUND,
in binary floating point, and the stored amount part on a half-cent, the notes name the documents rather than call them
errors. Returned goods go back to inventory at standard cost, except return lines of less than one unit (a whole
shipment line), which are costed at the quantity times the shipment line's extended cost, below standard.

Requirement 7's timeline of the largest refund is built from the data, step by step in date order, with the evidence its
facts call for. Flags kept on purpose (claims the author revisits on each roll): the AnomalyLog planting nothing in the
cycle's tables (Requirement 1), and the expectation of returns calling for investigation (Requirement 3).
"""

from __future__ import annotations

import statistics as st
from collections import Counter, defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from scipy.stats import beta, hypergeom

from notes import note
from notes.ch08 import abbreviated
from notes.ch16 import entries, orders, register, registers

CHAPTER = "chapters/19-customer-credits-audit/chapter.qmd"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
# The case's parameters (Requirements 3 and 6): materiality 5% of income before income taxes, performance materiality
# 75% of it, clearly trivial 5% of it; key items are refunds of 5,000 or more and refunds to a customer whose refunds
# over the window exceed 10,000; the expected sampling parameters are 95% confidence, 5% tolerable, 0% expected, so
# n = 59 (tbl-19-03).
MATERIALITY, PERFORMANCE, TRIVIAL = 0.05, 0.75, 0.05
KEY_AMOUNT, KEY_CUSTOMER = 5000, 10000
CONFIDENCE, TOLERABLE, SAMPLE = 0.95, 0.05, 59
TAIL = 0.05                 # the plausible draws of Requirement 6: the tightest range with each tail below 5%
REVENUE = ("4010", "4020", "4030", "4040", "4080")     # the product and service revenue accounts (Requirement 3)
SOURCES = ("SalesReturn", "CreditMemo", "CustomerRefund", "SalesCommissionAdjustment", "CashReceipt",
           "CashReceiptApplication")
# The cycle's tables, for the AnomalyLog test.
CYCLE_TABLES = {"SalesReturn", "SalesReturnLine", "CreditMemo", "CreditMemoLine", "CustomerRefund",
                "SalesCommissionAdjustment", "SalesCommissionAccrual", "SalesCommissionPayment",
                "SalesCommissionPaymentLine", "SalesCommissionRate", "CashReceipt", "CashReceiptApplication"}
TOP_FAMILIES = 5
HALF_CENT = Decimal("0.005")
CS, CSR, CSM = "Customer Service", "Customer Service Representative", "Customer Service Manager"


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def D(day: str) -> date:
    return date.fromisoformat(day[:10])


def md(day: str) -> str:
    """'2025-04-30' -> '04-30', as the timeline writes dates after the first."""
    return day[5:10]


def year_end(year: int) -> str:
    return f"{year}-12-31"


def plural(title: str) -> str:
    return title + "s"


def r2(x: float) -> float:
    return round(x + 0.0, 2)


def money2(x: float) -> str:
    return f"{x:,.2f}"


def method_word(method: str) -> str:
    """A payment method in running text: 'Wire Transfer' -> 'wire', 'Credit Card' -> 'credit card', 'ACH' -> 'ACH'."""
    return "wire" if method == "Wire Transfer" else method if method.isupper() else method.lower()


# --- the cycle, loaded once ------------------------------------------------------------------------

@lru_cache(maxsize=None)
def cycle(d) -> SimpleNamespace:
    q = d.q
    emp = {r[0]: dict(id=r[0], title=r[1], limit=r[2] or 0, hire=r[3], term=r[4], cc=r[5]) for r in q(
        "SELECT e.EmployeeID, e.JobTitle, e.MaxApprovalAmount, e.HireDate, e.TerminationDate, c.CostCenterName "
        "FROM Employee e LEFT JOIN CostCenter c ON c.CostCenterID = e.CostCenterID")}
    holders = Counter(e["title"] for e in emp.values())
    inv = {r[0]: dict(id=r[0], num=r[1], cust=r[2], date=r[3], due=r[4], gt=r[5], freight=r[6]) for r in q(
        "SELECT SalesInvoiceID, InvoiceNumber, CustomerID, InvoiceDate, DueDate, GrandTotal, FreightAmount FROM SalesInvoice")}
    cm = {r[0]: dict(id=r[0], num=r[1], date=r[2], ret=r[3], cust=r[4], inv=r[5], sub=r[6], freight=r[7], tax=r[8],
                     gt=r[9], status=r[10], appr=r[11], adate=r[12]) for r in q(
        "SELECT CreditMemoID, CreditMemoNumber, CreditMemoDate, SalesReturnID, CustomerID, OriginalSalesInvoiceID, SubTotal, "
        "FreightCreditAmount, TaxAmount, GrandTotal, Status, ApprovedByEmployeeID, ApprovedDate FROM CreditMemo ORDER BY CreditMemoID")}
    rf = {r[0]: dict(id=r[0], num=r[1], date=r[2], cust=r[3], cm=r[4], amt=r[5], method=r[6], appr=r[7], cleared=r[8])
          for r in q("SELECT CustomerRefundID, RefundNumber, RefundDate, CustomerID, CreditMemoID, Amount, PaymentMethod, "
                     "ApprovedByEmployeeID, ClearedDate FROM CustomerRefund ORDER BY CustomerRefundID")}
    sr = {r[0]: dict(id=r[0], num=r[1], date=r[2], cust=r[3], recv=r[4], reason=r[5], status=r[6]) for r in q(
        "SELECT SalesReturnID, ReturnNumber, ReturnDate, CustomerID, ReceivedByEmployeeID, ReasonCode, Status FROM SalesReturn "
        "ORDER BY SalesReturnID")}
    rcpt = {r[0]: dict(id=r[0], num=r[1], date=r[2], cust=r[3], inv=r[4], amt=r[5], method=r[6], dep=r[7], rec=r[8])
            for r in q("SELECT CashReceiptID, ReceiptNumber, ReceiptDate, CustomerID, SalesInvoiceID, Amount, PaymentMethod, "
                       "DepositDate, RecordedByEmployeeID FROM CashReceipt")}
    apps = defaultdict(list)          # by invoice: (date, amount, applier, receipt)
    for i, day, amt, e, rid in q("SELECT SalesInvoiceID, ApplicationDate, AppliedAmount, AppliedByEmployeeID, CashReceiptID "
                                 "FROM CashReceiptApplication ORDER BY CashReceiptApplicationID"):
        apps[i].append((day, amt, e, rid))
    cred = defaultdict(list)          # credits by invoice: (date, grand total)
    for m in cm.values():
        cred[m["inv"]].append((m["date"], m["gt"]))
    adj = [dict(num=r[0], date=r[1], cm=r[2], appr=r[3], base=r[4], rate=r[5], amt=r[6], accrual=r[7], line=r[8], id=r[9],
                sql_round=r[10]) for r in q(
        "SELECT AdjustmentNumber, AdjustmentDate, CreditMemoID, ApprovedByEmployeeID, CommissionBaseReductionAmount, "
        "CommissionRatePct, CommissionAdjustmentAmount, SalesCommissionAccrualID, CreditMemoLineID, SalesCommissionAdjustmentID, "
        "ROUND(CommissionBaseReductionAmount * CommissionRatePct, 2) FROM SalesCommissionAdjustment ORDER BY AdjustmentNumber")]
    # the credits' parts posted to receivables and to customer deposits (2060)
    a1020, a2060 = d.account("1020"), d.account("2060")
    parts = defaultdict(lambda: [0.0, 0.0])
    for doc, acc, cr in q("SELECT SourceDocumentID, AccountID, SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'CreditMemo' "
                          "AND AccountID IN (?, ?) AND Credit > 0 GROUP BY 1, 2", a1020, a2060):
        parts[doc][0 if acc == a1020 else 1] += cr
    return SimpleNamespace(emp=emp, holders=holders, inv=inv, cm=cm, rf=rf, sr=sr, rcpt=rcpt, apps=apps, cred=cred,
                           adj=adj, parts=parts)


def title_of(d, e: int) -> str:
    return cycle(d).emp[e]["title"]


def phrase(d, title: str) -> str:
    """'the Warehouse Manager' for a title one employee holds, 'Shipping Clerks' for one several hold."""
    return f"the {title}" if cycle(d).holders[title] == 1 else plural(title)


def bare(d, title: str) -> str:
    """'Accounting Manager' for a title one employee holds, 'Staff Accountants' for one several hold."""
    return title if cycle(d).holders[title] == 1 else plural(title)


def by_title(d, ids, order: str = "count") -> list[tuple[str, int]]:
    """Employees' documents counted by job title: by count (descending), by first appearance, or by name."""
    counts = Counter(title_of(d, e) for e in ids)
    if order == "count":
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if order == "name":
        return sorted(counts.items())
    return list(counts.items())


def year_of(day: str) -> int:
    return int(day[:4])


def per_year(d, items, key, value=None) -> list:
    """Counts (or sums of `value`) of items by the fiscal year of `key`, one per year of the window."""
    out = [0 if value is None else 0.0 for _ in d.years]
    for x in items:
        y = year_of(key(x))
        if y in d.years:
            out[d.years.index(y)] += 1 if value is None else value(x)
    return out


@lru_cache(maxsize=None)
def gl(d) -> dict:
    """The cycle's postings: (source type, account number, fiscal year) -> [debits, credits, debit rows, credit rows]."""
    marks = ",".join("?" * len(SOURCES))
    out = defaultdict(lambda: [0.0, 0.0, 0, 0])
    for src, acct, y, dr, cr, ndr, ncr in d.q(
            f"SELECT g.SourceDocumentType, a.AccountNumber, CAST(substr(g.PostingDate, 1, 4) AS INTEGER), SUM(g.Debit), "
            f"SUM(g.Credit), SUM(g.Debit > 0), SUM(g.Credit > 0) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
            f"WHERE g.SourceDocumentType IN ({marks}) GROUP BY 1, 2, 3", *SOURCES):
        out[(src, str(acct), y)] = [dr, cr, ndr, ncr]
    return out


def gl_year(d, src: str, acct: str, y: int, side: str) -> float:
    row = gl(d).get((src, acct, y), [0.0, 0.0, 0, 0])
    return row[0] if side == "Dr" else row[1]


def gl_total(d, src: str, acct: str, side: str) -> tuple[float, int]:
    """The total and the rows of one side of a source type's postings to an account, over all years."""
    amount = rows = 0
    for (s, a, y), (dr, cr, ndr, ncr) in gl(d).items():
        if s == src and a == acct:
            amount += dr if side == "Dr" else cr
            rows += ndr if side == "Dr" else ncr
    return amount, rows


def sides(d, src: str) -> set[tuple[str, str]]:
    out = set()
    for (s, a, y), (dr, cr, ndr, ncr) in gl(d).items():
        if s == src:
            if ndr:
                out.add(("Dr", a))
            if ncr:
                out.add(("Cr", a))
    return out


# --- the control tests (Requirement 4) ---------------------------------------------------------------

def paid_by(c, inv: int, day: str) -> float:
    return sum(a[1] for a in c.apps[inv] if a[0] <= day)


def last_payment(c, inv: int) -> str | None:
    return max((a[0] for a in c.apps[inv]), default=None)


@lru_cache(maxsize=None)
def tests(d) -> SimpleNamespace:
    c = cycle(d)
    emp, cm, rf = c.emp, c.cm, c.rf
    cm_above = [m for m in cm.values() if m["gt"] > emp[m["appr"]]["limit"]]
    cash_credit = [m for m in cm.values() if any(a[2] == m["appr"] for a in c.apps[m["inv"]])]
    cc_early = [m for m in cash_credit if any(a[2] == m["appr"] and a[0] <= m["date"] for a in c.apps[m["inv"]])]
    cc_rec = [m for m in cm.values() if any(a[2] == m["appr"] or c.rcpt[a[3]]["rec"] == m["appr"] for a in c.apps[m["inv"]])]
    rf_above = [r for r in rf.values() if r["amt"] > emp[r["appr"]]["limit"]]
    before = [r for r in rf.values() if (last_payment(c, cm[r["cm"]]["inv"]) or "") > r["date"]]
    nothing = [r for r in rf.values() if not any(a[0] <= r["date"] for a in c.apps[cm[r["cm"]]["inv"]])]
    by_cust = defaultdict(list)
    for i, v in c.inv.items():
        by_cust[v["cust"]].append(i)

    def past_due(cust: int, asof: str) -> float:
        total = 0.0
        for i in by_cust[cust]:
            v = c.inv[i]
            if v["date"] > asof:
                continue
            bal = v["gt"] - paid_by(c, i, asof) - sum(a for day, a in c.cred[i] if day <= asof)
            if bal > 0.005 and v["due"] < asof:
                total += bal
        return total
    pdue = {k: past_due(r["cust"], r["date"]) for k, r in rf.items()}
    methods = {k: {c.rcpt[a[3]]["method"] for a in c.apps[cm[r["cm"]]["inv"]]} for k, r in rf.items()}
    mism = [r for k, r in rf.items() if r["method"] not in methods[k]]
    above_ids = {r["id"] for r in rf_above}
    cm_above_ids = {m["id"] for m in cm_above}
    mism_ids = {r["id"] for r in mism}
    before_ids = {r["id"] for r in before}
    flags = {k: [k in above_ids, r["cm"] in cm_above_ids, k in mism_ids, k in before_ids, pdue[k] >= r["amt"]]
             for k, r in rf.items()}
    score = {k: sum(f) for k, f in flags.items()}
    return SimpleNamespace(cm_above=cm_above, cash_credit=cash_credit, cc_early=cc_early, cc_rec=cc_rec, rf_above=rf_above,
                           before=before, nothing=nothing, pdue=pdue, methods=methods, mism=mism, flags=flags, score=score)


def amount(items, key="gt") -> float:
    return r2(sum(x[key] for x in items))


def in_year(items, y: int, key="date") -> list:
    return [x for x in items if year_of(x[key]) == y]


# --- shared figures --------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def income(d) -> float:
    """Income before income taxes as the ledger records it for d.C: revenue less expenses, the closes left out."""
    return d.one(f"SELECT SUM(g.Credit - g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                 f"WHERE a.AccountType IN ('Revenue', 'Expense') AND g.FiscalYear = ? AND {d.no_closes()}", d.C)


def materiality(d) -> dict:
    m = income(d) * MATERIALITY
    return dict(income=income(d), mat=m, perf=m * PERFORMANCE, trivial=m * TRIVIAL)


@lru_cache(maxsize=None)
def revenue(d) -> list[float]:
    """SalesInvoice postings to the product and service revenue accounts, credits less debits, by fiscal year."""
    marks = ",".join("?" * len(REVENUE))
    rows = dict(d.q(f"SELECT CAST(substr(g.PostingDate, 1, 4) AS INTEGER), SUM(g.Credit - g.Debit) FROM GLEntry g "
                    f"JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber IN ({marks}) "
                    f"AND g.SourceDocumentType = 'SalesInvoice' GROUP BY 1", *REVENUE))
    return [rows.get(y, 0.0) for y in d.years]


@lru_cache(maxsize=None)
def returns_4060(d) -> list[float]:
    """The debits to 4060 by fiscal year, the closes left out."""
    rows = dict(d.q(f"SELECT CAST(substr(PostingDate, 1, 4) AS INTEGER), SUM(Debit) FROM GLEntry WHERE AccountID = ? "
                    f"AND {d.no_closes()} GROUP BY 1", d.account("4060")))
    return [rows.get(y, 0.0) for y in d.years]


def expectation(d) -> dict:
    rev, ret = revenue(d), returns_4060(d)
    rates = [r / v for r, v in zip(ret, rev)]
    exp = rates[-2] * rev[-1]
    exp_f = rates[0] * rev[-1]
    return dict(revenue=rev, rates=rates, actual=ret[-1], exp=exp, diff=ret[-1] - exp, diff_pct=ret[-1] / exp - 1,
                exp_f=exp_f, f_pct=ret[-1] / exp_f - 1)


@lru_cache(maxsize=None)
def subtotal_equals_4060(d) -> list[bool]:
    c = cycle(d)
    return [abs(sum(m["sub"] for m in in_year(c.cm.values(), y)) - gl_year(d, "CreditMemo", "4060", y, "Dr")) < 0.005
            for y in d.years]


def balance_2060(d, y: int) -> float:
    return d.one("SELECT COALESCE(SUM(Credit - Debit), 0) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ?",
                 d.account("2060"), year_end(y))


def open_2060(d, y: int) -> list[dict]:
    """The credits whose part posted to 2060 by a year-end is not yet refunded by it."""
    c = cycle(d)
    left = defaultdict(float)
    for doc, amt in d.q("SELECT SourceDocumentID, SUM(Credit) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ? "
                        "AND SourceDocumentType = 'CreditMemo' GROUP BY 1", d.account("2060"), year_end(y)):
        left[doc] += amt
    for r in c.rf.values():
        if r["date"] <= year_end(y):
            left[r["cm"]] -= r["amt"]
    return [dict(id=k, number=c.cm[k]["num"], amount=r2(v), status=c.cm[k]["status"])
            for k, v in sorted(left.items(), key=lambda kv: c.cm[kv[0]]["num"]) if v > 0.005]


def reconciles(d) -> bool:
    """Requirement 2's reconciliations hold in every year, to the cent."""
    c = cycle(d)
    ok = all(subtotal_equals_4060(d))
    for y in d.years:
        ms = in_year(c.cm.values(), y)
        ok &= abs(sum(m["freight"] for m in ms) - gl_year(d, "CreditMemo", "4050", y, "Dr")) < 0.005
        ok &= abs(sum(m["tax"] for m in ms) - gl_year(d, "CreditMemo", "2050", y, "Dr")) < 0.005
        ok &= abs(sum(m["gt"] for m in ms) - gl_year(d, "CreditMemo", "1020", y, "Cr")
                  - gl_year(d, "CreditMemo", "2060", y, "Cr")) < 0.005
        rs = in_year(c.rf.values(), y)
        ok &= abs(sum(r["amt"] for r in rs) - gl_year(d, "CustomerRefund", "1010", y, "Cr")) < 0.005
        ok &= abs(sum(r["amt"] for r in rs) - gl_year(d, "CustomerRefund", "2060", y, "Dr")) < 0.005
        cb = sum(a["amt"] for a in c.adj if year_of(a["date"]) == y)
        ok &= abs(cb - gl_year(d, "SalesCommissionAdjustment", "2034", y, "Dr")) < 0.005
        ok &= abs(cb - gl_year(d, "SalesCommissionAdjustment", "6290", y, "Cr")) < 0.005
        rc = sum(r["amt"] for r in c.rcpt.values() if year_of(r["date"]) == y)
        ap = sum(a[1] for v in c.apps.values() for a in v if year_of(a[0]) == y)
        ok &= abs(rc - ap) < 0.005 and abs(rc - gl_year(d, "CashReceipt", "1010", y, "Dr")) < 0.005
        ok &= abs(ap - gl_year(d, "CashReceiptApplication", "1020", y, "Cr")) < 0.005
    return bool(ok)


@lru_cache(maxsize=None)
def credit_lines(d) -> list[dict]:
    """Each credit line traced to its return line, shipment line, and invoice line."""
    return [dict(id=r[0], qty=r[1], price=r[2], disc=r[3], total=r[4], returned=r[5], shipped=r[6], inv_price=r[7],
                 inv_disc=r[8], inv=r[9], credit_inv=r[10], date=r[11], group=r[12], family=r[13], reason=r[14],
                 ship_date=r[15], delivered=r[16], carrier=r[17], warehouse=r[18], return_date=r[19], segment=r[20],
                 code=r[21])
            for r in d.q("SELECT l.CreditMemoLineID, l.Quantity, l.UnitPrice, l.Discount, l.LineTotal, srl.QuantityReturned, "
                         "sl.QuantityShipped, sil.UnitPrice, sil.Discount, sil.SalesInvoiceID, cm.OriginalSalesInvoiceID, "
                         "cm.CreditMemoDate, i.ItemGroup, substr(i.ItemCode, 5, 3), sr.ReasonCode, s.ShipmentDate, s.DeliveryDate, "
                         "s.ShippedBy, s.WarehouseID, sr.ReturnDate, cu.CustomerSegment, i.ItemCode "
                         "FROM CreditMemoLine l JOIN CreditMemo cm ON cm.CreditMemoID = l.CreditMemoID "
                         "JOIN Item i ON i.ItemID = l.ItemID JOIN SalesReturnLine srl ON srl.SalesReturnLineID = l.SalesReturnLineID "
                         "JOIN SalesReturn sr ON sr.SalesReturnID = srl.SalesReturnID "
                         "JOIN ShipmentLine sl ON sl.ShipmentLineID = srl.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                         "JOIN Customer cu ON cu.CustomerID = cm.CustomerID "
                         "LEFT JOIN SalesInvoiceLine sil ON sil.ShipmentLineID = sl.ShipmentLineID ORDER BY l.CreditMemoLineID")]


def tax_rate(d) -> float:
    """The sales tax rate the credits carry, read from their totals (to a tenth of a percent)."""
    c = cycle(d)
    return round(sum(m["tax"] for m in c.cm.values()) / sum(m["sub"] + m["freight"] for m in c.cm.values()), 3)


@lru_cache(maxsize=None)
def substantive(d) -> dict:
    """Requirement 7's recomputation of the credits."""
    c = cycle(d)
    lines = credit_lines(d)
    n_lines = d.one("SELECT COUNT(*) FROM CreditMemoLine")
    traced = [l for l in lines if l["inv"] is not None and l["inv"] == l["credit_inv"]]
    over = [l for l in lines if l["qty"] > l["shipped"] + 1e-9]
    price_off = [l for l in lines if l["inv_price"] is None or abs(l["price"] - l["inv_price"]) > 0.004
                 or abs(l["disc"] - l["inv_disc"]) > 1e-9]
    # LineTotal against SQLite's ROUND(Q x P x (1 - D), 2): the lines that differ are rounding, not errors, when the exact
    # product is a half-cent and LineTotal is its other rounding (binary floating point decides which way ROUND goes)
    def exact(l) -> Decimal:
        return Decimal(repr(l["qty"])) * Decimal(repr(l["price"])) * (1 - Decimal(repr(l["disc"])))
    by_id = {l["id"]: l for l in lines}
    off = [by_id.get(i) for (i,) in d.q("SELECT CreditMemoLineID FROM CreditMemoLine WHERE ABS(LineTotal - ROUND(Quantity * "
                                        "UnitPrice * (1 - Discount), 2)) > 0.004 ORDER BY 1")]
    half = [l for l in off if l is not None and abs(abs(Decimal(repr(l["total"])) - exact(l)) - HALF_CENT) < Decimal("1e-9")]
    total_off = [l for l in off if l not in half]          # differences that are not a half-cent rounding
    twice = d.one("SELECT COUNT(*) FROM (SELECT ShipmentLineID FROM SalesReturnLine GROUP BY 1 HAVING COUNT(*) > 1)")
    distinct_inv = len({m["inv"] for m in c.cm.values()})
    above_invoice = [m for m in c.cm.values() if m["gt"] > c.inv[m["inv"]]["gt"] + 0.005]
    sub_ok = d.one("SELECT COUNT(*) FROM CreditMemo cm WHERE ABS(cm.SubTotal - (SELECT SUM(LineTotal) FROM CreditMemoLine l "
                   "WHERE l.CreditMemoID = cm.CreditMemoID)) < 0.005")
    rate = tax_rate(d)
    tax_ok = [m for m in c.cm.values() if abs(m["tax"] - round((m["sub"] + m["freight"]) * rate, 2)) < 0.006]
    tax_sub_flags = [m for m in c.cm.values() if abs(m["tax"] - round(m["sub"] * rate, 2)) > 0.011]
    with_freight = [m for m in c.cm.values() if m["freight"] > 0.005]
    freight_over = [m for m in c.cm.values() if m["freight"] > c.inv[m["inv"]]["freight"] + 0.005]
    gt_ok = all(abs(m["gt"] - m["sub"] - m["freight"] - m["tax"]) < 0.005 for m in c.cm.values())
    clean = (len(traced) == n_lines == len(lines) and not over and not twice and not price_off and not total_off
             and distinct_inv == len(c.cm) and not above_invoice and sub_ok == len(c.cm) and len(tax_ok) == len(c.cm)
             and not freight_over and gt_ok)
    return dict(lines=n_lines, traced=len(traced), over=len(over), price_off=len(price_off), total_off=total_off, half=half,
                twice=twice, distinct_inv=distinct_inv, above_invoice=len(above_invoice), sub_ok=sub_ok, rate=rate,
                tax_ok=len(tax_ok), tax_sub_flags=tax_sub_flags, with_freight=with_freight, freight_over=len(freight_over),
                gt_ok=gt_ok, clean=clean)


@lru_cache(maxsize=None)
def lapping(d) -> dict:
    """Requirement 7's lapping tests."""
    c = cycle(d)
    other = sum(1 for i, v in c.apps.items() for a in v if c.rcpt[a[3]]["cust"] != c.inv[i]["cust"])
    dep = [(D(r["dep"]) - D(r["date"])).days for r in c.rcpt.values() if r["dep"]]
    no_dep = sum(1 for r in c.rcpt.values() if not r["dep"])
    lag = [(D(a[0]) - max(D(c.rcpt[a[3]]["date"]), D(c.inv[i]["date"]))).days for i, v in c.apps.items() for a in v]
    applied = defaultdict(float)
    for v in c.apps.values():
        for a in v:
            applied[a[3]] += a[1]
    not_full = sum(1 for k, r in c.rcpt.items() if abs(applied[k] - r["amt"]) > 0.005)
    early = [(i, a) for i, v in c.apps.items() for a in v if c.rcpt[a[3]]["date"] < c.inv[i]["date"]]
    clean = other == 0 and not_full == 0 and no_dep == 0 and min(lag) >= 0
    return dict(other=other, dep_lo=min(dep), dep_hi=max(dep), no_dep=no_dep, lag_lo=min(lag), lag_hi=max(lag),
                not_full=not_full, early_receipts=len({a[3] for i, a in early}), early_apps=len(early),
                early_amount=r2(sum(a[1] for i, a in early)), clean=clean)


@lru_cache(maxsize=None)
def clawbacks(d) -> dict:
    """Requirement 4's clawback tests: one per credit line, base and rate, and the amount (the half-cent products that
    SQLite's ROUND rounds the other way)."""
    c = cycle(d)
    lines = {r[0]: r[1] for r in d.q("SELECT CreditMemoLineID, LineTotal FROM CreditMemoLine")}
    acc = {r[0]: r[1] for r in d.q("SELECT SalesCommissionAccrualID, CommissionRatePct FROM SalesCommissionAccrual")}
    per_line = Counter(a["line"] for a in c.adj)
    complete = set(per_line) == set(lines) and all(n == 1 for n in per_line.values())
    base_ok = sum(1 for a in c.adj if abs(a["base"] - lines.get(a["line"], -1)) < 0.005 and abs(a["rate"] - acc.get(a["accrual"], -1)) < 1e-9)
    off = [a for a in c.adj if abs(a["amt"] - a["sql_round"]) > 0.004]
    half = all(abs(a["base"] * a["rate"] * 100 % 1 - 0.5) < 1e-6 and abs(a["amt"] - a["base"] * a["rate"] - 0.005) < 1e-6
               for a in off)
    netted = {r[0]: r[1] for r in d.q("SELECT l.SourceDocumentID, MIN(p.PaymentDate) FROM SalesCommissionPaymentLine l "
                                      "JOIN SalesCommissionPayment p ON p.SalesCommissionPaymentID = l.SalesCommissionPaymentID "
                                      "WHERE l.SourceDocumentType = 'SalesCommissionAdjustment' GROUP BY 1")}
    later = all(netted[a["id"]] >= a["date"] for a in c.adj if a["id"] in netted)
    exact = all(Decimal(repr(a["amt"])) == (Decimal(repr(a["base"])) * Decimal(repr(a["rate"]))).quantize(Decimal("0.01"), ROUND_HALF_UP)
                for a in c.adj)
    same = all(a["date"] == c.cm[a["cm"]]["date"] and a["appr"] == c.cm[a["cm"]]["appr"] for a in c.adj)
    return dict(n=len(c.adj), total=r2(sum(a["amt"] for a in c.adj)), complete=complete, base_ok=base_ok, off=off,
                half=half, exact=exact, netted=len(netted), pending=len(c.adj) - len(netted), later=later, same=same,
                clean=complete and base_ok == len(c.adj) and half and exact and same)


def commission_design(d) -> dict:
    rates = d.q("SELECT ApprovedByEmployeeID, EffectiveEndDate FROM SalesCommissionRate")
    accruals = d.q("SELECT DISTINCT CreatedByEmployeeID FROM SalesCommissionAccrual")
    n_accruals = d.one("SELECT COUNT(*) FROM SalesCommissionAccrual")
    payments = d.q("SELECT ApprovedByEmployeeID FROM SalesCommissionPayment")
    people = {r[0] for r in rates} | {r[0] for r in accruals} | {r[0] for r in payments}
    return dict(rates=len(rates), rate_ends=sorted({r[1] for r in rates}), accruals=n_accruals, payments=len(payments),
                people=people)


def accounting_manager(d) -> int | None:
    ids = [e for e, v in cycle(d).emp.items() if v["title"] == "Accounting Manager"]
    return ids[0] if len(ids) == 1 else None


def largest_refund(d) -> dict:
    c = cycle(d)
    top = max(r["amt"] for r in c.rf.values())
    found = [r for r in c.rf.values() if r["amt"] == top]
    return found[0]


def no_preparer(d) -> bool:
    """Neither CreditMemo nor CustomerRefund has a column for who prepared or created it."""
    cols = [r[1] for t in ("CreditMemo", "CustomerRefund") for r in d.q(f"PRAGMA table_info({t})")]
    return not any(w in col for col in cols for w in ("Prepared", "Created", "Requested", "Entered"))


def anomaly_tables(d) -> set[str] | None:
    """The tables the generator's AnomalyLog plants problems in (read-only), or None without a support workbook."""
    path = Path(d.path).parent / "CharlesRiver_support.xlsx"
    if not path.is_file():
        return None
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        rows = list(wb["AnomalyLog"].iter_rows(values_only=True))
    finally:
        wb.close()
    t = rows[0].index("table_name")
    return {r[t] for r in rows[1:] if r and r[t]}


def warehouse_receipt(d) -> bool:
    """Every return was received by warehouse staff."""
    c = cycle(d)
    return {c.emp[s["recv"]]["cc"] for s in c.sr.values()} == {"Warehouse"}


def no_orphans(d) -> bool:
    checks = [
        "SELECT COUNT(*) FROM SalesReturnLine srl WHERE NOT EXISTS (SELECT 1 FROM ShipmentLine sl WHERE sl.ShipmentLineID = srl.ShipmentLineID)",
        "SELECT COUNT(*) FROM SalesReturnLine srl WHERE NOT EXISTS (SELECT 1 FROM SalesReturn sr WHERE sr.SalesReturnID = srl.SalesReturnID)",
        "SELECT COUNT(*) FROM CreditMemo cm WHERE NOT EXISTS (SELECT 1 FROM SalesReturn sr WHERE sr.SalesReturnID = cm.SalesReturnID)",
        "SELECT COUNT(*) FROM CreditMemo cm WHERE NOT EXISTS (SELECT 1 FROM SalesInvoice si WHERE si.SalesInvoiceID = cm.OriginalSalesInvoiceID)",
        "SELECT COUNT(*) FROM CreditMemoLine l WHERE NOT EXISTS (SELECT 1 FROM SalesReturnLine r WHERE r.SalesReturnLineID = l.SalesReturnLineID)",
        "SELECT COUNT(*) FROM CreditMemoLine l WHERE NOT EXISTS (SELECT 1 FROM CreditMemo cm WHERE cm.CreditMemoID = l.CreditMemoID)",
        "SELECT COUNT(*) FROM SalesReturnLine r WHERE NOT EXISTS (SELECT 1 FROM CreditMemoLine l WHERE l.SalesReturnLineID = r.SalesReturnLineID)",
        "SELECT COUNT(*) FROM SalesReturn sr WHERE NOT EXISTS (SELECT 1 FROM CreditMemo cm WHERE cm.SalesReturnID = sr.SalesReturnID)",
        "SELECT COUNT(*) FROM CustomerRefund r WHERE NOT EXISTS (SELECT 1 FROM CreditMemo cm WHERE cm.CreditMemoID = r.CreditMemoID)",
        "SELECT COUNT(*) FROM CreditMemo cm WHERE cm.Status = 'Refunded' AND NOT EXISTS (SELECT 1 FROM CustomerRefund r WHERE r.CreditMemoID = cm.CreditMemoID)",
        "SELECT COUNT(*) FROM SalesCommissionAdjustment a WHERE NOT EXISTS (SELECT 1 FROM CreditMemoLine l WHERE l.CreditMemoLineID = a.CreditMemoLineID)",
        "SELECT COUNT(*) FROM CreditMemoLine l WHERE NOT EXISTS (SELECT 1 FROM SalesCommissionAdjustment a WHERE a.CreditMemoLineID = l.CreditMemoLineID)",
        "SELECT COUNT(*) FROM SalesCommissionAdjustment a WHERE NOT EXISTS (SELECT 1 FROM SalesCommissionAccrual x WHERE x.SalesCommissionAccrualID = a.SalesCommissionAccrualID)",
        "SELECT COUNT(*) FROM CashReceiptApplication a WHERE NOT EXISTS (SELECT 1 FROM CashReceipt r WHERE r.CashReceiptID = a.CashReceiptID)",
        "SELECT COUNT(*) FROM CashReceiptApplication a WHERE NOT EXISTS (SELECT 1 FROM SalesInvoice si WHERE si.SalesInvoiceID = a.SalesInvoiceID)",
    ]
    for src, table, key in (("SalesReturn", "SalesReturn", "SalesReturnID"), ("CreditMemo", "CreditMemo", "CreditMemoID"),
                            ("CustomerRefund", "CustomerRefund", "CustomerRefundID"),
                            ("SalesCommissionAdjustment", "SalesCommissionAdjustment", "SalesCommissionAdjustmentID"),
                            ("CashReceipt", "CashReceipt", "CashReceiptID"),
                            ("CashReceiptApplication", "CashReceiptApplication", "CashReceiptApplicationID")):
        checks.append(f"SELECT COUNT(*) FROM GLEntry g WHERE g.SourceDocumentType = '{src}' AND NOT EXISTS "
                      f"(SELECT 1 FROM {table} t WHERE t.{key} = g.SourceDocumentID)")
        checks.append(f"SELECT COUNT(*) FROM {table} t WHERE NOT EXISTS (SELECT 1 FROM GLEntry g WHERE "
                      f"g.SourceDocumentType = '{src}' AND g.SourceDocumentID = t.{key})")
    return all(d.one(sql) == 0 for sql in checks)


def numbering(d, table: str, col: str) -> list[tuple[int, int]] | None:
    """Each fiscal year's first and last sequence number, or None if a year has a gap or the numbers do not continue."""
    seqs = defaultdict(list)
    for (n,) in d.q(f"SELECT {col} FROM {table}"):
        prefix, y, s = n.rsplit("-", 2)
        seqs[int(y)].append(int(s))
    out = []
    for y in d.years:
        s = sorted(seqs.get(y, []))
        if not s or s[-1] - s[0] + 1 != len(s) or len(set(s)) != len(s):
            return None
        out.append((s[0], s[-1]))
    if out[0][0] != 1 or any(b[0] != a[1] + 1 for a, b in zip(out, out[1:])) or set(seqs) - set(d.years):
        return None
    return out


def ranges(rs) -> str:
    return ", ".join(f"{a}-{b}" for a, b in rs)


def sampling(d) -> dict:
    """Requirement 6: the key items, the remainder, and the sample statistics."""
    c, t = cycle(d), tests(d)
    by_cust = defaultdict(float)
    for r in c.rf.values():
        by_cust[r["cust"]] += r["amt"]
    key = [r for r in c.rf.values() if r["amt"] >= KEY_AMOUNT or by_cust[r["cust"]] > KEY_CUSTOMER]
    key_ids = {r["id"] for r in key}
    rest = [r for r in c.rf.values() if r["id"] not in key_ids]
    before_ids = {r["id"] for r in t.before}
    dev = [r for r in rest if r["id"] in before_ids]
    hg = hypergeom(len(rest), len(dev), SAMPLE)
    lo = max(k for k in range(SAMPLE + 1) if hg.cdf(k - 1) < TAIL)
    hi = min(k for k in range(SAMPLE + 1) if hg.sf(k) < TAIL)
    mid = round(hg.mean())

    def udl(k):
        return float(beta.ppf(CONFIDENCE, k + 1, SAMPLE - k))
    return dict(key=sorted(key, key=lambda r: r["num"]), key_total=amount(key, "amt"), rest=rest,
                rest_total=amount(rest, "amt"), dev=dev, key_dev=sum(1 for r in key if r["id"] in before_ids),
                share=SAMPLE / len(rest), udl=[udl(k) for k in range(4)], mean=float(hg.mean()), lo=lo, hi=hi, mid=mid,
                cdf_lo=float(hg.cdf(lo - 1)), cdf_hi=float(hg.cdf(hi)), inside=float(hg.cdf(hi) - hg.cdf(lo - 1)),
                udl_lo=udl(lo), udl_mid=udl(mid), udl_hi=udl(hi))


# --- Milestones ------------------------------------------------------------------------------------

@note("ch19.m1", CHAPTER)
def m1(d, claim):
    c = cycle(d)
    claim(all(subtotal_equals_4060(d)), "credit SubTotal equals the 4060 debits in every year")
    e = expectation(d)
    return dict(returns=len(c.sr), credits=len(c.cm), credit_total=amount(c.cm.values()), refunds=len(c.rf),
                refund_total=amount(c.rf.values(), "amt"), clawbacks=len(c.adj), clawback_total=amount(c.adj, "amt"),
                subtotals=[r2(sum(m["sub"] for m in in_year(c.cm.values(), y))) for y in d.years],
                b2060=[r2(balance_2060(d, y)) for y in d.years], **materiality(d), exp=e["exp"], actual=e["actual"])


@note("ch19.m2", CHAPTER)
def m2(d, claim):
    c, t, s = cycle(d), tests(d), sampling(d)
    big = largest_refund(d)
    claim(sum(1 for r in c.rf.values() if r["amt"] == big["amt"]) == 1, "one refund is the largest")
    inv = c.inv[c.cm[big["cm"]]["inv"]]
    unpaid = inv["gt"] - paid_by(c, inv["id"], big["date"])
    return dict(cm_above=len(t.cm_above), cm_above_total=amount(t.cm_above), cash_credit=len(t.cash_credit),
                rf_above=len(t.rf_above), rf_above_total=amount(t.rf_above, "amt"), before=len(t.before),
                before_total=amount(t.before, "amt"), key=len(s["key"]), key_total=s["key_total"], sample=SAMPLE,
                rest=len(s["rest"]), big=big["num"], big_amount=big["amt"], unpaid=unpaid)


@note("ch19.m3", CHAPTER)
def m3(d, claim):
    t = tests(d)
    design = commission_design(d)
    am = accounting_manager(d)
    claim(am is not None and design["people"] == {am}, "the Accounting Manager approved the commission rates and payments "
          "and created the accruals")
    m = materiality(d)
    claim(amount(in_year(t.cm_above, d.C)) < m["mat"] and amount(in_year(t.rf_above, d.C), "amt") < m["mat"],
          f"the {d.C} exposure of each authority deficiency is below materiality (no material weakness)")
    return dict(additions=[len(t.cm_above), len(t.cash_credit), len(t.rf_above), len(t.before)])


# --- Requirement 1 ---------------------------------------------------------------------------------

@note("ch19.r1", CHAPTER)
def r1(d, claim):
    c, t = cycle(d), tests(d)
    q = d.q
    # returns
    sr_lines = d.one("SELECT COUNT(*) FROM SalesReturnLine")
    statuses = sorted(Counter(s["status"] for s in c.sr.values()).items(), key=lambda kv: -kv[1])
    reasons = sorted(Counter(s["reason"] for s in c.sr.values()).items(), key=lambda kv: (-kv[1], kv[0]))
    receivers = [(phrase(d, ti), n) for ti, n in by_title(d, [s["recv"] for s in c.sr.values()])]
    # credits
    cm_lines = d.one("SELECT COUNT(*) FROM CreditMemoLine")
    cm_status = sorted(((st_, sum(1 for m in c.cm.values() if m["status"] == st_),
                         amount([m for m in c.cm.values() if m["status"] == st_]))
                        for st_ in {m["status"] for m in c.cm.values()}), key=lambda x: -x[1])
    approvers = [(phrase(d, ti), n) for ti, n in by_title(d, [m["appr"] for m in c.cm.values()])]
    same_date = sum(1 for m in c.cm.values() if m["adate"] == m["date"])
    claim(same_date == len(c.cm), "ApprovedDate equals CreditMemoDate on every credit")
    lag = [(D(m["date"]) - D(c.sr[m["ret"]]["date"])).days for m in c.cm.values()]
    # refunds
    refunded = [m for m in c.cm.values() if m["status"] == "Refunded"]
    claim(len(c.rf) == len(refunded) == len({r["cm"] for r in c.rf.values()})
          and {r["cm"] for r in c.rf.values()} == {m["id"] for m in refunded}, "one refund per refunded credit")
    rl = [(D(r["date"]) - D(c.cm[r["cm"]]["date"])).days for r in c.rf.values()]
    cl = [(D(r["cleared"]) - D(r["date"])).days for r in c.rf.values()]
    rf_appr = [(phrase(d, ti), n) for ti, n in by_title(d, [r["appr"] for r in c.rf.values()])]
    # clawbacks
    cb = clawbacks(d)
    claim(cb["complete"], "one clawback per credit line")
    claim(cb["same"], "each clawback has the credit's date and approver")
    # receipts
    rec_titles = dict(by_title(d, [r["rec"] for r in c.rcpt.values()]))
    claim(set(rec_titles) == {CSM, CSR}, "receipts are recorded by the customer service manager and representatives")
    claim({c.emp[r["rec"]]["cc"] for r in c.rcpt.values()} == {CS}, "receipts are recorded by customer service")
    n_apps = sum(len(v) for v in c.apps.values())
    claim({c.emp[a[2]]["cc"] for v in c.apps.values() for a in v} == {CS}, "all applications are by customer service")
    claim(no_orphans(d), "no orphans in any direction")
    nums = {t_: numbering(d, t_, col) for t_, col in (("SalesReturn", "ReturnNumber"), ("CreditMemo", "CreditMemoNumber"),
                                                      ("CustomerRefund", "RefundNumber"),
                                                      ("SalesCommissionAdjustment", "AdjustmentNumber"))}
    claim(all(v is not None for v in nums.values()), "document numbers run without gaps and continue across years")
    claim(nums["SalesReturn"] == nums["CreditMemo"], "returns and credits share their number ranges")
    nums = {k: ranges(v) if v else "?" for k, v in nums.items()}
    # posting matrix
    claim(sides(d, "CreditMemo") == {("Dr", "4060"), ("Dr", "4050"), ("Dr", "2050"), ("Cr", "1020"), ("Cr", "2060")},
          "credits post Dr 4060, 4050, 2050 and Cr 1020, 2060 only")
    cm_post = {f"{s} {a}": gl_total(d, "CreditMemo", a, s) for s, a in sides(d, "CreditMemo")}
    both = sum(1 for p in c.parts.values() if p[0] > 0 and p[1] > 0)
    claim(sides(d, "SalesReturn") == {("Dr", "1040"), ("Cr", "5010"), ("Cr", "5020"), ("Cr", "5030"), ("Cr", "5040")},
          "returns post Dr 1040 and Cr 5010-5040")
    sr_dr = gl_total(d, "SalesReturn", "1040", "Dr")[0]
    claim(abs(sr_dr - sum(gl_total(d, "SalesReturn", a, "Cr")[0] for a in ("5010", "5020", "5030", "5040"))) < 0.005,
          "the returns' debits to 1040 equal their credits to cost of goods sold")
    claim(sides(d, "CustomerRefund") == {("Dr", "2060"), ("Cr", "1010")}, "refunds post Dr 2060 and Cr 1010")
    rf_cr = gl_total(d, "CustomerRefund", "1010", "Cr")[0]
    claim(abs(rf_cr - gl_total(d, "CustomerRefund", "2060", "Dr")[0]) < 0.005, "the refunds' two sides are equal")
    claim(sides(d, "SalesCommissionAdjustment") == {("Dr", "2034"), ("Cr", "6290")}, "clawbacks post Dr 2034 and Cr 6290")
    sca = gl_total(d, "SalesCommissionAdjustment", "6290", "Cr")[0]
    claim(abs(sca - gl_total(d, "SalesCommissionAdjustment", "2034", "Dr")[0]) < 0.005, "the clawbacks' two sides are equal")
    claim(sides(d, "CashReceipt") == {("Dr", "1010"), ("Cr", "2060")}, "receipts post Dr 1010 and Cr 2060")
    claim(sides(d, "CashReceiptApplication") == {("Dr", "2060"), ("Cr", "1020")}, "applications post Dr 2060 and Cr 1020")
    rows = dict(q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE SourceDocumentType IN ('CashReceipt', "
                  "'CashReceiptApplication') GROUP BY 1"))
    # who posts
    people = {"SalesReturn": ("SalesReturn", "SalesReturnID", "ReceivedByEmployeeID"),
              "CreditMemo": ("CreditMemo", "CreditMemoID", "ApprovedByEmployeeID"),
              "CustomerRefund": ("CustomerRefund", "CustomerRefundID", "ApprovedByEmployeeID"),
              "SalesCommissionAdjustment": ("SalesCommissionAdjustment", "SalesCommissionAdjustmentID", "ApprovedByEmployeeID"),
              "CashReceipt": ("CashReceipt", "CashReceiptID", "RecordedByEmployeeID"),
              "CashReceiptApplication": ("CashReceiptApplication", "CashReceiptApplicationID", "AppliedByEmployeeID")}
    numbers = {"SalesReturn": "ReturnNumber", "CreditMemo": "CreditMemoNumber", "CustomerRefund": "RefundNumber",
               "SalesCommissionAdjustment": "AdjustmentNumber", "CashReceipt": "ReceiptNumber",
               "CashReceiptApplication": "CashReceiptApplicationID"}
    created_off = []     # (document, rows) whose GL rows name someone other than the document's person
    for src, (table, key, col) in people.items():
        n = d.one(f"SELECT COUNT(*) FROM GLEntry g JOIN {table} t ON t.{key} = g.SourceDocumentID WHERE g.SourceDocumentType = '{src}'")
        claim(n > 0, f"the cycle's {src} documents post to the ledger")
        created_off += q(f"SELECT t.{numbers[src]}, COUNT(*) FROM GLEntry g JOIN {table} t ON t.{key} = g.SourceDocumentID "
                         f"WHERE g.SourceDocumentType = '{src}' AND g.CreatedByEmployeeID IS NOT t.{col} GROUP BY 1 ORDER BY 1")
    for src, title in (("SalesInvoice", "Chief Executive Officer"), ("DisbursementPayment", "Chief Financial Officer")):
        titles = {r[0] for r in q(f"SELECT DISTINCT e.JobTitle FROM GLEntry g JOIN Employee e ON e.EmployeeID = "
                                  f"g.CreatedByEmployeeID WHERE g.SourceDocumentType = '{src}'")}
        nulls = d.one(f"SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = '{src}' AND CreatedByEmployeeID IS NULL")
        claim(titles == {title} and nulls == 0, f"every {src} row is created by the {title}")
    claim(no_preparer(d), "neither CreditMemo nor CustomerRefund has a preparer column")
    dated = ([(s["recv"], s["date"]) for s in c.sr.values()] + [(m["appr"], m["date"]) for m in c.cm.values()]
             + [(r["appr"], r["date"]) for r in c.rf.values()] + [(r["rec"], r["date"]) for r in c.rcpt.values()]
             + [(a[2], a[0]) for v in c.apps.values() for a in v] + [(a["appr"], a["date"]) for a in c.adj])
    claim(not any((c.emp[e]["term"] and day > c.emp[e]["term"]) or (c.emp[e]["hire"] and day < c.emp[e]["hire"])
                  for e, day in dated), "no document was recorded before hire or after termination")
    planted = anomaly_tables(d)
    claim(planted is not None and not (planted & CYCLE_TABLES), "the AnomalyLog plants nothing in the cycle's tables")
    return dict(sr=dict(n=len(c.sr), lines=sr_lines, first=min(s["date"] for s in c.sr.values()),
                        last=max(s["date"] for s in c.sr.values()), customers=len({s["cust"] for s in c.sr.values()})),
                statuses=statuses, reasons=reasons, receivers=receivers,
                cm=dict(n=len(c.cm), lines=cm_lines, first=min(m["date"] for m in c.cm.values()),
                        last=max(m["date"] for m in c.cm.values()), total=amount(c.cm.values())),
                cm_status=cm_status, approvers=approvers, same_date=same_date,
                lag=dict(lo=min(lag), hi=max(lag), mean=st.mean(lag), zero=lag.count(0)),
                rf=dict(n=len(c.rf), total=amount(c.rf.values(), "amt"), first=min(r["date"] for r in c.rf.values()),
                        last=max(r["date"] for r in c.rf.values()), lo=min(rl), hi=max(rl), mean=st.mean(rl),
                        over30=sum(x > 30 for x in rl), clo=min(cl), chi=max(cl)),
                rf_appr=rf_appr, cb=cb, receipts=len(c.rcpt), receipt_total=amount(c.rcpt.values(), "amt"),
                manager=rec_titles.get(CSM, 0), reps=rec_titles.get(CSR, 0), apps=n_apps, nums=nums,
                post=cm_post, both=both, sr_dr=sr_dr, rf_cr=rf_cr, sca=sca, rows=rows,
                created_off=[dict(doc=doc, rows=k) for doc, k in created_off])


# --- Requirement 2 ---------------------------------------------------------------------------------

@note("ch19.r2", CHAPTER)
def r2_(d, claim):
    c = cycle(d)
    yrs = d.years
    by = lambda f: [f(y) for y in yrs]  # noqa: E731
    credits = by(lambda y: in_year(c.cm.values(), y))
    claim(reconciles(d), "every reconciliation of Requirement 2 holds to the cent in every year")
    sub = [r2(sum(m["sub"] for m in ms)) for ms in credits]
    freight = [r2(sum(m["freight"] for m in ms)) for ms in credits]
    tax = [r2(sum(m["tax"] for m in ms)) for ms in credits]
    gt = [r2(sum(m["gt"] for m in ms)) for ms in credits]
    cr1020 = by(lambda y: gl_year(d, "CreditMemo", "1020", y, "Cr"))
    cr2060 = by(lambda y: gl_year(d, "CreditMemo", "2060", y, "Cr"))
    std = dict(d.q("SELECT CAST(substr(sr.ReturnDate, 1, 4) AS INTEGER), SUM(srl.ExtendedStandardCost) FROM SalesReturnLine srl "
                   "JOIN SalesReturn sr ON sr.SalesReturnID = srl.SalesReturnID GROUP BY 1"))
    std = [std.get(y, 0.0) for y in yrs]
    claim(all(abs(s - gl_year(d, "SalesReturn", "1040", y, "Dr")) < 0.005 for s, y in zip(std, yrs)),
          "the returns at standard equal the 1040 debits in every year")
    cogs = [(a, by(lambda y, a=a: gl_year(d, "SalesReturn", a, y, "Cr"))) for a in ("5010", "5020", "5030", "5040")]
    refunds = by(lambda y: in_year(c.rf.values(), y))
    clawback = by(lambda y: r2(sum(a["amt"] for a in c.adj if year_of(a["date"]) == y)))
    accruals = dict(d.q("SELECT CAST(substr(AccrualDate, 1, 4) AS INTEGER), SUM(CommissionAmount) FROM SalesCommissionAccrual GROUP BY 1"))
    payments = dict(d.q("SELECT CAST(substr(PaymentDate, 1, 4) AS INTEGER), SUM(NetPaymentAmount) FROM SalesCommissionPayment GROUP BY 1"))
    receipts = by(lambda y: r2(sum(r["amt"] for r in c.rcpt.values() if year_of(r["date"]) == y)))
    # 2060 at the year-ends and its items
    b2060 = by(lambda y: r2(balance_2060(d, y)))
    items = by(lambda y: open_2060(d, y))
    for y, b, it in zip(yrs, b2060, items):
        claim(abs(b - sum(i["amount"] for i in it)) < 0.005, f"2060 at the end of {y} is the open credit items")
    claim(all(i["status"] == "Issued" for i in items[-1]) and
          {i["id"] for i in items[-1]} == {m["id"] for m in c.cm.values() if m["status"] == "Issued"},
          f"the items in 2060 at the end of {d.C} are the Issued credits")
    p_items = abbreviated([i["number"] for i in items[1]])
    c_items = [dict(number=n, amount=i["amount"]) for n, i in zip(abbreviated([i["number"] for i in items[2]]), items[2])]
    b2034 = d.one("SELECT SUM(Credit - Debit) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ?", d.account("2034"),
                  year_end(d.C))
    closes = ",".join(f"'{x}'" for x in d.closes)
    close_rows = {str(a): (n, cr - dr) for a, n, dr, cr in d.q(
        f"SELECT a.AccountNumber, COUNT(*), SUM(g.Debit), SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        f"WHERE a.AccountNumber IN (4060, 6290) AND g.VoucherNumber IN ({closes}) GROUP BY 1")}
    return dict(n=[len(ms) for ms in credits], sub=sub, sub_total=r2(sum(sub)), freight=freight, tax=tax,
                tax_total=r2(sum(tax)), gt=gt, cr1020=cr1020, cr2060=cr2060, std=std, std_total=r2(sum(std)), cogs=cogs,
                rf_n=[len(rs) for rs in refunds], rf_amt=[amount(rs, "amt") for rs in refunds], clawback=clawback,
                accruals=[accruals.get(y, 0.0) for y in yrs], payments=[payments.get(y, 0.0) for y in yrs],
                receipts=receipts, b2060=b2060, f_items=items[0], p_items=p_items, c_items=c_items, b2034=b2034,
                close_4060=close_rows.get("4060", (0, 0.0)), close_6290=close_rows.get("6290", (0, 0.0)))


# --- Requirement 3 ---------------------------------------------------------------------------------

@note("ch19.r3", CHAPTER)
def r3(d, claim):
    c = cycle(d)
    m, e = materiality(d), expectation(d)
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountName LIKE '%Income Tax%'") == 0,
          "the chart has no income tax account, so net income is income before income taxes")
    claim(abs(e["diff"]) > m["trivial"], "the difference is above clearly trivial, so the expectation calls for investigation")
    claim(e["rates"][0] < e["rates"][1] and e["exp_f"] < e["actual"], f"the {d.F} rate understates the expectation")
    claim(d.one("SELECT MIN(ShipmentDate) FROM Shipment") >= f"{d.F}-01-01"
          and d.one("SELECT MIN(PostingDate) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice'") >= f"{d.F}-01-01",
          f"fiscal {d.F} had no earlier sales (no shipment or sales posting before it)")
    rf_people = {r["appr"] for r in c.rf.values()}
    claim(len(rf_people) <= 10, "a small team approves the refunds")
    clawback_total = sum(a["amt"] for a in c.adj)
    claim(clawback_total < 0.1 * m["mat"], "clawbacks are low in amount (under a tenth of materiality over the window)")
    cs = lambda ids: {c.emp[e_]["cc"] for e_ in ids} == {CS}  # noqa: E731
    claim(cs(r["rec"] for r in c.rcpt.values()) and cs(a[2] for v in c.apps.values() for a in v)
          and cs(x["appr"] for x in c.cm.values()) and cs(a["appr"] for a in c.adj),
          "customer service records receipts, applies cash, approves credits, and approves clawbacks")
    return dict(**m, **e, above_perf=abs(e["diff"]) > m["perf"])


# --- Requirement 4 ---------------------------------------------------------------------------------

@note("ch19.r4", CHAPTER)
def r4(d, claim):
    c, t = cycle(d), tests(d)
    yr = lambda items: [len(in_year(items, y)) for y in d.years]  # noqa: E731
    cur = lambda items, key="gt": (len(in_year(items, d.C)), amount(in_year(items, d.C), key))  # noqa: E731
    above_titles = {c.emp[m["appr"]]["title"] for m in t.cm_above}
    above_limits = {c.emp[m["appr"]]["limit"] for m in t.cm_above}
    claim(len(above_titles) == 1 and len(above_limits) == 1, "all credits above the limit were approved by one job title with one limit")
    above_title = above_titles.pop() if len(above_titles) == 1 else "?"
    claim(above_title == CSR, "the credits above the limit were approved by customer service representatives")
    within = [m for m in c.cm.values() if m not in t.cm_above]
    managers = {m["appr"] for m in within}
    claim(len(managers) == 1 and title_of(d, next(iter(managers))) == CSM and
          all(c.emp[m["appr"]]["limit"] == 0 or m["gt"] <= c.emp[m["appr"]]["limit"] for m in c.cm.values()
              if c.emp[m["appr"]]["limit"] > 0), "the customer service manager's limit is never exceeded")
    manager_limit = c.emp[next(iter(managers))]["limit"] if managers else 0
    # refunds
    rf_groups = []
    for title, n in by_title(d, [r["appr"] for r in t.rf_above], order="first"):
        rf_groups.append((bare(d, title), n, amount([r for r in t.rf_above if title_of(d, r["appr"]) == title], "amt")))
    within_rf = [r for r in c.rf.values() if r not in t.rf_above]
    within_titles = {title_of(d, r["appr"]) for r in within_rf}
    claim(len(within_titles) == 1, "the refunds within limit were all approved by one job title")
    within_title = within_titles.pop() if len(within_titles) == 1 else "?"
    claim(c.holders[within_title] == 1, "one employee holds the title of the refunds within limit")
    claim(len(d.years) == 3, "the window has three fiscal years")
    # before payment
    before_due = [r for r in t.before if r["date"] < c.inv[c.cm[r["cm"]]["inv"]]["due"]]
    wait = [(D(last_payment(c, c.cm[r["cm"]]["inv"])) - D(r["date"])).days for r in t.before]
    final = all(abs(p[0] - min(c.cm[k]["gt"], max(c.inv[c.cm[k]["inv"]]["gt"] - sum(a[1] for a in c.apps[c.cm[k]["inv"]]), 0)))
                < 0.01 for k, p in c.parts.items()) and set(c.parts) == set(c.cm)
    claim(final, "each credit's part to 1020 is what the invoice's final payments leave unpaid, the rest goes to 2060")
    to_2060 = [k for k, p in c.parts.items() if p[1] > 0]
    unpaid_2060 = [k for k in to_2060 if not any(a[0] <= c.cm[k]["date"] for a in c.apps[c.cm[k]["inv"]])]
    # past due
    pd1 = [r for k, r in c.rf.items() if t.pdue[k] > 0.005]
    pd2 = [r for k, r in c.rf.items() if t.pdue[k] >= r["amt"]]
    # method mismatch
    claim(all(len({r["method"] for r in c.rcpt.values() if r["cust"] == cu}) > 1 for cu in {r["cust"] for r in c.rcpt.values()}),
          "no customer pays by one method only")
    methods = {r["method"] for r in c.rf.values()}
    expected = sum(1 - len(t.methods[k] & methods) / len(methods) for k in c.rf)
    claim(abs(expected - len(t.mism)) <= 0.1 * len(t.mism), "a refund method chosen at random would mismatch about as often")
    # clean results
    claim(not any(r["appr"] == c.cm[r["cm"]]["appr"] for r in c.rf.values()), "the refund approver is never the credit approver")
    claim(warehouse_receipt(d), "returns are always received in the warehouse")
    equal_2060 = sum(1 for r in c.rf.values() if abs(c.parts[r["cm"]][1] - r["amt"]) < 0.005)
    claim(equal_2060 == len(c.rf), "every refund equals its credit's 2060 part")
    cb = clawbacks(d)
    claim(cb["complete"] and cb["base_ok"] == cb["n"], "a clawback for every credit line, at the line total and the accrual's rate")
    claim(cb["half"] and cb["exact"], "every clawback is base x rate rounded half up; those that differ from SQLite's "
          "ROUND(base x rate, 2) are exact half-cent products")
    claim(cb["later"], "the clawbacks were netted in later commission payments")
    last_payment_date = d.one("SELECT MAX(PaymentDate) FROM SalesCommissionPayment")
    claim(last_payment_date <= year_end(d.C), f"the commission payments end by the end of {d.C}")
    design = commission_design(d)
    am = accounting_manager(d)
    claim(am is not None and design["people"] == {am}, "the Accounting Manager approved all rates and payments and created "
          "all accruals")
    claim(len(design["rate_ends"]) == 1, "the commission rates share one end date")
    return dict(cm_above=dict(n=len(t.cm_above), amt=amount(t.cm_above), years=yr(t.cm_above), cur=cur(t.cm_above)),
                above_title=plural(above_title).lower(), above_limit=above_limits.pop() if above_limits else 0,
                manager_limit=manager_limit,
                cc=dict(n=len(t.cash_credit), amt=amount(t.cash_credit), years=yr(t.cash_credit), cur=cur(t.cash_credit)),
                cc_early=dict(n=len(t.cc_early), amt=amount(t.cc_early), cur=cur(t.cc_early)[0]),
                cc_rec=dict(n=len(t.cc_rec), amt=amount(t.cc_rec)),
                rf_above=dict(n=len(t.rf_above), amt=amount(t.rf_above, "amt"), years=yr(t.rf_above),
                              cur=cur(t.rf_above, "amt")), rf_groups=rf_groups, within_title=within_title,
                within=dict(n=len(within_rf), amt=amount(within_rf, "amt")),
                before=dict(n=len(t.before), amt=amount(t.before, "amt"), years=yr(t.before), cur=cur(t.before, "amt")),
                nothing=dict(n=len(t.nothing), amt=amount(t.nothing, "amt"), cur=cur(t.nothing, "amt")),
                before_due=len(before_due), wait=dict(lo=min(wait), hi=max(wait), mean=st.mean(wait)),
                unpaid_2060=len(unpaid_2060), to_2060=len(to_2060),
                pd1=dict(n=len(pd1), amt=amount(pd1, "amt")), pd2=dict(n=len(pd2), amt=amount(pd2, "amt"), cur=cur(pd2, "amt")),
                mism=dict(n=len(t.mism), amt=amount(t.mism, "amt"), cur=cur(t.mism, "amt")), n_methods=word(len(methods)),
                equal_2060=equal_2060, n_refunds=len(c.rf), cb=cb, off=abbreviated([a["num"] for a in cb["off"]]),
                design=design, rate_end=design["rate_ends"][0])


# --- Requirement 5 ---------------------------------------------------------------------------------

@note("ch19.r5", CHAPTER)
def r5(d, claim):
    c, t = cycle(d), tests(d)
    lines = credit_lines(d)
    yrs = d.years
    group_year = defaultdict(float)
    for l in lines:
        group_year[(l["group"], year_of(l["date"]))] += l["total"]
    groups = sorted({l["group"] for l in lines}, key=lambda g: -sum(group_year[(g, y)] for y in yrs))
    by_group = [(g, [r2(group_year[(g, y)]) for y in yrs]) for g in groups]
    top = groups[0]
    accounts = {r[0] for r in d.q("SELECT a.AccountNumber FROM Item i JOIN Account a ON a.AccountID = i.RevenueAccountID "
                                  "WHERE i.ItemGroup = ?", top)}
    claim(len(accounts) == 1, f"{top} items share one revenue account")
    top_account = str(accounts.pop()) if len(accounts) == 1 else "?"
    top_rev = [d.one("SELECT SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = ? "
                     "AND g.SourceDocumentType = 'SalesInvoice' AND CAST(substr(g.PostingDate, 1, 4) AS INTEGER) = ?", top_account, y)
               for y in yrs]
    top_rates = [group_year[(top, y)] / v for y, v in zip(yrs, top_rev)]
    reason = "Damaged"
    claim(any(l["reason"] == reason for l in lines), f"returns are coded {reason}")
    damaged = [r2(sum(l["total"] for l in lines if l["reason"] == reason and year_of(l["date"]) == y)) for y in yrs]
    top_damaged = [r2(sum(l["total"] for l in lines if l["reason"] == reason and l["group"] == top and year_of(l["date"]) == y))
                   for y in yrs]
    fam = Counter()
    for l in lines:
        if l["group"] == top and year_of(l["date"]) == d.C:
            fam[l["family"]] += l["total"]
    families = [(f, r2(v)) for f, v in sorted(fam.items(), key=lambda kv: -kv[1])[:TOP_FAMILIES]]
    seg_year = defaultdict(float)
    for l in lines:
        seg_year[(l["segment"], year_of(l["date"]))] += l["total"]
    segments = sorted({l["segment"] for l in lines}, key=lambda s: -sum(seg_year[(s, y)] for y in yrs))
    top_segment = segments[0]
    carriers = Counter(l["carrier"] for l in lines if l["reason"] == reason)
    claim(max(carriers.values()) < 1.5 * min(carriers.values()), f"no concentration of {reason} lines by carrier")
    warehouses = sorted(Counter(l["warehouse"] for l in lines).items())
    wn = [n for _, n in warehouses]
    claim(max(wn) < 1.5 * min(wn), "no concentration by warehouse")
    lag_s = [(D(l["return_date"]) - D(l["ship_date"])).days for l in lines]
    lag_d = [(D(l["return_date"]) - D(l["delivered"])).days for l in lines if l["delivered"]]
    # rates by shipment month
    ship_rev = defaultdict(float)
    for day, lt in d.q("SELECT s.ShipmentDate, sil.LineTotal FROM SalesInvoiceLine sil JOIN ShipmentLine sl ON "
                       "sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID"):
        ship_rev[day[:7]] += lt
    ret_ship = defaultdict(float)
    for l in lines:
        ret_ship[l["ship_date"][:7]] += l["total"]
    by_ship_year = [sum(v for k, v in ret_ship.items() if int(k[:4]) == y) / sum(v for k, v in ship_rev.items() if int(k[:4]) == y)
                    for y in yrs]
    months = {k: ret_ship[k] / ship_rev[k] for k in sorted(ship_rev) if int(k[:4]) == d.C}
    dec = months.get(f"{d.C}-12", 0.0)
    others = [v for k, v in months.items() if k != f"{d.C}-12"]
    claim(dec < min(others), f"December {d.C} shipments have the lowest return rate (censored)")
    cross = [l for l in lines if l["return_date"][:4] != l["ship_date"][:4]]
    claim(not any(l["ship_date"] < f"{d.F}-01-01" for l in lines)
          and d.one("SELECT COUNT(*) FROM Shipment WHERE ShipmentDate < ?", f"{d.F}-01-01") == 0,
          f"{d.F} has no {d.F - 1} carry-in")
    # customers
    sales = dict(d.q("SELECT si.CustomerID, SUM(sil.LineTotal) FROM SalesInvoiceLine sil JOIN SalesInvoice si ON "
                     "si.SalesInvoiceID = sil.SalesInvoiceID GROUP BY 1"))
    cred = defaultdict(float)
    for m in c.cm.values():
        cred[m["cust"]] += m["sub"]
    overall = sum(cred.values()) / sum(sales.values())
    focus = max(cred, key=lambda k: cred[k])
    seg, terms = d.q("SELECT CustomerSegment, PaymentTerms FROM Customer WHERE CustomerID = ?", focus)[0]
    rate = cred[focus] / sales[focus]
    focus_cm = [m for m in c.cm.values() if m["cust"] == focus]
    top_two = Counter(m["appr"] for m in focus_cm).most_common(2)
    claim(len(top_two) == 2, "two or more employees approved the customer's credits")

    def role(e: int) -> str:
        title = title_of(d, e)
        return ("a representative" if title == CSR else f"the {title}" if c.holders[title] == 1
                else f"{'an' if title[0] in 'AEIOU' else 'a'} {title}")
    two = "two representatives" if all(title_of(d, e) == CSR for e, _ in top_two) else " and ".join(role(e) for e, _ in top_two)
    focus_rf = [r for r in c.rf.values() if r["cust"] == focus]
    before_ids = {r["id"] for r in t.before}
    focus_before = sum(1 for r in focus_rf if r["id"] in before_ids)
    # the customers with a higher return rate, with their sales; "small" ones sell under a tenth of the customer's sales
    higher = sorted(((k, cred[k] / sales[k], sales[k]) for k in cred if k in sales and cred[k] / sales[k] > rate),
                    key=lambda x: -x[1])
    n_small = sum(1 for _, _, s in higher if s < sales[focus] / 10)
    approvers = [(bare(d, ti), [sum(1 for r in in_year(c.rf.values(), y) if title_of(d, r["appr"]) == ti) for y in yrs])
                 for ti, _ in by_title(d, [r["appr"] for r in c.rf.values()], order="name")]
    scores = Counter(t.score.values())
    hi = [k for k, s in t.score.items() if s >= 4]
    big = largest_refund(d)
    weekend_rf = sum(D(r["date"]).weekday() >= 5 for r in c.rf.values())
    weekend_cm = sum(D(m["date"]).weekday() >= 5 for m in c.cm.values())
    claim(abs(weekend_rf / len(c.rf) - 2 / 7) < 0.05 and abs(weekend_cm / len(c.cm) - 2 / 7) < 0.05,
          "weekend dates are spread evenly")
    return dict(by_group=by_group, top_rates=top_rates, top_account=top_account, damaged=damaged, top_damaged=top_damaged,
                top=top, families=families, top_segment=top_segment,
                segment=[r2(seg_year[(top_segment, y)]) for y in yrs], car_lo=min(carriers.values()), car_hi=max(carriers.values()),
                warehouses=wn, lag=dict(lo=min(lag_s), hi=max(lag_s), mean=st.mean(lag_s), dlo=min(lag_d), dhi=max(lag_d)),
                by_ship_year=by_ship_year, dec=dec, mlo=min(others), mhi=max(others), cross=len(cross),
                cross_amt=r2(sum(l["total"] for l in cross)), overall=overall, focus=focus, seg=seg, terms=terms,
                rate=rate, focus_cred=cred[focus], focus_sales=sales[focus], focus_n=len(focus_cm),
                focus_gt=amount(focus_cm), top_two=sum(n for _, n in top_two), focus_rf=len(focus_rf),
                focus_rf_amt=amount(focus_rf, "amt"), two=two, focus_before=focus_before, higher=higher,
                n_small=word(n_small), approvers=approvers, big_above=t.flags[big["id"]][0],
                scores=[scores.get(s, 0) for s in range(6)], hi=len(hi), hi_amt=r2(sum(c.rf[k]["amt"] for k in hi)),
                big=big["num"], big_score=t.score[big["id"]], weekend_rf=weekend_rf, weekend_cm=weekend_cm)


# --- Requirement 6 ---------------------------------------------------------------------------------

@note("ch19.r6", CHAPTER)
def r6(d, claim):
    s = sampling(d)
    claim(s["udl"][0] < TOLERABLE <= s["udl"][1], "only zero deviations supports reliance at 5%")
    claim(s["udl_lo"] > TOLERABLE and len(s["dev"]) / len(s["rest"]) > TOLERABLE,
          "every plausible draw concludes the control is ineffective, as the population did")
    return dict(s=s, key_numbers=abbreviated([r["num"] for r in s["key"]]), n=SAMPLE)


# --- Requirement 7 ---------------------------------------------------------------------------------

@note("ch19.r7", CHAPTER)
def r7(d, claim):
    c, t = cycle(d), tests(d)
    sub = substantive(d)
    claim(sub["traced"] == sub["lines"], "every credit line traces to its return, shipment, and invoice lines")
    claim(sub["over"] == 0 and sub["twice"] == 0, "no quantity above shipped and no shipment line returned twice")
    claim(sub["price_off"] == 0, "price and discount equal the invoice line's")
    claim(not sub["total_off"], "LineTotal is ROUND(Q x P x (1 - D), 2) on every credit line but half-cent roundings")
    claim(sub["distinct_inv"] == len(c.cm) and sub["above_invoice"] == 0, "one credit per invoice, none above its invoice")
    claim(sub["sub_ok"] == len(c.cm), "SubTotal equals the lines on every credit")
    claim(sub["tax_ok"] == len(c.cm) and sub["gt_ok"], "tax is the rate on SubTotal plus freight on every credit")
    claim({m["id"] for m in sub["tax_sub_flags"]} == {m["id"] for m in sub["with_freight"]},
          "a tax test on SubTotal alone flags exactly the credits with freight")
    claim(sub["freight_over"] == 0, "no freight credit above the invoice's freight")
    # restocking: at standard cost, except the return lines of less than one unit (the whole shipment line), which are
    # costed at the quantity times the shipment line's extended cost
    rest = dict(d.q("SELECT sr.ReasonCode || '|' || substr(sr.ReturnDate, 1, 4), SUM(srl.ExtendedStandardCost) FROM SalesReturnLine srl "
                    "JOIN SalesReturn sr ON sr.SalesReturnID = srl.SalesReturnID GROUP BY 1"))
    frac = d.q("SELECT sr.ReasonCode, srl.QuantityReturned, sl.QuantityShipped, srl.ExtendedStandardCost, sl.ExtendedStandardCost, "
               "ROUND(srl.QuantityReturned * i.StandardCost, 2) FROM SalesReturnLine srl JOIN SalesReturn sr ON sr.SalesReturnID = "
               "srl.SalesReturnID JOIN ShipmentLine sl ON sl.ShipmentLineID = srl.ShipmentLineID JOIN Item i ON i.ItemID = srl.ItemID "
               "WHERE ABS(srl.ExtendedStandardCost - ROUND(srl.QuantityReturned * i.StandardCost, 2)) > 0.011")
    claim(all(q < 1 and abs(q - qs) < 1e-9 and abs(ext - r2(q * ship_ext)) < 0.011 for _, q, qs, ext, ship_ext, _ in frac),
          "the return lines restocked off standard are whole shipment lines of less than one unit, costed at the quantity "
          "times the shipment line's extended cost")
    frac_gap = r2(sum(full - ext for _, _, _, ext, _, full in frac))
    frac_dq = r2(sum(full - ext for reason, _, _, ext, _, full in frac if reason in ("Damaged", "Quality Concern")))
    claim(sides(d, "SalesReturn") == {("Dr", "1040"), ("Cr", "5010"), ("Cr", "5020"), ("Cr", "5030"), ("Cr", "5040")},
          "returns go back to inventory with no write-down account")
    dmg = [r2(rest.get(f"Damaged|{y}", 0.0)) for y in d.years]
    both_c = r2(rest.get(f"Damaged|{d.C}", 0.0) + rest.get(f"Quality Concern|{d.C}", 0.0))
    both = r2(sum(v for k, v in rest.items() if k.split("|")[0] in ("Damaged", "Quality Concern")))
    lap = lapping(d)
    claim(lap["clean"], "lapping tests clean: no other customer's invoice, every receipt deposited and fully applied")
    claim(sides(d, "CashReceipt") == {("Dr", "1010"), ("Cr", "2060")}, "receipts are held in 2060 until applied")
    claim(len(c.cm) < 1000 and len(c.rf) < 1000, "credits and refunds are too few for a first-digit test")
    # the timeline of the largest refund, from the data: each step with its date and who did it
    rf = largest_refund(d)
    claim(sum(1 for r in c.rf.values() if r["amt"] == rf["amt"]) == 1, "one refund is the largest")
    claim(t.score[rf["id"]] > 0, "the largest refund carries at least one of the five flags, so it calls for follow-up")
    m = c.cm[rf["cm"]]
    inv = c.inv[m["inv"]]
    sr = c.sr[m["ret"]]
    ships = d.q("SELECT DISTINCT s.ShipmentNumber, s.ShipmentDate, s.DeliveryDate, s.ShippedBy FROM SalesInvoiceLine sil "
                "JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                "WHERE sil.SalesInvoiceID = ? ORDER BY s.ShipmentDate, s.ShipmentNumber", inv["id"])
    first_day = min([s[1] for s in ships] + [inv["date"]])

    def when(day: str, full: bool = False) -> str:
        """A date as the timeline writes it: in full the first time, then without its year while the year is the same."""
        return day[:10] if full or day[:4] != first_day[:4] else md(day)

    def who(e: int) -> str:
        title = title_of(d, e)
        if title == CSR:
            name = f"representative {e}"
        elif c.holders[title] == 1:
            name = f"the {title}"
        else:
            name = f"{'an' if title[0] in 'AEIOU' else 'a'} {title}"
        return name + (", the credit's approver" if e == m["appr"] else "")

    events = []      # (date, order, text): the steps in date order
    for number, shipped, delivered, carrier in ships:
        events.append((shipped, 0, f"{number} shipped {{when}} ({carrier}), delivered {when(delivered)}"))
    events.append((inv["date"], 1, f"{inv['num']} dated {{when}}, {money2(inv['gt'])}, due {when(inv['due'])} "
                                   f"(customer {inv['cust']})"))
    for day, applied, applier, rid in c.apps[inv["id"]]:
        r = c.rcpt[rid]
        if r["rec"] == applier:
            hands = f"recorded and applied{' on ' + when(day) if day != r['date'] else ''} by {who(applier)}"
        else:
            hands = f"recorded by {who(r['rec'])}, applied{' on ' + when(day) if day != r['date'] else ''} by {who(applier)}"
        events.append((r["date"], 2, f"{r['num']} {{when}}, {method_word(r['method'])}, {money2(applied)} applied ({hands})"))
    lines = d.q("SELECT srl.QuantityReturned, sl.QuantityShipped, i.ItemCode FROM SalesReturnLine srl JOIN ShipmentLine sl ON "
                "sl.ShipmentLineID = srl.ShipmentLineID JOIN Item i ON i.ItemID = srl.ItemID WHERE srl.SalesReturnID = ? "
                "ORDER BY srl.LineNumber", sr["id"])
    returned = "; ".join(f"{q:,.2f} of {s:,.2f} {code}" for q, s, code in lines)
    events.append((sr["date"], 3, f"{sr['num']} {{when}}, {sr['reason']} ({returned}), received by {who(sr['recv'])}"))
    largest = m["gt"] == max(x["gt"] for x in c.cm.values()) and sum(1 for x in c.cm.values() if x["gt"] == m["gt"]) == 1
    to1020, to2060 = c.parts[m["id"]]
    split = ("all to 2060" if to1020 < 0.005 else "all to 1020" if to2060 < 0.005
             else f"{money2(to1020)} to 1020 and {money2(to2060)} to 2060")
    unpaid = inv["gt"] - paid_by(c, inv["id"], m["date"])
    approver = who(m["appr"]).removesuffix(", the credit's approver")
    events.append((m["date"], 4, f"{m['num']} {{when}}, {money2(m['gt'])}"
                                 + (f", the largest credit of the {word(len(d.years))} years" if largest else "")
                                 + f", approved by {approver} with a limit of {c.emp[m['appr']]['limit']:,.0f}, {split} "
                                 + (f"while {money2(unpaid)} of the invoice was unpaid" if unpaid > 0.005 else "after the invoice was paid")))
    claws = sorted((a for a in c.adj if a["cm"] == m["id"]), key=lambda a: a["num"])
    if claws:
        nums = claws[0]["num"] + "".join("/" + str(int(a["num"].rsplit("-", 1)[1])) for a in claws[1:])
        events.append((claws[0]["date"], 5, f"clawback{'s' if len(claws) > 1 else ''} {nums} "
                                            f"({' and '.join(money2(a['amt']) for a in claws)})"))
    limit = c.emp[rf["appr"]]["limit"]
    events.append((rf["date"], 6, f"{rf['num']} {{when}}, a {D(rf['date']).strftime('%A')}, {method_word(rf['method'])}, "
                                  f"approved by {who(rf['appr'])} ({'within' if rf['amt'] <= limit else 'above'} the "
                                  f"{limit:,.0f} limit), cleared {when(rf['cleared']) if rf['cleared'] else 'not yet'}"))
    paid = sum(a[1] for a in c.apps[inv["id"]])
    settled = max((a[0] for a in c.apps[inv["id"]]), default=None)
    if settled and abs(paid - inv["gt"]) < 0.005:
        events.append((settled, 7, "the invoice was settled on {when}"))
    else:
        events.append(("9999-12-31", 7, f"{money2(inv['gt'] - paid)} of the invoice was never paid"))
    events.sort(key=lambda e: (e[0], e[1]))
    timeline = "; ".join(text.replace("{when}", when(day, full=k == 0)) for k, (day, _, text) in enumerate(events))
    # what the evidence must settle: the refund's payee, and why it differs from the invoice's payments, where it does
    methods = sorted({c.rcpt[a[3]]["method"] for a in c.apps[inv["id"]]})
    before = (last_payment(c, inv["id"]) or "") > rf["date"]
    payee = {"Wire Transfer": "the wire confirmation's beneficiary and account against the customer's known bank details",
             "ACH": "the ACH confirmation's beneficiary and account against the customer's known bank details",
             "Check": "the cleared check's payee and endorsement",
             "Credit Card": "the card processor's record of the card credited"}.get(rf["method"], "the refund's payee and account")
    why = []
    if methods and rf["method"] not in methods:
        why.append(f"why the refund went by {method_word(rf['method'])} to a customer who paid this invoice by "
                   f"{' and '.join(method_word(x) for x in methods)}")
    if before:
        paid_by_one = len(methods) == 1 and methods[0] in ("Check", "Wire Transfer")
        why.append(f"why before its {method_word(methods[0]) + 's' if paid_by_one else 'payments'} arrived")
    return dict(sub=sub, rate=sub["rate"], half=[x["id"] for x in sub["half"]],
                with_freight=len(sub["with_freight"]), dmg=dmg, dmg_total=r2(sum(dmg)), both=both, both_c=both_c, lap=lap,
                n_frac=len(frac), frac_gap=frac_gap, frac_dq=frac_dq, n_cm=len(c.cm), n_rf=len(c.rf),
                timeline=timeline, payee=payee, why=", and ".join(why))


# --- Requirement 8 ---------------------------------------------------------------------------------

@note("ch19.r8", CHAPTER)
def r8(d, claim):
    c, t = cycle(d), tests(d)
    m = materiality(d)
    d1 = amount(in_year(t.cm_above, d.C))
    all_c = amount(in_year(c.cm.values(), d.C))
    claim(m["perf"] < d1 < m["mat"], f"the {d.C} exposure of D1 is above performance materiality and below materiality")
    claim(all_c > m["mat"], f"all {d.C} credits exceed materiality")
    cs = lambda ids: {c.emp[e_]["cc"] for e_ in ids} == {CS}  # noqa: E731
    claim(cs(r["rec"] for r in c.rcpt.values()) and cs(a[2] for v in c.apps.values() for a in v)
          and cs(x["appr"] for x in c.cm.values()) and cs(a["appr"] for a in c.adj),
          "customer service records receipts, applies cash, approves credits, and approves clawbacks")
    sub = substantive(d)
    claim(no_orphans(d) and warehouse_receipt(d) and sub["price_off"] == 0,
          "every credit traces to a return received in the warehouse at invoice prices")
    rf_centers = sorted({c.emp[r["appr"]]["cc"] for r in c.rf.values()})
    claim(CS not in rf_centers, "refunds are approved outside customer service")
    claim(lapping(d)["clean"], "no lapping trace")
    d3 = in_year(t.rf_above, d.C)
    d4 = in_year(t.before, d.C)
    claim(all(c.parts[r["cm"]][1] > 0 and paid_by(c, c.cm[r["cm"]]["inv"], c.cm[r["cm"]]["date"]) < c.inv[c.cm[r["cm"]]["inv"]]["gt"] - 0.005
              for r in t.before), "the refunds before payment come from credits booked to 2060 on unpaid invoices")
    claim(no_preparer(d), "no preparer is recorded")
    exposure = {r["id"]: r["amt"] for r in d3 + d4}
    claim(sum(exposure.values()) < m["mat"] / 2, "the refund deficiencies' magnitude is well below materiality")
    am = accounting_manager(d)
    design = commission_design(d)
    claim(am is not None and design["people"] == {am}, "the Accounting Manager approved the rates and payments and created the accruals")
    claim(d.one("SELECT COUNT(*) FROM PayrollRegister WHERE ApprovedByEmployeeID IS NOT ?", am) == 0,
          "the Accounting Manager approved every payroll register")
    claim(warehouse_receipt(d) and sides(d, "SalesReturn") == {("Dr", "1040"), ("Cr", "5010"), ("Cr", "5020"), ("Cr", "5030"), ("Cr", "5040")},
          "damaged goods go back to inventory at full cost")
    claim(reconciles(d) and clawbacks(d)["clean"] and sub["clean"], "the reconciliations, clawbacks, and substantive tests are clean")
    return dict(rf_centers=rf_centers, am_largest=am is not None and largest_refund(d)["appr"] == am,
                d1_n=len(t.cm_above), d1=d1, perf=m["perf"], all_c=all_c, d2=len(t.cash_credit), d3_n=len(t.rf_above),
                d3=(len(d3), amount(d3, "amt")), d4_n=len(t.before), d4=(len(d4), amount(d4, "amt")))


# --- Requirement 9 ---------------------------------------------------------------------------------

@note("ch19.r9", CHAPTER)
def r9(d, claim):
    t = tests(d)
    claim(reconciles(d) and substantive(d)["clean"], "the records reconcile and the balances tested are right")
    claim(len(t.cm_above) > 0 and len(t.rf_above) > 0, "credits and refunds were granted above authority")
    claim(lapping(d)["clean"], "no trace of lapping")
    design = commission_design(d)
    claim(design["rate_ends"] == [year_end(d.C)], f"the commission rates end at the end of {d.C}, so {d.N} needs approved rates")
    return {}


# --- Requirement 10 --------------------------------------------------------------------------------

@note("ch19.r10", CHAPTER)
def r10(d, claim):
    c, t = cycle(d), tests(d)
    pop_c = [len(in_year(c.cm.values(), y)) for y in d.years]
    pop_r = [len(in_year(c.rf.values(), y)) for y in d.years]
    tests_ = []
    for name, rows, pop in (("CM AboveLimit", t.cm_above, pop_c), ("CM CashAndCredit", t.cash_credit, pop_c),
                            ("RF AboveLimit", t.rf_above, pop_r), ("RF BeforePayment", t.before, pop_r)):
        n = [len(in_year(rows, y)) for y in d.years]
        tests_.append(dict(name=name, n=len(rows), years=n, rates=[1000 * k / p for k, p in zip(n, pop)],
                           rate=1000 * len(rows) / sum(pop)))
    old = register(d)
    new = len(old) + sum(x["n"] for x in tests_)
    keys = Counter((e["test"], e["doc"]) for e in old)
    for x, rows, key in ((tests_[0], t.cm_above, "num"), (tests_[1], t.cash_credit, "num"), (tests_[2], t.rf_above, "num"),
                         (tests_[3], t.before, "num")):
        for r in rows:
            keys[(x["name"], r[key])] += 1
    claim(max(keys.values()) == 1, "(TestID, DocumentNumber) stays unique")
    claim(len(d.years) == 3, "the window has three fiscal years")
    last = dict(JE=max(e["date"] for e in entries(d)), PO=max(o["date"] for o in orders(d)),
                PR=max(r["date"] for r in registers(d)))
    through = min(last.values())
    claim(through == last["PR"], "Data Through is set by payroll")
    cm_last = max(m["date"] for m in c.cm.values())
    rf_last = max(r["date"] for r in c.rf.values())
    claim(cm_last > through and rf_last > through, "the credits and refunds run past Data Through, so it stays")
    return dict(tests=tests_, pop_c=pop_c, pop_r=pop_r, old=len(old), new=new, through=through, cm_last=cm_last,
                rf_last=rf_last)
