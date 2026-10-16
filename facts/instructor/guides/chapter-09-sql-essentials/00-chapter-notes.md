---
note: ch09.chapter
title: 'Chapter 9: SQL Essentials for Accounting Analytics'
kind: chapter-notes
unit: '9'
minutes: 240
tool: sql
figures:
  - id: IF-09-0-A
    kind: diagram
    purpose: A path from the symptom of a wrong result to its usual cause and its check, for the discussion of logical errors.
    shows: "A decision path read from top to bottom. The top box asks whether the query that ran is right. Four branches by symptom: no rows, far too many rows, one column instead of two, and blank cells. Each names the usual cause (a comparison with NULL, text in the wrong case, a text year compared with a number, AND and OR without parentheses, a missing comma, a NULL in a calculation) and the check (IS NULL, DISTINCT, quotes or CAST, parentheses and a row count, an alias read as a column, COALESCE). Each leaf cites the tutorial step or exercise that practices it."
    data: None; the leaves cite the chapter's tutorials and exercises.
  - id: IF-09-0-B
    kind: sql-mock
    purpose: The in-class calculator demonstration, a statement with no table.
    shows: "The Execute SQL tab with the statement of the check slide, a division of two INTEGER values, a division with a REAL operand and a text year compared with a number. The grid shows one row with three values, and the message pane reports one row returned."
    data: The expressions of the check slide and of question 15, evaluated by SQLite.
---
# Chapter 9: SQL Essentials for Accounting Analytics

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part III, Accounting Analytics with SQL: the first of four chapters, and the first that leaves Excel for a database |
| Analytics types | Descriptive: finding, listing and ranking the records. The audit exercises add a habit of diagnostic work: test a result against what it should be |
| Tools | DB Browser for SQLite {{ version }} with SQLite, one table at a time. Excel only receives a result in Tutorial 9.3 |
| Components | {{ unit.tutorials|length }} guided tutorials, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.sqlite, never edited, and CharlesRiver_Work.sqlite, the copy made in Tutorial 9.1. Chapter09.sql is built through the tutorials; Chapter09-companion.zip holds it at the start of Tutorials 9.2 and 9.3 and at the end of the chapter. Chapter09-exercises-sql.zip holds Ex 9.1.sql to Ex 9.6.sql |
| Time | Class: about 240 minutes. Students: about one hour of reading, 60 to 75 minutes for each tutorial and 45 to 75 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The ledger holds {{ t1.gl_n|count }} rows, which is why the chapter queries a database. GLEntry.AccountID is the Account table's surrogate key, not the account number: the manufacturing variance, account {{ t1.no.variance }}, is AccountID {{ t1.variance_id }}.
- The year's postings to that account are {{ t2.rows|count }} rows: {{ t2.wo_rows|count }} work order closes and one journal entry, the year-end close {{ t2.close }}, which makes the year net to zero. {{ t2.open_n }} work orders have no ClosedDate, and every one was released in {{ t2.year }}.
- Blank values are NULL, not empty text (ClosedDate, TrackingNumber, ClockOutTime), and dates are text in year-month-day form.
- The exercises rest on planted conditions (shipments with no tracking number or still In Transit after their delivery date, direct labor with no operation, clock entries with no clock-out) and on tests that are clean on purpose (the parts of every close and the components of every manufactured item add up).

## What students should be able to do afterward

1. Set up DB Browser for SQLite with a working copy of the database and read a table's structure before querying it. Practiced in Tutorial 9.1 (Steps 1 to 3) and question 10; every exercise starts in the working copy.
2. Write SELECT statements that choose, rename, calculate and DISTINCT columns. Practiced in Tutorial 9.1, Exercises 9.1 (1) and (2), 9.3 (1), (2) and (4), 9.4 (2) and questions 1, 7 and 15.
3. Filter rows with WHERE, with comparison and logical operators, BETWEEN, IN and LIKE, values of the right type and grouped AND and OR. Practiced in Tutorial 9.2 (Steps 1 to 4), Exercises 9.1 (3) to (5), 9.2 and 9.5, and questions 3 to 5, 12 and 13.
4. Test for missing values with IS NULL and COALESCE, and say what a missing value means in an audit test. Practiced in Tutorial 9.2 (Steps 6 to 8), Exercises 9.3 (3), 9.4, 9.5 and 9.6, and question 6.
5. Sort and limit results to rank transactions. Practiced in Tutorial 9.3, Exercises 9.2 (4), 9.3 (5) and 9.4 (4), and questions 8 and 9.
6. Save queries in a documented script, check each result against what it should be, and explain what it means. Practiced in Tutorial 9.3 (Step 6), the script and memo of every exercise, and questions 11, 14 and 15.

## Preparing to teach
**Before the first class**

- Students need DB Browser for SQLite {{ version }} (Windows, macOS or Linux), the plain edition and not the SQLCipher edition that can be installed beside it. **Help > About** shows the version; Linux packages can be older.
- The download is several hundred megabytes and each student makes a copy, so allow disk space for both. Ask students to do Step 1 of Tutorial 9.1 before class.
- A late student takes Chapter09.sql from Chapter09-companion.zip, opens it with **Open SQL file(s)** on the **Execute SQL** tab, and still needs the working copy.
- Do the tutorials yourself, and open the model scripts once: each query has two comment lines, and the notes at the end repeat the requirements.
- Get the PowerPoint deck from the Downloads page. Each tutorial has a checkpoint slide.

**Pitfalls that cost class time**

- **The wrong file.** The title bar must end in CharlesRiver_Work.sqlite, and **Write Changes** and **Revert Changes** stay grayed out while students only read. A value typed in **Browse Data** is held until **Write Changes**; **Revert Changes** undoes it.
- **Nothing selected.** Running with no selection runs the whole script and shows only the last result.
- **Ctrl+S.** It is **Write Changes**, not a script save; the script is saved with **Save SQL file**.
- **A doubled extension.** File Explorer hides extensions, so a typed name ends up CharlesRiver_Work.sqlite.sqlite.
- **A very large result.** The AND and OR example returns {{ t2.wrong|count }} rows against {{ t2.right|count }} intended, and DB Browser loads results in blocks.

## Teaching approaches

**Plan A: lecture with live demonstration (three sessions of 80 minutes, 240 minutes in all).** It fits a lecture course with time at home for the exercises. Demonstrate the steps that carry the ideas and leave the rest to students.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The controller's question; standard costing | 2 to 7 |
| 1 | 10 | Why query a database; SQLite, DB Browser and the working copy | 8 to 14 |
| 1 | 10 | SELECT and the errors SQLite names | 15 to 19 |
| 1 | 15 | Aliases, arithmetic, functions and DISTINCT; the check and the answer | 20 to 26 |
| 1 | 35 | Tutorial 9.1: Steps 2, 4, 6 and 7 live; Steps 1, 3 and 5 for students | 27 to 32 |
| 2 | 20 | WHERE: operators, AND before OR, dates as text | 33 to 37 |
| 2 | 15 | NULL; the check and the answer | 38 to 42 |
| 2 | 45 | Tutorial 9.2: Steps 2, 4, 6 and 8 live | 43 to 46 |
| 3 | 10 | ORDER BY and LIMIT | 47 to 49 |
| 3 | 10 | Scripts, comments and Copy with Headers | 50 to 52 |
| 3 | 15 | Logical errors; the check and the answer | 53 to 58 |
| 3 | 35 | Tutorial 9.3: Steps 1, 4 and 6 live | 59 to 63 |
| 3 | 10 | The controller's question again; assign the exercises | 64 to 69 |
| | 240 | Total | |

**Plan B: lab first (one session of 180 minutes, with the exercises as homework).** Students write queries before they hear the vocabulary, so each finding arrives as a result they produced. It fits a computer lab; pairs take the Tutorial 9.2 start file when they fall behind.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Pose the controller's question and standard costing | 5 to 7 |
| 45 | Tutorial 9.1 in pairs, to the checkpoint | 27 to 32 |
| 10 | Debrief: AccountID against account number; the red message pane | 29, 30 |
| 40 | Tutorial 9.2 in pairs | 43 to 46 |
| 10 | Debrief: `= NULL`, the text year and the closing entry | 39 to 42, 45 |
| 35 | Tutorial 9.3 in pairs | 59 to 63 |
| 15 | Break it: run the four logical errors of the check slide and say what each result should be | 57, 58 |
| 15 | Debrief and assign the exercises | 64 to 68 |
| 180 | Total | |

**Plan C: flipped, with one 90-minute class.** Students read the chapter and build the tutorials at home, so the class opens with a quiz. It fits upper-level and graduate classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Quiz on questions 3, 5, 6, 9, 11 and 15 | |
| 25 | Review clinic: partners swap Chapter09.sql and agree the row counts of the checkpoints, {{ t1.accounts }}, {{ t2.rows|count }}, {{ t2.open_n }} and {{ t3.thr }} | 32, 46, 63 |
| 25 | Break it: `= NULL`, AND and OR, the text year, a missing comma | 25, 42, 58 |
| 20 | Start Exercise 9.4 or 9.6 in pairs | |
| 10 | Discussion prompts 2 and 3; assign the exercises | 68 |
| 90 | Total | |

Plan A is the safest, because most stumbles are mechanical. Plan B gives students ownership of the findings and needs a lab. Plan C leaves no time for demonstration and fails for students who arrive without a working copy.

{{ figure('IF-09-0-B') }}

## Tutorial guide
### Guided Tutorial 9.1: Opening the Database and Writing Your First Queries

**Purpose.** Students make the working copy, read the ledger's structure, start Chapter09.sql, run their first queries, make a deliberate error and check that the parts of every variance add up. **Time.** About 60 to 75 minutes, most of it setup. **Demonstrate, then hand over.** Demonstrate Step 2 (the title bar and the Database Structure tab), Step 4 (select, run, read the message pane) and Step 6 (the red message). Leave Steps 1, 3 and 5 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | Two identical files in the folder | the copy named exactly CharlesRiver_Work.sqlite |
| 2 | The path in the title bar, and Write Changes grayed out | the path ends in CharlesRiver_Work.sqlite |
| 4 | The Account result, and the message pane | {{ t1.accounts }} rows, "Result: {{ t1.accounts }} rows returned" |
| 5 | The AccountIDs of the two manufacturing accounts | {{ t1.clearing_id }} for account {{ t1.no.clearing }}, {{ t1.variance_id }} for account {{ t1.no.variance }} |
| 6 | A red message pane | no such column: AccountNumbr, and the line where the statement starts |
| 7 | One row for each work order close, and CheckDifference | {{ t1.n_close|count }} rows, zero in the first rows; {{ t1.raw_rows|count }} rows are not exactly zero before ROUND |

**Stumbles to expect**

- Step 1: the doubled extension.
- Step 2: the original file opened by mistake; the title bar is the check.
- Step 3: the script saved with Ctrl+S, so the editor tab is not renamed.
- Step 4: nothing selected, so the whole script runs.

**The checkpoint to look for.** The five bullets. A strong student says that the variance is recorded in the WorkOrderClose table and in the ledger, under an AccountID that differs from the account number.

### Guided Tutorial 9.2: Filtering the Ledger to the Variance Postings

**Purpose.** Students filter the ledger to the variance account, list its source document types, set the closing entry apart, test every close, and meet NULL and the text year. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (the filter), Step 4 (the closing entry, with its three variations), Step 6 (`IS NULL` against `= NULL`) and Step 8 (the text year). Leave Steps 1, 3, 5 and 7 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | The two accounts by number | 2 rows, AccountID {{ t1.clearing_id }} and {{ t1.variance_id }} |
| 2 | The year's postings to the variance account | {{ t2.rows|count }} rows |
| 3 | The source document types | 2 rows: WorkOrderClose and JournalEntry |
| 4 | The closing entry, then the WorkOrderClose condition | one row, {{ t2.close }}, a credit of ${{ t2.close_credit|money }} dated {{ t2.close_date }}; {{ t2.wo_rows|count }} rows with the other condition, one fewer than Step 2 |
| 5 | Closes whose parts differ from their total | no rows |
| 6 | Work orders with no ClosedDate, and the same with `= NULL` | {{ t2.open_n }} rows; no rows |
| 7 | The Completed label and ReleaseYear | not completed on the Released and In Progress work orders; {{ t2.year }} on every row |
| 8 | The year as a number, then as text | no rows; {{ t2.substr_text }} rows |

**Stumbles to expect**

- Step 2: the chapter's AND and OR example is worth running live: {{ t2.wrong|count }} rows without parentheses against {{ t2.right|count }}.
- Step 4: the condition left changed, so the script no longer keeps the query that finds the closing entry.
- Step 5: the empty result read as an error.
- Steps 6 and 8: `= NULL` and the numeric year left in the script.

**The checkpoint to look for.** The five bullets. A strong student says that the empty result in Step 5 is a finding and the empty result in Step 8 is a logical error, and explains how they tell the two apart: by knowing what the result should be.

### Guided Tutorial 9.3: Ranking the Largest Work-Order Variances

**Purpose.** Students rank the closes of the year, measure the share of overhead, look at the favorable end, apply a review threshold, copy a result into Excel and complete the script. **Time.** About 45 to 60 minutes. **Demonstrate, then hand over.** Demonstrate Step 1 (ORDER BY with LIMIT) and Step 4 (ABS in a condition). Leave Steps 2, 3, 5 and 6 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | The largest closes of the year, and the part that dominates | {{ t3.top_n }} rows from ${{ t3.top_max|money }} down to ${{ t3.top_min|money }}, overhead the largest part of each |
| 2 | OverheadShare | from `{{ t3.share_low }}` to `{{ t3.share_high }}`, above `0.80` in {{ t3.over }} of the {{ t3.top_n }} |
| 3 | The ascending ranking | favorable (negative) totals, the most favorable -${{ (t3.asc_low|abs)|money }} |
| 4 | Closes above the threshold either way | {{ t3.thr|count }} rows of {{ t3.n_year|count }}, {{ t3.fav }} of them favorable |
| 5 | The ten rows in Excel | headings and one value in each cell |
| 6 | The saved script | a completed header and a comment above each query |

**Stumbles to expect**

- Step 1: LIMIT without ORDER BY returns any ten rows.
- Step 2: no comma after `AS Total`, a syntax error.
- Step 3: DESC not restored, so the script keeps the wrong ranking.
- Step 4: a condition without ABS returns {{ t3.one_way|count }} rows, because it leaves out the favorable closes.
- Step 5: a plain copy instead of **Copy with Headers**, or no Ctrl+A first.

**The checkpoint to look for.** The five bullets. A strong student says that overhead carries most of the largest variances and that the question of which products carry them needs joins, which Chapter 10 brings.

## Difficult ideas and misconceptions
**A query that runs is not a query that is right.** Questions 5, 11 and 15, slides 54 to 58. Students trust any result. Ask: what should the result look like, and how many rows do you expect? The AND and OR example returns {{ t2.wrong|count }} rows where {{ t2.right|count }} are intended.

**An empty result is not always a finding.** Tutorial 9.2 Steps 5 and 8, and Exercises 9.1, 9.3 and 9.6. A test that returns nothing proves little unless it could have found something. Ask: where is the control query that returns rows?

**NULL is not a value.** Question 6 and Exercises 9.4 to 9.6. Students write `= NULL` or `= ''`. In Exercise 9.6 the same blank is normal for indirect time. Ask: what does a blank mean in this population?

**AccountID is not the account number.** Question 2 and Exercise 9.2. Ask: which table holds the number, and which key does the ledger carry?

**The closing entry sits among the postings.** Tutorial 9.2 Step 4 and Exercise 9.2. A total over every row is zero. Ask: what is the year's variance if the close stays in?

**Text must match exactly, and LIKE does not.** Question 3 and Exercise 9.2, where `%favorable%` also matches the unfavorable rows. Ask: what does DISTINCT say the stored value is?

**Dates and years are text.** Questions 4 and 15, Tutorial 9.2 Step 8 and Exercise 9.4. Ask: what type does SUBSTR return, and which side gets converted?

**ORDER BY decides which rows LIMIT keeps.** Questions 8 and 9, and Exercise 9.2 Step 5, where two amounts tie inside the ten. Ask: what happens at the tenth place if two amounts are equal?

{{ figure('IF-09-0-A') }}

## Discussion prompts
1. **The controller asks for the year's manufacturing variance, and the ledger holds a closing entry. Do you include it?** A good discussion reaches the entry's description, the fact that the year nets to zero with it, and the rule that an entry which adjusts the variance belongs in the analysis.
2. **A test returns no rows. What goes in the workpaper?** It reaches the population, the condition, a control query that proves the test can find something, and what the clean result leaves open.
3. **Hundreds of work orders are past due and marked Released. Is the status wrong or the plant late?** It reaches both possibilities, the evidence in other tables that Chapter 10 can join, and the people to ask.
4. **The same question could be answered in Excel or in SQL. How do you choose?** It reaches the size of the data, related tables, repeatability and traceability, and the fact that professionals use both.
5. **A saved script is a workpaper. What must it hold for a stranger to rerun it next year?** It reaches the header, the dates typed into the conditions, the comment above each query and the checks, as the Documentation worksheet of Chapter 4 did.
6. **Exercises 9.4 to 9.6 each end with a question for a process owner. Who, and in what tone?** It reaches payroll, production and shipping, and the auditor's job of asking for evidence, not assigning blame.

## Using the exercises

All six exercises are SQL scripts with a model answer in Chapter09-exercises-sql.zip. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 9.1 Reviewing the Chart of Accounts | Financial | SQL | 75 | Basic | 2, 3, 6 |
| 9.2 The Purchase Price Variance in the Ledger | Financial | SQL | 60 | Intermediate | 3, 5, 6 |
| 9.3 Standard Cost Components of Manufactured Items | Managerial | SQL | 60 | Intermediate | 2, 4, 5, 6 |
| 9.4 Open Work Orders at Year-End | Managerial | SQL | 75 | Intermediate | 2, 4, 5, 6 |
| 9.5 Shipments That Need Follow-Up | Auditing | SQL | 45 | Basic | 3, 4, 6 |
| 9.6 Missing Values in Time and Labor Records | Auditing | SQL | 60 | Intermediate | 3, 4, 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 9.1 and 9.2, managerial students 9.3 and 9.4, auditing students 9.5 and 9.6. A swap of memos lets each track hear the others; all three tracks meet the variance accounts, the open work orders and the labor records.
- *One exercise a session.* Take the basic exercises first: 9.5, 9.1, 9.3, 9.2, 9.6, 9.4.
- *A light load.* Exercises 9.4 and 9.5 take about two hours and cover outcomes 2 to 6.

**Grading and discussion.** Each exercise guide holds a rubric. Exercises 9.3 and 9.5 suit grading from the script and the row counts, because their numbers have one answer. Exercises 9.1, 9.4 and 9.6 end in a memo or findings and suit class discussion. Collect the script, not a screenshot: its comment lines show the population and the expected result, and the query shows exactly what was tested.

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 2.** Option A says SQLite stores account numbers as text. AccountNumber is an INTEGER; the reason is that the ledger holds the surrogate key.
- **Question 5.** Option A is what the analyst intended; the point is that AND is evaluated first.
- **Question 6.** Option D denies that SQL can test for a missing value; IS NULL can.
- **Question 10.** Option C credits **Write Changes** with saving every result; a SELECT changes nothing.
- **Question 11.** Option A expects an error, and the missing comma makes the second name an alias.
- **Question 13.** Option B uses `=` with a wildcard, and option C a pattern whose `_` stands for exactly one character.
- **Question 15.** Option A keeps Excel's 3.5 for the first division and treats the text `'2026'` as equal to the number.
{% if n_longest %}
- **Length.** The correct option is also the longest in {{ n_longest }} of the {{ n_questions }} questions ({{ longest_correct }}), so wording alone can give it away. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1, 7 and 13 make a quiz of SELECT, DISTINCT and LIKE, questions 2 to 5 and 12 of the filters, questions 6 and 15 of NULL and types, and questions 8 to 11 and 14 of ranking, copies and scripts.

## Connections
**Builds on.** Chapter 1's comparison of Excel and SQL, Chapter 2's missing values and the shipment filters of Tutorial 2.1 that Exercise 9.5 repeats, and Chapter 3's tables, keys and the surrogate key that makes AccountID differ from the account number. Chapter 4's Documentation worksheet is the ancestor of the script header. Chapter 6 supplied the ledger to statements and the year-end close that Tutorial 9.2 sets apart, and Chapter 8 the habit of testing records for planted anomalies.

**Later chapters.** Chapter 10 joins and summarizes the tables, so the counts students read from the message pane become COUNT and the orphaned labor keys of Exercise 9.6 are found with a join. Chapter 11 adds dates, windows and views in the same working copy, and Chapter 12's audit library turns tests like Exercises 9.5 and 9.6 into a rerunnable script. The Part III case follows. Chapter 16 rebuilds the exception tests in Power BI.

**Appendices.** The quick reference lists the SQL functions of this chapter beside their Excel and DAX counterparts. **Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard; each exercise guide names the competencies it practices.
