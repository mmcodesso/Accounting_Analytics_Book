"""Chapter 3 figures: real rows from the dataset and data-true ER endpoints."""

from __future__ import annotations

from data import cardinality, one, q, relate, require_columns, trace
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CROSS_WIDTH, GRAY, GRAY_TINT, HEAD,
                    INK, LINE_WIDTH, RULE, ROW_H, SMALL, TEAL, WHITE, Diagram, Table, esc, money)

BOTTOM, TOP, LEFT, RIGHT = (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)


def table(d: Diagram, name: str, x: float, y: float, rows: list[tuple[str, str]], w: float = 240,
          focus: bool = True, group: str | None = None, caption_below: bool = False) -> Table:
    """An ER table whose columns are checked against the database first."""
    require_columns(name, [column for _, column in rows])
    return d.table(name, x, y, rows, w=w, focus=focus, group=group, caption_below=caption_below)


def legend(d: Diagram, x: float, y: float, w: float, trace_item: bool = False,
           stacked: bool = False) -> None:
    """Line styles used by the ER figures, matching the notation taught in the chapter."""
    items = [(GRAY, False, "Relationship within the table group"),
             (AMBER, False, "Relationship to a table in another group")]
    if trace_item:
        items.append((AMBER, True, "Source-document trace (SourceDocumentType and SourceDocumentID)"))
    note = "Solid lines are logical foreign keys: the file does not declare them."
    if stacked:
        h = 44 * len(items) + 60
        d.box("", x, y, w, h, fill=GRAY_TINT, stroke=RULE)
        for i, (color, dashed, label) in enumerate(items):
            d.line_sample(x + 12, y + 20 + 44 * i, 40, color=color, dashed=dashed,
                          width=CROSS_WIDTH if color == AMBER and not dashed else LINE_WIDTH)
            d.text(label, x + 60, y + 10 + 44 * i, w - 68, 36, size=SMALL)
        d.text(f"<i>{note}</i>", x + 12, y + 12 + 44 * len(items), w - 24, 40, size=SMALL,
               color=GRAY)
        return
    h = 26 * len(items) + 34
    d.box("", x, y, w, h, fill=GRAY_TINT, stroke=RULE)
    for i, (color, dashed, label) in enumerate(items):
        d.line_sample(x + 12, y + 18 + 26 * i, 44, color=color, dashed=dashed,
                      width=CROSS_WIDTH if color == AMBER and not dashed else LINE_WIDTH)
        d.text(label, x + 66, y + 8 + 26 * i, w - 76, 20, size=SMALL)
    d.text(f"<i>{note}</i>", x + 12, y + 8 + 26 * len(items), w - 24, 20, size=SMALL, color=GRAY)


def fig_03_01() -> Diagram:
    d = Diagram("Anatomy of a Database Table")
    rows = q("SELECT CustomerID, CustomerName, CustomerSegment, Region, CreditLimit, PaymentTerms "
             "FROM Customer WHERE CustomerID IN (1, 2, 4, 5, 12) ORDER BY CustomerID")
    rows = [(str(a), b, c, r, money(cl), pt) for a, b, c, r, cl, pt in rows]
    X, W = 40, [95, 210, 140, 90, 115, 115]
    xs = [X + sum(W[:i]) for i in range(len(W))]
    d.header_box("Customer", X, 0, sum(W))
    d.grid(X, 30, ["CustomerID", "CustomerName", "CustomerSegment", "Region", "CreditLimit",
                   "PaymentTerms"], W, rows, highlight={(5, 3)})
    grid_h = ROW_H * (len(rows) + 1)
    bottom = 30 + grid_h
    d.outline(xs[0], 30, W[0], grid_h, BLUE)
    d.outline(xs[2], 30, W[2], grid_h, TEAL)
    d.outline(X, 30 + ROW_H * 3, sum(W), ROW_H, AMBER)
    d.marker("1", 4, 3, BLUE)
    d.marker("2", xs[2] + W[2] / 2 - 12, bottom + 8, TEAL)
    d.marker("3", 4, 30 + ROW_H * 3, AMBER)
    d.marker("4", xs[0] + W[0] / 2 - 12, bottom + 8, BLUE)
    d.marker("5", xs[3] + W[3] / 2 - 12, bottom + 8, CORAL)
    d.text("<b>1 Table name.</b> The table stores one type of entity: customers.<br>"
           "<b>2 Column.</b> One attribute recorded for every customer, here CustomerSegment.<br>"
           "<b>3 Row.</b> One customer and all of its attributes.<br>"
           "<b>4 Primary key.</b> CustomerID uniquely identifies each row.<br>"
           f"<b>5 Cell value.</b> The value of one attribute for one customer: the Region of "
           f"customer {rows[4][0]}.", X, bottom + 44, sum(W), 100)
    return d


def fig_03_02() -> Diagram:
    d = Diagram("Primary Keys and Foreign Keys")
    so = q("SELECT SalesOrderID, OrderNumber, CustomerID FROM SalesOrder "
           "WHERE SalesOrderID IN (59, 62, 85) ORDER BY CustomerID, SalesOrderID")
    cu = q("SELECT CustomerID, CustomerName FROM Customer WHERE CustomerID IN (1, 4) "
           "ORDER BY CustomerID")
    SX, SW, CX, CW = 0, [115, 140, 110], 545, [110, 205]
    so_bar = d.header_box("SalesOrder", SX, 30, sum(SW))
    cu_bar = d.header_box("Customer", CX, 30, sum(CW))
    gs = d.grid(SX, 60, ["PK SalesOrderID", "OrderNumber", "FK CustomerID"], SW,
                [(str(a), b, str(c)) for a, b, c in so], highlight={(1, 2), (2, 2), (3, 2)})
    gc = d.grid(CX, 60, ["PK CustomerID", "CustomerName"], CW,
                [(str(a), b) for a, b in cu], highlight={(1, 0), (2, 0)})
    row_of = {r[0]: i for i, r in enumerate(cu, 1)}
    for i, r in enumerate(so, 1):
        # One lane per order keeps the jogs from crossing; rows start at y = 84.
        lane = 400 + 40 * i
        d.arrow(gs[(i, 2)], gc[(row_of[r[2]], 0)], color=AMBER, exit=RIGHT, entry=LEFT,
                points=[(lane, 72 + ROW_H * i), (lane, 72 + ROW_H * row_of[r[2]])])
    relate(d, "Customer", "CustomerID", "SalesOrder", "CustomerID", cu_bar, so_bar, exit=LEFT,
           entry=RIGHT)
    d.text("<i>One customer places zero or many sales orders</i>", 230, 0, 400, 22, color=GRAY,
           align="center")
    orders = [r for r in so if r[2] == 1]
    d.text("<b>Primary key (PK).</b> CustomerID uniquely identifies each customer in the Customer "
           "table.<br><b>Foreign key (FK).</b> SalesOrder.CustomerID stores the CustomerID of the "
           f"customer who placed each order. Orders {orders[0][0]} and {orders[1][0]} both point to "
           f"{esc(cu[0][1])}, customer 1.", 0, 60 + ROW_H * 4 + 20, 860, 60)
    return d


def fig_03_03() -> Diagram:
    d = Diagram("Three Types of Cardinality")

    def heading(y: float, title: str, note: str) -> None:
        d.text(f"<b>{title}</b>", 0, y, 860, 20, size=HEAD, color=BLUE)
        d.text(f"<i>{note}</i>", 0, y + 22, 860, 38, color=GRAY)

    heading(0, "One-to-one (one to zero or one)",
            "Each work order is closed at most once, and a work order that is still open has no "
            "close record yet.")
    wo = table(d, "WorkOrder", 0, 90, [("PK", "WorkOrderID"), ("", "WorkOrderNumber"), ("", "Status")],
               w=250)
    wc = table(d, "WorkOrderClose", 610, 66, [("PK", "WorkOrderCloseID"), ("FK", "WorkOrderID"),
                                            ("", "TotalVarianceAmount")], w=250)
    relate(d, "WorkOrder", "WorkOrderID", "WorkOrderClose", "WorkOrderID", wo.rows["WorkOrderID"],
           wc.rows["WorkOrderID"], exit=RIGHT, entry=LEFT)

    heading(210, "One-to-many",
            "One customer can place many sales orders, and each order belongs to one customer. "
            "Some customers have no orders yet.")
    cu = table(d, "Customer", 0, 300, [("PK", "CustomerID"), ("", "CustomerName"),
                                       ("", "CustomerSegment")], w=250)
    so = table(d, "SalesOrder", 610, 276, [("PK", "SalesOrderID"), ("FK", "CustomerID"),
                                           ("", "OrderDate")], w=250)
    relate(d, "Customer", "CustomerID", "SalesOrder", "CustomerID", cu.rows["CustomerID"],
           so.rows["CustomerID"], exit=RIGHT, entry=LEFT)

    heading(420, "Many-to-many, resolved by a junction table",
            "An order has one or more lines, and an item can appear on many lines. SalesOrderLine "
            "turns the many-to-many link into two one-to-many links.")
    so2 = table(d, "SalesOrder", 0, 534, [("PK", "SalesOrderID"), ("", "OrderDate")], w=220)
    sol = table(d, "SalesOrderLine", 315, 510, [("PK", "SalesOrderLineID"), ("FK", "SalesOrderID"),
                                                ("FK", "ItemID"), ("", "Quantity")], w=230)
    it = table(d, "Item", 640, 558, [("PK", "ItemID"), ("", "ItemName")], w=220, focus=False,
               group="Master Data")
    d.text("<i>junction table</i>", 315, sol.bottom + 4, 230, 18, size=SMALL, color=AMBER,
           align="center")
    relate(d, "SalesOrder", "SalesOrderID", "SalesOrderLine", "SalesOrderID",
           so2.rows["SalesOrderID"], sol.rows["SalesOrderID"], exit=RIGHT, entry=LEFT)
    relate(d, "Item", "ItemID", "SalesOrderLine", "ItemID", it.rows["ItemID"], sol.rows["ItemID"],
           color=AMBER, exit=LEFT, entry=RIGHT)
    return d


def fig_03_04() -> Diagram:
    d = Diagram("Crow's Foot Notation")
    for x, w, label in [(0, 180, "Symbol"), (180, 150, "Meaning"), (330, 530, "Charles River example")]:
        d.header_box(label, x, 0, w, 30, fill=GRAY)
    rows = [("ERmandOne", "Exactly one", "Each SalesOrderLine belongs to exactly one SalesOrder."),
            ("ERzeroToOne", "Zero or one",
             "A WorkOrder has zero or one WorkOrderClose record: open work orders have none."),
            ("ERoneToMany", "One or many", "A SalesOrder has one or more SalesOrderLines."),
            ("ERzeroToMany", "Zero or many",
             "A Customer has zero or more SalesOrders: some customers have not ordered yet.")]
    # The examples are claims about the data, so confirm each one.
    assert cardinality("SalesOrder", "SalesOrderID", "SalesOrderLine", "SalesOrderID") == \
        ("ERmandOne", "ERoneToMany")
    assert cardinality("WorkOrder", "WorkOrderID", "WorkOrderClose", "WorkOrderID")[1] == \
        "ERzeroToOne"
    assert cardinality("Customer", "CustomerID", "SalesOrder", "CustomerID")[1] == "ERzeroToMany"
    for i, (symbol, meaning, example) in enumerate(rows):
        y = 30 + i * 64
        d.box("", 0, y, 860, 64, fill=WHITE if i % 2 == 0 else GRAY_TINT, stroke=RULE,
              rounded=False)
        a, b = d.anchor(30, y + 32), d.anchor(150, y + 32)
        d.edge(a, b, end=symbol, color=INK, width=2, marker_size=14)
        d.text(f"<b>{meaning}</b>", 190, y + 20, 140, 24, valign="middle")
        d.text(example, 340, y + 10, 510, 44, valign="middle")
    d.text("<b>Reading a relationship.</b> Each end of a line describes the table it touches. For "
           "Customer and SalesOrder, the bar at the Customer end means each order has exactly one "
           "customer, and the circle with a crow's foot at the SalesOrder end means each customer "
           "has zero or many orders.", 0, 300, 860, 60)
    return d


def fig_03_05() -> Diagram:
    d = Diagram("The Chart of Accounts as a Table")
    ids = (1, 2, 3, 11, 12, 41, 42, 101)
    acc = q(f"SELECT AccountID, AccountNumber, AccountName, AccountType, AccountSubType, "
            f"ParentAccountID FROM Account WHERE AccountID IN {ids} ORDER BY AccountNumber")
    W = [100, 120, 215, 100, 150, 145]
    d.header_box("Account", 0, 0, sum(W))
    rows = [(str(a), str(n), nm, t, st, "" if p is None else str(p)) for a, n, nm, t, st, p in acc]
    r_ff = next(i for i, r in enumerate(acc, 1) if r[2] == "Furniture and Fixtures")
    r_fa = next(i for i, r in enumerate(acc, 1) if r[2] == "Fixed Assets")
    assert acc[r_ff - 1][5] == acc[r_fa - 1][0]
    d.grid(0, 30, ["PK AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType",
                   "FK ParentAccountID"], W, rows, highlight={(r_ff, 5), (r_fa, 0)})
    top = 30 + ROW_H * (len(acc) + 1) + 24
    d.text("<i>Resulting hierarchy</i>", 0, top, 300, 18, size=SMALL, color=GRAY)
    name = {r[0]: f"{r[1]} {r[2]}" for r in acc}
    level = {1: 0, 2: 1, 3: 1, 11: 1, 12: 2, 41: 0, 42: 1, 101: 1}
    parent = {r[0]: r[5] for r in acc}
    nodes, y = {}, top + 24
    for aid in (1, 2, 3, 11, 12, 41, 42, 101):
        if aid == 41:
            y += 12
        root = level[aid] == 0 or aid == 11
        nodes[aid] = d.box(f"<b>{esc(name[aid])}</b>" if root else esc(name[aid]),
                           level[aid] * 30, y, 270, 26, fill=BLUE_TINT if root else WHITE,
                           stroke=BLUE, align="left")
        y += 34
    for child, par in parent.items():
        if par in nodes:
            d.edge(nodes[par], nodes[child], color=BLUE, exit=(0.06, 1), entry=(0, 0.5))
    d.text("<b>Self-reference.</b> ParentAccountID points to another row in the same table. The "
           f"highlighted ParentAccountID ({acc[r_ff - 1][5]}) is the AccountID of "
           f"{acc[r_fa - 1][2]}, so Furniture and Fixtures sits under Fixed Assets.<br><br>"
           "AccountSubType marks summary accounts as Header, and no entries post to them. Current "
           "assets are identified by their subtype, not by a parent account.",
           360, top + 24, 500, 170)
    return d


def fig_03_06() -> Diagram:
    d = Diagram("General Ledger and Sub-Ledgers")
    gl = table(d, "GLEntry", 300, 0, [("PK", "GLEntryID"), ("", "PostingDate"), ("FK", "AccountID"),
                                      ("", "Debit"), ("", "Credit"), ("", "SourceDocumentType"),
                                      ("", "SourceDocumentID"), ("", "SourceLineID")], w=250)
    acc = table(d, "Account", 0, 48, [("PK", "AccountID"), ("", "AccountNumber"),
                                      ("", "AccountName"), ("", "AccountType")], w=220)
    relate(d, "Account", "AccountID", "GLEntry", "AccountID", acc.rows["AccountID"],
           gl.rows["AccountID"], exit=RIGHT, entry=LEFT)
    d.box("<b>The source-document trace.</b> SourceDocumentType names the table a posting came "
          "from, and SourceDocumentID holds the key of the row in that table. Because one column "
          "can point to several different tables, no single foreign key can describe the link. It "
          "is a logical link that analysts test.", 600, 0, 260, 142, fill=AMBER_TINT, stroke=AMBER,
          align="left", valign="top")
    sources = [("SalesInvoice", "SalesInvoiceID", "Order-to-Cash", ["InvoiceNumber", "GrandTotal"]),
               ("PurchaseInvoice", "PurchaseInvoiceID", "Procure-to-Pay",
                ["InvoiceNumber", "GrandTotal"]),
               ("PayrollPayment", "PayrollPaymentID", "Payroll and Time",
                ["PaymentDate", "PaymentMethod"]),
               ("JournalEntry", "JournalEntryID", None, ["EntryType", "TotalAmount"])]
    lanes = [250, 280, 280, 250]
    for i, (name, pk, group, cols) in enumerate(sources):
        x = i * 220
        t = table(d, name, x, 330, [("PK", pk)] + [("", c) for c in cols], w=200,
                  focus=group is None, group=group, caption_below=True)
        fx = 0.2 + 0.2 * i
        trace(d, name, pk, t.id, gl.id, exit=TOP, entry=(fx, 1),
              points=[(x + 100, lanes[i]), (300 + 250 * fx, lanes[i])])
    legend(d, 0, 470, 860, trace_item=True)
    return d


def fig_03_07() -> Diagram:
    d = Diagram("O2C Core ER Diagram")
    C0, C1, C2, W = 0, 290, 580, 240
    cu = table(d, "Customer", C1, 20, [("PK", "CustomerID"), ("", "CustomerName"),
                                       ("", "CustomerSegment")], w=W)
    it = table(d, "Item", C2, 20, [("PK", "ItemID"), ("", "ItemCode"), ("", "ItemName")], w=W,
               focus=False, group="Master Data")
    so = table(d, "SalesOrder", C1, 182, [("PK", "SalesOrderID"), ("", "OrderNumber"),
                                          ("FK", "CustomerID"), ("", "OrderDate")], w=W)
    sol = table(d, "SalesOrderLine", C2, 158, [("PK", "SalesOrderLineID"), ("FK", "SalesOrderID"),
                                               ("FK", "ItemID"), ("", "Quantity"),
                                               ("", "LineTotal")], w=W)
    sh = table(d, "Shipment", C1, 368, [("PK", "ShipmentID"), ("", "ShipmentNumber"),
                                        ("FK", "SalesOrderID"), ("", "ShipmentDate")], w=W)
    shl = table(d, "ShipmentLine", C2, 344, [("PK", "ShipmentLineID"), ("FK", "ShipmentID"),
                                             ("FK", "SalesOrderLineID"), ("", "QuantityShipped")],
                w=W)
    si = table(d, "SalesInvoice", C1, 530, [("PK", "SalesInvoiceID"), ("", "InvoiceNumber"),
                                            ("FK", "SalesOrderID"), ("", "InvoiceDate"),
                                            ("", "GrandTotal")], w=W)
    sil = table(d, "SalesInvoiceLine", C2, 506, [("PK", "SalesInvoiceLineID"),
                                                 ("FK", "SalesInvoiceID"), ("FK", "ShipmentLineID"),
                                                 ("FK", "SalesOrderLineID"), ("", "LineTotal")], w=W)
    cra = table(d, "CashReceiptApplication", C1, 716, [("PK", "CashReceiptApplicationID"),
                                                       ("FK", "CashReceiptID"),
                                                       ("FK", "SalesInvoiceID"),
                                                       ("", "AppliedAmount")], w=W)
    cr = table(d, "CashReceipt", C0, 740, [("PK", "CashReceiptID"), ("", "ReceiptNumber"),
                                           ("", "ReceiptDate"), ("", "Amount")], w=W)
    relate(d, "Customer", "CustomerID", "SalesOrder", "CustomerID", cu.id, so.id, exit=BOTTOM,
           entry=TOP)
    relate(d, "Item", "ItemID", "SalesOrderLine", "ItemID", it.id, sol.id, color=AMBER,
           exit=BOTTOM, entry=TOP)
    relate(d, "SalesOrder", "SalesOrderID", "SalesOrderLine", "SalesOrderID",
           so.rows["SalesOrderID"], sol.rows["SalesOrderID"], exit=RIGHT, entry=LEFT)
    relate(d, "SalesOrder", "SalesOrderID", "Shipment", "SalesOrderID", so.id, sh.id, exit=BOTTOM,
           entry=TOP)
    relate(d, "Shipment", "ShipmentID", "ShipmentLine", "ShipmentID", sh.rows["ShipmentID"],
           shl.rows["ShipmentID"], exit=RIGHT, entry=LEFT)
    relate(d, "SalesOrderLine", "SalesOrderLineID", "ShipmentLine", "SalesOrderLineID", sol.id,
           shl.id, exit=BOTTOM, entry=TOP)
    relate(d, "SalesOrder", "SalesOrderID", "SalesInvoice", "SalesOrderID", so.rows["SalesOrderID"],
           si.rows["SalesOrderID"], exit=LEFT, entry=LEFT,
           points=[(265, so.cy("SalesOrderID")), (265, si.cy("SalesOrderID"))])
    relate(d, "SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID",
           si.rows["SalesInvoiceID"], sil.rows["SalesInvoiceID"], exit=RIGHT, entry=LEFT)
    relate(d, "ShipmentLine", "ShipmentLineID", "SalesInvoiceLine", "ShipmentLineID", shl.id,
           sil.id, exit=BOTTOM, entry=TOP)
    relate(d, "SalesOrderLine", "SalesOrderLineID", "SalesInvoiceLine", "SalesOrderLineID",
           sol.rows["SalesOrderLineID"], sil.rows["SalesOrderLineID"], exit=RIGHT, entry=RIGHT,
           points=[(842, sol.cy("SalesOrderLineID")), (842, sil.cy("SalesOrderLineID"))])
    relate(d, "SalesInvoice", "SalesInvoiceID", "CashReceiptApplication", "SalesInvoiceID", si.id,
           cra.id, exit=BOTTOM, entry=TOP)
    relate(d, "CashReceipt", "CashReceiptID", "CashReceiptApplication", "CashReceiptID",
           cr.rows["CashReceiptID"], cra.rows["CashReceiptID"], exit=RIGHT, entry=LEFT)
    legend(d, C0, 20, W, stacked=True)
    return d


def fig_03_08() -> Diagram:
    d = Diagram("Manufacturing ER Diagram")
    C0, C1, C2, W = 0, 305, 610, 250
    it = table(d, "Item", C0, 40, [("PK", "ItemID"), ("", "ItemCode"), ("", "ItemName")], w=W,
               focus=False, group="Master Data")
    bom = table(d, "BillOfMaterial", C1, 40, [("PK", "BOMID"), ("FK", "ParentItemID"),
                                              ("", "VersionNumber"), ("", "Status")], w=W)
    bml = table(d, "BillOfMaterialLine", C2, 40, [("PK", "BOMLineID"), ("FK", "BOMID"),
                                                  ("FK", "ComponentItemID"),
                                                  ("", "QuantityPerUnit")], w=W)
    wo = table(d, "WorkOrder", C1, 230, [("PK", "WorkOrderID"), ("", "WorkOrderNumber"),
                                         ("FK", "ItemID"), ("FK", "BOMID"), ("", "PlannedQuantity"),
                                         ("", "ReleasedDate"), ("", "Status")], w=W)
    woo = table(d, "WorkOrderOperation", C0, 206, [("PK", "WorkOrderOperationID"),
                                                   ("FK", "WorkOrderID"),
                                                   ("", "OperationSequence"), ("", "Status")], w=W)
    mil = table(d, "MaterialIssueLine", C2, 230, [("PK", "MaterialIssueLineID"),
                                                  ("FK", "MaterialIssueID"), ("FK", "BOMLineID"),
                                                  ("", "QuantityIssued"),
                                                  ("", "ExtendedStandardCost")], w=W)
    mi = table(d, "MaterialIssue", C2, 430, [("PK", "MaterialIssueID"), ("", "IssueNumber"),
                                             ("FK", "WorkOrderID"), ("", "IssueDate")], w=W)
    woc = table(d, "WorkOrderClose", C1, 478, [("PK", "WorkOrderCloseID"), ("FK", "WorkOrderID"),
                                               ("", "CloseDate"), ("", "TotalVarianceAmount")], w=W)
    pc = table(d, "ProductionCompletion", C0, 478, [("PK", "ProductionCompletionID"),
                                                    ("", "CompletionNumber"), ("FK", "WorkOrderID"),
                                                    ("", "CompletionDate")], w=W)
    pcl = table(d, "ProductionCompletionLine", C0, 654, [("PK", "ProductionCompletionLineID"),
                                                         ("FK", "ProductionCompletionID"),
                                                         ("", "QuantityCompleted"),
                                                         ("", "ExtendedStandardTotalCost")], w=W)
    relate(d, "Item", "ItemID", "BillOfMaterial", "ParentItemID", it.rows["ItemID"],
           bom.rows["ParentItemID"], color=AMBER, exit=RIGHT, entry=LEFT)
    relate(d, "Item", "ItemID", "BillOfMaterialLine", "ComponentItemID", it.id, bml.id,
           color=AMBER, exit=(0.9, 0), entry=(0.5, 0),
           points=[(C0 + 0.9 * W, 10), (C2 + W / 2, 10)])
    relate(d, "BillOfMaterial", "BOMID", "BillOfMaterialLine", "BOMID", bom.rows["BOMID"],
           bml.rows["BOMID"], exit=RIGHT, entry=LEFT)
    relate(d, "BillOfMaterial", "BOMID", "WorkOrder", "BOMID", bom.id, wo.id, exit=BOTTOM,
           entry=TOP)
    relate(d, "Item", "ItemID", "WorkOrder", "ItemID", it.id, wo.id, color=AMBER, exit=BOTTOM,
           entry=(0.2, 0), points=[(C0 + W / 2, 180), (C1 + 0.2 * W, 180)])
    relate(d, "WorkOrder", "WorkOrderID", "WorkOrderOperation", "WorkOrderID",
           wo.rows["WorkOrderID"], woo.rows["WorkOrderID"], exit=LEFT, entry=RIGHT)
    relate(d, "BillOfMaterialLine", "BOMLineID", "MaterialIssueLine", "BOMLineID", bml.id, mil.id,
           exit=BOTTOM, entry=TOP)
    relate(d, "MaterialIssue", "MaterialIssueID", "MaterialIssueLine", "MaterialIssueID", mi.id,
           mil.id, exit=TOP, entry=BOTTOM)
    relate(d, "WorkOrder", "WorkOrderID", "MaterialIssue", "WorkOrderID", wo.rows["WorkOrderID"],
           mi.rows["WorkOrderID"], exit=RIGHT, entry=LEFT,
           points=[(582, wo.cy("WorkOrderID")), (582, mi.cy("WorkOrderID"))])
    relate(d, "WorkOrder", "WorkOrderID", "WorkOrderClose", "WorkOrderID", wo.id, woc.id,
           exit=BOTTOM, entry=TOP)
    relate(d, "WorkOrder", "WorkOrderID", "ProductionCompletion", "WorkOrderID", wo.id, pc.id,
           exit=(0.15, 1), entry=TOP, points=[(C1 + 0.15 * W, 452), (C0 + W / 2, 452)])
    relate(d, "ProductionCompletion", "ProductionCompletionID", "ProductionCompletionLine",
           "ProductionCompletionID", pc.id, pcl.id, exit=BOTTOM, entry=TOP)
    legend(d, C1, 654, 860 - C1)
    return d


def fig_03_09() -> Diagram:
    d = Diagram("Accounting Core ER Diagram")
    C0, C1, C2 = 36, 306, 606
    acc = table(d, "Account", C0, 40, [("PK", "AccountID"), ("", "AccountNumber"),
                                       ("", "AccountName"), ("", "AccountType"),
                                       ("", "AccountSubType"), ("FK", "ParentAccountID"),
                                       ("", "NormalBalance")], w=220)
    gl = table(d, "GLEntry", C1, 40, [("PK", "GLEntryID"), ("", "PostingDate"), ("FK", "AccountID"),
                                      ("", "Debit"), ("", "Credit"), ("", "SourceDocumentType"),
                                      ("", "SourceDocumentID"), ("", "SourceLineID"),
                                      ("FK", "CostCenterID"), ("", "FiscalYear"),
                                      ("", "FiscalPeriod")], w=250)
    je = table(d, "JournalEntry", C2, 64, [("PK", "JournalEntryID"), ("", "EntryNumber"),
                                           ("", "PostingDate"), ("", "EntryType"),
                                           ("", "TotalAmount"), ("FK", "CreatedByEmployeeID"),
                                           ("FK", "ApprovedByEmployeeID"),
                                           ("FK", "ReversesJournalEntryID")], w=226)
    cc = table(d, "CostCenter", C0, 280, [("PK", "CostCenterID"), ("", "CostCenterName")], w=220,
               focus=False, group="Organizational Planning")
    emp = table(d, "Employee", C2, 356, [("PK", "EmployeeID"), ("", "EmployeeName")], w=226,
                focus=False, group="Master Data")
    relate(d, "Account", "AccountID", "GLEntry", "AccountID", acc.rows["AccountID"],
           gl.rows["AccountID"], exit=RIGHT, entry=LEFT)
    relate(d, "Account", "AccountID", "Account", "ParentAccountID", acc.rows["AccountID"],
           acc.rows["ParentAccountID"], exit=LEFT, entry=LEFT,
           points=[(16, acc.cy("AccountID")), (16, acc.cy("ParentAccountID"))])
    relate(d, "CostCenter", "CostCenterID", "GLEntry", "CostCenterID", cc.rows["CostCenterID"],
           gl.rows["CostCenterID"], color=AMBER, exit=RIGHT, entry=LEFT)
    d.text("<i>Journal entries reach GLEntry through SourceDocumentType = 'JournalEntry' and "
           "SourceDocumentID.</i>", C2, 0, 254, 44, size=SMALL, color=AMBER)
    trace(d, "JournalEntry", "JournalEntryID", je.rows["JournalEntryID"], gl.id, exit=LEFT,
          entry=(1, round((je.cy("JournalEntryID") - gl.y) / gl.h, 4)))
    relate(d, "JournalEntry", "JournalEntryID", "JournalEntry", "ReversesJournalEntryID",
           je.rows["JournalEntryID"], je.rows["ReversesJournalEntryID"], exit=RIGHT, entry=RIGHT,
           points=[(848, je.cy("JournalEntryID")), (848, je.cy("ReversesJournalEntryID"))])
    for fx, col, label in [(0.5, "CreatedByEmployeeID", "created by"),
                           (0.82, "ApprovedByEmployeeID", "approved by")]:
        relate(d, "Employee", "EmployeeID", "JournalEntry", col, emp.id, je.id, color=AMBER,
               exit=(fx, 0), entry=(fx, 1), label=label)
    # Keep both lines clear of the "Master Data" caption at the left of the Employee header.
    sources = [("SalesInvoice", "SalesInvoiceID", "Order-to-Cash"),
               ("Shipment", "ShipmentID", "Order-to-Cash"),
               ("PurchaseInvoice", "PurchaseInvoiceID", "Procure-to-Pay"),
               ("MaterialIssue", "MaterialIssueID", "Manufacturing"),
               ("PayrollPayment", "PayrollPaymentID", "Payroll and Time")]
    lanes = [460, 484, None, 484, 460]
    for i, (name, pk, group) in enumerate(sources):
        x = i * 174
        t = table(d, name, x, 524, [("PK", pk)], w=164, focus=False, group=group,
                  caption_below=True)
        cx = x + 82
        if lanes[i] is None:
            trace(d, name, pk, t.id, gl.id, exit=TOP, entry=(round((cx - C1) / 250, 4), 1))
            continue
        gx = C1 + 250 * (0.1 + 0.2 * i)
        trace(d, name, pk, t.id, gl.id, exit=TOP, entry=(0.1 + 0.2 * i, 1),
              points=[(cx, lanes[i]), (gx, lanes[i])])
    legend(d, 0, 612, 860, trace_item=True)
    return d


def fig_03_10() -> Diagram:
    sid = 7947
    inv = one("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate, SalesOrderID, CustomerID, "
              "GrandTotal FROM SalesInvoice WHERE SalesInvoiceID = ?", sid)
    sil = one("SELECT SalesInvoiceLineID, SalesOrderLineID, ShipmentLineID, ItemID, Quantity, "
              "UnitPrice, LineTotal FROM SalesInvoiceLine WHERE SalesInvoiceID = ?", sid)
    shl = one("SELECT ShipmentLineID, ShipmentID, QuantityShipped FROM ShipmentLine "
              "WHERE ShipmentLineID = ?", sil[2])
    shp = one("SELECT ShipmentNumber, ShipmentDate FROM Shipment WHERE ShipmentID = ?", shl[1])
    sol = one("SELECT SalesOrderLineID, SalesOrderID FROM SalesOrderLine "
              "WHERE SalesOrderLineID = ?", sil[1])
    so = one("SELECT OrderNumber, OrderDate FROM SalesOrder WHERE SalesOrderID = ?", sol[1])
    cus = one("SELECT CustomerID, CustomerName FROM Customer WHERE CustomerID = ?", inv[4])
    itm = one("SELECT ItemCode, ItemName, StandardCost FROM Item WHERE ItemID = ?", sil[3])
    glr = q("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit, g.SourceLineID, "
            "a.AccountType, g.AccountID FROM GLEntry g JOIN Account a USING (AccountID) "
            "WHERE SourceDocumentType = 'SalesInvoice' AND SourceDocumentID = ? ORDER BY GLEntryID",
            sid)
    gls = q("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit FROM GLEntry g "
            "JOIN Account a USING (AccountID) WHERE SourceDocumentType = 'Shipment' "
            "AND SourceDocumentID = ? AND SourceLineID = ? ORDER BY GLEntryID", shl[1], shl[0])
    app = one("SELECT CashReceiptApplicationID, CashReceiptID, AppliedAmount, ApplicationDate "
              "FROM CashReceiptApplication WHERE SalesInvoiceID = ?", sid)
    rct = one("SELECT ReceiptNumber, Amount FROM CashReceipt WHERE CashReceiptID = ?", app[1])
    assert sum(r[2] for r in glr) == sum(r[3] for r in glr) == inv[5]

    def dc(r) -> str:
        return (f"Dr {r[0]} {esc(r[1])} {money(r[2])}" if r[2]
                else f"Cr {r[0]} {esc(r[1])} {money(r[3])}")

    d = Diagram("Cross-Group Traced Path")
    LX, LW, RX, RW = 0, 310, 440, 420

    def card(step: str, title: str, lines: list[str], x: float, y: float, w: float,
             focus: bool = True, group: str = "") -> str:
        fill = BLUE if focus else GRAY
        tag = f'&nbsp;&nbsp;<font style="font-size:{SMALL}px">{group}</font>' if group else ""
        d.box(f"<b>{step}&nbsp;&nbsp;{esc(title)}</b>{tag}", x, y, w, 30, fill=fill, stroke=fill,
              color=WHITE, size=HEAD, rounded=False, align="left")
        h = 30 + 18 * len(lines) + 12
        d.box("<br>".join(lines), x, y + 30, w, h - 30, stroke=RULE, rounded=False, align="left")
        return d.container(x, y, w, h)

    o2c, core = "Order-to-Cash", "Accounting Core"
    c1 = card("1", "SalesOrder", [f"{so[0]}, ordered {so[1]}",
                                  f"Customer {cus[0]}: {esc(cus[1])}"], LX, 0, LW, group=o2c)
    c2 = card("2", "SalesOrderLine", [f"SalesOrderLineID {sol[0]}", f"Item {esc(itm[0])}",
                                      esc(itm[1])], LX, 128, LW, group=o2c)
    c3 = card("3", "ShipmentLine", [f"ShipmentLineID {shl[0]} on {shp[0]}",
                                    f"Shipped {shp[1]}: {shl[2]:g} units"], LX, 274, LW, group=o2c)
    c4 = card("4", "SalesInvoiceLine", [f"SalesInvoiceLineID {sil[0]}",
                                        f"Invoice {inv[1]}, dated {inv[2]}",
                                        f"{sil[4]:g} × {money(sil[5])} = {money(sil[6])}"],
              LX, 402, LW, group=o2c)
    cb = card("B", "Cash settlement", [f"CashReceiptApplication {app[0]}",
                                       f"applies {money(app[2])} of receipt {rct[0]}",
                                       f"({money(rct[1])}) on {app[3]}"],
              LX, 548, LW, focus=False, group=o2c)
    ca = card("A", "Shipment postings", [
        "SourceDocumentType = 'Shipment'", f"SourceLineID = {shl[0]}",
        *[dc(r) for r in gls], f"{shl[2]:g} units × standard cost {money(itm[2])}"],
        RX, 240, RW, focus=False, group=core)
    c5 = card("5", "GLEntry", [
        "SourceDocumentType = 'SalesInvoice'", f"SourceDocumentID = {sid}",
        *[dc(r) + (f" (line {r[4]})" if r[4] else "") for r in glr]], RX, 402, RW, group=core)
    rev = next(r for r in glr if r[4])
    c6 = card("6", "Account", [f"AccountID {rev[6]}: {rev[0]} {esc(rev[1])}",
                               f"AccountType {rev[5]}"], RX, 604, RW, group=core)
    for a, b, label in [(c1, c2, f"SalesOrderID = {sol[1]}"),
                        (c2, c3, f"SalesOrderLineID = {sol[0]}"),
                        (c3, c4, f"ShipmentLineID = {shl[0]}"),
                        (c4, cb, f"SalesInvoiceID = {sid}")]:
        d.arrow(a, b, label=label, exit=BOTTOM, entry=TOP)
    # The trace labels sit above their arrows so the dashed lines stay visible.
    for src, tgt, entry, y, key in [(c3, ca, LEFT, 313, shl[1]), (c4, c5, (0, 0.3), 450, sid)]:
        d.arrow(src, tgt, color=AMBER, dashed=True, exit=RIGHT, entry=entry)
        d.text(f"SourceDocumentID = {key}", LX + LW + 6, y - 42, RX - LX - LW - 12, 36,
               size=SMALL, color=GRAY, align="center", valign="bottom")
    d.arrow(c5, c6, label=f"AccountID = {rev[6]}", exit=BOTTOM, entry=TOP)
    d.text(f"<b>Tracing one sale.</b> Steps 1 to 4 follow invoice {inv[1]} back through the "
           "Order-to-Cash tables. Step 5 uses the source-document trace to find its ledger "
           "postings, and step 6 classifies the revenue posting. A and B show the other postings "
           "the same sale creates.", RX, 0, RW, 110)
    return d


FIGURES = {
    "fig-03-01-anatomy-database-table": fig_03_01,
    "fig-03-02-pk-fk-illustrated": fig_03_02,
    "fig-03-03-three-cardinality-types": fig_03_03,
    "fig-03-04-crows-foot-notation": fig_03_04,
    "fig-03-05-chart-of-accounts-table": fig_03_05,
    "fig-03-06-gl-subledger-relationship": fig_03_06,
    "fig-03-07-o2c-core-er": fig_03_07,
    "fig-03-08-manufacturing-er-focused": fig_03_08,
    "fig-03-09-accounting-core-er": fig_03_09,
    "fig-03-10-cross-group-traced-path": fig_03_10,
}
