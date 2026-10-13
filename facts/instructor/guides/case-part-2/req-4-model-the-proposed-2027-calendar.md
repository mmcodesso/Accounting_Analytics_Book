---
note: case2.r4
uses: [case2.g4]
title: Model the proposed 2027 calendar (Chapter 7)
kind: requirement
number: '4'
unit: case2
perspective: managerial
tool: excel
minutes: 100
solution: "PartII-case.zip: Charles River Promotion Case.xlsx, sheets R4 Model and R4 Budgets, with the Parameters sheet and the queries BilledLines, BudgetPrices and OrderLines"
figures:
  - id: IF-C2-4-A
    kind: excel-mock
    purpose: The Furniture promotion's data table, with the positive cells highlighted.
    shows: "A grid of the difference in contribution, discounts of 5, 8, 10 and 12 percent across and lifts of 0 to 40 percent in steps of 5 points down, with the positive cells shaded in a staircase and a row of break-even lifts beneath. The two input cells and the result cell sit above it."
    data: The Furniture promotion's units, price before discount, standard cost and the commission rate (the Expected results).
  - id: IF-C2-4-B
    kind: chart
    purpose: Each promotion's measured difference against its break-even lift, for the discussion of requirement 4.
    shows: "A horizontal bar chart with a row for each promotion, the measured difference as a bar and the break-even lift as a marker to its right, the proposed promotions marked."
    data: The break-even lift and the measured difference of each promotion (R4 Model, second block).
---
{% set x = case2_g4 %}
# Requirement 4: Model the proposed 2027 calendar (Chapter 7)

{{ header() }}

## Purpose and learning outcomes

Requirement 4 turns the evidence into a decision tool. Students extend Tutorial 7.3's contribution model from one promotion to the three the sales team proposes, find how much volume each would need to pay for itself, and compare that with what Requirement 3 measured. They then read the budgets to see what the {{ x.plan_year }} plan assumes, and cost the proposal against it by quarter. The analytics types are predictive (a scenario model) and prescriptive (the basis for the recommendation).

By the end, students can:

- extend a contribution model to several scenarios with named inputs, one column each;
- compute a break-even lift by formula and confirm it with Goal Seek;
- map a result across two inputs with a data table and solve for a discount with Goal Seek;
- read a budget's planned prices and judge whether it plans promotions;
- estimate a cost by quarter and justify the volume it rests on.

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning and Performance (budgeting and forecasting, decision analysis); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** The Parameters sheet (Requirement 1), `BilledLines`, `BudgetPrices`, and the largest measured difference of Requirement 3 (the named cell `LargestLift` in the model answer). Tutorial 7.3 is the pattern, and its Steps 4 to 6 teach the techniques.
- **Data conditions.** The {{ x.plan_year }} budget has one approver and one approval date and prices every month alike; the earlier budgets price the promoted items lower in their promotion months. BudgetLine has no customer dimension, and its volume is several times actual.
- **Two Excel traps.** A data table's input cells must be on the sheet that holds the table, so the model needs its own rate and lift cells (the proposal's rates live on Parameters). And Goal Seek leaves its changing cell at the value it found: Tutorial 7.3 cancels, the model answer records the result and resets the lift to zero.

## How to run it

Individual work, about 100 minutes: 30 on the model, 10 on the break-evens and Goal Seek, 15 on the data table, 10 on the second Goal Seek, 20 on the budgets, 15 on the cost and the volume basis. Hold back the input-cell hint until a student has an error. **Collect** the model sheet and the cost table; they feed Exhibit 4.

{{ figure('IF-C2-4-A') }}

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
{% for c in x.cols %}
| {{ c.label }} ({{ c.rate|pct(0) }}) | {{ c.units|num(2) }} | ${{ c.price|money }} | ${{ c.cost|money }} | -${{ (c.diff|abs)|money }} | {{ c.be|pct(1) }} |
{% endfor %}

With the commission rate of {{ x.c|pct(3) }}, the three differences add to -${{ contribution|money }}. **Watch for:** the price before discount taken as LineTotal over units. That is the price after the discount, and the Furniture break-even reads {{ x.fur.be_net_price|pct(1) }} instead of {{ x.fur.be|pct(1) }}.

**Step 2. Confirm each break-even with Goal Seek.** Choose **Data > What-If Analysis > Goal Seek**, enter the difference cell in **Set cell**, `0` in **To value** and the lift cell in **By changing cell**. Note the lift, then return the cell to zero: a lift left behind hides the cost of the discount. The found lift equals the formula's. Treating the fixed overhead in the standard cost as fixed lowers the Furniture break-even to {{ x.fur.be_fixed|pct(1) }}, as Tutorial 7.3 noted.

**Step 3. Set the measured differences beside the break-evens.** Compute each promotion's break-even from its own billed lines and look up Requirement 3's difference.

| Promotion | Break-even lift | Measured difference | Share of break-even |
|---|---:|---:|---:|
{% for n in x.nine %}
| {{ n.id }} {{ n.label }} | {{ n.be|pct(1) }} | {{ n.lift|spct }} | {{ n.share|pct(0) }} |
{% endfor %}

The break-evens run from {{ be_low|pct(1) }} to {{ be_high|pct(1) }}, and no measured difference reached half of its own.

{{ figure('IF-C2-4-B') }}

### Phase 2: The data table and the second Goal Seek

**Step 4. Build the data table for the Furniture promotion.**

a. Beside the model, enter a discount-rate input cell (`0.1`) and a lift input cell (`0`) on the same sheet, and a result cell:

```jinja
=$C$7*(1+C{{ x.rows.lift }})*($C$8*(1-C{{ x.rows.rate }})*(1-$C$11)-$C$9)-$C$13
```

b. Put the result cell's address in the grid's top-left corner, the rates 5, 8, 10 and 12 percent across, and the lifts 0 to 40 percent in steps of 5 points down.
c. Select the grid and choose **Data > What-If Analysis > Data Table**. Enter the rate cell as the **Row input cell** and the lift cell as the **Column input cell**.
d. Choose **Home > Conditional Formatting > New Rule** to shade the positive cells.

**Check:** the cell at a 5 percent discount and no increase is -${{ (x.corner|abs)|money }}. The difference first turns positive at a lift of {% for p in x.positives %}{{ p.lift|pct(0) }} with a {{ p.rate|pct(0) }} discount{% if not loop.last %}; {% endif %}{% endfor %}. **Watch for:** the two input cells swapped. The first row then shows gains, +${{ x.swap|money }} in its first cell, because a zero discount with an increase can only add contribution.

**Step 5. Solve for the Furniture discount at the best measured increase.** Choose **Data > What-If Analysis > Goal Seek**: set the difference at that increase (the cell that holds `LargestLift`) to `0` by changing the discount-rate input cell.

**Check:** the largest measured increase is {{ best.lift|spct }} (promotion {{ best.id }}, {{ best.label }}), and the Furniture discount that it would just pay for is about {{ discount|pct(1) }}. At 5 percent the promotion needs a {{ grp.be5|pct(1) }} increase instead of {{ x.fur.be|pct(1) }}. The discount is a ceiling, not a recommendation.

### Phase 3: The budgets and the cost of the calendar

**Step 6. Read how the budgets planned prices.** On `R4 Budgets`, for each fiscal year and month:

```
=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)/SUMIFS(BudgetPrices[ListAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)
```

Then the same ratio for the promoted items in their promotion months, with the collection or item-group column, the year and the first and last month as SUMIFS criteria.

**Check:** the promoted items are budgeted at {{ promoted|num(4) }} of list in their promotion months, against {{ x.promoted_low|num(2) }} to {{ x.promoted_high|num(2) }} in their other months, and every item group is lower in November, the segment promotion's month. The {{ x.plan_year }} budget, approved by {{ x.cfo_name }}, the chief financial officer (EmployeeID {{ cfo }}), on {{ approved }}, is flat at {{ flat|num(4) }} of list in every month: it plans no promotion. **Watch for:** reading only the whole month's ratio, which moves from {{ x.whole_jan|num(4) }} in January to {{ x.whole_march|num(4) }} in March because the promoted items are a small part of the budget.

**Step 7. Cost the calendar by quarter.** For each proposed promotion and quarter, multiply the proposed rate by the report year's gross amount (SUMIFS on `BilledLines` by PromotionID, year and InvoiceQuarter), total, round to hundreds, and multiply the total by one less the commission rate.

**Check:** ${{ cost|money }} of discounts, ${{ contribution|money }} of contribution after the commissions saved, against a budget without promotions: about ${{ quarters[0][1]|money }} in the first quarter, ${{ quarters[1][1]|money }} in the second, ${{ quarters[2][1]|money }} in the third and ${{ quarters[3][1]|money }} in the fourth. **Watch for:** the rate applied to LineTotal, already net of the discount, which understates the cost by the rate itself.

**Step 8. State the volume basis.** The estimate uses the report year's billed lines at no increase, because Requirement 3 found none. It does not use the budget's quantities: the budget plans {{ budget_units|num(0) }} Furniture units for September and October {{ x.plan_year }} against {{ ordered|num(0) }} ordered in those months of {{ x.year }}, {{ x.budget_over|num(1) }} times as many, so a cost taken from it would be overstated almost fourfold. BudgetLine has no customer dimension, so the Design Trade promotion cannot be costed from it at all.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Break-even lift of the proposed promotions | {% for c in x.cols %}{{ c.be|pct(1) }}{% if not loop.last %}; {% endif %}{% endfor %} | 1 |
| Goal Seek discount at the best increase | {{ discount|pct(1) }} | 5 |
| Discounts of the calendar; contribution given up | ${{ cost|money }}; ${{ contribution|money }} | 7 |
| Budget quantity over quantity ordered, fall months | {{ x.budget_over|num(1) }} | 8 |

{{ expected() }}

## What a strong answer says

- **The model.** Three columns with stated assumptions, break-evens by formula and Goal Seek, and the fixed-overhead sensitivity.
- **The comparison.** Each measured difference far below its break-even, so none of the proposed promotions would pay for itself on the evidence.
- **The table and the discount.** Where each discount turns positive, and the Goal Seek discount as the most the best response on record would support.
- **The cost and its basis.** A cost by quarter from actual volumes, in contribution terms, with the lag explained and the budget's quantities rejected.

A weak answer treats the break-even as a forecast, or costs the calendar from the budget's volume.

## Common mistakes and how to respond

- **The break-even read as a prediction.** *Symptom:* "the promotion will lift volume by a third". *Response:* ask which measured difference supports that.
- **The wrong price.** *Symptom:* a Furniture break-even of {{ x.fur.be_net_price|pct(1) }}. *Response:* ask whether LineTotal is before or after the discount.
- **The lift left behind.** *Symptom:* the difference row reads about zero. *Response:* ask where Goal Seek left the lift cell.
- **The data table swapped or blocked.** *Symptom:* gains in the first row, or an error on the input cell. *Response:* check which input is the row and which the column, and which sheet each is on.
- **The budget's volume used.** *Symptom:* a cost several times the model's. *Response:* ask what volume the budget plans against what was ordered.
- **No commission.** *Symptom:* a contribution given up equal to the discount, ${{ cost|money }}. *Response:* ask what a lower price does to commissions.

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
