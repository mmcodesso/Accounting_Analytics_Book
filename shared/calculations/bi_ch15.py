"""Public Chapter 15 tutorial calculations, shared by book figures and slides.

The caller supplies a read-only SQLite connection. No files are opened or modified.
"""
from __future__ import annotations
import sqlite3
import datetime as dt
from collections import Counter, defaultdict
from shared.calculations.excel_analysis import _access

NOCLOSE = ("LEFT JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
           "WHERE COALESCE(j.EntryType, '') NOT LIKE 'Year-End Close%'")

def gross_to_net(db: sqlite3.Connection) -> tuple[float, float, float]:
    """List amount, price before discount, and revenue of fiscal 2026's invoice lines."""
    q, one, require_columns = _access(db)
    require_columns("SalesInvoiceLine", ["Quantity", "BaseListPrice", "UnitPrice", "LineTotal", "PromotionID"])
    return one("SELECT SUM(l.Quantity * l.BaseListPrice), SUM(l.Quantity * l.UnitPrice), SUM(l.LineTotal) "
               "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
               "WHERE si.InvoiceDate BETWEEN '2026-01-01' AND '2026-12-31'")

def promotion_discounts(db: sqlite3.Connection) -> list[tuple[str, float, int]]:
    q, one, require_columns = _access(db)
    require_columns("PromotionProgram", ["PromotionID", "PromotionName", "ScopeType", "DiscountPct",
                                         "EffectiveStartDate", "EffectiveEndDate"])
    return q("SELECT p.PromotionName, SUM(l.Quantity * l.UnitPrice * l.Discount), COUNT(*) "
             "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
             "JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
             "WHERE si.InvoiceDate BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY 1 ORDER BY 2 DESC")

def promotion_by_month(db: sqlite3.Connection, name: str) -> list[tuple[str, float, int]]:
    q, one, require_columns = _access(db)
    return q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.Quantity * l.UnitPrice * l.Discount), COUNT(*) "
             "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
             "JOIN PromotionProgram p ON p.PromotionID = l.PromotionID WHERE p.PromotionName = ? "
             "GROUP BY 1 ORDER BY 1", name)

def budget_data(db: sqlite3.Connection) -> dict:
    q, one, require_columns = _access(db)
    require_columns("BudgetLine", ["FiscalYear", "Month", "AccountID", "CostCenterID", "BudgetAmount",
                                   "BudgetCategory"])
    bud, act = defaultdict(float), defaultdict(float)
    bud_dep, act_dep, bud_com = defaultdict(float), defaultdict(float), defaultdict(float)
    for cc, an, m, amt in q("SELECT COALESCE(cc.CostCenterName, '(Blank)'), a.AccountNumber, b.Month, "
                            "SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
                            "LEFT JOIN CostCenter cc ON cc.CostCenterID = b.CostCenterID WHERE b.FiscalYear = 2026 "
                            "AND b.BudgetCategory <> 'Balance Sheet' AND a.AccountSubType = 'Operating Expense' "
                            "GROUP BY 1, 2, 3"):
        bud[cc] += amt
        bud[("month", m)] += amt
        if an == 6130:
            bud_dep[cc] += amt
        if an == 6290:
            bud_com[cc] += amt
            bud_com[("month", m)] += amt
    for cc, an, m, amt in q("SELECT COALESCE(cc.CostCenterName, '(Blank)'), a.AccountNumber, "
                            "CAST(substr(g.PostingDate, 6, 2) AS INT), SUM(g.Debit - g.Credit) FROM GLEntry g "
                            "JOIN Account a ON a.AccountID = g.AccountID LEFT JOIN CostCenter cc "
                            f"ON cc.CostCenterID = g.CostCenterID {NOCLOSE} AND g.FiscalYear = 2026 "
                            "AND a.AccountSubType = 'Operating Expense' GROUP BY 1, 2, 3"):
        act[cc] += amt
        act[("month", m)] += amt
        if an == 6130:
            act_dep[cc] += amt
    rev_budget = dict(q("SELECT b.Month, SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a "
                        "ON a.AccountID = b.AccountID WHERE b.FiscalYear = 2026 "
                        "AND a.AccountNumber IN (4010, 4020, 4030, 4040) GROUP BY 1"))
    product_rev = dict(q("SELECT CAST(substr(si.InvoiceDate, 6, 2) AS INT), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                         "JOIN SalesInvoice si USING (SalesInvoiceID) JOIN Item i USING (ItemID) "
                         "WHERE si.InvoiceDate BETWEEN '2026-01-01' AND '2026-12-31' AND i.ItemGroup <> 'Services' "
                         "GROUP BY 1"))
    flexed_com = {m: bud_com[("month", m)] / rev_budget[m] * product_rev[m] for m in range(1, 13)}
    centers = sorted(k for k in set(bud) | set(act) if isinstance(k, str))
    rows = {}
    for cc in centers:
        flexed = bud[cc] - bud_com[cc] + (sum(flexed_com.values()) if bud_com[cc] else 0)
        variance = act[cc] - bud[cc]
        volume = flexed - bud[cc]
        classification = act_dep[cc] - bud_dep[cc] if (act_dep[cc] or bud_dep[cc]) else None
        remaining = variance - volume - (classification or 0)
        rows[cc] = dict(budget=bud[cc], actual=act[cc], variance=variance, flexed=flexed, volume=volume,
                        classification=classification, remaining=remaining)
    monthly = []
    for m in range(1, 13):
        flexed_m = bud[("month", m)] - bud_com[("month", m)] + flexed_com[m]
        monthly.append(act[("month", m)] - flexed_m)
    data = dict(rows=rows, centers=centers, monthly=monthly, flexed_commission=sum(flexed_com.values()))
    total_b = sum(r["budget"] for r in rows.values())
    total_a = sum(r["actual"] for r in rows.values())
    assert abs(total_b - 8289648.80) < 0.01 and abs(total_a - 6471696.58) < 0.01, (total_b, total_a)
    assert abs(data["flexed_commission"] - 621780.04) < 0.02, data["flexed_commission"]
    assert abs(sum(r["classification"] or 0 for r in rows.values())) < 0.01, "classification nets to zero"
    assert abs(sum(monthly) + 174758.96) < 0.05, sum(monthly)
    return data

def plant_months(db: sqlite3.Connection) -> dict:
    q, one, require_columns = _access(db)
    require_columns("LaborTimeEntry", ["WorkDate", "LaborType", "RegularHours", "OvertimeHours", "EmployeeID",
                                       "WorkOrderOperationID"])
    require_columns("Item", ["StandardLaborHoursPerUnit"])
    last = one("SELECT MAX(WorkDate) FROM LaborTimeEntry")[0]
    hours = defaultdict(float)
    for ym, h in q("SELECT substr(WorkDate, 1, 7), SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry "
                   "WHERE LaborType <> 'NonManufacturing' GROUP BY 1"):
        hours[ym] = h
    std = dict(q("SELECT substr(pc.CompletionDate, 1, 7), SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) "
                 "FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc USING (ProductionCompletionID) "
                 "JOIN Item i ON i.ItemID = pcl.ItemID WHERE pc.CompletionDate <= ? GROUP BY 1", last))
    months = sorted(hours)
    assert months[0] == "2024-01" and months[-1] == "2026-12" and last == "2026-12-11"
    return dict(months=months, hours=hours, std=std)

def ttm(db: sqlite3.Connection, month: str, first: str = "2024-01") -> float | None:
    """The trailing ratio over the twelve months ending with month, using only months from first
    on: the measure when first is the start of the data, the visual calculation when it is the
    start of a filtered axis."""
    q, one, require_columns = _access(db)
    p = plant_months(db)
    ms = [m for m in p["months"] if first <= m <= month][-12:]
    return sum(p["hours"][m] for m in ms) / sum(p["std"].get(m, 0) for m in ms)
