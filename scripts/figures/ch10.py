"""Chapter 10 figures."""

from __future__ import annotations

import dbbrowser as db
import excel as xl
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK,
                    ROW_H, RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc, money)

SAMPLE_WORK_ORDERS = (13014, 13015, 13016, 13017)   # three closed, one released
FAN_OUT_INVOICE = "SI-2026-019134"                   # a fiscal 2026 invoice with three lines

# Chapter10.sql as the three tutorials build it (see dbbrowser.Script). The tutorial text must
# match these queries exactly.
HEADER = (
    "/* Chapter 10: manufacturing variance, joined and summarized\n"
    "   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)\n"
    "   Prepared by: your name, date\n"
    "   Checks: 2026 closes equal the ledger; the trial balance nets to zero */"
)
_JOIN_ITEMS = ("FROM WorkOrderClose AS woc\n"
               "    INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = woc.WorkOrderID\n"
               "    INNER JOIN Item AS i ON i.ItemID = wo.ItemID\n")
_TB_INNER = ("    SELECT gl.AccountID,\n"
             "        ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Balance\n"
             "    FROM GLEntry AS gl\n"
             "    WHERE gl.PostingDate <= '2026-12-31'\n"
             "        AND gl.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297')\n"
             "    GROUP BY gl.AccountID\n")
_OUTPUT = ("FROM ProductionCompletionLine AS pcl\n"
           "    INNER JOIN ProductionCompletion AS pc\n"
           "        ON pc.ProductionCompletionID = pcl.ProductionCompletionID\n"
           "    INNER JOIN Item AS i ON i.ItemID = pcl.ItemID\n")
_PAYROLL = ("FROM PayrollRegister AS pr\n"
            "    INNER JOIN PayrollPeriod AS pp\n"
            "        ON pp.PayrollPeriodID = pr.PayrollPeriodID\n"
            "    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID\n")
QUERIES = [
    ("closes_to_work_orders", "-- Tutorial 10.1: the closes joined to their work orders",
     "SELECT woc.WorkOrderCloseID, woc.CloseDate, wo.WorkOrderNumber,\n"
     "    wo.ItemID, woc.TotalVarianceAmount\n"
     "FROM WorkOrderClose AS woc\n"
     "    INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = woc.WorkOrderID;"),
    ("close_count", "-- Tutorial 10.1: the number of closes, to test the join",
     "SELECT COUNT(*) AS Closes\n"
     "FROM WorkOrderClose;"),
    ("closes_with_items", "-- Tutorial 10.1: the closes with their items",
     "SELECT woc.WorkOrderCloseID, woc.CloseDate, i.ItemCode,\n"
     "    i.ItemName, i.ItemGroup, woc.TotalVarianceAmount\n"
     + _JOIN_ITEMS.rstrip("\n") + ";"),
    ("variance_by_group", "-- Tutorial 10.1: the variance of fiscal 2026 by item group",
     "SELECT i.ItemGroup, COUNT(*) AS Closes,\n"
     "    ROUND(SUM(woc.TotalVarianceAmount), 2) AS TotalVariance\n"
     + _JOIN_ITEMS +
     "WHERE woc.CloseDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
     "GROUP BY i.ItemGroup\n"
     "ORDER BY TotalVariance DESC;"),
    ("ledger_variance", "-- Tutorial 10.1: the same variance in the ledger",
     "SELECT ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS LedgerVariance\n"
     "FROM GLEntry AS gl\n"
     "WHERE gl.AccountID = 93 AND gl.FiscalYear = 2026\n"
     "    AND gl.SourceDocumentType = 'WorkOrderClose';"),
    ("variance_by_group_year", "-- Tutorial 10.1: the variance by item group and year",
     "SELECT i.ItemGroup, SUBSTR(woc.CloseDate, 1, 4) AS CloseYear,\n"
     "    COUNT(*) AS Closes,\n"
     "    ROUND(SUM(woc.TotalVarianceAmount), 2) AS TotalVariance,\n"
     "    ROUND(SUM(woc.OverheadVarianceAmount), 2) AS OverheadVariance\n"
     + _JOIN_ITEMS +
     "GROUP BY i.ItemGroup, CloseYear\n"
     "ORDER BY i.ItemGroup, CloseYear;"),
    ("items_above_threshold", "-- Tutorial 10.1: items with more than $50,000 of variance in 2026",
     "SELECT i.ItemID, i.ItemCode, i.ItemName, COUNT(*) AS Closes,\n"
     "    ROUND(SUM(woc.TotalVarianceAmount), 2) AS TotalVariance\n"
     + _JOIN_ITEMS +
     "WHERE woc.CloseDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
     "GROUP BY i.ItemID, i.ItemCode, i.ItemName\n"
     "HAVING SUM(woc.TotalVarianceAmount) > 50000\n"
     "ORDER BY TotalVariance DESC;"),
    ("every_item", "-- Tutorial 10.1: every manufactured item with its closes of 2026",
     "SELECT i.ItemCode, i.ItemName, i.LifecycleStatus,\n"
     "    COUNT(woc.WorkOrderCloseID) AS Closes2026\n"
     "FROM Item AS i\n"
     "    LEFT JOIN WorkOrder AS wo ON wo.ItemID = i.ItemID\n"
     "    LEFT JOIN WorkOrderClose AS woc ON woc.WorkOrderID = wo.WorkOrderID\n"
     "        AND woc.CloseDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
     "WHERE i.SupplyMode = 'Manufactured'\n"
     "GROUP BY i.ItemID, i.ItemCode, i.ItemName, i.LifecycleStatus\n"
     "ORDER BY Closes2026, i.ItemCode;"),
    ("side_by_side", "-- Tutorial 10.2: the closes and the ledger side by side",
     "SELECT\n"
     "    (SELECT ROUND(SUM(TotalVarianceAmount), 2)\n"
     "     FROM WorkOrderClose\n"
     "     WHERE CloseDate BETWEEN '2026-01-01' AND '2026-12-31') AS Closes,\n"
     "    (SELECT ROUND(SUM(Debit) - SUM(Credit), 2)\n"
     "     FROM GLEntry\n"
     "     WHERE AccountID = 93 AND FiscalYear = 2026\n"
     "         AND SourceDocumentType = 'WorkOrderClose') AS Ledger;"),
    ("trial_balance", "-- Tutorial 10.2: the pre-closing trial balance of fiscal 2026",
     "SELECT a.AccountNumber, a.AccountName, a.AccountType,\n"
     "    ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Balance\n"
     "FROM GLEntry AS gl\n"
     "    INNER JOIN Account AS a ON a.AccountID = gl.AccountID\n"
     "WHERE gl.PostingDate <= '2026-12-31'\n"
     "    AND gl.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297')\n"
     "GROUP BY a.AccountID, a.AccountNumber, a.AccountName, a.AccountType\n"
     "ORDER BY a.AccountNumber;"),
    ("net_balance", "-- Tutorial 10.2: the net of all the balances",
     "SELECT COUNT(*) AS Accounts, ROUND(SUM(tb.Balance), 2) AS NetBalance\n"
     "FROM (\n" + _TB_INNER + ") AS tb;"),
    ("debit_balances", "-- Tutorial 10.2: the total of the debit balances",
     "SELECT COUNT(*) AS DebitAccounts,\n"
     "    ROUND(SUM(tb.Balance), 2) AS DebitBalances\n"
     "FROM (\n" + _TB_INNER + ") AS tb\n"
     "WHERE tb.Balance > 0;"),
    ("account_1090", "-- Tutorial 10.2: account 1090 by year and source",
     "SELECT gl.FiscalYear, gl.SourceDocumentType,\n"
     "    ROUND(SUM(gl.Debit), 2) AS Debits,\n"
     "    ROUND(SUM(gl.Credit), 2) AS Credits\n"
     "FROM GLEntry AS gl\n"
     "WHERE gl.AccountID = 92 AND gl.FiscalYear BETWEEN 2024 AND 2026\n"
     "GROUP BY gl.FiscalYear, gl.SourceDocumentType\n"
     "ORDER BY gl.FiscalYear, gl.SourceDocumentType;"),
    ("journal_entries", "-- Tutorial 10.2: the journal entries posted to account 1090",
     "SELECT gl.FiscalYear, je.EntryType,\n"
     "    ROUND(SUM(gl.Debit), 2) AS Debits\n"
     "FROM GLEntry AS gl\n"
     "    INNER JOIN JournalEntry AS je\n"
     "        ON gl.SourceDocumentType = 'JournalEntry'\n"
     "        AND je.JournalEntryID = gl.SourceDocumentID\n"
     "WHERE gl.AccountID = 92\n"
     "GROUP BY gl.FiscalYear, je.EntryType\n"
     "ORDER BY gl.FiscalYear, je.EntryType;"),
    ("output", "-- Tutorial 10.3: the output and its standard hours by year",
     "SELECT SUBSTR(pc.CompletionDate, 1, 4) AS CompletionYear,\n"
     "    ROUND(SUM(pcl.QuantityCompleted), 0) AS UnitsCompleted,\n"
     "    ROUND(SUM(pcl.QuantityCompleted\n"
     "        * i.StandardLaborHoursPerUnit), 0) AS StandardHours\n"
     + _OUTPUT +
     "GROUP BY CompletionYear\n"
     "ORDER BY CompletionYear;"),
    ("payroll_hours", "-- Tutorial 10.3: the hours and pay of the manufacturing payroll",
     "SELECT pp.FiscalYear, prl.LineType,\n"
     "    ROUND(SUM(prl.Hours), 0) AS Hours,\n"
     "    ROUND(SUM(prl.Amount), 2) AS Amount\n"
     "FROM PayrollRegisterLine AS prl\n"
     "    INNER JOIN PayrollRegister AS pr\n"
     "        ON pr.PayrollRegisterID = prl.PayrollRegisterID\n"
     "    INNER JOIN PayrollPeriod AS pp\n"
     "        ON pp.PayrollPeriodID = pr.PayrollPeriodID\n"
     "    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID\n"
     "WHERE cc.CostCenterName = 'Manufacturing'\n"
     "    AND prl.LineType IN ('Regular Earnings', 'Overtime Earnings')\n"
     "    AND pp.FiscalYear BETWEEN 2024 AND 2026\n"
     "GROUP BY pp.FiscalYear, prl.LineType\n"
     "ORDER BY pp.FiscalYear, prl.LineType;"),
    ("people", "-- Tutorial 10.3: the registers and the people they paid",
     "SELECT pp.FiscalYear, COUNT(*) AS Registers,\n"
     "    COUNT(DISTINCT pr.EmployeeID) AS Employees\n"
     + _PAYROLL +
     "WHERE cc.CostCenterName = 'Manufacturing'\n"
     "    AND pp.FiscalYear BETWEEN 2024 AND 2026\n"
     "GROUP BY pp.FiscalYear;"),
    ("record_ends", "-- Tutorial 10.3: the last day of the time records and of the output",
     "SELECT (SELECT MAX(WorkDate) FROM LaborTimeEntry) AS LastWorkDate,\n"
     "    (SELECT MAX(CompletionDate) FROM ProductionCompletion)\n"
     "        AS LastCompletionDate;"),
    ("last_periods", "-- Tutorial 10.3: the pay periods at the end of the data",
     "SELECT PeriodNumber, PeriodStartDate, PeriodEndDate, PayDate, Status\n"
     "FROM PayrollPeriod\n"
     "WHERE PeriodEndDate >= '2026-12-01'\n"
     "ORDER BY PeriodStartDate;"),
    ("hours_by_type", "-- Tutorial 10.3: hours per standard hour, by labor type",
     "SELECT h.WorkYear, h.LaborType, h.Hours, o.StandardHours,\n"
     "    ROUND(h.Hours / o.StandardHours, 2) AS HoursPerStandardHour\n"
     "FROM (\n"
     "    SELECT SUBSTR(lt.WorkDate, 1, 4) AS WorkYear, lt.LaborType,\n"
     "        ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 0) AS Hours\n"
     "    FROM LaborTimeEntry AS lt\n"
     "    WHERE lt.LaborType <> 'NonManufacturing'\n"
     "    GROUP BY WorkYear, lt.LaborType\n"
     ") AS h\n"
     "    INNER JOIN (\n"
     "        SELECT SUBSTR(pc.CompletionDate, 1, 4) AS WorkYear,\n"
     "            ROUND(SUM(pcl.QuantityCompleted\n"
     "                * i.StandardLaborHoursPerUnit), 0) AS StandardHours\n"
     "        FROM ProductionCompletionLine AS pcl\n"
     "            INNER JOIN ProductionCompletion AS pc\n"
     "                ON pc.ProductionCompletionID = pcl.ProductionCompletionID\n"
     "            INNER JOIN Item AS i ON i.ItemID = pcl.ItemID\n"
     "        WHERE pc.CompletionDate\n"
     "            <= (SELECT MAX(WorkDate) FROM LaborTimeEntry)\n"
     "        GROUP BY WorkYear\n"
     "    ) AS o ON o.WorkYear = h.WorkYear\n"
     "ORDER BY h.WorkYear, h.LaborType;"),
    ("no_operation", "-- Tutorial 10.3: labor time with no work order operation",
     "SELECT lt.LaborType, COUNT(*) AS Entries,\n"
     "    ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 0) AS Hours\n"
     "FROM LaborTimeEntry AS lt\n"
     "    LEFT JOIN WorkOrderOperation AS op\n"
     "        ON op.WorkOrderOperationID = lt.WorkOrderOperationID\n"
     "WHERE op.WorkOrderOperationID IS NULL\n"
     "GROUP BY lt.LaborType\n"
     "ORDER BY lt.LaborType;"),
]
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
    _, sql, _ = CHAPTER10.location("variance_by_group_year")
    headers, rows = db.run(sql)
    furniture = [r for r in rows if r[0] == "Furniture"]
    textiles = [r for r in rows if r[0] == "Textiles"]
    assert [r[1] for r in furniture] == ["2024", "2025", "2026"]
    assert furniture[0][3] < furniture[1][3] < furniture[2][3], "Furniture variance rises each year"
    assert furniture[0][2] > furniture[1][2] > furniture[2][2], "while its closes fall"
    assert textiles[1][3] > textiles[2][3], "Textiles fell back in 2026"
    assert furniture[2][3] > 0.66 * sum(r[3] for r in rows if r[1] == "2026")
    out = CHAPTER10.mock(d, "variance_by_group_year", [130, 110, 90, 170, 170])
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
    out = CHAPTER10.mock(d, "trial_balance", [130, 340, 110, 150], shown=slice(0, 12))
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
    note(d, f"Amounts are the postings of fiscal 2026. The debits exceed the credits by {money(remainder)}, "
            "the year's net change in the account.", 320, 40)
    return d


def fig_10_08() -> Diagram:
    d = Diagram("Hours per Standard Hour by Labor Type and Year")
    _, sql, _ = CHAPTER10.location("hours_by_type")
    headers, rows = db.run(sql)
    direct = [r[4] for r in rows if r[1] == "Direct Manufacturing"]
    indirect = [r[4] for r in rows if r[1] == "Indirect Manufacturing"]
    assert [r[0] for r in rows] == ["2024", "2024", "2025", "2025", "2026", "2026"], rows
    last_work, last_completion = one(CHAPTER10.location("record_ends")[1])
    assert last_work == "2026-12-11" and last_completion == "2026-12-31", (last_work, last_completion)
    open_periods = [r[0] for r in db.run(CHAPTER10.location("last_periods")[1])[1] if r[4] == "Open"]
    assert open_periods == ["PP-2026-078", "PP-2026-079"], open_periods
    assert all(0.8 < x < 1.0 for x in direct), direct            # direct time within standard
    assert indirect == sorted(indirect) and indirect[2] > 1.5 * indirect[0], indirect
    totals = [round(a + b, 2) for a, b in zip(direct, indirect)]
    assert totals == sorted(totals) and 1.4 < totals[2] < 1.55, totals
    out = CHAPTER10.mock(d, "hours_by_type", [110, 220, 120, 150, 210])
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
    "fig-10-08-hours-per-standard-hour": fig_10_08,
}
