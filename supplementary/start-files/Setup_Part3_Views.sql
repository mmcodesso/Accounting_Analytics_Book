/* Setup_Part3_Views.sql: recreates the view MonthlyLaborEfficiency of Tutorial 11.3
   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)
   Prepared by: companion file; dataset v2026.1
   Run it once on your working copy, then select Write Changes. The Part III case reads the view. */

-- Tutorial 11.3: the measure saved as a view
DROP VIEW IF EXISTS MonthlyLaborEfficiency;
CREATE VIEW MonthlyLaborEfficiency AS
WITH MonthlyOutput AS (
    SELECT strftime('%Y-%m', pc.CompletionDate) AS Month,
        SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit)
            AS StandardHours
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
    WHERE pc.CompletionDate
        <= (SELECT MAX(WorkDate) FROM LaborTimeEntry)
    GROUP BY Month
),
MonthlyHours AS (
    SELECT strftime('%Y-%m', WorkDate) AS Month,
        SUM(CASE LaborType WHEN 'Direct Manufacturing'
            THEN RegularHours + OvertimeHours ELSE 0 END)
            AS DirectHours,
        SUM(CASE LaborType WHEN 'Indirect Manufacturing'
            THEN RegularHours + OvertimeHours ELSE 0 END)
            AS IndirectHours,
        SUM(OvertimeHours) AS OvertimeHours
    FROM LaborTimeEntry
    WHERE LaborType <> 'NonManufacturing'
    GROUP BY Month
),
Monthly AS (
    SELECT o.Month, o.StandardHours, h.DirectHours,
        h.IndirectHours, h.OvertimeHours
    FROM MonthlyOutput AS o
        INNER JOIN MonthlyHours AS h ON h.Month = o.Month
),
Trailing AS (
    SELECT Month,
        ROUND((DirectHours + IndirectHours) / StandardHours, 2)
            AS HoursPerStandardHour,
        ROUND(SUM(DirectHours) OVER w
            / SUM(StandardHours) OVER w, 2) AS TTMDirect,
        ROUND(SUM(IndirectHours) OVER w
            / SUM(StandardHours) OVER w, 2) AS TTMIndirect,
        ROUND(SUM(DirectHours + IndirectHours) OVER w
            / SUM(StandardHours) OVER w, 2) AS TTMTotal,
        ROUND(SUM(OvertimeHours) OVER w
            / SUM(DirectHours + IndirectHours) OVER w, 3)
            AS TTMOvertimeShare,
        COUNT(*) OVER w AS MonthsInWindow
    FROM Monthly
    WINDOW w AS (ORDER BY Month
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
)
SELECT Month, HoursPerStandardHour, TTMDirect, TTMIndirect,
    TTMTotal, TTMOvertimeShare
FROM Trailing
WHERE MonthsInWindow = 12;  -- Result: creates the view MonthlyLaborEfficiency
