# Exercise 6.4: The Margin Bridge by Product Type

| | |
|---|---|
| Unit | Chapter 6: Descriptive and Diagnostic Analytics in Excel |
| Item | Exercise 6.4 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheet Ex 6.4 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial 6.3 decomposed the change in the Furniture margin for Furniture as a whole. This exercise repeats it product type by product type, the level at which the sales team plans its assortment, and asks what changes. It is the hardest exercise of the chapter because the four formulas must be built by hand and must add up. It practices PivotTables read with GETPIVOTDATA, per-unit measures, a decomposition with a check and a recommendation about the level of a report. The analytics type is diagnostic.

By the end, students can:

- calculate price, cost, volume and mix effects for several product types and show that they sum to the change in margin (outcome 5);
- explain why the cost effect is no longer zero although no standard cost changed (outcome 5);
- recommend the level at which a bridge should be reported (outcomes 4 and 5).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S1 M8 T3 to T4 (data mining and analysis of financial data); IMA Data Analysis and Strategic Cost Management; IFAC IES 2 (b) and IES 3 (a); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3, with its Bridge worksheet, which the comparison reads.
- **Data conditions.** All 8 Furniture product types sell in both quarters. The quantities are fractional, so the per-unit measures are totals divided by totals and are not literal units.
- **A definition to hand out.** The volume effect uses the Furniture margin per unit of the third quarter for the change in total units, and the mix effect uses each type's own third-quarter margin per unit. A student who defines volume by type gets a bridge that does not add up.

## How to run it

Individual or pairs, about 90 minutes: 15 on the PivotTable (requirement 1), 25 on the per-unit measures (2), 25 on the four effects and the check (3), 15 on the comparison (4) and 10 on the recommendation (5). Give the effect formulas only when a pair has tried the check cell and found it nonzero. Collect the workbook and the comparison.

## Step-by-step solution

### Requirement (1): The PivotTable

**Step 1. Build it.**

a. Insert a PivotTable from the InvoiceLines Table on a new worksheet named `Ex 6.4`. Drag ItemGroup to **Filters** and select Furniture, ProductType to **Rows** and Period to **Columns**.
b. Open the **Column Labels** filter and keep only 2026-Q3 and 2026-Q4.
c. Drag Quantity, LineTotal and StdCostAmount to **Values**, and remove the Grand Total column at the right, which adds the two quarters. Keep the Grand Total row at the bottom.
d. Read the values into a table below with GETPIVOTDATA, or paste them as values.

**Check:** Furniture totals of 7,091.23 then 7,122.12 units, revenue $4,283,322.86 then $4,156,787.84, standard cost $2,473,065.77 then $2,461,576.82. **Watch for:** values pasted with the Furniture filter off, so the types include other lines that use the same codes.

### Requirement (2): Per-unit measures

**Step 2. Add the per-unit measures.** In the table, with the third-quarter values in B to D and the fourth-quarter values in E to G for each type, enter these formulas in the first row of types and fill down:

```
Price per unit, Q3    =C20/B20
Cost per unit, Q3     =D20/B20
Margin per unit, Q3   =H20-I20
Price per unit, Q4    =F20/E20
Cost per unit, Q4     =G20/E20
Margin per unit, Q4   =K20-L20
Share of Q3 units     =B20/$B$28
```

**Check:** the per-unit columns of the Expected results. **Watch for:** the share divided by the wrong total. The shares add up to 100 percent.

### Requirement (3): The four effects

**Step 3. Calculate the effects by type and sum them.** In the row of the first type enter the price, cost and mix effects, and fill down. Row 28 holds the Furniture totals.

```
Price effect   =E20*(K20-H20)
Cost effect    =-E20*(L20-I20)
Mix effect     =(E20-$E$28*N20)*J20
```

Then compute the volume effect once, from the totals, and check the sum:

```
Volume   =(E28-B28)*J28
Check    =ROUND(B39-B34,2)
```

In the model answer B39 holds the sum of the four effects and B34 the change in margin.

**Check:** the check reads zero. The effects are price -$183,737.35, cost +$43,345.66, volume +$7,885.63 and mix +$17,459.98, summing to the change of -$115,046.07. **Watch for:** the cost sign. A rise in cost per unit reduces margin, so the cost effect carries a minus in front of the rise, and a wrong sign leaves the check off by twice the cost effect.

### Requirement (4): The comparison

**Step 4. Set the two bridges side by side.** In two columns, list the effects of this exercise and those of the Bridge worksheet, with price in Tutorial 6.3 as price lists plus promotions.

![A mock of the two bridges of Exercise 6.4 side by side, which is the comparison of requirement 4.](../figures/chapter-06-descriptive-analytics/IF-06-4-A.pdf)

**Check:** volume is the same in both ($7,885.63). Price is -$119,613.77 at the Furniture level, with +$1,073.25 from price lists and -$120,687.02 from promotions, and -$183,737.35 by type. Cost is zero against +$43,345.66. Mix is -$3,317.93 against +$17,459.98. The promotions inside the price effect are -$119,768.52 by type.

**Step 5. Explain the cost effect.** Use the type with the largest change in cost per unit: DSK. Its price per unit falls from $731.85 to $628.50 and its cost per unit from $406.55 to $359.63, because cheaper desks made up more of the quarter. At the Furniture level that shift is mix. By type it appears as an unfavorable price effect and a favorable cost effect. BNH and TBL move the same way.

### Requirement (5): The recommendation

**Step 6. Recommend a level.** The model answer presents the Furniture-level bridge as the headline, because its cost effect is zero by construction and its mix effect measures the change in list margin per unit from the items sold. Its price-list and promotion effects are changes in the average reduction per unit, which a shift between items can also move, so both bridges rest on a stated convention. The product-type bridge is supporting detail for the sales team and should be labeled as one in which item mix appears as price and cost.

## Expected results

| Product type | Q3 and Q4 units | Price per unit, Q3 to Q4 | Cost per unit, Q3 to Q4 |
|---|---|---|---|
| BKC (bookcase) | 475.61; 517.59 | $545.86; $574.05 | $334.63; $357.61 |
| BNH (bench) | 374.62; 422.79 | $625.24; $566.62 | $382.84; $357.16 |
| CON (console table) | 636.04; 667.36 | $714.01; $755.66 | $400.59; $429.88 |
| CTB (coffee table) | 1,296.08; 1,240.95 | $565.44; $556.15 | $330.10; $332.22 |
| DSK (desk) | 1,050.73; 1,195.45 | $731.85; $628.50 | $406.55; $359.63 |
| NGT (nightstand) | 905.06; 734.14 | $505.54; $503.95 | $294.84; $300.10 |
| SDB (sideboard) | 1,072.57; 958.22 | $590.27; $583.08 | $338.85; $339.02 |
| TBL (dining table) | 1,280.52; 1,385.62 | $580.12; $538.12 | $336.11; $325.65 |

| Effect | By product type | Tutorial 6.3 |
|---|---:|---:|
| Third-quarter margin | $1,810,257.09 | $1,810,257.09 |
| Fourth-quarter margin | $1,695,211.02 | $1,695,211.02 |
| Price | -$183,737.35 | -$119,613.77 |
| Cost | $43,345.66 | Zero |
| Volume | $7,885.63 | $7,885.63 |
| Mix | $17,459.98 | -$3,317.93 |

> **Instructor notes, Exercise 6.4:** Furniture margin 1,810,257.09 (Q3) to 1,695,211.02 (Q4), change -115,046.07. Product-type bridge: price -183,737.35, cost +43,345.66, volume +7,885.63, mix +17,459.98 (sums exactly). The cost effect is not zero because each type's average standard cost per unit depends on which of its items were sold: DSK (desks) price per unit 731.85 to 628.50 and cost per unit 406.55 to 359.63, as cheaper desks made up more of the quarter; TBL and BNH move the same way, and price and cost per unit rose together for CON and BKC. At this level, within-type item mix appears as price and cost; the price effect also contains the promotional discount (about -119,800 at this level). Units by type Q3 to Q4: NGT 905.06 to 734.14 and SDB 1,072.57 to 958.22 fell; DSK 1,050.73 to 1,195.45 and TBL 1,280.52 to 1,385.62 rose. Tutorial 6.3's Furniture-level bridge is the better headline because its cost effect is zero and its mix effect works at the item level, with the product-type view as supporting detail for the sales team. Both bridges assign the change by a convention. A shift between items also moves the average price-list and promotion reductions per unit, so a price effect is not by itself evidence of a price change.

## What a strong answer says

- **Requirement (3).** The four effects sum to the change, and the check cell shows it.
- **Requirement (4).** The change in margin is the same, and so is volume. The rest is divided differently because the level differs: items within a type change price and cost together, and that appears as price and cost by type and as mix for Furniture as a whole. The cost effect is not a cost change.
- **Requirement (5).** A stated level with a reason. The Furniture level keeps cost at zero and mix at the item level, and the type level serves the assortment planners, labeled. A strong answer adds that a price effect is not by itself evidence of a price change.

A weak answer reads the cost effect as evidence of rising costs, or recommends a level without saying what each effect means at it.

## Common mistakes and how to respond

- **Volume by type.** *Symptom:* the check is nonzero and mix does not offset it. *Response:* ask which margin per unit values the change in total units.
- **The cost sign.** *Symptom:* the check is off by twice the cost effect. *Response:* ask what a higher cost per unit does to margin.
- **Grand totals in the table.** *Symptom:* a ninth row of the Furniture total is summed with the types. *Response:* ask what the sum of the sum is.
- **A pasted PivotTable with the filter off.** *Symptom:* quantities that differ from Tutorial 6.3's. *Response:* compare the totals with the Bridge.
- **The cost effect read as a finding.** *Symptom:* "costs fell". *Response:* ask whether any standard cost changed.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the PivotTable | 15 | Furniture, two quarters, three sums, read by GETPIVOTDATA or pasted | Totals wrong or filter missing |
| Requirement 2: per-unit measures | 20 | Price, cost and margin per unit and the Q3 share, correct | One measure missing |
| Requirement 3: the effects | 30 | Four effects as defined, check cell zero | Effects without the check |
| Requirement 4: the comparison | 20 | Side by side, the cost effect explained with an example | Comparison without the explanation |
| Requirement 5: the recommendation | 15 | A level and a reason | A level only |

## Extensions and discussion questions

- Repeat the bridge item by item. At that level each item has one standard cost, so the cost effect returns to zero. What does mix mean there?
- Add the promotional discount per unit to the type table and split the price effect into price lists and promotions, as in Tutorial 6.3.
- Discuss: a sales manager asks which type "lost the most price". Which bridge answers, and what would you caution?
- Discuss: Chapter 10 explains the manufacturing variance, which the standard-cost margin leaves out. Where would a real cost effect appear?
