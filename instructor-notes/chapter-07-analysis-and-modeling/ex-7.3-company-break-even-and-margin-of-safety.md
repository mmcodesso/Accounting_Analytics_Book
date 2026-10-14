# Exercise 7.3: Company Break-Even and Margin of Safety

| | |
|---|---|
| Unit | Chapter 7: Forecasting, Budgeting, and What-If Analysis in Excel |
| Item | Exercise 7.3 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.3, with the query GLCostVariances |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial 7.3 modeled one decision. This exercise models the whole company: how far can revenue fall before the operating profit disappears? It makes students choose what is variable and what is fixed, test the choice by adding items the first version leaves out, and map the answer with a data table and Goal Seek. The analytics type is prescriptive, with the diagnostic question of which costs belong where.

By the end, students can:

- calculate a contribution margin ratio, break-even revenue and a margin of safety from recorded amounts (outcome 4);
- defend the choice of fixed costs, including the items that do not belong (interest) and those that standard costs omit (outcomes 4 and 5);
- build a two-variable data table and use Goal Seek for a target profit, and say what each cannot do (outcome 5).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning, and Performance: Decision Analysis; IFAC IES 2 (b); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, with InvoiceLines, BudgetLine and GLOpex (Tutorial 7.2). Students import the ledger again for requirement 4, with **Transform Data**, never **Load**.
- **Data conditions.** Services lines carry no standard cost, so design staff sit in the fixed costs. The budget files interest expense under Operating Expense although the chart of accounts makes it Other Expense. Accounts for freight-out, the purchase price variance and the manufacturing variance have journal-entry rows that are only the year-end close, so excluding the JournalEntry source removes just the close. The manufacturing variance grows every year of the window.
- **Verify first.** Run requirement 4 once. GLCostVariances holds 34,822 rows.

## How to run it

Individual, about 90 minutes: 15 for the ratio (requirement 1), 10 for the fixed costs (2), 5 for the break-even (3), 25 for the ledger query and the second break-even (4), 20 for the data table and Goal Seek (5) and 15 for the memo (6). Hold back the second set of fixed costs until students have the first answer and have been asked what that margin of safety would mean for a plant. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The contribution margin ratio

**Step 1. Set up the model.** On a worksheet named `Ex 7.3` enter the year in B3 in blue, then calculate in B5 to B9:

```
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[FiscalYear],$B$3)
=SUMIFS(InvoiceLines[StdCostAmount],InvoiceLines[FiscalYear],$B$3)
=SUMIFS(GLOpex[Amount],GLOpex[AccountNumber],6290)
=B5-B6-B7
=B8/B5
```

**Check:** revenue $29,756,420.08, standard cost $15,803,272.88, commissions $566,347.93, contribution margin $13,386,799.27, ratio 44.99%. **Watch for:** the commission taken from the budget and not from GLOpex, which is a different amount and a different ratio.

### Requirement (2): The fixed costs

**Step 2. Take the operating-expense budget and remove two items.** B11 is the operating-expense budget, B12 the commission budget (commissions are already in the margin), B13 the interest budget, and B14 `=B11-B12-B13`.

**Check:** $8,318,595.27 less $2,264,973.29 and $28,946.47 is $6,024,675.51. **Watch for:** the commission budget left in, which counts commissions twice and raises break-even by about $5,035,000, or the interest left in, which models profit after interest and raises it by about $64,342.74.

The two sentences of the answer: the expenses are salaries, rent, depreciation and other recurring costs that do not move with sales, and Tutorial 7.2 showed every account except two within a few percent of actual.

### Requirement (3): Break-even and margin of safety

**Step 3.** B15 `=B14/B9`, B16 `=B5-B15`, B17 `=B16/B5`.

**Check:** break-even $13,391,757.93, margin of safety $16,364,662.15 (55.0%).

### Requirement (4): The items that standard costs omit

**Step 4. Import the ledger again.** Choose **Data > Get Data > From File > From Excel Workbook**, select T3_GLEntry in the **Navigator** and click **Transform Data**. Name the query `GLCostVariances`, then filter FiscalYear to 2026, AccountID to the three accounts, and SourceDocumentType to exclude JournalEntry. The three AccountIDs are 54, 55 and 93. Load it to a worksheet.

**Step 5. Add the three accounts.** In B19 to B21, debits less credits for each account:

```
=SUMIFS(GLCostVariances[Debit],GLCostVariances[AccountID],54)-SUMIFS(GLCostVariances[Credit],GLCostVariances[AccountID],54)
```

for the other two accounts too, then B22 `=SUM(B19:B21)`, B23 `=B14+B22`, B24 `=B23/B9`, B25 `=B5-B24`, B26 `=B25/B5`.

**Check:** $513,133.49, $176,011.36 and $2,265,636.88, $2,954,781.73 in all; fixed costs $8,979,457.24; break-even $19,959,700.32; margin of safety 32.9%. **Watch for:** the closing entry left in. The close credits each of the three accounts, so they net to almost nothing and B22 reads almost nothing.

### Requirement (5): The data table and Goal Seek

**Step 6. Build the data table.**

a. In D3 enter `=B24`. In E3:O3 type the ratios `0.40` to `0.50` in steps of `0.01`, formatted as percentages. In D4:D12 type fixed costs from `6000000` to `10000000` in steps of `500000`.
b. Select D3:O12 and choose **Data > What-If Analysis > Data Table**.
c. Enter B9 as the **Row input cell** and B23 as the **Column input cell**, and click **OK**.

![A mock of the two-variable data table of Requirement 5, with the cell nearest the model's own assumptions outlined.](../figures/chapter-07-analysis-and-modeling/IF-07-3-A.pdf)

**Check:** the corners read $15,000,000 (40 percent, 6 million) and $20,000,000 (50 percent, 10 million), and the cell for 45 percent and 9 million reads $20,000,000. **Watch for:** the inputs swapped. The ratios are then substituted as fixed costs and the fixed costs as ratios, and the grid shows values near zero.

**Step 7. Use Goal Seek for the target.** Type `4000000` in B28, a starting revenue in B29 and `=B29*B9-B23` in B30. Choose **Data > What-If Analysis > Goal Seek**, enter B30 in **Set cell**, `4000000` in **To value** and B29 in **By changing cell**, and click **OK**. Click **OK** again in the **Goal Seek Status** dialog to keep the answer. In B31 enter `=(B28+B23)/B9` as a check and in B32 `=(B28+B14)/B9`.

**Check:** B29 and B31 read $28,850,972.83; without the added items $22,283,030.44.

### Requirement (6): The memo

**Step 8. Write it.** An outline: the ratio and the base year; break-even and the margin of safety for each set of fixed costs; the assumption that matters most.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Revenue | $29,756,420.08 | 1 |
| Standard cost of the products | $15,803,272.88 | 1 |
| Sales commissions, without the close JE-2026-000296 | $566,347.93 | 1 |
| Contribution margin; ratio | $13,386,799.27; 44.99% | 1 |
| Fixed costs | $6,024,675.51 | 2 |
| Break-even revenue; margin of safety | $13,391,757.93; $16,364,662.15 (55.0%) | 3 |
| 5050 Freight-Out | $513,133.49 | 5 |
| 5060 Purchase Price Variance | $176,011.36 | 5 |
| 5080 Manufacturing Variance | $2,265,636.88 | 5 |
| Break-even with the added items; margin of safety | $19,959,700.32; 32.9% | 5 |
| Revenue for an operating income of 4 million, with and without the added items | $28,850,972.83; $22,283,030.44 | 7 |

> **Instructor notes, Exercise 7.3:** 2026 revenue 29,756,420.08 (including Services); standard cost of products 15,803,272.88; commissions (GL 6290, excluding close JE-2026-000296) 566,347.93; contribution margin 13,386,799.27; CM ratio 44.99%. Fixed costs: 2026 operating-expense budget 8,318,595.27 less commission budget 2,264,973.29 and interest budget 28,946.47 (account 7030, which the budget files under Operating Expense but the income statement shows below operating income) = 6,024,675.51; a student who keeps the interest models profit after interest rather than operating income, with break-even about 64,342.74 higher (the budget is reasonable because salaries, rent, depreciation, and the other recurring accounts came within a few percent of actual, as Tutorial 7.2 showed). Break-even revenue 13,391,757.93; margin of safety 16,364,662.15 (55.0%). Adding 5050 Freight-Out 513,133.49, 5060 Purchase Price Variance 176,011.36, and 5080 Manufacturing Variance 2,265,636.88 (total 2,954,781.73): break-even 19,959,700.32, margin of safety 32.9%. Goal Seek for operating income of 4,000,000 under (4): revenue 28,850,972.83; without the added items it would be 22,283,030.44. Treating Services' design staff as fixed and all product standard cost as variable are further simplifications worth naming.

## What a strong answer says

- **Requirement (2).** The budget is a reasonable source because the recurring expenses came close to budget. The commission is out because it varies with revenue and is already in the margin. Interest is out because it is a financing cost shown below operating income.
- **Requirement (6).** A break-even figure for each set of fixed costs, with the second preferred. The assumption that matters most is the manufacturing variance treated as fixed: it grew from $1,317,927.32 to $1,861,950.08 to $2,265,636.88, and returning to its first-year level would lower break-even revenue by about $2,107,000. The ratio matters too: each percentage point moves break-even revenue by about $444,000. Services' design staff treated as fixed and all of the products' standard cost as variable are further simplifications.

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
| Requirement 6: memo | 20 | Both estimates, the key assumption named | No key assumption |

## Extensions and discussion questions

- Treat half of the manufacturing variance as variable and recompute. How far does break-even move?
- Repeat requirement 3 with the budget of the first year of the window as the fixed costs. How stable is the margin of safety?
- Discuss: a margin of safety of 33% instead of 55%. Which would you tell a lender?
- Discuss: Chapter 18 separates the variable and fixed parts of standard cost. What would change in this model?
