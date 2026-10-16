---
note: ch07.ex6
uses: [ch07.g6]
title: Evaluating Management's Forecast
kind: exercise
number: '7.6'
unit: '7'
perspective: auditing
tool: excel
minutes: 75
solution: "Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.6, with the queries DemandForecast, OrderLines and Employee"
figures:
  - id: IF-07-6-A
    kind: chart
    purpose: The forecast against orders by item group and year, which carries the finding of Requirement 3.
    shows: "A grouped bar chart. The horizontal axis holds the four product groups, each with three bars for the three years of the window; the vertical axis is the ratio of forecast units to ordered units, starting at zero, with a reference line at 1. The bars rise from the first year to the last in every group. A separate small panel shows the Services ratio on the same scale, below the line."
    data: The forecast-to-orders ratios of the Ex 7.6 sheet, rows for the four product groups and for Services (the Expected results).
---
{% set g = ch07_g6 %}
# Exercise 7.6: Evaluating Management's Forecast

{{ header() }}

## Purpose and learning outcomes

An auditor who tests an accounting estimate asks whether its assumptions are consistent with the company's experience. Here the assumption is the demand forecast, and the experience is the orders. Students compare the two by year and item group, set the budget beside them, and then look inside the forecast for the planner adjustments that no one approved. It is the auditor's version of a backtest, and it practices Power Query, SUMIFS by year, a ratio test and a control test. The analytics type is diagnostic.

By the end, students can:

- compare a forecast with historical experience by year and group and describe the bias (outcome 6);
- find the forecasts that departed from their baseline and identify the control the list tests (outcome 6);
- state the consequences of a biased forecast for estimates and plans, and the evidence to request (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Applied Forecasting, Predictive & Prescriptive Analytics, and Reporting and Control: Internal Control; IFAC IES 2 (f) and IES 4 (a); AACSB A5 parts 5.1 and 5.2.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, with the Item and SalesOrder queries of Chapter 5 and the InvoiceLines and BudgetLine Tables. The model answer uses FILTER and XLOOKUP, which every supported desktop Excel has.
- **Data conditions.** DemandForecast holds {{ rows|count }} rows, all in the current version ({{ version }}), with the methods {{ methods|join(", ") }}. The weeks run into {{ d.N }}, which have no orders to compare with. Services is forecast and ordered in hours of design work, and its forecast is the smaller of the two. Only the Planner Adjusted method has forecasts without an approver, {{ g.unapproved }} of {{ g.planner_adjusted|count }}.
- **Verify first.** A forecast that differs a little from its baseline is normal: {{ g.n_off|count }} rows do, by about ten percent at most, apart from the {{ g.n_big }} that students will find. A threshold of half of the baseline isolates them.

## How to run it

Individual, about 75 minutes: 15 for the forecast query and its totals (requirement 1), 15 for orders and the ratios (2), 5 for the description (3), 10 for the budget (4), 15 for the adjusted forecasts (5) and 15 for the memo (6). Hold back the 0.5 threshold until students have said what they would count as an unusual adjustment. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The forecast by year and group

**Step 1. Import the forecast.** Choose **Data > Get Data > From File > From Excel Workbook**, select T78_DemandForecast and click **Transform Data**. Name the query `DemandForecast`, keep the rows whose IsCurrent is 1, merge in ItemGroup from the Item query without the prefix, and add `Ratio` as `[ForecastQuantity] / [BaselineForecastQuantity]`, typed as a number.

**Step 2. Total by group and year.** On a worksheet named `Ex 7.6` put the years in B4:D4 and the five groups in A5:A9, then:

```
=SUMIFS(DemandForecast[ForecastQuantity],DemandForecast[ItemGroup],$A5,DemandForecast[ForecastWeekStartDate],">="&DATE(B$4,1,1),DemandForecast[ForecastWeekStartDate],"<"&DATE(B$4+1,1,1))
```

Row 10 sums the four product groups (rows 5 to 8) without Services.

**Check:** Furniture is forecast at {{ g.table[0].forecast[2]|num(0) }} units in {{ d.C }}, and the four product groups together at {{ years[2].forecast|num(1) }}.

### Requirement (2): Orders and the ratio

**Step 3. Import the orders.** Import T10_SalesOrderLine as `OrderLines`. Set Discount to **Decimal Number** with **Replace current**, because Power Query types it from its first 200 rows. Merge in OrderDate from the SalesOrder query and ItemGroup from the Item query, without the prefix.

**Step 4. Total and divide.** Repeat Step 2's SUMIFS on OrderLines[Quantity] by OrderDate in rows 14 to 19, and divide in rows 23 to 28: `=B5/B14`.

**Check:** the ratios are in the Expected results. **Watch for:** Services added to the product units, which pulls the total ratio down. Keep it in its own row.

### Requirement (3): The pattern

**Step 5. Describe it.** The forecast ran {{ years[0].ratio|num(2) }} times the orders in {{ years[0].year }}, {{ years[1].ratio|num(2) }} in {{ years[1].year }} and {{ years[2].ratio|num(2) }} in {{ years[2].year }}, more than twice in every product group and every year, and rising. The groups move together, so the bias is systematic. Services runs the other way: its forecast is {{ g.table[4].ratio|min|num(2) }} to {{ g.table[4].ratio|max|num(2) }} of the hours ordered.

{{ figure('IF-07-6-A') }}

### Requirement (4): The budget

**Step 6. Compare {{ d.C }}.** In B31 to H36 put, for each product group, the budget's quantity (`SUMIFS(BudgetLine[Quantity],BudgetLine[ItemGroup],$A32,BudgetLine[BudgetCategory],"Revenue")`), the forecast, the orders and the invoiced units, and the three ratios.

**Check:** the budget plans {{ budget|num(0) }} units, more than the forecast ({{ years[2].forecast|num(0) }}), and {{ (budget / years[2].orders)|num(1) }} times the {{ years[2].orders|num(0) }} units ordered ({{ invoiced|num(0) }} invoiced).

### Requirement (5): The adjusted forecasts

**Step 7. List the forecasts adjusted by more than half.**

a. Import T74_Employee as `Employee`, keeping EmployeeID, EmployeeName and JobTitle.
b. List the forecasts whose ratio differs from 1 by more than 0.5, and look up their item, warehouse, method, planner and approver:

```
=FILTER(DemandForecast[DemandForecastID],ABS(DemandForecast[Ratio]-1)>0.5)
=XLOOKUP(A46#,DemandForecast[DemandForecastID],DemandForecast[ApprovedByEmployeeID])
```

c. Look up the planners in Employee. For the approver, replace a looked-up 0 with a blank and then with `(none)`: a blank ApprovedByEmployeeID comes back from the lookup as 0.

**Check:** {{ adjusted|length }} forecasts:{% for r in adjusted %} DemandForecastID {{ r.id }} ({{ r.date }}, {{ r.forecast|num(2) }} against {{ r.baseline|num(2) }}){% if not loop.last %};{% endif %}{% endfor %}. All are for {{ code }} ({{ name }}, {{ group }}) at warehouse {{ warehouse_id }}, {{ warehouse }}, {{ method }}, {{ multiple|num(1) }} times the baseline, by {{ planner }} (employee {{ planner_id }}), a {{ title }}, with no approver. Every other forecast is between {{ low|num(2) }} and {{ high|num(2) }} times its baseline. **Watch for:** an approver column that shows employee 0 or "(not found)". It means the lookup read a blank as 0.

The control tested is the approval of planners' adjustments. The three are the only unapproved forecasts in the Table, so every other adjustment has an approver recorded. That shows the step was taken, not how well it was done.

### Requirement (6): The memo

**Step 8. Write it.** An outline: not consistent with experience, with the ratios; the consequences; what the adjusted forecasts show about the review; the evidence and explanations to request.

## Expected results

| Group | Forecast / orders, {{ years[0].year }} | {{ years[1].year }} | {{ years[2].year }} |
|---|---:|---:|---:|
{% for r in g.table %}
| {{ r.group }} | {{ r.ratio[0]|num(2) }} | {{ r.ratio[1]|num(2) }} | {{ r.ratio[2]|num(2) }} |
{% endfor %}
| Four product groups | {{ years[0].ratio|num(2) }} | {{ years[1].ratio|num(2) }} | {{ years[2].ratio|num(2) }} |

| Quantity | Value | Step |
|---|---:|---|
| {{ d.C }} units: budget; forecast; orders; invoiced (four product groups) | {{ budget|num(0) }}; {{ years[2].forecast|num(0) }}; {{ years[2].orders|num(0) }}; {{ invoiced|num(0) }} | 6 |
| Forecasts adjusted by more than half; forecasts with no approver | {{ adjusted|length }}; {{ g.unapproved }} | 7 |
| Planner; job title; purchase orders created | {{ planner }}; {{ title }}; {{ pos|count }} | 7 |

{{ expected() }}

## What a strong answer says

- **Requirement (3).** Not consistent: more than twice the orders in every product group and year, and the bias grows. Services runs the other way and needs its own explanation.
- **Requirement (5).** The list tests the approval of planner adjustments. The three are small in quantity but are an unapproved override by a buyer who plans most forecasts ({{ g.planner_adjusted|count }} Planner Adjusted rows in all) and also creates purchase orders. It is an authorization exception, and the buyer's two roles make an independent review more important.
- **Requirement (6).** Consequences whose direction depends on the estimate: plans that buy and build too much, a reserve understated if it relies on the forecast, and a budget that shows the gap from the plan but is a poor measure of performance. Services is assessed separately. The evidence to request: the method and its inputs, the comparisons management made, the reasons for the three overrides, how the forecast feeds the plans, and inventory levels and aging.

A weak answer says the forecast is "high" without the ratios, or treats a recorded approval as proof of a review.

## Common mistakes and how to respond

- **Services added to the units.** *Symptom:* a total ratio below the group ratios. *Cause:* hours added to units. *Response:* ask what a Services quantity measures.
- **Year taken from the wrong date.** *Symptom:* totals that do not match the model answer. *Response:* ask which date places a forecast in a year.
- **The first weeks of {{ d.N }} compared with orders.** *Symptom:* a ratio with a zero denominator. *Response:* ask what orders exist for those weeks.
- **A blank approver read as 0.** *Symptom:* an employee 0 in the list. *Response:* ask what a blank number becomes in a lookup.
- **Recorded approval as proof.** *Symptom:* "every other change was approved, so the process works". *Response:* ask what an approval field can and cannot show.
- **A conclusion without evidence.** *Symptom:* "management is biased". *Response:* ask what you would request to find out why.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: forecast totals | 15 | Current version, ItemGroup merged, totals by year | Year from the wrong date |
| Requirement 2: orders and ratios | 15 | Orders by year, ratios, Services apart | Services added |
| Requirement 3: description | 10 | Direction, growth and difference among groups | Direction only |
| Requirement 4: budget | 10 | Budget, forecast and orders compared | One missing |
| Requirement 5: adjusted forecasts | 25 | The list, planner, approver, the control named | Control unnamed |
| Requirement 6: memo | 25 | Verdict, consequences, review finding, evidence | No evidence requested |

## Extensions and discussion questions

- Compute the ratio for each item, not each group. Is the bias spread evenly, or do a few items carry it?
- Value the units forecast above orders at standard cost. How large is the exposure for a reserve?
- Discuss: Exercise 7.1 backtests your own forecast and this exercise tests management's. What is the same, and what must the auditor add?
- Discuss: the budget's volume is higher than the forecast. Whose assumption is it, and what does Tutorial 7.2 say it is worth?
