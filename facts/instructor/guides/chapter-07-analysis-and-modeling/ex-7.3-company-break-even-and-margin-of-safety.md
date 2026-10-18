---
note: ch07.ex3
uses: [ch07.g3]
title: Company Break-Even and Margin of Safety
kind: exercise
number: '7.3'
unit: '7'
perspective: managerial
tool: excel
minutes: 90
solution: "Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.3, with the query GLCostVariances"
figures:
  - id: IF-07-3-A
    kind: excel-mock
    purpose: The two-variable data table of Requirement 5, with the cell nearest the model's own assumptions outlined.
    shows: "The worksheet Ex 7.3, D2:O12. A title row, the corner cell D3 showing the break-even revenue, the percentages 40 to 50 across row 3, fixed costs from 6 to 10 million in steps of half a million down column D, and a grid of break-even revenues with thousands separators. The cell nearest the contribution margin ratio and fixed costs of Requirement 4 is outlined."
    data: The break-even revenue at each ratio and fixed-cost pair (fixed costs divided by the ratio) and the model's own ratio and fixed costs of Requirement 4.
---
{% set g = ch07_g3 %}
# Exercise 7.3: Company Break-Even and Margin of Safety

{{ header() }}

## Purpose and learning outcomes

Tutorial 7.3 modeled one decision. This exercise models the whole company: how far can revenue fall before the operating profit disappears? It makes students choose what is variable and what is fixed, test the choice by adding items the first version leaves out, and map the answer with a data table and Goal Seek. The analytics type is prescriptive, with the diagnostic question of which costs belong where.

By the end, students can:

- calculate a contribution margin ratio, break-even revenue and a margin of safety from recorded amounts (outcome 4);
- defend the choice of fixed costs, including the items that do not belong (interest) and those that standard costs omit (outcomes 4 and 5);
- build a two-variable data table and use Goal Seek for a target profit, and say what each cannot do (outcome 5).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning, and Performance: Decision Analysis; IFAC IES 2 (b); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, with InvoiceLines, BudgetLine and GLOpex (Tutorial 7.2). Students import the ledger again for requirement 4, with **Transform Data**, never **Load**.
- **Data conditions.** Services lines carry no standard cost, so design staff sit in the fixed costs. The budget files interest expense under Operating Expense although the chart of accounts makes it {{ g.interest_subtype }}. In {{ d.C }}, the journal-entry rows on the accounts for freight-out, the purchase price variance and the manufacturing variance are only the year-end close, so excluding the JournalEntry source removes just the close. That exclusion is not a general rule. In {{ d.F }} a Factory Overhead entry ({{ g.je_first|money }}) also posts to the manufacturing variance account, so a year-by-year extension identifies the closing vouchers by their EntryType instead. The manufacturing variance grows every year of the window.
- **Verify first.** Run requirement 4 once. GLCostVariances holds {{ g.n_rows|count }} rows.

## How to run it

Individual, about 90 minutes: 15 for the ratio (requirement 1), 10 for the fixed costs (2), 5 for the break-even (3), 25 for the ledger query and the second break-even (4), 20 for the data table and Goal Seek (5) and 15 for the memo (6). Hold back the second set of fixed costs until students have the first answer and have been asked what that margin of safety would mean for a plant. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The contribution margin ratio

**Step 1. Set up the model.** On a worksheet named `Ex 7.3` set B3 to {{ d.C }} and label A3 `Base year (fixed)`. B3 is not a year selector, because BudgetLine, GLOpex and GLCostVariances are filtered to {{ d.C }}, and a different year needs every input, query filter and closing-entry exclusion changed together. Then calculate in B5 to B9:

```
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[FiscalYear],$B$3)
=SUMIFS(InvoiceLines[StdCostAmount],InvoiceLines[FiscalYear],$B$3)
=SUMIFS(GLOpex[Amount],GLOpex[AccountNumber],6290)
=B5-B6-B7
=B8/B5
```

**Check:** revenue ${{ revenue|money }}, standard cost ${{ cost|money }}, commissions ${{ commissions|money }}, contribution margin ${{ cm|money }}, ratio {{ ratio|pct(2) }}. **Watch for:** the commission taken from the budget and not from GLOpex, which is a different amount and a different ratio.

### Requirement (2): The fixed costs

**Step 2. Take the operating-expense budget and remove two items.** B11 is the operating-expense budget, B12 the commission budget (commissions are already in the margin), B13 the interest budget, and B14 the fixed costs.

```
B11  =SUMIFS(BudgetLine[BudgetAmount],BudgetLine[BudgetCategory],"Operating Expense")
B12  =SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountNumber],6290)
B13  =SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountNumber],7030)
B14  =B11-B12-B13
```

**Check:** ${{ opex|money }} less ${{ budget_commission|money }} and ${{ interest|money }} is ${{ fixed|money }}. **Watch for:** the commission budget left in, which counts commissions twice and raises break-even by about ${{ g.commission_effect|num(0) }}, or the interest left in, which models profit after interest and raises it by about ${{ interest_effect|money }}.

The two sentences of the answer: the expenses are salaries, rent, depreciation and other recurring costs that do not move with sales, and Tutorial 7.2 showed every account except two within a few percent of actual.

### Requirement (3): Break-even and margin of safety

**Step 3.** B15 `=B14/B9`, B16 `=B5-B15`, B17 `=B16/B5`.

**Check:** break-even ${{ breakeven|money }}, margin of safety ${{ safety|money }} ({{ safety_pct|pct(1) }}).

### Requirement (4): The items that standard costs omit

**Step 4. Import the ledger again.** Choose **Data > Get Data > From File > From Excel Workbook**, select T3_GLEntry in the **Navigator** and click **Transform Data**. Name the query `GLCostVariances`, then filter FiscalYear to {{ d.C }}, AccountID to the three accounts, and SourceDocumentType to exclude JournalEntry. The three AccountIDs are {{ g.ids['5050'] }}, {{ g.ids['5060'] }} and {{ g.ids['5080'] }}. Load it to a worksheet.

**Step 5. Add the three accounts.** In B19 to B21, debits less credits for each account:

```jinja
=SUMIFS(GLCostVariances[Debit],GLCostVariances[AccountID],{{ g.ids['5050'] }})-SUMIFS(GLCostVariances[Credit],GLCostVariances[AccountID],{{ g.ids['5050'] }})
```

for the other two accounts too, then B22 `=SUM(B19:B21)`, B23 `=B14+B22`, B24 `=B23/B9`, B25 `=B5-B24`, B26 `=B25/B5`.

**Check:** ${{ added[0][2]|money }}, ${{ added[1][2]|money }} and ${{ added[2][2]|money }}, ${{ added_total|money }} in all; fixed costs ${{ g.fixed2|money }}; break-even ${{ breakeven2|money }}; margin of safety {{ safety2_pct|pct(1) }}. **Watch for:** the closing entry left in. The close credits each of the three accounts, so they net to almost nothing and B22 reads almost nothing.

### Requirement (5): The data table and Goal Seek

**Step 6. Build the data table.**

a. In D3 enter `=B24`. In E3:O3 type the ratios `0.40` to `0.50` in steps of `0.01`, formatted as percentages. In D4:D12 type fixed costs from `6000000` to `10000000` in steps of `500000`.
b. Select D3:O12 and choose **Data > What-If Analysis > Data Table**.
c. Enter B9 as the **Row input cell** and B23 as the **Column input cell**, and click **OK**.

{{ figure('IF-07-3-A') }}

**Check:** the corners read ${{ g.corner_low|num(0) }} (40 percent, 6 million) and ${{ g.corner_high|num(0) }} (50 percent, 10 million), and the cell for 45 percent and 9 million reads ${{ g.cell|num(0) }}. **Watch for:** the inputs swapped. The ratios are then substituted as fixed costs and the fixed costs as ratios, and the grid shows values near zero.

**Step 7. Use Goal Seek for the target.** Type `4000000` in B28, a starting revenue in B29 and `=B29*B9-B23` in B30. Choose **Data > What-If Analysis > Goal Seek**, enter B30 in **Set cell**, `4000000` in **To value** and B29 in **By changing cell**, and click **OK**. Click **OK** again in the **Goal Seek Status** dialog to keep the answer. In B31 enter `=(B28+B23)/B9` as a check and in B32 `=(B28+B14)/B9`.

**Check:** B29 and B31 read ${{ goal|money }}; without the added items ${{ goal_without|money }}.

### Requirement (6): The memo

**Step 8. Write it.** An outline: the ratio and the base year; break-even and the margin of safety for each set of fixed costs; the assumption that matters most.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Revenue | ${{ revenue|money }} | 1 |
| Standard cost of the products | ${{ cost|money }} | 1 |
| Sales commissions, without the close {{ close }} | ${{ commissions|money }} | 1 |
| Contribution margin; ratio | ${{ cm|money }}; {{ ratio|pct(2) }} | 1 |
| Fixed costs | ${{ fixed|money }} | 2 |
| Break-even revenue; margin of safety | ${{ breakeven|money }}; ${{ safety|money }} ({{ safety_pct|pct(1) }}) | 3 |
{% for n, name, amount in added %}
| {{ n }} {{ name }} | ${{ amount|money }} | 5 |
{% endfor %}
| Break-even with the added items; margin of safety | ${{ breakeven2|money }}; {{ safety2_pct|pct(1) }} | 5 |
| Revenue for an operating income of 4 million, with and without the added items | ${{ goal|money }}; ${{ goal_without|money }} | 7 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The budget is a reasonable source because the recurring expenses came close to budget. The commission is out because it varies with revenue and is already in the margin. Interest is out because it is a financing cost shown below operating income.
- **Requirement (6).** A break-even estimate with the fixed costs behind it. The assumption that matters most is the manufacturing variance treated as fixed: it grew from ${{ g.variance[0][1]|money }} to ${{ g.variance[1][1]|money }} to ${{ g.variance[2][1]|money }}, and returning to its first-year level would lower break-even revenue by about ${{ g.reduction|num(0) }}. The ratio matters too. Near the current assumptions, a one-percentage-point change moves break-even revenue by about ${{ g.per_point|num(0) }}, a local effect that is not constant over the whole grid of the data table. Services' design staff treated as fixed and all of the products' standard cost as variable are further simplifications.
- **A plus.** Both estimates side by side. The second includes costs the first leaves out, and the exercise treats freight-out and the two variances as fixed-equivalent costs for this scenario, which the totals do not establish. Both estimates also assume a constant sales mix, unchanged prices and unit costs, and a stated range of activity, and the strongest answers test an alternative cost-behavior assumption before recommending one economic estimate.

A weak answer reports the first break-even without noticing what the standard costs omit, or names no assumption.

## Common mistakes and how to respond

- **Interest left in.** *Symptom:* fixed costs above the model answer by the interest budget. *Response:* ask where the income statement puts interest.
- **Commission budget left in.** *Symptom:* a break-even that is too high. *Response:* ask where the commissions already are.
- **The closing entry included.** *Symptom:* the three accounts near zero. *Response:* ask what a year-end closing entry does to an expense account.
- **Swapped data table inputs.** *Symptom:* implausibly small values. *Response:* ask which input runs across the top.
- **Goal Seek on a formula cell.** *Symptom:* Goal Seek refuses to run. *Response:* ask which cell Goal Seek is allowed to change.
- **Cancelled Goal Seek.** *Symptom:* B29 back at its start. *Response:* ask what the exercise does with the answer, unlike Tutorial 7.3.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the ratio | 15 | Revenue, standard cost and actual commissions from the right sources | A source wrong |
| Requirement 2: fixed costs | 15 | Commissions and interest removed, two-sentence reason | Reason missing |
| Requirement 3: break-even | 10 | Break-even and margin of safety, in dollars and percent | One missing |
| Requirement 4: added items | 20 | Query filtered correctly, three items, second break-even | Closing entry left in |
| Requirement 5: table and Goal Seek | 20 | Data table with the right inputs, Goal Seek result kept | Inputs swapped, or no Goal Seek |
| Requirement 6: memo | 20 | A break-even estimate with its fixed costs, the key assumption named | No key assumption |

## Extensions and discussion questions

- Treat half of the manufacturing variance as variable and recompute. Remove that half from the fixed costs and add its ratio to revenue to the variable costs, so that the total modeled cost at the base-year revenue stays the same. Break-even then falls by about ${{ g.half_move|num(0) }}, to ${{ g.half_be|num(0) }}. Taking the half out of the fixed costs alone, with the ratio unchanged, gives ${{ g.half_naive|num(0) }}, which changes the cost behavior and the baseline cost together.
- Repeat requirement 3 with the budget of the first year of the window as the fixed costs. How stable is the margin of safety?
- Discuss: a margin of safety of {{ safety2_pct|pct(0) }} instead of {{ safety_pct|pct(0) }}. Which would you tell a lender?
- Discuss: Chapter 18 separates the variable and fixed parts of standard cost. What would change in this model?
