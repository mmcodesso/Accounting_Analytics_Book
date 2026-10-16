# Chapter 15: Reports for Management Decisions

| | |
|---|---|
| Unit | Chapter 15: Reports for Management Decisions |
| Tools | Power BI Desktop |
| Time | About 360 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part IV, Accounting Analytics with Power BI: the third of four chapters. It turns Chapter 14's model into a reporting package that Chapter 16, the appendix on publishing and security and the Part IV case build on |
| Analytics types | Descriptive and diagnostic throughout (reports, variances, drill-through to causes); the what-if parameter and the forecast are the chapter's first prescriptive and predictive tools |
| Tools | Power BI Desktop 2.158 on Windows, reading CharlesRiver.xlsx: Report view, Model view, Power Query, DAX query view |
| Components | 3 guided tutorials (9, 11 and 13 steps) that extend Charles River Reports.pbix, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 70 slides |
| Files students need | CharlesRiver.xlsx. Chapter15-companion.zip holds Charles River Reports, a Power BI project, at the start of Tutorials 15.1, 15.2 and 15.3 and at the end of the chapter. Chapter15-exercises-pbi.zip holds the model answer |
| Time | Class: about 360 minutes. Students: about 100 minutes of reading, 60 to 120 for each tutorial and 60 to 100 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- 9 promotions, three a year. The largest of fiscal 2026, Furniture Seasonal, gave $296,053.58 on 576 lines, and Harbor Collection ends (2026-02-28) before it starts (2026-03-01).
- The budget plans 3.6 times the product revenue actually billed, so only the operating expense lines are comparable. Depreciation is budgeted in Administration and recorded partly in Warehouse, $101,828.64 each way.
- Payroll is recorded on the pay date, so the two months with three pay dates, January and July, run above the flexed budget and every other month below it.
- The time records end 2026-12-11, before the year does, and the Date table runs to the end of 2027. A trailing figure without a year filter is blank for that reason.
- Indirect time ends earlier, 2026-12-04, so the plant ratio is an observed-records diagnostic whose last month is provisional. Counted to that day on both sides, hours and output alike, the year's ratio reads 1.48 against the published 1.51, a labeled sensitivity, not a correction.

## What students should be able to do afterward

1. Design a page for a named reader and decision, with each KPI beside its comparison and a layout that passes a five-second test. Practiced in Tutorials 15.1 to 15.3, Exercises 15.3 and 15.4 (a chart and a page for one reader), and questions 1 and 2.
2. Build drill-through and tooltip pages and say which filters a drill-through passes. Practiced in Tutorial 15.1 (Steps 7 to 9), Tutorial 15.2 (Step 8), Exercise 15.1, and questions 3 and 4.
3. Model a budget beside the ledger and explain a variance as volume, classification, timing, rate or spending. Practiced in Tutorial 15.2 (Steps 1 to 9), Exercise 15.2 (4) for timing, and questions 6 to 9.
4. Write visual calculations, and decide between one and a measure. Practiced in Tutorial 15.2 (Step 10), Tutorial 15.3 (Steps 8 and 9), Exercise 15.2, and questions 10 to 12.
5. Assemble a package with navigation, an About page and tests, and test a chart's claim against a second record. Practiced in Tutorial 15.3 (Steps 12 and 13), Exercise 15.6, and question 13.
6. Use what-if parameters and the forecast, and judge them against what is already known. Practiced in Exercises 15.3 (2), 15.4 and 15.5, and questions 14 and 15.

No exercise rebuilds the budget model or the package, so outcomes 3 and 5 rest mostly on the tutorials: grade Tutorial 15.2's reconciliation and Tutorial 15.3's About page and Test 5 with the exercises.

## Preparing to teach

**Before the first class**

- Students need Windows and Power BI Desktop 2.158 (**Help > About**). A Mac student works in a lab or a virtual machine, as in Chapter 13.
- Do the three tutorials yourself in order and save Charles River Reports.pbix. Tutorial 15.3 loads the labor time and the completions, tens of thousands of rows, so its refresh takes several minutes: tell students to start it before a break.
- A student who lacks the Chapter 14 report, or falls behind, takes Charles River Reports from Chapter15-companion.zip, from the folder of the tutorial they start. Its README gives the steps: open the .pbip, point the queries at CharlesRiver.xlsx (**Home > Transform data > Data source settings > Change Source**), choose **Home > Refresh**, and **File > Save as** a .pbix.
- Tell students to save a copy after Tutorial 15.3, such as `Ch15 Exercises.pbix`, for the exercises: one page or query tab and one display folder of measures for each.
- Open the model answer once. Its visible pages are About through Income Statement (the earlier chapters), then Promotions, Budget and Plant. It also holds the hidden pages Promotion Detail, Promotion Tooltip, Cost Center Detail and Ledger Detail, the visible pages Ex 15.2 to Ex 15.6 and Notes, and the DAX query tabs Tests, Ex 15.1 and Checks. After **Home > Refresh**, **Run** on the Checks tab tests 268 values of the chapter's tutorials and exercises (383 in all).
- The Checks tab cannot read what a visual computes: the visual calculations and the forecast. Compare those by eye on the pages.
- Separate Build and Format panes in place of Visualizations mean the on-object interaction preview is on. The tutorials describe the default panes.

**Pitfalls that cost class time**

- **The drill-through field.** It must also be a field of the visual the reader right-clicks, or the option does not appear (Tutorial 15.1, Step 7).
- **Ctrl.** In Desktop a button responds only with Ctrl held: the back button of a drill-through page and every navigator button.
- **No operating expense filter.** The budget matrix then includes revenue and cost of goods sold, whose static budget ($103,974,558.70 and $55,159,897.72) says nothing about the year.
- **Edit interactions.** Forgotten in Tutorial 15.3 Step 11, a click on Packing shows 0.49 on the card in place of 1.51.
- **KEEPFILTERS.** Without it Direct Hours reads 101,237 for fiscal 2026 in place of 62,764.
- **The forecast.** Desktop computes it, so a new release can move it. Do not hand students a number to match.

![A mock of Model view of the model answer, with the five fact tables around the shared Date table.](../figures/chapter-15-management-reports/IF-15-0-B.pdf)

## Teaching approaches

**Plan A: lecture with live demonstration (four sessions of 90 minutes, 360 minutes in all).** It fits a lecture course with the exercises at home.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 5 | The three readers | 2 to 5 |
| 1 | 25 | Designing for the reader, KPIs, the five-second test; check | 6 to 11 |
| 1 | 20 | Drill-through and tooltips; check | 12 to 17 |
| 1 | 40 | Tutorial 15.1: Steps 4, 7 and 8 live; the rest for students | 18 to 25 |
| 2 | 25 | Budget against actual, the causes, the static-budget trap; check | 26 to 32 |
| 2 | 15 | Visual calculations and where a calculation lives; check | 33 to 39 |
| 2 | 50 | Tutorial 15.2: Steps 6, 9 and 10 live | 40 to 47 |
| 3 | 15 | Navigation, the About page, the package; check | 48 to 52 |
| 3 | 55 | Tutorial 15.3: Steps 5, 8, 9 and 11 live | 53 to 60 |
| 3 | 20 | What-if parameters and forecasts | 61 to 64 |
| 4 | 10 | Looking ahead and the summary | 65 to 70 |
| 4 | 50 | Exercises 15.1 and 15.4 in pairs | |
| 4 | 15 | Quiz on questions 4, 7, 9, 10, 12 and 15 | |
| 4 | 15 | Discussion prompts 1, 2 and 5 | |
| | 360 | Total | |

**Plan B: lab first (three sessions of 120 minutes, 360 minutes in all).** Students build before they hear the vocabulary. It fits a computer lab; a pair that falls behind takes the next tutorial's start file.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Pose the three readers | 5 |
| 1 | 60 | Tutorial 15.1 in pairs | 19 to 24 |
| 1 | 20 | Debrief: drill-through, tooltip, the disconnected table | 13 to 15, 20 |
| 1 | 30 | Short lecture on budget against actual | 26 to 32 |
| 2 | 75 | Tutorial 15.2 in pairs | 41 to 46 |
| 2 | 20 | Debrief: the flex and the reconciliation | 44 to 46 |
| 2 | 25 | Short lecture on visual calculations | 33 to 39 |
| 3 | 80 | Tutorial 15.3 in pairs | 54 to 59 |
| 3 | 20 | Debrief: KEEPFILTERS and the drifting calculation | 56, 57 |
| 3 | 20 | Short lecture on what-if parameters and forecasts | 61 to 64 |
| | 360 | Total | |

**Plan C: flipped, with one 150-minute class.** Students build the tutorials at home. It fits upper-level and graduate classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 15 | Quiz on questions 3, 5, 7, 9, 10, 12, 13 and 15 | |
| 30 | Review clinic: partners compare Test 4, Test 5 and the Validation page | 47, 60 |
| 30 | Break it: the static budget, a visual calculation on a filtered axis, a click on a work center | 29, 36, 56, 57 |
| 50 | Exercises 15.1 and 15.2, or 15.5, in pairs | |
| 15 | Discussion prompts 3 and 6; assign | |
| 10 | Looking ahead to Chapter 16 | 65, 66 |
| 150 | Total | |

Plan A is the safest: the stumbles are in reading a variance and a filter, and a demonstration shows how. Plan B lets students meet the traps themselves and needs a lab. Plan C leaves no time to demonstrate, and fails for students who arrive without a finished package.

![What each tutorial adds to the model and where each exercise attaches, so an instructor sees the build at a glance.](../figures/chapter-15-management-reports/IF-15-0-A.pdf)

## Tutorial guide

### Guided Tutorial 15.1: The Promotions Page

**Purpose.** Students build the sales manager's page: a waterfall from list price to net, the discounts by promotion, and two detail pages. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Step 4 (SELECTEDVALUE and SWITCH on a table that relates to nothing), Step 7 (the drill-through well) and Step 8 (the tooltip page). Leave Steps 1 to 3, 5, 6 and 9 to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | The promotions, related | 9 promotions; 25,825 of 27,933 lines have none and sit under (Blank) |
| 3 to 5 | The waterfall, fiscal 2026 | list $33,589,137.45; price lists and overrides -$3,470,607.31; promotions -$362,110.06; total $29,756,420.08 |
| 6 | Discounts by promotion | Furniture Seasonal $296,053.58 on 576 lines, several times any other |
| 7, 9 | The detail page | Furniture Seasonal runs through months after its end date; Harbor Collection ends (2026-02-28) before it starts (2026-03-01) |
| 8 | The tooltip | the promotion's months, shown while pointing |

**Stumbles to expect**

- Step 2: DiscountPct left to sum. The detail page then adds the rate. Set **Don't summarize** (Step 2d).
- Step 4: the promotions step typed as the Discounts measure with its sign changed. The steps then miss the total by $0.69, the rounding of the lines.
- Step 7: the field dragged with a visual selected, so it joins the visual and the well stays empty.
- Step 8: the tooltip page switched on in one place only. It needs the page's type and the tooltip switch, and the visual's own tooltip setting.
- Step 9: the back button clicked without Ctrl.

**The checkpoint to look for.** The three bullets. A strong student says the promotions are the smaller of the two reductions from list price.

### Guided Tutorial 15.2: The Cost-Center Budget Page

**Purpose.** Students add the budget as a second fact table, compare it with the ledger, and explain the variances. **Time.** About 90 to 105 minutes. **Demonstrate, then hand over.** Demonstrate Step 6 (read the flexed budget a variable at a time), Step 9 (the reconciliation) and Step 10 (RUNNINGSUM). Leave Steps 1 to 5, 7, 8 and 11 to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | The budget related by month, account and cost center | BudgetDate, the first day of each month, related to Date |
| 3, 4 | Operating expense, fiscal 2026 | budget $8,289,648.80; actual $6,471,696.58; Sales -62.7%, Warehouse +26.9%, Administration -17.1%; the others -4.5% to -3.7% |
| 5 | Icons | arrows on the three outliers, a circle elsewhere |
| 6, 7 | The flexed budget | flexed commission $621,780.04; flexed operating expense $6,646,455.55 |
| 8 | The drill-through | Warehouse: depreciation with no budget; Administration: a budget above its actual |
| 9 | The reconciliation | volume -$1,643,193.25; classification Warehouse +$101,828.64, Administration -$101,828.64; remaining -$174,758.97 |
| 10 | The running variance | above the flexed budget only in January and July |
| 11 | Test 4 | $8,289,648.80; $6,646,455.55; $6,471,696.58 |

**Stumbles to expect**

- Step 2: BudgetDate related to a text column, or the keys left visible.
- Step 4: no filter on Operating Expense, so revenue and cost of goods sold enter.
- Step 5: the thresholds typed as whole percents. Rules take decimals, entered with **Number**.
- Step 6: the formula typed on one line, or KEEPFILTERS missing.
- Step 10: the visual calculation tried on an unselected visual, or the table not filtered to the year.
- The sign: a positive expense variance is spending above the budget, and students read it as good.

**The checkpoint to look for.** The three bullets. A strong student says the classification effect totals zero and names what remains.

### Guided Tutorial 15.3: The Plant Page and the Package

**Purpose.** Students add the labor time and the output, measure the plant over a trailing twelve months, finish the package and test it. **Time.** About 90 to 120 minutes, the refresh included. **Demonstrate, then hand over.** Demonstrate Step 5 (KEEPFILTERS), Steps 8 and 9 (the visual calculation drifting) and Step 11c (Edit interactions). Leave Steps 1 to 4, 6, 7, 10, 12 and 13 to students.

| Step | Look for | Value |
|---|---|---|
| 1 to 4 | The plant Tables, related | 68,859 labor lines, 51,097 direct lines with an operation; 17,352 completion lines for 83 items |
| 5, 6 | Hours, output, ratio, by year | 2024: 83,637 hours, 70,871 standard hours, 1.18; 2025: 93,391 hours, 66,109 standard hours, 1.41; 2026: 101,237 hours, 66,998 standard hours, 1.51 |
| 7 | The trailing measure | 2024-12 1.18 to 2026-12 1.51; blank before twelve months |
| 8, 9 | The visual calculation | on an axis from January of the prior year it reads 1.375, the measure 1.121; equal from December |
| 10 | The card | 1.51 beside the first year's 1.18; blank with no year filter |
| 11 | Work centers, job titles | Packing first with 33,026.9 direct hours |
| 12, 13 | About page; Test 5 | Test 5 returns the three yearly ratios; saved on About |

**Stumbles to expect**

- Step 3: **Load** in place of **Transform Data**, and a refresh abandoned because it is slow.
- Step 3d: the Item query's **Choose Columns** reopened from the wrong step.
- Step 5: KEEPFILTERS missing. Direct Hours reads every manufacturing hour.
- Step 6: Standard Hours without the cut-off, which overstates the last year's output.
- Step 9: the table's year filter not changed, so the two columns agree and the lesson is lost.
- Step 11c: Edit interactions skipped, so a click on Packing shows 0.49.
- Step 12: a measure without a description, or the navigator tested without Ctrl.

**The checkpoint to look for.** The four bullets. A strong student says why the card ignores the work-center chart: the output has no work center. A strong student also reads the latest ratio as provisional, because indirect time ends before the cut-off.

## Difficult ideas and misconceptions

**A drill-through passes the whole data point.** Tutorial 15.1 Step 9, Exercise 15.1 (5), questions 3 and 4. Students think the page filters itself. Ask: what does the page show if the click came from the row's label?

**A variance is a difference, not a cause.** Tutorial 15.2, questions 7 to 9. Sales reads -62.7% and looks like thrift; the commission budget was built on a volume that never came. Ask: what was the budget built on?

![A board sketch of the budget variance, from the static budget to the actual, by cause.](../figures/chapter-15-management-reports/IF-15-0-D.pdf)

**A classification effect nets to zero.** Question 9. It moves cost between cost centers: $101,828.64 each way, so it explains none of the company's total. Ask: what is the total of the column?

**Timing hides in a year-to-date.** Tutorial 15.2 Step 10. The running variance stands at $4,848.62 in July, close to the flexed budget, because January and July run above it and the months between run below it. A reader in July saw operating expense close to the flexed budget for the year to date. Ask: which months are above it, and why?

**A visual calculation sees only its visual.** Tutorial 15.3 Step 9, Exercise 15.2 (3), question 10. On an axis that starts a year in, the first month averages one month: 1.375 against the measure's 1.121. Ask: which rows can it see?

**KEEPFILTERS combines, a filter argument replaces.** Question 12. Ask: what does the inner filter do to the outer one?

**A ratio needs its denominator at the same grain.** Tutorial 15.3 Step 11c. Hours belong to a work center and output does not. Ask: what is the output of one work center?

**A forecast is a model, not data.** Exercise 15.5, question 15. It cannot be read from the model and moves with the history. Ask: which quarter do you already know?

**Two records of one fact.** Exercise 15.6. They agree most of the time and differ where the audit questions are. Ask: what does each record measure?

## Discussion prompts

1. **The controller wants one KPI for every department. What do you say?** It reaches Lipe and Salterio: shared measures defined alike, unique measures kept and flagged as counting.
2. **Where should the threshold of an icon come from?** It reaches the five percent as the package's choice, stated on the page, and Cardinaels and van Veen-Dirks on markers changing weights.
3. **Should the budget page show revenue against the static budget?** It reaches the static-budget trap, flexing, or leaving it off with a stated reason.
4. **A manager reads the report in July and sees operating expense close to its flexed budget for the year to date. What happened?** It reaches three pay dates, recorded when paid, and the months between.
5. **When is a visual calculation the right tool?** It reaches a chart's own shape, against a number readers export, compare or test.
6. **Is the plant ratio a measure of one work center?** It reaches grain, and what the page would need to measure output where it happens.
7. **Would you put the forecast on the plan page?** It reaches the hindcast, the benchmarks, the start-up month and the disclosure.

## Using the exercises

All six exercises are Power BI work with a model answer in Chapter15-exercises-pbi.zip: five pages and one DAX query tab, with the Checks tab behind them. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 15.1 From the Income Statement to the Entry | Financial | Power BI | 60 | Basic | 2 |
| 15.2 Month and Year to Date With Visual Calculations | Financial | Power BI | 60 | Intermediate | 3, 4 |
| 15.3 One Chart, Three Measures | Managerial | Power BI | 75 | Intermediate | 1, 6 |
| 15.4 What Would the Design Trade Promotion Need? | Managerial | Power BI | 75 | Intermediate | 1, 6 |
| 15.5 Testing the Forecast Before Trusting It | Auditing | Power BI | 75 | Advanced | 6 |
| 15.6 Which Work Center Did the Time Belong To? | Auditing | Power BI | 100 | Advanced | 5 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 15.1 and 15.2, managerial students 15.3 and 15.4, auditing students 15.5 and 15.6. Each track presents its traps to the others.
- *One exercise a session.* Take the basic one first: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6.
- *A light load.* Exercises 15.1 and 15.4 take about two hours and fifteen minutes and cover outcomes 1, 2 and 6.

**Grading and discussion.** Exercises 15.1 to 15.4 suit grading from the saved report, and Exercise 15.6 from its queries, with the Checks tab to compare a number. Exercise 15.5 is graded on its audit note: Desktop computes the forecast, so a student's value need not match. Exercises 15.4 and 15.5 suit class discussion. Collect the .pbix, not screenshots: the measures, the display folders and the query text are the evidence.

![What the Checks tab proves in each item and what only Desktop shows, the map an instructor needs before grading.](../figures/chapter-15-management-reports/IF-15-0-C.pdf)

## Multiple-choice questions

Key: 1 D, 2 B, 3 A, 4 C, 5 B, 6 D, 7 C, 8 A, 9 B, 10 D, 11 A, 12 C, 13 C, 14 B, 15 A.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | D | a KPI is a measure shown with the comparison that gives it meaning. |
| 2 | B | only the common measures affected the evaluations (Lipe & Salterio, 2000). |
| 3 | A | drill-through opens another page filtered to the selected item. |
| 4 | C | tooltips are not interactive and screen readers cannot read them (Learn). |
| 5 | B | a disconnected table supplies categories; the measure reads the selected step. |
| 6 | D | store the first day of the period and relate it one-to-many to the date table. |
| 7 | C | actual less budget, positive for an expense, is spending above budget, unfavorable. |
| 8 | A | the commission budget was calculated on the budget's revenue volume, several times actual. |
| 9 | B | a classification difference moves cost between cost centers; the total is unchanged. |
| 10 | D | a visual calculation sees only the rows on its visual (1.375 against the measure's 1.121). |
| 11 | A | visual calculations cannot be reused or exported; KPIs belong in measures. |
| 12 | C | a filter argument on the same column replaces the existing filter unless KEEPFILTERS is used. |
| 13 | C | the page navigator follows the pages by itself; a bookmark keeps the state it captured until it is updated. |
| 14 | B | a GENERATESERIES-style table and a measure with SELECTEDVALUE, and optionally a slider. |
| 15 | A | judge a forecast by a hindcast against known periods and simple benchmarks (Chapter 7). |

**Questions where a wrong option tempts**

- **Question 2.** Option D says all measures weighed equally, the opposite of the finding; option A inverts it.
- **Question 6.** Option B copies the budget to every day and overstates it by the days in each month; the guidance stores the first day.
- **Question 7.** Option A takes the variance as budget less actual, the opposite of the convention the text sets.
- **Question 9.** Option A: classification explains none of the total. Option C confuses it with timing.
- **Question 10.** Option D: the calculation averages the months it has, 1.375 against 1.121.
- **Question 12.** Option A sounds like a model problem. It is the inner filter replacing the outer one.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 4 make a quiz on design and detail pages, 5 to 9 on the budget, 10 to 13 on visual calculations, filters and navigation, and 14 and 15 on parameters and forecasts.

## Connections

**Builds on.** Chapter 1's promise of drill-down to causes; Chapter 2's warning about a budget and a ledger that classify a cost differently; Chapter 4's Documentation worksheet, here the About page; Chapter 6's bridge; Chapter 7's flexible budget, benchmarks and break-even lift; Chapters 10 to 12's plant measure, three pay dates and late time; Chapter 13's Validation page; and Chapter 14's model, DAX, the closes and KEEPFILTERS.

**Later chapters.** Chapter 16 monitors exceptions with the same model and audits the package itself: its tests, its currency and its change control. The Part IV case builds a new report with the same package structure.

**Appendices.** The appendix on publishing and security gives each department manager only their cost center and publishes the package. The appendix on Power BI in the browser rebuilds Chapter 13's model there. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
