# Requirement 4: Model the proposed 2027 calendar (Chapter 7)

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Item | Requirement 4 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 100 minutes |
| Solution file | PartII-case.zip: Charles River Promotion Case.xlsx, sheets R4 Model and R4 Budgets, with the Parameters sheet and the queries BilledLines, BudgetPrices and OrderLines |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 4 turns the evidence into a decision tool. Students extend Tutorial 7.3's contribution model from one promotion to the three the sales team proposes, find how much volume each would need to pay for itself, and compare that with what Requirement 3 measured. They then read the budgets to see what the 2027 plan assumes, and cost the proposal against it by quarter. The analytics types are predictive (a scenario model) and prescriptive (the basis for the recommendation).

By the end, students can:

- extend a contribution model to several scenarios with named inputs, one column each;
- compute a break-even lift by formula and confirm it with Goal Seek;
- map a result across two inputs with a data table and solve for a discount with Goal Seek;
- read a budget's planned prices and judge whether it plans promotions;
- estimate a cost by quarter and justify the volume it rests on.

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning and Performance (budgeting and forecasting, decision analysis); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** The Parameters sheet (Requirement 1), `BilledLines`, `BudgetPrices`, and the largest measured difference of Requirement 3 (the named cell `LargestLift` in the model answer). Tutorial 7.3 is the pattern, and its Steps 4 to 6 teach the techniques.
- **Data conditions.** The 2027 budget has one approver and one approval date and prices every month alike; the earlier budgets price the promoted items lower in their promotion months. BudgetLine has no customer dimension, and its volume is several times actual.
- **Two Excel traps.** A data table's input cells must be on the sheet that holds the table, so the model needs its own rate and lift cells (the proposal's rates live on Parameters). And Goal Seek leaves its changing cell at the value it found: Tutorial 7.3 cancels, the model answer records the result and resets the lift to zero.

## How to run it

Individual work, about 100 minutes: 30 on the model, 10 on the break-evens and Goal Seek, 15 on the data table, 10 on the second Goal Seek, 20 on the budgets, 15 on the cost and the volume basis. Hold back the input-cell hint until a student has an error. **Collect** the model sheet and the cost table; they feed Exhibit 4.

![A mock of the Furniture promotion's data table, with the positive cells highlighted.](../figures/case-part-2/IF-C2-4-A.pdf)

## Step-by-step solution

### Phase 1: One column for each proposed promotion

**Step 1. Build the model.** On `R4 Model`, put the three promotions in columns B to D. Rows: the promotion (the report year's promotion of that scope), the discount rate (linked to the Parameters name), the volume lift (blue, `0`), units, price before discount, standard cost per unit, fixed overhead in the standard cost, the commission rate, then the contribution without and with the promotion, the difference and the break-even lift. For the Furniture column:

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

**Step 2. Confirm each break-even with Goal Seek.** Choose **Data > What-If Analysis > Goal Seek**, enter the difference cell in **Set cell**, `0` in **To value** and the lift cell in **By changing cell**. Note the lift, then return the cell to zero: a lift left behind hides the cost of the discount. The found lift equals the formula's. Treating the fixed overhead in the standard cost as fixed lowers the Furniture break-even to 28.9%, as Tutorial 7.3 noted.

**Step 3. Set the measured differences beside the break-evens.** Compute each promotion's break-even from its own billed lines and look up Requirement 3's difference.

| Promotion | Break-even lift | Measured difference | Share of break-even |
|---|---:|---:|---:|
| 1 Alder | 23.6% | -3.3% | -14% |
| 2 Accessories | 24.8% | +11.9% | 48% |
| 3 Strategic | 39.7% | -20.7% | -52% |
| 4 Brookside | 26.2% | -15.4% | -59% |
| 5 Textiles | 26.2% | -5.8% | -22% |
| 6 Wholesale | 37.5% | +2.5% | 7% |
| 7 Harbor | 23.3% | +0.4% | 2% |
| 8 Furniture | 30.8% | +0.3% | 1% |
| 9 Design Trade | 34.2% | +3.1% | 9% |

The break-evens run from 23.3% to 39.7%, and no measured difference reached half of its own.

![Each promotion's measured difference against its break-even lift, for the discussion of requirement 4.](../figures/case-part-2/IF-C2-4-B.pdf)

### Phase 2: The data table and the second Goal Seek

**Step 4. Build the data table for the Furniture promotion.**

a. Beside the model, enter a discount-rate input cell (`0.1`) and a lift input cell (`0`) on the same sheet, and a result cell:

```
=$C$7*(1+C39)*($C$8*(1-C38)*(1-$C$11)-$C$9)-$C$13
```

b. Put the result cell's address in the grid's top-left corner, the rates 5, 8, 10 and 12 percent across, and the lifts 0 to 40 percent in steps of 5 points down.
c. Select the grid and choose **Data > What-If Analysis > Data Table**. Enter the rate cell as the **Row input cell** and the lift cell as the **Column input cell**.
d. Choose **Home > Conditional Formatting > New Rule** to shade the positive cells.

**Check:** the cell at a 5 percent discount and no increase is -$145,209.42. The difference first turns positive at a lift of 15% with a 5% discount; 25% with a 8% discount; 35% with a 10% discount; 40% with a 12% discount. **Watch for:** the two input cells swapped. The first row then shows gains, +$61,670.48 in its first cell, because a zero discount with an increase can only add contribution.

**Step 5. Solve for the Furniture discount at the best measured increase.** Choose **Data > What-If Analysis > Goal Seek**: set the difference at that increase (the cell that holds `LargestLift`) to `0` by changing the discount-rate input cell.

**Check:** the largest measured increase is +11.9% (promotion 2, Accessories), and the Furniture discount that it would just pay for is about 4.5%. At 5 percent the promotion needs a 13.3% increase instead of 30.8%. The discount is a ceiling, not a recommendation.

### Phase 3: The budgets and the cost of the calendar

**Step 6. Read how the budgets planned prices.** On `R4 Budgets`, for each fiscal year and month:

```
=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)/SUMIFS(BudgetPrices[ListAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)
```

Then the same ratio for the promoted items in their promotion months, with the collection or item-group column, the year and the first and last month as SUMIFS criteria.

**Check:** the promoted items are budgeted at 0.8806 of list in their promotion months, against 0.92 to 0.93 in their other months, and every item group is lower in November, the segment promotion's month. The 2027 budget, approved by Cynthia Reyes, the chief financial officer (EmployeeID 2), on 2026-12-15, is flat at 0.9277 of list in every month: it plans no promotion. **Watch for:** reading only the whole month's ratio, which moves from 0.9277 in January to 0.9237 in March because the promoted items are a small part of the budget.

**Step 7. Cost the calendar by quarter.** For each proposed promotion and quarter, multiply the proposed rate by the report year's gross amount (SUMIFS on `BilledLines` by PromotionID, year and InvoiceQuarter), total, round to hundreds, and multiply the total by one less the commission rate.

**Check:** $354,589.72 of discounts, $347,840.88 of contribution after the commissions saved, against a budget without promotions: about $7,600.00 in the first quarter, $22,500.00 in the second, $96,400.00 in the third and $228,100.00 in the fourth. **Watch for:** the rate applied to LineTotal, already net of the discount, which understates the cost by the rate itself.

**Step 8. State the volume basis.** The estimate uses the report year's billed lines at no increase, because Requirement 3 found none. It does not use the budget's quantities: the budget plans 17,580 Furniture units for September and October 2027 against 4,839 ordered in those months of 2026, 3.6 times as many, so a cost taken from it would be overstated almost fourfold. BudgetLine has no customer dimension, so the Design Trade promotion cannot be costed from it at all.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Break-even lift of the proposed promotions | 23.3%; 30.8%; 34.2% | 1 |
| Goal Seek discount at the best increase | 4.5% | 5 |
| Discounts of the calendar; contribution given up | $354,589.72; $347,840.88 | 7 |
| Budget quantity over quantity ordered, fall months | 3.6 | 8 |

> **Instructor notes, Requirement 4:** model inputs from the 2026 billed lines: Harbor (promotion 7) 569.21 units, price before discount 669.32, standard cost 378.46; Furniture (8) 4,823.89 units, 613.72, 346.36; Design Trade (9) 561.74 units, 416.23, 215.99. With CommissionRate 1.903%, the break-even increases are Harbor 23.3%, Furniture 30.8% (28.9% if fixed overhead is excluded from the standard cost, as in Tutorial 7.3), and Design Trade 34.2%; across all nine promotions they run from 23% to 40%. At a 5% Furniture discount the break-even increase is 13.3%. Goal Seek at promotion 2's +11.9% gives a Furniture discount of about 4.5%. Budgets (BudgetAmount / (Quantity x Item ListPrice) by month): the 2024-2026 budgets planned lower prices in the promotion months, 0.8806 of list for the promoted items (the year's collection in March-April, the year's item group in September-October), with every group lower in November. The 2027 budget, approved by the chief financial officer (EmployeeID 2) on 2026-12-15, is flat at about 0.9277 of list in every month. Cost at 2026 volumes, with no increase: discounts of 354,589.72, or 347,840.88 of contribution after the commission saved. The discounts land in Q1 about 7,600, Q2 22,500, Q3 96,400, and Q4 228,100 (Requirement 2). The budget's volume is several times actual (Chapter 7): it plans 17,580 Furniture units for September-October 2027 against 4,839 ordered in those months of 2026, so a cost taken from it would be overstated almost fourfold. BudgetLine has no customer dimension, so the Design Trade promotion cannot be costed from the budget at all.

## What a strong answer says

- **The model.** Three columns with stated assumptions, break-evens by formula and Goal Seek, and the fixed-overhead sensitivity.
- **The comparison.** Each measured difference far below its break-even, so none of the proposed promotions would pay for itself on the evidence.
- **The table and the discount.** Where each discount turns positive, and the Goal Seek discount as the most the best response on record would support.
- **The cost and its basis.** A cost by quarter from actual volumes, in contribution terms, with the lag explained and the budget's quantities rejected.

A weak answer treats the break-even as a forecast, or costs the calendar from the budget's volume.

## Common mistakes and how to respond

- **The break-even read as a prediction.** *Symptom:* "the promotion will lift volume by a third". *Response:* ask which measured difference supports that.
- **The wrong price.** *Symptom:* a Furniture break-even of 38.3%. *Response:* ask whether LineTotal is before or after the discount.
- **The lift left behind.** *Symptom:* the difference row reads about zero. *Response:* ask where Goal Seek left the lift cell.
- **The data table swapped or blocked.** *Symptom:* gains in the first row, or an error on the input cell. *Response:* check which input is the row and which the column, and which sheet each is on.
- **The budget's volume used.** *Symptom:* a cost several times the model's. *Response:* ask what volume the budget plans against what was ordered.
- **No commission.** *Symptom:* a contribution given up equal to the discount, $354,589.72. *Response:* ask what a lower price does to commissions.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| The model | 25 | Three columns, named inputs, correct formulas and sources | One column, or hard-coded inputs |
| Break-even and Goal Seek | 15 | Formula and Goal Seek agree, all promotions compared | Formula only |
| Data table | 15 | Correct grid, inputs right, positives shown | Grid with a swapped input |
| Discount from Goal Seek | 10 | Found and read as a ceiling | Found, not interpreted |
| Budgets | 15 | Ratios by month, promoted items, the plan year flat | Whole-month ratios only |
| Cost of the calendar | 15 | By quarter, in contribution terms | Total only |
| Volume basis | 5 | Stated, with why not the budget's | Not stated |

## Extensions and discussion questions

- Add a scenario in which half of the promotion's orders would have been lost without it, and find the lift at which it then pays for itself.
- Discuss: the model treats the whole standard cost as variable. Which promotions does that hurt most, and why?
- Discuss: a test at a small discount needs a comparison group. How would you choose one, and what would you do with the result?
