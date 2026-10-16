# Chapter 10: Joining and Summarizing Data in SQL

| | |
|---|---|
| Unit | Chapter 10: Joining and Summarizing Data in SQL |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 270 minutes of class time |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part III, Accounting Analytics with SQL: the second of four chapters. Chapter 9 queried one table at a time; this chapter combines tables and summarizes their rows |
| Analytics types | Diagnostic: joins and totals break the manufacturing variance down by product, year and part, and compare the hours recorded with the hours the standards allow. The audit exercises add the habit of testing that records match their parents |
| Tools | DB Browser for SQLite 3.13.1, reading the working copy. No query of the chapter writes to the database |
| Components | 3 guided tutorials, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 72 slides |
| Files students need | CharlesRiver_Work.sqlite, made in Tutorial 9.1. Chapter10.sql is built through the tutorials; Chapter10-companion.zip holds it at the start of Tutorials 10.2 and 10.3 and at the end. Chapter10-exercises-sql.zip holds Ex 10.1.sql to Ex 10.6.sql |
| Time | Class: about 270 minutes. Students: about 90 minutes of reading, 60 to 90 for each tutorial and 60 to 90 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- No foreign keys are declared, so a bad join raises no error; it returns more or fewer rows. Every key of Tutorial 10.1 matches: the joins return 12,998 rows, one for each close.
- The ledger reaches its documents through SourceDocumentType and SourceDocumentID, and the ID that numbers the traced sale also numbers ledger rows of 11 kinds of document.
- PurchaseRequisition has NULL approvers, so NOT IN returns 0 employees where NOT EXISTS finds 117 of 120. Two different customers share the name Brown LLC.
- The labor time records end before the year does, because the last pay periods are Open, while the completions run to the last day. Tutorial 10.3 depends on the cut-off. Indirect time ends earlier still (2026-12-04), so the tutorial calls its ratio an observed-records diagnostic.
- The exercises rest on planted conditions (ledger rows with no payroll payment, work orders without operations, labor entries whose operation key matches nothing, suppliers that share an employee's address) and on tests that are clean on purpose.

## What students should be able to do afterward

1. Join tables with INNER JOIN on their logical keys, qualify every column, and test each join by its row count. Practiced in Tutorial 10.1 (Steps 1 and 2), Exercises 10.1 (1), 10.2 (1) and (2), 10.3 (1), 10.4 (1) and (2) and 10.6 (1), and questions 1 and 2.
2. Keep unmatched rows with LEFT JOIN, find records with no match by an anti-join or NOT EXISTS, and put each condition in ON or WHERE correctly. Practiced in Tutorial 10.1 (Step 6), Tutorial 10.3 (Step 7), Exercises 10.2 (3) and 10.5 (2) to (5), and questions 4, 6, 10 and 11.
3. Summarize with aggregates, GROUP BY the key and HAVING, profile a table, and say in what order a query is evaluated. Practiced in Tutorial 10.1 (Steps 3 to 5), Tutorial 10.3 (Steps 3 and 4), Exercises 10.1 (2), 10.3, 10.4 (4), 10.5 (1) and 10.6 (3), and questions 3, 5, 7 and 12.
4. Recognize fan-out and sum each amount at its own level. Practiced in Tutorial 10.3 (Step 6), Exercise 10.6 (2) and questions 8 and 14.
5. Write scalar, IN, correlated and derived-table subqueries. Practiced in Tutorials 10.2 (Steps 1 and 3) and 10.3 (Step 6), Exercises 10.1 (4), 10.4 (2) and 10.6 (2), and questions 9 and 14.
6. Tie a summary to the ledger, rebuild the pre-closing trial balance, and compare recorded hours with standard hours. Practiced in Tutorials 10.2 and 10.3, Exercises 10.1 (3) and (4) and 10.4 (1) and (2), and questions 13 and 15. No exercise repeats the hours comparison; Chapter 11 extends it by month and work center.

## Preparing to teach

**Before the first class**

- Students need CharlesRiver_Work.sqlite from Tutorial 9.1 and DB Browser for SQLite 3.13.1, the plain edition and not the SQLCipher edition.
- Do the three tutorials yourself in order. Tutorial 10.3 depends on the pay-period lookup of Step 5 and the cut-off of Step 6.
- Open the model scripts once: each query has two comment lines and a result comment, and the notes at the end repeat the requirements and the checks.
- A late student takes Chapter10.sql from Chapter10-companion.zip, from the folder Start of Tutorial 10.2 or 10.3. Tutorial 10.1 needs only the working copy. Get the PowerPoint deck from the Downloads page; each tutorial has a checkpoint slide.
- Every query of the chapter runs in a few seconds at most, so slowness means a mistake. The exception is a correlated NOT EXISTS against LaborTimeEntry, which has no index on the operation key.

**Pitfalls that cost class time**

- **Ambiguous column.** A column in both tables of a join needs its alias; the red message pane reads ambiguous column name.
- **Nothing selected.** Running with no selection runs the whole script and shows only the last result.
- **A join on the wrong keys.** It raises no error: a close matched to the wrong work order key returns 12,485 rows instead of 12,998. The row-count test is the only alarm.
- **A condition in the wrong clause.** Moving the date test from ON to WHERE in Tutorial 10.1 Step 6 turns 88 rows into 83, with no sign in the message pane.
- **Joining the raw tables in Tutorial 10.3.** Labor time joined to the completions before summarizing asks for 366,690,316 rows, and DB Browser seems to hang. Stop it and ask what level each table is at.
- **A copy without its comment.** Tutorial 10.2 copies a query and edits it; the copy keeps its comment, or the script loses what each query tests.

## Teaching approaches

**Plan A: lecture with live demonstration (three sessions of 90 minutes, 270 minutes in all).** It fits a lecture course with time at home for the exercises. Demonstrate the steps that carry the ideas and leave the rest to students.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The controller's three questions; objectives | 2 to 5 |
| 1 | 20 | Why join; the inner join and its row-count test, live | 6 to 10 |
| 1 | 15 | Join paths; the document type in a join to the ledger | 11 to 15 |
| 1 | 25 | LEFT JOIN, anti-join, NOT IN, WHERE against ON; check | 16 to 21 |
| 1 | 20 | Aggregates, GROUP BY, group by the key | 22 to 25 |
| 2 | 10 | HAVING against WHERE; check | 26 to 29 |
| 2 | 10 | Profiling a table | 30 to 32 |
| 2 | 35 | Tutorial 10.1: Steps 1, 3, 5, 6 live; Steps 2, 4 for students | 33 to 37 |
| 2 | 20 | Fan-out; check | 38 to 42 |
| 2 | 15 | Subqueries and derived tables | 43 to 46 |
| 3 | 10 | The order in which a query runs | 47 to 49 |
| 3 | 30 | Tutorial 10.2: Steps 1, 2, 4 live; Steps 3, 5, 6 for students | 50 to 56 |
| 3 | 15 | Measuring the plant against its standards | 57 to 60 |
| 3 | 25 | Tutorial 10.3: Steps 4, 6, 7 live; Steps 1 to 3, 5 for students | 61 to 66 |
| 3 | 10 | The questions again; assign the exercises | 67 to 72 |
| | 270 | Total | |

**Plan B: lab first (two sessions of 120 minutes, 240 minutes in all, exercises as homework).** Students write the queries before they hear the vocabulary. It fits a computer lab; a pair that falls behind takes the next tutorial's start file.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Pose the three questions | 5, 9 |
| 1 | 55 | Tutorial 10.1 in pairs | 33 to 37 |
| 1 | 15 | Debrief: row counts, anti-join, WHERE against ON | 17 to 21 |
| 1 | 20 | Break it: sum GrandTotal over the join and over SalesInvoice alone | 38 to 42 |
| 1 | 20 | Subqueries and derived tables, a short lecture | 43 to 46 |
| 2 | 10 | The order in which a query runs | 47 to 49 |
| 2 | 40 | Tutorial 10.2 in pairs | 50 to 56 |
| 2 | 10 | Debrief: the ledger ties; payroll up, standard cost flat | 53, 54 |
| 2 | 10 | Measuring the plant against its standards | 57 to 60 |
| 2 | 40 | Tutorial 10.3, Steps 4 to 7 in pairs (Steps 1 to 3 at home) | 61 to 66 |
| 2 | 10 | The questions again; assign the exercises | 67 to 72 |
| | 240 | Total | |

**Plan C: flipped, with one 120-minute class.** Students read and build the tutorials at home, and the class opens with a quiz. It fits upper-level and graduate classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 15 | Quiz on questions 1, 4, 6, 8, 10 and 11 | |
| 30 | Review clinic: partners swap Chapter10.sql and agree the checkpoints, 12,998 rows, 5 items above the threshold, 71 accounts, 20 direct entries with no operation | 36, 55, 65 |
| 30 | Break it: NOT IN against the approvers, the date test in WHERE, the sum over the join, a grouping by name | 18, 19, 39, 25 |
| 35 | Start Exercise 10.2, 10.5 or 10.6 in pairs | |
| 10 | Discussion prompts 2 and 3; assign the exercises | 71 |
| 120 | Total | |

Plan A is the safest, because this chapter's stumbles are about reading a result, and a demonstration shows how. Plan B gives students ownership of the findings and needs a lab. Plan C leaves no time for demonstration and fails for students who arrive without a finished script.

![A chooser that takes a question about two or more tables to the right join or summary and to its row-count test.](../figures/chapter-10-joining-and-summarizing/IF-10-0-A.pdf)

## Tutorial guide

### Guided Tutorial 10.1: Joining the Variance to Its Work Orders and Products

**Purpose.** Students join the closes to their work orders and items, tie the year's variance by item group to the ledger, compare the years, keep the items above a threshold with HAVING, and list every manufactured item with a left join. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Steps 1, 3, 5 and 6, which carry the row-count test, the tie, HAVING and the left join. Leave Steps 2 and 4 to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | The joins, then the count of closes | 12,998 rows each time |
| 3 | The year's variance by item group, and the ledger | Furniture $1,579,134.23, Lighting $521,135.80, Textiles $165,366.85; the total is the ledger's $2,265,636.88 |
| 4 | Nine rows by group and year | Furniture from $836,103.74 to $1,579,134.23 while its closes fall from 3,150 to 2,588 |
| 5 | HAVING at two thresholds | 5 items above $50,000, then 27 above $30,000; the largest is TXT-THR-0001 |
| 6 | Every manufactured item | 88 rows, 5 with zero closes; 83 with the date in WHERE |

**Stumbles to expect**

- Step 1: a column without its alias stops with ambiguous column name; a join on the wrong keys returns 12,485 rows and no error.
- Step 3: a year taken from the work order's release date totals $1,740,602.20 over 3,337 closes and does not tie to the ledger.
- Step 6: `COUNT(*)` reads 1 for an item with no closes, where the count of the close key reads zero.

**The checkpoint to look for.** The six bullets. A strong student says that the variance is spread across most items and rises where the plant makes most while the number of work orders falls, so the question turns from products to the cost of production.

### Guided Tutorial 10.2: Building the Trial Balance and Following the Conversion Cost

**Purpose.** Students put two totals side by side with scalar subqueries, rebuild the pre-closing trial balance, check with a derived table that it nets to zero, follow account 1090 by year and source, split the conversion variance into labor and overhead, and identify the journal entries. **Time.** About 60 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (the two closes left out), Step 3 (the derived table) and Step 6 (the document type in ON). Leave Steps 1, 4 and 5 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | Closes and ledger in one row | both $2,265,636.88 |
| 2 | The pre-closing trial balance | 71 accounts, as in Chapter 6 |
| 3 | The net, then the debit balances | net $0.00; 46 accounts, $67,107,722.36 |
| 4 | Account 1090 by year and source | 12 rows; payroll debits from $2,848,551.11 to $3,815,397.14, standard cost released from $3,358,209.62 to $3,266,422.54 |
| 5 | Labor and overhead by year | labor -$290,882.15, -$167,921.70, -$14,074.81; overhead from $1,472,056.71 to $2,173,212.84 |
| 6 | Journal entries to 1090 | 6 rows: Factory Overhead and Depreciation in each year |

**Stumbles to expect**

- Step 2: with the closes left in, 46 accounts show a zero balance where 4 should, and the debit balances total $41,637,511.12; with no date condition, 526 ledger rows after the year-end change two balances.
- Step 4: a filter on the account number as if it were the AccountID returns no rows; the AccountID of 1090 is 92.
- Step 6: a join without SourceDocumentType returns 18 rows instead of 6, with entry types the plant never posts to 1090.

**The checkpoint to look for.** The six bullets. A strong student says that the two reconstructions agree and that agreement shows consistency, not completeness.

### Guided Tutorial 10.3: Comparing Output with the Hours It Took

**Purpose.** Students measure output and standard hours, the payroll's hours and pay and the people paid, profile the two tables they will compare, find why the time records end early, compare hours with standard hours by labor type with two derived tables, and test the time with no operation. **Time.** About 75 to 90 minutes, the longest of the three. **Demonstrate, then hand over.** Demonstrate Step 4 (the profiles), Step 6 (two derived tables and the cut-off) and Step 7 (the anti-join and the IS NOT NULL test). Leave Steps 1 to 3 and 5 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | Units and standard hours by year | units 52,263, 48,961, 51,160; standard hours 70,871, 66,109, 68,913 |
| 2 | Payroll hours | regular 70,645 to 85,051; overtime 9,452 to 20,411 |
| 3 | Registers and people | 1,675, 1,742, 1,742 registers; the same 67 employees each year |
| 4 | Two profiles | 68,859 entries, 51,114 with an operation, to 2026-12-11; 17,352 completions, to 2026-12-31 |
| 5 | The last pay periods | Processed, then Open and Open |
| 6 | Hours per standard hour | direct `0.85`, `0.87`, `0.94`; indirect `0.33`, `0.54`, `0.57`; the two rows of a year add to 1.18, 1.41, 1.51 |
| 7 | Time with no operation | 3 rows; the direct row holds 20 entries |
| 8 | The saved script | a header with its checks and a comment above each query |

**Stumbles to expect**

- Step 3: `COUNT(*)` read as the number of people.
- Step 4: the profiles skipped, so the last day of the time records goes unnoticed.
- Step 6: without the cut-off the last year reads `0.91` and `0.56`, which flatters the plant; a join of the raw tables first asks for 366,690,316 rows.
- Step 6, coverage: direct and non-manufacturing time end on 2026-12-11, indirect time on 2026-12-04, and the days between hold 3,631.51 direct hours and no indirect time. The sensitivity the text describes stops the hours and the output at 2026-12-04. It gives direct `0.89`, indirect `0.58` and a total of `1.48` from the unrounded hours (59,132.60 and 38,472.89 over 66,119.82 standard hours). Stopping each earlier year at its own last day of indirect time (2024-12-27 and 2025-12-29) leaves its rounded ratios as printed. A student who reports the sensitivity, or separate ratios for each kind of time, has read the coverage correctly. Two rounded ratios add up to the total only to within rounding.
- Step 7: a test on the entry's key alone finds 3 direct entries and misses the 17 whose key is filled in and matches nothing.

**The checkpoint to look for.** The seven bullets. A strong student says that output was about the same and the direct hours recorded stayed below the standard hours, while indirect time, which is overhead, grew, so the records point to the cost of production rather than volume. The strongest add that the ratio is an observed-hours diagnostic, with indirect time ending a week before the cut-off, not a labor efficiency variance or a measure of the production-volume variance.

![A mock of the in-class demonstration of fan-out, one total summed over a join and again from the header table alone.](../figures/chapter-10-joining-and-summarizing/IF-10-0-B.pdf)

## Difficult ideas and misconceptions

**A join that runs is not a join that is right.** Question 1, Tutorial 10.1 Steps 1 and 2, Exercise 10.1 (1). Ask: how many rows should this return, and what would a wrong key do to the count?

**The ledger's key is two columns.** Tutorial 10.2 Step 6, Exercises 10.1 (4) and 10.2. The traced sale's ID matches ledger rows of 11 kinds of document. Ask: which table does this ID belong to?

**An anti-join tests a column that is never NULL in a match.** Exercises 10.2 (3), 10.5 (2) and (5). A test on the entry's own key finds 3 direct entries and misses 17. Ask: which column is NULL only when the match failed?

**NOT IN is not NOT EXISTS.** Question 10, slide 18. With a NULL in the list NOT IN returns 0 employees, the anti-join 117. It is safe in Exercise 10.5 (2) only because the payment key is never NULL. Ask: can this column be NULL?

**WHERE can undo a left join.** Question 11, Tutorial 10.1 Step 6. WHERE leaves 83 rows where ON leaves 88. Ask: what is that column for an unmatched row?

**Fan-out.** Questions 8 and 14, slides 39 to 42, Exercise 10.6 (2). Over the join of invoices to lines, GrandTotal sums to $59,100,114.91 against $31,919,124.42 from the invoices alone, and the closes joined to their operations return 48,479 rows for 12,998 closes. Ask: at what level is each amount recorded?

**Group by the key, not the name.** Question 7, Exercises 10.3 and 10.6 (3). Two customers named Brown LLC merge into one row, and the result does not say so. Ask: what do the row counts of the two groupings say?

**A tie is evidence, not proof.** Tutorial 10.2 Step 3, question 13. The trial balance nets to $0.00 and agrees with Chapter 6, yet neither shows that the entries are complete. Ask: what would still be wrong if both agreed?

## Discussion prompts

1. **The invoice lines and the ledger differ by a few thousand dollars at the year-end. Where do you look first?** A good discussion reaches dated against posted, the invoices that cross the year, and the rule that a difference is explained to the cent.
2. **An anti-join from the ledger to its documents returns no rows. What did you prove?** It reaches existence against completeness: the test in the other direction asks whether every document was posted.
3. **NOT IN returned no one. Does every employee approve requisitions?** It reaches the NULL in the list and the control query that shows a test can find something.
4. **Two customers share a name. Which report misleads the sales manager, and how does the controller find out?** It reaches grouping by key, the row counts and the master-data question of duplicates.
5. **The direct hours recorded stayed below the standard hours while the variance grew. What data would split the overhead part by cause?** It reaches indirect time, overtime, the calendar and Chapter 11's monthly measure.
6. **A join beats comparing two lists by eye. What can it not tell you?** It reaches exact matches only, addresses written differently, and a coincidence of data that is not a relationship.

## Using the exercises

All six exercises are SQL scripts with a model answer in Chapter10-exercises-sql.zip. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 10.1 Reconciling Invoice Lines to the Ledger in SQL | Financial | SQL | 90 | Intermediate | 1, 3, 5, 6 |
| 10.2 Tracing a Sale from the Ledger to Its Documents | Financial | SQL | 75 | Intermediate | 1, 2, 5 |
| 10.3 Average Order Value by Customer | Managerial | SQL | 60 | Basic | 1, 3 |
| 10.4 Purchase Price Variance by Supplier | Managerial | SQL | 90 | Advanced | 1, 3, 5, 6 |
| 10.5 Testing Referential Integrity with Anti-Joins | Auditing | SQL | 90 | Intermediate | 2, 3 |
| 10.6 Suppliers That Share an Employee's Address | Auditing | SQL | 75 | Intermediate | 1, 3, 4, 5 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 10.1 and 10.2, managerial students 10.3 and 10.4, auditing students 10.5 and 10.6. A swap of memos lets each track hear the others.
- *One exercise a session.* Take the basic one first: 10.3, 10.2, 10.5, 10.6, 10.1, 10.4.
- *A light load.* Exercises 10.3 and 10.5 take about two and a half hours and cover outcomes 1 to 3.

**Grading and discussion.** Exercises 10.1, 10.3 and 10.4 (1) to (4) suit grading from the script and the row counts, because their numbers have one answer. Exercises 10.2 (4), 10.4 (5), 10.5 (6) and 10.6 (5) end in a memo or a table of dispositions and suit class discussion. Collect the script, not a screenshot: its comment lines show the population and the expected result.

## Multiple-choice questions

Key: 1 C, 2 A, 3 D, 4 B, 5 B, 6 D, 7 A, 8 C, 9 D, 10 B, 11 A, 12 C, 13 A, 14 D, 15 C.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | C | an inner join drops rows whose key finds no match; the row count is the test of the keys. |
| 2 | A | a column name in two joined tables must be qualified; an alias in SELECT does not say which table it comes from. |
| 3 | D | GROUP BY ItemGroup with SUM returns one total per group. |
| 4 | B | the unmatched item keeps one row, which COUNT(\*) counts; COUNT(wo.WorkOrderID) skips its NULL. |
| 5 | B | a condition on an aggregate belongs in HAVING. |
| 6 | D | Item LEFT JOIN WorkOrder keeps every item, and the IS NULL test keeps those with no matching work order. |
| 7 | A | grouping by name merges different customers that share it; group by the key. |
| 8 | C | fan-out repeats the header amount on each line. |
| 9 | D | a subquery in WHERE supplies the average to compare with. |
| 10 | B | with a NULL in the NOT IN list, a matching employee gives false and every other employee unknown, and WHERE keeps only true, so no row qualifies (use NOT EXISTS or an anti-join). |
| 11 | A | a condition on the second table in WHERE removes the NULL rows; put it in ON. |
| 12 | C | SQLite allows a bare column in a grouped query but returns an arbitrary row's value. |
| 13 | A | when all balances net to zero, the debit balances equal the credit balances (not proof that the entries are right). |
| 14 | D | amounts at different levels are summarized to a common level (the year) before joining. |
| 15 | C | indirect labor is overhead, which Charles River charges at a standard amount per unit, so the cost of extra indirect time can raise the overhead part of the variance. |

**Questions where a wrong option tempts**

- **Question 1.** Option B blames table sizes; a join drops rows because a key found no match.
- **Question 4.** Option A, 0 and 0: the unmatched item still has a row, so `COUNT(*)` counts it.
- **Question 8.** Option A is true, GrandTotal includes freight and tax, but it does not explain a total nearly double.
- **Question 10.** Option A offers a performance excuse for what is a NULL.
- **Question 11.** Option C says WHERE runs before the join, which contradicts the evaluation order of slide 48.
- **Question 13.** Options C and D: closing entries also net to zero, and the point is the sum of the balances.
- **Question 14.** Option C credits the derived table with speed; the reason is the level of each table.
- **Question 15.** Option A puts indirect time in the labor part.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1, 2, 3 and 12 make a quiz of joins and grouping, questions 4, 6, 10 and 11 of left joins and anti-joins, and questions 8, 13, 14 and 15 of fan-out and the variance.

## Connections

**Builds on.** Chapter 3's keys and its warning about double counting, which fan-out names; Chapter 5's Merge, whose inner, left outer and left anti kinds are this chapter's joins; Chapter 6's pre-closing trial balance, rebuilt here in SQL; Chapter 7's flexible budget, applied to hours; and Chapter 9's working copy, script habit and variance accounts.

**Later chapters.** Chapter 11 adds CASE, dates, window functions and views and turns the hours comparison into a monthly measure. Chapter 12's audit library is built from this chapter's anti-joins, profiles and reconciliations, and the Part III case uses the same joins. Chapter 14 rebuilds the invoice and ledger joins as a Power BI model, and Chapter 16 the exception tests.

**Appendices.** The quick reference lists the join and aggregate syntax beside Power Query's merge and DAX. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
