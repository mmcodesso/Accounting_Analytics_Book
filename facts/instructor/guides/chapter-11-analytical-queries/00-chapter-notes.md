---
note: ch11.chapter
title: 'Chapter 11: Analytical Queries in SQL'
kind: chapter-notes
unit: '11'
minutes: 270
tool: sql
figures:
  - id: IF-11-0-A
    kind: diagram
    purpose: A chooser from a question about rows to the SQL feature that answers it.
    shows: "Five questions lead to CASE, a CASE inside SUM, the date functions, a window (partition, order, frame), and a CTE chain or view. Each leaf names its check and the tutorial step."
    data: None; the leaves cite the tutorials and exercises.
  - id: IF-11-0-B
    kind: sql-mock
    purpose: The demonstration of tied rows, the default window against ROWS UNBOUNDED PRECEDING.
    shows: "The Furniture items ranked by StandardLaborHoursPerUnit with RANK, ROW_NUMBER and both running totals, the first ten rows, the first tied pair outlined."
    data: Item, Furniture group, read-only.
  - id: IF-11-0-C
    kind: chart
    purpose: The monthly ratio against the trailing twelve months, for the discussion of delay.
    shows: "Monthly hours per standard hour against the trailing total, direct and indirect lines; the peak labeled and the last point marked provisional."
    data: The view MonthlyLaborEfficiency, read-only.
---
# Chapter 11: Analytical Queries in SQL

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part III, Accounting Analytics with SQL: the third of four chapters. Chapter 10 joined and summarized tables; this chapter adds categories, periods, comparisons across rows and saved analyses, and Chapter 12 builds the audit library from them |
| Analytics types | Diagnostic: when the extra plant hours began and where they sit. The trailing measure is also a baseline for predictive work, and Exercises 11.5 and 11.6 are audit tests |
| Tools | DB Browser for SQLite {{ version }} on the working copy. The queries only read, except the views of Tutorial 11.3 and Exercises 11.1 and 11.5, which are written into the working copy |
| Components | {{ unit.tutorials|length }} guided tutorials, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver_Work.sqlite, made in Tutorial 9.1. Chapter11.sql is built through the tutorials; Chapter11-companion.zip holds it at the start of Tutorials 11.2 and 11.3 and at the end. Chapter11-exercises-sql.zip holds Ex 11.1.sql to Ex 11.6.sql |
| Time | Class: about 270, 240 or 120 minutes by plan; the plans do some or all of the tutorials in class, so these times overlap the students' own. Students: about 90 minutes of reading, 60 to 75 for Tutorial 11.1, 75 to 90 for each of Tutorials 11.2 and 11.3, and 75 to 100 for each exercise (assign two or three). All are provisional: time them yourself |

The chapter depends on these conditions of the data:

- Dates are text, and `strftime` returns text that SQLite does not convert in a comparison with a number: of the {{ n_year_text }} journal entries posted in {{ y }}, `strftime('%Y', PostingDate) = '{{ y }}'` finds them all, and the test against the number finds {{ n_year_num }}.
- The time records end on {{ t1.last }}, {{ t1.short }} days before the month ends, because the last pay periods are open. The measure cuts the output at the same day. Indirect time ends a week earlier, on {{ t3.ind_end }}, so the measure's last month is provisional.
- The plant starts up in the first month: indirect time is almost absent for four months afterward, and one of them, {{ t1.zero_month }}, has none at all.
- Payroll is posted on pay dates with no accrual, so the largest months of the gap in account `1090` have three pay dates.
- The only journal entries to the product-line revenue accounts (`4010` to `4040` and `4080`) are the {{ n_pl_closes }} closes of income to the income summary, {{ pl_closes|join(', ') }}. There are {{ n_close }} year-end closes in all, and other accounts typed Revenue receive other entries, so the statement covers these five accounts only.
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

- Students need CharlesRiver_Work.sqlite from Tutorial 9.1 and DB Browser for SQLite {{ version }}; `SELECT sqlite_version();` shows the version, and window functions need 3.25 or later.
- Do the three tutorials yourself in order and save Chapter11.sql; Tutorial 11.3 writes a view into your working copy.
- A late student takes Chapter11.sql from the folder of the tutorial they start in Chapter11-companion.zip; Tutorial 11.1 needs only the working copy. The PowerPoint deck is on the Downloads page.
- Open the model scripts once: each query has two comment lines and a result comment, and the notes at the end repeat the requirements and the checks. Exercises 11.1 and 11.5 create views in the working copy, so run the scripts there and not on the download. Every query runs in a few seconds, and Setup_Part3_Views.sql, in the companion zip, recreates the tutorial's view for the Part III case.

**Pitfalls that cost class time**

- **A copy-and-edit slip.** Tutorial 11.3 builds each step by copying the one before. A missing comma between two CTEs stops with `{{ t3.comma_msg }}`.
- **A second run without the drop.** Run the CREATE VIEW again without its DROP VIEW and the pane says `{{ t3.again }}`.
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
| 30 | Review clinic: partners swap Chapter11.sql and agree the checkpoints: {{ t1.n_months }} months, the gap's year-end totals, {{ t3.n_view }} rows in the view | 23, 41, 57 |
| 30 | Break it: the year as a number, a rank in WHERE, a LAG with no partition, a frame of twelve rows back | 13, 33, 30 |
| 35 | Start Exercise 11.2, 11.4 or 11.5 in pairs | |
| 10 | Discussion prompts 1 and 2; assign the exercises | 60 |
| 120 | Total | |

Plan A is the safest, because this chapter's stumbles are about reading a result, and a demonstration shows how. Plan B needs a lab. Plan C fails for students who arrive without a finished script.

{{ figure('IF-11-0-A') }}

## Tutorial guide

### Guided Tutorial 11.1: Classifying the Payroll and Measuring the Hours by Month

**Purpose.** Students classify the manufacturing payroll with CASE and tie it to the ledger, pivot the labor time by month, find where the time records stop, compare overtime shares and time the work orders. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Steps 2 and 3, which carry conditional aggregation and the date modifiers. Leave Steps 1, 4 and 5 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | Three categories tie to the ledger | hourly pay ${{ t1.hourly|money }}, salaries ${{ t1.salaries|money }}, employer taxes and benefits ${{ t1.employer|money }}; with the deductions (${{ t1.deductions|money }}) left out they add to ${{ t1.ledger|money }}, the charge to `1090` |
| 2 | One row for each month | {{ t1.n_months }} rows; indirect hours {{ t1.quiet_low|num }} to {{ t1.quiet_high|num }} in the four months after the first, against {{ t1.first[3]|num }} in the first; {{ t1.days_last }} days with time in the last month |
| 3 | Where the records stop | last work date {{ t1.last }}, month end {{ t1.month_end }}, {{ t1.short }} days short |
| 4 | Overtime shares | direct {{ t1.h1_low|pct }} to {{ t1.h1_high|pct }} in the first six months, a quarter or more in {{ t1.n_high }} months of {{ y }} with dips in {% for dp in t1.dips %}{{ dp[0] }} ({{ dp[1]|pct }}){{ " and " if not loop.last else "" }}{% endfor %}; indirect {{ t1.ind_low|pct }} to {{ t1.ind_high|pct }}; NULL in {{ t1.zero_month }} |
| 5 | Days from release to completion, and to close | by close year {% for l in t1.lead %}{{ l[2]|num(1) }}{{ ", " if not loop.last else "" }}{% endfor %}; completion to close {% for l in t1.lead %}{{ l[3]|num(1) }}{{ ", " if not loop.last else "" }}{% endfor %} |

**Stumbles to expect**

- Step 1: without an ELSE the deductions fall into a group named NULL (${{ t1.null_group|money }}); a `LIKE '%Earnings'` branch placed first takes the salaries into hourly pay (${{ t1.broad_hourly|money }}, {{ t1.broad_n }} categories).
- Step 2: without the LaborType filter the query adds nonmanufacturing overtime and work dates. The overtime of {{ y }} reads {{ t1.ot_year_all|num }} hours where {{ t1.ot_year|num }} is right, and DaysWithTime changes in {{ t1.n_days_changed }} of the {{ t1.n_months }} months, {{ t1.days_first[0] }} from {{ t1.days_first[1] }} to {{ t1.days_first[2] }} days and {{ t1.days_year[0] }} from {{ t1.days_year[1] }} to {{ t1.days_year[2] }}. DirectHours and IndirectHours do not change, because their CASE expressions still restrict those sums.
- Step 3: without `'start of month'` the month end reads {{ t1.no_start }}, {{ t1.no_start_days }} days away, not {{ t1.short }}; `date('2026-01-31', '+1 month')` returns {{ t1.jan31 }}.
- Step 5: `strftime('%Y', ClosedDate) = {{ y }}` finds {{ t1.n_num }} work orders, and {{ t1.n_text|count }} with the year as text.
- Step 5, the dates: one work order closed in {{ t1.neg_year }} is completed {{ -t1.neg_days }} days before its release, without moving the average. Credit checking the dates and reading cohorts, not a cause.

**The checkpoint to look for.** The six bullets. A strong student names three views of one change: indirect time, direct overtime and slower work orders.

### Guided Tutorial 11.2: Tracking the Gap Month by Month

**Purpose.** Students calculate the monthly gap in account `1090` with a year-to-date total, compare each month with the same month a year earlier, rank the months, count their pay dates, and rank the work centers by hours recorded against plan. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 1 (the year-to-date window), Step 3 (the derived table) and Step 6 (the work centers). Leave Steps 2, 4, 5 and 7 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | December year to date grows each year | {% for r in t2.ytd %}${{ r[2]|money }}{{ ", " if not loop.last else "" }}{% endfor %} |
| 2 | Same month a year earlier | NULL in the first year; July is {{ t2.jul_ratio|num(2) }} times the July before, August {{ t2.aug_ratio|num(2) }} |
| 3 | Three largest months a year | {{ t2.top|length }} rows; first-ranked {% for f in t2.firsts %}{{ f[1] }}{{ ", " if not loop.last else "" }}{% endfor %} |
| 4 | Pay dates of those months | three in every first-ranked month |
| 5 | Pay dates by month | months with three: {{ t2.three_text|join('; ') }}; per year {% for yr in t2.totals %}{{ t2.totals[yr] }}{{ ", " if not loop.last else "" }}{% endfor %} |
| 6 | Work centers in the last year | {% for r in t2.last %}{{ r[1] }} {{ r[3]|num(2) }}{{ "; " if not loop.last else "" }}{% endfor %} |
| 7 | The plant's excess | negative every year: {% for pl in t2.plant %}{{ pl[1]|num }}{{ ", " if not loop.last else "" }}{% endfor %} hours |

**Stumbles to expect**

- Step 2: a LAG with no partition compares each month with the month before: July of the last year against ${{ t2.prev_jul|money }}, June's figure.
- Step 3: the rank in WHERE stops with `{{ t2.msg_alias }}`, or `{{ t2.msg_direct }}` when the expression is repeated.
- Step 6: an inner join to the labor summary raises Packing to {{ t2.packing_inner|num(2) }} and Quality Assurance to {{ t2.qa_inner|num(2) }}, because operations with no direct time leave the plan; joining the labor entries straight to the operations repeats the planned hours and cuts them to {{ t2.packing_fan|num(2) }} and {{ t2.qa_fan|num(2) }}; without the cut-off {{ t2.n_null_year }} rows have no year.
- Step 6, the cohort: of the {{ t2.ops_last|num }} operations counted in the last year, {{ t2.ops_no_time|num }} have no direct time and {{ t2.ops_late|num }} have direct time dated after they ended, hence a finding to investigate.

**The checkpoint to look for.** The six bullets. A strong student says that the largest months come from the pay calendar, and that the work-center pattern is a finding to investigate, not an explanation.

### Guided Tutorial 11.3: Building the Monthly Measure and Saving It as a View

**Purpose.** Students build the output step and the hours step, join them, add the trailing twelve months over a named window, look at the partial windows, save the chain as a view, write it to the file and query it. **Time.** About 75 to 90 minutes, the longest of the three. **Demonstrate, then hand over.** Demonstrate Steps 1 and 4 (each step checked on its own, then the named window) and Steps 6 and 7 (the view and **Write Changes**). Leave Steps 2, 3, 5, 8 and 9 to students.

| Step | Look for | Value |
|---|---|---|
| 1 to 3 | Each step returns every month | {{ t3.n_out }}, {{ t3.n_hours }} and {{ t3.n_monthly }} rows |
| 4 | The view's rows | {{ t3.n_view }} rows from {{ t3.first_full }}; each December direct {% for r in t3.decs %}{{ r[2]|num(2) }}{{ ", " if not loop.last else "" }}{% endfor %}, indirect {% for r in t3.decs %}{{ r[3]|num(2) }}{{ ", " if not loop.last else "" }}{% endfor %}, total {% for r in t3.decs %}{{ r[4]|num(2) }}{{ ", " if not loop.last else "" }}{% endfor %}; peak total {{ t3.peak[4]|num(2) }} in {{ t3.peak[0] }} |
| 5 | Partial windows | {{ t3.n_partial }} rows; the first month's total reads {{ t3.first_partial[4]|num(2) }} |
| 6, 7 | The view | created without a result grid; under Views on **Database Structure**; saved by **Write Changes** |
| 8 | The view for the last year | {{ t3.via_view }} rows, as in Step 4 |

**Stumbles to expect**

- Step 2: indirect time in a step of its own, with `WHERE LaborType = 'Indirect Manufacturing'`, loses the month with none: {{ t3.sep_monthly }} months where {{ t3.n_monthly }} belong, and a view of {{ t3.sep_view }} rows starting {{ t3.sep_first }}.
- Step 4: `12 PRECEDING` holds thirteen months, and the filter on twelve keeps {{ t3.f13_rows }} row. An average of twelve monthly ratios reads {{ t3.avg_last|num(2) }} where the pooled figure reads {{ t3.last[4]|num(2) }}. Without the cut-off the last month's ratio reads {{ t3.nc_last[1]|num(2) }} instead of {{ t3.last[1]|num(2) }}.
- Step 4, coverage: the last row's direct time and output run to {{ t3.cut_day }}, its indirect time to {{ t3.ind_end }}. Counted to that day on both sides, the row reads direct `{{ t3.c_last[2] }}`, indirect `{{ t3.c_last[3] }}`, total `{{ t3.c_last[4] }}` and overtime share `{{ t3.c_last[5] }}` (published `{{ t3.last[2] }}`, `{{ t3.last[3] }}`, `{{ t3.last[4] }}`, `{{ t3.last[5] }}`); no other row changes. Accept it as a labeled sensitivity. The rounded parts miss the rounded total by a hundredth in {{ t3.n_round }} of {{ t3.n_view }} rows.

**The checkpoint to look for.** The seven bullets. A strong student says that the trailing ratio shows a trend only while coverage and definitions hold, and that the last month is provisional.

{{ figure('IF-11-0-C') }}

## Difficult ideas and misconceptions

**A text result compared with a numeric literal.** Question 6, Tutorial 11.1 Step 5, Exercises 11.4 and 11.5. `strftime` returns text, and a function's result is not a column, so SQLite has no affinity to convert the number with. A year compared with a number finds nothing, and `IN (0, 6)` flags no weekend. Compare with `'{{ y }}'`, or CAST. Ask: what type does this function return, and is anything here a column?

**An ELSE is a decision.** Question 1, Tutorial 11.1 Step 1, Exercise 11.1. A CASE without one sends the rest to NULL, and a CASE inside SUM needs `ELSE 0` or a NULL that COUNT skips. Ask: what should happen to a row that meets no condition?

**Order decides a CASE.** Question 2, Exercise 11.1. A broad branch first swallows the narrow ones. Ask: which branch does this row meet first?

**A window keeps the rows.** Questions 7 and 14. `GROUP BY` returns one row for each group, `PARTITION BY` keeps every row, and the partition decides which rows a calculation sees while the order and the frame decide which of them it uses. Ask: which rows does this row's calculation read?

**Tied rows share a total.** Question 11, slide 27. Below, the Furniture items ranked by standard labor hours tie at {{ peers.pair_hours|num(2) }} from row {{ peers.pair_row }}: both rows read a default running total of {{ peers.pair_default|num(2) }} and rank {{ peers.pair_rank }}, while ROW_NUMBER gives {{ peers.pair_nums[0] }} and {{ peers.pair_nums[1] }} and the ROWS totals {{ peers.pair_frame[0]|num(2) }} and {{ peers.pair_frame[1]|num(2) }}, in an order the engine chooses. Ask: what does the data decide, and what does the engine decide?

{{ figure('IF-11-0-B') }}

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

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 6.** Options A and B blame the date; the cause is the type of the result.
- **Question 7.** Option B is the whole-year total; the ORDER BY makes a running total.
- **Question 10.** Options A and C offer syntax excuses for evaluation order.
- **Question 11.** Option B describes `ROWS UNBOUNDED PRECEDING`; the default window runs through the peers.
- **Question 14.** Option A treats `PARTITION BY` as a filter or a sort.
- **Question 15.** Option C says a trailing measure always rises.
{% if n_longest %}
- **Length.** The correct option is also the longest in {{ n_longest }} of the {{ n_questions }} questions ({{ longest_correct }}), so wording alone can give it away. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 3 cover CASE, 4 to 6 dates, 7 to 11 and 14 windows, and 12, 13 and 15 CTEs, views and the measure.

## Connections

**Builds on.** Chapter 5's IFS and Chapter 6's SUMIFS and Show Values As, which CASE, conditional aggregation and windows repeat in SQL; Chapter 7's year-over-year comparison; Chapter 9's script habit; Chapter 10's joins, trial balance and hours comparison, which this chapter turns into a monthly measure; and Chapter 8's journal entry tests and Exercise 8.5, which Exercises 11.5 and 11.6 repeat.

**Later chapters.** Chapter 12's audit library is built from these CTEs, views and window functions, and it takes up the questions about the time records that this chapter ends with. The Part III case uses the saved view. Chapter 14 rebuilds the prior-year comparison in DAX, Chapter 15 the trailing measure, and Chapter 16 the journal entry tests.

**Appendices.** The quick reference lists CASE, the date functions and the window syntax beside Excel and DAX. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
