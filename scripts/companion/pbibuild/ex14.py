"""Chapter 14 Exercises - Solutions.pbip: the instructor's solutions to the Power BI exercises of Chapter 14, built on a
copy of Charles River Reports at the end of Tutorial 14.3 (the reader's File > Save as copy).

Exercises 14.1 to 14.4 each get a report page named after them; Exercise 14.5 is the DAX query tab Ex 14.5 and
Exercise 14.6 the tab Control Totals, as the exercises ask. The measures each exercise asks for sit in a display folder
of the Key Measures table named after it; the DAX the text prints (Balance, Shipped Revenue, Revenue by Ship Date,
Units, Margin PQ, Volume Effect, and the two queries) is read from _exercises.qmd, so the file and the text cannot
drift. Exercise 14.6's temporary change to GL Amount is undone in the file; its effect is checked with the changed
formula written inline. Every value of an exercise's instructor note becomes a check; the expected values come from
facts/notes/ch14.py (read-only SQL) or SQL here.
"""

from __future__ import annotations

import re

from pbibuild.model import MEASURES_TABLE, Measure, Query, query_table
from pbibuild.pbir import Page, Visual, agg, col, lit, meas, textbox
from pbibuild.reports import (CH14, COUNT, MONEY, Build, claim, dax_blocks, definitions, keep, money, one, rows, slicer)
from notes import ch14  # noqa: E402  (facts/ is on the path once pbibuild.reports is imported)

EX = CH14 / "_exercises.qmd"
MONTHS = ch14.MONTHS
PCT1 = "0.0%"
M = lambda n: meas(MEASURES_TABLE, n)


def pct(x: float, places: int = 1) -> str:
    return f"{x * 100:.{places}f}%"


def spct(x: float, places: int = 1) -> str:
    return ("+" if x > 0 else "") + pct(x, places)


def signed(x: float) -> str:
    return ("+" if x > 0 else "") + money(x)


def answer(name: str, x, y, w, h, title: str, paragraphs: list) -> Visual:
    """The model answer to an exercise's written requirements, in a text box on its page."""
    return textbox(name, x, y, w, h, [(f"Model answer: {title}", True)] + paragraphs, size=10)


def add(b: Build, folder: str, items: list[tuple[str, str, str | None]]) -> None:
    """Measures in the Key Measures table, in the exercise's display folder."""
    mt = b.model.tables[MEASURES_TABLE]
    have = {m.name for m in mt.measures}
    for name, dax, fmt in items:
        assert name not in have, f"measure {name} exists already"
        mt.measures.append(Measure(name, dax, fmt, display_folder=folder))


def inline(name: str) -> str:
    """A measure the text prints inline, as `Name = expression`."""
    text = EX.read_text(encoding="utf-8")
    return re.search(r"`" + re.escape(name) + r" = ([^`]+)`", text).group(1).strip()


def block(kind: str, name: str) -> str:
    """The expression of a measure the text prints in a marked block."""
    found = dict(d for body in dax_blocks(EX, kind) for d in definitions(body))
    return found[name]


def matrix_rows_expanded(levels: list[dict]) -> dict:
    from pbibuild.pbir import _ref
    return {"expansionStates": [{"roles": ["Rows"], "levels": [
        {"queryRefs": [_ref(levels[0])[1]], "isCollapsed": False, "identityKeys": [levels[0]], "isPinned": True},
        {"queryRefs": [_ref(levels[1])[1]], "isCollapsed": True, "isPinned": True}]}]}


def flat(dax: str) -> str:
    return re.sub(r"\s+", " ", dax).strip()


# --- Exercise 14.1 ---------------------------------------------------------------------------------------------------

BALANCE_VARIANTS = {
    "Balance with Closes": "VAR AsOf = MAX ( 'Date'[Date] )\nRETURN\n    CALCULATE (\n"
                           "        SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ),\n        REMOVEFILTERS ( 'Date' ),\n"
                           "        'Date'[Date] <= AsOf\n    )",
    "Balance on GL Amount": "VAR AsOf = MAX ( 'Date'[Date] )\nRETURN\n    CALCULATE ( [GL Amount], REMOVEFILTERS ( 'Date' ), "
                            "'Date'[Date] <= AsOf )",
}
CONTRA = ("( Account[AccountType] IN { \"Asset\", \"Expense\" } && Account[NormalBalance] = \"Credit\" )\n"
          "            || ( Account[AccountType] IN { \"Liability\", \"Equity\", \"Revenue\" } "
          "&& Account[NormalBalance] = \"Debit\" )")


def ex1(b: Build) -> None:
    ctx = ch14.ex1(b.data, claim)
    y, first = b.year, b.data.F
    add(b, "Ex 14.1", [("Balance", block("measure", "Balance"), MONEY)] +
        [(n, d, MONEY) for n, d in BALANCE_VARIANTS.items()] +
        [("Contra Accounts", f"COUNTROWS (\n    FILTER (\n        Account,\n        {CONTRA}\n    )\n)", COUNT)])
    types = [col("Account", "AccountType"), col("Account", "AccountSubType")]
    page = b.report.add(Page("ex141", "Ex 14.1", height=820))
    page.add(slicer("monthEnd", 20, 20, 220, 64, col("Date", "YearMonth"), [f"{y}-12"], style="dropdown", single=True,
                    title="Month-end"))
    page.add(Visual("balanceMatrix", "pivotTable", 20, 100, 600, 340, {"Rows": types, "Values": [M("Balance")]},
                    title="Balance at the selected month-end, before that day's closing entries",
                    extra=matrix_rows_expanded(types), active=("Rows",)))
    page.add(Visual("variantsMatrix", "pivotTable", 640, 20, 620, 200,
                    {"Rows": [types[0]], "Values": [M("Balance"), M("Balance with Closes"), M("Balance on GL Amount")]},
                    title="Three balance measures at the selected month-end"))
    page.add(Visual("contraTable", "tableEx", 640, 240, 620, 200, {"Values": [
        col("Account", "AccountNumber"), col("Account", "AccountName"), types[0], col("Account", "NormalBalance"),
        M("Contra Accounts")]}, title="Accounts whose normal balance is opposite to the usual side for their type"))
    now, mid, fst, gl = ctx["now"], ctx["mid"], ctx["first"], ctx["gl"]
    by = lambda d: "; ".join(f"{k} {money(d[k])}" for k in ch14.TYPES)
    contra = [ctx["allowance"]["number"]] + ctx["depreciation"] + [ctx["equity_contra"]["number"]] + \
             [r["number"] for r in ctx["revenue"]]
    page.add(answer("answer", 20, 460, 1240, 350, "Exercise 14.1", [
        "(1) REMOVEFILTERS ( 'Date' ) removes the month in the filter context, so the balance can reach back to the "
        "first posting; 'Date'[Date] <= AsOf keeps every posting up to the last day of that month, because a balance is "
        "cumulative; the third argument leaves out a closing entry only when it is posted on the as-of day, so a "
        "year-end shows the pre-closing balances while the closes of earlier years, dated before it, still move "
        "their net income into retained earnings.",
        f"(2) At {y}-12: {by(now)}; total {money(ctx['total'])}. Revenue and expense together "
        f"{money(now['Revenue'] + now['Expense'])}, the net income of fiscal {y} with its sign reversed; "
        f"{money(ctx['liab'])} + {money(ctx['equity'])} + {money(ctx['ni'])} = {money(now['Asset'])}, Chapter 6's "
        "balance sheet.",
        f"(3) {y}-06: {by(mid)}. {first}-12: {by(fst)} (net income {money(ctx['ni_first'])}). Both total zero. The "
        f"revenue and expense accounts at June {y} hold six months only, because the closes of the earlier years are "
        "dated December 31 of those years, before the as-of date, so the measure keeps them and they zero the "
        "revenue and expense accounts at each year-end.",
        f"(4) With no filter on the closes, at {y}-12 equity is {money(ctx['kept_equity'])} and revenue and expense "
        f"are zero: a post-closing balance sheet, with fiscal {y}'s net income already in retained earnings. On GL "
        f"Amount, equity is {money(gl['Equity'])}, the opening equity only, and revenue ({money(gl['Revenue'])}) and "
        f"expense ({money(gl['Expense'])}) hold all {ctx['years']} years: it leaves out every close, so no year's "
        f"income ever reaches retained earnings. Assets are {money(now['Asset'])} in all three.",
        f"(5) {ctx['n_contra']} accounts, the contra accounts of Chapter 9: " + ", ".join(map(str, contra)) +
        ". Signing by NormalBalance would show accumulated depreciation as a positive amount and add it to the assets "
        "instead of deducting it, and add the contra revenue to revenue."]))
    page.expect = ["Balance with Closes", money(now["Asset"]), money(now["Equity"]), money(ctx["kept_equity"]),
                   ctx["allowance"]["name"], "Model answer: Exercise 14.1"]

    t = "Exercise 14.1"
    for label, asof, d in ((f"{y}-12", f"{y}-12", now), (f"{y}-06", f"{y}-06", mid), (f"{first}-12", f"{first}-12", fst)):
        for k in ch14.TYPES:
            b.check(t, f"Balance at {label}, {k}", round(d[k], 2),
                    f"CALCULATE ( [Balance], 'Date'[YearMonth] = \"{asof}\", Account[AccountType] = \"{k}\" )", 0.01)
        b.check(t, f"Balance at {label} totals zero", 0, f"CALCULATE ( [Balance], 'Date'[YearMonth] = \"{asof}\" )", 0.01)
    b.check(t, f"revenue and expense at {y}-12 = minus the net income of fiscal {y}", round(-ctx["ni"], 2),
            f"CALCULATE ( [Balance], 'Date'[YearMonth] = \"{y}-12\", Account[AccountType] IN {{ \"Revenue\", \"Expense\" }} )",
            0.01)
    b.check(t, f"... and equals Net Income of {y} (Tutorial 14.3)", round(ctx["ni"], 2),
            f"CALCULATE ( [Net Income], 'Date'[Year] = {y} )", 0.01)
    for measure, d in (("Balance with Closes", {"Equity": ctx["kept_equity"], "Revenue": 0.0, "Expense": 0.0,
                                                "Asset": now["Asset"]}),
                       ("Balance on GL Amount", {k: gl[k] for k in ("Equity", "Revenue", "Expense", "Asset")})):
        for k, v in d.items():
            b.check(t, f"{measure} at {y}-12, {k}", round(v, 2),
                    f"CALCULATE ( [{measure}], 'Date'[YearMonth] = \"{y}-12\", Account[AccountType] = \"{k}\" )", 0.01)
    b.check(t, "contra accounts", len(contra), "[Contra Accounts]", 0)
    b.check(t, "contra account numbers", ", ".join(map(str, sorted(contra))),
            f"CONCATENATEX ( FILTER ( Account, {flat(CONTRA)} ), Account[AccountNumber], \", \", "
            "Account[AccountNumber], ASC )")


# --- Exercise 14.2 ---------------------------------------------------------------------------------------------------

def ex2(b: Build) -> None:
    ctx = ch14.ex2(b.data, claim)
    m, y = b.model, b.year
    # (1) the shipment Tables, Enable load cleared
    headers = m.stage(Query.navigator("ShipmentHeaders", b.xlsx, 14, "Shipment").select(["ShipmentID", "ShipmentDate"]))
    lines = m.stage(Query.navigator("ShipmentLines", b.xlsx, 15, "ShipmentLine").select(["ShipmentLineID", "ShipmentID"]))
    # (2) and (5) the invoice lines again, with their invoice and shipment dates, and the CrossesYear flag
    q = (Query.navigator("ShippedLines", b.xlsx, 17, "SalesInvoiceLine")
         .select(["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "ShipmentLineID", "LineTotal"])
         .merge(b.query("SalesInvoice"), "SalesInvoiceID", "SalesInvoiceID", ["InvoiceNumber", "InvoiceDate"])
         .merge(lines, "ShipmentLineID", "ShipmentLineID", ["ShipmentID"])
         .merge(headers, "ShipmentID", "ShipmentID", ["ShipmentDate"])
         .types({"InvoiceDate": "type date", "ShipmentDate": "type date"})
         .custom("CrossesYear", "[ShipmentDate] <> null and Date.Year([ShipmentDate]) <> Date.Year([InvoiceDate])",
                 "type logical"))
    keys = ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "ShipmentLineID", "ShipmentID"]
    m.add(query_table(q, formats={"LineTotal": MONEY}, summarize={k: "none" for k in keys}))
    # (3) the relationships: Item and the invoice date active, the ship date inactive (the dashed line)
    m.relate("ShippedLines.ItemID", "Item.ItemID")
    m.relate("ShippedLines.InvoiceDate", "Date.Date")
    m.relate("ShippedLines.ShipmentDate", "Date.Date", active=False)
    # (4) the measures
    add(b, "Ex 14.2", [("Shipped Revenue", inline("Shipped Revenue"), MONEY),
                       ("Revenue by Ship Date", block("skip", "Revenue by Ship Date"), MONEY)])
    page = b.report.add(Page("ex142", "Ex 14.2", height=900))
    page.add(Visual("yearMatrix", "pivotTable", 20, 20, 620, 200,
                    {"Rows": [col("Date", "Year")], "Values": [M("Revenue"), M("Shipped Revenue"), M("Revenue by Ship Date")]},
                    title="Revenue by invoice date and by ship date"))
    sl = lambda c: col("ShippedLines", c)
    page.add(Visual("crossTable", "tableEx", 660, 20, 600, 520, {"Values": [
        sl("SalesInvoiceLineID"), sl("InvoiceNumber"), sl("InvoiceDate"), sl("ShipmentDate"),
        agg("ShippedLines", "LineTotal")]}, title="Invoice lines whose invoice date and ship date fall in different years",
        filters=[keep("crossTableFlag", sl("CrossesYear"), [True])], sort=[(sl("InvoiceDate"), "Ascending")]))
    late, early, ch12 = ctx["late"], ctx["early"], ctx["ch12"]
    yrs = b.data.years
    page.add(answer("answer", 20, 560, 1240, 330, "Exercise 14.2", [
        "(3) Date and ShippedLines are already related on InvoiceDate, and only one path between two tables can be "
        "active, so the ShipmentDate relationship is inactive (dashed) and works only where a measure calls it with "
        "USERELATIONSHIP.",
        "(4) Shipped Revenue equals the Validation page's revenue in each year (" +
        "; ".join(f"{yy} {money(v)}" for yy, v in zip(yrs, ctx["by_invoice"])) + "). By ship date: " +
        "; ".join(f"{yy} {money(v)}" for yy, v in zip(yrs, ctx["by_ship"])) +
        f"; (Blank) {money(ctx['blank'])}, the {ctx['n_services']} Services lines, which have no shipment, so the "
        f"inactive relationship finds no date for them. Both columns total {money(ctx['all'])}.",
        f"(5) {ctx['n_cross']} lines cross a year. Invoices issued after the year in which the goods shipped: " +
        "; ".join(f"{g['lines']} lines on {g['invoices']} invoices dated {g['first']} to {g['last'][5:]} for shipments "
                  f"of December {g['ship_year']} ({money(g['amount'])})" for g in late) +
        f": Chapter 12's revenue cutoff findings (it counts {ch12['n']} invoices, {money(ch12['sub'])}, for "
        f"{yrs[-2]}, by posting date, adding " + ", ".join(a["number"] for a in ctx["added"]) +
        ", which is dated in the earlier year and posted on " + ", ".join(a["posted"] for a in ctx["added"]) +
        "). Invoices dated before their shipment: " +
        "; ".join(f"{g['lines']} lines on {g['numbers']}, dated {g['dates']} and shipped {g['shipped']} "
                  f"({money(g['amount'])})" for g in early) +
        " (Chapter 12; their numbers carry the next year's prefix, Chapter 5).",
        "(6) Use the ship date for revenue: control passes at shipment or delivery, and every shipment is delivered in "
        "the year it ships. Invoice-date revenue misstates the years by the late invoices. Services have no ship date, so "
        "the report needs a rule for them (their invoice date) and should disclose it, with the invoice-date figures as "
        "a reconciliation."]))
    page.expect = ["Revenue by Ship Date", money(ctx["by_ship"][-1]), money(ctx["blank"]), "(Blank)",
                   early[0]["numbers"].split(" ")[0], "Model answer: Exercise 14.2"]

    t = "Exercise 14.2"
    for yy, inv, shp in zip(yrs, ctx["by_invoice"], ctx["by_ship"]):
        b.check(t, f"{yy} Shipped Revenue", round(inv, 2), f"CALCULATE ( [Shipped Revenue], 'Date'[Year] = {yy} )", 0.01)
        b.check(t, f"{yy} Shipped Revenue = the Validation page's revenue", 0,
                f"CALCULATE ( [Shipped Revenue] - [Revenue], 'Date'[Year] = {yy} )", 0.01)
        b.check(t, f"{yy} Revenue by Ship Date", round(shp, 2),
                f"CALCULATE ( [Revenue by Ship Date], 'Date'[Year] = {yy} )", 0.01)
    b.check(t, "(Blank) row: revenue with no ship date", round(ctx["blank"], 2),
            "CALCULATE ( [Shipped Revenue], ISBLANK ( ShippedLines[ShipmentDate] ) )", 0.01)
    b.check(t, "lines with no ship date", ctx["n_services"],
            "CALCULATE ( COUNTROWS ( ShippedLines ), ISBLANK ( ShippedLines[ShipmentDate] ) )", 0)
    b.check(t, "... all of them Services", ctx["n_services"],
            "CALCULATE ( COUNTROWS ( ShippedLines ), ISBLANK ( ShippedLines[ShipmentDate] ), "
            "'Item'[ItemGroup] = \"Services\" )", 0)
    for yy, s in zip(yrs, ctx["by_services"]):
        b.check(t, f"{yy} Services revenue", round(s, 2),
                f"CALCULATE ( [Shipped Revenue], 'Date'[Year] = {yy}, 'Item'[ItemGroup] = \"Services\" )", 0.01)
    b.check(t, "Revenue by Ship Date in all", round(ctx["all"], 2), "[Revenue by Ship Date]", 0.01)
    b.check(t, "lines with a shipment", ctx["n_shipped"],
            "CALCULATE ( COUNTROWS ( ShippedLines ), NOT ISBLANK ( ShippedLines[ShipmentDate] ) )", 0)
    b.check(t, "lines that cross a year (CrossesYear)", ctx["n_cross"],
            "CALCULATE ( COUNTROWS ( ShippedLines ), ShippedLines[CrossesYear] = TRUE () )", 0)
    kinds = [(f"invoiced in {g['ship_year'] + 1} for {g['ship_year']} shipments", g,
              f"YEAR ( ShippedLines[ShipmentDate] ) = {g['ship_year']} && YEAR ( ShippedLines[InvoiceDate] ) = "
              f"{g['ship_year'] + 1}") for g in late] + \
            [(f"dated before their {g['shipped'][:4]} shipment", g,
              f"YEAR ( ShippedLines[ShipmentDate] ) = {g['shipped'][:4]} && YEAR ( ShippedLines[InvoiceDate] ) = "
              f"{int(g['shipped'][:4]) - 1}") for g in early]
    for label, g, cond in kinds:
        rows_ = f"FILTER ( ShippedLines, ShippedLines[CrossesYear] && {cond} )"
        b.check(t, f"{label}: lines", g["lines"], f"COUNTROWS ( {rows_} )", 0)
        b.check(t, f"{label}: invoices", g["invoices"],
                f"COUNTROWS ( SUMMARIZE ( {rows_}, ShippedLines[SalesInvoiceID] ) )", 0)
        b.check(t, f"{label}: amount", round(g["amount"], 2), f"SUMX ( {rows_}, ShippedLines[LineTotal] )", 0.01)


# --- Exercise 14.3 ---------------------------------------------------------------------------------------------------

PY_FIRST = "CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )"      # Revenue PY as first written


def ex3(b: Build) -> None:
    ctx = ch14.ex3(b.data, claim)
    y = b.year
    # (1) the measures; (5) Revenue PY as changed, blank wherever Revenue is blank; (4) the line count
    add(b, "Ex 14.3", [
        ("Revenue PY", f"IF (\n    NOT ISBLANK ( [Revenue] ),\n    {PY_FIRST}\n)", MONEY),
        ("Revenue YoY %", "DIVIDE ( [Revenue] - [Revenue PY], [Revenue PY] )", PCT1),
        ("Revenue YTD", "TOTALYTD ( [Revenue], 'Date'[Date] )", MONEY),
        ("Revenue PY YTD", "CALCULATE ( [Revenue YTD], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )", MONEY),
        ("YTD Change %", "DIVIDE ( [Revenue YTD] - [Revenue PY YTD], [Revenue PY YTD] )", PCT1),
        ("Group Lines", "COUNTROWS ( SalesInvoiceLine )", COUNT)])
    ig, ym, yr = col("Item", "ItemGroup"), col("Date", "YearMonth"), col("Date", "Year")
    page = b.report.add(Page("ex143", "Ex 14.3", height=1100))
    page.add(Visual("yoyMatrix", "pivotTable", 20, 20, 1240, 200, {"Rows": [ig], "Columns": [ym],
                                                                   "Values": [M("Revenue YoY %")]},
                    title=f"Revenue against the same month of the prior year, by item group, fiscal {y}",
                    filters=[keep("yoyMatrixYear", yr, [y])]))
    page.add(Visual("ytdTable", "tableEx", 20, 240, 760, 220,
                    {"Values": [ig, M("Revenue YTD"), M("Revenue PY YTD"), M("YTD Change %")]},
                    title=f"Year to date at December {y} against the prior year to date",
                    filters=[keep("ytdTableMonth", ym, [f"{y}-12"])]))
    page.add(Visual("pyTable", "tableEx", 800, 240, 460, 220, {"Values": [yr, M("Revenue"), M("Revenue PY")]},
                    title="Revenue and Revenue PY by year, no filter (Revenue PY as changed)"))
    page.add(Visual("linesMatrix", "pivotTable", 20, 480, 1240, 200, {"Rows": [ig], "Columns": [ym],
                                                                     "Values": [M("Group Lines")]},
                    title=f"Invoice lines by item group and month, fiscal {y}",
                    filters=[keep("linesMatrixYear", yr, [y])]))
    mo = {x["name"]: x for x in ctx["months"]}
    lo, hi = mo[ctx["low"]], mo[ctx["high"]]
    sv, tx = ctx["services"], ctx["textiles"]
    ytd = ctx["ytd"]
    turn = next((i for i, v in enumerate(ytd) if v < 0), None)
    page.add(answer("answer", 20, 700, 1240, 390, "Exercise 14.3", [
        f"(2) Furniture against the prior year: " + "; ".join(f"{x['name'][:3]} {spct(x['yoy'])}" for x in ctx["months"]) +
        f". The largest decline is {ctx['low']} ({money(lo['now'])} against {money(lo['before'])}), the largest increase "
        f"{ctx['high']} ({money(hi['now'])} against {money(hi['before'])}). Both equal Exercise 11.2's ledger figures; in "
        f"{y} the ledger differs from the lines only in January, by {ctx['crossing']}, dated in December {y - 1} and "
        "posted in January.",
        f"(3) At December {y}, year to date against the prior year to date: " +
        "; ".join(f"{g['group']} {money(g['now'])} against {money(g['before'])} ({spct(g['now'] / g['before'] - 1)})"
                  for g in ctx["by_group"]) +
        f"; total {money(ctx['now_total'])} against {money(ctx['before_total'])} "
        f"({spct(ctx['now_total'] / ctx['before_total'] - 1)}). Grew: " +
        ", ".join(g["group"] for g in ctx["by_group"] if g["now"] > g["before"]) + "; shrank: " +
        ", ".join(g["group"] for g in ctx["by_group"] if g["now"] < g["before"]) +
        f". Furniture's year-to-date change is {ctx['ytd_sign']} from January to September" +
        (f" and turns negative in {MONTHS[turn]}" if turn is not None else "") + f", ending at {spct(ytd[-1])}.",
        f"(4) Services swings the most ({spct(sv['low'])} in {sv['low_month']}, {spct(sv['high'])} in "
        f"{sv['high_month']}); Textiles next ({spct(tx['low'])} in {tx['low_month']}, {spct(tx['high'])} in "
        f"{tx['high_month']}). Services bills {ctx['lines_low']} to {ctx['lines_high']} lines a month to "
        f"{ctx['cust_low']} to {ctx['cust_high']} customers ({ctx['customers']} in the year), and one design-service "
        f"line of up to {money(ctx['largest'])} ({ctx['largest_month']}) moves a month's total, so a percentage change "
        "measures a handful of engagements, not a trend.",
        f"(5) Without the change, the {y + 1} row showed Revenue PY of {money(ctx['now_total'])} and no revenue, because "
        f"the Date table runs through {y + 1} and SAMEPERIODLASTYEAR finds fiscal {y}. Revenue PY now returns blank "
        "wherever Revenue is blank: IF ( NOT ISBLANK ( [Revenue] ), CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( "
        "'Date'[Date] ) ) )."]))
    # a matrix with one value shows no value header, so its title and values prove it rendered
    page.expect = [f"Revenue against the same month of the prior year, by item group, fiscal {y}", pct(lo["yoy"]),
                   "Revenue PY YTD", money(next(g["before"] for g in ctx["by_group"] if g["group"] == "Furniture")),
                   f"Invoice lines by item group and month, fiscal {y}", "Model answer: Exercise 14.3"]

    t = "Exercise 14.3"
    furn = "'Item'[ItemGroup] = \"Furniture\""
    month = lambda i, yy=y: f"'Date'[YearMonth] = \"{yy}-{i + 1:02d}\""
    for i, x in enumerate(ctx["months"]):
        b.check(t, f"Furniture Revenue YoY % {y}-{i + 1:02d}", round(x["yoy"], 6),
                f"CALCULATE ( [Revenue YoY %], {month(i)}, {furn} )", 0.000005)
        b.check(t, f"Furniture YTD Change % {y}-{i + 1:02d}", round(ytd[i], 6),
                f"CALCULATE ( [YTD Change %], {month(i)}, {furn} )", 0.000005)
        if x["detail"]:
            b.check(t, f"Furniture Revenue {y}-{i + 1:02d}", round(x["now"], 2),
                    f"CALCULATE ( [Revenue], {month(i)}, {furn} )", 0.01)
            b.check(t, f"Furniture Revenue PY {y}-{i + 1:02d}", round(x["before"], 2),
                    f"CALCULATE ( [Revenue PY], {month(i)}, {furn} )", 0.01)
    # Exercise 11.2 took the change from the ledger (4010, the closes left out)
    for x in ctx["extremes"]:
        i = MONTHS.index(x["name"])
        led = lambda yy: one("SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                             "WHERE a.AccountNumber = 4010 AND substr(g.PostingDate, 1, 7) = ? AND " + b.data.no_closes(),
                             f"{yy}-{i + 1:02d}")
        b.check(t, f"Furniture {x['name']} {y} from the ledger (4010, Exercise 11.2)", round(led(y) / led(y - 1) - 1, 6),
                f"DIVIDE ( CALCULATE ( [P&L Amount], Account[AccountNumber] = 4010, {month(i)} ), CALCULATE ( "
                f"[P&L Amount], Account[AccountNumber] = 4010, {month(i, y - 1)} ) ) - 1", 0.000005)
    dec = month(11)
    for g in ctx["by_group"]:
        gf = f"'Item'[ItemGroup] = \"{g['group']}\""
        b.check(t, f"{g['group']} Revenue YTD at {y}-12", round(g["now"], 2), f"CALCULATE ( [Revenue YTD], {dec}, {gf} )", 0.01)
        b.check(t, f"{g['group']} Revenue PY YTD at {y}-12", round(g["before"], 2),
                f"CALCULATE ( [Revenue PY YTD], {dec}, {gf} )", 0.01)
    b.check(t, f"Revenue YTD at {y}-12, total", round(ctx["now_total"], 2), f"CALCULATE ( [Revenue YTD], {dec} )", 0.01)
    b.check(t, f"Revenue PY YTD at {y}-12, total", round(ctx["before_total"], 2), f"CALCULATE ( [Revenue PY YTD], {dec} )",
            0.01)
    for name, s in (("Services", sv), ("Textiles", tx)):
        gf = f"'Item'[ItemGroup] = \"{name}\""
        for which in ("low", "high"):
            i = MONTHS.index(s[f"{which}_month"])
            b.check(t, f"{name} Revenue YoY % {y}-{i + 1:02d} ({which})", round(s[which], 6),
                    f"CALCULATE ( [Revenue YoY %], {month(i)}, {gf} )", 0.000005)
    svc = f"'Date'[Year] = {y}, 'Item'[ItemGroup] = \"Services\""
    each = "VALUES ( 'Date'[YearMonth] )"
    b.check(t, "Services Group Lines, fewest in a month", ctx["lines_low"], f"CALCULATE ( MINX ( {each}, [Group Lines] ), {svc} )", 0)
    b.check(t, "Services Group Lines, most in a month", ctx["lines_high"], f"CALCULATE ( MAXX ( {each}, [Group Lines] ), {svc} )", 0)
    cust = "CALCULATE ( DISTINCTCOUNT ( SalesInvoiceLine[CustomerID] ) )"
    b.check(t, "Services customers, fewest in a month", ctx["cust_low"], f"CALCULATE ( MINX ( {each}, {cust} ), {svc} )", 0)
    b.check(t, "Services customers, most in a month", ctx["cust_high"], f"CALCULATE ( MAXX ( {each}, {cust} ), {svc} )", 0)
    b.check(t, "Services customers in the year", ctx["customers"],
            f"CALCULATE ( DISTINCTCOUNT ( SalesInvoiceLine[CustomerID] ), {svc} )", 0)
    li = MONTHS.index(ctx["largest_month"])
    b.check(t, f"largest Services line ({ctx['largest_month']})", round(ctx["largest"], 2),
            f"CALCULATE ( MAX ( SalesInvoiceLine[LineTotal] ), {svc}, {month(li)} )")
    b.check(t, f"{y + 1}: Revenue PY as first written (the row the exercise explains)", round(ctx["now_total"], 2),
            f"CALCULATE ( {PY_FIRST}, 'Date'[Year] = {y + 1} )", 0.01)
    b.check(t, f"{y + 1}: Revenue PY as changed is blank", "blank",
            f"IF ( ISBLANK ( CALCULATE ( [Revenue PY], 'Date'[Year] = {y + 1} ) ), \"blank\", \"not blank\" )")
    b.check(t, f"{y + 1}: Revenue is blank", "blank",
            f"IF ( ISBLANK ( CALCULATE ( [Revenue], 'Date'[Year] = {y + 1} ) ), \"blank\", \"not blank\" )")


# --- Exercise 14.4 ---------------------------------------------------------------------------------------------------

EFFECTS = {
    "Mix Effect": ("ListMarginPerUnit", "DIVIDE ( [List Amount] - [Standard Cost], [Units] )",
                   "[Units] * ( ListMarginPerUnit - ListMarginPerUnitPQ )"),
    "Price List Effect": ("ReductionPerUnit", "DIVIDE ( [List Amount] - [Revenue] - [Discounts], [Units] )",
                          "- [Units] * ( ReductionPerUnit - ReductionPerUnitPQ )"),
    "Promotion Effect": ("DiscountPerUnit", "DIVIDE ( [Discounts], [Units] )",
                         "- [Units] * ( DiscountPerUnit - DiscountPerUnitPQ )"),
}
BRIDGE = ["Margin PQ", "Volume Effect", "Mix Effect", "Price List Effect", "Promotion Effect", "Gross Margin",
          "Bridge Check"]


def effect(var: str, per_unit: str, result: str) -> str:
    """An effect written in the same way as the text's Volume Effect (cells B18 to B20 of Tutorial 6.3)."""
    return ("VAR PriorQuarter = DATEADD ( 'Date'[Date], -1, QUARTER )\n"
            f"VAR {var} = {per_unit}\n"
            f"VAR {var}PQ =\n    CALCULATE ( {per_unit}, PriorQuarter )\n"
            f"RETURN\n    {result}")


def ex4(b: Build) -> None:
    ctx = ch14.ex4(b.data, claim)
    y = b.year
    add(b, "Ex 14.4", [("Units", inline("Units"), "#,0.00"), ("Margin PQ", inline("Margin PQ"), MONEY),
                       ("Volume Effect", block("skip", "Volume Effect"), MONEY)] +
        [(n, effect(*parts), MONEY) for n, parts in EFFECTS.items()] +
        [("Bridge Check", "[Margin PQ] + [Volume Effect] + [Mix Effect] + [Price List Effect]\n"
                          "    + [Promotion Effect] - [Gross Margin]", MONEY)])
    page = b.report.add(Page("ex144", "Ex 14.4", height=820))
    for i, group in enumerate(["Furniture", "Lighting"]):
        page.add(Visual(f"bridge{group}", "pivotTable", 20, 20 + i * 230, 1240, 210,
                        {"Rows": [col("Date", "YearQuarter")], "Values": [M(n) for n in BRIDGE]},
                        title=f"{group} margin bridge by quarter, fiscal {y}",
                        filters=[keep(f"bridge{group}Year", col("Date", "Year"), [y]),
                                 keep(f"bridge{group}Group", col("Item", "ItemGroup"), [group])]))
    qs, lt = ctx["quarters"], ctx["lighting"]
    q3, q4 = qs[2], qs[3]
    fmt = lambda q: (f"Margin PQ {money(q['pq'])}, volume {signed(q['volume'])}, mix {signed(q['mix'])}, price lists "
                     f"{signed(q['lists'])}, promotions {signed(q['promotions'])}, margin {money(q['gm'])}")
    page.add(answer("answer", 20, 480, 1240, 330, "Exercise 14.4", [
        f"(4) Furniture {y}: " + "; ".join(f"{q['label']}: {fmt(q)}" for q in qs) +
        ". The Q4 row reproduces Chapter 6's bridge, and Bridge Check is zero in every row.",
        "(3) Each item has one StandardCost, so the cost per unit changes only with the mix, which the mix effect "
        "already includes (Chapter 6); a cost effect would be zero.",
        f"(5) Q3: fewer units than in Q2 (volume {signed(q3['volume'])}) and the first month of promotion "
        f"{ctx['promotion']} ({ctx['start_month']}, promotions {signed(q3['promotions'])}) together explain the fall. "
        f"Q4: volume, mix, and price lists are small, and the promotion effect ({signed(q4['promotions'])}) is larger "
        "than the whole decline.",
        f"(6) Lighting {y}-Q4: {money(lt['pq'])} to {money(lt['gm'])}; volume {signed(lt['volume'])}, mix "
        f"{signed(lt['mix'])}, price lists {signed(lt['lists'])}, promotions {signed(lt['promotions'])}: a "
        f"{ctx['main']['name']} {ctx['main']['direction']}, not a price effect."]))
    page.expect = ["Price List Effect", "Bridge Check", signed(q4["promotions"]).lstrip("+"),
                   signed(lt["volume"]).lstrip("+"), "Model answer: Exercise 14.4"]

    t = "Exercise 14.4"
    keys = dict(zip(BRIDGE, ["pq", "volume", "mix", "lists", "promotions", "gm", "check"]))
    for group, quarters in (("Furniture", qs), ("Lighting", [dict(label="Q4", **lt)])):
        for q in quarters:
            where = f"'Date'[YearQuarter] = \"{y}-{q['label']}\", 'Item'[ItemGroup] = \"{group}\""
            for n, k in keys.items():
                b.check(t, f"{group} {y}-{q['label']} {n}", round(q[k], 2), f"CALCULATE ( [{n}], {where} )", 0.01)
            b.check(t, f"{group} {y}-{q['label']} Units", round(q["units"], 2), f"CALCULATE ( [Units], {where} )", 0.01)
    b.check(t, "Bridge Check, largest in any quarter of the window and item group", 0,
            "MAXX ( CROSSJOIN ( VALUES ( 'Date'[YearQuarter] ), VALUES ( 'Item'[ItemGroup] ) ), "
            "ABS ( CALCULATE ( [Bridge Check] ) ) )", 0.01)


# --- Exercise 14.5 ---------------------------------------------------------------------------------------------------

def ex5(b: Build) -> None:
    ctx = ch14.ex5(b.data, claim)
    y = b.year
    (q1,) = [q for q in dax_blocks(EX, "query") if "Customer Rows Both" in q]
    both = "CROSSFILTER ( SalesInvoiceLine[InvoiceDate], 'Date'[Date], BOTH )"
    q2 = (f"// (2) Operating expense by item group, fiscal {y}, with the relationship between\n"
          "// SalesInvoiceLine[InvoiceDate] and Date set to Both for the calculation\n"
          "EVALUATE\nSUMMARIZECOLUMNS (\n    ROLLUPADDISSUBTOTAL ( 'Item'[ItemGroup], \"All Groups\" ),\n"
          f"    TREATAS ( {{ {y} }}, 'Date'[Year] ),\n    \"Operating Expense\", [Operating Expense],\n"
          f"    \"Operating Expense Both\", CALCULATE ( [Operating Expense], {both} ),\n"
          f"    \"Dates Left\", CALCULATE ( COUNTROWS ( 'Date' ), {both} )\n)")
    q3 = (f"// (3) Shares of revenue by item group, fiscal {y}: REMOVEFILTERS ( 'Item' ) against\n"
          "// ALL ( SalesInvoiceLine ); the All Groups row adds up each column\n"
          "EVALUATE\nSUMMARIZECOLUMNS (\n    ROLLUPADDISSUBTOTAL ( 'Item'[ItemGroup], \"All Groups\" ),\n"
          f"    TREATAS ( {{ {y} }}, 'Date'[Year] ),\n    \"Share REMOVEFILTERS\", [Share of Revenue],\n"
          "    \"Share ALL\", DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALL ( SalesInvoiceLine ) ) )\n)")
    sv, others = ctx["services"], ctx["others"]
    inv = ", ".join(f"{x['group']} {x['n']}" for x in ctx["invoiced"])
    notes = [
        "Model answer, Exercise 14.5",
        f"(1) Customer Rows is {ctx['customers']} for every group: the Customer table, which a filter on Item or Date "
        "does not reach, because the filter flows from Customer to the lines, not back. Customers Invoiced is the "
        f"distinct count on the fact table ({inv}; {ctx['n_invoiced']} in all). Customer Rows Both equals Customers "
        "Invoiced: Both lets the lines filter Customer. A report uses the distinct count on the fact table; Both "
        "gives the same answer here but changes every measure that uses the relationship.",
        f"(2) Operating Expense is {money(ctx['opex'])} for every group. With Both on the Date relationship, a "
        "selection on Item filters Date to the days with an invoice of that group, and the ledger follows: " +
        "; ".join(f"{x['group']} {money(x['opex'])} ({x['days']} days)" for x in others) +
        f"; Services {money(sv['opex'])} ({sv['days']} days). The Services figure is the operating expense of the "
        f"{ctx['services_word']} days on which design services were invoiced, a number with no meaning: a selection in "
        "one fact table has filtered the other, as the Watch out on two fact tables warns.",
        "(3) REMOVEFILTERS: " + "; ".join(f"{s['group']} {pct(s['rf'], 2)}" for s in ctx["shares"]) +
        "; total 100%. ALL ( SalesInvoiceLine ): " + "; ".join(f"{s['group']} {pct(s['all'], 2)}" for s in ctx["shares"]) +
        f"; total {pct(ctx['all_total'], 2)}, the share of fiscal {y} in {ctx['years']} years of revenue "
        f"({money(ctx['every'])}), because ALL on the fact table removes the year as well.",
        "(4) Review list: relationships set to Both (compare a count with and without CROSSFILTER); a count taken from a "
        "dimension or header table (compare it with a distinct count on the facts); ALL on a fact table inside a share "
        "(the shares must total 100%); inactive relationships used without USERELATIONSHIP; (Blank) members (count the "
        "unmatched keys); measures that keep the closing entries (Exercise 14.6)."]
    comment = "\n".join("// " + line for n in notes for line in _wrap(n, 110))
    b.project.queries["Ex 14.5"] = "\n\n".join([q1, q2, q3, comment]) + "\n"
    _keep_checks_last(b)

    t = "Exercise 14.5"
    cy = f"'Date'[Year] = {y}"
    cross = "CROSSFILTER ( SalesInvoiceLine[CustomerID], Customer[CustomerID], BOTH )"
    for x in ctx["invoiced"]:
        g = f"'Item'[ItemGroup] = \"{x['group']}\""
        b.check(t, f"{x['group']}: Customer Rows", ctx["customers"], f"CALCULATE ( COUNTROWS ( Customer ), {cy}, {g} )", 0)
        b.check(t, f"{x['group']}: Customers Invoiced", x["n"],
                f"CALCULATE ( DISTINCTCOUNT ( SalesInvoiceLine[CustomerID] ), {cy}, {g} )", 0)
        b.check(t, f"{x['group']}: Customer Rows Both", x["n"], f"CALCULATE ( COUNTROWS ( Customer ), {cross}, {cy}, {g} )", 0)
    b.check(t, "customers invoiced in all", ctx["n_invoiced"],
            f"CALCULATE ( DISTINCTCOUNT ( SalesInvoiceLine[CustomerID] ), {cy} )", 0)
    for x in others + [sv]:
        g = f"'Item'[ItemGroup] = \"{x['group']}\""
        b.check(t, f"{x['group']}: Operating Expense", round(ctx["opex"], 2),
                f"CALCULATE ( [Operating Expense], {cy}, {g} )", 0.01)
        b.check(t, f"{x['group']}: Operating Expense Both", round(x["opex"], 2),
                f"CALCULATE ( [Operating Expense], {both}, {cy}, {g} )", 0.01)
        b.check(t, f"{x['group']}: dates left under Both", x["days"], f"CALCULATE ( COUNTROWS ( 'Date' ), {both}, {cy}, {g} )", 0)
    b.check(t, "all groups: Operating Expense Both", round(ctx["opex"], 2),
            f"CALCULATE ( [Operating Expense], {both}, {cy} )", 0.01)
    b.check(t, "all groups: dates left under Both", ctx["year_days"], f"CALCULATE ( COUNTROWS ( 'Date' ), {both}, {cy} )", 0)
    for s in ctx["shares"]:
        g = f"'Item'[ItemGroup] = \"{s['group']}\""
        b.check(t, f"{s['group']}: share with REMOVEFILTERS", round(s["rf"], 6),
                f"CALCULATE ( [Share of Revenue], {cy}, {g} )", 0.000005)
        b.check(t, f"{s['group']}: share with ALL ( SalesInvoiceLine )", round(s["all"], 6),
                f"CALCULATE ( DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALL ( SalesInvoiceLine ) ) ), {cy}, {g} )",
                0.000005)
    b.check(t, "shares with ALL ( SalesInvoiceLine ) add up to", round(ctx["all_total"], 6),
            f"CALCULATE ( SUMX ( VALUES ( 'Item'[ItemGroup] ), DIVIDE ( [Revenue], CALCULATE ( [Revenue], "
            f"ALL ( SalesInvoiceLine ) ) ) ), {cy} )", 0.000005)
    b.check(t, "shares with REMOVEFILTERS add up to", 1,
            f"CALCULATE ( SUMX ( VALUES ( 'Item'[ItemGroup] ), [Share of Revenue] ), {cy} )", 0.000001)


def _wrap(text: str, width: int) -> list[str]:
    import textwrap
    return textwrap.wrap(text, width) or [""]


def _keep_checks_last(b: Build) -> None:
    if "Checks" in b.project.queries:
        b.project.queries["Checks"] = b.project.queries.pop("Checks")


# --- Exercise 14.6 ---------------------------------------------------------------------------------------------------

def ex6(b: Build) -> None:
    ctx = ch14.ex6(b.data, claim)
    y = b.year
    (text,) = [q for q in dax_blocks(EX, "query") if "Control totals" in q]
    assert text.count('"Expected", 0,') == 2, "the Control Totals query no longer has two tests with an expected 0"
    accounts = ", ".join(ch14.REVENUE)
    ledger = (f"CALCULATE ( - [GL Amount], GLEntry[SourceDocumentType] = \"SalesInvoice\",\n"
              f"                Account[AccountNumber] IN {{ {accounts} }}, 'Date'[Year] = {y} )")
    tests = [
        (f"Net income, fiscal {y}", round(ctx["ni"], 2), f"CALCULATE ( [Net Income], 'Date'[Year] = {y} )"),
        ("Journal entry debits, all years", round(ctx["debits"], 2),
         "CALCULATE ( SUM ( GLEntry[Debit] ), GLEntry[SourceDocumentType] = \"JournalEntry\" )"),
        (f"Manufacturing variance (5080), fiscal {y}", round(ctx["variance"], 2),
         f"CALCULATE ( [GL Amount], Account[AccountNumber] = 5080, 'Date'[Year] = {y} )"),
        (f"Invoice revenue in the ledger, fiscal {y}", round(ctx["ledger"], 2), ledger),
        (f"Ledger less invoice lines = {ctx['numbers']}", round(sum(ctx["amounts"]), 2),
         f"{ledger}\n                - CALCULATE ( [Revenue], 'Date'[Year] = {y} )")]
    # (1) the expected values of the two tests the text prints, then one ROW per added test
    q = text.replace('"Expected", 0,', f'"Expected", {ctx["n"]},', 1).replace('"Expected", 0,', f'"Expected", {ctx["rev"]:.2f},', 1)
    added = "".join(f",\n        ROW ( \"Test\", \"{name}\", \"Expected\", {exp:.2f},\n            \"Actual\", {dax} )"
                    for name, exp, dax in tests)
    head, sep, tail = q.partition("\n    )\nRETURN")
    assert sep, "the Control Totals query no longer ends its UNION before RETURN"
    q = head + added + sep + tail
    notes = [
        f"(2) The ledger exceeds the invoice lines by {money(ctx['gap'])}: {ctx['numbers']} (" +
        " + ".join(money(a) for a in ctx["amounts"]) + f"), dated in late {y - 1} and posted on {y}-01-01 (Chapter 6, "
        "Exercise 6.1). A reconciling item is tested as its own expected difference, not left as a failure.",
        "(3) With GL Amount changed to keep the closing entries, the net income test and the 5080 test fail (both read "
        "0); the invoice lines, revenue, journal entry debits, invoice revenue in the ledger, the reconciling item, and "
        "Test 3's trial balance (which leaves out the two closes by VoucherNumber) still pass. The change was then "
        "undone, and every test passes again.",
        "(4) The tests show that the model's totals agree with earlier, independent calculations on the same "
        "database. They cannot show that individual rows are right, that the source data is complete or valid, or that "
        "a total no test covers is right. Run the library after every refresh and every change to the model, before "
        "the report is shared."]
    comment = "\n".join("// " + line for n in ["Model answer, Exercise 14.6"] + notes for line in _wrap(n, 110))
    b.project.queries["Control Totals"] = q + "\n\n" + comment + "\n"
    _keep_checks_last(b)

    t = "Exercise 14.6"
    b.check(t, f"Invoice lines, fiscal {y}", ctx["n"], f"CALCULATE ( [Invoice Lines], 'Date'[Year] = {y} )", 0)
    b.check(t, f"Revenue, fiscal {y}", round(ctx["rev"], 2), f"CALCULATE ( [Revenue], 'Date'[Year] = {y} )", 0.01)
    for name, exp, dax in tests:
        b.check(t, name, exp, flat(dax), 0.01)
    union = flat(q[q.index("UNION ("):q.index("\nRETURN")])
    b.check(t, "Control Totals: tests that fail", 0,
            f"COUNTROWS ( FILTER ( {union}, ABS ( [Actual] - [Expected] ) > 0.01 ) )", 0)
    b.check(t, "Control Totals: tests", 2 + len(tests), f"COUNTROWS ( {union} )", 0)
    b.check(t, "(3) GL Amount keeping the closes (changed, then undone): net income reads 0, the test fails", 0,
            f"CALCULATE ( SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] ), Account[AccountType] IN "
            f"{{ \"Revenue\", \"Expense\" }}, 'Date'[Year] = {y} )", 0.01)
    b.check(t, "(3) GL Amount keeping the closes (changed, then undone): 5080 reads 0, the test fails", 0,
            f"CALCULATE ( SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ), Account[AccountNumber] = 5080, "
            f"'Date'[Year] = {y} )", 0.01)
    b.check(t, "(3) GL Amount keeping the closes: invoice revenue in the ledger still passes", round(ctx["ledger"], 2),
            f"CALCULATE ( SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] ), GLEntry[SourceDocumentType] = "
            f"\"SalesInvoice\", Account[AccountNumber] IN {{ {accounts} }}, 'Date'[Year] = {y} )", 0.01)
    b.check(t, "the file keeps the tutorial's GL Amount (the change undone): 5080 in the ledger", round(ctx["variance"], 2),
            f"CALCULATE ( [GL Amount], Account[AccountNumber] = 5080, 'Date'[Year] = {y} )", 0.01)


EXERCISES = [("14.1", ex1), ("14.2", ex2), ("14.3", ex3), ("14.4", ex4), ("14.5", ex5), ("14.6", ex6)]
