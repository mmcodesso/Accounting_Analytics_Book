# Requirement 4: Model the proposed 2027 calendar (Chapter 7)

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Item | Requirement 4 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 100 minutes |
| Solution file | PartII-case.zip: Charles River Promotion Case.xlsx, sheets R4 Model and R4 Budgets, with the Parameters sheet and the queries BilledLines, BudgetPrices and OrderLines |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 4 turns the evidence into a decision tool. Students extend Tutorial 7.3's contribution model to the three proposed promotions, compare each break-even with what Requirement 3 measured, read what the 2027 budget assumes and cost the proposal by quarter. The analytics types are predictive (a scenario model) and prescriptive (the basis for the recommendation).

By the end, students can:

- build a contribution model with named inputs, one column for each scenario;
- find a break-even lift by formula and confirm it with Goal Seek;
- map a result across two inputs with a data table and solve for a discount;
- judge from a budget's planned prices whether it plans promotions;
- estimate a cost by quarter and justify its volume basis.

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning and Performance (budgeting and forecasting, decision analysis); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** The Parameters sheet, `BilledLines`, `BudgetPrices`, and Requirement 3's largest difference (`LargestLift`). Tutorial 7.3 is the pattern.
- **Data conditions.** The earlier budgets price the promoted items lower in their promotion months, while the 2027 budget is nearly flat across the months. BudgetLine has no customer dimension, and its volume is several times actual.
- **Two Excel traps.** A data table's input cells must be on the sheet that holds the table, so the model needs its own rate and lift cells. Goal Seek leaves its changing cell at the value it found, so record the result and restore the input.

## How to run it

Individual work, about 100 minutes: 40 on the model and break-evens, 25 on the table and the second Goal Seek, 35 on the budgets and the cost. **Collect** the model sheet and the cost table; they feed Exhibit 4.

![A mock of the Furniture promotion's data table, with the positive cells highlighted.](../figures/case-part-2/IF-C2-4-A.pdf)

## Step-by-step solution

### Phase 1: One column for each proposed promotion

**Step 1. Build the model.** The cell addresses are one reference layout, and a student may arrange the sheet differently. On `R4 Model`, put Harbor, Furniture and Design Trade in columns B to D. Row 4 holds each promotion's PromotionID (the report year's promotion of that scope, from Parameters), row 5 its rate (linked to the Parameters name) and row 6 the volume lift (blue, `0`). Rows 7 to 11 hold units, price before discount, standard cost per unit, fixed overhead in the standard cost and the commission rate, and rows 13 to 16 the contribution without and with the promotion, the difference and the break-even lift. Row 17 repeats the break-even with the fixed overhead treated as fixed (`Items[StandardFixedOverheadCost]`), and row 18 holds Step 2's Goal Seek result. For the Furniture column:

```
Units:               =SUMIFS(BilledLines[Quantity],BilledLines[PromotionID],C$4,BilledLines[InvoiceYear],ReportYear)
Price before:        =SUMIFS(BilledLines[GrossAmount],BilledLines[PromotionID],C$4,BilledLines[InvoiceYear],ReportYear)/C7
Standard cost:       =SUMPRODUCT((BilledLines[PromotionID]=C$4)*(BilledLines[InvoiceYear]=ReportYear)*BilledLines[Quantity]*BilledLines[StandardCost])/C7
Without promotion:   =C7*(C8*(1-C11)-C9)
With promotion:      =C7*(1+C6)*(C8*(1-C5)*(1-C11)-C9)
Difference:          =C14-C13
Break-even lift:     =(C8*(1-C11)-C9)/(C8*(1-C5)*(1-C11)-C9)-1
```

**Check:**

| Promotion | Units | Price before discount | Standard cost | Difference at no increase | Break-even lift |
|---|---:|---:|---:|---:|---:|
| Harbor (8%) | 569.21 | $669.32 | $378.46 | -$29,898.47 | 23.3% |
| Furniture (10%) | 4,823.89 | $613.72 | $346.36 | -$290,418.85 | 30.8% |
| Design Trade (12%) | 561.74 | $416.23 | $215.99 | -$27,523.56 | 34.2% |

With the commission rate of 1.903%, the three differences add to -$347,840.88. **Watch for:** the price before discount taken as LineTotal over units. That is the price after the discount, and the Furniture break-even reads 38.3% instead of 30.8%.

**Step 2. Confirm each break-even with Goal Seek.** Choose **Data > What-If Analysis > Goal Seek**, enter the difference cell in **Set cell**, `0` in **To value** and the lift cell in **By changing cell**. Note the lift and return the cell to zero, since a lift left behind makes the difference read about zero. The lift found equals the formula's. Treating the fixed overhead in the standard cost as fixed lowers the Furniture break-even to 28.9%, as Tutorial 7.3 noted.

**Step 3. Set the measured differences beside the break-evens.** The requirement asks for the three proposed promotions. The model answer also shows the other six, as corroboration.

| Promotion | Break-even lift | Measured difference |
|---|---:|---:|
| 1 Alder | 23.6% | -3.3% |
| 2 Accessories | 24.8% | +11.9% |
| 3 Strategic | 39.7% | -20.7% |
| 4 Brookside | 26.2% | -15.4% |
| 5 Textiles | 26.2% | -5.8% |
| 6 Wholesale | 37.5% | +2.5% |
| 7 Harbor | 23.3% | +0.4% |
| 8 Furniture | 30.8% | +0.3% |
| 9 Design Trade | 34.2% | +3.1% |

The break-evens run from 23.3% to 39.7%, and no measured difference reached half of its own.

![Each promotion's measured difference against its break-even lift, for the discussion of requirement 4.](../figures/case-part-2/IF-C2-4-B.pdf)

### Phase 2: The data table and the second Goal Seek

**Step 4. Build the data table for the Furniture promotion.**

a. Below the nine-promotion block, enter a discount-rate input cell in C38 (`0.1`), a lift input cell in C39 (`0`) and the result in C40, all on the model's own sheet:

```
=$C$7*(1+C39)*($C$8*(1-C38)*(1-$C$11)-$C$9)-$C$13
```

b. Put `=C40` in B42, the rates 5, 8, 10 and 12 percent in C42:F42 and the lifts 0 to 40 percent in steps of 5 points in B43:B51.
c. Select B42:F51 and choose **Data > What-If Analysis > Data Table**. Enter C38 as the **Row input cell** and C39 as the **Column input cell**.
d. Choose **Home > Conditional Formatting > New Rule** to shade the positive cells.

**Check:** the cell at a 5 percent discount and no increase is -$145,209.42. The difference first turns positive at a lift of 15% when the discount is 5%; 25% when the discount is 8%; 35% when the discount is 10%; 40% when the discount is 12%. **Watch for:** the input cells swapped. The first row then shows gains, +$61,670.48 in its first cell, because a zero discount with an increase only adds contribution.

**Step 5. Solve for the Furniture discount at the best measured increase.** Keep the observed increase fixed and let the discount move. In the next block enter the increase, a starting discount and the dependent difference:

```
C56:  =LargestLift
C57:  0.10
C58:  =$C$7*(1+C56)*($C$8*(1-C57)*(1-$C$11)-$C$9)-$C$13
```

Choose **Data > What-If Analysis > Goal Seek**, set C58 to `0` by changing C57, and record the result. Do not set `LargestLift` itself to zero: it does not depend on the discount. Restore any temporary inputs afterward.

**Check:** the largest measured increase is +11.9% (promotion 2, Accessories), and the Furniture discount that it would just pay for is about 4.5183%, a result that depends on that observation. At 5 percent the promotion needs a 13.3% increase instead of 30.8%. The discount is a sensitivity, not a recommendation. The increase was measured for another scope and year (2024) and is an observed difference, not an effect of a promotion. Furniture's own difference of +0.3% would support a discount of only about 0.15%.

### Phase 3: The budgets and the cost of the calendar

**Step 6. Read how the budgets planned prices.** On `R4 Budgets`, for each fiscal year and month:

```
=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)/SUMIFS(BudgetPrices[ListAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)
```

Then the same ratio for the promoted items in their promotion months.

**Check:** the promoted items are budgeted at 0.8806 of list in their promotion months, against 0.92 to 0.93 in their other months, and every item group is lower in November, the segment promotion's month. The 2027 budget, approved by Cynthia Reyes, the chief financial officer (EmployeeID 2), on 2026-12-15, is approximately flat, between 0.9277 and 0.9279 of list across the months, with no promotion-month price reductions. The ratio is not exactly flat, and six Furniture items also carry two planned unit prices in the plan year. **Watch for:** the whole month's ratio alone, which in 2026 moves only from 0.9277 in January to 0.9237 in March, because the promoted items are a small part of the budget.

**Step 7. Cost the calendar by quarter.** For each proposed promotion and quarter, multiply the proposed rate by the report year's gross billed amount (SUMIFS on `BilledLines` by PromotionID, year and InvoiceQuarter) at full precision. Sum those amounts, then multiply the unrounded total by one less the commission rate. Round only what is displayed, and show the discounts and the contribution given up in separate columns. Do not round the discount to hundreds before the commission step.

**Check:** $354,589.72 of discounts and $347,840.88 of contribution after the commissions saved, against a budget without promotions. Rounding the annual discount to hundreds first gives about $347,850.97, and a typed commission of 1.903% about $347,841.87. Both are legitimate under a stated policy, which sets the tolerance. By quarter the discounts are about $7,600, $22,500, $96,400 and $228,100, and the contribution given up is $7,452.40, $22,096.11, $94,519.84, $223,772.53. That pattern is historical billed volume at the report year's mix, prices, costs and billing, neither a budget-price bridge nor a forecast. The estimate leaves out $5,625.76 of discount on the proposal's report-year orders not yet billed in the data (Furniture $891.18, Design Trade $4,734.58). **Watch for:** the rate applied to LineTotal, already net of the discount, which understates the cost by the rate itself.

**Step 8. State the volume basis.** The estimate uses the report year's billed lines at no increase, because Requirement 3 found no increase near any break-even. It does not use the budget's quantities: the budget plans 17,580 Furniture units for September and October 2027 against 4,839 ordered in those months of 2026, 3.6 times as many. Budget quantities imply a substantially larger scenario, and they do not establish actual 2027 demand. BudgetLine has no customer dimension, so the Design Trade promotion cannot be isolated directly without an explicit allocation or a customer-mix assumption.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Break-even lift of the proposed promotions | 23.3%; 30.8%; 34.2% | 1 |
| Goal Seek discount at the best increase | 4.5% | 5 |
| Discounts of the calendar; contribution given up | $354,589.72; $347,840.88 | 7 |
| Budget quantity over quantity ordered, fall months | 3.6 | 8 |

> **Instructor notes, Requirement 4:** the model reads each proposal promotion's 2026 billed lines (the units, price before discount and standard cost of Harbor, Furniture and Design Trade). With CommissionRate 1.903%, the break-even increases are Harbor 23.3%, Furniture 30.8% (28.9% if fixed overhead is excluded from the standard cost, as in Tutorial 7.3), and Design Trade 34.2%; across all nine promotions they run from 23% to 40%. At a 5% Furniture discount the break-even increase is 13.3%. Goal Seek at promotion 2's +11.9% gives a Furniture discount of about 4.5%, a cross-scope sensitivity, because that difference was measured for the Accessories promotion of 2024 and is an observed difference, not a measured effect. The Furniture promotion's own +0.3% would support about 0.15%. Budgets: the 2024-2026 budgets planned lower prices in the promotion months (0.8806 of list for the promoted items), and the 2027 budget, approved by the chief financial officer (EmployeeID 2) on 2026-12-15, is approximately flat, from 0.9277 to 0.9279 of list across the months, with no promotion-month price reductions. At 2026 billed volumes and with no increase, a sensitivity that holds the 2026 volume, mix, prices and costs, the calendar gives discounts of 354,589.72, or 347,840.88 of contribution after the commission saved, computed at full precision and rounded only for display. It leaves out 5,625.76 of discount on the proposal's orders not yet billed in the data (Furniture 891.18, Design Trade 4,734.58), whose billing dates are unknown. The budget plans 17,580 Furniture units for September-October 2027 against 4,839 ordered in those months of 2026, several times as many, so its quantities imply a substantially larger scenario without establishing actual 2027 demand. BudgetLine has no customer dimension, so the Design Trade promotion cannot be isolated from the budget without an allocation or a customer-mix assumption.

## What a strong answer says

- **The model and the table.** Three columns with stated assumptions, break-evens by formula and Goal Seek, the fixed-overhead sensitivity, and where each discount turns positive.
- **The comparison.** Each measured difference far below its break-even, so no proposed promotion is shown to pay for itself, and the Goal Seek discount labeled a cross-scope sensitivity.
- **The cost and its basis.** A cost by quarter in contribution terms from actual volumes, with the lag, the fixed mix and the unbilled orders disclosed, and the budget's quantities rejected.

A weak answer treats the break-even as a forecast, or costs the calendar from the budget's volume.

## Common mistakes and how to respond

- **The break-even read as a prediction.** *Symptom:* "the promotion will lift volume by a third". *Response:* ask what measured difference supports that.
- **The data table swapped or blocked.** *Symptom:* gains in the first row, or an error on the input cell. *Response:* check the row and column inputs and the sheet each is on.
- **The Goal Seek discount recommended, or aimed at the wrong cell.** *Symptom:* "run the promotion at that rate", or a Set cell that is `LargestLift`. *Response:* ask whose increase the rate rests on, and which cell depends on the discount.
- **The budget's volume used.** *Symptom:* a cost several times the model's. *Response:* ask what volume the budget plans against what was ordered.
- **No commission.** *Symptom:* a contribution given up equal to the discount. *Response:* ask what a lower price does to commissions.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| The model | 25 | Three columns, named inputs, correct formulas and sources | One column, or hard-coded inputs |
| Break-even and Goal Seek | 15 | Formula and Goal Seek agree, each beside its measured difference | Formula only |
| Data table | 15 | Correct grid, inputs right, positives shown | Grid with a swapped input |
| Discount from Goal Seek | 10 | Found and labeled a sensitivity | Found, not interpreted |
| Budgets | 15 | Ratios by month, promoted items, the plan year approximately flat | Whole-month ratios only |
| Cost of the calendar | 15 | By quarter, in contribution terms, at full precision | Total only |
| Volume basis | 5 | Stated, with why not the budget's | Not stated |

## Extensions and discussion questions

- Add a scenario in which half of the promotion's orders would have been lost without it, and find the lift at which it then pays for itself.
- Discuss: the model treats the whole standard cost as variable. Which promotions does that hurt most, and why?
