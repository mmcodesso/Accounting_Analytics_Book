---
note: ch09.ex6
uses: [ch09.g6]
title: Missing Values in Time and Labor Records
kind: exercise
number: '9.6'
unit: '9'
perspective: auditing
tool: sql
minutes: 60
solution: "Chapter09-exercises-sql.zip: Ex 9.6.sql"
figures:
  - id: IF-09-6-A
    kind: sql-mock
    purpose: The time clock entries with no clock-out, shown with the COALESCE label that makes the gap visible.
    shows: "The Execute SQL tab on the tab Ex 9.6.sql. The editor holds the comment lines and the query of Step 5 with COALESCE(ClockOutTime, 'missing') AS ClockOut and ClockOutTime IS NULL. The grid shows the entries with TimeClockEntryID, EmployeeID, WorkDate, ClockInTime, ClockOut, RegularHours, OvertimeHours and ClockStatus, with the word missing in the ClockOut column outlined and Pending in the last column. The message pane reports the number of rows returned."
    data: TimeClockEntry, the Step 5 query, run read-only on the dataset (the Expected results give the entries).
---
{% set g = ch09_g6 %}
# Exercise 9.6: Missing Values in Time and Labor Records

{{ header() }}

## Purpose and learning outcomes

The manufacturing variance depends on the labor time recorded against work orders, so the audit senior wants the time records tested for missing values before anyone relies on them. This is the chapter's In Practice idea as an audit procedure: a missing value can be the sign of a step that did not happen, or of one that happened without being recorded. The exercise teaches two cautions. A NULL means different things in different populations, so the test must be scoped. And IS NULL finds only the keys that are blank, not the ones that point nowhere. The analytics type is descriptive.

By the end, students can:

- write IS NULL and IS NOT NULL tests, and label a missing value with COALESCE (outcomes 2 and 4);
- scope a test to the right population and group OR conditions inside an AND (outcome 3);
- separate a missing value from a related status, such as Pending (outcome 4);
- explain why each finding matters for the labor and payroll records, say whether the tests show an effect on manufacturing cost, and put a question to payroll or production (outcome 6).

**Competencies practiced.** CPA Evolution ISC M4 and Core S1 M8 T2 (use and management of data; financial data cleansing); IMA Data Analytics and Insights (data governance, data literacy); IFAC IES 2 (f) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** CharlesRiver_Work.sqlite and a script `Ex 9.6.sql`.
- **Data conditions.** LaborTimeEntry.LaborType is Direct Manufacturing, Indirect Manufacturing or NonManufacturing, and WorkOrderOperationID is blank on every row of the last two, because no routing step applies to indirect or non-manufacturing time. A blank ClockOutTime in TimeClockEntry is NULL, not empty text. An employee with a TerminationDate has an EmploymentStatus and an IsActive flag.
- **Verify first.** `SELECT DISTINCT LaborType FROM LaborTimeEntry;` returns three values.

## How to run it

Individual, about 60 minutes: 15 for requirement (1), 20 for (2), 10 for (3) and 15 for (4). The routine of Exercise 9.1 applies: type the comment lines and query at the end of the script, select it, click **Execute all/selected SQL** and read the message pane. Hold back the scoping hint until a student's list in (1) is far longer than expected. Collect the script and the findings.

## Step-by-step solution

### Requirement (1): Direct labor with no operation

**Step 1. List the direct labor rows with no operation.**

```sql
-- Requirement (1): direct labor time with no work order operation
-- Population: LaborTimeEntry, Direct Manufacturing; expected: three rows (213, 26171, 48261)
SELECT LaborTimeEntryID, EmployeeID, WorkOrderID, WorkDate,
    RegularHours, OvertimeHours,
    RegularHours + OvertimeHours AS Hours
FROM LaborTimeEntry
WHERE LaborType = 'Direct Manufacturing'
    AND WorkOrderOperationID IS NULL
ORDER BY LaborTimeEntryID;
```

**Check:** {{ g.direct }} rows, one a year. **Watch for:** without the LaborType condition the test returns {{ g.unfiltered|count }} rows, because {{ g.indirect|count }} indirect and {{ g.nonmfg|count }} non-manufacturing entries have no operation by design. `'Direct'` returns no rows, and `= NULL` returns none. The test also misses direct rows whose operation key points at no operation: {{ g.orphans }} exist, and a join finds them in Chapter 10.

**Step 2. Look up the employees.** Steps 2 and 6 are lookups that support the findings.

```sql
-- Requirement (1): the employees on those rows
-- Population: Employee; expected: 17, 18, assemblers
SELECT EmployeeID, EmployeeName, JobTitle, CostCenterID
FROM Employee
WHERE EmployeeID IN (17, 18);
```

**Check:** 2 rows, both {{ title }}. Students copy the IDs from Step 1.

### Requirement (2): The time clock

**Step 3. List the clock statuses.**

```sql
-- Requirement (2): the values of ClockStatus
-- Population: TimeClockEntry; expected: Approved and Pending
SELECT DISTINCT ClockStatus
FROM TimeClockEntry
ORDER BY ClockStatus;
```

**Check:** 2 rows, Approved and Pending.

**Step 4. Count each status.** The message pane gives each count.

```sql
-- Requirement (2): the time clock entries with ClockStatus Approved (count in the message pane)
-- Population: TimeClockEntry; expected: 52,962 entries
SELECT TimeClockEntryID, EmployeeID, WorkDate, ClockStatus
FROM TimeClockEntry
WHERE ClockStatus = 'Approved';
```

```sql
-- Requirement (2): the time clock entries with ClockStatus Pending (count in the message pane)
-- Population: TimeClockEntry; expected: 5 entries
SELECT TimeClockEntryID, EmployeeID, WorkDate, ClockStatus
FROM TimeClockEntry
WHERE ClockStatus = 'Pending';
```

**Check:** {{ clock[0][1]|count }} Approved and {{ clock[1][1] }} Pending.

**Step 5. List the entries with no clock-out.**

```sql
-- Requirement (2): time clock entries with no ClockOutTime
-- Population: TimeClockEntry, ClockOutTime NULL; expected: 3 entries, employee 85, Pending
SELECT TimeClockEntryID, EmployeeID, WorkDate, ClockInTime,
    COALESCE(ClockOutTime, 'missing') AS ClockOut,
    RegularHours, OvertimeHours, ClockStatus
FROM TimeClockEntry
WHERE ClockOutTime IS NULL
ORDER BY WorkDate;
```

{{ figure('IF-09-6-A') }}

**Check:** {{ g.missing }} rows, all employee {{ clock_employee }}, one on the first day of each fiscal year, all Pending, each with {{ g.hours[0] }} to {{ g.hours[1] }} hours recorded and the word missing in ClockOut. **Watch for:** `= NULL` and `= ''` both return no rows. Pending is a related test, not the same one: {{ g.pending }} entries are Pending, and {{ g.pending_out }} of them have a clock-out.

**Step 6. Look up that employee.**

```sql
-- Requirement (2): employee 85
-- Population: Employee; expected: an Inventory Specialist
SELECT EmployeeID, EmployeeName, JobTitle, EmploymentStatus,
    TerminationDate
FROM Employee
WHERE EmployeeID = 85;
```

**Check:** 1 row, {{ clock_title }}, terminated {{ g.emp_term }}. {{ g.after }} of the {{ g.missing }} entries are dated after that day.

### Requirement (3): Terminated employees

**Step 7. List the employees with a TerminationDate.**

```sql
-- Requirement (3): employees with a TerminationDate
-- Population: Employee, TerminationDate not NULL; expected: 13 employees, all Terminated and inactive
SELECT EmployeeID, EmployeeName, TerminationDate,
    EmploymentStatus, IsActive
FROM Employee
WHERE TerminationDate IS NOT NULL
ORDER BY TerminationDate;
```

**Check:** {{ g.n_term }} rows, every one Terminated and IsActive 0.

**Step 8. Test the other direction.** Is anyone Terminated or inactive without a date?

```sql
-- Requirement (3): employees without a TerminationDate who are Terminated or inactive
-- Population: Employee, TerminationDate NULL; expected: no rows
SELECT EmployeeID, EmployeeName, EmploymentStatus, IsActive
FROM Employee
WHERE TerminationDate IS NULL
    AND (EmploymentStatus = 'Terminated' OR IsActive = 0);
```

**Check:** 0 rows, so the three columns agree. **Watch for:** without the parentheses the test returns {{ g.wrong }} rows, the terminated employees themselves, as if the columns disagreed.

### Requirement (4): Findings and questions

**Step 9. Write the findings.** See "What a strong answer says".

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Direct labor rows with no operation | {{ g.direct }} | 1 |
| Their entries and employees | {% for r in labor %}{{ r.id }} (employee {{ r.employee }}, {{ r.date }}, {{ r.hours }} hours){{ "; " if not loop.last else "" }}{% endfor %} | 1 |
| Clock statuses | Approved {{ clock[0][1]|count }}; Pending {{ clock[1][1] }} | 4 |
| Entries with no clock-out, and the employee | {{ g.missing }}; employee {{ clock_employee }}, {{ g.after }} after the termination date {{ g.emp_term }} | 5, 6 |
| Employees with a TerminationDate, and rows that disagree | {{ g.n_term }}; 0 | 7, 8 |

{{ expected() }}

## What a strong answer says

- **Finding 1.** The direct rows with no operation are charged to their work orders, whose closes count them in actual direct labor, so they reach the variance (a cross-table fact the model answer states, beyond this chapter's queries). They cannot be traced to a routing step, so an operation-level comparison leaves them out, and the missing link does not show that the hours are wrong. Ask production which operation each belongs to, and why the system accepted direct time without one. A strong answer adds that IS NULL finds only blank keys.
- **Finding 2.** The entries with no clock-out are Pending, yet each records hours, and some fall after the employee's termination. Hours without a complete record cannot be verified. Their linked labor records are non-manufacturing, with no work order, so the tests show a gap in the time and payroll support, not an effect on manufacturing cost, which would first need a trace of any allocation. Ask payroll who entered them, on what support, and whether and to whom they were paid. Chapter 12 tests it.
- **Finding 3.** The three termination columns agree. A strong answer notes that this is the master table agreeing with itself, and asks payroll to confirm that no time or pay was recorded after each date, as Step 6 shows for one employee.

A weak answer reports the counts without a consequence or a question, calls Pending a missing value, or says the missing clock-outs raised the manufacturing variance.

## Common mistakes and how to respond

- **No LaborType condition.** *Symptom:* {{ g.unfiltered|count }} rows. *Response:* ask what a blank operation means for indirect time.
- **`= NULL`, or `'Direct'`.** *Symptom:* no rows. *Response:* run DISTINCT on LaborType, and ask what a comparison with a missing value returns.
- **Pending read as a missing clock-out.** *Symptom:* {{ g.pending }} entries in the finding. *Response:* ask the student to run the clock-out test alone.
- **No parentheses in Step 8.** *Symptom:* {{ g.wrong }} rows and a claim that the columns disagree. *Response:* ask which condition the AND covers.
- **"The columns agree, so there is no problem."** *Response:* ask what the Employee table says about the time table.
- **Findings with no question.** *Response:* ask who could resolve each one.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: direct rows with no operation | 25 | Scoped test, the rows and their employees | Unscoped list |
| Requirement 2: clock status and clock-outs | 25 | DISTINCT, counts, IS NULL with COALESCE, Pending kept apart | Missing clock-outs only |
| Requirement 3: terminated employees | 20 | Both directions of the consistency test, grouped correctly | One direction |
| Requirement 4: findings and questions | 30 | Each finding with what it shows about the records, whether an effect on manufacturing cost is shown or only possible, and a question for the right team | Findings without questions |

## Extensions and discussion questions

- In Chapter 10, find the direct rows whose operation key matches nothing, with an anti-join.
- Chapter 12 tests time and pay recorded after termination. What would you expect it to find, given Step 6?
- Discuss: should payroll be blocked when a clock-out is missing, and who should approve an exception?
- Discuss: a test finds three rows among many records. Is that a control failure or noise?
