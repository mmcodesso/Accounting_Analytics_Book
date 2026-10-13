---
uses: [ch19.g0, ch19.g3, ch19.g4, ch19.m1, ch19.m2, ch19.m3, ch19.r8, ch19.r10]
title: 'Chapter 19: Auditing the Customer Credits Cycle'
kind: case-notes
unit: '19'
minutes: 240
tool: mixed
figures:
  - id: IF-19-0-A
    kind: diagram
    purpose: How the ten requirements, the four model files and the three milestones fit, for the kickoff.
    shows: "Three columns, one for each phase, holding ten boxes for the requirements in order (1 to 3; 4 to 7; 8 to 10). Each box carries a tag for its tool: SQL, Excel or Power BI, two tags where a requirement uses both. Arrows run from the query results to the workbook, from the refund flags exported by Requirement 4 to the Power BI report, from the workbook's evaluation to the report to the committee, and from Chapter 16's register to Requirement 10. Three checkpoints, one for each milestone, sit under the columns."
    data: none; the boxes and tags come from the case's requirements and its tools table.
  - id: IF-19-0-B
    kind: chart
    purpose: The deficiencies' exposure against the three thresholds, the picture behind classifying by likelihood and magnitude and not by counts.
    shows: "Horizontal bars for the last fiscal year: credits above the approver's authority, the credits that fail the authority or the cash test counted once, refunds above authority, refunds before the payment, the refunds that fail either counted once, and all credits of the year as the potential magnitude. Three vertical reference lines mark the clearly trivial threshold, performance materiality and overall materiality, each labeled. Dollar labels on the bars."
    data: The exposures of Requirement 8 and the thresholds of Requirement 3.
---
{% set c = ch19_g0 %}
{% set s = c.s %}
{% set m1 = ch19_m1 %}
{% set m2 = ch19_m2 %}
{% set m3 = ch19_m3 %}
{% set r8 = ch19_r8 %}
{% set r10 = ch19_r10 %}
# Chapter 19: Auditing the Customer Credits Cycle

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part V, Capstone Cases. The case is an independent final-project option: it asks for nothing from another capstone. Chapters 8, 12 and 16, whose internal auditor this is, are context, and the Part III and Part IV case files are only an optional head start |
| Analytics types | Descriptive (Requirements 1 and 2), diagnostic (4, 5 and 7), a small predictive model (the expectation of returns, Requirement 3), statistical inference (the sample, Requirement 6) and prescriptive (the recommendations and action plans, Requirements 9 and 10) |
| Tools | SQL in DB Browser for SQLite, Excel and Power BI Desktop. Where the choice is clear the requirement says why a tool fits; where it is not, students choose and explain |
| Components | Ten requirements in three phases, with a milestone after each; no tutorials, exercises or questions. The deck has {{ c.slides }} slides. The model answer is four files: Credits.sql ({{ c.n_queries }} queries), Credits Audit.xlsx ({{ c.n_sheets }} worksheets), the Power BI project Credits Analytics ({{ c.n_pages }} pages, {{ c.checks }} checks) and Audit Monitoring updated |
| Files students need | CharlesRiver.sqlite, copied as CharlesRiver_Capstone.sqlite; CharlesRiver.xlsx; the three files they build; Audit Monitoring.pbix from Chapter 16 if they built it. Solutions: Chapter19-capstone-sql.zip, Chapter19-capstone-excel.zip, Chapter19-capstone-pbi.zip and Chapter19-capstone-pbi-monitoring.zip |
| Deliverables | The script; the workbook; the report and the register; a report to the audit committee of three pages with an appendix of three |
| Time | Class: about {{ meta.minutes }} minutes in Plan A. Students: about {{ c.student_hours }} hours in all, from {{ c.plan[10] }} minutes for Requirement 10 to {{ c.plan[4] }} for Requirement 4 |

The case depends on these conditions of the data, all visible in the files students build:

- Every population ties to the ledger by year to the cent: {{ m1.credits }} credits (${{ m1.credit_total|money }}), {{ m1.refunds }} refunds (${{ m1.refund_total|money }}), {{ m1.clawbacks }} clawbacks (${{ m1.clawback_total|money }}). Account `2060` is a hub with large flows and a balance of a few thousand dollars (${{ m1.b2060[0]|money }}, ${{ m1.b2060[1]|money }} and ${{ m1.b2060[2]|money }} at the year-ends).
- The year-end closes post to `4060` and `6290` and zero every revenue and expense account, so every account-level query needs them left out.
- Neither the credit memo nor the refund records a preparer, and GLEntry.CreatedByEmployeeID names the approver on every row. MaxApprovalAmount is a general limit, not a delegation of authority.
- The records hold dates, not times, and the tables end on different dates ({{ c.dt.SalesReturn }} for returns, {{ c.dt.CreditMemo }} for credits, {{ c.dt.CustomerRefund }} for refunds).
- The generator plants no anomaly in this cycle, so the patterns come from how the data were produced, and every finding is worded as what the records show.
- Materiality, the key-item thresholds and the sampling parameters are the case's assumptions, not data.

## What students should be able to do afterward

1. Plan an integrated audit of a cycle: map it from its records, reconcile each population to the ledger, and set materiality. Practiced in Requirements 1, 2 and 3.
2. Assess the cycle's risks, including fraud, and link each to a control point, a test and the evidence it needs. Practiced in Requirements 3 and 4.
3. Tell a test of controls from a substantive test, and decide when a query of the whole population replaces a sample. Practiced in Requirements 4, 6 and 7.
4. Size an attribute sample, select it at random with key items taken in full, and evaluate it with an upper deviation limit. Practiced in Requirement 6.
5. Explain the growth of returns and rank refunds with descriptive and diagnostic analytics, allowing for timing and for periods the data do not complete. Practiced in Requirement 5.
6. Classify deficiencies by likelihood, magnitude and compensating controls, and report them to a committee with action plans and the tests that keep watching. Practiced in Requirements 8, 9 and 10.

## Preparing to teach

**Before the first class**

- Check the software. Students need DB Browser for SQLite, Excel for Microsoft 365 (RANDARRAY, SORTBY and BETA.INV for Requirement 6; the model workbook also uses XLOOKUP, LET, UNIQUE and VSTACK) and Power BI Desktop, which runs only on Windows. Students on a Mac need a Windows computer for Requirements 5 and 10.
- Open the model answer as Opening a Companion File on the Downloads page describes. Credits Analytics reads CharlesRiver.xlsx and RefundFlags.csv from one folder: copy both there or use **Change Source**, and refresh once before class. Audit Monitoring is a separate project.
- Run Credits.sql top to bottom on a copy of the database: every query returns in a fraction of a second. In **DAX query view**, run the Checks tab of Credits Analytics: all {{ c.checks }} rows agree.
- In the workbook, the amber cells hold values pasted from Credits.sql. After a new run of the script, paste them again: **Data > Refresh All** does not rerun the script.
- Open the deck. Slides {{ s.kick }} set out the question and the criteria, slides {{ s.cycle }} the cycle and its risks, and slides {{ s.deficient }} the classification of deficiencies.

**Pitfalls that cost class time**

- The closes (slide {{ s.watch1 }}). A query by account includes them: reconciliations and materiality fail until they are left out.
- The hub and the date (slides {{ s.watch1 }} and {{ s.watch2 }}). Account `2060` is reconciled flow by flow, and a balance, a payment or a past-due amount is as of the day of the event, not today.
- Definitions (slide {{ s.r4 }}). "Refunded before the payment" has more than one reading; the case asks students to state theirs. Grade the statement, not the count.
- The preparer (slide {{ s.watch1 }}). The ledger's creator is the approver; students who read it as the preparer find a deficiency that is not in the records.
- Query or sample (slides {{ s.sampling }} and {{ s.r6 }}). A query replaces a sample only where the records hold the evidence. Requirement 6 has no results to report: students who invent results lose the point of the plan.
- Wording (slide {{ s.watch3 }}). A finding says what the records show, never what someone did.
- Severity (slides {{ s.deficient }}). Classify by likelihood and magnitude, not by the number of exceptions.

## Teaching approaches

**Plan A: take-home work with five class touchpoints ({{ meta.minutes }} minutes in class).** It fits a course that wants the work done outside class and catches the errors that compound: the closes, the dates, the definitions and the wording. The risk is a late start, so assign Requirements 1 to 3 at the kickoff.

| Touchpoint | Minutes | Activity | Slides |
|---|---:|---|---|
| 1. Kickoff | 10 | The question, deliverables and criteria | {{ s.kick }} |
| 1. Kickoff | 10 | The engagement and the chief audit executive's conditions | {{ s.engage }} |
| 1. Kickoff | 20 | The cycle, its control points and the fraud schemes | {{ s.cycle }} |
| 1. Kickoff | 10 | The data and the three Watch outs | {{ s.data }} |
| 1. Kickoff | 10 | Set up the files; choose the tool for each step | {{ s.setup }} |
| 2. Milestone 1 | 15 | The map and the reconciliations | {{ s.r1 }}, {{ s.r2 }} |
| 2. Milestone 1 | 15 | Materiality, the expectation and the matrix | {{ s.r3 }} |
| 2. Milestone 1 | 10 | Test or substantive; self-check | {{ s.check2 }}, {{ s.m1 }} |
| 3. Milestone 2 | 20 | The controls on every document; the definitions | {{ s.r4 }} |
| 3. Milestone 2 | 10 | The returns and the refund ranking | {{ s.r5 }} |
| 3. Milestone 2 | 15 | Sampling and the evidence outside the database | {{ s.sampling }}, {{ s.r6 }} |
| 3. Milestone 2 | 10 | The balances and the largest refund | {{ s.r7 }} |
| 3. Milestone 2 | 5 | Query or sample; self-check | {{ s.check3 }}, {{ s.m2 }} |
| 4. Milestone 3 | 15 | What makes a control deficient; the classifications | {{ s.deficient }} |
| 4. Milestone 3 | 10 | The evaluation of the deficiencies | {{ s.r8 }} |
| 4. Milestone 3 | 10 | The report and the expected pushback | {{ s.r9 }} |
| 4. Milestone 3 | 5 | Keeping the tests running | {{ s.r10 }} |
| 4. Milestone 3 | 5 | Severity check; self-check | {{ s.check4 }}, {{ s.m3 }} |
| 5. Debrief | 20 | Each group states its conclusion in two sentences and hears the owners | {{ s.r9 }} |
| 5. Debrief | 10 | What the case practiced; after the report | {{ s.ahead }} |
| 5. Debrief | 5 | The checklist | {{ s.deliver }} |
| | {{ meta.minutes }} | Total | |

**Plan B: lab sessions (five sessions of 150 minutes, 750 minutes in all).** Students work in class on the data-heavy phases and you circulate. It fits a computer lab. Requirements 6 to 10 are done outside class; use touchpoints 3 to 5 of Plan A for them.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 30 | Kickoff: deliverables, criteria and the three Watch outs | {{ s.kick }}, {{ s.data }} |
| 1 | 120 | Requirement 1 | {{ s.r1 }} |
| 2 | 120 | Requirement 2 | {{ s.r2 }} |
| 2 | 30 | Requirement 3: materiality | {{ s.r3 }} |
| 3 | 90 | Requirement 3: the expectation, the brainstorm and the matrix | {{ s.r3 }}, {{ s.m1 }} |
| 3 | 60 | Requirement 4: authority and separation of duties | {{ s.r4 }} |
| 4 | 150 | Requirement 4: timing, the past-due balance, the clawbacks | {{ s.r4 }} |
| 5 | 30 | Requirement 4: the combined list and the export | {{ s.r4 }} |
| 5 | 120 | Requirement 5: the model, the measures and the pages | {{ s.r5 }}, {{ s.m2 }} |
| | 750 | Total | |

**Plan C: committee workshop (90 minutes).** Students arrive with Requirements 1 to 9 done. Groups of four play the audit team (two), an owner of the cycle and a member of the audit committee. It fits an upper-level or graduate class and moves the learning to the pushback. The risk is an early error found late, so collect the workbook and the report the day before and read the evaluation matrix.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval: test or substantive, query or sample, what decides severity | {{ s.check2 }}, {{ s.check3 }}, {{ s.check4 }} |
| 20 | Each audit team states its bounded conclusion and its most serious finding: condition, criteria, cause, effect | {{ s.r9 }} |
| 30 | The owners answer from their compensating controls; the audit team replies with the evidence | {{ s.r8 }}, {{ s.r9 }} |
| 20 | Revise the ratings and the action plans in the light of the owners' evidence | {{ s.r8 }} |
| 10 | Looking ahead | {{ s.ahead }} |
| 90 | Total | |

## Milestone guide

Students hand in a milestone, and you may then release its checkpoint values so that an early error does not carry through the audit. A quick check for each is to compare one or two numbers before reading anything else.

### Milestone 1: Plan the audit

Students hold the map of the cycle, the reconciliations, the thresholds and the risk-and-control matrix.

| Quantity | Value |
|---|---|
| Returns; credits; refunds; clawbacks | {{ m1.returns }}; {{ m1.credits }}; {{ m1.refunds }}; {{ m1.clawbacks }} |
| Credit SubTotal by year, equal to `4060` | ${{ m1.subtotals[0]|money }}; ${{ m1.subtotals[1]|money }}; ${{ m1.subtotals[2]|money }} |
| Balance of `2060` at the year-ends | ${{ m1.b2060[0]|money }}; ${{ m1.b2060[1]|money }}; ${{ m1.b2060[2]|money }} |
| Income; materiality; performance; clearly trivial | ${{ m1.income|money }}; ${{ m1.mat|money }}; ${{ m1.perf|money }}; ${{ m1.trivial|money }} |
| Expected returns against recorded | ${{ m1.exp|money }}; ${{ m1.actual|money }} |

**Quick check:** every difference in the reconciliation is zero and the closes are named as excluded. A balance of `2060` can tie while one of its flows is wrong, so look for the reconciliation of each flow.

### Milestone 2: Test controls and balances

Students hold the control tests with their definitions, the report, the sampling plan with its frozen selection, and the substantive tests and timeline.

| Quantity | Value |
|---|---|
| Credits above the approver's limit | {{ m2.cm_above }} (${{ m2.cm_above_total|money }}) |
| Credits whose approver also applied cash | {{ m2.cash_credit }} |
| Refunds above the limit | {{ m2.rf_above }} (${{ m2.rf_above_total|money }}) |
| Refunds before the last application; by receipt date | {{ m2.before }} (${{ m2.before_total|money }}); {{ m2.before_rcpt }} (${{ m2.before_rcpt_total|money }}) |
| Key items; the remainder; the sample | {{ m2.key }} (${{ m2.key_total|money }}); {{ m2.rest }}; {{ m2.sample }} |
| The largest refund; its amount; unpaid on its invoice | {{ m2.big }}; ${{ m2.big_amount|money }}; ${{ m2.unpaid|money }} |

**Quick check:** each count comes with the definition that produced it. The sample is frozen with its date and parameters and the rule written before any test, and there are no results for the documents outside the database.

### Milestone 3: Evaluate and report

Students hold the evaluation of the deficiencies, the report to the committee and the register with the new tests.

| Quantity | Value |
|---|---|
| Credits that fail authority or the cash test, each counted once; exposure | {{ r8.u12[0] }}; ${{ r8.u12[1]|money }} |
| Refunds that fail authority or timing, each counted once; exposure | {{ r8.u34[0] }}; ${{ r8.u34[1]|money }} |
| Exceptions added to the register | {{ m3.additions[0] }}; {{ m3.additions[1] }}; {{ m3.additions[2] }}; {{ m3.additions[3] }} |
| Rows in the register, before and after | {{ r10.old }}; {{ r10.new }} |

**Quick check:** the ratings are provisional, resting on the records and on compensating controls not yet tested: two significant deficiencies (credits and refunds), the Accounting Manager's concentration a deficiency, and no material weakness identified on the records. A reasoned rating of material weakness over credits is accepted. The report's conclusion says what the tests could not reach.

## Difficult ideas and misconceptions

- **A tie is not a proof.** A reconciliation shows that the populations are complete against the ledger, not that the amounts are right. Ask which requirement recomputes them.
- **A clean anti-join proves less than it seems.** It finds records that point at nothing, not the record that was never made. Ask what would show a missing document.
- **As of the day.** A customer's past-due balance or a payment is read as of the refund date. On today's balances no refund finds a past-due invoice at all. Ask what the customer owed that day.
- **Dates are not times.** "Before the payment" depends on the date used and on the same-day case, and no table shows when a payment cleared the bank. Ask which reading the student chose and why.
- **The creator is not the preparer.** GLEntry.CreatedByEmployeeID names the approver on every credit and refund row. Ask what it names on the sales invoices.
- **Query or sample.** The records hold the approver and the limit, so a query tests every credit. A written request or an inspection record is a document outside the database, and the inspection applies only to the refunds of damaged returns; a draw across all refunds would pass the others as inspected.
- **Severity is not a count.** It turns on likelihood, magnitude and compensating controls. Ask students to put the exposures beside the thresholds.

- **A pattern is not an act.** A refund method unlike the customer's payments is an anomaly to follow up: a method chosen at random would mismatch about as often. Ask what evidence would turn it into a finding.
- **Inference is not a forecast.** An upper deviation limit says what the population could be, not what will happen.

{{ figure('IF-19-0-B') }}

## Discussion prompts

1. Are the controls over credits and refunds adequate? A good discussion reaches approvers whose general limit is zero, the cash and the credits handled by one department, the missing preparer, and that every compensating control is untested.
2. Which findings would you hold back until evidence from outside the database arrives? A good discussion separates what the records show from what only a document, a bank or a policy can settle.
3. When does a query replace a sample? A good discussion reaches the evidence's location and the cost of a result that cannot be inspected.
4. How would you word the finding on the largest refund? A good discussion reaches a description of the timeline, a disposition of follow up, and the evidence that would settle it.
5. Should a refund wait for the customer's cleared payment? A good discussion weighs the control against its cost to customers and names the data that would show the cost.
6. What should the committee hear first? A good discussion reaches the bounded conclusion and what the tests could not reach, before the ratings.
7. Which tool choices would change on another dataset? A good discussion reaches the reasons each requirement gives for its tool.

## Using the requirements

| Requirement | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1. Map the cycle from its records (Chapters 3, 10, and 12) | Auditing | SQL | {{ c.plan[1] }} min | Intermediate | 1 |
| 2. Reconcile each population to the ledger (Chapters 8 and 12) | Auditing | SQL | {{ c.plan[2] }} min | Intermediate | 1 |
| 3. Assess the risks and set materiality (Chapters 6 and 8) | Auditing | Excel | {{ c.plan[3] }} min | Intermediate | 1, 2 |
| 4. Test the controls on every document (Chapters 10 to 12) | Auditing | SQL | {{ c.plan[4] }} min | Advanced | 2, 3 |
| 5. Explain the returns and rank the refunds (Chapters 13 to 15) | Auditing | Power BI | {{ c.plan[5] }} min | Intermediate | 5 |
| 6. Sample what the database cannot show (Chapter 8) | Auditing | Excel | {{ c.plan[6] }} min | Advanced | 3, 4 |
| 7. Test the balances, and follow the largest refund (Chapters 8 and 12) | Auditing | SQL and Excel | {{ c.plan[7] }} min | Advanced | 3 |
| 8. Evaluate the deficiencies (Chapter 8) | Auditing | Excel | {{ c.plan[8] }} min | Advanced | 6 |
| 9. Report to the audit committee | General | Excel and a written report | {{ c.plan[9] }} min | Advanced | 6 |
| 10. Keep the tests running (Chapter 16) | Auditing | Power BI | {{ c.plan[10] }} min | Intermediate | 6 |

Every requirement is part of the case, and each phase uses what the one before found. The figure shows how the files feed one another and the report.

{{ figure('IF-19-0-A') }}

Four bundles:

- **The full case (the default).** All ten requirements, graded with the rubric below. About {{ c.student_hours }} hours.
- **A controls-testing version without Power BI.** Requirements 1 to 4 and 6 to 9, with a two-page report. It suits a course with no Windows computers and leaves out the report of Requirement 5 and the register of Requirement 10.
- **An analytics-and-monitoring version.** Requirements 1, 2, 4, 5 and 10 and a one-page memo on what the tests show. It leaves out the sample, the balances and the evaluation.
- **Teams of three.** One student leads each tool (SQL for Requirements 1, 2, 4 and 7, Excel for 3, 6, 8 and 9, Power BI for 5 and 10), the report is shared, and each writes a one-page reflection on the definitions chosen.

The check slides suit class discussion. Requirements 1 and 2 grade from the script, because each ends in zeros and ties; Requirement 4 query by query; Requirements 3, 6 and 8 from the workbook; Requirement 5 from the Tests tab; Requirements 9 and 10 from the written work. A fast way to grade is to read the report's conclusion and its evaluation table, then trace one number in each row back to the script.

## Assessment rubric

| Requirement | Weight | What carries the points |
|---|---:|---|
| 1. The map | {{ c.weights[1] }} | Profiles, links tested both ways, the ledger trace, numbering, the posting matrix, the marked control points |
| 2. Reconciliations | {{ c.weights[2] }} | Each population tied by year from both sides, the hub flow by flow, items named, exclusions stated |
| 3. Risks and materiality | {{ c.weights[3] }} | Named threshold cells, the expectation judged against two thresholds, a brainstorm from the records, a matrix with evidence location |
| 4. Control tests | {{ c.weights[4] }} | Each test with its definition, as-of dates, the preparer not testable, clean results reported, the combined list and the export |
| 5. The report | {{ c.weights[5] }} | Rates by both dates, timing allowed for, concentration as a share of sales, the score and drill-through, Validation and Tests |
| 6. The sample | {{ c.weights[6] }} | Three attributes with the third on its own population, parameters, key items, a frozen selection, the rule written first, no invented results |
| 7. The balances | {{ c.weights[7] }} | Recomputed credits, restocking by reason, lapping tests, the first-digit reasoning, the largest refund's timeline and its disposition |
| 8. Deficiencies | {{ c.weights[8] }} | A matrix against the threshold cells, design or operation, exposure, likelihood, compensating controls, a classification with what could change it |
| 9. The report | {{ c.weights[9] }} | Page limits, a bounded conclusion, findings with condition, criteria, cause, effect, rating and recommendation, action plans, the expected pushback |
| 10. Continuing tests | {{ c.weights[10] }} | Four rule tests and two processes in the register, anomalies kept outside, one design finding, the data-through date rechecked and the change recorded |
| Total | 100 | |

Four criteria run through every requirement.

| Criterion | Full credit looks like | Assessed mainly in |
|---|---|---|
| Accuracy | Populations tie to the ledger to the cent; each count carries its definition | Requirements 1, 2, 4 and 7 |
| Evidence | Every number traces to a query, a formula or a frozen selection; clean results reported; the limits of each test named | Requirements 4, 5, 6 and 8 |
| Judgment | Severity by likelihood, magnitude and compensating controls; query or sample chosen for a reason; ratings provisional where the evidence is outside | Requirements 3, 6, 8 and 9 |
| Communication | Findings worded as what the records show; a report the owners can act on | Requirements 9 and 10 |

Each requirement guide has its own grading table out of 100; scale it by the weight above to place it in the case grade.

## Connections

**Builds on.** Chapter 3's trace of a document to the ledger; Chapter 6's expectations and reconciliations; Chapter 8's reconciliations, random selection, sampling and dispositions; Chapters 10 and 11 for joins, anti-joins and as-of dates; Chapter 12's approval and trace tests and Audit.sql; Chapters 13 to 15 for the model, the measures and drill-through; and Chapter 16's exception register, design findings and change control. The internal auditor of Chapters 8, 12 and 16 is the same role.

**What builds on it.** Nothing in the book depends on this case. The tests in the register keep running after the report, which is the point of its Looking Ahead, and the book's closing thoughts draw on the audit standards it cites.

**Appendix D** maps each requirement to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each requirement guide names the competencies it practices.
