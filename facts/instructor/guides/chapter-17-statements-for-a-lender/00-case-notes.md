---
uses: [ch17.g0, ch17.m1, ch17.m2, ch17.m3, ch17.m4]
title: 'Chapter 17: Financial Statements for a Lender'
kind: case-notes
unit: '17'
minutes: 220
tool: mixed
figures:
  - id: IF-17-0-A
    kind: diagram
    purpose: How the nine requirements, the three files and the four milestones fit together, for the kickoff.
    shows: "Four columns, one for each phase, holding nine boxes for the requirements in order (1 and 2; 3 to 5; 6 and 7; 8 and 9). Each box carries a tag for its tool: SQL, Excel or Power BI, two tags where a requirement uses more than one. Arrows run from the SQL results to the workbook, from the workbook's adjustment lines to the Review file, and from all three files to the memo. Four checkpoints, one for each milestone, sit under the columns."
    data: none; the boxes and tags come from the case's requirements and its tools table.
  - id: IF-17-0-B
    kind: diagram
    purpose: The dates of the case, which students must not mix.
    shows: "One horizontal timeline from the opening entry on the first day of the first fiscal year through the three year-ends to the ledger's last posting. Each year-end carries two marks for its two closes. After the last year-end, three dates are labeled in order: the last pay date with registers, the last day of the year (the data-through date) and the ledger's last posting, with a bracket after the second date labeled supplier payments only."
    data: The opening entry's date, the three year-ends, the last pay date, and the ledger's last posting, from the ledger (Requirement 1).
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% macro sg(x) %}{{ "-" if x < 0 else "+" }}${{ (x|abs)|money }}{% endmacro %}
{% set c = ch17_g0 %}
{% set s = c.s %}
{% set m1 = ch17_m1 %}
{% set m2 = ch17_m2 %}
{% set m3 = ch17_m3 %}
{% set m4 = ch17_m4 %}
# Chapter 17: Financial Statements for a Lender

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part V, Capstone Cases. The case is an independent final-project option: it asks for nothing from another capstone, and the Part III and Part IV case files are only an optional head start |
| Analytics types | Descriptive (the statements and notes), diagnostic (the rebuilt accruals, the cutoff tests, the opening balances), predictive (the estimates: payroll at a cost per working day, returns still to come) and prescriptive (what to record, pass and settle) |
| Tools | SQL in DB Browser for SQLite, Excel and Power BI Desktop. Where the choice is clear the requirement says why a tool fits; where it is not, students choose and explain |
| Components | Nine requirements in four phases, with a milestone after each; no tutorials, exercises or questions. The deck has {{ c.slides }} slides. The model answer is three files: LenderPackage.sql ({{ c.n_queries }} queries), Charles River Lender Package.xlsx ({{ c.n_sheets }} worksheets) and the Power BI project Charles River Lender Review ({{ c.n_pages }} pages, {{ c.checks }} checks) |
| Files students need | CharlesRiver.sqlite, copied as CharlesRiver_Capstone.sqlite; CharlesRiver.xlsx; and the three files they build. Solutions: Chapter17-capstone-sql.zip, Chapter17-capstone-excel.zip and Chapter17-capstone-pbi.zip |
| Deliverables | The script; the workbook; a PDF of the draft statements and notes; the Review file with its Questions table and Tests tab; a memo of two pages with an appendix of three |
| Time | Class: about {{ meta.minutes }} minutes in Plan A. Students: about {{ c.student_hours }} hours in all, from 90 minutes for Requirement 1 to 180 for each of Requirements 5 and 6 |

The case depends on these conditions of the data, all visible in the files students build:

- The ledger records net income of {{ sm(m1.ni[2]) }} for {{ d.C }} and has no income tax account, so every statement shows income before income taxes.
- Three trial balances ({{ m1.rec[0].n }}, {{ m1.rec[1].n }} and {{ m1.rec[2].n }} accounts) differ only in date. The closes of earlier years stay in, and {{ m1.never }} accounts have never posted.
- Fiscal {{ d.N }} holds only supplier payments ({{ m4.payments }} of them, {{ sm(m4.amount) }}), the last pay date with registers is {{ c.pay_end }}, and the ledger ends {{ c.last }}.
- Accrued expenses carry an opening line with no document, freight, and accruals that invoices cleared late or never: {{ m2.comp[0].n_old }}, {{ m2.comp[1].n_old }} and {{ m2.comp[2].n_old }} old items at the three year-ends.
- Revenue, payroll and interest are each missing from a year-end: cutoff of {{ sm(m2.cut[0]) }}, {{ sm(m2.cut[1]) }} and {{ sm(m2.cut[2]) }} in revenue, and payroll owed of {{ sm(m2.pay[0]) }}, {{ sm(m2.pay[1]) }} and {{ sm(m2.pay[2]) }}.
- Sales tax payable of {{ sm(m4.stax) }} has no remittance recorded, rent is paid from cash with no lease recorded, and balances that no document supports would raise equity by {{ sm(m4.equity) }} if none is real.

## What students should be able to do afterward

1. Prepare comparative statements, including equity and cash flows, from trial balances at successive year-ends, treating closes, opening balances and later postings correctly. Practiced in Requirements 1 and 6.
2. Rebuild a liability from the documents behind it and use subledger evidence to find the year-end adjustments for accruals, cutoff and interest. Practiced in Requirements 3 and 4.
3. Assign each adjustment to its period, tell an error from a change in estimate, and judge materiality singly and in aggregate. Practiced in Requirement 5.
4. Build note disclosures from the database and reconcile each to the statements. Practiced in Requirement 7.
5. Separate what the records can settle from what needs outside evidence, and assess liquidity and going concern as a lender would. Practiced in Requirements 8 and 9, with the questions of Requirement 2.
6. Choose Excel, SQL or Power BI for each part of a reporting task and document the work so a reviewer can rerun it. Practiced in Requirements 1 and 2, and in every requirement's evidence.

## Preparing to teach

**Before the first class**

- Check the software. Students need DB Browser for SQLite, Excel for Microsoft 365 or Excel 2024 (the model workbook uses dynamic array functions such as CHOOSECOLS, HSTACK and TAKE) and Power BI Desktop, which runs only on Windows. Students on a Mac need a Windows computer for Requirements 2 and 6.
- Open the model answer as Opening a Companion File on the Downloads page describes. The Review project reads two workbooks, CharlesRiver.xlsx and the package workbook, so use **Change Source** for both and refresh once before class; the ledger is large.
- In **DAX query view**, run the Checks tab: all {{ c.checks }} rows should agree. Run the script top to bottom on a copy of the database; every query is read-only except the views it creates.
- Open the deck. Slides {{ s.criteria }} set out the criteria, which are the six bullets of "What a Strong Submission Includes".

**Pitfalls that cost class time**

- The as-of rule (slide {{ s.r1 }}). A strict less-than, every close left out or every close left in each give a trial balance that still balances. Students trust a balanced trial balance; ask for Chapter 6's control total.
- Three dates (slides {{ s.watch }}). A balance at the ledger's last date is not a year-end balance, and payroll ends earlier than the data.
- Clearing measured from documents (slides {{ s.r3 }}). Invoice totals overstate what cleared an accrual; the ledger's postings do not.
- Cutoff by one method (slide {{ s.r4 }}). The last year-end's pay periods have no registers, so an accrual from registers alone is zero.
- Reversal (slides {{ s.err }}). A student who takes each year-end's amount as the year's effect gets the wrong sign for the last year.
- Wording. Students may reach for hidden, unpaid or fraud. The controller's third condition is that findings read as what the records show.

{{ figure('IF-17-0-B') }}

## Teaching approaches

**Plan A: take-home work with four class touchpoints ({{ meta.minutes }} minutes in class).** It fits a course that wants the work done outside class and catches the errors that compound: the as-of rule, the clearing, the cutoff method and the reversal. The risk is a late start, so assign Requirements 1 and 2 at the kickoff.

| Touchpoint | Minutes | Activity | Slides |
|---|---:|---|---|
| 1. Kickoff | 10 | The question, the deliverables and the criteria | {{ s.kick }} |
| 1. Kickoff | 20 | The situation, the data and the two Watch outs | {{ s.situation }}, {{ s.data }} |
| 1. Kickoff | 15 | Set up the files; choose the tool for each step | {{ s.setup }} |
| 2. Milestone 1 | 15 | Compare trial balances against Chapter 6's total | {{ s.r1 }} |
| 2. Milestone 1 | 15 | The Review page, the flags and the Questions table | {{ s.r2 }} |
| 2. Milestone 1 | 10 | Self-check; assign Requirements 3 to 5 | {{ s.m1 }} |
| 3. Milestone 2 | 15 | Accrued expenses: the parts and the reconciliation | {{ s.r3 }} |
| 3. Milestone 2 | 10 | Cutoff by one method | {{ s.r4 }} |
| 3. Milestone 2 | 25 | The schedule, error or estimate, materiality | {{ s.r5 }} |
| 3. Milestone 2 | 10 | Check your understanding; self-check | {{ s.check2 }}, {{ s.m2 }} |
| 4. Milestone 3 | 15 | The statements and the cash flows | {{ s.st }} |
| 4. Milestone 3 | 10 | Notes reconciled to the statements | {{ s.notes }} |
| 4. Milestone 3 | 10 | Self-check; assign Requirements 8 and 9 | {{ s.m3 }} |
| 5. Debrief | 20 | Later events and the memo | {{ s.r8 }}, {{ s.r9 }} |
| 5. Debrief | 10 | Check your understanding; self-check | {{ s.check3 }}, {{ s.m4 }} |
| 5. Debrief | 10 | Looking ahead | {{ s.ahead }} |
| | {{ meta.minutes }} | Total | |

**Plan B: lab sessions (four sessions of 150 minutes, 600 minutes in all).** Students work in class on the data-heavy phases and you circulate. It fits a computer lab. Requirements 6 to 9 are done outside class; use the last two touchpoints of Plan A for them.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 30 | Kickoff: deliverables, criteria and the two Watch outs | {{ s.kick }}, {{ s.watch }} |
| 1 | 120 | Requirement 1, and the Review file's model | {{ s.r1 }}, {{ s.r2 }} |
| 2 | 150 | Requirement 2's review and sources; Requirement 3 begins | {{ s.r2 }}, {{ s.r3 }} |
| 3 | 150 | Requirement 3's reconciliation and decision; Requirement 4 | {{ s.r3 }}, {{ s.r4 }} |
| 4 | 150 | Requirement 5: the schedule and the judgment | {{ s.r5 }} |
| | 600 | Total | |

**Plan C: memo workshop (90 minutes).** Students arrive with Requirements 1 to 8 done. It fits an upper-level or graduate class and moves the learning to the writing. The risk is an early error found late, so collect the schedule of adjustments the day before and mark it.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval: each pair states what the ledger could not settle | {{ s.ahead }} |
| 15 | Each pair states its recommendation in one sentence; the room compares | {{ s.r9 }} |
| 30 | Draft the matters section from the Requirement 9 outline | {{ s.r8 }}, {{ s.r9 }}, {{ s.check3 }} |
| 25 | Swap drafts and review them against the Requirement 9 grading guide | {{ s.before }} |
| 10 | Looking ahead | {{ s.ahead }} |
| 90 | Total | |

## Milestone guide

Students hand in a milestone, and you may then release its checkpoint values so an early error does not carry through the case. A quick check for each is to compare one or two numbers before reading anything else.

### Milestone 1: The ledger as it stands

Students hold three trial balances from one query, the recorded statements, the accounts never posted, the Review file and the Questions table.

| Quantity | {{ d.F }} | {{ d.P }} | {{ d.C }} |
|---|---:|---:|---:|
| Accounts; at zero | {{ m1.rec[0].n }}; {{ m1.rec[0].zero }} | {{ m1.rec[1].n }}; {{ m1.rec[1].zero }} | {{ m1.rec[2].n }}; {{ m1.rec[2].zero }} |
| Debit balances (equal to credit) | {{ sm(m1.rec[0].debits) }} | {{ sm(m1.rec[1].debits) }} | {{ sm(m1.rec[2].debits) }} |
| Net income | {{ sm(m1.ni[0]) }} | {{ sm(m1.ni[1]) }} | {{ sm(m1.ni[2]) }} |
| Total assets | {{ sm(m1.rec[0].ta) }} | {{ sm(m1.rec[1].ta) }} | {{ sm(m1.rec[2].ta) }} |

**Quick check:** the last debit balance is Chapter 6's control total. If it fails, look at which closes the query left out. {{ m1.never }} accounts have never posted, and none is an income tax account.

### Milestone 2: The adjustments

Students hold accrued expenses rebuilt and reconciled, the cutoff measures, and the schedule with its evidence and its materiality judgment.

| Quantity | {{ d.F }} | {{ d.P }} | {{ d.C }} |
|---|---:|---:|---:|
| Accrued expenses, rebuilt | {{ sm(m2.comp[0].total) }} | {{ sm(m2.comp[1].total) }} | {{ sm(m2.comp[2].total) }} |
| Revenue cutoff | {{ sm(m2.cut[0]) }} | {{ sm(m2.cut[1]) }} | {{ sm(m2.cut[2]) }} |
| Payroll owed | {{ sm(m2.pay[0]) }} | {{ sm(m2.pay[1]) }} | {{ sm(m2.pay[2]) }} |
| Interest accrued | {{ sm(m2.intr[0]) }} | {{ sm(m2.intr[1]) }} | {{ sm(m2.intr[2]) }} |

**Quick check:** reconcile accrued expenses first: its parts must equal the ledger at every year-end before any decision about old items. The adjustments change income by {{ sg(m2.total.P) }} for {{ d.P }} and {{ sg(m2.total.C) }} for {{ d.C }}, and opening retained earnings by {{ sg(m2.total.re) }}; materiality is {{ sm(m2.mat_p) }} and {{ sm(m2.mat_c) }}. A student who holds the old accruals for evidence has income lower by {{ sm(m2.a3.P) }} and {{ sm(m2.a3.C) }}; that answer is acceptable.

### Milestone 3: The statements and notes

Students hold the adjusted statements, the notes with their reconciliations, and the Review file's tests.

| Quantity | {{ d.P }} | {{ d.C }} |
|---|---:|---:|
| Income before income taxes | {{ sm(m3.adj_ni[d.P]) }} | {{ sm(m3.adj_ni[d.C]) }} |
| Total assets | {{ sm(m3.s_p.ta) }} | {{ sm(m3.s_c.ta) }} |
| Current ratio | {{ m3.s_p.cr|num(2) }} | {{ m3.s_c.cr|num(2) }} |

**Quick check:** retained earnings at the start of {{ d.P }} are {{ sm(m3.reported) }} as reported and {{ sm(m3.restated) }} as restated. Cash flows for {{ d.C }}: operating {{ sm(m3.cf.operating) }}, investing {{ sm(m3.cf.investing) }}, financing {{ sm(m3.cf.financing) }}, a change in cash of {{ sm(m3.cf.cash) }} that no adjustment moves. Property and equipment cost is {{ sm(m3.cost) }}, accumulated depreciation {{ sm(m3.accumulated) }}, and notes payable {{ sm(m3.s_c.notes) }} with {{ sm(m3.s_c.cur) }} current.

### Milestone 4: What the data cannot settle

Students hold the review of later events, the going-concern conditions and the memo to the CFO.

**Quick check:** the records after the year-end hold {{ m4.payments }} supplier payments ({{ sm(m4.amount) }}) and no unrecorded liability. The memo must cover the tax status, the leases, the sales tax payable of {{ sm(m4.stax) }} with no remittance recorded, and the balances no document supports, which would raise equity by {{ sm(m4.equity) }} if none is real. Read the opening and the recommendation first.

## Difficult ideas and misconceptions

- **A balanced trial balance is not a right one.** A strict less-than, every close left out and every close left in all balance. Ask what Chapter 6's total says.
- **Age is not evidence.** An accrual older than the longest wait has gone unbilled, not unowed. Ask what the suppliers' statements would show.
- **Measure clearing from the ledger.** An invoice larger than its accrual clears only the accrual; the rest is expense. Ask what the ledger debited.
- **Errors reverse.** A cutoff item missed at one year-end enters that year's income and reverses in the next. Ask what the year before already took out.
- **Error or estimate.** The test is what the facts were at the year-end. Ask whether the facts existed and were missed.
- **Materiality is not only a number.** The effect on {{ d.C }} income is less than a third of materiality, yet the payroll liability alone exceeds it. Ask what it does to working capital.
- **Adjustments change lines, not totals.** None moves cash, so the change in cash stays {{ sm(m3.cf.cash) }}. Ask which entry would move it.
- **Describe, do not accuse.** The records show no remittance of the sales tax; they do not show anyone keeping it. Ask what evidence outside the database would settle it.

## Discussion prompts

1. The company earned {{ sm(m1.ni[2]) }} in {{ d.C }}, yet the bank asks whether it can carry its working capital. What does a lender read first in the statements? A good discussion reaches liquidity, inventories and cash flow from operations.
2. Which adjustments would you record, and which pass? A good discussion reaches materiality by size and by other grounds, and the recurring error.
3. Is a payroll accrual an error or an estimate? A good discussion separates the facts at the year-end from the amount measured later.
4. Would you reverse the old accruals without the suppliers' statements? A good discussion reaches the evidence, the assumption and the effect of the other choice.
5. What does restating {{ d.P }} cost the company with its shareholders and its bank? A good discussion reaches the disclosures and the weight a lender gives to a correction.
6. What can the ledger never tell you about tax status and leases? A good discussion reaches the agreements, the returns and the tax payments.
7. Should the package go to the bank as it stands? A good discussion reaches the matters the CFO must settle first.

## Using the requirements

| Requirement | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1. Build the trial balances and the recorded statements (Chapters 6, 10, and 11) | Financial | SQL and Excel | {{ c.plan[1] }} min | Intermediate | 1, 6 |
| 2. Review the recorded statements before adjusting them (Chapters 14 and 15) | Financial | Power BI | {{ c.plan[2] }} min | Intermediate | 5, 6 |
| 3. Rebuild Accrued Expenses at each year-end (Chapters 3, 10, and 12) | Auditing | SQL | {{ c.plan[3] }} min | Advanced | 2 |
| 4. Test cutoff at each year-end (Chapters 6 and 12) | Auditing | SQL and Excel | {{ c.plan[4] }} min | Advanced | 2 |
| 5. Classify, measure, and judge the adjustments (Chapters 4, 6, and 8) | Financial | Excel and SQL | {{ c.plan[5] }} min | Advanced | 3 |
| 6. Prepare the statements (Chapter 6) | Financial | Excel and Power BI | {{ c.plan[6] }} min | Advanced | 1 |
| 7. Build the note schedules from the records (Chapters 6, 10, 11, and 14) | Financial | SQL and Excel | {{ c.plan[7] }} min | Intermediate | 4 |
| 8. Look past the balance-sheet date and at the year ahead (Chapters 8 and 12) | Auditing | SQL and Excel | {{ c.plan[8] }} min | Intermediate | 5 |
| 9. Assemble the package and write the memo to the CFO (Chapter 8) | General | Excel and a written memo | {{ c.plan[9] }} min | Advanced | 5 |

Every requirement is part of the case, and each phase depends on the one before it. The figure shows how the files feed one another and the memo.

{{ figure('IF-17-0-A') }}

Four bundles:

- **The full case (the default).** All nine requirements, graded with the rubric below. About {{ c.student_hours }} hours.
- **A financial accounting version.** Requirements 1, 3, 4, 5, 6 and 7 with a one-page memo, in the workbook and the script only. It leaves out the Review file and the review of later events.
- **An auditing version.** Requirements 1 to 4, 8 and 9: the ledger, the rebuilt liability, the cutoff tests, what the data cannot settle, and the memo. It leaves out the statements.
- **Teams of three.** One file for each tool, with one student leading each (SQL, Excel, Power BI), a shared schedule of adjustments and an individual one-page reflection on the recommendation.

The check slides suit class discussion. Requirements 1, 3 and 4 suit grading from the files, because each ends in numbers that agree or do not; Requirements 2 and 6 suit grading from the Tests tab; Requirements 5, 7 and 9 from the schedule, the notes and the memo. A fast way to grade is to read the memo's opening and recommendation, then trace one number in each section back to the workbook.

## Assessment rubric

| Requirement | Weight | What carries the points |
|---|---:|---|
| 1. Trial balances and recorded statements | {{ c.weights[1] }} | One parameterized query, control totals, mapping, anti-join |
| 2. The review | {{ c.weights[2] }} | Ledger model, flags at materiality, drill-through, sources, Questions table |
| 3. Accrued expenses | {{ c.weights[3] }} | Clearing from postings, lag, parts equal the ledger, stated assumption |
| 4. Cutoff | {{ c.weights[4] }} | Both revenue tests, one payroll method at every year-end, interest convention |
| 5. The adjustments | {{ c.weights[5] }} | Numbered entries, classification, reversal, materiality and aggregate judgment |
| 6. The statements | {{ c.weights[6] }} | Four statements that agree, cash flows unchanged by adjustments, the Review file's tests |
| 7. The notes | {{ c.weights[7] }} | Schedules reconciled to the statements, the text of the required notes |
| 8. Later events | {{ c.weights[8] }} | Records after the year-end, unrecorded liabilities, going-concern conditions |
| 9. The package and the memo | {{ c.weights[9] }} | Order, accuracy, wording, a usable recommendation, length |
| Total | 100 | |

Four criteria run through every requirement.

| Criterion | Full credit looks like | Assessed mainly in |
|---|---|---|
| Accuracy | Totals tie to the ledger and to Chapter 6, entries balance, no adjustment touches cash | Requirements 1, 3, 4 and 6 |
| Evidence | Every number traces to a query, a formula or a document; assumptions stated | Requirements 3, 5 and 7 |
| Judgment | Error or estimate decided on the facts, materiality by size and other grounds, tools chosen and defended | Requirements 2, 5 and 8 |
| Communication | A memo in the order of the CFO's questions, careful with its words, ending in a recommendation | Requirement 9 |

Each requirement guide has its own grading table out of 100; scale it by the weight above to place it in the case grade.

## Connections

**Builds on.** Chapter 6 supplies the mapping from accounts to statement lines and the control totals; Chapter 4 the documentation habit; Chapter 8 the aging rates and the unsupported opening balances; Chapter 10 the joins and the anti-join; Chapter 11 the Params CTE and Exercise 11.1's statements; Chapter 12 the cutoff tests of Audit.sql; Chapters 14 and 15 the ledger model, the what-if parameter and the drill-through; Chapter 16 the Questions and dispositions pattern. The Part III and Part IV cases offer a head start on the payroll accrual and a ledger model, and the earlier cases supply the memo form.

**What builds on it.** Nothing in the book depends on this case. Its reconciliations and documentation are what an outside accountant would start from, which is the point of its last milestone.

**Appendix D** maps each requirement to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each requirement guide names the competencies it practices.
