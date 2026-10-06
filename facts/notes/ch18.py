"""Chapter 18's instructor notes (make, buy, or reprice): the values each note states, and the claims its wording
makes.

The case is set in the summer of d.N and takes fiscal d.C as its base year. A family is the first seven characters of
the item code, and the families are those of the manufactured finished goods (Item.SupplyMode 'Manufactured'); a group
is the families' ItemGroup. Sales are invoice lines dated in d.C, the variance is that of the work order closes dated in
d.C, and completions are those dated in d.C. The inputs to 1090 are its d.C debits other than the closes' (PayrollSummary,
Factory Overhead entries, and Depreciation entries). Practical capacity is 80% of the WorkCenterCalendar hours of d.C,
the committed costs are the Manufacturing cost center's payroll with its employer costs (hourly crew and salaried
staff) and the depreciation charged to 1090, and the time-driven rate is the committed cost per practical hour. The
routing time of a unit is its routing's run hours plus its setup hours over the family's average batch of d.C. Every
value is the SQL twin of the case's workbook (scripts/verify/twins/ch18_twins.py): its regressions, Goal Seek targets,
Data Tables, and the Solver model, solved here with scipy's linprog. The explorer's totals of Requirement 5 and
Milestone 2 come from the CR18 reference model, which loads the item costs from a CSV written to six decimals; the
totals here use the same rounded costs.

Book constants: the contract manufacturer's quote (tbl-18-01, a hypothetical exhibit: its families, volumes, prices,
tooling, and freight), the planning assumptions the text sets in tbl-18-02 (the straight-time rate of 26.62 an hour, the
14.14% burden, 1.18 hours per standard hour at plan with 0.18 indirect, practical capacity at 80% of available hours,
the 40% margin floor, the 40% and 50% growth tests, eight 40-hour weeks of severance, materiality at 5% of income before
income taxes), and the 2028 price lists (the scenario's calendar, not the data's window). The other plan values of
tbl-18-02 come from the data as the Part III case computes them: the plan volume (the d.C completions' standard hours),
the salaried staff (the d.C salaried gross), and the depreciation of d.N (the FixedAsset schedule). The claims check
that the rate, burden, and hours per standard hour the text sets are still the Part III plan's.

Flags kept on purpose (claims that the author revisits on each roll): which quoted families are worth buying only with
the crew reduced (Requirements 6 and 10, Milestone 3), the opening scenario's "about ten points" (Requirement 1), and the
1.18 hours per standard hour that tbl-18-02 sets (Requirement 9).
"""

from __future__ import annotations

import statistics as st
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

import numpy as np
from scipy.optimize import linprog

from notes import note
from notes.case2 import volume
from notes.case3 import burden as part3_burden
from notes.case3 import depreciation as part3_depreciation
from notes.case3 import rate as part3_rate
from notes.case3 import working_days
from notes.case3 import yearly as part3_yearly

CHAPTER = "chapters/18-make-buy-or-reprice/chapter.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]

# tbl-18-01, the contract manufacturer's quote (hypothetical): family -> (annual volume, price, tooling), in its order.
QUOTE = {"FUR-BNH": (1450, 325, 18000), "FUR-NGT": (3200, 270, 22000), "FUR-SDB": (3800, 325, 25000),
         "FUR-TBL": (5000, 315, 30000), "LGT-SCN": (4600, 180, 15000), "TXT-PIL": (700, 220, 8000)}
FREIGHT = 0.03                  # inbound freight, a share of the quoted price
# tbl-18-02, the controller's planning assumptions that the text sets.
PRACTICAL = 0.80                # practical capacity, a share of the calendar's available hours
RATE, BURDEN = 26.62, 0.1414    # straight-time labor rate and burden
PLAN_HOURS = 1.18               # hours per standard hour at plan, of which PLAN_HOURS - 1 indirect
FLOOR = 0.40                    # gross margin floor on time-driven cost
GROWTH = (0.40, 0.50)           # the optional demand-growth tests
SEVERANCE_WEEKS, WEEK_HOURS = 8, 40
DAY_HOURS = 8                   # a position's day
MATERIALITY = 0.05              # of income before income taxes as recorded
DATA_TABLE = (0.75, 0.80, 0.85, 0.90)   # Requirement 4's Data Table of practical capacity
TOP_SHARE = 0.20                # the top fifth of items
COST_PLACES = 6                 # the reference model's item costs, as its CSV holds them
EXAMPLE = max(QUOTE, key=lambda f: QUOTE[f][0])  # the family the notes follow through: the quote's largest volume
STORY_GROUP = "Furniture"       # the group of the CFO's comparison in the opening scenario
MATERIALS = ("Raw Materials", "Packaging")
SIX = 6                         # the Part IV case's raw materials that carry the build


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def xr(x: float, places: int = 2) -> float:
    """Round half away from zero, as Excel's ROUND does."""
    return float(Decimal(repr(round(x, 9))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)) + 0.0


def short(family: str) -> str:
    """'FUR-BNH' -> 'BNH'."""
    return family[4:]


def wc_short(name: str) -> str:
    """A work center as the notes name it in running text: 'Finishing and Test Work Center' -> 'Finishing',
    'Quality Assurance Work Center' -> 'QA'."""
    base = name.removesuffix(" Work Center").split(" and ")[0]
    words = base.split()
    return base if len(words) == 1 else "".join(w[0] for w in words)


def wc_name(name: str) -> str:
    """A work center as Requirement 3's table names it: 'Finishing and Test Work Center' -> 'Finishing and Test'."""
    return name.removesuffix(" Work Center")


def month_name(ym: str) -> str:
    """'2024-02' -> 'February 2024'."""
    return f"{MONTHS[int(ym[5:7]) - 1]} {ym[:4]}"


# --- the model, computed once ------------------------------------------------------------------------

@lru_cache(maxsize=None)
def model(d) -> dict:
    """Every value of the case, as the twin computes it."""
    year = str(d.C)
    first, last = f"{d.C}-01-01", f"{d.C}-12-31"
    items = {r[0]: dict(code=r[1], group=r[2], type=r[3], mode=r[4], std=r[5], lst=r[6], conv=r[7] or 0.0,
                        stdh=r[8] or 0.0, routing=r[9], fam=r[1][:7])
             for r in d.q("SELECT ItemID, ItemCode, ItemGroup, ItemType, SupplyMode, StandardCost, ListPrice, "
                          "StandardConversionCost, StandardLaborHoursPerUnit, RoutingID FROM Item")}
    mfg = {i for i, v in items.items() if v["mode"] == "Manufactured" and v["type"] == "Finished Good"}
    fams = sorted({items[i]["fam"] for i in mfg})

    # Requirement 1: sales, closes, and completions of the year.
    sold = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])    # by item: units, revenue, standard cost, list value
    for iid, qty, total, base in d.q("SELECT l.ItemID, l.Quantity, l.LineTotal, l.BaseListPrice FROM SalesInvoiceLine l "
                                     "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                                     "WHERE si.InvoiceDate BETWEEN ? AND ?", first, last):
        s = sold[iid]
        s[0] += qty
        s[1] += total
        s[2] += qty * items[iid]["std"]
        s[3] += qty * (base or 0.0)
    var = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0])  # by family: total, material, labor, overhead, closes
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
        fam[f] = dict(name=f, short=short(f), group=sorted(groups)[0], groups=groups, ids=ids, units=units, rev=rev,
                      std=std, closes=var[f][4], variance=var[f][0], share=var[f][0] / completed_std,
                      vpu=vpu.get(f, 0.0), m_std=1 - std / rev, m_unit=1 - (std + vpu.get(f, 0.0) * units) / rev,
                      m_year=1 - (std + var[f][0]) / rev, m_purch=(1 - pstd / prev) if prev else None)
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
                  labor=sum(v[2] for v in var.values()), overhead=sum(v[3] for v in var.values()))
    mv_rate = totals["material"] / mat_std_completed

    # Requirement 2: the inputs to 1090 and what completions released.
    a1090 = d.account("1090")
    payroll = d.q("SELECT l.LineType, lte.LaborType, SUM(l.Hours), SUM(l.Amount) FROM PayrollRegisterLine l "
                  "JOIN PayrollRegister pr ON pr.PayrollRegisterID = l.PayrollRegisterID JOIN PayrollPeriod pp "
                  "ON pp.PayrollPeriodID = pr.PayrollPeriodID JOIN CostCenter cc ON cc.CostCenterID = pr.CostCenterID "
                  "LEFT JOIN LaborTimeEntry lte ON lte.LaborTimeEntryID = l.LaborTimeEntryID "
                  "WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = ? AND l.LineType NOT IN "
                  "('Benefits Deduction', 'Employee Tax Withholding') GROUP BY 1, 2", d.C)
    pay = {(t, k): (h, a) for t, k, h, a in payroll}
    src = dict(d.q("SELECT COALESCE(je.EntryType, g.SourceDocumentType), SUM(g.Debit) FROM GLEntry g LEFT JOIN JournalEntry je "
                   "ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry' "
                   "WHERE g.AccountID = ? AND g.PostingDate BETWEEN ? AND ? AND g.Debit > 0 "
                   "AND g.SourceDocumentType <> 'WorkOrderClose' GROUP BY 1", a1090, first, last))
    inputs = sum(src.values())
    foh = src.get("Factory Overhead", 0.0)
    dep = src.get("Depreciation", 0.0)
    released_gl = d.one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                        "AND SourceDocumentType = 'ProductionCompletion'", a1090, d.C)
    labor, var_oh, fixed_oh, conversion, stdh = d.q(
        "SELECT SUM(l.ExtendedStandardDirectLaborCost), SUM(l.ExtendedStandardVariableOverheadCost), "
        "SUM(l.ExtendedStandardFixedOverheadCost), SUM(l.ExtendedStandardConversionCost), "
        "SUM(l.QuantityCompleted * i.StandardLaborHoursPerUnit) FROM ProductionCompletionLine l JOIN ProductionCompletion pc "
        "ON pc.ProductionCompletionID = l.ProductionCompletionID JOIN Item i ON i.ItemID = l.ItemID "
        "WHERE pc.CompletionDate BETWEEN ? AND ?", first, last)[0]
    direct = sum(a for (t, k), (h, a) in pay.items() if k == "Direct Manufacturing")
    std_m = dict(d.q("SELECT substr(pc.CompletionDate, 1, 7), SUM(l.QuantityCompleted * i.StandardLaborHoursPerUnit) "
                     "FROM ProductionCompletionLine l JOIN ProductionCompletion pc ON pc.ProductionCompletionID = "
                     "l.ProductionCompletionID JOIN Item i ON i.ItemID = l.ItemID GROUP BY 1"))

    def series(where: str) -> dict:
        return defaultdict(float, d.q(
            f"SELECT substr(g.PostingDate, 1, 7), SUM(g.Debit) FROM GLEntry g LEFT JOIN JournalEntry je "
            f"ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry' "
            f"WHERE g.AccountID = ? AND {where} GROUP BY 1", a1090))
    fo_m = series("je.EntryType = 'Factory Overhead'")
    pay_m = series("g.SourceDocumentType = 'PayrollSummary'")
    dep_m = series("je.EntryType = 'Depreciation'")
    start = f"{d.F}-01"                                  # the start-up month the test leaves out
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
    dep_months = [dep_m[f"{year}-{k:02d}"] for k in range(1, 13)]
    runs = []
    for k, v in enumerate(dep_months):
        if runs and abs(runs[-1]["amount"] - v) < 0.005:
            runs[-1]["last"] = k
        else:
            runs.append(dict(amount=v, first=k, last=k))

    # Requirement 3: activities and capacity.
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
    activity = defaultdict(lambda: [0.0, 0, 0.0, 0])        # by group: units, work orders, setup hours, issue lines
    for f in sorted(batch):
        g = activity[items[next(i for i in mfg if items[i]["fam"] == f)]["group"]]
        g[0] += comp[f]
        g[1] += len(comp_wo[f])
        g[2] += sum(setup[wo_routing[wo]] for wo in comp_wo[f])
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
    centers = [dict(id=wc, name=wc_name(wc_names[wc]), short=wc_short(wc_names[wc]), avail=avail[wc],
                    pract=avail[wc] * PRACTICAL, used=used_wc[wc], of_avail=used_wc[wc] / avail[wc],
                    of_pract=used_wc[wc] / (avail[wc] * PRACTICAL)) for wc in sorted(avail)]

    # Requirement 4: the committed costs and the time-driven costs.
    pclass = {r[0]: dict(gross=r[1], tax=r[2], benefits=r[3], n=r[4]) for r in d.q(
        "SELECT e.PayClass, SUM(pr.GrossPay), SUM(pr.EmployerPayrollTax), SUM(pr.EmployerBenefits), COUNT(DISTINCT pr.EmployeeID) "
        "FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID JOIN Employee e "
        "ON e.EmployeeID = pr.EmployeeID JOIN CostCenter cc ON cc.CostCenterID = pr.CostCenterID "
        "WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = ? GROUP BY 1", d.C)}
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

    # Requirement 5: the explorer, on the finished goods sold (Services left out).
    fg = [i for i in sold if items[i]["type"] == "Finished Good" and sold[i][0] > 0]
    rev_fg = sum(sold[i][1] for i in fg)
    view, view_exact, item_m = defaultdict(float), defaultdict(float), {}
    for i in fg:
        u = sold[i][0]
        if i in mfg:
            c = costs(i)
            vals = dict(std=c["std"], absorp=c["absorp"], td=c["td"])
        else:
            vals = dict(std=items[i]["std"], absorp=items[i]["std"], td=items[i]["std"])
        for k, v in vals.items():
            view[k] += u * round(v, COST_PLACES)
            view_exact[k] += u * v
        item_m[i] = {k: sold[i][1] - u * v for k, v in vals.items()}
    top_n = round(len(fg) * TOP_SHARE)
    tops = {}
    for k in ("std", "absorp", "td"):
        ms = sorted((m[k] for m in item_m.values()), reverse=True)
        low = min(item_m, key=lambda i: item_m[i][k] / sold[i][1])
        tops[k] = dict(share=sum(ms[:top_n]) / sum(ms), negative=sum(1 for m in ms if m < 0),
                       low=items[low]["code"], low_margin=item_m[low][k] / sold[low][1])
    all_rev, all_std = d.q("SELECT SUM(l.LineTotal), SUM(l.Quantity * i.StandardCost) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                           "ON si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
                           "WHERE si.InvoiceDate BETWEEN ? AND ?", first, last)[0]
    services = d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = "
                     "l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID WHERE si.InvoiceDate BETWEEN ? AND ? "
                     "AND i.ItemGroup = 'Services'", first, last)
    unused_h = pract - used
    explorer = dict(n_items=len(fg), rev=rev_fg, std=rev_fg - view["std"], absorp=rev_fg - view["absorp"],
                    td=rev_fg - view["td"], td_unused=rev_fg - view["td"] - unused_h * td_rate,
                    year=rev_fg - view_exact["std"] - totals["total"], top_n=top_n, tops=tops,
                    all_rev=all_rev, all_std=all_std, services=services, std_cost=view_exact["std"],
                    exact={k: rev_fg - v for k, v in view_exact.items()})

    # Requirement 6: make or buy.
    labor_rate = RATE * (1 + BURDEN)
    pos_hours = PRACTICAL * DAY_HOURS * working_days(d, first, last)
    severance = SEVERANCE_WEEKS * WEEK_HOURS * labor_rate
    quoted = []
    for f, (vol, price, tooling) in QUOTE.items():
        w, u = fam[f]["unit"], fam[f]["units"]
        dq = price * (1 + FREIGHT)
        quoted.append(dict(name=f, short=short(f), volume=vol, price=price, tooling=tooling, units=u, kept=w["kept"],
                           reduced=w["reduced"], delivered=dq, absorp=(w["absorp"] - dq) * u, a_kept=(w["kept"] - dq) * u,
                           a_reduced=(w["reduced"] - dq) * u, be_kept=w["kept"] / (1 + FREIGHT),
                           be_reduced=w["reduced"] / (1 + FREIGHT), margin=1 - dq / w["price"], time=w["time"]))
    buy = [q for q in quoted if q["a_reduced"] > 0]
    lose = [q for q in quoted if q["a_reduced"] <= 0 and q["a_kept"] <= 0]
    gain = sum(q["a_reduced"] for q in buy)
    hours = sum(q["time"] * q["units"] for q in buy)
    positions = hours / pos_hours
    tooling = sum(q["tooling"] for q in buy)
    two_way = [[sum(((q["kept"] + share * crew_rate * q["time"]) - q["price"] * (1 + adj) * (1 + FREIGHT)) * q["units"]
                    for q in buy) for adj in (-0.10, 0.0, 0.10)] for share in (0.0, 0.5, 1.0)]
    buy_names = {q["name"] for q in buy}
    buy_material = sum(comp_item[i] * (items[i]["std"] - items[i]["conv"]) for i in comp_item if items[i]["fam"] in buy_names)
    issues = d.one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                   "AND SourceDocumentType = 'MaterialIssue'", d.account("1045"), d.C)
    build = d.q(f"WITH r AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM GoodsReceiptLine l JOIN GoodsReceipt g "
                f"ON g.GoodsReceiptID = l.GoodsReceiptID WHERE substr(g.ReceiptDate, 1, 4) = ?1 GROUP BY 1), "
                f"s AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM MaterialIssueLine l JOIN MaterialIssue m "
                f"ON m.MaterialIssueID = l.MaterialIssueID WHERE substr(m.IssueDate, 1, 4) = ?1 GROUP BY 1) "
                f"SELECT i.ItemID, i.ItemGroup, COALESCE(r.v, 0) - COALESCE(s.v, 0) FROM Item i "
                f"LEFT JOIN r ON r.ItemID = i.ItemID LEFT JOIN s ON s.ItemID = i.ItemID "
                f"WHERE i.ItemGroup IN ({','.join('?' * len(MATERIALS))}) ORDER BY 3 DESC", year, *MATERIALS)
    six = build[:SIX]
    fam_marks = ",".join("?" * len(buy_names))
    six_marks = ",".join(str(r[0]) for r in six)
    fam_issued = d.one(f"SELECT SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID = "
                       f"l.MaterialIssueID JOIN WorkOrder wo ON wo.WorkOrderID = m.WorkOrderID JOIN Item i ON i.ItemID = wo.ItemID "
                       f"WHERE substr(m.IssueDate, 1, 4) = ? AND substr(i.ItemCode, 1, 7) IN ({fam_marks})",
                       year, *sorted(buy_names)) if buy_names else 0.0
    six_issued = d.one(f"SELECT SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID = "
                       f"l.MaterialIssueID JOIN WorkOrder wo ON wo.WorkOrderID = m.WorkOrderID JOIN Item i ON i.ItemID = wo.ItemID "
                       f"WHERE substr(m.IssueDate, 1, 4) = ? AND substr(i.ItemCode, 1, 7) IN ({fam_marks}) "
                       f"AND l.ItemID IN ({six_marks})", year, *sorted(buy_names)) if buy_names else 0.0

    # Requirement 7: capacity.
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
    wcs = sorted(avail)
    headroom = {wc: avail[wc] * PRACTICAL / sum(load[f][wc] for f in fam) for wc in wcs}
    lp = []
    for growth in GROWTH:
        qf = [q for q in quoted]
        cvec = [q["delivered"] - q["kept"] for q in qf]
        a_ub, b_ub = [], []
        for wc in wcs:
            a_ub.append([-load[q["name"]][wc] / q["units"] for q in qf])
            b_ub.append(avail[wc] * PRACTICAL - sum(load[f][wc] * (1 + growth) for f in fam))
        bounds = [(0, q["units"] * (1 + growth)) for q in qf]
        res = linprog(cvec, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
        slack = np.array(b_ub) - np.array(a_ub) @ res.x
        duals = res.ineqlin.marginals
        binding = [dict(short=wc_short(wc_names[wcs[k]]), price=-duals[k]) for k in range(len(wcs)) if abs(slack[k]) < 1e-6]
        bought = [dict(short=q["short"], units=x, all=x >= bounds[k][1] - 0.5) for k, (q, x) in enumerate(zip(qf, res.x))
                  if x > 0.5]
        lp.append(dict(growth=growth, status=res.status, cost=res.fun, binding=binding, bought=bought))

    # Requirement 8: reprice.
    reprice = []
    for f in sorted(fam):
        w = fam[f]["unit"]
        if w["m_td"] < FLOOR:
            new = w["td"] / (1 - FLOOR)
            cm = w["price"] - w["kept"]
            reprice.append(dict(name=f, short=short(f), increase=new / w["price"] - 1,
                                loss=1 - cm / (cm + (new - w["price"])), revenue=(new - w["price"]) * fam[f]["units"]))

    # Requirement 9: standards and the statements.
    plan_stdh = stdh                                              # the Part III plan volume: the year's standard hours
    plan_salary = pclass["Salary"]["gross"]
    plan_dep = round(sum(part3_depreciation(d)["months"][d.N]), 2)
    parts = dict(direct=labor_rate, variable=fo_rate, indirect=(PLAN_HOURS - 1) * labor_rate,
                 supervision=plan_salary * (1 + BURDEN) / plan_stdh, depreciation=plan_dep / plan_stdh)
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
                           "ON pc.ProductionCompletionID = l.ProductionCompletionID WHERE pc.CompletionDate <= ? GROUP BY 1", asof):
            net[iid] += qc
        for iid, qs in d.q("SELECT l.ItemID, SUM(l.QuantityShipped) FROM ShipmentLine l JOIN Shipment s ON s.ShipmentID = "
                           "l.ShipmentID WHERE s.ShipmentDate <= ? GROUP BY 1", asof):
            net[iid] -= qs
        for iid, qr in d.q("SELECT l.ItemID, SUM(l.QuantityReturned) FROM SalesReturnLine l JOIN SalesReturn r ON r.SalesReturnID = "
                           "l.SalesReturnID WHERE r.ReturnDate <= ? GROUP BY 1", asof):
            net[iid] += qr
        on_hand = {i: u for i, u in net.items() if i in mfg and u > 0}
        negative = sorted(items[i]["code"] for i, u in net.items() if i in mfg and u < -0.05)
        sh = sum(u * items[i]["stdh"] for i, u in on_hand.items())
        cv = sum(u * items[i]["conv"] for i, u in on_hand.items())
        stock.append(dict(year=y, units=sum(on_hand.values()), std=sum(u * items[i]["std"] for i, u in on_hand.items()),
                          stdh=sh, conv=cv, per_hour=cv / sh, negative=negative, plan=sh * new_rate - cv,
                          one=sh * one_rate - cv, td=sh * td_std - cv, actual=sh * actual_rate - cv))

    return dict(items=items, fams=fams, fam=fam, unsold=unsold, groups=groups, totals=totals, mv_rate=mv_rate,
                comp=comp, comp_item=comp_item, sold=sold, pay=pay, src=src, inputs=inputs, foh=foh, dep=dep,
                released_gl=released_gl, labor=labor, var_oh=var_oh, fixed_oh=fixed_oh, conversion=conversion, stdh=stdh,
                direct=direct, months=months, with_start=with_start,
                fits=dict(fo=fit(fo_m, months), pay=fit(pay_m, months), dep=fit(dep_m, months), pay_start=fit(pay_m, with_start)),
                fo_ratio=fo_ratio, dep_months=dep_months, runs=runs, activities=activities, centers=centers,
                avail=avail_total, pract=pract, used=used, run_total=run_total, setup_total=setup_total, pclass=pclass,
                crew=crew, sal=sal, committed=committed, td_rate=td_rate, crew_rate=crew_rate, fo_rate=fo_rate,
                unused_h=unused_h, data_table=data_table, explorer=explorer, labor_rate=labor_rate, pos_hours=pos_hours,
                severance=severance, quoted=quoted, buy=buy, lose=lose, gain=gain, hours=hours, positions=positions,
                tooling=tooling, two_way=two_way, buy_material=buy_material, issues=issues, six=six,
                build=sum(r[2] for r in build), six_issued=six_issued, fam_issued=fam_issued,
                freed={wc: freed[wc] for wc in wcs if freed[wc] > 0.5}, wc_names=wc_names, supervision=supervision,
                headroom=headroom, wcs=wcs, lp=lp, reprice=reprice, plan_stdh=plan_stdh, plan_salary=plan_salary,
                plan_dep=plan_dep, parts=parts, new_rate=new_rate, one_rate=one_rate, td_std=td_std,
                actual_rate=actual_rate, stock=stock, batch=batch)


@lru_cache(maxsize=None)
def net_income(d, year: int) -> float:
    """Revenue less expenses of a fiscal year, the closes left out (the ledger records no income tax)."""
    return d.one(f"SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                 f"WHERE a.AccountType IN ('Revenue', 'Expense') AND g.FiscalYear = ? AND {d.no_closes()}", year)


def materiality(d, year: int) -> float:
    return xr(MATERIALITY * net_income(d, year))


def story(m: dict) -> dict:
    """The group of the CFO's comparison."""
    return next(g for g in m["groups"] if g["name"] == STORY_GROUP)


def by_year(m: dict, year: int) -> dict:
    return next(s for s in m["stock"] if s["year"] == year)


def plan_claims(d, claim) -> None:
    """The rate, burden, and hours per standard hour that tbl-18-02 sets are the Part III plan's."""
    claim(round(part3_rate(d, d.C), 2) == RATE, f"the Part III plan's labor rate ({d.C}, hours-weighted) is {RATE}")
    claim(part3_burden(d, d.C) == BURDEN, f"the Part III plan's burden is {BURDEN:.2%}")
    claim(round(part3_yearly(d)[0]["ratio"], 2) == PLAN_HOURS,
          f"the Part III plan's middle scenario is {PLAN_HOURS} hours per standard hour")


def ledger_5080(d) -> float:
    return d.one(f"SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                 d.account("5080"), d.C)


def make_buy_claims(m: dict, claim) -> None:
    claim(all(q["a_kept"] < 0 < q["a_reduced"] for q in m["buy"]),
          "the families to buy gain only with the crew reduced (with the crew kept, buying them costs more)")
    claim(len(m["buy"]) + len(m["lose"]) == len(QUOTE),
          "every quoted family either gains only with the crew reduced or loses either way")
    claim(len(m["buy"]) > 0 and len(m["lose"]) > 0, "some quoted families are worth buying and some are not")


# --- Milestones ------------------------------------------------------------------------------------

@note("ch18.m1", CHAPTER)
def m1(d, claim):
    m = model(d)
    claim(any(g["name"] == STORY_GROUP for g in m["groups"]), f"{STORY_GROUP} is one of the manufactured groups")
    g0 = story(m)
    return dict(g0=g0, rest=[g for g in m["groups"] if g is not g0], variance=m["totals"]["total"], inputs=m["inputs"],
                released=m["released_gl"], r_fo=m["fits"]["fo"]["r"], r_pay=m["fits"]["pay"]["r"],
                use=m["used"] / m["pract"])


@note("ch18.m2", CHAPTER)
def m2(d, claim):
    m = model(d)
    return dict(committed=m["committed"], td_rate=m["td_rate"], crew_rate=m["crew_rate"], unused_h=m["unused_h"],
                unused=m["unused_h"] * m["td_rate"], groups=m["groups"], e=m["explorer"])


@note("ch18.m3", CHAPTER)
def m3(d, claim):
    m = model(d)
    make_buy_claims(m, claim)
    kept = -sum(q["a_kept"] for q in m["buy"])
    claim(kept > 0, "with the crew kept, buying the families costs money")
    return dict(buy=m["buy"], lose=m["lose"], gain=m["gain"], positions=m["positions"],
                net=2 * m["gain"] - m["positions"] * m["severance"] - m["tooling"], kept_cost=kept,
                n_floor=word(len(m["reprice"])), reprice=sum(r["revenue"] for r in m["reprice"]))


@note("ch18.m4", CHAPTER)
def m4(d, claim):
    m = model(d)
    stock = m["stock"]
    incomes = [dict(year=b["year"], amount=b["plan"] - a["plan"]) for a, b in zip(stock, stock[1:])]
    return dict(new_rate=m["new_rate"], one_rate=m["one_rate"], current=m["conversion"] / m["stdh"], stock=stock,
                incomes=incomes)


# --- Requirement 1 -----------------------------------------------------------------------------------

@note("ch18.r1", CHAPTER)
def r1(d, claim):
    m = model(d)
    first, last = f"{d.C}-01-01", f"{d.C}-12-31"
    claim(len(m["unsold"]) == 1, "one manufactured family was not sold in the year")
    unmade = [f for f in m["unsold"] if not m["comp"].get(f)]
    claim(unmade == m["unsold"], "the family not sold was not made in the year either")
    claim(abs(m["totals"]["total"] - ledger_5080(d)) < 0.005, "the closes' variance equals account 5080 without the closes")
    claim(all(len(f["groups"]) == 1 for f in m["fam"].values()), "each family belongs to one item group")
    fams = list(m["fam"].values())
    g0 = story(m)
    claim(abs(g0["m_std"] - g0["m_year"] - 0.10) <= 0.01,
          f"{STORY_GROUP}'s margin falls about ten points with the year's variance")
    beats = [f["name"] for f in fams if f["m_purch"] is not None and f["m_unit"] > f["m_purch"] and f["m_year"] > f["m_purch"]]
    either = [f["name"] for f in fams if f["m_purch"] is not None and (f["m_unit"] > f["m_purch"] or f["m_year"] > f["m_purch"])]
    claim(len(beats) == 1 and beats == either,
          "only one family beats its purchased benchmark after the variance, on either measure")
    lines, mismatched = d.q("SELECT COUNT(*), SUM(sil.BaseListPrice IS NULL OR i.ListPrice IS NULL OR ABS(sil.BaseListPrice - "
                            "i.ListPrice) > 0.004) FROM SalesInvoiceLine sil JOIN Item i ON i.ItemID = sil.ItemID")[0]
    claim(mismatched == 0, "BaseListPrice equals Item.ListPrice on every invoice line")
    claim(d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Item i ON i.ItemID = sl.ItemID WHERE sl.ExtendedStandardCost IS NULL "
                "OR ABS(sl.ExtendedStandardCost - ROUND(sl.QuantityShipped * i.StandardCost, 2)) > 0.011") == 0,
          "every ShipmentLine standard cost equals quantity x StandardCost")
    max_diff = d.one("SELECT MAX(ABS(l.ExtendedStandardTotalCost - l.QuantityCompleted * i.StandardCost)) FROM "
                     "ProductionCompletionLine l JOIN Item i ON i.ItemID = l.ItemID")
    claim(max_diff < 0.025, "completion lines differ from quantity x StandardCost by at most 0.02")
    all_years = d.one("SELECT COUNT(*) FROM (SELECT l.ItemID FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = "
                      "l.SalesInvoiceID WHERE si.InvoiceDate BETWEEN ? AND ? GROUP BY 1 "
                      "HAVING COUNT(DISTINCT substr(si.InvoiceDate, 1, 4)) = ?)", f"{d.F}-01-01", last, len(d.years))
    po = defaultdict(lambda: [0.0, 0.0])
    for code, qty, cost, lst in d.q("SELECT i.ItemCode, l.Quantity, l.UnitCost, i.ListPrice FROM PurchaseOrderLine l "
                                    "JOIN PurchaseOrder p ON p.PurchaseOrderID = l.PurchaseOrderID JOIN Item i ON i.ItemID = l.ItemID "
                                    "WHERE i.SupplyMode = 'Purchased' AND i.ItemType = 'Finished Good' "
                                    "AND p.OrderDate BETWEEN ? AND ?", first, last):
        po[code[:7]][0] += qty * cost
        po[code[:7]][1] += qty * lst
    purchased = []
    for f in QUOTE:
        claim(po[f][1] > 0, f"Charles River bought products of {f} in the year")
        purchased.append(dict(short=short(f), ratio=po[f][0] / po[f][1] if po[f][1] else 0.0))
    total, low, high = d.q("SELECT SUM(l.Quantity * l.UnitCost) / SUM(l.Quantity * i.StandardCost), MIN(l.UnitCost / i.StandardCost), "
                           "MAX(l.UnitCost / i.StandardCost) FROM PurchaseOrderLine l JOIN PurchaseOrder p ON p.PurchaseOrderID = "
                           "l.PurchaseOrderID JOIN Item i ON i.ItemID = l.ItemID WHERE i.SupplyMode = 'Purchased' AND "
                           "i.ItemType = 'Finished Good' AND p.OrderDate BETWEEN ? AND ?", first, last)[0]
    return dict(unsold=m["unsold"], t=m["totals"], fams=fams, groups=m["groups"], story=g0, beats=beats, lines=lines,
                max_diff=max_diff, all_years=all_years, n_years=word(len(d.years)), purchased=purchased, avg_ratio=total,
                low_ratio=low, high_ratio=high)


# --- Requirement 2 -----------------------------------------------------------------------------------

@note("ch18.r2", CHAPTER)
def r2(d, claim):
    m = model(d)
    claim(set(m["src"]) == {"PayrollSummary", "Factory Overhead", "Depreciation"},
          "the debits to 1090 other than the closes' are PayrollSummary, Factory Overhead, and Depreciation entries")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'WorkOrderClose' "
                "AND Debit > 0", d.account("1090"), d.C) > 0, "favorable closes post debits to 1090")
    pay = m["pay"]
    kinds = {("Regular Earnings", "Direct Manufacturing"), ("Overtime Earnings", "Direct Manufacturing"),
             ("Regular Earnings", "Indirect Manufacturing"), ("Overtime Earnings", "Indirect Manufacturing"),
             ("Salary Earnings", None), ("Employer Payroll Tax", None), ("Employer Benefits", None)}
    claim(set(pay) == kinds, "the Manufacturing payroll lines are direct and indirect regular and overtime earnings, "
                             "salaries, employer tax, and benefits")
    payroll = sum(a for h, a in pay.values())
    claim(abs(payroll - m["src"].get("PayrollSummary", 0.0)) < 0.005,
          "the Manufacturing payroll equals the PayrollSummary debits to 1090")

    def line(t, k):
        h, a = pay.get((t, k), (0.0, 0.0))
        return dict(h=h or 0.0, a=a)
    applied = m["var_oh"] + m["fixed_oh"]
    actual_oh = m["inputs"] - m["direct"]
    third = applied / actual_oh
    claim(1 / 3 <= third < 0.4, "the overhead applied is a little more than a third of the actual overhead")
    fits = m["fits"]
    oh_rate = applied / m["stdh"]
    claim(fits["fo"]["r"] > 0.9 and abs(fits["fo"]["slope"] / oh_rate - 1) < 0.05
          and all(abs(x - 1) < 0.02 for x in m["fo_ratio"]),
          "the Factory Overhead entries vary with output at about the applied overhead rate")
    claim(m["foh"] <= applied, "the overhead the standards apply covers the Factory Overhead entries (the overhead that varies)")
    claim(abs(fits["pay"]["r"]) < 0.2, "payroll to 1090 does not move with output (committed)")
    claim(fits["pay_start"]["r"] > fits["pay"]["r"] + 0.2, "with the start-up month, payroll appears to move with output")
    schedule = part3_depreciation(d)["months"][d.C]
    claim(all(abs(a - b) < 0.005 for a, b in zip(m["dep_months"], schedule)),
          "the monthly depreciation charged to 1090 follows the asset schedule")
    runs = m["runs"]
    claim(len(runs) == 3 and runs[0]["first"] == runs[0]["last"] == 0 and runs[2]["last"] == 11,
          "the year's depreciation has three monthly levels: January, a middle run, and the rest of the year")
    claim(m["used"] / m["avail"] < 0.75, "the plant runs well below its capacity")
    months = m["months"]
    return dict(dreg=line("Regular Earnings", "Direct Manufacturing"), dot=line("Overtime Earnings", "Direct Manufacturing"),
                ireg=line("Regular Earnings", "Indirect Manufacturing"), iot=line("Overtime Earnings", "Indirect Manufacturing"),
                salaries=line("Salary Earnings", None)["a"], tax=line("Employer Payroll Tax", None)["a"],
                benefits=line("Employer Benefits", None)["a"], payroll=payroll, foh=m["foh"], dep=m["dep"], inputs=m["inputs"],
                released_gl=m["released_gl"], conversion=m["conversion"], labor=m["labor"], var_oh=m["var_oh"],
                fixed_oh=m["fixed_oh"], stdh=m["stdh"], conv_rate=m["conversion"] / m["stdh"],
                labor_rate=m["labor"] / m["stdh"], oh_rate=oh_rate, actual_rate=m["inputs"] / m["stdh"], direct=m["direct"],
                actual_oh=actual_oh, actual_oh_rate=actual_oh / m["stdh"], times=actual_oh / applied, third=third,
                n_months=len(months), first_month=month_name(months[0]), last_month=month_name(months[-1]),
                start_month=month_name(m["with_start"][0]), fo=fits["fo"], pay=fits["pay"], pay_start=fits["pay_start"],
                dep_fit=fits["dep"], fo_ratio=m["fo_ratio"],
                runs=[dict(amount=r["amount"], first=MONTHS[r["first"]], last=MONTHS[r["last"]]) for r in runs])


# --- Requirement 3 -----------------------------------------------------------------------------------

@note("ch18.r3", CHAPTER)
def r3(d, claim):
    m = model(d)
    acts = m["activities"]
    small = max(acts, key=lambda a: a["setup"])
    claim(small is min(acts, key=lambda a: a["batch"]), "the group with the most setup per unit has the smallest batches")
    claim(all(1.75 <= small["setup"] / a["setup"] <= 2.5 for a in acts if a is not small),
          "its batches carry about twice the setup per unit of the other groups")
    claim(abs(m["run_total"] - m["stdh"]) < 0.01, "run hours on the year's completions equal the standard labor hours")
    return dict(acts=acts, small=small["name"], run=m["run_total"], setup=m["setup_total"],
                total=m["run_total"] + m["setup_total"], centers=m["centers"], avail=m["avail"], pract=m["pract"],
                used=m["used"], of_avail=m["used"] / m["avail"], of_pract=m["used"] / m["pract"])


# --- Requirement 4 -----------------------------------------------------------------------------------

@note("ch18.r4", CHAPTER)
def r4(d, claim):
    m = model(d)
    conv = m["used"] * m["td_rate"] + m["foh"]
    unused = m["unused_h"] * m["td_rate"]
    claim(abs(conv + unused - m["inputs"]) < 0.01, "the products' conversion plus the unused capacity equals the inputs to 1090")
    hourly = d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter c ON c.CostCenterID = e.CostCenterID "
                   "WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly'")
    claim(m["pclass"]["Hourly"]["n"] == hourly, "the hourly crew is every hourly manufacturing employee")
    fams = list(m["fam"].values())
    claim(all(f["unit"]["std"] < f["unit"]["td"] for f in fams), "time-driven cost is above standard for every family")
    above = [f["name"] for f in fams if f["unit"]["td"] > f["unit"]["absorp"]]     # time-driven above absorption
    claim(m["labor"] / m["stdh"] < m["labor_rate"], "the standards' labor per standard hour is below the current rate with "
                                                     "burden (the standards miss the rate increase)")
    e = m["explorer"]
    claim(e["std"] > e["td"] > e["absorp"], "in total, time-driven cost lies between standard and absorption")
    # where each group's time-driven cost sits, by its totals: nearer standard or nearer absorption
    near = defaultdict(list)
    for g in m["groups"]:
        fs = [f for f in fams if f["group"] == g["name"]]
        over_std = sum((f["unit"]["td"] - f["unit"]["std"]) * f["units"] for f in fs)
        under_absorp = sum((f["unit"]["absorp"] - f["unit"]["td"]) * f["units"] for f in fs)
        near["standard" if over_std < under_absorp else "absorption"].append(g["name"])
    tops = m["explorer"]["tops"]
    claim(all(t["negative"] == 0 for t in tops.values()), "no item loses money under any view")
    table = m["data_table"]
    steps = [abs(a["example"] - b["example"]) for a, b in zip(table, table[1:])]
    moves = [abs(a["unused"] - b["unused"]) for a, b in zip(table, table[1:])]
    claim(max(steps) < 10, f"{EXAMPLE}'s cost moves by a few dollars across the Data Table")
    claim(all(100_000 <= x < 1_000_000 for x in moves), "the unused capacity moves by hundreds of thousands at each step")
    return dict(committed=m["committed"], crew=m["pclass"]["Hourly"], sal=m["pclass"]["Salary"], dep=m["dep"],
                pract=m["pract"], td_rate=m["td_rate"], crew_rate=m["crew_rate"], sup_rate=m["td_rate"] - m["crew_rate"],
                fo_rate=m["fo_rate"], mv_rate=m["mv_rate"], conv=conv, unused_h=m["unused_h"], unused=unused,
                unused_crew=m["unused_h"] * m["crew_rate"], total=conv + unused, fams=fams, groups=m["groups"],
                n_items=m["explorer"]["n_items"], top_n=m["explorer"]["top_n"], tops=tops, table=table, example=EXAMPLE,
                above=above, td_over=e["std"] - e["td"], absorp_over=e["td"] - e["absorp"], near_std=near["standard"],
                near_absorp=near["absorption"])


# --- Requirement 5 -----------------------------------------------------------------------------------

@note("ch18.r5", CHAPTER)
def r5(d, claim):
    m = model(d)
    e = m["explorer"]
    first, last = f"{d.C}-01-01", f"{d.C}-12-31"
    others = d.q("SELECT DISTINCT i.ItemType, i.ItemGroup FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = "
                 "l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID WHERE si.InvoiceDate BETWEEN ? AND ? "
                 "AND i.ItemType <> 'Finished Good'", first, last)
    claim(all(g == "Services" for t, g in others), "the lines that are not finished goods are Services")
    claim(abs(e["all_rev"] - e["services"] - e["rev"]) < 0.005, "finished goods revenue is all revenue less Services")
    claim(abs(e["all_std"] - e["std_cost"]) < 0.005,
          "Services carry no standard cost, so the finished goods' standard cost is the year's")
    claim(abs(e["year"] - e["absorp"]) > 1, "the margin with the year's variance differs from the absorption margin")
    made = sum(m["comp"].values())
    sold_mfg = sum(f["units"] for f in m["fam"].values())
    claim(made > sold_mfg, "the plant completed more units than it sold in the year (an inventory build)")
    claim(abs(m["totals"]["total"] - ledger_5080(d)) < 0.005, "the variances charged equal 5080")
    ex = m["fam"][EXAMPLE]
    # the totals use the item costs at six decimals, as CR18's CSV holds them; the views whose unrounded total differs
    labels = dict(std="standard", absorp="absorption", td="time-driven")
    exact = [dict(view=labels[k], value=e["exact"][k]) for k in ("std", "absorp", "td") if xr(e["exact"][k]) != xr(e[k])]
    return dict(e=e, example=EXAMPLE, ex_std=ex["m_std"], ex_absorp=ex["m_unit"], ex_td=ex["unit"]["m_td"], exact=exact)


# --- Requirement 6 -----------------------------------------------------------------------------------

@note("ch18.r6", CHAPTER)
def r6(d, claim):
    m = model(d)
    make_buy_claims(m, claim)
    quoted = m["quoted"]
    gap = max(abs(q["volume"] / q["units"] - 1) for q in quoted)     # the quoted volumes against the year's sales
    claim(gap < 0.10, "the quoted volumes are close to the year's sales (within 10% for each family)")
    six = m["six"]
    claim(all(r[1] == "Raw Materials" for r in six), "the six largest builds are raw materials")
    claim(sum(r[2] for r in six) > 0.9 * m["build"], "the six raw materials carry the materials build (over 90% of it)")
    claim(m["six_issued"] < m["buy_material"], "the six raw materials are part of the three families' material")
    absorp_buy = sum(1 for q in quoted if q["absorp"] > 0)
    kept = -sum(q["a_kept"] for q in m["buy"])
    return dict(quoted=quoted, mat_factor=1 + m["mv_rate"], fo_rate=m["fo_rate"], crew_rate=m["crew_rate"],
                absorp_buy=word(absorp_buy), n_quoted=word(len(quoted)), buy=m["buy"], lose=m["lose"], gain=m["gain"],
                hours=m["hours"], positions=m["positions"], pos_hours=m["pos_hours"], weeks=SEVERANCE_WEEKS,
                week_hours=WEEK_HOURS, labor_rate=m["labor_rate"], severance=m["severance"],
                severance_total=m["positions"] * m["severance"], tooling=m["tooling"],
                net=2 * m["gain"] - m["positions"] * m["severance"] - m["tooling"], n_buy=word(len(m["buy"])),
                kept_cost=kept, two_way=m["two_way"], buy_material=m["buy_material"], gap=gap,
                fam_issued=m["fam_issued"], issues=m["issues"], share=m["fam_issued"] / m["issues"],
                six_issued=m["six_issued"], n_six=word(len(six)))


# --- Requirement 7 -----------------------------------------------------------------------------------

@note("ch18.r7", CHAPTER)
def r7(d, claim):
    m = model(d)
    freed = [dict(short=wc_short(m["wc_names"][wc]), hours=h) for wc, h in m["freed"].items()]
    total = sum(m["freed"].values())
    claim(m["unused_h"] > total, "the plant already leaves more practical hours unused than buying would free")
    head = m["headroom"]
    first_limit = min(head.values())
    claim(0.35 <= first_limit - 1 <= 0.45, "growth of about 40% reaches the first limit")
    lp = m["lp"]
    claim(all(s["status"] == 0 for s in lp), "the Solver model solves at each growth rate")
    least = wc_short(m["wc_names"][min(head, key=head.get)])
    claim(all(b["short"] == least for b in lp[0]["binding"]),
          "a work center that binds at the first growth rate is the one with the least headroom")
    return dict(buy=m["buy"], freed=freed, total=total, use_before=m["used"] / m["pract"],
                use_after=(m["used"] - total) / m["pract"], unused_h=m["unused_h"],
                unused_positions=m["unused_h"] / m["pos_hours"], n_buy=word(len(m["buy"])), supervision=m["supervision"],
                crew_hours=m["hours"], crew_cost=m["hours"] * m["crew_rate"],
                headroom=[dict(short=wc_short(m["wc_names"][wc]), ratio=head[wc]) for wc in m["wcs"]],
                lp=[dict(growth=s["growth"], cost=float(s["cost"]),
                         binding=[dict(short=b["short"], price=float(b["price"])) for b in s["binding"]],
                         bought=[dict(short=b["short"], units=float(b["units"]), all=bool(b["all"])) for b in s["bought"]])
                    for s in lp])


# --- Requirement 8 -----------------------------------------------------------------------------------

@note("ch18.r8", CHAPTER)
def r8(d, claim):
    m = model(d)
    buy_names = {q["name"] for q in m["buy"]}
    claim(all(q["margin"] >= FLOOR for q in m["buy"]), "the families to buy clear the floor at their delivered price")
    need = [r["short"] for r in m["reprice"] if r["name"] not in buy_names]
    claim(all(v["z"] < 2 for v in volume(d)), "no promotion raised volume (no lift is unusually high)")
    lists = d.q("SELECT pl.PriceListID, pl.Status, MIN(pll.UnitPrice / i.ListPrice), MAX(pll.UnitPrice / i.ListPrice) "
                "FROM PriceList pl JOIN PriceListLine pll ON pll.PriceListID = pl.PriceListID JOIN Item i ON i.ItemID = pll.ItemID "
                "GROUP BY 1, 2 ORDER BY 1")
    active = [r for r in lists if r[1] == "Active"]
    ends = sorted({r[0] for r in d.q("SELECT EffectiveEndDate FROM PriceList WHERE Status = 'Active'")})
    claim(ends == [f"{d.C}-12-31"], "every active price list ends at the end of the base year")
    expired = [r[0] for r in d.q("SELECT DISTINCT pl.PriceListID FROM PriceList pl JOIN PriceListLine pll ON pll.PriceListID = "
                                 "pl.PriceListID JOIN SalesOrderLine l ON l.PriceListLineID = pll.PriceListLineID JOIN SalesOrder o "
                                 "ON o.SalesOrderID = l.SalesOrderID WHERE pl.Status = 'Expired' "
                                 "AND o.OrderDate > pl.EffectiveEndDate ORDER BY 1")]
    claim(expired == [r[0] for r in d.q("SELECT PriceListID FROM PriceList WHERE Status = 'Expired' ORDER BY 1")],
          "every expired list was still used after its end date")
    approvers = {r[0] for r in d.q("SELECT e.JobTitle FROM PriceOverrideApproval a JOIN Employee e ON e.EmployeeID = "
                                   "a.ApprovedByEmployeeID WHERE a.Status = 'Approved'")}
    claim(approvers == {"Sales Manager"}, "the Sales Manager approves the overrides")
    return dict(reprice=m["reprice"], revenue=sum(r["revenue"] for r in m["reprice"]), buy=m["buy"], need=need,
                low=min(r[2] for r in active), high=max(r[3] for r in active), expired=expired)


# --- Requirement 9 -----------------------------------------------------------------------------------

@note("ch18.r9", CHAPTER)
def r9(d, claim):
    m = model(d)
    plan_claims(d, claim)
    s_f, s_p, s_c = by_year(m, d.F), by_year(m, d.P), by_year(m, d.C)
    mat_p, mat_c = materiality(d, d.P), materiality(d, d.C)
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountName LIKE '%Income Tax%'") == 0,
          "the ledger records no income tax, so income before income taxes is net income")
    claim(s_p["plan"] > mat_p and s_c["plan"] > mat_c, "both balance sheet effects are above materiality")
    claim(s_p["plan"] - s_f["plan"] < mat_p and s_c["plan"] - s_p["plan"] < mat_c, "the income effects are below materiality")
    claim(s_p["one"] < mat_p and s_c["one"] > mat_c,
          "at 1.0 hours the prior year's balance falls below materiality and the current year's stays above")
    negatives = [dict(code=c, year=s["year"]) for s in m["stock"] for c in s["negative"]]
    opening = d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")
    opening_fg = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?",
                       d.account("1040"), opening)
    return dict(plan_stdh=m["plan_stdh"], plan_hours=PLAN_HOURS, rate=RATE, burden=BURDEN, p=m["parts"],
                plan_salary=m["plan_salary"], plan_dep=m["plan_dep"], new_rate=m["new_rate"], one_rate=m["one_rate"],
                current=m["conversion"] / m["stdh"], td_std=m["td_std"], actual=m["actual_rate"], quoted=m["quoted"],
                negatives=negatives, stock=m["stock"], s_f=s_f, s_p=s_p, s_c=s_c, mat_p=mat_p, mat_c=mat_c,
                opening_fg=opening_fg)


# --- Requirement 10 ----------------------------------------------------------------------------------

@note("ch18.r10", CHAPTER)
def r10(d, claim):
    m = model(d)
    make_buy_claims(m, claim)
    unused_positions = m["unused_h"] / m["pos_hours"]
    claim(unused_positions > m["positions"] and m["unused_h"] * m["crew_rate"] > m["gain"],
          "fitting the crew to the work is worth more than outsourcing")
    below = {r["name"] for r in m["reprice"]}
    buy_names = [q["name"] for q in m["buy"]]
    need = [r["short"] for r in m["reprice"] if r["name"] not in buy_names]
    return dict(lose=m["lose"], buy=m["buy"], positions=m["positions"], unused_positions=unused_positions, need=need,
                buy_below=[q["short"] for q in m["buy"] if q["name"] in below])
