# Chapter 11: Analytical Queries in SQL

| | |
|---|---|
| Unit | Chapter 11: Analytical Queries in SQL |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 270 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part III, Accounting Analytics with SQL: the third of four chapters. Chapter 10 joined and summarized tables; this chapter adds categories, periods, comparisons across rows and saved analyses, and Chapter 12 builds the audit library from them |
| Analytics types | Diagnostic: when the extra plant hours began and where they sit. The trailing measure is also a baseline for predictive work, and Exercises 11.5 and 11.6 are audit tests |
| Tools | DB Browser for SQLite 3.13.1 on the working copy. The queries only read, except the views of Tutorial 11.3 and Exercises 11.1 and 11.5, which are written into the working copy |
| Components | 3 guided tutorials, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 64 slides |
| Files students need | CharlesRiver_Work.sqlite, made in Tutorial 9.1. Chapter11.sql is built through the tutorials; Chapter11-companion.zip holds it at the start of Tutorials 11.2 and 11.3 and at the end. Chapter11-exercises-sql.zip holds Ex 11.1.sql to Ex 11.6.sql |
| Time | Class: about 270, 240 or 120 minutes by plan; the plans do some or all of the tutorials in class, so these times overlap the students' own. Students: about 90 minutes of reading, 60 to 75 for Tutorial 11.1, 75 to 90 for each of Tutorials 11.2 and 11.3, and 75 to 100 for each exercise (assign two or three). All are provisional: time them yourself |

The chapter depends on these conditions of the data:

- Dates are text, and `strftime` returns text that SQLite does not convert in a comparison with a number: of the 297 journal entries posted in 2026, `strftime('%Y', PostingDate) = '2026'` finds them all, and the test against the number finds 0.
- The time records end on 2026-12-11, 20 days before the month ends, because the last pay periods are open. The measure cuts the output at the same day. Indirect time ends a week earlier, on 2026-12-04, so the measure's last month is provisional.
- The plant starts up in the first month: indirect time is almost absent for four months afterward, and one of them, 2024-03, has none at all.
- Payroll is posted on pay dates with no accrual, so the largest months of the gap in account `1090` have three pay dates.
- The only journal entries to the product-line revenue accounts (`4010` to `4040` and `4080`) are the 3 closes of income to the income summary, JE-2024-000265, JE-2025-000287, JE-2026-000296. There are 6 year-end closes in all, and other accounts typed Revenue receive other entries, so the statement covers these five accounts only.
- Every CreatedDate carries a time. Unit margins do not tie but margin percentages do, and six requisitions have no approver.

## What students should be able to do afterward

1. Classify rows with CASE and turn categories into columns with conditional aggregation. Practiced in Tutorial 11.1 (Steps 1, 2 and 4), Exercises 11.1 (2) and (3) and 11.5 (1) and (2), and questions 1 to 3.
2. Use the date functions to group by period, find a month's end and measure days between dates. Practiced in Tutorial 11.1 (Steps 2, 3 and 5), Exercise 11.5 (1), and questions 4 to 6. Exercise 11.5 is the only exercise that calls them.
3. Apply window functions with partitions, frames, rankings and LAG. Practiced in Tutorial 11.2, Exercises 11.2 (2), (3) and (5), 11.3 (2) to (4), 11.4 (2) and (3), 11.5 (4) and 11.6 (3), and questions 7 to 11 and 14.
4. Organize an analysis as a chain of CTEs that can be checked one step at a time. Practiced in Tutorial 11.3 (Steps 1 to 4), in every exercise, and in question 12.
5. Save an analysis as a view in the working copy and query it. Practiced in Tutorial 11.3 (Steps 6 to 8), Exercises 11.1 (5) and 11.5 (5), and question 13.
6. Combine these into a monthly measure, cut off at the last day with records, and judge it. Practiced in Tutorial 11.3 (Steps 4, 5 and 8) and question 15. No exercise rebuilds the trailing measure; Exercise 11.2 applies the same pattern to revenue.

The six outcomes follow the chapter's six learning objectives one for one.

## Preparing to teach

**Before the first class**

- Students need CharlesRiver_Work.sqlite from Tutorial 9.1 and DB Browser for SQLite 3.13.1; `SELECT sqlite_version();` shows the version, and window functions need 3.25 or later.
- Do the three tutorials yourself in order and save Chapter11.sql; Tutorial 11.3 writes a view into your working copy.
- A late student takes Chapter11.sql from the folder of the tutorial they start in Chapter11-companion.zip; Tutorial 11.1 needs only the working copy. The PowerPoint deck is on the Downloads page.
- Open the model scripts once: each query has two comment lines and a result comment, and the notes at the end repeat the requirements and the checks. Exercises 11.1 and 11.5 create views in the working copy, so run the scripts there and not on the download. Every query runs in a few seconds, and Setup_Part3_Views.sql, in the companion zip, recreates the tutorial's view for the Part III case.

**Pitfalls that cost class time**

- **A copy-and-edit slip.** Tutorial 11.3 builds each step by copying the one before. A missing comma between two CTEs stops with `near "MonthlyHours": syntax error`.
- **A second run without the drop.** Run the CREATE VIEW again without its DROP VIEW and the pane says `view MonthlyLaborEfficiency already exists`.
- **Write Changes forgotten.** The view exists in the open database at once but is saved only by **Write Changes**; closing the database and choosing Discard removes it.
- **Nothing selected.** Running with no selection runs the whole script and shows only the last result.

## Teaching approaches

**Plan A: lecture with live demonstration (three sessions of 90 minutes, 270 minutes in all).** It fits a lecture course with the exercises at home. Demonstrate the steps that carry the ideas.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 25 | The plant manager's questions; objectives; CASE | 2 to 9 |
| 1 | 15 | Date functions and their Watch out, month end live | 10 to 13 |
| 1 | 15 | Conditional aggregation; check | 14 to 18 |
| 1 | 35 | Tutorial 11.1: Steps 2 and 3 live; Steps 1, 4 and 5 for students | 19 to 24 |
| 2 | 25 | Window functions: partitions, the peers demonstration, ranking, frames | 25 to 30 |
| 2 | 20 | The functions and clauses; when windows run; check | 31 to 35 |
| 2 | 45 | Tutorial 11.2: Steps 1, 3 and 6 live; Steps 2, 4, 5 and 7 for students | 36 to 42 |
| 3 | 25 | CTEs and views; the working copy; check | 43 to 51 |
| 3 | 40 | Tutorial 11.3: Steps 1, 4, 6 and 7 live; Steps 2, 3, 5, 8 and 9 for students | 52 to 58 |
| 3 | 25 | The plant manager's questions again; summary; assign; quiz on questions 1, 6, 11 and 13 | 59 to 64 |
| | 270 | Total | |

**Plan B: lab first (two sessions of 120 minutes, 240 minutes in all, exercises as homework).** Students write the queries before they hear the vocabulary. It fits a computer lab.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Pose the plant manager's questions | 5 |
| 1 | 50 | Tutorial 11.1 in pairs | 20 to 24 |
| 1 | 15 | Debrief: the ELSE, the modifier order, conditional aggregation | 9, 13, 15 |
| 1 | 45 | Window functions, a short lecture; Tutorial 11.2, Steps 1 to 3 in pairs | 26 to 30, 37, 38 |
| 2 | 35 | Tutorial 11.2, Steps 4 to 7 in pairs; debrief on the pay calendar and the work centers | 39, 40 |
| 2 | 10 | CTEs and views, a short lecture | 44 to 51 |
| 2 | 65 | Tutorial 11.3 in pairs; debrief on partial windows, the provisional last month and the view | 53 to 58 |
| 2 | 10 | The questions again; assign the exercises | 60 to 64 |
| | 240 | Total | |

**Plan C: flipped, with one 120-minute class.** Students read and build the tutorials at home, and the class opens with a quiz. It fits upper-level classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 15 | Quiz on questions 1, 6, 7, 10, 11 and 13 | |
| 30 | Review clinic: partners swap Chapter11.sql and agree the checkpoints: 36 months, the gap's year-end totals, 25 rows in the view | 23, 41, 57 |
| 30 | Break it: the year as a number, a rank in WHERE, a LAG with no partition, a frame of twelve rows back | 13, 33, 30 |
| 35 | Start Exercise 11.2, 11.4 or 11.5 in pairs | |
| 10 | Discussion prompts 1 and 2; assign the exercises | 60 |
| 120 | Total | |

Plan A is the safest, because this chapter's stumbles are about reading a result, and a demonstration shows how. Plan B needs a lab. Plan C fails for students who arrive without a finished script.

![A chooser from a question about rows to the SQL feature that answers it.](../figures/chapter-11-analytical-queries/IF-11-0-A.pdf)

## Tutorial guide

### Guided Tutorial 11.1: Classifying the Payroll and Measuring the Hours by Month

**Purpose.** Students classify the manufacturing payroll with CASE and tie it to the ledger, pivot the labor time by month, find where the time records stop, compare overtime shares and time the work orders. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Steps 2 and 3, which carry conditional aggregation and the date modifiers. Leave Steps 1, 4 and 5 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | Three categories tie to the ledger | hourly pay $3,079,544.37, salaries $263,191.24, employer taxes and benefits $472,661.53; with the deductions ($568,470.78) left out they add to $3,815,397.14, the charge to `1090` |
| 2 | One row for each month | 36 rows; indirect hours 0 to 97 in the four months after the first, against 4,931 in the first; 9 days with time in the last month |
| 3 | Where the records stop | last work date 2026-12-11, month end 2026-12-31, 20 days short |
| 4 | Overtime shares | direct 6.0% to 11.1% in the first six months, a quarter or more in 10 months of 2026 with dips in May (17.8%) and November (9.3%); indirect 5.9% to 11.6%; NULL in 2024-03 |
| 5 | Days from release to completion, and to close | by close year 17.5, 28.8, 40.3; completion to close 8.4, 8.8, 8.4 |

**Stumbles to expect**

- Step 1: without an ELSE the deductions fall into a group named NULL ($568,470.78); a `LIKE '%Earnings'` branch placed first takes the salaries into hourly pay ($3,342,735.61, 3 categories).
- Step 2: without the LaborType filter the query adds nonmanufacturing overtime and work dates. The overtime of 2026 reads 20,547 hours where 20,030 is right, and DaysWithTime changes in 16 of the 36 months, January 2024 from 13 to 23 days and January 2026 from 21 to 22. DirectHours and IndirectHours do not change, because their CASE expressions still restrict those sums.
- Step 3: without `'start of month'` the month end reads 2027-01-10, 30 days away, not 20; `date('2026-01-31', '+1 month')` returns 2026-03-03.
- Step 5: `strftime('%Y', ClosedDate) = 2026` finds 0 work orders, and 3,960 with the year as text.
- Step 5, the dates: one work order closed in 2024 is completed 3 days before its release, without moving the average. Credit checking the dates and reading cohorts, not a cause.

**The checkpoint to look for.** The six bullets. A strong student names three views of one change: indirect time, direct overtime and slower work orders.

### Guided Tutorial 11.2: Tracking the Gap Month by Month

**Purpose.** Students calculate the monthly gap in account `1090` with a year-to-date total, compare each month with the same month a year earlier, rank the months, count their pay dates, and rank the work centers by hours recorded against plan. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 1 (the year-to-date window), Step 3 (the derived table) and Step 6 (the work centers). Leave Steps 2, 4, 5 and 7 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | December year to date grows each year | $1,111,350.47, $1,779,843.09, $2,161,510.29 |
| 2 | Same month a year earlier | NULL in the first year; July is 2.86 times the July before, August 0.54 |
| 3 | Three largest months a year | 9 rows; first-ranked August, August, July |
| 4 | Pay dates of those months | three in every first-ranked month |
| 5 | Pay dates by month | months with three: 2024: March and August; 2025: January and August; 2026: January and July; per year 24, 26, 26 |
| 6 | Work centers in the last year | Packing Work Center 4.19; Quality Assurance Work Center 4.02; Finishing and Test Work Center 0.56; Cutting Work Center 0.41; Assembly Work Center 0.40 |
| 7 | The plant's excess | negative every year: -17,715, -13,365, -9,141 hours |

**Stumbles to expect**

- Step 2: a LAG with no partition compares each month with the month before: July of the last year against $150,042.56, June's figure.
- Step 3: the rank in WHERE stops with `misuse of aliased window function GapRank`, or `misuse of window function RANK()` when the expression is repeated.
- Step 6: an inner join to the labor summary raises Packing to 4.73 and Quality Assurance to 6.28, because operations with no direct time leave the plan; joining the labor entries straight to the operations repeats the planned hours and cuts them to 1.93 and 2.45; without the cut-off 5 rows have no year.
- Step 6, the cohort: of the 13,131 operations counted in the last year, 5,981 have no direct time and 1,795 have direct time dated after they ended, hence a finding to investigate.

**The checkpoint to look for.** The six bullets. A strong student says that the largest months come from the pay calendar, and that the work-center pattern is a finding to investigate, not an explanation.

### Guided Tutorial 11.3: Building the Monthly Measure and Saving It as a View

**Purpose.** Students build the output step and the hours step, join them, add the trailing twelve months over a named window, look at the partial windows, save the chain as a view, write it to the file and query it. **Time.** About 75 to 90 minutes, the longest of the three. **Demonstrate, then hand over.** Demonstrate Steps 1 and 4 (each step checked on its own, then the named window) and Steps 6 and 7 (the view and **Write Changes**). Leave Steps 2, 3, 5, 8 and 9 to students.

| Step | Look for | Value |
|---|---|---|
| 1 to 3 | Each step returns every month | 36, 36 and 36 rows |
| 4 | The view's rows | 25 rows from 2024-12; each December direct 0.85, 0.87, 0.94, indirect 0.33, 0.54, 0.57, total 1.18, 1.41, 1.51; peak total 1.54 in 2026-10 |
| 5 | Partial windows | 11 rows; the first month's total reads 12.52 |
| 6, 7 | The view | created without a result grid; under Views on **Database Structure**; saved by **Write Changes** |
| 8 | The view for the last year | 12 rows, as in Step 4 |

**Stumbles to expect**

- Step 2: indirect time in a step of its own, with `WHERE LaborType = 'Indirect Manufacturing'`, loses the month with none: 35 months where 36 belong, and a view of 24 rows starting 2025-01.
- Step 4: `12 PRECEDING` holds thirteen months, and the filter on twelve keeps 1 row. An average of twelve monthly ratios reads 1.53 where the pooled figure reads 1.51. Without the cut-off the last month's ratio reads 0.72 instead of 1.03.
- Step 4, coverage: the last row's direct time and output run to 2026-12-11, its indirect time to 2026-12-04. Counted to that day on both sides, the row reads direct `0.89`, indirect `0.58`, total `1.48` and overtime share `0.192` (published `0.94`, `0.57`, `1.51`, `0.198`); no other row changes. Accept it as a labeled sensitivity. The rounded parts miss the rounded total by a hundredth in 8 of 25 rows.

**The checkpoint to look for.** The seven bullets. A strong student says that the trailing ratio shows a trend only while coverage and definitions hold, and that the last month is provisional.

![The monthly ratio against the trailing twelve months, for the discussion of delay.](../figures/chapter-11-analytical-queries/IF-11-0-C.pdf)

## Difficult ideas and misconceptions

**A text result compared with a numeric literal.** Question 6, Tutorial 11.1 Step 5, Exercises 11.4 and 11.5. `strftime` returns text, and a function's result is not a column, so SQLite has no affinity to convert the number with. A year compared with a number finds nothing, and `IN (0, 6)` flags no weekend. Compare with `'2026'`, or CAST. Ask: what type does this function return, and is anything here a column?

**An ELSE is a decision.** Question 1, Tutorial 11.1 Step 1, Exercise 11.1. A CASE without one sends the rest to NULL, and a CASE inside SUM needs `ELSE 0` or a NULL that COUNT skips. Ask: what should happen to a row that meets no condition?

**Order decides a CASE.** Question 2, Exercise 11.1. A broad branch first swallows the narrow ones. Ask: which branch does this row meet first?

**A window keeps the rows.** Questions 7 and 14. `GROUP BY` returns one row for each group, `PARTITION BY` keeps every row, and the partition decides which rows a calculation sees while the order and the frame decide which of them it uses. Ask: which rows does this row's calculation read?

**Tied rows share a total.** Question 11, slide 27. Below, the Furniture items ranked by standard labor hours tie at 1.99 from row 7: both rows read a default running total of 16.50 and rank 7, while ROW_NUMBER gives 8 and 7 and the ROWS totals 16.50 and 14.51, in an order the engine chooses. Ask: what does the data decide, and what does the engine decide?

![A mock of the demonstration of tied rows, the default window against ROWS UNBOUNDED PRECEDING.](../figures/chapter-11-analytical-queries/IF-11-0-B.pdf)

**A rank cannot be filtered where it is made.** Question 10, Tutorial 11.2 Step 3, Exercise 11.3 (3). WHERE runs before windows, so the filter belongs in an outer query. The same rule makes a year filter beside a LAG leave every prior year NULL (Exercise 11.2). Ask: when does WHERE run?

**The partition is the comparison.** Question 8, Exercise 11.2 (3). A LAG partitioned by the month compares a month with the same month of an earlier year; with no partition it reads the previous row, or another product line. Ask: which row is the prior one?

**A calendar effect is not performance.** Tutorial 11.2 Steps 4 and 5. The largest months have three pay dates, and the first year has two pay dates fewer than the later years. Ask: what would a month-end accrual have done to these months?

**A trailing figure needs full windows.** Question 15, Tutorial 11.3 Steps 4 and 5. A frame counts rows, not months; partial windows are left out; the figure pools twelve months and is not an average of ratios; the last month is provisional. Ask: does this window hold twelve months?

**A view is a query, not a result.** Question 13, Tutorial 11.3 Steps 6 to 8, Exercise 11.5 (5). It runs on whatever the file holds, and a change to its tables can be refused at once or leave a view that fails or changes meaning later. Ask: what would make today's view return something different tomorrow?

## Discussion prompts

1. **The monthly ratio swings and the trailing ratio rises. Which does the controller report, and what does each hide?** A good discussion reaches the delay of a trailing figure and the need for full windows.
2. **The largest months of the gap have three pay dates. Is the plant worse in those months?** It reaches the pay calendar against performance and the missing accrual.
3. **Packing and Quality Assurance record several times their planned hours while the plant records less than plan. What do you test first?** It reaches how time is recorded against operations.
4. **A view stores a query. When is that a control and when a risk?** It reaches one logic for every user, dependence on the tables, and why a view is not a record.
5. **The journal entry flags of Exercise 11.5 mark entries for follow-up. Which would you weigh differently?** It reaches flags as screens and equal weights as an assumption.
6. **Overtime is spread across the employees who recorded it. Is that good news for the plant manager's claim?** It reaches an even spread as a pattern that needs explaining, and Chapter 12's surge days.

## Using the exercises

All six exercises are SQL scripts with a model answer in Chapter11-exercises-sql.zip. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 11.1 The Financial Statements from the Ledger | Financial | SQL | 100 | Advanced | 1, 4, 5 |
| 11.2 Monthly Revenue with Year-to-Date and Prior-Year Comparisons | Financial | SQL | 90 | Intermediate | 1, 3, 4 |
| 11.3 Ranking Items by Unit Margin Within Each Product Line | Managerial | SQL | 75 | Basic | 3, 4 |
| 11.4 Is Overtime Concentrated? | Managerial | SQL | 90 | Intermediate | 3, 4 |
| 11.5 Journal Entry Tests in SQL | Auditing | SQL | 100 | Intermediate | 1, 2, 3, 4, 5 |
| 11.6 Requisitions Just Under the Approval Threshold | Auditing | SQL | 90 | Intermediate | 1, 3, 4 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 11.1 and 11.2, managerial students 11.3 and 11.4, auditing students 11.5 and 11.6.
- *One exercise a session.* Take the basic one first: 11.3, 11.6, 11.2, 11.4, 11.5, 11.1.
- *A light load.* Exercises 11.3 and 11.5 take about three hours and cover outcomes 1 to 5.

**Grading and discussion.** Requirements (1) to (4) of every exercise suit grading from the script and the row counts, because their numbers have one answer. The notes and memos, Requirement (5) of Exercises 11.2 to 11.6 and the note of 11.1, suit class discussion. Collect the script, not a screenshot: its comment lines show the population and the expected result. Full credit asks only for what each requirement asks. The extras the guides add, such as freight or a decline's base in Exercise 11.2, a memo's two readings and next steps, or an ELSE, are a plus, named in What a strong answer says.

## Multiple-choice questions

Key: 1 D, 2 B, 3 C, 4 A, 5 D, 6 C, 7 A, 8 B, 9 D, 10 B, 11 A, 12 C, 13 D, 14 B, 15 A.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | D | a CASE without ELSE returns NULL for rows that meet no condition. |
| 2 | B | conditions are tested in order, and the first true one wins. |
| 3 | C | conditional aggregation passes the amounts of one category and zero for the others; B counts rows, and D is not an aggregate of the category. |
| 4 | A | strftime returns text formatted by its pattern. |
| 5 | D | the difference of two julianday values is a number of days. |
| 6 | C | strftime returns text, and this comparison does not convert the numeric literal; compare with '2026' or CAST. |
| 7 | A | an ordered aggregate window is a running total, restarting in each partition (with one row for each fiscal year and period there are no ties). |
| 8 | B | LAG with offset 12 over one row per month returns the same month a year earlier, on a row with at least twelve earlier rows (the first twelve return NULL). |
| 9 | D | RANK gives ties the same number; ROW\_NUMBER numbers every row differently. |
| 10 | B | WHERE runs before window functions; filter in an outer query (RANK \<= 3 keeps more than three rows if the third ties). |
| 11 | A | the default window of an ordered aggregate runs through the current row and its peers, the rows tied with it; B describes ROWS UNBOUNDED PRECEDING. |
| 12 | C | named steps can be read and checked one at a time; a subquery can also be repeated, so D is false. |
| 13 | D | a view stores its query and runs it again each time. |
| 14 | B | PARTITION BY decides which rows each calculation sees, without collapsing them. |
| 15 | A | a trailing measure separates a trend in the recorded measure from single-month swings, if coverage and definitions held. |

**Questions where a wrong option tempts**

- **Question 6.** Options A and B blame the date; the cause is the type of the result.
- **Question 7.** Option B is the whole-year total; the ORDER BY makes a running total.
- **Question 10.** Options A and C offer syntax excuses for evaluation order.
- **Question 11.** Option B describes `ROWS UNBOUNDED PRECEDING`; the default window runs through the peers.
- **Question 14.** Option A treats `PARTITION BY` as a filter or a sort.
- **Question 15.** Option C says a trailing measure always rises.
- **Length.** The correct option is also the longest in 2 of the 15 questions (3 and 15), so wording alone can give it away. If you grade with these, ask students to explain their answer or reword the options.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 3 cover CASE, 4 to 6 dates, 7 to 11 and 14 windows, and 12, 13 and 15 CTEs, views and the measure.

## Connections

**Builds on.** Chapter 5's IFS and Chapter 6's SUMIFS and Show Values As, which CASE, conditional aggregation and windows repeat in SQL; Chapter 7's year-over-year comparison; Chapter 9's script habit; Chapter 10's joins, trial balance and hours comparison, which this chapter turns into a monthly measure; and Chapter 8's journal entry tests and Exercise 8.5, which Exercises 11.5 and 11.6 repeat.

**Later chapters.** Chapter 12's audit library is built from these CTEs, views and window functions, and it takes up the questions about the time records that this chapter ends with. The Part III case uses the saved view. Chapter 14 rebuilds the prior-year comparison in DAX, Chapter 15 the trailing measure, and Chapter 16 the journal entry tests.

**Appendices.** The quick reference lists CASE, the date functions and the window syntax beside Excel and DAX. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
