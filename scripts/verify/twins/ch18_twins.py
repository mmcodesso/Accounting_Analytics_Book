"""Read-only twins for Chapter 18 ("Make, Buy, or Reprice"). Every value the chapter's instructor notes state is
computed here: SQL for the records, Python for the workbook's regressions, Goal Seek targets, Data Tables, and Solver."""
import sqlite3
import statistics as st
from collections import defaultdict

import numpy as np
from scipy.optimize import linprog

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, db_uri  # noqa: E402
c = sqlite3.connect(db_uri(), uri=True)
q = lambda s, p=(): c.execute(s, p).fetchall()
one = lambda s, p=(): c.execute(s, p).fetchone()
r2 = lambda x: round(x + 0.0, 2)


def hdr(t):
    print(f"\n=== {t}")


# ---- assumptions (tbl-18-02) -------------------------------------------------------------------------------
PRACTICAL = 0.80
RATE, BURDEN, PLAN_HOURS = 26.62, 0.1414, 1.18          # the Part III plan
WORKING_DAYS = 256
POS_HOURS = PRACTICAL * 8 * WORKING_DAYS                 # 1,638.4
SEVERANCE = 8 * 40 * RATE * (1 + BURDEN)
FLOOR = 0.40
FREIGHT = 0.03
QUOTE = {"FUR-BNH": (1450, 325, 18000), "FUR-NGT": (3200, 270, 22000), "FUR-SDB": (3800, 325, 25000),
         "FUR-TBL": (5000, 315, 30000), "LGT-SCN": (4600, 180, 15000), "TXT-PIL": (700, 220, 8000)}

ITEMS = {r[0]: dict(code=r[1], group=r[2], type=r[3], mode=r[4], std=r[5], lst=r[6], conv=r[7], stdh=r[8] or 0, routing=r[9],
                    active=r[10], fam=r[1][:7])
         for r in q("""SELECT ItemID, ItemCode, ItemGroup, ItemType, SupplyMode, StandardCost, ListPrice, StandardConversionCost,
             StandardLaborHoursPerUnit, RoutingID, IsActive FROM Item""")}
MFG = {i for i, v in ITEMS.items() if v["mode"] == "Manufactured"}
FAMS = sorted({ITEMS[i]["fam"] for i in MFG})

# ---- Requirement 1 ------------------------------------------------------------------------------------------
hdr("R1 families, 2026")
sold = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])     # by item: units, revenue, standard cost, list value
for iid, qty, lt, blp in q("""SELECT sil.ItemID, sil.Quantity, sil.LineTotal, sil.BaseListPrice FROM SalesInvoiceLine sil
        JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID WHERE si.InvoiceDate BETWEEN '2026-01-01' AND '2026-12-31'"""):
    s = sold[iid]; s[0] += qty; s[1] += lt; s[2] += qty * ITEMS[iid]["std"]; s[3] += qty * (blp or 0)
var = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0])  # by family: total, material, labor, overhead, closes
for iid, tv, mv, lv, ov in q("""SELECT wo.ItemID, woc.TotalVarianceAmount, woc.MaterialVarianceAmount, woc.DirectLaborVarianceAmount,
        woc.OverheadVarianceAmount FROM WorkOrderClose woc JOIN WorkOrder wo ON wo.WorkOrderID = woc.WorkOrderID
        WHERE woc.CloseDate BETWEEN '2026-01-01' AND '2026-12-31'"""):
    v = var[ITEMS[iid]["fam"]]; v[0] += tv; v[1] += mv; v[2] += lv; v[3] += ov; v[4] += 1
comp = defaultdict(float); comp_wo = defaultdict(set); comp_item = defaultdict(float)
mat_std_completed = 0.0
for wo, iid, qc, msc in q("""SELECT pc.WorkOrderID, pcl.ItemID, pcl.QuantityCompleted, pcl.ExtendedStandardMaterialCost
        FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        WHERE pc.CompletionDate BETWEEN '2026-01-01' AND '2026-12-31'"""):
    f = ITEMS[iid]["fam"]; comp[f] += qc; comp_wo[f].add(wo); comp_item[iid] += qc; mat_std_completed += msc
print("variance of 2026 closes", r2(sum(v[0] for v in var.values())), "| material", r2(sum(v[1] for v in var.values())),
      "labor", r2(sum(v[2] for v in var.values())), "overhead", r2(sum(v[3] for v in var.values())))
VPU = {f: var[f][0] / comp[f] for f in FAMS if comp[f]}
FAM = {}
grp = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
print(f"{'family':8} {'units':>8} {'revenue':>12} {'closes':>6} {'variance':>11} {'%std':>5} {'v/unit':>7} {'std%':>5} {'unit%':>6} {'year%':>6} {'purch%':>6}")
for f in FAMS:
    ids = [i for i in MFG if ITEMS[i]["fam"] == f and sold[i][0] > 0]
    u = sum(sold[i][0] for i in ids); r = sum(sold[i][1] for i in ids); sc = sum(sold[i][2] for i in ids); lst = sum(sold[i][3] for i in ids)
    if not u:
        print(f, "not sold in 2026"); continue
    vpu = VPU.get(f, 0)
    share = var[f][0] / (comp[f] * 0 + sum(comp_item[i] * ITEMS[i]["std"] for i in comp_item if ITEMS[i]["fam"] == f))
    pids = [i for i in ITEMS if ITEMS[i]["fam"] == f and ITEMS[i]["mode"] == "Purchased" and sold[i][0] > 0]
    pr = sum(sold[i][1] for i in pids); psc = sum(sold[i][2] for i in pids)
    FAM[f] = dict(units=u, rev=r, std=sc, lst=lst, vpu=vpu, ids=ids)
    print(f"{f:8} {u:8.1f} {r:12.2f} {var[f][4]:6} {var[f][0]:11.2f} {share*100:5.1f} {vpu:7.2f} {(1-sc/r)*100:5.1f} {(1-(sc+vpu*u)/r)*100:6.1f} "
          f"{(1-(sc+var[f][0])/r)*100:6.1f} {('%.1f' % ((1-psc/pr)*100)) if pr else 'none':>6}")
    g = grp[f[:3]]; g[0] += r; g[1] += sc; g[2] += vpu * u; g[3] += var[f][0]
for g, (r, sc, pv, v) in grp.items():
    print(g, "revenue", r2(r), "standard %.2f%% unit %.2f%% year %.2f%%" % ((1 - sc / r) * 100, (1 - (sc + pv) / r) * 100, (1 - (sc + v) / r) * 100), "variance", r2(v))
pur = defaultdict(lambda: [0.0, 0.0])
for iid, qty, uc in q("""SELECT pol.ItemID, pol.Quantity, pol.UnitCost FROM PurchaseOrderLine pol JOIN PurchaseOrder po ON po.PurchaseOrderID = pol.PurchaseOrderID
        WHERE po.OrderDate BETWEEN '2026-01-01' AND '2026-12-31'"""):
    if ITEMS[iid]["mode"] == "Purchased" and ITEMS[iid]["type"] == "Finished Good":
        pur[ITEMS[iid]["fam"]][0] += qty * uc; pur[ITEMS[iid]["fam"]][1] += qty * ITEMS[iid]["lst"]
print("purchased PO cost / list by family (quoted):", {f: round(pur[f][0] / pur[f][1], 3) for f in QUOTE if pur[f][1]})
print("tests: BaseListPrice <> ListPrice", one("SELECT COUNT(*) FROM SalesInvoiceLine sil JOIN Item i ON i.ItemID = sil.ItemID WHERE ABS(sil.BaseListPrice - i.ListPrice) > 0.004")[0],
      "| shipment std <> qty x std", one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Item i ON i.ItemID = sl.ItemID WHERE ABS(sl.ExtendedStandardCost - ROUND(sl.QuantityShipped * i.StandardCost, 2)) > 0.011")[0],
      "| completion std less qty x std (lines over 1 cent, largest)", one("SELECT SUM(ABS(pcl.ExtendedStandardTotalCost - pcl.QuantityCompleted * i.StandardCost) > 0.01), ROUND(MAX(ABS(pcl.ExtendedStandardTotalCost - pcl.QuantityCompleted * i.StandardCost)), 4) FROM ProductionCompletionLine pcl JOIN Item i ON i.ItemID = pcl.ItemID"),
      "| items sold in all three years", one("""SELECT COUNT(*) FROM (SELECT sil.ItemID FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID
          GROUP BY 1 HAVING COUNT(DISTINCT substr(si.InvoiceDate, 1, 4)) = 3)""")[0])
mv_rate = sum(v[1] for v in var.values()) / mat_std_completed
print("material variance rate", round(mv_rate, 5))

# ---- Requirement 2 ------------------------------------------------------------------------------------------
hdr("R2 the inputs to 1090, 2026")
for r in q("""SELECT prl.LineType, lte.LaborType, ROUND(SUM(prl.Hours), 1), ROUND(SUM(prl.Amount), 2) FROM PayrollRegisterLine prl
        JOIN PayrollRegister pr ON pr.PayrollRegisterID = prl.PayrollRegisterID JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID
        LEFT JOIN LaborTimeEntry lte ON lte.LaborTimeEntryID = prl.LaborTimeEntryID
        WHERE pr.CostCenterID = 4 AND pp.FiscalYear = 2026 AND prl.LineType NOT IN ('Benefits Deduction', 'Employee Tax Withholding') GROUP BY 1, 2"""):
    print(" ", r)
src = dict(q("""SELECT COALESCE(je.EntryType, g.SourceDocumentType), ROUND(SUM(g.Debit), 2) FROM GLEntry g LEFT JOIN JournalEntry je
        ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry'
        WHERE g.AccountID = 92 AND g.PostingDate BETWEEN '2026-01-01' AND '2026-12-31' AND g.Debit > 0
        AND g.SourceDocumentType <> 'WorkOrderClose' GROUP BY 1"""))
print("debits to 1090 by source", src, "total", r2(sum(src.values())))
rel = one("""SELECT SUM(pcl.ExtendedStandardDirectLaborCost), SUM(pcl.ExtendedStandardVariableOverheadCost), SUM(pcl.ExtendedStandardFixedOverheadCost),
        SUM(pcl.ExtendedStandardConversionCost), SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) FROM ProductionCompletionLine pcl
        JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID JOIN Item i ON i.ItemID = pcl.ItemID
        WHERE pc.CompletionDate BETWEEN '2026-01-01' AND '2026-12-31'""")
STDH = rel[4]
print("released at standard: labor", r2(rel[0]), "variable OH", r2(rel[1]), "fixed OH", r2(rel[2]), "conversion", r2(rel[3]), "| std hours", r2(STDH),
      "| per std hour: conversion", round(rel[3] / STDH, 2), "labor", round(rel[0] / STDH, 2), "overhead", round((rel[1] + rel[2]) / STDH, 2))
inputs = sum(src.values())
dl = 1253247.29 + 682821.11
print("inputs", r2(inputs), "| actual conversion per std hour", round(inputs / STDH, 2), "| actual overhead (inputs less direct earnings)", r2(inputs - dl),
      "per std hour", round((inputs - dl) / STDH, 2), "x applied", round((inputs - dl) / (rel[1] + rel[2]), 2))
std_m = defaultdict(float)
for m, h in q("""SELECT substr(pc.CompletionDate, 1, 7), SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) FROM ProductionCompletionLine pcl
        JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID JOIN Item i ON i.ItemID = pcl.ItemID GROUP BY 1"""):
    std_m[m] = h


def series(where):
    d = defaultdict(float)
    for m, v in q(f"""SELECT substr(g.PostingDate, 1, 7), SUM(g.Debit) FROM GLEntry g LEFT JOIN JournalEntry je ON je.JournalEntryID = g.SourceDocumentID
            AND g.SourceDocumentType = 'JournalEntry' WHERE g.AccountID = 92 AND {where} GROUP BY 1"""):
        d[m] = v
    return d


fo, pay, dep = series("je.EntryType = 'Factory Overhead'"), series("g.SourceDocumentType = 'PayrollSummary'"), series("je.EntryType = 'Depreciation'")
months = sorted(m for m in std_m if "2024-02" <= m <= "2026-12")
for name, y in (("factory overhead", fo), ("payroll", pay), ("depreciation", dep)):
    xs = [std_m[m] for m in months]; ys = [y[m] for m in months]
    lr = st.linear_regression(xs, ys); rr = st.correlation(xs, ys)
    print(f"  {name}: n {len(months)} slope {lr.slope:.2f} intercept {lr.intercept:,.0f} r {rr:.3f} R2 {rr*rr:.3f}")
m36 = sorted(m for m in std_m if "2024-01" <= m <= "2026-12")
print("  payroll with January 2024: r", round(st.correlation([std_m[m] for m in m36], [pay[m] for m in m36]), 3))
for y in ("2024", "2025", "2026"):
    app = one("""SELECT SUM(pcl.ExtendedStandardVariableOverheadCost + pcl.ExtendedStandardFixedOverheadCost) FROM ProductionCompletionLine pcl
        JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID WHERE pc.CompletionDate LIKE ?""", (y + "%",))[0]
    print("  factory overhead / applied", y, round(sum(v for m, v in fo.items() if m.startswith(y)) / app, 3))
print("  depreciation by month 2026", sorted({r2(v) for m, v in dep.items() if m.startswith("2026")}))

# ---- Requirement 3 ------------------------------------------------------------------------------------------
hdr("R3 activities and capacity, 2026")
RUN = dict(q("SELECT RoutingID, SUM(StandardRunHoursPerUnit) FROM RoutingOperation GROUP BY 1"))
SETUP = dict(q("SELECT RoutingID, SUM(StandardSetupHours) FROM RoutingOperation GROUP BY 1"))
WC = {r[0]: r[1] for r in q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter")}
RUN_WC = defaultdict(dict); SET_WC = defaultdict(dict)
for rid, wc, sh, rh in q("SELECT RoutingID, WorkCenterID, SUM(StandardSetupHours), SUM(StandardRunHoursPerUnit) FROM RoutingOperation GROUP BY 1, 2"):
    RUN_WC[rid][wc] = rh; SET_WC[rid][wc] = sh
issue_lines = defaultdict(int)
for iid, n in q("""SELECT wo.ItemID, COUNT(*) FROM MaterialIssueLine mil JOIN MaterialIssue mi ON mi.MaterialIssueID = mil.MaterialIssueID
        JOIN WorkOrder wo ON wo.WorkOrderID = mi.WorkOrderID WHERE mi.WorkOrderID IN (SELECT DISTINCT WorkOrderID FROM ProductionCompletion
        WHERE CompletionDate BETWEEN '2026-01-01' AND '2026-12-31') GROUP BY 1"""):
    issue_lines[ITEMS[iid]["fam"]] += n
BATCH = {f: comp[f] / len(comp_wo[f]) for f in list(comp) if comp_wo.get(f)}
gstat = defaultdict(lambda: [0.0, 0, 0.0, 0.0, 0])
for f in sorted(BATCH):
    wos = comp_wo[f]
    setup_h = sum(SETUP[r[0]] for r in q(f"SELECT RoutingID FROM WorkOrder WHERE WorkOrderID IN ({','.join(map(str, wos))})"))
    g = gstat[f[:3]]; g[0] += comp[f]; g[1] += len(wos); g[2] += setup_h; g[4] += issue_lines[f]
for g, (u, n, sh, _, il) in gstat.items():
    print(g, "units", round(u, 1), "work orders", n, "batch", round(u / n, 1), "setup per 1,000 units", round(sh / u * 1000, 1), "issue lines per 1,000", round(il / u * 1000, 1))
avail = dict(q("SELECT WorkCenterID, SUM(AvailableHours) FROM WorkCenterCalendar WHERE CalendarDate BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY 1"))
used_wc = defaultdict(float)
for wo, rid, qc in q("""SELECT pc.WorkOrderID, wo.RoutingID, SUM(pcl.QuantityCompleted) FROM ProductionCompletionLine pcl
        JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID JOIN WorkOrder wo ON wo.WorkOrderID = pc.WorkOrderID
        WHERE pc.CompletionDate BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY 1, 2"""):
    for wc, rh in RUN_WC[rid].items():
        used_wc[wc] += qc * rh + SET_WC[rid][wc]
AVAIL = sum(avail.values()); PRACT = AVAIL * PRACTICAL; USED = sum(used_wc.values())
for wc in sorted(avail):
    print(f"  {WC[wc]:32} available {avail[wc]:10.2f} practical {avail[wc]*PRACTICAL:10.2f} used {used_wc[wc]:9.1f} "
          f"{used_wc[wc]/avail[wc]*100:5.1f}% / {used_wc[wc]/avail[wc]/PRACTICAL*100:5.1f}%")
print("  plant", r2(AVAIL), r2(PRACT), round(USED, 1), round(USED / PRACT * 100, 1), "| setup", r2(sum(SETUP[r[0]] for r in q(
    "SELECT RoutingID FROM WorkOrder WHERE WorkOrderID IN (SELECT DISTINCT WorkOrderID FROM ProductionCompletion WHERE CompletionDate LIKE '2026%')"))))

# ---- Requirement 4 ------------------------------------------------------------------------------------------
hdr("R4 time-driven costs")
pc_ = {r[0]: r[1:] for r in q("""SELECT e.PayClass, SUM(pr.GrossPay), SUM(pr.EmployerPayrollTax), SUM(pr.EmployerBenefits), COUNT(DISTINCT pr.EmployeeID)
        FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID JOIN Employee e ON e.EmployeeID = pr.EmployeeID
        WHERE pr.CostCenterID = 4 AND pp.FiscalYear = 2026 GROUP BY 1""")}
CREW = sum(pc_["Hourly"][:3]); SAL = sum(pc_["Salary"][:3]); DEP = 303666.63
COMMITTED = CREW + SAL + DEP
TD, CREW_RATE, FO_RATE = COMMITTED / PRACT, CREW / PRACT, 1308869.06 / STDH
print("crew", r2(CREW), pc_["Hourly"], "| salaried", r2(SAL), pc_["Salary"], "| committed", r2(COMMITTED))
print("rate", round(TD, 4), "crew", round(CREW_RATE, 4), "supervision and equipment", round(TD - CREW_RATE, 4), "| factory OH per std hour", round(FO_RATE, 4))
print("used conversion", r2(USED * TD + 1308869.06), "unused", r2((PRACT - USED) * TD), "hours", round(PRACT - USED, 1),
      "crew part", r2((PRACT - USED) * CREW_RATE), "| total", r2(USED * TD + 1308869.06 + (PRACT - USED) * TD))


def time_per_unit(i):
    return RUN[ITEMS[i]["routing"]] + SETUP[ITEMS[i]["routing"]] / BATCH[ITEMS[i]["fam"]]


def costs(i, td_rate=TD):
    it = ITEMS[i]; mat = (it["std"] - it["conv"]) * (1 + mv_rate)
    return dict(mat=mat, std=it["std"], absorp=it["std"] + VPU.get(it["fam"], 0), td=mat + FO_RATE * it["stdh"] + td_rate * time_per_unit(i),
                kept=mat + FO_RATE * it["stdh"], time=time_per_unit(i))


UC = {}
print(f"{'family':8} {'price':>7} {'std':>7} {'absorp':>7} {'TD':>7} {'TD m%':>6} {'kept':>7} {'reduced':>8} {'time':>6}")
for f in sorted(FAM):
    ids = FAM[f]["ids"]; u = FAM[f]["units"]
    w = {k: sum(sold[i][0] * costs(i)[k] for i in ids) / u for k in ("std", "absorp", "td", "kept", "time", "mat")}
    w["price"] = FAM[f]["rev"] / u; w["reduced"] = w["kept"] + CREW_RATE * w["time"]
    UC[f] = w
    print(f"{f:8} {w['price']:7.2f} {w['std']:7.2f} {w['absorp']:7.2f} {w['td']:7.2f} {(1-w['td']/w['price'])*100:6.1f} {w['kept']:7.2f} {w['reduced']:8.2f} {w['time']:6.3f}")
for g in ("FUR", "LGT", "TXT"):
    r = sum(FAM[f]["rev"] for f in FAM if f[:3] == g); cst = sum(UC[f]["td"] * FAM[f]["units"] for f in FAM if f[:3] == g)
    print(" group TD margin", g, round((1 - cst / r) * 100, 2))
for share in (0.75, 0.80, 0.85, 0.90):
    pr = AVAIL * share; rate = COMMITTED / pr
    tbl = sum(sold[i][0] * costs(i, rate)["td"] for i in FAM["FUR-TBL"]["ids"]) / FAM["FUR-TBL"]["units"]
    print(f"  data table {share:.0%}: rate {rate:.2f} unused {(pr-USED)*rate:,.0f} FUR-TBL {tbl:.2f}")

# ---- Requirement 5 ------------------------------------------------------------------------------------------
hdr("R5 the explorer's totals (finished goods sold in 2026, Services excluded)")
fg = [i for i in sold if ITEMS[i]["type"] == "Finished Good" and sold[i][0] > 0]
rev = sum(sold[i][1] for i in fg)
view = defaultdict(float); item_m = {}
for i in fg:
    u = sold[i][0]
    if i in MFG:
        cc = costs(i); vals = dict(std=cc["std"], absorp=cc["absorp"], td=cc["td"])
    else:
        vals = dict(std=ITEMS[i]["std"], absorp=ITEMS[i]["std"], td=ITEMS[i]["std"])
    for k, v in vals.items():
        view[k] += u * v
    item_m[i] = {k: sold[i][1] - u * v for k, v in vals.items()}
print("items", len(fg), "revenue", r2(rev), "| margin std", r2(rev - view["std"]), "absorption", r2(rev - view["absorp"]), "time-driven", r2(rev - view["td"]),
      "TD less unused", r2(rev - view["td"] - (PRACT - USED) * TD), "year (std less 5080)", r2(rev - view["std"] - 2265636.88))
for k in ("std", "absorp", "td"):
    ms = sorted((m[k] for m in item_m.values()), reverse=True); top = ms[: round(len(ms) * 0.2)]
    low = min(item_m, key=lambda i: item_m[i][k] / sold[i][1])
    print(f"  {k}: top 20% of items ({len(top)}) earn {sum(top)/sum(ms)*100:.1f}%; negative items {sum(1 for m in ms if m < 0)}; lowest {ITEMS[low]['code']} {item_m[low][k]/sold[low][1]*100:.1f}%")

# ---- Requirement 6 ------------------------------------------------------------------------------------------
hdr("R6 make or buy")
ann = {}
for f, (vol, price, tooling) in QUOTE.items():
    w = UC[f]; u = FAM[f]["units"]; dq = price * (1 + FREIGHT)
    ann[f] = dict(kept=(w["kept"] - dq) * u, red=(w["reduced"] - dq) * u, absorp=(w["absorp"] - dq) * u)
    print(f"{f}: kept {w['kept']:.2f} reduced {w['reduced']:.2f} delivered {dq:.2f} | per year absorption {ann[f]['absorp']:+,.0f} kept {ann[f]['kept']:+,.0f} "
          f"reduced {ann[f]['red']:+,.0f} | break-even quote {w['kept']/(1+FREIGHT):.2f} / {w['reduced']/(1+FREIGHT):.2f} | delivered margin {(1-dq/w['price'])*100:.1f}%")
buy = ["FUR-BNH", "FUR-NGT", "FUR-TBL"]
gain = sum(ann[f]["red"] for f in buy); hours = sum(UC[f]["time"] * FAM[f]["units"] for f in buy); pos = hours / POS_HOURS
tool = sum(QUOTE[f][2] for f in buy)
print("buy", buy, "gain", round(gain), "| hours freed (sales basis)", round(hours), "positions", round(pos, 2), "severance", round(SEVERANCE, 2), round(pos * SEVERANCE),
      "tooling", tool, "two-year net", round(2 * gain - pos * SEVERANCE - tool), "| crew kept", round(sum(ann[f]["kept"] for f in buy)))
print("standard material of the three families (2026 completions)", r2(sum(comp_item[i] * (ITEMS[i]["std"] - ITEMS[i]["conv"]) for i in comp_item if ITEMS[i]["fam"] in buy)))
for share in (0.0, 0.5, 1.0):
    for adj in (-0.10, 0.0, 0.10):
        tot = sum(((UC[f]["kept"] + share * CREW_RATE * UC[f]["time"]) - QUOTE[f][1] * (1 + adj) * (1 + FREIGHT)) * FAM[f]["units"] for f in buy)
        print(f"  two-way: crew removed {share:.0%}, quote {adj:+.0%}: {tot:+,.0f}")

# ---- Requirement 7 ------------------------------------------------------------------------------------------
hdr("R7 capacity")
freed = defaultdict(float)
for wo, rid, qc, iid in q("""SELECT pc.WorkOrderID, wo.RoutingID, SUM(pcl.QuantityCompleted), wo.ItemID FROM ProductionCompletionLine pcl
        JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID JOIN WorkOrder wo ON wo.WorkOrderID = pc.WorkOrderID
        WHERE pc.CompletionDate BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY 1, 2"""):
    if ITEMS[iid]["fam"] in buy:
        for wc, rh in RUN_WC[rid].items():
            freed[wc] += qc * rh + SET_WC[rid][wc]
print("freed by work center (production basis)", {WC[k]: round(v) for k, v in freed.items()}, "total", round(sum(freed.values())),
      "| plant use after", round((USED - sum(freed.values())) / PRACT * 100, 1))
print("unused hours", round(PRACT - USED, 1), "positions", round((PRACT - USED) / POS_HOURS, 2))
sup = sum(UC[f]["time"] * FAM[f]["units"] for f in buy) * (TD - CREW_RATE)
print("supervision and equipment carried by the three families", round(sup))
# sales basis load per work center and the LP
fams = sorted(FAM)
load = {f: defaultdict(float) for f in fams}
for f in fams:
    for i in FAM[f]["ids"]:
        rid = ITEMS[i]["routing"]
        for wc, rh in RUN_WC[rid].items():
            load[f][wc] += sold[i][0] * (rh + SET_WC[rid][wc] / BATCH[f])
wcs = sorted(avail)
print("practical / used (sales basis)", {WC[w]: round(avail[w] * PRACTICAL / sum(load[f][w] for f in fams), 3) for w in wcs})
for growth in (1.4, 1.5):
    qf = [f for f in fams if f in QUOTE]
    cvec = [((QUOTE[f][1] * (1 + FREIGHT)) - UC[f]["kept"]) for f in qf]           # extra cost per unit bought, crew kept
    A, b = [], []
    for w in wcs:
        tot = sum(load[f][w] * growth for f in fams)
        A.append([-load[f][w] / FAM[f]["units"] for f in qf]); b.append(avail[w] * PRACTICAL - tot)
    bounds = [(0, FAM[f]["units"] * growth) for f in qf]
    res = linprog(cvec, A_ub=A, b_ub=b, bounds=bounds, method="highs")
    slack = np.array(b) - np.array(A) @ res.x
    duals = res.ineqlin.marginals
    print(f"  growth {growth}: status {res.status} cost {res.fun:,.0f}", {qf[k]: round(v) for k, v in enumerate(res.x) if v > 0.5},
          "binding", {WC[wcs[k]]: round(-duals[k], 2) for k in range(len(wcs)) if abs(slack[k]) < 1e-6})

# ---- Requirement 8 ------------------------------------------------------------------------------------------
hdr("R8 reprice")
total = 0
for f in sorted(UC):
    w = UC[f]
    if 1 - w["td"] / w["price"] < FLOOR:
        newp = w["td"] / (1 - FLOOR); inc = newp / w["price"] - 1
        cm = w["price"] - w["kept"]; loss = 1 - cm / (cm + (newp - w["price"]))
        total += (newp - w["price"]) * FAM[f]["units"]
        print(f"  {f}: +{inc*100:.2f}% to {newp:.2f}; volume loss absorbed {loss*100:.1f}%")
print("  revenue if volume holds", round(total))

# ---- Requirement 9 ------------------------------------------------------------------------------------------
hdr("R9 standards and the July statements")
PLAN_STDH = 68912.79
lab = RATE * (1 + BURDEN); sal_plan = 263191.24 * (1 + BURDEN); dep27 = 293499.96
comp9 = dict(direct=lab, variable=FO_RATE, indirect=(PLAN_HOURS - 1) * lab, supervision=sal_plan / PLAN_STDH, depreciation=dep27 / PLAN_STDH)
NEW = sum(comp9.values())
print({k: round(v, 4) for k, v in comp9.items()}, "rate", round(NEW, 4), "| at 1.0 hours", round(NEW - comp9["indirect"], 4),
      "| current", round(rel[3] / STDH, 2), "| time-driven per std hour", round(FO_RATE + TD * USED / STDH, 2), "| 2026 actual", round(inputs / STDH, 2))
for f in QUOTE:
    ids = FAM[f]["ids"]; u = FAM[f]["units"]
    newc = sum(sold[i][0] * ((ITEMS[i]["std"] - ITEMS[i]["conv"]) + NEW * ITEMS[i]["stdh"]) for i in ids) / u
    print(f"  revised standard {f}: {newc:.2f} (time-driven {UC[f]['td']:.2f})")
reval = {}
for asof in ("2024-12-31", "2025-12-31", "2026-12-31"):
    net = defaultdict(float)
    for iid, qc in q("SELECT pcl.ItemID, SUM(pcl.QuantityCompleted) FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID WHERE pc.CompletionDate <= ? GROUP BY 1", (asof,)):
        net[iid] += qc
    for iid, qs in q("SELECT sl.ItemID, SUM(sl.QuantityShipped) FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE s.ShipmentDate <= ? GROUP BY 1", (asof,)):
        net[iid] -= qs
    for iid, qr in q("SELECT srl.ItemID, SUM(srl.QuantityReturned) FROM SalesReturnLine srl JOIN SalesReturn sr ON sr.SalesReturnID = srl.SalesReturnID WHERE sr.ReturnDate <= ? GROUP BY 1", (asof,)):
        net[iid] += qr
    pos_ = {i: u for i, u in net.items() if i in MFG and u > 0}
    neg = {ITEMS[i]["code"]: round(u, 1) for i, u in net.items() if i in MFG and u < -0.05}
    sh = sum(u * ITEMS[i]["stdh"] for i, u in pos_.items()); cv = sum(u * ITEMS[i]["conv"] for i, u in pos_.items())
    sv = sum(u * ITEMS[i]["std"] for i, u in pos_.items())
    reval[asof] = dict(plan=sh * NEW - cv, one=sh * (NEW - comp9["indirect"]) - cv, td=sh * (FO_RATE + TD * USED / STDH) - cv, actual=sh * inputs / STDH - cv)
    print(f"  {asof}: units {sum(pos_.values()):,.1f} at standard {sv:,.2f} std hours {sh:,.1f} conversion {cv:,.2f} ({cv/sh:.2f}) | "
          + " ".join(f"{k} {v:+,.0f}" for k, v in reval[asof].items()), "| negative", neg)
for k in ("plan", "one"):
    a, b_, c_ = (reval[d][k] for d in ("2024-12-31", "2025-12-31", "2026-12-31"))
    print(f"  effect on the July statements ({k}): retained earnings 1 Jan 2025 {a:+,.0f}; 2025 income {b_-a:+,.0f}; 2026 income {c_-b_:+,.0f}; "
          f"balance 2025 {b_:+,.0f}, 2026 {c_:+,.0f} against materiality 256,717.74 / 225,180.56")
print("  1040 at 2026", one("SELECT ROUND(SUM(Debit - Credit), 2) FROM GLEntry WHERE AccountID = 5 AND PostingDate <= '2026-12-31'")[0], "opening", 4111795.76)

# ---- exports for the CR18 reference model ----------------------------------------------------------------------
import csv
with open(REFERENCE_MODELS / "cr18_itemcosts.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["ItemID", "ItemCode", "Family", "ItemGroup", "SupplyMode", "StandardCost", "AbsorptionCost", "TimeDrivenCost"])
    for i, it in sorted(ITEMS.items()):
        if it["type"] != "Finished Good":
            continue
        if i in MFG and it["fam"] in BATCH and it["routing"] in RUN:
            cc = costs(i); vals = (cc["std"], cc["absorp"], cc["td"])
        else:
            vals = (it["std"], it["std"], it["std"])
        w.writerow([i, it["code"], it["fam"], it["group"], it["mode"]] + [f"{v:.6f}" for v in vals])
with open(REFERENCE_MODELS / "cr18_sales.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["SalesInvoiceLineID", "ItemID", "InvoiceDate", "Quantity", "LineTotal"])
    for row in q("""SELECT sil.SalesInvoiceLineID, sil.ItemID, si.InvoiceDate, sil.Quantity, sil.LineTotal FROM SalesInvoiceLine sil
            JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID"""):
        w.writerow(row)
print("\nwrote cr18_itemcosts.csv and cr18_sales.csv")
