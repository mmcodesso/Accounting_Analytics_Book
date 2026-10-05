"""The data contract: conditions in the Charles River data that the book's storylines rely on.

Each check names the chapters that rely on it and tests the condition relative to the fiscal window
(F, P, C are the first, prior, and current fiscal years, and N = C + 1), never against fixed years or
values, so it applies to any build of the generator. Run it on a new build before it replaces the
book's dataset:

    python facts/contract.py [--db path/to/CharlesRiver.sqlite] [--json out.json]
    python facts/contract.py --snapshot-schema      # record the schema of the current dataset

A failing check means a chapter's analysis no longer holds on that build: either the generator must
plant the condition again, or the chapter must change. facts/baseline-2026.md holds the exact values
of the 2026 edition behind each condition.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from math import log10
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import DB, Data  # noqa: E402

HERE = Path(__file__).resolve().parent
SCHEMA_FILE = HERE / "schema-2026.json"
CHECKS: list[tuple[str, str, str, object]] = []


def check(cid: str, chapters: str, text: str):
    def register(fn):
        CHECKS.append((cid, chapters, text, fn))
        return fn
    return register


def pct(a: float, b: float) -> str:
    return f"{(a / b - 1) * 100:+.1f}%" if b else "n/a"


# --- schema and window -------------------------------------------------------------------------

def schema(d: Data) -> dict[str, list[str]]:
    tables = [r[0] for r in d.q("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
    return {t: [r[1] for r in d.q(f"PRAGMA table_info({t})")] for t in tables}


@check("S1", "all", "tables and columns (names and order) are those of the 2026 edition")
def s1(d):
    if not SCHEMA_FILE.exists():
        return False, "no schema snapshot; run with --snapshot-schema on the edition's dataset"
    base, now = json.loads(SCHEMA_FILE.read_text(encoding="utf-8")), schema(d)
    missing = sorted(set(base) - set(now))
    added = sorted(set(now) - set(base))
    changed = sorted(t for t in set(base) & set(now) if base[t] != now[t])
    ok = not missing and not changed
    return ok, f"{len(now)} tables; missing {missing or 'none'}; changed {changed or 'none'}; added {added or 'none'}"


# Power Query types each column of an Excel source from its first 200 rows (Microsoft Learn, "Data types in Power
# Query"). A numeric column that is whole in those rows but fractional later becomes a whole number and is rounded; a
# column empty in those rows gets no type. Tutorials 4.1 and 13.1, Exercises 8.6, 13.1 and 13.5, and the Part II case tell
# readers to correct the columns below. A roll that adds a column to these lists needs the same treatment in the text.
TYPE_TRAPS_WHOLE = {"SalesInvoiceLine.Discount", "SalesOrderLine.Discount", "SalesInvoice.FreightAmount",
                    "MaterialRequirementPlan.NetRequirementQuantity", "MaterialRequirementPlan.RecommendedOrderQuantity"}
TYPE_TRAPS_EMPTY = {"GLEntry.SourceLineID", "JournalEntry.ReversesJournalEntryID", "LaborTimeEntry.WorkOrderID",
                    "LaborTimeEntry.WorkOrderOperationID", "OvertimeApproval.WorkOrderID",
                    "OvertimeApproval.WorkOrderOperationID", "PayrollRegisterLine.Hours", "PayrollRegisterLine.Rate",
                    "PayrollRegisterLine.WorkOrderID", "PayrollRegisterLine.LaborTimeEntryID",
                    "PurchaseInvoiceLine.AccrualJournalEntryID", "SalesInvoiceLine.PromotionID",
                    "SalesOrderLine.PromotionID", "TimeClockEntry.WorkOrderID", "TimeClockEntry.WorkOrderOperationID",
                    "TimeClockPunch.WorkCenterID"}


@check("S2", "4, 8, 13, Part II case", "Power Query's 200-row type detection mistypes only the columns the text corrects")
def s2(d):
    whole, empty = set(), set()
    for (t,) in d.q("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"):
        for col in [r[1] for r in d.q(f"PRAGMA table_info({t})")]:
            head = [r[0] for r in d.q(f"SELECT {col} FROM {t} ORDER BY rowid LIMIT 200")]
            values = [v for v in head if v is not None]
            if not values:
                if d.one(f"SELECT COUNT(*) FROM {t} WHERE {col} IS NOT NULL"):
                    empty.add(f"{t}.{col}")
            elif all(isinstance(v, (int, float)) and float(v).is_integer() for v in values):
                if d.one(f"SELECT COUNT(*) FROM {t} WHERE typeof({col}) = 'real' AND {col} <> CAST({col} AS INTEGER)"):
                    whole.add(f"{t}.{col}")
    new = sorted((whole - TYPE_TRAPS_WHOLE) | (empty - TYPE_TRAPS_EMPTY))
    return not new, f"whole in the first 200 rows, fractional later: {len(whole)}; empty, filled later: {len(empty)}; new: {new or 'none'}"


@check("W1", "1, 8, 17, Part IV case", "three fiscal years of sales; fiscal N holds only supplier payments, early in the year")
def w1(d):
    types = d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE FiscalYear = ?", d.N)
    last = d.one("SELECT MAX(PostingDate) FROM GLEntry WHERE FiscalYear = ?", d.N)
    ok = d.C - d.F == 2 and [t[0] for t in types] == ["DisbursementPayment"] and last < f"{d.N}-04-01"
    return ok, f"window {d.F}-{d.C}; fiscal {d.N} types {[t[0] for t in types]}, last {last}"


@check("W2", "10, 11, 12, Part III case, 17", "time records end in mid-December of C, with the last two pay periods Open")
def w2(d):
    last = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    open_ = d.q("SELECT PeriodStartDate, (SELECT COUNT(*) FROM PayrollRegister r WHERE r.PayrollPeriodID = p.PayrollPeriodID) "
                "FROM PayrollPeriod p WHERE Status = 'Open' ORDER BY PeriodStartDate")
    ok = (f"{d.C}-12-01" <= last <= f"{d.C}-12-24" and len(open_) == 2
          and all(s > last and n == 0 for s, n in open_))
    return ok, f"last work date {last}; open periods {open_}"


@check("W3", "11, 12, 14, 15, Part III case", "each fiscal year has months with three pay dates")
def w3(d):
    counts = {}
    for y in d.years:
        counts[y] = d.one("SELECT COUNT(*) FROM (SELECT substr(PayDate, 1, 7) AS m FROM PayrollPeriod "
                          "WHERE Status = 'Processed' AND substr(PayDate, 1, 4) = ? GROUP BY m HAVING COUNT(*) = 3)", str(y))
    return all(counts[y] >= 1 for y in d.years[1:]), f"three-pay-date months by year {counts}"


@check("W4", "11, 12, Part III case, 17", "no month-end wage accrual: account 2030 has no journal entries but the opening")
def w4(d):
    n = d.one("SELECT COUNT(*) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
              "WHERE g.SourceDocumentType = 'JournalEntry' AND g.AccountID = ? AND j.EntryType <> 'Opening'", d.account("2030"))
    return n == 0, f"{n} non-opening journal rows to 2030"


DOCUMENT_DATES = [("SalesOrder", "OrderDate"), ("SalesInvoice", "InvoiceDate"), ("Shipment", "ShipmentDate"),
                  ("CashReceipt", "ReceiptDate"), ("PurchaseOrder", "OrderDate"), ("PurchaseInvoice", "InvoiceDate"),
                  ("GoodsReceipt", "ReceiptDate"), ("JournalEntry", "PostingDate")]


@check("W5", "4, 5, 13, 14, 15, 16", "no document is dated before the first fiscal year (the Date tables start there)")
def w5(d):
    # Found in the robustness pass (2026-10-03): the pinned fiscal 2025-2027 build dates 2 sales invoices 2024-12-31,
    # the planted invoices dated before their shipment, pushed across the window's start.
    early = {f"{t}.{c}": d.one(f"SELECT COUNT(*) FROM {t} WHERE {c} < ?", f"{d.F}-01-01") for t, c in DOCUMENT_DATES}
    early = {k: n for k, n in early.items() if n}
    return not early, f"dated before {d.F}-01-01: {early or 'none'}"


# --- Parts I and II: the Furniture margin -----------------------------------------------------

def quarter_margin(d, year: int, q: int) -> float:
    months = [f"{year}-{m:02d}" for m in range(3 * q - 2, 3 * q + 1)]
    marks = ",".join(f"'{m}'" for m in months)
    rev = d.one(f"SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry' "
                f"AND substr(PostingDate, 1, 7) IN ({marks})", d.account("4010"))
    cogs = d.one(f"SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry' "
                 f"AND substr(PostingDate, 1, 7) IN ({marks})", d.account("5010"))
    return 1 - cogs / rev


@check("P1", "1, Part I case, 4-7, Part II case, 13-15", "the Furniture gross margin falls by a point or more from Q3 to Q4 of C")
def p1(d):
    q3, q4 = quarter_margin(d, d.C, 3), quarter_margin(d, d.C, 4)
    return q3 - q4 >= 0.01, f"Q3 {q3:.1%}, Q4 {q4:.1%}"


def furniture_quarter(d, year: int, q: int) -> tuple[float, float, float]:
    r = d.q("SELECT SUM(l.Quantity), SUM(l.LineTotal), SUM(l.Quantity * i.StandardCost) "
            "FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID "
            "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND substr(s.InvoiceDate, 1, 4) = ? "
            "AND CAST(substr(s.InvoiceDate, 6, 2) AS INTEGER) BETWEEN ? AND ?", str(year), 3 * q - 2, 3 * q)[0]
    return r[0], r[1] / r[0], r[2] / r[0]


@check("P2", "6, Part II case, 14", "the Q4 fall is a price effect: price per unit down, units and standard cost per unit about flat")
def p2(d):
    (u3, p3, c3), (u4, p4, c4) = furniture_quarter(d, d.C, 3), furniture_quarter(d, d.C, 4)
    ok = p4 / p3 - 1 <= -0.015 and abs(u4 / u3 - 1) <= 0.15 and abs(c4 / c3 - 1) <= 0.03
    return ok, f"price {pct(p4, p3)}, units {pct(u4, u3)}, standard cost per unit {pct(c4, c3)}"


@check("P3", "4-7, Part II case, 15", "three promotions a year (spring collection 8%, Sep-Oct item group 10%, November segment 12%), "
       "and C's item-group promotion is Furniture, with the most invoice lines of any promotion")
def p3(d):
    promos = d.q("SELECT PromotionID, ScopeType, ItemGroup, DiscountPct, EffectiveStartDate FROM PromotionProgram ORDER BY PromotionID")
    by_year = Counter(p[4][:4] for p in promos)
    pattern = all(
        [(p[1], round(p[3], 2), p[4][5:]) for p in promos if p[4][:4] == str(y)]
        == [("Collection", 0.08, "03-01"), ("ItemGroup", 0.1, "09-01"), ("Segment", 0.12, "11-01")]
        for y in d.years)
    furniture = [p[0] for p in promos if p[4][:4] == str(d.C) and p[1] == "ItemGroup" and p[2] == "Furniture"]
    top = d.q("SELECT PromotionID, COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL "
              "GROUP BY PromotionID ORDER BY 2 DESC LIMIT 1")[0]
    ok = pattern and furniture and top[0] == furniture[0]
    return ok, f"by year {dict(by_year)}; pattern {'ok' if pattern else 'differs'}; C item group {[p[2] for p in promos if p[4][:4] == str(d.C) and p[1] == 'ItemGroup']}; most lines promotion {top}"


@check("P4", "4, 6, 8", "discounts only on promotion lines, and LineTotal = ROUND(Quantity * UnitPrice * (1 - Discount), 2)")
def p4(d):
    stray = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE Discount > 0 AND PromotionID IS NULL")
    # The generator rounds half up, as Excel does; SQLite's ROUND on a binary float can land a cent lower.
    off = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ABS(LineTotal - Quantity * UnitPrice * (1 - Discount)) > 0.0051")
    return stray == 0 and off == 0, f"discount without promotion {stray}; LineTotal off {off}"


@check("P5", "8, Part II case", "promotions whose end date is before their start date (a master-data error)")
def p5(d):
    n = d.one("SELECT COUNT(*) FROM PromotionProgram WHERE EffectiveEndDate < EffectiveStartDate")
    return n >= 1, f"{n} promotions"


@check("P6", "7, 15, Part II case", "the sales budget's volume is inflated: C's budgeted units are 2.5 times invoiced units or more")
def p6(d):
    budget = d.one("SELECT SUM(Quantity) FROM BudgetLine WHERE BudgetCategory = 'Revenue' AND FiscalYear = ?", d.C)
    actual = d.one("SELECT SUM(l.Quantity) FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID "
                   "WHERE substr(s.InvoiceDate, 1, 4) = ? AND l.ItemID IN (SELECT ItemID FROM BudgetLine WHERE BudgetCategory = 'Revenue')", str(d.C))
    return budget / actual >= 2.5, f"budget / invoiced units {budget / actual:.2f}"


@check("P7", "2, 3, 5, 10", "master-data quirks: same-name customers, items with a blank ListPrice, fractional quantities on Furniture lines")
def p7(d):
    names = d.one("SELECT COUNT(*) FROM (SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1)")
    blank = d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NULL")
    frac = d.one("SELECT AVG(l.Quantity <> CAST(l.Quantity AS INTEGER)) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID "
                 "WHERE i.ItemGroup = 'Furniture'")
    return names >= 1 and blank >= 1 and frac > 0.5, f"same-name customers {names}; blank ListPrice {blank}; fractional Furniture lines {frac:.0%}"


@check("P8", "2, 5, 6, 12, 14", "cutoff quirks: a handful of invoices dated before their order's first shipment, and invoices numbered with the next year")
def p8(d):
    before = d.one("SELECT COUNT(*) FROM SalesInvoice s WHERE s.InvoiceDate < (SELECT MIN(ShipmentDate) FROM Shipment sh "
                   "WHERE sh.SalesOrderID = s.SalesOrderID)")
    prefix = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE substr(InvoiceNumber, 4, 4) <> substr(InvoiceDate, 1, 4)")
    return 1 <= before <= 30 and prefix >= 3, f"dated before shipment {before}; number year differs from date {prefix}"


@check("P9", "6, 8, 10, 14", "an opening entry (the first journal entry) with receivable and payable lines, and two year-end closes dated 12-31 each year")
def p9(d):
    first = d.q("SELECT JournalEntryID, EntryType FROM JournalEntry ORDER BY JournalEntryID LIMIT 1")[0]
    accts = {str(r[0]) for r in d.q("SELECT a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                               "WHERE g.SourceDocumentType = 'JournalEntry' AND g.SourceDocumentID = ?", first[0])}
    closes = {y: d.one("SELECT COUNT(*) FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' AND PostingDate = ?", f"{y}-12-31")
              for y in d.years}
    ok = first[1] == "Opening" and {"1020", "2010"} <= accts and all(n == 2 for n in closes.values())
    return ok, f"first entry {first[1]} with 1020 {'1020' in accts}, 2010 {'2010' in accts}; closes {closes}"


# --- Chapter 8: audit analytics ------------------------------------------------------------------

@check("A1", "8, 11, 16", "journal entries created on weekends, self-approved, and approved above the approver's limit")
def a1(d):
    weekend = d.one("SELECT COUNT(*) FROM JournalEntry WHERE strftime('%w', CreatedDate) IN ('0', '6')")
    selfapp = d.one("SELECT COUNT(*) FROM JournalEntry WHERE CreatedByEmployeeID = ApprovedByEmployeeID")
    above = d.one("SELECT COUNT(*) FROM JournalEntry j JOIN Employee e ON e.EmployeeID = j.ApprovedByEmployeeID "
                  "WHERE j.TotalAmount > e.MaxApprovalAmount")
    return weekend >= 5 and selfapp >= 3 and above >= 3, f"weekend {weekend}; self-approved {selfapp}; above limit {above}"


@check("A2", "2, 8, 12, 16", "duplicate supplier invoice numbers and reused check numbers")
def a2(d):
    dup = d.one("SELECT COUNT(*) FROM (SELECT SupplierID, InvoiceNumber FROM PurchaseInvoice GROUP BY 1, 2 HAVING COUNT(*) > 1)")
    checks = d.one("SELECT COUNT(*) FROM (SELECT CheckNumber FROM DisbursementPayment WHERE CheckNumber IS NOT NULL "
                   "GROUP BY CheckNumber HAVING COUNT(*) > 1)")
    return dup >= 2 and checks >= 1, f"duplicate invoice numbers {dup}; reused check numbers {checks}"


def mad(amounts: list[float]) -> float:
    digits = Counter(int(f"{a:.8e}"[0]) for a in amounts if a > 0)
    total = sum(digits.values())
    return sum(abs(digits.get(k, 0) / total - log10(1 + 1 / k)) for k in range(1, 10)) / 9


@check("A3", "8, 12, 16", "Benford: partial payments (only on invoices of 1,000 or more) do not conform; full payments do")
def a3(d):
    rows = d.q("SELECT p.Amount, i.GrandTotal FROM DisbursementPayment p JOIN PurchaseInvoice i ON i.PurchaseInvoiceID = p.PurchaseInvoiceID "
               "WHERE p.PaymentDate <= ?", f"{d.C}-12-31")
    full = [a for a, g in rows if abs(a - g) < 0.005]
    partial = [(a, g) for a, g in rows if a < g - 0.005]
    small = sum(1 for _, g in partial if g < 1000)
    mf, mp = mad(full), mad([a for a, _ in partial])
    return small == 0 and mp > 0.015 and mf < 0.012, f"full MAD {mf:.5f}; partial MAD {mp:.5f}; partial on invoices under 1,000: {small}"


@check("A4", "2, 8, 11", "requisitions with no approver, all converted to purchase orders")
def a4(d):
    rows = d.q("SELECT Status, COUNT(*) FROM PurchaseRequisition WHERE ApprovedByEmployeeID IS NULL GROUP BY Status")
    return bool(rows) and all(s == "Converted to PO" for s, _ in rows), f"{rows}"


@check("A5", "8", "order lines priced from price lists after the list's end date")
def a5(d):
    n = d.one("SELECT COUNT(*) FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
              "JOIN PriceListLine pl ON pl.PriceListLineID = l.PriceListLineID JOIN PriceList p ON p.PriceListID = pl.PriceListID "
              "WHERE o.OrderDate > p.EffectiveEndDate")
    return n >= 100, f"{n} lines"


# --- Part III: the plant ---------------------------------------------------------------------------

@check("M1", "9-12, Part III case, 18", "manufacturing variance (5080, closes excluded) grows 40% or more from F to C while revenue grows under 15%")
def m1(d):
    v = {y: d.one(f"SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                  d.account("5080"), y) for y in (d.F, d.C)}
    r = {y: d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID "
                  "WHERE substr(s.InvoiceDate, 1, 4) = ?", str(y)) for y in (d.F, d.C)}
    return v[d.C] / v[d.F] >= 1.4 and r[d.C] / r[d.F] < 1.15, f"variance {pct(v[d.C], v[d.F])}; revenue {pct(r[d.C], r[d.F])}"


SURGE = ("SELECT t.WorkDate FROM TimeClockEntry t JOIN Employee e ON e.EmployeeID = t.EmployeeID "
         "JOIN CostCenter c ON c.CostCenterID = e.CostCenterID WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly' "
         "GROUP BY t.WorkDate HAVING COUNT(*) >= 40 AND MIN(t.OvertimeHours) = MAX(t.OvertimeHours) AND MIN(t.OvertimeHours) >= 4 "
         "AND MIN(t.RegularHours) = MAX(t.RegularHours)")


@check("M2", "12, Part III case, 16", "surge days (every hourly manufacturing employee clocks the same hours with 4+ overtime) exist and grow each year")
def m2(d):
    days = Counter(r[0][:4] for r in d.q(SURGE))
    n = [days.get(str(y), 0) for y in d.years]
    return n[0] >= 1 and n[0] < n[1] < n[2], f"surge days by year {dict(zip(d.years, n))}"


def by_year(d, sql: str) -> list[float]:
    return [d.one(sql, str(y)) or 0.0 for y in d.years]


@check("M3", "10, 11, 12, 15", "the direct-labor overtime share rises each year")
def m3(d):
    s = by_year(d, "SELECT SUM(OvertimeHours) / SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry "
                   "WHERE LaborType = 'Direct Manufacturing' AND substr(WorkDate, 1, 4) = ?")
    return s[0] < s[1] < s[2], "overtime share " + ", ".join(f"{x:.3f}" for x in s)


@check("M4", "12, Part III case", "the share of direct labor recorded after its operation ended rises each year")
def m4(d):
    s = by_year(d, "SELECT SUM(CASE WHEN l.WorkDate > o.ActualEndDate THEN l.RegularHours + l.OvertimeHours ELSE 0 END) "
                   "/ SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l JOIN WorkOrderOperation o "
                   "ON o.WorkOrderOperationID = l.WorkOrderOperationID WHERE l.LaborType = 'Direct Manufacturing' "
                   "AND substr(l.WorkDate, 1, 4) = ?")
    return s[0] < s[1] < s[2], "share after end " + ", ".join(f"{x:.3f}" for x in s)


@check("M5", "11, 12", "the start-up build: far less indirect time in February-May of F than in July-December")
def m5(d):
    months = dict(d.q("SELECT CAST(substr(WorkDate, 6, 2) AS INTEGER), SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry "
                      "WHERE LaborType = 'Indirect Manufacturing' AND substr(WorkDate, 1, 4) = ? GROUP BY 1", str(d.F)))
    early = sum(months.get(m, 0) for m in (2, 3, 4, 5)) / 4
    late = sum(months.get(m, 0) for m in range(7, 13)) / 6
    return late > 0 and early / late < 0.30, f"indirect hours a month: Feb-May {early:,.0f}, Jul-Dec {late:,.0f}"


@check("M6", "12, Part IV case, 16, 19", "payroll controls: one approver for every register, pay after termination, and payments missing behind ledger rows")
def m6(d):
    approvers = d.one("SELECT COUNT(DISTINCT ApprovedByEmployeeID) FROM PayrollRegister")
    after = d.one("SELECT COUNT(*) FROM PayrollRegister r JOIN PayrollPeriod p ON p.PayrollPeriodID = r.PayrollPeriodID "
                  "JOIN Employee e ON e.EmployeeID = r.EmployeeID WHERE e.TerminationDate < p.PeriodStartDate")
    orphans = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'PayrollPayment' "
                    "AND SourceDocumentID NOT IN (SELECT PayrollPaymentID FROM PayrollPayment)")
    return approvers == 1 and after >= 1 and orphans >= 1, f"approvers {approvers}; registers after termination {after}; orphan GL rows {orphans}"


@check("M7", "10, 12", "overtime above half an hour is approved except a few entries; half an hour or less never is")
def m7(d):
    missing = d.one("SELECT COUNT(*) FROM TimeClockEntry WHERE OvertimeHours > 0.5 AND OvertimeApprovalID IS NULL")
    short = d.one("SELECT COUNT(*) FROM TimeClockEntry WHERE OvertimeHours > 0 AND OvertimeHours <= 0.5 AND OvertimeApprovalID IS NOT NULL")
    return 1 <= missing <= 10 and short == 0, f"long without approval {missing}; short with approval {short}"


@check("M8", "9, 10", "a few hundred work orders still open at the end of C")
def m8(d):
    n = d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate IS NULL")
    return n >= 100, f"{n} open"


@check("M9", "12, 14, 16, 17", "revenue cutoff: December deliveries invoiced in January after F and P; December C shipment lines never invoiced")
def m9(d):
    late = {y: d.one("SELECT COUNT(DISTINCT s.SalesInvoiceID) FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID "
                     "JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment sh ON sh.ShipmentID = sl.ShipmentID "
                     "WHERE substr(sh.DeliveryDate, 1, 7) = ? AND substr(s.InvoiceDate, 1, 4) = ?", f"{y}-12", str(y + 1))
            for y in (d.F, d.P)}
    never = d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Shipment sh ON sh.ShipmentID = sl.ShipmentID "
                  "WHERE substr(sh.ShipmentDate, 1, 7) = ? AND sl.ShipmentLineID NOT IN "
                  "(SELECT ShipmentLineID FROM SalesInvoiceLine WHERE ShipmentLineID IS NOT NULL)", f"{d.C}-12")
    return all(n >= 1 for n in late.values()) and never >= 1, f"invoiced in January {late}; December {d.C} lines never invoiced {never}"


# --- Part IV case: cash --------------------------------------------------------------------------------

def net_income(d, year: int) -> float:
    return d.one(f"SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                 f"WHERE a.AccountType IN ('Revenue', 'Expense') AND g.FiscalYear = ? AND g.{d.no_closes()}", year)


@check("C1", "Part IV case, 17", "sales tax is collected and never remitted: 2050 is debited only by credit memos")
def c1(d):
    other = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND Debit > 0 AND SourceDocumentType <> 'CreditMemo'", d.account("2050"))
    bal = [-d.balance(["2050"], f"{y}-12-31") for y in d.years]
    return other == 0 and bal[0] < bal[1] < bal[2], f"other debits {other}; balance " + ", ".join(f"{b:,.0f}" for b in bal)


@check("C2", "Part IV case, 17", "cash falls in C while net income is positive, and inventories rise by more than half of net income")
def c2(d):
    cash = d.balance(["1010"], f"{d.C}-12-31") - d.balance(["1010"], f"{d.P}-12-31")
    inv = d.balance(["1040", "1045", "1046"], f"{d.C}-12-31") - d.balance(["1040", "1045", "1046"], f"{d.P}-12-31")
    ni = net_income(d, d.C)
    return cash < 0 < ni and inv > 0.5 * ni, f"cash {cash:,.0f}; net income {ni:,.0f}; inventories {inv:+,.0f}"


@check("C3", "Part IV case", "work-order shortfall requisitions are raised again for the same work order and item")
def c3(d):
    n = d.one("SELECT COALESCE(SUM(n), 0) FROM (SELECT COUNT(*) AS n FROM PurchaseRequisition "
              "WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%' GROUP BY Justification HAVING COUNT(*) > 1)")
    return n >= 1000, f"{n} requisitions in repeated work order and item pairs"


# --- Part V: the capstones --------------------------------------------------------------------------------

@check("V1", "17", "accruals of C older than about two months that no supplier invoice ever cleared")
def v1(d):
    n = d.one("SELECT COUNT(*) FROM JournalEntry WHERE EntryType = 'Accrual' AND PostingDate BETWEEN ? AND ? "
              "AND JournalEntryID NOT IN (SELECT AccrualJournalEntryID FROM PurchaseInvoiceLine WHERE AccrualJournalEntryID IS NOT NULL) "
              "AND JournalEntryID NOT IN (SELECT ReversesJournalEntryID FROM JournalEntry WHERE ReversesJournalEntryID IS NOT NULL)",
              f"{d.C}-01-01", f"{d.C}-10-30")
    return n >= 5, f"{n} old accruals"


@check("V2", "19", "credits approved above the approver's limit, and refunds paid before the customer's last payment on the invoice")
def v2(d):
    above = d.one("SELECT COUNT(*) FROM CreditMemo c JOIN Employee e ON e.EmployeeID = c.ApprovedByEmployeeID WHERE c.GrandTotal > e.MaxApprovalAmount")
    early = d.one("SELECT COUNT(*) FROM CustomerRefund r JOIN CreditMemo c ON c.CreditMemoID = r.CreditMemoID "
                  "WHERE r.RefundDate < (SELECT MAX(ApplicationDate) FROM CashReceiptApplication a WHERE a.SalesInvoiceID = c.OriginalSalesInvoiceID)")
    return above >= 100 and early >= 10, f"credits above limit {above}; refunds before last payment {early}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--snapshot-schema", action="store_true")
    args = parser.parse_args()
    d = Data(args.db)
    if args.snapshot_schema:
        SCHEMA_FILE.write_text(json.dumps(schema(d), indent=1) + "\n", encoding="utf-8")
        print(f"wrote {SCHEMA_FILE}")
        return 0
    print(f"{args.db}: fiscal {d.F}-{d.C}")
    results, failed = [], 0
    for cid, chapters, text, fn in CHECKS:
        try:
            ok, detail = fn(d)
        except Exception as exc:  # a missing table or column is a failure, not a crash
            ok, detail = False, f"error: {exc}"
        failed += not ok
        results.append(dict(id=cid, ok=bool(ok), chapters=chapters, check=text, detail=detail))
        print(f"{'PASS' if ok else 'FAIL'}  {cid:3} {text}\n         {detail}")
    print(f"{len(CHECKS) - failed} of {len(CHECKS)} checks pass")
    if args.json:
        args.json.write_text(json.dumps(dict(db=str(args.db), window=[d.F, d.C], results=results), indent=1), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
