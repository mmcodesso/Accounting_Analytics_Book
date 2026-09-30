"""Chapter 10 figures."""

from __future__ import annotations

import dbbrowser as db
import excel as xl
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK,
                    ROW_H, RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc, money)

SAMPLE_WORK_ORDERS = (13014, 13015, 13016, 13017)   # three closed, one released
FAN_OUT_INVOICE = "SI-2026-019134"                   # a fiscal 2026 invoice with three lines


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
    d.grid(0, y + 22, ["WorkOrderID", "WorkOrderNumber", "WorkOrderCloseID", "TotalVariance"],
           [110, 170, 140, 130], left, highlight={(missing[0], 2), (missing[0], 3)})
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
    sql = ("SELECT i.ItemGroup, SUBSTR(woc.CloseDate, 1, 4) AS CloseYear,\n"
           "    COUNT(*) AS Closes,\n"
           "    ROUND(SUM(woc.TotalVarianceAmount), 2) AS TotalVariance,\n"
           "    ROUND(SUM(woc.OverheadVarianceAmount), 2) AS OverheadVariance\n"
           "FROM WorkOrderClose AS woc\n"
           "    INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = woc.WorkOrderID\n"
           "    INNER JOIN Item AS i ON i.ItemID = wo.ItemID\n"
           "GROUP BY i.ItemGroup, CloseYear\n"
           "ORDER BY i.ItemGroup, CloseYear;")
    headers, rows = db.run(sql)
    furniture = [r for r in rows if r[0] == "Furniture"]
    assert [r[1] for r in furniture] == ["2024", "2025", "2026"]
    assert furniture[0][3] < furniture[1][3] < furniture[2][3], "Furniture variance rises each year"
    assert furniture[0][2] > furniture[1][2] > furniture[2][2], "while its closes fall"
    assert furniture[2][3] > 0.66 * sum(r[3] for r in rows if r[1] == "2026")
    out = db.execute_sql(d, sql, [130, 110, 90, 170, 170])
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
    written = ["SELECT", "FROM and JOIN", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT"]
    evaluated = [("FROM and JOIN", "assemble the rows of the tables and their joins"),
                 ("WHERE", "keep the rows that meet the condition"),
                 ("GROUP BY", "form the groups"),
                 ("HAVING", "keep the groups that meet the condition"),
                 ("SELECT", "calculate the columns, aggregates, and aliases"),
                 ("ORDER BY", "sort the result, and aliases can be used"),
                 ("LIMIT", "keep the first rows")]
    d.text("<b>Written</b>", 0, 0, 200, 20, size=SMALL)
    d.text("<b>Evaluated</b>", 330, 0, 530, 20, size=SMALL)
    left, right = {}, {}
    for i, name in enumerate(written):
        left[name] = d.box(f"<b>{esc(name)}</b>", 0, 26 + i * 44, 200, 34, fill=GRAY_TINT,
                           stroke=GRAY, size=SMALL)
    for i, (name, what) in enumerate(evaluated):
        right[name] = d.box(f"<b>{i + 1}. {esc(name)}</b>", 330, 26 + i * 44, 200, 34,
                            fill=BLUE_TINT, stroke=BLUE, size=SMALL)
        d.text(esc(what), 546, 26 + i * 44, 314, 34, size=SMALL, valign="middle")
    for name in written:
        d.edge(left[name], right[name], color=GRAY, exit=(1, 0.5), entry=(0, 0.5))
    note(d, "WHERE runs before any group exists, so it cannot use an aggregate; HAVING runs after grouping, "
            "and ORDER BY after SELECT.", 26 + 7 * 44 + 4, 40)
    return d


def fig_10_06() -> Diagram:
    d = Diagram("The Pre-Closing Trial Balance of Fiscal 2026")
    sql = ("SELECT a.AccountNumber, a.AccountName, a.AccountType,\n"
           "    ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Balance\n"
           "FROM GLEntry AS gl\n"
           "    INNER JOIN Account AS a ON a.AccountID = gl.AccountID\n"
           "WHERE gl.PostingDate <= '2026-12-31'\n"
           "    AND gl.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297')\n"
           "GROUP BY a.AccountID, a.AccountNumber, a.AccountName, a.AccountType\n"
           "ORDER BY a.AccountNumber;")
    headers, rows = db.run(sql)
    assert len(rows) == 71
    debit = round(sum(r[3] for r in rows if r[3] > 0), 2)
    credit = round(-sum(r[3] for r in rows if r[3] < 0), 2)
    assert debit == credit == 67107722.36, (debit, credit)
    out = db.execute_sql(d, sql, [130, 340, 110, 150], shown=slice(0, 12))
    note(d, "The first twelve of the accounts are shown. Positive balances are debit balances and negative "
            "balances credit balances.", out["bottom"] + 8, 40)
    return d


def fig_10_07() -> Diagram:
    d = Diagram("The Flow of Conversion Cost Through Account 1090 in Fiscal 2026")
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
    note(d, f"Amounts are the postings of fiscal 2026. The cost in exceeds the cost out by {money(remainder)}, "
            "which stays in the account for work not yet closed.", 320, 40)
    return d


def fig_10_08() -> Diagram:
    d = Diagram("Paid Hours per Standard Hour by Year")
    sql = ("SELECT o.Yr, o.StandardHours, p.PaidHours,\n"
           "    ROUND(p.PaidHours / o.StandardHours, 2) AS PaidPerStandardHour\n"
           "FROM (SELECT CAST(SUBSTR(pc.CompletionDate, 1, 4) AS INTEGER) AS Yr, ...) AS o\n"
           "    INNER JOIN (SELECT pp.FiscalYear AS Yr, ...) AS p ON p.Yr = o.Yr\n"
           "ORDER BY o.Yr;")
    full = (
        "SELECT o.Yr, o.StandardHours, p.PaidHours, ROUND(p.PaidHours / o.StandardHours, 2) AS PaidPerStandardHour "
        "FROM (SELECT CAST(SUBSTR(pc.CompletionDate, 1, 4) AS INTEGER) AS Yr, "
        "ROUND(SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit), 0) AS StandardHours "
        "FROM ProductionCompletionLine AS pcl INNER JOIN ProductionCompletion AS pc "
        "ON pc.ProductionCompletionID = pcl.ProductionCompletionID INNER JOIN Item AS i ON i.ItemID = pcl.ItemID "
        "GROUP BY Yr) AS o INNER JOIN (SELECT pp.FiscalYear AS Yr, ROUND(SUM(prl.Hours), 0) AS PaidHours "
        "FROM PayrollRegisterLine AS prl INNER JOIN PayrollRegister AS pr ON pr.PayrollRegisterID = prl.PayrollRegisterID "
        "INNER JOIN PayrollPeriod AS pp ON pp.PayrollPeriodID = pr.PayrollPeriodID "
        "INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID "
        "WHERE cc.CostCenterName = 'Manufacturing' AND prl.LineType IN ('Regular Earnings', 'Overtime Earnings') "
        "GROUP BY pp.FiscalYear) AS p ON p.Yr = o.Yr ORDER BY o.Yr")
    headers, rows = db.run(full)
    ratios = [r[3] for r in rows]
    assert [r[0] for r in rows] == [2024, 2025, 2026] and ratios == sorted(ratios)
    assert ratios[0] < 1.2 and ratios[2] > 1.45, ratios
    y = db.window(d)
    y = db.editor(d, 0, y, 860, sql) + 8
    geometry = db.results(d, 0, y, headers, [110, 180, 180, 220], rows)
    y += (len(rows) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0])
    db.emphasize_cells(d, geometry, [(-1, 3), (2, 3)])
    note(d, "The two derived tables are shortened here with an ellipsis; Tutorial 10.3 gives the full query. "
            "Outlined: the ratio, which rises in each year.", bottom + 8, 40)
    return d


FIGURES = {
    "fig-10-01-join-matching": fig_10_01,
    "fig-10-02-group-by": fig_10_02,
    "fig-10-03-variance-by-group-year": fig_10_03,
    "fig-10-04-fan-out": fig_10_04,
    "fig-10-05-evaluation-order": fig_10_05,
    "fig-10-06-trial-balance": fig_10_06,
    "fig-10-07-conversion-cost-flow": fig_10_07,
    "fig-10-08-paid-per-standard-hour": fig_10_08,
}
