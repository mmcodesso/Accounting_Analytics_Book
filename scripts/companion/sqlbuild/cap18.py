"""MakeBuy.sql: the SQL part of the solution to the Chapter 18 capstone case ("Make, Buy, or Reprice"), instructor files.

The case splits the work by tool (tbl-18-03): MakeBuy.sql returns the family results, the inputs to 1090, the
activities, and the capacity, and hands them to Excel by Copy with Headers. The Excel part of the solution
(xlbuild/cap18.py, Make Buy Reprice.xlsx) pastes the results of the queries it keeps in QUERIES; this script holds those
queries, in the book's style and with the fiscal window's dates written in (DB Browser binds no parameters), in the order
the requirements ask for them, and adds the ones the chapter asks of MakeBuy.sql that the workbook computes by formula
(the variance per unit completed and the margins, the activities per thousand units, the capacity by work center, the
hours that buying would free, and the stock on hand at each year-end). Two views, FamilyResults and FamilyActivity (made
in the capstone's working copy, as Chapter 11 made MonthlyLaborEfficiency), let the later queries read those results
without repeating them.

Every query the workbook pastes carries a check that its result equals, cell for cell (to the cent), what the
workbook's own query returns, run as xlbuild/cap18.py runs it (its QUERIES and query_text are read from that module's
source, because the module imports Excel's COM helpers, which the SQL build's Python need not have). The other checks
take their expected values from the notes' model (facts/notes/ch18.py, the values of the generated instructor notes) or
from read-only SQL of this module.
"""

from __future__ import annotations

import ast
from pathlib import Path

from sqlbuild.script import Check

FILE = "MakeBuy.sql"
DATABASE = "CharlesRiver_Capstone.sqlite (a copy of CharlesRiver.sqlite)"
PRACTICAL = 0.80                 # tbl-18-02: practical capacity, a share of the calendar's available hours
MATERIALITY = 0.05               # tbl-18-02: of income before income taxes as recorded
CLOSES = """\
    AND gl.VoucherNumber NOT IN (
        SELECT EntryNumber
        FROM JournalEntry
        WHERE EntryType LIKE 'Year-End Close%')"""


def notes(b):
    b.data                                       # puts facts/ on sys.path
    from notes import ch18
    return ch18


def model(b) -> dict:
    return notes(b).model(b.data)


def context(b, name: str) -> dict:
    return getattr(notes(b), name)(b.data, lambda *a, **k: None)


def script(b):
    d = b.data
    return b.script(FILE, f"make, buy, or reprice: what the records show for fiscal {d.C}",
                    f"family variances against account 5080; inputs to 1090 against the ledger and the standard cost "
                    f"released; routing time against the standard hours completed; each result the workbook pastes "
                    f"against the workbook's own query", database=DATABASE)


def window(b) -> tuple[str, str]:
    d = b.data
    return f"'{d.C}-01-01'", f"'{d.C}-12-31'"


def money(x: float) -> str:
    return f"{x:,.2f}"


def one(x: float) -> str:
    """A number to one place, rounded half up as SQLite and Excel show it."""
    from decimal import ROUND_HALF_UP, Decimal
    return f"{Decimal(repr(x)).quantize(Decimal('0.1'), ROUND_HALF_UP):,}"


def pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


# --- the workbook's queries, as xlbuild/cap18.py runs them -------------------------------------------------------

class _WorkbookData:
    """The attributes xlbuild/cap18.py's Data gives its queries (the fiscal window and the read-only connection)."""

    def __init__(self, d):
        self.con, self.q, self.closes, self.years = d.con, d.q, d.closes, d.years
        self.F, self.P, self.C, self.N = d.F, d.P, d.C, d.N
        self.first, self.last = f"{d.C}-01-01", f"{d.C}-12-31"


def workbook(b):
    """xlbuild/cap18.py's run_query, with its QUERIES and query_text, read from the module's source."""
    if not hasattr(b, "_cap18_workbook"):
        src = Path(__file__).resolve().parents[1] / "xlbuild" / "cap18.py"
        ns: dict = {"Data": object}
        for node in ast.parse(src.read_text(encoding="utf-8")).body:
            target = getattr(node, "target", None)
            if (isinstance(node, ast.AnnAssign) and getattr(target, "id", "") == "QUERIES") or \
                    (isinstance(node, ast.FunctionDef) and node.name in ("wc_short", "query_text", "run_query")):
                exec(compile(ast.Module([node], []), str(src), "exec"), ns)
        data = _WorkbookData(b.data)
        b._cap18_workbook = lambda key, **extra: ns["run_query"](data, key, **extra)
    return b._cap18_workbook


def equal_cells(x, y) -> bool:
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
        return abs(float(x) - float(y)) <= 0.0051 + 1e-12 * max(abs(x), abs(y))
    return x == y


def same_as_workbook(b, key: str, **extra) -> Check:
    """The query's result equals the workbook's pasted result: the same columns, the same rows in the same order, and
    every value equal to the cent (the script rounds what the workbook pastes unrounded)."""
    cols, rows = workbook(b)(key, **extra)
    expected = f"{len(rows)} row{'' if len(rows) == 1 else 's'} of {len(cols)} columns, equal"

    def compare(r):
        if r.columns != cols:
            return f"columns {r.columns}"
        if len(r.rows) != len(rows):
            return f"{len(r.rows)} rows"
        for k, (got, want) in enumerate(zip(r.rows, rows)):
            for c, x, y in zip(cols, got, want):
                if not equal_cells(x, y):
                    return f"row {k + 1} {c}: {x} against {y}"
        return expected
    return Check(f"the workbook's pasted result ({key})", expected, compare)


def wc_short(name: str) -> str:
    base = name.removesuffix(" Work Center").split(" and ")[0]
    words = base.split()
    return base if len(words) == 1 else "".join(w[0] for w in words)


def centers(b) -> list[tuple[int, str]]:
    return [(w, wc_short(n)) for w, n in b.data.q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter "
                                                   "ORDER BY WorkCenterID")]


def remember(b, key: str, q) -> None:
    if not hasattr(b, "_cap18_queries"):
        b._cap18_queries = {}
    b._cap18_queries[key] = q


def recall(b, key: str):
    return b._cap18_queries[key]


# --- Requirement 1 -----------------------------------------------------------------------------------------------

def r1(b):
    d, m = b.data, model(b)
    v = context(b, "r1")
    first, last = window(b)
    s = script(b)
    s.query("Requirement 1, Q1: the dates through which the base year's records run",
            f"Population: invoices, completions, closes, and time records of {d.C}; expected: time records end first",
            f"""\
SELECT
    (SELECT MAX(InvoiceDate)
     FROM SalesInvoice
     WHERE InvoiceDate <= {last}) AS LastInvoice,
    (SELECT MAX(CompletionDate)
     FROM ProductionCompletion
     WHERE CompletionDate <= {last}) AS LastCompletion,
    (SELECT MAX(CloseDate)
     FROM WorkOrderClose
     WHERE CloseDate <= {last}) AS LastClose,
    (SELECT MAX(WorkDate)
     FROM LaborTimeEntry
     WHERE WorkDate <= {last}) AS LastTimeRecord;""",
            [same_as_workbook(b, "dates"),
             Check("last invoice", d.one("SELECT MAX(InvoiceDate) FROM SalesInvoice WHERE InvoiceDate <= ?",
                                         f"{d.C}-12-31"), lambda r: r.value("LastInvoice")),
             Check("last time record", d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry WHERE WorkDate <= ?",
                                             f"{d.C}-12-31"), lambda r: r.value("LastTimeRecord"))])
    s.query("Requirement 1, Q2: the family results of the base year, kept as the view FamilyResults",
            "Population: finished goods by family (ItemCode's first seven characters); expected: each family sold",
            f"""\
DROP VIEW IF EXISTS FamilyResults;
CREATE VIEW FamilyResults AS
WITH FinishedGoods AS (
    SELECT ItemID, SUBSTR(ItemCode, 1, 7) AS Family, ItemGroup,
        SupplyMode, StandardCost
    FROM Item
    WHERE ItemType = 'Finished Good'
),
Sold AS (
    SELECT fg.Family, fg.SupplyMode, SUM(sil.Quantity) AS Units,
        SUM(sil.LineTotal) AS Revenue,
        SUM(sil.Quantity * sil.BaseListPrice) AS ListValue,
        SUM(sil.Quantity * fg.StandardCost) AS StandardCost
    FROM SalesInvoiceLine AS sil
        INNER JOIN SalesInvoice AS si
            ON si.SalesInvoiceID = sil.SalesInvoiceID
        INNER JOIN FinishedGoods AS fg ON fg.ItemID = sil.ItemID
    WHERE si.InvoiceDate BETWEEN {first} AND {last}
    GROUP BY fg.Family, fg.SupplyMode
),
Closes AS (
    SELECT fg.Family, COUNT(*) AS Closes,
        SUM(woc.MaterialVarianceAmount) AS MaterialVariance,
        SUM(woc.DirectLaborVarianceAmount) AS LaborVariance,
        SUM(woc.OverheadVarianceAmount) AS OverheadVariance,
        SUM(woc.TotalVarianceAmount) AS TotalVariance
    FROM WorkOrderClose AS woc
        INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = woc.WorkOrderID
        INNER JOIN FinishedGoods AS fg ON fg.ItemID = wo.ItemID
    WHERE woc.CloseDate BETWEEN {first} AND {last}
    GROUP BY fg.Family
),
Made AS (
    SELECT fg.Family, SUM(pcl.QuantityCompleted) AS UnitsCompleted,
        SUM(pcl.QuantityCompleted * fg.StandardCost)
            AS StandardCostCompleted,
        SUM(pcl.ExtendedStandardMaterialCost)
            AS StandardMaterialCompleted
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        INNER JOIN FinishedGoods AS fg ON fg.ItemID = pcl.ItemID
    WHERE pc.CompletionDate BETWEEN {first} AND {last}
    GROUP BY fg.Family
)
SELECT s.Family,
    (SELECT MIN(fg.ItemGroup)
     FROM FinishedGoods AS fg
     WHERE fg.Family = s.Family) AS ItemGroup,
    ROUND(s.Units, 2) AS Units, ROUND(s.Revenue, 2) AS Revenue,
    ROUND(s.ListValue, 2) AS ListValue,
    ROUND(s.StandardCost, 2) AS StandardCost, c.Closes,
    ROUND(c.MaterialVariance, 2) AS MaterialVariance,
    ROUND(c.LaborVariance, 2) AS LaborVariance,
    ROUND(c.OverheadVariance, 2) AS OverheadVariance,
    ROUND(c.TotalVariance, 2) AS TotalVariance,
    ROUND(m.UnitsCompleted, 2) AS UnitsCompleted,
    ROUND(m.StandardCostCompleted, 2) AS StandardCostCompleted,
    ROUND(m.StandardMaterialCompleted, 2) AS StandardMaterialCompleted,
    ROUND(p.Revenue, 2) AS PurchasedRevenue,
    ROUND(p.StandardCost, 2) AS PurchasedStandardCost
FROM Sold AS s
    LEFT JOIN Closes AS c ON c.Family = s.Family
    LEFT JOIN Made AS m ON m.Family = s.Family
    LEFT JOIN Sold AS p
        ON p.Family = s.Family AND p.SupplyMode = 'Purchased'
WHERE s.SupplyMode = 'Manufactured';""")
    fams = [f for f in sorted(m["fam"])]
    checks = [same_as_workbook(b, "family"),
              Check("families sold", fams, lambda r: r.col("Family")),
              Check("the families' variance", round(m["totals"]["total"], 2), lambda r: r.total("TotalVariance")),
              Check("material variance", round(m["totals"]["material"], 2), lambda r: r.total("MaterialVariance")),
              Check("labor variance", round(m["totals"]["labor"], 2), lambda r: r.total("LaborVariance")),
              Check("overhead variance", round(m["totals"]["overhead"], 2), lambda r: r.total("OverheadVariance"))]
    for f in fams:
        x = m["fam"][f]
        checks += [Check(f"{f} units sold", round(x["units"], 2), lambda r, f=f: r.where(Family=f)["Units"]),
                   Check(f"{f} revenue", round(x["rev"], 2), lambda r, f=f: r.where(Family=f)["Revenue"]),
                   Check(f"{f} closes", x["closes"], lambda r, f=f: r.where(Family=f)["Closes"]),
                   Check(f"{f} variance", round(x["variance"], 2), lambda r, f=f: r.where(Family=f)["TotalVariance"])]
    for name in v["unsold"]:
        checks.append(Check(f"{name} not sold in {d.C}", False, lambda r, n=name: n in r.col("Family")))
    s.query("Requirement 1, Q3: the family results, as the workbook pastes them (Copy with Headers)",
            "Population: the view FamilyResults; expected: sales, the closes' variance by part, and completions",
            """\
SELECT *
FROM FamilyResults
ORDER BY Family;""", checks)
    checks = []
    for f in fams:
        x = m["fam"][f]
        checks += [Check(f"{f} variance as a share of standard completed", round(x["share"], 4),
                         lambda r, f=f: r.where(Family=f)["ShareOfStandardCompleted"], 0.00006),
                   Check(f"{f} variance per unit completed", round(x["vpu"], 2),
                         lambda r, f=f: r.where(Family=f)["VariancePerUnit"]),
                   Check(f"{f} margin at standard", round(x["m_std"], 4),
                         lambda r, f=f: r.where(Family=f)["MarginAtStandard"], 0.00006),
                   Check(f"{f} margin after the variance per unit", round(x["m_unit"], 4),
                         lambda r, f=f: r.where(Family=f)["MarginAfterPerUnit"], 0.00006),
                   Check(f"{f} margin with the year's variance", round(x["m_year"], 4),
                         lambda r, f=f: r.where(Family=f)["MarginWithYearVariance"], 0.00006),
                   Check(f"{f} purchased margin at standard",
                         None if x["m_purch"] is None else round(x["m_purch"], 4),
                         lambda r, f=f: r.where(Family=f)["PurchasedMarginAtStandard"], 0.00006)]
    checks.append(Check("families whose purchased margin is below their margin after the variance per unit",
                        v["beats"], lambda r: [f for f, a, p in zip(r.col("Family"), r.col("MarginAfterPerUnit"),
                                                                     r.col("PurchasedMarginAtStandard"))
                                               if p is not None and a > p]))
    s.query("Requirement 1, Q4: each family's variance per unit completed and three margins, purchased beside",
            "Population: the view FamilyResults; expected: the variance lowers every margin, few beat purchased",
            """\
SELECT Family, ItemGroup,
    ROUND(TotalVariance / StandardCostCompleted, 4)
        AS ShareOfStandardCompleted,
    ROUND(TotalVariance / UnitsCompleted, 2) AS VariancePerUnit,
    ROUND(1 - StandardCost / Revenue, 4) AS MarginAtStandard,
    ROUND(1 - (StandardCost + TotalVariance / UnitsCompleted * Units)
        / Revenue, 4) AS MarginAfterPerUnit,
    ROUND(1 - (StandardCost + TotalVariance) / Revenue, 4)
        AS MarginWithYearVariance,
    ROUND(1 - PurchasedStandardCost / PurchasedRevenue, 4)
        AS PurchasedMarginAtStandard
FROM FamilyResults
ORDER BY Family;""", checks)
    checks = []
    for g in m["groups"]:
        n = g["name"]
        checks += [Check(f"{n} revenue", round(g["rev"], 2), lambda r, n=n: r.where(ItemGroup=n)["Revenue"]),
                   Check(f"{n} variance", round(g["variance"], 2), lambda r, n=n: r.where(ItemGroup=n)["Variance"]),
                   Check(f"{n} margin at standard", round(g["m_std"], 4),
                         lambda r, n=n: r.where(ItemGroup=n)["MarginAtStandard"], 0.00006),
                   Check(f"{n} margin after the variance per unit", round(g["m_unit"], 4),
                         lambda r, n=n: r.where(ItemGroup=n)["MarginAfterPerUnit"], 0.00006),
                   Check(f"{n} margin with the year's variance", round(g["m_year"], 4),
                         lambda r, n=n: r.where(ItemGroup=n)["MarginWithYearVariance"], 0.00006)]
    q = s.query("Requirement 1, Q5: the three margins by item group (the CFO's comparison)",
                "Population: the view FamilyResults; expected: about ten points from standard to the year's variance",
                """\
SELECT ItemGroup, ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(SUM(TotalVariance), 2) AS Variance,
    ROUND(1 - SUM(StandardCost) / SUM(Revenue), 4) AS MarginAtStandard,
    ROUND(1 - SUM(StandardCost + TotalVariance / UnitsCompleted * Units)
        / SUM(Revenue), 4) AS MarginAfterPerUnit,
    ROUND(1 - SUM(StandardCost + TotalVariance) / SUM(Revenue), 4)
        AS MarginWithYearVariance
FROM FamilyResults
GROUP BY ItemGroup
ORDER BY ItemGroup;""", checks)
    remember(b, "groups", q)
    s.query("Requirement 1, Q6: account 5080 Manufacturing Variance in the base year, the closes left out",
            f"Population: the ledger's 5080 postings of fiscal {d.C}; expected: the closes' variance",
            f"""\
SELECT ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Variance5080
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE a.AccountNumber = 5080 AND gl.FiscalYear = {d.C}
{CLOSES};""",
            [same_as_workbook(b, "ledger5080"),
             Check("5080", round(notes(b).ledger_5080(d), 2), lambda r: r.value())])
    q = s.query("Requirement 1, Q7: the families' variances reconciled to account 5080",
                "Population: the view FamilyResults and the 5080 postings; expected: no difference",
                f"""\
SELECT
    (SELECT ROUND(SUM(TotalVariance), 2)
     FROM FamilyResults) AS FamilyVariance,
    (SELECT ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2)
     FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
     WHERE a.AccountNumber = 5080 AND gl.FiscalYear = {d.C}
    {CLOSES.replace(chr(10), chr(10) + '    ')}) AS Variance5080;""",
                [Check("family variances", round(m["totals"]["total"], 2), lambda r: r.value("FamilyVariance")),
                 Check("5080", round(notes(b).ledger_5080(d), 2), lambda r: r.value("Variance5080")),
                 Check("difference", 0.0, lambda r: round(r.value("FamilyVariance") - r.value("Variance5080"), 2))])
    remember(b, "5080", q)
    ratio = {x["short"]: x["ratio"] for x in v["purchased"]}
    s.query("Requirement 1, Q8: the base year's purchase orders for purchased finished goods, by family",
            f"Population: {d.C} order lines for purchased finished goods; expected: near standard, half of list",
            f"""\
SELECT SUBSTR(i.ItemCode, 1, 7) AS Family,
    ROUND(SUM(pol.Quantity * pol.UnitCost), 2) AS OrderCost,
    ROUND(SUM(pol.Quantity * i.ListPrice), 2) AS ListValue,
    ROUND(SUM(pol.Quantity * i.StandardCost), 2) AS StandardValue,
    ROUND(MIN(pol.UnitCost / i.StandardCost), 4)
        AS LowestCostToStandard,
    ROUND(MAX(pol.UnitCost / i.StandardCost), 4)
        AS HighestCostToStandard
FROM PurchaseOrderLine AS pol
    INNER JOIN PurchaseOrder AS po
        ON po.PurchaseOrderID = pol.PurchaseOrderID
    INNER JOIN Item AS i ON i.ItemID = pol.ItemID
WHERE i.SupplyMode = 'Purchased' AND i.ItemType = 'Finished Good'
    AND po.OrderDate BETWEEN {first} AND {last}
GROUP BY Family
ORDER BY Family;""",
            [same_as_workbook(b, "purchased"),
             Check("purchased cost over standard, all families", round(v["avg_ratio"], 3),
                   lambda r: round(r.total("OrderCost") / r.total("StandardValue"), 3), 0.0006),
             Check("lowest cost to standard", round(v["low_ratio"], 2),
                   lambda r: round(min(r.col("LowestCostToStandard")), 2)),
             Check("highest cost to standard", round(v["high_ratio"], 2),
                   lambda r: round(max(r.col("HighestCostToStandard")), 2))] +
            [Check(f"{k} purchased cost to list", round(x, 3),
                   lambda r, k=k: round(next(c / lv for f, c, lv in zip(r.col("Family"), r.col("OrderCost"),
                                                                      r.col("ListValue")) if f[4:] == k), 3), 0.0006)
             for k, x in ratio.items()])
    s.query("Requirement 1, Q9: the CFO's second premise: did list prices or standard costs ever change?",
            "Population: every invoice, shipment, and completion line; expected: no change beyond rounding",
            f"""\
SELECT
    (SELECT COUNT(*)
     FROM SalesInvoiceLine) AS InvoiceLines,
    (SELECT COUNT(*)
     FROM SalesInvoiceLine AS sil
        INNER JOIN Item AS i ON i.ItemID = sil.ItemID
     WHERE sil.BaseListPrice IS NULL OR i.ListPrice IS NULL
        OR ABS(sil.BaseListPrice - i.ListPrice) > 0.004)
        AS ListPriceDiffers,
    (SELECT COUNT(*)
     FROM ShipmentLine AS sl
        INNER JOIN Item AS i ON i.ItemID = sl.ItemID
     WHERE sl.ExtendedStandardCost IS NULL
        OR ABS(sl.ExtendedStandardCost
            - ROUND(sl.QuantityShipped * i.StandardCost, 2)) > 0.011)
        AS ShipmentCostDiffers,
    (SELECT ROUND(MAX(ABS(pcl.ExtendedStandardTotalCost
            - pcl.QuantityCompleted * i.StandardCost)), 4)
     FROM ProductionCompletionLine AS pcl
        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID)
        AS LargestCompletionDifference,
    (SELECT COUNT(*)
     FROM (SELECT sil.ItemID
           FROM SalesInvoiceLine AS sil
               INNER JOIN SalesInvoice AS si
                   ON si.SalesInvoiceID = sil.SalesInvoiceID
           WHERE si.InvoiceDate BETWEEN '{d.F}-01-01' AND {last}
           GROUP BY sil.ItemID
           HAVING COUNT(DISTINCT SUBSTR(si.InvoiceDate, 1, 4))
               = {len(d.years)})) AS ItemsSoldEveryYear;""",
            [same_as_workbook(b, "premises"),
             Check("invoice lines", v["lines"], lambda r: r.value("InvoiceLines")),
             Check("list prices that differ", 0, lambda r: r.value("ListPriceDiffers")),
             Check("shipment costs that differ", 0, lambda r: r.value("ShipmentCostDiffers")),
             Check("largest completion difference", round(v["max_diff"], 2),
                   lambda r: r.value("LargestCompletionDifference")),
             Check("items sold in every year", v["all_years"], lambda r: r.value("ItemsSoldEveryYear"))])
    g0 = notes(b).story(m)
    fam_rows = [m["fam"][f] for f in fams]
    s.answer("Requirement 1", f"""\
Queries Q2 to Q5 rebuild the CFO's comparison once, from the invoice lines, items, work orders, closes, and completions
of {d.C}, each joined at its own grain and aggregated by family before the families are joined (the joins cannot fan
out). The families' variances total {money(m['totals']['total'])} (material {money(m['totals']['material'])}, labor
{money(m['totals']['labor'])}, overhead {money(m['totals']['overhead'])}), equal to account 5080 without the closes (Q7).
{g0['name']} earns {pct(g0['m_std'])} at standard, {pct(g0['m_unit'])} after the variance per unit completed, and
{pct(g0['m_year'])} with the year's whole variance charged: the CFO's "about ten points" is the gap between the first
and the last. Only {', '.join(v['beats'])} keeps a margin after the variance per unit above that of the purchased
products of its family (Q4); the variance runs from {pct(min(x['share'] for x in fam_rows))} to
{pct(max(x['share'] for x in fam_rows))} of the standard cost completed.

The second premise holds as arithmetic (Q9): the base list price equals the item's list price on all {v['lines']:,}
invoice lines, every shipment line's standard cost is its quantity times the item's standard cost, completion lines
differ by at most {v['max_diff']:.2f} (component rounding), and {v['all_years']} items were sold in each of the
{v['n_years']} years, so neither list prices nor standards changed. It fails as a diagnosis: whether the products are
under-costed depends on what the variance is made of, which Requirement 2 takes apart.""")


# --- Requirement 2 -----------------------------------------------------------------------------------------------

def r2(b):
    d, m = b.data, model(b)
    v = context(b, "r2")
    first, last = window(b)
    s = script(b)
    pay = m["pay"]
    checks = [same_as_workbook(b, "payroll"),
              Check("payroll lines", len(pay), len),
              Check("payroll to 1090", round(v["payroll"], 2), lambda r: r.total("Amount"))]
    for (t, k), (h, a) in sorted(pay.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        label = f"{t}{', ' + k if k else ''}"
        checks.append(Check(f"{label} amount", round(a, 2),
                            lambda r, t=t, k=k: r.where(LineType=t, LaborType=k or "")["Amount"]))
        if h is not None:
            checks.append(Check(f"{label} hours", round(h, 2),
                                lambda r, t=t, k=k: r.where(LineType=t, LaborType=k or "")["Hours"]))
    s.query("Requirement 2, Q10: the inputs to 1090 from payroll, by line type and labor type",
            f"Population: Manufacturing payroll lines of {d.C}, deductions left out; expected: the PayrollSummary debits",
            f"""\
SELECT prl.LineType, COALESCE(lte.LaborType, '') AS LaborType,
    ROUND(SUM(prl.Hours), 2) AS Hours,
    ROUND(SUM(prl.Amount), 2) AS Amount
FROM PayrollRegisterLine AS prl
    INNER JOIN PayrollRegister AS pr
        ON pr.PayrollRegisterID = prl.PayrollRegisterID
    INNER JOIN PayrollPeriod AS pp
        ON pp.PayrollPeriodID = pr.PayrollPeriodID
    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
    LEFT JOIN LaborTimeEntry AS lte
        ON lte.LaborTimeEntryID = prl.LaborTimeEntryID
WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = {d.C}
    AND prl.LineType NOT IN ('Benefits Deduction',
        'Employee Tax Withholding')
GROUP BY prl.LineType, lte.LaborType
ORDER BY CASE prl.LineType
        WHEN 'Regular Earnings' THEN 1
        WHEN 'Overtime Earnings' THEN 2
        WHEN 'Salary Earnings' THEN 3
        WHEN 'Employer Payroll Tax' THEN 4
        ELSE 5 END,
    lte.LaborType;""", checks)
    q = s.query("Requirement 2, Q11: the debits to 1090 Manufacturing Cost Clearing by source",
                f"Population: 1090 debits of {d.C} but the closes'; expected: payroll, overhead entries, depreciation",
                f"""\
SELECT COALESCE(je.EntryType, gl.SourceDocumentType) AS Source,
    ROUND(SUM(gl.Debit), 2) AS Debits
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    LEFT JOIN JournalEntry AS je
        ON je.JournalEntryID = gl.SourceDocumentID
        AND gl.SourceDocumentType = 'JournalEntry'
WHERE a.AccountNumber = 1090
    AND gl.PostingDate BETWEEN {first} AND {last}
    AND gl.Debit > 0 AND gl.SourceDocumentType <> 'WorkOrderClose'
GROUP BY Source
ORDER BY Source;""",
                [same_as_workbook(b, "debits1090"),
                 Check("inputs to 1090", round(v["inputs"], 2), lambda r: r.total("Debits")),
                 Check("Factory Overhead entries", round(v["foh"], 2), lambda r: r.where(Source="Factory Overhead")["Debits"]),
                 Check("depreciation", round(v["dep"], 2), lambda r: r.where(Source="Depreciation")["Debits"]),
                 Check("payroll", round(v["payroll"], 2), lambda r: r.where(Source="PayrollSummary")["Debits"])])
    remember(b, "debits", q)
    q = s.query("Requirement 2, Q12: what the base year's completions released at standard, and 1090's credits",
                f"Population: the completion lines of {d.C}; expected: conversion equal to the credits within rounding",
                f"""\
SELECT ROUND(SUM(pcl.QuantityCompleted
        * i.StandardLaborHoursPerUnit), 2) AS StandardHours,
    ROUND(SUM(pcl.ExtendedStandardMaterialCost), 2) AS Material,
    ROUND(SUM(pcl.ExtendedStandardDirectLaborCost), 2) AS DirectLabor,
    ROUND(SUM(pcl.ExtendedStandardVariableOverheadCost), 2)
        AS VariableOverhead,
    ROUND(SUM(pcl.ExtendedStandardFixedOverheadCost), 2)
        AS FixedOverhead,
    ROUND(SUM(pcl.ExtendedStandardConversionCost), 2) AS Conversion,
    (SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2)
     FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
     WHERE a.AccountNumber = 1090 AND gl.FiscalYear = {d.C}
        AND gl.SourceDocumentType = 'ProductionCompletion')
        AS CreditsTo1090
FROM ProductionCompletionLine AS pcl
    INNER JOIN ProductionCompletion AS pc
        ON pc.ProductionCompletionID = pcl.ProductionCompletionID
    INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
WHERE pc.CompletionDate BETWEEN {first} AND {last};""",
                [same_as_workbook(b, "released"),
                 Check("standard hours", round(v["stdh"], 2), lambda r: r.value("StandardHours")),
                 Check("labor released", round(v["labor"], 2), lambda r: r.value("DirectLabor")),
                 Check("variable overhead released", round(v["var_oh"], 2), lambda r: r.value("VariableOverhead")),
                 Check("fixed overhead released", round(v["fixed_oh"], 2), lambda r: r.value("FixedOverhead")),
                 Check("conversion on the lines", round(v["conversion"], 2), lambda r: r.value("Conversion")),
                 Check("ProductionCompletion credits to 1090", round(v["released_gl"], 2),
                       lambda r: r.value("CreditsTo1090"))])
    remember(b, "released", q)
    s.query("Requirement 2, Q13: the inputs to 1090 and the standard cost released, per standard hour",
            "Population: the totals of Q10 to Q12; expected: actual cost well above standard, mostly overhead",
            f"""\
WITH Totals AS (
    SELECT
        (SELECT SUM(gl.Debit)
         FROM GLEntry AS gl
            INNER JOIN Account AS a ON a.AccountID = gl.AccountID
         WHERE a.AccountNumber = 1090
            AND gl.PostingDate BETWEEN {first} AND {last}
            AND gl.Debit > 0
            AND gl.SourceDocumentType <> 'WorkOrderClose') AS Inputs,
        (SELECT SUM(prl.Amount)
         FROM PayrollRegisterLine AS prl
            INNER JOIN PayrollRegister AS pr
                ON pr.PayrollRegisterID = prl.PayrollRegisterID
            INNER JOIN PayrollPeriod AS pp
                ON pp.PayrollPeriodID = pr.PayrollPeriodID
            INNER JOIN CostCenter AS cc
                ON cc.CostCenterID = pr.CostCenterID
            INNER JOIN LaborTimeEntry AS lte
                ON lte.LaborTimeEntryID = prl.LaborTimeEntryID
         WHERE cc.CostCenterName = 'Manufacturing'
            AND pp.FiscalYear = {d.C}
            AND lte.LaborType = 'Direct Manufacturing'
            AND prl.LineType IN ('Regular Earnings',
                'Overtime Earnings')) AS DirectEarnings,
        (SELECT SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit)
         FROM ProductionCompletionLine AS pcl
            INNER JOIN ProductionCompletion AS pc
                ON pc.ProductionCompletionID = pcl.ProductionCompletionID
            INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
         WHERE pc.CompletionDate BETWEEN {first} AND {last})
            AS StandardHours,
        (SELECT SUM(pcl.ExtendedStandardDirectLaborCost)
         FROM ProductionCompletionLine AS pcl
            INNER JOIN ProductionCompletion AS pc
                ON pc.ProductionCompletionID = pcl.ProductionCompletionID
         WHERE pc.CompletionDate BETWEEN {first} AND {last})
            AS LaborReleased,
        (SELECT SUM(pcl.ExtendedStandardVariableOverheadCost
                + pcl.ExtendedStandardFixedOverheadCost)
         FROM ProductionCompletionLine AS pcl
            INNER JOIN ProductionCompletion AS pc
                ON pc.ProductionCompletionID = pcl.ProductionCompletionID
         WHERE pc.CompletionDate BETWEEN {first} AND {last})
            AS OverheadReleased
)
SELECT ROUND(Inputs / StandardHours, 2) AS InputsPerStandardHour,
    ROUND((LaborReleased + OverheadReleased) / StandardHours, 2)
        AS ReleasedPerStandardHour,
    ROUND(LaborReleased / StandardHours, 2) AS LaborPerStandardHour,
    ROUND(OverheadReleased / StandardHours, 2)
        AS OverheadPerStandardHour,
    ROUND(DirectEarnings, 2) AS DirectEarnings,
    ROUND(Inputs - DirectEarnings, 2) AS ActualOverhead,
    ROUND((Inputs - DirectEarnings) / StandardHours, 2)
        AS ActualOverheadPerStandardHour,
    ROUND((Inputs - DirectEarnings) / OverheadReleased, 2)
        AS ActualToApplied,
    ROUND(OverheadReleased / (Inputs - DirectEarnings), 2)
        AS AppliedShareOfActual
FROM Totals;""",
            [Check("inputs per standard hour", round(v["actual_rate"], 2), lambda r: r.value("InputsPerStandardHour")),
             Check("released per standard hour", round(v["conv_rate"], 2),
                   lambda r: r.value("ReleasedPerStandardHour")),
             Check("labor released per standard hour", round(v["labor_rate"], 2),
                   lambda r: r.value("LaborPerStandardHour")),
             Check("overhead released per standard hour", round(v["oh_rate"], 2),
                   lambda r: r.value("OverheadPerStandardHour")),
             Check("direct earnings", round(v["direct"], 2), lambda r: r.value("DirectEarnings")),
             Check("actual overhead", round(v["actual_oh"], 2), lambda r: r.value("ActualOverhead")),
             Check("actual overhead per standard hour", round(v["actual_oh_rate"], 2),
                   lambda r: r.value("ActualOverheadPerStandardHour")),
             Check("actual overhead over applied", round(v["times"], 2), lambda r: r.value("ActualToApplied")),
             Check("applied over actual (the CFO's 'a third')", round(v["third"], 2),
                   lambda r: r.value("AppliedShareOfActual"))])
    months = m["with_start"]
    pay_dates = d.q("SELECT strftime('%Y-%m', PostingDate), COUNT(DISTINCT PostingDate) FROM GLEntry WHERE AccountID = ? "
                    "AND SourceDocumentType = 'PayrollSummary' AND FiscalYear BETWEEN ? AND ? GROUP BY 1",
                    d.account("1090"), d.F, d.C)
    three = sorted(mo for mo, n in pay_dates if n == 3)
    s.query("Requirement 2, Q14: each input to 1090 by month, with the standard hours completed",
            f"Population: completions and 1090 debits, {d.F}-01 to {d.C}-12; expected: some months with 3 pay dates",
            f"""\
WITH Made AS (
    SELECT strftime('%Y-%m', pc.CompletionDate) AS Month,
        SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit)
            AS StandardHours,
        SUM(pcl.ExtendedStandardVariableOverheadCost
            + pcl.ExtendedStandardFixedOverheadCost) AS AppliedOverhead
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
    GROUP BY Month
),
Posted AS (
    SELECT strftime('%Y-%m', gl.PostingDate) AS Month,
        SUM(CASE WHEN je.EntryType = 'Factory Overhead'
            THEN gl.Debit ELSE 0 END) AS FactoryOverhead,
        SUM(CASE WHEN gl.SourceDocumentType = 'PayrollSummary'
            THEN gl.Debit ELSE 0 END) AS Payroll,
        SUM(CASE WHEN je.EntryType = 'Depreciation'
            THEN gl.Debit ELSE 0 END) AS Depreciation,
        COUNT(DISTINCT CASE WHEN gl.SourceDocumentType = 'PayrollSummary'
            THEN gl.PostingDate END) AS PayDates
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
        LEFT JOIN JournalEntry AS je
            ON je.JournalEntryID = gl.SourceDocumentID
            AND gl.SourceDocumentType = 'JournalEntry'
    WHERE a.AccountNumber = 1090
    GROUP BY Month
)
SELECT mo.Month, ROUND(mo.StandardHours, 2) AS StandardHours,
    ROUND(mo.AppliedOverhead, 2) AS AppliedOverhead,
    ROUND(COALESCE(p.FactoryOverhead, 0), 2) AS FactoryOverhead,
    ROUND(COALESCE(p.Payroll, 0), 2) AS Payroll,
    ROUND(COALESCE(p.Depreciation, 0), 2) AS Depreciation,
    COALESCE(p.PayDates, 0) AS PayDates
FROM Made AS mo
    LEFT JOIN Posted AS p ON p.Month = mo.Month
WHERE mo.Month BETWEEN '{d.F}-01' AND '{d.C}-12'
ORDER BY mo.Month;""",
            [same_as_workbook(b, "monthly"),
             Check("months", months, lambda r: r.col("Month")),
             Check(f"Factory Overhead entries in {d.C}", round(v["foh"], 2),
                   lambda r: round(sum(x for mo, x in zip(r.col("Month"), r.col("FactoryOverhead"))
                                       if mo.startswith(str(d.C))), 2)),
             Check(f"payroll in {d.C}", round(v["payroll"], 2),
                   lambda r: round(sum(x for mo, x in zip(r.col("Month"), r.col("Payroll"))
                                       if mo.startswith(str(d.C))), 2)),
             Check(f"depreciation in {d.C}", round(v["dep"], 2),
                   lambda r: round(sum(x for mo, x in zip(r.col("Month"), r.col("Depreciation"))
                                       if mo.startswith(str(d.C))), 2)),
             Check(f"standard hours in {d.C}", round(v["stdh"], 2),
                   lambda r: round(sum(x for mo, x in zip(r.col("Month"), r.col("StandardHours"))
                                       if mo.startswith(str(d.C))), 2), 0.06),
             Check("Factory Overhead entries over the overhead applied, by year", [round(x, 3) for x in v["fo_ratio"]],
                   lambda r: [round(sum(f for mo, f in zip(r.col("Month"), r.col("FactoryOverhead")) if mo.startswith(str(y)))
                                    / sum(a for mo, a in zip(r.col("Month"), r.col("AppliedOverhead"))
                                          if mo.startswith(str(y))), 3) for y in d.years]),
             Check("months with three pay dates", three,
                   lambda r: [mo for mo, n in zip(r.col("Month"), r.col("PayDates")) if n == 3]),
             Check(f"{d.C} depreciation by month (its schedule)", [round(x, 2) for x in m["dep_months"]],
                   lambda r: [x for mo, x in zip(r.col("Month"), r.col("Depreciation")) if mo.startswith(str(d.C))])])
    s.answer("Requirement 2", f"""\
In {d.C}, 1090 received {money(v['inputs'])} (Q11): payroll {money(v['payroll'])}, the Factory Overhead entries
{money(v['foh'])}, and depreciation {money(v['dep'])}; the completions released {money(v['released_gl'])} at standard
(Q12), {v['conv_rate']:.2f} per standard hour (labor {v['labor_rate']:.2f}, overhead {v['oh_rate']:.2f}) against
{v['actual_rate']:.2f} of actual cost (Q13). Overhead, the inputs less the direct earnings of {money(v['direct'])}, is
{money(v['actual_oh'])}, {v['times']:.2f} times what the standards applied: the standards apply {v['third']:.2f} of it, the
CFO's "a third". Q14 is the monthly extract the workbook's regressions read, from {v['first_month']} on, and from
{v['start_month']} to show what the start-up month does to them; it carries the pay dates of each month, so the months
with three payrolls ({', '.join(three)}) can be marked before anyone reads a slope from them.""")


# --- Requirement 3 -----------------------------------------------------------------------------------------------

def r3(b):
    d, m = b.data, model(b)
    v = context(b, "r3")
    first, last = window(b)
    s = script(b)
    wcs = centers(b)
    run = ",\n".join(f"        SUM(CASE WHEN ro.WorkCenterID = {w}\n"
                     f"            THEN o.Units * ro.StandardRunHoursPerUnit END) AS {n}Run" for w, n in wcs)
    setup = ",\n".join(f"        SUM(CASE WHEN ro.WorkCenterID = {w}\n"
                       f"            THEN ro.StandardSetupHours END) AS {n}Setup" for w, n in wcs)
    cols = ",\n".join(f"    ROUND(h.{n}Run, 2) AS {n}Run" for w, n in wcs) + ",\n" + \
        ",\n".join(f"    ROUND(h.{n}Setup, 2) AS {n}Setup" for w, n in wcs)
    s.query("Requirement 3, Q15: the activities of the base year's completions, kept as the view FamilyActivity",
            f"Population: work orders completed in {d.C}, their routings and issues; expected: each family made",
            f"""\
DROP VIEW IF EXISTS FamilyActivity;
CREATE VIEW FamilyActivity AS
WITH Done AS (
    SELECT pc.WorkOrderID, SUM(pcl.QuantityCompleted) AS Units
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
    WHERE pc.CompletionDate BETWEEN {first} AND {last}
    GROUP BY pc.WorkOrderID
),
Orders AS (
    SELECT dn.WorkOrderID, dn.Units, wo.RoutingID,
        SUBSTR(i.ItemCode, 1, 7) AS Family, i.ItemGroup
    FROM Done AS dn
        INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = dn.WorkOrderID
        INNER JOIN Item AS i ON i.ItemID = wo.ItemID
),
Issues AS (
    SELECT mi.WorkOrderID, COUNT(*) AS IssueLines
    FROM MaterialIssueLine AS mil
        INNER JOIN MaterialIssue AS mi
            ON mi.MaterialIssueID = mil.MaterialIssueID
    WHERE mi.WorkOrderID IN (SELECT WorkOrderID FROM Done)
    GROUP BY mi.WorkOrderID
),
Families AS (
    SELECT o.Family, MIN(o.ItemGroup) AS ItemGroup,
        COUNT(*) AS WorkOrders, SUM(o.Units) AS UnitsCompleted,
        SUM(COALESCE(x.IssueLines, 0)) AS IssueLines
    FROM Orders AS o
        LEFT JOIN Issues AS x ON x.WorkOrderID = o.WorkOrderID
    GROUP BY o.Family
),
Hours AS (
    SELECT o.Family,
{run},
{setup}
    FROM Orders AS o
        INNER JOIN RoutingOperation AS ro ON ro.RoutingID = o.RoutingID
    GROUP BY o.Family
)
SELECT f.Family, f.ItemGroup, f.WorkOrders,
    ROUND(f.UnitsCompleted, 2) AS UnitsCompleted,
{cols},
    f.IssueLines
FROM Families AS f
    LEFT JOIN Hours AS h ON h.Family = f.Family;""")
    run_cols = [f"{n}Run" for w, n in wcs]
    setup_cols = [f"{n}Setup" for w, n in wcs]
    s.query("Requirement 3, Q16: the activities by family, as the workbook pastes them (Copy with Headers)",
            "Population: the view FamilyActivity; expected: run hours equal to the standard hours completed",
            """\
SELECT *
FROM FamilyActivity
ORDER BY Family;""",
            [same_as_workbook(b, "activity"),
             Check("run hours", round(v["run"], 2),
                   lambda r: round(sum(r.total(c) for c in run_cols), 2), 0.4),
             Check("setup hours", round(v["setup"], 2),
                   lambda r: round(sum(r.total(c) for c in setup_cols), 2), 0.4),
             Check("work orders", sum(a["wos"] for a in v["acts"]), lambda r: r.total("WorkOrders"))])
    setup_lines = "\n        + ".join(f"COALESCE({c}, 0)" for c in setup_cols)
    checks = []
    for f in sorted(m["batch"]):
        checks.append(Check(f"{f} average batch", m["batch"][f],
                            lambda r, f=f: r.where(Family=f)["AverageBatch"], 0.051))
    s.query("Requirement 3, Q17: setup hours and material issue lines per thousand units, by family",
            "Population: the view FamilyActivity; expected: small batches carry more setup per unit",
            f"""\
SELECT Family, ItemGroup, WorkOrders, UnitsCompleted,
    ROUND(UnitsCompleted / WorkOrders, 1) AS AverageBatch,
    ROUND(({setup_lines})
        / UnitsCompleted * 1000, 1) AS SetupHoursPerThousand,
    ROUND(IssueLines / UnitsCompleted * 1000, 1)
        AS IssueLinesPerThousand
FROM FamilyActivity
ORDER BY Family;""", checks)
    checks = []
    for a in v["acts"]:
        n = a["name"]
        checks += [Check(f"{n} units", a["units"], lambda r, n=n: r.where(ItemGroup=n)["UnitsCompleted"], 0.051),
                   Check(f"{n} work orders", a["wos"], lambda r, n=n: r.where(ItemGroup=n)["WorkOrders"]),
                   Check(f"{n} average batch", a["batch"], lambda r, n=n: r.where(ItemGroup=n)["AverageBatch"],
                         0.051),
                   Check(f"{n} setup hours per thousand units", a["setup"],
                         lambda r, n=n: r.where(ItemGroup=n)["SetupHoursPerThousand"], 0.051),
                   Check(f"{n} issue lines per thousand units", a["issues"],
                         lambda r, n=n: r.where(ItemGroup=n)["IssueLinesPerThousand"], 0.051)]
    checks.append(Check("the group with the most setup per unit", v["small"],
                        lambda r: max(zip(r.col("SetupHoursPerThousand"), r.col("ItemGroup")))[1]))
    s.query("Requirement 3, Q18: the same activities by item group",
            "Population: the view FamilyActivity; expected: Furniture's small batches carry twice the setup",
            f"""\
SELECT ItemGroup, SUM(WorkOrders) AS WorkOrders,
    ROUND(SUM(UnitsCompleted), 1) AS UnitsCompleted,
    ROUND(SUM(UnitsCompleted) / SUM(WorkOrders), 1) AS AverageBatch,
    ROUND(SUM({setup_lines})
        / SUM(UnitsCompleted) * 1000, 1) AS SetupHoursPerThousand,
    ROUND(SUM(IssueLines) / SUM(UnitsCompleted) * 1000, 1)
        AS IssueLinesPerThousand
FROM FamilyActivity
GROUP BY ItemGroup
ORDER BY ItemGroup;""", checks)
    s.query("Requirement 3, Q19: the hours available at each work center in the base year",
            f"Population: WorkCenterCalendar, {d.C}; expected: one row for each work center",
            f"""\
SELECT wc.WorkCenterID, wc.WorkCenterName,
    ROUND(SUM(wcc.AvailableHours), 2) AS AvailableHours,
    SUM(wcc.IsWorkingDay) AS WorkingDays
FROM WorkCenterCalendar AS wcc
    INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = wcc.WorkCenterID
WHERE wcc.CalendarDate BETWEEN {first} AND {last}
GROUP BY wc.WorkCenterID, wc.WorkCenterName
ORDER BY wc.WorkCenterID;""",
            [same_as_workbook(b, "calendar"),
             Check("available hours", round(v["avail"], 2), lambda r: r.total("AvailableHours"))])
    checks = [Check("plant available", round(v["avail"], 2), lambda r: r.where(WorkCenterName="Plant")["AvailableHours"]),
              Check("plant practical", round(v["pract"], 2), lambda r: r.where(WorkCenterName="Plant")["PracticalHours"]),
              Check("plant run hours", round(v["run"], 2), lambda r: r.where(WorkCenterName="Plant")["RunHours"], 0.006),
              Check("plant setup hours", round(v["setup"], 2), lambda r: r.where(WorkCenterName="Plant")["SetupHours"],
                    0.006),
              Check("plant routing hours", v["used"], lambda r: r.where(WorkCenterName="Plant")["RoutingHours"],
                    0.051),
              Check("plant share of available", round(v["of_avail"], 3),
                    lambda r: r.where(WorkCenterName="Plant")["ShareOfAvailable"], 0.0006),
              Check("plant share of practical", round(v["of_pract"], 3),
                    lambda r: r.where(WorkCenterName="Plant")["ShareOfPractical"], 0.0006),
              Check("unused practical hours", m["unused_h"],
                    lambda r: round(r.where(WorkCenterName="Plant")["PracticalHours"]
                                    - r.where(WorkCenterName="Plant")["RoutingHours"], 1), 0.051)]
    for c in v["centers"]:
        i = c["id"]
        checks += [Check(f"{c['name']} available", round(c["avail"], 2),
                         lambda r, i=i: r.where(WorkCenterID=i)["AvailableHours"]),
                   Check(f"{c['name']} practical", round(c["pract"], 2),
                         lambda r, i=i: r.where(WorkCenterID=i)["PracticalHours"]),
                   Check(f"{c['name']} routing hours", c["used"],
                         lambda r, i=i: r.where(WorkCenterID=i)["RoutingHours"], 0.051),
                   Check(f"{c['name']} share of available", round(c["of_avail"], 3),
                         lambda r, i=i: r.where(WorkCenterID=i)["ShareOfAvailable"], 0.0006),
                   Check(f"{c['name']} share of practical", round(c["of_pract"], 3),
                         lambda r, i=i: r.where(WorkCenterID=i)["ShareOfPractical"], 0.0006)]
    q = s.query("Requirement 3, Q20: each work center's available, practical, and routing hours, and its shares",
                f"Population: the calendar, 80% practical (tbl-18-02), {d.C}'s routings; expected: idle capacity",
                f"""\
WITH Done AS (
    SELECT pc.WorkOrderID, SUM(pcl.QuantityCompleted) AS Units
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
    WHERE pc.CompletionDate BETWEEN {first} AND {last}
    GROUP BY pc.WorkOrderID
),
Used AS (
    SELECT ro.WorkCenterID,
        SUM(dn.Units * ro.StandardRunHoursPerUnit) AS RunHours,
        SUM(ro.StandardSetupHours) AS SetupHours
    FROM Done AS dn
        INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = dn.WorkOrderID
        INNER JOIN RoutingOperation AS ro ON ro.RoutingID = wo.RoutingID
    GROUP BY ro.WorkCenterID
),
Available AS (
    SELECT WorkCenterID, SUM(AvailableHours) AS AvailableHours
    FROM WorkCenterCalendar
    WHERE CalendarDate BETWEEN {first} AND {last}
    GROUP BY WorkCenterID
),
Centers AS (
    SELECT wc.WorkCenterID, wc.WorkCenterName, av.AvailableHours,
        av.AvailableHours * {PRACTICAL:.2f} AS PracticalHours,
        COALESCE(u.RunHours, 0) AS RunHours,
        COALESCE(u.SetupHours, 0) AS SetupHours
    FROM WorkCenter AS wc
        INNER JOIN Available AS av ON av.WorkCenterID = wc.WorkCenterID
        LEFT JOIN Used AS u ON u.WorkCenterID = wc.WorkCenterID
),
Rows AS (
    SELECT WorkCenterID, WorkCenterName, AvailableHours,
        PracticalHours, RunHours, SetupHours
    FROM Centers
    UNION ALL
    SELECT NULL, 'Plant', SUM(AvailableHours), SUM(PracticalHours),
        SUM(RunHours), SUM(SetupHours)
    FROM Centers
)
SELECT WorkCenterID, WorkCenterName,
    ROUND(AvailableHours, 2) AS AvailableHours,
    ROUND(PracticalHours, 2) AS PracticalHours,
    ROUND(RunHours, 2) AS RunHours, ROUND(SetupHours, 2) AS SetupHours,
    ROUND(RunHours + SetupHours, 1) AS RoutingHours,
    ROUND((RunHours + SetupHours) / AvailableHours, 3)
        AS ShareOfAvailable,
    ROUND((RunHours + SetupHours) / PracticalHours, 3)
        AS ShareOfPractical
FROM Rows
ORDER BY COALESCE(WorkCenterID, 99);""", checks)
    remember(b, "capacity", q)
    s.answer("Requirement 3", f"""\
Routing time is the right measure of use because it is what each product should take, set by engineering for every
operation, and it does not depend on the time records that Part III found drifting toward packing and quality assurance
and recorded after the operations ended: the {d.C} completions' run hours ({v['run']:,.2f}) equal their standard labor
hours exactly. What it leaves out is everything the plant pays for beyond that standard: the indirect time, the hours
beyond the work, and the overtime of the surge days. The plant used {pct(v['of_pract'])} of its practical capacity on
routing time ({one(v['used'])} of {one(v['pract'])} hours); the {one(m['unused_h'])} practical hours left over are
exactly what Requirement 4's unused capacity holds.""")


# --- Requirement 4 -----------------------------------------------------------------------------------------------

def r4(b):
    d, m = b.data, model(b)
    s = script(b)
    checks = [same_as_workbook(b, "payclass")]
    for k, x in m["pclass"].items():
        checks += [Check(f"{k} employees", x["n"], lambda r, k=k: r.where(PayClass=k)["Employees"]),
                   Check(f"{k} gross pay", round(x["gross"], 2), lambda r, k=k: r.where(PayClass=k)["GrossPay"]),
                   Check(f"{k} employer tax", round(x["tax"], 2), lambda r, k=k: r.where(PayClass=k)["EmployerTax"]),
                   Check(f"{k} benefits", round(x["benefits"], 2), lambda r, k=k: r.where(PayClass=k)["Benefits"]),
                   Check(f"{k} with employer costs", round(x["total"], 2),
                         lambda r, k=k: round(sum(r.where(PayClass=k)[c] for c in ("GrossPay", "EmployerTax",
                                                                                   "Benefits")), 2))]
    s.query("Requirement 4, Q21: the committed cost of the crew and supervision: payroll by pay class",
            f"Population: Manufacturing payroll registers of {d.C}; expected: the hourly crew, a few salaried",
            f"""\
SELECT e.PayClass, COUNT(DISTINCT pr.EmployeeID) AS Employees,
    (SELECT COUNT(*)
     FROM Employee AS x
        INNER JOIN CostCenter AS y ON y.CostCenterID = x.CostCenterID
     WHERE y.CostCenterName = 'Manufacturing'
        AND x.PayClass = e.PayClass) AS EmployeesOnRecord,
    ROUND(SUM(pr.GrossPay), 2) AS GrossPay,
    ROUND(SUM(pr.EmployerPayrollTax), 2) AS EmployerTax,
    ROUND(SUM(pr.EmployerBenefits), 2) AS Benefits
FROM PayrollRegister AS pr
    INNER JOIN PayrollPeriod AS pp
        ON pp.PayrollPeriodID = pr.PayrollPeriodID
    INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = {d.C}
GROUP BY e.PayClass
ORDER BY e.PayClass;""", checks)


# --- Requirement 6 -----------------------------------------------------------------------------------------------

def family_list(m: dict) -> str:
    return ", ".join(f"'{q['name']}'" for q in m["buy"])


def r6(b):
    d, m = b.data, model(b)
    first, last = window(b)
    s = script(b)
    fams = family_list(m)
    names = ", ".join(q["name"] for q in m["buy"])
    s.query(f"Requirement 6, Q22: the materials of the families to buy ({names})",
            f"Population: their {d.C} completions and issues, and all {d.C} issues; expected: a quarter of issues",
            f"""\
WITH Received AS (
    SELECT grl.ItemID, SUM(grl.ExtendedStandardCost) AS Amount
    FROM GoodsReceiptLine AS grl
        INNER JOIN GoodsReceipt AS gr
            ON gr.GoodsReceiptID = grl.GoodsReceiptID
    WHERE gr.ReceiptDate BETWEEN {first} AND {last}
    GROUP BY grl.ItemID
),
Issued AS (
    SELECT mil.ItemID, SUM(mil.ExtendedStandardCost) AS Amount
    FROM MaterialIssueLine AS mil
        INNER JOIN MaterialIssue AS mi
            ON mi.MaterialIssueID = mil.MaterialIssueID
    WHERE mi.IssueDate BETWEEN {first} AND {last}
    GROUP BY mil.ItemID
),
SixBuilt AS (
    SELECT i.ItemID
    FROM Item AS i
        LEFT JOIN Received AS rc ON rc.ItemID = i.ItemID
        LEFT JOIN Issued AS iss ON iss.ItemID = i.ItemID
    WHERE i.ItemGroup IN ('Raw Materials', 'Packaging')
    ORDER BY COALESCE(rc.Amount, 0) - COALESCE(iss.Amount, 0) DESC
    LIMIT 6
),
FamilyIssues AS (
    SELECT mil.ItemID, mil.ExtendedStandardCost
    FROM MaterialIssueLine AS mil
        INNER JOIN MaterialIssue AS mi
            ON mi.MaterialIssueID = mil.MaterialIssueID
        INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = mi.WorkOrderID
        INNER JOIN Item AS i ON i.ItemID = wo.ItemID
    WHERE mi.IssueDate BETWEEN {first} AND {last}
        AND SUBSTR(i.ItemCode, 1, 7) IN ({fams})
)
SELECT
    (SELECT ROUND(SUM(pcl.QuantityCompleted
            * (i.StandardCost - i.StandardConversionCost)), 2)
     FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
     WHERE pc.CompletionDate BETWEEN {first} AND {last}
        AND SUBSTR(i.ItemCode, 1, 7) IN ({fams}))
        AS StandardMaterialCompleted,
    (SELECT ROUND(SUM(ExtendedStandardCost), 2)
     FROM FamilyIssues) AS IssuedToTheirWorkOrders,
    (SELECT ROUND(SUM(ExtendedStandardCost), 2)
     FROM FamilyIssues
     WHERE ItemID IN (SELECT ItemID FROM SixBuilt))
        AS OfWhichSixRawMaterials,
    (SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2)
     FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
     WHERE a.AccountNumber = 1045 AND gl.FiscalYear = {d.C}
        AND gl.SourceDocumentType = 'MaterialIssue') AS AllIssues1045;""",
            [same_as_workbook(b, "materials", families=fams),
             Check("standard material completed", round(m["buy_material"], 2),
                   lambda r: r.value("StandardMaterialCompleted")),
             Check("issued to their work orders", round(m["fam_issued"], 2),
                   lambda r: r.value("IssuedToTheirWorkOrders")),
             Check("of which the six raw materials", round(m["six_issued"], 2),
                   lambda r: r.value("OfWhichSixRawMaterials")),
             Check("all issues (1045)", round(m["issues"], 2), lambda r: r.value("AllIssues1045")),
             Check("share of the year's issues", round(m["fam_issued"] / m["issues"], 2),
                   lambda r: round(r.value("IssuedToTheirWorkOrders") / r.value("AllIssues1045"), 2))])


# --- Requirement 7 -----------------------------------------------------------------------------------------------

def r7(b):
    d, m = b.data, model(b)
    v = context(b, "r7")
    first, last = window(b)
    s = script(b)
    fams = family_list(m)
    wcs = centers(b)
    routing = ",\n".join(f"        COALESCE({n}Run, 0) + COALESCE({n}Setup, 0) AS {n}" for w, n in wcs)
    freed = ",\n".join(f"    ROUND(SUM(CASE WHEN Family IN ({fams})\n        THEN {n} ELSE 0 END), 1) AS {n}Freed"
                       for w, n in wcs)
    total = " + ".join(n for w, n in wcs)
    by_short = {x["short"]: x["hours"] for x in v["freed"]}
    checks = [Check(f"{n} hours freed", by_short.get(n, 0.0), lambda r, n=n: r.value(f"{n}Freed"), 0.051)
              for w, n in wcs]
    checks += [Check("hours freed", v["total"], lambda r: r.value("HoursFreed"), 0.06),
               Check("use of practical capacity before", round(v["use_before"], 3), lambda r: r.value("UseBefore"),
                     0.0006),
               Check("use of practical capacity after", round(v["use_after"], 3), lambda r: r.value("UseAfter"),
                     0.0006),
               Check("practical hours left unused today", v["unused_h"], lambda r: r.value("UnusedToday"),
                     0.06)]
    s.query("Requirement 7, Q23: the hours that buying the families of Requirement 6 frees at each work center",
            f"Population: FamilyActivity ({d.C}) and the calendar; expected: fewer than the hours already unused",
            f"""\
WITH Routing AS (
    SELECT Family,
{routing}
    FROM FamilyActivity
),
Practical AS (
    SELECT SUM(AvailableHours) * {PRACTICAL:.2f} AS PracticalHours
    FROM WorkCenterCalendar
    WHERE CalendarDate BETWEEN {first} AND {last}
)
SELECT
{freed},
    ROUND(SUM(CASE WHEN Family IN ({fams})
        THEN {total} ELSE 0 END), 1) AS HoursFreed,
    ROUND(SUM({total})
        / (SELECT PracticalHours FROM Practical), 3) AS UseBefore,
    ROUND((SUM({total})
        - SUM(CASE WHEN Family IN ({fams})
            THEN {total} ELSE 0 END))
        / (SELECT PracticalHours FROM Practical), 3) AS UseAfter,
    ROUND((SELECT PracticalHours FROM Practical)
        - SUM({total}), 1) AS UnusedToday
FROM Routing;""", checks)


# --- Requirement 8 -----------------------------------------------------------------------------------------------

def r8(b):
    d, m = b.data, model(b)
    v = context(b, "r8")
    s = script(b)
    months = ",\n".join(f"    ROUND(SUM(CASE WHEN sc.M = {k} THEN sc.ListValue ELSE 0 END), 2)\n        AS M{k:02d}"
                        for k in range(1, 13))
    b.data
    from notes import case2
    promos, lifts = case2.promotions(d), {x["id"]: x["lift"] for x in case2.volume(d)}

    def lift(r, pid):
        row = r.where(PromotionID=pid)
        months = [int(k) for k in row["PromotionMonths"].split(",")]
        values = [row[f"M{k:02d}"] for k in range(1, 13)]
        other = [x for k, x in enumerate(values, 1) if k not in months]
        return sum(values[k - 1] for k in months) / (sum(other) / len(other) * len(months)) - 1
    checks = [same_as_workbook(b, "promotions"),
              Check("promotions", len(promos), len),
              Check("largest lift in a promotion's months (none unusual, Part II case)", round(max(lifts.values()), 3),
                    lambda r: round(max(lift(r, p["id"]) for p in promos), 3), 0.0006)]
    for p in promos:
        pid = p["id"]
        checks += [Check(f"promotion {pid} months of its lines", ",".join(str(k) for k in p["months"]),
                         lambda r, pid=pid: r.where(PromotionID=pid)["PromotionMonths"]),
                   Check(f"promotion {pid} lift on the other months of its year", round(lifts[pid], 4),
                         lambda r, pid=pid: round(lift(r, pid), 4), 0.00006)]
    s.query("Requirement 8, Q24: list-price order value by month in each promotion's scope (the Part II case)",
            "Population: every sales order line in each promotion's scope and year; expected: no lift",
            f"""\
WITH Orders AS (
    SELECT so.OrderDate, sol.Quantity * sol.BaseListPrice AS ListValue,
        sol.PromotionID, i.CollectionName, i.ItemGroup,
        c.CustomerSegment
    FROM SalesOrderLine AS sol
        INNER JOIN SalesOrder AS so ON so.SalesOrderID = sol.SalesOrderID
        INNER JOIN Item AS i ON i.ItemID = sol.ItemID
        INNER JOIN Customer AS c ON c.CustomerID = so.CustomerID
),
Promotions AS (
    SELECT PromotionID, PromotionCode, ScopeType,
        CASE ScopeType
            WHEN 'Collection' THEN CollectionName
            WHEN 'ItemGroup' THEN ItemGroup
            ELSE CustomerSegment END AS Scope,
        SUBSTR(EffectiveStartDate, 1, 4) AS Year
    FROM PromotionProgram
),
Scoped AS (
    SELECT p.PromotionID,
        CAST(SUBSTR(o.OrderDate, 6, 2) AS INTEGER) AS M, o.ListValue
    FROM Promotions AS p
        INNER JOIN Orders AS o
            ON SUBSTR(o.OrderDate, 1, 4) = p.Year
            AND p.Scope = CASE p.ScopeType
                WHEN 'Collection' THEN o.CollectionName
                WHEN 'ItemGroup' THEN o.ItemGroup
                ELSE o.CustomerSegment END
)
SELECT p.PromotionID, p.PromotionCode, p.ScopeType, p.Scope,
    CAST(p.Year AS INTEGER) AS Year,
    (SELECT GROUP_CONCAT(M, ',')
     FROM (SELECT DISTINCT CAST(SUBSTR(o.OrderDate, 6, 2) AS INTEGER) AS M
           FROM Orders AS o
           WHERE o.PromotionID = p.PromotionID
           ORDER BY M)) AS PromotionMonths,
{months}
FROM Promotions AS p
    INNER JOIN Scoped AS sc ON sc.PromotionID = p.PromotionID
GROUP BY p.PromotionID, p.PromotionCode, p.ScopeType, p.Scope, p.Year
ORDER BY p.PromotionID;""", checks)
    after = d.one("SELECT COUNT(*) FROM SalesOrderLine sol JOIN SalesOrder so ON so.SalesOrderID = sol.SalesOrderID "
                  "JOIN PriceListLine pll ON pll.PriceListLineID = sol.PriceListLineID JOIN PriceList pl "
                  "ON pl.PriceListID = pll.PriceListID WHERE so.OrderDate > pl.EffectiveEndDate")
    active_ends = sorted({r[0] for r in d.q("SELECT EffectiveEndDate FROM PriceList WHERE Status = 'Active' "
                                            "AND PriceListID IN (SELECT PriceListID FROM PriceListLine)")})
    s.query("Requirement 8, Q25: the price lists, prices against list, and lines priced after the end (Ex. 8.6)",
            "Population: every price list; expected: expired lists still in use",
            """\
SELECT pl.PriceListID, pl.PriceListName, pl.ScopeType, pl.Status,
    pl.EffectiveStartDate, pl.EffectiveEndDate,
    (SELECT ROUND(MIN(pll.UnitPrice / i.ListPrice), 4)
     FROM PriceListLine AS pll
        INNER JOIN Item AS i ON i.ItemID = pll.ItemID
     WHERE pll.PriceListID = pl.PriceListID) AS LowestPriceToList,
    (SELECT ROUND(MAX(pll.UnitPrice / i.ListPrice), 4)
     FROM PriceListLine AS pll
        INNER JOIN Item AS i ON i.ItemID = pll.ItemID
     WHERE pll.PriceListID = pl.PriceListID) AS HighestPriceToList,
    (SELECT COUNT(*)
     FROM SalesOrderLine AS sol
        INNER JOIN SalesOrder AS so ON so.SalesOrderID = sol.SalesOrderID
        INNER JOIN PriceListLine AS pll
            ON pll.PriceListLineID = sol.PriceListLineID
     WHERE pll.PriceListID = pl.PriceListID
        AND so.OrderDate > pl.EffectiveEndDate) AS OrderLinesAfterEnd
FROM PriceList AS pl
ORDER BY pl.PriceListID;""",
            [same_as_workbook(b, "pricelists"),
             Check("expired lists used after their end", v["expired"],
                   lambda r: [i for i, st, n in zip(r.col("PriceListID"), r.col("Status"), r.col("OrderLinesAfterEnd"))
                              if st == "Expired" and n > 0]),
             Check("order lines priced after the end date", after, lambda r: r.total("OrderLinesAfterEnd")),
             Check("lowest price to list on an active list", round(v["low"], 2),
                   lambda r: round(min(x for x, st in zip(r.col("LowestPriceToList"), r.col("Status"))
                                       if st == "Active" and x is not None), 2)),
             Check("highest price to list on an active list", round(v["high"], 2),
                   lambda r: round(max(x for x, st in zip(r.col("HighestPriceToList"), r.col("Status"))
                                       if st == "Active" and x is not None), 2)),
             Check("end dates of the active lists in use", active_ends,
                   lambda r: sorted({e for e, st, lo in zip(r.col("EffectiveEndDate"), r.col("Status"),
                                                           r.col("LowestPriceToList"))
                                     if st == "Active" and lo is not None}))])
    approvers = d.q("SELECT e.JobTitle, COUNT(*) FROM PriceOverrideApproval a JOIN Employee e ON e.EmployeeID = "
                    "a.ApprovedByEmployeeID WHERE a.Status = 'Approved' GROUP BY 1 ORDER BY 2 DESC")
    s.query("Requirement 8, Q26: approved price overrides by the approver's job title",
            "Population: PriceOverrideApproval, status Approved; expected: one approver",
            """\
SELECT e.JobTitle AS ApproverJobTitle, COUNT(*) AS ApprovedOverrides
FROM PriceOverrideApproval AS poa
    INNER JOIN Employee AS e ON e.EmployeeID = poa.ApprovedByEmployeeID
WHERE poa.Status = 'Approved'
GROUP BY e.JobTitle
ORDER BY ApprovedOverrides DESC;""",
            [same_as_workbook(b, "overrides"),
             Check("approvers", [a[0] for a in approvers], lambda r: r.col("ApproverJobTitle")),
             Check("approved overrides", sum(a[1] for a in approvers), lambda r: r.total("ApprovedOverrides"))])


# --- Requirement 9 -----------------------------------------------------------------------------------------------

def r9(b):
    d, m = b.data, model(b)
    v = context(b, "r9")
    s = script(b)
    N = d.N
    s.query(f"Requirement 9, Q27: the depreciation FixedAsset charges to 1090 in {N} (the plan's)",
            "Population: assets depreciated to 1090, month after service to month before disposal; expected: a total",
            f"""\
WITH Assets AS (
    SELECT ROUND(fa.OriginalCost * 1.0 / fa.UsefulLifeMonths, 2)
            AS Monthly,
        CAST(SUBSTR(fa.InServiceDate, 1, 4) AS INTEGER) * 12
            + CAST(SUBSTR(fa.InServiceDate, 6, 2) AS INTEGER)
            AS FirstMonth,
        CAST(SUBSTR(fa.InServiceDate, 1, 4) AS INTEGER) * 12
            + CAST(SUBSTR(fa.InServiceDate, 6, 2) AS INTEGER)
            + fa.UsefulLifeMonths - 1 AS LifeEndMonth,
        CAST(SUBSTR(fa.DisposalDate, 1, 4) AS INTEGER) * 12
            + CAST(SUBSTR(fa.DisposalDate, 6, 2) AS INTEGER) - 2
            AS DisposalEndMonth
    FROM FixedAsset AS fa
        INNER JOIN Account AS a
            ON a.AccountID = fa.DepreciationDebitAccountID
    WHERE a.AccountNumber = 1090
),
InPlanYear AS (
    SELECT Monthly,
        CASE WHEN FirstMonth > {N} * 12 THEN FirstMonth
            ELSE {N} * 12 END AS FromMonth,
        CASE WHEN DisposalEndMonth < LifeEndMonth
                AND DisposalEndMonth < {N} * 12 + 11
                THEN DisposalEndMonth
            WHEN LifeEndMonth < {N} * 12 + 11 THEN LifeEndMonth
            ELSE {N} * 12 + 11 END AS ToMonth
    FROM Assets
)
SELECT ROUND(SUM(Monthly * (ToMonth - FromMonth + 1)), 2)
    AS PlanYearDepreciation
FROM InPlanYear
WHERE ToMonth >= FromMonth;""",
            [same_as_workbook(b, "plandep"),
             Check(f"depreciation of {N}", round(v["plan_dep"], 2), lambda r: r.value())])
    years = ",\n".join(f"    ROUND(SUM(CASE WHEN mv.MoveDate <= '{y}-12-31'\n        THEN mv.Quantity ELSE 0 END), 2)"
                       f" AS OnHand{y}" for y in d.years)
    moves = f"""\
WITH Moves AS (
    SELECT pcl.ItemID, pc.CompletionDate AS MoveDate,
        pcl.QuantityCompleted AS Quantity
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
    UNION ALL
    SELECT sl.ItemID, s.ShipmentDate, -sl.QuantityShipped
    FROM ShipmentLine AS sl
        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
    UNION ALL
    SELECT srl.ItemID, sr.ReturnDate, srl.QuantityReturned
    FROM SalesReturnLine AS srl
        INNER JOIN SalesReturn AS sr ON sr.SalesReturnID = srl.SalesReturnID
)"""
    negatives = [(x["code"], x["year"]) for x in v["negatives"]]
    checks = [same_as_workbook(b, "onhand")]
    for code, y in negatives:
        checks.append(Check(f"{code} negative at {y} (opening stock)", True,
                            lambda r, code=code, y=y: r.where(ItemCode=code)[f"OnHand{y}"] < -0.05))
    for st in v["stock"]:
        y = st["year"]
        checks.append(Check(f"units on hand at {y}", st["units"],
                            lambda r, y=y: round(sum(x for x in r.col(f"OnHand{y}") if x > 0), 1), 0.051))
    s.query("Requirement 9, Q28: manufactured finished goods made since the opening, on hand at each year-end",
            "Population: completions less shipments plus returns; expected: a few items negative (opening stock)",
            f"""\
{moves}
SELECT i.ItemID, i.ItemCode,
{years}
FROM Moves AS mv
    INNER JOIN Item AS i ON i.ItemID = mv.ItemID
WHERE i.SupplyMode = 'Manufactured' AND i.ItemType = 'Finished Good'
GROUP BY i.ItemID, i.ItemCode
ORDER BY i.ItemCode;""", checks)
    checks = [Check("years", d.years, lambda r: r.col("FiscalYear"))]
    for st in v["stock"]:
        y = st["year"]
        checks += [Check(f"{y} units", st["units"], lambda r, y=y: r.where(FiscalYear=y)["Units"], 0.051),
                   Check(f"{y} standard hours", st["stdh"], lambda r, y=y: r.where(FiscalYear=y)["StandardHours"],
                         0.051),
                   Check(f"{y} conversion at standard", round(st["conv"], 2),
                         lambda r, y=y: r.where(FiscalYear=y)["ConversionAtStandard"]),
                   Check(f"{y} at standard cost", round(st["std"], 2),
                         lambda r, y=y: r.where(FiscalYear=y)["AtStandardCost"]),
                   Check(f"{y} conversion per standard hour", round(st["per_hour"], 2),
                         lambda r, y=y: r.where(FiscalYear=y)["ConversionPerHour"])]
    s.query("Requirement 9, Q29: the stock of Q28 at each year-end, the negative items left out",
            "Population: the items of Q28 with units on hand; expected: stock growing every year",
            f"""\
{moves},
YearEnds AS (
    SELECT DISTINCT FiscalYear, FiscalYear || '-12-31' AS YearEnd
    FROM GLEntry
    WHERE FiscalYear BETWEEN {d.F} AND {d.C}
),
OnHand AS (
    SELECT ye.FiscalYear, mv.ItemID, SUM(mv.Quantity) AS Units
    FROM YearEnds AS ye
        INNER JOIN Moves AS mv ON mv.MoveDate <= ye.YearEnd
    GROUP BY ye.FiscalYear, mv.ItemID
)
SELECT oh.FiscalYear, COUNT(*) AS Items, ROUND(SUM(oh.Units), 1) AS Units,
    ROUND(SUM(oh.Units * i.StandardLaborHoursPerUnit), 1)
        AS StandardHours,
    ROUND(SUM(oh.Units * i.StandardConversionCost), 2)
        AS ConversionAtStandard,
    ROUND(SUM(oh.Units * i.StandardCost), 2) AS AtStandardCost,
    ROUND(SUM(oh.Units * i.StandardConversionCost)
        / SUM(oh.Units * i.StandardLaborHoursPerUnit), 2)
        AS ConversionPerHour
FROM OnHand AS oh
    INNER JOIN Item AS i ON i.ItemID = oh.ItemID
WHERE i.SupplyMode = 'Manufactured' AND i.ItemType = 'Finished Good'
    AND oh.Units > 0
GROUP BY oh.FiscalYear
ORDER BY oh.FiscalYear;""", checks)
    income = {y: notes(b).net_income(d, y) for y in d.years}
    s.query("Requirement 9, Q30: income before income taxes as recorded, by fiscal year (for materiality)",
            "Population: revenue and expense postings, closes left out (no tax account); expected: a row a year",
            f"""\
SELECT gl.FiscalYear,
    ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS IncomeBeforeTaxes
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE a.AccountType IN ('Revenue', 'Expense')
    AND gl.FiscalYear BETWEEN {d.F} AND {d.C}
{CLOSES}
GROUP BY gl.FiscalYear
ORDER BY gl.FiscalYear;""",
            [same_as_workbook(b, "income")] +
            [Check(f"{y} income before income taxes", round(x, 2), lambda r, y=y: r.where(FiscalYear=y)["IncomeBeforeTaxes"])
             for y, x in income.items()] +
            [Check(f"{d.P} materiality", v["mat_p"],
                   lambda r: round(MATERIALITY * r.where(FiscalYear=d.P)["IncomeBeforeTaxes"], 2)),
             Check(f"{d.C} materiality", v["mat_c"],
                   lambda r: round(MATERIALITY * r.where(FiscalYear=d.C)["IncomeBeforeTaxes"], 2))])
    s.query("Requirement 9, Q31: the finished goods (1040) on the opening entry, which has no item detail",
            "Population: the opening entry's 1040 line; expected: one row, left out of the revaluation",
            """\
SELECT je.EntryNumber,
    ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS OpeningFinishedGoods
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    INNER JOIN JournalEntry AS je ON je.EntryNumber = gl.VoucherNumber
WHERE a.AccountNumber = 1040 AND je.EntryType = 'Opening'
GROUP BY je.EntryNumber;""",
            [same_as_workbook(b, "openingfg"),
             Check("opening finished goods", round(v["opening_fg"], 2), lambda r: r.value("OpeningFinishedGoods"))])
    s3 = v["s_c"]
    s.answer("Requirement 9", f"""\
Q28 and Q29 rebuild the manufactured finished goods made since the ledger opened and still on hand: {one(v['s_f']['units'])}
units ({one(v['s_f']['stdh'])} standard hours) at the end of {d.F}, {one(v['s_p']['units'])} at the end of {d.P}, and
{one(s3['units'])} ({one(s3['stdh'])} standard hours, {money(s3['std'])} at standard) at the end of {d.C}, carried at
about {s3['per_hour']:.2f} of conversion per standard hour. {' and '.join(f"{c} at {y}" for c, y in negatives)} come
out negative, which proves stock that predates the ledger's item detail; they are left out, as is the opening
{money(v['opening_fg'])} of finished goods (Q31). The workbook revalues this stock at the proposed standard; Q30 gives
the materiality it is measured against ({money(v['mat_p'])} for {d.P} and {money(v['mat_c'])} for {d.C}).""")


# --- Milestones ----------------------------------------------------------------------------------------------------

def m1(b):
    v = context(b, "m1")
    script(b)
    g0 = v["g0"]
    groups = recall(b, "groups")
    groups.checks += [Check(f"Milestone 1: {g0['name']} margin at standard", round(g0["m_std"], 4),
                            lambda r: r.where(ItemGroup=g0["name"])["MarginAtStandard"], 0.00006),
                      Check(f"Milestone 1: {g0['name']} margin with the year's variance", round(g0["m_year"], 4),
                            lambda r: r.where(ItemGroup=g0["name"])["MarginWithYearVariance"], 0.00006)]
    recall(b, "5080").checks.append(Check("Milestone 1: family variances", round(v["variance"], 2),
                                          lambda r: r.value("FamilyVariance")))
    recall(b, "debits").checks.append(Check("Milestone 1: inputs to 1090", round(v["inputs"], 2),
                                            lambda r: r.total("Debits")))
    recall(b, "released").checks.append(Check("Milestone 1: released", round(v["released"], 2),
                                              lambda r: r.value("CreditsTo1090")))
    recall(b, "capacity").checks.append(Check("Milestone 1: share of practical capacity used", round(v["use"], 3),
                                              lambda r: r.where(WorkCenterName="Plant")["ShareOfPractical"], 0.0006))


def m2(b):
    v = context(b, "m2")
    script(b)
    recall(b, "capacity").checks.append(Check("Milestone 2: unused capacity hours", v["unused_h"],
                                              lambda r: round(r.where(WorkCenterName="Plant")["PracticalHours"]
                                                              - r.where(WorkCenterName="Plant")["RoutingHours"], 1),
                                              0.051))


EXERCISES = [("Requirement 1", r1), ("Requirement 2", r2), ("Requirement 3", r3), ("Requirement 4", r4),
             ("Requirement 6", r6), ("Requirement 7", r7), ("Requirement 8", r8), ("Requirement 9", r9),
             ("Milestone 1", m1), ("Milestone 2", m2)]
