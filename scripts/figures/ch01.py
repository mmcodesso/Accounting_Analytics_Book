"""Chapter 1 figures."""

from __future__ import annotations

import excel as xl
from data import one, q, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CROSS_WIDTH, GRAY, GRAY_TINT, HEAD, HIGHLIGHT,
                    INK, RULE, ROW_H, SMALL, TEAL, WHITE, Diagram, esc, money)


def card(title: str, subtitle: str, subtitle_color: str = GRAY) -> str:
    """Two-line label: a bold 14 px title over 13 px detail text."""
    return (f'<font style="font-size:{HEAD}px"><b>{title}</b></font><br>'
            f'<font color="{subtitle_color}">{subtitle}</font>')


def fig_01_01() -> Diagram:
    d = Diagram("The Analytics Continuum")
    types = [
        ("Descriptive Analytics", "What happened?", "Revenue summary by quarter"),
        ("Diagnostic Analytics", "Why did it happen?", "Drill-down of a margin decline"),
        ("Predictive Analytics", "What might happen?", "Regression forecast of sales"),
        ("Prescriptive Analytics", "What should we do?", "Optimal product mix via Solver"),
    ]
    w, gap = 190, 32
    boxes = []
    for i, (name, question, example) in enumerate(types):
        x = 2 + i * (w + gap)
        boxes.append(d.box(card(name, f'<i>"{question}"</i>', WHITE), x, 0, w, 72, fill=BLUE,
                           stroke=BLUE, color=WHITE))
        d.text(f"<i>{example}</i>", x, 82, w, 36, align="center")
    for a, b in zip(boxes, boxes[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5))
    d.line_sample(2, 136, 856, color=GRAY, end="block")
    d.text("Increasing analytical complexity", 230, 144, 400, 20, color=GRAY, align="center")
    return d


def fig_01_02() -> Diagram:
    d = Diagram("The Accounting Analytics Workflow")
    stages = [
        ("1. Define the question", "Translate the business need into a specific analytical question"),
        ("2. Access the data", "Identify sources, extract relevant tables and columns"),
        ("3. Prepare and clean", "Resolve missing values, duplicates, inconsistent formatting"),
        ("4. Analyze", "Summarize, compare, model, detect anomalies"),
        ("5. Visualize and present", "Charts, dashboards, interactive reports for stakeholders"),
        ("6. Communicate findings", "Memoranda, presentations, and reports to decision makers"),
    ]
    spots = [(0, 0), (310, 0), (620, 0), (620, 150), (310, 150), (0, 150)]
    fills = [BLUE, BLUE, BLUE, TEAL, TEAL, HIGHLIGHT]
    ids = []
    for (title, text), (x, y), fill in zip(stages, spots, fills):
        color = INK if fill == HIGHLIGHT else WHITE
        ids.append(d.box(card(title, text, color), x, y, 240, 86, fill=fill, stroke=fill,
                         color=color))
    d.arrow(ids[0], ids[1], exit=(1, 0.5), entry=(0, 0.5))
    d.arrow(ids[1], ids[2], exit=(1, 0.5), entry=(0, 0.5))
    d.arrow(ids[2], ids[3], exit=(0.5, 1), entry=(0.5, 0))
    d.arrow(ids[3], ids[4], exit=(0, 0.5), entry=(1, 0.5))
    d.arrow(ids[4], ids[5], exit=(0, 0.5), entry=(1, 0.5))
    d.text("<i>Part I introduces stages 1-2. Parts II and III develop stages 3-4. Part IV develops "
           "stage 5. Every chapter practices stage 6.</i>", 0, 256, 860, 22, color=GRAY,
           align="center")
    return d


def fig_01_03() -> Diagram:
    d = Diagram("The Three Tools and Their Roles in the Analytics Workflow")
    w, step = 124, 147.2
    xs = [round(i * step, 1) for i in range(6)]
    heads = ["1. Define", "2. Access", "3. Prepare", "4. Analyze", "5. Visualize", "6. Communicate"]
    hids = [d.box(f"<b>{h}</b>", x, 0, w, 40, fill=GRAY_TINT, stroke=RULE) for h, x in zip(heads, xs)]
    for a, b in zip(hids, hids[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5))
    tools = [
        ("SQL (Part III)", "Access, prepare, and analyze data from databases", 1, 3, BLUE, WHITE, BLUE),
        ("Excel (Part II)", "Prepare, analyze, and model data", 2, 2, TEAL, WHITE, TEAL),
        ("Power BI (Part IV)", "Analyze, visualize, and communicate", 3, 2, HIGHLIGHT, INK, AMBER),
    ]
    for row, (name, role, col, span, fill, color, border) in enumerate(tools):
        y = 70 + row * 82
        bar = d.box(card(name, role, color), xs[col], y, xs[col + span - 1] + w - xs[col], 62,
                    fill=fill, stroke=fill, color=color)
        comm = d.box("Communicate", xs[5], y, w, 62, fill=WHITE, stroke=border, dashed=True,
                     stroke_width=1.5)
        d.edge(bar, comm, color=GRAY, dashed=True, exit=(1, 0.5), entry=(0, 0.5))
    d.text("<i>Solid bars show the stages where each tool does most of its work. Dashed boxes show "
           "that every tool also helps communicate the results.</i>", 0, 322, 860, 40, color=GRAY,
           align="center")
    return d


def fig_01_04() -> Diagram:
    d = Diagram("Charles River High-Level Architecture Diagram")
    LX, CX, RX, LW, CW, RW = 0, 318, 610, 250, 224, 250

    def group(x: float, y: float, w: float, name: str, tables: str, note: str, fill: str,
              dashed: bool = False, body_h: float = 76) -> str:
        color = INK if fill == GRAY_TINT else WHITE
        d.box(f"<b>{name}</b>", x, y, w, 28, fill=fill,
              stroke=TEAL if dashed else (GRAY if fill == GRAY_TINT else fill),
              color=color, size=HEAD, rounded=False, dashed=dashed)
        body = tables + (f'<br><i><font color="{GRAY}">{note}</font></i>' if note else "")
        d.box(body, x, y + 28, w, body_h, fill=WHITE,
              stroke=TEAL if dashed else (GRAY if fill == GRAY_TINT else RULE),
              align="left", valign="top", rounded=False, dashed=dashed)
        return d.container(x, y, w, 28 + body_h)

    left = [
        ("Order-to-Cash", "SalesOrder, Shipment, SalesInvoice, CashReceipt, ...",
         "Posts through invoices, shipments, and cash receipts"),
        ("Procure-to-Pay", "PurchaseOrder, GoodsReceipt, PurchaseInvoice, ...",
         "Posts through goods receipts, invoices, and payments"),
        ("Manufacturing", "BillOfMaterial, WorkOrder, ProductionCompletion, ...",
         "Posts through material issues, completions, and closes"),
        ("Payroll and Time", "PayrollRegister, LaborTimeEntry, PayrollPayment, ...",
         "Posts through payroll summaries, payments, and remittances"),
    ]
    cycles, mids = [], []
    y = 0
    for i, (name, tables, note) in enumerate(left):
        cycles.append(group(LX, y, LW, name, tables, note, TEAL))
        mids.append(y + 52)
        y += 104 + 12
        if i == 0:
            group(LX + 20, y, LW - 20, "Design Services",
                  "Within Order-to-Cash: ServiceEngagement, ServiceTimeEntry, ServiceBillingLine",
                  "", GRAY_TINT, dashed=True, body_h=60)
            y += 88 + 12
    right = [
        ("Fixed Assets and Financing", "FixedAsset, DebtAgreement, ...", "Posts through purchase invoices and journal entries", TEAL),
        ("Master Data", "Item, Warehouse, Employee", "Shared keys: ItemID, EmployeeID", GRAY_TINT),
        ("Organizational Planning", "CostCenter, Budget, BudgetLine", "Shared keys: CostCenterID, AccountID", GRAY_TINT),
        ("Demand Planning and MRP", "DemandForecast, InventoryPolicy, ...", "Shared key: ItemID", GRAY_TINT),
    ]
    refs = []
    for i, (name, tables, note, fill) in enumerate(right):
        refs.append(group(RX, 40 + i * 124, RW, name, tables, note, fill, body_h=62))

    core_y = 170
    d.box("<b>Accounting Core</b>", CX, core_y, CW, 28, fill=BLUE, stroke=BLUE, color=WHITE,
          size=HEAD, rounded=False)
    d.box("Account, JournalEntry, GLEntry", CX, core_y + 28, CW, 196, fill=WHITE, stroke=BLUE,
          valign="top", rounded=False)
    core = d.container(CX, core_y, CW, 224)
    gl_y, gl_h = core_y + 76, 120
    gl = d.box(card("GLEntry", "Every posting from every business cycle", WHITE), CX + 16,
               gl_y, CW - 32, gl_h, fill=BLUE, stroke=BLUE, color=WHITE)
    # Separate lanes keep the four posting arrows from overlapping in the gap.
    for i, (src, mid, lane) in enumerate(zip(cycles, mids, [300, 288, 288, 300])):
        entry = 0.2 + 0.2 * i
        d.arrow(src, gl, color=AMBER, dashed=True, exit=(1, 0.5), entry=(0, entry),
                points=[(lane, mid), (lane, gl_y + entry * gl_h)])
    d.arrow(refs[0], gl, color=AMBER, dashed=True, exit=(0, 0.5), entry=(1, 0.3))
    for i, src in enumerate(refs[1:]):
        d.edge(src, core, color=AMBER, end="blockThin", width=CROSS_WIDTH, exit=(0, 0.5),
               entry=(1, 0.62 + 0.14 * i))

    y = d.bottom + 24
    d.line_sample(0, y + 9, 44, color=AMBER, dashed=True, end="blockThin")
    d.text("Posts to the general ledger", 52, y, 220, 20)
    d.line_sample(290, y + 9, 44, color=AMBER, end="blockThin", width=CROSS_WIDTH)
    d.text("Shared keys", 342, y, 120, 20)
    for x, fill, label in [(470, TEAL, "Business cycle"), (620, GRAY_TINT, "Reference and planning")]:
        d.box("", x, y + 2, 16, 16, fill=fill, stroke=TEAL if fill == TEAL else GRAY,
              rounded=False)
        d.text(label, x + 22, y, 180, 20)
    return d


def fig_01_05() -> Diagram:
    d = Diagram("Simplified O2C Process Flow")
    W, H, xs = 190, 66, [0, 223, 446, 669]
    row1 = [("Customer", "places orders"), ("SalesOrder", "customer, date, status"),
            ("SalesOrderLine", "item, quantity, price"), ("Item", "Master Data: product, cost")]
    row2 = [("Shipment", "ship date, carrier, tracking"), ("SalesInvoice", "invoice date, total, terms"),
            ("CashReceipt", "receipt date, amount, method"), ("CashReceiptApplication", "matches receipts to invoices")]
    top = [d.box(card(t, s), x, 0, W, H, stroke=GRAY if t == "Item" else TEAL, stroke_width=1.5)
           for (t, s), x in zip(row1, xs)]
    bottom = [d.box(card(t, s), x, 150, W, H, stroke=TEAL, stroke_width=1.5)
              for (t, s), x in zip(row2, xs)]
    gl = d.box(card("GLEntry", "Accounting Core: every posting the cycle creates", WHITE), 0, 300,
               860, 52, fill=BLUE, stroke=BLUE, color=WHITE)
    d.arrow(top[0], top[1], exit=(1, 0.5), entry=(0, 0.5))
    d.arrow(top[1], top[2], exit=(1, 0.5), entry=(0, 0.5))
    d.arrow(top[3], top[2], color=AMBER, width=CROSS_WIDTH, exit=(0, 0.5), entry=(1, 0.5))
    d.arrow(top[2], bottom[0], exit=(0.5, 1), entry=(0.5, 0),
            points=[(xs[2] + W / 2, 108), (W / 2, 108)])
    for a, b in zip(bottom, bottom[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5))
    for src, x, label in zip(bottom, xs, ["COGS and inventory", "revenue and AR", "cash",
                                          "clears AR"]):
        d.arrow(src, gl, color=AMBER, dashed=True, label=label, exit=(0.5, 1),
                entry=(round((x + W / 2) / 860, 4), 0))
    y = 372
    d.line_sample(0, y + 9, 44, color=GRAY, end="blockThin")
    d.text("Business process flow", 52, y, 200, 20)
    d.line_sample(250, y + 9, 44, color=AMBER, dashed=True, end="blockThin")
    d.text("Posts to the general ledger", 302, y, 240, 20)
    d.line_sample(560, y + 9, 44, color=AMBER, end="blockThin", width=CROSS_WIDTH)
    d.text("Link to Master Data", 612, y, 240, 20)
    return d


def fig_01_06() -> Diagram:
    d = Diagram("One Ledger Posting Traced to Its Source")
    gl = one("SELECT GLEntryID, PostingDate, AccountID, Debit, Credit, SourceDocumentType, "
             "SourceDocumentID, SourceLineID FROM GLEntry WHERE GLEntryID = 126312")
    assert gl[5:] == ("SalesInvoice", 7947, 10645), gl
    acc = one("SELECT AccountID, AccountNumber, AccountName, AccountType FROM Account "
              "WHERE AccountID = ?", gl[2])
    inv = one("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate, GrandTotal FROM SalesInvoice "
              "WHERE SalesInvoiceID = ?", gl[6])
    line = one("SELECT l.SalesInvoiceLineID, l.ItemID, i.ItemCode, l.Quantity, l.UnitPrice, "
               "l.LineTotal FROM SalesInvoiceLine l JOIN Item i USING (ItemID) "
               "WHERE l.SalesInvoiceLineID = ?", gl[7])

    def record(x: float, y: float, name: str, pairs: list[tuple[str, str]], focus: bool,
               tints: dict[str, str], group: str | None = None, kw: float = 170):
        """A one-row record shown as column/value pairs. Returns key-cell and value-cell ids."""
        w = 360
        if group:
            d.text(f"<i>{group}</i>", x, y - 19, w, 18, size=SMALL, color=GRAY, valign="bottom")
        keys = {"__header__": d.header_box(esc(name), x, y, w, fill=BLUE if focus else GRAY)}
        values = {}
        for i, (key, value) in enumerate(pairs):
            ry = y + 30 + i * ROW_H
            tint = tints.get(key)
            bg = tint or (WHITE if i % 2 == 0 else GRAY_TINT)
            keys[key] = d.box(esc(key), x, ry, kw, ROW_H, fill=bg, stroke=RULE, align="left",
                              rounded=False, bold=bool(tint))
            values[key] = d.box(esc(value), x + kw, ry, w - kw, ROW_H, fill=bg, stroke=RULE,
                                align="left", rounded=False)
        return keys, values

    _, g = record(0, 60, "GLEntry", [
        ("GLEntryID", str(gl[0])), ("PostingDate", gl[1]), ("AccountID", str(gl[2])),
        ("Debit", money(gl[3])), ("Credit", money(gl[4])), ("SourceDocumentType", gl[5]),
        ("SourceDocumentID", str(gl[6])), ("SourceLineID", str(gl[7]))], True,
        {"AccountID": BLUE_TINT, "SourceDocumentType": AMBER_TINT,
         "SourceDocumentID": AMBER_TINT, "SourceLineID": AMBER_TINT})
    a, _ = record(500, 0, "Account", [
        ("AccountID", str(acc[0])), ("AccountNumber", str(acc[1])), ("AccountName", acc[2]),
        ("AccountType", acc[3])], True, {"AccountID": BLUE_TINT}, kw=150)
    s, _ = record(500, 190, "SalesInvoice", [
        ("SalesInvoiceID", str(inv[0])), ("InvoiceNumber", inv[1]), ("InvoiceDate", inv[2]),
        ("GrandTotal", money(inv[3]))], False, {"SalesInvoiceID": AMBER_TINT},
        group="Order-to-Cash", kw=150)
    ln, _ = record(500, 360, "SalesInvoiceLine", [
        ("SalesInvoiceLineID", str(line[0])), ("ItemID", f"{line[1]} ({line[2]})"),
        ("Quantity", f"{line[3]:g}"), ("UnitPrice", money(line[4])),
        ("LineTotal", money(line[5]))], False, {"SalesInvoiceLineID": AMBER_TINT},
        group="Order-to-Cash", kw=150)

    # Rows are 24 px from y + 30, so a row's center is y + 42 + 24 * index.
    lane = 410
    links = [
        (g["AccountID"], a["AccountID"], 150, 42, "which account", GRAY, False),
        (g["SourceDocumentType"], s["__header__"], 222, 205, "which table", AMBER, True),
        (g["SourceDocumentID"], s["SalesInvoiceID"], 246, 232, "which row", AMBER, True),
        (g["SourceLineID"], ln["SalesInvoiceLineID"], 270, 402, "which line", AMBER, True),
    ]
    for src, tgt, y0, y1, label, color, dashed in links:
        d.arrow(src, tgt, color=color, dashed=dashed, exit=(1, 0.5), entry=(0, 0.5),
                points=[(lane, y0), (lane, y1)])
        d.text(label, lane + 2, y1 - 19, 500 - lane - 4, 17, size=SMALL, color=GRAY,
               valign="bottom")
    d.text("The three source columns identify the document, and the line within it, that created "
           "the posting. AccountID identifies the account it was posted to.", 0, 316, 390, 60)
    y = 400
    d.line_sample(0, y + 9, 44, color=GRAY, end="blockThin")
    d.text("A key column (AccountID)", 52, y, 300, 20)
    d.line_sample(0, y + 39, 44, color=AMBER, dashed=True, end="blockThin")
    d.text("The source-document trace", 52, y + 30, 300, 20)
    return d


def fig_01_08() -> Diagram:
    d = Diagram("Book Organization Map")

    def part(x, y, w, h, label, fill, caption=None):
        color = INK if fill in (GRAY_TINT, HIGHLIGHT) else WHITE
        pid = d.box(label, x, y, w, h, fill=fill, stroke=GRAY if fill == GRAY_TINT else fill,
                    color=color)
        if caption:
            d.text(f"<i>{caption}</i>", x, y + h + 4, w, 36, size=SMALL, color=GRAY, align="center")
        return pid

    p1 = part(0, 120, 150, 90, card("Part I", "Foundations", INK), GRAY_TINT,
              "All table groups, at overview level")
    p2 = part(225, 0, 200, 64, card("Part II", "Excel", WHITE), TEAL,
              "Sales and ledger, then planning and purchasing")
    p3 = part(225, 125, 200, 64, card("Part III", "SQL", WHITE), BLUE,
              "Expands into Procure-to-Pay and Manufacturing")
    p4 = part(225, 250, 200, 64, card("Part IV", "Power BI", INK), HIGHLIGHT,
              "Data models that span table groups")
    p5 = part(500, 100, 360, 130, card("Part V", "Capstone Cases<br>Three independent cases in financial "
                                        "reporting,<br>managerial accounting, and auditing", WHITE), GRAY,
              "All three tools, each where it fits, and all table groups")
    for p in (p2, p3, p4):
        d.arrow(p1, p, exit=(1, 0.5), entry=(0, 0.5))
        d.arrow(p, p5, exit=(1, 0.5), entry=(0, 0.5))
    d.text("All parts use the <b>Charles River Accounting Dataset</b>, and table groups are introduced "
           "progressively.<br>A comprehensive case closes each of Parts I to IV.", 0, 364, 860, 40,
           align="center")
    return d


def fig_01_07() -> Diagram:
    d = Diagram("The Charles River SalesOrder Worksheet")
    cols = ["SalesOrderID", "OrderNumber", "OrderDate", "CustomerID", "RequestedDeliveryDate",
            "Status", "SalesRepEmployeeID"]
    require_columns("SalesOrder", cols)
    table_cols = [r[1] for r in q("PRAGMA table_info(SalesOrder)")]
    assert table_cols[:len(cols)] == cols, table_cols
    first, last, count = one("SELECT MIN(SalesOrderID), MAX(SalesOrderID), COUNT(*) FROM SalesOrder")
    assert (first, last) == (1, count), "row numbers assume IDs 1..n in worksheet order"
    orphans = one("SELECT COUNT(*) FROM SalesOrder o WHERE NOT EXISTS "
                  "(SELECT 1 FROM Customer c WHERE c.CustomerID = o.CustomerID)")[0]
    assert orphans == 0, orphans
    rows = q(f"SELECT {', '.join(cols)} FROM SalesOrder ORDER BY SalesOrderID LIMIT 14")

    widths = [40, 100, 130, 92, 92, 164, 70, 150]
    body = [(str(r[0] + 1), [str(v) for v in r]) for r in rows]
    geo = xl.table_view(d, 0, 0, list("ABCDEFG"), widths, cols, body)
    xl.emphasis(d, *xl.column_box(geo, 3, len(body) + 1))
    bottom = 22 + ROW_H * (len(body) + 1)
    xl.sheet_tabs(d, 0, bottom + 6, xl.tabs_around("SalesOrder", 4, 3), "SalesOrder")
    d.text("<i>Outlined: CustomerID, the column that links each order to the customer who placed "
           "it.</i>", 0, bottom + 38, 860, 20, size=SMALL, color=GRAY)
    return d

FIGURES = {
    "fig-01-01-analytics-continuum": fig_01_01,
    "fig-01-02-analytics-workflow": fig_01_02,
    "fig-01-03-tools-workflow-mapping": fig_01_03,
    "fig-01-04-charles-river-architecture": fig_01_04,
    "fig-01-05-o2c-process-flow": fig_01_05,
    "fig-01-06-ledger-posting-trace": fig_01_06,
    "fig-01-07-salesorder-worksheet": fig_01_07,
    "fig-01-08-book-organization-map": fig_01_08,
}

