"""The Part II case's instructor guides: the values the guides state, and the claims their wording makes.

The case (cases/part-2-case.qmd, "Deciding on the 2027 Promotion Calendar") is built in a new workbook, Charles River
Promotion Case.xlsx, and its model answer is the solution workbook of PartII-case.zip.  The registered notes case2.r1 to
case2.r6 (facts/notes/case2.py) already supply the expected values of the six requirements; these contexts add what the
model paths need beyond them (the queries' row counts, the tie-out by account, the volume test's pitfalls, the model's
columns and data table, the control tests by promotion) and check, with claim(), every table and column the guides name
and every statement about the data that another dataset could falsify.

Keys: case2.chapter (the case note) and case2.g1 to case2.g6 (the six requirements, each used next to the note
case2.r1 to case2.r6).
"""

from __future__ import annotations

import re
import statistics as st
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, rows_of, schema

REPO = Path(__file__).resolve().parents[3]
CASE = REPO / "cases" / "part-2-case.qmd"
DECK = REPO / "slides" / "case-part-2" / "index.qmd"
DOWNLOADS = REPO / "front-matter" / "downloads.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
KIND = {"Collection": "collection", "ItemGroup": "item group", "Segment": "segment"}
CAL_MONTHS = {"Collection": [3, 4], "ItemGroup": [9, 10], "Segment": [11]}     # the months each kind of promotion ran in
RATES = [0.05, 0.08, 0.10, 0.12]                     # the data table's discount rates (Requirement 4)
LIFTS = [round(i * 0.05, 2) for i in range(9)]       # its volume increases, 0 to 40 percent in steps of 5 points

CASE_SCHEMA = {
    "PromotionProgram": ["PromotionID", "PromotionCode", "PromotionName", "ScopeType", "CustomerSegment", "ItemGroup",
                         "CollectionName", "DiscountPct", "EffectiveStartDate", "EffectiveEndDate", "ApprovedByEmployeeID",
                         "ApprovedDate"],
    "SalesOrder": ["SalesOrderID", "OrderNumber", "OrderDate", "CustomerID", "OrderTotal"],
    "SalesOrderLine": ["SalesOrderLineID", "SalesOrderID", "ItemID", "Quantity", "BaseListPrice", "UnitPrice", "Discount",
                       "LineTotal", "PromotionID", "PriceOverrideApprovalID"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "FreightAmount"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "SalesOrderLineID", "ItemID", "Quantity", "BaseListPrice",
                         "UnitPrice", "Discount", "LineTotal", "PromotionID"],
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "StandardCost", "ListPrice", "StandardFixedOverheadCost",
             "RevenueAccountID", "CollectionName"],
    "Customer": ["CustomerID", "CustomerName", "CustomerSince", "CustomerSegment"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "SourceDocumentID",
                "SourceLineID", "FiscalYear"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"],
    "BudgetLine": ["FiscalYear", "Month", "ItemID", "Quantity", "BudgetAmount", "BudgetCategory", "ApprovedByEmployeeID",
                   "ApprovedDate"],
    "PriceOverrideApproval": ["PriceOverrideApprovalID", "SalesOrderLineID", "RequestedByEmployeeID", "ApprovedByEmployeeID",
                              "Status"],
    "Employee": ["EmployeeID", "EmployeeName", "JobTitle", "CostCenterID"],
}


# --- helpers -------------------------------------------------------------------------------------------------------

def notes_module():
    import notes
    notes.load()
    from notes import case2
    return case2


def months_text(months: list[int]) -> str:
    return and_join(MONTHS[m - 1] for m in months)


def deck_titles() -> list[str]:
    """The slide titles of the case's deck in order, the title slide first."""
    titles = ["(title slide)"]
    for line in DECK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,2} (.+?)\s*(\{[^}]*\})?\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    return titles


def at(titles: list[str], first: str) -> int:
    return next(n for n, t in enumerate(titles, 1) if t.startswith(first))


def span(titles: list[str], first: str, after: str | None = None) -> str:
    """'5 to 6' for the slides from the one titled `first` up to the one before `after`; one number when alone."""
    start = at(titles, first)
    end = (at(titles, after) - 1) if after else start
    return str(start) if end <= start else f"{start} to {end}"


def r4_rows(n: int) -> dict:
    """Row positions on R4 Model of the solution workbook for n promotions (scripts/companion/xlbuild/case2.py)."""
    e9 = 24 + n
    d0 = e9 + 4
    t0 = d0 + 5
    tb = t0 + len(LIFTS) + 1
    g0 = tb + 3
    return dict(rate=d0 + 1, lift=d0 + 2, diff=d0 + 3, top=t0, first=t0 + 1, last=t0 + len(LIFTS), tb=tb, big=g0 + 1,
                disc=g0 + 2, gdiff=g0 + 3, nine=24, nine_last=23 + n)


def r3_rows(n: int) -> dict:
    """Row positions on R3 Volume (cal = first row of the calendar)."""
    cal = 5
    g0 = cal + n + 1
    p0 = g0 + n + 3
    k0 = p0 + n + 3
    return dict(cal=cal, grid_head=g0 + 1, grid=g0 + 2, prior_head=p0 + 1, prior=p0 + 2, cmp_head=k0 + 1, cmp=k0 + 2)


def contribution(m: dict, rate: float, lift: float, c: float) -> float:
    """Units x (1 + lift) x (price x (1 - rate) x (1 - c) - cost): Tutorial 7.3's contribution with the promotion."""
    return m["units"] * (1 + lift) * (m["price"] * (1 - rate) * (1 - c) - m["cost"])


# --- the case note -------------------------------------------------------------------------------------------------------

@context("case2.chapter")
def chapter(d, claim):
    schema(d, claim, CASE_SCHEMA)
    n2 = notes_module()
    titles = deck_titles()
    claim(len(titles) == 33, "the case's deck has 33 slides")
    text = CASE.read_text(encoding="utf-8")
    n_req = len(re.findall(r"^\*\*Requirement \d+:", text, re.M))
    claim(n_req == 6, "the case has six requirements")
    claim("Milestone" not in text, "the case has no milestones")
    claim("PartII-case.zip" in DOWNLOADS.read_text(encoding="utf-8"), "the Downloads page lists the Part II solution, PartII-case.zip")
    rows = rows_of(d, ["SalesOrderLine", "SalesInvoiceLine", "GLEntry", "SalesOrder", "Customer", "BudgetLine"])
    promos = []
    for p in n2.promotions(d):
        name = d.one("SELECT PromotionName FROM PromotionProgram WHERE PromotionID = ?", p["id"])
        promos.append(dict(id=p["id"], name=name, kind=KIND[p["scope"]], label=p["label"], rate=p["rate"], start=p["start"],
                           end=p["end"], first=p["lo"], last=p["hi"], lines=p["lines"], year=p["year"],
                           ran=months_text(p["months"])))
    n2.calendar_claims(d, claim)
    proposal = [dict(name=d.one("SELECT PromotionName FROM PromotionProgram WHERE PromotionID = ?", p["id"]), id=p["id"],
                     rate=p["rate"], ran=months_text(CAL_MONTHS[s])) for s, p in n2.proposal(d).items()]
    claim(len(proposal) == 3, "the proposal repeats three promotions")
    claim(len(promos) == 9 and len(d.years) == 3, "the case's data holds nine promotions in three fiscal years")
    _, quarters, total = n2.proposal_quarters(d)
    ordered = d.one("SELECT COUNT(DISTINCT CustomerID) FROM SalesOrder")
    return dict(
        n_req=n_req, slides=len(titles), rows=rows, promos=promos, n_promo=len(promos), proposal=proposal,
        first_year=d.F, report_year=d.C, plan_year=d.N, years=d.years, cost=total, customers_ordered=ordered,
        slide=dict(intro=at(titles, "In this case"), decision=at(titles, "Should Charles River"),
                   kickoff=span(titles, "Should Charles River", "The Situation"),
                   handin=at(titles, "What you will hand in"),
                   criteria=span(titles, "How your work will be judged", "The Situation"),
                   situation=span(titles, "Three promotions a year", "The Data You Will Use"),
                   arguments=at(titles, "The sales team's two arguments"), questions=at(titles, "Four questions"),
                   data=span(titles, "A new workbook for the case", "Requirements"),
                   queries=at(titles, "The queries the case builds"), watch=at(titles, "Watch out"),
                   dates_check=at(titles, "Each question has its date") - 1, dates_answer=at(titles, "Each question has its date"),
                   six=at(titles, "Six requirements"), r1=at(titles, "Build and validate"),
                   r2=at(titles, "Measure what the promotions cost"), r3=at(titles, "Test whether the promotions"),
                   r4=at(titles, "Model the proposed calendar"), lift_check=at(titles, "Each change moves") - 1,
                   lift_answer=at(titles, "Each change moves"), r5=at(titles, "Test the controls"),
                   design_check=at(titles, "Design or operation") - 1, design_answer=at(titles, "Design or operation"),
                   r6=at(titles, "Write the decision memo"), before=at(titles, "Before you submit"),
                   ahead=span(titles, "Looking Ahead", "About these slides")))


# --- requirement 1: the workbook -------------------------------------------------------------------------------------

@context("case2.g1")
def g1(d, claim):
    schema(d, claim, CASE_SCHEMA)
    n2 = notes_module()
    first_order = d.one("SELECT MIN(SalesOrderLineID) FROM SalesOrderLine WHERE PromotionID IS NOT NULL")
    first_billed = d.one("SELECT MIN(SalesInvoiceLineID) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL")
    clean = d.one("SELECT COUNT(*) FROM (SELECT Discount, PromotionID FROM SalesOrderLine ORDER BY SalesOrderLineID LIMIT 200) "
                  "WHERE Discount <> 0 OR PromotionID IS NOT NULL") + d.one(
        "SELECT COUNT(*) FROM (SELECT Discount, PromotionID FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT 200) "
        "WHERE Discount <> 0 OR PromotionID IS NOT NULL")
    claim(clean == 0 and min(first_order, first_billed) > 200,
          "none of the first 200 order lines or invoice lines carries a discount or a promotion (the type trap)")
    rates = [r[0] for r in d.q("SELECT DISTINCT Discount FROM SalesOrderLine ORDER BY 1")]
    promo_rates = sorted({r[0] for r in d.q("SELECT DISTINCT DiscountPct FROM PromotionProgram")} | {0})
    claim(rates == promo_rates, "the discount rates on the order lines are zero and the promotions' DiscountPct")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NULL AND Discount <> 0") == 0,
          "no invoice line without a PromotionID carries a discount")
    tables = [("Promotions", "T7_PromotionProgram", "PromotionProgram"), ("Orders", "T9_SalesOrder", "SalesOrder"),
              ("Items", "T44_Item", "Item"), ("Customers", "T4_Customer", "Customer"),
              ("OrderLines", "T10_SalesOrderLine", "SalesOrderLine"),
              ("BilledLines", "T17_SalesInvoiceLine", "SalesInvoiceLine"), ("Accounts", "T1_Account", "Account"),
              ("Overrides", "T8_PriceOverrideApproval", "PriceOverrideApproval"), ("Employees", "T74_Employee", "Employee")]
    sources = [dict(query=q, table=t, rows=d.one(f"SELECT COUNT(*) FROM {s}")) for q, t, s in tables]
    accounts = d.q("SELECT DISTINCT a.AccountNumber, a.AccountName FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                   "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.FiscalYear = ? ORDER BY 1", d.C)
    claim(any(str(n) == "4050" for n, _ in accounts) and any(str(n) == "2050" for n, _ in accounts),
          "the sales invoices post freight revenue (4050) and sales tax (2050) as well as the item revenue accounts")
    debits = d.one("SELECT SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ?", d.C)
    credits = d.one("SELECT SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ?", d.C)
    claim(abs(debits - credits) < 0.005, "each sales invoice posts in balance, so the filtered postings' debits equal their credits")
    promo_lines = d.one("SELECT COUNT(*) FROM SalesOrderLine WHERE PromotionID IS NOT NULL")
    total_lines = d.one("SELECT COUNT(*) FROM SalesOrderLine")
    comm = d.q("SELECT DISTINCT VoucherNumber FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'JournalEntry'",
               d.account("6290"), d.C)
    claim(len(comm) == 1, "one journal entry posts to the commission account in the year (the year-end close)")
    return dict(
        first_order=first_order, first_billed=first_billed, sources=sources, n_sources=len(sources),
        gl_rows=d.one("SELECT COUNT(*) FROM GLEntry"), budget_all=d.one("SELECT COUNT(*) FROM BudgetLine"),
        posting_accounts=[dict(number=n, name=a) for n, a in accounts], n_posting_accounts=len(accounts),
        credits=credits, rate_list=", ".join(f"{r:g}" for r in rates), non_promo=total_lines - promo_lines,
        year=d.C, first_year=d.F, plan_year=d.N,
        non_promo_billed=d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NULL"))


# --- requirement 2: the cost and the ledger -------------------------------------------------------------------------

@context("case2.g2")
def g2(d, claim):
    n2 = notes_module()
    groups = d.q("SELECT it.ItemGroup, a.AccountNumber, a.AccountName FROM Item it JOIN Account a ON a.AccountID = it.RevenueAccountID "
                 "WHERE it.ItemGroup IN (SELECT ItemGroup FROM Item) GROUP BY 1, 2, 3 ORDER BY 2")
    claim(len({g for g, _, _ in groups}) == len(groups), "each item group posts its revenue to one account")
    tie = []
    for group, number, name in groups:
        credit = d.one("SELECT COALESCE(SUM(g.Credit), 0) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                       "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.FiscalYear = ? AND g.SourceLineID IS NOT NULL "
                       "AND a.AccountNumber = ?", d.C, number)
        net = d.one(f"SELECT COALESCE(SUM(l.LineTotal), 0) {n2.BILLED} JOIN Item it ON it.ItemID = l.ItemID "
                    f"WHERE it.ItemGroup = ? AND substr(i.InvoiceDate, 1, 4) = ?", group, str(d.C))
        tie.append(dict(group=group, number=number, name=name, credit=credit, net=net, diff=credit - net))
    claim(len(tie) == 5, "five item groups post to five revenue accounts")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", d.account("4070")) == 0,
          "the discount account (4070) has no postings in any year")
    freight = d.one("SELECT COALESCE(SUM(Credit), 0) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'SalesInvoice' "
                    "AND FiscalYear = ?", d.account("4050"), d.C)
    net_all = sum(t["net"] for t in tie)
    with_freight = sum(t["credit"] for t in tie) + freight - net_all
    services = d.q(f"SELECT SUM(l.Quantity * l.BaseListPrice - l.Quantity * l.UnitPrice), SUM(l.Quantity * l.UnitPrice * l.Discount) "
                   f"{n2.BILLED} JOIN Item it ON it.ItemID = l.ItemID WHERE it.ItemGroup = 'Services' AND substr(i.InvoiceDate, 1, 4) = ?",
                   str(d.C))[0]
    claim(abs(services[0] or 0) < 0.005 and abs(services[1] or 0) < 0.005,
          "the design services carry no price-list reduction and no promotional discount")
    ordered = {}
    for p in n2.proposal(d).values():
        for q, v in d.q(f"SELECT (CAST(substr(o.OrderDate, 6, 2) AS INTEGER) + 2) / 3, SUM(l.Quantity * l.UnitPrice * l.Discount) "
                        f"{n2.ORDERS} WHERE l.PromotionID = ? GROUP BY 1", p["id"]):
            ordered[q] = ordered.get(q, 0.0) + v
    _, quarters, total = n2.proposal_quarters(d)
    q4_invoiced = dict(quarters).get(4, 0.0) / total
    q4_ordered = ordered.get(4, 0.0) / sum(ordered.values())
    claim(q4_ordered < q4_invoiced, "by order date a smaller share of the proposal's discount falls in the fourth quarter than by invoice date")
    promo_billed = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL")
    after = {p["id"]: d.one(f"SELECT COUNT(*) {n2.BILLED} WHERE l.PromotionID = ? AND i.InvoiceDate > ?", p["id"], p["end"])
             for p in n2.proposal(d).values()}
    fall = n2.proposal(d)["ItemGroup"]
    spill = [q["id"] for q in n2.promotions(d) if d.one(
        f"SELECT COUNT(*) {n2.BILLED} WHERE l.PromotionID = ? AND substr(i.InvoiceDate, 1, 4) > ?", q["id"], str(q["year"])) > 0]
    claim(len(spill) > 0 and all(q["year"] < d.C for q in n2.promotions(d) if q["id"] in spill),
          "some promotions of the earlier years were also billed in the year after they ran")
    quarter_rows = []
    for p in n2.proposal(d).values():
        got = dict(d.q(f"SELECT (CAST(substr(i.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3, SUM(l.Quantity * l.UnitPrice * l.Discount) "
                       f"{n2.BILLED} WHERE l.PromotionID = ? AND substr(i.InvoiceDate, 1, 4) = ? GROUP BY 1", p["id"], str(d.C)))
        quarter_rows.append(dict(id=p["id"], label=p["label"], name=d.one("SELECT PromotionName FROM PromotionProgram WHERE PromotionID = ?", p["id"]),
                                 q=[got.get(k, 0.0) for k in (1, 2, 3, 4)]))
    return dict(tie=tie, spill=n2.series(spill), quarter_rows=quarter_rows, with_freight=with_freight, freight=freight, q4_ordered=q4_ordered, q4_invoiced=q4_invoiced,
                billed_lines=d.one("SELECT COUNT(*) FROM SalesInvoiceLine"),
                pivot_total=d.one("SELECT SUM(Quantity * UnitPrice * Discount) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL"),
                freight_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 4050"),
                tax_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 2050"),
                blank_billed=d.one("SELECT COUNT(*) FROM SalesInvoiceLine") - promo_billed, promo_billed=promo_billed,
                fall_after=after[fall["id"]], fall_label=fall["label"], year=d.C, first_year=d.F, prior_year=d.P,
                discount_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 4070"),
                discount_name=d.one("SELECT AccountName FROM Account WHERE AccountNumber = 4070"),
                returns_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 4060"),
                returns_name=d.one("SELECT AccountName FROM Account WHERE AccountNumber = 4060"))


# --- requirement 3: did the promotions bring in sales ---------------------------------------------------------------

@context("case2.g3")
def g3(d, claim):
    n2 = notes_module()
    vol = n2.volume(d)
    be = n2.breakevens(d)
    rows = []
    naive = []
    for p, v in zip(n2.promotions(d), vol):
        by_month = {(int(y), int(m)): (lst, net) for y, m, lst, net in d.q(
            f"SELECT substr(o.OrderDate, 1, 4), substr(o.OrderDate, 6, 2), SUM(l.Quantity * l.BaseListPrice), SUM(l.LineTotal) "
            f"{n2.ORDERS} WHERE {n2.SCOPE_SQL[p['scope']]} = ? GROUP BY 1, 2", p["label"])}
        y, months = p["year"], p["months"]
        other = [by_month.get((y, m), (0.0, 0.0)) for m in range(1, 13) if m not in months]
        window = [by_month.get((y, m), (0.0, 0.0)) for m in months]
        list_sd = st.stdev([o[0] for o in other])
        list_gap = sum(w[0] for w in window) - st.mean([o[0] for o in other]) * len(months)
        net_lift = sum(w[1] for w in window) / (st.mean([o[1] for o in other]) * len(months)) - 1
        z1 = list_gap / list_sd
        if abs(z1) >= 2:
            naive.append(p["id"])
        rows.append(dict(id=p["id"], label=p["label"], kind=KIND[p["scope"]], ran=months_text(months), n_months=len(months),
                         lift=v["lift"], sd=v["sd"], py=v["py"], z=v["z"], net_lift=net_lift, naive_z=z1,
                         be=be[p["id"]], lines=p["lines"], recorded_start=p["start"], recorded_end=p["end"],
                         first=p["lo"], last=p["hi"]))
    bad = [p for p in n2.promotions(d) if d.one(f"SELECT COUNT(*) {n2.ORDERS} WHERE l.PromotionID = ? AND o.OrderDate BETWEEN ? AND ?",
                                              p["id"], p["start"], p["end"]) < p["lines"]]
    claim(len(bad) > 0 and all(d.one(f"SELECT COUNT(*) {n2.ORDERS} WHERE l.PromotionID = ? AND o.OrderDate BETWEEN ? AND ?",
                                     p["id"], p["start"], p["end"]) == 0 for p in bad),
          "the promotions whose recorded dates fail contain none of their lines")
    claim(all(abs(r["z"]) < 2 for r in rows), "no promotion's difference is beyond two standard deviations of its months' total")
    claim(len(naive) == 1, "read against one month's standard deviation, exactly one promotion would look unusual")
    claim(sum(1 for r in rows if r["net_lift"] > 0) <= 1, "at net amounts at most one promotion shows a difference above zero")
    no_py = [r["id"] for r in rows if r["py"] is None]
    claim(all(p["year"] == d.F for p in n2.promotions(d) if p["id"] in no_py), "the promotions with no earlier year are those of the first year")
    first = d.q("WITH f AS (SELECT CustomerID, MIN(OrderDate) AS d FROM SalesOrder GROUP BY 1) SELECT d FROM f ORDER BY d")
    early = sum(1 for (x,) in first if x <= f"{d.F}-04-30")
    in_jan = sum(1 for (x,) in first if x.startswith(f"{d.F}-01"))
    never = d.one("SELECT COUNT(*) FROM Customer WHERE CustomerID NOT IN (SELECT CustomerID FROM SalesOrder)")
    claim(d.one("SELECT COUNT(*) FROM Customer WHERE CustomerID NOT IN (SELECT CustomerID FROM SalesOrder) AND IsActive = 1") == 0,
          "every customer without an order is inactive")
    return dict(rows=rows, n_rows=len(rows), naive_flagged=n2.series(naive), no_py=n2.series(no_py), first_year=d.F,
                net_low=min(r["net_lift"] for r in rows), net_high=max(r["net_lift"] for r in rows),
                n_net_up=sum(1 for r in rows if r["net_lift"] > 0), early=early, jan=in_jan, never=never,
                cmp=r3_rows(len(rows)), lift_low=min(r["lift"] for r in rows), lift_high=max(r["lift"] for r in rows))


# --- requirement 4: the model ----------------------------------------------------------------------------------------

@context("case2.g4")
def g4(d, claim):
    n2 = notes_module()
    c = n2.commission(d)[2]
    prop = n2.proposal(d)
    cols = []
    for scope in ("Collection", "ItemGroup", "Segment"):
        p = prop[scope]
        m = n2.unit_model(d, p["id"], d.C)
        without = m["units"] * (m["price"] * (1 - c) - m["cost"])
        with0 = contribution(m, p["rate"], 0.0, c)
        discount = m["units"] * m["price"] * p["rate"]
        net_price = d.one(f"SELECT SUM(l.LineTotal) / SUM(l.Quantity) {n2.BILLED} WHERE l.PromotionID = ? AND substr(i.InvoiceDate, 1, 4) = ?",
                          p["id"], str(d.C))
        cols.append(dict(
            scope=scope, id=p["id"], label=p["label"], rate=p["rate"], units=m["units"], price=m["price"], cost=m["cost"],
            fixed=m["fixed"], without=without, with0=with0, diff=with0 - without, discount=discount,
            given_up=discount * (1 - c), be=n2.breakeven(m["price"], m["cost"], p["rate"], c),
            be_fixed=n2.breakeven(m["price"], m["cost"] - m["fixed"], p["rate"], c),
            be_net_price=n2.breakeven(net_price, m["cost"], p["rate"], c)))
    fur = next(x for x in cols if x["scope"] == "ItemGroup")
    be = n2.breakevens(d)
    vol = {v["id"]: v for v in n2.volume(d)}
    nine = []
    for p in n2.promotions(d):
        m = n2.unit_model(d, p["id"])
        nine.append(dict(id=p["id"], label=p["label"], rate=p["rate"], units=m["units"], price=m["price"], cost=m["cost"],
                         be=be[p["id"]], lift=vol[p["id"]]["lift"], share=vol[p["id"]]["lift"] / be[p["id"]]))
    claim(max(x["share"] for x in nine) < 0.5, "no promotion's measured difference reached half of its break-even increase")
    best = max(nine, key=lambda x: x["lift"])
    # the data table: the Furniture promotion's difference at each rate and volume increase
    base = fur["without"]
    first_positive = {}
    for rate in RATES:
        pos = [lift for lift in LIFTS if contribution(fur_model(fur), rate, lift, c) - base > 0]
        first_positive[rate] = pos[0] if pos else None
    claim(first_positive[0.10] == 0.35, "at a 10 percent discount the Furniture promotion turns positive between a 30 and a 35 percent increase")
    claim(all(v is not None for v in first_positive.values()), "every discount rate in the data table turns positive by a 40 percent increase")
    swap = contribution(fur_model(fur), 0.0, 0.05, c) - base       # a data table with its two input cells swapped, at 5 percent and 0
    corner = contribution(fur_model(fur), 0.05, 0.0, c) - base
    # how the budgets planned the promoted items, by promotion year
    promoted = []
    for p in n2.promotions(d):
        if p["scope"] not in ("Collection", "ItemGroup"):
            continue
        column = "i.CollectionName" if p["scope"] == "Collection" else "i.ItemGroup"
        months = ",".join(str(m) for m in n2.CALENDAR[p["scope"]])
        a, b = n2.budget_ratio(d, f"b.FiscalYear = ? AND {column} = ? AND b.Month IN ({months})", p["year"], p["label"])
        a2, b2 = n2.budget_ratio(d, f"b.FiscalYear = ? AND {column} = ? AND b.Month NOT IN ({months})", p["year"], p["label"])
        promoted.append(dict(id=p["id"], label=p["label"], year=p["year"], ratio=a / b, other=a2 / b2))
    claim(all(x["other"] > x["ratio"] + 0.02 for x in promoted), "the promoted items are budgeted lower in their promotion months than in the others")
    plan_months = [r for _, r in d.q(f"SELECT b.Month, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) {n2.BUDGET} "
                                     f"AND b.FiscalYear = ? GROUP BY 1", d.N)]
    plan_all = n2.budget_ratio(d, "b.FiscalYear = ?", d.N)
    plan_all = plan_all[0] / plan_all[1]
    whole = dict(d.q(f"SELECT b.Month, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) {n2.BUDGET} "
                     f"AND b.FiscalYear = ? GROUP BY 1", d.C))
    claim(len(whole) == 12 and whole[3] < whole[1] and abs(whole[3] - whole[1]) < 0.01,
          "the whole budget's ratio in the collection months is only a few thousandths below January's")
    year_ratio = {y: (lambda ab: ab[0] / ab[1])(n2.budget_ratio(d, "b.FiscalYear = ?", y)) for y in d.years}
    _, quarters, total = n2.proposal_quarters(d)
    fall = prop["ItemGroup"]
    months = ",".join(str(m) for m in fall["months"])
    budget_units = d.one(f"SELECT SUM(b.Quantity) {n2.BUDGET} AND b.FiscalYear = ? AND i.ItemGroup = ? AND b.Month IN ({months})",
                         d.N, fall["label"])
    ordered = d.one(f"SELECT SUM(l.Quantity) {n2.ORDERS} WHERE i.ItemGroup = ? AND o.OrderDate BETWEEN ? AND ?",
                    fall["label"], f"{d.C}-{fall['months'][0]:02d}-01", f"{d.C}-{fall['months'][-1]:02d}-31")
    claim(budget_units / ordered > 3, "the budget plans more than three times the units ordered in the fall promotion's months")
    cfo_name = d.one("SELECT EmployeeName FROM Employee WHERE EmployeeID = (SELECT DISTINCT ApprovedByEmployeeID FROM BudgetLine WHERE FiscalYear = ?)", d.N)
    return dict(
        cols=cols, nine=nine, c=c, fur=fur, best=best, positives=[dict(rate=r, lift=v) for r, v in first_positive.items()],
        swap=swap, corner=corner, whole_march=whole[3], whole_jan=whole[1],
        promoted=promoted, promoted_low=min(x["other"] for x in promoted), promoted_high=max(x["other"] for x in promoted),
        plan_dev=max(abs(r - plan_all) for r in plan_months), plan_all=plan_all,
        year_ratios=[dict(year=y, ratio=r) for y, r in year_ratio.items()],
        quarters=[(q, v) for q, v in quarters], total=total, rows=r4_rows(len(nine)), cfo_name=cfo_name,
        budget_units=budget_units, ordered=ordered, budget_over=budget_units / ordered,
        year=d.C, plan_year=d.N, first_year=d.F)


def fur_model(fur: dict) -> dict:
    return dict(units=fur["units"], price=fur["price"], cost=fur["cost"])


# --- requirement 5: the controls ---------------------------------------------------------------------------------------

@context("case2.g5")
def g5(d, claim):
    n2 = notes_module()
    promos = n2.promotions(d)
    tests = []
    evidence = []
    for p in promos:
        within = d.one(f"SELECT COUNT(*) {n2.ORDERS} WHERE l.PromotionID = ? AND o.OrderDate BETWEEN ? AND ?", p["id"], p["start"], p["end"])
        out_scope = d.one(f"SELECT COUNT(*) {n2.ORDERS} JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                          f"WHERE l.PromotionID = ? AND NOT {n2.IN_SCOPE}", p["id"])
        bad_rate = d.one(f"SELECT COUNT(*) {n2.ORDERS} JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                         f"WHERE l.PromotionID = ? AND ABS(l.Discount - p.DiscountPct) > 1e-9", p["id"])
        fails = within < p["lines"]
        if fails:
            start, end = f"{p['year']}-{p['months'][0]:02d}-01", f"{p['year']}-{p['months'][-1]:02d}-31"
        else:
            start, end = p["start"], p["end"]
        col = n2.SCOPE_SQL[p["scope"]]
        missing = d.one(f"SELECT COUNT(*) {n2.ORDERS} WHERE {col} = ? AND o.OrderDate BETWEEN ? AND ? AND (l.PromotionID IS NULL OR l.PromotionID <> ?)",
                        p["label"], start, end, p["id"])
        recorded = d.one(f"SELECT COUNT(*) {n2.ORDERS} WHERE {col} = ? AND o.OrderDate BETWEEN ? AND ?", p["label"], p["start"], p["end"])
        tests.append(dict(id=p["id"], name=d.one("SELECT PromotionName FROM PromotionProgram WHERE PromotionID = ?", p["id"]),
                          kind=KIND[p["scope"]], label=p["label"], lines=p["lines"], out_dates=p["lines"] - within,
                          out_scope=out_scope, bad_rate=bad_rate, missing=missing, window=(start, end), fails=fails,
                          recorded_in_scope=recorded))
        if fails:
            ratios = n2.monthly_ratios(d, p["year"], "i.CollectionName", p["label"])
            evidence.append(dict(id=p["id"], label=p["label"], year=p["year"], start=p["start"], end=p["end"], first=p["lo"],
                                 last=p["hi"], ran=months_text(p["months"]), lines=p["lines"],
                                 high=max(ratios[m] for m in p["months"]), low=min(ratios[m] for m in n2.PLAIN_MONTHS)))
    failing = [t for t in tests if t["fails"]]
    claim(all(t["recorded_in_scope"] == 0 for t in failing),
          "no in-scope line of a failing promotion was ordered inside its recorded dates, so a completeness test on those dates passes with nothing to test")
    claim(all(t["bad_rate"] == 0 for t in tests) and all(t["missing"] == 0 for t in tests),
          "no promotion line carries another rate, and none in scope and window lacks the promotion")
    claim(all(t["kind"] == "collection" for t in failing), "the promotions that fail the date test are the collection promotions")
    collection_lines = sum(t["lines"] for t in tests if t["kind"] == "collection")
    claim(collection_lines == sum(t["lines"] for t in failing), "the collection promotions' lines are the failing promotions' lines")
    claim(all(p["end"] <= p["start"] for p in promos if p["id"] in {f["id"] for f in failing}),
          "the failing promotions' recorded end dates are on or before their start dates")
    claim(d.one("SELECT COUNT(DISTINCT ApprovedByEmployeeID) FROM PromotionProgram") == 1
          and d.one("SELECT COUNT(DISTINCT ApprovedByEmployeeID) FROM PriceOverrideApproval WHERE Status = 'Approved'") == 1
          and d.one("SELECT DISTINCT ApprovedByEmployeeID FROM PromotionProgram")
          == d.one("SELECT DISTINCT ApprovedByEmployeeID FROM PriceOverrideApproval WHERE Status = 'Approved'"),
          "one employee approved every promotion and every approved override")
    non_promo = d.one("SELECT COUNT(*) FROM SalesOrderLine WHERE PromotionID IS NULL")
    items = d.q("SELECT i.ItemCode, i.ItemName, i.ItemGroup, (SELECT COUNT(*) FROM SalesOrderLine l WHERE l.ItemID = i.ItemID) FROM Item i "
                "WHERE i.CollectionName IS NULL AND i.ItemGroup IN (SELECT ItemGroup FROM Item WHERE CollectionName IS NOT NULL) "
                "ORDER BY i.ItemID")
    names = {r[0] for r in d.q("SELECT DISTINCT CollectionName FROM Item WHERE CollectionName IS NOT NULL")}
    claim(all(r[1].split()[0] in names for r in items), "every item with no collection is named for a collection")
    blank = [dict(code=r[0], word=r[1].split()[0], lines=r[3]) for r in items]
    pending = d.q("SELECT PriceOverrideApprovalID FROM PriceOverrideApproval WHERE Status = 'Pending' ORDER BY 1")
    mgr = d.one("SELECT DISTINCT ApprovedByEmployeeID FROM PromotionProgram")
    return dict(tests=tests, evidence=evidence, collection_lines=collection_lines, non_promo=non_promo,
                unguarded=non_promo + sum(t["out_dates"] for t in tests), blank=blank, n_blank=len(blank),
                total_lines=sum(t["lines"] for t in tests), n_failing=len(failing), failing_ids=n2.series(t["id"] for t in failing),
                overrides=d.one("SELECT COUNT(*) FROM PriceOverrideApproval"),                 approver_id=mgr, n_pending=len(pending), plan_year=d.N,
                other_kinds=sum(t["lines"] for t in tests if t["kind"] != "item group"))


# --- requirement 6: the memo ---------------------------------------------------------------------------------------------

@context("case2.g6")
def g6(d, claim):
    n2 = notes_module()
    prop = n2.proposal(d)
    c = n2.commission(d)[2]
    _, quarters, total = n2.proposal_quarters(d)
    best, discount = n2.goal_seek(d)
    be = n2.breakevens(d)
    vol = n2.volume(d)
    claim(all(v["lift"] < be[v["id"]] for v in vol), "no promotion reached its break-even increase")
    proposal = []
    for scope in ("Collection", "ItemGroup", "Segment"):
        p = prop[scope]
        proposal.append(dict(id=p["id"], label=p["label"], rate=p["rate"], be=be[p["id"]], ran=months_text(CAL_MONTHS[scope])))
    return dict(proposal=proposal, total=total, given_up=total * (1 - c), discount=discount, best=best,
                discount_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 4070"),
                q4_share=dict(quarters).get(4, 0.0) / total, year=d.C, plan_year=d.N, first_year=d.F,
                lift_low=min(v["lift"] for v in vol), lift_high=max(v["lift"] for v in vol),
                be_low=min(be.values()), be_high=max(be.values()))
