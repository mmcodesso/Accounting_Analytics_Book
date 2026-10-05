"""The Part II case's instructor notes (deciding on the next year's promotion calendar): the values each
note states, and the claims its wording makes.

The proposal is the current year's calendar (the promotions that start in d.C), and the plan it is costed
against is the next year's budget (d.N). Promotions are labeled by their scope: the collection, item group,
or customer segment they cover.
"""

from __future__ import annotations

import statistics as st
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

from notes import note

CASE = "cases/part-2-case.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
SCOPE_WORD = {"Collection": "collection", "ItemGroup": "item group", "Segment": "segment"}
SCOPE_SQL = {"Collection": "i.CollectionName", "ItemGroup": "i.ItemGroup", "Segment": "c.CustomerSegment"}
CALENDAR = {"Collection": [3, 4], "ItemGroup": [9, 10], "Segment": [11]}   # the months the wording names
PLAIN_MONTHS = (1, 2, 5, 6, 7, 8, 12)                                       # months no promotion ever ran in
ORDERS = ("FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
          "JOIN Item i ON i.ItemID = l.ItemID JOIN Customer c ON c.CustomerID = o.CustomerID")
BILLED = "FROM SalesInvoiceLine l JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID"
BUDGET = ("FROM BudgetLine b JOIN Item i ON i.ItemID = b.ItemID WHERE b.BudgetCategory = 'Revenue'")


def series(items) -> str:
    """'a', 'a and b', 'a, b, and c'."""
    items = [str(x) for x in items]
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def xround(value: float, places: int = 2) -> float:
    """Round half away from zero, as Excel's ROUND does (scripts/figures/excel.py)."""
    text = repr(float(f"{value:.15g}"))
    return float(Decimal(text).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


# --- shared measures ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def promotions(d) -> tuple[dict, ...]:
    """Each promotion with its scope label, recorded dates, and the order dates of its lines."""
    out = []
    for pid, code, scope, seg, grp, coll, rate, start, end, approver, approved in d.q(
            "SELECT PromotionID, PromotionCode, ScopeType, CustomerSegment, ItemGroup, CollectionName, DiscountPct, "
            "EffectiveStartDate, EffectiveEndDate, ApprovedByEmployeeID, ApprovedDate FROM PromotionProgram "
            "ORDER BY PromotionID"):
        lo, hi, n = d.q(f"SELECT MIN(o.OrderDate), MAX(o.OrderDate), COUNT(*) {ORDERS} WHERE l.PromotionID = ?", pid)[0]
        months = sorted({int(m) for (m,) in d.q(
            f"SELECT DISTINCT substr(o.OrderDate, 6, 2) {ORDERS} WHERE l.PromotionID = ?", pid)})
        out.append(dict(id=pid, code=code, scope=scope, label={"Collection": coll, "ItemGroup": grp, "Segment": seg}[scope],
                        rate=rate, start=start, end=end, approver=approver, approved=approved, year=int(start[:4]),
                        lo=lo, hi=hi, lines=n, months=months))
    return tuple(out)


def proposal(d) -> dict[str, dict]:
    """The current year's calendar, by scope type."""
    return {p["scope"]: p for p in promotions(d) if p["year"] == d.C}


def calendar_claims(d, claim) -> None:
    """The wording names the months each kind of promotion ran in, and one promotion of each kind a year."""
    claim(all(p["months"] == CALENDAR[p["scope"]] and int(p["lo"][:4]) == int(p["hi"][:4]) == p["year"]
              for p in promotions(d)),
          "every promotion's lines were ordered in its year, collections in March-April, item groups in "
          "September-October, segments in November")
    claim(all(sorted(p["scope"] for p in promotions(d) if p["year"] == y) == ["Collection", "ItemGroup", "Segment"]
              for y in d.years), "each year ran one collection, one item group, and one segment promotion")


@lru_cache(maxsize=None)
def commission(d) -> tuple[float, float, float]:
    """Tutorial 7.3's rate: the current year's 6290 postings without the closes over invoice-line revenue."""
    comm = d.one(f"SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                 d.account("6290"), d.C)
    rev = d.one(f"SELECT SUM(l.LineTotal) {BILLED} WHERE substr(i.InvoiceDate, 1, 4) = ?", str(d.C))
    return comm, rev, comm / rev


def unit_model(d, pid: int, year: int | None = None) -> dict:
    """Units, price before discount, and standard cost per unit (with its fixed overhead) of a promotion's billed lines."""
    where, args = "l.PromotionID = ?", [pid]
    if year is not None:
        where, args = where + " AND substr(i.InvoiceDate, 1, 4) = ?", args + [str(year)]
    u, gross, std, fixed = d.q(
        f"SELECT SUM(l.Quantity), SUM(l.Quantity * l.UnitPrice), SUM(l.Quantity * it.StandardCost), "
        f"SUM(l.Quantity * COALESCE(it.StandardFixedOverheadCost, 0)) {BILLED} JOIN Item it ON it.ItemID = l.ItemID "
        f"WHERE {where}", *args)[0]
    return dict(units=u, price=gross / u, cost=std / u, fixed=fixed / u)


def breakeven(price: float, cost: float, rate: float, c: float) -> float:
    """The increase in volume at which the promotion's contribution equals the contribution without it."""
    return (price * (1 - c) - cost) / (price * (1 - rate) * (1 - c) - cost) - 1


@lru_cache(maxsize=None)
def breakevens(d) -> dict[int, float]:
    c = commission(d)[2]
    out = {}
    for p in promotions(d):
        m = unit_model(d, p["id"])
        out[p["id"]] = breakeven(m["price"], m["cost"], p["rate"], c)
    return out


@lru_cache(maxsize=None)
def volume(d) -> tuple[dict, ...]:
    """List-price order value in each promotion's months against the other months of its year and the year before."""
    first = int(d.one("SELECT MIN(OrderDate) FROM SalesOrder")[:4])
    out = []
    for p in promotions(d):
        by_month = {(int(y), int(m)): v for y, m, v in d.q(
            f"SELECT substr(o.OrderDate, 1, 4), substr(o.OrderDate, 6, 2), SUM(l.Quantity * l.BaseListPrice) {ORDERS} "
            f"WHERE {SCOPE_SQL[p['scope']]} = ? GROUP BY 1, 2", p["label"])}
        y, months = p["year"], p["months"]
        window = sum(by_month.get((y, m), 0.0) for m in months)
        other = [by_month.get((y, m), 0.0) for m in range(1, 13) if m not in months]
        expected, sd = st.mean(other) * len(months), st.stdev(other)
        prior = sum(by_month.get((y - 1, m), 0.0) for m in months) if y - 1 >= first else None
        out.append(dict(id=p["id"], label=p["label"], scope=SCOPE_WORD[p["scope"]], months=len(months),
                        lift=window / expected - 1, sd=sd / st.mean(other),
                        py=window / prior - 1 if prior else None,
                        z=(window - expected) / (sd * len(months) ** 0.5)))
    return tuple(out)


def goal_seek(d) -> tuple[dict, float]:
    """The item-group promotion's discount at which the largest measured increase just pays for it."""
    best = max(volume(d), key=lambda v: v["lift"])
    c = commission(d)[2]
    m = unit_model(d, proposal(d)["ItemGroup"]["id"], d.C)
    p, s, lift = m["price"], m["cost"], best["lift"]
    return best, 1 - ((p * (1 - c) - s) / (1 + lift) + s) / (p * (1 - c))


@lru_cache(maxsize=None)
def proposal_quarters(d) -> tuple[list, list, float]:
    """The proposal's discounts billed in the current year, by promotion and invoice quarter, and by quarter."""
    by_promo = []
    for scope in ("Collection", "ItemGroup", "Segment"):
        p = proposal(d)[scope]
        rows = d.q(f"SELECT (CAST(substr(i.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3, SUM(l.Quantity * l.UnitPrice * l.Discount) "
                   f"{BILLED} WHERE l.PromotionID = ? AND substr(i.InvoiceDate, 1, 4) = ? GROUP BY 1 ORDER BY 1", p["id"], str(d.C))
        by_promo.append(dict(id=p["id"], quarters=[(qn, amount) for qn, amount in rows]))
    totals: dict[int, float] = {}
    for p in by_promo:
        for qn, amount in p["quarters"]:
            totals[qn] = totals.get(qn, 0.0) + amount
    quarters = sorted(totals.items())
    return by_promo, quarters, sum(totals.values())


def budget_ratio(d, where: str, *args) -> tuple[float, float]:
    """BudgetAmount and Quantity x Item ListPrice of the revenue budget rows that match."""
    return d.q(f"SELECT SUM(b.BudgetAmount), SUM(b.Quantity * i.ListPrice) {BUDGET} AND {where}", *args)[0]


def monthly_ratios(d, year: int, column: str, value: str) -> dict[int, float]:
    return {m: r for m, r in d.q(f"SELECT b.Month, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) {BUDGET} "
                                 f"AND b.FiscalYear = ? AND {column} = ? GROUP BY 1", year, value)}


# 1 when an order line (aliases i, c, p) falls in its promotion's scope, 0 otherwise (a blank collection included)
IN_SCOPE = ("COALESCE((p.ScopeType = 'ItemGroup' AND i.ItemGroup = p.ItemGroup) "
            "OR (p.ScopeType = 'Segment' AND c.CustomerSegment = p.CustomerSegment) "
            "OR (p.ScopeType = 'Collection' AND i.CollectionName = p.CollectionName), 0)")


# --- the notes ---------------------------------------------------------------------------------

@note("case2.r1", CASE)
def r1(d, claim):
    """Requirement 1 (not registered: the comment names the wrong close; see the module docstring)."""
    order_lines, order_total, promo_disc = d.q(
        "SELECT COUNT(*), SUM(LineTotal), SUM(CASE WHEN PromotionID IS NOT NULL THEN Quantity * UnitPrice * Discount END) "
        "FROM SalesOrderLine")[0]
    orders, orders_total = d.q("SELECT COUNT(*), SUM(OrderTotal) FROM SalesOrder")[0]
    claim(abs(order_total - orders_total) < 0.005, "the LineTotal of the order lines equals the OrderTotal of the orders")
    claim(d.one("SELECT COUNT(*) FROM SalesOrder o LEFT JOIN (SELECT SalesOrderID, SUM(LineTotal) AS s FROM SalesOrderLine "
                "GROUP BY 1) t ON t.SalesOrderID = o.SalesOrderID WHERE t.s IS NULL OR ABS(o.OrderTotal - t.s) > 0.005") == 0,
          "every order agrees with its own lines")
    claim(d.one("SELECT COUNT(*) FROM SalesOrderLine WHERE PromotionID IS NULL AND Discount <> 0") == 0,
          "no order line without a PromotionID has a nonzero Discount")
    comm, rev, rate = commission(d)
    closes = [r[0] for r in d.q("SELECT DISTINCT VoucherNumber FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                                "AND SourceDocumentType = 'JournalEntry' ORDER BY 1", d.account("6290"), d.C)]
    claim(len(closes) == 1 and closes[0] in d.closes, "the only journal entry to 6290 in the year is a year-end close")
    return dict(order_lines=order_lines, order_total=order_total, orders=orders,
                promo_lines=d.one("SELECT COUNT(*) FROM SalesOrderLine WHERE PromotionID IS NOT NULL"), promo_disc=promo_disc,
                billed=d.one("SELECT COUNT(*) FROM SalesInvoiceLine"),
                billed_total=d.one("SELECT SUM(LineTotal) FROM SalesInvoiceLine"),
                items=d.one("SELECT COUNT(*) FROM Item"), customers=d.one("SELECT COUNT(*) FROM Customer"),
                promotions=d.one("SELECT COUNT(*) FROM PromotionProgram"),
                overrides=d.one("SELECT COUNT(*) FROM PriceOverrideApproval"), employees=d.one("SELECT COUNT(*) FROM Employee"),
                budget_rows=d.one("SELECT COUNT(*) FROM BudgetLine WHERE BudgetCategory = 'Revenue'"),
                rate=rate, comm=comm, rev=rev, close=closes[0])


@note("case2.r2", CASE)
def r2(d, claim):
    by_year = {int(y): (disc, rev) for y, disc, rev in d.q(
        f"SELECT substr(i.InvoiceDate, 1, 4), SUM(l.Quantity * l.UnitPrice * l.Discount), SUM(l.LineTotal) {BILLED} GROUP BY 1")}
    years = [dict(year=y, disc=by_year[y][0], rev=by_year[y][1], share=by_year[y][0] / by_year[y][1]) for y in d.years]
    promo = d.q(f"SELECT l.PromotionID, l.Quantity * l.UnitPrice * l.Discount {BILLED} WHERE l.PromotionID IS NOT NULL")
    total = sum(r[1] for r in promo)
    claim(abs(total - sum(y["disc"] for y in years)) < 0.005, "every promotion line was billed within the three fiscal years")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NULL AND Discount <> 0") == 0,
          "only promotion lines carry a discount, so the discount total is the promotions' cost")
    growth = years[-1]["disc"] / years[0]["disc"]
    claim(growth > 1, "the cost grew over the window")
    grew = ("more than tripled" if growth >= 3 else "nearly tripled" if growth >= 2.5 else "more than doubled" if growth >= 2
            else "nearly doubled" if growth >= 1.8 else f"grew {growth - 1:.0%}")
    by_promo = [dict(id=pid, disc=sum(r[1] for r in promo if r[0] == pid)) for pid in sorted({r[0] for r in promo})]

    groups = [dict(group=g, list=round(lst, 2), red=round(lst - gross, 2), disc=round(disc, 2), net=net)
              for g, lst, gross, disc, net in d.q(
                  f"SELECT it.ItemGroup, SUM(l.Quantity * l.BaseListPrice), SUM(l.Quantity * l.UnitPrice), "
                  f"SUM(l.Quantity * l.UnitPrice * l.Discount), SUM(l.LineTotal) {BILLED} JOIN Item it ON it.ItemID = l.ItemID "
                  f"WHERE substr(i.InvoiceDate, 1, 4) = ? GROUP BY 1 ORDER BY 2 DESC", str(d.C))]
    lst, gross, disc, net = d.q(f"SELECT SUM(l.Quantity * l.BaseListPrice), SUM(l.Quantity * l.UnitPrice), "
                                f"SUM(l.Quantity * l.UnitPrice * l.Discount), SUM(l.LineTotal) {BILLED} "
                                f"WHERE substr(i.InvoiceDate, 1, 4) = ?", str(d.C))[0]
    after = round(gross, 2) - round(disc, 2)
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ABS(LineTotal - Quantity * UnitPrice * (1 - Discount)) "
                "> 0.0051") == 0, "LineTotal is each line's amount rounded to the cent, so the difference is line rounding")

    ledger = [dict(number=n, credit=cr) for n, cr, dr in d.q(
        "SELECT a.AccountNumber, SUM(g.Credit), SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.FiscalYear = ? AND g.SourceLineID IS NOT NULL "
        "GROUP BY 1 ORDER BY 1", d.C)]
    claim(d.one("SELECT COALESCE(SUM(g.Debit), 0) FROM GLEntry g WHERE g.SourceDocumentType = 'SalesInvoice' "
                "AND g.FiscalYear = ? AND g.SourceLineID IS NOT NULL", d.C) == 0, "the invoice lines post only credits")
    ledger_total = sum(a["credit"] for a in ledger)
    posted = ("SELECT i.SalesInvoiceID, i.InvoiceNumber, i.InvoiceDate, MIN(g.PostingDate) AS posted FROM SalesInvoice i "
              "JOIN GLEntry g ON g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID = i.SalesInvoiceID "
              "GROUP BY i.SalesInvoiceID")
    cutoff = d.q(f"SELECT * FROM ({posted}) WHERE substr(InvoiceDate, 1, 4) = ? AND substr(posted, 1, 4) = ? "
                 f"ORDER BY InvoiceNumber", str(d.P), str(d.C))
    claim(not d.q(f"SELECT * FROM ({posted}) WHERE substr(InvoiceDate, 1, 4) = ? AND substr(posted, 1, 4) <> ?",
                  str(d.C), str(d.C)), "no invoice of the current year is posted in another year")
    ids = ",".join(str(r[0]) for r in cutoff)
    cutoff_accounts = [dict(number=n, credit=cr) for n, cr in d.q(
        f"SELECT a.AccountNumber, SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        f"WHERE g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID IN ({ids}) AND g.SourceLineID IS NOT NULL "
        f"GROUP BY 1 ORDER BY 1")]
    difference = ledger_total - net
    claim(abs(difference - sum(a["credit"] for a in cutoff_accounts)) < 0.005,
          "the difference between ledger and lines is exactly the invoices dated in the prior year and posted in this one")
    numbers = [int(r[1][-6:]) for r in cutoff]
    claim(numbers == list(range(numbers[0], numbers[0] + len(numbers))), "the cutoff invoices are consecutive (a range)")
    claim(all(r[2] >= f"{d.P}-10-01" for r in cutoff), f"the cutoff invoices are dated late in {d.P}")
    claim(len({r[3] for r in cutoff}) == 1, "the cutoff invoices were all posted on one date")

    freight_id, tax_id = d.account("4050"), d.account("2050")
    freight = d.one("SELECT SUM(Credit) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'SalesInvoice' "
                    "AND FiscalYear = ?", freight_id, d.C)
    header = d.q("SELECT SUM(i.FreightAmount), SUM(i.TaxAmount) FROM SalesInvoice i WHERE i.SalesInvoiceID IN "
                 "(SELECT SourceDocumentID FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ?)", d.C)[0]
    claim(abs(freight - header[0]) < 0.005 and d.one(
        "SELECT COUNT(SourceLineID) FROM GLEntry WHERE AccountID = ?", freight_id) == 0,
        "freight revenue comes from the invoice header (FreightAmount), not from the lines")
    tax = d.one("SELECT SUM(Credit) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'SalesInvoice' AND FiscalYear = ?",
                tax_id, d.C)
    claim(abs(tax - header[1]) < 0.005, "account 2050 holds the invoices' sales tax")
    discounts_id = d.account("4070")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", discounts_id) == 0, "4070 has no postings in any year")

    by_promo_q, quarters, prop_total = proposal_quarters(d)
    q4 = dict(quarters).get(4, 0.0)
    fall = proposal(d)["ItemGroup"]
    claim(fall["months"] == [9, 10], "the item-group promotion runs in the fall")
    claim(d.one(f"SELECT COUNT(*) {BILLED} WHERE l.PromotionID = ? AND i.InvoiceDate > ?", fall["id"], fall["end"]) > 0,
          "the fall promotion's orders are invoiced after it ends")
    name = lambda account_id: d.one("SELECT AccountName FROM Account WHERE AccountID = ?", account_id)
    # "in all" is the total of the yearly amounts as stated (the unrounded total can differ by a cent)
    return dict(years=years, grew=grew, span=word(len(years) - 1), total=sum(round(y["disc"], 2) for y in years), lines=len(promo), rounded=sum(xround(r[1]) for r in promo), by_promo=by_promo,
                groups=groups, list=lst, red=lst - gross, disc=disc, net=net, after=after, rounding=net - after,
                ledger=ledger, ledger_total=ledger_total, difference=difference,
                first=cutoff[0][1], last=cutoff[-1][1][-6:], cutoff_accounts=cutoff_accounts, cutoff_posted=cutoff[0][3],
                freight_name=name(freight_id), freight=freight, discounts_name=name(discounts_id),
                prop=by_promo_q, q4=q4, prop_total=prop_total, q4_share=q4 / prop_total)


@note("case2.r3", CASE)
def r3(d, claim):
    """Requirement 3 (not registered: the comment rounds one value twice; see the module docstring)."""
    calendar_claims(d, claim)
    bad = [p["id"] for p in promotions(d) if d.one(
        f"SELECT COUNT(*) {ORDERS} WHERE l.PromotionID = ? AND o.OrderDate BETWEEN ? AND ?", p["id"], p["start"], p["end"])
        < p["lines"]]
    claim(len(bad) > 0, "some promotions have recorded dates that do not cover their lines")
    vol = volume(d)
    claim(all(v["z"] < 2 for v in vol), "no increase is unusual (all within two standard deviations)")
    falls = [v for v in vol if v["z"] <= -2]              # unusual falls, if any: no promotion lifted volume either way
    top = max(vol, key=lambda v: v["lift"])
    low = min(vol, key=lambda v: v["lift"])
    claim(top["lift"] > 0, "the largest difference is an increase")
    claim(low["lift"] < 0, "the lowest difference is a fall")
    sd_total = ("one-month total (the monthly sd)" if top["months"] == 1 else
                f"{word(top['months'])}-month total (the monthly sd times the square root of {top['months']})")
    be = breakevens(d)
    claim(all(v["lift"] < be[v["id"]] for v in vol), "every difference is below its break-even increase")
    near = max(vol, key=lambda v: v["lift"] / be[v["id"]])

    first = d.q("WITH f AS (SELECT CustomerID, MIN(OrderDate) AS d FROM SalesOrder GROUP BY 1) "
                "SELECT f.CustomerID, f.d, EXISTS (SELECT 1 FROM SalesOrder o JOIN SalesOrderLine l ON l.SalesOrderID = o.SalesOrderID "
                "WHERE o.CustomerID = f.CustomerID AND o.OrderDate = f.d AND l.PromotionID IS NOT NULL), c.CustomerSince "
                "FROM f JOIN Customer c ON c.CustomerID = f.CustomerID ORDER BY f.d")
    promoted = [r for r in first if r[2]]                     # customers whose first order included a promotion line
    promoted_ids = sorted({p for r in promoted for (p,) in d.q(
        "SELECT DISTINCT l.PromotionID FROM SalesOrder o JOIN SalesOrderLine l ON l.SalesOrderID = o.SalesOrderID "
        "WHERE o.CustomerID = ? AND o.OrderDate = ? AND l.PromotionID IS NOT NULL", r[0], r[1])})
    claim(first[0][1].startswith(f"{d.F}-01"), f"the data begins in January {d.F}")
    early = sum(1 for r in first if r[1] <= f"{d.F}-04-30")
    claim(early / len(first) >= 0.9, f"first orders cluster in January to April {d.F}")
    late = [r for r in first if r[1] > f"{d.F}-06-30"]
    last = first[-1][1]
    since = [r for r in first if r[3] >= f"{d.F}-01-01"]
    return dict(bad=series(bad), vol=vol, top=top, low=low, sd_total=sd_total, far=all(v["lift"] < be[v["id"]] / 2 for v in vol),
                near=dict(near, be=be[near["id"]]),
                falls=series(f"promotion {v['id']}'s {v['lift']:+.1%} ({v['z']:.1f} standard deviations)" for v in falls),
                n_falls=len(falls), promoted=len(promoted), n_promoted=word(len(promoted)),
                promoted_ids=series(promoted_ids), customers=len(first), late=word(len(late)),
                last=f"{MONTHS[int(last[5:7]) - 1]} {last[:4]}", since=len(since),
                since_before=sum(1 for r in since if r[1] < r[3]))


@note("case2.r4", CASE)
def r4(d, claim):
    calendar_claims(d, claim)
    prop = proposal(d)
    _, _, c = commission(d)
    model = {}
    for scope, p in prop.items():
        m = unit_model(d, p["id"], d.C)
        claim(abs(m["units"] - unit_model(d, p["id"])["units"]) < 0.005, f"all of promotion {p['id']}'s lines were billed in {d.C}")
        model[scope] = dict(id=p["id"], label=p["label"], **m, be=breakeven(m["price"], m["cost"], p["rate"], c))
    grp = model["ItemGroup"]
    grp["be_variable"] = breakeven(grp["price"], grp["cost"] - grp["fixed"], prop["ItemGroup"]["rate"], c)
    grp["be5"] = breakeven(grp["price"], grp["cost"], 0.05, c)
    be = breakevens(d)
    best, discount = goal_seek(d)

    # budgets: promoted items at a lower price in their promotion months, the next year's budget flat
    promoted = []
    for y in d.years:
        for p in promotions(d):
            if p["year"] == y and p["scope"] in ("Collection", "ItemGroup"):
                column = "i.CollectionName" if p["scope"] == "Collection" else "i.ItemGroup"
                months = ",".join(str(m) for m in CALENDAR[p["scope"]])
                promoted.append(budget_ratio(d, f"b.FiscalYear = ? AND {column} = ? AND b.Month IN ({months})", y, p["label"]))
    promoted_ratio = sum(a for a, _ in promoted) / sum(b for _, b in promoted)
    claim(all(abs(a / b - promoted_ratio) < 0.0001 for a, b in promoted),
          "every year's promoted items are budgeted at the same fraction of list in their promotion months")
    groups = [g for (g,) in d.q(f"SELECT DISTINCT i.ItemGroup {BUDGET}")]
    claim(all(r[11] < min(r[m] for m in PLAIN_MONTHS) for y in d.years for g in groups
              for r in [monthly_ratios(d, y, "i.ItemGroup", g)]), "every group is budgeted lower in November")
    approvers = d.q("SELECT DISTINCT ApprovedByEmployeeID, ApprovedDate FROM BudgetLine WHERE FiscalYear = ?", d.N)
    claim(len(approvers) == 1, f"the {d.N} budget has one approver and one approval date")
    cfo, approved = approvers[0]
    claim(d.one("SELECT JobTitle FROM Employee WHERE EmployeeID = ?", cfo) == "Chief Financial Officer",
          f"the {d.N} budget was approved by the chief financial officer")
    flat = (lambda a, b: a / b)(*budget_ratio(d, "b.FiscalYear = ?", d.N))
    monthly = [r for _, r in d.q(f"SELECT b.Month, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) {BUDGET} "
                                 f"AND b.FiscalYear = ? GROUP BY 1", d.N)]
    claim(len(monthly) == 12 and all(abs(r - flat) < 0.0005 for r in monthly), f"the {d.N} budget is flat in every month")

    _, quarters, prop_total = proposal_quarters(d)
    fall = prop["ItemGroup"]
    claim(fall["months"] == [9, 10], "the item-group promotion runs in September-October")
    months = ",".join(str(m) for m in fall["months"])
    budget_units = d.one(f"SELECT SUM(b.Quantity) {BUDGET} AND b.FiscalYear = ? AND i.ItemGroup = ? AND b.Month IN ({months})",
                         d.N, fall["label"])
    ordered = d.one(f"SELECT SUM(l.Quantity) {ORDERS} WHERE i.ItemGroup = ? AND o.OrderDate BETWEEN ? AND ?",
                    fall["label"], f"{d.C}-{fall['months'][0]:02d}-01", f"{d.C}-{fall['months'][-1]:02d}-31")
    claim(3.5 <= budget_units / ordered < 4, "the budget's volume would overstate the cost almost fourfold")
    claim(not any("Customer" in r[1] for r in d.q("PRAGMA table_info(BudgetLine)")), "BudgetLine has no customer dimension")
    return dict(coll=model["Collection"], grp=grp, seg=model["Segment"], rate=c, be_low=min(be.values()),
                be_high=max(be.values()), promos=word(len(be)), best=best, discount=discount,
                promoted=promoted_ratio, cfo=cfo, approved=approved, flat=flat, cost=prop_total,
                contribution=prop_total * (1 - c), quarters=[(qn, round(amount, -2)) for qn, amount in quarters],
                budget_units=budget_units, ordered=ordered)


@note("case2.r5", CASE)
def r5(d, claim):
    calendar_claims(d, claim)
    promos = promotions(d)
    window = {p["id"]: d.one(f"SELECT COUNT(*) {ORDERS} WHERE l.PromotionID = ? AND o.OrderDate BETWEEN ? AND ?",
                             p["id"], p["start"], p["end"]) for p in promos}
    bad = [p for p in promos if window[p["id"]] < p["lines"]]
    claim(all(window[p["id"]] == 0 for p in bad), "every line of the failing promotions fails the date test")
    claim(all(window[p["id"]] == p["lines"] for p in promos if p not in bad), "every line of the other promotions passes")
    claim(all(p["scope"] == "Collection" for p in bad), "the failing promotions are the collection promotions")
    claim(all(p["lo"] >= f"{p['year']}-03-01" and p["hi"] <= f"{p['year']}-04-30" for p in bad),
          "all their lines were ordered between March 1 and April 30")
    claim(all(p["end"] < p["lo"] for p in bad), "their recorded end dates fall before the order dates")

    def missed(p, start, end):
        return d.one(f"SELECT COUNT(*) {ORDERS} WHERE {SCOPE_SQL[p['scope']]} = ? AND o.OrderDate BETWEEN ? AND ? "
                     f"AND (l.PromotionID IS NULL OR l.PromotionID <> ?)", p["label"], start, end, p["id"])
    claim(all(missed(p, f"{p['year']}-03-01", f"{p['year']}-04-30") == 0 for p in bad),
          "every line of the collection ordered in March-April carries the promotion")
    claim(all(max(r[3], r[4]) < min(r[m] for m in PLAIN_MONTHS) - 0.02 for p in bad
              for r in [monthly_ratios(d, p["year"], "i.CollectionName", p["label"])]),
          "each year's budget planned the collection's discount in March and April")

    oos = d.q(f"SELECT l.SalesOrderLineID, l.PromotionID, i.ItemID, i.ItemCode, i.ItemName, i.PrimaryMaterial "
              f"{ORDERS} JOIN PromotionProgram p ON p.PromotionID = l.PromotionID WHERE NOT {IN_SCOPE} "
              f"ORDER BY l.SalesOrderLineID")
    claim(len(oos) > 0 and len({r[1] for r in oos}) == 1 and len({r[2] for r in oos}) == 1,
          "the lines outside their scope belong to one promotion and one item")
    item_id, code, item_name, material = oos[0][2:]
    base = item_name.split(f" {material} ")[0]
    oos_promo = next(p for p in promos if p["id"] == oos[0][1])
    claim(base != item_name and base.startswith(oos_promo["label"] + " "),
          "the item's name places it in the promotion's collection (the discount is right)")
    claim(d.one("SELECT CollectionName FROM Item WHERE ItemID = ?", item_id) is None, "the item's CollectionName is blank")
    collections = {r[0] for r in d.q("SELECT DISTINCT CollectionName FROM Item WHERE CollectionName IS NOT NULL")}
    others = d.q("SELECT ItemCode, ItemName FROM Item WHERE CollectionName IS NULL AND ItemID <> ? AND ItemGroup IN "
                 "(SELECT ItemGroup FROM Item WHERE CollectionName IS NOT NULL) ORDER BY ItemID", item_id)
    claim(all(name.split()[0] in collections for _, name in others), "the other items without a collection are named for one")
    claim(d.one(f"SELECT COUNT(*) {ORDERS} JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                f"WHERE ABS(l.Discount - p.DiscountPct) > 1e-9") == 0, "every promotion line carries its promotion's DiscountPct")
    claim(all(missed(p, *((f"{p['year']}-03-01", f"{p['year']}-04-30") if p["scope"] == "Collection" else (p["start"], p["end"])))
              == 0 for p in promos), "no line in a promotion's scope and months lacks the promotion")

    approver = {p["approver"] for p in promos}
    claim(len(approver) == 1, "one employee approved every promotion")
    mgr_id = approver.pop()
    claim(all(p["approved"] == p["start"] for p in promos), "each promotion was approved on its start date")
    name, title, center = d.q("SELECT e.EmployeeName, e.JobTitle, cc.CostCenterName FROM Employee e "
                              "JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID WHERE e.EmployeeID = ?", mgr_id)[0]
    claim("Manager" in title, "the approver is a manager (the manager's own requests)")
    overrides = d.q("SELECT PriceOverrideApprovalID, RequestedByEmployeeID, ApprovedByEmployeeID, Status, SalesOrderLineID "
                    "FROM PriceOverrideApproval ORDER BY PriceOverrideApprovalID")
    approved = [r for r in overrides if r[3] == "Approved"]
    claim(all(r[2] == mgr_id for r in approved), "the same employee approved every approved override")
    own = [r for r in approved if r[1] == mgr_id]
    pending = [r for r in overrides if r[3] != "Approved"]
    claim(all(r[3] == "Pending" for r in pending), "the requests not approved are all Pending")
    own_pending = [r for r in pending if r[1] == mgr_id]       # the manager's own requests among them
    claim(all(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE SalesOrderLineID = ?", r[4]) > 0 for r in pending),
          "the Pending requests were billed")
    titles = sorted({r[0] for r in d.q("SELECT e.JobTitle FROM PriceOverrideApproval a JOIN Employee e "
                                       "ON e.EmployeeID = a.RequestedByEmployeeID WHERE a.RequestedByEmployeeID <> ?", mgr_id)})
    claim(center == "Sales", "pricing authority sits in sales, not finance")
    stack = (f"JOIN PriceOverrideApproval a ON a.PriceOverrideApprovalID = l.PriceOverrideApprovalID "
             f"WHERE l.PromotionID IS NOT NULL AND a.Status = 'Approved'")
    stack_orders = d.one(f"SELECT COUNT(*) FROM SalesOrderLine l {stack}")
    stack_billed, stack_disc = d.q(f"SELECT COUNT(*), SUM(l.Quantity * l.UnitPrice * l.Discount) FROM SalesInvoiceLine l {stack}")[0]
    claim(any(p["end"] < p["start"] for p in promos), "the system accepted end dates before start dates")
    return dict(bad=bad, good=word(len(promos) - len(bad)), oos=word(len(oos)), oos_promo=oos_promo["id"],
                oos_ids=series(r[0] for r in oos), item_id=item_id, code=code, base=base,
                others=series(f"{c} ({n.split()[0]})" for c, n in others),
                mgr=dict(id=mgr_id, name=name, title=title), promos=word(len(promos)), approved=len(approved), own=len(own),
                pending=word(len(pending)), pending_ids=[r[0] for r in pending], n_pending=len(pending),
                own_pending=len(own_pending), n_own_pending=word(len(own_pending)),
                requesters=series(t.lower() + "s" for t in titles),
                stack_orders=stack_orders, stack_billed=stack_billed, stack_disc=stack_disc)


@note("case2.r6", CASE)
def r6(d, claim):
    vol = volume(d)
    be = breakevens(d)
    claim(all(v["lift"] < be[v["id"]] for v in vol), "no promotion reached its break-even increase")
    near = all(v["lift"] < be[v["id"]] / 2 for v in vol)      # every increase under half its break-even
    _, quarters, prop_total = proposal_quarters(d)
    share = dict(quarters).get(4, 0.0) / prop_total
    claim(0.6 <= share < 0.72, "about two thirds of the cost lands in the fourth quarter")
    _, discount = goal_seek(d)
    return dict(promos=word(len(be)), proposed=word(len(proposal(d))), reached="came near" if near else "reached",
                cost=round(prop_total * (1 - commission(d)[2]), -4), discount=discount)
