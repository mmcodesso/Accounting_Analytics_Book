"""Chapter 12 figures."""

from __future__ import annotations

import dbbrowser as db
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, GRAY, GRAY_TINT, ROW_H, SMALL, Diagram,
                    esc)
from shared.calculations.sql_ch12 import (
    HEADER, _APPROVAL_CTE, _PLANT_DAYS, _EARNINGS, _AFTER_END, QUERIES
)

# Audit.sql as the three tutorials build it (see dbbrowser.Script): a header, then each test under a
# two-line comment that names it and states its population and expected result. The tutorial text
# must match these queries exactly.

CHAPTER12 = db.Script(HEADER, QUERIES, "Audit.sql")


def sql(key: str) -> str:
    return CHAPTER12.location(key)[1]


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


def comment_lines(key: str) -> int:
    return CHAPTER12.location(key)[0].count("\n") + 1


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
    for table, column in [("Shipment", "DeliveryDate"), ("PayrollPeriod", "PeriodEndDate")]:
        assert column in {r[1] for r in q(f"PRAGMA table_info({table})")}, (table, column)
    gl_columns = [("PK", "GLEntryID"), ("", "PostingDate"), ("FK", "AccountID"), ("", "Debit"),
                  ("", "Credit"), ("", "SourceDocumentType"), ("FK", "SourceDocumentID")]
    assert {c for _, c in gl_columns} <= {r[1] for r in q("PRAGMA table_info(GLEntry)")}
    d.text("<b>The general ledger</b>", 0, 0, 250, 20, size=SMALL)
    gl = d.table("GLEntry", 0, 24, gl_columns, w=250)
    d.text("<b>Source document tables (four of many)</b>", 590, 0, 270, 20, size=SMALL)
    doc_y = 24
    for table, key, date in documents:
        t = d.table(table, 610, doc_y, [("PK", key), ("", date)], w=250)
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
    d.box("<b>Cutoff: when the event happened against when it was posted</b><br>Compare the PostingDate "
          "of the ledger rows with the date of the event: the DeliveryDate of the goods a sales invoice "
          "bills, and the work dates of the pay period a payroll pays. A posting in a different fiscal "
          "year from the event records it in the wrong period.", 0, cut_y, 860, 86,
          fill=GRAY_TINT, stroke=GRAY, align="left", size=SMALL)
    ly = cut_y + 106
    d.line_sample(0, ly + 10, 50, color=AMBER, dashed=True, end="blockThin")
    d.text("the direction of a trace between the ledger and its documents, which link on "
           "SourceDocumentType and SourceDocumentID", 60, ly, 800, 22, size=SMALL)
    return d


def fig_12_02() -> Diagram:
    d = Diagram("The Trace Exceptions in One List")
    rows = db.run(sql("trace"))[1]
    assert len(rows) == 6 and {r[0] for r in rows} == {"Posting with no payroll payment"}, rows
    assert sorted({r[2][:7] for r in rows}) == ["2024-01", "2025-01", "2026-01"], rows
    out = CHAPTER12.mock(d, "trace", [320, 130, 150, 150], lines=slice(0, 22), compact=True)
    db.emphasize_cells(d, out["geometry"], [(-1, 0), (len(rows) - 1, 0)])
    note(d, "The editor shows the first two of the four tests; the query continues below. Outlined: every "
            "row comes from the first test, and the other three return none.", out["bottom"] + 8, 40)
    return d


def fig_12_03() -> Diagram:
    d = Diagram("Revenue Posted Outside the Year of Delivery")
    rows = db.run(sql("revenue_cutoff"))[1]
    found = {(r[0], r[1]): (r[2], r[3]) for r in rows}
    assert found[("Revenue posted in another year", "2024")] == (15, 90138.93), found
    assert found[("Revenue posted in another year", "2025")] == (8, 19540.86), found
    assert sum(v[0] for k, v in found.items() if k[0] == "Invoice dated before shipment") == 8, found
    # every shipment an invoice bills was delivered in the year it shipped
    assert not q("SELECT 1 FROM Shipment WHERE strftime('%Y', DeliveryDate) <> strftime('%Y', ShipmentDate)")
    cl = comment_lines("revenue_cutoff")
    start = cl + sql("revenue_cutoff").split("\n").index("Classified AS (")
    out = CHAPTER12.mock(d, "revenue_cutoff", [300, 130, 110, 150], lines=slice(start, None), compact=True)
    marks = [i for i, r in enumerate(rows) if r[0] == "Revenue posted in another year"]
    db.emphasize_cells(d, out["geometry"], [(marks[0], 0), (marks[-1], 3)])
    note(d, "The editor is scrolled past the two CTEs that find each invoice's shipment and posting dates. "
            "Outlined: revenue for December deliveries posted in January of the next year.", out["bottom"] + 8, 40)
    return d


def fig_12_04() -> Diagram:
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
    # in the order the CASE of test P1 tests them, so that no exception hides under a normal status
    outcomes = [("Exception: invoiced above received", "invoiced above received", "investigate"),
                ("Exception: received above ordered", "received above ordered", "investigate"),
                ("Not yet received", "nothing received", "an open order"),
                ("Received, not fully invoiced", "invoiced below received",
                 "an accrual: goods received not invoiced"),
                ("Partly received", "received below ordered", "an open order"),
                ("Matched", "ordered = received = invoiced", "complete")]
    case_order = [line.split("'")[1] for line in sql("match_status").split("\n") if "THEN '" in line]
    assert [o[0] for o in outcomes] == case_order + ["Matched"], case_order
    d.grid(0, oy + 22, ["Status, in the order tested", "Condition", "Meaning"], [290, 250, 320], outcomes,
           highlight={(1, 0), (2, 0)})
    split_id = split[0][0]
    split_qty = split[0][2]
    parts = [i[2] for i in invoices if i[1] == split_id]
    note(d, f"Compared row by row, receipt line {split_id} ({split_qty:,.2f}) matches neither of its invoice "
            f"lines ({parts[0]:,.2f} and {parts[1]:,.2f}); summed to the purchase order line, the three "
            "quantities agree. At a 2% tolerance, the first invoice line would be an exception.",
         oy + 22 + ROW_H * 7 + 12, 40)
    return d


def fig_12_05() -> Diagram:
    d = Diagram("The Three-Way Match of Every Purchase Order Line")
    rows = db.run(sql("match_status"))[1]
    status = dict(rows)
    assert not any(s.startswith("Exception") for s in status), status
    assert set(status) == {"Matched", "Received, not fully invoiced", "Not yet received",
                           "Partly received"}, status
    assert status["Matched"] > 0.9 * sum(status.values())
    cl = comment_lines("match_status")
    start = cl + sql("match_status").split("\n").index("SELECT")
    out = CHAPTER12.mock(d, "match_status", [360, 140], lines=slice(start, None), compact=True)
    db.emphasize_cells(d, out["geometry"], [(-1, 0), (len(rows) - 1, 1)])
    note(d, "The editor is scrolled past the three CTEs, which sum the quantities received and invoiced for "
            "each purchase order line. Outlined: four statuses, and neither exception status appears.",
         out["bottom"] + 8, 40)
    return d


def fig_12_06() -> Diagram:
    d = Diagram("Approval Exceptions in the Purchase Orders")
    rows = db.run(sql("approval_summary"))[1]
    counts = {r[0]: r[1] for r in rows}
    assert counts == {"Above approver limit": 13, "Self-approved": 9, "Approved after termination": 3}, counts
    detail = db.run(sql("approval_detail"))[1]
    assert len(detail) == 14 and sum(1 for r in detail if ";" in r[7]) == 11, detail
    out = CHAPTER12.mock(d, "approval_summary", [300, 120, 160], compact=True)
    db.emphasize_cells(d, out["geometry"], [(-1, 0), (len(rows) - 1, 2)])
    note(d, "Outlined: the three tests, with the number of purchase orders each flags and their value. "
            "Most of the fourteen orders fail two tests.", out["bottom"] + 8, 40)
    return d


def fig_12_07() -> Diagram:
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
    assert "LaborTimeEntryID" in {r[1] for r in q("PRAGMA table_info(PayrollRegisterLine)")}
    tests = [("Profiled; overtime above half an hour is approved; no day on which everyone clocks the "
              "same hours", "Tutorial 12.3, Steps 1, 6, and 7"),
             ("Its hours equal the clock entry's; direct time recorded while its operation was open",
              "Tutorial 12.3, Steps 2, 8, and 9"),
             ("Pays its own employee's approved time at the employee's rate; not approved by that employee",
              "Tutorial 12.3, Steps 4 and 5; Exercise 12.5"),
             ("One payment for each approved register, made after its ApprovedDate",
              "Tutorial 12.1; Exercise 12.5"),
             ("Every payment posting traces to a payment; unpaid wages accrued at the year-end",
              "Tutorial 12.1, Steps 3 and 8")]
    w, gap = 148, 30
    boxes = []
    for i, (table, what, key) in enumerate(records):
        x = i * (w + gap)
        via = f"<br><i>linked by {esc(key)}</i>" if key else ""
        boxes.append(d.box(f"<b>{table}</b><br>{esc(what)}{via}", x, 24, w, 130, fill=BLUE_TINT,
                           stroke=BLUE, size=SMALL))
        test, where = tests[i]
        d.box(f"<b>Test</b><br>{esc(test)}<br><i>{esc(where)}</i>", x, 190, w, 170, fill=GRAY_TINT,
              stroke=GRAY, size=SMALL, align="left", valign="top")
    d.text("<b>The records</b>", 0, 0, 300, 20, size=SMALL)
    d.text("<b>The test of each record</b>", 0, 166, 300, 20, size=SMALL)
    for i in range(len(boxes) - 1):
        posting = i == len(boxes) - 2
        d.arrow(boxes[i], boxes[i + 1], color=AMBER if posting else GRAY, dashed=posting,
                exit=(1, 0.5), entry=(0, 0.5))
    ly = 380
    d.line_sample(0, ly + 10, 50, color=GRAY, end="blockThin")
    d.text("one record leads to the next, linked by the key named in the box", 60, ly, 380, 22, size=SMALL)
    d.line_sample(460, ly + 10, 50, color=AMBER, dashed=True, end="blockThin")
    d.text("a posting to the ledger", 520, ly, 340, 22, size=SMALL)
    return d


def fig_12_08() -> Diagram:
    d = Diagram("Days on Which Every Hourly Manufacturing Employee Clocked the Same Hours")
    rows = db.run(sql("surge_days"))[1]
    assert [r[0] for r in rows] == ["2024", "2025", "2026"], rows
    assert [r[1] for r in rows] == [12, 32, 49] and {r[2] for r in rows} == {64}, rows
    shares = [r[4] for r in rows]
    assert shares == sorted(shares) and shares[2] > 0.7, shares
    other = q("SELECT substr(tc.WorkDate, 1, 4), SUM(tc.OvertimeHours) FROM TimeClockEntry tc "
              "JOIN Employee e ON e.EmployeeID = tc.EmployeeID WHERE e.CostCenterID = 4 GROUP BY 1")
    others = [total - r[3] for (_, total), r in zip(other, rows)]
    assert max(others) - min(others) < 0.1 * max(others), others      # overtime on other days flat
    approvers = q("SELECT DISTINCT oa.ApprovedByEmployeeID, oa.ApprovedDate = tc.WorkDate FROM TimeClockEntry tc "
                  "JOIN Employee e ON e.EmployeeID = tc.EmployeeID LEFT JOIN OvertimeApproval oa "
                  "ON oa.OvertimeApprovalID = tc.OvertimeApprovalID WHERE e.CostCenterID = 4 AND tc.WorkDate IN "
                  "(SELECT tc2.WorkDate FROM TimeClockEntry tc2 JOIN Employee e2 ON e2.EmployeeID = tc2.EmployeeID "
                  "WHERE e2.CostCenterID = 4 GROUP BY tc2.WorkDate "
                  "HAVING COUNT(DISTINCT tc2.RegularHours + tc2.OvertimeHours) = 1 AND COUNT(*) > 1)")
    assert approvers == [(4, 1)], approvers        # the Production Manager, on the work date
    out = CHAPTER12.mock(d, "surge_days", [110, 110, 170, 150, 130], compact=True)
    db.emphasize_cells(d, out["geometry"], [(-1, 1), (len(rows) - 1, 1)])
    db.emphasize_cells(d, out["geometry"], [(-1, 4), (len(rows) - 1, 4)])
    hourly = one("SELECT COUNT(*) FROM Employee e JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
                 "WHERE cc.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly'")[0]
    assert hourly == 64, hourly
    note(d, "Outlined: the days on which every one of the 64 hourly manufacturing employees clocked the same hours, "
            "and their share of the year's manufacturing overtime.", out["bottom"] + 8, 40)
    return d


NORMAL_DAY, SURGE_DAY = "2024-03-12", "2026-06-10"
SAMPLE_EMPLOYEES = (17, 18, 19, 20, 21, 22)          # six hourly Assemblers


def fig_12_09() -> Diagram:
    d = Diagram("A Day Before the Surge Days and a Surge Day")
    marks = ",".join("?" * len(SAMPLE_EMPLOYEES))
    staff = q(f"SELECT DISTINCT e.JobTitle, e.PayClass, cc.CostCenterName FROM Employee e JOIN CostCenter cc "
              f"ON cc.CostCenterID = e.CostCenterID WHERE e.EmployeeID IN ({marks})", *SAMPLE_EMPLOYEES)
    assert staff == [("Assembler", "Hourly", "Manufacturing")], staff
    first_surge = one("SELECT MIN(WorkDate) FROM (SELECT tc.WorkDate FROM TimeClockEntry tc JOIN Employee e "
                      "ON e.EmployeeID = tc.EmployeeID WHERE e.CostCenterID = 4 GROUP BY tc.WorkDate HAVING "
                      "COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1 AND COUNT(*) > 1)")[0]
    assert NORMAL_DAY < first_surge, first_surge

    def stats(day: str) -> tuple:
        return one("SELECT COUNT(*), COUNT(DISTINCT tc.ClockInTime), "
                   "COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours), "
                   "SUM(CASE WHEN tc.OvertimeHours > 0 THEN 1 ELSE 0 END), SUM(tc.OvertimeHours) "
                   "FROM TimeClockEntry tc JOIN Employee e ON e.EmployeeID = tc.EmployeeID "
                   "JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
                   "WHERE cc.CostCenterName = 'Manufacturing' AND tc.WorkDate = ?", day)

    def rows(day: str) -> list[tuple]:
        out = []
        for emp, cin, cout, reg, ot, approver, when in q(
                "SELECT tc.EmployeeID, substr(tc.ClockInTime, 12, 5), substr(tc.ClockOutTime, 12, 5), "
                "tc.RegularHours, tc.OvertimeHours, ap.JobTitle, oa.ApprovedDate FROM TimeClockEntry tc "
                "LEFT JOIN OvertimeApproval oa ON oa.OvertimeApprovalID = tc.OvertimeApprovalID "
                "LEFT JOIN Employee ap ON ap.EmployeeID = oa.ApprovedByEmployeeID "
                f"WHERE tc.WorkDate = ? AND tc.EmployeeID IN ({marks}) ORDER BY tc.EmployeeID",
                day, *SAMPLE_EMPLOYEES):
            approval = ("no overtime" if not ot else
                        f"{approver}, on the work date" if when == day else f"{approver}, {when}" if approver
                        else "no approval")
            out.append((str(emp), cin, cout, f"{reg:.2f}", f"{ot:.2f}", approval))
        assert len(out) == len(SAMPLE_EMPLOYEES), (day, out)
        return out

    normal, surge = stats(NORMAL_DAY), stats(SURGE_DAY)
    assert normal[0] == surge[0] == 64 and normal[2] > 20 and surge[2] == 1 and surge[3] == 64, (normal, surge)
    heads = ["Employee", "Clock in", "Clock out", "Regular", "Overtime", "Overtime approved by"]
    widths = [110, 110, 110, 110, 110, 310]
    y = 0
    for day, title, st, highlight in [
            (NORMAL_DAY, "12 March 2024, before the first surge day", normal, None),
            (SURGE_DAY, "10 June 2026, a surge day", surge, {(r, c) for r in range(1, 7) for c in (1, 2, 3, 4)})]:
        d.text(f"<b>{title}</b>", 0, y, 860, 20, size=SMALL)
        d.grid(0, y + 22, heads, widths, rows(day), highlight=highlight)
        y += 22 + ROW_H * 7 + 6
        clock_ins = f"{st[1]} different clock-in times" if st[1] > 1 else "one clock-in time"
        hours = f"{st[2]} different numbers of hours" if st[2] > 1 else "one number of hours"
        d.text(f"All {st[0]} hourly manufacturing employees: {clock_ins}, {hours}; {st[3]} worked overtime, "
               f"{st[4]:,.1f} hours in all.", 0, y, 860, 22, size=SMALL)
        y += 44
    note(d, "The same six Assemblers on both days; a clock-out after midnight falls on the next day. Highlighted: "
            "the identical times and hours of the surge day, when the two shifts clocked in at the same minutes.",
         y, 40)
    return d


def fig_12_10() -> Diagram:
    d = Diagram("Direct Labor Recorded After Its Operation Ended")
    rows = db.run(sql("late_by_year"))[1]
    shares = [r[3] for r in rows]
    assert [r[0] for r in rows] == ["2024", "2025", "2026"], rows
    assert 0.17 < shares[0] < 0.23 and 0.45 < shares[1] < 0.55 and 0.6 < shares[2] < 0.7, shares
    on_surge = [r[4] / r[2] for r in rows]
    assert on_surge == sorted(on_surge) and on_surge[0] > 0.7 and on_surge[2] > 0.85, on_surge
    cl = comment_lines("late_by_year")
    start = cl + sql("late_by_year").split("\n").index("SELECT strftime('%Y', lt.WorkDate) AS WorkYear,")
    out = CHAPTER12.mock(d, "late_by_year", [100, 120, 100, 140, 200], lines=slice(start, None),
                         compact=True)
    db.emphasize_cells(d, out["geometry"], [(-1, 3), (len(rows) - 1, 4)])
    note(d, "The editor is scrolled past the CTE that lists the surge days of test H8. Outlined: the share of "
            "direct hours recorded after the operation ended, and the part of them recorded on surge days.",
         out["bottom"] + 8, 40)
    return d


def fig_12_11() -> Diagram:
    d = Diagram("The Start of an Audit Query Library")
    for key, _, text in QUERIES:                 # every test of the script runs
        db.run(text)
    comment, text, line = CHAPTER12.location("je_population")
    end = line - 1 + comment.count("\n") + 1 + text.count("\n") + 1   # the header and test L1
    shown = "\n".join(CHAPTER12.text().split("\n")[:end])
    bottom = db.editor(d, 0, 0, 860, shown, tab="Audit.sql", toolbar=False)
    note(d, "The header records the purpose, the data, and who prepared and reviewed the script. Each test "
            "begins with a comment that names it and states its population and expected result. The script "
            "continues with the other tests below the lines shown.", bottom + 8, 40)
    return d


FIGURES = {
    "fig-12-01-two-way-trace": fig_12_01,
    "fig-12-02-trace-exceptions": fig_12_02,
    "fig-12-03-revenue-cutoff": fig_12_03,
    "fig-12-04-three-way-match": fig_12_04,
    "fig-12-05-three-way-match-status": fig_12_05,
    "fig-12-06-approval-exceptions": fig_12_06,
    "fig-12-07-labor-record-chain": fig_12_07,
    "fig-12-08-surge-days": fig_12_08,
    "fig-12-09-normal-and-surge-day": fig_12_09,
    "fig-12-10-labor-after-operation-end": fig_12_10,
    "fig-12-11-audit-library": fig_12_11,
}
