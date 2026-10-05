"""Chapter 6's instructor notes: the values each note states, and the claims its wording makes.

The invoice lines are InvoiceLines as Tutorial 5.3 builds it, with chapter 6's unrounded custom columns
(StdCostAmount = Quantity x StandardCost, ListAmount = Quantity x BaseListPrice, DiscountAmount =
Quantity x UnitPrice x Discount); a line belongs to the fiscal year and quarter of its InvoiceDate.
"""

from __future__ import annotations

import statistics

from notes import note

EXERCISES = "chapters/06-descriptive-analytics/_exercises.qmd"
GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories", "Services"]       # the book's order of the item groups
REVENUE_LINES = [("4010", "Furniture"), ("4020", "Lighting"), ("4030", "Textiles"), ("4040", "Accessories"),
                 ("4080", "Services")]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
ORDINALS = ["", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]
# Chapter 5's Furniture product type codes (tbl-05-03), singular and plural.
TYPE_NAMES = {"BKC": ("bookcase", "bookcases"), "BNH": ("bench", "benches"), "CON": ("console table", "console tables"),
              "CTB": ("coffee table", "coffee tables"), "DSK": ("desk", "desks"), "NGT": ("nightstand", "nightstands"),
              "SDB": ("sideboard", "sideboards"), "TBL": ("dining table", "dining tables")}

_LINES: dict = {}


def lines(d, year: int) -> list[dict]:
    """The invoice lines of a fiscal year (by InvoiceDate), with the columns the chapter's exercises use."""
    key = (str(d.path), year)
    if key not in _LINES:
        rows = d.q("SELECT l.SalesInvoiceLineID, si.SalesInvoiceID, si.InvoiceDate, i.ItemGroup, i.ItemCode, i.UnitOfMeasure, "
                   "i.StandardCost, l.Quantity, l.LineTotal, l.Quantity * i.StandardCost, l.Quantity * l.BaseListPrice, "
                   "l.Quantity * l.UnitPrice * l.Discount, l.PricingMethod, l.PromotionID, c.CustomerID, c.CustomerName, "
                   "c.CustomerSegment, c.Region FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "JOIN Item i ON i.ItemID = l.ItemID JOIN Customer c ON c.CustomerID = si.CustomerID "
                   "WHERE si.InvoiceDate BETWEEN ? AND ?", f"{year}-01-01", f"{year}-12-31")
        names = ["id", "invoice", "date", "grp", "code", "uom", "std", "U", "R", "C", "L", "D", "method", "promo",
                 "customer", "name", "segment", "region"]
        _LINES[key] = [dict(zip(names, r), q=(int(r[2][5:7]) + 2) // 3, type=r[4][4:7]) for r in rows]
    return _LINES[key]


def total(rows, field: str, **match) -> float:
    return sum(r[field] for r in rows if all(r[k] == v for k, v in match.items()))


def period(start: str, end: str) -> str:
    """A promotion's effective months in prose: "November 2025", "September to October 2025" (an end on or before the
    start's month gives the start's month alone)."""
    s, e = MONTHS[int(start[5:7]) - 1], MONTHS[int(end[5:7]) - 1]
    if end[:7] <= start[:7]:
        return f"{s} {start[:4]}"
    return f"{s} to {e} {start[:4]}" if start[:4] == end[:4] else f"{s} {start[:4]} to {e} {end[:4]}"


def series(items: list[str]) -> str:
    """A list in prose: "A", "A and B", "A, B, and C"."""
    return items[0] if len(items) == 1 else (" and ".join(items) if len(items) == 2 else ", ".join(items[:-1]) + ", and " + items[-1])


@note("ch06.ex1", EXERCISES)
def ex1(d, claim):
    asof = f"{d.C}-12-31"
    close1, close2 = d.closes_of(d.C)
    close_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber IN (?, ?)", close1, close2)
    tb = d.q("SELECT a.AccountNumber, a.AccountType, a.AccountSubType, ROUND(SUM(g.Debit) - SUM(g.Credit), 2) FROM GLEntry g "
             "JOIN Account a ON a.AccountID = g.AccountID WHERE g.PostingDate < ? AND g.VoucherNumber NOT IN (?, ?) "
             "GROUP BY a.AccountID ORDER BY a.AccountNumber", f"{d.N}-01-01", close1, close2)
    debits = sum(max(0.0, r[3]) for r in tb)
    credits = sum(max(0.0, -r[3]) for r in tb)
    claim(abs(debits - credits) < 0.005, "debit and credit balances are equal")
    balance = {str(r[0]): r[3] for r in tb}
    by = {}
    for _, t, s, b in tb:
        by[(t, s)] = by.get((t, s), 0.0) + b
    # revenue and expense accounts hold only the current year's activity (the earlier closes zeroed them)
    activity = dict((str(n), b) for n, b in d.q(
        f"SELECT a.AccountNumber, ROUND(SUM(g.Debit) - SUM(g.Credit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        f"WHERE g.FiscalYear = ? AND a.AccountType IN ('Revenue', 'Expense') AND {d.no_closes()} GROUP BY 1", d.C))
    claim(all(abs(activity.get(str(n), 0.0) - b) < 0.005 for n, t, _, b in tb if t in ("Revenue", "Expense")),
          f"revenue and expense accounts show only fiscal {d.C}")
    claim(d.P - d.F == 1 and all(d.closes_of(y) for y in (d.F, d.P)), f"the earlier years of the window ({d.F} and {d.P}) were closed")
    opr = -by.get(("Revenue", "Operating Revenue"), 0.0)
    contra = -by.get(("Revenue", "Contra Revenue"), 0.0)
    net_rev = opr + contra
    cogs = -by.get(("Expense", "COGS"), 0.0)
    gm = net_rev + cogs
    opex = -by.get(("Expense", "Operating Expense"), 0.0)
    oi = gm + opex
    other = -(by.get(("Revenue", "Other Income or Expense"), 0.0) + by.get(("Expense", "Other Expense"), 0.0)
              + by.get(("Revenue", "Other Income"), 0.0))
    ni = oi + other
    claim([n for n, t, s, b in tb if t == "Revenue" and s == "Contra Revenue" and b != 0] == [4060],
          "sales returns and allowances (4060) is the only contra revenue account with a balance")
    cogs_accounts = {str(n) for n, t, s, b in tb if s == "COGS" and b != 0}
    claim({"5050", "5060", "5080"} <= cogs_accounts, "cost of goods sold includes 5050, 5060, and 5080")
    others = {str(n): (t, s) for n, t, s, b in tb if s in ("Other Income or Expense", "Other Expense", "Other Income") and b != 0}
    claim(others == {"7020": ("Revenue", "Other Income or Expense"), "7030": ("Expense", "Other Expense")},
          "other income and expense is 7020 (typed Revenue, subtype Other Income or Expense) and 7030 (Other Expense)")
    loss, interest = balance["7020"], balance["7030"]
    claim(loss > 0, "7020 holds a loss (a debit balance)")
    closing = d.one("SELECT TotalAmount FROM JournalEntry WHERE EntryNumber = ?", close2)
    claim(abs(closing - ni) < 0.005, f"net income equals {close2}")
    assets = sum(b for (t, _), b in by.items() if t == "Asset")
    liabilities = -sum(b for (t, _), b in by.items() if t == "Liability")
    equity = -sum(b for (t, _), b in by.items() if t == "Equity")
    claim(abs(assets - (liabilities + equity + ni)) < 0.005, "assets equal liabilities plus equity plus net income")
    claim(d.one("SELECT COUNT(*) FROM JournalEntry WHERE EntryType = 'Opening' AND PostingDate <= ?", asof) > 0,
          "the balances include the opening balance entry")
    # revenue reconciliation: account balance against InvoiceLines of the year
    rows = lines(d, d.C)
    recon = []
    for number, group in REVENUE_LINES:
        bal = -balance.get(number, 0.0)
        ln = round(total(rows, "R", grp=group), 2)
        recon.append(dict(account=number, group=group, balance=bal, lines=ln, diff=round(bal - ln, 2)))
    invoices = d.q("SELECT DISTINCT si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate, g.PostingDate FROM SalesInvoice si "
                   "JOIN GLEntry g ON g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID = si.SalesInvoiceID "
                   "WHERE g.FiscalYear = ? AND si.InvoiceDate < ? ORDER BY si.InvoiceNumber", d.C, f"{d.C}-01-01")
    found = []
    for sid, number, date, posted in invoices:
        groups = d.q("SELECT i.ItemGroup, ROUND(SUM(l.LineTotal), 2) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID "
                     "WHERE l.SalesInvoiceID = ? GROUP BY 1", sid)
        # the invoice's lines by shipment date (an invoice may bill goods shipped on more than one date)
        shipped = d.q("SELECT s.ShipmentDate, ROUND(SUM(l.LineTotal), 2) FROM SalesInvoiceLine l JOIN ShipmentLine sl "
                      "ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                      "WHERE l.SalesInvoiceID = ? GROUP BY 1 ORDER BY 1", sid)
        claim(len(groups) > 0 and len(shipped) > 0, f"{number} has invoice lines with shipments")
        found.append(dict(number=number, date=date, posted=posted, group=" and ".join(g for g, _ in groups),
                          first=groups[0][0] if groups else None, amounts=dict(groups), amount=sum(a for _, a in groups),
                          shipped=shipped))
    order = [g for _, g in REVENUE_LINES]
    found.sort(key=lambda i: (order.index(i["first"]) if i["first"] in order else len(order), i["number"]))
    claim(all(abs(r["diff"] - sum(i["amounts"].get(r["group"], 0.0) for i in found)) < 0.005 for r in recon),
          "the differences are exactly these invoices")
    claim(all(i["date"][:4] == str(d.P) and i["number"].startswith(f"SI-{d.C}-") for i in found),
          f"the invoices are dated in {d.P} with the next year's number")
    claim(len({i["posted"] for i in found}) == 1, "the invoices were posted on one date")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE DeliveryDate IS NOT NULL AND substr(DeliveryDate, 1, 4) <> substr(ShipmentDate, 1, 4)") == 0,
          "every shipment is delivered in the year it ships")
    early = [i for i in found if any(s[:4] == str(d.P) for s, _ in i["shipped"])]
    later = [i for i in found if i not in early]
    claim(len(early) == 1, f"only one of the invoices shipped in {d.P}")
    early = early[0] if early else found[0]
    cut = [(s, a) for s, a in early["shipped"] if s[:4] == str(d.P)]           # the goods shipped in the prior year
    rest = [(s, a) for s, a in early["shipped"] if s[:4] != str(d.P)]
    # the dates on which everything else shipped: the other invoices, and the rest of the cutoff invoice
    dates = sorted({s for i in later for s, _ in i["shipped"]} | {s for s, _ in rest})
    claim(len(later) > 0 and all(s[:4] == str(d.C) for s in dates),
          f"the other invoices (and any rest of the cutoff invoice) shipped in {d.C}")
    when = f"on {dates[0]}" if len(dates) == 1 else (f"between {dates[0]} and {dates[-1]}" if dates else "")
    freight = -balance.get("4050", 0.0)
    billed = d.one("SELECT ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g WHERE g.AccountID = ? AND g.FiscalYear = ? "
                   "AND g.SourceDocumentType = 'SalesInvoice'", d.account("4050"), d.C)
    header = d.one("SELECT ROUND(SUM(FreightAmount), 2) FROM SalesInvoice WHERE SalesInvoiceID IN (SELECT SourceDocumentID FROM GLEntry "
                   "WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ?)", d.C)
    claim(abs(billed - header) < 0.005, "freight revenue is billed on the invoice header, not on an invoice line")
    return dict(asof=asof, close1=close1, close2=close2, close_rows=close_rows, accounts=len(tb),
                zero=sum(1 for r in tb if r[3] == 0), debits=debits, opr=opr, contra=contra, net_rev=net_rev, cogs=cogs, gm=gm,
                opex=opex, oi=oi, other=other, loss=loss, interest=interest, ni=ni, assets=assets, liabilities=liabilities,
                equity=equity, recon=recon, invoices=found, posted=found[0]["posted"],
                early=dict(number=early["number"], shipped=" and ".join(s for s, _ in cut), amount=early["amount"],
                           cut=sum(a for _, a in cut), rest=sum(a for _, a in rest), part=bool(rest)),
                others=WORDS[len(later)] if len(later) < len(WORDS) else len(later), others_shipped=when, freight=freight)


@note("ch06.ex2", EXERCISES)
def ex2(d, claim):
    now, before = lines(d, d.C), lines(d, d.P)
    combos = {}
    for r in now:
        combos.setdefault((r["segment"], r["grp"]), [0.0, 0.0])[1] += r["R"]
    for r in before:
        combos.setdefault((r["segment"], r["grp"]), [0.0, 0.0])[0] += r["R"]
    grand = sum(v[1] for v in combos.values())
    ranked = sorted(combos.items(), key=lambda kv: -kv[1][1])
    shares = [(s, g, v[1] / grand, v[1]) for (s, g), v in ranked[:5]]
    large = [(s, g, v[0], v[1], v[1] / v[0] - 1) for (s, g), v in combos.items() if v[0] >= 500000]
    up = sorted(large, key=lambda t: -t[4])[:2]
    down = sorted(large, key=lambda t: t[4])[:2]
    claim(all(t[4] > 0 for t in up) and all(t[4] < 0 for t in down), "two combinations increased and two decreased")
    by = lambda key: sorted(((k, sum(r["R"] for r in now if r[key] == k) / sum(r["R"] for r in before if r[key] == k) - 1)
                             for k in {r[key] for r in now}), key=lambda t: -t[1])
    segments, regions = by("segment"), by("region")
    total_change = sum(r["R"] for r in now) / sum(r["R"] for r in before) - 1
    claim({r["grp"] for r in now + before if r["segment"] == "Design Services"} == {"Services"}
          and {r["segment"] for r in now + before if r["grp"] == "Services"} == {"Design Services"},
          "Design Services buys only Services, and only Design Services buys Services")
    return dict(shares=shares, up=up, down=down, segments=segments, total_change=total_change, regions=regions)


@note("ch06.ex3", EXERCISES)
def ex3(d, claim):
    rows = lines(d, d.C)
    groups = []
    for g in GROUPS:
        revenue, cost = total(rows, "R", grp=g), total(rows, "C", grp=g)
        groups.append(dict(group=g, revenue=revenue, margin=revenue - cost, pct=(revenue - cost) / revenue))
    services = next(x for x in groups if x["group"] == "Services")
    claim(all(r["std"] == 0 for r in rows if r["grp"] == "Services") and abs(services["pct"] - 1) < 1e-9,
          "Services items carry StandardCost 0, so their margin shows 100%")
    products = [x for x in groups if x["group"] != "Services"]
    by_margin = sorted(products, key=lambda x: -x["pct"])
    revenue, margin = sum(x["revenue"] for x in products), sum(x["margin"] for x in products)
    by_revenue = sorted(products, key=lambda x: -x["revenue"])
    more = [x["group"] for x in by_revenue if x["margin"] / margin > x["revenue"] / revenue]
    claim(len(more) >= 2, "more than one product line contributes more margin than revenue (the verb is plural)")
    types = {}
    for r in rows:
        if r["grp"] == "Furniture":
            t = types.setdefault(r["type"], [0.0, 0.0])
            t[0] += r["R"]
            t[1] += r["C"]
    ranked = sorted(((code, (rc[0] - rc[1]) / rc[0]) for code, rc in types.items()), key=lambda t: -t[1])
    high = [(code, TYPE_NAMES[code][0], p) for code, p in ranked[:2]]
    low = [(code, TYPE_NAMES[code][0], p) for code, p in ranked[::-1][:2]]
    time_cost = d.one("SELECT SUM(ExtendedCost) FROM ServiceTimeEntry WHERE WorkDate BETWEEN ? AND ?", f"{d.C}-01-01", f"{d.C}-12-31")
    salaries = d.one(f"SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                     d.account("6280"), d.C)
    return dict(by_margin=by_margin, shares=[(x["group"], x["revenue"] / revenue, x["margin"] / margin) for x in by_revenue],
                more=series(more), high=high, low=low, time_cost=time_cost, time_pct=1 - time_cost / services["revenue"],
                salaries=salaries, salaries_pct=1 - salaries / services["revenue"])


@note("ch06.ex4", EXERCISES)
def ex4(d, claim):
    rows = [r for r in lines(d, d.C) if r["grp"] == "Furniture" and r["q"] in (3, 4)]
    agg = {}
    for r in rows:
        a = agg.setdefault((r["type"], r["q"]), dict(U=0.0, R=0.0, C=0.0, D=0.0, L=0.0))
        for k in "URCDL":
            a[k] += r[k]
    types = sorted({t for t, _ in agg})
    claim(all((t, 3) in agg and (t, 4) in agg for t in types), "every product type sold in both quarters")
    a = {t: agg[(t, 3)] for t in types}
    b = {t: agg[(t, 4)] for t in types}
    u3, u4 = sum(v["U"] for v in a.values()), sum(v["U"] for v in b.values())
    q3, q4 = sum(v["R"] - v["C"] for v in a.values()), sum(v["R"] - v["C"] for v in b.values())
    per = lambda v, k: v[k] / v["U"]
    margin = lambda v: (v["R"] - v["C"]) / v["U"]
    price = sum(b[t]["U"] * (per(b[t], "R") - per(a[t], "R")) for t in types)
    cost = -sum(b[t]["U"] * (per(b[t], "C") - per(a[t], "C")) for t in types)
    volume = (u4 - u3) * q3 / u3
    mix = sum((b[t]["U"] - u4 * a[t]["U"] / u3) * margin(a[t]) for t in types)
    claim(abs(price + cost + volume + mix - (q4 - q3)) < 1e-6, "the four effects sum exactly to the change")
    claim(abs(cost) >= 0.005, "the cost effect is not zero")
    promotions = -sum(b[t]["U"] * (per(b[t], "D") - per(a[t], "D")) for t in types)
    claim(promotions < 0, "the price effect contains a (negative) promotional discount")
    change = {t: (per(b[t], "R") - per(a[t], "R"), per(b[t], "C") - per(a[t], "C")) for t in types}
    top = max(types, key=lambda t: abs(change[t][1]))
    claim(change[top][0] < 0 and change[top][1] < 0 and per(b[top], "L") < per(a[top], "L"),
          f"{top}'s price and cost per unit fell because cheaper items made up more of the quarter (its list price per unit fell)")
    # the other types whose price and cost per unit both fell like the example's, and those where both rose
    same = sorted((t for t in types if t != top and change[t][0] < 0 and change[t][1] < 0), key=lambda t: -b[t]["U"])
    rose_both = sorted((t for t in types if change[t][0] > 0 and change[t][1] > 0), key=lambda t: -b[t]["U"])
    parts = ([f"{series(same)} move{'s' if len(same) == 1 else ''} the same way"] if same else []) + \
            ([f"price and cost per unit rose together for {series(rose_both)}"] if rose_both else [])
    together = "; " + ", and ".join(parts) if parts else ""
    moves = sorted(types, key=lambda t: b[t]["U"] - a[t]["U"])
    fell, rose = moves[:2], moves[::-1][:2]
    claim(all(b[t]["U"] < a[t]["U"] for t in fell) and all(b[t]["U"] > a[t]["U"] for t in rose), "two types fell and two rose")
    unit = lambda t: (t, a[t]["U"], b[t]["U"])
    return dict(q3=q3, q4=q4, change=q4 - q3, price=price, cost=cost, volume=volume, mix=mix,
                top=dict(code=top, plural=TYPE_NAMES[top][1], p3=per(a[top], "R"), p4=per(b[top], "R"),
                         c3=per(a[top], "C"), c4=per(b[top], "C")),
                same=same, together=together, promotions=round(promotions, -2), fell=[unit(t) for t in fell],
                rose=[unit(t) for t in rose])


@note("ch06.ex5", EXERCISES)
def ex5(d, claim):
    now, before = lines(d, d.C), lines(d, d.P)
    rows = []
    for g in GROUPS:
        for q in range(1, 5):
            expected, actual = total(before, "R", grp=g, q=q), total(now, "R", grp=g, q=q)
            diff = actual - expected
            rows.append(dict(group=g, q=q, diff=diff, pct=diff / expected,
                             flagged=abs(diff) > 0.10 * expected and abs(diff) > 50000))
    flagged = [r for r in rows if r["flagged"]]
    missed = sorted((r for r in rows if not r["flagged"]), key=lambda r: -abs(r["diff"]))[:2]
    # the largest unflagged difference's rank among all the differences in dollars ("the second-largest")
    rank = sorted(rows, key=lambda r: -abs(r["diff"])).index(missed[0]) + 1
    largest = "largest" if rank == 1 else f"{ORDINALS[rank] if rank < len(ORDINALS) else f'{rank}th'}-largest"
    # the product lines by revenue, and how far down the list the unflagged differences reach
    lines_ = sorted(GROUPS, key=lambda g: -total(now, "R", grp=g))
    reach = max(lines_.index(r["group"]) + 1 for r in missed)
    claim(reach <= 2, "the two largest unflagged differences are in the largest product lines")
    furniture_q4 = next(r for r in rows if (r["group"], r["q"]) == ("Furniture", 4))
    claim(furniture_q4["diff"] < 0, "Furniture Q4 revenue fell against the prior year (the quarter of the promotion discounts, Tutorial 6.3)")
    claim(any(r["group"] == "Services" for r in flagged), "Services has flagged differences")
    # Requirement (5)'s example: the largest flagged difference, split into volume and price (units and price per unit)
    claim(len(flagged) > 0, "the threshold flags at least one difference")
    top = max(flagged, key=lambda r: abs(r["diff"]))
    u0, u1 = total(before, "U", grp=top["group"], q=top["q"]), total(now, "U", grp=top["group"], q=top["q"])
    r0, r1 = total(before, "R", grp=top["group"], q=top["q"]), total(now, "R", grp=top["group"], q=top["q"])
    volume, price = (u1 - u0) * r0 / u0, u1 * (r1 / u1 - r0 / u0)
    claim(abs(volume + price - top["diff"]) < 0.01, "the volume and price parts add up to the difference")
    driver = "volume" if abs(volume) > abs(price) else "price"
    claim(abs(max(volume, price, key=abs)) > 0.5 * abs(top["diff"]),
          f"{top['group']} Q{top['q']}'s difference is mostly {driver} (that part is more than half of it)")
    example = dict(group=top["group"], q=top["q"], diff=top["diff"], driver=driver, units=u1 / u0 - 1,
                   price=(r1 / u1) / (r0 / u0) - 1)
    # the note points Furniture Q4 (the promotion quarter) to its evidence only when the threshold misses it
    return dict(flagged=flagged, missed=missed, largest=largest, example=example, furniture_q4_missed=not furniture_q4["flagged"],
                lines="the largest product line" if reach == 1 else f"the {WORDS[reach]} largest product lines")


@note("ch06.ex6", EXERCISES)
def ex6(d, claim):
    rows = lines(d, d.C)
    groups = []
    for g in GROUPS:
        values = [r["R"] for r in rows if r["grp"] == g]
        groups.append((g, len(values), sum(values), statistics.mean(values), statistics.median(values)))
    revenue = sum(r["R"] for r in rows)
    customers = {}
    for r in rows:
        customers.setdefault(r["customer"], [r["name"], r["segment"], 0.0])[2] += r["R"]
    ranked = sorted(customers.values(), key=lambda c: -c[2])
    top5, top10 = sum(c[2] for c in ranked[:5]) / revenue, sum(c[2] for c in ranked[:10]) / revenue
    segments = {c[1] for c in ranked[:10]}
    claim(len(segments) == 1, "the ten largest customers are all in one segment")
    claim(top10 < 0.20, "concentration is low (the ten largest customers hold less than a fifth of revenue)")
    methods = {}
    for r in rows:
        m = methods.setdefault(r["method"], [0, 0.0])
        m[0] += 1
        m[1] += r["R"]
    pricing = sorted(((m, v[1] / revenue, v[0]) for m, v in methods.items()), key=lambda t: -t[1])
    claim(all(r["grp"] == "Services" and r["uom"] == "Hour" for r in rows if r["method"] == "Base List"),
          "Base List prices only the hourly design services")
    promos = {}
    for r in rows:
        if r["promo"] is not None:
            p = promos.setdefault(r["promo"], [0, 0.0])
            p[0] += 1
            p[1] += r["D"]
    shares = sorted(((g, sum(1 for r in rows if r["grp"] == g and r["promo"] is not None) / sum(1 for r in rows if r["grp"] == g))
                     for g in GROUPS), key=lambda t: -t[1])
    info = {r[0]: r[1:] for r in d.q("SELECT PromotionID, ScopeType, CustomerSegment, ItemGroup, CollectionName, "
                                     "EffectiveStartDate, EffectiveEndDate FROM PromotionProgram")}
    late = []
    months = []
    for pid in sorted(promos):
        scope, segment, group, collection, start, end = info[pid]
        if start[:4] == str(d.P):
            dates = [r["date"] for r in rows if r["promo"] == pid]
            months += [int(x[5:7]) for x in dates]
            late.append(dict(id=pid, scope=segment or group or collection, when=period(start, end)))
    claim(len(late) == 2, f"two promotions of {d.P} have lines invoiced in {d.C}")
    main = max(promos, key=lambda p: promos[p][0])
    claim(any(r["date"] > info[main][5] for r in rows if r["promo"] == main),
          f"promotion {main} has lines invoiced after its end date (late invoicing)")
    reversed_ = [p for p in sorted(promos) if info[p][5] <= info[p][4] and info[p][4][:4] == str(d.C)]
    claim(len(reversed_) == 1, f"one promotion of {d.C} has effective dates that end on or before their start")
    return dict(groups=groups, customers=len(customers), top5=top5, top10=top10, segment=sorted(segments)[0],
                largest=[c[0] for c in ranked[:5]], pricing=pricing,
                promos=[(p, promos[p][0], promos[p][1]) for p in sorted(promos)], shares=shares, late=late,
                first=MONTHS[min(months) - 1] if months else None, last=MONTHS[max(months) - 1] if months else None,
                main=main, reversed=reversed_[0] if reversed_ else None)
