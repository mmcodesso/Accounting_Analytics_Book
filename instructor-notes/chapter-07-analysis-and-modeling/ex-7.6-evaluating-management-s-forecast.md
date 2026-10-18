# Exercise 7.6: Evaluating Management's Forecast

| | |
|---|---|
| Unit | Chapter 7: Forecasting, Budgeting, and What-If Analysis in Excel |
| Item | Exercise 7.6 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.6, with the queries DemandForecast, OrderLines and Employee |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

An auditor who tests an accounting estimate asks whether its assumptions are consistent with the company's experience. Here the assumption is the demand forecast, and the experience is the orders. Students compare the two by year and item group, set the budget beside them, and then look inside the forecast for the planner adjustments that no one approved. It is a retrospective consistency comparison of the stored, current forecast with historical orders. Before it counts as a backtest of an ex ante forecast, the auditor would need frozen forecasts or a version history that shows what was available before each forecast period, because IsCurrent and an approval date alone do not show that the stored quantities were unchanged afterward. The exercise practices Power Query, SUMIFS by year, a ratio test and a control test. The analytics type is diagnostic.

By the end, students can:

- compare a forecast with historical experience by year and group and describe the bias (outcome 6);
- find the forecasts that departed from their baseline and identify the control the list tests (outcome 6);
- state the consequences of a biased forecast for estimates and plans, and the evidence to request (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Applied Forecasting, Predictive & Prescriptive Analytics, and Reporting and Control: Internal Control; IFAC IES 2 (f) and IES 4 (a); AACSB A5 parts 5.1 and 5.2.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, with the Item and SalesOrder queries of Chapter 5 and the InvoiceLines and BudgetLine Tables. The model answer uses FILTER and XLOOKUP, which every supported desktop Excel has.
- **Data conditions.** DemandForecast holds 66,496 rows, all in the current version (Current Weekly Plan), with the methods Seasonal Trend, Planner Adjusted, Lifecycle Adjusted. The weeks run into 2027, which have no orders to compare with. Services is forecast and ordered in hours of design work, and its forecast is the smaller of the two. Only the Planner Adjusted method has forecasts without an approver, 3 of 5,405.
- **Verify first.** A forecast that differs a little from its baseline is normal: 65,912 rows do, by about ten percent at most, apart from the 3 that students will find. A threshold of half of the baseline isolates them.

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

**Check:** Furniture is forecast at 83,764 units in 2026, and the four product groups together at 218,920.6.

### Requirement (2): Orders and the ratio

**Step 3. Import the orders.** Import T10_SalesOrderLine as `OrderLines`. Set Discount to **Decimal Number** with **Replace current**, because Power Query types it from its first 200 rows. Merge in OrderDate from the SalesOrder query and ItemGroup from the Item query, without the prefix.

**Step 4. Total and divide.** Repeat Step 2's SUMIFS on OrderLines[Quantity] by OrderDate in rows 14 to 19, and divide in rows 23 to 28: `=B5/B14`.

**Check:** the ratios are in the Expected results. **Watch for:** Services added to the product units, which pulls the total ratio down. Keep it in its own row.

### Requirement (3): The pattern

**Step 5. Describe it.** The forecast ran 2.33 times the orders in 2024, 2.57 in 2025 and 2.88 in 2026, more than twice in every product group and every year, and rising. The groups move together, so the bias is systematic. Services runs the other way: its forecast is 0.28 to 0.31 of the hours ordered.

![The forecast against orders by item group and year, which carries the finding of Requirement 3.](../figures/chapter-07-analysis-and-modeling/IF-07-6-A.pdf)

### Requirement (4): The budget

**Step 6. Compare 2026.** In B31 to H36 put, for each product group, the budget's quantity, the forecast, the orders and the invoiced units, and the three ratios. The budget's quantity is:

```
=SUMIFS(BudgetLine[Quantity],BudgetLine[ItemGroup],$A32,BudgetLine[BudgetCategory],"Revenue")
```

**Check:** the budget plans 264,494 units, more than the forecast (218,921), and 3.5 times the 76,023 units ordered (76,089 invoiced).

### Requirement (5): The adjusted forecasts

**Step 7. List the forecasts adjusted by more than half.**

a. Import T74_Employee as `Employee`, keeping EmployeeID, EmployeeName and JobTitle.
b. List the forecasts whose ratio differs from 1 by more than 0.5, and look up their item, warehouse, method, planner and approver:

```
=FILTER(DemandForecast[DemandForecastID],ABS(DemandForecast[Ratio]-1)>0.5)
=XLOOKUP(A46#,DemandForecast[DemandForecastID],DemandForecast[ApprovedByEmployeeID])
```

c. Look up the planners in Employee. For the approver, replace a looked-up 0 with a blank and then with `(none)`: a blank ApprovedByEmployeeID comes back from the lookup as 0.
d. Count the blank approvals independently of the size filter, and list those rows. The model answer keeps the count in B40:

   ```
   =COUNTBLANK(DemandForecast[ApprovedByEmployeeID])
   ```

   Expect 3, the same forecasts as the size filter. A smaller unapproved adjustment in a later release would still be an approval exception even if it failed the size filter, so the filter alone is not the test of the control. A zero or missing baseline would make the ratio an error and is a separate exception.

**Check:** 3 forecasts: DemandForecastID 1 (2024-01-01, 23.78 against 7.67); DemandForecastID 107 (2025-01-06, 28.15 against 9.08); DemandForecastID 211 (2026-01-05, 28.06 against 9.05). All are for ACC-MIR-0001 (Foundry Mirror Glass Soft White, Accessories) at warehouse 1, Planner Adjusted, 3.1 times the baseline, by Michelle Garcia (employee 90), a Buyer, with no approver. The warehouse's name, East Distribution Center, needs a lookup in Warehouse, which the exercise does not import. Every other forecast is between 0.92 and 1.10 times its baseline. **Watch for:** an approver column that shows employee 0 or "(not found)". It means the lookup read a blank as 0.

The control tested is the approval of planners' adjustments. Because the independent count finds only these three, every other adjustment has an approver recorded. That shows the step was taken, not how well it was done. The 2,884 purchase orders that Michelle Garcia created come from PurchaseOrder (CreatedByEmployeeID), which the exercise does not supply, so they are instructor evidence. To have students substantiate them, supply or import PurchaseOrder and count the orders.

### Requirement (6): The memo

**Step 8. Write it.** An outline: not consistent with experience, with the ratios; the consequences; what the adjusted forecasts show about the review; the evidence and explanations to request.

## Expected results

| Group | Forecast / orders, 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| Furniture | 2.31 | 2.51 | 2.92 |
| Lighting | 2.30 | 2.55 | 2.83 |
| Textiles | 2.34 | 2.60 | 2.84 |
| Accessories | 2.36 | 2.67 | 2.90 |
| Services | 0.31 | 0.28 | 0.31 |
| Four product groups | 2.33 | 2.57 | 2.88 |

| Quantity | Value | Step |
|---|---:|---|
| 2026 units: budget; forecast; orders; invoiced (four product groups) | 264,494; 218,921; 76,023; 76,089 | 6 |
| Forecasts adjusted by more than half; forecasts with no approver | 3; 3 | 7 |
| Planner; job title; purchase orders created (instructor evidence from PurchaseOrder) | Michelle Garcia; Buyer; 2,884 | 7 |

> **Instructor notes, Exercise 7.6:** forecast / orders by year, the four product groups: 2024 about 2.33 (Furniture 2.31, Lighting 2.30, Textiles 2.34, Accessories 2.36); 2025 about 2.57 (2.51 / 2.55 / 2.60 / 2.67); 2026 about 2.88 (2.92 / 2.83 / 2.84 / 2.90). The forecast is consistently more than twice the orders in every product group, and the bias grows each year, so it is not consistent with historical experience. Services, whose forecasts and orders are hours of design work, runs the other way: its forecast is 0.31, 0.28, 0.31 of the hours ordered, an underforecast to explain separately; it is not added to the product units. 2026 product-group totals: forecast 218,920.6 units, budget 264,493.7 units (higher still), orders 76,023.4, invoiced 76,088.9. Forecast methods in the Table: Seasonal Trend, Planner Adjusted, and Lifecycle Adjusted; the forecast weeks run to February 2027. All 66,496 rows are IsCurrent 1 (one version, Current Weekly Plan). Requirement (5): every forecast is within about 10 percent of its baseline (ratios 0.92-1.10) except DemandForecastID 1, 107, and 211, the first forecast week of 2024, 2025, and 2026 (2024-01-01, 2025-01-06, 2026-01-05) for item ACC-MIR-0001 (Foundry Mirror Glass Soft White, Accessories) at warehouse 1, East Distribution Center: ForecastMethod Planner Adjusted, ForecastQuantity 3.1 times BaselineForecastQuantity (23.78 against 7.67, 28.15 against 9.08, 28.06 against 9.05), planner employee 90, Michelle Garcia, a Buyer, and no ApprovedByEmployeeID. They are the only unapproved forecasts in the Table, so the control is the approval of planner adjustments: every other adjustment has an approver recorded, which shows the approval step was taken, not how carefully each change was reviewed. The quantities are small, and the three missing approvals are documented approval-record exceptions. Employee 90 plans most forecasts, and the purchase-order records show 2,884 orders created by that employee, so the buying role creates a potential segregation-of-duties risk, to confirm against the required approvals, delegated authority and compensating reviews before concluding that the role combination breaches policy. Consequences, whose direction depends on the estimate: inflated purchasing and production plans, excess inventory and a possible need for an obsolescence reserve, a reserve understated if it relies on the forecast's view of recoverability, and a budget whose volume makes it a poor standalone measure of performance (Tutorial 7.2). Evidence to request: the forecasting method and its inputs, the planners' adjustments, and management's own comparisons of forecast with actual.

## What a strong answer says

- **Requirement (3).** Not consistent: more than twice the orders in every product group and year, and the bias grows. Services runs the other way and needs its own explanation.
- **Requirement (5).** The list tests the approval of planner adjustments. The three missing approvals are documented approval-record exceptions, small in quantity, on forecasts entered by a buyer who plans most of the Planner Adjusted rows (5,405 in all). The planner's buying role creates a potential segregation-of-duties risk, to confirm against the required approvals, delegated authority and compensating reviews before concluding that the role combination breaches company policy. A populated approval field records a step, not the quality of its review. A plus: the planner's purchase orders (2,884, from PurchaseOrder) and the independent count of blank approvals.
- **Requirement (6).** Consequences whose direction depends on the estimate: plans that buy and build too much, a reserve understated if it relies on the forecast, and a budget that shows the gap from the plan but is a poor measure of performance. Services is assessed separately. The evidence to request: the method and its inputs, the comparisons management made, the reasons for the three overrides, how the forecast feeds the plans, and inventory levels and aging.

A weak answer says the forecast is "high" without the ratios, or treats a recorded approval as proof of a review.

## Common mistakes and how to respond

- **Services added to the units.** *Symptom:* a total ratio below the group ratios. *Cause:* hours added to units. *Response:* ask what a Services quantity measures.
- **Year taken from the wrong date.** *Symptom:* totals that do not match the model answer. *Response:* ask which date places a forecast in a year.
- **The first weeks of 2027 compared with orders.** *Symptom:* a ratio with a zero denominator. *Response:* ask what orders exist for those weeks.
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
- Value the excess forecast product units at standard cost as a planning exposure indicator, and do not call that amount an inventory reserve. A reserve assessment needs the inventory on hand, its aging, expected sales and realizable values, the relevant costs and the applicable accounting policy.
- Discuss: Exercise 7.1 backtests your own forecast and this exercise tests management's. What is the same, and what must the auditor add?
- Discuss: the budget's volume is higher than the forecast. Whose assumption is it, and what does Tutorial 7.2 say it is worth?
