"""Instructor figures of Chapter 3 (guides in facts/instructor/guides/chapter-03-accounting-data-environment/)."""

from __future__ import annotations

import ctx
import excel as xl
import kit
from check_figures import text_width
from data import cardinality, relate, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HEAD, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc, money)

RIGHT, LEFT, TOP, BOTTOM = (1, 0.5), (0, 0.5), (0.5, 0), (0.5, 1)
DASHED_AMBER = (f"rounded=0;html=1;fillColor=none;strokeColor={AMBER};strokeWidth=2;dashed=1;dashPattern=6 3;")


def _table(d: Diagram, name: str, x: float, y: float, rows: list[tuple[str, str]], w: float = 240, **kw):
    """An ER table whose columns are checked against the database first (as scripts/figures/ch03.py does)."""
    require_columns(name, [column for _, column in rows])
    return d.table(name, x, y, rows, w=w, **kw)


def _label(d: Diagram, text: str, cx: float, cy: float, size: int = SMALL, pad: float = 10, h: float | None = None) -> str:
    """A white label centered on a line (used for dashed lines, whose own edge labels leave dash fragments)."""
    parts = text.split("<br>")
    width = max(text_width(p, size, False) for p in parts) + pad * 2
    height = h or 16 * len(parts) + 6
    return d.box(text, cx - width / 2, cy - height / 2, width, height, fill=WHITE, stroke=WHITE, size=size, rounded=False)


def _above(d: Diagram, text: str, cx: float, cy: float, size: int = SMALL) -> str:
    """A label that sits just above a horizontal line at height cy, centered on cx (the line stays visible)."""
    parts = text.split("<br>")
    width = max(text_width(p, size, False) for p in parts) + 16
    height = 16 * len(parts) + 2
    return d.text(text, cx - width / 2, cy - height - 3, width, height, size=size, align="center", valign="bottom")


# -- IF-03-0-A: what a join does to one customer's rows ----------------------------------------------------------------

def if_03_0_a() -> Diagram:
    """Customer, SalesOrder and SalesOrderLine joined for one customer: the customer repeats on every line row."""
    data = ctx.data()
    fan = ctx.values("ch03.chapter")["fan"]
    cid = fan["id"]
    customer = data.q("SELECT CustomerID, CustomerName FROM Customer WHERE CustomerID = ?", cid)
    assert customer == [(cid, fan["name"])], "the figure and the guide use the same customer"
    orders = data.q("SELECT o.SalesOrderID, o.OrderNumber, COUNT(l.SalesOrderLineID) FROM SalesOrder o LEFT JOIN "
                    "SalesOrderLine l USING (SalesOrderID) WHERE o.CustomerID = ? GROUP BY 1, 2 ORDER BY 1", cid)
    lines = data.q("SELECT o.OrderNumber, l.SalesOrderLineID FROM SalesOrder o JOIN SalesOrderLine l USING (SalesOrderID) "
                   "WHERE o.CustomerID = ? ORDER BY l.SalesOrderLineID", cid)
    n_orders, n_lines = len(orders), len(lines)
    assert (n_orders, n_lines) == (fan["orders"], fan["lines"]), "the counts of the figure and of the guide agree"
    assert all(n >= 1 for _, _, n in orders), "every order has a line, so the join keeps every order"
    d = Diagram("What a Join Does to One Customer's Rows")

    # The three tables, with the rows of this one customer.
    row_h, head_h, sub_h = 22, 30, 24
    ox, ow, lx, lw, cx, cw = 330, 200, 650, 210, 0, 210
    top = 0
    body_top = top + head_h + sub_h
    d.header_box("Customer", cx, top, cw, head_h, size=HEAD)
    d.header_box("SalesOrder", ox, top, ow, head_h, size=HEAD)
    d.header_box("SalesOrderLine", lx, top, lw, head_h, size=HEAD)
    d.text(f"<i>{n_orders} orders</i>", ox, top + head_h, ow, sub_h, size=SMALL, color=GRAY, align="center", valign="middle")
    d.text(f"<i>{n_lines} lines</i>", lx, top + head_h, lw, sub_h, size=SMALL, color=GRAY, align="center", valign="middle")
    d.text("<i>1 customer</i>", cx, top + head_h, cw, sub_h, size=SMALL, color=GRAY, align="center", valign="middle")
    for i, (key, value) in enumerate([("CustomerID", str(cid)), ("CustomerName", fan["name"])]):
        d.box(esc(key), cx, body_top + i * row_h, 100, row_h, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        d.box(f"<b>{esc(value)}</b>", cx + 100, body_top + i * row_h, cw - 100, row_h, fill=BLUE_TINT, stroke=RULE,
              size=SMALL, align="left", rounded=False)
    chip, chip_gap = 14, 5
    assert 10 + max(n for _, _, n in orders) * (chip + chip_gap) <= lw, "the squares of the longest order fit their cell"
    for i, (_, number, n) in enumerate(orders):
        y = body_top + i * row_h
        d.box(esc(number), ox, y, ow, row_h, fill=WHITE if i % 2 == 0 else GRAY_TINT, stroke=RULE, size=SMALL, align="left",
              rounded=False)
        d.box("", lx, y, lw, row_h, fill=WHITE if i % 2 == 0 else GRAY_TINT, stroke=RULE, rounded=False)
        for k in range(n):
            d.box("", lx + 10 + k * (chip + chip_gap), y + (row_h - chip) / 2, chip, chip, fill=BLUE, stroke=BLUE,
                  rounded=False)
    bottom = body_top + n_orders * row_h
    # Arrows between the tables carry the join columns.
    cust_box = d.container(cx, top, cw, body_top + 2 * row_h - top)
    orders_box = d.container(ox, top, ow, bottom - top)
    lines_box = d.container(lx, top, lw, bottom - top)
    centre = (top + body_top + 2 * row_h) / 2
    d.arrow(cust_box, orders_box, color=GRAY, label="CustomerID", exit=RIGHT, entry=(0, centre / (bottom - top)))
    d.arrow(orders_box, lines_box, color=GRAY, label="SalesOrderID", exit=RIGHT, entry=LEFT)
    d.text("<i>One square is one order line; each row lines up with its order.</i>", lx, bottom + 4, lw, 34, size=SMALL,
           color=GRAY)
    d.text("<i>The join meets each order with its customer and each line with its order, so the customer is carried once "
           "for every line.</i>", cx, body_top + 2 * row_h + 20, 290, 70, size=SMALL, color=GRAY)

    # The joined result: the customer's name repeats on every line row.
    sketch_y = bottom + 74
    sk_w = [150, 150, 140]
    sk_x = [0, 150, 300]
    row = 22
    shown_head, shown_tail = 5, 1
    d.text("<b>The joined result</b> <i>(Customer, SalesOrder and SalesOrderLine, joined on the two keys)</i>", 0,
           sketch_y - 24, 470, 20, size=SMALL)
    for x, w, head in zip(sk_x, sk_w, ["CustomerName", "OrderNumber", "SalesOrderLineID"]):
        d.box(f"<b>{head}</b>", x, sketch_y, w, row, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False,
              align="left")
    shown = lines[:shown_head]
    y = sketch_y + row
    for number, line_id in shown:
        for x, w, value, repeat in zip(sk_x, sk_w, [fan["name"], number, str(line_id)], [True, False, False]):
            d.box(esc(value), x, y, w, row, fill=AMBER_TINT if repeat else WHITE, stroke=AMBER if repeat else RULE,
                  size=SMALL, align="left", rounded=False)
        y += row
    hidden = n_lines - shown_head - shown_tail
    d.box(f"<i>... {hidden} more rows</i>", 0, y, sum(sk_w), row, fill=GRAY_TINT, stroke=RULE, color=GRAY, size=SMALL,
          rounded=False)
    y += row
    number, line_id = lines[-1]
    for x, w, value, repeat in zip(sk_x, sk_w, [fan["name"], number, str(line_id)], [True, False, False]):
        d.box(esc(value), x, y, w, row, fill=AMBER_TINT if repeat else WHITE, stroke=AMBER if repeat else RULE, size=SMALL,
              align="left", rounded=False)
    y += row
    # Counters beside the sketch.
    kx, kw = 480, 380
    d.box(f"<b style=\"font-size:24px\">{n_lines}</b><br>rows in the result", kx, sketch_y - 24, 180, 74, fill=CORAL_TINT,
          stroke=CORAL, stroke_width=1.5, size=SMALL)
    d.box(f"<b style=\"font-size:24px\">1</b><br>customer", kx + 200, sketch_y - 24, 180, 74, fill=TEAL_TINT, stroke=TEAL,
          stroke_width=1.5, size=SMALL)
    kit.callout(d, f"<b>Summing line amounts by line is right:</b> each line appears once, so the total is the "
                   f"customer's. <b>Counting customers by row is wrong:</b> it finds {n_lines} where there is 1. Count "
                   f"distinct CustomerID, or aggregate at the grain you mean.", kx, sketch_y + 62, kw, color="amber")
    d.text(f"<i>Customer {cid}, {esc(fan['name'])}: {n_orders} orders and {n_lines} lines. The amber cells show the one "
           f"customer's name repeated once for every line.</i>", 0, y + 10, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-03-0-B: sorting a column into primary key, foreign key, bridge key or the trace ---------------------------------

def if_03_0_b() -> Diagram:
    """A decision tree for the role of a column (Chapter 3 note, Difficult ideas)."""
    for table, cols in {"SalesOrder": ["SalesOrderID", "CustomerID", "OrderDate"], "SalesOrderLine": ["ItemID"],
                        "GLEntry": ["SourceDocumentType", "SourceDocumentID"]}.items():
        require_columns(table, cols)
    assert cardinality("Customer", "CustomerID", "SalesOrder", "CustomerID")[0] == "ERmandOne", "CustomerID is a foreign key"
    d = Diagram("Sorting a Column into Its Role")
    qx, qw, bx, bw, ex, ew = 0, 270, 330, 230, 596, 252
    qh = 52
    ys = {"pk": 0, "fk": 100, "side": 200, "bridge": 300, "ref": 436, "attr": 556}

    def question(text: str, x: float, y: float, w: float = qw, h: float = qh) -> str:
        return d.box(text, x, y, w, h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5)

    def leaf(text: str, y: float, fill: str = TEAL_TINT, stroke: str = TEAL, x: float = bx, w: float = bw, h: float = qh,
             dashed: bool = False) -> str:
        return d.box(text, x, y, w, h, fill=fill, stroke=stroke, stroke_width=2 if dashed else 1.5, dashed=dashed)

    q1 = question("Does the column identify the rows of its own table?", qx, ys["pk"])
    q2 = question("Does it hold the key values of another table?", qx, ys["fk"])
    q3 = question("Does the meaning of its value depend on another column?", qx, ys["ref"])
    l_pk = leaf("<b>Primary key</b><br>identifies each row of its own table", ys["pk"])
    l_fk = leaf("<b>Foreign key</b><br>holds the key values of another table", ys["fk"])
    side = question("Does the same column reach into another table group?", bx, ys["side"], w=bw)
    l_bridge = leaf("<b>Bridge key</b><br>a foreign key across table groups", ys["bridge"])
    l_ref = leaf("<b>Logical reference, not a key</b><br>read together with SourceDocumentType", ys["ref"], fill=AMBER_TINT,
                 stroke=AMBER, dashed=True)
    l_attr = leaf("<b>An ordinary column</b><br>it describes the row", ys["attr"], fill=GRAY_TINT, stroke=GRAY, x=qx, w=qw)
    d.arrow(q1, l_pk, exit=RIGHT, entry=LEFT, label="Yes")
    d.arrow(q2, l_fk, exit=RIGHT, entry=LEFT, label="Yes")
    d.arrow(q1, q2, exit=BOTTOM, entry=TOP, label="No")
    d.arrow(q2, q3, exit=BOTTOM, entry=TOP, label="No")
    d.arrow(q3, l_ref, exit=RIGHT, entry=LEFT, label="Yes")
    d.arrow(q3, l_attr, exit=BOTTOM, entry=TOP, label="No")
    d.arrow(l_fk, side, exit=BOTTOM, entry=TOP, label="then ask")
    d.arrow(side, l_bridge, exit=BOTTOM, entry=TOP, label="Yes")
    # The examples, as small table headers.
    t_pk = _table(d, "SalesOrder", ex, ys["pk"], [("PK", "SalesOrderID")], w=ew)
    t_fk = _table(d, "SalesOrder", ex, ys["fk"], [("FK", "CustomerID")], w=ew)
    t_br = _table(d, "SalesOrderLine", ex, ys["bridge"], [("FK", "ItemID")], w=ew)
    t_ref = _table(d, "GLEntry", ex, ys["ref"] - 12, [("", "SourceDocumentType"), ("", "SourceDocumentID")], w=ew)
    d.vertex("", DASHED_AMBER, ex - 4, ys["ref"] - 16, ew + 8, t_ref.h + 8)
    d.text("<i>No: it stays an ordinary foreign key, inside its own table group.</i>", ex, ys["side"] + 4, ew, 44, size=SMALL,
           color=GRAY)
    d.text("<i>ItemID in SalesOrderLine reaches Item, in Master Data.</i>", ex, ys["bridge"] + 58, ew, 34, size=SMALL,
           color=GRAY)
    d.text("<i>The dashed amber leaf is the source-document trace: its two columns work as one.</i>", ex, ys["ref"] + 68,
           ew, 50, size=SMALL, color=GRAY)
    ly = ys["attr"] + 84
    d.box("", 0, ly + 3, 16, 14, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5)
    d.text("A question to ask of the column", 22, ly, 220, 20, size=SMALL, valign="middle")
    d.box("", 262, ly + 3, 16, 14, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5)
    d.text("The role it plays", 284, ly, 130, 20, size=SMALL, valign="middle")
    d.line_sample(430, ly + 10, 30, color=AMBER, dashed=True, width=2.5)
    d.text("The source-document trace: a logical link that analysts test", 468, ly, 392, 20, size=SMALL, valign="middle")
    return d


# -- IF-03-1-A: the model purchase from the supplier to the payment ----------------------------------------------------

def _entry_lines(rows: list[dict]) -> list[str]:
    """'Dr 2020 Goods Received Not Invoiced' lines from the ledger rows of one document: debits first."""
    out = [f"Dr {r['number']} {esc(r['name'])}" for r in rows if r["debit"]]
    return out + [f"Cr {r['number']} {esc(r['name'])}" for r in rows if r["credit"]]


def if_03_1_a() -> Diagram:
    """The model purchase of Exercise 3.1, document by document, with the ledger rows of the receipt, the invoice and
    the payment."""
    v = ctx.values("ch03.ex1")
    data = ctx.data()
    pi, pil, grl, gr, pol, po, sup, pay = v["pi"], v["pil"], v["grl"], v["gr"], v["pol"], v["po"], v["supplier"], v["pay"]
    types = {r[0] for r in data.q("SELECT DISTINCT SourceDocumentType FROM GLEntry")}
    assert not types & {"Supplier", "PurchaseOrder", "PurchaseOrderLine"}, "the supplier and the order post nothing"
    for rows in (v["gl_pi"], v["gl_gr"], v["gl_dp"]):
        assert abs(sum(r["debit"] for r in rows) - sum(r["credit"] for r in rows)) < 0.005, "each document balances"
    d = Diagram("The Model Purchase from Supplier to Payment")
    bw, gap = 300, 38
    docs = [
        ("Supplier", [sup["name"], f"SupplierID {sup['id']}"]),
        ("PurchaseOrder", [po["number"], f"ordered {po['date']}"]),
        ("PurchaseOrderLine", [f"POLineID {pol['id']}", f"{pol['quantity']:g} units at {money(pol['cost'])}"]),
        ("GoodsReceiptLine and GoodsReceipt", [f"{gr['number']}, received {gr['date']}",
                                               f"line {grl['id']}: {grl['quantity']:g} units, {money(grl['cost'])}"]),
        ("PurchaseInvoiceLine and PurchaseInvoice", [f"{pi['number']}, dated {pi['date']}",
                                                      f"line {pil['id']}: {pil['quantity']:g} units at {money(pil['cost'])}",
                                                      f"received {pi['received']}, total {money(pi['total'])}"]),
        ("DisbursementPayment", [f"{pay['number']}, {pay['date']}", f"{money(pay['amount'])} by {pay['method']}"]),
    ]
    keys = ["SupplierID", "PurchaseOrderID", "POLineID", "GoodsReceiptLineID", "PurchaseInvoiceID"]
    ids, spans, y = [], [], 0.0
    for i, (title, lines) in enumerate(docs):
        h = 16 * (len(lines) + 1) + 14
        fill, stroke = kit.tint("teal" if i >= 3 else "blue")
        ids.append(d.box("<br>".join([f"<b>{title}</b>"] + [esc(x) for x in lines]), 0, y, bw, h,
                         fill=fill, stroke=stroke, stroke_width=1.5, size=SMALL))
        spans.append((y, h))
        y += h + gap
    bottom = y - gap
    for i, key in enumerate(keys):
        d.arrow(ids[i], ids[i + 1], label=key, exit=BOTTOM, entry=TOP)
    # The ledger: GLEntry with the rows of each document, each arrow ending on its own rows.
    gx, gw = 600, 260
    top = spans[3][0] - 36
    d.box("<b>GLEntry</b>", gx, top, gw, bottom - top, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5, valign="top", size=HEAD)
    postings = [(3, "GoodsReceipt", gr["id"], v["gl_gr"]), (4, "PurchaseInvoice", v["pid"], v["gl_pi"]),
                (5, "DisbursementPayment", pay["id"], v["gl_dp"])]
    for i, kind, key, rows in postings:
        y0, h = spans[i]
        cy = y0 + h / 2
        posted = {r["date"] for r in rows}
        assert len(posted) == 1, "the rows of one document carry one posting date"
        rows_box = d.box(f"<b>{len(rows)} rows</b><br>posted {posted.pop()}", gx + 16, cy - 26, gw - 32, 52, fill=WHITE,
                         stroke=GRAY, size=SMALL, rounded=False)
        d.edge(ids[i], rows_box, end="blockThin", color=AMBER, dashed=True, width=2.5, exit=RIGHT, entry=LEFT)
        lines = [f"<i>type {kind}, ID {key}</i>"] + _entry_lines(rows)
        d.text("<br>".join(lines), bw + 12, cy - 16 * len(lines) - 4, gx - bw - 24, 16 * len(lines) + 4, size=SMALL,
               valign="bottom", align="center")
    ny = bottom + 14
    kit.legend(d, 0, ny, [("Solid gray: the key that links two documents", GRAY, "line"),
                          ("Dashed amber: the ledger rows a document posts", AMBER, "dashed")])
    receipt_credit = next(r for r in v["gl_gr"] if r["credit"])
    invoice_debits = [r for r in v["gl_pi"] if r["debit"]]
    clearing = next((r for r in invoice_debits if r["number"] == receipt_credit["number"]), None)
    variance_row = next((r for r in invoice_debits if r is not clearing), None)
    assert clearing and variance_row, "the invoice debits the account the receipt credited, and posts the difference elsewhere"
    assert abs(variance_row["debit"] - v["variance_abs"]) < 0.005, "the second debit is the price variance of the guide"
    d.text(f"<i>The supplier, the order and its line post nothing. The receipt credits {esc(receipt_credit['name']).lower()} "
           f"({receipt_credit['number']}), which the invoice then debits. The {money(v['variance_abs'])} between the order "
           f"price and the invoice price goes to {esc(variance_row['name']).lower()} ({variance_row['number']}), an "
           f"{v['variance_side']} difference here. Each document's ledger rows are found by its type and its key, not by "
           f"its number.</i>", 0, ny + 30, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-03-3-A: from a finished product to its components --------------------------------------------------------------

def if_03_3_a() -> Diagram:
    """Item, BillOfMaterial, BillOfMaterialLine and Item again, with the material roll-up of Step 3 (Exercise 3.3)."""
    v = ctx.values("ch03.ex3")
    data = ctx.data()
    item, lines = v["item"], v["lines"]
    bom = data.q("SELECT BOMID, VersionNumber, Status FROM BillOfMaterial WHERE ParentItemID = ?", item["id"])
    assert bom == [(item["bom"], item["version"], bom[0][2])], "the model product has one bill, the one of the guide"
    comps = data.q("SELECT l.LineNumber, l.ComponentItemID, i.ItemCode, i.ItemName, i.StandardCost, l.QuantityPerUnit, "
                   "l.ScrapFactorPct FROM BillOfMaterialLine l JOIN Item i ON i.ItemID = l.ComponentItemID WHERE l.BOMID = ? "
                   "ORDER BY l.LineNumber", item["bom"])
    assert [(c[0], c[2], c[4], c[5], c[6]) for c in comps] == [(x["line"], x["code"], x["cost"], x["quantity"], x["scrap"])
                                                               for x in lines], "the figure and the guide list the same lines"
    assert not data.q("SELECT 1 FROM BillOfMaterial WHERE ParentItemID IN (SELECT ComponentItemID FROM BillOfMaterialLine "
                      "WHERE BOMID = ?)", item["bom"]), "no component is itself a parent"
    line_cost = [c[5] * (1 + c[6]) * c[4] for c in comps]
    material = sum(line_cost)
    assert abs(material - v["material"]) < 1e-9
    assert abs(material + item["conversion"] - item["cost"]) < 0.03, "the roll-up plus conversion is the standard cost"
    digits = 2 if abs(sum(round(x, 2) for x in line_cost) - round(material, 2)) < 0.005 else 4
    d = Diagram("From a Finished Product to Its Components")
    iw, mx, mw, rx = 210, 330, 200, 650
    top, head = 46, 26
    row_h = 52

    tall = 66            # the product row and the bill row are as tall as the name of the product needs

    def item_box(x: float, y: float, rows: list[list[str]], h: float) -> list[str]:
        d.box("<b>Item</b>", x, y, iw, head, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
        return [d.box("<br>".join(cell), x, y + head + k * h, iw, h, fill=WHITE if k % 2 == 0 else GRAY_TINT, stroke=RULE,
                      size=SMALL, rounded=False) for k, cell in enumerate(rows)]

    product = [[f"<b>{item['code']}</b>", esc(item["name"]), f"ItemID {item['id']}, StandardCost {money(item['cost'])}"]]
    left = item_box(0, top, product, tall)[0]
    # The bill.
    bom_h = head + tall
    d.box("<b>BillOfMaterial</b>", mx, top, mw, head, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
    bom_box = d.box(f"BOMID {item['bom']}, version {item['version']}<br>ParentItemID {item['id']}<br>Status {bom[0][2]}", mx,
                    top + head, mw, tall, fill=WHITE, stroke=RULE, size=SMALL, rounded=False)
    bom_all = d.container(mx, top, mw, bom_h)
    # The lines of the bill, and the components they name.
    ly = top + bom_h + 40
    d.box("<b>BillOfMaterialLine</b>", mx, ly, mw, head, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
    line_boxes, item_rows = [], []
    for k, c in enumerate(comps):
        line_boxes.append(d.box(f"Line {c[0]}: ComponentItemID {c[1]}<br>QuantityPerUnit {c[5]:g}<br>ScrapFactorPct {c[6]:g}",
                                mx, ly + head + k * row_h, mw, row_h, fill=WHITE if k % 2 == 0 else GRAY_TINT, stroke=RULE,
                                size=SMALL, rounded=False))
    lines_all = d.container(mx, ly, mw, head + len(comps) * row_h)
    d.box("<b>Item</b>", rx, ly, iw, head, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
    for k, c in enumerate(comps):
        item_rows.append(d.box(f"<b>{c[2]}</b><br>{esc(c[3])}<br>ItemID {c[1]}, StandardCost {money(c[4])}", rx,
                               ly + head + k * row_h, iw, row_h, fill=WHITE if k % 2 == 0 else GRAY_TINT, stroke=RULE,
                               size=SMALL, rounded=False))
    comp_all = d.container(rx, ly, iw, head + len(comps) * row_h)
    d.arrow(left, bom_box, label="ParentItemID", exit=RIGHT, entry=LEFT)
    d.arrow(bom_all, lines_all, label="BOMID", exit=BOTTOM, entry=TOP)
    for k, (src, tgt) in enumerate(zip(line_boxes, item_rows)):
        d.arrow(src, tgt, label="ComponentItemID" if k == len(comps) // 2 else None, exit=RIGHT, entry=LEFT)
    # One table in two roles.
    d.edge(d.container(0, top, iw, head + tall), comp_all, color=GRAY, width=2, exit=TOP, entry=TOP,
           points=[(iw / 2, 18), (rx + iw / 2, 18)],
           meta="dashed=1;dashPattern=2 4;")
    _label(d, "<b>One table in two roles:</b> the product, and its components", (iw / 2 + rx + iw / 2) / 2, 18, size=SMALL)
    bottom = ly + head + len(comps) * row_h
    # The roll-up.
    cy = bottom + 22
    d.text("<b>The roll-up of Step 3, line by line</b>", 0, cy - 4, 400, 20, size=SMALL)
    cy += 20
    widths = [260, 140, 150, 140, 170]
    xs = [0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    for x, w, head_text in zip(xs, widths, ["Component", "QuantityPerUnit", "× (1 + ScrapFactorPct)", "× StandardCost",
                                           "= cost of the line"]):
        d.box(f"<b>{head_text}</b>", x, cy, w, 24, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False, align="left")
    for k, (c, cost) in enumerate(zip(comps, line_cost)):
        y = cy + 24 * (k + 1)
        for x, w, text, align in zip(xs, widths, [f"{c[2]} {c[3]}", f"{c[5]:g}", f"{1 + c[6]:g}", money(c[4]),
                                                  f"${cost:,.{digits}f}"], ["left", "right", "right", "right", "right"]):
            d.box(esc(text), x, y, w, 24, fill=WHITE, stroke=RULE, size=SMALL, rounded=False, align=align)
    y = cy + 24 * (len(comps) + 1)
    # The strip: the lines added up, then the standard cost.
    sw = [250, 30, 250, 30, 300]
    sx = [0, 250, 280, 530, 560]
    d.box(f"<b>Material cost</b><br>the lines added up: ${material:,.2f}", sx[0], y + 14, sw[0], 48, fill=BLUE_TINT, stroke=BLUE,
          stroke_width=1.5, size=SMALL)
    d.text("<b>+</b>", sx[1], y + 14, sw[1], 48, size=HEAD, align="center", valign="middle")
    d.box(f"<b>Conversion cost</b><br>StandardConversionCost: {money(item['conversion'])}", sx[2], y + 14, sw[2], 48,
          fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL)
    d.text("<b>=</b>", sx[3], y + 14, sw[3], 48, size=HEAD, align="center", valign="middle")
    d.box(f"<b>Standard cost</b><br>StandardCost of {item['code']}: {money(item['cost'])}", sx[4], y + 14, sw[4], 48,
          fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, size=SMALL)
    d.text(f"<i>Without the scrap factor the material cost is {money(v['noscrap'])} and the roll-up does not reproduce the "
           f"standard cost. The two Item boxes are drawn alike because they are one table: ParentItemID and ComponentItemID "
           f"are two foreign keys to ItemID.</i>", 0, y + 72, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-03-4-A: the join path from Budget to the ledger ---------------------------------------------------------------

END_WORDS = {"ERmandOne": "exactly one", "ERzeroToOne": "zero or one", "ERoneToMany": "one or many",
             "ERzeroToMany": "zero or many"}


def if_03_4_a() -> Diagram:
    """Budget and GLEntry share four columns and no key; each relates to CostCenter and to Account by a foreign key
    (Exercise 3.4)."""
    v = ctx.values("ch03.ex4")
    data = ctx.data()
    assert data.one("SELECT MIN(Month) || '-' || MAX(Month) FROM Budget") == data.one(
        "SELECT MIN(FiscalPeriod) || '-' || MAX(FiscalPeriod) FROM GLEntry") == "1-12", "Month and FiscalPeriod are both 1 to 12"
    assert not data.q("SELECT 1 FROM CostCenter WHERE ParentCostCenterID IS NOT NULL AND ParentCostCenterID <> ''"), "flat cost centers"
    d = Diagram("The Join Path from Budget to the Ledger")
    cc = _table(d, "CostCenter", 330, 24, [("PK", "CostCenterID")], w=200, focus=False, group="Organizational Planning")
    ty, tw = 170, 270
    bud = _table(d, "Budget", 0, ty, [("", "FiscalYear"), ("", "Month"), ("FK", "CostCenterID"), ("FK", "AccountID"),
                                        ("", "BudgetAmount")], w=tw)
    gl = _table(d, "GLEntry", 860 - tw, ty, [("", "FiscalYear"), ("", "FiscalPeriod"), ("FK", "CostCenterID"),
                                               ("FK", "AccountID"), ("", "Debit"), ("", "Credit")], w=tw)
    ay = gl.bottom + 96
    acc = _table(d, "Account", 330, ay, [("PK", "AccountID")], w=200, focus=False, caption_below=True, group="Accounting Core")
    # The four-column match.
    pairs = [("FiscalYear", "FiscalYear", "same fiscal year"), ("Month", "FiscalPeriod", "same month number"),
             ("CostCenterID", "CostCenterID", "same cost center"), ("AccountID", "AccountID", "same account")]
    for b_col, g_col, label in pairs:
        d.edge(bud.rows[b_col], gl.rows[g_col], start="oval", end="oval", color=BLUE, width=2.5, exit=RIGHT, entry=LEFT,
               label=label, marker_size=8)
    d.text("<b>A match on four columns, not a key</b>", tw + 10, ty - 22, 860 - 2 * tw - 20, 20, size=SMALL, align="center",
           color=BLUE)
    # The foreign keys, with end symbols computed from the data.
    relate(d, "CostCenter", "CostCenterID", "Budget", "CostCenterID", cc.id, bud.id, exit=(0.15, 1), entry=(0.5, 0))
    relate(d, "CostCenter", "CostCenterID", "GLEntry", "CostCenterID", cc.id, gl.id, color=AMBER, exit=(0.85, 1),
           entry=(0.5, 0))
    relate(d, "Account", "AccountID", "Budget", "AccountID", acc.id, bud.id, color=AMBER, exit=(0.15, 0), entry=(0.5, 1))
    relate(d, "Account", "AccountID", "GLEntry", "AccountID", acc.id, gl.id, exit=(0.85, 0), entry=(0.5, 1))
    # What the two cost center links say at the CostCenter end.
    bud_end = END_WORDS[cardinality("CostCenter", "CostCenterID", "Budget", "CostCenterID")[0]]
    gl_end = END_WORDS[cardinality("CostCenter", "CostCenterID", "GLEntry", "CostCenterID")[0]]
    assert (bud_end, gl_end) == (v["bud_cc"]["parent_end"], v["gl_cc"]["parent_end"]), "the ends agree with the guide"
    d.text(f"<i>{bud_end}</i>", 280, 84, 78, 20, size=SMALL, color=GRAY, align="right")
    d.marker("1", 508, 84, CORAL)
    d.text(f"<i>{gl_end}</i>", 538, 84, 100, 20, size=SMALL, color=GRAY)
    n_blank, n_rows = v["gl_cc"]["blank"], v["gl_cc"]["rows"]
    on_sheet = data.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.CostCenterID IS NULL AND "
                        "a.AccountType IN ('Asset', 'Liability', 'Equity')")
    assert on_sheet > n_blank / 2, "most ledger rows with no cost center are on balance sheet accounts"
    assert v["bud_cc"]["blank"] == 0, "every Budget row names a cost center"
    bottom = acc.bottom + 22
    kit.callout(d, f"<b>1</b> The circle: a ledger row has at most one cost center and may have none. {n_blank:,} of "
                   f"{n_rows:,} ledger rows have a blank CostCenterID, mostly on balance sheet accounts, so a report by cost "
                   f"center leaves them out. Every Budget row names a cost center.", 0, bottom + 14, 860, color="amber")
    ly = bottom + 14 + 56
    lx = 0.0
    for label, color, end in [("The same column in both tables", BLUE, "oval"), ("A foreign key within a table group", GRAY, "none"),
                              ("A foreign key to another group", AMBER, "none")]:
        d.line_sample(lx, ly + 10, 30, color=color, width=1.5 if color == GRAY else 2.5, end=end)
        width = text_width(label, SMALL, False) + 10
        d.text(label, lx + 38, ly, width, 20, size=SMALL, valign="middle")
        lx += 38 + width + 22
    assert lx - 22 <= 860, lx
    d.text("<i>Month in Budget and FiscalPeriod in GLEntry hold the same month number under two names. To compare the "
           "two, sum the ledger to the four columns after leaving out the year-end close entries, then set it beside "
           "BudgetAmount.</i>", 0, ly + 28, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-03-5-A: the three extraction plans ----------------------------------------------------------------------------

def if_03_5_a() -> Diagram:
    """Revenue completeness, the three-way match and the journal entry analysis as three lanes (Exercise 3.5)."""
    v = ctx.values("ch03.ex5")
    for table, cols in {"ShipmentLine": ["ShipmentLineID"], "SalesInvoiceLine": ["ShipmentLineID", "SalesInvoiceID"],
                        "SalesInvoice": ["SubTotal"], "GLEntry": ["SourceDocumentType", "SourceDocumentID"],
                        "PurchaseOrderLine": ["POLineID", "Quantity", "UnitCost"],
                        "GoodsReceiptLine": ["POLineID", "QuantityReceived"],
                        "PurchaseInvoiceLine": ["POLineID", "GoodsReceiptLineID", "Quantity", "UnitCost"],
                        "JournalEntry": ["TotalAmount", "ApprovedByEmployeeID"], "Employee": ["EmployeeID"]}.items():
        require_columns(table, cols)
    assert not {c[1] for c in ctx.data().q("PRAGMA table_info(GoodsReceiptLine)")} & {"UnitCost", "UnitPrice"},         "the receipt line carries no unit cost of its own"
    assert v["unposted"] == 0 and v["n_uninvoiced"] > 0, "every invoice is posted, and some shipment lines were never invoiced"
    d = Diagram("Three Extraction Plans")

    def band(y: float, text: str) -> None:
        d.box(f"<b>{text}</b>", 0, y, 860, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False, align="left")

    def node(x: float, y: float, w: float, h: float, text: str, tint: str = "blue") -> str:
        fill, stroke = kit.tint(tint)
        return d.box(text, x, y, w, h, fill=fill, stroke=stroke, stroke_width=1.5, size=SMALL)

    def control(x: float, y: float, w: float, text: str, h: float | None = None) -> tuple[str, float]:
        h = h or kit.height_for(text, w, SMALL, pad=14)
        return node(x, y, w, h, text, "teal"), h

    post = "SourceDocumentType<br>and SourceDocumentID"
    # Lane 1: revenue completeness.
    y = 0
    band(y, "1  Revenue completeness: start from events that do not come from the invoices")
    ry, rh = y + 40, 78
    b1 = node(0, ry, 130, rh, "<b>Shipment and ShipmentLine</b><br><i>the independent population</i>")
    b2 = node(250, ry, 150, rh, "<b>SalesInvoiceLine and SalesInvoice</b><br><i>the recorded revenue</i>")
    b3 = node(550, ry, 80, rh, "<b>GLEntry</b><br><i>the ledger</i>")
    c1, _ = control(660, ry, 200, "<b>Control totals</b><br>invoice SubTotal against the revenue credits of its ledger rows; "
                                   "shipment lines with no invoice line", rh)
    d.arrow(b1, b2, label="<b>completeness</b><br>ShipmentLineID", exit=RIGHT, entry=LEFT)
    d.edge(b2, b3, end="blockThin", color=AMBER, dashed=True, width=2.5, exit=RIGHT, entry=LEFT)
    _above(d, f"<b>posting</b><br>{post}", 475, ry + rh / 2)
    d.edge(b3, c1, color=GRAY, exit=RIGHT, entry=LEFT)
    # Lane 2: the three-way match.
    y = ry + rh + 28
    band(y, "2  Purchasing: the three-way match, joined at the line level")
    po_y, low = y + 38, y + 138
    po = node(160, po_y, 190, 48, "<b>PurchaseOrderLine</b><br>Quantity, UnitCost")
    gr = node(0, low, 180, 62, "<b>GoodsReceiptLine</b><br>QuantityReceived<br><i>no unit cost of its own</i>")
    pi = node(330, low, 190, 62, "<b>PurchaseInvoiceLine</b><br>Quantity, UnitCost")
    d.edge(po, gr, color=GRAY, exit=LEFT, entry=TOP)
    d.edge(po, pi, color=GRAY, exit=RIGHT, entry=TOP)
    d.edge(gr, pi, color=GRAY, exit=RIGHT, entry=LEFT, label="GoodsReceiptLineID")
    _label(d, "POLineID", 90, (po_y + 24 + low) / 2)
    _label(d, "POLineID", 425, (po_y + 24 + low) / 2)
    c2, _ = control(570, low, 290, "<b>Control total</b><br>quantity ordered, received and invoiced, summed for each order line",
                    62)
    d.edge(pi, c2, color=GRAY, exit=RIGHT, entry=LEFT)
    kit.callout(d, "Join the lines, not the headers: joining the headers on PurchaseOrderID alone multiplies the rows.", 470,
                po_y, 390, color="amber")
    # Lane 3: journal entries.
    y = low + 62 + 28
    band(y, "3  Journal entries: one table for the entry, another for its lines")
    jy = y + 40
    e = node(0, jy, 100, rh, "<b>Employee</b><br><i>the approver</i>", "gray")
    je = node(270, jy, 130, rh, "<b>JournalEntry</b><br><i>one row for each entry</i>")
    gl = node(550, jy, 80, rh, "<b>GLEntry</b><br><i>its lines</i>")
    c3, _ = control(660, jy, 200, "<b>Control totals</b><br>count of entries and sum of TotalAmount against the debits "
                                  "of the ledger rows", rh)
    d.edge(e, je, color=AMBER, width=2.5, exit=RIGHT, entry=LEFT, label="ApprovedByEmployeeID")
    d.edge(je, gl, color=AMBER, dashed=True, width=2.5, exit=RIGHT, entry=LEFT)
    _above(d, post, 475, jy + rh / 2)
    d.edge(gl, c3, color=GRAY, exit=RIGHT, entry=LEFT)
    # The key.
    ky = jy + rh + 24
    items = [("arrow", "Arrowhead: the direction the test runs", GRAY), ("line", "Solid gray: a join inside a group", GRAY),
             ("line", "Solid amber: a join to another group", AMBER), ("dashed", "Dashed amber: the source-document trace", AMBER)]
    kx, row = 0.0, 0
    for kind, label, color in items:
        width = text_width(label, SMALL, False) + 10
        if kx + 38 + width > 860:
            kx, row = 0.0, row + 1
        d.line_sample(kx, ky + row * 24 + 10, 30, color=color, dashed=kind == "dashed", end="blockThin" if kind == "arrow" else "none",
                      width=1.5 if color == GRAY else 2.5)
        d.text(label, kx + 38, ky + row * 24, width, 20, size=SMALL, valign="middle")
        kx += 38 + width + 18
    d.text("<i>The lanes are plans, not test results, so they carry no counts. Each starts from its population, names the "
           "keys that join the tables and ends in the control total that would show the extract is complete.</i>", 0,
           ky + row * 24 + 30, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-03-6-A: the integrity test log of a finished answer ----------------------------------------------------------

def if_03_6_a() -> Diagram:
    """The Integrity Tests worksheet of a finished answer, with the PivotTable of ledger accounts below the log
    (Exercise 3.6)."""
    v = ctx.values("ch03.ex6")
    data = ctx.data()
    tests = v["tests"]
    assert len(tests) == v["n_tests"], "the log has one row for each relationship of the guide"
    account_test = next(t for t in tests if (t["child"], t["fk"]) == ("GLEntry", "AccountID"))
    accounts = [r[0] for r in data.q("SELECT DISTINCT AccountID FROM GLEntry ORDER BY 1")]
    assert len(accounts) == v["used"] == v["pivot"]["GLEntry.AccountID"], "the PivotTable lists the accounts the ledger uses"
    assert set(accounts) <= {r[0] for r in data.q("SELECT AccountID FROM Account")}, "every listed account is in the chart"
    misses = account_test["orphans"]
    assert misses == 0 and all(t["orphans"] == 0 for t in tests), "no relationship has an orphan"
    heads = ["Child table", "Foreign key", "Parent table", "Primary key", "Rows", "Blank", "Orphans", "Blank allowed because",
             "Verdict"]
    rows = [[t["child"], t["fk"], t["parent"], t["pk"], str(t["rows"]), str(t["blank"]), str(t["orphans"]),
             t["reason"] if t["blank"] else "never blank", "Maintained"] for t in tests]
    assert all(bool(t["reason"]) == bool(t["blank"]) for t in tests), "every blank has a reason, and only blanks do"
    # Column widths: each as wide as its widest value or bold heading, the reason column takes the rest (and wraps).
    letters = list("ABCDEFGHI")
    narrow = {c: max([text_width(heads[c], SMALL, True)] + [text_width(r[c], SMALL, False) for r in rows]) + 14
              for c in range(9) if c != 7}
    number_w = 34
    widths = [number_w] + [round(narrow[c]) if c != 7 else 0 for c in range(9)]
    widths[8] = 860 - sum(widths)
    reason_w = widths[8]
    assert reason_w >= 110, widths
    # (the heading row wraps, the reason column wraps: rows are as tall as their tallest cell)
    d = Diagram("The Integrity Tests Worksheet")
    first_formula = f'=IF(COUNTIFS(Account!A:A,A16)=0,"orphan","ok")'
    xl.formula_bar(d, 0, 0, 860, "B16", first_formula)
    y = 40
    xs = [0.0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)

    def sheet_row(y: float, number: str, values: list[str], h: float, style=None) -> dict:
        return xl.sheet(d, 0, y, [], widths, [(number, values)], style, row_h=h, number_color=GRAY, show_letters=False)

    # Column letters, then the heading row (row 1), then one row for each relationship.
    xl.sheet(d, 0, y, letters, widths, [], None, show_letters=True)
    y += 22
    head_h = 38
    sheet_row(y, "1", heads, head_h, lambda r, c, val: dict(fill=BLUE, stroke=BLUE, color=WHITE, align="left",
                                                           label=f"<b>{esc(val)}</b>".replace("allowed because", "allowed<br>because")))
    table_top = y
    y += head_h
    spans = []
    for k, values in enumerate(rows):
        h = max(24, kit.height_for(values[7], reason_w, SMALL, pad=10))
        band = WHITE if k % 2 == 0 else BLUE_TINT

        def style(r, c, val, band=band) -> dict:
            out = dict(fill=band, align="left" if c in (0, 1, 2, 3, 7, 8) else "right")
            if c == 7 and val == "never blank":
                out.update(color=GRAY)
            return out
        sheet_row(y, str(k + 2), values, h, style)
        spans.append((y, h))
        y += h
    table_bottom = y
    # The PivotTable of the ledger's AccountID values, with the lookup beside it.
    sheet_row(y, "14", [""] * 9, 24)
    y += 24
    pivot_head = ["Row Labels", "In Account?"]
    sheet_row(y, "15", pivot_head + [""] * 7, 24,
              lambda r, c, val: dict(fill=BLUE_TINT if c == 0 else GRAY_TINT, label=f"<b>{esc(val)}</b>", align="left")
              if c < 2 else dict(fill=WHITE))
    y += 24
    shown = accounts[:4]
    for k, acct in enumerate(shown):
        sheet_row(y, str(16 + k), [str(acct), "ok"] + [""] * 7, 24, lambda r, c, val: dict(fill=WHITE, align="left"))
        y += 24
    last_row = 15 + len(accounts)
    d.box(f"<i>rows {16 + len(shown)} to {last_row - 1} are scrolled out of view</i>", 0, y, 860, 24, fill=WHITE, stroke=RULE,
          color=GRAY, size=SMALL, rounded=False, dashed=True)
    y += 24
    sheet_row(y, str(last_row), [str(accounts[-1]), "ok"] + [""] * 7, 24, lambda r, c, val: dict(fill=WHITE, align="left"))
    y += 24
    sheet_row(y, str(last_row + 1), [""] * 9, 24)
    y += 24
    sheet_row(y, str(last_row + 2), ["Misses", str(misses)] + [""] * 7, 24,
              lambda r, c, val: dict(fill=WHITE, align="left", label=f"<b>{esc(val)}</b>") if c < 2 else dict(fill=WHITE))
    pivot_bottom = y + 24
    # Emphasis: no orphans, a verdict of Maintained, and the lookup column of the PivotTable.
    for c in (6, 8):
        xl.emphasis(d, xs[c + 1], table_top, widths[c + 1], table_bottom - table_top)
    xl.emphasis(d, xs[2], table_bottom + 24, widths[2], pivot_bottom - table_bottom - 24)
    xl.sheet_tabs(d, 0, pivot_bottom + 10, ["Account", "GLEntry", "Integrity Tests"], "Integrity Tests")
    d.text(f"<i>A finished answer: one row for each of the {len(tests)} relationships, with counts of rows, blanks and orphans "
           f"and a reason for every blank. The PivotTable below the log lists the {len(accounts)} AccountID values the ledger "
           f"uses, and each is looked up in the AccountID column of Account (the formula bar shows the lookup of the first). "
           f"Outlined: the Orphans and Verdict columns, and the lookup, whose {misses} misses are counted in the last row.</i>", 0, pivot_bottom + 44, 860, 70, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "IF-03-0-A": if_03_0_a,
    "IF-03-0-B": if_03_0_b,
    "IF-03-1-A": if_03_1_a,
    "IF-03-3-A": if_03_3_a,
    "IF-03-4-A": if_03_4_a,
    "IF-03-5-A": if_03_5_a,
    "IF-03-6-A": if_03_6_a,
}
