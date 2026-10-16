"""The Part III case's instructor guides: the values the guides state, and the claims their wording makes.

The case (cases/part-3-case.qmd, "Planning the Plant's Hours for 2027") is worked in one SQL script, Case.sql, whose model
answer is outputs/companion/solutions/PartIII-case-sql/Case.sql (71 queries, eight saved views).  The registered notes
case3.r1 to case3.r5 (facts/notes/case3.py) already supply the expected values of the requirements; these contexts add what
the model paths need beyond them: the row count each quoted query reports, and the result of every wrong variant a guide
names, run read-only on the model script's own text with one change, so the symptom a guide describes is the symptom of the
very query it quotes.  They also check, with claim(), every table and column the guides name and every statement about the
data that another dataset could falsify.

The model script's views (SurgeDays, PlantEntries, PlantWeeks, PlantLedger, PlantAssets, PayrollAccrual, PriorYearWork,
CutoffItems) and Tutorial 11.3's MonthlyLaborEfficiency (from Setup_Part3_Views.sql) are created as TEMP views for the length of
one context and dropped again, because the Data object is shared and Chapter 11's contexts create the same view name.

Keys: case3.chapter (the case note) and case3.g1 to case3.g6 (the six requirements, each used next to the note case3.r1 to
case3.r5 that supplies the values of the requirement's instructor note; Requirement 6 has no note and uses the others).
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, schema
from guide_contexts.ch12 import tutorial_sql

REPO = Path(__file__).resolve().parents[3]
CASE = REPO / "cases" / "part-3-case.qmd"
DECK = REPO / "slides" / "case-part-3" / "index.qmd"
DOWNLOADS = REPO / "front-matter" / "downloads.qmd"
SOLUTION = REPO / "outputs" / "companion" / "solutions" / "PartIII-case-sql" / "Case.sql"
SETUP = REPO / "supplementary" / "start-files" / "Setup_Part3_Views.sql"

SCHEMA = {
    "TimeClockPunch": ["TimeClockPunchID", "EmployeeID", "WorkDate", "EmployeeShiftRosterID", "TimeClockEntryID", "WorkCenterID",
                       "PunchTimestamp", "PunchType", "PunchSource"],
    "TimeClockEntry": ["TimeClockEntryID", "EmployeeID", "WorkDate", "EmployeeShiftRosterID", "OvertimeApprovalID", "ClockInTime",
                       "ClockOutTime", "RegularHours", "OvertimeHours", "ClockStatus"],
    "EmployeeShiftRoster": ["EmployeeShiftRosterID", "EmployeeID", "RosterDate", "ScheduledStartTime", "ScheduledEndTime",
                            "ScheduledHours", "RosterStatus", "CreatedByEmployeeID", "CreatedDate"],
    "AttendanceException": ["AttendanceExceptionID", "EmployeeID", "WorkDate", "TimeClockEntryID", "ExceptionType", "Severity",
                            "MinutesVariance", "Status", "ReviewedByEmployeeID"],
    "WorkCenterCalendar": ["WorkCenterID", "CalendarDate", "IsWorkingDay", "AvailableHours", "ExceptionReason"],
    "RoughCutCapacityPlan": ["BucketWeekStartDate", "WorkCenterID", "PlannedLoadHours", "AvailableHours"],
    "EmployeeAbsence": ["EmployeeID", "AbsenceDate"],
    "OvertimeApproval": ["OvertimeApprovalID", "WorkDate", "WorkOrderOperationID", "ReasonCode", "ApprovedByEmployeeID"],
    "WorkOrderOperation": ["WorkOrderOperationID", "ActualEndDate"],
    "WorkOrder": ["ReleasedDate", "CompletedDate", "ClosedDate"],
    "WorkOrderClose": ["CloseDate", "MaterialVarianceAmount"],
    "ProductionCompletion": ["ProductionCompletionID", "CompletionDate"],
    "ProductionCompletionLine": ["ProductionCompletionID", "ItemID", "QuantityCompleted", "ExtendedStandardConversionCost",
                                 "ExtendedStandardDirectLaborCost", "ExtendedStandardVariableOverheadCost",
                                 "ExtendedStandardFixedOverheadCost"],
    "Item": ["ItemID", "ItemGroup", "SupplyMode", "StandardLaborHoursPerUnit"],
    "Employee": ["EmployeeID", "JobTitle", "CostCenterID", "PayClass", "IsActive", "BaseHourlyRate"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
    "PayrollPeriod": ["PayrollPeriodID", "PeriodNumber", "PeriodStartDate", "PeriodEndDate", "PayDate", "FiscalYear", "Status"],
    "PayrollRegister": ["PayrollPeriodID", "EmployeeID", "CostCenterID", "GrossPay", "EmployerPayrollTax", "EmployerBenefits"],
    "FixedAsset": ["AssetCode", "InServiceDate", "DisposalDate", "UsefulLifeMonths", "OriginalCost", "DepreciationDebitAccountID"],
    "BudgetLine": ["FiscalYear", "ItemID", "Quantity", "BudgetCategory", "CostCenterID"],
    "DemandForecast": ["ForecastWeekStartDate", "ItemID", "ForecastQuantity", "IsCurrent"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "SourceDocumentID", "CostCenterID",
                "FiscalYear"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"],
    "JournalEntry": ["JournalEntryID", "EntryNumber", "EntryType"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SubTotal"],
    "ShipmentLine": ["ShipmentLineID", "ShipmentID", "SalesOrderLineID", "QuantityShipped", "ExtendedStandardCost"],
    "Shipment": ["ShipmentID", "ShipmentNumber", "ShipmentDate", "DeliveryDate"],
}

VIEWS = ["SurgeDays", "PlantEntries", "PlantWeeks", "PlantLedger", "PlantAssets", "PayrollAccrual", "PriorYearWork", "CutoffItems",
         "MonthlyLaborEfficiency"]


# --- the model script -----------------------------------------------------------------------------------------------------

def norm(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().rstrip(";").strip())


def sub(sql: str, old: str, new: str, count: int = 1) -> str:
    """The statement with `old` replaced by `new`, ignoring differences in whitespace; the text must be there."""
    pattern = r"\s+".join(re.escape(w) for w in old.split())
    if not re.search(pattern, sql):
        raise ValueError(f"the text to change is not in the statement: {old[:70]}")
    return re.sub(pattern, lambda m: new, sql, count=count)


@lru_cache(maxsize=None)
def script() -> tuple[tuple[str, str], ...]:
    """(first comment line, statement) of every query of Case.sql, in order; the trailing result comment is dropped."""
    body = SOLUTION.read_text(encoding="utf-8").split("/* Model answer", 1)[0]
    out = []
    for chunk in re.split(r"(?m)^(?=-- Requirement \d+:)", body):
        if not chunk.startswith("-- Requirement"):
            continue
        lines = chunk.rstrip().split("\n")
        stmt = re.sub(r";[ \t]*-- Result:[^\n]*$", ";", "\n".join(lines[2:]), flags=re.M)
        out.append((lines[0], stmt.strip()))
    return tuple(out)


@lru_cache(maxsize=None)
def view_texts() -> dict[str, str]:
    """The CREATE VIEW statement of each saved view, from the model script and from Setup_Part3_Views.sql."""
    found = {}
    for _, stmt in script():
        m = re.match(r"(?s)DROP VIEW IF EXISTS (\w+);\s*(CREATE VIEW \1 AS.*)", stmt)
        if m:
            found[m.group(1)] = m.group(2).rstrip().rstrip(";")
    setup = SETUP.read_text(encoding="utf-8")
    m = re.search(r"(?s)(CREATE VIEW MonthlyLaborEfficiency AS.*?);[ \t]*(?:--[^\n]*)?(?:\n|$)", setup)
    found["MonthlyLaborEfficiency"] = m.group(1).rstrip()
    return found


def temp(sql: str) -> str:
    return re.sub(r"(?i)^CREATE VIEW", "CREATE TEMP VIEW", sql, count=1)


class Kit:
    """Runs the model script's queries and variants of them against the open database."""

    def __init__(self, d):
        self.d = d

    def q(self, sql: str) -> list:
        return self.d.q(sql.strip().rstrip(";"))

    def stmt(self, key: str) -> str:
        hits = [s for first, s in script() if key in first]
        if len(hits) != 1:
            raise KeyError(f"{len(hits)} queries of Case.sql contain {key!r}")
        return hits[0]

    def run(self, key: str) -> list:
        return self.q(self.stmt(key))

    def n(self, key: str) -> int:
        return len(self.run(key))

    def alt(self, key: str, old: str, new: str) -> list:
        return self.q(sub(self.stmt(key), old, new))

    def body(self, view: str) -> str:
        return view_texts()[view].split(" AS\n", 1)[1]

    @contextmanager
    def swapped(self, view: str, old: str, new: str):
        """The saved view with one change, for the length of the block."""
        self.d.con.execute(f"DROP VIEW IF EXISTS temp.{view}")
        self.d.con.execute(temp(sub(view_texts()[view], old, new)))
        try:
            yield
        finally:
            self.d.con.execute(f"DROP VIEW IF EXISTS temp.{view}")
            self.d.con.execute(temp(view_texts()[view]))


@contextmanager
def kit(d):
    def drop():
        for v in VIEWS:
            d.con.execute(f"DROP VIEW IF EXISTS temp.{v}")
    drop()
    texts = view_texts()
    for v in ["MonthlyLaborEfficiency"] + [v for v in VIEWS if v != "MonthlyLaborEfficiency"]:
        d.con.execute(temp(texts[v]))
    try:
        yield Kit(d)
    finally:
        drop()


def deck_titles() -> list[str]:
    """The slide titles of the case's deck in order, the title slide first."""
    titles = ["(title slide)"]
    for line in DECK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,2} (.+?)\s*(\{[^}]*\})?\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    return titles


def at(titles: list[str], first: str) -> int:
    return next(n for n, t in enumerate(titles, 1) if t.startswith(first))


def span(titles: list[str], first: str, after: str | None = None) -> str:
    start = at(titles, first)
    end = (at(titles, after) - 1) if after else start
    return str(start) if end <= start else f"{start} to {end}"


def short(name: str) -> str:
    return name.replace(" Work Center", "")


# --- the case note ----------------------------------------------------------------------------------------------------------

@context("case3.chapter")
def chapter(d, claim):
    schema(d, claim, SCHEMA)
    titles = deck_titles()
    claim(len(titles) == 33, "the case's deck has 33 slides")
    text = CASE.read_text(encoding="utf-8")
    n_req = len(re.findall(r"^\*\*Requirement \d+:", text, re.M))
    claim(n_req == 6, "the case has six requirements")
    claim("Milestone" not in text, "the case has no milestones")
    downloads = DOWNLOADS.read_text(encoding="utf-8")
    claim("PartIII-case-sql.zip" in downloads and "Setup_Part3_Views.sql" in downloads,
          "the Downloads page lists the Part III solution, PartIII-case-sql.zip, and the views script, Setup_Part3_Views.sql")
    queries = script()
    per_req = Counter(int(re.match(r"-- Requirement (\d+):", first).group(1)) for first, _ in queries)
    claim(len(queries) == 71, "the model script holds 71 queries")
    claim(len(view_texts()) == len(VIEWS), "the model script saves eight views and reads Tutorial 11.3's")
    hourly = d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
                   "WHERE cc.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly' AND e.IsActive = 1")
    cc_all = d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
                   "WHERE cc.CostCenterName = 'Manufacturing'")
    claim(cc_all > hourly, "the Manufacturing cost center has employees besides its hourly ones (the salaried staff)")
    return dict(
        n_req=n_req, slides=len(titles), n_queries=len(queries), per_req=dict(per_req), n_views=len(VIEWS) - 1,
        hourly=hourly, cost_center=cc_all, first_year=d.F, prior_year=d.P, last_year=d.C, plan_year=d.N,
        slide=dict(intro=at(titles, "In this case"), question=at(titles, "What should the plant plan for"),
                   handin=at(titles, "What you will hand in"), criteria=span(titles, "How your work will be judged", "The Situation"),
                   situation=span(titles, "The audit left one question open", "The Data You Will Use"),
                   unsupported=at(titles, "Call the hours unsupported"), questions=at(titles, "Four questions"),
                   data=span(titles, "Work in Case.sql", "Requirements"), tables=at(titles, "Tables the chapters"),
                   calendars=at(titles, "Watch out: three calendars"), cal_check=at(titles, "Each measure has its calendar") - 1,
                   cal_answer=at(titles, "Each measure has its calendar"), dates=at(titles, "Watch out: dates without days"),
                   six=at(titles, "Six requirements"), r1=at(titles, "Build the case script"),
                   r2=at(titles, "Test whether other records"), indep_check=at(titles, "Independence depends") - 1,
                   indep_answer=at(titles, "Independence depends"), r3=at(titles, "What the hours produced"),
                   r4=at(titles, "Plan the new year"), r5=at(titles, "Close the fiscal year"),
                   inv_check=at(titles, "The inventory standard decides") - 1, inv_answer=at(titles, "The inventory standard decides"),
                   r6=at(titles, "Write the decision memo"), before=at(titles, "Before you submit"),
                   ahead=span(titles, "From queries to reports", "About these slides")))


# --- requirement 1: the script and its populations ------------------------------------------------------------------------

@context("case3.g1")
def g1(d, claim):
    schema(d, claim, SCHEMA)
    with kit(d) as k:
        rows = {name: k.run(key) for name, key in dict(
            punch_profile="profile of TimeClockPunch", codes="the code columns of TimeClockPunch", repeats="keys of TimeClockPunch",
            no_out="clock-in punch and no clock-out", roster_profile="profile of EmployeeShiftRoster", statuses="the roster statuses",
            creators="who created the rosters", exc_profile="profile of AttendanceException", cal_profile="profile of WorkCenterCalendar",
            cal_2026="the calendar of 2026 by exception reason", cal_days="the working days and available hours of 2026",
            punch_links="punches whose employee or date", roster_links="clock entries whose roster is missing",
            detached="punches detached from their clock entry", dispositions="each attendance exception against",
            reconcile="the two views reconciled").items()}
        n = {name: len(r) for name, r in rows.items()}
        profile = rows["punch_profile"][0]
        cal = rows["cal_profile"][0]
        cal_dates = d.one("SELECT COUNT(DISTINCT CalendarDate) FROM WorkCenterCalendar")
        claim(cal[4] == cal[0] and cal_dates * cal[1] == cal[0], "WorkCenterCalendar has one row for each work center and date, "
              "so each date appears once for every work center")
        claim(profile[5] < profile[0] and profile[6] < profile[5], "of the punches, the roster link is blank on a few and "
              "the work center on many more")
        claim(d.one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND tbl_name = 'TimeClockPunch' "
                    "AND sql LIKE '%TimeClockEntryID%'") == 0, "TimeClockPunch has no index on TimeClockEntryID")
        per_entry = d.q("SELECT MIN(n), MAX(n) FROM (SELECT COUNT(*) AS n FROM TimeClockPunch GROUP BY TimeClockEntryID)")[0]
        claim(per_entry == (2, 4), "a clock entry has two to four punches")
        links = rows["punch_links"]
        date_only = sum(r[2] for r in links)
        employee_only = sum(r[3] for r in links)
        claim(date_only > 0 and employee_only == 0, "the punches that differ from their clock entry differ in the date and never in the employee")
        disp = Counter(r[-1] for r in rows["dispositions"])
        order = [(label.split(":")[0], c) for label, c in disp.most_common()]
        reordered = k.alt("each attendance exception against",
                          "WHEN ae.EmployeeID <> tc.EmployeeID THEN 'Names another employee: correct the report' "
                          "WHEN ae.ExceptionType = 'Paid Without Approved Clock' THEN 'Paid on a Pending entry (test H1): follow up'",
                          "WHEN ae.ExceptionType = 'Paid Without Approved Clock' THEN 'Paid on a Pending entry (test H1): follow up' "
                          "WHEN ae.EmployeeID <> tc.EmployeeID THEN 'Names another employee: correct the report'")
        claim(Counter(r[-1] for r in reordered) == disp, "no exception is both of a type the CASE tests and a name that differs, "
              "so the order of its first two tests does not change a count")
        exc = d.q("SELECT COUNT(*), COUNT(DISTINCT TimeClockEntryID) FROM AttendanceException")[0]
        plant_twice = d.one("SELECT COUNT(*) FROM (SELECT ae.TimeClockEntryID FROM AttendanceException ae JOIN PlantEntries pe "
                            "ON pe.TimeClockEntryID = ae.TimeClockEntryID GROUP BY ae.TimeClockEntryID HAVING COUNT(*) > 1)")
        claim(exc[1] < exc[0] and plant_twice == 0, "some clock entries carry two or more exceptions, but none of them is a plant entry")
        multi = d.q("SELECT ae.TimeClockEntryID, COUNT(*), MIN(tc.EmployeeID) FROM AttendanceException ae JOIN TimeClockEntry tc "
                    "ON tc.TimeClockEntryID = ae.TimeClockEntryID GROUP BY ae.TimeClockEntryID HAVING COUNT(*) > 1 ORDER BY 1")
        claim(len({r[2] for r in multi}) == 1 and all(r[2] == multi[0][2] for r in multi), "the entries that carry several exceptions all belong to one employee")
        # the views
        surge_body, plant_body = k.body("SurgeDays"), k.body("PlantEntries")
        claim(norm(surge_body) in norm(tutorial_sql("H9")), "the SurgeDays view is the definition of the SurgeDays CTE of Tutorial 12.3's test H9")
        no_mfg = d.one(f"SELECT COUNT(*) FROM ({sub(surge_body, 'WHERE cc.CostCenterName = ' + chr(39) + 'Manufacturing' + chr(39), 'WHERE 1 = 1')})")
        no_single = d.one(f"SELECT COUNT(*) FROM ({sub(surge_body, 'AND COUNT(DISTINCT tc.EmployeeID) > 1', '')})")
        by_rows = d.one(f"SELECT COUNT(*) FROM ({sub(surge_body, 'AND COUNT(DISTINCT tc.EmployeeID) > 1', 'AND COUNT(*) > 1')})")
        surge_n = d.one("SELECT COUNT(*) FROM SurgeDays")
        claim(no_mfg == 0, "without the Manufacturing filter no day of the company has one pattern of hours")
        claim(no_single == surge_n, "every Manufacturing work date has more than one employee clocking in, so the test for more than one employee removes nothing")
        claim(by_rows == surge_n, "counting clock rows instead of employees gives the same surge days here")
        inner = d.one(f"SELECT COUNT(*) FROM ({sub(plant_body, 'LEFT JOIN SurgeDays', 'INNER JOIN SurgeDays')})")
        no_class = d.one(f"SELECT COUNT(*) FROM ({sub(plant_body, 'AND e.PayClass = ' + chr(39) + 'Hourly' + chr(39), '')})")
        entries = d.one("SELECT COUNT(*) FROM PlantEntries")
        claim(no_class == entries, "every Manufacturing clock entry belongs to an hourly employee, so the PayClass filter removes nothing")
        try:
            k.d.con.execute(temp(view_texts()["SurgeDays"]))
            again = ""
        except Exception as exc_:                             # noqa: BLE001
            again = str(exc_)
        claim("already exists" in again, "creating a view that exists, with no DROP VIEW before it, fails with 'already exists'")
        h8 = d.q(sql_h8())
        claim([r[1] for r in h8] == [r[1] for r in rows["reconcile"]], "the SurgeDays view gives the surge days that Tutorial 12.3's test H8 counts")
        hourly = d.one("SELECT COUNT(DISTINCT EmployeeID) FROM PlantEntries")
        cc_staff = d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
                         "WHERE cc.CostCenterName = 'Manufacturing'")
    return dict(
        n=n, profile=profile, cal=cal, cal_dates=cal_dates, per_entry=per_entry, date_only=date_only, employee_only=employee_only,
        disp=order, exceptions=exc[0], exception_entries=exc[1], multi=multi, multi_total=sum(r[1] for r in multi), no_mfg=no_mfg, inner=inner, entries=entries, again=again,
        reconcile=rows["reconcile"], hourly=hourly, cost_center_staff=cc_staff, links_punch_entries=len(links),
        no_out=[(r[0], r[1], r[2]) for r in rows["no_out"]], detached=len(rows["detached"]), roster_off=len(rows["roster_links"]),
        statuses=rows["statuses"], creators=rows["creators"], exc_types=len(rows["exc_profile"]))


def sql_h8() -> str:
    return tutorial_sql("H8")


# --- requirement 2: do other records support the surge days ---------------------------------------------------------------

@context("case3.g2")
def g2(d, claim):
    schema(d, claim, SCHEMA)
    with kit(d) as k:
        keys = dict(
            daily="surge days against ordinary days, attendance", meals="entries with meal punches", punch_times="clock punches whose timestamp",
            rosters="the rosters of the surge-day entries", mfg_creators="who creates the rosters of the Manufacturing",
            minutes="minutes of clock time before and after", roster_hours="rostered hours against the hours clocked",
            off_shift="the Off Shift Clocking exceptions against", rule="the Off Shift Clocking rule reperformed",
            operation="the operation of the attendance-exception control", calendar="the calendar status of each surge day",
            load="planned load against available hours", reasons="the reason codes and approver",
            approvals="overtime approvals that cite", weekdays="surge days by day of the week",
            absences="absences recorded by cost center")
        rows = {name: k.run(key) for name, key in keys.items()}
        n = {name: len(r) for name, r in rows.items()}
        daily_key = keys["daily"]
        # the attendance counted in clock rows rather than people
        by_rows = k.alt(daily_key, "COUNT(DISTINCT EmployeeID) AS Employees", "COUNT(*) AS Employees")
        rows_present = {r[0]: r[3] for r in by_rows}
        people_present = {r[0]: r[3] for r in rows["daily"]}
        claim(rows_present["Ordinary"] != people_present["Ordinary"] and rows_present["Surge"] == people_present["Surge"],
              "counting clock rows instead of people changes the ordinary days with everyone present, and not the surge days")
        # the largest group on one clock-in time: a window with no ClockInTime in its partition
        flat = k.alt(daily_key, "COUNT(*) OVER (PARTITION BY WorkDate, ClockInTime)", "COUNT(*) OVER (PARTITION BY WorkDate)")
        flat_largest = {r[0]: r[5] for r in flat}
        claim(flat_largest["Surge"] == 64.0 and flat_largest["Ordinary"] > 60,
              "a window partitioned by the date alone counts the day's whole attendance, so the largest group equals the attendance")
        # the plant's headcount taken from the whole cost center
        cost_center = k.alt(daily_key, "WHERE cc.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly' )",
                            "WHERE cc.CostCenterName = 'Manufacturing' )")
        all_present_67 = sum(r[3] for r in cost_center)
        claim(all_present_67 == 0, "no day has as many entries as the Manufacturing cost center has employees, because its salaried staff keep no time clock")
        # meal punches joined without summarizing
        fan = k.alt(keys["meals"], "WITH Meals AS ( SELECT TimeClockEntryID FROM TimeClockPunch WHERE PunchType = 'Meal Start' "
                    "GROUP BY TimeClockEntryID )", "WITH Meals AS ( SELECT TimeClockEntryID FROM TimeClockPunch "
                    "WHERE PunchType IN ('Meal Start', 'Meal End') )")
        fan_entries = {r[0]: r[1] for r in fan}
        meal_entries = {r[0]: r[1] for r in rows["meals"]}
        claim(all(fan_entries[t] > meal_entries[t] for t in meal_entries), "joining both meal punches of an entry repeats the entry")
        # the roster's start time without its date, and the clock-out as a time of day
        no_date = k.alt(keys["minutes"], "julianday(r.RosterDate || ' ' || r.ScheduledStartTime)", "julianday(r.ScheduledStartTime)")
        no_date_min = min(abs(r[3]) for r in no_date)
        time_of_day = k.alt(keys["minutes"], "ROUND((julianday(pe.ClockOutTime) - julianday(r.RosterDate || ' ' || r.ScheduledEndTime)) * 1440) "
                            "AS MinutesLate", "ROUND((strftime('%s', time(pe.ClockOutTime)) - strftime('%s', r.ScheduledEndTime)) / 60.0) "
                            "AS MinutesLate")
        tod_late = sorted({r[4] for r in time_of_day})
        claim(no_date_min > 1_000_000, "a roster time with no date is read as a day in the year 2000, so its distance from a clock time is millions of minutes")
        claim(tod_late[0] < 0 < tod_late[-1], "the time of day of a clock-out after midnight is earlier than the roster's end, so it reads as leaving early")
        # the rule
        rule = rows["rule"]
        by_type = {r[0]: r for r in rule}
        late_in = d.q("SELECT COUNT(*), SUM(r.RosterDate <> pe.WorkDate) FROM PlantEntries pe JOIN EmployeeShiftRoster r "
                      "ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID WHERE ROUND((julianday(pe.ClockInTime) - "
                      "julianday(r.RosterDate || ' ' || r.ScheduledStartTime)) * 1440) >= (SELECT MIN(MinutesVariance) FROM "
                      "AttendanceException WHERE ExceptionType = 'Off Shift Clocking')")[0]
        claim(late_in[0] == by_type["Ordinary"][2] and late_in[0] == late_in[1],
              "the ordinary entries that arrive the rule's minutes late are all rostered on another date (Requirement 1's shifted entries)")
        gt = k.alt(keys["rule"], "WHEN t.Arrival >= (SELECT Minutes FROM RuleMinutes)", "WHEN t.Arrival > (SELECT Minutes FROM RuleMinutes)")
        ge = k.alt(keys["rule"], "WHEN t.Departure > (SELECT Minutes FROM RuleMinutes)", "WHEN t.Departure >= (SELECT Minutes FROM RuleMinutes)")
        raw = k.alt(keys["rule"], "ROUND((julianday(pe.ClockOutTime) - julianday(r.RosterDate || ' ' || r.ScheduledEndTime)) * 1440) AS Departure",
                    "(julianday(pe.ClockOutTime) - julianday(r.RosterDate || ' ' || r.ScheduledEndTime)) * 1440 AS Departure")
        ge_o, raw_o = {r[0]: r for r in ge}["Ordinary"][3], {r[0]: r for r in raw}["Ordinary"][3]
        rule_o = {r[0]: r for r in rule}["Ordinary"][3]
        ungrouped = k.alt(keys["rule"], "Flagged AS ( SELECT TimeClockEntryID FROM AttendanceException GROUP BY TimeClockEntryID )",
                          "Flagged AS ( SELECT TimeClockEntryID FROM AttendanceException )")
        claim(gt == rule, "no plant entry arrives exactly on the rule's minutes, so > and >= give the same arrivals")
        claim(ge_o > rule_o and raw_o != rule_o, "some ordinary entries leave exactly the rule's minutes late, so in whole minutes >= counts more "
              "than >, and the raw julianday minutes put some of those exact cases on the wrong side")
        claim(ungrouped == rule, "no plant entry carries two exceptions, so joining the exceptions without grouping them gives the same counts")
        claim(by_type["Surge"][2] == 0 and by_type["Surge"][3] == by_type["Surge"][1] and by_type["Surge"][4] == 0,
              "no surge entry arrives late, every one leaves late by the rule's minutes, and none was flagged")
        off = rows["off_shift"]
        minutes_rule = off[0][1]
        claim(all(r[1] == minutes_rule == r[4] for r in off), "each Off Shift Clocking exception records the minutes its clock-in was after the scheduled start")
        # the plan: available hours summed straight from the item rows, and weeks beyond the last time record
        flat_load = k.alt(keys["load"], "SUM(PlannedLoadHours) AS PlannedHours, MAX(AvailableHours) AS AvailableHours",
                          "SUM(PlannedLoadHours) AS PlannedHours, SUM(AvailableHours) AS AvailableHours")
        flat_shares = [r[3] for r in flat_load]
        claim(max(flat_shares) < 0.05, "summing the available hours of every item row makes the load a few hundredths of capacity")
        no_cut = k.alt(keys["load"], "WHERE w.WeekStart <= ( SELECT date(MAX(WorkDate), '-6 days', 'weekday 1') FROM TimeClockEntry)", "")
        surge_load = [r for r in rows["load"] if r[1] == "Surge days"]
        claim(sum(r[4] for r in surge_load) > 0 and all(r[3] < 1 for r in rows["load"]),
              "every group of weeks is planned below capacity on average, yet some surge weeks are planned above it")
        beyond = [r for r in no_cut if r[0] > str(d.C)]
        claim(len(beyond) == 1 and len(no_cut) == len(rows["load"]) + 1, "the plan runs into the next year, one more row")
        weekday1 = k.alt(keys["load"], "date(WorkDate, '-6 days', 'weekday 1')", "date(WorkDate, 'weekday 1')")
        w_last = [r for r in weekday1 if r[0] == str(d.C)]
        w_ref = [r for r in rows["load"] if r[0] == str(d.C)]
        claim(w_last != w_ref, "'weekday 1' alone moves each date to the next Monday and changes the weeks of surge days")
        # the approvals
        ap = k.alt(keys["approvals"], "LEFT JOIN WorkOrderOperation AS op", "INNER JOIN WorkOrderOperation AS op")
        le = k.alt(keys["approvals"], "WHEN op.ActualEndDate < oa.WorkDate", "WHEN op.ActualEndDate <= oa.WorkDate")
        cite = {r[0]: r for r in rows["approvals"]}
        claim(all(r[1] == r[2] for r in ap) and {r[0]: r[1] for r in ap} == {t: cite[t][2] for t in cite},
              "an inner join to the operations keeps only the approvals that cite one")
        claim({r[0]: r[3] for r in le}["Ordinary"] == cite["Ordinary"][2], "an operation that ends on the work date is open on it, so < and <= differ on ordinary days")
        centers = [r[0] for r in rows["absences"]]
        claim("Manufacturing" not in centers, "the absence records hold no absence in Manufacturing")
        claim({r[2] for r in rows["reasons"]} == {r[3] for r in rows["rosters"]}, "the manager who created the surge rosters approved every surge-day overtime")
        days_ahead = {r[4] for r in rows["rosters"]}
        claim(days_ahead == {7.0}, "every surge entry was rostered seven days ahead")
        cost_center_staff = d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
                                  "WHERE cc.CostCenterName = 'Manufacturing'")
    return dict(cost_center_staff=cost_center_staff,
        n=n, flat_largest=flat_largest, all_present_67=all_present_67, fan_entries=fan_entries, meal_entries=meal_entries,
        no_date_min=no_date_min, tod_late=tod_late, rule=rule, minutes_rule=minutes_rule, flat_shares=flat_shares,
        beyond=beyond, weekday1=w_last, ap_inner=ap, le=le, centers=centers, load=rows["load"], cite=cite,
        rosters=rows["rosters"], operation=rows["operation"], calendar=rows["calendar"],
        by_type=by_type, ordinary_ended_le={r[0]: r[3] for r in le}["Ordinary"], ge_ordinary=ge_o, raw_ordinary=raw_o, rows_present=rows_present,
        surge_load=surge_load)


# --- requirement 3: what the hours produced and what they cost -----------------------------------------------------------

@context("case3.g3")
def g3(d, claim):
    schema(d, claim, SCHEMA)
    with kit(d) as k:
        keys = dict(
            year="hours clocked against the standard hours", december="the December values of MonthlyLaborEfficiency",
            groups="the weeks of 2026 grouped", versus="weeks with surge days against weeks without",
            limits="what limits the weekly comparison", capacity="regular capacity the ordinary days used",
            cost="the cost of the surge-day overtime at base rates", ledger="the ledger lines of 5080 by fiscal year",
            bridge="the bridge of 5080 from fiscal 2024", direct="the postings made directly to 5080",
            measures="three measures of the payroll line")
        rows = {name: k.run(key) for name, key in keys.items()}
        n = {name: len(r) for name, r in rows.items()}
        year = rows["year"]
        no_cut = k.alt(keys["year"], "WHERE pc.CompletionDate <= (SELECT MAX(WorkDate) FROM TimeClockEntry)", "")
        claim(no_cut[-1][3] < year[-1][3] and no_cut[0] == year[0], "counting the output to the end of the last year lowers its ratio and leaves the first year unchanged")
        claim([round(r[3], 2) for r in year] == [round(r[3], 2) for r in rows["december"]],
              "the ratio of each year equals the December value of Tutorial 11.3's trailing measure")
        err = ""
        d.con.execute("DROP VIEW IF EXISTS temp.MonthlyLaborEfficiency")
        try:
            k.run(keys["december"])
        except sqlite3.OperationalError as exc:
            err = str(exc)
        finally:
            d.con.execute(temp(view_texts()["MonthlyLaborEfficiency"]))
        claim(err == "no such table: MonthlyLaborEfficiency", "without the saved view the December query fails with 'no such table'")

        # the weekly view
        def groups_with(old, new):
            with k.swapped("PlantWeeks", old, new):
                return k.run(keys["groups"])
        model_next = [r[5] for r in rows["groups"]]
        cumulative = groups_with("ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING", "ROWS UNBOUNDED PRECEDING")
        cum_next = [r[5] for r in cumulative]
        own_week = groups_with("ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING", "ROWS BETWEEN CURRENT ROW AND 5 FOLLOWING")
        own_next = [r[5] for r in own_week]
        claim(max(cum_next) - min(cum_next) < 0.1 * max(cum_next), "a running average of the earlier weeks is nearly the same for every group of weeks")
        claim(own_next != model_next, "a frame that includes the week itself changes the average of its following weeks")
        claim(d.one("SELECT COUNT(*) FROM PlantWeeks WHERE StandardHours = 0") == 0, "every week with hours has some completions, so the join to output loses no week")
        with k.swapped("PlantWeeks", "WHERE pc.CompletionDate <= (SELECT MAX(WorkDate) FROM TimeClockEntry)", ""):
            versus_no_cut = k.run(keys["versus"])
        surge_v = next(r for r in rows["versus"] if r[0] == str(d.C) and r[1] == "Surge days")
        surge_nc = next(r for r in versus_no_cut if r[0] == str(d.C) and r[1] == "Surge days")
        claim(surge_nc[4] > surge_v[4], "without the cut-off the weekly output takes in the completions dated after the last day with time records")
        short = sum(r[7] for r in rows["versus"] if r[0] == str(d.C))
        claim(short > 0, "some frames at the end of the series hold fewer than six weeks")
        # cost
        all_centers = k.alt(keys["cost"], "WHERE cc.CostCenterName = 'Manufacturing' GROUP BY pp.FiscalYear", "GROUP BY pp.FiscalYear")
        claim(all_centers[-1][4] < rows["cost"][-1][4], "the burden of all cost centers is lower than the plant's")
        cap = rows["capacity"]
        claim(cap[-1][2] > 2 * cap[-1][3], "the last year's unused straight time is more than twice its surge overtime")
        # the ledger
        with k.swapped("PlantLedger", "AND gl.VoucherNumber NOT IN ( SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%')", ""):
            closes_in = k.run(keys["ledger"])
        with k.swapped("PlantLedger", "WHERE a.AccountNumber IN (1090, 5080)", "WHERE gl.AccountID IN (1090, 5080)"):
            by_id = k.run(keys["ledger"])
        claim(all(abs(r[7]) < 0.005 for r in closes_in), "with the year-end closes left in, account 5080 nets to zero in every year")
        claim(by_id == [] and d.one("SELECT MAX(AccountID) FROM Account") < 1090, "no AccountID is as large as 1090, so a filter on the number as an AccountID finds nothing")
        claim(all(abs(r[9]) < 0.005 for r in rows["ledger"]), "the ledger lines add up to account 5080 in every year")
        # the measures
        m = rows["measures"][0]
        m_cut = k.alt(keys["measures"], "WHERE pc.CompletionDate <= (SELECT MAX(WorkDate) FROM TimeClockEntry)", "")[0]
        m_cal = k.alt(keys["measures"], "(lc.PayDates - lf.PayDates) * lf.Payroll / lf.PayDates", "(lc.PayDates - lf.PayDates) * lc.Payroll / lc.PayDates")[0]
        claim(m[6] > 0 and m_cut[6] < m[6], "the three measures exceed the payroll line, and by less when the output is counted to the year's end")
        two_dates = d.q("SELECT FiscalYear, PayDates FROM PlantLedger ORDER BY 1")
        claim(two_dates[-1][1] - two_dates[0][1] == 2, "the last year posted two more payrolls to 1090 than the first")
    return dict(
        n=n, year=year, no_cut=no_cut[-1], december=rows["december"], groups=rows["groups"], versus=rows["versus"], err=err,
        cum_next=cum_next, own_next=own_next, limits=rows["limits"][0], capacity=cap, cost=rows["cost"], all_centers=all_centers,
        ledger=rows["ledger"], closes_in=closes_in, by_id=len(by_id), bridge=rows["bridge"][0], direct=rows["direct"], m=m, m_cut=m_cut,
        m_cal=m_cal, pay_dates=two_dates, surge_no_cut=surge_nc, short=short,
        ind_end=d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry WHERE LaborType = 'Indirect Manufacturing'"))


# --- requirement 4: the plan ----------------------------------------------------------------------------------------------

@context("case3.g4")
def g4(d, claim):
    schema(d, claim, SCHEMA)
    with kit(d) as k:
        keys = dict(
            assets="each asset's depreciation in 2026 and 2027", months="the monthly depreciation charged to 1090 in 2026",
            purchases="the purchases behind the equipment", standard="the standard cost of 2026's output",
            salaried="the salaried manufacturing staff", volume="why the volume comes from output",
            budget="what the budget holds for Manufacturing", plan="the 2027 plan, hours against regular capacity",
            variance="the variance left at standard hours")
        rows = {name: k.run(key) for name, key in keys.items()}
        n = {name: len(r) for name, r in rows.items()}
        assets = rows["assets"]
        ledger = d.one("SELECT ROUND(SUM(gl.Debit), 2) FROM GLEntry gl JOIN JournalEntry je ON je.JournalEntryID = gl.SourceDocumentID "
                       "JOIN Account a ON a.AccountID = gl.AccountID WHERE gl.SourceDocumentType = 'JournalEntry' "
                       "AND je.EntryType = 'Depreciation' AND a.AccountNumber = 1090 AND gl.FiscalYear = ?", d.C)
        total_c = round(sum(r[4] for r in assets), 2)
        claim(total_c == ledger, "the schedule rebuilt from FixedAsset equals the depreciation the ledger charged to 1090 in the last year")
        with k.swapped("PlantAssets", "+ CAST(strftime('%m', fa.InServiceDate) AS INTEGER) AS FirstMonth,",
                       "+ CAST(strftime('%m', fa.InServiceDate) AS INTEGER) - 1 AS FirstMonth,"):
            early = k.run(keys["assets"])
        total_early = round(sum(r[4] for r in early), 2)
        claim(total_early != ledger, "starting a month early gives a total that differs from the ledger")
        cal_months = k.alt(keys["assets"], "WHERE CalendarDate BETWEEN '2026-01-01' AND '2026-12-31'",
                           f"WHERE CalendarDate BETWEEN '{d.N}-01-01' AND '{d.N}-12-31'")
        in_calendar = d.one("SELECT COUNT(DISTINCT strftime('%Y-%m', CalendarDate)) FROM WorkCenterCalendar WHERE CalendarDate >= ?", f"{d.N}-01-01")
        short_dep = round(sum(r[4] for r in cal_months), 2)
        claim(in_calendar < 12, "the calendar covers only part of the plan year")
        plan = rows["plan"]
        emp_all = k.alt(keys["plan"], "WHERE cc.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly' AND e.IsActive = 1) AS Employees,",
                        "WHERE cc.CostCenterName = 'Manufacturing') AS Employees,")
        short_days = k.alt(keys["plan"], "AND CalendarDate BETWEEN '2026-01-01' AND '2026-12-31') AS WorkingDays",
                           f"AND CalendarDate BETWEEN '{d.N}-01-01' AND '{d.N}-12-31') AS WorkingDays")
        claim(all(r[4] > 0 for r in short_days) and all(r[4] == 0 for r in plan), "with the plan year's few calendar days every scenario would need overtime")
        union = sub(k.stmt(keys["plan"]), "UNION ALL", "UNION", count=2)
        claim(k.q(union) == plan, "the three scenarios differ in their ratio, so UNION and UNION ALL give the same rows")
        ratios = k.alt(keys["volume"], "ROUND(b.Units / c.Units, 2) AS BudgetToCompleted", "b.Units / c.Units AS BudgetToCompleted")
        last_ratio = ratios[-1][1]
        std_hours = rows["standard"][0][0]
        claim(rows["volume"][-1][1] > 2.5 and rows["volume"][-1][2] > 2, "the budget plans about three times the units the plant completed and the forecast more than twice the units ordered")
        claim({r[1] for r in rows["budget"]} == {"COGS"}, "the Manufacturing cost center's budget lines are cost of goods sold only")
        claim(plan[0][4] == 0 and plan[-1][4] == 0, "no scenario needs overtime for capacity")
        final = rows["variance"][0]
        claim(all(r[4] > r[5] for r in rows["purchases"]), "each plant asset bought in the window was ordered above its approver's limit")
        titles = [r[0] for r in rows["salaried"]]
    return dict(
        n=n, assets=assets, ledger=ledger, total_early=total_early, early_gap=round(total_early - ledger, 2), in_calendar=in_calendar,
        short_dep=short_dep, plan=plan, emp_all=emp_all, short_days=short_days, volume=rows["volume"], last_ratio=last_ratio,
        budget_hours=std_hours * last_ratio, budget_over=std_hours * last_ratio - plan[0][3], standard=rows["standard"][0],
        salaried=rows["salaried"], budget=rows["budget"], final=final, titles=titles, purchases=rows["purchases"],
        months=rows["months"])


# --- requirement 5: closing the statements ------------------------------------------------------------------------------

@context("case3.g5")
def g5(d, claim):
    schema(d, claim, SCHEMA)
    with kit(d) as k:
        keys = dict(
            total="the accrual for December 14-31, 2026, in total", centers="the accrual at 2026-12-31 by cost center",
            accounts="the accounts each cost center's payroll is debited to", names="the accounts the adjusting entries credit",
            prior="the 2025 work in the registers paid in fiscal 2026", l8="test L8 of Audit.sql rerun", l5="test L5 of Audit.sql rerun",
            l6="test L6 of Audit.sql rerun", adjust="the proposed adjustments and their effect", asc="actual conversion cost per standard hour",
            asv="supplier invoices dated in 2025 and received in 2026")
        rows = {name: k.run(key) for name, key in keys.items()}
        n = {name: len(r) for name, r in rows.items()}
        total = rows["total"][0]

        def accrual_with(old, new):
            with k.swapped("PayrollAccrual", old, new):
                return k.run(keys["total"])[0]
        no_status = accrual_with("WHERE Status = 'Processed' ORDER BY PeriodEndDate DESC", "ORDER BY PeriodEndDate DESC")
        days_row = ("COUNT(DISTINCT c.CalendarDate) FROM WorkCenterCalendar AS c WHERE c.IsWorkingDay = 1 AND c.CalendarDate BETWEEN "
                    "sp.FirstDay AND sp.LastDay")
        period_rows = accrual_with(days_row, days_row.replace("COUNT(DISTINCT c.CalendarDate)", "COUNT(c.CalendarDate)"))
        left_row = "COUNT(DISTINCT c.CalendarDate) FROM WorkCenterCalendar AS c WHERE c.IsWorkingDay = 1 AND c.CalendarDate > sp.LastDay"
        left_rows = accrual_with(left_row, left_row.replace("COUNT(DISTINCT c.CalendarDate)", "COUNT(c.CalendarDate)"))
        first_day, last_day = total[0], total[1]
        cal_days = d.one("SELECT CAST(julianday(?) - julianday(?) AS INTEGER) + 1", last_day, first_day)
        cal_left = d.one("SELECT CAST(julianday(?) - julianday(?) AS INTEGER)", f"{d.C}-12-31", last_day)
        calendar_accrual = round(total[4] / cal_days * cal_left, 2)
        claim(no_status[6] == 0 and no_status[3] == 0, "with the open periods counted among the last eight, no day is left after the last period and the accrual is nothing")
        claim(abs(period_rows[6] * 5 - total[6]) < 1 and abs(left_rows[6] - 5 * total[6]) < 1, "counting calendar rows instead of dates, on one side, scales the accrual by the five work centers")
        claim(calendar_accrual < total[6], "calendar days give a smaller accrual than working days")
        prior = rows["prior"]
        with k.swapped("PriorYearWork", "WHERE pp.PeriodStartDate <= '2025-12-31' AND pp.PayDate > '2025-12-31'",
                       "WHERE pp.PeriodEndDate > '2025-12-31' AND pp.PeriodStartDate <= '2025-12-31'"):
            by_end = k.run(keys["prior"])
        claim(len(prior) == 2 and len(by_end) == 1, "two pay periods cross the year-end by pay date, and one by period end")
        adjust = rows["adjust"][0]
        closes_in = k.alt(keys["adjust"], "AND gl.VoucherNumber NOT IN ( SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%')", "")[0]
        claim(closes_in[0] == 0, "with the closes left in, the year's net income is nothing")
        asc = rows["asc"][0]
        fg_year = k.alt(keys["asc"], "WHERE a.AccountNumber = 1040 AND gl.PostingDate <= '2026-12-31'", "WHERE a.AccountNumber = 1040 AND gl.FiscalYear = 2026")[0][2]
        claim(fg_year < asc[2], "the year's movement of the finished goods account is less than its balance")
        l5 = rows["l5"]
        before_ship = [r for r in l5 if r[0] == "Invoice dated before shipment" and r[1] == str(d.C)]
        another = [r for r in l5 if r[0] == "Revenue posted in another year" and r[1] == str(d.P)]
        claim(len(before_ship) == 1 and len(another) == 1, "the revenue cutoff test has one row of each finding for the last two years")
        l6 = rows["l6"]
        only_new = round(adjust[0] - total[6] + adjust[2], 2)
        accounts = {}
        for cc, num, name, debit in rows["accounts"]:
            accounts.setdefault(cc, []).append(num)
        claim(accounts["Manufacturing"] == [1090], "the Manufacturing payroll is debited to account 1090 alone")
        claim(all(len(v) == 2 and 6060 in v for c, v in accounts.items() if c != "Manufacturing"), "every other cost center's payroll goes to a salary account and 6060")
        l8 = {r[0]: r for r in rows["l8"]}
        claim(abs(l8["PayrollSummary"][2] + l8["PayrollPayment"][2]) < 0.005 and l8["JournalEntry"][1] == 1, "account 2030's payroll postings net to zero and one journal entry line carries the balance")
    return dict(
        work_centers=d.one("SELECT COUNT(DISTINCT WorkCenterID) FROM WorkCenterCalendar"),
        variance_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 5080"),
        n=n, total=total, no_status=no_status, period_rows=period_rows, left_rows=left_rows, cal_days=cal_days, cal_left=cal_left,
        calendar_accrual=calendar_accrual, by_end=by_end[0], prior=prior, adjust=adjust, closes_in=closes_in, asc=asc, fg_year=fg_year,
        before_ship=before_ship[0], another=another[0], l6=l6, only_new=only_new, accounts=accounts, centers=rows["centers"],
        names=rows["names"], l8=rows["l8"], asv=rows["asv"], l5=l5)


# --- requirement 6: the memo ----------------------------------------------------------------------------------------------

@context("case3.g6")
def g6(d, claim):
    text = SOLUTION.read_text(encoding="utf-8")
    block = re.search(r"(?s)/\* Model answer \(Requirement 6\)(.*?)\*/", text).group(1)
    words = len(re.findall(r"\w+", block))
    case = CASE.read_text(encoding="utf-8")
    claim("no more than two pages" in case and "one-page appendix" in case, "the memo is at most two pages and its appendix one")
    exhibits = ["the corroboration matrix", "output against hours", "the bridge of the variance", "the 2027 plan against the status quo",
                "the proposed adjustments"]
    claim(all(e in case.replace("\n", " ") for e in exhibits), "the case lists the five exhibits")
    return dict(model_words=words, exhibits=exhibits, n_exhibits=len(exhibits),
                variance_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 5080"),
                clearing_account=d.one("SELECT AccountNumber FROM Account WHERE AccountNumber = 1090"))
