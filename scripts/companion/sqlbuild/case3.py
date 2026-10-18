"""Instructor SQL solution to the Part III comprehensive case, "Planning the Plant's Hours for 2027": one script,
Case.sql, with the queries of every requirement in order.

The script follows the case's standard (the header of Audit.sql, and two comment lines above every query: what it tests,
and its population and expected result). It saves the populations it reuses as views, as the case asks: SurgeDays (the
SurgeDays CTE of test H9 in Tutorial 12.3), PlantEntries (one row per hourly manufacturing clock entry, with its
DayType), PlantWeeks (Monday weeks of hours and output), PlantLedger (accounts 1090 and 5080 by fiscal year), PlantAssets
(the manufacturing equipment's monthly depreciation), PayrollAccrual and PriorYearWork (the year-end payroll), and
CutoffItems (the revenue cutoff). It reads the view MonthlyLaborEfficiency of Tutorial 11.3 (the manifest entry has
`setup_views`, so the build creates it first as a TEMP view) and reruns tests L5, L6 and L8 of Audit.sql as Tutorial
12.1 wrote them.

Every expected value comes from the context functions of the case's instructor notes (facts/notes/case3.py) or from
read-only SQL of this module; every actual value is read from the query's result. Years are the fiscal window's (F, P,
C, and the plan year N), so a rolled dataset rebuilds the script for its own window.
"""

from __future__ import annotations

import sys

from paths import REPO
from sqlbuild.script import Build, Check

FILE = "Case.sql"
TITLE = "the plant's hours: corroboration, cost, the next year's plan, and the year-end close"
SETUP_VIEWS = True                      # dev harness flag; the manifest entry has setup_views
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def notes(b: Build):
    b.data                                       # puts facts/ on sys.path
    from notes import case3
    return case3


def context(b: Build, name: str) -> dict:
    return getattr(notes(b), name)(b.data, lambda *a, **k: None)


def audit_sql(key: str) -> str:
    """A test of Audit.sql as Tutorial 12.1 wrote it (the shared definitions of the book's figures)."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from shared.calculations.sql_ch12 import QUERIES
    return next(text for k, _, text in QUERIES if k == key)


def money(x: float) -> str:
    return f"{x:,.2f}"


def num(x: float, places: int = 0) -> str:
    return f"{x:,.{places}f}"


def script(b: Build):
    d = b.data
    return b.script(FILE, TITLE,
                    f"populations profiled and linked; SurgeDays reconciles to Tutorial 12.3; the 5080 bridge adds up "
                    f"to the ledger; the plan's depreciation reproduces {d.C}'s; the cutoff reruns Audit.sql L5, L6, L8")


def year_between(year: int, column: str) -> str:
    return f"{column} BETWEEN '{year}-01-01' AND '{year}-12-31'"


CLOSES = """SELECT EntryNumber
FROM JournalEntry
WHERE EntryType LIKE 'Year-End Close%'"""
LAST_WORK = "(SELECT MAX(WorkDate) FROM TimeClockEntry)"
COMPLETIONS = """\
FROM ProductionCompletionLine AS pcl
    INNER JOIN ProductionCompletion AS pc
        ON pc.ProductionCompletionID = pcl.ProductionCompletionID
    INNER JOIN Item AS i ON i.ItemID = pcl.ItemID"""
STD_HOURS = "pcl.QuantityCompleted * i.StandardLaborHoursPerUnit"


def indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.split("\n"))


def sub(text: str, col: int) -> str:
    """Multi-line SQL placed at column `col` of a query written in the source: every line after the first is
    indented by `col`, so that the query's own dedent keeps the inserted lines in place."""
    lines = text.split("\n")
    return "\n".join([lines[0]] + [" " * col + line if line else line for line in lines[1:]])


# --- Requirement 1: the script and its populations -------------------------------------------------------------------

def r1(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r1")
    ys = notes(b).yearly(d)
    types = n["types"]
    missing = types["Clock In"] - types["Clock Out"]

    s.query("Requirement 1: profile of TimeClockPunch, its rows, dates, and columns not always filled in",
            f"Population: every punch; expected: {num(n['punches'])} punches of {n['punch_employees']} employees, "
            f"{n['punch_first']} to {n['punch_last']}",
            """
            SELECT COUNT(*) AS Punches,
                COUNT(DISTINCT EmployeeID) AS Employees,
                COUNT(DISTINCT TimeClockEntryID) AS ClockEntries,
                MIN(WorkDate) AS FirstDate,
                MAX(WorkDate) AS LastDate,
                COUNT(EmployeeShiftRosterID) AS WithRoster,
                COUNT(WorkCenterID) AS WithWorkCenter
            FROM TimeClockPunch;
            """,
            [Check("punches", n["punches"], lambda r: r.value("Punches")),
             Check("employees", n["punch_employees"], lambda r: r.value("Employees")),
             Check("clock entries with punches: every clock entry", d.one("SELECT COUNT(*) FROM TimeClockEntry"),
                   lambda r: r.value("ClockEntries")),
             Check("first date", n["punch_first"], lambda r: r.value("FirstDate")),
             Check("last date", n["punch_last"], lambda r: r.value("LastDate")),
             Check("punches without a roster (the detached clock-ins)", len(n["detached"]),
                   lambda r: r.value("Punches") - r.value("WithRoster"))])

    s.query("Requirement 1: the code columns of TimeClockPunch, PunchType and PunchSource",
            f"Population: every punch; expected: {len(types)} punch types, all {n['source']}; "
            f"{missing} fewer clock-outs than clock-ins",
            """
            SELECT PunchType, PunchSource, COUNT(*) AS Punches
            FROM TimeClockPunch
            GROUP BY PunchType, PunchSource
            ORDER BY Punches DESC, PunchType;
            """,
            [Check("punch types", sorted(types), lambda r: sorted(r.col("PunchType"))),
             Check("sources", [n["source"]], lambda r: sorted(set(r.col("PunchSource"))))]
            + [Check(f"{t} punches", v, lambda r, t=t: r.where(PunchType=t)["Punches"]) for t, v in types.items()])

    repeated = d.one("SELECT COUNT(*) FROM (SELECT TimeClockEntryID, PunchType FROM TimeClockPunch GROUP BY 1, 2 "
                     "HAVING COUNT(*) > 1)")
    orphans = d.one("SELECT COUNT(*) FROM TimeClockPunch WHERE TimeClockEntryID NOT IN "
                    "(SELECT TimeClockEntryID FROM TimeClockEntry)")
    s.query("Requirement 1: keys of TimeClockPunch that appear more than once, and punches without their clock entry",
            "Population: every punch; expected: no clock entry with two punches of one type, no orphan",
            """
            SELECT
                (SELECT COUNT(*)
                 FROM (
                     SELECT TimeClockEntryID, PunchType
                     FROM TimeClockPunch
                     GROUP BY TimeClockEntryID, PunchType
                     HAVING COUNT(*) > 1
                 ) AS t) AS RepeatedPunchTypes,
                (SELECT COUNT(*)
                 FROM TimeClockPunch AS p
                     LEFT JOIN TimeClockEntry AS tc
                         ON tc.TimeClockEntryID = p.TimeClockEntryID
                 WHERE tc.TimeClockEntryID IS NULL) AS PunchesWithoutEntry;
            """,
            [Check("entries with two punches of one type", repeated, lambda r: r.value("RepeatedPunchTypes")),
             Check("punches without their clock entry", orphans, lambda r: r.value("PunchesWithoutEntry"))])

    s.query("Requirement 1: clock entries with a clock-in punch and no clock-out punch",
            f"Population: clock entries with punches; expected: {missing} entries of employee "
            f"{n['missing_employee']}, each on January 1",
            """
            SELECT p.TimeClockEntryID, tc.EmployeeID, tc.WorkDate,
                tc.ClockStatus
            FROM TimeClockPunch AS p
                INNER JOIN TimeClockEntry AS tc
                    ON tc.TimeClockEntryID = p.TimeClockEntryID
            GROUP BY p.TimeClockEntryID, tc.EmployeeID, tc.WorkDate,
                tc.ClockStatus
            HAVING SUM(CASE WHEN p.PunchType = 'Clock Out'
                THEN 1 ELSE 0 END) = 0
            ORDER BY tc.WorkDate;
            """,
            [Check("entries without a clock-out", missing, len),
             Check("their employee", [n["missing_employee"]], lambda r: sorted(set(r.col("EmployeeID")))),
             Check("their dates", [f"{y}-01-01" for y in d.years], lambda r: r.col("WorkDate"))])

    s.query("Requirement 1: profile of EmployeeShiftRoster, with any employee rostered twice on one date",
            f"Population: every roster; expected: {num(n['rosters'])} rosters, no employee rostered twice",
            """
            SELECT COUNT(*) AS Rosters,
                COUNT(DISTINCT EmployeeID) AS Employees,
                MIN(RosterDate) AS FirstDate,
                MAX(RosterDate) AS LastDate,
                COUNT(WorkCenterID) AS WithWorkCenter,
                (SELECT COUNT(*)
                 FROM (
                     SELECT EmployeeID, RosterDate
                     FROM EmployeeShiftRoster
                     GROUP BY EmployeeID, RosterDate
                     HAVING COUNT(*) > 1
                 ) AS t) AS RosteredTwice
            FROM EmployeeShiftRoster;
            """,
            [Check("rosters", n["rosters"], lambda r: r.value("Rosters")),
             Check("employees rostered twice on one date",
                   d.one("SELECT COUNT(*) - COUNT(DISTINCT EmployeeID || '/' || RosterDate) FROM EmployeeShiftRoster"),
                   lambda r: r.value("RosteredTwice"))])

    s.query("Requirement 1: the roster statuses",
            f"Population: every roster; expected: {len(n['statuses'])} statuses",
            """
            SELECT RosterStatus, COUNT(*) AS Rosters
            FROM EmployeeShiftRoster
            GROUP BY RosterStatus
            ORDER BY Rosters DESC;
            """,
            [Check("statuses and counts", [list(x) for x in n["statuses"]], lambda r: [list(x) for x in r.rows])])

    s.query("Requirement 1: who created the rosters",
            f"Population: every roster; expected: {len(n['creators'])} department managers",
            """
            SELECT r.CreatedByEmployeeID, e.JobTitle, COUNT(*) AS Rosters
            FROM EmployeeShiftRoster AS r
                INNER JOIN Employee AS e
                    ON e.EmployeeID = r.CreatedByEmployeeID
            GROUP BY r.CreatedByEmployeeID, e.JobTitle
            ORDER BY r.CreatedByEmployeeID;
            """,
            [Check("creators and their titles", [list(x) for x in n["creators"]],
                   lambda r: [[x[0], x[1]] for x in r.rows])])

    per_type = n["exceptions"] // len(n["exc_types"])
    s.query("Requirement 1: profile of AttendanceException by type, with the columns not always filled in",
            f"Population: every exception; expected: {n['exceptions']} exceptions, {per_type} of each of "
            f"{len(n['exc_types'])} types, no reviewer and no review date",
            """
            SELECT ExceptionType, Severity, Status,
                COUNT(*) AS Exceptions,
                COUNT(EmployeeShiftRosterID) AS WithRoster,
                COUNT(ShiftDefinitionID) AS WithShift,
                COUNT(ReviewedByEmployeeID) AS Reviewed,
                COUNT(ReviewedDate) AS WithReviewDate,
                MIN(WorkDate) AS FirstDate,
                MAX(WorkDate) AS LastDate
            FROM AttendanceException
            GROUP BY ExceptionType, Severity, Status
            ORDER BY ExceptionType;
            """,
            [Check("exception types", n["exc_types"], lambda r: r.col("ExceptionType")),
             Check("exceptions of each type", [per_type] * len(n["exc_types"]), lambda r: r.col("Exceptions")),
             Check("statuses", ["Open"], lambda r: sorted(set(r.col("Status")))),
             Check("exceptions with a reviewer", d.one("SELECT COUNT(ReviewedByEmployeeID) FROM AttendanceException"),
                   lambda r: r.total("Reviewed")),
             Check("exceptions with a review date", d.one("SELECT COUNT(ReviewedDate) FROM AttendanceException"),
                   lambda r: r.total("WithReviewDate"))])

    centers = d.one("SELECT COUNT(DISTINCT WorkCenterID) FROM WorkCenterCalendar")
    s.query("Requirement 1: profile of WorkCenterCalendar, with any work center and date that appears twice",
            f"Population: every calendar row; expected: {num(n['cal_rows'])} rows, {centers} work centers, "
            f"{n['cal_first']} to {n['cal_last']}",
            """
            SELECT COUNT(*) AS CalendarRows,
                COUNT(DISTINCT WorkCenterID) AS WorkCenters,
                MIN(CalendarDate) AS FirstDate,
                MAX(CalendarDate) AS LastDate,
                COUNT(DISTINCT WorkCenterID || ' ' || CalendarDate)
                    AS CenterDates
            FROM WorkCenterCalendar;
            """,
            [Check("rows", n["cal_rows"], lambda r: r.value("CalendarRows")),
             Check("work centers", centers, lambda r: r.value("WorkCenters")),
             Check("first date", n["cal_first"], lambda r: r.value("FirstDate")),
             Check("last date", n["cal_last"], lambda r: r.value("LastDate")),
             Check("no work center and date twice", n["cal_rows"], lambda r: r.value("CenterDates"))])

    year = d.C
    s.query(f"Requirement 1: the calendar of {year} by exception reason",
            f"Population: WorkCenterCalendar, {year}; expected: maintenance on {n['maintenance']} dates, "
            f"reduced capacity on {n['reduced']}",
            f"""
            SELECT ExceptionReason, IsWorkingDay,
                COUNT(DISTINCT CalendarDate) AS Dates,
                COUNT(*) AS CenterDays,
                ROUND(SUM(AvailableHours), 2) AS AvailableHours
            FROM WorkCenterCalendar
            WHERE {year_between(year, 'CalendarDate')}
            GROUP BY ExceptionReason, IsWorkingDay
            ORDER BY IsWorkingDay DESC, ExceptionReason;
            """,
            [Check("maintenance dates", n["maintenance"], lambda r: r.where(ExceptionReason="Maintenance")["Dates"]),
             Check("reduced-capacity dates", n["reduced"],
                   lambda r: r.where(ExceptionReason="Reduced Capacity")["Dates"]),
             Check("available hours", n["avail"], lambda r: round(r.total("AvailableHours"), 2))])

    s.query(f"Requirement 1: the working days and available hours of {year}",
            f"Population: WorkCenterCalendar, {year}; expected: {n['working']} working days, "
            f"{money(n['avail'])} available hours",
            f"""
            SELECT COUNT(DISTINCT CASE WHEN IsWorkingDay = 1
                    THEN CalendarDate END) AS WorkingDays,
                ROUND(SUM(AvailableHours), 2) AS AvailableHours
            FROM WorkCenterCalendar
            WHERE {year_between(year, 'CalendarDate')};
            """,
            [Check("working days", n["working"], lambda r: r.value("WorkingDays")),
             Check("available hours", n["avail"], lambda r: r.value("AvailableHours"))])

    other_employee = d.one("SELECT COUNT(*) FROM TimeClockPunch p JOIN TimeClockEntry tc ON tc.TimeClockEntryID = "
                           "p.TimeClockEntryID WHERE p.EmployeeID <> tc.EmployeeID")
    s.query("Requirement 1: punches whose employee or date differs from their clock entry's",
            f"Population: every punch; expected: {n['shifted_punches']} punches of {len(n['shifted_entries'])} "
            f"entries, all dated differently",
            """
            SELECT p.TimeClockEntryID, COUNT(*) AS Punches,
                SUM(CASE WHEN p.WorkDate <> tc.WorkDate
                    THEN 1 ELSE 0 END) AS OtherDate,
                SUM(CASE WHEN p.EmployeeID <> tc.EmployeeID
                    THEN 1 ELSE 0 END) AS OtherEmployee
            FROM TimeClockPunch AS p
                INNER JOIN TimeClockEntry AS tc
                    ON tc.TimeClockEntryID = p.TimeClockEntryID
            WHERE p.WorkDate <> tc.WorkDate
                OR p.EmployeeID <> tc.EmployeeID
            GROUP BY p.TimeClockEntryID
            ORDER BY p.TimeClockEntryID;
            """,
            [Check("the clock entries", n["shifted_entries"], lambda r: r.col("TimeClockEntryID")),
             Check("punches dated differently", n["shifted_punches"], lambda r: r.total("OtherDate")),
             Check("punches of another employee", other_employee, lambda r: r.total("OtherEmployee"))])

    no_roster = d.one("SELECT COUNT(*) FROM TimeClockEntry tc LEFT JOIN EmployeeShiftRoster r ON r.EmployeeShiftRosterID "
                      "= tc.EmployeeShiftRosterID WHERE r.EmployeeShiftRosterID IS NULL OR r.EmployeeID <> tc.EmployeeID")
    s.query("Requirement 1: clock entries whose roster is missing, of another employee, or of another date",
            f"Population: every clock entry; expected: every entry has its own roster; the "
            f"{len(n['shifted_entries'])} entries above are rostered on another date",
            """
            SELECT tc.TimeClockEntryID, tc.EmployeeID, tc.WorkDate,
                r.EmployeeID AS RosterEmployeeID, r.RosterDate
            FROM TimeClockEntry AS tc
                LEFT JOIN EmployeeShiftRoster AS r
                    ON r.EmployeeShiftRosterID = tc.EmployeeShiftRosterID
            WHERE r.EmployeeShiftRosterID IS NULL
                OR r.EmployeeID <> tc.EmployeeID
                OR r.RosterDate <> tc.WorkDate
            ORDER BY tc.TimeClockEntryID;
            """,
            [Check("the entries rostered on another date", n["shifted_entries"], lambda r: r.col("TimeClockEntryID")),
             Check("entries without a roster of the same employee", no_roster,
                   lambda r: sum(1 for x in r.rows if x[3] is None or x[3] != x[1]))])

    s.query("Requirement 1: punches detached from their clock entry's roster",
            f"Population: every punch; expected: {len(n['detached'])} clock-in punches of employee "
            f"{n['detached_employee']}, one on each January 1",
            """
            SELECT p.TimeClockPunchID, p.EmployeeID, p.WorkDate,
                p.PunchType, p.EmployeeShiftRosterID,
                tc.EmployeeShiftRosterID AS EntryRosterID
            FROM TimeClockPunch AS p
                INNER JOIN TimeClockEntry AS tc
                    ON tc.TimeClockEntryID = p.TimeClockEntryID
            WHERE p.EmployeeShiftRosterID IS NULL
                OR p.EmployeeShiftRosterID <> tc.EmployeeShiftRosterID
            ORDER BY p.TimeClockPunchID;
            """,
            [Check("the punches", n["detached"], lambda r: r.col("TimeClockPunchID")),
             Check("their employee", [n["detached_employee"]], lambda r: sorted(set(r.col("EmployeeID")))),
             Check("all clock-in punches", ["Clock In"], lambda r: sorted(set(r.col("PunchType")))),
             Check("their dates", [f"{y}-01-01" for y in d.years], lambda r: r.col("WorkDate"))])

    without_entry = d.one("SELECT COUNT(*) FROM AttendanceException WHERE TimeClockEntryID NOT IN "
                          "(SELECT TimeClockEntryID FROM TimeClockEntry)")
    wrong = n["wrong_ids"]
    s.query("Requirement 1: each attendance exception against its clock entry, with a disposition",
            f"Population: every exception; expected: {n['exceptions']} rows, each on its entry's date; exceptions "
            f"{', '.join(map(str, wrong))} name employee {n['wrong_named']} on employee {n['wrong_owner']}'s entries",
            """
            SELECT ae.AttendanceExceptionID, ae.ExceptionType, ae.WorkDate,
                ae.EmployeeID, tc.EmployeeID AS EntryEmployeeID,
                tc.TimeClockEntryID, tc.ClockStatus,
                CASE
                    WHEN tc.TimeClockEntryID IS NULL
                        THEN 'No clock entry: investigate'
                    WHEN ae.WorkDate <> tc.WorkDate
                        THEN 'Dated differently: correct the report'
                    WHEN ae.EmployeeID <> tc.EmployeeID
                        THEN 'Names another employee: correct the report'
                    WHEN ae.ExceptionType = 'Paid Without Approved Clock'
                        THEN 'Paid on a Pending entry (test H1): follow up'
                    ELSE 'Isolated: logged, not pursued in this case'
                END AS Disposition
            FROM AttendanceException AS ae
                LEFT JOIN TimeClockEntry AS tc
                    ON tc.TimeClockEntryID = ae.TimeClockEntryID
            ORDER BY ae.AttendanceExceptionID;
            """,
            [Check("exceptions", n["exceptions"], len),
             Check("exceptions without their clock entry", without_entry,
                   lambda r: sum(1 for x in r.rows if x[5] is None)),
             Check("exceptions dated differently from their clock entry", n["exc_dates"],
                   lambda r: sum(1 for x in r.rows if x[-1].startswith("Dated differently"))),
             Check("exceptions naming another employee", wrong,
                   lambda r: [x[0] for x in r.rows if x[3] != x[4]]),
             Check("the employee they name", [n["wrong_named"]],
                   lambda r: sorted({x[3] for x in r.rows if x[3] != x[4]})),
             Check("the owner of their clock entries", [n["wrong_owner"]],
                   lambda r: sorted({x[4] for x in r.rows if x[3] != x[4]})),
             Check("their clock entries", n["wrong_entries"],
                   lambda r: sorted({x[5] for x in r.rows if x[3] != x[4]}))])

    s.query("Requirement 1: the surge days saved as a view, with the SurgeDays CTE of test H9",
            "Population: manufacturing clock entries by work date; expected: the view SurgeDays",
            """
            DROP VIEW IF EXISTS SurgeDays;
            CREATE VIEW SurgeDays AS
            SELECT tc.WorkDate
            FROM TimeClockEntry AS tc
                INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
            WHERE cc.CostCenterName = 'Manufacturing'
            GROUP BY tc.WorkDate
            HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1
                AND COUNT(DISTINCT tc.EmployeeID) > 1;
            """)

    s.query("Requirement 1: the hourly manufacturing clock entries saved as a view, each with its DayType",
            "Population: clock entries of hourly Manufacturing employees; expected: the view PlantEntries",
            """
            DROP VIEW IF EXISTS PlantEntries;
            CREATE VIEW PlantEntries AS
            SELECT tc.TimeClockEntryID, tc.EmployeeID, tc.WorkDate,
                tc.EmployeeShiftRosterID, tc.OvertimeApprovalID,
                tc.ClockInTime, tc.ClockOutTime, tc.RegularHours,
                tc.OvertimeHours, e.BaseHourlyRate,
                CASE WHEN sd.WorkDate IS NULL THEN 'Ordinary'
                    ELSE 'Surge' END AS DayType
            FROM TimeClockEntry AS tc
                INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
                LEFT JOIN SurgeDays AS sd ON sd.WorkDate = tc.WorkDate
            WHERE cc.CostCenterName = 'Manufacturing'
                AND e.PayClass = 'Hourly';
            """)

    s.query("Requirement 1: the two views reconciled to the surge days and entries of Tutorial 12.3",
            f"Population: SurgeDays and PlantEntries; expected: {', '.join(map(str, n['surge_days']))} surge days "
            f"and {', '.join(num(x) for x in n['surge_entries'])} surge entries",
            """
            SELECT strftime('%Y', pe.WorkDate) AS WorkYear,
                (SELECT COUNT(*)
                 FROM SurgeDays AS sd
                 WHERE strftime('%Y', sd.WorkDate)
                     = strftime('%Y', pe.WorkDate)) AS SurgeDays,
                SUM(CASE WHEN pe.DayType = 'Surge'
                    THEN 1 ELSE 0 END) AS SurgeEntries,
                COUNT(DISTINCT CASE WHEN pe.DayType = 'Ordinary'
                    THEN pe.WorkDate END) AS OrdinaryDays,
                SUM(CASE WHEN pe.DayType = 'Ordinary'
                    THEN 1 ELSE 0 END) AS OrdinaryEntries
            FROM PlantEntries AS pe
            GROUP BY WorkYear
            ORDER BY WorkYear;
            """,
            [Check("work years", [str(y) for y in d.years], lambda r: r.col("WorkYear")),
             Check("surge days by year", n["surge_days"], lambda r: r.col("SurgeDays")),
             Check("surge entries by year", n["surge_entries"], lambda r: r.col("SurgeEntries")),
             Check("ordinary days by year", [y["ordinary"]["days"] for y in ys], lambda r: r.col("OrdinaryDays")),
             Check("ordinary entries by year", [y["ordinary"]["entries"] for y in ys],
                   lambda r: r.col("OrdinaryEntries")),
             Check("surge entries in all", n["surge_total"], lambda r: r.total("SurgeEntries"))])


# --- Requirement 2: do other records support the surge days? ---------------------------------------------------------

def r2(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r2")
    sg, od = n["s"], n["o"]
    s.query("Requirement 2: surge days against ordinary days, attendance and clock-in times (conditional aggregation "
            "and a window)",
            f"Population: PlantEntries by work date; expected: {sg['days']} surge and {od['days']} ordinary days; "
            f"largest group on one clock-in time {sg['largest_min']}-{sg['largest_max']} on surge days",
            """
            WITH Daily AS (
                SELECT WorkDate, DayType,
                    COUNT(DISTINCT EmployeeID) AS Employees,
                    COUNT(DISTINCT ClockInTime) AS ClockInTimes
                FROM PlantEntries
                GROUP BY WorkDate, DayType
            ),
            Groups AS (
                SELECT WorkDate, MAX(SameClockIn) AS LargestGroup
                FROM (
                    SELECT WorkDate,
                        COUNT(*) OVER (PARTITION BY WorkDate, ClockInTime)
                            AS SameClockIn
                    FROM PlantEntries
                ) AS t
                GROUP BY WorkDate
            ),
            Plant AS (
                SELECT COUNT(*) AS HourlyEmployees
                FROM Employee AS e
                    INNER JOIN CostCenter AS cc
                        ON cc.CostCenterID = e.CostCenterID
                WHERE cc.CostCenterName = 'Manufacturing'
                    AND e.PayClass = 'Hourly'
            )
            SELECT d.DayType, COUNT(*) AS Days,
                ROUND(AVG(d.Employees), 1) AS EmployeesPerDay,
                SUM(CASE WHEN d.Employees
                    = (SELECT HourlyEmployees FROM Plant)
                    THEN 1 ELSE 0 END) AS DaysAllPresent,
                ROUND(AVG(d.ClockInTimes), 1) AS ClockInTimesPerDay,
                ROUND(AVG(g.LargestGroup), 1) AS LargestGroupAverage,
                MIN(g.LargestGroup) AS LargestGroupMin,
                MAX(g.LargestGroup) AS LargestGroupMax
            FROM Daily AS d
                INNER JOIN Groups AS g ON g.WorkDate = d.WorkDate
            GROUP BY d.DayType
            ORDER BY d.DayType DESC;
            """,
            [c for t, v in (("Surge", sg), ("Ordinary", od)) for c in (
                Check(f"{t} days", v["days"], lambda r, t=t: r.where(DayType=t)["Days"]),
                Check(f"{t} employees per day", round(v["employees"], 1),
                      lambda r, t=t: r.where(DayType=t)["EmployeesPerDay"], 0.051),
                Check(f"{t} days with every hourly employee present", v["all_present"],
                      lambda r, t=t: r.where(DayType=t)["DaysAllPresent"]),
                Check(f"{t} different clock-in times per day", round(v["clock_ins"], 1),
                      lambda r, t=t: r.where(DayType=t)["ClockInTimesPerDay"], 0.051),
                Check(f"{t} largest group sharing one clock-in time, average", round(v["largest"], 1),
                      lambda r, t=t: r.where(DayType=t)["LargestGroupAverage"], 0.051),
                Check(f"{t} largest group, at most", v["largest_max"],
                      lambda r, t=t: r.where(DayType=t)["LargestGroupMax"]))]
            + [Check("Surge largest group, at least", sg["largest_min"],
                     lambda r: r.where(DayType="Surge")["LargestGroupMin"]),
               Check("hourly employees present on every surge day", n["plant"],
                     lambda r: r.where(DayType="Surge")["EmployeesPerDay"])])

    meals = n["meals"]
    share = meals["Ordinary"][1] / meals["Ordinary"][0]
    s.query("Requirement 2: entries with meal punches, surge days against ordinary days",
            f"Population: PlantEntries; expected: every surge entry, {num(meals['Ordinary'][1])} of "
            f"{num(meals['Ordinary'][0])} ordinary entries ({share:.1%})",
            """
            WITH Meals AS (
                SELECT TimeClockEntryID
                FROM TimeClockPunch
                WHERE PunchType = 'Meal Start'
                GROUP BY TimeClockEntryID
            )
            SELECT pe.DayType, COUNT(*) AS Entries,
                COUNT(m.TimeClockEntryID) AS WithMealPunches,
                ROUND(COUNT(m.TimeClockEntryID) * 1.0 / COUNT(*), 3)
                    AS MealShare
            FROM PlantEntries AS pe
                LEFT JOIN Meals AS m
                    ON m.TimeClockEntryID = pe.TimeClockEntryID
            GROUP BY pe.DayType
            ORDER BY pe.DayType DESC;
            """,
            [c for t in ("Surge", "Ordinary") for c in (
                Check(f"{t} entries", meals[t][0], lambda r, t=t: r.where(DayType=t)["Entries"]),
                Check(f"{t} entries with meal punches", meals[t][1], lambda r, t=t: r.where(DayType=t)["WithMealPunches"]))]
            + [Check("ordinary share", round(share, 3), lambda r: r.where(DayType="Ordinary")["MealShare"], 0.0006)])

    differ = {r[0] for r in d.q("SELECT p.TimeClockEntryID FROM TimeClockPunch p JOIN TimeClockEntry tc ON "
                                "tc.TimeClockEntryID = p.TimeClockEntryID WHERE p.PunchType IN ('Clock In', 'Clock Out') "
                                "AND p.PunchTimestamp IS NOT CASE p.PunchType WHEN 'Clock In' THEN tc.ClockInTime "
                                "ELSE tc.ClockOutTime END")}
    cited = differ & {r[0] for r in d.q("SELECT TimeClockEntryID FROM AttendanceException")}
    s.query("Requirement 2: clock punches whose timestamp differs from their clock entry's times",
            f"Population: clock-in and clock-out punches; expected: {len(differ)} entries, all cited by "
            f"attendance exceptions",
            """
            SELECT COUNT(DISTINCT p.TimeClockEntryID) AS EntriesDiffering,
                COUNT(DISTINCT ae.TimeClockEntryID) AS CitedByExceptions
            FROM TimeClockPunch AS p
                INNER JOIN TimeClockEntry AS tc
                    ON tc.TimeClockEntryID = p.TimeClockEntryID
                LEFT JOIN AttendanceException AS ae
                    ON ae.TimeClockEntryID = p.TimeClockEntryID
            WHERE (p.PunchType = 'Clock In'
                    AND p.PunchTimestamp <> tc.ClockInTime)
                OR (p.PunchType = 'Clock Out'
                    AND p.PunchTimestamp <> tc.ClockOutTime);
            """,
            [Check("entries whose punches differ", len(differ), lambda r: r.value("EntriesDiffering")),
             Check("of them cited by exceptions", len(cited), lambda r: r.value("CitedByExceptions"))])

    leads = sorted({r[0] for r in d.q(notes(b).PLANT + "SELECT julianday(r.RosterDate) - julianday(r.CreatedDate) FROM "
                                      "PlantEntries pe JOIN EmployeeShiftRoster r ON r.EmployeeShiftRosterID = "
                                      "pe.EmployeeShiftRosterID WHERE pe.DayType = 'Surge'")})
    s.query("Requirement 2: the rosters of the surge-day entries, their shifts, creator, and lead time",
            f"Population: surge entries with their rosters; expected: two shifts, {', '.join(n['shifts'])}, "
            f"{n['rostered']:.1f} hours, created by the {n['creator_title']} {n['lead']} days ahead",
            """
            SELECT r.ScheduledStartTime, r.ScheduledEndTime,
                r.ScheduledHours, e.JobTitle AS CreatedBy,
                julianday(r.RosterDate) - julianday(r.CreatedDate)
                    AS DaysAhead,
                COUNT(*) AS Entries
            FROM PlantEntries AS pe
                INNER JOIN EmployeeShiftRoster AS r
                    ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID
                INNER JOIN Employee AS e
                    ON e.EmployeeID = r.CreatedByEmployeeID
            WHERE pe.DayType = 'Surge'
            GROUP BY r.ScheduledStartTime, r.ScheduledEndTime,
                r.ScheduledHours, r.CreatedByEmployeeID, e.JobTitle,
                DaysAhead
            ORDER BY r.ScheduledStartTime;
            """,
            [Check("the rostered shifts", n["shifts"],
                   lambda r: [f"{x[0][:5]}-{x[1][:5]}" for x in r.rows]),
             Check("rostered hours", [n["rostered"]], lambda r: sorted(set(r.col("ScheduledHours")))),
             Check("created by", [n["creator_title"]], lambda r: sorted(set(r.col("CreatedBy")))),
             Check("days ahead", leads, lambda r: sorted(set(r.col("DaysAhead")))),
             Check("surge entries", sum(meals["Surge"][:1]), lambda r: r.total("Entries"))])

    s.query("Requirement 2: who creates the rosters of the Manufacturing employees",
            f"Population: rosters of Manufacturing employees; expected: the {n['creator_title']} alone",
            """
            SELECT r.CreatedByEmployeeID, cr.JobTitle AS CreatedBy,
                COUNT(*) AS Rosters
            FROM EmployeeShiftRoster AS r
                INNER JOIN Employee AS e ON e.EmployeeID = r.EmployeeID
                INNER JOIN CostCenter AS cc
                    ON cc.CostCenterID = e.CostCenterID
                INNER JOIN Employee AS cr
                    ON cr.EmployeeID = r.CreatedByEmployeeID
            WHERE cc.CostCenterName = 'Manufacturing'
            GROUP BY r.CreatedByEmployeeID, cr.JobTitle;
            """,
            [Check("creators", [n["creator_title"]], lambda r: r.col("CreatedBy"))])

    s.query("Requirement 2: minutes of clock time before and after the roster on surge days",
            f"Population: surge entries with their rosters; expected: {', '.join(n['clocks'])}, "
            f"{n['early']} minutes early and {n['late']} late, {n['clocked']} hours against {n['rostered']:.1f}",
            """
            WITH Outside AS (
                SELECT pe.DayType,
                    substr(pe.ClockInTime, 12, 5) || '-'
                        || substr(pe.ClockOutTime, 12, 5) AS ClockPattern,
                    pe.RegularHours + pe.OvertimeHours AS ClockedHours,
                    r.ScheduledHours,
                    ROUND((julianday(r.RosterDate || ' '
                        || r.ScheduledStartTime)
                        - julianday(pe.ClockInTime)) * 1440) AS MinutesEarly,
                    ROUND((julianday(pe.ClockOutTime)
                        - julianday(r.RosterDate || ' '
                        || r.ScheduledEndTime)) * 1440) AS MinutesLate
                FROM PlantEntries AS pe
                    INNER JOIN EmployeeShiftRoster AS r
                        ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID
            )
            SELECT ClockPattern, ClockedHours, ScheduledHours,
                MinutesEarly, MinutesLate, COUNT(*) AS Entries
            FROM Outside
            WHERE DayType = 'Surge'
            GROUP BY ClockPattern, ClockedHours, ScheduledHours,
                MinutesEarly, MinutesLate
            ORDER BY ClockPattern;
            """,
            [Check("clock patterns", n["clocks"], lambda r: r.col("ClockPattern")),
             Check("clocked hours", [n["clocked"]], lambda r: sorted(set(r.col("ClockedHours")))),
             Check("minutes early", [float(n["early"])], lambda r: sorted(set(r.col("MinutesEarly")))),
             Check("minutes late", [float(n["late"])], lambda r: sorted(set(r.col("MinutesLate"))))])

    eq = n["equal"]
    s.query("Requirement 2: rostered hours against the hours clocked, surge days against ordinary days",
            f"Population: PlantEntries with their rosters; expected: equal on {num(eq['Ordinary'][1])} of "
            f"{num(eq['Ordinary'][0])} ordinary entries, on no surge entry",
            """
            SELECT pe.DayType, COUNT(*) AS Entries,
                SUM(CASE WHEN ABS(r.ScheduledHours
                    - (pe.RegularHours + pe.OvertimeHours)) < 0.005
                    THEN 1 ELSE 0 END) AS RosterEqualsClock,
                ROUND(AVG(r.ScheduledHours), 2) AS RosteredHours,
                ROUND(AVG(pe.RegularHours + pe.OvertimeHours), 2)
                    AS ClockedHours
            FROM PlantEntries AS pe
                INNER JOIN EmployeeShiftRoster AS r
                    ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID
            GROUP BY pe.DayType
            ORDER BY pe.DayType DESC;
            """,
            [c for t in ("Surge", "Ordinary") for c in (
                Check(f"{t} entries", eq[t][0], lambda r, t=t: r.where(DayType=t)["Entries"]),
                Check(f"{t} entries rostered for the hours clocked", eq[t][1],
                      lambda r, t=t: r.where(DayType=t)["RosterEqualsClock"]))])

    s.query("Requirement 2: the Off Shift Clocking exceptions against their rosters, to find the rule",
            f"Population: Off Shift Clocking exceptions; expected: {n['n_off']} clock-ins at {n['off_in']} against "
            f"a {n['off_start']} start, {n['threshold']} minutes late",
            """
            SELECT ae.AttendanceExceptionID, ae.MinutesVariance,
                tc.ClockInTime, r.ScheduledStartTime,
                ROUND((julianday(tc.ClockInTime)
                    - julianday(r.RosterDate || ' '
                    || r.ScheduledStartTime)) * 1440) AS MinutesAfterStart
            FROM AttendanceException AS ae
                INNER JOIN TimeClockEntry AS tc
                    ON tc.TimeClockEntryID = ae.TimeClockEntryID
                INNER JOIN EmployeeShiftRoster AS r
                    ON r.EmployeeShiftRosterID = tc.EmployeeShiftRosterID
            WHERE ae.ExceptionType = 'Off Shift Clocking'
            ORDER BY ae.AttendanceExceptionID;
            """,
            [Check("exceptions", d.one("SELECT COUNT(*) FROM AttendanceException WHERE ExceptionType = "
                                       "'Off Shift Clocking'"), len),
             Check("minutes after the scheduled start", [float(n["threshold"])],
                   lambda r: sorted(set(r.col("MinutesAfterStart")))),
             Check("as the exceptions record them", [n["threshold"]], lambda r: sorted(set(r.col("MinutesVariance")))),
             Check("clock-in times", [n["off_in"]], lambda r: sorted({x[2][11:16] for x in r.rows})),
             Check("scheduled starts", [n["off_start"]], lambda r: sorted({x[3][:5] for x in r.rows}))])

    surge_entries = meals["Surge"][0]
    late_surge = d.one(notes(b).PLANT + "SELECT COUNT(*) FROM PlantEntries pe JOIN EmployeeShiftRoster r ON "
                       "r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID WHERE pe.DayType = 'Surge' AND "
                       "ROUND((julianday(pe.ClockInTime) - julianday(r.RosterDate || ' ' || r.ScheduledStartTime)) * 1440) >= ?",
                       n["threshold"])
    s.query("Requirement 2: the Off Shift Clocking rule reperformed on every entry, and the exceptions raised",
            f"Population: PlantEntries with their rosters; expected: no surge entry arrives {n['threshold']} minutes "
            f"late or carries any attendance exception; {num(n['beyond'])} ordinary entries also leave more than "
            f"{n['threshold']} minutes late, in whole minutes, and no plant entry carries an Off Shift Clocking exception",
            """
            WITH RuleMinutes AS (
                SELECT MIN(MinutesVariance) AS Minutes
                FROM AttendanceException
                WHERE ExceptionType = 'Off Shift Clocking'
            ),
            Timing AS (
                SELECT pe.TimeClockEntryID, pe.DayType,
                    ROUND((julianday(pe.ClockInTime)
                        - julianday(r.RosterDate || ' '
                        || r.ScheduledStartTime)) * 1440) AS Arrival,
                    ROUND((julianday(pe.ClockOutTime)
                        - julianday(r.RosterDate || ' '
                        || r.ScheduledEndTime)) * 1440) AS Departure
                FROM PlantEntries AS pe
                    INNER JOIN EmployeeShiftRoster AS r
                        ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID
            ),
            Flagged AS (
                SELECT TimeClockEntryID,
                    MAX(CASE WHEN ExceptionType = 'Off Shift Clocking'
                        THEN 1 ELSE 0 END) AS OffShift
                FROM AttendanceException
                GROUP BY TimeClockEntryID
            )
            SELECT t.DayType, COUNT(*) AS Entries,
                SUM(CASE WHEN t.Arrival >= (SELECT Minutes FROM RuleMinutes)
                    THEN 1 ELSE 0 END) AS LateArrivals,
                SUM(CASE WHEN t.Departure > (SELECT Minutes FROM RuleMinutes)
                    THEN 1 ELSE 0 END) AS LateDepartures,
                COUNT(f.TimeClockEntryID) AS AnyAttendanceException,
                COALESCE(SUM(f.OffShift), 0) AS OffShiftException
            FROM Timing AS t
                LEFT JOIN Flagged AS f
                    ON f.TimeClockEntryID = t.TimeClockEntryID
            GROUP BY t.DayType
            ORDER BY t.DayType DESC;
            """,
            [Check("surge entries arriving late by the rule", late_surge,
                   lambda r: r.where(DayType="Surge")["LateArrivals"]),
             Check("surge entries leaving late by the rule (all of them)", surge_entries,
                   lambda r: r.where(DayType="Surge")["LateDepartures"]),
             Check("surge entries with any attendance exception", d.one(
                 notes(b).PLANT + "SELECT COUNT(ae.AttendanceExceptionID) FROM PlantEntries pe JOIN AttendanceException ae "
                 "ON ae.TimeClockEntryID = pe.TimeClockEntryID WHERE pe.DayType = 'Surge'"),
                   lambda r: r.where(DayType="Surge")["AnyAttendanceException"]),
             Check("ordinary entries with any attendance exception (other types than Off Shift Clocking)",
                   sum(x[1] for x in n["plant_flagged"]), lambda r: r.where(DayType="Ordinary")["AnyAttendanceException"]),
             Check("plant entries with an Off Shift Clocking exception", 0, lambda r: r.total("OffShiftException")),
             Check("ordinary entries leaving more than the rule's minutes late", n["beyond"],
                   lambda r: r.where(DayType="Ordinary")["LateDepartures"])])

    pending = d.one("SELECT COUNT(*) FROM AttendanceException ae JOIN TimeClockEntry tc ON tc.TimeClockEntryID = "
                    "ae.TimeClockEntryID WHERE ae.ExceptionType = 'Paid Without Approved Clock' AND tc.ClockStatus = 'Pending'")
    wrong = d.one("SELECT COUNT(*) FROM AttendanceException ae JOIN TimeClockEntry tc ON tc.TimeClockEntryID = "
                  "ae.TimeClockEntryID WHERE ae.EmployeeID <> tc.EmployeeID")
    s.query("Requirement 2: the operation of the attendance-exception control, review and status by type",
            f"Population: every exception; expected: all {n['exceptions']} Open with no reviewer recorded since "
            f"{d.F}; {pending} Paid Without Approved Clock on Pending entries; {wrong} name the wrong employee",
            """
            SELECT ae.ExceptionType, COUNT(*) AS Exceptions,
                SUM(CASE WHEN ae.Status = 'Open' THEN 1 ELSE 0 END)
                    AS StillOpen,
                COUNT(ae.ReviewedByEmployeeID) AS Reviewed,
                MIN(ae.WorkDate) AS Oldest,
                SUM(CASE WHEN tc.ClockStatus = 'Pending'
                    THEN 1 ELSE 0 END) AS OnPendingEntries,
                SUM(CASE WHEN ae.EmployeeID <> tc.EmployeeID
                    THEN 1 ELSE 0 END) AS NameAnotherEmployee
            FROM AttendanceException AS ae
                INNER JOIN TimeClockEntry AS tc
                    ON tc.TimeClockEntryID = ae.TimeClockEntryID
            GROUP BY ae.ExceptionType
            ORDER BY ae.ExceptionType;
            """,
            [Check("open exceptions", n["exceptions"], lambda r: r.total("StillOpen")),
             Check("reviewed", d.one("SELECT COUNT(ReviewedByEmployeeID) FROM AttendanceException"),
                   lambda r: r.total("Reviewed")),
             Check("oldest exception", d.one("SELECT MIN(WorkDate) FROM AttendanceException"),
                   lambda r: min(r.col("Oldest"))),
             Check("Paid Without Approved Clock on Pending entries", pending,
                   lambda r: r.where(ExceptionType="Paid Without Approved Clock")["OnPendingEntries"]),
             Check("exceptions naming another employee", wrong, lambda r: r.total("NameAnotherEmployee"))])

    s.query("Requirement 2: the calendar status of each surge day",
            f"Population: SurgeDays with WorkCenterCalendar; expected: every surge day a working day; maintenance "
            f"on {n['maintenance']}, reduced capacity on {n['reduced']}",
            """
            SELECT c.ExceptionReason, c.IsWorkingDay,
                COUNT(DISTINCT c.CalendarDate) AS SurgeDays
            FROM SurgeDays AS sd
                INNER JOIN WorkCenterCalendar AS c
                    ON c.CalendarDate = sd.WorkDate
            GROUP BY c.ExceptionReason, c.IsWorkingDay
            ORDER BY c.IsWorkingDay, c.ExceptionReason;
            """,
            [Check("working days only", [1], lambda r: sorted(set(r.col("IsWorkingDay")))),
             Check("surge days with maintenance", n["maintenance"],
                   lambda r: r.where(ExceptionReason="Maintenance")["SurgeDays"]),
             Check("surge days with reduced capacity", n["reduced"],
                   lambda r: r.where(ExceptionReason="Reduced Capacity")["SurgeDays"])])

    load = n["load"]
    s.query("Requirement 2: planned load against available hours, weeks with surge days against other weeks, with "
            "the weeks and work centers planned above capacity",
            f"Population: RoughCutCapacityPlan by Monday week through {n['through']}, available hours once per work "
            f"center and week; expected: surge weeks {', '.join(f'{a:.3f}' for a, _ in load)} against "
            f"{', '.join(f'{x:.3f}' for _, x in load)}; {len(n['over_weeks'])} surge weeks and {n['center_over']} "
            f"work-center weeks above capacity",
            """
            WITH SurgeWeeks AS (
                SELECT date(WorkDate, '-6 days', 'weekday 1') AS WeekStart,
                    COUNT(*) AS SurgeDays
                FROM SurgeDays
                GROUP BY WeekStart
            ),
            Centers AS (
                SELECT BucketWeekStartDate AS WeekStart, WorkCenterID,
                    SUM(PlannedLoadHours) AS PlannedHours,
                    MAX(AvailableHours) AS AvailableHours
                FROM RoughCutCapacityPlan
                GROUP BY BucketWeekStartDate, WorkCenterID
            ),
            Weeks AS (
                SELECT WeekStart, SUM(PlannedHours) AS PlannedHours,
                    SUM(AvailableHours) AS AvailableHours,
                    SUM(CASE WHEN PlannedHours > AvailableHours
                        THEN 1 ELSE 0 END) AS CentersOver
                FROM Centers
                GROUP BY WeekStart
            )
            SELECT strftime('%Y', w.WeekStart) AS PlanYear,
                CASE WHEN sw.WeekStart IS NULL THEN 'No surge days'
                    ELSE 'Surge days' END AS WeekType,
                COUNT(*) AS Weeks,
                ROUND(SUM(w.PlannedHours) / SUM(w.AvailableHours), 3)
                    AS LoadShare,
                SUM(CASE WHEN w.PlannedHours > w.AvailableHours
                    THEN 1 ELSE 0 END) AS WeeksOver,
                SUM(w.CentersOver) AS CenterWeeksOver
            FROM Weeks AS w
                LEFT JOIN SurgeWeeks AS sw ON sw.WeekStart = w.WeekStart
            WHERE w.WeekStart <= (
                SELECT date(MAX(WorkDate), '-6 days', 'weekday 1')
                FROM TimeClockEntry)
            GROUP BY PlanYear, WeekType
            ORDER BY PlanYear, WeekType DESC;
            """,
            [c for y, (a, x) in zip(d.years, load) for c in (
                Check(f"{y} surge weeks", round(a, 3),
                      lambda r, y=y: r.where(PlanYear=str(y), WeekType="Surge days")["LoadShare"], 0.0006),
                Check(f"{y} other weeks", round(x, 3),
                      lambda r, y=y: r.where(PlanYear=str(y), WeekType="No surge days")["LoadShare"], 0.0006))]
            + [Check("surge weeks", n["surge_weeks"], lambda r: sum(x[2] for x in r.rows if x[1] == "Surge days")),
               Check("surge weeks above capacity", len(n["over_weeks"]),
                     lambda r: sum(x[4] for x in r.rows if x[1] == "Surge days")),
               Check("work-center weeks above capacity in surge weeks", n["center_over"],
                     lambda r: sum(x[5] for x in r.rows if x[1] == "Surge days")),
               Check("other weeks above capacity", n["other_over"],
                     lambda r: sum(x[4] for x in r.rows if x[1] == "No surge days"))])

    n_reasons = d.one(notes(b).PLANT + "SELECT COUNT(DISTINCT oa.ReasonCode) FROM PlantEntries pe JOIN OvertimeApproval "
                      "oa ON oa.OvertimeApprovalID = pe.OvertimeApprovalID WHERE pe.DayType = 'Surge'")
    s.query("Requirement 2: the reason codes and approver of the surge-day overtime",
            f"Population: approvals of surge entries; expected: {n['n_reasons']} reason codes, "
            f"{num(n['per_reason'])} each, all approved by the {n['creator_title']}",
            """
            SELECT oa.ReasonCode, oa.ApprovedByEmployeeID,
                ap.JobTitle AS ApprovedBy, COUNT(*) AS Approvals
            FROM PlantEntries AS pe
                INNER JOIN OvertimeApproval AS oa
                    ON oa.OvertimeApprovalID = pe.OvertimeApprovalID
                INNER JOIN Employee AS ap
                    ON ap.EmployeeID = oa.ApprovedByEmployeeID
            WHERE pe.DayType = 'Surge'
            GROUP BY oa.ReasonCode, oa.ApprovedByEmployeeID, ap.JobTitle
            ORDER BY oa.ReasonCode;
            """,
            [Check("reason codes, one approver each", n_reasons, len),
             Check("approvals per reason code", [n["per_reason"]], lambda r: sorted(set(r.col("Approvals")))),
             Check("approved by", [n["creator_title"]], lambda r: sorted(set(r.col("ApprovedBy"))))])

    cite = n["cite"]
    s.query("Requirement 2: overtime approvals that cite an operation already ended before the work date",
            f"Population: approvals of PlantEntries; expected: {num(cite['Surge']['cited'])} of "
            f"{num(cite['Surge']['approvals'])} surge approvals cite one, every one ended; "
            f"{num(cite['Ordinary']['ended'])} of {num(cite['Ordinary']['cited'])} on ordinary days",
            """
            SELECT pe.DayType, COUNT(*) AS Approvals,
                COUNT(oa.WorkOrderOperationID) AS CiteOperation,
                SUM(CASE WHEN op.ActualEndDate < oa.WorkDate
                    THEN 1 ELSE 0 END) AS OperationEnded
            FROM PlantEntries AS pe
                INNER JOIN OvertimeApproval AS oa
                    ON oa.OvertimeApprovalID = pe.OvertimeApprovalID
                LEFT JOIN WorkOrderOperation AS op
                    ON op.WorkOrderOperationID = oa.WorkOrderOperationID
            GROUP BY pe.DayType
            ORDER BY pe.DayType DESC;
            """,
            [c for t in ("Surge", "Ordinary") for k, col in (("approvals", "Approvals"), ("cited", "CiteOperation"),
                                                              ("ended", "OperationEnded"))
             for c in [Check(f"{t} {k}", cite[t][k], lambda r, t=t, col=col: r.where(DayType=t)[col])]])

    s.query("Requirement 2: surge days by day of the week",
            f"Population: SurgeDays; expected: {', '.join(f'{w} {k}' for w, k in n['weekdays'])}",
            """
            SELECT strftime('%w', WorkDate) AS DayNumber,
                CASE strftime('%w', WorkDate)
                    WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'
                    WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday'
                    WHEN '5' THEN 'Friday' ELSE 'Weekend'
                END AS Weekday,
                COUNT(*) AS SurgeDays
            FROM SurgeDays
            GROUP BY DayNumber
            ORDER BY DayNumber;
            """,
            [Check("surge days by weekday", [[w, k] for w, k in n["weekdays"] if k],
                   lambda r: [[x[1], x[2]] for x in r.rows])])

    absences = [r[0] for r in d.q("SELECT DISTINCT c.CostCenterName FROM EmployeeAbsence a JOIN Employee e ON "
                                  "e.EmployeeID = a.EmployeeID JOIN CostCenter c ON c.CostCenterID = e.CostCenterID")]
    s.query("Requirement 2: absences recorded by cost center, the evidence that could explain attendance",
            "Population: EmployeeAbsence; expected: none in Manufacturing in any year",
            """
            SELECT cc.CostCenterName, COUNT(*) AS Absences,
                MIN(a.AbsenceDate) AS FirstDate,
                MAX(a.AbsenceDate) AS LastDate
            FROM EmployeeAbsence AS a
                INNER JOIN Employee AS e ON e.EmployeeID = a.EmployeeID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
            GROUP BY cc.CostCenterID, cc.CostCenterName
            ORDER BY cc.CostCenterName;
            """,
            [Check("cost centers with absences", sorted(absences), lambda r: sorted(r.col("CostCenterName"))),
             Check("absences in Manufacturing", "Manufacturing" in absences,
                   lambda r: "Manufacturing" in r.col("CostCenterName"))])

    ow = n["over_weeks"]
    over_text = " and ".join(f"{w} at {v:.1%}" for w, v in ow)
    s.answer("Requirement 2", f"""
        Corroboration matrix. Supports means agreement with a specified recorded feature, such as attendance or a
        timestamp, and does not establish that all {n['clocked']:.1f} recorded hours were worked. Supports the hours,
        though both records come from the time clock and so show only its internal consistency: every hourly employee present on every surge day ({sg['employees']:.0f} people a day,
        against {od['employees']:.1f} on ordinary days, though {od['all_present']} of {od['days']} ordinary days also had
        all {n['plant']}, so attendance says little); badge punches on every entry, with meal punches on every surge
        entry. Contradicts or leaves unexplained: about {sg['clock_ins']:.0f} clock-in times a day for the whole plant, so
        {sg['largest_min']} or {sg['largest_max']} employees share one timestamp (at most {od['largest_max']} on an
        ordinary day); overtime in no roster (every surge entry rostered for {n['rostered']:.0f} hours on
        {', '.join(n['shifts'])}, clocked {n['clocks'][0]} or {n['clocks'][1]}); approvals that cite operations already
        finished (every one of the {num(cite['Surge']['cited'])} surge-day approvals that cite an operation); planned load
        lower in surge weeks than in the other weeks on average, although {len(ow)} of the {n['surge_weeks']} surge weeks
        ({over_text}) and {n['center_over']} work-center weeks were planned above capacity, as were {n['other_over']} of
        the other weeks, so the plan does not explain a pattern that recurs across the plant; overtime on days with
        maintenance ({n['maintenance']}) or reduced capacity ({n['reduced']}); and the output (surge weeks completed more,
        not in proportion to their hours, and the weeks after completed less, Requirement 3). Silent: absences, none
        recorded in Manufacturing in any year.

        Independence. The punches and the clock entries are one system (the punches repeat the entry's timestamps).
        The rosters and the overtime approvals come from the same manager, the {n['creator_title']}, who creates every
        manufacturing roster and approved every surge-day approval on the work date. The calendar, the capacity plan,
        and the output lie outside the clock trail, but the records do not show who keeps or can change them, so their
        independence from the {n['creator_title']} and from the time clock is judged separately, and a record whose
        provenance is not shown stays not established. None of them supports the hours as recorded.

        The control. The {n['n_off']} Off Shift Clocking exceptions are consistent with a rule that flags arrivals
        {n['threshold']} minutes or more after the scheduled start, but {n['n_off']} examples cannot show its threshold,
        whether it also tests departures, or whether approved overtime is exempt. All {n['n_off']} belong to
        {' and '.join(n['off_centers']).lower()} employees, so no plant entry carries one. The system's configuration and
        its change history would show them. On that reading, surge arrivals {n['early']} minutes early and departures
        {n['late'] // 60} hours late with approved overtime could not be flagged, and nothing compares overtime with a
        roster or a plan made in advance, a weakness of design to confirm against the configuration. All
        {n['exceptions']} exceptions are Open with no reviewer or review date recorded in up to {n['years']} years, among
        them {n['n_pwac']} Paid Without Approved Clock and {n['wrong']} that name the wrong employee, a failure of
        operation in the review the records show, unless evidence of a review exists outside them.

        Two explanations fit the records: the hours were worked, and the time was entered for the plant as a block,
        which breaks the timekeeping control but not the pay; or the hours were not worked as recorded. Evidence outside
        the database would tell them apart: building access or gate logs, statements of supervisors and employees,
        security video, machine-run or utility data, and the timekeeping system's own log of who entered or edited the
        punches, each checked for who controls it. Until then the memo should call the hours unsupported.""")


# --- Requirement 3: what the hours produced and what they cost -------------------------------------------------------

def output_cte(name: str = "Output", cut: bool = True) -> str:
    where = f"\n    WHERE pc.CompletionDate <= {LAST_WORK}" if cut else ""
    return (f"{name} AS (\n    SELECT strftime('%Y', pc.CompletionDate) AS WorkYear,\n"
            f"        SUM({STD_HOURS})\n            AS StandardHours\n" + indent(COMPLETIONS, 4) + where
            + "\n    GROUP BY WorkYear\n)")


def r3(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r3")
    ys = n["ys"]
    s.query("Requirement 3: hours clocked against the standard hours of the output, by work year",
            f"Population: PlantEntries; completions up to {n['cutoff']}, the last day with time records; expected: "
            f"{', '.join(f'{y['ratio']:.3f}' for y in ys)} hours per standard hour",
            f"""
            WITH {sub(output_cte(), 12)},
            Hours AS (
                SELECT strftime('%Y', WorkDate) AS WorkYear,
                    SUM(RegularHours + OvertimeHours) AS ClockedHours,
                    SUM(CASE WHEN DayType = 'Surge'
                        THEN OvertimeHours ELSE 0 END) AS SurgeOvertime,
                    SUM(CASE WHEN DayType = 'Ordinary'
                        THEN OvertimeHours ELSE 0 END) AS OtherOvertime
                FROM PlantEntries
                GROUP BY WorkYear
            )
            SELECT h.WorkYear, ROUND(h.ClockedHours, 0) AS ClockedHours,
                ROUND(o.StandardHours, 0) AS StandardHours,
                ROUND(h.ClockedHours / o.StandardHours, 3)
                    AS HoursPerStandardHour,
                ROUND(h.SurgeOvertime, 0) AS SurgeOvertime,
                ROUND(h.OtherOvertime, 0) AS OtherOvertime
            FROM Hours AS h
                INNER JOIN Output AS o ON o.WorkYear = h.WorkYear
            ORDER BY h.WorkYear;
            """,
            [c for y in ys for c in (
                Check(f"{y['year']} hours clocked", y["hours"], lambda r, y=y: r.where(WorkYear=str(y["year"]))["ClockedHours"], 0.5),
                Check(f"{y['year']} standard hours", y["std"], lambda r, y=y: r.where(WorkYear=str(y["year"]))["StandardHours"], 0.5),
                Check(f"{y['year']} hours per standard hour", round(y["ratio"], 3),
                      lambda r, y=y: r.where(WorkYear=str(y["year"]))["HoursPerStandardHour"], 0.0006),
                Check(f"{y['year']} surge overtime", y["surge"]["overtime"],
                      lambda r, y=y: r.where(WorkYear=str(y["year"]))["SurgeOvertime"], 0.5),
                Check(f"{y['year']} other overtime", y["ordinary"]["overtime"],
                      lambda r, y=y: r.where(WorkYear=str(y["year"]))["OtherOvertime"], 0.5))])

    s.query("Requirement 3: the December values of MonthlyLaborEfficiency (Tutorial 11.3), the same measure on labor "
            "time",
            f"Population: the view; expected: trailing twelve months {', '.join(f'{y['ratio']:.2f}' for y in ys)}, "
            f"as the time clock gives; the {d.C} row provisional, its indirect time ending {context(b, 'r4')['ind_end']}",
            """
            SELECT Month, TTMDirect, TTMIndirect, TTMTotal
            FROM MonthlyLaborEfficiency
            WHERE Month LIKE '%-12'
            ORDER BY Month;
            """,
            [Check("Decembers", [f"{y['year']}-12" for y in ys], lambda r: r.col("Month"))]
            + [Check(f"{y['year']} TTMTotal against the time clock, to two decimals", round(y["ratio"], 2),
                     lambda r, y=y: r.where(Month=f"{y['year']}-12")["TTMTotal"], 0.0051) for y in ys])

    s.query("Requirement 3: Monday weeks of hours and output saved as a view, with the output of up to six weeks that "
            "follow",
            f"Population: PlantEntries and completions up to {n['cutoff']}, by Monday week through the week of "
            f"{n['last_day']}, {d.C}; expected: the view PlantWeeks",
            f"""
            DROP VIEW IF EXISTS PlantWeeks;
            CREATE VIEW PlantWeeks AS
            WITH Hours AS (
                SELECT date(WorkDate, '-6 days', 'weekday 1') AS WeekStart,
                    SUM(RegularHours + OvertimeHours) AS ClockedHours,
                    COUNT(DISTINCT CASE WHEN DayType = 'Surge'
                        THEN WorkDate END) AS SurgeDays
                FROM PlantEntries
                GROUP BY WeekStart
            ),
            Output AS (
                SELECT date(pc.CompletionDate, '-6 days', 'weekday 1')
                        AS WeekStart,
                    SUM({STD_HOURS}) AS StandardHours
                {sub(COMPLETIONS, 16)}
                WHERE pc.CompletionDate <= {LAST_WORK}
                GROUP BY WeekStart
            )
            SELECT h.WeekStart, h.ClockedHours, h.SurgeDays,
                COALESCE(o.StandardHours, 0) AS StandardHours,
                AVG(COALESCE(o.StandardHours, 0)) OVER (
                    ORDER BY h.WeekStart
                    ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING
                ) AS NextSixWeeks,
                COUNT(*) OVER (
                    ORDER BY h.WeekStart
                    ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING
                ) AS FollowingWeeks
            FROM Hours AS h
                LEFT JOIN Output AS o ON o.WeekStart = h.WeekStart
            WHERE h.WeekStart <= (
                SELECT date(MAX(WorkDate), '-6 days', 'weekday 1')
                FROM TimeClockEntry);
            """)

    weeks = notes(b).weeks(d)
    current = [w for w in weeks if w["week"][:4] == str(d.C)]
    groups = {}
    for w in current:
        groups.setdefault(w["surge"], []).append(w)
    group = {k: notes(b).week_group(v) for k, v in groups.items()}
    s.query(f"Requirement 3: the weeks of {d.C} grouped by their number of surge days",
            f"Population: PlantWeeks, {d.C}; expected: {group[0]['n']} weeks without surge days at "
            f"{num(group[0]['hours'])} hours and {num(group[0]['std'])} standard hours",
            f"""
            SELECT SurgeDays, COUNT(*) AS Weeks,
                ROUND(AVG(ClockedHours), 0) AS ClockedHours,
                ROUND(AVG(StandardHours), 0) AS StandardHours,
                ROUND(SUM(StandardHours) / SUM(ClockedHours), 2)
                    AS StandardPerClocked,
                ROUND(AVG(NextSixWeeks), 0) AS NextSixWeeks
            FROM PlantWeeks
            WHERE {year_between(d.C, 'WeekStart')}
            GROUP BY SurgeDays
            ORDER BY SurgeDays;
            """,
            [Check("surge days per week", sorted(group), lambda r: r.col("SurgeDays"))]
            + [c for k, g in sorted(group.items()) for c in (
                Check(f"{k} surge days: weeks", g["n"], lambda r, k=k: r.where(SurgeDays=k)["Weeks"]),
                Check(f"{k} surge days: hours", g["hours"], lambda r, k=k: r.where(SurgeDays=k)["ClockedHours"], 0.5),
                Check(f"{k} surge days: standard hours", g["std"], lambda r, k=k: r.where(SurgeDays=k)["StandardHours"], 0.5),
                Check(f"{k} surge days: next six weeks", g["next"], lambda r, k=k: r.where(SurgeDays=k)["NextSixWeeks"], 0.5))])

    other, surge, later = n["other"], n["surge"], n["later"]
    s.query("Requirement 3: weeks with surge days against weeks without, and the weeks that follow them",
            f"Population: PlantWeeks, {d.C}, and every week without surge days from {n['since']}; expected: "
            f"{surge['n']} surge weeks at {num(surge['hours'])} and {num(surge['std'])}, following weeks "
            f"{num(surge['next'])} against {num(other['next'])}; {surge['short'] + other['short']} frames short of six weeks",
            f"""
            SELECT '{d.C}' AS Period,
                CASE WHEN SurgeDays > 0 THEN 'Surge days'
                    ELSE 'No surge days' END AS WeekType,
                COUNT(*) AS Weeks,
                ROUND(AVG(ClockedHours), 0) AS ClockedHours,
                ROUND(AVG(StandardHours), 0) AS StandardHours,
                ROUND(SUM(StandardHours) / SUM(ClockedHours), 2)
                    AS StandardPerClocked,
                ROUND(AVG(NextSixWeeks), 0) AS NextSixWeeks,
                SUM(CASE WHEN FollowingWeeks < 6 THEN 1 ELSE 0 END)
                    AS ShortFrames
            FROM PlantWeeks
            WHERE {year_between(d.C, 'WeekStart')}
            GROUP BY WeekType
            UNION ALL
            SELECT 'After the first surge week', 'No surge days', COUNT(*),
                ROUND(AVG(ClockedHours), 0), ROUND(AVG(StandardHours), 0),
                ROUND(SUM(StandardHours) / SUM(ClockedHours), 2),
                ROUND(AVG(NextSixWeeks), 0),
                SUM(CASE WHEN FollowingWeeks < 6 THEN 1 ELSE 0 END)
            FROM PlantWeeks
            WHERE SurgeDays = 0
                AND WeekStart > (
                    SELECT MIN(WeekStart) FROM PlantWeeks WHERE SurgeDays > 0)
            ORDER BY Period, WeekType;
            """,
            [c for label, (p, t), g in (("surge weeks", (str(d.C), "Surge days"), surge),
                                         ("other weeks", (str(d.C), "No surge days"), other),
                                         ("weeks without surge days since the first", ("After the first surge week",
                                                                                       "No surge days"), later))
             for c in (
                Check(f"{label}: weeks", g["n"], lambda r, p=p, t=t: r.where(Period=p, WeekType=t)["Weeks"]),
                Check(f"{label}: hours", g["hours"], lambda r, p=p, t=t: r.where(Period=p, WeekType=t)["ClockedHours"], 0.5),
                Check(f"{label}: standard hours", g["std"],
                      lambda r, p=p, t=t: r.where(Period=p, WeekType=t)["StandardHours"], 0.5),
                Check(f"{label}: standard per clocked hour", round(g["ratio"], 2),
                      lambda r, p=p, t=t: r.where(Period=p, WeekType=t)["StandardPerClocked"], 0.0051),
                Check(f"{label}: next six weeks", g["next"],
                      lambda r, p=p, t=t: r.where(Period=p, WeekType=t)["NextSixWeeks"], 0.5),
                Check(f"{label}: frames short of six weeks", g["short"],
                      lambda r, p=p, t=t: r.where(Period=p, WeekType=t)["ShortFrames"]))])

    s.query(f"Requirement 3: the weeks of {d.C} over six complete following weeks, surge weeks against the others",
            f"Population: PlantWeeks, {d.C}, with six following weeks that end before the last, partial week; expected: "
            f"{surge['n_six']} surge weeks at {surge['six']:,.2f} standard hours and {other['n_six']} other weeks at "
            f"{other['six']:,.2f}",
            f"""
            SELECT CASE WHEN SurgeDays > 0 THEN 'Surge'
                    ELSE 'Ordinary' END AS WeekType,
                COUNT(*) AS Weeks,
                ROUND(AVG(NextSixWeeks), 2) AS FollowingOutput
            FROM PlantWeeks
            WHERE {year_between(d.C, 'WeekStart')}
                AND FollowingWeeks = 6
                AND date(WeekStart, '+42 days') < (
                    SELECT MAX(WeekStart) FROM PlantWeeks)
            GROUP BY WeekType
            ORDER BY WeekType DESC;
            """,
            [Check("surge weeks with six complete following weeks", surge["n_six"], lambda r: r.where(WeekType="Surge")["Weeks"]),
             Check("other weeks with six complete following weeks", other["n_six"], lambda r: r.where(WeekType="Ordinary")["Weeks"]),
             Check("output after surge weeks", round(surge["six"], 2), lambda r: r.where(WeekType="Surge")["FollowingOutput"], 0.005),
             Check("output after other weeks", round(other["six"], 2), lambda r: r.where(WeekType="Ordinary")["FollowingOutput"],
                   0.005)])

    weekend = d.one(f"SELECT COUNT(*) FROM ProductionCompletion WHERE strftime('%w', CompletionDate) IN ('0', '6') "
                    f"AND substr(CompletionDate, 1, 4) = '{d.C}'")
    s.query("Requirement 3: what limits the weekly comparison, lead times and completions dated on weekends",
            f"Population: work orders closed and completions of {d.C}; expected: lead time about "
            f"{n['lead']:.0f} days; {weekend} completions on weekends",
            f"""
            SELECT
                (SELECT ROUND(AVG(julianday(CompletedDate)
                    - julianday(ReleasedDate)), 1)
                 FROM WorkOrder
                 WHERE {year_between(d.C, 'ClosedDate')}) AS LeadTimeDays,
                (SELECT COUNT(*)
                 FROM ProductionCompletion
                 WHERE {year_between(d.C, 'CompletionDate')}
                     AND strftime('%w', CompletionDate) IN ('0', '6'))
                    AS WeekendCompletions,
                (SELECT COUNT(*)
                 FROM ProductionCompletion
                 WHERE {year_between(d.C, 'CompletionDate')})
                    AS Completions;
            """,
            [Check("lead time in days", round(n["lead"], 1), lambda r: r.value("LeadTimeDays"), 0.051),
             Check("completions on weekends", weekend, lambda r: r.value("WeekendCompletions"))])

    s.query("Requirement 3: the regular capacity the ordinary days used, by employee and day, against the surge-day "
            "overtime",
            "Population: PlantEntries summed by employee and work date; expected: unused straight time "
            f"{', '.join(num(y['ordinary']['unused_day']) for y in ys)} hours against surge overtime "
            f"{', '.join(num(y['surge']['overtime']) for y in ys)}",
            """
            WITH EmployeeDays AS (
                SELECT EmployeeID, WorkDate, DayType,
                    SUM(RegularHours) AS RegularHours,
                    SUM(OvertimeHours) AS OvertimeHours,
                    SUM(RegularHours + OvertimeHours) AS ClockedHours
                FROM PlantEntries
                GROUP BY EmployeeID, WorkDate, DayType
            )
            SELECT strftime('%Y', WorkDate) AS WorkYear,
                ROUND(AVG(CASE WHEN DayType = 'Ordinary'
                    THEN ClockedHours END), 2) AS OrdinaryHoursPerDay,
                ROUND(SUM(CASE WHEN DayType = 'Ordinary' AND RegularHours < 8
                    THEN 8 - RegularHours ELSE 0 END), 0)
                    AS UnusedStraightTime,
                ROUND(SUM(CASE WHEN DayType = 'Surge'
                    THEN OvertimeHours ELSE 0 END), 0) AS SurgeOvertime
            FROM EmployeeDays
            GROUP BY WorkYear
            ORDER BY WorkYear;
            """,
            [c for y in ys for c in (
                Check(f"{y['year']} hours per ordinary employee-day", round(y["ordinary"]["per_day"], 2),
                      lambda r, y=y: r.where(WorkYear=str(y["year"]))["OrdinaryHoursPerDay"], 0.0051),
                Check(f"{y['year']} unused straight time", y["ordinary"]["unused_day"],
                      lambda r, y=y: r.where(WorkYear=str(y["year"]))["UnusedStraightTime"], 0.5),
                Check(f"{y['year']} surge overtime", y["surge"]["overtime"],
                      lambda r, y=y: r.where(WorkYear=str(y["year"]))["SurgeOvertime"], 0.5))])

    burden = n["burden"]
    cur = ys[-1]
    s.query("Requirement 3: the cost of the surge-day overtime at base rates, the premium and the full cost, with "
            "the employer's taxes and benefits",
            f"Population: surge entries by work year, burden from the Manufacturing registers of the pay year; "
            f"expected: {d.C} premium {money(cur['surge_premium'] * (1 + burden))} and full cost "
            f"{money(cur['surge_full'] * (1 + burden))} with burden",
            """
            WITH Burden AS (
                SELECT pp.FiscalYear,
                    ROUND(SUM(pr.EmployerPayrollTax + pr.EmployerBenefits)
                        / SUM(pr.GrossPay), 4) AS BurdenRate
                FROM PayrollRegister AS pr
                    INNER JOIN PayrollPeriod AS pp
                        ON pp.PayrollPeriodID = pr.PayrollPeriodID
                    INNER JOIN CostCenter AS cc
                        ON cc.CostCenterID = pr.CostCenterID
                WHERE cc.CostCenterName = 'Manufacturing'
                GROUP BY pp.FiscalYear
            ),
            Surge AS (
                SELECT CAST(strftime('%Y', WorkDate) AS INTEGER) AS WorkYear,
                    SUM(OvertimeHours) AS OvertimeHours,
                    SUM(OvertimeHours * BaseHourlyRate) AS StraightTimeCost
                FROM PlantEntries
                WHERE DayType = 'Surge'
                GROUP BY WorkYear
            )
            SELECT s.WorkYear, ROUND(s.OvertimeHours, 0) AS OvertimeHours,
                b.BurdenRate,
                ROUND(s.StraightTimeCost * 0.5, 2) AS Premium,
                ROUND(s.StraightTimeCost * 0.5 * (1 + b.BurdenRate), 2)
                    AS PremiumWithBurden,
                ROUND(s.StraightTimeCost * 1.5, 2) AS FullCost,
                ROUND(s.StraightTimeCost * 1.5 * (1 + b.BurdenRate), 2)
                    AS FullCostWithBurden
            FROM Surge AS s
                INNER JOIN Burden AS b ON b.FiscalYear = s.WorkYear
            ORDER BY s.WorkYear;
            """,
            [c for y in ys for c in (
                Check(f"{y['year']} premium", y["surge_premium"], lambda r, y=y: r.where(WorkYear=y["year"])["Premium"]),
                Check(f"{y['year']} full cost", y["surge_full"], lambda r, y=y: r.where(WorkYear=y["year"])["FullCost"]))]
            + [Check(f"{d.C} burden", burden, lambda r: r.where(WorkYear=d.C)["BurdenRate"], 0.00005),
               Check(f"{d.C} premium with burden", round(cur["surge_premium"] * (1 + burden), 2),
                     lambda r: r.where(WorkYear=d.C)["PremiumWithBurden"]),
               Check(f"{d.C} full cost with burden", round(cur["surge_full"] * (1 + burden), 2),
                     lambda r: r.where(WorkYear=d.C)["FullCostWithBurden"])])

    lf, lc = n["lf"], n["lc"]
    lp = notes(b).ledger(d)[d.P]
    s.query("Requirement 3: accounts 1090 and 5080 by fiscal year saved as a view, the ledger lines of the bridge",
            "Population: GLEntry, 1090 and 5080, closes excluded, with WorkOrderClose's material variance; expected: "
            "the view PlantLedger",
            f"""
            DROP VIEW IF EXISTS PlantLedger;
            CREATE VIEW PlantLedger AS
            WITH Ledger AS (
                SELECT gl.FiscalYear,
                    SUM(CASE WHEN a.AccountNumber = 1090
                        AND gl.SourceDocumentType = 'PayrollSummary'
                        THEN gl.Debit - gl.Credit ELSE 0 END) AS Payroll,
                    SUM(CASE WHEN a.AccountNumber = 1090
                        AND gl.SourceDocumentType = 'JournalEntry'
                        THEN gl.Debit - gl.Credit ELSE 0 END) AS JournalEntries,
                    SUM(CASE WHEN a.AccountNumber = 1090
                        AND gl.SourceDocumentType = 'ProductionCompletion'
                        THEN gl.Credit - gl.Debit ELSE 0 END) AS Released,
                    SUM(CASE WHEN a.AccountNumber = 1090
                        THEN gl.Debit - gl.Credit ELSE 0 END) AS ChangeIn1090,
                    SUM(CASE WHEN a.AccountNumber = 5080
                        AND gl.SourceDocumentType <> 'WorkOrderClose'
                        THEN gl.Debit - gl.Credit ELSE 0 END) AS DirectTo5080,
                    SUM(CASE WHEN a.AccountNumber = 5080
                        THEN gl.Debit - gl.Credit ELSE 0 END) AS Variance5080,
                    COUNT(DISTINCT CASE WHEN a.AccountNumber = 1090
                        AND gl.SourceDocumentType = 'PayrollSummary'
                        THEN gl.PostingDate END) AS PayDates
                FROM GLEntry AS gl
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                WHERE a.AccountNumber IN (1090, 5080)
                    AND gl.VoucherNumber NOT IN (
                        {sub(CLOSES, 24)})
                GROUP BY gl.FiscalYear
            ),
            Material AS (
                SELECT CAST(strftime('%Y', CloseDate) AS INTEGER) AS FiscalYear,
                    SUM(MaterialVarianceAmount) AS MaterialVariance
                FROM WorkOrderClose
                GROUP BY FiscalYear
            )
            SELECT l.FiscalYear, l.Payroll, l.JournalEntries, l.Released,
                l.ChangeIn1090, m.MaterialVariance, l.DirectTo5080,
                l.Variance5080, l.PayDates
            FROM Ledger AS l
                INNER JOIN Material AS m ON m.FiscalYear = l.FiscalYear;
            """)

    s.query("Requirement 3: the ledger lines of 5080 by fiscal year",
            f"Population: the view PlantLedger; expected: 5080 {money(lf['v5080'])} in {d.F} and "
            f"{money(lc['v5080'])} in {d.C}",
            """
            SELECT FiscalYear, ROUND(Payroll, 2) AS Payroll,
                ROUND(JournalEntries, 2) AS JournalEntries,
                ROUND(Released, 2) AS StandardReleased,
                ROUND(ChangeIn1090, 2) AS ChangeIn1090,
                ROUND(MaterialVariance, 2) AS MaterialVariance,
                ROUND(DirectTo5080, 2) AS DirectTo5080,
                ROUND(Variance5080, 2) AS Variance5080,
                ROUND(Payroll + JournalEntries - Released - ChangeIn1090, 2)
                    AS ConversionVariance,
                ROUND(Payroll + JournalEntries - Released - ChangeIn1090
                    + MaterialVariance + DirectTo5080 - Variance5080, 2)
                    AS Unexplained
            FROM PlantLedger
            ORDER BY FiscalYear;
            """,
            [c for y, l in ((d.F, lf), (d.P, lp), (d.C, lc)) for k, col in (
                ("payroll", "Payroll"), ("je", "JournalEntries"), ("released", "StandardReleased"),
                ("change", "ChangeIn1090"), ("material", "MaterialVariance"), ("direct", "DirectTo5080"),
                ("v5080", "Variance5080"))
             for c in [Check(f"{y} {col}", l[k], lambda r, y=y, col=col: r.where(FiscalYear=y)[col])]]
            + [Check(f"{d.C} conversion variance, as WorkOrderClose records it", lc["conversion"],
                     lambda r: r.where(FiscalYear=d.C)["ConversionVariance"]),
               Check("unexplained, every year", [0.0] * len(d.years), lambda r: [abs(v) for v in r.col("Unexplained")])])

    br = n["bridge"]
    s.query(f"Requirement 3: the bridge of 5080 from fiscal {d.F} to fiscal {d.C}",
            f"Population: the view PlantLedger; expected: growth {money(br['delta'])} = payroll "
            f"{money(br['payroll'])} {money(br['je'])} {money(br['released'])} {money(br['change'])} "
            f"{money(br['material'])} {money(br['direct'])}",
            f"""
            SELECT ROUND(c.Variance5080 - f.Variance5080, 2) AS Growth5080,
                ROUND(c.Payroll - f.Payroll, 2) AS Payroll,
                ROUND(c.JournalEntries - f.JournalEntries, 2)
                    AS JournalEntries,
                ROUND(f.Released - c.Released, 2) AS StandardReleased,
                ROUND(f.ChangeIn1090 - c.ChangeIn1090, 2) AS ChangeIn1090,
                ROUND(c.MaterialVariance - f.MaterialVariance, 2)
                    AS MaterialVariance,
                ROUND(c.DirectTo5080 - f.DirectTo5080, 2) AS DirectPostings
            FROM PlantLedger AS f
                INNER JOIN PlantLedger AS c
                    ON f.FiscalYear = {d.F} AND c.FiscalYear = {d.C};
            """,
            [Check("growth of 5080", br["delta"], lambda r: r.value("Growth5080")),
             Check("payroll charged to 1090", br["payroll"], lambda r: r.value("Payroll")),
             Check("journal entries charged to 1090", br["je"], lambda r: r.value("JournalEntries")),
             Check("standard cost released", br["released"], lambda r: r.value("StandardReleased")),
             Check("change in 1090", br["change"], lambda r: r.value("ChangeIn1090")),
             Check("material variance", br["material"], lambda r: r.value("MaterialVariance")),
             Check("direct postings", br["direct"], lambda r: r.value("DirectPostings")),
             Check("the lines add up to the growth", 0.0,
                   lambda r: round(sum(r.rows[0][1:]) - r.rows[0][0], 2))])

    s.query(f"Requirement 3: the postings made directly to 5080, outside the work order closes",
            f"Population: GLEntry, 5080, closes excluded; expected: {d.F}'s {n['pay_month']} payroll "
            f"{money(n['pay_amount'])} and {n['je']} {money(n['je_amount'])}",
            f"""
            SELECT gl.FiscalYear, gl.SourceDocumentType, gl.VoucherNumber,
                gl.PostingDate, ROUND(SUM(gl.Debit - gl.Credit), 2) AS Amount
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE a.AccountNumber = 5080
                AND gl.SourceDocumentType <> 'WorkOrderClose'
                AND gl.VoucherNumber NOT IN (
                    {sub(CLOSES, 20)})
            GROUP BY gl.FiscalYear, gl.SourceDocumentType,
                gl.VoucherNumber, gl.PostingDate
            ORDER BY gl.PostingDate;
            """,
            [Check("payroll posted to 5080", n["pay_amount"],
                   lambda r: r.where(SourceDocumentType="PayrollSummary")["Amount"]),
             Check("journal entry posted to 5080", [n["je"], n["je_amount"]],
                   lambda r: [r.where(SourceDocumentType="JournalEntry")[k] for k in ("VoucherNumber", "Amount")]),
             Check("total", lf["direct"], lambda r: round(r.total("Amount"), 2))])

    rate = n["rate"]
    s.query("Requirement 3: three measures of the payroll line, the calendar, the hours beyond the work, and the "
            "surge premium",
            f"Population: PlantLedger, PlantEntries, completions to the last day with time records; expected: "
            f"{money(n['calendar'])} + {num(n['beyond_cost'])} + {num(n['premium_growth'])} = {num(n['together'])}, "
            f"{num(n['excess'])} above the payroll line",
            f"""
            WITH {sub(output_cte(), 12)},
            Hours AS (
                SELECT strftime('%Y', WorkDate) AS WorkYear,
                    SUM(RegularHours + OvertimeHours) AS ClockedHours,
                    SUM(CASE WHEN DayType = 'Surge'
                        THEN OvertimeHours * BaseHourlyRate ELSE 0 END)
                        * 0.5 AS SurgePremium,
                    ROUND(SUM((RegularHours + OvertimeHours) * BaseHourlyRate)
                        / SUM(RegularHours + OvertimeHours), 4) AS Rate
                FROM PlantEntries
                GROUP BY WorkYear
            ),
            Burden AS (
                SELECT ROUND(SUM(pr.EmployerPayrollTax + pr.EmployerBenefits)
                        / SUM(pr.GrossPay), 4) AS BurdenRate
                FROM PayrollRegister AS pr
                    INNER JOIN PayrollPeriod AS pp
                        ON pp.PayrollPeriodID = pr.PayrollPeriodID
                    INNER JOIN CostCenter AS cc
                        ON cc.CostCenterID = pr.CostCenterID
                WHERE cc.CostCenterName = 'Manufacturing'
                    AND pp.FiscalYear = {d.C}
            ),
            Measures AS (
                SELECT lc.Payroll - lf.Payroll AS PayrollLine,
                    (lc.PayDates - lf.PayDates) * lf.Payroll / lf.PayDates
                        AS Calendar,
                    hc.ClockedHours
                        - hf.ClockedHours / ofy.StandardHours * oc.StandardHours
                        AS HoursBeyond,
                    hc.Rate * (1 + (SELECT BurdenRate FROM Burden))
                        AS RateWithBurden,
                    (hc.SurgePremium - hf.SurgePremium)
                        * (1 + (SELECT BurdenRate FROM Burden)) AS PremiumGrowth
                FROM PlantLedger AS lf
                    INNER JOIN PlantLedger AS lc ON lc.FiscalYear = {d.C}
                    INNER JOIN Hours AS hf ON hf.WorkYear = '{d.F}'
                    INNER JOIN Hours AS hc ON hc.WorkYear = '{d.C}'
                    INNER JOIN Output AS ofy ON ofy.WorkYear = '{d.F}'
                    INNER JOIN Output AS oc ON oc.WorkYear = '{d.C}'
                WHERE lf.FiscalYear = {d.F}
            )
            SELECT ROUND(PayrollLine, 2) AS PayrollLine,
                ROUND(Calendar, 2) AS Calendar,
                ROUND(HoursBeyond, 0) AS HoursBeyond,
                ROUND(HoursBeyond * RateWithBurden, 0) AS HoursBeyondCost,
                ROUND(PremiumGrowth, 0) AS PremiumGrowth,
                ROUND(Calendar + HoursBeyond * RateWithBurden
                    + PremiumGrowth, 0) AS Together,
                ROUND(Calendar + HoursBeyond * RateWithBurden
                    + PremiumGrowth - PayrollLine, 0) AS Excess
            FROM Measures;
            """,
            [Check("payroll line", br["payroll"], lambda r: r.value("PayrollLine")),
             Check("calendar", n["calendar"], lambda r: r.value("Calendar")),
             Check("hours beyond the 2024 level", n["hours_beyond"], lambda r: r.value("HoursBeyond"), 0.5),
             Check("their cost", n["beyond_cost"], lambda r: r.value("HoursBeyondCost"), 0.5),
             Check("growth of the surge premium", n["premium_growth"], lambda r: r.value("PremiumGrowth"), 0.5),
             Check("together", n["together"], lambda r: r.value("Together"), 0.5),
             Check("excess over the payroll line", n["excess"], lambda r: r.value("Excess"), 0.5)])

    cur_o = ys[-1]["ordinary"]
    s.answer("Requirement 3", f"""
        Output was flat while surge overtime {n['grew']}: standard hours {', '.join(num(y['std']) for y in ys)} against
        surge overtime of {', '.join(num(y['surge']['overtime']) for y in ys)} hours, with other overtime about
        {num(ys[0]['ordinary']['overtime'])} hours a year. In {d.C}, with output counted to {n['cutoff']}, the
        {surge['n']} weeks with surge days completed more ({num(surge['std'])} standard hours against {num(other['std'])})
        but not in proportion to their hours ({surge['ratio']:.2f} standard hours per hour clocked against
        {other['ratio']:.2f}), and the following weeks completed less ({num(surge['next'])} against {num(other['next'])}).
        The last weeks have fewer than six weeks after them and the last week stops on {n['cutoff']}; counted only over
        six complete following weeks, the figures are {num(surge['six'])} after {surge['n_six']} surge weeks against
        {num(other['six'])} after {other['n_six']} others. The pattern is consistent with output timing, including work
        brought forward, but completion dates cannot show which hours produced the output: work orders closed in {d.C}
        took about {n['lead']:.0f} days from release to completion, and completions post on weekends, when nobody clocks
        in.

        Capacity: ordinary days used about {cur_o['per_day']:.1f} hours per employee-day (counted by employee and work
        date), leaving {num(cur_o['unused_day'])} straight-time hours unused in {d.C} against
        {num(ys[-1]['surge']['overtime'])} hours of surge overtime, more than twice as many in total. Whether the work
        could have moved into straight time needs a dated plan by work center and skill, because annual hours cannot be
        moved into a constrained week. Cost at base rates with the {burden:.2%} burden: the premium alone
        {money(ys[-1]['surge_premium'] * (1 + burden))} if the hours were needed, the full cost
        {money(ys[-1]['surge_full'] * (1 + burden))} if they were not. These are two alternatives, not amounts to add,
        and neither is a finding that the hours were unneeded.

        Bridge: 5080 grew {money(br['delta'])} = payroll {money(br['payroll'])} + journal entries {money(br['je'])} +
        standard released {money(br['released'])} + change in 1090 {money(br['change'])} + material
        {money(br['material'])} + direct postings {money(br['direct'])}, an exact reconciliation. The payroll line is then
        read with three diagnostics, which are not a second bridge: the calendar ({n['extra']} more payrolls charged to
        1090, {money(n['calendar'])}, {n['added_dates']} of them a pay date the calendar added and the other {d.F}'s
        first payroll, which posted to 5080), the hours beyond {d.F}'s {n['ratio_f']:.2f} hours per standard hour
        ({num(n['hours_beyond'])} hours, {num(n['beyond_cost'])}), and the growth of the surge premium
        ({num(n['premium_growth'])}). Together they come to {num(n['together'])}, {num(n['excess'])} more than the payroll
        line, because they overlap and use different calendars and populations: the hours follow work dates through
        {n['last_day']} and describe the hourly staff, the payroll follows its pay dates and includes the salaried staff,
        and the calendar measure uses {d.F}'s average payroll, which includes the start-up month.""")


# --- Requirement 4: the plan -----------------------------------------------------------------------------------------

def params_cte(d) -> str:
    """The plan's one-row Params CTE, each assumption with its source in a comment, after the CTEs it reads: output
    by completion year (with the standard hours up to the last day with time records), hours by work year, and the
    months of the current year."""
    c, f, n = d.C, d.F, d.N
    return f"""Output AS (
    SELECT strftime('%Y', pc.CompletionDate) AS WorkYear,
        SUM({STD_HOURS})
            AS StandardHours,
        SUM(CASE WHEN pc.CompletionDate
                <= {LAST_WORK}
            THEN {STD_HOURS}
            ELSE 0 END) AS StandardHoursToCutoff,
        SUM(pcl.ExtendedStandardConversionCost) AS Conversion,
        SUM(pcl.ExtendedStandardDirectLaborCost) AS Labor,
        SUM(pcl.ExtendedStandardVariableOverheadCost
            + pcl.ExtendedStandardFixedOverheadCost) AS Overhead
{indent(COMPLETIONS, 4)}
    GROUP BY WorkYear
),
Hours AS (
    SELECT strftime('%Y', WorkDate) AS WorkYear,
        SUM(RegularHours + OvertimeHours) AS ClockedHours,
        SUM((RegularHours + OvertimeHours) * BaseHourlyRate)
            AS StraightTimeCost,
        SUM(OvertimeHours * BaseHourlyRate) * 0.5 AS Premium
    FROM PlantEntries
    GROUP BY WorkYear
),
Months AS (
    SELECT DISTINCT CAST(strftime('%Y', CalendarDate) AS INTEGER) * 12
        + CAST(strftime('%m', CalendarDate) AS INTEGER) - 1 AS MonthIndex
    FROM WorkCenterCalendar
    WHERE {year_between(c, 'CalendarDate')}
),
Params AS (
    SELECT
        -- volume: the {c} output in standard hours; the budget's units
        -- run well above the units completed, and the demand forecast
        -- well above the units ordered
        (SELECT StandardHours FROM Output WHERE WorkYear = '{c}')
            AS StandardHours,
        -- what completions released to 1090 at standard (the ledger),
        -- and the standard labor and overhead of the completion lines
        (SELECT Released FROM PlantLedger WHERE FiscalYear = {c})
            AS StandardConversion,
        (SELECT Labor FROM Output WHERE WorkYear = '{c}') AS StandardLabor,
        (SELECT Overhead FROM Output WHERE WorkYear = '{c}')
            AS AppliedOverhead,
        -- hours per standard hour: the {f} level (the target) and the
        -- {c} level, on output up to the last day with time records
        (SELECT ROUND(h.ClockedHours / o.StandardHoursToCutoff, 2)
         FROM Hours AS h
             INNER JOIN Output AS o ON o.WorkYear = h.WorkYear
         WHERE h.WorkYear = '{f}') AS TargetRatio,
        (SELECT ROUND(h.ClockedHours / o.StandardHoursToCutoff, 3)
         FROM Hours AS h
             INNER JOIN Output AS o ON o.WorkYear = h.WorkYear
         WHERE h.WorkYear = '{c}') AS CurrentRatio,
        -- straight-time rate: {c} base rates weighted by hours clocked
        (SELECT ROUND(StraightTimeCost / ClockedHours, 4)
         FROM Hours
         WHERE WorkYear = '{c}') AS Rate,
        -- the {c} overtime premium (half the base rate), all overtime
        (SELECT Premium FROM Hours WHERE WorkYear = '{c}') AS Premium,
        -- burden: employer taxes and benefits over gross pay, on the
        -- Manufacturing registers of {c}
        (SELECT ROUND(SUM(pr.EmployerPayrollTax + pr.EmployerBenefits)
             / SUM(pr.GrossPay), 4)
         FROM PayrollRegister AS pr
             INNER JOIN PayrollPeriod AS pp
                 ON pp.PayrollPeriodID = pr.PayrollPeriodID
             INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
         WHERE cc.CostCenterName = 'Manufacturing'
             AND pp.FiscalYear = {c}) AS Burden,
        -- salaried manufacturing staff, {c} gross pay
        (SELECT SUM(pr.GrossPay)
         FROM PayrollRegister AS pr
             INNER JOIN PayrollPeriod AS pp
                 ON pp.PayrollPeriodID = pr.PayrollPeriodID
             INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
             INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
         WHERE cc.CostCenterName = 'Manufacturing'
             AND e.PayClass = 'Salary'
             AND pp.FiscalYear = {c}) AS Salaried,
        -- factory overhead at the run rate of its {c} entries to 1090
        (SELECT SUM(gl.Debit)
         FROM GLEntry AS gl
             INNER JOIN JournalEntry AS je
                 ON je.JournalEntryID = gl.SourceDocumentID
             INNER JOIN Account AS a ON a.AccountID = gl.AccountID
         WHERE gl.SourceDocumentType = 'JournalEntry'
             AND je.EntryType = 'Factory Overhead'
             AND a.AccountNumber = 1090
             AND gl.FiscalYear = {c}) AS FactoryOverhead,
        -- {n} depreciation of the equipment charged to 1090 (PlantAssets):
        -- the months of {n} are those of {c} plus twelve
        (SELECT SUM(pa.Monthly)
         FROM PlantAssets AS pa
             INNER JOIN Months AS m
                 ON m.MonthIndex + 12 BETWEEN pa.FirstMonth AND pa.LastMonth)
            AS Depreciation,
        -- regular capacity: active hourly employees x 8 hours x the
        -- working days of {c}, because the calendar stops early in {n}
        (SELECT COUNT(*)
         FROM Employee AS e
             INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
         WHERE cc.CostCenterName = 'Manufacturing'
             AND e.PayClass = 'Hourly'
             AND e.IsActive = 1) AS Employees,
        (SELECT COUNT(DISTINCT CalendarDate)
         FROM WorkCenterCalendar
         WHERE IsWorkingDay = 1
             AND {year_between(c, 'CalendarDate')})
            AS WorkingDays
)"""


def r4(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r4")
    c, nn = d.C, d.N
    s.query("Requirement 4: the depreciation of the equipment charged to 1090 saved as a view, by asset",
            "Population: FixedAsset, DepreciationDebitAccountID of 1090; expected: the view PlantAssets, months "
            "counted as year x 12 + month - 1",
            """
            DROP VIEW IF EXISTS PlantAssets;
            CREATE VIEW PlantAssets AS
            SELECT fa.AssetCode, fa.InServiceDate, fa.DisposalDate,
                fa.UsefulLifeMonths, fa.OriginalCost,
                ROUND(fa.OriginalCost * 1.0 / fa.UsefulLifeMonths, 2)
                    AS Monthly,
                CAST(strftime('%Y', fa.InServiceDate) AS INTEGER) * 12
                    + CAST(strftime('%m', fa.InServiceDate) AS INTEGER)
                    AS FirstMonth,
                CASE
                    WHEN fa.DisposalDate IS NULL
                        OR CAST(strftime('%Y', fa.DisposalDate) AS INTEGER) * 12
                            + CAST(strftime('%m', fa.DisposalDate) AS INTEGER) - 2
                            > CAST(strftime('%Y', fa.InServiceDate) AS INTEGER) * 12
                            + CAST(strftime('%m', fa.InServiceDate) AS INTEGER)
                            - 1 + fa.UsefulLifeMonths
                        THEN CAST(strftime('%Y', fa.InServiceDate) AS INTEGER) * 12
                            + CAST(strftime('%m', fa.InServiceDate) AS INTEGER)
                            - 1 + fa.UsefulLifeMonths
                    ELSE CAST(strftime('%Y', fa.DisposalDate) AS INTEGER) * 12
                        + CAST(strftime('%m', fa.DisposalDate) AS INTEGER) - 2
                END AS LastMonth
            FROM FixedAsset AS fa
                INNER JOIN Account AS a
                    ON a.AccountID = fa.DepreciationDebitAccountID
            WHERE a.AccountNumber = 1090;
            """)

    ledger_dep = d.one("SELECT SUM(g.Debit) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
                       "WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryType = 'Depreciation' AND g.AccountID = ? "
                       "AND g.FiscalYear = ?", d.account("1090"), c)
    assets = notes(b).depreciation(d)["assets"]
    per_asset = {a["code"]: [round(a["monthly"] * max(0, min(a["last"], y * 12 + 11) - max(a["start"], y * 12) + 1), 2)
                             for y in (c, nn)] for a in assets}
    s.query(f"Requirement 4: each asset's depreciation in {c} and {nn}, and the {c} total against the ledger",
            f"Population: PlantAssets; expected: {money(n['dep_c'])} in {c}, equal to the ledger; "
            f"{money(n['dep_n'])} in {nn}; {n['ending']['code']} ends its life in {n['ending']['month']} {nn}",
            f"""
            WITH Months AS (
                SELECT DISTINCT CAST(strftime('%Y', CalendarDate) AS INTEGER) * 12
                    + CAST(strftime('%m', CalendarDate) AS INTEGER) - 1
                    AS MonthIndex
                FROM WorkCenterCalendar
                WHERE {year_between(c, 'CalendarDate')}
            )
            SELECT pa.AssetCode, pa.InServiceDate, pa.DisposalDate, pa.Monthly,
                ROUND(pa.Monthly * (SELECT COUNT(*) FROM Months AS m
                    WHERE m.MonthIndex BETWEEN pa.FirstMonth AND pa.LastMonth),
                    2) AS Depreciation{c},
                ROUND(pa.Monthly * (SELECT COUNT(*) FROM Months AS m
                    WHERE m.MonthIndex + 12
                        BETWEEN pa.FirstMonth AND pa.LastMonth),
                    2) AS Depreciation{nn},
                pa.LastMonth - {nn} * 12 + 1 AS LastMonthOf{nn}
            FROM PlantAssets AS pa
            ORDER BY pa.AssetCode;
            """,
            [Check("assets", sorted(per_asset), lambda r: r.col("AssetCode"))]
            + [Check(f"{code} {c} and {nn}", v, lambda r, code=code: [r.where(AssetCode=code)[f"Depreciation{y}"]
                                                                     for y in (c, nn)]) for code, v in per_asset.items()]
            + [Check(f"{c} total", n["dep_c"], lambda r: round(r.total(f"Depreciation{c}"), 2)),
               Check(f"{c} total equals the ledger", round(ledger_dep, 2), lambda r: round(r.total(f"Depreciation{c}"), 2)),
               Check(f"{nn} total", n["dep_n"], lambda r: round(r.total(f"Depreciation{nn}"), 2)),
               Check(f"{nn} a month", n["monthly_n"], lambda r: round(r.total(f"Depreciation{nn}") / 12, 2)),
               Check(f"{n['ending']['code']} last month in {nn}", notes(b).MONTHS.index(n["ending"]["month"]) + 1,
                     lambda r: r.where(AssetCode=n["ending"]["code"])[f"LastMonthOf{nn}"])])

    months = n["changes"]
    s.query(f"Requirement 4: the monthly depreciation charged to 1090 in {c}",
            f"Population: PlantAssets against the months of {c} in WorkCenterCalendar; expected: {money(n['jan'])} in "
            f"January, " + ", ".join(f"{money(m['amount'])} from {m['month']} ({m['code']})" for m in months),
            f"""
            WITH Months AS (
                SELECT DISTINCT strftime('%Y-%m', CalendarDate) AS Month,
                    CAST(strftime('%Y', CalendarDate) AS INTEGER) * 12
                        + CAST(strftime('%m', CalendarDate) AS INTEGER) - 1
                        AS MonthIndex
                FROM WorkCenterCalendar
                WHERE {year_between(c, 'CalendarDate')}
            )
            SELECT m.Month, COUNT(*) AS Assets,
                ROUND(SUM(pa.Monthly), 2) AS Depreciation
            FROM Months AS m
                INNER JOIN PlantAssets AS pa
                    ON m.MonthIndex BETWEEN pa.FirstMonth AND pa.LastMonth
            GROUP BY m.Month
            ORDER BY m.Month;
            """,
            [Check("months", 12, len), Check("January", n["jan"], lambda r: r.rows[0][2]),
             Check("the year", n["dep_c"], lambda r: round(r.total("Depreciation"), 2))]
            + [Check(f"from {m['month']} ({m['code']})", m["amount"],
                     lambda r, m=m: r.where(Month=f"{c}-{notes(b).MONTHS.index(m['month']) + 1:02d}")["Depreciation"])
               for m in months])

    s.query("Requirement 4: the purchases behind the equipment placed in service in the window",
            f"Population: PlantAssets in service from {d.F}, their supplier invoices and orders; expected: "
            + ", ".join(f"{a['code']} {a['po']}" for a in n["new"]) + ", each above its approver's limit",
            f"""
            SELECT fa.AssetCode, fa.InServiceDate, fa.OriginalCost,
                po.PONumber, po.OrderTotal,
                ap.MaxApprovalAmount AS ApproverLimit
            FROM FixedAsset AS fa
                INNER JOIN Account AS a
                    ON a.AccountID = fa.DepreciationDebitAccountID
                INNER JOIN PurchaseInvoice AS pi
                    ON pi.ReceivedDate = fa.InServiceDate
                    AND ABS(pi.GrandTotal - fa.OriginalCost) < 0.005
                INNER JOIN PurchaseOrder AS po
                    ON po.PurchaseOrderID = pi.PurchaseOrderID
                INNER JOIN Employee AS ap
                    ON ap.EmployeeID = po.ApprovedByEmployeeID
            WHERE a.AccountNumber = 1090
                AND fa.InServiceDate >= '{d.F}-01-01'
                AND EXISTS (
                    SELECT 1
                    FROM PurchaseOrderLine AS pol
                    WHERE pol.PurchaseOrderID = po.PurchaseOrderID
                        AND pol.ItemID = fa.ItemID)
            ORDER BY fa.AssetCode;
            """,
            [Check("assets and their purchase orders", [[a["code"], a["po"]] for a in n["new"]],
                   lambda r: [[x[0], x[3]] for x in r.rows]),
             Check("each above its approver's limit", [True] * len(n["new"]), lambda r: [x[4] > x[5] for x in r.rows])])

    comp = notes(b).completions(d)
    s.query(f"Requirement 4: the standard cost of {c}'s output, per standard hour",
            f"Population: completion lines of {c}; expected: {money(n['std'])} standard hours, "
            f"{money(n['lines'])} of conversion cost ({money(n['released'])} released on the ledger, "
            f"{' and '.join(x['number'] for x in n['stray']) or 'none'} posted in {c} but dated earlier), "
            f"{n['conv_rate']:.2f} per standard hour",
            f"""
            WITH Output AS (
                SELECT SUM({STD_HOURS})
                        AS StandardHours,
                    SUM(pcl.ExtendedStandardConversionCost) AS Conversion,
                    SUM(pcl.ExtendedStandardDirectLaborCost) AS Labor,
                    SUM(pcl.ExtendedStandardVariableOverheadCost
                        + pcl.ExtendedStandardFixedOverheadCost) AS Overhead
                {sub(COMPLETIONS, 16)}
                WHERE {year_between(c, 'pc.CompletionDate')}
            )
            SELECT ROUND(StandardHours, 2) AS StandardHours,
                ROUND(Conversion, 2) AS StandardConversion,
                ROUND(Labor, 2) AS StandardLabor,
                ROUND(Overhead, 2) AS AppliedOverhead,
                ROUND(Conversion / StandardHours, 2) AS ConversionPerHour,
                ROUND(Labor / StandardHours, 2) AS LaborPerHour,
                ROUND(Overhead / StandardHours, 2) AS OverheadPerHour
            FROM Output;
            """,
            [Check("standard hours", n["std"], lambda r: r.value("StandardHours")),
             Check("standard conversion of the completion lines", round(comp["conversion"], 2),
                   lambda r: r.value("StandardConversion")),
             Check("equal to what completions released to 1090, within a dollar", n["released"],
                   lambda r: r.value("StandardConversion"), 1.0),
             Check("conversion per standard hour", round(n["conv_rate"], 2), lambda r: r.value("ConversionPerHour")),
             Check("labor per standard hour", round(n["std_labor_rate"], 2), lambda r: r.value("LaborPerHour")),
             Check("applied overhead", n["applied"], lambda r: r.value("AppliedOverhead")),
             Check("overhead per standard hour", round(n["oh_rate"], 2), lambda r: r.value("OverheadPerHour")),
             Check("standard labor", comp["labor"], lambda r: r.value("StandardLabor"), 0.01)])

    salaried = d.q("SELECT e.JobTitle, SUM(pr.GrossPay) FROM PayrollRegister pr JOIN PayrollPeriod pp ON "
                   "pp.PayrollPeriodID = pr.PayrollPeriodID JOIN Employee e ON e.EmployeeID = pr.EmployeeID JOIN CostCenter "
                   "cc ON cc.CostCenterID = pr.CostCenterID WHERE cc.CostCenterName = 'Manufacturing' AND e.PayClass = "
                   "'Salary' AND pp.FiscalYear = ? GROUP BY 1 ORDER BY 1", c)
    s.query(f"Requirement 4: the salaried manufacturing staff and their {c} gross pay",
            f"Population: Manufacturing registers of {c}, salaried employees; expected: {n['titles']}, "
            f"{money(n['salary'])}",
            f"""
            SELECT e.JobTitle, COUNT(DISTINCT pr.EmployeeID) AS Employees,
                ROUND(SUM(pr.GrossPay), 2) AS GrossPay
            FROM PayrollRegister AS pr
                INNER JOIN PayrollPeriod AS pp
                    ON pp.PayrollPeriodID = pr.PayrollPeriodID
                INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
            WHERE cc.CostCenterName = 'Manufacturing'
                AND e.PayClass = 'Salary'
                AND pp.FiscalYear = {c}
            GROUP BY e.JobTitle
            ORDER BY e.JobTitle;
            """,
            [Check("job titles", [t for t, _ in salaried], lambda r: r.col("JobTitle")),
             Check("their gross pay", n["salary"], lambda r: round(r.total("GrossPay"), 2))])

    budget = d.q("SELECT b.FiscalYear, SUM(b.Quantity) FROM BudgetLine b JOIN Item i ON i.ItemID = b.ItemID WHERE "
                 "b.BudgetCategory = 'Revenue' AND i.SupplyMode = 'Manufactured' GROUP BY 1")
    made = dict(d.q("SELECT CAST(substr(pc.CompletionDate, 1, 4) AS INTEGER), SUM(pcl.QuantityCompleted) FROM "
                    "ProductionCompletionLine pcl JOIN ProductionCompletion pc ON pc.ProductionCompletionID = "
                    "pcl.ProductionCompletionID GROUP BY 1"))
    budget_ratio = {y: q / made[y] for y, q in budget if y in made}
    products = ("Furniture", "Lighting", "Textiles", "Accessories")
    forecast = {}
    for y in d.years:
        f_q = d.one("SELECT SUM(f.ForecastQuantity) FROM DemandForecast f JOIN Item i ON i.ItemID = f.ItemID WHERE "
                    "f.IsCurrent = 1 AND i.ItemGroup IN ('Furniture', 'Lighting', 'Textiles', 'Accessories') AND "
                    "substr(f.ForecastWeekStartDate, 1, 4) = ?", str(y))
        o_q = d.one("SELECT SUM(l.Quantity) FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
                    "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup IN ('Furniture', 'Lighting', 'Textiles', "
                    "'Accessories') AND substr(o.OrderDate, 1, 4) = ?", str(y))
        forecast[y] = f_q / o_q
    s.query("Requirement 4: why the volume comes from output, the budget against units completed and the demand "
            "forecast against units ordered",
            f"Population: BudgetLine revenue of manufactured items, completions, current forecasts and orders of the "
            f"product groups; expected: budget about {n['budget']} times output; forecast {n['forecast_low']} to "
            f"{n['forecast_high']} times orders",
            f"""
            WITH Budgeted AS (
                SELECT b.FiscalYear, SUM(b.Quantity) AS Units
                FROM BudgetLine AS b
                    INNER JOIN Item AS i ON i.ItemID = b.ItemID
                WHERE b.BudgetCategory = 'Revenue'
                    AND i.SupplyMode = 'Manufactured'
                GROUP BY b.FiscalYear
            ),
            Completed AS (
                SELECT CAST(strftime('%Y', pc.CompletionDate) AS INTEGER)
                        AS FiscalYear,
                    SUM(pcl.QuantityCompleted) AS Units
                FROM ProductionCompletionLine AS pcl
                    INNER JOIN ProductionCompletion AS pc
                        ON pc.ProductionCompletionID = pcl.ProductionCompletionID
                GROUP BY FiscalYear
            ),
            Forecast AS (
                SELECT CAST(strftime('%Y', f.ForecastWeekStartDate) AS INTEGER)
                        AS FiscalYear,
                    SUM(f.ForecastQuantity) AS Units
                FROM DemandForecast AS f
                    INNER JOIN Item AS i ON i.ItemID = f.ItemID
                WHERE f.IsCurrent = 1
                    AND i.ItemGroup IN ({', '.join(f"'{p}'" for p in products)})
                GROUP BY FiscalYear
            ),
            Ordered AS (
                SELECT CAST(strftime('%Y', so.OrderDate) AS INTEGER)
                        AS FiscalYear,
                    SUM(sol.Quantity) AS Units
                FROM SalesOrderLine AS sol
                    INNER JOIN SalesOrder AS so
                        ON so.SalesOrderID = sol.SalesOrderID
                    INNER JOIN Item AS i ON i.ItemID = sol.ItemID
                WHERE i.ItemGroup IN ({', '.join(f"'{p}'" for p in products)})
                GROUP BY FiscalYear
            )
            SELECT c.FiscalYear,
                ROUND(b.Units / c.Units, 2) AS BudgetToCompleted,
                ROUND(f.Units / o.Units, 2) AS ForecastToOrdered
            FROM Completed AS c
                INNER JOIN Budgeted AS b ON b.FiscalYear = c.FiscalYear
                INNER JOIN Forecast AS f ON f.FiscalYear = c.FiscalYear
                INNER JOIN Ordered AS o ON o.FiscalYear = c.FiscalYear
            ORDER BY c.FiscalYear;
            """,
            [Check(f"{c} budget to units completed", round(budget_ratio[c], 2),
                   lambda r: r.where(FiscalYear=c)["BudgetToCompleted"], 0.0051)]
            + [Check(f"{y} forecast to orders", round(v, 2), lambda r, y=y: r.where(FiscalYear=y)["ForecastToOrdered"],
                     0.0051) for y, v in forecast.items()])

    s.query(f"Requirement 4: the {c} budget's volume weighted by standard labor hours, against the regular capacity",
            f"Population: BudgetLine revenue of manufactured items, {c}, with each item's standard labor hours per unit; "
            f"expected: {num(n['budget_units'], 2)} units, {num(n['budget_std'], 2)} standard hours, {num(n['budget_over'], 2)} "
            f"above the {num(n['capacity'])} regular hours",
            f"""
            WITH Capacity AS (
                SELECT (SELECT COUNT(*)
                        FROM Employee AS e
                            INNER JOIN CostCenter AS cc
                                ON cc.CostCenterID = e.CostCenterID
                        WHERE cc.CostCenterName = 'Manufacturing'
                            AND e.PayClass = 'Hourly'
                            AND e.IsActive = 1)
                    * 8
                    * (SELECT COUNT(DISTINCT CalendarDate)
                       FROM WorkCenterCalendar
                       WHERE IsWorkingDay = 1
                           AND {year_between(c, 'CalendarDate')})
                    AS RegularHours
            )
            SELECT b.FiscalYear,
                ROUND(SUM(b.Quantity), 2) AS BudgetUnits,
                ROUND(SUM(b.Quantity * i.StandardLaborHoursPerUnit), 2)
                    AS BudgetStandardHours,
                (SELECT RegularHours FROM Capacity) AS RegularCapacity,
                ROUND(SUM(b.Quantity * i.StandardLaborHoursPerUnit)
                    - (SELECT RegularHours FROM Capacity), 2)
                    AS HoursAboveCapacity
            FROM BudgetLine AS b
                INNER JOIN Item AS i ON i.ItemID = b.ItemID
            WHERE b.FiscalYear = {c}
                AND b.BudgetCategory = 'Revenue'
                AND i.SupplyMode = 'Manufactured'
            GROUP BY b.FiscalYear;
            """,
            [Check("budget units", round(n["budget_units"], 2), lambda r: r.value("BudgetUnits"), 0.005),
             Check("budget standard hours, item by item", round(n["budget_std"], 2), lambda r: r.value("BudgetStandardHours"), 0.005),
             Check("regular capacity", n["capacity"], lambda r: r.value("RegularCapacity")),
             Check("hours above the regular capacity", round(n["budget_over"], 2), lambda r: r.value("HoursAboveCapacity"), 0.005)])

    categories = [r[0] for r in d.q("SELECT DISTINCT b.BudgetCategory FROM BudgetLine b JOIN CostCenter c ON "
                                    "c.CostCenterID = b.CostCenterID WHERE c.CostCenterName = 'Manufacturing'")]
    s.query("Requirement 4: what the budget holds for Manufacturing",
            "Population: BudgetLine of the Manufacturing cost center; expected: cost of goods sold only, no labor or "
            "overhead budget",
            """
            SELECT b.FiscalYear, b.BudgetCategory, COUNT(*) AS Lines
            FROM BudgetLine AS b
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = b.CostCenterID
            WHERE cc.CostCenterName = 'Manufacturing'
            GROUP BY b.FiscalYear, b.BudgetCategory
            ORDER BY b.FiscalYear, b.BudgetCategory;
            """,
            [Check("budget categories", sorted(categories), lambda r: sorted(set(r.col("BudgetCategory"))))])

    levels, need, conv, var = n["levels"], n["need"], n["conv"], n["variance"]
    names = ["Standard hours", f"{d.F} level", f"{c} level with its overtime"]
    s.query(f"Requirement 4: the {nn} plan, hours against regular capacity and conversion cost against standard, in "
            "three scenarios",
            f"Population: the Params CTE; expected: capacity {num(n['capacity'])} hours; expected variance "
            f"{', '.join(num(v) for v in var)}",
            f"""
            WITH {sub(params_cte(d), 12)},
            Scenarios AS (
                SELECT '{names[0]}' AS Scenario, 1.0 AS Ratio,
                    0 AS WithPremium, p.*
                FROM Params AS p
                UNION ALL
                SELECT '{names[1]}', p.TargetRatio, 0, p.*
                FROM Params AS p
                UNION ALL
                SELECT '{names[2]}', p.CurrentRatio, 1, p.*
                FROM Params AS p
            )
            SELECT Scenario, Ratio,
                ROUND(StandardHours * Ratio, 0) AS HoursNeeded,
                Employees * 8 * WorkingDays AS RegularCapacity,
                CASE WHEN StandardHours * Ratio > Employees * 8 * WorkingDays
                    THEN ROUND(StandardHours * Ratio
                        - Employees * 8 * WorkingDays, 0)
                    ELSE 0 END AS OvertimeNeeded,
                ROUND(StandardHours * Ratio * Rate * (1 + Burden), 0)
                    AS HourlyLabor,
                ROUND(WithPremium * Premium * (1 + Burden), 0)
                    AS OvertimePremium,
                ROUND(Salaried * (1 + Burden) + FactoryOverhead
                    + Depreciation, 0) AS Overhead,
                ROUND(StandardHours * Ratio * Rate * (1 + Burden)
                    + WithPremium * Premium * (1 + Burden)
                    + Salaried * (1 + Burden) + FactoryOverhead
                    + Depreciation, 0) AS ConversionCost,
                ROUND(StandardConversion, 0) AS StandardConversion,
                ROUND(StandardHours * Ratio * Rate * (1 + Burden)
                    + WithPremium * Premium * (1 + Burden)
                    + Salaried * (1 + Burden) + FactoryOverhead
                    + Depreciation - StandardConversion, 0)
                    AS ExpectedVariance
            FROM Scenarios
            ORDER BY Ratio;
            """,
            [Check("scenarios", names, lambda r: r.col("Scenario")),
             Check("ratios", levels, lambda r: r.col("Ratio"), 0)]
            + [Check(f"{names[k]}: hours needed", need[k], lambda r, k=k: r.rows[k][2], 0.5) for k in range(3)]
            + [Check("regular capacity", [n["capacity"]] * 3, lambda r: r.col("RegularCapacity")),
               Check("overtime needed for capacity", [0, 0, 0], lambda r: r.col("OvertimeNeeded")),
               Check("overtime premium with burden", round(n["premium"] * (1 + n["burden"]), 0),
                     lambda r: r.rows[2][6], 0.5),
               Check("plan overhead", n["overhead"], lambda r: r.rows[0][7], 0.5)]
            + [Check(f"{names[k]}: conversion cost", conv[k], lambda r, k=k: r.rows[k][8], 0.5) for k in range(3)]
            + [Check(f"{names[k]}: expected variance", var[k], lambda r, k=k: r.rows[k][10], 0.5) for k in range(3)])

    s.query("Requirement 4: the variance left at standard hours, by cause",
            f"Population: the Params CTE and {c}'s completions; expected: labor rate with burden "
            f"{n['rate_b']:.2f} against {n['std_labor_rate']:.2f} (about {num(n['labor_excess'])}), overhead "
            f"{num(n['overhead'])} against {num(n['applied'])} applied (about {num(n['oh_excess'])})",
            f"""
            WITH {sub(params_cte(d), 12)}
            SELECT Rate, Burden, ROUND(Salaried, 2) AS Salaried,
                ROUND(FactoryOverhead, 2) AS FactoryOverhead,
                ROUND(Depreciation, 2) AS Depreciation,
                ROUND(Rate * (1 + Burden), 2) AS RateWithBurden,
                ROUND(StandardLabor / StandardHours, 2)
                    AS StandardRate,
                ROUND(Rate * (1 + Burden) * StandardHours
                    - StandardLabor, 0) AS LaborExcess,
                ROUND(Salaried * (1 + Burden) + FactoryOverhead
                    + Depreciation, 0) AS PlanOverhead,
                ROUND(AppliedOverhead, 0) AS AppliedOverhead,
                ROUND(Salaried * (1 + Burden) + FactoryOverhead + Depreciation
                    - AppliedOverhead, 0) AS OverheadExcess,
                ROUND(StandardHours / (Employees * 8 * WorkingDays), 3)
                    AS CapacityUsed
            FROM Params;
            """,
            [Check("straight-time rate", n["rate"], lambda r: r.value("Rate"), 0.00005),
             Check("burden", n["burden"], lambda r: r.value("Burden"), 0.00005),
             Check("salaried staff", n["salary"], lambda r: r.value("Salaried")),
             Check("factory overhead run rate", n["foh"], lambda r: r.value("FactoryOverhead")),
             Check(f"{nn} depreciation", n["dep_n"], lambda r: r.value("Depreciation")),
             Check("rate with burden", round(n["rate_b"], 2), lambda r: r.value("RateWithBurden")),
             Check("standard labor rate", round(n["std_labor_rate"], 2), lambda r: r.value("StandardRate")),
             Check("labor excess", (n["rate_b"] - n["std_labor_rate"]) * n["std"], lambda r: r.value("LaborExcess"), 0.5),
             Check("plan overhead", round(n["overhead"]), lambda r: r.value("PlanOverhead"), 0.5),
             Check("applied overhead", round(n["applied"]), lambda r: r.value("AppliedOverhead"), 0.5),
             Check("overhead excess", n["overhead"] - n["applied"], lambda r: r.value("OverheadExcess"), 0.5),
             Check("capacity used", round(n["use"], 3), lambda r: r.value("CapacityUsed"), 0.0006)])

    stray = " and ".join(f"{x['number']}, dated {x['dated']} and posted {x['posted']}" for x in n["stray"])
    s.answer("Requirement 4", f"""
        Assumptions (the Params CTE): volume {money(n['std'])} standard hours, the {c} output, because the budget plans
        about {n['budget']} times the units the plant completed (weighted item by item, {num(n['budget_std'])} standard
        hours, {num(n['budget_over'])} more than the regular capacity) and the demand forecast {n['forecast_low']} to
        {n['forecast_high']} times the units ordered, and no year has a manufacturing labor or overhead budget; a target
        of {levels[1]:.2f} hours per standard hour, the {d.F} level, a planning target to test rather than a measure of
        what the work requires; a straight-time rate of {n['rate']:.2f} an hour (the {c} base rates weighted by hours)
        with a {n['burden']:.2%} burden, on the assumption that paid hours follow the hours scheduled; {n['days']}
        working days, from {c}, because the calendar stops early in {nn}; Factory Overhead at its {c} run rate,
        {money(n['foh'])}; and {nn} depreciation of {money(n['dep_n'])} from FixedAsset (cost over useful life, zero residual value, from the
        month after the in-service date through the month before disposal and no longer than the life), after the same
        schedule reproduced {c}'s {money(n['dep_c'])} to the cent. Salaried staff ({n['titles']}) cost {money(n['salary'])}
        before the burden. The standard conversion of the plan is what completions released to 1090 in {c},
        {money(n['released'])}; the completion lines dated in {c} carry {money(n['lines'])}, and the difference is
        {stray}.

        Capacity: {n['employees']} employees x 8 hours x {n['days']} days = {num(n['capacity'])} regular hours, against
        {num(need[0])} hours needed at standard, {num(need[1])} at {levels[1]:.2f}, and {num(need[2])} at the {c} level
        of {levels[2]:.3f}. On the year's total no scenario needs overtime, so the plan should allow none as a routine.
        The total is only a screen: weeks and work centers can still bind (Requirement 2 found surge weeks planned
        above capacity), so any exception is approved against a dated plan.

        Conversion cost and expected variance: {num(conv[0])} and {num(var[0])} at standard hours; {num(conv[1])} and
        {num(var[1])} at the {d.F} level; {num(conv[2])} and {num(var[2])} at the {c} level with its overtime premium,
        close to {c}'s conversion variance of {money(n['actual'])}. Even at standard hours a variance remains: the labor
        rate with burden is {n['rate_b']:.2f} an hour against the standard {n['std_labor_rate']:.2f} (about
        {num(n['labor_excess'])}), and overhead of {num(n['overhead'])} is set against {num(n['applied'])} applied at
        {n['oh_rate']:.2f} per standard hour ({num(n['variable'])} variable, {num(n['fixed'])} fixed; about
        {num(n['oh_excess'])}). The output is about {n['use']:.0%} of the plant's regular employee-hours, but those hours
        are not the normal capacity of the inventory standard, and part of the applied overhead is variable, so the
        residual is not all idle capacity until the overhead is analyzed into fixed and variable, normal and abnormal.

        Standards: keep the direct-hour standards provisionally, since the records give no reason to revise them. Direct
        time stayed below the standard hours ({num(n['direct'])} against {num(n['std_cut'])} to {n['cutoff']}, and
        {num(n['direct_common'])} against {num(n['std_common'])} counted on both sides to {n['ind_end']}, the day
        indirect time ends), but that compares period totals, does not validate the standards and does not show that they
        are right. Review the rates on a defensible normal-capacity basis, and do not raise the fixed overhead rate
        simply to absorb idle capacity (Requirement 5).""")


# --- Requirement 5: the year-end close -------------------------------------------------------------------------------

def r5(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r5")
    p, prior = n["p"], n["prior"]
    c, pp_ = d.C, d.P
    s.query(f"Requirement 5: the payroll owed at {c}-12-31, saved as a view: the last eight processed pay periods' "
            "cost per working day",
            f"Population: PayrollPeriod Processed, their registers, WorkCenterCalendar; expected: the view "
            f"PayrollAccrual",
            f"""
            DROP VIEW IF EXISTS PayrollAccrual;
            CREATE VIEW PayrollAccrual AS
            WITH Periods AS (
                SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate
                FROM PayrollPeriod
                WHERE Status = 'Processed'
                ORDER BY PeriodEndDate DESC
                LIMIT 8
            ),
            Span AS (
                SELECT MIN(PeriodStartDate) AS FirstDay,
                    MAX(PeriodEndDate) AS LastDay
                FROM Periods
            ),
            Days AS (
                SELECT sp.FirstDay, sp.LastDay,
                    (SELECT COUNT(DISTINCT c.CalendarDate)
                     FROM WorkCenterCalendar AS c
                     WHERE c.IsWorkingDay = 1
                         AND c.CalendarDate BETWEEN sp.FirstDay AND sp.LastDay)
                        AS PeriodDays,
                    (SELECT COUNT(DISTINCT c.CalendarDate)
                     FROM WorkCenterCalendar AS c
                     WHERE c.IsWorkingDay = 1
                         AND c.CalendarDate > sp.LastDay
                         AND c.CalendarDate <= '{c}-12-31') AS DaysLeft
                FROM Span AS sp
            ),
            Centers AS (
                SELECT cc.CostCenterID, cc.CostCenterName,
                    SUM(pr.GrossPay) AS GrossPay,
                    SUM(pr.EmployerPayrollTax) AS EmployerTaxes,
                    SUM(pr.EmployerBenefits) AS Benefits
                FROM PayrollRegister AS pr
                    INNER JOIN CostCenter AS cc
                        ON cc.CostCenterID = pr.CostCenterID
                WHERE pr.PayrollPeriodID IN (SELECT PayrollPeriodID FROM Periods)
                GROUP BY cc.CostCenterID, cc.CostCenterName
            )
            SELECT ce.CostCenterID, ce.CostCenterName,
                (SELECT FirstDay FROM Days) AS FirstDay,
                (SELECT LastDay FROM Days) AS LastDay,
                (SELECT PeriodDays FROM Days) AS PeriodDays,
                (SELECT DaysLeft FROM Days) AS DaysLeft,
                ce.GrossPay + ce.EmployerTaxes + ce.Benefits AS PeriodCost,
                ce.GrossPay / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days) AS GrossPay,
                ce.EmployerTaxes / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days) AS EmployerTaxes,
                ce.Benefits / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days) AS Benefits
            FROM Centers AS ce;
            """)

    s.query(f"Requirement 5: the accrual for December 14-31, {c}, in total",
            f"Population: the view PayrollAccrual; expected: {money(p['cost'])} over {p['wd']} working days, "
            f"{money(p['daily'])} a day, x {p['left']} days = {money(p['accrual'])}",
            """
            SELECT MIN(FirstDay) AS FirstDay, MAX(LastDay) AS LastDay,
                MAX(PeriodDays) AS PeriodDays, MAX(DaysLeft) AS DaysLeft,
                ROUND(SUM(PeriodCost), 2) AS PeriodCost,
                ROUND(SUM(PeriodCost) / MAX(PeriodDays), 2) AS CostPerDay,
                ROUND(SUM(GrossPay + EmployerTaxes + Benefits), 2) AS Accrual,
                ROUND(SUM(GrossPay), 2) AS GrossPay,
                ROUND(SUM(EmployerTaxes), 2) AS EmployerTaxes,
                ROUND(SUM(Benefits), 2) AS Benefits
            FROM PayrollAccrual;
            """,
            [Check("first day", p["start"], lambda r: r.value("FirstDay")),
             Check("last day", p["end"], lambda r: r.value("LastDay")),
             Check("working days of the eight periods", p["wd"], lambda r: r.value("PeriodDays")),
             Check("working days left", p["left"], lambda r: r.value("DaysLeft")),
             Check("cost of the eight periods", p["cost"], lambda r: r.value("PeriodCost")),
             Check("cost per working day", round(p["daily"], 2), lambda r: r.value("CostPerDay")),
             Check("accrual", p["accrual"], lambda r: r.value("Accrual")),
             Check("gross pay", p["gross"], lambda r: r.value("GrossPay")),
             Check("employer taxes", p["tax"], lambda r: r.value("EmployerTaxes")),
             Check("benefits", p["ben"], lambda r: r.value("Benefits"))])

    centers = p["centers"]
    s.query(f"Requirement 5: the accrual at {c}-12-31 by cost center",
            f"Population: the view PayrollAccrual; expected: {len(centers)} cost centers, Manufacturing "
            f"{money(centers[0]['amount'])}",
            """
            SELECT CostCenterName,
                ROUND(GrossPay + EmployerTaxes + Benefits, 2) AS Accrual,
                ROUND(GrossPay, 2) AS GrossPay
            FROM PayrollAccrual
            ORDER BY Accrual DESC;
            """,
            [Check("cost centers", [x["name"] for x in centers], lambda r: r.col("CostCenterName"))]
            + [Check(f"{centers[0]['name']} gross pay", centers[0]["gross"],
                     lambda r: r.where(CostCenterName=centers[0]["name"])["GrossPay"])]
            + [Check(f"{x['name']} accrual", x["amount"], lambda r, x=x: r.where(CostCenterName=x["name"])["Accrual"])
               for x in centers])

    routes = {}
    for center, number in d.q("SELECT DISTINCT cc.CostCenterName, a.AccountNumber FROM GLEntry g JOIN Account a ON "
                              "a.AccountID = g.AccountID JOIN CostCenter cc ON cc.CostCenterID = g.CostCenterID WHERE "
                              "g.SourceDocumentType = 'PayrollSummary' AND g.FiscalYear = ? AND g.Debit > 0", c):
        routes.setdefault(center, set()).add(int(number))
    s.query(f"Requirement 5: the accounts each cost center's payroll is debited to, {c}",
            "Population: PayrollSummary debits; expected: Manufacturing to 1090; each other cost center to one salary "
            "account and 6060",
            f"""
            SELECT cc.CostCenterName, a.AccountNumber, a.AccountName,
                ROUND(SUM(gl.Debit), 2) AS Debits
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = gl.CostCenterID
            WHERE gl.SourceDocumentType = 'PayrollSummary'
                AND gl.FiscalYear = {c}
                AND gl.Debit > 0
            GROUP BY cc.CostCenterID, cc.CostCenterName, a.AccountID,
                a.AccountNumber, a.AccountName
            ORDER BY cc.CostCenterName, a.AccountNumber;
            """,
            [Check("Manufacturing", sorted(routes["Manufacturing"]),
                   lambda r: sorted(x[1] for x in r.rows if x[0] == "Manufacturing")),
             Check("every account by cost center", {k: sorted(v) for k, v in routes.items()},
                   lambda r: {k: sorted(x[1] for x in r.rows if x[0] == k) for k in {x[0] for x in r.rows}})])

    names = dict(d.q("SELECT AccountNumber, AccountName FROM Account WHERE AccountNumber IN (2030, 2032, 2033, 6060)"))
    s.query("Requirement 5: the accounts the adjusting entries credit and debit for the employer's costs",
            "Population: Account; expected: 2030 Accrued Payroll, the employer tax and benefit liabilities, 6060",
            """
            SELECT AccountNumber, AccountName, AccountType, AccountSubType
            FROM Account
            WHERE AccountNumber IN (2030, 2032, 2033, 6060)
            ORDER BY AccountNumber;
            """,
            [Check("account names", [[k, v] for k, v in sorted(names.items())], lambda r: [[x[0], x[1]] for x in r.rows])])

    s.query(f"Requirement 5: the {pp_} work paid in fiscal {c}, saved as a view: the pay periods that cross "
            f"{pp_}-12-31, by working day",
            f"Population: PayrollPeriod paid after {pp_}-12-31 that start by then; expected: the view PriorYearWork",
            f"""
            DROP VIEW IF EXISTS PriorYearWork;
            CREATE VIEW PriorYearWork AS
            WITH Periods AS (
                SELECT pp.PayrollPeriodID, pp.PeriodNumber,
                    pp.PeriodStartDate, pp.PeriodEndDate, pp.PayDate,
                    (SELECT COUNT(DISTINCT c.CalendarDate)
                     FROM WorkCenterCalendar AS c
                     WHERE c.IsWorkingDay = 1
                         AND c.CalendarDate BETWEEN pp.PeriodStartDate
                             AND pp.PeriodEndDate
                         AND c.CalendarDate <= '{pp_}-12-31') AS DaysInYear,
                    (SELECT COUNT(DISTINCT c.CalendarDate)
                     FROM WorkCenterCalendar AS c
                     WHERE c.IsWorkingDay = 1
                         AND c.CalendarDate BETWEEN pp.PeriodStartDate
                             AND pp.PeriodEndDate) AS WorkingDays
                FROM PayrollPeriod AS pp
                WHERE pp.PeriodStartDate <= '{pp_}-12-31'
                    AND pp.PayDate > '{pp_}-12-31'
            )
            SELECT p.PeriodNumber, p.PeriodStartDate, p.PeriodEndDate,
                p.PayDate, p.DaysInYear, p.WorkingDays,
                SUM(pr.GrossPay + pr.EmployerPayrollTax + pr.EmployerBenefits)
                    AS PeriodCost,
                SUM(CASE WHEN cc.CostCenterName = 'Manufacturing'
                    THEN pr.GrossPay + pr.EmployerPayrollTax
                        + pr.EmployerBenefits ELSE 0 END) AS Manufacturing
            FROM Periods AS p
                INNER JOIN PayrollRegister AS pr
                    ON pr.PayrollPeriodID = p.PayrollPeriodID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
            GROUP BY p.PayrollPeriodID, p.PeriodNumber, p.PeriodStartDate,
                p.PeriodEndDate, p.PayDate, p.DaysInYear, p.WorkingDays;
            """)

    full, cross = prior["full"], prior["cross"]
    s.query(f"Requirement 5: the {pp_} work in the registers paid in fiscal {c}",
            f"Population: the view PriorYearWork; expected: period of {full['start']} in full, {money(full['cost'])}, "
            f"and {cross['inside']} of {cross['days']} working days of the next, {money(cross['share'])}: "
            f"{money(prior['total'])}",
            """
            SELECT PeriodNumber, PeriodStartDate, PeriodEndDate, PayDate,
                DaysInYear, WorkingDays, ROUND(PeriodCost, 2) AS PeriodCost,
                ROUND(PeriodCost * DaysInYear / WorkingDays, 2)
                    AS PriorYearWork,
                ROUND(Manufacturing * DaysInYear / WorkingDays, 2)
                    AS ManufacturingPart
            FROM PriorYearWork
            ORDER BY PeriodStartDate;
            """,
            [Check("periods", [full["start"], cross["start"]], lambda r: r.col("PeriodStartDate")),
             Check("period in full", full["cost"], lambda r: r.where(PeriodStartDate=full["start"])["PriorYearWork"]),
             Check("working days of the crossing period in the year", [cross["inside"], cross["days"]],
                   lambda r: [r.where(PeriodStartDate=cross["start"])[k] for k in ("DaysInYear", "WorkingDays")]),
             Check("crossing period's cost", cross["cost"], lambda r: r.where(PeriodStartDate=cross["start"])["PeriodCost"]),
             Check("its share", cross["share"], lambda r: r.where(PeriodStartDate=cross["start"])["PriorYearWork"]),
             Check("total", prior["total"], lambda r: round(r.total("PriorYearWork"), 2)),
             Check("manufacturing part", prior["mfg"], lambda r: round(r.total("ManufacturingPart"), 2), 0.015)])

    a2030 = d.q("SELECT g.SourceDocumentType, SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g WHERE g.AccountID = ? AND "
                "g.PostingDate <= ? GROUP BY 1", d.account("2030"), f"{c}-12-31")
    s.query("Requirement 5: test L8 of Audit.sql rerun, account 2030 by source document type",
            f"Population: account 2030 to {c}-12-31; expected: the opening {money(n['opening'])} of {n['entry']} "
            f"alone; the payroll postings net to zero",
            audit_sql("accrued_payroll").replace("'2026-12-31'", f"'{c}-12-31'"),
            [Check("opening line", n["opening"], lambda r: r.where(SourceDocumentType="JournalEntry")["Balance"]),
             Check("the payroll postings net", round(sum(v for t, v in a2030 if t != "JournalEntry"), 2),
                   lambda r: round(sum(x[2] for x in r.rows if x[0] != "JournalEntry"), 2)),
             Check("the balance", round(sum(v for _, v in a2030), 2), lambda r: round(r.total("Balance"), 2))])

    s.query(f"Requirement 5: test L5 of Audit.sql rerun, revenue posted in another year than its delivery",
            f"Population: every sales invoice; expected: {money(n['delivered'])} of {pp_} deliveries posted in {c}",
            audit_sql("revenue_cutoff"),
            [Check(f"{pp_} deliveries posted in another year", n["delivered"],
                   lambda r: r.where(Finding="Revenue posted in another year", DeliveryYear=str(pp_))["SubTotal"])])

    s.query(f"Requirement 5: test L6 of Audit.sql rerun, shipments never invoiced",
            f"Population: every shipment line; expected: {n['n_uninv']} lines, {money(n['uninv'])} at order price, "
            f"standard cost {money(n['uninv_std'])}",
            audit_sql("unbilled_shipments"),
            [Check("lines", n["n_uninv"], len),
             Check("value at order price", n["uninv"], lambda r: round(r.total("SalesValue"), 2)),
             Check("standard cost", n["uninv_std"], lambda r: round(r.total("StandardCost"), 2))])

    s.query("Requirement 5: the revenue cutoff items saved as a view, by delivery and posting year",
            "Population: invoices posted in another year than their latest delivery, and shipment lines never "
            "invoiced; expected: the view CutoffItems",
            """
            DROP VIEW IF EXISTS CutoffItems;
            CREATE VIEW CutoffItems AS
            WITH Shipped AS (
                SELECT sil.SalesInvoiceID, MAX(s.DeliveryDate) AS DeliveryDate
                FROM SalesInvoiceLine AS sil
                    INNER JOIN ShipmentLine AS sl
                        ON sl.ShipmentLineID = sil.ShipmentLineID
                    INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
                GROUP BY sil.SalesInvoiceID
            ),
            Posted AS (
                SELECT SourceDocumentID AS SalesInvoiceID,
                    MIN(PostingDate) AS PostingDate
                FROM GLEntry
                WHERE SourceDocumentType = 'SalesInvoice'
                GROUP BY SourceDocumentID
            )
            SELECT 'Posted in another year' AS Item, si.InvoiceNumber AS Document,
                strftime('%Y', sh.DeliveryDate) AS DeliveryYear,
                strftime('%Y', p.PostingDate) AS PostingYear,
                si.SubTotal AS Amount
            FROM SalesInvoice AS si
                INNER JOIN Shipped AS sh ON sh.SalesInvoiceID = si.SalesInvoiceID
                INNER JOIN Posted AS p ON p.SalesInvoiceID = si.SalesInvoiceID
            WHERE strftime('%Y', p.PostingDate) <> strftime('%Y', sh.DeliveryDate)
            UNION ALL
            SELECT 'Never invoiced', s.ShipmentNumber,
                strftime('%Y', s.DeliveryDate), NULL,
                ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2)
            FROM ShipmentLine AS sl
                INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
                INNER JOIN SalesOrderLine AS sol
                    ON sol.SalesOrderLineID = sl.SalesOrderLineID
                LEFT JOIN SalesInvoiceLine AS sil
                    ON sil.ShipmentLineID = sl.ShipmentLineID
            WHERE sil.SalesInvoiceLineID IS NULL;
            """)

    ni = n["ni"]
    s.query(f"Requirement 5: the proposed adjustments and their effect on fiscal {c} net income and the balance sheet",
            f"Population: the views PayrollAccrual, PriorYearWork and CutoffItems, and Chapter 6's net income; "
            f"expected: {money(ni)} - {money(n['change'])} + {money(n['net_rev'])} = {money(n['adj_ni'])}",
            f"""
            WITH Measures AS (
                SELECT
                    (SELECT ROUND(SUM(GrossPay + EmployerTaxes + Benefits), 2)
                     FROM PayrollAccrual) AS AccrualAtYearEnd,
                    (SELECT ROUND(SUM(PeriodCost * DaysInYear / WorkingDays), 2)
                     FROM PriorYearWork) AS AccrualYearBefore,
                    (SELECT ROUND(SUM(Amount), 2)
                     FROM CutoffItems
                     WHERE DeliveryYear = '{c}') AS RevenueToAdd,
                    (SELECT ROUND(SUM(Amount), 2)
                     FROM CutoffItems
                     WHERE DeliveryYear = '{pp_}' AND PostingYear = '{c}')
                        AS RevenueToRemove,
                    (SELECT ROUND(SUM(gl.Credit - gl.Debit), 2)
                     FROM GLEntry AS gl
                         INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                     WHERE a.AccountType IN ('Revenue', 'Expense')
                         AND gl.FiscalYear = {c}
                         AND gl.VoucherNumber NOT IN (
                             {sub(CLOSES, 29)})) AS NetIncome,
                    (SELECT ROUND(SUM(gl.Credit - gl.Debit), 2)
                     FROM GLEntry AS gl
                         INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                     WHERE a.AccountSubType = 'Current Liability'
                         AND gl.PostingDate <= '{c}-12-31')
                        AS CurrentLiabilities
            )
            SELECT NetIncome,
                ROUND(AccrualYearBefore - AccrualAtYearEnd, 2) AS PayrollEffect,
                ROUND(RevenueToAdd - RevenueToRemove, 2) AS CutoffEffect,
                ROUND(NetIncome + AccrualYearBefore - AccrualAtYearEnd
                    + RevenueToAdd - RevenueToRemove, 2) AS AdjustedNetIncome,
                ROUND((AccrualYearBefore - AccrualAtYearEnd + RevenueToAdd
                    - RevenueToRemove) / NetIncome, 4) AS ShareOfNetIncome,
                AccrualAtYearEnd AS LiabilityAdded,
                RevenueToAdd AS ReceivablesAdded,
                ROUND(RevenueToRemove - AccrualYearBefore, 2)
                    AS OpeningRetainedEarnings,
                ROUND(AccrualAtYearEnd / NetIncome, 4)
                    AS LiabilityToNetIncome,
                ROUND(AccrualAtYearEnd / CurrentLiabilities, 4)
                    AS LiabilityToCurrentLiabilities
            FROM Measures;
            """,
            [Check("recorded net income (Chapter 6)", ni, lambda r: r.value("NetIncome")),
             Check("payroll effect on income", -round(n["change"], 2), lambda r: r.value("PayrollEffect")),
             Check("cutoff effect on income", n["net_rev"], lambda r: r.value("CutoffEffect")),
             Check("adjusted net income", n["adj_ni"], lambda r: r.value("AdjustedNetIncome")),
             Check("share of net income", round(n["share"], 4), lambda r: abs(r.value("ShareOfNetIncome")), 0.00005),
             Check("liability added", p["accrual"], lambda r: r.value("LiabilityAdded")),
             Check("receivables added", n["uninv"], lambda r: r.value("ReceivablesAdded")),
             Check("opening retained earnings", round(n["delivered"] - prior["total"], 2),
                   lambda r: r.value("OpeningRetainedEarnings")),
             Check("liability left out against net income", round(n["liab_ni"], 4),
                   lambda r: r.value("LiabilityToNetIncome"), 0.00005),
             Check("liability left out against current liabilities", round(n["liab_cl"], 4),
                   lambda r: r.value("LiabilityToCurrentLiabilities"), 0.00005)])

    s.query(f"Requirement 5: the standard conversion cost that completions dated after the time records end released to "
            "1090",
            f"Population: ProductionCompletion lines and the 1090 postings of completions from the day after the last "
            f"time record ({n['after_first']}) and from the day after the last processed period (December {n['left_day']}) to "
            f"{c}-12-31; expected: {n['after_time']['n']} completions and {money(n['after_time']['cost'])}, then "
            f"{n['in_window']['n']} and {money(n['in_window']['cost'])}, each equal to the credits to 1090",
            f"""
            WITH Windows AS (
                SELECT 'After the last time record' AS Basis,
                    date((SELECT MAX(WorkDate) FROM TimeClockEntry),
                        '+1 day') AS FirstDay
                UNION ALL
                SELECT 'After the last processed period',
                    date((SELECT MAX(LastDay) FROM PayrollAccrual), '+1 day')
            )
            SELECT w.Basis, w.FirstDay,
                (SELECT COUNT(DISTINCT pc.ProductionCompletionID)
                 FROM ProductionCompletion AS pc
                 WHERE pc.CompletionDate BETWEEN w.FirstDay AND '{c}-12-31')
                    AS Completions,
                (SELECT ROUND(SUM(pcl.ExtendedStandardConversionCost), 2)
                 FROM ProductionCompletionLine AS pcl
                     INNER JOIN ProductionCompletion AS pc
                         ON pc.ProductionCompletionID = pcl.ProductionCompletionID
                 WHERE pc.CompletionDate BETWEEN w.FirstDay AND '{c}-12-31')
                    AS StandardConversion,
                (SELECT ROUND(SUM(gl.Credit - gl.Debit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 1090
                     AND gl.SourceDocumentType = 'ProductionCompletion'
                     AND gl.PostingDate BETWEEN w.FirstDay AND '{c}-12-31')
                    AS CreditedTo1090
            FROM Windows AS w
            ORDER BY w.FirstDay;
            """,
            [Check("completions after the last time record", n["after_time"]["n"],
                   lambda r: r.where(Basis="After the last time record")["Completions"]),
             Check("standard conversion after the last time record", round(n["after_time"]["cost"], 2),
                   lambda r: r.where(Basis="After the last time record")["StandardConversion"], 0.005),
             Check("credited to 1090 after the last time record", round(n["after_time"]["cost"], 2),
                   lambda r: r.where(Basis="After the last time record")["CreditedTo1090"], 0.005),
             Check("completions after the last processed period", n["in_window"]["n"],
                   lambda r: r.where(Basis="After the last processed period")["Completions"]),
             Check("standard conversion after the last processed period", round(n["in_window"]["cost"], 2),
                   lambda r: r.where(Basis="After the last processed period")["StandardConversion"], 0.005),
             Check("credited to 1090 after the last processed period", round(n["in_window"]["cost"], 2),
                   lambda r: r.where(Basis="After the last processed period")["CreditedTo1090"], 0.005)])

    s.query("Requirement 5: actual conversion cost per standard hour against the standard, and the finished goods "
            "it would revalue",
            f"Population: PlantLedger and {c}'s completions; account 1040 at {c}-12-31; expected: "
            f"{n['actual_rate']:.2f} against {n['std_rate']:.2f}; finished goods {money(n['fg'])}",
            f"""
            SELECT ROUND((pl.Payroll + pl.JournalEntries)
                    / (SELECT SUM({STD_HOURS})
                       {sub(COMPLETIONS, 23)}
                       WHERE {year_between(c, 'pc.CompletionDate')}), 2)
                    AS ActualPerStandardHour,
                ROUND(pl.Released
                    / (SELECT SUM({STD_HOURS})
                       {sub(COMPLETIONS, 23)}
                       WHERE {year_between(c, 'pc.CompletionDate')}), 2)
                    AS StandardPerStandardHour,
                (SELECT ROUND(SUM(gl.Debit - gl.Credit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 1040
                     AND gl.PostingDate <= '{c}-12-31') AS FinishedGoods
            FROM PlantLedger AS pl
            WHERE pl.FiscalYear = {c};
            """,
            [Check("actual per standard hour", round(n["actual_rate"], 2), lambda r: r.value("ActualPerStandardHour")),
             Check("standard per standard hour", round(n["std_rate"], 2), lambda r: r.value("StandardPerStandardHour")),
             Check("finished goods", round(n["fg"], 2), lambda r: r.value("FinishedGoods"))])

    asv = n["asv"]
    s.query(f"Requirement 5: supplier invoices dated in {pp_} and received in {c}, with the accrual that carried them",
            f"Population: PurchaseInvoice; expected: {', '.join(a['number'] for a in asv)}, accrued by "
            f"{', '.join(a['je'] for a in asv)}",
            f"""
            SELECT pi.InvoiceNumber, pi.InvoiceDate, pi.ReceivedDate,
                pi.GrandTotal, je.EntryNumber AS AccrualEntry,
                je.PostingDate AS AccruedOn
            FROM PurchaseInvoice AS pi
                LEFT JOIN PurchaseInvoiceLine AS pil
                    ON pil.PurchaseInvoiceID = pi.PurchaseInvoiceID
                    AND pil.AccrualJournalEntryID IS NOT NULL
                LEFT JOIN JournalEntry AS je
                    ON je.JournalEntryID = pil.AccrualJournalEntryID
            WHERE {year_between(pp_, 'pi.InvoiceDate')}
                AND {year_between(c, 'pi.ReceivedDate')}
            ORDER BY pi.InvoiceNumber;
            """,
            [Check("invoices", [a["number"] for a in asv], lambda r: r.col("InvoiceNumber")),
             Check("amounts", [a["total"] for a in asv], lambda r: r.col("GrandTotal")),
             Check("their accruals", [a["je"] for a in asv], lambda r: r.col("AccrualEntry")),
             Check("accrued before the year-end", [True] * len(asv), lambda r: [x[5] <= f"{pp_}-12-31" for x in r.rows])])

    s.answer("Requirement 5", f"""
        Payroll accrual at {c}-12-31: the last eight processed periods ({p['start']} to {p['end']}) cost
        {money(p['cost'])} over {p['wd']} working days, {money(p['daily'])} a day; December 14-31 has {p['left']}
        working days, so the accrual is {money(p['accrual'])} (gross {money(p['gross'])}, employer taxes
        {money(p['tax'])}, benefits {money(p['ben'])}). Entries: debit 1090 for Manufacturing's whole cost,
        {money(n['mfg_all_in'])} (its gross pay and {money(n['mfg_employer'])} of employer costs), the other cost
        centers' salary accounts for their gross pay, {money(n['other_gross'])}, and 6060 for their employer costs only,
        {money(n['other_employer'])}; credit 2030 for gross pay, 2032 for employer taxes, and 2033 for benefits. The
        manufacturing part stays in 1090 until it is cleared. Completions continue to the year-end and have already
        released standard conversion cost ({n['in_window']['n']} completions dated December {n['left_day']} to 31
        released {money(n['in_window']['cost'])}), so posting the accrual does not create another release. For the income
        figures below, the accrual's manufacturing part and the prior year's ({money(prior['mfg'])}) are taken as costs of
        the period, a second entry moving each to 5080 (debit 5080, credit 1090). How much of either is normal
        conversion cost that belongs in inventory, and how much is abnormal, needs the overhead analysis of Requirement 4
        and evidence on normal capacity, and any other split changes the income and equity figures.

        The year-end before was not accrued either: {money(prior['total'])} of {pp_} work (manufacturing
        {money(prior['mfg'])}) was charged to fiscal {c}. Recording both raises {c} expense by only
        {money(n['change'])}, while the liability at {c}-12-31 rises by {money(p['accrual'])} and opening retained
        earnings fall by {money(prior['total'])}. The errors counterbalance in income but not on the balance sheet. The
        {money(n['opening'])} in 2030 is the opening line of {n['entry']}, and no payroll ever cleared it, so it is not
        the year-end accrual. Investigate it with the other unsupported opening balances of Chapter 8, and reverse it
        against opening retained earnings only if the investigation shows it is not owed (no payment in the records does
        not show that), rather than netting it against the new accrual.

        ASC Topic 330: {c}'s conversion cost on the ledger was {n['actual_rate']:.2f} per standard hour of the year's
        output against the standard {n['std_rate']:.2f}, a pay-year cost over output rather than a matching of hours to
        work. Raising the standards to absorb it would carry any idle capacity and any unsupported hours into finished goods
        ({money(n['fg'])} at year-end) and defer them to later years. Identified abnormal costs, such as idle capacity,
        belong in {c}'s cost of goods sold, and normal conversion cost needs a separate allocation on normal capacity.
        Hours with no support are not automatically hours not worked or an abnormal cost of the same amount, and
        measuring the abnormal part needs Requirement 4's analysis of the overhead.

        Cutoff (L5, L6): fiscal {c} revenue includes {money(n['delivered'])} of December {pp_} deliveries and excludes
        {n['n_uninv']} shipment lines of December {c} never invoiced, {money(n['uninv'])} at order price, whose standard
        cost ({money(n['uninv_std'])}) is already in cost of goods sold: {money(n['net_rev'])} more {c} revenue. Adjusted
        net income {money(ni)} - {money(n['change'])} + {money(n['net_rev'])} = {money(n['adj_ni'])}, on the assumption
        that the manufacturing parts are period costs and not an independently determined split of normal and abnormal
        cost (the ledger records no income tax). The net effect on income, {money(n['effect'])}, is {n['share']:.2%} of net income, but that does
        not make the errors immaterial. The liability left out is {n['liab_ni']:.1%} of net income and {n['liab_cl']:.1%}
        of current liabilities, the prior-year error moves opening retained earnings, and the missing year-end accrual
        is a deficiency in the close that recurs every year, so each is judged on its own and together with the
        qualitative factors. The case supplies no materiality threshold.

        Adjustment schedule, a proposal and not a change to the database, on the manufacturing assumption above. Round
        each line to cents and put any cent left over on a named line, never by changing a query total: the cost centers'
        amounts rounded one by one add to {money(n['centers_sum'])}, a cent off the accrual rounded once, so the entry
        is built from the totals. (1) Accrual: debit 1090 {money(n['mfg_all_in'])}, the other cost centers' salary
        accounts {money(n['other_gross'])} and 6060 {money(n['other_employer'])}; credit 2030 {money(p['gross'])}, 2032
        {money(p['tax'])} and 2033 {money(p['ben'])}. (2) The manufacturing part to the period: debit 5080, credit 1090,
        {money(n['mfg_all_in'])}. (3) The {pp_} work paid in {c}: debit opening retained earnings {money(prior['total'])};
        credit 5080 {money(n['split']['mfg'])} (Manufacturing, where the same assumption puts it), the salary accounts
        {money(n['split']['other_gross'])} and 6060 {money(n['split']['other_employer'])}, which carries the
        {money(n['split']['residual'])} left over from rounding. (4) The {pp_} revenue recognized in {c}: debit the
        revenue accounts and credit opening retained earnings {money(n['delivered'])}. (5) The {c} deliveries not
        invoiced: debit 1020 and credit the revenue accounts {money(n['uninv'])}, with no further cost of goods sold,
        because their {money(n['uninv_std'])} of standard cost is already recorded. The effects reconcile: receivables
        +{money(n['uninv'])}, liabilities +{money(p['accrual'])}, opening equity {money(n['open_equity'])}, the year's
        income {money(n['effect'])}, ending equity {money(n['end_equity'])}. The {money(n['opening'])} in 2030 is neither
        released nor netted. The estimate uses the manufacturing working-day calendar and the recent processed-payroll
        mix for every cost center, so check salary arrangements, unusual overtime and December work patterns, and true it
        up to the payroll actually posted. A different defensible allocation method is a sensitivity, not an arithmetic
        error in the stipulated method. {', '.join(a['number'] for a in asv)} is not a
        payables cutoff item: its accrual {', '.join(a['je'] for a in asv)} carried the liability at the year-end.""")


# --- Requirement 6: the memo -----------------------------------------------------------------------------------------

def r6(b: Build) -> None:
    d = b.data
    s = script(b)
    r3n, r4n, r5n = context(b, "r3"), context(b, "r4"), context(b, "r5")
    s.answer("Requirement 6", f"""
        Decision memo, in the order of the controller's questions. Auditing: the records outside the time clock do not
        support the surge-day hours as recorded, and the records that agree with them come from the same system (the
        punches) or the same manager (the rosters and the overtime approvals). The records outside the clock trail are
        not shown to be independent of that manager, so the question goes to evidence outside the database, and the
        hours should be called unsupported, not fictitious. Managerial accounting: output was flat while surge overtime
        {r3n['grew']}; {d.C} surge overtime cost {money(r3n['ys'][-1]['surge_premium'] * (1 + r3n['burden']))} as a
        premium or {money(r3n['ys'][-1]['surge_full'] * (1 + r3n['burden']))} in full, two alternatives rather than a
        sum; 5080 grew {money(r3n['bridge']['delta'])}, almost all of it payroll charged to 1090. The {d.N} plan at
        {r4n['levels'][1]:.2f} hours per standard hour needs {num(r4n['need'][1])} hours against
        {num(r4n['capacity'])} of regular capacity on the year's total and expects a variance of about
        {num(r4n['variance'][1])}. Financial reporting: record the payroll accrual of {money(r5n['p']['accrual'])} and
        the revenue cutoff ({money(r5n['net_rev'])}), for adjusted net income of {money(r5n['adj_ni'])}, on the stated
        assumption that the manufacturing parts are period costs. The net effect is small, but the liability left out is
        not, and each error is judged on its own. Identified abnormal costs are expensed, while normal conversion costs
        need a separate inventory-allocation analysis.

        Recommendation: stop routine surge days and require overtime to be approved in advance against a plan, by
        someone outside production; review the open attendance exceptions, obtain the rule's configuration, and add a
        rule that compares overtime with the roster; have internal audit corroborate a sample of surge days with access
        logs and interviews; adopt a {d.N} plan at about the {d.F} level of hours per standard hour as a target to test,
        with no routine overtime, since the year's capacity allows it, and exceptions approved against a dated plan; keep
        the direct-hour standards provisionally, since the records give no reason to revise them and the comparison does
        not show they are right, and review the overhead rates on normal capacity; and record the year-end payroll accrual now and at every year-end.""")


EXERCISES = [("Requirement 1", r1), ("Requirement 2", r2), ("Requirement 3", r3), ("Requirement 4", r4),
             ("Requirement 5", r5), ("Requirement 6", r6)]
