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
    shows: "A horizontal bar chart with a row for each promotion, the measured difference as a bar and the break-even lift as a marker to its right, the proposed promotions marked, and at the right the share of its break-even that each difference reaches."
    data: The break-even lift and the measured difference of each promotion (R4 Model, second block).
---
{% set x = case2_g4 %}
# Requirement 4: Model the proposed 2027 calendar (Chapter 7)

{{ header() }}

## Purpose and learning outcomes

Requirement 4 turns the evidence into a decision tool. Students extend Tutorial 7.3's contribution model to the three proposed promotions, compare each break-even with what Requirement 3 measured, read what the {{ x.plan_year }} budget assumes and cost the proposal by quarter. The analytics types are predictive (a scenario model) and prescriptive (the basis for the recommendation).

By the end, students can:

- build a contribution model with named inputs, one column for each scenario;
- find a break-even lift by formula and confirm it with Goal Seek;
- map a result across two inputs with a data table and solve for a discount;
- judge from a budget's planned prices whether it plans promotions;
- estimate a cost by quarter and justify its volume basis.

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning and Performance (budgeting and forecasting, decision analysis); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** The Parameters sheet, `BilledLines`, `BudgetPrices`, and Requirement 3's largest difference (`LargestLift`). Tutorial 7.3 is the pattern.
- **Data conditions.** The earlier budgets price the promoted items lower in their promotion months, while the {{ x.plan_year }} budget is nearly flat across the months. BudgetLine has no customer dimension, and its volume is several times actual.
- **Two Excel traps.** A data table's input cells must be on the sheet that holds the table, so the model needs its own rate and lift cells. Goal Seek leaves its changing cell at the value it found, so record the result and restore the input.

## How to run it

Individual work, about 100 minutes: 40 on the model and break-evens, 25 on the table and the second Goal Seek, 35 on the budgets and the cost. **Collect** the model sheet and the cost table; they feed Exhibit 4.

{{ figure('IF-C2-4-A') }}

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
{% for c in x.cols %}
| {{ c.label }} ({{ c.rate|pct(0) }}) | {{ c.units|num(2) }} | ${{ c.price|money }} | ${{ c.cost|money }} | -${{ (c.diff|abs)|money }} | {{ c.be|pct(1) }} |
{% endfor %}

With the commission rate of {{ x.c|pct(3) }}, the three differences add to -${{ contribution|money }}. **Watch for:** the price before discount taken as LineTotal over units. That is the price after the discount, and the Furniture break-even reads {{ x.fur.be_net_price|pct(1) }} instead of {{ x.fur.be|pct(1) }}.

**Step 2. Confirm each break-even with Goal Seek.** Choose **Data > What-If Analysis > Goal Seek**, enter the difference cell in **Set cell**, `0` in **To value** and the lift cell in **By changing cell**. Note the lift and return the cell to zero, since a lift left behind makes the difference read about zero. The lift found equals the formula's. Treating the fixed overhead in the standard cost as fixed lowers the Furniture break-even to {{ x.fur.be_fixed|pct(1) }}, as Tutorial 7.3 noted.

**Step 3. Set the measured differences beside the break-evens.** The requirement asks for the three proposed promotions. The model answer also shows the other six, as corroboration.

| Promotion | Break-even lift | Measured difference |
|---|---:|---:|
{% for n in x.nine %}
| {{ n.id }} {{ n.label }} | {{ n.be|pct(1) }} | {{ n.lift|spct }} |
{% endfor %}

The break-evens run from {{ be_low|pct(1) }} to {{ be_high|pct(1) }}, and no measured difference reached half of its own.

{{ figure('IF-C2-4-B') }}

### Phase 2: The data table and the second Goal Seek

**Step 4. Build the data table for the Furniture promotion.**

a. Below the nine-promotion block, enter a discount-rate input cell in C{{ x.rows.rate }} (`0.1`), a lift input cell in C{{ x.rows.lift }} (`0`) and the result in C{{ x.rows.diff }}, all on the model's own sheet:

```jinja
=$C$7*(1+C{{ x.rows.lift }})*($C$8*(1-C{{ x.rows.rate }})*(1-$C$11)-$C$9)-$C$13
```

b. Put `=C{{ x.rows.diff }}` in B{{ x.rows.top }}, the rates 5, 8, 10 and 12 percent in C{{ x.rows.top }}:F{{ x.rows.top }} and the lifts 0 to 40 percent in steps of 5 points in B{{ x.rows.first }}:B{{ x.rows.last }}.
c. Select B{{ x.rows.top }}:F{{ x.rows.last }} and choose **Data > What-If Analysis > Data Table**. Enter C{{ x.rows.rate }} as the **Row input cell** and C{{ x.rows.lift }} as the **Column input cell**.
d. Choose **Home > Conditional Formatting > New Rule** to shade the positive cells.

**Check:** the cell at a 5 percent discount and no increase is -${{ (x.corner|abs)|money }}. The difference first turns positive at a lift of {% for p in x.positives %}{{ p.lift|pct(0) }} when the discount is {{ p.rate|pct(0) }}{% if not loop.last %}; {% endif %}{% endfor %}. **Watch for:** the input cells swapped. The first row then shows gains, +${{ x.swap|money }} in its first cell, because a zero discount with an increase only adds contribution.

**Step 5. Solve for the Furniture discount at the best measured increase.** Keep the observed increase fixed and let the discount move. In the next block enter the increase, a starting discount and the dependent difference:

```jinja
C{{ x.rows.big }}:  =LargestLift
C{{ x.rows.disc }}:  0.10
C{{ x.rows.gdiff }}:  =$C$7*(1+C{{ x.rows.big }})*($C$8*(1-C{{ x.rows.disc }})*(1-$C$11)-$C$9)-$C$13
```

Choose **Data > What-If Analysis > Goal Seek**, set C{{ x.rows.gdiff }} to `0` by changing C{{ x.rows.disc }}, and record the result. Do not set `LargestLift` itself to zero: it does not depend on the discount. Restore any temporary inputs afterward.

**Check:** the largest measured increase is {{ best.lift|spct }} (promotion {{ best.id }}, {{ best.label }}), and the Furniture discount that it would just pay for is about {{ discount|pct(4) }}, a result that depends on that observation. At 5 percent the promotion needs a {{ grp.be5|pct(1) }} increase instead of {{ x.fur.be|pct(1) }}. The discount is a sensitivity, not a recommendation.{% if x.cross %} The increase was measured for another scope and year ({{ x.best_year }}) and is an observed difference, not an effect of a promotion. Furniture's own difference of {{ x.own_lift|spct }} would support {% if x.own_discount > 0 %}a discount of only about {{ x.own_discount|pct(2) }}{% else %}no discount{% endif %}.{% endif %}


### Phase 3: The budgets and the cost of the calendar

**Step 6. Read how the budgets planned prices.** On `R4 Budgets`, for each fiscal year and month:

```
=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)/SUMIFS(BudgetPrices[ListAmount],BudgetPrices[FiscalYear],$A5,BudgetPrices[Month],B$4)
```

Then the same ratio for the promoted items in their promotion months.

**Check:** the promoted items are budgeted at {{ promoted|num(4) }} of list in their promotion months, against {{ x.promoted_low|num(2) }} to {{ x.promoted_high|num(2) }} in their other months, and every item group is lower in November, the segment promotion's month. The {{ x.plan_year }} budget, approved by {{ x.cfo_name }}, the chief financial officer (EmployeeID {{ cfo }}), on {{ approved }}, is approximately flat, between {{ x.plan_low|num(4) }} and {{ x.plan_high|num(4) }} of list across the months, with no promotion-month price reductions. The ratio is not exactly flat, and {{ x.n_two_prices }} Furniture items also carry two planned unit prices in the plan year. **Watch for:** the whole month's ratio alone, which in {{ x.year }} moves only from {{ x.whole_jan|num(4) }} in January to {{ x.whole_march|num(4) }} in March, because the promoted items are a small part of the budget.

**Step 7. Cost the calendar by quarter.** For each proposed promotion and quarter, multiply the proposed rate by the report year's gross billed amount (SUMIFS on `BilledLines` by PromotionID, year and InvoiceQuarter) at full precision. Sum those amounts, then multiply the unrounded total by one less the commission rate. Round only what is displayed, and show the discounts and the contribution given up in separate columns. Do not round the discount to hundreds before the commission step.

**Check:** ${{ cost|money }} of discounts and ${{ contribution|money }} of contribution after the commissions saved, against a budget without promotions. Rounding the annual discount to hundreds first gives about ${{ x.contrib_rounded_first|money }}, and a typed commission of {{ x.typed_rate|pct(3) }} about ${{ x.contrib_typed|money }}. Both are legitimate under a stated policy, which sets the tolerance. By quarter the discounts are about ${{ quarters[0][1]|num }}, ${{ quarters[1][1]|num }}, ${{ quarters[2][1]|num }} and ${{ quarters[3][1]|num }}, and the contribution given up is {% for q, v in x.contrib_quarters %}${{ v|money }}{% if not loop.last %}, {% endif %}{% endfor %}. That pattern is historical billed volume at the report year's mix, prices, costs and billing, neither a budget-price bridge nor a forecast. The estimate leaves out ${{ x.unbilled_total|money }} of discount on the proposal's report-year orders not yet billed in the data ({% for u in x.unbilled %}{{ u.label }} ${{ u.amount|money }}{% if not loop.last %}, {% endif %}{% endfor %}). **Watch for:** the rate applied to LineTotal, already net of the discount, which understates the cost by the rate itself.

**Step 8. State the volume basis.** The estimate uses the report year's billed lines at no increase, because Requirement 3 found no increase near any break-even. It does not use the budget's quantities: the budget plans {{ budget_units|num(0) }} Furniture units for September and October {{ x.plan_year }} against {{ ordered|num(0) }} ordered in those months of {{ x.year }}, {{ x.budget_over|num(1) }} times as many. Budget quantities imply a substantially larger scenario, and they do not establish actual {{ x.plan_year }} demand. BudgetLine has no customer dimension, so the Design Trade promotion cannot be isolated directly without an explicit allocation or a customer-mix assumption.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Break-even lift of the proposed promotions | {% for c in x.cols %}{{ c.be|pct(1) }}{% if not loop.last %}; {% endif %}{% endfor %} | 1 |
| Goal Seek discount at the best increase | {{ discount|pct(1) }} | 5 |
| Discounts of the calendar; contribution given up | ${{ cost|money }}; ${{ contribution|money }} | 7 |
| Budget quantity over quantity ordered, fall months | {{ x.budget_over|num(1) }} | 8 |

{{ expected() }}

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
