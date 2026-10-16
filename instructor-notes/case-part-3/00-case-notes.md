# Comprehensive Case, Part III: Planning the Plant's Hours for 2027

| | |
|---|---|
| Unit | Case Part 3: Planning the Plant's Hours for 2027 |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 150 minutes of class time |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part III, Accounting Analytics with SQL. The case closes the Part and integrates Chapters 9 to 12 |
| Analytics types | The case text does not label them. Read together: descriptive (Requirement 1), diagnostic (Requirements 2 and 3), predictive and prescriptive (Requirements 4 to 6) |
| Tools | SQL only, in DB Browser for SQLite: CASE, conditional aggregation, window functions and frames, CTEs, views and date functions |
| Components | Six requirements, no tutorials, no milestones and no multiple-choice questions; the deck has 33 slides; the model script has 71 queries and 8 saved views |
| Files students need | CharlesRiver_Work.sqlite (Chapter 9's working copy); the script they write, `Case.sql`; Audit.sql from Chapter 12 (tests H9, L5, L6, L8); Tutorial 11.3's view, or Setup_Part3_Views.sql from the Downloads page. The solution is PartIII-case-sql.zip |
| Deliverable | A memo of at most two pages to the controller, a one-page appendix of five exhibits, and Case.sql with its header and a comment above every query |
| Time | Class: about 150 minutes in Plan A. Students: about 13 hours, from 90 minutes for Requirement 6 to 150 for each of Requirements 2 to 4 |

The case depends on these conditions of the data, all visible in the working copy:

- The plant has 64 hourly employees with a time clock. On 93 days (12, 32, 49 by year) all of them recorded the same hours, the surge days, which carry 5,952 entries and the growth in overtime.
- The punches behind each clock entry repeat its times; the rosters and the overtime approvals come from the Production Manager. The work center calendar, the capacity plan and the output lie outside the time clock, though the records do not show who keeps them.
- Time records end on 2026-12-11 (indirect labor time on 2026-12-04), the calendar on 2027-03-25; payroll posts on pay dates, with no accrual at any year-end.
- The plant's output is about 53% of its regular employee-hours, and the budget plans three times the units it completed.
- All 18 attendance exceptions are Open and never reviewed, and four of them name the wrong employee.
- Account 2030 carries an opening balance of 95,000.00 that no payroll ever cleared, and the ledger records no income tax.

## What students should be able to do afterward

1. Build a script that another person can rerun: a header, a two-line comment on every query, profiles of new tables, link tests and views, each population reconciled before it is used. Practiced in Requirement 1.
2. Test a claim against records outside its source, grade each record for independence, reperform a control and place its failure in design or operation. Practiced in Requirement 2.
3. Compare output with hours on the right calendars, cost the overtime two ways, and bridge a ledger account into lines that sum to its change. Practiced in Requirement 3.
4. Document a plan's assumptions in one place, check it against capacity, and read three scenarios and the variance left at standard hours. Practiced in Requirement 4.
5. Accrue unrecorded payroll by working day, separate the effect on income from the effect on the balance sheet, and apply the inventory standard to idle capacity. Practiced in Requirement 5.
6. Write a short memo that answers a reader's questions in order, keeps its wording within its evidence, and ends with a recommendation. Practiced in Requirement 6.

## Preparing to teach

**Before the first class**

- Check the software. The model script uses CTEs, window frames, `julianday` and `strftime`, so students need the DB Browser for SQLite release the chapters use. Each model query finished in seconds when run through Python's sqlite3 on the working copy; time a few in DB Browser.
- Ask students to confirm three things in their working copy: Tutorial 11.3's view exists, Audit.sql is at hand, and the original download is untouched. A student without the view runs Setup_Part3_Views.sql once and selects **Write Changes**. Views the case creates persist only after **Write Changes**.
- Run the model script once from the top, or build your own answer. Its views are created in order, each after a `DROP VIEW IF EXISTS`; note the time it takes.
- Open the deck. Slides 5 to 6 set out the criteria, which are the six bullets of "What a Strong Submission Includes"; read them aloud at kickoff.

**Pitfalls that cost class time**

- Three calendars (slide 14; the check on slides 15 and 16). Time records follow the work date and end on 2026-12-11; the ledger follows the pay date, which put 24 payrolls in the first year and 26 in the last; output follows the completion date and includes weekends. Mixing them is the commonest error: the last year reads 1.511 hours per standard hour when output is cut off at the last time record, and a different figure when it is not.
- Dates without days and fan-out (slide 17). Roster times carry no date, and a late shift clocks out the next day. Each clock entry has two to four punches, RoughCutCapacityPlan repeats a work center's hours on every item row, and WorkCenterCalendar has a row for each work center and date. Summarize each side before the join.
- The plant's 64 hourly employees, not the cost center's 67: the salaried staff keep no time clock, so a headcount from the cost center breaks the attendance test and the capacity.
- Correlated subqueries on TimeClockPunch, which has no index on TimeClockEntryID. A query that runs for minutes is almost always one of these, or a join that was not summarized.
- Word choice. Students reach for fictitious, fraud or proof. The deck's slide 10 sets the rule; repeat it at Requirement 2.

![The three calendars of the case, which must not be mixed.](../figures/case-part-3/IF-C3-0-B.pdf)

## Teaching approaches

**Plan A: take-home work with four class touchpoints (150 minutes in class).** It fits a lecture course that wants the case done mostly outside class and catches the errors that compound: the populations, the independence grading and the plan. The risk is a late start, so assign Requirements 1 and 2 at kickoff.

| Touchpoint | Minutes | Activity | Slides |
|---|---:|---|---|
| 1. Kickoff | 10 | The question, the deliverable and the criteria | 3 to 6 |
| 1. Kickoff | 10 | The situation and the wording rule | 8 to 10 |
| 1. Kickoff | 10 | The data, the three calendars and the check | 12 to 17 |
| 2. Checkpoint | 15 | Requirement 1: compare reconciliations | 20 |
| 2. Checkpoint | 25 | Requirement 2: the window result, the rule and the matrix; assign Requirements 3 and 4 | 21 to 23 |
| 3. Checkpoint | 20 | Requirement 3: output against hours, and the bridge | 24 |
| 3. Checkpoint | 20 | Requirement 4: the scenarios; assign Requirements 5 and 6 | 25 |
| 4. Debrief | 20 | Requirement 5: the accrual, income against balance sheet, the inventory standard | 26 to 28 |
| 4. Debrief | 15 | Requirement 6: read two openings; state the recommendation | 29, 30 |
| 4. Debrief | 5 | Looking ahead to Part IV | 32 |
| | 150 | Total | |

**Plan B: lab sessions (three sessions of 120 minutes, 360 minutes in all).** Students work in class and you circulate. It fits a computer lab or a course that does not want to depend on outside work. Requirements 4 to 6 go home, and the memo is collected the week after.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 15 | Kickoff: the question, the criteria and the wording rule | 3 to 10 |
| 1 | 15 | The data and the Watch outs | 12 to 17 |
| 1 | 90 | Requirement 1: header, profiles, links, views | 20 |
| 2 | 100 | Requirement 2: the surge-day comparison, the rule, the plans and the approvals | 21 |
| 2 | 20 | The matrix and the independence check | 22, 23 |
| 3 | 90 | Requirement 3: the weekly view, the cost and the bridge | 24 |
| 3 | 30 | Requirement 4: the depreciation and the Params CTE | 25 |
| | 360 | Total | |

**Plan C: memo workshop (90 minutes).** Students arrive with Requirements 1 to 5 done. It fits an upper-level or graduate class and moves the learning to the writing. Its risk is that an early error is found late, so collect the tables of Requirements 2 to 5 the day before and mark them.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval: each pair states the independence finding, the cost, the plan and the adjustments | 19 |
| 10 | Each pair states its recommendation in one sentence; the room compares | 29 |
| 30 | Draft the opening and the Auditing section in pairs from the Requirement 6 outline | 29 |
| 30 | Swap drafts and review them against the Requirement 6 grading guide | 30 |
| 10 | Looking ahead to Part IV | 32 |
| 90 | Total | |

## Difficult ideas and misconceptions

- **Unsupported is not unworked.** The records fail to support the hours as recorded; they do not show that no one worked. Students write fictitious, or call the hours proved because every employee was present (576 of 652 ordinary days also had everyone). Ask which record is independent and what each explanation predicts.
- **Agreement is not corroboration.** The punches equal the clock entry's times on all but nine entries, so they repeat the clock, and a separate table is not by itself an independent source. Ask who produced each record.
- **The stored exceptions point to a rule; they do not show it.** The three Off Shift exceptions are consistent with a rule on arrival, which could not flag surge entries 30 minutes early and 240 minutes late, but three examples cannot show its threshold or scope. A student who applies it to departures concludes the opposite, and one who states the rule as proven overreaches. Ask what the configuration would add.
- **Three calendars.** Hours by work date, cost by pay date, output by completion date. It shows as 1.511 against a lower figure when output is not cut off, and as a payroll measure 106,612 above the payroll line. Ask what date each record carries.
- **A bridge is not a set of measures.** The ledger lines sum to the 947,709.56 growth of 5080; the three measures overlap and do not. Ask which are ledger lines.
- **A scenario is not a forecast.** The expected variances (730,432, 1,107,366, 2,104,714) are what each ratio would produce, and the budget's volume would have put the plan 81,903 hours beyond regular capacity. Ask what each ratio assumes.
- **Two accruals nearly cancel in income and not on the balance sheet.** Income moves 17,123.63; the liability moves 383,044.82. Ask what opening retained earnings would then claim.
- **Abnormal cost belongs in the period.** The actual conversion cost was 78.77 per standard hour against 47.40; raising the standards would carry idle capacity and unsupported hours into 12,169,701.74 of finished goods. Ask where an abnormal cost goes, and how much of the difference is abnormal.
- **A saved view is not saved until Write Changes.** The next session fails with "no such table". Ask whether the changes were written.

## Discussion prompts

1. The Production Manager creates the rosters and approves the overtime. What would a second approver add, and what would it cost? A good discussion reaches segregation of duties and the difference between design and operation.
2. The plant clocked 101,237 hours in the last year against 66,998 standard hours. What would you want to know before calling the difference inefficiency? A good discussion reaches idle capacity, the standards and how output is dated.
3. The overtime was paid on each employee's own register. Does that settle whether the hours were worked? A good discussion reaches the difference between payment and evidence.
4. The two accruals nearly cancel in income, yet the liability left out is 8.5% of net income and recurs every year. Is the error immaterial? A good discussion reaches materiality judged on each error, the balance sheet and the deficiency in the close.
5. Should the overhead rate rise to absorb idle capacity? A good discussion reaches the inventory standard, normal capacity and what a standard is for.
6. Which single record would you ask for first to settle the two explanations, and from whom? A good discussion reaches independence and access.
7. What would you monitor next month, and how would the saved views help? A good discussion reaches repeatable scripts and the move to dashboards in Part IV.

## Using the requirements

| Requirement | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1. Build the script and its populations (Chapters 9 and 10) | General | SQL | 120 min | Intermediate | 1 |
| 2. Test whether other records support the surge days (Chapters 10 to 12) | Auditing | SQL | 150 min | Advanced | 2 |
| 3. What the hours produced and what they cost (Chapters 10 and 11) | Managerial | SQL | 150 min | Advanced | 3 |
| 4. Plan the 2027 hours and conversion cost (Chapter 11, with Chapter 7) | Managerial | SQL | 150 min | Intermediate | 4 |
| 5. Close the fiscal 2026 statements (Chapters 11 and 12) | Financial | SQL | 140 min | Intermediate | 5 |
| 6. Write the decision memo | General | Written, with SQL exhibits | 90 min | Advanced | 6 |

Every requirement is part of the case, and each depends on the first. The figure shows how their results feed the memo and its appendix.

![How the six requirements build the memo and its appendix, and the chapters each one draws on.](../figures/case-part-3/IF-C3-0-A.pdf)

Three bundles:

- **The full case (the default).** All six requirements, graded with the rubric below. About 13 hours.
- **A shorter version for an audit course.** Requirements 1, 2 and 5 and a one-page memo on their sections. It skips the plan.
- **Teams of three.** One script and one memo for the team, with one student leading each perspective (Requirement 2 for auditing, Requirements 3 and 4 for managerial accounting, Requirement 5 for financial reporting), and an individual one-page reflection on the recommendation.

The check slides on calendars, independence and the inventory standard suit class discussion. Requirements 1 and 5 suit grading from the script and its tables, Requirements 2 to 4 from the exhibits, and Requirement 6 from the memo. A fast way to grade the script is to run it top to bottom on a fresh copy of the database and compare each reconciliation with the Expected results of the requirement guide.

## Assessment rubric

| Requirement | Weight | What carries the points |
|---|---:|---|
| 1. Script and populations | 10 | Header and comments, profiles with blanks and keys, link tests, two views, a reconciliation that agrees |
| 2. Other records | 20 | Surge against ordinary days, the rule reperformed, plans and approvals tested, a matrix graded for independence, two explanations |
| 3. Hours and cost | 20 | Output against hours on the right calendars, the frame, two costs, a bridge that sums, measures with the reason they overlap |
| 4. The plan | 15 | Assumptions in one place, depreciation reproduced, capacity checked, three scenarios, the standards decision |
| 5. The close | 15 | Accrual by working day, both accruals, income against balance sheet, the inventory standard, cutoff and materiality |
| 6. The memo | 20 | Order of the questions, accuracy, wording, a usable recommendation, five exhibits, length |
| Total | 100 | |

Four criteria run through every requirement.

| Criterion | Full credit looks like | Assessed mainly in |
|---|---|---|
| Accuracy | Populations reconcile, queries summarize before joining, calendars are respected, no silent fan-out | Requirements 1, 3 and 5 |
| Evidence | Every number in the memo traces to a query, and records are graded for independence | Requirements 2 and 6 |
| Judgment | Design separated from operation, a scenario read as a scenario, the inventory standard applied, materiality judged | Requirements 2, 4 and 5 |
| Communication | A memo in the order of the questions, within two pages, careful with the word unsupported, ending in a recommendation | Requirement 6 |

Each requirement guide has its own grading table out of 100; scale it by the weight above to place it in the case grade.

## Connections

**Builds on.** Chapter 9 supplies the working copy, the script header and the habit of a comment on every query. Chapter 10 supplies the data profile, joins, aggregates and the measure of the plant (hours per standard hour, Tutorial 10.3). Chapter 11 supplies CASE, dates, windows and frames, CTEs and the saved view (Tutorials 11.2 and 11.3, with the pay dates). Chapter 12 supplies the tests the case reuses: H9's surge days, L5 and L6's cutoff and L8's account 2030, with Exercises 12.1, 12.3 and 12.5 as neighbors. Chapter 7 supplies the documented model and the flexible budget, Chapter 6 the income statement the adjustments start from, and Chapter 8 the unsupported opening balances. The Part II case supplies the memo form. The finished guides for Chapters 9 to 12 hold the tutorial and exercise detail each requirement here relies on.

**What builds on it.** Part IV turns results like these into reports managers can explore: Chapter 15 builds the plant page and the trailing hours per standard hour in Power BI, and Chapter 16 monitors exceptions in a register. The script and its views can run again on new records once their dates are moved forward and the coverage checks repeated, which is the bridge to both.

**Appendix D** maps each requirement to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each requirement guide names the competencies it practices.
