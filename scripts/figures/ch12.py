"""Chapter 12 figures."""

from __future__ import annotations

import dbbrowser as db
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, GRAY, GRAY_TINT, ROW_H, SMALL, Diagram,
                    esc)

TRACE_SQL = """SELECT 'Posting with no payroll payment' AS Test,
    gl.GLEntryID AS RecordID, gl.PostingDate AS RecordDate,
    gl.Debit + gl.Credit AS Amount
FROM GLEntry AS gl
    LEFT JOIN PayrollPayment AS pp
        ON pp.PayrollPaymentID = gl.SourceDocumentID
WHERE gl.SourceDocumentType = 'PayrollPayment'
    AND pp.PayrollPaymentID IS NULL
UNION ALL
SELECT 'Posting with no supplier payment', gl.GLEntryID,
    gl.PostingDate, gl.Debit + gl.Credit
FROM GLEntry AS gl
    LEFT JOIN DisbursementPayment AS dp
        ON dp.DisbursementID = gl.SourceDocumentID
WHERE gl.SourceDocumentType = 'DisbursementPayment'
    AND dp.DisbursementID IS NULL
UNION ALL
SELECT 'Sales invoice never posted', si.SalesInvoiceID,
    si.InvoiceDate, si.GrandTotal
FROM SalesInvoice AS si
    LEFT JOIN GLEntry AS gl ON gl.SourceDocumentType = 'SalesInvoice'
        AND gl.SourceDocumentID = si.SalesInvoiceID
WHERE gl.GLEntryID IS NULL
UNION ALL
SELECT 'Supplier invoice never posted', pi.PurchaseInvoiceID,
    pi.InvoiceDate, pi.GrandTotal
FROM PurchaseInvoice AS pi
    LEFT JOIN GLEntry AS gl ON gl.SourceDocumentType = 'PurchaseInvoice'
        AND gl.SourceDocumentID = pi.PurchaseInvoiceID
WHERE gl.GLEntryID IS NULL;"""

MATCH_CTES = """WITH Received AS (
    SELECT POLineID, SUM(QuantityReceived) AS QtyReceived
    FROM GoodsReceiptLine
    GROUP BY POLineID
),
Invoiced AS (
    SELECT POLineID, SUM(Quantity) AS QtyInvoiced
    FROM PurchaseInvoiceLine
    WHERE POLineID IS NOT NULL
    GROUP BY POLineID
),
Matched AS (
    SELECT pol.POLineID, pol.Quantity AS QtyOrdered,
        COALESCE(r.QtyReceived, 0) AS QtyReceived,
        COALESCE(i.QtyInvoiced, 0) AS QtyInvoiced
    FROM PurchaseOrderLine AS pol
        LEFT JOIN Received AS r ON r.POLineID = pol.POLineID
        LEFT JOIN Invoiced AS i ON i.POLineID = pol.POLineID
)
"""

MATCH_SELECT = """SELECT
    CASE
        WHEN QtyInvoiced > QtyReceived + 0.0001
            THEN 'Exception: invoiced above received'
        WHEN QtyReceived > QtyOrdered + 0.0001
            THEN 'Exception: received above ordered'
        WHEN QtyReceived = 0 THEN 'Not yet received'
        WHEN QtyInvoiced < QtyReceived - 0.0001
            THEN 'Received, not fully invoiced'
        WHEN QtyReceived < QtyOrdered - 0.0001 THEN 'Partly received'
        ELSE 'Matched'
    END AS MatchStatus,
    COUNT(*) AS POLines
FROM Matched
GROUP BY MatchStatus
ORDER BY POLines DESC;"""

APPROVAL_SQL = """WITH ApprovalExceptions AS (
    SELECT 'Self-approved' AS Test, po.PONumber, po.OrderTotal
    FROM PurchaseOrder AS po
    WHERE po.CreatedByEmployeeID = po.ApprovedByEmployeeID
    UNION ALL
    SELECT 'Above approver limit', po.PONumber, po.OrderTotal
    FROM PurchaseOrder AS po
        INNER JOIN Employee AS e ON e.EmployeeID = po.ApprovedByEmployeeID
    WHERE po.OrderTotal > e.MaxApprovalAmount
    UNION ALL
    SELECT 'Approved after termination', po.PONumber, po.OrderTotal
    FROM PurchaseOrder AS po
        INNER JOIN Employee AS e ON e.EmployeeID = po.ApprovedByEmployeeID
    WHERE e.TerminationDate IS NOT NULL
        AND po.OrderDate > e.TerminationDate
)
SELECT Test, COUNT(*) AS Orders, ROUND(SUM(OrderTotal), 2) AS OrderValue
FROM ApprovalExceptions
GROUP BY Test
ORDER BY Orders DESC;"""

LATE_LABOR_SQL = """SELECT strftime('%Y', lt.WorkDate) AS WorkYear,
    ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 0) AS DirectHours,
    ROUND(SUM(CASE WHEN lt.WorkDate > op.ActualEndDate
        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0)
        AS HoursAfterOperationEnded,
    ROUND(SUM(CASE WHEN lt.WorkDate > op.ActualEndDate
        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END)
        / SUM(lt.RegularHours + lt.OvertimeHours), 3) AS ShareAfterEnd
FROM LaborTimeEntry AS lt
    INNER JOIN WorkOrderOperation AS op
        ON op.WorkOrderOperationID = lt.WorkOrderOperationID
WHERE lt.LaborType = 'Direct Manufacturing'
GROUP BY WorkYear
ORDER BY WorkYear;"""

JE_RECON_SQL = """SELECT
    (SELECT COUNT(*) FROM JournalEntry) AS Entries,
    (SELECT ROUND(SUM(TotalAmount), 2) FROM JournalEntry) AS EntryTotal,
    (SELECT COUNT(DISTINCT SourceDocumentID) FROM GLEntry
        WHERE SourceDocumentType = 'JournalEntry') AS PostedEntries,
    (SELECT ROUND(SUM(Debit), 2) FROM GLEntry
        WHERE SourceDocumentType = 'JournalEntry') AS PostedDebits;"""


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


def trace_rows() -> list[tuple]:
    rows = q(TRACE_SQL)
    assert len(rows) == 6 and {r[0] for r in rows} == {"Posting with no payroll payment"}, rows
    assert sorted({r[2][:7] for r in rows}) == ["2024-01", "2025-01", "2026-01"], rows
    return rows


def fig_12_01() -> Diagram:
    d = Diagram("Tracing in Both Directions Between the Ledger and Its Documents")
    types = {r[0] for r in q("SELECT DISTINCT SourceDocumentType FROM GLEntry")}
    documents = [("SalesInvoice", "SalesInvoiceID", "InvoiceDate"),
                 ("PurchaseInvoice", "PurchaseInvoiceID", "InvoiceDate"),
                 ("DisbursementPayment", "DisbursementID", "PaymentDate"),
                 ("PayrollPayment", "PayrollPaymentID", "PaymentDate")]
    for table, key, date in documents:
        assert table in types
        columns = {r[1] for r in q(f"PRAGMA table_info({table})")}
        assert {key, date} <= columns, (table, key, date)
    gl_columns = [("PK", "GLEntryID"), ("", "PostingDate"), ("FK", "AccountID"), ("", "Debit"),
                  ("", "Credit"), ("", "SourceDocumentType"), ("FK", "SourceDocumentID")]
    assert {c for _, c in gl_columns} <= {r[1] for r in q("PRAGMA table_info(GLEntry)")}
    d.text("<b>The general ledger</b>", 0, 0, 250, 20, size=SMALL)
    gl = d.table("GLEntry", 0, 24, gl_columns, w=250)
    d.text("<b>Source document tables (four of many)</b>", 590, 0, 270, 20, size=SMALL)
    doc_y = 24
    doc_tables = []
    for table, key, date in documents:
        t = d.table(table, 610, doc_y, [("PK", key), ("", date)], w=250)
        doc_tables.append(t)
        doc_y += t.h + 18
    docs = d.container(610, 24, 250, doc_y - 18 - 24)
    docs_h = doc_y - 18 - 24
    ex_y, co_y, box_h = 30, 150, 96
    exist = d.box("<b>Existence: ledger to documents</b><br>LEFT JOIN from GLEntry to the document "
                  "table on SourceDocumentID; the postings whose document key IS NULL point to "
                  "nothing", 290, ex_y, 280, box_h, fill=AMBER_TINT, stroke=AMBER, align="left",
                  size=SMALL)
    complete = d.box("<b>Completeness: documents to ledger</b><br>LEFT JOIN from the document "
                     "table to GLEntry; the documents with no GLEntryID were never posted",
                     290, co_y, 280, box_h, fill=AMBER_TINT, stroke=AMBER, align="left", size=SMALL)
    ex_mid, co_mid = ex_y + box_h / 2, co_y + box_h / 2
    assert co_mid < 24 + gl.h and co_mid < 24 + docs_h
    d.arrow(gl.id, exist, color=AMBER, dashed=True, exit=(1, round((ex_mid - 24) / gl.h, 4)),
            entry=(0, 0.5))
    d.arrow(exist, docs, color=AMBER, dashed=True, exit=(1, 0.5),
            entry=(0, round((ex_mid - 24) / docs_h, 4)))
    d.arrow(docs, complete, color=AMBER, dashed=True, exit=(0, round((co_mid - 24) / docs_h, 4)),
            entry=(1, 0.5))
    d.arrow(complete, gl.id, color=AMBER, dashed=True, exit=(0, 0.5),
            entry=(1, round((co_mid - 24) / gl.h, 4)))
    cut_y = doc_y - 18 + 30
    d.box("<b>Cutoff: the dates of both sides</b><br>Compare each document's own date (InvoiceDate, "
          "PaymentDate) with the PostingDate of its ledger rows. A posting in a different fiscal "
          "year from the document records the event in the wrong period.", 0, cut_y, 860, 70,
          fill=GRAY_TINT, stroke=GRAY, align="left", size=SMALL)
    ly = cut_y + 90
    d.line_sample(0, ly + 10, 50, color=AMBER, dashed=True, end="blockThin")
    d.text("the direction of a trace between the ledger and its documents, which link on "
           "SourceDocumentType and SourceDocumentID", 60, ly, 800, 22, size=SMALL)
    return d


def fig_12_02() -> Diagram:
    d = Diagram("The Trace Exceptions in One List")
    shown = ("SELECT 'Posting with no payroll payment' AS Test,\n"
             "    gl.GLEntryID AS RecordID, gl.PostingDate AS RecordDate,\n"
             "    gl.Debit + gl.Credit AS Amount\n"
             "FROM GLEntry AS gl\n"
             "    LEFT JOIN PayrollPayment AS pp\n"
             "        ON pp.PayrollPaymentID = gl.SourceDocumentID\n"
             "WHERE gl.SourceDocumentType = 'PayrollPayment'\n"
             "    AND pp.PayrollPaymentID IS NULL\n"
             "UNION ALL\n"
             "SELECT 'Posting with no supplier payment', ...\n"
             "UNION ALL\n"
             "SELECT 'Sales invoice never posted', ...\n"
             "UNION ALL\n"
             "SELECT 'Supplier invoice never posted', ...;")
    rows = trace_rows()
    headers = ["Test", "RecordID", "RecordDate", "Amount"]
    y = db.window(d)
    y = db.editor(d, 0, y, 860, shown, tab="Audit.sql") + 8
    geometry = db.results(d, 0, y, headers, [320, 130, 150, 150], rows)
    y += (len(rows) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), shown.split("\n")[0])
    db.emphasize_cells(d, geometry, [(-1, 0), (len(rows) - 1, 0)])
    note(d, "The last three tests are shortened here; Tutorial 12.1 gives the full query. Outlined: "
            "every row comes from the first test, and the other three return none.", bottom + 8, 40)
    return d


def fig_12_03() -> Diagram:
    d = Diagram("The Three-Way Match at the Level of the Purchase Order Line")
    line = 12834
    po, number, item, name, ordered, cost = one(
        "SELECT po.PONumber, pol.LineNumber, i.ItemCode, i.ItemName, pol.Quantity, pol.UnitCost "
        "FROM PurchaseOrderLine pol JOIN PurchaseOrder po ON po.PurchaseOrderID = pol.PurchaseOrderID "
        "JOIN Item i ON i.ItemID = pol.ItemID WHERE pol.POLineID = ?", line)
    receipts = q("SELECT grl.GoodsReceiptLineID, gr.ReceiptDate, grl.QuantityReceived "
                 "FROM GoodsReceiptLine grl JOIN GoodsReceipt gr ON gr.GoodsReceiptID = grl.GoodsReceiptID "
                 "WHERE grl.POLineID = ? ORDER BY grl.GoodsReceiptLineID", line)
    invoices = q("SELECT pil.PILineID, pil.GoodsReceiptLineID, pil.Quantity, pil.UnitCost "
                 "FROM PurchaseInvoiceLine pil WHERE pil.POLineID = ? ORDER BY pil.PILineID", line)
    received = sum(r[2] for r in receipts)
    invoiced = sum(r[2] for r in invoices)
    diffs = [(c - cost) / cost for *_, c in invoices]
    assert len(receipts) == 2 and len(invoices) == 3
    assert abs(received - ordered) < 1e-4 and abs(invoiced - received) < 1e-4
    assert 0.02 < max(diffs) < 0.03 and min(diffs) < 0, diffs
    split = [r for r in receipts if sum(1 for i in invoices if i[1] == r[0]) == 2]
    assert len(split) == 1
    d.box(f"<b>PurchaseOrderLine {line}</b><br>{esc(po)}, line {number}: {esc(item)} {esc(name)}<br>"
          f"Quantity {ordered:,.2f} at UnitCost {cost:,.2f}", 200, 0, 460, 70, fill=BLUE_TINT,
          stroke=BLUE, size=SMALL)
    gy = 110
    d.text(f"<b>Goods receipt lines with POLineID {line}</b>", 0, gy - 22, 390, 20, size=SMALL)
    left = d.grid(0, gy, ["GoodsReceiptLineID", "ReceiptDate", "QuantityReceived"], [150, 104, 136],
                  [(str(i), dt, f"{qty:,.2f}") for i, dt, qty in receipts])
    d.text(f"<b>Supplier invoice lines with POLineID {line}</b>", 420, gy - 22, 440, 20, size=SMALL)
    right = d.grid(420, gy, ["PILineID", "Receipt line", "Quantity", "UnitCost", "vs order"],
                   [80, 110, 84, 80, 86],
                   [(str(i), str(g), f"{qty:,.2f}", f"{c:,.2f}", f"{(c - cost) / cost:+.2%}")
                    for i, g, qty, c in invoices])
    sy = gy + ROW_H * 4 + 14
    rsum = d.box(f"SUM(QuantityReceived) = <b>{received:,.2f}</b>", 0, sy, 390, 34, fill=GRAY_TINT,
                 stroke=GRAY, size=SMALL)
    isum = d.box(f"SUM(Quantity) = <b>{invoiced:,.2f}</b>", 420, sy, 440, 34, fill=GRAY_TINT,
                 stroke=GRAY, size=SMALL)
    d.arrow(left[(len(receipts), 1)], rsum, exit=(0.5, 1), entry=(0.37, 0))
    d.arrow(right[(len(invoices), 2)], isum, exit=(0.5, 1), entry=(0.53, 0))
    cy = sy + 70
    result = d.box(f"<b>Matched</b>: ordered {ordered:,.2f} = received {received:,.2f} = invoiced "
                   f"{invoiced:,.2f}. Every invoice price is within 3% of the order's {cost:,.2f}, the largest "
                   f"{max(diffs):+.2%}.", 150, cy, 560, 56, fill=BLUE_TINT, stroke=BLUE, size=SMALL)
    d.arrow(rsum, result, exit=(0.5, 1), entry=(0.1, 0))
    d.arrow(isum, result, exit=(0.5, 1), entry=(0.9, 0))
    oy = cy + 90
    d.text("<b>The status of a purchase order line after the comparison</b>", 0, oy, 860, 20, size=SMALL)
    outcomes = [("Matched", "ordered = received = invoiced", "complete"),
                ("Not yet received", "nothing received", "an open order"),
                ("Partly received", "received below ordered", "an open order"),
                ("Received, not fully invoiced", "invoiced below received",
                 "an accrual: goods received not invoiced"),
                ("Exception: invoiced above received", "invoiced above received", "investigate"),
                ("Exception: received above ordered", "received above ordered", "investigate")]
    d.grid(0, oy + 22, ["Status", "Condition", "Meaning"], [290, 250, 320], outcomes,
           highlight={(5, 0), (6, 0)})
    split_id = split[0][0]
    split_qty = split[0][2]
    parts = [i[2] for i in invoices if i[1] == split_id]
    note(d, f"Compared row by row, receipt line {split_id} ({split_qty:,.2f}) matches neither of its invoice "
            f"lines ({parts[0]:,.2f} and {parts[1]:,.2f}); summed to the purchase order line, the three "
            "quantities agree. At a 2% tolerance, the first invoice line would be an exception.",
         oy + 22 + ROW_H * 7 + 12, 40)
    return d


def fig_12_04() -> Diagram:
    d = Diagram("The Three-Way Match of Every Purchase Order Line")
    headers, rows = db.run(MATCH_CTES + MATCH_SELECT)
    status = dict(rows)
    assert not any(s.startswith("Exception") for s in status), status
    assert set(status) == {"Matched", "Received, not fully invoiced", "Not yet received",
                           "Partly received"}, status
    assert status["Matched"] > 0.9 * sum(status.values())
    shown = ("WITH Received AS (...),   -- quantity received per POLineID\n"
             "Invoiced AS (...),        -- quantity invoiced per POLineID\n"
             "Matched AS (...)          -- ordered, received, invoiced per line\n"
             + MATCH_SELECT)
    y = db.window(d)
    y = db.editor(d, 0, y, 860, shown, tab="Audit.sql") + 8
    geometry = db.results(d, 0, y, headers, [360, 140], rows)
    y += (len(rows) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), shown.split("\n")[0])
    db.emphasize_cells(d, geometry, [(-1, 0), (len(rows) - 1, 1)])
    note(d, "The three CTEs are shortened here; Tutorial 12.2 gives them in full. Outlined: four statuses, "
            "and neither exception status appears.", bottom + 8, 40)
    return d


def fig_12_05() -> Diagram:
    d = Diagram("Approval Exceptions in the Purchase Orders")
    headers, rows = db.run(APPROVAL_SQL)
    counts = {r[0]: r[1] for r in rows}
    assert counts == {"Above approver limit": 13, "Self-approved": 9, "Approved after termination": 3}, counts
    out = db.execute_sql(d, APPROVAL_SQL, [300, 120, 160])
    db.emphasize_cells(d, out["geometry"], [(-1, 0), (len(rows) - 1, 2)])
    note(d, "Outlined: the three tests, with the number of purchase orders each flags and their value. "
            "Some orders fail more than one test.", out["bottom"] + 8, 40)
    return d


def fig_12_06() -> Diagram:
    d = Diagram("The Chain of Records Behind the Labor Cost")
    records = [("TimeClockEntry", "the hours clocked each day, regular and overtime", None),
               ("LaborTimeEntry", "the hours charged to a work order operation, or indirect time",
                "TimeClockEntryID"),
               ("PayrollRegister", "each employee's pay for a pay period", "EmployeeID, PayrollPeriodID"),
               ("PayrollPayment", "the net pay disbursed", "PayrollRegisterID"),
               ("GLEntry", "the cost and the payment posted to the ledger", "SourceDocumentID")]
    for table, _, key in records:
        columns = {r[1] for r in q(f"PRAGMA table_info({table})")}
        assert columns, table
        if key:
            assert {k.strip() for k in key.split(",")} <= columns, (table, key)
    tests = [("Overtime above half an hour has an OvertimeApproval", "Tutorial 12.3, Steps 1 and 2"),
             ("Direct time recorded on or before its operation's ActualEndDate", "Tutorial 12.3, Step 3"),
             ("The employee was employed on the pay date (TerminationDate)", "Tutorial 12.3, Step 4"),
             ("One payment for each approved register, made after its ApprovedDate",
              "Tutorials 12.1 and 12.3"),
             ("Every PayrollPayment posting traces to an existing payment", "Tutorial 12.1, Step 3")]
    w, gap = 148, 30
    boxes = []
    for i, (table, what, key) in enumerate(records):
        x = i * (w + gap)
        via = f"<br><i>linked by {esc(key)}</i>" if key else ""
        boxes.append(d.box(f"<b>{table}</b><br>{esc(what)}{via}", x, 24, w, 130, fill=BLUE_TINT,
                           stroke=BLUE, size=SMALL))
        test, where = tests[i]
        d.box(f"<b>Test</b><br>{esc(test)}<br><i>{esc(where)}</i>", x, 190, w, 110, fill=GRAY_TINT,
              stroke=GRAY, size=SMALL, align="left", valign="top")
    d.text("<b>The records</b>", 0, 0, 300, 20, size=SMALL)
    d.text("<b>The test of each record</b>", 0, 166, 300, 20, size=SMALL)
    for i in range(len(boxes) - 1):
        posting = i == len(boxes) - 2
        d.arrow(boxes[i], boxes[i + 1], color=AMBER if posting else GRAY, dashed=posting,
                exit=(1, 0.5), entry=(0, 0.5))
    ly = 320
    d.line_sample(0, ly + 10, 50, color=GRAY, end="blockThin")
    d.text("one record leads to the next, linked by the key named in the box", 60, ly, 380, 22, size=SMALL)
    d.line_sample(460, ly + 10, 50, color=AMBER, dashed=True, end="blockThin")
    d.text("a posting to the ledger", 520, ly, 340, 22, size=SMALL)
    return d


def fig_12_07() -> Diagram:
    d = Diagram("Direct Labor Recorded After Its Operation Ended")
    headers, rows = db.run(LATE_LABOR_SQL)
    shares = [r[3] for r in rows]
    assert [r[0] for r in rows] == ["2024", "2025", "2026"], rows
    assert 0.17 < shares[0] < 0.23 and 0.45 < shares[1] < 0.55 and 0.6 < shares[2] < 0.7, shares
    out = db.execute_sql(d, LATE_LABOR_SQL, [120, 140, 260, 160])
    db.emphasize_cells(d, out["geometry"], [(-1, 3), (len(rows) - 1, 3)])
    note(d, "Outlined: the share of direct hours recorded after the operation's actual end date, which grew "
            "in each year.", out["bottom"] + 8, 40)
    return d


def fig_12_08() -> Diagram:
    d = Diagram("The Start of an Audit Query Library")
    entries, total, posted, debits = one(JE_RECON_SQL.rstrip(";"))
    assert entries == posted and abs(total - debits) < 0.005
    postings = len(trace_rows())
    script = (
        "/* Audit.sql: internal audit query library\n"
        "   Engagement: records behind the manufacturing variance, fiscal 2026\n"
        "   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)\n"
        "   Prepared by: your name, date; reviewed by: name, date */\n"
        "\n"
        "-- Test 1.1: journal entry population\n"
        "-- Objective: JournalEntry holds every entry the ledger posted\n"
        "-- Population: all journal entries; reconciled to GLEntry debits\n"
        "-- Expected: counts and totals agree to the cent\n"
        + JE_RECON_SQL + "\n"
        "\n"
        "-- Test 1.2: postings with no document, documents with no posting\n"
        "-- Objective: existence and completeness of the ledger's postings\n"
        "-- Population: GLEntry by SourceDocumentType; each document table\n"
        f"-- Expected: no rows. Found {postings} PayrollPayment postings (finding 1)\n"
        + "\n".join(TRACE_SQL.split("\n")[:10]))
    y = db.window(d)
    bottom = db.editor(d, 0, y, 860, script, tab="Audit.sql")
    note(d, "The header records the engagement, the data, and who prepared and reviewed the script. Each test "
            "states its objective, population, and expected result. The script continues below the lines shown.",
         bottom + 8, 40)
    return d


FIGURES = {
    "fig-12-01-two-way-trace": fig_12_01,
    "fig-12-02-trace-exceptions": fig_12_02,
    "fig-12-03-three-way-match": fig_12_03,
    "fig-12-04-three-way-match-status": fig_12_04,
    "fig-12-05-approval-exceptions": fig_12_05,
    "fig-12-06-labor-record-chain": fig_12_06,
    "fig-12-07-labor-after-operation-end": fig_12_07,
    "fig-12-08-audit-library": fig_12_08,
}
