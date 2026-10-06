"""Make Buy Reprice.xlsx: the Excel part of the solution to the Chapter 18 capstone case ("Make, Buy, or Reprice").

The case splits the work by tool (tbl-18-03). MakeBuy.sql returns the family results, the inputs to 1090, the
activities, and the capacity, and hands them to Excel by Copy with Headers; the workbook holds the assumptions, the cost
behavior tests, the three costs, make or buy, capacity, prices, and standards, and hands Power BI a Table of item costs.
The solution follows that split:

- the results the case assigns to MakeBuy.sql are pasted as values, each block an Excel Table whose first cell carries a
  note naming the query's purpose (the query is run read-only on CharlesRiver.sqlite when the solution is built, and its
  text is kept in QUERIES below, so the SQL solution can supply the same query);
- the item master, the routings, and the fiscal-year sales by item, which the workbook's own Table of item costs needs,
  come from CharlesRiver.xlsx through Power Query and refresh;
- everything else is a formula over those inputs and the Assumptions sheet, where the quote (tbl-18-01) and the
  controller's assumptions (tbl-18-02) are typed in blue as the chapter gives them.

Three outputs cannot be produced live, and each is labeled in a cell note: the Goal Seek results (break-even quotes and
target prices, left in their changing cells as Goal Seek leaves them, each beside its closed form), and Solver's optimum
and Sensitivity reports for the optional growth test of Requirement 7 (computed by the bounded-variable simplex of
ex07.py, the method of Solver's Simplex LP, written into the variable cells, with the model saved in Solver's hidden
worksheet names so Data > Solver opens it ready to solve).

Every value the instructor notes state is checked on the Solution Notes worksheet with a live formula against a value
computed here, independently of Excel, from CharlesRiver.sqlite (read-only): `model` mirrors the twin
scripts/verify/twins/ch18_twins.py and facts/notes/ch18.py in plain Python (row by row, as the twin does, where the
pasted blocks come from GROUP BY queries).
"""

from __future__ import annotations

import sqlite3
import statistics as st
from collections import defaultdict
from datetime import date

from paths import db_uri
from xlbuild import pq, xl
from xlbuild.analysis import formulas
from xlbuild.ex07 import SOLVER_DEFAULTS, col, model_answer, sensitivity, series, solve_lp, write_report
from xlbuild.solutions import COUNT, MONEY, ExerciseBuild

NOTES = "Solution Notes"

# --- book constants: tbl-18-01 (a hypothetical quote) and tbl-18-02 (the controller's assumptions) -------------------
QUOTE = {"FUR-BNH": ("Benches", 1450, 325, 18000, 8), "FUR-NGT": ("Nightstands", 3200, 270, 22000, 8),
         "FUR-SDB": ("Sideboards", 3800, 325, 25000, 8), "FUR-TBL": ("Dining tables", 5000, 315, 30000, 8),
         "LGT-SCN": ("Wall sconces", 4600, 180, 15000, 6), "TXT-PIL": ("Pillow covers", 700, 220, 8000, 6)}
FREIGHT = 0.03                  # inbound freight, a share of price (the purchasing manager's estimate)
MINIMUM = 0.80                  # Charles River buys at least 80% of the quoted volume of each family it chooses
DEFECTS = 0.015                 # the supplier credits defects above 1.5% of units
PAYMENT_DAYS = 45
PRICE_YEARS = 2                 # prices fixed for 2028 and 2029
PRACTICAL = 0.80                # practical capacity, a share of the available hours in WorkCenterCalendar
RATE, BURDEN = 26.62, 0.1414    # straight-time labor rate and burden
PLAN_HOURS, INDIRECT = 1.18, 0.18   # hours per standard hour at plan, of which indirect
PLAN_VOLUME = 68912.79          # the plan volume, the normal capacity (standard hours a year)
PLAN_SALARIES = 263191.24       # salaried production staff at plan, before burden
PLAN_DEPRECIATION = 293499.96   # depreciation at plan
DAY_HOURS = 8                   # a position's day
SEVERANCE_WEEKS, WEEK_HOURS = 8, 40
MATERIALITY = 0.05              # of income before income taxes as recorded
FLOOR = 0.40                    # gross margin floor on time-driven cost
GROWTH = (0.40, 0.50)           # the optional demand-growth tests
DATA_TABLE = (0.75, 0.80, 0.85, 0.90)   # Requirement 4's Data Table of practical capacity
TWO_WAY_CREW = (0.0, 0.5, 1.0)          # Requirement 6's two-way Data Table: share of freed crew time removed
TWO_WAY_QUOTE = (-0.10, 0.0, 0.10)      # ... and the quote, 10% either side
TOP_SHARE = 0.20
EXAMPLE = "FUR-TBL"             # the family Requirement 4's Data Table follows (the quote's largest volume)
MATERIALS = ("Raw Materials", "Packaging")
SIX = 6                         # the Part IV case's raw materials that carry the build


def short(family: str) -> str:
    return family[4:]


def wc_short(name: str) -> str:
    """'Finishing and Test Work Center' -> 'Finishing', 'Quality Assurance Work Center' -> 'QA'."""
    base = name.removesuffix(" Work Center").split(" and ")[0]
    words_ = base.split()
    return base if len(words_) == 1 else "".join(w[0] for w in words_)


# --- data (read-only) -----------------------------------------------------------------------------------------------

class Data:
    """The dataset, read-only, with its fiscal window: F, P, C (the base year), and N = C + 1."""

    def __init__(self, year: int):
        self.con = sqlite3.connect(db_uri(), uri=True)
        self.F = self.one("SELECT MIN(FiscalYear) FROM GLEntry")
        self.C = self.one("SELECT MAX(FiscalYear) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice'")
        assert self.C == year, f"the base year is {self.C}, the build's report year {year}"
        self.P, self.N = self.C - 1, self.C + 1
        self.years = list(range(self.F, self.C + 1))
        self.closes = [r[0] for r in self.q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' "
                                            "ORDER BY PostingDate, EntryNumber")]
        self.first, self.last = f"{self.C}-01-01", f"{self.C}-12-31"

    def q(self, sql: str, *args):
        return self.con.execute(sql, args).fetchall()

    def one(self, sql: str, *args):
        return self.con.execute(sql, args).fetchone()[0]

    def account(self, number) -> int:
        return self.one("SELECT AccountID FROM Account WHERE AccountNumber = ?", str(number))

    def no_closes(self) -> str:
        return "VoucherNumber NOT IN (" + ",".join(f"'{e}'" for e in self.closes) + ")"


def data(b: ExerciseBuild) -> Data:
    if "data" not in b.found:
        b.found["data"] = Data(b.year)
    return b.found["data"]


def month_index(day: str) -> int:
    return int(day[:4]) * 12 + int(day[5:7]) - 1


def depreciation_schedule(d: Data) -> dict:
    """The monthly depreciation charged to 1090 from FixedAsset (as the Part III case computes it): OriginalCost /
    UsefulLifeMonths from the month after the in-service date through the month before disposal."""
    assets = []
    for s, life, cost, disp in d.q("SELECT InServiceDate, UsefulLifeMonths, OriginalCost, DisposalDate FROM FixedAsset "
                                   "WHERE DepreciationDebitAccountID = ?", d.account(1090)):
        start, end = month_index(s) + 1, month_index(s) + life
        last = min(end, month_index(disp) - 1) if disp else end
        assets.append((start, last, round(cost / life, 2)))
    return {y: [round(sum(m for a, b_, m in assets if a <= y * 12 + k <= b_), 2) for k in range(12)] for y in (d.C, d.N)}


# --- the expected values: the twin, in plain Python -------------------------------------------------------------

def model(d: Data) -> dict:
    """Every value of the case as the twin computes it (scripts/verify/twins/ch18_twins.py, facts/notes/ch18.py),
    row by row in Python; the linear programs of Requirement 7 are solved by ex07.solve_lp."""
    first, last = d.first, d.last
    items = {r[0]: dict(code=r[1], group=r[2], type=r[3], mode=r[4], std=r[5], lst=r[6], conv=r[7] or 0.0,
                        stdh=r[8] or 0.0, routing=r[9], fam=r[1][:7])
             for r in d.q("SELECT ItemID, ItemCode, ItemGroup, ItemType, SupplyMode, StandardCost, ListPrice, "
                          "StandardConversionCost, StandardLaborHoursPerUnit, RoutingID FROM Item")}
    mfg = {i for i, v in items.items() if v["mode"] == "Manufactured" and v["type"] == "Finished Good"}
    fams = sorted({items[i]["fam"] for i in mfg})

    # Requirement 1
    sold = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for iid, qty, total, base in d.q("SELECT l.ItemID, l.Quantity, l.LineTotal, l.BaseListPrice FROM SalesInvoiceLine l "
                                     "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                                     "WHERE si.InvoiceDate BETWEEN ? AND ?", first, last):
        s = sold[iid]
        s[0] += qty
        s[1] += total
        s[2] += qty * items[iid]["std"]
        s[3] += qty * (base or 0.0)
    var = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0])
    for iid, tv, mv, lv, ov in d.q("SELECT wo.ItemID, c.TotalVarianceAmount, c.MaterialVarianceAmount, "
                                   "c.DirectLaborVarianceAmount, c.OverheadVarianceAmount FROM WorkOrderClose c "
                                   "JOIN WorkOrder wo ON wo.WorkOrderID = c.WorkOrderID WHERE c.CloseDate BETWEEN ? AND ?",
                                   first, last):
        v = var[items[iid]["fam"]]
        v[0] += tv
        v[1] += mv
        v[2] += lv
        v[3] += ov
        v[4] += 1
    comp, comp_wo, comp_item = defaultdict(float), defaultdict(set), defaultdict(float)
    mat_std_completed = 0.0
    for wo, iid, qc, msc in d.q("SELECT pc.WorkOrderID, l.ItemID, l.QuantityCompleted, l.ExtendedStandardMaterialCost "
                                "FROM ProductionCompletionLine l JOIN ProductionCompletion pc "
                                "ON pc.ProductionCompletionID = l.ProductionCompletionID "
                                "WHERE pc.CompletionDate BETWEEN ? AND ?", first, last):
        f = items[iid]["fam"]
        comp[f] += qc
        comp_wo[f].add(wo)
        comp_item[iid] += qc
        mat_std_completed += msc
    vpu = {f: var[f][0] / comp[f] for f in fams if comp[f]}
    fam = {}
    for f in fams:
        ids = [i for i in mfg if items[i]["fam"] == f and sold[i][0] > 0]
        units = sum(sold[i][0] for i in ids)
        if not units:
            continue
        rev = sum(sold[i][1] for i in ids)
        std = sum(sold[i][2] for i in ids)
        completed_std = sum(comp_item[i] * items[i]["std"] for i in comp_item if items[i]["fam"] == f)
        pids = [i for i in items if items[i]["fam"] == f and items[i]["mode"] == "Purchased" and sold[i][0] > 0]
        prev, pstd = sum(sold[i][1] for i in pids), sum(sold[i][2] for i in pids)
        groups = {items[i]["group"] for i in mfg if items[i]["fam"] == f}
        fam[f] = dict(name=f, short=short(f), group=sorted(groups)[0], ids=ids, units=units, rev=rev, std=std,
                      lst=sum(sold[i][3] for i in ids), closes=var[f][4], variance=var[f][0], material=var[f][1],
                      labor=var[f][2], overhead=var[f][3], share=var[f][0] / completed_std, completed=comp[f],
                      completed_std=completed_std, vpu=vpu.get(f, 0.0), m_std=1 - std / rev,
                      m_unit=1 - (std + vpu.get(f, 0.0) * units) / rev, m_year=1 - (std + var[f][0]) / rev,
                      m_purch=(1 - pstd / prev) if prev else None, p_rev=prev, p_std=pstd)
    unsold = [f for f in fams if f not in fam]
    groups = []
    for g in sorted({v["group"] for v in fam.values()}):
        fs = [v for v in fam.values() if v["group"] == g]
        rev = sum(v["rev"] for v in fs)
        std = sum(v["std"] for v in fs)
        groups.append(dict(name=g, rev=rev, variance=sum(v["variance"] for v in fs), m_std=1 - std / rev,
                           m_unit=1 - (std + sum(v["vpu"] * v["units"] for v in fs)) / rev,
                           m_year=1 - (std + sum(v["variance"] for v in fs)) / rev))
    totals = dict(total=sum(v[0] for v in var.values()), material=sum(v[1] for v in var.values()),
                  labor=sum(v[2] for v in var.values()), overhead=sum(v[3] for v in var.values()),
                  closes=sum(v[4] for v in var.values()))
    mv_rate = totals["material"] / mat_std_completed
    ledger_5080 = d.one(f"SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND "
                        f"{d.no_closes()}", d.account(5080), d.C)
    lines, mismatched = d.q("SELECT COUNT(*), SUM(sil.BaseListPrice IS NULL OR i.ListPrice IS NULL OR ABS(sil.BaseListPrice - "
                            "i.ListPrice) > 0.004) FROM SalesInvoiceLine sil JOIN Item i ON i.ItemID = sil.ItemID")[0]
    ship_mismatch = d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Item i ON i.ItemID = sl.ItemID WHERE "
                          "sl.ExtendedStandardCost IS NULL OR ABS(sl.ExtendedStandardCost - "
                          "ROUND(sl.QuantityShipped * i.StandardCost, 2)) > 0.011")
    max_diff = d.one("SELECT MAX(ABS(l.ExtendedStandardTotalCost - l.QuantityCompleted * i.StandardCost)) FROM "
                     "ProductionCompletionLine l JOIN Item i ON i.ItemID = l.ItemID")
    all_years = d.one("SELECT COUNT(*) FROM (SELECT l.ItemID FROM SalesInvoiceLine l JOIN SalesInvoice si ON "
                      "si.SalesInvoiceID = l.SalesInvoiceID WHERE si.InvoiceDate BETWEEN ? AND ? GROUP BY 1 "
                      "HAVING COUNT(DISTINCT substr(si.InvoiceDate, 1, 4)) = ?)", f"{d.F}-01-01", last, len(d.years))
    po = defaultdict(lambda: [0.0, 0.0])
    for code, qty, cost, lst in d.q("SELECT i.ItemCode, l.Quantity, l.UnitCost, i.ListPrice FROM PurchaseOrderLine l "
                                    "JOIN PurchaseOrder p ON p.PurchaseOrderID = l.PurchaseOrderID JOIN Item i ON "
                                    "i.ItemID = l.ItemID WHERE i.SupplyMode = 'Purchased' AND i.ItemType = 'Finished Good' "
                                    "AND p.OrderDate BETWEEN ? AND ?", first, last):
        po[code[:7]][0] += qty * cost
        po[code[:7]][1] += qty * lst
    purchased = {f: po[f][0] / po[f][1] for f in QUOTE if po[f][1]}
    p_total, p_low, p_high = d.q("SELECT SUM(l.Quantity * l.UnitCost) / SUM(l.Quantity * i.StandardCost), "
                                 "MIN(l.UnitCost / i.StandardCost), MAX(l.UnitCost / i.StandardCost) FROM PurchaseOrderLine l "
                                 "JOIN PurchaseOrder p ON p.PurchaseOrderID = l.PurchaseOrderID JOIN Item i ON i.ItemID = "
                                 "l.ItemID WHERE i.SupplyMode = 'Purchased' AND i.ItemType = 'Finished Good' AND "
                                 "p.OrderDate BETWEEN ? AND ?", first, last)[0]

    # Requirement 2
    a1090 = d.account(1090)
    pay = {(t, k): (h or 0.0, a) for t, k, h, a in d.q(
        "SELECT l.LineType, lte.LaborType, SUM(l.Hours), SUM(l.Amount) FROM PayrollRegisterLine l "
        "JOIN PayrollRegister pr ON pr.PayrollRegisterID = l.PayrollRegisterID JOIN PayrollPeriod pp "
        "ON pp.PayrollPeriodID = pr.PayrollPeriodID JOIN CostCenter cc ON cc.CostCenterID = pr.CostCenterID "
        "LEFT JOIN LaborTimeEntry lte ON lte.LaborTimeEntryID = l.LaborTimeEntryID "
        "WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = ? AND l.LineType NOT IN "
        "('Benefits Deduction', 'Employee Tax Withholding') GROUP BY 1, 2", d.C)}
    src = dict(d.q("SELECT COALESCE(je.EntryType, g.SourceDocumentType), SUM(g.Debit) FROM GLEntry g LEFT JOIN JournalEntry je "
                   "ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry' "
                   "WHERE g.AccountID = ? AND g.PostingDate BETWEEN ? AND ? AND g.Debit > 0 "
                   "AND g.SourceDocumentType <> 'WorkOrderClose' GROUP BY 1", a1090, first, last))
    inputs = sum(src.values())
    foh = src.get("Factory Overhead", 0.0)
    dep = src.get("Depreciation", 0.0)
    released_gl = d.one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                        "AND SourceDocumentType = 'ProductionCompletion'", a1090, d.C)
    labor, var_oh, fixed_oh, conversion, stdh, material_released = d.q(
        "SELECT SUM(l.ExtendedStandardDirectLaborCost), SUM(l.ExtendedStandardVariableOverheadCost), "
        "SUM(l.ExtendedStandardFixedOverheadCost), SUM(l.ExtendedStandardConversionCost), "
        "SUM(l.QuantityCompleted * i.StandardLaborHoursPerUnit), SUM(l.ExtendedStandardMaterialCost) "
        "FROM ProductionCompletionLine l JOIN ProductionCompletion pc "
        "ON pc.ProductionCompletionID = l.ProductionCompletionID JOIN Item i ON i.ItemID = l.ItemID "
        "WHERE pc.CompletionDate BETWEEN ? AND ?", first, last)[0]
    direct = sum(a for (t, k), (h, a) in pay.items() if k == "Direct Manufacturing")
    std_m = dict(d.q("SELECT substr(pc.CompletionDate, 1, 7), SUM(l.QuantityCompleted * i.StandardLaborHoursPerUnit) "
                     "FROM ProductionCompletionLine l JOIN ProductionCompletion pc ON pc.ProductionCompletionID = "
                     "l.ProductionCompletionID JOIN Item i ON i.ItemID = l.ItemID GROUP BY 1"))

    def gl_series(where: str) -> dict:
        return defaultdict(float, d.q(
            f"SELECT substr(g.PostingDate, 1, 7), SUM(g.Debit) FROM GLEntry g LEFT JOIN JournalEntry je "
            f"ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry' "
            f"WHERE g.AccountID = ? AND {where} GROUP BY 1", a1090))
    fo_m = gl_series("je.EntryType = 'Factory Overhead'")
    pay_m = gl_series("g.SourceDocumentType = 'PayrollSummary'")
    dep_m = gl_series("je.EntryType = 'Depreciation'")
    start = f"{d.F}-01"
    months = sorted(m for m in std_m if start < m <= f"{d.C}-12")
    with_start = sorted(m for m in std_m if start <= m <= f"{d.C}-12")

    def fit(y: dict, ms: list) -> dict:
        xs, ys = [std_m[m] for m in ms], [y[m] for m in ms]
        lr, r = st.linear_regression(xs, ys), st.correlation(xs, ys)
        return dict(slope=lr.slope, intercept=lr.intercept, r=r, r2=r * r)
    applied = dict(d.q("SELECT substr(pc.CompletionDate, 1, 4), SUM(l.ExtendedStandardVariableOverheadCost + "
                       "l.ExtendedStandardFixedOverheadCost) FROM ProductionCompletionLine l JOIN ProductionCompletion pc "
                       "ON pc.ProductionCompletionID = l.ProductionCompletionID GROUP BY 1"))
    fo_ratio = [sum(v for m, v in fo_m.items() if m.startswith(str(y))) / applied[str(y)] for y in d.years]
    dep_months = [dep_m[f"{d.C}-{k:02d}"] for k in range(1, 13)]
    runs = []
    for k, v in enumerate(dep_months):
        if runs and abs(runs[-1]["amount"] - v) < 0.005:
            runs[-1]["last"] = k
        else:
            runs.append(dict(amount=v, first=k, last=k))

    # Requirement 3
    run = dict(d.q("SELECT RoutingID, SUM(StandardRunHoursPerUnit) FROM RoutingOperation GROUP BY 1"))
    setup = dict(d.q("SELECT RoutingID, SUM(StandardSetupHours) FROM RoutingOperation GROUP BY 1"))
    wc_names = dict(d.q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter"))
    run_wc, setup_wc = defaultdict(dict), defaultdict(dict)
    for rid, wc, sh, rh in d.q("SELECT RoutingID, WorkCenterID, SUM(StandardSetupHours), SUM(StandardRunHoursPerUnit) "
                               "FROM RoutingOperation GROUP BY 1, 2"):
        run_wc[rid][wc] = rh
        setup_wc[rid][wc] = sh
    issue_lines = defaultdict(int)
    for iid, n in d.q("SELECT wo.ItemID, COUNT(*) FROM MaterialIssueLine l JOIN MaterialIssue mi ON mi.MaterialIssueID = "
                      "l.MaterialIssueID JOIN WorkOrder wo ON wo.WorkOrderID = mi.WorkOrderID WHERE mi.WorkOrderID IN "
                      "(SELECT DISTINCT WorkOrderID FROM ProductionCompletion WHERE CompletionDate BETWEEN ? AND ?) "
                      "GROUP BY 1", first, last):
        issue_lines[items[iid]["fam"]] += n
    wo_routing = dict(d.q("SELECT WorkOrderID, RoutingID FROM WorkOrder"))
    batch = {f: comp[f] / len(comp_wo[f]) for f in comp if comp_wo.get(f)}
    activity = defaultdict(lambda: [0.0, 0, 0.0, 0])
    fam_setup = {}
    for f in sorted(batch):
        g = activity[items[next(i for i in mfg if items[i]["fam"] == f)]["group"]]
        fam_setup[f] = sum(setup[wo_routing[wo]] for wo in comp_wo[f])
        g[0] += comp[f]
        g[1] += len(comp_wo[f])
        g[2] += fam_setup[f]
        g[3] += issue_lines[f]
    activities = [dict(name=g, units=u, wos=n, batch=u / n, setup=sh / u * 1000, issues=il / u * 1000)
                  for g, (u, n, sh, il) in sorted(activity.items())]
    avail = dict(d.q("SELECT WorkCenterID, SUM(AvailableHours) FROM WorkCenterCalendar WHERE CalendarDate BETWEEN ? AND ? "
                     "GROUP BY 1", first, last))
    used_wc = defaultdict(float)
    by_wo = d.q("SELECT pc.WorkOrderID, wo.RoutingID, wo.ItemID, SUM(l.QuantityCompleted) FROM ProductionCompletionLine l "
                "JOIN ProductionCompletion pc ON pc.ProductionCompletionID = l.ProductionCompletionID JOIN WorkOrder wo "
                "ON wo.WorkOrderID = pc.WorkOrderID WHERE pc.CompletionDate BETWEEN ? AND ? GROUP BY 1, 2, 3", first, last)
    run_total = setup_total = 0.0
    for wo, rid, iid, qc in by_wo:
        for wc, rh in run_wc[rid].items():
            used_wc[wc] += qc * rh + setup_wc[rid][wc]
        run_total += qc * run[rid]
        setup_total += setup[rid]
    avail_total = sum(avail.values())
    pract = avail_total * PRACTICAL
    used = sum(used_wc.values())
    wcs = sorted(avail)
    centers = [dict(id=wc, name=wc_names[wc].removesuffix(" Work Center"), short=wc_short(wc_names[wc]), avail=avail[wc],
                    pract=avail[wc] * PRACTICAL, used=used_wc[wc], of_avail=used_wc[wc] / avail[wc],
                    of_pract=used_wc[wc] / (avail[wc] * PRACTICAL)) for wc in wcs]
    cal_wc = d.one("SELECT MIN(WorkCenterID) FROM WorkCenterCalendar")
    working_days = d.one("SELECT COUNT(*) FROM WorkCenterCalendar WHERE WorkCenterID = ? AND IsWorkingDay = 1 "
                         "AND CalendarDate BETWEEN ? AND ?", cal_wc, first, last)

    # Requirement 4
    pclass = {r[0]: dict(gross=r[1], tax=r[2], benefits=r[3], n=r[4]) for r in d.q(
        "SELECT e.PayClass, SUM(pr.GrossPay), SUM(pr.EmployerPayrollTax), SUM(pr.EmployerBenefits), "
        "COUNT(DISTINCT pr.EmployeeID) FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = "
        "pr.PayrollPeriodID JOIN Employee e ON e.EmployeeID = pr.EmployeeID JOIN CostCenter cc ON cc.CostCenterID = "
        "pr.CostCenterID WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = ? GROUP BY 1", d.C)}
    for v in pclass.values():
        v["total"] = v["gross"] + v["tax"] + v["benefits"]
    crew, sal = pclass["Hourly"]["total"], pclass["Salary"]["total"]
    committed = crew + sal + dep
    td_rate, crew_rate, fo_rate = committed / pract, crew / pract, foh / stdh

    def time_per_unit(i):
        it = items[i]
        return run[it["routing"]] + setup[it["routing"]] / batch[it["fam"]]

    def costs(i, rate=td_rate):
        it = items[i]
        mat = (it["std"] - it["conv"]) * (1 + mv_rate)
        return dict(mat=mat, std=it["std"], absorp=it["std"] + vpu.get(it["fam"], 0.0),
                    td=mat + fo_rate * it["stdh"] + rate * time_per_unit(i), kept=mat + fo_rate * it["stdh"],
                    time=time_per_unit(i))
    for f, v in fam.items():
        u = v["units"]
        w = {k: sum(sold[i][0] * costs(i)[k] for i in v["ids"]) / u for k in ("std", "absorp", "td", "kept", "time", "mat")}
        w.update(price=v["rev"] / u, reduced=w["kept"] + crew_rate * w["time"])
        w["m_td"] = 1 - w["td"] / w["price"]
        v["unit"] = w
    for g in groups:
        fs = [v for v in fam.values() if v["group"] == g["name"]]
        g["m_td"] = 1 - sum(v["unit"]["td"] * v["units"] for v in fs) / g["rev"]
    data_table = []
    for share in DATA_TABLE:
        p = avail_total * share
        rate = committed / p
        ex = fam[EXAMPLE]
        data_table.append(dict(share=share, rate=rate, unused=(p - used) * rate,
                               example=sum(sold[i][0] * costs(i, rate)["td"] for i in ex["ids"]) / ex["units"]))

    # Requirement 5: the explorer's totals, the finished goods sold (Services left out)
    fg = [i for i in sold if items[i]["type"] == "Finished Good" and sold[i][0] > 0]
    rev_fg = sum(sold[i][1] for i in fg)
    view, item_m = defaultdict(float), {}
    for i in fg:
        u = sold[i][0]
        if i in mfg:
            c = costs(i)
            vals = dict(std=c["std"], absorp=c["absorp"], td=c["td"])
        else:
            vals = dict(std=items[i]["std"], absorp=items[i]["std"], td=items[i]["std"])
        for k, v in vals.items():
            view[k] += u * v
        item_m[i] = {k: sold[i][1] - u * v for k, v in vals.items()}
    top_n = round(len(fg) * TOP_SHARE)
    tops = {}
    for k in ("std", "absorp", "td"):
        ms = sorted((m[k] for m in item_m.values()), reverse=True)
        low = min(item_m, key=lambda i: item_m[i][k] / sold[i][1])
        tops[k] = dict(share=sum(ms[:top_n]) / sum(ms), negative=sum(1 for m in ms if m < 0),
                       low=items[low]["code"], low_margin=item_m[low][k] / sold[low][1])
    unused_h = pract - used
    explorer = dict(n_items=len(fg), rev=rev_fg, std_cost=view["std"], std=rev_fg - view["std"],
                    absorp=rev_fg - view["absorp"], td=rev_fg - view["td"],
                    td_unused=rev_fg - view["td"] - unused_h * td_rate, year=rev_fg - view["std"] - totals["total"],
                    top_n=top_n, tops=tops)

    # Requirement 6
    labor_rate = RATE * (1 + BURDEN)
    pos_hours = PRACTICAL * DAY_HOURS * working_days
    severance = SEVERANCE_WEEKS * WEEK_HOURS * labor_rate
    quoted = []
    for f, (_, vol, price, tooling, _) in QUOTE.items():
        w, u = fam[f]["unit"], fam[f]["units"]
        dq = price * (1 + FREIGHT)
        quoted.append(dict(name=f, short=short(f), volume=vol, price=price, tooling=tooling, units=u, kept=w["kept"],
                           reduced=w["reduced"], absorp_cost=w["absorp"], delivered=dq, absorp=(w["absorp"] - dq) * u,
                           a_kept=(w["kept"] - dq) * u, a_reduced=(w["reduced"] - dq) * u,
                           be_kept=w["kept"] / (1 + FREIGHT), be_reduced=w["reduced"] / (1 + FREIGHT),
                           margin=1 - dq / w["price"], time=w["time"]))
    buy = [q for q in quoted if q["a_reduced"] > 0]
    lose = [q for q in quoted if q["a_reduced"] <= 0 and q["a_kept"] <= 0]
    gain = sum(q["a_reduced"] for q in buy)
    hours = sum(q["time"] * q["units"] for q in buy)
    positions = hours / pos_hours
    tooling = sum(q["tooling"] for q in buy)
    two_way = [[sum(((q["kept"] + share * crew_rate * q["time"]) - q["price"] * (1 + adj) * (1 + FREIGHT)) * q["units"]
                    for q in buy) for adj in TWO_WAY_QUOTE] for share in TWO_WAY_CREW]
    buy_names = sorted(q["name"] for q in buy)
    buy_material = sum(comp_item[i] * (items[i]["std"] - items[i]["conv"]) for i in comp_item if items[i]["fam"] in buy_names)
    issues = d.one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                   "AND SourceDocumentType = 'MaterialIssue'", d.account(1045), d.C)
    build = d.q(f"WITH r AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM GoodsReceiptLine l JOIN GoodsReceipt g "
                f"ON g.GoodsReceiptID = l.GoodsReceiptID WHERE substr(g.ReceiptDate, 1, 4) = ?1 GROUP BY 1), "
                f"s AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM MaterialIssueLine l JOIN MaterialIssue m "
                f"ON m.MaterialIssueID = l.MaterialIssueID WHERE substr(m.IssueDate, 1, 4) = ?1 GROUP BY 1) "
                f"SELECT i.ItemID, i.ItemGroup, COALESCE(r.v, 0) - COALESCE(s.v, 0), i.ItemCode FROM Item i "
                f"LEFT JOIN r ON r.ItemID = i.ItemID LEFT JOIN s ON s.ItemID = i.ItemID "
                f"WHERE i.ItemGroup IN ({','.join('?' * len(MATERIALS))}) ORDER BY 3 DESC", str(d.C), *MATERIALS)
    six = build[:SIX]
    fam_marks = ",".join("?" * len(buy_names))
    six_marks = ",".join(str(r[0]) for r in six)
    fam_issued = d.one(f"SELECT SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l JOIN MaterialIssue m ON "
                       f"m.MaterialIssueID = l.MaterialIssueID JOIN WorkOrder wo ON wo.WorkOrderID = m.WorkOrderID JOIN Item i "
                       f"ON i.ItemID = wo.ItemID WHERE substr(m.IssueDate, 1, 4) = ? AND substr(i.ItemCode, 1, 7) IN "
                       f"({fam_marks})", str(d.C), *buy_names)
    six_issued = d.one(f"SELECT SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l JOIN MaterialIssue m ON "
                       f"m.MaterialIssueID = l.MaterialIssueID JOIN WorkOrder wo ON wo.WorkOrderID = m.WorkOrderID JOIN Item i "
                       f"ON i.ItemID = wo.ItemID WHERE substr(m.IssueDate, 1, 4) = ? AND substr(i.ItemCode, 1, 7) IN "
                       f"({fam_marks}) AND l.ItemID IN ({six_marks})", str(d.C), *buy_names)

    # Requirement 7
    freed = defaultdict(float)
    for wo, rid, iid, qc in by_wo:
        if items[iid]["fam"] in buy_names:
            for wc, rh in run_wc[rid].items():
                freed[wc] += qc * rh + setup_wc[rid][wc]
    supervision = hours * (td_rate - crew_rate)
    load = {f: defaultdict(float) for f in fam}
    for f, v in fam.items():
        for i in v["ids"]:
            rid = items[i]["routing"]
            for wc, rh in run_wc[rid].items():
                load[f][wc] += sold[i][0] * (rh + setup_wc[rid][wc] / batch[f])
    headroom = {wc: avail[wc] * PRACTICAL / sum(load[f][wc] for f in fam) for wc in wcs}
    lp = [growth_lp(quoted, fam, load, wcs, avail, g) for g in GROWTH]

    # Requirement 8
    reprice = []
    for f in sorted(fam):
        w = fam[f]["unit"]
        if w["m_td"] < FLOOR:
            new = w["td"] / (1 - FLOOR)
            cm = w["price"] - w["kept"]
            reprice.append(dict(name=f, short=short(f), new=new, increase=new / w["price"] - 1,
                                loss=1 - cm / (cm + (new - w["price"])), revenue=(new - w["price"]) * fam[f]["units"]))

    # Requirement 9
    plan_dep = round(sum(depreciation_schedule(d)[d.N]), 2)
    parts = dict(direct=labor_rate, variable=fo_rate, indirect=(PLAN_HOURS - 1) * labor_rate,
                 supervision=pclass["Salary"]["gross"] * (1 + BURDEN) / stdh, depreciation=plan_dep / stdh)
    new_rate = sum(parts.values())
    one_rate = new_rate - parts["indirect"]
    td_std = fo_rate + td_rate * used / stdh
    actual_rate = inputs / stdh
    for q in quoted:
        f = fam[q["name"]]
        q["revised"] = sum(sold[i][0] * ((items[i]["std"] - items[i]["conv"]) + new_rate * items[i]["stdh"])
                           for i in f["ids"]) / f["units"]
        q["td"] = f["unit"]["td"]
    stock = []
    for y in d.years:
        asof = f"{y}-12-31"
        net = defaultdict(float)
        for iid, qc in d.q("SELECT l.ItemID, SUM(l.QuantityCompleted) FROM ProductionCompletionLine l JOIN ProductionCompletion pc "
                           "ON pc.ProductionCompletionID = l.ProductionCompletionID WHERE pc.CompletionDate <= ? GROUP BY 1",
                           asof):
            net[iid] += qc
        for iid, qs in d.q("SELECT l.ItemID, SUM(l.QuantityShipped) FROM ShipmentLine l JOIN Shipment s ON s.ShipmentID = "
                           "l.ShipmentID WHERE s.ShipmentDate <= ? GROUP BY 1", asof):
            net[iid] -= qs
        for iid, qr in d.q("SELECT l.ItemID, SUM(l.QuantityReturned) FROM SalesReturnLine l JOIN SalesReturn r ON "
                           "r.SalesReturnID = l.SalesReturnID WHERE r.ReturnDate <= ? GROUP BY 1", asof):
            net[iid] += qr
        on_hand = {i: u for i, u in net.items() if i in mfg and u > 0}
        negative = sorted(items[i]["code"] for i, u in net.items() if i in mfg and u < -0.05)
        sh = sum(u * items[i]["stdh"] for i, u in on_hand.items())
        cv = sum(u * items[i]["conv"] for i, u in on_hand.items())
        stock.append(dict(year=y, units=sum(on_hand.values()), std=sum(u * items[i]["std"] for i, u in on_hand.items()),
                          stdh=sh, conv=cv, per_hour=cv / sh, negative=negative, plan=sh * new_rate - cv,
                          one=sh * one_rate - cv, td=sh * td_std - cv, actual=sh * actual_rate - cv))
    income = {y: d.one(f"SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                       f"WHERE a.AccountType IN ('Revenue', 'Expense') AND g.FiscalYear = ? AND {d.no_closes()}", y)
              for y in d.years}
    opening = d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")
    opening_fg = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?",
                       d.account(1040), opening)

    return dict(items=items, mfg=mfg, fams=fams, fam=fam, unsold=unsold, groups=groups, totals=totals, mv_rate=mv_rate,
                mat_std_completed=mat_std_completed, ledger_5080=ledger_5080, lines=lines, mismatched=mismatched,
                ship_mismatch=ship_mismatch, max_diff=max_diff, all_years=all_years, purchased=purchased,
                p_total=p_total, p_low=p_low, p_high=p_high, comp=comp, sold=sold, pay=pay, src=src, inputs=inputs,
                foh=foh, dep=dep, released_gl=released_gl, labor=labor, var_oh=var_oh, fixed_oh=fixed_oh,
                conversion=conversion, stdh=stdh, material_released=material_released, direct=direct, months=months,
                with_start=with_start,
                fits=dict(fo=fit(fo_m, months), pay=fit(pay_m, months), dep=fit(dep_m, months),
                          pay_start=fit(pay_m, with_start)),
                fo_ratio=fo_ratio, dep_months=dep_months, runs=runs, activities=activities, fam_setup=fam_setup,
                issue_lines=issue_lines, comp_wo={f: len(v) for f, v in comp_wo.items()}, centers=centers,
                avail=avail_total, pract=pract, used=used, run_total=run_total, setup_total=setup_total,
                working_days=working_days, pclass=pclass, crew=crew, sal=sal, committed=committed, td_rate=td_rate,
                crew_rate=crew_rate, fo_rate=fo_rate, unused_h=unused_h, data_table=data_table, explorer=explorer,
                labor_rate=labor_rate, pos_hours=pos_hours, severance=severance, quoted=quoted, buy=buy, lose=lose,
                gain=gain, hours=hours, positions=positions, tooling=tooling, two_way=two_way, buy_names=buy_names,
                buy_material=buy_material, issues=issues, six=six, fam_issued=fam_issued, six_issued=six_issued,
                freed={wc: freed[wc] for wc in wcs}, wc_names=wc_names, supervision=supervision, headroom=headroom,
                wcs=wcs, load=load, lp=lp, reprice=reprice, plan_dep=plan_dep, parts=parts, new_rate=new_rate,
                one_rate=one_rate, td_std=td_std, actual_rate=actual_rate, stock=stock, batch=batch, income=income,
                opening=opening, opening_fg=opening_fg)


def growth_lp(quoted: list[dict], fam: dict, load: dict, wcs: list, avail: dict, growth: float) -> dict:
    """Requirement 7's optional Solver model: with volume up by `growth`, buy as few units of the quoted families as
    keeps every work center within its practical capacity, at the least added cost with the crew kept (the delivered
    quote less the relevant cost kept, per unit bought).

    Solver's model minimizes the added cost over the units bought. It is solved here in terms of the units made instead
    (made = demand at growth - bought), which turns it into the form solve_lp takes (maximize, A x <= b with b >= 0):
    maximize the added cost avoided, subject to the hours of the units made fitting the capacity left after the other
    families. The two are the same program, so the optimum, the binding work centers, the reduced costs, and the
    objective ranges carry over; a shadow price changes sign (an hour of capacity lowers the cost Solver minimizes)."""
    names = {q["name"] for q in quoted}
    c = [q["delivered"] - q["kept"] for q in quoted]
    upper = [q["units"] * (1 + growth) for q in quoted]
    per_unit = [[load[q["name"]][wc] / q["units"] for q in quoted] for wc in wcs]
    others = [sum(load[f][wc] * (1 + growth) for f in fam if f not in names) for wc in wcs]
    cap = [avail[wc] * PRACTICAL for wc in wcs]
    rhs = [cap[k] - others[k] for k in range(len(wcs))]
    assert all(r >= 0 for r in rhs), "the other families alone exceed a work center's practical capacity"
    s = solve_lp(c, per_unit, rhs, upper)
    var, con = sensitivity(s, len(quoted))
    made = s["x"]
    bought = [max(u - z, 0.0) for u, z in zip(upper, made)]
    full = [sum(load[f][wc] * (1 + growth) for f in fam) for wc in wcs]
    used = [full[k] - sum(per_unit[k][j] * bought[j] for j in range(len(quoted))) for k in range(len(wcs))]
    binding = [k for k in range(len(wcs)) if cap[k] - used[k] < 1e-6]
    return dict(growth=growth, cost=sum(ci * bi for ci, bi in zip(c, bought)), bought=bought, upper=upper, extra=c,
                per_unit=per_unit, cap=cap, full=full, used=used, binding=binding, shadow=[-y for y in s["y"]],
                reduced=[v["reduced"] for v in var], c_inc=[v["inc"] for v in var], c_dec=[v["dec"] for v in var],
                r_inc=[v["inc"] for v in con], r_dec=[v["dec"] for v in con])


def volume_test(d: Data) -> list[dict]:
    """The Part II case's test (facts/notes/case2.volume): list-price order value in each promotion's months against the
    other months of its year."""
    orders = ("FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
              "JOIN Item i ON i.ItemID = l.ItemID JOIN Customer c ON c.CustomerID = o.CustomerID")
    scope_sql = {"Collection": "i.CollectionName", "ItemGroup": "i.ItemGroup", "Segment": "c.CustomerSegment"}
    out = []
    for pid, code, scope, seg, grp, coll, start in d.q(
            "SELECT PromotionID, PromotionCode, ScopeType, CustomerSegment, ItemGroup, CollectionName, EffectiveStartDate "
            "FROM PromotionProgram ORDER BY PromotionID"):
        label = {"Collection": coll, "ItemGroup": grp, "Segment": seg}[scope]
        months = sorted({int(m) for (m,) in d.q(f"SELECT DISTINCT substr(o.OrderDate, 6, 2) {orders} WHERE l.PromotionID = ?",
                                                pid)})
        by_month = {(int(y), int(m)): v for y, m, v in d.q(
            f"SELECT substr(o.OrderDate, 1, 4), substr(o.OrderDate, 6, 2), SUM(l.Quantity * l.BaseListPrice) {orders} "
            f"WHERE {scope_sql[scope]} = ? GROUP BY 1, 2", label)}
        y = int(start[:4])
        window = sum(by_month.get((y, m), 0.0) for m in months)
        other = [by_month.get((y, m), 0.0) for m in range(1, 13) if m not in months]
        expected, sd = st.mean(other) * len(months), st.stdev(other)
        out.append(dict(id=pid, code=code, scope=scope, label=label, year=y, months=months,
                        values=[by_month.get((y, m), 0.0) for m in range(1, 13)], lift=window / expected - 1,
                        z=(window - expected) / (sd * len(months) ** 0.5)))
    return out


# --- MakeBuy.sql: the queries whose results the workbook pastes (Copy with Headers) ------------------------------------
# Each is run read-only on CharlesRiver.sqlite when the solution is built. :first and :last are the base year's first and
# last days, :start the first day of the ledger's first year; {closes}, {families}, and the work-center and month
# columns are filled in from the data before the query runs.

QUERIES: dict[str, tuple[str, str]] = {
    "family": ("family results of the base year: each manufactured family's sales (units, revenue, list value, standard "
               "cost), the variance of the year's work order closes by part, the units and standard cost its completions "
               "released, and the sales of the purchased products of the same family", """
WITH it AS (
    SELECT ItemID, substr(ItemCode, 1, 7) AS Family, ItemGroup, SupplyMode, StandardCost
    FROM Item
    WHERE ItemType = 'Finished Good'
),
sold AS (
    SELECT it.Family, it.SupplyMode,
        SUM(l.Quantity) AS Units, SUM(l.LineTotal) AS Revenue,
        SUM(l.Quantity * l.BaseListPrice) AS ListValue,
        SUM(l.Quantity * it.StandardCost) AS StandardCost
    FROM SalesInvoiceLine l
    JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID
    JOIN it ON it.ItemID = l.ItemID
    WHERE si.InvoiceDate BETWEEN :first AND :last
    GROUP BY it.Family, it.SupplyMode
),
closes AS (
    SELECT it.Family, COUNT(*) AS Closes,
        SUM(c.MaterialVarianceAmount) AS MaterialVariance,
        SUM(c.DirectLaborVarianceAmount) AS LaborVariance,
        SUM(c.OverheadVarianceAmount) AS OverheadVariance,
        SUM(c.TotalVarianceAmount) AS TotalVariance
    FROM WorkOrderClose c
    JOIN WorkOrder wo ON wo.WorkOrderID = c.WorkOrderID
    JOIN it ON it.ItemID = wo.ItemID
    WHERE c.CloseDate BETWEEN :first AND :last
    GROUP BY it.Family
),
made AS (
    SELECT it.Family, SUM(l.QuantityCompleted) AS UnitsCompleted,
        SUM(l.QuantityCompleted * it.StandardCost) AS StandardCostCompleted,
        SUM(l.ExtendedStandardMaterialCost) AS StandardMaterialCompleted
    FROM ProductionCompletionLine l
    JOIN ProductionCompletion pc ON pc.ProductionCompletionID = l.ProductionCompletionID
    JOIN it ON it.ItemID = l.ItemID
    WHERE pc.CompletionDate BETWEEN :first AND :last
    GROUP BY it.Family
)
SELECT m.Family, (SELECT MIN(ItemGroup) FROM it WHERE it.Family = m.Family) AS ItemGroup,
    m.Units, m.Revenue, m.ListValue, m.StandardCost,
    c.Closes, c.MaterialVariance, c.LaborVariance, c.OverheadVariance, c.TotalVariance,
    d.UnitsCompleted, d.StandardCostCompleted, d.StandardMaterialCompleted,
    p.Revenue AS PurchasedRevenue, p.StandardCost AS PurchasedStandardCost
FROM sold m
LEFT JOIN closes c ON c.Family = m.Family
LEFT JOIN made d ON d.Family = m.Family
LEFT JOIN sold p ON p.Family = m.Family AND p.SupplyMode = 'Purchased'
WHERE m.SupplyMode = 'Manufactured'
ORDER BY m.Family;"""),
    "ledger5080": ("account 5080 Manufacturing Variance in the base year, the year-end closes left out", """
SELECT SUM(g.Debit) - SUM(g.Credit) AS Variance5080
FROM GLEntry g
JOIN Account a ON a.AccountID = g.AccountID
WHERE a.AccountNumber = 5080 AND g.FiscalYear = :year
    AND g.VoucherNumber NOT IN ({closes});"""),
    "purchased": ("the base year's purchase orders for purchased finished goods, by family: what Charles River paid, "
                  "with the list and standard value of the same units", """
SELECT substr(i.ItemCode, 1, 7) AS Family,
    SUM(l.Quantity * l.UnitCost) AS OrderCost,
    SUM(l.Quantity * i.ListPrice) AS ListValue,
    SUM(l.Quantity * i.StandardCost) AS StandardValue,
    MIN(l.UnitCost / i.StandardCost) AS LowestCostToStandard,
    MAX(l.UnitCost / i.StandardCost) AS HighestCostToStandard
FROM PurchaseOrderLine l
JOIN PurchaseOrder p ON p.PurchaseOrderID = l.PurchaseOrderID
JOIN Item i ON i.ItemID = l.ItemID
WHERE i.SupplyMode = 'Purchased' AND i.ItemType = 'Finished Good'
    AND p.OrderDate BETWEEN :first AND :last
GROUP BY substr(i.ItemCode, 1, 7)
ORDER BY Family;"""),
    "premises": ("the CFO's second premise: whether list prices and standard costs changed in the three years", """
SELECT
    (SELECT COUNT(*) FROM SalesInvoiceLine) AS InvoiceLines,
    (SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID
        WHERE l.BaseListPrice IS NULL OR i.ListPrice IS NULL
            OR ABS(l.BaseListPrice - i.ListPrice) > 0.004) AS ListPriceDiffers,
    (SELECT COUNT(*) FROM ShipmentLine l JOIN Item i ON i.ItemID = l.ItemID
        WHERE l.ExtendedStandardCost IS NULL
            OR ABS(l.ExtendedStandardCost - ROUND(l.QuantityShipped * i.StandardCost, 2)) > 0.011)
        AS ShipmentCostDiffers,
    (SELECT MAX(ABS(l.ExtendedStandardTotalCost - l.QuantityCompleted * i.StandardCost))
        FROM ProductionCompletionLine l JOIN Item i ON i.ItemID = l.ItemID) AS LargestCompletionDifference,
    (SELECT COUNT(*) FROM (
        SELECT l.ItemID FROM SalesInvoiceLine l
        JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID
        WHERE si.InvoiceDate BETWEEN :start AND :last
        GROUP BY l.ItemID
        HAVING COUNT(DISTINCT substr(si.InvoiceDate, 1, 4)) = :years)) AS ItemsSoldEveryYear;"""),
    "payroll": ("the inputs to 1090: the Manufacturing cost center's payroll of the base year by line type and labor "
                "type (employee deductions left out)", """
SELECT l.LineType, COALESCE(t.LaborType, '') AS LaborType,
    SUM(l.Hours) AS Hours, SUM(l.Amount) AS Amount
FROM PayrollRegisterLine l
JOIN PayrollRegister pr ON pr.PayrollRegisterID = l.PayrollRegisterID
JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID
JOIN CostCenter cc ON cc.CostCenterID = pr.CostCenterID
LEFT JOIN LaborTimeEntry t ON t.LaborTimeEntryID = l.LaborTimeEntryID
WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = :year
    AND l.LineType NOT IN ('Benefits Deduction', 'Employee Tax Withholding')
GROUP BY l.LineType, t.LaborType
ORDER BY CASE l.LineType WHEN 'Regular Earnings' THEN 1 WHEN 'Overtime Earnings' THEN 2
    WHEN 'Salary Earnings' THEN 3 WHEN 'Employer Payroll Tax' THEN 4 ELSE 5 END, t.LaborType;"""),
    "debits1090": ("the debits to 1090 Manufacturing Cost Clearing in the base year by source, the favorable closes' "
                   "debits left out", """
SELECT COALESCE(je.EntryType, g.SourceDocumentType) AS Source, SUM(g.Debit) AS Debits
FROM GLEntry g
JOIN Account a ON a.AccountID = g.AccountID
LEFT JOIN JournalEntry je
    ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry'
WHERE a.AccountNumber = 1090 AND g.PostingDate BETWEEN :first AND :last
    AND g.Debit > 0 AND g.SourceDocumentType <> 'WorkOrderClose'
GROUP BY COALESCE(je.EntryType, g.SourceDocumentType)
ORDER BY Source;"""),
    "released": ("what the base year's completions released at standard, by part, with their standard labor hours; and "
                 "the ProductionCompletion credits to 1090", """
SELECT SUM(l.QuantityCompleted * i.StandardLaborHoursPerUnit) AS StandardHours,
    SUM(l.ExtendedStandardMaterialCost) AS Material,
    SUM(l.ExtendedStandardDirectLaborCost) AS DirectLabor,
    SUM(l.ExtendedStandardVariableOverheadCost) AS VariableOverhead,
    SUM(l.ExtendedStandardFixedOverheadCost) AS FixedOverhead,
    SUM(l.ExtendedStandardConversionCost) AS Conversion,
    (SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID
        WHERE a.AccountNumber = 1090 AND g.FiscalYear = :year
            AND g.SourceDocumentType = 'ProductionCompletion') AS CreditsTo1090
FROM ProductionCompletionLine l
JOIN ProductionCompletion pc ON pc.ProductionCompletionID = l.ProductionCompletionID
JOIN Item i ON i.ItemID = l.ItemID
WHERE pc.CompletionDate BETWEEN :first AND :last;"""),
    "monthly": ("the inputs to 1090 by month with the standard hours completed and the overhead they applied, from the "
                "ledger's first month to the end of the base year, and the payroll dates posted to 1090 each month", """
WITH made AS (
    SELECT substr(pc.CompletionDate, 1, 7) AS Month,
        SUM(l.QuantityCompleted * i.StandardLaborHoursPerUnit) AS StandardHours,
        SUM(l.ExtendedStandardVariableOverheadCost + l.ExtendedStandardFixedOverheadCost) AS AppliedOverhead
    FROM ProductionCompletionLine l
    JOIN ProductionCompletion pc ON pc.ProductionCompletionID = l.ProductionCompletionID
    JOIN Item i ON i.ItemID = l.ItemID
    GROUP BY substr(pc.CompletionDate, 1, 7)
),
posted AS (
    SELECT substr(g.PostingDate, 1, 7) AS Month,
        SUM(CASE WHEN je.EntryType = 'Factory Overhead' THEN g.Debit ELSE 0 END) AS FactoryOverhead,
        SUM(CASE WHEN g.SourceDocumentType = 'PayrollSummary' THEN g.Debit ELSE 0 END) AS Payroll,
        SUM(CASE WHEN je.EntryType = 'Depreciation' THEN g.Debit ELSE 0 END) AS Depreciation,
        COUNT(DISTINCT CASE WHEN g.SourceDocumentType = 'PayrollSummary' THEN g.PostingDate END) AS PayDates
    FROM GLEntry g
    JOIN Account a ON a.AccountID = g.AccountID
    LEFT JOIN JournalEntry je
        ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry'
    WHERE a.AccountNumber = 1090
    GROUP BY substr(g.PostingDate, 1, 7)
)
SELECT m.Month, m.StandardHours, m.AppliedOverhead,
    COALESCE(p.FactoryOverhead, 0) AS FactoryOverhead, COALESCE(p.Payroll, 0) AS Payroll,
    COALESCE(p.Depreciation, 0) AS Depreciation, COALESCE(p.PayDates, 0) AS PayDates
FROM made m
LEFT JOIN posted p ON p.Month = m.Month
WHERE m.Month BETWEEN substr(:start, 1, 7) AND substr(:last, 1, 7)
ORDER BY m.Month;"""),
    "activity": ("activities of the base year's completions by family: work orders, units, routing run and setup hours "
                 "at each work center, and the material issue lines of those work orders", """
WITH done AS (
    SELECT pc.WorkOrderID, SUM(l.QuantityCompleted) AS Units
    FROM ProductionCompletionLine l
    JOIN ProductionCompletion pc ON pc.ProductionCompletionID = l.ProductionCompletionID
    WHERE pc.CompletionDate BETWEEN :first AND :last
    GROUP BY pc.WorkOrderID
),
orders AS (
    SELECT d.WorkOrderID, d.Units, wo.RoutingID,
        substr(i.ItemCode, 1, 7) AS Family, i.ItemGroup
    FROM done d
    JOIN WorkOrder wo ON wo.WorkOrderID = d.WorkOrderID
    JOIN Item i ON i.ItemID = wo.ItemID
),
issues AS (
    SELECT mi.WorkOrderID, COUNT(*) AS IssueLines
    FROM MaterialIssueLine l
    JOIN MaterialIssue mi ON mi.MaterialIssueID = l.MaterialIssueID
    WHERE mi.WorkOrderID IN (SELECT WorkOrderID FROM done)
    GROUP BY mi.WorkOrderID
),
hours AS (
    SELECT o.Family, r.WorkCenterID,
        SUM(o.Units * r.StandardRunHoursPerUnit) AS RunHours,
        SUM(r.StandardSetupHours) AS SetupHours
    FROM orders o
    JOIN RoutingOperation r ON r.RoutingID = o.RoutingID
    GROUP BY o.Family, r.WorkCenterID
)
SELECT o.Family, MIN(o.ItemGroup) AS ItemGroup, COUNT(*) AS WorkOrders, SUM(o.Units) AS UnitsCompleted,
{run_columns},
{setup_columns},
    SUM(COALESCE(x.IssueLines, 0)) AS IssueLines
FROM orders o
LEFT JOIN issues x ON x.WorkOrderID = o.WorkOrderID
GROUP BY o.Family
ORDER BY o.Family;"""),
    "calendar": ("the hours available at each work center in the base year (WorkCenterCalendar), with its working days",
                 """
SELECT w.WorkCenterID, w.WorkCenterName, SUM(c.AvailableHours) AS AvailableHours,
    SUM(c.IsWorkingDay) AS WorkingDays
FROM WorkCenterCalendar c
JOIN WorkCenter w ON w.WorkCenterID = c.WorkCenterID
WHERE c.CalendarDate BETWEEN :first AND :last
GROUP BY w.WorkCenterID, w.WorkCenterName
ORDER BY w.WorkCenterID;"""),
    "payclass": ("the committed cost of the crew and supervision: the Manufacturing cost center's payroll of the base "
                 "year by pay class, with the employees on record", """
SELECT e.PayClass, COUNT(DISTINCT pr.EmployeeID) AS Employees,
    (SELECT COUNT(*) FROM Employee x JOIN CostCenter y ON y.CostCenterID = x.CostCenterID
        WHERE y.CostCenterName = 'Manufacturing' AND x.PayClass = e.PayClass) AS EmployeesOnRecord,
    SUM(pr.GrossPay) AS GrossPay, SUM(pr.EmployerPayrollTax) AS EmployerTax,
    SUM(pr.EmployerBenefits) AS Benefits
FROM PayrollRegister pr
JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID
JOIN Employee e ON e.EmployeeID = pr.EmployeeID
JOIN CostCenter cc ON cc.CostCenterID = pr.CostCenterID
WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = :year
GROUP BY e.PayClass
ORDER BY e.PayClass;"""),
    "plandep": ("the depreciation the FixedAsset schedule charges to 1090 in the year after the base year (the plan's "
                "depreciation)", """
WITH RECURSIVE m(k) AS (SELECT 0 UNION ALL SELECT k + 1 FROM m WHERE k < 11),
assets AS (
    SELECT ROUND(f.OriginalCost * 1.0 / f.UsefulLifeMonths, 2) AS Monthly,
        CAST(substr(f.InServiceDate, 1, 4) AS INTEGER) * 12 + CAST(substr(f.InServiceDate, 6, 2) AS INTEGER)
            AS FirstMonth,
        MIN(CAST(substr(f.InServiceDate, 1, 4) AS INTEGER) * 12 + CAST(substr(f.InServiceDate, 6, 2) AS INTEGER)
                + f.UsefulLifeMonths - 1,
            COALESCE(CAST(substr(f.DisposalDate, 1, 4) AS INTEGER) * 12
                + CAST(substr(f.DisposalDate, 6, 2) AS INTEGER) - 2, 999999)) AS LastMonth
    FROM FixedAsset f
    JOIN Account a ON a.AccountID = f.DepreciationDebitAccountID
    WHERE a.AccountNumber = 1090
)
SELECT ROUND(SUM(a.Monthly), 2) AS PlanYearDepreciation
FROM assets a
JOIN m ON (:next * 12 + m.k) BETWEEN a.FirstMonth AND a.LastMonth;"""),
    "materials": ("materials of the families bought ({families}): the standard material of their base-year completions, "
                  "the materials issued to their work orders in the base year, of which the six raw materials that "
                  "carry the Part IV case's build, and all the year's issues (1045)", """
WITH six AS (
    SELECT i.ItemID
    FROM Item i
    LEFT JOIN (SELECT l.ItemID, SUM(l.ExtendedStandardCost) AS v FROM GoodsReceiptLine l
               JOIN GoodsReceipt g ON g.GoodsReceiptID = l.GoodsReceiptID
               WHERE g.ReceiptDate BETWEEN :first AND :last GROUP BY l.ItemID) r ON r.ItemID = i.ItemID
    LEFT JOIN (SELECT l.ItemID, SUM(l.ExtendedStandardCost) AS v FROM MaterialIssueLine l
               JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID
               WHERE m.IssueDate BETWEEN :first AND :last GROUP BY l.ItemID) s ON s.ItemID = i.ItemID
    WHERE i.ItemGroup IN ('Raw Materials', 'Packaging')
    ORDER BY COALESCE(r.v, 0) - COALESCE(s.v, 0) DESC
    LIMIT 6
),
issued AS (
    SELECT l.ItemID, l.ExtendedStandardCost
    FROM MaterialIssueLine l
    JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID
    JOIN WorkOrder wo ON wo.WorkOrderID = m.WorkOrderID
    JOIN Item i ON i.ItemID = wo.ItemID
    WHERE m.IssueDate BETWEEN :first AND :last AND substr(i.ItemCode, 1, 7) IN ({families})
)
SELECT
    (SELECT SUM(l.QuantityCompleted * (i.StandardCost - i.StandardConversionCost))
        FROM ProductionCompletionLine l
        JOIN ProductionCompletion pc ON pc.ProductionCompletionID = l.ProductionCompletionID
        JOIN Item i ON i.ItemID = l.ItemID
        WHERE pc.CompletionDate BETWEEN :first AND :last
            AND substr(i.ItemCode, 1, 7) IN ({families})) AS StandardMaterialCompleted,
    (SELECT SUM(ExtendedStandardCost) FROM issued) AS IssuedToTheirWorkOrders,
    (SELECT SUM(ExtendedStandardCost) FROM issued WHERE ItemID IN (SELECT ItemID FROM six)) AS OfWhichSixRawMaterials,
    (SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID
        WHERE a.AccountNumber = 1045 AND g.FiscalYear = :year
            AND g.SourceDocumentType = 'MaterialIssue') AS AllIssues1045;"""),
    "promotions": ("list-price order value by month in each promotion's scope and year, with the months its lines were "
                   "ordered in (the Part II case's test of volume)", """
WITH orders AS (
    SELECT o.OrderDate, l.Quantity * l.BaseListPrice AS ListValue, l.PromotionID,
        i.CollectionName, i.ItemGroup, c.CustomerSegment
    FROM SalesOrderLine l
    JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID
    JOIN Item i ON i.ItemID = l.ItemID
    JOIN Customer c ON c.CustomerID = o.CustomerID
),
promo AS (
    SELECT PromotionID, PromotionCode, ScopeType,
        CASE ScopeType WHEN 'Collection' THEN CollectionName WHEN 'ItemGroup' THEN ItemGroup
            ELSE CustomerSegment END AS Scope,
        substr(EffectiveStartDate, 1, 4) AS Year
    FROM PromotionProgram
),
scoped AS (
    SELECT p.PromotionID, CAST(substr(o.OrderDate, 6, 2) AS INTEGER) AS M, o.ListValue
    FROM promo p
    JOIN orders o ON substr(o.OrderDate, 1, 4) = p.Year
        AND p.Scope = CASE p.ScopeType WHEN 'Collection' THEN o.CollectionName
            WHEN 'ItemGroup' THEN o.ItemGroup ELSE o.CustomerSegment END
)
SELECT p.PromotionID, p.PromotionCode, p.ScopeType, p.Scope, CAST(p.Year AS INTEGER) AS Year,
    (SELECT GROUP_CONCAT(M, ',') FROM (SELECT DISTINCT CAST(substr(o.OrderDate, 6, 2) AS INTEGER) AS M
        FROM orders o WHERE o.PromotionID = p.PromotionID ORDER BY 1)) AS PromotionMonths,
{month_columns}
FROM promo p
JOIN scoped s ON s.PromotionID = p.PromotionID
GROUP BY p.PromotionID
ORDER BY p.PromotionID;"""),
    "pricelists": ("the price lists: scope, status, and dates, their prices against list, and the order lines priced "
                   "from them after their end date (Exercise 8.6's test)", """
SELECT pl.PriceListID, pl.PriceListName, pl.ScopeType, pl.Status,
    pl.EffectiveStartDate, pl.EffectiveEndDate,
    (SELECT MIN(x.UnitPrice / i.ListPrice) FROM PriceListLine x JOIN Item i ON i.ItemID = x.ItemID
        WHERE x.PriceListID = pl.PriceListID) AS LowestPriceToList,
    (SELECT MAX(x.UnitPrice / i.ListPrice) FROM PriceListLine x JOIN Item i ON i.ItemID = x.ItemID
        WHERE x.PriceListID = pl.PriceListID) AS HighestPriceToList,
    (SELECT COUNT(*) FROM SalesOrderLine l
        JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID
        JOIN PriceListLine x ON x.PriceListLineID = l.PriceListLineID
        WHERE x.PriceListID = pl.PriceListID AND o.OrderDate > pl.EffectiveEndDate) AS OrderLinesAfterEnd
FROM PriceList pl
ORDER BY pl.PriceListID;"""),
    "overrides": ("approved price overrides by the approver's job title", """
SELECT e.JobTitle AS ApproverJobTitle, COUNT(*) AS ApprovedOverrides
FROM PriceOverrideApproval a
JOIN Employee e ON e.EmployeeID = a.ApprovedByEmployeeID
WHERE a.Status = 'Approved'
GROUP BY e.JobTitle
ORDER BY ApprovedOverrides DESC;"""),
    "onhand": ("manufactured finished goods made since the ledger opened and on hand at each year-end: completions less "
               "shipments plus returns through the year-end, by item", """
WITH moves AS (
    SELECT l.ItemID, pc.CompletionDate AS MoveDate, l.QuantityCompleted AS Quantity
    FROM ProductionCompletionLine l
    JOIN ProductionCompletion pc ON pc.ProductionCompletionID = l.ProductionCompletionID
    UNION ALL
    SELECT l.ItemID, s.ShipmentDate, -l.QuantityShipped
    FROM ShipmentLine l JOIN Shipment s ON s.ShipmentID = l.ShipmentID
    UNION ALL
    SELECT l.ItemID, r.ReturnDate, l.QuantityReturned
    FROM SalesReturnLine l JOIN SalesReturn r ON r.SalesReturnID = l.SalesReturnID
)
SELECT i.ItemID, i.ItemCode,
{year_columns}
FROM moves m
JOIN Item i ON i.ItemID = m.ItemID
WHERE i.SupplyMode = 'Manufactured' AND i.ItemType = 'Finished Good'
GROUP BY i.ItemID, i.ItemCode
ORDER BY i.ItemCode;"""),
    "income": ("income before income taxes as recorded: revenue less expenses by fiscal year, the year-end closes left "
               "out (the ledger has no income tax account)", """
SELECT g.FiscalYear, SUM(g.Credit) - SUM(g.Debit) AS IncomeBeforeTaxes
FROM GLEntry g
JOIN Account a ON a.AccountID = g.AccountID
WHERE a.AccountType IN ('Revenue', 'Expense') AND g.FiscalYear BETWEEN :fy AND :year
    AND g.VoucherNumber NOT IN ({closes})
GROUP BY g.FiscalYear
ORDER BY g.FiscalYear;"""),
    "openingfg": ("the finished goods (1040) on the opening journal entry, which carries no item detail", """
SELECT je.EntryNumber, SUM(g.Debit) - SUM(g.Credit) AS OpeningFinishedGoods
FROM GLEntry g
JOIN Account a ON a.AccountID = g.AccountID
JOIN JournalEntry je ON je.EntryNumber = g.VoucherNumber
WHERE a.AccountNumber = 1040 AND je.EntryType = 'Opening'
GROUP BY je.EntryNumber;"""),
    "dates": ("the dates through which the base year's records run", """
SELECT
    (SELECT MAX(InvoiceDate) FROM SalesInvoice WHERE InvoiceDate <= :last) AS LastInvoice,
    (SELECT MAX(CompletionDate) FROM ProductionCompletion WHERE CompletionDate <= :last) AS LastCompletion,
    (SELECT MAX(CloseDate) FROM WorkOrderClose WHERE CloseDate <= :last) AS LastClose,
    (SELECT MAX(WorkDate) FROM LaborTimeEntry WHERE WorkDate <= :last) AS LastTimeRecord;"""),
}


def query_text(d: Data, key: str, **extra) -> str:
    """A query's SQL with the data-dependent parts filled in (the closes, the work-center columns, the months)."""
    sql = QUERIES[key][1].strip()
    centers = d.q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter ORDER BY WorkCenterID")
    fill = dict(
        closes=",".join(f"'{e}'" for e in d.closes),
        run_columns=",\n".join(f"    (SELECT h.RunHours FROM hours h WHERE h.Family = o.Family AND h.WorkCenterID = {w})"
                               f" AS {wc_short(n)}Run" for w, n in centers),
        setup_columns=",\n".join(f"    (SELECT h.SetupHours FROM hours h WHERE h.Family = o.Family AND h.WorkCenterID = "
                                 f"{w}) AS {wc_short(n)}Setup" for w, n in centers),
        month_columns=",\n".join(f"    SUM(CASE WHEN s.M = {k} THEN s.ListValue ELSE 0 END) AS M{k:02d}"
                                 for k in range(1, 13)),
        year_columns=",\n".join(f"    SUM(CASE WHEN m.MoveDate <= '{y}-12-31' THEN m.Quantity ELSE 0 END) AS OnHand{y}"
                                for y in d.years),
        families="")
    fill.update(extra)
    for k, v in fill.items():
        sql = sql.replace("{" + k + "}", v)
    return sql


def run_query(d: Data, key: str, **extra) -> tuple[list[str], list[tuple]]:
    params = dict(first=d.first, last=d.last, start=f"{d.F}-01-01", year=d.C, fy=d.F, next=d.N, years=len(d.years))
    cur = d.con.execute(query_text(d, key, **extra), params)        # named parameters; the unused ones are ignored
    return [c[0] for c in cur.description], cur.fetchall()


# --- worksheet helpers ----------------------------------------------------------------------------------------------

HOURS, RATE4, PCT1, UNITS = "#,##0.0", "#,##0.0000", "0.0%", "#,##0.0"
TOP = -4160                                       # xlTop
SRC_RANGE = 1                                     # xlSrcRange
AMBER = 0xCCF2FF                                  # a light amber tint (BGR), for changing cells
CALC_AUTOMATIC, CALC_EXCEPT_TABLES = -4105, 2     # xlCalculationAutomatic, xlCalculationSemiautomatic


def ms(b: ExerciseBuild) -> dict:
    """The expected values (computed once per build)."""
    if "model" not in b.found:
        b.found["model"] = model(data(b))
    return b.found["model"]


def sheet(b: ExerciseBuild, name: str):
    """A new worksheet, placed before the query worksheets and the Solution Notes (so the analysis sheets stay in order)."""
    names = [ws.Name for ws in b.wb.Worksheets]
    anchor = next((n for n in ("ItemCosts", NOTES) if n in names), None)
    return xl.sheet(b.wb, name, before=b.wb.Worksheets(anchor)) if anchor else xl.sheet(b.wb, name)


def wait_idle(app, timeout: float = 600.0) -> None:
    """Wait until Excel is ready and not calculating. Unlike xl.wait_ready, a pending calculation (Data Tables left
    for the next full calculation) counts as idle."""
    import time
    import pythoncom
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if app.Ready and app.CalculationState != 1:          # 1 = xlCalculating
                return
        except pythoncom.com_error as exc:
            if exc.hresult not in xl.BUSY:
                raise
        time.sleep(0.25)
    raise TimeoutError("Excel stayed busy")


def settle(b: ExerciseBuild) -> None:
    """Wait until Excel has finished calculating (a Data Table or Goal Seek keeps it busy, and it rejects calls)."""
    wait_idle(b.wb.Application)


def answer(ws, row: int, paragraphs: list[str], last_col: str = "H") -> int:
    """ex07.model_answer, retried while Excel is busy recalculating the Data Tables."""
    wait_idle(ws.Application)
    return xl.retry(lambda: model_answer(ws, row, paragraphs, last_col=last_col))


def ref(ws, addr: str) -> str:
    """A cell reference from another sheet: 'Sheet name'!$B$3."""
    cell = ws.Range(addr).GetAddress(True, True)
    return "'" + ws.Name.replace("'", "''") + "'!" + cell


def bold(ws, addr: str) -> None:
    ws.Range(addr).Font.Bold = True


def blue(ws, addr: str) -> None:
    ws.Range(addr).Font.Color = xl.BLUE


def note(ws, addr: str, text: str, width: int = 360, height: int = 130) -> None:
    def run():
        cell = ws.Range(addr)
        if cell.Comment is not None:
            cell.Comment.Delete()
        cell.AddComment(text)
        cell.Comment.Shape.Width = width
        cell.Comment.Shape.Height = height
    wait_idle(ws.Application)
    xl.retry(run)


def title(ws, text: str, sub: str = "") -> None:
    ws.Range("A1").Value = text
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 13
    if sub:
        ws.Range("A2").Value = sub
        ws.Range("A2").Font.Italic = True


def heading(ws, row: int, text: str, col: str = "A") -> None:
    ws.Range(f"{col}{row}").Value = text
    ws.Range(f"{col}{row}").Font.Bold = True


def header(ws, row: int, labels: list[str], col: int = 1) -> None:
    for i, label in enumerate(labels):
        ws.Cells(row, col + i).Value = label
    rng = ws.Range(ws.Cells(row, col), ws.Cells(row, col + len(labels) - 1))
    rng.Font.Bold = True
    rng.WrapText = True
    rng.VerticalAlignment = TOP


def lines(ws, row: int, items: list[tuple], col: str = "A", wb=None) -> dict[str, str]:
    """Label and value rows from `row`: (label, value or formula, number format, name). Returns each item's address
    (by its name, or its label) as a sheet-qualified reference; a name, when given, is defined for the value cell."""
    out = {}
    c0 = ws.Range(f"{col}1").Column
    for i, item in enumerate(items):
        label, value, fmt, name = (list(item) + [None, None, None])[:4]
        r = row + i
        ws.Cells(r, c0).Value = label
        cell = ws.Cells(r, c0 + 1)
        if isinstance(value, str) and value.startswith("="):
            cell.Formula2 = value
        elif value is not None:
            cell.Value = value
        if fmt:
            cell.NumberFormat = fmt
        addr = ref(ws, cell.Address)
        if name:
            ws.Parent.Names.Add(Name=name, RefersTo="=" + addr)
        out[name or label] = addr
    return out


def write_block(ws, top_left: str, rows: list[list]) -> object:
    r0, c0 = ws.Range(top_left).Row, ws.Range(top_left).Column
    rng = ws.Range(ws.Cells(r0, c0), ws.Cells(r0 + len(rows) - 1, c0 + len(rows[0]) - 1))
    rng.Value = tuple(tuple(r) for r in rows)
    return rng


def as_date(v):
    """An ISO date as an Excel serial number (a datetime would be shifted by the time-zone offset through COM)."""
    if isinstance(v, str) and len(v) >= 10:
        return float((date(int(v[:4]), int(v[5:7]), int(v[8:10])) - date(1899, 12, 30)).days)
    return v


def paste(b: ExerciseBuild, ws, top_left: str, key: str, table: str, formats: dict | None = None,
          text: tuple = (), dates: tuple = (), **extra):
    """Paste a MakeBuy.sql result with its headers (Copy with Headers), make it an Excel Table, and label it with a
    note that names the query's purpose."""
    d = data(b)
    cols, rows = run_query(d, key, **extra)
    r0, c0 = ws.Range(top_left).Row, ws.Range(top_left).Column
    for name in text:                                  # text columns stay text (a month such as 2024-01 is not a date)
        k = cols.index(name)
        ws.Range(ws.Cells(r0 + 1, c0 + k), ws.Cells(r0 + max(len(rows), 1), c0 + k)).NumberFormat = "@"
    body = [[as_date(v) if c in dates else v for v, c in zip(row, cols)] for row in rows]
    rng = write_block(ws, top_left, [cols] + body)
    lo = ws.ListObjects.Add(SRC_RANGE, rng, None, xl.XL_YES)
    lo.Name = table
    for name, fmt in (formats or {}).items():
        lo.ListColumns(name).DataBodyRange.NumberFormat = fmt
    for name in dates:
        lo.ListColumns(name).DataBodyRange.NumberFormat = "yyyy-mm-dd"
    purpose = QUERIES[key][0].replace("{families}", extra.get("families", "").replace("'", ""))
    note(ws, top_left, f"Pasted from MakeBuy.sql (Copy with Headers), query: {purpose}. The query was run read-only on "
                       f"CharlesRiver.sqlite when this solution was built; its result is pasted as values and made an "
                       f"Excel Table ({table}).", height=150)
    b.found.setdefault("pasted", []).append((ws.Name, table, purpose))
    return lo


def add_cols(lo, specs: list[tuple]) -> None:
    """Calculated columns: (name, formula, number format)."""
    for name, formula, *fmt in specs:
        xl.add_column(lo, name, formula, fmt[0] if fmt else None)


def col_letter(lo, name: str) -> str:
    return col(lo.ListColumns(name).Range.Column)


def autofit(ws, cols: str, width: float | None = None) -> None:
    if width:
        ws.Columns(cols).ColumnWidth = width
    else:
        ws.Columns(cols).AutoFit()


def fam_lookup(table: str, column: str, family: str) -> str:
    return f'=XLOOKUP("{family}",{table}[Family],{table}[{column}])'


def text_list(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


# --- Documentation and Assumptions --------------------------------------------------------------------------------

def documentation(b: ExerciseBuild) -> None:
    """The Documentation worksheet: purpose, sources, the date through which the data run, and what each sheet holds."""
    ws = b.wb.Worksheets("Documentation")
    d = data(b)
    if "dates" not in b.found:
        paste(b, ws, "A22", "dates", "DataThrough", dates=("LastInvoice", "LastCompletion", "LastClose", "LastTimeRecord"))
        b.found["dates"] = True
        heading(ws, 21, "The dates through which the records of the base year run")
    pasted = b.found.get("pasted", [])
    sheets = [s.Name for s in b.wb.Worksheets if s.Name != NOTES]
    rows = [
        ("Purpose", "Make, Buy, or Reprice (Chapter 18): the cost of each product family the plant makes under three "
                    "views, the decision on the contract manufacturer's quote, the price increases the 2028 lists need, "
                    "and standards on normal capacity with their effect on the statements already issued."),
        ("Prepared by", "Instructor solution (the companion builder), " + date.today().isoformat()),
        ("Base year", f"Fiscal {d.C}, the last year of the records (tbl-18-02)."),
        ("Data through", '="The base year\'s sales invoices and completions run through "&TEXT(MAX(DataThrough[LastInvoice],'
                         'DataThrough[LastCompletion]),"d mmmm yyyy")&"; the last work order close of the year is dated "'
                         '&TEXT(DataThrough[LastClose],"d mmmm yyyy")&", and the time records end "&TEXT('
                         'DataThrough[LastTimeRecord],"d mmmm yyyy")&" (pay periods after that are open)."'),
        ("Sources: CharlesRiver.xlsx", "Power Query (Data > Refresh All): ItemCosts (Item finished goods with their "
                                       "routing hours and the base year's sales by item, from the queries RoutingTotals, "
                                       "Invoices, and ItemSales, which are connection only) and RoutingHours (routing "
                                       "hours by routing and work center)."),
        ("Sources: MakeBuy.sql", "Run on CharlesRiver_Capstone.sqlite and pasted with Copy with Headers as Excel Tables "
                                 "(each table's first cell names its query): "
                                 + "; ".join(f"{t} on {s}" for s, t, _ in pasted) + "."),
        ("Inputs", "Blue cells are typed inputs: the quote (tbl-18-01) and the controller's assumptions (tbl-18-02) on "
                   "Assumptions, and the sensitivity inputs of the Data Tables. Black cells are formulas or pasted "
                   "query results."),
        ("Not from a refresh", "Goal Seek leaves its results in the changing cells (break-even quotes on Make or Buy, "
                               "target prices on Prices), each beside the same value computed directly. Solver's optimum "
                               "(Growth 40% and Growth 50%) and its Sensitivity reports are written as values; each "
                               "model is saved with its sheet, so Data > Solver opens it ready to solve."),
        ("Worksheets", "; ".join(sheets) + "."),
        ("Checks", "The Solution Notes worksheet checks every result the instructor notes state against values computed "
                   "independently from CharlesRiver.sqlite."),
    ]
    for i, (label, text) in enumerate(rows, start=1):
        ws.Cells(i, 1).Value = label
        if text.startswith("="):
            ws.Cells(i, 2).Formula2 = text
        else:
            ws.Cells(i, 2).Value = text
    ws.Range(f"A1:A{len(rows)}").Font.Bold = True
    ws.Columns("A").ColumnWidth = 24
    ws.Columns("B").ColumnWidth = 110
    ws.Range(f"B1:B{len(rows)}").WrapText = True
    ws.Range(f"A1:B{len(rows)}").VerticalAlignment = TOP
    ws.Range(f"A1:B{len(rows)}").Rows.AutoFit()


def assumptions(b: ExerciseBuild) -> None:
    ws = sheet(b, "Assumptions")
    title(ws, "Assumptions", "Typed in blue as the chapter gives them: the quote (tbl-18-01) and the controller's "
                             "planning assumptions (tbl-18-02). Every other sheet reads them from here.")
    heading(ws, 4, "The contract manufacturer's quote (tbl-18-01, a hypothetical exhibit)")
    rows = [["Family", "Description", "QuotedVolume", "Price", "Tooling", "LeadTimeWeeks"]]
    rows += [[f, desc, vol, price, tool, lead] for f, (desc, vol, price, tool, lead) in QUOTE.items()]
    rng = write_block(ws, "A5", rows)
    lo = ws.ListObjects.Add(SRC_RANGE, rng, None, xl.XL_YES)
    lo.Name = "Quote"
    lo.DataBodyRange.Font.Color = xl.BLUE
    for c, fmt in (("QuotedVolume", COUNT), ("Price", MONEY), ("Tooling", COUNT)):
        lo.ListColumns(c).DataBodyRange.NumberFormat = fmt
    r = 6 + len(QUOTE) + 1
    heading(ws, r, "Terms of the quote")
    terms = [("Inbound freight, a share of the price (Charles River pays it)", FREIGHT, PCT1, "Freight"),
             ("Minimum purchase, a share of the quoted volume of each family chosen", MINIMUM, PCT1, "MinimumShare"),
             ("Defects credited above, a share of units", DEFECTS, PCT1, "DefectThreshold"),
             ("Payment terms (days)", PAYMENT_DAYS, COUNT, "PaymentDays"),
             ("Years the prices are fixed (2028 and 2029)", PRICE_YEARS, COUNT, "PriceYears")]
    lines(ws, r + 1, terms)
    blue(ws, f"B{r + 1}:B{r + len(terms)}")
    r += len(terms) + 2
    heading(ws, r, "The controller's planning assumptions (tbl-18-02)")
    d = data(b)
    items = [("Base year (fiscal)", d.C, "0", "BaseYear"),
             ("Practical capacity, a share of the available hours in WorkCenterCalendar", PRACTICAL, PCT1, "PracticalShare"),
             ("Straight-time labor rate, an hour", RATE, MONEY, "LaborRate"),
             ("Burden, a share of pay", BURDEN, "0.00%", "Burden"),
             ("Hours per standard hour at plan", PLAN_HOURS, "0.00", "PlanHours"),
             ("  of which indirect", INDIRECT, "0.00", "IndirectHours"),
             ("Plan volume, the normal capacity (standard hours a year)", PLAN_VOLUME, MONEY, "PlanVolume"),
             ("Salaried production staff at plan, a year, before burden", PLAN_SALARIES, MONEY, "PlanSalaries"),
             ("Depreciation at plan, a year", PLAN_DEPRECIATION, MONEY, "PlanDepreciation"),
             ("Hours in a position's day", DAY_HOURS, "0", "DayHours"),
             ("Working days in the base year (WorkCenterCalendar; from the Activities sheet)", 0, "0", "WorkingDays"),
             ("Practical hours of one position: practical share x hours a day x working days",
              "=PracticalShare*DayHours*WorkingDays", HOURS, "PositionHours"),
             ("Severance per position: weeks of straight-time pay", SEVERANCE_WEEKS, "0", "SeveranceWeeks"),
             ("  hours a week", WEEK_HOURS, "0", "WeekHours"),
             ("Severance per position, with burden", "=SeveranceWeeks*WeekHours*LaborRate*(1+Burden)", MONEY,
              "SeverancePerPosition"),
             ("Materiality for the statements, a share of income before income taxes as recorded", MATERIALITY, PCT1,
              "MaterialityShare"),
             ("Margin floor for pricing: gross margin on time-driven cost, before unused capacity", FLOOR, PCT1,
              "MarginFloor"),
             ("Demand-growth test (optional), lower", GROWTH[0], PCT1, "GrowthLow"),
             ("Demand-growth test (optional), higher", GROWTH[1], PCT1, "GrowthHigh")]
    addr = lines(ws, r + 1, items)
    for i, item in enumerate(items):
        if not (isinstance(item[1], str) or item[3] == "WorkingDays"):
            blue(ws, f"B{r + 1 + i}")
    b.found["assumption_rows"] = addr
    ws.Columns("A").ColumnWidth = 78
    ws.Columns("B:F").ColumnWidth = 14
    ws.Range("A5:F5").Font.Bold = True


# --- Power Query: the item master, the routings, and the base year's sales by item ---------------------------------

def item_queries(b: ExerciseBuild) -> None:
    from xlbuild.analysis import nav
    wb, y = b.wb, b.year
    num = "type number"
    xl.add_query(wb, "Invoices", nav(b, 16, "SalesInvoice", {"InvoiceDate": "type date"}, extra=[
        ("Removed Other Columns", pq.select_columns(["SalesInvoiceID", "InvoiceDate"]))]))
    xl.add_query(wb, "ItemSales", nav(b, 17, "SalesInvoiceLine", {"Quantity": num, "LineTotal": num, "BaseListPrice": num},
                                      extra=[
        ("Merged Queries", pq.merge("Invoices", "SalesInvoiceID", "SalesInvoiceID", "Invoices")),
        ("Expanded Invoices", pq.expand("Invoices", ["InvoiceDate"])),
        ("Filtered Rows", pq.select_rows(f"Date.Year([InvoiceDate]) = {y}")),
        ("Added Custom", pq.add_custom("ListValue", "[Quantity] * [BaseListPrice]")),
        ("Grouped Rows", 'Table.Group({prev}, {"ItemID"}, {{"Units", each List.Sum([Quantity]), type number}, '
                         '{"Revenue", each List.Sum([LineTotal]), type number}, '
                         '{"ListValue", each List.Sum([ListValue]), type number}})')]))
    hours = {"StandardSetupHours": num, "StandardRunHoursPerUnit": num}
    xl.add_query(wb, "RoutingTotals", nav(b, 50, "RoutingOperation", hours, extra=[
        ("Grouped Rows", 'Table.Group({prev}, {"RoutingID"}, {{"RunHours", each List.Sum([StandardRunHoursPerUnit]), '
                         'type number}, {"SetupHours", each List.Sum([StandardSetupHours]), type number}})')]))
    xl.add_query(wb, "RoutingHours", nav(b, 50, "RoutingOperation", hours, extra=[
        ("Grouped Rows", 'Table.Group({prev}, {"RoutingID", "WorkCenterID"}, {{"RunHours", each '
                         'List.Sum([StandardRunHoursPerUnit]), type number}, {"SetupHours", each '
                         'List.Sum([StandardSetupHours]), type number}})'),
        ("Sorted Rows", 'Table.Sort({prev},{{"RoutingID", Order.Ascending}, {"WorkCenterID", Order.Ascending}})')]))
    keep = ["ItemID", "ItemCode", "ItemName", "ItemGroup", "SupplyMode", "RoutingID", "StandardCost",
            "StandardConversionCost", "StandardLaborHoursPerUnit"]
    order = keep[:3] + ["Family"] + keep[3:] + ["RunHours", "SetupHours", "Units", "Revenue", "ListValue"]
    xl.add_query(wb, "ItemCosts", nav(b, 44, "Item", {"StandardCost": num, "StandardConversionCost": num,
                                                      "StandardLaborHoursPerUnit": num, "ListPrice": num}, extra=[
        ("Filtered Rows", pq.select_rows('([ItemType] = "Finished Good")')),
        ("Removed Other Columns", pq.select_columns(keep)),
        ("Added Custom", pq.add_custom("Family", "Text.Start([ItemCode], 7)")),
        ("Merged Queries", pq.merge("RoutingTotals", "RoutingID", "RoutingID", "RoutingTotals")),
        ("Expanded RoutingTotals", pq.expand("RoutingTotals", ["RunHours", "SetupHours"])),
        ("Merged Queries1", pq.merge("ItemSales", "ItemID", "ItemID", "ItemSales")),
        ("Expanded ItemSales", pq.expand("ItemSales", ["Units", "Revenue", "ListValue"])),
        ("Replaced Value", 'Table.ReplaceValue({prev},null,0,Replacer.ReplaceValue,{"RunHours", "SetupHours", "Units", '
                           '"Revenue", "ListValue"})'),
        ("Changed Type1", pq.transform_types([("Family", "type text"), ("RunHours", num), ("SetupHours", num),
                                              ("Units", num), ("Revenue", num), ("ListValue", num)])),
        ("Reordered Columns", "Table.ReorderColumns({prev},{" + ", ".join(pq.m_string(c) for c in order) + "})"),
        ("Sorted Rows", 'Table.Sort({prev},{{"ItemID", Order.Ascending}})')]))
    last = b.wb.Worksheets(b.wb.Worksheets.Count)
    lo = xl.load_query(wb, "ItemCosts", "ItemCosts", after=last)
    xl.load_query(wb, "RoutingHours", "RoutingHours", after=lo.Parent)
    for c, fmt in (("StandardCost", MONEY), ("StandardConversionCost", MONEY), ("Revenue", MONEY),
                   ("ListValue", MONEY), ("Units", UNITS)):
        lo.ListColumns(c).DataBodyRange.NumberFormat = fmt


# --- Requirement 1: the CFO's numbers and the premises behind them ------------------------------------------------

def r1(b: ExerciseBuild) -> None:
    wb = b.wb
    m, d = ms(b), data(b)
    doc = wb.Worksheets(1)
    doc.Name = "Documentation"
    assumptions(b)
    ws = sheet(b, "Families")
    item_queries(b)
    title(ws, f"Requirement 1: the CFO's numbers and the premises behind them (fiscal {d.C})",
          "Families are the first seven characters of the item code; sales by invoice date; the variance is that of the "
          "year's work order closes; the variance per unit divides it by the year's units completed.")
    lo = paste(b, ws, "A4", "family", "FamilyResults", formats={
        "Units": UNITS, "Revenue": MONEY, "ListValue": MONEY, "StandardCost": MONEY, "Closes": COUNT,
        "MaterialVariance": MONEY, "LaborVariance": MONEY, "OverheadVariance": MONEY, "TotalVariance": MONEY,
        "UnitsCompleted": UNITS, "StandardCostCompleted": MONEY, "StandardMaterialCompleted": MONEY,
        "PurchasedRevenue": MONEY, "PurchasedStandardCost": MONEY})
    add_cols(lo, [
        ("VarianceShare", "=[@TotalVariance]/[@StandardCostCompleted]", PCT1),
        ("VariancePerUnit", "=[@TotalVariance]/[@UnitsCompleted]", MONEY),
        ("MarginStandard", "=1-[@StandardCost]/[@Revenue]", PCT1),
        ("MarginPerUnit", "=1-([@StandardCost]+[@VariancePerUnit]*[@Units])/[@Revenue]", PCT1),
        ("MarginYear", "=1-([@StandardCost]+[@TotalVariance])/[@Revenue]", PCT1),
        ("PurchasedMargin", '=IF([@PurchasedRevenue]>0,1-[@PurchasedStandardCost]/[@PurchasedRevenue],"none")', PCT1),
        ("BeatsPurchased", '=IF(ISNUMBER([@PurchasedMargin]),AND([@MarginPerUnit]>[@PurchasedMargin],'
                           '[@MarginYear]>[@PurchasedMargin]),"")'),
        ("UnitsInItemTable", '=SUMIFS(ItemCosts[Units],ItemCosts[Family],[@Family],ItemCosts[SupplyMode],"Manufactured")',
         UNITS),
        ("RevenueInItemTable", '=SUMIFS(ItemCosts[Revenue],ItemCosts[Family],[@Family],ItemCosts[SupplyMode],'
                               '"Manufactured")', MONEY)])
    note(ws, f"{col_letter(lo, 'UnitsInItemTable')}4", "UnitsInItemTable and RevenueInItemTable recompute the units and "
         "revenue from the ItemCosts query (Power Query on CharlesRiver.xlsx), a second path to the same sales: they "
         "must equal the pasted Units and Revenue.")
    n = lo.ListRows.Count
    r = 5 + n + 1
    ws.Cells(r, 1).Value = "Total"
    for c in ("Units", "Revenue", "StandardCost", "Closes", "MaterialVariance", "LaborVariance", "OverheadVariance",
              "TotalVariance", "UnitsCompleted", "StandardCostCompleted"):
        cl = col_letter(lo, c)
        ws.Range(f"{cl}{r}").Formula = f"=SUBTOTAL(109,FamilyResults[{c}])"
        ws.Range(f"{cl}{r}").NumberFormat = COUNT if c == "Closes" else (UNITS if c.startswith("Units") else MONEY)
    ws.Range(f"A{r}:{col_letter(lo, 'RevenueInItemTable')}{r}").Font.Bold = True
    b.found["fam_total_row"] = r

    # Groups
    r += 3
    heading(ws, r - 1, "By item group (the CFO's comparison is Furniture's)")
    header(ws, r, ["Group", "Revenue", "Standard cost", "Variance of the year's closes",
                   "Variance at the per-unit rate on units sold", "Margin at standard",
                   "Margin after the variance per unit completed", "Margin with the year's variance"])
    groups = [g["name"] for g in m["groups"]]
    gro = {}
    for i, g in enumerate(groups + ["All manufactured families"]):
        rr = r + 1 + i
        ws.Cells(rr, 1).Value = g
        if i < len(groups):
            crit = f"FamilyResults[ItemGroup],$A{rr}"
            formulas(ws, {f"B{rr}": f"=SUMIFS(FamilyResults[Revenue],{crit})",
                          f"C{rr}": f"=SUMIFS(FamilyResults[StandardCost],{crit})",
                          f"D{rr}": f"=SUMIFS(FamilyResults[TotalVariance],{crit})",
                          f"E{rr}": f"=SUMPRODUCT((FamilyResults[ItemGroup]=$A{rr})*FamilyResults[VariancePerUnit]*"
                                    "FamilyResults[Units])"})
        else:
            for c in "BCDE":
                ws.Range(f"{c}{rr}").Formula = f"=SUM({c}{r + 1}:{c}{rr - 1})"
        formulas(ws, {f"F{rr}": f"=1-C{rr}/B{rr}", f"G{rr}": f"=1-(C{rr}+E{rr})/B{rr}", f"H{rr}": f"=1-(C{rr}+D{rr})/B{rr}"})
        gro[g] = rr
    ws.Range(f"B{r + 1}:E{r + len(groups) + 1}").NumberFormat = MONEY
    ws.Range(f"F{r + 1}:H{r + len(groups) + 1}").NumberFormat = "0.00%"
    b.found["group_rows"] = gro
    r += len(groups) + 3

    # Reconciliation to the ledger, and the premises
    heading(ws, r, "Reconciliation to account 5080")
    paste(b, ws, f"D{r + 1}", "ledger5080", "Ledger5080", formats={"Variance5080": MONEY})
    rec = lines(ws, r + 1, [
        ("Variance of the year's closes, all families", "=SUM(FamilyResults[TotalVariance])", MONEY, "FamilyVariance"),
        ("Account 5080, the year-end closes left out (pasted, column D)", "=Ledger5080[Variance5080]", MONEY),
        ("Difference", f"=B{r + 1}-B{r + 2}", MONEY),
        ("  of which material", "=SUM(FamilyResults[MaterialVariance])", MONEY),
        ("  of which direct labor", "=SUM(FamilyResults[LaborVariance])", MONEY),
        ("  of which overhead", "=SUM(FamilyResults[OverheadVariance])", MONEY),
        ("Manufactured families not sold in the base year",
         '=LET(f,UNIQUE(FILTER(ItemCosts[Family],ItemCosts[SupplyMode]="Manufactured")),'
         'TEXTJOIN(", ",TRUE,FILTER(f,ISNA(XMATCH(f,FamilyResults[Family])),"none")))', None)])
    b.found["rec1"] = rec
    r += 9
    heading(ws, r, "The purchased products of the same families: what Charles River paid, against list and standard")
    lp = paste(b, ws, f"A{r + 1}", "purchased", "PurchasedCosts", formats={
        "OrderCost": MONEY, "ListValue": MONEY, "StandardValue": MONEY, "LowestCostToStandard": "0.000",
        "HighestCostToStandard": "0.000"})
    add_cols(lp, [("CostToList", "=[@OrderCost]/[@ListValue]", "0.000"),
                  ("CostToStandard", "=[@OrderCost]/[@StandardValue]", "0.000")])
    r += lp.ListRows.Count + 3
    pur = lines(ws, r, [
        ("All purchased finished goods: cost to standard", "=SUM(PurchasedCosts[OrderCost])/SUM(PurchasedCosts[StandardValue])",
         "0.000"),
        ("  lowest order line", "=MIN(PurchasedCosts[LowestCostToStandard])", "0.00"),
        ("  highest order line", "=MAX(PurchasedCosts[HighestCostToStandard])", "0.00")]
        + [(f"{f}: purchased cost to list (the quote's calibration)",
            f'=XLOOKUP("{f}",PurchasedCosts[Family],PurchasedCosts[CostToList])', "0.000") for f in QUOTE])
    b.found["pur1"] = pur
    r += 3 + len(QUOTE) + 1
    heading(ws, r, "The CFO's second premise: did list prices or standard costs change in the three years?")
    paste(b, ws, f"A{r + 1}", "premises", "Premises", formats={"InvoiceLines": COUNT, "LargestCompletionDifference": "0.0000"})
    r += 4
    prem = lines(ws, r, [
        ("Conclusion", '=IF(AND(Premises[ListPriceDiffers]=0,Premises[ShipmentCostDiffers]=0,'
                       'Premises[LargestCompletionDifference]<0.025),"Neither list prices nor standard costs changed: '
                       'every invoice line carries the item\'s list price, every shipment line its standard cost, and '
                       'completion lines differ only by component rounding","A price or a standard changed")', None),
        ("Furniture: margin at standard less margin with the year's variance (the CFO's \"ten points\")",
         f"=F{gro['Furniture']}-H{gro['Furniture']}", "0.0%"),
        ("Families whose margin after the variance (either measure) beats their purchased products'",
         '=TEXTJOIN(", ",TRUE,FILTER(FamilyResults[Family],FamilyResults[BeatsPurchased]=TRUE,"none"))', None)])
    b.found["prem1"] = prem
    r += 4
    g0 = next(g for g in m["groups"] if g["name"] == "Furniture")
    beats = [f["name"] for f in m["fam"].values() if f["m_purch"] is not None and f["m_unit"] > f["m_purch"]
             and f["m_year"] > f["m_purch"]]
    answer(ws, r, [
        f"The CFO's comparison holds as arithmetic. Furniture earns {g0['m_std']:.1%} at standard and {g0['m_year']:.1%} "
        f"once the year's variance is charged ({g0['m_unit']:.1%} at the variance per unit completed), about "
        f"{(g0['m_std'] - g0['m_year']) * 100:.0f} points less; the purchased furniture earns about what its standards "
        f"say, and only {series(beats)} beats its purchased benchmark after the variance. The families' variances add "
        f"up to {m['totals']['total']:,.2f}, which is account 5080 for fiscal {d.C} without the year-end close.",
        f"The second premise holds too: list prices and standard costs never changed in the three years (every invoice "
        f"line carries the item's list price, every shipment line its standard cost, completion lines differ by at most "
        f"{m['max_diff']:.2f}, and {m['all_years']} items sold in every year). But the premise is not a diagnosis: the "
        f"variance is almost all overhead ({m['totals']['overhead']:,.0f} of {m['totals']['total']:,.0f}), so whether the "
        f"products are under-costed depends on how that overhead behaves, which Requirement 2 tests."], last_col="H")
    ws.Columns("A").ColumnWidth = 30
    ws.Columns("B:Z").ColumnWidth = 14
    ws.Range("A4").EntireRow.WrapText = True

    t = "Requirement 1"
    for f in m["fam"].values():
        fam = f["name"]
        look = lambda c: fam_lookup("FamilyResults", c, fam)
        b.check(t, f"{fam}: units sold (from ItemCosts)", round(f["units"], 4), look("UnitsInItemTable"), 0.005, UNITS)
        b.check(t, f"{fam}: revenue (from ItemCosts)", round(f["rev"], 2), look("RevenueInItemTable"), 0.01)
        b.check(t, f"{fam}: closes", f["closes"], look("Closes"), 0, COUNT)
        b.check(t, f"{fam}: variance of the year's closes", round(f["variance"], 2), look("TotalVariance"), 0.01)
        b.check(t, f"{fam}: variance as a share of the standard cost completed", round(f["share"], 9),
                look("VarianceShare"), 1e-9, PCT1)
        b.check(t, f"{fam}: variance per unit completed", round(f["vpu"], 6), look("VariancePerUnit"), 1e-6)
        b.check(t, f"{fam}: margin at standard", round(f["m_std"], 9), look("MarginStandard"), 1e-9, PCT1)
        b.check(t, f"{fam}: margin after the variance per unit completed", round(f["m_unit"], 9), look("MarginPerUnit"),
                1e-9, PCT1)
        b.check(t, f"{fam}: margin with the year's variance", round(f["m_year"], 9), look("MarginYear"), 1e-9, PCT1)
        b.check(t, f"{fam}: purchased products' margin at standard",
                round(f["m_purch"], 9) if f["m_purch"] is not None else "none", look("PurchasedMargin"), 1e-9, PCT1)
    for g in m["groups"]:
        rr = gro[g["name"]]
        b.check(t, f"{g['name']}: revenue", round(g["rev"], 2), f"=Families!B{rr}", 0.01)
        b.check(t, f"{g['name']}: variance", round(g["variance"], 2), f"=Families!D{rr}", 0.01)
        for c, k, lab in (("F", "m_std", "at standard"), ("G", "m_unit", "after the variance per unit completed"),
                          ("H", "m_year", "with the year's variance")):
            b.check(t, f"{g['name']}: margin {lab}", round(g[k], 9), f"=Families!{c}{rr}", 1e-9, "0.00%")
    tt = m["totals"]
    b.check(t, "variance of the year's closes, all families", round(tt["total"], 2), "=FamilyVariance", 0.01)
    b.check(t, "account 5080 without the year-end closes", round(m["ledger_5080"], 2), "=" + rec[list(rec)[1]], 0.01)
    b.check(t, "difference between the families and 5080", 0, "=" + rec["Difference"], 0.005)
    b.check(t, "material variance", round(tt["material"], 2), "=" + rec["  of which material"], 0.01)
    b.check(t, "direct labor variance", round(tt["labor"], 2), "=" + rec["  of which direct labor"], 0.01)
    b.check(t, "overhead variance", round(tt["overhead"], 2), "=" + rec["  of which overhead"], 0.01)
    b.check(t, "closes of the year", tt["closes"], f"=Families!{col_letter(lo, 'Closes')}{b.found['fam_total_row']}", 0,
            COUNT)
    b.check(t, "manufactured families not sold in the base year", text_list(m["unsold"]),
            "=" + rec["Manufactured families not sold in the base year"], 0, "@")
    b.check(t, "purchased finished goods: cost to standard", round(m["p_total"], 9),
            "=" + pur["All purchased finished goods: cost to standard"], 1e-9, "0.000")
    b.check(t, "lowest purchase cost to standard", round(m["p_low"], 9), "=" + pur["  lowest order line"], 1e-9, "0.000")
    b.check(t, "highest purchase cost to standard", round(m["p_high"], 9), "=" + pur["  highest order line"], 1e-9, "0.000")
    for f, v in m["purchased"].items():
        b.check(t, f"{f}: purchased cost to list", round(v, 9),
                "=" + pur[f"{f}: purchased cost to list (the quote's calibration)"], 1e-9, "0.000")
    b.check(t, "invoice lines tested", m["lines"], "=Premises[InvoiceLines]", 0, COUNT)
    b.check(t, "invoice lines whose list price differs from the item's", m["mismatched"], "=Premises[ListPriceDiffers]", 0,
            COUNT)
    b.check(t, "shipment lines whose standard cost differs", m["ship_mismatch"], "=Premises[ShipmentCostDiffers]", 0,
            COUNT)
    b.check(t, "largest completion-line difference from units x standard cost", round(m["max_diff"], 9),
            "=Premises[LargestCompletionDifference]", 1e-9, "0.0000")
    b.check(t, "items sold in every year", m["all_years"], "=Premises[ItemsSoldEveryYear]", 0, COUNT)
    b.check(t, "Furniture: margin at standard less margin with the year's variance", round(g0["m_std"] - g0["m_year"], 9),
            "=" + prem[list(prem)[1]], 1e-9, "0.0%")
    b.check(t, "families that beat their purchased benchmark after the variance", text_list(beats),
            "=" + prem[list(prem)[2]], 0, "@")


# --- Requirement 2: take the overhead apart -----------------------------------------------------------------------

PAY_ROWS = [("Direct labor, regular earnings", "Regular Earnings", "Direct Manufacturing"),
            ("Direct labor, overtime earnings", "Overtime Earnings", "Direct Manufacturing"),
            ("Indirect labor, regular earnings", "Regular Earnings", "Indirect Manufacturing"),
            ("Indirect labor, overtime earnings", "Overtime Earnings", "Indirect Manufacturing"),
            ("Salaries", "Salary Earnings", None),
            ("Employer payroll tax", "Employer Payroll Tax", None),
            ("Employer benefits", "Employer Benefits", None)]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December"]


def pay_dates(d: Data) -> list[str]:
    """The months whose 1090 debits carry three payroll dates (Python's own count of the PayrollSummary postings)."""
    seen = defaultdict(set)
    for day, in d.q("SELECT g.PostingDate FROM GLEntry g WHERE g.AccountID = ? AND g.SourceDocumentType = 'PayrollSummary'",
                    d.account(1090)):
        seen[day[:7]].add(day)
    return sorted(mo for mo, days in seen.items() if len(days) == 3 and mo <= f"{d.C}-12")


def r2(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    ws = sheet(b, "Cost Behavior")
    title(ws, f"Requirement 2: the overhead taken apart (inputs to 1090, fiscal {d.C})",
          "The inputs are the PayrollSummary, Factory Overhead, and Depreciation debits to 1090; the debits that "
          "favorable closes post back to it are left out.")
    heading(ws, 4, "Pasted from MakeBuy.sql")
    paste(b, ws, "A5", "payroll", "PayrollLines", formats={"Hours": HOURS, "Amount": MONEY})
    paste(b, ws, "F5", "debits1090", "Debits1090", formats={"Debits": MONEY})
    paste(b, ws, "A15", "released", "Released", formats={c: MONEY for c in ("StandardHours", "Material", "DirectLabor",
                                                                            "VariableOverhead", "FixedOverhead",
                                                                            "Conversion", "CreditsTo1090")})
    r = 19
    header(ws, r, ["Input to 1090", "Hours", "Amount", "Per standard hour", "Behavior (the evidence is below)"])
    behavior = {"Direct labor, regular earnings": "Committed: the crew's pay (payroll does not move with output)",
                "Direct labor, overtime earnings": "Committed: surge-day overtime, scheduled, not driven by output",
                "Indirect labor, regular earnings": "Committed: the crew's time with no work order",
                "Indirect labor, overtime earnings": "Committed",
                "Salaries": "Committed: supervision",
                "Employer payroll tax": "Committed: follows the payroll it is charged on",
                "Employer benefits": "Committed: follows the payroll it is charged on"}
    for i, (label, line_type, labor) in enumerate(PAY_ROWS):
        rr = r + 1 + i
        crit = f'PayrollLines[LineType],"{line_type}"' + (f',PayrollLines[LaborType],"{labor}"' if labor else "")
        ws.Cells(rr, 1).Value = label
        if labor:
            ws.Range(f"B{rr}").Formula = f"=SUMIFS(PayrollLines[Hours],{crit})"
        ws.Range(f"C{rr}").Formula = f"=SUMIFS(PayrollLines[Amount],{crit})"
        ws.Range(f"E{rr}").Value = behavior[label]
    p0, p1 = r + 1, r + len(PAY_ROWS)
    rows = {"payroll": p1 + 1, "foh": p1 + 2, "dep": p1 + 3, "total": p1 + 4, "ledger": p1 + 5, "diff": p1 + 6}
    ws.Cells(rows["payroll"], 1).Value = "Payroll to 1090"
    ws.Range(f"C{rows['payroll']}").Formula = f"=SUM(C{p0}:C{p1})"
    ws.Cells(rows["foh"], 1).Value = "Factory Overhead entries"
    ws.Range(f"C{rows['foh']}").Formula = '=SUMIFS(Debits1090[Debits],Debits1090[Source],"Factory Overhead")'
    ws.Range(f"E{rows['foh']}").Value = "Varies with output, at about the rate the standards apply"
    ws.Cells(rows["dep"], 1).Value = "Depreciation entries"
    ws.Range(f"C{rows['dep']}").Formula = '=SUMIFS(Debits1090[Debits],Debits1090[Source],"Depreciation")'
    ws.Range(f"E{rows['dep']}").Value = "Neither: follows the asset schedule (a committed capacity cost)"
    ws.Cells(rows["total"], 1).Value = "Total inputs to 1090"
    ws.Range(f"C{rows['total']}").Formula = f"=C{rows['payroll']}+C{rows['foh']}+C{rows['dep']}"
    ws.Cells(rows["ledger"], 1).Value = "PayrollSummary debits to 1090 (the ledger)"
    ws.Range(f"C{rows['ledger']}").Formula = '=SUMIFS(Debits1090[Debits],Debits1090[Source],"PayrollSummary")'
    ws.Cells(rows["diff"], 1).Value = "Payroll registers less the ledger"
    ws.Range(f"C{rows['diff']}").Formula = f"=C{rows['payroll']}-C{rows['ledger']}"
    for rr in list(range(p0, p1 + 1)) + [rows["payroll"], rows["foh"], rows["dep"], rows["total"]]:
        ws.Range(f"D{rr}").Formula = f"=C{rr}/StdHours"
    ws.Range(f"B{p0}:B{p1}").NumberFormat = HOURS
    ws.Range(f"C{p0}:C{rows['diff']}").NumberFormat = MONEY
    ws.Range(f"D{p0}:D{rows['total']}").NumberFormat = MONEY
    bold(ws, f"A{rows['payroll']}:D{rows['payroll']}")
    bold(ws, f"A{rows['total']}:D{rows['total']}")
    wb = b.wb
    for name, key in (("PayrollTo1090", "payroll"), ("FactoryOverhead", "foh"), ("Depreciation1090", "dep"),
                      ("Inputs1090", "total")):
        wb.Names.Add(Name=name, RefersTo="=" + ref(ws, f"C{rows[key]}"))
    b.found["r2rows"] = rows

    r = rows["diff"] + 2
    heading(ws, r, "Released at standard by the year's completions, against the actual inputs")
    rel = lines(ws, r + 1, [
        ("Standard labor hours completed", "=Released[StandardHours]", MONEY, "StdHours"),
        ("Direct labor released", "=Released[DirectLabor]", MONEY),
        ("Variable overhead released", "=Released[VariableOverhead]", MONEY),
        ("Fixed overhead released", "=Released[FixedOverhead]", MONEY),
        ("Overhead applied (variable plus fixed)", "=Released[VariableOverhead]+Released[FixedOverhead]", MONEY,
         "AppliedOverhead"),
        ("Conversion released (completion lines)", "=Released[Conversion]", MONEY, "ConversionReleased"),
        ("ProductionCompletion credits to 1090 (the ledger)", "=Released[CreditsTo1090]", MONEY),
        ("Conversion released per standard hour", "=ConversionReleased/StdHours", MONEY),
        ("  of which direct labor", "=Released[DirectLabor]/StdHours", MONEY),
        ("  of which overhead", "=AppliedOverhead/StdHours", MONEY),
        ("Actual inputs per standard hour", "=Inputs1090/StdHours", MONEY),
        ("Direct earnings (regular and overtime)", f"=C{p0}+C{p0 + 1}", MONEY, "DirectEarnings"),
        ("Actual overhead: the inputs less the direct earnings", "=Inputs1090-DirectEarnings", MONEY, "ActualOverhead"),
        ("Actual overhead per standard hour", "=ActualOverhead/StdHours", MONEY),
        ("Actual overhead as a multiple of the overhead applied", "=ActualOverhead/AppliedOverhead", "0.00"),
        ("Overhead applied as a share of actual overhead (the CFO's \"a third\")", "=AppliedOverhead/ActualOverhead",
         "0.00")])
    b.found["rel2"] = rel
    r += len(rel) + 3

    heading(ws, r, "The inputs by month, with the standard hours completed (pasted from MakeBuy.sql)")
    mon = paste(b, ws, f"A{r + 1}", "monthly", "Monthly", text=("Month",), formats={
        "StandardHours": MONEY, "AppliedOverhead": MONEY, "FactoryOverhead": MONEY, "Payroll": MONEY,
        "Depreciation": MONEY, "PayDates": "0"})
    top = r + 1
    k = 10                                   # column J: the tests
    J = col(k)
    heading(ws, top, f"Cost behavior: each input regressed on the standard hours completed, {MONTH_NAMES[1]} {d.F} to "
                     f"December {d.C}", col=J)
    test = lines(ws, top + 1, [("First month of the test (the start-up month is left out)", "=INDEX(Monthly[Month],2)",
                                None, "TestFrom")], col=J)
    header(ws, top + 3, ["Input", "Slope (per standard hour)", "Intercept (a month)", "r", "R Square", "Months"], col=k)
    x = "FILTER(Monthly[StandardHours],Monthly[Month]>=TestFrom)"
    fits = [("Factory Overhead entries", "FactoryOverhead", x), ("Payroll to 1090", "Payroll", x),
            ("Depreciation entries", "Depreciation", x),
            ("Payroll to 1090, the start-up month included", "Payroll", "Monthly[StandardHours]")]
    fit_rows = {}
    for i, (label, c, xs) in enumerate(fits):
        rr = top + 4 + i
        ys = f"FILTER(Monthly[{c}],Monthly[Month]>=TestFrom)" if xs == x else f"Monthly[{c}]"
        ws.Cells(rr, k).Value = label
        for j, f in enumerate((f"=SLOPE({ys},{xs})", f"=INTERCEPT({ys},{xs})", f"=CORREL({xs},{ys})",
                               f"=RSQ({ys},{xs})", f"=COUNT({xs})")):
            ws.Cells(rr, k + 1 + j).Formula2 = f
        fit_rows[label] = rr
    ws.Range(f"{col(k + 1)}{top + 4}:{col(k + 2)}{top + 7}").NumberFormat = MONEY
    ws.Range(f"{col(k + 3)}{top + 4}:{col(k + 4)}{top + 7}").NumberFormat = "0.000"
    r = top + 9
    header(ws, r, ["Year", "Factory Overhead entries", "Overhead applied", "Ratio"], col=k)
    ratio_rows = {}
    for i, y in enumerate(d.years):
        rr = r + 1 + i
        ws.Cells(rr, k).Value = y
        ws.Cells(rr, k + 1).Formula = f'=SUMIFS(Monthly[FactoryOverhead],Monthly[Month],{J}{rr}&"-*")'
        ws.Cells(rr, k + 2).Formula = f'=SUMIFS(Monthly[AppliedOverhead],Monthly[Month],{J}{rr}&"-*")'
        ws.Cells(rr, k + 3).Formula = f"={col(k + 1)}{rr}/{col(k + 2)}{rr}"
        ratio_rows[y] = rr
    ws.Range(f"{col(k + 1)}{r + 1}:{col(k + 2)}{r + 3}").NumberFormat = MONEY
    ws.Range(f"{col(k + 3)}{r + 1}:{col(k + 3)}{r + 3}").NumberFormat = "0.000"
    r += len(d.years) + 2
    header(ws, r, [f"Depreciation charged to 1090 in {d.C}", "A month"], col=k)
    dep_rows = []
    for i, run in enumerate(m["runs"]):
        rr = r + 1 + i
        first, last_ = MONTH_NAMES[run["first"]], MONTH_NAMES[run["last"]]
        ws.Cells(rr, k).Value = first if first == last_ else f"{first} to {last_}"
        ws.Cells(rr, k + 1).Formula = f'=XLOOKUP(BaseYear&"-{run["first"] + 1:02d}",Monthly[Month],Monthly[Depreciation])'
        ws.Cells(rr, k + 1).NumberFormat = MONEY
        dep_rows.append(rr)
    r += len(m["runs"]) + 2
    three = lines(ws, r, [("Months whose 1090 debits carry three payroll dates",
                           '=TEXTJOIN(", ",TRUE,FILTER(Monthly[Month],Monthly[PayDates]=3,"none"))', None)], col=J)
    chart = ws.Shapes.AddChart2(-1, xl.XL_XY_SCATTER, ws.Range(f"{J}{r + 2}").Left, ws.Range(f"{J}{r + 2}").Top,
                                480, 288).Chart
    while chart.SeriesCollection().Count:
        chart.SeriesCollection(1).Delete()
    for name, c in (("Factory Overhead entries", "FactoryOverhead"), ("Payroll to 1090", "Payroll")):
        s = chart.SeriesCollection().NewSeries()
        s.Name = name
        s.XValues = mon.ListColumns("StandardHours").DataBodyRange
        s.Values = mon.ListColumns(c).DataBodyRange
    chart.HasTitle = True
    chart.ChartTitle.Text = "Inputs to 1090 against the standard hours completed, by month"
    for axis, text in ((1, "Standard hours completed"), (2, "Debits to 1090")):
        chart.Axes(axis).HasTitle = True
        chart.Axes(axis).AxisTitle.Text = text
    b.found["r2"] = dict(fit_rows=fit_rows, ratio_rows=ratio_rows, dep_rows=dep_rows, three=three, J=J, k=k)

    fo, pay, dep, ps = (m["fits"][x] for x in ("fo", "pay", "dep", "pay_start"))
    applied = m["var_oh"] + m["fixed_oh"]
    actual_oh = m["inputs"] - m["direct"]
    runs = m["runs"]
    months3 = pay_dates(d)
    answer(ws, mon.Range.Row + mon.Range.Rows.Count + 2, [
        f"Per standard hour, the year's inputs cost {m['inputs'] / m['stdh']:.2f} against the {m['conversion'] / m['stdh']:.2f} "
        f"the standards released ({m['labor'] / m['stdh']:.2f} labor, {applied / m['stdh']:.2f} overhead). Actual overhead, "
        f"the inputs less the direct earnings, is {actual_oh:,.2f}, {actual_oh / m['stdh']:.2f} a standard hour and "
        f"{actual_oh / applied:.2f} times what the standards applied: the CFO's \"a third\" is {applied / actual_oh:.2f}.",
        f"Factory Overhead entries vary with output: over the {len(m['months'])} months from {MONTH_NAMES[1]} {d.F}, "
        f"r = {fo['r']:.3f} (R Square {fo['r2']:.3f}), with a slope of {fo['slope']:.2f} a standard hour, about the rate the "
        f"standards apply, and they run at {m['fo_ratio'][0]:.3f}, {m['fo_ratio'][1]:.3f}, and {m['fo_ratio'][2]:.3f} of "
        "the overhead applied in each year. They are the overhead that varies, and the standards already cover them.",
        f"Payroll to 1090 (direct and indirect labor, regular and overtime, salaries, employer tax, and benefits) does not "
        f"move with output: r = {pay['r']:.3f}, R Square {pay['r2']:.3f}, an intercept of {pay['intercept']:,.0f} a month "
        f"and a slope of {pay['slope']:.2f}. It is a committed capacity cost: the crew and supervision are paid for their "
        f"hours whatever the plant completes. Salaries are committed by contract; employer tax and benefits follow the "
        f"payroll they are charged on.",
        f"Depreciation is neither: it follows the asset schedule ({runs[0]['amount']:,.2f} a month, then "
        + ", then ".join(f"{x['amount']:,.2f} from {MONTH_NAMES[x['first']]}" for x in runs[1:])
        + f" {d.C}), and its r of {dep['r']:.3f} is spurious, a coincidence of the schedule's steps with output.",
        f"January {d.F}, the start-up month, has a full month of costs on almost no output; with it, payroll appears to "
        f"move with output (r = {ps['r']:.3f}), an artifact, so the test starts in {MONTH_NAMES[1]}. Payroll posts on its "
        f"pay dates, so the months with three pay dates ({series(months3)}) carry a third payroll with no more output: "
        "they add noise to a monthly test of payroll and would inflate any month's cost per unit; testing by pay period, "
        "or leaving those months out, removes it.",
        "Conclusion: the gap between the inputs and the standards is not variable overhead the standards miss. It is the "
        "crew and supervision, which do not move with output, plus depreciation, spread over a plant that runs well "
        "below its capacity. The question is what the committed capacity is for."], last_col="H")
    ws.Columns("A").ColumnWidth = 44
    ws.Columns("B:D").ColumnWidth = 15
    ws.Columns("E").ColumnWidth = 40
    ws.Columns("F:I").ColumnWidth = 14
    ws.Columns(J).ColumnWidth = 44
    ws.Columns(f"{col(k + 1)}:{col(k + 5)}").ColumnWidth = 15

    t = "Requirement 2"
    pay_amount = {lab: m["pay"].get((lt, lb), (0.0, 0.0)) for lab, lt, lb in PAY_ROWS}
    for i, (label, line_type, labor) in enumerate(PAY_ROWS):
        rr = r0 = 20 + i
        h, a = pay_amount[label]
        b.check(t, f"{label}: amount", round(a, 2), f"='Cost Behavior'!C{rr}", 0.01)
        if labor:
            b.check(t, f"{label}: hours", round(h, 4), f"='Cost Behavior'!B{rr}", 0.005, HOURS)
    b.check(t, "payroll to 1090", round(sum(a for h, a in m["pay"].values()), 2), "=PayrollTo1090", 0.01)
    b.check(t, "payroll registers less the PayrollSummary debits to 1090", 0, f"='Cost Behavior'!C{rows['diff']}", 0.005)
    b.check(t, "Factory Overhead entries", round(m["foh"], 2), "=FactoryOverhead", 0.01)
    b.check(t, "Depreciation entries", round(m["dep"], 2), "=Depreciation1090", 0.01)
    b.check(t, "total inputs to 1090", round(m["inputs"], 2), "=Inputs1090", 0.01)
    labels = list(rel)
    b.check(t, "standard labor hours completed", round(m["stdh"], 4), "=StdHours", 0.0005)
    b.check(t, "direct labor released", round(m["labor"], 2), "=" + rel[labels[1]], 0.01)
    b.check(t, "variable overhead released", round(m["var_oh"], 2), "=" + rel[labels[2]], 0.01)
    b.check(t, "fixed overhead released", round(m["fixed_oh"], 2), "=" + rel[labels[3]], 0.01)
    b.check(t, "conversion released (completion lines)", round(m["conversion"], 2), "=ConversionReleased", 0.01)
    b.check(t, "ProductionCompletion credits to 1090", round(m["released_gl"], 2), "=" + rel[labels[6]], 0.01)
    b.check(t, "conversion released per standard hour", round(m["conversion"] / m["stdh"], 9), "=" + rel[labels[7]], 1e-9)
    b.check(t, "  of which labor", round(m["labor"] / m["stdh"], 9), "=" + rel[labels[8]], 1e-9)
    b.check(t, "  of which overhead", round(applied / m["stdh"], 9), "=" + rel[labels[9]], 1e-9)
    b.check(t, "actual inputs per standard hour", round(m["inputs"] / m["stdh"], 9), "=" + rel[labels[10]], 1e-9)
    b.check(t, "direct earnings", round(m["direct"], 2), "=DirectEarnings", 0.01)
    b.check(t, "actual overhead (inputs less direct earnings)", round(actual_oh, 2), "=ActualOverhead", 0.01)
    b.check(t, "actual overhead per standard hour", round(actual_oh / m["stdh"], 9), "=" + rel[labels[13]], 1e-9)
    b.check(t, "actual overhead as a multiple of applied", round(actual_oh / applied, 9), "=" + rel[labels[14]], 1e-9,
            "0.00")
    b.check(t, "overhead applied as a share of actual (the CFO's \"a third\")", round(applied / actual_oh, 9),
            "=" + rel[labels[15]], 1e-9, "0.00")
    kk = b.found["r2"]["k"]
    for label, key in (("Factory Overhead entries", "fo"), ("Payroll to 1090", "pay"), ("Depreciation entries", "dep"),
                       ("Payroll to 1090, the start-up month included", "pay_start")):
        rr, f = fit_rows[label], m["fits"][key]
        if key in ("fo", "pay"):
            b.check(t, f"{label}: slope", round(f["slope"], 9), f"='Cost Behavior'!{col(kk + 1)}{rr}", 1e-6)
            b.check(t, f"{label}: intercept", round(f["intercept"], 6), f"='Cost Behavior'!{col(kk + 2)}{rr}", 1e-4)
            b.check(t, f"{label}: R Square", round(f["r2"], 9), f"='Cost Behavior'!{col(kk + 4)}{rr}", 1e-9, "0.000")
        b.check(t, f"{label}: r", round(f["r"], 9), f"='Cost Behavior'!{col(kk + 3)}{rr}", 1e-9, "0.000")
    b.check(t, "months in the test", len(m["months"]), f"='Cost Behavior'!{col(kk + 5)}{fit_rows['Factory Overhead entries']}",
            0, COUNT)
    for y, ratio in zip(d.years, m["fo_ratio"]):
        b.check(t, f"Factory Overhead entries over overhead applied, {y}", round(ratio, 9),
                f"='Cost Behavior'!{col(kk + 3)}{ratio_rows[y]}", 1e-9, "0.000")
    for rr, run in zip(dep_rows, runs):
        b.check(t, f"depreciation a month from {MONTH_NAMES[run['first']]} {d.C}", round(run["amount"], 2),
                f"='Cost Behavior'!{col(kk + 1)}{rr}", 0.005)
    b.check(t, "months with three payroll dates", text_list(months3), "=" + three[list(three)[0]], 0, "@")


# --- Requirement 3: activities and capacity ------------------------------------------------------------------------

def centers(b: ExerciseBuild) -> list[tuple[int, str, str]]:
    """The work centers: (WorkCenterID, name without "Work Center", short name used in column names)."""
    return [(w, n.removesuffix(" Work Center"), wc_short(n))
            for w, n in data(b).q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter ORDER BY WorkCenterID")]


def r3(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    wcs = centers(b)
    ws = sheet(b, "Activities")
    title(ws, f"Requirement 3: what each family uses of the plant, and what the plant had (fiscal {d.C})",
          "Routing time (run hours per unit times the units completed, plus setup hours per work order) on the year's "
          "completions; available hours from WorkCenterCalendar.")
    fmts = {"WorkOrders": COUNT, "UnitsCompleted": UNITS, "IssueLines": COUNT}
    fmts.update({f"{s}{k}": "#,##0.00" for _, _, s in wcs for k in ("Run", "Setup")})
    lo = paste(b, ws, "A4", "activity", "Activity", formats=fmts)
    s0, s1 = wcs[0][2], wcs[-1][2]
    add_cols(lo, [("Batch", "=[@UnitsCompleted]/[@WorkOrders]", "0.0"),
                  ("RunHours", f"=SUM(Activity[@[{s0}Run]:[{s1}Run]])", MONEY),
                  ("SetupHours", f"=SUM(Activity[@[{s0}Setup]:[{s1}Setup]])", MONEY),
                  ("SetupPer1000Units", "=[@SetupHours]/[@UnitsCompleted]*1000", "0.0"),
                  ("IssueLinesPer1000Units", "=[@IssueLines]/[@UnitsCompleted]*1000", "0.0")])
    r = 5 + lo.ListRows.Count + 2
    heading(ws, r, "By item group")
    header(ws, r + 1, ["Group", "Units completed", "Work orders", "Average batch (units)", "Setup hours per 1,000 units",
                       "Issue lines per 1,000 units", "Run hours", "Setup hours"])
    grow = {}
    for i, a in enumerate(m["activities"]):
        rr = r + 2 + i
        ws.Cells(rr, 1).Value = a["name"]
        c = f"Activity[ItemGroup],$A{rr}"
        formulas(ws, {f"B{rr}": f"=SUMIFS(Activity[UnitsCompleted],{c})", f"C{rr}": f"=SUMIFS(Activity[WorkOrders],{c})",
                      f"D{rr}": f"=B{rr}/C{rr}", f"E{rr}": f"=H{rr}/B{rr}*1000",
                      f"F{rr}": f"=SUMIFS(Activity[IssueLines],{c})/B{rr}*1000",
                      f"G{rr}": f"=SUMIFS(Activity[RunHours],{c})", f"H{rr}": f"=SUMIFS(Activity[SetupHours],{c})"})
        grow[a["name"]] = rr
    last = r + 1 + len(m["activities"])
    ws.Range(f"B{r + 2}:B{last}").NumberFormat = UNITS
    ws.Range(f"C{r + 2}:C{last}").NumberFormat = COUNT
    ws.Range(f"D{r + 2}:F{last}").NumberFormat = "0.0"
    ws.Range(f"G{r + 2}:H{last}").NumberFormat = MONEY
    r = last + 2
    tot = lines(ws, r, [("Run hours on the year's completions", "=SUM(Activity[RunHours])", MONEY, "RunHoursUsed"),
                        ("Standard labor hours completed (Cost Behavior)", "=StdHours", MONEY),
                        ("Setup hours on the year's completions", "=SUM(Activity[SetupHours])", MONEY, "SetupHoursUsed"),
                        ("Routing time used", "=RunHoursUsed+SetupHoursUsed", MONEY, "UsedHours")])
    r += 6
    heading(ws, r, "Hours available (pasted from MakeBuy.sql)")
    paste(b, ws, f"A{r + 1}", "calendar", "Calendar", formats={"AvailableHours": MONEY, "WorkingDays": "0"})
    b.wb.Worksheets("Assumptions").Range(b.found["assumption_rows"]["WorkingDays"].split("!")[1]).Formula = \
        "=XLOOKUP(MIN(Calendar[WorkCenterID]),Calendar[WorkCenterID],Calendar[WorkingDays])"
    r += len(wcs) + 3
    heading(ws, r, "Capacity and its use")
    header(ws, r + 1, ["Work center", "Available hours", "Practical capacity", "Routing time used", "Share of available",
                       "Share of practical"])
    cap = {}
    for i, (w, name, s) in enumerate(wcs):
        rr = r + 2 + i
        ws.Cells(rr, 1).Value = name
        formulas(ws, {f"B{rr}": f"=XLOOKUP({w},Calendar[WorkCenterID],Calendar[AvailableHours])",
                      f"C{rr}": f"=B{rr}*PracticalShare", f"D{rr}": f"=SUM(Activity[{s}Run],Activity[{s}Setup])",
                      f"E{rr}": f"=D{rr}/B{rr}", f"F{rr}": f"=D{rr}/C{rr}"})
        cap[s] = rr
    rp = r + 2 + len(wcs)
    ws.Cells(rp, 1).Value = "Plant"
    for c in "BCD":
        ws.Range(f"{c}{rp}").Formula = f"=SUM({c}{r + 2}:{c}{rp - 1})"
    formulas(ws, {f"E{rp}": f"=D{rp}/B{rp}", f"F{rp}": f"=D{rp}/C{rp}"})
    bold(ws, f"A{rp}:F{rp}")
    ws.Range(f"B{r + 2}:D{rp}").NumberFormat = MONEY
    ws.Range(f"E{r + 2}:F{rp}").NumberFormat = PCT1
    cap["Plant"] = rp
    b.found["cap_rows"] = cap
    answer(ws, rp + 3, [
        "Routing time is the right measure of what each family uses, because it is what the products should take: the "
        "time actually recorded drifted toward packing and quality assurance and was often recorded after the operation "
        f"had ended (Part III). Run hours on the year's completions equal the standard labor hours ({m['run_total']:,.2f}); "
        f"setup adds {m['setup_total']:,.2f}, and Furniture's small batches carry about twice the setup per unit of the "
        "other groups.",
        "What routing time leaves out is the indirect time and the hours paid beyond the work that Part III found. The plant "
        f"used {m['used'] / m['pract']:.1%} of its practical capacity ({m['used'] / m['avail']:.1%} of the available "
        "hours) on routing time; the rest is unused capacity, which is exactly where those hours belong in Requirement 4."],
        last_col="H")
    ws.Columns("A").ColumnWidth = 30
    ws.Columns("B:Z").ColumnWidth = 13

    t = "Requirement 3"
    for a in m["activities"]:
        rr = grow[a["name"]]
        b.check(t, f"{a['name']}: units completed", round(a["units"], 4), f"=Activities!B{rr}", 0.005, UNITS)
        b.check(t, f"{a['name']}: work orders", a["wos"], f"=Activities!C{rr}", 0, COUNT)
        b.check(t, f"{a['name']}: average batch", round(a["batch"], 9), f"=Activities!D{rr}", 1e-9, "0.0")
        b.check(t, f"{a['name']}: setup hours per 1,000 units", round(a["setup"], 9), f"=Activities!E{rr}", 1e-9, "0.0")
        b.check(t, f"{a['name']}: issue lines per 1,000 units", round(a["issues"], 9), f"=Activities!F{rr}", 1e-9, "0.0")
    b.check(t, "run hours on the year's completions", round(m["run_total"], 4), "=RunHoursUsed", 0.0005)
    b.check(t, "run hours less the standard labor hours", 0, "=RunHoursUsed-StdHours", 0.0005)
    b.check(t, "setup hours", round(m["setup_total"], 4), "=SetupHoursUsed", 0.0005)
    b.check(t, "routing time used", round(m["used"], 4), "=UsedHours", 0.0005)
    for c in m["centers"]:
        rr = cap[c["short"]]
        b.check(t, f"{c['name']}: available hours", round(c["avail"], 2), f"=Activities!B{rr}", 0.005)
        b.check(t, f"{c['name']}: practical capacity", round(c["pract"], 4), f"=Activities!C{rr}", 0.005)
        b.check(t, f"{c['name']}: routing time used", round(c["used"], 4), f"=Activities!D{rr}", 0.0005)
        b.check(t, f"{c['name']}: share of available", round(c["of_avail"], 9), f"=Activities!E{rr}", 1e-9, PCT1)
        b.check(t, f"{c['name']}: share of practical", round(c["of_pract"], 9), f"=Activities!F{rr}", 1e-9, PCT1)
    b.check(t, "plant: available hours", round(m["avail"], 2), f"=Activities!B{rp}", 0.005)
    b.check(t, "plant: practical capacity", round(m["pract"], 4), f"=Activities!C{rp}", 0.005)
    b.check(t, "plant: share of available", round(m["used"] / m["avail"], 9), f"=Activities!E{rp}", 1e-9, PCT1)
    b.check(t, "plant: share of practical", round(m["used"] / m["pract"], 9), f"=Activities!F{rp}", 1e-9, PCT1)
    b.check(t, "working days in the base year (Assumptions)", m["working_days"], "=WorkingDays", 0, "0")
    b.check(t, "practical hours of one position (Assumptions)", round(m["pos_hours"], 6), "=PositionHours", 1e-6, HOURS)


# --- Requirement 4: three costs for each family --------------------------------------------------------------------

FAM_COLS = [("Units", "Units sold (manufactured items)", UNITS), ("Price", "Price per unit at the base-year mix", MONEY),
            ("Standard", "Standard cost", MONEY), ("Absorption", "Actual absorption cost", MONEY),
            ("TimeDriven", "Time-driven cost", MONEY), ("MarginStandard", "Margin at standard", PCT1),
            ("MarginAbsorption", "Margin, actual absorption", PCT1), ("MarginTimeDriven", "Margin, time-driven", PCT1),
            ("MaterialAtActual", "Material at the actual rate", MONEY), ("Kept", "Relevant cost, crew kept", MONEY),
            ("Reduced", "Relevant cost, crew reduced", MONEY), ("RoutingTime", "Routing time per unit (hours)", "0.0000"),
            ("Between", "Standard < time-driven < absorption", None)]


def famref(name: str) -> str:
    """The defined name of a column of the family summary on Costs (FamCostUnits, FamCostTimeDriven, ...)."""
    return f"FamCost{name}"


def r4(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    wcs = centers(b)
    # From here on the workbook holds Data Tables, which recalculate the whole item model on every edit; build with
    # "automatic except tables" (a full calculation still computes them, as the build's CalculateFull does) and
    # restore automatic calculation in the last step, so the saved file calculates as usual.
    b.wb.Application.Calculation = CALC_EXCEPT_TABLES
    ws = sheet(b, "Costs")
    title(ws, f"Requirement 4: three costs for each family (fiscal {d.C})",
          "Standard: the item's standard cost. Actual absorption: standard plus the family's variance per unit "
          "completed. Time-driven: material at the actual rate, the Factory Overhead entries per standard hour, and the "
          "committed cost of the crew, supervision, and equipment per hour of practical capacity, times the routing time "
          "per unit (setup spread over the family's average batch).")
    heading(ws, 3, "The committed capacity cost (pasted from MakeBuy.sql)")
    pc = paste(b, ws, "A4", "payclass", "PayClass", formats={"GrossPay": MONEY, "EmployerTax": MONEY, "Benefits": MONEY})
    add_cols(pc, [("Total", "=[@GrossPay]+[@EmployerTax]+[@Benefits]", MONEY)])
    r = 5 + pc.ListRows.Count + 1
    heading(ws, r, "The time-driven rate")
    rate = lines(ws, r + 1, [
        ("Hourly crew: every hourly manufacturing employee, with employer tax and benefits",
         '=SUMIFS(PayClass[Total],PayClass[PayClass],"Hourly")', MONEY, "CrewCost"),
        ("Salaried production staff (supervision), with employer tax and benefits",
         '=SUMIFS(PayClass[Total],PayClass[PayClass],"Salary")', MONEY, "SalariedCost"),
        ("Depreciation charged to 1090 (equipment)", "=Depreciation1090", MONEY),
        ("Committed capacity cost", "=CrewCost+SalariedCost+Depreciation1090", MONEY, "CommittedCost"),
        ("Available hours (WorkCenterCalendar)", "=SUM(Calendar[AvailableHours])", MONEY, "AvailableHours"),
        ("Practical capacity used by the model (the Assumptions value; the Data Table below changes it)",
         "=PracticalShare", PCT1, "PracticalUsed"),
        ("Practical hours", "=AvailableHours*PracticalUsed", MONEY, "PracticalHours"),
        ("Time-driven rate: committed cost per practical hour", "=CommittedCost/PracticalHours", RATE4, "TDRate"),
        ("  of which the crew", "=CrewCost/PracticalHours", RATE4, "CrewRate"),
        ("  of which supervision and equipment", "=TDRate-CrewRate", RATE4, "SupportRate"),
        ("Factory Overhead entries per standard hour (the overhead that varies)", "=FactoryOverhead/StdHours", RATE4,
         "FORate"),
        ("Material variance rate: the year's material variance over the standard material completed",
         "=SUM(FamilyResults[MaterialVariance])/Released[Material]", "0.000%", "MaterialVarianceRate")])
    practical_cell = rate["PracticalUsed"].split("!")[1]
    note(ws, practical_cell, "A Data Table's input cell must be on the Data Table's own worksheet, so the model reads "
                             "the Assumptions value through this cell, and the Data Table below substitutes 75% to 90% "
                             "into it.")
    r += 14
    heading(ws, r, "Products and unused capacity, reconciled to the inputs to 1090")
    recon = lines(ws, r + 1, [
        ("Routing time used (Activities)", "=UsedHours", MONEY),
        ("Products' conversion: routing time at the time-driven rate, plus the Factory Overhead entries",
         "=UsedHours*TDRate+FactoryOverhead", MONEY, "ProductsConversion"),
        ("Unused capacity: practical hours not used", "=PracticalHours-UsedHours", MONEY, "UnusedHours"),
        ("Unused capacity cost, a cost of the plant (not of the products)", "=UnusedHours*TDRate", MONEY, "UnusedCost"),
        ("  of which the crew", "=UnusedHours*CrewRate", MONEY),
        ("Products plus unused capacity", "=ProductsConversion+UnusedCost", MONEY),
        ("Inputs to 1090 (Cost Behavior)", "=Inputs1090", MONEY),
        ("Difference", "=ProductsConversion+UnusedCost-Inputs1090", MONEY)])

    # The Table of item costs (the hand-off to Power BI): calculated columns on the ItemCosts query
    ic = xl.table(b.wb, "ItemCosts")
    specs = [
        ("Costed", '=AND([@SupplyMode]="Manufactured",ISNUMBER([@RoutingID]),ISNUMBER(XMATCH([@Family],Activity[Family])))'),
        ("Batch", '=IF([@Costed],XLOOKUP([@Family],Activity[Family],Activity[Batch]),"")', "0.0"),
        ("Material", "=[@StandardCost]-[@StandardConversionCost]", MONEY),
        ("VariancePerUnit", "=IF([@Costed],XLOOKUP([@Family],FamilyResults[Family],FamilyResults[VariancePerUnit],0),0)",
         MONEY),
        ("RoutingTime", '=IF([@Costed],[@RunHours]+[@SetupHours]/[@Batch],"")', "0.0000"),
        ("MaterialAtActual", '=IF([@Costed],[@Material]*(1+MaterialVarianceRate),"")', MONEY),
        ("CostKept", '=IF([@Costed],[@MaterialAtActual]+FORate*[@StandardLaborHoursPerUnit],"")', MONEY),
        ("CostReduced", '=IF([@Costed],[@CostKept]+CrewRate*[@RoutingTime],"")', MONEY),
        ("AbsorptionCost", "=IF([@Costed],[@StandardCost]+[@VariancePerUnit],[@StandardCost])", MONEY),
        ("TimeDrivenCost", "=IF([@Costed],[@CostKept]+TDRate*[@RoutingTime],[@StandardCost])", MONEY)]
    for w, name, s in wcs:
        hours = (f"SUMIFS(RoutingHours[RunHours],RoutingHours[RoutingID],[@RoutingID],RoutingHours[WorkCenterID],{w})+"
                 f"SUMIFS(RoutingHours[SetupHours],RoutingHours[RoutingID],[@RoutingID],RoutingHours[WorkCenterID],{w})"
                 "/[@Batch]")
        specs.append((f"{s}Hours", f"=IF([@Costed],{hours},0)", "0.0000"))
    specs += [("MarginStandard", "=[@Revenue]-[@Units]*[@StandardCost]", MONEY),
              ("MarginAbsorption", "=[@Revenue]-[@Units]*[@AbsorptionCost]", MONEY),
              ("MarginTimeDriven", "=[@Revenue]-[@Units]*[@TimeDrivenCost]", MONEY)]
    add_cols(ic, specs)
    note(ic.Parent, "A1", "ItemCosts: the finished goods (Item, through Power Query on CharlesRiver.xlsx) with their routing "
                          "hours and the base year's sales by item; the columns from Costed on are formulas. Purchased "
                          "items, and manufactured items with no routing or no completions in the base year, carry their "
                          "standard cost in every view. This Table is what Product Costs.pbix loads.", height=120)

    # Families at the base-year mix
    r += 11
    heading(ws, r, "By family, at the base-year mix of items sold (manufactured items only)")
    header(ws, r + 1, ["Family", "Group"] + [lab for _, lab, _ in FAM_COLS])
    f0 = r + 2
    fams = sorted(m["fam"])
    for i, f in enumerate(fams):
        rr = f0 + i
        ws.Cells(rr, 1).Value = f
        mask = f'(ItemCosts[Family]=$A{rr})*(ItemCosts[SupplyMode]="Manufactured")'
        formulas(ws, {f"B{rr}": f"=XLOOKUP($A{rr},FamilyResults[Family],FamilyResults[ItemGroup])",
                      f"C{rr}": f"=SUMPRODUCT({mask}*ItemCosts[Units])",
                      f"D{rr}": f"=SUMPRODUCT({mask},ItemCosts[Revenue])/C{rr}"})
        for j, c in enumerate(("StandardCost", "AbsorptionCost", "TimeDrivenCost")):
            ws.Cells(rr, 5 + j).Formula2 = f"=SUMPRODUCT({mask}*ItemCosts[Units],ItemCosts[{c}])/$C{rr}"
        formulas(ws, {f"H{rr}": f"=1-E{rr}/$D{rr}", f"I{rr}": f"=1-F{rr}/$D{rr}", f"J{rr}": f"=1-G{rr}/$D{rr}"})
        for j, c in enumerate(("MaterialAtActual", "CostKept", "CostReduced", "RoutingTime")):
            ws.Cells(rr, 11 + j).Formula2 = f"=SUMPRODUCT({mask}*ItemCosts[Units],ItemCosts[{c}])/$C{rr}"
        ws.Range(f"O{rr}").Formula = f"=AND(E{rr}<G{rr},G{rr}<F{rr})"
    f1 = f0 + len(fams) - 1
    for j, (name, _, fmt) in enumerate(FAM_COLS):
        c = col(3 + j)
        if fmt:
            ws.Range(f"{c}{f0}:{c}{f1}").NumberFormat = fmt
        b.wb.Names.Add(Name=famref(name), RefersTo="=" + ref(ws, f"{c}{f0}:{c}{f1}"))
    b.wb.Names.Add(Name=famref("Family"), RefersTo="=" + ref(ws, f"A{f0}:A{f1}"))
    b.found["fam_rows"] = {f: f0 + i for i, f in enumerate(fams)}
    r = f1 + 2
    heading(ws, r, "By item group")
    header(ws, r + 1, ["Group", "Revenue", "Margin at standard", "Margin, actual absorption", "Margin, time-driven"])
    grp = {}
    for i, g in enumerate(m["groups"]):
        rr = r + 2 + i
        ws.Cells(rr, 1).Value = g["name"]
        sel = f"($B${f0}:$B${f1}=$A{rr})*$C${f0}:$C${f1}"
        ws.Range(f"B{rr}").Formula2 = f"=SUMPRODUCT({sel}*$D${f0}:$D${f1})"
        for j, c in enumerate("EFG"):
            ws.Cells(rr, 3 + j).Formula2 = f"=1-SUMPRODUCT({sel}*${c}${f0}:${c}${f1})/B{rr}"
        grp[g["name"]] = rr
    b.found["td_group_rows"] = grp
    ws.Range(f"B{r + 2}:B{r + 1 + len(m['groups'])}").NumberFormat = MONEY
    ws.Range(f"C{r + 2}:E{r + 1 + len(m['groups'])}").NumberFormat = "0.00%"
    r += len(m["groups"]) + 3
    heading(ws, r, "The top fifth of the finished goods sold (all finished goods, purchased ones at standard)")
    top_f = ('=LET(m,FILTER(ItemCosts[{c}],ItemCosts[Units]>0),n,ROUND(ROWS(m)*0.2,0),SUM(LARGE(m,SEQUENCE(n)))/SUM(m))')
    low_f = ('=LET(k,FILTER(HSTACK(ItemCosts[ItemCode],ItemCosts[{c}]/ItemCosts[Revenue]),ItemCosts[Units]>0),'
             'INDEX(SORTBY(k,INDEX(k,,2),1),1,{i}))')
    tops = lines(ws, r + 1, [
        ("Finished goods sold", '=COUNTIFS(ItemCosts[Units],">0")', COUNT, "ItemsSold"),
        ("The top fifth (items)", "=ROUND(ItemsSold*0.2,0)", COUNT),
        ("Share of margin the top fifth earns: standard", top_f.format(c="MarginStandard"), PCT1),
        ("  actual absorption", top_f.format(c="MarginAbsorption"), PCT1),
        ("  time-driven", top_f.format(c="MarginTimeDriven"), PCT1),
        ("Items that lose money under any view",
         '=COUNTIFS(ItemCosts[Units],">0",ItemCosts[MarginStandard],"<0")+COUNTIFS(ItemCosts[Units],">0",'
         'ItemCosts[MarginAbsorption],"<0")+COUNTIFS(ItemCosts[Units],">0",ItemCosts[MarginTimeDriven],"<0")', COUNT),
        ("Lowest margin under actual absorption: item", low_f.format(c="MarginAbsorption", i=1), None),
        ("  its margin", low_f.format(c="MarginAbsorption", i=2), PCT1)])
    r += 10
    heading(ws, r, "Data Table: practical capacity from 75% to 90% of the available hours")
    ex_row = b.found["fam_rows"][EXAMPLE]
    header(ws, r + 1, ["Practical capacity", "Time-driven rate", "Unused capacity cost",
                       f"{EXAMPLE} time-driven cost per unit"])
    t0 = r + 2
    formulas(ws, {f"B{t0}": "=TDRate", f"C{t0}": "=UnusedCost", f"D{t0}": f"=G{ex_row}"})
    for i, share in enumerate(DATA_TABLE):
        ws.Cells(t0 + 1 + i, 1).Value = share
    ws.Range(f"A{t0}:D{t0 + len(DATA_TABLE)}").Table(None, ws.Range(practical_cell))
    settle(b)
    ws.Range(f"A{t0 + 1}:A{t0 + len(DATA_TABLE)}").NumberFormat = "0%"
    ws.Range(f"B{t0}:B{t0 + len(DATA_TABLE)}").NumberFormat = MONEY
    ws.Range(f"C{t0}:C{t0 + len(DATA_TABLE)}").NumberFormat = COUNT
    ws.Range(f"D{t0}:D{t0 + len(DATA_TABLE)}").NumberFormat = MONEY
    ws.Range(f"A{t0}").Value = "(current)"
    blue(ws, f"A{t0 + 1}:A{t0 + len(DATA_TABLE)}")
    note(ws, f"A{t0}", f"Data > What-If Analysis > Data Table, column input cell {practical_cell} (Practical capacity used "
                       "by the model).")
    dt_rows = {share: t0 + 1 + i for i, share in enumerate(DATA_TABLE)}
    r = t0 + len(DATA_TABLE) + 2
    e = m["explorer"]
    fl = m["fam"]
    near_std = [g["name"] for g in m["groups"]
                if sum((f["unit"]["td"] - f["unit"]["std"]) * f["units"] for f in fl.values() if f["group"] == g["name"])
                < sum((f["unit"]["absorp"] - f["unit"]["td"]) * f["units"] for f in fl.values() if f["group"] == g["name"])]
    near_abs = [g["name"] for g in m["groups"] if g["name"] not in near_std]
    dt = m["data_table"]
    tops_m = e["tops"]
    paras = [
        f"The committed capacity cost is {m['committed']:,.2f}: the hourly crew {m['crew']:,.2f} "
        f"({m['pclass']['Hourly']['n']} employees), the salaried staff {m['sal']:,.2f}, and depreciation {m['dep']:,.2f}. "
        f"Over {m['pract']:,.1f} practical hours it costs {m['td_rate']:.2f} an hour ({m['crew_rate']:.2f} for the crew). "
        f"The products' routing time and the Factory Overhead entries absorb {m['used'] * m['td_rate'] + m['foh']:,.2f}; "
        f"the {m['unused_h']:,.1f} practical hours left unused cost {m['unused_h'] * m['td_rate']:,.2f}, and the two add up "
        f"to the {m['inputs']:,.2f} that flowed into 1090.",
        "Time-driven cost lies between standard and actual absorption for every family: the products cost more than "
        "their standards say (the standards miss the labor rate's increase, supervision, and depreciation) but less than "
        "absorption says, because idle capacity is not theirs. It sits nearer standard for "
        f"{series(near_std) or 'no group'} and nearer absorption for {series(near_abs) or 'no group'}. Group margins on "
        + ", ".join(f"{g['name']} {g['m_td']:.2%}" for g in m["groups"]) + " time-driven.",
        f"The top fifth of the {e['n_items']} finished goods sold ({e['top_n']} items) earns {tops_m['std']['share']:.1%} "
        f"of the margin at standard, {tops_m['absorp']['share']:.1%} under absorption, and {tops_m['td']['share']:.1%} "
        f"time-driven; no item loses money under any view (the lowest under absorption is {tops_m['absorp']['low']}, "
        f"{tops_m['absorp']['low_margin']:.1%}).",
        f"The Data Table shows what moves. From {DATA_TABLE[0]:.0%} to {DATA_TABLE[-1]:.0%} of available hours, the rate "
        f"falls from {dt[0]['rate']:.2f} to {dt[-1]['rate']:.2f} and the unused capacity rises from {dt[0]['unused']:,.0f} "
        f"to {dt[-1]['unused']:,.0f}, while {EXAMPLE}'s cost moves only from {dt[0]['example']:.2f} to "
        f"{dt[-1]['example']:.2f}: the product costs move by a few dollars, the unused capacity by hundreds of thousands. "
        "The choice of practical capacity decides how much of the plant's cost is reported as idle, not what the products "
        "cost."]
    answer(ws, r, paras, last_col="J")
    b.found["costs_next"] = r + len(paras) + 2
    ws.Columns("A").ColumnWidth = 40
    ws.Columns("B:O").ColumnWidth = 14

    t = "Requirement 4"
    hourly, salary = m["pclass"]["Hourly"], m["pclass"]["Salary"]
    b.check(t, "hourly crew: employees paid", hourly["n"], '=XLOOKUP("Hourly",PayClass[PayClass],PayClass[Employees])', 0,
            COUNT)
    b.check(t, "hourly crew: every hourly manufacturing employee on record", hourly["n"],
            '=XLOOKUP("Hourly",PayClass[PayClass],PayClass[EmployeesOnRecord])', 0, COUNT)
    b.check(t, "hourly crew: gross pay", round(hourly["gross"], 2),
            '=XLOOKUP("Hourly",PayClass[PayClass],PayClass[GrossPay])', 0.01)
    b.check(t, "hourly crew: employer tax", round(hourly["tax"], 2),
            '=XLOOKUP("Hourly",PayClass[PayClass],PayClass[EmployerTax])', 0.01)
    b.check(t, "hourly crew: benefits", round(hourly["benefits"], 2),
            '=XLOOKUP("Hourly",PayClass[PayClass],PayClass[Benefits])', 0.01)
    b.check(t, "hourly crew, with employer costs", round(m["crew"], 2), "=CrewCost", 0.01)
    b.check(t, "salaried staff: employees", salary["n"], '=XLOOKUP("Salary",PayClass[PayClass],PayClass[Employees])', 0,
            COUNT)
    b.check(t, "salaried staff: gross pay", round(salary["gross"], 2),
            '=XLOOKUP("Salary",PayClass[PayClass],PayClass[GrossPay])', 0.01)
    b.check(t, "salaried staff, with employer costs", round(m["sal"], 2), "=SalariedCost", 0.01)
    b.check(t, "committed capacity cost", round(m["committed"], 2), "=CommittedCost", 0.01)
    b.check(t, "practical hours", round(m["pract"], 4), "=PracticalHours", 0.0005)
    b.check(t, "time-driven rate", round(m["td_rate"], 9), "=TDRate", 1e-9, RATE4)
    b.check(t, "  of which the crew", round(m["crew_rate"], 9), "=CrewRate", 1e-9, RATE4)
    b.check(t, "  of which supervision and equipment", round(m["td_rate"] - m["crew_rate"], 9), "=SupportRate", 1e-9,
            RATE4)
    b.check(t, "Factory Overhead per standard hour", round(m["fo_rate"], 9), "=FORate", 1e-9, RATE4)
    b.check(t, "material variance rate", round(m["mv_rate"], 12), "=MaterialVarianceRate", 1e-12, "0.000%")
    b.check(t, "products' conversion", round(m["used"] * m["td_rate"] + m["foh"], 2), "=ProductsConversion", 0.01)
    b.check(t, "unused capacity, hours", round(m["unused_h"], 4), "=UnusedHours", 0.0005, HOURS)
    b.check(t, "unused capacity cost", round(m["unused_h"] * m["td_rate"], 2), "=UnusedCost", 0.01)
    b.check(t, "  of which the crew", round(m["unused_h"] * m["crew_rate"], 2), "=" + recon[list(recon)[4]], 0.01)
    b.check(t, "products plus unused capacity", round(m["inputs"], 2), "=" + recon[list(recon)[5]], 0.01)
    b.check(t, "difference from the inputs to 1090", 0, "=" + recon[list(recon)[7]], 0.005)
    for f in fams:
        u, rr = m["fam"][f]["unit"], b.found["fam_rows"][f]
        b.check(t, f"{f}: price at the mix", round(u["price"], 6), f"=Costs!D{rr}", 1e-6)
        b.check(t, f"{f}: standard cost", round(u["std"], 6), f"=Costs!E{rr}", 1e-6)
        b.check(t, f"{f}: absorption cost", round(u["absorp"], 6), f"=Costs!F{rr}", 1e-6)
        b.check(t, f"{f}: time-driven cost", round(u["td"], 6), f"=Costs!G{rr}", 1e-6)
        b.check(t, f"{f}: time-driven margin", round(u["m_td"], 9), f"=Costs!J{rr}", 1e-9, PCT1)
    b.check(t, "families where standard < time-driven < absorption", len(fams), f"=COUNTIF(Costs!O{f0}:O{f1},TRUE)", 0,
            COUNT)
    for g in m["groups"]:
        b.check(t, f"{g['name']}: time-driven margin", round(g["m_td"], 9), f"=Costs!E{grp[g['name']]}", 1e-9, "0.00%")
    b.check(t, "finished goods sold", e["n_items"], "=ItemsSold", 0, COUNT)
    b.check(t, "the top fifth (items)", e["top_n"], "=" + tops[list(tops)[1]], 0, COUNT)
    for i, k in enumerate(("std", "absorp", "td")):
        b.check(t, f"share of margin the top fifth earns, {('standard', 'absorption', 'time-driven')[i]}",
                round(tops_m[k]["share"], 9), "=" + tops[list(tops)[2 + i]], 1e-9, PCT1)
    b.check(t, "items that lose money under any view", sum(tops_m[k]["negative"] for k in tops_m),
            "=" + tops[list(tops)[5]], 0, COUNT)
    b.check(t, "lowest margin under absorption: item", tops_m["absorp"]["low"], "=" + tops[list(tops)[6]], 0, "@")
    b.check(t, "lowest margin under absorption: margin", round(tops_m["absorp"]["low_margin"], 9),
            "=" + tops[list(tops)[7]], 1e-9, PCT1)
    for x in dt:
        rr = dt_rows[x["share"]]
        b.check(t, f"Data Table at {x['share']:.0%}: time-driven rate", round(x["rate"], 9), f"=Costs!B{rr}", 1e-9)
        b.check(t, f"Data Table at {x['share']:.0%}: unused capacity cost", round(x["unused"], 2), f"=Costs!C{rr}", 0.01,
                COUNT)
        b.check(t, f"Data Table at {x['share']:.0%}: {EXAMPLE} time-driven cost", round(x["example"], 6), f"=Costs!D{rr}",
                1e-6)


# --- Requirement 5: the totals the explorer's Tests tab compares with ------------------------------------------------

def r5(b: ExerciseBuild) -> None:
    m = ms(b)
    ws = b.wb.Worksheets("Costs")
    r = b.found["costs_next"]
    heading(ws, r, "Requirement 5: the totals the explorer's Tests tab checks against this workbook (the finished goods "
                   "sold, Services left out)")
    tot = lines(ws, r + 1, [
        ("Revenue", '=SUMIFS(ItemCosts[Revenue],ItemCosts[Units],">0")', MONEY, "ExplorerRevenue"),
        ("Standard cost of the units sold", "=SUMPRODUCT(ItemCosts[Units],ItemCosts[StandardCost])", MONEY),
        ("Margin at standard", "=SUM(ItemCosts[MarginStandard])", MONEY, "ExplorerMarginStandard"),
        ("Margin, actual absorption", "=SUM(ItemCosts[MarginAbsorption])", MONEY, "ExplorerMarginAbsorption"),
        ("Margin, time-driven", "=SUM(ItemCosts[MarginTimeDriven])", MONEY, "ExplorerMarginTimeDriven"),
        ("Margin, time-driven, after the unused capacity", "=ExplorerMarginTimeDriven-UnusedCost", MONEY),
        ("Margin at standard with the year's variance charged (the ledger's view)",
         "=ExplorerMarginStandard-SUM(FamilyResults[TotalVariance])", MONEY),
        ("What the standards miss: standard less time-driven margin",
         "=ExplorerMarginStandard-ExplorerMarginTimeDriven", MONEY),
        ("The idle capacity absorption charges: time-driven less absorption margin",
         "=ExplorerMarginTimeDriven-ExplorerMarginAbsorption", MONEY)])
    e = m["explorer"]
    answer(ws, r + 11, [
        "Product Costs.pbix loads the ItemCosts Table (one row per finished good, with StandardCost, AbsorptionCost, and "
        "TimeDrivenCost), relates it to the invoice lines on ItemID, and switches its Product Cost measure on the view a "
        "Costing View table selects. Its Tests tab compares each view's total margin with the totals above. Design "
        "services have no row in the Table, so the report shows them as a blank row to be left out, as Chapter 13 "
        f"taught: revenue without them is {e['rev']:,.2f}. The Power BI file itself is outside this workbook.",
        "These totals take the item costs unrounded; the CR18 reference model reads them from a CSV at six decimals, "
        "so its absorption margin can differ by a cent."], last_col="J")

    t = "Requirement 5"
    b.check(t, "finished goods revenue", round(e["rev"], 2), "=ExplorerRevenue", 0.01)
    b.check(t, "standard cost of the units sold (Chapter 14's figure)", round(e["std_cost"], 2), "=" + tot[list(tot)[1]],
            0.01)
    b.check(t, "margin at standard", round(e["std"], 2), "=ExplorerMarginStandard", 0.01)
    b.check(t, "margin, actual absorption (unrounded item costs)", round(e["absorp"], 2), "=ExplorerMarginAbsorption", 0.01)
    b.check(t, "margin, time-driven", round(e["td"], 2), "=ExplorerMarginTimeDriven", 0.01)
    b.check(t, "time-driven after the unused capacity", round(e["td_unused"], 2), "=" + tot[list(tot)[5]], 0.01)
    b.check(t, "with the year's variance charged", round(e["year"], 2), "=" + tot[list(tot)[6]], 0.01)
    b.check(t, "standard less time-driven margin", round(e["std"] - e["td"], 2), "=" + tot[list(tot)[7]], 0.01)
    b.check(t, "time-driven less absorption margin", round(e["td"] - e["absorp"], 2), "=" + tot[list(tot)[8]], 0.01)
    fam_tbl = m["fam"][EXAMPLE]
    b.check(t, f"{EXAMPLE}: margin at standard", round(fam_tbl["m_std"], 9), fam_lookup("FamilyResults", "MarginStandard",
                                                                                         EXAMPLE), 1e-9, PCT1)
    b.check(t, f"{EXAMPLE}: margin, actual absorption", round(fam_tbl["m_unit"], 9),
            f'=XLOOKUP("{EXAMPLE}",{famref("Family")},{famref("MarginAbsorption")})', 1e-9, PCT1)
    b.check(t, f"{EXAMPLE}: margin, time-driven", round(fam_tbl["unit"]["m_td"], 9),
            f'=XLOOKUP("{EXAMPLE}",{famref("Family")},{famref("MarginTimeDriven")})', 1e-9, PCT1)


# --- Requirement 6: make or buy, family by family -----------------------------------------------------------------

MB = dict(first=10)          # the Make or Buy table's first row
MB_COLS = ["Family", "Description", "Units sold, base year", "Quoted annual volume", "Quoted volume against sales",
           "Quoted price", "Delivered quote (price plus freight)", "Actual absorption cost", "Relevant cost, crew kept",
           "Relevant cost, crew reduced", "Routing time per unit (hours)", "Effect of buying a year: absorption view",
           "Effect of buying a year: crew kept", "Effect of buying a year: crew reduced", "Decision",
           "Buy (1) only with the crew reduced", "Break-even quote, crew kept", "Break-even quote, crew reduced",
           "Delivered margin at the base-year price", "Routing hours freed (base-year sales)", "Positions",
           "Effect at the sensitivity inputs", "Tooling and qualification"]


def mb(c: str, row: int | None = None, absolute: bool = True) -> str:
    """A cell or column range of the Make or Buy table: mb("N") -> 'Make or Buy'!$N$10:$N$15."""
    n = len(QUOTE)
    if row is not None:
        return f"'Make or Buy'!${c}${row}"
    return f"'Make or Buy'!${c}${MB['first']}:${c}${MB['first'] + n - 1}"


def r6(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    ws = sheet(b, "Make or Buy")
    title(ws, "Requirement 6: make or buy, family by family",
          "Relevant cost with the crew kept: material at the actual rate plus the overhead that varies (Factory Overhead "
          "per standard hour). With the crew reduced in step with the hours freed, add the crew's cost of the routing "
          "time. The annual effect of buying is the cost that stops less the delivered quote, at base-year volume.")
    heading(ws, 4, "Sensitivity inputs (the two-way Data Table below changes them; they stay at 0% and 100%)")
    sens = lines(ws, 5, [("Quote adjustment", 0, "0%", "QuoteAdjustment"),
                         ("Share of the freed crew time actually removed", 1, "0%", "CrewRemoved")])
    blue(ws, "B5:B6")
    first = MB["first"]
    header(ws, first - 1, MB_COLS)
    families = list(QUOTE)
    for i, f in enumerate(families):
        rr = first + i
        ws.Cells(rr, 1).Value = f
        fam = f"$A{rr}"
        formulas(ws, {
            f"B{rr}": f"=XLOOKUP({fam},Quote[Family],Quote[Description])",
            f"C{rr}": f"=XLOOKUP({fam},{famref('Family')},{famref('Units')})",
            f"D{rr}": f"=XLOOKUP({fam},Quote[Family],Quote[QuotedVolume])",
            f"E{rr}": f"=D{rr}/C{rr}-1",
            f"F{rr}": f"=XLOOKUP({fam},Quote[Family],Quote[Price])",
            f"G{rr}": f"=F{rr}*(1+Freight)",
            f"H{rr}": f"=XLOOKUP({fam},{famref('Family')},{famref('Absorption')})",
            f"I{rr}": f"=XLOOKUP({fam},{famref('Family')},{famref('Kept')})",
            f"J{rr}": f"=XLOOKUP({fam},{famref('Family')},{famref('Reduced')})",
            f"K{rr}": f"=XLOOKUP({fam},{famref('Family')},{famref('RoutingTime')})",
            f"L{rr}": f"=(H{rr}-G{rr})*C{rr}",
            f"M{rr}": f"=(I{rr}-G{rr})*C{rr}",
            f"N{rr}": f"=(J{rr}-G{rr})*C{rr}",
            f"O{rr}": f'=IF(M{rr}>0,"Buy",IF(N{rr}>0,"Buy only with the crew reduced","Make"))',
            f"P{rr}": f"=--(N{rr}>0)",
            f"Q{rr}": f"=I{rr}/(1+Freight)",
            f"R{rr}": f"=J{rr}/(1+Freight)",
            f"S{rr}": f"=1-G{rr}/XLOOKUP({fam},{famref('Family')},{famref('Price')})",
            f"T{rr}": f"=K{rr}*C{rr}",
            f"U{rr}": f"=T{rr}/PositionHours",
            f"V{rr}": f"=(I{rr}+CrewRemoved*CrewRate*K{rr}-F{rr}*(1+QuoteAdjustment)*(1+Freight))*C{rr}",
            f"W{rr}": f"=XLOOKUP({fam},Quote[Family],Quote[Tooling])"})
    last = first + len(families) - 1
    for c, fmt in (("C", UNITS), ("D", COUNT), ("E", PCT1), ("F", MONEY), ("G", MONEY), ("H", MONEY), ("I", MONEY),
                   ("J", MONEY), ("K", "0.0000"), ("L", COUNT), ("M", COUNT), ("N", COUNT), ("Q", MONEY), ("R", MONEY),
                   ("S", PCT1), ("T", COUNT), ("U", "0.00"), ("V", COUNT), ("W", COUNT)):
        ws.Range(f"{c}{first}:{c}{last}").NumberFormat = fmt
    ws.Rows(first - 1).RowHeight = 60

    # Goal Seek: the quote at which buying breaks even, under each crew case
    g = last + 3
    heading(ws, g - 1, "Break-even quotes by Goal Seek (set the annual effect to 0 by changing the quote)")
    header(ws, g, ["Family", "Quote, crew kept (Goal Seek's changing cell)", "Annual effect at that quote, crew kept",
                   "Quote, crew reduced (Goal Seek's changing cell)", "Annual effect at that quote, crew reduced"])
    gs = {}
    for i, f in enumerate(families):
        rr, src = g + 1 + i, first + i
        ws.Cells(rr, 1).Value = f
        ws.Range(f"B{rr}").Value = QUOTE[f][2]
        ws.Range(f"D{rr}").Value = QUOTE[f][2]
        formulas(ws, {f"C{rr}": f"=(I{src}-B{rr}*(1+Freight))*C{src}", f"E{rr}": f"=(J{src}-D{rr}*(1+Freight))*C{src}"})
        gs[f] = rr
    b.wb.Application.Calculate()
    for f, rr in gs.items():
        settle(b)
        xl.retry(lambda r_=rr: ws.Range(f"C{r_}").GoalSeek(0, ws.Range(f"B{r_}")))
        settle(b)
        xl.retry(lambda r_=rr: ws.Range(f"E{r_}").GoalSeek(0, ws.Range(f"D{r_}")))
    settle(b)
    ws.Range(f"B{g + 1}:E{g + len(families)}").NumberFormat = MONEY
    for c in ("B", "D"):
        ws.Range(f"{c}{g + 1}:{c}{g + len(families)}").Interior.Color = AMBER
    note(ws, f"B{g}", "Goal Seek (Data > What-If Analysis > Goal Seek), run for each family and crew case when the "
                      "solution was built: Set cell C (or E) To value 0 By changing cell B (or D). The results stay in the "
                      "changing cells, as Goal Seek leaves them; columns Q and R of the table above compute the same "
                      "quotes directly (relevant cost / (1 + freight)).", height=140)

    # The families to buy
    r = g + len(families) + 2
    heading(ws, r, "The families to buy, only with the crew reduced")
    tot = lines(ws, r + 1, [
        ("Families", f'=TEXTJOIN(", ",TRUE,FILTER({mb("A")},{mb("P")}=1,"none"))', None, "BuyFamilies"),
        ("Annual effect, crew reduced", f"=SUMPRODUCT({mb('P')},{mb('N')})", COUNT, "BuyGain"),
        ("Annual effect if they are bought and the crew is kept", f"=SUMPRODUCT({mb('P')},{mb('M')})", COUNT, "BuyKept"),
        ("Routing hours freed (base-year sales)", f"=SUMPRODUCT({mb('P')},{mb('T')})", COUNT, "BuyHours"),
        ("Positions no longer needed", "=BuyHours/PositionHours", "0.00", "BuyPositions"),
        ("Severance per position (Assumptions)", "=SeverancePerPosition", MONEY),
        ("Severance", "=BuyPositions*SeverancePerPosition", COUNT, "BuySeverance"),
        ("Tooling and qualification", f"=SUMPRODUCT({mb('P')},{mb('W')})", COUNT, "BuyTooling"),
        ("Effect over the two years the prices are fixed", "=PriceYears*BuyGain-BuySeverance-BuyTooling", COUNT,
         "BuyTwoYears"),
        ("Families the CFO's absorption view would buy", f'=COUNTIF({mb("L")},">0")', COUNT),
        ("Families to make under either crew case",
         f'=TEXTJOIN(", ",TRUE,FILTER({mb("A")},({mb("M")}<=0)*({mb("N")}<=0),"none"))', None),
        ("Largest gap between a quoted volume and base-year sales", f"=MAX(ABS({mb('E')}))", PCT1)])
    r += 14
    heading(ws, r, "Two-way Data Table: the families above together, with the quote 10% either side (across) and the "
                   "share of the freed crew time removed (down)")
    t0 = r + 1
    ws.Range(f"A{t0}").Formula = f"=SUMPRODUCT({mb('P')},{mb('V')})"
    for j, adj in enumerate(TWO_WAY_QUOTE):
        ws.Cells(t0, 2 + j).Value = adj
    for i, share in enumerate(TWO_WAY_CREW):
        ws.Cells(t0 + 1 + i, 1).Value = share
    ws.Range(f"A{t0}:{col(1 + len(TWO_WAY_QUOTE))}{t0 + len(TWO_WAY_CREW)}").Table(
        ws.Range(sens["QuoteAdjustment"].split("!")[1]), ws.Range(sens["CrewRemoved"].split("!")[1]))
    settle(b)
    ws.Range(f"B{t0}:D{t0}").NumberFormat = "+0%;-0%;0%"
    ws.Range(f"A{t0 + 1}:A{t0 + 3}").NumberFormat = "0%"
    ws.Range(f"B{t0 + 1}:D{t0 + 3}").NumberFormat = "+#,##0;-#,##0"
    ws.Range(f"A{t0}").NumberFormat = "+#,##0;-#,##0"
    blue(ws, f"B{t0}:D{t0}")
    blue(ws, f"A{t0 + 1}:A{t0 + 3}")
    note(ws, f"A{t0}", "Data > What-If Analysis > Data Table: row input cell B5 (Quote adjustment), column input cell B6 "
                       "(Share of the freed crew time removed).")
    tw = {(share, adj): (t0 + 1 + i, col(2 + j)) for i, share in enumerate(TWO_WAY_CREW)
          for j, adj in enumerate(TWO_WAY_QUOTE)}
    r = t0 + len(TWO_WAY_CREW) + 2
    fams_txt = ",".join(f"'{f}'" for f in m["buy_names"])
    heading(ws, r, "What the numbers leave out: the materials of the Part IV case (pasted from MakeBuy.sql)")
    paste(b, ws, f"A{r + 1}", "materials", "Materials", families=fams_txt, formats={
        "StandardMaterialCompleted": MONEY, "IssuedToTheirWorkOrders": MONEY, "OfWhichSixRawMaterials": MONEY,
        "AllIssues1045": MONEY})
    mat = lines(ws, r + 4, [("Share of the year's issues drawn by the families bought",
                             "=Materials[IssuedToTheirWorkOrders]/Materials[AllIssues1045]", PCT1)])
    r += 7
    q = {x["name"]: x for x in m["quoted"]}
    buy, lose = m["buy"], m["lose"]
    absorp_buy = [x["short"] for x in m["quoted"] if x["absorp"] > 0]
    kept_cost = -sum(x["a_kept"] for x in buy)
    paras = [
        f"Buy {series([x['short'] for x in buy])} only with the crew reduced: together they save {m['gain']:,.0f} a year, "
        f"free {m['hours']:,.0f} routing hours ({m['positions']:.2f} positions of {m['pos_hours']:,.1f} hours), and cost "
        f"{m['positions'] * m['severance']:,.0f} of severance and {m['tooling']:,.0f} of tooling, a net of about "
        f"{2 * m['gain'] - m['positions'] * m['severance'] - m['tooling']:,.0f} over the two years the prices are fixed. With "
        f"the crew kept, buying them costs {kept_cost:,.0f} a year, because the quote replaces only materials and the "
        f"overhead that varies. Make {series([x['short'] for x in lose])}: they lose under either crew case.",
        f"The CFO's absorption view would buy {len(absorp_buy)} of the {len(m['quoted'])} families. The two disagree "
        "because absorption cost includes supervision, depreciation, and the crew's idle hours, which do not stop when a "
        "family is bought, while relevant cost counts only the costs that stop; if a family goes and those costs stay, "
        "they fall on the families that remain and invite the next decision to buy.",
        f"What the numbers leave out: the 80% minimum (the quoted volumes are within {max(abs(x['volume'] / x['units'] - 1) for x in m['quoted']):.0%} "
        "of base-year sales, family by family), quality and the 1.5% defect threshold, lead time and the inventory it "
        "requires, the designs and bills of material shared with a supplier, the price risk after two years, and the "
        f"materials stock of the Part IV case: the families bought used {m['buy_material']:,.2f} of standard material in "
        f"their completions, and their work orders drew {m['fam_issued']:,.2f}, {m['fam_issued'] / m['issues']:.0%} of the "
        f"year's issues, of which {m['six_issued']:,.0f} was the six raw materials that carry the build, so buying them "
        "slows its drawdown."]
    answer(ws, r, paras, last_col="O")
    ws.Columns("A").ColumnWidth = 34
    ws.Columns("B:W").ColumnWidth = 14

    t = "Requirement 6"
    for i, f in enumerate(families):
        x, rr = q[f], first + i
        cell = lambda c: f"='Make or Buy'!{c}{rr}"
        b.check(t, f"{f}: delivered quote", round(x["delivered"], 6), cell("G"), 1e-6)
        b.check(t, f"{f}: relevant cost, crew kept", round(x["kept"], 6), cell("I"), 1e-6)
        b.check(t, f"{f}: relevant cost, crew reduced", round(x["reduced"], 6), cell("J"), 1e-6)
        b.check(t, f"{f}: annual effect, absorption view", round(x["absorp"], 2), cell("L"), 0.01, COUNT)
        b.check(t, f"{f}: annual effect, crew kept", round(x["a_kept"], 2), cell("M"), 0.01, COUNT)
        b.check(t, f"{f}: annual effect, crew reduced", round(x["a_reduced"], 2), cell("N"), 0.01, COUNT)
        b.check(t, f"{f}: break-even quote, crew kept (direct)", round(x["be_kept"], 6), cell("Q"), 1e-6)
        b.check(t, f"{f}: break-even quote, crew reduced (direct)", round(x["be_reduced"], 6), cell("R"), 1e-6)
        b.check(t, f"{f}: break-even quote, crew kept (Goal Seek)", round(x["be_kept"], 4), f"='Make or Buy'!B{gs[f]}",
                0.005)
        b.check(t, f"{f}: break-even quote, crew reduced (Goal Seek)", round(x["be_reduced"], 4),
                f"='Make or Buy'!D{gs[f]}", 0.005)
        decision = "Buy" if x["a_kept"] > 0 else ("Buy only with the crew reduced" if x["a_reduced"] > 0 else "Make")
        b.check(t, f"{f}: decision", decision, cell("O"), 0, "@")
        b.check(t, f"{f}: delivered margin at the base-year price", round(x["margin"], 9), cell("S"), 1e-9, PCT1)
    b.check(t, "families to buy, only with the crew reduced", ", ".join(m["buy_names"]), "=BuyFamilies", 0, "@")
    b.check(t, "annual effect, crew reduced", round(m["gain"], 2), "=BuyGain", 0.01, COUNT)
    b.check(t, "annual effect if bought with the crew kept", round(-kept_cost, 2), "=BuyKept", 0.01, COUNT)
    b.check(t, "routing hours freed (base-year sales)", round(m["hours"], 4), "=BuyHours", 0.0005, COUNT)
    b.check(t, "positions no longer needed", round(m["positions"], 9), "=BuyPositions", 1e-9, "0.00")
    b.check(t, "severance per position", round(m["severance"], 6), "=SeverancePerPosition", 1e-6)
    b.check(t, "severance", round(m["positions"] * m["severance"], 2), "=BuySeverance", 0.01, COUNT)
    b.check(t, "tooling and qualification", m["tooling"], "=BuyTooling", 0, COUNT)
    b.check(t, "effect over the two years", round(PRICE_YEARS * m["gain"] - m["positions"] * m["severance"] - m["tooling"], 2),
            "=BuyTwoYears", 0.01, COUNT)
    b.check(t, "families the absorption view would buy", len(absorp_buy), "=" + tot[list(tot)[9]], 0, COUNT)
    b.check(t, "families to make under either crew case", ", ".join(x["name"] for x in lose), "=" + tot[list(tot)[10]], 0,
            "@")
    b.check(t, "largest gap between quoted volume and sales", round(max(abs(x["volume"] / x["units"] - 1)
                                                                        for x in m["quoted"]), 9),
            "=" + tot[list(tot)[11]], 1e-9, PCT1)
    for i, share in enumerate(TWO_WAY_CREW):
        for j, adj in enumerate(TWO_WAY_QUOTE):
            rr, c = tw[(share, adj)]
            b.check(t, f"two-way Data Table: crew removed {share:.0%}, quote {adj:+.0%}", round(m["two_way"][i][j], 2),
                    f"='Make or Buy'!{c}{rr}", 0.01, COUNT)
    b.check(t, "standard material of the families' completions", round(m["buy_material"], 2),
            "=Materials[StandardMaterialCompleted]", 0.01)
    b.check(t, "materials issued to their work orders", round(m["fam_issued"], 2), "=Materials[IssuedToTheirWorkOrders]",
            0.01)
    b.check(t, "of which the six raw materials of the build", round(m["six_issued"], 2),
            "=Materials[OfWhichSixRawMaterials]", 0.01)
    b.check(t, "all the year's issues (1045)", round(m["issues"], 2), "=Materials[AllIssues1045]", 0.01)
    b.check(t, "share of the year's issues", round(m["fam_issued"] / m["issues"], 9), "=" + mat[list(mat)[0]], 1e-9, PCT1)


# --- Requirement 7: the capacity buying would free, and the optional Solver test ----------------------------------

def save_solver_min(ws, objective: str, variables: str, constraints: list[tuple[str, int, str]]) -> None:
    """ex07.save_solver_model for a model that minimizes (solver_typ 2): Solver keeps its model in hidden
    worksheet-level names, so Data > Solver opens this one ready to solve (Simplex LP, variables non-negative)."""
    sheet_ref = "'" + ws.Name.replace("'", "''") + "'"
    items = dict(SOLVER_DEFAULTS)
    items.update(solver_opt=f"{sheet_ref}!{objective}", solver_typ="2", solver_adj=f"{sheet_ref}!{variables}",
                 solver_eng="2", solver_num=str(len(constraints)))
    for i, (lhs, rel, rhs) in enumerate(constraints, start=1):
        items[f"solver_lhs{i}"] = f"{sheet_ref}!{lhs}"
        items[f"solver_rel{i}"] = str(rel)
        items[f"solver_rhs{i}"] = f"{sheet_ref}!{rhs}"
    for name, refers in items.items():
        ws.Names.Add(Name=name, RefersTo=f"={refers}", Visible=False)


def growth_name(g: float) -> str:
    return f"Growth {g:.0%}"


def r7(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    wcs = centers(b)
    ws = sheet(b, "Capacity")
    title(ws, "Requirement 7: the capacity that buying would free",
          "Freed hours are the routing time of the families bought on the base year's completions; the headroom compares "
          "practical capacity with the routing time the base year's sales need (setup over each family's average batch).")
    heading(ws, 4, f"Hours freed by buying {', '.join(m['buy_names'])} (the base year's completions)")
    header(ws, 5, ["Work center", "Routing time used", "Freed by buying", "Used after buying", "Practical capacity",
                   "Use of practical capacity, before", "Use of practical capacity, after"])
    freed_rows = {}
    for i, (w, name, s) in enumerate(wcs):
        rr, cr = 6 + i, b.found["cap_rows"][s]
        ws.Cells(rr, 1).Value = name
        formulas(ws, {f"B{rr}": f"=Activities!D{cr}",
                      f"C{rr}": f"=SUMPRODUCT(XLOOKUP(Activity[Family],{mb('A')},{mb('P')},0),"
                                f"Activity[{s}Run]+Activity[{s}Setup])",
                      f"D{rr}": f"=B{rr}-C{rr}", f"E{rr}": f"=Activities!C{cr}", f"F{rr}": f"=B{rr}/E{rr}",
                      f"G{rr}": f"=D{rr}/E{rr}"})
        freed_rows[w] = rr
    rp = 6 + len(wcs)
    ws.Cells(rp, 1).Value = "Plant"
    for c in "BCDE":
        ws.Range(f"{c}{rp}").Formula = f"=SUM({c}6:{c}{rp - 1})"
    formulas(ws, {f"F{rp}": f"=B{rp}/E{rp}", f"G{rp}": f"=D{rp}/E{rp}"})
    bold(ws, f"A{rp}:G{rp}")
    ws.Range(f"B6:E{rp}").NumberFormat = COUNT
    ws.Range(f"F6:G{rp}").NumberFormat = PCT1
    r = rp + 2
    heading(ws, r, "Against the capacity the plant already leaves unused")
    lines(ws, r + 1, [
        ("Practical hours already unused (Costs)", "=UnusedHours", HOURS),
        ("  in positions of the Assumptions' practical hours", "=UnusedHours/PositionHours", "0.00", "UnusedPositions"),
        ("Hours buying would free (the base year's completions, above)", f"=C{rp}", COUNT),
        ("Positions buying would free (the base year's sales, Make or Buy)", "=BuyPositions", "0.00")])
    r += 6
    heading(ws, r, "If the crew is kept")
    total_route = sum(f["unit"]["time"] * f["units"] for f in m["fam"].values())
    kept = lines(ws, r + 1, [
        ("Routing hours of the families bought (the base year's sales)", "=BuyHours", COUNT),
        ("The crew's cost of that time, which stays if the crew is kept", "=BuyHours*CrewRate", COUNT),
        ("The supervision and equipment that time carried", "=BuyHours*SupportRate", COUNT, "BuySupport"),
        ("Committed cost that stays", f"=B{r + 2}+B{r + 3}", COUNT),
        ("Routing hours of the remaining families (the base year's sales)",
         '=SUMPRODUCT((ItemCosts[SupplyMode]="Manufactured")*ItemCosts[Units],ItemCosts[RoutingTime])-BuyHours', COUNT),
        ("Added to each of their routing hours if it is spread over them (absorption)", f"=B{r + 4}/B{r + 5}", MONEY),
        ("Time-driven: unused capacity cost after buying", f"=UnusedCost+B{r + 4}", COUNT)])
    r += 9
    heading(ws, r, "Headroom for growth: practical capacity against the routing time the base year's sales need")
    header(ws, r + 1, ["Work center", "Practical capacity", "Load of the base year's sales", "Practical / load"])
    head_rows = {}
    for i, (w, name, s) in enumerate(wcs):
        rr = r + 2 + i
        ws.Cells(rr, 1).Value = name
        formulas(ws, {f"B{rr}": f"=E{freed_rows[w]}",
                      f"C{rr}": f'=SUMPRODUCT((ItemCosts[SupplyMode]="Manufactured")*ItemCosts[Units],ItemCosts[{s}Hours])',
                      f"D{rr}": f"=B{rr}/C{rr}"})
        head_rows[w] = rr
    last = r + 1 + len(wcs)
    ws.Range(f"B{r + 2}:C{last}").NumberFormat = COUNT
    ws.Range(f"D{r + 2}:D{last}").NumberFormat = "0.00"
    lines(ws, last + 1, [("Growth that reaches the first limit", f"=MIN(D{r + 2}:D{last})-1", PCT1, "FirstLimit")])
    b.found["head_rows"] = head_rows
    freed_total = sum(m["freed"].values())
    lp0, lp1 = m["lp"]
    bind = lambda s: series([m["centers"][k]["name"] for k in s["binding"]])
    paras = [
        f"Buying {series([x['short'] for x in m['buy']])} would free {freed_total:,.0f} routing hours on the base year's "
        "completions ("
        + ", ".join(f"{c['short']} {m['freed'][c['id']]:,.0f}" for c in m["centers"] if m["freed"][c["id"]] > 0.5)
        + f"), and the plant's use of its practical capacity would fall from {m['used'] / m['pract']:.1%} to "
        f"{(m['used'] - freed_total) / m['pract']:.1%}.",
        f"The plant already leaves {m['unused_h']:,.1f} practical hours unused, {m['unused_h'] / m['pos_hours']:.2f} "
        f"positions, more than buying would free ({m['positions']:.2f} positions). Fitting the crew to the work matters "
        "more than outsourcing. The production manager is right that idle capacity is not the products' fault, but the "
        "point cuts both ways: it is still a cost, and keeping the crew while buying adds to it.",
        f"If the crew is kept, the families bought take with them only materials and the overhead that varies; the crew's "
        f"time and the supervision and equipment that time carried (about {m['supervision']:,.0f}) stay. Under absorption "
        "they spread over the remaining families, whose cost per unit rises; under time-driven costing the remaining "
        "families' costs do not change and the unused capacity grows by the same amount.",
        "Optional growth test (Solver, sheets " + growth_name(GROWTH[0]) + " and " + growth_name(GROWTH[1]) + "): "
        f"practical capacity covers the base year's sales {min(m['headroom'].values()):.2f} times at the tightest work "
        f"center, so growth of about {min(m['headroom'].values()) - 1:.0%} reaches the first limit. At "
        f"+{GROWTH[0]:.0%}, {bind(lp0)} binds (an hour is worth about {lp0['shadow'][lp0['binding'][0]] * -1:.2f}) and "
        "Solver buys "
        + series([f"{x:,.0f} {short(q['name'])}" for q, x in zip(m["quoted"], lp0["bought"]) if x > 0.5])
        + f" at an added cost of about {lp0['cost']:,.0f}; at +{GROWTH[1]:.0%}, {bind(lp1)} binds (about "
        f"{lp1['shadow'][lp1['binding'][0]] * -1:.2f} an hour), and Solver buys "
        + series([f"{x:,.0f} {short(q['name'])}" for q, x in zip(m["quoted"], lp1["bought"]) if x > 0.5])
        + f" at about {lp1['cost']:,.0f}. Growth, not the base year, is when the quote becomes useful: as overflow "
        "capacity for the families with the smallest added cost."]
    answer(ws, last + 4, paras, last_col="G")
    ws.Columns("A").ColumnWidth = 62
    ws.Columns("B:G").ColumnWidth = 15

    t = "Requirement 7"
    for c in m["centers"]:
        b.check(t, f"{c['name']}: hours freed by buying", round(m["freed"][c["id"]], 4), f"=Capacity!C{freed_rows[c['id']]}",
                0.0005, COUNT)
    b.check(t, "hours freed, all work centers", round(freed_total, 4), f"=Capacity!C{rp}", 0.0005, COUNT)
    b.check(t, "use of practical capacity before buying", round(m["used"] / m["pract"], 9), f"=Capacity!F{rp}", 1e-9, PCT1)
    b.check(t, "use of practical capacity after buying", round((m["used"] - freed_total) / m["pract"], 9),
            f"=Capacity!G{rp}", 1e-9, PCT1)
    b.check(t, "practical hours already unused, in positions", round(m["unused_h"] / m["pos_hours"], 9),
            "=UnusedPositions", 1e-9, "0.00")
    b.check(t, "supervision and equipment the families bought carried", round(m["supervision"], 2), "=BuySupport", 0.01,
            COUNT)
    b.check(t, "routing hours of the remaining families", round(total_route - m["hours"], 4), "=" + kept[list(kept)[4]],
            0.0005, COUNT)
    for c in m["centers"]:
        b.check(t, f"{c['name']}: practical capacity over the base year's load", round(m["headroom"][c["id"]], 9),
                f"=Capacity!D{head_rows[c['id']]}", 1e-9, "0.00")
    b.check(t, "growth that reaches the first limit", round(min(m["headroom"].values()) - 1, 9), "=FirstLimit", 1e-9, PCT1)
    for k in range(len(GROWTH)):
        growth_sheet(b, k, t)


def growth_sheet(b: ExerciseBuild, k: int, t: str) -> None:
    m = ms(b)
    wcs = centers(b)
    s, g = m["lp"][k], GROWTH[k]
    name = growth_name(g)
    ws = sheet(b, name)
    rep = sheet(b, f"{name} Sensitivity")
    title(ws, f"Requirement 7 (optional): which quoted families to buy if volume grew by {g:.0%}",
          "Solver (Simplex LP) minimizes the added cost of buying, with the crew kept (the delivered quote less the "
          "relevant cost kept, per unit bought), keeping every work center within its practical capacity.")
    lines(ws, 3, [("Growth in volume (Assumptions)", f"={('GrowthLow', 'GrowthHigh')[k]}", PCT1)])
    header(ws, 5, ["Work center", "Practical capacity", "Load of the base year's sales", "Load at growth, nothing bought",
                   "Hours used after buying", "Slack", "Status", "Shadow price (Sensitivity report)",
                   "Value of an hour of capacity"])
    fam0 = 14
    n = len(QUOTE)
    for i, (w, wname, sh) in enumerate(wcs):
        rr = 6 + i
        hr = b.found["head_rows"][w]
        hcol = col(7 + i)
        ws.Cells(rr, 1).Value = wname
        formulas(ws, {f"B{rr}": f"=Capacity!B{hr}", f"C{rr}": f"=Capacity!C{hr}", f"D{rr}": f"=C{rr}*(1+$B$3)",
                      f"E{rr}": f"=D{rr}-SUMPRODUCT({hcol}${fam0}:{hcol}${fam0 + n - 1},$L${fam0}:$L${fam0 + n - 1})",
                      f"F{rr}": f"=B{rr}-E{rr}", f"G{rr}": f'=IF(F{rr}<=0.001,"Binding","Not binding")',
                      f"I{rr}": f"=-H{rr}"})
    w1 = 5 + len(wcs)
    ws.Range(f"B6:F{w1}").NumberFormat = COUNT
    ws.Range(f"H6:I{w1}").NumberFormat = MONEY
    header(ws, fam0 - 1, ["Family", "Base-year units", "Units at growth (the most that can be bought)", "Delivered quote",
                          "Relevant cost, crew kept", "Added cost per unit bought"]
           + [f"{wname} hours per unit" for _, wname, _ in wcs] + ["Units bought (variable cells)", "Added cost"])
    for j, f in enumerate(QUOTE):
        rr = fam0 + j
        ws.Cells(rr, 1).Value = f
        formulas(ws, {f"B{rr}": f"=XLOOKUP($A{rr},{mb('A')},{mb('C')})", f"C{rr}": f"=B{rr}*(1+$B$3)",
                      f"D{rr}": f"=XLOOKUP($A{rr},{mb('A')},{mb('G')})", f"E{rr}": f"=XLOOKUP($A{rr},{mb('A')},{mb('I')})",
                      f"F{rr}": f"=D{rr}-E{rr}", f"M{rr}": f"=L{rr}*F{rr}"})
        for i, (_, _, sh) in enumerate(wcs):
            ws.Cells(rr, 7 + i).Formula2 = (f'=SUMPRODUCT((ItemCosts[Family]=$A{rr})*(ItemCosts[SupplyMode]="Manufactured")'
                                            f"*ItemCosts[Units],ItemCosts[{sh}Hours])/$B{rr}")
    f1 = fam0 + n - 1
    ws.Range(f"L{fam0}:L{f1}").Value = tuple((x,) for x in s["bought"])
    ws.Range(f"L{fam0}:L{f1}").Interior.Color = AMBER
    blue(ws, f"L{fam0}:L{f1}")
    ws.Range(f"B{fam0}:C{f1}").NumberFormat = UNITS
    ws.Range(f"D{fam0}:F{f1}").NumberFormat = MONEY
    ws.Range(f"G{fam0}:K{f1}").NumberFormat = "0.0000"
    ws.Range(f"L{fam0}:L{f1}").NumberFormat = UNITS
    ws.Range(f"M{fam0}:M{f1}").NumberFormat = MONEY
    res = lines(ws, f1 + 2, [
        ("Total added cost (Solver's objective: minimize)", f"=SUM(M{fam0}:M{f1})", MONEY),
        ("Binding work centers", f'=TEXTJOIN(", ",TRUE,FILTER(A6:A{w1},G6:G{w1}="Binding","none"))', None),
        ("Families bought", f'=TEXTJOIN(", ",TRUE,FILTER(A{fam0}:A{f1},L{fam0}:L{f1}>0.5,"none"))', None),
        ("Every work center within its practical capacity", f"=AND(E6:E{w1}<=B6:B{w1}+0.001)", None),
        ("Every family bought within its units at growth", f"=AND(L{fam0}:L{f1}>=0,L{fam0}:L{f1}<=C{fam0}:C{f1}+0.001)",
         None)])
    obj = res[list(res)[0]].split("!")[1]
    save_solver_min(ws, obj, f"$L${fam0}:$L${f1}", [(f"$E$6:$E${w1}", 1, f"$B$6:$B${w1}"),
                                                    (f"$L${fam0}:$L${f1}", 1, f"$C${fam0}:$C${f1}")])
    note(ws, f"L{fam0 - 1}", f"Variable cells. Solver's optimum (Simplex LP; minimize {obj}; E6:E{w1} <= B6:B{w1}; "
                             f"L{fam0}:L{f1} <= C{fam0}:C{f1}; Make Unconstrained Variables Non-Negative), computed when "
                             "the solution was built by the bounded-variable simplex method and written here as values, as "
                             "Solver leaves them after Keep Solver Solution. The model is saved with the worksheet: Data > "
                             "Solver opens it ready to solve.", height=150)
    ws.Columns("A").ColumnWidth = 44
    ws.Columns("B:M").ColumnWidth = 14

    book = b.wb.Name
    rows = [("Microsoft Excel Sensitivity Report (written in Solver's layout; see the note)",),
            (f"Worksheet: [{book}]{name}",), (), ("Variable Cells",),
            ("", "", "Final", "Reduced", "Objective", "Allowable", "Allowable"),
            ("Cell", "Name", "Value", "Cost", "Coefficient", "Increase", "Decrease")]
    rows += [(f"$L${fam0 + j}", f"{f} Units bought", s["bought"][j], s["reduced"][j], s["extra"][j], s["c_inc"][j],
              s["c_dec"][j]) for j, f in enumerate(QUOTE)]
    rows += [(), ("Constraints",), ("", "", "Final", "Shadow", "Constraint", "Allowable", "Allowable"),
             ("Cell", "Name", "Value", "Price", "R.H. Side", "Increase", "Decrease")]
    con_top = len(rows) + 1
    rows += [(f"$E${6 + i}", f"{wname} Hours used after buying", s["used"][i], s["shadow"][i], s["cap"][i], s["r_inc"][i],
              s["r_dec"][i]) for i, (_, wname, _) in enumerate(wcs)]
    write_report(rep, rows, money_cols=(3, 4, 5, 6, 7))
    note(rep, "B1", "Written by the companion builder in the layout of Solver's Sensitivity Report: Solver itself was not "
                    "run while building. The optimum and its sensitivity analysis were computed from the dataset by the "
                    "bounded-variable simplex method (the method of Solver's Simplex LP) and written here as values. A "
                    "shadow price is the change in the added cost for one more hour of practical capacity, so it is "
                    f"negative where capacity binds. To regenerate the report, choose Data > Solver on {name}, click "
                    "Solve, and select Sensitivity under Reports.", height=170)
    for i in range(len(wcs)):
        ws.Range(f"H{6 + i}").Formula = f"='{rep.Name}'!E{con_top + i}"

    bnames = [m["centers"][x]["name"] for x in s["binding"]]
    b.check(t, f"growth {g:.0%}: binding work centers", ", ".join(bnames), "=" + res[list(res)[1]], 0, "@")
    for x in s["binding"]:
        b.check(t, f"growth {g:.0%}: value of an hour of {m['centers'][x]['name']} (Sensitivity report)",
                round(-s["shadow"][x], 6), f"='{name}'!I{6 + x}", 1e-6, MONEY)
    for j, (f, x) in enumerate(zip(QUOTE, s["bought"])):
        if x > 0.5:
            b.check(t, f"growth {g:.0%}: {f} units bought", round(x, 6), f"='{name}'!L{fam0 + j}", 1e-4, UNITS)
    b.check(t, f"growth {g:.0%}: families bought", ", ".join(f for f, x in zip(QUOTE, s["bought"]) if x > 0.5),
            "=" + res[list(res)[2]], 0, "@")
    b.check(t, f"growth {g:.0%}: added cost (Solver's objective)", round(s["cost"], 4), "=" + res[list(res)[0]], 0.005)
    b.check(t, f"growth {g:.0%}: every work center within its capacity", True, "=" + res[list(res)[3]], 0, "General")
    b.check(t, f"growth {g:.0%}: units bought within their limits", True, "=" + res[list(res)[4]], 0, "General")


# --- Requirement 8: reprice the families below the floor ------------------------------------------------------------

def price_evidence(d: Data) -> dict:
    """The price-list evidence, computed in Python from the rows."""
    ratio = defaultdict(list)
    for pid, status, up, lp in d.q("SELECT pl.PriceListID, pl.Status, x.UnitPrice, i.ListPrice FROM PriceList pl "
                                   "JOIN PriceListLine x ON x.PriceListID = pl.PriceListID JOIN Item i ON i.ItemID = x.ItemID"):
        ratio[(pid, status)].append(up / lp)
    active = [v for (pid, st_), v in ratio.items() if st_ == "Active"]
    ends = sorted({e for (e,) in d.q("SELECT EffectiveEndDate FROM PriceList WHERE Status = 'Active'")})
    used = sorted({pid for pid, end, od in d.q(
        "SELECT pl.PriceListID, pl.EffectiveEndDate, o.OrderDate FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = "
        "l.SalesOrderID JOIN PriceListLine x ON x.PriceListLineID = l.PriceListLineID JOIN PriceList pl ON pl.PriceListID = "
        "x.PriceListID WHERE pl.Status = 'Expired'") if od > end})
    approvers = sorted({r[0] for r in d.q("SELECT e.JobTitle FROM PriceOverrideApproval a JOIN Employee e ON e.EmployeeID = "
                                          "a.ApprovedByEmployeeID WHERE a.Status = 'Approved'")})
    return dict(low=min(min(v) for v in active), high=max(max(v) for v in active), ends=ends, expired_used=used,
                approvers=approvers)


def r8(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    ws = sheet(b, "Prices")
    title(ws, "Requirement 8: reprice the families below the floor",
          "The floor is a 40% gross margin on time-driven cost, before unused capacity (Assumptions). Contribution is "
          "measured over the relevant cost with the crew kept.")
    cols = ["Family", "Units sold, base year", "Price at the base-year mix", "Time-driven cost", "Time-driven margin",
            "Below the floor", "Target price (Goal Seek's changing cell)",
            "Margin above the floor at the target price, a year (Goal Seek sets it to 0)", "Target price (direct)",
            "Increase", "Relevant cost, crew kept", "Contribution per unit at today's price",
            "Volume the increase can lose before contribution falls", "Revenue a year if volume holds"]
    header(ws, 4, cols)
    ws.Rows(4).RowHeight = 60
    fams = sorted(m["fam"])
    rows = {}
    below = {r_["name"] for r_ in m["reprice"]}
    for i, f in enumerate(fams):
        rr = 5 + i
        ws.Cells(rr, 1).Value = f
        look = lambda c: f"=XLOOKUP($A{rr},{famref('Family')},{famref(c)})"
        formulas(ws, {f"B{rr}": look("Units"), f"C{rr}": look("Price"), f"D{rr}": look("TimeDriven"),
                      f"E{rr}": f"=1-D{rr}/C{rr}", f"F{rr}": f"=E{rr}<MarginFloor",
                      f"H{rr}": f'=IF(F{rr},B{rr}*(G{rr}*(1-MarginFloor)-D{rr}),"")',
                      f"I{rr}": f'=IF(F{rr},D{rr}/(1-MarginFloor),"")', f"J{rr}": f'=IF(F{rr},G{rr}/C{rr}-1,"")',
                      f"K{rr}": look("Kept"), f"L{rr}": f"=C{rr}-K{rr}",
                      f"M{rr}": f'=IF(F{rr},1-L{rr}/(L{rr}+G{rr}-C{rr}),"")',
                      f"N{rr}": f'=IF(F{rr},(G{rr}-C{rr})*B{rr},"")'})
        rows[f] = rr
    last = 4 + len(fams)
    b.wb.Application.Calculate()
    for f in fams:
        if f in below:
            rr = rows[f]
            ws.Range(f"G{rr}").Value = round(m["fam"][f]["unit"]["price"], 2)
            ws.Range(f"G{rr}").Interior.Color = AMBER
    b.wb.Application.Calculate()
    for f in fams:
        if f in below:
            settle(b)
            xl.retry(lambda r_=rows[f]: ws.Range(f"H{r_}").GoalSeek(0, ws.Range(f"G{r_}")))
    settle(b)
    note(ws, "G4", "Goal Seek (Data > What-If Analysis > Goal Seek), run for each family below the floor when the solution "
                   "was built: Set cell H To value 0 By changing cell G. The results stay in the changing cells, as Goal "
                   "Seek leaves them; column I computes the same price directly (time-driven cost / (1 - floor)).",
         height=130)
    for c, fmt in (("B", UNITS), ("C", MONEY), ("D", MONEY), ("E", PCT1), ("G", MONEY), ("H", MONEY), ("I", MONEY),
                   ("J", "0.00%"), ("K", MONEY), ("L", MONEY), ("M", PCT1), ("N", COUNT)):
        ws.Range(f"{c}5:{c}{last}").NumberFormat = fmt
    r = last + 2
    tot = lines(ws, r, [
        ("Families below the floor", f"=COUNTIF(F5:F{last},TRUE)", COUNT),
        ("  which", f'=TEXTJOIN(", ",TRUE,FILTER(A5:A{last},F5:F{last},"none"))', None),
        ("Revenue a year if volume holds", f"=SUM(N5:N{last})", COUNT, "RepriceRevenue"),
        ("If the families of Requirement 6 are bought, those still below the floor",
         f'=TEXTJOIN(", ",TRUE,FILTER(A5:A{last},F5:F{last}*ISNA(XMATCH(A5:A{last},'
         f'FILTER({mb("A")},{mb("P")}=1))),"none"))', None, "StillToReprice"),
        ("  their revenue a year if volume holds",
         f'=SUMPRODUCT(--F5:F{last},ISNA(XMATCH(A5:A{last},FILTER({mb("A")},{mb("P")}=1)))*1,N5:N{last})', COUNT)])
    r += 6
    heading(ws, r, "Delivered margins of the families bought (the quote against the base-year price)")
    header(ws, r + 1, ["Family", "Delivered margin", "Above the floor"])
    buy_rows = {}
    for i, x in enumerate(m["buy"]):
        rr = r + 2 + i
        ws.Cells(rr, 1).Value = x["name"]
        formulas(ws, {f"B{rr}": f"=XLOOKUP($A{rr},{mb('A')},{mb('S')})", f"C{rr}": f"=B{rr}>=MarginFloor"})
        ws.Range(f"B{rr}").NumberFormat = PCT1
        buy_rows[x["name"]] = rr
    r += len(m["buy"]) + 3

    heading(ws, r, "Evidence on how customers respond to price: order volume in the months of past promotions")
    pv = paste(b, ws, f"A{r + 1}", "promotions", "PromotionVolume", text=("PromotionMonths",),
               formats={f"M{k:02d}": COUNT for k in range(1, 13)})
    flags = 'ISNUMBER(SEARCH(","&SEQUENCE(1,12)&",",","&[@PromotionMonths]&","))'
    vals = "PromotionVolume[@[M01]:[M12]]"
    add_cols(pv, [("Months", f"=SUM(--{flags})", "0"),
                  ("PromotionValue", f"=SUM({vals}*{flags})", COUNT),
                  ("Expected", f"=AVERAGE(FILTER({vals},NOT({flags})))*[@Months]", COUNT),
                  ("Lift", "=[@PromotionValue]/[@Expected]-1", PCT1),
                  ("Z", f"=([@PromotionValue]-[@Expected])/(STDEV.S(FILTER({vals},NOT({flags})))*SQRT([@Months]))",
                   "0.00")])
    note(ws, f"{col_letter(pv, 'Months')}{r + 1}", "Months, PromotionValue, Expected, Lift, and Z are formulas: the "
         "list-price order value in the promotion's months against the mean of the other months of its year (Expected), "
         "and the difference in standard deviations of those months (Z), as the Part II case tested it.")
    r += pv.ListRows.Count + 3
    vol = volume_test(d)
    ev = lines(ws, r, [("Lowest lift", "=MIN(PromotionVolume[Lift])", PCT1),
                       ("Highest lift", "=MAX(PromotionVolume[Lift])", PCT1),
                       ("Largest Z", "=MAX(PromotionVolume[Z])", "0.00"),
                       ("Promotions with a Z of 2 or more", '=COUNTIF(PromotionVolume[Z],">=2")', COUNT)])
    r += 6
    heading(ws, r, "The price lists: their dates and use (Exercise 8.6's test)")
    pl = paste(b, ws, f"A{r + 1}", "pricelists", "PriceLists", dates=("EffectiveStartDate", "EffectiveEndDate"),
               formats={"LowestPriceToList": "0.000", "HighestPriceToList": "0.000", "OrderLinesAfterEnd": COUNT})
    r += pl.ListRows.Count + 3
    pe = price_evidence(d)
    lists = lines(ws, r, [
        ("Active lists: lowest price to list", '=MINIFS(PriceLists[LowestPriceToList],PriceLists[Status],"Active")', "0.00"),
        ("Active lists: highest price to list", '=MAXIFS(PriceLists[HighestPriceToList],PriceLists[Status],"Active")',
         "0.00"),
        ("Active lists' end dates",
         '=TEXTJOIN(", ",TRUE,TEXT(UNIQUE(FILTER(PriceLists[EffectiveEndDate],PriceLists[Status]="Active")),"yyyy-mm-dd"))',
         None),
        ("Expired lists still used after their end date",
         '=TEXTJOIN(", ",TRUE,FILTER(PriceLists[PriceListID],(PriceLists[Status]="Expired")*'
         '(PriceLists[OrderLinesAfterEnd]>0),"none"))', None)])
    r += 5
    paste(b, ws, f"A{r}", "overrides", "Overrides", formats={"ApprovedOverrides": COUNT})
    ov = lines(ws, r + 3, [("Who approves price overrides", '=TEXTJOIN(", ",TRUE,Overrides[ApproverJobTitle])', None)])
    r += 6
    need = [x["short"] for x in m["reprice"] if x["name"] not in m["buy_names"]]
    paras = [
        f"{len(m['reprice'])} families earn less than the 40% floor on their time-driven cost: "
        + "; ".join(f"{x['short']} needs {x['increase']:+.2%} and can lose {x['loss']:.1%} of its volume before it earns "
                    "less contribution than now" for x in m["reprice"])
        + f". If volume holds, the increases add {sum(x['revenue'] for x in m['reprice']):,.0f} of revenue a year. If "
        f"{series([x['short'] for x in m['buy']])} are bought, their delivered margins are "
        + ", ".join(f"{x['margin']:.1%}" for x in m["buy"]) + f", above the floor, so only {series(need)} need increases.",
        f"The evidence says customers do not respond much to price in the short run: no past promotion raised order "
        f"volume (lifts from {min(v['lift'] for v in vol):+.1%} to {max(v['lift'] for v in vol):+.1%}, none unusual), "
        "so increases of a few percent are unlikely to lose the volume they can afford. But the prices customers pay "
        f"come from price lists: the active lists run at {pe['low']:.2f} to {pe['high']:.2f} of list and every one ends "
        f"on {', '.join(pe['ends'])}, lists {series([str(x) for x in pe['expired_used']])} had expired and were still "
        f"used, and the {', '.join(pe['approvers'])} approves the overrides.",
        "Recommendation: raise the families below the floor to it (and the families bought, if they are kept) through new, "
        "approved price lists for 2028 with stated end dates; renegotiate the customer-specific lists rather than "
        "inheriting them; and watch the volume of each family against the loss it can afford."]
    answer(ws, r, paras, last_col="N")
    ws.Columns("A").ColumnWidth = 30
    ws.Columns("B:Z").ColumnWidth = 13

    t = "Requirement 8"
    for x in m["reprice"]:
        rr = rows[x["name"]]
        b.check(t, f"{x['name']}: target price (Goal Seek)", round(x["new"], 4), f"=Prices!G{rr}", 0.005)
        b.check(t, f"{x['name']}: target price (direct)", round(x["new"], 6), f"=Prices!I{rr}", 1e-6)
        b.check(t, f"{x['name']}: increase", round(x["increase"], 6), f"=Prices!J{rr}", 1e-5, "0.00%")
        b.check(t, f"{x['name']}: volume the increase can lose", round(x["loss"], 6), f"=Prices!M{rr}", 1e-5, PCT1)
        b.check(t, f"{x['name']}: revenue a year if volume holds", round(x["revenue"], 2), f"=Prices!N{rr}", 0.5, COUNT)
    b.check(t, "families below the floor", len(m["reprice"]), "=" + tot[list(tot)[0]], 0, COUNT)
    b.check(t, "  which", ", ".join(x["name"] for x in m["reprice"]), "=" + tot[list(tot)[1]], 0, "@")
    b.check(t, "revenue a year if volume holds", round(sum(x["revenue"] for x in m["reprice"]), 2), "=RepriceRevenue", 1,
            COUNT)
    b.check(t, "families still below the floor if the families of Requirement 6 are bought",
            ", ".join(x["name"] for x in m["reprice"] if x["name"] not in m["buy_names"]), "=StillToReprice", 0, "@")
    for x in m["buy"]:
        b.check(t, f"{x['name']}: delivered margin", round(x["margin"], 9), f"=Prices!B{buy_rows[x['name']]}", 1e-9, PCT1)
    b.check(t, "lowest lift of a past promotion", round(min(v["lift"] for v in vol), 9), "=" + ev[list(ev)[0]], 1e-9, PCT1)
    b.check(t, "highest lift", round(max(v["lift"] for v in vol), 9), "=" + ev[list(ev)[1]], 1e-9, PCT1)
    b.check(t, "largest Z", round(max(v["z"] for v in vol), 9), "=" + ev[list(ev)[2]], 1e-9, "0.00")
    b.check(t, "promotions with a Z of 2 or more", sum(1 for v in vol if v["z"] >= 2), "=" + ev[list(ev)[3]], 0, COUNT)
    b.check(t, "active lists: lowest price to list", round(pe["low"], 9), "=" + lists[list(lists)[0]], 1e-9, "0.000")
    b.check(t, "active lists: highest price to list", round(pe["high"], 9), "=" + lists[list(lists)[1]], 1e-9, "0.000")
    serial = lambda iso: float((date.fromisoformat(iso) - date(1899, 12, 30)).days)
    b.check(t, "active lists: earliest end date", serial(pe["ends"][0]),
            '=MIN(FILTER(PriceLists[EffectiveEndDate],PriceLists[Status]="Active"))', 0, "yyyy-mm-dd")
    b.check(t, "active lists: latest end date", serial(pe["ends"][-1]),
            '=MAX(FILTER(PriceLists[EffectiveEndDate],PriceLists[Status]="Active"))', 0, "yyyy-mm-dd")
    b.check(t, "expired lists still used after their end date", "lists " + ", ".join(str(x) for x in pe["expired_used"]),
            '="lists "&' + lists[list(lists)[3]], 0, "@")
    b.check(t, "who approves price overrides", ", ".join(pe["approvers"]), "=" + ov[list(ov)[0]], 0, "@")


# --- Requirement 9: standards on normal capacity, and the statements ------------------------------------------------

def typed_plan(m: dict) -> dict:
    """The proposed rate as the workbook computes it, from the plan values typed on Assumptions (tbl-18-02: 68,912.79
    standard hours, 263,191.24 of salaries, 293,499.96 of depreciation). The notes compute the same rate from the data
    those values come from (68,912.7917 standard hours), which differs only beyond the eighth significant digit."""
    lab = m["labor_rate"]
    parts = dict(direct=lab, variable=m["fo_rate"], indirect=INDIRECT * lab,
                 supervision=PLAN_SALARIES * (1 + BURDEN) / PLAN_VOLUME, depreciation=PLAN_DEPRECIATION / PLAN_VOLUME)
    new = sum(parts.values())
    one = new - parts["indirect"]
    items, sold = m["items"], m["sold"]
    revised = {f: sum(sold[i][0] * ((items[i]["std"] - items[i]["conv"]) + new * items[i]["stdh"])
                      for i in m["fam"][f]["ids"]) / m["fam"][f]["units"] for f in QUOTE}
    stock = {x["year"]: dict(plan=x["stdh"] * new - x["conv"], one=x["stdh"] * one - x["conv"]) for x in m["stock"]}
    return dict(parts=parts, new_rate=new, one_rate=one, revised=revised, stock=stock)


def r9(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    ws = sheet(b, "Standards")
    title(ws, "Requirement 9: standards on normal capacity, and what they mean for the statements",
          "Normal capacity is the plan volume at its hours per standard hour (tbl-18-02); the rates are next year's plan "
          "applied to the stock of earlier years, an approximation.")
    header(ws, 4, ["Proposed standard conversion rate, per standard hour", "Amount", "Basis"])
    parts = [("Direct labor at the straight-time rate with burden", "=LaborRate*(1+Burden)", "26.62 x 1.1414"),
             ("Overhead that varies with output (Factory Overhead entries per standard hour)", "=FORate",
              "Requirement 2: varies with output at about the applied rate"),
             ("Indirect labor at plan", "=IndirectHours*B5", "0.18 hours per standard hour at the labor rate"),
             ("Supervision", "=PlanSalaries*(1+Burden)/PlanVolume", "the plan's salaried staff with burden over the plan volume"),
             ("Depreciation", "=PlanDepreciation/PlanVolume", "the plan's depreciation over the plan volume")]
    for i, (label, f, basis) in enumerate(parts):
        ws.Cells(5 + i, 1).Value = label
        ws.Range(f"B{5 + i}").Formula = f
        ws.Cells(5 + i, 3).Value = basis
    rate = lines(ws, 10, [
        ("Proposed rate, normal capacity (1.18 hours per standard hour)", "=SUM(B5:B9)", MONEY, "NewRate"),
        ("Proposed rate at 1.0 hours per standard hour (no indirect time)", "=NewRate-B7", MONEY, "OneRate"),
        ("Current standard: conversion released per standard hour", "=ConversionReleased/StdHours", MONEY, "CurrentRate"),
        ("Time-driven, per standard hour", "=FORate+TDRate*UsedHours/StdHours", MONEY, "TDStdRate"),
        ("The base year's actual cost per standard hour", "=Inputs1090/StdHours", MONEY, "ActualRate")])
    ws.Range("B5:B9").NumberFormat = MONEY
    heading(ws, 16, "The plan's figures against the records")
    paste(b, ws, "E17", "plandep", "PlanDepreciationSchedule", formats={"PlanYearDepreciation": MONEY})
    plan = lines(ws, 17, [
        ("Plan volume (Assumptions) equals the base year's standard hours, rounded", "=ROUND(StdHours,2)=PlanVolume", None),
        ("Salaried staff at plan equals the base year's salaried gross pay",
         '=ROUND(XLOOKUP("Salary",PayClass[PayClass],PayClass[GrossPay]),2)=PlanSalaries', None),
        ("Depreciation at plan equals the FixedAsset schedule for the next year (column E)",
         "=ROUND(PlanDepreciation-PlanDepreciationSchedule[PlanYearDepreciation],2)=0", None)])
    heading(ws, 21, "Revised standard costs of the quoted families, at the base-year mix")
    header(ws, 22, ["Family", "Revised standard (proposed rate)", "Time-driven cost", "Current standard cost"])
    rev_rows = {}
    for i, f in enumerate(QUOTE):
        rr = 23 + i
        ws.Cells(rr, 1).Value = f
        mask = f'(ItemCosts[Family]=$A{rr})*(ItemCosts[SupplyMode]="Manufactured")*ItemCosts[Units]'
        formulas(ws, {f"B{rr}": f"=SUMPRODUCT({mask},ItemCosts[Material]+NewRate*ItemCosts[StandardLaborHoursPerUnit])/"
                                f"SUMPRODUCT({mask})",
                      f"C{rr}": f"=XLOOKUP($A{rr},{famref('Family')},{famref('TimeDriven')})",
                      f"D{rr}": f"=XLOOKUP($A{rr},{famref('Family')},{famref('Standard')})"})
        rev_rows[f] = rr
    ws.Range(f"B23:D{22 + len(QUOTE)}").NumberFormat = MONEY

    # The stock the standards apply to (pasted at J4), revalued at each year-end
    years = d.years
    oh = paste(b, ws, "J4", "onhand", "OnHand", formats={f"OnHand{y}": UNITS for y in years})
    add_cols(oh, [("StdHoursPerUnit", "=XLOOKUP([@ItemID],ItemCosts[ItemID],ItemCosts[StandardLaborHoursPerUnit])", "0.0000"),
                  ("ConversionPerUnit", "=XLOOKUP([@ItemID],ItemCosts[ItemID],ItemCosts[StandardConversionCost])", MONEY),
                  ("StandardCostPerUnit", "=XLOOKUP([@ItemID],ItemCosts[ItemID],ItemCosts[StandardCost])", MONEY)])
    r = 23 + len(QUOTE) + 2
    heading(ws, r, "Manufactured finished goods made since the ledger opened and on hand at each year-end")
    header(ws, r + 1, ["Measure"] + [f"End of fiscal {y}" for y in years])
    measures = [("Units on hand (items with a positive balance)", "SUMPRODUCT((OnHand[{c}]>0)*OnHand[{c}])", UNITS),
                ("Standard hours", "SUMPRODUCT((OnHand[{c}]>0)*OnHand[{c}]*OnHand[StdHoursPerUnit])", MONEY),
                ("Conversion at the current standard", "SUMPRODUCT((OnHand[{c}]>0)*OnHand[{c}]*OnHand[ConversionPerUnit])",
                 MONEY),
                ("Value at the current standard", "SUMPRODUCT((OnHand[{c}]>0)*OnHand[{c}]*OnHand[StandardCostPerUnit])", MONEY),
                ("Conversion per standard hour in that stock", "{col}{r2}/{col}{r1}", MONEY),
                ("Revaluation at the proposed rate (1.18 hours)", "{col}{r1}*NewRate-{col}{r2}", COUNT),
                ("Revaluation at 1.0 hours per standard hour", "{col}{r1}*OneRate-{col}{r2}", COUNT),
                ("Revaluation at the time-driven rate", "{col}{r1}*TDStdRate-{col}{r2}", COUNT),
                ("Revaluation at the base year's actual cost (capitalizes idle capacity)", "{col}{r1}*ActualRate-{col}{r2}",
                 COUNT),
                ("Items with a negative balance (proof of opening stock; left out)",
                 'TEXTJOIN(", ",TRUE,FILTER(OnHand[ItemCode],OnHand[{c}]<-0.05,"none"))', None)]
    s0 = r + 2
    srow = {}
    for i, (label, f, fmt) in enumerate(measures):
        rr = s0 + i
        ws.Cells(rr, 1).Value = label
        srow[label] = rr
        for j, y in enumerate(years):
            c = col(2 + j)
            ws.Cells(rr, 2 + j).Formula2 = "=" + f.format(c=f"OnHand{y}", col=c, r1=s0 + 1, r2=s0 + 2)
            if fmt:
                ws.Cells(rr, 2 + j).NumberFormat = fmt
    keys = [x[0] for x in measures]
    r = s0 + len(measures) + 1
    heading(ws, r, "Effect on the statements issued to the shareholders, at the proposed rate")
    paste(b, ws, f"F{r + 1}", "income", "Income", formats={"IncomeBeforeTaxes": MONEY})
    yc = {y: col(2 + j) for j, y in enumerate(years)}
    reval = srow[keys[5]]
    one = srow[keys[6]]
    P, C, F_ = d.P, d.C, d.F
    eff = lines(ws, r + 1, [
        (f"Retained earnings at the start of fiscal {P}", f"={yc[F_]}{reval}", COUNT, "RevalOpening"),
        (f"Fiscal {P} income", f"={yc[P]}{reval}-{yc[F_]}{reval}", COUNT, "RevalIncomePrior"),
        (f"Fiscal {C} income", f"={yc[C]}{reval}-{yc[P]}{reval}", COUNT, "RevalIncomeCurrent"),
        (f"Inventories at the end of fiscal {P}", f"={yc[P]}{reval}", COUNT, "RevalBalancePrior"),
        (f"Inventories at the end of fiscal {C}", f"={yc[C]}{reval}", COUNT, "RevalBalanceCurrent"),
        (f"Materiality for fiscal {P} (5% of income before income taxes as recorded)",
         f"=ROUND(MaterialityShare*XLOOKUP({P},Income[FiscalYear],Income[IncomeBeforeTaxes]),2)", MONEY, "MaterialityPrior"),
        (f"Materiality for fiscal {C}",
         f"=ROUND(MaterialityShare*XLOOKUP({C},Income[FiscalYear],Income[IncomeBeforeTaxes]),2)", MONEY,
         "MaterialityCurrent"),
        ("Both balance sheet effects above materiality",
         "=AND(RevalBalancePrior>MaterialityPrior,RevalBalanceCurrent>MaterialityCurrent)", None),
        ("Both income effects below materiality",
         "=AND(RevalIncomePrior<MaterialityPrior,RevalIncomeCurrent<MaterialityCurrent)", None),
        (f"At 1.0 hours: fiscal {P} balance above materiality", f"={yc[P]}{one}>MaterialityPrior", None),
        (f"At 1.0 hours: fiscal {C} balance above materiality", f"={yc[C]}{one}>MaterialityCurrent", None)])
    r += 13
    paste(b, ws, f"A{r}", "openingfg", "OpeningFG", formats={"OpeningFinishedGoods": MONEY})
    r += 3
    sp, sc, sf = (next(x for x in m["stock"] if x["year"] == y) for y in (P, C, F_))
    tp = typed_plan(m)
    mat_p = round(MATERIALITY * m["income"][P] + 1e-9, 2)
    mat_c = round(MATERIALITY * m["income"][C] + 1e-9, 2)
    paras = [
        f"Proposed standard on normal capacity, the plan volume of {PLAN_VOLUME:,.2f} standard hours at "
        f"{PLAN_HOURS} hours per standard hour: direct labor {m['parts']['direct']:.2f} + the overhead that varies "
        f"{m['parts']['variable']:.2f} + indirect labor {m['parts']['indirect']:.2f} + supervision "
        f"{m['parts']['supervision']:.2f} + depreciation {m['parts']['depreciation']:.2f} = {m['new_rate']:.2f} a standard "
        f"hour ({m['one_rate']:.2f} at 1.0 hours), against {m['conversion'] / m['stdh']:.2f} today, "
        f"{m['td_std']:.2f} time-driven, and {m['actual_rate']:.2f} actual. A standard built on the base year's actual "
        "cost would carry the idle capacity and the hours paid beyond the work into inventory; ASC Topic 330 allocates "
        "fixed overhead on normal capacity and charges abnormal costs, such as idle facility expense, to the period.",
        f"Revalued at the proposed rate, the manufactured finished goods made since the opening and on hand rise by "
        f"{sf['plan']:,.0f}, {sp['plan']:,.0f}, and {sc['plan']:,.0f} at the {F_}, {P}, and {C} year-ends: retained "
        f"earnings at the start of fiscal {P} +{sf['plan']:,.0f}, fiscal {P} income +{sp['plan'] - sf['plan']:,.0f}, fiscal "
        f"{C} income +{sc['plan'] - sp['plan']:,.0f}. The balance sheet effects exceed materiality ({mat_p:,.2f} for {P}, "
        f"{mat_c:,.2f} for {C}); the income effects do not. The answer depends on what is treated as normal capacity: at "
        f"1.0 hours the {P} balance effect ({sp['one']:,.0f}) falls below materiality and the {C} one ({sc['one']:,.0f}) "
        f"stays above; at the actual rate the {C} effect would be {sc['actual']:,.0f}, by capitalizing idle capacity.",
        "Recommendation: on the plan's definition of normal capacity the inventory error is material to the balance "
        f"sheets the shareholders received, so the fiscal {P} and {C} statements should be revised (inventories, retained "
        "earnings, and income corrected, with the correction disclosed), and the CFO should tell the shareholders that "
        "the standards had not been updated in three years and understated the cost of the stock on hand. If the CFO "
        "judges the effect immaterial on a narrower definition of normal capacity, the correction belongs in the next "
        f"statements with disclosure. The decision is the CFO's. The opening {m['opening_fg']:,.2f} of finished goods "
        "has no item detail and is left out."]
    answer(ws, r, paras, last_col="H")
    ws.Columns("A").ColumnWidth = 60
    ws.Columns("B:D").ColumnWidth = 15
    ws.Columns("E:H").ColumnWidth = 13
    b.found["stock_rows"] = srow

    t = "Requirement 9"
    for (label, _, _), (k, v) in zip(parts, tp["parts"].items()):
        b.check(t, f"{label}", round(v, 9), f"=Standards!B{5 + list(tp['parts']).index(k)}", 1e-9)
    b.check(t, "proposed rate per standard hour", round(tp["new_rate"], 9), "=NewRate", 1e-9)
    b.check(t, "proposed rate at 1.0 hours", round(tp["one_rate"], 9), "=OneRate", 1e-9)
    b.check(t, "current standard per standard hour", round(m["conversion"] / m["stdh"], 9), "=CurrentRate", 1e-9)
    b.check(t, "time-driven per standard hour", round(m["td_std"], 9), "=TDStdRate", 1e-9)
    b.check(t, "the base year's actual cost per standard hour", round(m["actual_rate"], 9), "=ActualRate", 1e-9)
    for i, label in enumerate(plan):
        b.check(t, label, True, "=" + plan[label], 0, "General")
    q = {x["name"]: x for x in m["quoted"]}
    for f, rr in rev_rows.items():
        b.check(t, f"{f}: revised standard cost", round(tp["revised"][f], 6), f"=Standards!B{rr}", 1e-6)
        b.check(t, f"{f}: time-driven cost", round(q[f]["td"], 6), f"=Standards!C{rr}", 1e-6)
    for x in m["stock"]:
        c = yc[x["year"]]
        b.check(t, f"end of fiscal {x['year']}: units on hand", round(x["units"], 4), f"=Standards!{c}{srow[keys[0]]}", 0.005,
                UNITS)
        b.check(t, f"end of fiscal {x['year']}: standard hours", round(x["stdh"], 4), f"=Standards!{c}{srow[keys[1]]}", 0.005)
        b.check(t, f"end of fiscal {x['year']}: conversion at standard", round(x["conv"], 2), f"=Standards!{c}{srow[keys[2]]}",
                0.01)
        b.check(t, f"end of fiscal {x['year']}: conversion per standard hour", round(x["per_hour"], 9),
                f"=Standards!{c}{srow[keys[4]]}", 1e-9)
        for key, k in (("plan", 5), ("one", 6), ("td", 7), ("actual", 8)):
            value = tp["stock"][x["year"]][key] if key in ("plan", "one") else x[key]
            b.check(t, f"end of fiscal {x['year']}: {keys[k][0].lower() + keys[k][1:]}", round(value, 2),
                    f"=Standards!{c}{srow[keys[k]]}", 0.01, COUNT)
        b.check(t, f"end of fiscal {x['year']}: items with a negative balance", text_list(x["negative"]),
                f"=Standards!{c}{srow[keys[9]]}", 0, "@")
    b.check(t, f"end of fiscal {C}: value at standard", round(sc["std"], 2), f"=Standards!{yc[C]}{srow[keys[3]]}", 0.01)
    rf, rp_, rc = (tp["stock"][y]["plan"] for y in (F_, P, C))
    b.check(t, f"retained earnings at the start of fiscal {P}", round(rf, 2), "=RevalOpening", 0.01, COUNT)
    b.check(t, f"fiscal {P} income", round(rp_ - rf, 2), "=RevalIncomePrior", 0.01, COUNT)
    b.check(t, f"fiscal {C} income", round(rc - rp_, 2), "=RevalIncomeCurrent", 0.01, COUNT)
    b.check(t, f"materiality for fiscal {P}", mat_p, "=MaterialityPrior", 0.005)
    b.check(t, f"materiality for fiscal {C}", mat_c, "=MaterialityCurrent", 0.005)
    one_p, one_c = tp["stock"][P]["one"], tp["stock"][C]["one"]
    flags = [rp_ > mat_p and rc > mat_c, rp_ - rf < mat_p and rc - rp_ < mat_c, one_p > mat_p, one_c > mat_c]
    for label, flag in zip(list(eff)[7:], flags):
        b.check(t, label, flag, "=" + eff[label], 0, "General")
    b.check(t, "finished goods on the opening entry (no item detail)", round(m["opening_fg"], 2),
            "=OpeningFG[OpeningFinishedGoods]", 0.01)


# --- Requirement 10: the decision memo ------------------------------------------------------------------------------

def r10(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    ws = sheet(b, "Memo")
    title(ws, "Requirement 10: the decision table and the memo (model answer)",
          "The memo itself is a separate document of no more than two pages; the decision table's figures are formulas "
          "over the other sheets.")
    header(ws, 4, ["Family", "What to do", "Annual effect", "One-time cost", "What the decision depends on"])
    reprice = {x["name"]: x for x in m["reprice"]}
    order = [x["name"] for x in m["buy"]] + [x["name"] for x in m["lose"]] + \
            [x["name"] for x in m["reprice"] if x["name"] not in QUOTE]
    rows = {}
    prices = lambda c, rr: f"XLOOKUP($A{rr},Prices!$A$5:$A$40,Prices!${c}$5:${c}$40)"
    for i, f in enumerate(order):
        rr = 5 + i
        ws.Cells(rr, 1).Value = f
        if f in m["buy_names"]:
            formulas(ws, {
                f"B{rr}": (f'="Buy, only with the crew reduced in step (about "&TEXT(XLOOKUP($A{rr},{mb("A")},{mb("U")}),'
                           f'"0.0")&" positions); otherwise keep making it and raise its price "&TEXT({prices("J", rr)},'
                           '"0.0%")'),
                f"C{rr}": f"=XLOOKUP($A{rr},{mb('A')},{mb('N')})",
                f"D{rr}": f"=XLOOKUP($A{rr},{mb('A')},{mb('W')})+XLOOKUP($A{rr},{mb('A')},{mb('U')})*SeverancePerPosition"})
            ws.Cells(rr, 5).Value = ("The production manager's decision to reduce the crew; quality against the 1.5% "
                                     "defect credit; lead time and the 80% minimum; the price after 2029")
        elif f in QUOTE:
            what = '="Make"' + (f'&"; raise its price "&TEXT({prices("J", rr)},"0.0%")' if f in reprice else "")
            formulas(ws, {f"B{rr}": what,
                          f"C{rr}": f"={prices('N', rr)}" if f in reprice else "=0"})
            ws.Range(f"D{rr}").Value = 0
            ws.Range(f"E{rr}").Formula2 = (f'="Buying loses money with the crew kept ("&TEXT(XLOOKUP($A{rr},{mb("A")},'
                                           f'{mb("M")}),"#,##0")&" a year) and reduced ("&TEXT(XLOOKUP($A{rr},{mb("A")},'
                                           f'{mb("N")}),"#,##0")&")"'
                                           + (f'&"; the increase can lose "&TEXT({prices("M", rr)},"0.0%")&" of volume"'
                                              if f in reprice else ""))
        else:
            formulas(ws, {f"B{rr}": f'="Raise its price "&TEXT({prices("J", rr)},"0.0%")&" to the floor"',
                          f"C{rr}": f"={prices('N', rr)}",
                          f"E{rr}": (f'="Volume loss below "&TEXT({prices("M", rr)},"0.0%")&"; a new, approved price list '
                                     'with an end date"')})
            ws.Range(f"D{rr}").Value = 0
        rows[f] = rr
    last = 4 + len(order)
    tot = lines(ws, last + 1, [("Total annual effect", f"=SUM(C5:C{last})", COUNT),
                               ("Total one-time cost", f"=SUM(D5:D{last})", COUNT)])
    ws.Range(f"C5:D{last}").NumberFormat = COUNT
    ws.Range(f"B5:B{last}").WrapText = True
    ws.Range(f"E5:E{last}").WrapText = True
    buy, lose = m["buy"], m["lose"]
    need = [x["short"] for x in m["reprice"] if x["name"] not in m["buy_names"]]
    unused_pos = m["unused_h"] / m["pos_hours"]
    sp, sc = (next(x for x in m["stock"] if x["year"] == y) for y in (d.P, d.C))
    paras = [
        "To: the CFO and the production manager. From: the staff accountant. Subject: make, buy, or reprice; and the "
        "standards.",
        f"The plant already pays for about {unused_pos:.1f} positions of capacity it does not use ({m['unused_h']:,.0f} "
        f"practical hours, {m['unused_h'] * m['td_rate']:,.0f} a year): fitting the crew to the work is worth more than "
        f"any outsourcing decision. Both of you are right about part of the cost. The CFO is right that the products cost "
        f"more than their standards say ({m['new_rate']:.2f} a standard hour on normal capacity against "
        f"{m['conversion'] / m['stdh']:.2f}); the production manager is right that idle capacity is not the products' "
        "fault, and should be reported as a cost of the plant, not spread over the products.",
        f"Make {series([x['short'] for x in lose])}: buying them loses money whatever happens to the crew. Buy "
        f"{series([x['short'] for x in buy])} only with a committed plan to reduce the crew in step, about "
        f"{m['positions']:.1f} positions: that saves {m['gain']:,.0f} a year, about "
        f"{2 * m['gain'] - m['positions'] * m['severance'] - m['tooling']:,.0f} over the two years the prices are fixed "
        f"after severance and tooling. With the crew kept, buying them costs {sum(-x['a_kept'] for x in buy):,.0f} a year, "
        "so if the crew stays, keep making them and reprice them.",
        f"Raise {series(need)} to the 40% floor through new, approved price lists for 2028 with end dates (and the "
        f"families bought, if they are kept); the past promotions show no volume response large enough to undo "
        f"increases of this size, which add about {sum(x['revenue'] for x in m['reprice'] if x['name'] not in m['buy_names']):,.0f} "
        "a year if volume holds.",
        f"Standards: adopt {m['new_rate']:.2f} a standard hour on normal capacity for inventory, and time-driven costs "
        "(capacity at its practical cost, idle capacity reported apart) for decisions. The fiscal "
        f"{d.C} statements need attention: revalued at the proposed standard, inventories were understated by about "
        f"{sp['plan']:,.0f} at the end of {d.P} and {sc['plan']:,.0f} at the end of {d.C}, above materiality, so the CFO "
        "should decide whether to issue revised statements to the shareholders.",
        "The one decision only the production manager can make: whether, and how fast, to reduce the crew to the work "
        "the plant has. Every saving above depends on it."]
    answer(ws, last + 4, paras, last_col="E")
    ws.Columns("A").ColumnWidth = 14
    ws.Columns("B").ColumnWidth = 48
    ws.Columns("C:D").ColumnWidth = 14
    ws.Columns("E").ColumnWidth = 60

    t = "Requirement 10"
    q = {x["name"]: x for x in m["quoted"]}
    total = 0.0
    for f, rr in rows.items():
        if f in m["buy_names"]:
            v = q[f]["a_reduced"]
            one_time = q[f]["tooling"] + q[f]["time"] * q[f]["units"] / m["pos_hours"] * m["severance"]
            b.check(t, f"{f}: one-time cost", round(one_time, 2), f"=Memo!D{rr}", 0.01, COUNT)
        else:
            v = reprice[f]["revenue"] if f in reprice else 0.0
        total += v
        b.check(t, f"{f}: annual effect", round(v, 2), f"=Memo!C{rr}", 0.5, COUNT)
    b.check(t, "total annual effect", round(total, 2), "=" + tot[list(tot)[0]], 1, COUNT)
    b.check(t, "total one-time cost", round(m["tooling"] + m["positions"] * m["severance"], 2), "=" + tot[list(tot)[1]],
            0.01, COUNT)
    b.check(t, "unused capacity exceeds the positions buying frees", True, "=UnusedPositions>BuyPositions", 0, "General")
    documentation(b)


# --- Milestones: the checkpoint values an instructor may release ----------------------------------------------------

def m1(b: ExerciseBuild) -> None:
    m = ms(b)
    t = "Milestone 1"
    gro = b.found["group_rows"]
    for g in m["groups"]:
        for c, k, lab in (("F", "m_std", "at standard"), ("G", "m_unit", "after the variance per unit"),
                          ("H", "m_year", "with the year's variance")):
            b.check(t, f"{g['name']} margin {lab}", round(g[k], 9), f"=Families!{c}{gro[g['name']]}", 1e-9, "0.00%")
    b.check(t, "family variances", round(m["totals"]["total"], 2), "=FamilyVariance", 0.01)
    b.check(t, "inputs to 1090", round(m["inputs"], 2), "=Inputs1090", 0.01)
    b.check(t, "released (ProductionCompletion credits to 1090)", round(m["released_gl"], 2), "=Released[CreditsTo1090]",
            0.01)
    k = b.found["r2"]["k"]
    fr = b.found["r2"]["fit_rows"]
    b.check(t, "Factory Overhead r", round(m["fits"]["fo"]["r"], 9), f"='Cost Behavior'!{col(k + 3)}{fr['Factory Overhead entries']}",
            1e-9, "0.000")
    b.check(t, "payroll r", round(m["fits"]["pay"]["r"], 9), f"='Cost Behavior'!{col(k + 3)}{fr['Payroll to 1090']}", 1e-9,
            "0.000")
    b.check(t, "use of practical capacity", round(m["used"] / m["pract"], 9), f"=Activities!F{b.found['cap_rows']['Plant']}",
            1e-9, PCT1)


def m2(b: ExerciseBuild) -> None:
    m = ms(b)
    t = "Milestone 2"
    e = m["explorer"]
    b.check(t, "committed cost", round(m["committed"], 2), "=CommittedCost", 0.01)
    b.check(t, "time-driven rate", round(m["td_rate"], 9), "=TDRate", 1e-9, MONEY)
    b.check(t, "crew rate", round(m["crew_rate"], 9), "=CrewRate", 1e-9, MONEY)
    b.check(t, "unused capacity, hours", round(m["unused_h"], 4), "=UnusedHours", 0.0005, HOURS)
    b.check(t, "unused capacity cost", round(m["unused_h"] * m["td_rate"], 2), "=UnusedCost", 0.01)
    for g in m["groups"]:
        b.check(t, f"{g['name']} time-driven margin", round(g["m_td"], 9), f"=Costs!E{b.found['td_group_rows'][g['name']]}",
                1e-9, "0.00%")
    b.check(t, "explorer margin, standard", round(e["std"], 2), "=ExplorerMarginStandard", 0.01)
    b.check(t, "explorer margin, absorption (unrounded item costs)", round(e["absorp"], 2), "=ExplorerMarginAbsorption", 0.01)
    b.check(t, "explorer margin, time-driven", round(e["td"], 2), "=ExplorerMarginTimeDriven", 0.01)
    b.check(t, "explorer revenue", round(e["rev"], 2), "=ExplorerRevenue", 0.01)


def m3(b: ExerciseBuild) -> None:
    m = ms(b)
    t = "Milestone 3"
    b.check(t, "families to buy only with the crew reduced", ", ".join(m["buy_names"]), "=BuyFamilies", 0, "@")
    b.check(t, "annual effect, crew reduced", round(m["gain"], 2), "=BuyGain", 0.01, COUNT)
    b.check(t, "positions", round(m["positions"], 9), "=BuyPositions", 1e-9, "0.00")
    b.check(t, "two-year net", round(PRICE_YEARS * m["gain"] - m["positions"] * m["severance"] - m["tooling"], 2),
            "=BuyTwoYears", 0.01, COUNT)
    b.check(t, "annual effect with the crew kept", round(sum(x["a_kept"] for x in m["buy"]), 2), "=BuyKept", 0.01, COUNT)
    b.check(t, "families below the floor", len(m["reprice"]), '=COUNTIF(Prices!F5:F40,TRUE)', 0, COUNT)
    b.check(t, "revenue a year if volume holds", round(sum(x["revenue"] for x in m["reprice"]), 2), "=RepriceRevenue", 1,
            COUNT)


def m4(b: ExerciseBuild) -> None:
    m, d = ms(b), data(b)
    t = "Milestone 4"
    tp = typed_plan(m)
    b.check(t, "proposed rate", round(tp["new_rate"], 9), "=NewRate", 1e-9)
    b.check(t, "at 1.0 hours", round(tp["one_rate"], 9), "=OneRate", 1e-9)
    b.check(t, "current rate", round(m["conversion"] / m["stdh"], 9), "=CurrentRate", 1e-9)
    srow = b.found["stock_rows"]
    reval = srow[next(k for k in srow if k.startswith("Revaluation at the proposed"))]
    for j, x in enumerate(m["stock"]):
        b.check(t, f"revaluation at the end of fiscal {x['year']}", round(tp["stock"][x["year"]]["plan"], 2),
                f"=Standards!{col(2 + j)}{reval}", 0.01, COUNT)
    rf, rp_, rc = (tp["stock"][y]["plan"] for y in d.years)
    b.check(t, f"fiscal {d.P} income", round(rp_ - rf, 2), "=RevalIncomePrior", 0.01, COUNT)
    b.check(t, f"fiscal {d.C} income", round(rc - rp_, 2), "=RevalIncomeCurrent", 0.01, COUNT)
    app = b.wb.Application                    # the last step: the saved workbook calculates automatically again
    app.Calculation = CALC_AUTOMATIC
    xl.wait_ready(app)


EXERCISES = [("Requirement 1", r1), ("Requirement 2", r2), ("Requirement 3", r3), ("Requirement 4", r4),
             ("Requirement 5", r5), ("Requirement 6", r6), ("Requirement 7", r7), ("Requirement 8", r8),
             ("Requirement 9", r9), ("Requirement 10", r10), ("Milestone 1", m1), ("Milestone 2", m2),
             ("Milestone 3", m3), ("Milestone 4", m4)]
