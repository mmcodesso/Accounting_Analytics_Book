"""Figures of the appendix on Power BI in the browser.

The mocks follow the Power BI service as it was used for the appendix in October 2026 (Power Query Online's Get
data, the model editor, the report editor, and DAX query view), drawn in the book's figure style. The labels were read
from the service; every value is computed from the dataset with the logic of Chapter 13's tutorials, through the same
helpers as ch13.py, so a rebuild keeps the figures current.
"""

from __future__ import annotations

import datetime as dt

import excel as xl
import powerbi as pbi
from ch13 import MONTHS_2026, lines, monthly, total
from check_figures import text_width
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL, WHITE,
                    Diagram, esc)

PQ_TABS = ["Home", "Transform", "Add column", "View", "Help"]
EDITOR_TABS = ["File", "Home", "Help"]
EDITOR_VIEWS = ["Model view", "DAX query view", "TMDL View (Preview)"]
TABLES = ["Customer", "SalesInvoice", "SalesInvoiceLine", "Item"]
CHOSEN = ["T4_Customer", "T16_SalesInvoice", "T17_SalesInvoiceLine", "T44_Item"]


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


def header(d: Diagram, y: float, crumb: str, right: list[str] | None = None) -> float:
    """The service's top bar: Power BI, the item or workspace open, the search box, and buttons on the right."""
    d.box("", 0, y, 860, 32, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.text("<b>Power BI</b>", 8, y + 5, 80, 22, size=SMALL, color=BLUE, valign="middle")
    d.text(esc(crumb), 84, y + 5, 230, 22, size=SMALL, valign="middle")
    d.box("Search", 330, y + 4, 200, 24, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, align="left",
          rounded=True)
    x = 852
    for label in reversed(right or []):
        w = text_width(esc(label), SMALL, False) + 22
        x -= w
        xl.button(d, x, y + 3, w, label, primary=label == "Share")
        x -= 6
    return y + 32


def radio(d: Diagram, x: float, y: float, label: str, on: bool) -> float:
    d.vertex("", f"ellipse;html=1;fillColor={BLUE if on else WHITE};strokeColor={BLUE if on else GRAY};"
                 "strokeWidth=1.5;", x, y + 4, 12, 12)
    w = text_width(esc(label), SMALL, False) + 10
    d.text(esc(label), x + 16, y, w, 20, size=SMALL, valign="middle")
    return x + 16 + w + 12


def views(d: Diagram, y: float, active: str) -> None:
    """The model editor's views, as tabs along the bottom."""
    x = 0
    d.box("", 0, y, 860, 30, fill=GRAY_TINT, stroke=RULE, rounded=False)
    for name in EDITOR_VIEWS:
        on = name == active
        w = text_width(esc(name), SMALL, on) + 24
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), x + 4, y + 3, w, 24, fill=WHITE if on else GRAY_TINT,
              stroke=BLUE if on else GRAY_TINT, stroke_width=2 if on else 1, color=BLUE if on else INK, size=SMALL,
              rounded=False)
        x += w + 6


def serial(date: str) -> int:
    """An Excel date: the count of days that Excel stores and Power Query Online reads as a number."""
    return (dt.date.fromisoformat(date[:10]) - dt.date(1899, 12, 30)).days


def mdy(date: str) -> str:
    return f"{int(date[5:7])}/{int(date[8:10])}/{date[:4]}"


# -- fig-c-01 --------------------------------------------------------------------------------

def text_order(name: str) -> str:
    """The order in which Choose data lists the workbook's items: T1_Account before T10_SalesOrderLine."""
    return name.replace("_", " ").lower()


def fig_c_01() -> Diagram:
    d = Diagram("Uploading the Workbook and Choosing Its Tables")
    tables = sorted(xl.workbook_tables().values(), key=text_order)
    sheets = xl.workbook_sheets()
    assert all(t in tables for t in CHOSEN), CHOSEN
    # Connect to data source, after the upload.
    w, h = 420, 424
    d.box("", 0, 0, w, h, fill=WHITE, stroke=GRAY, stroke_width=2, rounded=False)
    xl.title_bar(d, 0, 0, w, "Power Query")
    d.text("Get data", 14, 34, 200, 20, size=SMALL, color=GRAY)
    d.text("<b>Connect to data source</b>", 14, 52, 300, 24, size=14)
    d.box("<b>X</b>", 14, 86, 28, 28, fill=TEAL, stroke=TEAL, color=WHITE, size=SMALL, rounded=False)
    d.text("<b>Excel workbook</b><br>File", 48, 82, 200, 40, size=SMALL)
    d.text("<b>Connection settings</b>", 14, 128, 300, 22, size=SMALL)
    x = radio(d, 14, 152, "Link to file", False)
    radio(d, x, 152, "Upload file", True)
    d.box("", 14, 180, 392, 52, fill=WHITE, stroke=RULE, rounded=False)
    d.box("<b>X</b>", 24, 192, 28, 28, fill=TEAL, stroke=TEAL, color=WHITE, size=SMALL, rounded=False)
    d.text(f"{esc(xl.XLSX.name)}<br><font color=\"{TEAL}\">✓</font> Upload successful", 60, 184, 320, 44,
           size=SMALL)
    d.text("<b>Connection credentials</b>", 14, 246, 300, 22, size=SMALL)
    d.text("Connection", 14, 270, 200, 20, size=SMALL)
    d.box("https://…-my.sharepoint.com/personal/…", 14, 290, 392, 26, fill=WHITE, stroke=GRAY, size=SMALL,
          align="left", rounded=False)
    d.text("Authentication kind: Organizational account", 14, 324, 280, 20, size=SMALL)
    d.text(f"<u><font color=\"{BLUE}\">Edit connection</font></u>", 300, 324, 110, 20, size=SMALL)
    xl.button(d, 14, 386, 70, "Back")
    xl.button(d, 254, 386, 76, "Cancel")
    xl.button(d, 338, 386, 68, "Next", primary=True)
    # Choose data, with the four Tables checked.
    x0 = 440
    d.box("", x0, 0, w, h, fill=WHITE, stroke=GRAY, stroke_width=2, rounded=False)
    xl.title_bar(d, x0, 0, w, "Power Query")
    d.text("Get data", x0 + 14, 34, 200, 20, size=SMALL, color=GRAY)
    d.text("<b>Choose data</b>", x0 + 14, 52, 300, 24, size=14)
    d.box("Search", x0 + 14, 84, 200, 24, fill=WHITE, stroke=GRAY, color=GRAY, size=SMALL, align="left",
          rounded=False)
    d.text("Display options ▾", x0 + 14, 112, 200, 20, size=SMALL)
    d.text(f"▾ <b>Excel workbook</b>&nbsp;&nbsp;[{len(tables) + len(sheets)}]", x0 + 14, 136, 300, 20, size=SMALL)
    shown: list[str | None] = []
    for t in tables[:3]:
        shown.append(t)
    for t in CHOSEN[1:3] + CHOSEN[:1] + CHOSEN[3:]:
        shown += [None, t]
    y = 160
    for item in shown:
        if item is None:
            d.text("⋮", x0 + 38, y - 2, 20, 20, size=SMALL, color=GRAY)
            y += 16
            continue
        on = item in CHOSEN
        xl.checkbox(d, x0 + 30, y + 4, on)
        xl.item_icon(d, x0 + 52, y + 5, "table")
        d.text(f"<b>{esc(item)}</b>" if on else esc(item), x0 + 74, y, 300, 22, size=SMALL, valign="middle")
        y += 22
    assert y < 380, y
    xl.button(d, x0 + 14, 386, 70, "Back")
    xl.button(d, x0 + 290, 386, 116, "Transform data", primary=True)
    note(d, "Left: Upload file, after the upload; the credentials need no choice. Right: Choose data, which takes the "
            "place of the Navigator, with the four Tables of Tutorial 13.1 checked. Its list is in text order, and "
            "Transform data is the only way on.", h + 10, 56)
    return d


# -- fig-c-02 --------------------------------------------------------------------------------

def fig_c_02() -> Diagram:
    d = Diagram("InvoiceDate as Power Query Online Reads It")
    rows = q("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate, CustomerID FROM SalesInvoice "
             "ORDER BY SalesInvoiceID LIMIT 7")
    xl.title_bar(d, 0, 0, 860, "Power Query")
    top = pbi.ribbon(d, 0, 30, 860, "Home", ["Get data ▾", "Enter data", "Manage parameters ▾", "Refresh ▾",
                                              "Choose columns ▾", "Remove columns ▾", "Merge queries ▾"],
                     tabs=PQ_TABS)
    bottom = top + 300
    # Queries pane.
    d.box("", 0, top, 150, bottom - top, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>Queries [{len(TABLES)}]</b>", 8, top + 6, 140, 22, size=SMALL)
    for i, name in enumerate(TABLES):
        on = name == "SalesInvoice"
        d.box(f"<b>{name}</b>" if on else name, 6, top + 34 + i * 28, 138, 24, fill=BLUE_TINT if on else WHITE,
              stroke=BLUE if on else WHITE, size=SMALL, align="left", rounded=False)
    # Formula bar and grid.
    gx = 160
    d.text("<i>fx</i>", gx, top + 8, 24, 22, size=SMALL, color=GRAY)
    d.box(esc('Table.SelectColumns(#"Changed column type", {"SalesInvoiceID", …})'), gx + 26, top + 6, 450, 26,
          fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    heads = [("123", "SalesInvoiceID"), ("ABC", "InvoiceNumber"), ("123", "InvoiceDate"), ("123", "CustomerID")]
    widths = [126, 140, 112, 104]
    gy = top + 44
    cx = gx
    for (kind, name), wd in zip(heads, widths):
        d.box(f"<font color=\"{GRAY}\">{kind}</font>&nbsp;<b>{esc(name)}</b>", cx, gy, wd, pbi.ROW + 4,
              fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        cx += wd
    for r, (sid, number, date, cust) in enumerate(rows):
        cx = gx
        for c, (value, wd) in enumerate(zip([str(sid), number, str(serial(date)), str(cust)], widths)):
            d.box(esc(value), cx, gy + pbi.ROW + 4 + r * pbi.ROW, wd, pbi.ROW, fill=WHITE, stroke=RULE, size=SMALL,
                  align="left" if c == 1 else "right", rounded=False)
            cx += wd
    date_x = gx + sum(widths[:2])
    xl.emphasis(d, date_x, gy, widths[2], pbi.ROW + 4 + len(rows) * pbi.ROW)
    d.box("Columns: 4&nbsp;&nbsp;&nbsp;Rows: 99+", 150, bottom - 28, 520, 28, fill=GRAY_TINT, stroke=RULE,
          size=SMALL, align="left", rounded=False)
    # Query settings.
    sx = 680
    d.box("", sx, top, 180, bottom - top, fill=WHITE, stroke=RULE, rounded=False)
    d.text("<b>Query settings</b>", sx + 8, top + 6, 170, 22, size=SMALL)
    d.text("Name", sx + 8, top + 32, 170, 20, size=SMALL, color=GRAY)
    d.box("SalesInvoice", sx + 8, top + 52, 164, 24, fill=WHITE, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    d.text("<b>Applied steps</b>", sx + 8, top + 88, 170, 22, size=SMALL)
    steps = ["Source", "Navigation 1", "Changed column type", "Choose columns"]
    for i, step in enumerate(steps):
        on = step == steps[-1]
        d.box(f"<b>{step}</b>" if on else step, sx + 8, top + 114 + i * 28, 164, 24, fill=BLUE_TINT if on else WHITE,
              stroke=BLUE if on else RULE, size=SMALL, align="left", rounded=False)
    # The same rows after the type is set to Date.
    y = bottom + 14
    d.text("<b>After Date is chosen on InvoiceDate's header</b> (a step named Changed column type 1):", 0, y, 860,
           22, size=SMALL)
    pbi.table_visual(d, 0, y + 26, ["SalesInvoiceID", "InvoiceDate"], [126, 112],
                     [[str(r[0]), mdy(r[2])] for r in rows[:3]])
    note(d, "Outlined: InvoiceDate, which the workbook stores as an Excel date. Power Query Online reads the number "
            "and types the column as a whole number; Power BI Desktop reads the same cells as dates. The real "
            "headers show type icons; the mock writes 123 and ABC.", y + 140, 56)
    return d


# -- fig-c-03 --------------------------------------------------------------------------------

def fig_c_03() -> Diagram:
    d = Diagram("The Model Editor After Steps 9 and 10")
    for parent, pk, child, fk in [("Item", "ItemID", "SalesInvoiceLine", "ItemID"),
                                  ("SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID"),
                                  ("Customer", "CustomerID", "SalesInvoice", "CustomerID")]:
        n, distinct = one(f"SELECT COUNT(*), COUNT(DISTINCT {pk}) FROM {parent}")
        assert n == distinct, f"{parent}.{pk} is not unique"
    y = header(d, 0, "Charles River Reports", ["Editing ▾", "Share"])
    top = pbi.ribbon(d, 0, y + 2, 860, "Home", ["Get data", "Transform data", "Refresh", "New measure",
                                                 "New table", "New parameter ▾", "Manage relationships",
                                                 "New report"], tabs=EDITOR_TABS)
    bottom = top + 424
    d.box("", 0, top, 570, bottom - top, fill=GRAY_TINT, stroke=RULE, rounded=False)
    # Rows line up so that each relationship is drawn level: ItemID is Item's third column and SalesInvoiceLine's
    # fourth, and SalesInvoiceID is SalesInvoice's eighth and SalesInvoiceLine's tenth.
    sil_y = top + 12
    item = pbi.model_table(d, "Item", 10, sil_y + pbi.ROW, ["ItemCode", "ItemGroup", "ItemID", "ItemName",
                                                           "ListPrice", "ProductType", "StandardCost"], w=124)
    sil = pbi.model_table(d, "SalesInvoiceLine", 196, sil_y, [
        "BaseListPrice", "Discount", "DiscountAmount", "ItemID", "LineTotal", "ListAmount", "PricingMethod",
        "PromotionID", "Quantity", "SalesInvoiceID", "SalesInvoiceLineID", "UnitPrice"], w=148)
    si = pbi.model_table(d, "SalesInvoice", 392, sil_y + 2 * pbi.ROW, ["CustomerID", "FiscalQuarter", "FiscalYear",
                                                                        "InvoiceDate", "InvoiceNumber", "Month",
                                                                        "Period", "SalesInvoiceID"], w=124,
                         marked=("FiscalYear",))
    cust = pbi.model_table(d, "Customer", 392, si.y + si.h + 24, ["CustomerID", "CustomerName", "CustomerSegment",
                                                                   "Region"], w=124)
    assert item.rows["ItemID"] == sil.rows["ItemID"] and si.rows["SalesInvoiceID"] == sil.rows["SalesInvoiceID"]
    assert cust.y + cust.h < bottom - 6, (cust.y + cust.h, bottom)
    pbi.relationship(d, item.right("ItemID"), sil.left("ItemID"))
    pbi.relationship(d, si.left("SalesInvoiceID"), sil.right("SalesInvoiceID"))
    pbi.relationship(d, cust.right("CustomerID"), si.right("CustomerID"),
                     [(548, cust.rows["CustomerID"]), (548, si.rows["CustomerID"])])
    # Properties pane of the selected column.
    px = 578
    d.box("", px, top, 860 - px, bottom - top, fill=WHITE, stroke=RULE, rounded=False)
    d.text("<b>Properties</b>", px + 8, top + 6, 240, 22, size=SMALL)
    entries = [("General", None), ("Name", "FiscalYear"), ("Formatting", None), ("Data type", "Whole number"),
               ("Thousands separator", "No"), ("Advanced", None), ("Sort by column", "FiscalYear (Default)"),
               ("Data category", "Uncategorized"), ("Summarize by", "None"), ("Is nullable", "Yes")]
    ey = top + 34
    for label, value in entries:
        if value is None:
            d.text(f"<b>▾ {label}</b>", px + 8, ey, 240, 22, size=SMALL)
            ey += 26
            continue
        d.text(esc(label), px + 10, ey, 134, 22, size=SMALL, color=GRAY, valign="middle")
        d.box(esc(value), px + 146, ey, 128, 22, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
        if label == "Summarize by":
            xl.emphasis(d, px + 146, ey, 128, 22)
        ey += 28
    views(d, bottom, "Model view")
    note(d, "Amber: the selected column, FiscalYear, whose Properties are shown. Outlined: Summarize by, set to None, "
            "which is Desktop's Don't summarize. The real editor shows the Data pane to the right of Properties; the "
            "mock leaves it out.", bottom + 40, 56)
    return d


# -- fig-c-04 --------------------------------------------------------------------------------

def fig_c_04() -> Diagram:
    d = Diagram("The Sales and Discounts Page in the Report Editor")
    y = header(d, 0, "Charles River Reports", ["Text box", "Buttons", "Visual interactions", "Save"])
    d.box("", 0, y, 860, 30, fill=WHITE, stroke=RULE, rounded=False)
    mx = 8
    for label in ["File ▾", "View ▾", "Reading view", "Mobile layout", "Open semantic model"]:
        w = text_width(esc(label), SMALL, False) + 18
        d.text(esc(label), mx, y + 5, w, 20, size=SMALL, valign="middle")
        mx += w + 6
    top = y + 30
    cw = 600
    bottom = top + 420
    pbi.canvas(d, 0, top, cw, bottom - top)
    x0 = 18
    pbi.slicer_tiles(d, x0, top + 18, "FiscalYear", ["2024", "2025", "2026"], "2026", tile_w=56)
    invoices = len({r["inv"] for r in lines() if r["fy"] == 2026})
    assert invoices == one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate LIKE '2026%'")[0]
    cards = [("Revenue", pbi.amount(total("rev", fy=2026))), ("At list price", pbi.amount(total("list", fy=2026))),
             ("Discounts", pbi.amount(total("disc", fy=2026))), ("Invoices", str(invoices))]
    cy = top + 86
    pbi.frame(d, x0, cy, cw - 36, 72, None, selected=True)
    cardw = (cw - 36 - 12) / 4
    for i, (label, value) in enumerate(cards):
        pbi.card(d, x0 + 6 + i * cardw, cy + 6, cardw - 6, 60, label, value)
    disc = monthly("disc")
    assert disc.index(max(disc)) == 9 and disc[8] > 10 * disc[7], "the autumn promotion months stand out"
    ly = cy + 86
    pbi.line_chart(d, x0, ly, cw - 36, 230, "Promotional discounts by month", MONTHS_2026, [("Discounts", disc, BLUE)],
                   "K", pbi.nice_ticks(0, max(disc), 3), every=2)
    pbi.page_tabs(d, 4, bottom + 4, ["Sales and Discounts", "Validation"], "Sales and Discounts")
    # Visualizations pane: the visual types with Card, and the card's wells.
    vx = cw + 8
    d.box("", vx, top, 860 - vx, bottom - top, fill=WHITE, stroke=RULE, rounded=False)
    d.text("<b>Visualizations</b>", vx + 8, top + 6, 200, 22, size=SMALL)
    d.text("Build visual", vx + 8, top + 30, 200, 20, size=SMALL, color=BLUE)
    types = ["Slicer", "Table", "Matrix", "Line chart", "Gauge", "Card", "KPI", "…"]
    for i, name in enumerate(types):
        col, row = i % 2, i // 2
        on = name == "Card"
        d.box(f"<b>{name}</b>" if on else name, vx + 8 + col * 120, top + 56 + row * 28, 114, 24,
              fill=AMBER_TINT if on else GRAY_TINT, stroke=AMBER if on else RULE, size=SMALL, rounded=False)
    wy = top + 180
    d.text("<b>Value</b>", vx + 8, wy, 200, 20, size=SMALL)
    for i, (label, _) in enumerate(cards):
        d.box(esc(label), vx + 8, wy + 22 + i * 28, 236, 24, fill=BLUE_TINT, stroke=RULE, size=SMALL, align="left",
              rounded=False)
    d.text("<b>Categories</b>", vx + 8, wy + 140, 200, 20, size=SMALL)
    d.box("<i>Add data fields here</i>", vx + 8, wy + 162, 236, 28, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL,
          dashed=True)
    # Numbered markers and their legend.
    d.marker("1", vx + 214, top + 138, fill=CORAL)
    d.marker("2", x0 + cw - 66, cy - 12, fill=CORAL)
    d.marker("3", x0 + cw - 66, ly - 12, fill=CORAL)
    legend = ["The … below the visual types > Restore default visuals adds Card when the list lacks it.",
              "Format visual > Visual > Callout > Apply settings to one card > Value > Display units: None, "
              "card by card.",
              "The chart's More options > Sort by > Month, then Sort by > Sort ascending."]
    ly2 = bottom + 40
    for i, text in enumerate(legend):
        d.marker(str(i + 1), 0, ly2 + i * 30, fill=CORAL)
        d.text(esc(text), 30, ly2 + i * 30 + 1, 830, 24, size=SMALL)
    note(d, "The real toolbar and pane show icons; the mock writes their names, and only a few of the visual types. The "
            "real report editor also shows the Filters and Data panes beside Visualizations.", ly2 + 94, 40)
    return d


# -- fig-c-05 --------------------------------------------------------------------------------

QUERY = """EVALUATE
SUMMARIZECOLUMNS (
    SalesInvoice[FiscalYear],
    "Revenue", ROUND ( [Revenue], 2 )
)
ORDER BY SalesInvoice[FiscalYear]"""


def fig_c_05() -> Diagram:
    d = Diagram("Testing the Revenue Measure in DAX Query View")
    years = sorted({r["fy"] for r in lines()})
    revenue = [round(total("rev", fy=y), 2) for y in years]
    assert f"{revenue[-1]:.2f}" == "29756420.08", revenue
    y = header(d, 0, "Charles River Reports", ["Editing ▾", "Share"])
    top = pbi.ribbon(d, 0, y + 2, 860, "Home", ["Format", "Comment", "Uncomment", "Find", "Replace",
                                                 "Command palette"], tabs=EDITOR_TABS)
    ew = 620
    d.box("DAX queries are discarded on close. DAX queries previously saved to the model are not shown or impacted.",
          0, top + 6, ew, 40, fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", rounded=False)
    end = pbi.dax_query_editor(d, 0, top + 54, ew, QUERY, ["Query 1"], "Query 1")
    res = pbi.dax_results(d, 0, end + 12, ["SalesInvoice[FiscalYear]", "[Revenue]"], [190, 150],
                          [[str(y), f"{v:.2f}"] for y, v in zip(years, revenue)])
    bottom = res["bottom"] + 10
    # Data pane: Key Measures first, with its measure.
    dx = ew + 10
    d.box("", dx, top, 860 - dx, bottom - top, fill=WHITE, stroke=RULE, rounded=False)
    d.text("<b>Data</b>", dx + 8, top + 6, 200, 22, size=SMALL)
    entries = [("▾ Key Measures", 0, True), ("Revenue", 1, True), ("▸ Customer", 0, False), ("▸ Item", 0, False),
               ("▸ SalesInvoice", 0, False), ("▸ SalesInvoiceLine", 0, False)]
    for i, (label, level, bold) in enumerate(entries):
        text = f"<b>{esc(label)}</b>" if bold else esc(label)
        d.text("&nbsp;" * 4 * level + text, dx + 8, top + 34 + i * 26, 210, 22, size=SMALL)
    views(d, bottom, "DAX query view")
    note(d, "The Results grid shows the values as the query returns them, without the measure's format. Key Measures "
            "heads the Data pane because its only column, Column1, is hidden.", bottom + 40, 40)
    return d


FIGURES = {
    "fig-c-01-upload-and-choose": fig_c_01,
    "fig-c-02-dates-as-numbers": fig_c_02,
    "fig-c-03-model-editor": fig_c_03,
    "fig-c-04-cards-and-sort": fig_c_04,
    "fig-c-05-dax-query-measure": fig_c_05,
}
