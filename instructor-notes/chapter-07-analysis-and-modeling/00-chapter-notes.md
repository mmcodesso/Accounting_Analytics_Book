# Chapter 7: Forecasting, Budgeting, and What-If Analysis in Excel

| | |
|---|---|
| Unit | Chapter 7: Forecasting, Budgeting, and What-If Analysis in Excel |
| Tools | Excel |
| Time | About 240 minutes of class time |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part II, Accounting Analytics with Excel: the fourth Excel chapter. It turns from explaining the past (Chapters 5 and 6) to estimating the future and evaluating decisions |
| Analytics types | Predictive (regression, trend forecasts, backtests, budgets) and prescriptive (break-even analysis, what-if tools, Solver) |
| Tools | Excel with Power Query: the Analysis ToolPak (Correlation and Regression), FORECAST.LINEAR, TREND, SUMIFS, FILTER, UNIQUE and SORT, named cells, Scenario Manager, data tables, Goal Seek and Solver. No SQL or Power BI |
| Components | 3 guided tutorials, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 57 slides |
| Files students need | CharlesRiver.xlsx, never edited, and Charles River Furniture Analysis.xlsx as it stands at the end of Chapter 6. Chapter07-companion.zip holds the workbook at the start of each tutorial and at the end of the chapter, and Chapter07-exercises.zip the model answers (Chapter 7 Exercises - Solutions.xlsx). The companion files read `C:\CharlesRiver\CharlesRiver.xlsx` |
| Time | Class: about 240 minutes. Students: about two hours of reading, 60 to 90 minutes for each tutorial and 60 to 120 for each exercise (assign two or three). The tutorial times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The first month of the data is a start-up month. It holds 279 invoices against about 587 in each other month of its year, and its revenue ($1,408,516.50) is far below the average of the other 35 months ($2,429,666.55). One month makes a flat series look like a significant trend.
- The sales budget plans 3.5 times the units sold, so its sales-volume variance (-$34,792,987.53) dwarfs everything else. The budget's prices are close, and its operating expenses are close except two accounts.
- Budget lines with no cost center (rent, utilities, insurance and others) are missing from the Budget Table: the summary understates the detail by $2,024,273.70 in 2026.
- The Furniture Seasonal Promotion needs a volume lift of 30.8% to pay for itself, and the Furniture units ordered in its months are +0.7% against the other months.
- The Solver exercise rests on a hypothetical: half of each work center's hours. Only Assembly binds.
- The demand forecast runs 2.33, 2.57 and 2.88 times the units ordered in 2024, 2025 and 2026, and 3 planner adjustments have no approver.

## What students should be able to do afterward

1. Measure the relationship between two variables with correlation and regression, and judge it with R Square, p-values and residuals. Practiced in Tutorial 7.1 (Steps 3 to 5), Exercise 7.5 (requirements 2 and 3) and questions 1 to 4.
2. Forecast with TREND and FORECAST.LINEAR and judge a forecast by backtesting it against benchmarks. Practiced in Tutorial 7.1 (Steps 6 to 8), Exercise 7.1 and questions 5 to 7.
3. Compare actual results with a static and a flexible budget, and explain the two variances. Practiced in Tutorial 7.2, Exercise 7.2 (the summary against its detail) and questions 8 to 10.
4. Build a contribution margin model with documented assumptions and calculate break-even revenue and the margin of safety. Practiced in Tutorial 7.3 (Steps 1 to 3), Exercise 7.3 (requirements 1 to 4 and 6) and question 11.
5. Evaluate a decision with Scenario Manager, a data table and Goal Seek, and describe what Solver adds. Practiced in Tutorial 7.3 (Steps 4 to 8), Exercises 7.3 (requirement 5) and 7.4, and questions 12 to 15.
6. Test someone else's expectation or forecast as an auditor: its precision, its consistency with experience and the control over its adjustments. Practiced in Exercises 7.5 and 7.6.

## Preparing to teach
**Before the first class**

- Students need desktop Excel with Power Query (on a Mac, Excel for Microsoft 365). The tutorials use FILTER, UNIQUE, SORT and spill ranges (Microsoft 365 or Excel 2021 or later); the model answers also use LET, XLOOKUP, HSTACK and VSTACK (Microsoft 365 or Excel 2024).
- Students load the Analysis ToolPak before Tutorial 7.1 and the Solver add-in before Exercise 7.4. Check on one machine that **Data > Data Analysis** and **Data > Solver** appear.
- A late student takes the start file from Chapter07-companion.zip, points its queries at their copy of CharlesRiver.xlsx (**Data > Get Data > Data Source Settings**, **Change Source**) and chooses **Data > Refresh All**.
- Do the three tutorials yourself. Tutorial 7.2 is the longest: several merges, one on three columns, and a FlexLines Table of several thousand rows. Time its refreshes.
- Get the PowerPoint deck from the Downloads page; its modules follow the chapter's sections.

**Pitfalls that cost class time**

- **Fixed rows.** Tutorial 7.1 names rows (the backtest reads rows 3 to 34 and 35 to 37), so a student who shifts the series gets a different backtest.
- **Labels in the ToolPak.** Step 4 checks **Labels** and Step 5 clears it. A wrong choice shifts every range by one row.
- **Frozen results.** ToolPak output and a Scenario Summary do not update when data change, and Goal Seek leaves its answer in the cell.
- **Named cells.** A name typed in a cell defines nothing: use the **Name Box**.
- **Data table inputs.** They must be on the table's worksheet, and a swap gives plausible, wrong values.

## Teaching approaches

**Plan A: lecture with live demonstration (three sessions of 80 minutes, 240 minutes in all).** It fits a lecture course with a projector and home time for the exercises. One tutorial anchors each session; you demonstrate the steps that carry the ideas and leave the rest to students.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The controller's three requests, the objectives, predictive and prescriptive analytics | 2 to 6 |
| 1 | 20 | Correlation and regression: the four numbers, the start-up month, the Watch out | 7 to 12 |
| 1 | 15 | Trend functions, benchmarks, backtests; the check and the answer | 13 to 18 |
| 1 | 35 | Tutorial 7.1: Steps 3, 4 and 6 live; students finish at home | 19 to 22 |
| 2 | 20 | Budgets, flexible budgets, the two variances; the check and the answer | 23 to 30 |
| 2 | 40 | Tutorial 7.2: Steps 3, 4 and 10 live; the rest is homework | 31 to 36 |
| 2 | 20 | Contribution margin, break-even, the price cut and the four what-if tools | 37 to 41 |
| 3 | 10 | Which tool answers each question: the check and the answer | 42 to 43 |
| 3 | 45 | Tutorial 7.3: Steps 2, 3, 5 and 6 live | 44 to 49 |
| 3 | 10 | Communicating forecasts and models | 50 to 51 |
| 3 | 15 | Looking ahead, the summary; assign the exercises | 52 to 57 |
| | 240 | Total | |

**Plan B: lab first (one session of 180 minutes, with Tutorial 7.2 as homework).** Students build before they hear the vocabulary, so the backtest and the break-even lift arrive as results they produced. It fits a computer lab. Pairs take the next start file when they fall behind.

| Minutes | Activity | Slides |
|---|---:|---|
| 5 | Pose the controller's three requests | 4 |
| 55 | Tutorial 7.1 in pairs, to the checkpoint | 19 to 22 |
| 10 | Debrief: the start-up month, the regression output, the backtest | 8 to 18 |
| 20 | Debrief of Tutorial 7.2, done at home: the BudgetReport worksheet | 23 to 36 |
| 10 | Contribution margin and the four what-if tools | 37 to 43 |
| 55 | Tutorial 7.3 in pairs, from the Tutorial 7.2 start file | 44 to 49 |
| 15 | Debrief: the lift, the data table, the recommendation | 46 to 48 |
| 10 | Assign the exercises | 52 to 57 |
| 180 | Total | |

**Plan C: flipped, with one 90-minute class.** Students read the chapter and build the three tutorials at home. It fits upper-level and graduate classes and opens with a quiz.

| Minutes | Activity | Slides |
|---|---:|---|
| 10 | Quiz on questions 4, 5, 8, 10, 11 and 13 | |
| 20 | Review clinic: partners swap workbooks and check Forecast!C38, the backtest errors, the margin check on BudgetReport and Model!B11 | 21, 34, 47 |
| 25 | Break it: a regression through the start-up month, a flexible budget that flexes rent, a data table with swapped input cells | 12, 28, 46 |
| 25 | Start Exercise 7.2 or 7.5 in pairs | |
| 10 | Discussion prompts 1 and 4; assign the exercises | 51, 56 |
| 90 | Total | |

Plan A is the safest. Plan B gives students ownership of the models and needs a lab and a homework habit. Plan C leaves no time for demonstration and relies on the check clinic to catch what home work missed.

> **[Figure placeholder IF-07-0-A]** Which what-if tool answers which question, as a decision tree for the discussion of Tutorial 7.3 and Exercise 7.4.
> Kind: diagram · Shows: A top-down decision tree. The root asks what you want to know. Four branches end in a tool: results under a few named sets of inputs (Scenario Manager), results across a range of one or two inputs (data table), the input that reaches a target (Goal Seek), the best values of several inputs within limits (Solver). Under each tool, one example from the chapter, named without numbers. · Data: The chapter's table of what-if tools, with the examples of Tutorial 7.3 and Exercise 7.4. · Status: planned

## Tutorial guide
### Guided Tutorial 7.1: Forecasting Revenue and Testing the Forecast

**Purpose.** Students build a monthly series, find what moves with revenue, fit a trend with and without the start-up month, and backtest three forecasts before forecasting the next quarter with a range. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Step 3 (the correlation tool, with and without the first month) and Step 6 (the backtest layout). Leave Steps 8 and 9 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1, 2 | The series: 36 months, the control total at zero; the first month far below the rest | $1,408,516.50 against an average of $2,429,666.55 |
| 3 | Revenue against the customers and against the average line, all months, then without the first | 0.77 and 0.24; then 0.43 and 0.66 |
| 4 | Trend36: R Square, slope per month, P-value | 0.169; $9,225.54; 0.013 |
| 5 | Trend35: the same three | 0.096; $5,033.92; 0.071 |
| 6, 7 | The fourth quarter's actual revenue, then each forecast's error of the quarter and monthly error | $7,287,187.68; trend +4.72%, 4.88%; mean +0.03%, 3.65%; same quarter +0.32%, 11.48% |
| 8 | The forecast of 2027 Q1 with its range | $7,288,999.66; low $7,022,788.21; high $7,555,211.11 |

**Stumbles to expect**

- Step 1: the control total in C38 not zero, because a range or a criterion was miscopied.
- Step 3: **Labels in first row** left checked on the second run, which has no headings.
- Steps 4 and 5: **Labels** wrong, which shifts every range by one row.
- Step 6: forecasts built on the wrong rows. The mean must use rows 3 to 34 only.

**The checkpoint to look for.** The five bullets. A strong student says the trend is significant only with the first month (about 45% of the slope comes from that month) and that the range is the backtest error, not a confidence interval.

### Guided Tutorial 7.2: Comparing 2026 with the Budget

**Purpose.** Students price every invoice line at the budget's planned price, build the static, flexible and actual margins by product line, split the price variance and test two expense assumptions. **Time.** About 75 to 90 minutes; the merges of Steps 3 and 8 take longest. **Demonstrate, then hand over.** Demonstrate Step 3 (the three-column merge, with the types matched) and Step 10 (the drivers). Leave Steps 6 and 7 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 3 | Lines with no planned price | 5, seasonal items in their launch month |
| 4, 5 | The Total column: static, flexible and actual margin | $48,814,660.98; $14,021,673.45; $12,739,803.20; row 6 plus the two variances equals row 12 in every column |
| 5 | The two variances | Sales-volume -$34,792,987.53; flexible-budget -$1,281,870.25; budgeted units 3.5 times actual |
| 6 | Price gap before discounts, as a share of flexible revenue | 2.7% to 3.7% in the four lines; discounts $362,110.75, almost all Furniture |
| 7 | Furniture price after promotions, September and October, against the planned price | 83.8% and 80.6% against 88.1%; still 88.3% in December against 89.2% before promotions |
| 9, 10 | The two expense exceptions | Burden rate 13.5% against 18.0% budgeted; flexed commission $621,780.04 against $566,347.93 paid |

**Stumbles to expect**

- Step 3: the merge columns clicked in the wrong order, or the type of Month left unmatched, so every planned price is empty and FlexRevenue equals the actual.
- Step 4: the COGS formulas copied without changing `"Revenue"` to `"COGS"`.
- Step 8: **Load** chosen for the ledger Table, which has hundreds of thousands of rows.
- Step 9: a typed value in the spill range, which returns #SPILL!.

**The checkpoint to look for.** The five bullets. A strong student says the static budget cannot judge the year, and that only the flexible-budget variance is a pricing question.

### Guided Tutorial 7.3: Should Charles River Repeat the Furniture Promotion?

**Purpose.** Students build a model whose inputs sit apart from its results, use Scenario Manager, a data table and Goal Seek on it, and check the answer against the orders. **Time.** About 60 minutes. **Demonstrate, then hand over.** Demonstrate Step 1 (names through the **Name Box**) and Steps 5 and 6 (the data table and Goal Seek, with **Cancel**). Leave Steps 7 and 8 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2 | The inputs of the promotion's lines | 4,823.89 units; $613.72 before discount; $346.36 cost; commission rate 1.90% |
| 3 | The difference at the 10% discount and no lift | -$290,418.84 |
| 4 | The Scenario Summary: repeat as in 2026, repeat with 15 percent lift, deeper discount | -$290,418.84; -$148,970.24; -$315,961.07 |
| 5, 6 | The data table's rows at 30 and 35 percent lift at the 10% discount, and Goal Seek's break-even lift | -$7,521.63 and $39,627.90; 30.8% |
| 7 | Furniture units from orders placed in September and October, against January to August | 2,361 and 2,462; an average of 2,396; December only 1,571, because orders are not yet invoiced |

**Stumbles to expect**

- Step 1: names typed into column C only, so the formulas of Step 3 return #NAME?.
- Step 4: lifts entered as 15 and not as 0.15, which makes every scenario absurd.
- Step 5: the row and column input cells swapped.
- Step 6: **OK** instead of **Cancel** in the status dialog, which leaves the lift in B3 and changes every later result.

**The checkpoint to look for.** The four bullets. A strong student states the recommendation with its condition: do not repeat as it ran unless a lift near 31% is credible, and the orders show no such lift without proving what the promotion caused.

> **[Figure placeholder IF-07-0-B]** How the break-even lift of the promotion depends on the discount, for the discussion of the assumptions table.
> Kind: chart · Shows: A line chart. The horizontal axis is the discount rate from zero to 15 percent, the vertical axis the volume lift at which the promotion breaks even, both as percentages, starting at zero. Three points are labeled: 5 percent, 10 percent (the promotion as it ran) and 15 percent. · Data: The break-even lift computed from the inputs of the Model worksheet (units, price before discount, variable cost, commission rate) at each discount. · Status: planned

## Difficult ideas and misconceptions
**One point can flip a result.** Questions 2 and 4, and Tutorial 7.1: the correlation with customers falls from 0.77 to 0.43 and the slope loses its significance. Ask: what would you report to the controller, and what would you ask about the first month?

**A large p-value is not proof of no trend.** Question 4's option D. The honest sentence is "no reliable evidence of a trend". Ask: why?

**R Square is a share, not an accuracy.** Question 3's options A and C. A line with R Square of 0.17 can still be extended; the backtest decides.

**The backtest must not see the answer.** Question 5. Students fit the line to the whole series and report errors near zero. Ask: what did you know on the day of the forecast?

**The simplest method is a benchmark, not a rival.** The mean beats the trend in Tutorial 7.1, and no method wins in every group of Exercise 7.1. Question 6's option B ("always more accurate") overstates it.

> **[Figure placeholder IF-07-0-C]** The static budget, the flexible budget and the actual margin of the four product lines in one walk.
> Kind: diagram · Shows: A bridge with six bars: static budget margin, sales-volume variance, flexible budget margin, price gap before discounts, promotional discounts, actual margin. The totals are blue, the three variances coral, each with a signed dollar label, and the sales-volume bar is drawn to scale so the others look small. · Data: The Total column of the BudgetReport worksheet (Tutorial 7.2), rows for the three margins, the sales-volume variance, the price gap and the discounts. · Status: planned

**Flex what varies.** Question 8's option B scales every line by one percentage, and question 10's option D calls commissions fixed. Tutorial 7.2 flexes the commission and leaves rent at its budget.

**Two variances, two questions.** The sales-volume variance (question 9) belongs to whoever built the volume forecast, the flexible-budget variance to pricing and production. For the product lines it is entirely a price variance, because the budget and the actuals value units at standard cost.

**Break-even needs the right fixed costs.** Exercise 7.3 leaves out interest, which the income statement of Chapter 6 shows below operating income, and adds freight-out and two variances that standard costs omit. Question 11 tests the formula; the exercise tests the judgment.

**The lift depends only on margins.** Fixed costs do not enter, because the decision does not change them. Ask: which inputs change if the discount changes?

**A constraint that is an assumption.** Exercise 7.4 halves the hours by hypothesis; the plant used well under its capacity in 2026. Questions 13 and 14 ask which tool and when the Sensitivity report exists. Ask: what is the shadow price when no work center binds?

## Discussion prompts
1. **The sales team wants a higher revenue forecast. What do you give the controller?** A good discussion reaches the backtest as the objective reference, the range as a record of past errors, and a statement of the method and the months fitted.
2. **The trend is significant with the first month and not without it. Which result do you report?** Both, with the reason for any exclusion; the first month is a start-up month, not noise.
3. **The budget planned 3.5 times the units sold. What is the variance report worth?** The sales-volume variance describes the forecast; the flexible-budget variance is the one to act on.
4. **The Furniture promotion needs a lift of 31%. How would you find out whether it would come?** It reaches the orders as description and not cause, a test or a smaller promotion, and the lower bar of a smaller discount.
5. **Solver says only Assembly binds. What do you do on Monday?** It reaches the shadow price as the most you would pay for an extra hour, and the range over which it holds.
6. **A forecast runs 2.9 times the orders. Is it an estimate or a bias?** The same direction in every group and year, a systematic cause, and what a reserve or a plan built on it would do.
7. **Who approved the forecast changes?** The three unapproved adjustments, a buyer who also places orders, and a recorded approval that shows a step and not a review.

## Using the exercises

All six exercises are Excel builds with a model answer in the workbook of Chapter07-exercises.zip, one or more worksheets each. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 7.1 Forecasting Revenue by Product Line | Financial | Excel | 90 | Intermediate | 2 |
| 7.2 Reconciling the Budget to Its Detail | Financial | Excel | 60 | Basic | 3 |
| 7.3 Company Break-Even and Margin of Safety | Managerial | Excel | 90 | Intermediate | 4, 5 |
| 7.4 The Product Mix under a Capacity Constraint | Managerial | Excel | 120 | Advanced | 5 |
| 7.5 Regression-Based Expectations for Revenue and Commissions | Auditing | Excel | 90 | Advanced | 1, 6 |
| 7.6 Evaluating Management's Forecast | Auditing | Excel | 75 | Intermediate | 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 7.1 and 7.2, managerial students 7.3 and 7.4, auditing students 7.5 and 7.6. A swap of memos lets each track hear the others; Exercise 7.4 is worth presenting to everyone.
- *One exercise a session.* Take them in the order 7.2, 7.6, 7.1, 7.3, 7.5, 7.4, from the lightest to the longest.
- *A light load.* Exercises 7.2 and 7.3 take about two and a half hours and cover outcomes 3 to 5. Add Exercise 7.6 for the audit view.

**Grading and discussion.** Each exercise guide holds a rubric. Exercises 7.2, 7.3 and 7.4 suit grading from the workbook, because their numbers have one answer. Exercises 7.1, 7.5 and 7.6 end in a judgment and suit class discussion. Collect the workbook, not a screenshot: the formulas show the work.

## Multiple-choice questions

Key: 1 D, 2 A, 3 B, 4 C, 5 B, 6 D, 7 A, 8 C, 9 C, 10 B, 11 D, 12 A, 13 B, 14 C, 15 A.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | D | a coefficient of -0.80 is a strong negative linear association; it says nothing about cause or size. |
| 2 | A | when one observation changes the conclusion, investigate it and report both results, with the reason for any exclusion. |
| 3 | B | R Square is the share of the variation in y that the line explains. |
| 4 | C | the slope is significant only with the start-up month, so test the trend before relying on it; a p-value above 0.05 is no proof of no trend. |
| 5 | B | a backtest fits the method to earlier data and compares its forecasts of held-back data with the actuals. |
| 6 | D | a method that cannot beat simple benchmarks is not worth its extra complexity. |
| 7 | A | both fit the same least-squares line; TREND can return several values, FORECAST.LINEAR one. |
| 8 | C | a flexible budget recalculates the budget at actual volume with budgeted prices and costs per unit. |
| 9 | C | the sales-volume variance values the difference in units at the planned margins per unit. |
| 10 | B | commissions are variable, so lower revenue may explain much of the gap; flex the budget to actual revenue before judging the rest. |
| 11 | D | break-even revenue is fixed costs divided by the contribution margin ratio: 900,000 / 0.30 = 3,000,000. |
| 12 | A | Goal Seek changes one input until a formula cell reaches a target value. |
| 13 | B | a two-variable data table fills in a result for every combination of two inputs. |
| 14 | C | the Sensitivity report requires an optimal solution and no integer constraints. |
| 15 | A | the sensitivity column shows which assumptions change the conclusion, so review focuses on them. |

**Questions where a wrong option tempts**

- **Question 3.** Option A reads R Square as a growth rate and option C as a p-value.
- **Question 4.** Option A extends the trend, option D reads a large p-value as proof.
- **Question 5.** Option A recalculates after the fact. A backtest never lets the method see the held-back data.
- **Question 8.** Option B scales every line by one percentage, which is not flexing.
- **Question 10.** Option A treats a volume effect as savings, option D calls commissions fixed.
- **Question 11.** Option A multiplies, option B adds, option C multiplies by three. Only division works.
- **Question 14.** Option A requires whole numbers, the one condition that removes the report.
- **Questions 2, 3, 4, 5, 7, 8, 9, 10, and 15.** The correct option is also the longest. If you grade with these, ask students to explain their answer or reword the options.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 4 make a quiz of regression, questions 5 to 7 of forecasting, questions 8 to 10 of budgets, and questions 11 to 15 of break-even and the what-if tools.

## Connections
**Builds on.** Chapter 1 introduced the regression-based expectation and the four analytics types. Chapter 4 taught SUMIFS, Tables, named cells, Power Query and the control total, and Chapter 5 built InvoiceLines and the order date and item group that Tutorial 7.3 uses. Chapter 6 supplied the unrounded cost and discount columns, the ledger and income statement, and the promotion whose break-even lift this chapter measures.

**Later chapters.** Chapter 8 takes up what this chapter leaves for the auditor, such as invoices whose dates and numbers disagree and the planning forecast, and Part III builds expectations in SQL (Tutorial 12.3's pay expectation). Part IV rebuilds the budget variance in DAX, with a flexed commission, a what-if discount and a forecast. The Part II case decides a promotion calendar with the same break-even model, and Chapter 18 returns to make-or-buy with a Solver model.

**Appendices.** The quick reference lists every Excel and Power Query function the chapter uses. **Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard; each exercise guide names the competencies it practices.
