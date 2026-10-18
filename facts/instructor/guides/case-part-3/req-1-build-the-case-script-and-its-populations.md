---
note: case3.r1
uses: [case3.g1, case3.chapter]
title: Build the case script and its populations (Chapters 9 and 10)
kind: requirement
number: '1'
unit: case3
perspective: general
tool: sql
minutes: 120
solution: "PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 1 (the profiles, the link tests, and the views SurgeDays and PlantEntries with their reconciliation)"
figures:
  - id: IF-C3-1-A
    kind: sql-mock
    purpose: The reconciliation of the two views to Tutorial 12.3, the check students must pass before Requirement 2.
    shows: "The tab Case.sql at the reconciliation query. Columns WorkYear, SurgeDays, SurgeEntries, OrdinaryDays and OrdinaryEntries, one row for each fiscal year; the SurgeDays and SurgeEntries cells are outlined; the message pane reports three rows."
    data: The reconciliation query, run read-only.
  - id: IF-C3-1-B
    kind: sql-mock
    purpose: The dispositions of the attendance exceptions, where the misattributed rows stand out.
    shows: "The tab Case.sql at the disposition query, its CASE expression in the editor. The grid is scrolled right so that the columns EmployeeID, EntryEmployeeID, TimeClockEntryID, ClockStatus and Disposition fit the frame (the row numbers are the AttendanceExceptionIDs); the rows whose EmployeeID differs from EntryEmployeeID are outlined, and the message pane reports 18 rows."
    data: The disposition query, run read-only.
---
{% set g = case3_g1 %}
{% set c = case3_chapter %}
# Requirement 1: Build the case script and its populations (Chapters 9 and 10)

{{ header() }}

## Purpose and learning outcomes

Every later requirement tests, measures or plans on the populations built here, so a student who skips the reconciliation builds Requirements 2 to 5 on sand. The requirement applies Chapter 9's script habits and Chapter 10's data profile to tables the chapters never queried, tests the links between them as an auditor tests a trace, and saves the surge days and the plant's clock entries as views (Chapter 11). The analytics type is descriptive, with a diagnostic edge in the link tests.

Students can:

- document a script so another person can rerun it (Part 1);
- profile a table: rows, dates, code columns, blank columns, repeated keys (Part 2);
- test a link by comparing the employee and the date on each side, and give each exception a disposition (Part 3);
- save a population as a view and reconcile it to an earlier finding (Part 4).

**Competencies practiced.** CPA Evolution BAR M10 (advanced data analytics) and ISC M4 (use and management of data); IMA Data Analytics and Insights (data tools and techniques); IFAC IES 2 (i), using information and communications technology to analyze data; AACSB A5 part 5.1 (technology integration, SQL).

## Before you assign

- **Files.** CharlesRiver_Work.sqlite, a new editor tab for `Case.sql`, and Audit.sql for test H9's CTE. Requirement 3 reads Tutorial 11.3's view; a student without it runs Setup_Part3_Views.sql once and selects **Write Changes**.
- **Data conditions.** TimeClockPunch has no index on TimeClockEntryID, so a correlated test scans {{ punches|count }} punches for every entry, and each entry has {{ g.per_entry[0] }} to {{ g.per_entry[1] }} punches, so a join that does not summarize repeats entries. The calendar has one row for each work center and date. The plant has {{ g.hourly }} hourly employees in a cost center of {{ g.cost_center_staff }}: the salaried staff keep no time clock.
- **Builds on.** Chapter 9's script habits, Chapter 10's data profile (Tutorial 10.3) and Chapter 12's Tutorial 12.3 (test H9); their guides hold the detail.
- **Verify first.** The reconciliation returns {{ g.n.reconcile|count }} rows, one for each fiscal year.

## How to run it

Pairs, about 120 minutes: 10 for the header, 35 for the profiles, 35 for the link tests, 40 for the views and the reconciliation. The routine for every step: type the two comment lines and the query at the end of the script, select it, click **Execute all/selected SQL** and read the message pane. Hold back the disposition CASE until a pair has run the link tests, and SurgeDays until they have looked for it in test H9. **Collect** Case.sql with both views created.

## Step-by-step solution

### Part 1: The header and the comments

**Step 1. Write the header, then two comment lines above every query.** The header names the purpose, the database file, the preparer and date, and the checks, as Audit.sql's does. The first comment line says what the query tests; the second gives its population and the result expected, so a reviewer sees whether the run agrees.

**Check:** no query lacks its two lines. The model script has {{ c.n_queries }} queries, {{ c.per_req[1] }} of them for this requirement.

### Part 2: The profiles

**Step 2. Profile TimeClockPunch.** One row of counts, the date range, and a `COUNT` of each column that may be blank.

```sql
-- Requirement 1: profile of TimeClockPunch, its rows, dates, and columns not always filled in
-- Population: every punch; expected: 165,137 punches of 76 employees, 2024-01-01 to 2026-12-11
SELECT COUNT(*) AS Punches,
    COUNT(DISTINCT EmployeeID) AS Employees,
    COUNT(DISTINCT TimeClockEntryID) AS ClockEntries,
    MIN(WorkDate) AS FirstDate,
    MAX(WorkDate) AS LastDate,
    COUNT(EmployeeShiftRosterID) AS WithRoster,
    COUNT(WorkCenterID) AS WithWorkCenter
FROM TimeClockPunch;
```

**Check:** {{ punches|count }} punches of {{ punch_employees }} employees, {{ punch_first }} to {{ punch_last }}; WithRoster reads {{ g.profile[5]|count }}, so {{ g.detached }} punches have no roster, and WithWorkCenter {{ g.profile[6]|count }}. **Watch for:** two wrong versions.

- `COUNT(*)` where `COUNT(EmployeeShiftRosterID)` belongs reports the roster as complete: count each column by name, or the blanks never appear.
- Profiling the calendar by its date alone reads {{ g.cal_dates|count }} dates in {{ g.cal[0]|count }} rows and looks like duplicates. The key is the work center and the date; the model counts the pair with `||` and gets {{ g.cal[4]|count }}.

**Step 3. Profile the other three tables the same way.** Roster: employees rostered twice on one date. Exceptions: group by type, severity and status, and count the reviewer and the review date. Calendar: group by exception reason and day type, and total the working days and available hours of {{ d.C }}.

**Check:** see Expected results. The exceptions are {{ exceptions }} in {{ exc_types|length }} types, {{ per_type }} of each, all Open, with no reviewer and no review date (WithReviewDate is zero, as Reviewed is, though a missing reviewer and a missing review date are different gaps).

### Part 3: The links

**Step 4. Test each punch against its clock entry, and each clock entry against its roster.**

```sql
-- Requirement 1: punches whose employee or date differs from their clock entry's
-- Population: every punch; expected: 18 punches of 6 entries, all dated differently
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
```

**Check:** {{ g.links_punch_entries }} rows: {{ shifted_word }} clock entries ({{ shifted_entries|join(', ') }}), {{ shifted_punches }} punches, all dated differently, none for another employee. A `LEFT JOIN` from the clock entries to their rosters, comparing employee and date, returns the same {{ g.roster_off }} entries, and the punches whose roster link is blank or differs return {{ g.detached }} clock-ins of employee {{ detached_employee }}, one on each January 1. **Watch for:** comparing only the employee finds nothing ({{ g.employee_only }} punches differ, against {{ g.date_only }} by date), and the link looks clean. An `INNER JOIN` to the rosters would also drop an entry with no roster; none is missing here, so check the habit, not the result.

**Step 5. Link each attendance exception to its clock entry and assign a disposition.** A left join keeps an exception with no entry, and the CASE assigns the disposition in the order of its tests.

```sql
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
```

{{ figure('IF-C3-1-B') }}

**Check:** {{ g.n.dispositions }} rows:{% for label, n in g.disp %} {{ label }}, {{ n }}{{ ";" if not loop.last else "." }}{% endfor %} Exceptions {{ wrong_ids|join(', ') }} name employee {{ wrong_named }} on entries that belong to employee {{ wrong_owner }}, so the exception report misattributes its own rows. No exception carries another date than its entry, so the date test returns none, and the order of the employee and Pending tests does not change a count, because no exception is both. The isolated rows are logged and not pursued, which does not clear them.

### Part 4: The views

**Step 6. Save SurgeDays and PlantEntries.** SurgeDays is test H9's CTE as a view; PlantEntries has one row for each hourly manufacturing clock entry and a DayType of Surge or Ordinary.

```sql
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
```

```sql
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
```

**Check:** no result grid; select **Write Changes** so the views stay in the working copy. PlantEntries holds {{ g.entries|count }} entries. **Watch for:** three wrong versions.

- Without the Manufacturing filter SurgeDays is empty ({{ g.no_mfg }} days): across the company the hours are never one pattern.
- An `INNER JOIN` to SurgeDays leaves {{ g.inner|count }} entries, all surge, so Requirement 2 has no ordinary days.
- A second run without `DROP VIEW IF EXISTS` fails with "{{ g.again }}". The `PayClass` filter and the test for more than one employee remove nothing here. Keep them, because they state who the plant is, and count employees rather than rows, as H9 does, so two entries of one person cannot make a surge day.

**Step 7. Reconcile the views to Tutorial 12.3.**

```sql
-- Requirement 1: the two views reconciled to the surge days and entries of Tutorial 12.3
-- Population: SurgeDays and PlantEntries; expected: 12, 32, 49 surge days and 768, 2,048, 3,136 surge entries
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
```

{{ figure('IF-C3-1-A') }}

**Check:** three rows (year, surge days, surge entries, ordinary days, ordinary entries):{% for r in g.reconcile %} {{ r[0] }}, {{ r[1] }}, {{ r[2]|count }}, {{ r[3] }}, {{ r[4]|count }}{{ ";" if not loop.last else "." }}{% endfor %} The surge figures are those of Tutorial 12.3's test H8, and a count against Employee shows that each surge day holds one entry for each of the {{ g.hourly }} hourly employees.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Clock entries with punches; roster links blank | {{ g.profile[2]|count }}; {{ g.detached }} | 2 |
| Rosters; managers who created them | {{ rosters|count }}; {{ creators|length }} | 3 |
| Exceptions; entries they sit on | {{ exceptions }}; {{ g.exception_entries }} | 3 |
| Calendar rows; work centers; dates | {{ g.cal[0]|count }}; {{ g.cal[1] }}; {{ g.cal_dates|count }} | 3 |
| Working days and available hours of {{ d.C }} | {{ working }}; {{ avail|num(2) }} | 3 |
| Punches dated differently; entries | {{ shifted_punches }}; {{ g.links_punch_entries }} | 4 |
| Surge days; surge entries; plant entries | {{ surge_days|join(', ') }}; {{ surge_entries|map('count')|join(', ') }}; {{ g.entries|count }} | 6, 7 |

{{ expected() }}

## What a strong answer says

- **Documentation.** A header with purpose, file, preparer, date and checks, and a population and expected result above every query, so the script reruns without its author.
- **Profiles.** Each blank column counted by name, each key tested whole, each code column listed with its values.
- **Links.** The employee and the date compared on each side, the exceptions dispositioned by rule, and the detached punches named, not hidden by an inner join.
- **Views.** One definition of the population, traceable to test H9, reconciled to Tutorial 12.3 before any test relies on it.

A strong script separates what needs follow-up (the exceptions on Pending entries, the misattributed rows) from what only needs a record. A weak one lists counts and moves on.

## Common mistakes and how to respond

- **Counting rows where a column belongs.** *Symptom:* a profile with no blanks. *Response:* ask which columns the later tests need, and how many are filled in.
- **Calling the calendar a table of duplicates.** *Symptom:* {{ g.cal_dates|count }} dates in {{ g.cal[0]|count }} rows. *Response:* ask what identifies a row of this table.
- **Comparing only the employee.** *Symptom:* every link passes. *Response:* ask what else a punch records that its entry also records.
- **An empty SurgeDays view or an inner join to it.** *Symptom:* {{ g.no_mfg }} surge days, or {{ g.inner|count }} entries. *Response:* ask whose hours form the pattern, and what an ordinary day is in the join.
- **Views lost between sessions.** *Symptom:* "no such table: SurgeDays" the next day. *Response:* ask whether **Write Changes** was selected.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Header and comments | 10 | Header complete; two-line comment on every query | Header without checks, or some comments missing |
| Profiles | 25 | All four tables; blanks counted by column; keys tested whole | Counts without blanks or keys |
| Link tests | 25 | Employee and date compared; dispositions by rule; misattribution found | Dates only, or no dispositions |
| Views | 25 | Both views correct, DROP before CREATE, written to the copy | One view, or a filter missing |
| Reconciliation | 15 | Agrees with Tutorial 12.3, by year | Run but not compared |

## Extensions and discussion questions

- Find the clock entries that carry two or more exceptions ({{ g.multi|length }} entries, {{ g.multi_total }} exceptions) and say what the pattern suggests about how the exceptions were raised.
- Write the same link test from OvertimeApproval to its clock entry, and say what a break would mean for Requirement 2.
- Discuss: "Isolated: logged, not pursued in this case" is a decision to stop looking. What would you want to know before you closed such an item for a real company?
- Discuss: what must a reviewer see in Case.sql before they trust a number in the memo?
