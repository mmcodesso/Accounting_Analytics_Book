"""Chapter 5 figures."""

from __future__ import annotations

import excel as xl
from data import one, q, require_columns
from drawio import (AMBER_TINT, BLUE, BLUE_TINT, GRAY, GRAY_TINT, HEAD, INK, ROW_H, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

SIL_COLUMNS = [r[1] for r in q("PRAGMA table_info(SalesInvoiceLine)")]
SI_COLUMNS = [r[1] for r in q("PRAGMA table_info(SalesInvoice)")]
ITEM_KEPT = ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "StandardCost",
             "ListPrice", "UnitOfMeasure", "SupplyMode", "CollectionName", "LifecycleStatus"]
# Columns added to the SalesInvoiceLine Table in Tutorial 4.1 and Tutorial 5.2, in order.
SIL_ADDED = ["ListAmount", "DiscountAmount", "InvoiceDate", "Period", "SalesOrderID", "OrderDate",
             "ItemGroup", "ProductType"]
# The InvoiceLines query of Tutorial 5.3, in column order.
IL_COLUMNS = SIL_COLUMNS + ["InvoiceDate", "SalesOrderID", "CustomerID", "ItemCode", "ItemGroup",
                            "StandardCost", "CustomerSegment", "Region", "FiscalYear",
                            "FiscalQuarter", "Period", "ProductType", "WholeQuantity"]


def letter(index: int) -> str:
    out, index = "", index + 1
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def period(date_text: str) -> str:
    return f"{date_text[:4]}-Q{(int(date_text[5:7]) + 2) // 3}"


def fig_05_01() -> Diagram:
    d = Diagram("From Related Tables to One Analytical Table")
    require_columns("SalesInvoiceLine", ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID",
                                         "Quantity", "UnitPrice", "Discount", "LineTotal",
                                         "PromotionID"])
    require_columns("SalesInvoice", ["SalesInvoiceID", "InvoiceDate", "SalesOrderID", "CustomerID"])
    require_columns("Item", ["ItemID", "ItemCode", "ItemGroup", "StandardCost"])
    require_columns("Customer", ["CustomerID", "CustomerSegment", "Region"])
    sections = [
        ("SalesInvoiceLine", "The starting query: one row per invoice line", BLUE, BLUE_TINT,
         ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "UnitPrice", "Discount",
          "LineTotal", "PromotionID", "and the other line columns"]),
        ("SalesInvoice", "Merged on SalesInvoiceID", TEAL, TEAL_TINT,
         ["InvoiceDate", "SalesOrderID", "CustomerID"]),
        ("Item", "Merged on ItemID", GRAY, GRAY_TINT, ["ItemCode", "ItemGroup", "StandardCost"]),
        ("Customer", "Merged on CustomerID, from SalesInvoice", GRAY, GRAY_TINT,
         ["CustomerSegment", "Region"]),
        ("Custom columns", "Calculated in the query", BLUE, WHITE,
         ["FiscalYear", "FiscalQuarter", "Period", "ProductType", "WholeQuantity"]),
    ]
    rx, rw, lx, lw = 520, 340, 0, 300
    d.header_box("InvoiceLines", rx, 0, rw, 32)
    y = 44
    for name, caption, fill, tint, cols in sections:
        top = y
        d.box(f"<b>From {esc(name)}</b>" if name != "Custom columns" else "<b>Added columns</b>",
              rx, y, rw, 22, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        y += 22
        for col in cols:
            italic = col.startswith("and ")
            d.box(f"<i>{esc(col)}</i>" if italic else esc(col), rx, y, rw, 22, fill=tint,
                  stroke=RULE, size=SMALL, color=GRAY if italic else INK, align="left",
                  rounded=False)
            y += 22
        height = y - top
        box_h = min(height, 90)
        box_y = top + (height - box_h) / 2
        if name == "Custom columns":
            src = d.box("<b>Power Query</b><br>Custom Column formulas, such as "
                        "Text.Middle([ItemCode], 4, 3)", lx, box_y, lw, box_h, fill=WHITE,
                        stroke=BLUE, stroke_width=1.5, align="left", valign="middle")
        else:
            d.header_box(esc(name), lx, box_y, lw, 30, fill=fill)
            src = d.box(esc(caption), lx, box_y + 30, lw, box_h - 30, fill=WHITE, stroke=RULE,
                        align="left", rounded=False)
        tgt = d.container(rx, top, rw, height)
        d.arrow(src, tgt, exit=(1, 0.5), entry=(0, 0.5))
        y += 12
    d.text("<i>Each source Table contributes the columns listed in its section. Every key refers "
           "to exactly one row, so InvoiceLines has one row for each invoice line.</i>", 0, y + 4,
           860, 40, size=SMALL, color=GRAY)
    return d


def fig_05_02() -> Diagram:
    d = Diagram("The Item Table with the Product Type Extracted from the Item Code")
    kept = q("SELECT ItemID FROM Item WHERE ListPrice IS NOT NULL ORDER BY ItemID")
    position = {item: i + 2 for i, (item,) in enumerate(kept)}
    rows = q("SELECT ItemID, ItemCode, ItemName, ItemGroup FROM Item WHERE ListPrice IS NOT NULL "
             "AND ItemGroup = 'Furniture' ORDER BY ItemID LIMIT 7")
    assert all(len(code) == 12 and code[3] == code[7] == "-" for _, code, _, _ in rows)
    letters = ["A", "B", "C", "D", letter(len(ITEM_KEPT)), letter(len(ITEM_KEPT) + 1)]
    heads = ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ProductType", "CodeCheck"]
    body = [(str(position[i]), [str(i), code, name, grp, code[4:7], "TRUE"])
            for i, code, name, grp in rows]
    selected = 1
    xl.formula_bar(d, 0, 0, 860, f"{letters[4]}{body[selected][0]}", "=MID([@ItemCode],5,3)")
    widths = [44, 70, 120, 330, 96, 100, 96]

    def added(r: int, c: int, value: str) -> dict:
        return dict(fill=TEAL_TINT) if c >= 4 else {}

    geo = xl.table_view(d, 0, 40, letters, widths, heads, body, extra=added)
    xl.select(d, *geo[(selected + 1, 4)])
    x4, y0, _, _ = geo[(0, 4)]
    xl.emphasis(d, x4, y0, widths[5] + widths[6], ROW_H * (len(body) + 1))
    bottom = 40 + 22 + ROW_H * (len(body) + 1)
    d.text("<i>Columns E through K are hidden. Outlined: the two calculated columns added in Steps 1 "
           "and 2.</i>", 0, bottom + 8, 860, 20, size=SMALL, color=GRAY)
    return d


def fig_05_03() -> Diagram:
    d = Diagram("The SalesInvoice Table with Fiscal Period and Payment Terms Columns")
    # A block of consecutive invoices around the start of the fourth quarter of 2026.
    first = one("SELECT MIN(SalesInvoiceID) FROM SalesInvoice WHERE InvoiceDate >= '2026-10-01'")[0]
    rows = q("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate, DueDate FROM SalesInvoice "
             "WHERE SalesInvoiceID BETWEEN ? AND ? ORDER BY 1", first - 3, first + 3)
    assert len(rows) == 7
    assert {period(r[2]) for r in rows} >= {"2026-Q3", "2026-Q4"}, rows
    from datetime import date
    n = len(SI_COLUMNS)
    letters = ["A", "B", "C", "D", letter(n), letter(n + 1), letter(n + 2), letter(n + 3)]
    heads = ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "FiscalYear",
             "FiscalQuarter", "Period", "DaysToDue"]
    body = []
    for sid, number, inv, due in rows:
        days = (date.fromisoformat(due) - date.fromisoformat(inv)).days
        body.append((str(sid + 1), [str(sid), number, inv, due, inv[:4],
                                    str((int(inv[5:7]) + 2) // 3), period(inv), str(days)]))
    selected = 3
    xl.formula_bar(d, 0, 0, 860, f"{letters[6]}{body[selected][0]}",
                   '=[@FiscalYear]&"-Q"&[@FiscalQuarter]')
    widths = [56, 112, 122, 96, 96, 90, 106, 84, 98]

    def added(r: int, c: int, value: str) -> dict:
        return dict(fill=TEAL_TINT) if c >= 4 else {}

    geo = xl.table_view(d, 0, 40, letters, widths, heads, body, extra=added)
    xl.select(d, *geo[(selected + 1, 6)])
    x4, y0, _, _ = geo[(0, 4)]
    xl.emphasis(d, x4, y0, sum(widths[5:]), ROW_H * (len(body) + 1))
    bottom = 40 + 22 + ROW_H * (len(body) + 1)
    d.text("<i>Columns E through L are hidden. The rows shown span the end of the third quarter and "
           "the start of the fourth. Outlined: the four calculated columns.</i>", 0, bottom + 8,
           860, 40, size=SMALL, color=GRAY)
    return d


def fig_05_04() -> Diagram:
    d = Diagram("How XLOOKUP Retrieves a Value from Another Table")
    line = one("SELECT SalesInvoiceLineID, SalesInvoiceID, LineTotal FROM SalesInvoiceLine "
               "WHERE SalesInvoiceLineID = 10645")
    inv_id = line[1]
    invoices = q("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate FROM SalesInvoice "
                 "WHERE SalesInvoiceID BETWEEN ? AND ? ORDER BY 1", inv_id - 2, inv_id + 2)
    match = next(r for r in invoices if r[0] == inv_id)

    d.box('<b>=XLOOKUP(</b>[@SalesInvoiceID]<b>,</b> SalesInvoice[SalesInvoiceID]<b>,</b> '
          'SalesInvoice[InvoiceDate]<b>,</b> "No match"<b>)</b>', 0, 0, 860, 34, fill=GRAY_TINT,
          stroke=RULE, align="center", rounded=False)
    labels = [("1", 132), ("2", 330), ("3", 560), ("4", 740)]
    for num, x in labels:
        d.marker(num, x, 40, size=22)

    # Left: the invoice line, in the SalesInvoiceLine Table.
    d.text("<b>SalesInvoiceLine</b>", 0, 80, 340, 22)
    lw = [120, 110, 110]
    lx = [0, 120, 230]
    for x, w, h in zip(lx, lw, ["SalesInvoiceLineID", "InvoiceDate", "SalesInvoiceID"]):
        d.box(f"<b>{h}</b>", x, 104, w, 26, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL,
              align="left", rounded=False)
    vals = [str(line[0]), match[2], str(inv_id)]
    cells = []
    for x, w, v, fill in zip(lx, lw, vals, [WHITE, TEAL_TINT, AMBER_TINT]):
        cells.append(d.box(f"<b>{esc(v)}</b>", x, 130, w, ROW_H, fill=fill, stroke=RULE,
                           size=SMALL, align="right", rounded=False))
    d.marker("1", 230 + 110 - 26, 160, size=22)

    # Right: the SalesInvoice Table.
    rx = 490
    d.text("<b>SalesInvoice</b>", rx, 80, 360, 22)
    rw = [110, 140, 110]
    rxs = [rx, rx + 110, rx + 250]
    for x, w, h in zip(rxs, rw, ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate"]):
        d.box(f"<b>{h}</b>", x, 104, w, 26, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL,
              align="left", rounded=False)
    match_cells = {}
    for i, (sid, num, date_) in enumerate(invoices):
        hit = sid == inv_id
        for j, (x, w, v) in enumerate(zip(rxs, rw, [str(sid), num, date_])):
            fill = (AMBER_TINT if j == 0 else TEAL_TINT if j == 2 else BLUE_TINT) if hit else \
                (WHITE if i % 2 == 0 else GRAY_TINT)
            cid = d.box(f"<b>{esc(v)}</b>" if hit else esc(v), x, 130 + i * ROW_H, w, ROW_H,
                        fill=fill, stroke=RULE, size=SMALL,
                        align="right" if j != 1 else "left", rounded=False)
            if hit:
                match_cells[j] = cid
    top_r = 130
    bottom_r = 130 + ROW_H * len(invoices)
    d.marker("2", rxs[0] + 4, bottom_r + 6, size=22)
    d.marker("3", rxs[2] + 4, bottom_r + 6, size=22)
    d.arrow(cells[2], match_cells[0], exit=(1, 0.5), entry=(0, 0.5), label="finds the key")
    match_y = 130 + ROW_H * [r[0] for r in invoices].index(inv_id) + ROW_H / 2
    d.arrow(match_cells[2], cells[1], exit=(1, 0.5), entry=(0.5, 1),
            points=[(857, match_y), (857, bottom_r + 48), (175, bottom_r + 48)],
            label="returns the date")
    y = bottom_r + 70
    legend = [
        ("1", "Lookup value: the key on the current row, [@SalesInvoiceID]."),
        ("2", "Lookup array: the column searched for the key, SalesInvoice[SalesInvoiceID]."),
        ("3", "Return array: the column whose value is returned, SalesInvoice[InvoiceDate]."),
        ("4", "If not found: the value returned when the key is missing, \"No match\"."),
    ]
    for i, (num, text) in enumerate(legend):
        d.marker(num, 0, y + i * 28, size=22)
        d.text(esc(text), 30, y + i * 28, 830, 24)
    d.text(f"<i>Invoice line {line[0]} belongs to invoice {match[1]}; the lookup returns that "
           "invoice's date.</i>", 0, y + len(legend) * 28 + 4, 860, 20, size=SMALL, color=GRAY)
    return d


def _late_promo_lines() -> tuple[list[tuple], int, int]:
    """Promotion 8 lines invoiced after its end date, in the order Tutorial 4.3 sorted them."""
    end = one("SELECT EffectiveEndDate FROM PromotionProgram WHERE PromotionID = 8")[0]
    lines = q("SELECT l.SalesInvoiceLineID, l.Quantity, l.UnitPrice, l.Discount, l.LineTotal, "
              "l.PromotionID, si.InvoiceDate, si.SalesOrderID, so.OrderDate, i.ItemGroup, i.ItemCode "
              "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
              "JOIN SalesOrder so ON so.SalesOrderID = si.SalesOrderID JOIN Item i USING (ItemID) "
              "WHERE l.PromotionID = 8")
    lines.sort(key=lambda r: -xl.xround(r[1] * r[2] * r[3]))
    before = one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID < 8")[0]
    rows = [(before + 2 + i, r) for i, r in enumerate(lines) if r[6] > end]
    return rows, len(rows), end


def fig_05_05() -> Diagram:
    d = Diagram("Invoice Lines with Their Looked-Up Dates and Groups")
    rows, late, end = _late_promo_lines()
    start = one("SELECT EffectiveStartDate FROM PromotionProgram WHERE PromotionID = 8")[0]
    assert all(start <= r[8] <= end for _, r in rows), "late lines should come from promotion orders"
    total = one("SELECT COUNT(*) FROM SalesInvoiceLine")[0]
    shown = rows[:7]
    base = len(SIL_COLUMNS)
    col = {name: letter(base + i) for i, name in enumerate(SIL_ADDED)}
    letters = ["A", letter(SIL_COLUMNS.index("LineTotal")), letter(SIL_COLUMNS.index("PromotionID")),
               col["InvoiceDate"], col["Period"], col["SalesOrderID"], col["OrderDate"],
               col["ItemGroup"], col["ProductType"]]
    heads = ["SalesInvoiceLineID", "LineTotal", "PromotionID", "InvoiceDate", "Period",
             "SalesOrderID", "OrderDate", "ItemGroup", "ProductType"]
    body = [(str(row), [str(r[0]), xl.num(r[4]), str(r[5]), r[6], period(r[6]), str(r[7]), r[8],
                        r[9], r[10][4:7]]) for row, r in shown]
    xl.formula_bar(d, 0, 0, 860, f"{col['InvoiceDate']}{body[0][0]}",
                   '=XLOOKUP([@SalesInvoiceID],SalesInvoice[SalesInvoiceID],SalesInvoice[InvoiceDate],'
                   '"No match")')
    widths = [48, 132, 84, 86, 92, 72, 94, 92, 76, 84]
    geo = xl.table_view(d, 0, 40, letters, widths, heads, body, number_color=BLUE)
    for c in (3, 6):
        xl.emphasis(d, *xl.column_box(geo, c, len(body) + 1))
    bottom = 40 + 22 + ROW_H * (len(body) + 1)
    xl.status_bar(d, 0, bottom + 8, 860, f"{late} of {total} records found")
    d.text(f"<i>Filtered to promotion 8 and to invoice dates after {end}, the promotion's end date; "
           f"the first {len(shown)} lines in view are shown. Outlined: every line was invoiced after "
           "the promotion ended, from an order placed while it ran.</i>", 0, bottom + 40, 860, 40,
           size=SMALL, color=GRAY)
    return d


def fig_05_06() -> Diagram:
    d = Diagram("The Merge Dialog in Power Query")
    lines = q("SELECT SalesInvoiceLineID, SalesInvoiceID, LineNumber, ItemID, Quantity "
              "FROM SalesInvoiceLine ORDER BY 1 LIMIT 3")
    invoices = q("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate, DueDate, SalesOrderID "
                 "FROM SalesInvoice ORDER BY 1 LIMIT 3")
    total = one("SELECT COUNT(*) FROM SalesInvoiceLine")[0]
    matched = one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                  "USING (SalesInvoiceID)")[0]
    xl.title_bar(d, 0, 0, 860, "Merge")
    d.text("Select tables and matching columns to create a merged table.", 12, 34, 700, 20,
           size=SMALL)

    def preview(y: float, name: str, heads: list[str], rows: list[tuple], key: int) -> float:
        d.box(f"<b>{esc(name)}</b>", 12, y, 836, 24, fill=WHITE, stroke=RULE, size=SMALL,
              align="left", rounded=False)
        widths = [150, 140, 120, 110, 110]
        xs = [12]
        for w in widths[:-1]:
            xs.append(xs[-1] + w)
        for c, (x, w, h) in enumerate(zip(xs, widths, heads)):
            on = c == key
            d.box(f"<b>{esc(h)}</b>", x, y + 28, w, 24, fill=BLUE if on else GRAY_TINT,
                  stroke=BLUE if on else RULE, color=WHITE if on else INK, size=SMALL,
                  align="left", rounded=False)
        for r, row in enumerate(rows):
            for c, (x, w, v) in enumerate(zip(xs, widths, row)):
                d.box(esc(str(v)), x, y + 52 + r * 22, w, 22,
                      fill=BLUE_TINT if c == key else WHITE, stroke=RULE, size=SMALL,
                      align="right" if isinstance(v, (int, float)) else "left", rounded=False)
        xl.emphasis(d, xs[key], y + 28, widths[key], 24 + 22 * len(rows))
        return y + 52 + 22 * len(rows)

    y = preview(62, "InvoiceLines", ["SalesInvoiceLineID", "SalesInvoiceID", "LineNumber",
                                     "ItemID", "Quantity"],
                [(r[0], r[1], r[2], r[3], f"{r[4]:.2f}") for r in lines], 1)
    y = preview(y + 16, "SalesInvoice ▾", ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate",
                                          "DueDate", "SalesOrderID"], invoices, 0)
    d.text("<b>Join Kind</b>", 12, y + 14, 200, 20, size=SMALL)
    d.box("Left Outer (all from first, matching from second) ▾", 12, y + 36, 420, 26, fill=WHITE,
          stroke=RULE, size=SMALL, align="left", rounded=False)
    xl.emphasis(d, 12, y + 36, 420, 26)
    d.box(f"The selection matches {matched} of {total} rows from the first table.", 12, y + 74,
          560, 26, fill=TEAL_TINT, stroke=TEAL, size=SMALL, align="left", rounded=False)
    xl.button(d, 680, y + 74, 76, "OK", primary=True)
    xl.button(d, 766, y + 74, 82, "Cancel")
    d.box("", 0, 28, 860, y + 112 - 28, fill="none", stroke=RULE, rounded=False)
    d.text("<i>Outlined: the key column selected in each table, and the join kind.</i>", 0,
           y + 120, 860, 20, size=SMALL, color=GRAY)
    return d


def fig_05_07() -> Diagram:
    d = Diagram("The Custom Column Dialog in Power Query")
    require_columns("Item", ["ItemCode"])
    xl.title_bar(d, 0, 0, 860, "Custom Column")
    d.text("<b>New column name</b>", 16, 38, 300, 20, size=SMALL)
    d.box("ProductType", 16, 60, 520, 26, fill=WHITE, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    d.text("<b>Custom column formula</b>", 16, 96, 300, 20, size=SMALL)
    formula = d.box("= Text.Middle([ItemCode], 4, 3)", 16, 118, 520, 170, fill=WHITE, stroke=RULE,
                    size=SMALL, align="left", valign="top", rounded=False)
    xl.emphasis(d, 16, 118, 520, 30)
    d.text("<b>Available columns</b>", 560, 38, 280, 20, size=SMALL)
    available = ["SalesInvoiceLineID", "Quantity", "LineTotal", "InvoiceDate", "CustomerID",
                 "ItemCode", "ItemGroup", "CustomerSegment", "FiscalYear"]
    for i, name in enumerate(available):
        on = name == "ItemCode"
        d.box(f"<b>{name}</b>" if on else name, 560, 60 + i * 22, 284, 22,
              fill=BLUE_TINT if on else WHITE, stroke=RULE, size=SMALL, align="left",
              rounded=False)
    xl.button(d, 560, 60 + len(available) * 22 + 8, 100, "<< Insert")
    d.text("No syntax errors have been detected.", 16, 298, 520, 20, size=SMALL, color=TEAL)
    xl.button(d, 680, 330, 76, "OK", primary=True)
    xl.button(d, 766, 330, 82, "Cancel")
    d.box("", 0, 28, 860, 340, fill="none", stroke=RULE, rounded=False)
    d.text("<i>Text.Middle counts from zero, so position 4 is the fifth character, the first letter "
           "of the product type. Outlined: the formula.</i>", 0, 376, 860, 20, size=SMALL,
           color=GRAY)
    return d


def fig_05_08() -> Diagram:
    d = Diagram("The InvoiceLines Table Loaded by Power Query")
    rows = q("SELECT l.SalesInvoiceLineID, l.Quantity, l.LineTotal, si.InvoiceDate, i.ItemGroup, "
             "c.CustomerSegment, i.ItemCode FROM SalesInvoiceLine l JOIN SalesInvoice si "
             "USING (SalesInvoiceID) JOIN Item i USING (ItemID) JOIN Customer c "
             "ON c.CustomerID = si.CustomerID ORDER BY 1 LIMIT 7")
    counts = {
        "Customer": one("SELECT COUNT(*) FROM Customer")[0],
        "InvoiceLines": one("SELECT COUNT(*) FROM SalesInvoiceLine")[0],
        "Item": one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL")[0],
        "PromotionProgram": one("SELECT COUNT(*) FROM PromotionProgram")[0],
        "SalesInvoice": one("SELECT COUNT(*) FROM SalesInvoice")[0],
        "SalesInvoiceLine": one("SELECT COUNT(*) FROM SalesInvoiceLine")[0],
        "SalesOrder": one("SELECT COUNT(*) FROM SalesOrder")[0],
    }
    shown = ["SalesInvoiceLineID", "Quantity", "InvoiceDate", "ItemGroup", "CustomerSegment",
             "Period", "WholeQuantity"]
    letters = [letter(IL_COLUMNS.index(c)) for c in shown]
    body = []
    for line_id, qty, total, inv, grp, seg, code in rows:
        whole = "TRUE" if qty == int(qty) else "FALSE"
        body.append((str(line_id + 1), [str(line_id), xl.num(qty), inv, grp, seg, period(inv),
                                        whole]))
    widths = [36, 128, 66, 88, 82, 126, 68, 100]
    xl.table_view(d, 0, 0, letters, widths, shown, body)
    px = sum(widths) + 14
    pw = 860 - px
    d.box("<b>Queries &amp; Connections</b>", px, 0, pw, 28, fill=GRAY_TINT, stroke=RULE,
          size=SMALL, align="left", rounded=False)
    y = 32
    for name in sorted(counts):
        on = name == "InvoiceLines"
        d.box(f"<b>{name}</b><br>{counts[name]:,} rows loaded", px, y, pw, 40,
              fill=BLUE_TINT if on else WHITE, stroke=RULE, size=SMALL, align="left",
              valign="middle", rounded=False)
        if on:
            xl.emphasis(d, px, y, pw, 40)
        y += 42
    bottom = max(22 + ROW_H * (len(body) + 1), y)
    d.text("<i>Seven of the Table's columns are shown. Outlined: InvoiceLines loads as many rows as "
           "SalesInvoiceLine.</i>", 0, bottom + 8, 860, 20, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-05-01-invoicelines-map": fig_05_01,
    "fig-05-02-item-product-type": fig_05_02,
    "fig-05-03-salesinvoice-periods": fig_05_03,
    "fig-05-04-xlookup-anatomy": fig_05_04,
    "fig-05-05-invoice-line-lookups": fig_05_05,
    "fig-05-06-merge-dialog": fig_05_06,
    "fig-05-07-custom-column": fig_05_07,
    "fig-05-08-invoicelines-table": fig_05_08,
}
