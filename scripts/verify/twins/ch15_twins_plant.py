"""SQL twins for Tutorials 15.1 and 15.3: promotions, and plant hours per standard hour."""
import sqlite3
from collections import defaultdict

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, db_uri  # noqa: E402
c = sqlite3.connect(db_uri(), uri=True)

# ---- plant ----
maxwd = c.execute("SELECT MAX(WorkDate) FROM LaborTimeEntry").fetchone()[0]
hrs = defaultdict(lambda: defaultdict(float))
for ym, lt, reg, ot in c.execute("""SELECT substr(WorkDate,1,7), LaborType, SUM(RegularHours), SUM(OvertimeHours)
        FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' GROUP BY 1,2"""):
    hrs[ym]["direct" if lt.startswith("Direct") else "indirect"] += reg + ot
    hrs[ym]["ot"] += ot
std = dict(c.execute("""SELECT substr(pc.CompletionDate,1,7), SUM(pcl.QuantityCompleted*i.StandardLaborHoursPerUnit)
        FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc ON pc.ProductionCompletionID=pcl.ProductionCompletionID
        JOIN Item i ON i.ItemID=pcl.ItemID WHERE pc.CompletionDate <= ? GROUP BY 1""", (maxwd,)).fetchall())
months = sorted(hrs)
print("last work date", maxwd, "months", months[0], months[-1], len(months))


def ttm(i, start=0):
    w = months[max(start, i - 11):i + 1]
    d = sum(hrs[m]["direct"] for m in w); ind = sum(hrs[m]["indirect"] for m in w)
    s = sum(std.get(m, 0) for m in w); ot = sum(hrs[m]["ot"] for m in w)
    return len(w), d / s, ind / s, (d + ind) / s, ot / (d + ind)


print("month  monthly  TTM(n, direct, indirect, total, otshare)  visual-calc on axis from 2025-01")
start25 = months.index("2025-01")
for i, m in enumerate(months):
    tot = hrs[m]["direct"] + hrs[m]["indirect"]
    n, d, ind, t, ots = ttm(i)
    vc = ttm(i, start25)[3] if i >= start25 else None
    flag = "" if n == 12 else " (partial)"
    print(f"  {m} {tot / std[m]:6.3f}  {n:2} {d:.3f} {ind:.3f} {t:.3f} {ots:.3f}{flag}   {'' if vc is None else f'{vc:.3f}'}")

print("2026 direct hours by work center (operation path):")
for r in c.execute("""SELECT COALESCE(wc.WorkCenterName,'(Blank)'), ROUND(SUM(l.RegularHours+l.OvertimeHours),1), COUNT(*)
        FROM LaborTimeEntry l LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID=l.WorkOrderOperationID
        LEFT JOIN WorkCenter wc ON wc.WorkCenterID=o.WorkCenterID
        WHERE l.LaborType='Direct Manufacturing' AND l.WorkDate LIKE '2026%' GROUP BY 1 ORDER BY 2 DESC"""):
    print("  ", r)
print("Manufacturing hours by work center, all years (incl. indirect):")
for r in c.execute("""SELECT COALESCE(wc.WorkCenterName,'(Blank)'), ROUND(SUM(l.RegularHours+l.OvertimeHours),1)
        FROM LaborTimeEntry l LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID=l.WorkOrderOperationID
        LEFT JOIN WorkCenter wc ON wc.WorkCenterID=o.WorkCenterID
        WHERE l.LaborType<>'NonManufacturing' GROUP BY 1 ORDER BY 2 DESC"""):
    print("  ", r)
print("Direct hours by work center by year (share):")
for y in ("2024", "2025", "2026"):
    rows = c.execute("""SELECT COALESCE(wc.WorkCenterName,'(Blank)'), SUM(l.RegularHours+l.OvertimeHours)
        FROM LaborTimeEntry l LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID=l.WorkOrderOperationID
        LEFT JOIN WorkCenter wc ON wc.WorkCenterID=o.WorkCenterID
        WHERE l.LaborType='Direct Manufacturing' AND l.WorkDate LIKE ? GROUP BY 1""", (y + "%",)).fetchall()
    tot = sum(r[1] for r in rows)
    print("  ", y, {k: f"{v / tot:.3f}" for k, v in rows})
print("time clock vs operation work center (direct):", c.execute("""SELECT COUNT(*), SUM(t.WorkCenterID <> o.WorkCenterID),
        SUM(t.WorkCenterID IS NULL) FROM LaborTimeEntry l JOIN WorkOrderOperation o ON o.WorkOrderOperationID=l.WorkOrderOperationID
        JOIN TimeClockEntry t ON t.TimeClockEntryID=l.TimeClockEntryID WHERE l.LaborType='Direct Manufacturing'""").fetchone())

# ---- promotions ----
print("Promotions:")
for r in c.execute("""SELECT p.PromotionID, p.PromotionName, p.ScopeType, p.DiscountPct, p.EffectiveStartDate, p.EffectiveEndDate,
        COUNT(l.SalesInvoiceLineID), ROUND(SUM(l.Quantity*l.UnitPrice*l.Discount),2), MIN(si.InvoiceDate), MAX(si.InvoiceDate),
        SUM(si.InvoiceDate > p.EffectiveEndDate)
        FROM PromotionProgram p LEFT JOIN SalesInvoiceLine l ON l.PromotionID=p.PromotionID
        LEFT JOIN SalesInvoice si ON si.SalesInvoiceID=l.SalesInvoiceID GROUP BY p.PromotionID"""):
    print("  ", r)
print("Promotion 8 by invoice month:", c.execute("""SELECT substr(si.InvoiceDate,1,7), COUNT(*), ROUND(SUM(l.Quantity*l.UnitPrice*l.Discount),2)
        FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID=l.SalesInvoiceID WHERE l.PromotionID=8 GROUP BY 1""").fetchall())
print("2026 discounts by promotion:", c.execute("""SELECT l.PromotionID, ROUND(SUM(l.Quantity*l.UnitPrice*l.Discount),2), COUNT(*)
        FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID=l.SalesInvoiceID WHERE si.InvoiceDate LIKE '2026%'
        GROUP BY 1""").fetchall())
r = c.execute("""SELECT SUM(l.Quantity*l.BaseListPrice), SUM(l.Quantity*l.UnitPrice), SUM(l.LineTotal), SUM(l.Quantity*l.UnitPrice*l.Discount)
        FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID=l.SalesInvoiceID WHERE si.InvoiceDate LIKE '2026%'""").fetchone()
print("2026 gross to net: list %.2f, before discount %.2f, revenue %.2f, discounts %.2f; steps %.2f %.2f" %
      (r[0], r[1], r[2], r[3], r[1] - r[0], r[2] - r[1]))
