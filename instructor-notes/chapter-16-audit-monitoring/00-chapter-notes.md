# Chapter 16: Audit Monitoring and Report Assurance

| | |
|---|---|
| Unit | Chapter 16: Audit Monitoring and Report Assurance |
| Tools | Power BI Desktop |
| Time | About 360 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part IV, Accounting Analytics with Power BI: the last of four chapters. It monitors the tests of Chapters 8 and 12, and audits the package of Chapter 15 and its own report |
| Analytics types | Descriptive and diagnostic; the memo's recommendations on controls and on the reports are prescriptive |
| Tools | Power BI Desktop 2.158 on Windows, reading CharlesRiver.xlsx: Power Query (flags, unpivot, append, merge), Report view with drill-through, DAX query view |
| Components | 3 guided tutorials (12, 14 and 9 steps) that build Audit Monitoring.pbix, 6 exercises (2 for each perspective), 14 multiple-choice questions and a deck of 71 slides |
| Files students need | CharlesRiver.xlsx. Chapter16-companion.zip holds Audit Monitoring, a Power BI project, at the start of Tutorials 16.2 and 16.3 (with Charles River Reports at the end of Chapter 15) and at the end of the chapter. Chapter16-exercises-pbi.zip holds the model answer |
| Time | Class: about 360 minutes. Students: about 100 minutes of reading, 75 to 120 for each tutorial and 60 to 90 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The register holds 151 exceptions from 11 tests: 43 journal entry, 25 purchase order and 83 payroll. January holds 44 of the 68 journal entry and purchase order exceptions, and leads in every year.
- One test recurs in every month: 77 payroll registers approved by the employee they pay. One employee, the Accounting Manager, approves every register.
- A first review records 15 dispositions and leaves 136 exceptions open. The six year-end closes, two a year, are the expected ones.
- The last pay date of a payroll register is December 18, while the journal entries and the orders run to 2026-12-31. No pay period has a later pay date in the year, and the rest of December's work is in periods marked Open, with no registers. The purchase order numbers run from 1 to 18,832 with no gap.

## What students should be able to do afterward

1. Distinguish exceptions from anomalies and continuous auditing from continuous monitoring, and specify a test by its rule, population, frequency and expected result. Practiced in Tutorial 16.2 (Test 2), Exercises 16.5 and 16.6, and questions 1 to 3.
2. Build an exception register in Power Query and extend it with a new test. Practiced in Tutorials 16.1 and 16.2, Exercise 16.2, and questions 4 to 6.
3. Show counts and rates by test, month and year, and read a rate against its population. Practiced in Tutorial 16.2 (Steps 10 to 12), Exercises 16.3 and 16.4, and questions 6 and 7.
4. Record dispositions that survive every refresh and decide which open exceptions come first. Practiced in Tutorial 16.3 (Steps 1 to 5), Exercises 16.4 and 16.6, and questions 8 to 11.
5. Test a report before relying on it: reconcile its populations, rerun its tests and state the date through which its data run. Practiced in Tutorial 16.3 (Steps 6 to 8), Exercises 16.1 and 16.2, and questions 12 and 13.
6. Explain the change controls a monthly report needs. Practiced in the memo of Tutorial 16.3 (Step 9) and questions 13 and 14 only: no exercise builds it, so grade the memo.

## Preparing to teach

**Before the first class**

- Students need Windows and Power BI Desktop 2.158 (**Help > About**). A Mac student works in a lab or a virtual machine, as in Chapter 13.
- Do the three tutorials yourself in order and save Audit Monitoring.pbix. Tutorial 16.3 Step 8 opens Charles River Reports.pbix as left at the end of Chapter 15, so every student needs it.
- A student who falls behind takes Audit Monitoring from Chapter16-companion.zip, from the folder of the tutorial they start. Its README gives the steps: open the .pbip, point the queries at CharlesRiver.xlsx (**Home > Transform data > Data source settings > Change Source**), choose **Home > Refresh**, and **File > Save as** a .pbix.
- Tell students to save a copy after Tutorial 16.3, such as `Ch16 Exercises.pbix`, with one page and one display folder of measures for each exercise. Exercise 16.2 uses Exercise 16.1's ledger query, and Exercise 16.6 uses Exercise 16.5's payments.
- Open the model answer once. Its pages are Journal Entries, Entry Lines, Validation, Monitoring, Exception Detail and Review (the tutorials), Ex 16.1 to Ex 16.6 and Notes; its DAX query tabs are Tests and Checks. After **Home > Refresh**, **Run** on the Checks tab tests 299 values. Its queries read C:\CharlesRiver\CharlesRiver.xlsx.
- The Checks tab cannot read how a visual renders: compare the heat map's shading, the drill-through and the edited interactions by eye.

**Pitfalls that cost class time**

- **Rename before Append.** Tutorial 16.2 Step 6. A query that keeps OrderDate leaves EventDate empty on 25 order exceptions.
- **The week.** Tutorial 16.1 Step 4. `Date.DayOfWeek` without Monday as the first day flags 270 entries in place of 17.
- **Backdated.** If PostingDate is still Date/Time and CreatedDate is not cut to its date, every entry reads as backdated: 851 of 851.
- **The merge key.** Tutorial 16.3 Step 2. A merge on TestID alone gives 214 rows in place of 151; a mistyped document number leaves 14 reviewed and 137 open; a disposition typed twice gives 152 rows.
- **Data Through.** Tutorial 16.3 Step 7. MAX in place of MINX reads 2026-12-31, not 2026-12-18.
- **Edit interactions.** Tutorial 16.2 Step 12c: a click on the departed approver shows PO AfterTermination at 0.16 per 1,000 of all orders. Tutorial 16.3 Step 7c keeps a click from moving the Data Through card.
- **Closing without saving.** Step 8 tests the package and must not change it.

![A mock of Model view of the monitoring model, the register beside the populations it tests.](../figures/chapter-16-audit-monitoring/IF-16-0-B.pdf)

## Teaching approaches

**Plan A: lecture with live demonstration (four sessions of 90 minutes, 360 minutes in all).** It fits a lecture course with the exercises at home.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 5 | The three requests | 2 to 5 |
| 1 | 25 | From audit tests to monitoring: terms, tests, the cycle; check | 6 to 14 |
| 1 | 15 | Designing an exception register | 15 to 20 |
| 1 | 45 | Tutorial 16.1: Steps 4, 5, 8, 10 and 12 live | 21 to 28 |
| 2 | 20 | The monitoring page: heat map, January, rates; check | 29 to 34 |
| 2 | 70 | Tutorial 16.2: Steps 5, 7, 10, 12 and 13 live | 35 to 42 |
| 3 | 25 | Reviewing exceptions; check | 43 to 48 |
| 3 | 25 | Auditing the report itself; check | 49 to 56 |
| 3 | 40 | Tutorial 16.3: Steps 1 to 3, 6 and 7 live | 57 to 64 |
| 4 | 10 | Looking ahead and the summary | 65 to 71 |
| 4 | 45 | Exercises 16.2 and 16.4 in pairs | |
| 4 | 15 | Quiz on questions 5, 7, 9, 10, 12 and 14 | |
| 4 | 20 | Discussion prompts 1, 2 and 5 | |
| | 360 | Total | |

**Plan B: lab first (three sessions of 120 minutes, 360 minutes in all).** Students build before they hear the vocabulary. It fits a computer lab; a pair that falls behind takes the next tutorial's start file.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Pose the three requests | 5 |
| 1 | 70 | Tutorial 16.1 in pairs | 22 to 28 |
| 1 | 20 | Debrief: the flags, the score, the drill-through | 24 to 27 |
| 1 | 20 | Short lecture on monitoring and the register | 7 to 20 |
| 2 | 80 | Tutorial 16.2 in pairs | 36 to 42 |
| 2 | 20 | Debrief: the heat map and the recurring row | 39 to 41 |
| 2 | 20 | Short lecture on reviewing exceptions | 44 to 48 |
| 3 | 70 | Tutorial 16.3 in pairs | 58 to 64 |
| 3 | 20 | Debrief: Test 3, Test 4 and Data Through | 60 to 63 |
| 3 | 30 | Short lecture on auditing the report itself | 50 to 56 |
| | 360 | Total | |

**Plan C: flipped, with one 150-minute class.** Students build the tutorials at home. It fits upper-level and graduate classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 15 | Quiz on questions 3, 5, 7, 8, 9, 11, 12 and 14 | |
| 30 | Review clinic: partners compare Test 2, Test 3 and Test 4 | 37, 58, 61, 62 |
| 30 | Break it: a mistyped disposition, an unrenamed column, Data Through taken with MAX | 17, 58, 63 |
| 50 | Exercises 16.4 and 16.6 in pairs | |
| 15 | Discussion prompts 2 and 4; assign | |
| 10 | Looking ahead to the appendix and the Part IV case | 65 to 67 |
| 150 | Total | |

Plan A is the safest: the stumbles are in a merge key and a filter, and a demonstration shows how. Plan B lets students meet the traps themselves and needs a lab. Plan C leaves no time to demonstrate, and fails for students who arrive without a finished file.

![What each tutorial adds to Audit Monitoring and where each exercise attaches, so an instructor sees the build at a glance.](../figures/chapter-16-audit-monitoring/IF-16-0-A.pdf)

## Tutorial guide

### Guided Tutorial 16.1: Journal Entry Monitoring

**Purpose.** Students start internal audit's own file and rebuild Chapter 8's five tests as flags. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 4 (the flags), Step 8 (the filter on a score), Step 10 (drill-through) and Step 12 (Test 1). Leave Steps 1 to 3, 5, 6, 7, 9 and 11 to students.

| Step | Look for | Value |
|---|---|---|
| 4, 5 | The five flags | Weekend 17, Backdated 6, SelfApproved 7, AboveLimit 9, RoundAmount 4 |
| 7 | Scores 0 to 4 | 818, 25, 7, 0, 1 entries |
| 8 | Entries at 2 or more | JE-2024-000001 (Opening) first with four; 7 others |
| 9, 10 | The ledger lines | 2,821 lines in all; JE-2024-000001 has 18, each side $13,817,192.58 |
| 11 | JE Exceptions | 43 rows, not loaded |
| 12 | Test 1 | 851 entries; $129,860,610.27 = debits = credits |

**Stumbles to expect**

- Step 4: the week and the date comparison (see the pitfalls). Step 5: the six new columns left without the Whole Number type (Step 5c).
- Step 8: RiskScore left to sum, so Advanced filtering is missing. Set **Don't summarize** first.
- Step 9: the ledger loaded before it is filtered on SourceDocumentType.
- Step 10: the drill-through field dragged with a visual selected.
- Step 11: **Enable load** left on, and the row count not read.

**The checkpoint to look for.** The four bullets. A strong student says why agreeing totals are good evidence that falls short of proof.

### Guided Tutorial 16.2: The Exception Register and the Monitoring Page

**Purpose.** Students add the purchasing and payroll tests, append the register, and build the page the committee asked for. **Time.** About 90 to 120 minutes. **Demonstrate, then hand over.** Demonstrate Step 5 (a flag guarded against null), Step 7 (Append), Step 10 (Population), Step 12c (Edit interactions) and Step 13 (drill-through). Leave Steps 1 to 4, 6, 8, 9, 11 and 14 to students.

| Step | Look for | Value |
|---|---|---|
| 3, 5 | The new flags | PO: SelfApproved 9, AboveLimit 13, AfterTermination 3; PR: PaidBeforeApproval 3, AfterTermination 3, SelfApproved 77 |
| 7 | The register | 151 rows: 43, 25, 83 |
| 10 | Population and rate | 18,832 orders, 8,197 registers; a total row with no rate |
| 11 | The heat map | January darkest; PR SelfApproved 6 to 8 in every month name; December JE AboveLimit 6, the year-end closes |
| 12 | Approvers | Tasha Todd (Accounting Manager) 89, Cynthia Reyes (CFO) 21, David Roth (Controller) 16, Daniel Diaz (Account Executive, terminated 2024-04-26) 6, Jennifer Cole (Purchasing Manager) 5, the rest by job title |
| 13 | Drill-through | Three PO AfterTermination orders, one approver, who approved only those |
| 14 | Test 2 | the counts above for the eleven tests |

**Stumbles to expect**

- Step 3: a flag that compares with a null termination date, which fails: guard it first.
- Step 5: the pay date compared in place of the period's end date. It finds the same registers today, as the tutorial says, but would flag a final paycheck for earlier work.
- Steps 6 and 7: the renaming (see the pitfalls).
- Step 9: the keys and flag columns left visible.
- Step 11: the number removed from the cells, so the fill carries the meaning alone.
- Step 12c: Edit interactions skipped.

**The checkpoint to look for.** The five bullets. A strong student separates the January cluster, which asks how the controls work then, from the recurring row, which asks for a change to the control.

### Guided Tutorial 16.3: Reviewing Exceptions and Testing the Reports

**Purpose.** Students record dispositions, measure the open exceptions, test both reports and write the memo. **Time.** About 90 to 105 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (a two-column merge), Step 3 (Test 3), Step 6 (Test 4), Step 7 (Data Through) and Step 8 (rerun, then close without saving). Leave Steps 1, 4, 5 and 9 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | The dispositions | 15 rows: Expected 6, Deficiency 6, Follow up 3 |
| 2, 3 | Test 3 | 151 exceptions, 151 keys; 15 dispositions, 15 keys; reviewed 15; open 136 |
| 4 | Open by year | JE 14, 10, 13; PO 10, 5, 7; PR 25, 26, 26 |
| 5 | Two tests or more | 19 documents; JE-2024-000001 with 4 |
| 6 | Test 4 | 18,832 orders, 18,832 unique, first 1, last 18,832; 8,197 registers, 3 with no payment record |
| 7 | Data Through | 2026-12-18; by year 2024-12-20, 2025-12-19, 2026-12-18 |
| 8 | The package's tests | Test 1 by year 9,040, 9,371, 9,522 lines; Test 3 71 accounts, $67,107,722.36; Test 5 1.18, 1.41, 1.51 |

**Stumbles to expect**

- Step 1: keys that do not match character for character (see the pitfalls). The six Deficiency rows rest on the tutorial's assumption that the reviewer looked past the register, at the approval log, the employment records and the earnings. Ask what the flags alone would support.
- Step 3: a Test 3 that reads reviewed equal to dispositions and so passes a disposition typed twice: the key counts catch it.
- Step 7: MAX in place of MINX.
- Step 8: the package saved over, or a test run without its comment line.
- Step 9: the registers approved by their own employee reported document by document. The memo reports them once.

**The checkpoint to look for.** The four bullets. A strong student calls the card a bound observed in the extract, proving neither a refresh nor a complete payroll.

## Difficult ideas and misconceptions

**An exception is not an anomaly.** Tutorial 16.2 and Exercises 16.5 and 16.6, question 2. A rule fails or holds. A near-duplicate or a first-digit departure is a reason to look. Ask: which of these needs an explanation before anyone calls it a problem?

**A count is not a rate.** Exercise 16.4, question 6. Purchase order exceptions rose by a third (6 to 8) and the rate barely moved, because orders grew by 28%. Ask: how many orders were there?

**A recurring exception is one finding.** Tutorial 16.2 Step 11, question 11. The 77 registers are a design question: one approver approves every register, including the approver's own. Ask: what control would stop them?

**Open is not unresolved.** Tutorial 16.3, question 9. An open exception has no disposition. The three follow-ups and six deficiencies are reviewed and still await action. Ask: which list holds the matters to track?

**A disposition belongs to an exception.** Tutorial 16.3 Step 5. The departed approver's three orders are reviewed for one test and open for another. Ask: how many exceptions does one order hold?

![A board sketch of the order in which a reviewer takes the register's exceptions.](../figures/chapter-16-audit-monitoring/IF-16-0-D.pdf)

**More exceptions than reviewers can examine.** Tutorial 16.3, question 10. Li and colleagues and Alles and colleagues describe alarm floods. The chapter's answer is a simple order and one disposition for what is expected or recurs. Ask: what would you change in the rules before adding reviewers?

**An uncontrolled copy is not the controlled report.** Question 14. A .pbix that imports its data holds every row, and a copy kept outside the approved release stops at the date of the copy. Ask: who holds copies of the package?

**A process's rate counts failed tests.** Tutorial 16.2 Step 10. A document that fails two tests counts twice. Ask: what does the journal entry rate count?

**Agreeing totals do not prove completeness, and Data Through proves no refresh.** Tutorial 16.1 Step 12, Tutorial 16.3 Step 7, question 12. Ask: what could be missing from both totals?

**Who sees the report matters.** Question 3. Gonzalez and Hoffman found that prompt notice can encourage fraud when detection is weak. The chapter calls it a reason to think, not a rule. Ask: what does a notice reveal about what the test cannot detect?

**A filter reaches only what it is related to.** Tutorial 16.2 Step 12c, Exercise 16.6. Employee reaches the entries and not the orders or registers; Cynthia Reyes approved 99.92% of the orders, and a plain count shows every order on every row. Ask: which tables does the employee filter?

## Discussion prompts

1. **Should the monitoring report go to the managers whose approvals it tests?** It reaches Gonzalez and Hoffman and the chapter's split: the report to the people who oversee the controls, the exceptions to those who must explain them.
2. **The recurring payroll test fires every month. Keep it, retire it or reclassify it?** It reaches one finding, then a test that the approver's own pay has another approver, and the unexplained rate.
3. **Who should write dispositions, and what should the record show?** It reaches who and when in the record, a reviewer who is not the preparer, and review by the chief audit executive.
4. **A December page shows no payroll exceptions after December 18. What can you conclude?** It reaches the open pay periods that hold the rest of December's work, and Data Through as a bound on what the tests saw, not proof of a complete payroll.
5. **Next month brings dozens of new exceptions. How do you order the review?** It reaches the score, novelty and Li and colleagues, and the alarm floods Alles and colleagues found at Siemens.
6. **A measure passed its test in April and was changed in May. Do you trust it?** It reaches rerunning the tests, the change record and the project under version control.
7. **Should anomaly tests share the register with rule tests?** It reaches the register's five columns, a different disposition path, and keeping the two layers apart.
8. **Who approves the approver?** It reaches 100% of the registers on one approver and the segregation and absence questions.

## Using the exercises

All six exercises are Power BI work with a model answer in Chapter16-exercises-pbi.zip: six pages with the Checks tab behind them. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 16.1 Monitoring the Receivables | Financial | Power BI | 90 | Intermediate | 5 |
| 16.2 Year-End Cutoff on the Monitoring Report | Financial | Power BI | 90 | Advanced | 2, 5 |
| 16.3 Surge Days by Month | Managerial | Power BI | 75 | Intermediate | 3 |
| 16.4 Exception Rates over Time | Managerial | Power BI | 60 | Basic | 3, 4 |
| 16.5 Benford's Law in DAX | Auditing | Power BI | 75 | Intermediate | 1 |
| 16.6 Near-Duplicates and the Concentration of Approval | Auditing | Power BI | 90 | Advanced | 1, 4 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 16.1 and 16.2, managerial students 16.3 and 16.4, auditing students 16.5 and 16.6. Each track presents its traps to the others.
- *One exercise a session.* Take the basic one first: 16.4, 16.1, 16.3, 16.5, 16.2, 16.6.
- *A light load.* Exercises 16.4 and 16.1 take about two and a half hours and cover outcomes 3, 4 and 5.

**Grading and discussion.** Exercises 16.1 to 16.4 suit grading from the saved report, with the Checks tab to compare a number. Exercises 16.5 and 16.6 are graded on their notes: the classification and the design question are the judgment. Exercises 16.3, 16.5 and 16.6 suit class discussion. Collect the .pbix, not screenshots: the queries, measures and display folders are the evidence.

![What the Checks tab proves and what only Desktop shows, the map an instructor needs before grading.](../figures/chapter-16-audit-monitoring/IF-16-0-C.pdf)

## Multiple-choice questions

Key: 1 C, 2 A, 3 D, 4 B, 5 A, 6 C, 7 B, 8 D, 9 B, 10 A, 11 C, 12 D, 13 A, 14 B.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | C | continuous monitoring is management's ongoing review of its own controls (Tronto & Killingsworth, 2021). |
| 2 | A | rule tests produce exceptions; analytical tests produce anomalies (Kogan et al., 2014). |
| 3 | D | with a weak system, early notification increased the inclination to commit fraud (Gonzalez & Hoffman, 2018), a conditional result, not a rule that control owners never learn their exceptions. |
| 4 | B | unpivoting turns the selected columns into Attribute and Value rows. |
| 5 | A | Append matches by name, so OrderDate becomes its own column and EventDate stays null for orders. |
| 6 | C | rates need populations; a count alone hides volume (hundreds of entries against thousands of orders). |
| 7 | B | an exception in every period points to a possible design flaw, to confirm against the policy and any other review (one approver approves every register, including the approver's own). |
| 8 | D | the register is rebuilt at every refresh; a merge on the test and the document attaches each conclusion again, while text typed beside query output can end up beside a different row (Chapter 8). |
| 9 | B | a null disposition means no conclusion yet, an open exception not yet reviewed (a mistyped disposition leaves its intended exception open, which Test 3 detects, but the null itself marks the exception as open). A reviewed exception is not necessarily resolved: follow-ups and deficiencies stay matters to track. |
| 10 | A | with amounts and urgency alike, several failed tests come first under the chapter's simple order (Chapter 8's risk score), and new comes before explained; it is a first cue, not Li et al.'s adaptive suspicion score, and a serious single failure can come first when amounts or urgency differ. |
| 11 | C | a recurring exception by design is one finding; the response is a change to the control. |
| 12 | D | Data Through is the earliest of the populations' last dates, here the last pay date of a register, December 18; the rest of December's work is in pay periods marked Open, scheduled to pay in the next year. It is a bound observed in the extract; it does not prove a refresh or a complete payroll. |
| 13 | A | a .pbip stores the model and report as text files that version control compares line by line. |
| 14 | B | a .pbix whose model imports its data, as this one does, holds every row, and a copy kept outside the approved release can go stale and drift from it; an approved, recorded and protected copy can stay governed. |

**Questions where a wrong option tempts**

- **Question 3.** Option A inverts the finding and B denies any effect; the fraud inclination rose only with a weak system.
- **Question 5.** Option C carries over UNION ALL's habit of matching by position. Append matches by name.
- **Question 7.** Option C reads size as seriousness; D discards the design finding as noise.
- **Question 9.** Option D confuses a null with a mistyped key. The null marks the exception open; Test 3 finds the mistype.
- **Question 10.** Option C is the recurring design finding, one finding, not first; B is expected; D takes age over score. The stem holds amounts and urgency alike, so the chapter's simple order applies.
- **Question 11.** Option A reviews each register separately; D treats a design flaw as expected.
- **Question 12.** Option A sounds like a refresh problem. The card shows only that no payroll register has a later pay date, a bound observed in the extract.
- **Length.** In none of the 14 questions is the correct option also the longest, so wording alone does not give it away.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 3 make a quiz on monitoring and its tests, 4 to 6 on the register, 7 to 11 on the review, and 12 to 14 on auditing the reports.

## Connections

**Builds on.** Chapter 4's control totals and Documentation worksheet; Chapter 8's tests, risk score and dispositions; Chapter 12's audit query library with its UNION ALL, the payroll tests of Exercise 12.5 and the surge days; Chapter 13's Validation page; Chapter 14's Date table, DAX query view tests, CALCULATE and TREATAS; and Chapter 15's package, whose Tests tab and About page this chapter reruns and reads.

**Later chapters.** The appendix on publishing and security secures and shares the package; its start folder also holds Audit Monitoring at the end of this chapter. The Part IV case builds a new report with the same Validation page, Tests tab and Data Through card. Part V's capstone cases draw on every tool of the book.

**Appendices.** The appendix on Power BI in the browser rebuilds Chapter 13's model there. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
