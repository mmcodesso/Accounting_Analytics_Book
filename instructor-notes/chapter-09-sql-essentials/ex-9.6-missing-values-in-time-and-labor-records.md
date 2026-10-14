# Exercise 9.6: Missing Values in Time and Labor Records

| | |
|---|---|
| Unit | Chapter 9: SQL Essentials for Accounting Analytics |
| Item | Exercise 9.6 |
| Perspective | Auditing |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 60 minutes |
| Solution file | Chapter09-exercises-sql.zip: Ex 9.6.sql |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The manufacturing variance depends on the labor time recorded against work orders, so the audit senior wants the time records tested for missing values before anyone relies on them. This is the chapter's In Practice idea as an audit procedure: a missing value can be the sign of a step that did not happen. The exercise teaches two cautions. A NULL means different things in different populations, so the test must be scoped. And IS NULL finds only the keys that are blank, not the ones that point nowhere. The analytics type is descriptive.

By the end, students can:

- write IS NULL and IS NOT NULL tests, and label a missing value with COALESCE (outcomes 2 and 4);
- scope a test to the right population and group OR conditions inside an AND (outcome 3);
- separate a missing value from a related status, such as Pending (outcome 4);
- explain why each finding matters for labor cost and put a question to payroll or production (outcome 6).

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

**Check:** 3 rows, one a year. **Watch for:** without the LaborType condition the test returns 17,745 rows, because 11,702 indirect and 6,040 non-manufacturing entries have no operation by design. `'Direct'` returns no rows, and `= NULL` returns none. The test also misses direct rows whose operation key points at no operation: 17 exist, and a join finds them in Chapter 10.

**Step 2. Look up the employees.** Steps 2 and 6 are lookups that support the findings.

```sql
-- Requirement (1): the employees on those rows
-- Population: Employee; expected: 17, 18, assemblers
SELECT EmployeeID, EmployeeName, JobTitle, CostCenterID
FROM Employee
WHERE EmployeeID IN (17, 18);
```

**Check:** 2 rows, both assemblers. Students copy the IDs from Step 1.

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

**Check:** 52,962 Approved and 5 Pending.

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

![A mock of the time clock entries with no clock-out, shown with the COALESCE label that makes the gap visible.](../figures/chapter-09-sql-essentials/IF-09-6-A.pdf)

**Check:** 3 rows, all employee 85, one on the first day of each fiscal year, all Pending, each with 8.64 to 9.1 hours recorded and the word missing in ClockOut. **Watch for:** `= NULL` and `= ''` both return no rows. Pending is a related test, not the same one: 5 entries are Pending, and 2 of them have a clock-out.

**Step 6. Look up that employee.**

```sql
-- Requirement (2): employee 85
-- Population: Employee; expected: an Inventory Specialist
SELECT EmployeeID, EmployeeName, JobTitle, EmploymentStatus,
    TerminationDate
FROM Employee
WHERE EmployeeID = 85;
```

**Check:** 1 row, an Inventory Specialist, terminated 2024-09-13. 2 of the 3 entries are dated after that day.

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

**Check:** 13 rows, every one Terminated and IsActive 0.

**Step 8. Test the other direction.** Is anyone Terminated or inactive without a date?

```sql
-- Requirement (3): employees without a TerminationDate who are Terminated or inactive
-- Population: Employee, TerminationDate NULL; expected: no rows
SELECT EmployeeID, EmployeeName, EmploymentStatus, IsActive
FROM Employee
WHERE TerminationDate IS NULL
    AND (EmploymentStatus = 'Terminated' OR IsActive = 0);
```

**Check:** 0 rows, so the three columns agree. **Watch for:** without the parentheses the test returns 13 rows, the terminated employees themselves, as if the columns disagreed.

### Requirement (4): Findings and questions

**Step 9. Write the findings.** See "What a strong answer says".

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Direct labor rows with no operation | 3 | 1 |
| Their entries and employees | 213 (employee 17, 2024-01-17, 3.74 hours); 26171 (employee 17, 2025-01-02, 1.55 hours); 48261 (employee 18, 2026-01-02, 0.5 hours) | 1 |
| Clock statuses | Approved 52,962; Pending 5 | 4 |
| Entries with no clock-out, and the employee | 3; employee 85, 2 after the termination date 2024-09-13 | 5, 6 |
| Employees with a TerminationDate, and rows that disagree | 13; 0 | 7, 8 |

> **Instructor notes, Exercise 9.6:** three Direct Manufacturing labor rows have no WorkOrderOperationID: LaborTimeEntryIDs 213 (employee 17, work order 1, 2024-01-17, 3.74 hours), 26171 (employee 17, work order 5328, 2025-01-02, 1.55 hours), and 48261 (employee 18, work order 9897, 2026-01-02, 0.50 hours); employees 17 and 18 are assemblers. They are planted anomalies (invalid direct labor operation link). ClockStatus values: Approved (52,962) and Pending (5). Three entries have no ClockOutTime, all for employee 85 (an Inventory Specialist) on January 1 of 2024, 2025, and 2026, with Pending status (planted missing clock-out). Thirteen employees have a TerminationDate; all are Terminated with IsActive 0, so the three columns agree. Missing links mean labor cost that cannot be traced to an operation; missing clock-outs mean recorded hours without a complete time record; whether they were paid is a payroll question, which Chapter 12 tests.

## What a strong answer says

- **Finding 1.** The direct rows with no operation carry cost that is charged as direct labor and cannot be traced to a routing step, so it reaches the work order's actual cost, and the variance, without a standard to compare with. Ask production which operation each belongs to, and why the system accepted direct time without one. A strong answer adds that IS NULL finds only blank keys.
- **Finding 2.** The entries with no clock-out are Pending, yet each records hours, and some fall after the employee's termination. Hours without a complete record cannot be verified, and if they were paid they reach labor cost unsupported. Ask payroll who entered them, on what support, and whether and to whom they were paid. Chapter 12 tests it.
- **Finding 3.** The three termination columns agree. A strong answer notes that this is the master table agreeing with itself, and asks payroll to confirm that no time or pay was recorded after each date, as Step 6 shows for one employee.

A weak answer reports the counts without a consequence or a question, or calls Pending a missing value.

## Common mistakes and how to respond

- **No LaborType condition.** *Symptom:* 17,745 rows. *Response:* ask what a blank operation means for indirect time.
- **`= NULL`, or `'Direct'`.** *Symptom:* no rows. *Response:* run DISTINCT on LaborType, and ask what a comparison with a missing value returns.
- **Pending read as a missing clock-out.** *Symptom:* 5 entries in the finding. *Response:* ask the student to run the clock-out test alone.
- **No parentheses in Step 8.** *Symptom:* 13 rows and a claim that the columns disagree. *Response:* ask which condition the AND covers.
- **"The columns agree, so there is no problem."** *Response:* ask what the Employee table says about the time table.
- **Findings with no question.** *Response:* ask who could resolve each one.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: direct rows with no operation | 25 | Scoped test, the rows and their employees | Unscoped list |
| Requirement 2: clock status and clock-outs | 25 | DISTINCT, counts, IS NULL with COALESCE, Pending kept apart | Missing clock-outs only |
| Requirement 3: terminated employees | 20 | Both directions of the consistency test, grouped correctly | One direction |
| Requirement 4: findings and questions | 30 | Each finding with the effect on labor cost and a question for the right team | Findings without questions |

## Extensions and discussion questions

- In Chapter 10, find the direct rows whose operation key matches nothing, with an anti-join.
- Chapter 12 tests time and pay recorded after termination. What would you expect it to find, given Step 6?
- Discuss: should payroll be blocked when a clock-out is missing, and who should approve an exception?
- Discuss: a test finds three rows among many records. Is that a control failure or noise?
