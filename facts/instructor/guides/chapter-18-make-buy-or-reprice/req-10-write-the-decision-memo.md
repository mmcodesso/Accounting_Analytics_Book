---
note: ch18.r10
uses: [ch18.g10]
title: Write the decision memo
kind: requirement
number: '10'
unit: '18'
perspective: general
tool: excel
minutes: 90
solution: "Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Memo (the decision table, and the text of the model memo below it)"
figures:
  - id: IF-18-10-A
    kind: excel-mock
    purpose: The Memo sheet's decision table, the exhibit the memo's recommendation rests on.
    shows: "Nine family rows with the action, the annual effect, the one-time cost and what the decision depends on, and two totals rows below; the three families to buy are grouped first, the three to make next, and the other families below the floor last."
    data: The Memo sheet of the model workbook, the decision table and its totals.
  - id: IF-18-10-B
    kind: diagram
    purpose: The page plan of the memo and its appendix, for the kickoff and for grading.
    shows: "Two columns of boxes: a memo of two pages with seven short sections in order (the finding, the two views, the decisions, the whole paths, the prices, the standards and statements, the production manager's decision), and an appendix of three pages with three exhibits, each tagged with the sheet of the workbook it comes from."
    data: none; the sections and exhibits come from the requirement and from the sheets of the model workbook.
---
{% set g = ch18_g10 %}
{% macro sg(x) %}{{ "" if x == 0 else ("-" if x < 0 else "+") }}${{ (x|abs)|num(0) }}{% endmacro %}
# Requirement 10: Write the decision memo

{{ header() }}

## Purpose and learning outcomes

The memo is where the case's analysis becomes a decision two people who disagree can act on. It goes to the CFO and the production manager, so it gives each the evidence they need and leaves the crew decision with the production manager. Students pull the figures from their own workbook, compare whole paths and not single decisions, and keep to the page limits. The analytics type is prescriptive. This guide gives an outline and a rubric, not a memo to copy.

Students can:

- build a decision table from the workbook for each quoted family and each family below the floor, with the action, the annual effect, the one-time cost and what each depends on (Step 1);
- write a two-page memo that leads with the finding that changes the question, states each decision with its condition, and compares the whole paths (Steps 2 to 4);
- close with the standards, the statements and the one decision only the production manager can make, and choose exhibits that fit three pages (Steps 5 and 6).

**Competencies practiced.** CPA Evolution Core S1 M8 (visualization and communicating results); IMA Leadership (communication skills); IFAC IES 3 (b); AACSB A5 parts 5.2 and 5.3 (technology judgment, interpretation and communication).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with Requirements 4 to 9 finished; the memo is a separate document.
- **Data conditions.** None of its own: every figure comes from an earlier requirement, so a wrong figure there is wrong here.
- **Verify first.** Read the Memo sheet's decision table before class: it has {{ g.n_rows|count }} rows, {{ g.n_buy_rows|count }} to buy, {{ g.n_make_rows|count }} to make and {{ g.n_only|count }} others below the floor, and its totals are the path that buys and reprices the rest.

## How to run it

Individual work, about 90 minutes: 25 for the decision table, 45 for the memo, 10 for the appendix, 10 for a read-aloud check. Do not hand out the outline until students have a draft; then give it as a checklist. Peer review works well: each student reads a classmate's decision table first and says what to do with each family, before reading the memo. **Collect** the memo with its appendix.

{{ figure('IF-18-10-B') }}

## Step-by-step solution

Each step is a move in the memo, with the evidence to cite and the model conclusion.

**Step 1. Build the decision table.** One row for each quoted family and each other family below the floor. The Memo sheet fills the action, the annual effect and the one-time cost with formulas over Make or Buy and Prices.

```jinja
What to do    {{ g.f.what }}
Annual effect {{ g.f.effect }}
One-time cost {{ g.f.once }}
```

**Check:** {{ g.n_rows|count }} rows; the annual effects, the path that buys, add up to ${{ paths.buy|num(0) }} and the one-time costs to ${{ paths.once|num(0) }}. **Watch for:** the saving from buying added to the increases of the families bought as well: ${{ g.both|num(0) }}, more than either honest path. And one-time costs of tooling alone: ${{ g.once_tooling|num(0) }}.

{{ figure('IF-18-10-A') }}

**Step 2. Lead with the finding that changes the question.** Evidence: Requirements 3, 4 and 7. The plant already pays for about {{ unused_positions|num(1) }} positions of capacity it does not use (${{ unused_crew|num(0) }} of crew cost a year), which is more than buying would free ({{ positions|num(1) }} positions). Fitting the crew to the work is the larger question, and the two reductions add up only if both can be made.

**Step 3. State each decision with its condition.** Evidence: Requirements 6 and 8. Make {{ lose|map(attribute='short')|join(', ') }}: buying them loses money whatever happens to the crew. Buy {{ buy|map(attribute='short')|join(', ') }} only with a committed plan to reduce the crew in step, about {{ positions|num(1) }} positions; otherwise keep making them and raise their prices. Raise {{ need|join(', ') }} to the floor through new, approved price lists with end dates.

**Step 4. Compare the whole paths.** Evidence: the Memo sheet and Requirement 8. If volume holds, making all six and raising the {{ n_below }} families below the floor gains ${{ paths.make|num(0) }} a year with no one-time cost; buying {{ buy|map(attribute='short')|join(', ') }} and raising the rest gains ${{ paths.buy|num(0) }} with ${{ paths.once|num(0) }} once. Buying is a cost advantage at today's prices, not the better path under every assumption: which wins depends on how much volume the increases on those families would cost and on the crew plan.

**Step 5. Explain the disagreement, and close.** Both decision makers are right about part of the cost: the CFO that the products cost more than their standards say, the production manager that idle capacity is not the products' fault and belongs to the plant. Then the standards (a rate on normal capacity for inventory, time-driven costs for decisions), what the base year's statements need (the evidence that would show whether the old standards misstated them, before anything is restated), and the one decision only the production manager can make: whether, and how fast, to reduce the crew to the work the plant has.

**Step 6. Choose the exhibits.** Three pages hold three exhibits: the family costs under the three views (Costs), the make-or-buy table with the break-even quotes and the two-way table (Make or Buy), and the capacity, price and standards results (Capacity, Prices, Standards). Each exhibit is cited in the memo by name and supports a number the memo states.

**Check:** read the decision table first, then trace one number in each row back to its sheet.

## Expected results

| Family | What to do | Annual effect | One-time cost |
|---|---|---:|---:|
{% for r in g.rows %}
| {{ r.short }} | {{ r.action }} | {{ sg(r.effect) }} | ${{ r.once|num(0) }} |
{% endfor %}

{{ expected() }}

## What a strong answer says

- **A finding before the decisions,** worded for both readers: the unused capacity, then the two views of the cost.
- **A condition on every decision.** What happens to the crew, what the quote's terms require, what volume loss an increase can absorb.
- **Whole paths,** with the one-time costs shown, and an honest statement that buying is not the better path under every assumption.
- **The standards and the statements,** kept apart from the make-or-buy decision, with the evidence named and no restatement claimed.
- **The production manager's decision left open,** with what it would save and cost.

A strong memo reads in two pages; a weak one lists results in the order the work was done, buries the crew decision, or tells the CFO that the statements are wrong.

## Common mistakes and how to respond

- **Double counting.** *Symptom:* a total of ${{ g.both|num(0) }}. *Response:* ask which path each row belongs to.
- **Missing one-time costs.** *Symptom:* ${{ g.once_tooling|num(0) }} of one-time cost. *Response:* ask who is paid severance.
- **Buying without a crew plan.** *Symptom:* "buy" in every decision row. *Response:* ask what the same purchase costs with the crew kept, ${{ g.kept_cost|num(0) }} a year.
- **The crew decision taken.** *Symptom:* "reduce the crew by {{ positions|num(0) }} positions". *Response:* ask who owns that decision.
- **Over the page limit.** *Symptom:* a third page of text. *Response:* ask which sentence a reader would miss.
- **A sensitivity reported as an error.** *Symptom:* "the statements were misstated". *Response:* ask what evidence at the time would show it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Decision table | 25 | Every quoted family and every family below the floor, with action, annual effect, one-time cost and dependence | Missing rows or conditions |
| Recommendation and paths | 25 | A condition on each decision, whole paths compared | Single decisions only |
| Standards and statements | 15 | Rate on normal capacity, evidence named, no restatement claimed | An error claimed without evidence |
| The crew decision | 15 | Left to the production manager, with what it would cost and save | Taken, or missing |
| Writing and limits | 15 | Two pages, appendix of three, finding first, both readers addressed | Over the limit, or results in the order of the work |
| Traceability | 5 | Every number matches the workbook | Figures that disagree with it |

## Extensions and discussion questions

- Rewrite the first section for the audit committee, which has not read the case.
- Reduce the memo to one slide and say what the slide cannot carry.
- Discuss: what would make you change a recommendation after the quote expires?
- Discuss: how should the memo say what the data cannot show?
