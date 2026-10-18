---
note: ch06.chapter
uses: [ch06.ex1, ch06.g1, ch06.g5]
title: 'Chapter 6: Descriptive and Diagnostic Analytics in Excel'
kind: chapter-notes
unit: '6'
minutes: 180
tool: excel
figures:
  - id: IF-06-0-A
    kind: diagram
    purpose: The revenue ladder of the chapter, from the invoice lines of the Profile worksheet to the net revenue of the income statement.
    shows: "A vertical ladder of four boxes joined by arrows, each box holding a label and an amount: invoice lines of the report year (the Profile control total), product revenue accounts, operating revenue, net revenue. Each arrow carries its signed adjustment: the three cutoff invoices, freight revenue (account 4050, no invoice line) and sales returns (account 4060)."
    data: Invoice lines total, cutoff invoices, freight revenue and returns, from the Expected results of Exercises 6.1 and 6.2.
  - id: IF-06-0-B
    kind: diagram
    purpose: Why a calculated field cannot multiply two fields, and what to do instead.
    shows: "Two panels with the same three invented lines (quantity and unit price). Left, a calculated field Quantity*UnitPrice: the quantities are added, the prices are added, and the two sums are multiplied, giving a number marked wrong. Right, a custom column in the source: each line is multiplied first and the PivotTable adds the products, giving a number marked correct."
    data: Three invented round-number lines, labeled as an illustration and not Charles River values.
  - id: IF-06-0-C
    kind: chart
    purpose: The same change in the Furniture margin decomposed at two levels, for the discussion of Exercise 6.4.
    shows: "A grouped bar chart. The horizontal axis holds the effects volume, mix, price and cost; each group has two bars, Furniture as a whole (Tutorial 6.3, price as price lists plus promotions) and product type by product type (Exercise 6.4). The value axis starts at zero, bars carry signed dollar labels, and the Furniture-level cost bar is labeled zero."
    data: The effects of Tutorial 6.3 and of Exercise 6.4 (the Expected results of Exercise 6.4).
---
# Chapter 6: Descriptive and Diagnostic Analytics in Excel

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part II, Accounting Analytics with Excel: the third Excel chapter. It takes the InvoiceLines table of Chapter 5 and answers the question that opened Part I: why did the Furniture margin fall? |
| Analytics types | Descriptive (statistics, conditional totals, PivotTables, the statements) and diagnostic (drill down, compare, decompose with a margin bridge) |
| Tools | Excel with Power Query: statistical functions, SUMIFS and its family, FILTER, PivotTables with calculated fields, GETPIVOTDATA, PivotCharts, a waterfall chart. No SQL or Power BI |
| Components | {{ unit.tutorials|length }} guided tutorials, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.xlsx, never edited, and Charles River Furniture Analysis.xlsx as it stands at the end of Chapter 5. Chapter06-companion.zip holds the workbook at the start of each tutorial and at the end of the chapter, and Chapter06-exercises.zip the model answers (Chapter 6 Exercises - Solutions.xlsx). The companion files read `C:\CharlesRiver\CharlesRiver.xlsx` |
| Time | Class: about 180 minutes. Students: about two hours of reading, 45 minutes for Tutorial 6.1, 60 for Tutorial 6.2, 60 for Tutorial 6.3 and 60 to 120 for each exercise (assign two or three). The tutorial times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- InvoiceLines holds {{ t1.lines|count }} lines for fiscal {{ y }}, billing ${{ t1.revenue|money }}, in five item groups. {{ t1.groups[4].group }} is billed by the hour ({{ t1.groups[4].lines|count }} lines) and its items carry a standard cost of 0, so its margin at standard cost is 100 percent.
- The lines are skewed to the right, as the histogram of Tutorial 6.1 shows, and the average line (${{ t1.mean|money }}) is {{ t1.ratio|num(2) }} times the median (${{ t1.median|money }}). The largest line is a design service.
- The Furniture margin at standard cost falls from {{ t2.margin_q[0][2]|pct(2) }} in the third quarter to {{ t2.margin_q[0][3]|pct(2) }} in the fourth, while the other product lines stay within a point of their level. Promotional discounts more than double ({{ t3.disc_ratio|num(1) }} times) while quantity, list price and standard cost per unit barely move.
- The ledger has {{ ch06_ex1.accounts }} accounts with a pre-closing balance. Three invoices numbered for fiscal {{ y }} are dated in fiscal {{ p }}, and the ledger holds supplier payments dated after the fiscal year-end, so a trial balance needs a date filter.
- The prior-year expectation of Exercise 6.5 flags {{ ch06_g5.both|length }} of {{ ch06_g5.n_cells }} differences and misses the largest, which are Furniture's. Each exercise guide lists its own conditions.

## What students should be able to do afterward

The six outcomes follow the chapter's learning objectives in order.

1. Describe a column with statistical functions and show its shape with a histogram. Practiced in Tutorial 6.1 (Steps 3 to 5 and 8 to 9), Exercise 6.6 (requirements 1 and 2) and questions 1 to 3 and 6.
2. Calculate conditional totals and test them against a control total. Practiced in Tutorial 6.1 (Steps 3, 6 and 7), Exercises 6.1 (requirements 3 and 5), 6.5 (requirement 2) and 6.6 (requirement 1), and questions 4 and 5.
3. Build PivotTables and PivotCharts across two or more dimensions and choose a chart that fits the question. Practiced in Tutorial 6.2, Exercises 6.2, 6.3, 6.5 (requirement 1) and 6.6 (requirements 2 to 4), and questions 6 and 8 to 10.
4. Create calculated fields for margins and ratios, and explain why they work on totals. Practiced in Tutorial 6.2 (Step 3), Tutorial 6.3 (Step 3), Exercise 6.3 (requirement 1) and question 7.
5. Explain a change by drilling down, comparing and decomposing it into volume, mix, price and cost effects, and communicate the finding. Practiced in Tutorial 6.3, Exercises 6.4 and 6.5, the memos and paragraphs of every exercise, and questions 13 to 15.
6. Build a pre-closing trial balance and a common-size income statement from the ledger. Practiced in Exercise 6.1 and questions 11 and 12.

## Preparing to teach

**Before the first class**

- Students need a supported desktop Excel with Power Query, Microsoft 365 recommended, as the Preface's What You Need says. On a Mac the Power Query Editor needs Excel for Microsoft 365. FILTER is in Excel for Microsoft 365, Excel 2024 and Excel 2021, whose support ended in October 2026. The model answers also use CHOOSECOLS, HSTACK, TAKE and SORTBY, so open them in Microsoft 365 or Excel 2024.
- Each tutorial begins from the previous one's workbook. A late student takes the start file from Chapter06-companion.zip, points its queries at their copy of CharlesRiver.xlsx (**Data > Get Data > Data Source Settings**, **Change Source**) and chooses **Data > Refresh All**.
- Do the three tutorials yourself and time them. Tutorials 6.2 and 6.3 build several PivotTables on the InvoiceLines Table of {{ lines_all|count }} rows, so time the refreshes on your students' machines.
- Get the PowerPoint deck from the Downloads page; its modules follow the chapter's sections.
- Run Exercise 6.1's Group By once. It reads the whole GLEntry Table ({{ ch06_g1.rows_all|count }} rows): students use **Transform Data**, never **Load**, and filter before they group.

**Pitfalls that cost class time**

- **Two filters on the year.** The report year in Tutorial 6.1 is a named cell. A PivotTable has its own FiscalYear filter, and changing the parameter does not change it. Students who "update the year" see the Profile worksheet move and the PivotTables stay. A new PivotTable does not inherit another's selection either, so each exercise PivotTable needs the year selected.
- **The Data Model box.** A PivotTable created with **Add this data to the Data Model** checked has no **Calculated Field** command.
- **The shared pivot cache.** Calculated fields belong to the pivot cache, so MarginPct appears in every PivotTable built from the InvoiceLines Table. A PivotTable built from a pasted range does not have it, and a student who lacks it recreates the field.
- **Σ Values.** A second value field sends **Σ Values** to the Columns area. Dragging it to Rows is a step the tutorials give once, and students forget it in the exercises.
- **GETPIVOTDATA reads what the PivotTable shows.** The Bridge returns Furniture totals only while the ItemGroup filter says Furniture. A plain cell reference means **PivotTable Analyze > Options > Generate GetPivotData** is off.
- **Refresh after the query.** A new query column may need a second **Refresh All** once the query has finished loading, because background refresh can update a PivotTable before its query ends. A second click while the query still runs repeats the problem.
- **Load To.** In Exercise 6.1 **Only Create Connection** applies to both new queries, so TrialBalance is loaded afterward from **Data > Queries & Connections**.

## Teaching approaches

**Plan A: lecture with live demonstration (two sessions of 90 minutes, 180 minutes in all).** It fits a lecture course with a projector and home time for the tutorials. You demonstrate the steps that carry the ideas and leave the rest to students.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The three requests, the objectives, descriptive and diagnostic analytics | 2 to 7 |
| 1 | 20 | Statistics: mean against median, spread, FILTER, the Watch out | 8 to 12 |
| 1 | 15 | Conditional totals fail silently; the check and the answer | 13 to 16 |
| 1 | 10 | Choosing and designing a chart | 17 to 20 |
| 1 | 35 | Tutorial 6.1: Steps 3, 4, 6 and 7 live; students finish at home | 21 to 26 |
| 2 | 15 | PivotTables: the four areas, calculated fields, Show Values As, the check and the answer | 27 to 34 |
| 2 | 20 | Tutorial 6.2: Steps 2 to 4 live | 35 to 39 |
| 2 | 15 | The ledger to the statements | 40 to 44 |
| 2 | 15 | Diagnosis, the bridge, the check and the answer | 45 to 50 |
| 2 | 20 | Tutorial 6.3: Steps 3, 5 and 6 live | 51 to 55 |
| 2 | 5 | Interpreting results; looking ahead; assign the exercises | 56 to 64 |
| | 180 | Total | |

**Plan B: lab first (one session of 150 minutes).** Students build the workbook before the vocabulary, so the control total and the bridge arrive as results they produced. It fits a computer lab. Students work in pairs and take the next start file when they fall behind. The tutorials take about 165 minutes in full against the 110 the plan gives the builds, so students prepare before class or finish at home, and the session does not promise that first-time users complete every step. The ledger section is not covered: assign Exercise 6.1 for the next session.

| Minutes | Activity | Slides |
|---|---:|---|
| 5 | Pose the controller's three requests; ask what a good profile of a year's lines would contain | 5 |
| 35 | Tutorial 6.1 in pairs, to the checkpoint | 21 to 26 |
| 10 | Debrief: mean against median, the silent zero, the control total | 9 to 16 |
| 35 | Tutorial 6.2 in pairs, to the checkpoint | 35 to 39 |
| 10 | Debrief: four areas, calculated field, Show Values As | 28 to 34 |
| 40 | Tutorial 6.3 in pairs, to the checkpoint | 51 to 55 |
| 10 | Debrief: what each effect means and what the finding claims | 46 to 50, 57 to 58 |
| 5 | Assign the exercises | 63 |
| 150 | Total | |

**Plan C: flipped, with one 75-minute class.** Students read the chapter and build the three tutorials at home. It fits upper-level and graduate classes and depends on prepared students, so it opens with a quiz.

| Minutes | Activity | Slides |
|---|---:|---|
| 10 | Quiz on questions 1, 4, 5, 7, 11 and 13 | |
| 15 | Review clinic: partners swap workbooks and check the control total on the Profile worksheet and the Check cell of the Bridge worksheet | 24, 55 |
| 20 | Break it: a SUMIFS with a misspelled criterion, a calculated field that multiplies two fields, a PivotTable of the ledger with the closing entry left in | 14, 30, 32 |
| 20 | Start Exercise 6.1 or 6.5 in pairs | |
| 10 | Discussion prompts 1 and 3; assign the exercises | 60, 63 |
| 75 | Total | |

Plan A is the safest. Plan B trades the lecture for ownership of the workbook and needs a lab. Plan C leaves no time for demonstration.

## Tutorial guide

### Guided Tutorial 6.1: Profiling Fiscal {{ y }} and Checking the Total

**Purpose.** Students profile a year of invoice lines with statistics, catch a missing category with a control total, and draw the distribution.

**Time.** About 45 minutes.

**Demonstrate, then hand over.** Demonstrate Step 4 (MEDIAN of FILTER) and Step 7 (the Services row and the SUM range that does not grow). Leave Steps 8 and 9 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 3, 4 | Count, total, average, median, spread, 90th percentile | {{ t1.lines|count }} lines; ${{ t1.revenue|money }}; ${{ t1.mean|money }}; ${{ t1.median|money }}; ${{ t1.stdev|money }}; ${{ t1.p90|money }} |
| 5 | The extremes | Smallest ${{ t1.smallest|money }}; largest ${{ t1.largest|money }}, {{ t1.big_name }} ({{ t1.big_code }}), {{ t1.big_hours|num(2) }} hours |
| 6 | The four product lines against the control total | Differences of -{{ (t1.groups[4].lines)|count }} lines and -${{ t1.groups[4].revenue|money }} |
| 7 | Services added; both differences zero | Services: {{ t1.groups[4].lines|count }} lines, ${{ t1.groups[4].revenue|money }} |
| 8, 9 | The bins and the chart | First bin {{ t1.bins[0]|count }}, last bin {{ t1.last_bin|count }}, total {{ t1.lines|count }} |

**Stumbles to expect**

- Step 1: the name typed in the cell, not the **Name Box**, so ReportYear is undefined and every formula errors.
- Step 4: a FILTER with no match returns #CALC!.
- Step 6: a group name typed with a stray space, so SUMIFS returns zero for that row. Also C17 without ROUND, which can read -0.00 because of a residue below a cent.
- Step 7: the SUM ranges still end at the old last row, so the differences stay nonzero after Services is added. That is the lesson of the step.
- Step 8: the open-ended last bin formula missing, so the bins do not add up.

**The checkpoint to look for.** The four bullets. A strong student says why the average is above the median (a right skew: a minority of large lines) and changes ReportYear to {{ p }} to see {{ t1.prior_lines|count }} lines and ${{ t1.prior_revenue|money }}.

### Guided Tutorial 6.2: Revenue and Margin by Product Line and Quarter

**Purpose.** Students build PivotTables from InvoiceLines, define a margin as a calculated field and describe the Furniture decline.

**Time.** About 60 minutes. The three PivotTables take longest.

**Demonstrate, then hand over.** Demonstrate Step 3 (the calculated field and Σ Values) and Step 5 (% Difference From with (previous)). Leave Steps 6 and 7 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2 | RevenuePivot against Tutorial 6.1 | Grand total ${{ t1.revenue|money }}, equal to Profile!B3 |
| 3, 4 | Furniture margin, third and fourth quarter | {{ t2.margin_q[0][2]|pct(2) }} and {{ t2.margin_q[0][3]|pct(2) }}; the other product lines move by under a point across the year; Services 100 percent |
| 5 | Share and change | Furniture's share of the quarter {{ t2.share3|pct(1) }} then {{ t2.share4|pct(1) }}; its revenue {{ t2.furniture_change|spct(1) }}; the first quarter blank |
| 6 | SegmentPivot against the year before | {{ t2.segments[0].segment }} {{ t2.segments[0].change|spct(2) }}; total {{ t2.total_change|spct(2) }} |
| 7, 8 | MarginChart; refresh | Four lines, Furniture lowest and falling; totals unchanged after **Refresh All** |

**Stumbles to expect**

- Step 2: the FiscalYear filter left on (All), so every total is the three-year sum.
- Step 3: Σ Values left in Columns, so the margin sits beside the revenue and not under it.
- Step 5: % Difference From with the wrong base. Period is the base field and (previous) the base item.
- Step 6: the first year left in the Column Labels, so the change column also compares the middle year with it.
- Step 4: margins that differ slightly from the Part I case's. The case measured the posted accounts, whose cost is the standard cost of the goods shipped less the goods returned, and this PivotTable the standard cost of the quantities invoiced. Both fall.
- Step 7: MarginPct missing from the field list because the PivotChart was built from a copied range.

**The checkpoint to look for.** The five bullets. A strong student explains the 100 percent Services margin as an absence of standard cost, not as a finding, and says that the other product lines held steady.

### Guided Tutorial 6.3: Explaining the Furniture Margin

**Purpose.** Students decompose the change in the Furniture margin, tie it to the change with a check cell, chart it as a waterfall and name the promotions behind it.

**Time.** About 60 minutes. The driver PivotTable and the bridge take longest.

**Demonstrate, then hand over.** Demonstrate Step 4 (GETPIVOTDATA by clicking) and Step 5 (the formulas and the check). Leave Steps 6 and 7 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2, 3 | Quantity, per-unit measures and margins, third then fourth quarter | {{ t3.q3.U|num(2) }} then {{ t3.q4.U|num(2) }} units; price per unit ${{ t3.q3.price|money }} then ${{ t3.q4.price|money }}; discounts ${{ t3.q3.D|money }} then ${{ t3.q4.D|money }}; margin before discounts {{ t3.q3.mbd|pct(2) }} then {{ t3.q4.mbd|pct(2) }} |
| 4, 5 | The bridge | Margin ${{ t3.q3.M|money }}; volume +${{ t3.effects.volume|money }}; mix -${{ (t3.effects.mix|abs)|money }}; price lists +${{ t3.effects.price_lists|money }}; promotions -${{ (t3.effects.promotions|abs)|money }}; cost 0; margin ${{ t3.q4.M|money }}; B23 reads zero and C23 reads PASS |
| 7 | Discounts by promotion | Promotion {{ t3.main }} in both quarters ({{ t3.promos[t3.main][3][0]|count }} then {{ t3.promos[t3.main][4][0]|count }} lines), promotion {{ t3.nine }} in the fourth quarter only |

**Stumbles to expect**

- Step 2: the grand totals left on, so a column that adds the two quarters sits among the values.
- Step 4: a typed cell reference instead of the click. The formulas name the period and not the item group, so they read the Furniture filter.
- Step 5: a bridge formula that points at the wrong quarter's column, which B23 shows as a nonzero check and C23 as INVESTIGATE. After the test with `+0.1`, students forget to remove it.
- Step 6: the first and last bars not set as totals, so the waterfall climbs from zero and shows no decline.
- Step 7: SalesInvoiceLineID summed instead of counted.

**The checkpoint to look for.** The four bullets. A strong student says that the promotions effect (${{ (t3.effects.promotions|abs)|money }}) is larger than the whole decline (${{ (t3.change|abs)|money }}) because the other effects net to a small gain, and that the bridge measures what the discounts cost, not whether the promotion was wise.

## Difficult ideas and misconceptions

**The mean is not the typical line.** Question 1 tempts with "symmetric" and with "errors". Ask: what would the average tell a reader who never sees the lines? It falls between the small accessories lines and the large design-service lines and resembles neither.

**A calculated field works on totals.** Question 7's option A, a formula applied to each row, is the intuitive wrong answer. Tutorial 6.2 adds StdCostAmount in the source for that reason.

{{ figure('IF-06-0-B') }}

**A control total shows coverage, not accuracy.** A difference of zero means the parts add up to the whole of the same source, not that the source is right, and a SUM range that does not grow after a row is inserted defeats it (Step 7). Question 4's option D is the silent zero, and question 14's rising margin before discounts shows that the larger discounts more than offset the other effects, which on balance raised the margin.

**A PivotTable summarizes a copy, with its own filters.** Question 10 and the two-filters pitfall have one cause: the pivot cache refreshes only on request, and its FiscalYear filter is not ReportYear.

**A balanced trial balance is not a complete one.** Equal balances, and net income equal to the closing entry, test arithmetic. The extract holds {{ ch06_g1.rows_next|count }} rows dated after the fiscal year-end, and the ledger balances with or without them, so only the date filter protects the result (questions 11 and 12). Ask: which check would have caught an unfiltered extract?

**Which date decides the period?** In Exercise 6.1 the ledger exceeds the invoice lines by ${{ ch06_ex1.recon[0].diff|money }} in account {{ ch06_ex1.recon[0].account }} and two smaller amounts, because three invoices are dated in the earlier year. Students pick the invoice date or the number. The answer is delivery, when control passes, and only one of the three was delivered in the earlier year. The shipment dates fall in the same years here, but the delivery date is the evidence.

{{ figure('IF-06-0-A') }}

**The cost effect is zero by construction.** Every unit carries one standard cost, so a Furniture-level bridge cannot show a cost effect (question 13). A product-type bridge shows one, because the items sold change (Exercise 6.4). Ask: is the cost effect a finding or a consequence of the level?

{{ figure('IF-06-0-C') }}

**An expectation that is the prior year.** Question 15's option C is copying last year's revenue without considering known changes or the reliability of the data, yet Exercise 6.5 uses last year as a deliberately simple expectation and names its weakness. The question concerns what the auditor must do first: develop the expectation and set the acceptable difference in advance. The weakness is the unexamined shortcut, not prior-year data.

## Discussion prompts

1. **The sales manager asks for the typical invoice line. Which number do you give?** A good discussion reaches the median for a typical line, the mean for totals and planning, and the group-by-group profile of Exercise 6.6.
2. **A control total difference is zero. What can still be wrong?** It reaches an error both totals share, offsetting misclassifications and the cutoff of Exercise 6.1.
3. **The Furniture volume was steady, so why did the margin fall?** It reaches price, promotions and the margin before discounts, and the bridge as the control total of the explanation.
4. **The bridge says the promotions cost ${{ (t3.effects.promotions|abs)|money }} of margin. Was it a mistake?** It reaches the bridge measuring cost and not benefit, the lift the promotion may have produced, and Chapter 7's break-even analysis.
5. **Which date should decide the period of the three invoices dated in fiscal {{ p }}?** It reaches transfer of control, delivery as evidence and the shipment records.
6. **You present the bridge for Furniture, and the sales team wants it by product type. Which goes in the report?** It reaches stating the level and its convention, a headline at the level where cost is zero and mix works item by item, and detail for the people who plan the assortment.
7. **When is last year a good expectation for this year?** A stable business with known changes adjusted, and never when a promotion or a price change falls in only one of the years.
8. **A PivotTable shows Services at 100 percent. What do you tell the vice president of sales?** It reaches the missing standard cost, the two possible cost definitions of Exercise 6.3, and stating the definition.

## Using the exercises

All six exercises are Excel builds with a model answer in the workbook of Chapter06-exercises.zip, one worksheet or more per exercise. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 6.1 From the Ledger to the Income Statement | Financial | Excel | 120 | Advanced | 6, 2, 5 |
| 6.2 Disaggregating Revenue by Segment and Product Line | Financial | Excel | 75 | Intermediate | 3, 5 |
| 6.3 Product-Line Profitability at Standard Cost | Managerial | Excel | 60 | Basic | 3, 4 |
| 6.4 The Margin Bridge by Product Type | Managerial | Excel | 90 | Advanced | 5, 4 |
| 6.5 A Substantive Analytical Procedure on Quarterly Revenue | Auditing | Excel | 60 | Intermediate | 3, 5 |
| 6.6 A Descriptive Profile of the Revenue Population | Auditing | Excel | 90 | Intermediate | 1, 2, 3 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 6.1 and 6.2, managerial students 6.3 and 6.4, auditing students 6.5 and 6.6. A swap lets each track hear the others; Exercise 6.4 is worth presenting to everyone.
- *One exercise a session.* Take them in the order 6.3, 6.2, 6.5, 6.6, 6.4, 6.1, from the lightest to the longest.
- *A light load.* Exercises 6.3 and 6.5 take about two hours and cover outcomes 3 to 5. Add Exercise 6.1 for the ledger and the control totals.

**Grading and discussion.** Each exercise guide holds a rubric. Exercises 6.3 and 6.5 suit grading from the workbook. Exercises 6.1, 6.2, 6.4 and 6.6 end in a memo or paragraph and suit class discussion. A rubric's full-credit cell asks only for what the requirement asks. Extras are named in each guide as a plus. Collect the workbook, not a screenshot.

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 1.** Option D, that accounting data should have an equal average and median, confuses a skewed population with an error.
- **Question 4.** Option A, #N/A, is what a student expects from a lookup. SUMIFS returns zero.
- **Question 7.** Option A, a formula applied row by row, is how a student reads a worksheet formula.
- **Question 11.** Option A, credit memos, is a plausible business reason. The closing entry is the cause.
- **Question 12.** Option C says the closes fall after the cutoff. They are dated December 31; the later rows are supplier payments.
- **Question 14.** Options B and C blame cost and volume, which are nearly unchanged.
- **Question 15.** Option A is the independence failure. Option C is the unexamined prior-year shortcut: Exercise 6.5 uses last year's quarter as a deliberately simple expectation and names its weakness.
{% if n_longest %}
- **Questions {{ longest_correct }}.** The correct option is also the longest. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 6 make a quiz of the functions and charts, questions 7 to 10 of PivotTables, and questions 11 to 15 of the ledger and the bridge.

## Connections

**Builds on.** Chapter 1 named the four analytics types, and the Part I case found the decline and the Furniture Seasonal Promotion. Chapter 3 showed that the database has no trial balance, so Exercise 6.1 builds one. Chapter 4 taught SUMIFS, named cells, Tables and the control total, and Chapter 5 built InvoiceLines and found the promotion lines invoiced after the end date that Tutorial 6.3 prices. Exercise 6.1 returns to the invoices of Exercise 5.2.

**Later chapters.** Chapter 7 turns from explaining to estimating, with a break-even lift for the same promotion. Chapter 8 returns to the promotion dates and the journal entries. Tutorial 12.1 tests the cutoff by delivery date for every invoice. Part III writes the PivotTable as a GROUP BY, and Part IV writes the calculated field as a measure and the bridge in DAX.

**Appendices.** The quick reference lists every Excel and Power Query function the chapter uses. **Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard; each exercise guide names the competencies it practices.
