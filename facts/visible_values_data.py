"""The queries behind the val.* keys of facts/visible_values.py.

Each group below computes a family of keys from a facts/db.Data window `d` (F, P, C, N), read-only, so a roll
recomputes them on the new dataset. Where a hidden note already computes a value, the group reads it from the
note's context function (`note(d, "ch10.ex2")`) instead of querying again. A group that cannot be computed on a
dataset (a document the text relies on is missing) leaves its keys out and records why in ERRORS; the rewriter
then refuses to rewrite the literals that use those keys and lists them for the impact review.

A key's name says what it is: val.trace.* the traced sale of Chapters 1 and 3, val.account_id.<number> an Account
surrogate key, val.furniture.margin.Q3 a margin, and so on. The values are numbers (float or int) or strings;
visible_values.display() writes them in the format of the literal.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

GROUPS: list[tuple[str, Callable]] = []
ERRORS: dict[str, str] = {}


def group(fn: Callable) -> Callable:
    GROUPS.append((fn.__name__, fn))
    return fn


_CACHE: dict = {}


def note(d, key: str) -> dict:
    """The context of one generated note on this dataset (facts/notes/<chapter>.py), cached per dataset."""
    ck = (id(d), key)
    if ck not in _CACHE:
        import notes as _notes
        _notes.load()
        claims = _notes.Claims()
        _CACHE[ck] = _notes.NOTES[key].context(d, claims)
    return _CACHE[ck]


def trace_ids(d) -> dict:
    """The traced sale's registry keys (agent A's selection rule in facts/visible.py)."""
    ck = (id(d), "trace")
    if ck not in _CACHE:
        import visible
        _CACHE[ck] = visible.trace(d)
    return _CACHE[ck]


def one(d, sql, *args):
    row = d.q(sql, *args)
    if not row:
        raise LookupError(sql[:80])
    return row[0]


# --- accounts --------------------------------------------------------------------------------------

@group
def accounts(d) -> dict:
    """val.account_id.<AccountNumber>: the Account surrogate key of each account (AccountID 42 is account 4010)."""
    return {f"val.account_id.{int(n)}": i for i, n in d.q("SELECT AccountID, AccountNumber FROM Account")}


# --- the traced sale (Chapters 1 and 3) ------------------------------------------------------------

@group
def trace(d) -> dict:
    """The amounts of the sale selected by visible.trace: the invoice (SubTotal, freight, tax, GrandTotal), its one
    line (UnitPrice, LineTotal), the item's standard cost and list price, the shipment's cost postings, and the
    check that paid it. The invoice's SubTotal equals its line total because it has one line."""
    t = trace_ids(d)
    sid, line = t["id.trace.invoice_id"], t["id.trace.line_id"]
    sub, fr, tax, gt = one(d, "SELECT SubTotal, FreightAmount, TaxAmount, GrandTotal FROM SalesInvoice WHERE SalesInvoiceID = ?", sid)
    price, total, qty = one(d, "SELECT UnitPrice, LineTotal, Quantity FROM SalesInvoiceLine WHERE SalesInvoiceLineID = ?", line)
    cost, lst = one(d, "SELECT StandardCost, ListPrice FROM Item WHERE ItemID = ?", t["id.trace.item_id"])
    ext = one(d, "SELECT ExtendedStandardCost FROM ShipmentLine WHERE ShipmentLineID = ?", t["id.trace.shipment_line_id"])[0]
    rec = one(d, "SELECT Amount FROM CashReceipt WHERE CashReceiptID = ?", t["id.trace.receipt_id"])[0]
    out = {"val.trace.subtotal": sub, "val.trace.line_total": total, "val.trace.freight": fr, "val.trace.tax": tax,
           "val.trace.grand_total": gt, "val.trace.unit_price": price, "val.trace.standard_cost": cost,
           "val.trace.list_price": lst, "val.trace.extended_cost": ext, "val.trace.receipt_amount": rec,
           "val.trace.quantity": qty, "val.trace.line_total_x100": round(total * 100), "val.trace.item_number": int(t["id.trace.item_code"][-4:])}
    line_plus = {n: line + n for n in (1, 2, 3)}
    out.update({f"val.trace.line_id_p{n}": v for n, v in line_plus.items()})
    return out


@group
def freight(d) -> dict:
    """Chapter 2's outlier: the mean and the largest FreightCost over all shipments."""
    mean, top = one(d, "SELECT ROUND(AVG(FreightCost), 2), MAX(FreightCost) FROM Shipment")
    return {"val.freight.mean": mean, "val.freight.max": top}


@group
def first_rows(d) -> dict:
    """Master-data rows the slides name: the first sales order and its customer, and two items' standard costs."""
    cust = one(d, "SELECT CustomerID FROM SalesOrder WHERE SalesOrderID = 1")[0]
    inv_order = one(d, "SELECT SalesOrderID FROM SalesInvoice WHERE SalesInvoiceID = 1")[0]
    c3 = one(d, "SELECT StandardCost FROM Item WHERE ItemID = 3")[0]
    c9, code9 = one(d, "SELECT StandardCost, ItemCode FROM Item WHERE ItemID = 9")
    return {"val.order1.customer_id": cust, "val.invoice1.order_id": inv_order,
            "val.item3.standard_cost": c3, "val.item9.standard_cost": c9, "val.item9.code": code9}


@group
def gl_totals(d) -> dict:
    """The ledger as a whole: total debits (equal to total credits), and the rows after the last fiscal year of
    sales (the supplier payments of the next year)."""
    debits, credits = one(d, "SELECT ROUND(SUM(Debit), 2), ROUND(SUM(Credit), 2) FROM GLEntry")
    after = d.one("SELECT COUNT(*) FROM GLEntry WHERE FiscalYear > ?", d.C)
    return {"val.gl.total_debits": debits, "val.gl.total_credits": credits, "val.gl.rows_after_window": after}


# --- promotions --------------------------------------------------------------------------------------

@group
def promotions(d) -> dict:
    """The three promotions of C in order (the collection of spring, the item group of September and October, the
    customer segment of November): their PromotionIDs and discount rates; and the distinct discount rates on the
    invoice lines."""
    rows = d.q("SELECT PromotionID, DiscountPct, ItemGroup FROM PromotionProgram "
               "WHERE EffectiveStartDate BETWEEN ? AND ? ORDER BY EffectiveStartDate, PromotionID", f"{d.C}-01-01", f"{d.C}-12-31")
    names = ("collection", "furniture", "segment")
    out = {}
    for name, (pid, rate, _) in zip(names, rows):
        out[f"val.promo.{name}_id"] = pid
        out[f"val.promo.{name}_rate"] = rate
    rates = [r[0] for r in d.q("SELECT DISTINCT Discount FROM SalesInvoiceLine WHERE Discount > 0 ORDER BY Discount")]
    for i, r in enumerate(rates, 1):
        out[f"val.discount.rate.{i}"] = r
    return out


# --- Furniture margins (Chapter 1, Chapter 6, Case 1) --------------------------------------------

@group
def furniture_margin(d) -> dict:
    """Furniture's invoice-based margin at standard cost by quarter of C (4010 revenue lines less their standard cost),
    and the fall from the third quarter to the fourth as a fraction (0.0148116 in the 2026 edition: 1.48116 percentage points)."""
    rows = d.q("""
        SELECT (CAST(substr(s.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3 AS Q,
               SUM(l.LineTotal) AS Rev, SUM(l.Quantity * i.StandardCost) AS Cost
        FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID
        JOIN Item i ON i.ItemID = l.ItemID
        WHERE i.ItemGroup = 'Furniture' AND s.InvoiceDate BETWEEN ? AND ? GROUP BY Q ORDER BY Q""",
               f"{d.C}-01-01", f"{d.C}-12-31")
    m = {q: (rev - cost) / rev for q, rev, cost in rows}
    out = {f"val.furniture.margin.Q{q}": v for q, v in m.items()}
    out["val.furniture.margin_drop"] = m[3] - m[4]
    return out


# --- Part II (Chapters 6-8) --------------------------------------------------------------------------

@group
def trend(d) -> dict:
    """Chapter 7: R squared and the slope's p-value of monthly revenue on a month index, with every month and
    without the first month (the start-up month); the ToolPak's Regression (shared/calculations/excel_analysis)."""
    sys.path.insert(0, str(HERE.parent))
    from shared.calculations import excel_analysis as ea
    rows = d.q("SELECT substr(s.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l "
               "JOIN SalesInvoice s USING (SalesInvoiceID) GROUP BY 1 ORDER BY 1")
    ys = [r[1] for r in rows]
    xs = list(range(1, len(ys) + 1))
    full, rest = ea.regression(xs, ys), ea.regression(xs[1:], ys[1:])
    return {"val.trend.r2": full["r2"], "val.trend.p_with": full["p_b"], "val.trend.p_without": rest["p_b"],
            "val.trend.r2_without": rest["r2"], "val.trend.months": len(ys)}


@group
def commission(d) -> dict:
    """Chapter 7's multiple choice: actual sales commission expense (6290, closes left out) against the static budget
    of the report year, as a share below it."""
    budget = one(d, "SELECT SUM(bl.BudgetAmount) FROM BudgetLine bl JOIN Account a USING (AccountID) "
                    "WHERE a.AccountNumber = 6290 AND bl.FiscalYear = ?", d.C)[0]
    actual = one(d, f"SELECT SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                    f"WHERE a.AccountNumber = 6290 AND g.FiscalYear = ? AND {d.no_closes()}", d.C)[0]
    return {"val.commission.below_static": 1 - actual / budget, "val.commission.actual": actual, "val.commission.static": budget}


@group
def promotion_model(d) -> dict:
    """Tutorial 7.3 and the Part II case: the break-even volume lift of the Furniture promotion of C at its own
    discount (price before discount, standard cost per unit, and the commission rate of all commissions on all
    revenue): (p(1-r) - c) / (p(1-d)(1-r) - c) - 1."""
    pid = promotions(d)["val.promo.furniture_id"]
    rate = promotions(d)["val.promo.furniture_rate"]
    u, r, dsc, sc = one(d, "SELECT SUM(l.Quantity), SUM(l.LineTotal), SUM(l.Quantity * l.UnitPrice * l.Discount), "
                           "SUM(l.Quantity * i.StandardCost) FROM SalesInvoiceLine l JOIN Item i USING (ItemID) "
                           "WHERE l.PromotionID = ?", pid)
    commission = one(d, f"SELECT SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                        f"WHERE g.FiscalYear = ? AND a.AccountNumber = 6290 AND {d.no_closes()}", d.C)[0]
    revenue = one(d, "SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice s USING (SalesInvoiceID) "
                     "WHERE s.InvoiceDate BETWEEN ? AND ?", f"{d.C}-01-01", f"{d.C}-12-31")[0]
    price, cost, comm = (r + dsc) / u, sc / u, commission / revenue
    lift = (price * (1 - comm) - cost) / (price * (1 - rate) * (1 - comm) - cost) - 1
    return {"val.promo.breakeven_lift": lift, "val.promo.commission_rate": comm}


@group
def benford(d) -> dict:
    """Chapter 8: the mean absolute deviation of the first digits of the supplier payments through the end of C
    (the digit read as =--LEFT(TEXT(x,"0.00000000E+00"),1) reads it)."""
    import math
    from collections import Counter
    amounts = [r[0] for r in d.q("SELECT Amount FROM DisbursementPayment WHERE PaymentDate <= ? AND Amount > 0",
                                 f"{d.C}-12-31")]
    counts = Counter(int(f"{a:.8E}"[0]) for a in amounts)
    n = sum(counts.values())
    mad = sum(abs(counts[k] / n - math.log10(1 + 1 / k)) for k in range(1, 10)) / 9
    return {"val.benford.mad": mad, "val.benford.payments": n}


# --- Parts III and IV -----------------------------------------------------------------------------

@group
def sql_chapters(d) -> dict:
    """Chapters 9-12: the size of the ledger ("more than 800,000 rows"), the close of C that posts to 5080 (its
    sequence number and the variance of the most favorable work-order close of C), the hourly manufacturing
    employees, and the first day of the pay periods still Open."""
    import visible
    rows = d.one("SELECT COUNT(*) FROM GLEntry")
    out = {"val.gl.rows": rows}
    pl = visible.closes(d)[f"id.close.pl.C"]
    out["val.close.pl_seq"] = int(pl.rsplit("-", 1)[1])
    out["val.variance.most_favorable"] = d.one("SELECT MIN(TotalVarianceAmount) FROM WorkOrderClose WHERE CloseDate BETWEEN ? AND ?",
                                               f"{d.C}-01-01", f"{d.C}-12-31")
    out["val.plant.hourly_employees"] = d.one(
        "SELECT COUNT(*) FROM Employee e JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
        "WHERE cc.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly'")
    start = one(d, "SELECT PeriodStartDate FROM PayrollPeriod WHERE Status = 'Open' ORDER BY PeriodStartDate")[0]
    out["val.open_period.start_day"] = int(start[8:10])
    out["val.cost_center.manufacturing_id"] = d.one("SELECT CostCenterID FROM CostCenter WHERE CostCenterName = 'Manufacturing'")
    return out


@group
def payroll_registers(d) -> dict:
    """Tutorial 16.3's dispositions: the three registers paid after the payee's termination and the three paid
    before their approval (the first of each fiscal year), from the note that builds the register; and the
    number of registers never paid."""
    t2 = note(d, "ch16.t2")
    out = {}
    for i, n in enumerate(t2["after"]["ids"], 1):
        out[f"val.register.after_termination.{i}"] = n
    for i, n in enumerate(t2["pba"]["ids"], 1):
        out[f"val.register.paid_before_approval.{i}"] = n
    out["val.register.unpaid_count"] = len(note(d, "ch16.t3")["unpaid"])
    return out


@group
def plan(d) -> dict:
    """Chapter 18's assumptions (tbl-18-02): the Part III plan values the capstone states in its text, from the notes
    that compute them (the labor rate and burden of the base year, the first year's hours per standard hour, the
    base year's standard hours, the salaried staff and the depreciation of the plan year)."""
    r3, r4 = note(d, "case3.r3"), note(d, "case3.r4")
    ratio = r3["ratio_f"]["ratio"] if isinstance(r3["ratio_f"], dict) else r3["ratio_f"]
    return {"val.plan.rate": r3["rate"], "val.plan.burden": r3["burden"], "val.plan.burden_factor": 1 + r3["burden"], "val.plan.hours_ratio": ratio,
            "val.plan.indirect_ratio": ratio - 1, "val.plan.standard_hours": r4["std"],
            "val.plan.salary": r4["salary"], "val.plan.depreciation": r4["dep_n"]}


@group
def reports(d) -> dict:
    """Chapters 13 and 15: revenue growth from the first month of the data to the last month of C (the misleading
    chart's "almost 80%"), and the operating-expense variance of the Warehouse cost center."""
    months = d.q("SELECT substr(s.InvoiceDate, 1, 7) AS m, SUM(l.LineTotal) FROM SalesInvoiceLine l "
                 "JOIN SalesInvoice s USING (SalesInvoiceID) GROUP BY m ORDER BY m")
    first, last = months[0][1], [r[1] for r in months if r[0] == f"{d.C}-12"][0]
    out = {"val.revenue.growth_first_to_last": last / first - 1}
    for c in note(d, "ch15.t2")["centers"]:
        out[f"val.cost_center.variance.{c['name']}"] = c["pct"]
    return out


# --- values the figure scripts and shared calculations assert ----------------------------------------

@group
def year_totals(d) -> dict:
    """Chapters 13-15: the Validation page of the report year (lines, revenue, list amount, discounts), the price before
    discount, Furniture's revenue and its last quarter's, the largest customer's revenue, and the Furniture
    promotion's discounts."""
    lo, hi = f"{d.C}-01-01", f"{d.C}-12-31"
    lines, rev, lst, disc, pbd = one(d, """
        SELECT COUNT(*), SUM(l.LineTotal), SUM(l.Quantity * i.ListPrice), SUM(l.Quantity * l.UnitPrice * l.Discount),
               SUM(l.Quantity * l.UnitPrice)
        FROM SalesInvoiceLine l JOIN SalesInvoice s USING (SalesInvoiceID) JOIN Item i USING (ItemID)
        WHERE s.InvoiceDate BETWEEN ? AND ?""", lo, hi)
    furn = one(d, "SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice s USING (SalesInvoiceID) "
                  "JOIN Item i USING (ItemID) WHERE i.ItemGroup = 'Furniture' AND s.InvoiceDate BETWEEN ? AND ?", lo, hi)[0]
    q4 = one(d, "SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice s USING (SalesInvoiceID) "
                "JOIN Item i USING (ItemID) WHERE i.ItemGroup = 'Furniture' AND s.InvoiceDate BETWEEN ? AND ?",
             f"{d.C}-10-01", hi)[0]
    top = one(d, "SELECT SUM(l.LineTotal) AS r FROM SalesInvoiceLine l JOIN SalesInvoice s USING (SalesInvoiceID) "
                 "GROUP BY s.CustomerID ORDER BY r DESC")[0]            # the largest customer over all the years
    pid = promotions(d)["val.promo.furniture_id"]
    pdisc = one(d, "SELECT SUM(Quantity * UnitPrice * Discount) FROM SalesInvoiceLine WHERE PromotionID = ?", pid)[0]
    nlines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    return {"val.invoice_lines.last_row": nlines + 1, "val.year.lines": lines, "val.year.revenue": rev, "val.year.list": lst, "val.year.discounts": disc,
            "val.year.price_before_discount": pbd, "val.year.adjusted_discount": pbd - rev,
            "val.furniture.revenue": furn, "val.furniture.q4_revenue": q4, "val.top_customer.revenue": top,
            "val.promo.furniture_discount": pdisc}


@group
def budget_page(d) -> dict:
    """Chapter 15's budget page: the operating-expense budget and actual of the report year, the flexed commission
    (6290 at the budget's rate on actual product revenue), the remaining variance after the classification effect,
    the budget lines with no cost center, and each cost center's budget and actual."""
    t2 = note(d, "ch15.t2")
    out = {"val.opex.budget": t2["opex"], "val.opex.actual": t2["actual"], "val.opex.flexed_commission": t2["flexed_com"],
           "val.opex.remaining": -t2["remaining"], "val.budget.lines_without_cost_center": note(d, "ch07.ex2")["blank_rows"]}
    for c in t2["centers"]:
        out[f"val.cost_center.budget.{c['name']}"] = c["budget"]
        out[f"val.cost_center.actual.{c['name']}"] = c["actual"]
    return out


@group
def hours_ratio(d) -> dict:
    """Chapters 10, 11 and 15: direct plus indirect hours per standard hour for each year, the trailing-twelve-month
    peak, the value at the month after the first full window, and the visual calculation's first value on an axis that
    starts then (a moving average over fewer months)."""
    t3 = note(d, "ch15.t3")
    out = {}
    for role, row in zip(("F", "P", "C"), t3["tests"]):
        out[f"val.hours_ratio.{role}"] = row["ratio"]
    ttm = dict((m, v) for m, v in t3["ttm"])
    out["val.ttm.peak"] = max(ttm.values())
    months = sorted(ttm)
    out["val.ttm.second_month"] = ttm[months[1]]
    out["val.ttm.visual_first"] = t3["visual"][0]
    return out


@group
def surge_and_cutoff(d) -> dict:
    """Chapter 12: the surge days of each year (every hourly manufacturing employee's hours the same), and the
    invoices posted in the year after their goods were delivered (count and SubTotal) for the first two years."""
    out = {}
    rows = d.q("""SELECT substr(WorkDate, 1, 4), COUNT(*) FROM (
                    SELECT tc.WorkDate FROM TimeClockEntry tc JOIN Employee e ON e.EmployeeID = tc.EmployeeID
                    JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID WHERE cc.CostCenterName = 'Manufacturing'
                    GROUP BY tc.WorkDate HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1 AND COUNT(*) > 1)
                  GROUP BY 1""")
    by = {int(y): n for y, n in rows}
    for role, y in (("F", d.F), ("P", d.P), ("C", d.C)):
        out[f"val.surge.days.{role}"] = by.get(y, 0)
    for role, y in (("F", d.F), ("P", d.P)):
        n, sub = one(d, """
            SELECT COUNT(*), ROUND(SUM(SubTotal), 2) FROM (
              SELECT s.SalesInvoiceID, s.SubTotal FROM SalesInvoice s
              JOIN GLEntry g ON g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID = s.SalesInvoiceID
                   AND g.SourceLineID IS NOT NULL
              JOIN SalesInvoiceLine l ON l.SalesInvoiceID = s.SalesInvoiceID
              JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment sh ON sh.ShipmentID = sl.ShipmentID
              WHERE g.FiscalYear = ? GROUP BY s.SalesInvoiceID HAVING MAX(sh.ShipmentDate) <= ?)""", y + 1, f"{y}-12-31")
        out[f"val.cutoff.{role}.invoices"] = n
        out[f"val.cutoff.{role}.amount"] = sub
    return out


@group
def audit_counts(d) -> dict:
    """Chapters 8, 12, 16: the journal entry and register tests (counts by test), the exception register (rows, open,
    January, entries with two or more flags), purchase orders and payroll registers, the opening entry's lines, the
    trial balance, the unsupported opening receivable, the payments of $50,000 or more, and the Production Manager."""
    t1, t2, t3 = note(d, "ch16.t1"), note(d, "ch16.t2"), note(d, "ch16.t3")
    out = {"val.je.entries": t1["n"], "val.je.opening_lines": t1["top"]["lines"], "val.exceptions.total": t2["n"],
           "val.exceptions.january": dict(t2["months"])["Jan"], "val.exceptions.open": t3["open"],
           "val.exceptions.dispositions": t3["n_disp"], "val.docs.multi_exception": t3["n_multi"],
           "val.po.orders": t2["po"]["n"], "val.pr.registers": t2["pr"]["n"], "val.po.docs_flagged": t2["po_docs"]}
    for process, rows in t2["tests"].items():
        for name, n in rows:
            out[f"val.test.{process}.{name}"] = n
    for s in t1["scores"]:
        out[f"val.je.score.{s['score']}"] = s["n"]
    out["val.je.score2plus"] = sum(s["n"] for s in t1["scores"] if s["score"] >= 2)
    out["val.tb.accounts"] = t3["tb_accounts"]
    out["val.tb.debits"] = t3["tb"]
    out["val.opening.receivables"] = note(d, "ch08.ex1")["opening"]
    out["val.payments.over_50k"] = d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE Amount >= 50000 AND PaymentDate <= ?",
                                         f"{d.C}-12-31")
    out["val.employee.production_manager"] = d.one(
        "SELECT EmployeeID FROM Employee WHERE JobTitle = 'Production Manager' ORDER BY EmployeeID")
    return out


@group
def other_counts(d) -> dict:
    """Chapter 11 and 12: the months with three pay dates; the purchase orders that fail two or more tests (self-approved,
    above the approver's limit, approved after termination); the invoices dated before their first shipment and
    posted in the year their goods were delivered."""
    three = len(d.q("SELECT strftime('%Y-%m', PayDate) FROM PayrollPeriod WHERE PayrollPeriodID IN "
                    "(SELECT PayrollPeriodID FROM PayrollRegister) GROUP BY 1 HAVING COUNT(*) = 3"))
    rows = d.q("""SELECT (po.CreatedByEmployeeID = po.ApprovedByEmployeeID), (po.OrderTotal > e.MaxApprovalAmount),
                         (e.TerminationDate IS NOT NULL AND po.OrderDate > e.TerminationDate)
                  FROM PurchaseOrder po JOIN Employee e ON e.EmployeeID = po.ApprovedByEmployeeID""")
    two = sum(1 for r in rows if sum(r) >= 2)
    before = d.one("""
        SELECT COUNT(*) FROM SalesInvoice s
        WHERE s.InvoiceDate < (SELECT MIN(sh.ShipmentDate) FROM Shipment sh WHERE sh.SalesOrderID = s.SalesOrderID)
          AND (SELECT g.FiscalYear FROM GLEntry g WHERE g.SourceDocumentType = 'SalesInvoice'
               AND g.SourceDocumentID = s.SalesInvoiceID LIMIT 1) <=
              CAST(substr((SELECT MAX(sh.ShipmentDate) FROM Shipment sh WHERE sh.SalesOrderID = s.SalesOrderID), 1, 4) AS INTEGER)""")
    return {"val.pay.three_date_months": three, "val.po.failing_two_tests": two,
            "val.invoice_before_shipment.count": before}


@group
def net_income(d) -> dict:
    """Chapter 14: net income of each fiscal year from the ledger (revenue and expense accounts, the year-end closes left
    out)."""
    out = {}
    for role, y in (("F", d.F), ("P", d.P), ("C", d.C)):
        out[f"val.net_income.{role}"] = one(d, f"SELECT ROUND(-SUM(g.Debit - g.Credit), 2) FROM GLEntry g "
                                               f"JOIN Account a USING (AccountID) WHERE g.FiscalYear = ? "
                                               f"AND a.AccountType IN ('Revenue', 'Expense') AND {d.no_closes()}", y)[0]
    return out


@group
def date_table(d) -> dict:
    """Chapter 14: the days of the Date table (the first day of F to the last day of N)."""
    import datetime as dt
    return {"val.date_table.days": (dt.date(d.N, 12, 31) - dt.date(d.F, 1, 1)).days + 1}


def compute(d) -> dict:
    """Every val.* key computable on this dataset; the failures are recorded in ERRORS."""
    ERRORS.clear()
    out: dict = {}
    for name, fn in GROUPS:
        try:
            out.update(fn(d))
        except Exception as exc:   # a dataset without what the text relies on
            ERRORS[name] = f"{type(exc).__name__}: {exc}"
    return out
