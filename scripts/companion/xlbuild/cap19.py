"""Credits Audit.xlsx: the Excel part of the solution to the Chapter 19 capstone case, "Auditing the Customer Credits
Cycle".

The case gives Excel the workbook of its tools-and-files table (tbl-19-02): materiality, the risk-and-control matrix,
the sample, and the evaluation of deficiencies, with a Documentation worksheet, and the tables for the report's
appendix. This builder starts from a blank workbook, as the case tells the reader to, and applies one function per
requirement the workbook answers: the appendix tables of Requirements 1, 2, 4, and 7 (the map of the cycle, the
reconciliation by year, the test results, and the timeline of the largest refund), the planning workbook of
Requirement 3, the sample of Requirement 6, the evaluation of Requirement 8, and the report of Requirement 9 as a model
answer. Requirement 5 (the returns analytics) and Requirement 10 (the continuing tests) are Power BI work, and
Credits.sql is a later phase; this workbook does not build them.

Every check compares a live formula with a value computed here from CharlesRiver.sqlite (read-only), independently of
Excel, with the case's definitions; the values agree with the instructor notes (facts/notes/ch19.py), which the xlenv
Python cannot import (no jinja2 or scipy), so the logic is restated here and the beta and hypergeometric
distributions are computed exactly from the binomial.

What the builder decides where the case leaves a choice (the workbook says so where a reader would look):
  - The populations come from CharlesRiver.xlsx through Power Query, so the workbook refreshes: the ledger summarized
    by fiscal year, account, source document, and close (T3_GLEntry with Transform Data, filtered before 2027-01-01
    first); the credits, refunds, return lines, clawbacks, receipts and applications by year and by job title, the
    commission accruals and payments by year, and the commission rates. The control-test flags the case defines are
    computed in M where M can do it (authority, the credit approver's cash on the invoice, the refund before the last
    payment, the refund method), as the Requirement 10 note describes for the register.
  - What M cannot do reasonably is pasted as values from the queries Credits.sql answers (the as-of past-due balance on
    each refund date, the open items in 2060, the timeline of the largest refund, the substantive and lapping
    results, the payroll approvals of Chapters 12 and 16), with an amber fill and a cell note naming the query. The
    refund flags are pasted as RefundFlags.csv would hold them, and the live flags are reconciled to them.
  - The sample is drawn by Excel's own RANDARRAY and SORTBY and pasted as values (the draw is frozen in the file, a
    cell note says when, and no check depends on which refunds it drew).
  - Sheets: Documentation, Cycle Map, Reconciliation, Materiality, Risks, Tests, Sample, Timeline, Deficiencies, and
    Report, then the query worksheets (each named after its query) and the Solution Notes.
  - Employees appear by ID and job title only, as the case's roles do.
"""

from __future__ import annotations

import functools
import math
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import cached_property
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import db_uri  # noqa: E402
from xlbuild import notes, pq, xl  # noqa: E402
from xlbuild.solutions import COUNT, MONEY, PCT, ExerciseBuild  # noqa: E402

DATE = "yyyy-mm-dd"
MA = "Model answer"
PASTED = "Pasted as values from Credits.sql"
CS, CSR, CSM = "Customer Service", "Customer Service Representative", "Customer Service Manager"
AM = "Accounting Manager"
# The case's parameters: materiality 5% of income before income taxes as the ledger records it, performance
# materiality 75% of it, clearly trivial 5% of it (Requirement 3); key items are refunds of 5,000 or more and refunds to
# a customer whose refunds over the window exceed 10,000; the sampling parameters are 95% confidence, 5% tolerable,
# 0% expected, so n = 59 from tbl-19-03 (Requirement 6).
MATERIALITY, PERFORMANCE, TRIVIAL = 0.05, 0.75, 0.05
KEY_AMOUNT, KEY_CUSTOMER = 5000, 10000
CONFIDENCE, TOLERABLE, EXPECTED = 0.95, 0.05, 0.0
TAIL = 0.05                     # the plausible draws: the tightest range with each tail below 5%
REVENUE = ("4010", "4020", "4030", "4040", "4080")
SOURCES = ("SalesReturn", "CreditMemo", "CustomerRefund", "SalesCommissionAdjustment", "CashReceipt",
           "CashReceiptApplication")
MATRIX_ACCOUNTS = ("1010", "1020", "1040", "2034", "2050", "2060", "4050", "4060", "5010", "5020", "5030", "5040",
                   "6290")
REASONS = ("Late Delivery", "Wrong Item", "Customer Remorse", "Damaged", "Quality Concern")
# tbl-19-03: (expected rate) -> [(confidence, tolerable, n, deviations allowed)]
TBL_19_03 = {0.00: [(0.95, 0.05, 59, 0), (0.95, 0.10, 29, 0), (0.90, 0.05, 45, 0), (0.90, 0.10, 22, 0)],
             0.01: [(0.95, 0.05, 93, 1), (0.95, 0.10, 46, 1), (0.90, 0.05, 77, 1), (0.90, 0.10, 38, 1)],
             0.02: [(0.95, 0.05, 181, 4), (0.95, 0.10, 46, 1), (0.90, 0.05, 132, 3), (0.90, 0.10, 38, 1)]}
DATA_SHEETS = ("Ledger", "Credits", "Refunds", "ReturnLines", "Clawbacks", "CashByYear", "CashHandlers",
               "CommissionByYear", "CommissionRates", "RefundFlags")
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


# --- helpers ---------------------------------------------------------------------------------------------------------

def r2(x: float) -> float:
    return round(x + 0.0, 2)


def xr(x: float, places: int = 2) -> float:
    """Excel's ROUND: half away from zero, on the value as Excel shows it."""
    return float(Decimal(repr(round(x, 9))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def money(x: float) -> str:
    return f"-${-x:,.2f}" if x < 0 else f"${x:,.2f}"


def amt(x: float) -> str:
    return f"{x:,.2f}"


def word(n: int, capital: bool = False) -> str:
    text = WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"
    return text.capitalize() if capital else text


def pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


def series(items) -> str:
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else " and ".join(items) if len(items) == 2 else \
        ", ".join(items[:-1]) + ", and " + items[-1]


def plural(title: str) -> str:
    return title + "s"


def iso(day: str) -> date:
    return date.fromisoformat(day[:10])


def year_of(day: str) -> int:
    return int(day[:4])


def binom_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def beta_inv(conf: float, k: int, n: int) -> float:
    """Excel's BETA.INV(conf, k + 1, n - k): the upper deviation limit for k deviations in a sample of n. With integer
    parameters the beta CDF is a binomial tail, P(Beta(k+1, n-k) <= x) = P(Bin(n, x) >= k + 1), so bisect on it."""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 1 - binom_cdf(k, n, mid) < conf:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def hypergeom_cdf(k: int, population: int, successes: int, n: int) -> float:
    """Excel's HYPGEOM.DIST(k, n, successes, population, TRUE)."""
    total = math.comb(population, n)
    return sum(math.comb(successes, i) * math.comb(population - successes, n - i)
               for i in range(0, k + 1)) / total if k >= 0 else 0.0


def letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# --- the values the solution must reproduce ---------------------------------------------------------------------------

class Facts:
    """Expected values for the checks and the figures the model answers quote, from CharlesRiver.sqlite (read-only)."""

    def __init__(self, year: int):
        con = sqlite3.connect(db_uri(), uri=True)
        self.q = lambda sql, *args: con.execute(sql, args).fetchall()
        self.one = lambda sql, *args: con.execute(sql, args).fetchone()[0]
        self.C = year
        self.F = self.one("SELECT MIN(FiscalYear) FROM GLEntry")
        self.years = list(range(self.F, self.C + 1))
        self.P, self.N = self.C - 1, self.C + 1
        assert len(self.years) == 3, self.years
        self.closes = [r[0] for r in self.q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' "
                                            "ORDER BY EntryNumber")]
        self.acct = {str(r[0]): r[1] for r in self.q("SELECT AccountNumber, AccountID FROM Account")}
        self.emp = {r[0]: dict(id=r[0], title=r[1], limit=r[2] or 0, hire=r[3], term=r[4]) for r in self.q(
            "SELECT EmployeeID, JobTitle, MaxApprovalAmount, HireDate, TerminationDate FROM Employee")}
        self.holders = Counter(e["title"] for e in self.emp.values())
        self.inv = {r[0]: dict(id=r[0], num=r[1], cust=r[2], date=r[3], due=r[4], gt=r[5]) for r in self.q(
            "SELECT SalesInvoiceID, InvoiceNumber, CustomerID, InvoiceDate, DueDate, GrandTotal FROM SalesInvoice")}
        self.cm = {r[0]: dict(id=r[0], num=r[1], date=r[2], ret=r[3], cust=r[4], inv=r[5], sub=r[6], freight=r[7],
                              tax=r[8], gt=r[9], status=r[10], appr=r[11]) for r in self.q(
            "SELECT CreditMemoID, CreditMemoNumber, CreditMemoDate, SalesReturnID, CustomerID, OriginalSalesInvoiceID, "
            "SubTotal, FreightCreditAmount, TaxAmount, GrandTotal, Status, ApprovedByEmployeeID FROM CreditMemo "
            "ORDER BY CreditMemoID")}
        self.rf = {r[0]: dict(id=r[0], num=r[1], date=r[2], cust=r[3], cm=r[4], amt=r[5], method=r[6], appr=r[7],
                              cleared=r[8]) for r in self.q(
            "SELECT CustomerRefundID, RefundNumber, RefundDate, CustomerID, CreditMemoID, Amount, PaymentMethod, "
            "ApprovedByEmployeeID, ClearedDate FROM CustomerRefund ORDER BY CustomerRefundID")}
        self.sr = {r[0]: dict(id=r[0], num=r[1], date=r[2], cust=r[3], recv=r[4], reason=r[5], status=r[6])
                   for r in self.q("SELECT SalesReturnID, ReturnNumber, ReturnDate, CustomerID, ReceivedByEmployeeID, "
                                   "ReasonCode, Status FROM SalesReturn ORDER BY SalesReturnID")}
        self.srl = [dict(id=r[0], ret=r[1], qty=r[2], std=r[3]) for r in self.q(
            "SELECT SalesReturnLineID, SalesReturnID, QuantityReturned, ExtendedStandardCost FROM SalesReturnLine")]
        self.rcpt = {r[0]: dict(id=r[0], num=r[1], date=r[2], cust=r[3], amt=r[4], method=r[5], dep=r[6], rec=r[7])
                     for r in self.q("SELECT CashReceiptID, ReceiptNumber, ReceiptDate, CustomerID, Amount, "
                                     "PaymentMethod, DepositDate, RecordedByEmployeeID FROM CashReceipt")}
        self.apps = defaultdict(list)            # by invoice: (date, amount, applier, receipt)
        self.all_apps = []
        for inv, day, a, e, rid in self.q("SELECT SalesInvoiceID, ApplicationDate, AppliedAmount, AppliedByEmployeeID, "
                                          "CashReceiptID FROM CashReceiptApplication ORDER BY CashReceiptApplicationID"):
            self.apps[inv].append((day, a, e, rid))
            self.all_apps.append((inv, day, a, e, rid))
        self.cred = defaultdict(list)            # credits by invoice: (date, grand total)
        for m in self.cm.values():
            self.cred[m["inv"]].append((m["date"], m["gt"]))
        self.adj = [dict(id=r[0], num=r[1], date=r[2], cm=r[3], line=r[4], base=r[5], rate=r[6], amt=r[7], appr=r[8],
                         accrual=r[9]) for r in self.q(
            "SELECT SalesCommissionAdjustmentID, AdjustmentNumber, AdjustmentDate, CreditMemoID, CreditMemoLineID, "
            "CommissionBaseReductionAmount, CommissionRatePct, CommissionAdjustmentAmount, ApprovedByEmployeeID, "
            "SalesCommissionAccrualID FROM SalesCommissionAdjustment ORDER BY AdjustmentNumber")]
        self.cm_lines = {r[0]: dict(id=r[0], cm=r[1], total=r[2]) for r in self.q(
            "SELECT CreditMemoLineID, CreditMemoID, LineTotal FROM CreditMemoLine")}
        self.accrual_rate = dict(self.q("SELECT SalesCommissionAccrualID, CommissionRatePct FROM SalesCommissionAccrual"))
        # the ledger, as the Ledger query summarizes it: (year, account number, source, close) -> [debit, credit, rows]
        closes = ",".join(f"'{c}'" for c in self.closes)
        self.gl = defaultdict(lambda: [0.0, 0.0, 0])
        for y, acct, src, close, dr, cr, n in self.q(
                f"SELECT g.FiscalYear, a.AccountNumber, g.SourceDocumentType, g.VoucherNumber IN ({closes}), "
                f"SUM(g.Debit), SUM(g.Credit), COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                f"WHERE g.PostingDate < ? GROUP BY 1, 2, 3, 4", f"{self.C + 1}-01-01"):
            self.gl[(y, str(acct), src, bool(close))] = [dr, cr, n]
        self.acct_type = {str(r[0]): r[1] for r in self.q("SELECT AccountNumber, AccountType FROM Account")}
        self.ledger_rows = len(self.gl)
        # each credit's parts posted to receivables (1020) and to customer deposits (2060)
        self.parts = defaultdict(lambda: [0.0, 0.0])
        for doc, acct, cr in self.q("SELECT SourceDocumentID, AccountID, SUM(Credit) FROM GLEntry WHERE SourceDocumentType = "
                                    "'CreditMemo' AND AccountID IN (?, ?) AND Credit > 0 GROUP BY 1, 2",
                                    self.acct["1020"], self.acct["2060"]):
            self.parts[doc][0 if acct == self.acct["1020"] else 1] += cr

    def title(self, e: int) -> str:
        return self.emp[e]["title"]

    def by_title(self, ids) -> dict[str, int]:
        return dict(Counter(self.title(e) for e in ids))

    def gl_sum(self, side: str, acct: str | None = None, src: str | None = None, years=None, close: bool | None = False,
               types=None) -> float:
        i = 0 if side == "Dr" else 1
        out = 0.0
        for (y, a, s, c), v in self.gl.items():
            if (acct is None or a == acct) and (src is None or s == src) and (years is None or y in years) \
                    and (close is None or c == close) and (types is None or self.acct_type[a] in types):
                out += v[i]
        return out

    def gl_rows(self, acct: str, src: str) -> int:
        return sum(v[2] for (y, a, s, c), v in self.gl.items() if a == acct and s == src)

    # --- Requirement 3 ---------------------------------------------------------------------------------------------
    @cached_property
    def materiality(self) -> dict:
        income = self.gl_sum("Cr", years=[self.C], types=("Revenue", "Expense")) - \
            self.gl_sum("Dr", years=[self.C], types=("Revenue", "Expense"))
        m = income * MATERIALITY
        return dict(income=income, mat=m, perf=m * PERFORMANCE, trivial=m * TRIVIAL)

    @cached_property
    def expectation(self) -> dict:
        rev = [sum(self.gl_sum("Cr", a, "SalesInvoice", [y]) - self.gl_sum("Dr", a, "SalesInvoice", [y]) for a in REVENUE)
               for y in self.years]
        ret = [self.gl_sum("Dr", "4060", None, [y]) for y in self.years]
        rates = [r / v for r, v in zip(ret, rev)]
        exp = rates[-2] * rev[-1]
        exp_f = rates[0] * rev[-1]
        m = self.materiality
        diff = ret[-1] - exp
        return dict(revenue=rev, returns=ret, rates=rates, actual=ret[-1], exp=exp, diff=diff, diff_pct=ret[-1] / exp - 1,
                    exp_f=exp_f, diff_f=ret[-1] - exp_f, f_pct=ret[-1] / exp_f - 1,
                    above_trivial=abs(diff) > m["trivial"], above_perf=abs(diff) > m["perf"],
                    first_shipment=self.one("SELECT MIN(ShipmentDate) FROM Shipment"))

    # --- Requirement 4 ---------------------------------------------------------------------------------------------
    def paid_by(self, inv: int, day: str) -> float:
        return sum(a[1] for a in self.apps[inv] if a[0] <= day)

    def last_payment(self, inv: int) -> str | None:
        return max((a[0] for a in self.apps[inv]), default=None)

    @cached_property
    def tests(self) -> dict:
        emp, cm, rf = self.emp, self.cm, self.rf
        t = {}
        t["cm_above"] = [m for m in cm.values() if m["gt"] > emp[m["appr"]]["limit"]]
        t["cash_credit"] = [m for m in cm.values() if any(a[2] == m["appr"] for a in self.apps[m["inv"]])]
        t["cc_early"] = [m for m in cm.values() if any(a[2] == m["appr"] and a[0] <= m["date"]
                                                       for a in self.apps[m["inv"]])]
        t["cc_rec"] = [m for m in cm.values() if any(a[2] == m["appr"] or self.rcpt[a[3]]["rec"] == m["appr"]
                                                     for a in self.apps[m["inv"]])]
        t["rf_above"] = [r for r in rf.values() if r["amt"] > emp[r["appr"]]["limit"]]
        t["before"] = [r for r in rf.values() if (self.last_payment(cm[r["cm"]]["inv"]) or "") > r["date"]]
        t["nothing"] = [r for r in rf.values() if not any(a[0] <= r["date"] for a in self.apps[cm[r["cm"]]["inv"]])]
        t["same_approver"] = [r for r in rf.values() if r["appr"] == cm[r["cm"]]["appr"]]
        dated = ([(m["appr"], m["date"]) for m in cm.values()] + [(r["appr"], r["date"]) for r in rf.values()])
        t["outside_employment"] = [x for x in dated if (emp[x[0]]["term"] and x[1] > emp[x[0]]["term"])
                                   or (emp[x[0]]["hire"] and x[1] < emp[x[0]]["hire"])]
        by_cust = defaultdict(list)
        for i, v in self.inv.items():
            by_cust[v["cust"]].append(i)

        def past_due(cust: int, asof: str) -> float:
            total = 0.0
            for i in by_cust[cust]:
                v = self.inv[i]
                if v["date"] > asof:
                    continue
                bal = v["gt"] - self.paid_by(i, asof) - sum(a for day, a in self.cred[i] if day <= asof)
                if bal > 0.005 and v["due"] < asof:
                    total += bal
            return total
        t["pdue"] = {k: past_due(r["cust"], r["date"]) for k, r in rf.items()}
        t["methods"] = {k: {self.rcpt[a[3]]["method"] for a in self.apps[cm[r["cm"]]["inv"]]} for k, r in rf.items()}
        t["mism"] = [r for k, r in rf.items() if r["method"] not in t["methods"][k]]
        t["pd1"] = [r for k, r in rf.items() if t["pdue"][k] > 0.005]
        t["pd2"] = [r for k, r in rf.items() if t["pdue"][k] >= r["amt"]]
        above_ids = {r["id"] for r in t["rf_above"]}
        cm_above_ids = {m["id"] for m in t["cm_above"]}
        mism_ids = {r["id"] for r in t["mism"]}
        before_ids = {r["id"] for r in t["before"]}
        t["flags"] = {k: [k in above_ids, r["cm"] in cm_above_ids, k in mism_ids, k in before_ids,
                          t["pdue"][k] >= r["amt"]] for k, r in rf.items()}
        t["score"] = {k: sum(f) for k, f in t["flags"].items()}
        t["wait"] = [(iso(self.last_payment(cm[r["cm"]]["inv"])) - iso(r["date"])).days for r in t["before"]]
        # the clawbacks: one per credit line, the line total and the accrual's rate, the amount by Excel's ROUND
        per_line = Counter(a["line"] for a in self.adj)
        t["cb_lines"] = len(self.cm_lines)
        t["cb_distinct"] = len(per_line)
        t["cb_complete"] = set(per_line) == set(self.cm_lines) and all(n == 1 for n in per_line.values())
        t["cb_base"] = sum(1 for a in self.adj if abs(a["base"] - self.cm_lines[a["line"]]["total"]) < 0.005)
        t["cb_rate"] = sum(1 for a in self.adj if abs(a["rate"] - self.accrual_rate[a["accrual"]]) < 1e-9)
        t["cb_round"] = sum(1 for a in self.adj if abs(a["amt"] - xr(a["base"] * a["rate"])) < 0.001)
        t["cb_same"] = sum(1 for a in self.adj if a["date"] == cm[a["cm"]]["date"] and a["appr"] == cm[a["cm"]]["appr"])
        receivers = {s["recv"] for s in self.sr.values()}
        t["receiver_is_approver"] = sum(1 for m in cm.values() if self.sr[m["ret"]]["recv"] == m["appr"])
        t["receiver_titles"] = sorted({self.title(e) for e in receivers})
        return t

    def in_year(self, items, y: int, key: str = "date") -> list:
        return [x for x in items if year_of(x[key]) == y]

    def stat(self, items, key: str = "gt") -> dict:
        """Count and amount over the window, by year, and in the current year."""
        return dict(n=len(items), amt=r2(sum(x[key] for x in items)),
                    years=[len(self.in_year(items, y)) for y in self.years],
                    amts=[r2(sum(x[key] for x in self.in_year(items, y))) for y in self.years],
                    cur=len(self.in_year(items, self.C)), cur_amt=r2(sum(x[key] for x in self.in_year(items, self.C))))

    # --- Requirement 6 ---------------------------------------------------------------------------------------------
    @cached_property
    def sampling(self) -> dict:
        by_cust = defaultdict(float)
        for r in self.rf.values():
            by_cust[r["cust"]] += r["amt"]
        key = sorted((r for r in self.rf.values() if r["amt"] >= KEY_AMOUNT or by_cust[r["cust"]] > KEY_CUSTOMER),
                     key=lambda r: r["num"])
        key_ids = {r["id"] for r in key}
        rest = [r for r in self.rf.values() if r["id"] not in key_ids]
        before_ids = {r["id"] for r in self.tests["before"]}
        dev = [r for r in rest if r["id"] in before_ids]
        n = next(x[2] for x in TBL_19_03[EXPECTED] if x[0] == CONFIDENCE and x[1] == TOLERABLE)
        N, K = len(rest), len(dev)
        cdf = lambda k: hypergeom_cdf(k, N, K, n)  # noqa: E731
        lo = max(k for k in range(n + 1) if cdf(k - 1) < TAIL)
        hi = min(k for k in range(n + 1) if 1 - cdf(k) < TAIL)
        mean = n * K / N
        mid = round(mean)
        return dict(key=key, key_total=r2(sum(r["amt"] for r in key)), key_dev=sum(1 for r in key if r["id"] in before_ids),
                    rest=rest, rest_total=r2(sum(r["amt"] for r in rest)), dev=dev, n=n, share=n / N,
                    udl=[beta_inv(CONFIDENCE, k, n) for k in range(4)], mean=mean, lo=lo, hi=hi, mid=mid,
                    cdf_lo=cdf(lo - 1), cdf_hi=cdf(hi), udl_lo=beta_inv(CONFIDENCE, lo, n),
                    udl_mid=beta_inv(CONFIDENCE, mid, n), udl_hi=beta_inv(CONFIDENCE, hi, n),
                    big_customers={c: v for c, v in by_cust.items() if v > KEY_CUSTOMER},
                    zero_draw=hypergeom_cdf(0, N, K, n))

    # --- Requirement 2 ---------------------------------------------------------------------------------------------
    def balance(self, acct: str, y: int) -> float:
        """Credit less debit of an account through the end of fiscal year y (closes included: none touch the hubs)."""
        return sum(v[1] - v[0] for (yy, a, s, c), v in self.gl.items() if a == acct and yy <= y)

    @cached_property
    def open_2060(self) -> dict[int, list[tuple[str, float]]]:
        """The credits whose part posted to 2060 by a year-end is not yet refunded by it."""
        out = {}
        a2060 = self.acct["2060"]
        for y in self.years:
            left = defaultdict(float)
            for doc, v in self.q("SELECT SourceDocumentID, SUM(Credit) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ? "
                                 "AND SourceDocumentType = 'CreditMemo' GROUP BY 1", a2060, f"{y}-12-31"):
                left[doc] += v
            for r in self.rf.values():
                if r["date"] <= f"{y}-12-31":
                    left[r["cm"]] -= r["amt"]
            out[y] = [(self.cm[k]["num"], r2(v), self.cm[k]["status"]) for k, v in
                      sorted(left.items(), key=lambda kv: self.cm[kv[0]]["num"]) if v > 0.005]
        return out

    @cached_property
    def commission(self) -> dict:
        acc = dict(self.q("SELECT CAST(substr(AccrualDate, 1, 4) AS INTEGER), SUM(CommissionAmount) FROM "
                          "SalesCommissionAccrual GROUP BY 1"))
        pay = dict(self.q("SELECT CAST(substr(PaymentDate, 1, 4) AS INTEGER), SUM(NetPaymentAmount) FROM "
                          "SalesCommissionPayment GROUP BY 1"))
        creators = {r[0] for r in self.q("SELECT DISTINCT CreatedByEmployeeID FROM SalesCommissionAccrual")}
        payers = {r[0] for r in self.q("SELECT DISTINCT ApprovedByEmployeeID FROM SalesCommissionPayment")}
        rates = self.q("SELECT ApprovedByEmployeeID, EffectiveEndDate FROM SalesCommissionRate")
        return dict(accruals=[acc.get(y, 0.0) for y in self.years], payments=[pay.get(y, 0.0) for y in self.years],
                    n_accruals=self.one("SELECT COUNT(*) FROM SalesCommissionAccrual"),
                    n_payments=self.one("SELECT COUNT(*) FROM SalesCommissionPayment"), creators=creators,
                    payers=payers, n_rates=len(rates), rate_approvers={r[0] for r in rates},
                    rate_ends=sorted({r[1][:10] for r in rates}),
                    pending=sum(1 for a in self.adj if a["id"] not in {
                        r[0] for r in self.q("SELECT SourceDocumentID FROM SalesCommissionPaymentLine WHERE "
                                             "SourceDocumentType = 'SalesCommissionAdjustment'")}))

    # --- Requirement 7 ---------------------------------------------------------------------------------------------
    @cached_property
    def restock(self) -> dict:
        out = defaultdict(float)
        for l in self.srl:
            s = self.sr[l["ret"]]
            out[(s["reason"], year_of(s["date"]))] += l["std"]
        return out

    @cached_property
    def fractional(self) -> dict:
        rows = self.q("SELECT sr.ReasonCode, srl.ExtendedStandardCost, ROUND(srl.QuantityReturned * i.StandardCost, 2) "
                      "FROM SalesReturnLine srl JOIN SalesReturn sr ON sr.SalesReturnID = srl.SalesReturnID "
                      "JOIN Item i ON i.ItemID = srl.ItemID WHERE ABS(srl.ExtendedStandardCost - "
                      "ROUND(srl.QuantityReturned * i.StandardCost, 2)) > 0.011")
        return dict(n=len(rows), gap=r2(sum(full - ext for _, ext, full in rows)),
                    gap_dq=r2(sum(full - ext for reason, ext, full in rows if reason in ("Damaged", "Quality Concern"))))

    @cached_property
    def largest(self) -> dict:
        top = max(r["amt"] for r in self.rf.values())
        rf = [r for r in self.rf.values() if r["amt"] == top]
        assert len(rf) == 1
        rf = rf[0]
        m = self.cm[rf["cm"]]
        inv = self.inv[m["inv"]]
        sr = self.sr[m["ret"]]
        ships = self.q("SELECT DISTINCT s.ShipmentNumber, s.ShipmentDate, s.DeliveryDate, s.ShippedBy FROM "
                       "SalesInvoiceLine sil JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s "
                       "ON s.ShipmentID = sl.ShipmentID WHERE sil.SalesInvoiceID = ? ORDER BY s.ShipmentDate", inv["id"])
        lines = self.q("SELECT srl.QuantityReturned, sl.QuantityShipped, i.ItemCode FROM SalesReturnLine srl JOIN "
                       "ShipmentLine sl ON sl.ShipmentLineID = srl.ShipmentLineID JOIN Item i ON i.ItemID = srl.ItemID "
                       "WHERE srl.SalesReturnID = ? ORDER BY srl.LineNumber", sr["id"])
        claws = sorted((a for a in self.adj if a["cm"] == m["id"]), key=lambda a: a["num"])
        to2060 = self.one("SELECT COALESCE(SUM(Credit), 0) FROM GLEntry WHERE SourceDocumentType = 'CreditMemo' AND "
                          "SourceDocumentID = ? AND AccountID = ?", m["id"], self.acct["2060"])
        to1020 = self.one("SELECT COALESCE(SUM(Credit), 0) FROM GLEntry WHERE SourceDocumentType = 'CreditMemo' AND "
                          "SourceDocumentID = ? AND AccountID = ?", m["id"], self.acct["1020"])
        unpaid_credit = inv["gt"] - self.paid_by(inv["id"], m["date"])
        unpaid_refund = inv["gt"] - self.paid_by(inv["id"], rf["date"])

        def who(e: int) -> str:
            t = self.title(e)
            return f"{t} (employee {e})"
        steps = []        # (date, order, step, document, detail, who)
        for number, shipped, delivered, carrier in ships:
            steps.append((shipped, 0, "Shipment", number, f"Shipped by {carrier}; delivered {delivered[:10]}", "Warehouse"))
        steps.append((inv["date"], 1, "Sales invoice", inv["num"],
                      f"{money(inv['gt'])}, due {inv['due'][:10]}, customer {inv['cust']}", "Accounting (billing)"))
        for day, applied, applier, rid in self.apps[inv["id"]]:
            r = self.rcpt[rid]
            hands = (f"Recorded and applied by {who(applier)}" if r["rec"] == applier else
                     f"Recorded by {who(r['rec'])}; applied by {who(applier)}")
            steps.append((r["date"], 2, "Cash receipt", r["num"],
                          f"{r['method']}, {money(applied)} applied to the invoice on {day[:10]}", hands))
        returned = "; ".join(f"{q:,.2f} of {s:,.2f} {code}" for q, s, code in lines)
        steps.append((sr["date"], 3, "Sales return", sr["num"], f"{sr['reason']}: {returned}",
                      f"Received by {who(sr['recv'])}"))
        largest_credit = m["gt"] == max(x["gt"] for x in self.cm.values())
        steps.append((m["date"], 4, "Credit memo", m["num"],
                      f"{money(m['gt'])}{', the largest credit of the window' if largest_credit else ''}; "
                      f"{money(to2060)} to 2060 and {money(to1020)} to 1020 while {money(unpaid_credit)} of the invoice "
                      f"was unpaid; approver's limit {money(self.emp[m['appr']]['limit'])}",
                      f"Approved by {who(m['appr'])}"))
        for a in claws:
            steps.append((a["date"], 5, "Commission clawback", a["num"], f"{money(a['amt'])} at {a['rate']:.2%}",
                          f"Approved by {who(a['appr'])}"))
        steps.append((rf["date"], 6, "Customer refund", rf["num"],
                      f"{money(rf['amt'])} by {rf['method']} on a {iso(rf['date']).strftime('%A')}, cleared "
                      f"{rf['cleared'][:10]}; {money(unpaid_refund)} of the invoice unpaid; approver's limit "
                      f"{money(self.emp[rf['appr']]['limit'])}", f"Approved by {who(rf['appr'])}"))
        paid = sum(a[1] for a in self.apps[inv["id"]])
        settled = self.last_payment(inv["id"])
        assert abs(paid - inv["gt"]) < 0.005
        steps.append((settled, 7, "Invoice settled", inv["num"], f"Fully paid ({money(paid)} applied in all)", ""))
        steps.sort(key=lambda s: (s[0], s[1]))
        methods = sorted({self.rcpt[a[3]]["method"] for a in self.apps[inv["id"]]})
        return dict(rf=rf, cm=m, inv=inv, sr=sr, steps=steps, unpaid_credit=unpaid_credit, unpaid_refund=unpaid_refund,
                    to2060=to2060, to1020=to1020, largest_credit=largest_credit, methods=methods, claws=claws,
                    settled=settled, weekday=iso(rf["date"]).strftime("%A"),
                    score=self.tests["score"][rf["id"]], flags=self.tests["flags"][rf["id"]])

    @cached_property
    def substantive(self) -> dict:
        """Requirement 7's recomputations and lapping tests, as Credits.sql answers them (pasted in the workbook)."""
        lines = self.q("SELECT l.CreditMemoLineID, l.Quantity, l.UnitPrice, l.Discount, l.LineTotal, sl.QuantityShipped, "
                       "sil.UnitPrice, sil.Discount, sil.SalesInvoiceID, cm.OriginalSalesInvoiceID FROM CreditMemoLine l "
                       "JOIN CreditMemo cm ON cm.CreditMemoID = l.CreditMemoID JOIN SalesReturnLine srl ON "
                       "srl.SalesReturnLineID = l.SalesReturnLineID JOIN ShipmentLine sl ON sl.ShipmentLineID = "
                       "srl.ShipmentLineID LEFT JOIN SalesInvoiceLine sil ON sil.ShipmentLineID = sl.ShipmentLineID")
        traced = sum(1 for r in lines if r[8] is not None and r[8] == r[9])
        over = sum(1 for r in lines if r[1] > r[5] + 1e-9)
        price_off = sum(1 for r in lines if r[6] is None or abs(r[2] - r[6]) > 0.004 or abs(r[3] - r[7]) > 1e-9)
        total_off = [r[0] for r in self.q("SELECT CreditMemoLineID FROM CreditMemoLine WHERE ABS(LineTotal - "
                                          "ROUND(Quantity * UnitPrice * (1 - Discount), 2)) > 0.004 ORDER BY 1")]
        twice = self.one("SELECT COUNT(*) FROM (SELECT ShipmentLineID FROM SalesReturnLine GROUP BY 1 HAVING COUNT(*) > 1)")
        distinct_inv = len({m["inv"] for m in self.cm.values()})
        above_invoice = sum(1 for m in self.cm.values() if m["gt"] > self.inv[m["inv"]]["gt"] + 0.005)
        rate = round(sum(m["tax"] for m in self.cm.values()) / sum(m["sub"] + m["freight"] for m in self.cm.values()), 3)
        tax_ok = sum(1 for m in self.cm.values() if abs(m["tax"] - round((m["sub"] + m["freight"]) * rate, 2)) < 0.006)
        with_freight = sum(1 for m in self.cm.values() if m["freight"] > 0.005)
        other = sum(1 for inv, day, a, e, rid in self.all_apps if self.rcpt[rid]["cust"] != self.inv[inv]["cust"])
        dep = [(iso(r["dep"]) - iso(r["date"])).days for r in self.rcpt.values() if r["dep"]]
        lag = [(iso(day) - max(iso(self.rcpt[rid]["date"]), iso(self.inv[inv]["date"]))).days
               for inv, day, a, e, rid in self.all_apps]
        applied = defaultdict(float)
        for inv, day, a, e, rid in self.all_apps:
            applied[rid] += a
        not_full = sum(1 for k, r in self.rcpt.items() if abs(applied[k] - r["amt"]) > 0.005)
        early = [(rid, a) for inv, day, a, e, rid in self.all_apps if self.rcpt[rid]["date"] < self.inv[inv]["date"]]
        return dict(lines=len(lines), traced=traced, over=over, price_off=price_off, total_off=total_off, twice=twice,
                    distinct_inv=distinct_inv, above_invoice=above_invoice, rate=rate, tax_ok=tax_ok,
                    with_freight=with_freight, other=other, dep_lo=min(dep), dep_hi=max(dep), lag_lo=min(lag),
                    lag_hi=max(lag), not_full=not_full, early_receipts=len({rid for rid, _ in early}),
                    early_apps=len(early), early_amount=r2(sum(a for _, a in early)))

    @cached_property
    def payroll_approvals(self) -> dict:
        am = [e for e, v in self.emp.items() if v["title"] == AM]
        assert len(am) == 1
        n = self.one("SELECT COUNT(*) FROM PayrollRegister")
        by_am = self.one("SELECT COUNT(*) FROM PayrollRegister WHERE ApprovedByEmployeeID = ?", am[0])
        return dict(am=am[0], registers=n, by_am=by_am)

    @cached_property
    def cause(self) -> dict:
        """Requirement 4's cause of the refunds before payment: the credits posted to 2060 on unpaid invoices."""
        to_2060 = [k for k, p in self.parts.items() if p[1] > 0]
        unpaid = [k for k in to_2060 if not any(a[0] <= self.cm[k]["date"] for a in self.apps[self.cm[k]["inv"]])]
        both = sum(1 for p in self.parts.values() if p[0] > 0 and p[1] > 0)
        before_due = sum(1 for r in self.tests["before"] if r["date"] < self.inv[self.cm[r["cm"]]["inv"]]["due"])
        return dict(to_2060=len(to_2060), unpaid=len(unpaid), both=both, before_due=before_due)


_FACTS: dict[int, Facts] = {}


def facts(b: ExerciseBuild) -> Facts:
    if b.year not in _FACTS:
        _FACTS[b.year] = Facts(b.year)
    return _FACTS[b.year]


# --- worksheet helpers -----------------------------------------------------------------------------------------------

def notes_sheet(b: ExerciseBuild):
    for ws in b.wb.Worksheets:
        if ws.Name == notes.NOTES_SHEET:
            return ws
    return None


def new_sheet(b: ExerciseBuild, name: str):
    """A work sheet: before the query worksheets (or the Solution Notes), so the sheets follow the requirements."""
    anchor = next((ws for ws in b.wb.Worksheets if ws.Name in DATA_SHEETS), None) or notes_sheet(b)
    return xl.sheet(b.wb, name, before=anchor) if anchor is not None else xl.sheet(b.wb, name)


def data_anchor(b: ExerciseBuild):
    """The sheet a new query worksheet goes after: the last sheet before the Solution Notes, or the last sheet."""
    ns = notes_sheet(b)
    return b.wb.Worksheets(ns.Index - 1) if ns is not None else b.wb.Worksheets(b.wb.Worksheets.Count)


def load(b: ExerciseBuild, query: str):
    lo = xl.load_query(b.wb, query, query, after=data_anchor(b))
    xl.wait_ready(b.wb.Application)
    return lo


def put(ws, cells: dict) -> None:
    for addr, value in cells.items():
        if isinstance(value, str) and value.startswith("="):
            xl.retry(lambda a=addr, v=value: setattr(ws.Range(a), "Formula2", v))
        else:
            xl.retry(lambda a=addr, v=value: setattr(ws.Range(a), "Value", v))


def setp(obj, prop: str, value) -> None:
    """Set a COM property, retrying while Excel rejects the call because it is busy."""
    xl.retry(lambda: setattr(obj, prop, value))


def bold(ws, addr: str) -> None:
    setp(ws.Range(addr).Font, "Bold", True)


def fmt(ws, addr: str, number_format: str) -> None:
    setp(ws.Range(addr), "NumberFormat", number_format)


def title(ws, text: str, sub: str = "") -> None:
    put(ws, {"A1": text})
    setp(ws.Range("A1").Font, "Bold", True)
    setp(ws.Range("A1").Font, "Size", 13)
    if sub:
        put(ws, {"A2": sub})
        setp(ws.Range("A2").Font, "Italic", True)


def heading(ws, row: int, text: str, col: int = 1) -> None:
    cell = ws.Cells(row, col)
    setp(cell, "Value", text)
    setp(cell.Font, "Bold", True)
    setp(cell.Font, "Size", 12)


def header(ws, row: int, col: int, names: list) -> None:
    for i, name in enumerate(names):
        setp(ws.Cells(row, col + i), "Value", name)
    rng = ws.Range(ws.Cells(row, col), ws.Cells(row, col + len(names) - 1))
    setp(rng.Font, "Bold", True)
    setp(rng, "WrapText", True)
    setp(rng, "VerticalAlignment", -4160)


def widths(ws, spec: dict[str, float]) -> None:
    for col, w in spec.items():
        setp(ws.Columns(col), "ColumnWidth", w)


def text_block(ws, row: int, label: str, paragraphs: list[str], col: int = 1, span: int = 8) -> int:
    """A labeled block of wrapped text, one merged row per paragraph; returns the next free row (after a gap)."""
    setp(ws.Cells(row, col), "Value", label)
    setp(ws.Cells(row, col).Font, "Bold", True)
    width = sum(ws.Columns(col + i).ColumnWidth for i in range(span))
    r = row + 1
    for p in paragraphs:
        rng = ws.Range(ws.Cells(r, col), ws.Cells(r, col + span - 1))
        xl.retry(rng.Merge)
        setp(rng, "WrapText", True)
        setp(rng, "VerticalAlignment", -4160)                     # top
        setp(ws.Cells(r, col), "Value", p)
        lines = math.ceil(len(p) * 1.12 / max(width, 20)) + 0.4
        setp(ws.Rows(r), "RowHeight", min(409, max(15, 15 * lines)))
        r += 1
    return r + 1


def text_table(ws, row: int, col: int, names: list[str], rows: list[list]) -> int:
    """A table of wrapped text (a header and rows) with light borders; returns the next free row (after a gap)."""
    header(ws, row, col, names)
    for i, values in enumerate(rows, start=1):
        for j, v in enumerate(values):
            cell = ws.Cells(row + i, col + j)
            setp(cell, "Formula2" if isinstance(v, str) and v.startswith("=") else "Value", v)
    rng = ws.Range(ws.Cells(row, col), ws.Cells(row + len(rows), col + len(names) - 1))
    setp(rng, "WrapText", True)
    setp(rng, "VerticalAlignment", -4160)
    setp(rng.Borders, "LineStyle", 1)
    setp(rng.Borders, "Color", 0xDCD8D5)                  # #D5D8DC (BGR)
    xl.retry(rng.Rows.AutoFit)
    return row + len(rows) + 2


def serial(day: str) -> int:
    """A date as Excel's serial number (written with a date format, so no text is parsed)."""
    return (iso(day) - date(1899, 12, 30)).days


def paste(ws, row: int, col: int, rows: list[list], note: str, number_formats: dict[int, str] | None = None):
    """Values pasted from a Credits.sql query: an amber fill and a cell note that names the query."""
    if not rows:
        return None
    width = max(len(r) for r in rows)
    data = [list(r) + [None] * (width - len(r)) for r in rows]
    rng = ws.Range(ws.Cells(row, col), ws.Cells(row + len(rows) - 1, col + width - 1))
    rng.Value = tuple(tuple(r) for r in data)
    rng.Interior.Color = xl.LIGHT_FILL
    for j, f in (number_formats or {}).items():
        ws.Range(ws.Cells(row, col + j), ws.Cells(row + len(rows) - 1, col + j)).NumberFormat = f
    ws.Cells(row, col).AddComment(f"{PASTED}, query: {note}. Rerun the query and paste again if the data change.")
    return rng


def check_date(b: ExerciseBuild, t: str, label: str, day: str, addr: str) -> None:
    """A date checked as Excel's serial number (an expected value typed as text would be read as a date)."""
    b.check(t, label, serial(day), f"={addr}", 0, DATE)


def gl_f(side: str, acct, src: str | None = None, year: str | None = None, close: str | None = "FALSE",
         year_op: str = "") -> str:
    """A SUMIFS over the Ledger Table (without the =)."""
    col = "Debit" if side == "Dr" else "Credit"
    parts = [f"Ledger[{col}]", "Ledger[AccountNumber]", str(acct)]
    if src:
        parts += ["Ledger[SourceDocumentType]", f'"{src}"']
    if year:
        parts += ["Ledger[FiscalYear]", f'"{year_op}"&{year}' if year_op else year]
    if close:
        parts += ["Ledger[IsYearEndClose]", close]
    return "SUMIFS(" + ",".join(parts) + ")"


# --- the queries -----------------------------------------------------------------------------------------------------

def ordered(b: ExerciseBuild, table: str, columns: list[str]) -> list[str]:
    """Columns as Choose Columns keeps them: in the table's order."""
    order = [c for c, _ in pq.detected_types(b.xlsx, table)]
    missing = [c for c in columns if c not in order]
    assert not missing, f"{table} has no column {missing}"
    return sorted(columns, key=order.index)


def nav(b: ExerciseBuild, number: int, table: str, extra=()) -> str:
    return pq.navigator_query(b.src, number, table, list(pq.detected_types(b.xlsx, table)), None, list(extra))


def choose(b: ExerciseBuild, table: str, columns: list[str]) -> tuple[str, str]:
    return ("Removed Other Columns", pq.select_columns(ordered(b, table, columns)))


def expand_as(column: str, fields: list[str], names: list[str]) -> str:
    """Expand a merged column with new names (typed in the formula bar where a name would clash)."""
    a = "{" + ", ".join(pq.m_string(f) for f in fields) + "}"
    n = "{" + ", ".join(pq.m_string(f) for f in names) + "}"
    return f"Table.ExpandTableColumn({{prev}}, {pq.m_string(column)}, {a}, {n})"


def group(keys: list[str], aggs: list[tuple[str, str, str]]) -> str:
    k = "{" + ", ".join(pq.m_string(x) for x in keys) + "}"
    a = "{" + ", ".join("{" + f"{pq.m_string(n)}, each {e}, {t}" + "}" for n, e, t in aggs) + "}"
    return f"Table.Group({{prev}}, {k}, {a})"


def sort(cols: list[str]) -> str:
    return "Table.Sort({prev},{" + ", ".join("{" + f"{pq.m_string(c)}, Order.Ascending" + "}" for c in cols) + "})"


def remove(cols: list[str]) -> str:
    return "Table.RemoveColumns({prev},{" + ", ".join(pq.m_string(c) for c in cols) + "})"


def add_queries(b: ExerciseBuild) -> None:
    """The Power Query queries: staging queries (connection only) and the Tables the worksheets read."""
    wb = b.wb
    year_end = f"#datetime({b.year + 1}, 1, 1, 0, 0, 0)"
    q = lambda name, m: xl.add_query(wb, name, m)  # noqa: E731
    fiscal = lambda col: pq.add_custom("FiscalYear", f"Date.Year([{col}])")  # noqa: E731
    ids = 'Text.Combine(List.Transform(List.Sort(List.Distinct({col})), Text.From), ", ")'
    # staging queries (connection only)
    q("Accounts", nav(b, 1, "Account", [choose(b, "Account", ["AccountID", "AccountNumber", "AccountName",
                                                               "AccountType"])]))
    q("JournalEntries", nav(b, 2, "JournalEntry", [choose(b, "JournalEntry", ["EntryNumber", "EntryType"])]))
    q("Employees", nav(b, 74, "Employee", [choose(b, "Employee", ["EmployeeID", "JobTitle", "HireDate",
                                                                   "TerminationDate", "MaxApprovalAmount"])]))
    q("Receipts", nav(b, 19, "CashReceipt", [choose(b, "CashReceipt", [
        "CashReceiptID", "ReceiptNumber", "ReceiptDate", "CustomerID", "SalesInvoiceID", "Amount", "PaymentMethod",
        "DepositDate", "RecordedByEmployeeID"])]))
    q("Applications", nav(b, 20, "CashReceiptApplication", [
        ("Merged Queries", pq.merge("Receipts", "CashReceiptID", "CashReceiptID", "Receipts")),
        ("Expanded Receipts", pq.expand("Receipts", ["PaymentMethod", "RecordedByEmployeeID"]))]))
    q("InvoicePayments", pq.steps_query([
        ("Source", "Applications"),
        ("Grouped Rows", group(["SalesInvoiceID"], [
            ("FirstPayment", "List.Min([ApplicationDate])", "type nullable datetime"),
            ("LastPayment", "List.Max([ApplicationDate])", "type nullable datetime"),
            ("Methods", "List.Distinct([PaymentMethod])", "type list"),
            ("Appliers", "List.Distinct([AppliedByEmployeeID])", "type list"),
            ("Recorders", "List.Distinct([RecordedByEmployeeID])", "type list"),
            ("Applied", 'Table.ToRecords(Table.SelectColumns(_, {"ApplicationDate", "AppliedByEmployeeID"}))',
             "type list")]))]))
    q("CreditLines", nav(b, 24, "CreditMemoLine", [choose(b, "CreditMemoLine", ["CreditMemoLineID", "CreditMemoID",
                                                                                "LineTotal"])]))
    q("CreditLineCounts", pq.steps_query([
        ("Source", "CreditLines"),
        ("Grouped Rows", group(["CreditMemoID"], [("Lines", "Table.RowCount(_)", "Int64.Type")]))]))
    q("Returns", nav(b, 21, "SalesReturn", [choose(b, "SalesReturn", [
        "SalesReturnID", "ReturnNumber", "ReturnDate", "CustomerID", "ReceivedByEmployeeID", "ReasonCode", "Status"])]))
    q("Accruals", nav(b, 27, "SalesCommissionAccrual", [choose(b, "SalesCommissionAccrual", [
        "SalesCommissionAccrualID", "AccrualDate", "CommissionRatePct", "CommissionAmount", "CreatedByEmployeeID"])]))
    q("CommissionPayments", nav(b, 29, "SalesCommissionPayment", [
        choose(b, "SalesCommissionPayment", ["SalesCommissionPaymentID", "PaymentDate", "NetPaymentAmount",
                                             "ApprovedByEmployeeID"]),
        ("Added Custom", fiscal("PaymentDate")),
        ("Grouped Rows", group(["FiscalYear"], [
            ("Payments", "Table.RowCount(_)", "Int64.Type"),
            ("PaymentAmount", "List.Sum([NetPaymentAmount])", "type nullable number"),
            ("PaymentApprovers", ids.format(col="[ApprovedByEmployeeID]"), "type text")]))]))
    q("ApplicationsByYear", pq.steps_query([
        ("Source", "Applications"),
        ("Added Custom", fiscal("ApplicationDate")),
        ("Grouped Rows", group(["FiscalYear"], [
            ("Applications", "Table.RowCount(_)", "Int64.Type"),
            ("AppliedAmount", "List.Sum([AppliedAmount])", "type nullable number")]))]))
    for name, source, person, label, amount_col in (
            ("ReceiptsByTitle", "Receipts", "RecordedByEmployeeID", "Receipts recorded", "Amount"),
            ("ApplicationsByTitle", "Applications", "AppliedByEmployeeID", "Applications", "AppliedAmount")):
        q(name, pq.steps_query([
            ("Source", source),
            ("Merged Queries", pq.merge("Employees", person, "EmployeeID", "Employees")),
            ("Expanded Employees", pq.expand("Employees", ["JobTitle"])),
            ("Grouped Rows", group(["JobTitle"], [("Documents", "Table.RowCount(_)", "Int64.Type"),
                                                  ("Amount", f"List.Sum([{amount_col}])", "type nullable number")])),
            ("Added Custom", pq.add_custom("Document", pq.m_string(label))),
            ("Reordered Columns", 'Table.ReorderColumns({prev},{"Document", "JobTitle", "Documents", "Amount"})')]))

    # the Tables the worksheets read
    q("Ledger", nav(b, 3, "GLEntry", [
        ("Filtered Rows", f"Table.SelectRows({{prev}}, each [PostingDate] < {year_end})"),
        choose(b, "GLEntry", ["AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "FiscalYear"]),
        ("Merged Queries", pq.merge("Accounts", "AccountID", "AccountID", "Accounts")),
        ("Expanded Accounts", pq.expand("Accounts", ["AccountNumber", "AccountName", "AccountType"])),
        ("Merged Queries1", pq.merge("JournalEntries", "VoucherNumber", "EntryNumber", "JournalEntries")),
        ("Expanded JournalEntries", pq.expand("JournalEntries", ["EntryType"])),
        ("Added Custom", pq.add_custom("IsYearEndClose",
                                       '[EntryType] <> null and Text.StartsWith([EntryType], "Year-End Close")')),
        ("Grouped Rows", group(["FiscalYear", "AccountNumber", "AccountName", "AccountType", "SourceDocumentType",
                                "IsYearEndClose"], [
            ("Debit", "List.Sum([Debit])", "type nullable number"),
            ("Credit", "List.Sum([Credit])", "type nullable number"),
            ("Rows", "Table.RowCount(_)", "Int64.Type")])),
        ("Changed Type1", pq.transform_types([("IsYearEndClose", "type logical")])),
        ("Sorted Rows", sort(["FiscalYear", "AccountNumber", "SourceDocumentType", "IsYearEndClose"]))]))
    q("Credits", nav(b, 23, "CreditMemo", [
        choose(b, "CreditMemo", ["CreditMemoID", "CreditMemoNumber", "CreditMemoDate", "SalesReturnID", "CustomerID",
                                 "OriginalSalesInvoiceID", "SubTotal", "FreightCreditAmount", "TaxAmount", "GrandTotal",
                                 "Status", "ApprovedByEmployeeID"]),
        ("Merged Queries", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", expand_as("Employees", ["JobTitle", "HireDate", "TerminationDate", "MaxApprovalAmount"],
                                         ["ApproverTitle", "ApproverHireDate", "ApproverTerminationDate",
                                          "ApproverLimit"])),
        ("Merged Queries1", pq.merge("CreditLineCounts", "CreditMemoID", "CreditMemoID", "CreditLineCounts")),
        ("Expanded CreditLineCounts", pq.expand("CreditLineCounts", ["Lines"])),
        ("Merged Queries2", pq.merge("InvoicePayments", "OriginalSalesInvoiceID", "SalesInvoiceID",
                                     "InvoicePayments")),
        ("Expanded InvoicePayments", pq.expand("InvoicePayments", ["Appliers", "Recorders", "Applied"])),
        ("Added Custom", fiscal("CreditMemoDate")),
        ("Added Custom1", pq.add_custom("AboveLimit", "[GrandTotal] > [ApproverLimit]")),
        ("Added Custom2", pq.add_custom("CashAndCredit",
                                        "[Appliers] <> null and List.Contains([Appliers], [ApprovedByEmployeeID])")),
        ("Added Custom3", pq.add_custom("AppliedByCreditDate",
                                        "let a = [ApprovedByEmployeeID], d = [CreditMemoDate] in [Applied] <> null and "
                                        "List.MatchesAny([Applied], each [AppliedByEmployeeID] = a and "
                                        "[ApplicationDate] <= d)")),
        ("Added Custom4", pq.add_custom("HandledCash", "[Appliers] <> null and "
                                        "List.Contains([Appliers] & [Recorders], [ApprovedByEmployeeID])")),
        ("Added Custom5", pq.add_custom("OutsideEmployment", "[CreditMemoDate] < [ApproverHireDate] or "
                                        "([ApproverTerminationDate] <> null and "
                                        "[CreditMemoDate] > [ApproverTerminationDate])")),
        ("Removed Columns", remove(["ApproverHireDate", "ApproverTerminationDate", "Appliers", "Recorders",
                                    "Applied"])),
        ("Changed Type1", pq.transform_types([("Lines", "Int64.Type"), ("FiscalYear", "Int64.Type"),
                                              ("AboveLimit", "type logical"), ("CashAndCredit", "type logical"),
                                              ("AppliedByCreditDate", "type logical"), ("HandledCash", "type logical"),
                                              ("OutsideEmployment", "type logical")])),
        ("Sorted Rows", sort(["CreditMemoID"]))]))
    q("Refunds", nav(b, 25, "CustomerRefund", [
        choose(b, "CustomerRefund", ["CustomerRefundID", "RefundNumber", "RefundDate", "CustomerID", "CreditMemoID",
                                     "Amount", "PaymentMethod", "ApprovedByEmployeeID", "ClearedDate"]),
        ("Merged Queries", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", expand_as("Employees", ["JobTitle", "HireDate", "TerminationDate", "MaxApprovalAmount"],
                                         ["ApproverTitle", "ApproverHireDate", "ApproverTerminationDate",
                                          "ApproverLimit"])),
        ("Merged Queries1", pq.merge("Credits", "CreditMemoID", "CreditMemoID", "Credits")),
        ("Expanded Credits", expand_as("Credits", ["CreditMemoNumber", "CreditMemoDate", "OriginalSalesInvoiceID",
                                                   "ApprovedByEmployeeID", "AboveLimit"],
                                       ["CreditMemoNumber", "CreditMemoDate", "OriginalSalesInvoiceID",
                                        "CreditApproverID", "CreditAboveLimit"])),
        ("Merged Queries2", pq.merge("InvoicePayments", "OriginalSalesInvoiceID", "SalesInvoiceID",
                                     "InvoicePayments")),
        ("Expanded InvoicePayments", pq.expand("InvoicePayments", ["FirstPayment", "LastPayment", "Methods"])),
        ("Added Custom", fiscal("RefundDate")),
        ("Added Custom1", pq.add_custom("AboveLimit", "[Amount] > [ApproverLimit]")),
        ("Added Custom2", pq.add_custom("BeforePayment", "[LastPayment] <> null and [LastPayment] > [RefundDate]")),
        ("Added Custom3", pq.add_custom("BeforeAnyPayment", "[FirstPayment] = null or [FirstPayment] > [RefundDate]")),
        ("Added Custom4", pq.add_custom("MethodMismatch",
                                        "[Methods] = null or not List.Contains([Methods], [PaymentMethod])")),
        ("Added Custom5", pq.add_custom("ReceiptMethods",
                                        'if [Methods] = null then "" else Text.Combine(List.Sort([Methods]), ", ")')),
        ("Added Custom6", pq.add_custom("DaysToLastPayment", "if [LastPayment] = null then null else "
                                                             "Duration.Days([LastPayment] - [RefundDate])")),
        ("Added Custom7", pq.add_custom("SameApprover", "[ApprovedByEmployeeID] = [CreditApproverID]")),
        ("Added Custom8", pq.add_custom("OutsideEmployment", "[RefundDate] < [ApproverHireDate] or "
                                        "([ApproverTerminationDate] <> null and [RefundDate] > [ApproverTerminationDate])")),
        ("Removed Columns", remove(["ApproverHireDate", "ApproverTerminationDate", "Methods"])),
        ("Changed Type1", pq.transform_types([("FiscalYear", "Int64.Type"), ("CreditAboveLimit", "type logical"),
                                              ("AboveLimit", "type logical"), ("BeforePayment", "type logical"),
                                              ("BeforeAnyPayment", "type logical"), ("MethodMismatch", "type logical"),
                                              ("ReceiptMethods", "type text"), ("DaysToLastPayment", "Int64.Type"),
                                              ("SameApprover", "type logical"), ("OutsideEmployment", "type logical")])),
        ("Sorted Rows", sort(["CustomerRefundID"]))]))
    q("ReturnLines", nav(b, 22, "SalesReturnLine", [
        choose(b, "SalesReturnLine", ["SalesReturnLineID", "SalesReturnID", "ShipmentLineID", "ItemID",
                                      "QuantityReturned", "ExtendedStandardCost"]),
        ("Merged Queries", pq.merge("Returns", "SalesReturnID", "SalesReturnID", "Returns")),
        ("Expanded Returns", pq.expand("Returns", ["ReturnNumber", "ReturnDate", "CustomerID", "ReceivedByEmployeeID",
                                                   "ReasonCode", "Status"])),
        ("Merged Queries1", pq.merge("Employees", "ReceivedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", expand_as("Employees", ["JobTitle"], ["ReceiverTitle"])),
        ("Added Custom", fiscal("ReturnDate")),
        ("Changed Type1", pq.transform_types([("FiscalYear", "Int64.Type")])),
        ("Sorted Rows", sort(["SalesReturnLineID"]))]))
    q("Clawbacks", nav(b, 28, "SalesCommissionAdjustment", [
        choose(b, "SalesCommissionAdjustment", ["SalesCommissionAdjustmentID", "AdjustmentNumber", "AdjustmentDate",
                                                "SalesCommissionAccrualID", "CreditMemoID", "CreditMemoLineID",
                                                "CommissionBaseReductionAmount", "CommissionRatePct",
                                                "CommissionAdjustmentAmount", "ApprovedByEmployeeID"]),
        ("Merged Queries", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", expand_as("Employees", ["JobTitle"], ["ApproverTitle"])),
        ("Merged Queries1", pq.merge("Credits", "CreditMemoID", "CreditMemoID", "Credits")),
        ("Expanded Credits", expand_as("Credits", ["CreditMemoDate", "ApprovedByEmployeeID"],
                                       ["CreditMemoDate", "CreditApproverID"])),
        ("Merged Queries2", pq.merge("CreditLines", "CreditMemoLineID", "CreditMemoLineID", "CreditLines")),
        ("Expanded CreditLines", pq.expand("CreditLines", ["LineTotal"])),
        ("Merged Queries3", pq.merge("Accruals", "SalesCommissionAccrualID", "SalesCommissionAccrualID", "Accruals")),
        ("Expanded Accruals", expand_as("Accruals", ["CommissionRatePct"], ["AccrualRatePct"])),
        ("Added Custom", fiscal("AdjustmentDate")),
        ("Added Custom1", pq.add_custom("BaseMatches", "[LineTotal] <> null and "
                                        "Number.Abs([CommissionBaseReductionAmount] - [LineTotal]) < 0.005")),
        ("Added Custom2", pq.add_custom("RateMatches", "[AccrualRatePct] <> null and "
                                        "Number.Abs([CommissionRatePct] - [AccrualRatePct]) < 0.000000001")),
        ("Added Custom3", pq.add_custom("SameAsCredit", "[AdjustmentDate] = [CreditMemoDate] and "
                                        "[ApprovedByEmployeeID] = [CreditApproverID]")),
        ("Changed Type1", pq.transform_types([("FiscalYear", "Int64.Type"), ("BaseMatches", "type logical"),
                                              ("RateMatches", "type logical"), ("SameAsCredit", "type logical")])),
        ("Sorted Rows", sort(["AdjustmentNumber"]))]))
    q("CashByYear", pq.steps_query([
        ("Source", "Receipts"),
        ("Added Custom", fiscal("ReceiptDate")),
        ("Grouped Rows", group(["FiscalYear"], [
            ("Receipts", "Table.RowCount(_)", "Int64.Type"),
            ("ReceiptAmount", "List.Sum([Amount])", "type nullable number"),
            ("FirstReceipt", "List.Min([ReceiptDate])", "type nullable datetime"),
            ("LastReceipt", "List.Max([ReceiptDate])", "type nullable datetime")])),
        ("Merged Queries", pq.merge("ApplicationsByYear", "FiscalYear", "FiscalYear", "ApplicationsByYear")),
        ("Expanded ApplicationsByYear", pq.expand("ApplicationsByYear", ["Applications", "AppliedAmount"])),
        ("Sorted Rows", sort(["FiscalYear"]))]))
    q("CashHandlers", pq.steps_query([
        ("Source", "Table.Combine({ReceiptsByTitle, ApplicationsByTitle})"),
        ("Sorted Rows", sort(["Document", "JobTitle"]))]))
    q("CommissionByYear", pq.steps_query([
        ("Source", "Accruals"),
        ("Added Custom", fiscal("AccrualDate")),
        ("Grouped Rows", group(["FiscalYear"], [
            ("Accruals", "Table.RowCount(_)", "Int64.Type"),
            ("AccrualAmount", "List.Sum([CommissionAmount])", "type nullable number"),
            ("AccrualCreators", ids.format(col="[CreatedByEmployeeID]"), "type text")])),
        ("Merged Queries", pq.merge("CommissionPayments", "FiscalYear", "FiscalYear", "CommissionPayments")),
        ("Expanded CommissionPayments", pq.expand("CommissionPayments", ["Payments", "PaymentAmount",
                                                                         "PaymentApprovers"])),
        ("Sorted Rows", sort(["FiscalYear"]))]))
    q("CommissionRates", nav(b, 26, "SalesCommissionRate", [
        choose(b, "SalesCommissionRate", ["SalesCommissionRateID", "RevenueType", "CustomerSegment", "RatePct",
                                          "EffectiveStartDate", "EffectiveEndDate", "Status", "ApprovedByEmployeeID"]),
        ("Merged Queries", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", expand_as("Employees", ["JobTitle"], ["ApproverTitle"]))]))


LOADED = {   # query -> {column: number format}
    "Ledger": {"Debit": MONEY, "Credit": MONEY, "Rows": COUNT},
    "Credits": {"CreditMemoDate": DATE, "SubTotal": MONEY, "FreightCreditAmount": MONEY, "TaxAmount": MONEY,
                "GrandTotal": MONEY, "ApproverLimit": COUNT},
    "Refunds": {"RefundDate": DATE, "Amount": MONEY, "ClearedDate": DATE, "ApproverLimit": COUNT,
                "CreditMemoDate": DATE, "FirstPayment": DATE, "LastPayment": DATE},
    "ReturnLines": {"ExtendedStandardCost": MONEY, "ReturnDate": DATE},
    "Clawbacks": {"AdjustmentDate": DATE, "CreditMemoDate": DATE, "CommissionBaseReductionAmount": MONEY,
                  "CommissionAdjustmentAmount": MONEY, "LineTotal": MONEY},
    "CashByYear": {"ReceiptAmount": MONEY, "FirstReceipt": DATE, "LastReceipt": DATE, "AppliedAmount": MONEY},
    "CashHandlers": {"Amount": MONEY, "Documents": COUNT},
    "CommissionByYear": {"AccrualAmount": MONEY, "PaymentAmount": MONEY, "Accruals": COUNT},
    "CommissionRates": {"EffectiveStartDate": DATE, "EffectiveEndDate": DATE},
}


def load_all(b: ExerciseBuild) -> None:
    for name, formats in LOADED.items():
        start = time.time()
        lo = load(b, name)
        print(f"    loaded {name} in {time.time() - start:.0f}s", flush=True)
        for col, f in formats.items():
            lo.ListColumns(col).DataBodyRange.NumberFormat = f
        lo.Range.Worksheet.Columns.AutoFit()


def merged_table(ws, row: int, spans: list[int], names: list[str], rows: list[list], col: int = 1) -> int:
    """A table whose text cells span several worksheet columns (merged), with wrapped text and row heights estimated
    from the longest cell; formulas are written as formulas. Returns the next free row (after a gap)."""
    starts = [col + sum(spans[:i]) for i in range(len(spans))]
    widths_ = [sum(ws.Columns(s + k).ColumnWidth for k in range(n)) for s, n in zip(starts, spans)]

    def write(r: int, values: list, is_header: bool) -> None:
        lines = 1
        for s, n, w, v in zip(starts, spans, widths_, values):
            rng = ws.Range(ws.Cells(r, s), ws.Cells(r, s + n - 1))
            if n > 1:
                xl.retry(rng.Merge)
            setp(rng, "WrapText", True)
            setp(rng, "VerticalAlignment", -4160)
            cell = ws.Cells(r, s)
            if isinstance(v, str) and v.startswith("="):
                setp(cell, "Formula2", v)
            else:
                setp(cell, "Value", v)
                lines = max(lines, math.ceil(len(str(v)) * 1.15 / max(w, 8)))
        setp(ws.Rows(r), "RowHeight", min(409, max(15, 15 * lines + 2)))
        if is_header:
            setp(ws.Range(ws.Cells(r, col), ws.Cells(r, starts[-1] + spans[-1] - 1)).Font, "Bold", True)

    write(row, names, True)
    for i, values in enumerate(rows, start=1):
        write(row + i, values, False)
    rng = ws.Range(ws.Cells(row, col), ws.Cells(row + len(rows), starts[-1] + spans[-1] - 1))
    setp(rng.Borders, "LineStyle", 1)
    setp(rng.Borders, "Color", 0xDCD8D5)                  # #D5D8DC (BGR)
    return row + len(rows) + 2


# --- Requirement 1: the Documentation worksheet, the queries, and the map of the cycle --------------------------------

SHEETS = [
    ("Documentation", "Purpose, sources, preparer, the date through which the data run, and this index", "Getting Started"),
    ("Cycle Map", "Populations, statuses, who records each document, the posting matrix, numbering, and what the records "
                  "evidence at each control point (appendix: the map of the cycle)", "Requirement 1"),
    ("Reconciliation", "Each population against the ledger by fiscal year, 2060 rolled forward with its items, 2034 at the "
                       "end of fiscal 2026, and what was excluded (appendix: the reconciliation by year)", "Requirement 2"),
    ("Materiality", "Materiality, performance materiality, clearly trivial, and the expectation of returns", "Requirement 3"),
    ("Risks", "The fraud brainstorm and the risk-and-control matrix", "Requirement 3"),
    ("Tests", "The control tests on every document, by year, the combined exception list, and the refund flags "
              "reconciled to RefundFlags (appendix: the test results)", "Requirement 4"),
    ("Sample", "Attributes, parameters, key items, the frozen random selection, the evaluation rule, and the data "
               "attribute applied to the sample (appendix: the sample plan)", "Requirement 6"),
    ("Timeline", "The largest refund from shipment to the last receipt, its disposition, the restocking by reason, and the "
                 "substantive and lapping results", "Requirement 7"),
    ("Deficiencies", "The evaluation matrix against the materiality cells, the combined classification, and the clean "
                     "results (appendix: the evaluation of deficiencies)", "Requirement 8"),
    ("Report", "The report to the audit committee and the action plans (model answer)", "Requirement 9"),
    ("Ledger ... CommissionRates", "Power Query Tables from CharlesRiver.xlsx (refresh with Data > Refresh All)",
     "Requirements 1 to 8"),
    ("RefundFlags", "The refund flags of Credits.sql (RefundFlags.csv), pasted as values", "Requirement 4"),
]


def documentation(b: ExerciseBuild, ws) -> int:
    f = facts(b)
    widths(ws, {"A": 34, "B": 100, "C": 26})
    title(ws, "Credits Audit.xlsx: Documentation")
    rows = [
        ("Purpose", "Internal audit of the customer credits cycle (sales returns, credit memos, customer refunds, "
                    "commission clawbacks, and cash application): materiality, the risk-and-control matrix, the sample, "
                    "and the evaluation of deficiencies, with the tables for the appendix of the report to the audit "
                    "committee's November meeting."),
        ("Scope", f"Analytics and tests of controls over fiscal {f.F} to {f.C}; conclusions on controls as at the end of "
                  f"fiscal {f.C}. Magnitude is judged against 5% of fiscal {f.C} income before income taxes as the ledger "
                  "records it (Materiality worksheet)."),
        ("Sources", "CharlesRiver.xlsx, imported with Power Query: T1_Account, T2_JournalEntry, T3_GLEntry (Transform "
                    f"Data, filtered to postings before {f.C + 1}-01-01 first), T19_CashReceipt, "
                    "T20_CashReceiptApplication, T21_SalesReturn, T22_SalesReturnLine, T23_CreditMemo, T24_CreditMemoLine, "
                    "T25_CustomerRefund, T26_SalesCommissionRate, T27_SalesCommissionAccrual, "
                    "T28_SalesCommissionAdjustment, T29_SalesCommissionPayment, and T74_Employee. Data > Refresh All "
                    "updates every Table and formula."),
        ("Pasted values", "Cells with an amber fill hold values pasted from Credits.sql (run on "
                          "CharlesRiver_Capstone.sqlite), each with a cell note that names its query: what M cannot "
                          "compute reasonably (balances as of each refund date, the items in 2060, the timeline, the "
                          "substantive and lapping results). They do not refresh; rerun the query and paste again."),
        ("Written parts", f"Text labeled \"{MA}\" is the instructor's model answer; reasoned alternatives are accepted."),
        ("Prepared by", "Accounting Analytics instructor solution; replace with your name and the date."),
        ("Reviewed by", ""),
    ]
    r = 3
    for label, text in rows:
        put(ws, {f"A{r}": label, f"B{r}": text})
        bold(ws, f"A{r}")
        ws.Range(f"B{r}").WrapText = True
        r += 1
    r += 1
    heading(ws, r, "The date through which the data run")
    r += 1
    first = r
    dates = [("Fiscal years in the analysis", '=MIN(Ledger[FiscalYear])&" to "&MAX(Ledger[FiscalYear])', None),
             ("Ledger postings used, through", "=DATE(MAX(Ledger[FiscalYear]),12,31)", DATE),
             ("Last sales return", "=MAX(ReturnLines[ReturnDate])", DATE),
             ("Last credit memo", "=MAX(Credits[CreditMemoDate])", DATE),
             ("Last commission clawback", "=MAX(Clawbacks[AdjustmentDate])", DATE),
             ("Last customer refund", "=MAX(Refunds[RefundDate])", DATE),
             ("Last cash receipt", "=MAX(CashByYear[LastReceipt])", DATE)]
    for label, formula, nf in dates:
        put(ws, {f"A{r}": label, f"B{r}": formula})
        if nf:
            fmt(ws, f"B{r}", nf)
        ws.Range(f"B{r}").HorizontalAlignment = -4131
        r += 1
    last_cm = max(m["date"] for m in f.cm.values())
    last_rf = max(x["date"] for x in f.rf.values())
    put(ws, {f"A{r}": "Statement",
             f"B{r}": f"The data run through {f.C}-12-31, the end of fiscal {f.C}. The ledger extract continues into "
                      f"{f.C + 1} with supplier payments only, which the Ledger query leaves out. The cycle's last "
                      f"documents are a credit memo of {last_cm[:10]} and a refund of {last_rf[:10]}: returns of late "
                      f"{f.C} shipments and the {f.C + 1} refunds of {f.C} credits are not in the data, so rates for the "
                      f"last months are incomplete (the case's second Watch out)."})
    bold(ws, f"A{first}:A{r}")
    ws.Range(f"B{r}").WrapText = True
    b.found["doc_dates"] = first
    r += 2
    heading(ws, r, "Worksheets")
    r = text_table(ws, r + 1, 1, ["Worksheet", "Holds", "Requirement"], [list(x) for x in SHEETS])
    ws.Columns("A:C").VerticalAlignment = -4160
    return first


def r1(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    t = "Requirement 1"
    doc = wb.Worksheets(1)
    doc.Name = "Documentation"
    add_queries(b)
    load_all(b)
    d0 = documentation(b, doc)
    ws = new_sheet(b, "Cycle Map")
    widths(ws, {"A": 30, "B": 30, "C": 14, "D": 12, "E": 12, "F": 12, "G": 16, "H": 12, "I": 12, "J": 12, "K": 12,
                "L": 12, "M": 12, "N": 12, "O": 12})
    title(ws, "Requirement 1: The cycle mapped from its records",
          "Live formulas on the query Tables; the posting matrix sums the Ledger Table over all fiscal years, closes "
          "excluded.")

    # A. populations
    heading(ws, 4, "Populations")
    header(ws, 5, 1, ["Document", "Table", "Documents", "Lines", "First date", "Last date", "Amount", "Customers"])
    pops = [
        ("Sales returns", "SalesReturn, SalesReturnLine", "=ROWS(UNIQUE(ReturnLines[ReturnNumber]))", "=ROWS(ReturnLines)",
         "=MIN(ReturnLines[ReturnDate])", "=MAX(ReturnLines[ReturnDate])", "=SUM(ReturnLines[ExtendedStandardCost])",
         "=ROWS(UNIQUE(ReturnLines[CustomerID]))"),
        ("Credit memos", "CreditMemo, CreditMemoLine", "=ROWS(Credits)", "=SUM(Credits[Lines])",
         "=MIN(Credits[CreditMemoDate])", "=MAX(Credits[CreditMemoDate])", "=SUM(Credits[GrandTotal])",
         "=ROWS(UNIQUE(Credits[CustomerID]))"),
        ("Customer refunds", "CustomerRefund", "=ROWS(Refunds)", "", "=MIN(Refunds[RefundDate])",
         "=MAX(Refunds[RefundDate])", "=SUM(Refunds[Amount])", "=ROWS(UNIQUE(Refunds[CustomerID]))"),
        ("Commission clawbacks", "SalesCommissionAdjustment", "=ROWS(Clawbacks)", "", "=MIN(Clawbacks[AdjustmentDate])",
         "=MAX(Clawbacks[AdjustmentDate])", "=SUM(Clawbacks[CommissionAdjustmentAmount])", ""),
        ("Cash receipts", "CashReceipt", "=SUM(CashByYear[Receipts])", "", "=MIN(CashByYear[FirstReceipt])",
         "=MAX(CashByYear[LastReceipt])", "=SUM(CashByYear[ReceiptAmount])", ""),
        ("Cash applications", "CashReceiptApplication", "=SUM(CashByYear[Applications])", "", "", "",
         "=SUM(CashByYear[AppliedAmount])", ""),
    ]
    for i, row in enumerate(pops):
        r = 6 + i
        for j, v in enumerate(row):
            if v:
                put(ws, {f"{letter(1 + j)}{r}": v})
    fmt(ws, "C6:D11", COUNT)
    fmt(ws, "E6:F11", DATE)
    fmt(ws, "G6:G11", MONEY)
    fmt(ws, "H6:H11", COUNT)
    put(ws, {"A12": "Returns are valued at standard cost (ExtendedStandardCost); the other amounts are document totals."})
    ws.Range("A12").Font.Italic = True
    srs = list(f.sr.values())
    cms = list(f.cm.values())
    rfs = list(f.rf.values())
    b.check(t, "sales returns", len(srs), "='Cycle Map'!C6", 0, COUNT)
    b.check(t, "sales return lines", len(f.srl), "='Cycle Map'!D6", 0, COUNT)
    check_date(b, t, "first return", min(s["date"] for s in srs)[:10], "'Cycle Map'!E6")
    check_date(b, t, "last return", max(s["date"] for s in srs)[:10], "'Cycle Map'!F6")
    b.check(t, "returns at standard cost", r2(sum(l["std"] for l in f.srl)), "='Cycle Map'!G6")
    b.check(t, "customers with returns", len({s["cust"] for s in srs}), "='Cycle Map'!H6", 0, COUNT)
    b.check(t, "credit memos", len(cms), "='Cycle Map'!C7", 0, COUNT)
    b.check(t, "credit memo lines", len(f.cm_lines), "='Cycle Map'!D7", 0, COUNT)
    check_date(b, t, "first credit", min(m["date"] for m in cms)[:10], "'Cycle Map'!E7")
    check_date(b, t, "last credit", max(m["date"] for m in cms)[:10], "'Cycle Map'!F7")
    b.check(t, "credit memo total", r2(sum(m["gt"] for m in cms)), "='Cycle Map'!G7")
    b.check(t, "refunds", len(rfs), "='Cycle Map'!C8", 0, COUNT)
    check_date(b, t, "first refund", min(x["date"] for x in rfs)[:10], "'Cycle Map'!E8")
    check_date(b, t, "last refund", max(x["date"] for x in rfs)[:10], "'Cycle Map'!F8")
    b.check(t, "refund total", r2(sum(x["amt"] for x in rfs)), "='Cycle Map'!G8")
    b.check(t, "clawbacks", len(f.adj), "='Cycle Map'!C9", 0, COUNT)
    b.check(t, "clawback total", r2(sum(a["amt"] for a in f.adj)), "='Cycle Map'!G9")
    b.check(t, "cash receipts", len(f.rcpt), "='Cycle Map'!C10", 0, COUNT)
    b.check(t, "cash receipt total", r2(sum(x["amt"] for x in f.rcpt.values())), "='Cycle Map'!G10")
    b.check(t, "cash applications", len(f.all_apps), "='Cycle Map'!C11", 0, COUNT)

    # B. statuses and reasons
    heading(ws, 14, "Statuses and reasons")
    header(ws, 15, 1, ["Document", "Status or reason", "Documents", "Amount"])
    r = 16
    stat_rows = []
    for status in sorted({s["status"] for s in srs}):
        stat_rows.append(("Sales returns", status,
                          f'=ROWS(UNIQUE(FILTER(ReturnLines[ReturnNumber],ReturnLines[Status]="{status}")))', "",
                          sum(1 for s in srs if s["status"] == status), None))
    for reason in sorted({s["reason"] for s in srs}, key=lambda x: -sum(1 for s in srs if s["reason"] == x)):
        stat_rows.append(("Sales returns, reason", reason,
                          f'=ROWS(UNIQUE(FILTER(ReturnLines[ReturnNumber],ReturnLines[ReasonCode]="{reason}")))', "",
                          sum(1 for s in srs if s["reason"] == reason), None))
    for status in sorted({m["status"] for m in cms}, key=lambda x: -sum(1 for m in cms if m["status"] == x)):
        stat_rows.append(("Credit memos", status, f'=COUNTIF(Credits[Status],"{status}")',
                          f'=SUMIFS(Credits[GrandTotal],Credits[Status],"{status}")',
                          sum(1 for m in cms if m["status"] == status),
                          r2(sum(m["gt"] for m in cms if m["status"] == status))))
    for doc_, label, cnt, total, n, a in stat_rows:
        put(ws, {f"A{r}": doc_, f"B{r}": label, f"C{r}": cnt})
        if total:
            put(ws, {f"D{r}": total})
        b.check(t, f"{doc_.lower()}: {label}", n, f"='Cycle Map'!C{r}", 0, COUNT)
        if a is not None:
            b.check(t, f"{doc_.lower()}: {label}, amount", a, f"='Cycle Map'!D{r}")
        r += 1
    fmt(ws, f"C16:C{r}", COUNT)
    fmt(ws, f"D16:D{r}", MONEY)

    # C. who records each document
    r += 1
    heading(ws, r, "Who records each document, by job title")
    r += 1
    header(ws, r, 1, ["Document and role", "Job title", "Documents", "Cost center of the role"])
    r += 1
    who_rows = []
    recv = Counter(f.title(s["recv"]) for s in srs)
    for ti, n in sorted(recv.items(), key=lambda kv: -kv[1]):
        who_rows.append(("Sales returns, received by", ti,
                         f'=ROWS(UNIQUE(FILTER(ReturnLines[ReturnNumber],ReturnLines[ReceiverTitle]="{ti}")))', n,
                         "Warehouse"))
    for label, items, key, table in (("Credit memos, approved by", cms, "appr", "Credits"),
                                     ("Commission clawbacks, approved by", f.adj, "appr", "Clawbacks"),
                                     ("Customer refunds, approved by", rfs, "appr", "Refunds")):
        cnt = Counter(f.title(x[key]) for x in items)
        for ti, n in sorted(cnt.items(), key=lambda kv: -kv[1]):
            who_rows.append((label, ti, f'=COUNTIF({table}[ApproverTitle],"{ti}")', n,
                             "Customer Service" if table != "Refunds" else "Administration"))
    for label, items, doc_label in (("Cash receipts, recorded by", [x["rec"] for x in f.rcpt.values()],
                                     "Receipts recorded"),
                                    ("Cash applications, applied by", [a[3] for a in f.all_apps], "Applications")):
        cnt = Counter(f.title(e) for e in items)
        for ti, n in sorted(cnt.items(), key=lambda kv: -kv[1]):
            who_rows.append((label, ti, f'=SUMIFS(CashHandlers[Documents],CashHandlers[Document],"{doc_label}",'
                                        f'CashHandlers[JobTitle],"{ti}")', n, "Customer Service"))
    rates_by = Counter(f.title(e) for e in f.commission["rate_approvers"])
    for ti in rates_by:
        who_rows.append(("Commission rates, approved by", ti, f'=COUNTIF(CommissionRates[ApproverTitle],"{ti}")',
                         f.commission["n_rates"], "Administration"))
    w0 = r
    for label, ti, formula, n, center in who_rows:
        put(ws, {f"A{r}": label, f"B{r}": ti, f"C{r}": formula, f"D{r}": center})
        b.check(t, f"{label.lower()} {ti}", n, f"='Cycle Map'!C{r}", 0, COUNT)
        r += 1
    fmt(ws, f"C{w0}:C{r}", COUNT)
    put(ws, {f"A{r}": "GLEntry.CreatedByEmployeeID names the document's approver, recorder, or applier on every row of "
                      "the cycle (and the chief executive on every sales invoice row), and neither CreditMemo nor "
                      "CustomerRefund has a preparer column: the records cannot show who prepared a credit or a refund."})
    ws.Range(f"A{r}").Font.Italic = True
    r += 2

    # D. the posting matrix
    heading(ws, r, "Ledger postings by source document and account (debits positive, credits negative)")
    r += 1
    m_head = r
    put(ws, {f"A{r}": "Source document"})
    for j, a in enumerate(MATRIX_ACCOUNTS):
        ws.Cells(r, 2 + j).Value = int(a)
    bold(ws, f"A{r}:{letter(1 + len(MATRIX_ACCOUNTS))}{r}")
    r += 1
    rows_head = r + len(SOURCES) + 1
    put(ws, {f"A{rows_head}": "GL rows"})
    for j, a in enumerate(MATRIX_ACCOUNTS):
        ws.Cells(rows_head, 2 + j).Value = int(a)
    bold(ws, f"A{rows_head}:{letter(1 + len(MATRIX_ACCOUNTS))}{rows_head}")
    for i, src in enumerate(SOURCES):
        ra, rr = r + i, rows_head + 1 + i
        put(ws, {f"A{ra}": src, f"A{rr}": src})
        for j, a in enumerate(MATRIX_ACCOUNTS):
            c = letter(2 + j)
            ws.Range(f"{c}{ra}").Formula2 = (f"=SUMIFS(Ledger[Debit],Ledger[SourceDocumentType],$A{ra},Ledger[AccountNumber],"
                                             f"{c}${m_head})-SUMIFS(Ledger[Credit],Ledger[SourceDocumentType],$A{ra},"
                                             f"Ledger[AccountNumber],{c}${m_head})")
            ws.Range(f"{c}{rr}").Formula2 = (f"=SUMIFS(Ledger[Rows],Ledger[SourceDocumentType],$A{rr},"
                                             f"Ledger[AccountNumber],{c}${rows_head})")
            dr, cr = f.gl_sum("Dr", a, src, close=None), f.gl_sum("Cr", a, src, close=None)
            n = f.gl_rows(a, src)
            if n:
                b.check(t, f"{src} postings to {a}, debits less credits", r2(dr - cr), f"='Cycle Map'!{c}{ra}")
                if src in ("CreditMemo", "CashReceipt", "CashReceiptApplication", "CustomerRefund"):
                    b.check(t, f"{src} GL rows on {a}", n, f"='Cycle Map'!{c}{rr}", 0, COUNT)
    last_col = letter(1 + len(MATRIX_ACCOUNTS))
    fmt(ws, f"B{r}:{last_col}{r + len(SOURCES) - 1}", '#,##0.00;-#,##0.00;""')
    fmt(ws, f"B{rows_head + 1}:{last_col}{rows_head + len(SOURCES)}", '#,##0;-#,##0;""')
    r = rows_head + len(SOURCES) + 2
    put(ws, {f"A{r}": "Credits post to receivables (1020), to customer deposits (2060), or to both: "
                      f"{f.cause['both']} credits post to both. Every receipt passes through 2060 on its way to "
                      "1020, and every refund is paid out of 2060."})
    ws.Range(f"A{r}").Font.Italic = True
    r += 2

    # E. numbering
    heading(ws, r, "Document numbers: first, last, count, and gaps by year")
    r += 1
    header(ws, r, 1, ["Document", "Year", "First", "Last", "Numbers", "Gaps", "Continues the year before"])
    r += 1
    n0 = r
    nums = [("Sales returns", "ReturnLines[ReturnNumber]", [s["num"] for s in srs]),
            ("Credit memos", "Credits[CreditMemoNumber]", [m["num"] for m in cms]),
            ("Customer refunds", "Refunds[RefundNumber]", [x["num"] for x in rfs]),
            ("Commission clawbacks", "Clawbacks[AdjustmentNumber]", [a["num"] for a in f.adj])]
    for label, rng, values in nums:
        seqs = defaultdict(list)
        for v in values:
            _, y, s = v.rsplit("-", 2)
            seqs[int(y)].append(int(s))
        for k, y in enumerate(f.years):
            let = (f'LET(n,UNIQUE({rng}),y,--TEXTBEFORE(TEXTAFTER(n,"-"),"-"),s,--TEXTAFTER(n,"-",-1),'
                   f'FILTER(s,y=$B{r}))')
            put(ws, {f"A{r}": label, f"B{r}": y, f"C{r}": f"=MIN({let})", f"D{r}": f"=MAX({let})",
                     f"E{r}": f"=ROWS({let})", f"F{r}": f"=D{r}-C{r}+1-E{r}",
                     f"G{r}": "" if k == 0 else f'=IF(C{r}=D{r - 1}+1,"Yes","No")'})
            s = sorted(seqs[y])
            b.check(t, f"{label.lower()} {y}: first number", s[0], f"='Cycle Map'!C{r}", 0, COUNT)
            b.check(t, f"{label.lower()} {y}: last number", s[-1], f"='Cycle Map'!D{r}", 0, COUNT)
            b.check(t, f"{label.lower()} {y}: gaps", s[-1] - s[0] + 1 - len(set(s)), f"='Cycle Map'!F{r}", 0, COUNT)
            r += 1
    fmt(ws, f"C{n0}:F{r}", COUNT)
    r += 1

    # F. control points
    heading(ws, r, "Control points: what the records evidence and what they cannot")
    r += 1
    tt = f.tests
    cps = [
        ("C1", "Every credit rests on a return received outside customer service",
         "Every credit traces to a return, and every return was received by warehouse staff (Inventory Specialists, "
         "Shipping Clerks, the Warehouse Manager); no receiver approved the credit.",
         "Whether anyone inspected the goods, their condition, or a carrier claim.",
         "=SUMPRODUCT(--(XLOOKUP(Credits[SalesReturnID],ReturnLines[SalesReturnID],ReturnLines[ReceivedByEmployeeID])"
         "=Credits[ApprovedByEmployeeID]))", "Requirements 1, 4"),
        ("C2", "Credits approved within the approver's authority",
         "The approver and the approver's general limit (MaxApprovalAmount) on every credit.",
         "The delegation of authority for credits, if one exists; who prepared the credit.",
         "=COUNTIF(Credits[AboveLimit],TRUE)", "Requirement 4"),
        ("C3", "Credits at the invoice price for no more than was shipped",
         "Each credit line against its return, shipment, and invoice lines; tax and freight on each credit.",
         "Nothing material: the recomputation is complete in the records.", 0, "Requirement 7"),
        ("C4", "The credit approver does not handle that customer's cash",
         "Who recorded each receipt and who applied it to the credited invoice.",
         "Cash handled outside the system (mail opening, deposits, remittance advices).",
         "=COUNTIF(Credits[CashAndCredit],TRUE)", "Requirement 4"),
        ("C5", "A clawback for every credit line at the accrual's rate",
         "One clawback per credit line, its base, rate, and amount, and its netting in later commission payments.",
         "Whether the representatives were informed; the approval of the rates beyond their end date.",
         "=SUM(Credits[Lines])-ROWS(UNIQUE(Clawbacks[CreditMemoLineID]))", "Requirement 4"),
        ("C6", "Refunds approved within authority, outside customer service",
         "The refund's approver, title, and general limit; the credit's approver.",
         "The delegation of authority for refunds; who prepared the refund (no preparer column).",
         "=COUNTIF(Refunds[AboveLimit],TRUE)", "Requirement 4"),
        ("C7", "A refund only of a credit balance the customer has paid",
         "The refund date against the dates of the payments applied to the credited invoice.",
         "Whether a payment had cleared the bank; the customer's request for the refund.",
         "=COUNTIF(Refunds[BeforePayment],TRUE)", "Requirements 4, 6"),
        ("C8", "Refunds to the payer's own method or account, net of open balances",
         "The refund's method against the methods of the receipts on the invoice; the customer's open balances on "
         "the refund date.",
         "The payee's name, the bank account, and the customer's written request: no table holds them.",
         "=COUNTIF(Refunds[MethodMismatch],TRUE)", "Requirements 4, 6"),
        ("C9", "Cash applied promptly to the remitting customer's invoices",
         "Receipt, deposit, and application dates; the customer on the receipt and on the invoice.",
         "Remittance advices and bank deposit records.", 0, "Requirement 7"),
    ]
    cp_rows = [[cp, check, ev, cannot, cnt if not isinstance(cnt, int) else "None found (Requirement 7)", where]
               for cp, check, ev, cannot, cnt, where in cps]
    cp0 = r + 1
    r = merged_table(ws, r, [1, 1, 5, 5, 2, 2], ["Control point", "What a well-designed cycle checks",
                                                 "What the records evidence", "What the records cannot show",
                                                 "Exceptions in the records", "Tested in"], cp_rows)
    expected_cp = {"C1": tt["receiver_is_approver"], "C2": len(tt["cm_above"]), "C4": len(tt["cash_credit"]),
                   "C5": tt["cb_lines"] - tt["cb_distinct"], "C6": len(tt["rf_above"]), "C7": len(tt["before"]),
                   "C8": len(tt["mism"])}
    for k, (cp, *_rest) in enumerate(cps):
        if cp in expected_cp:
            b.check(t, f"control point {cp}: exceptions in the records", expected_cp[cp], f"='Cycle Map'!M{cp0 + k}", 0,
                    COUNT)
    fmt(ws, f"M{cp0}:M{cp0 + len(cps)}", COUNT)
    ws.Columns("A").VerticalAlignment = -4160

    # the Documentation sheet's dates
    names = ["fiscal years", "ledger postings through", "last sales return", "last credit memo", "last clawback",
             "last refund", "last cash receipt"]
    expected = [f"{f.F} to {f.C}", f"{f.C}-12-31", max(s["date"] for s in srs)[:10], max(m["date"] for m in cms)[:10],
                max(a["date"] for a in f.adj)[:10], max(x["date"] for x in rfs)[:10],
                max(x["date"] for x in f.rcpt.values())[:10]]
    for k, (name, value) in enumerate(zip(names, expected)):
        if k == 0:
            b.check(t, f"Documentation: {name}", value, f"=Documentation!B{d0 + k}")
        else:
            check_date(b, t, f"Documentation: {name}", value, f"Documentation!B{d0 + k}")



# --- Requirement 2: the reconciliation by year -----------------------------------------------------------------------

def keyed_rows(ws, b: ExerciseBuild, t: str, r: int, cols: list[str], years: list[int], spec: list, total: bool = True,
               sheet: str = "Reconciliation") -> tuple[int, dict[str, int]]:
    """Rows of formulas by year. spec holds (key, label, source, formula template, expected by year, kind): the template
    uses {c} for the year's column and {key} for the row of an earlier key; a None template writes a heading; kind is
    "count", "money", or "diff" (a difference, in bold)."""
    at: dict[str, int] = {}
    for key, label, source, formula, exp, kind in spec:
        if formula is None:
            heading(ws, r, label)
            r += 1
            continue
        put(ws, {f"A{r}": label, f"B{r}": source})
        for c, y in zip(cols, years):
            put(ws, {f"{c}{r}": formula.format(c=c, **at)})
        if total:
            put(ws, {f"{letter(ord(cols[-1]) - 63)}{r}": f"=SUM({cols[0]}{r}:{cols[-1]}{r})"})
        last = letter(ord(cols[-1]) - 63) if total else cols[-1]
        fmt(ws, f"{cols[0]}{r}:{last}{r}", COUNT if kind == "count" else MONEY)
        if kind == "diff":
            bold(ws, f"A{r}:{last}{r}")
        for c, y in zip(cols, years):
            value = exp(y)
            name = f"{y}: {label[0].lower() + label[1:]}" + (f" ({source})" if source and kind != "diff" else "")
            b.check(t, name, value if kind == "count" else r2(value), f"={sheet}!{c}{r}",
                    0 if kind == "count" else 0.005, COUNT if kind == "count" else MONEY)
        at[key] = r
        r += 1
    return r, at


def r2_(b: ExerciseBuild) -> None:
    f = facts(b)
    t = "Requirement 2"
    ws = new_sheet(b, "Reconciliation")
    widths(ws, {"A": 54, "B": 32, "C": 16, "D": 16, "E": 16, "F": 16})
    title(ws, "Requirement 2: Each population reconciled to the ledger, by fiscal year",
          "Documents by their own dates; ledger postings by PostingDate (fiscal periods are calendar months); the "
          "year-end closes are excluded (see Exclusions). Differences are document less ledger.")
    years = f.years
    cols = ["C", "D", "E"]
    header(ws, 4, 1, ["Item", "Source"] + [str(y) for y in years] + ["Total"])
    for c, y in zip(cols, years):
        ws.Range(f"{c}4").Value = y

    def doc_sum(table: str, col: str) -> str:
        return f"=SUMIFS({table}[{col}],{table}[FiscalYear],{{c}}$4)"

    def gl(side, acct, src):
        return "=" + gl_f(side, acct, src, "{c}$4")

    def gly(side, acct, src):
        return lambda y: f.gl_sum(side, acct, src, [y])
    cmy = lambda y: f.in_year(f.cm.values(), y)  # noqa: E731
    rfy = lambda y: f.in_year(f.rf.values(), y)  # noqa: E731
    std = lambda y: sum(l["std"] for l in f.srl if year_of(f.sr[l["ret"]]["date"]) == y)  # noqa: E731
    cby = lambda y: sum(a["amt"] for a in f.adj if year_of(a["date"]) == y)  # noqa: E731
    rcy = lambda y: sum(x["amt"] for x in f.rcpt.values() if year_of(x["date"]) == y)  # noqa: E731
    apy = lambda y: sum(a[2] for a in f.all_apps if year_of(a[1]) == y)  # noqa: E731
    zero = lambda y: 0.0  # noqa: E731
    spec = [
        ("h1", "Credit memos", None, None, None, None),
        ("n", "Credit memos (count)", "Credits", "=COUNTIFS(Credits[FiscalYear],{c}$4)", lambda y: len(cmy(y)), "count"),
        ("sub", "Credit SubTotal", "Credits", doc_sum("Credits", "SubTotal"), lambda y: sum(m["sub"] for m in cmy(y)),
         "money"),
        ("g4060", "Debits to 4060 Sales Returns and Allowances", "Ledger, CreditMemo", gl("Dr", 4060, "CreditMemo"),
         gly("Dr", "4060", "CreditMemo"), "money"),
        ("d1", "Difference, SubTotal less 4060", "", "={c}{sub}-{c}{g4060}", zero, "diff"),
        ("fr", "Freight credited", "Credits", doc_sum("Credits", "FreightCreditAmount"),
         lambda y: sum(m["freight"] for m in cmy(y)), "money"),
        ("g4050", "Debits to 4050 Freight Revenue", "Ledger, CreditMemo", gl("Dr", 4050, "CreditMemo"),
         gly("Dr", "4050", "CreditMemo"), "money"),
        ("d2", "Difference, freight less 4050", "", "={c}{fr}-{c}{g4050}", zero, "diff"),
        ("tax", "Sales tax credited", "Credits", doc_sum("Credits", "TaxAmount"), lambda y: sum(m["tax"] for m in cmy(y)),
         "money"),
        ("g2050", "Debits to 2050 Sales Tax Payable", "Ledger, CreditMemo", gl("Dr", 2050, "CreditMemo"),
         gly("Dr", "2050", "CreditMemo"), "money"),
        ("d3", "Difference, tax less 2050", "", "={c}{tax}-{c}{g2050}", zero, "diff"),
        ("gt", "Credit GrandTotal", "Credits", doc_sum("Credits", "GrandTotal"), lambda y: sum(m["gt"] for m in cmy(y)),
         "money"),
        ("g1020", "Credits to 1020 Accounts Receivable", "Ledger, CreditMemo", gl("Cr", 1020, "CreditMemo"),
         gly("Cr", "1020", "CreditMemo"), "money"),
        ("g2060", "Credits to 2060 Customer Deposits and Unapplied Cash", "Ledger, CreditMemo",
         gl("Cr", 2060, "CreditMemo"), gly("Cr", "2060", "CreditMemo"), "money"),
        ("d4", "Difference, GrandTotal less 1020 and 2060", "", "={c}{gt}-{c}{g1020}-{c}{g2060}", zero, "diff"),
        ("h2", "Sales returns", None, None, None, None),
        ("std", "Returns at standard cost", "ReturnLines", doc_sum("ReturnLines", "ExtendedStandardCost"), std, "money"),
        ("g1040", "Debits to 1040 Inventory", "Ledger, SalesReturn", gl("Dr", 1040, "SalesReturn"),
         gly("Dr", "1040", "SalesReturn"), "money"),
        ("d5", "Difference, standard cost less 1040", "", "={c}{std}-{c}{g1040}", zero, "diff"),
    ]
    for a in ("5010", "5020", "5030", "5040"):
        spec.append((f"g{a}", f"Credits to {a} Cost of Goods Sold", "Ledger, SalesReturn", gl("Cr", int(a), "SalesReturn"),
                     gly("Cr", a, "SalesReturn"), "money"))
    spec += [
        ("d6", "Difference, standard cost less the four cost of goods sold credits", "",
         "={c}{std}-{c}{g5010}-{c}{g5020}-{c}{g5030}-{c}{g5040}", zero, "diff"),
        ("h3", "Customer refunds", None, None, None, None),
        ("rn", "Refunds (count)", "Refunds", "=COUNTIFS(Refunds[FiscalYear],{c}$4)", lambda y: len(rfy(y)), "count"),
        ("ra", "Refund amount", "Refunds", doc_sum("Refunds", "Amount"), lambda y: sum(x["amt"] for x in rfy(y)), "money"),
        ("r1010", "Credits to 1010 Cash", "Ledger, CustomerRefund", gl("Cr", 1010, "CustomerRefund"),
         gly("Cr", "1010", "CustomerRefund"), "money"),
        ("r2060", "Debits to 2060", "Ledger, CustomerRefund", gl("Dr", 2060, "CustomerRefund"),
         gly("Dr", "2060", "CustomerRefund"), "money"),
        ("d7", "Difference, refunds less 1010", "", "={c}{ra}-{c}{r1010}", zero, "diff"),
        ("d8", "Difference, refunds less 2060", "", "={c}{ra}-{c}{r2060}", zero, "diff"),
        ("h4", "Commission clawbacks", None, None, None, None),
        ("cb", "Clawback amount", "Clawbacks", doc_sum("Clawbacks", "CommissionAdjustmentAmount"), cby, "money"),
        ("c2034", "Debits to 2034 Sales Commissions Payable", "Ledger, SalesCommissionAdjustment",
         gl("Dr", 2034, "SalesCommissionAdjustment"), gly("Dr", "2034", "SalesCommissionAdjustment"), "money"),
        ("c6290", "Credits to 6290 Sales Commission Expense", "Ledger, SalesCommissionAdjustment",
         gl("Cr", 6290, "SalesCommissionAdjustment"), gly("Cr", "6290", "SalesCommissionAdjustment"), "money"),
        ("d9", "Difference, clawbacks less 2034", "", "={c}{cb}-{c}{c2034}", zero, "diff"),
        ("d10", "Difference, clawbacks less 6290", "", "={c}{cb}-{c}{c6290}", zero, "diff"),
        ("h5", "Cash receipts and applications", None, None, None, None),
        ("rc", "Cash receipts", "CashByYear", "=SUMIFS(CashByYear[ReceiptAmount],CashByYear[FiscalYear],{c}$4)", rcy,
         "money"),
        ("k1010", "Debits to 1010 Cash", "Ledger, CashReceipt", gl("Dr", 1010, "CashReceipt"),
         gly("Dr", "1010", "CashReceipt"), "money"),
        ("k2060", "Credits to 2060", "Ledger, CashReceipt", gl("Cr", 2060, "CashReceipt"),
         gly("Cr", "2060", "CashReceipt"), "money"),
        ("ap", "Cash applications", "CashByYear", "=SUMIFS(CashByYear[AppliedAmount],CashByYear[FiscalYear],{c}$4)", apy,
         "money"),
        ("a2060", "Debits to 2060", "Ledger, CashReceiptApplication", gl("Dr", 2060, "CashReceiptApplication"),
         gly("Dr", "2060", "CashReceiptApplication"), "money"),
        ("a1020", "Credits to 1020", "Ledger, CashReceiptApplication", gl("Cr", 1020, "CashReceiptApplication"),
         gly("Cr", "1020", "CashReceiptApplication"), "money"),
        ("d11", "Difference, receipts less applications", "", "={c}{rc}-{c}{ap}", zero, "diff"),
        ("d12", "Difference, receipts less 1010", "", "={c}{rc}-{c}{k1010}", zero, "diff"),
        ("d13", "Difference, receipts less 2060", "", "={c}{rc}-{c}{k2060}", zero, "diff"),
        ("d14", "Difference, applications less 2060", "", "={c}{ap}-{c}{a2060}", zero, "diff"),
        ("d15", "Difference, applications less 1020", "", "={c}{ap}-{c}{a1020}", zero, "diff"),
    ]
    r, at = keyed_rows(ws, b, t, 5, cols, years, spec)
    b.found["recon_diffs"] = [at[k] for k in at if k.startswith("d")]

    # 2060 rolled forward
    r += 1
    heading(ws, r, "Account 2060 Customer Deposits and Unapplied Cash, rolled forward (credit balance positive)")
    r += 1
    roll0 = r
    put(ws, {f"A{r}": "Opening balance", "C" + str(r): 0, "D" + str(r): f"=C{r + 5}", "E" + str(r): f"=D{r + 5}"})
    roll = [("Receipts held (credits from CashReceipt)", "=" + gl_f("Cr", 2060, "CashReceipt", "{c}$4")),
            ("Applied to invoices (debits from CashReceiptApplication)",
             "=-" + gl_f("Dr", 2060, "CashReceiptApplication", "{c}$4")),
            ("Credits on paid invoices (credits from CreditMemo)", "=" + gl_f("Cr", 2060, "CreditMemo", "{c}$4")),
            ("Refunds paid (debits from CustomerRefund)", "=-" + gl_f("Dr", 2060, "CustomerRefund", "{c}$4")),
            ("Closing balance, rolled forward", f"=SUM({{c}}{roll0}:{{c}}{roll0 + 4})"),
            ("Ledger balance of 2060 at the year-end", "=" + gl_f("Cr", 2060, None, "{c}$4", None, "<=") + "-" +
             gl_f("Dr", 2060, None, "{c}$4", None, "<=")),
            ("Difference, rolled forward less ledger", f"={{c}}{roll0 + 5}-{{c}}{roll0 + 6}")]
    for label, formula in roll:
        r += 1
        put(ws, {f"A{r}": label})
        for c in cols:
            put(ws, {f"{c}{r}": formula.format(c=c)})
    fmt(ws, f"C{roll0}:E{r}", MONEY)
    bold(ws, f"A{roll0 + 5}:E{roll0 + 7}")
    for c, y in zip(cols, years):
        b.check(t, f"2060 at the end of {y}, rolled forward", r2(f.balance("2060", y)), f"=Reconciliation!{c}{roll0 + 5}")
        b.check(t, f"2060 at the end of {y}, ledger", r2(f.balance("2060", y)), f"=Reconciliation!{c}{roll0 + 6}")
        b.check(t, f"2060 at the end of {y}, difference", 0.0, f"=Reconciliation!{c}{roll0 + 7}")
    r += 2
    put(ws, {f"A{r}": "Items in 2060 at each year-end: credits whose part posted to 2060 was not yet refunded"})
    bold(ws, f"A{r}")
    r += 1
    header(ws, r, 1, ["Year-end", "Credit memo", "Status today", "Amount in 2060"])
    r += 1
    items = [(y, num, status, a) for y in years for num, a, status in f.open_2060[y]]
    it0, it1 = r, r + len(items) - 1
    paste(ws, r, 1, [[y, num, status, a] for y, num, status, a in items],
          "open items in 2060 at each year-end (each credit's 2060 postings dated by the year-end, less its refund "
          "if dated by then)", {3: MONEY})
    r = it1 + 1
    put(ws, {f"A{r}": "Items, total by year-end"})
    for c, y in zip(cols, years):
        put(ws, {f"{c}{r}": f"=SUMIFS($D${it0}:$D${it1},$A${it0}:$A${it1},{c}$4)"})
    fmt(ws, f"C{r}:E{r}", MONEY)
    r += 1
    put(ws, {f"A{r}": "Difference, ledger balance less items"})
    for c, y in zip(cols, years):
        put(ws, {f"{c}{r}": f"={c}{roll0 + 6}-{c}{r - 1}"})
        b.check(t, f"2060 at the end of {y}: ledger balance less the items pasted", 0.0, f"=Reconciliation!{c}{r}")
    fmt(ws, f"C{r}:E{r}", MONEY)
    bold(ws, f"A{r}:E{r}")
    r += 2

    # 2034
    heading(ws, r, "Account 2034 Sales Commissions Payable (credit balance positive)")
    r += 1
    acc = lambda y: f.commission["accruals"][years.index(y)]  # noqa: E731
    pay = lambda y: f.commission["payments"][years.index(y)]  # noqa: E731
    spec34 = [
        ("acc", "Accruals", "CommissionByYear", "=SUMIFS(CommissionByYear[AccrualAmount],CommissionByYear[FiscalYear],{c}$4)",
         acc, "money"),
        ("gacc", "Credits to 2034 from SalesCommissionAccrual", "Ledger", "=" + gl_f("Cr", 2034, "SalesCommissionAccrual",
                                                                                      "{c}$4"),
         gly("Cr", "2034", "SalesCommissionAccrual"), "money"),
        ("pay", "Commission payments, net", "CommissionByYear",
         "=SUMIFS(CommissionByYear[PaymentAmount],CommissionByYear[FiscalYear],{c}$4)", pay, "money"),
        ("gpay", "Debits to 2034 from SalesCommissionPayment", "Ledger", "=" + gl_f("Dr", 2034, "SalesCommissionPayment",
                                                                                     "{c}$4"),
         gly("Dr", "2034", "SalesCommissionPayment"), "money"),
        ("cb", "Clawbacks", "Clawbacks", "=SUMIFS(Clawbacks[CommissionAdjustmentAmount],Clawbacks[FiscalYear],{c}$4)", cby,
         "money"),
        ("chg", "Change: accruals less payments and clawbacks", "", "={c}{acc}-{c}{pay}-{c}{cb}",
         lambda y: acc(y) - pay(y) - cby(y), "money"),
        ("sub", "Subledger balance at the year-end", "", "=SUM($C{chg}:{c}{chg})",
         lambda y: sum(acc(z) - pay(z) - cby(z) for z in years if z <= y), "money"),
        ("led", "Ledger balance of 2034 at the year-end", "Ledger", "=" + gl_f("Cr", 2034, None, "{c}$4", None, "<=") +
         "-" + gl_f("Dr", 2034, None, "{c}$4", None, "<="), lambda y: f.balance("2034", y), "money"),
        ("d1", "Difference, subledger less ledger", "", "={c}{sub}-{c}{led}", zero, "diff"),
        ("d2", "Difference, accruals less their postings", "", "={c}{acc}-{c}{gacc}", zero, "diff"),
        ("d3", "Difference, payments less their postings", "", "={c}{pay}-{c}{gpay}", zero, "diff"),
    ]
    r, at34 = keyed_rows(ws, b, t, r, cols, years, spec34, total=False)
    b.found["recon_last"] = r
    r += 1

    # exclusions
    heading(ws, r, "Excluded, and why")
    r += 1
    header(ws, r, 1, ["Exclusion", "Source", "Rows", "Amount"])
    r += 1
    ex0 = r
    for acct in ("4060", "6290"):
        n = sum(v[2] for (y, a, s, c), v in f.gl.items() if a == acct and c)
        put(ws, {f"A{r}": f"Year-end closes posted to {acct}", f"B{r}": "Ledger (IsYearEndClose)",
                 f"C{r}": f"=SUMIFS(Ledger[Rows],Ledger[AccountNumber],{acct},Ledger[IsYearEndClose],TRUE)",
                 f"D{r}": "=" + gl_f("Cr", acct, None, None, "TRUE") + "-" + gl_f("Dr", acct, None, None, "TRUE")})
        b.check(t, f"closes on {acct}: rows", n, f"=Reconciliation!C{r}", 0, COUNT)
        b.check(t, f"closes on {acct}: credits less debits", r2(f.gl_sum("Cr", acct, None, None, True)
                                                                 - f.gl_sum("Dr", acct, None, None, True)),
                f"=Reconciliation!D{r}")
        r += 1
    fmt(ws, f"C{ex0}:C{r}", COUNT)
    fmt(ws, f"D{ex0}:D{r}", MONEY)
    n_next = f.one("SELECT COUNT(*) FROM GLEntry WHERE PostingDate >= ?", f"{f.C + 1}-01-01")
    srcs_next = [x[0] for x in f.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE PostingDate >= ?",
                                   f"{f.C + 1}-01-01")]
    close_rows = {a: sum(v[2] for (y, aa, s, c), v in f.gl.items() if aa == a and c) for a in ("4060", "6290")}
    text_block(ws, r + 1, MA, [
        f"Excluded: the year-end closing entries ({series(f.closes)}). They zero the revenue and expense accounts, "
        f"crediting 4060 ({close_rows['4060']} rows, {money(f.gl_sum('Cr', '4060', None, None, True))}) and 6290 "
        f"({close_rows['6290']} rows, {money(f.gl_sum('Cr', '6290', None, None, True))}), so leaving them in would "
        "break every reconciliation of a document to its account. The Ledger query flags them (IsYearEndClose), and "
        "every formula here takes IsYearEndClose = FALSE. None of the cycle's documents is a close, and 2060 and 2034 "
        f"have no closing rows. Also excluded: the {n_next} ledger rows dated in fiscal {f.C + 1} "
        f"({series(srcs_next)} only), which the Ledger query leaves out because the scope ends with fiscal {f.C}.",
        "Every population reconciles to the cent in every year: credits to 4060, 4050, and 2050, and their totals to "
        "the credits to 1020 and 2060; returns at standard to 1040 and to the four cost of goods sold accounts; "
        "refunds to cash and 2060; clawbacks to 2034 and 6290; receipts and applications to cash, 2060, and "
        "receivables. Account 2060 is a hub with large flows and a small balance, so each flow is reconciled "
        "separately; its year-end balances are only the credits on paid invoices not yet refunded "
        f"({money(f.balance('2060', years[0]))}, {money(f.balance('2060', years[1]))}, and "
        f"{money(f.balance('2060', years[2]))}; the last is the three credits still Issued). Account 2034 at the end "
        f"of fiscal {f.C}, {money(f.balance('2034', f.C))}, equals the accruals less the net commission payments and "
        "the clawbacks to date."], span=6)


# --- Requirement 3: materiality, the expectation of returns, the fraud brainstorm, and the risk-and-control matrix ----

def r3(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    t = "Requirement 3"
    m, e = f.materiality, f.expectation
    ws = new_sheet(b, "Materiality")
    widths(ws, {"A": 70, "B": 18, "C": 18, "D": 18, "E": 18})
    title(ws, "Requirement 3: Materiality and the expectation of returns",
          "The parameters every later test refers to: named cells Materiality, PerformanceMateriality, and ClearlyTrivial.")
    header(ws, 3, 1, ["Parameter", "Value", "Basis"])
    rev_types = '{"Revenue","Expense"}'
    income = (f"=SUM(SUMIFS(Ledger[Credit],Ledger[FiscalYear],{f.C},Ledger[AccountType],{rev_types},"
              f"Ledger[IsYearEndClose],FALSE))-SUM(SUMIFS(Ledger[Debit],Ledger[FiscalYear],{f.C},"
              f"Ledger[AccountType],{rev_types},Ledger[IsYearEndClose],FALSE))")
    put(ws, {"A4": f"Income before income taxes, fiscal {f.C} (revenue less expenses as the ledger records them, "
                   "closes excluded)", "B4": income, "C4": "Ledger",
             "A5": "Materiality rate", "B5": MATERIALITY, "C5": "The chief audit executive's condition",
             "A6": "Overall materiality", "B6": "=B4*B5",
             "A7": "Performance materiality rate", "B7": PERFORMANCE, "C7": "75% of materiality",
             "A8": "Performance materiality", "B8": "=B6*B7",
             "A9": "Clearly trivial rate", "B9": TRIVIAL, "C9": "5% of materiality",
             "A10": "Clearly trivial threshold", "B10": "=B6*B9"})
    fmt(ws, "B4", MONEY)
    fmt(ws, "B5", "0%")
    fmt(ws, "B7", "0%")
    fmt(ws, "B9", "0%")
    fmt(ws, "B6", MONEY)
    fmt(ws, "B8", MONEY)
    fmt(ws, "B10", MONEY)
    bold(ws, "A6:B6")
    bold(ws, "A8:B8")
    bold(ws, "A10:B10")
    xl.name_cell(wb, "Materiality", "Materiality!$B$6")
    xl.name_cell(wb, "PerformanceMateriality", "Materiality!$B$8")
    xl.name_cell(wb, "ClearlyTrivial", "Materiality!$B$10")
    put(ws, {"A11": "The chart of accounts has no income tax account, so the income the ledger records is income before "
                    "income taxes. Materiality is not rounded, so every comparison uses the cells above."})
    ws.Range("A11").WrapText = True
    ws.Range("A11").Font.Italic = True
    b.check(t, f"income before income taxes, fiscal {f.C}", r2(m["income"]), "=Materiality!B4")
    b.check(t, "overall materiality", m["mat"], "=Materiality", 0.0001)
    b.check(t, "performance materiality", m["perf"], "=PerformanceMateriality", 0.0001)
    b.check(t, "clearly trivial", m["trivial"], "=ClearlyTrivial", 0.0001)

    heading(ws, 13, f"Analytical expectation of fiscal {f.C} returns")
    header(ws, 14, 1, ["Item"] + [str(y) for y in f.years])
    for j, y in enumerate(f.years):
        ws.Cells(14, 2 + j).Value = y
    accts = "{" + ",".join(REVENUE) + "}"
    for j, c in enumerate(["B", "C", "D"]):
        put(ws, {f"{c}15": f'=SUM(SUMIFS(Ledger[Credit],Ledger[SourceDocumentType],"SalesInvoice",Ledger[AccountNumber],'
                           f'{accts},Ledger[FiscalYear],{c}$14))-SUM(SUMIFS(Ledger[Debit],Ledger[SourceDocumentType],'
                           f'"SalesInvoice",Ledger[AccountNumber],{accts},Ledger[FiscalYear],{c}$14))',
                 f"{c}16": "=" + gl_f("Dr", 4060, None, f"{c}$14"),
                 f"{c}17": f"={c}16/{c}15"})
    put(ws, {"A15": "Revenue posted by sales invoices to 4010-4040 and 4080 (credits less debits)",
             "A16": "Returns and allowances: debits to 4060, closes excluded",
             "A17": "Return rate"})
    fmt(ws, "B15:D16", MONEY)
    fmt(ws, "B17:D17", "0.000%")
    rows = [("A19", f"Expectation of fiscal {f.C} returns at the {f.P} rate", "B19", "=D15*C17", MONEY),
            ("A20", f"Recorded fiscal {f.C} returns (debits to 4060)", "B20", "=D16", MONEY),
            ("A21", "Difference, recorded less expected", "B21", "=B20-B19", MONEY),
            ("A22", "Difference as a percentage of the expectation", "B22", "=B21/B19", "0.0%"),
            ("A23", "Against the clearly trivial threshold", "B23",
             '=IF(ABS(B21)>ClearlyTrivial,"Above clearly trivial","Not above clearly trivial")', None),
            ("A24", "Against performance materiality", "B24",
             '=IF(ABS(B21)>PerformanceMateriality,"Above performance materiality","Below performance materiality")', None),
            ("A25", "Conclusion", "B25",
             '=IF(ABS(B21)>PerformanceMateriality,"Investigate: the difference exceeds performance materiality",'
             'IF(ABS(B21)>ClearlyTrivial,"Investigate (Requirement 5): above clearly trivial, below performance '
             'materiality","Accept: the difference is clearly trivial"))', None),
            ("A27", f"Expectation of fiscal {f.C} returns at the {f.F} rate", "B27", "=D15*B17", MONEY),
            ("A28", "Difference, recorded less expected", "B28", "=B20-B27", MONEY),
            ("A29", "Difference as a percentage of the expectation", "B29", "=B28/B27", "0.0%")]
    for la, label, cell, formula, nf in rows:
        put(ws, {la: label, cell: formula})
        if nf:
            fmt(ws, cell, nf)
    bold(ws, "A25:B25")
    for j, (c, y) in enumerate(zip(["B", "C", "D"], f.years)):
        b.check(t, f"{y} revenue posted by sales invoices to 4010-4040 and 4080", r2(e["revenue"][j]),
                f"=Materiality!{c}15")
        b.check(t, f"{y} debits to 4060", r2(e["returns"][j]), f"=Materiality!{c}16")
        b.check(t, f"{y} return rate", e["rates"][j], f"=Materiality!{c}17", 5e-7, "0.000%")
    b.check(t, f"expectation of {f.C} returns at the {f.P} rate", e["exp"], "=Materiality!B19", 0.005)
    b.check(t, "difference, recorded less expected", e["diff"], "=Materiality!B21", 0.005)
    b.check(t, "difference, percentage", e["diff_pct"], "=Materiality!B22", 5e-5, "0.0%")
    b.check(t, "against clearly trivial", "Above clearly trivial" if e["above_trivial"] else "Not above clearly trivial",
            "=Materiality!B23")
    b.check(t, "against performance materiality",
            "Above performance materiality" if e["above_perf"] else "Below performance materiality", "=Materiality!B24")
    b.check(t, f"expectation at the {f.F} rate", e["exp_f"], "=Materiality!B27", 0.005)
    b.check(t, f"difference at the {f.F} rate, percentage", e["f_pct"], "=Materiality!B29", 5e-5, "0.0%")
    text_block(ws, 31, MA, [
        f"Materiality is 5% of fiscal {f.C} income before income taxes as the ledger records it, {money(m['income'])}: "
        f"{money(m['mat'])}, with performance materiality of {money(m['perf'])} and a clearly trivial threshold of "
        f"{money(m['trivial'])}. The chart of accounts has no income tax account, so the ledger's net income is the "
        "basis; the CFO's open questions on tax status do not change it for this audit.",
        f"At the {f.P} return rate ({pct(e['rates'][1], 3)} of the revenue sales invoices posted), fiscal {f.C} "
        f"returns would be expected at {money(e['exp'])}; the ledger records {money(e['actual'])}, "
        f"{money(e['diff'])} or {pct(e['diff_pct'])} more. The difference is above clearly trivial and below "
        "performance materiality, so it is not a misstatement in itself, but it calls for an explanation: Requirement "
        "5 looks for where returns grow (by item group, reason, customer, and shipment month).",
        f"The {f.F} rate ({pct(e['rates'][0], 3)}) would make a poorer expectation ({money(e['exp_f'])}, "
        f"{pct(e['f_pct'])} below the recorded returns). Fiscal {f.F} was the first year of operations in the data "
        f"(the first shipment is dated {e['first_shipment'][:10]}): it had no earlier sales to return, and returns "
        "arrive weeks after shipment, so its early months carry almost no returns and its rate understates the "
        "steady state. The prior year is the closest complete, comparable period."], span=4)

    # the fraud brainstorm and the risk-and-control matrix
    rk = new_sheet(b, "Risks")
    widths(rk, {"A": 30, "B": 24, "C": 22, "D": 30, "E": 34, "F": 24, "G": 34, "H": 22, "I": 12})
    title(rk, "Requirement 3: Fraud brainstorm and risk-and-control matrix",
          "Mapped to the people and documents of the cycle (fig-19-01) and to the schemes of tbl-19-01; AS 2401's "
          "three conditions.")
    tt = f.tests
    n_rf_people = len({x["appr"] for x in f.rf.values()})
    facts_rows = [
        ["People who approve refunds", "=ROWS(UNIQUE(Refunds[ApprovedByEmployeeID]))",
         "A small team in accounting approves every refund, with no preparer recorded."],
        ["Clawbacks over three years, as a share of materiality",
         "=SUM(Clawbacks[CommissionAdjustmentAmount])/Materiality",
         "Low in amount, but part of the representatives' pay."],
        ["Receipts recorded by customer service", '=SUMIFS(CashHandlers[Documents],CashHandlers[Document],'
                                                  '"Receipts recorded")',
         "Customer service records receipts ..."],
        ["Applications made by customer service", '=SUMIFS(CashHandlers[Documents],CashHandlers[Document],"Applications")',
         "... applies them to invoices ..."],
        ["Credits approved by customer service", "=ROWS(Credits)", "... approves the credits ..."],
        ["Clawbacks approved by customer service", "=ROWS(Clawbacks)",
         "... and approves the clawbacks: duties that should be separated."],
    ]
    heading(rk, 4, "Facts behind the ratings (live)")
    header(rk, 5, 1, ["Fact", "Value", "What it means"])
    for i, (label, formula, meaning) in enumerate(facts_rows):
        put(rk, {f"A{6 + i}": label, f"B{6 + i}": formula, f"C{6 + i}": meaning})
    fmt(rk, "B6", COUNT)
    fmt(rk, "B7", "0.0%")
    fmt(rk, "B8:B11", COUNT)
    b.check(t, "people who approve refunds", n_rf_people, "=Risks!B6", 0, COUNT)
    b.check(t, "clawbacks as a share of materiality", sum(a["amt"] for a in f.adj) / m["mat"], "=Risks!B7", 5e-6, "0.0%")
    cs_titles = (CSR, CSM)
    b.check(t, "receipts recorded by customer service",
            sum(1 for x in f.rcpt.values() if f.title(x["rec"]) in cs_titles), "=Risks!B8", 0, COUNT)
    b.check(t, "applications by customer service", sum(1 for a in f.all_apps if f.title(a[3]) in cs_titles),
            "=Risks!B9", 0, COUNT)
    r = 13
    heading(rk, r, "Process risk ratings")
    r = text_table(rk, r + 1, 1, ["Process", "Rating", "Why"], [
        ["Customer refunds", "High", f"Cash leaves the company on the strength of a record; {word(n_rf_people)} people "
                                     "approve every refund, two of the three job titles with a limit of $0, and no "
                                     "table holds the payee, the bank account, or the customer's request."],
        ["Credit memos", "High", "They reduce revenue and receivables, and a credit can conceal stolen cash; "
                                 "representatives with a limit of $0 approve them, in the department that also "
                                 "records and applies the customer's cash."],
        ["Cash application", "Moderate", "Lapping is possible because one department records and applies receipts, "
                                         "but every receipt passes through 2060 and the delays can be measured."],
        ["Commission clawbacks", "Low", "Small in amount (a few percent of materiality over three years), but part of "
                                        "employees' pay, and approved by the same people who approve the credits."]])
    heading(rk, r, "Fraud brainstorm (AS 2401: incentive or pressure, opportunity, attitude or rationalization)")
    r = text_table(rk, r + 1, 1, ["Scheme (tbl-19-01)", "Who could commit it", "Documents (fig-19-01)",
                                  "Incentive or pressure", "Opportunity in the records", "Attitude or rationalization",
                                  "Traces a query can look for", "Test"], [
        ["Lapping", "Customer service staff who record receipts and apply cash", "CashReceipt, CashReceiptApplication",
         "Personal financial pressure; a debt to cover", "One department records receipts, deposits them, and applies "
         "them; nobody outside it reconciles deposits to applications", "\"I will put it back before anyone notices\"",
         "Receipts applied to another customer's invoices; growing delays from receipt to deposit and to application",
         "Requirement 7 (lapping tests)"],
        ["False credit", "A customer service representative or the manager", "CreditMemo, CashReceiptApplication",
         "Pressure to hide a shortage of cash taken", "The credit approver also applies the customer's cash; "
         "representatives approve credits with a limit of $0", "\"The customer would have returned it anyway\"",
         "Credits with no return received; the credit's approver handled that customer's cash",
         "Requirements 1 and 4 (C1, C4)"],
        ["Diverted refund", "An accounting approver, alone or with someone who can change payee details",
         "CustomerRefund, CreditMemo", "Personal financial pressure", "No payee, bank account, or customer request in "
         "the records; refunds by wire and ACH; no preparer recorded", "\"It is a small amount and nobody checks\"",
         "Refunds by a method unlike the customer's payments; refunds of credits not yet paid for; concentration by "
         "approver or customer", "Requirements 4, 5, and 6 (C6 to C8)"],
        ["Unauthorized credits", "Customer service representatives", "CreditMemo, SalesReturn",
         "Keeping a customer satisfied; sales or service targets", "Approval limits are not enforced by the system",
         "\"I am helping the customer, and the goods came back\"",
         "Credits above authority; concentration by approver and customer; return rates out of line",
         "Requirements 4 and 5 (C2)"],
        ["Commission manipulation", "Sales representatives, customer service, the Accounting Manager",
         "SalesCommissionAdjustment, Accrual, Payment, Rate", "Commission income", "The Accounting Manager approves the "
         "rates, creates the accruals, and approves the payments; customer service approves the clawbacks",
         "\"The rates were going to change anyway\"", "Credit lines without clawbacks; clawbacks at the wrong rate",
         "Requirement 4 (C5)"]])
    heading(rk, r, "Risk-and-control matrix")
    rcm = [
        ["Credits granted without authority reduce revenue", "Occurrence of credits; accuracy of revenue", "C2",
         "Credits approved within the approver's authority", "GrandTotal against the approver's MaxApprovalAmount, "
         "every credit", "SQL (Credits.sql); Excel for the evaluation", "Database for the limit; the delegation of "
         "authority for credits is outside", "414 credits above the limit", "High"],
        ["A false credit covers stolen cash", "Occurrence of credits; completeness of cash", "C1, C4",
         "Every credit rests on a return received in the warehouse; the approver does not handle the customer's cash",
         "Anti-join of credits to returns; credit approver against the recorders and appliers of the invoice's cash",
         "SQL", "Database", "206 credits whose approver applied the invoice's cash", "High"],
        ["Credit amounts are wrong", "Accuracy and valuation of credits", "C3",
         "Credits at the invoice price for no more than was shipped", "Recompute each credit line, its tax and freight",
         "SQL", "Database", "Clean", "Moderate"],
        ["Clawbacks are skipped or mis-rated", "Completeness and accuracy of commission expense", "C5",
         "A clawback for every credit line at the accrual's rate", "Anti-join of credit lines to clawbacks; recompute "
         "base, rate, and amount", "SQL", "Database", "Clean", "Low"],
        ["Refunds are granted without authority", "Occurrence of cash disbursements", "C6",
         "Refunds approved within authority, outside customer service", "Amount against the approver's limit; refund "
         "approver against the credit approver", "SQL", "Database for the limit; the delegation of authority for "
         "refunds is outside", "163 refunds above the limit", "High"],
        ["A refund pays out a credit balance the customer has not paid", "Occurrence of disbursements; existence of 2060",
         "C7", "A refund only of a credit balance the customer has paid", "Refund date against the last payment on the "
         "credited invoice", "SQL; the sample's data attribute in Excel", "Database (dates); clearance is outside",
         "58 refunds before the payment", "High"],
        ["A refund is diverted to another payee", "Occurrence of disbursements (fraud)", "C8",
         "Refunds to the payer's method or a verified account, open balances offset first", "Refund method against the "
         "receipts' methods; past-due balance on the refund date; sample for the payee check and the written request",
         "SQL; Excel sample", "Mostly outside: the payee, the bank account, and the request are in no table",
         "153 method mismatches; 124 refunds to customers past due by at least the refund", "High"],
        ["Lapping delays or hides receipts", "Completeness and cutoff of cash; existence of receivables", "C9",
         "Cash applied promptly to the remitting customer's invoices", "Receipts applied to other customers' invoices; "
         "receipt to deposit and to application delays", "SQL", "Database; remittance advices are outside", "Clean",
         "Moderate"],
        ["Returned goods are restocked at full value", "Valuation of inventory", "C1",
         "Returned goods are inspected, and damaged goods are written down", "Restocking cost by reason; the sample's "
         "inspection record for Damaged returns", "SQL; Excel sample", "Outside: the inspection record", "Damaged "
         "returns restocked at standard cost", "Moderate"],
        ["Populations are incomplete or misposted", "Completeness and cutoff of every population", "All",
         "Every document posts once, in its own period", "Reconcile each population to the ledger by year; numbering "
         "gaps; anti-joins in both directions", "SQL; Excel for the appendix", "Database", "Clean", "Moderate"],
    ]
    r0 = r + 2
    r = text_table(rk, r + 1, 1, ["Risk", "Assertion", "Control point", "Control expected", "Test", "Tool",
                                  "Evidence: in the database or outside", "Result", "Rating"], rcm)
    covered = f'=SUMPRODUCT(--(COUNTIF(C{r0}:C{r0 + len(rcm) - 1},"*C"&SEQUENCE(9)&"*")>0))'
    put(rk, {f"A{r}": "Control points C1 to C9 covered by the matrix", f"B{r}": covered})
    bold(rk, f"A{r}")
    b.check(t, "control points covered by the risk-and-control matrix", 9, f"=Risks!B{r}", 0, COUNT)
    text_block(rk, r + 2, MA, [
        "The matrix sees what matters most in this cycle: customer service records receipts, applies cash, approves "
        "credits, and approves clawbacks, duties that should be separated, and accounting approves refunds with no "
        "preparer recorded and, for two of its three job titles, a general limit of $0. Most of the evidence on "
        "authority, timing, and separation lies in the database and is tested on whole populations; the evidence on "
        "the payee, the customer's request, and the inspection of damaged goods lies outside it and needs the "
        "sample of Requirement 6. Refunds and credits are rated high, cash application moderate, and clawbacks low in "
        "amount but sensitive because they are part of employees' pay."], span=8)


# --- Requirement 4: the control tests --------------------------------------------------------------------------------

def refund_flags_rows(f: Facts) -> list[list]:
    """The rows RefundFlags.csv holds: the export of Credits.sql's refund flags (Requirement 4)."""
    t = f.tests
    out = []
    for k, x in f.rf.items():
        fl = t["flags"][k]
        out.append([x["num"], serial(x["date"]), year_of(x["date"]), x["cust"], x["amt"], int(fl[0]), int(fl[1]),
                    int(fl[2]), int(fl[3]), r2(t["pdue"][k]), int(fl[4]), int(t["pdue"][k] > 0.005), t["score"][k]])
    return out


FLAG_COLUMNS = ["RefundNumber", "RefundDate", "FiscalYear", "CustomerID", "Amount", "AboveLimit", "CreditAboveLimit",
                "MethodMismatch", "BeforePayment", "PastDue", "PastDueAtLeastRefund", "PastDueAny", "Score"]


def r4(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    t = "Requirement 4"
    tt = f.tests
    # the refund flags of Credits.sql, as RefundFlags.csv holds them
    fs = xl.sheet(wb, "RefundFlags", after=data_anchor(b))
    rows = refund_flags_rows(f)
    header(fs, 1, 1, FLAG_COLUMNS)
    paste(fs, 2, 1, rows, "refund flags exported as RefundFlags.csv (one row per refund; flags 1 or 0; PastDue is the "
                          "customer's past-due balance on the refund date)", {1: DATE, 4: MONEY, 9: MONEY})
    lo = fs.ListObjects.Add(1, fs.Range(fs.Cells(1, 1), fs.Cells(1 + len(rows), len(FLAG_COLUMNS))), None, xl.XL_YES)
    lo.Name = "RefundFlags"
    fs.Columns.AutoFit()

    ws = new_sheet(b, "Tests")
    widths(ws, {"A": 7, "B": 58, "C": 9, "D": 22, "E": 10, "F": 10, "G": 10, "H": 10, "I": 15, "J": 15, "K": 26})
    title(ws, "Requirement 4: The controls tested on every document",
          "Fiscal years by the document's own date. Live flags from the Credits and Refunds queries; the past-due "
          "tests read the RefundFlags pasted from Credits.sql.")
    years = f.years
    header(ws, 4, 1, ["ID", "Test", "Control point", "Population", str(years[0]), str(years[1]), str(years[2]), "Total",
                      "Amount", f"Amount {f.C}", "Source"])
    for c, y in zip("EFG", years):
        ws.Range(f"{c}4").Value = y

    def cflag(col):
        return dict(year=f"=COUNTIFS(Credits[{col}],TRUE,Credits[FiscalYear],{{c}}$4)",
                    total=f"=COUNTIF(Credits[{col}],TRUE)", amount=f"=SUMIFS(Credits[GrandTotal],Credits[{col}],TRUE)",
                    cur=f"=SUMIFS(Credits[GrandTotal],Credits[{col}],TRUE,Credits[FiscalYear],$G$4)")

    def rflag(col):
        return dict(year=f"=COUNTIFS(Refunds[{col}],TRUE,Refunds[FiscalYear],{{c}}$4)",
                    total=f"=COUNTIF(Refunds[{col}],TRUE)", amount=f"=SUMIFS(Refunds[Amount],Refunds[{col}],TRUE)",
                    cur=f"=SUMIFS(Refunds[Amount],Refunds[{col}],TRUE,Refunds[FiscalYear],$G$4)")

    def pflag(col):
        return dict(year=f"=COUNTIFS(RefundFlags[{col}],1,RefundFlags[FiscalYear],{{c}}$4)",
                    total=f"=COUNTIF(RefundFlags[{col}],1)", amount=f"=SUMIFS(RefundFlags[Amount],RefundFlags[{col}],1)",
                    cur=f"=SUMIFS(RefundFlags[Amount],RefundFlags[{col}],1,RefundFlags[FiscalYear],$G$4)")
    receiver = ("(XLOOKUP(Credits[SalesReturnID],ReturnLines[SalesReturnID],ReturnLines[ReceivedByEmployeeID])"
                "=Credits[ApprovedByEmployeeID])")
    spec = [
        ("T1", "Credit above the approver's limit (GrandTotal > MaxApprovalAmount)", "C2", "Credit memos",
         cflag("AboveLimit"), "Credits", tt["cm_above"], "gt"),
        ("T2", "Credit approver also applied cash to the credited invoice", "C4", "Credit memos", cflag("CashAndCredit"),
         "Credits", tt["cash_credit"], "gt"),
        ("T3", "... and did so on or before the credit date", "C4", "Credit memos", cflag("AppliedByCreditDate"),
         "Credits", tt["cc_early"], "gt"),
        ("T4", "Credit approver recorded or applied cash on the credited invoice", "C4", "Credit memos",
         cflag("HandledCash"), "Credits", tt["cc_rec"], "gt"),
        ("T5", "Return received by the credit's approver", "C1", "Credit memos",
         dict(year=f"=SUMPRODUCT((Credits[FiscalYear]={{c}}$4)*{receiver})", total=f"=SUMPRODUCT(--{receiver})",
              amount=f"=SUMPRODUCT({receiver}*Credits[GrandTotal])", cur=""), "Credits, ReturnLines", [], "gt"),
        ("T6", "Credit or refund approved before the approver's hire or after termination", "C2, C6",
         "Credits and refunds",
         dict(year="=COUNTIFS(Credits[OutsideEmployment],TRUE,Credits[FiscalYear],{c}$4)+COUNTIFS("
                   "Refunds[OutsideEmployment],TRUE,Refunds[FiscalYear],{c}$4)",
              total="=COUNTIF(Credits[OutsideEmployment],TRUE)+COUNTIF(Refunds[OutsideEmployment],TRUE)", amount="",
              cur=""), "Credits, Refunds", tt["outside_employment"], None),
        ("T7", "Refund above the approver's limit", "C6", "Refunds", rflag("AboveLimit"), "Refunds", tt["rf_above"],
         "amt"),
        ("T8", "Refund approved by the credit's approver", "C6", "Refunds", rflag("SameApprover"), "Refunds",
         tt["same_approver"], "amt"),
        ("T9", "Refund dated before the last payment on the credited invoice", "C7", "Refunds",
         rflag("BeforePayment"), "Refunds", tt["before"], "amt"),
        ("T10", "... and before any payment on it", "C7", "Refunds", rflag("BeforeAnyPayment"), "Refunds",
         tt["nothing"], "amt"),
        ("T11", "Customer past due on the refund date (any amount)", "C8", "Refunds", pflag("PastDueAny"),
         "RefundFlags (Credits.sql)", tt["pd1"], "amt"),
        ("T12", "Customer past due by at least the refund on the refund date", "C8", "Refunds",
         pflag("PastDueAtLeastRefund"), "RefundFlags (Credits.sql)", tt["pd2"], "amt"),
        ("T13", "Refund method unlike every receipt on the credited invoice", "C8", "Refunds", rflag("MethodMismatch"),
         "Refunds", tt["mism"], "amt"),
    ]
    r = 5
    at = {}
    for tid, name, cp, pop, fl, source, items, key in spec:
        put(ws, {f"A{r}": tid, f"B{r}": name, f"C{r}": cp, f"D{r}": pop, f"K{r}": source})
        for c in "EFG":
            put(ws, {f"{c}{r}": fl["year"].format(c=c)})
        put(ws, {f"H{r}": fl["total"]})
        if fl["amount"]:
            put(ws, {f"I{r}": fl["amount"]})
        if fl["cur"]:
            put(ws, {f"J{r}": fl["cur"]})
        if tid == "T6":
            yrs = [sum(1 for e_, d_ in items if year_of(d_) == y) for y in years]
            st = dict(n=len(items), years=yrs)
        elif tid == "T5":
            st = dict(n=tt["receiver_is_approver"], years=[0, 0, 0] if not tt["receiver_is_approver"] else None)
        else:
            st = f.stat(items, key)
        b.check(t, f"{tid} {name}: total", st["n"], f"=Tests!H{r}", 0, COUNT)
        if st.get("years") is not None:
            for c, y, n in zip("EFG", years, st["years"]):
                b.check(t, f"{tid} {y}", n, f"=Tests!{c}{r}", 0, COUNT)
        if key and items:
            b.check(t, f"{tid} amount", st["amt"], f"=Tests!I{r}")
            b.check(t, f"{tid} {f.C} amount", st["cur_amt"], f"=Tests!J{r}")
        at[tid] = r
        r += 1
    fmt(ws, f"E5:H{r}", COUNT)
    fmt(ws, f"I5:J{r}", MONEY)
    b.found["tests"] = at
    # structural tests (totals only)
    struct = [
        ("T14", "Refunds per credit above one", "C7", "Refunds", "=ROWS(Refunds)-ROWS(UNIQUE(Refunds[CreditMemoID]))",
         0),
        ("T15", "Refunded credits without a refund", "C7", "Credit memos",
         '=COUNTIF(Credits[Status],"Refunded")-SUM(--ISNUMBER(XMATCH(FILTER(Credits[CreditMemoID],'
         'Credits[Status]="Refunded"),Refunds[CreditMemoID])))', 0),
        ("T16", "Credit lines without a clawback", "C5", "Credit lines",
         "=SUM(Credits[Lines])-ROWS(UNIQUE(Clawbacks[CreditMemoLineID]))", tt["cb_lines"] - tt["cb_distinct"]),
        ("T17", "Credit lines with more than one clawback", "C5", "Clawbacks",
         "=ROWS(Clawbacks)-ROWS(UNIQUE(Clawbacks[CreditMemoLineID]))", len(f.adj) - tt["cb_distinct"]),
        ("T18", "Clawback base not the credit line's total, or rate not the accrual's", "C5", "Clawbacks",
         "=COUNTIF(Clawbacks[BaseMatches],FALSE)+COUNTIF(Clawbacks[RateMatches],FALSE)",
         2 * len(f.adj) - tt["cb_base"] - tt["cb_rate"]),
        ("T19", "Clawback amount not ROUND(base x rate, 2)", "C5", "Clawbacks",
         "=SUMPRODUCT(--(ABS(ROUND(Clawbacks[CommissionBaseReductionAmount]*Clawbacks[CommissionRatePct],2)"
         "-Clawbacks[CommissionAdjustmentAmount])>0.001))", len(f.adj) - tt["cb_round"]),
        ("T20", "Clawback not on the credit's date or not by its approver", "C5", "Clawbacks",
         "=COUNTIF(Clawbacks[SameAsCredit],FALSE)", len(f.adj) - tt["cb_same"]),
    ]
    for tid, name, cp, pop, formula, exp in struct:
        put(ws, {f"A{r}": tid, f"B{r}": name, f"C{r}": cp, f"D{r}": pop, f"H{r}": formula,
                 f"K{r}": "Credits, Refunds, Clawbacks"})
        b.check(t, f"{tid} {name}", exp, f"=Tests!H{r}", 0, COUNT)
        at[tid] = r
        r += 1
    put(ws, {f"A{r}": "T21", f"B{r}": "Preparer against approver", f"C{r}": "C2, C6", f"D{r}": "Credits and refunds",
             f"H{r}": "Not testable",
             f"K{r}": "No preparer column; GLEntry.CreatedByEmployeeID names the approver"})
    fmt(ws, f"H5:H{r}", COUNT)
    ws.Range(f"A4:K{r}").Borders.LineStyle = 1
    ws.Range(f"A4:K{r}").Borders.Color = 0xDCD8D5
    ws.Range(f"B5:B{r}").WrapText = True
    ws.Range(f"K5:K{r}").WrapText = True
    r += 2

    # by approver title
    heading(ws, r, "Authority by approver's job title")
    r += 1
    header(ws, r, 1, ["", "Approver's job title", "Limit", "Document", "Documents", "Above limit", "", "",
                      "Amount above limit", f"Amount above limit {f.C}", "Largest document"])
    r += 1
    title_rows = []
    for table, label, key in (("Credits", "Credit memos", "gt"), ("Refunds", "Refunds", "amt")):
        items = f.cm.values() if table == "Credits" else f.rf.values()
        amount_col = "GrandTotal" if table == "Credits" else "Amount"
        for ti, n in sorted(Counter(f.title(x["appr"]) for x in items).items(), key=lambda kv: -kv[1]):
            sel = [x for x in items if f.title(x["appr"]) == ti]
            above = [x for x in sel if x[key] > f.emp[x["appr"]]["limit"]]
            put(ws, {f"B{r}": ti, f"C{r}": f'=MAXIFS({table}[ApproverLimit],{table}[ApproverTitle],B{r})',
                     f"D{r}": label, f"E{r}": f'=COUNTIF({table}[ApproverTitle],B{r})',
                     f"F{r}": f'=COUNTIFS({table}[ApproverTitle],B{r},{table}[AboveLimit],TRUE)',
                     f"I{r}": f'=SUMIFS({table}[{amount_col}],{table}[ApproverTitle],B{r},{table}[AboveLimit],TRUE)',
                     f"J{r}": f'=SUMIFS({table}[{amount_col}],{table}[ApproverTitle],B{r},{table}[AboveLimit],TRUE,'
                              f'{table}[FiscalYear],{f.C})',
                     f"K{r}": f'=MAXIFS({table}[{amount_col}],{table}[ApproverTitle],B{r})'})
            b.check(t, f"{label.lower()} approved by {plural(ti)}", n, f"=Tests!E{r}", 0, COUNT)
            b.check(t, f"{label.lower()} above limit, {plural(ti)}", len(above), f"=Tests!F{r}", 0, COUNT)
            b.check(t, f"{label.lower()} above limit, {plural(ti)}, amount", r2(sum(x[key] for x in above)),
                    f"=Tests!I{r}")
            if not above:
                b.check(t, f"{label.lower()} approved by {plural(ti)}: within limit, amount",
                        r2(sum(x[key] for x in sel)), f'=SUMIFS({table}[{amount_col}],{table}[ApproverTitle],"{ti}")')
            title_rows.append(r)
            r += 1
    fmt(ws, f"C{title_rows[0]}:C{r}", COUNT)
    fmt(ws, f"E{title_rows[0]}:F{r}", COUNT)
    fmt(ws, f"I{title_rows[0]}:K{r}", MONEY)
    r += 1

    # timing of the refunds before payment
    heading(ws, r, "Refunds dated before the customer's payment: timing and cause")
    r += 1
    w = tt["wait"]
    timing = [("Days from the refund to the last payment: fewest",
               "=MINIFS(Refunds[DaysToLastPayment],Refunds[BeforePayment],TRUE)", min(w), COUNT),
              ("Most", "=MAXIFS(Refunds[DaysToLastPayment],Refunds[BeforePayment],TRUE)", max(w), COUNT),
              ("Mean", "=AVERAGEIFS(Refunds[DaysToLastPayment],Refunds[BeforePayment],TRUE)", sum(w) / len(w), "0.0")]
    for label, formula, exp, nf in timing:
        put(ws, {f"B{r}": label, f"H{r}": formula})
        fmt(ws, f"H{r}", nf)
        b.check(t, f"refunds before payment: {label.lower()}", exp, f"=Tests!H{r}", 0.0001 if nf != COUNT else 0, nf)
        r += 1
    cz = f.cause
    pasted = [["Refunds before payment also dated before the invoice's due date", cz["before_due"]],
              ["Credits that posted a part to 2060", cz["to_2060"]],
              ["... of which posted when nothing had been paid on the invoice", cz["unpaid"]]]
    for i, (label, v) in enumerate(pasted):
        put(ws, {f"B{r + i}": label})
    paste(ws, r, 8, [[v] for _, v in pasted], "refunds before payment and the credits' 2060 parts (the timing of the "
                                               "credits posted to 2060 against the payments on their invoices)",
          {0: COUNT})
    r += len(pasted) + 1

    # the combined exception list
    heading(ws, r, "Exceptions of the four register tests combined by year (UNION ALL), with rates per 1,000 documents")
    r += 1
    sum0 = r
    header(ws, r, 1, ["", "TestID", "", "Population", str(years[0]), str(years[1]), str(years[2]), "Total",
                      f"Per 1,000, {years[0]}", f"Per 1,000, {years[1]}", f"Per 1,000, {years[2]}"])
    for c, y in zip("EFG", years):
        ws.Range(f"{c}{r}").Value = y
    list_row = r + 9
    reg = [("CM AboveLimit", "Credit memos", tt["cm_above"]), ("CM CashAndCredit", "Credit memos", tt["cash_credit"]),
           ("RF AboveLimit", "Refunds", tt["rf_above"]), ("RF BeforePayment", "Refunds", tt["before"])]
    r += 1
    reg0 = r
    for tid, pop, items in reg:
        table = "Credits" if pop == "Credit memos" else "Refunds"
        put(ws, {f"B{r}": tid, f"D{r}": pop, f"H{r}": f"=SUM(E{r}:G{r})"})
        for c, cc in zip("EFG", "IJK"):
            put(ws, {f"{c}{r}": f"=COUNTIFS(INDEX($B${list_row + 1}#,0,1),$B{r},INDEX($B${list_row + 1}#,0,4),{c}${sum0})",
                     f"{cc}{r}": f"=1000*{c}{r}/COUNTIFS({table}[FiscalYear],{c}${sum0})"})
        st = f.stat(items, "gt" if table == "Credits" else "amt")
        for c, cc, y, n in zip("EFG", "IJK", years, st["years"]):
            b.check(t, f"register {tid} {y}", n, f"=Tests!{c}{r}", 0, COUNT)
            pop_n = len(f.in_year(f.cm.values() if table == "Credits" else f.rf.values(), y))
            b.check(t, f"register {tid} {y} per 1,000", 1000 * n / pop_n, f"=Tests!{cc}{r}", 0.05, "0.0")
        r += 1
    put(ws, {f"B{r}": "Total", f"H{r}": f"=SUM(H{reg0}:H{r - 1})"})
    for c in "EFG":
        put(ws, {f"{c}{r}": f"=SUM({c}{reg0}:{c}{r - 1})"})
    bold(ws, f"B{r}:H{r}")
    b.check(t, "register additions, total", sum(len(x[2]) for x in reg), f"=Tests!H{r}", 0, COUNT)
    b.found["register_total"] = f"=Tests!H{r}"
    b.found["register_rows"] = {tid: reg0 + i for i, (tid, _, _) in enumerate(reg)}
    fmt(ws, f"E{reg0}:H{r}", COUNT)
    fmt(ws, f"I{reg0}:K{r}", "0.0")
    r += 2
    assert r <= list_row, "the combined list would overlap the summary"
    header(ws, list_row, 2, ["TestID", "DocumentNumber", "DocumentDate", "FiscalYear", "Amount"])

    def part(tid, table, num, day, amount, flag):
        return (f'FILTER(HSTACK(IF({table}[{flag}],"{tid}"),{table}[{num}],{table}[{day}],{table}[FiscalYear],'
                f'{table}[{amount}]),{table}[{flag}])')
    ws.Range(f"B{list_row + 1}").Formula2 = "=VSTACK(" + ",".join([
        part("CM AboveLimit", "Credits", "CreditMemoNumber", "CreditMemoDate", "GrandTotal", "AboveLimit"),
        part("CM CashAndCredit", "Credits", "CreditMemoNumber", "CreditMemoDate", "GrandTotal", "CashAndCredit"),
        part("RF AboveLimit", "Refunds", "RefundNumber", "RefundDate", "Amount", "AboveLimit"),
        part("RF BeforePayment", "Refunds", "RefundNumber", "RefundDate", "Amount", "BeforePayment")]) + ")"
    total = sum(len(x[2]) for x in reg)
    fmt(ws, f"D{list_row + 1}:D{list_row + total}", DATE)
    fmt(ws, f"F{list_row + 1}:F{list_row + total}", MONEY)
    b.check(t, "rows in the combined list", total, f"=ROWS(Tests!B{list_row + 1}#)", 0, COUNT)
    b.check(t, "(TestID, DocumentNumber) unique in the combined list", total,
            f"=ROWS(UNIQUE(CHOOSECOLS(Tests!B{list_row + 1}#,1,2)))", 0, COUNT)

    # the live flags reconciled to the pasted RefundFlags, and the score (to the right of the register summary)
    put(ws, {f"M{sum0}": "Flag", f"N{sum0}": "Refunds agreeing", f"O{sum0}": "Of"})
    bold(ws, f"M{sum0}:O{sum0}")
    for i, col in enumerate(("AboveLimit", "CreditAboveLimit", "MethodMismatch", "BeforePayment")):
        rr = sum0 + 1 + i
        put(ws, {f"M{rr}": col,
                 f"N{rr}": f"=SUMPRODUCT(--(XLOOKUP(Refunds[RefundNumber],RefundFlags[RefundNumber],RefundFlags[{col}])"
                           f"=--Refunds[{col}]))",
                 f"O{rr}": "=ROWS(Refunds)"})
        b.check(t, f"refund flag {col}: live equals RefundFlags", len(f.rf), f"=Tests!N{rr}", 0, COUNT)
    widths(ws, {"M": 22, "N": 16, "O": 8})
    # the score distribution (the ranking itself is Requirement 5's report)
    sc = Counter(tt["score"].values())
    put(ws, {f"M{sum0 + 6}": "Score (five flags)", f"N{sum0 + 6}": "Refunds", f"O{sum0 + 6}": "Amount"})
    bold(ws, f"M{sum0 + 6}:O{sum0 + 6}")
    for s_ in range(6):
        rr = sum0 + 7 + s_
        put(ws, {f"M{rr}": s_, f"N{rr}": f"=COUNTIF(RefundFlags[Score],M{rr})",
                 f"O{rr}": f"=SUMIFS(RefundFlags[Amount],RefundFlags[Score],M{rr})"})
        b.check(t, f"refunds scoring {s_}", sc.get(s_, 0), f"=Tests!N{rr}", 0, COUNT)
    hi = [k for k, v in tt["score"].items() if v >= 4]
    b.check(t, "refunds scoring 4 or 5: amount", r2(sum(f.rf[k]["amt"] for k in hi)),
            f"=SUM(Tests!O{sum0 + 11}:O{sum0 + 12})")
    fmt(ws, f"N{sum0 + 7}:N{sum0 + 12}", COUNT)
    fmt(ws, f"O{sum0 + 7}:O{sum0 + 12}", MONEY)

    # the model answer, below the combined list
    text_row = list_row + total + 3
    ws.Range(f"A{list_row - 1}").Value = (
        f"The combined list (a VSTACK of FILTERs, the UNION ALL of Credits.sql); the written conclusions are below it, "
        f"from row {text_row}.")
    ws.Range(f"A{list_row - 1}").Font.Bold = True
    cb = tt
    pd2 = f.stat(tt["pd2"], "amt")
    mism = f.stat(tt["mism"], "amt")
    methods = sorted({x["method"] for x in f.rf.values()})
    expected_mism = sum(1 - len(tt["methods"][k] & set(methods)) / len(methods) for k in f.rf)
    text_block(ws, text_row, MA, [
        f"Authority. {len(tt['cm_above'])} credits ({money(f.stat(tt['cm_above'])['amt'])}; {len(f.in_year(tt['cm_above'], f.C))} "
        f"in fiscal {f.C}, {money(f.stat(tt['cm_above'])['cur_amt'])}) were approved above the approver's limit, all by "
        "customer service representatives, whose general limit is $0; the Customer Service Manager's $25,000 is never "
        f"exceeded. {len(tt['rf_above'])} refunds ({money(f.stat(tt['rf_above'], 'amt')['amt'])}) were approved above "
        "the limit by Staff Accountants and Administrative Specialists, also with limits of $0; the Accounting "
        "Manager's refunds are all within the $25,000 limit. No credit or refund was approved before the approver's "
        "hire or after termination. MaxApprovalAmount is a general limit: the delegation of authority for credits and "
        "refunds, if one exists, is outside the records, so these are exceptions against the only criterion the data "
        "hold.",
        f"Separation of duties. The credit's approver applied cash to the credited invoice on {len(tt['cash_credit'])} "
        f"credits ({money(f.stat(tt['cash_credit'])['amt'])}), {len(tt['cc_early'])} of them on or before the credit "
        f"date; counting receipts recorded as well as applied, {len(tt['cc_rec'])} credits. No refund was approved by "
        "the credit's approver, and every return was received in the warehouse by someone other than the credit's "
        "approver. The preparer cannot be tested against the approver: neither CreditMemo nor CustomerRefund has a "
        "preparer column, and GLEntry.CreatedByEmployeeID names the approver on every row, as it names the chief "
        "executive on every sales invoice, so the records cannot show who keyed a credit or a refund. That is a gap "
        "in the evidence, not evidence of self-approval.",
        f"Refunds and payment. {len(tt['before'])} refunds ({money(f.stat(tt['before'], 'amt')['amt'])}) are dated "
        "before the last payment applied to the credited invoice (definition: the refund date is earlier than the "
        f"latest ApplicationDate on the invoice), {len(tt['nothing'])} of them before any payment; the payment arrived "
        f"{min(w)} to {max(w)} days later (mean {sum(w) / len(w):.1f}). The cause is in how credits post: a credit "
        "goes to receivables only for what the invoice's final payments leave unpaid, and the rest to 2060, so "
        f"{cz['unpaid']} of the {cz['to_2060']} credits to 2060 were posted when nothing had been paid, and the refund "
        "control pays out 2060 without checking that the customer's payment has arrived.",
        f"Offset and method. On the refund date (as of that date: GrandTotal less the applications and credits dated by "
        "then, for invoices whose DueDate had passed, as Chapter 8 aged receivables), "
        f"{len(tt['pd1'])} refunds went to customers with a past-due balance, {pd2['n']} of them past due by at least "
        f"the refund ({money(pd2['amt'])}; {pd2['cur']} in fiscal {f.C}, {money(pd2['cur_amt'])}): balances that could "
        f"have been offset. {mism['n']} refunds ({money(mism['amt'])}) went by a method that none of the receipts on "
        f"the credited invoice used. No customer pays by one method only, and a method chosen at random from the "
        f"{word(len(methods))} would mismatch about {expected_mism:.0f} times, so this is an anomaly to follow up, not "
        "a rule.",
        f"Clean. One refund per refunded credit, equal to the credit's part in 2060; a clawback for every credit line "
        f"({cb['cb_lines']}), at the line total and the accrual's rate, on the credit's date and by its approver; every "
        "clawback amount is base x rate rounded half up (Excel's ROUND agrees on all of them; SQLite's ROUND gives a "
        "cent less on three exact half-cent products, stored just below the half in binary floating point). "
        f"The {len(f.adj) - f.commission['pending']} clawbacks netted in later "
        f"commission payments leave {f.commission['pending']} pending at the end of {f.C}."], span=10)


# --- Requirement 6: the sample ---------------------------------------------------------------------------------------

NOT_KEY = ("LET(c,Refunds[CustomerID],a,Refunds[Amount],t,SUMIFS(Refunds[Amount],Refunds[CustomerID],c),"
           "(a<KeyAmount)*(t<=KeyCustomerTotal)=1)")
NOT_DOC = "Not tested: no document in the database"


def r6(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    t = "Requirement 6"
    s = f.sampling
    ws = new_sheet(b, "Sample")
    widths(ws, {"A": 46, "B": 16, "C": 13, "D": 13, "E": 14, "F": 16, "G": 26, "H": 18, "I": 18, "J": 22, "K": 18})
    title(ws, "Requirement 6: Sampling what the database cannot show",
          "Refunds of fiscal 2024 to 2026: key items in full, a random selection of the rest frozen with Paste Values, "
          "and the evaluation rule written before testing.")
    heading(ws, 4, "Attributes")
    merged_table(ws, 5, [1, 4, 5], ["Attribute", "Evidence needed", "A deviation is"], [
        ["A1. A written request from the customer", "The customer's request for the refund (letter, e-mail, or portal "
         "record), dated before the refund and for its amount; outside the database.",
         "No request, a request dated after the refund, or a request for another amount or another payee."],
        ["A2. A payee checked against the customer master by someone independent", "Evidence that someone outside "
         "customer service, other than the refund's approver, compared the payee and bank account with the customer "
         "master before payment; outside the database.", "No evidence of the check, a check by the approver or by "
         "customer service, or a payee or account that differs from the customer master."],
        ["A3. For refunds of returns coded Damaged, an inspection record of the goods", "The warehouse's inspection "
         "record of the goods returned (and any carrier claim); outside the database.",
         "No inspection record, or a record that does not support the reason code. Applies to Damaged returns only."],
        ["D1. The refund dated before the customer's payment (the data attribute)", "The database: the refund date "
         "against the last payment applied to the credited invoice (Refunds[BeforePayment]).",
         "The refund is dated before the last payment on the credited invoice."]])

    # parameters and tbl-19-03
    heading(ws, 11, "Parameters (chosen before the selection)")
    put(ws, {"A12": "Confidence level (1 less the risk of overreliance)", "B12": CONFIDENCE,
             "A13": "Tolerable deviation rate", "B13": TOLERABLE,
             "A14": "Expected deviation rate", "B14": EXPECTED,
             "A15": "Sample size from tbl-19-03", "A16": "Deviations the plan allows",
             "A17": "Key item: a refund of at least", "B17": KEY_AMOUNT,
             "A18": "Key item: every refund to a customer whose refunds over the three years exceed", "B18": KEY_CUSTOMER,
             "A19": "Selection frozen on", "B19": serial(pq.today()),
             "A20": "Method", "B20": "SORTBY and RANDARRAY over the remainder, the first SampleSize kept, Paste Values"})
    fmt(ws, "B12:B14", "0%")
    fmt(ws, "B15:B16", COUNT)
    fmt(ws, "B17:B18", MONEY)
    fmt(ws, "B19", DATE)
    for name, addr in (("SampleConfidence", "$B$12"), ("TolerableRate", "$B$13"), ("ExpectedRate", "$B$14"),
                       ("SampleSize", "$B$15"), ("KeyAmount", "$B$17"), ("KeyCustomerTotal", "$B$18")):
        xl.name_cell(wb, name, f"Sample!{addr}")
    put(ws, {"B15": "=INDEX($E$15:$H$17,MATCH(ExpectedRate,$D$15:$D$17,0),MATCH(1,($E$13:$H$13=SampleConfidence)*"
                    "($E$14:$H$14=TolerableRate),0))",
             "B16": "=INDEX($E$20:$H$22,MATCH(ExpectedRate,$D$20:$D$22,0),MATCH(1,($E$13:$H$13=SampleConfidence)*"
                    "($E$14:$H$14=TolerableRate),0))"})
    put(ws, {"D12": "tbl-19-03: sample size", "D13": "Confidence", "D14": "Tolerable rate",
             "D19": "tbl-19-03: deviations allowed", "D15": 0.0, "D16": 0.01, "D17": 0.02, "D20": 0.0, "D21": 0.01,
             "D22": 0.02})
    bold(ws, "D12")
    bold(ws, "D19")
    combos = TBL_19_03[0.0]
    for j, (conf, tol, _, _) in enumerate(combos):
        c = letter(5 + j)
        put(ws, {f"{c}13": conf, f"{c}14": tol})
        for i, exp_rate in enumerate((0.0, 0.01, 0.02)):
            row = TBL_19_03[exp_rate][j]
            put(ws, {f"{c}{15 + i}": row[2], f"{c}{20 + i}": row[3]})
    fmt(ws, "E13:H14", "0%")
    fmt(ws, "D15:D17", "0%")
    fmt(ws, "D20:D22", "0%")
    b.check(t, "sample size from tbl-19-03", s["n"], "=SampleSize", 0, COUNT)
    b.check(t, "deviations the plan allows", 0, "=Sample!B16", 0, COUNT)

    # the population and the key items
    heading(ws, 24, "Population")
    put(ws, {"A25": f"Refunds, fiscal {f.F} to {f.C}", "B25": "=ROWS(Refunds)", "C25": "=SUM(Refunds[Amount])",
             "A26": "Key items, taken in full", "B26": "=ROWS(A32#)", "C26": "=SUM(INDEX(A32#,0,4))",
             "A27": "Remaining refunds, the population to sample", "B27": "=B25-B26", "C27": "=C25-C26",
             "A28": "Sample as a share of the remaining refunds", "B28": "=SampleSize/B27"})
    fmt(ws, "B25:B27", COUNT)
    fmt(ws, "C25:C27", MONEY)
    fmt(ws, "B28", "0.0%")
    rf_total = r2(sum(x["amt"] for x in f.rf.values()))
    b.check(t, "refunds in the population", len(f.rf), "=Sample!B25", 0, COUNT)
    b.check(t, "refund total", rf_total, "=Sample!C25")
    b.check(t, "key items", len(s["key"]), "=Sample!B26", 0, COUNT)
    b.check(t, "key items, amount", s["key_total"], "=Sample!C26")
    b.check(t, "remaining refunds", len(s["rest"]), "=Sample!B27", 0, COUNT)
    b.check(t, "remaining refunds, amount", s["rest_total"], "=Sample!C27")
    b.check(t, "sample as a share of the remainder", s["share"], "=Sample!B28", 5e-6, "0.0%")
    heading(ws, 30, "Key items")
    header(ws, 31, 1, ["RefundNumber", "RefundDate", "CustomerID", "Amount", "Customer's refunds, three years",
                       "Why a key item", "D1: before payment"])
    ws.Range("A32").Formula2 = (
        "=LET(c,Refunds[CustomerID],a,Refunds[Amount],t,SUMIFS(Refunds[Amount],Refunds[CustomerID],c),"
        "k,(a>=KeyAmount)+(t>KeyCustomerTotal)>0,SORT(FILTER(HSTACK(Refunds[RefundNumber],Refunds[RefundDate],c,a,t,"
        'IF((a>=KeyAmount)*(t>KeyCustomerTotal),"Amount and customer",IF(a>=KeyAmount,"Amount","Customer total")),'
        "Refunds[BeforePayment]),k)))")
    nk = len(s["key"])
    fmt(ws, f"B32:B{31 + nk}", DATE)
    fmt(ws, f"D32:E{31 + nk}", MONEY)
    b.check(t, "key items listed", ", ".join(r["num"] for r in s["key"]), '=TEXTJOIN(", ",TRUE,INDEX(Sample!A32#,0,1))')
    b.check(t, "key items dated before the customer's payment (D1)", s["key_dev"], "=COUNTIF(INDEX(Sample!A32#,0,7),TRUE)",
            0, COUNT)

    # the evaluation rule, written before the test
    e0 = 33 + nk + 2
    heading(ws, e0, "Evaluation rule, written before testing: the upper deviation limit for zero to three deviations")
    header(ws, e0 + 1, 1, ["Deviations found in the sample", "Upper deviation limit", "Supports reliance at the "
                                                                                       "tolerable rate?"])
    for k in range(4):
        r = e0 + 2 + k
        put(ws, {f"A{r}": k, f"B{r}": f"=BETA.INV(SampleConfidence,A{r}+1,SampleSize-A{r})",
                 f"C{r}": f'=IF(B{r}<=TolerableRate,"Yes","No")'})
        b.check(t, f"upper deviation limit, {k} deviations", s["udl"][k], f"=Sample!B{r}", 5e-6, "0.00%")
        b.check(t, f"supports reliance with {k} deviations", "Yes" if s["udl"][k] <= TOLERABLE else "No",
                f"=Sample!C{r}")
    fmt(ws, f"A{e0 + 2}:A{e0 + 5}", COUNT)
    fmt(ws, f"B{e0 + 2}:B{e0 + 5}", "0.00%")
    put(ws, {f"A{e0 + 6}": "Rule: rely on the control only if the upper deviation limit is at or below the tolerable "
                           "rate; at n = 59 that means no deviation at all."})
    ws.Range(f"A{e0 + 6}").Font.Italic = True

    # the frozen selection
    s0 = e0 + 9
    heading(ws, s0, "The random selection of the remaining refunds, frozen")
    cols = ["#", "RefundNumber", "RefundDate", "CustomerID", "Amount", "Approver's job title", "Return reason",
            "A1: written request", "A2: payee checked", "A3: inspection (Damaged only)", "D1: before payment (data)"]
    header(ws, s0 + 1, 1, cols)
    first = s0 + 2
    n = s["n"]
    last = first + n - 1
    draw = (f"=LET(c,Refunds[CustomerID],a,Refunds[Amount],t,SUMIFS(Refunds[Amount],Refunds[CustomerID],c),"
            f"rest,FILTER(Refunds[RefundNumber],(a<KeyAmount)*(t<=KeyCustomerTotal)),"
            f"TAKE(SORTBY(rest,RANDARRAY(ROWS(rest))),SampleSize))")
    ws.Range(f"B{first}").Formula2 = draw
    xl.retry(wb.Application.Calculate)
    xl.wait_ready(wb.Application)
    spill = ws.Range(f"B{first}").SpillingToRange
    assert spill.Rows.Count == n, f"the draw spilled {spill.Rows.Count} rows, not {n}"
    drawn = [row[0] for row in spill.Value]
    ws.Range(f"B{first}").ClearContents()
    ws.Range(f"B{first}:B{last}").Value = tuple((x,) for x in drawn)          # Paste Values: the selection is frozen
    ws.Range(f"B{s0 + 1}").AddComment(
        f"Drawn by Excel's RANDARRAY when this solution was built, on {pq.today()}, with\n{draw}\nand frozen with Paste "
        "Values (Requirement 6). Your own draw will differ; the evaluation below follows the draw.")
    lk = lambda col, r: f"=XLOOKUP($B{r},Refunds[RefundNumber],Refunds[{col}])"  # noqa: E731
    for i in range(n):
        r = first + i
        reason = (f"=XLOOKUP(XLOOKUP(XLOOKUP($B{r},Refunds[RefundNumber],Refunds[CreditMemoID]),Credits[CreditMemoID],"
                  f"Credits[SalesReturnID]),ReturnLines[SalesReturnID],ReturnLines[ReasonCode])")
        put(ws, {f"A{r}": i + 1, f"C{r}": lk("RefundDate", r), f"D{r}": lk("CustomerID", r), f"E{r}": lk("Amount", r),
                 f"F{r}": lk("ApproverTitle", r), f"G{r}": reason, f"H{r}": NOT_DOC, f"I{r}": NOT_DOC,
                 f"J{r}": f'=IF(G{r}="Damaged","{NOT_DOC}","Not applicable")',
                 f"K{r}": f'=IF(XLOOKUP($B{r},Refunds[RefundNumber],Refunds[BeforePayment]),"Deviation","No deviation")'})
    fmt(ws, f"C{first}:C{last}", DATE)
    fmt(ws, f"E{first}:E{last}", MONEY)
    ws.Range(f"H{first}:J{last}").Font.Italic = True
    rng = f"Sample!B{first}:B{last}"
    b.check(t, "refunds selected", n, f"=COUNTA({rng})", 0, COUNT)
    b.check(t, "selected refunds that are distinct", n, f"=ROWS(UNIQUE({rng}))", 0, COUNT)
    b.check(t, "selected refunds found among the refunds", n, f"=SUM(--ISNUMBER(XMATCH({rng},Refunds[RefundNumber])))",
            0, COUNT)
    b.check(t, "selected refunds that are key items", 0, f"=SUM(--ISNUMBER(XMATCH({rng},INDEX(Sample!A32#,0,1))))", 0,
            COUNT)

    # the data attribute applied to the sample, and the population
    v0 = last + 3
    heading(ws, v0, "D1 applied to the sample, and compared with the population test of Requirement 4")
    put(ws, {f"A{v0 + 1}": "Deviations in the sample", f"B{v0 + 1}": f'=COUNTIF(K{first}:K{last},"Deviation")',
             f"A{v0 + 2}": "Sample deviation rate", f"B{v0 + 2}": f"=B{v0 + 1}/SampleSize",
             f"A{v0 + 3}": "Upper deviation limit", f"B{v0 + 3}": f"=BETA.INV(SampleConfidence,B{v0 + 1}+1,"
                                                                   f"SampleSize-B{v0 + 1})",
             f"A{v0 + 4}": "The sample's conclusion",
             f"B{v0 + 4}": f'=IF(B{v0 + 3}<=TolerableRate,"Supports reliance","Does not support reliance")',
             f"A{v0 + 5}": "Remaining refunds dated before the payment (population test)",
             f"B{v0 + 5}": f"=SUM(--FILTER(Refunds[BeforePayment],{NOT_KEY}))",
             f"A{v0 + 6}": "Their rate", f"B{v0 + 6}": f"=B{v0 + 5}/B27",
             f"A{v0 + 7}": "Key items dated before the payment", f"B{v0 + 7}": "=COUNTIF(INDEX(A32#,0,7),TRUE)",
             f"A{v0 + 8}": "All refunds dated before the payment (Requirement 4)",
             f"B{v0 + 8}": "=COUNTIF(Refunds[BeforePayment],TRUE)",
             f"A{v0 + 9}": "Deviations a sample of SampleSize expects", f"B{v0 + 9}": f"=SampleSize*B{v0 + 5}/B27",
             f"A{v0 + 10}": "Plausible draws: lowest count (each tail below 5%)",
             f"B{v0 + 10}": f"=XMATCH(TRUE,HYPGEOM.DIST(SEQUENCE(SampleSize+1,,0),SampleSize,B{v0 + 5},B27,TRUE)>=0.05)-1",
             f"A{v0 + 11}": "Plausible draws: highest count",
             f"B{v0 + 11}": f"=XMATCH(TRUE,HYPGEOM.DIST(SEQUENCE(SampleSize+1,,0),SampleSize,B{v0 + 5},B27,TRUE)>0.95)-1",
             f"A{v0 + 12}": "Probability of fewer than the lowest count",
             f"B{v0 + 12}": f"=HYPGEOM.DIST(B{v0 + 10}-1,SampleSize,B{v0 + 5},B27,TRUE)",
             f"A{v0 + 13}": "Probability of no more than the highest count",
             f"B{v0 + 13}": f"=HYPGEOM.DIST(B{v0 + 11},SampleSize,B{v0 + 5},B27,TRUE)",
             f"A{v0 + 14}": "Upper deviation limit at the lowest count",
             f"B{v0 + 14}": f"=BETA.INV(SampleConfidence,B{v0 + 10}+1,SampleSize-B{v0 + 10})",
             f"A{v0 + 15}": "Upper deviation limit at the expected count",
             f"B{v0 + 15}": f"=BETA.INV(SampleConfidence,ROUND(B{v0 + 9},0)+1,SampleSize-ROUND(B{v0 + 9},0))",
             f"A{v0 + 16}": "Upper deviation limit at the highest count",
             f"B{v0 + 16}": f"=BETA.INV(SampleConfidence,B{v0 + 11}+1,SampleSize-B{v0 + 11})",
             f"A{v0 + 17}": "Probability that a sample finds no deviation",
             f"B{v0 + 17}": f"=HYPGEOM.DIST(0,SampleSize,B{v0 + 5},B27,FALSE)",
             f"A{v0 + 18}": "Comparison",
             f"B{v0 + 18}": f'=IF(AND(B{v0 + 4}="Does not support reliance",B{v0 + 8}>0),"The sample agrees with the '
                            f'population test: the control is not effective","The sample and the population disagree: '
                            f'investigate")'})
    fmt(ws, f"B{v0 + 1}", COUNT)
    fmt(ws, f"B{v0 + 2}:B{v0 + 3}", "0.0%")
    fmt(ws, f"B{v0 + 5}", COUNT)
    fmt(ws, f"B{v0 + 6}", "0.0%")
    fmt(ws, f"B{v0 + 7}:B{v0 + 8}", COUNT)
    fmt(ws, f"B{v0 + 9}", "0.00")
    fmt(ws, f"B{v0 + 10}:B{v0 + 11}", COUNT)
    fmt(ws, f"B{v0 + 12}:B{v0 + 13}", "0.000")
    fmt(ws, f"B{v0 + 14}:B{v0 + 16}", "0.0%")
    fmt(ws, f"B{v0 + 17}", "0.0E+00")
    b.check(t, "remaining refunds dated before the payment", len(s["dev"]), f"=Sample!B{v0 + 5}", 0, COUNT)
    b.check(t, "their rate", len(s["dev"]) / len(s["rest"]), f"=Sample!B{v0 + 6}", 5e-6, "0.0%")
    b.check(t, "key items dated before the payment", s["key_dev"], f"=Sample!B{v0 + 7}", 0, COUNT)
    b.check(t, "all refunds dated before the payment", len(f.tests["before"]), f"=Sample!B{v0 + 8}", 0, COUNT)
    b.check(t, "deviations a sample of 59 expects", s["mean"], f"=Sample!B{v0 + 9}", 5e-5, "0.00")
    b.check(t, "plausible draws: lowest count", s["lo"], f"=Sample!B{v0 + 10}", 0, COUNT)
    b.check(t, "plausible draws: highest count", s["hi"], f"=Sample!B{v0 + 11}", 0, COUNT)
    b.check(t, "probability of fewer than the lowest", s["cdf_lo"], f"=Sample!B{v0 + 12}", 5e-6, "0.000")
    b.check(t, "probability of no more than the highest", s["cdf_hi"], f"=Sample!B{v0 + 13}", 5e-6, "0.000")
    b.check(t, "upper limit at the lowest count", s["udl_lo"], f"=Sample!B{v0 + 14}", 5e-6, "0.0%")
    b.check(t, "upper limit at the expected count", s["udl_mid"], f"=Sample!B{v0 + 15}", 5e-6, "0.0%")
    b.check(t, "upper limit at the highest count", s["udl_hi"], f"=Sample!B{v0 + 16}", 5e-6, "0.0%")
    b.check(t, "probability that a sample finds no deviation", s["zero_draw"], f"=Sample!B{v0 + 17}", 1e-12, "0.0E+00")
    # the conclusion depends on the draw only if a sample of 59 found no deviation (probability above, about 3 in 10^9)
    b.check(t, "the sample's conclusion", "Does not support reliance", f"=Sample!B{v0 + 4}")
    xl.retry(wb.Application.Calculate)
    xl.wait_ready(wb.Application)
    k_drawn = int(ws.Range(f"B{v0 + 1}").Value)
    udl_drawn = float(ws.Range(f"B{v0 + 3}").Value)
    b.found["sample"] = dict(k=k_drawn, udl=udl_drawn, first=first, last=last, conclusion=f"Sample!B{v0 + 4}")
    text_block(ws, v0 + 20, MA, [
        f"Plan. The three attributes need evidence outside the database, so they are sampled: a written request "
        f"(A1), an independent payee check (A2), and, for refunds of Damaged returns, an inspection record (A3). At "
        f"95% confidence, a 5% tolerable rate, and no expected deviations, tbl-19-03 gives a sample of {n} with no "
        f"deviation allowed. The {len(s['key'])} key items ({money(s['key_total'])}: {series(r['num'] for r in s['key'])}) "
        "are every refund of $5,000 or more and every refund to a customer whose refunds over the three years exceed "
        f"$10,000; they are examined in full. The other {len(s['rest'])} refunds ({money(s['rest_total'])}) were put in "
        f"random order with SORTBY and RANDARRAY, the first {n} kept and frozen with Paste Values on {pq.today()}. "
        f"A sample of {n} is {pct(s['share'])} of {len(s['rest'])}: the large-population table is conservative here, "
        "and a finite-population correction would allow a smaller sample.",
        f"Rule, written before testing. The upper deviation limit at {n} is {pct(s['udl'][0], 2)} for no deviation, "
        f"{pct(s['udl'][1], 2)} for one, {pct(s['udl'][2], 2)} for two, and {pct(s['udl'][3], 2)} for three. Only "
        "zero deviations supports reliance at 5%; one deviation in any attribute means the control cannot be relied "
        "on.",
        f"The data attribute. Applied to this draw, D1 finds {k_drawn} refunds dated before the customer's payment "
        f"({pct(k_drawn / n)}), an upper limit of {pct(udl_drawn)}: the control does not support reliance. The "
        f"population test agrees: {len(s['dev'])} of the {len(s['rest'])} remaining refunds deviate "
        f"({pct(len(s['dev']) / len(s['rest']))}), and {s['key_dev']} of the {len(s['key'])} key items. Any draw "
        f"would say the same: a sample of {n} expects {s['mean']:.1f} deviations, and about "
        f"{pct(s['cdf_hi'] - s['cdf_lo'], 0)} of draws find {s['lo']} to {s['hi']}, with upper limits of about "
        f"{pct(s['udl_lo'], 0)} to {pct(s['udl_hi'], 0)}. Where the data allow, the population test replaces the "
        "sample: it found all of them, not an estimate.",
        "What is delivered. The database holds no requests, payee checks, or inspection records, so A1 to A3 cannot "
        "be completed here: the deliverable is the plan, the frozen selection, and the rule, with the attribute "
        "columns marked as not tested. No results are invented; the documents are requested from the owners for "
        "fieldwork."], span=8)
    b.check(t, "D1 deviations in the frozen sample, read back", k_drawn, f"=Sample!B{v0 + 1}", 0, COUNT)


# --- Requirement 7: the largest refund, restocking, and the substantive results -------------------------------------

def r7(b: ExerciseBuild) -> None:
    f = facts(b)
    t = "Requirement 7"
    L = f.largest
    ws = new_sheet(b, "Timeline")
    widths(ws, {"A": 44, "B": 22, "C": 24, "D": 70, "E": 52, "F": 14, "G": 14})
    title(ws, "Requirement 7: The largest refund, the restocking of returns, and the substantive tests")
    heading(ws, 3, "The largest refund (live)")
    lk = lambda col: f"=XLOOKUP($B$5,Refunds[RefundNumber],Refunds[{col}])"  # noqa: E731
    ck = lambda col: f"=XLOOKUP($B$13,Credits[CreditMemoNumber],Credits[{col}])"  # noqa: E731
    rows = [("Largest refund, amount", "=MAX(Refunds[Amount])", MONEY, L["rf"]["amt"]),
            ("Refund", "=XLOOKUP(B4,Refunds[Amount],Refunds[RefundNumber])", None, L["rf"]["num"]),
            ("Refund date", lk("RefundDate"), DATE, L["rf"]["date"][:10]),
            ("Day of the week", '=TEXT(B6,"dddd")', None, L["weekday"]),
            ("Method", lk("PaymentMethod"), None, L["rf"]["method"]),
            ("Approver's job title", lk("ApproverTitle"), None, f.title(L["rf"]["appr"])),
            ("Approver's limit", lk("ApproverLimit"), COUNT, f.emp[L["rf"]["appr"]]["limit"]),
            ("Above the approver's limit", lk("AboveLimit"), None, None),
            ("Cleared", lk("ClearedDate"), DATE, L["rf"]["cleared"][:10]),
            ("Credit memo", lk("CreditMemoNumber"), None, L["cm"]["num"]),
            ("Credit total", ck("GrandTotal"), MONEY, L["cm"]["gt"]),
            ("The largest credit of the three years", "=B14=MAX(Credits[GrandTotal])", None, None),
            ("Credit approver's job title", ck("ApproverTitle"), None, f.title(L["cm"]["appr"])),
            ("Credit approver's limit", ck("ApproverLimit"), COUNT, f.emp[L["cm"]["appr"]]["limit"]),
            ("Credit approver applied cash to the invoice", ck("CashAndCredit"), None, None),
            ("Refund dated before the last payment on the invoice", lk("BeforePayment"), None, None),
            ("Last payment on the invoice", lk("LastPayment"), DATE, L["settled"][:10]),
            ("Methods of the receipts on the invoice", lk("ReceiptMethods"), None, ", ".join(L["methods"])),
            ("Customer", lk("CustomerID"), COUNT, L["rf"]["cust"]),
            ("Customer's refunds over the three years", "=SUMIFS(Refunds[Amount],Refunds[CustomerID],B22)", MONEY,
             r2(sum(x["amt"] for x in f.rf.values() if x["cust"] == L["rf"]["cust"]))),
            ("Score on the five refund flags (RefundFlags)",
             "=XLOOKUP(B5,RefundFlags[RefundNumber],RefundFlags[Score])", COUNT, L["score"])]
    for i, (label, formula, nf, exp) in enumerate(rows):
        r = 4 + i
        put(ws, {f"A{r}": label, f"B{r}": formula})
        if nf:
            fmt(ws, f"B{r}", nf)
        ws.Range(f"B{r}").HorizontalAlignment = -4131
        if exp is None:
            continue
        if nf == DATE:
            check_date(b, t, f"largest refund: {label.lower()}", exp, f"Timeline!B{r}")
        elif isinstance(exp, str):
            b.check(t, f"largest refund: {label.lower()}", exp, f"=Timeline!B{r}")
        else:
            b.check(t, f"largest refund: {label.lower()}", exp, f"=Timeline!B{r}", 0.005 if nf == MONEY else 0,
                    nf or COUNT)
    flag_rows = {"Above the approver's limit": L["rf"]["amt"] > f.emp[L["rf"]["appr"]]["limit"],
                 "The largest credit of the three years": L["largest_credit"],
                 "Credit approver applied cash to the invoice": L["cm"]["id"] in {m["id"] for m in f.tests["cash_credit"]},
                 "Refund dated before the last payment on the invoice": L["rf"]["id"] in {x["id"] for x in
                                                                                          f.tests["before"]}}
    for i, (label, *_x) in enumerate(rows):
        if label in flag_rows:
            b.check(t, f"largest refund: {label.lower()} (1 = TRUE)", int(bool(flag_rows[label])),
                    f"=--Timeline!B{4 + i}", 0, COUNT)
    r = 4 + len(rows)
    put(ws, {f"A{r}": "Unpaid on the invoice on the refund date"})
    paste(ws, r, 2, [[r2(L["unpaid_refund"])]], "the balance of the credited invoice on the refund date (GrandTotal less "
                                                "the applications dated by then)", {0: MONEY})
    b.found["unpaid"] = f"Timeline!B{r}"
    r += 2
    heading(ws, r, "Timeline, from the shipment to the last receipt on the invoice")
    r += 1
    header(ws, r, 1, ["Date", "Step", "Document", "What the records show", "Who did it"])
    r += 1
    t0 = r
    paste(ws, r, 1, [[serial(d), step, doc, detail, who] for d, _, step, doc, detail, who in L["steps"]],
          "timeline of the largest refund (the shipment, invoice, receipts and applications, return, credit, "
          "clawbacks, and refund on its invoice, in date order, with who recorded or approved each)", {0: DATE})
    r += len(L["steps"])
    ws.Range(f"D{t0}:E{r}").WrapText = True
    ws.Range(f"A{t0}:E{r}").VerticalAlignment = -4160
    rf, m, inv = L["rf"], L["cm"], L["inv"]
    appliers = {a[2] for a in f.apps[inv["id"]]}
    r = text_block(ws, r + 1, f"{MA}: disposition and the evidence that would settle it", [
        f"Disposition: follow up (Chapter 8), not a conclusion. {rf['num']}, {money(rf['amt'])}, the largest refund of "
        f"the three years, was paid by {rf['method'].lower()} on a {L['weekday']} to customer {rf['cust']}, who paid "
        f"this invoice only by {series(x.lower() for x in L['methods'])}; it was approved by the {f.title(rf['appr'])} "
        f"within the {money(f.emp[rf['appr']]['limit'])} limit. It refunded {m['num']}, the largest credit of the three "
        f"years, approved by a {f.title(m['appr'])} with a limit of {money(f.emp[m['appr']]['limit'])} and booked "
        f"entirely to 2060 while {money(L['unpaid_credit'])} of {inv['num']} was unpaid; the refund was paid while "
        f"{money(L['unpaid_refund'])} was still unpaid, and the invoice was settled on {L['settled'][:10]} by checks"
        + (", one of them applied by the credit's approver" if m["appr"] in appliers else "") + ". Every step is in "
        "the records and balances, but the pattern (a credit above authority, a refund before payment, by a method "
        "the customer did not use, on a weekend) is the trace a diverted refund would leave, so it is reported as "
        "what the records show.",
        "Evidence outside the database: the wire confirmation's beneficiary and account against the customer's known "
        "bank details; a confirmation from the customer of the credit and the refund received; the warehouse's "
        "receiving and inspection record of the damaged goods and any carrier claim; the customer's written request "
        "for the refund; and an explanation of why the refund went by wire to a customer who paid by check, and why "
        "before its checks arrived."], span=5)

    # restocking by reason
    heading(ws, r, "What returned goods were put back into inventory at, by reason (standard cost, live)")
    r += 1
    header(ws, r, 1, ["Reason", str(f.years[0]), str(f.years[1]), str(f.years[2]), "Total", "Return lines"])
    hdr = r
    for j, y in enumerate(f.years):
        ws.Cells(r, 2 + j).Value = y
    r += 1
    rs0 = r
    reasons = sorted({s["reason"] for s in f.sr.values()})
    for reason in reasons:
        put(ws, {f"A{r}": reason, f"E{r}": f"=SUM(B{r}:D{r})",
                 f"F{r}": f'=COUNTIF(ReturnLines[ReasonCode],A{r})'})
        for j, (c, y) in enumerate(zip("BCD", f.years)):
            put(ws, {f"{c}{r}": f"=SUMIFS(ReturnLines[ExtendedStandardCost],ReturnLines[ReasonCode],$A{r},"
                                f"ReturnLines[FiscalYear],{c}${hdr})"})
            b.check(t, f"restocked at standard, {reason}, {y}", r2(f.restock.get((reason, y), 0.0)),
                    f"=Timeline!{c}{r}")
        b.check(t, f"restocked at standard, {reason}, total", r2(sum(f.restock.get((reason, y), 0.0) for y in f.years)),
                f"=Timeline!E{r}")
        r += 1
    put(ws, {f"A{r}": "Total"})
    for c in "BCDEF":
        put(ws, {f"{c}{r}": f"=SUM({c}{rs0}:{c}{r - 1})"})
    bold(ws, f"A{r}:F{r}")
    r += 1
    dq = ("Damaged", "Quality Concern")
    put(ws, {f"A{r}": "Damaged and Quality Concern"})
    for c in "BCDE":
        put(ws, {f"{c}{r}": f'=SUMIFS({c}{rs0}:{c}{r - 2},$A{rs0}:$A{r - 2},"Damaged")+SUMIFS({c}{rs0}:{c}{r - 2},'
                            f'$A{rs0}:$A{r - 2},"Quality Concern")'})
    for c, y in zip("BCD", f.years):
        b.check(t, f"restocked at standard, Damaged and Quality Concern, {y}",
                r2(sum(f.restock.get((x, y), 0.0) for x in dq)), f"=Timeline!{c}{r}")
    b.check(t, "restocked at standard, Damaged and Quality Concern, total",
            r2(sum(f.restock.get((x, y), 0.0) for x in dq for y in f.years)), f"=Timeline!E{r}")
    bold(ws, f"A{r}:E{r}")
    b.found["restock"] = dict(dmg_row=rs0 + reasons.index("Damaged"), dq_row=r)
    fmt(ws, f"B{rs0}:E{r}", MONEY)
    fmt(ws, f"F{rs0}:F{r}", COUNT)
    r += 1
    fr = f.fractional
    put(ws, {f"A{r}": "Return lines restocked below standard (less than one unit)", f"A{r + 1}": "Below standard by",
             f"A{r + 2}": "... of which Damaged and Quality Concern"})
    paste(ws, r, 2, [[fr["n"]], [fr["gap"]], [fr["gap_dq"]]], "return lines whose ExtendedStandardCost is not the "
          "quantity times the item's standard cost (lines of less than one unit, costed at the quantity times the "
          "shipment line's extended cost)", {0: "#,##0.00"})
    fmt(ws, f"B{r}", COUNT)
    r += 4

    # substantive and lapping results (Credits.sql)
    sb = f.substantive
    heading(ws, r, "Substantive and lapping tests (Credits.sql)")
    r += 1
    header(ws, r, 1, ["Test", "Result", "", "Conclusion"])
    r += 1
    results = [
        ("Credit lines traced to their return, shipment, and invoice lines", f"{sb['traced']} of {sb['lines']}",
         "Clean"),
        ("Credit lines for more than was shipped; shipment lines returned twice", f"{sb['over']}; {sb['twice']}", "Clean"),
        ("Credit lines whose price or discount differs from the invoice line's", f"{sb['price_off']}", "Clean"),
        ("Credit lines whose LineTotal is not ROUND(Q x P x (1 - D), 2) (SQLite)",
         f"{len(sb['total_off'])} (credit line {', '.join(map(str, sb['total_off']))})",
         "A half-cent rounding, not an error"),
        ("Credits per invoice; credits above their invoice's total", f"{sb['distinct_inv']} credits on "
         f"{sb['distinct_inv']} invoices; {sb['above_invoice']}", "Clean"),
        (f"Tax at {sb['rate']:.1%} of SubTotal plus freight", f"{sb['tax_ok']} of {len(f.cm)} (a test on SubTotal alone "
         f"falsely flags the {sb['with_freight']} credits with freight)", "Clean"),
        ("Receipts applied to another customer's invoices", f"{sb['other']}", "Clean"),
        ("Days from receipt to deposit", f"{sb['dep_lo']} to {sb['dep_hi']}", "Clean"),
        ("Days from the later of receipt and invoice date to application", f"{sb['lag_lo']} to {sb['lag_hi']}",
         "Clean"),
        ("Receipts not fully applied", f"{sb['not_full']}", "Clean"),
        ("Receipts applied to invoices dated after the receipt", f"{sb['early_receipts']} receipts "
         f"({sb['early_apps']} applications, {money(sb['early_amount'])})", "Deposits held in 2060, not lapping"),
    ]
    paste(ws, r, 1, [[a, b_, "", c] for a, b_, c in results],
          "substantive tests of the credits and lapping tests of the receipts (recomputation, tracing, and timing)")
    ws.Range(f"A{r}:D{r + len(results)}").WrapText = True
    r += len(results) + 1
    text_block(ws, r, MA, [
        "Restocking. Returned goods go back to inventory at standard cost whatever their reason, so goods returned "
        f"Damaged were restocked at {money(sum(f.restock.get(('Damaged', y), 0.0) for y in f.years))} over three "
        f"years ({money(f.restock.get(('Damaged', f.C), 0.0))} in fiscal {f.C}), and with Quality Concern "
        f"{money(sum(f.restock.get((x, f.C), 0.0) for x in dq))} in fiscal {f.C}; no write-down account exists. "
        "This is a valuation question for the inventory at the year-end (lower of cost and net realizable value), "
        "below performance materiality but worth an inspection step.",
        "First digits. A first-digit test does not suit these populations, by Chapter 8's criteria: "
        f"{len(f.cm)} credits and {len(f.rf)} refunds are too few for the test to have power, and their amounts are "
        "not naturally occurring: each is a price times a quantity plus tax, set by the invoice it reverses, so "
        "their digits follow the price list rather than Benford's law. The tests that fit are the recomputation of "
        "each credit and the comparison of each refund with its credit and payments."], span=5)


# --- Requirement 8: the evaluation of deficiencies -------------------------------------------------------------------

def r8(b: ExerciseBuild) -> None:
    f = facts(b)
    t = "Requirement 8"
    tt = f.tests
    m = f.materiality
    T = b.found["tests"]
    ws = new_sheet(b, "Deficiencies")
    widths(ws, {"A": 7, "B": 34, "C": 9, "D": 14, "E": 11, "F": 11, "G": 14, "H": 14, "I": 26, "J": 30, "K": 44,
                "L": 13, "M": 20, "N": 24})
    title(ws, "Requirement 8: Evaluating the deficiencies",
          f"Exposure against the materiality cells of Requirement 3; frequencies and exposures are live (Tests sheet "
          f"and the query Tables). Exposure is the amount of the documents that failed the control.")
    put(ws, {"A3": "Materiality", "D3": "=Materiality", "A4": "Performance materiality", "D4": "=PerformanceMateriality",
             "A5": "Clearly trivial", "D5": "=ClearlyTrivial"})
    fmt(ws, "D3:D5", MONEY)
    bold(ws, "A3:A5")
    cy = f.C
    against = ('=IF(H{r}>=Materiality,"At or above materiality",IF(H{r}>=PerformanceMateriality,"Above performance '
               'materiality, below materiality",IF(H{r}>=ClearlyTrivial,"Above clearly trivial, below performance '
               'materiality","Clearly trivial")))')

    def tref(tid):
        r = T[tid]
        return [f"=Tests!H{r}", f"=Tests!G{r}", f"=Tests!I{r}", f"=Tests!J{r}"]
    am = AM
    rows = [
        ["D1", "Credits approved above the approver's authority", "C2", "Design", *tref("T1"), against,
         "Reasonably possible: the system accepts any approver, and representatives with a limit of $0 approved "
         f"{pct(len(tt['cm_above']) / len(f.cm), 0)} of the credits.",
         "Every credit traces to a return received in the warehouse, at invoice prices and quantities (Requirement 7); "
         "the manager's limit is never exceeded. These limit what a credit can be for, not who grants it.",
         "D2", "Significant deficiency (combined with D2)", "Control deficiency: report"],
        ["D2", "Customer service records receipts, applies cash, and approves credits and clawbacks (approver applied "
               "cash to the credited invoice)", "C4", "Design", *tref("T2"), against,
         "Reasonably possible: one department can take a payment and close the invoice with a credit.",
         "The warehouse receipt behind every credit; refunds are approved outside customer service (in "
         "Administration); no lapping or false-credit trace (Requirement 7).", "D1",
         "Significant deficiency (combined with D1)", "Control deficiency: report"],
        ["D3", "Refunds approved above the approver's authority", "C6", "Design", *tref("T7"), against,
         "Reasonably possible: Staff Accountants and Administrative Specialists with a limit of $0 approve refunds.",
         "Each refund equals its credit's 2060 part; the credits are clean. No control over the payee.", "D4, D6",
         "Significant deficiency (combined with D4 and D6)", "Control deficiency: report"],
        ["D4", "Refunds dated before the customer's payment on the credited invoice", "C7", "Design", *tref("T9"),
         against, "Reasonably possible: credits on unpaid invoices go to 2060, and the refund step does not check "
                  "payment.", f"None found: the payments arrived {min(tt['wait'])} to {max(tt['wait'])} days later, which no control "
         "required.",
         "D3, D6", "Significant deficiency (combined with D3 and D6)", "Control deficiency: report"],
        ["D5", "No offset of past-due balances before a refund (refunds to customers past due by at least the refund)",
         "C8", "Design (no policy)", *tref("T12"), against,
         "Not a misstatement in itself: the receivable remains collectible.", "Collection of the past-due balances "
                                                                               "afterwards.", "D3",
         "Follow up; a policy recommendation, not a deficiency until a policy exists", "Follow up"],
        ["D5", "Refund method unlike every receipt on the credited invoice", "C8", "Design (no policy)", *tref("T13"),
         against, "An anomaly: a method chosen at random would mismatch about as often.",
         "None in the records: no payee or account to verify.", "D3",
         "Follow up; a policy recommendation, not a deficiency until a policy exists", "Follow up"],
        ["D6", "No preparer recorded on credits or refunds (all refunds)", "C2, C6", "Design", "=ROWS(Refunds)",
         f"=COUNTIFS(Refunds[FiscalYear],{cy})", "=SUM(Refunds[Amount])",
         f"=SUMIFS(Refunds[Amount],Refunds[FiscalYear],{cy})", against,
         "The approver cannot be shown to differ from the preparer, so separation cannot be evidenced at all.",
         "None in the records.", "D3, D4", "Significant deficiency (combined with D3 and D4)",
         "Control deficiency: report"],
        ["D7", f"The {am}'s concentration: commission rates, accruals, and payments; refunds within limit, "
               "including the largest; all payroll registers (Chapters 12 and 16)", "C5, C6", "Design",
         f'=COUNTIF(Refunds[ApproverTitle],"{am}")', f'=COUNTIFS(Refunds[ApproverTitle],"{am}",Refunds[FiscalYear],{cy})',
         f'=SUMIFS(Refunds[Amount],Refunds[ApproverTitle],"{am}")',
         f'=SUMIFS(Refunds[Amount],Refunds[ApproverTitle],"{am}",Refunds[FiscalYear],{cy})', against,
         "Reasonably possible in this cycle, though no exception was found in the clawbacks.",
         "The clawbacks are complete and accurate (Requirement 4).", "Entity-wide: payroll approvals",
         "Deficiency (may combine entity-wide into a significant deficiency)", "Control deficiency: report to management"],
        ["D8", "Damaged goods restocked at full standard cost (Damaged returns)", "C1", "Design",
         '=COUNTIF(ReturnLines[ReasonCode],"Damaged")', f'=COUNTIFS(ReturnLines[ReasonCode],"Damaged",'
                                                         f'ReturnLines[FiscalYear],{cy})',
         '=SUMIFS(ReturnLines[ExtendedStandardCost],ReturnLines[ReasonCode],"Damaged")',
         f'=SUMIFS(ReturnLines[ExtendedStandardCost],ReturnLines[ReasonCode],"Damaged",ReturnLines[FiscalYear],{cy})',
         against, "Possible overstatement of inventory by part of the restocked cost.", "None: no write-down account.",
         "", "Valuation follow-up", "Follow up"],
    ]
    names = ["ID", "Pattern", "Control point", "Design or operation", "Frequency, three years", f"Frequency, {cy}",
             "Exposure, three years", f"Exposure, {cy}", f"{cy} exposure against materiality", "Likelihood of a "
             "misstatement", "Compensating controls and the evidence they operate", "Combines with", "Classification",
             "Disposition (Chapter 8)"]
    r0 = 7
    for i, row in enumerate(rows):
        row[8] = row[8].format(r=r0 + 1 + i)
    end = text_table(ws, r0, 1, names, rows)
    fmt(ws, f"E{r0 + 1}:F{r0 + len(rows)}", COUNT)
    fmt(ws, f"G{r0 + 1}:H{r0 + len(rows)}", MONEY)
    stat = lambda items, key: f.stat(items, key)  # noqa: E731
    exp_rows = {0: (stat(tt["cm_above"], "gt"), "D1"), 1: (stat(tt["cash_credit"], "gt"), "D2"),
                2: (stat(tt["rf_above"], "amt"), "D3"), 3: (stat(tt["before"], "amt"), "D4"),
                4: (stat(tt["pd2"], "amt"), "D5 offset"), 5: (stat(tt["mism"], "amt"), "D5 method"),
                6: (stat(list(f.rf.values()), "amt"), "D6"),
                7: (stat([x for x in f.rf.values() if f.title(x["appr"]) == AM], "amt"), "D7")}

    def band(x):
        return ("At or above materiality" if x >= m["mat"] else "Above performance materiality, below materiality"
                if x >= m["perf"] else "Above clearly trivial, below performance materiality" if x >= m["trivial"]
                else "Clearly trivial")
    for i, (st, label) in exp_rows.items():
        r = r0 + 1 + i
        b.check(t, f"{label}: frequency, three years", st["n"], f"=Deficiencies!E{r}", 0, COUNT)
        b.check(t, f"{label}: frequency, {cy}", st["cur"], f"=Deficiencies!F{r}", 0, COUNT)
        b.check(t, f"{label}: exposure, three years", st["amt"], f"=Deficiencies!G{r}")
        b.check(t, f"{label}: exposure, {cy}", st["cur_amt"], f"=Deficiencies!H{r}")
        b.check(t, f"{label}: against materiality", band(st["cur_amt"]), f"=Deficiencies!I{r}")
    dmg = [l for l in f.srl if f.sr[l["ret"]]["reason"] == "Damaged"]
    dmg_c = [l for l in dmg if year_of(f.sr[l["ret"]]["date"]) == cy]
    r = r0 + 9
    b.check(t, "D8: Damaged return lines", len(dmg), f"=Deficiencies!E{r}", 0, COUNT)
    b.check(t, f"D8: Damaged return lines, {cy}", len(dmg_c), f"=Deficiencies!F{r}", 0, COUNT)
    b.check(t, "D8: restocked at standard", r2(sum(l["std"] for l in dmg)), f"=Deficiencies!G{r}")
    b.check(t, f"D8: restocked at standard, {cy}", r2(sum(l["std"] for l in dmg_c)), f"=Deficiencies!H{r}")

    # combined
    r = end
    heading(ws, r, "Combined evaluation (deficiencies that affect the same account or assertion combine)")
    r += 1
    credits_c = ("=SUMPRODUCT((Credits[FiscalYear]={y})*((Credits[AboveLimit]+Credits[CashAndCredit])>0)*"
                 "Credits[GrandTotal])").format(y=cy)
    refunds_c = ("=SUMPRODUCT((Refunds[FiscalYear]={y})*((Refunds[AboveLimit]+Refunds[BeforePayment])>0)*"
                 "Refunds[Amount])").format(y=cy)
    pot = ('=IF({c}{r}>=Materiality,"At or above materiality",IF({c}{r}>=PerformanceMateriality,"Above performance '
           'materiality, below materiality",IF({c}{r}>=ClearlyTrivial,"Above clearly trivial, below performance '
           'materiality","Clearly trivial")))')
    comb = [
        ["G1", "D1, D2", "Credit memos and receivables: occurrence of credits, completeness of cash", credits_c,
         f"=SUMIFS(Credits[GrandTotal],Credits[FiscalYear],{cy})", pot,
         "Every credit rests on a warehouse receipt at invoice prices; no lapping or false-credit trace.",
         "Significant deficiency",
         "Any credit could be granted without authority by the department that handles the cash, and the year's "
         "credits exceed materiality; not a material weakness, because a material misstatement would need a "
         "falsified warehouse record, and none of the traces appears."],
        ["G2", "D3, D4, D6", "Customer refunds and 2060: occurrence of disbursements", refunds_c,
         f"=SUMIFS(Refunds[Amount],Refunds[FiscalYear],{cy})", pot, "Refund equals the credit's 2060 part; clean "
                                                                     "credits.",
         "Significant deficiency", "Cash leaves on a record that no one with authority approved, before the customer "
                                   "has paid, with no preparer recorded: a fraud risk factor, although the magnitude is "
                                   "well below materiality."],
        ["G3", "D7", "Commissions, refunds, and payroll: segregation of duties",
         f'=SUMIFS(Refunds[Amount],Refunds[ApproverTitle],"{am}",Refunds[FiscalYear],{cy})',
         f"=SUMIFS(Refunds[Amount],Refunds[FiscalYear],{cy})", pot, "Clawbacks complete and accurate.", "Deficiency",
         "No exception found in this cycle, but one person sets, accrues, and pays commissions and approves refunds "
         "and payroll; it may combine entity-wide."],
        ["G4", "D5", "Refunds: offset and payee", f"=Tests!J{T['T13']}",
         f"=SUMIFS(Refunds[Amount],Refunds[FiscalYear],{cy})", pot, "None in the records.",
         "Follow up (not a deficiency until a policy exists)", "No policy requires an offset or the original payment "
                                                               "instrument; recommend one."],
        ["G5", "D8", "Inventory: valuation of returned goods",
         f'=SUMIFS(ReturnLines[ExtendedStandardCost],ReturnLines[ReasonCode],"Damaged",ReturnLines[FiscalYear],{cy})'
         f'+SUMIFS(ReturnLines[ExtendedStandardCost],ReturnLines[ReasonCode],"Quality Concern",ReturnLines[FiscalYear],'
         f'{cy})', f"=SUMIFS(ReturnLines[ExtendedStandardCost],ReturnLines[FiscalYear],{cy})", pot, "None.",
         "Valuation follow-up", "Damaged and Quality Concern returns restocked at full standard cost; inspect and write "
                                "down."],
    ]
    c0 = r + 1
    for i, row in enumerate(comb):
        row[5] = row[5].format(c="E", r=c0 + i)
        row[1], row[2] = row[2], row[1]
    r = merged_table(ws, r, [1, 1, 1, 1, 2, 2, 1, 1, 1],
                     ["Group", "Accounts and assertions", "Deficiencies", f"Exposure, {cy}",
                      f"Potential magnitude, {cy} (all such documents)", "Potential against materiality",
                      "Compensating controls", "Classification", "Why"], comb)
    fmt(ws, f"D{c0}:E{c0 + len(comb) - 1}", MONEY)
    cls = f"J{c0}:J{c0 + len(comb) - 1}"
    put(ws, {f"A{r}": "Significant deficiencies", f"D{r}": f'=COUNTIF({cls},"Significant deficiency")',
             f"A{r + 1}": "Material weaknesses", f"D{r + 1}": f'=COUNTIF({cls},"Material weakness")',
             f"A{r + 2}": "Overall", f"D{r + 2}": f'=IF(D{r + 1}=0,"No material weakness","Material weakness")'})
    bold(ws, f"A{r}:D{r + 2}")
    b.found["deficiencies"] = dict(sd=f"Deficiencies!D{r}", mw=f"Deficiencies!D{r + 1}",
                                   overall=f"Deficiencies!D{r + 2}", g3=f"Deficiencies!J{c0 + 2}")
    cr_c = [x for x in f.cm.values() if year_of(x["date"]) == cy]
    g1 = r2(sum(x["gt"] for x in cr_c if x["id"] in {y["id"] for y in tt["cm_above"]} |
                {y["id"] for y in tt["cash_credit"]}))
    rf_c = [x for x in f.rf.values() if year_of(x["date"]) == cy]
    g2 = r2(sum(x["amt"] for x in rf_c if x["id"] in {y["id"] for y in tt["rf_above"]} | {y["id"] for y in tt["before"]}))
    b.check(t, f"G1 credits failing D1 or D2, {cy}", g1, f"=Deficiencies!D{c0}")
    b.check(t, f"G1 all credits, {cy}", r2(sum(x["gt"] for x in cr_c)), f"=Deficiencies!E{c0}")
    b.check(t, "G1 potential against materiality", band(sum(x["gt"] for x in cr_c)), f"=Deficiencies!G{c0}")
    b.check(t, f"G2 refunds failing D3 or D4, {cy}", g2, f"=Deficiencies!D{c0 + 1}")
    b.check(t, f"G2 all refunds, {cy}", r2(sum(x["amt"] for x in rf_c)), f"=Deficiencies!E{c0 + 1}")
    b.check(t, "G2 potential against materiality", band(sum(x["amt"] for x in rf_c)), f"=Deficiencies!G{c0 + 1}")
    dq = sum(f.restock.get((x, cy), 0.0) for x in ("Damaged", "Quality Concern"))
    b.check(t, f"G5 Damaged and Quality Concern restocked, {cy}", r2(dq), f"=Deficiencies!D{c0 + 4}")
    b.check(t, "significant deficiencies", 2, f"=Deficiencies!D{r}", 0, COUNT)
    b.check(t, "material weaknesses", 0, f"=Deficiencies!D{r + 1}", 0, COUNT)
    r += 4

    # clean results
    heading(ws, r, "Clean results, reported with the same care")
    r += 1
    last = b.found.get("recon_last", 120)
    clean = [
        ["Populations reconcile to the ledger (every difference on the Reconciliation sheet)",
         f'=SUMPRODUCT((LEFT(Reconciliation!A5:A{last},10)="Difference")*IFERROR(ABS(Reconciliation!C5:E{last}),0))',
         "Sum of the absolute differences: zero to the cent"],
        ["Clawbacks complete, at the line total and the accrual's rate, correctly rounded, on the credit's date",
         "=" + "+".join(f"Tests!H{T[k]}" for k in ("T16", "T17", "T18", "T19", "T20")), "Exceptions: none"],
        ["Approvers within their employment dates", f"=Tests!H{T['T6']}", "Exceptions: none"],
        ["Refund approver different from the credit approver", f"=Tests!H{T['T8']}", "Exceptions: none"],
        ["Returns received in the warehouse, by someone other than the credit's approver", f"=Tests!H{T['T5']}",
         "Exceptions: none"],
        ["One refund per refunded credit", f"=Tests!H{T['T14']}+Tests!H{T['T15']}", "Exceptions: none"],
        ["Credits recomputed from their return, shipment, and invoice lines", "Clean (Timeline, Credits.sql)",
         "Quantities, prices, tax, and freight all agree"],
        ["Lapping: receipts, deposits, and applications", "Clean (Timeline, Credits.sql)", "No trace of lapping"],
    ]
    k0 = r + 1
    r = merged_table(ws, r, [1, 1, 2, 5], ["", "Test", "Result", "Conclusion"], [[""] + x for x in clean])
    for i in range(6):
        fmt(ws, f"C{k0 + i}", "#,##0.00" if i == 0 else COUNT)
        b.check(t, f"clean result: {clean[i][0][:60].lower()}", 0.0 if i == 0 else 0, f"=Deficiencies!C{k0 + i}",
                0.005 if i == 0 else 0, "#,##0.00" if i == 0 else COUNT)
    st1, st3, st4 = stat(tt["cm_above"], "gt"), stat(tt["rf_above"], "amt"), stat(tt["before"], "amt")
    all_c = r2(sum(x["gt"] for x in cr_c))
    text_block(ws, r, MA, [
        f"D1 and D2 combine into a significant deficiency over credits and receivables. D1's fiscal {cy} exposure, "
        f"{money(st1['cur_amt'])} ({st1['cur']} credits), is above performance materiality "
        f"({money(m['perf'])}) and below materiality ({money(m['mat'])}), and all {cy} credits, "
        f"{money(all_c)}, exceed materiality, because any credit could have been approved without authority. D2 "
        "(customer service records receipts, applies cash, approves credits, and approves clawbacks) is a design "
        "deficiency, mitigated but not removed by every credit tracing to a return received in the warehouse at "
        "invoice prices, by refunds approved outside customer service, and by the absence of any lapping or "
        "false-credit trace. It is not a material weakness: a material misstatement through credits would need a "
        "falsified warehouse record, and none of the traces appears. A student who argues material weakness from "
        "gross exposure must address that compensating link and the likelihood test.",
        f"D3, D4, and D6 combine into a significant deficiency over refunds: {st3['n']} refunds above authority "
        f"({st3['cur']} in {cy}, {money(st3['cur_amt'])}), {st4['n']} paid before the customer's payment arrived "
        f"({st4['cur']} in {cy}, {money(st4['cur_amt'])}), and no preparer recorded. The magnitude is well below "
        "materiality, but cash leaves on the strength of a record, which makes it a fraud risk factor worth the "
        "committee's attention. D5 (no offset; refund method) is a follow-up and a policy recommendation, not a "
        f"deficiency until a policy exists. D7, the {AM}'s concentration (all {f.commission['n_rates']} commission "
        f"rates, all {f.commission['n_accruals']:,} accruals, all {f.commission['n_payments']} commission payments, "
        f"the largest refund, and all {f.payroll_approvals['registers']:,} payroll registers of Chapters 12 and 16), is "
        "a deficiency in this cycle that may combine entity-wide into a significant deficiency. D8, damaged goods "
        "restocked at full cost, is a valuation follow-up. There is no material weakness.",
        "Clean: the reconciliations, the clawbacks, the employment dates, the separation of refund and credit "
        "approvers, one refund per credit, the substantive tests of every credit, and the lapping tests."], span=11)


# --- Requirement 9: the report to the audit committee ----------------------------------------------------------------

def r9(b: ExerciseBuild) -> None:
    f = facts(b)
    t = "Requirement 9"
    tt = f.tests
    m = f.materiality
    L = f.largest
    T = b.found["tests"]
    ws = new_sheet(b, "Report")
    widths(ws, {"A": 26, "B": 30, "C": 30, "D": 30, "E": 30, "F": 30, "G": 22})
    title(ws, "Requirement 9: Report to the audit committee (model answer)",
          "At most three pages, with an appendix of exhibits: the Cycle Map, Reconciliation, Tests, Sample, "
          "Deficiencies, and the action plans below.")
    st = lambda items, key="amt": f.stat(items, key)  # noqa: E731
    c1, c2, r3_, r4_ = st(tt["cm_above"], "gt"), st(tt["cash_credit"], "gt"), st(tt["rf_above"]), st(tt["before"])
    pd2, mism = st(tt["pd2"]), st(tt["mism"])
    rec_total = r2(sum(x["amt"] for x in f.rcpt.values()))
    heading(ws, 4, "Key figures (live)")
    keys = [("Credits approved above the approver's limit", f"=Tests!H{T['T1']}", c1["n"]),
            ("Credits whose approver applied cash to the credited invoice", f"=Tests!H{T['T2']}", c2["n"]),
            ("Refunds approved above the approver's limit", f"=Tests!H{T['T7']}", r3_["n"]),
            ("Refunds dated before the customer's payment", f"=Tests!H{T['T9']}", r4_["n"]),
            ("Significant deficiencies", "=" + b.found["deficiencies"]["sd"], 2),
            ("Overall", "=" + b.found["deficiencies"]["overall"], "No material weakness")]
    for i, (label, formula, exp) in enumerate(keys):
        r = 5 + i
        put(ws, {f"A{r}": label, f"D{r}": formula})
        if isinstance(exp, str):
            b.check(t, f"report: {label.lower()}", exp, f"=Report!D{r}")
        else:
            fmt(ws, f"D{r}", COUNT)
            b.check(t, f"report: {label.lower()}", exp, f"=Report!D{r}", 0, COUNT)
    r = text_block(ws, 12, "Executive summary and overall conclusion", [
        f"To the audit committee, November {f.C + 1} meeting. Internal audit tested the customer credits cycle (sales "
        f"returns, credit memos, customer refunds, commission clawbacks, and cash application) over fiscal {f.F} to "
        f"{f.C}, and states its conclusions on controls as at the end of fiscal {f.C}.",
        "Overall conclusion. The records reconcile, and the balances we tested are right: every population agrees "
        "with the ledger to the cent in every year, every credit recomputes from its return, shipment, and invoice, "
        "and we found no trace of lapping or of a credit covering stolen cash. The controls over who may grant credits "
        f"and refunds, however, are not designed to prevent an unauthorized one: {c1['n']} credits "
        f"({money(c1['amt'])}) and {r3_['n']} refunds ({money(r3_['amt'])}) were approved by employees whose approval "
        f"limit is $0, and {r4_['n']} refunds ({money(r4_['amt'])}) were dated before the customer's payment on the "
        "credited invoice had arrived. We rate two significant deficiencies, one over credits and one over refunds, "
        "and one deficiency in the concentration of duties with the Accounting Manager. There is no material "
        "weakness. One refund, the largest, is under follow-up.",
        f"Scope and populations. {len(f.sr)} returns, {len(f.cm)} credit memos ({money(sum(x['gt'] for x in f.cm.values()))}), "
        f"{len(f.rf)} refunds ({money(sum(x['amt'] for x in f.rf.values()))}), {len(f.adj)} clawbacks "
        f"({money(sum(a['amt'] for a in f.adj))}), and {len(f.rcpt):,} receipts ({money(rec_total)}) with "
        f"{len(f.all_apps):,} applications, all tested in full. Each population reconciles to its ledger accounts by "
        "year with no difference (appendix: Reconciliation). Magnitude is judged against materiality of "
        f"{money(m['mat'])}, 5% of fiscal {f.C} income before income taxes as the ledger records it. Sampling was "
        "used only for what the records cannot show (the customer's request, an independent payee check, and the "
        "inspection of damaged goods); the plan and the frozen selection are in the appendix, and the documents have "
        "been requested."], span=7)
    heading(ws, r, "Findings")
    r += 1
    findings = [
        ["F1. Credits approved without authority, in the department that handles the customer's cash (D1, D2)",
         f"{c1['n']} credits ({money(c1['amt'])}; {c1['cur']} in fiscal {f.C}, {money(c1['cur_amt'])}) were approved by "
         "customer service representatives whose approval limit is $0. On "
         f"{c2['n']} credits the approver had also applied cash to the credited invoice.",
         "Credits are approved within delegated authority, by someone who does not handle the customer's cash (C2, C4).",
         "No delegation of authority for credits exists in the records, and the system accepts any approver; customer "
         "service records receipts, applies cash, and approves credits and clawbacks.",
         f"A credit could be granted, or cash concealed, without independent approval. Fiscal {f.C} credits above "
         f"authority ({money(c1['cur_amt'])}) exceed performance materiality; every credit traces to a return "
         "received in the warehouse at invoice prices.", "Significant deficiency",
         "Approve a delegation of authority for credits and enforce it in the system; have credits approved by "
         "someone who does not record or apply the customer's cash."],
        ["F2. Refunds approved without authority and paid before the customer's payment, with no preparer recorded "
         "(D3, D4, D6)",
         f"{r3_['n']} refunds ({money(r3_['amt'])}) were approved above the approver's limit by Staff Accountants and "
         f"Administrative Specialists (limit $0). {r4_['n']} refunds ({money(r4_['amt'])}; {r4_['cur']} in fiscal "
         f"{f.C}) were dated before the last payment on the credited invoice, {len(tt['nothing'])} before any "
         "payment. Neither a credit nor a refund records who prepared it.",
         "Refunds are approved within authority, outside customer service, and only of credit balances the customer "
         "has paid (C6, C7).",
         "Credits on unpaid invoices are booked to customer deposits (2060), and the refund step pays out 2060 without "
         "checking that the customer's payment has arrived; no delegation of authority for refunds.",
         f"Cash could leave for balances not yet paid for, or go to the wrong payee. The magnitude is below "
         f"materiality (fiscal {f.C} refunds {money(st([x for x in f.rf.values() if year_of(x['date']) == f.C])['amt'])}), "
         "but cash leaving on a record is a fraud risk factor.", "Significant deficiency",
         "Book credits on unpaid invoices against the receivable; release refunds only after the payment has cleared; "
         "record a preparer separate from the approver; approve a delegation of authority for refunds."],
        ["F3. Concentration of duties with the Accounting Manager (D7)",
         f"The Accounting Manager approved all {f.commission['n_rates']} commission rates (which ended on "
         f"{f.commission['rate_ends'][-1]}), created all {f.commission['n_accruals']:,} commission accruals, approved "
         f"all {f.commission['n_payments']} commission payments and {sum(1 for x in f.rf.values() if f.title(x['appr']) == AM)} "
         f"refunds (the largest among them), and approved all {f.payroll_approvals['registers']:,} payroll registers "
         "(Chapters 12 and 16).", "Incompatible duties are separated, or reviewed independently.",
         "A small accounting team with no independent review of commissions and refunds.",
         "An error or a fraud in commissions or refunds could go undetected; no exception was found in the "
         "clawbacks.", "Deficiency (may combine entity-wide)",
         "Have someone independent approve commission rates and payments; approve the 2027 rates."],
        ["F4. No offset of past-due balances, and refunds by another method (D5)",
         f"{pd2['n']} refunds went to customers past due by at least the refund on the refund date; {mism['n']} refunds "
         "went by a method that none of the receipts on the credited invoice used.",
         "No policy exists; good practice pays refunds to the original instrument or a verified account, net of open "
         "balances.", "No refund policy.", "An anomaly, not a misstatement: a diverted refund would look like this.",
         "Follow up", "Adopt a refund policy: original instrument or verified account, open balances offset first."],
        ["F5. Damaged goods restocked at full cost (D8)",
         f"Damaged returns were restocked at standard cost ({money(sum(f.restock.get(('Damaged', y), 0.0) for y in f.years))}"
         f" over three years; with Quality Concern {money(sum(f.restock.get((x, f.C), 0.0) for x in ('Damaged', 'Quality Concern')))}"
         f" in fiscal {f.C}).", "Inventory at the lower of cost and net realizable value.",
         "No inspection or write-down step for returned goods.",
         "Inventory may be overstated by part of these amounts; below performance materiality.", "Valuation follow-up",
         "Inspect returned goods and write down damaged items before restocking."],
        ["F6. The largest refund (follow-up)",
         f"{L['rf']['num']}, {money(L['rf']['amt'])}, paid by wire on a {L['weekday']} to a customer who paid by check, "
         f"while {money(L['unpaid_refund'])} of the invoice was unpaid; its credit, the largest of the three years, "
         "was approved by a representative with a limit of $0.", "C2, C7, C8.",
         "Not yet known.", "Not yet known; the records balance.", "Follow up",
         "Obtain the wire confirmation's beneficiary and account, a customer confirmation, the inspection record, and "
         "the customer's request (appendix: Timeline)."],
    ]
    r = merged_table(ws, r, [1, 1, 1, 1, 1, 1, 1], ["Finding", "Condition", "Criteria", "Cause", "Effect", "Rating",
                                                   "Recommendation"], findings)
    r = text_block(ws, r, "Clean results", [
        "The reconciliations of every population, the completeness and accuracy of the clawbacks, the approvers' "
        "employment dates, the separation of the refund approver from the credit approver, one refund per credit, "
        "the recomputation of every credit (quantity, price, discount, tax, and freight), and the lapping tests "
        "(no receipt applied to another customer's invoice; deposits within two days) found no exception. The "
        "receipts applied to invoices dated after them are customer deposits held in 2060, not lapping."], span=7)
    heading(ws, r, "Action plans")
    r += 1
    plans = [
        ["Approve a delegation of authority for credits and refunds, and enforce it in the system", "Controller, with "
         "the chief financial officer", f"{f.C + 1}-12-31", "Agree; may ask for thresholds",
         "The customer service manager may argue that representatives need authority for small credits: answer with "
         "the credits above $0 and propose a threshold with a second approver above it."],
        ["Have credits approved by someone who does not record or apply the customer's cash", "Customer service "
         "manager", f"{f.C + 2}-03-31", "Will point to the warehouse receipt as the compensating control",
         "The receipt shows that goods came back, not that the credit's amount or the customer's cash was right; "
         "show the credits whose approver applied the invoice's cash."],
        ["Book credits on unpaid invoices against the receivable, and release refunds only after cleared payment",
         "Controller", f"{f.C + 2}-03-31", "Agree; a change to the posting rule",
         "Little disagreement expected; show the refunds dated before the payment and the credits posted to 2060 on "
         "unpaid invoices."],
        ["Pay refunds to the original instrument or a verified account, offsetting open balances first",
         "Accounting manager", f"{f.C + 2}-03-31", "Will point to the review of each credit balance",
         "The review did not stop refunds before payment or to customers past due by at least the refund; show its "
         "precision with those counts."],
        ["Record a preparer on credits and refunds, separate from the approver", "Controller, with IT",
         f"{f.C + 2}-06-30", "Agree", "Cost of a system change; the audit committee can weigh it against the risk."],
        ["Review the concentration of duties with the Accounting Manager (commissions, refunds, payroll)",
         "Chief financial officer", f"{f.C + 1}-12-31", "May argue that the team is small",
         "Managers resist a weakness when no error has been detected (Cohen et al., 2020): answer with the likelihood "
         "and the absence of any independent review, not with a detected error."],
        [f"Approve the {f.C + 1} commission rates (the approved rates ended on {f.commission['rate_ends'][-1]})",
         "Chief financial officer", f"{f.C + 1}-11-30", "Agree", "None expected."],
        ["Inspect returned goods and write down damaged items before restocking", "Warehouse manager, with the "
         "controller", f"{f.C + 2}-03-31", "Agree; may question the cost of inspection",
         "Show the Damaged and Quality Concern returns restocked at full cost."],
        ["Settle the follow-up of the largest refund", "Internal audit", f"{f.C + 1}-10-31", "Owners will supply the "
         "documents", "None expected; the result goes to the committee."],
        ["Keep the four rule tests running in the exception register (credits and refunds above authority, the credit "
         "approver's cash, refunds before payment), with the historical exceptions recorded once as a design finding",
         "Internal audit", f"{f.C + 1}-11-30", "Agree", "None expected; after remediation the two authority tests "
                                                         "should fall to zero."],
    ]
    r = merged_table(ws, r, [2, 1, 1, 1, 2], ["Action", "Owner (role)", "Date", "Expected response",
                                              "Where we expect disagreement, and the evidence to answer it"], plans)
    put(ws, {f"A{r}": "Action plans with an owner and a date", f"D{r}": f"=COUNTA(D{r - len(plans) - 1}:D{r - 2})"})
    fmt(ws, f"D{r}", COUNT)
    b.check(t, "action plans with a date", len(plans), f"=Report!D{r}", 0, COUNT)


# --- Milestones: the checkpoint values an instructor may release ----------------------------------------------------

def m1(b: ExerciseBuild) -> None:
    f = facts(b)
    t = "Milestone 1"
    e, mat = f.expectation, f.materiality
    b.check(t, "returns", len(f.sr), "='Cycle Map'!C6", 0, COUNT)
    b.check(t, "credit memos", len(f.cm), "='Cycle Map'!C7", 0, COUNT)
    b.check(t, "credit memo total", r2(sum(x["gt"] for x in f.cm.values())), "='Cycle Map'!G7")
    b.check(t, "refunds", len(f.rf), "='Cycle Map'!C8", 0, COUNT)
    b.check(t, "refund total", r2(sum(x["amt"] for x in f.rf.values())), "='Cycle Map'!G8")
    b.check(t, "clawbacks", len(f.adj), "='Cycle Map'!C9", 0, COUNT)
    b.check(t, "clawback total", r2(sum(a["amt"] for a in f.adj)), "='Cycle Map'!G9")
    for y, v in zip(f.years, e["returns"]):
        sub = r2(sum(x["sub"] for x in f.in_year(f.cm.values(), y)))
        assert abs(sub - v) < 0.005
        b.check(t, f"credit SubTotal equals 4060, {y}", sub,
                f"=SUMIFS(Credits[SubTotal],Credits[FiscalYear],{y})")
    for y in f.years:
        b.check(t, f"2060 at the end of {y}", r2(f.balance("2060", y)),
                "=" + gl_f("Cr", 2060, None, str(y), None, "<=") + "-" + gl_f("Dr", 2060, None, str(y), None, "<="))
    b.check(t, "materiality", mat["mat"], "=Materiality", 0.0001)
    b.check(t, "performance materiality", mat["perf"], "=PerformanceMateriality", 0.0001)
    b.check(t, "clearly trivial", mat["trivial"], "=ClearlyTrivial", 0.0001)
    b.check(t, f"expectation of {f.C} returns at the {f.P} rate", e["exp"], "=Materiality!B19")
    b.check(t, f"recorded {f.C} returns", r2(e["actual"]), "=Materiality!B20")


def m2(b: ExerciseBuild) -> None:
    f = facts(b)
    t = "Milestone 2"
    tt, s, L = f.tests, f.sampling, f.largest
    T = b.found["tests"]
    for tid, items, key, label in (("T1", tt["cm_above"], "gt", "credits above the approver's limit"),
                                   ("T2", tt["cash_credit"], "gt", "credit approver also applied cash"),
                                   ("T7", tt["rf_above"], "amt", "refunds above the limit"),
                                   ("T9", tt["before"], "amt", "refunds dated before the customer's payment")):
        st = f.stat(items, key)
        b.check(t, label, st["n"], f"=Tests!H{T[tid]}", 0, COUNT)
        if tid != "T2":
            b.check(t, f"{label}, amount", st["amt"], f"=Tests!I{T[tid]}")
    b.check(t, "key items", len(s["key"]), "=Sample!B26", 0, COUNT)
    b.check(t, "key items, amount", s["key_total"], "=Sample!C26")
    b.check(t, "sample size", s["n"], "=SampleSize", 0, COUNT)
    b.check(t, "remaining refunds", len(s["rest"]), "=Sample!B27", 0, COUNT)
    b.check(t, "largest refund", L["rf"]["num"], "=Timeline!B5")
    b.check(t, "largest refund, amount", L["rf"]["amt"], "=Timeline!B4")
    b.check(t, "unpaid on the refund date", r2(L["unpaid_refund"]), "=" + b.found["unpaid"])


def m3(b: ExerciseBuild) -> None:
    f = facts(b)
    t = "Milestone 3"
    d = b.found["deficiencies"]
    b.check(t, "significant deficiencies", 2, "=" + d["sd"], 0, COUNT)
    b.check(t, "the Accounting Manager's concentration", "Deficiency", "=" + d["g3"])
    b.check(t, "overall", "No material weakness", "=" + d["overall"])
    rows = b.found["register_rows"]
    tt = f.tests
    for tid, items in (("CM AboveLimit", tt["cm_above"]), ("CM CashAndCredit", tt["cash_credit"]),
                       ("RF AboveLimit", tt["rf_above"]), ("RF BeforePayment", tt["before"])):
        b.check(t, f"register additions, {tid}", len(items), f"=Tests!H{rows[tid]}", 0, COUNT)


XL_CALC_MANUAL, XL_CALC_AUTOMATIC = -4135, -4105


def quiet(fn):
    """Apply a requirement with calculation set to manual, so Excel is not busy recalculating while cells are written
    (it rejects COM calls then), and set it back to automatic afterwards."""
    @functools.wraps(fn)
    def run(b: ExerciseBuild) -> None:
        app = b.wb.Application
        xl.wait_ready(app)
        xl.retry(lambda: setattr(app, "Calculation", XL_CALC_MANUAL))
        try:
            fn(b)
        finally:
            xl.retry(lambda: setattr(app, "Calculation", XL_CALC_AUTOMATIC))
            xl.retry(app.Calculate)
            xl.wait_ready(app)
    return run


EXERCISES = [("Requirement 1", quiet(r1)), ("Requirement 2", quiet(r2_)), ("Requirement 3", quiet(r3)),
             ("Requirement 4", quiet(r4)), ("Requirement 6", quiet(r6)), ("Requirement 7", quiet(r7)),
             ("Requirement 8", quiet(r8)), ("Requirement 9", quiet(r9)), ("Milestone 1", m1), ("Milestone 2", m2),
             ("Milestone 3", m3)]
