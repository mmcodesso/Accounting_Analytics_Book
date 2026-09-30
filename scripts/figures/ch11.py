"""Chapter 11 figures."""

from __future__ import annotations

import dbbrowser as db
import excel as xl
from data import connection, q
from drawio import (AMBER, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK, ROW_H,
                    SMALL, Diagram)

# Chapter11.sql as the three tutorials build it (see dbbrowser.Script). The tutorial text must
# match these queries exactly.
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
    ("work_centers", "-- Tutorial 11.2: work centers ranked by hours recorded against plan",
     "SELECT EndYear, WorkCenterName,\n"
     "    RecordedHours - PlannedHours AS ExcessHours,\n"
     "    ROUND(RecordedHours / PlannedHours, 2) AS RecordedPerPlanned,\n"
     "    RANK() OVER (PARTITION BY EndYear\n"
     "        ORDER BY RecordedHours / PlannedHours DESC) AS CenterRank,\n"
     "    SUM(RecordedHours - PlannedHours) OVER (PARTITION BY EndYear)\n"
     "        AS PlantExcessHours\n"
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
     "ORDER BY EndYear, CenterRank;"),
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
CHAPTER11 = db.Script(HEADER, QUERIES, "Chapter11.sql")
VIEW_COLUMNS = ["Month", "HoursPerStandardHour", "TTMDirect", "TTMIndirect", "TTMTotal",
                "TTMOvertimeShare"]

# The conditional-aggregation example of the chapter text (chapter.qmd), shown in fig-11-01.
PIVOT_SQL = ("SELECT FiscalYear,\n"
             "    ROUND(SUM(CASE WHEN SourceDocumentType = 'PayrollSummary'\n"
             "        THEN Debit ELSE 0 END), 2) AS Payroll,\n"
             "    ROUND(SUM(CASE WHEN SourceDocumentType = 'JournalEntry'\n"
             "        THEN Debit ELSE 0 END), 2) AS JournalEntries,\n"
             "    ROUND(SUM(CASE WHEN SourceDocumentType = 'ProductionCompletion'\n"
             "        THEN Credit ELSE 0 END), 2) AS Completions\n"
             "FROM GLEntry\n"
             "WHERE AccountID = 92 AND FiscalYear BETWEEN 2024 AND 2026\n"
             "GROUP BY FiscalYear\n"
             "ORDER BY FiscalYear;")


def sql(key: str) -> str:
    return CHAPTER11.location(key)[1]


def create_temp_view() -> None:
    """The tutorial's view, created as a TEMP view on the read-only connection, so that the
    mocks can query it as the tutorial does."""
    con = connection()
    con.execute("DROP VIEW IF EXISTS temp.MonthlyLaborEfficiency")
    con.execute(VIEW_SQL.replace("CREATE VIEW", "CREATE TEMP VIEW", 1).rstrip(";"))


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


def num(value: float, places: int = 2) -> str:
    return f"{value:,.{places}f}"


def fig_11_01() -> Diagram:
    d = Diagram("Conditional Aggregation Turns Rows into Columns")
    by_source = q("SELECT SourceDocumentType, SUM(Debit), SUM(Credit) FROM GLEntry "
                  "WHERE AccountID = 92 AND FiscalYear = 2026 GROUP BY SourceDocumentType "
                  "ORDER BY SourceDocumentType")
    assert [r[0] for r in by_source] == ["JournalEntry", "PayrollSummary", "ProductionCompletion",
                                         "WorkOrderClose"], by_source
    _, rows = db.run(PIVOT_SQL)
    year, payroll, journals, completions = rows[-1]
    assert year == 2026 and len(rows) == 3
    src = {r[0]: r for r in by_source}
    assert round(src["PayrollSummary"][1], 2) == payroll
    assert round(src["JournalEntry"][1], 2) == journals
    assert round(src["ProductionCompletion"][2], 2) == completions
    d.text("<b>Account 1090 in fiscal 2026, one row per source</b>", 0, 0, 440, 20, size=SMALL)
    left = [(s, num(dr), num(cr)) for s, dr, cr in by_source]
    d.grid(0, 24, ["SourceDocumentType", "Debit", "Credit"], [190, 120, 120], left)
    d.text("<b>The same postings, one column per source</b>", 470, 0, 390, 20, size=SMALL)
    d.grid(470, 24, ["FiscalYear", "Payroll", "JournalEntries", "Completions"], [80, 100, 110, 100],
           [(str(year), num(payroll), num(journals), num(completions))])
    # Numbered badges key each source cell to the column that receives it.
    cells = {"JournalEntry": (1, 190), "PayrollSummary": (2, 190), "ProductionCompletion": (3, 310)}
    centers = {"PayrollSummary": 600, "JournalEntry": 705, "ProductionCompletion": 810}
    for k, name in enumerate(["PayrollSummary", "JournalEntry", "ProductionCompletion"], 1):
        row, cx = cells[name]
        d.marker(str(k), cx + 4, 24 + row * ROW_H + 2, size=20)
        d.marker(str(k), centers[name] - 10, 24 + 2 * ROW_H + 6, size=20)   # under the column
    y = 24 + 5 * ROW_H + 18
    formulas = [
        ("1", "Payroll", "SUM(CASE WHEN SourceDocumentType = 'PayrollSummary' THEN Debit ELSE 0 END)"),
        ("2", "JournalEntries", "SUM(CASE WHEN SourceDocumentType = 'JournalEntry' THEN Debit ELSE 0 END)"),
        ("3", "Completions",
         "SUM(CASE WHEN SourceDocumentType = 'ProductionCompletion' THEN Credit ELSE 0 END)"),
    ]
    for i, (k, alias, expr) in enumerate(formulas):
        d.marker(k, 0, y + i * 26, size=20)
        d.text(f"<b>{alias}</b> = {expr}", 28, y + i * 26, 832, 22, size=SMALL, color=INK)
    y += 3 * 26 + 6
    note(d, "Each CASE passes the amount of one source and zero for every other row, so each sum "
            "collects one source. The WorkOrderClose rows meet no condition and add zero to every column.",
         y, 40)
    return d


def fig_11_02() -> Diagram:
    d = Diagram("Overtime Shares by Kind of Labor and Month")
    rows = db.run(sql("overtime_shares"))[1]
    assert len(rows) == 36
    first_half_2024 = [r[1] for r in rows if "2024-01" <= r[0] <= "2024-06"]
    direct_2026 = [r[1] for r in rows if r[0].startswith("2026")]
    indirect_2026 = [r[2] for r in rows if r[0].startswith("2026")]
    assert max(first_half_2024) < 0.12, first_half_2024
    assert sum(1 for s in direct_2026 if s >= 0.25) >= 9, direct_2026
    assert all(0.05 < s < 0.1 for s in indirect_2026), indirect_2026
    out = CHAPTER11.mock(d, "overtime_shares", [110, 200, 210], shown=slice(24, 36))
    db.emphasize_cells(d, out["geometry"], [(-1, 1), (11, 1)])
    note(d, "The grid is scrolled to the twelve months of 2026. Outlined: the direct overtime share, a "
            "quarter or more in most months.", out["bottom"] + 8, 40)
    return d


def fig_11_03() -> Diagram:
    d = Diagram("Partitions and Frames in a Window Function")
    gaps = [(y, p, g) for y, p, g in q("SELECT FiscalYear, FiscalPeriod, SUM(Debit) - SUM(Credit) "
                                        "FROM GLEntry WHERE AccountID = 92 AND FiscalYear BETWEEN 2025 "
                                        "AND 2026 AND SourceDocumentType <> 'WorkOrderClose' "
                                        "GROUP BY FiscalYear, FiscalPeriod ORDER BY FiscalYear, FiscalPeriod")]
    assert len(gaps) == 24
    rows, ytd, prev_year = [], 0.0, None
    for i, (y, p, g) in enumerate(gaps):
        ytd = g if y != prev_year else ytd + g
        prev_year = y
        moving = sum(x[2] for x in gaps[max(0, i - 2):i + 1])
        rows.append((f"{y}-{p:02d}", num(g), num(ytd), num(moving)))
    y0 = 22
    d.text("<b>Monthly gap in account 1090, fiscal 2025 and 2026</b>", 0, 0, 600, 20, size=SMALL)
    d.grid(0, y0, ["Month", "Gap", "Year to date", "Moving 3 months"], [110, 120, 130, 150], rows,
           row_h=24)
    # Partitions: one bracket per fiscal year.
    for k, year in enumerate((2025, 2026)):
        top = y0 + 24 * (1 + 12 * k)
        d.box(f"<b>Partition: {year}</b><br>the year-to-date total restarts in January", 540, top + 4, 220, 60,
              fill=BLUE_TINT, stroke=BLUE, align="left", size=SMALL)
        d.outline(512, top, 8, 24 * 12, BLUE, width=2)
    # One frame: the current row and the two before it.
    frame_row = 18   # 2026-07, the 19th data row
    ftop = y0 + 24 * (1 + frame_row - 2)
    xl.emphasis(d, 0, ftop, 510, 24 * 3)
    d.box("<b>Frame for 2026-07</b><br>ROWS BETWEEN 2 PRECEDING AND CURRENT ROW: the moving total adds these "
          "three months", 540, ftop - 6, 320, 84, fill=CORAL_TINT, stroke=CORAL, align="left", size=SMALL)
    note(d, "Amounts are the monthly postings of fiscal 2025 and 2026. A partition decides which rows belong together; "
            "a frame decides which of them each row's calculation uses.", y0 + 24 * 25 + 10, 40)
    return d


def fig_11_04() -> Diagram:
    d = Diagram("The Monthly Gap in Account 1090 and Its Year-to-Date Total")
    rows = db.run(sql("gap_ytd"))[1]
    decembers = [r[3] for r in rows if r[1] == 12]
    assert decembers == sorted(decembers) and decembers[2] > 1.9 * decembers[0], decembers
    out = CHAPTER11.mock(d, "gap_ytd", [130, 130, 180, 200], shown=slice(24, 36))
    db.emphasize_cells(d, out["geometry"], [(-1, 3), (11, 3)])
    note(d, "The grid is scrolled to fiscal 2026. Outlined: the year-to-date total, which accumulates through the year.",
         out["bottom"] + 8, 22)
    return d


def fig_11_05() -> Diagram:
    d = Diagram("The Largest Months of the Gap and Their Pay Dates")
    rows = db.run(sql("gap_pay_dates"))[1]
    assert len(rows) == 9
    assert all(r[3] == 3 for r in rows if r[4] == 1), rows          # each year's largest month
    three = q("SELECT FiscalYear, FiscalPeriod FROM GLEntry WHERE AccountID = 92 "
              "AND SourceDocumentType = 'PayrollSummary' GROUP BY FiscalYear, FiscalPeriod "
              "HAVING COUNT(DISTINCT PostingDate) = 3")
    assert len(three) == 6 and set(three) <= {(r[0], r[1]) for r in rows}, three
    assert not q("SELECT 1 FROM JournalEntry je INNER JOIN GLEntry gl ON gl.SourceDocumentType = "
                 "'JournalEntry' AND gl.SourceDocumentID = je.JournalEntryID INNER JOIN Account a "
                 "ON a.AccountID = gl.AccountID WHERE a.AccountNumber = 2030 AND je.EntryType "
                 "LIKE 'Accrual%'"), "no month-end wage accrual"
    out = CHAPTER11.mock(d, "gap_pay_dates", [120, 120, 160, 110, 110])
    for i, r in enumerate(rows):
        if r[3] == 3:
            db.emphasize_cells(d, out["geometry"], [(i, 3)])
    note(d, "Outlined: the months with three pay dates, which include the largest month of every year.",
         out["bottom"] + 8, 22)
    return d


def fig_11_06() -> Diagram:
    d = Diagram("Work Centers Ranked by Hours Recorded Against Plan")
    rows = db.run(sql("work_centers"))[1]
    assert len(rows) == 15
    top = {r[1] for r in rows if r[4] <= 2}
    assert top == {"Packing Work Center", "Quality Assurance Work Center"}, top
    assert all(r[5] < 0 for r in rows), "the plant as a whole records less direct time than planned"
    out = CHAPTER11.mock(d, "work_centers", [70, 230, 110, 140, 100, 150], shown=slice(10, 15))
    marks = [i for i, r in enumerate(rows[10:15]) if r[4] <= 2]
    for i in marks:
        db.emphasize_cells(d, out["geometry"], [(i, 0), (i, 4)])
    note(d, "The grid is scrolled to the operations that ended in 2026. Outlined: the two work centers ranked first.",
         out["bottom"] + 8, 22)
    return d


def fig_11_07() -> Diagram:
    d = Diagram("The Chain of Common Table Expressions in the Monthly Measure")
    rows = db.run(sql("measure_trailing"))[1]
    assert rows[0][0] == "2024-12" and rows[-1][0] == "2026-12" and len(rows) == 25
    out = d.box("<b>MonthlyOutput</b><br>ProductionCompletionLine, ProductionCompletion, Item:<br>"
                "standard hours by month, up to the last day with time records",
                0, 0, 410, 80, fill=BLUE_TINT, stroke=BLUE)
    hrs = d.box("<b>MonthlyHours</b><br>LaborTimeEntry, without NonManufacturing time:<br>"
                "direct, indirect, and overtime hours by month",
                450, 0, 410, 80, fill=BLUE_TINT, stroke=BLUE)
    mon = d.box("<b>Monthly</b><br>joins the two steps on Month", 230, 130, 400, 60, fill=BLUE_TINT, stroke=BLUE)
    trl = d.box("<b>Trailing</b><br>the monthly ratio, and the trailing twelve-month direct, indirect, and total<br>"
                "hours per standard hour and overtime share over the window w;<br>the months in each window",
                100, 240, 660, 90, fill=BLUE_TINT, stroke=BLUE)
    sel = d.box("<b>Final SELECT</b><br>keeps the months whose window holds twelve months", 230, 380, 400, 60,
                fill=GRAY_TINT, stroke=GRAY)
    d.arrow(out, mon, exit=(0.5, 1), entry=(0.25, 0))
    d.arrow(hrs, mon, exit=(0.5, 1), entry=(0.75, 0))
    d.arrow(mon, trl)
    d.arrow(trl, sel)
    note(d, "Each step can be checked on its own by selecting from it. Saved with CREATE VIEW, the whole chain "
            "becomes MonthlyLaborEfficiency.", 450, 40)
    return d


def fig_11_08() -> Diagram:
    d = Diagram("The Saved View in the Database Structure Tab")
    create_temp_view()
    columns = [r[1] for r in q("PRAGMA temp.table_info(MonthlyLaborEfficiency)")]
    assert columns == VIEW_COLUMNS, columns
    counts = dict(q("SELECT type, COUNT(*) FROM main.sqlite_master WHERE name NOT LIKE 'sqlite_%' "
                    "GROUP BY type"))
    assert counts.get("view", 0) == 0 and counts.get("trigger", 0) == 0, counts
    y = db.window(d, active="Database Structure")
    widths = [320, 120, 420]
    db.structure_row(d, 0, y, widths, ["Name", "Type", "Schema"], bold=True, fill=GRAY_TINT)
    y += ROW_H
    db.structure_row(d, 0, y, widths, [f"▸ Tables ({counts['table']})", "", ""], bold=True)
    y += ROW_H
    db.structure_row(d, 0, y, widths, [f"▸ Indices ({counts['index']})", "", ""], bold=True)
    y += ROW_H
    top = y
    db.structure_row(d, 0, y, widths, ["▾ Views (1)", "", ""], bold=True)
    y += ROW_H
    db.structure_row(d, 0, y, widths, ["▾ MonthlyLaborEfficiency", "", "CREATE VIEW MonthlyLaborEfficiency AS WITH …"],
                     indent=1, bold=True, fill=BLUE_TINT)
    y += ROW_H
    for name in columns:
        db.structure_row(d, 0, y, widths, [name, "", f'"{name}"'], indent=2)
        y += ROW_H
    xl.emphasis(d, 0, top, 860, y - top)
    db.structure_row(d, 0, y, widths, ["▸ Triggers (0)", "", ""], bold=True)
    y += ROW_H
    note(d, "Outlined: the view saved in CharlesRiver_Work.sqlite after Write Changes, with its six columns.",
         y + 10, 22)
    return d


def fig_11_09() -> Diagram:
    d = Diagram("The Monthly Measure for Fiscal 2026, Queried from the View")
    create_temp_view()
    rows = db.run(sql("query_view"))[1]
    full = [r for r in db.run(sql("measure_trailing"))[1] if r[0] >= "2026-01"]
    assert rows == full and len(rows) == 12, "the view returns the rows of the full query"
    direct = [r[2] for r in rows]
    indirect = [r[3] for r in rows]
    total = [r[4] for r in rows]
    assert max(indirect) - min(indirect) < 0.06, indirect                  # flat indirect time
    assert direct[-1] > direct[0] and max(total) == total[9] == 1.54, (direct, total)
    out = CHAPTER11.mock(d, "query_view", [90, 180, 110, 120, 110, 160])
    db.emphasize_cells(d, out["geometry"], [(-1, 2), (11, 5)])
    note(d, "Outlined: the trailing twelve-month columns, which change slowly while the monthly ratio swings.",
         out["bottom"] + 8, 22)
    return d


FIGURES = {
    "fig-11-01-conditional-aggregation": fig_11_01,
    "fig-11-02-overtime-shares": fig_11_02,
    "fig-11-03-window-frames": fig_11_03,
    "fig-11-04-gap-year-to-date": fig_11_04,
    "fig-11-05-gap-pay-dates": fig_11_05,
    "fig-11-06-work-center-rank": fig_11_06,
    "fig-11-07-cte-pipeline": fig_11_07,
    "fig-11-08-view-in-structure": fig_11_08,
    "fig-11-09-monthly-measure": fig_11_09,
}
