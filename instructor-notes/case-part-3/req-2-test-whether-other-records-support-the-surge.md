# Requirement 2: Test whether other records support the surge days (Chapters 10 to 12; auditing)

| | |
|---|---|
| Unit | Case Part 3: Planning the Plant's Hours for 2027 |
| Item | Requirement 2 |
| Perspective | Auditing |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 150 minutes |
| Solution file | PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 2, and the Requirement 2 model answer in its closing comments (the corroboration matrix, independence, the control, the two explanations) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The audit left one question: were the surge-day hours worked? This requirement tests them against every record that is not the time clock and grades each record for independence as well as agreement, because two records from one source agree for free. The wording rule holds: the hours are unsupported, not unworked. The analytics type is diagnostic.

Students can:

- compare two populations with conditional aggregation and a window (Step 1);
- reperform a control and place its failure in design or operation (Steps 3 and 4);
- test the reasons behind a payment against the plant's own plans (Steps 5 and 6);
- grade evidence for independence (Step 7).

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance) and M9 (audit data analytics); IMA Reporting and Control (internal control); IFAC IES 2 (f) and IES 4 (a); AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql with the views SurgeDays and PlantEntries of Requirement 1, saved with **Write Changes**. It builds on Chapter 11's CASE and windows and Chapter 12's tests (Exercise 12.4 on overtime approval).
- **Data conditions.** The plant has 64 hourly employees. Roster times are `HH:MM:SS` with no date, clock times carry the date, and a late shift clocks out the next day. RoughCutCapacityPlan repeats a work center's available hours on every item row. The absence table records none in Manufacturing.

## How to run it

Pairs, about 150 minutes: 25 for Steps 1 and 2, 35 for the roster and clock, 30 for the rule, 30 for the plans and approvals, 30 for the matrix. The routine: type the two comment lines and the query, select it, click **Execute all/selected SQL**, read the message pane. Hold back the rule until a pair has listed the three Off Shift Clocking exceptions, and the matrix until Requirement 3's weekly comparison is done. **Collect** the script and matrix.

## Step-by-step solution

### Part 1: Surge days against ordinary days

**Step 1. Compare attendance, clock-in times and groups sharing one time.** Daily counts entries and distinct clock-in times, Plant the hourly employees, and Groups the largest group on one clock-in timestamp, with a window.

```sql
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
```

**Check:** 93 surge days at 2.0 clock-in times a day and a largest group of 32.6, against 652 ordinary days at 22.4 and 13.2. All 64 are present on every surge day and on 573 ordinary days, so attendance says little. **Watch for:** two wrong versions.

- A window partitioned by the date alone counts the whole day's attendance: the largest group reads 64.0 and 62.8, the attendance itself.
- A headcount from the whole cost center (67) leaves 0 days with everyone present. The salaried staff keep no time clock.

**Step 2. Count the entries with meal punches.** Summarize the punches, then left-join.

```sql
WITH Meals AS (
    SELECT TimeClockEntryID
    FROM TimeClockPunch
    WHERE PunchType = 'Meal Start'
    GROUP BY TimeClockEntryID
)
```

**Check:** every surge entry has meal punches, against 17,707 of 40,974 ordinary entries. The punches equal the clock's times except on nine entries, so they repeat the clock and do not corroborate it. **Watch for:** joining the punches unsummarized repeats the entries, 11,904 for 5,952.

### Part 2: The roster and the control

**Step 3. Measure each entry's clock time before and after its roster.** An Outside CTE joins each plant entry to its roster and builds the roster's timestamp from its date and time with `||`; `julianday` gives the minutes.

```sql
        ROUND((julianday(r.RosterDate || ' '
            || r.ScheduledStartTime)
            - julianday(pe.ClockInTime)) * 1440) AS MinutesEarly,
        ROUND((julianday(pe.ClockOutTime)
            - julianday(r.RosterDate || ' '
            || r.ScheduledEndTime)) * 1440) AS MinutesLate
```

**Check:** the surge entries were rostered 8.0 hours on 07:00-15:30 and 15:00-23:30 by the Production Manager, seven days ahead, and clocked 06:30-19:30 and 14:30-03:30, 12.5 hours: 30 minutes early and 240 late. Roster equals clock on 30,251 of 40,974 ordinary entries and on 0 surge entries. **Watch for:** the roster's time without its date reads as a day in the year `2000`, and the minutes run to millions (the smallest is 12,840,450); the clock-out taken as a time of day makes the late shift leave early, -1,200 minutes.

**Step 4. Find the rule behind the Off Shift Clocking exceptions and apply it.** The three exceptions are clock-ins at 10:00 against a start of 08:00, 120 minutes after it, so the rule tests arrival. RuleMinutes, Timing and Flagged CTEs feed a final query that counts arrivals and departures against the rule, and the entries flagged.

```sql
    SUM(CASE WHEN t.Arrival >= (SELECT Minutes FROM RuleMinutes)
        THEN 1 ELSE 0 END) AS LateArrivals,
    SUM(CASE WHEN t.Departure > (SELECT Minutes FROM RuleMinutes)
        THEN 1 ELSE 0 END) AS LateDepartures,
```

**Check:** surge entries: 0 late arrivals, 5,952 late departures, 0 flagged; ordinary: 3, 2,591 and 8. Design failed: surge arrivals are early, and the late departures count as approved overtime that nothing compares with a roster or a plan. Operation failed: all 18 exceptions are Open, none reviewed, four naming the wrong employee. **Watch for:** applying the rule to departures flags all 5,952 surge entries and reverses the finding; `>` against `>=` and an ungrouped Flagged CTE change nothing here.

### Part 3: The plans and the approvals

**Step 5. Test the calendar and the planned load.** Join SurgeDays to WorkCenterCalendar on the date. For the load, take each work center's hours once a week and compare planned load with available hours in weeks with and without surge days, through the week of 2026-12-07.

```sql
Available AS (
    SELECT WeekStart, SUM(Hours) AS AvailableHours
    FROM (
        SELECT BucketWeekStartDate AS WeekStart, WorkCenterID,
            MAX(AvailableHours) AS Hours
        FROM RoughCutCapacityPlan
        GROUP BY BucketWeekStartDate, WorkCenterID
    ) AS t
    GROUP BY WeekStart
),
```

**Check:** every surge day is a working day, 6 with maintenance at a work center and 21 at reduced capacity. Load in surge weeks against other weeks: 2024, 0.568 against 0.687; 2025, 0.596 against 0.618; 2026, 0.585 against 0.614. The surge weeks were not planned overloads. **Watch for:** three wrong versions.

- Summing every item row's hours makes the load a few hundredths of capacity (0.007 to 0.008).
- Without the cut-off a row for 2027 appears, with 7 weeks.
- `'weekday 1'` without `'-6 days'` moves dates to the next Monday: 14 surge weeks in 2026, 35 without.

**Step 6. Test the overtime approvals.** For each approval of a plant entry, join the operation it cites and test whether it had ended before the work date.

```sql
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
```

**Check:** the four reason codes are used 1,488 times each on surge days, all approved by the Production Manager. Of 5,952 surge approvals 1,475 cite an operation, all ended; of 10,723 ordinary approvals 2,397 cite one and 497 had ended. **Watch for:** an `INNER JOIN` to the operations drops the approvals that cite none and reads 1,475 surge approvals, all citing a finished operation; `<=` counts an operation ending on the work date as ended, and all 2,397 ordinary citations look stale.

### Part 4: The matrix

**Step 7. Grade each test for independence, and name two explanations.** Place every test in one result column and mark whether its record is independent of the Production Manager and the time clock. Attendance and punches support the hours but come from the clock; clock-in times, rosters and approvals contradict them and come from the clock or the Production Manager; the calendar, the plan and the output are outside, and none supports the hours as recorded; absences are silent. Two explanations fit: the hours were worked and entered for the plant as a block, or they were not worked as recorded. Gate logs, supervisor statements, security video, machine data and the system's own entry log would separate them.

![The corroboration matrix, the exhibit that carries this requirement into the memo.](../figures/case-part-3/IF-C3-2-A.pdf)

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Surge and ordinary days | 93; 652 | 1 |
| Minutes early and late on surge days | 30; 240 | 3 |
| Surge entries flagged by the rule | 0 | 4 |
| Surge approvals citing an ended operation | 1,475 of 5,952 | 6 |

> **Instructor notes, Requirement 2:** 93 surge days against 652 ordinary days, hourly manufacturing employees only. Employees per day 64.0 against 62.8, and 573 of the 652 ordinary days also had all 64, so attendance says little. Different clock-in times per day 2.0 against 22.4; the largest group sharing one clock-in timestamp is 32 or 33 on every surge day (COUNT(\*) OVER (PARTITION BY WorkDate, ClockInTime)), against 13.2 on average and 25 at most on ordinary days. Every surge entry (5,952) has meal punches, against 17,707 of the 40,974 ordinary entries (43.2%). The punches are all Badge punches whose timestamps equal the clock entry's (except on nine entries, all cited by attendance exceptions), so they repeat the timekeeping record rather than corroborate it. Rosters: every surge entry is rostered for a normal eight-hour shift, 07:00-15:30 or 15:00-23:30, created seven days ahead by the Production Manager, who creates every manufacturing roster; the clock shows 06:30-19:30 or 14:30-03:30, 30 minutes early and 240 minutes late, 12.5 hours against 8.0. On ordinary days the rostered hours equal the clocked hours on 30,251 of 40,974 entries (73.8%), on surge days on none. The control: the three Off Shift Clocking exceptions are clock-ins 120 minutes after the scheduled start (10:00 against 08:00), so the rule tests arrival; surge arrivals are 30 minutes early and the four-hour late departures count as approved overtime, so no surge entry could be flagged, and the anti-join finds none flagged (2,591 ordinary entries also end more than 120 minutes after their roster). Design: nothing compares overtime with a roster or a plan made in advance. Operation: all 18 exceptions are Open and none was reviewed in up to three years, among them the three Paid Without Approved Clock exceptions (the Pending entries of test H1) and four that name the wrong employee. Calendar: every surge day is a working day, but on 6 of them a work center was under maintenance and on 21 at reduced capacity. Rough-cut plan (Monday weeks, available hours taken once per work center and week, through 2026-12-07): planned load against available hours was 0.568, 0.596, and 0.585 in weeks with surge days against 0.687, 0.618, and 0.614 in other weeks (2024-2026), so the surge weeks were not planned overloads; the four reason codes are used 1,488 times each on surge days. Approvals: 1,475 of the 5,952 surge-day approvals cite a work order operation, and every one of those operations had ended before the work date; on ordinary days 497 of the 2,397 cited operations had ended. Surge days fall mostly late in the week (Monday 4, Tuesday 13, Wednesday 19, Thursday 26, Friday 31). Matrix: supports: every employee present, badge punches, more output in surge weeks (Requirement 3); contradicts or unexplained: one clock-in time for half the plant at once, overtime in no roster, approvals citing finished work, no planned overload, overtime on maintenance and reduced-capacity days; silent: absences (none recorded in Manufacturing in any year). Independence: punches and clock entries are one system, rosters and overtime approvals come from the same manager, and only the calendar, the capacity plan, and the output come from outside timekeeping. Two explanations: the hours were worked and the time was entered for the plant as a block, which breaks the timekeeping control but not the pay; or the hours were not worked as recorded. Evidence outside the database: building access or gate logs, statements of supervisors and employees, security video, machine-run or utility data, and the timekeeping system's own log of who entered the punches.

## What a strong answer says

- **Corroboration.** Attendance and punches agree with the hours but are one system; the clock-in pattern, roster, approvals and plan contradict them.
- **Independence.** Rosters and approvals come from one manager; only the calendar, the capacity plan and the output are outside, and they do not support the hours.
- **The control.** A design failure (the rule tests arrival only) and an operation failure (every exception open, none reviewed, some misattributed).
- **Wording.** Unsupported, never fictitious; the evidence that separates the explanations lies outside the database.

## Common mistakes and how to respond

- **A window without the clock-in time, or the cost center as the headcount.** *Symptom:* the largest group equals the attendance; no day has everyone present. *Response:* ask what makes a group, and who has a time clock.
- **A time with no date.** *Symptom:* millions of minutes, or a late shift that leaves early. *Response:* ask what date each time belongs to.
- **The rule applied to departures.** *Symptom:* everything would have been flagged. *Response:* ask what the system's own exceptions tested.
- **Plan tests on the item rows, or without the cut-off.** *Symptom:* a load of a few hundredths, or a row after the data. *Response:* ask how often a center's hours repeat.
- **Fictitious, or proven.** *Symptom:* "the hours were faked", or "attendance proves them". *Response:* ask which record is independent and what each explanation predicts.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Surge against ordinary days | 20 | All measures; window correct; hourly headcount | A measure wrong |
| Roster and clock | 15 | Minutes early and late; rostered against clocked | Dates or times mishandled |
| Control reperformance | 20 | Rule found, applied to arrival; design and operation | Applied to departures, or one failure |
| Plans and approvals | 15 | Cut-off, hours once a week, operations tested | A fan-out |
| Matrix and explanations | 30 | Result and independence for each test; two explanations; outside evidence | No independence |

## Extensions and discussion questions

- Count the ordinary entries that leave more than the rule's minutes late (2,591) and ask why so few were flagged.
- Group the surge days by weekday and say what the pattern suggests (Monday 4, Friday 31).
- Discuss: which record would you ask for first, and from whom?
