# Requirement 10: Write the decision memo

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 10 |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Memo (the decision table, and the text of the model memo below it) |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The memo is where the case's analysis becomes a decision two people who disagree can act on. It goes to the CFO and the production manager, so it gives each the evidence they need and leaves the crew decision with the production manager. Students pull the figures from their own workbook, compare whole paths and not single decisions, and keep within the page maximums. The analytics type is prescriptive. This guide gives an outline and a rubric, not a memo to copy.

Students can:

- build a decision table from the workbook for each quoted family and each family below the floor, with the action, the annual effect, the one-time cost and what each depends on (Step 1);
- write a memo of at most two pages, including the decision table, that leads with the finding that changes the question, states each decision with its condition, and compares the whole paths (Steps 2 to 4);
- close with the standards, the statements and the one decision only the production manager can make, and choose exhibits that fit at most three pages (Steps 5 and 6).

**Competencies practiced.** CPA Evolution Core S1 M8 (visualization and communicating results); IMA Leadership (communication skills); IFAC IES 3 (b); AACSB A5 part 5.2 (technology judgment, interpretation and communication).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with Requirements 4 to 9 finished; the memo is a separate document.
- **Data conditions.** None of its own: every figure comes from an earlier requirement, so a wrong figure there is wrong here.
- **Verify first.** Read the Memo sheet's decision table before class: it has 9 rows, 3 to buy, 3 to make and 3 others below the floor, and its totals are the path that buys and reprices the rest.

## How to run it

Individual work, about 90 minutes: 25 for the decision table, 45 for the memo, 10 for the appendix, 10 for a read-aloud check. Do not hand out the outline until students have a draft; then give it as a checklist. Peer review works well: each student reads a classmate's decision table first and says what to do with each family, before reading the memo. **Collect** the memo with its appendix.

![The page plan of the memo and its appendix, for the kickoff and for grading.](../figures/chapter-18-make-buy-or-reprice/IF-18-10-B.pdf)

## Step-by-step solution

Each step is a move in the memo, with the evidence to cite and the model conclusion.

**Step 1. Build the decision table.** One row for each quoted family and each other family below the floor. The Memo sheet fills the action, the annual effect and the one-time cost with formulas over Make or Buy and Prices.

```
What to do    ="Buy, only with the crew reduced in step (about "&TEXT(XLOOKUP($A5,'Make or Buy'!$A$10:$A$15,'Make or Buy'!$U$10:$U$15),"0.0")&" positions); otherwise keep making it and raise its price "&TEXT(XLOOKUP($A5,Prices!$A$5:$A$40,Prices!$J$5:$J$40),"0.0%")
Annual effect =XLOOKUP($A5,'Make or Buy'!$A$10:$A$15,'Make or Buy'!$N$10:$N$15)
One-time cost =XLOOKUP($A5,'Make or Buy'!$A$10:$A$15,'Make or Buy'!$W$10:$W$15)+XLOOKUP($A5,'Make or Buy'!$A$10:$A$15,'Make or Buy'!$U$10:$U$15)*SeverancePerPosition
```

**Check:** 9 rows; the annual effects, the path that buys, add up to $501,792 and the one-time costs to $172,660. **Watch for:** the saving from buying added to the increases of the families bought as well: $812,016, more than either honest path. And one-time costs of tooling alone: $70,000.

![A mock of the Memo sheet's decision table, the exhibit the memo's recommendation rests on.](../figures/chapter-18-make-buy-or-reprice/IF-18-10-A.pdf)

**Step 2. Lead with the finding that changes the question.** Evidence: Requirements 3, 4 and 7. On the routings, the plant supplies about 17.8 position-equivalents of practical hours more than its completions need ($997,574 of crew cost a year), more than buying would free on the same base (10.9). Fitting the crew to the work is the larger question, and the two reductions add up only if both can be made. The memo says that these are annual hours from standard times, not a staffing plan, since 6 of the 49 weekly buckets of the rough-cut plan through 2026-12-07 were planned above the plant's available hours.

**Step 3. State each decision with its condition.** Evidence: Requirements 6 and 8. Make SDB, SCN, PIL: buying them loses money whatever happens to the crew. Buy BNH, NGT, TBL only with a committed plan to reduce the crew in step, about 10.6 positions; otherwise keep making them and raise their prices. Raise BKC, CTB, SDB, CHD to the floor through new, approved price lists with end dates.

**Step 4. Compare the whole paths.** Evidence: the Memo sheet and Requirement 8. If volume holds, making all six and raising the seven families below the floor gains $556,535 a year with no one-time cost; buying BNH, NGT, TBL and raising the rest gains $501,792 with $172,660 once. Buying is a cost advantage at today's prices, not the better path under every assumption: which wins depends on how much volume the increases on those families would cost and on the crew plan.

**Step 5. Explain the disagreement, and close.** Both decision makers are right about part of the cost: the CFO that the products cost more than their standards say, the production manager that idle capacity is not the products' fault and belongs to the plant. Then the standards (a rate on normal capacity for inventory, relevant costs for make or buy, and time-driven costs for the pricing floor and the capacity question, with demand, opportunity cost and implementation constraints still part of each decision), what the base year's statements need (the evidence that would show whether the old standards misstated them, before anything is restated), and the one decision only the production manager can make: whether, and how fast, to reduce the crew to the work the plant has.

**Step 6. Choose the exhibits.** At most three pages hold three exhibits: the family costs under the three views (Costs), the make-or-buy table with the break-even quotes and the two-way table (Make or Buy), and the capacity, price and standards results (Capacity, Prices, Standards). Each exhibit is cited in the memo by name, with its workbook sheet and the date of its assumptions, and supports a decision or a number the memo states. Use abbreviated, legible summaries, above all on the last page, which carries three sheets, and keep the detailed worksheets for traceability. Read the exported PDF at normal size.

**Check:** read the decision table first, then trace one number in each row back to its sheet.

## Expected results

| Family | What to do | Annual effect | One-time cost |
|---|---|---:|---:|
| BNH | Buy only with the crew reduced | +$79,249 | $32,443 |
| NGT | Buy only with the crew reduced | +$67,149 | $53,067 |
| TBL | Buy only with the crew reduced | +$109,084 | $87,150 |
| SDB | Make; raise the price | +$50,779 | $0 |
| SCN | Make | $0 | $0 |
| PIL | Make | $0 | $0 |
| BKC | Raise the price | +$80,662 | $0 |
| CTB | Raise the price | +$81,312 | $0 |
| CHD | Raise the price | +$33,558 | $0 |

> **Instructor notes, Requirement 10:** a strong memo makes SDB, SCN, and PIL; buys BNH, NGT, and TBL only with a committed plan to reduce the crew in step (about 10.6 position-equivalents on the 2026 sales; otherwise keep making them and reprice); says first that, on the routings, the plant supplies about 17.8 position-equivalents of practical hours more than its completions need (997,574 of crew cost a year), more than buying would free on the same base (10.9), a larger question than outsourcing, that this is an annual estimate from standard times and not a staffing plan (6 of the 49 weekly buckets of the rough-cut plan through 2026-12-07 are above the plant's available hours), and that the two crew reductions add up only if the production manager can make both; raises BKC, CTB, SDB, and CHD to the floor (and BNH, NGT, TBL if kept) through new, approved price lists with end dates; and compares the whole paths, not one decision at a time: if volume holds, making all six and raising the seven families below the floor to it gains 556,535 a year with no one-time cost, against 501,792 for buying BNH, NGT, and TBL and raising the rest, with 172,660 once. Buying is a cost advantage at today's prices and with the crew reduced, not the better path under every assumption about price and demand: which wins depends on how much volume the increases on BNH, NGT, and TBL would cost and on the crew plan. It adopts standards on normal capacity for inventory, relevant costs for make or buy, and time-driven costs for the pricing floor and the capacity question, and raises with the CFO the evidence the fiscal 2026 inventory question needs before anything is restated. It explains the disagreement between the CFO and the production manager in their own terms: both are right about part of the cost. It says that the figures rest on fiscal 2026 for decisions that take effect in 2028, so the 2027 records so far (demand, staffing, costs) should confirm them. A memo that keeps all six families and stages the increases, unless a workable crew plan and the demand evidence favor buying, is an equally strong answer.

## What a strong answer says

- **A finding before the decisions,** worded for both readers: the unused capacity, then the two views of the cost.
- **A condition on every decision.** What happens to the crew, what the quote's terms require, what volume loss an increase can absorb.
- **Whole paths,** with the one-time costs shown, and an honest statement that buying is not the better path under every assumption. A memo that keeps all six families and stages the price increases, unless a workable crew plan and the demand evidence favor buying, is an equally strong answer.
- **The dates.** The figures rest on fiscal 2026 for decisions that take effect in 2028, so the memo names the 2027 records that should confirm them.
- **The standards and the statements,** kept apart from the make-or-buy decision, with the evidence named and no restatement claimed.
- **The production manager's decision left open,** with what it would save and cost.

A strong memo reads within two pages, and a concise one that is supported earns full credit; a weak one lists results in the order the work was done, buries the crew decision, or tells the CFO that the statements are wrong.

## Common mistakes and how to respond

- **Double counting.** *Symptom:* a total of $812,016. *Response:* ask which path each row belongs to.
- **Missing one-time costs.** *Symptom:* $70,000 of one-time cost. *Response:* ask who is paid severance.
- **Buying without a crew plan.** *Symptom:* "buy" in every decision row. *Response:* ask what the same purchase costs with the crew kept, $334,636 a year.
- **The crew decision taken.** *Symptom:* "reduce the crew by 11 positions". *Response:* ask who owns that decision, and which weeks and skills the hours come from.
- **Over the page limit.** *Symptom:* a third page of text. *Response:* ask which sentence a reader would miss.
- **A sensitivity reported as an error.** *Symptom:* "the statements were misstated". *Response:* ask what evidence at the time would show it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Decision table | 25 | Every quoted family and every family below the floor, with action, annual effect, one-time cost and dependence | Missing rows or conditions |
| Recommendation and paths | 25 | A condition on each decision, whole paths compared | Single decisions only |
| Standards and statements | 15 | Rate on normal capacity, evidence named, no restatement claimed | An error claimed without evidence |
| The crew decision | 15 | Left to the production manager, with what it would cost and save | Taken, or missing |
| Writing and limits | 15 | At most two pages and at most three of exhibits, legible; finding first, both readers addressed | Over a maximum, or results in the order of the work |
| Traceability | 5 | Every number matches the workbook | Figures that disagree with it |

## Extensions and discussion questions

- Rewrite the first section for the audit committee, which has not read the case.
- Reduce the memo to one slide and say what the slide cannot carry.
- Discuss: what would make you change a recommendation after the quote expires?
- Discuss: how should the memo say what the data cannot show?
