"""Instructor figures of Chapter 5 (guides in facts/instructor/guides/chapter-05-data-preparation/)."""

from __future__ import annotations

import ctx
import excel as xl
import kit
from check_figures import text_width
from data import cardinality, relate, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, BODY, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc)

RIGHT, LEFT, TOP, BOTTOM = (1, 0.5), (0, 0.5), (0.5, 0), (0.5, 1)
STRAIGHT = "edgeStyle=none;"


# -- shared drawing helpers (copied from fig_04: Excel pieces) -------------------------------------------------------------

def _money(x: float) -> str:
    return f"{x:,.2f}"


def _general(x: float) -> str:
    """A number as Excel's General format shows it: 0.0 reads 0."""
    return f"{x:.15g}"


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow worksheet column shows it."""
    if text_width(text, size, bold) <= width - margin:
        return text
    while text and text_width(text + "…", size, bold) > width - margin:
        text = text[:-1]
    return text + "…"


def _fit(headers: list[str], rows: list[list[str]], pad: float = 20, filters: set[int] = frozenset(),
         floor: float = 40) -> list[float]:
    """Each column as wide as its bold header (plus room for a filter button) or its widest value, plus padding.
    A header written with <br> counts its longest line."""
    out = []
    for c, head in enumerate(headers):
        head_w = max(text_width(part, SMALL, True) for part in head.split("<br>"))
        need = max([head_w + (18 if c in filters else 0)] + [text_width(r[c], SMALL, False) for r in rows])
        out.append(round(max(floor, need + pad)))
    return out


def _spread(widths: list[float], total: float, first: int = 1) -> list[float]:
    """Share the spare room of a frame between the columns from index `first` on."""
    spare = total - sum(widths)
    assert spare >= 0, (widths, spare)
    n = len(widths) - first
    return [w + spare / n if i >= first else w for i, w in enumerate(widths)]


def _dropdown(d: Diagram, geo: tuple, active: bool = False) -> None:
    """The filter button of a Table header: a small white triangle; an active filter adds a bar under it (a funnel)."""
    hx, hy, hw, hh = geo
    d.vertex("", "triangle;direction=south;html=1;fillColor=#FFFFFF;strokeColor=none;", hx + hw - 16,
             hy + hh / 2 - (5 if active else 3.5), 9, 7)
    if active:
        d.box("", hx + hw - 13, hy + hh / 2 + 3, 3, 5, fill=WHITE, stroke=WHITE, rounded=False)


def _gap(d: Diagram, x: float, y: float, w: float, text: str, h: float = 24) -> float:
    """A band that stands for the rows of a long worksheet that the figure leaves out."""
    d.box(f"<i>{esc(text)}</i>", x, y, w, h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, rounded=False, dashed=True)
    return y + h


def _sheet(d: Diagram, x: float, y: float, letters: list[str], widths: list[float], rows: list[dict],
           number_color: str = GRAY, show_letters: bool = True, row_h: float = 22) -> dict:
    """A worksheet with a letter row and rows of any height.

    widths[0] is the row-number column; letters label the others.  A row is {"n": row number, "cells": [cell, ...],
    "h": height}, its cells taken in order from column A (a cell with span uses that many columns); a cell is a string
    or a dict: text, bold, italic, align ("left", "right", "center"), color, fill, stroke, html (a ready label), span
    (columns the text overflows across, as Excel text does when the cells beside it are empty), clip (False keeps a
    long text whole), filter (True draws the filter button, "active" a funnel), bar (0..1, a data bar behind the
    value).  Returns {(row index, column): (x, y, w, h)} and "bottom"."""
    xs = [x]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    top = 22 if show_letters else 0
    if show_letters:
        for cx, w, letter in zip(xs, widths, ["", *letters]):
            d.box(esc(letter), cx, y, w, 22, fill=GRAY_TINT, stroke=RULE, color=GRAY, size=SMALL, rounded=False)
    geo: dict = {}
    ry = y + top
    for i, row in enumerate(rows):
        h = row.get("h", row_h)
        d.box(esc(row["n"]), xs[0], ry, widths[0], h, fill=GRAY_TINT, stroke=RULE, color=row.get("number_color", number_color),
              size=SMALL, rounded=False)
        cells = list(row["cells"])
        c = idx = 0                                   # cells are taken in order; a spanning cell uses several columns
        while c < len(widths) - 1:
            cell = cells[idx] if idx < len(cells) else ""
            idx += 1
            if isinstance(cell, str):
                cell = {"text": cell}
            span = cell.get("span", 1)
            cx = xs[c + 1]
            cw = sum(widths[c + 1:c + 1 + span])
            text = cell.get("text", "")
            numeric = text[:1].isdigit() or text[:1] in "-$" and text[1:2].isdigit()
            align = cell.get("align", "right" if numeric else "left")
            bold = cell.get("bold", False)
            if "html" in cell:
                label = cell["html"]
            else:
                shown = _clip(text, cw, bold=bold, margin=cell.get("margin", 22 if cell.get("filter") else 14)) \
                    if cell.get("clip", True) else text
                label = esc(shown)
                if bold:
                    label = f"<b>{label}</b>"
                if cell.get("italic"):
                    label = f"<i>{label}</i>"
            d.box(label, cx, ry, cw, h, fill=cell.get("fill", WHITE), stroke=cell.get("stroke", RULE),
                  color=cell.get("color", INK), size=SMALL, rounded=False, align=align, valign=cell.get("valign", "middle"))
            geo[(i, c)] = (cx, ry, cw, h)
            if cell.get("filter"):
                _dropdown(d, geo[(i, c)], active=cell["filter"] == "active")
            c += span
        ry += h
    geo["bottom"] = ry
    return geo


def _header(text: str, **kw) -> dict:
    """A Table header cell: blue fill, white bold text."""
    return dict(text=text, bold=True, fill=BLUE, stroke=BLUE, color=WHITE, align="left", **kw)


def _head(text: str, align: str = "left", html: str | None = None) -> dict:
    """A heading cell of a plain grid: light blue, bold."""
    return dict(html=f"<b>{html}</b>", fill=BLUE_TINT, align=align) if html else \
        dict(text=text, bold=True, fill=BLUE_TINT, align=align)


def _formula_bar(d: Diagram, x: float, y: float, w: float, name: str, formula_html: str, h: float = 28) -> None:
    """The Name Box, the fx label and a formula bar."""
    d.box(esc(name), x, y, 90, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<i>fx</i>", x + 94, y, 30, 28, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(formula_html, x + 128, y, w - 128, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)


def _hidden_text(visible: list[str], n: int) -> str:
    """'A to I, L and N': the letters among a worksheet's first n columns that the figure hides."""
    letters = [chr(65 + i) for i in range(n) if chr(65 + i) not in visible]
    runs: list[list[str]] = []
    for letter in letters:
        if runs and ord(letter) == ord(runs[-1][-1]) + 1:
            runs[-1].append(letter)
        else:
            runs.append([letter])
    parts = [part for run in runs for part in ([f"{run[0]} to {run[-1]}"] if len(run) > 2 else run)]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def _mark(d: Diagram, x: float, y: float, w: float, h: float, color: str) -> str:
    """An outline like xl.emphasis in another color (a blue outline would vanish on a blue Table header)."""
    left, top = max(0, x - 2), max(0, y - 2)
    return d.outline(left, top, min(860, x + w + 2) - left, y + h + 2 - top, color, width=2.5, front=True)


def _swatch(d: Diagram, x: float, y: float, fill: str, stroke: str = GRAY, size: float = 14) -> None:
    d.box("", x, y, size, size, fill=fill, stroke=stroke, rounded=False)


def _word(n: int) -> str:
    words = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    return words[n] if 0 <= n < len(words) else f"{n:,}"


def _demo_order(data) -> dict:
    """An order of the fiscal year with exactly two shipments on different dates (and the fewest invoices of such orders),
    with the first of its invoices and that invoice's customer."""
    row = data.q("SELECT o.SalesOrderID, o.OrderNumber, (SELECT COUNT(*) FROM SalesInvoice i WHERE i.SalesOrderID = o.SalesOrderID) "
                 "FROM SalesOrder o WHERE substr(o.OrderDate, 1, 4) = ? "
                 "AND (SELECT COUNT(*) FROM Shipment s WHERE s.SalesOrderID = o.SalesOrderID) = 2 "
                 "AND (SELECT COUNT(DISTINCT ShipmentDate) FROM Shipment s WHERE s.SalesOrderID = o.SalesOrderID) = 2 "
                 "AND (SELECT COUNT(*) FROM SalesInvoice i WHERE i.SalesOrderID = o.SalesOrderID) > 0 "
                 "ORDER BY 3, o.SalesOrderID LIMIT 1", str(data.C))
    assert row, "some order of the fiscal year has two shipments on different dates and an invoice"
    oid, number, n_invoices = row[0]
    ships = data.q("SELECT ShipmentNumber, ShipmentDate FROM Shipment WHERE SalesOrderID = ? ORDER BY ShipmentDate", oid)
    invoice = data.q("SELECT i.InvoiceNumber, c.CustomerName FROM SalesInvoice i JOIN Customer c ON c.CustomerID = i.CustomerID "
                     "WHERE i.SalesOrderID = ? ORDER BY i.InvoiceNumber LIMIT 1", oid)[0]
    return dict(id=oid, number=number, ships=ships, invoice=invoice[0], customer=invoice[1], n_invoices=n_invoices)


# -- IF-05-0-A: which way a lookup may follow a relationship ------------------------------------------------------------------

def if_05_0_a() -> Diagram:
    """SalesInvoiceLine, SalesInvoice and SalesOrder with XLOOKUP toward the one side; Shipment below SalesOrder."""
    data = ctx.data()
    t2 = ctx.values("ch05.chapter")["t2"]
    tables = {"SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "LineTotal"],
              "SalesInvoice": ["SalesInvoiceID", "SalesOrderID", "InvoiceDate"],
              "SalesOrder": ["SalesOrderID", "OrderDate"], "Shipment": ["ShipmentID", "SalesOrderID", "ShipmentDate"]}
    for name, cols in tables.items():
        require_columns(name, cols)
    ends = {"line": cardinality("SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID"),
            "invoice": cardinality("SalesOrder", "SalesOrderID", "SalesInvoice", "SalesOrderID"),
            "ship": cardinality("SalesOrder", "SalesOrderID", "Shipment", "SalesOrderID")}
    many = {"ERoneToMany", "ERzeroToMany"}
    assert all(parent == "ERmandOne" and child in many for parent, child in ends.values()), ends
    assert t2["multi_ship"] > 0 and t2["multi_invoice"] > 0, "an order can have several shipments and several invoices"
    demo = _demo_order(data)
    (n1, d1), (n2, d2) = demo["ships"]
    d = Diagram("Which Way a Lookup May Follow a Relationship")
    tw, row_h, head_h = 200, 24, 30
    x0, x1, x2 = 0, 330, 660
    y0 = 84                                          # the top of SalesInvoiceLine
    # The tables step down by one row, so each foreign key sits level with the key it points to.
    line = d.table("SalesInvoiceLine", x0, y0, [("PK", "SalesInvoiceLineID"), ("FK", "SalesInvoiceID"), ("", "LineTotal")], w=tw)
    inv = d.table("SalesInvoice", x1, y0 + row_h, [("PK", "SalesInvoiceID"), ("FK", "SalesOrderID"), ("", "InvoiceDate")], w=tw)
    order = d.table("SalesOrder", x2, y0 + 2 * row_h, [("PK", "SalesOrderID"), ("", "OrderDate")], w=tw)
    relate(d, "SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID", inv.rows["SalesInvoiceID"],
           line.rows["SalesInvoiceID"], exit=LEFT, entry=RIGHT)
    relate(d, "SalesOrder", "SalesOrderID", "SalesInvoice", "SalesOrderID", order.rows["SalesOrderID"],
           inv.rows["SalesOrderID"], exit=LEFT, entry=RIGHT)
    ly1, ly2 = y0 + row_h + head_h + row_h / 2, y0 + 2 * row_h + head_h + row_h / 2       # the two relationship lines
    for label, lx, ly, align in (("many", x0 + tw + 6, ly1, "left"), ("one", x1 - 42, ly1, "right"),
                                 ("many", x1 + tw + 6, ly2, "left"), ("one", x2 - 42, ly2, "right")):
        d.text(f"<i>{label}</i>", lx, ly - 30, 36, 18, size=SMALL, color=GRAY, align=align)
    # The lookups run toward the one side: from the foreign key's table over the top to the table it points to.
    peak = 44
    d.edge(line.id, inv.id, end="blockThin", color=TEAL, width=2.5, exit=(0.5, 0), entry=(0.25, 0),
           points=[(x0 + tw / 2, peak), (x1 + tw * 0.25, peak)])
    d.edge(inv.id, order.id, end="blockThin", color=TEAL, width=2.5, exit=(0.75, 0), entry=(0.5, 0),
           points=[(x1 + tw * 0.75, peak), (x2 + tw / 2, peak)])
    d.text("<b>XLOOKUP</b> by SalesInvoiceID<br>many-to-one: one match", x0 + tw / 2 - 20, peak - 38, x1 + tw * 0.25 - x0 - tw / 2 + 40,
           36, size=SMALL, align="center", valign="bottom")
    d.text("<b>XLOOKUP</b> by SalesOrderID<br>many-to-one: one match", x1 + tw * 0.75 - 20, peak - 38,
           x2 + tw / 2 - x1 - tw * 0.75 + 40, 36, size=SMALL, align="center", valign="bottom")
    # Below SalesOrder: Shipment, with the relationship toward the many side and the lookup that does not work.
    ship_y = order.bottom + 76
    ship = d.table("Shipment", x2, ship_y, [("PK", "ShipmentID"), ("FK", "SalesOrderID"), ("", "ShipmentDate")], w=tw)
    relate(d, "SalesOrder", "SalesOrderID", "Shipment", "SalesOrderID", order.id, ship.id, exit=(0.2, 1), entry=(0.2, 0))
    d.edge(order.id, ship.id, end="blockThin", color=CORAL, width=2.5, exit=(0.72, 1), entry=(0.72, 0), meta=STRAIGHT)
    mid = (order.bottom + ship_y) / 2
    d.box("<b><s>XLOOKUP</s></b>", x2 + tw * 0.72 - 44, mid - 11, 88, 22, fill=WHITE, stroke=WHITE, color=CORAL, size=SMALL,
          rounded=False)
    d.text("<b>SalesOrderID</b><br>one-to-many", x2 + tw * 0.2 - 124, mid - 17, 118, 34, size=SMALL, align="right",
           valign="middle")
    # Two shipments of one order, as rows under the table.
    gy = ship.bottom + 20
    d.text(f"<i>Order {esc(demo['number'])}: two shipments</i>", x2 - 140, gy - 20, tw + 140, 18, size=SMALL, color=GRAY,
           align="right")
    d.grid(x2, gy, ["SalesOrderID", "ShipmentDate"], [100, 100], [(str(demo["id"]), d1), (str(demo["id"]), d2)], row_h=24,
           header_size=SMALL)
    # The note beside Shipment.
    note_bottom = kit.callout(d, "<b><s>XLOOKUP</s></b> returns the first shipment and says nothing about the other. Use "
                                 "<b>MINIFS, SUMIFS or COUNTIFS</b> instead of a lookup: they read every shipment of the order.",
                              x1, ship_y + 4, 300, color="coral")
    # The legend (Chapter 3's notation, and the lookups).
    ky = ship_y + 4
    key_w = 310
    items = [("line", GRAY, "A relationship inside one table group"),
             ("ends", GRAY, "Line ends: a bar means one, a crow's foot many, a circle zero"),
             ("arrow", TEAL, "A lookup toward the one side"),
             ("arrow", CORAL, "A lookup toward the many side")]
    d.box("", x0, ky, key_w, 4 * 30 + 12, fill=GRAY_TINT, stroke=RULE)
    for i, (kind, color, label) in enumerate(items):
        cy = ky + 22 + 30 * i
        if kind == "ends":
            a, b = d.anchor(x0 + 12, cy), d.anchor(x0 + 52, cy)
            d.edge(a, b, start=ends["line"][0], end=ends["line"][1], color=GRAY, meta=STRAIGHT)
        else:
            d.line_sample(x0 + 12, cy, 40, color=color, end="blockThin" if kind == "arrow" else "none",
                          width=2.5 if kind == "arrow" else 1.5)
        label_h = 17 * kit.lines_for(label, key_w - 70, SMALL) + 6
        d.text(esc(label), x0 + 62, cy - label_h / 2, key_w - 70, label_h, size=SMALL, valign="middle")
    bottom = max(note_bottom, ky + 132, gy + 3 * 24) + 14
    d.text(f"<i>The four tables are all in the Order-to-Cash group, so every relationship is a solid gray line. A lookup from "
           f"a line to its invoice, or from an invoice to its order, finds exactly one row. An order can have several "
           f"invoices ({t2['multi_invoice']:,} do) and several shipments ({t2['multi_ship']:,} do), so a lookup of the "
           f"order's shipment date returns the first of them, {d1}, and not {d2}, without a message.</i>",
           0, bottom, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-05-0-B: the row-count test for a merge ----------------------------------------------------------------------------------

def if_05_0_b() -> Diagram:
    """A left outer merge with Customer keeps the row count; a merge with Shipment on SalesOrderID multiplies it."""
    data = ctx.data()
    chapter = ctx.values("ch05.chapter")
    t1, t2 = chapter["t1"], chapter["t2"]
    invoices, fanout = t1["invoices"], t2["fanout"]
    with_customer = data.one("SELECT COUNT(*) FROM SalesInvoice s LEFT JOIN Customer c ON c.CustomerID = s.CustomerID")
    with_shipment = data.one("SELECT COUNT(*) FROM SalesInvoice s LEFT JOIN Shipment h ON h.SalesOrderID = s.SalesOrderID")
    n_customers, distinct_customers = data.q("SELECT COUNT(*), COUNT(DISTINCT CustomerID) FROM Customer")[0]
    n_ships, ship_orders = data.q("SELECT COUNT(*), COUNT(DISTINCT SalesOrderID) FROM Shipment")[0]
    assert with_customer == invoices and with_shipment == fanout and fanout > invoices, (with_customer, with_shipment)
    assert n_customers == distinct_customers and n_ships > ship_orders, "each customer key once, shipment keys repeat"
    demo = _demo_order(data)
    assert len(demo["ships"]) == 2
    d = Diagram("The Row-Count Test for a Merge")
    pw, gap = 415, 30
    ratio = fanout / invoices
    box_h, after_h = 64, round(64 * min(ratio, 2.2))
    panels = [
        (0, "Merge SalesInvoice with Customer on CustomerID", invoices, with_customer, TEAL_TINT, TEAL, box_h,
         f"<b>CustomerID</b> in Customer: each key appears once<br>{n_customers:,} rows, {distinct_customers:,} different keys",
         ["InvoiceNumber", "CustomerName"], [[demo["invoice"], demo["customer"]]], [False, False],
         "<b>Count unchanged, no row repeated</b>", "teal"),
        (pw + gap, "Merge SalesInvoice with Shipment on SalesOrderID", invoices, with_shipment, CORAL_TINT, CORAL, after_h,
         f"<b>SalesOrderID</b> in Shipment: the key repeats in the second table<br>{n_ships:,} rows for {ship_orders:,} "
         f"orders; {t2['multi_ship']:,} orders have several",
         ["InvoiceNumber", "ShipmentDate"], [[demo["invoice"], d1] for _, d1 in demo["ships"]], [True, False],
         "<b>Count grew, the key repeats</b>", "coral"),
    ]
    sketch_top = 48 + after_h + 14 + 52 + 14 + 20
    verdict_y = sketch_top + 24 * 3 + 16
    for px, title, before, after, fill, stroke, a_h, key_text, heads, rows, repeat, verdict, tone in panels:
        d.header_box(esc(title), px, 0, pw, 32, size=SMALL)
        b = d.box(f"<b style=\"font-size:22px\">{before:,}</b><br>rows of SalesInvoice", px, 48, 140, box_h, fill=BLUE_TINT, stroke=BLUE,
                  stroke_width=1.5, size=SMALL)
        a = d.box(f"<b style=\"font-size:22px\">{after:,}</b><br>rows after the merge" + (f"<br><b>+{after - before:,}</b> rows" if after != before else ""),
                  px + pw - 140, 48, 140, a_h, fill=fill, stroke=stroke, stroke_width=1.5, size=SMALL)
        d.arrow(b, a, exit=RIGHT, entry=(0, (box_h / 2) / a_h), label="left outer merge")
        ky = 48 + max(p[6] for p in panels) + 14
        kit.callout(d, key_text, px, ky, pw, color="gray")
        d.text(f"<i>One invoice, {esc(demo['invoice'])}, after the merge</i>", px, sketch_top - 24, pw, 18, size=SMALL, color=GRAY)
        for c, (head, width) in enumerate(zip(heads, [pw / 2, pw / 2])):
            d.box(f"<b>{head}</b>", px + c * width, sketch_top, width, 24, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL,
                  rounded=False, align="left")
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                hot = repeat[c] and len(rows) > 1
                d.box(esc(value), px + c * pw / 2, sketch_top + 24 * (r + 1), pw / 2, 24, fill=AMBER_TINT if hot else WHITE,
                      stroke=AMBER if hot else RULE, size=SMALL, rounded=False, align="left")
        fill_v, stroke_v = kit.tint(tone)
        d.box(verdict, px, verdict_y, pw, 40, fill=fill_v, stroke=stroke_v, stroke_width=1.5, size=BODY)
    d.text(f"<i>Both merges are left outer merges, so no invoice is dropped. The row count after loading tests repetition, "
           f"so compare it with the {invoices:,} invoices. It cannot show that every invoice found a match, because an invoice "
           f"without one stays in the result with empty columns, and a left anti merge that returns no rows tests that. Merging "
           f"on a key that repeats in the second table gives the invoice one row for each match, here one for each shipment of "
           f"its order, and every total on the invoice then counts twice or more. Amber cells: the invoice number repeated by "
           f"the merge.</i>", 0, verdict_y + 54, 860, 72, size=SMALL, color=GRAY)
    return d



# -- IF-05-1-A: net Furniture revenue by quarter ------------------------------------------------------------------------------

def if_05_1_a() -> Diagram:
    """Ex 5.1: the quarterly grid with its checks, and the credits for invoices of earlier years beneath it."""
    data = ctx.data()
    g = ctx.values("ch05.g1")
    n = ctx.values("ch05.ex1")
    gross, credits, net = n["gross"], n["credits"], n["net"]
    periods, year = g["periods"], g["y"]
    unmatched = data.one("SELECT COUNT(*) FROM CreditMemoLine cl LEFT JOIN CreditMemo cm ON cm.CreditMemoID = cl.CreditMemoID "
                         "LEFT JOIN Item i ON i.ItemID = cl.ItemID WHERE cm.CreditMemoID IS NULL OR i.ItemID IS NULL")
    assert unmatched == 0 and len(periods) == 4
    total_gross, total_credit = round(sum(gross), 2), round(sum(c["amount"] for c in credits), 2)
    assert abs(total_credit - n["credit_total"]) < 0.005 and abs(sum(net) - (total_gross - total_credit)) < 0.01
    by_invoice = g["by_invoice"]                        # credits of the year by their invoice's quarter; [0] earlier years
    moved = [round(gross[k] - by_invoice[k + 1], 2) for k in range(4)]
    assert moved[2] == g["alt3"] and moved[3] == g["alt4"] and g["early_lines"] == n["earlier"]
    assert abs(sum(by_invoice) - total_credit) < 0.01
    d = Diagram("The Ex 5.1 Worksheet: Net Furniture Revenue by Quarter")
    widths = [28, 340, 96, 96, 96, 96, 108]
    letters = list("ABCDEF")
    money = lambda v: _money(v)
    formula = "=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],\"Furniture\",InvoiceLines[Period],B$4)"
    _formula_bar(d, 0, 0, 860, "B5", esc(formula))

    def row(label: str, values: list[str], total: str | None, bold: bool = False) -> list:
        cells = [dict(text=label, bold=bold)] + [dict(text=v, bold=bold) for v in values]
        return cells + ([dict(text=total, bold=bold)] if total is not None else [])

    rows = [
        dict(n="1", cells=[dict(text="Exercise 5.1: Net Furniture Revenue by Quarter", bold=True, span=6, clip=False)]),
        dict(n="2", cells=["Fiscal year", dict(text=year, color=BLUE)]),
        dict(n="3", cells=[]),
        dict(n="4", cells=[_head("Measure")] + [dict(text=p, bold=True, fill=BLUE_TINT, color=BLUE, align="right") for p in periods]
             + [_head("Total", "right")]),
        dict(n="5", cells=row("Furniture revenue billed", [money(v) for v in gross], money(total_gross))),
        dict(n="6", cells=row("Furniture credit memo lines", [money(c["amount"]) for c in credits], money(total_credit))),
        dict(n="7", cells=row("Net Furniture revenue", [money(v) for v in net], money(round(sum(net), 2)), bold=True)),
        dict(n="8", cells=[]),
        dict(n="9", cells=row("Credit memo lines (count)", [f"{c['lines']:,}" for c in credits],
                              f"{sum(c['lines'] for c in credits):,}")),
        dict(n="10", cells=row("Credits as a share of revenue billed", [f"{c['amount'] / gr:.2%}" for c, gr in zip(credits, gross)],
                               f"{total_credit / total_gross:.2%}")),
        dict(n="11", cells=["Credit memo lines not matched", dict(text="0")]),
        dict(n="12", cells=[]),
        dict(n="13", cells=[dict(text="Credit memos for invoices of earlier years", bold=True, span=6, clip=False)]),
        dict(n="14", cells=[f"Credit memos of {year} for invoices of earlier years", dict(text=f"{g['early_memos']:,}")]),
        dict(n="15", cells=["Furniture credits they carry", dict(text=money(g["early_furn"]))]),
        dict(n="16", cells=row("Net revenue, credits moved to their invoice's quarter", [money(v) for v in moved],
                               money(round(sum(moved), 2)))),
    ]
    geo = _sheet(d, 0, 40, letters, widths, rows)
    xl.select(d, *geo[(4, 1)])
    zero = geo[(10, 1)]
    xl.emphasis(d, *zero)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["InvoiceLines", "Ex 5.1", "Ex 5.1 CreditMemo", "Ex 5.1 CreditMemoLine"], "Ex 5.1")
    d.text(f"<i>Selected: B5, whose formula shows in the bar; B6 uses the same SUMIFS on CreditMemoLine. Outlined: the count of "
           f"lookups not matched, zero. Net revenue is billed less credits, in bold. The last row moves each of the {year} "
           f"credits to the quarter of its invoice and leaves out the {g['early_memos']} credit memos for invoices of earlier "
           f"years, all dated in January ({money(g['early_furn'])} of Furniture credits).</i>", 0, bottom + 34, 860, 52,
           size=SMALL, color=GRAY)
    return d


# -- IF-05-2-A: the flagged invoices ---------------------------------------------------------------------------------------------

def if_05_2_a() -> Diagram:
    """Ex 5.2: the nine invoices flagged by either test, then Tutorial 2.1's list of invoices dated before shipment."""
    g = ctx.values("ch05.g2")
    n = ctx.values("ch05.ex2")
    nine = g["nine"]
    assert all(r["prefix"] != r["before"] for r in nine), "no invoice is flagged by both tests"
    assert n["missed"] == [] and len(nine) == g["n_prefix"] + g["n_before"]
    shipped = sorted(nine, key=lambda r: r["number"])
    first = [r for r in shipped if r["before"]]
    second = [r for r in shipped if r["prefix"]]
    # sorted by number: the two groups are each one run of rows (checked, since the outlines assume it)
    flags = [r["prefix"] for r in shipped]
    changes = sum(1 for a, b in zip(flags, flags[1:]) if a != b)
    assert changes == 1, "each test's invoices form one block in the list sorted by number"
    d = Diagram("The Ex 5.2 Worksheet: the Invoices Flagged by Either Test and Tutorial 2.1's List")
    heads = ["InvoiceNumber", "InvoiceDate", "OrderDate", "NumberYear", "NumberYearMatches", "BeforeOrder", "In Tutorial<br>2.1 list"]
    body = [[r["number"], r["date"], r["order"], r["number"][3:7], "FALSE" if r["prefix"] else "TRUE", "TRUE" if r["before"] else "FALSE",
             "TRUE"] for r in shipped]
    widths = [28] + _fit(heads, body, pad=20)
    widths = _spread(widths, 860)
    letters = list("ABCDEFG")
    rows = [dict(n="1", cells=[dict(text="Exercise 5.2: Testing Document Numbers Against Dates", bold=True, span=7, clip=False)]),
            dict(n="2", cells=[])]
    counts = [("Invoices whose number year differs from the date", g["n_prefix"]),
              ("Invoices dated before their order", g["n_before"]),
              ("Invoices flagged by either test", g["n_prefix"] + g["n_before"]),
              ("Tutorial 2.1 invoices that neither test flags", len(n["missed"]))]
    for k, (label, value) in enumerate(counts):
        rows.append(dict(n=str(3 + k), cells=[dict(text=label, span=4, clip=False), dict(text=f"{value:,}", bold=True)]))
    rows.append(dict(n="7", cells=[]))
    rows.append(dict(n="8", cells=[dict(text="Flagged by either test, sorted by number", bold=True, span=7, clip=False)]))
    head_align = {"InvoiceDate": "right", "OrderDate": "right", "NumberYear": "right", "NumberYearMatches": "center",
                  "BeforeOrder": "center", "In Tutorial<br>2.1 list": "center"}
    head_row = dict(n="9", h=38, cells=[_head("", html=h, align=head_align.get(h, "left")) for h in heads])
    rows.append(head_row)
    first_row = len(rows)
    for k, (r, values) in enumerate(zip(shipped, body)):
        cells = []
        for c, v in enumerate(values):
            cell = dict(text=v, align="left" if c == 0 else "right" if c in (1, 2, 3) else "center")
            if c == 4 and r["prefix"]:
                cell.update(fill=CORAL_TINT, bold=True)
            elif c == 5 and r["before"]:
                cell.update(fill=TEAL_TINT, bold=True)
            cells.append(cell)
        rows.append(dict(n=str(10 + k), cells=cells))
    rows.append(dict(n=str(10 + len(shipped)), cells=[]))
    title_n = 11 + len(shipped)
    rows.append(dict(n=str(title_n), cells=[dict(text="Tutorial 2.1: invoices dated before their first shipment", bold=True, span=7, clip=False)]))
    rows.append(dict(n=str(title_n + 1), h=38, cells=[_head("", html="Tutorial 2.1<br>InvoiceNumber"), _head("", html="InvoiceDate"),
                                                      _head("", html="First<br>ShipmentDate")]))
    for k, r in enumerate(shipped):
        rows.append(dict(n=str(title_n + 2 + k), cells=[r["number"], r["date"], r["ship"]]))
    geo = _sheet(d, 0, 0, letters, widths, rows)
    # The two groups of flagged invoices: each test's rows in one outline.
    def block(rows_idx: list[int], cols: tuple[int, int], color: str) -> None:
        x0, y0, _, _ = geo[(rows_idx[0], cols[0])]
        x1, y1, w1, h1 = geo[(rows_idx[-1], cols[1])]
        d.outline(x0 + 1.5, y0 + 1.5, x1 + w1 - x0 - 3, y1 + h1 - y0 - 3, color, width=2.5, front=True)
    prefix_idx = [first_row + k for k, r in enumerate(shipped) if r["prefix"]]
    before_idx = [first_row + k for k, r in enumerate(shipped) if r["before"]]
    block(before_idx, (0, 6), TEAL)
    block(prefix_idx, (0, 6), CORAL)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["SalesInvoice", "SalesOrder", "Ex 5.2"], "Ex 5.2")
    # The key.
    ky = bottom + 34
    d.box("", 0, ky + 3, 14, 14, fill=CORAL_TINT, stroke=CORAL, stroke_width=2, rounded=False)
    d.text(f"NumberYearMatches is FALSE: the number year differs from the date ({len(prefix_idx)} invoices)", 22, ky, 700, 20,
           size=SMALL, valign="middle")
    d.box("", 0, ky + 27, 14, 14, fill=TEAL_TINT, stroke=TEAL, stroke_width=2, rounded=False)
    d.text(f"BeforeOrder is TRUE: dated before the order ({len(before_idx)} invoices)", 22, ky + 24, 700, 20, size=SMALL,
           valign="middle")
    d.text(f"<i>Row 2 and row 7 are blank, and the four counts sit above the list. The two outlined groups share no invoice, so "
           f"together they list the {len(shipped)} invoices that Tutorial 2.1 found, which are typed below as values with the "
           f"first shipment date of each order: each test finds only part of them. Every flagged invoice is dated before its "
           f"first shipment.</i>", 0, ky + 52, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-05-3-A: the product mix grid ---------------------------------------------------------------------------------------------

def if_05_3_a() -> Diagram:
    """Ex 5.3: the grid of eight product types with the threshold lowered to one point, so four rows are shaded."""
    g = ctx.values("ch05.g3")
    rows_data = g["rows"]
    threshold = 0.01
    over = [r for r in rows_data if abs(r["pts"]) > 100 * threshold]
    assert len(over) == g["one_n"] and [r["code"] for r in over] == g["one"]
    assert abs(sum(r["share3"] for r in rows_data) - 1) < 1e-9 and abs(sum(r["pts"] for r in rows_data)) < 1e-6
    d = Diagram("The Ex 5.3 Worksheet: the Product Mix with the Threshold at One Point")
    heads = ["Code", "Product type", "Revenue", "Quantity", "Revenue", "Quantity", "Q3 share", "Q4 share", "Change in<br>share"]
    letters = list("ABCDEFGHI")
    body = [[r["code"], r["name"], _money(r["rev3"]), f"{r['q3']:,.2f}", _money(r["rev4"]), f"{r['q4']:,.2f}",
             f"{r['share3']:.1%}", f"{r['share4']:.1%}", f"{r['pts']:+.1f}%"] for r in rows_data]
    total = ["Total", "", _money(g["t3"]), f"{g['qty3']:,.2f}", _money(g["t4"]), f"{g['qty4']:,.2f}", "100.0%", "100.0%", "0.0%"]
    labels = ["Threshold", "Highlighted", "Furniture lines", "Fractional qty"]
    widths = [28] + _fit(heads, body + [total], pad=20)
    widths[1] = max(widths[1], round(max(text_width(t, SMALL, False) for t in labels) + 20))
    widths = _spread(widths, 860, first=2)
    first_data = 4
    cells = [dict(n="1", cells=[dict(text="Exercise 5.3: The Furniture Product Mix", bold=True, span=9, clip=False)]),
             dict(n="2", cells=[dict(text="", span=2), dict(text=g["q3"], bold=True, color=BLUE, span=2, align="center", fill=BLUE_TINT),
                                dict(text=g["q4"], bold=True, color=BLUE, span=2, align="center", fill=BLUE_TINT),
                                dict(text="Share of the Furniture total", bold=True, span=3, align="center", fill=BLUE_TINT)]),
             dict(n="3", h=38, cells=[_head("", html=h, align="left" if i < 2 else "right") for i, h in enumerate(heads)])]
    for k, (r, values) in enumerate(zip(rows_data, body)):
        shaded = abs(r["pts"]) > 100 * threshold
        cells.append(dict(n=str(first_data + k), cells=[
            dict(text=v, align="left" if c < 2 else "right", fill=AMBER_TINT if shaded else WHITE, bold=shaded and c == 8)
            for c, v in enumerate(values)]))
    last = first_data + len(rows_data)
    cells.append(dict(n=str(last), cells=[dict(text=v, bold=True, align="left" if c < 2 else "right") for c, v in enumerate(total)]))
    cells.append(dict(n=str(last + 1), cells=[]))
    cells.append(dict(n=str(last + 2), cells=["Threshold", dict(text=f"{threshold:.2%}", color=BLUE)]))
    cells.append(dict(n=str(last + 3), cells=["Highlighted", dict(text=str(len(over)), bold=True)]))
    cells.append(dict(n=str(last + 4), cells=["Furniture lines", dict(text=f"{g['lines']:,}")]))
    cells.append(dict(n=str(last + 5), cells=["Fractional qty", dict(text=f"{g['fractional']:,}")]))
    geo = _sheet(d, 0, 0, letters, widths, cells)
    count_cell = geo[(len(cells) - 3, 1)]
    thr_cell = geo[(len(cells) - 4, 1)]
    xl.emphasis(d, thr_cell[0], thr_cell[1], thr_cell[2], count_cell[1] + count_cell[3] - thr_cell[1])
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["InvoiceLines", "Ex 5.1", "Ex 5.2", "Ex 5.3"], "Ex 5.3")
    ky = bottom + 34
    _swatch(d, 0, ky + 3, AMBER_TINT)
    d.text(f"Rule on A{first_data}:I{last - 1}, A{first_data} active: <b>=ABS($I{first_data})&gt;$B${last + 2}</b>", 22, ky, 500, 20,
           size=SMALL, valign="middle")
    d.text(f"<i>Rows 1 and 2 hold the title and the period labels. With the threshold typed as one point instead of two, "
           f"{_word(len(over))} product types ({', '.join(g['one'])}) change their share by more than one point, the falls and the rises "
           f"alike, so their rows are shaded across all nine columns and B{last + 3} counts them. At two points no row is "
           f"shaded and the count is zero, which the rule alone cannot tell from a rule that never fires. Outlined: the "
           f"threshold and the count.</i>", 0, ky + 28, 860, 70, size=SMALL, color=GRAY)
    return d


# -- IF-05-4-A: the promotion table ---------------------------------------------------------------------------------------------

def if_05_4_a() -> Diagram:
    """Ex 5.4: the lag of all invoices above the nine promotions with the share invoiced after the end date."""
    g = ctx.values("ch05.g4")
    n = ctx.values("ch05.ex4")
    promos = g["promos"]
    assert len(promos) == 9 == len(n["promos"]) and n["invoices"] > 0
    flagged = [p for p in promos if p["kind"]]
    assert [p["id"] for p in flagged] == [p["id"] for p in promos if p["share"] == 1.0] and len(flagged) == g["n_flagged"]
    others = [p for p in promos if not p["kind"]]
    assert all(0.2 < p["share"] < 0.6 for p in others)
    mean, median, p90 = n["mean"], float(n["median"].replace(",", "")), float(n["p90"].replace(",", ""))
    assert mean > median
    d = Diagram("The Ex 5.4 Worksheet: the Lag of All Invoices and the Promotions")
    heads = ["PromotionID", "PromotionCode", "EffectiveStartDate", "EffectiveEndDate", "Invoice lines", "Invoiced after<br>end date",
             "Share after<br>end date"]
    body = [[str(p["id"]), p["code"], p["start"], p["end"], f"{p['lines']:,}", f"{p['after']:,}", f"{p['share']:.0%}"] for p in promos]
    widths = _spread([28] + _fit(heads, body, pad=20), 860)
    letters = list("ABCDEFG")
    lag = [("Invoices", f"{n['invoices']:,}"), ("Average lag, days", f"{mean:,.1f}"), ("Median lag, days", n["median"]),
           ("90th percentile, days", n["p90"])]
    rows = [dict(n="3", cells=[dict(text="Days from order to invoice, all invoices", bold=True, span=3, clip=False)])]
    for k, (label, value) in enumerate(lag):
        rows.append(dict(n=str(4 + k), cells=[dict(text=label, span=2, clip=False, align="left"),
                                              dict(text=value, bold=k in (1, 2))]))
    geo_top = _sheet(d, 0, 0, letters, widths, rows)
    y = _gap(d, 0, geo_top["bottom"], 860, "rows 8 to 18 hold the summary by quarter; not shown")
    table = [dict(n="19", h=38, cells=[_head("", html=h, align="right" if i >= 4 else "left") for i, h in enumerate(heads)])]
    for k, (p, values) in enumerate(zip(promos, body)):
        wrong = bool(p["kind"])
        table.append(dict(n=str(20 + k), cells=[
            dict(text=v, align="left" if c < 4 else "right", fill=CORAL_TINT if wrong and c in (2, 3) else WHITE,
                 bold=wrong and c in (2, 3, 6)) for c, v in enumerate(values)]))
    geo = _sheet(d, 0, y, [], widths, table, show_letters=False)
    for k, p in enumerate(promos):
        if p["kind"]:
            x0, y0, _, h = geo[(1 + k, 0)]
            _mark(d, x0, y0, 860 - x0 - 2, h, CORAL)
    ay = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, ay, ["SalesInvoice", "SalesOrder", "Ex 5.3", "Ex 5.4"], "Ex 5.4")
    notes = "; ".join(f"promotion {p['id']} {p['kind']}" for p in flagged)
    d.text(f"<i>Rows 1 and 2 are scrolled out of view. The average lag is above the median: a minority of orders take much longer. "
           f"Outlined: the promotions whose dates cannot span their sales ({notes}); every line of them falls after the end date, "
           f"so the 100 percent says nothing about billing. The other {len(others)} promotions have between "
           f"{min(p['share'] for p in others):.0%} and {max(p['share'] for p in others):.0%} of their lines invoiced after the end date.</i>",
           0, ay + 34, 860, 64, size=SMALL, color=GRAY)
    return d


# -- IF-05-5-A: the Supplier Table with its match key -------------------------------------------------------------------------

def if_05_5_a() -> Diagram:
    """Ex 5.5: the right-hand columns of the Supplier Table filtered to the matches, and the result block."""
    data = ctx.data()
    g = ctx.values("ch05.g5")
    n = ctx.values("ch05.ex5")
    require_columns("Supplier", ["SupplierID", "Address", "City"])
    require_columns("Employee", ["EmployeeID", "Address", "City"])
    n_cols = g["supplier_columns"]
    assert n_cols + 7 <= 26, "the new columns stay within column Z"
    letter = lambda k: chr(65 + n_cols + k)
    key = lambda a, c: f"{a.strip()}, {c.strip()}".upper()
    emp_keys = [key(a, c) for a, c in data.q("SELECT Address, City FROM Employee")]
    suppliers = data.q("SELECT SupplierID, Address, City FROM Supplier ORDER BY SupplierID")
    assert [s[0] for s in suppliers] == list(range(1, len(suppliers) + 1)), "worksheet row = SupplierID + 1"
    shown = []
    for sid, a, c in suppliers:
        k = key(a, c)
        if emp_keys.count(k):
            shown.append((sid, k, emp_keys.count(k)))
    matches = n["matches"]
    assert [s[0] for s in shown] == [m["id"] for m in matches] and all(s[2] == 1 for s in shown), "each match has one employee"
    assert len(shown) == g["n_match"] and g["raw"] == g["by_address"] == len(shown)
    d = Diagram("The Ex 5.5 Supplier Table, Filtered to the Matches, and the Result Block")
    formula = '=UPPER(TRIM([@Address])&", "&TRIM([@City]))'
    _formula_bar(d, 0, 0, 860, f"{letter(0)}{shown[0][0] + 1}", esc(formula))
    # Strip 1: MatchKey, EmployeeMatches, MatchedEmployeeID.
    head1 = ["MatchKey", "EmployeeMatches", "MatchedEmployeeID"]
    body1 = [[k, str(c), str(m["emp"])] for (_, k, c), m in zip(shown, matches)]
    w1 = [38] + _fit(head1, body1, pad=20, filters={0, 1, 2})
    w1 = _spread(w1, 860, first=1)
    rows1 = [dict(n="1", cells=[_header(h, filter="active" if h == "EmployeeMatches" else True) for h in head1])]
    for (sid, k, c), m in zip(shown, matches):
        band = WHITE if len(rows1) % 2 else BLUE_TINT
        rows1.append(dict(n=str(sid + 1), number_color=BLUE, cells=[dict(text=k, align="left", fill=band), dict(text=str(c), align="right", fill=band),
                                                                   dict(text=str(m["emp"]), align="right", fill=band)]))
    top = 40
    geo1 = _sheet(d, 0, top, [letter(0), letter(1), letter(2)], w1, rows1, row_h=24)
    mk = geo1[(1, 0)]
    xl.select(d, *mk)
    # Strip 2: the matched employee and the payments.
    head2 = ["MatchedEmployee", "MatchedJobTitle", "PaymentCount", "PaymentTotal"]
    body2 = [[m["emp_name"], m["title"], f"{m['payments']:,}", _money(m["paid"])] for m in matches]
    w2 = [38] + _fit(head2, body2, pad=20, filters={0, 1, 2, 3})
    w2 = _spread(w2, 860, first=1)
    rows2 = [dict(n="1", cells=[_header(h, filter=True) for h in head2])]
    for (sid, _, _), m, v in zip(shown, matches, body2):
        band = WHITE if len(rows2) % 2 else BLUE_TINT
        rows2.append(dict(n=str(sid + 1), number_color=BLUE, cells=[dict(text=v[0], fill=band, align="left"), dict(text=v[1], fill=band, align="left"),
                                                                    dict(text=v[2], align="right", fill=band), dict(text=v[3], align="right", fill=band)]))
    y2 = geo1["bottom"] + 14
    geo2 = _sheet(d, 0, y2, [letter(k) for k in range(3, 7)], w2, rows2, row_h=24)
    status_y = geo2["bottom"] + 6
    xl.status_bar(d, 0, status_y, 860, f"{len(shown)} of {len(suppliers)} records found")
    xl.sheet_tabs(d, 0, status_y + 30, ["Ex 5.5", "Ex 5.5 Supplier", "Ex 5.5 Employee", "Ex 5.5 DisbursementPayment"], "Ex 5.5 Supplier")
    # The result block of the Ex 5.5 worksheet.
    ry = status_y + 72
    xl.title_bar(d, 0, ry, 860, "Ex 5.5 worksheet")
    head3 = ["SupplierID", "Supplier", "EmployeeID", "Employee", "Job title"]
    body3 = [[str(m["id"]), m["name"], str(m["emp"]), m["emp_name"], m["title"]] for m in matches]
    w3 = [28] + _fit(head3, body3, pad=20)
    w3 = _spread(w3, 860, first=1)
    rows3 = [dict(n="3", cells=[dict(text="Suppliers that share an address with an employee", bold=True, span=5, clip=False)]),
             dict(n="4", cells=[_head(h, "right" if h in ("SupplierID", "EmployeeID") else "left") for h in head3])]
    for k, v in enumerate(body3):
        rows3.append(dict(n=str(5 + k), cells=[dict(text=x, align="right" if c in (0, 2) else "left") for c, x in enumerate(v)]))
    rows3.append(dict(n=str(5 + len(body3)), cells=[dict(text="Suppliers with a match", bold=True, span=2, clip=False),
                                                     dict(text=str(len(shown)), bold=True, align="right")]))
    geo3 = _sheet(d, 0, ry + 28, list("ABCDE"), w3, rows3, row_h=24)
    hidden = _hidden_text([letter(k) for k in range(7)], n_cols)
    d.text(f"<i>Columns {hidden} of the Supplier Table are hidden, and its other columns are shown in two strips of the same "
           f"rows. The Table is filtered to EmployeeMatches greater than zero ({len(shown)} of {len(suppliers)} suppliers; the row "
           f"numbers are blue). Selected: the first MatchKey, whose formula shows in the bar: the address, a comma, a space and "
           f"the city, in capitals. The result block below is on the Ex 5.5 worksheet.</i>", 0, geo3["bottom"] + 10, 860, 64,
           size=SMALL, color=GRAY)
    return d


FIGURES = {
    "IF-05-0-A": if_05_0_a,
    "IF-05-0-B": if_05_0_b,
    "IF-05-1-A": if_05_1_a,
    "IF-05-2-A": if_05_2_a,
    "IF-05-3-A": if_05_3_a,
    "IF-05-4-A": if_05_4_a,
    "IF-05-5-A": if_05_5_a,
}
