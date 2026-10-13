---
uses: [case1.chapter]
title: 'Comprehensive Case, Part 1: Getting the Data Ready for the Furniture Margin Question'
kind: case-notes
unit: case1
minutes: 120
tool: conceptual
figures:
  - id: IF-C1-0-A
    kind: diagram
    purpose: How the six requirements feed the memo and its appendix, and which workflow stages the case completes.
    shows: Six boxes in a row for the requirements, each tagged with the chapter it draws on (Chapter 1, Chapter 3, Chapter 2, Chapters 2 and 3, none, none). Arrows run from Requirements 2 and 4 into a box labeled "Appendix with the data map and the reconciliation table", from Requirements 3 and 4 into the memo section "Financial reporting", from Requirement 5 into "Managerial accounting" and "Auditing", and from all of them into the memo. Beneath the boxes, a strip of the six workflow stages with stages 1 to 3 and the readiness part of stage 6 filled and stages 4 and 5 outlined and labeled "Part II".
    data: none; the boxes and tags come from the case's requirements and the stage list of Chapter 1.
  - id: IF-C1-0-B
    kind: diagram
    purpose: Where the quarter to analyze sits on the extract's timeline, and why the latest rows of the ledger are not it.
    shows: A horizontal timeline from the first posting date of the ledger to its last. Three bars sit above it, for the sales invoices, the shipments and the ledger. The invoice and shipment bars end at the last day of the current fiscal year, and the ledger bar runs on past it to a short tail labeled "only supplier payments". The third and fourth quarters of the current fiscal year are shaded as the quarters to compare, and a marker on the last day of the year is labeled "year-end close".
    data: The first and last PostingDate of GLEntry, the last InvoiceDate and the last ShipmentDate, and the posting date of the year-end close (the Expected results of Requirements 3 and 5).
---
{% set g = case1_chapter %}
# Comprehensive Case, Part 1: Getting the Data Ready for the Furniture Margin Question

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part I, Foundations of Accounting Analytics. The case closes the Part and integrates Chapters 1, 2 and 3 |
| Analytics types | Students name the descriptive and the diagnostic question (Requirement 1) and do the descriptive work, the margin of each quarter. The diagnosis itself is left for Part II |
| Tools | Excel only, in the Part I working copy: filters, XLOOKUP and MINIFS helper columns, and PivotTables. No SQL and no Power BI |
| Components | The case has {{ g.n_req }} requirements, no tutorials, no milestones and no multiple-choice questions, and its deck has {{ g.slides }} slides |
| Files students need | CharlesRiver_Work.xlsx, the working copy that Tutorial 2.1 makes from CharlesRiver.xlsx. The Downloads page lists no start file and no solution for this case; the model answers are in the files of this folder |
| Deliverable | A memorandum of one to two pages to the controller, and a one-page appendix with the data map (Requirement 2) and the reconciliation table (Requirement 4) |
| Time | Class: about 120 minutes in Plan A. Students: about four and a half hours, from 20 minutes for Requirement 1 to 60 minutes for each of Requirements 4 and 6 |

The case depends on these conditions of the data, all visible in the workbook:

- The ledger has {{ g.rows.GLEntry|count }} rows and runs from {{ g.first_post }} to {{ g.last_post }}. Invoices and shipments end on {{ g.last_invoice }}, and the {{ g.late_rows }} ledger rows of fiscal {{ g.next_year }} are all supplier payments.
- Every Furniture item posts its revenue, its cost of goods sold and its inventory to one account each, so the product line is a clean selection of ledger rows.
- The Furniture invoice lines and shipment lines of the two quarters equal their ledger postings to the cent.
- The year-end closing entry posts to both Furniture accounts on the last day of the last quarter, which turns a naive Q4 margin into a plausible-looking ratio on negative totals.
- A return posts its cost to the product line's account but its revenue to an account shared by every product line.
- The Chapter 2 cutoff findings exist, but none of the Furniture invoices among them falls in either quarter.

## What students should be able to do afterward

1. Restate a business request as a descriptive and a diagnostic question, name the type of analytics of each, and mark which stages of the six-stage workflow the work completes. Practiced in Requirement 1.
2. Find where a product line's revenue and cost are recorded (item group, then account ID, then account number), and name the key and the cardinality of every join on the path from a document to the ledger. Practiced in Requirement 2.
3. Choose the quarters of a comparison from the edges of the extract, and decide for each known data quality finding whether it could distort that comparison. Practiced in Requirement 3.
4. Reconcile a sub-ledger to the ledger for two quarters, and say what agreement shows and what it leaves open. Practiced in Requirement 4.
5. Read the totals behind a percentage, trace an odd total to the entry and source document type behind it, and recompute the measure without it. Practiced in Requirement 5.
6. Write a short memo that reports readiness by perspective, states the limits of the data and ends with a recommendation. Practiced in Requirement 6.

## Preparing to teach

**Before the first class**

- Ask each student to confirm that CharlesRiver_Work.xlsx exists and opens. A student who skipped Tutorial 2.1 can copy CharlesRiver.xlsx and rename the copy in two minutes; the download itself stays unchanged for Parts II and IV.
- Check the Excel version. The model paths use XLOOKUP and MINIFS, which Tutorials 2.1 and 2.2 already introduced, so a student who completed them has what the case needs.
- Build your own answer workbook once, in about an hour, following Requirements 2 to 5. Part I has no solution file. The values in these guides were checked with equivalent database queries, and the Excel formulas follow the Part I tutorials but were not run in Excel for these notes, so run each helper column and PivotTable in your own copy before class.
- Rehearse the PivotTables on GLEntry, the largest worksheet ({{ g.rows.GLEntry|count }} rows). The first PivotTable takes a moment to build; say so, so that students do not think Excel has frozen. The Watch out in Tutorial 2.2 and in the case says to summarize GLEntry rather than copy formulas down every row.
- Open the deck (slides {{ g.slide.question }} to {{ g.slide.handin }} set out the question and the deliverable). The criteria slides ({{ g.slide.judged }}) are the six bullets of "What a Strong Submission Includes"; read them aloud at kickoff.

**Pitfalls that cost class time**

- AccountID is not the account number. A student who filters the AccountID column of GLEntry for an account number finds no rows. The Watch out on slide {{ g.slide.watch }} says so; repeat it at the first lookup.
- A PivotTable ignores the filters of the worksheet it reads. A student who filters SalesInvoiceLine to Furniture and then builds a PivotTable still sums every group. Put the item group in the PivotTable's own filter area.
- The helper columns must be filled to the last row of the Table, or the PivotTable totals come out short by the rows that are blank.
- Students read the quarter from FiscalPeriod (periods {{ g.periods3 }} for the third quarter, {{ g.periods4 }} for the fourth) or from a date helper. Either is right, because a fiscal period is a calendar month; make them say which they used.
- Revenue is a credit balance. A student who subtracts credits from debits for the revenue account reports a negative revenue in every quarter, and then finds the Q4 trap hidden by the sign.

## Teaching approaches

**Plan A: take-home work with three class touchpoints (120 minutes in class).** It fits a lecture course that wants the case done mostly outside class, and it catches errors at the two points where they compound: the data map and the reconciliation.

| Touchpoint | Minutes | Activity | Slides |
|---|---:|---|---|
| 1. Kickoff | 10 | The controller's question, the deliverable and the six criteria | {{ g.slide.opening }} |
| 1. Kickoff | 10 | The situation, the three chapters, the worksheets and the AccountID Watch out | {{ g.slide.situation }}, {{ g.slide.data }} |
| 1. Kickoff | 15 | Requirement 1 together, with the classification check and its answers | {{ g.slide.r1 }} |
| 1. Kickoff | 5 | Assign Requirements 2 to 4 for the second touchpoint | |
| 2. Checkpoint | 15 | Compare data maps and the choice of quarters; the one-or-many check | {{ g.slide.r2 }}, {{ g.slide.r3 }} |
| 2. Checkpoint | 20 | Compare reconciliation tables to the cent and say what agreement shows; assign Requirements 5 and 6 | {{ g.slide.r4 }} |
| 3. Debrief | 20 | Requirement 5: the PivotTable by source document type, the naive margin and the corrected one | {{ g.slide.r5 }} |
| 3. Debrief | 15 | The memo: three sections and a recommendation; read two anonymized openings | {{ g.slide.r6 }}, {{ g.slide.before }} |
| 3. Debrief | 10 | Looking ahead to Part II | {{ g.slide.ahead }} |
| | 120 | Total | |

**Plan B: lab sessions (two sessions of 75 minutes, 150 minutes in all).** Students work in class and you circulate. It fits a computer lab or a course that does not want to depend on outside work. Requirement 4 is tight, so hand out the helper-column formulas of that guide at the start of session 2, and let the memo be written outside class.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Kickoff: the question, the deliverable, the criteria and the Watch out | {{ g.slide.question }} to {{ g.slide.watch }} |
| 1 | 10 | Requirement 1 individually, then pair and compare | {{ g.slide.r1 }} |
| 1 | 25 | Requirement 2: Item and Account, then the join sketch and the returns | {{ g.slide.r2 }} |
| 1 | 30 | Requirement 3: the edges of the extract and the findings | {{ g.slide.r3 }} |
| 2 | 35 | Requirement 4: helper columns, two PivotTables for each side, and the table | {{ g.slide.r4 }} |
| 2 | 25 | Requirement 5: the PivotTable by source document type, then recompute | {{ g.slide.r5 }} |
| 2 | 15 | Plan the memo from the outline in the Requirement 6 guide; assign it | {{ g.slide.r6 }} |
| | 150 | Total | |

**Plan C: memo workshop (one session of 75 minutes).** Students arrive having done Requirements 1 to 5 and bring their tables. It fits an upper-level or graduate class, and it moves the learning to the writing. Its risk is that an early mistake is found late, so collect the reconciliation table the day before and mark it.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval: each pair states its two margins and the two reconciliation differences; resolve disagreements | {{ g.slide.r4 }}, {{ g.slide.r5 }} |
| 15 | The question to the room: what would you tell the controller about a Q4 margin of {{ g.naive_q4|pct(1) }}? | {{ g.slide.r5 }} |
| 25 | Draft the opening and the Auditing section in pairs, from the outline | {{ g.slide.r6 }} |
| 20 | Swap drafts; review against the grading guide of Requirement 6 | {{ g.slide.before }} |
| 5 | Looking ahead to Part II | {{ g.slide.ahead }} |
| 75 | Total | |

## Difficult ideas and misconceptions

- **A surrogate key is not a business key.** It shows as a filter on GLEntry that returns nothing, or as a lookup of the wrong account. Send the student to the Account worksheet and ask them to read the AccountID and AccountNumber side by side.
- **The latest rows are not the latest complete period.** A student picks the quarter that holds the last rows of the ledger. Ask what the ledger holds after {{ g.last_invoice }}: supplier payments only, no sales and no shipments, so there is no margin to compute.
- **Agreement proves too much.** Students write that a tie-out shows the data is complete and right. It shows that what was invoiced and shipped reached the ledger at the same amounts. It does not show that every sale was invoiced, that prices and dates are right, or that revenue and cost are matched in time. The Requirement 4 guide gives the cases the data holds.
- **A believable ratio can hide nonsense totals.** The naive Q4 margin of {{ g.naive_q4|pct(1) }} is about the Q3 figure of {{ g.m3|pct(1) }}. Make students say what a negative revenue means before they accept the percentage.
- **Exclude an entry for a reason, not for its size.** A student drops the closing entry because it is large. The reason is its nature: it moves balances to an income summary and belongs to no quarter's operations. Excluding every journal entry would work here only because the closes are the only journal entries on the two accounts, and it would be wrong where adjusting entries exist.
- **Not every finding matters for every question.** Students either list all findings as threats or dismiss all of them. A finding matters when it touches the population, the period or the measure of this comparison. The same finding may matter for another question.
- **Description is not diagnosis.** A memo that says what drove the margin down claims what the analysis has not yet been asked. The case answers the descriptive question and prepares the diagnostic one.
- **A shared account limits a product-line margin.** Students notice that returns reach the revenue side through one account, and stop. The source trace reaches the product line anyway, through the credit memo line, which the Requirement 2 guide shows.

The timeline shows the second idea at a glance, and is worth putting on the board when students choose their quarters.

{{ figure('IF-C1-0-B') }}

## Discussion prompts

1. The naive Q4 margin looks fine. What would you have to see before you trusted it? A good discussion reaches the habit of reading the totals behind a ratio and checking their sign and scale.
2. Why is the last day of the fiscal year different from any other day? A good discussion reaches closing entries, year-end adjustments and cutoff, and why an auditor looks at the last and first days of a year.
3. If the sub-ledger and the ledger agree to the cent, can you rely on the data? A good discussion separates tests of completeness and accuracy from tests of agreement, and names what other evidence would add.
4. Which of the Chapter 2 findings would matter if the controller asked about customers instead of products? A good discussion links each finding to the population and the measure of a question.
5. Revenue on a return posts to one account for all product lines. How would you report Furniture's margin, before returns or after them? A good discussion weighs a simple ledger measure against a more exact one found by tracing, and ends with a stated choice.
6. What do you hand the analyst who will do the Part II diagnosis? A good discussion reaches the data map, the definition of the margin measure, the rows to exclude and the open questions.
7. The memo goes to the controller. What would you leave out of it, and where would that material go? A good discussion distinguishes the memo from its appendix and from working papers.

## Using the requirements

| Requirement | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1. Frame the question (Chapter 1) | General | Written | 20 min | Basic | 1 |
| 2. Map the data (Chapter 3) | General | Excel | 45 min | Intermediate | 2 |
| 3. Test the data (Chapter 2) | General | Excel | 40 min | Intermediate | 3 |
| 4. Reconcile the sub-ledger to the ledger (Chapters 2 and 3) | General | Excel | 60 min | Advanced | 4 |
| 5. Find what could mislead (Auditing) | Auditing | Excel | 45 min | Intermediate | 5 |
| 6. Write the data readiness memo | General | Written | 60 min | Advanced | 6 |

Every requirement is part of the case; none is optional, and each depends on the one before. The figure shows how their results feed the memo and its appendix.

{{ figure('IF-C1-0-A') }}

Three bundles:

- **The full case (the default).** All six requirements, graded with the rubric below. About four and a half hours.
- **A shorter version for a course with little time.** Requirements 2 to 5 as a worksheet, graded on the numbers, and a memo of one page. It skips Requirement 1 and shortens Requirement 6 to the Auditing section and the recommendation.
- **Teams of two or three.** One memo and one appendix for the team, plus an individual one-page reflection on Requirement 5.

The deck's check slides on question types, cardinality and data quality dimensions suit class discussion. Requirements 4 and 5 suit grading from the tables and Requirement 6 from the memo. Collect, besides the book's deliverable, one page of working notes with Requirements 1, 3 and 5: the book's deliverable carries only Requirements 2, 4 and 6, and those three would otherwise go ungraded. This is a suggestion, not a rule of the case.

## Assessment rubric

| Requirement | Weight | What carries the points |
|---|---:|---|
| 1. Frame the question | 10 | Two distinct questions, each with its type, and the stages marked with reasons |
| 2. Map the data | 15 | Account numbers and keys correct, every join with its cardinality, and the returns explained |
| 3. Test the data | 15 | The two quarters chosen from the edges of the extract, and a reasoned judgment on each finding |
| 4. Reconcile | 20 | Both sides, both quarters, to the cent, with what agreement shows and what it does not |
| 5. Find what could mislead | 15 | The naive margin and its totals, the entry traced to its EntryType, and the corrected margins |
| 6. The memo | 25 | Organization, accuracy, judgment, length and a usable recommendation |
| Total | 100 | |

Four criteria run through every requirement.

| Criterion | Full credit looks like | Assessed mainly in |
|---|---|---|
| Accuracy | Keys, account numbers and totals right, and the reconciliations agreeing to the cent | Requirements 2, 4 and 5 |
| Evidence | Every number in the memo traces to a filter, a lookup or a PivotTable, and the student says what agreement shows | Requirements 3, 4 and 6 |
| Judgment | The right quarters, the right findings, the correct treatment of the closing entry, and the limits of the data named | Requirements 3, 5 and 6 |
| Communication | A distinction between what the case settles and what Part II must analyze, and a memo that a controller can act on | Requirements 1 and 6 |

The six bullets of "What a Strong Submission Includes" map one to one onto the requirements: the types and the stages to Requirement 1, the data map to 2, the choice of quarters to 3, the reconciliations to 4, the hidden totals and the closing entry to 5, and the memo to 6. Each requirement's guide has its own grading table out of 100; scale it by the weight above to place it in the case grade.

## Connections

**Builds on.** Chapter 1 supplies the four types of analytics and the six-stage workflow (the case's Requirement 1), and its Exercise 1.4 frames questions the same way. Chapter 2 supplies the data quality dimensions, the edges of an extract and the findings of Tutorial 2.1 (Requirements 3 and 4), with Exercises 2.1 and 2.2 as practice. Chapter 3 supplies keys, cardinality and the source-document trace (Requirements 2 and 4), with Tutorial 3.2 and Exercises 3.2 and 3.6.

**What builds on it.** Part II starts from this case's data map and margin measure: Chapter 4 imports the same tables with Power Query, Chapter 5 returns to the nine invoices dated before their shipment, and Chapter 6 splits the Furniture margin change into its volume, mix, price and cost effects, which is the diagnosis that Requirement 1 names. Chapter 6 also meets the year-end closing entries again in its trial balance. Part III tests the cutoff in SQL, and Part IV puts the same closing-entry flag into a data model.

**Appendix D** maps each requirement to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each requirement guide names the competencies it practices.
