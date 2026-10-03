"""Chapter 15's instructor notes: the values each note states, and the claims its wording makes.

The chapter's DAX values were verified with SQL twins (scripts/verify/twins/ch15_twins_budget.py and
ch15_twins_plant.py); the context functions below are those twins written through Data. The model's Date
table relates to InvoiceDate, PostingDate, BudgetDate, WorkDate, and CompletionDate, so a year or month of
the model is the calendar year or month of those dates (fiscal periods equal calendar months).

Exercise 15.5's note states no forecast value: Power BI's Analytics-pane forecast is computed in the visual
and cannot be read from the model, so the note leaves it to the students and only the benchmarks are data.
"""

from __future__ import annotations

import statistics
from functools import lru_cache

from notes import note
from notes.case2 import breakeven, unit_model, volume

TUTORIAL1 = "chapters/15-management-reports/_tutorial-01.qmd"
TUTORIAL2 = "chapters/15-management-reports/_tutorial-02.qmd"
TUTORIAL3 = "chapters/15-management-reports/_tutorial-03.qmd"
EXERCISES = "chapters/15-management-reports/_exercises.qmd"
MCQ = "chapters/15-management-reports/_multiple-choice.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
# Exercise 15.4's discounts and the Part II case's commission rate, both set by the exercise text.
DISCOUNTS = [0.05, 0.08, 0.10, 0.12, 0.15]
CASE_RATE = 0.01903
# Tutorial 15.3's job titles (Step 11 filters the chart to them).
TITLES = ["Assembler", "Machine Operator", "Quality Technician"]
PRODUCT_REVENUE = ("4010", "4020", "4030", "4040")      # the commission budget's base (Flexed Budget)


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def center(name: str | None) -> str | None:
    """A work center's name as the notes write it ("Packing", "Finishing and Test")."""
    return None if name is None else name.replace(" Work Center", "")


def short(name: str | None) -> str | None:
    """The shorter label of Exercise 15.6 ("QA" for Quality Assurance)."""
    n = center(name)
    return "QA" if n == "Quality Assurance" else n


# --- the plant measures (Tutorial 15.3) ----------------------------------------------------------

@lru_cache(maxsize=None)
def plant(d) -> dict:
    """Manufacturing hours, overtime hours, labor cost, and standard hours to the cut-off, by month (YYYY-MM)."""
    last = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    hours, overtime, cost = {}, {}, {}
    for m, h, o, c in d.q("SELECT substr(WorkDate, 1, 7), SUM(RegularHours + OvertimeHours), SUM(OvertimeHours), "
                          "SUM(ExtendedLaborCost) FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' GROUP BY 1"):
        hours[m], overtime[m], cost[m] = h, o, c
    standard = dict(d.q("SELECT substr(pc.CompletionDate, 1, 7), SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) "
                        "FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc "
                        "ON pc.ProductionCompletionID = pcl.ProductionCompletionID JOIN Item i ON i.ItemID = pcl.ItemID "
                        "WHERE pc.CompletionDate <= ? GROUP BY 1", last))
    months = [f"{y}-{m:02d}" for y in d.years for m in range(1, 13)]
    return dict(last=last, hours=hours, overtime=overtime, cost=cost, standard=standard, months=months)


def by_year(p: dict, key: str, year: int) -> float:
    return sum(v for m, v in p[key].items() if m.startswith(f"{year}-"))


def ratio(p: dict, window: list[str]) -> float:
    return sum(p["hours"].get(m, 0.0) for m in window) / sum(p["standard"].get(m, 0.0) for m in window)


def ttm(p: dict) -> list[tuple[str, float]]:
    """Hours per Standard Hour TTM: the twelve months ending with each month, from the first full window."""
    months = p["months"]
    return [(m, ratio(p, months[i - 11:i + 1])) for i, m in enumerate(months) if i >= 11 and m in p["hours"]]


def visual_ttm(p: dict, start: str) -> list[tuple[str, float]]:
    """The MOVINGAVERAGE visual calculation on an axis that starts at `start`: it sees only the axis's months."""
    months = p["months"]
    s = months.index(start)
    return [(months[i], ratio(p, months[max(s, i - 11):i + 1])) for i in range(s, min(s + 12, len(months)))]


# --- Tutorial 15.1 --------------------------------------------------------------------------------

@note("ch15.t1", TUTORIAL1)
def t1(d, claim):
    year = str(d.C)
    lines, no_promo = d.q("SELECT COUNT(*), SUM(PromotionID IS NULL) FROM SalesInvoiceLine")[0]
    list_amount, before, revenue, discounts = d.q(
        "SELECT SUM(l.Quantity * l.BaseListPrice), SUM(l.Quantity * l.UnitPrice), SUM(l.LineTotal), "
        "SUM(l.Quantity * l.UnitPrice * l.Discount) FROM SalesInvoiceLine l JOIN SalesInvoice si "
        "ON si.SalesInvoiceID = l.SalesInvoiceID WHERE substr(si.InvoiceDate, 1, 4) = ?", year)[0]
    promos = []
    for pid, name, start, end, amount, n, first, last, after in d.q(
            "SELECT p.PromotionID, p.PromotionName, p.EffectiveStartDate, p.EffectiveEndDate, "
            "SUM(l.Quantity * l.UnitPrice * l.Discount), COUNT(*), MIN(si.InvoiceDate), MAX(si.InvoiceDate), "
            "SUM(si.InvoiceDate > p.EffectiveEndDate) FROM SalesInvoiceLine l JOIN SalesInvoice si "
            "ON si.SalesInvoiceID = l.SalesInvoiceID JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
            "WHERE substr(si.InvoiceDate, 1, 4) = ? GROUP BY 1 ORDER BY 5 DESC", year):
        promos.append(dict(id=pid, label=name.removesuffix(" Promotion"), year=int(start[:4]), start=start, end=end,
                           discounts=amount, lines=n, first=first, last=last, after=after))
    claim(all(p["year"] in (d.P, d.C) for p in promos), "every promotion invoiced in the year started in that year or the year before")
    top = promos[0]
    top_months = d.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.Quantity * l.UnitPrice * l.Discount), COUNT(*) "
                     "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                     "WHERE l.PromotionID = ? GROUP BY 1 ORDER BY 1", top["id"])
    claim(all(m[:4] == year for m, _, _ in top_months), "the largest promotion's lines were all invoiced in the year")
    reversed_dates = [p for p in promos if p["year"] == d.C and p["end"] < p["start"]]
    claim(len(reversed_dates) == 1, "one promotion of the year has an end date before its start date")
    odd = (reversed_dates or promos)[0]
    return dict(promotions=d.one("SELECT COUNT(*) FROM PromotionProgram"), lines=lines, no_promo=no_promo,
                list=list_amount, step2=before - list_amount, step3=revenue - before, discounts=discounts,
                rounding=discounts - (before - revenue), revenue=revenue, by_promo=promos, top=top,
                top_months=top_months, odd=odd)


# --- Tutorial 15.2 --------------------------------------------------------------------------------

def budget_lines(d) -> list[tuple]:
    """The income-statement budget lines of the current year (Balance Sheet cleared): month, cost center, account
    number, subtype, category, driver, amount."""
    return d.q("SELECT b.Month, COALESCE(cc.CostCenterName, '(Blank)'), a.AccountNumber, a.AccountSubType, "
               "b.BudgetCategory, b.DriverType, b.BudgetAmount FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
               "LEFT JOIN CostCenter cc ON cc.CostCenterID = b.CostCenterID "
               "WHERE b.FiscalYear = ? AND b.BudgetCategory <> 'Balance Sheet'", d.C)


def actual_lines(d) -> list[tuple]:
    """GL Amount (debits less credits, closes excluded) of the current year: month, cost center, account number, subtype."""
    return d.q(f"SELECT CAST(substr(g.PostingDate, 6, 2) AS INT), COALESCE(cc.CostCenterName, '(Blank)'), a.AccountNumber, "
               f"a.AccountSubType, SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
               f"LEFT JOIN CostCenter cc ON cc.CostCenterID = g.CostCenterID WHERE substr(g.PostingDate, 1, 4) = ? "
               f"AND {d.no_closes()} GROUP BY 1, 2, 3", str(d.C))


@note("ch15.t2", TUTORIAL2)
def t2(d, claim):
    bud, act = budget_lines(d), actual_lines(d)
    product = dict(d.q("SELECT CAST(substr(si.InvoiceDate, 6, 2) AS INT), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                       "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
                       "WHERE substr(si.InvoiceDate, 1, 4) = ? AND i.ItemGroup <> 'Services' GROUP BY 1", str(d.C)))

    def budget(months=None, cc=None, accounts=None, subtype="Operating Expense"):
        return sum(r[6] for r in bud if (months is None or r[0] in months) and (cc is None or r[1] == cc)
                   and (accounts is None or str(r[2]) in accounts) and (subtype is None or r[3] == subtype))

    def actual(months=None, cc=None, accounts=None, subtype="Operating Expense"):
        return sum(r[4] for r in act if (months is None or r[0] in months) and (cc is None or r[1] == cc)
                   and (accounts is None or str(r[2]) in accounts) and (subtype is None or r[3] == subtype))

    def rate(months):
        return budget(months, None, ("6290",), None) / budget(months, None, PRODUCT_REVENUE, None)

    def flexed(months, cc=None):
        """Flexed Budget: the commission budget replaced by the budget's rate times actual product revenue."""
        commission = budget(months, cc, ("6290",))
        if not commission:
            return budget(months, cc)
        return budget(months, cc) - commission + rate(months) * sum(product.get(m, 0.0) for m in months)

    year = list(range(1, 13))
    revenue = [r for r in bud if r[4] == "Revenue"]
    cogs = [r for r in bud if r[4] == "COGS"]
    claim(len({r[1] for r in revenue}) == 1 and len({r[1] for r in cogs}) == 1,
          "the revenue budget lines are all in one cost center, and the COGS lines in one")
    other = sorted({(r[5], r[2], r[3]) for r in bud if r[4] == "Operating Expense" and r[3] != "Operating Expense"})
    claim(len(other) == 1, "one driver type of the Operating Expense category posts to an account outside the Operating Expense subtype")
    driver, other_account, other_subtype = other[0]
    centers = []
    for cc in sorted({r[1] for r in bud if r[3] == "Operating Expense"} | {r[1] for r in act if r[3] == "Operating Expense"}):
        b, a = budget(cc=cc), actual(cc=cc)
        f = flexed(year, cc)
        centers.append(dict(name=cc, budget=b, actual=a, pct=a / b - 1, flexed=f, volume=f - b,
                            cls=actual(cc=cc, accounts=("6130",)) - budget(cc=cc, accounts=("6130",))))
        centers[-1]["remaining"] = a - b - centers[-1]["volume"] - centers[-1]["cls"]
    sales = [c for c in centers if abs(c["volume"]) > 0.005]
    shifted = sorted((c for c in centers if abs(c["cls"]) > 0.005), key=lambda c: -c["cls"])
    claim(len(sales) == 1, "only one cost center has a commission budget, so only it has a volume effect")
    claim(len(shifted) == 2 and abs(shifted[0]["cls"] + shifted[1]["cls"]) < 0.005,
          "two cost centers have equal and opposite classification effects")
    sales, to, frm = sales[0], shifted[0], shifted[1]
    dep_budget = {r[1] for r in bud if str(r[2]) == "6130"}
    dep_actual = {r[1]: 0.0 for r in act if str(r[2]) == "6130"}
    for r in act:
        if str(r[2]) == "6130":
            dep_actual[r[1]] += r[4]
    claim(dep_budget == {frm["name"]}, "the depreciation budget is all in one cost center")
    claim(set(dep_actual) == {frm["name"], to["name"]}, "depreciation was recorded in that cost center and one other")
    claim(abs(budget(accounts=("6130",)) - actual(accounts=("6130",))) < 0.005,
          "depreciation recorded equals depreciation budgeted, so the classification effects total zero")
    monthly_rates = {round(100 * rate([m]), 4) for m in year}
    claim(len(monthly_rates) == 1, "the commission rate is the same in every month")
    blank = next(c for c in centers if c["name"] == "(Blank)")
    flexed_total = flexed(year)
    opex, actual_total = budget(), actual()
    by_month = [actual([m]) - flexed([m]) for m in year]
    ytd = [sum(by_month[:i + 1]) for i in range(12)]
    claim([i + 1 for i, v in enumerate(by_month) if v > 0] == [1, 7],
          "January and July are the only months above the flexed budget")
    commission_budget = budget(None, None, ("6290",))
    product_total = sum(product.values())
    return dict(rev=sum(r[6] for r in revenue), rev_lines=len(revenue), rev_cc=revenue[0][1],
                cogs=sum(r[6] for r in cogs), cogs_cc=cogs[0][1],
                opex_cat=sum(r[6] for r in bud if r[4] == "Operating Expense"),
                other=dict(driver=driver, account=other_account, subtype=other_subtype,
                           amount=sum(r[6] for r in bud if r[5] == driver and r[3] == other_subtype)),
                opex=opex, actual=actual_total, centers=centers,
                commission=commission_budget, rev_budget=budget(None, None, PRODUCT_REVENUE, None), rate=rate(year),
                product=product_total, flexed_com=rate(year) * product_total,
                sales=dict(name=sales["name"], flexed=sales["flexed"], other=sales["budget"] - commission_budget,
                           remaining=sales["remaining"], pct=sales["remaining"] / sales["flexed"]),
                volume=flexed_total - opex,
                dep=dict(budget=budget(accounts=("6130",)), frm=frm["name"], to=to["name"], frm_actual=dep_actual[frm["name"]],
                         to_actual=dep_actual[to["name"]], cls=to["cls"]),
                to=dict(name=to["name"], remaining=to["remaining"], pct=to["remaining"] / to["flexed"]),
                frm=dict(name=frm["name"], remaining=frm["remaining"], pct=frm["remaining"] / frm["flexed"]),
                blank=blank["remaining"], remaining=actual_total - flexed_total, flexed_total=flexed_total,
                months=list(zip([m[:3] for m in MONTHS], by_month)), ytd=ytd)


# --- Tutorial 15.3 --------------------------------------------------------------------------------

@note("ch15.t3", TUTORIAL3)
def t3(d, claim):
    p = plant(d)
    types = d.q("SELECT LaborType, COUNT(*) FROM LaborTimeEntry GROUP BY 1 ORDER BY 1")
    claim([t for t, _ in types] == ["Direct Manufacturing", "Indirect Manufacturing", "NonManufacturing"],
          "the labor types are direct, indirect, and non-manufacturing")
    matched = d.one("SELECT COUNT(*) FROM LaborTimeEntry l JOIN WorkOrderOperation o "
                    "ON o.WorkOrderOperationID = l.WorkOrderOperationID WHERE l.LaborType = 'Direct Manufacturing'")
    completions, items = d.q("SELECT COUNT(*), COUNT(DISTINCT ItemID) FROM ProductionCompletionLine")[0]
    tests = [dict(year=y, hours=by_year(p, "hours", y), standard=by_year(p, "standard", y)) for y in d.years]
    for t in tests:
        t["ratio"] = t["hours"] / t["standard"]
    series = ttm(p)
    claim(series[0][0] == f"{d.F}-12" and series[-1][0] == f"{d.C}-12",
          "the trailing measure runs from December of the first year to December of the current year")
    visual = visual_ttm(p, f"{d.P}-01")
    measure = dict(series)
    claim(all(round(v, 3) != round(measure[m], 3) for m, v in visual[:-1]) and round(visual[-1][1], 3) == round(measure[visual[-1][0]], 3),
          "the visual calculation differs from the measure until December of the prior year, and equals it there")
    centers = d.q("SELECT wc.WorkCenterName, SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l "
                  "LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID "
                  "LEFT JOIN WorkCenter wc ON wc.WorkCenterID = o.WorkCenterID "
                  "WHERE l.LaborType = 'Direct Manufacturing' AND substr(l.WorkDate, 1, 4) = ? GROUP BY 1", str(d.C))
    named = sorted(((center(n), h) for n, h in centers if n is not None), key=lambda c: -c[1])
    blank = sum(h for n, h in centers if n is None)
    unmatched = d.one("SELECT SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l LEFT JOIN WorkOrderOperation o "
                      "ON o.WorkOrderOperationID = l.WorkOrderOperationID WHERE l.LaborType = 'Direct Manufacturing' "
                      "AND o.WorkOrderOperationID IS NULL AND substr(l.WorkDate, 1, 4) = ?", str(d.C))
    claim(abs(blank - (unmatched or 0.0)) < 0.05, "the (Blank) work center holds the direct lines without an operation")
    shares = {(t, int(y)): o / h for t, y, o, h in d.q(
        "SELECT e.JobTitle, substr(l.WorkDate, 1, 4), SUM(l.OvertimeHours), SUM(l.RegularHours + l.OvertimeHours) "
        "FROM LaborTimeEntry l JOIN Employee e ON e.EmployeeID = l.EmployeeID WHERE l.LaborType <> 'NonManufacturing' "
        "GROUP BY 1, 2")}
    every_year = sorted(t for t in {t for t, _ in shares} if all((t, y) in shares for y in d.years))
    claim(every_year == TITLES, "the job titles with manufacturing time in every year are the three of Step 11")
    claim(d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE substr(WorkDate, 1, 4) = ?", str(d.N)) == 0,
          "there are no time records in the year after the data, the last year of the Date table")
    return dict(rows=sum(n for _, n in types), types=[(t.replace(" Manufacturing", ""), n) for t, n in types],
                last=p["last"], matched=matched, completions=completions, items=items, tests=tests, ttm=series,
                visual=[v for _, v in visual], centers=named, blank=blank,
                titles=[(t, shares[(t, d.F)], shares[(t, d.C)]) for t in TITLES],
                plant=[by_year(p, "overtime", y) / by_year(p, "hours", y) for y in d.years],
                card=series[-1][1], first=tests[0]["ratio"])


# --- Exercise 15.1 --------------------------------------------------------------------------------

def disposal(d, number: str) -> dict:
    """An asset-disposal entry: its loss line, cash proceeds, accumulated depreciation, cost, and asset event."""
    rows = d.q("SELECT a.AccountNumber, a.AccountName, a.AccountSubType, g.Debit, g.Credit, g.Description, g.PostingDate, "
               "g.SourceDocumentID FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.VoucherNumber = ? "
               "ORDER BY g.GLEntryID", number)
    loss = [r for r in rows if r[2] == "Other Income or Expense"]
    cash = [r for r in rows if r[2] == "Current Asset" and r[3] > 0]
    accumulated = [r for r in rows if r[2] == "Contra Fixed Asset" and r[3] > 0]
    cost = [r for r in rows if r[2] == "Fixed Asset" and r[4] > 0]
    event = d.q("SELECT FixedAssetEventID, FixedAssetID, Description, ProceedsAmount FROM FixedAssetEvent "
                "WHERE JournalEntryID = ? AND EventType = 'Disposal'", rows[0][7])
    ok = len(loss) == len(accumulated) == len(cost) == len(event) == 1 and len(rows) == 3 + len(cash) and len(cash) <= 1
    out = dict(number=number, date=rows[0][6], ok=ok)
    if ok:
        out.update(desc=loss[0][5], loss=loss[0][3] - loss[0][4],
                   cash=dict(account=cash[0][0], amount=cash[0][3]) if cash else None,
                   acc=dict(account=accumulated[0][0], name=accumulated[0][1], amount=accumulated[0][3]),
                   cost=dict(account=cost[0][0], name=cost[0][1], amount=cost[0][4]),
                   event=event[0][0], asset=event[0][1], event_desc=event[0][2], proceeds=event[0][3])
    return out


@note("ch15.ex1", EXERCISES)
def ex1(d, claim):
    accounts = d.q("SELECT a.AccountID, a.AccountNumber, a.AccountName, (SELECT COUNT(*) FROM GLEntry g "
                   "WHERE g.AccountID = a.AccountID) FROM Account a WHERE a.AccountSubType = 'Other Income or Expense' "
                   "ORDER BY a.AccountNumber")
    posted = [a for a in accounts if a[3] > 0]
    unposted = [a for a in accounts if a[3] == 0]
    claim(len(posted) == 1 and len(unposted) == 1, "the subtype holds two accounts, and only one has postings")
    account = posted[0]
    entries = d.q(f"SELECT FiscalYear, VoucherNumber FROM GLEntry WHERE AccountID = ? AND {d.no_closes()} "
                  f"GROUP BY 1, 2 ORDER BY 1", account[0])
    claim([y for y, _ in entries] == [d.P, d.C], "the subtype has one entry in each of the prior and current years, and none in other years")
    by_year = dict(entries)
    now, before = disposal(d, by_year[d.C]), disposal(d, by_year[d.P])
    claim(now["ok"] and before["ok"], "both entries are asset disposals with one loss, accumulated depreciation, and cost line")
    claim(now["cash"] is None and now["proceeds"] == 0, "the current year's disposal had no proceeds")
    claim(before["cash"] is not None and abs(before["cash"]["amount"] - before["proceeds"]) < 0.005,
          "the prior year's disposal debited cash with its proceeds")
    for e in (now, before):
        claim(abs(e["loss"] - (e["cost"]["amount"] - e["acc"]["amount"] - e["proceeds"])) < 0.005,
              f"{e['number']}'s loss equals cost less accumulated depreciation less proceeds")
    closes = []
    for year in (d.C, d.P):
        rows = d.q("SELECT VoucherNumber, SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                   "AND VoucherNumber IN (%s) GROUP BY 1" % ",".join("?" * len(d.closes)), account[0], year, *d.closes)
        claim(len(rows) == 1 and rows[0][1] > 0, f"one close credits the account in {year}")
        closes.append(rows[0][0])
    return dict(account=dict(number=account[1], name=account[2]), unposted=dict(number=unposted[0][1], name=unposted[0][2]),
                now=now, before=before, closes=closes)


# --- Exercise 15.2 --------------------------------------------------------------------------------

@note("ch15.ex2", EXERCISES)
def ex2(d, claim):
    income = dict(d.q(f"SELECT CAST(substr(g.PostingDate, 6, 2) AS INT), SUM(g.Credit - g.Debit) FROM GLEntry g "
                      f"JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountType IN ('Revenue', 'Expense') "
                      f"AND substr(g.PostingDate, 1, 4) = ? AND {d.no_closes()} GROUP BY 1", str(d.C)))
    months = [income[m] for m in range(1, 13)]
    total = sum(months)
    retained = d.q("SELECT g.VoucherNumber, g.Credit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                   "WHERE a.AccountName = 'Retained Earnings' AND g.VoucherNumber IN (%s)" % ",".join("?" * len(d.closes_of(d.C))),
                   *d.closes_of(d.C))
    claim(len(retained) == 1 and abs(retained[0][1] - total) < 0.005, "the year's net income equals the close's credit to retained earnings")
    lowest = sorted(range(1, 13), key=lambda m: income[m])
    claim(lowest[:2] == [7, 10], "July and October are the two months with the lowest net income, July the lowest")
    pay_dates = d.one("SELECT COUNT(DISTINCT PayDate) FROM PayrollPeriod WHERE substr(PayDate, 1, 7) = ?", f"{d.C}-07")
    claim(pay_dates == 3, "July has three pay dates")
    furniture = {(int(y), int(m)): v for y, m, v in d.q(
        "SELECT substr(PostingDate, 1, 4), substr(PostingDate, 6, 2), SUM(Credit) - SUM(Debit) FROM GLEntry "
        "WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry' GROUP BY 1, 2", d.account("4010"))}
    october = furniture[(d.C, 10)] / furniture[(d.P, 10)] - 1
    claim(october < 0, "October's Furniture revenue is below the prior year's October")
    peak = d.one("SELECT substr(si.InvoiceDate, 6, 2) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                 "ON si.SalesInvoiceID = l.SalesInvoiceID WHERE substr(si.InvoiceDate, 1, 4) = ? GROUP BY 1 "
                 "ORDER BY SUM(l.Quantity * l.UnitPrice * l.Discount) DESC LIMIT 1", str(d.C))
    claim(peak == "10", "October is the month of the year's largest promotional discounts")
    return dict(months=list(zip([m[:3] for m in MONTHS], months)), june=sum(months[:6]), ni=total, close=retained[0][0],
                h2=sum(months[6:]), july=sum(months[:7]), october=-october)


# --- Exercise 15.3 --------------------------------------------------------------------------------

@note("ch15.ex3", EXERCISES)
def ex3(d, claim):
    p = plant(d)
    years = []
    for y in d.years:
        hours, standard = by_year(p, "hours", y), by_year(p, "standard", y)
        cost, overtime = by_year(p, "cost", y), by_year(p, "overtime", y)
        years.append(dict(ratio=hours / standard, share=overtime / hours, per_std=cost / standard, cost=cost,
                          per_hour=cost / hours))
    rates = [r for _, r in d.q("SELECT substr(WorkDate, 1, 4), SUM(ExtendedLaborCost) / SUM(RegularHours + 1.5 * OvertimeHours) "
                               "FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' GROUP BY 1 ORDER BY 1")]
    first, last = years[0], years[-1]
    claim(last["per_std"] / first["per_std"] > last["ratio"] / first["ratio"],
          "the labor cost per standard hour rose faster than the hours per standard hour")
    claim(all(a["share"] < b["share"] for a, b in zip(years, years[1:])), "the overtime share grew every year")
    claim(all(a["per_hour"] < b["per_hour"] for a, b in zip(years, years[1:])), "the cost per hour rose every year")
    claim(all(a < b for a, b in zip(rates, rates[1:])), "the straight-time rates also rose")
    return dict(years=years)


# --- Exercise 15.4 --------------------------------------------------------------------------------

@note("ch15.ex4", EXERCISES)
def ex4(d, claim):
    promo = d.q("SELECT PromotionID, PromotionName, DiscountPct FROM PromotionProgram WHERE ScopeType = 'Segment' "
                "AND substr(EffectiveStartDate, 1, 4) = ?", str(d.C))
    claim(len(promo) == 1 and promo[0][1] == "Design Trade Customer Promotion",
          "the current year's segment promotion is the Design Trade Customer Promotion the exercise names")
    pid, _, rate = promo[0]
    claim(abs(rate - 0.12) < 1e-9, "the promotion's discount was 12 percent, the Part II case's")
    m = unit_model(d, pid, d.C)
    case_rate = d.one(f"SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                      d.account("6290"), d.C) / d.one(
        "SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
        "WHERE substr(si.InvoiceDate, 1, 4) = ?", str(d.C))
    claim(round(case_rate, 5) == CASE_RATE, "the Part II case's commission rate is 1.903 percent")
    lifts = [(x, breakeven(m["price"], m["cost"], x, CASE_RATE)) for x in DISCOUNTS]
    measured = [v["lift"] for v in volume(d)]
    claim(all(abs(v["z"]) < 2 for v in volume(d)), "no promotion's months show an unusual increase in volume")
    claim(abs(lifts[0][1] - max(measured)) < 0.01, "a 5% discount needs about the largest increase ever measured")
    return dict(id=pid, units=m["units"], price=m["price"], cost=m["cost"], lifts=lifts,
                low=min(measured), high=max(measured))


# --- Exercise 15.5 --------------------------------------------------------------------------------

@note("ch15.ex5", EXERCISES)
def ex5(d, claim):
    revenue = dict(d.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                       "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID GROUP BY 1"))
    months = [f"{y}-{m:02d}" for y in d.years for m in range(1, 13)]
    ys = [revenue[m] for m in months]
    fitted = ys[1:-3]                                   # Chapter 7: February of the first year to September
    xs = list(range(2, 2 + len(fitted)))                # MonthIndex, 1 for January of the first year
    mx, my = statistics.mean(xs), statistics.mean(fitted)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, fitted)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    actual = ys[-3:]
    methods = {"trend": [a + b * x for x in range(xs[-1] + 1, xs[-1] + 4)], "mean": [my] * 3, "last": ys[-15:-12]}
    errors = {k: dict(quarter=sum(f) / sum(actual) - 1,
                      monthly=statistics.mean(abs(fi - ai) / ai for fi, ai in zip(f, actual))) for k, f in methods.items()}
    others = statistics.mean(ys[1:12])
    claim(0.4 <= ys[0] / others <= 0.65, "January of the first year is about half the size of the other months")
    return dict(actual=sum(actual), fit_months=len(months) - 3, errors=errors, years=word(len(d.years)))


# --- Exercise 15.6 --------------------------------------------------------------------------------

@note("ch15.ex6", EXERCISES)
def ex6(d, claim):
    rows = d.q("SELECT substr(l.WorkDate, 1, 4), l.WorkDate, l.LaborType, l.RegularHours + l.OvertimeHours, ow.WorkCenterName, "
               "cw.WorkCenterName, o.ActualEndDate, o.WorkOrderOperationID IS NOT NULL, t.TimeClockEntryID IS NOT NULL "
               "FROM LaborTimeEntry l LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID "
               "LEFT JOIN WorkCenter ow ON ow.WorkCenterID = o.WorkCenterID "
               "LEFT JOIN TimeClockEntry t ON t.TimeClockEntryID = l.TimeClockEntryID "
               "LEFT JOIN WorkCenter cw ON cw.WorkCenterID = t.WorkCenterID")
    both = [r for r in rows if r[2] == "Direct Manufacturing" and r[7] and r[8]]
    years = []
    for y in d.years:
        lines = [r for r in both if r[0] == str(y)]
        differ = [r for r in lines if r[4] != r[5]]
        years.append(dict(year=y, differ=len(differ), lines=len(lines), hours=sum(r[3] for r in differ)))
    now = [r for r in both if r[0] == str(d.C)]
    cells = {}
    for r in now:
        cells[(r[4], r[5])] = cells.get((r[4], r[5]), 0.0) + r[3]
    names = sorted({r[4] for r in now}, key=lambda n: -sum(v for (o, _), v in cells.items() if o == n))
    claim(len(names) == 5, "five work centers have direct time in the year")
    claim(center(names[0]) == "Packing", "Packing has the most direct hours, the Packing finding")
    matrix = []
    for n in names:
        off = sorted(((short(c), v) for (o, c), v in cells.items() if o == n and c != n), key=lambda cv: -cv[1])
        matrix.append(dict(label=short(n).split()[0], diag=cells.get((n, n), 0.0), off=off))
    differ = [r for r in now if r[4] != r[5]]
    late_differ = sum(1 for r in differ if r[6] and r[1] > r[6])
    late_all = sum(1 for r in now if r[6] and r[1] > r[6])
    claim(late_differ / len(differ) > late_all / len(now),
          "lines recorded after their operation ended are a larger share of the disagreeing lines than of all direct lines")
    indirect = {}
    for r in rows:
        if r[2] == "Indirect Manufacturing" and r[0] == str(d.C):
            indirect[r[5]] = indirect.get(r[5], 0.0) + r[3]
    claim(None not in indirect, "the time clock places every indirect line at a work center")
    return dict(both=len(both), years=years, total=sum(y["differ"] for y in years), m=matrix,
                late_differ=late_differ, differ=len(differ), late_all=late_all, now=len(now),
                indirect=sorted(((short(n), v) for n, v in indirect.items()), key=lambda nv: -nv[1]))


# --- Multiple-choice answer key --------------------------------------------------------------------

@note("ch15.mcq", MCQ)
def mcq(d, claim):
    p = plant(d)
    start = f"{d.P}-01"
    visual = visual_ttm(p, start)[0][1]
    measure = dict(ttm(p))[start]
    claim(round(visual, 3) != round(measure, 3), "the visual calculation and the measure differ in January")
    budgeted = d.one("SELECT SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
                     "WHERE b.FiscalYear = ? AND a.AccountNumber IN (%s)" % ",".join("?" * len(PRODUCT_REVENUE)),
                     d.C, *PRODUCT_REVENUE)
    billed = d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "JOIN Item i ON i.ItemID = l.ItemID WHERE substr(si.InvoiceDate, 1, 4) = ? AND i.ItemGroup <> 'Services'",
                   str(d.C))
    claim(budgeted / billed >= 3, "the budget's product revenue is several times the actual (question 8)")
    return dict(visual=visual, measure=measure)
