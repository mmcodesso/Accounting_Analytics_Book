"""Public Chapter 10 tutorial SQL shared by book figures and slides.

These definitions never open a database. Run authoring examples against a
read-only connection; save views only in a separate student working copy.
"""

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
    ("variance_parts", "-- Tutorial 10.2: the labor and overhead parts by year",
     "SELECT SUBSTR(CloseDate, 1, 4) AS CloseYear,\n"
     "    ROUND(SUM(DirectLaborVarianceAmount), 2) AS LaborVariance,\n"
     "    ROUND(SUM(OverheadVarianceAmount), 2) AS OverheadVariance,\n"
     "    ROUND(SUM(ConversionVarianceAmount), 2) AS ConversionVariance\n"
     "FROM WorkOrderClose\n"
     "GROUP BY CloseYear\n"
     "ORDER BY CloseYear;"),
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
    ("profile_time", "-- Tutorial 10.3: a profile of the labor time entries",
     "SELECT COUNT(*) AS Entries,\n"
     "    COUNT(WorkOrderOperationID) AS WithOperation,\n"
     "    COUNT(DISTINCT EmployeeID) AS Employees,\n"
     "    MIN(WorkDate) AS FirstWorkDate, MAX(WorkDate) AS LastWorkDate\n"
     "FROM LaborTimeEntry;"),
    ("profile_output", "-- Tutorial 10.3: a profile of the production completions",
     "SELECT COUNT(*) AS Completions,\n"
     "    MIN(CompletionDate) AS FirstCompletionDate,\n"
     "    MAX(CompletionDate) AS LastCompletionDate\n"
     "FROM ProductionCompletion;"),
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
