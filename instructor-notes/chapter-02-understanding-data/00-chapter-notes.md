# Chapter 2: Understanding Data in Accounting

| | |
|---|---|
| Unit | Chapter 2: Understanding Data in Accounting |
| Tools | Workbook browsing and written work |
| Time | About 150 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part I, Foundations of Accounting Analytics: the second of three chapters, closed by a comprehensive case |
| Analytics types | None is named. The tests are descriptive (counts, totals, comparisons of what is recorded), and they come before any of the four types |
| Tools | Excel only, in the working copy: filters, sorting, PivotTables, COUNTIFS, MINIFS, SUMIFS, XLOOKUP and a few totals. No SQL or Power BI |
| Components | 2 guided tutorials, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 52 slides |
| Files students need | CharlesRiver.xlsx, from the Charles River Accounting Dataset (Excel) link on the Downloads page, and the working copy CharlesRiver_Work.xlsx that Tutorial 2.1 has them make. The Downloads table lists no start files and no solutions for Chapter 2; the guides in this folder hold the model answers |
| Time | Class: about 150 minutes. Students: about two hours of reading, 45 minutes for each tutorial, and 45 to 75 minutes for each exercise (assign two or three) |

The chapter depends on these conditions of the data, all visible in the workbook:

- Shipments with no TrackingNumber number 392 of 9,707, with every carrier. Shipments marked In Transit number 740, each with a DeliveryDate on or before the last date in the data.
- Customer names shared by two customers: 2.
- Invoices dated before the first shipment on their order: 9. Invoices with no shipment, because they bill design services: 439.
- Items with no ListPrice, by design: 43; items sold: 223.
- The ledger has 815,921 rows, and debits equal credits. Its first period and its last two are small, and the last fiscal year holds only supplier payments. Rows with neither a debit nor a credit: 128.
- Supplier invoice numbers that appear twice for one supplier: six. Check numbers that repeat: two (Exercise 2.6).

## What students should be able to do afterward

1. Classify data as quantitative or qualitative and as structured, semi-structured or unstructured, and say why the book's tools are built for structured data. Practiced in questions 4 and 7 and the check slides; no exercise asks for it directly.
2. Name the sources of accounting data and say how a sub-ledger and the ledger should agree. Practiced in Exercises 2.2 and 2.5 and questions 9, 10 and 13.
3. Classify a finding as accuracy, completeness, consistency or timeliness, and say when it touches two. Practiced in the memo of every exercise and in questions 1, 2, 3 and 6.
4. Run the basic tests in Excel (filter for blanks, count repeats, compare dates, total and compare) and report each result with its table, column and count. Practiced in both tutorials and Exercises 2.1, 2.2, 2.3, 2.5 and 2.6.
5. Judge whether a blank, a repeat or an outlier is an error, and write the judgment with its evidence. Practiced in Exercises 2.1, 2.3, 2.5 and 2.6.
6. Explain the difference between tidy and clean, and what a balanced ledger and source-to-ledger traceability do and do not show. Practiced in Exercises 2.2 (requirement 3), 2.4 and 2.6 (requirement 4) and questions 5, 11 and 15.

## Preparing to teach

**Before the first class**

- Tutorial 2.1 asks students to copy CharlesRiver.xlsx and name the copy CharlesRiver_Work.xlsx, and every exercise starts from that copy. The tutorials of Parts II and IV read the downloaded workbook with Power Query, so it must stay as provided. Say this before the tutorial, and again if a student reports that the original has helper columns.
- Work through both tutorials yourself on a machine like the students'. Time the filter on GLEntry, the largest worksheet, and the PivotTable of Tutorial 2.2, so you know how long to tell students to wait.
- Check that every student's Excel has MINIFS and XLOOKUP, which the tutorial and the exercises use. An older perpetual version may lack them, so find out in the first week.
- Get the PowerPoint deck from the Downloads page. Each module slide matches a section of the chapter, and every slide has talk-track notes.

**Pitfalls that cost class time**

- GLEntry has 815,921 rows, about 78% of a worksheet. A formula copied down every row makes Excel unresponsive. The tutorial summarizes with a PivotTable for this reason, and Step 4 of Tutorial 2.2 types `Total` one row below the data so the Table does not grow.
- Tutorial 2.1, Step 6: MINIFS returns a serial number until the result is formatted as a date, and students then read it as a wrong date. The same step returns 0 when an order has no shipment, which Step 7 turns into "No shipment".
- Whole-column COUNTIFS and SUMIFS on PurchaseInvoice and DisbursementPayment (Exercise 2.6) take a while. Tell students to wait.
- Filters left on: ask students to clear a filter before the next worksheet. And a clean result: several students will think it means they did the test wrong, so say early that a test that finds nothing is a finding and the memo must record it.
- Say out loud that the dataset is fictional and cleaner than most real extracts. A student who finds nothing in a table should record a clean result, not search until something turns up.

## Teaching approaches

**Plan A: lecture with a live demonstration (two sessions of 75 minutes, 150 minutes in all).** It fits a lecture course with a projector and covers the whole deck. Students touch the workbook in the second session, so the first is vocabulary and the second is the two tutorials.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The opening scenario: which of the four observations worries you most, and why? Read the objectives | 2 to 5 |
| 1 | 10 | Why quality comes first; data types and the first check | 6 to 13 |
| 1 | 10 | Sources of data; sub-ledgers must agree with the ledger | 14 to 16 |
| 1 | 20 | The four dimensions; the Watch out; sort the tutorial findings by dimension in groups | 17 to 20 |
| 1 | 25 | The four problems, the check slide and the checklist tables | 21 to 28 |
| 2 | 35 | Tutorial 2.1: demonstrate Steps 2, 6 and 7, students do the rest, then the checkpoint | 29 to 32 |
| 2 | 10 | Tidy data and traceability | 33 to 38 |
| 2 | 20 | Tutorial 2.2: demonstrate Steps 4, 6 and 8; students finish it outside class | 39 to 42 |
| 2 | 10 | Table groups, the check slide, the summary; assign exercises | 43 to 51 |
| | 150 | Total | |

**Plan B: lab first (one session of 120 minutes).** Students meet the data before the vocabulary. It fits a computer lab, and it lets the findings motivate the dimensions. Pair students who are slow to open the workbook, since GLEntry delays them.

| Minutes | Activity | Slides |
|---:|---|---|
| 5 | Pose the opening scenario; students list what they would look at | 5 |
| 40 | Tutorial 2.1 in pairs, to the checkpoint | 29 to 32 |
| 10 | Debrief: sort the findings by dimension, then show the four dimensions and the checklist | 17 to 20, 22, 27, 28 |
| 35 | Tutorial 2.2 in pairs, to the checkpoint | 39 to 42 |
| 10 | Mini-lecture: tidy data, traceability, and what a balanced ledger cannot show | 33 to 38 |
| 10 | Debrief of the ledger tests: the small periods, the rows with no amount, the source types | 41, 42 |
| 10 | Table groups; assign exercises | 43 to 47, 51 |
| 120 | Total | |

**Plan C: flipped, with one 75-minute class.** Students read the chapter and do both tutorials at home. It fits upper-level and graduate classes, and it depends on students arriving prepared, so open with a quiz.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval quiz on questions 1, 2, 3, 6, 11 and 12 | |
| 25 | Findings workshop: groups sort their tutorial findings by dimension and mark each as an error, a judgment or by design; compare with the other groups | 22 to 26 |
| 15 | Debrief the ledger checkpoint: the small periods, the rows with no amount, what equal totals do not show | 41, 42 |
| 15 | Start Exercise 2.5 (requirements 1 to 3) in pairs | |
| 10 | Discussion prompts 1 and 6; assign exercises | |
| 75 | Total | |

## Tutorial guide

### Guided Tutorial 2.1: Inspecting Charles River O2C and Item Data for Data Quality Problems

**Purpose.** Students apply the four dimensions to real tables before they write a memo. They find three findings to follow up (the In Transit rows conflict with their dates only if DeliveryDate records the delivery), weigh three that need judgment (one turns out to be expected) and make the working copy.

**Time.** About 45 minutes in class, or 30 if students have read the steps. Steps 6 and 7 take longest, because they build formulas over whole columns.

**Demonstrate, then hand over.** Demonstrate Step 2 (filter the blank tracking numbers and read the status bar) and Steps 6 and 7 (MINIFS, then the check formula). Leave Steps 1, 3, 4, 5 and 8 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2 | TrackingNumber blank | 392 of 9,707 shipments, with all 4 carriers |
| 3 | Status In Transit | 740 shipments, from every year (234 from 2024) |
| 4 | Same-name customers | 2 pairs |
| 5 | FreightCost | average $152.20, largest $873.95 |
| 7 | Check column | "Check" on 9 invoices, "No shipment" on 439 |
| 8 | ListPrice blank | 43 of 266 items: Capex (11), Packaging (10), Raw Materials (11), and Services (11) |

**Stumbles to expect**

- Steps 2 and 3: students filter the wrong column, or leave the filter on. In Step 3 they call "In Transit" wrong only because the date is old. Every DeliveryDate falls on or before the year-end under review. If the date records the delivery, two columns of one record disagree, and if it is only the expected date, the shipments are overdue. The tutorial asks what the DeliveryDate means before blaming the Status, and either reading is a finding to follow up.
- Step 4: the Smith Ltd pair is the harder one, because both customers share a region and a segment. Make students compare the city, the contact and the activity before they conclude.
- Step 5: students stop at "several times the average". The next move is to read the freight against the size of the shipment: the largest freight costs are on the largest shipments.
- Steps 6 and 7: a column letter that differs from the tutorial's, a result not formatted as a date, and a formula not copied to the first row.
- Step 8: students record the blank list prices as errors. The contrast with Step 2 is the lesson.

**The checkpoint to look for.** The tutorial lists three findings to follow up and three judgments. A good written list names the table, the column, the type, the count and the conclusion for each, as the checkpoint says. A list with counts and no conclusion is the common weak answer.

### Guided Tutorial 2.2: Examining the Charles River Accounting Core for Completeness and Consistency

**Purpose.** The same method applied to the ledger. Students test a total, a reference, a range of dates and a list of source types, and meet the ideas that a clean result needs recording and that equal totals prove little.

**Time.** About 45 minutes. Building the PivotTables on 815,921 rows is the wait.

**Demonstrate, then hand over.** Demonstrate Step 4 (the totals) and Step 6 (the PivotTable of periods and what the small ones are). Leave Steps 1, 2, 3, 5, 7 and 8 to students, with Step 5 as the one to check closely.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2 | Account types in the chart | 5 classes, 104 accounts |
| 4 | Debit and credit totals | $731,949,908.31 each; difference, rounded to the cent, $0.00 |
| 5 | Distinct AccountIDs in the ledger; unmatched | 71 of the chart's 104; 0 |
| 6 | Periods; the small ones | 38 periods; 3 small ones, the first and the last two |
| 7 | Rows with no debit and no credit | 128 rows, all PayrollPayment |
| 8 | Source types | 20 types; the eight the step names are present |

**Stumbles to expect**

- Step 4: students press Ctrl+Down from a column with blanks, such as SourceLineID or CostCenterID, which stops at the first blank and puts the totals over ledger rows (the tutorial starts in A2, the GLEntryID column, which is never blank). Others type the totals directly below the data, so the Table swallows them (the tutorial leaves one blank row), or compare the unrounded totals, whose difference can show a fraction of a cent (the tutorial rounds each to the cent and investigates any other difference).
- Step 5: students expect a mismatch and think a clean result means the test failed.
- Step 6: students read the last periods as missing transactions. Send them to the SourceDocumentType of those rows.
- Step 7: the zero rows sit on 1010 Cash and Cash Equivalents and 2030 Accrued Payroll. The tutorial says only that they should be investigated and explained.
- Step 8: the distribution counts ledger rows, not documents.

**The checkpoint to look for.** The tutorial's three bullets plus a written summary that records the tests that found nothing. A student who lists only the problems has missed the point of its last sentence.

## Difficult ideas and misconceptions

**One finding, two dimensions.** If the DeliveryDate records the delivery, shipments still In Transit are a consistency problem (two columns disagree) and a timeliness problem (the status was not updated). If it is only the expected date, they are overdue shipments to follow up. Question 6 asks about an extract taken before the final entries were posted, which is also a completeness problem. Students who want one right answer lose marks. Teach them to name the dimension the test examines and to add the second when it applies.

![Where each finding of the two tutorials sits among the four data quality dimensions, and whether it is an error.](../figures/chapter-02-understanding-data/IF-02-0-A.pdf)

**A blank is not an error.** The blank TrackingNumber is information that should exist. The blank ListPrice of a raw material is expected. The notes of an order and the payment date of an unpaid invoice are blank by design. Students who flag every blank, or none, miss the sorting that the assessment is for. Ask for the reason a value would be blank, then the evidence for it.

**An outlier is a question.** The largest freight costs are several times the average, and they belong to the largest shipments. Students who delete them have answered the question without asking it.

**A clean result is a finding.** Every table has tests that find nothing: no orphaned AccountID, no order without a customer, no invoice paid above its total. Record the test, the population and the result.

**Totals and counts show less than they seem to.** Debits equal credits, so the ledger is in balance; an entry left out with both of its sides, or two offsetting errors, would not show. All the source types are present, so each cycle posts; that does not show every document posted. The model answer to Exercise 2.2 gives the case of 6 material issue headers that have no postings.

**Tidy is not clean.** A dataset can have each variable in a column and still hold wrong amounts, and a report with months across the top can be accurate and hard to analyze. Question 11 tests the first, question 5 the second, and Exercise 2.4 the layout.

![The four combinations of tidy or messy and clean or dirty, each with an accounting example.](../figures/chapter-02-understanding-data/IF-02-0-B.pdf)

**Same name is not same customer.** Two customers with one name are two companies here, and grouping by name merges them (question 12). The chapter also raises the opposite problem, one customer under several spellings, which these tests do not look for.

**A repeated invoice number is not a duplicate payment.** The pairs in Exercise 2.6 have different dates and amounts and are paid once each: a reason to ask for evidence, not a finding.

## Discussion prompts

1. **A test finds nothing. Is that a finding?** A good discussion reaches the chapter's line. Such a result tells you which tested relationships held in the population tested, not that the data are right in every other respect, and the memo should record the test, the population and the result.
2. **How would you decide whether two customers with one name are one company?** Compare the rest of the record: city, contact, segment, activity. Then ask what a wrong merge or a wrong split would do to a receivables report.
3. **A shipment has no tracking number. What evidence would you ask for, and from whom?** A dispatch log or a signed delivery receipt, from the warehouse or the carrier. The extract holds no other carrier reference.
4. **Which of the four dimensions is hardest to test from inside one extract?** Accuracy needs an independent source, and completeness needs a population from outside the records. Expect the answer that each test has a blind spot.
5. **Debits equal credits. What has been shown, and what has not?** The ledger balances as a whole. Missing entries and offsetting errors are not excluded.
6. **Which comes first, making a dataset tidy or making it clean, and does the order matter?** There is no fixed order, but reshaping with errors in the data can spread them. Ask students to defend one.
7. **Whose job is data quality: the preparer's, the analyst's or the auditor's?** The chapter says it is a professional responsibility of all three, and gives the audit standard as an example. Ask what each would test first.

## Using the exercises

All six exercises are done in the working copy and end in a short memo or written assessment. There is no solution workbook; the model answers are in the guide for each exercise. The outcome column uses the numbers of the list at the top of this note.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 2.1 Assessing Revenue Data Quality in the O2C Tables | Financial | Workbook and memo | 60 | Basic | 3, 4, 5 |
| 2.2 Evaluating General Ledger Completeness | Financial | Workbook and memo | 50 | Basic | 2, 3, 4, 6 |
| 2.3 Data Quality Assessment for Product Cost Analysis | Managerial | Workbook and memo | 60 | Intermediate | 3, 4, 5 |
| 2.4 Evaluating Budget Data for Budget-Versus-Actual | Managerial | Workbook and memo | 45 | Intermediate | 3, 6 |
| 2.5 Data Quality Evaluation for Audit Planning | Auditing | Workbook and memo | 75 | Intermediate | 2, 3, 4, 5 |
| 2.6 Testing for Duplicate Payments | Auditing | Workbook and memo | 75 | Advanced | 4, 5, 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 2.1 and 2.2, managerial students 2.3 and 2.4, auditing students 2.5 and 2.6, about two hours each. A short swap discussion lets each student hear the other perspectives.
- *One exercise a session.* Take them in the order 2.2 (after Tutorial 2.2), 2.1, 2.4, 2.3, 2.5, 2.6. Exercise 2.5 repeats tests that the tutorials taught, and Exercise 2.6 is the first that goes beyond them.
- *A light load.* Exercises 2.1 and 2.6 take about 135 minutes and cover outcomes 3 to 6. Add Exercise 2.2 for an accounting-core emphasis.

**Grading and discussion.** Every exercise ends in a memo, so every one can be graded with the rubric in its guide. Exercises 2.2 and 2.4 suit pairs and a class review, and Exercise 2.6 is the one most worth discussing, because its conclusion rests on what the tests cannot show. Collect the memo and a copy of the helper columns, since students cannot check themselves against a file.

## Multiple-choice questions

Key: 1 A, 2 B, 3 C, 4 A, 5 D, 6 D, 7 C, 8 A, 9 C, 10 A, 11 B, 12 C, 13 B, 14 D, 15 B.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | A | a recorded value that differs from the true value is an accuracy problem. |
| 2 | B | blank values in a required field are a completeness problem. |
| 3 | C | with the DeliveryDate recording the arrival, as the stem states, two columns of the same record disagree, a consistency problem (the stale status is also a timeliness concern). |
| 4 | A | a cost center's name is a category, not a measurement. |
| 5 | D | months as column headers leave the month without a column and put several observations in one row. |
| 6 | D | an extract taken before the final entries were posted is not current as of the reporting date (its missing entries are also a completeness concern; the dimensions overlap). |
| 7 | C | a general ledger table has defined columns and types, while a contract's narrative has no predefined format (an XBRL filing is semi-structured, a file does not make a scanned invoice structured, and a payroll register is structured). |
| 8 | A | one product under two ItemIDs is a duplicate record. |
| 9 | C | the general ledger is the broadest record of the organization's posted financial transactions. |
| 10 | A | SourceDocumentType names the kind of business event that created the ledger row. |
| 11 | B | the structure is tidy, but the entry errors mean it is not clean. |
| 12 | C | grouping by name merges two different customers that share it. |
| 13 | B | an ERP system integrates the data of several functional areas in one database. |
| 14 | D | quality problems can make results unreliable, so they are found and addressed first. |
| 15 | B | the journal-originated entries are the starting population for management-override testing; the source type alone does not show who keyed an entry or that it is suspicious. |

**Questions where a wrong option tempts**

- **Questions 1, 2, 3 and 6 (the dimensions)** share one set of options. Ask students to name the test before they choose: a value that differs from the truth (accuracy), a value that is missing (completeness), two fields that disagree (consistency), a date that is too early (timeliness).
- **Question 3.** Timeliness tempts because the status is stale. The stem says that the DeliveryDate records the arrival, so the two columns disagree, which is consistency. Without that statement the rows could be overdue expectations, which is why Tutorial 2.1 asks what the date means first.
- **Question 7.** Option A tempts students who remember that XBRL is not a table, but the chapter calls it semi-structured. Option B tests whether a file in a system makes a document structured. A payroll register is one of the chapter's structured examples.
- **Question 5.** The stem says each department-month is one observation, so both principles are broken. Students who pick only one of them have read half of the layout.
- **Question 6.** Completeness tempts, because the final entries are missing from the extract. The question asks about the date of the extract. Accept the discussion that the dimensions overlap.
- **Question 8.** A duplicate record, not a missing value or an outlier: the same product under two keys.
- **Question 11.** Students confuse tidy and clean. The structure is tidy and the errors mean it is not clean.
- **Question 12.** A formula error tempts. The result is correct arithmetic on the wrong grouping.
- **Question 13.** A relational database tempts because it is true of an ERP system, but it does not set an ERP system apart from other software. The question asks what does, and the answer is integration across functional areas.
- **Question 15.** Calculating revenue tempts because the question mentions SalesInvoice. The separation matters for choosing the journal entries as a starting population.
- **Questions 4, 10, 12, 13, 14 and 15.** The correct option is also the longest. If you grade with these, ask students to explain their answer or reword the options.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1, 2, 3, 6 and 11 make a good quiz of the dimensions. Questions 4 and 7 cover data types, 9, 10 and 13 sources, and 12 and 15 the Charles River tables.

## Connections

**Builds on.** Chapter 1: the dataset, the table groups, the workflow and source-to-ledger traceability, which this chapter uses as a quality test and which Tutorial 3.2 traces in full.

**Chapter 3.** Keys, referential integrity and orphaned records become precise. The tests in Exercises 2.1 and 2.2 (every CustomerID and AccountID exists) are the informal version.

**The Part I case.** The comprehensive case that closes Part I uses the three chapters on the controller's question. Its data preparation depends on the tests here.

**Later chapters.** Chapter 5 cleans data in Power Query, where tidy and clean become steps. Exercise 6.1 revisits the invoices that straddle a year-end, and Chapter 8 builds the duplicate payment, journal entry and first-digit tests that Exercises 2.5 and 2.6 preview. Chapter 10 maps the tests of the checklist (Table 2.3) to SQL queries, Chapter 12 tests cutoff across the whole population, and Chapter 13 shows that Power BI's column profile and type detection read only the first rows of a table.

**Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each exercise guide names the competencies it practices.
