"""Chapter 4's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 4 is the first Excel chapter (Power Query, Tables, structured references, named cells, validation, conditional
formatting, slicers), so the contexts do three jobs:

- they supply the values a step-by-step solution can show as "Check" values (the totals of the tutorials' workbook, the
  cells of each exercise's model answer),
- they give each Table's column letters as the workbook lays them out (a conditional formatting rule is written with a
  column letter, so the guide must name the right one), and
- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll or a schema change flags the wording instead of leaving it stale.

Keys: ch04.chapter (the chapter note and its three tutorials) and ch04.g1 to ch04.g6 (the exercises; each is used next to
the registered note ch04.ex1 to ch04.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter04-exercises (Chapter 4 Exercises - Solutions.xlsx).
"""

from __future__ import annotations

import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, schema
from guide_contexts.ch03 import col_letter
from notes.ch04 import xround

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "04-excel-essentials"
DECK = REPO / "slides" / "chapter-04" / "index.qmd"

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
ITEM_COLUMNS = ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "StandardCost", "ListPrice", "UnitOfMeasure",
                "SupplyMode", "CollectionName", "LifecycleStatus"]                      # Tutorial 4.1, Step 5
PRICING_METHODS = ["Approved Override", "Base List", "Customer Price List", "Segment Price List"]   # Tutorial 4.2, Step 4
DISCOUNT_RATES = [0.0, 0.08, 0.1, 0.12]
BLANK_TRACKING = "(TrackingNumber IS NULL OR TrackingNumber = '')"


# --- helpers -------------------------------------------------------------------------------------------------------

def long_date(iso: str) -> str:
    y, m, day = (int(x) for x in iso.split("-"))
    return f"{MONTHS[m - 1]} {day}, {y}"


def day_before(iso: str) -> str:
    from datetime import date, timedelta
    return (date.fromisoformat(iso) - timedelta(days=1)).isoformat()


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
    comment = source.note_comment("chapters/04-excel-essentials/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 4\b")
    letters = re.findall(r"(\d+) ([A-D])[,.]", comment.split("\n", 2)[1])
    key = {int(n): a for n, a in letters}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def excel_percentile(values: list[float], p: float) -> float:
    """PERCENTILE.INC: linear interpolation at position p * (n - 1) of the sorted values."""
    xs = sorted(values)
    k = p * (len(xs) - 1)
    f = int(k)
    return xs[f] if f + 1 >= len(xs) else xs[f] + (k - f) * (xs[f + 1] - xs[f])


def letters_of(d, claim, table: str, chosen: list[str] | None = None, extra: list[str] = ()) -> dict[str, str]:
    """The worksheet column letter of each column of the Table the exercise works in: the database's columns in their
    order (or the chosen ones, kept in that order, as Choose Columns does), then the calculated columns the steps add."""
    cols = [r[1] for r in d.q(f"PRAGMA table_info({table})")]
    if chosen is not None:
        missing = [c for c in chosen if c not in cols]
        claim(not missing, f"{table} has the columns the tutorial keeps (missing: {', '.join(missing)})")
        kept = [c for c in cols if c in chosen]
        claim(kept == list(chosen), f"{table}'s Table keeps its columns in the order the tutorial lists them")
        cols = kept
    return {c: col_letter(i + 1) for i, c in enumerate(list(cols) + list(extra))}


def promotions(d) -> list[dict]:
    rows = d.q("SELECT PromotionID, PromotionCode, PromotionName, ScopeType, CustomerSegment, ItemGroup, CollectionName, "
               "DiscountPct, EffectiveStartDate, EffectiveEndDate FROM PromotionProgram ORDER BY PromotionID")
    out = []
    for pid, code, name, scope, segment, group, collection, rate, start, end in rows:
        out.append(dict(id=pid, code=code, name=name, scope=scope, target=group or segment or collection, rate=rate,
                        start=start, end=end, start_long=long_date(start), end_long=long_date(end)))
    return out


# --- the chapter note and its tutorials ----------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceDate", "DueDate", "PaymentDate", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "Quantity", "BaseListPrice", "UnitPrice", "Discount", "LineTotal",
                         "PromotionID", "PricingMethod"],
    "Item": ITEM_COLUMNS,
    "PromotionProgram": ["PromotionID", "PromotionCode", "PromotionName", "ScopeType", "ItemGroup", "DiscountPct", "EffectiveStartDate",
                         "EffectiveEndDate"],
    "Shipment": ["TrackingNumber", "Status", "ShipmentDate", "DeliveryDate", "FreightCost", "BillableFreightAmount"],
    "SalesOrder": ["SalesOrderID", "FreightTerms"],
    "PriceOverrideApproval": ["RequestedByEmployeeID", "ApprovedByEmployeeID", "Status", "ReferenceUnitPrice", "ApprovedUnitPrice"],
    "CreditMemo": ["CreditMemoDate", "SubTotal"],
}


@context("ch04.chapter")
def chapter(d, claim):
    have = schema(d, claim, CHAPTER_SCHEMA)
    lines = d.q("SELECT SalesInvoiceLineID, Quantity, BaseListPrice, UnitPrice, Discount, LineTotal, PricingMethod, PromotionID "
                "FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID")
    n_lines = len(lines)
    n_invoices = d.one("SELECT COUNT(*) FROM SalesInvoice")
    items_all = d.one("SELECT COUNT(*) FROM Item")
    items_sold = d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL")
    claim(0 < items_sold < items_all, "the Item Table's blank ListPrice filter removes the items Charles River buys and keeps the items it sells")
    n_programs = d.one("SELECT COUNT(*) FROM PromotionProgram")

    # Tutorial 4.1: the type trap and the control totals
    claim(all(r[4] == 0 and r[7] is None for r in lines[:200]),
          "the first 200 invoice lines carry no promotion, so Power Query can type Discount as a whole number")
    claim(d.one("SELECT COUNT(*) FROM (SELECT FreightAmount FROM SalesInvoice ORDER BY SalesInvoiceID LIMIT 200) "
                "WHERE FreightAmount <> CAST(FreightAmount AS INTEGER)") == 0
          and d.one("SELECT COUNT(*) FROM SalesInvoice WHERE FreightAmount <> CAST(FreightAmount AS INTEGER)") > 0,
          "FreightAmount is whole in the first 200 invoices and fractional later, so it can be typed as a whole number")
    line_total = round(sum(r[5] for r in lines), 2)
    subtotal = d.one("SELECT ROUND(SUM(SubTotal), 2) FROM SalesInvoice")
    claim(abs(line_total - subtotal) < 0.005, "the invoice lines add up to the invoice subtotals, so the control total difference is zero")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice s WHERE ABS(s.SubTotal - (SELECT SUM(LineTotal) FROM SalesInvoiceLine l "
                "WHERE l.SalesInvoiceID = s.SalesInvoiceID)) > 0.005") == 0, "every invoice's SubTotal equals the sum of its lines")
    discount = round(sum(xround(r[1] * r[3] * r[4]) for r in lines), 2)
    list_amount = round(sum(xround(r[1] * r[2]) for r in lines), 2)
    claim(0 < discount < 0.05 * line_total and list_amount > line_total,
          "the discount taken is a small fraction of the line total, and the list amount is above it")
    t1 = dict(lines=n_lines, invoices=n_invoices, line_total=line_total, subtotal=subtotal, discount=discount, list_amount=list_amount,
              items_all=items_all, items_sold=items_sold, n_programs=n_programs,
              items_removed=items_all - items_sold, kept_columns=len(ITEM_COLUMNS))

    # Tutorial 4.2: the threshold, the large lines and the grid
    totals = [r[5] for r in lines]
    thr = excel_percentile(totals, 0.9)
    large = [x for x in totals if x > thr]
    share = sum(large) / sum(totals)
    thr95 = excel_percentile(totals, 0.95)
    large95 = [x for x in totals if x > thr95]
    median = excel_percentile(totals, 0.5)
    claim(median < thr < max(totals) / 2, "the 90th percentile is well above the median line total and far below the largest line")
    claim(3000 <= thr < 10000, "the 90th-percentile threshold is several thousand dollars (Tutorial 4.2, Step 2)")
    claim(0.08 <= len(large) / n_lines <= 0.12, "about a tenth of the lines are large")
    claim(0.25 <= share <= 0.4, "the large lines hold close to a third of the value billed")
    methods = sorted({r[6] for r in lines})
    rates = sorted({r[4] for r in lines})
    claim(methods == PRICING_METHODS, "the four pricing methods are the ones Tutorial 4.2 types into the grid")
    claim(rates == DISCOUNT_RATES, "the four discount rates on the invoice lines are 0, 0.08, 0.1 and 0.12")
    grid = []
    for m in PRICING_METHODS:
        counts = [sum(1 for r in lines if r[6] == m and r[4] == rate) for rate in DISCOUNT_RATES]
        grid.append(dict(method=m, counts=counts, total=sum(counts)))
    column_totals = [sum(g["counts"][j] for g in grid) for j in range(len(DISCOUNT_RATES))]
    base = next(g for g in grid if g["method"] == "Base List")
    claim(sum(base["counts"][1:]) == 0, "no Base List line carries a discount")
    segment = next(g for g in grid if g["method"] == "Segment Price List")
    claim(segment["counts"][0] == max(c for g in grid for c in g["counts"]),
          "most lines are billed at a segment price list with no discount")
    t2 = dict(threshold=thr, large=len(large), share=share, threshold95=thr95, large95=len(large95),
              grid=grid, column_totals=column_totals, grid_total=sum(column_totals), segment_share=segment["counts"][0] / n_lines)

    # Tutorial 4.3: the promotion that stands out
    promos = promotions(d)
    by_lines = {p["id"]: 0 for p in promos}
    by_discount = {p["id"]: 0.0 for p in promos}
    shaded = 0
    for r in lines:
        if r[4] > 0:
            shaded += 1
        if r[7] is not None:
            by_lines[r[7]] += 1
            by_discount[r[7]] += xround(r[1] * r[3] * r[4])
    top = max(promos, key=lambda p: by_lines[p["id"]])
    claim(top["id"] == max(by_discount, key=by_discount.get), "the promotion with the most lines also has the most discount dollars")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE Discount > 0 AND PromotionID IS NULL") == 0
          and d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE Discount = 0 AND PromotionID IS NOT NULL") == 0,
          "a line has a discount exactly when it has a PromotionID, so the formula rule shades the promotion lines")
    claim(top["target"] == "Furniture" and top["scope"] == "ItemGroup", "the promotion that stands out covers the Furniture item group")
    t3 = dict(promo=dict(top, lines=by_lines[top["id"]], discount=round(by_discount[top["id"]], 2),
                         share=by_discount[top["id"]] / sum(by_discount.values())),
              shaded=shaded, no_promo=n_lines - shaded, blank_button=n_lines - sum(by_lines.values()))

    n_q, longest = mcq_facts()
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    return dict(n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(), n_questions=n_q,
                longest_correct=and_join(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3,
                letters=letters_of(d, claim, "SalesInvoiceLine", extra=["ListAmount", "DiscountAmount"]),
                promos_with_dates=[p for p in promos if p["end"] <= p["start"]],
                odd_ids=and_join(p["id"] for p in promos if p["end"] <= p["start"]))


# --- Exercise 4.1: a billing schedule --------------------------------------------------------------------------------------

@context("ch04.g1")
def g1(d, claim):
    have = schema(d, claim, {"SalesInvoice": ["InvoiceDate", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"],
                             "CreditMemo": ["CreditMemoDate", "SubTotal"]})
    years = d.years
    first, c = years[0], years[-1]
    rows = []
    for y in years:
        n, sub, frt, tax, gt = d.q("SELECT COUNT(*), SUM(SubTotal), SUM(FreightAmount), SUM(TaxAmount), SUM(GrandTotal) FROM SalesInvoice "
                                   "WHERE substr(InvoiceDate, 1, 4) = ?", str(y))[0]
        rows.append(dict(year=y, n=n, sub=round(sub, 2), frt=round(frt, 2), tax=round(tax, 2), gt=round(gt, 2)))
    total = dict(n=sum(r["n"] for r in rows), **{k: round(sum(r[k] for r in rows), 2) for k in ("sub", "frt", "tax", "gt")})
    claim(total["n"] == d.one("SELECT COUNT(*) FROM SalesInvoice"), "every invoice is dated in a fiscal year of the window, so the grid's total row equals the entire Table")
    claim(abs(total["gt"] - d.one("SELECT ROUND(SUM(GrandTotal), 2) FROM SalesInvoice")) < 0.005, "the grid's GrandTotal equals the Table's")
    columns = [r[1] for r in d.q("PRAGMA table_info(SalesInvoice)")]
    claim(columns[columns.index("SubTotal"):columns.index("SubTotal") + 4] == ["SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"],
          "the four amount columns are adjacent in the Table, so one formula can be filled across the grid")
    claim(len(set(r["sub"] for r in rows)) == len(rows), "each year's SubTotal differs, so a grid pasted with SubTotal in every column shows it")
    memos = {int(y): (n, s) for y, n, s in d.q("SELECT substr(CreditMemoDate, 1, 4), COUNT(*), ROUND(SUM(SubTotal), 2) FROM CreditMemo GROUP BY 1")}
    claim(c in memos, "the period has credit memos, so the model answer can quote them")
    posted = d.q("SELECT a.AccountNumber, a.AccountType, ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                 "WHERE g.SourceDocumentType = 'SalesInvoice' GROUP BY 1, 2")
    freight = [n for n, t, b in posted if t == "Revenue" and abs(b - total["frt"]) < 0.005]
    tax = [n for n, t, b in posted if t == "Liability" and abs(b - total["tax"]) < 0.005]
    claim(len(freight) == 1 and len(tax) == 1, "the freight billed has its own revenue account and the sales tax a liability account in the ledger")
    # a freight column left as whole numbers (the type trap of Tutorial 4.1, Step 6c) breaks the parts check
    freights = [r[0] for r in d.q("SELECT FreightAmount FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) = ?", str(c))]
    half_up = sum(xround(f, 0) - f for f in freights)
    half_even = sum(round(f) - f for f in freights)
    claim(abs(half_up) > 0.005 and abs(half_even) > 0.005, "rounding FreightAmount to whole dollars leaves the period's parts check nonzero")
    fractional = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE FreightAmount <> CAST(FreightAmount AS INTEGER)")
    claim(fractional > 0, "some invoices carry cents of freight")
    return dict(first=first, c=c, start=f"{c}-01-01", end=f"{c}-12-31", start_long=long_date(f"{c}-01-01"), end_long=long_date(f"{c}-12-31"),
                rows=rows, total=total, fractional=fractional, cm_n=memos[c][0], cm_sub=memos[c][1], year=rows[-1], freight_account=freight[0], tax_account=tax[0],
                letters=letters_of(d, claim, "SalesInvoice"))


# --- Exercise 4.2: promotions ----------------------------------------------------------------------------------------------

@context("ch04.g2")
def g2(d, claim):
    schema(d, claim, {"PromotionProgram": ["PromotionID", "PromotionCode", "PromotionName", "ScopeType", "ItemGroup", "CustomerSegment",
                                           "CollectionName", "DiscountPct", "EffectiveStartDate", "EffectiveEndDate"],
                      "SalesInvoiceLine": ["PromotionID", "Discount", "LineTotal", "Quantity", "UnitPrice"]})
    promos = promotions(d)
    lines = d.q("SELECT PromotionID, Quantity, UnitPrice, Discount, LineTotal FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL")
    for p in promos:
        mine = [r for r in lines if r[0] == p["id"]]
        p.update(lines=len(mine), total=round(sum(r[4] for r in mine), 2), discount=round(sum(xround(r[1] * r[2] * r[3]) for r in mine), 2),
                 other=sum(1 for r in mine if abs(r[3] - p["rate"]) > 1e-9))
    discount = round(sum(p["discount"] for p in promos), 2)
    for p in promos:
        p["share"] = p["discount"] / discount
    top = max(promos, key=lambda p: p["discount"])
    second = sorted(promos, key=lambda p: -p["discount"])[1]
    claim(top["lines"] == max(p["lines"] for p in promos), "the promotion with the most discount dollars also has the most lines")
    claim(sum(p["other"] for p in promos) == 0, "no promotion line carries a rate other than its promotion's DiscountPct")
    claim(top["scope"] == "ItemGroup" and top["target"] == "Furniture", "the largest promotion's scope is an item group, Furniture")
    unit = d.one("SELECT COUNT(*) FROM PromotionProgram WHERE EffectiveStartDate IS NULL OR EffectiveEndDate IS NULL")
    claim(unit == 0, "every promotion has both effective dates")
    rates = sorted({p["rate"] for p in promos})
    claim(rates == [0.08, 0.1, 0.12], "the promotion rates are 8, 10 and 12 percent")
    scope_words = {"ItemGroup": f"every item in the {top['target']} item group", "Segment": f"every customer in the {top['target']} segment",
                   "Collection": f"the items of the {top['target']} collection"}
    claim(top["scope"] in scope_words, "the largest promotion has a scope the model answer can describe")
    return dict(promos=promos, discount=discount, lines=sum(p["lines"] for p in promos), total=round(sum(p["total"] for p in promos), 2),
                top=top, second=second, scope_phrase=scope_words[top["scope"]], n_promos=len(promos),
                backwards=[p for p in promos if p["end"] < p["start"]], single=[p for p in promos if p["end"] == p["start"]],
                backwards_ids=and_join(p["id"] for p in promos if p["end"] < p["start"]),
                single_ids=and_join(p["id"] for p in promos if p["end"] == p["start"]),
                rates=rates, letters=letters_of(d, claim, "SalesInvoiceLine", extra=["ListAmount", "DiscountAmount"]))


# --- Exercise 4.3: list-price margins --------------------------------------------------------------------------------------

@context("ch04.g3")
def g3(d, claim):
    schema(d, claim, {"Item": ITEM_COLUMNS})
    letters = letters_of(d, claim, "Item", ITEM_COLUMNS, extra=["UnitMargin", "MarginPct"])
    items = d.q("SELECT ItemCode, ItemName, ItemGroup, ItemType, StandardCost, ListPrice FROM Item WHERE ListPrice IS NOT NULL")
    goods = [i for i in items if i[3] == "Finished Good"]
    services = [i for i in items if i[3] != "Finished Good"]
    groups = ["Accessories", "Furniture", "Lighting", "Textiles"]
    target = 0.45
    claim(sorted({i[2] for i in goods}) == groups, "the finished goods are in the four product groups the exercise offers")
    claim(all(i[2] == "Services" and i[4] == 0 for i in services),
          "the items with a list price that are not finished goods are the design services, all with a StandardCost of 0")
    claim(all(1 - i[4] / i[5] >= target for i in services) and all(i[2] not in groups for i in services),
          "the design services change neither the group averages nor the count below the target, so omitting the ItemType condition shows no difference here")
    ordered = sorted(items, key=lambda i: (i[2], -(1 - i[4] / i[5])))
    first_unique = (1 - ordered[0][4] / ordered[0][5]) != (1 - ordered[1][4] / ordered[1][5])
    claim(first_unique and ordered[0][2] == groups[0], "the first row after the sort is the Accessories item with the highest MarginPct, with no tie")
    markup_max = max((i[5] - i[4]) / i[4] for i in goods)
    claim(markup_max > 1, "a margin divided by StandardCost instead of ListPrice would exceed 100 percent for some finished good")
    service_pct = min(1 - i[4] / i[5] for i in services)
    claim(service_pct == 1 == max(1 - i[4] / i[5] for i in services), "the design services' MarginPct is 100 percent")
    rows = []
    for name in groups:
        mine = [i for i in goods if i[2] == name]
        rows.append(dict(name=name, n=len(mine), margin=sum(i[5] - i[4] for i in mine) / len(mine),
                         pct=sum(1 - i[4] / i[5] for i in mine) / len(mine), below=sum(1 for i in mine if 1 - i[4] / i[5] < target)))
    most = max(rows, key=lambda r: r["margin"])
    least = min(rows, key=lambda r: r["margin"])
    claim(most is min(rows, key=lambda r: r["pct"]) and least is max(rows, key=lambda r: r["pct"]),
          "the group with the largest margin per unit has the lowest average percentage, and the group with the smallest has the highest")
    return dict(letters=letters, n_items=len(items), n_goods=len(goods), services=[dict(code=i[0], name=i[1]) for i in services],
                n_services=len(services), service_pct=service_pct, groups=groups, rows=rows, most=most, least=least, target=target, first=ordered[0][0],
                markup_max=markup_max, kept=len(ITEM_COLUMNS))


# --- Exercise 4.4: freight -------------------------------------------------------------------------------------------------

@context("ch04.g4")
def g4(d, claim):
    schema(d, claim, {"Shipment": ["ShipmentID", "SalesOrderID", "FreightCost", "BillableFreightAmount"], "SalesOrder": ["SalesOrderID", "FreightTerms"]})
    rows = d.q("SELECT o.FreightTerms, s.FreightCost, s.BillableFreightAmount FROM Shipment s LEFT JOIN SalesOrder o ON o.SalesOrderID = s.SalesOrderID")
    claim(all(r[0] is not None for r in rows), "every shipment's sales order is found, so the lookup returns no errors")
    terms = []
    for t in sorted({r[0] for r in rows}):
        mine = [r for r in rows if r[0] == t]
        terms.append(dict(name=t, n=len(mine), cost=round(sum(r[1] for r in mine), 2), billed=round(sum(r[2] for r in mine), 2),
                          margin=round(sum(r[2] - r[1] for r in mine), 2), avg_cost=sum(r[1] for r in mine) / len(mine),
                          billing=sum(1 for r in mine if r[2] > 0)))
    claim([t["name"] for t in terms] == ["Prepaid", "Prepaid and Add"], "the FreightTerms values are Prepaid and Prepaid and Add")
    negative = [round(r[2] - r[1], 2) for r in rows if round(r[2] - r[1], 2) < 0]
    claim(abs(sum(t["margin"] for t in terms) - round(sum(r[2] - r[1] for r in rows), 2)) < 0.005, "the grid's terms add up to the Table's FreightMargin")
    total = round(sum(t["margin"] for t in terms), 2)
    pp, pa = terms
    claim(pp["billing"] == 0 and pa["billing"] > 0, "Prepaid shipments bill no freight and Prepaid and Add shipments do")
    claim(abs(pp["margin"]) > 10 * abs(pa["margin"]), "the freight absorbed on Prepaid orders is far larger than the shortfall on Prepaid and Add")
    return dict(terms=terms, pp=pp, pa=pa, total=total, negative_n=len(negative), negative_total=round(sum(negative), 2),
                orders=d.one("SELECT COUNT(*) FROM SalesOrder"), absorbed_share=pp["margin"] / total,
                letters=letters_of(d, claim, "Shipment", extra=["FreightTerms", "FreightMargin"]))


# --- Exercise 4.5: the shipment exception report -----------------------------------------------------------------------------

@context("ch04.g5")
def g5(d, claim):
    schema(d, claim, {"Shipment": ["ShipmentID", "ShipmentDate", "TrackingNumber", "Status", "DeliveryDate"]})
    review, review2 = f"{d.C}-12-31", f"{d.C}-12-01"
    status = dict(d.q("SELECT Status, COUNT(*) FROM Shipment GROUP BY 1"))
    claim(set(status) == {"Delivered", "In Transit"}, "the shipment statuses are Delivered and In Transit")
    late = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", review)
    late2 = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", review2)
    claim(late2 < late, "moving the review date back by a month removes some In Transit shipments from the late count")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate >= ?", review) > 0,
          "an In Transit shipment is due on or after the review date, so the Status slicer shows more shipments than the late count")
    claim(d.one(f"SELECT COUNT(*) FROM Shipment WHERE {BLANK_TRACKING} AND Status = 'Delivered'") > 0,
          "some Delivered shipments have no tracking number")
    return dict(delivered=status["Delivered"], in_transit=status["In Transit"], review_long=long_date(review), review2_long=long_date(review2),
                drop=late - late2, window=f"{MONTHS[int(review2[5:7]) - 1]} {int(review2[8:])} to {MONTHS[int(review[5:7]) - 1]} {int(day_before(review)[8:])}",
                letters=letters_of(d, claim, "Shipment"))


# --- Exercise 4.6: price override approvals ------------------------------------------------------------------------------------

@context("ch04.g6")
def g6(d, claim):
    schema(d, claim, {"PriceOverrideApproval": ["PriceOverrideApprovalID", "SalesOrderLineID", "RequestedByEmployeeID", "ApprovedByEmployeeID",
                                                "RequestDate", "ApprovedDate", "ReferenceUnitPrice", "RequestedUnitPrice", "ApprovedUnitPrice",
                                                "Status"],
                      "Employee": ["EmployeeID", "EmployeeName", "JobTitle"],
                      "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesOrderLineID", "UnitPrice", "PricingMethod", "PriceListLineID",
                                           "PriceOverrideApprovalID"]})
    req = d.q("SELECT PriceOverrideApprovalID, SalesOrderLineID, RequestedByEmployeeID, ApprovedByEmployeeID, Status, "
              "1 - ApprovedUnitPrice / ReferenceUnitPrice, ApprovedUnitPrice FROM PriceOverrideApproval ORDER BY PriceOverrideApprovalID")
    names = {e: (n, t) for e, n, t in d.q("SELECT EmployeeID, EmployeeName, JobTitle FROM Employee")}
    requesters = sorted({r[2] for r in req})
    claim(all(e in names for e in requesters), "every requester is in the Employee Table, so the lookups find a name and a job title")
    grid = []
    for e in requesters:
        mine = [r for r in req if r[2] == e]
        grid.append(dict(id=e, name=names[e][0], title=names[e][1], n=len(mine),
                         other=sum(1 for r in mine if r[4] == "Approved" and r[3] is not None and r[3] != e),
                         own=sum(1 for r in mine if r[4] == "Approved" and r[3] == e), open=sum(1 for r in mine if r[4] == "Pending"),
                         wrong_other=sum(1 for r in mine if r[3] != e)))
    claim(sum(g["n"] for g in grid) == len(req), "the grid's requesters account for every request")
    own_row = max(grid, key=lambda g: g["own"])
    claim(own_row["wrong_other"] > own_row["other"], "a formula that tests only the approver counts the Pending requests, whose approver is blank, as approvals by someone else")
    approved = [r for r in req if r[4] == "Approved"]
    claim(all(r[3] is not None for r in approved) and all(r[3] is None for r in req if r[4] == "Pending"),
          "every Approved request has an approver and every Pending request has none, so the blank-approver and self-approved groups do not overlap")
    claim(own_row["open"] == sum(1 for r in req if r[4] == "Pending"), "the approver made every Pending request")
    top = max(req, key=lambda r: r[5])
    claim(top[4] == "Approved" and sorted(r[5] for r in req)[-2] < top[5], "the request with the largest DiscountFromReference is an Approved one, with no tie")
    pending = []
    for r in (r for r in req if r[4] == "Pending"):
        billed = d.q("SELECT UnitPrice, PricingMethod, SalesInvoiceLineID, PriceOverrideApprovalID FROM SalesInvoiceLine "
                     "WHERE SalesOrderLineID = ? ORDER BY SalesInvoiceLineID", r[1])
        requested = d.one("SELECT RequestedUnitPrice FROM PriceOverrideApproval WHERE PriceOverrideApprovalID = ?", r[0])
        pending.append(dict(id=r[0], line=r[1], lines=len(billed), at_price=sum(1 for u, *_ in billed if abs(u - r[6]) < 0.005),
                            methods=and_join(sorted({m for _, m, *_ in billed})), line_ids=and_join(b[2] for b in billed),
                            linked=sum(1 for b in billed if b[3] is not None), requested=requested, price=r[6]))
    claim(all(p["lines"] > 0 and p["at_price"] == p["lines"] for p in pending), "every Pending request's order line was invoiced, at the pending price")
    claim(all(p["linked"] == 0 for p in pending), "no invoice line of a Pending request carries a PriceOverrideApprovalID")
    claim(all(abs(p["requested"] - p["price"]) >= 0.005 for p in pending),
          "on every Pending request the amount in ApprovedUnitPrice differs from the RequestedUnitPrice, so it is not the requested price")
    return dict(grid=grid, own_row=own_row, blank=sum(1 for r in req if r[3] is None), top_id=top[0], pending=pending,
                pending_lines=sum(p["lines"] for p in pending), n_approved=len(approved),
                letters=letters_of(d, claim, "PriceOverrideApproval", extra=["DiscountFromReference", "SelfApproved"]))
