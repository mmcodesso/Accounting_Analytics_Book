# Exercise 4.3: List-Price Margins by Product Group

| | |
|---|---|
| Unit | Chapter 4: Excel Essentials for Accounting Analytics |
| Item | Exercise 4.3 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheets Ex 4.3 and Item |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise adds row-level measures to the Item Table and then asks the managerial question: which groups carry the highest list-price margins, and which items fall below a target. It practices calculated columns, a multi-level sort, a color scale, a formula rule, a validated parameter and a list-driven AVERAGEIFS. Its main lesson is about the measure itself: a margin at list price, averaged over items, is not the margin Charles River earns. The analytics type is descriptive.

By the end, students can:

- add calculated columns with structured references (outcome 2);
- sort on two levels and filter on a condition (outcome 4);
- write a formula-based rule and a validated parameter that drives it (outcome 5);
- use COUNTIFS and AVERAGEIFS with a selector cell, and see that a filter does not limit them (outcomes 3 and 4);
- interpret a margin at list price with its limits (outcome 1).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Data Analysis, and Cost Accounting; IFAC IES 2 (b), management accounting, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 4.3. The Item Table keeps 11 columns and 223 items, the ones with a ListPrice. The new columns land in L and M, and the formula rule refers to the MarginPct letter.
- **Data conditions.** Every finished good has a list price. The 4 design services (Design Consultation, Space Planning, Specification Development, Project Coordination) have a StandardCost of 0, so their MarginPct is 100 percent. They sit in the Services group, outside the four product groups, so leaving out the ItemType condition changes no result here. Tell students that this is luck, not a reason to leave it out.
- **Hint to hold.** A filter hides rows from view but not from COUNTIFS or AVERAGEIFS. Give it only after a student asks why the formula needs an ItemType test when the Table is already filtered.

## How to run it

Individual, about 75 minutes: 15 on the columns and the filter (requirements 1 and 2), 15 on the sort and the color scale (3), 20 on the parameter, the rule and the count (4), 10 on the selector (5) and 15 on the interpretation (6). Collect the workbook and the three or four sentences.

## Step-by-step solution

### Requirement (1): The two calculated columns

**Step 1. Add UnitMargin and MarginPct.**

a. On the **Item** worksheet, click the first empty cell right of LifecycleStatus (cell L1), type `UnitMargin` and press Enter. The Table expands.
b. In the first data cell enter `=[@ListPrice]-[@StandardCost]`. Excel fills the column.
c. Repeat in the next column with the header `MarginPct` and the formula `=[@UnitMargin]/[@ListPrice]`.
d. Format MarginPct as a percentage with one decimal.

**Check:** the Table has 223 rows and the two new columns, L and M, filled to the last row. **Watch for:** a MarginPct divided by StandardCost. That is a markup, and it reaches 177% here, so a margin above 100 percent is the symptom.

### Requirement (2): Finished goods only

**Step 2. Filter the Table and say why.**

a. Click the filter button on ItemType and show only Finished Good.
b. Read the status bar.

**Check:** 219 of 223 records are in view. The model answer: the 4 design services are billed by the hour and carry a StandardCost of 0, so their MarginPct of 100 percent says nothing about profitability. In a comparison they would top every ranking and pull the averages up.

### Requirement (3): Sort and color scale

**Step 3. Sort on two levels.** Choose **Data > Sort**. For the first level sort ItemGroup **A to Z**, choose **Add Level**, and sort MarginPct **Largest to Smallest**.

**Step 4. Add the color scale.** Select the MarginPct data cells and choose **Home > Conditional Formatting > Color Scales**, then a scale.

**Check:** the first row of the Table is ACC-CDL-0046, the Accessories item with the highest MarginPct, and the scale shades the column from low to high. **Watch for:** a scale applied to the whole Table. It shades every numeric column.

### Requirement (4): The target, the rule and the count

**Step 5. Create the validated target.**

a. On a worksheet named `Ex 4.3`, type `MarginTarget` in A4 and 0.45 in B4. Name B4 `MarginTarget` in the **Name Box** and set its font to blue.
b. Choose **Data > Data Validation** and allow a **Decimal** between 0 and 1, with an input message and the **Stop** style.

**Check:** typing 45 is refused, because the percentage was typed as a whole number.

**Step 6. Highlight the items below the target.**

a. On the Item worksheet select A2 and extend the selection to the last data row of column L, so that MarginPct is left out and A2 stays the active cell.
b. Choose **Home > Conditional Formatting > New Rule**, select **Use a formula to determine which cells to format**, and enter `=$M2<MarginTarget`.
c. Click **Format**, choose a light fill, and click **OK** twice.

**Step 7. Count them.** On `Ex 4.3` enter:

```
=COUNTIFS(Item[ItemType],"Finished Good",Item[MarginPct],"<"&MarginTarget)
```

**Check:** 27 finished goods are below the target: Furniture 20; Lighting 6; Textiles 1; Accessories 0. A second COUNTIFS with a limit of 0.3 returns 0, and the MarginPct of the finished goods runs from 39.6% to 63.9%. **Watch for:** the rule written without the dollar sign, or with another cell active. The shading then shifts across the columns. A count without the ItemType condition agrees here, as noted above.

### Requirement (5): The group selector

**Step 8. Build the selector and the averages.**

a. In A5 type `ProductGroup` and in B5 choose a **List** rule whose entries are the four product groups (Accessories, Furniture, Lighting, Textiles). Name B5 `ProductGroup`.
b. In B18 and B19 enter the two averages, with the ItemType condition:

```
=AVERAGEIFS(Item[UnitMargin],Item[ItemType],"Finished Good",Item[ItemGroup],ProductGroup)
=AVERAGEIFS(Item[MarginPct],Item[ItemType],"Finished Good",Item[ItemGroup],ProductGroup)
```

c. Choose each group in turn and record the results in a small table. The model answer keeps the table live by repeating the formulas with the group name in column A in place of `ProductGroup`.

**Check:** Furniture reads $385.62 and 49.3%. A group name that does not match the Item column exactly returns #DIV/0!.

### Requirement (6): The interpretation

**Step 9. Write three or four sentences.** A model answer: Furniture earns the most per unit and has the lowest average percentage, while Accessories earns the least per unit and has the highest. A margin at list price is not what Charles River earns, because most sales are billed at price-list prices below list, some lines carry promotions, and StandardCost is a standard. An average of item margins counts each item once, so it is not the margin on a group's sales.

**Check:** the answer names both limits and does not call the averages group margins.

## Expected results

| Group | Finished goods | Average UnitMargin | Average MarginPct | Below the target | Where |
|---|---:|---:|---:|---:|---|
| Accessories | 56 | $76.47 | 56.2% | 0 | Steps 7 and 8 |
| Furniture | 85 | $385.62 | 49.3% | 20 | Steps 7 and 8 |
| Lighting | 44 | $162.03 | 51.8% | 6 | Steps 7 and 8 |
| Textiles | 34 | $141.65 | 53.5% | 1 | Steps 7 and 8 |
| All finished goods | 219 | | 39.6% to 63.9% | 27 | Steps 2 and 7 |
| Design services; their MarginPct | 4; 100% | | | | Step 2 |
| First row after the sort | ACC-CDL-0046 | | | | Step 4 |

> **[Figure placeholder IF-04-3-A]** The Item worksheet after requirements (1) to (4), with the calculated columns, the sort, the color scale and the highlighted rows below the target.
> Kind: excel-mock · Shows: The Item Table filtered to finished goods and sorted by ItemGroup and then MarginPct from largest to smallest, scrolled to the boundary between two groups. Columns A to K are the tutorial's columns, then UnitMargin and MarginPct. A color scale shades the MarginPct column. Rows whose MarginPct is below the target carry a light fill across columns A to L only, so the scale stays visible in the last column. The status bar reports how many records are in view. · Data: Item rows with a ListPrice, for Furniture and Lighting (the Expected results table). · Status: planned

> **Instructor notes, Exercise 4.3:** 219 finished goods. The four design services have a StandardCost of 0, so their MarginPct is 100 percent. Average UnitMargin / average MarginPct: Accessories 76.47 / 56.2%; Furniture 385.62 / 49.3%; Lighting 162.03 / 51.8%; Textiles 141.65 / 53.5%. MarginPct ranges from 39.6% to 63.9%, so no item is below 30 percent; 27 items are below 0.45 (Furniture 20, Lighting 6, Textiles 1, Accessories 0). Furniture earns the most per unit but the lowest percentage. The group figures are simple averages that count each item once, whatever it sold, so they are not the groups' margins on sales. The design services change neither the count below the target nor the group averages, because their MarginPct is 100 percent and their ItemGroup is Services, so a formula without the ItemType condition happens to give the same results here; the condition is still needed, because a filter does not limit COUNTIFS or AVERAGEIFS. List-price margin overstates realized margin, because most sales are billed at price-list prices below list, some carry promotional discounts, and StandardCost is a standard, not an actual cost.

## What a strong answer says

- **Requirement (2).** The design services are a different kind of item: a standard cost of zero, so a margin of 100 percent that is arithmetic, not performance.
- **Requirement (4).** A target held in a named, validated cell, a rule that refers to it, and a count that does not depend on the filter.
- **Requirement (6).** Both limits: list price against realized price, and an average of items against a margin on sales.

A weak answer reports the averages as the groups' margins, or leaves out the second limit.

## Common mistakes and how to respond

- **A markup, not a margin.** *Symptom:* percentages above 100. *Response:* ask what the denominator of a margin is.
- **A rule that shifts.** *Symptom:* shading in the wrong rows or columns. *Response:* check the dollar sign and that A2 was active.
- **A rule that hides the scale.** *Cause:* the fill covers MarginPct. *Response:* apply the rule to the columns left of it, as the model answer does.
- **Counting with the filter.** *Symptom:* "the filter handles it". *Response:* ask which formulas see hidden rows.
- **A selector that returns an error.** *Cause:* a group name typed differently from the data. *Response:* use the list.
- **Averages called group margins.** *Response:* ask how a large item that sold once and a small one that sold often would count.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: columns | 10 | Two calculated columns with structured references and the right denominator | Typed values or a markup |
| Requirement 2: filter | 10 | Finished goods only, with the reason for excluding services | No reason |
| Requirement 3: sort and scale | 15 | Two-level sort and a scale on MarginPct only | Single-level sort |
| Requirement 4: target, rule, count | 30 | Named and validated target, a correct rule, a count with the ItemType condition | Rule without the target, or a count that depends on the filter |
| Requirement 5: selector | 20 | A list rule driving AVERAGEIFS, with all four groups recorded | A typed group, or averages without the condition |
| Requirement 6: interpretation | 15 | Both limits, in three or four sentences | One limit |

## Extensions and discussion questions

- Weight each group's margin by units invoiced, using SalesInvoiceLine, and compare it with the simple average. Chapter 5 builds the table that makes this easy.
- Add an icon set to MarginPct and say why a flag column survives a printout better.
- Discuss: should a margin target be one number for all groups, or one for each?
- Discuss: Chapter 6 measures margin at standard cost on sales. Which of this exercise's limits does that remove?
