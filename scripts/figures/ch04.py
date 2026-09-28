"""Chapter 4 figures."""

from __future__ import annotations

import re
import zipfile

import excel as xl
from data import REPO_ROOT, one, q, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, HEAD, INK, ROW_H,
                    RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

XLSX = xl.XLSX
QUERIES = ["SalesInvoice", "SalesInvoiceLine", "Item", "PromotionProgram"]
ITEM_COLUMNS = ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "StandardCost",
                "ListPrice", "UnitOfMeasure", "SupplyMode", "CollectionName", "LifecycleStatus"]
PRICING = ["Approved Override", "Base List", "Customer Price List", "Segment Price List"]
RATES = [0.0, 0.08, 0.10, 0.12]


def excel_tables() -> dict[str, str]:
    return xl.workbook_tables()


def sil_columns() -> list[str]:
    return [r[1] for r in q("PRAGMA table_info(SalesInvoiceLine)")]


def letter(index: int) -> str:
    """Column letter of a 0-based column index (A..Z, then AA..)."""
    out = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def _cell(d: Diagram, value: str, x: float, y: float, w: float, fill: str = WHITE,
          bold: bool = False, align: str = "left", color: str = INK, stroke: str = RULE) -> str:
    text = f"<b>{value}</b>" if bold else value
    return d.box(text, x, y, w, ROW_H, fill=fill, stroke=stroke, color=color, align=align,
                 rounded=False)


def fig_04_01() -> Diagram:
    d = Diagram("A Plain Range Compared with an Excel Table")
    require_columns("SalesInvoiceLine", ["SalesInvoiceLineID", "Quantity", "BaseListPrice",
                                         "LineTotal"])
    ids = (10644, 10645, 10646, 10647)
    rows = q("SELECT SalesInvoiceLineID, Quantity, BaseListPrice, LineTotal FROM SalesInvoiceLine "
             f"WHERE SalesInvoiceLineID IN ({','.join('?' * len(ids))}) ORDER BY 1", *ids)
    assert [r[0] for r in rows] == list(ids), rows
    first, last = one("SELECT MIN(SalesInvoiceLineID), MAX(SalesInvoiceLineID) FROM SalesInvoiceLine")
    count = one("SELECT COUNT(*) FROM SalesInvoiceLine")[0]
    assert (first, last) == (1, count), "row numbers below assume IDs 1..n in worksheet order"
    invoice = one("SELECT si.InvoiceNumber FROM SalesInvoiceLine l JOIN SalesInvoice si "
                  "USING (SalesInvoiceID) WHERE l.SalesInvoiceLineID = 10645")[0]
    traced = 10645
    cols = sil_columns()
    # Worksheet letters of the source columns, and of the first empty column after the data.
    letters = [letter(cols.index(c)) for c in ("SalesInvoiceLineID", "Quantity", "BaseListPrice",
                                                "LineTotal")] + [letter(len(cols))]
    qty_l, price_l, total_l, new_l = letters[1], letters[2], letters[3], letters[4]
    heads = ["SalesInvoiceLineID", "Quantity", "BaseListPrice", "LineTotal", "ListAmount"]
    # Both views use the same worksheet frame, so their columns line up and span the full width.
    widths = [60, 196, 128, 156, 156, 164]
    assert sum(widths) == 860
    gap, box_h = 12, 84
    box_w = (860 - gap) / 2

    def values(line_id: int, qty: float, price: float, total: float) -> list[str]:
        return [str(line_id), xl.num(qty), xl.num(price), xl.num(total),
                xl.num(xl.xround(qty * price))]

    body = [("1", heads)] + [(str(r[0] + 1), values(*r)) for r in rows]
    traced_r = ids.index(traced) + 1
    grid_h = 22 + ROW_H * len(body)

    # Top: the plain range. Row 1 is ordinary cells, and Excel knows nothing about the data.
    d.text("<b>Plain range</b>: Excel sees cells, identified by column letters and row numbers",
           0, 0, 860, 22, size=HEAD)

    def plain(r: int, c: int, value: str) -> dict:
        if r == 0:
            return dict(fill=GRAY_TINT, align="left")
        mark = r == traced_r
        return dict(fill=AMBER_TINT if mark else WHITE,
                    label=f"<b>{esc(value)}</b>" if mark else esc(value))

    xs = [0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    d.text("<i>No name: formulas must refer to cell addresses</i>", xs[1], 26, 400, 20,
           size=SMALL, color=GRAY)
    d.text("<i>Formula copied by hand</i>", xs[5], 26, widths[5], 20, size=SMALL, color=GRAY,
           align="center")
    top = 48
    geo = xl.sheet(d, 0, top, letters, widths, body, plain)
    xl.select(d, *geo[(traced_r, 4)])
    y = top + grid_h + 12
    traced_row = traced + 1
    d.box(f"<b>Column formula, copied by hand:</b><br>{new_l}{traced_row} holds "
          f"=ROUND({qty_l}{traced_row}*{price_l}{traced_row},2). The formula was typed in "
          f"{new_l}2 and copied down, so every row has its own copy. Rows added below the data "
          "get no formula until you copy it again.", 0, y, box_w, box_h, fill=GRAY_TINT,
          stroke=GRAY, stroke_width=1.5, align="left", valign="top")
    d.box(f"<b>Total:</b> =SUM({total_l}2:{total_l}{count + 1})<br>The formula names fixed cells. "
          f"Rows added below row {count + 1} are left out of the total, and nothing warns you.",
          box_w + gap, y, box_w, box_h, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5,
          align="left", valign="top")

    # Bottom: the same cells stored as the SalesInvoiceLine Table.
    top = y + box_h + 32
    d.text("<b>Excel Table</b>: Excel sees a named dataset with named columns", 0, top, 860, 22,
           size=HEAD)
    d.text("<i>Table name: SalesInvoiceLine</i>", xs[1], top + 26, 400, 20, size=SMALL, color=GRAY)
    d.text("<i>Calculated column</i>", xs[5], top + 26, widths[5], 20, size=SMALL, color=TEAL,
           align="center")

    def table(r: int, c: int, value: str) -> dict:
        if r == 0:
            fill = TEAL if c == 4 else BLUE
            return dict(fill=fill, stroke=fill, color=WHITE, align="left",
                        label=f"<b>{esc(value)} ▾</b>")
        if r == traced_r:
            return dict(fill=AMBER_TINT, label=f"<b>{esc(value)}</b>")
        if c == 4:
            return dict(fill=TEAL_TINT)
        return dict(fill=WHITE if r % 2 else BLUE_TINT)

    grid_top = top + 48
    xl.sheet(d, 0, grid_top, letters, widths, body, table)
    y = grid_top + grid_h + 12
    d.box("<b>Calculated column:</b><br>=ROUND([@Quantity]*[@BaseListPrice],2)<br>One formula for "
          "the whole column. Excel fills it into every row, including rows added later.", 0, y,
          box_w, box_h, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, align="left",
          valign="top")
    d.box("<b>Total:</b> =SUM(SalesInvoiceLine[LineTotal])<br>Includes every row the Table "
          "holds, however many there are.", box_w + gap, y, box_w, box_h, fill=BLUE_TINT,
          stroke=BLUE, stroke_width=1.5, align="left", valign="top")
    d.text(f"<i>Both views show the same cells. Shaded row: line {traced}, the Alder Desk sold on "
           f"invoice {invoice}, which you traced in Tutorial 3.2. The selected cell holds the plain "
           "range's formula for that line.</i>", 0, y + box_h + 10, 860, 40, size=SMALL,
           color=GRAY)
    return d


def fig_04_05() -> Diagram:
    d = Diagram("How Cell References Behave When a Formula Is Copied")
    panel_w = 272
    gap = (860 - 3 * panel_w) / 2

    def grid(x: float, y: float, widths: list[float], rows: list[list[str]],
             formula_cells: set[tuple[int, int]]) -> float:
        """Draw a small worksheet: row 0 holds column letters, column 0 holds row numbers."""
        xs = [x]
        for w in widths[:-1]:
            xs.append(xs[-1] + w)
        for r, row in enumerate(rows):
            for c, (value, cx, w) in enumerate(zip(row, xs, widths)):
                if r == 0 or c == 0:
                    _cell(d, value, cx, y + r * ROW_H, w, fill=GRAY_TINT, align="center",
                          color=GRAY)
                elif (r, c) in formula_cells:
                    _cell(d, value, cx, y + r * ROW_H, w, fill=AMBER_TINT, stroke=AMBER)
                else:
                    _cell(d, value, cx, y + r * ROW_H, w,
                          align="right" if value[:1].isdigit() else "left")
        return y + len(rows) * ROW_H

    panels = [
        ("Relative: A2", BLUE,
         [["", "B", "C", "D"], ["2", "4", "25.00", "=B2*C2"], ["3", "6", "30.00", "=B3*C3"]],
         [30, 60, 70, 112], {(1, 3), (2, 3)},
         "Copied down one row, <b>=B2*C2</b> becomes <b>=B3*C3</b>. Both the row and the "
         "column adjust, so each row uses its own data."),
        ("Absolute: $A$2", TEAL,
         [["", "B", "C"], ["2", "100.00", "=B2/<b>$B$6</b>"], ["3", "250.00", "=B3/<b>$B$6</b>"],
          ["6", "1,000.00", "Total"]],
         [30, 100, 142], {(1, 2), (2, 2)},
         "Copied down, the relative part changes, but <b>$B$6</b> never does, so every row "
         "divides by the same total."),
        ("Mixed: $A2 and A$2", GRAY,
         [["", "A", "B", "C"], ["2", "", "5%", "10%"], ["3", "100", "=<b>$A</b>3*(1-B<b>$2</b>)",
                                                        "=<b>$A</b>3*(1-C<b>$2</b>)"],
          ["4", "250", "=<b>$A</b>4*(1-B<b>$2</b>)", ""]],
         [26, 40, 103, 103], {(2, 2), (2, 3), (3, 2)},
         "<b>$A</b> locks the column of the row labels, and <b>$2</b> locks the row of the column "
         "headers. One formula fills the whole grid."),
    ]
    for i, (title, fill, rows, widths, formulas, note) in enumerate(panels):
        x = i * (panel_w + gap)
        d.header_box(title, x, 0, panel_w, 30, fill=fill)
        bottom = grid(x, 42, widths, rows, formulas)
        d.text(note, x, max(bottom, 42 + 4 * ROW_H) + 10, panel_w, 64)
    d.text("<i>Shaded cells hold the copied formula. Values are illustrative.</i>", 0, 238, 860,
           20, size=SMALL, color=GRAY, align="center")
    return d


def fig_04_07() -> Diagram:
    d = Diagram("Layers of an Analysis Workbook")
    tables = q("SELECT name FROM sqlite_master WHERE type = 'table' AND name IN "
               "('SalesInvoice', 'SalesInvoiceLine', 'Item', 'PromotionProgram')")
    assert len(tables) == 4, tables

    # Source workbook.
    d.header_box("CharlesRiver.xlsx", 0, 110, 160, 32, fill=GRAY)
    source = d.box("<i>Source, never edited</i><br><br>T16_SalesInvoice<br>T17_SalesInvoiceLine<br>"
                   "T44_Item<br>T7_PromotionProgram", 0, 142, 160, 150, fill=GRAY_TINT,
                   stroke=RULE, align="left", valign="top", rounded=False)

    # Documentation, first worksheet.
    d.header_box("1  Documentation", 260, 0, 600, 32, fill=BLUE)
    d.box("Purpose, source file and query steps, parameters, worksheets, conventions, preparer "
          "and reviewer, open questions. First worksheet in the workbook; describes every layer "
          "below.", 260, 32, 600, 50, fill=BLUE_TINT, stroke=RULE, align="left", rounded=False)

    # Data worksheets.
    d.header_box("2  Data worksheets", 260, 110, 250, 32, fill=BLUE)
    data = d.box("One Table per worksheet, loaded by a query:<br>SalesInvoice<br>SalesInvoiceLine "
                 "(with calculated columns)<br>Item<br>PromotionProgram<br><i>Nothing else on these "
                 "sheets.</i>", 260, 142, 250, 150, fill=WHITE, stroke=RULE, align="left",
                 valign="top", rounded=False)

    # Parameters.
    d.header_box("3  Parameters", 260, 340, 250, 32, fill=TEAL)
    params = d.box("Named, validated inputs:<br>ThresholdPercentile (input)<br>LargeLineThreshold "
                   "(formula)", 260, 372, 250, 76, fill=TEAL_TINT, stroke=RULE, align="left",
                   valign="top", rounded=False)

    # Analysis.
    d.header_box("4  Analysis", 610, 110, 250, 32, fill=BLUE)
    analysis = d.box("Control totals, summary grid, SUBTOTAL results.<br>Formulas use structured "
                     "references to the Tables and names for the parameters.", 610, 142, 250, 150,
                     fill=WHITE, stroke=RULE, align="left", valign="top", rounded=False)

    d.arrow(source, data, exit=(1, 0.5), entry=(0, 0.5),
            label="Power Query:<br>recorded steps;<br>Refresh All<br>repeats them")
    d.arrow(data, analysis, exit=(1, 0.5), entry=(0, 0.5), label="structured<br>references")
    d.arrow(params, analysis, exit=(1, 0.5), entry=(0.5, 1), points=[(735, 410)],
            label="named cells")
    d.text("<i>Numbers give the order of the worksheet tabs. Gray marks the external source; "
           "blue and teal mark worksheets in the analysis workbook.</i>", 0, 464, 860, 20,
           size=SMALL, color=GRAY, align="center")
    return d


def fig_04_02() -> Diagram:
    d = Diagram("The Power Query Navigator")
    tables = excel_tables()
    chosen = [tables[t] for t in QUERIES]
    cols = ["SalesInvoiceLineID", "SalesInvoiceID", "SalesOrderLineID", "ItemID", "Quantity"]
    require_columns("SalesInvoiceLine", cols)
    rows = q(f"SELECT {', '.join(cols)} FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT 6")

    xl.title_bar(d, 0, 0, 860, "Navigator")
    # Left pane: the list of worksheets and Tables.
    d.box("<i>Search</i>", 12, 40, 290, 26, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL,
          align="left", rounded=False)
    xl.checkbox(d, 14, 78, True)
    d.text("Select multiple items", 34, 74, 200, 22, size=SMALL)
    xl.emphasis(d, 12, 74, 170, 22)
    d.text(f"<b>{esc(XLSX.name)} [{len(chosen)}]</b>", 12, 104, 290, 22, size=SMALL)
    listing = [("sheet", "Item", False), ("sheet", "PromotionProgram", False),
               ("sheet", "SalesInvoice", False), ("sheet", "SalesInvoiceLine", False),
               ("gap", "", False)]
    listing += [("table", name, True) for name in sorted(chosen)]
    y = 130
    for kind, name, checked in listing:
        if kind == "gap":
            d.text("<i>. . .</i>", 60, y, 200, 20, size=SMALL, color=GRAY)
            y += 22
            continue
        if name == tables["SalesInvoiceLine"]:
            d.box("", 12, y - 2, 290, 24, fill=BLUE_TINT, stroke=BLUE_TINT, rounded=False)
        xl.checkbox(d, 20, y + 3, checked)
        xl.item_icon(d, 42, y + 4, kind)
        d.text(f"<b>{esc(name)}</b>" if checked else esc(name), 64, y, 230, 20, size=SMALL)
        y += 26
    list_bottom = y
    # Right pane: the preview of the selected Table.
    d.text(f"<b>{esc(tables['SalesInvoiceLine'])}</b>", 322, 40, 400, 22, size=SMALL)
    widths = [126, 104, 120, 60, 70, 40]
    xs = [322]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    for cx, w, head in zip(xs, widths, [*cols, "..."]):
        d.box(f"<b>{esc(head)}</b>", cx, 66, w, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              align="left", rounded=False)
    for r, row in enumerate(rows):
        values = [str(row[0]), str(row[1]), str(row[2]), str(row[3]), f"{row[4]:.2f}", ""]
        for c, (cx, w, v) in enumerate(zip(xs, widths, values)):
            d.box(esc(v), cx, 90 + r * 24, w, 24, fill=WHITE, stroke=RULE, size=SMALL,
                  align="right" if c else "left", rounded=False)
    d.text("<i>Preview of the first rows; the Table has more columns to the right.</i>", 322,
           90 + len(rows) * 24 + 4, 510, 20, size=SMALL, color=GRAY)
    # Buttons, then the dialog border.
    by = max(list_bottom, 330) + 8
    xl.button(d, 560, by, 80, "Load")
    xl.button(d, 648, by, 120, "Transform Data", primary=True)
    xl.button(d, 776, by, 70, "Cancel")
    xl.emphasis(d, 648, by, 120, 26)
    d.box("", 0, 28, 860, by + 38 - 28, fill="none", stroke=RULE, rounded=False)
    # Legend.
    ly = by + 50
    xl.item_icon(d, 0, ly + 4, "table")
    d.text("Excel Table", 22, ly, 110, 20, size=SMALL)
    xl.item_icon(d, 130, ly + 4, "sheet")
    d.text("Worksheet", 152, ly, 100, 20, size=SMALL)
    d.text("<i>Outlined: the check box and the button used in Step 2. The list is an excerpt; "
           "the Navigator lists every worksheet and every Table.</i>", 250, ly, 610, 36,
           size=SMALL, color=GRAY)
    return d


def fig_04_03() -> Diagram:
    d = Diagram("The Power Query Editor with the Item Query")
    require_columns("Item", ITEM_COLUMNS)
    kept = q("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL")[0][0]
    shown = ["ItemID", "ItemName", "ItemGroup", "ListPrice"]
    rows = q(f"SELECT {', '.join(shown)} FROM Item WHERE ListPrice IS NOT NULL ORDER BY ItemID "
             "LIMIT 7")

    xl.title_bar(d, 0, 0, 860, "Power Query Editor")
    # Queries pane.
    d.box(f"<b>Queries [{len(QUERIES)}]</b>", 0, 36, 160, 26, fill=GRAY_TINT, stroke=RULE,
          size=SMALL, align="left", rounded=False)
    for i, name in enumerate(QUERIES):
        on = name == "Item"
        d.box(f"<b>{name}</b>" if on else name, 0, 62 + i * 26, 160, 26,
              fill=BLUE if on else WHITE, stroke=BLUE if on else RULE,
              color=WHITE if on else INK, size=SMALL, align="left", rounded=False)
    # Formula bar and data preview.
    step = '= Table.SelectColumns(#"Filtered Rows", {"ItemID", "ItemCode", "ItemName", ...})'
    d.box("<i>fx</i>", 172, 36, 26, 26, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL,
          rounded=False)
    d.box(esc(step), 200, 36, 470, 26, fill=WHITE, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    widths = [28, 60, 222, 96, 92]
    xs = [172]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    heads = ["", *[c + (" ▾" if c == "ListPrice" else "") for c in shown]]
    for cx, w, head in zip(xs, widths, heads):
        d.box(f"<b>{esc(head)}</b>", cx, 72, w, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              align="left", rounded=False)
    for r, row in enumerate(rows):
        values = [str(r + 1), str(row[0]), row[1], row[2], f"{row[3]:.2f}"]
        for c, (cx, w, v) in enumerate(zip(xs, widths, values)):
            d.box(esc(v), cx, 98 + r * 24, w, 24, fill=GRAY_TINT if c == 0 else WHITE,
                  stroke=RULE, color=GRAY if c == 0 else INK, size=SMALL,
                  align="right" if c in (0, 1, 4) else "left", rounded=False)
    grid_bottom = 98 + len(rows) * 24
    xl.emphasis(d, xs[-1], 72, widths[-1], grid_bottom - 72)
    # Query Settings pane.
    d.box("<b>Query Settings</b>", 684, 36, 176, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL,
          align="left", rounded=False)
    d.text("<b>Name</b>", 690, 66, 166, 20, size=SMALL)
    d.box("Item", 690, 86, 166, 24, fill=WHITE, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    d.text("<b>Applied Steps</b>", 690, 118, 166, 20, size=SMALL)
    steps = ["Source", "Navigation", "Changed Type", "Filtered Rows", "Removed Other Columns"]
    for i, name in enumerate(steps):
        last = i == len(steps) - 1
        d.box(f"<b>{name}</b>" if last else name, 690, 140 + i * 24, 166, 24,
              fill=BLUE_TINT if last else WHITE, stroke=RULE, size=SMALL, align="left",
              rounded=False)
    xl.emphasis(d, 690, 140 + 3 * 24, 166, 48)
    bottom = max(grid_bottom, 140 + len(steps) * 24) + 12
    xl.status_bar(d, 0, bottom, 860, f"{len(ITEM_COLUMNS)} COLUMNS, {kept} ROWS")
    d.text(f"<i>Outlined: the ListPrice column, filtered in Step 4, and the two steps that Steps 4 and 5 add to the Applied Steps list. "
           f"{len(shown)} of the {len(ITEM_COLUMNS)} columns kept are shown, without their data type icons.</i>", 0, bottom + 32,
           860, 40, size=SMALL, color=GRAY)
    return d


def _sil_rows(ids: list[int]) -> list[tuple]:
    rows = q("SELECT SalesInvoiceLineID, Quantity, BaseListPrice, UnitPrice, Discount, LineTotal, "
             f"PromotionID FROM SalesInvoiceLine WHERE SalesInvoiceLineID IN "
             f"({','.join('?' * len(ids))}) ORDER BY 1", *ids)
    assert [r[0] for r in rows] == ids, rows
    return rows


def fig_04_04() -> Diagram:
    d = Diagram("The SalesInvoiceLine Table with Calculated Columns")
    cols = sil_columns()
    ids = [24950, 24951, 24952, 24953, 24954]
    rows = _sil_rows(ids)
    assert sum(1 for r in rows if r[6]) >= 2 and sum(1 for r in rows if not r[6]) >= 2, rows
    assert one("SELECT MIN(SalesInvoiceLineID) FROM SalesInvoiceLine")[0] == 1
    shown = ["SalesInvoiceLineID", "Quantity", "BaseListPrice", "UnitPrice", "Discount",
             "LineTotal"]
    letters = [letter(cols.index(c)) for c in shown] + [letter(len(cols)), letter(len(cols) + 1)]
    selected = 1  # the data row whose ListAmount cell is selected
    cell_name = f"{letters[6]}{ids[selected] + 1}"

    d.box("<b>Table Design</b>", 0, 0, 120, 26, fill=WHITE, stroke=BLUE, stroke_width=2,
          color=BLUE, size=SMALL, rounded=False)
    d.text("Table Name:", 136, 2, 90, 22, size=SMALL)
    d.box("SalesInvoiceLine", 226, 2, 150, 22, fill=WHITE, stroke=RULE, size=SMALL,
          align="left", rounded=False)
    xl.emphasis(d, 226, 2, 150, 22)
    xl.formula_bar(d, 0, 36, 860, cell_name, "=ROUND([@Quantity]*[@BaseListPrice],2)")
    heads = [*shown, "ListAmount", "DiscountAmount"]
    widths = [54, 136, 74, 104, 86, 72, 86, 100, 128]
    body = [("1", heads)]
    for line_id, qty, price, unit, disc, total, promo in rows:
        body.append((str(line_id + 1), [str(line_id), xl.num(qty), xl.num(price), xl.num(unit),
                                        f"{disc:g}", xl.num(total), xl.num(xl.xround(qty * price)),
                                        xl.num(xl.xround(qty * unit * disc))]))

    def style(r: int, c: int, value: str) -> dict:
        if r == 0:
            fill = TEAL if c >= 6 else BLUE
            return dict(fill=fill, stroke=fill, color=WHITE, align="left",
                        label=f"<b>{esc(value)}</b>")
        if c >= 6:
            return dict(fill=TEAL_TINT)
        return dict(fill=WHITE if r % 2 else BLUE_TINT)

    geo = xl.sheet(d, 0, 76, letters, widths, body, style)
    gx, gy, gw, gh = geo[(selected + 1, 6)]
    xl.select(d, gx, gy, gw, gh)
    hx, hy, _, _ = geo[(0, 6)]
    xl.emphasis(d, hx, hy, gw + geo[(0, 7)][2], ROW_H * len(body))
    note_y = 76 + 22 + ROW_H * len(body) + 10
    promo_lines = " and ".join(str(r[0]) for r in rows if r[6])
    d.text(f"<i>Columns B–F and L–O are hidden. Lines {promo_lines} carry a promotional discount, "
           "so their DiscountAmount is not zero. Outlined: the Table name and the two calculated "
           "columns.</i>", 0, note_y, 860, 40, size=SMALL, color=GRAY)
    return d


def _analysis_values() -> dict:
    lines = q("SELECT Quantity, BaseListPrice, UnitPrice, Discount, LineTotal, PricingMethod "
              "FROM SalesInvoiceLine")
    methods = {r[5] for r in lines}
    assert methods == set(PRICING), methods
    rates = {round(r[3], 4) for r in lines}
    assert rates == {round(x, 4) for x in RATES}, rates
    totals = [r[4] for r in lines]
    threshold = xl.percentile_inc(totals, 0.9)
    grid = {(m, rate): sum(1 for r in lines if r[5] == m and abs(r[3] - rate) < 1e-9)
            for m in PRICING for rate in RATES}
    line_total = sum(totals)
    large = [t for t in totals if t > threshold]
    return dict(
        lines=len(lines), invoices=one("SELECT COUNT(*) FROM SalesInvoice")[0],
        line_total=line_total, subtotal=one("SELECT SUM(SubTotal) FROM SalesInvoice")[0],
        discount=sum(xl.xround(r[0] * r[2] * r[3]) for r in lines),
        list_amount=sum(xl.xround(r[0] * r[1]) for r in lines),
        threshold=threshold, large=len(large), large_share=sum(large) / line_total, grid=grid)


def fig_04_06() -> Diagram:
    d = Diagram("The Analysis Worksheet with the Summary Grid")
    v = _analysis_values()
    grid, total = v["grid"], v["lines"]
    assert sum(grid.values()) == total

    def pct(x: float) -> str:
        return f"{x:.1%}"

    blank = ["", "", "", "", ""]
    rows: list[tuple[str, list[str]]] = [
        ("1", ["<b>Control totals</b>", *blank]),
        ("3", ["Invoice lines", f"{v['lines']:,}", *blank[1:]]),
        ("4", ["Invoices", f"{v['invoices']:,}", *blank[1:]]),
        ("5", ["Line total", xl.num(v["line_total"]), *blank[1:]]),
        ("6", ["Invoice subtotal", xl.num(v["subtotal"]), *blank[1:]]),
        ("7", ["Difference", xl.num(xl.xround(v["line_total"] - v["subtotal"])), *blank[1:]]),
        ("8", ["Discount taken", xl.num(v["discount"]), *blank[1:]]),
        ("9", ["List amount", xl.num(v["list_amount"]), *blank[1:]]),
        ("11", ["Large lines", f"{v['large']:,}", *blank[1:]]),
        ("12", ["Share of line total", pct(v["large_share"]), *blank[1:]]),
        ("14", ["<b>Invoice lines by pricing method and discount rate</b>", *blank]),
        ("15", ["", *[f"{r:.0%}" for r in RATES], "Total"]),
    ]
    for i, m in enumerate(PRICING):
        counts = [grid[(m, r)] for r in RATES]
        rows.append((str(16 + i), [m, *[f"{c:,}" for c in counts], f"{sum(counts):,}"]))
    col_totals = [sum(grid[(m, r)] for m in PRICING) for r in RATES]
    rows.append(("20", ["Total", *[f"{c:,}" for c in col_totals], f"{total:,}"]))
    rows.append(("22", ["<b>Share of all invoice lines</b>", *blank]))
    for i, m in enumerate(PRICING):
        rows.append((str(23 + i), [m, *[pct(grid[(m, r)] / total) for r in RATES], ""]))
    numbers = [n for n, _ in rows]

    formula = "=COUNTIFS(SalesInvoiceLine[PricingMethod],$A19,SalesInvoiceLine[Discount],E$15)"
    xl.formula_bar(d, 0, 0, 860, "E19", formula)
    widths = [36, 334, 100, 84, 84, 84, 96]

    def style(r: int, c: int, value: str) -> dict:
        out = {}
        if value.startswith("<b>"):
            out["label"] = value
        if numbers[r] in ("15", "20") and value:
            out["label"] = f"<b>{esc(value)}</b>"
            out["align"] = "right" if c else "left"
        return out

    geo = xl.sheet(d, 0, 40, list("ABCDEF"), widths, rows, style, row_h=22)
    xl.select(d, *geo[(numbers.index("19"), 4)])
    gx, gy, _, _ = geo[(numbers.index("16"), 1)]
    xl.emphasis(d, gx, gy, sum(widths[2:]), 22 * 5)
    bottom = 40 + 22 + 22 * len(rows)
    right = xl.sheet_tabs(d, 0, bottom + 6, ["Documentation", "SalesInvoice", "SalesInvoiceLine",
                                            "Item", "PromotionProgram", "Parameters", "Analysis"],
                          "Analysis")
    assert right <= 860, right
    d.text("<i>Rows the tutorial leaves empty are not shown. Outlined: the grid of counts. Cell "
           "E19 is selected, so the formula bar shows its formula.</i>", 0, bottom + 38, 860, 20,
           size=SMALL, color=GRAY)
    return d


def fig_04_08() -> Diagram:
    d = Diagram("The PromotionID Slicer Set to Promotion 8")
    ids = [p for (p,) in q("SELECT PromotionID FROM PromotionProgram ORDER BY 1")]
    counts = dict(q("SELECT PromotionID, COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT "
                    "NULL GROUP BY 1"))
    discount = {p: 0.0 for p in ids}
    for p, qty, unit, disc in q("SELECT PromotionID, Quantity, UnitPrice, Discount FROM "
                                "SalesInvoiceLine WHERE PromotionID IS NOT NULL"):
        discount[p] += xl.xround(qty * unit * disc)
    top = max(ids, key=lambda p: counts.get(p, 0))
    assert top == 8 == max(ids, key=lambda p: discount[p]), (counts, discount)
    total = one("SELECT COUNT(*) FROM SalesInvoiceLine")[0]
    before = sum(counts.get(p, 0) for p in ids if p < top)
    lines = q("SELECT SalesInvoiceLineID, Quantity, UnitPrice, Discount, LineTotal, PromotionID "
              "FROM SalesInvoiceLine WHERE PromotionID = ?", top)
    lines.sort(key=lambda r: -xl.xround(r[1] * r[2] * r[3]))
    shown = lines[:8]

    cols = sil_columns()
    heads = ["SalesInvoiceLineID", "Quantity", "UnitPrice", "Discount", "LineTotal",
             "PromotionID"]
    letters = [letter(cols.index(c)) for c in heads] + [letter(len(cols) + 1)]
    heads.append("DiscountAmount")
    widths = [52, 136, 74, 84, 72, 84, 96, 118]
    body = [("1", list(heads))]
    for i, (line_id, qty, unit, disc, lt, promo) in enumerate(shown):
        body.append((str(before + 2 + i), [str(line_id), xl.num(qty), xl.num(unit), f"{disc:g}",
                                           xl.num(lt), str(promo),
                                           xl.num(xl.xround(qty * unit * disc))]))

    def style(r: int, c: int, value: str) -> dict:
        if r == 0:
            return dict(fill=BLUE, stroke=BLUE, color=WHITE, align="left",
                        label=f"<b>{esc(value)}</b>")
        return dict(fill=AMBER_TINT)

    xl.sheet(d, 0, 0, letters, widths, body, style, number_color=BLUE)
    grid_bottom = 22 + ROW_H * len(body)
    # The slicer.
    sx, sw = 730, 130
    d.box("<b>PromotionID</b>", sx, 0, sw, 28, fill=WHITE, stroke=WHITE, size=SMALL,
          align="left", rounded=False)
    buttons = [str(p) for p in ids] + ["(blank)"]
    for i, label in enumerate(buttons):
        on = label == str(top)
        by = 32 + i * 24
        d.box(f"<b>{label}</b>" if on else label, sx + 6, by, sw - 12, 20,
              fill=BLUE if on else WHITE, stroke=BLUE if on else RULE,
              color=WHITE if on else INK, size=SMALL, rounded=False)
        if on:
            xl.emphasis(d, sx + 6, by, sw - 12, 20)
    slicer_bottom = 32 + len(buttons) * 24 + 4
    d.box("", sx, 0, sw, slicer_bottom, fill="none", stroke=GRAY, stroke_width=1.5,
          rounded=False)
    bottom = max(grid_bottom, slicer_bottom) + 12
    xl.status_bar(d, 0, bottom, 860, f"{counts[top]} of {total} records found")
    xl.emphasis(d, 2, bottom, 220, 24)
    d.text(f"<i>Sorted by PromotionID, then by DiscountAmount from largest to smallest; the first "
           f"{len(shown)} lines in view are shown. The shading comes from the rule =$J2&gt;0, and "
           "blue row numbers mark a filtered Table.</i>", 0, bottom + 32, 860, 40, size=SMALL,
           color=GRAY)
    return d


def fig_04_09() -> Diagram:
    d = Diagram("The Documentation Worksheet of the Analysis Workbook")
    code, name, pct, start, end, group = one(
        "SELECT PromotionCode, PromotionName, DiscountPct, EffectiveStartDate, EffectiveEndDate, "
        "ItemGroup FROM PromotionProgram WHERE PromotionID = 8")
    assert group == "Furniture", group
    tables = excel_tables()
    entries = [
        ("Workbook documentation", ""),
        ("Purpose", "Diagnose the decline in Furniture gross margin from the third to the fourth "
                    "quarter of fiscal 2026, as requested by the controller."),
        ("Source", f"{XLSX.name}: Tables {', '.join(tables[t] for t in QUERIES)}, imported with "
                   "Power Query."),
        ("Query steps", "Item keeps only items with a list price, and eleven columns. SalesInvoice "
                        "has its date columns set to the Date type. The other queries keep every "
                        "row and column."),
        ("Last refreshed", "Date of the last Refresh All"),
        ("Parameters", "ThresholdPercentile (Parameters!B3, an input validated between 0.5 and "
                       "0.99); LargeLineThreshold (Parameters!B4, a formula)."),
        ("Calculated columns", "SalesInvoiceLine: ListAmount =ROUND([@Quantity]*[@BaseListPrice],2); "
                               "DiscountAmount =ROUND([@Quantity]*[@UnitPrice]*[@Discount],2)."),
        ("Worksheets", "Documentation; SalesInvoice, SalesInvoiceLine, Item, and PromotionProgram "
                       "(data loaded by queries); Parameters; Analysis (control totals and the "
                       "summary grid)."),
        ("Conventions", "Blue font marks input cells; black font marks formulas."),
        ("Prepared by", "Staff accountant, with the date prepared"),
        ("Reviewed by", ""),
        ("Open questions", f"Promotion 8, the {name} ({code}, {pct:.0%}, {start} to {end}), has "
                           "the most promotion lines and the most discount dollars. Its dates "
                           "straddle the two quarters under review. Its effect on Furniture prices "
                           "in each quarter cannot yet be measured, because the invoice lines carry "
                           "no invoice date or item group."),
    ]
    for cx, w, label in zip([0, 36, 226], [36, 190, 630], ["", "A", "B"]):
        d.box(label, cx, 0, w, 22, fill=GRAY_TINT, stroke=RULE, color=GRAY, size=SMALL,
              rounded=False)
    y = 22
    for i, (label, entry) in enumerate(entries):
        lines = max(1, -(-len(entry) // 92))
        h = 24 if lines == 1 else 17 * lines + 8
        d.box(str(i + 1), 0, y, 36, h, fill=GRAY_TINT, stroke=RULE, color=GRAY, size=SMALL,
              rounded=False)
        d.box(f"<b>{esc(label)}</b>", 36, y, 190, h, fill=WHITE, stroke=RULE,
              size=HEAD if i == 0 else SMALL, align="left", valign="top", rounded=False)
        d.box(esc(entry), 226, y, 630, h, fill=WHITE, stroke=RULE, size=SMALL, align="left",
              valign="top", rounded=False)
        if label == "Open questions":
            xl.emphasis(d, 36, y, 820, h)
        y += h
    right = xl.sheet_tabs(d, 0, y + 8, ["Documentation", "SalesInvoice", "SalesInvoiceLine",
                                       "Item", "PromotionProgram", "Parameters", "Analysis"],
                          "Documentation")
    assert right <= 860, right
    d.text("<i>Outlined: the open question that the rest of Part II takes up.</i>", 0, y + 40, 860,
           20, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-04-01-range-vs-table": fig_04_01,
    "fig-04-02-power-query-navigator": fig_04_02,
    "fig-04-03-power-query-editor-item": fig_04_03,
    "fig-04-04-salesinvoiceline-table": fig_04_04,
    "fig-04-05-cell-reference-types": fig_04_05,
    "fig-04-06-analysis-worksheet": fig_04_06,
    "fig-04-07-analysis-workbook-layout": fig_04_07,
    "fig-04-08-promotion-slicer": fig_04_08,
    "fig-04-09-documentation-sheet": fig_04_09,
}
