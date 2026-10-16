---
note: ch16.chapter
uses: [ch16.t1, ch16.t2, ch16.t3, ch16.ex4, ch16.ex6, ch16.mcq]
title: 'Chapter 16: Audit Monitoring and Report Assurance'
kind: chapter-notes
unit: '16'
minutes: 360
tool: powerbi
figures:
  - id: IF-16-0-A
    kind: diagram
    purpose: What each tutorial adds to Audit Monitoring and where each exercise attaches, so an instructor sees the build at a glance.
    shows: "Left to right: Tutorial 16.1 (journal entry flags, the score, ledger lines, JE Exceptions, Test 1), Tutorial 16.2 (purchase order and payroll flags, the appended register, the Tests table, measures, the Monitoring and Exception Detail pages, Test 2), Tutorial 16.3 (Dispositions, open exceptions, Review page, Tests 3 and 4, Data Through, the package's tests, the memo). Below the line, the six exercises as branches, each labeled with the query or page it adds."
    data: None; the boxes cite the tutorials, the exercises and the model answer's queries and pages.
  - id: IF-16-0-B
    kind: pbi-mock
    purpose: Model view of the monitoring model, the register beside the populations it tests.
    shows: "Model view with Exceptions related to Tests on TestID, to Date on EventDate and to Employee on EmployeeID; JournalEntry, PurchaseOrder and PayrollRegister as populations related to Date; JournalEntry also related to Employee through the approver, with JournalLines related to JournalEntry; PurchaseOrder and PayrollRegister with no line to Employee. Dispositions stands alone and hidden. Each line shows 1 at the dimension and an asterisk at the fact table."
    data: None; the tables and relationships of the model answer.
  - id: IF-16-0-C
    kind: diagram
    purpose: What the Checks tab proves and what only Desktop shows, the map an instructor needs before grading.
    shows: "A two-column board. Left, proved by the Checks tab: the counts, totals, buckets, rates, shares and dates of the tutorials and the six exercises. Right, visible only in Desktop: the heat map's shading, the drill-through click, the edited interactions as a reader meets them, the Data Through card under a slicer, and the Power Query step names a student chose."
    data: None; the Checks tab's sections and the exercises' pages.
  - id: IF-16-0-D
    kind: diagram
    purpose: A board sketch of the order in which a reviewer takes the register's exceptions.
    shows: "A short decision list from top to bottom. Expected every period, such as the year-end closes: disposition and evidence once, then check that it recurs. Recurs by design, such as registers approved by their own employee: one finding, change the control. Fails several tests, such as the opening entry: first. New this month: next. Everything else: by amount and age. Each box names its example from the register."
    data: None; the chapter's rules for ordering the review, with examples from the register.
---
{% set t1 = ch16_t1 %}
{% set t2 = ch16_t2 %}
{% set t3 = ch16_t3 %}
{% set e4 = ch16_ex4 %}
{% set e6 = ch16_ex6 %}
{% set mq = ch16_mcq %}
# Chapter 16: Audit Monitoring and Report Assurance

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part IV, Accounting Analytics with Power BI: the last of four chapters. It monitors the tests of Chapters 8 and 12, and audits the package of Chapter 15 and its own report |
| Analytics types | Descriptive and diagnostic; the memo's recommendations on controls and on the reports are prescriptive |
| Tools | Power BI Desktop {{ version }} on Windows, reading CharlesRiver.xlsx: Power Query (flags, unpivot, append, merge), Report view with drill-through, DAX query view |
| Components | {{ unit.tutorials|length }} guided tutorials ({{ steps[1] }}, {{ steps[2] }} and {{ steps[3] }} steps) that build Audit Monitoring.pbix, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.xlsx. Chapter16-companion.zip holds Audit Monitoring, a Power BI project, at the start of Tutorials 16.2 and 16.3 (with Charles River Reports at the end of Chapter 15) and at the end of the chapter. Chapter16-exercises-pbi.zip holds the model answer |
| Time | Class: about 360 minutes. Students: about 100 minutes of reading, 75 to 120 for each tutorial and 60 to 90 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The register holds {{ t3.n }} exceptions from {{ n_tests }} tests: {{ t2.process_n['JE'] }} journal entry, {{ t2.process_n['PO'] }} purchase order and {{ t2.process_n['PR'] }} payroll. January holds {{ jan_jepo }} of the {{ n_jepo }} journal entry and purchase order exceptions, and leads in every year.
- One test recurs in every month: {{ t2.selfs.n }} payroll registers approved by the employee they pay. One employee, the Accounting Manager, approves every register.
- A first review records {{ t3.n_disp }} dispositions and leaves {{ t3.open }} exceptions open. The {{ t2.n_closes }} year-end closes, two a year, are the expected ones.
- The last pay date of a payroll register is {{ mq.pay_day }}, while the journal entries and the orders run to {{ last_je }}. No pay period has a later pay date in the year, and the rest of December's work is in periods marked Open, with no registers. The purchase order numbers run from {{ t3.first }} to {{ t3.last_number|count }} with no gap.

## What students should be able to do afterward

1. Distinguish exceptions from anomalies and continuous auditing from continuous monitoring, and specify a test by its rule, population, frequency and expected result. Practiced in Tutorial 16.2 (Test 2), Exercises 16.5 and 16.6, and questions 1 to 3.
2. Build an exception register in Power Query and extend it with a new test. Practiced in Tutorials 16.1 and 16.2, Exercise 16.2, and questions 4 to 6.
3. Show counts and rates by test, month and year, and read a rate against its population. Practiced in Tutorial 16.2 (Steps 10 to 12), Exercises 16.3 and 16.4, and questions 6 and 7.
4. Record dispositions that survive every refresh and decide which open exceptions come first. Practiced in Tutorial 16.3 (Steps 1 to 5), Exercises 16.4 and 16.6, and questions 8 to 11.
5. Test a report before relying on it: reconcile its populations, rerun its tests and state the date through which its data run. Practiced in Tutorial 16.3 (Steps 6 to 8), Exercises 16.1 and 16.2, and questions 12 and 13.
6. Explain the change controls a monthly report needs. Practiced in the memo of Tutorial 16.3 (Step 9) and questions 13 and 14 only: no exercise builds it, so grade the memo.

## Preparing to teach

**Before the first class**

- Students need Windows and Power BI Desktop {{ version }} (**Help > About**). A Mac student works in a lab or a virtual machine, as in Chapter 13.
- Do the three tutorials yourself in order and save Audit Monitoring.pbix. Tutorial 16.3 Step 8 opens Charles River Reports.pbix as left at the end of Chapter 15, so every student needs it.
- A student who falls behind takes Audit Monitoring from Chapter16-companion.zip, from the folder of the tutorial they start. Its README gives the steps: open the .pbip, point the queries at CharlesRiver.xlsx (**Home > Transform data > Data source settings > Change Source**), choose **Home > Refresh**, and **File > Save as** a .pbix.
- Tell students to save a copy after Tutorial 16.3, such as `Ch16 Exercises.pbix`, with one page and one display folder of measures for each exercise. Exercise 16.2 uses Exercise 16.1's ledger query, and Exercise 16.6 uses Exercise 16.5's payments.
- Open the model answer once. Its pages are Journal Entries, Entry Lines, Validation, Monitoring, Exception Detail and Review (the tutorials), Ex 16.1 to Ex 16.6 and Notes; its DAX query tabs are Tests and Checks. After **Home > Refresh**, **Run** on the Checks tab tests {{ n_checks }} values. Its queries read C:\CharlesRiver\CharlesRiver.xlsx.
- The Checks tab cannot read how a visual renders: compare the heat map's shading, the drill-through and the edited interactions by eye.

**Pitfalls that cost class time**

- **Rename before Append.** Tutorial 16.2 Step 6. A query that keeps OrderDate leaves EventDate empty on {{ t2.process_n['PO'] }} order exceptions.
- **The week.** Tutorial 16.1 Step 4. `Date.DayOfWeek` without Monday as the first day flags {{ sunday_first }} entries in place of {{ weekend }}.
- **Backdated.** If PostingDate is still Date/Time and CreatedDate is not cut to its date, every entry reads as backdated: {{ created_after }} of {{ total_je }}.
- **The merge key.** Tutorial 16.3 Step 2. A merge on TestID alone gives {{ test_only_rows }} rows in place of {{ n_register }}; a mistyped document number leaves {{ mistyped_reviewed }} reviewed and {{ mistyped_open }} open; a disposition typed twice gives {{ twice_rows }} rows.
- **Data Through.** Tutorial 16.3 Step 7. MAX in place of MINX reads {{ through_max }}, not {{ through_min }}.
- **Edit interactions.** Tutorial 16.2 Step 12c: a click on the departed approver shows PO AfterTermination at {{ t2.diaz_rate|num(2) }} per 1,000 of all orders. Tutorial 16.3 Step 7c keeps a click from moving the Data Through card.
- **Closing without saving.** Step 8 tests the package and must not change it.

{{ figure('IF-16-0-B') }}

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

{{ figure('IF-16-0-A') }}

## Tutorial guide

### Guided Tutorial 16.1: Journal Entry Monitoring

**Purpose.** Students start internal audit's own file and rebuild Chapter 8's five tests as flags. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 4 (the flags), Step 8 (the filter on a score), Step 10 (drill-through) and Step 12 (Test 1). Leave Steps 1 to 3, 5, 6, 7, 9 and 11 to students.

| Step | Look for | Value |
|---|---|---|
| 4, 5 | The five flags | {% for f in t1.flags %}{{ f[0] }} {{ f[1] }}{{ ", " if not loop.last else "" }}{% endfor %} |
| 7 | Scores 0 to {{ t1.scores|length - 1 }} | {% for s in t1.scores %}{{ s.n }}{{ ", " if not loop.last else "" }}{% endfor %} entries |
| 8 | Entries at 2 or more | {{ t1.top.number }} ({{ t1.top.type }}) first with four; {{ t1.scores[2].n }} others |
| 9, 10 | The ledger lines | {{ t1.lines|count }} lines in all; {{ t1.top.number }} has {{ t1.top.lines }}, each side ${{ t1.top.debits|money }} |
| 11 | JE Exceptions | {{ t1.exceptions }} rows, not loaded |
| 12 | Test 1 | {{ t1.n }} entries; ${{ t1.total|money }} = debits = credits |

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
| 3, 5 | The new flags | {% for p in ['PO', 'PR'] %}{{ p }}: {% for nm, k in t2.tests[p] %}{{ nm }} {{ k }}{{ ", " if not loop.last else "" }}{% endfor %}{{ "; " if not loop.last else "" }}{% endfor %} |
| 7 | The register | {{ t2.n }} rows: {{ t2.process_n['JE'] }}, {{ t2.process_n['PO'] }}, {{ t2.process_n['PR'] }} |
| 10 | Population and rate | {{ t2.po.n|count }} orders, {{ t2.pr.n|count }} registers; a total row with no rate |
| 11 | The heat map | January darkest; PR SelfApproved {{ t2.self_low }} to {{ t2.self_high }} in every month name; December JE AboveLimit {{ t2.december }}, the year-end closes |
| 12 | Approvers | {{ t2.approvers[:5]|join(", ") }}, the rest by job title |
| 13 | Drill-through | {{ t2.diaz_orders|capitalize }} PO AfterTermination orders, one approver, who approved only those |
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
| 1 | The dispositions | {{ t3.n_disp }} rows: {% for k in t3.kinds %}{{ k[0] }} {{ k[1] }}{{ ", " if not loop.last else "" }}{% endfor %} |
| 2, 3 | Test 3 | {{ t3.n }} exceptions, {{ t3.n_keys }} keys; {{ t3.n_disp }} dispositions, {{ t3.n_disp_keys }} keys; reviewed {{ t3.reviewed }}; open {{ t3.open }} |
| 4 | Open by year | JE {{ t3.open_years['JE']|join(", ") }}; PO {{ t3.open_years['PO']|join(", ") }}; PR {{ t3.open_years['PR']|join(", ") }} |
| 5 | Two tests or more | {{ t3.n_multi }} documents; {{ t3.je_top }} with {{ t3.je_top_n }} |
| 6 | Test 4 | {{ t3.orders|count }} orders, {{ t3.unique|count }} unique, first {{ t3.first }}, last {{ t3.last_number|count }}; {{ t3.registers|count }} registers, {{ t3.unpaid|length }} with no payment record |
| 7 | Data Through | {{ t3.through }}; by year {{ t3.through_years|join(", ") }} |
| 8 | The package's tests | Test 1 by year {% for r in t3.test1 %}{{ r[0]|count }}{{ ", " if not loop.last else "" }}{% endfor %} lines; Test 3 {{ t3.tb_accounts }} accounts, ${{ t3.tb|money }}; Test 5 {% for r in t3.test5 %}{{ r|num(2) }}{{ ", " if not loop.last else "" }}{% endfor %} |

**Stumbles to expect**

- Step 1: keys that do not match character for character (see the pitfalls). The six Deficiency rows rest on the tutorial's assumption that the reviewer looked past the register, at the approval log, the employment records and the earnings. Ask what the flags alone would support.
- Step 3: a Test 3 that reads reviewed equal to dispositions and so passes a disposition typed twice: the key counts catch it.
- Step 7: MAX in place of MINX.
- Step 8: the package saved over, or a test run without its comment line.
- Step 9: the registers approved by their own employee reported document by document. The memo reports them once.

**The checkpoint to look for.** The four bullets. A strong student calls the card a bound observed in the extract, proving neither a refresh nor a complete payroll.

## Difficult ideas and misconceptions

**An exception is not an anomaly.** Tutorial 16.2 and Exercises 16.5 and 16.6, question 2. A rule fails or holds. A near-duplicate or a first-digit departure is a reason to look. Ask: which of these needs an explanation before anyone calls it a problem?

**A count is not a rate.** Exercise 16.4, question 6. Purchase order exceptions rose by {{ e4.rose }} ({{ e4.po_n[1] }} to {{ e4.po_n[2] }}) and the rate {{ e4.moved }}, because orders grew by {{ e4.growth|pct(0) }}. Ask: how many orders were there?

**A recurring exception is one finding.** Tutorial 16.2 Step 11, question 11. The {{ t2.selfs.n }} registers are a design question: one approver approves every register, including the approver's own. Ask: what control would stop them?

**Open is not unresolved.** Tutorial 16.3, question 9. An open exception has no disposition. The {{ t3.follow }} follow-ups and {{ t3.deficient }} deficiencies are reviewed and still await action. Ask: which list holds the matters to track?

**A disposition belongs to an exception.** Tutorial 16.3 Step 5. The departed approver's {{ t2.diaz_orders }} orders are reviewed for one test and open for another. Ask: how many exceptions does one order hold?

{{ figure('IF-16-0-D') }}

**More exceptions than reviewers can examine.** Tutorial 16.3, question 10. Li and colleagues and Alles and colleagues describe alarm floods. The chapter's answer is a simple order and one disposition for what is expected or recurs. Ask: what would you change in the rules before adding reviewers?

**An uncontrolled copy is not the controlled report.** Question 14. A .pbix that imports its data holds every row, and a copy kept outside the approved release stops at the date of the copy. Ask: who holds copies of the package?

**A process's rate counts failed tests.** Tutorial 16.2 Step 10. A document that fails two tests counts twice. Ask: what does the journal entry rate count?

**Agreeing totals do not prove completeness, and Data Through proves no refresh.** Tutorial 16.1 Step 12, Tutorial 16.3 Step 7, question 12. Ask: what could be missing from both totals?

**Who sees the report matters.** Question 3. Gonzalez and Hoffman found that prompt notice can encourage fraud when detection is weak. The chapter calls it a reason to think, not a rule. Ask: what does a notice reveal about what the test cannot detect?

**A filter reaches only what it is related to.** Tutorial 16.2 Step 12c, Exercise 16.6. Employee reaches the entries and not the orders or registers; {{ e6.cfo.name }} approved {{ e6.cfo.share|pct(2) }} of the orders, and a plain count shows every order on every row. Ask: which tables does the employee filter?

## Discussion prompts

1. **Should the monitoring report go to the managers whose approvals it tests?** It reaches Gonzalez and Hoffman and the chapter's split: the report to the people who oversee the controls, the exceptions to those who must explain them.
2. **The recurring payroll test fires every month. Keep it, retire it or reclassify it?** It reaches one finding, then a test that the approver's own pay has another approver, and the unexplained rate.
3. **Who should write dispositions, and what should the record show?** It reaches who and when in the record, a reviewer who is not the preparer, and review by the chief audit executive.
4. **A December page shows no payroll exceptions after {{ mq.pay_day }}. What can you conclude?** It reaches the open pay periods that hold the rest of December's work, and Data Through as a bound on what the tests saw, not proof of a complete payroll.
5. **Next month brings dozens of new exceptions. How do you order the review?** It reaches the score, novelty and Li and colleagues, and the alarm floods Alles and colleagues found at Siemens.
6. **A measure passed its test in April and was changed in May. Do you trust it?** It reaches rerunning the tests, the change record and the project under version control.
7. **Should anomaly tests share the register with rule tests?** It reaches the register's five columns, a different disposition path, and keeping the two layers apart.
8. **Who approves the approver?** It reaches {{ e6.manager.share|pct(0) }} of the registers on one approver and the segregation and absence questions.

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

{{ figure('IF-16-0-C') }}

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 3.** Option A inverts the finding and B denies any effect; the fraud inclination rose only with a weak system.
- **Question 5.** Option C carries over UNION ALL's habit of matching by position. Append matches by name.
- **Question 7.** Option C reads size as seriousness; D discards the design finding as noise.
- **Question 9.** Option D confuses a null with a mistyped key. The null marks the exception open; Test 3 finds the mistype.
- **Question 10.** Option C is the recurring design finding, one finding, not first; B is expected; D takes age over score. The stem holds amounts and urgency alike, so the chapter's simple order applies.
- **Question 11.** Option A reviews each register separately; D treats a design flaw as expected.
- **Question 12.** Option A sounds like a refresh problem. The card shows only that no payroll register has a later pay date, a bound observed in the extract.
{% if not n_longest %}
- **Length.** In none of the {{ n_questions }} questions is the correct option also the longest, so wording alone does not give it away.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 3 make a quiz on monitoring and its tests, 4 to 6 on the register, 7 to 11 on the review, and 12 to 14 on auditing the reports.

## Connections

**Builds on.** Chapter 4's control totals and Documentation worksheet; Chapter 8's tests, risk score and dispositions; Chapter 12's audit query library with its UNION ALL, the payroll tests of Exercise 12.5 and the surge days; Chapter 13's Validation page; Chapter 14's Date table, DAX query view tests, CALCULATE and TREATAS; and Chapter 15's package, whose Tests tab and About page this chapter reruns and reads.

**Later chapters.** The appendix on publishing and security secures and shares the package; its start folder also holds Audit Monitoring at the end of this chapter. The Part IV case builds a new report with the same Validation page, Tests tab and Data Through card. Part V's capstone cases draw on every tool of the book.

**Appendices.** The appendix on Power BI in the browser rebuilds Chapter 13's model there. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
