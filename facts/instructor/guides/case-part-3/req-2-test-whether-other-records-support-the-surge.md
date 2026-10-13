---
note: case3.r2
uses: [case3.g2]
title: Test whether other records support the surge days (Chapters 10 to 12; auditing)
kind: requirement
number: '2'
unit: case3
perspective: auditing
tool: sql
minutes: 150
solution: "PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 2, and the Requirement 2 model answer in its closing comments (the corroboration matrix, independence, the control, the two explanations)"
figures:
  - id: IF-C3-2-A
    kind: diagram
    purpose: The corroboration matrix, the exhibit that carries this requirement into the memo.
    shows: "One row for each test (attendance, punches, clock-in times, roster against clock, approvals, planned load, calendar, output, absences), three result columns (Supports, Contradicts or unexplained, Silent) with one mark each, and a column that says in a word and a symbol whether the record is independent of the Production Manager and the time clock."
    data: The results of Steps 1 to 6 and of Requirement 3's weekly comparison.
---
{% set g = case3_g2 %}
# Requirement 2: Test whether other records support the surge days (Chapters 10 to 12; auditing)

{{ header() }}

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
- **Data conditions.** The plant has {{ plant }} hourly employees. Roster times are `HH:MM:SS` with no date, clock times carry the date, and a late shift clocks out the next day. RoughCutCapacityPlan repeats a work center's available hours on every item row. The absence table records none in Manufacturing.

## How to run it

Pairs, about 150 minutes: 25 for Steps 1 and 2, 35 for the roster and clock, 30 for the rule, 30 for the plans and approvals, 30 for the matrix. The routine: type the two comment lines and the query, select it, click **Execute all/selected SQL**, read the message pane. Hold back the rule until a pair has listed the {{ n_off }} Off Shift Clocking exceptions, and the matrix until Requirement 3's weekly comparison is done. **Collect** the script and matrix.

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

**Check:** {{ s.days }} surge days at {{ s.clock_ins|num(1) }} clock-in times a day and a largest group of {{ s.largest|num(1) }}, against {{ o.days }} ordinary days at {{ o.clock_ins|num(1) }} and {{ o.largest|num(1) }}. All {{ plant }} are present on every surge day and on {{ o.all_present }} ordinary days, so attendance says little. **Watch for:** two wrong versions.

- A window partitioned by the date alone counts the whole day's attendance: the largest group reads {{ g.flat_largest.Surge|num(1) }} and {{ g.flat_largest.Ordinary|num(1) }}, the attendance itself.
- A headcount from the whole cost center ({{ g.cost_center_staff }}) leaves {{ g.all_present_67 }} days with everyone present. The salaried staff keep no time clock.

**Step 2. Count the entries with meal punches.** Summarize the punches, then left-join.

```sql
WITH Meals AS (
    SELECT TimeClockEntryID
    FROM TimeClockPunch
    WHERE PunchType = 'Meal Start'
    GROUP BY TimeClockEntryID
)
```

**Check:** every surge entry has meal punches, against {{ meals.Ordinary[1]|count }} of {{ meals.Ordinary[0]|count }} ordinary entries. The punches equal the clock's times except on {{ n_differ }} entries, so they repeat the clock and do not corroborate it. **Watch for:** joining the punches unsummarized repeats the entries, {{ g.fan_entries.Surge|count }} for {{ g.meal_entries.Surge|count }}.

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

**Check:** the surge entries were rostered {{ rostered }} hours on {{ shifts|join(' and ') }} by the {{ creator_title }}, {{ lead }} days ahead, and clocked {{ clocks|join(' and ') }}, {{ clocked }} hours: {{ early }} minutes early and {{ late }} late. Roster equals clock on {{ equal.Ordinary[1]|count }} of {{ equal.Ordinary[0]|count }} ordinary entries and on {{ equal.Surge[1] }} surge entries. **Watch for:** the roster's time without its date reads as a day in the year `2000`, and the minutes run to millions (the smallest is {{ g.no_date_min|num }}); the clock-out taken as a time of day makes the late shift leave early, {{ g.tod_late[0]|num }} minutes.

**Step 4. Find the rule behind the Off Shift Clocking exceptions and apply it.** The {{ n_off }} exceptions are clock-ins at {{ off_in }} against a start of {{ off_start }}, {{ g.minutes_rule }} minutes after it, so the rule tests arrival. RuleMinutes, Timing and Flagged CTEs feed a final query that counts arrivals and departures against the rule, and the entries flagged.

```sql
    SUM(CASE WHEN t.Arrival >= (SELECT Minutes FROM RuleMinutes)
        THEN 1 ELSE 0 END) AS LateArrivals,
    SUM(CASE WHEN t.Departure > (SELECT Minutes FROM RuleMinutes)
        THEN 1 ELSE 0 END) AS LateDepartures,
```

**Check:** surge entries: {{ g.by_type.Surge[2] }} late arrivals, {{ g.by_type.Surge[3]|count }} late departures, {{ g.by_type.Surge[4] }} flagged; ordinary: {{ g.by_type.Ordinary[2] }}, {{ g.by_type.Ordinary[3]|count }} and {{ g.by_type.Ordinary[4] }}. Design failed: surge arrivals are early, and the late departures count as approved overtime that nothing compares with a roster or a plan. Operation failed: all {{ exceptions }} exceptions are Open, none reviewed, {{ wrong }} naming the wrong employee. **Watch for:** applying the rule to departures flags all {{ g.by_type.Surge[3]|count }} surge entries and reverses the finding; `>` against `>=` and an ungrouped Flagged CTE change nothing here.

### Part 3: The plans and the approvals

**Step 5. Test the calendar and the planned load.** Join SurgeDays to WorkCenterCalendar on the date. For the load, take each work center's hours once a week and compare planned load with available hours in weeks with and without surge days, through the week of {{ through }}.

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

**Check:** every surge day is a working day, {{ maintenance }} with maintenance at a work center and {{ reduced }} at reduced capacity. Load in surge weeks against other weeks:{% for y in d.years %} {{ y }}, {{ load[loop.index0][0]|num(3) }} against {{ load[loop.index0][1]|num(3) }}{{ ";" if not loop.last else "." }}{% endfor %} The surge weeks were not planned overloads. **Watch for:** three wrong versions.

- Summing every item row's hours makes the load a few hundredths of capacity ({{ g.flat_shares|min|num(3) }} to {{ g.flat_shares|max|num(3) }}).
- Without the cut-off a row for {{ g.beyond[0][0] }} appears, with {{ g.beyond[0][2] }} weeks.
- `'weekday 1'` without `'-6 days'` moves dates to the next Monday: {{ g.weekday1[0][2] }} surge weeks in {{ d.C }}, {{ g.weekday1[1][2] }} without.

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

**Check:** the {{ n_reasons }} reason codes are used {{ per_reason|count }} times each on surge days, all approved by the {{ creator_title }}. Of {{ cite.Surge.approvals|count }} surge approvals {{ cite.Surge.cited|count }} cite an operation, all ended; of {{ cite.Ordinary.approvals|count }} ordinary approvals {{ cite.Ordinary.cited|count }} cite one and {{ cite.Ordinary.ended }} had ended. **Watch for:** an `INNER JOIN` to the operations drops the approvals that cite none and reads {{ g.ap_inner[0][1]|count }} surge approvals, all citing a finished operation; `<=` counts an operation ending on the work date as ended, and all {{ g.ordinary_ended_le|count }} ordinary citations look stale.

### Part 4: The matrix

**Step 7. Grade each test for independence, and name two explanations.** Place every test in one result column and mark whether its record is independent of the {{ creator_title }} and the time clock. Attendance and punches support the hours but come from the clock; clock-in times, rosters and approvals contradict them and come from the clock or the {{ creator_title }}; the calendar, the plan and the output are outside, and none supports the hours as recorded; absences are silent. Two explanations fit: the hours were worked and entered for the plant as a block, or they were not worked as recorded. Gate logs, supervisor statements, security video, machine data and the system's own entry log would separate them.

{{ figure('IF-C3-2-A') }}

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Surge and ordinary days | {{ s.days }}; {{ o.days }} | 1 |
| Minutes early and late on surge days | {{ early }}; {{ late }} | 3 |
| Surge entries flagged by the rule | {{ g.by_type.Surge[4] }} | 4 |
| Surge approvals citing an ended operation | {{ cite.Surge.ended|count }} of {{ cite.Surge.approvals|count }} | 6 |

{{ expected() }}

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

- Count the ordinary entries that leave more than the rule's minutes late ({{ beyond|count }}) and ask why so few were flagged.
- Group the surge days by weekday and say what the pattern suggests ({{ weekdays[0][0] }} {{ weekdays[0][1] }}, {{ weekdays[-1][0] }} {{ weekdays[-1][1] }}).
- Discuss: which record would you ask for first, and from whom?
