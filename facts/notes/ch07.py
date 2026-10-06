"""Chapter 7's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

import math
import statistics

from notes import note

EXERCISES = "chapters/07-analysis-and-modeling/_exercises.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
PRODUCTS = ["Furniture", "Lighting", "Textiles", "Accessories"]
GROUPS = PRODUCTS + ["Services"]


def fit(xs: list[float], ys: list[float]) -> dict:
    """Least squares of y on x, as the ToolPak's Regression tool and FORECAST.LINEAR compute it."""
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    sse = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - my) ** 2 for y in ys)
    return dict(a=a, b=b, r2=1 - sse / sst, se=math.sqrt(sse / (n - 2)))


def revenue_by_month(d) -> dict[str, float]:
    """InvoiceLines revenue by month of InvoiceDate (YYYY-MM), over the window's months, as Tutorial 7.1's series."""
    return dict(d.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                    "JOIN SalesInvoice si USING (SalesInvoiceID) WHERE CAST(substr(si.InvoiceDate, 1, 4) AS INT) "
                    "BETWEEN ? AND ? GROUP BY 1 ORDER BY 1", d.F, d.C))


def commission_close(d, year: int) -> str:
    """The year-end close that posts to 6290 in a fiscal year (the only journal entry on the account)."""
    rows = [r[0] for r in d.q("SELECT DISTINCT VoucherNumber FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                              "AND SourceDocumentType = 'JournalEntry'", d.account("6290"), year)]
    assert len(rows) == 1 and rows[0] in d.closes, rows
    return rows[0]


def commission_rate(d) -> tuple[float, float, float]:
    """Tutorial 7.3's rate: fiscal C commission expense (6290 without the close) over all of C's revenue."""
    expense = d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                    d.account("6290"), d.C)
    revenue = d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
                    "WHERE substr(si.InvoiceDate, 1, 4) = ?", str(d.C))
    return expense / revenue, expense, revenue


@note("ch07.ex1", EXERCISES)
def ex1(d, claim):
    quarters = {(g, int(y), int(k)): v for g, y, k, v in d.q(
        "SELECT i.ItemGroup, substr(si.InvoiceDate, 1, 4), (CAST(substr(si.InvoiceDate, 6, 2) AS INT) + 2) / 3, "
        "SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
        "JOIN Item i USING (ItemID) GROUP BY 1, 2, 3")}
    claim({g for g, _, _ in quarters} == set(GROUPS), "the item groups are the five the note lists")
    window = [(y, k) for y in d.years for k in range(1, 5)]
    claim(len(window) == 12, "the window holds twelve quarters")
    mape, best = [], {}
    for g in GROUPS:
        fitted = [quarters[(g, y, k)] for y in (d.F, d.P) for k in range(1, 5)]
        actual = [quarters[(g, d.C, k)] for k in range(1, 5)]
        line = fit(list(range(1, 9)), fitted)
        forecasts = dict(trend=[line["a"] + line["b"] * x for x in range(9, 13)],
                         mean=[statistics.mean(fitted)] * 4,
                         same=[quarters[(g, d.P, k)] for k in range(1, 5)])
        errors = {m: statistics.mean(abs(f - a) / a for f, a in zip(fc, actual)) for m, fc in forecasts.items()}
        mape.append((g, [errors["trend"], errors["mean"], errors["same"]]))
        best[g] = min(errors, key=errors.get)
    e = dict(mape)
    claim(e["Furniture"][1] < e["Furniture"][0] and e["Furniture"][2] < e["Furniture"][0],
          "the mean and the same quarter last year beat the trend for Furniture")
    claim(best["Lighting"] == "trend", "the trend suits Lighting best")
    lighting = [sum(quarters[("Lighting", y, k)] for k in range(1, 5)) for y in (d.P, d.C)]
    claim(lighting[1] > lighting[0], f"Lighting's revenue grew in {d.C}")
    claim(all(best[g] == "mean" for g in ("Textiles", "Accessories", "Services")),
          "the mean suits Textiles, Accessories, and Services best")
    claim(len(set(best.values())) > 1, "no single method wins")
    claim(all(e["Services"][i] == max(errors[i] for _, errors in mape) for i in range(3)),
          "Services has the largest error under every method (volatile under every method)")
    months = revenue_by_month(d)
    totals = [sum(quarters[(g, y, k)] for g in GROUPS) for y, k in window]
    claim(totals[0] == min(totals) and min(months, key=months.get) == f"{d.F}-01",
          f"Q1 {d.F} is the lowest quarter, depressed by the start-up month")
    q1 = [(g, quarters[(g, d.C, 1)]) for g in GROUPS]
    means = []
    for g in GROUPS:
        values = [quarters[(g, y, k)] for y, k in window]
        means.append((g, statistics.mean(values), min(values), max(values)))
    claim(len(months) == 12 * len(d.years), "every month of the window has revenue (Tutorial 7.1's series)")
    later = [v for k, v in sorted(months.items())][1:]
    return dict(mape=mape, q1=q1, means=means, totals=totals, company=3 * statistics.mean(later))


@note("ch07.ex2", EXERCISES)
def ex2(d, claim):
    categories = "BudgetCategory IN ('Revenue', 'COGS', 'Operating Expense')"
    gaps = {}
    for y in d.years:
        summary = d.one("SELECT SUM(BudgetAmount) FROM Budget WHERE FiscalYear = ?", y)
        detail = d.one(f"SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND {categories}", y)
        gaps[y] = detail - summary
    summary, rows = d.q("SELECT SUM(BudgetAmount), COUNT(*) FROM Budget WHERE FiscalYear = ?", d.C)[0]
    detail = d.one(f"SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND {categories}", d.C)
    blank = d.q("SELECT a.AccountID, a.AccountNumber, a.AccountName, COUNT(*), COUNT(DISTINCT bl.Month), SUM(bl.BudgetAmount) "
                "FROM BudgetLine bl JOIN Account a USING (AccountID) WHERE bl.FiscalYear = ? "
                "AND bl.BudgetCategory = 'Operating Expense' AND bl.CostCenterID IS NULL GROUP BY 1, 2, 3 ORDER BY 2", d.C)
    blank_total = sum(r[5] for r in blank)
    blank_rows = sum(r[3] for r in blank)
    claim(abs((detail - summary) - blank_total) < 0.005,
          "the difference is exactly the operating-expense rows with a blank CostCenterID")
    claim(d.one(f"SELECT COUNT(*) FROM BudgetLine WHERE FiscalYear = ? AND {categories} AND CostCenterID IS NULL "
                "AND BudgetCategory <> 'Operating Expense'", d.C) == 0,
          "only operating-expense rows have a blank CostCenterID")
    claim(all(r[3] == 12 and r[4] == 12 for r in blank), "the blank rows are twelve months for each account")
    ids = ",".join(str(r[0]) for r in blank)
    claim(d.one(f"SELECT COUNT(*) FROM Budget WHERE FiscalYear = ? AND AccountID IN ({ids})", d.C) == 0,
          "the Budget Table omits these accounts entirely")
    by_summary = dict(d.q("SELECT AccountID, SUM(BudgetAmount) FROM Budget WHERE FiscalYear = ? GROUP BY 1", d.C))
    by_detail = dict(d.q(f"SELECT AccountID, SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND {categories} "
                         "AND CostCenterID IS NOT NULL GROUP BY 1", d.C))
    claim(all(abs(by_summary.get(a, 0) - by_detail.get(a, 0)) < 0.005 for a in set(by_summary) | set(by_detail)),
          "every other account agrees, so the blank rows are the whole difference")
    strip = lambda name: name[:-len(" Expense")] if name.endswith(" Expense") else name
    return dict(summary=summary, rows=rows, detail=detail, gap=detail - summary, blank_rows=blank_rows,
                accounts=[(n, strip(name), amount) for _, n, name, _, _, amount in blank],
                earlier=[(y, gaps[y]) for y in (d.F, d.P)])


@note("ch07.ex3", EXERCISES)
def ex3(d, claim):
    revenue, cost = d.q("SELECT SUM(l.LineTotal), SUM(l.Quantity * i.StandardCost) FROM SalesInvoiceLine l "
                        "JOIN SalesInvoice si USING (SalesInvoiceID) JOIN Item i USING (ItemID) "
                        "WHERE substr(si.InvoiceDate, 1, 4) = ?", str(d.C))[0]
    close = commission_close(d, d.C)
    commissions = d.one("SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND VoucherNumber <> ?",
                        d.account("6290"), d.C, close)
    claim(d.one("SELECT MAX(i.StandardCost) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
                "JOIN Item i USING (ItemID) WHERE i.ItemGroup = 'Services' AND substr(si.InvoiceDate, 1, 4) = ?", str(d.C)) == 0,
          "the Services lines carry no standard cost, so design staff are among the fixed costs")
    cm = revenue - cost - commissions
    ratio = cm / revenue
    opex = d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory = 'Operating Expense'", d.C)
    budget_commission = d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND AccountID = ?",
                              d.C, d.account("6290"))
    fixed = opex - budget_commission
    budget = dict(d.q("SELECT CAST(a.AccountNumber AS TEXT), SUM(bl.BudgetAmount) FROM BudgetLine bl JOIN Account a USING (AccountID) "
                      "WHERE bl.FiscalYear = ? AND bl.BudgetCategory = 'Operating Expense' GROUP BY 1", d.C))
    actual = dict(d.q(f"SELECT CAST(a.AccountNumber AS TEXT), SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                      f"WHERE g.FiscalYear = ? AND {d.no_closes()} GROUP BY 1", d.C))
    recurring = [n for n in budget if n not in ("6060", "6290")]
    claim(all(abs(actual.get(n, 0) / budget[n] - 1) < 0.05 for n in recurring),
          "every budgeted operating-expense account except 6060 and 6290 (salaries, rent, depreciation, and the others) "
          "came within a few percent of actual")
    breakeven = fixed / ratio
    names = dict(d.q("SELECT CAST(AccountNumber AS TEXT), AccountName FROM Account WHERE AccountNumber IN (5050, 5060, 5080)"))
    added = [(n, names[n].replace(" Expense", ""),
              d.one("SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                    "AND SourceDocumentType <> 'JournalEntry'", d.account(n), d.C)) for n in ("5050", "5060", "5080")]
    for n, _, _ in added:
        claim({r[0] for r in d.q("SELECT DISTINCT VoucherNumber FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                                 "AND SourceDocumentType = 'JournalEntry'", d.account(n), d.C)} <= set(d.closes),
              f"the only journal entries on {n} in {d.C} are closes, so excluding JournalEntry removes only them")
    fixed2 = fixed + sum(a for _, _, a in added)
    breakeven2 = fixed2 / ratio
    target = 4_000_000
    return dict(revenue=revenue, cost=cost, close=close, commissions=commissions, cm=cm, ratio=ratio, opex=opex,
                budget_commission=budget_commission, fixed=fixed, breakeven=breakeven, safety=revenue - breakeven,
                safety_pct=(revenue - breakeven) / revenue, added=added, added_total=fixed2 - fixed,
                breakeven2=breakeven2, safety2_pct=(revenue - breakeven2) / revenue,
                goal=(target + fixed2) / ratio, goal_without=(target + fixed) / ratio)


@note("ch07.ex4", EXERCISES)
def ex4(d, claim):
    import numpy as np
    from scipy.optimize import linprog

    rate = commission_rate(d)[0]
    items = d.q("SELECT i.ItemID, i.ItemCode, i.ItemGroup, i.StandardCost - i.StandardFixedOverheadCost, i.RoutingID, "
                "SUM(l.Quantity), SUM(l.LineTotal) FROM Item i JOIN SalesInvoiceLine l USING (ItemID) "
                "JOIN SalesInvoice si USING (SalesInvoiceID) WHERE i.SupplyMode = 'Manufactured' "
                "AND substr(si.InvoiceDate, 1, 4) = ? GROUP BY 1 ORDER BY 1", str(d.C))
    unsold = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured' AND ItemID NOT IN (SELECT l.ItemID "
                   "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) WHERE substr(si.InvoiceDate, 1, 4) = ?)",
                   str(d.C))
    claim(all(r[4] is not None for r in items), "every manufactured item sold has a routing")
    centers = d.q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter ORDER BY WorkCenterID")
    short = {w: name.replace(" Work Center", "") for w, name in centers}
    available = dict(d.q("SELECT WorkCenterID, SUM(AvailableHours) FROM WorkCenterCalendar "
                         "WHERE substr(CalendarDate, 1, 4) = ? GROUP BY 1", str(d.C)))
    hours = {(r, w): h for r, w, h in d.q("SELECT RoutingID, WorkCenterID, SUM(StandardRunHoursPerUnit) "
                                          "FROM RoutingOperation GROUP BY 1, 2")}
    demand = np.array([r[5] for r in items])
    price = np.array([r[6] / r[5] for r in items])
    unit = price - np.array([r[3] for r in items]) - rate * price
    A = np.array([[hours.get((r[4], w), 0.0) for r in items] for w, _ in centers])
    cap = np.array([available[w] / 2 for w, _ in centers])
    need = A @ demand / cap
    res = linprog(-unit, A_ub=A, b_ub=cap, bounds=[(0, q) for q in demand], method="highs")
    claim(res.status == 0, "Solver finds an optimal solution")
    x = res.x
    used = A @ x
    shadow = -res.ineqlin.marginals
    binding = [short[w] for (w, _), u, c in zip(centers, used, cap) if c - u < 1e-6]
    claim(binding == ["Assembly"], "only Assembly binds")
    assembly = next(i for i, (w, _) in enumerate(centers) if short[w] == "Assembly")
    finishing = next(i for i, (w, _) in enumerate(centers) if short[w].startswith("Finishing"))
    reduced = [i for i in range(len(items)) if x[i] < demand[i] - 1e-6]
    per_hour = {i: unit[i] / A[assembly][i] for i in range(len(items)) if A[assembly][i] > 0}
    kept = [i for i in per_hour if i not in reduced]
    claim(all(i in per_hour for i in reduced) and max(per_hour[i] for i in reduced) <= min(per_hour[i] for i in kept),
          "the items reduced are those with the lowest contribution per Assembly hour")
    groups = [(g, sum(1 for r in items if r[2] == g)) for g in GROUPS]
    claim({r[2] for r in items} <= set(GROUPS), "the manufactured items sold belong to the listed groups")
    # Setup hours need a lot size, which the exercise does not give; the item's average work-order quantity in the year
    # is one choice (the note names it), and the claims check that it leaves the same work center binding.
    setup = {(r, w): h for r, w, h in d.q("SELECT RoutingID, WorkCenterID, SUM(StandardSetupHours) "
                                          "FROM RoutingOperation GROUP BY 1, 2")}
    lots = dict(d.q("SELECT ItemID, AVG(PlannedQuantity) FROM WorkOrder WHERE substr(ReleasedDate, 1, 4) = ? GROUP BY 1",
                    str(d.C)))
    claim(all(lots.get(r[0]) for r in items), f"every manufactured item sold has work orders released in {d.C} (a lot size)")
    S = np.array([[setup.get((r[4], w), 0.0) / lots[r[0]] if lots.get(r[0]) else 0.0 for r in items] for w, _ in centers])
    with_setup = linprog(-unit, A_ub=A + S, b_ub=cap, bounds=[(0, q) for q in demand], method="highs")
    claim(with_setup.status == 0, "Solver finds an optimal solution with setup hours")
    setup_binding = [short[w] for (w, _), u, c in zip(centers, (A + S) @ with_setup.x, cap) if c - u < 1e-6] \
        if with_setup.status == 0 else []
    claim(setup_binding == binding, "with setup hours spread over the lots, the same work center binds")
    setup_loss = float(unit @ demand) + with_setup.fun if with_setup.status == 0 else 0.0
    return dict(sold=len(items), groups=[(g, n) for g, n in groups if n], unsold=unsold, rate=rate,
                need=[(short[w], n) for (w, _), n in zip(centers, need)], optimum=-res.fun,
                full=float(unit @ demand), loss=float(unit @ demand) + res.fun,
                bind_cap=cap[assembly], shadow=shadow[assembly], fin_used=used[finishing], fin_cap=cap[finishing],
                reduced=[(items[i][1], x[i], demand[i]) for i in reduced], setup_loss=round(setup_loss, -3))


@note("ch07.ex5", EXERCISES)
def ex5(d, claim):
    revenue = revenue_by_month(d)
    invoices = dict(d.q("SELECT substr(InvoiceDate, 1, 7), COUNT(*) FROM SalesInvoice GROUP BY 1"))
    commission = dict(d.q("SELECT substr(PostingDate, 1, 7), SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? "
                          "AND SourceDocumentType <> 'JournalEntry' GROUP BY 1", d.account("6290")))
    journal = {r[0] for r in d.q("SELECT DISTINCT VoucherNumber FROM GLEntry WHERE AccountID = ? "
                                 "AND SourceDocumentType = 'JournalEntry'", d.account("6290"))}
    claim(journal <= set(d.closes), "the only journal entries on 6290 are the year-end closes")
    months = sorted(revenue)
    claim(len(months) == 12 * len(d.years), "every month of the window has revenue")
    with_first = fit([invoices[m] for m in months], [revenue[m] for m in months])
    without = fit([invoices[m] for m in months[1:]], [revenue[m] for m in months[1:]])
    average = statistics.mean(revenue[m] for m in months[1:])
    claim(0.05 * average < 2 * without["se"], "a 5% misstatement lies within two standard errors, so it cannot be reliably detected")
    fitted = [m for m in months if m[:4] in (str(d.F), str(d.P))]
    line = fit([revenue[m] for m in fitted], [commission[m] for m in fitted])
    current = []
    for m in months:
        if m[:4] == str(d.C):
            expected = line["a"] + line["b"] * revenue[m]
            diff = commission[m] - expected
            current.append(dict(month=MONTHS[int(m[5:]) - 1], diff=diff, pct=diff / expected))
    flagged = [r for r in current if abs(r["pct"]) > 0.03]
    others = [r for r in current if abs(r["pct"]) <= 0.03]
    within = "2.5%" if all(abs(r["pct"]) < 0.025 for r in others) else "3%"
    # consecutive flagged months whose differences nearly offset: the pattern Requirement (4) asks students to look for
    offset = [(a, b) for a, b in zip(current, current[1:]) if a in flagged and b in flagged and a["diff"] * b["diff"] < 0
              and abs(a["diff"] + b["diff"]) < 0.1 * max(abs(a["diff"]), abs(b["diff"]))]
    claim(len(offset) > 0, "two consecutive months' differences are flagged and nearly offset")
    pair = offset[0] if offset else (current[0], current[1])
    # Why they offset. Not timing: each accrual is dated on its invoice's date, except a few (the misdated invoices),
    # whose commission is too small to move either month. The customer mix: the rate depends on the segment and the
    # revenue type, so a month weighted toward the lowest-rate segment accrues less per dollar than the regression's one slope.
    accrual_rows, misdated, other_month = d.q(
        "SELECT COUNT(*), SUM(a.AccrualDate <> si.InvoiceDate), SUM(substr(a.AccrualDate, 1, 7) <> substr(si.InvoiceDate, 1, 7)) "
        "FROM SalesCommissionAccrual a JOIN SalesInvoice si ON si.SalesInvoiceID = a.SalesInvoiceID")[0]
    misdated_invoices = {r[0] for r in d.q("SELECT DISTINCT a.SalesInvoiceID FROM SalesCommissionAccrual a "
                                           "JOIN SalesInvoice si ON si.SalesInvoiceID = a.SalesInvoiceID "
                                           "WHERE a.AccrualDate <> si.InvoiceDate")}
    before_shipment = {r[0] for r in d.q("SELECT si.SalesInvoiceID FROM SalesInvoice si WHERE si.InvoiceDate < "
                                         "(SELECT MIN(s.ShipmentDate) FROM Shipment s WHERE s.SalesOrderID = si.SalesOrderID)")}
    claim(misdated_invoices == before_shipment,
          "the accruals not dated on their invoice's date are those of the invoices dated before their first shipment (Tutorial 2.1)")
    keys = [f"{d.C}-{MONTHS.index(r['month']) + 1:02d}" for r in pair]
    moved = d.one("SELECT COALESCE(SUM(a.CommissionAmount), 0) FROM SalesCommissionAccrual a "
                  "JOIN SalesInvoice si ON si.SalesInvoiceID = a.SalesInvoiceID "
                  "WHERE substr(a.AccrualDate, 1, 7) <> substr(si.InvoiceDate, 1, 7) "
                  "AND (substr(a.AccrualDate, 1, 7) IN (?, ?) OR substr(si.InvoiceDate, 1, 7) IN (?, ?))", *keys, *keys)
    claim(moved < 0.1 * min(abs(r["diff"]) for r in pair),
          "the accruals dated in another month than their invoice move too little commission to explain the pair (not timing)")
    low, high = d.q("SELECT MIN(CommissionRatePct), MAX(CommissionRatePct) FROM SalesCommissionAccrual")[0]
    claim({r[0] for r in d.q("SELECT DISTINCT CustomerSegment FROM SalesCommissionAccrual WHERE CommissionRatePct = ?", low)}
          == {"Wholesale"}, "the lowest commission rate is Wholesale's")
    claim({r[0] for r in d.q("SELECT DISTINCT RevenueType FROM SalesCommissionAccrual WHERE CommissionRatePct = ?", high)}
          == {"Design Service"}, "the highest commission rate is the design services'")
    mix = "SUM(CASE WHEN CustomerSegment = 'Wholesale' THEN CommissionBaseAmount ELSE 0 END) / SUM(CommissionBaseAmount)"
    rate = "SUM(CommissionAmount) / SUM(CommissionBaseAmount)"
    by_month = {m: (s, r) for m, s, r in d.q(f"SELECT substr(AccrualDate, 1, 7), {mix}, {rate} FROM SalesCommissionAccrual "
                                              "WHERE substr(AccrualDate, 1, 4) = ? GROUP BY 1", str(d.C))}
    share_year, rate_year = d.q(f"SELECT {mix}, {rate} FROM SalesCommissionAccrual WHERE substr(AccrualDate, 1, 4) = ?",
                                str(d.C))[0]
    sign = lambda x: (x > 0) - (x < 0)
    claim(all(sign(by_month[k][1] - rate_year) == sign(r["diff"]) and sign(by_month[k][0] - share_year) == -sign(r["diff"])
              for k, r in zip(keys, pair)),
          "the month below its expectation has more Wholesale and a lower accrual rate than the year, the month above less "
          "and a higher rate (the customer mix explains the pair)")
    accruals = d.one("SELECT SUM(CommissionAmount) FROM SalesCommissionAccrual WHERE substr(AccrualDate, 1, 4) = ?", str(d.C))
    adj_rows, adj_amount, no_memo = d.q(
        "SELECT COUNT(*), -SUM(g.Debit - g.Credit), SUM(a.CreditMemoID IS NULL) FROM GLEntry g "
        "JOIN SalesCommissionAdjustment a ON a.SalesCommissionAdjustmentID = g.SourceDocumentID "
        "WHERE g.AccountID = ? AND g.FiscalYear = ? AND g.SourceDocumentType = 'SalesCommissionAdjustment'",
        d.account("6290"), d.C)[0]
    claim(no_memo == 0, "every SalesCommissionAdjustment row comes from a credit memo")
    gl = d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
               d.account("6290"), d.C)
    claim(abs(accruals - adj_amount - gl) < 0.005, "the accruals less the adjustments equal the ledger")
    return dict(r2_with=with_first["r2"], r2_without=without["r2"], slope=without["b"], se=round(without["se"], -3),
                se_share=without["se"] / average, average=average, a=line["a"], b=line["b"], r2=line["r2"], flagged=flagged,
                within=within, pair=[pair[0]["month"], pair[1]["month"]],
                accrual_rows=accrual_rows, misdated=misdated, other_month=other_month, low=low, high=high,
                share=[by_month[k][0] for k in keys], share_year=share_year, rate=[by_month[k][1] for k in keys],
                accruals=accruals, adj_rows=adj_rows, adj_amount=adj_amount, gl=gl)


@note("ch07.ex6", EXERCISES)
def ex6(d, claim):
    forecast = {(g, int(y)): v for g, y, v in d.q(
        "SELECT i.ItemGroup, substr(f.ForecastWeekStartDate, 1, 4), SUM(f.ForecastQuantity) FROM DemandForecast f "
        "JOIN Item i USING (ItemID) WHERE f.IsCurrent = 1 GROUP BY 1, 2")}
    orders = {(g, int(y)): v for g, y, v in d.q(
        "SELECT i.ItemGroup, substr(o.OrderDate, 1, 4), SUM(l.Quantity) FROM SalesOrderLine l "
        "JOIN SalesOrder o USING (SalesOrderID) JOIN Item i USING (ItemID) GROUP BY 1, 2")}
    years = []
    for y in d.years:
        # The overall ratio and the forecast total cover the four product groups, like the orders, the
        # budget, and the group ratios (author's decision 2026-10-02; the Services forecasts are left out).
        total = sum(forecast[(g, y)] for g in PRODUCTS)
        ordered = sum(orders[(g, y)] for g in PRODUCTS)
        years.append(dict(year=y, ratio=total / ordered, groups=[(g, forecast[(g, y)] / orders[(g, y)]) for g in PRODUCTS],
                          forecast=total, orders=ordered))
    claim(all(r > 2 for y in years for _, r in y["groups"]), "the forecast is more than twice the orders in every group and year")
    claim(all(a["ratio"] < b["ratio"] for a, b in zip(years, years[1:])), "the bias grows each year")
    budget = d.one("SELECT SUM(Quantity) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory = 'Revenue'", d.C)
    claim(budget > years[-1]["forecast"], "the budget's quantity is higher still than the forecast")
    invoiced = d.one("SELECT SUM(l.Quantity) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
                     "JOIN Item i USING (ItemID) WHERE i.ItemGroup <> 'Services' AND substr(si.InvoiceDate, 1, 4) = ?", str(d.C))
    methods = sorted((r[0] for r in d.q("SELECT DISTINCT ForecastMethod FROM DemandForecast")), reverse=True)
    last = d.one("SELECT MAX(ForecastWeekStartDate) FROM DemandForecast")
    claim(int(last[:4]) == d.N, f"the forecast weeks run into {d.N}")
    rows, current = d.q("SELECT COUNT(*), SUM(IsCurrent = 1) FROM DemandForecast")[0]
    versions = [r[0] for r in d.q("SELECT DISTINCT ForecastVersion FROM DemandForecast")]
    claim(rows == current, "all rows are IsCurrent 1")
    claim(len(versions) == 1, "there is one forecast version")
    all_rows = d.q("SELECT DemandForecastID, ForecastWeekStartDate, ItemID, WarehouseID, ForecastMethod, ForecastQuantity, "
                   "BaselineForecastQuantity, PlannerEmployeeID, ApprovedByEmployeeID FROM DemandForecast ORDER BY 1")
    adjusted = [r for r in all_rows if abs(r[5] / r[6] - 1) > 0.5]
    ratios = [r[5] / r[6] for r in all_rows if abs(r[5] / r[6] - 1) <= 0.5]
    claim(round(min(ratios), 2) >= 0.90 and round(max(ratios), 2) <= 1.10, "every other forecast is within about 10 percent of its baseline")
    claim([int(r[1][:4]) for r in adjusted] == d.years, f"the adjusted forecasts are one in each of {d.F}, {d.P}, and {d.C}")
    claim(all(r[1] == d.one("SELECT MIN(ForecastWeekStartDate) FROM DemandForecast WHERE substr(ForecastWeekStartDate, 1, 4) = ?",
                            r[1][:4]) for r in adjusted), "each is the first forecast week of its year")
    claim(len({(r[2], r[3], r[4], r[7]) for r in adjusted}) == 1, "all are for one item, warehouse, method, and planner")
    claim(len({round(r[5] / r[6], 1) for r in adjusted}) == 1, "all are the same multiple of their baseline")
    claim(all(r[8] is None for r in adjusted), "none has an ApprovedByEmployeeID")
    unapproved = [r[0] for r in all_rows if r[8] is None]
    claim(unapproved == [r[0] for r in adjusted], "they are the only unapproved forecasts, so every other adjustment was approved")
    first = adjusted[0]
    code, name, group = d.q("SELECT ItemCode, ItemName, ItemGroup FROM Item WHERE ItemID = ?", first[2])[0]
    warehouse = d.one("SELECT WarehouseName FROM Warehouse WHERE WarehouseID = ?", first[3])
    planner, title = d.q("SELECT EmployeeName, JobTitle FROM Employee WHERE EmployeeID = ?", first[7])[0]
    claim(sum(r[5] - r[6] for r in adjusted) < 0.001 * sum(r[5] for r in all_rows),
          "the quantities are small (the overrides add less than a tenth of a percent to the forecast)")
    planned = d.one("SELECT COUNT(*) FROM DemandForecast WHERE PlannerEmployeeID = ?", first[7])
    claim(planned > rows / 2, f"employee {first[7]} plans most forecasts")
    pos = d.one("SELECT COUNT(*) FROM PurchaseOrder WHERE CreatedByEmployeeID = ?", first[7])
    claim(title == "Buyer" and pos > 0, "the planner is a buyer who also places purchase orders")
    return dict(years=years, budget=budget, invoiced=invoiced, methods=methods, last_month=MONTHS[int(last[5:7]) - 1],
                rows=rows, version=versions[0], low=min(ratios), high=max(ratios),
                adjusted=[dict(id=r[0], date=r[1], forecast=r[5], baseline=r[6]) for r in adjusted],
                code=code, name=name, group=group, warehouse_id=first[3], warehouse=warehouse, method=first[4],
                multiple=first[5] / first[6], planner_id=first[7], planner=planner, title=title, pos=pos)
