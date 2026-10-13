---
note: ch15.chapter
uses: [ch15.t1, ch15.t2, ch15.t3, ch15.ex2, ch15.mcq]
title: 'Chapter 15: Reports for Management Decisions'
kind: chapter-notes
unit: '15'
minutes: 360
tool: powerbi
figures:
  - id: IF-15-0-A
    kind: diagram
    purpose: What each tutorial adds to the model and where each exercise attaches, so an instructor sees the build at a glance.
    shows: "Left to right: the Chapter 14 report, Tutorial 15.1 (promotions and the Steps table, three hidden detail pages), Tutorial 15.2 (the budget as a second fact table, the flexed budget, the cost-center detail page), Tutorial 15.3 (labor time and completions, the plant page, the About page and navigator). Below the line, the six exercises as branches, each labeled with the page or tab it adds."
    data: None; the boxes cite the tutorials, the exercises and the model answer's pages and tabs.
  - id: IF-15-0-B
    kind: pbi-mock
    purpose: Model view of the model answer, with the five fact tables around the shared Date table.
    shows: "Model view with SalesInvoiceLine, GLEntry, BudgetLine, LaborTimeEntry and ProductionCompletionLine as fact tables around Date; Account, CostCenter, Item, Customer, PromotionProgram, Employee and WorkCenter as dimensions; LaborPaths related to Date; and Steps, Discount and Plant Measure standing alone with no lines. Each line shows 1 at the dimension and an asterisk at the fact table."
    data: None; the tables and relationships of the model answer.
  - id: IF-15-0-C
    kind: diagram
    purpose: What the Checks tab proves in each item and what only Desktop shows, the map an instructor needs before grading.
    shows: "A two-column board. Left, proved by the Checks tab: the entries and amounts of Exercise 15.1, the monthly net income and the measure of Exercise 15.2, the three plant measures of Exercise 15.3, the lifts of Exercise 15.4, the actual quarter and the benchmarks of Exercise 15.5, the disagreement counts of Exercise 15.6. Right, visible only in Desktop: the drill-through click, the visual calculations of Exercise 15.2 and Tutorial 15.3, the field-parameter slicer, the Analytics-pane forecast."
    data: None; the Checks tab's sections and the exercises' pages.
  - id: IF-15-0-D
    kind: diagram
    purpose: A board sketch of the budget variance, from the static budget to the actual, by cause.
    shows: "A waterfall for fiscal year operating expense. Start bar, the static budget. Steps: the volume effect in the commission budget, the classification effect (drawn as an up arrow in one cost center and a down arrow of the same size in another, netting to zero), the remaining variance. End bar, the actual. A note says what the remaining variance holds: the payroll burden rate and the months with three pay dates."
    data: The Tutorial 15.2 quantities (budget, volume effect, classification effect, remaining, actual), from the generated note.
---
{% set t1 = ch15_t1 %}
{% set t2 = ch15_t2 %}
{% set t3 = ch15_t3 %}
{% set e2 = ch15_ex2 %}
{% set mq = ch15_mcq %}
{% set rest = t2.centers|rejectattr('name', 'in', [t2.sales.name, t2.to.name, t2.frm.name, '(Blank)'])|list %}
{% set sales_c = (t2.centers|selectattr('name', 'equalto', t2.sales.name)|first) %}
{% set wh_c = (t2.centers|selectattr('name', 'equalto', t2.to.name)|first) %}
{% set ad_c = (t2.centers|selectattr('name', 'equalto', t2.frm.name)|first) %}
# Chapter 15: Reports for Management Decisions

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part IV, Accounting Analytics with Power BI: the third of four chapters. It turns Chapter 14's model into a reporting package that Chapter 16, the appendix on publishing and security and the Part IV case build on |
| Analytics types | Descriptive and diagnostic throughout (reports, variances, drill-through to causes); the what-if parameter and the forecast are the chapter's first prescriptive and predictive tools |
| Tools | Power BI Desktop {{ version }} on Windows, reading CharlesRiver.xlsx: Report view, Model view, Power Query, DAX query view |
| Components | {{ unit.tutorials|length }} guided tutorials ({{ steps[1] }}, {{ steps[2] }} and {{ steps[3] }} steps) that extend Charles River Reports.pbix, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.xlsx. Chapter15-companion.zip holds Charles River Reports, a Power BI project, at the start of Tutorials 15.1, 15.2 and 15.3 and at the end of the chapter. Chapter15-exercises-pbi.zip holds the model answer |
| Time | Class: about 360 minutes. Students: about 100 minutes of reading, 60 to 120 for each tutorial and 60 to 100 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- {{ t1.promotions }} promotions, three a year. The largest of fiscal {{ y }}, {{ t1.top.label }}, gave ${{ t1.top.discounts|money }} on {{ t1.top.lines|count }} lines, and {{ t1.odd.label }} ends ({{ t1.odd.end }}) before it starts ({{ t1.odd.start }}).
- The budget plans {{ static_ratio|num(1) }} times the product revenue actually billed, so only the operating expense lines are comparable. Depreciation is budgeted in {{ t2.frm.name }} and recorded partly in {{ t2.to.name }}, ${{ t2.dep.cls|money }} each way.
- Payroll is recorded on the pay date, so the two months with three pay dates, {{ t2.above|join(" and ") }}, run above the flexed budget and every other month below it.
- The time records end {{ t3.last }}, before the year does, and the Date table runs to the end of {{ n }}. A trailing figure without a year filter is blank for that reason.

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

- Students need Windows and Power BI Desktop {{ version }} (**Help > About**). A Mac student works in a lab or a virtual machine, as in Chapter 13.
- Do the three tutorials yourself in order and save Charles River Reports.pbix. Tutorial 15.3 loads the labor time and the completions, tens of thousands of rows, so its refresh takes several minutes: tell students to start it before a break.
- A student who lacks the Chapter 14 report, or falls behind, takes Charles River Reports from Chapter15-companion.zip, from the folder of the tutorial they start. Its README gives the steps: open the .pbip, point the queries at CharlesRiver.xlsx (**Home > Transform data > Data source settings > Change Source**), choose **Home > Refresh**, and **File > Save as** a .pbix.
- Tell students to save a copy after Tutorial 15.3, such as `Ch15 Exercises.pbix`, for the exercises: one page or query tab and one display folder of measures for each.
- Open the model answer once. Its visible pages are About through Income Statement (the earlier chapters), then Promotions, Budget and Plant. It also holds the hidden pages Promotion Detail, Promotion Tooltip, Cost Center Detail and Ledger Detail, the visible pages Ex 15.2 to Ex 15.6 and Notes, and the DAX query tabs Tests, Ex 15.1 and Checks. After **Home > Refresh**, **Run** on the Checks tab tests {{ n_checks_mine }} values of the chapter's tutorials and exercises ({{ n_checks }} in all).
- The Checks tab cannot read what a visual computes: the visual calculations and the forecast. Compare those by eye on the pages.
- Separate Build and Format panes in place of Visualizations mean the on-object interaction preview is on. The tutorials describe the default panes.

**Pitfalls that cost class time**

- **The drill-through field.** It must also be a field of the visual the reader right-clicks, or the option does not appear (Tutorial 15.1, Step 7).
- **Ctrl.** In Desktop a button responds only with Ctrl held: the back button of a drill-through page and every navigator button.
- **No operating expense filter.** The budget matrix then includes revenue and cost of goods sold, whose static budget (${{ t2.rev|money }} and ${{ t2.cogs|money }}) says nothing about the year.
- **Edit interactions.** Forgotten in Tutorial 15.3 Step 11, a click on {{ t3.top_center }} shows {{ t3.wrong|num(2) }} on the card in place of {{ t3.card|num(2) }}.
- **KEEPFILTERS.** Without it Direct Hours reads {{ manufacturing_hours|num(0) }} for fiscal {{ y }} in place of {{ direct_hours|num(0) }}.
- **The forecast.** Desktop computes it, so a new release can move it. Do not hand students a number to match.

{{ figure('IF-15-0-B') }}

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

{{ figure('IF-15-0-A') }}

## Tutorial guide

### Guided Tutorial 15.1: The Promotions Page

**Purpose.** Students build the sales manager's page: a waterfall from list price to net, the discounts by promotion, and two detail pages. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Step 4 (SELECTEDVALUE and SWITCH on a table that relates to nothing), Step 7 (the drill-through well) and Step 8 (the tooltip page). Leave Steps 1 to 3, 5, 6 and 9 to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | The promotions, related | {{ t1.promotions }} promotions; {{ t1.no_promo|count }} of {{ t1.lines|count }} lines have none and sit under (Blank) |
| 3 to 5 | The waterfall, fiscal {{ y }} | list ${{ t1.list|money }}; price lists and overrides -${{ (t1.step2|abs)|money }}; promotions -${{ (t1.step3|abs)|money }}; total ${{ t1.revenue|money }} |
| 6 | Discounts by promotion | {{ t1.top.label }} ${{ t1.top.discounts|money }} on {{ t1.top.lines|count }} lines, several times any other |
| 7, 9 | The detail page | {{ t1.top.label }} runs through months after its end date; {{ t1.odd.label }} ends ({{ t1.odd.end }}) before it starts ({{ t1.odd.start }}) |
| 8 | The tooltip | the promotion's months, shown while pointing |

**Stumbles to expect**

- Step 2: DiscountPct left to sum. The detail page then adds the rate. Set **Don't summarize** (Step 2d).
- Step 4: the promotions step typed as the Discounts measure with its sign changed. The steps then miss the total by ${{ t1.rounding|money }}, the rounding of the lines.
- Step 7: the field dragged with a visual selected, so it joins the visual and the well stays empty.
- Step 8: the tooltip page switched on in one place only. It needs the page's type and the tooltip switch, and the visual's own tooltip setting.
- Step 9: the back button clicked without Ctrl.

**The checkpoint to look for.** The three bullets. A strong student says the promotions are the smaller of the two reductions from list price.

### Guided Tutorial 15.2: The Cost-Center Budget Page

**Purpose.** Students add the budget as a second fact table, compare it with the ledger, and explain the variances. **Time.** About 90 to 105 minutes. **Demonstrate, then hand over.** Demonstrate Step 6 (read the flexed budget a variable at a time), Step 9 (the reconciliation) and Step 10 (RUNNINGSUM). Leave Steps 1 to 5, 7, 8 and 11 to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | The budget related by month, account and cost center | BudgetDate, the first day of each month, related to Date |
| 3, 4 | Operating expense, fiscal {{ y }} | budget ${{ t2.opex|money }}; actual ${{ t2.actual|money }}; {{ t2.sales.name }} {{ sales_c.pct|spct }}, {{ t2.to.name }} {{ wh_c.pct|spct }}, {{ t2.frm.name }} {{ ad_c.pct|spct }}; the others {{ (rest|map(attribute='pct')|min)|spct }} to {{ (rest|map(attribute='pct')|max)|spct }} |
| 5 | Icons | arrows on the three outliers, a circle elsewhere |
| 6, 7 | The flexed budget | flexed commission ${{ t2.flexed_com|money }}; flexed operating expense ${{ t2.flexed_total|money }} |
| 8 | The drill-through | {{ t2.to.name }}: depreciation with no budget; {{ t2.frm.name }}: a budget above its actual |
| 9 | The reconciliation | volume -${{ (t2.volume|abs)|money }}; classification {{ t2.dep.to }} +${{ t2.dep.cls|money }}, {{ t2.dep.frm }} -${{ t2.dep.cls|money }}; remaining -${{ (t2.remaining|abs)|money }} |
| 10 | The running variance | above the flexed budget only in {{ t2.above|join(" and ") }} |
| 11 | Test 4 | ${{ t2.opex|money }}; ${{ t2.flexed_total|money }}; ${{ t2.actual|money }} |

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
| 1 to 4 | The plant Tables, related | {{ t3.rows|count }} labor lines, {{ t3.matched|count }} direct lines with an operation; {{ t3.completions|count }} completion lines for {{ t3['items'] }} items |
| 5, 6 | Hours, output, ratio, by year | {% for t in t3.tests %}{{ t.year }}: {{ t.hours|num(0) }} hours, {{ t.standard|num(0) }} standard hours, {{ t.ratio|num(2) }}{{ "; " if not loop.last else "" }}{% endfor %} |
| 7 | The trailing measure | {{ t3.ttm[0][0] }} {{ t3.ttm[0][1]|num(2) }} to {{ t3.ttm[-1][0] }} {{ t3.ttm[-1][1]|num(2) }}; blank before twelve months |
| 8, 9 | The visual calculation | on an axis from January of the prior year it reads {{ t3.visual[0]|num(3) }}, the measure {{ t3.ttm[1][1]|num(3) }}; equal from December |
| 10 | The card | {{ t3.card|num(2) }} beside the first year's {{ t3.first|num(2) }}; blank with no year filter |
| 11 | Work centers, job titles | {{ t3.top_center }} first with {{ t3.centers[0][1]|num(1) }} direct hours |
| 12, 13 | About page; Test 5 | Test 5 returns the three yearly ratios; saved on About |

**Stumbles to expect**

- Step 3: **Load** in place of **Transform Data**, and a refresh abandoned because it is slow.
- Step 3d: the Item query's **Choose Columns** reopened from the wrong step.
- Step 5: KEEPFILTERS missing. Direct Hours reads every manufacturing hour.
- Step 6: Standard Hours without the cut-off, which overstates the last year's output.
- Step 9: the table's year filter not changed, so the two columns agree and the lesson is lost.
- Step 11c: Edit interactions skipped, so a click on {{ t3.top_center }} shows {{ t3.wrong|num(2) }}.
- Step 12: a measure without a description, or the navigator tested without Ctrl.

**The checkpoint to look for.** The four bullets. A strong student says why the card ignores the work-center chart: the output has no work center.

## Difficult ideas and misconceptions

**A drill-through passes the whole data point.** Tutorial 15.1 Step 9, Exercise 15.1 (5), questions 3 and 4. Students think the page filters itself. Ask: what does the page show if the click came from the row's label?

**A variance is a difference, not a cause.** Tutorial 15.2, questions 7 to 9. {{ t2.sales.name }} reads {{ sales_c.pct|spct }} and looks like thrift; the commission budget was built on a volume that never came. Ask: what was the budget built on?

{{ figure('IF-15-0-D') }}

**A classification effect nets to zero.** Question 9. It moves cost between cost centers: ${{ t2.dep.cls|money }} each way, so it explains none of the company's total. Ask: what is the total of the column?

**Timing hides in a year-to-date.** Tutorial 15.2 Step 10. The running variance stands at ${{ t2.ytd[6]|money }} in July, close to the flexed budget, because {{ t2.above|join(" and ") }} run above it and the months between run below it. A manager who read the report in July saw a cost center on budget. Ask: which months are above it, and why?

**A visual calculation sees only its visual.** Tutorial 15.3 Step 9, Exercise 15.2 (3), question 10. On an axis that starts a year in, the first month averages one month: {{ mq.visual|num(3) }} against the measure's {{ mq.measure|num(3) }}. Ask: which rows can it see?

**KEEPFILTERS combines, a filter argument replaces.** Question 12. Ask: what does the inner filter do to the outer one?

**A ratio needs its denominator at the same grain.** Tutorial 15.3 Step 11c. Hours belong to a work center and output does not. Ask: what is the output of one work center?

**A forecast is a model, not data.** Exercise 15.5, question 15. It cannot be read from the model and moves with the history. Ask: which quarter do you already know?

**Two records of one fact.** Exercise 15.6. They agree most of the time and differ where the audit questions are. Ask: what does each record measure?

## Discussion prompts

1. **The controller wants one KPI for every department. What do you say?** It reaches Lipe and Salterio: shared measures defined alike, unique measures kept and flagged as counting.
2. **Where should the threshold of an icon come from?** It reaches the five percent as the package's choice, stated on the page, and Cardinaels and van Veen-Dirks on markers changing weights.
3. **Should the budget page show revenue against the static budget?** It reaches the static-budget trap, flexing, or leaving it off with a stated reason.
4. **A manager reads the report in July and sees the cost center on budget. What happened?** It reaches three pay dates, recorded when paid, and the months between.
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

{{ figure('IF-15-0-C') }}

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 2.** Option D says all measures weighed equally, the opposite of the finding; option A inverts it.
- **Question 6.** Option B copies the budget to every day and overstates it by the days in each month; the guidance stores the first day.
- **Question 7.** Option A takes the variance as budget less actual, the opposite of the convention the text sets.
- **Question 9.** Option A: classification explains none of the total. Option C confuses it with timing.
- **Question 10.** Option D: the calculation averages the months it has, {{ mq.visual|num(3) }} against {{ mq.measure|num(3) }}.
- **Question 12.** Option A sounds like a model problem. It is the inner filter replacing the outer one.
{% if n_longest %}
- **Length.** The correct option is also the longest in {{ n_longest }} of the {{ n_questions }} questions ({{ longest_correct }}), so wording alone can give it away. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 4 make a quiz on design and detail pages, 5 to 9 on the budget, 10 to 13 on visual calculations, filters and navigation, and 14 and 15 on parameters and forecasts.

## Connections

**Builds on.** Chapter 1's promise of drill-down to causes; Chapter 2's warning about a budget and a ledger that classify a cost differently; Chapter 4's Documentation worksheet, here the About page; Chapter 6's bridge; Chapter 7's flexible budget, benchmarks and break-even lift; Chapters 10 to 12's plant measure, three pay dates and late time; Chapter 13's Validation page; and Chapter 14's model, DAX, the closes and KEEPFILTERS.

**Later chapters.** Chapter 16 monitors exceptions with the same model and audits the package itself: its tests, its currency and its change control. The Part IV case builds a new report with the same package structure.

**Appendices.** The appendix on publishing and security gives each department manager only their cost center and publishes the package. The appendix on Power BI in the browser rebuilds Chapter 13's model there. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
