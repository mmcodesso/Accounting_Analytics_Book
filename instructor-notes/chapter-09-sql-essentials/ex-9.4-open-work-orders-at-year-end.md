# Exercise 9.4: Open Work Orders at Year-End

| | |
|---|---|
| Unit | Chapter 9: SQL Essentials for Accounting Analytics |
| Item | Exercise 9.4 |
| Perspective | Managerial accounting |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 75 minutes |
| Solution file | Chapter09-exercises-sql.zip: Ex 9.4.sql |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A work order's variance reaches the ledger only when it closes, so the production manager and the controller want to know what is still open at year-end, in what state and how late. The exercise is the chapter's missing-value lesson in a plant setting. It practices IS NULL, COALESCE, SUBSTR with CAST, DISTINCT and a date comparison, and it ends on a judgment: a status is a claim in a table, not proof of what happened on the floor. The analytics type is descriptive.

By the end, students can:

- find open records with IS NULL and explain why `= NULL` returns nothing (outcome 4);
- take a year out of a document number with SUBSTR and CAST, and label a missing date with COALESCE (outcome 2);
- compare dates stored as text, and sort to find the oldest item (outcomes 3 and 5);
- say why the variance of open work orders is not in the year's results, and what the status cannot show (outcome 6).

**Competencies practiced.** CPA Evolution BAR M5 and ISC M4 (cost accounting; use and management of data); IMA Reporting and Control (cost accounting) and Business Acumen and Operations (operational knowledge); IFAC IES 2 (b) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** CharlesRiver_Work.sqlite and a script `Ex 9.4.sql`.
- **Data conditions.** WorkOrder.ClosedDate is NULL, not empty text, on the open work orders. WorkOrderNumber carries the year of release in characters 4 to 7. Status is Released, In Progress, Completed or Closed, and the Closed ones have a ClosedDate. Among the open work orders, CompletedDate is filled only on the Completed ones.
- **Verify first.** `SELECT * FROM WorkOrder;` returns 13,668 rows, of which 670 are open.

## How to run it

Individual, about 75 minutes: 10 for requirements (1) and (2), 15 for (3), 15 for (4) and (5), and 30 for the memo and the discussion of what Released means. The routine of Exercise 9.1 applies: type the comment lines and query at the end of the script, select it, click **Execute all/selected SQL** and read the message pane. Hold back the point that Released does not prove "not started" until students have the list for (5). Collect the script and the memo.

## Step-by-step solution

### Requirement (1): The open work orders

**Step 1. List the work orders with no ClosedDate.**

```sql
-- Requirement (1): the work orders with no ClosedDate
-- Population: WorkOrder, ClosedDate NULL; expected: 670 work orders (Released 558, In Progress 27, Completed 85)
SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
    CompletedDate, PlannedQuantity
FROM WorkOrder
WHERE ClosedDate IS NULL;
```

**Check:** 670 rows, with CompletedDate empty on most. **Watch for:** `ClosedDate = NULL` returns 0 rows and no error, an empty result that looks like a finding.

### Requirement (2): The release year and a label

**Step 2. Add the year and the completion label.**

```sql
-- Requirement (2): the release year and the completion date or a label
-- Population: as (1); expected: every release year 2026, not completed on 585 work orders
SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
    COALESCE(CompletedDate, 'not completed') AS Completed,
    PlannedQuantity,
    CAST(SUBSTR(WorkOrderNumber, 4, 4) AS INTEGER) AS ReleaseYear
FROM WorkOrder
WHERE ClosedDate IS NULL;
```

**Check:** 670 rows. ReleaseYear is 2026 on every row, the dates run from 2026-05-23 to 2026-12-31, and Completed reads not completed on 585 rows and shows a date on the others. **Watch for:** a filter `SUBSTR(WorkOrderNumber, 4, 4) = 2026` returns 0 rows, because SUBSTR returns text and no side is converted. With the year in quotes it returns 670, and CAST gives the same.

### Requirement (3): The statuses

**Step 3. List the statuses.**

```sql
-- Requirement (3): the statuses of the open work orders
-- Population: as (1); expected: Released, In Progress, Completed
SELECT DISTINCT Status
FROM WorkOrder
WHERE ClosedDate IS NULL;
```

**Check:** 3 rows: Released, In Progress and Completed. A Completed work order has a CompletedDate and no ClosedDate.

**Step 4. Count each status.** The message pane gives each count.

a. Type and run the three queries below, one at a time.
b. Read "Result: N rows returned" for each.

```sql
-- Requirement (3): the open work orders with Status Released (count in the message pane)
-- Population: as (1); expected: 558 work orders
SELECT WorkOrderNumber, Status, ReleasedDate, DueDate
FROM WorkOrder
WHERE ClosedDate IS NULL AND Status = 'Released';
```

```sql
-- Requirement (3): the open work orders with Status In Progress (count in the message pane)
-- Population: as (1); expected: 27 work orders
SELECT WorkOrderNumber, Status, ReleasedDate, DueDate
FROM WorkOrder
WHERE ClosedDate IS NULL AND Status = 'In Progress';
```

```sql
-- Requirement (3): the open work orders with Status Completed (count in the message pane)
-- Population: as (1); expected: 85 work orders
SELECT WorkOrderNumber, Status, ReleasedDate, DueDate
FROM WorkOrder
WHERE ClosedDate IS NULL AND Status = 'Completed';
```

**Check:** 558, 27 and 85 rows, 670 in all. **Watch for:** `'In progress'` with a small p returns 0 rows.

### Requirement (4): The past-due work orders

**Step 5. List those due on or before the last day of the year.**

```sql
-- Requirement (4): the open work orders due on or before 2026-12-31
-- Population: as (1); expected: 471 work orders, the oldest WO-2026-011512
SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
    COALESCE(CompletedDate, 'not completed') AS Completed
FROM WorkOrder
WHERE ClosedDate IS NULL AND DueDate <= '2026-12-31'
ORDER BY DueDate, WorkOrderNumber;
```

![A mock of the oldest past-due work orders that are still marked Released, for the discussion of what a status proves.](../figures/chapter-09-sql-essentials/IF-09-4-A.pdf)

**Check:** 471 rows; the oldest is WO-2026-011512, released 2026-05-23 and due 2026-06-07, then WO-2026-011742 (due 2026-06-21) and WO-2026-012609 (due 2026-08-30). **Watch for:** `<` and `<=` return the same 471 rows here, because no open work order is due on the last day; that is a property of this data, not a rule. A date typed as `12/31/2026` returns 0 rows, because the stored dates begin with the year.

### Requirement (5): Past due and still Released

**Step 6. Keep the Released ones.**

```sql
-- Requirement (5): those still Released
-- Population: the work orders of (4); expected: 406 work orders
SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
    PlannedQuantity
FROM WorkOrder
WHERE ClosedDate IS NULL AND DueDate <= '2026-12-31'
    AND Status = 'Released'
ORDER BY DueDate, WorkOrderNumber;
```

**Check:** 406 rows, hundreds of work orders past due that the table still calls Released. Of these, 26 show material issues, completions and started operations in other tables, which Chapter 10's joins can find; the three oldest are among them.

### Requirement (6): The memo

**Step 7. Outline the memo.** See "What a strong answer says".

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Open work orders, and by status | 670; Released 558, In Progress 27, Completed 85 | 1, 4 |
| Release years, and the date range | 2026; 2026-05-23 to 2026-12-31 | 2 |
| Not completed on | 585 rows | 2 |
| Due on or before the last day, by status | 471: Released 406, Completed 64, In Progress 1 | 5 |
| Oldest | WO-2026-011512, due 2026-06-07 | 5 |
| Still Released and past due | 406 | 6 |

> **Instructor notes, Exercise 9.4:** 670 work orders have a NULL ClosedDate: Released 558, In Progress 27, Completed 85 (completed but not closed). Every WorkOrderNumber carries the year of its ReleasedDate, and every open work order is a 2026 work order (released 2026-05-23 to 2026-12-31); COALESCE shows not completed for the 585 released or in progress and a date for the 85 completed. Due on or before 2026-12-31: 471 (Released 406, Completed 64, In Progress 1). The oldest is WO-2026-011512, released 2026-05-23 and due 2026-06-07, still Released at the end of the data; the next are WO-2026-011742 (due 2026-06-21) and WO-2026-012609 (due 2026-08-30). Hundreds of work orders are past due and still Released, but the status is not proof that work has not started: 26 of the 406 have material issues, production completions, and started operations in other tables (23 also labor time), including the three named above, which a cross-table check beyond this chapter's single-table queries finds (Chapter 10's joins can show it). The statuses need reconciling with production; for the others, the absence of recorded activity in the extract is not proof that nothing happened. Any variance on the open work orders will be recorded when they close, after the data ends, and the open status alone does not say how large it will be. Counting needs one query per status (COUNT comes in Chapter 10).

## What a strong answer says

- **Requirement (2).** Every open work order was released in the current year, so nothing from earlier years is open, and COALESCE separates the work that was never completed from the work that was completed and not closed.
- **Requirement (5).** Hundreds of work orders are past due and still Released. A strong answer treats the status as unreliable, not as a fact: some of them show activity in other tables, so production should reconcile the statuses. For the others, no recorded activity does not prove that nothing happened.
- **Requirement (6).** The counts by status and the late ones, the oldest named, and the accounting: the variance is recorded when the WorkOrderClose document posts the difference between actual and standard cost to 5080. Until then the costs sit in work in process and 1090, so any variance on these work orders is not in the year's results, and the open status does not say how large it will be. The completed work orders should be closed.

A weak memo says that no work has started on the Released orders, or leaves out why the year's variance is understated.

## Common mistakes and how to respond

- **`= NULL`.** *Symptom:* 0 rows. *Response:* ask what a comparison with a missing value returns.
- **The year compared as a number.** *Symptom:* 0 rows where 670 are expected. *Response:* ask what type SUBSTR returns.
- **A status typed from memory.** *Symptom:* no rows for `'In progress'`. *Response:* run DISTINCT and copy the value.
- **A date in another form.** *Symptom:* 0 rows. *Response:* ask how the dates are stored.
- **Counting by scrolling.** *Symptom:* a count that does not match the pane. *Response:* use the message pane.
- **Released read as not started.** *Symptom:* a memo that calls the 406 work orders idle. *Response:* ask what other tables would show if work had started.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: open list | 10 | IS NULL, columns as asked | `= NULL` shown and corrected |
| Requirement 2: functions | 15 | SUBSTR with CAST, COALESCE, both read correctly | One function |
| Requirement 3: statuses and counts | 15 | DISTINCT and three counts from the pane | Counts without DISTINCT |
| Requirement 4: past due | 15 | Date test, sorted, oldest named | Unsorted |
| Requirement 5: still Released | 15 | List and the caution about the status | List only |
| Requirement 6: memo | 30 | Counts, lateness, status caveat and why the variance is not yet recorded | Counts only |

## Extensions and discussion questions

- In Chapter 10, join the Released work orders to MaterialIssue and ProductionCompletion to find the ones with activity.
- Discuss: who should clean up stale statuses, and how often should the test be rerun?
- Discuss: how would you estimate the variance on work orders that are still open, and what evidence would support it?
