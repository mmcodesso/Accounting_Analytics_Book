"""Chapter 13's instructor notes: the values each note states, and the claims its wording makes.

The Power BI values of the chapter come from the model of Tutorial 13.1: the four Tables (Item filtered to the items
with a list price), FiscalYear = the year of InvoiceDate, Month = its year and month, and the unrounded custom columns
ListAmount = Quantity x BaseListPrice and DiscountAmount = Quantity x UnitPrice x Discount. The SQL here is their twin.
Power Query's profile reads the Tables in the workbook's order, which is the order of the primary key.

Two notes are not registered, because their comments state a value the data do not give; each context function
renders the corrected text, so register it once the comment is fixed:
- t2 gives Design Trade's December 2026 discounts as 8,692.03; the line chart sums the unrounded DiscountAmount,
  8,692.035176, which shows as 8,692.04 (8,692.03 is the sum of the rounded parts by promotion, 2,116.66 + 6,575.37);
- t3 gives October 2026 revenue as 2,297,493.18; the October lines (and the invoices' SubTotal) total 2,297,493.38.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from notes import note

EXERCISES = "chapters/13-power-bi-essentials/_exercises.qmd"
T1 = "chapters/13-power-bi-essentials/_tutorial-01.qmd"
T2 = "chapters/13-power-bi-essentials/_tutorial-02.qmd"
T3 = "chapters/13-power-bi-essentials/_tutorial-03.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
ORDINALS = ["zeroth", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
            "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth",
            "nineteenth", "twentieth"]
TOP_ROWS = 1000          # Power Query profiles the top 1,000 rows by default (a software constant)
TOP_N = 10               # Exercise 13.2's Top N filter
POLICY = 0.05            # Exercise 13.2's concentration policy
TRACED_SALE_ID = 7947    # the book's traced sale (Tutorial 3.2, Chapter 10); its number is queried


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def ordinal(n: int) -> str:
    if n < len(ORDINALS):
        return ORDINALS[n]
    suffix = "th" if 10 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def rate(x: float) -> str:
    """A Discount value as the notes write it: 0, 0.08, 0.10, 0.12."""
    return "0" if x == 0 else f"{x:.2f}"


def lines(d) -> list[dict]:
    """The invoice lines with what Tutorial 13.1's model relates to them (every line finds its invoice, item, and
    customer; the checks are t1's claims)."""
    rows = d.q("SELECT l.SalesInvoiceLineID, l.SalesInvoiceID, si.InvoiceDate, i.ItemGroup, substr(i.ItemCode, 5, 3), "
               "c.CustomerID, c.CustomerName, c.CustomerSegment, c.Region, l.LineTotal, l.Quantity * l.BaseListPrice, "
               "l.Quantity * l.UnitPrice * l.Discount, l.Quantity * l.UnitPrice, l.Discount, l.PromotionID "
               "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
               "JOIN Item i ON i.ItemID = l.ItemID JOIN Customer c ON c.CustomerID = si.CustomerID "
               "ORDER BY l.SalesInvoiceLineID")
    return [dict(id=r[0], inv=r[1], date=r[2], year=int(r[2][:4]), month=r[2][:7], m=int(r[2][5:7]),
                 quarter=(int(r[2][5:7]) + 2) // 3, group=r[3], ptype=r[4], customer=r[5], name=r[6], segment=r[7],
                 region=r[8], rev=r[9], list=r[10], disc=r[11], price=r[12], rate=r[13], promo=r[14]) for r in rows]


def total(rows, field: str) -> float:
    return sum(r[field] for r in rows)


def promotions(d) -> dict[int, dict]:
    return {r[0]: dict(id=r[0], name=r[1], scope=r[2], group=r[3], segment=r[4], collection=r[5], start=r[6], end=r[7])
            for r in d.q("SELECT PromotionID, PromotionName, ScopeType, ItemGroup, CustomerSegment, CollectionName, "
                         "EffectiveStartDate, EffectiveEndDate FROM PromotionProgram ORDER BY PromotionID")}


def autumn_promotion(d) -> dict:
    """The current year's item-group promotion of Furniture (the Furniture Seasonal Promotion of Chapter 6)."""
    found = [p for p in promotions(d).values() if p["scope"] == "ItemGroup" and p["group"] == "Furniture"
             and p["start"][:4] == str(d.C)]
    if len(found) != 1:
        raise LookupError(f"no single Furniture item-group promotion in {d.C}")
    return found[0]


def segment_promotion(d, segment: str) -> dict:
    found = [p for p in promotions(d).values() if p["scope"] == "Segment" and p["segment"] == segment
             and p["start"][:4] == str(d.C)]
    if len(found) != 1:
        raise LookupError(f"no single {segment} segment promotion in {d.C}")
    return found[0]


def monthly_revenue(rows) -> dict[str, float]:
    by = defaultdict(float)
    for r in rows:
        by[r["month"]] += r["rev"]
    return dict(sorted(by.items()))


def month_name(month: str) -> str:
    return MONTHS[int(month[5:7]) - 1]


# --- Tutorial 13.1 -------------------------------------------------------------------------------

@note("ch13.t1", T1)
def t1(d, claim):
    all_lines = lines(d)
    n_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    claim(len(all_lines) == n_lines, "every line finds its invoice, item, and customer")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID WHERE i.ListPrice IS NULL") == 0,
          "no invoice line refers to an item with a blank ListPrice (so no (Blank) item group)")
    years = []
    for y in d.years:
        rows = [r for r in all_lines if r["year"] == y]
        years.append(dict(year=y, n=len(rows), rev=total(rows, "rev"), list=total(rows, "list"), disc=total(rows, "disc")))
    claim(sum(y["n"] for y in years) == n_lines, "every invoice line is dated in a fiscal year of the window")
    first = all_lines[:TOP_ROWS]
    discounts_first = sorted({r["rate"] for r in first})
    claim(len(discounts_first) == 1, "the first 1,000 lines have a single Discount value")
    return dict(n_lines=n_lines, n_invoices=d.one("SELECT COUNT(*) FROM SalesInvoice"),
                items=d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL"), items_all=d.one("SELECT COUNT(*) FROM Item"),
                customers=d.one("SELECT COUNT(*) FROM Customer"), years=years, rev=total(all_lines, "rev"),
                first_from=min(r["date"] for r in first), first_to=max(r["date"] for r in first),
                first_empty=sum(r["promo"] is None for r in first) / len(first),
                first_discounts=[rate(x) for x in discounts_first],
                empty=sum(r["promo"] is None for r in all_lines),
                discounts=[rate(x) for x in sorted({r["rate"] for r in all_lines})])


# --- Tutorial 13.2 -------------------------------------------------------------------------------

@note("ch13.t2", "chapters/13-power-bi-essentials/_tutorial-02.qmd")
def t2(d, claim):
    """Tutorial 13.2 (not registered: the comment rounds one value; see the module docstring)."""
    rows = [r for r in lines(d) if r["year"] == d.C]
    furniture = [r for r in rows if r["group"] == "Furniture"]
    autumn = autumn_promotion(d)
    trade = segment_promotion(d, "Design Trade")
    start = int(autumn["start"][5:7])

    def by_month(subset):
        out = defaultdict(float)
        for r in subset:
            out[r["m"]] += r["disc"]
        return out

    months = by_month(rows)
    furniture_months = by_month(furniture)
    groups = defaultdict(float)
    for r in rows:
        groups[r["group"]] += r["disc"]
    design = [r for r in rows if r["segment"] == "Design Trade"]
    design_groups = defaultdict(float)
    for r in design:
        design_groups[r["group"]] += r["disc"]
    design_months = by_month(design)
    trade_month = int(trade["start"][5:7])
    trade_disc = sum(r["disc"] for r in rows if r["promo"] == trade["id"] and r["m"] == trade_month)
    claim(trade["start"][:7] == trade["end"][:7], "the Design Trade promotion runs within one month")
    quarters = defaultdict(float)
    for r in furniture:
        quarters[r["quarter"]] += r["rev"]
    header = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", f"{d.C}-01-01", f"{d.C}-12-31")
    return dict(rev=total(rows, "rev"), list=total(rows, "list"), disc=total(rows, "disc"),
                invoices=len({r["inv"] for r in rows}),
                f_rev=total(furniture, "rev"), f_list=total(furniture, "list"), f_disc=total(furniture, "disc"),
                f_invoices=len({r["inv"] for r in furniture}), header=header,
                months=[(MONTHS[m - 1][:3], months[m]) for m in range(1, 13)],
                f_months=[(MONTHS[m - 1][:3], furniture_months[m]) for m in range(start, 13)],
                groups=sorted(groups.items(), key=lambda kv: -kv[1]),
                d_groups=sorted(design_groups.items(), key=lambda kv: -kv[1]),
                d_months=[(MONTHS[m - 1][:3], design_months[m], trade_disc if m == trade_month else None)
                          for m in range(start, 13)],
                trade=trade["id"], types=sorted({r["ptype"] for r in furniture}),
                quarters=[(q, quarters[q]) for q in range(1, 5)])


# --- Tutorial 13.3 -------------------------------------------------------------------------------

@note("ch13.t3", "chapters/13-power-bi-essentials/_tutorial-03.qmd")
def t3(d, claim):
    """Tutorial 13.3 (not registered: the comment mistypes one value; see the module docstring)."""
    all_lines = lines(d)
    rows = [r for r in all_lines if r["year"] == d.C]
    monthly = monthly_revenue(rows)
    low = min(monthly, key=monthly.get)
    high = max(monthly, key=monthly.get)
    mean = sum(monthly.values()) / len(monthly)
    everything = monthly_revenue(all_lines)
    jan, feb, dec = everything[f"{d.F}-01"], everything[f"{d.F}-02"], everything[f"{d.C}-12"]
    years = [sum(r["rev"] for r in all_lines if r["year"] == y) for y in d.years]
    invoices = dict(d.q("SELECT substr(InvoiceDate, 1, 7), COUNT(*) FROM SalesInvoice GROUP BY 1"))
    start = f"{d.F}-01"
    others = [n for m, n in invoices.items() if m != start]
    claim(invoices[start] < 0.6 * min(others), f"January {d.F} has far fewer invoices than any other month")
    discounts = defaultdict(float)
    for r in rows:
        discounts[r["month"]] += r["disc"]
    shares = sorted(((m, discounts[m] / monthly[m]) for m in monthly), key=lambda kv: -kv[1])
    claim(max(discounts.values()) < min(monthly.values()),
          "the two ranges barely overlap (the largest month's discounts are below the smallest month's revenue)")
    top = shares[0][0]
    return dict(low=monthly[low], low_month=month_name(low), high=monthly[high], high_month=month_name(high), mean=mean,
                range=(monthly[high] - monthly[low]) / mean, jan=jan, feb=feb, dec=dec, from_jan=dec / jan - 1,
                from_feb=dec / feb - 1, years=years, changes=[b / a - 1 for a, b in zip(years, years[1:])],
                jan_invoices=invoices[start], others_low=min(others), others_high=max(others),
                top=dict(month=month_name(top), share=shares[0][1], disc=discounts[top], rev=monthly[top]),
                next=[(month_name(m), s) for m, s in shares[1:3]])


# --- Exercise 13.1 -------------------------------------------------------------------------------

@note("ch13.ex1", EXERCISES)
def ex1(d, claim):
    all_lines = lines(d)
    groups = sorted({r["group"] for r in all_lines})
    years = []
    for y in d.years:
        rows = [r for r in all_lines if r["year"] == y]
        by_group = defaultdict(float)
        for r in rows:
            by_group[r["group"]] += r["rev"]
        n, subtotal, freight, tax, grand = d.q(
            "SELECT COUNT(*), SUM(SubTotal), SUM(FreightAmount), SUM(TaxAmount), SUM(GrandTotal) FROM SalesInvoice "
            "WHERE InvoiceDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")[0]
        claim(abs(subtotal - total(rows, "rev")) < 0.005, f"SubTotal of {y} equals the line totals exactly")
        claim(abs(subtotal + freight + tax - grand) < 0.005, f"GrandTotal of {y} = SubTotal + freight + tax")
        years.append(dict(year=y, groups=[(g, by_group[g]) for g in groups], total=total(rows, "rev"), n=n,
                          freight=freight, tax=tax, grand=grand))
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice si WHERE NOT EXISTS (SELECT 1 FROM SalesInvoiceLine l "
                "WHERE l.SalesInvoiceID = si.SalesInvoiceID)") == 0, "no invoice without lines")
    header = {r[0] for r in d.q("SELECT DISTINCT a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                                "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.SourceLineID IS NULL")}
    claim({str(a) for a in header} == {"1020", "4050", "2050"},
          "the header-level postings of invoices go to receivables, freight revenue (4050), and sales tax (2050)")
    traced = d.one("SELECT InvoiceNumber FROM SalesInvoice WHERE SalesInvoiceID = ?", TRACED_SALE_ID)
    return dict(years=years, traced=traced)


# --- Exercise 13.2 -------------------------------------------------------------------------------

@note("ch13.ex2", EXERCISES)
def ex2(d, claim):
    rows = [r for r in lines(d) if r["year"] == d.C]
    revenue = sum(r["rev"] for r in rows)
    by_key, info = defaultdict(float), {}
    for r in rows:
        by_key[r["customer"]] += r["rev"]
        info[r["customer"]] = (r["name"], r["region"], r["segment"])
    by_name = defaultdict(float)
    for k, v in by_key.items():
        by_name[info[k][0]] += v
    keys = sorted(by_key, key=lambda k: -by_key[k])
    names = sorted(by_name, key=lambda n: -by_name[n])
    key_rank = {k: i for i, k in enumerate(keys, 1)}
    name_rank = {n: i for i, n in enumerate(names, 1)}
    dup = defaultdict(list)
    for cid, name in d.q("SELECT CustomerID, CustomerName FROM Customer ORDER BY CustomerID"):
        dup[name].append(cid)
    dups = {n: ids for n, ids in dup.items() if len(ids) > 1}
    merged = [n for n, ids in dups.items() if sum(i in by_key for i in ids) > 1]
    single = [n for n, ids in dups.items() if sum(i in by_key for i in ids) == 1]
    claim(len(merged) == 1 and len(single) == 1 and len(dups) == 2,
          "two names belong to two customers: one with revenue from both, one with revenue from only one")
    m = merged[0]
    parts = sorted((i for i in dups[m] if i in by_key), key=lambda i: -by_key[i])
    claim(name_rank[m] <= TOP_N, "the merged name enters the top ten by name")
    tenth = keys[TOP_N - 1]
    claim(name_rank[info[tenth][0]] > TOP_N, "the tenth customer by key drops out of the top ten by name")
    s = single[0]
    s_with = [i for i in dups[s] if i in by_key][0]
    largest, second = keys[0], keys[1]
    claim(names[0] == info[largest][0], "the largest customer is the same by key and by name")
    claim(by_key[largest] / revenue < POLICY / 2, "no customer approaches the 5% policy (the largest holds under half of it)")
    return dict(customers=len(by_key), names=len(by_name),
                merged=dict(name=m, rank=ordinal(name_rank[m]), amount=by_name[m], n=word(len(parts)),
                            parts=[dict(id=i, region=info[i][1], segment=info[i][2], amount=by_key[i],
                                        rank=ordinal(key_rank[i])) for i in parts]),
                tenth=dict(name=info[tenth][0], id=tenth, amount=by_key[tenth], rank=ordinal(name_rank[info[tenth][0]])),
                single=dict(name=s, ids=dups[s], n=word(len(dups[s])), id=s_with, amount=by_key[s_with]),
                largest=dict(name=info[largest][0], id=largest, amount=by_key[largest], share=by_key[largest] / revenue),
                second=dict(name=info[second][0], share=by_key[second] / revenue),
                top_key=sum(by_key[k] for k in keys[:TOP_N]) / revenue,
                top_name=sum(by_name[n] for n in names[:TOP_N]) / revenue)


# --- Exercise 13.3 -------------------------------------------------------------------------------

@note("ch13.ex3", EXERCISES)
def ex3(d, claim):
    promos = promotions(d)
    rows = [r for r in lines(d) if r["year"] == d.C]
    with_promo = [r for r in rows if r["promo"] is not None]
    ordered = dict(d.q("SELECT l.SalesInvoiceLineID, o.OrderDate FROM SalesInvoiceLine l JOIN SalesInvoice si "
                       "ON si.SalesInvoiceID = l.SalesInvoiceID JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID "
                       "WHERE l.PromotionID IS NOT NULL"))
    listed = []
    for pid in sorted({r["promo"] for r in with_promo}):
        p = promos[pid]
        mine = [r for r in with_promo if r["promo"] == pid]
        by = defaultdict(lambda: [0, 0.0])
        for r in mine:
            by[r["m"]][0] += 1
            by[r["m"]][1] += r["disc"]
        months = [dict(name=MONTHS[m - 1], n=by[m][0], disc=by[m][1]) for m in sorted(by)]
        # The note's layout: a promotion of an earlier year is dated by its month when it ran within one month,
        # otherwise by its year; a current promotion with valid dates gets its discounts month by month.
        earlier = p["start"][:4] != str(d.C)
        if earlier:
            when = (f", {MONTHS[int(p['start'][5:7]) - 1]} {p['start'][:4]}" if p["start"][:7] == p["end"][:7]
                    else f", {p['start'][:4]} promotion")
        else:
            when = ""
        style = "one" if len(months) == 1 else "total" if earlier or p["end"] < p["start"] else "monthly"
        after = [r for r in mine if r["date"] > p["end"]]
        listed.append(dict(id=pid, short=p["name"].removesuffix(" Promotion"), when=when, style=style, months=months,
                           disc=total(mine, "disc"), earlier=earlier, invalid=p["end"] < p["start"], n=len(mine),
                           after=len(after), after_months=sorted({MONTHS[r["m"] - 1] for r in after},
                                                                 key=MONTHS.index),
                           within=all(p["start"] <= ordered[r["id"]] <= p["end"] for r in after),
                           ordered=sorted({MONTHS[int(ordered[r["id"]][5:7]) - 1] for r in mine}, key=MONTHS.index),
                           start=p["start"], end=p["end"], collection=p["collection"]))
    blank = [r for r in rows if r["promo"] is None]
    claim(all(r["rate"] == 0 for r in blank), "the lines without a promotion carry zero discount")
    current = [p for p in listed if not p["earlier"] and not p["invalid"]]
    earlier = [p for p in listed if p["earlier"]]
    invalid = [p for p in listed if p["invalid"]]
    claim(len(invalid) == 1 and not invalid[0]["earlier"], "one current promotion ends before it starts")
    claim(all(p["start"][:4] == str(d.P) for p in earlier), f"the earlier promotions with {d.C} lines are {d.P} promotions")
    claim(all(p["after"] == p["n"] for p in earlier), f"all {d.C} lines of the {d.P} promotions fall after their end dates")
    claim(all(p["after"] == p["n"] for p in invalid), "all the lines of the promotion that ends before it starts fall after its end date")
    claim(all(p["after"] > 0 for p in current), "each current promotion has lines invoiced after its end date")
    claim(current[0]["within"], "all of the first current promotion's late lines were ordered within its dates")
    return dict(promos=listed, total=total(with_promo, "disc"), blank=len(blank), blank_rev=total(blank, "rev"),
                current=current, earlier=earlier, invalid=invalid[0])


# --- Exercise 13.4 -------------------------------------------------------------------------------

@note("ch13.ex4", EXERCISES)
def ex4(d, claim):
    rows = [r for r in lines(d) if r["year"] == d.C]
    seg = defaultdict(lambda: [0.0, set(), 0.0])
    region, cells = defaultdict(float), defaultdict(float)
    for r in rows:
        s = seg[r["segment"]]
        s[0] += r["rev"]
        s[1].add(r["customer"])
        s[2] += r["disc"]
        region[r["region"]] += r["rev"]
        cells[(r["segment"], r["region"])] += r["rev"]
    segments = [dict(name=k, rev=v[0], customers=len(v[1]), disc=v[2]) for k, v in sorted(seg.items(), key=lambda kv: -kv[1][0])]
    zero = [s["name"] for s in segments if s["disc"] == 0]
    claim(all({r["group"] for r in rows if r["segment"] == z} == {"Services"} for z in zero),
          "the segment without discounts buys only services")
    claim(all(r["promo"] is None for r in rows if r["group"] == "Services"), "services carry no promotion")
    cell = max(cells, key=cells.get)
    return dict(segments=segments, regions=sorted(region.items(), key=lambda kv: -kv[1]),
                cell=dict(segment=cell[0], region=cell[1], rev=cells[cell]))


# --- Exercise 13.5 -------------------------------------------------------------------------------

@note("ch13.ex5", EXERCISES)
def ex5(d, claim):
    all_lines = d.q("SELECT PromotionID, PriceOverrideApprovalID, PriceListLineID, ShipmentLineID, PricingMethod, Discount, "
                    "Quantity, SalesInvoiceLineID FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID")
    top = all_lines[:TOP_ROWS]

    def empty(rows, i):
        return sum(r[i] is None for r in rows)

    n = len(all_lines)
    claim([r[7] for r in all_lines if r[2] is None] == [r[7] for r in all_lines if r[3] is None]
          == [r[7] for r in all_lines if r[4] == "Base List"],
          "PriceListLineID and ShipmentLineID are empty on the same lines, the Base List lines")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID WHERE l.PricingMethod = 'Base List' "
                "AND i.ItemGroup <> 'Services'") == 0, "the Base List lines are design services")
    methods_all, methods_top = len({r[4] for r in all_lines}), len({r[4] for r in top})
    claim(methods_all == methods_top, "PricingMethod has the same number of distinct values on both bases")
    rates_top = {r[5] for r in top}
    claim(rates_top == {0}, "the top 1,000 lines have one Discount value, zero")
    invoices = d.q("SELECT PaymentDate, Status, InvoiceDate FROM SalesInvoice ORDER BY SalesInvoiceID")
    statuses = list(dict.fromkeys(r[1] for r in invoices))          # in order of first appearance
    top_statuses = list(dict.fromkeys(r[1] for r in invoices[:TOP_ROWS]))
    claim(top_statuses == ["Settled"], "the top 1,000 invoices are all Settled (paid)")
    unpaid = [r for r in invoices if r[0] is None]
    claim(sum(r[1] != "Settled" for r in unpaid) > 0.9 * len(unpaid),
          "the invoices with an empty PaymentDate are mostly open invoices")
    items = d.q("SELECT ListPrice, SupplyMode, ItemGroup, CollectionName, ItemID FROM Item")
    unpriced = [r for r in items if r[0] is None]
    claim(all(r[1] == "Purchased" for r in unpriced), "the items without a ListPrice are bought")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID WHERE i.ListPrice IS NULL") == 0,
          "the items without a ListPrice are not sold")
    sellable = [r for r in items if r[0] is not None]
    blank = Counter(r[2] for r in sellable if not r[3])
    groups = Counter(r[2] for r in sellable)
    claim(blank["Accessories"] == groups["Accessories"], "every sellable Accessories item lacks a CollectionName")
    claim(blank["Services"] == groups["Services"], "every service lacks a CollectionName")
    claim(set(blank) == {"Accessories", "Furniture", "Services"}, "only Accessories, Furniture, and services lack one")
    customer_columns = [r[1] for r in d.q("PRAGMA table_info(Customer)")]
    claim(all(d.one(f"SELECT COUNT(*) FROM Customer WHERE {c} IS NULL OR {c} = ''") == 0 for c in customer_columns),
          "Customer has no empty values")
    dup = d.q("SELECT CustomerName, COUNT(*) FROM Customer GROUP BY 1 HAVING COUNT(*) > 1 ORDER BY 1")
    claim(all(c == 2 for _, c in dup), "each duplicated customer name appears twice")
    # "The first rows are the earliest records": few later rows are dated within the first rows' dates.
    first_line = d.one("SELECT MAX(si.InvoiceDate) FROM (SELECT SalesInvoiceID FROM SalesInvoiceLine ORDER BY "
                       "SalesInvoiceLineID LIMIT ?) l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID", TOP_ROWS)
    later_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                        "WHERE l.SalesInvoiceLineID NOT IN (SELECT SalesInvoiceLineID FROM SalesInvoiceLine ORDER BY "
                        "SalesInvoiceLineID LIMIT ?) AND si.InvoiceDate < ?", TOP_ROWS, first_line)
    first_invoice = max(r[2] for r in invoices[:TOP_ROWS])
    later_invoices = sum(r[2] < first_invoice for r in invoices[TOP_ROWS:])
    claim(later_lines < TOP_ROWS / 10 and later_invoices < TOP_ROWS / 10,
          "the first rows are the earliest records (fewer than a tenth as many later rows fall within their dates)")
    claim(empty(top, 0) == len(top), "the first rows predate the promotions")
    claim(sum(r[0] is None for r in invoices[:TOP_ROWS]) / TOP_ROWS < len(unpaid) / len(invoices) / 5,
          "the first invoices have far fewer unpaid invoices than the whole table")
    collection = d.q("SELECT DISTINCT i.ItemCode, p.CollectionName FROM SalesOrderLine l JOIN Item i ON i.ItemID = l.ItemID "
                     "JOIN PromotionProgram p ON p.PromotionID = l.PromotionID WHERE p.ScopeType = 'Collection' "
                     "AND i.ListPrice IS NOT NULL AND i.ItemGroup = 'Furniture' AND COALESCE(i.CollectionName, '') = ''")
    claim(len(collection) == 1, "one of the Furniture items without a CollectionName was ordered under a collection promotion")
    return dict(n=n, promo=empty(all_lines, 0), override=empty(all_lines, 1), override_top=empty(top, 1),
                base=empty(all_lines, 2), base_top=empty(top, 2), methods=methods_all, discounts=len({r[5] for r in all_lines}),
                discounts_top=len(rates_top), top_empty=empty(top, 0) / len(top),
                fractional=sum(r[6] != int(r[6]) for r in all_lines),
                invoices=len(invoices), unpaid=len(unpaid), unpaid_top=sum(r[0] is None for r in invoices[:TOP_ROWS]),
                statuses=statuses, top_statuses=top_statuses, items=len(items), sellable=len(sellable), unpriced=len(unpriced),
                blank=sum(blank.values()), acc=blank["Accessories"], fur=blank["Furniture"], fur_word=word(blank["Furniture"]),
                svc=blank["Services"], customers=d.one("SELECT COUNT(*) FROM Customer"),
                names=d.one("SELECT COUNT(DISTINCT CustomerName) FROM Customer"), dup=[n for n, _ in dup],
                item=collection[0][0], collection=collection[0][1])


# --- Exercise 13.6 -------------------------------------------------------------------------------

@note("ch13.ex6", EXERCISES)
def ex6(d, claim):
    all_lines = lines(d)
    rows = [r for r in all_lines if r["year"] == d.C]
    revenue = total(rows, "rev")
    groups = defaultdict(float)
    for r in rows:
        groups[r["group"]] += r["rev"]
    slices = sorted(((g, v / revenue) for g, v in groups.items()), key=lambda kv: -kv[1])
    claim(slices[-2][1] - slices[-1][1] < 0.03, "the small slices are close together, so they cannot be ranked by eye")
    furniture = [r["rate"] for r in rows if r["group"] == "Furniture"]
    everything = monthly_revenue(all_lines)
    start = f"{d.F}-01"
    others = [v for m, v in everything.items() if m != start]
    growth = everything[f"{d.C}-12"] / everything[start] - 1
    claim(0.75 <= growth < 0.80, f"growth from January {d.F} to December {d.C} is almost 80%")
    years = [sum(r["rev"] for r in all_lines if r["year"] == y) for y in d.years]
    monthly = monthly_revenue(rows)
    discounts = defaultdict(float)
    for r in rows:
        discounts[r["month"]] += r["disc"]
    peak = max(monthly, key=lambda m: discounts[m] / monthly[m])
    return dict(n_slices=word(len(slices)), slices=slices, avg=sum(r["rate"] for r in rows) / len(rows),
                ratio=total(rows, "disc") / total(rows, "price"), of_list=total(rows, "disc") / total(rows, "list"),
                f_avg=sum(furniture) / len(furniture), start=everything[start], low=min(others), high=max(others),
                changes=[b / a - 1 for a, b in zip(years, years[1:])],
                peak=dict(month=month_name(peak), share=discounts[peak] / monthly[peak]),
                services=groups["Services"], services_share=groups["Services"] / revenue)
