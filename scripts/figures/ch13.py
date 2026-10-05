"""Chapter 13 figures (Power BI essentials).

Every value in the mocks is computed here from the dataset with the logic of the tutorials:
the four tables of Tutorial 13.1 (Item filtered to the items with a list price) and the custom
columns of tbl-13-03, ListAmount = Quantity * BaseListPrice and DiscountAmount = Quantity *
UnitPrice * Discount, left unrounded.
"""

from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

import excel as xl
import powerbi as pbi
from data import one, q, require_columns
from data import connection
from shared.calculations import bi_ch13 as public_calculations
from drawio import (AMBER, BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc)

GROUPS = ["Accessories", "Furniture", "Lighting", "Services", "Textiles"]
MONTHS_2026 = public_calculations.MONTHS_2026
QUARTERS_2026 = [f"2026-Q{n}" for n in range(1, 5)]


@lru_cache(maxsize=1)
def lines() -> list[dict]:
    return public_calculations.lines(connection())


def total(field: str, **match) -> float:
    return public_calculations.total(connection() ,field, **match)


def count(**match) -> int:
    return public_calculations.count(connection() ,**match)


def monthly(field: str, year: int = 2026, **match) -> list[float]:
    return public_calculations.monthly(connection() ,field, year, **match)


def short(month: str) -> str:
    return month   # Month is the text column of tbl-13-03, such as 2026-09


# -- fig-13-01 --------------------------------------------------------------------------------

def fig_13_01() -> Diagram:
    d = Diagram("From the Data to a Published Report")
    steps = [
        ("CharlesRiver.xlsx", "The source: one Excel Table for each Charles River table, never changed"),
        ("Power Query", "Load the Tables, keep and filter, set types, add custom columns"),
        ("Semantic model", "Tables, the relationships between them, and measures"),
        ("Report", "Pages of interactive visuals: cards, charts, matrices, slicers"),
        ("Power BI service", "Publish and share in a browser; pin visuals to dashboards"),
    ]
    chapters = ["", "Chapters 13 to 16, as in Chapters 4 and 5", "Chapters 13 to 16, in depth in Chapter 14",
                "Chapters 13 to 16, as a package in Chapter 15", "Optional: needs a license"]
    w, gap, x0, y0, h = 150, 22, 11, 60, 116
    xs = [x0 + i * (w + gap) for i in range(len(steps))]
    # Bands that show where each step happens.
    d.box("", xs[1] - 8, y0 - 36, xs[3] + w - xs[1] + 16, h + 52, fill=BLUE_TINT, stroke=BLUE_TINT)
    d.text("<b>Power BI Desktop</b>", xs[1], y0 - 32, 3 * w + 2 * gap, 22, size=SMALL, align="center")
    d.box("", xs[4] - 8, y0 - 36, w + 16, h + 52, fill=TEAL_TINT, stroke=TEAL_TINT)
    d.text("<b>In a browser</b>", xs[4], y0 - 32, w, 22, size=SMALL, align="center")
    ids = []
    for i, ((name, detail), x) in enumerate(zip(steps, xs)):
        fill = GRAY if i == 0 else TEAL if i == 4 else BLUE
        ids.append(d.box("", x, y0, w, h, fill=WHITE, stroke=fill, stroke_width=2))
        d.header_box(esc(name), x, y0, w, 30, fill=fill, size=SMALL)
        d.text(esc(detail), x + 6, y0 + 36, w - 12, h - 40, size=SMALL)
        if chapters[i]:
            d.text(f"<i>{esc(chapters[i])}</i>", x, y0 + h + 22, w, 36, size=SMALL, color=GRAY,
                   align="center")
    for a, b in zip(ids, ids[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5))
    d.text("<i>Each box is a step of the work; the italic notes name the chapters of Part IV that "
           "cover it. Every tutorial works in Desktop. Refresh repeats the Power Query steps against the "
           "source.</i>", 0, y0 + h + 66,
           860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-13-02 --------------------------------------------------------------------------------

def fig_13_02() -> Diagram:
    d = Diagram("The Power BI Desktop Window")
    pane_w = 130
    win = pbi.window(d, 500, panes=["Filters", "Visualizations", "Data"], pane_w=pane_w)
    cx, cw = win.canvas_x, win.canvas_w
    pbi.canvas(d, cx, win.top, cw, win.bottom - win.top - 30)
    pbi.page_tabs(d, cx + 4, win.bottom - 28, ["Sales and Discounts", "Validation"],
                  "Sales and Discounts")
    # Two visuals on the page: a card and a column chart of fiscal 2026 revenue by item group.
    revenue = {g: total("rev", fy=2026, grp=g) for g in GROUPS}
    grand = sum(revenue.values())
    assert abs(grand - total("rev", fy=2026)) < 0.005
    pbi.frame(d, cx + 18, win.top + 18, 170, 70, None)
    pbi.card(d, cx + 22, win.top + 22, 162, 62, "Revenue", pbi.units(grand, "M"))
    order = sorted(GROUPS, key=revenue.get, reverse=True)
    pbi.bar_chart(d, cx + 18, win.top + 100, cw - 36, 240, "Revenue by item group, fiscal 2026",
                  order, [revenue[g] for g in order], "M", pbi.nice_ticks(0, max(revenue.values()), 4),
                  label_w=88)
    # Filters pane.
    fx = win.panes_x
    for i, label in enumerate(["Filters on this visual", "Filters on this page", "Filters on all pages"]):
        y = win.top + 34 + i * 92
        d.text(f"<b>{esc(label)}</b>", fx + 6, y, pane_w - 12, 36, size=SMALL)
        d.box("<i>Add data fields here</i>", fx + 6, y + 38, pane_w - 12, 40, fill=WHITE, stroke=RULE,
              color=GRAY, size=SMALL, dashed=True)
    # Visualizations pane: three tabs, the gallery, and the wells of the selected chart.
    vx = fx + pane_w
    for i, label in enumerate(["Build visual", "Format visual", "Analytics"]):
        on = i == 0
        d.box(f"<b>{label}</b>" if on else label, vx + 4, win.top + 30 + i * 24, pane_w - 8, 22,
              fill=WHITE, stroke=BLUE if on else RULE, color=BLUE if on else INK, size=SMALL,
              align="left", rounded=False)
    d.text("<i>Visual types</i>", vx + 6, win.top + 104, pane_w - 12, 20, size=SMALL, color=GRAY)
    for r in range(3):
        for c in range(5):
            d.box("", vx + 8 + c * 23, win.top + 126 + r * 22, 18, 18, fill=GRAY_TINT, stroke=RULE,
                  rounded=False)
    for i, (well, value) in enumerate([("Y-axis", "ItemGroup"), ("X-axis", "Sum of LineTotal")]):
        y = win.top + 200 + i * 60
        d.text(f"<b>{well}</b>", vx + 6, y, pane_w - 12, 20, size=SMALL)
        d.box(esc(value), vx + 6, y + 22, pane_w - 12, 26, fill=BLUE_TINT, stroke=RULE, size=SMALL,
              align="left", rounded=False)
    # Data pane: the four tables, one of them expanded.
    dx = vx + pane_w
    # Numeric columns carry the summation sign; the pane lists columns alphabetically.
    entries = [("▸ Customer", 0), ("▸ Item", 0), ("▸ SalesInvoice", 0), ("▾ SalesInvoiceLine", 0),
               ("Σ Discount", 1), ("Σ DiscountAmount", 1), ("Σ ItemID", 1), ("Σ LineTotal", 1),
               ("Σ ListAmount", 1), ("PricingMethod", 1)]
    for i, (label, level) in enumerate(entries):
        d.text(("&nbsp;" * 2 * level) + esc(label), dx + 4, win.top + 34 + i * 24, pane_w - 6, 22,
               size=SMALL)
    # Numbered markers and their legend.
    marks = [(1, 446, 31), (2, 24, win.top + 186), (3, cx + cw / 2 - 12, win.top + 352),
             (4, fx + pane_w / 2 - 12, win.bottom - 36), (5, vx + pane_w / 2 - 12, win.bottom - 36),
             (6, dx + pane_w / 2 - 12, win.bottom - 36)]
    for n, x, y in marks:
        d.marker(str(n), x, y, fill=CORAL)
    legend = ["Ribbon, with the commands of the active tab", "Views: Report, Table, Model, DAX query, TMDL",
              "Canvas: the report page, with its page tabs below", "Filters pane",
              "Visualizations pane: visual types and the wells of the selected visual",
              "Data pane: the tables of the model and their columns"]
    ly = win.bottom + 16
    for i, text in enumerate(legend):
        col, row = divmod(i, 3)
        x, y = col * 430, ly + row * 28
        d.marker(str(i + 1), x, y, fill=CORAL)
        d.text(esc(text), x + 30, y + 1, 400, 22, size=SMALL)
    d.text("<i>The real bar of views and the pane tabs show icons; the mock writes their names.</i>",
           0, ly + 88, 860, 22, size=SMALL, color=GRAY)
    return d


# -- fig-13-03 --------------------------------------------------------------------------------

def _profile(sample: int | None) -> dict:
    return public_calculations._profile(connection() ,sample)


def _pct(part: int, whole: int) -> str:
    share = 100 * part / whole
    return "< 1%" if 0 < share < 1 else f"{share:.0f}%"


def fig_13_03() -> Diagram:
    d = Diagram("The Same Column Profiled on the First 1,000 Rows and on the Entire Data Set")
    top, full = _profile(1000), _profile(None)
    assert top["promo_empty"] == 1000 and top["d_distinct"] == 1, top
    assert full["promo_empty"] < full["n"] and full["d_distinct"] == 4, full
    first_dates = one("SELECT MIN(si.InvoiceDate), MAX(si.InvoiceDate) FROM (SELECT * FROM SalesInvoiceLine "
                      "ORDER BY SalesInvoiceLineID LIMIT 1000) l JOIN SalesInvoice si USING (SalesInvoiceID)")
    first_promo = one("SELECT MIN(EffectiveStartDate) FROM PromotionProgram")[0]
    assert first_dates[1] < first_promo, "the first 1,000 lines predate every promotion"
    panels = [(0, "Profiled on the top 1,000 rows", top, "Column profiling based on top 1000 rows"),
              (436, "Profiled on the entire data set", full, "Column profiling based on entire data set")]
    for x, caption, p, status in panels:
        d.text(f"<b>{esc(caption)}</b>", x, 0, 424, 22, size=SMALL)
        xl.title_bar(d, x, 24, 424, "Power Query Editor - SalesInvoiceLine")
        cols = [("Discount", 140), ("PromotionID", 140), ("LineTotal", 144)]
        cx = x
        for name, w in cols:
            d.box(f"<b>{name}</b>", cx, 54, w, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left",
                  rounded=False)
            cx += w
        # Column quality for every column.
        quality = {"Discount": (p["n"], 0, 0), "PromotionID": (p["n"] - p["promo_empty"], 0, p["promo_empty"]),
                   "LineTotal": (p["n"], 0, 0)}
        cx = x
        for name, w in cols:
            valid, error, empty = quality[name]
            for i, (label, value, color) in enumerate([("Valid", valid, TEAL), ("Error", error, CORAL),
                                                       ("Empty", empty, GRAY)]):
                y = 82 + i * 20
                d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={color};", cx + 6, y + 6, 8, 8)
                d.text(f"{label} {_pct(value, p['n'])}", cx + 18, y, w - 22, 20, size=SMALL)
            cx += w
        # Column distribution for Discount: one bar per distinct value, most frequent first.
        counts = [r[1] for r in q(
            "SELECT Discount, COUNT(*) FROM {} GROUP BY Discount ORDER BY 2 DESC".format(
                "(SELECT * FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT 1000)"
                if p is top else "SalesInvoiceLine"))]
        peak = max(counts)
        for i, c in enumerate(counts):
            h = max(2, 34 * c / peak)
            d.box("", x + 8 + i * 22, 182 - h, 16, h, fill=BLUE, stroke=BLUE, rounded=False)
        d.text(f"{p['d_distinct']} distinct, {p['d_unique']} unique", x + 4, 186, 136, 20, size=SMALL)
        # The first rows of the preview.
        for r, (disc, promo, lt) in enumerate(p["first"]):
            y = 212 + r * 22
            cx = x
            for (name, w), value in zip(cols, [f"{disc:g}", "null" if promo is None else str(promo),
                                               f"{lt:,.2f}"]):
                d.box(f"<i>{value}</i>" if value == "null" else esc(value), cx, y, w, 22, fill=WHITE,
                      stroke=RULE, color=GRAY if value == "null" else INK, size=SMALL,
                      align="left" if value == "null" else "right", rounded=False)
                cx += w
        xl.status_bar(d, x, 302, 424, status)
        xl.emphasis(d, x, 302, 300, 24)
    d.text("<i>The first 1,000 invoice lines are the lines of January and February 2024, billed before "
           "Charles River's first promotion. Column distribution is shown for Discount only; the editor "
           "draws it under every column.</i>", 0, 338, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-13-04 --------------------------------------------------------------------------------

def _one_to_many(parent: str, pk: str, child: str, fk: str) -> None:
    """Assert what Model view would draw: the key is unique on the one side and every
    foreign key value finds it."""
    n, distinct = one(f"SELECT COUNT(*), COUNT(DISTINCT {pk}) FROM {parent}")
    assert n == distinct, f"{parent}.{pk} is not unique"
    orphans = one(f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p ON p.{pk} = c.{fk} "
                  f"WHERE c.{fk} IS NOT NULL AND p.{pk} IS NULL")[0]
    assert orphans == 0, f"{child}.{fk} has {orphans} orphans"


def fig_13_04() -> Diagram:
    d = Diagram("The Sales Tables in Model View")
    _one_to_many("Item", "ItemID", "SalesInvoiceLine", "ItemID")
    _one_to_many("SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID")
    _one_to_many("Customer", "CustomerID", "SalesInvoice", "CustomerID")
    item = pbi.model_table(d, "Item", 0, 66, ["ItemID", "ItemCode", "ItemName", "ItemGroup",
                                             "ListPrice", "ProductType", "StandardCost"], w=150)
    sil = pbi.model_table(d, "SalesInvoiceLine", 222, 0, [
        "BaseListPrice", "Discount", "DiscountAmount", "ItemID", "LineTotal", "ListAmount",
        "PricingMethod", "PromotionID", "Quantity", "SalesInvoiceID", "SalesInvoiceLineID",
        "UnitPrice"], w=170)
    si = pbi.model_table(d, "SalesInvoice", 464, 44, ["CustomerID", "FiscalQuarter", "FiscalYear",
                                                     "InvoiceDate", "InvoiceNumber", "Month",
                                                     "Period", "SalesInvoiceID"], w=160)
    cust = pbi.model_table(d, "Customer", 700, 44, ["CustomerID", "CustomerName",
                                                   "CustomerSegment", "Region"], w=160)
    pbi.relationship(d, item.right("ItemID"), sil.left("ItemID"))
    pbi.relationship(d, si.left("SalesInvoiceID"), sil.right("SalesInvoiceID"))
    pbi.relationship(d, cust.left("CustomerID"), si.right("CustomerID"))
    y = sil.y + sil.h + 16
    d.text("<b>1</b>&nbsp;the table that holds the key &nbsp;&nbsp;<b>*</b>&nbsp;the table that refers to it"
           " &nbsp;&nbsp;<b>Arrow</b>&nbsp;the direction in which a filter flows", 0, y, 860, 22, size=SMALL)
    d.text("<i>Model view lists each table's columns in alphabetical order and draws the relationship "
           "between the tables; the mock draws each line to the related columns so that they can be "
           "read. Power BI's 1 and * replace the crow's feet of Chapter 3.</i>", 0, y + 26, 860, 40,
           size=SMALL, color=GRAY)
    return d


# -- fig-13-05 --------------------------------------------------------------------------------

def fig_13_05() -> Diagram:
    d = Diagram("The Validation Page of the Charles River Reports File")
    years = [2024, 2025, 2026]
    rows = []
    for y in years:
        rows.append([str(y), f"{count(fy=y):,}", pbi.amount(total("rev", fy=y)),
                     pbi.amount(total("list", fy=y)), pbi.amount(total("disc", fy=y))])
    # Chapter 6's control totals for fiscal 2026 and the Part II case's gross to net.
    assert rows[2][1:] == ["9,522", "29,756,420.08", "33,589,137.45", "362,110.75"], rows[2]
    totals = ["Total", f"{len(lines()):,}", pbi.amount(total("rev")), pbi.amount(total("list")),
              pbi.amount(total("disc"))]
    pbi.canvas(d, 0, 0, 860, 352)
    t1 = pbi.table_visual(d, 20, 20, ["FiscalYear", "Count of SalesInvoiceLineID", "Sum of LineTotal",
                                       "Sum of ListAmount", "Sum of DiscountAmount"],
                          [86, 190, 150, 150, 168], rows, total=totals)
    x0, y0, w0, _ = t1["geometry"][(2, 0)]
    xl.emphasis(d, x0, y0, sum([86, 190, 150, 150, 168]), pbi.ROW)
    groups = [[g, pbi.amount(total("rev", grp=g))] for g in GROUPS]
    assert len(groups) == len({r["grp"] for r in lines()}), "no (Blank) item group"
    pbi.table_visual(d, 20, t1["bottom"] + 16, ["ItemGroup", "Sum of LineTotal"], [140, 150], groups,
                     total=["Total", pbi.amount(total("rev"))])
    pbi.page_tabs(d, 4, 356, ["Validation"], "Validation")
    d.text("<i>Outlined: the fiscal 2026 row, which matches the invoice line count and line total of "
           "Chapter 6. The item group table lists all years and has no (Blank) row.</i>", 0, 388, 860, 40,
           size=SMALL, color=GRAY)
    return d


# -- fig-13-06 --------------------------------------------------------------------------------

def fig_13_06() -> Diagram:
    d = Diagram("The Sales and Discounts Page")
    y26 = dict(fy=2026)
    pbi.canvas(d, 0, 0, 860, 792)
    x0, y = 16, 16
    right = pbi.slicer_tiles(d, x0, y, "FiscalYear", ["2024", "2025", "2026"], "2026", tile_w=56)
    right = pbi.slicer_dropdown(d, right + 12, y, 170, "CustomerSegment", "All")
    pbi.slicer_dropdown(d, right + 12, y, 150, "Region", "All")
    # Cards.
    invoices = len({r["inv"] for r in lines() if r["fy"] == 2026})
    assert invoices == one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate LIKE '2026%'")[0]
    cards = [("Revenue", pbi.amount(total("rev", **y26))), ("At list price", pbi.amount(total("list", **y26))),
             ("Discounts", pbi.amount(total("disc", **y26))), ("Invoices", f"{invoices:,}")]
    y = 84
    pbi.frame(d, x0, y, 828, 76, None)
    for i, (label, value) in enumerate(cards):
        pbi.card(d, x0 + 6 + i * 205, y + 6, 198, 64, label, value)
    # Line chart of discounts by month and bar chart by item group.
    y = 172
    disc = monthly("disc")
    peak = max(disc)
    assert disc.index(peak) == 9 and disc[8] > 10 * disc[7], "the autumn promotion months stand out"
    pbi.line_chart(d, x0, y, 430, 230, "Promotional discounts by month", MONTHS_2026,
                   [("Discounts", disc, BLUE)], "K", pbi.nice_ticks(0, peak, 3), every=3)
    by_group = {g: total("disc", fy=2026, grp=g) for g in GROUPS}
    order = sorted(GROUPS, key=by_group.get, reverse=True)
    assert order[0] == "Furniture" and by_group["Furniture"] > 0.9 * sum(by_group.values())
    pbi.bar_chart(d, x0 + 442, y, 386, 230, "Promotional discounts by item group", order,
                  [by_group[g] for g in order], "K", pbi.nice_ticks(0, max(by_group.values()), 4),
                  label_w=86)
    # Matrix of revenue by item group and product type by quarter, Furniture expanded.
    y = 414
    rows = []
    for g in GROUPS:
        values = [pbi.amount(total("rev", fy=2026, grp=g, period=p)) for p in QUARTERS_2026]
        values.append(pbi.amount(total("rev", fy=2026, grp=g)))
        rows.append((0, g, values, "-" if g == "Furniture" else "+"))
        if g == "Furniture":
            for pt in sorted({r["pt"] for r in lines() if r["grp"] == "Furniture"}):
                pv = [pbi.amount(total("rev", fy=2026, grp=g, pt=pt, period=p)) for p in QUARTERS_2026]
                pv.append(pbi.amount(total("rev", fy=2026, grp=g, pt=pt)))
                rows.append((1, pt, pv, ""))
    rows.append((0, "Total", [pbi.amount(total("rev", fy=2026, period=p)) for p in QUARTERS_2026]
                 + [pbi.amount(total("rev", **y26))], ""))
    pbi.matrix_visual(d, x0, y, ["ItemGroup", *QUARTERS_2026, "Total"], [190, 118, 118, 118, 118, 128],
                      rows, title="Revenue by item group and quarter")
    pbi.page_tabs(d, 4, 796, ["Sales and Discounts", "Validation"], "Sales and Discounts")
    return d


# -- fig-13-07 --------------------------------------------------------------------------------

def fig_13_07() -> Diagram:
    d = Diagram("The Same Revenue in Four Visual Encodings")
    rev = {g: total("rev", fy=2026, grp=g) for g in GROUPS}
    grand = sum(rev.values())
    order = sorted(GROUPS, key=rev.get, reverse=True)
    colors = dict(zip(order, [BLUE, TEAL, AMBER, CORAL, GRAY]))
    panel_w, panel_h = 420, 300
    spots = [(0, 0), (440, 0), (0, 320), (440, 320)]
    titles = ["1. Position on a common scale: bars", "2. Length without a common baseline: one stacked bar",
              "3. Angle: a pie", "4. Area: circles"]
    for (x, y), title in zip(spots, titles):
        d.box("", x, y, panel_w, panel_h, fill=WHITE, stroke=RULE, rounded=False)
        d.text(f"<b>{esc(title)}</b>", x + 8, y + 6, panel_w - 16, 22, size=SMALL)
    # 1. Bars sharing a baseline.
    x, y = spots[0]
    peak = max(rev.values())
    for i, g in enumerate(order):
        by = y + 44 + i * 48
        d.text(esc(g), x + 8, by + 4, 92, 22, size=SMALL, align="right")
        d.box("", x + 106, by, 280 * rev[g] / peak, 28, fill=colors[g], stroke=colors[g], rounded=False)
    # 2. One stacked bar: each segment starts where the previous one ends.
    x, y = spots[1]
    sx = x + 20
    for g in order:
        w = 380 * rev[g] / grand
        d.box("", sx, y + 80, w, 60, fill=colors[g], stroke=WHITE, rounded=False)
        sx += w
    for i, g in enumerate(order):
        lx = x + 20 + (i % 3) * 132
        ly = y + 170 + (i // 3) * 28
        d.box("", lx, ly + 4, 14, 14, fill=colors[g], stroke=colors[g], rounded=False)
        d.text(esc(g), lx + 18, ly, 110, 22, size=SMALL)
    # 3. A pie, its slices labeled.
    x, y = spots[2]
    start = 0.0
    cx, cy, r = x + 150, y + 165, 110
    for g in order:
        share = rev[g] / grand
        d.vertex("", f"shape=mxgraph.basic.pie;html=1;startAngle={start:.4f};endAngle={start + share:.4f};"
                     f"fillColor={colors[g]};strokeColor={WHITE};", cx - r, cy - r, 2 * r, 2 * r)
        start += share
    for i, g in enumerate(order):
        d.box("", x + 290, y + 70 + i * 32, 14, 14, fill=colors[g], stroke=colors[g], rounded=False)
        d.text(esc(g), x + 308, y + 66 + i * 32, 104, 22, size=SMALL)
    # 4. Circles with areas proportional to revenue.
    x, y = spots[3]
    biggest = 120
    cx = x + 14
    for i, g in enumerate(order):
        diameter = biggest * (rev[g] / peak) ** 0.5
        d.vertex("", f"ellipse;html=1;fillColor={colors[g]};strokeColor={colors[g]};",
                 cx, y + 170 - diameter / 2, diameter, diameter)
        d.text(esc(g), cx + diameter / 2 - 45, y + 238 + (i % 2) * 24, 90, 22, size=SMALL, align="center")
        cx += diameter + 14
    d.text("<i>Fiscal 2026 revenue of the five item groups. Readers judge the bars most accurately, then "
           "the stacked lengths, then the angles, and the areas least accurately (Cleveland and McGill, "
           "1984).</i>", 0, 628, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-13-08 --------------------------------------------------------------------------------

def fig_13_08() -> Diagram:
    d = Diagram("The Same Monthly Revenue on Two Value Axes")
    rev = monthly("rev")
    low, high = min(rev), max(rev)
    assert (high - low) / (sum(rev) / 12) < 0.25, "a narrow band"
    auto = pbi.nice_ticks(low, high, 4)
    assert auto[0] > 0 and auto[0] <= low
    zero = pbi.nice_ticks(0, high, 5)
    top = pbi.line_chart(d, 0, 0, 860, 300, "Sum of LineTotal by Month", MONTHS_2026,
                         [("Revenue", rev, BLUE)], "M", auto, every=1)
    tx, ty, tw, th = top["axis_box"]
    xl.emphasis(d, tx, ty + th - 22, 46, 22)
    bottom = pbi.line_chart(d, 0, 320, 860, 300, "Monthly revenue, fiscal 2026", MONTHS_2026,
                            [("Revenue", rev, BLUE)], "M", zero, every=1)
    bx, by, bw, bh = bottom["axis_box"]
    xl.emphasis(d, bx, by + bh - 22, 46, 22)
    d.text("<i>Above, the default axis starts just below the weakest month. Below, the axis starts at zero "
           "(Format visual > Y-axis > Range > Minimum). Outlined: the lowest value on each axis.</i>",
           0, 636, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-13-09 --------------------------------------------------------------------------------

def fig_13_09() -> Diagram:
    d = Diagram("Revenue and Discounts on Two Axes and Corrected")
    rev, disc = monthly("rev"), monthly("disc")
    assert max(disc) < 0.1 * min(rev), "the ranges barely overlap, so the line gets its own axis"
    combo = pbi.combo_chart(d, 0, 0, 860, 290, "Revenue and discounts by month (draft)", MONTHS_2026,
                            ("Sum of LineTotal", rev), ("Sum of DiscountAmount", disc), "M",
                            pbi.nice_ticks(0, max(rev), 5), "K", pbi.nice_ticks(0, max(disc), 3), every=1)
    xl.emphasis(d, *combo["right_axis"])
    shared = pbi.nice_ticks(0, max(rev), 5)
    pbi.line_chart(d, 0, 306, 860, 280, "Revenue and promotional discounts by month, fiscal 2026",
                   MONTHS_2026, [("Revenue", rev, BLUE), ("Discounts", disc, AMBER)], "M", shared,
                   legend=True)
    pbi.line_chart(d, 0, 600, 860, 250, "Promotional discounts by month, fiscal 2026", MONTHS_2026,
                   [("Discounts", disc, AMBER)], "K", pbi.nice_ticks(0, max(disc), 3))
    d.text("<i>Top: the draft, with discounts on a second axis on the right (outlined). Middle: both series "
           "on one axis. Bottom: the discounts on their own axis, in a separate chart. The revenue columns "
           "and the revenue line are blue; the discounts are amber, with diamond markers in the draft.</i>",
           0, 864, 860, 40, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-13-01-power-bi-workflow": fig_13_01,
    "fig-13-02-desktop-window": fig_13_02,
    "fig-13-03-column-profile": fig_13_03,
    "fig-13-04-model-view": fig_13_04,
    "fig-13-05-validation-page": fig_13_05,
    "fig-13-06-sales-discounts-page": fig_13_06,
    "fig-13-07-encodings": fig_13_07,
    "fig-13-08-value-axis": fig_13_08,
    "fig-13-09-dual-axis": fig_13_09,
}
