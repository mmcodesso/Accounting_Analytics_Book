"""Chapter 11's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

from notes import note

EXERCISES = "chapters/11-analytical-queries/_exercises.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
REVENUE_LINES = [("4010", "Furniture"), ("4020", "Lighting"), ("4030", "Textiles"), ("4040", "Accessories"),
                 ("4080", "Services")]


@note("ch11.ex1", EXERCISES)
def ex1(d, claim):
    asof = f"{d.C}-12-31"
    close1, close2 = d.closes_of(d.C)
    rows = dict(((t, s), b) for t, s, b in d.q(
        "SELECT a.AccountType, a.AccountSubType, ROUND(SUM(g.Debit) - SUM(g.Credit), 2) FROM GLEntry g "
        "JOIN Account a ON a.AccountID = g.AccountID WHERE g.PostingDate <= ? AND g.VoucherNumber NOT IN (?, ?) "
        "GROUP BY 1, 2", asof, close1, close2))
    cr = lambda t, s: -rows.get((t, s), 0.0)              # credits less debits
    v = dict(asof=asof, close1=close1, close2=close2,
             opr=cr("Revenue", "Operating Revenue"), contra=cr("Revenue", "Contra Revenue"),
             cogs=cr("Expense", "COGS"), opex=cr("Expense", "Operating Expense"),
             oexp=cr("Expense", "Other Expense"), oie=cr("Revenue", "Other Income or Expense"))
    v["net_rev"] = v["opr"] + v["contra"]
    v["gm"] = v["net_rev"] + v["cogs"]
    v["oi"] = v["gm"] + v["opex"]
    v["ni"] = v["oi"] + v["oexp"] + v["oie"]
    v["gm_pct"], v["oi_pct"] = v["gm"] / v["net_rev"], v["oi"] / v["net_rev"]
    v.update(current=rows[("Asset", "Current Asset")], fixed=rows[("Asset", "Fixed Asset")],
             contra_fixed=-rows[("Asset", "Contra Fixed Asset")], cl=-rows[("Liability", "Current Liability")],
             ltl=-rows[("Liability", "Long-Term Liability")], equity=-rows[("Equity", "Equity")])
    v["assets"] = v["current"] + v["fixed"] - v["contra_fixed"]
    v["le_total"] = v["cl"] + v["ltl"] + v["equity"] + v["ni"]
    retained = d.one("SELECT g.Credit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                     "WHERE g.VoucherNumber = ? AND a.AccountName = 'Retained Earnings'", close2)
    claim(abs(retained - v["ni"]) < 0.005, f"net income equals the credit of {close2} to retained earnings")
    claim(abs(v["assets"] - v["le_total"]) < 0.005, "assets equal liabilities plus equity plus net income")
    claim(abs(rows.get(("Equity", "Closing"), 0.0)) < 0.005, "the Closing subtype has a zero balance before the closes")
    claim(set(rows) <= {("Revenue", "Operating Revenue"), ("Revenue", "Contra Revenue"), ("Revenue", "Other Income or Expense"),
                        ("Expense", "COGS"), ("Expense", "Operating Expense"), ("Expense", "Other Expense"),
                        ("Asset", "Current Asset"), ("Asset", "Fixed Asset"), ("Asset", "Contra Fixed Asset"),
                        ("Liability", "Current Liability"), ("Liability", "Long-Term Liability"), ("Equity", "Equity"),
                        ("Equity", "Closing")}, "the subtypes listed are all the subtypes with balances")
    return v


def revenue_by_month(d, number: str) -> dict[tuple[int, int], float]:
    return {(int(y), int(m)): b for y, m, b in d.q(
        "SELECT substr(PostingDate, 1, 4), substr(PostingDate, 6, 2), ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry "
        "WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry' GROUP BY 1, 2", d.account(number))}


@note("ch11.ex2", EXERCISES)
def ex2(d, claim):
    closes = [r[0] for r in d.q(
        "SELECT DISTINCT j.EntryNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        "JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID WHERE g.SourceDocumentType = 'JournalEntry' "
        "AND a.AccountType = 'Revenue' AND a.AccountNumber IN ('4010', '4020', '4030', '4040', '4080') ORDER BY 1")]
    types = {r[0] for r in d.q("SELECT EntryType FROM JournalEntry WHERE EntryNumber IN (%s)" % ",".join("?" * len(closes)), *closes)}
    claim(all(t.startswith("Year-End Close") for t in types), "the only journal entries to the revenue lines are year-end closes")
    monthly = {name: revenue_by_month(d, number) for number, name in REVENUE_LINES}
    months = sorted({k for m in monthly.values() for k in m})
    ytd = [(name, sum(b for (y, _), b in monthly[name].items() if y == d.C)) for _, name in REVENUE_LINES]
    total = sum(b for _, b in ytd)
    tb = d.one("SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID IN (%s) AND FiscalYear = ? AND %s"
               % (",".join(str(d.account(n)) for n, _ in REVENUE_LINES), d.no_closes()), d.C)
    claim(abs(tb - total) < 0.005, "the year-to-date total equals the trial balance of those accounts")
    freight = d.one(f"SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                    d.account("4050"), d.C)
    furniture = monthly["Furniture"]
    change = {m: (furniture[(d.C, m)], furniture[(d.P, m)]) for m in range(1, 13)}
    down = min(change, key=lambda m: change[m][0] / change[m][1])
    up = max(change, key=lambda m: change[m][0] / change[m][1])
    # The prior-year month behind the largest decline, ranked among the prior year's months (a high base explains part of it).
    base_rank = sorted((furniture[(d.P, m)] for m in range(1, 13)), reverse=True).index(change[down][1]) + 1
    # The current year's Furniture promotion (Chapter 6): the months it priced orders in, and the later months its orders
    # were invoiced in.
    promo = d.q("SELECT PromotionID, EffectiveStartDate, EffectiveEndDate FROM PromotionProgram WHERE ItemGroup = 'Furniture' "
                "AND substr(EffectiveStartDate, 1, 4) = ?", str(d.C))
    claim(len(promo) == 1, f"fiscal {d.C} has one Furniture promotion")
    promo_id, start, stop = promo[0] if promo else (None, f"{d.C}-01-01", f"{d.C}-01-01")
    priced = list(range(int(start[5:7]), int(stop[5:7]) + 1))
    claim(bool(priced) and stop[:4] == start[:4], "the promotion's dates run forward within the year")
    invoiced = [int(m) for (m,) in d.q("SELECT DISTINCT substr(s.InvoiceDate, 6, 2) FROM SalesInvoiceLine l JOIN SalesInvoice s "
                                       "ON s.SalesInvoiceID = l.SalesInvoiceID WHERE l.PromotionID = ? AND substr(s.InvoiceDate, 1, 4) = ? "
                                       "ORDER BY 1", promo_id, str(d.C))]
    later = [m for m in invoiced if m > (priced[-1] if priced else 12)]
    claim(bool(later), "the promotion's orders were invoiced after it ended")
    claim(down in priced + later or up in priced + later,
          "the largest decline or the largest increase falls in the promotion's months or the months its orders were invoiced "
          "(so its timing is the first thing to examine)")
    return dict(closes=closes, rows=len(REVENUE_LINES) * len(months), lines=len(REVENUE_LINES), months=len(months),
                ytd=ytd, total=total, freight=freight,
                base=["highest", "second-highest", "third-highest"][base_rank - 1] if base_rank <= 3 else None,
                priced=[MONTHS[m - 1] for m in priced], later=[MONTHS[m - 1] for m in later],
                down=dict(month=MONTHS[down - 1], now=change[down][0], before=change[down][1],
                          pct=change[down][0] / change[down][1] - 1),
                up=dict(month=MONTHS[up - 1], now=change[up][0], before=change[up][1], pct=change[up][0] / change[up][1] - 1))


@note("ch11.ex3", EXERCISES)
def ex3(d, claim):
    rows = d.q("SELECT ItemGroup, ItemCode, ItemName, ListPrice - StandardCost FROM Item WHERE ListPrice IS NOT NULL")
    groups = sorted({r[0] for r in rows})
    by_group = {g: sorted((r for r in rows if r[0] == g), key=lambda r: -r[3]) for g in groups}
    claim(all(len({round(r[3], 2) for r in by_group[g]}) == len(by_group[g]) for g in groups),
          "no two items in a group share a unit margin (so RANK, DENSE_RANK, and ROW_NUMBER agree)")
    top = sorted(([g] + list(by_group[g][0][1:]) for g in groups), key=lambda t: -t[3])
    ranges_order = ["Furniture", "Accessories", "Lighting", "Textiles", "Services"]
    claim(sorted(ranges_order) == groups, "the item groups are the five the ranges list")
    services_cost = d.one("SELECT MAX(StandardCost) FROM Item WHERE ItemGroup = 'Services' AND ListPrice IS NOT NULL")
    claim(services_cost == 0, "Services carry a StandardCost of zero")
    manufactured = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured' AND ItemType = 'Finished Good'")
    purchased = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Purchased' AND ItemType = 'Finished Good'")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Purchased' AND ItemType = 'Finished Good' "
                "AND StandardFixedOverheadCost > 0") == 0, "purchased finished goods carry no fixed overhead")
    return dict(items=len(rows), counts=[(g, len(by_group[g])) for g in groups], top=top,
                ranges=[(g, by_group[g][-1][3], by_group[g][0][3]) for g in ranges_order],
                manufactured=manufactured, purchased=purchased)


@note("ch11.ex4", EXERCISES)
def ex4(d, claim):
    rows = d.q("SELECT l.EmployeeID, e.JobTitle, SUM(l.OvertimeHours) AS h FROM LaborTimeEntry l JOIN Employee e "
               "ON e.EmployeeID = l.EmployeeID WHERE l.LaborType <> 'NonManufacturing' AND substr(l.WorkDate, 1, 4) = ? "
               "GROUP BY 1, 2 HAVING h > 0 ORDER BY h DESC, l.EmployeeID", str(d.C))
    total = sum(r[2] for r in rows)
    running, half = 0.0, None
    for rank, r in enumerate(rows, 1):
        running += r[2]
        if half is None and running >= total / 2:
            half = rank
    payroll = d.one("SELECT SUM(l.Hours) FROM PayrollRegisterLine l JOIN PayrollRegister r ON r.PayrollRegisterID = "
                    "l.PayrollRegisterID JOIN PayrollPeriod p ON p.PayrollPeriodID = r.PayrollPeriodID JOIN CostCenter c "
                    "ON c.CostCenterID = r.CostCenterID WHERE c.CostCenterName = 'Manufacturing' "
                    "AND l.LineType = 'Overtime Earnings' AND p.FiscalYear = ?", d.C)
    titles = sorted({r[1] for r in rows})
    by_title = [(t + "s", sum(1 for r in rows if r[1] == t), sum(r[2] for r in rows if r[1] == t)) for t in titles]
    averages = [h / n for _, n, h in by_title]
    weekly = total / len(rows) / 52
    claim(rows[0][2] / rows[4][2] < 1.1, "the five largest totals are close together")
    claim(abs(half - len(rows) / 2) <= 1, "half of the overtime is reached at about half of the employees")
    claim(max(averages) / min(averages) < 1.05, "overtime per employee is about the same in every job title (plant-wide)")
    return dict(employees=len(rows), total=total, payroll=payroll, top=[(r[0], r[1], r[2]) for r in rows[:5]],
                half=half, titles=by_title, year=d.C, weekly=WORDS[round(weekly)])


@note("ch11.ex5", EXERCISES)
def ex5(d, claim):
    rows = d.q("SELECT j.EntryNumber, j.EntryType, c.JobTitle, "
               "(strftime('%w', j.CreatedDate) IN ('0', '6')), (date(j.CreatedDate) > j.PostingDate), "
               "(j.CreatedByEmployeeID = j.ApprovedByEmployeeID), (j.TotalAmount > COALESCE(a.MaxApprovalAmount, 0)), "
               "(j.TotalAmount = ROUND(j.TotalAmount / 1000, 0) * 1000) FROM JournalEntry j "
               "LEFT JOIN Employee a ON a.EmployeeID = j.ApprovedByEmployeeID "
               "LEFT JOIN Employee c ON c.EmployeeID = j.CreatedByEmployeeID")
    flags = ["Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"]
    counts = [(f, sum(r[3 + i] for r in rows)) for i, f in enumerate(flags)]
    scores = {}
    for r in rows:
        s = sum(r[3:8])
        scores[s] = scores.get(s, 0) + 1
    present = sorted(scores)
    missing = [s for s in range(present[-1] + 1) if s not in scores]
    top = [r for r in rows if sum(r[3:8]) == present[-1]]
    claim(len(top) == 1, "one entry has the highest score")
    claim(top[0][1] == "Opening" and top[0][2] == "Chief Financial Officer",
          "the highest-scoring entry is the opening balance entry, created by the chief financial officer")
    claim(len(missing) <= 1, "at most one score in the range is missing (the wording names one)")
    return dict(entries=len(rows), counts=counts, scores=[(s, scores[s]) for s in present], missing=missing,
                top_score=present[-1], top_entry=top[0][0])


@note("ch11.ex6", EXERCISES)
def ex6(d, claim):
    amounts = d.q("SELECT RequisitionID, RequisitionNumber, RequestDate, RequestedByEmployeeID, ApprovedByEmployeeID, Status, "
                  "ROUND(Quantity * EstimatedUnitCost, 2) FROM PurchaseRequisition ORDER BY RequisitionID")
    bands = [sum(1 for r in amounts if lo <= r[6] < lo + 50) for lo in range(4700, 5250, 50)]
    claim(bands[5] > bands[6], "the band just below 5,000 holds more than the band just above it")
    middles = [i for i in range(1, len(amounts) - 1) if amounts[i - 1][6] == amounts[i][6] == amounts[i + 1][6]]
    runs = [amounts[i - 1:i + 2] for i in middles]
    claim(len(runs) == 2, "there are two runs of three")
    claim(len({r[6] for run in runs for r in run}) == 1, "both runs have the same amount")
    claim(all(r[2][5:] == "01-01" for run in runs for r in run), "each run is on January 1")
    unapproved_in_runs = [r[0] for run in runs for r in run if r[4] is None]
    approved = [r for run in runs for r in run if r[4] is not None]
    claim(all(sum(r[4] is None for r in run) == 2 for run in runs), "in each run, two requisitions have no approver")
    cfo = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Chief Financial Officer'")
    claim(all(r[4] == cfo for r in approved), "the third requisition of each run was approved by the chief financial officer")
    claim(all(r[5] == "Converted to PO" for run in runs for r in run), "all six were converted to purchase orders")
    no_approver = [r for r in amounts if r[4] is None]
    claim(len(no_approver) == 6 and set(unapproved_in_runs) <= {r[0] for r in no_approver},
          "the unapproved ones are among the six of Exercise 2.5")
    claim(all(4950 <= r[6] < 5000 for r in no_approver), "all requisitions without an approver fall just below 5,000")
    limits = d.q("SELECT MaxApprovalAmount, COUNT(*) FROM Employee GROUP BY 1 ORDER BY 1")
    claim([l for l, _ in limits] == [0, 5000, 25000, 250000] and dict(limits)[5000] == 2,
          "the approval limits are 0, 5,000 (two employees), 25,000, and 250,000")
    claim(set(r[0] for r in d.q("SELECT JobTitle FROM Employee WHERE MaxApprovalAmount = 5000")) <=
          {"Production Supervisor", "Production Planner"}, "the two 5,000 limits belong to production employees")
    return dict(bands=bands, twice=bands[5] >= 2 * max(bands[4], bands[6]), amount=runs[0][0][6], cfo=cfo,
                runs=[dict(first=run[0][1], last=run[2][1][-6:], date=run[0][2], requesters=[r[3] for r in run]) for run in runs],
                unapproved=unapproved_in_runs, middles=[amounts[i][0] for i in middles],
                low=min(r[6] for r in no_approver), high=max(r[6] for r in no_approver))
