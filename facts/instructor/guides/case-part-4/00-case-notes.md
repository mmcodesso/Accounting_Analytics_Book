---
uses: [case4.chapter, case4.r1, case4.r2, case4.r3, case4.r4, case4.r5]
title: 'Comprehensive Case, Part IV: Finding the Cash Behind the Profit'
kind: case-notes
unit: case4
minutes: 150
tool: powerbi
figures:
  - id: IF-C4-0-A
    kind: diagram
    purpose: How the six requirements build the memo and its appendix, and the chapters each one draws on.
    shows: "Six boxes in a row for the requirements, each tagged with its chapters (Chapters 13, 14 and 16; 14 and 15; 14 and 15; 13 to 15; 14 to 16; none). Arrows run from Requirement 1 into every other box. Requirements 2 to 5 feed the memo's three sections (Financial reporting, Managerial accounting, Auditing); all six feed the memo. Five exhibit boxes under the memo are tagged with the requirement and report page that produce each."
    data: none; the boxes and tags come from the case's requirements and deliverable.
  - id: IF-C4-0-B
    kind: diagram
    purpose: The three dates of the case, which students must not mix.
    shows: "One horizontal timeline from the last payroll posting through the last day of the current fiscal year to the ledger's last posting. Three marks are labeled: the last payroll posting, Data Through, and the last posting in the ledger. A bracket after the second mark reads supplier payments of the year's invoices, the only postings after the year. Under the first mark a note says the last two pay periods are open."
    data: The last payroll posting, Data Through and the ledger's last posting (Requirement 1, Step 8).
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set c = case4_chapter %}
{% set r1 = case4_r1 %}
{% set r2 = case4_r2 %}
{% set r3 = case4_r3 %}
{% set r4 = case4_r4 %}
{% set r5 = case4_r5 %}
{% set s = c.slide %}
{% set q0 = r3.qs[0] %}
{% set q1 = r3.qs[-1] %}
# Comprehensive Case, Part IV: Finding the Cash Behind the Profit

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part IV, Accounting Analytics with Power BI. The case closes the Part and integrates Chapters 13 to 16 |
| Analytics types | The case text does not label them. Read together: descriptive (Requirements 1 and 2), diagnostic (Requirements 3 to 5), prescriptive (Requirements 4 and 6) |
| Tools | Power BI Desktop only: Power Query (merges, Group By, custom columns), a star model with DAX (CALCULATE, KEEPFILTERS, trailing windows), report pages (waterfall, matrices, field parameter, what-if, drill-through, tooltip) and DAX query view for tests |
| Components | Six requirements, no tutorials, milestones or multiple-choice questions; the deck has {{ c.slides }} slides; the model answer has {{ c.n_pages }} pages ({{ c.n_hidden }} hidden), {{ c.n_measures }} measures and a Checks tab of {{ c.checks }} rows |
| Files students need | CharlesRiver.xlsx and the file they build, Charles River Cash Case.pbix. Charles River Reports.pbix and Audit Monitoring.pbix stay as they are. The solution is PartIV-case.zip |
| Deliverable | A memo of at most two pages to the controller, an appendix of up to three pages of five exhibits, and the .pbix with its About page, Validation page, Tests tab and Data Through card |
| Time | Class: about 150 minutes in Plan A. Students: about 15 hours, from 90 minutes for Requirement 6 to 180 for each of Requirements 2 and 3 |

The case depends on these conditions of the data, all visible in the file students build:

- Net income was {{ sm(r2.cur.net_income) }} in {{ d.C }} while cash fell {{ sm(-r2.cur.cash) }}, after rising {{ sm(r2.pri.cash) }} the year before. Inventories absorbed {{ sm(-r2.cur.inventories) }}.
- Three dates differ: the last payroll posting ({{ c.pay_end }}), Data Through ({{ c.thru }}) and the ledger's last posting ({{ c.last }}), which holds only supplier payments of the year's invoices. Data Through is a bound observed in the extract, not proof that the data are complete.
- The opening entry {{ r5.entry }} of the first fiscal year brings in receivables of ${{ r5.opening_ar|money }}, payables of ${{ r5.opening_ap|money }}, materials of ${{ r5.opening_materials|money }} and finished goods of ${{ r5.opening_fg|money }} that no document in the extract supports.
- Sales tax payable of ${{ r2.tax_c|money }}, the tax billed less credit memos, has no remittance recorded. The notes, ${{ r2.outstanding|money }}, all sit in a long-term account although ${{ r2.due_next|money }} falls due in the next year.
- One employee, the {{ r4.approver_title }}, approved every work-order shortfall requisition, and every inventory policy ends at the current year-end.

## What students should be able to do afterward

1. Build a model another person can refresh and check: queries that follow the Part IV conventions, profiles on the whole data set, links tested, a Validation page, a Tests tab and a Data Through date. Practiced in Requirement 1.
2. Bridge net income to the change in cash with measures that use KEEPFILTERS, find the entries that moved no cash and restate the sections as the indirect method requires. Practiced in Requirement 2.
3. Define balance-to-flow ratios on full twelve-month windows, with a flow for each balance, and say what an opening entry does to a first year. Practiced in Requirement 3.
4. Trace a build to the documents behind it, compare requisitions with what production used and size an excess with a what-if. Practiced in Requirement 4.
5. Reconcile accounts to their open items, explain each difference, and record findings in terms the report tests. Practiced in Requirement 5.
6. Write a short memo that answers the reader's questions in order, words findings as what the records show and ends with a recommendation. Practiced in Requirement 6.

## Preparing to teach

**Before the first class**

- Check the software. Students need Power BI Desktop at the release the Part IV chapters use (Windows only) and CharlesRiver.xlsx where the queries expect it. Charles River Cash Case.pbix is a new file, so the package and the monitoring file stay as they are.
- Open the model answer as Opening a Companion File on the Downloads page describes: copy the .pbip with its two folders, open it, use **Change Source** and refresh. GLEntry is large, so refresh once before class and note how long it takes.
- In **DAX query view**, run the Checks tab. All {{ c.checks }} rows should agree; the Tests tab holds the five tests students write.
- Open the deck. Slides {{ s.criteria }} set out the criteria, which are the six bullets of "What a Strong Submission Includes"; read them at kickoff.

**Pitfalls that cost class time**

- Three dates (slide {{ s.watch1 }}; figure below). A student who uses the last posting date gets cash of ${{ r1.cash_last|money }}, or include payroll and blank the last quarter.
- The closes and the opening entry. A flow that keeps the closes reads zero; a bridge for the first year starts from zero cash and shows ${{ r2.first.cash|money }}.
- KEEPFILTERS (slide {{ s.r2 }}). Without it every step of the waterfall reads {{ sm(r2.cur.cash) }}, and nothing looks wrong until a student reads two steps.
- Flows (slides {{ s.watch2 }} and {{ s.flow_check }} to {{ s.flow_answer }}). Billing, issues, shipments and supplier invoices are different flows, and each balance needs its own.
- The Date table ends before the debt schedule does, so a filter through it drops later payments silently.
- Word choice. Students may reach for unpaid, withheld or fraud. Slide {{ s.evidence }} sets the rule; repeat it at Requirement 5.

{{ figure('IF-C4-0-B') }}

## Teaching approaches

**Plan A: take-home work with four class touchpoints (150 minutes in class).** It fits a lecture course that wants the work done outside class and catches the errors that compound: the model, the bridge and the findings. The risk is a late start, so assign Requirements 1 and 2 at kickoff.

| Touchpoint | Minutes | Activity | Slides |
|---|---:|---|---|
| 1. Kickoff | 10 | The question, the deliverable and the criteria | {{ s.question }}, {{ s.handin }}, {{ s.criteria }} |
| 1. Kickoff | 10 | The situation and the wording rule | {{ s.situation }} |
| 1. Kickoff | 10 | The data, the Watch outs and the flow check | {{ s.data }} |
| 2. Checkpoint | 20 | Requirement 1: compare Validation pages and Data Through | {{ s.r1 }} |
| 2. Checkpoint | 25 | Requirement 2: the waterfall, the entries that moved no cash; assign Requirements 3 and 4 | {{ s.r2 }} to {{ s.cash_answer }} |
| 3. Checkpoint | 15 | Requirement 3: the measures and the cycle | {{ s.r3 }} |
| 3. Checkpoint | 15 | Requirement 4: the build and the target; assign Requirements 5 and 6 | {{ s.r4 }} |
| 4. Debrief | 20 | Requirement 5: the findings and their dispositions | {{ s.r5 }} to {{ s.disp_answer }} |
| 4. Debrief | 20 | Requirement 6: read two openings; state the recommendation | {{ s.r6 }}, {{ s.before }} |
| 4. Debrief | 5 | Looking ahead to Part V | {{ s.ahead }} |
| | 150 | Total | |

**Plan B: lab sessions (three sessions of 120 minutes, 360 minutes in all).** Students work in class and you circulate. It fits a computer lab. Requirements 4 to 6 go home, and the memo is collected the week after.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 15 | Kickoff: the question, criteria and wording rule | {{ s.question }} to {{ s.evidence }} |
| 1 | 105 | Requirement 1: queries, profiles, links, Validation, Data Through | {{ s.data }}, {{ s.r1 }} |
| 2 | 120 | Requirement 2: balance sheet, bridge, drill-through, restated sections | {{ s.r2 }} |
| 3 | 120 | Requirement 3: the measures, the field parameter and the tooltip | {{ s.r3 }} |
| | 360 | Total | |

These sessions start and check Requirements 1 to 3. Budget about 45 minutes after Session 1 and 60 minutes after each of Sessions 2 and 3 to finish them, in addition to the work on Requirements 4 to 6. Require a validated model before Session 2 and a tied cash bridge before Session 3. The estimates assume the prerequisite exercises are done.

**Plan C: memo workshop (90 minutes).** Students arrive with Requirements 1 to 5 done. It fits an upper-level or graduate class and moves the learning to the writing. Its risk is an early error found late, so collect the Tests tab and the findings the day before and mark them.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval: each pair states the bridge, the cycle, the build and the findings | {{ s.six }} |
| 10 | Each pair states its recommendation in one sentence; the room compares | {{ s.r6 }} |
| 30 | Draft the opening and the Financial reporting section from the Requirement 6 outline | {{ s.r6 }} |
| 30 | Swap drafts and review them against the Requirement 6 grading guide | {{ s.before }} |
| 10 | Looking ahead to Part V | {{ s.ahead }} |
| 90 | Total | |

## Difficult ideas and misconceptions

- **Profit is not cash.** Net income of {{ sm(r2.cur.net_income) }} and a fall of {{ sm(-r2.cur.cash) }} are both true. A student may call the year a loss. Ask where the profit went and which line of the bridge holds it.
- **A flow is not a difference of balances.** A bridge from differences of Balance gives a net income step of {{ sm(r2.cur.net_income - r2.pri.net_income) }}, because the prior close sits in retained earnings. Ask what a close does at two dates.
- **The first year starts at zero.** The opening entry makes the first year's bridge show ${{ r2.first.cash|money }} and its DSO and DPO rest on balances no document supports. Ask what the opening line stands for.
- **A ratio needs a definition.** DSO on revenue reads differently from DSO on billing, and a quarter's flow overstates every measure about fourfold. Ask what each balance is compared with.
- **Data Through is not the last posting.** The last posting is supplier payments. Nor does Data Through prove the data complete, because it is a bound observed in the extract. Ask what the report would claim if it ran to the last date, and what would show that no document is missing.
- **A difference is not an error.** Each difference equals recorded items to the cent: ${{ r5.ar_diff|money }} and ${{ r5.ap_diff|money }}. Ask which items and what disposition each earns.
- **Describe, do not accuse.** The records show no remittance of ${{ r2.tax_c|money }}, which is tax billed rather than tax collected, and they do not show anyone withholding it. Ask what evidence outside the database would settle it.
- **An estimate is not a forecast.** The excess at the year's rate of issue is ${{ r4.whatif[0].excess|money }} at {{ r4.whatif[0].days }} days. Ask what the estimate assumes and leaves out.

## Discussion prompts

1. The company earned a profit and ended the year with less cash. Which single line of the bridge would you show the committee first? A good discussion reaches inventories, the channel behind them and the size against the year's income.
2. The quick ratio fell while the current ratio did not. What does that say about which ratio a committee should watch? A good discussion reaches what each includes and the weight of inventories.
3. The cycle grew from {{ q0.ccc|num(1) }} to {{ q1.ccc|num(1) }} days. Is that a problem, a policy or a measurement issue? A good discussion reaches the targets, the opening entry and the standard cost.
4. One manager approves every shortfall requisition. What would a second approver cost and add? A good discussion reaches segregation of duties and the check against stock on hand.
5. No remittance of sales tax is recorded. What do you ask for, and from whom? A good discussion reaches the tax returns, the authority's account and the bank reconciliation.
6. Which tests of this report would you rerun on every refresh? A good discussion reaches Data Through, the control totals and Chapter 16's monitoring.
7. The excess is about {{ r4.multiple }} times the year's fall in cash even at the longest target. Can the company release it? A good discussion reaches use, valuation and the time the cash takes to return.

## Using the requirements

| Requirement | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1. Build and validate the case file (Chapters 13, 14 and 16) | General | Power BI | 150 min | Intermediate | 1 |
| 2. Explain where the cash went (Chapters 14 and 15) | Financial | Power BI | 180 min | Advanced | 2 |
| 3. Measure how fast working capital turns (Chapters 14 and 15) | Managerial | Power BI | 180 min | Advanced | 3 |
| 4. Trace the materials build and set a target for {{ d.N }} (Chapters 13 to 15) | Managerial | Power BI | 150 min | Advanced | 4 |
| 5. Test the balances behind the report (Chapters 14 to 16) | Auditing | Power BI | 150 min | Intermediate | 5 |
| 6. Write the decision memo | General | Written, with report exhibits | 90 min | Advanced | 6 |

Every requirement is part of the case, and each depends on the first. The figure shows how their results feed the memo and its appendix.

{{ figure('IF-C4-0-A') }}

Three bundles:

- **The full case (the default).** All six requirements, graded with the rubric below. About 15 hours.
- **A shorter version for an accounting course.** Requirements 1, 2 and 5 and a one-page memo on their sections. It skips the turnover and the build.
- **Teams of three.** One file and one memo for the team, with one student leading each perspective (Requirement 2 for financial reporting, Requirements 3 and 4 for managerial accounting, Requirement 5 for auditing) and an individual one-page reflection on the recommendation.

The check slides on flows, cash and dispositions suit class discussion. Requirements 1 and 5 suit grading from the file, because each ends in tests that pass or fail; Requirements 2 to 4 suit grading from the pages and the exhibits; Requirement 6 from the memo. A fast way to grade the file is to refresh it and read the Tests tab, then compare the Findings table with the Expected results of Requirement 5.

## Assessment rubric

| Requirement | Weight | What carries the points |
|---|---:|---|
| 1. File and validation | 15 | Closes flagged, channel through the line, profiles on the entire data set, links tested, Validation and Tests, Data Through explained |
| 2. Where the cash went | 20 | Balance sheets and ratios, bridge with KEEPFILTERS, waterfall, the entries that moved no cash, restated sections, cash net of tax and notes |
| 3. How fast it turns | 15 | Four days on full windows with their own flows, days of supply against targets, the page, the opening-entry and average comparison |
| 4. The materials build | 15 | Receipts by channel, requisition groups and the key, approvals, the what-if, limits of the estimate |
| 5. The balances | 15 | Roll-forward, both reconciliations, cutoff, aging, sales tax, Findings with dispositions and tests |
| 6. The memo | 20 | Order of the questions, accuracy, wording, a usable recommendation, five exhibits, length |
| Total | 100 | |

Four criteria run through every requirement.

| Criterion | Full credit looks like | Assessed mainly in |
|---|---|---|
| Accuracy | Totals tie to the ledger, flows leave the closes out, windows are full, tests pass | Requirements 1, 3 and 5 |
| Evidence | Every number in the memo traces to a measure and a page; findings are recorded with dispositions | Requirements 5 and 6 |
| Judgment | Entries that moved no cash found, versions of a ratio compared, an estimate's limits stated | Requirements 2 to 4 |
| Communication | A memo in the order of the questions, within two pages, careful with its words, ending in a recommendation | Requirement 6 |

Each requirement guide has its own grading table out of 100; scale it by the weight above to place it in the case grade.

## Connections

**Builds on.** Chapter 13 supplies the loading options, the profiles and the honest visuals. Chapter 14 supplies the Date table, the ledger star with its flagged closes, Exercise 14.1's Balance measure and the DAX of CALCULATE and KEEPFILTERS. Chapter 15 supplies the waterfall, the drill-through and tooltip pages, the trailing twelve-month measure with its guard, the field parameter and the what-if. Chapter 16 supplies the document key, the Tests tab, the dispositions table and Data Through. Chapter 8 supplies the dispositions and the unsupported opening balances, Chapter 6 and Chapter 12 the cutoff findings, and the Part III case the payroll accrual it proposed (${{ r5.accrual|money }}), carried into the findings as a proposal, not posted. The Part I to Part III cases supply the memo form. The finished guides for Chapters 13 to 16 hold the detail each requirement relies on.

**What builds on it.** Part V offers capstone cases that are independent final projects: each states the methods it needs and asks students to choose the tool for every step. This case is the last one that fixes the tool; those cases ask students to choose it.

**Appendix D** maps each requirement to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each requirement guide names the competencies it practices.
