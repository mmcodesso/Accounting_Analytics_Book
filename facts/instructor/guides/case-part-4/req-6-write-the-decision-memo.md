---
note: case4.r6
uses: [case4.g6, case4.r1, case4.r2, case4.r3, case4.r4, case4.r5]
title: Write the decision memo
kind: requirement
number: '6'
unit: case4
perspective: general
tool: powerbi
minutes: 90
solution: "PartIV-case.zip: Charles River Cash Case.pbip, page Memo (the model memo in two text boxes, in the order of the controller's questions, ending with the recommendation) and the Requirement 6 rows of the Checks tab"
figures:
  - id: IF-C4-6-A
    kind: diagram
    purpose: How the memo and its one-page appendix are laid out, and which requirement and report page supplies each part.
    shows: "Two page outlines side by side and a smaller third page for the appendix. The memo pages show the header lines, three headed sections in the order Financial reporting, Managerial accounting, Auditing, and a closing Recommendation. The appendix shows five numbered exhibit boxes. Tags name the source of each section and exhibit: Requirement 2 and the Cash Bridge page, Requirement 3 and the Working Capital page, Requirement 4 and the Materials pages, Requirement 5 and the Reconciliations page. The Auditing section also names Requirement 1 and its Validation and About pages."
    data: none; the layout and tags come from the case's Requirement 6 and Deliverable.
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set x = case4_g6 %}
{% set a = case4_r2 %}
{% set b = case4_r3 %}
{% set c = case4_r4 %}
{% set e = case4_r5 %}
{% set q0 = b.qs[0] %}
{% set q1 = b.qs[-1] %}
# Requirement 6: Write the decision memo

{{ header() }}

## Purpose and learning outcomes

The memo is where five requirements become a decision. The controller takes it into the audit committee's meeting, so students must choose the few numbers that carry the argument, word each finding as what the records show, say what the evidence cannot settle and end with a recommendation someone can act on. It follows the memos of the Part I to Part III cases. The analytics type is prescriptive.

Students can:

- organize two pages by the controller's questions, not by the order of the work (Steps 1 and 2);
- choose and state the evidence of each section with its limits (Steps 3 to 5);
- recommend actions with a way to learn more (Step 6);
- support the memo with exhibits a reviewer can trace to the file (Step 7).

**Competencies practiced.** CPA Evolution Core S1 M8 T5 to T6 (visualization and communicating results); IMA Leadership (communication skills); IFAC IES 3 (b), interpersonal and communication skills; AACSB A5 part 5.2 (technology judgment, interpretation and communication).

## Before you assign

- **From earlier work.** Requirements 1 to 5 with their pages, and the memos of the earlier cases as models. No new modeling: students write in a word processor.
- **Length.** At most two pages with a one-page appendix of {{ x.n_exhibits }} exhibits. The model memo on the Memo page is about {{ x.model_words|count }} words, an outline and not a finished memo.
- **The model's view.** The recorded profit went into inventories, the growth of the recorded tax payable and of payables held cash up, the cash on the balance sheet may overstate what the company can use until the tax position is settled, and settling it comes first. Another recommendation from the same evidence earns full credit if it follows from the exhibits and states its limits.

## How to run it

Individual, about 90 minutes in class or as a take-home: 15 to plan the evidence, 50 to draft, 25 to check every number against its page and the length. In a workshop, students swap drafts and review them against the grading guide. **Collect** the memo, the appendix and the .pbix.

{{ figure('IF-C4-6-A') }}

## Step-by-step solution

### Part 1: Plan the memo

**Step 1. Fix the reader and the recommendation.** The reader is the controller. Write the recommendation first, in one sentence, then keep only evidence that supports it or limits it.

**Step 2. Choose the evidence.** Three to five numbers for each section, each traceable to a page of the report:

| Section | What it must say | Source | Exhibit |
|---|---|---|---|
| Financial reporting | Where the cash went, the restated sections with the noncash disclosure, what the balance sheet needs | Requirement 2 | 1, 2 |
| Managerial accounting | Which balances absorbed the cash and how fast each turns, what drove the build, a target with its cash effect and assumptions | Requirements 3 and 4 | 3, 4 |
| Auditing | Reconciliations and findings with dispositions, outside evidence, requisition controls, the report's own controls | Requirements 1 and 5 | 5 |

### Part 2: The sections and the close

**Step 3. Financial reporting.** Net income was {{ sm(a.cur.net_income) }} but cash fell {{ sm(-a.cur.cash) }}, from ${{ a.cash_from|money }} to ${{ a.cash_to|money }}, after rising {{ sm(a.pri.cash) }} the year before. Inventories absorbed {{ sm(-a.cur.inventories) }}, {{ sm(x.inv_over) }} more than the year earned, while the growth of the recorded sales tax payable ({{ sm(a.cur.sales_tax) }}) and of payables ({{ sm(a.cur.payables) }}) held cash up. Restated, operating activities used {{ sm(-a.rc.operating) }}, investing {{ sm(a.rc.investing) }} and financing {{ sm(-a.rc.financing) }} in principal, with ${{ a.rc.notes_financed|money }} of equipment acquired by a note disclosed apart. The balance sheet needs the tax position settled (${{ a.tax_c|money }} with no remittance recorded, so cash net of it is ${{ a.net[-1]|money }}), ${{ a.due_next|money }} of notes reclassified to current, and support requested for the opening receivables (${{ e.opening_ar|money }}), payables (${{ e.opening_ap|money }}), materials (${{ e.opening_materials|money }}) and finished goods (${{ e.opening_fg|money }}), adjusted only if the evidence shows them wrong.

**Step 4. Managerial accounting.** Receivables and payables barely moved (DSO {{ q0.dso|num(1) }} to {{ q1.dso|num(1) }} days, DPO without the opening line {{ q0.dpo_x|num(1) }} to {{ q1.dpo_x|num(1) }}); the cycle grew from {{ q0.ccc|num(1) }} to {{ q1.ccc|num(1) }} days, mainly through inventory, materials at {{ q1.mat|num(1) }} days against the largest materials target of {{ b.raw }}. The shortfall channel carried the build (${{ c.by_year[-1].short[1]|money }} of receipts in {{ d.C }} against issues near ${{ c.ttm|money }}), with {{ c.repeated|count }} of {{ c.pairs|count }} work order and item pairs requisitioned more than once. A target of {{ c.whatif[0].days }} days leaves an excess of ${{ c.whatif[0].excess|money }}, about {{ c.multiple }} times the fall in cash even at {{ c.whatif[2].days }} days; the estimate assumes issues continue and the stock is usable, and leaves out finished goods, {{ c.n_never }} unordered requisitions and the open orders.

**Step 5. Auditing.** Receivables reconcile to the open invoices except ${{ e.ar_diff|money }}, and payables except ${{ e.ap_diff|money }}. Dispositions: the opening balances and the sales tax, follow up, with the schedules, the returns filed, the tax authority's account and the bank reconciliation as outside evidence; the note invoices, expected; the current portion and the unrecorded payroll accrual (${{ e.accrual|money }}, the Part III case's proposed estimate), misstatements. One manager, the {{ c.approver_title }}, approved every shortfall requisition, and the records do not show whether stock on hand or open orders were checked. The report needs its Tests tab rerun and its Data Through card checked on every refresh.

**Step 6. Recommend.** Settle the sales tax position first. Check every shortfall requisition against stock on hand and open orders before conversion, route it through the supply plan with an approver outside production, and review the {{ n_never }} open requisitions. Approve {{ d.N }} inventory targets and a purchase budget that draws the stock toward them. Present the restated cash flow with its disclosure, reclassify the notes' current portion and follow up the opening balances.

**Step 7. Build the appendix.** One page, {{ ['zero', 'one', 'two', 'three', 'four', 'five', 'six'][x.n_exhibits] }} numbered exhibits, each cited in the memo: {{ x.exhibits|join('; ') }}. They come from the visuals titled "{{ x.titles.bridge }}", "{{ x.titles.restated }}", "{{ x.titles.wc }}", "{{ x.titles.channels }}" with "{{ x.titles.tested }}", and "{{ x.titles.findings }}".

**Check:** the memo answers the controller's questions in the order asked, every number appears in an exhibit or a page, wording describes the records and not a person, and the length holds.

## Expected results

| Memo section | Numbers a correct memo carries | Source |
|---|---|---|
| Financial reporting | {{ sm(a.cur.net_income) }}; cash {{ sm(a.cur.cash) }}; inventories {{ sm(a.cur.inventories) }}; restated financing {{ sm(a.rc.financing) }} | R2 |
| Managerial accounting | Cycle {{ q1.ccc|num(1) }} days; materials {{ q1.mat|num(1) }}; excess at {{ c.whatif[0].days }} days ${{ c.whatif[0].excess|money }} | R3, R4 |
| Auditing | Differences ${{ e.ar_diff|money }} and ${{ e.ap_diff|money }}; tax ${{ a.tax_c|money }} | R5 |
| Recommendation | Settle the tax; control requisitions; approve targets; keep the tests | R1 to R5 |

{{ expected() }}

## What a strong answer says

- **Opening.** The question and the answer in two sentences: the recorded profit went into inventories, and cash fell.
- **Financial reporting.** The bridge, the restated sections with the noncash disclosure, and three balance sheet items.
- **Managerial accounting.** Which balances moved, the channel behind the build, and a target with its cash effect and its assumptions.
- **Auditing.** Differences equal to recorded items, dispositions, outside evidence, controls over requisitions and over the report.
- **Recommendation.** Specific actions in an order the controller can follow.

A strong memo makes choices and says what the data cannot show; a weak one reports every result in the order found.

## Common mistakes and how to respond

- **Too long.** *Symptom:* three pages or a squeezed font. *Response:* ask which finding the controller would miss least.
- **Organized by requirement.** *Symptom:* headings that read Requirement 1 to 5. *Response:* ask what the controller's questions were.
- **Accusing or overstated wording.** *Symptom:* "unpaid" or "withheld" for the sales tax, or "collected" for tax that was billed. *Response:* ask what the ledger shows and what it cannot.
- **Cash and profit confused.** *Symptom:* "the company lost money". *Response:* ask where the profit went.
- **No recommendation, or a hedged one.** *Symptom:* "it depends". *Response:* ask what the student would do tomorrow.
- **Numbers that disagree.** *Symptom:* memo and exhibit differ. *Response:* trace each to its page and fix one source.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Financial reporting | 25 | Bridge, restated sections, noncash disclosure, three balance sheet items | Bridge without the restatement |
| Managerial accounting | 20 | Turnover, build, target with cash effect and assumptions | Results without assumptions |
| Auditing | 25 | Reconciliations, dispositions, outside evidence, both sets of controls | Differences without dispositions |
| Recommendation | 15 | Specific, ordered actions | A decision without actions |
| Exhibits and traceability | 10 | {{ x.n_exhibits }} exhibits, cited, agreeing with the text | Missing or inconsistent |
| Form and audience | 5 | Two pages, three sections, plain for the controller | Over length |

## Extensions and discussion questions

- Write a five-sentence note to the Production Manager that explains the requisition control without assigning blame.
- Present the first section to the committee in three minutes and name the exhibit you would show.
- Discuss: if the tax authority's account showed the tax remitted, what would change in the memo and what would stay?
- Discuss: the report will be refreshed every quarter. Which of its tests should the committee see?
