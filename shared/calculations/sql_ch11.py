"""Public Chapter 11 tutorial SQL shared by book figures and slides.

These definitions never open a database. Run authoring examples against a
read-only connection; save views only in a separate student working copy.
"""

HEADER = (
    "/* Chapter 11: the plant's hours, month by month\n"
    "   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)\n"
    "   Prepared by: your name, date\n"
    "   Checks: the payroll ties to the ledger; the measure has 36 months */"
)

_PAYROLL = ("FROM PayrollRegisterLine AS prl\n"
            "    INNER JOIN PayrollRegister AS pr\n"
            "        ON pr.PayrollRegisterID = prl.PayrollRegisterID\n"
            "    INNER JOIN PayrollPeriod AS pp\n"
            "        ON pp.PayrollPeriodID = pr.PayrollPeriodID\n"
            "    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID\n")

_LABOR = ("FROM LaborTimeEntry AS lt\n"
          "WHERE lt.LaborType <> 'NonManufacturing'\n"
          "GROUP BY WorkMonth\n"
          "ORDER BY WorkMonth;")

_GAP = ("FROM GLEntry\n"
        "WHERE AccountID = 92 AND FiscalYear BETWEEN 2024 AND 2026\n"
        "    AND SourceDocumentType <> 'WorkOrderClose'\n"
        "GROUP BY FiscalYear, FiscalPeriod\n")

_GAP_INNER = ("    FROM GLEntry\n"
              "    WHERE AccountID = 92 AND FiscalYear BETWEEN 2024 AND 2026\n"
              "        AND SourceDocumentType <> 'WorkOrderClose'\n"
              "    GROUP BY FiscalYear, FiscalPeriod\n")

_CENTERS = (
    "FROM (\n"
    "    SELECT strftime('%Y', op.ActualEndDate) AS EndYear,\n"
    "        wc.WorkCenterName,\n"
    "        ROUND(SUM(op.PlannedLoadHours), 0) AS PlannedHours,\n"
    "        ROUND(SUM(lab.Hours), 0) AS RecordedHours\n"
    "    FROM WorkOrderOperation AS op\n"
    "        INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = op.WorkCenterID\n"
    "        LEFT JOIN (\n"
    "            SELECT WorkOrderOperationID,\n"
    "                SUM(RegularHours + OvertimeHours) AS Hours\n"
    "            FROM LaborTimeEntry\n"
    "            WHERE LaborType = 'Direct Manufacturing'\n"
    "            GROUP BY WorkOrderOperationID\n"
    "        ) AS lab ON lab.WorkOrderOperationID = op.WorkOrderOperationID\n"
    "    WHERE op.ActualEndDate <= (SELECT MAX(WorkDate) FROM LaborTimeEntry)\n"
    "    GROUP BY EndYear, wc.WorkCenterName\n"
    ") AS centers\n"
    "ORDER BY EndYear, CenterRank;")

_OUTPUT_CTE = ("MonthlyOutput AS (\n"
               "    SELECT strftime('%Y-%m', pc.CompletionDate) AS Month,\n"
               "        SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit)\n"
               "            AS StandardHours\n"
               "    FROM ProductionCompletionLine AS pcl\n"
               "        INNER JOIN ProductionCompletion AS pc\n"
               "            ON pc.ProductionCompletionID = pcl.ProductionCompletionID\n"
               "        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID\n"
               "    WHERE pc.CompletionDate\n"
               "        <= (SELECT MAX(WorkDate) FROM LaborTimeEntry)\n"
               "    GROUP BY Month\n"
               ")")

_HOURS_CTE = ("MonthlyHours AS (\n"
              "    SELECT strftime('%Y-%m', WorkDate) AS Month,\n"
              "        SUM(CASE LaborType WHEN 'Direct Manufacturing'\n"
              "            THEN RegularHours + OvertimeHours ELSE 0 END)\n"
              "            AS DirectHours,\n"
              "        SUM(CASE LaborType WHEN 'Indirect Manufacturing'\n"
              "            THEN RegularHours + OvertimeHours ELSE 0 END)\n"
              "            AS IndirectHours,\n"
              "        SUM(OvertimeHours) AS OvertimeHours\n"
              "    FROM LaborTimeEntry\n"
              "    WHERE LaborType <> 'NonManufacturing'\n"
              "    GROUP BY Month\n"
              ")")

_MONTHLY_CTE = ("Monthly AS (\n"
                "    SELECT o.Month, o.StandardHours, h.DirectHours,\n"
                "        h.IndirectHours, h.OvertimeHours\n"
                "    FROM MonthlyOutput AS o\n"
                "        INNER JOIN MonthlyHours AS h ON h.Month = o.Month\n"
                ")")

_TRAILING_CTE = ("Trailing AS (\n"
                 "    SELECT Month,\n"
                 "        ROUND((DirectHours + IndirectHours) / StandardHours, 2)\n"
                 "            AS HoursPerStandardHour,\n"
                 "        ROUND(SUM(DirectHours) OVER w\n"
                 "            / SUM(StandardHours) OVER w, 2) AS TTMDirect,\n"
                 "        ROUND(SUM(IndirectHours) OVER w\n"
                 "            / SUM(StandardHours) OVER w, 2) AS TTMIndirect,\n"
                 "        ROUND(SUM(DirectHours + IndirectHours) OVER w\n"
                 "            / SUM(StandardHours) OVER w, 2) AS TTMTotal,\n"
                 "        ROUND(SUM(OvertimeHours) OVER w\n"
                 "            / SUM(DirectHours + IndirectHours) OVER w, 3)\n"
                 "            AS TTMOvertimeShare,\n"
                 "        COUNT(*) OVER w AS MonthsInWindow\n"
                 "    FROM Monthly\n"
                 "    WINDOW w AS (ORDER BY Month\n"
                 "        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)\n"
                 ")")

_CHAIN = f"WITH {_OUTPUT_CTE},\n{_HOURS_CTE},\n{_MONTHLY_CTE},\n{_TRAILING_CTE}\n"

_FINAL = ("SELECT Month, HoursPerStandardHour, TTMDirect, TTMIndirect,\n"
          "    TTMTotal, TTMOvertimeShare\n"
          "FROM Trailing\n"
          "WHERE MonthsInWindow = 12")

VIEW_SQL = "CREATE VIEW MonthlyLaborEfficiency AS\n" + _CHAIN + _FINAL + ";"

QUERIES = [
    ("payroll_categories", "-- Tutorial 11.1: the manufacturing payroll of 2026 by category",
     "SELECT\n"
     "    CASE\n"
     "        WHEN prl.LineType IN ('Regular Earnings', 'Overtime Earnings')\n"
     "            THEN 'Hourly pay'\n"
     "        WHEN prl.LineType = 'Salary Earnings' THEN 'Salaries'\n"
     "        WHEN prl.LineType IN ('Employer Payroll Tax', 'Employer Benefits')\n"
     "            THEN 'Employer taxes and benefits'\n"
     "        ELSE 'Employee deductions'\n"
     "    END AS Category,\n"
     "    ROUND(SUM(prl.Amount), 2) AS Amount\n"
     + _PAYROLL +
     "WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = 2026\n"
     "GROUP BY Category\n"
     "ORDER BY Amount DESC;"),
    ("payroll_ledger", "-- Tutorial 11.1: the payroll charged to account 1090 in 2026",
     "SELECT ROUND(SUM(Debit), 2) AS PayrollCharged\n"
     "FROM GLEntry\n"
     "WHERE AccountID = 92 AND FiscalYear = 2026\n"
     "    AND SourceDocumentType = 'PayrollSummary';"),
    ("hours_by_month", "-- Tutorial 11.1: manufacturing labor time by month",
     "SELECT strftime('%Y-%m', lt.WorkDate) AS WorkMonth,\n"
     "    COUNT(DISTINCT lt.WorkDate) AS DaysWithTime,\n"
     "    ROUND(SUM(CASE lt.LaborType WHEN 'Direct Manufacturing'\n"
     "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0)\n"
     "        AS DirectHours,\n"
     "    ROUND(SUM(CASE lt.LaborType WHEN 'Indirect Manufacturing'\n"
     "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0)\n"
     "        AS IndirectHours,\n"
     "    ROUND(SUM(lt.OvertimeHours), 0) AS OvertimeHours\n"
     + _LABOR),
    ("end_of_records", "-- Tutorial 11.1: how far the time records fall short of month-end",
     "SELECT MAX(WorkDate) AS LastWorkDate,\n"
     "    date(MAX(WorkDate), 'start of month', '+1 month', '-1 day')\n"
     "        AS MonthEnd,\n"
     "    julianday(date(MAX(WorkDate), 'start of month', '+1 month',\n"
     "        '-1 day')) - julianday(MAX(WorkDate)) AS DaysNotRecorded\n"
     "FROM LaborTimeEntry;"),
    ("overtime_shares", "-- Tutorial 11.1: the overtime share of each kind of labor by month",
     "SELECT strftime('%Y-%m', lt.WorkDate) AS WorkMonth,\n"
     "    ROUND(SUM(CASE lt.LaborType WHEN 'Direct Manufacturing'\n"
     "            THEN lt.OvertimeHours ELSE 0 END)\n"
     "        / SUM(CASE lt.LaborType WHEN 'Direct Manufacturing'\n"
     "            THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 3)\n"
     "        AS DirectOvertimeShare,\n"
     "    ROUND(SUM(CASE lt.LaborType WHEN 'Indirect Manufacturing'\n"
     "            THEN lt.OvertimeHours ELSE 0 END)\n"
     "        / SUM(CASE lt.LaborType WHEN 'Indirect Manufacturing'\n"
     "            THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 3)\n"
     "        AS IndirectOvertimeShare\n"
     + _LABOR),
    ("lead_times", "-- Tutorial 11.1: days from release to completion and to close",
     "SELECT strftime('%Y', ClosedDate) AS CloseYear,\n"
     "    COUNT(*) AS WorkOrders,\n"
     "    ROUND(AVG(julianday(CompletedDate) - julianday(ReleasedDate)), 1)\n"
     "        AS DaysReleaseToComplete,\n"
     "    ROUND(AVG(julianday(ClosedDate) - julianday(CompletedDate)), 1)\n"
     "        AS DaysCompleteToClose\n"
     "FROM WorkOrder\n"
     "WHERE ClosedDate IS NOT NULL\n"
     "GROUP BY CloseYear\n"
     "ORDER BY CloseYear;"),
    ("gap_ytd", "-- Tutorial 11.2: the gap in account 1090 by month and year to date",
     "SELECT FiscalYear, FiscalPeriod,\n"
     "    ROUND(SUM(Debit) - SUM(Credit), 2) AS Gap,\n"
     "    ROUND(SUM(SUM(Debit) - SUM(Credit)) OVER (\n"
     "        PARTITION BY FiscalYear ORDER BY FiscalPeriod), 2)\n"
     "        AS GapYearToDate\n"
     + _GAP +
     "ORDER BY FiscalYear, FiscalPeriod;"),
    ("gap_same_month", "-- Tutorial 11.2: the gap against the same month a year earlier",
     "SELECT FiscalYear, FiscalPeriod,\n"
     "    ROUND(SUM(Debit) - SUM(Credit), 2) AS Gap,\n"
     "    ROUND(LAG(SUM(Debit) - SUM(Credit)) OVER (\n"
     "        PARTITION BY FiscalPeriod ORDER BY FiscalYear), 2)\n"
     "        AS GapSameMonthLastYear\n"
     + _GAP +
     "ORDER BY FiscalYear, FiscalPeriod;"),
    ("gap_rank", "-- Tutorial 11.2: the three largest months of each year",
     "SELECT FiscalYear, FiscalPeriod, Gap, GapRank\n"
     "FROM (\n"
     "    SELECT FiscalYear, FiscalPeriod,\n"
     "        ROUND(SUM(Debit) - SUM(Credit), 2) AS Gap,\n"
     "        RANK() OVER (PARTITION BY FiscalYear\n"
     "            ORDER BY SUM(Debit) - SUM(Credit) DESC) AS GapRank\n"
     + _GAP_INNER +
     ") AS monthly\n"
     "WHERE GapRank <= 3\n"
     "ORDER BY FiscalYear, GapRank;"),
    ("gap_pay_dates", "-- Tutorial 11.2: the three largest months with their pay dates",
     "SELECT FiscalYear, FiscalPeriod, Gap, PayDates, GapRank\n"
     "FROM (\n"
     "    SELECT FiscalYear, FiscalPeriod,\n"
     "        ROUND(SUM(Debit) - SUM(Credit), 2) AS Gap,\n"
     "        COUNT(DISTINCT CASE WHEN SourceDocumentType = 'PayrollSummary'\n"
     "            THEN PostingDate END) AS PayDates,\n"
     "        RANK() OVER (PARTITION BY FiscalYear\n"
     "            ORDER BY SUM(Debit) - SUM(Credit) DESC) AS GapRank\n"
     + _GAP_INNER +
     ") AS monthly\n"
     "WHERE GapRank <= 3\n"
     "ORDER BY FiscalYear, GapRank;"),
    ("pay_dates", "-- Tutorial 11.2: pay dates by month, one column per year",
     "SELECT FiscalPeriod,\n"
     "    COUNT(DISTINCT CASE WHEN FiscalYear = 2024\n"
     "        THEN PostingDate END) AS Pay2024,\n"
     "    COUNT(DISTINCT CASE WHEN FiscalYear = 2025\n"
     "        THEN PostingDate END) AS Pay2025,\n"
     "    COUNT(DISTINCT CASE WHEN FiscalYear = 2026\n"
     "        THEN PostingDate END) AS Pay2026\n"
     "FROM GLEntry\n"
     "WHERE AccountID = 92 AND FiscalYear BETWEEN 2024 AND 2026\n"
     "    AND SourceDocumentType = 'PayrollSummary'\n"
     "GROUP BY FiscalPeriod\n"
     "ORDER BY FiscalPeriod;"),
    ("work_centers", "-- Tutorial 11.2: work centers ranked by hours recorded against plan",
     "SELECT EndYear, WorkCenterName,\n"
     "    RecordedHours - PlannedHours AS ExcessHours,\n"
     "    ROUND(RecordedHours / PlannedHours, 2) AS RecordedPerPlanned,\n"
     "    RANK() OVER (PARTITION BY EndYear\n"
     "        ORDER BY RecordedHours / PlannedHours DESC) AS CenterRank\n"
     + _CENTERS),
    ("work_centers_plant", "-- Tutorial 11.2: the ranking with the plant's excess hours",
     "SELECT EndYear, WorkCenterName,\n"
     "    RecordedHours - PlannedHours AS ExcessHours,\n"
     "    ROUND(RecordedHours / PlannedHours, 2) AS RecordedPerPlanned,\n"
     "    RANK() OVER (PARTITION BY EndYear\n"
     "        ORDER BY RecordedHours / PlannedHours DESC) AS CenterRank,\n"
     "    SUM(RecordedHours - PlannedHours) OVER (PARTITION BY EndYear)\n"
     "        AS PlantExcessHours\n"
     + _CENTERS),
    ("measure_output", "-- Tutorial 11.3: step 1, the standard hours of output by month",
     f"WITH {_OUTPUT_CTE}\n"
     "SELECT * FROM MonthlyOutput\n"
     "ORDER BY Month;"),
    ("measure_hours", "-- Tutorial 11.3: step 2, the labor hours by month",
     f"WITH {_HOURS_CTE}\n"
     "SELECT * FROM MonthlyHours\n"
     "ORDER BY Month;"),
    ("measure_monthly", "-- Tutorial 11.3: step 3, the two steps joined by month",
     f"WITH {_OUTPUT_CTE},\n{_HOURS_CTE},\n{_MONTHLY_CTE}\n"
     "SELECT COUNT(*) AS Months FROM Monthly;"),
    ("measure_trailing", "-- Tutorial 11.3: step 4, the trailing twelve months",
     _CHAIN + _FINAL + "\nORDER BY Month;"),
    ("create_view", "-- Tutorial 11.3: the measure saved as a view",
     "DROP VIEW IF EXISTS MonthlyLaborEfficiency;\n" + VIEW_SQL),
    ("query_view", "-- Tutorial 11.3: the view for fiscal 2026",
     "SELECT *\n"
     "FROM MonthlyLaborEfficiency\n"
     "WHERE Month >= '2026-01'\n"
     "ORDER BY Month;"),
]
