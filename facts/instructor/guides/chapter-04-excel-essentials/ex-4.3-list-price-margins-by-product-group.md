---
note: ch04.ex3
uses: [ch04.g3]
title: List-Price Margins by Product Group
kind: exercise
number: '4.3'
unit: '4'
perspective: managerial
tool: excel
minutes: 75
solution: "Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheets Ex 4.3 and Item"
figures:
  - id: IF-04-3-A
    kind: excel-mock
    purpose: The Item worksheet after requirements (1) to (4), with the calculated columns, the sort, the color scale and the highlighted rows below the target.
    shows: "The Item Table filtered to finished goods and sorted by ItemGroup and then MarginPct from largest to smallest, scrolled to the boundary between two groups. Of the tutorial's columns A to K, ItemID, ItemName and the last four are hidden to fit the figure, and UnitMargin and MarginPct follow in columns L and M. A color scale, drawn in three steps, shades the MarginPct column. Rows whose MarginPct is below the target carry a light fill across columns A to L only, so the scale stays visible in the last column. The status bar reports how many records are in view."
    data: Item rows with a ListPrice, for Furniture and Lighting (the Expected results table).
---
{% set g = ch04_g3 %}
# Exercise 4.3: List-Price Margins by Product Group

{{ header() }}

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

- **Files.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 4.3. The Item Table keeps {{ g.kept }} columns and {{ g.n_items }} items, the ones with a ListPrice. The new columns land in {{ g.letters.UnitMargin }} and {{ g.letters.MarginPct }}, and the formula rule refers to the MarginPct letter.
- **Data conditions.** Every finished good has a list price. The {{ g.n_services|count }} design services ({{ g.services|map(attribute='name')|join(', ') }}) have a StandardCost of 0, so their MarginPct is 100 percent. They sit in the Services group, outside the four product groups, so leaving out the ItemType condition changes no result here. Tell students that this is luck, not a reason to leave it out.
- **Hint to hold.** A filter hides rows from view but not from COUNTIFS or AVERAGEIFS. Give it only after a student asks why the formula needs an ItemType test when the Table is already filtered.

## How to run it

Individual, about 75 minutes: 15 on the columns and the filter (requirements 1 and 2), 15 on the sort and the color scale (3), 20 on the parameter, the rule and the count (4), 10 on the selector (5) and 15 on the interpretation (6). Collect the workbook and the three or four sentences.

## Step-by-step solution

### Requirement (1): The two calculated columns

**Step 1. Add UnitMargin and MarginPct.**

a. On the **Item** worksheet, click the first empty cell right of LifecycleStatus (cell {{ g.letters.UnitMargin }}1), type `UnitMargin` and press Enter. The Table expands.
b. In the first data cell enter `=[@ListPrice]-[@StandardCost]`. Excel fills the column.
c. Repeat in the next column with the header `MarginPct` and the formula `=[@UnitMargin]/[@ListPrice]`.
d. Format MarginPct as a percentage with one decimal.

**Check:** the Table has {{ g.n_items }} rows and the two new columns, {{ g.letters.UnitMargin }} and {{ g.letters.MarginPct }}, filled to the last row. **Watch for:** a MarginPct divided by StandardCost. That is a markup, and it reaches {{ g.markup_max|pct(0) }} here, so a margin above 100 percent is the symptom.

### Requirement (2): Finished goods only

**Step 2. Filter the Table and say why.**

a. Click the filter button on ItemType and show only Finished Good.
b. Read the status bar.

**Check:** {{ g.n_goods }} of {{ g.n_items }} records are in view. The model answer: the {{ g.n_services }} design services are billed by the hour and carry a StandardCost of 0, so their MarginPct of 100 percent says nothing about profitability. In a comparison they would top every ranking and pull the averages up.

### Requirement (3): Sort and color scale

**Step 3. Sort on two levels.** Choose **Data > Sort**. For the first level sort ItemGroup **A to Z**, choose **Add Level**, and sort MarginPct **Largest to Smallest**.

**Step 4. Add the color scale.** Select the MarginPct data cells and choose **Home > Conditional Formatting > Color Scales**, then a scale.

**Check:** the first row of the Table is {{ g.first }}, the Accessories item with the highest MarginPct, and the scale shades the column from low to high. **Watch for:** a scale applied to the whole Table. It shades every numeric column.

### Requirement (4): The target, the rule and the count

**Step 5. Create the validated target.**

a. On a worksheet named `Ex 4.3`, type `MarginTarget` in A4 and {{ g.target }} in B4. Name B4 `MarginTarget` in the **Name Box** and set its font to blue.
b. Choose **Data > Data Validation** and allow a **Decimal** between 0 and 1, with an input message and the **Stop** style.

**Check:** typing 45 is refused, because the percentage was typed as a whole number.

**Step 6. Highlight the items below the target.**

a. On the Item worksheet select A2 and extend the selection to the last data row of column {{ g.letters.UnitMargin }}, so that MarginPct is left out and A2 stays the active cell.
b. Choose **Home > Conditional Formatting > New Rule**, select **Use a formula to determine which cells to format**, and enter `=${{ g.letters.MarginPct }}2<MarginTarget`.
c. Click **Format**, choose a light fill, and click **OK** twice.

**Step 7. Count them.** On `Ex 4.3` enter:

```
=COUNTIFS(Item[ItemType],"Finished Good",Item[MarginPct],"<"&MarginTarget)
```

**Check:** {{ below }} finished goods are below the target: {% for n, k in below_by %}{{ n }} {{ k }}{{ '; ' if not loop.last else '' }}{% endfor %}. A second COUNTIFS with a limit of 0.3 returns 0, and the MarginPct of the finished goods runs from {{ low|pct }} to {{ high|pct }}. **Watch for:** the rule written without the dollar sign, or with another cell active. The shading then shifts across the columns. A count without the ItemType condition agrees here, as noted above.

### Requirement (5): The group selector

**Step 8. Build the selector and the averages.**

a. In A5 type `ProductGroup` and in B5 choose a **List** rule whose entries are the four product groups ({{ g.groups|join(', ') }}). Name B5 `ProductGroup`.
b. In B18 and B19 enter the two averages, with the ItemType condition:

```
=AVERAGEIFS(Item[UnitMargin],Item[ItemType],"Finished Good",Item[ItemGroup],ProductGroup)
=AVERAGEIFS(Item[MarginPct],Item[ItemType],"Finished Good",Item[ItemGroup],ProductGroup)
```

c. Choose each group in turn and record the results in a small table. The model answer keeps the table live by repeating the formulas with the group name in column A in place of `ProductGroup`.

**Check:** Furniture reads ${{ g.most.margin|money }} and {{ g.most.pct|pct }}. A group name that does not match the Item column exactly returns #DIV/0!.

### Requirement (6): The interpretation

**Step 9. Write three or four sentences.** A model answer: {{ g.most.name }} earns the most per unit and has the lowest average percentage, while {{ g.least.name }} earns the least per unit and has the highest. A margin at list price is not what Charles River earns, because most sales are billed at price-list prices below list, some lines carry promotions, and StandardCost is a standard. An average of item margins counts each item once, so it is not the margin on a group's sales.

**Check:** the answer names both limits and does not call the averages group margins.

## Expected results

| Group | Finished goods | Average UnitMargin | Average MarginPct | Below the target | Where |
|---|---:|---:|---:|---:|---|
{% for r in g.rows %}
| {{ r.name }} | {{ r.n|count }} | ${{ r.margin|money }} | {{ r.pct|pct }} | {{ r.below }} | Steps 7 and 8 |
{% endfor %}
| All finished goods | {{ g.n_goods|count }} | | {{ low|pct }} to {{ high|pct }} | {{ below }} | Steps 2 and 7 |
| Design services; their MarginPct | {{ g.n_services }}; {{ g.service_pct|pct(0) }} | | | | Step 2 |
| First row after the sort | {{ g.first }} | | | | Step 4 |

{{ figure('IF-04-3-A') }}

{{ expected() }}

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
