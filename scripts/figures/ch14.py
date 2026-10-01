"""Chapter 14 figures (data models and DAX measures).

Every value is computed here from the dataset with the logic of the chapter's model: the invoice
lines with the invoice date, number and customer merged in (Tutorial 14.1), standard cost as
Quantity * Item.StandardCost left unrounded (Tutorial 14.2), and the ledger with the year-end
closing entries flagged through JournalEntry.EntryType (Tutorial 14.3). The same results were
checked against Power BI Desktop 2.158's engine on a reference model of the tutorials.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache

import excel as xl
import powerbi as pbi
from ch13 import _one_to_many
from data import one, q, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK, RULE,
                    SMALL, TEAL, WHITE, Diagram, esc)

GROUPS = ["Accessories", "Furniture", "Lighting", "Services", "Textiles"]
YEARS = [2024, 2025, 2026]
CALENDAR = (date(2024, 1, 1), date(2027, 12, 31))
CLOSE = "j.EntryType LIKE 'Year-End Close%'"


@lru_cache(maxsize=1)
def lines() -> list[dict]:
    """The fact table of the star: one row per invoice line with the merged header columns."""
    require_columns("SalesInvoiceLine", ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity",
                                         "LineTotal"])
    require_columns("SalesInvoice", ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID"])
    require_columns("Item", ["ItemID", "ItemGroup", "StandardCost", "ListPrice"])
    rows = q("SELECT l.SalesInvoiceLineID, si.InvoiceDate, si.CustomerID, i.ItemGroup, l.Quantity, "
             "l.LineTotal, l.Quantity * i.StandardCost FROM SalesInvoiceLine l "
             "JOIN SalesInvoice si USING (SalesInvoiceID) JOIN Item i USING (ItemID)")
    assert len(rows) == one("SELECT COUNT(*) FROM SalesInvoiceLine")[0], "every line finds its invoice"
    out = []
    for r in rows:
        d = r[1]
        out.append(dict(id=r[0], date=d, cust=r[2], grp=r[3], qty=r[4], rev=r[5], cost=r[6],
                        year=int(d[:4]), quarter=f"{d[:4]}-Q{(int(d[5:7]) + 2) // 3}"))
    return out


def total(field: str, **match) -> float:
    return sum(r[field] for r in lines() if all(r[k] == v for k, v in match.items()))


def margin_pct(**match) -> float:
    rev = total("rev", **match)
    return (rev - total("cost", **match)) / rev


def pct(value: float, places: int = 2) -> str:
    return f"{100 * value:.{places}f}%"


def quarters(years: list[int]) -> list[str]:
    return [f"{y}-Q{n}" for y in years for n in range(1, 5)]


@lru_cache(maxsize=1)
def pnl() -> dict:
    """Credit less debit by fiscal year, account type and subtype, with and without the closes."""
    rows = q("SELECT g.FiscalYear, a.AccountType, a.AccountSubType, "
             f"CASE WHEN {CLOSE} THEN 1 ELSE 0 END, SUM(g.Credit - g.Debit) "
             "FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
             "LEFT JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
             "WHERE a.AccountType IN ('Revenue', 'Expense') GROUP BY 1, 2, 3, 4")
    out = defaultdict(float)
    for year, typ, sub, close, value in rows:
        out[(year, typ, sub, "all")] += value
        if not close:
            out[(year, typ, sub, "open")] += value
    return out


def pnl_total(year: int, kind: str, typ: str | None = None, sub: str | None = None) -> float:
    return sum(v for (y, t, s, k), v in pnl().items()
               if y == year and k == kind and typ in (None, t) and sub in (None, s))


# -- fig-14-01 --------------------------------------------------------------------------------

SIL_13 = ["BaseListPrice", "Discount", "DiscountAmount", "ItemID", "LineTotal", "ListAmount",
          "PricingMethod", "PromotionID", "Quantity", "SalesInvoiceID", "SalesInvoiceLineID", "UnitPrice"]
MERGED = ("CustomerID", "InvoiceDate", "InvoiceNumber")
SIL_14 = sorted(SIL_13 + list(MERGED))
ITEM = ["ItemCode", "ItemGroup", "ItemID", "ItemName", "ListPrice", "ProductType", "StandardCost"]
CUSTOMER = ["CustomerID", "CustomerName", "CustomerSegment", "Region"]
DATE_COLS = ["Date", "MonthName", "MonthNumber", "Quarter", "Year", "YearMonth", "YearQuarter"]


def fig_14_01() -> Diagram:
    d = Diagram("The Sales Tables as a Snowflake and as a Star")
    _one_to_many("Item", "ItemID", "SalesInvoiceLine", "ItemID")
    _one_to_many("SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID")
    _one_to_many("Customer", "CustomerID", "SalesInvoice", "CustomerID")
    first, last = one("SELECT MIN(InvoiceDate), MAX(InvoiceDate) FROM SalesInvoice")
    assert CALENDAR[0].isoformat() <= first and last <= CALENDAR[1].isoformat(), "Date covers every invoice"
    # Top: the model of Chapter 13, with the header between the lines and Customer.
    d.text("<b>Chapter 13: Customer reaches the lines only through the invoice header</b>", 0, 0, 860, 22,
           size=SMALL)
    top = 30
    item = pbi.model_table(d, "Item", 0, top + 22, ITEM, w=140)   # ItemID level with the lines' ItemID
    sil = pbi.model_table(d, "SalesInvoiceLine", 200, top, SIL_13, w=170)
    si = pbi.model_table(d, "SalesInvoice", 450, top + 40, ["CustomerID", "FiscalQuarter", "FiscalYear",
                                                           "InvoiceDate", "InvoiceNumber", "Month",
                                                           "Period", "SalesInvoiceID"], w=160)
    cust = pbi.model_table(d, "Customer", 700, top + 40, CUSTOMER, w=160)
    assert item.rows["ItemID"] == sil.rows["ItemID"]
    pbi.relationship(d, item.right("ItemID"), sil.left("ItemID"))
    pbi.relationship(d, si.left("SalesInvoiceID"), sil.right("SalesInvoiceID"),
                     [(410, si.rows["SalesInvoiceID"]), (410, sil.rows["SalesInvoiceID"])])
    pbi.relationship(d, cust.left("CustomerID"), si.right("CustomerID"),
                     [(655, cust.rows["CustomerID"]), (655, si.rows["CustomerID"])])
    # Bottom: the star of Tutorial 14.1.
    y0 = sil.y + sil.h + 30
    d.box("", 0, y0 - 12, 860, 1, fill=RULE, stroke=RULE, rounded=False)
    d.text("<b>Chapter 14: every dimension relates to the invoice lines directly</b>", 0, y0, 860, 22,
           size=SMALL)
    top = y0 + 30
    sil2 = pbi.model_table(d, "SalesInvoiceLine", 330, top, SIL_14, w=180, marked=MERGED)
    item2 = pbi.model_table(d, "Item", 60, top + 88, ITEM, w=140)
    cust2 = pbi.model_table(d, "Customer", 660, top, CUSTOMER, w=160)
    date2 = pbi.model_table(d, "Date", 660, top + 160, DATE_COLS, w=160)
    assert item2.rows["ItemID"] == sil2.rows["ItemID"]
    pbi.relationship(d, item2.right("ItemID"), sil2.left("ItemID"))
    pbi.relationship(d, cust2.left("CustomerID"), sil2.right("CustomerID"),
                     [(570, cust2.rows["CustomerID"]), (570, sil2.rows["CustomerID"])])
    pbi.relationship(d, date2.left("Date"), sil2.right("InvoiceDate"),
                     [(610, date2.rows["Date"]), (610, sil2.rows["InvoiceDate"])])
    y = sil2.y + sil2.h + 16
    d.box("", 0, y + 3, 16, 16, fill=AMBER_TINT, stroke=RULE, rounded=False)
    d.text("Merged from SalesInvoice in Tutorial 14.1 &nbsp;&nbsp;<b>1</b>&nbsp;the table that holds the key"
           " &nbsp;&nbsp;<b>*</b>&nbsp;the table that refers to it &nbsp;&nbsp;<b>Arrow</b>&nbsp;the direction "
           "of the filter", 22, y, 838, 22, size=SMALL)
    d.text("<i>Model view lists each table's columns in alphabetical order; the mock draws each line to the "
           "related columns. SalesInvoice stays in the Power Query Editor, where the merge reads it, but is "
           "no longer loaded.</i>", 0, y + 26, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-14-02 --------------------------------------------------------------------------------

def fig_14_02() -> Diagram:
    d = Diagram("The Date Table in Table View")
    days = (CALENDAR[1] - CALENDAR[0]).days + 1
    gl_first, gl_last = one("SELECT MIN(PostingDate), MAX(PostingDate) FROM GLEntry")
    assert CALENDAR[0].isoformat() <= gl_first and gl_last <= CALENDAR[1].isoformat(), "Date covers the ledger"
    assert days == 1461
    pane_w = 150
    win = pbi.window(d, 420, view="Table", tab="Table tools", tabs=pbi.TABLE_TABS, panes=["Data"],
                     pane_w=pane_w, buttons=["Name", "Manage relationships", "New measure", "Quick measure",
                                             "New column", "New table", "Mark as date table"])
    rows = []
    for i in range(9):
        day = CALENDAR[0] + timedelta(days=i)
        rows.append([f"{day.month}/{day.day}/{day.year}", str(day.year), f"Q{(day.month + 2) // 3}",
                     f"{day.year}-Q{(day.month + 2) // 3}", f"{day.year}-{day.month:02d}", str(day.month),
                     day.strftime("%b")])
    headers = ["Date", "Year", "Quarter", "YearQuarter", "YearMonth", "MonthNumber", "MonthName"]
    widths = [84, 56, 70, 98, 88, 108, 96]
    grid = pbi.table_view(d, win.canvas_x + 12, win.top + 14, "Date", headers, widths, rows, days)
    xl.emphasis(d, *grid["status"])
    for i, name in enumerate(["Customer", "Date", "Item", "SalesInvoice", "SalesInvoiceLine"]):
        on = name == "Date"
        d.text(f"<b>{esc(name)}</b>" if on else esc(name), win.panes_x + 8, win.top + 34 + i * 26,
               pane_w - 12, 22, size=SMALL, color=BLUE if on else INK)
    d.text("<i>The first rows of the Date table after Tutorial 14.1, Step 3. The status bar, outlined, names "
           "the table and counts its rows: one for each day of four full years. SalesInvoice is still "
           "loaded at this step.</i>", 0, win.bottom + 10, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-14-03 --------------------------------------------------------------------------------

def fig_14_03() -> Diagram:
    d = Diagram("The Filter Context of One Matrix Cell")
    cell = total("rev", grp="Furniture", quarter="2026-Q4")
    n_cell = sum(1 for r in lines() if r["grp"] == "Furniture" and r["quarter"] == "2026-Q4")
    assert abs(cell - 4156787.84) < 0.005, cell   # Chapter 6's fourth-quarter Furniture revenue
    rows = [[g, pbi.amount(total("rev", grp=g, quarter="2026-Q3")),
             pbi.amount(total("rev", grp=g, quarter="2026-Q4"))] for g in GROUPS]
    d.text("<b>1. The cell</b>", 0, 0, 330, 22, size=SMALL)
    t = pbi.table_visual(d, 0, 26, ["ItemGroup", "2026-Q3", "2026-Q4"], [104, 108, 108], rows,
                         title="Revenue by ItemGroup and YearQuarter")
    cx, cy, cw, ch = t["geometry"][(1, 2)]
    xl.emphasis(d, cx, cy, cw, ch)
    # The two filters the cell carries.
    d.text("<b>2. Its filters</b>", 380, 0, 200, 22, size=SMALL)
    f_item = d.box("<b>Item</b><br>ItemGroup = Furniture", 380, 40, 190, 54, fill=BLUE_TINT, stroke=BLUE,
                   size=SMALL)
    f_date = d.box("<b>Date</b><br>YearQuarter = 2026-Q4", 380, 120, 190, 54, fill=BLUE_TINT, stroke=BLUE,
                   size=SMALL)
    src = d.container(cx, cy, cw, ch)
    d.arrow(src, f_item, color=CORAL, exit=(1, 0.5), entry=(0, 0.5))
    d.arrow(src, f_date, color=CORAL, exit=(1, 0.5), entry=(0, 0.5))
    # The fact table and the sum.
    d.text("<b>3. The lines that remain</b>", 620, 0, 240, 22, size=SMALL)
    fact = d.box(f"<b>SalesInvoiceLine</b><br>{len(lines()):,} lines in all<br>{n_cell:,} Furniture lines "
                 f"invoiced in 2026-Q4", 620, 52, 240, 96, fill=WHITE, stroke=BLUE, stroke_width=2, size=SMALL)
    d.arrow(f_item, fact, exit=(1, 0.5), entry=(0, 0.3))
    d.arrow(f_date, fact, exit=(1, 0.5), entry=(0, 0.8))
    d.text("<b>4. The measure</b>", 620, 168, 240, 22, size=SMALL)
    result = d.box(f"SUM ( SalesInvoiceLine[LineTotal] )<br><b>= {pbi.amount(cell)}</b>", 620, 194, 240, 54,
                   fill=GRAY_TINT, stroke=GRAY, size=SMALL)
    d.arrow(fact, result, exit=(0.5, 1), entry=(0.5, 0))
    d.text("<i>The row and the column of the cell become filters on the Item and Date tables; the "
           "relationships carry them to the invoice lines, and the measure adds up the lines that remain. "
           "A slicer on the page would add its own filter in the same way.</i>", 0, 268, 860, 40,
           size=SMALL, color=GRAY)
    return d


# -- fig-14-04 --------------------------------------------------------------------------------

def fig_14_04() -> Diagram:
    d = Diagram("Row Context With and Without Context Transition")
    grand = total("rev")
    by_cust = defaultdict(float)
    for r in lines():
        by_cust[r["cust"]] += r["rev"]
    top3 = sorted(by_cust, key=by_cust.get, reverse=True)[:3]
    names = {cid: (name, seg) for cid, name, seg in q("SELECT CustomerID, CustomerName, CustomerSegment "
                                                      "FROM Customer")}
    n_customers = len(names)
    assert names[top3[0]][0] == "Wright PLC" and abs(by_cust[top3[0]] - 1645084.67) < 0.005
    formulas = ["Revenue All = SUM ( SalesInvoiceLine[LineTotal] )",
                "Revenue Own = CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ) )"]
    for i, f in enumerate(formulas):
        d.text(f"<b>{'AB'[i]}</b>", 0, 4 + i * 34, 20, 24, size=SMALL)
        d.box(pbi.highlight_dax(f), 24, 2 + i * 34, 520, 28, fill=WHITE, stroke=RULE, size=SMALL,
              align="left", rounded=False)
    rows = []
    for cid in top3:
        rows.append([str(cid), names[cid][0], names[cid][1], f"{grand:.2f}", f"{by_cust[cid]:.2f}"])
    headers = ["CustomerID", "CustomerName", "CustomerSegment", "Revenue All", "Revenue Own"]
    widths = [96, 170, 150, 140, 140]
    grid = pbi.table_view(d, 0, 84, "Customer", headers, widths, rows, n_customers)
    x_all = sum(widths[:3])
    d.outline(x_all, 84, widths[3], pbi.ROW + 2 + 3 * pbi.ROW, CORAL, width=2.5, front=True)
    d.outline(x_all + widths[3], 84, widths[4], pbi.ROW + 2 + 3 * pbi.ROW, TEAL, width=2.5, front=True)
    d.text("<b>A</b>: the row context alone filters nothing, so SUM adds every invoice line on every row "
           "(coral outline).", 0, grid["bottom"] + 12, 860, 22, size=SMALL)
    d.text("<b>B</b>: CALCULATE turns the current customer into a filter, and the relationship carries it to "
           "the lines: each customer's own revenue (teal outline).", 0, grid["bottom"] + 36, 860, 40, size=SMALL)
    d.text("<i>Two calculated columns on the Customer table in Table view, sorted by Revenue Own, largest "
           "first, with all years of invoice lines. The two columns are left in the General format, without "
           "a thousands separator.</i>", 0, grid["bottom"] + 80, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-14-05 --------------------------------------------------------------------------------

def fig_14_05() -> Diagram:
    d = Diagram("A Filter That Replaces and a Filter That Is Removed")
    rev = {g: total("rev", grp=g, year=2026) for g in GROUPS}
    year_total = sum(rev.values())
    furniture = rev["Furniture"]
    all_years = total("rev")
    assert abs(year_total - 29756420.08) < 0.005 and furniture / year_total > 0.5
    pbi.canvas(d, 0, 0, 860, 300)
    pbi.slicer_tiles(d, 16, 16, "Year", ["2024", "2025", "2026"], "2026", tile_w=56)
    rows = [[g, pbi.amount(rev[g]), pbi.amount(furniture), pct(rev[g] / year_total)] for g in GROUPS]
    widths = [120, 130, 160, 150]
    t = pbi.table_visual(d, 16, 86, ["ItemGroup", "Revenue", "Furniture Revenue", "Share of Revenue"],
                         widths, rows, total=["Total", pbi.amount(year_total), pbi.amount(furniture), "100.00%"])
    fx, fy, fw, _ = t["geometry"][(-1, 2)]
    xl.emphasis(d, fx, fy, fw, pbi.ROW * 7)
    note_x = t["right"] + 20
    d.box(f"<b>With ALL ( SalesInvoiceLine )</b> as the denominator instead, Furniture's share reads "
          f"{pct(furniture / all_years)} and the five shares add up to {pct(year_total / all_years)}: removing "
          "the filters from the fact table removes the year as well.", note_x, 86, 860 - 16 - note_x, 118,
          fill=CORAL_TINT, stroke=CORAL, size=SMALL, align="left", valign="top")
    d.text("<i>The table visual on the Margins page of Tutorial 14.2, with the year slicer set to 2026. "
           "Outlined: Furniture Revenue, the same on every row because its filter replaces the row's item "
           "group. Share of Revenue removes the filter on Item and keeps the year.</i>", 0, 310, 860, 40,
           size=SMALL, color=GRAY)
    return d



# -- fig-14-06 --------------------------------------------------------------------------------

TEST_1 = """// Test 1: fiscal 2026 revenue and lines must equal Chapter 6's control totals
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[Year],
    "Lines", [Invoice Lines],
    "Revenue", ROUND ( [Revenue], 2 ),
    "Gross Margin", ROUND ( [Gross Margin], 2 ),
    "Margin %", ROUND ( [Margin %], 4 )
)
ORDER BY 'Date'[Year]"""


def raw(value: float) -> str:
    """A value as the results grid shows it: unformatted, in the shortest form that round-trips."""
    return repr(value) if value != int(value) else str(int(value))


def fig_14_06() -> Diagram:
    d = Diagram("A Test in DAX Query View")
    pane_w = 140
    win = pbi.window(d, 600, view="DAX query", tab="Home", tabs=pbi.QUERY_TABS, panes=["Data"],
                     pane_w=pane_w, buttons=["Format", "Comment", "Uncomment", "Find", "Replace",
                                             "Command palette"])
    x, w = win.canvas_x + 8, win.canvas_w - 16
    bottom = pbi.dax_query_editor(d, x, win.top + 10, w, TEST_1, ["Tests"], "Tests")
    rows = []
    for y in YEARS:
        n = sum(1 for r in lines() if r["year"] == y)
        rev = round(total("rev", year=y), 2)
        gm = round(total("rev", year=y) - total("cost", year=y), 2)
        rows.append([str(y), str(n), raw(rev), raw(gm), raw(round(margin_pct(year=y), 4))])
    assert rows[2][1:3] == ["9522", "29756420.08"], rows[2]
    res = pbi.dax_results(d, x, bottom + 12, ["Date[Year]", "[Lines]", "[Revenue]", "[Gross Margin]",
                                              "[Margin %]"], [100, 80, 130, 130, 100], rows)
    xl.emphasis(d, *res["geometry"][(2, 2)])
    for i, name in enumerate(["Measures", "Customer", "Date", "Item", "SalesInvoiceLine"]):
        d.text(esc(name), win.panes_x + 8, win.top + 34 + i * 26, pane_w - 12, 22, size=SMALL)
    d.text("<i>The Tests tab of Tutorial 14.2 after Run. The grid shows values without the measures' formats, "
           "which is why the test rounds them. Outlined: the fiscal 2026 revenue, which must equal Chapter 6's "
           "control total.</i>", 0, win.bottom + 10, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-14-07 --------------------------------------------------------------------------------

def fig_14_07() -> Diagram:
    d = Diagram("Margin at Standard Cost by Item Group and Quarter")
    qs = quarters([2025, 2026])
    fur = {p: margin_pct(grp="Furniture", quarter=p) for p in qs}
    assert f"{100 * fur['2026-Q3']:.2f}" == "42.26" and f"{100 * fur['2026-Q4']:.2f}" == "40.78", fur
    assert min(fur.values()) == fur["2026-Q4"], "the fourth quarter of 2026 is the lowest of the two years"
    in_years = [r for r in lines() if r["year"] in (2025, 2026)]
    rows = []
    for g in GROUPS:
        values = [pct(margin_pct(grp=g, quarter=p)) for p in qs]
        rev = sum(r["rev"] for r in in_years if r["grp"] == g)
        cost = sum(r["cost"] for r in in_years if r["grp"] == g)
        rows.append((0, g, values + [pct((rev - cost) / rev)], ""))
    rev = sum(r["rev"] for r in in_years)
    cost = sum(r["cost"] for r in in_years)
    rows.append((0, "Total", [pct(margin_pct(quarter=p)) for p in qs] + [pct((rev - cost) / rev)], ""))
    widths = [104] + [80] * 9
    pbi.canvas(d, 0, 0, 860, 230)
    pbi.matrix_visual(d, 12, 14, ["ItemGroup", *qs, "Total"], widths, rows,
                      title="Margin % by ItemGroup and YearQuarter")
    fy = 14 + 26 + pbi.ROW * 2
    xl.emphasis(d, 18, fy, sum(widths), pbi.ROW)
    d.text("<i>The matrix of Tutorial 14.2, Step 6, filtered to fiscal 2025 and 2026. Outlined: the Furniture "
           "row. Every cell and total is a ratio of totals, Gross Margin divided by Revenue for the lines in "
           "its filter context.</i>", 0, 240, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-14-08 --------------------------------------------------------------------------------

GL_COLS = ["AccountID", "CostCenterID", "Credit", "Debit", "EntryType", "GLEntryID", "IsYearEndClose",
           "PostingDate", "SourceDocumentType", "VoucherNumber"]
ACCOUNT = ["AccountID", "AccountName", "AccountNumber", "AccountSubType", "AccountType", "NormalBalance"]


def fig_14_08() -> Diagram:
    d = Diagram("Two Fact Tables Sharing One Date Table")
    _one_to_many("Account", "AccountID", "GLEntry", "AccountID")
    _one_to_many("CostCenter", "CostCenterID", "GLEntry", "CostCenterID")
    _one_to_many("Customer", "CustomerID", "SalesInvoice", "CustomerID")
    cust = pbi.model_table(d, "Customer", 0, 0, CUSTOMER, w=120)   # above Item, so the lines do not cross
    item = pbi.model_table(d, "Item", 0, 150, ITEM, w=120)
    sil = pbi.model_table(d, "SalesInvoiceLine", 172, 0, SIL_14, w=160)
    gl = pbi.model_table(d, "GLEntry", 530, 0, GL_COLS, w=160)
    acct = pbi.model_table(d, "Account", 730, 70, ACCOUNT, w=130)
    cc = pbi.model_table(d, "CostCenter", 730, 270, ["CostCenterID", "CostCenterName"], w=130)
    dt = pbi.model_table(d, "Date", 361, 300, DATE_COLS, w=140)
    pbi.relationship(d, item.right("ItemID"), sil.left("ItemID"),
                     [(134, item.rows["ItemID"]), (134, sil.rows["ItemID"])])
    pbi.relationship(d, cust.right("CustomerID"), sil.left("CustomerID"),
                     [(152, cust.rows["CustomerID"]), (152, sil.rows["CustomerID"])])
    pbi.relationship(d, dt.left("Date"), sil.right("InvoiceDate"),
                     [(347, dt.rows["Date"]), (347, sil.rows["InvoiceDate"])])
    pbi.relationship(d, dt.right("Date"), gl.left("PostingDate"),
                     [(515, dt.rows["Date"]), (515, gl.rows["PostingDate"])])
    pbi.relationship(d, acct.left("AccountID"), gl.right("AccountID"),
                     [(716, acct.rows["AccountID"]), (716, gl.rows["AccountID"])])
    pbi.relationship(d, cc.left("CostCenterID"), gl.right("CostCenterID"),
                     [(704, cc.rows["CostCenterID"]), (704, gl.rows["CostCenterID"])])
    y = max(sil.y + sil.h, dt.y + dt.h) + 16
    d.text("<b>1</b>&nbsp;the table that holds the key &nbsp;&nbsp;<b>*</b>&nbsp;the table that refers to it"
           " &nbsp;&nbsp;<b>Arrow</b>&nbsp;the direction of the filter, from each dimension to the fact table",
           0, y, 860, 22, size=SMALL)
    d.text("<i>The model after Tutorial 14.3: the sales star on the left, the ledger star on the right, and "
           "the Date table related to both. The Measures table, which has no relationships, is not shown.</i>",
           0, y + 26, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-14-09 --------------------------------------------------------------------------------

NET_INCOME = {2024: 5110308.27, 2025: 5134354.71, 2026: 4503611.24}


def fig_14_09() -> Diagram:
    d = Diagram("The Income Statement With and Without the Closing Entries")
    for y in YEARS:
        assert abs(pnl_total(y, "all")) < 0.005, y
        assert abs(pnl_total(y, "open") - NET_INCOME[y]) < 0.005, y
        # The second close of each year moves net income from Income Summary to Retained Earnings.
        moved = one("SELECT MAX(g.Debit) FROM GLEntry g JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
                    f"WHERE {CLOSE} AND g.FiscalYear = ? AND (SELECT COUNT(*) FROM GLEntry x "
                    "WHERE x.VoucherNumber = j.EntryNumber) = 2", y)[0]
        assert abs(moved - NET_INCOME[y]) < 0.005, (y, moved)
    widths = [92, 104, 104, 104]
    for x, kind, title in [(0, "all", "Net Income with Closes by AccountType and Year"),
                           (440, "open", "P&L Amount by AccountType and Year")]:
        rows = []
        for typ in ["Expense", "Revenue"]:
            rows.append((0, typ, [pbi.amount(abs(v) if abs(v) < 0.005 else v)
                                  for v in (pnl_total(y, kind, typ) for y in YEARS)], ""))
        rows.append((0, "Total", [pbi.amount(abs(v) if abs(v) < 0.005 else v)
                                  for v in (pnl_total(y, kind) for y in YEARS)], ""))
        pbi.matrix_visual(d, x, 0, ["AccountType", "2024", "2025", "2026"], widths, rows, title=title)
        xl.emphasis(d, x + 6, 26 + pbi.ROW * 3, sum(widths), pbi.ROW)
    d.text("<b>All postings, closing entries included</b>", 0, 150, 420, 22, size=SMALL, color=CORAL)
    d.text("<b>Closing entries excluded (IsYearEndClose = FALSE)</b>", 440, 150, 420, 22, size=SMALL, color=TEAL)
    d.text("<i>Both matrices show credits less debits on the revenue and expense accounts. On the left the "
           "closing entries of December 31 reverse each year's balances, so every total is zero. On the right "
           "each total, outlined, is the year's net income, the amount its closing entry moved to retained "
           "earnings.</i>", 0, 180, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-14-10 --------------------------------------------------------------------------------

def fig_14_10() -> Diagram:
    d = Diagram("The Income Statement by Year")
    subtypes = {}
    for typ in ["Expense", "Revenue"]:
        subtypes[typ] = sorted({s for (y, t, s, k), v in pnl().items()
                                if t == typ and k == "open" and y in YEARS and abs(v) >= 0.005})
    assert subtypes == {"Expense": ["COGS", "Operating Expense", "Other Expense"],
                        "Revenue": ["Contra Revenue", "Operating Revenue", "Other Income or Expense"]}, subtypes

    def cells(typ=None, sub=None) -> list[str]:
        values = [pnl_total(y, "open", typ, sub) for y in YEARS]
        return [pbi.amount(v) if abs(v) >= 0.005 else "" for v in values] + [pbi.amount(sum(values))]

    rows = []
    for typ in ["Expense", "Revenue"]:
        rows.append((0, typ, cells(typ), "-"))
        for sub in subtypes[typ]:
            rows.append((1, sub, cells(typ, sub), ""))
    rows.append((0, "Total", cells(), ""))
    widths = [224, 128, 128, 128, 136]
    my = 104
    height = my + 30 + pbi.ROW * (len(rows) + 1) + 12 + 16
    pbi.canvas(d, 0, 0, 860, height)
    pbi.frame(d, 16, 16, 240, 76, None)
    pbi.card(d, 20, 20, 232, 68, "Net Income", pbi.amount(NET_INCOME[2026]))
    d.text("<i>Filters on this visual: Year is 2026</i>", 270, 40, 300, 22, size=SMALL, color=GRAY)
    pbi.matrix_visual(d, 16, my, ["AccountType", "2024", "2025", "2026", "Total"], widths, rows,
                      title="P&L Amount by AccountType, AccountSubType, and Year")
    total_y = my + 26 + pbi.ROW * len(rows)
    xl.emphasis(d, 22, total_y, sum(widths), pbi.ROW)
    pbi.page_tabs(d, 4, height + 4, ["Sales and Discounts", "Validation", "Review", "Margins",
                                     "Income Statement"], "Income Statement")
    d.text("<i>Credit-positive: revenue reads positive and expenses negative, so the total row, outlined, is "
           "each year's net income, and the 2026 total equals the card. Other Income or Expense is a revenue "
           "subtype in the chart of accounts; its balances are net charges. The matrix is filtered to fiscal "
           "2024 to 2026.</i>", 0, height + 36, 860, 56, size=SMALL, color=GRAY)
    return d


# -- fig-14-11 --------------------------------------------------------------------------------

def fig_14_11() -> Diagram:
    d = Diagram("Monthly Operating Expense Against the Average of the Three Months Before")
    rows = q("SELECT substr(g.PostingDate, 1, 7), SUM(g.Debit - g.Credit) FROM GLEntry g "
             "JOIN Account a ON a.AccountID = g.AccountID "
             "LEFT JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
             f"WHERE a.AccountSubType = 'Operating Expense' AND NOT COALESCE({CLOSE}, 0) "
             "AND g.PostingDate BETWEEN '2024-01-01' AND '2026-12-31' GROUP BY 1 ORDER BY 1")
    months = [m for m, _ in rows]
    opex = [v for _, v in rows]
    assert len(months) == 36 and months[0] == "2024-01"
    expected = [None] + [sum(opex[max(0, i - 3):i]) / len(opex[max(0, i - 3):i]) for i in range(1, 36)]
    deviation = {m: (v - e) / e for m, v, e in zip(months, opex, expected) if e}
    spikes = {m for m, dv in deviation.items() if dv > 0.2}
    three_pay = {m for (m,) in q("SELECT substr(PayDate, 1, 7) FROM PayrollPeriod "
                                 "WHERE PayDate <= '2026-12-31' GROUP BY 1 HAVING COUNT(DISTINCT PayDate) = 3")}
    assert spikes == three_pay | {"2024-02"}, (spikes, three_pay)
    assert all(-0.11 < dv < 0.02 for m, dv in deviation.items() if m not in spikes), "the rest stay close"
    peak = max(opex)
    chart = pbi.line_chart(d, 0, 0, 860, 360, "Operating Expense and Expected Operating Expense by YearMonth",
                           months, [("Operating Expense", opex, BLUE), ("Expected Operating Expense", expected,
                                                                         AMBER)],
                           "K", pbi.nice_ticks(0, peak, 4), every=3, legend=True)
    for i, m in enumerate(months):
        if m in spikes:
            px, py = chart["xs"][i], chart["y_of"](opex[i])
            d.outline(px - 8, py - 8, 16, 16, CORAL, width=2.5, front=True)
    d.text("<i>The expectation is blank for January 2024, which has no earlier month, so its line starts in "
           "February. Outlined: the months whose expense exceeds the expectation by more than a fifth, "
           "February and March 2024 at the start-up and every later month with three pay dates. The value "
           "axis starts at zero.</i>", 0, 372, 860, 56, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-14-01-star": fig_14_01,
    "fig-14-02-date-table": fig_14_02,
    "fig-14-03-filter-context": fig_14_03,
    "fig-14-04-context-transition": fig_14_04,
    "fig-14-05-calculate": fig_14_05,
    "fig-14-06-dax-query-view": fig_14_06,
    "fig-14-07-margin-matrix": fig_14_07,
    "fig-14-08-two-stars": fig_14_08,
    "fig-14-09-closes-trap": fig_14_09,
    "fig-14-10-income-statement": fig_14_10,
    "fig-14-11-expense-expectation": fig_14_11,
}
