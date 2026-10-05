"""Chapter 13 Exercises - Solutions.pbip: the instructor's solutions to the Power BI exercises of Chapter 13, built on a
copy of Charles River Reports at the end of Tutorial 13.3 (the reader's File > Save as copy).

Each exercise gets its own report page named after it (Ex 13.1 ...; Exercise 13.6 has a Draft and a Revised page),
with the visuals the exercise asks for and a text box labeled "Model answer" that answers its written requirements
from computed values. Tables the tutorials trimmed are imported again under the query names the exercises give
(InvoiceHeaders, PromotionProgram, and the four Profile queries, whose Enable load is cleared), with the type
corrections of the workbook's first 200 rows. Every value of an exercise's instructor note becomes a check that reads
the model the way the exercise's visuals do; the expected values come from facts/notes/ch13.py (read-only SQL).
"""

from __future__ import annotations

from collections import defaultdict

from pbibuild.model import Query, query_table
from pbibuild.pbir import Page, Visual, _ref, agg, col, lit, textbox
from pbibuild.reports import (MONEY, Build, _aliased, card, claim, keep, money, one, rows, slicer, value_axis)
from notes import ch13  # noqa: E402  (facts/ is on the path once pbibuild.reports is imported)

MONTHS = ch13.MONTHS
FY = col("SalesInvoice", "FiscalYear")
LT, DA, LA = (agg("SalesInvoiceLine", c) for c in ("LineTotal", "DiscountAmount", "ListAmount"))


def pct(x: float, places: int = 1) -> str:
    return f"{x * 100:.{places}f}%"


def spct(x: float, places: int = 1) -> str:
    return ("+" if x > 0 else "") + pct(x, places)


def answer(name: str, x, y, w, h, title: str, paragraphs: list) -> Visual:
    """The model answer to an exercise's written requirements, in a text box on its page."""
    return textbox(name, x, y, w, h, [(f"Model answer: {title}", True)] + paragraphs, size=10)


def top_n(name: str, f: dict, by: dict, n: int) -> dict:
    """Filters on this visual, Filter type Top N: show the top `n` items of `f` by value `by` (an aggregation)."""
    entity, alias, ref = _aliased(f)
    inner = by["Aggregation"]["Expression"]["Column"]
    b_entity = inner["Expression"]["SourceRef"]["Entity"]
    b_alias = b_entity[0].lower() if b_entity[0].lower() != alias else "t"
    order = {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": b_alias}},
                                                       "Property": inner["Property"]}},
                             "Function": by["Aggregation"]["Function"]}}
    sub = {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0},
                                  {"Name": b_alias, "Entity": b_entity, "Type": 0}],
           "Select": [{**ref, "Name": "field"}], "OrderBy": [{"Direction": 2, "Expression": order}], "Top": n}
    return {"name": name, "field": f, "type": "TopN", "howCreated": "User",
            "filter": {"Version": 2, "From": [{"Name": "subquery", "Expression": {"Subquery": {"Query": sub}}, "Type": 2},
                                              {"Name": alias, "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [ref],
                                                       "Table": {"SourceRef": {"Source": "subquery"}}}}}]}}


def expand_all(levels: list[dict]) -> dict:
    """A matrix's Rows expanded all the way down (Expand all down one level, repeated)."""
    return {"expansionStates": [{"roles": ["Rows"], "levels": [
        {"queryRefs": [_ref(f)[1]], "isCollapsed": False, "identityKeys": [f], "isPinned": True} for f in levels[:-1]] +
        [{"queryRefs": [_ref(levels[-1])[1]], "isCollapsed": True, "isPinned": True}]}]}


def labels(show: bool = True) -> dict:
    return {"labels": [{"properties": {"show": lit(show)}}]}


def year_of(y: int) -> str:
    return f"SalesInvoice[FiscalYear] = {y}"


def lt(*filters: str) -> str:
    return f"CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ), {', '.join(filters)} )"


def ex1(b: Build) -> None:
    ctx = ch13.ex1(b.data, claim)
    y = b.year
    # (2) InvoiceHeaders: T16_SalesInvoice again, FreightAmount corrected with Replace current before Choose Columns
    q = (Query.navigator("InvoiceHeaders", b.xlsx, 16, "SalesInvoice", corrections={"FreightAmount": "type number"})
         .select(["SalesInvoiceID", "InvoiceDate", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"])
         .custom("FiscalYear", "Date.Year([InvoiceDate])", "Int64.Type"))
    amounts = ["SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"]
    b.model.add(query_table(q, formats={a: MONEY for a in amounts},
                            summarize={"SalesInvoiceID": "none", "FiscalYear": "none"}))
    hy = col("InvoiceHeaders", "FiscalYear")
    page = b.report.add(Page("ex131", "Ex 13.1"))
    page.add(Visual("groupMatrix", "pivotTable", 20, 20, 1240, 190,
                    {"Rows": [FY], "Columns": [col("Item", "ItemGroup")], "Values": [LT]},
                    title="Revenue (line totals) by fiscal year and item group"))
    page.add(Visual("headerTable", "tableEx", 20, 230, 820, 170,
                    {"Values": [hy] + [agg("InvoiceHeaders", a) for a in amounts]},
                    title="Invoice header amounts by fiscal year (InvoiceHeaders, not related to the model)"))
    accounts = dict(rows("SELECT a.AccountName, a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                         "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.SourceLineID IS NULL GROUP BY 1, 2"))
    freight = next(n for k, n in accounts.items() if "Freight" in k)
    tax = next(n for k, n in accounts.items() if "Tax" in k)
    cur = ctx["years"][-1]
    yrs = ctx["years"]
    page.add(answer("answer", 20, 420, 1240, 290, "Exercise 13.1", [
        f"(1) The fiscal {y} row is Chapter 6's revenue by item group: " +
        "; ".join(f"{g} {money(v)}" for g, v in cur["groups"]) + f"; total {money(cur['total'])}.",
        "(2) SubTotal by fiscal year equals the line totals exactly: " +
        "; ".join(f"{x['year']} {money(x['total'])} on {x['n']:,} invoices" for x in yrs) +
        ". No invoice is without lines.",
        "(3) GrandTotal (" + "; ".join(money(x["grand"]) for x in yrs) + ") is SubTotal plus freight (" +
        "; ".join(money(x["freight"]) for x in yrs) + ") plus sales tax (" + "; ".join(money(x["tax"]) for x in yrs) +
        "). The lines hold only the goods and services sold, so they reconcile to SubTotal. Revenue from the sale of "
        f"goods and services is SubTotal: freight billed to the customer posts to its own revenue account ({freight}), "
        f"and sales tax is collected for the state and posts to a liability ({tax}), as Chapter 10's trace of "
        f"{ctx['traced']} showed.",
        "(4) SalesInvoice already relates the invoices to their lines. A second table with the same key would be a "
        "second path from the invoices to the lines, and the model keeps one table per entity; InvoiceHeaders exists "
        "only to test the header amounts, so it stays unrelated (a filter on Item does not change its totals)."]))
    page.expect = ["ItemGroup", money(dict(cur["groups"])["Furniture"]), money(cur["total"]), "Sum of GrandTotal",
                   money(cur["grand"]), "Model answer: Exercise 13.1"]

    t = "Exercise 13.1"
    for x in yrs:
        yy = x["year"]
        for g, v in x["groups"]:
            b.check(t, f"{yy} {g} line totals (matrix)", round(v, 2), lt(year_of(yy), f"'Item'[ItemGroup] = \"{g}\""))
        b.check(t, f"{yy} line totals (row total)", round(x["total"], 2), lt(year_of(yy)))
        h = f"InvoiceHeaders[FiscalYear] = {yy}"
        b.check(t, f"{yy} invoices in InvoiceHeaders", x["n"], f"CALCULATE ( COUNTROWS ( InvoiceHeaders ), {h} )", 0)
        b.check(t, f"{yy} SubTotal (equals the line totals)", round(x["total"], 2),
                f"CALCULATE ( SUM ( InvoiceHeaders[SubTotal] ), {h} )")
        for label, key, column in [("freight", "freight", "FreightAmount"), ("sales tax", "tax", "TaxAmount"),
                                   ("GrandTotal", "grand", "GrandTotal")]:
            b.check(t, f"{yy} {label}", round(x[key], 2), f"CALCULATE ( SUM ( InvoiceHeaders[{column}] ), {h} )")
        b.check(t, f"{yy} GrandTotal = SubTotal + freight + tax", 0,
                f"CALCULATE ( SUM ( InvoiceHeaders[GrandTotal] ) - SUM ( InvoiceHeaders[SubTotal] ) - "
                f"SUM ( InvoiceHeaders[FreightAmount] ) - SUM ( InvoiceHeaders[TaxAmount] ), {h} )")
    b.check(t, "freight is not rounded (FreightAmount typed Decimal Number)", round(sum(x["freight"] for x in yrs), 2),
            "SUM ( InvoiceHeaders[FreightAmount] )")
    b.check(t, "invoices without lines", 0, "COUNTROWS ( EXCEPT ( VALUES ( InvoiceHeaders[SalesInvoiceID] ), "
                                            "VALUES ( SalesInvoiceLine[SalesInvoiceID] ) ) )", 0)
    b.check(t, "InvoiceHeaders is unrelated (a filter on Item leaves its SubTotal whole)",
            round(sum(x["total"] for x in yrs), 2),
            "CALCULATE ( SUM ( InvoiceHeaders[SubTotal] ), 'Item'[ItemGroup] = \"Furniture\" )")


def rank_dax(column: str, value, y: int) -> str:
    v = f"\"{value}\"" if isinstance(value, str) else value
    return (f"CALCULATE ( RANKX ( ALL ( {column} ), CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ) ) ), "
            f"{column} = {v}, {year_of(y)} )")


def ex2(b: Build) -> None:
    ctx = ch13.ex2(b.data, claim)
    y, n = b.year, ch13.TOP_N
    name, cid = col("Customer", "CustomerName"), col("Customer", "CustomerID")
    page = b.report.add(Page("ex132", "Ex 13.2"))
    page.add(Visual("byName", "tableEx", 20, 20, 400, 330, {"Values": [name, LT]},
                    title=f"Top {n} customers by revenue, fiscal {y} (grouped by name)",
                    filters=[keep("byNameYear", FY, [y]), top_n("byNameTop", name, LT, n)], sort=[(LT, "Descending")]))
    page.add(Visual("byKey", "tableEx", 440, 20, 440, 330, {"Values": [cid, name, LT]},
                    title=f"Top {n} customers by revenue, fiscal {y} (grouped by CustomerID)",
                    filters=[keep("byKeyYear", FY, [y]), top_n("byKeyTop", cid, LT, n)], sort=[(LT, "Descending")]))
    ids = agg("Customer", "CustomerID", "distinctcount")
    page.add(Visual("sharedNames", "tableEx", 900, 20, 360, 330, {"Values": [name, (ids, "CustomerIDs")]},
                    title="Customer names and the number of CustomerIDs that carry them", sort=[(ids, "Descending")]))
    dups = [ctx["merged"]["name"], ctx["single"]["name"]]
    seg, reg = col("Customer", "CustomerSegment"), col("Customer", "Region")
    page.add(Visual("sharedRevenue", "tableEx", 20, 370, 620, 140, {"Values": [name, cid, seg, reg, LT]},
                    title=f"Fiscal {y} revenue of the names that belong to more than one CustomerID",
                    filters=[keep("sharedRevenueYear", FY, [y]), keep("sharedRevenueNames", name, dups)]))
    mg, tenth, single = ctx["merged"], ctx["tenth"], ctx["single"]
    parts = mg["parts"]
    page.add(answer("answer", 660, 370, 600, 340, "Exercise 13.2", [
        f"(2) By name, {mg['name']} ranks {mg['rank']} with {money(mg['amount'])}, the sum of {mg['n']} different "
        "customers: " + "; ".join(f"CustomerID {p['id']} ({p['region']}, {p['segment']}) {money(p['amount'])}, "
                                  f"{p['rank']} by key" for p in parts) +
        f". By key, the tenth customer is {tenth['name']} ({tenth['id']}), {money(tenth['amount'])}, which grouping by "
        f"name pushes to {tenth['rank']}. Group by the key, and show the name beside it.",
        f"(3) {mg['name']} is CustomerIDs " + " and ".join(str(p["id"]) for p in parts) +
        f"; {single['name']} is CustomerIDs " + " and ".join(map(str, single["ids"])) +
        f", but only {single['id']} had fiscal {y} revenue ({money(single['amount'])}). {ctx['customers']} customers "
        f"had revenue in fiscal {y}, under {ctx['names']} names.",
        f"(4) The largest customer, {ctx['largest']['name']} ({ctx['largest']['id']}), holds "
        f"{pct(ctx['largest']['share'])} of revenue; the second, {ctx['second']['name']}, {pct(ctx['second']['share'])}; "
        f"the top ten by key {pct(ctx['top_key'])} ({pct(ctx['top_name'])} by name). No customer approaches the "
        f"{ch13.POLICY:.0%} policy, so there is no concentration to report.",
        "(5) A Top N filter sits in the Filters pane, which a reader of the published page may never open, so the table "
        f"reads as if it listed every customer. State it on the page: \"Top {n} customers by revenue, fiscal {y}\"."]))
    page.expect = [f"Top {n} customers by revenue, fiscal {y} (grouped by name)", mg["name"], money(mg["amount"]),
                   tenth["name"], money(tenth["amount"]), money(parts[0]["amount"]), "CustomerIDs"]

    t = "Exercise 13.2"
    fy = year_of(y)
    b.check(t, f"customers with revenue in fiscal {y}", ctx["customers"],
            f"CALCULATE ( DISTINCTCOUNT ( SalesInvoice[CustomerID] ), {fy} )", 0)
    b.check(t, f"customer names with revenue in fiscal {y}", ctx["names"],
            f"CALCULATE ( COUNTROWS ( SUMMARIZE ( SalesInvoiceLine, Customer[CustomerName] ) ), {fy} )", 0)
    number = lambda o: ch13.ORDINALS.index(o) if o in ch13.ORDINALS else int(o[:-2])     # "ninth" -> 9, "117th"
    b.check(t, f"{mg['name']} by name", round(mg["amount"], 2), lt(fy, f"Customer[CustomerName] = \"{mg['name']}\""))
    b.check(t, f"{mg['name']} rank by name", number(mg["rank"]), rank_dax("Customer[CustomerName]", mg["name"], y), 0)
    for p in parts:
        b.check(t, f"CustomerID {p['id']} revenue", round(p["amount"], 2), lt(fy, f"Customer[CustomerID] = {p['id']}"))
        b.check(t, f"CustomerID {p['id']} rank by key", number(p["rank"]), rank_dax("Customer[CustomerID]", p["id"], y), 0)
    b.check(t, f"tenth by key: {tenth['name']} ({tenth['id']})", round(tenth["amount"], 2),
            lt(fy, f"Customer[CustomerID] = {tenth['id']}"))
    b.check(t, f"{tenth['name']} rank by key", n, rank_dax("Customer[CustomerID]", tenth["id"], y), 0)
    b.check(t, f"{tenth['name']} rank by name", number(tenth["rank"]),
            rank_dax("Customer[CustomerName]", tenth["name"], y), 0)
    b.check(t, f"{single['name']}: CustomerIDs", len(single["ids"]),
            f"CALCULATE ( COUNTROWS ( Customer ), Customer[CustomerName] = \"{single['name']}\" )", 0)
    b.check(t, f"{single['name']} ({single['id']}) revenue", round(single["amount"], 2),
            lt(fy, f"Customer[CustomerName] = \"{single['name']}\""))
    b.check(t, "names carried by more than one CustomerID", 2,
            "COUNTROWS ( FILTER ( VALUES ( Customer[CustomerName] ), CALCULATE ( COUNTROWS ( Customer ) ) > 1 ) )", 0)
    by = "ADDCOLUMNS ( VALUES ( Customer[{0}] ), \"R\", CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ) ) )"
    total = "SUM ( SalesInvoiceLine[LineTotal] )"
    b.check(t, f"largest customer's share ({ctx['largest']['name']})", round(ctx["largest"]["share"], 6),
            f"CALCULATE ( DIVIDE ( MAXX ( {by.format('CustomerID')}, [R] ), {total} ), {fy} )", 0.000005)
    b.check(t, "top ten share by key", round(ctx["top_key"], 6),
            f"CALCULATE ( DIVIDE ( SUMX ( TOPN ( {n}, {by.format('CustomerID')}, [R], DESC ), [R] ), {total} ), {fy} )",
            0.000005)
    b.check(t, "top ten share by name", round(ctx["top_name"], 6),
            f"CALCULATE ( DIVIDE ( SUMX ( TOPN ( {n}, {by.format('CustomerName')}, [R], DESC ), [R] ), {total} ), {fy} )",
            0.000005)


def ex3(b: Build) -> None:
    ctx = ch13.ex3(b.data, claim)
    y = b.year
    # (1) the promotions, related to the lines on PromotionID (dates typed Date, as Tutorial 13.1 Step 4b does)
    q = (Query.navigator("PromotionProgram", b.xlsx, 7, "PromotionProgram")
         .select(["PromotionID", "PromotionCode", "PromotionName", "ScopeType", "DiscountPct", "EffectiveStartDate",
                  "EffectiveEndDate"]).types({"EffectiveStartDate": "type date", "EffectiveEndDate": "type date"}))
    b.model.add(query_table(q, formats={"DiscountPct": "0%"}, summarize={"PromotionID": "none", "DiscountPct": "none"}))
    b.model.relate("SalesInvoiceLine.PromotionID", "PromotionProgram.PromotionID")
    levels = [col("PromotionProgram", c) for c in ("PromotionName", "EffectiveStartDate", "EffectiveEndDate")]
    count = agg("SalesInvoiceLine", "SalesInvoiceLineID", "count")
    page = b.report.add(Page("ex133", "Ex 13.3"))
    page.add(Visual("promotionMatrix", "pivotTable", 20, 20, 1240, 400,
                    {"Rows": levels, "Columns": [col("SalesInvoice", "Month")], "Values": [DA, count]},
                    title=f"Promotional discounts and invoice lines by promotion and month, fiscal {y}",
                    filters=[keep("promotionMatrixYear", FY, [y])], extra=expand_all(levels), active=("Rows",)))
    cur, early, bad = ctx["current"], ctx["earlier"], ctx["invalid"]
    after = "; ".join(f"{p['short']} (ends {p['end']}): {p['after']} of {p['n']} lines invoiced after it, in "
                      + " and ".join(p["after_months"]) for p in cur + early)
    page.add(answer("answer", 20, 440, 1240, 270, "Exercise 13.3", [
        f"(2) The (Blank) row holds the {ctx['blank']:,} lines of fiscal {y} that carry no promotion "
        f"({money(ctx['blank_rev'])} of revenue, no discount): a meaningful blank (Chapter 5), not a broken key.",
        f"(3) Lines invoiced after the promotion's end date: {after}. All of the late lines of "
        f"{cur[0]['short']} were ordered within its dates (Chapter 5): the discount is set when the order is priced, so "
        "invoicing later does not remove it.",
        f"(4) {bad['short']} ends on {bad['end']}, before it starts on {bad['start']}, so all {bad['n']} of its lines "
        f"fall after its end date. They were ordered in {' and '.join(bad['ordered'])}, its real season: a master-data "
        "error in the end date, not discounts given outside the promotion (the Part II case).",
        f"(5) In fiscal {y} the promotions gave away {money(ctx['total'])}: " +
        "; ".join(f"{p['short']} {money(p['disc'])}" for p in sorted(ctx["promos"], key=lambda p: -p["disc"])) +
        ". The report shows what each promotion cost and when, but not whether it paid off: that needs the margin given up "
        "against the volume it added (Chapter 7 and the Part II case)."]))
    top = cur[0]
    names = dict(rows("SELECT PromotionID, PromotionName FROM PromotionProgram"))
    peak = max(top["months"], key=lambda m: m["disc"])
    page.expect = ["PromotionName", "Count of SalesInvoiceLineID", money(peak["disc"]), "(Blank)",
                   f"Expanded {names[top['id']]}", "Model answer: Exercise 13.3"]

    t = "Exercise 13.3"
    fy = year_of(y)
    for p in ctx["promos"]:
        pid = f"PromotionProgram[PromotionID] = {p['id']}"
        for mth in p["months"]:
            month = f"SalesInvoice[Month] = \"{y}-{MONTHS.index(mth['name']) + 1:02d}\""
            b.check(t, f"promotion {p['id']} {mth['name']}: lines", mth["n"],
                    f"CALCULATE ( COUNTROWS ( SalesInvoiceLine ), {month}, {pid} )", 0)
            b.check(t, f"promotion {p['id']} {mth['name']}: discounts", round(mth["disc"], 2),
                    f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), {month}, {pid} )", 0.01)
        b.check(t, f"promotion {p['id']} ({p['short']}): discounts in fiscal {y}", round(p["disc"], 2),
                f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), {fy}, {pid} )", 0.01)
        b.check(t, f"promotion {p['id']}: lines invoiced after the end date", p["after"],
                f"COUNTROWS ( FILTER ( SalesInvoiceLine, RELATED ( SalesInvoice[FiscalYear] ) = {y} && "
                f"RELATED ( PromotionProgram[PromotionID] ) = {p['id']} && "
                "RELATED ( SalesInvoice[InvoiceDate] ) > RELATED ( PromotionProgram[EffectiveEndDate] ) ) )", 0)
    blank = "ISBLANK ( PromotionProgram[PromotionName] )"
    b.check(t, "(Blank) row: lines", ctx["blank"], f"CALCULATE ( COUNTROWS ( SalesInvoiceLine ), {fy}, {blank} )", 0)
    b.check(t, "(Blank) row: revenue", round(ctx["blank_rev"], 2), lt(fy, blank))
    b.check(t, "(Blank) row: discounts", 0, f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), {fy}, {blank} )", 0.005)
    b.check(t, f"discounts in fiscal {y}", round(ctx["total"], 2),
            f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), {fy} )", 0.01)
    b.check(t, f"promotions with fiscal {y} lines that end before they start", names[bad["id"]],
            "CALCULATE ( CONCATENATEX ( FILTER ( VALUES ( PromotionProgram[PromotionID] ), "
            "CALCULATE ( COUNTROWS ( SalesInvoiceLine ) ) > 0 && CALCULATE ( MAX ( PromotionProgram[EffectiveEndDate] ) ) "
            "< CALCULATE ( MAX ( PromotionProgram[EffectiveStartDate] ) ) ), "
            f"CALCULATE ( MAX ( PromotionProgram[PromotionName] ) ), \", \" ), {fy} )")


def ex4(b: Build) -> None:
    ctx = ch13.ex4(b.data, claim)
    y = b.year
    seg, reg = col("Customer", "CustomerSegment"), col("Customer", "Region")
    page = b.report.add(Page("ex134", "Ex 13.4"))
    page.add(slicer("regionSlicer", 20, 20, 260, 64, reg, style="dropdown", title="Region"))
    page.add(card("discountCard", 300, 20, 340, 64, [(DA, "Discounts")], units_none=True,
                  title=f"Promotional discounts, fiscal {y} (the segment selected in the bar chart)"))
    page.add(Visual("segmentBars", "clusteredBarChart", 20, 100, 620, 300, {"Category": [seg], "Y": [LT]},
                    title=f"Revenue by customer segment, fiscal {y}", sort=[(LT, "Descending")],
                    objects=labels(), alt_text=f"Revenue by customer segment in fiscal {y}, sorted from the largest. "
                                               "Wholesale is the largest segment, well ahead of Strategic; Small "
                                               "Business and Design Services are the smallest."))
    page.add(Visual("segmentMatrix", "pivotTable", 660, 20, 600, 380,
                    {"Rows": [seg], "Columns": [reg], "Values": [LT]},
                    title=f"Revenue by segment and region, fiscal {y}"))
    fy_filter = keep("ex134Year", FY, [y])
    page.extra = {"filterConfig": {"filters": [fy_filter]},
                  "visualInteractions": [{"source": "segmentBars", "target": "segmentMatrix", "type": "NoFilter"}]}
    segs = ctx["segments"]
    zero = [s["name"] for s in segs if s["disc"] == 0]
    page.add(answer("answer", 20, 420, 1240, 290, "Exercise 13.4", [
        "(1) Cognitive fit: in meetings the manager compares segments and regions at a glance, a spatial task the bar "
        "chart fits; on calls the manager quotes exact figures, a symbolic task the matrix fits.",
        f"(2) Fiscal {y} by segment: " + "; ".join(f"{s['name']} {money(s['rev'])} ({s['customers']} customers; "
                                                  f"discounts {money(s['disc'])})" for s in segs) +
        ". By region: " + "; ".join(f"{r} {money(v)}" for r, v in ctx["regions"]) +
        f". The largest cell is {ctx['cell']['segment']} in the {ctx['cell']['region']}, {money(ctx['cell']['rev'])}.",
        "(3) By default, clicking a bar cross-highlights the matrix and filters the card to that segment. With Format > "
        "Edit interactions set to None on the matrix, the bar chart still filters the card but the matrix stays whole: "
        "better when the manager wants one segment's discounts beside the full table of exact figures. " +
        (f"{zero[0]} received no discounts: services carry no promotion." if zero else ""),
        "(4) Region is a choice the manager makes while reading, so it belongs in a slicer the manager can see. The "
        f"fiscal year is fixed for the page, so it sits in Filters on this page and every title says fiscal {y}; a "
        "restriction such as leaving out the Design Services segment from a merchandise page would also belong in the "
        "Filters pane, stated in the titles.",
        "(5) Each visual has a title that says what it shows and for which period, and the bar chart has alternative "
        "text."]))
    page.expect = [f"Revenue by customer segment, fiscal {y}", f"Revenue by segment and region, fiscal {y}",
                   money(ctx["cell"]["rev"]), money(segs[0]["rev"]), money(sum(s["disc"] for s in segs))]

    t = "Exercise 13.4"
    fy = year_of(y)
    for s in segs:
        sf = f"Customer[CustomerSegment] = \"{s['name']}\""
        b.check(t, f"{s['name']} revenue", round(s["rev"], 2), lt(fy, sf))
        b.check(t, f"{s['name']} customers with revenue", s["customers"],
                f"CALCULATE ( DISTINCTCOUNT ( SalesInvoice[CustomerID] ), {fy}, {sf} )", 0)
        b.check(t, f"{s['name']} discounts", round(s["disc"], 2),
                f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), {fy}, {sf} )", 0.01)
    for r_, v in ctx["regions"]:
        b.check(t, f"{r_} revenue", round(v, 2), lt(fy, f"Customer[Region] = \"{r_}\""))
    c = ctx["cell"]
    b.check(t, f"largest cell: {c['segment']} in the {c['region']}", round(c["rev"], 2),
            lt(fy, f"Customer[CustomerSegment] = \"{c['segment']}\"", f"Customer[Region] = \"{c['region']}\""))
    b.check(t, "largest cell (the maximum over segments and regions)", round(c["rev"], 2),
            f"CALCULATE ( MAXX ( CROSSJOIN ( VALUES ( Customer[CustomerSegment] ), VALUES ( Customer[Region] ) ), "
            f"CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ) ) ), {fy} )")


def ex5(b: Build) -> None:
    ctx = ch13.ex5(b.data, claim)
    # (1) the four Tables again with every column, Discount and FreightAmount corrected, Enable load cleared
    for name, number, table, fix in [("Profile_Lines", 17, "SalesInvoiceLine", {"Discount": "type number"}),
                                     ("Profile_Invoices", 16, "SalesInvoice", {"FreightAmount": "type number"}),
                                     ("Profile_Items", 44, "Item", None), ("Profile_Customers", 4, "Customer", None)]:
        b.model.stage(Query.navigator(name, b.xlsx, number, table, corrections=fix))
    top, n, inv = ch13.TOP_ROWS, ctx["n"], ctx["invoices"]
    share = lambda k, of: f"{k:,} ({k / of:.1%})"
    page = b.report.add(Page("ex135", "Ex 13.5", height=900))
    left = [
        "Profile of the four sales Tables, CharlesRiver.xlsx, as Power Query profiles them: on the top "
        f"{top:,} rows (the default) and on the entire data set. Empty = null in Column quality; distinct = Column "
        "distribution.", "",
        (f"Profile_Lines ({n:,} rows)", True),
        f"PromotionID empty: {share(ctx['promo'], n)} on the entire data set; {ctx['top_empty']:.0%} of the top {top:,}.",
        f"PriceOverrideApprovalID empty: {share(ctx['override'], n)}; {ctx['override_top']:,} of the top {top:,}.",
        f"PriceListLineID and ShipmentLineID empty: {share(ctx['base'], n)} (the Base List design-service lines); "
        f"{ctx['base_top']} of the top {top:,}.",
        f"PricingMethod: {ctx['methods']} distinct values on both bases. Discount: {ctx['discounts']} distinct on the "
        f"entire data set, {ctx['discounts_top']} (zero) on the top {top:,}.",
        f"Quantity is fractional on {ctx['fractional']:,} lines (Chapter 5's validity check).", "",
        (f"Profile_Invoices ({inv:,} rows)", True),
        f"PaymentDate empty: {share(ctx['unpaid'], inv)} ({ctx['unpaid_open']:,} open invoices, {ctx['unpaid_settled']} "
        f"Settled); {ctx['unpaid_top']} of the top {top:,}.",
        f"Status: {len(ctx['statuses'])} distinct ({', '.join(ctx['statuses'])}); {len(ctx['top_statuses'])} "
        f"({', '.join(ctx['top_statuses'])}) on the top {top:,}.", "",
        (f"Profile_Items ({ctx['items']:,} rows; {ctx['sellable']} with a ListPrice)", True),
        f"ListPrice empty on {ctx['unpriced']} items (bought, not sold). CollectionName empty on {ctx['blank']} of the "
        f"sellable items (all {ctx['acc']} Accessories, {ctx['fur']} Furniture, the {ctx['svc']} services).", "",
        (f"Profile_Customers ({ctx['customers']} rows)", True),
        f"No empty values. CustomerName has {ctx['names']} distinct values ({' and '.join(ctx['dup'])} twice)."]
    right = [
        ("Why the first rows mislead", True),
        f"The top {top:,} rows are the earliest records: lines to {ctx['first_line']} and invoices to "
        f"{ctx['first_invoice']} (only {ctx['later_lines']} later lines and {ctx['later_invoices']} later invoices are "
        "dated earlier). They predate the first promotion, and almost every invoice among them is paid, so Discount, "
        "PromotionID, PaymentDate, and Status look far cleaner and simpler than the Tables are. Overrides already occur "
        f"({(top - ctx['override_top']) / top:.1%} of the top {top:,} against {(n - ctx['override']) / n:.1%} overall).",
        "Columns whose profile changes materially: PromotionID, Discount, PriceOverrideApprovalID, PriceListLineID, "
        "ShipmentLineID, PaymentDate, and Status. Switch the status bar to Column profiling based on entire data set "
        "before relying on a profile.", "",
        ("Blanks", True),
        "PromotionID: a meaningful blank (no promotion). PaymentDate: a meaningful blank (unpaid), but the Settled "
        "invoices without one are a matter for follow-up. PriceListLineID on Base List lines: meaningful (design "
        f"services are priced from the base list). CollectionName on the {ctx['fur_word']} Furniture items: follow-up "
        f"(the Part II case found one of them, {ctx['item']}, ordered under the {ctx['collection']} promotion).", "",
        ("Conclusion for the file", True),
        "The four Tables are complete and keyed (every line finds its invoice, item, and customer). The blanks are "
        "explained except the ones marked for follow-up, Quantity is fractional, and two customer names belong to two "
        "customers each, so the report groups by key."]
    page.add(answer("memo", 20, 20, 610, 860, "Exercise 13.5, profile memo", left))
    page.add(textbox("memoRight", 650, 20, 610, 860, right, size=10))
    page.expect = ["Model answer: Exercise 13.5, profile memo", "Why the first rows mislead"]

    t = "Exercise 13.5"
    first = f"TOPN ( {top}, SalesInvoiceLine, SalesInvoiceLine[SalesInvoiceLineID], ASC )"
    b.check(t, "SalesInvoiceLine rows (the model's copy of Profile_Lines)", n, "COUNTROWS ( SalesInvoiceLine )", 0)
    b.check(t, "PromotionID empty, entire data set", ctx["promo"],
            "COUNTROWS ( FILTER ( SalesInvoiceLine, ISBLANK ( SalesInvoiceLine[PromotionID] ) ) )", 0)
    b.check(t, f"PromotionID empty, top {top:,}", round(ctx["top_empty"] * top),
            f"COUNTROWS ( FILTER ( {first}, ISBLANK ( SalesInvoiceLine[PromotionID] ) ) )", 0)
    b.check(t, "Discount distinct values, entire data set", ctx["discounts"],
            "DISTINCTCOUNT ( SalesInvoiceLine[Discount] )", 0)
    b.check(t, f"Discount distinct values, top {top:,}", ctx["discounts_top"],
            f"COUNTROWS ( DISTINCT ( SELECTCOLUMNS ( {first}, \"D\", SalesInvoiceLine[Discount] ) ) )", 0)
    b.check(t, "PricingMethod distinct values, entire data set", ctx["methods"],
            "DISTINCTCOUNT ( SalesInvoiceLine[PricingMethod] )", 0)
    b.check(t, f"PricingMethod distinct values, top {top:,}", ctx["methods"],
            f"COUNTROWS ( DISTINCT ( SELECTCOLUMNS ( {first}, \"P\", SalesInvoiceLine[PricingMethod] ) ) )", 0)
    b.check(t, "lines with a fractional Quantity", ctx["fractional"],
            "COUNTROWS ( FILTER ( SalesInvoiceLine, SalesInvoiceLine[Quantity] <> INT ( SalesInvoiceLine[Quantity] ) ) )", 0)
    b.check(t, "SalesInvoice rows", inv, "COUNTROWS ( SalesInvoice )", 0)
    b.check(t, f"last invoice date of the top {top:,} lines", ctx["first_line"],
            f"FORMAT ( MAXX ( {first}, RELATED ( SalesInvoice[InvoiceDate] ) ), \"yyyy-mm-dd\" )")
    b.check(t, "sellable items (Item rows)", ctx["sellable"], "COUNTROWS ( 'Item' )", 0)
    b.check(t, "Customer rows", ctx["customers"], "COUNTROWS ( Customer )", 0)
    b.check(t, "distinct customer names", ctx["names"], "DISTINCTCOUNT ( Customer[CustomerName] )", 0)
    # the Profile queries do not load, so their own figures (PaymentDate, Status, PriceOverrideApprovalID, ...) are
    # checked against the Tables in SQL here, and stated on the page
    claim(ctx["base"] == one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ShipmentLineID IS NULL"),
          "the lines without a shipment line are the Base List lines")


def ex6(b: Build) -> None:
    ctx = ch13.ex6(b.data, claim)
    y, first = b.year, b.data.F
    ig, month = col("Item", "ItemGroup"), col("SalesInvoice", "Month")
    avg = agg("SalesInvoiceLine", "Discount", "avg")
    # (1) the draft, exactly as described
    draft = b.report.add(Page("ex136d", "Ex 13.6 Draft"))
    draft.add(Visual("pie", "pieChart", 20, 20, 420, 320, {"Category": [ig], "Y": [LT]}, objects=labels(False),
                     filters=[keep("pieYear", FY, [y])]))
    draft.add(card("avgCard", 460, 20, 300, 120, [avg], title="Average discount", filters=[keep("avgCardYear", FY, [y])]))
    draft.add(Visual("monthLine", "lineChart", 20, 360, 620, 340, {"Category": [month], "Y": [LT]}))
    draft.add(Visual("combo", "lineClusteredColumnComboChart", 660, 360, 600, 340,
                     {"Category": [month], "Y": [LT], "Y2": [DA]},
                     filters=[keep("comboYear", FY, [y]), keep("comboNoServices", ig, ["Services"], exclude=True)]))
    draft.expect = ["Average discount", "Furniture", "Services", "LineTotal and DiscountAmount"]

    # (3) and (4) the revised page
    rev = b.report.add(Page("ex136r", "Ex 13.6 Revised", height=1180))
    rev.add(Visual("groupBars", "clusteredBarChart", 20, 20, 600, 260, {"Category": [ig], "Y": [LT]},
                   title=f"Revenue by item group, fiscal {y} (all item groups, including Services)",
                   sort=[(LT, "Descending")], objects=labels(), filters=[keep("groupBarsYear", FY, [y])],
                   alt_text=f"Revenue by item group in fiscal {y}, sorted from the largest, with data labels. Furniture "
                            "holds more than half of revenue; Services is the smallest group."))
    rev.add(card("discountCards", 640, 20, 620, 110, [(DA, "Promotional discounts"), (LA, "Revenue at list price")],
                 units_none=True, title=f"Promotional discounts beside revenue at list price, fiscal {y}",
                 filters=[keep("discountCardsYear", FY, [y])]))
    rev.add(Visual("yearColumns", "clusteredColumnChart", 640, 150, 620, 130, {"Category": [FY], "Y": [LT]},
                   title=f"Revenue by fiscal year, {first} to {y}", objects=labels(),
                   alt_text=f"Revenue by whole fiscal year from {first} to {y}, with data labels. Revenue grew "
                            "modestly from year to year."))
    rev.add(Visual("monthsFromZero", "lineChart", 20, 300, 620, 260, {"Category": [month], "Y": [LT]},
                   title=f"Monthly revenue, January {first} to December {y}, on an axis from zero",
                   objects=value_axis(start=0),
                   alt_text="Monthly revenue over three years on an axis from zero. The first month, the start-up "
                            "month, is far below the others; after it, revenue moves within a narrow band."))
    rev.add(Visual("oneAxis", "lineChart", 660, 300, 600, 260, {"Category": [month], "Y": [LT, DA]},
                   title=f"Revenue and promotional discounts by month, fiscal {y}, on one axis",
                   filters=[keep("oneAxisYear", FY, [y])],
                   alt_text=f"Revenue and promotional discounts by month in fiscal {y} on one axis. Even in the "
                            "month of the largest discounts, they were a small fraction of revenue."))
    sl = ctx["slices"]
    rev.add(answer("answer", 20, 580, 1240, 580, "Exercise 13.6, review notes", [
        ("(2) Review notes on the draft", True),
        f"Pie chart: a reader would try to rank the {ctx['n_slices']} slices, but the small ones cannot be ranked by "
        "eye without labels: " + "; ".join(f"{g} {pct(s)}" for g, s in sl) +
        ". Replace it with a bar chart sorted from the largest, with labels.",
        f"Average discount card: Average of Discount for fiscal {y} is {pct(ctx['avg'], 2)}, an unweighted average of "
        "line rates, in which a small line counts as much as a large one. Discount dollars over the dollars before "
        f"discount are {pct(ctx['ratio'], 2)} ({pct(ctx['of_list'], 2)} of list), and Furniture's average rate alone is "
        f"{pct(ctx['f_avg'], 2)}. The right figure is a ratio of totals, which needs a measure (Chapter 14); until then, "
        "show discount dollars and the list amount side by side.",
        f"Line chart: the default axis does not start at zero, and the start-up month (January {first}, "
        f"{money(ctx['start'])}, against {money(ctx['low'])} to {money(ctx['high'])} in the other months) makes "
        f"December {y} look {pct(ctx['growth'], 0)} higher. Whole years changed by " +
        " and ".join(spct(c) for c in ctx["changes"]) + ". Start the axis at zero and compare whole years.",
        "Line and clustered column chart: the discounts get their own axis and look comparable to revenue, although "
        f"they were {pct(ctx['peak']['share'])} of revenue in {ctx['peak']['month']} {y}, their largest month. Use one "
        "axis, or two charts with titles that name their scales.",
        f"Hidden filter: leaving out Services removes {money(ctx['services'])} ({pct(ctx['services_share'])}) of fiscal "
        f"{y} revenue from the chart without telling the reader. Remove it, or make it a visible slicer and say so in "
        "the title.",
        ("(3) and (4) The revised page", True),
        "Each element is replaced by an honest equivalent: a sorted bar chart with labels, the discount dollars beside "
        "revenue at list price (a discount rate needs a measure, Chapter 14), whole years and an axis from zero, "
        "revenue and discounts on one axis, and no hidden filter. Accessibility: every visual has a title that states "
        "what it shows and for which period, and alternative text; data labels carry the values, so no meaning rests on "
        "color; the report keeps the default theme, whose text meets the 4.5 to 1 contrast threshold."]))
    rev.expect = [f"Revenue by item group, fiscal {y} (all item groups, including Services)",
                  "Promotional discounts", money(ctx["services"]), "Model answer: Exercise 13.6, review notes"]

    t = "Exercise 13.6"
    fy = year_of(y)
    rev_y = lt(fy)
    for g, s in sl:
        group = lt(fy, f"'Item'[ItemGroup] = \"{g}\"")
        b.check(t, f"pie slice {g}", round(s, 6), f"DIVIDE ( {group}, {rev_y} )", 0.000005)
    b.check(t, "card: Average of Discount", round(ctx["avg"], 6),
            f"CALCULATE ( AVERAGE ( SalesInvoiceLine[Discount] ), {fy} )", 0.000005)
    b.check(t, "discount dollars over the dollars before discount", round(ctx["ratio"], 6),
            f"CALCULATE ( DIVIDE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SUMX ( SalesInvoiceLine, "
            f"SalesInvoiceLine[Quantity] * SalesInvoiceLine[UnitPrice] ) ), {fy} )", 0.000005)
    b.check(t, "discount dollars over revenue at list price", round(ctx["of_list"], 6),
            f"CALCULATE ( DIVIDE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SUM ( SalesInvoiceLine[ListAmount] ) ), "
            f"{fy} )", 0.000005)
    b.check(t, "Furniture's Average of Discount", round(ctx["f_avg"], 6),
            f"CALCULATE ( AVERAGE ( SalesInvoiceLine[Discount] ), {fy}, 'Item'[ItemGroup] = \"Furniture\" )", 0.000005)
    b.check(t, f"start-up month {first}-01", round(ctx["start"], 2), lt(f"SalesInvoice[Month] = \"{first}-01\""))
    other = (f"FILTER ( VALUES ( SalesInvoice[Month] ), SalesInvoice[Month] <> \"{first}-01\" && "
             f"VALUE ( LEFT ( SalesInvoice[Month], 4 ) ) >= {first} )")
    b.check(t, "smallest other month", round(ctx["low"], 2),
            f"MINX ( {other}, CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ) ) )")
    b.check(t, "largest other month", round(ctx["high"], 2),
            f"MAXX ( {other}, CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ) ) )")
    dec, jan = lt(f"SalesInvoice[Month] = \"{y}-12\""), lt(f"SalesInvoice[Month] = \"{first}-01\"")
    b.check(t, f"December {y} against the start-up month", round(ctx["growth"], 6), f"DIVIDE ( {dec}, {jan} ) - 1",
            0.000005)
    for i, c in enumerate(ctx["changes"]):
        yy = first + 1 + i
        b.check(t, f"fiscal {yy} against {yy - 1}", round(c, 6), f"DIVIDE ( {lt(year_of(yy))}, {lt(year_of(yy - 1))} ) - 1",
                0.000005)
    pm = f"{y}-{MONTHS.index(ctx['peak']['month']) + 1:02d}"
    b.check(t, f"discounts as a share of revenue, {pm}", round(ctx["peak"]["share"], 6),
            f"CALCULATE ( DIVIDE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SUM ( SalesInvoiceLine[LineTotal] ) ), "
            f"SalesInvoice[Month] = \"{pm}\" )", 0.000005)
    b.check(t, "Services revenue (what the hidden filter removes)", round(ctx["services"], 2),
            lt(fy, "'Item'[ItemGroup] = \"Services\""))
    shown = one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = "
                "l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID WHERE substr(si.InvoiceDate, 1, 4) = ? "
                "AND i.ItemGroup <> 'Services'", str(y))
    b.check(t, "the draft's combo chart total (Services left out)", round(shown, 2),
            lt(fy, "NOT 'Item'[ItemGroup] IN { \"Services\" }"))


EXERCISES = [("13.1", ex1), ("13.2", ex2), ("13.3", ex3), ("13.4", ex4), ("13.5", ex5), ("13.6", ex6)]
