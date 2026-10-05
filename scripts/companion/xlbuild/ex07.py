"""Chapter 7 Exercises - Solutions.xlsx: the solutions to the exercises of Chapter 7.

The workbook is a copy of Charles River Furniture Analysis.xlsx at the end of Tutorial 7.3, with the worksheets each
exercise asks for (named after the exercise) and the queries it imports (each loaded to a worksheet named after its
query). Every result the instructor note states is checked on the Solution Notes worksheet with a live formula against
a value computed here from CharlesRiver.sqlite (read-only), independently of Excel.

Two outputs cannot be produced live, and each is labeled in a cell note: the Analysis ToolPak's regression output
(written in the tool's layout with LINEST and frozen as values, as in Tutorial 7.1), and Solver's optimum and reports
for Exercise 7.4. The optimum is computed here by a bounded-variable simplex (the method of Solver's Simplex LP), written
into the variable cells, and the model is saved in Solver's hidden worksheet names, so Data > Solver opens it ready to
solve; the Answer and Sensitivity reports are written in Solver's layout from the same computation.
"""

from __future__ import annotations

import math
import sqlite3
import statistics

from paths import db_uri
from xlbuild import pq, xl
from xlbuild.analysis import formulas, nav, regression_output, values
from xlbuild.solutions import COUNT, MONEY, PCT, RATIO, ExerciseBuild

GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories", "Services"]
PRODUCTS = GROUPS[:4]
NOTES = "Solution Notes"
TOP = -4160                          # xlTop
BIG = 1e30                           # Solver's "infinity" in the Sensitivity report
RANGE_FORMAT = "[>=1E+29]0E+00;[<=-1E+29]-0E+00;#,##0.0000"


# --- data (read-only) -----------------------------------------------------------------------------------------------

class Data:
    """The dataset, read-only, with the fiscal window of the exercises: F, P, C (the report year), and N = C + 1."""

    def __init__(self, year: int):
        self.C, self.P, self.F, self.N = year, year - 1, year - 2, year + 1
        self.years = [self.F, self.P, self.C]
        self.con = sqlite3.connect(db_uri(), uri=True)
        self.closes = [r[0] for r in self.q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%'")]

    def q(self, sql: str, *args):
        return self.con.execute(sql, args).fetchall()

    def one(self, sql: str, *args):
        return self.con.execute(sql, args).fetchone()[0]

    def account(self, number: int) -> int:
        return self.one("SELECT AccountID FROM Account WHERE AccountNumber = ?", number)

    def no_closes(self) -> str:
        return "VoucherNumber NOT IN (" + ",".join(f"'{e}'" for e in self.closes) + ")"


def data(b: ExerciseBuild) -> Data:
    if "data" not in b.found:
        b.found["data"] = Data(b.year)
    return b.found["data"]


def line_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least squares (intercept, slope), as FORECAST.LINEAR, INTERCEPT, and SLOPE compute them."""
    mx, my = statistics.mean(xs), statistics.mean(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - slope * mx, slope


def fit_stats(xs: list[float], ys: list[float]) -> dict:
    """Intercept, slope, R Square, and the standard error of the estimate (STEYX) of y on x."""
    a, b = line_fit(xs, ys)
    my = statistics.mean(ys)
    sse = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - my) ** 2 for y in ys)
    return dict(a=a, b=b, r2=1 - sse / sst, se=math.sqrt(sse / (len(xs) - 2)))


def mape(forecast: list[float], actual: list[float]) -> float:
    return statistics.mean(abs(f - a) / a for f, a in zip(forecast, actual))


# --- worksheet helpers ----------------------------------------------------------------------------------------------

def ex_sheet(b: ExerciseBuild, name: str):
    ws = xl.sheet(b.wb, name, before=b.wb.Worksheets(NOTES))
    b.found["last"] = ws
    return ws


def after_last(b: ExerciseBuild, name: str):
    """A worksheet right after the one added last (the exercise's own worksheets stay together, before the notes)."""
    ws = xl.sheet(b.wb, name, after=b.found["last"])
    b.found["last"] = ws
    return ws


def load(b: ExerciseBuild, name: str, m: str):
    """Add a query and load it to a worksheet named after it, placed after the worksheet added last."""
    xl.add_query(b.wb, name, m)
    lo = xl.load_query(b.wb, name, name, after=b.found["last"])
    b.found["last"] = lo.Parent
    return lo


def bold(ws, addr: str) -> None:
    ws.Range(addr).Font.Bold = True


def blue(ws, addr: str) -> None:
    ws.Range(addr).Font.Color = xl.BLUE


def model_answer(ws, row: int, paragraphs: list[str], last_col: str = "H") -> int:
    """A 'Model answer' heading and one merged, wrapped row per paragraph; returns the row after the last."""
    ws.Cells(row, 1).Value = "Model answer"
    ws.Cells(row, 1).Font.Bold = True
    width = sum(ws.Columns(c).ColumnWidth for c in range(1, ws.Range(f"{last_col}1").Column + 1))
    for i, text in enumerate(paragraphs, start=1):
        r = row + i
        rng = ws.Range(f"A{r}:{last_col}{r}")
        rng.Merge()
        rng.WrapText = True
        rng.VerticalAlignment = TOP
        ws.Cells(r, 1).Value = text
        lines = sum(max(1, math.ceil(len(part) * 1.15 / max(width, 20))) for part in text.split("\n"))
        ws.Rows(r).RowHeight = min(409, 15 * lines + 4)
    return row + len(paragraphs) + 1


def words(n: int) -> str:
    """A count as the book writes it in prose: a word up to ten, digits above."""
    return ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][n] if 0 <= n <= 10 \
        else f"{n:,}"


def series(items: list[str]) -> str:
    """a, b, and c."""
    items = list(items)
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def note(ws, addr: str, text: str) -> None:
    ws.Range(addr).AddComment(text)
    ws.Range(addr).Comment.Shape.Width = 320
    ws.Range(addr).Comment.Shape.Height = 150


def col(n: int) -> str:
    """Column letter of a 1-based column number."""
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# --- Exercise 7.1 ---------------------------------------------------------------------------------------------------

def quarterly(d: Data) -> dict[str, list[float]]:
    rows = d.q("SELECT i.ItemGroup, CAST(substr(si.InvoiceDate, 1, 4) AS INT), "
               "(CAST(substr(si.InvoiceDate, 6, 2) AS INT) + 2) / 3, SUM(l.LineTotal) FROM SalesInvoiceLine l "
               "JOIN SalesInvoice si USING (SalesInvoiceID) JOIN Item i USING (ItemID) GROUP BY 1, 2, 3")
    qv = {(g, y, k): v for g, y, k, v in rows}
    return {g: [qv.get((g, y, k), 0.0) for y in d.years for k in range(1, 5)] for g in GROUPS}


def ex7_1_expected(d: Data) -> dict:
    s = quarterly(d)
    idx = list(range(1, 13))
    out = {}
    for g in GROUPS:
        v = s[g]
        actual = v[8:12]
        a, b = line_fit(idx[:8], v[:8])
        a2, b2 = line_fit(idx[1:8], v[1:8])
        fc = {"Trend": [a + b * x for x in range(9, 13)], "Mean": [statistics.mean(v[:8])] * 4,
              "Same quarter last year": v[4:8], "Trend without Q1": [a2 + b2 * x for x in range(9, 13)],
              "Mean without Q1": [statistics.mean(v[1:8])] * 4}
        errors = {m: mape(f, actual) for m, f in fc.items()}
        a3, b3 = line_fit(idx[1:], v[1:])
        final = {"Trend": a3 + b3 * 13, "Mean": statistics.mean(v[1:]), "Same quarter last year": v[8]}
        out[g] = dict(series=v, errors=errors, final=final, mean12=statistics.mean(v), low=min(v), high=max(v))
    totals = [sum(s[g][i] for g in GROUPS) for i in range(12)]
    months = d.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                 "JOIN SalesInvoice si USING (SalesInvoiceID) WHERE CAST(substr(si.InvoiceDate, 1, 4) AS INT) "
                 "BETWEEN ? AND ? GROUP BY 1 ORDER BY 1", d.F, d.C)
    company = 3 * statistics.mean(v for _, v in months[1:])          # Tutorial 7.1, Forecast!B47
    return dict(groups=out, totals=totals, company=company)


# The chosen method of each group (Requirement 3): the note's reading of the backtest, fitted without the start-up quarter
CHOSEN = {"Furniture": "Mean", "Lighting": "Trend", "Textiles": "Mean", "Accessories": "Mean", "Services": "Mean"}


def ex7_1(b: ExerciseBuild) -> None:
    d = data(b)
    e = ex7_1_expected(d)
    ws = ex_sheet(b, "Ex 7.1")
    gcols = "CDEFG"
    values(ws, {"A1": "Exercise 7.1: quarterly revenue by item group (InvoiceLines), a backtest of three forecasting "
                      f"methods, and a forecast of {d.N}-Q1"})
    bold(ws, "A1")
    # Requirement 1: the quarterly table
    values(ws, {"A3": "QuarterIndex", "B3": "Period", "H3": "Total"})
    for c, g in zip(gcols, GROUPS):
        ws.Range(f"{c}3").Value = g
    ws.Range("B4:B15").NumberFormat = "@"
    for i in range(12):
        r = 4 + i
        y, k = d.years[i // 4], i % 4 + 1
        ws.Cells(r, 1).Value = i + 1
        ws.Cells(r, 2).Value = f"{y}-Q{k}"
        for c in gcols:
            ws.Range(f"{c}{r}").Formula = f"=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],{c}$3,InvoiceLines[Period],$B{r})"
        ws.Range(f"H{r}").Formula = f"=SUM(C{r}:G{r})"
    values(ws, {"A16": "Control total"})
    ws.Range("H16").Formula = "=SUM(H4:H15)-SUM(InvoiceLines[LineTotal])"
    # Requirement 2: the backtest
    values(ws, {"A18": f"Backtest: each method fitted to the quarters of {d.F} and {d.P} (QuarterIndex 1 to 8), forecasting "
                       f"the four quarters of {d.C}; the last two methods leave out {d.F}-Q1, which holds the start-up month",
                "A19": "QuarterIndex", "B19": "Method"})
    for c, g in zip(gcols, GROUPS):
        ws.Range(f"{c}19").Value = g
    blocks = [("Trend", "=FORECAST.LINEAR($A{r},{c}$4:{c}$11,$A$4:$A$11)"),
              ("Mean", "=AVERAGE({c}$4:{c}$11)"),
              ("Same quarter last year", "={c}{prev}"),
              (f"Trend without {d.F}-Q1", "=FORECAST.LINEAR($A{r},{c}$5:{c}$11,$A$5:$A$11)"),
              (f"Mean without {d.F}-Q1", "=AVERAGE({c}$5:{c}$11)")]
    for bi, (method, f) in enumerate(blocks):
        for j in range(4):
            r = 20 + 4 * bi + j
            ws.Cells(r, 1).Value = 9 + j
            ws.Cells(r, 2).Value = method
            for c in gcols:
                ws.Range(f"{c}{r}").Formula = f.format(r=r, c=c, prev=8 + j)
    values(ws, {"A41": f"Mean absolute percentage error over {d.C}-Q1 to {d.C}-Q4", "B42": "Method"})
    for c, g in zip(gcols, GROUPS):
        ws.Range(f"{c}42").Value = g
    for bi, (method, _) in enumerate(blocks):
        r = 43 + bi
        ws.Cells(r, 2).Value = method
        first = 20 + 4 * bi
        for c in gcols:
            ws.Range(f"{c}{r}").Formula2 = f"=AVERAGE(ABS({c}{first}:{c}{first + 3}-{c}$12:{c}$15)/{c}$12:{c}$15)"
    values(ws, {"B48": "Lowest of the first three", "B49": "Lowest of all five"})
    for c in gcols:
        ws.Range(f"{c}48").Formula = f"=INDEX($B$43:$B$45,MATCH(MIN({c}43:{c}45),{c}43:{c}45,0))"
        ws.Range(f"{c}49").Formula = f"=INDEX($B$43:$B$47,MATCH(MIN({c}43:{c}47),{c}43:{c}47,0))"
    # Requirement 4: the forecast of N-Q1
    values(ws, {"A51": f"Forecast of {d.N}-Q1 with the chosen method, fitted to {d.F}-Q2 to {d.C}-Q4 (QuarterIndex 2 to 12)",
                "B52": "Item", "H52": "Sum of groups", "B53": "Chosen method (Trend, Mean, or Same quarter last year)",
                "B54": f"Forecast, {d.N}-Q1", "B55": "Backtest error of the method (fitted without the start-up quarter)",
                "B56": "Low", "B57": "High", "B59": "Reference: mean of all twelve quarters", "B60": "Lowest quarter",
                "B61": "Highest quarter", "B63": "Company forecast of Tutorial 7.1 (Forecast!B47)",
                "B64": "Sum of the item-group forecasts", "B65": "Difference", "B66": "Difference, % of the company forecast",
                "B67": "Sum of the item groups' means without the start-up quarter"})
    for c, g in zip(gcols, GROUPS):
        ws.Range(f"{c}52").Value = g
        ws.Range(f"{c}53").Value = CHOSEN[g]
        formulas(ws, {
            f"{c}54": (f'=SWITCH({c}53,"Trend",FORECAST.LINEAR(13,{c}5:{c}15,$A$5:$A$15),"Mean",AVERAGE({c}5:{c}15),'
                       f'"Same quarter last year",{c}12)'),
            f"{c}55": f'=SWITCH({c}53,"Trend",{c}46,"Mean",{c}47,"Same quarter last year",{c}45)',
            f"{c}56": f"={c}54*(1-{c}55)", f"{c}57": f"={c}54*(1+{c}55)",
            f"{c}59": f"=AVERAGE({c}4:{c}15)", f"{c}60": f"=MIN({c}4:{c}15)", f"{c}61": f"=MAX({c}4:{c}15)"})
    blue(ws, "C53:G53")
    formulas(ws, {"H54": "=SUM(C54:G54)", "H56": "=SUM(C56:G56)", "H57": "=SUM(C57:G57)", "H59": "=SUM(C59:G59)",
                  "C63": "=Forecast!B47", "C64": "=H54", "C65": "=C64-C63", "C66": "=C65/C63",
                  "C67": "=AVERAGE(C5:C15)+AVERAGE(D5:D15)+AVERAGE(E5:E15)+AVERAGE(F5:F15)+AVERAGE(G5:G15)"})
    ws.Range("C4:H16").NumberFormat = MONEY
    ws.Range("C20:G39").NumberFormat = MONEY
    ws.Range("C43:G47").NumberFormat = PCT
    ws.Range("C54:H54").NumberFormat = MONEY
    ws.Range("C55:G55").NumberFormat = PCT
    ws.Range("C56:H61").NumberFormat = MONEY
    ws.Range("C63:C65").NumberFormat = MONEY
    ws.Range("C66").NumberFormat = PCT
    ws.Range("C67").NumberFormat = MONEY
    for addr in ("A3:H3", "A19:G19", "B42:G42", "B52:H52", "A18", "A41", "A51"):
        bold(ws, addr)
    ws.Columns("A").ColumnWidth = 13
    ws.Columns("B").ColumnWidth = 30
    ws.Columns("C:H").ColumnWidth = 15

    # Model answer
    g = e["groups"]
    er = lambda grp, m: g[grp]["errors"][m]
    fin = {grp: g[grp]["final"][CHOSEN[grp]] for grp in GROUPS}
    total = sum(fin.values())
    means_wo = sum(g[grp]["final"]["Mean"] for grp in GROUPS)
    diff = total - e["company"]
    lowest = e["totals"].index(min(e["totals"])) == 0
    acc = g["Accessories"]["series"][1:]
    turns = sum(1 for x, y, z in zip(acc, acc[1:], acc[2:]) if (y - x) * (z - y) < 0)
    acc_text = ("its quarterly revenue rises and falls with no steady direction, so a level forecast is the safer choice"
                if turns >= (len(acc) - 2) / 2 else "the difference is small, and a level forecast is the simpler choice")
    changed = [(grp, m, er(grp, m), er(grp, f"{m} without Q1")) for grp in GROUPS for m in ("Trend", "Mean")]
    fell = [c for c in changed if c[3] < c[2]]
    rose = [c for c in changed if c[3] >= c[2]]
    best = max(fell, key=lambda c: c[2] - c[3]) if fell else None
    three = ("Trend", "Mean", "Same quarter last year")
    lowest_of = lambda grp, methods: min(methods, key=lambda m: er(grp, m))
    fur_best = lowest_of("Furniture", list(g["Furniture"]["errors"])) == "Mean without Q1"
    lig_best = lowest_of("Lighting", ["Trend without Q1", "Mean without Q1", "Same quarter last year"]) == "Trend without Q1"
    tex_best = (lowest_of("Textiles", three) == "Mean"
                and lowest_of("Textiles", list(g["Textiles"]["errors"])) == "Mean without Q1")
    svc = [er("Services", m) for m in three]
    widest = max(GROUPS, key=lambda grp: g[grp]["errors"][{"Trend": "Trend without Q1", "Mean": "Mean without Q1"}
                                                        .get(CHOSEN[grp], CHOSEN[grp])])
    lighting_part = fin["Lighting"] - g["Lighting"]["final"]["Mean"]
    paras = [
        "Requirement 3, the choice by item group (errors are the mean absolute percentage errors of the backtest, "
        "rows 43 to 47):",
        f"Furniture: the mean. Fitted to all eight quarters, the same quarter last year does slightly better "
        f"({er('Furniture', 'Same quarter last year'):.1%} against {er('Furniture', 'Mean'):.1%}; the trend misses by "
        f"{er('Furniture', 'Trend'):.1%}), but with {d.F}-Q1 left out the mean's error falls to "
        f"{er('Furniture', 'Mean without Q1'):.1%}" + (", the lowest of all," if fur_best else ",")
        + " and a level forecast does not hang on a single quarter.",
        f"Lighting: the trend ({er('Lighting', 'Trend'):.1%}, against {er('Lighting', 'Mean'):.1%} for the mean and "
        f"{er('Lighting', 'Same quarter last year'):.1%} for the same quarter last year). Lighting's revenue grew in {d.C}, "
        "which a level forecast misses. Without the start-up quarter the trend's backtest error is "
        f"{er('Lighting', 'Trend without Q1'):.1%}" + (", still the lowest for Lighting," if lig_best else ",")
        + " and the slope no longer leans on the depressed first quarter, so the forecast is fitted without it.",
        f"Textiles: the mean ({er('Textiles', 'Mean'):.1%}; {er('Textiles', 'Mean without Q1'):.1%} without {d.F}-Q1)"
        + (", the lowest error with or without the start-up quarter." if tex_best else "."),
        f"Accessories: the mean ({er('Accessories', 'Mean'):.1%}), narrowly ahead of the same quarter last year "
        f"({er('Accessories', 'Same quarter last year'):.1%}). Without {d.F}-Q1 the trend does better "
        f"({er('Accessories', 'Trend without Q1'):.1%}), but {acc_text}.",
        f"Services: the mean ({er('Services', 'Mean'):.1%}), but every method misses by {min(svc):.0%} to {max(svc):.0%}: "
        "Services revenue rests on a small number of design-service lines a month, so it is volatile under every method "
        "and its forecast needs a wide range.",
        f"The first quarter of {d.F}: leave it out. It contains January {d.F}, the start-up month"
        + (", and is the company's lowest quarter by far" if lowest else "")
        + ", so it understates every group's level, tilts every trend, and makes the same-quarter forecast of "
        f"{d.P}-Q1 too low. In the backtest, leaving it out lowers the error of {words(len(fell))} of the ten trend and "
        "mean forecasts (rows 46 and 47 against rows 43 and 44)"
        + (f", most for the {best[0]} {best[1].lower()} ({best[2]:.1%} to {best[3]:.1%})" if best else "")
        + ((", and raises it for " + series(f"the {c[0]} {c[1].lower()} ({c[2]:.1%} to {c[3]:.1%})" for c in rose))
           if rose else "")
        + ". The forecasts of requirement 4 are therefore fitted to QuarterIndex 2 to 12.",
        f"Requirement 4: with these methods the item groups sum to {total:,.0f} for {d.N}-Q1, {diff:+,.0f} "
        f"({diff / e['company']:+.1%}) against the company-level forecast of Tutorial 7.1, {e['company']:,.0f}. "
        + (f"Most of the difference is Lighting's trend, which carries its {d.C} growth forward ({fin['Lighting']:,.0f} "
           f"against a mean of {g['Lighting']['final']['Mean']:,.0f}). " if abs(lighting_part) > abs(diff) / 2 else "")
        + f"With the mean for every group the sum would be {means_wo:,.0f} "
        f"({(means_wo - e['company']) / e['company']:+.1%}); the rest of the gap is that the company forecast leaves out "
        f"only January {d.F}, not the whole first quarter. Each range is the chosen method's backtest error without the "
        f"start-up quarter, so {widest} carries the widest. The bank should receive the item-group forecasts with their "
        "ranges and a note that they need not add up to the company forecast, because the methods differ.",
    ]
    model_answer(ws, 70, paras)

    t = "7.1"
    b.check(t, "control total of the quarterly table (Ex 7.1!H16)", 0, "='Ex 7.1'!H16", 0.01)
    for i in range(12):
        b.check(t, f"company revenue, {d.years[i // 4]}-Q{i % 4 + 1} (H{4 + i})", round(e["totals"][i], 2),
                f"='Ex 7.1'!H{4 + i}", 0.01)
    labels = [("Trend", 43), ("Mean", 44), ("Same quarter last year", 45), ("Trend without Q1", 46),
              ("Mean without Q1", 47)]
    for c, grp in zip(gcols, GROUPS):
        for m, r in labels:
            b.check(t, f"{grp}, error of {m.lower().replace('q1', f'{d.F}-Q1')} ({c}{r})", round(g[grp]["errors"][m], 9),
                    f"='Ex 7.1'!{c}{r}", 1e-9, PCT)
    for c, grp in zip(gcols, GROUPS):
        b.check(t, f"{grp} actual revenue, {d.C}-Q1 ({c}12)", round(g[grp]["series"][8], 2), f"='Ex 7.1'!{c}12", 0.01)
    for c, grp in zip(gcols, GROUPS):
        b.check(t, f"{grp} forecast of {d.N}-Q1, {CHOSEN[grp].lower()} ({c}54)", round(fin[grp], 2), f"='Ex 7.1'!{c}54",
                0.01)
    for c, grp in zip(gcols, GROUPS):
        b.check(t, f"{grp} mean of all twelve quarters, the note's reference ({c}59)", round(g[grp]["mean12"], 2),
                f"='Ex 7.1'!{c}59", 0.01)
    b.check(t, "Furniture lowest quarter (C60)", round(g["Furniture"]["low"], 2), "='Ex 7.1'!C60", 0.01)
    b.check(t, "Furniture highest quarter (C61)", round(g["Furniture"]["high"], 2), "='Ex 7.1'!C61", 0.01)
    b.check(t, "company forecast of Tutorial 7.1 (C63)", round(e["company"], 2), "='Ex 7.1'!C63", 0.01)
    b.check(t, "sum of the item-group forecasts (H54)", round(total, 2), "='Ex 7.1'!H54", 0.01)
    b.check(t, "sum of the groups' means without the start-up quarter (C67)", round(means_wo, 2), "='Ex 7.1'!C67", 0.01)


# --- Exercise 7.2 ---------------------------------------------------------------------------------------------------

GROUP_BUDGET = ('Table.Group({prev}, {"FiscalYear", "AccountID"}, {{"BudgetAmount", each List.Sum([BudgetAmount]), '
                'type nullable number}, {"Rows", each Table.RowCount(_), Int64.Type}})')
GROUP_LINES = ('Table.Group({prev}, {"FiscalYear", "AccountID"}, {{"BudgetAmount", each List.Sum([BudgetAmount]), '
               'type nullable number}})')


def ex7_2_expected(d: Data) -> dict:
    cats = "BudgetCategory IN ('Revenue', 'COGS', 'Operating Expense')"
    years = {}
    for y in d.years:
        summary = dict(d.q("SELECT AccountID, SUM(BudgetAmount) FROM Budget WHERE FiscalYear = ? GROUP BY 1", y))
        detail = dict(d.q(f"SELECT AccountID, SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND {cats} GROUP BY 1", y))
        missing = sum(v for a, v in detail.items() if a not in summary)
        years[y] = dict(summary=sum(summary.values()), detail=sum(detail.values()), missing=missing,
                        rows=d.one("SELECT COUNT(*) FROM Budget WHERE FiscalYear = ?", y),
                        accounts=len(set(summary) | set(detail)),
                        diffs={a: detail.get(a, 0) - summary.get(a, 0) for a in set(summary) | set(detail)
                               if abs(detail.get(a, 0) - summary.get(a, 0)) > 0.005})
    blank = d.q("SELECT a.AccountNumber, a.AccountName, COUNT(*), SUM(bl.BudgetAmount) FROM BudgetLine bl "
                f"JOIN Account a USING (AccountID) WHERE bl.FiscalYear = ? AND bl.{cats} AND bl.CostCenterID IS NULL "
                "GROUP BY 1, 2 ORDER BY 1", d.C)
    numbers = dict(d.q("SELECT AccountID, AccountNumber FROM Account"))
    with_cc = d.one(f"SELECT COUNT(*) FROM BudgetLine WHERE FiscalYear = ? AND {cats} AND CostCenterID IS NOT NULL "
                    f"AND AccountID IN ({','.join(str(a) for a in years[d.C]['diffs'])})", d.C)
    return dict(years=years, blank=blank, numbers=numbers, with_cc=with_cc)


def ex7_2(b: ExerciseBuild) -> None:
    d = data(b)
    e = ex7_2_expected(d)
    yc = e["years"][d.C]
    ws = ex_sheet(b, "Ex 7.2")
    load(b, "BudgetSummary", nav(b, 76, "Budget", extra=[
        ("Grouped Rows", GROUP_BUDGET),
        ("Merged Queries", pq.merge("Account", "AccountID", "AccountID", "Account")),
        ("Expanded Account", pq.expand("Account", ["AccountNumber", "AccountName"]))]))
    load(b, "BudgetLineAll", nav(b, 77, "BudgetLine", extra=[
        ("Filtered Rows", pq.select_rows('([BudgetCategory] <> "Balance Sheet")')),
        ("Grouped Rows", GROUP_LINES)]))

    values(ws, {"A1": "Exercise 7.2: reconciling the Budget Table (BudgetSummary) to the budget lines (BudgetLineAll)",
                "A2": "Year", "B2": d.C,
                "A4": "BudgetSummary (T76_Budget)", "A5": "BudgetLineAll (T77_BudgetLine; Revenue, COGS, Operating Expense)",
                "A6": "Difference", "A7": "Accounts whose totals differ", "A8": "Rows of the T76_Budget Table in the year",
                "A9": "BudgetLine rows with a blank CostCenterID (Tutorial 7.2's query, 2026)",
                "A10": "Their BudgetAmount"})
    bold(ws, "A1")
    blue(ws, "B2")
    formulas(ws, {
        "B4": "=SUMIFS(BudgetSummary[BudgetAmount],BudgetSummary[FiscalYear],$B$2)",
        "B5": "=SUMIFS(BudgetLineAll[BudgetAmount],BudgetLineAll[FiscalYear],$B$2)",
        "B6": "=ROUND(B5-B4,2)", "B7": "=ROWS(H13#)",
        "B8": "=SUMIFS(BudgetSummary[Rows],BudgetSummary[FiscalYear],$B$2)",
        "B9": '=COUNTIFS(BudgetLine[CostCenterID],"")',
        "B10": '=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[CostCenterID],"")'})
    ws.Range("A9").Value = f"BudgetLine rows with a blank CostCenterID (Tutorial 7.2's query, {d.C})"
    # Requirement 4: the comparison by year
    values(ws, {"D3": "Comparison by year (requirements 3 and 4)", "D4": "Year", "E4": "BudgetSummary",
                "F4": "BudgetLineAll", "G4": "Difference", "H4": "BudgetLineAll on accounts missing from BudgetSummary"})
    for i, y in enumerate(d.years):
        r = 5 + i
        ws.Cells(r, 4).Value = y
        formulas(ws, {
            f"E{r}": f"=SUMIFS(BudgetSummary[BudgetAmount],BudgetSummary[FiscalYear],D{r})",
            f"F{r}": f"=SUMIFS(BudgetLineAll[BudgetAmount],BudgetLineAll[FiscalYear],D{r})",
            f"G{r}": f"=ROUND(F{r}-E{r},2)",
            f"H{r}": (f"=SUM(FILTER(BudgetLineAll[BudgetAmount],(BudgetLineAll[FiscalYear]=D{r})*"
                      f"ISNA(XMATCH(BudgetLineAll[AccountID],FILTER(BudgetSummary[AccountID],BudgetSummary[FiscalYear]=D{r})))))")})
    # Requirement 3: the comparison by account, and the differences
    values(ws, {"A12": "AccountID", "B12": "AccountNumber", "C12": "AccountName", "D12": "BudgetSummary",
                "E12": "BudgetLineAll", "F12": "Difference", "H11": "Accounts whose totals differ",
                "H12": "AccountNumber", "I12": "AccountName", "J12": "BudgetSummary", "K12": "BudgetLineAll",
                "L12": "Difference", "N11": f"Their rows in Tutorial 7.2's BudgetLine query ({d.C})",
                "N12": "Rows with a blank CostCenterID", "O12": "Their BudgetAmount", "P12": "Rows with a cost center"})
    formulas(ws, {
        "A13": ("=LET(ids,UNIQUE(VSTACK(FILTER(BudgetSummary[AccountID],BudgetSummary[FiscalYear]=$B$2),"
                "FILTER(BudgetLineAll[AccountID],BudgetLineAll[FiscalYear]=$B$2))),"
                "SORTBY(ids,XLOOKUP(ids,Account[AccountID],Account[AccountNumber])))"),
        "B13": "=XLOOKUP(A13#,Account[AccountID],Account[AccountNumber])",
        "C13": "=XLOOKUP(A13#,Account[AccountID],Account[AccountName])",
        "D13": "=SUMIFS(BudgetSummary[BudgetAmount],BudgetSummary[AccountID],A13#,BudgetSummary[FiscalYear],$B$2)",
        "E13": "=SUMIFS(BudgetLineAll[BudgetAmount],BudgetLineAll[AccountID],A13#,BudgetLineAll[FiscalYear],$B$2)",
        "F13": "=ROUND(E13#-D13#,2)",
        "H13": "=FILTER(HSTACK(B13#,C13#,D13#,E13#,F13#),ABS(F13#)>0.005)",
        "N13": '=COUNTIFS(BudgetLine[AccountNumber],INDEX(H13#,0,1),BudgetLine[CostCenterID],"")',
        "O13": '=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountNumber],INDEX(H13#,0,1),BudgetLine[CostCenterID],"")',
        "P13": '=COUNTIFS(BudgetLine[AccountNumber],INDEX(H13#,0,1),BudgetLine[CostCenterID],"<>")'})
    n = yc["accounts"]
    ws.Range("B4:B6").NumberFormat = MONEY
    ws.Range("B10").NumberFormat = MONEY
    ws.Range("E5:H7").NumberFormat = MONEY
    ws.Range(f"D13:F{12 + n}").NumberFormat = MONEY
    ws.Range(f"J13:L{12 + n}").NumberFormat = MONEY
    ws.Range(f"O13:O{12 + n}").NumberFormat = MONEY
    for addr in ("A12:F12", "H12:P12", "D4:H4", "D3", "H11", "N11"):
        bold(ws, addr)
    ws.Columns("A").ColumnWidth = 44
    ws.Columns("B").ColumnWidth = 16
    ws.Columns("C").ColumnWidth = 30
    ws.Columns("D:F").ColumnWidth = 16
    ws.Columns("H").ColumnWidth = 18
    ws.Columns("I").ColumnWidth = 30
    ws.Columns("J:L").ColumnWidth = 16
    ws.Columns("N:P").ColumnWidth = 16

    blank = e["blank"]
    gaps = {y: e["years"][y]["detail"] - e["years"][y]["summary"] for y in d.years}
    names = ", ".join(f"{num} {name}" for num, name, _, _ in blank)
    rows_blank = sum(r[2] for r in blank)
    paras = [
        f"Requirement 3: {len(yc['diffs'])} accounts differ, and in each the whole BudgetLineAll total is missing from "
        f"BudgetSummary: {names}. Their BudgetLine rows have one thing in common, a blank CostCenterID: "
        f"{rows_blank} operating-expense rows, twelve months for each account, and no row of these accounts has a cost "
        "center. Every other account agrees to the cent.",
        "Memo (requirement 5). To: the controller. Subject: the budget summary sent to the bank.",
        f"The Budget Table, from which last year's budget summary for the bank was prepared, totals {yc['summary']:,.2f} for "
        f"{d.C}, while the budget lines (revenue, cost of goods sold, and operating expenses) total {yc['detail']:,.2f}. The "
        f"difference, {gaps[d.C]:,.2f}, is exactly the {rows_blank} operating-expense lines that have no cost center. The "
        "Budget Table summarizes the budget by cost center, so lines without one never reach it, and the accounts budgeted "
        f"only that way ({len(blank)} accounts, listed above) are missing from it altogether. The same gap appears in "
        f"every year: {gaps[d.F]:,.2f} in {d.F} and {gaps[d.P]:,.2f} in {d.P}, so the summaries sent to the bank "
        "understated budgeted operating expenses, and overstated budgeted profit, by "
        f"{min(gaps.values()) / 1e6:.1f} to {max(gaps.values()) / 1e6:.1f} million dollars a year.",
        "The budget sent to the bank should be prepared from the BudgetLine Table, which is complete, or from the Budget "
        "Table only after the unassigned lines have been assigned to cost centers and the two agree.",
        "Recommended control: whenever the budget is approved or revised, reconcile the summary to the detail by year and "
        "account, with a check that the difference is zero, and have the reconciliation reviewed and signed off before any "
        "summary leaves the company. In the budgeting system, require a cost center on every operating-expense line, or "
        "assign lines without one to an Unassigned cost center so that they reach the summary.",
    ]
    model_answer(ws, 15 + n, paras, last_col="F")

    t = "7.2"
    b.check(t, f"BudgetSummary total, {d.C} (Ex 7.2!B4)", round(yc["summary"], 2), "='Ex 7.2'!B4", 0.01)
    b.check(t, f"BudgetLineAll total, {d.C} (B5)", round(yc["detail"], 2), "='Ex 7.2'!B5", 0.01)
    b.check(t, f"difference, {d.C} (B6)", round(gaps[d.C], 2), "='Ex 7.2'!B6", 0.01)
    b.check(t, "accounts whose totals differ (B7)", len(yc["diffs"]), "='Ex 7.2'!B7", 0, COUNT)
    b.check(t, f"rows of the T76_Budget Table in {d.C} (B8)", yc["rows"], "='Ex 7.2'!B8", 0, COUNT)
    b.check(t, "BudgetLine rows with a blank CostCenterID (B9)", rows_blank, "='Ex 7.2'!B9", 0, COUNT)
    b.check(t, "their BudgetAmount equals the difference (B10)", round(sum(r[3] for r in blank), 2), "='Ex 7.2'!B10", 0.01)
    for num, name, _, amount in blank:
        b.check(t, f"difference on {num} {name}", round(amount, 2),
                f"=XLOOKUP({num},INDEX('Ex 7.2'!H13#,0,1),INDEX('Ex 7.2'!H13#,0,5))", 0.01)
    b.check(t, "rows of the differing accounts that have a cost center (P13#)", e["with_cc"], "=SUM('Ex 7.2'!P13#)", 0, COUNT)
    b.check(t, "blank-cost-center rows behind the differences (N13#)", rows_blank, "=SUM('Ex 7.2'!N13#)", 0, COUNT)
    for i, y in enumerate(d.years):
        r = 5 + i
        b.check(t, f"difference, {y} (G{r})", round(gaps[y], 2), f"='Ex 7.2'!G{r}", 0.01)
        b.check(t, f"BudgetLineAll on accounts missing from BudgetSummary, {y} (H{r})", round(e["years"][y]["missing"], 2),
                f"='Ex 7.2'!H{r}", 0.01)


# --- Exercise 7.3 ---------------------------------------------------------------------------------------------------

def ex7_3_expected(d: Data) -> dict:
    revenue, cost = d.q("SELECT SUM(l.LineTotal), SUM(l.Quantity * i.StandardCost) FROM SalesInvoiceLine l "
                        "JOIN SalesInvoice si USING (SalesInvoiceID) JOIN Item i USING (ItemID) "
                        "WHERE substr(si.InvoiceDate, 1, 4) = ?", str(d.C))[0]
    commissions = d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                        d.account(6290), d.C)
    opex = d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory = 'Operating Expense'", d.C)
    budget_commission = d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND AccountID = ?",
                              d.C, d.account(6290))
    added = {n: d.one("SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                      "AND SourceDocumentType <> 'JournalEntry'", d.account(n), d.C) for n in (5050, 5060, 5080)}
    variance = {y: d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                         d.account(5080), y) for y in d.years}
    cm = revenue - cost - commissions
    ratio = cm / revenue
    fixed = opex - budget_commission
    fixed2 = fixed + sum(added.values())
    return dict(revenue=revenue, cost=cost, commissions=commissions, cm=cm, ratio=ratio, opex=opex,
                budget_commission=budget_commission, fixed=fixed, be=fixed / ratio, added=added, fixed2=fixed2,
                be2=fixed2 / ratio, goal=(4_000_000 + fixed2) / ratio, goal_without=(4_000_000 + fixed) / ratio,
                variance=variance)


def ex7_3(b: ExerciseBuild) -> None:
    d = data(b)
    e = ex7_3_expected(d)
    ids = {n: d.account(n) for n in (5050, 5060, 5080)}
    ws = ex_sheet(b, "Ex 7.3")
    cond = " or ".join(f"[AccountID] = {ids[n]}" for n in (5050, 5060, 5080))
    load(b, "GLCostVariances", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", pq.select_rows(f"([FiscalYear] = {d.C})")),
        ("Filtered Rows1", pq.select_rows(f"({cond})")),
        ("Filtered Rows2", pq.select_rows('([SourceDocumentType] <> "JournalEntry")'))]))
    names = dict(d.q("SELECT AccountNumber, AccountName FROM Account WHERE AccountNumber IN (5050, 5060, 5080)"))
    values(ws, {"A1": f"Exercise 7.3: company break-even and margin of safety, {d.C}", "A3": "Year", "B3": d.C,
                "A5": "Revenue (InvoiceLines)", "A6": "Standard cost of the products sold (InvoiceLines)",
                "A7": "Sales commission expense (GLOpex, account 6290)", "A8": "Contribution margin",
                "A9": "Contribution margin ratio",
                "A11": "Operating-expense budget (BudgetLine)", "A12": "Less: sales commission budget (account 6290)",
                "A13": "Fixed costs (requirement 2)", "A14": "Break-even revenue", "A15": "Margin of safety",
                "A16": "Margin of safety, % of revenue",
                "A18": "Requirement 4: items GLOpex does not contain (GLCostVariances)",
                "A19": f"5050 {names[5050]}", "A20": f"5060 {names[5060]}", "A21": f"5080 {names[5080]}",
                "A22": "Added items", "A23": "Fixed costs with the added items", "A24": "Break-even revenue",
                "A25": "Margin of safety", "A26": "Margin of safety, % of revenue",
                "A28": "Requirement 5: target operating income", "B28": 4000000,
                "A29": "Revenue (changed by Goal Seek)", "A30": "Operating income at that revenue (B29 x B9 - B23)",
                "A31": "Check: (target + fixed costs) / ratio", "A32": "The same without the added items"})
    bold(ws, "A1")
    blue(ws, "B3")
    blue(ws, "B28")
    formulas(ws, {
        "B5": "=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[FiscalYear],$B$3)",
        "B6": "=SUMIFS(InvoiceLines[StdCostAmount],InvoiceLines[FiscalYear],$B$3)",
        "B7": "=SUMIFS(GLOpex[Amount],GLOpex[AccountNumber],6290)",
        "B8": "=B5-B6-B7", "B9": "=B8/B5",
        "B11": '=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[BudgetCategory],"Operating Expense")',
        "B12": "=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountNumber],6290)",
        "B13": "=B11-B12", "B14": "=B13/B9", "B15": "=B5-B14", "B16": "=B15/B5",
        "B22": "=SUM(B19:B21)", "B23": "=B13+B22", "B24": "=B23/B9", "B25": "=B5-B24", "B26": "=B25/B5",
        "B30": "=B29*B9-B23", "B31": "=(B28+B23)/B9", "B32": "=(B28+B13)/B9"})
    for r, n in zip((19, 20, 21), (5050, 5060, 5080)):
        ws.Range(f"B{r}").Formula = (f"=SUMIFS(GLCostVariances[Debit],GLCostVariances[AccountID],{ids[n]})-"
                                     f"SUMIFS(GLCostVariances[Credit],GLCostVariances[AccountID],{ids[n]})")
    ws.Range("B5:B8").NumberFormat = MONEY
    ws.Range("B9").NumberFormat = PCT
    ws.Range("B11:B15").NumberFormat = MONEY
    ws.Range("B16").NumberFormat = PCT
    ws.Range("B19:B25").NumberFormat = MONEY
    ws.Range("B26").NumberFormat = PCT
    ws.Range("B28:B32").NumberFormat = MONEY
    # Requirement 5: a two-variable data table of break-even revenue (fixed costs down, ratio across)
    ratios = [round(0.40 + 0.01 * i, 2) for i in range(11)]
    fixeds = [6_000_000 + 500_000 * i for i in range(9)]
    values(ws, {"D2": "Break-even revenue: fixed costs (down) by contribution margin ratio (across); "
                      "a data table with B9 as the row input cell and B23 as the column input cell"})
    ws.Range("D3").Formula = "=B24"
    for i, rv in enumerate(ratios):
        ws.Cells(3, 5 + i).Value = rv
    for i, fv in enumerate(fixeds):
        ws.Cells(4 + i, 4).Value = fv
    last_col, last_row = col(4 + len(ratios)), 3 + len(fixeds)
    ws.Range(f"D3:{last_col}{last_row}").Table(ws.Range("B9"), ws.Range("B23"))
    ws.Range(f"E3:{last_col}3").NumberFormat = "0%"
    ws.Range(f"D4:D{last_row}").NumberFormat = "#,##0"
    ws.Range(f"E4:{last_col}{last_row}").NumberFormat = "#,##0"
    ws.Range("D3").NumberFormat = "#,##0"
    bold(ws, "D2")
    # Goal Seek: the revenue that gives the target operating income under requirement 4's assumptions
    ws.Range("B29").Value = round(e["revenue"], 2)
    ws.Range("B30").GoalSeek(4000000, ws.Range("B29"))
    ws.Columns("A").ColumnWidth = 52
    ws.Columns("B").ColumnWidth = 18
    ws.Columns("C").ColumnWidth = 3
    ws.Columns(f"D:{last_col}").ColumnWidth = 12
    note(ws, "B29", "Goal Seek (Data > What-If Analysis > Goal Seek: Set cell B30, To value 4000000, By changing cell "
                    "B29) wrote this value when the solution file was built; it stays as a value. B31 computes the same "
                    "revenue directly and follows the data.")

    i45, i9 = ratios.index(0.45), fixeds.index(9_000_000)
    i40, i6 = ratios.index(0.40), fixeds.index(6_000_000)
    per_point = e["fixed2"] / e["ratio"] ** 2 / 100
    v = e["variance"]
    paras = [
        "Requirement 2: the operating-expense budget is a reasonable source for the fixed costs because Charles River's "
        "operating expenses are salaries, rent, depreciation, insurance, and other recurring costs that do not move with "
        "sales volume, and Tutorial 7.2 showed that every budgeted account except the payroll burden and the commissions "
        "came within a few percent of actual. The commission budget is taken out because commissions vary with revenue "
        "and are already in the contribution margin.",
        f"Memo (requirement 6). With {d.C} as the base, the contribution margin ratio is {e['ratio']:.1%} (revenue less the "
        "standard cost of the products sold and sales commissions). With the operating-expense budget less commissions as "
        f"the fixed costs ({e['fixed']:,.0f}), revenue could fall to {e['be']:,.0f} before the operating profit disappeared, "
        f"a margin of safety of {e['revenue'] - e['be']:,.0f}, or {1 - e['be'] / e['revenue']:.1%} of {d.C} revenue. That "
        f"estimate is too optimistic, because it leaves out freight-out and the purchase price and manufacturing variances, "
        f"{sum(e['added'].values()):,.0f} in {d.C}, which the ledger reports with cost of goods sold but the standard costs "
        f"do not include. With them, break-even revenue rises to {e['be2']:,.0f} and the margin of safety falls to "
        f"{1 - e['be2'] / e['revenue']:.1%}; earning an operating income of $4 million would take revenue of "
        f"{e['goal']:,.0f}, close to the {e['revenue']:,.0f} of {d.C}.",
        f"The assumption that affects the estimate most is the treatment of the manufacturing variance "
        f"({e['added'][5080]:,.0f})"
        + (", larger than the other added items together" if e["added"][5080] > e["added"][5050] + e["added"][5060] else "")
        + (" and growing every year" if v[d.F] < v[d.P] < v[d.C] else "")
        + f" ({v[d.F]:,.0f}, {v[d.P]:,.0f}, {v[d.C]:,.0f} in {d.F} to {d.C}). It is treated as fixed, but it comes from "
        "the plant's hours and "
        "overhead, part of which would fall with volume; if it returned to its "
        f"{d.F} level, break-even revenue would fall by about {round((v[d.C] - v[d.F]) / e['ratio'], -3):,.0f}. The contribution "
        "margin ratio matters too: at these fixed "
        f"costs each percentage point of the ratio moves break-even revenue by about {round(per_point, -3):,.0f}, as the data table "
        "shows. Two further simplifications are worth naming: Services' design staff are treated as fixed (Services "
        "carries no standard cost), and all of the products' standard cost as variable, though it includes fixed overhead.",
    ]
    model_answer(ws, 35, paras, last_col="H")

    t = "7.3"
    rows = [("B5", "revenue", e["revenue"]), ("B6", "standard cost of the products sold", e["cost"]),
            ("B7", "sales commission expense (6290, without the close)", e["commissions"]),
            ("B8", "contribution margin", e["cm"]), ("B11", "operating-expense budget", e["opex"]),
            ("B12", "commission budget", e["budget_commission"]), ("B13", "fixed costs", e["fixed"]),
            ("B14", "break-even revenue", e["be"]), ("B15", "margin of safety", e["revenue"] - e["be"])]
    for addr, label, value in rows:
        b.check(t, f"{label} (Ex 7.3!{addr})", round(value, 2), f"='Ex 7.3'!{addr}", 0.01)
    b.check(t, "contribution margin ratio (B9)", round(e["ratio"], 9), "='Ex 7.3'!B9", 1e-9, PCT)
    b.check(t, "margin of safety, % of revenue (B16)", round(1 - e["be"] / e["revenue"], 9), "='Ex 7.3'!B16", 1e-9, PCT)
    for r, n in zip((19, 20, 21), (5050, 5060, 5080)):
        b.check(t, f"{n} {names[n]}, {d.C} without journal entries (B{r})", round(e["added"][n], 2), f"='Ex 7.3'!B{r}", 0.01)
    b.check(t, "added items (B22)", round(sum(e["added"].values()), 2), "='Ex 7.3'!B22", 0.01)
    b.check(t, "break-even revenue with the added items (B24)", round(e["be2"], 2), "='Ex 7.3'!B24", 0.01)
    b.check(t, "margin of safety with the added items, % (B26)", round(1 - e["be2"] / e["revenue"], 9), "='Ex 7.3'!B26",
            1e-9, PCT)
    b.check(t, "Goal Seek's revenue for an operating income of 4,000,000 (B29)", round(e["goal"], 2), "='Ex 7.3'!B29", 0.01)
    b.check(t, "operating income at Goal Seek's revenue (B30)", 4000000, "='Ex 7.3'!B30", 0.01)
    b.check(t, "the same revenue computed directly (B31)", round(e["goal"], 2), "='Ex 7.3'!B31", 0.01)
    b.check(t, "the revenue without the added items (B32)", round(e["goal_without"], 2), "='Ex 7.3'!B32", 0.01)
    for ri, fi in ((i45, i9), (i40, i6)):
        addr = f"{col(5 + ri)}{4 + fi}"
        b.check(t, f"data table: ratio {ratios[ri]:.0%}, fixed costs {fixeds[fi]:,} ({addr})",
                round(fixeds[fi] / ratios[ri], 2), f"='Ex 7.3'!{addr}", 0.01)


# --- Exercise 7.4: linear programming -------------------------------------------------------------------------------

def _inverse(m: list[list[float]]) -> list[list[float]]:
    n = len(m)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        if abs(a[p][c]) < 1e-12:
            raise ValueError("singular basis")
        a[c], a[p] = a[p], a[c]
        piv = a[c][c]
        a[c] = [v / piv for v in a[c]]
        for r in range(n):
            if r != c and a[r][c] != 0:
                f = a[r][c]
                a[r] = [x - f * y for x, y in zip(a[r], a[c])]
    return [row[n:] for row in a]


def solve_lp(c: list[float], A: list[list[float]], b: list[float], u: list[float], tol: float = 1e-9) -> dict:
    """Maximize c.x subject to A x <= b and 0 <= x <= u (b >= 0), by the bounded-variable primal simplex method, the
    method of Solver's Simplex LP engine, with Bland's rule against cycling. Returns the solution, the shadow prices y of
    the constraints, the reduced costs d, and the final basis (for the sensitivity analysis)."""
    m, n = len(A), len(c)
    total = n + m
    cost = list(c) + [0.0] * m
    upper = list(u) + [math.inf] * m
    cols = [[A[i][j] for i in range(m)] for j in range(n)] + \
           [[1.0 if i == k else 0.0 for i in range(m)] for k in range(m)]
    basis = list(range(n, total))
    at_upper = [False] * total
    for _ in range(100_000):
        binv = _inverse([[cols[j][i] for j in basis] for i in range(m)])
        rhs = list(b)
        inb = set(basis)
        for j in range(total):
            if at_upper[j] and j not in inb:
                rhs = [r - cols[j][i] * upper[j] for i, r in enumerate(rhs)]
        xb = [sum(binv[k][i] * rhs[i] for i in range(m)) for k in range(m)]
        y = [sum(cost[basis[k]] * binv[k][i] for k in range(m)) for i in range(m)]
        enter = None
        for j in range(total):
            if j in inb:
                continue
            dj = cost[j] - sum(y[i] * cols[j][i] for i in range(m))
            if (not at_upper[j] and dj > tol) or (at_upper[j] and dj < -tol):
                enter = j
                break
        if enter is None:
            break
        sign = 1.0 if not at_upper[enter] else -1.0
        alpha = [sum(binv[k][i] * cols[enter][i] for i in range(m)) for k in range(m)]
        step, leave, to_upper = upper[enter], None, False
        for k in range(m):
            dlt = sign * alpha[k]
            if dlt > tol:
                r, up = max(xb[k], 0.0) / dlt, False
            elif dlt < -tol and upper[basis[k]] < math.inf:
                r, up = max(upper[basis[k]] - xb[k], 0.0) / -dlt, True
            else:
                continue
            if r < step - 1e-12 or (leave is not None and abs(r - step) <= 1e-12 and basis[k] < basis[leave]):
                step, leave, to_upper = r, k, up
        if step == math.inf:
            raise ValueError("the linear program is unbounded")
        if leave is None:
            at_upper[enter] = not at_upper[enter]          # the entering variable moves to its other bound
            continue
        at_upper[basis[leave]] = to_upper
        at_upper[enter] = False
        basis[leave] = enter
    else:
        raise RuntimeError("the simplex method did not converge")
    x = [upper[j] if at_upper[j] else 0.0 for j in range(total)]
    for k, j in enumerate(basis):
        x[j] = xb[k]
    d = [cost[j] - sum(y[i] * cols[j][i] for i in range(m)) for j in range(total)]
    return dict(x=x[:n], y=y, d=d, basis=basis, at_upper=at_upper, binv=binv, xb=xb, cols=cols, upper=upper,
                objective=sum(ci * xi for ci, xi in zip(c, x[:n])))


def sensitivity(s: dict, n: int, tol: float = 1e-9) -> tuple[list[dict], list[dict]]:
    """The Sensitivity report of a linear model: each variable's reduced cost and the range of its objective coefficient
    over which the solution stays optimal; each constraint's shadow price and the range of its right-hand side over
    which the shadow price holds. Simple bounds on the variables are not listed as constraints; their dual values are
    the reduced costs, as in Solver's report."""
    m = len(s["y"])
    basis, binv, xb, cols, upper, at_upper, d = (s[k] for k in ("basis", "binv", "xb", "cols", "upper", "at_upper", "d"))
    inb = {j: k for k, j in enumerate(basis)}
    nonbasic = [j for j in range(n + m) if j not in inb]
    variables = []
    for j in range(n):
        if j in inb:
            k, inc, dec = inb[j], BIG, BIG
            for jj in nonbasic:
                a = sum(binv[k][i] * cols[jj][i] for i in range(m))
                if abs(a) < tol:
                    continue
                if not at_upper[jj]:                      # its reduced cost must stay <= 0
                    if a < 0:
                        inc = min(inc, d[jj] / a)
                    else:
                        dec = min(dec, -d[jj] / a)
                elif a > 0:                               # at its upper bound: its reduced cost must stay >= 0
                    inc = min(inc, d[jj] / a)
                else:
                    dec = min(dec, d[jj] / -a)
            variables.append(dict(reduced=0.0, inc=max(inc, 0.0), dec=max(dec, 0.0)))
        elif at_upper[j]:
            variables.append(dict(reduced=d[j], inc=BIG, dec=d[j]))
        else:
            variables.append(dict(reduced=d[j], inc=-d[j], dec=BIG))
    constraints = []
    for i in range(m):
        if n + i in inb:                                  # not binding: its slack is basic
            constraints.append(dict(inc=BIG, dec=xb[inb[n + i]]))
            continue
        inc = dec = BIG
        for k, j in enumerate(basis):
            g = binv[k][i]
            if abs(g) < tol:
                continue
            room = upper[j] - xb[k]
            if g > 0:
                inc = min(inc, room / g) if upper[j] < math.inf else inc
                dec = min(dec, xb[k] / g)
            else:
                inc = min(inc, xb[k] / -g)
                dec = min(dec, room / -g) if upper[j] < math.inf else dec
        constraints.append(dict(inc=max(inc, 0.0), dec=max(dec, 0.0)))
    return variables, constraints


def commission_rate(d: Data) -> float:
    """Tutorial 7.3's CommissionRate: the report year's commission expense (6290, without the close) over its revenue."""
    expense = d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}",
                    d.account(6290), d.C)
    revenue = d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
                    "WHERE substr(si.InvoiceDate, 1, 4) = ?", str(d.C))
    return expense / revenue


def ex7_4_expected(d: Data) -> dict:
    rate = commission_rate(d)
    items = d.q("SELECT i.ItemID, i.ItemCode, i.ItemGroup, i.StandardCost - i.StandardFixedOverheadCost, i.RoutingID, "
                "SUM(l.Quantity), SUM(l.LineTotal) FROM Item i JOIN SalesInvoiceLine l USING (ItemID) "
                "JOIN SalesInvoice si USING (SalesInvoiceID) WHERE i.SupplyMode = 'Manufactured' "
                "AND substr(si.InvoiceDate, 1, 4) = ? GROUP BY 1 ORDER BY 1", str(d.C))
    items = [r for r in items if r[5] > 0]
    unsold = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured'") - len(items)
    centers = d.q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter ORDER BY WorkCenterID")
    available = dict(d.q("SELECT WorkCenterID, SUM(AvailableHours) FROM WorkCenterCalendar "
                         "WHERE substr(CalendarDate, 1, 4) = ? GROUP BY 1", str(d.C)))
    run = {(r, w): h for r, w, h in d.q("SELECT RoutingID, WorkCenterID, SUM(StandardRunHoursPerUnit) "
                                        "FROM RoutingOperation GROUP BY 1, 2")}
    demand = [r[5] for r in items]
    price = [r[6] / r[5] for r in items]
    unit = [p - r[3] - rate * p for p, r in zip(price, items)]
    A = [[run.get((r[4], w), 0.0) for r in items] for w, _ in centers]
    cap = [available.get(w, 0.0) / 2 for w, _ in centers]
    s = solve_lp(unit, A, cap, demand)
    var, con = sensitivity(s, len(items))
    used = [sum(a * x for a, x in zip(row, s["x"])) for row in A]
    need = [sum(a * q for a, q in zip(row, demand)) for row in A]
    binding = [i for i in range(len(centers)) if cap[i] - used[i] < 1e-6]
    # Setup hours, which the exercise leaves out, spread over each item's average work-order quantity in the year
    setup = {(r, w): h for r, w, h in d.q("SELECT RoutingID, WorkCenterID, SUM(StandardSetupHours) "
                                          "FROM RoutingOperation GROUP BY 1, 2")}
    lots = dict(d.q("SELECT ItemID, AVG(PlannedQuantity) FROM WorkOrder WHERE substr(ReleasedDate, 1, 4) = ? GROUP BY 1",
                    str(d.C)))
    setup_loss = None
    if all(lots.get(r[0]) for r in items):
        A2 = [[A[i][j] + setup.get((items[j][4], w), 0.0) / lots[items[j][0]] for j in range(len(items))]
              for i, (w, _) in enumerate(centers)]
        s2 = solve_lp(unit, A2, cap, demand)
        setup_loss = sum(c * q for c, q in zip(unit, demand)) - s2["objective"]
    return dict(rate=rate, items=items, unsold=unsold, centers=centers, available=available, demand=demand, price=price,
                unit=unit, A=A, cap=cap, s=s, var=var, con=con, used=used, need=need, binding=binding,
                full=sum(c * q for c, q in zip(unit, demand)), setup_loss=setup_loss)


SOLVER_DEFAULTS = {"solver_cvg": "0.0001", "solver_drv": "1", "solver_est": "1", "solver_itr": "2147483647",
                   "solver_lin": "1", "solver_mip": "2147483647", "solver_mni": "30", "solver_mrt": "0.075",
                   "solver_msl": "2", "solver_neg": "1", "solver_nod": "2147483647", "solver_nwt": "1",
                   "solver_pre": "0.000001", "solver_rbv": "1", "solver_rlx": "2", "solver_rsd": "0",
                   "solver_scl": "1", "solver_sho": "2", "solver_ssz": "100", "solver_tim": "2147483647",
                   "solver_tol": "0.01", "solver_val": "0", "solver_ver": "3"}


def save_solver_model(ws, objective: str, variables: str, constraints: list[tuple[str, int, str]]) -> None:
    """Solver keeps its model in hidden worksheet-level names; writing them is what Solver's Save does, so Data > Solver
    opens this model: maximize the objective (solver_typ 1) with Simplex LP (solver_eng 2), unconstrained variables
    non-negative (solver_neg 1)."""
    sheet = "'" + ws.Name.replace("'", "''") + "'"
    items = dict(SOLVER_DEFAULTS)
    items.update(solver_opt=f"{sheet}!{objective}", solver_typ="1", solver_adj=f"{sheet}!{variables}", solver_eng="2",
                 solver_num=str(len(constraints)))
    for i, (lhs, rel, rhs) in enumerate(constraints, start=1):
        items[f"solver_lhs{i}"] = f"{sheet}!{lhs}"
        items[f"solver_rel{i}"] = str(rel)
        items[f"solver_rhs{i}"] = f"{sheet}!{rhs}"
    for name, refers in items.items():
        ws.Names.Add(Name=name, RefersTo=f"={refers}", Visible=False)


def ex7_4(b: ExerciseBuild) -> None:
    d = data(b)
    e = ex7_4_expected(d)
    items, centers, s = e["items"], e["centers"], e["s"]
    n, m = len(items), len(centers)
    short = [name.replace(" Work Center", "") for _, name in centers]
    assert len(e["binding"]) >= 1, "no work center binds: the exercise's constraint does not bite"
    bind = e["binding"][0]
    first, last = 21, 20 + n
    hcol = [col(10 + i) for i in range(m)]               # J, K, ... : the run hours per unit at each work center
    pcol = col(10 + m)                                   # contribution per hour of the binding work center

    ws = ex_sheet(b, "Ex 7.4")
    ans = after_last(b, "Ex 7.4 Answer Report")
    sen = after_last(b, "Ex 7.4 Sensitivity Report")
    load(b, "ItemRouting", nav(b, 44, "Item", extra=[("Removed Other Columns", pq.select_columns(
        ["ItemID", "ItemCode", "ItemGroup", "StandardCost", "StandardFixedOverheadCost", "SupplyMode", "RoutingID"]))]))
    load(b, "RoutingOperation", nav(b, 50, "RoutingOperation"))
    load(b, "WorkCenter", nav(b, 47, "WorkCenter"))
    load(b, "WorkCenterCalendar", nav(b, 48, "WorkCenterCalendar"))

    values(ws, {"A1": "Exercise 7.4: the product mix when every work center has half its "
                      f"{d.C} hours (a hypothetical constraint)",
                "A2": "Year of demand and capacity", "B2": d.C, "A3": "Commission rate (Tutorial 7.3, Model!B7)",
                "A4": "Total contribution (Solver's objective)", "A5": f"Contribution if all {d.C} demand were met",
                "A6": "Contribution lost", "A7": f"Manufactured items sold in {d.C}",
                "A8": f"Manufactured items not sold in {d.C}"})
    bold(ws, "A1")
    blue(ws, "B2")
    formulas(ws, {"B3": "=CommissionRate", "B4": f"=SUMPRODUCT(H{first}:H{last},I{first}:I{last})",
                  "B5": f"=SUMPRODUCT(H{first}:H{last},E{first}:E{last})", "B6": "=B5-B4", "B7": "=ROWS(A21#)",
                  "B8": '=COUNTIFS(ItemRouting[SupplyMode],"Manufactured")-B7'})
    values(ws, {"A10": "WorkCenterID", "B10": "Work center", "C10": f"Available hours, {d.C}", "D10": "Capacity (half)",
                "E10": "Hours to meet all demand", "F10": "Demand / capacity", "G10": "Hours used (SUMPRODUCT)",
                "H10": "Slack", "I10": "Status", "J10": "Shadow price (Sensitivity Report)"})
    formulas(ws, {
        "A11": "=SORT(WorkCenter[WorkCenterID])",
        "B11": "=XLOOKUP(A11#,WorkCenter[WorkCenterID],WorkCenter[WorkCenterName])",
        "C11": ('=SUMIFS(WorkCenterCalendar[AvailableHours],WorkCenterCalendar[WorkCenterID],A11#,'
                'WorkCenterCalendar[CalendarDate],">="&DATE($B$2,1,1),WorkCenterCalendar[CalendarDate],"<"&DATE($B$2+1,1,1))'),
        "D11": "=C11#/2"})
    for i in range(m):
        r = 11 + i
        h = hcol[i]
        formulas(ws, {f"E{r}": f"=SUMPRODUCT({h}${first}:{h}${last},$E${first}:$E${last})", f"F{r}": f"=E{r}/D{r}",
                      f"G{r}": f"=SUMPRODUCT({h}${first}:{h}${last},$I${first}:$I${last})", f"H{r}": f"=D{r}-G{r}",
                      f"I{r}": f'=IF(H{r}<=0.0001,"Binding","Not binding")'})
    values(ws, {"I19": "WorkCenterID", "A20": "ItemID", "B20": "ItemCode", "C20": "ItemGroup", "D20": "RoutingID",
                "E20": f"Demand, {d.C} (units)", "F20": "Average price", "G20": "Variable standard cost",
                "H20": "Contribution per unit", "I20": "Quantity (variable cells)",
                f"{pcol}20": f"Contribution per {short[bind]} hour"})
    formulas(ws, {
        f"{hcol[0]}19": "=TRANSPOSE(A11#)", f"{hcol[0]}20": "=TRANSPOSE(B11#)",
        "A21": ('=SORT(FILTER(ItemRouting[ItemID],(ItemRouting[SupplyMode]="Manufactured")*'
                "(SUMIFS(InvoiceLines[Quantity],InvoiceLines[ItemID],ItemRouting[ItemID],InvoiceLines[FiscalYear],$B$2)>0)))"),
        "B21": "=XLOOKUP(A21#,ItemRouting[ItemID],ItemRouting[ItemCode])",
        "C21": "=XLOOKUP(A21#,ItemRouting[ItemID],ItemRouting[ItemGroup])",
        "D21": "=XLOOKUP(A21#,ItemRouting[ItemID],ItemRouting[RoutingID])",
        "E21": "=SUMIFS(InvoiceLines[Quantity],InvoiceLines[ItemID],A21#,InvoiceLines[FiscalYear],$B$2)",
        "F21": "=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemID],A21#,InvoiceLines[FiscalYear],$B$2)/E21#",
        "G21": "=XLOOKUP(A21#,ItemRouting[ItemID],ItemRouting[StandardCost]-ItemRouting[StandardFixedOverheadCost])",
        "H21": "=F21#-G21#-$B$3*F21#",
        f"{hcol[0]}21": ("=SUMIFS(RoutingOperation[StandardRunHoursPerUnit],RoutingOperation[RoutingID],D21#,"
                         f"RoutingOperation[WorkCenterID],{hcol[0]}19#)"),
        f"{pcol}21": f"=IFERROR(H21#/INDEX({hcol[0]}21#,0,{bind + 1}),\"\")"})
    # The plan a reader starts from (all demand), then Solver's optimum in the variable cells
    ws.Range(f"I{first}:I{last}").Value = tuple((q,) for q in e["demand"])
    b.wb.Application.Calculate()
    start_objective, start_used = ws.Range("B4").Value, [ws.Range(f"G{11 + i}").Value for i in range(m)]
    ws.Range(f"I{first}:I{last}").Value = tuple((x,) for x in s["x"])
    ws.Range(f"I{first}:I{last}").Interior.Color = 0xCCF2FF                 # a light amber tint (BGR)
    blue(ws, f"I{first}:I{last}")
    save_solver_model(ws, "$B$4", f"$I${first}:$I${last}",
                      [(f"$G$11:$G${10 + m}", 1, f"$D$11:$D${10 + m}"), (f"$I${first}:$I${last}", 1, f"$E${first}:$E${last}")])
    note(ws, "I20", "Variable cells. Solver's optimum (Simplex LP; maximize B4; G11:G15 <= D11:D15; I21:I103 <= E21:E103; "
                    "Make Unconstrained Variables Non-Negative; whole units not required), computed from the dataset "
                    "when the solution file was built and written here as values, as Solver leaves them after Keep "
                    "Solver Solution. The model is saved with the worksheet: Data > Solver opens it ready to solve."
                    .replace("G11:G15", f"G11:G{10 + m}").replace("D11:D15", f"D11:D{10 + m}")
                    .replace("I21:I103", f"I{first}:I{last}").replace("E21:E103", f"E{first}:E{last}"))
    # Requirement 5, beside the model: the items Solver reduces
    values(ws, {"L2": "Requirement 5: items Solver makes less of than their demand", "L3": "ItemCode",
                "M3": "Quantity", "N3": "Demand", "O3": f"Contribution per {short[bind]} hour",
                "L1": "Shadow price of the binding work center: the contribution per hour of the item made only in part"})
    formulas(ws, {
        "L4": (f"=FILTER(HSTACK(B21#,I{first}:I{last},E21#,{pcol}21#),I{first}:I{last}<E21#-0.0001)"),
        "Q1": (f"=LET(part,(I{first}:I{last}>0.0001)*(I{first}:I{last}<E21#-0.0001),"
               f"SUM(FILTER({pcol}21#,part)))")})
    # Column L is the requirement-5 block; keep the work center block's widths readable
    ws.Range("B3").NumberFormat = "0.000%"
    ws.Range("B4:B6").NumberFormat = MONEY
    ws.Range(f"C11:H{10 + m}").NumberFormat = MONEY
    ws.Range(f"F11:F{10 + m}").NumberFormat = "0.00"
    ws.Range(f"J11:J{10 + m}").NumberFormat = MONEY
    ws.Range(f"E{first}:I{last}").NumberFormat = MONEY
    ws.Range(f"{hcol[0]}{first}:{hcol[-1]}{last}").NumberFormat = "0.00"
    ws.Range(f"{pcol}{first}:{pcol}{last}").NumberFormat = MONEY
    ws.Range("M4:O40").NumberFormat = MONEY
    ws.Range("Q1").NumberFormat = MONEY
    for addr in ("A10:J10", "A20:O20", "L2", "L3:O3"):
        bold(ws, addr)
    ws.Columns("A").ColumnWidth = 34
    ws.Columns("B").ColumnWidth = 26
    ws.Columns("C:I").ColumnWidth = 14
    ws.Columns(f"{hcol[0]}:{hcol[-1]}").ColumnWidth = 12
    ws.Columns(pcol).ColumnWidth = 14

    # The two reports, in Solver's layout, from the same computation
    book = b.wb.Name
    var, con = e["var"], e["con"]
    header_note = ("Written by the companion builder in the layout of Solver's {kind} Report: Solver itself was not run "
                   "while building. The optimum and its sensitivity analysis were computed from the dataset by the "
                   "bounded-variable simplex method (the method of Solver's Simplex LP) and written here as values, as "
                   "Solver writes its reports. To regenerate the report, choose Data > Solver on Ex 7.4 (the model is "
                   "saved with the worksheet), click Solve, and select Answer and Sensitivity under Reports; Solver "
                   "names them Answer Report 1 and Sensitivity Report 1.")
    names_var = [f"{r[1]} Quantity" for r in items]
    names_con = [f"{name} Hours used" for _, name in centers]
    rows = [("Microsoft Excel Answer Report (written in Solver's layout; see the note)",),
            (f"Worksheet: [{book}]Ex 7.4",), ("Result: Solver found a solution. All Constraints and optimality "
                                              "conditions are satisfied.",),
            ("Solver Engine",), ("", "Engine: Simplex LP"), ("Solver Options",),
            ("", "Max Time Unlimited, Iterations Unlimited, Precision 0.000001, Use Automatic Scaling"),
            ("", "Max Subproblems Unlimited, Max Integer Sols Unlimited, Integer Tolerance 1%, Assume NonNegative"), (),
            ("Objective Cell (Max)",), ("Cell", "Name", "Original Value", "Final Value"),
            ("$B$4", "Total contribution (Solver's objective)", start_objective, s["objective"]), (),
            ("Variable Cells",), ("Cell", "Name", "Original Value", "Final Value", "Integer")]
    rows += [(f"$I${first + j}", names_var[j], e["demand"][j], s["x"][j], "Contin") for j in range(n)]
    rows += [(), ("Constraints",), ("Cell", "Name", "Cell Value", "Formula", "Status", "Slack")]
    for i in range(m):
        slack = e["cap"][i] - e["used"][i]
        rows.append((f"$G${11 + i}", names_con[i], e["used"][i], f"$G${11 + i}<=$D${11 + i}",
                     "Binding" if slack < 1e-6 else "Not Binding", max(slack, 0.0)))
    for j in range(n):
        slack = e["demand"][j] - s["x"][j]
        rows.append((f"$I${first + j}", names_var[j], s["x"][j], f"$I${first + j}<=$E${first + j}",
                     "Binding" if slack < 1e-6 else "Not Binding", max(slack, 0.0)))
    write_report(ans, rows, money_cols=(3, 4, 6))
    note(ans, "B1", header_note.format(kind="Answer"))
    del start_used

    srows = [("Microsoft Excel Sensitivity Report (written in Solver's layout; see the note)",),
             (f"Worksheet: [{book}]Ex 7.4",), (), ("Variable Cells",),
             ("", "", "Final", "Reduced", "Objective", "Allowable", "Allowable"),
             ("Cell", "Name", "Value", "Cost", "Coefficient", "Increase", "Decrease")]
    srows += [(f"$I${first + j}", names_var[j], s["x"][j], var[j]["reduced"], e["unit"][j], var[j]["inc"], var[j]["dec"])
              for j in range(n)]
    srows += [(), ("Constraints",), ("", "", "Final", "Shadow", "Constraint", "Allowable", "Allowable"),
              ("Cell", "Name", "Value", "Price", "R.H. Side", "Increase", "Decrease")]
    con_top = len(srows) + 1
    srows += [(f"$G${11 + i}", names_con[i], e["used"][i], s["y"][i], e["cap"][i], con[i]["inc"], con[i]["dec"])
              for i in range(m)]
    write_report(sen, srows, money_cols=(3, 4, 5, 6, 7))
    note(sen, "B1", header_note.format(kind="Sensitivity"))
    for i in range(m):
        ws.Range(f"J{11 + i}").Formula = f"='Ex 7.4 Sensitivity Report'!E{con_top + i}"   # column E holds Shadow Price

    # Model answer: the recommendation
    reduced = [(items[j][1], s["x"][j], e["demand"][j]) for j in range(n) if s["x"][j] < e["demand"][j] - 1e-6]
    loss = e["full"] - s["objective"]
    need = {short[i]: e["need"][i] / e["cap"][i] for i in range(m)}
    over = [k for k, v in need.items() if v > 1]
    nb = sorted((i for i in range(m) if i not in e["binding"]), key=lambda i: e["cap"][i] - e["used"][i])
    nxt = nb[0]
    listing = "; ".join(f"{code} ({x:,.1f} of {q:,.1f} units)" for code, x, q in reduced)
    paras = [
        f"To: the operations manager. Subject: the product mix while the upgrade halves every work center's hours.",
        f"At {d.C} demand, half of each work center's {d.C} hours would not be enough in "
        + " and ".join(f"{k} ({need[k]:.0%} of the halved capacity)" for k in over)
        + "; the other centers would have room. Solving for the mix that earns the most contribution (Solver, Simplex LP), "
        + ("only " if len(e["binding"]) == 1 else "")
        + " and ".join(short[i] for i in e["binding"]) + f" binds: it uses all of its {e['cap'][bind]:,.0f} hours, while "
        f"{short[nxt]} ends just under its limit ({e['used'][nxt]:,.0f} of {e['cap'][nxt]:,.0f} hours) and would bind "
        "next. Every other center has slack.",
        f"The plan makes every item in full except {words(len(reduced))}: {listing}. These are the items with the lowest "
        f"contribution per {short[bind]} hour. The plan earns a total contribution of {s['objective']:,.0f}, "
        f"{loss:,.0f} less than meeting all demand ({e['full']:,.0f}).",
        f"Each additional {short[bind]} hour is worth about ${s['y'][bind]:,.2f} of contribution (the shadow price), for "
        f"up to {con[bind]['inc']:,.0f} more hours, according to the Sensitivity report. Overtime, an extra shift, or "
        f"outsourced assembly that costs less than that per hour would pay for itself, so {short[bind]} hours are the ones "
        "to protect: schedule the upgrade so that it keeps as much of its capacity as possible, give it priority to the "
        f"items with the highest contribution per {short[bind]} hour, and discuss the reduced items with sales, since "
        "customers may accept later delivery or the items could be bought in.",
        "Limits of the model: demand and prices are fixed at their 2026 levels, quantities need not be whole, standard "
        "run hours are taken as exact, and setup hours are ignored"
        + (f" (spread over each item's average {d.C} work-order quantity, setup time raises the contribution lost to "
           f"about {round(e['setup_loss'], -3):,.0f})" if e["setup_loss"] is not None else "") + ".",
    ]
    model_answer(ws, last + 3, paras, last_col="I")

    t = "7.4"
    groups = {}
    for r in items:
        groups[r[2]] = groups.get(r[2], 0) + 1
    b.check(t, f"manufactured items sold in {d.C} (Ex 7.4!B7)", n, "='Ex 7.4'!B7", 0, COUNT)
    for g, k in groups.items():
        b.check(t, f"of which {g}", k, f"=COUNTIF('Ex 7.4'!C21#,\"{g}\")", 0, COUNT)
    b.check(t, f"manufactured items not sold in {d.C} (B8)", e["unsold"], "='Ex 7.4'!B8", 0, COUNT)
    b.check(t, "commission rate of Tutorial 7.3 (B3)", round(e["rate"], 12), "='Ex 7.4'!B3", 1e-12, "0.0000%")
    for i in range(m):
        b.check(t, f"{short[i]}: capacity, half of its {d.C} hours (D{11 + i})", round(e["cap"][i], 4),
                f"='Ex 7.4'!D{11 + i}", 0.005)
        b.check(t, f"{short[i]}: hours to meet all demand / capacity (F{11 + i})", round(e["need"][i] / e["cap"][i], 9),
                f"='Ex 7.4'!F{11 + i}", 1e-9, RATIO)
        b.check(t, f"{short[i]}: hours used by the optimum (G{11 + i})", round(e["used"][i], 4), f"='Ex 7.4'!G{11 + i}",
                0.005)
    b.check(t, "total contribution of the optimum (B4)", round(s["objective"], 2), "='Ex 7.4'!B4", 0.01)
    b.check(t, "contribution if all demand were met (B5)", round(e["full"], 2), "='Ex 7.4'!B5", 0.01)
    b.check(t, "contribution lost (B6)", round(loss, 2), "='Ex 7.4'!B6", 0.01)
    b.check(t, "hours used within capacity at every work center", True,
            f"=AND('Ex 7.4'!G11:G{10 + m}<='Ex 7.4'!D11:D{10 + m}+0.0001)", 0, "General")
    b.check(t, "every quantity between zero and its demand", True,
            f"=AND('Ex 7.4'!I{first}:I{last}>=0,'Ex 7.4'!I{first}:I{last}<='Ex 7.4'!E{first}:E{last}+0.0001)", 0, "General")
    b.check(t, "work centers whose capacity binds", len(e["binding"]), f"=COUNTIF('Ex 7.4'!I11:I{10 + m},\"Binding\")", 0,
            COUNT)
    b.check(t, "the binding work center", centers[bind][1],
            f"=INDEX('Ex 7.4'!B11#,MATCH(\"Binding\",'Ex 7.4'!I11:I{10 + m},0))", 0, "@")
    b.check(t, "items Solver reduces (L4#)", len(reduced), "=ROWS('Ex 7.4'!L4#)", 0, COUNT)
    b.check(t, "their codes", ", ".join(code for code, _, _ in reduced), "=TEXTJOIN(\", \",TRUE,INDEX('Ex 7.4'!L4#,0,1))",
            0, "@")
    part = [(code, x) for code, x, q in reduced if x > 1e-6]
    for code, x in part:
        b.check(t, f"{code}, made only in part", round(x, 6), f"=XLOOKUP(\"{code}\",'Ex 7.4'!B21#,'Ex 7.4'!I{first}:I{last})",
                1e-4, MONEY)
    b.check(t, f"shadow price of {short[bind]} hours (Sensitivity Report, J{11 + bind})", round(s["y"][bind], 6),
            f"='Ex 7.4'!J{11 + bind}", 1e-6, MONEY)
    if len(e["binding"]) == 1 and len(part) == 1:
        b.check(t, f"shadow price recomputed live: contribution per {short[bind]} hour of the item made in part (Q1)",
                round(s["y"][bind], 6), "='Ex 7.4'!Q1", 1e-6, MONEY)


def write_report(ws, rows: list[tuple], money_cols: tuple[int, ...]) -> None:
    """Rows of a Solver report from column B (Solver leaves column A narrow and empty)."""
    for r, row in enumerate(rows, start=1):
        for c, v in enumerate(row):
            if v is None or v == "":
                continue
            cell = ws.Cells(r, 2 + c)
            if isinstance(v, str) and v.startswith("$"):
                cell.NumberFormat = "@"
            cell.Value = v
            if isinstance(v, (int, float)) and not isinstance(v, bool) and (1 + c) in money_cols:
                cell.NumberFormat = RANGE_FORMAT
    ws.Columns("A").ColumnWidth = 2
    ws.Columns("B").ColumnWidth = 10
    ws.Columns("C").ColumnWidth = 40
    ws.Columns("D:H").ColumnWidth = 16
    ws.Range("B1").Font.Bold = True


# --- Exercise 7.5 ---------------------------------------------------------------------------------------------------

def ex7_5_expected(d: Data) -> dict:
    revenue = dict(d.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                       "JOIN SalesInvoice si USING (SalesInvoiceID) WHERE CAST(substr(si.InvoiceDate, 1, 4) AS INT) "
                       "BETWEEN ? AND ? GROUP BY 1", d.F, d.C))
    invoices = dict(d.q("SELECT substr(InvoiceDate, 1, 7), COUNT(*) FROM SalesInvoice GROUP BY 1"))
    acc = d.account(6290)
    commission = dict(d.q("SELECT substr(PostingDate, 1, 7), SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? "
                          "AND SourceDocumentType <> 'JournalEntry' GROUP BY 1", acc))
    months = [f"{y}-{k:02d}" for y in d.years for k in range(1, 13)]
    rev = [revenue[mo] for mo in months]
    inv = [invoices[mo] for mo in months]
    com = [commission.get(mo, 0.0) for mo in months]
    with_first = fit_stats(inv, rev)
    without = fit_stats(inv[1:], rev[1:])
    comm = fit_stats(rev[:24], com[:24])
    current = []
    for i in range(24, 36):
        exp = comm["a"] + comm["b"] * rev[i]
        current.append(dict(month=months[i], expected=exp, diff=com[i] - exp, pct=(com[i] - exp) / exp))
    accruals = d.one("SELECT SUM(CommissionAmount) FROM SalesCommissionAccrual WHERE substr(AccrualDate, 1, 4) = ?", str(d.C))
    by_type = dict(d.q("SELECT SourceDocumentType, SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                       "AND SourceDocumentType <> 'JournalEntry' GROUP BY 1", acc, d.C))
    adj_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                     "AND SourceDocumentType = 'SalesCommissionAdjustment'", acc, d.C)
    gl_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry'", acc)
    # The evidence of requirement 4: the accrual rate and the customer mix by month, and accrual dates against invoices
    rates = d.q("SELECT CustomerSegment, MIN(CommissionRatePct), MAX(CommissionRatePct) FROM SalesCommissionAccrual "
                "GROUP BY 1 ORDER BY 2, 1")
    low = rates[0][0]
    mix = {mo: dict(rate=amount / base, low=lb / base) for mo, amount, base, lb in d.q(
        "SELECT substr(AccrualDate, 1, 7), SUM(CommissionAmount), SUM(CommissionBaseAmount), "
        "SUM(CASE WHEN CustomerSegment = ? THEN CommissionBaseAmount ELSE 0 END) FROM SalesCommissionAccrual GROUP BY 1",
        low)}
    year_low = d.one("SELECT SUM(CASE WHEN CustomerSegment = ? THEN CommissionBaseAmount ELSE 0 END) / "
                     "SUM(CommissionBaseAmount) FROM SalesCommissionAccrual WHERE substr(AccrualDate, 1, 4) = ?", low, str(d.C))
    total, other_month, other_day = d.q(
        "SELECT COUNT(*), SUM(substr(a.AccrualDate, 1, 7) <> substr(si.InvoiceDate, 1, 7)), "
        "SUM(a.AccrualDate <> si.InvoiceDate) FROM SalesCommissionAccrual a JOIN SalesInvoice si USING (SalesInvoiceID)")[0]
    return dict(months=months, rev=rev, inv=inv, com=com, with_first=with_first, without=without, comm=comm,
                current=current, average=statistics.mean(rev[1:]), accruals=accruals, by_type=by_type,
                adj_rows=adj_rows, gl_total=sum(com), invoices_total=sum(invoices.values()), gl_rows=gl_rows,
                rates=rates, low=low, mix=mix, year_low=year_low, accrual_count=total, other_month=other_month,
                other_day=other_day)


def ex7_5(b: ExerciseBuild) -> None:
    d = data(b)
    e = ex7_5_expected(d)
    acc = d.account(6290)
    ws = ex_sheet(b, "Ex 7.5")
    load(b, "GLCommission", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", pq.select_rows(f"([AccountID] = {acc})")),
        ("Filtered Rows1", pq.select_rows('([SourceDocumentType] <> "JournalEntry")')),
        ("Added Custom", pq.add_custom("Amount", "[Debit] - [Credit]"))]))
    load(b, "SalesCommissionAccrual", nav(b, 27, "SalesCommissionAccrual"))
    values(ws, {"A1": "Exercise 7.5: regression-based expectations for revenue and sales commission expense",
                "A3": "Month", "B3": "Revenue (InvoiceLines)", "C3": "Invoices (SalesInvoice)",
                "D3": "Commission expense (GLCommission, 6290)", "E3": "Expected commission", "F3": "Difference",
                "G3": "Difference %", "H3": "More than 3%"})
    bold(ws, "A1")
    for i in range(36):
        r = 4 + i
        ws.Range(f"A{r}").Formula = f"=DATE({d.F},1,1)" if i == 0 else f"=EDATE(A{r - 1},1)"
        formulas(ws, {
            f"B{r}": f'=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[InvoiceDate],">="&$A{r},InvoiceLines[InvoiceDate],"<"&EDATE($A{r},1))',
            f"C{r}": f'=COUNTIFS(SalesInvoice[InvoiceDate],">="&$A{r},SalesInvoice[InvoiceDate],"<"&EDATE($A{r},1))',
            f"D{r}": f'=SUMIFS(GLCommission[Amount],GLCommission[PostingDate],">="&$A{r},GLCommission[PostingDate],"<"&EDATE($A{r},1))'})
        if i >= 24:
            formulas(ws, {f"E{r}": f"=$K$18+$K$19*B{r}", f"F{r}": f"=D{r}-E{r}", f"G{r}": f"=F{r}/E{r}",
                          f"H{r}": f'=IF(ABS(G{r})>0.03,"Investigate","")'})
    values(ws, {"A40": "Control totals"})
    formulas(ws, {"B40": "=SUM(B4:B39)-SUM(InvoiceLines[LineTotal])", "C40": "=SUM(C4:C39)-ROWS(SalesInvoice[SalesInvoiceID])",
                  "D40": "=SUM(D4:D39)-SUM(GLCommission[Amount])"})
    ws.Range("A4:A39").NumberFormat = "mmm yyyy"
    ws.Range("B4:B40").NumberFormat = MONEY
    ws.Range("C4:C40").NumberFormat = COUNT
    ws.Range("D4:F40").NumberFormat = MONEY
    ws.Range("G4:G39").NumberFormat = "0.0%"
    # Requirement 2: revenue on the number of invoices
    values(ws, {"J3": "Requirement 2: revenue on the number of invoices", "J4": "R Square, all 36 months",
                "J5": f"R Square, without January {d.F}", "J6": "Standard error, all 36 months",
                "J7": f"Standard error, without January {d.F}", "J8": f"Slope per invoice, without January {d.F}",
                "J9": f"Average monthly revenue, February {d.F} to December {d.C}", "J10": "Standard error / average",
                "J11": "5% of average monthly revenue", "J12": "Standard error / 5% of average",
                "J14": "Requirement 3: commission expense on revenue, 2024 and 2025",
                "J15": f"R Square, {d.F} and {d.P}", "J16": "Standard error", "J17": "Observations",
                "J18": "Intercept", "J19": "Slope (commission per dollar of revenue)",
                "J21": "Requirement 4: months flagged (difference above 3%)",
                "J22": "Largest difference among the other months",
                "J24": f"Requirement 5: reconciliation of {d.C} commission expense", "J25": f"Accruals dated in {d.C} (SalesCommissionAccrual)",
                "J26": f"GL 6290, {d.C}: SalesCommissionAccrual postings", "J27": f"GL 6290, {d.C}: SalesCommissionAdjustment postings",
                "J28": "SalesCommissionAdjustment rows", "J29": f"GL 6290, {d.C} (without the closing entry)",
                "J30": "Accruals less GL expense", "J31": "Unexplained difference (accruals + adjustments - GL)"})
    for a in ("J3", "J14", "J21", "J24"):
        bold(ws, a)
    y_ = f"DATE({d.C},1,1)"
    formulas(ws, {
        "K4": "=RSQ(B4:B39,C4:C39)", "K5": "=RSQ(B5:B39,C5:C39)", "K6": "=STEYX(B4:B39,C4:C39)",
        "K7": "=STEYX(B5:B39,C5:C39)", "K8": "=SLOPE(B5:B39,C5:C39)", "K9": "=AVERAGE(B5:B39)", "K10": "=K7/K9",
        "K11": "=0.05*K9", "K12": "=K7/K11",
        "K15": "=RSQ(D4:D27,B4:B27)", "K16": "=STEYX(D4:D27,B4:B27)", "K17": "=COUNT(D4:D27)",
        "K18": "=INTERCEPT(D4:D27,B4:B27)", "K19": "=SLOPE(D4:D27,B4:B27)",
        "K21": '=COUNTIF(H28:H39,"Investigate")', "K22": '=MAX(FILTER(ABS(G28:G39),H28:H39=""))',
        "K25": (f'=SUMIFS(SalesCommissionAccrual[CommissionAmount],SalesCommissionAccrual[AccrualDate],">="&{y_},'
                f'SalesCommissionAccrual[AccrualDate],"<"&DATE({d.N},1,1))'),
        "K26": f'=SUMIFS(GLCommission[Amount],GLCommission[FiscalYear],{d.C},GLCommission[SourceDocumentType],"SalesCommissionAccrual")',
        "K27": f'=SUMIFS(GLCommission[Amount],GLCommission[FiscalYear],{d.C},GLCommission[SourceDocumentType],"SalesCommissionAdjustment")',
        "K28": f'=COUNTIFS(GLCommission[FiscalYear],{d.C},GLCommission[SourceDocumentType],"SalesCommissionAdjustment")',
        "K29": f"=SUMIFS(GLCommission[Amount],GLCommission[FiscalYear],{d.C})", "K30": "=K25-K29",
        "K31": "=ROUND(K25+K27-K29,2)"})
    low = e["low"]
    values(ws, {"M3": "Accrual rate (SalesCommissionAccrual)", "N3": f"{low} share of the commission base",
                "P3": "CustomerSegment", "Q3": "Lowest rate", "R3": "Highest rate"})
    acc_dates = 'SalesCommissionAccrual[AccrualDate],">="&$A{r},SalesCommissionAccrual[AccrualDate],"<"&EDATE($A{r},1)'
    for i in range(36):
        r = 4 + i
        dates = acc_dates.format(r=r)
        formulas(ws, {
            f"M{r}": (f"=SUMIFS(SalesCommissionAccrual[CommissionAmount],{dates})/"
                      f"SUMIFS(SalesCommissionAccrual[CommissionBaseAmount],{dates})"),
            f"N{r}": (f'=SUMIFS(SalesCommissionAccrual[CommissionBaseAmount],SalesCommissionAccrual[CustomerSegment],"{low}",'
                      f"{dates})/SUMIFS(SalesCommissionAccrual[CommissionBaseAmount],{dates})")})
    formulas(ws, {"P4": ("=SORTBY(UNIQUE(SalesCommissionAccrual[CustomerSegment]),MAXIFS(SalesCommissionAccrual[CommissionRatePct],"
                         "SalesCommissionAccrual[CustomerSegment],UNIQUE(SalesCommissionAccrual[CustomerSegment])),1)"),
                  "Q4": "=MINIFS(SalesCommissionAccrual[CommissionRatePct],SalesCommissionAccrual[CustomerSegment],P4#)",
                  "R4": "=MAXIFS(SalesCommissionAccrual[CommissionRatePct],SalesCommissionAccrual[CustomerSegment],P4#)"})
    ws.Range("M4:M39").NumberFormat = "0.000%"
    ws.Range("N4:N39").NumberFormat = "0.0%"
    ws.Range("Q4:R12").NumberFormat = "0.0%"
    bold(ws, "M3:R3")
    ws.Columns("L").ColumnWidth = 3
    ws.Columns("M:N").ColumnWidth = 16
    ws.Columns("O").ColumnWidth = 3
    ws.Columns("P").ColumnWidth = 18
    ws.Columns("Q:R").ColumnWidth = 12
    ws.Range("K4:K5").NumberFormat = RATIO
    ws.Range("K6:K9").NumberFormat = MONEY
    ws.Range("K10").NumberFormat = PCT
    ws.Range("K11").NumberFormat = MONEY
    ws.Range("K12").NumberFormat = "0.00"
    ws.Range("K15").NumberFormat = RATIO
    ws.Range("K16").NumberFormat = MONEY
    ws.Range("K18").NumberFormat = MONEY
    ws.Range("K19").NumberFormat = "0.000000"
    ws.Range("K22").NumberFormat = PCT
    ws.Range("K25:K27").NumberFormat = MONEY
    ws.Range("K28").NumberFormat = COUNT
    ws.Range("K29:K31").NumberFormat = MONEY
    bold(ws, "A3:H3")
    ws.Columns("A").ColumnWidth = 11
    ws.Columns("B:H").ColumnWidth = 15
    ws.Columns("I").ColumnWidth = 3
    ws.Columns("J").ColumnWidth = 52
    ws.Columns("K").ColumnWidth = 16
    b.wb.Application.Calculate()

    # The Analysis ToolPak's regressions, in the tool's layout (frozen, as Tutorial 7.1's)
    sheet = "'Ex 7.5'"
    r36 = regression_output(b.wb, "Ex 7.5 Revenue36", ws, f"{sheet}!$B$4:$B$39", f"{sheet}!$C$4:$C$39",
                            "Invoices", "Revenue")
    r35 = regression_output(b.wb, "Ex 7.5 Revenue35", r36, f"{sheet}!$B$5:$B$39", f"{sheet}!$C$5:$C$39", "Invoices",
                            "Revenue")
    rc = regression_output(b.wb, "Ex 7.5 Commission", r35, f"{sheet}!$D$4:$D$27", f"{sheet}!$B$4:$B$27", "Revenue",
                           "Commission")
    for reg, what in ((r36, "revenue (Ex 7.5!B4:B39) on invoices (C4:C39), all 36 months"),
                      (r35, f"revenue (Ex 7.5!B5:B39) on invoices (C5:C39), without January {d.F}"),
                      (rc, f"commission expense (Ex 7.5!D4:D27) on revenue (B4:B27), {d.F} and {d.P}")):
        note(reg, "A1", f"Analysis ToolPak Regression of {what}, with Residuals and Residual Plots. Written by the "
                        "companion builder in the tool's layout, computed with LINEST and frozen as values, as the "
                        "tool writes them; the live equivalents are on Ex 7.5, column K.")

    w, wo, cm = e["with_first"], e["without"], e["comm"]
    cur = e["current"]
    flagged = [c for c in cur if abs(c["pct"]) > 0.03]
    others = [c for c in cur if abs(c["pct"]) <= 0.03]
    mname = lambda c: f"{['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][int(c['month'][5:]) - 1]}"
    pairs = [(a, c) for a, c in zip(cur, cur[1:]) if a in flagged and c in flagged and a["diff"] * c["diff"] < 0]
    flag_text = ", ".join(f"{mname(c)} {c['diff']:+,.0f} ({c['pct']:+.1%})" for c in flagged)
    pair_text = (f"The {mname(pairs[0][0])} and {mname(pairs[0][1])} differences have opposite signs and nearly offset, "
                 "the pattern of a shift between two months rather than a misstatement of the year"
                 if pairs else "The differences do not offset one another")
    mix, low, yl = e["mix"], e["low"], e["year_low"]
    rate_text = ", ".join(f"{seg} {lo:.1%}" for seg, lo, _ in e["rates"])
    paired = {c["month"] for pr in pairs for c in pr}

    def explained(c):
        share = mix[c["month"]]["low"]
        return (c["diff"] < 0) == (share > yl)          # more low-rate business, lower expense than revenue predicts

    evidence = []
    if pairs:
        a_, c_ = pairs[0]
        evidence.append(
            f"The evidence settles it. Accrual dates agree with invoice dates on all but {e['other_day']} of the "
            f"{e['accrual_count']:,} accruals ({e['other_month']} fall in another month), so accruals are not booked in the "
            f"wrong month. The rates differ by customer segment ({rate_text}, columns P to R), and {low} customers, at the "
            f"lowest rate, made up {mix[a_['month']]['low']:.0%} of {mname(a_)}'s commission base against "
            f"{mix[c_['month']]['low']:.0%} of {mname(c_)}'s (column N; {yl:.0%} for {d.C}), so the accrual rate was "
            f"{mix[a_['month']]['rate']:.2%} in {mname(a_)} and {mix[c_['month']]['rate']:.2%} in {mname(c_)} (column M). "
            + ("The offsetting differences come from the customer mix, which a regression on total revenue cannot see, "
               "not from an error." if explained(a_) and explained(c_) else
               "The customer mix explains only part of the offsetting differences, so the accruals need recomputing."))
    for c in flagged:
        if c["month"] in paired:
            continue
        evidence.append(
            f"{mname(c)} has no offsetting month; its {low} share was {mix[c['month']]['low']:.0%} against {yl:.0%} for "
            "the year, " + ("so the mix explains its difference too. " if explained(c) else
                            "so the mix does not explain its difference. ")
            + "I would still recompute a sample of its accruals from their invoice lines and the rate table and examine "
            "the credit-memo adjustments posted in the month.")
    evidence.append("A more precise expectation for commissions would multiply each segment's revenue by its rate.")
    adj = e["by_type"].get("SalesCommissionAdjustment", 0.0)
    paras = [
        "Memo to the audit senior. Subject: regression-based expectations for revenue and commissions.",
        f"Revenue on the number of invoices: R Square is {w['r2']:.3f} with January {d.F} and {wo['r2']:.3f} without it; "
        f"the start-up month, with few invoices and little revenue, makes the fit look better than it is. Without it, "
        f"each invoice adds about {wo['b']:,.0f} of revenue, but the standard error, {wo['se']:,.0f}, is "
        f"{wo['se'] / e['average']:.1%} of average monthly revenue ({e['average']:,.0f}). A 5% misstatement of a month "
        f"({0.05 * e['average']:,.0f}) is "
        + ("smaller than" if 0.05 * e["average"] < wo["se"] else "about") + " one standard error, within the ordinary "
        "scatter of the months around the line, so the "
        "expectation could not reliably detect it and is not precise enough for a substantive analytical procedure at "
        "that level.",
        f"Commission expense on revenue fits closely: fitted on {d.F} and {d.P}, the intercept is {cm['a']:,.2f}, the slope "
        f"{cm['b']:.5f}, and R Square {cm['r2']:.3f}. In {d.C}, {words(len(flagged))} months differ from the expectation by more "
        f"than 3%: {flag_text}; every other month is within {max(abs(c['pct']) for c in others):.1%}. {pair_text}. For "
        "each flagged month the evidence to examine is the accrual dates against the invoice dates around the month-end, "
        "the commission rates applied (the customer mix), and the credit-memo adjustments posted in the month.",
        " ".join(evidence),
        f"Reconciliation: the accruals dated in {d.C} total {e['accruals']:,.2f}. The ledger's {d.C} commission expense, "
        f"{sum(v for v in e['by_type'].values()):,.2f}, is the accrual postings less {e['adj_rows']} "
        f"SalesCommissionAdjustment rows ({-adj:,.2f}), which reverse commissions on credit memos; that source document "
        "type explains the whole difference.",
    ]
    model_answer(ws, 43, paras, last_col="H")

    t = "7.5"
    b.check(t, "control total of monthly revenue (Ex 7.5!B40)", 0, "='Ex 7.5'!B40", 0.01)
    b.check(t, "control total of invoices (C40)", 0, "='Ex 7.5'!C40", 0, COUNT)
    b.check(t, "control total of commission expense (D40)", 0, "='Ex 7.5'!D40", 0.01)
    b.check(t, "GLCommission rows (6290 without journal entries)", e["gl_rows"], "=ROWS(GLCommission[GLEntryID])", 0, COUNT)
    b.check(t, "R Square, revenue on invoices, all months (K4)", round(w["r2"], 9), "='Ex 7.5'!K4", 1e-9, RATIO)
    b.check(t, f"R Square, without January {d.F} (K5)", round(wo["r2"], 9), "='Ex 7.5'!K5", 1e-9, RATIO)
    b.check(t, "R Square on the ToolPak output, all months (Ex 7.5 Revenue36!B5)", round(w["r2"], 9),
            "='Ex 7.5 Revenue36'!B5", 1e-9, RATIO)
    b.check(t, "R Square on the ToolPak output, without the start-up month (Ex 7.5 Revenue35!B5)", round(wo["r2"], 9),
            "='Ex 7.5 Revenue35'!B5", 1e-9, RATIO)
    b.check(t, "standard error, all months (K6)", round(w["se"], 4), "='Ex 7.5'!K6", 0.001)
    b.check(t, f"standard error, without January {d.F} (K7)", round(wo["se"], 4), "='Ex 7.5'!K7", 0.001)
    b.check(t, "slope per invoice, without the start-up month (K8)", round(wo["b"], 6), "='Ex 7.5'!K8", 1e-6)
    b.check(t, "average monthly revenue without the start-up month (K9)", round(e["average"], 4), "='Ex 7.5'!K9", 0.001)
    b.check(t, "standard error / average (K10)", round(wo["se"] / e["average"], 9), "='Ex 7.5'!K10", 1e-9, PCT)
    b.check(t, f"commission on revenue, R Square, {d.F}-{d.P} (K15)", round(cm["r2"], 9), "='Ex 7.5'!K15", 1e-9, RATIO)
    b.check(t, "R Square on the ToolPak output (Ex 7.5 Commission!B5)", round(cm["r2"], 9), "='Ex 7.5 Commission'!B5",
            1e-9, RATIO)
    b.check(t, "intercept (K18)", round(cm["a"], 6), "='Ex 7.5'!K18", 1e-6)
    b.check(t, "slope (K19)", round(cm["b"], 12), "='Ex 7.5'!K19", 1e-12, "0.000000000")
    for i, c in enumerate(cur):
        if c in flagged:
            r = 28 + i
            b.check(t, f"{c['month']}: difference from the expectation (F{r})", round(c["diff"], 4), f"='Ex 7.5'!F{r}", 0.001)
            b.check(t, f"{c['month']}: difference % (G{r})", round(c["pct"], 9), f"='Ex 7.5'!G{r}", 1e-9, PCT)
    b.check(t, "months flagged (K21)", len(flagged), "='Ex 7.5'!K21", 0, COUNT)
    for i, c in enumerate(cur):
        if c in flagged:
            r = 28 + i
            b.check(t, f"{c['month']}: accrual rate (M{r})", round(mix[c["month"]]["rate"], 12), f"='Ex 7.5'!M{r}", 1e-12,
                    "0.000%")
            b.check(t, f"{c['month']}: {low} share of the commission base (N{r})", round(mix[c["month"]]["low"], 12),
                    f"='Ex 7.5'!N{r}", 1e-12, PCT)
    b.check(t, f"lowest commission rate, {low} (Q4)", e["rates"][0][1], "=INDEX('Ex 7.5'!Q4#,1)", 1e-12, PCT)
    b.check(t, "customer segments in the accruals (P4#)", len(e["rates"]), "=ROWS('Ex 7.5'!P4#)", 0, COUNT)
    b.check(t, "largest difference among the other months (K22)", round(max(abs(c["pct"]) for c in others), 9),
            "='Ex 7.5'!K22", 1e-9, PCT)
    b.check(t, f"accruals dated in {d.C} (K25)", round(e["accruals"], 2), "='Ex 7.5'!K25", 0.01)
    b.check(t, "SalesCommissionAccrual postings (K26)", round(e["by_type"].get("SalesCommissionAccrual", 0), 2),
            "='Ex 7.5'!K26", 0.01)
    b.check(t, "SalesCommissionAdjustment postings (K27)", round(adj, 2), "='Ex 7.5'!K27", 0.01)
    b.check(t, "SalesCommissionAdjustment rows (K28)", e["adj_rows"], "='Ex 7.5'!K28", 0, COUNT)
    b.check(t, f"GL 6290, {d.C} (K29)", round(sum(e["by_type"].values()), 2), "='Ex 7.5'!K29", 0.01)
    b.check(t, "unexplained difference (K31)", 0, "='Ex 7.5'!K31", 0.005)


# --- Exercise 7.6 ---------------------------------------------------------------------------------------------------

def ex7_6_expected(d: Data) -> dict:
    forecast = {(g, int(y)): v for g, y, v in d.q(
        "SELECT i.ItemGroup, substr(f.ForecastWeekStartDate, 1, 4), SUM(f.ForecastQuantity) FROM DemandForecast f "
        "JOIN Item i USING (ItemID) WHERE f.IsCurrent = 1 GROUP BY 1, 2")}
    orders = {(g, int(y)): v for g, y, v in d.q(
        "SELECT i.ItemGroup, substr(o.OrderDate, 1, 4), SUM(l.Quantity) FROM SalesOrderLine l "
        "JOIN SalesOrder o USING (SalesOrderID) JOIN Item i USING (ItemID) GROUP BY 1, 2")}
    budget = dict(d.q("SELECT i.ItemGroup, SUM(b.Quantity) FROM BudgetLine b JOIN Item i USING (ItemID) "
                      "WHERE b.FiscalYear = ? AND b.BudgetCategory = 'Revenue' GROUP BY 1", d.C))
    invoiced = dict(d.q("SELECT i.ItemGroup, SUM(l.Quantity) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                        "USING (SalesInvoiceID) JOIN Item i USING (ItemID) WHERE substr(si.InvoiceDate, 1, 4) = ? "
                        "GROUP BY 1", str(d.C)))
    rows = d.q("SELECT DemandForecastID, ForecastWeekStartDate, ItemID, WarehouseID, ForecastMethod, "
               "BaselineForecastQuantity, ForecastQuantity, PlannerEmployeeID, ApprovedByEmployeeID, IsCurrent "
               "FROM DemandForecast ORDER BY 1")
    current = [r for r in rows if r[9] == 1]
    adjusted = [r for r in current if abs(r[6] / r[5] - 1) > 0.5]
    others = [r[6] / r[5] for r in current if abs(r[6] / r[5] - 1) <= 0.5]
    emp = {r[0]: (r[1], r[2]) for r in d.q("SELECT EmployeeID, EmployeeName, JobTitle FROM Employee")}
    items = {r[0]: (r[1], r[2], r[3]) for r in d.q("SELECT ItemID, ItemCode, ItemGroup, ItemName FROM Item")}
    planner = adjusted[0][7] if adjusted else None
    return dict(forecast=forecast, orders=orders, budget=budget, invoiced=invoiced, rows=len(rows), current=len(current),
                adjusted=adjusted, low=min(others), high=max(others), emp=emp, items=items,
                unapproved=sum(1 for r in current if r[8] is None),
                planned=sum(1 for r in current if r[7] == planner) if planner else 0,
                pos=d.one("SELECT COUNT(*) FROM PurchaseOrder WHERE CreatedByEmployeeID = ?", planner) if planner else 0,
                warehouse=dict(d.q("SELECT WarehouseID, WarehouseName FROM Warehouse")),
                last_week=d.one("SELECT MAX(ForecastWeekStartDate) FROM DemandForecast"))


def ex7_6(b: ExerciseBuild) -> None:
    d = data(b)
    e = ex7_6_expected(d)
    ws = ex_sheet(b, "Ex 7.6")
    load(b, "DemandForecast", nav(b, 78, "DemandForecast", extra=[
        ("Filtered Rows", pq.select_rows("([IsCurrent] = 1)")),
        ("Merged Queries", pq.merge("Item", "ItemID", "ItemID", "Item")),
        ("Expanded Item", pq.expand("Item", ["ItemGroup"])),
        ("Added Custom", pq.add_custom("Ratio", "[ForecastQuantity] / [BaselineForecastQuantity]")),
        ("Changed Type1", pq.transform_types([("Ratio", "type number")]))]))
    load(b, "OrderLines", nav(b, 10, "SalesOrderLine", corrections={"Discount": "type number"}, extra=[
        ("Merged Queries", pq.merge("SalesOrder", "SalesOrderID", "SalesOrderID", "SalesOrder")),
        ("Expanded SalesOrder", pq.expand("SalesOrder", ["OrderDate"])),
        ("Merged Queries1", pq.merge("Item", "ItemID", "ItemID", "Item")),
        ("Expanded Item", pq.expand("Item", ["ItemGroup"]))]))
    load(b, "Employee", nav(b, 74, "Employee", extra=[
        ("Removed Other Columns", pq.select_columns(["EmployeeID", "EmployeeName", "JobTitle"]))]))

    years = d.years
    ycols = "BCD"
    values(ws, {"A1": "Exercise 7.6: management's demand forecast against orders, the budget, and its own baseline",
                "A3": "Forecast units (DemandForecast, IsCurrent = 1) by item group and year of ForecastWeekStartDate",
                "A4": "ItemGroup", "A12": "Units ordered (OrderLines) by item group and year of OrderDate",
                "A13": "ItemGroup", "A21": "Forecast / orders", "A22": "ItemGroup"})
    for c, y in zip(ycols, years):
        for r in (4, 13, 22):
            ws.Range(f"{c}{r}").Value = y
    for i, g in enumerate(GROUPS):
        for base in (5, 14, 23):
            ws.Cells(base + i, 1).Value = g
        for c in ycols:
            formulas(ws, {
                f"{c}{5 + i}": (f'=SUMIFS(DemandForecast[ForecastQuantity],DemandForecast[ItemGroup],$A{5 + i},'
                                f'DemandForecast[ForecastWeekStartDate],">="&DATE({c}$4,1,1),'
                                f'DemandForecast[ForecastWeekStartDate],"<"&DATE({c}$4+1,1,1))'),
                f"{c}{14 + i}": (f'=SUMIFS(OrderLines[Quantity],OrderLines[ItemGroup],$A{14 + i},OrderLines[OrderDate],'
                                 f'">="&DATE({c}$13,1,1),OrderLines[OrderDate],"<"&DATE({c}$13+1,1,1))'),
                f"{c}{23 + i}": f"={c}{5 + i}/{c}{14 + i}"})
    for r, lab in ((10, "Product groups (without Services)"), (19, "Product groups (without Services)"),
                   (28, "Product groups (without Services)")):
        ws.Cells(r, 1).Value = lab
    for c in ycols:
        formulas(ws, {f"{c}10": f"=SUM({c}5:{c}8)", f"{c}19": f"=SUM({c}14:{c}17)", f"{c}28": f"={c}10/{c}19"})
    # Requirement 4: the current year against the budget
    values(ws, {"A30": f"{d.C}: budget, forecast, orders, and invoiced units (requirement 4)", "A31": "ItemGroup",
                "B31": "Budget (BudgetLine)", "C31": "Forecast", "D31": "Orders", "E31": "Invoiced (InvoiceLines)",
                "F31": "Budget / orders", "G31": "Forecast / orders", "H31": "Budget / forecast", "A36": "Product groups"})
    for i, g in enumerate(PRODUCTS):
        r = 32 + i
        ws.Cells(r, 1).Value = g
        formulas(ws, {f"B{r}": f'=SUMIFS(BudgetLine[Quantity],BudgetLine[ItemGroup],$A{r},BudgetLine[BudgetCategory],"Revenue")',
                      f"C{r}": f"=D{5 + i}", f"D{r}": f"=D{14 + i}",
                      f"E{r}": f"=SUMIFS(InvoiceLines[Quantity],InvoiceLines[ItemGroup],$A{r},InvoiceLines[FiscalYear],$D$4)"})
    for c in "BCDE":
        ws.Range(f"{c}36").Formula = f"=SUM({c}32:{c}35)"
    for r in range(32, 37):
        formulas(ws, {f"F{r}": f"=B{r}/D{r}", f"G{r}": f"=C{r}/D{r}", f"H{r}": f"=B{r}/C{r}"})
    # Requirement 5: the forecasts adjusted by more than half of their baseline
    values(ws, {"A38": "Forecasts adjusted by more than half of their baseline (requirement 5)",
                "A39": "Forecasts (current version)", "A40": "Forecasts with no ApprovedByEmployeeID",
                "A41": "Lowest ratio among the other forecasts", "A42": "Highest ratio among the other forecasts"})
    formulas(ws, {"B39": "=ROWS(DemandForecast[DemandForecastID])",
                  "B40": "=COUNTBLANK(DemandForecast[ApprovedByEmployeeID])",
                  "B41": '=MINIFS(DemandForecast[Ratio],DemandForecast[Ratio],">=0.5",DemandForecast[Ratio],"<=1.5")',
                  "B42": '=MAXIFS(DemandForecast[Ratio],DemandForecast[Ratio],">=0.5",DemandForecast[Ratio],"<=1.5")'})
    heads = ["DemandForecastID", "ForecastWeekStartDate", "ItemCode", "ItemGroup", "WarehouseID", "ForecastMethod",
             "BaselineForecastQuantity", "ForecastQuantity", "Ratio", "PlannerEmployeeID", "Planner", "Planner's job title",
             "ApprovedByEmployeeID", "Approver"]
    for j, h in enumerate(heads):
        ws.Cells(45, 1 + j).Value = h
    look = lambda field: f"=XLOOKUP(A46#,DemandForecast[DemandForecastID],DemandForecast[{field}])"
    formulas(ws, {
        "A46": "=FILTER(DemandForecast[DemandForecastID],ABS(DemandForecast[Ratio]-1)>0.5)",
        "B46": look("ForecastWeekStartDate"),
        "C46": "=XLOOKUP(XLOOKUP(A46#,DemandForecast[DemandForecastID],DemandForecast[ItemID]),Item[ItemID],Item[ItemCode])",
        "D46": look("ItemGroup"), "E46": look("WarehouseID"), "F46": look("ForecastMethod"),
        "G46": look("BaselineForecastQuantity"), "H46": look("ForecastQuantity"), "I46": look("Ratio"),
        "J46": look("PlannerEmployeeID"),
        "K46": '=XLOOKUP(J46#,Employee[EmployeeID],Employee[EmployeeName],"(not found)")',
        "L46": '=XLOOKUP(J46#,Employee[EmployeeID],Employee[JobTitle],"")',
        "M46": ("=LET(a,XLOOKUP(A46#,DemandForecast[DemandForecastID],DemandForecast[ApprovedByEmployeeID]),"
                'IF(a=0,"",a))'),
        "N46": '=IF(M46#="","(none)",XLOOKUP(M46#,Employee[EmployeeID],Employee[EmployeeName],"(not found)"))'})
    planner = e["adjusted"][0][7] if e["adjusted"] else 0
    values(ws, {"A43": f"Forecasts planned by employee {planner} (the planner of the adjusted forecasts)"})
    ws.Range("B43").Formula = f"=COUNTIFS(DemandForecast[PlannerEmployeeID],{planner})"
    ws.Range("B5:D10").NumberFormat = MONEY
    ws.Range("B14:D19").NumberFormat = MONEY
    ws.Range("B23:D28").NumberFormat = "0.00"
    ws.Range("B32:E36").NumberFormat = MONEY
    ws.Range("F32:H36").NumberFormat = "0.00"
    ws.Range("B39:B40").NumberFormat = COUNT
    ws.Range("B41:B42").NumberFormat = RATIO
    ws.Range("B43").NumberFormat = COUNT
    ws.Range("B46:B60").NumberFormat = "yyyy-mm-dd"
    ws.Range("G46:H60").NumberFormat = "0.00"
    ws.Range("I46:I60").NumberFormat = RATIO
    for addr in ("A3", "A4:D4", "A12", "A13:D13", "A21", "A22:D22", "A30", "A31:H31", "A38", "A45:N45"):
        bold(ws, addr)
    ws.Columns("A").ColumnWidth = 40
    ws.Columns("B:N").ColumnWidth = 16

    f, o = e["forecast"], e["orders"]
    ratio = {(g, y): f[(g, y)] / o[(g, y)] for g in GROUPS for y in years}
    total = {y: sum(f[(g, y)] for g in PRODUCTS) / sum(o[(g, y)] for g in PRODUCTS) for y in years}
    by_year = {y: [ratio[(g, y)] for g in PRODUCTS] for y in years}
    grows = all(total[a] < total[c] for a, c in zip(years, years[1:]))
    budget26 = sum(e["budget"].get(g, 0) for g in PRODUCTS)
    fc26 = sum(f[(g, d.C)] for g in PRODUCTS)
    or26 = sum(o[(g, d.C)] for g in PRODUCTS)
    inv26 = sum(e["invoiced"].get(g, 0) for g in PRODUCTS)
    adj = e["adjusted"]
    a0 = adj[0] if adj else None
    code, group, name = e["items"][a0[2]] if adj else ("", "", "")
    pname, ptitle = e["emp"][a0[7]] if adj else ("", "")
    multiples = sorted({round(r[6] / r[5], 1) for r in adj})
    svc = [ratio[("Services", y)] for y in years]
    paras = [
        f"Requirement 3: forecast units were {total[d.F]:.2f}, {total[d.P]:.2f}, and {total[d.C]:.2f} times the units "
        f"ordered in {d.F}, {d.P}, and {d.C}" + (", rising every year" if grows else "") + ". The four product groups move "
        "together: their ratios range from "
        + ", ".join(f"{min(by_year[y]):.2f} to {max(by_year[y]):.2f} in {y}" for y in years)
        + ", so the bias is systematic, not a problem of one group. Services is the exception: its forecast is only "
        f"{min(svc):.2f} to {max(svc):.2f} of the hours ordered, a sign that design services are not really forecast "
        "with the same method.",
        f"Requirement 4: the {d.C} budget planned {budget26:,.0f} product units, more still than the forecast "
        f"({fc26:,.0f}) and {budget26 / or26:.1f} times the {or26:,.0f} units ordered ({inv26:,.0f} invoiced).",
        "Memo (requirement 6). To: the audit senior. Subject: management's demand forecast.",
        "The forecast is not consistent with Charles River's historical experience. In every product group and every year "
        f"it ran at more than twice the units customers ordered ({min(min(v) for v in by_year.values()):.2f} to "
        f"{max(max(v) for v in by_year.values()):.2f} times), and the bias grew each year, to {total[d.C]:.2f} in {d.C}. "
        "Any plan or estimate that relies on it is overstated: purchasing and production plans would buy and build far "
        "more than customers order, building inventory that may need an excess and obsolescence reserve; estimates of "
        "inventory recoverability or capacity needs based on it would be too high; and the budget, whose volume is "
        "higher still, cannot be used to evaluate performance, as Tutorial 7.2 found.",
        f"The review of planners' changes: every forecast is within about 10 percent of its baseline (ratios "
        f"{e['low']:.2f} to {e['high']:.2f}) except {words(len(adj))}: DemandForecastID "
        + series(str(r[0]) for r in adj)
        + f", the first forecast week of each year for {code} ({name}, {group}) at warehouse {a0[3]}, "
        f"{e['warehouse'].get(a0[3], '')}, each {multiples[0]:.1f} times its baseline, entered as {a0[4]} by {pname} "
        f"(employee {a0[7]}), a {ptitle}, with no approver. The list tests the approval of planners' adjustments. These "
        f"are the only unapproved forecasts in the Table ({words(e['unapproved'])} in all), so the control operated for every "
        "other adjustment but not for these. The quantities are small, but an unapproved override by a buyer who plans "
        f"most forecasts ({e['planned']:,} of {e['current']:,}) and also creates purchase orders ({e['pos']:,} of them) "
        "is a segregation-of-duties exception worth reporting.",
        "Evidence and explanations to request: the forecasting method and its inputs, and why it runs above orders; "
        "management's own comparisons of forecast with actual orders; the reasons for the three overrides and who should "
        "have approved them; how the forecast feeds purchasing, production, and the budget; and inventory levels and "
        "aging, to judge whether a reserve is needed.",
    ]
    model_answer(ws, 50 + max(len(adj), 3), paras, last_col="H")

    t = "7.6"
    b.check(t, "DemandForecast rows, all IsCurrent 1 (B39)", e["current"], "='Ex 7.6'!B39", 0, COUNT)
    b.check(t, "rows of the T78_DemandForecast Table", e["rows"], "='Ex 7.6'!B39", 0, COUNT)
    for j, y in enumerate(years):
        c = ycols[j]
        b.check(t, f"product-group forecast / orders, {y} ({c}28)", round(total[y], 9), f"='Ex 7.6'!{c}28", 1e-9, RATIO)
        for i, g in enumerate(PRODUCTS):
            b.check(t, f"{g} forecast / orders, {y} ({c}{23 + i})", round(ratio[(g, y)], 9), f"='Ex 7.6'!{c}{23 + i}", 1e-9,
                    RATIO)
    b.check(t, f"Services forecast / orders, {d.C} (D27)", round(ratio[("Services", d.C)], 9), "='Ex 7.6'!D27", 1e-9, RATIO)
    b.check(t, f"product-group forecast, {d.C} (C36)", round(fc26, 2), "='Ex 7.6'!C36", 0.01)
    b.check(t, f"product-group orders, {d.C} (D36)", round(or26, 2), "='Ex 7.6'!D36", 0.01)
    b.check(t, f"budget units, {d.C} (B36)", round(budget26, 2), "='Ex 7.6'!B36", 0.01)
    b.check(t, f"invoiced product units, {d.C} (E36)", round(inv26, 2), "='Ex 7.6'!E36", 0.01)
    b.check(t, "forecasts adjusted by more than half (A46#)", len(adj), "=ROWS('Ex 7.6'!A46#)", 0, COUNT)
    b.check(t, "their DemandForecastIDs", ", ".join(str(r[0]) for r in adj), "=TEXTJOIN(\", \",TRUE,'Ex 7.6'!A46#)", 0, "@")
    b.check(t, "their item", code, "=INDEX('Ex 7.6'!C46#,1)", 0, "@")
    b.check(t, "the first one's ratio to its baseline (I46)", round(a0[6] / a0[5], 9), "=INDEX('Ex 7.6'!I46#,1)", 1e-9,
            RATIO)
    b.check(t, "their planner", pname, "=INDEX('Ex 7.6'!K46#,1)", 0, "@")
    b.check(t, "the planner's job title", ptitle, "=INDEX('Ex 7.6'!L46#,1)", 0, "@")
    b.check(t, "adjusted forecasts with no approver", sum(1 for r in adj if r[8] is None),
            "=COUNTIF('Ex 7.6'!N46#,\"(none)\")", 0, COUNT)
    b.check(t, "forecasts with no approver in the Table (B40)", e["unapproved"], "='Ex 7.6'!B40", 0, COUNT)
    b.check(t, "lowest ratio among the other forecasts (B41)", round(e["low"], 9), "='Ex 7.6'!B41", 1e-9, RATIO)
    b.check(t, "highest ratio among the other forecasts (B42)", round(e["high"], 9), "='Ex 7.6'!B42", 1e-9, RATIO)
    b.check(t, f"forecasts planned by employee {planner} (B43)", e["planned"], "='Ex 7.6'!B43", 0, COUNT)


EXERCISES = [("7.1", ex7_1), ("7.2", ex7_2), ("7.3", ex7_3), ("7.4", ex7_4), ("7.5", ex7_5), ("7.6", ex7_6)]
