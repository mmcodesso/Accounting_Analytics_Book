---
note: ch07.ex4
uses: [ch07.g4]
title: The Product Mix under a Capacity Constraint
kind: exercise
number: '7.4'
unit: '7'
perspective: managerial
tool: excel
minutes: 120
solution: "Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheets Ex 7.4, Ex 7.4 Answer Report and Ex 7.4 Sensitivity Report (the Solver model is saved with the Ex 7.4 sheet)"
figures:
  - id: IF-07-4-A
    kind: chart
    purpose: Why Solver cuts the items it cuts, ranked by contribution per Assembly hour against the shadow price.
    shows: "A bar chart of the manufactured items sold, sorted by contribution per Assembly hour from the highest to the lowest, one thin bar each. A horizontal line marks the shadow price of an Assembly hour. The bars below the line are shaded coral and labeled as the items Solver reduces, the one bar on the line is the item made in part, and the vertical axis starts at zero."
    data: The contribution per Assembly hour of each item (the column beside the routing hours of the Ex 7.4 sheet) and the shadow price of the Sensitivity report.
---
{% set g = ch07_g4 %}
# Exercise 7.4: The Product Mix under a Capacity Constraint

{{ header() }}

## Purpose and learning outcomes

Tutorial 7.3 asked what one decision is worth. This exercise asks which products to make when a resource runs short, the question Solver is built for. Students set up a linear program from routings and calendars, solve it, and read the Sensitivity report as a manager would: which center binds, what an extra hour is worth and for how many hours. The analytics type is prescriptive. The constraint is a hypothesis, as the exercise says, and not a description of the data.

By the end, students can:

- set up decision variables, an objective and constraints from tables of routings and capacity (outcome 5);
- solve the model with Simplex LP and report its Answer and Sensitivity results (outcome 5);
- interpret a shadow price and its range, and name the model's limits in a recommendation (outcome 5).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models) and BAR M10 (advanced data analytics); IMA Applied Forecasting, Predictive & Prescriptive Analytics, and Decision Analysis; IFAC IES 2 (b) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, including the CommissionRate name of Tutorial 7.3, and the Solver add-in loaded and checked on every machine. The model answer saves its Solver model with the worksheet: **Data > Solver** opens it ready to solve.
- **Data conditions.** {{ g.manufactured }} items are manufactured, {{ g.n_items }} of them sold in {{ d.C }} and {{ unsold }} not; every one sold has a routing. The routings give run hours for {{ g.n_centers }} work centers. In {{ d.C }} the plant used well under its capacity, so half of the hours is an assumption.
- **Verify first.** Solve it yourself. The model has {{ g.n_items }} variable cells and {{ g.n_constraints }} constraints counting the demand limits, and solves instantly. The Answer and Sensitivity reports in the solution file were written in Solver's layout by the builder, not by Solver, so your own reports will differ in names and formatting but not in numbers.

## How to run it

Individual or pairs, about 120 minutes: 25 for the imports and the item list (requirement 1), 25 for contribution and hours (2), 15 for the model (3), 20 for Solver (4), 15 for reading the results (5) and 20 for the recommendation. Hold back the SUMPRODUCT formula for the hours used until students ask how to total hours across items, and hold back the instruction not to require whole numbers until a student adds it. Collect the workbook, both reports and the recommendation.

## Step-by-step solution

### Requirement (1): The data and the items

**Step 1. Import the four Tables.** Choose **Data > Get Data > From File > From Excel Workbook** and select T44_Item, T50_RoutingOperation, T47_WorkCenter and T48_WorkCenterCalendar. For T44_Item, **Transform Data**, name the query `ItemRouting` and keep ItemID, ItemCode, ItemGroup, StandardCost, StandardFixedOverheadCost, SupplyMode and RoutingID. Name the others `RoutingOperation`, `WorkCenter` and `WorkCenterCalendar`.

**Step 2. List the manufactured items sold.** On a worksheet named `Ex 7.4` enter the year in B2, and in A21 the list of items:

```
=SORT(FILTER(ItemRouting[ItemID],(ItemRouting[SupplyMode]="Manufactured")*(SUMIFS(InvoiceLines[Quantity],InvoiceLines[ItemID],ItemRouting[ItemID],InvoiceLines[FiscalYear],$B$2)>0)))
```

**Check:** {{ g.n_items }} items, of which {{ groups[0][1] }} {{ groups[0][0] }}, {{ groups[1][1] }} {{ groups[1][0] }} and {{ groups[2][1] }} {{ groups[2][0] }}; {{ unsold }} manufactured items had no sales.

### Requirement (2): Demand, contribution and hours

**Step 3. Build the item table in rows {{ g.first_row }} to {{ g.last_row }}.**

a. Demand (column E): the units sold in the year by SUMIFS on InvoiceLines.
b. Average price (F): revenue divided by demand. Variable standard cost (G): StandardCost less StandardFixedOverheadCost.
c. Contribution per unit (H): `=F21#-G21#-$B$3*F21#`, with B3 `=CommissionRate`.
d. Hours per unit at each work center (columns J to N, headed by the transposed center names): SUMIFS of StandardRunHoursPerUnit by routing and center.

```
=SUMIFS(RoutingOperation[StandardRunHoursPerUnit],RoutingOperation[RoutingID],D21#,RoutingOperation[WorkCenterID],J19#)
```

**Check:** the commission rate is {{ rate|pct(3) }}. **Watch for:** a contribution that keeps the fixed overhead in the standard cost, or leaves out the commission. Both change the objective and the items Solver cuts.

### Requirement (3): The model

**Step 4. Capacity and hours.**

a. In C11:C15 total each work center's available hours in the year from WorkCenterCalendar with SUMIFS on the center and a date range, and in D11 `=C11#/2`.
b. Fill I21:I103 with the demand as a starting plan.
c. Hours to meet all demand (E) and hours used (G) for each center: `=SUMPRODUCT(J$21:J$103,$E$21:$E$103)` and `=SUMPRODUCT(J$21:J$103,$I$21:$I$103)`. Slack is `=D11-G11`.
d. In B4 the objective: `=SUMPRODUCT(H21:H103,I21:I103)`.

**Check:** hours to meet all demand against half of capacity:{% for c, n in need %} {{ c }} {{ n|pct(0) }}{% if not loop.last %};{% endif %}{% endfor %}. The contribution if all demand were met is ${{ full|money }}. **Watch for:** capacity left at the full hours. Nothing then binds and the loss is zero.

### Requirement (4): Solver

**Step 5. Solve.**

a. Choose **Data > Solver**. Name B4 as the objective to maximize and I21:I103 as the variable cells.
b. Add two constraints: G11:G15 less than or equal to D11:D15, and I21:I103 less than or equal to E21:E103.
c. Check **Make Unconstrained Variables Non-Negative**, choose the Simplex LP method, and do not require whole units.
d. Click **Solve**, choose **Keep Solver Solution**, and select **Answer** and **Sensitivity** under the reports.

**Check:** a total contribution of ${{ optimum|money }}, ${{ loss|money }} less than ${{ full|money }}. **Watch for:** an integer constraint, which removes the Sensitivity report, and a missing demand limit, which lets Solver make more than customers bought.

### Requirement (5): Reading the answer

**Step 6. Read the Answer report.** {{ g.binding }} uses all of its {{ bind_cap|num(0) }} hours. {{ g.next_center }} ends at {{ fin_used|num(0) }} of {{ fin_cap|num(0) }} hours and would bind next. The plan makes {{ g.n_whole }} items in full and reduces {{ g.n_reduced }}:{% for code, q, dm in reduced %} {{ code }} ({{ q|num(1) }} of {{ dm|num(1) }} units){% if not loop.last %};{% endif %}{% endfor %}.

**Step 7. Read the Sensitivity report.** In the Constraints block, the Assembly row shows a shadow price of ${{ shadow|money }}, with an allowable increase of {{ g.allowed_up|num(0) }} hours and a decrease of {{ g.allowed_down|num(0) }}: the value holds for capacity from {{ g.range_low|num(0) }} to {{ g.range_high|num(0) }} hours. It equals the contribution per Assembly hour of {{ g.part_code }}, the one item made in part ({{ g.part_qty|num(1) }} of {{ g.part_demand|num(1) }}).

{{ figure('IF-07-4-A') }}

**Step 8. Write the recommendation.** An outline: which center binds and by how much; the plan and the items cut, with the reason (the lowest contribution per Assembly hour, not per unit); the shadow price and its range; what to do with it; the limits.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Manufactured items sold; not sold | {{ sold }}; {{ unsold }} | 2 |
| Commission rate | {{ rate|pct(3) }} | 3 |
| Contribution if all demand were met | ${{ full|money }} | 4 |
| Contribution at the optimum; lost | ${{ optimum|money }}; ${{ loss|money }} | 5 |
{% for c in g.centers %}
| {{ c.name }}: capacity; hours used; status | {{ c.capacity|num(0) }}; {{ c.used|num(0) }}; {{ c.status }} | 4, 6 |
{% endfor %}
| Shadow price of {{ g.binding }}; allowable increase; decrease | ${{ shadow|money }}; {{ g.allowed_up|num(1) }}; {{ g.allowed_down|num(1) }} | 7 |
| Items reduced; made only in part | {{ g.n_reduced }}; {{ g.part_code }} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirement (5).** {{ g.binding }} is the only center that binds, though {{ g.next_center }} is close. The plan cuts the items that earn the least for each Assembly hour, which are not always the items with the smallest unit margin: {{ g.swap|join(' and ') }} earn less per unit than some items that are cut, and are made in full because they use less Assembly time. The shadow price is the most an extra Assembly hour is worth, and only over the range the report gives.
- **The recommendation.** Protect Assembly hours in the upgrade schedule, give priority to the items with the highest contribution per Assembly hour, price overtime or outsourcing against the shadow price, and talk to sales about the reduced items. It names the limits: demand and prices fixed, fractional units allowed, run hours exact, and setup hours ignored. With setup hours spread over each item's average lot, the contribution lost rises to about ${{ setup_loss|num(0) }}.

A weak answer lists the quantities without saying which resource drives them, reads the shadow price as a price per item, or applies it beyond its range.

## Common mistakes and how to respond

- **Full capacity.** *Symptom:* no center binds and the loss is zero. *Response:* ask what the exercise does to the hours.
- **Fixed overhead in the unit cost.** *Symptom:* an objective below the model answer's, with the same items cut. *Response:* ask which costs change when a unit is not made.
- **Whole units required.** *Symptom:* no Sensitivity report. *Response:* ask what the chapter says the report needs.
- **No demand limit.** *Symptom:* quantities above demand. *Response:* ask who will buy them.
- **Mismatched SUMPRODUCT ranges.** *Symptom:* #VALUE!. *Response:* ask whether both ranges have the same size.
- **Shadow price misread.** *Symptom:* "an item is worth this much". *Response:* ask for the unit of a shadow price.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: imports and items | 15 | Four queries, the list of items sold | A query missing |
| Requirement 2: contribution and hours | 20 | Contribution with variable cost and commission, hours by center | Fixed overhead kept |
| Requirement 3: the model | 15 | Capacity at half, SUMPRODUCT hours and objective | Capacity wrong |
| Requirement 4: Solver | 20 | Maximize, both constraints, Simplex LP, no integers, both reports | A constraint missing |
| Requirement 5: reading | 15 | Binding center, shadow price and range, items cut, loss | Shadow price without range |
| Recommendation | 15 | Action, reasons, limits | Limits missing |

## Extensions and discussion questions

- Raise Assembly capacity by a hundred hours and solve again. Does the objective rise by the shadow price times a hundred?
- Spread setup hours over each item's average lot and solve again. Does the same center bind?
- Discuss: the plan makes most items in full and cuts a handful. Which of those would you test with customers first?
- Discuss: Chapter 18 asks which products to make or buy. What do the shadow price and the relevant cost have in common?
