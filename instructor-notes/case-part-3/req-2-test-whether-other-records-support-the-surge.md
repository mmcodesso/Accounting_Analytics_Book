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

The audit left one question: were the surge-day hours worked? This requirement tests them against every record that is not the time clock and grades each record for independence as well as agreement, because two records from one source agree for free. The analytics type is diagnostic.

Students can:

- compare two populations with conditional aggregation and a window (Step 1);
- reperform a control and place its failure in design or operation (Steps 3 and 4);
- test the reasons behind a payment against the plant's own plans (Steps 5 and 6);
- grade evidence for independence (Step 7).

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance) and M9 (audit data analytics); IMA Reporting and Control (internal control); IFAC IES 2 (f) and IES 4 (a); AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql with the views SurgeDays and PlantEntries of Requirement 1, saved with **Write Changes**. It builds on Chapter 11's CASE and windows and Chapter 12's tests (Exercise 12.4 on overtime approval).
- **Data conditions.** Roster times are `HH:MM:SS` with no date, clock times carry the date, and a late shift clocks out the next day. RoughCutCapacityPlan repeats a work center's available hours on every item row.

## How to run it

Pairs, about 150 minutes: 25 for Steps 1 and 2, 35 for the roster and clock, 30 for the rule, 30 for the plans and approvals, 30 for the matrix. Hold back the matrix until Requirement 3's weekly comparison is done. **Collect** the script and matrix.

## Step-by-step solution

### Part 1: Surge days against ordinary days

**Step 1. Compare attendance, clock-in times and groups sharing one time.** Daily counts distinct employees and clock-in times, Plant the hourly employees, and Groups the largest group on one clock-in timestamp, with a window.

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

**Check:** 93 surge days at 2.0 clock-in times a day and a largest group of 32.6, against 652 ordinary days at 22.4 and 13.2. All 64 are present on every surge day and on 576 ordinary days, so attendance says little. **Watch for:** three wrong versions.

- `COUNT(*)` for the employees counts clock rows: a few ordinary days carry two entries for one person, and the count reads 573 days.

- A window partitioned by the date alone counts the whole day's attendance: the largest group reads 64.0 and 62.8, the attendance itself.
- A headcount from the whole cost center (67) leaves 0 days with everyone present.

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

**Step 4. Infer the rule behind the Off Shift Clocking exceptions and apply it.** The three exceptions are clock-ins at 10:00 against a start of 08:00, 120 minutes after it. They point to a rule on arrival, but cannot show its threshold, whether it tests departures or whether approved overtime is exempt, which only the configuration shows. RuleMinutes, Timing (minutes rounded with `ROUND`) and Flagged feed a query that counts arrivals, departures and flags.

```sql
    SUM(CASE WHEN t.Arrival >= (SELECT Minutes FROM RuleMinutes)
        THEN 1 ELSE 0 END) AS LateArrivals,
    SUM(CASE WHEN t.Departure > (SELECT Minutes FROM RuleMinutes)
        THEN 1 ELSE 0 END) AS LateDepartures,
```

**Check:** surge entries: 0 late arrivals, 5,952 late departures, 0 flagged; ordinary: 3 (date-shifted entries, Requirement 1), 2,588 and 8. On that rule the design fails, because surge arrivals are early and nothing compares the approved late departures with a roster or plan, a finding to confirm against the configuration. The operation fails in the recorded review: all 18 exceptions are Open, none reviewed, four naming the wrong employee. **Watch for:** applying the rule to departures flags all 5,952 surge entries and reverses the finding. Unrounded minutes leave exact two-hour departures a fraction of a second either side and give 2,591, and in whole minutes `>=` gives 2,592. An ungrouped Flagged CTE changes nothing here.

### Part 3: The plans and the approvals

**Step 5. Test the calendar and the planned load.** Join SurgeDays to WorkCenterCalendar on the date. For the load, take each work center's hours once a week, compare planned load with available hours in weeks with and without surge days through the week of 2026-12-07, and count the weeks and work centers planned above capacity.

```sql
Centers AS (
    SELECT BucketWeekStartDate AS WeekStart, WorkCenterID,
        SUM(PlannedLoadHours) AS PlannedHours,
        MAX(AvailableHours) AS AvailableHours
    FROM RoughCutCapacityPlan
    GROUP BY BucketWeekStartDate, WorkCenterID
),
```

**Check:** every surge day is a working day, 6 with maintenance at a work center and 21 at reduced capacity. Load in surge weeks against other weeks: 2024, 0.568 against 0.687; 2025, 0.596 against 0.618; 2026, 0.585 against 0.614. Surge weeks were planned more lightly on average, yet 2 of the 31 were planned above the plant's capacity, with 9 work-center weeks above theirs, and so were 10 other weeks. An average cannot rule out an overloaded week, and the plan does not explain a recurring pattern. **Watch for:** three wrong versions.

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

**Step 7. Grade each test for independence, and name two explanations.** Place every test in one result column and mark whether its record is independent of the Production Manager and the time clock. Attendance and punches support the hours but come from the clock. Clock-in times, rosters and approvals contradict them and come from the clock or the Production Manager. The calendar, the plan and the output lie outside the clock trail, their independence from that manager not established, and none supports the hours as recorded. Absences are silent. Two explanations fit, the hours worked and entered as a block or not worked as recorded, and evidence outside the database would separate them.

![The corroboration matrix, the exhibit that carries this requirement into the memo.](../figures/case-part-3/IF-C3-2-A.pdf)

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Surge and ordinary days | 93; 652 | 1 |
| Minutes early and late on surge days | 30; 240 | 3 |
| Surge entries flagged by the rule | 0 | 4 |
| Surge approvals citing an ended operation | 1,475 of 5,952 | 6 |

> **Instructor notes, Requirement 2:** 93 surge days against 652 ordinary days, hourly manufacturing employees only. Employees per day (distinct people) 64.0 against 62.8, and 576 of the 652 ordinary days also had all 64, so attendance says little. Different clock-in times per day 2.0 against 22.4; the largest group sharing one clock-in timestamp is 32 or 33 on every surge day (COUNT(\*) OVER (PARTITION BY WorkDate, ClockInTime)), against 13.2 on average and 25 at most on ordinary days. Every surge entry (5,952) has meal punches, against 17,707 of the 40,974 ordinary entries (43.2%). The punches are all Badge punches whose timestamps equal the clock entry's (except on nine entries, all cited by attendance exceptions), so they repeat the timekeeping record rather than corroborate it. Rosters: every surge entry is rostered for a normal eight-hour shift, 07:00-15:30 or 15:00-23:30, created seven days ahead by the Production Manager, who creates every manufacturing roster; the clock shows 06:30-19:30 or 14:30-03:30, 30 minutes early and 240 minutes late, 12.5 hours against 8.0. On ordinary days the rostered hours equal the clocked hours on 30,251 of 40,974 entries (73.8%), on surge days on none. The control: the three Off Shift Clocking exceptions are clock-ins 120 minutes after the scheduled start (10:00 against 08:00). They are consistent with a rule that flags arrivals 120 minutes or more late, but three examples cannot show its threshold, whether it also tests departures, or whether approved overtime is exempt, which only the system's configuration would show. Surge arrivals are 30 minutes early and the departures four hours late, with approved overtime, so a rule on arrival could not flag them, and the anti-join finds none flagged (2,588 ordinary entries also end more than 120 minutes after their roster, counted in whole minutes). Design, as far as the records show: nothing compares overtime with a roster or a plan made in advance. Operation: all 18 exceptions are Open and none was reviewed in up to three years, among them the three Paid Without Approved Clock exceptions (the Pending entries of test H1) and four that name the wrong employee. Calendar: every surge day is a working day, but on 6 of them a work center was under maintenance and on 21 at reduced capacity. Rough-cut plan (Monday weeks, available hours taken once per work center and week, through 2026-12-07): planned load against available hours was 0.568, 0.596, and 0.585 in weeks with surge days against 0.687, 0.618, and 0.614 in other weeks (2024-2026), so surge weeks were planned more lightly on average. An average does not rule out an overloaded week: 2 of the 31 surge weeks were planned above the plant's capacity (2025-12-08 at 102.0% and 2026-12-07 at 108.7%), with 9 work-center weeks over capacity in 5 surge weeks, and 10 of the 121 other weeks were too, so the plan does not explain a pattern that recurs across the plant. The four reason codes are used 1,488 times each on surge days. Approvals: 1,475 of the 5,952 surge-day approvals cite a work order operation, and every one of those operations had ended before the work date; on ordinary days 497 of the 2,397 cited operations had ended. Surge days fall mostly late in the week (Monday 4, Tuesday 13, Wednesday 19, Thursday 26, Friday 31). Matrix: supports: every employee present and badge punches, both from the time clock; contradicts or unexplained: one clock-in time for half the plant, overtime in no roster, approvals citing finished work, lighter planned load in surge weeks, overtime on maintenance and reduced-capacity days, and the output (more in surge weeks, not in proportion to the hours, less after; Requirement 3); silent: absences (none in Manufacturing). Independence: punches and clock entries are one system, rosters and approvals one manager. The calendar, the plan and the output lie outside the clock trail, but who keeps them is not shown, so their independence from the Production Manager is not established. Two explanations: the hours were worked and the time was entered for the plant as a block, which breaks the timekeeping control but not the pay; or the hours were not worked as recorded. Evidence outside the database: building access or gate logs, statements of supervisors and employees, security video, machine-run or utility data, and the timekeeping system's own log of who entered the punches.

## What a strong answer says

- **Corroboration and independence.** Agreement from one system, contradiction from the rest, and no record shown to be independent of the Production Manager.
- **The control.** A candidate rule with its limits, a design failure to confirm against the configuration, and an operation failure in the recorded review.
- **Wording.** Unsupported, never fictitious.

## Common mistakes and how to respond

- **A window without the clock-in time, or the cost center as the headcount.** *Symptom:* the largest group equals the attendance; no day has everyone present. *Response:* ask what makes a group, and who has a time clock.
- **The rule applied to departures.** *Symptom:* everything would have been flagged. *Response:* ask what the system's own exceptions tested.
- **Plan tests on the item rows, or without the cut-off.** *Symptom:* a load of a few hundredths, or a row after the data. *Response:* ask how often a center's hours repeat.
- **Fictitious, or proven.** *Symptom:* "the hours were faked", or "attendance proves them". *Response:* ask which record is independent and what each explanation predicts.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Surge against ordinary days | 20 | All measures; window correct; hourly headcount | A measure wrong |
| Roster and clock | 15 | Minutes early and late; rostered against clocked | Dates or times mishandled |
| Control reperformance | 20 | Rule inferred with its limits, minutes rounded; design and operation | Applied to departures, or one failure |
| Plans and approvals | 15 | Cut-off, hours once a week, operations tested | A fan-out |
| Matrix and explanations | 30 | Result and independence for each test; two explanations; outside evidence | No independence |

## Extensions and discussion questions

- Count the ordinary entries that leave more than the rule's minutes late (2,588) and ask why so few were flagged.
- Discuss: which record would you ask for first, and from whom?
