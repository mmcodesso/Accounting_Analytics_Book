"""Chapter 15 Exercises - Solutions.pbip: the exercises of Chapter 15, built on a copy of Charles River Reports at the
end of Tutorial 15.3 (the reader's Save as copy).

Each function builds one exercise as a strong student would: its page (or drill-through page) named after it, its
measures in a display folder of the Key Measures table named after it, the Tables it imports under the query names it
gives, and a "Model answer" text box for the written requirements, built from computed values. The checks compare the
model with the values of the exercise's instructor note (facts/notes/ch15.py) and with read-only SQL. Visual
calculations and the Analytics-pane forecast are computed in the visual, so the engine cannot check them: the pages'
`expect` strings prove the visual calculations rendered, and the forecast is left to the reader, as the note says.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pbibuild.audit_monitoring import drillthrough
from pbibuild.model import MEASURES_TABLE, Column, Measure, Query, Table, query_table
from pbibuild.pbir import Page, Visual, col, lit, meas, textbox
from pbibuild.reports import (MONEY, Build, card, center_name, claim, keep, money, one, rows, sales, slicer)

from notes import ch15  # noqa: E402  (facts/ is on sys.path through pbibuild.reports)

KM = MEASURES_TABLE
M = lambda n: meas(KM, n)                 # noqa: E731
DIRECT, INDIRECT = "Direct Manufacturing", "Indirect Manufacturing"


def measure(b: Build, folder: str, name: str, dax: str, fmt: str | None = None, table: str = KM) -> None:
    b.model.tables[table].measures.append(Measure(name, dax, fmt, display_folder=folder))


def answer(name: str, x, y, w, h, lines: list, size: int = 10) -> Visual:
    """The text box with the written answers, headed "Model answer"."""
    return textbox(name, x, y, w, h, [("Model answer", True)] + lines, size=size)


@dataclass
class ParamVisual(Visual):
    """A visual whose well holds a field parameter: the parameter's fields as projections, in the parameter's order,
    and the role's fieldParameters entry pointing at the parameter column (PBIR RoleFieldParameter)."""
    params: dict = field(default_factory=dict)          # role -> parameter column field

    def doc(self, z: int) -> dict:
        d = super().doc(z)
        state = d["visual"]["query"]["queryState"]
        for role, f in self.params.items():
            state[role]["fieldParameters"] = [{"parameterExpr": f, "index": 0, "length": len(state[role]["projections"])}]
        return d


def pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


# --- Exercise 15.1 ---------------------------------------------------------------------------------------------------

def ex1(b: Build) -> None:
    ctx = ch15.ex1(b.data, claim)
    now, before = ctx["now"], ctx["before"]
    sub = "Other Income or Expense"
    # (1) the Ledger Detail page: AccountSubType in its drill-through well, as left after a drill-through on the subtype
    page = b.report.add(Page("ledgerDetail", "Ledger Detail"))
    page.hidden = True
    drillthrough(page, col("Account", "AccountSubType"), sub)
    page.add(Visual("ledgerTable", "tableEx", 20, 70, 760, 220, {"Values": [
        col("GLEntry", "PostingDate"), col("GLEntry", "VoucherNumber"), col("GLEntry", "SourceDocumentType"),
        col("Account", "AccountNumber"), col("Account", "AccountName"), M("P&L Amount")]},
        title="Postings to the drilled-through subtype"))
    def entry(e):
        lines = [f"Dr {e['acc']['account']} {e['acc']['name']} {money(e['acc']['amount'])}",
                 f"Cr {e['cost']['account']} {e['cost']['name']} {money(e['cost']['amount'])}"]
        if e["cash"]:
            lines.insert(0, f"Dr {e['cash']['account']} {e['cash']['name']} {money(e['cash']['amount'])}")
        return lines
    page.add(answer("ledgerAnswer", 800, 70, 460, 640, [
        f"(2) Fiscal {b.year}: {now['number']}, {now['date']}, \"{now['entry']}\": Dr {ctx['account']['number']} "
        f"{ctx['account']['name']} {money(now['loss'])}. Fiscal {b.year - 1}: {before['number']}, {before['date']}, "
        f"\"{before['entry']}\": Dr {ctx['account']['number']} {money(before['loss'])}. The subtype's other account, "
        f"{ctx['unposted']['number']} {ctx['unposted']['name']}, has no postings.",
        f"(4) {now['number']} retires asset {now['asset']} (\"{now['event_desc']}\"): " + "; ".join(entry(now)) +
        f". Loss = cost {money(now['cost']['amount'])} less accumulated depreciation {money(now['acc']['amount'])} less "
        f"proceeds {money(now['proceeds'])} = {money(now['loss'])}.",
        f"{before['number']} disposes of asset {before['asset']} (\"{before['event_desc']}\"): " + "; ".join(entry(before)) +
        f". The same calculation, {money(before['cost']['amount'])} - {money(before['acc']['amount'])} - "
        f"{money(before['proceeds'])} in proceeds = {money(before['loss'])}, gives a smaller loss because the asset was "
        "sold for cash and was further depreciated relative to its cost.",
        f"The closes {', '.join(ctx['closes'])} credit {ctx['account']['number']} too, but GL Amount leaves the closes "
        "out, so the drill-through lists only the two loss entries.",
        "(5) Drill-through passes every filter of the data point: the row (AccountSubType) and the matrix column (Year). "
        "Without the year, the page lists both years' entries, as it does when opened as saved here."], size=10))
    page.expect = ["VoucherNumber", "AccountName", now["number"], before["number"], money(-now["loss"]),
                   money(-before["loss"]), "Model answer"]
    # (3) the query
    b.project.queries["Ex 15.1"] = (
        f"// Exercise 15.1 (3): every posting of {now['number']}, with the account columns brought by RELATED\n"
        "EVALUATE\nSELECTCOLUMNS (\n"
        f"    FILTER ( GLEntry, GLEntry[VoucherNumber] = \"{now['number']}\" ),\n"
        "    \"PostingDate\", GLEntry[PostingDate],\n"
        "    \"AccountNumber\", RELATED ( Account[AccountNumber] ),\n"
        "    \"AccountName\", RELATED ( Account[AccountName] ),\n"
        "    \"Debit\", GLEntry[Debit],\n"
        "    \"Credit\", GLEntry[Credit]\n)\nORDER BY [Debit] DESC, [Credit] DESC\n")

    t, s = "Exercise 15.1", f"Account[AccountSubType] = \"{sub}\""
    b.check(t, "accounts of the subtype", 2, f"COUNTROWS ( FILTER ( Account, {s} ) )", 0)
    vouchers = ("CALCULATE ( CONCATENATEX ( FILTER ( VALUES ( GLEntry[VoucherNumber] ), NOT ISBLANK ( [P&L Amount] ) ), "
                "GLEntry[VoucherNumber], \", \", GLEntry[VoucherNumber], ASC ), {} )")
    for e, yr in ((now, b.year), (before, b.year - 1)):
        f = f"{s}, 'Date'[Year] = {yr}"
        b.check(t, f"{yr} entry on the drill-through page", e["number"], vouchers.format(f))
        b.check(t, f"{yr} P&L Amount of the subtype", round(-e["loss"], 2), f"CALCULATE ( [P&L Amount], {f} )", 0.01)
        v = f"GLEntry[VoucherNumber] = \"{e['number']}\""
        b.check(t, f"{e['number']} posting date", e["date"],
                f"FORMAT ( CALCULATE ( MIN ( GLEntry[PostingDate] ), {v} ), \"yyyy-mm-dd\" )")
        b.check(t, f"{e['number']} postings (the query's rows)", 3 + (1 if e["cash"] else 0),
                f"CALCULATE ( COUNTROWS ( GLEntry ), {v} )", 0)
        legs = [("debit", ctx["account"]["number"], e["loss"]), ("debit", e["acc"]["account"], e["acc"]["amount"]),
                ("credit", e["cost"]["account"], e["cost"]["amount"])]
        if e["cash"]:
            legs.append(("debit", e["cash"]["account"], e["cash"]["amount"]))
        for side, acct, amount in legs:
            b.check(t, f"{e['number']} {side} to {acct}", round(amount, 2),
                    f"CALCULATE ( SUM ( GLEntry[{side.title()}] ), {v}, Account[AccountNumber] = {acct} )", 0.01)
    b.check(t, "entries listed without a year filter (requirement 5)", f"{before['number']}, {now['number']}",
            vouchers.format(s))
    closes = one("SELECT SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE "
                 "a.AccountSubType = ? AND g.VoucherNumber IN (%s)" % ",".join("?" * len(ctx["closes"])), sub, *ctx["closes"])
    b.check(t, "the closes' credits to the subtype (left out by GL Amount)", round(closes, 2),
            f"CALCULATE ( SUM ( GLEntry[Credit] ), {s}, GLEntry[IsYearEndClose] )", 0.01)


# --- Exercise 15.2 ---------------------------------------------------------------------------------------------------

def ex2(b: Build) -> None:
    ctx = ch15.ex2(b.data, claim)
    y, folder = b.year, "Ex 15.2"
    measure(b, folder, "Net Income YTD", "TOTALYTD ( [Net Income], 'Date'[Date] )", MONEY)
    ytd = {"NativeVisualCalculation": {"Language": "dax", "Expression": "RUNNINGSUM ( [Net Income] )", "Name": "YTD"}}
    change = {"NativeVisualCalculation": {"Language": "dax", "Expression": "[Net Income] - PREVIOUS ( [Net Income] )",
                                          "Name": "Change"}}
    months = [f"{y}-{m:02d}" for m in range(1, 13)]
    values = lambda: [col("Date", "YearMonth"), M("Net Income"), ytd, change, M("Net Income YTD")]   # noqa: E731
    page = b.report.add(Page("ex152", "Ex 15.2"))
    page.add(Visual("netIncomeByMonth", "tableEx", 20, 20, 600, 420, {"Values": values()},
                    title=f"Net income by month, fiscal {y}", filters=[keep("nimYear", col("Date", "Year"), [y])]))
    page.add(Visual("secondHalf", "tableEx", 20, 460, 600, 250, {"Values": values()},
                    title="Filtered to July to December (requirement 3)",
                    filters=[keep("shYear", col("Date", "Year"), [y]), keep("shMonths", col("Date", "YearMonth"), months[6:])]))
    nm = [v for _, v in ctx["months"]]
    low = ctx["low"]
    page.add(answer("ex152Answer", 640, 20, 620, 690, [
        f"(2) Net Income YTD equals the YTD visual calculation in every month and reaches {money(ctx['ni'])} in December, "
        f"the net income of Tutorial 14.3 (and the close {ctx['close']}'s credit to retained earnings).",
        f"(3) Filtered to July to December, the running sum starts again at July and reaches {money(ctx['h2'])} in "
        f"December, while TOTALYTD still shows {money(ctx['july'])} in July and {money(ctx['ni'])} in December: the "
        "measure reads the model's dates, the visual calculation only the rows the visual shows.",
        f"(4) The two lowest months are {low[0]['name']} ({money(min(nm))}) and {low[1]['name']} "
        f"({money(sorted(nm)[1])}). " + " ".join(
            (f"{x['name']} has three pay dates, as does {', '.join(x['others'])} (Chapters 11 and 14)." if x["pay"] else
             f"{x['name']} is the peak of the promotion's discounts, with Furniture revenue {pct(x['furniture'])} below "
             f"the same month a year earlier (Chapter 11)." if x["promo"] else "") for x in low),
        "(5) The measure: it is right whatever the visual shows, it can be reused and exported, and a filter on the "
        "months cannot change what it means."]))
    feb = nm[1] - nm[0]
    page.expect = ["YTD", "Change", "Net Income YTD", money(ctx["h2"]), money(feb), money(ctx["ni"]), "Model answer"]

    t = "Exercise 15.2"
    for m_, v in zip(months, nm):
        b.check(t, f"Net Income {m_}", round(v, 2), f"CALCULATE ( [Net Income], 'Date'[YearMonth] = \"{m_}\" )", 0.01)
    running = 0.0
    for m_, v in zip(months, nm):
        running += v
        b.check(t, f"Net Income YTD {m_} (the running sum)", round(running, 2),
                f"CALCULATE ( [Net Income YTD], 'Date'[YearMonth] = \"{m_}\" )", 0.01)
    b.check(t, "YTD at June", round(ctx["june"], 2), f"CALCULATE ( [Net Income YTD], 'Date'[YearMonth] = \"{months[5]}\" )",
            0.01)
    b.check(t, "TOTALYTD in July with the table filtered to July-December", round(ctx["july"], 2),
            f"CALCULATE ( [Net Income YTD], 'Date'[YearMonth] = \"{months[6]}\", 'Date'[YearMonth] IN {{ "
            + ", ".join(f'"{x}"' for x in months[6:]) + " } )", 0.01)
    b.check(t, "the running sum of July-December (the visual calculation's December)", round(ctx["h2"], 2),
            f"CALCULATE ( [Net Income], 'Date'[YearMonth] IN {{ " + ", ".join(f'"{x}"' for x in months[6:]) + " } )", 0.01)
    lowest = sorted(zip(months, nm), key=lambda mv: mv[1])[:2]
    b.check(t, "the two months with the lowest net income", ", ".join(sorted(m_ for m_, _ in lowest)),
            f"CONCATENATEX ( TOPN ( 2, CALCULATETABLE ( VALUES ( 'Date'[YearMonth] ), 'Date'[Year] = {y} ), "
            "[Net Income], ASC ), 'Date'[YearMonth], \", \", 'Date'[YearMonth], ASC )")


# --- Exercise 15.3 ---------------------------------------------------------------------------------------------------

PLANT = ["Hours per Standard Hour", "Overtime Share", "Labor Cost per Standard Hour"]


def ex3(b: Build) -> None:
    ctx = ch15.ex3(b.data, claim)
    y, folder = b.year, "Ex 15.3"
    years = [y - 2, y - 1, y]
    # (1) the measure, with KEEPFILTERS as Manufacturing Hours
    measure(b, folder, "Labor Cost per Standard Hour",
            "DIVIDE (\n    CALCULATE (\n        SUM ( LaborTimeEntry[ExtendedLaborCost] ),\n"
            "        KEEPFILTERS ( LaborTimeEntry[LaborType] <> \"NonManufacturing\" )\n    ),\n"
            "    [Standard Hours to Cut-off]\n)", "0.00")
    # (2) Modeling > New parameter > Fields: the calculated table Desktop writes, three columns and ParameterMetadata
    p = "Plant Measure"
    tuples = ",\n".join(f"    (\"{n}\", NAMEOF ( '{KM}'[{n}] ), {i})" for i, n in enumerate(PLANT))
    b.model.add(Table(p, [
        Column(p, "string", "[Value1]", sort_by=f"{p} Order", extra=(f"relatedColumnDetails\n\t\t\tgroupByColumn: '{p} Fields'",)),
        Column(f"{p} Fields", "string", "[Value2]", hidden=True, sort_by=f"{p} Order",
               extra=('extendedProperty ParameterMetadata = {"version":3,"kind":2}',)),
        Column(f"{p} Order", "int64", "[Value3]", fmt="0", summarize="sum", hidden=True)], dax="{\n" + tuples + "\n}"))
    # (3) the chart, with the slicer Power BI adds; a table records the three measures by year
    page = b.report.add(Page("ex153", "Ex 15.3"))
    pf = col(p, p)
    page.add(slicer("plantMeasureSlicer", 20, 20, 300, 150, pf, ["Labor Cost per Standard Hour"], title=p))
    page.add(ParamVisual("plantMeasureChart", "clusteredColumnChart", 340, 20, 920, 330,
                         {"Category": [col("Date", "Year")], "Y": [M(n) for n in PLANT]},
                         title="The plant measure chosen in the slicer, by year",
                         filters=[keep("pmYears", col("Date", "Year"), years)], params={"Y": pf}))
    page.add(Visual("plantMeasureTable", "tableEx", 20, 370, 600, 160, {"Values": [col("Date", "Year")] + [M(n) for n in PLANT]},
                    title="The three measures by year (requirement 3)", filters=[keep("pmtYears", col("Date", "Year"), years)]))
    yr = ctx["years"]
    page.add(answer("ex153Answer", 640, 370, 620, 340, [
        "(3) " + "; ".join(f"{yy}: {x['ratio']:.2f} hours per standard hour, overtime share {x['share']:.3f}, labor cost "
                           f"{x['per_std']:.2f} per standard hour" for yy, x in zip(years, yr)) + ".",
        f"(4) Labor cost per standard hour = hours per standard hour x cost per hour. The hours per standard hour rose "
        f"{pct(yr[-1]['ratio'] / yr[0]['ratio'] - 1)}, the cost per hour {pct(yr[-1]['per_hour'] / yr[0]['per_hour'] - 1)} "
        f"(from {yr[0]['per_hour']:.2f} to {yr[-1]['per_hour']:.2f}), because the overtime share grew and overtime hours "
        f"cost a premium; the straight-time rate barely moved ({', '.join(f'{r:.2f}' for r in ctx['rates'])}), so the "
        f"cost per standard hour rose {pct(yr[-1]['per_std'] / yr[0]['per_std'] - 1)}.",
        "(5) A field parameter cannot be the field of a drill-through (or tooltip) page; Power BI allows the underlying "
        "fields instead, so the drill-through page lists the measures' own fields (Year, JobTitle) in its well."]))
    page.expect = [p, "Labor Cost per Standard Hour"] + [f"{x['per_std']:.2f}" for x in yr] + [f"{yr[0]['ratio']:.2f}"]

    t = "Exercise 15.3"
    b.check(t, "the parameter's fields, in order", ", ".join(PLANT),
            f"CONCATENATEX ( '{p}', '{p}'[{p}], \", \", '{p}'[{p} Order], ASC )")
    for yy, x in zip(years, yr):
        cy = f"'Date'[Year] = {yy}"
        b.check(t, f"{yy} Hours per Standard Hour", round(x["ratio"], 6), f"CALCULATE ( [Hours per Standard Hour], {cy} )",
                0.000005)
        b.check(t, f"{yy} Overtime Share", round(x["share"], 6), f"CALCULATE ( [Overtime Share], {cy} )", 0.000005)
        b.check(t, f"{yy} Labor Cost per Standard Hour", round(x["per_std"], 6),
                f"CALCULATE ( [Labor Cost per Standard Hour], {cy} )", 0.000005)
        b.check(t, f"{yy} manufacturing labor cost", round(x["cost"], 2),
                f"CALCULATE ( SUM ( LaborTimeEntry[ExtendedLaborCost] ), KEEPFILTERS ( LaborTimeEntry[LaborType] <> "
                f"\"NonManufacturing\" ), {cy} )", 0.01)
    for yy, r in zip(years, ctx["rates"]):
        b.check(t, f"{yy} straight-time rate (cost / (regular + 1.5 x overtime hours))", round(r, 6),
                f"CALCULATE ( DIVIDE ( SUM ( LaborTimeEntry[ExtendedLaborCost] ), SUMX ( LaborTimeEntry, "
                f"LaborTimeEntry[RegularHours] + 1.5 * LaborTimeEntry[OvertimeHours] ) ), KEEPFILTERS ( "
                f"LaborTimeEntry[LaborType] <> \"NonManufacturing\" ), 'Date'[Year] = {yy} )", 0.000005)


# --- Exercise 15.4 ---------------------------------------------------------------------------------------------------

def ex4(b: Build) -> None:
    ctx = ch15.ex4(b.data, claim)
    y, folder = b.year, "Ex 15.4"
    name = one("SELECT PromotionName FROM PromotionProgram WHERE PromotionID = ?", ctx["id"])
    claim(one("SELECT COUNT(*) FROM PromotionProgram WHERE PromotionName = ?", name) == 1, "the promotion's name is unique")
    # (1) Modeling > New parameter > Numeric range: the GENERATESERIES table and its Value measure, as Desktop writes them
    default = 0.12
    b.model.add(Table("Discount", [Column("Discount", "double", "[Value]", fmt="0%", summarize="none",
                                          extra=('extendedProperty ParameterMetadata = {"version":0}',))],
                      measures=[Measure("Discount Value", f"SELECTEDVALUE ( 'Discount'[Discount], {default} )", "0%")],
                      dax="GENERATESERIES ( 0, 0.2, 0.01 )"))
    # (2) and (3) the measures
    scope = f"PromotionProgram[PromotionName] = \"{name}\", 'Date'[Year] = {y}"
    measure(b, folder, "Design Trade Units", f"CALCULATE ( SUM ( SalesInvoiceLine[Quantity] ), {scope} )", "#,0.00")
    measure(b, folder, "Design Trade Price per Unit",
            f"DIVIDE ( CALCULATE ( [Price Before Discount], {scope} ), [Design Trade Units] )", MONEY)
    measure(b, folder, "Design Trade Cost per Unit",
            f"DIVIDE ( CALCULATE ( [Standard Cost], {scope} ), [Design Trade Units] )", MONEY)
    measure(b, folder, "Break-even Lift",
            "VAR Price = [Design Trade Price per Unit]\nVAR Cost = [Design Trade Cost per Unit]\n"
            f"VAR Commission = {ch15.CASE_RATE}\nVAR Disc = [Discount Value]\nRETURN\n"
            "    DIVIDE (\n        Price * ( 1 - Commission ) - Cost,\n"
            "        Price * ( 1 - Disc ) * ( 1 - Commission ) - Cost\n    ) - 1", "0.0%")
    # the page: the slider (Single value, set to the default), the cards, and the lift at every discount
    page = b.report.add(Page("ex154", "Ex 15.4"))
    d = col("Discount", "Discount")
    page.add(Visual("discountSlider", "slicer", 20, 20, 360, 110, {"Values": [d]}, title="Discount",
                    objects={"data": [{"properties": {"mode": lit("Single")}}],
                             "general": [{"properties": {"filter": {"filter": {
                                 "Version": 2, "From": [{"Name": "d", "Entity": "Discount", "Type": 0}],
                                 "Where": [{"Condition": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {
                                     "Expression": {"SourceRef": {"Source": "d"}}, "Property": "Discount"}},
                                     "Right": {"Literal": {"Value": f"{default}D"}}}}}]}}}}]}))
    page.add(card("liftCards", 400, 20, 860, 110, [M("Design Trade Units"), M("Design Trade Price per Unit"),
                                                   M("Design Trade Cost per Unit"), meas("Discount", "Discount Value"),
                                                   M("Break-even Lift")]))
    page.add(Visual("liftByDiscount", "tableEx", 20, 150, 360, 560, {"Values": [d, M("Break-even Lift")]},
                    title="Break-even lift at each discount"))
    page.extra = {"visualInteractions": [{"source": "discountSlider", "target": "liftByDiscount", "type": "NoFilter"}]}
    lifts = dict(ctx["lifts"])
    case_lift = lifts[0.12]
    page.add(answer("ex154Answer", 400, 150, 860, 560, [
        f"(2) {name}, fiscal {y}: {ctx['units']:,.2f} units, price before discount {ctx['price']:.2f} per unit, standard "
        f"cost {ctx['cost']:.2f} per unit (the Part II case's inputs).",
        "(4) Break-even lift: " + "; ".join(f"{pct(k, 0)} discount {pct(v)}" for k, v in ctx["lifts"]) +
        f". At 12 percent the lift is {pct(case_lift)}, the Part II case's result for the same promotion.",
        f"(5) The Part II case found no lift in any promotion's months: volume ran from {pct(ctx['low'])} to "
        f"{pct(ctx['high'])} against the other months of the year, none of it unusual. Even a 5 percent discount needs "
        f"{ctx['five']} the largest increase ever measured ({pct(lifts[0.05])} against {pct(ctx['high'])}). The "
        "recommendation: do not repeat the promotion at 12 percent; if the sales manager wants to test it, offer a "
        "small discount (5 percent or less) to a defined group of design trade customers and measure the volume "
        "against a comparable group before extending it."]))
    page.expect = ["Break-even Lift", "Discount Value", f"{ctx['units']:,.2f}", pct(case_lift), pct(lifts[0.05])]

    t = "Exercise 15.4"
    b.check(t, "Discount rows (0 to 0.2 by 0.01)", 21, "COUNTROWS ( 'Discount' )", 0)
    b.check(t, "Design Trade Units", round(ctx["units"], 4), "[Design Trade Units]", 0.0001)
    b.check(t, "Design Trade Price per Unit", round(ctx["price"], 6), "[Design Trade Price per Unit]", 0.000005)
    b.check(t, "Design Trade Cost per Unit", round(ctx["cost"], 6), "[Design Trade Cost per Unit]", 0.000005)
    b.check(t, "Break-even Lift at the default (12%)", round(case_lift, 6), "[Break-even Lift]", 0.000005)
    for k, v in ctx["lifts"]:
        b.check(t, f"Break-even Lift at {pct(k, 0)}", round(v, 6),
                f"CALCULATE ( [Break-even Lift], FILTER ( ALL ( 'Discount'[Discount] ), ABS ( 'Discount'[Discount] - {k} ) "
                "< 0.0001 ) )", 0.000005)
    b.check(t, "promotion lines in the scope", one(
        "SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
        "WHERE l.PromotionID = ? AND substr(si.InvoiceDate, 1, 4) = ?", ctx["id"], str(y)),
        f"CALCULATE ( COUNTROWS ( SalesInvoiceLine ), {scope} )", 0)


# --- Exercise 15.5 ---------------------------------------------------------------------------------------------------

def ex5(b: Build) -> None:
    ctx = ch15.ex5(b.data, claim)
    y = b.year
    first = y - 2
    # (1) the calculated column
    b.model.tables["Date"].columns.append(Column("MonthStart", "dateTime", fmt="Short Date", summarize="none",
                                                 expression="DATE ( YEAR ( 'Date'[Date] ), MONTH ( 'Date'[Date] ), 1 )"))
    fit = [f"{yy}-{mm:02d}" for yy in range(first, y + 1) for mm in range(1, 13)][:-3]
    forecast = {"forecast": [{"properties": {"show": lit(True), "forecastLength": {"expr": {"Literal": {"Value": "3L"}}},
                                             "confidenceLevel": {"expr": {"Literal": {"Value": "95D"}}},
                                             "confidenceBandStyle": lit("fill")}}],
                "categoryAxis": [{"properties": {"axisType": lit("Continuous")}}]}
    page = b.report.add(Page("ex155", "Ex 15.5"))
    for i, (name, months, title) in enumerate([
            ("forecastFromJanuary", fit, f"Revenue, January {first} to September {y}, with a three-month forecast"),
            ("forecastFromFebruary", fit[1:], f"Revenue, February {first} to September {y}, with a three-month forecast")]):
        page.add(Visual(name, "lineChart", 20, 20 + 300 * i, 760, 280,
                        {"Category": [col("Date", "MonthStart")], "Y": [M("Revenue")]}, title=title, objects=forecast,
                        filters=[keep(f"{name}Months", col("Date", "YearMonth"), months)]))
    q4 = [f"{y}-{m:02d}" for m in (10, 11, 12)]
    page.add(Visual("actualQ4", "tableEx", 20, 620, 760, 90, {"Values": [col("Date", "YearQuarter"), M("Revenue")]},
                    title="Actual revenue of the quarter forecast",
                    filters=[keep("actualQ4Quarter", col("Date", "YearQuarter"), [f"{y}-Q4"])]))
    e = ctx["errors"]
    page.add(answer("ex155Answer", 800, 20, 460, 690, [
        f"(3) The forecast is computed in the visual (exponential smoothing) and cannot be read from the model: read the "
        "three months and the interval from the forecast's tooltip, and add the three months.",
        f"(4) Actual revenue of fiscal {y}'s fourth quarter: {money(ctx['actual'])}. Chapter 7's benchmarks for the same "
        f"quarter, fitted from February {first} to September {y}: trend {pct(e['trend']['quarter'], 2)} quarter error "
        f"(monthly {pct(e['trend']['monthly'], 2)}); mean {pct(e['mean']['quarter'], 2)} ({pct(e['mean']['monthly'], 2)}); "
        f"same quarter last year {pct(e['last']['quarter'], 2)} ({pct(e['last']['monthly'], 2)}). Compare the forecast's "
        "quarter error with these.",
        f"(5) January {first}, the start-up month, is {pct(ctx['start'], 0)} of the year's other months; leaving it out "
        "changes the fit, and the change shows how sensitive the forecast is to one unrepresentative month. With "
        f"{ctx['years']} years, a seasonal pattern cannot be detected reliably.",
        "(6) Audit note: the forecast is fit for the 2027 plan only if its hindcast error on a known quarter is "
        "disclosed with it, beside the benchmark it beat or did not beat (the mean has done best here), with the "
        "fitted period and the treatment of the start-up month."]))
    page.expect = ["MonthStart", "Revenue", money(ctx["actual"]), "Model answer"]

    t = "Exercise 15.5"
    b.check(t, "MonthStart values (one per month of the Date table)", 12 * len(range(first, b.data.N + 1)),
            "COUNTROWS ( VALUES ( 'Date'[MonthStart] ) )", 0)
    b.check(t, "months with revenue in the fitted window", ctx["fit_months"],
            f"COUNTROWS ( FILTER ( VALUES ( 'Date'[MonthStart] ), 'Date'[MonthStart] <= DATE ( {y}, 9, 1 ) && "
            "NOT ISBLANK ( [Revenue] ) ) )", 0)
    b.check(t, f"actual revenue {y}-Q4", round(ctx["actual"], 2), f"CALCULATE ( [Revenue], 'Date'[YearQuarter] = \"{y}-Q4\" )")
    for m_ in q4:
        b.check(t, f"actual revenue {m_}", round(sales("substr(si.InvoiceDate, 1, 7) = ?", m_)["rev"], 2),
                f"CALCULATE ( [Revenue], 'Date'[YearMonth] = \"{m_}\" )")
    last = sum(sales("substr(si.InvoiceDate, 1, 7) = ?", f"{y - 1}-{m:02d}")["rev"] for m in (10, 11, 12))
    b.check(t, "the same quarter last year (a benchmark)", round(last, 2),
            f"CALCULATE ( [Revenue], 'Date'[YearQuarter] = \"{y - 1}-Q4\" )")
    b.check(t, "the same-quarter benchmark's quarter error", round(e["last"]["quarter"], 6),
            f"DIVIDE ( CALCULATE ( [Revenue], 'Date'[YearQuarter] = \"{y - 1}-Q4\" ), CALCULATE ( [Revenue], "
            f"'Date'[YearQuarter] = \"{y}-Q4\" ) ) - 1", 0.000005)
    fitted = "FILTER ( VALUES ( 'Date'[YearMonth] ), 'Date'[YearMonth] >= \"{}\" && 'Date'[YearMonth] <= \"{}\" )"
    b.check(t, "the mean benchmark's quarter error (mean month February to September x 3)", round(e["mean"]["quarter"], 6),
            f"DIVIDE ( 3 * AVERAGEX ( {fitted.format(fit[1], fit[-1])}, [Revenue] ), CALCULATE ( [Revenue], "
            f"'Date'[YearQuarter] = \"{y}-Q4\" ) ) - 1", 0.000005)
    b.check(t, f"January {first} against the year's other months", round(ctx["start"], 6),
            f"DIVIDE ( CALCULATE ( [Revenue], 'Date'[YearMonth] = \"{first}-01\" ), AVERAGEX ( "
            f"{fitted.format(f'{first}-02', f'{first}-12')}, [Revenue] ) )", 0.000005)


# --- Exercise 15.6 ---------------------------------------------------------------------------------------------------

def ex6(b: Build) -> None:
    ctx = ch15.ex6(b.data, claim)
    y, folder, x = b.year, "Ex 15.6", b.xlsx
    m = b.model
    # (1) the two paths' Tables, Enable load cleared
    ops = (Query.navigator("OperationPaths", x, 52, "WorkOrderOperation")
           .select(["WorkOrderOperationID", "WorkCenterID", "ActualEndDate"]).types({"ActualEndDate": "type date"}))
    clock = Query.navigator("ClockPaths", x, 66, "TimeClockEntry").select(["TimeClockEntryID", "WorkCenterID"])
    m.stage(ops)
    m.stage(clock)
    # (2) the labor lines with each path's work-center name
    center = b.query("WorkCenter")
    paths = (Query.navigator("LaborPaths", x, 60, "LaborTimeEntry", corrections={"WorkOrderOperationID": "Int64.Type"})
             .select(["LaborTimeEntryID", "WorkOrderOperationID", "TimeClockEntryID", "WorkDate", "LaborType",
                      "RegularHours", "OvertimeHours"])
             .types({"WorkDate": "type date"})
             .merge(ops, "WorkOrderOperationID", "WorkOrderOperationID", ["WorkCenterID", "ActualEndDate"])
             .merge(center, "WorkCenterID", "WorkCenterID", ["WorkCenterName"])
             .rename({"WorkCenterID": "OperationWorkCenterID", "WorkCenterName": "OperationWorkCenter"})
             .merge(clock, "TimeClockEntryID", "TimeClockEntryID", ["WorkCenterID"])
             .merge(center, "WorkCenterID", "WorkCenterID", ["WorkCenterName"])
             .rename({"WorkCenterID": "ClockWorkCenterID", "WorkCenterName": "ClockWorkCenter"}))
    # (3) the two tests
    paths.custom("SameWorkCenter", "if [OperationWorkCenter] = null or [ClockWorkCenter] = null then null "
                                   "else [OperationWorkCenter] = [ClockWorkCenter]", "type logical")
    paths.custom("AfterOperationEnd", "if [ActualEndDate] = null then null else [WorkDate] > [ActualEndDate]",
                 "type logical")
    ids = ("LaborTimeEntryID", "WorkOrderOperationID", "TimeClockEntryID", "OperationWorkCenterID", "ClockWorkCenterID")
    m.add(query_table(paths, summarize={k: "none" for k in ids}, hidden=set(ids)))
    m.relate("LaborPaths.WorkDate", "Date.Date")
    # (4) and (5) the measures
    measure(b, folder, "Path Lines", "COUNTROWS ( LaborPaths )", "#,0")
    measure(b, folder, "Path Hours", "SUMX ( LaborPaths, LaborPaths[RegularHours] + LaborPaths[OvertimeHours] )", "#,0.0")
    measure(b, folder, "Lines on Both Paths", "CALCULATE ( [Path Lines], NOT ISBLANK ( LaborPaths[SameWorkCenter] ) )",
            "#,0")
    measure(b, folder, "Disagreeing Lines", "CALCULATE ( [Path Lines], LaborPaths[SameWorkCenter] == FALSE () )", "#,0")
    measure(b, folder, "Disagreeing Hours", "CALCULATE ( [Path Hours], LaborPaths[SameWorkCenter] == FALSE () )", "#,0.0")
    measure(b, folder, "Share After Operation End",
            "DIVIDE ( CALCULATE ( [Path Lines], LaborPaths[AfterOperationEnd] == TRUE () ), [Path Lines] )", "0.0%")
    lt, ow, cw = col("LaborPaths", "LaborType"), col("LaborPaths", "OperationWorkCenter"), col("LaborPaths", "ClockWorkCenter")
    page = b.report.add(Page("ex156", "Ex 15.6"))
    page.add(Visual("disagreeByYear", "tableEx", 20, 20, 600, 150, {"Values": [
        col("Date", "Year"), M("Lines on Both Paths"), M("Disagreeing Lines"), M("Disagreeing Hours")]},
        title="Direct lines whose two work centers disagree", filters=[keep("dbyType", lt, [DIRECT])]))
    page.add(Visual("pathMatrix", "pivotTable", 20, 190, 1240, 230, {"Rows": [ow], "Columns": [cw], "Values": [M("Path Hours")]},
                    title=f"Direct hours of {y}: operation's work center (rows) against the time clock's (columns)",
                    filters=[keep("pmType", lt, [DIRECT]), keep("pmYear", col("Date", "Year"), [y]),
                             keep("pmBlank", ow, [None], exclude=True)]))
    page.add(Visual("lateShare", "tableEx", 640, 20, 620, 150, {"Values": [
        col("LaborPaths", "SameWorkCenter"), M("Path Lines"), M("Share After Operation End")]},
        title=f"Direct lines of {y} on both paths, recorded after the operation ended",
        filters=[keep("lsType", lt, [DIRECT]), keep("lsYear", col("Date", "Year"), [y]),
                 keep("lsBlank", col("LaborPaths", "SameWorkCenter"), [None], exclude=True)]))
    page.add(Visual("indirectByClock", "clusteredBarChart", 20, 440, 600, 270, {"Category": [cw], "Y": [M("Path Hours")]},
                    title=f"Indirect manufacturing hours of {y} by the time clock's work center",
                    filters=[keep("ibcType", lt, [INDIRECT]), keep("ibcYear", col("Date", "Year"), [y])],
                    sort=[(M("Path Hours"), "Descending")]))
    yrs = ctx["years"]
    page.add(answer("ex156Answer", 640, 440, 620, 270, [
        "(4) Disagreements (lines / of lines on both paths / hours): " + "; ".join(
            f"{v['year']} {v['differ']:,} / {v['lines']:,} / {v['hours']:,.1f}" for v in yrs) +
        f"; {ctx['total']:,} in all. Packing operations were often clocked at another work center.",
        f"(5) After the operation's end: {ctx['late_differ']:,} of the {ctx['differ']:,} disagreeing lines "
        f"({pct(ctx['late_differ'] / ctx['differ'], 0)}) against {ctx['late_all']:,} of the {ctx['now']:,} direct lines "
        f"on both paths ({pct(ctx['late_all'] / ctx['now'], 0)}): the disagreement concentrates in the late time of "
        "Chapter 12.",
        "(6) The clock places the indirect hours mostly at " + ", ".join(f"{n} ({h:,.1f})" for n, h in ctx["indirect"][:3]) +
        ". The operation path answers what work the time was charged to; the clock path where the employee was. "
        "Neither alone supports the Packing finding, which needs corroboration."], size=9))
    page.expect = ["OperationWorkCenter", "ClockWorkCenter", f"{yrs[-1]['differ']:,}", f"{yrs[0]['differ']:,}",
                   center_name("Packing"), "Model answer"]

    t = "Exercise 15.6"
    d_ = f"LaborPaths[LaborType] = \"{DIRECT}\""
    b.check(t, "LaborPaths rows", one("SELECT COUNT(*) FROM LaborTimeEntry"), "COUNTROWS ( LaborPaths )", 0)
    b.check(t, "direct lines on both paths, all years", ctx["both"], f"CALCULATE ( [Lines on Both Paths], {d_} )", 0)
    b.check(t, "disagreeing direct lines, all years", ctx["total"], f"CALCULATE ( [Disagreeing Lines], {d_} )", 0)
    for v in yrs:
        cy = f"'Date'[Year] = {v['year']}"
        b.check(t, f"{v['year']} disagreeing lines", v["differ"], f"CALCULATE ( [Disagreeing Lines], {d_}, {cy} )", 0)
        b.check(t, f"{v['year']} direct lines on both paths", v["lines"], f"CALCULATE ( [Lines on Both Paths], {d_}, {cy} )", 0)
        b.check(t, f"{v['year']} disagreeing hours", round(v["hours"], 2), f"CALCULATE ( [Disagreeing Hours], {d_}, {cy} )",
                0.01)
    cells = rows("SELECT ow.WorkCenterName, cw.WorkCenterName, SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l "
                 "JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID JOIN WorkCenter ow "
                 "ON ow.WorkCenterID = o.WorkCenterID JOIN TimeClockEntry tc ON tc.TimeClockEntryID = l.TimeClockEntryID "
                 "JOIN WorkCenter cw ON cw.WorkCenterID = tc.WorkCenterID WHERE l.LaborType = ? AND substr(l.WorkDate, 1, 4) = ? "
                 "GROUP BY 1, 2", DIRECT, str(y))
    by = {(a, c): h for a, c, h in cells}
    for row_ in ctx["m"]:
        op = next(n for n in {a for a, _ in by} if n.startswith(row_["label"]) or
                  (row_["label"] == "QA" and n.startswith("Quality")))
        claim(abs(by[(op, op)] - row_["diag"]) < 0.01, f"the matrix's {op} diagonal agrees with the note")
        clocked = next(c for (a, c), h in by.items() if a == op and c != op and abs(h - row_["off"][0][1]) < 0.01)
        for c_ in (op, clocked):
            b.check(t, f"{y} direct hours, operation at {op}, clocked at {c_}", round(by[(op, c_)], 2),
                    f"CALCULATE ( [Path Hours], {d_}, 'Date'[Year] = {y}, LaborPaths[OperationWorkCenter] = \"{op}\", "
                    f"LaborPaths[ClockWorkCenter] = \"{c_}\" )", 0.01)
    cy = f"'Date'[Year] = {y}"
    b.check(t, f"{y} disagreeing lines recorded after the operation ended", ctx["late_differ"],
            f"CALCULATE ( [Path Lines], {d_}, {cy}, LaborPaths[SameWorkCenter] == FALSE (), "
            "LaborPaths[AfterOperationEnd] == TRUE () )", 0)
    b.check(t, f"{y} share after the operation's end, disagreeing lines", round(ctx["late_differ"] / ctx["differ"], 6),
            f"CALCULATE ( [Share After Operation End], {d_}, {cy}, LaborPaths[SameWorkCenter] == FALSE () )", 0.000005)
    b.check(t, f"{y} share after the operation's end, all direct lines on both paths",
            round(ctx["late_all"] / ctx["now"], 6),
            f"CALCULATE ( [Share After Operation End], {d_}, {cy}, NOT ISBLANK ( LaborPaths[SameWorkCenter] ) )", 0.000005)
    b.check(t, f"{y} direct lines in all", ctx["direct"], f"CALCULATE ( [Path Lines], {d_}, {cy} )", 0)
    for short, h in ctx["indirect"]:
        name = center_name("Quality Assurance" if short == "QA" else short)
        b.check(t, f"{y} indirect hours clocked at {name}", round(h, 2),
                f"CALCULATE ( [Path Hours], LaborPaths[LaborType] = \"{INDIRECT}\", {cy}, "
                f"LaborPaths[ClockWorkCenter] = \"{name}\" )", 0.01)
    b.check(t, f"{y} indirect hours with no clock work center", "blank",
            f"IF ( ISBLANK ( CALCULATE ( [Path Hours], LaborPaths[LaborType] = \"{INDIRECT}\", {cy}, "
            "ISBLANK ( LaborPaths[ClockWorkCenter] ) ) ), \"blank\", \"not blank\" )")


EXERCISES = [("15.1", ex1), ("15.2", ex2), ("15.3", ex3), ("15.4", ex4), ("15.5", ex5), ("15.6", ex6)]
