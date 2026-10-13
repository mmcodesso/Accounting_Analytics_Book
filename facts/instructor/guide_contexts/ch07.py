"""Chapter 7's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 7 is the fourth Excel chapter (correlation and regression, forecasts and backtests, flexible budgets, break-even
analysis and the what-if tools, Solver), so, as in Chapters 4 to 6, the contexts do three jobs:

- they supply the values the tutorials' checkpoints show (the Forecast, BudgetReport, Model and OrderVolume worksheets), which
  no registered note covers,
- they supply what each exercise's steps need beyond its registered note (ch07.ex1 to ch07.ex6): the layout of the solution
  workbook where a step names a cell, the intermediate values of a model answer, the ranges of Solver's Sensitivity report,
- they check, with claim(), every table and column the guides name and every statement about the data that another dataset
  could falsify, so a roll flags the wording instead of leaving it stale.

Keys: ch07.chapter (the chapter note and its three tutorials) and ch07.g1 to ch07.g6 (the exercises; each is used next to the
registered note ch07.ex1 to ch07.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter07-exercises (Chapter 7 Exercises - Solutions.xlsx).
"""

from __future__ import annotations

import re
import statistics
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from notes.ch06 import lines
from notes.ch07 import GROUPS, MONTHS, PRODUCTS, commission_rate, fit

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "07-analysis-and-modeling"
DECK = REPO / "slides" / "chapter-07" / "index.qmd"
PROMOTION = "Furniture Seasonal Promotion"
# The model answer's choice of method for each item group (Exercise 7.1, requirement 4); the claims below check the reasons.
CHOSEN = {"Furniture": "Mean", "Lighting": "Trend", "Textiles": "Mean", "Accessories": "Mean", "Services": "Mean"}
METHODS = ["Trend", "Mean", "Same quarter last year", "Trend without the first quarter", "Mean without the first quarter"]


# --- helpers -------------------------------------------------------------------------------------------------------

def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise \d+\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/07-analysis-and-modeling/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 7\b")
    key = {int(n): a for n, a in re.findall(r"(\d+) ([A-D])[,.]", comment.split("\n", 2)[1])}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def and_list(items) -> str:
    items = [str(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    return items[0] + " and " + items[1] if len(items) == 2 else ", ".join(items[:-1]) + ", and " + items[-1]


def monthly(d):
    """Tutorial 7.1's series: by month of the window, the revenue, the customers invoiced and the average line (InvoiceLines)."""
    months = [f"{y}-{m:02d}" for y in d.years for m in range(1, 13)]
    by: dict = {m: [] for m in months}
    for y in d.years:
        for r in lines(d, y):
            by[r["date"][:7]].append(r)
    rev = [sum(r["R"] for r in by[m]) for m in months]
    cust = [len({r["customer"] for r in by[m]}) for m in months]
    avg = [statistics.mean(r["R"] for r in by[m]) for m in months]
    invoices = [len({r["invoice"] for r in by[m]}) for m in months]
    return months, rev, cust, avg, invoices


def mape(forecast, actual) -> float:
    return statistics.mean(abs(f - a) / a for f, a in zip(forecast, actual))


# --- the chapter note and its tutorials ----------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SalesOrderID", "CustomerID"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "BaseListPrice", "UnitPrice", "Discount",
                         "LineTotal", "PromotionID"],
    "SalesOrder": ["SalesOrderID", "OrderDate"],
    "Item": ["ItemID", "ItemCode", "ItemGroup", "StandardCost", "StandardFixedOverheadCost", "SupplyMode", "RoutingID"],
    "BudgetLine": ["FiscalYear", "Month", "AccountID", "CostCenterID", "ItemID", "Quantity", "UnitAmount", "BudgetAmount",
                   "BudgetCategory", "DriverType"],
    "Budget": ["FiscalYear", "CostCenterID", "AccountID", "Month", "BudgetAmount"],
    "PromotionProgram": ["PromotionID", "PromotionName", "ItemGroup", "DiscountPct"],
    "GLEntry": ["PostingDate", "VoucherNumber", "AccountID", "Debit", "Credit", "FiscalYear", "SourceDocumentType"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountSubType"],
}


def tutorial_71(d, claim) -> dict:
    from scipy import stats
    months, rev, cust, avg, invoices = monthly(d)
    n = len(months)
    claim(n == 36, "the window holds thirty-six months, so Tutorial 7.1's series fills rows 2 to 37")
    x = list(range(1, n + 1))
    first = invoices[0]
    others = statistics.mean(invoices[1:12])
    claim(0.4 < first / others < 0.6, "the first month of the data has about half as many invoices as a normal month of its year")
    corr = dict(all_customers=statistics.correlation(rev, cust), all_average=statistics.correlation(rev, avg),
                wo_customers=statistics.correlation(rev[1:], cust[1:]), wo_average=statistics.correlation(rev[1:], avg[1:]))
    claim(corr["all_customers"] > 0.7 and corr["all_customers"] > corr["all_average"],
          "with all months, revenue is strongly correlated with the customers invoiced and only weakly with the average line")
    claim(corr["wo_average"] > corr["wo_customers"], "without the first month, revenue correlates more closely with the average line than with the customers")
    r36, r35 = stats.linregress(x, rev), stats.linregress(x[1:], rev[1:])
    claim(r36.pvalue < 0.05 < r35.pvalue, "the trend's slope is significant with all months and not significant without the first")
    claim(r36.rvalue ** 2 < 0.25 and r35.rvalue ** 2 < r36.rvalue ** 2, "R Square is low, and lower without the first month")
    claim(0.4 < 1 - r35.slope / r36.slope < 0.5, "the first month accounts for almost half of the slope")
    # the backtest of Tutorial 7.1, Steps 6 and 7: fitted to the months from the second to the 33rd, held out the last three
    fx, fy = x[1:33], rev[1:33]
    line = fit(fx, fy)
    actual = rev[33:36]
    methods = dict(trend=[line["a"] + line["b"] * k for k in (34, 35, 36)], mean=[statistics.mean(fy)] * 3, same=rev[21:24])
    quarter = {k: (sum(v) / sum(actual) - 1, mape(v, actual)) for k, v in methods.items()}
    claim(quarter["trend"][0] > 0.03, "the trend forecast overshoots the quarter by several percent")
    claim(abs(quarter["mean"][0]) < 0.005 and quarter["mean"][1] == min(m for _, m in quarter.values()),
          "the mean misses the quarter by a small fraction of a percent and has the smallest monthly errors")
    claim(abs(quarter["same"][0]) < abs(quarter["trend"][0]) and quarter["same"][1] > quarter["mean"][1],
          "the same quarter of last year is close on the total but has larger monthly errors than the mean")
    forecast = 3 * statistics.mean(rev[1:])
    err = quarter["mean"][1]
    return dict(months=n, control=sum(rev) - sum(r["R"] for y in d.years for r in lines(d, y)), first_invoices=first,
                normal_invoices=others, corr=corr, r36=dict(r2=float(r36.rvalue ** 2), slope=float(r36.slope), p=float(r36.pvalue)),
                r35=dict(r2=float(r35.rvalue ** 2), slope=float(r35.slope), p=float(r35.pvalue)), slope_share=float(1 - r35.slope / r36.slope),
                q_actual=sum(actual), trend_q=sum(methods["trend"]), mean_q=sum(methods["mean"]), same_q=sum(methods["same"]),
                err_trend=quarter["trend"], err_mean=quarter["mean"], err_same=quarter["same"], forecast=forecast, err=err,
                low=forecast * (1 - err), high=forecast * (1 + err), rev=rev, jan=rev[0], month_low=min(rev),
                avg_month=statistics.mean(rev[1:]))


def flexible_budget(d, claim) -> dict:
    y = d.C
    plan = d.q("SELECT i.ItemGroup, b.BudgetCategory, SUM(b.BudgetAmount), SUM(b.Quantity) FROM BudgetLine b JOIN Item i USING (ItemID) "
               "WHERE b.FiscalYear = ? AND b.BudgetCategory IN ('Revenue', 'COGS') GROUP BY 1, 2", y)
    claim({r[0] for r in plan} == set(PRODUCTS), "the budget plans the four product groups and no Services revenue or cost")
    claim(d.one("SELECT COUNT(*) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory = 'Revenue'", y)
          == d.one("SELECT COUNT(DISTINCT ItemID || '-' || Month) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory = 'Revenue'", y),
          "the budget has exactly one planned net price for each item and month, so the merge on year, month and item adds no rows")
    static = {(g, c): (a, q) for g, c, a, q in plan}
    rows = d.q("SELECT i.ItemGroup, CAST(substr(si.InvoiceDate, 6, 2) AS INT), l.Quantity, l.LineTotal, bl.UnitAmount, l.Quantity * i.StandardCost, "
               "l.Quantity * l.UnitPrice * l.Discount, l.Quantity * l.BaseListPrice FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
               "JOIN Item i USING (ItemID) LEFT JOIN BudgetLine bl ON bl.BudgetCategory = 'Revenue' AND bl.FiscalYear = ? "
               "AND bl.Month = CAST(substr(si.InvoiceDate, 6, 2) AS INT) AND bl.ItemID = l.ItemID "
               "WHERE substr(si.InvoiceDate, 1, 4) = ? AND i.ItemGroup <> 'Services'", y, str(y))
    no_price = sum(1 for r in rows if r[4] is None)
    out = []
    for g in PRODUCTS:
        part = [r for r in rows if r[0] == g]
        flex = sum(r[2] * r[4] if r[4] is not None else r[3] for r in part)
        act = sum(r[3] for r in part)
        cogs = sum(r[5] for r in part)
        sr, sq = static[(g, "Revenue")]
        sc, _ = static[(g, "COGS")]
        disc = sum(r[6] for r in part)
        out.append(dict(group=g, static_revenue=sr, static_cogs=sc, static_margin=sr - sc, flex_revenue=flex, flex_cogs=cogs,
                        flex_margin=flex - cogs, revenue=act, margin=act - cogs, svv=(flex - cogs) - (sr - sc), fbv=(act - cogs) - (flex - cogs),
                        discounts=disc, gap=(act - cogs) - (flex - cogs) + disc, budget_units=sq, units=sum(r[2] for r in part),
                        gap_pct=((act - cogs) - (flex - cogs) + disc) / flex, unit_ratio=sq / sum(r[2] for r in part)))
    tot = {k: sum(g[k] for g in out) for k in out[0] if k != "group" and not k.endswith(("_pct", "_ratio"))}
    tot["gap_pct"] = tot["gap"] / tot["flex_revenue"]
    tot["unit_ratio"] = tot["budget_units"] / tot["units"]
    claim(0 < no_price <= 10, "a handful of invoice lines have no planned price (seasonal items in their launch month)")
    claim(all(g["svv"] < 0 and abs(g["svv"]) > 10 * abs(g["fbv"]) for g in out),
          "the sales-volume variance is unfavorable and at least ten times the flexible-budget variance in every product line")
    claim(all(g["fbv"] < 0 for g in out), "the flexible-budget variance is unfavorable in every product line")
    claim(all(g["unit_ratio"] > 2.5 for g in out), "the budgeted units are more than two and a half times the actual units in every product line")
    claim(all(-0.05 < g["gap_pct"] < -0.02 or -0.05 < -g["gap_pct"] < 0.05 for g in out) and max(g["gap_pct"] for g in out) < 0.05,
          "the price gap before discounts is a few percent of flexible revenue in every product line")
    claim(out[0]["discounts"] / tot["discounts"] > 0.9, "Furniture carries more than nine-tenths of the promotional discounts")
    return dict(groups=out, total=tot, no_price=no_price)


def furniture_prices(d, claim) -> dict:
    y = d.C
    rows = d.q("SELECT CAST(substr(si.InvoiceDate, 6, 2) AS INT), l.Quantity, l.LineTotal, bl.UnitAmount, l.Quantity * l.UnitPrice * l.Discount, "
               "l.Quantity * l.BaseListPrice FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) JOIN Item i USING (ItemID) "
               "LEFT JOIN BudgetLine bl ON bl.BudgetCategory = 'Revenue' AND bl.FiscalYear = ? AND bl.Month = CAST(substr(si.InvoiceDate, 6, 2) AS INT) "
               "AND bl.ItemID = l.ItemID WHERE substr(si.InvoiceDate, 1, 4) = ? AND i.ItemGroup = 'Furniture'", y, str(y))
    out = []
    for m in range(1, 13):
        part = [r for r in rows if r[0] == m]
        flex = sum(r[1] * r[3] if r[3] is not None else r[2] for r in part)
        lst = sum(r[5] for r in part)
        after = sum(r[2] for r in part) / lst
        before = (sum(r[2] for r in part) + sum(r[4] for r in part)) / lst
        out.append(dict(month=MONTHS[m - 1], planned=flex / lst, before=before, after=after))
    plan_low = [r["month"] for r in out if r["planned"] < r["before"]]
    claim(plan_low == ["September", "October"], "the planned price is below the actual price before promotions only in September and October")
    claim(all(r["after"] < r["before"] for r in out[8:]), "the actual price after promotions is below the price before promotions in every month from September to December")
    claim(max(abs(r["after"] - r["before"]) for r in out[:8]) < 0.01, "before September the price after promotions is within a point of the price before them")
    return dict(months=out, sep=out[8], oct=out[9], nov=out[10], dec=out[11], planned_low=plan_low)


def operating_expenses(d, claim, product_revenue: float, static_revenue: float) -> dict:
    y = d.C
    budget = dict(d.q("SELECT a.AccountNumber, SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a USING (AccountID) "
                      "WHERE b.FiscalYear = ? AND b.BudgetCategory = 'Operating Expense' GROUP BY 1", y))
    names = dict(d.q("SELECT a.AccountNumber, a.AccountName FROM Account a"))
    actual = dict(d.q(f"SELECT a.AccountNumber, SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.FiscalYear = ? "
                      f"AND a.AccountNumber BETWEEN 6000 AND 7999 AND {d.no_closes()} GROUP BY 1", y))
    claim(set(budget) <= set(actual), "every budgeted operating-expense account has postings in the year")
    rows = [dict(number=n, name=names[n], budget=budget[n], actual=actual[n], variance=actual[n] - budget[n]) for n in sorted(budget)]
    salaries_b = sum(budget[n] for n in budget if names[n].startswith("Salaries"))
    salaries_a = sum(actual[n] for n in budget if names[n].startswith("Salaries"))
    commission_budget = budget[6290]
    rate_b = commission_budget / static_revenue
    flexed = rate_b * product_revenue
    biggest = sorted(rows, key=lambda r: -abs(r["variance"]))
    claim({biggest[0]["number"], biggest[1]["number"]} == {6060, 6290},
          "the two largest operating-expense variances are the payroll taxes and benefits (6060) and the sales commissions (6290)")
    claim(all(abs(r["variance"]) < 0.05 * r["budget"] for r in rows if r["number"] not in (6060, 6290)),
          "every other budgeted operating-expense account is within five percent of its budget")
    claim(rows[-1]["number"] == 7030 and names[7030].startswith("Interest"), "the list of budgeted accounts ends with 7030, interest expense")
    burden_b, burden_a = budget[6060] / salaries_b, actual[6060] / salaries_a
    claim(burden_b > burden_a, "the budgeted burden rate is higher than the actual rate")
    claim(0.85 < actual[6290] / flexed < 0.95, "the flexed commission budget is within about a tenth of what was paid")
    exact = [r for r in rows if abs(r["variance"]) < 0.005]
    claim(len(exact) >= 3, "several accounts match their budget exactly")
    return dict(accounts=rows, n_accounts=len(rows), burden_b=burden_b, burden_a=burden_a, rate_b=rate_b, flexed=flexed,
                commissions=actual[6290], commission_budget=commission_budget, n_exact=len(exact), v6060=actual[6060] - budget[6060],
                v6290=actual[6290] - budget[6290], interest=actual[7030])


def tutorial_73(d, claim, commission: tuple) -> dict:
    ids = d.q("SELECT PromotionID, DiscountPct, ItemGroup FROM PromotionProgram WHERE PromotionName = ?", PROMOTION)
    claim(len(ids) == 1 and ids[0][2] == "Furniture", "one promotion is the Furniture Seasonal Promotion, on the Furniture group")
    pid, discount, _ = ids[0]
    rows = [r for y in d.years for r in lines(d, y) if r["promo"] == pid]
    units = sum(r["U"] for r in rows)
    price = (sum(r["R"] for r in rows) + sum(r["D"] for r in rows)) / units
    cost = sum(r["C"] for r in rows) / units
    rate = commission[0]

    def contribution(disc: float, lift: float) -> float:
        return units * (1 + lift) * (price * (1 - disc) * (1 - rate) - cost)

    without = contribution(0, 0)
    scen = [("End the promotion", 0.0, 0.0), ("Repeat as in 2026", discount, 0.0), ("Repeat with 15% lift", discount, 0.15),
            ("Deeper discount", 0.15, 0.15)]
    scen = [dict(name=n, discount=dd, lift=ll, difference=contribution(dd, ll) - without, with_=contribution(dd, ll)) for n, dd, ll in scen]
    claim(scen[0]["difference"] == 0 and all(s["difference"] < 0 for s in scen[1:]), "the difference is zero when the promotion ends and negative in every scenario that keeps a discount")
    claim(scen[3]["difference"] < scen[1]["difference"], "a deeper discount with the same lift is worse than repeating the promotion as it ran")
    claim(contribution(discount, 0.15) < without, "even a 15 percent lift recovers only part of the cost of the discount")

    def be(disc: float) -> float:
        return disc * price * (1 - rate) / (price * (1 - disc) * (1 - rate) - cost)
    lift = be(discount)
    claim(abs(contribution(discount, lift) - without) < 1e-6, "the closed form of the break-even lift agrees with the model")
    claim(0.25 < lift < 0.35, "the break-even lift is almost a third")
    # the data table of Step 5: discounts across (5, 10 and 15 percent), lifts down (0 to 40 percent in steps of 5)
    table = {(dd, ll): contribution(dd / 100, ll / 100) - without for dd in (5, 10, 15) for ll in range(0, 45, 5)}
    positive = [ll for ll in range(0, 45, 5) if table[(10, ll)] > 0]
    claim(abs(discount - 0.10) < 1e-9 and positive[0] == 35 and table[(10, 30)] < 0, "at a 10 percent discount the difference turns positive between a 30 and a 35 percent lift")
    claim(table[(15, 40)] < 0 and table[(5, 15)] > 0, "at 15 percent even a 40 percent lift falls short, and at 5 percent a 15 percent lift is enough")
    be5, be15 = be(0.05), be(0.15)
    orders = {m: u for m, u in d.q("SELECT substr(o.OrderDate, 1, 7), SUM(l.Quantity) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
                                   "JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID JOIN Item i USING (ItemID) "
                                   "WHERE i.ItemGroup = 'Furniture' GROUP BY 1")}
    promo_months = (f"{d.C}-09", f"{d.C}-10")
    promo_avg = statistics.mean(orders[m] for m in promo_months)
    other_avg = statistics.mean(orders[f"{d.C}-{k:02d}"] for k in range(1, 9))
    prior_avg = statistics.mean(orders[f"{y}-{k:02d}"] for y in (d.F, d.P) for k in (9, 10))
    claim(abs(promo_avg / other_avg - 1) < 0.1 and abs(promo_avg / prior_avg - 1) < 0.15 * 2, "the Furniture units from orders placed in the promotion's months are in line with the other months and the same months of earlier years")
    claim(orders[f"{d.C}-12"] < 0.8 * other_avg, "December's orders look low because some were not yet invoiced when the data ends")
    return dict(promo=pid, discount=discount, units=units, price=price, cost=cost, rate=rate, without=without, with_=contribution(discount, 0),
                difference=contribution(discount, 0) - without, scenarios=scen, lift=lift, lift5=be5, lift15=be15,
                cell_30=table[(10, 30)], cell_35=table[(10, 35)], promo_avg=promo_avg, other_avg=other_avg,
                prior_avg=prior_avg, sep=orders[promo_months[0]], oct=orders[promo_months[1]], dec=orders[f"{d.C}-12"],
                promo_vs_other=promo_avg / other_avg - 1, price_over_cost=price / cost, lines=len(rows))


@context("ch07.chapter")
def chapter(d, claim):
    schema(d, claim, CHAPTER_SCHEMA)
    t1 = tutorial_71(d, claim)
    fb = flexible_budget(d, claim)
    prices = furniture_prices(d, claim)
    total = fb["total"]
    opex = operating_expenses(d, claim, total["revenue"], total["static_revenue"])
    t3 = tutorial_73(d, claim, commission_rate(d))
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    return dict(y=d.C, p=d.P, f=d.F, n=d.N, n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(),
                n_questions=n_q, longest_correct=and_list(longest), n_longest=len(longest), t1=t1, t2=dict(fb=fb, prices=prices, opex=opex),
                t3=t3)


# --- Exercise 7.1: forecasting revenue by product line ---------------------------------------------------------------------

@context("ch07.g1")
def g1(d, claim):
    schema(d, claim, {"SalesInvoiceLine": ["LineTotal", "ItemID", "SalesInvoiceID"], "SalesInvoice": ["InvoiceDate"], "Item": ["ItemGroup"]})
    rev: dict = {}
    for i, y in enumerate(d.years):
        rows = lines(d, y)
        for g in GROUPS:
            for k in range(1, 5):
                rev[(g, 4 * i + k)] = sum(r["R"] for r in rows if r["grp"] == g and r["q"] == k)
    claim(len(d.years) == 3, "the window holds three fiscal years, so the table has twelve quarters")
    per_group, totals = [], [sum(rev[(g, i)] for g in GROUPS) for i in range(1, 13)]
    for g in GROUPS:
        s = [rev[(g, i)] for i in range(1, 13)]
        actual = s[8:12]
        fx, fy = list(range(1, 9)), s[:8]
        fxw, fyw = list(range(2, 9)), s[1:8]
        line, linew = fit(fx, fy), fit(fxw, fyw)
        fc = {"Trend": [line["a"] + line["b"] * k for k in range(9, 13)], "Mean": [statistics.mean(fy)] * 4, "Same quarter last year": s[4:8],
              "Trend without the first quarter": [linew["a"] + linew["b"] * k for k in range(9, 13)],
              "Mean without the first quarter": [statistics.mean(fyw)] * 4}
        errors = {m: mape(v, actual) for m, v in fc.items()}
        final_line = fit(list(range(2, 13)), s[1:12])
        final = {"Trend": final_line["a"] + final_line["b"] * 13, "Mean": statistics.mean(s[1:12]), "Same quarter last year": s[8]}
        method = CHOSEN[g]
        err = errors[{"Trend": "Trend without the first quarter", "Mean": "Mean without the first quarter"}.get(method, method)]
        forecast = final[method]
        per_group.append(dict(group=g, errors=errors, best3=min(("Trend", "Mean", "Same quarter last year"), key=errors.get),
                              best5=min(errors, key=errors.get), method=method, forecast=forecast, err=err, low=forecast * (1 - err),
                              high=forecast * (1 + err), mean_all=statistics.mean(s), lowest=min(s), highest=max(s), q1=s[8],
                              mean_without=final["Mean"], span=(min(errors.values()), max(errors.values()))))
    e = {x["group"]: x for x in per_group}
    claim(e["Furniture"]["best5"] == "Mean without the first quarter", "for Furniture the mean fitted without the first quarter has the lowest error of the five")
    claim(e["Furniture"]["best3"] == "Same quarter last year", "for Furniture the same quarter last year has the lowest error of the first three")
    claim(e["Lighting"]["best3"] == "Trend", "for Lighting the trend has the lowest error of the first three")
    claim(min(("Trend without the first quarter", "Mean without the first quarter", "Same quarter last year"), key=e["Lighting"]["errors"].get)
          == "Trend without the first quarter", "for Lighting the trend fitted without the first quarter still has the lowest error")
    claim(e["Textiles"]["best3"] == "Mean" and e["Textiles"]["best5"] == "Mean without the first quarter", "for Textiles the mean is best, with or without the first quarter")
    acc = e["Accessories"]["errors"]
    claim(e["Accessories"]["best3"] == "Mean" and acc["Mean"] < acc["Same quarter last year"] and acc["Trend without the first quarter"] < acc["Mean"],
          "for Accessories the mean is narrowly ahead of the same quarter last year, and the trend fitted without the first quarter does better")
    claim(e["Services"]["best3"] == "Mean" and e["Services"]["span"][0] > 0.13, "for Services the mean is best of the first three and every method misses by more than a tenth")
    drop_q1 = [x["group"] for x in per_group if x["errors"]["Mean without the first quarter"] < x["errors"]["Mean"]]
    claim(all(r["uom"] == "Hour" for y in d.years for r in lines(d, y) if r["grp"] == "Services"),
          "the Services invoice lines are design hours")
    claim(totals[0] == min(totals), "the first quarter is the company's lowest quarter of the window")
    claim(sum(rev[("Lighting", i)] for i in range(9, 13)) > sum(rev[("Lighting", i)] for i in range(5, 9)), f"Lighting's revenue grew in {d.C}")
    total = sum(x["forecast"] for x in per_group)
    months_rev = monthly(d)[1]
    company = 3 * statistics.mean(months_rev[1:])
    means_wo = sum(x["mean_without"] for x in per_group)
    claim(total > company, "the item-group forecasts sum to more than the company-level forecast of Tutorial 7.1")
    claim(abs(e["Lighting"]["forecast"] - e["Lighting"]["mean_without"]) > abs(total - company) / 2,
          "most of the difference between the sums is Lighting's trend, which carries its 2026 growth forward")
    changes = [(x["group"], m, x["errors"][m], x["errors"][f"{m} without the first quarter"]) for x in per_group for m in ("Trend", "Mean")]
    lowered = [c for c in changes if c[3] < c[2]]
    best = max(lowered, key=lambda c: c[2] - c[3])
    claim(len(lowered) > 0 and len(lowered) < len(changes), "leaving out the first quarter lowers the error of some of the trend and mean forecasts and raises that of others")
    return dict(groups=per_group, total=total, company=company, diff=total - company, diff_pct=total / company - 1,
                n_lowered=len(lowered), n_changes=len(changes), best_drop=dict(group=best[0], method=best[1].lower(), before=best[2], after=best[3]),
                means_without=means_wo, means_diff=means_wo / company - 1, low_sum=sum(x["low"] for x in per_group),
                high_sum=sum(x["high"] for x in per_group), drop_q1=drop_q1, n_methods=len(METHODS), methods=METHODS,
                widest=max(per_group, key=lambda x: x["err"])["group"], control=sum(totals) - sum(r["R"] for y in d.years for r in lines(d, y)))


# --- Exercise 7.2: reconciling the budget to its detail --------------------------------------------------------------------

@context("ch07.g2")
def g2(d, claim):
    schema(d, claim, {"Budget": ["FiscalYear", "AccountID", "BudgetAmount", "CostCenterID"],
                      "BudgetLine": ["FiscalYear", "AccountID", "BudgetAmount", "BudgetCategory", "CostCenterID"],
                      "Account": ["AccountID", "AccountNumber", "AccountName"]})
    cats = "BudgetCategory IN ('Revenue', 'COGS', 'Operating Expense')"
    years = []
    for y in d.years:
        s = d.one("SELECT SUM(BudgetAmount) FROM Budget WHERE FiscalYear = ?", y)
        dt = d.one(f"SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND {cats}", y)
        years.append(dict(year=y, summary=s, detail=dt, gap=dt - s))
    n_summary = d.one("SELECT COUNT(*) FROM (SELECT DISTINCT FiscalYear, AccountID FROM Budget)")
    n_detail = d.one(f"SELECT COUNT(*) FROM (SELECT DISTINCT FiscalYear, AccountID FROM BudgetLine WHERE {cats})")
    union = d.one(f"SELECT COUNT(*) FROM (SELECT AccountID FROM Budget WHERE FiscalYear = ? UNION SELECT AccountID FROM BudgetLine WHERE FiscalYear = ? AND {cats})",
                  d.C, d.C)
    summary_years = [r[0] for r in d.q("SELECT DISTINCT FiscalYear FROM Budget ORDER BY 1")]
    claim(summary_years == d.years + [d.N], f"the Budget Table covers the window and fiscal {d.N}, so the group-by query has rows for {d.N} too")
    claim(all(y["gap"] > 0 for y in years), "the detail exceeds the summary in every year of the window")
    claim(max(y["gap"] for y in years) < 0.02 * max(y["detail"] for y in years), "the gap is about one percent of the budget in every year")
    claim(d.one(f"SELECT COUNT(*) FROM BudgetLine WHERE FiscalYear = ? AND {cats} AND CostCenterID IS NULL AND BudgetCategory <> 'Operating Expense'", d.C) == 0,
          "only operating-expense lines have a blank cost center")
    in_both = union - d.one("SELECT COUNT(*) FROM (SELECT AccountID FROM BudgetLine WHERE FiscalYear = ? AND " + cats +
                            " AND CostCenterID IS NULL AND AccountID NOT IN (SELECT AccountID FROM Budget WHERE FiscalYear = ?) GROUP BY 1)", d.C, d.C)
    summary_rows = d.one("SELECT COUNT(*) FROM Budget WHERE FiscalYear = ?", d.C)
    return dict(years=years, n_summary=n_summary, n_detail=n_detail, accounts_union=union, accounts_both=in_both, summary_rows=summary_rows,
                bl_rows=d.one("SELECT COUNT(*) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory <> 'Balance Sheet'", d.C),
                share=years[-1]["gap"] / years[-1]["detail"])


# --- Exercise 7.3: company break-even and margin of safety ------------------------------------------------------------------

@context("ch07.g3")
def g3(d, claim):
    schema(d, claim, {"GLEntry": ["AccountID", "FiscalYear", "SourceDocumentType", "Debit", "Credit"],
                      "Account": ["AccountID", "AccountNumber", "AccountName", "AccountSubType"]})
    ids = {n: d.account(n) for n in ("5050", "5060", "5080")}
    interest = d.one("SELECT AccountSubType FROM Account WHERE AccountNumber = 7030")
    variance = {y: d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}", ids["5080"], y) for y in d.years}
    claim(variance[d.F] < variance[d.P] < variance[d.C], "the manufacturing variance grows every year of the window")
    revenue, cost = d.q("SELECT SUM(l.LineTotal), SUM(l.Quantity * i.StandardCost) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
                        "JOIN Item i USING (ItemID) WHERE substr(si.InvoiceDate, 1, 4) = ?", str(d.C))[0]
    commissions = d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}", d.account("6290"), d.C)
    ratio = (revenue - cost - commissions) / revenue
    opex = d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory = 'Operating Expense'", d.C)
    fixed = opex - d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND AccountID = ?", d.C, d.account("6290")) \
        - d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND AccountID = ?", d.C, d.account("7030"))
    added = sum(d.one("SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType <> 'JournalEntry'", ids[n], d.C)
                for n in ids)
    fixed2 = fixed + added
    n_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE FiscalYear = ? AND AccountID IN (?, ?, ?) AND SourceDocumentType <> 'JournalEntry'", d.C, *ids.values())
    n_before = d.one("SELECT COUNT(*) FROM GLEntry WHERE FiscalYear = ? AND AccountID IN (?, ?, ?)", d.C, *ids.values())
    claim(n_before - n_rows == len(d.closes_of(d.C)) or n_before - n_rows > 0, "excluding the JournalEntry source removes the closing entry's rows from the three accounts")
    claim(interest == "Other Expense", "the chart of accounts files interest expense (7030) as Other Expense, below operating income")
    claim(0.4 < ratio < 0.5, "the contribution margin ratio is between 40 and 50 percent, inside the data table's grid")
    claim(6_000_000 <= fixed <= 10_000_000 and 6_000_000 <= fixed2 <= 10_000_000, "both sets of fixed costs lie inside the data table's range of 6 to 10 million")
    grid_lo, grid_hi = 6_000_000 / 0.50, 10_000_000 / 0.40
    return dict(ids=ids, variance=[(y, variance[y]) for y in d.years], reduction=round((variance[d.C] - variance[d.F]) / ratio, -3),
                per_point=round(fixed2 / ratio ** 2 / 100, -3), commission_effect=round(d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND AccountID = ?", d.C, d.account("6290")) / ratio, -3), n_rows=n_rows, corner_low=6_000_000 / 0.40, corner_high=10_000_000 / 0.50,
                grid_lo=grid_lo, grid_hi=grid_hi, cell=9_000_000 / 0.45, interest_subtype=interest, ratio=ratio, fixed2=fixed2,
                lowest_ratio_row=6_000_000 / 0.50, highest_ratio_row=10_000_000 / 0.40)


# --- Exercise 7.4: the product mix under a capacity constraint --------------------------------------------------------------

def lp(d):
    import numpy as np
    from scipy.optimize import linprog
    rate = commission_rate(d)[0]
    items = d.q("SELECT i.ItemID, i.ItemCode, i.ItemGroup, i.StandardCost - i.StandardFixedOverheadCost, i.RoutingID, SUM(l.Quantity), SUM(l.LineTotal) "
                "FROM Item i JOIN SalesInvoiceLine l USING (ItemID) JOIN SalesInvoice si USING (SalesInvoiceID) WHERE i.SupplyMode = 'Manufactured' "
                "AND substr(si.InvoiceDate, 1, 4) = ? GROUP BY 1 ORDER BY 1", str(d.C))
    centers = d.q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter ORDER BY WorkCenterID")
    available = dict(d.q("SELECT WorkCenterID, SUM(AvailableHours) FROM WorkCenterCalendar WHERE substr(CalendarDate, 1, 4) = ? GROUP BY 1", str(d.C)))
    hours = {(r, w): h for r, w, h in d.q("SELECT RoutingID, WorkCenterID, SUM(StandardRunHoursPerUnit) FROM RoutingOperation GROUP BY 1, 2")}
    demand = np.array([r[5] for r in items])
    price = np.array([r[6] / r[5] for r in items])
    unit = price - np.array([r[3] for r in items]) - rate * price
    A = np.array([[hours.get((r[4], w), 0.0) for r in items] for w, _ in centers])
    cap = np.array([available[w] / 2 for w, _ in centers])

    def solve(extra: float, k: int):
        c2 = cap.copy()
        c2[k] += extra
        return linprog(-unit, A_ub=A, b_ub=c2, bounds=[(0, q) for q in demand], method="highs")
    return rate, items, centers, available, demand, price, unit, A, cap, solve


@context("ch07.g4")
def g4(d, claim):
    import numpy as np
    schema(d, claim, {"Item": ["ItemID", "ItemCode", "ItemGroup", "StandardCost", "StandardFixedOverheadCost", "SupplyMode", "RoutingID"],
                      "RoutingOperation": ["RoutingID", "WorkCenterID", "StandardRunHoursPerUnit", "StandardSetupHours"],
                      "WorkCenter": ["WorkCenterID", "WorkCenterName"], "WorkCenterCalendar": ["WorkCenterID", "CalendarDate", "AvailableHours"]})
    rate, items, centers, available, demand, price, unit, A, cap, solve = lp(d)
    res = solve(0.0, 0)
    claim(res.status == 0, "Solver finds an optimal solution")
    x, used = res.x, A @ res.x
    short = [name.replace(" Work Center", "") for _, name in centers]
    bind = [i for i in range(len(centers)) if cap[i] - used[i] < 1e-6]
    claim(len(bind) == 1 and short[bind[0]] == "Assembly", "only Assembly binds")
    k = bind[0]
    shadow = float(-res.ineqlin.marginals[k])
    # the range over which the shadow price holds: the objective stays on its line while the capacity moves
    base = -res.fun

    def holds(delta: float) -> bool:
        r = solve(delta, k)
        return r.status == 0 and abs((-r.fun - base) - shadow * delta) < 1e-4

    def edge(sign: int) -> float:
        lo, hi = 0.0, 4000.0 if sign > 0 else float(cap[k]) - 1.0
        if holds(sign * hi):
            return hi
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if holds(sign * mid) else (lo, mid)
        return lo
    up, down = edge(+1), edge(-1)
    claim(up > 50 and down > 50, "the shadow price holds over a range of tens of hours on each side of the capacity")
    need = A @ demand
    claim({r[0] for r in d.q("SELECT DISTINCT WorkCenterID FROM RoutingOperation")} == {w for w, _ in centers},
          "the routings give run hours for every work center")
    nxt = min((i for i in range(len(centers)) if i != k), key=lambda i: cap[i] - used[i])
    claim(short[nxt].startswith("Finishing"), "Finishing and Test is the next center to bind (the least slack after Assembly)")
    centers_out = [dict(name=short[i], available=available[centers[i][0]], capacity=float(cap[i]), need=float(need[i]), need_ratio=float(need[i] / cap[i]),
                        used=float(used[i]), slack=float(cap[i] - used[i]), status="Binding" if cap[i] - used[i] < 1e-6 else "Not binding",
                        shadow=float(-res.ineqlin.marginals[i]) if i == k else 0.0) for i in range(len(centers))]
    over = [c["name"] for c in centers_out if c["need_ratio"] > 1]
    n = len(items)
    reduced = [i for i in range(n) if x[i] < demand[i] - 1e-6]
    partial = [i for i in reduced if x[i] > 1e-6]
    claim(len(partial) == 1, "Solver makes one item only in part, and that item's contribution per Assembly hour is the shadow price")
    p = partial[0]
    claim(abs(unit[p] / A[k][p] - shadow) < 1e-6, "the shadow price equals the contribution per Assembly hour of the item made in part")
    per_hour = {i: unit[i] / A[k][i] for i in range(n) if A[k][i] > 0}
    made_full = [i for i in per_hour if i not in reduced]
    claim(min(per_hour[i] for i in made_full) >= shadow - 1e-9, "every item made in full earns at least the shadow price per Assembly hour")
    claim(all(per_hour.get(i, 0) <= shadow + 1e-9 for i in reduced), "every item made less than its demand earns no more than the shadow price per Assembly hour")
    lowest = sorted(range(n), key=lambda i: unit[i])[:len(reduced)]
    swap = [items[i][1] for i in lowest if i not in reduced]
    claim(len(swap) > 0 and all(A[k][i] < max(A[k][j] for j in reduced) for i in lowest if i not in reduced),
          "some items with the lowest unit contribution are made in full, because they use less Assembly time than the items Solver cuts")
    first = 21
    last = first + n - 1
    return dict(swap=swap, rate=rate, centers=centers_out, n_centers=len(centers), over=over, binding=short[k], allowed_up=float(up), allowed_down=float(down),
                range_low=float(cap[k] - down), range_high=float(cap[k] + up), n_items=n, first_row=first, last_row=last, n_constraints=len(centers) + n,
                part_code=items[p][1], part_qty=float(x[p]), part_demand=float(demand[p]), per_hour_part=float(unit[p] / A[k][p]),
                n_reduced=len(reduced), n_whole=n - len(reduced), next_center=short[nxt], routing_ops=d.one("SELECT COUNT(*) FROM RoutingOperation"),
                calendar_rows=d.one("SELECT COUNT(*) FROM WorkCenterCalendar"), manufactured=d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured'"),
                lowest_per_hour=float(min(per_hour[i] for i in made_full)), highest_per_hour=float(max(per_hour[i] for i in made_full)),
                full_loss_share=float((float(unit @ demand) + res.fun) / float(unit @ demand)), centers_letters=[chr(ord("J") + i) for i in range(len(centers))],
                hours_cols=f"J{first}:{chr(ord('J') + len(centers) - 1)}{last}", var_range=f"I{first}:I{last}", demand_range=f"E{first}:E{last}",
                cap_range=f"D11:D{10 + len(centers)}", used_range=f"G11:G{10 + len(centers)}")


# --- Exercise 7.5: regression-based expectations -----------------------------------------------------------------------------

@context("ch07.g5")
def g5(d, claim):
    schema(d, claim, {"SalesCommissionAccrual": ["AccrualDate", "SalesInvoiceID", "CustomerSegment", "CommissionBaseAmount", "CommissionRatePct",
                                                  "CommissionAmount"],
                      "SalesCommissionAdjustment": ["SalesCommissionAdjustmentID", "CreditMemoID"],
                      "GLEntry": ["AccountID", "PostingDate", "Debit", "Credit", "SourceDocumentType", "FiscalYear"]})
    months, rev, cust, avg, invoices = monthly(d)
    acc = d.account("6290")
    gl_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry'", acc)
    closes = d.one("SELECT COUNT(DISTINCT VoucherNumber) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'JournalEntry'", acc)
    inv_all = d.one("SELECT COUNT(*) FROM SalesInvoice")
    inv_month = dict(d.q("SELECT substr(InvoiceDate, 1, 7), COUNT(*) FROM SalesInvoice GROUP BY 1"))
    claim([inv_month[m] for m in months] == invoices, "the invoices counted from the SalesInvoice Table equal those of the invoice lines in every month")
    w = fit([inv_month[m] for m in months], rev)
    claim(w["r2"] > 0.7, "revenue on the number of invoices has a high R Square with the first month")
    claim(closes == len(d.years), "the only journal entries on 6290 are one year-end close for each fiscal year of the window")
    claim({r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry'", acc)}
          == {"SalesCommissionAccrual", "SalesCommissionAdjustment"},
          "the commission postings besides the closes come from SalesCommissionAccrual and SalesCommissionAdjustment documents")
    rates = d.q("SELECT CustomerSegment, MIN(CommissionRatePct), MAX(CommissionRatePct) FROM SalesCommissionAccrual GROUP BY 1 ORDER BY 2, 1")
    claim(all(lo == hi for _, lo, hi in rates), "each customer segment has one commission rate")
    claim(len(rates) == 5, "the accruals name five customer segments")
    se_all = fit(list(map(float, [inv_month[m] for m in months])), rev)["se"]
    avg_month = statistics.mean(rev[1:])
    claim(0.05 * avg_month < se_all and 0.05 * avg_month < fit([inv_month[m] for m in months[1:]], rev[1:])["se"],
          "five percent of an average month is below the standard error of either regression")
    rate_rows = [dict(segment=s, rate=lo) for s, lo, _ in rates]
    return dict(account_id=acc, n_months=len(months), gl_rows=gl_rows, closes=closes, invoices_all=inv_all, se_all=se_all, five=0.05 * avg_month,
                observations=24, rates=rate_rows, n_segments=len(rates), accrual_rows_all=d.one("SELECT COUNT(*) FROM SalesCommissionAccrual"),
                low_segment=rates[0][0], high_segment=rates[-1][0], revenue_rows=sum(inv_month.values()))


# --- Exercise 7.6: evaluating management's forecast --------------------------------------------------------------------------

@context("ch07.g6")
def g6(d, claim):
    schema(d, claim, {"DemandForecast": ["ForecastWeekStartDate", "ItemID", "BaselineForecastQuantity", "ForecastQuantity", "ForecastMethod",
                                         "PlannerEmployeeID", "ApprovedByEmployeeID", "IsCurrent"],
                      "SalesOrderLine": ["SalesOrderID", "ItemID", "Quantity"], "SalesOrder": ["SalesOrderID", "OrderDate"],
                      "Employee": ["EmployeeID", "EmployeeName", "JobTitle"], "BudgetLine": ["FiscalYear", "ItemID", "Quantity", "BudgetCategory"]})
    forecast = {(g, int(y)): v for g, y, v in d.q("SELECT i.ItemGroup, substr(f.ForecastWeekStartDate, 1, 4), SUM(f.ForecastQuantity) FROM DemandForecast f "
                                                  "JOIN Item i USING (ItemID) WHERE f.IsCurrent = 1 GROUP BY 1, 2")}
    orders = {(g, int(y)): v for g, y, v in d.q("SELECT i.ItemGroup, substr(o.OrderDate, 1, 4), SUM(l.Quantity) FROM SalesOrderLine l "
                                                "JOIN SalesOrder o USING (SalesOrderID) JOIN Item i USING (ItemID) GROUP BY 1, 2")}
    table = []
    for g in GROUPS:
        table.append(dict(group=g, forecast=[forecast[(g, y)] for y in d.years], orders=[orders[(g, y)] for y in d.years],
                          ratio=[forecast[(g, y)] / orders[(g, y)] for y in d.years]))
    budget = dict(d.q("SELECT i.ItemGroup, SUM(b.Quantity) FROM BudgetLine b JOIN Item i USING (ItemID) WHERE b.FiscalYear = ? AND b.BudgetCategory = 'Revenue' GROUP BY 1", d.C))
    claim(set(budget) == set(PRODUCTS), "the budget plans the four product groups only")
    c26 = []
    for g in PRODUCTS:
        o = orders[(g, d.C)]
        c26.append(dict(group=g, budget=budget[g], forecast=forecast[(g, d.C)], orders=o, b_o=budget[g] / o, f_o=forecast[(g, d.C)] / o, b_f=budget[g] / forecast[(g, d.C)]))
    claim(all(r["b_f"] > 1 for r in c26), "the budget's quantity exceeds the forecast in every product group")
    after_2026 = d.one("SELECT COUNT(*) FROM DemandForecast WHERE substr(ForecastWeekStartDate, 1, 4) = ?", str(d.N))
    claim(after_2026 > 0, f"the forecast also covers the first weeks of {d.N}, which have no orders to compare with")
    methods = d.q("SELECT ForecastMethod, COUNT(*), SUM(ApprovedByEmployeeID IS NULL), MIN(ForecastQuantity / BaselineForecastQuantity), "
                  "MAX(ForecastQuantity / BaselineForecastQuantity) FROM DemandForecast GROUP BY 1 ORDER BY 1")
    adjusted = [m for m in methods if m[0] == "Planner Adjusted"][0]
    claim(adjusted[2] == 3, "three Planner Adjusted forecasts have no approver, and no forecast of another method lacks one")
    claim(all(m[2] == 0 for m in methods if m[0] != "Planner Adjusted"), "every forecast of the other methods has an approver")
    claim(all(abs(m[3] - 1) < 0.5 and abs(m[4] - 1) < 0.5 for m in methods if m[0] != "Planner Adjusted"), "the forecasts of the other methods stay within half of their baseline")
    n_off = d.one("SELECT COUNT(*) FROM DemandForecast WHERE ForecastQuantity <> BaselineForecastQuantity")
    n_big = d.one("SELECT COUNT(*) FROM DemandForecast WHERE ABS(ForecastQuantity / BaselineForecastQuantity - 1) > 0.5")
    claim(n_big == 3 and n_off > 1000, "only three forecasts differ from their baseline by more than half, though many others are adjusted by a few percent")
    approvers = d.one("SELECT COUNT(DISTINCT ApprovedByEmployeeID) FROM DemandForecast")
    return dict(table=table, c26=c26, planner_adjusted=adjusted[1], unapproved=adjusted[2], n_off=n_off, n_big=n_big, approvers=approvers,
                n_forecast_weeks=after_2026, methods=[dict(method=m[0], rows=m[1], low=m[3], high=m[4]) for m in methods])
