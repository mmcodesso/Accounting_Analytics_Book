"""Chapter 11 figures."""

from __future__ import annotations

import dbbrowser as db
import excel as xl
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK,
                    ROW_H, RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

MEASURE_CTE = """WITH MonthlyOutput AS (
    SELECT strftime('%Y-%m', pc.CompletionDate) AS Month,
        SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) AS StandardHours
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
    GROUP BY Month),
MonthlyHours AS (
    SELECT strftime('%Y-%m', WorkDate) AS Month,
        SUM(RegularHours + OvertimeHours) AS LaborHours, SUM(OvertimeHours) AS OvertimeHours
    FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' GROUP BY Month),
Monthly AS (
    SELECT o.Month, o.StandardHours, h.LaborHours, h.OvertimeHours
    FROM MonthlyOutput AS o INNER JOIN MonthlyHours AS h ON h.Month = o.Month),
Trailing AS (
    SELECT Month, ROUND(LaborHours / StandardHours, 2) AS HoursPerStandardHour,
        ROUND(SUM(LaborHours) OVER w / SUM(StandardHours) OVER w, 2) AS TTMHoursPerStandardHour,
        ROUND(SUM(OvertimeHours) OVER w / SUM(LaborHours) OVER w, 3) AS TTMOvertimeShare,
        COUNT(*) OVER w AS MonthsInWindow
    FROM Monthly WINDOW w AS (ORDER BY Month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW))
SELECT Month, HoursPerStandardHour, TTMHoursPerStandardHour, TTMOvertimeShare
FROM Trailing WHERE MonthsInWindow = 12"""


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


def num(value: float, places: int = 2) -> str:
    return f"{value:,.{places}f}"


def monthly_gap() -> list[tuple]:
    return q("SELECT FiscalYear, FiscalPeriod, SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = 92 "
             "AND FiscalYear BETWEEN 2024 AND 2026 AND SourceDocumentType <> 'WorkOrderClose' "
             "GROUP BY FiscalYear, FiscalPeriod ORDER BY FiscalYear, FiscalPeriod")


def fig_11_01() -> Diagram:
    d = Diagram("Conditional Aggregation Turns Rows into Columns")
    day = "2026-03-10"
    rows = q("SELECT LaborTimeEntryID, RegularHours, OvertimeHours, WorkOrderOperationID IS NULL "
             "FROM LaborTimeEntry WHERE LaborType = 'Direct Manufacturing' AND WorkDate = ? "
             "AND OvertimeHours > 0 ORDER BY LaborTimeEntryID LIMIT 4", day)
    rows += q("SELECT LaborTimeEntryID, RegularHours, OvertimeHours, WorkOrderOperationID IS NULL "
              "FROM LaborTimeEntry WHERE LaborType = 'Indirect Manufacturing' AND WorkDate = ? "
              "ORDER BY LaborTimeEntryID LIMIT 2", day)
    assert len(rows) == 6 and any(r[3] for r in rows) and not all(r[3] for r in rows)
    d.text(f"<b>Labor time entries of {day} (a sample)</b>", 0, 0, 470, 20, size=SMALL)
    d.grid(0, 22, ["LaborTimeEntryID", "RegularHours", "OvertimeHours", "On a work order"],
           [130, 110, 110, 120], [(str(i), num(r), num(o), "No" if n else "Yes") for i, r, o, n in rows])
    reg = sum(r[1] for r in rows)
    ot = sum(r[2] for r in rows)
    off = sum(r[1] + r[2] for r in rows if r[3])
    d.text("<b>The sample summarized, one column per category</b>", 510, 0, 350, 20, size=SMALL)
    out = d.grid(510, 58, ["Regular", "Overtime", "NotOnWorkOrder"], [100, 100, 150],
                 [(num(reg), num(ot), num(off))])
    labels = ["<b>Regular</b> = SUM(RegularHours)", "<b>Overtime</b> = SUM(OvertimeHours)",
              "<b>NotOnWorkOrder</b> = SUM(CASE WHEN",
              "&nbsp;&nbsp;&nbsp;&nbsp;WorkOrderOperationID IS NULL",
              "&nbsp;&nbsp;&nbsp;&nbsp;THEN RegularHours + OvertimeHours",
              "&nbsp;&nbsp;&nbsp;&nbsp;ELSE 0 END)"]
    for i, lab in enumerate(labels):
        d.text(lab, 510, 118 + i * 20, 350, 20, size=SMALL, color=INK)
    d.arrow(d.container(472, 22, 2, ROW_H * 7), out[(1, 0)], color=GRAY)
    note(d, "The summary totals only the six sample entries shown. The CASE expression passes the hours of the "
            "entries with no work order operation and zero for the others.",
         max(22 + ROW_H * 7, 118 + len(labels) * 20) + 12, 40)
    return d


def fig_11_02() -> Diagram:
    d = Diagram("Labor Hours by Category and Month")
    sql = ("SELECT strftime('%Y-%m', lt.WorkDate) AS WorkMonth,\n"
           "    ROUND(SUM(lt.RegularHours), 0) AS RegularHours,\n"
           "    ROUND(SUM(lt.OvertimeHours), 0) AS OvertimeHours,\n"
           "    ROUND(SUM(CASE WHEN lt.WorkOrderOperationID IS NULL\n"
           "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0)\n"
           "        AS NotOnWorkOrder,\n"
           "    ROUND(SUM(lt.OvertimeHours)\n"
           "        / SUM(lt.RegularHours + lt.OvertimeHours), 3) AS OvertimeShare,\n"
           "    ROUND(SUM(CASE WHEN lt.WorkOrderOperationID IS NULL\n"
           "        THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END)\n"
           "        / SUM(lt.RegularHours + lt.OvertimeHours), 3) AS NotOnWorkOrderShare\n"
           "FROM LaborTimeEntry AS lt\n"
           "WHERE lt.LaborType <> 'NonManufacturing'\n"
           "GROUP BY WorkMonth\n"
           "ORDER BY WorkMonth;")
    headers, rows = db.run(sql)
    assert len(rows) == 36
    shares_2026 = [r[4] for r in rows if r[0].startswith("2026")]
    assert sum(1 for s in shares_2026 if s >= 0.18) >= 9, shares_2026
    out = db.execute_sql(d, sql, [100, 120, 120, 130, 130, 150], shown=slice(24, 36))
    db.emphasize_cells(d, out["geometry"], [(-1, 4), (11, 4)])
    note(d, "The grid is scrolled to the twelve months of 2026. Outlined: the overtime share, around a fifth in most months.",
         out["bottom"] + 8, 22)
    return d


def fig_11_03() -> Diagram:
    d = Diagram("Partitions and Frames in a Window Function")
    gaps = [(y, p, g) for y, p, g in monthly_gap() if y in (2025, 2026)]
    assert len(gaps) == 24
    rows, ytd, prev_year = [], 0.0, None
    for i, (y, p, g) in enumerate(gaps):
        ytd = g if y != prev_year else ytd + g
        prev_year = y
        moving = sum(x[2] for x in gaps[max(0, i - 2):i + 1])
        rows.append((f"{y}-{p:02d}", num(g), num(ytd), num(moving)))
    y0 = 22
    d.text("<b>Monthly gap in account 1090, fiscal 2025 and 2026</b>", 0, 0, 600, 20, size=SMALL)
    geo = d.grid(0, y0, ["Month", "Gap", "Year to date", "Moving 3 months"], [110, 120, 130, 150], rows,
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
    sql = ("SELECT FiscalYear, FiscalPeriod,\n"
           "    ROUND(SUM(Debit) - SUM(Credit), 2) AS Gap,\n"
           "    ROUND(SUM(SUM(Debit) - SUM(Credit)) OVER (\n"
           "        PARTITION BY FiscalYear ORDER BY FiscalPeriod), 2) AS GapYearToDate\n"
           "FROM GLEntry\n"
           "WHERE AccountID = 92 AND FiscalYear BETWEEN 2024 AND 2026\n"
           "    AND SourceDocumentType <> 'WorkOrderClose'\n"
           "GROUP BY FiscalYear, FiscalPeriod\n"
           "ORDER BY FiscalYear, FiscalPeriod;")
    headers, rows = db.run(sql)
    decembers = [r[3] for r in rows if r[1] == 12]
    assert decembers == sorted(decembers) and decembers[2] > 1.9 * decembers[0], decembers
    out = db.execute_sql(d, sql, [130, 130, 180, 200], shown=slice(24, 36))
    db.emphasize_cells(d, out["geometry"], [(-1, 3), (11, 3)])
    note(d, "The grid is scrolled to fiscal 2026. Outlined: the year-to-date total, which accumulates through the year.",
         out["bottom"] + 8, 22)
    return d


def fig_11_05() -> Diagram:
    d = Diagram("Work Centers Ranked by Hours Recorded Against Plan")
    shown = ("SELECT CloseYear, WorkCenterName, PlannedHours, RecordedHours,\n"
             "    ROUND(RecordedHours / PlannedHours, 2) AS RecordedPerPlanned,\n"
             "    RANK() OVER (PARTITION BY CloseYear\n"
             "        ORDER BY RecordedHours / PlannedHours DESC) AS CenterRank\n"
             "FROM (SELECT strftime('%Y', op.ActualEndDate) AS CloseYear, ...) AS centers\n"
             "ORDER BY CloseYear, CenterRank;")
    full = ("SELECT CloseYear, WorkCenterName, PlannedHours, RecordedHours, "
            "ROUND(RecordedHours / PlannedHours, 2) AS RecordedPerPlanned, "
            "RANK() OVER (PARTITION BY CloseYear ORDER BY RecordedHours / PlannedHours DESC) AS CenterRank "
            "FROM (SELECT strftime('%Y', op.ActualEndDate) AS CloseYear, wc.WorkCenterName, "
            "ROUND(SUM(op.PlannedLoadHours), 0) AS PlannedHours, ROUND(SUM(lab.Hours), 0) AS RecordedHours "
            "FROM WorkOrderOperation AS op INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = op.WorkCenterID "
            "LEFT JOIN (SELECT WorkOrderOperationID, SUM(RegularHours + OvertimeHours) AS Hours FROM LaborTimeEntry "
            "WHERE LaborType = 'Direct Manufacturing' GROUP BY WorkOrderOperationID) AS lab "
            "ON lab.WorkOrderOperationID = op.WorkOrderOperationID WHERE op.ActualEndDate IS NOT NULL "
            "GROUP BY CloseYear, wc.WorkCenterName) AS centers ORDER BY CloseYear, CenterRank")
    headers, rows = db.run(full)
    top = {r[1] for r in rows if r[5] <= 2}
    assert top == {"Packing Work Center", "Quality Assurance Work Center"}, top
    y = db.window(d)
    y = db.editor(d, 0, y, 860, shown) + 8
    geometry = db.results(d, 0, y, headers, [90, 250, 110, 120, 140, 110], rows)
    y += (len(rows) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), shown.split("\n")[0])
    marks = [i for i, r in enumerate(rows) if r[5] <= 2]
    for i in marks:
        db.emphasize_cells(d, geometry, [(i, 0), (i, 5)])
    note(d, "The derived table is shortened here with an ellipsis; Tutorial 11.2 gives the full query. "
            "Outlined: the two work centers ranked first and second in each year.", bottom + 8, 40)
    return d


def fig_11_06() -> Diagram:
    d = Diagram("The Chain of Common Table Expressions in the Monthly Measure")
    rows = q(MEASURE_CTE)
    assert rows[0][0] == "2024-12" and len(rows) == 25
    out = d.box("<b>MonthlyOutput</b><br>ProductionCompletionLine, ProductionCompletion, Item:<br>standard hours by month",
                0, 0, 400, 80, fill=BLUE_TINT, stroke=BLUE)
    hrs = d.box("<b>MonthlyHours</b><br>LaborTimeEntry, without NonManufacturing time:<br>labor and overtime hours by month",
                460, 0, 400, 80, fill=BLUE_TINT, stroke=BLUE)
    mon = d.box("<b>Monthly</b><br>joins the two steps on Month", 230, 130, 400, 60, fill=BLUE_TINT, stroke=BLUE)
    trl = d.box("<b>Trailing</b><br>monthly ratio, and trailing twelve-month ratio and overtime share<br>"
                "over ROWS BETWEEN 11 PRECEDING AND CURRENT ROW; months in each window",
                130, 240, 600, 80, fill=BLUE_TINT, stroke=BLUE)
    sel = d.box("<b>Final SELECT</b><br>keeps the months whose window holds twelve months", 230, 370, 400, 60,
                fill=GRAY_TINT, stroke=GRAY)
    d.arrow(out, mon, exit=(0.5, 1), entry=(0.25, 0))
    d.arrow(hrs, mon, exit=(0.5, 1), entry=(0.75, 0))
    d.arrow(mon, trl)
    d.arrow(trl, sel)
    note(d, "Each step can be checked on its own with SELECT * FROM its name. Saved with CREATE VIEW, the whole chain "
            "becomes MonthlyLaborEfficiency.", 440, 40)
    return d


def fig_11_07() -> Diagram:
    d = Diagram("The Saved View in the Database Structure Tab")
    columns = ["Month", "HoursPerStandardHour", "TTMHoursPerStandardHour", "TTMOvertimeShare"]
    names = [r[0] for r in q("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                             "ORDER BY name")]
    y = db.window(d, active="Database Structure")
    widths = [320, 120, 420]
    db.structure_row(d, 0, y, widths, ["Name", "Type", "Schema"], bold=True, fill=GRAY_TINT)
    y += ROW_H
    db.structure_row(d, 0, y, widths, ["▸ Tables", "", ""], bold=True)
    y += ROW_H
    db.structure_row(d, 0, y, widths, ["▸ Indices", "", ""], bold=True)
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
    db.structure_row(d, 0, y, widths, ["▸ Triggers", "", ""], bold=True)
    y += ROW_H
    note(d, "Outlined: the view saved in CharlesRiver_Work.sqlite after Write Changes, with its four columns.",
         y + 10, 22)
    return d


def fig_11_08() -> Diagram:
    d = Diagram("The Monthly Measure for Fiscal 2026, Queried from the View")
    sql = ("SELECT *\n"
           "FROM MonthlyLaborEfficiency\n"
           "WHERE Month >= '2026-01'\n"
           "ORDER BY Month;")
    rows = [r for r in q(MEASURE_CTE) if r[0] >= "2026-01"]
    assert len(rows) == 12 and 1.4 < rows[-1][2] < 1.6
    headers = ["Month", "HoursPerStandardHour", "TTMHoursPerStandardHour", "TTMOvertimeShare"]
    y = db.window(d)
    y = db.editor(d, 0, y, 860, sql) + 8
    geometry = db.results(d, 0, y, headers, [120, 200, 240, 200], rows)
    y += (len(rows) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), "SELECT *")
    db.emphasize_cells(d, geometry, [(-1, 2), (11, 3)])
    note(d, "Outlined: the trailing twelve-month columns, which change slowly while the monthly ratio swings.",
         bottom + 8, 22)
    return d


FIGURES = {
    "fig-11-01-conditional-aggregation": fig_11_01,
    "fig-11-02-hours-by-month": fig_11_02,
    "fig-11-03-window-frames": fig_11_03,
    "fig-11-04-gap-year-to-date": fig_11_04,
    "fig-11-05-work-center-rank": fig_11_05,
    "fig-11-06-cte-pipeline": fig_11_06,
    "fig-11-07-view-in-structure": fig_11_07,
    "fig-11-08-monthly-measure": fig_11_08,
}
