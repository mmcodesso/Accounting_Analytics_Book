"""Chapter 10 figures."""

from __future__ import annotations

import dbbrowser as db
import excel as xl
from ch03 import legend, table as er_table
from data import one, q, relate
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK,
                    ROW_H, RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc, money)
from shared.calculations.sql_ch10 import (
    HEADER, _JOIN_ITEMS, _TB_INNER, _OUTPUT, _PAYROLL, QUERIES
)

SAMPLE_WORK_ORDERS = (13014, 13015, 13016, 13017)   # three closed, one released
FAN_OUT_INVOICE = "SI-2026-019134"                   # a fiscal 2026 invoice with three lines

# Chapter10.sql as the three tutorials build it (see dbbrowser.Script). The tutorial text must
# match these queries exactly.
CHAPTER10 = db.Script(HEADER, QUERIES, "Chapter10.sql")


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


def num(value: float) -> str:
    return f"{value:,.2f}"


def fig_10_01() -> Diagram:
    d = Diagram("How Inner and Left Joins Match Rows")
    orders = q("SELECT WorkOrderID, WorkOrderNumber, Status FROM WorkOrder WHERE WorkOrderID IN "
               "(?, ?, ?, ?) ORDER BY WorkOrderID", *SAMPLE_WORK_ORDERS)
    closes = dict((w, (c, v)) for c, w, v in q(
        "SELECT WorkOrderCloseID, WorkOrderID, TotalVarianceAmount FROM WorkOrderClose "
        "WHERE WorkOrderID IN (?, ?, ?, ?)", *SAMPLE_WORK_ORDERS))
    assert len(orders) == 4 and len(closes) == 3, (orders, closes)
    d.text("<b>WorkOrder</b>", 0, 0, 380, 20, size=SMALL)
    d.grid(0, 22, ["WorkOrderID", "WorkOrderNumber", "Status"], [110, 170, 100],
           [(str(w), n, s) for w, n, s in orders])
    d.text("<b>WorkOrderClose</b>", 480, 0, 380, 20, size=SMALL)
    d.grid(480, 22, ["WorkOrderCloseID", "WorkOrderID", "TotalVariance"], [140, 110, 130],
           [(str(c), str(w), num(v)) for w, (c, v) in sorted(closes.items())])
    d.text("Matched on WorkOrderID. The released work order has no close.", 0, 150, 860, 20,
           size=SMALL, color=INK)
    y = 186
    d.text("<b>Inner join:</b> only the work orders that have a close", 0, y, 860, 20, size=SMALL)
    inner = [(str(w), n, str(closes[w][0]), num(closes[w][1])) for w, n, _ in orders if w in closes]
    d.grid(0, y + 22, ["WorkOrderID", "WorkOrderNumber", "WorkOrderCloseID", "TotalVariance"],
           [110, 170, 140, 130], inner)
    y += 22 + ROW_H * (len(inner) + 1) + 16
    d.text("<b>Left join from WorkOrder:</b> every work order, with NULL where no close exists",
           0, y, 860, 20, size=SMALL)
    left = [(str(w), n, str(closes[w][0]) if w in closes else "NULL",
             num(closes[w][1]) if w in closes else "NULL") for w, n, _ in orders]
    missing = [i + 1 for i, row in enumerate(left) if row[2] == "NULL"]
    assert len(missing) == 1, missing
    d.grid(0, y + 22, ["WorkOrderID", "WorkOrderNumber", "WorkOrderCloseID", "TotalVariance"],
           [110, 170, 140, 130], left, highlight={(missing[0], 2), (missing[0], 3)})
    y += 22 + ROW_H * (len(left) + 1) + 16
    d.text("<b>Anti-join:</b> the left join, keeping only the rows where WorkOrderCloseID IS NULL",
           0, y, 860, 20, size=SMALL)
    d.grid(0, y + 22, ["WorkOrderID", "WorkOrderNumber", "WorkOrderCloseID", "TotalVariance"],
           [110, 170, 140, 130], [left[missing[0] - 1]], highlight={(1, 2), (1, 3)})
    note(d, "Highlighted: the NULLs that the left join supplies where no close exists. The anti-join keeps only "
            "those rows.", y + 22 + ROW_H * 2 + 8, 40)
    return d


def fig_10_02() -> Diagram:
    d = Diagram("GROUP BY Collapses Rows into One Row per Group")
    rows = []
    for group in ("Furniture", "Lighting"):
        rows += q("SELECT i.ItemGroup, woc.WorkOrderCloseID, woc.TotalVarianceAmount "
                  "FROM WorkOrderClose woc JOIN WorkOrder wo ON wo.WorkOrderID = woc.WorkOrderID "
                  "JOIN Item i ON i.ItemID = wo.ItemID WHERE woc.CloseDate BETWEEN '2026-12-01' "
                  "AND '2026-12-31' AND i.ItemGroup = ? ORDER BY woc.WorkOrderCloseID LIMIT 3", group)
    assert len(rows) == 6
    d.text("<b>Rows of the sample</b>", 0, 0, 400, 20, size=SMALL)
    d.grid(0, 22, ["ItemGroup", "WorkOrderCloseID", "TotalVariance"], [130, 150, 130],
           [(g, str(c), num(v)) for g, c, v in rows])
    d.text("<b>GROUP BY ItemGroup</b>", 520, 0, 340, 20, size=SMALL)
    totals = {}
    for g, _, v in rows:
        n, s = totals.get(g, (0, 0.0))
        totals[g] = (n + 1, s + v)
    out = d.grid(520, 58, ["ItemGroup", "COUNT(*)", "SUM(TotalVariance)"], [110, 80, 150],
                 [(g, str(n), num(s)) for g, (n, s) in totals.items()])
    for i, group in enumerate(totals):
        src = d.container(410, 22 + ROW_H * (1 + 3 * i), 2, ROW_H * 3)
        d.arrow(src, out[(i + 1, 0)], color=GRAY)
    note(d, "The summary totals only the six sample rows shown, three December 2026 closes from each of two "
            "item groups. Each group of rows becomes one row of the result.", 22 + ROW_H * 7 + 10, 40)
    return d


def fig_10_03() -> Diagram:
    d = Diagram("The Manufacturing Variance by Item Group and Year")
    _, sql, _ = CHAPTER10.location("variance_by_group_year")
    headers, rows = db.run(sql)
    furniture = [r for r in rows if r[0] == "Furniture"]
    textiles = [r for r in rows if r[0] == "Textiles"]
    assert [r[1] for r in furniture] == ["2024", "2025", "2026"]
    assert furniture[0][3] < furniture[1][3] < furniture[2][3], "Furniture variance rises each year"
    assert furniture[0][2] > furniture[1][2] > furniture[2][2], "while its closes fall"
    assert textiles[1][3] > textiles[2][3], "Textiles fell back in 2026"
    assert furniture[2][3] > 0.66 * sum(r[3] for r in rows if r[1] == "2026")
    out = CHAPTER10.mock(d, "variance_by_group_year", [130, 110, 90, 170, 170], compact=True)
    db.emphasize_cells(d, out["geometry"], [(0, 0), (2, 4)])
    note(d, "Outlined: the Furniture rows, whose variance rises in each year while the number of closes falls.",
         out["bottom"] + 8, 22)
    return d


def fig_10_04() -> Diagram:
    d = Diagram("Fan-Out: A Header Amount Repeated on Every Line")
    rows = q("SELECT i.InvoiceNumber, i.GrandTotal, l.LineNumber, l.LineTotal FROM SalesInvoice i "
             "JOIN SalesInvoiceLine l ON l.SalesInvoiceID = i.SalesInvoiceID WHERE i.InvoiceNumber = ? "
             "ORDER BY l.LineNumber", FAN_OUT_INVOICE)
    assert len(rows) == 3
    grand = rows[0][1]
    lines = sum(r[3] for r in rows)
    freight_tax = one("SELECT FreightAmount + TaxAmount FROM SalesInvoice WHERE InvoiceNumber = ?",
                      FAN_OUT_INVOICE)[0]
    assert abs(lines + freight_tax - grand) < 0.005
    true_total, joined_total = one(
        "SELECT (SELECT SUM(GrandTotal) FROM SalesInvoice WHERE InvoiceDate BETWEEN '2026-01-01' AND '2026-12-31'), "
        "(SELECT SUM(i.GrandTotal) FROM SalesInvoice i JOIN SalesInvoiceLine l ON l.SalesInvoiceID = i.SalesInvoiceID "
        "WHERE i.InvoiceDate BETWEEN '2026-01-01' AND '2026-12-31')")
    assert 1.7 < joined_total / true_total < 2.0
    d.text(f"<b>SalesInvoice joined to SalesInvoiceLine: invoice {FAN_OUT_INVOICE}</b>", 0, 0, 860, 20,
           size=SMALL)
    d.grid(0, 22, ["InvoiceNumber", "GrandTotal", "LineNumber", "LineTotal"], [170, 140, 110, 140],
           [(n, num(g), str(ln), num(lt)) for n, g, ln, lt in rows],
           highlight={(1, 1), (2, 1), (3, 1)})
    y = 22 + ROW_H * 4 + 16
    d.box(f"<b>SUM(GrandTotal)</b> over the joined rows<br>{num(grand * 3)}: the invoice counted three times",
          0, y, 410, 56, fill=CORAL_TINT, stroke=CORAL, align="left")
    d.box(f"<b>SUM(LineTotal)</b> over the joined rows<br>{num(lines)}: each line counted once",
          450, y, 410, 56, fill=TEAL_TINT, stroke=TEAL, align="left")
    note(d, f"Outlined: the GrandTotal repeated on every line. Across fiscal 2026, SUM(GrandTotal) over the joined rows "
            f"is {joined_total / 1e6:,.1f} million, against {true_total / 1e6:,.1f} million for the invoices themselves.",
         y + 66, 40)
    return d


def fig_10_05() -> Diagram:
    d = Diagram("The Order in Which a Query Is Written and Evaluated")
    steps = [("FROM and JOIN", "assemble the rows of the tables and their joins"),
             ("WHERE", "keep the rows that meet the condition"),
             ("GROUP BY", "form the groups"),
             ("HAVING", "keep the groups that meet the condition"),
             ("SELECT and DISTINCT", "calculate the columns and aliases, then drop duplicate rows"),
             ("ORDER BY", "sort the result; the aliases of SELECT can be used"),
             ("LIMIT", "keep the first rows")]
    step_of = {name: i + 1 for i, (name, _) in enumerate(steps)}
    written = ["SELECT and DISTINCT", "FROM and JOIN", "WHERE", "GROUP BY", "HAVING", "ORDER BY",
               "LIMIT"]
    d.text("<b>Written</b>", 0, 0, 280, 20, size=SMALL)
    d.text("<b>Evaluated, logically</b>", 330, 0, 530, 20, size=SMALL)
    for i, name in enumerate(written):
        y = 26 + i * 44
        label = name.replace(" and DISTINCT", " (DISTINCT)")
        d.box(f"<b>{esc(label)}</b>", 0, y, 240, 34, fill=GRAY_TINT, stroke=GRAY, size=SMALL)
        d.marker(str(step_of[name]), 250, y + 5)
    for i, (name, what) in enumerate(steps):
        y = 26 + i * 44
        d.marker(str(i + 1), 330, y + 5)
        d.box(f"<b>{esc(name)}</b>", 362, y, 190, 34, fill=BLUE_TINT, stroke=BLUE, size=SMALL)
        d.text(esc(what), 562, y, 298, 34, size=SMALL, valign="middle")
    note(d, "The number beside each written clause is the step at which it is evaluated. WHERE runs before any "
            "group exists, so it cannot use an aggregate; HAVING runs after grouping, and ORDER BY after SELECT.",
         26 + 7 * 44 + 4, 40)
    return d


def fig_10_06() -> Diagram:
    d = Diagram("The Pre-Closing Trial Balance of Fiscal 2026")
    _, sql, _ = CHAPTER10.location("trial_balance")
    headers, rows = db.run(sql)
    assert len(rows) == 71
    debit = round(sum(r[3] for r in rows if r[3] > 0), 2)
    credit = round(-sum(r[3] for r in rows if r[3] < 0), 2)
    assert debit == credit == 67107722.36, (debit, credit)
    out = CHAPTER10.mock(d, "trial_balance", [130, 340, 110, 150], shown=slice(0, 12), compact=True)
    note(d, "The first twelve of the accounts are shown. Positive balances are debit balances and negative "
            "balances credit balances.", out["bottom"] + 8, 40)
    return d


def fig_10_07() -> Diagram:
    d = Diagram("The Flow of Conversion Cost Through Account 1090")
    payroll = one("SELECT SUM(Debit) FROM GLEntry WHERE AccountID = 92 AND FiscalYear = 2026 "
                  "AND SourceDocumentType = 'PayrollSummary'")[0]
    je = dict(q("SELECT je.EntryType, SUM(gl.Debit) FROM GLEntry gl JOIN JournalEntry je "
                "ON je.JournalEntryID = gl.SourceDocumentID WHERE gl.AccountID = 92 AND gl.FiscalYear = 2026 "
                "AND gl.SourceDocumentType = 'JournalEntry' GROUP BY je.EntryType"))
    completions = one("SELECT SUM(Credit) FROM GLEntry WHERE AccountID = 92 AND FiscalYear = 2026 "
                      "AND SourceDocumentType = 'ProductionCompletion'")[0]
    closes = one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = 92 AND FiscalYear = 2026 "
                 "AND SourceDocumentType = 'WorkOrderClose'")[0]
    conversion = one("SELECT SUM(ConversionVarianceAmount) FROM WorkOrderClose WHERE CloseDate "
                     "BETWEEN '2026-01-01' AND '2026-12-31'")[0]
    assert abs(closes - conversion) < 0.01
    assert set(je) == {"Factory Overhead", "Depreciation"}
    inflow = payroll + je["Factory Overhead"] + je["Depreciation"]
    remainder = inflow - completions - closes
    assert 0 < remainder < 10000, remainder
    ins = [("Manufacturing payroll", "PayrollSummary", payroll),
           ("Factory overhead", "journal entries", je["Factory Overhead"]),
           ("Depreciation of manufacturing equipment", "journal entries", je["Depreciation"])]
    acct = d.box("<b>1090 Manufacturing<br>Cost Clearing</b>", 330, 110, 200, 110, fill=BLUE,
                 stroke=BLUE, color=WHITE, size=14)
    for i, (label, source, amount) in enumerate(ins):
        b = d.box(f"<b>{esc(label)}</b><br>{esc(source)}: {money(amount)}", 0, 40 + i * 90, 260, 70,
                  fill=AMBER_TINT if i == 0 else GRAY_TINT, stroke=AMBER if i == 0 else GRAY,
                  align="left")
        d.arrow(b, acct, color=GRAY, exit=(1, 0.5), entry=(0, 0.2 + 0.3 * i))
    out1 = d.box(f"<b>Finished goods inventory</b><br>standard conversion cost of the units completed: "
                 f"{money(completions)}", 600, 40, 260, 80, fill=GRAY_TINT, stroke=GRAY, align="left")
    out2 = d.box(f"<b>5080 Manufacturing Variance</b><br>conversion variance cleared by work order closes: "
                 f"{money(closes)}", 600, 180, 260, 80, fill=CORAL_TINT, stroke=CORAL, align="left")
    d.arrow(acct, out1, color=GRAY, exit=(1, 0.3), entry=(0, 0.5))
    d.arrow(acct, out2, color=GRAY, exit=(1, 0.7), entry=(0, 0.5))
    d.text("<b>Debits: actual cost in</b>", 0, 10, 260, 22, size=SMALL)
    d.text("<b>Credits: cost out</b>", 600, 10, 260, 22, size=SMALL)
    note(d, f"Amounts are the postings of fiscal 2026. The debits exceed the credits by {money(remainder)}, "
            "the year's net change in the account.", 320, 40)

    def by_year(sql: str) -> list[float]:
        rows = dict(q(sql + " AND FiscalYear BETWEEN 2024 AND 2026 GROUP BY FiscalYear"))
        assert sorted(rows) == [2024, 2025, 2026], rows
        return [rows[y] for y in (2024, 2025, 2026)]

    pay = by_year("SELECT FiscalYear, SUM(Debit) FROM GLEntry WHERE AccountID = 92 "
                  "AND SourceDocumentType = 'PayrollSummary'")
    jes = by_year("SELECT FiscalYear, SUM(Debit) FROM GLEntry WHERE AccountID = 92 "
                  "AND SourceDocumentType = 'JournalEntry'")
    std = by_year("SELECT FiscalYear, SUM(Credit) FROM GLEntry WHERE AccountID = 92 "
                  "AND SourceDocumentType = 'ProductionCompletion'")
    cleared = by_year("SELECT FiscalYear, SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = 92 "
                      "AND SourceDocumentType = 'WorkOrderClose'")
    _, rows = db.run(CHAPTER10.location("variance_parts")[1])
    assert [r[0] for r in rows] == ["2024", "2025", "2026"], rows
    labor, overhead, conversion = ([r[i] for r in rows] for i in (1, 2, 3))
    assert all(abs(a - b) < 0.01 for a, b in zip(cleared, conversion)), (cleared, conversion)
    assert all(abs(a + b - c) < 0.02 for a, b, c in zip(labor, overhead, conversion))
    assert labor[0] < labor[1] < labor[2] < 0, labor              # favorable and shrinking
    assert overhead == sorted(overhead) and pay == sorted(pay)
    assert max(std) / min(std) < 1.1, std                          # standard cost released nearly flat
    y = 376
    d.text("<b>Account 1090 by fiscal year</b>", 0, y, 860, 20, size=SMALL)
    d.grid(0, y + 22, ["Postings", "2024", "2025", "2026"], [370, 160, 160, 170],
           [("Debits: manufacturing payroll", *map(num, pay)),
            ("Debits: factory overhead and depreciation", *map(num, jes)),
            ("Credits: standard conversion cost of completions", *map(num, std)),
            ("Credits: conversion variance cleared to 5080", *map(num, cleared)),
            ("Of which the direct labor part", *map(num, labor)),
            ("Of which the overhead part", *map(num, overhead))],
           highlight={(6, 1), (6, 2), (6, 3)})
    note(d, "The two parts of the variance come from the work order closes; a negative part is favorable. "
            "Highlighted: the overhead part, which grew in each year while the labor part shrank.",
         y + 22 + ROW_H * 7 + 8, 40)
    return d


def fig_10_08() -> Diagram:
    d = Diagram("The Payroll and Time Tables")
    C0, C1, C2, W = 0, 300, 600, 240
    BOTTOM, TOP, LEFT, RIGHT = (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)
    oa = er_table(d, "OvertimeApproval", C0, 20, [("PK", "OvertimeApprovalID"), ("", "WorkDate"),
                  ("", "RequestedHours"), ("", "ApprovedHours"), ("", "ReasonCode"), ("", "Status")], w=W)
    woo = er_table(d, "WorkOrderOperation", C1, 20, [("PK", "WorkOrderOperationID"), ("FK", "WorkOrderID"),
                   ("", "PlannedLoadHours"), ("", "ActualEndDate")], w=W, focus=False,
                   group="Manufacturing")
    lte = er_table(d, "LaborTimeEntry", C1, 196, [("PK", "LaborTimeEntryID"), ("FK", "WorkOrderOperationID"),
                   ("FK", "TimeClockEntryID"), ("FK", "EmployeeID"), ("", "WorkDate"), ("", "LaborType"),
                   ("", "RegularHours"), ("", "OvertimeHours")], w=W)
    # TimeClockEntry sits so that its key row lines up with LaborTimeEntry.TimeClockEntryID
    tce_y = lte.cy("TimeClockEntryID") - 30 - ROW_H / 2
    tce = er_table(d, "TimeClockEntry", C0, tce_y, [("PK", "TimeClockEntryID"), ("FK", "EmployeeID"),
                   ("FK", "OvertimeApprovalID"), ("", "WorkDate"), ("", "ClockInTime"), ("", "ClockOutTime"),
                   ("", "RegularHours"), ("", "OvertimeHours"), ("", "ClockStatus")], w=W)
    assert tce_y >= oa.y + oa.h + 40, tce_y
    emp = er_table(d, "Employee", C1, lte.y + lte.h + 60, [("PK", "EmployeeID"), ("", "EmployeeName"),
                   ("", "JobTitle"), ("", "TerminationDate")], w=W, focus=False, group="Master Data")
    cc = er_table(d, "CostCenter", C1, emp.y + emp.h + 60, [("PK", "CostCenterID"), ("", "CostCenterName")],
                  w=W, focus=False, group="Organizational Planning")
    pp = er_table(d, "PayrollPeriod", C2, 20, [("PK", "PayrollPeriodID"), ("", "PeriodNumber"),
                  ("", "PeriodEndDate"), ("", "PayDate"), ("", "FiscalYear"), ("", "Status")], w=W)
    pr = er_table(d, "PayrollRegister", C2, lte.y + 48, [("PK", "PayrollRegisterID"), ("FK", "PayrollPeriodID"),
                  ("FK", "EmployeeID"), ("FK", "CostCenterID"), ("", "GrossPay"), ("", "Status")], w=W)
    prl = er_table(d, "PayrollRegisterLine", C2, pr.y + pr.h + 50, [("PK", "PayrollRegisterLineID"),
                   ("FK", "PayrollRegisterID"), ("", "LineType"), ("", "Hours"), ("", "Amount")], w=W)
    pay = er_table(d, "PayrollPayment", C2, prl.y + prl.h + 50, [("PK", "PayrollPaymentID"),
                   ("FK", "PayrollRegisterID"), ("", "PaymentDate")], w=W)
    relate(d, "OvertimeApproval", "OvertimeApprovalID", "TimeClockEntry", "OvertimeApprovalID", oa.id, tce.id,
           exit=BOTTOM, entry=TOP)
    relate(d, "TimeClockEntry", "TimeClockEntryID", "LaborTimeEntry", "TimeClockEntryID",
           tce.rows["TimeClockEntryID"], lte.rows["TimeClockEntryID"], exit=RIGHT, entry=LEFT)
    relate(d, "WorkOrderOperation", "WorkOrderOperationID", "LaborTimeEntry", "WorkOrderOperationID",
           woo.id, lte.id, color=AMBER, exit=BOTTOM, entry=TOP)
    relate(d, "Employee", "EmployeeID", "LaborTimeEntry", "EmployeeID", emp.id, lte.id, color=AMBER,
           exit=TOP, entry=BOTTOM)
    relate(d, "Employee", "EmployeeID", "TimeClockEntry", "EmployeeID", emp.rows["EmployeeID"],
           tce.rows["EmployeeID"], color=AMBER, exit=LEFT, entry=RIGHT,
           points=[(C0 + W + 30, emp.cy("EmployeeID")), (C0 + W + 30, tce.cy("EmployeeID"))])
    relate(d, "Employee", "EmployeeID", "PayrollRegister", "EmployeeID", emp.rows["EmployeeID"],
           pr.rows["EmployeeID"], color=AMBER, exit=RIGHT, entry=LEFT,
           points=[(C1 + W + 20, emp.cy("EmployeeID")), (C1 + W + 20, pr.cy("EmployeeID"))])
    relate(d, "CostCenter", "CostCenterID", "PayrollRegister", "CostCenterID", cc.rows["CostCenterID"],
           pr.rows["CostCenterID"], color=AMBER, exit=RIGHT, entry=LEFT,
           points=[(C1 + W + 42, cc.cy("CostCenterID")), (C1 + W + 42, pr.cy("CostCenterID"))])
    relate(d, "PayrollPeriod", "PayrollPeriodID", "PayrollRegister", "PayrollPeriodID", pp.id, pr.id,
           exit=BOTTOM, entry=TOP)
    relate(d, "PayrollRegister", "PayrollRegisterID", "PayrollRegisterLine", "PayrollRegisterID", pr.id,
           prl.id, exit=BOTTOM, entry=TOP)
    relate(d, "PayrollRegister", "PayrollRegisterID", "PayrollPayment", "PayrollRegisterID",
           pr.rows["PayrollRegisterID"], pay.rows["PayrollRegisterID"], exit=RIGHT, entry=RIGHT,
           points=[(C2 + W + 14, pr.cy("PayrollRegisterID")), (C2 + W + 14, pay.cy("PayrollRegisterID"))])
    legend(d, C0, tce.y + tce.h + 50, W, stacked=True)
    return d


def fig_10_09() -> Diagram:
    d = Diagram("Hours per Standard Hour by Labor Type and Year")
    _, sql, _ = CHAPTER10.location("hours_by_type")
    headers, rows = db.run(sql)
    direct = [r[4] for r in rows if r[1] == "Direct Manufacturing"]
    indirect = [r[4] for r in rows if r[1] == "Indirect Manufacturing"]
    assert [r[0] for r in rows] == ["2024", "2024", "2025", "2025", "2026", "2026"], rows
    entries, with_op, _, first_work, last_work = db.run(CHAPTER10.location("profile_time")[1])[1][0]
    assert 0.7 < with_op / entries < 0.8 and (first_work, last_work) == ("2024-01-01", "2026-12-11")
    last_completion = db.run(CHAPTER10.location("profile_output")[1])[1][0][2]
    assert last_completion == "2026-12-31", last_completion
    open_periods = [r[0] for r in db.run(CHAPTER10.location("last_periods")[1])[1] if r[4] == "Open"]
    assert open_periods == ["PP-2026-078", "PP-2026-079"], open_periods
    assert all(0.8 < x < 1.0 for x in direct), direct            # direct time within standard
    assert indirect == sorted(indirect) and indirect[2] > 1.5 * indirect[0], indirect
    totals = [round(a + b, 2) for a, b in zip(direct, indirect)]
    assert totals == sorted(totals) and 1.4 < totals[2] < 1.55, totals
    out = CHAPTER10.mock(d, "hours_by_type", [110, 220, 120, 150, 210], compact=True)
    db.emphasize_cells(d, out["geometry"], [(-1, 4), (5, 4)])
    note(d, "Outlined: hours recorded per standard hour of output. Direct time stays below the standard in each "
            "year, while indirect time grows.", out["bottom"] + 8, 40)
    return d


FIGURES = {
    "fig-10-01-join-matching": fig_10_01,
    "fig-10-02-group-by": fig_10_02,
    "fig-10-03-variance-by-group-year": fig_10_03,
    "fig-10-04-fan-out": fig_10_04,
    "fig-10-05-evaluation-order": fig_10_05,
    "fig-10-06-trial-balance": fig_10_06,
    "fig-10-07-conversion-cost-flow": fig_10_07,
    "fig-10-08-payroll-time-er": fig_10_08,
    "fig-10-09-hours-per-standard-hour": fig_10_09,
}
