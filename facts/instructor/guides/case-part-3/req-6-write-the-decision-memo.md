---
note: case3.r6
uses: [case3.g6, case3.r2, case3.r3, case3.r4, case3.r5]
title: Write the decision memo
kind: requirement
number: '6'
unit: case3
perspective: general
tool: mixed
minutes: 90
solution: "PartIII-case-sql.zip: Case.sql, the Requirement 6 model answer in its closing comments (the memo's content, in the order of the controller's questions, with its recommendation)"
figures:
  - id: IF-C3-6-A
    kind: diagram
    purpose: How the memo and its one-page appendix are laid out, and which requirement supplies each part.
    shows: "Two page outlines side by side and a smaller third page for the appendix. The memo pages show the header lines, an opening paragraph, three headed sections (Auditing, Managerial accounting, Financial reporting) and a recommendation. The appendix shows five numbered exhibit boxes. Arrows tag each section and exhibit with its source: Requirement 2 for Auditing and the matrix, 3 and 4 for Managerial accounting and exhibits 2 to 4, 5 for Financial reporting and exhibit 5."
    data: none; the layout and tags come from the case's Requirement 6 and Deliverable.
---
{% set r2 = case3_r2 %}
{% set r3 = case3_r3 %}
{% set r4 = case3_r4 %}
{% set r5 = case3_r5 %}
{% set x = case3_g6 %}
# Requirement 6: Write the decision memo

{{ header() }}

## Purpose and learning outcomes

The memo is where five requirements become a decision. The controller will take it into a review by the chief audit executive, so students must choose the few numbers that carry the argument, state what they do not show, keep the word unsupported where the evidence stops, and end with a recommendation someone can act on. It follows the Part I and Part II cases' memos, with three sections in the order of the controller's questions. The analytics type is prescriptive.

Students can:

- organize a two-page memo by the reader's questions, not by the order of the work (Steps 1 and 2);
- select the evidence of each section and state its limits (Steps 3 to 5);
- recommend actions with owners and a way to learn more (Step 6);
- support the memo with exhibits a reviewer can trace to Case.sql (Step 7).

**Competencies practiced.** CPA Evolution Core S1 M8 T5 to T6 (visualization and communication of results); IMA Leadership (communication skills); IFAC IES 3 (b), interpersonal and communication skills; AACSB A5 part 5.2 (technology judgment, interpretation and communication).

## Before you assign

- **From earlier work.** Requirements 1 to 5 complete, with their tables and Case.sql, and the memos of the Part I and Part II cases as models. No new SQL: students write the memo and appendix in a word processor.
- **Length.** At most two pages, with a one-page appendix of {{ x.n_exhibits }} exhibits. The model answer in Case.sql is an outline of about {{ x.model_words }} words, not a finished memo. Students choose the decision-critical results for each exhibit and keep full reconciliations and entries in the labeled output of Case.sql. A landscape exhibit page is fine, and you may allow a second exhibit page when a readable layout needs it, rather than shrinking the type.
- **The model's view.** The hours are unsupported, not fictitious; the plan allows no routine overtime; the {{ d.C }} statements get the payroll accrual and the cutoff; identified abnormal costs are expensed and normal conversion cost needs a separate allocation analysis. Students may reach another recommendation from the same evidence. Grade the reasoning and the wording, not the verdict, if it follows from the exhibits and states its limits.

## How to run it

Individual, about 90 minutes in class or as a take-home: 15 to plan the evidence, 50 to draft, 25 to check every number against its query and the length. In a workshop (the memo workshop of the case note), students swap drafts and review them against the grading guide below. **Collect** the memo, the appendix and Case.sql.

{{ figure('IF-C3-6-A') }}

## Step-by-step solution

### Part 1: Plan the memo

**Step 1. Fix the reader and the recommendation.** The reader is the controller, who needs a position for the audit committee's response. Write the recommendation first, in one sentence, then keep only evidence that supports it or limits it.

**Step 2. Choose the evidence from each requirement.** Three to five numbers for each section, each traceable to a query:

| Section | What it must say | Source | Exhibit |
|---|---|---|---|
| Auditing | What the records outside the time clock show, how independent they are, the open explanations and the evidence that would settle them, what the control needs | Requirement 2 | 1 |
| Managerial accounting | What the hours produced and cost, the bridge, the plan with its assumptions and the overtime it allows | Requirements 3 and 4 | 2, 3, 4 |
| Financial reporting | The adjustments and their effect, why identified abnormal costs are expensed, and why normal conversion cost needs its own allocation analysis | Requirement 5 | 5 |

### Part 2: The sections and the close

**Step 3. Auditing.** Say that the records outside the time clock do not support the surge-day hours as recorded: on {{ r2.s.days }} surge days the plant used {{ r2.s.clock_ins|num(1) }} different clock-in times a day against {{ r2.o.clock_ins|num(1) }} on ordinary days, rostered {{ r2.rostered }} hours and clocked {{ r2.clocked }}, and {{ r2.cite.Surge.ended|count }} approvals cite an operation that had ended. Say that the records that agree (attendance, punches) come from the time clock, the rosters and approvals from one manager, and that the calendar, the plan and the output are not shown to be independent of that manager. Name two explanations, the hours worked and entered as a block, or not worked as recorded, and the evidence outside the database that would separate them. Say what the control needs: its configuration, since the stored exceptions only point to a rule, a rule that compares overtime with a roster or plan, and a review of the {{ r2.exceptions }} open exceptions.

**Step 4. Managerial accounting.** Output was flat ({{ r3.ys[0].std|num }}, {{ r3.ys[1].std|num }} and {{ r3.ys[2].std|num }} standard hours) while surge overtime rose from {{ r3.ys[0].surge.overtime|num }} to {{ r3.ys[2].surge.overtime|num }} hours; the last year's cost was {{ (r3.ys[2].surge_premium * (1 + r3.burden))|money }} as a premium or {{ (r3.ys[2].surge_full * (1 + r3.burden))|money }} in full, each with the employer's taxes and benefits as Requirement 3 asks, two alternatives and not a sum. Account {{ x.variance_account }} grew {{ r3.bridge.delta|money }}, nearly all payroll charged to {{ x.clearing_account }} ({{ r3.bridge.payroll|money }}). The plan at {{ r4.levels[1]|num(2) }} hours per standard hour needs {{ r4.need[1]|num }} hours against {{ r4.capacity|count }} of regular capacity and expects a variance of {{ r4.variance[1]|num }}; it allows no routine overtime, and exceptions are approved against a dated plan, because the year's total does not show that every week fits. State the assumptions, and that the budget's volume was not used.

**Step 5. Financial reporting.** Record the payroll accrual of {{ r5.p.accrual|money }}; with the {{ d.P }} work paid in {{ d.C }} ({{ r5.prior.total|money }}), income falls only {{ r5.change|money }}, while the liability rises by the full accrual. With the cutoff (+{{ r5.net_rev|money }}), adjusted net income is {{ r5.adj_ni|money }}, on the stated assumption that the manufacturing parts are period costs. The net change is small, but the liability left out is {{ r5.liab_ni|pct(1) }} of net income, so judge it and each error on their own, and call the missing accrual a recurring deficiency. Do not raise the standards to absorb the cost: actual conversion cost was {{ r5.actual_rate|num(2) }} per standard hour against the standard {{ r5.std_rate|num(2) }}. Identified abnormal costs, such as idle capacity, are expensed, and normal conversion cost needs a separate allocation analysis. Unsupported hours are not automatically an abnormal cost of the same amount.

**Step 6. Recommend.** Stop routine surge days and require overtime to be approved in advance against a plan, by someone outside production; review the open attendance exceptions and add a rule that compares overtime with the roster; have internal audit corroborate a sample of surge days with access logs and interviews; adopt a {{ d.N }} plan at about the first year's hours per standard hour as a target to test, with no routine overtime and exceptions against a dated plan; keep the direct-hour standards provisionally, since the records give no reason to revise them and the comparison does not show they are right, and review the overhead rates on normal capacity; record the year-end payroll accrual now and at every year-end.

**Step 7. Build the appendix.** One page, {{ x.n_exhibits }} numbered exhibits, each cited in the memo: {{ x.exhibits|join(', ') }}. Each panel carries only the decisive results.

- Corroboration: three or four decisive tests, the independence of the time clock and of the manager judged apart, and what remains unknown.
- Output: the three annual comparisons, one qualified weekly result, and the cutoff note.
- Bridge: all six ledger lines and the total, with the payroll measures marked as non-additive diagnostics.
- Plan: the three scenarios, the baseline assumptions and a work-center scheduling caveat.
- Adjustments: the payroll, cutoff, opening-equity and liability effects with the manufacturing assumption beside them, referring to the full entries.

**Check:** the memo answers the controller's questions in the order they were asked, every number appears in an exhibit or a query, no hours are called fictitious and no person blamed without evidence ("these records do not prove the hours were fictitious" is acceptable), and the length holds.

## Expected results

| Memo section | Numbers a correct memo carries | Source |
|---|---|---|
| Auditing | {{ r2.s.days }} surge days; {{ r2.s.clock_ins|num(1) }} against {{ r2.o.clock_ins|num(1) }} clock-in times; {{ r2.rostered }} hours rostered, {{ r2.clocked }} clocked | R2 |
| Managerial accounting | Premium {{ (r3.ys[2].surge_premium * (1 + r3.burden))|money }}, full {{ (r3.ys[2].surge_full * (1 + r3.burden))|money }}, with burden; {{ x.variance_account }} up {{ r3.bridge.delta|money }}; variance {{ r4.variance[1]|num }} | R3, R4 |
| Financial reporting | Accrual {{ r5.p.accrual|money }}; adjusted net income {{ r5.adj_ni|money }}, on the manufacturing assumption | R5 |
| Recommendation | No routine overtime; approval in advance; corroborate; accrue every year-end | R2 to R5 |

{{ expected() }}

## What a strong answer says

- **Opening.** The question and the answer in two sentences, before any detail.
- **Auditing.** The records contradict or fail to support the hours; the agreeing records are not independent; two explanations remain, and the evidence that separates them lies outside the database.
- **Managerial accounting.** Output flat, overtime up, the cost two ways, the bridge, and a plan with stated assumptions that needs no routine overtime.
- **Financial reporting.** The accruals, the effect on income against the balance sheet, materiality, and why identified abnormal costs are expensed while normal conversion cost needs its own allocation analysis.
- **Recommendation.** Specific actions, owners, and a way to learn more.

A strong memo makes choices: it leaves out findings that do not bear on the decision and states what the data cannot show. A weak memo reports every result in the order found, hedges the recommendation, or asserts fictitious hours without evidence.

## Common mistakes and how to respond

- **Too long.** *Symptom:* three pages or a squeezed font. *Response:* ask which finding the controller would miss least, and move detail to the appendix.
- **Organized by requirement.** *Symptom:* headings that read Requirement 1 to 5. *Response:* ask what the controller's questions were.
- **Fictitious hours.** *Symptom:* the memo says the hours were faked. *Response:* ask which record shows that nobody worked, and what each explanation predicts.
- **Blame.** *Symptom:* a named person at fault. *Response:* use the role, and ask what design would have prevented it.
- **No recommendation, or a hedged one.** *Symptom:* "it depends". *Response:* ask what the student would do tomorrow.
- **Numbers that disagree.** *Symptom:* memo and exhibit differ. *Response:* trace each to its query and fix one source.
- **Immaterial because the net is small.** *Symptom:* "the adjustments are immaterial". *Response:* ask how large the liability left out is, and what the balance sheet would show without it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Auditing | 25 | Evidence, independence, open explanations, outside evidence, control needs | Results without independence |
| Managerial accounting | 25 | Output, cost, bridge, plan and assumptions, overtime allowed | Results listed without a conclusion |
| Financial reporting | 20 | Accruals, effect on income and balance sheet, materiality, inventory | One accrual, or no reason for inventory |
| Recommendation | 15 | Specific actions, owners, a way to learn more; another recommendation that follows from the exhibits and states its limits | A decision without actions |
| Exhibits and traceability | 10 | {{ x.n_exhibits }} exhibits, cited, agreeing with the text | Missing or inconsistent |
| Form and audience | 5 | Two pages, three sections, plain for the controller | Over length or unorganized |

## Extensions and discussion questions

- Write a five-sentence note to the Production Manager explaining the recommendation without assigning blame.
- Present the Auditing section to the audit committee in three minutes, and name the one exhibit you would show.
- Discuss: if gate logs showed the hours were worked, what would change in the memo and what would stay?
- Discuss: the memo calls the hours unsupported. What is the cost of saying more, and of saying less?
