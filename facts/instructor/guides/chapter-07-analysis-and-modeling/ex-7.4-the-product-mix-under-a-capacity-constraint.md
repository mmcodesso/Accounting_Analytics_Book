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

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, including the CommissionRate name of Tutorial 7.3, and the Solver add-in loaded and checked on every machine. The model answer saves its Solver model with the worksheet: **Data > Solver** opens it ready to solve. Its list of reduced items uses HSTACK, which needs a newer Excel than the tutorials do, as the chapter note says.
- **Data conditions.** {{ g.manufactured }} items are manufactured, {{ g.n_items }} of them sold in {{ d.C }} and {{ unsold }} not; every one sold has a routing. The routings give run hours for {{ g.n_centers }} work centers. In {{ d.C }} the plant used well under its capacity, so half of the hours is an assumption.
- **Verify first.** Solve it yourself. The model has {{ g.n_items }} variable cells and {{ g.n_constraints }} constraints counting the demand limits, and solves instantly. The Answer and Sensitivity reports in the solution file were written in Solver's layout by the builder, not by Solver, so your own reports will differ in names and formatting but not in numbers.

## How to run it

Individual or pairs, about 120 minutes: 25 for the imports and the item list (requirement 1), 25 for contribution and hours (2), 15 for the model (3), 20 for Solver (4), 15 for reading the results (5) and 20 for the recommendation. Hold back the SUMPRODUCT formula for the hours used until students ask how to total hours across items, and hold back the instruction not to require whole numbers until a student adds it. Collect the workbook, both reports and the recommendation.

## Step-by-step solution

### Requirement (1): The data and the items

**Step 1. Import the four Tables.** Choose **Data > Get Data > From File > From Excel Workbook** and select T44_Item, T50_RoutingOperation, T47_WorkCenter and T48_WorkCenterCalendar. For T44_Item, **Transform Data**, name the query `ItemRouting` and keep ItemID, ItemCode, ItemGroup, StandardCost, StandardFixedOverheadCost, SupplyMode and RoutingID. Name the others `RoutingOperation`, `WorkCenter` and `WorkCenterCalendar`. Load all four to worksheet Tables named after their queries (**Close & Load To**, **Table**), because the worksheet formulas read them as Tables.

**Step 2. List the manufactured items sold.** On a worksheet named `Ex 7.4` set B2 to {{ d.C }} and B3 to `=CommissionRate`. In A20:I20 type `ItemID`, `ItemCode`, `ItemGroup`, `RoutingID`, `Demand`, `Average price`, `Variable standard cost`, `Contribution per unit` and `Quantity`. Enter the item list in A21, and leave every cell that a spill will fill, here and below, empty:

```
=SORT(FILTER(ItemRouting[ItemID],(ItemRouting[SupplyMode]="Manufactured")*(SUMIFS(InvoiceLines[Quantity],InvoiceLines[ItemID],ItemRouting[ItemID],InvoiceLines[FiscalYear],$B$2)>0)))
```

**Check:** {{ g.n_items }} items, of which {{ groups[0][1] }} {{ groups[0][0] }}, {{ groups[1][1] }} {{ groups[1][0] }} and {{ groups[2][1] }} {{ groups[2][0] }}; {{ unsold }} manufactured items had no sales.

### Requirement (2): Demand, contribution and hours

**Step 3. Build the work centers and the item table in rows {{ g.first_row }} to {{ g.last_row }}.** The work-center block comes first, because the hours matrix needs its IDs. Every formula goes in its one named cell, and the line breaks below are only for reading.

a. In A10:H10 type `WorkCenterID`, `Work center`, `Available hours`, `Capacity (half)`, `Hours to meet all demand`, `Demand / capacity`, `Hours used (SUMPRODUCT)` and `Slack`, then enter these formulas, each of which spills over the five centers:

```
A11  =SORT(WorkCenter[WorkCenterID])
B11  =XLOOKUP(A11#,WorkCenter[WorkCenterID],WorkCenter[WorkCenterName])
C11  =SUMIFS(WorkCenterCalendar[AvailableHours],
         WorkCenterCalendar[WorkCenterID],A11#,
         WorkCenterCalendar[CalendarDate],">="&DATE($B$2,1,1),
         WorkCenterCalendar[CalendarDate],"<"&DATE($B$2+1,1,1))
D11  =C11#/2
```

b. In the item table, units sold by SUMIFS on InvoiceLines (demand), the average price as revenue over demand, the variable standard cost as StandardCost less StandardFixedOverheadCost, and the contribution per unit:

```
B21  =XLOOKUP(A21#,ItemRouting[ItemID],ItemRouting[ItemCode])
C21  =XLOOKUP(A21#,ItemRouting[ItemID],ItemRouting[ItemGroup])
D21  =XLOOKUP(A21#,ItemRouting[ItemID],ItemRouting[RoutingID])
E21  =SUMIFS(InvoiceLines[Quantity],InvoiceLines[ItemID],A21#,
         InvoiceLines[FiscalYear],$B$2)
F21  =SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemID],A21#,
         InvoiceLines[FiscalYear],$B$2)/E21#
G21  =XLOOKUP(A21#,ItemRouting[ItemID],
         ItemRouting[StandardCost]-ItemRouting[StandardFixedOverheadCost])
H21  =F21#-G21#-$B$3*F21#
```

c. Hours per unit at each work center, in columns J to N. Row 19 holds the numeric work center IDs, because SUMIFS matches RoutingOperation[WorkCenterID], and row 20 the names for reading:

```
J19  =TRANSPOSE(A11#)
J20  =TRANSPOSE(B11#)
J21  =SUMIFS(RoutingOperation[StandardRunHoursPerUnit],
         RoutingOperation[RoutingID],D21#,
         RoutingOperation[WorkCenterID],J19#)
```

d. Copy E21:E{{ g.last_row }} and choose **Paste Special > Values** into I21:I{{ g.last_row }}. These are Solver's {{ g.n_items }} changing cells, so they must hold typed values and not a spill linked to demand.

**Check:** the commission rate is {{ rate|pct(3) }}, the work-center block has {{ g.n_centers }} rows, and the hours matrix is {{ g.n_items }} items by {{ g.n_centers }} centers. **Watch for:** a contribution that keeps the fixed overhead in the standard cost, or leaves out the commission. Both change the objective (${{ g.alt_fixed.objective|money }} with the fixed overhead kept and ${{ g.alt_commission.objective|money }} without the commission, against the model answer's) and the shadow price (${{ g.alt_fixed.shadow|money }} and ${{ g.alt_commission.shadow|money }}). In this dataset neither changes the quantities, so the same {{ g.n_reduced }} items are cut. The cost definition still matters, because a different demand mix or capacity pattern could change the plan.

### Requirement (3): The model

**Step 4. Hours used, slack and the objective.**

a. The capacity is in D11 from Step 3, and the starting plan is in I21:I{{ g.last_row }}.
b. In E11 and G11 enter the hours to meet all demand and the hours used for the first center, which uses matrix column J:

```jinja
E11  =SUMPRODUCT(J$21:J${{ g.last_row }},$E$21:$E${{ g.last_row }})
G11  =SUMPRODUCT(J$21:J${{ g.last_row }},$I$21:$I${{ g.last_row }})
```

c. For the centers in rows 12 to 15 use the matrix columns {{ g.centers_letters[1:]|join(', ') }} in place of J, keeping rows 21 to {{ g.last_row }}. A straight fill downward would keep column J in every row and give every center the first center's hours.
d. In F11 enter `=E11/D11` and in H11 `=D11-G11`, and fill both down through row 15. In B4 enter the objective: `=SUMPRODUCT(H21:H{{ g.last_row }},I21:I{{ g.last_row }})`.

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

**Step 7. Read the Sensitivity report.** In the Constraints block, the Assembly row shows a shadow price of ${{ shadow|money }}, with an allowable increase of {{ g.allowed_up|num(0) }} hours and a decrease of {{ g.allowed_down|num(0) }}: the value holds for capacity from {{ g.range_low|num(0) }} to {{ g.range_high|num(0) }} hours. It equals the contribution per Assembly hour of {{ g.part_code }}, the one item made in part ({{ g.part_qty|num(1) }} of {{ g.part_demand|num(1) }}). The allowable increase and decrease describe a change in Assembly's capacity alone, with every other input held. At the top of the range the item made in part reaches its demand, and at the bottom its quantity reaches zero, so another item takes its place and the shadow price changes. Neither end is another work center starting to bind. After a larger change, or a change in another input at the same time, solve again.

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
- **The recommendation.** Protect Assembly hours in the upgrade schedule, give priority to the items with the highest contribution per Assembly hour, price overtime or outsourcing against the shadow price, and talk to sales about the reduced items.
- **A plus.** The limits: demand and prices fixed, fractional units allowed, run hours exact, and setup hours ignored. With setup hours spread over each item's average lot, the contribution lost rises to about ${{ setup_loss|num(0) }}.

A weak answer lists the quantities without saying which resource drives them, reads the shadow price as a price per item, or applies it beyond its range.

## Common mistakes and how to respond

- **Full capacity.** *Symptom:* no center binds and the loss is zero. *Response:* ask what the exercise does to the hours.
- **Fixed overhead in the unit cost.** *Symptom:* an objective below the model answer's, with the same items cut. *Response:* ask which costs change when a unit is not made.
- **Whole units required.** *Symptom:* no Sensitivity report. *Response:* ask what the chapter says the report needs.
- **No demand limit.** *Symptom:* quantities above demand. *Response:* ask who will buy them.
- **Mismatched SUMPRODUCT ranges.** *Symptom:* #VALUE!. *Response:* ask whether both ranges have the same size.
- **A fill-down of the hours formulas.** *Symptom:* the same hours at every center. *Response:* ask which matrix column each center needs.
- **Shadow price misread.** *Symptom:* "an item is worth this much". *Response:* ask for the unit of a shadow price.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: imports and items | 15 | Four queries, the list of items sold | A query missing |
| Requirement 2: contribution and hours | 20 | Contribution with variable cost and commission, hours by center | Fixed overhead kept |
| Requirement 3: the model | 15 | Capacity at half, SUMPRODUCT hours and objective | Capacity wrong |
| Requirement 4: Solver | 20 | Maximize, both constraints, Simplex LP, no integers, both reports | A constraint missing |
| Requirement 5: reading | 15 | Binding center, shadow price and range, items cut, loss | Shadow price without range |
| Recommendation | 15 | Action and the reasons from the results | No reasons |

## Extensions and discussion questions

- Raise Assembly capacity by a hundred hours and solve again. Does the objective rise by the shadow price times a hundred?
- Spread setup hours over each item's average lot and solve again. Does the same center bind?
- Discuss: the plan makes most items in full and cuts a handful. Which of those would you test with customers first?
- Discuss: Chapter 18 asks which products to make or buy. What do the shadow price and the relevant cost have in common?
