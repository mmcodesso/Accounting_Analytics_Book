"""Chapter 12 figures."""

from __future__ import annotations

import dbbrowser as db
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, GRAY, GRAY_TINT, ROW_H, SMALL, Diagram,
                    esc)

# Audit.sql as the three tutorials build it (see dbbrowser.Script): a header, then each test under a
# two-line comment that names it and states its population and expected result. The tutorial text
# must match these queries exactly.
HEADER = (
    "/* Audit.sql: tests of the records behind the manufacturing variance\n"
    "   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)\n"
    "   Prepared by: your name, date; reviewed by: name, date\n"
    "   Checks: populations tie to the ledger; exceptions listed by test */"
)
_APPROVAL_CTE = (
    "WITH ApprovalExceptions AS (\n"
    "    SELECT 'Self-approved' AS Test, po.PONumber, po.OrderTotal\n"
    "    FROM PurchaseOrder AS po\n"
    "    WHERE po.CreatedByEmployeeID = po.ApprovedByEmployeeID\n"
    "    UNION ALL\n"
    "    SELECT 'Above approver limit', po.PONumber, po.OrderTotal\n"
    "    FROM PurchaseOrder AS po\n"
    "        INNER JOIN Employee AS e\n"
    "            ON e.EmployeeID = po.ApprovedByEmployeeID\n"
    "    WHERE po.OrderTotal > e.MaxApprovalAmount\n"
    "    UNION ALL\n"
    "    SELECT 'Approved after termination', po.PONumber, po.OrderTotal\n"
    "    FROM PurchaseOrder AS po\n"
    "        INNER JOIN Employee AS e\n"
    "            ON e.EmployeeID = po.ApprovedByEmployeeID\n"
    "    WHERE e.TerminationDate IS NOT NULL\n"
    "        AND po.OrderDate > e.TerminationDate\n"
    ")")
_PLANT_DAYS = ("    FROM TimeClockEntry AS tc\n"
               "        INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID\n"
               "        INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID\n"
               "    WHERE cc.CostCenterName = 'Manufacturing'\n"
               "    GROUP BY tc.WorkDate\n")
_EARNINGS = ("FROM PayrollRegisterLine AS prl\n"
             "    INNER JOIN PayrollRegister AS pr\n"
             "        ON pr.PayrollRegisterID = prl.PayrollRegisterID\n"
             "    INNER JOIN LaborTimeEntry AS lt\n"
             "        ON lt.LaborTimeEntryID = prl.LaborTimeEntryID\n"
             "    INNER JOIN Employee AS pe ON pe.EmployeeID = pr.EmployeeID\n"
             "    INNER JOIN Employee AS we ON we.EmployeeID = lt.EmployeeID\n")
_AFTER_END = ("CASE WHEN lt.WorkDate > op.ActualEndDate\n"
              "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END")

QUERIES = [
    # Tutorial 12.1: the ledger
    ("je_population",
     "-- Tutorial 12.1, test L1: journal entries against the ledger\n"
     "-- Population: all journal entries; expected: counts and totals agree",
     "SELECT\n"
     "    (SELECT COUNT(*) FROM JournalEntry) AS Entries,\n"
     "    (SELECT ROUND(SUM(TotalAmount), 2) FROM JournalEntry) AS EntryTotal,\n"
     "    (SELECT COUNT(DISTINCT SourceDocumentID) FROM GLEntry\n"
     "        WHERE SourceDocumentType = 'JournalEntry') AS PostedEntries,\n"
     "    (SELECT ROUND(SUM(Debit), 2) FROM GLEntry\n"
     "        WHERE SourceDocumentType = 'JournalEntry') AS PostedDebits;"),
    ("payroll_population",
     "-- Tutorial 12.1, test L2: manufacturing payroll against the ledger\n"
     "-- Population: Manufacturing registers; expected: no difference",
     "SELECT reg.FiscalYear, reg.RegisterCost, gl.LedgerCost,\n"
     "    ROUND(reg.RegisterCost - gl.LedgerCost, 2) AS Difference\n"
     "FROM (\n"
     "    SELECT pp.FiscalYear,\n"
     "        ROUND(SUM(pr.GrossPay + pr.EmployerPayrollTax\n"
     "            + pr.EmployerBenefits), 2) AS RegisterCost\n"
     "    FROM PayrollRegister AS pr\n"
     "        INNER JOIN PayrollPeriod AS pp\n"
     "            ON pp.PayrollPeriodID = pr.PayrollPeriodID\n"
     "        INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID\n"
     "    WHERE cc.CostCenterName = 'Manufacturing'\n"
     "    GROUP BY pp.FiscalYear\n"
     ") AS reg\n"
     "    INNER JOIN (\n"
     "        SELECT gl.FiscalYear, ROUND(SUM(gl.Debit), 2) AS LedgerCost\n"
     "        FROM GLEntry AS gl\n"
     "            INNER JOIN CostCenter AS cc\n"
     "                ON cc.CostCenterID = gl.CostCenterID\n"
     "        WHERE gl.SourceDocumentType = 'PayrollSummary'\n"
     "            AND cc.CostCenterName = 'Manufacturing'\n"
     "        GROUP BY gl.FiscalYear\n"
     "    ) AS gl ON gl.FiscalYear = reg.FiscalYear\n"
     "ORDER BY reg.FiscalYear;"),
    ("trace",
     "-- Tutorial 12.1, test L3: postings and documents traced both ways\n"
     "-- Population: four document types; expected: no rows",
     "SELECT 'Posting with no payroll payment' AS Test,\n"
     "    gl.GLEntryID AS RecordID, gl.PostingDate AS RecordDate,\n"
     "    gl.Debit + gl.Credit AS Amount\n"
     "FROM GLEntry AS gl\n"
     "    LEFT JOIN PayrollPayment AS pp\n"
     "        ON pp.PayrollPaymentID = gl.SourceDocumentID\n"
     "WHERE gl.SourceDocumentType = 'PayrollPayment'\n"
     "    AND pp.PayrollPaymentID IS NULL\n"
     "UNION ALL\n"
     "SELECT 'Posting with no supplier payment', gl.GLEntryID,\n"
     "    gl.PostingDate, gl.Debit + gl.Credit\n"
     "FROM GLEntry AS gl\n"
     "    LEFT JOIN DisbursementPayment AS dp\n"
     "        ON dp.DisbursementID = gl.SourceDocumentID\n"
     "WHERE gl.SourceDocumentType = 'DisbursementPayment'\n"
     "    AND dp.DisbursementID IS NULL\n"
     "UNION ALL\n"
     "SELECT 'Sales invoice never posted', si.SalesInvoiceID,\n"
     "    si.InvoiceDate, si.GrandTotal\n"
     "FROM SalesInvoice AS si\n"
     "    LEFT JOIN GLEntry AS gl ON gl.SourceDocumentType = 'SalesInvoice'\n"
     "        AND gl.SourceDocumentID = si.SalesInvoiceID\n"
     "WHERE gl.GLEntryID IS NULL\n"
     "UNION ALL\n"
     "SELECT 'Supplier invoice never posted', pi.PurchaseInvoiceID,\n"
     "    pi.InvoiceDate, pi.GrandTotal\n"
     "FROM PurchaseInvoice AS pi\n"
     "    LEFT JOIN GLEntry AS gl ON gl.SourceDocumentType = 'PurchaseInvoice'\n"
     "        AND gl.SourceDocumentID = pi.PurchaseInvoiceID\n"
     "WHERE gl.GLEntryID IS NULL;"),
    ("unpaid_registers",
     "-- Tutorial 12.1, test L4: approved registers with no payment\n"
     "-- Population: all payroll registers; expected: no rows",
     "SELECT pr.PayrollRegisterID, e.JobTitle,\n"
     "    ec.CostCenterName AS EmployeeCenter,\n"
     "    rc.CostCenterName AS RegisterCenter, e.TerminationDate,\n"
     "    pp.PayDate, pr.GrossPay, pr.NetPay, pr.Status\n"
     "FROM PayrollRegister AS pr\n"
     "    INNER JOIN PayrollPeriod AS pp\n"
     "        ON pp.PayrollPeriodID = pr.PayrollPeriodID\n"
     "    INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID\n"
     "    INNER JOIN CostCenter AS ec ON ec.CostCenterID = e.CostCenterID\n"
     "    INNER JOIN CostCenter AS rc ON rc.CostCenterID = pr.CostCenterID\n"
     "    LEFT JOIN PayrollPayment AS pay\n"
     "        ON pay.PayrollRegisterID = pr.PayrollRegisterID\n"
     "WHERE pay.PayrollPaymentID IS NULL;"),
    ("revenue_cutoff",
     "-- Tutorial 12.1, test L5: revenue posted in the year of delivery\n"
     "-- Population: all sales invoices; expected: no rows",
     "WITH Shipped AS (\n"
     "    SELECT sil.SalesInvoiceID, MIN(s.ShipmentDate) AS ShipmentDate,\n"
     "        MAX(s.DeliveryDate) AS DeliveryDate\n"
     "    FROM SalesInvoiceLine AS sil\n"
     "        INNER JOIN ShipmentLine AS sl\n"
     "            ON sl.ShipmentLineID = sil.ShipmentLineID\n"
     "        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID\n"
     "    GROUP BY sil.SalesInvoiceID\n"
     "),\n"
     "Posted AS (\n"
     "    SELECT SourceDocumentID AS SalesInvoiceID,\n"
     "        MIN(PostingDate) AS PostingDate\n"
     "    FROM GLEntry\n"
     "    WHERE SourceDocumentType = 'SalesInvoice'\n"
     "    GROUP BY SourceDocumentID\n"
     "),\n"
     "Classified AS (\n"
     "    SELECT si.SubTotal,\n"
     "        strftime('%Y', sh.DeliveryDate) AS DeliveryYear,\n"
     "        CASE\n"
     "            WHEN strftime('%Y', p.PostingDate)\n"
     "                    <> strftime('%Y', sh.DeliveryDate)\n"
     "                THEN 'Revenue posted in another year'\n"
     "            WHEN si.InvoiceDate < sh.ShipmentDate\n"
     "                THEN 'Invoice dated before shipment'\n"
     "            ELSE 'In the year of delivery'\n"
     "        END AS Finding\n"
     "    FROM SalesInvoice AS si\n"
     "        INNER JOIN Shipped AS sh\n"
     "            ON sh.SalesInvoiceID = si.SalesInvoiceID\n"
     "        INNER JOIN Posted AS p ON p.SalesInvoiceID = si.SalesInvoiceID\n"
     ")\n"
     "SELECT Finding, DeliveryYear, COUNT(*) AS Invoices,\n"
     "    ROUND(SUM(SubTotal), 2) AS SubTotal\n"
     "FROM Classified\n"
     "WHERE Finding <> 'In the year of delivery'\n"
     "GROUP BY Finding, DeliveryYear\n"
     "ORDER BY Finding, DeliveryYear;"),
    ("unbilled_shipments",
     "-- Tutorial 12.1, test L6: shipments never invoiced\n"
     "-- Population: all shipment lines; expected: no rows",
     "SELECT s.ShipmentNumber, s.ShipmentDate, s.DeliveryDate,\n"
     "    ROUND(sl.ExtendedStandardCost, 2) AS StandardCost,\n"
     "    ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2)\n"
     "        AS SalesValue\n"
     "FROM ShipmentLine AS sl\n"
     "    INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID\n"
     "    INNER JOIN SalesOrderLine AS sol\n"
     "        ON sol.SalesOrderLineID = sl.SalesOrderLineID\n"
     "    LEFT JOIN SalesInvoiceLine AS sil\n"
     "        ON sil.ShipmentLineID = sl.ShipmentLineID\n"
     "WHERE sil.SalesInvoiceLineID IS NULL\n"
     "ORDER BY s.ShipmentDate;"),
    ("payroll_cutoff",
     "-- Tutorial 12.1, test L7: pay periods that cross a year-end\n"
     "-- Population: all pay periods; expected: every period processed",
     "SELECT pp.PeriodNumber, pp.PeriodStartDate, pp.PeriodEndDate,\n"
     "    pp.PayDate, pp.Status, COALESCE(reg.Registers, 0) AS Registers,\n"
     "    reg.PayrollCost\n"
     "FROM PayrollPeriod AS pp\n"
     "    LEFT JOIN (\n"
     "        SELECT PayrollPeriodID, COUNT(*) AS Registers,\n"
     "            ROUND(SUM(GrossPay + EmployerPayrollTax\n"
     "                + EmployerBenefits), 2) AS PayrollCost\n"
     "        FROM PayrollRegister\n"
     "        GROUP BY PayrollPeriodID\n"
     "    ) AS reg ON reg.PayrollPeriodID = pp.PayrollPeriodID\n"
     "WHERE strftime('%Y', pp.PeriodStartDate) <> strftime('%Y', pp.PayDate)\n"
     "ORDER BY pp.PeriodStartDate;"),
    ("accrued_payroll",
     "-- Tutorial 12.1, test L8: accrued payroll at the year-end\n"
     "-- Population: account 2030 to 2026-12-31; expected: unpaid wages",
     "SELECT gl.SourceDocumentType, COUNT(*) AS Postings,\n"
     "    ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance\n"
     "FROM GLEntry AS gl\n"
     "    INNER JOIN Account AS a ON a.AccountID = gl.AccountID\n"
     "WHERE a.AccountNumber = 2030 AND gl.PostingDate <= '2026-12-31'\n"
     "GROUP BY gl.SourceDocumentType;"),
    # Tutorial 12.2: purchasing
    ("match_status",
     "-- Tutorial 12.2, test P1: three-way match by purchase order line\n"
     "-- Population: all PO lines; expected: no exception statuses",
     "WITH Received AS (\n"
     "    SELECT POLineID, SUM(QuantityReceived) AS QtyReceived\n"
     "    FROM GoodsReceiptLine\n"
     "    GROUP BY POLineID\n"
     "),\n"
     "Invoiced AS (\n"
     "    SELECT POLineID, SUM(Quantity) AS QtyInvoiced\n"
     "    FROM PurchaseInvoiceLine\n"
     "    WHERE POLineID IS NOT NULL\n"
     "    GROUP BY POLineID\n"
     "),\n"
     "Matched AS (\n"
     "    SELECT pol.POLineID, pol.Quantity AS QtyOrdered,\n"
     "        COALESCE(r.QtyReceived, 0) AS QtyReceived,\n"
     "        COALESCE(i.QtyInvoiced, 0) AS QtyInvoiced\n"
     "    FROM PurchaseOrderLine AS pol\n"
     "        LEFT JOIN Received AS r ON r.POLineID = pol.POLineID\n"
     "        LEFT JOIN Invoiced AS i ON i.POLineID = pol.POLineID\n"
     ")\n"
     "SELECT\n"
     "    CASE\n"
     "        WHEN QtyInvoiced > QtyReceived + 0.0001\n"
     "            THEN 'Exception: invoiced above received'\n"
     "        WHEN QtyReceived > QtyOrdered + 0.0001\n"
     "            THEN 'Exception: received above ordered'\n"
     "        WHEN QtyReceived = 0 THEN 'Not yet received'\n"
     "        WHEN QtyInvoiced < QtyReceived - 0.0001\n"
     "            THEN 'Received, not fully invoiced'\n"
     "        WHEN QtyReceived < QtyOrdered - 0.0001 THEN 'Partly received'\n"
     "        ELSE 'Matched'\n"
     "    END AS MatchStatus,\n"
     "    COUNT(*) AS POLines\n"
     "FROM Matched\n"
     "GROUP BY MatchStatus\n"
     "ORDER BY POLines DESC;"),
    ("price_tolerance",
     "-- Tutorial 12.2, test P2: invoice prices against order prices\n"
     "-- Population: invoice lines with a PO line; expected: none above 3%",
     "SELECT COUNT(*) AS InvoiceLines,\n"
     "    SUM(CASE WHEN ABS(pil.UnitCost - pol.UnitCost) / pol.UnitCost\n"
     "        > 0.03 THEN 1 ELSE 0 END) AS AboveThreePercent,\n"
     "    SUM(CASE WHEN ABS(pil.UnitCost - pol.UnitCost) / pol.UnitCost\n"
     "        > 0.02 THEN 1 ELSE 0 END) AS AboveTwoPercent,\n"
     "    ROUND(MAX((pil.UnitCost - pol.UnitCost) / pol.UnitCost), 4)\n"
     "        AS LargestIncrease,\n"
     "    ROUND(MIN((pil.UnitCost - pol.UnitCost) / pol.UnitCost), 4)\n"
     "        AS LargestDecrease\n"
     "FROM PurchaseInvoiceLine AS pil\n"
     "    INNER JOIN PurchaseOrderLine AS pol ON pol.POLineID = pil.POLineID;"),
    ("grni",
     "-- Tutorial 12.2, test P3: receipts not invoiced against account 2020\n"
     "-- Population: open receipt lines; expected: equal to the ledger",
     "WITH InvoicedByReceipt AS (\n"
     "    SELECT GoodsReceiptLineID, SUM(Quantity) AS QtyInvoiced\n"
     "    FROM PurchaseInvoiceLine\n"
     "    GROUP BY GoodsReceiptLineID\n"
     ")\n"
     "SELECT\n"
     "    (SELECT ROUND(SUM(grl.ExtendedStandardCost\n"
     "        * (1 - COALESCE(ibr.QtyInvoiced, 0) / grl.QuantityReceived)), 2)\n"
     "     FROM GoodsReceiptLine AS grl\n"
     "        LEFT JOIN InvoicedByReceipt AS ibr\n"
     "            ON ibr.GoodsReceiptLineID = grl.GoodsReceiptLineID\n"
     "     WHERE COALESCE(ibr.QtyInvoiced, 0) < grl.QuantityReceived - 0.0001)\n"
     "        AS NotInvoicedValue,\n"
     "    (SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2)\n"
     "     FROM GLEntry AS gl\n"
     "        INNER JOIN Account AS a ON a.AccountID = gl.AccountID\n"
     "     WHERE a.AccountNumber = 2020 AND gl.PostingDate <= '2026-12-31')\n"
     "        AS LedgerBalance;"),
    ("approval_summary",
     "-- Tutorial 12.2, test P4: purchase order approvals\n"
     "-- Population: all purchase orders; expected: no rows",
     _APPROVAL_CTE + "\n"
     "SELECT Test, COUNT(*) AS Orders, ROUND(SUM(OrderTotal), 2) AS OrderValue\n"
     "FROM ApprovalExceptions\n"
     "GROUP BY Test\n"
     "ORDER BY Orders DESC;"),
    ("approval_detail",
     "-- Tutorial 12.2, test P5: the orders behind the approval exceptions\n"
     "-- Population: the orders flagged by test P4",
     _APPROVAL_CTE + ",\n"
     "Flagged AS (\n"
     "    SELECT PONumber, GROUP_CONCAT(Test, '; ') AS Tests\n"
     "    FROM ApprovalExceptions\n"
     "    GROUP BY PONumber\n"
     ")\n"
     "SELECT f.PONumber, po.OrderDate, po.OrderTotal,\n"
     "    c.JobTitle AS CreatedBy, a.JobTitle AS ApprovedBy,\n"
     "    a.MaxApprovalAmount, a.TerminationDate, f.Tests\n"
     "FROM Flagged AS f\n"
     "    INNER JOIN PurchaseOrder AS po ON po.PONumber = f.PONumber\n"
     "    INNER JOIN Employee AS c ON c.EmployeeID = po.CreatedByEmployeeID\n"
     "    INNER JOIN Employee AS a ON a.EmployeeID = po.ApprovedByEmployeeID\n"
     "ORDER BY po.OrderTotal DESC;"),
    ("approvers",
     "-- Tutorial 12.2, test P6: who approves the purchase orders\n"
     "-- Population: all purchase orders; expected: approval shared",
     "SELECT e.EmployeeID, e.JobTitle, COUNT(*) AS OrdersApproved\n"
     "FROM PurchaseOrder AS po\n"
     "    INNER JOIN Employee AS e ON e.EmployeeID = po.ApprovedByEmployeeID\n"
     "GROUP BY e.EmployeeID, e.JobTitle\n"
     "ORDER BY OrdersApproved DESC;"),
    # Tutorial 12.3: the hours and the pay
    ("time_profile",
     "-- Tutorial 12.3, test H1: a profile of the time clock entries\n"
     "-- Population: all clock entries; expected: approved and complete",
     "SELECT COUNT(*) AS Entries,\n"
     "    SUM(CASE WHEN ClockStatus <> 'Approved' THEN 1 ELSE 0 END)\n"
     "        AS NotApproved,\n"
     "    COUNT(*) - COUNT(ClockOutTime) AS NoClockOut,\n"
     "    COUNT(DISTINCT EmployeeID) AS Employees,\n"
     "    MIN(WorkDate) AS FirstWorkDate, MAX(WorkDate) AS LastWorkDate\n"
     "FROM TimeClockEntry;"),
    ("hours_chain",
     "-- Tutorial 12.3, test H2: clocked, recorded, and paid hours\n"
     "-- Population: every pay period; expected: equal in every period",
     "WITH Clocked AS (\n"
     "    SELECT PayrollPeriodID, SUM(RegularHours + OvertimeHours) AS Hours\n"
     "    FROM TimeClockEntry\n"
     "    GROUP BY PayrollPeriodID\n"
     "),\n"
     "Recorded AS (\n"
     "    SELECT PayrollPeriodID, SUM(RegularHours + OvertimeHours) AS Hours\n"
     "    FROM LaborTimeEntry\n"
     "    GROUP BY PayrollPeriodID\n"
     "),\n"
     "Paid AS (\n"
     "    SELECT pr.PayrollPeriodID, SUM(prl.Hours) AS Hours\n"
     "    FROM PayrollRegisterLine AS prl\n"
     "        INNER JOIN PayrollRegister AS pr\n"
     "            ON pr.PayrollRegisterID = prl.PayrollRegisterID\n"
     "    WHERE prl.LineType IN ('Regular Earnings', 'Overtime Earnings')\n"
     "    GROUP BY pr.PayrollPeriodID\n"
     ")\n"
     "SELECT COUNT(*) AS Periods,\n"
     "    SUM(CASE WHEN ABS(c.Hours - r.Hours) > 0.001\n"
     "        OR ABS(r.Hours - p.Hours) > 0.001 THEN 1 ELSE 0 END)\n"
     "        AS PeriodsThatDiffer,\n"
     "    ROUND(SUM(c.Hours), 1) AS Clocked,\n"
     "    ROUND(SUM(r.Hours), 1) AS Recorded,\n"
     "    ROUND(SUM(p.Hours), 1) AS Paid\n"
     "FROM Clocked AS c\n"
     "    INNER JOIN Recorded AS r ON r.PayrollPeriodID = c.PayrollPeriodID\n"
     "    INNER JOIN Paid AS p ON p.PayrollPeriodID = c.PayrollPeriodID;"),
    ("chain_2024",
     "-- Tutorial 12.3, test H3: the manufacturing hours of 2024 by kind\n"
     "-- Population: manufacturing labor time; expected: every period recorded",
     "SELECT pp.PeriodNumber, pp.PeriodStartDate,\n"
     "    ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 0) AS Hours,\n"
     "    ROUND(SUM(CASE lt.LaborType WHEN 'Direct Manufacturing'\n"
     "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0)\n"
     "        AS DirectHours,\n"
     "    ROUND(SUM(CASE lt.LaborType WHEN 'Indirect Manufacturing'\n"
     "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0)\n"
     "        AS IndirectHours\n"
     "FROM LaborTimeEntry AS lt\n"
     "    INNER JOIN PayrollPeriod AS pp\n"
     "        ON pp.PayrollPeriodID = lt.PayrollPeriodID\n"
     "WHERE lt.LaborType <> 'NonManufacturing' AND pp.FiscalYear = 2024\n"
     "GROUP BY pp.PayrollPeriodID, pp.PeriodNumber, pp.PeriodStartDate\n"
     "ORDER BY pp.PeriodStartDate;"),
    ("chain_exceptions",
     "-- Tutorial 12.3, test H4: time paid to another person or unapproved\n"
     "-- Population: all earnings lines; expected: no rows",
     "SELECT 'Time paid to another employee' AS Test,\n"
     "    pr.EmployeeID AS PaidID, pe.JobTitle AS PaidTitle,\n"
     "    lt.EmployeeID AS WorkedID, we.JobTitle AS WorkedTitle,\n"
     "    we.TerminationDate AS WorkerLeft, prl.Amount\n"
     + _EARNINGS +
     "WHERE lt.EmployeeID <> pr.EmployeeID\n"
     "UNION ALL\n"
     "SELECT 'Time paid on an unapproved clock entry',\n"
     "    pr.EmployeeID, pe.JobTitle, lt.EmployeeID, we.JobTitle,\n"
     "    we.TerminationDate, prl.Amount\n"
     + _EARNINGS +
     "    INNER JOIN TimeClockEntry AS tc\n"
     "        ON tc.TimeClockEntryID = lt.TimeClockEntryID\n"
     "WHERE tc.ClockStatus <> 'Approved';"),
    ("pay_expectation",
     "-- Tutorial 12.3, test H5: earnings paid against hours and pay rates\n"
     "-- Population: hourly earnings lines; expected: within a cent a line",
     "WITH Expected AS (\n"
     "    SELECT pp.FiscalYear, prl.Amount,\n"
     "        prl.Hours * e.BaseHourlyRate\n"
     "            * CASE prl.LineType WHEN 'Overtime Earnings'\n"
     "                THEN 1.5 ELSE 1 END AS ExpectedAmount\n"
     "    FROM PayrollRegisterLine AS prl\n"
     "        INNER JOIN PayrollRegister AS pr\n"
     "            ON pr.PayrollRegisterID = prl.PayrollRegisterID\n"
     "        INNER JOIN PayrollPeriod AS pp\n"
     "            ON pp.PayrollPeriodID = pr.PayrollPeriodID\n"
     "        INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID\n"
     "    WHERE prl.LineType IN ('Regular Earnings', 'Overtime Earnings')\n"
     ")\n"
     "SELECT FiscalYear, ROUND(SUM(Amount), 2) AS EarningsPaid,\n"
     "    ROUND(SUM(ExpectedAmount), 2) AS Expected,\n"
     "    ROUND(SUM(Amount) - SUM(ExpectedAmount), 2) AS Difference,\n"
     "    SUM(CASE WHEN ABS(Amount - ExpectedAmount) > 0.01 THEN 1 ELSE 0 END)\n"
     "        AS LinesAboveOneCent\n"
     "FROM Expected\n"
     "GROUP BY FiscalYear\n"
     "ORDER BY FiscalYear;"),
    ("overtime_length",
     "-- Tutorial 12.3, test H6: overtime and its approvals\n"
     "-- Population: clock entries with overtime; expected: approved",
     "SELECT\n"
     "    CASE WHEN OvertimeHours <= 0.5 THEN 'Half an hour or less'\n"
     "        ELSE 'More than half an hour' END AS OvertimeLength,\n"
     "    COUNT(*) AS Entries,\n"
     "    SUM(CASE WHEN OvertimeApprovalID IS NULL THEN 1 ELSE 0 END)\n"
     "        AS WithoutApproval,\n"
     "    ROUND(SUM(OvertimeHours), 1) AS OvertimeHours\n"
     "FROM TimeClockEntry\n"
     "WHERE OvertimeHours > 0\n"
     "GROUP BY OvertimeLength;"),
    ("overtime_unapproved",
     "-- Tutorial 12.3, test H7: long overtime without an approval\n"
     "-- Population: overtime above half an hour; expected: no rows",
     "SELECT e.JobTitle, e.TerminationDate, tc.WorkDate,\n"
     "    tc.OvertimeHours, tc.ClockOutTime, tc.ClockStatus,\n"
     "    oa.OvertimeApprovalID AS UnlinkedApproval,\n"
     "    ap.JobTitle AS ApprovedBy\n"
     "FROM TimeClockEntry AS tc\n"
     "    INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID\n"
     "    LEFT JOIN OvertimeApproval AS oa\n"
     "        ON oa.EmployeeID = tc.EmployeeID AND oa.WorkDate = tc.WorkDate\n"
     "    LEFT JOIN Employee AS ap ON ap.EmployeeID = oa.ApprovedByEmployeeID\n"
     "WHERE tc.OvertimeHours > 0.5 AND tc.OvertimeApprovalID IS NULL;"),
    ("surge_days",
     "-- Tutorial 12.3, test H8: days when everyone clocked the same hours\n"
     "-- Population: manufacturing clock entries; expected: no such days",
     "WITH PlantDays AS (\n"
     "    SELECT tc.WorkDate, COUNT(*) AS Employees,\n"
     "        COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours)\n"
     "            AS HourPatterns,\n"
     "        SUM(tc.OvertimeHours) AS OvertimeHours\n"
     + _PLANT_DAYS +
     ")\n"
     "SELECT strftime('%Y', WorkDate) AS WorkYear,\n"
     "    SUM(CASE WHEN HourPatterns = 1 AND Employees > 1\n"
     "        THEN 1 ELSE 0 END) AS SurgeDays,\n"
     "    MAX(CASE WHEN HourPatterns = 1 AND Employees > 1\n"
     "        THEN Employees END) AS EmployeesPerDay,\n"
     "    ROUND(SUM(CASE WHEN HourPatterns = 1 AND Employees > 1\n"
     "        THEN OvertimeHours ELSE 0 END), 0) AS SurgeOvertime,\n"
     "    ROUND(SUM(CASE WHEN HourPatterns = 1 AND Employees > 1\n"
     "        THEN OvertimeHours ELSE 0 END) / SUM(OvertimeHours), 3)\n"
     "        AS SurgeShare\n"
     "FROM PlantDays\n"
     "GROUP BY WorkYear\n"
     "ORDER BY WorkYear;"),
    ("late_by_year",
     "-- Tutorial 12.3, test H9: direct time recorded after its operation\n"
     "-- Population: direct labor time; expected: a small share",
     "WITH SurgeDays AS (\n"
     "    SELECT tc.WorkDate\n"
     + _PLANT_DAYS +
     "    HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1\n"
     "        AND COUNT(*) > 1\n"
     ")\n"
     "SELECT strftime('%Y', lt.WorkDate) AS WorkYear,\n"
     "    ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 0) AS DirectHours,\n"
     f"    ROUND(SUM({_AFTER_END}), 0)\n"
     "        AS AfterEnd,\n"
     f"    ROUND(SUM({_AFTER_END})\n"
     "        / SUM(lt.RegularHours + lt.OvertimeHours), 3) AS ShareAfterEnd,\n"
     "    ROUND(SUM(CASE WHEN lt.WorkDate > op.ActualEndDate\n"
     "        AND sd.WorkDate IS NOT NULL\n"
     "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0)\n"
     "        AS AfterEndOnSurgeDays\n"
     "FROM LaborTimeEntry AS lt\n"
     "    INNER JOIN WorkOrderOperation AS op\n"
     "        ON op.WorkOrderOperationID = lt.WorkOrderOperationID\n"
     "    LEFT JOIN SurgeDays AS sd ON sd.WorkDate = lt.WorkDate\n"
     "WHERE lt.LaborType = 'Direct Manufacturing'\n"
     "GROUP BY WorkYear\n"
     "ORDER BY WorkYear;"),
    ("late_by_center",
     "-- Tutorial 12.3, test H10: late direct time by work center, 2026\n"
     "-- Population: direct labor time of 2026; expected: a small share",
     "SELECT wc.WorkCenterName,\n"
     "    ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 0) AS DirectHours,\n"
     f"    ROUND(SUM({_AFTER_END})\n"
     "        / SUM(lt.RegularHours + lt.OvertimeHours), 3) AS ShareAfterEnd\n"
     "FROM LaborTimeEntry AS lt\n"
     "    INNER JOIN WorkOrderOperation AS op\n"
     "        ON op.WorkOrderOperationID = lt.WorkOrderOperationID\n"
     "    INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = op.WorkCenterID\n"
     "WHERE lt.LaborType = 'Direct Manufacturing'\n"
     "    AND lt.WorkDate BETWEEN '2026-01-01' AND '2026-12-31'\n"
     "GROUP BY wc.WorkCenterID, wc.WorkCenterName\n"
     "ORDER BY ShareAfterEnd DESC;"),
]
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
