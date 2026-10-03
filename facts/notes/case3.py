"""The Part III case's instructor notes (planning the plant's hours for the next year): the values each note
states, and the claims its wording makes.

The case is set early in d.N, after the internal audit of Chapter 12. Surge days are the days on which every
manufacturing employee with a time clock entry recorded the same hours (the SurgeDays CTE of Tutorial 12.3's
test H9), and the plant's entries are the time clock entries of the hourly manufacturing employees. Time
records follow the work date and end before the fiscal year does, so output is counted up to the last day with
time records wherever it is compared with hours. The plan year is d.N; the statements to close are d.C's.

One note is not registered, because its comment states a value the data do not give; its context function
renders the corrected text, so register it once the comment is fixed:
- r4 gives the overhead applied at 19.12 per standard hour as 1,317,582; the standard variable and fixed
  overhead of the fiscal 2026 completions is 1,317,562.72 (1,317,563), the released conversion cost less its
  standard labor gives 1,317,563.31 too. Its overhead of the plan, 1,902,775, is 1,902,775.50 (salaried staff
  with the 14.14% burden, factory overhead, and depreciation, the same overhead its conversion costs use), which
  rounds to 1,902,776; the comment truncates.
"""

from __future__ import annotations

import math
import statistics as st
from datetime import date, timedelta
from functools import lru_cache

from notes import note

CASE = "cases/part-3-case.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]   # strftime('%w')

SURGE = ("SurgeDays AS (SELECT tc.WorkDate FROM TimeClockEntry AS tc JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID "
         "JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID WHERE cc.CostCenterName = 'Manufacturing' "
         "GROUP BY tc.WorkDate HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1 AND COUNT(*) > 1)")
PLANT = ("WITH " + SURGE + ", PlantEntries AS (SELECT tc.*, e.BaseHourlyRate, CASE WHEN s.WorkDate IS NULL "
         "THEN 'Ordinary' ELSE 'Surge' END AS DayType FROM TimeClockEntry AS tc JOIN Employee AS e "
         "ON e.EmployeeID = tc.EmployeeID JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID "
         "LEFT JOIN SurgeDays AS s ON s.WorkDate = tc.WorkDate WHERE cc.CostCenterName = 'Manufacturing' "
         "AND e.PayClass = 'Hourly') ")
COMPLETIONS = ("FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc ON pc.ProductionCompletionID = "
               "pcl.ProductionCompletionID JOIN Item i ON i.ItemID = pcl.ItemID")
UNINVOICED = ("FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN SalesOrderLine sol "
              "ON sol.SalesOrderLineID = sl.SalesOrderLineID LEFT JOIN (SELECT DISTINCT ShipmentLineID FROM "
              "SalesInvoiceLine) x ON x.ShipmentLineID = sl.ShipmentLineID WHERE x.ShipmentLineID IS NULL")
OT_PREMIUM = 0.5        # the overtime premium over the base rate (time and a half), as test H5 pays it
STRAIGHT_DAY = 8        # the straight-time hours of a day, the regular hours of a full shift


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def series(items) -> str:
    """'a', 'a and b', 'a, b, and c'."""
    items = [str(x) for x in items]
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def monday(day: str) -> str:
    """The Monday of a date's week, as date(x, '-6 days', 'weekday 1') gives it."""
    dt = date.fromisoformat(day)
    return (dt - timedelta(days=dt.weekday())).isoformat()


def month_index(day: str) -> int:
    return int(day[:4]) * 12 + int(day[5:7]) - 1


def day_month(day: str) -> str:
    """'2026-12-11' -> '11 December'."""
    return f"{int(day[8:10])} {MONTHS[int(day[5:7]) - 1]}"


# --- shared measures ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def last_work(d) -> str:
    """The last day with time records."""
    return d.one("SELECT MAX(WorkDate) FROM TimeClockEntry")


@lru_cache(maxsize=None)
def surge_days(d) -> tuple[str, ...]:
    return tuple(r[0] for r in d.q("WITH " + SURGE + " SELECT WorkDate FROM SurgeDays ORDER BY 1"))


@lru_cache(maxsize=None)
def yearly(d) -> tuple[dict, ...]:
    """The plant's entries by work year and day type, with output up to the last day with time records."""
    rows = {(int(y), t): dict(days=days, entries=n, hours=h, regular=reg, overtime=ot, per_entry=avg, unused=unused,
                              premium=premium) for y, t, days, n, h, reg, ot, avg, unused, premium in d.q(
        PLANT + "SELECT substr(WorkDate, 1, 4), DayType, COUNT(DISTINCT WorkDate), COUNT(*), SUM(RegularHours + OvertimeHours), "
        "SUM(RegularHours), SUM(OvertimeHours), AVG(RegularHours + OvertimeHours), "
        f"SUM(CASE WHEN RegularHours < {STRAIGHT_DAY} THEN {STRAIGHT_DAY} - RegularHours ELSE 0 END), "
        "SUM(OvertimeHours * BaseHourlyRate) FROM PlantEntries GROUP BY 1, 2")}
    std = {int(y): v for y, v in d.q(f"SELECT substr(pc.CompletionDate, 1, 4), SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) "
                                     f"{COMPLETIONS} WHERE pc.CompletionDate <= ? GROUP BY 1", last_work(d))}
    out = []
    for y in d.years:
        s, o = rows[(y, "Surge")], rows[(y, "Ordinary")]
        hours = s["hours"] + o["hours"]
        out.append(dict(year=y, surge=s, ordinary=o, hours=hours, std=std[y], ratio=hours / std[y],
                        surge_premium=s["premium"] * OT_PREMIUM, surge_full=s["premium"] * (1 + OT_PREMIUM),
                        premium=(s["premium"] + o["premium"]) * OT_PREMIUM))
    return tuple(out)


def of_year(d, year: int) -> dict:
    return next(y for y in yearly(d) if y["year"] == year)


@lru_cache(maxsize=None)
def rate(d, year: int) -> float:
    """The hours-weighted base rate of the plant's entries in a work year, to four decimals."""
    return round(d.one(PLANT + "SELECT SUM((RegularHours + OvertimeHours) * BaseHourlyRate) / SUM(RegularHours + OvertimeHours) "
                       "FROM PlantEntries WHERE substr(WorkDate, 1, 4) = ?", str(year)), 4)


@lru_cache(maxsize=None)
def burden(d, year: int) -> float:
    """Employer payroll taxes and benefits over gross pay on the Manufacturing registers of a pay year, to four decimals."""
    return round(d.one("SELECT SUM(pr.EmployerPayrollTax + pr.EmployerBenefits) / SUM(pr.GrossPay) FROM PayrollRegister pr "
                       "JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID JOIN CostCenter c "
                       "ON c.CostCenterID = pr.CostCenterID WHERE c.CostCenterName = 'Manufacturing' AND pp.FiscalYear = ?",
                       year), 4)


@lru_cache(maxsize=None)
def weeks(d) -> tuple[dict, ...]:
    """Monday weeks with hours through the week of the last day with time records: hours, standard hours completed,
    surge days, and the average output of the six weeks that follow (a ROWS frame over these weeks)."""
    hours = dict(d.q(PLANT + "SELECT date(WorkDate, '-6 days', 'weekday 1'), SUM(RegularHours + OvertimeHours) "
                     "FROM PlantEntries GROUP BY 1"))
    output = dict(d.q(f"SELECT date(pc.CompletionDate, '-6 days', 'weekday 1'), SUM(pcl.QuantityCompleted * "
                      f"i.StandardLaborHoursPerUnit) {COMPLETIONS} GROUP BY 1"))
    surge = {}
    for day in surge_days(d):
        surge[monday(day)] = surge.get(monday(day), 0) + 1
    end = monday(last_work(d))
    keys = sorted(w for w in hours if w <= end)
    out = []
    for i, w in enumerate(keys):
        following = [output.get(k, 0.0) for k in keys[i + 1:i + 7]]
        out.append(dict(week=w, hours=hours[w], std=output.get(w, 0.0), surge=surge.get(w, 0),
                        next=st.mean(following) if following else None))
    return tuple(out)


def week_group(rows) -> dict:
    nexts = [r["next"] for r in rows if r["next"] is not None]
    return dict(n=len(rows), hours=st.mean(r["hours"] for r in rows), std=st.mean(r["std"] for r in rows),
                ratio=sum(r["std"] for r in rows) / sum(r["hours"] for r in rows), next=st.mean(nexts))


@lru_cache(maxsize=None)
def ledger(d) -> dict[int, dict]:
    """Accounts 1090 and 5080 by fiscal year, closes excluded."""
    a1090, a5080 = d.account("1090"), d.account("5080")
    out = {}
    for y, v5080, payroll, payroll_cr, je, je_cr, released, change, paydates in d.q(
            f"SELECT FiscalYear, SUM(CASE WHEN AccountID = {a5080} THEN Debit - Credit ELSE 0 END), "
            f"SUM(CASE WHEN AccountID = {a1090} AND SourceDocumentType = 'PayrollSummary' THEN Debit ELSE 0 END), "
            f"SUM(CASE WHEN AccountID = {a1090} AND SourceDocumentType = 'PayrollSummary' THEN Credit ELSE 0 END), "
            f"SUM(CASE WHEN AccountID = {a1090} AND SourceDocumentType = 'JournalEntry' THEN Debit ELSE 0 END), "
            f"SUM(CASE WHEN AccountID = {a1090} AND SourceDocumentType = 'JournalEntry' THEN Credit ELSE 0 END), "
            f"SUM(CASE WHEN AccountID = {a1090} AND SourceDocumentType = 'ProductionCompletion' THEN Credit - Debit ELSE 0 END), "
            f"SUM(CASE WHEN AccountID = {a1090} THEN Debit - Credit ELSE 0 END), "
            f"COUNT(DISTINCT CASE WHEN AccountID = {a1090} AND SourceDocumentType = 'PayrollSummary' THEN PostingDate END) "
            f"FROM GLEntry WHERE AccountID IN ({a1090}, {a5080}) AND {d.no_closes()} GROUP BY 1"):
        out[y] = dict(v5080=v5080, payroll=payroll, payroll_cr=payroll_cr, je=je, je_cr=je_cr, released=released,
                      change=change, paydates=paydates)
    for y, material, conversion in d.q("SELECT substr(CloseDate, 1, 4), SUM(MaterialVarianceAmount), "
                                       "SUM(ConversionVarianceAmount) FROM WorkOrderClose GROUP BY 1"):
        if int(y) in out:
            out[int(y)].update(material=material, conversion=conversion)
    for y in out:
        out[y]["direct"] = d.one(f"SELECT COALESCE(SUM(Debit - Credit), 0) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                                 f"AND SourceDocumentType <> 'WorkOrderClose' AND {d.no_closes()}", a5080, y)
    return out


@lru_cache(maxsize=None)
def calendar_wc(d) -> int:
    return d.one("SELECT MIN(WorkCenterID) FROM WorkCenterCalendar")


def working_days(d, first: str, last: str) -> int:
    return d.one("SELECT COUNT(*) FROM WorkCenterCalendar WHERE WorkCenterID = ? AND IsWorkingDay = 1 "
                 "AND CalendarDate BETWEEN ? AND ?", calendar_wc(d), first, last)


@lru_cache(maxsize=None)
def completions(d) -> dict:
    """The current year's completions: standard hours, and their standard labor and overhead."""
    std, labor, overhead, conversion = d.q(
        f"SELECT SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit), SUM(pcl.ExtendedStandardDirectLaborCost), "
        f"SUM(pcl.ExtendedStandardVariableOverheadCost + pcl.ExtendedStandardFixedOverheadCost), "
        f"SUM(pcl.ExtendedStandardConversionCost) {COMPLETIONS} WHERE substr(pc.CompletionDate, 1, 4) = ?", str(d.C))[0]
    return dict(std=std, labor=labor, overhead=overhead, conversion=conversion)


@lru_cache(maxsize=None)
def depreciation(d) -> dict:
    """The monthly depreciation charged to account 1090, from FixedAsset: OriginalCost / UsefulLifeMonths from the
    month after the in-service date through the month before disposal (and the end of the asset's life)."""
    assets = [dict(id=a, code=c, start=month_index(s) + 1, end=month_index(s) + life, disposal=disp, service=s,
                   monthly=round(cost / life, 2), item=item, cost=cost)
              for a, c, s, life, cost, disp, item in d.q(
                  "SELECT FixedAssetID, AssetCode, InServiceDate, UsefulLifeMonths, OriginalCost, DisposalDate, ItemID "
                  "FROM FixedAsset WHERE DepreciationDebitAccountID = ? ORDER BY AssetCode", d.account("1090"))]
    for a in assets:
        a["last"] = min(a["end"], month_index(a["disposal"]) - 1) if a["disposal"] else a["end"]

    def charge(m):
        return round(sum(a["monthly"] for a in assets if a["start"] <= m <= a["last"]), 2)
    return dict(assets=assets, months={y: [charge(y * 12 + k) for k in range(12)] for y in (d.C, d.N)})


@lru_cache(maxsize=None)
def processed(d) -> dict:
    """The last eight processed pay periods and their cost per working day, by cost center."""
    periods = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate FROM PayrollPeriod WHERE Status = 'Processed' "
                  "ORDER BY PeriodEndDate DESC LIMIT 8")[::-1]
    ids = [p[0] for p in periods]
    marks = ",".join("?" * len(ids))
    gross, tax, ben = d.q(f"SELECT SUM(GrossPay), SUM(EmployerPayrollTax), SUM(EmployerBenefits) FROM PayrollRegister "
                          f"WHERE PayrollPeriodID IN ({marks})", *ids)[0]
    centers = d.q(f"SELECT c.CostCenterName, SUM(pr.GrossPay + pr.EmployerPayrollTax + pr.EmployerBenefits), SUM(pr.GrossPay) "
                  f"FROM PayrollRegister pr JOIN CostCenter c ON c.CostCenterID = pr.CostCenterID "
                  f"WHERE pr.PayrollPeriodID IN ({marks}) GROUP BY 1 ORDER BY 2 DESC", *ids)
    wd = working_days(d, periods[0][1], periods[-1][2])
    left_start = (date.fromisoformat(periods[-1][2]) + timedelta(days=1)).isoformat()
    left = working_days(d, left_start, f"{d.C}-12-31")
    accrue = lambda x: round(x / wd * left, 2)
    return dict(ids=ids, start=periods[0][1], end=periods[-1][2], cost=gross + tax + ben, wd=wd, daily=(gross + tax + ben) / wd,
                left_start=left_start, left=left, accrual=accrue(gross + tax + ben), gross=accrue(gross), tax=accrue(tax),
                ben=accrue(ben), centers=[dict(name=n, amount=accrue(a), gross=accrue(g)) for n, a, g in centers])


def period_cost(d, pid: int, center: str | None = None) -> float:
    where, args = "pr.PayrollPeriodID = ?", [pid]
    if center:
        where, args = where + " AND c.CostCenterName = ?", args + [center]
    return d.one(f"SELECT SUM(pr.GrossPay + pr.EmployerPayrollTax + pr.EmployerBenefits) FROM PayrollRegister pr "
                 f"JOIN CostCenter c ON c.CostCenterID = pr.CostCenterID WHERE {where}", *args)


@lru_cache(maxsize=None)
def prior_year_end(d) -> dict:
    """The work of the prior year's last days, paid in the current fiscal year, by working day."""
    end = f"{d.P}-12-31"
    full = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate, PayDate FROM PayrollPeriod WHERE PeriodEndDate <= ? "
               "AND FiscalYear = ? ORDER BY 1", end, d.C)
    cross = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate, PayDate FROM PayrollPeriod WHERE PeriodStartDate <= ? "
                "AND PeriodEndDate > ? ORDER BY 1", end, end)
    f, c = full[0], cross[0]
    inside, days = working_days(d, c[1], end), working_days(d, c[1], c[2])
    f_cost, c_cost = period_cost(d, f[0]), period_cost(d, c[0])
    share = round(c_cost * inside / days, 2)
    mfg = period_cost(d, f[0], "Manufacturing") + period_cost(d, c[0], "Manufacturing") * inside / days
    return dict(n_full=len(full), n_cross=len(cross), full=dict(id=f[0], start=f[1], end=f[2], pay=f[3], cost=f_cost),
                cross=dict(id=c[0], start=c[1], end=c[2], cost=c_cost, inside=inside, days=days, share=share),
                total=round(f_cost + share, 2), mfg=round(mfg, 2))


def hour_based(d, year: int) -> float:
    """Exercise 12.1's allocation: the hourly labor of `year`'s work paid in the next fiscal year, by work date, with its
    share of the hourly employees' employer costs, plus the salaried pay and its employer costs by working day."""
    end = f"{year}-12-31"
    total = 0.0
    for pid, start, stop in d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate FROM PayrollPeriod "
                                "WHERE PeriodStartDate <= ? AND FiscalYear = ?", end, year + 1):
        labor, all_labor = d.q("SELECT SUM(CASE WHEN WorkDate <= ? THEN ExtendedLaborCost ELSE 0 END), SUM(ExtendedLaborCost) "
                               "FROM LaborTimeEntry WHERE PayrollPeriodID = ?", end, pid)[0]
        pay = dict((cls, (g, e)) for cls, g, e in d.q(
            "SELECT e.PayClass, SUM(pr.GrossPay), SUM(pr.EmployerPayrollTax + pr.EmployerBenefits) FROM PayrollRegister pr "
            "JOIN Employee e ON e.EmployeeID = pr.EmployeeID WHERE pr.PayrollPeriodID = ? GROUP BY 1", pid))
        share = working_days(d, start, min(stop, end)) / working_days(d, start, stop)
        hourly_employer = pay["Hourly"][1] * labor / all_labor
        salaried = sum(pay.get("Salary", (0.0, 0.0)))
        total += labor + hourly_employer + salaried * share
    return total


# --- Requirement 1 -------------------------------------------------------------------------------

@note("case3.r1", CASE)
def r1(d, claim):
    punches, employees, first, last = d.q("SELECT COUNT(*), COUNT(DISTINCT EmployeeID), MIN(WorkDate), MAX(WorkDate) "
                                          "FROM TimeClockPunch")[0]
    sources = [r[0] for r in d.q("SELECT DISTINCT PunchSource FROM TimeClockPunch")]
    claim(len(sources) == 1, "every punch has the same PunchSource")
    types = dict(d.q("SELECT PunchType, COUNT(*) FROM TimeClockPunch GROUP BY 1"))
    claim(types.get("Meal Start") == types.get("Meal End"), "there are as many Meal Start as Meal End punches")
    entry_types = {}
    for entry, kind in d.q("SELECT TimeClockEntryID, PunchType FROM TimeClockPunch GROUP BY 1, 2"):
        entry_types.setdefault(entry, set()).add(kind)
    no_out = [e for e, kinds in entry_types.items() if "Clock In" in kinds and "Clock Out" not in kinds]
    owners = d.q("SELECT EmployeeID, WorkDate FROM TimeClockEntry WHERE TimeClockEntryID IN (%s)" % ",".join(map(str, no_out)))
    claim(len(no_out) == types["Clock In"] - types["Clock Out"], "the missing clock-outs are the entries without one")
    claim(len({o[0] for o in owners}) == 1 and all(o[1][5:] == "01-01" for o in owners),
          "the missing clock-outs all belong to one employee's January 1 entries")
    claim(d.one("SELECT COUNT(*) FROM TimeClockPunch p LEFT JOIN TimeClockEntry tc ON tc.TimeClockEntryID = p.TimeClockEntryID "
                "WHERE tc.TimeClockEntryID IS NULL") == 0, "no punch lacks its clock entry")
    claim(d.one("SELECT COUNT(*) FROM (SELECT TimeClockEntryID, PunchType FROM TimeClockPunch GROUP BY 1, 2 "
                "HAVING COUNT(*) > 1)") == 0, "no clock entry has two punches of one type")
    rosters = d.one("SELECT COUNT(*) FROM EmployeeShiftRoster")
    statuses = d.q("SELECT RosterStatus, COUNT(*) FROM EmployeeShiftRoster GROUP BY 1 ORDER BY 2 DESC")
    claim(d.one("SELECT COUNT(*) FROM (SELECT EmployeeID, RosterDate FROM EmployeeShiftRoster GROUP BY 1, 2 "
                "HAVING COUNT(*) > 1)") == 0, "no employee is rostered twice on one date")
    creators = d.q("SELECT DISTINCT r.CreatedByEmployeeID, e.JobTitle FROM EmployeeShiftRoster r JOIN Employee e "
                   "ON e.EmployeeID = r.CreatedByEmployeeID ORDER BY 1")
    claim(all(t.endswith("Manager") for _, t in creators), "every roster was created by a department manager")
    claim(any(t == "Production Manager" for _, t in creators), "the Production Manager is among the roster creators")
    exc = d.q("SELECT ExceptionType, COUNT(*), SUM(Status = 'Open'), COUNT(ReviewedByEmployeeID), COUNT(ReviewedDate) "
              "FROM AttendanceException GROUP BY 1 ORDER BY 1")
    n_exc = sum(r[1] for r in exc)
    claim(len({r[1] for r in exc}) == 1, "every exception type has the same number of exceptions")
    claim(all(r[2] == r[1] for r in exc), "every exception is Open")
    claim(all(r[3] == 0 and r[4] == 0 for r in exc), "no exception was reviewed (ReviewedByEmployeeID is NULL on every row)")
    cal_rows, centers, cal_first, cal_last = d.q("SELECT COUNT(*), COUNT(DISTINCT WorkCenterID), MIN(CalendarDate), "
                                                 "MAX(CalendarDate) FROM WorkCenterCalendar")[0]
    year = str(d.C)
    working = d.one("SELECT COUNT(DISTINCT CalendarDate) FROM WorkCenterCalendar WHERE IsWorkingDay = 1 "
                    "AND substr(CalendarDate, 1, 4) = ?", year)
    reasons = {r: n for r, n in d.q("SELECT ExceptionReason, COUNT(DISTINCT CalendarDate) FROM WorkCenterCalendar "
                                    "WHERE substr(CalendarDate, 1, 4) = ? GROUP BY 1", year)}
    avail = d.one("SELECT SUM(AvailableHours) FROM WorkCenterCalendar WHERE substr(CalendarDate, 1, 4) = ?", year)
    # Links.
    shifted = d.q("SELECT p.TimeClockEntryID, COUNT(*) FROM TimeClockPunch p JOIN TimeClockEntry tc "
                  "ON tc.TimeClockEntryID = p.TimeClockEntryID WHERE p.WorkDate <> tc.WorkDate GROUP BY 1 ORDER BY 1")
    shifted_entries = [r[0] for r in shifted]
    behind = sorted(r[0] for r in d.q("SELECT TimeClockEntryID FROM AttendanceException WHERE ExceptionType IN "
                                      "('Duplicate Clock Day', 'Labor After Close')"))
    claim(shifted_entries == behind, "the punches dated differently from their clock entry are those of the clock entries "
                                     "behind the Duplicate Clock Day and Labor After Close exceptions")
    roster_shifted = sorted(r[0] for r in d.q("SELECT tc.TimeClockEntryID FROM TimeClockEntry tc JOIN EmployeeShiftRoster r "
                                              "ON r.EmployeeShiftRosterID = tc.EmployeeShiftRosterID WHERE r.RosterDate <> tc.WorkDate"))
    claim(roster_shifted == shifted_entries, "those clock entries' roster dates also differ, and no other's does")
    detached = d.q("SELECT p.TimeClockPunchID, p.EmployeeID, p.WorkDate, p.PunchType FROM TimeClockPunch p JOIN TimeClockEntry tc "
                   "ON tc.TimeClockEntryID = p.TimeClockEntryID WHERE p.EmployeeShiftRosterID IS NULL "
                   "OR p.EmployeeShiftRosterID <> tc.EmployeeShiftRosterID ORDER BY 1")
    claim(all(r[3] == "Clock In" for r in detached), "the detached punches are clock-in punches")
    claim(len({r[1] for r in detached}) == 1, "the detached punches belong to one employee")
    claim(sorted(r[2] for r in detached) == [f"{y}-01-01" for y in d.years], "one detached punch on each January 1")
    no_roster, missing, other_employee = d.q(
        "SELECT SUM(tc.EmployeeShiftRosterID IS NULL), SUM(tc.EmployeeShiftRosterID IS NOT NULL AND r.EmployeeShiftRosterID IS NULL), "
        "SUM(r.EmployeeID <> tc.EmployeeID) FROM TimeClockEntry tc LEFT JOIN EmployeeShiftRoster r "
        "ON r.EmployeeShiftRosterID = tc.EmployeeShiftRosterID")[0]
    claim(no_roster == 0 and missing == 0 and other_employee == 0, "every clock entry has a roster of the same employee")
    wrong = d.q("SELECT ae.AttendanceExceptionID, ae.EmployeeID, tc.EmployeeID, tc.TimeClockEntryID FROM AttendanceException ae "
                "JOIN TimeClockEntry tc ON tc.TimeClockEntryID = ae.TimeClockEntryID WHERE ae.EmployeeID <> tc.EmployeeID ORDER BY 1")
    claim(len({r[1] for r in wrong}) == 1 and len({r[2] for r in wrong}) == 1,
          "the misattributed exceptions name one employee on another single employee's clock entries")
    claim(d.one("SELECT COUNT(*) FROM AttendanceException ae LEFT JOIN TimeClockEntry tc ON tc.TimeClockEntryID = "
                "ae.TimeClockEntryID WHERE tc.TimeClockEntryID IS NULL") == 0, "every exception has its clock entry")
    for kind, keys in (("punch_without_roster", [r[0] for r in detached]), ("missing_clock_out", sorted(no_out))):
        logged = d.anomalies(kind)
        if logged is not None:
            claim(sorted(keys) == logged, f"the {kind} rows are the generator's planted anomalies")
    surge = [(y["year"], y["surge"]["days"], y["surge"]["entries"]) for y in yearly(d)]
    return dict(punches=punches, punch_employees=employees, punch_first=first, punch_last=last, source=sources[0],
                types=types, missing=word(len(no_out)), missing_employee=owners[0][0],
                rosters=rosters, statuses=statuses, creators=creators,
                exceptions=n_exc, per_type=word(exc[0][1]), exc_types=[r[0] for r in exc],
                cal_rows=cal_rows, centers=word(centers), cal_first=cal_first, cal_last=cal_last, working=working,
                maintenance=reasons.get("Maintenance", 0), reduced=reasons.get("Reduced Capacity", 0), avail=avail,
                shifted_punches=sum(r[1] for r in shifted), shifted_word=word(len(shifted)), shifted_entries=shifted_entries,
                detached=[r[0] for r in detached], detached_employee=detached[0][1],
                wrong_ids=[r[0] for r in wrong], wrong_named=wrong[0][1], wrong_owner=wrong[0][2],
                wrong_entries=sorted({r[3] for r in wrong}),
                surge_days=[n for _, n, _ in surge], surge_entries=[e for _, _, e in surge],
                surge_total=sum(e for _, _, e in surge))


# --- Requirement 2 -------------------------------------------------------------------------------

@note("case3.r2", CASE)
def r2(d, claim):
    days = {t: dict(days=n, employees=emp, all_present=allp, clock_ins=ci, largest=lg, largest_max=lmax, largest_min=lmin)
            for t, n, emp, allp, ci, lg, lmin, lmax in d.q(
                PLANT + ", Daily AS (SELECT WorkDate, DayType, COUNT(*) AS n, COUNT(DISTINCT ClockInTime) AS ci FROM PlantEntries "
                "GROUP BY 1, 2), Groups AS (SELECT WorkDate, MAX(k) AS L FROM (SELECT WorkDate, COUNT(*) OVER (PARTITION BY "
                "WorkDate, ClockInTime) AS k FROM PlantEntries) GROUP BY 1) "
                "SELECT DayType, COUNT(*), AVG(n), SUM(n = (SELECT COUNT(DISTINCT e.EmployeeID) FROM Employee e JOIN CostCenter c "
                "ON c.CostCenterID = e.CostCenterID WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly')), "
                "AVG(ci), AVG(L), MIN(L), MAX(L) FROM Daily JOIN Groups USING (WorkDate) GROUP BY 1")}
    s, o = days["Surge"], days["Ordinary"]
    plant = d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter c ON c.CostCenterID = e.CostCenterID "
                  "WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly'")
    claim(s["all_present"] == s["days"] and s["employees"] == plant, "every hourly manufacturing employee clocked in on every surge day")
    claim(s["largest_max"] - s["largest_min"] == 1, "the largest group on a surge day is one of two adjacent sizes")
    claim(abs(s["largest_min"] / plant - 0.5) <= 0.05, "one clock-in time covers half the plant on a surge day")
    meals = dict((t, (n, m)) for t, n, m in d.q(
        PLANT + ", Meals AS (SELECT TimeClockEntryID FROM TimeClockPunch WHERE PunchType = 'Meal Start' GROUP BY 1) "
        "SELECT DayType, COUNT(*), SUM(m.TimeClockEntryID IS NOT NULL) FROM PlantEntries pe LEFT JOIN Meals m "
        "USING (TimeClockEntryID) GROUP BY 1"))
    claim(meals["Surge"][1] == meals["Surge"][0], "every surge entry has meal punches")
    sources = [r[0] for r in d.q("SELECT DISTINCT PunchSource FROM TimeClockPunch")]
    claim(len(sources) == 1, "every punch has the same PunchSource")
    differ = {r[0] for r in d.q("SELECT p.TimeClockEntryID FROM TimeClockPunch p JOIN TimeClockEntry tc ON tc.TimeClockEntryID = "
                                "p.TimeClockEntryID WHERE p.PunchType IN ('Clock In', 'Clock Out') AND p.PunchTimestamp IS NOT "
                                "CASE p.PunchType WHEN 'Clock In' THEN tc.ClockInTime ELSE tc.ClockOutTime END")}
    excepted = {r[0] for r in d.q("SELECT TimeClockEntryID FROM AttendanceException")}
    claim(differ <= excepted, "clock punches equal their clock entry's times except on the entries the exceptions cite")
    rosters = d.q(PLANT + "SELECT r.ScheduledHours, r.ScheduledStartTime, r.ScheduledEndTime, r.CreatedByEmployeeID, "
                  "julianday(r.RosterDate) - julianday(r.CreatedDate), COUNT(*) FROM PlantEntries pe JOIN EmployeeShiftRoster r "
                  "ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID WHERE pe.DayType = 'Surge' GROUP BY 1, 2, 3, 4, 5 ORDER BY 2")
    shifts = sorted({(r[1], r[2]) for r in rosters})
    claim(len({r[0] for r in rosters}) == 1, "every surge entry is rostered for the same hours")
    claim(len(shifts) == 2, "the surge entries are rostered on two shifts")
    claim(len({r[3] for r in rosters}) == 1 and len({r[4] for r in rosters}) == 1,
          "every surge roster was created by one employee the same number of days ahead")
    creator = rosters[0][3]
    title = d.one("SELECT JobTitle FROM Employee WHERE EmployeeID = ?", creator)
    claim(title == "Production Manager", "the surge rosters were created by the Production Manager")
    claim([r[0] for r in d.q("SELECT DISTINCT r.CreatedByEmployeeID FROM EmployeeShiftRoster r JOIN Employee e ON e.EmployeeID = "
                             "r.EmployeeID JOIN CostCenter c ON c.CostCenterID = e.CostCenterID WHERE c.CostCenterName = 'Manufacturing'")]
          == [creator], "the Production Manager creates every manufacturing roster")
    clocks = d.q(PLANT + "SELECT substr(pe.ClockInTime, 12, 5), substr(pe.ClockOutTime, 12, 5), pe.RegularHours + pe.OvertimeHours, "
                 "ROUND((julianday(r.RosterDate || ' ' || r.ScheduledStartTime) - julianday(pe.ClockInTime)) * 1440), "
                 "ROUND((julianday(pe.ClockOutTime) - julianday(r.RosterDate || ' ' || r.ScheduledEndTime)) * 1440) "
                 "FROM PlantEntries pe JOIN EmployeeShiftRoster r ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID "
                 "WHERE pe.DayType = 'Surge' GROUP BY 1, 2, 3, 4, 5 ORDER BY 1")
    claim(len(clocks) == 2, "the surge entries show two clock patterns, one for each rostered shift, each with the same hours "
                            "and minutes outside the roster")
    claim(len({c[2] for c in clocks}) == 1 and len({c[3] for c in clocks}) == 1 and len({c[4] for c in clocks}) == 1,
          "every surge entry clocks the same hours, as early and as late against its roster")
    late = int(clocks[0][4])
    claim(late % 60 == 0, "the late departure is a whole number of hours")
    equal = dict((t, (n, e)) for t, n, e in d.q(
        PLANT + "SELECT pe.DayType, COUNT(*), SUM(ABS(r.ScheduledHours - (pe.RegularHours + pe.OvertimeHours)) < 0.005) "
        "FROM PlantEntries pe JOIN EmployeeShiftRoster r ON r.EmployeeShiftRosterID = pe.EmployeeShiftRosterID GROUP BY 1"))
    claim(equal["Surge"][1] == 0, "on surge days the rostered hours never equal the clocked hours")
    off = d.q("SELECT ae.MinutesVariance, substr(tc.ClockInTime, 12, 5), substr(r.ScheduledStartTime, 1, 5), "
              "ROUND((julianday(tc.ClockInTime) - julianday(r.RosterDate || ' ' || r.ScheduledStartTime)) * 1440) "
              "FROM AttendanceException ae JOIN TimeClockEntry tc ON tc.TimeClockEntryID = ae.TimeClockEntryID "
              "JOIN EmployeeShiftRoster r ON r.EmployeeShiftRosterID = tc.EmployeeShiftRosterID "
              "WHERE ae.ExceptionType = 'Off Shift Clocking'")
    claim(len(set(off)) == 1 and off[0][0] == off[0][3], "the Off Shift Clocking exceptions are all clock-ins the same minutes "
                                                         "after the scheduled start, as their MinutesVariance records")
    threshold = int(off[0][3])
    flagged = d.one(PLANT + "SELECT COUNT(ae.AttendanceExceptionID) FROM PlantEntries pe LEFT JOIN AttendanceException ae "
                    "ON ae.TimeClockEntryID = pe.TimeClockEntryID WHERE pe.DayType = 'Surge'")
    claim(flagged == 0, "no surge entry was flagged")
    approved = d.one(PLANT + "SELECT COUNT(*) FROM PlantEntries pe JOIN OvertimeApproval oa ON oa.OvertimeApprovalID = "
                     "pe.OvertimeApprovalID WHERE pe.DayType = 'Surge' AND oa.Status = 'Approved'")
    claim(approved == meals["Surge"][0], "every surge entry's overtime is approved")
    beyond = d.one(PLANT + "SELECT COUNT(*) FROM PlantEntries pe JOIN EmployeeShiftRoster r ON r.EmployeeShiftRosterID = "
                   "pe.EmployeeShiftRosterID WHERE pe.DayType = 'Ordinary' AND (julianday(pe.ClockOutTime) - "
                   "julianday(r.RosterDate || ' ' || r.ScheduledEndTime)) * 1440 > ?", threshold)
    n_exc, open_exc, reviewed, first = d.q("SELECT COUNT(*), SUM(Status = 'Open'), COUNT(ReviewedByEmployeeID), MIN(WorkDate) "
                                           "FROM AttendanceException")[0]
    claim(open_exc == n_exc and reviewed == 0, "all exceptions are Open and none was reviewed")
    pwac = [r[0] for r in d.q("SELECT tc.ClockStatus FROM AttendanceException ae JOIN TimeClockEntry tc ON tc.TimeClockEntryID = "
                              "ae.TimeClockEntryID WHERE ae.ExceptionType = 'Paid Without Approved Clock'")]
    claim(set(pwac) == {"Pending"}, "the Paid Without Approved Clock exceptions are on Pending clock entries")
    wrong = d.one("SELECT COUNT(*) FROM AttendanceException ae JOIN TimeClockEntry tc ON tc.TimeClockEntryID = "
                  "ae.TimeClockEntryID WHERE ae.EmployeeID <> tc.EmployeeID")
    calendar = {(r, w): n for r, w, n in d.q("WITH " + SURGE + " SELECT c.ExceptionReason, c.IsWorkingDay, COUNT(DISTINCT "
                                             "c.CalendarDate) FROM WorkCenterCalendar c JOIN SurgeDays s ON s.WorkDate = "
                                             "c.CalendarDate GROUP BY 1, 2")}
    claim(all(w == 1 for _, w in calendar), "every surge day is a working day")
    maintenance, reduced = calendar.get(("Maintenance", 1), 0), calendar.get(("Reduced Capacity", 1), 0)
    claim(maintenance > 0 and reduced > 0, "some surge days had maintenance and some reduced capacity")
    claim(d.one("SELECT COUNT(*) FROM (SELECT BucketWeekStartDate, WorkCenterID FROM RoughCutCapacityPlan GROUP BY 1, 2 "
                "HAVING COUNT(DISTINCT AvailableHours) > 1)") == 0,
          "a work center's available hours are the same on every row of a week")
    through = monday(last_work(d))
    load = {(int(y), bool(sw)): v for y, sw, v in d.q(
        "WITH " + SURGE + ", Weeks AS (SELECT date(WorkDate, '-6 days', 'weekday 1') AS W FROM SurgeDays GROUP BY 1), "
        "Available AS (SELECT W, SUM(A) AS A FROM (SELECT BucketWeekStartDate AS W, WorkCenterID, MAX(AvailableHours) AS A "
        "FROM RoughCutCapacityPlan GROUP BY 1, 2) GROUP BY 1), Load AS (SELECT BucketWeekStartDate AS W, "
        "SUM(PlannedLoadHours) AS L FROM RoughCutCapacityPlan GROUP BY 1) "
        "SELECT substr(Load.W, 1, 4), Weeks.W IS NOT NULL, SUM(L) / SUM(A) FROM Load JOIN Available USING (W) "
        "LEFT JOIN Weeks USING (W) WHERE Load.W <= ? GROUP BY 1, 2", through)}
    claim(all(load[(y, True)] < load[(y, False)] for y in d.years), "each year, surge weeks had a lower planned load than other weeks")
    claim(all(v < 1 for v in load.values()), "no group of weeks was planned above its available hours")
    reasons = d.q(PLANT + "SELECT oa.ReasonCode, COUNT(*), COUNT(DISTINCT oa.ApprovedByEmployeeID), MIN(oa.ApprovedByEmployeeID) "
                  "FROM PlantEntries pe JOIN OvertimeApproval oa ON oa.OvertimeApprovalID = pe.OvertimeApprovalID "
                  "WHERE pe.DayType = 'Surge' GROUP BY 1")
    claim(len({r[1] for r in reasons}) == 1, "each reason code is used equally often on surge days")
    claim({r[3] for r in reasons} == {creator} and all(r[2] == 1 for r in reasons),
          "the surge overtime was approved by the manager who created the rosters")
    cite = {t: dict(approvals=n, cited=c, ended=e) for t, n, c, e in d.q(
        PLANT + "SELECT pe.DayType, COUNT(*), COUNT(oa.WorkOrderOperationID), SUM(op.ActualEndDate < oa.WorkDate) "
        "FROM PlantEntries pe JOIN OvertimeApproval oa ON oa.OvertimeApprovalID = pe.OvertimeApprovalID "
        "LEFT JOIN WorkOrderOperation op ON op.WorkOrderOperationID = oa.WorkOrderOperationID GROUP BY 1")}
    claim(cite["Surge"]["ended"] == cite["Surge"]["cited"], "every operation a surge-day approval cites had ended before the work date")
    weekdays = dict((int(w), n) for w, n in d.q("WITH " + SURGE + " SELECT strftime('%w', WorkDate), COUNT(*) FROM SurgeDays GROUP BY 1"))
    claim(set(weekdays) <= {1, 2, 3, 4, 5}, "no surge day falls on a weekend")
    counts = [weekdays.get(k, 0) for k in range(1, 6)]
    claim(all(a <= b for a, b in zip(counts, counts[1:])) and counts[3] + counts[4] > sum(counts) / 2,
          "surge days fall mostly late in the week, more on each later weekday")
    claim(d.one("SELECT COUNT(*) FROM EmployeeAbsence a JOIN Employee e ON e.EmployeeID = a.EmployeeID JOIN CostCenter c "
                "ON c.CostCenterID = e.CostCenterID WHERE c.CostCenterName = 'Manufacturing'") == 0,
          "no absence is recorded in Manufacturing in any year")
    current = [w for w in weeks(d) if w["week"][:4] == str(d.C)]
    claim(st.mean(w["std"] for w in current if w["surge"]) > st.mean(w["std"] for w in current if not w["surge"]),
          "weeks with surge days completed more output (Requirement 3)")
    return dict(s=s, o=o, plant=plant, meals=meals, source=sources[0],
                hours=word(int(rosters[0][0])),
                shifts=[f"{a[:5]}-{b[:5]}" for a, b in shifts], lead=word(int(rosters[0][4])), creator_title=title,
                clocks=[f"{c[0]}-{c[1]}" for c in clocks], early=int(clocks[0][3]), late=late, clocked=clocks[0][2],
                rostered=rosters[0][0], equal=equal, n_off=word(len(off)), threshold=threshold,
                off_in=off[0][1], off_start=off[0][2], late_hours=word(late // 60), beyond=beyond,
                exceptions=n_exc, years=word(d.N - int(first[:4])), n_pwac=word(len(pwac)), wrong=word(wrong),
                maintenance=maintenance, reduced=reduced, through=through,
                load=[(load[(y, True)], load[(y, False)]) for y in d.years],
                n_reasons=word(len(reasons)), per_reason=reasons[0][1], cite=cite,
                weekdays=[(WEEKDAYS[k], weekdays.get(k, 0)) for k in range(1, 6)])


# --- Requirement 3 -------------------------------------------------------------------------------

@note("case3.r3", CASE)
def r3(d, claim):
    ys = yearly(d)
    first, cur = ys[0], ys[-1]
    claim(max(y["std"] for y in ys) / min(y["std"] for y in ys) < 1.1, "output was flat (within a tenth across the years)")
    growth = cur["surge"]["overtime"] / first["surge"]["overtime"]
    claim(3.5 <= growth < 4.5, "surge overtime quadrupled")
    current = [w for w in weeks(d) if w["week"][:4] == str(d.C)]
    none = week_group([w for w in current if not w["surge"]])
    some = week_group([w for w in current if w["surge"]])
    detail = [dict(days=k, **week_group([w for w in current if w["surge"] == k]))
              for k in sorted({w["surge"] for w in current if w["surge"]})]
    since = monday((date.fromisoformat(monday(surge_days(d)[0])) + timedelta(days=7)).isoformat())
    later = week_group([w for w in weeks(d) if w["week"] >= since and not w["surge"]])
    claim(some["std"] > none["std"], "surge weeks complete more")
    claim(some["ratio"] < none["ratio"], "surge weeks complete less in proportion to the hours")
    claim(some["next"] < none["next"], "the weeks after surge weeks complete less")
    lead = d.one("SELECT AVG(julianday(CompletedDate) - julianday(ReleasedDate)) FROM WorkOrder WHERE substr(ClosedDate, 1, 4) = ?",
                 str(d.C))
    claim(d.one("SELECT COUNT(*) FROM ProductionCompletion WHERE strftime('%w', CompletionDate) IN ('0', '6') "
                "AND substr(CompletionDate, 1, 4) = ?", str(d.C)) > 0, "completions post on weekends")
    claim(cur["ordinary"]["unused"] > 2 * cur["surge"]["overtime"],
          f"the {d.C} surge overtime would fit more than twice over into the unused straight time")
    b = burden(d, d.C)
    led = ledger(d)
    lf, lc = led[d.F], led[d.C]
    claim(lf["payroll_cr"] == 0 and lc["payroll_cr"] == 0 and lf["je_cr"] == 0 and lc["je_cr"] == 0,
          "payroll and journal entries only debit 1090")
    bridge = dict(delta=lc["v5080"] - lf["v5080"], payroll=lc["payroll"] - lf["payroll"], je=lc["je"] - lf["je"],
                  released=lf["released"] - lc["released"], change=-(lc["change"] - lf["change"]),
                  material=lc["material"] - lf["material"], direct=lc["direct"] - lf["direct"])
    parts = sum(v for k, v in bridge.items() if k != "delta")
    claim(abs(parts - bridge["delta"]) < 0.005, "the bridge adds up to the change in 5080")
    claim(bridge["delta"] > 0, "5080 rose")
    claim(lc["direct"] == 0, f"nothing was posted directly to 5080 in {d.C}")
    direct = d.q(f"SELECT SourceDocumentType, VoucherNumber, PostingDate, SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? "
                 f"AND FiscalYear = ? AND SourceDocumentType <> 'WorkOrderClose' AND {d.no_closes()} GROUP BY 1, 2, 3 ORDER BY 1 DESC",
                 d.account("5080"), d.F)
    claim([r[0] for r in direct] == ["PayrollSummary", "JournalEntry"],
          f"the direct postings of {d.F} are one payroll and one journal entry")
    pay = direct[0]
    extra = lc["paydates"] - lf["paydates"]
    claim(extra > 0, f"1090 received more payrolls in {d.C} than in {d.F}")
    calendar = lf["payroll"] / lf["paydates"] * extra
    r4 = rate(d, d.C)
    hours_beyond = cur["hours"] - first["ratio"] * cur["std"]
    beyond_cost = hours_beyond * r4 * (1 + b)
    premium_growth = (cur["surge_premium"] - first["surge_premium"]) * (1 + b)
    together = calendar + beyond_cost + premium_growth
    claim(together > bridge["payroll"], "the three measures exceed the payroll line")
    return dict(cutoff=last_work(d), ys=ys, other=none, surge=some, detail=detail, since=MONTHS[int(since[5:7]) - 1] + " " + since[:4],
                later=later, lead=lead, burden=b,
                lf=lf, lc=lc, bridge=bridge, released_word="less" if bridge["released"] > 0 else "more",
                pay_month=MONTHS[int(pay[2][5:7]) - 1], pay_amount=pay[3], je=direct[1][1], je_amount=direct[1][3],
                extra=word(extra), calendar=calendar, ratio_f=first["ratio"], hours_beyond=hours_beyond, rate=r4,
                beyond_cost=beyond_cost, premium_growth=premium_growth, together=together,
                excess=together - bridge["payroll"], last_day=day_month(last_work(d)))


# --- Requirement 4 -------------------------------------------------------------------------------

@note("case3.r4", CASE)
def r4(d, claim):
    comp = completions(d)
    std = comp["std"]
    released = ledger(d)[d.C]["released"]
    claim(abs(released - comp["conversion"]) < 1, "the completions' standard conversion cost is what completions released to 1090")
    budget = d.one("SELECT SUM(b.Quantity) FROM BudgetLine b JOIN Item i ON i.ItemID = b.ItemID WHERE b.FiscalYear = ? "
                   "AND b.BudgetCategory = 'Revenue' AND i.SupplyMode = 'Manufactured'", d.C)
    made = d.one("SELECT SUM(pcl.QuantityCompleted) FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc "
                 "ON pc.ProductionCompletionID = pcl.ProductionCompletionID WHERE substr(pc.CompletionDate, 1, 4) = ?", str(d.C))
    products = ("Furniture", "Lighting", "Textiles", "Accessories")
    marks = ",".join("?" * len(products))
    ratios = []
    for y in d.years:
        forecast = d.one(f"SELECT SUM(f.ForecastQuantity) FROM DemandForecast f JOIN Item i ON i.ItemID = f.ItemID WHERE "
                         f"f.IsCurrent = 1 AND i.ItemGroup IN ({marks}) AND substr(f.ForecastWeekStartDate, 1, 4) = ?", *products, str(y))
        ordered = d.one(f"SELECT SUM(l.Quantity) FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
                        f"JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup IN ({marks}) AND substr(o.OrderDate, 1, 4) = ?",
                        *products, str(y))
        ratios.append(forecast / ordered)
    claim(d.one("SELECT COUNT(*) FROM BudgetLine b JOIN CostCenter c ON c.CostCenterID = b.CostCenterID "
                "WHERE c.CostCenterName = 'Manufacturing' AND b.BudgetCategory <> 'COGS'") == 0
          and d.one("SELECT COUNT(*) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
                    "WHERE a.AccountNumber IN ('1090', '5080')") == 0
          and d.one("SELECT COUNT(*) FROM BudgetLine WHERE BudgetCategory = 'COGS'") > 0,
          "no year has a manufacturing labor or overhead budget, only cost of goods sold")
    r, b = rate(d, d.C), burden(d, d.C)
    salaried = d.q("SELECT e.JobTitle, SUM(pr.GrossPay) FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = "
                   "pr.PayrollPeriodID JOIN Employee e ON e.EmployeeID = pr.EmployeeID JOIN CostCenter c ON c.CostCenterID = "
                   "pr.CostCenterID WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Salary' AND pp.FiscalYear = ? "
                   "GROUP BY 1 ORDER BY 1", d.C)
    prefix = salaried[0][0].split()[0] + " "
    claim(all(t.startswith(prefix) for t, _ in salaried), "the salaried manufacturing titles share their first word")
    titles = ", ".join([salaried[0][0]] + [t[len(prefix):] for t, _ in salaried[1:]])
    salary = sum(g for _, g in salaried)
    foh = d.one("SELECT SUM(g.Debit) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
                "WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryType = 'Factory Overhead' AND g.AccountID = ? "
                "AND g.FiscalYear = ?", d.account("1090"), d.C)
    dep = depreciation(d)
    months_c, months_n = dep["months"][d.C], dep["months"][d.N]
    changes = []
    for k in range(1, 12):
        if months_c[k] != months_c[k - 1]:
            m = d.C * 12 + k
            started = [a for a in dep["assets"] if a["start"] == m]
            stopped = [a for a in dep["assets"] if a["last"] == m - 1]
            claim(len(started) + len(stopped) == 1, "each change in the monthly charge has one cause")
            claim(all(a["disposal"] and month_index(a["disposal"]) == m for a in stopped),
                  "an asset stops being depreciated during the year only because it is disposed of")
            a = (started or stopped)[0]
            changes.append(dict(amount=months_c[k], month=MONTHS[k], code=a["code"], kind="in" if started else "out",
                                date=a["service"] if started else a["disposal"]))
    ledger_dep = d.one("SELECT SUM(g.Debit) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
                       "WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryType = 'Depreciation' AND g.AccountID = ? "
                       "AND g.FiscalYear = ?", d.account("1090"), d.C)
    dep_c, dep_n = round(sum(months_c), 2), round(sum(months_n), 2)
    claim(abs(dep_c - ledger_dep) < 0.005, f"the schedule's {d.C} depreciation equals the ledger")
    claim(len(set(months_n)) == 1, f"every month of {d.N} carries the same depreciation")
    ending = [a for a in dep["assets"] if a["end"] // 12 == d.N and not a["disposal"]]
    claim(len(ending) == 1, f"one asset reaches the end of its life in {d.N}")
    new = []
    for a in dep["assets"]:
        if a["service"] >= f"{d.F}-01-01":
            rows = d.q("SELECT DISTINCT po.PONumber, po.OrderTotal, e.MaxApprovalAmount FROM PurchaseInvoice pi "
                       "JOIN PurchaseOrder po ON po.PurchaseOrderID = pi.PurchaseOrderID JOIN PurchaseOrderLine pol "
                       "ON pol.PurchaseOrderID = po.PurchaseOrderID JOIN Employee e ON e.EmployeeID = po.ApprovedByEmployeeID "
                       "WHERE pi.ReceivedDate = ? AND pol.ItemID = ? AND ABS(pi.GrandTotal - ?) < 0.005", a["service"], a["item"], a["cost"])
            claim(len(rows) == 1, f"{a['code']} is the purchase of one purchase order")
            claim(all(t > lim for _, t, lim in rows), f"{a['code']}'s purchase order was approved above the approver's limit")
            new.append(dict(code=a["code"], po=rows[0][0] if rows else "?"))
    employees = d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter c ON c.CostCenterID = e.CostCenterID "
                      "WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly' AND e.IsActive = 1")
    claim(employees == yearly(d)[-1]["surge"]["entries"] // yearly(d)[-1]["surge"]["days"],
          "the active hourly manufacturing employees are the ones who clock on surge days")
    claim(d.one("SELECT MAX(RegularHours) FROM TimeClockEntry WHERE substr(WorkDate, 1, 4) = ?", str(d.C)) >= STRAIGHT_DAY,
          "a full day is 8 regular hours")
    days = working_days(d, f"{d.C}-01-01", f"{d.C}-12-31")
    capacity = employees * STRAIGHT_DAY * days
    avail = d.one("SELECT SUM(AvailableHours) FROM WorkCenterCalendar WHERE substr(CalendarDate, 1, 4) = ?", str(d.C))
    ys = yearly(d)
    levels = [1.0, round(ys[0]["ratio"], 2), round(ys[-1]["ratio"], 3)]
    need = [std * k for k in levels]
    claim(max(need) < capacity, "no scenario needs overtime for capacity")
    premium = ys[-1]["premium"]
    overhead = salary * (1 + b) + foh + dep_n
    labor = [h * r * (1 + b) for h in need]
    conv = [labor[0] + overhead, labor[1] + overhead, labor[2] + premium * (1 + b) + overhead]
    variance = [c - released for c in conv]
    actual = ledger(d)[d.C]["conversion"]
    claim(abs(variance[2] / actual - 1) < 0.05, f"the variance at the {d.C} level is close to {d.C}'s conversion variance")
    rate_b = r * (1 + b)
    std_labor_rate, oh_rate = comp["labor"] / std, comp["overhead"] / std
    use = std / capacity
    direct = d.one("SELECT SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry WHERE LaborType = 'Direct Manufacturing' "
                   "AND substr(WorkDate, 1, 4) = ?", str(d.C))
    claim(direct < ys[-1]["std"], "direct time stays within the standard hours")
    return dict(std=std, released=released, conv_rate=released / std, budget=word(round(budget / made)),
                forecast_low=word(math.floor(min(ratios))), forecast_high=word(math.ceil(max(ratios))),
                rate=r, burden=b, salary=salary, titles=titles, foh=foh, acct=d.account("1090"),
                jan=months_c[0], changes=changes, dep_c=dep_c, monthly_n=months_n[0], dep_n=dep_n,
                ending=dict(code=ending[0]["code"], month=MONTHS[ending[0]["end"] % 12]) if ending else dict(code="?", month="?"),
                new=new, employees=employees, days=days, capacity=capacity, avail=avail,
                levels=levels, need=need, conv=conv, variance=variance, premium=premium, actual=actual,
                rate_b=rate_b, std_labor_rate=std_labor_rate, labor_excess=round((rate_b - std_labor_rate) * std, -3),
                overhead=overhead, applied=comp["overhead"], oh_rate=oh_rate,
                oh_excess=round(overhead - comp["overhead"], -3), use=use)


# --- Requirement 5 -------------------------------------------------------------------------------

@note("case3.r5", CASE)
def r5(d, claim):
    p = processed(d)
    claim(p["left_start"][:8] == f"{d.C}-12-", f"the days left after the last processed period are in December {d.C}")
    claim(d.one("SELECT COUNT(*) FROM (SELECT CalendarDate FROM WorkCenterCalendar GROUP BY 1 "
                "HAVING SUM(IsWorkingDay) NOT IN (0, COUNT(*)))") == 0, "every work center has the same working days")
    holiday = d.q("SELECT ExceptionReason, strftime('%w', CalendarDate) FROM WorkCenterCalendar WHERE WorkCenterID = ? "
                  "AND CalendarDate = ?", calendar_wc(d), f"{d.C}-12-25")
    claim(holiday and holiday[0][0] == "Holiday" and holiday[0][1] not in ("0", "6"),
          f"25 December {d.C} is a holiday on a weekday")
    accounts = {}
    for center, number, debit in d.q("SELECT c.CostCenterName, a.AccountNumber, SUM(g.Debit) FROM GLEntry g JOIN Account a "
                                     "ON a.AccountID = g.AccountID JOIN CostCenter c ON c.CostCenterID = g.CostCenterID "
                                     "WHERE g.SourceDocumentType = 'PayrollSummary' AND g.FiscalYear = ? AND g.Debit > 0 "
                                     "GROUP BY 1, 2", d.C):
        accounts.setdefault(center, set()).add(str(number))
    claim(accounts.get("Manufacturing") == {"1090"}, "the payroll of Manufacturing is debited to 1090")
    others = {c: a for c, a in accounts.items() if c != "Manufacturing"}
    claim(all("6060" in a and len(a) == 2 for a in others.values()),
          "each other cost center's payroll is debited to one salary account and 6060")
    claim({n for a in others.values() for n in a} - {"6060"} ==
          {"6010", "6020", "6030", "6040", "6050", "6230", "6240", "6250", "6280"},
          "the salary accounts of the other cost centers are 6010-6050, 6230, 6240, 6250, and 6280")
    names = {str(n): a for n, a in d.q("SELECT AccountNumber, AccountName FROM Account WHERE AccountNumber IN ('2030', '6060')")}
    claim(names == {"2030": "Accrued Payroll", "6060": "Payroll Taxes and Benefits"}, "the account names are as written")
    prior = prior_year_end(d)
    claim(prior["n_full"] == 1 and prior["n_cross"] == 1,
          f"one pay period of {d.P} work is paid in {d.C}, and one crosses the year-end")
    change = p["accrual"] - prior["total"]
    claim(0 < change < p["accrual"], f"recording both accruals raises {d.C} expense, by less than the new accrual")
    a2030 = d.account("2030")
    entry = d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")
    opening = d.one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?", a2030, entry)
    claim(abs(d.balance(["2030"], f"{d.C}-12-31") + opening) < 0.005, "2030 holds only its opening balance")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'JournalEntry' AND VoucherNumber <> ?",
                a2030, entry) == 0, "no journal entry ever accrued payroll in 2030")
    led = ledger(d)[d.C]
    std = completions(d)["std"]
    fg = d.balance(["1040"], f"{d.C}-12-31")
    delivered = d.q("WITH inv AS (SELECT si.SalesInvoiceID, si.SubTotal, (SELECT MAX(s.DeliveryDate) FROM SalesInvoiceLine sil "
                    "JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                    "WHERE sil.SalesInvoiceID = si.SalesInvoiceID) AS dd, (SELECT MIN(g.PostingDate) FROM GLEntry g WHERE "
                    "g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID = si.SalesInvoiceID) AS pd FROM SalesInvoice si) "
                    "SELECT COUNT(*), SUM(SubTotal), MIN(dd) FROM inv WHERE substr(dd, 1, 4) = ? AND substr(pd, 1, 4) = ?",
                    str(d.P), str(d.C))[0]
    claim(delivered[2] is not None and delivered[2][5:7] == "12", f"the {d.P} deliveries posted in {d.C} were all delivered in December")
    n_uninv, uninv, uninv_std, first_ship = d.q(f"SELECT COUNT(*), SUM(ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2)), "
                                                f"SUM(sl.ExtendedStandardCost), MIN(s.ShipmentDate) {UNINVOICED}")[0]
    claim(first_ship >= f"{d.C}-12-01", f"the shipment lines never invoiced were all shipped in December {d.C}")
    posted = d.one("SELECT SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.SourceDocumentType = "
                   "'Shipment' AND a.AccountSubType = 'COGS' AND g.SourceLineID IN (SELECT sl.ShipmentLineID " + UNINVOICED + ")")
    claim(posted is not None and abs(posted - uninv_std) < 0.005, "their standard cost is already in cost of goods sold")
    net_rev = uninv - delivered[1]
    claim(net_rev > 0, f"the cutoff raises {d.C} revenue")
    close = d.closes_of(d.C)[-1]
    ni = d.one("SELECT g.Credit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.VoucherNumber = ? "
               "AND a.AccountName = 'Retained Earnings'", close)
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountName LIKE '%Income Tax%'") == 0, "the ledger records no income tax")
    effect = net_rev - change
    claim(abs(effect) / ni < 0.002, "the effect on income is under 0.2%")
    asv = d.q("SELECT PurchaseInvoiceID, InvoiceNumber, GrandTotal, ReceivedDate FROM PurchaseInvoice WHERE substr(InvoiceDate, 1, 4) = ? "
              "AND substr(ReceivedDate, 1, 4) = ?", str(d.P), str(d.C))
    claim(len(asv) == 1, f"one supplier invoice dated in {d.P} was received in {d.C}")
    pid, number, total, received = asv[0]
    accruals = d.q("SELECT DISTINCT j.EntryNumber, j.PostingDate FROM PurchaseInvoiceLine l JOIN JournalEntry j ON j.JournalEntryID = "
                   "l.AccrualJournalEntryID WHERE l.PurchaseInvoiceID = ?", pid)
    claim(len(accruals) == 1 and accruals[0][1] <= f"{d.P}-12-31", "the invoice was accrued before the year-end")
    a2040 = d.account("2040")
    claim(d.one("SELECT SUM(Credit) FROM GLEntry WHERE VoucherNumber = ? AND AccountID = ?", accruals[0][0], a2040) > 0
          and d.one("SELECT SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'PurchaseInvoice' AND SourceDocumentID = ? "
                    "AND AccountID = ?", pid, a2040) > 0,
          "its accrual credited 2040, and the invoice cleared it, so the accrual carried the liability at the year-end")
    return dict(p=p, left_day=int(p["left_start"][8:]), prior=prior, change=change, hours=round(hour_based(d, d.P), -3),
                opening=opening, entry=entry, actual_rate=(led["payroll"] + led["je"]) / std, std_rate=led["released"] / std,
                fg=fg, delivered=delivered[1], n_uninv=n_uninv, uninv=uninv, uninv_std=uninv_std, net_rev=net_rev, ni=ni,
                adj_ni=ni - change + net_rev, about=round(p["accrual"], -3),
                asv=dict(number=number, total=total, received=received, je=accruals[0][0],
                         month=MONTHS[int(accruals[0][1][5:7]) - 1], year=accruals[0][1][:4]))


# --- Requirement 6 -------------------------------------------------------------------------------

@note("case3.r6", CASE)
def r6(d, claim):
    ys = yearly(d)
    employees = ys[-1]["surge"]["entries"] // ys[-1]["surge"]["days"]
    capacity = employees * STRAIGHT_DAY * working_days(d, f"{d.C}-01-01", f"{d.C}-12-31")
    claim(completions(d)["std"] * ys[0]["ratio"] < capacity,
          f"a plan at the {d.F} level of hours per standard hour needs no overtime, since capacity allows it")
    return {}
