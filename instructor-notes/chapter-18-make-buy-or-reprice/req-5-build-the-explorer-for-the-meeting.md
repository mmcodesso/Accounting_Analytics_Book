# Requirement 5: Build the explorer for the meeting (Chapters 13 to 15)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 5 |
| Perspective | Managerial accounting |
| Tools | Power BI Desktop |
| Time | About 150 minutes |
| Solution file | Chapter18-capstone-pbi.zip: Product Costs/Product Costs.pbip (pages About, Families, Concentration, Capacity, Validation and Notes; the Tests and Checks tabs in DAX query view); it reads Make Buy Reprice.xlsx from Chapter18-capstone-excel.zip |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The CFO and the production manager will want to move between families and items and between the three views while they talk. That is a report, not a workbook, and Chapters 13 to 15 taught the patterns: a model with explicit relationships, a disconnected table that switches a measure (Tutorial 15.1's Steps table), a Validation page and a Tests tab. Power BI fits because the readers explore, and the item costs come from the workbook so the two files cannot disagree. The analytics type is descriptive, with prescriptive intent.

Students can:

- load the workbook's item costs and CharlesRiver.xlsx, add a year column, relate the lines to the costs and decide how the report treats the lines with no cost (Part 1);
- write a Product Cost measure that switches on the view selected, with Margin and Margin % beside it (Part 2);
- build Families and Capacity pages, and About, Validation and Tests that tie the report to the workbook and to earlier chapters (Part 3).

**Competencies practiced.** CPA Evolution Core S1 M8 (visualization and communicating results) and BAR M10 (data models, dashboards); IMA Data Analytics and Insights (data visualization); IFAC IES 3 (b); AACSB A5 part 5.1 (Power BI).

## Before you assign

- **Files.** Power BI Desktop (Windows only), CharlesRiver.xlsx and Make Buy Reprice.xlsx with its ItemCosts Table from Requirement 4. The project reads `C:\CharlesRiver\` for both; students point the queries at their copies with **Change Source**.
- **Data conditions.** The design services have no row in ItemCosts: 439 lines in all years, $1,213,344.00 of revenue in the year. ItemCosts holds the base year's costs only, so every visual needs the year.
- **Verify first.** In DAX query view, run the Checks tab: all 209 rows of Requirement 5 and 12 of Milestone 2 agree.

## How to run it

Individual work or pairs, about 150 minutes: 30 for the model, 20 for the measures, 45 for the two pages, 35 for About, Validation and Tests, 20 for documentation. Hold back the year filter and the blank row until the totals disagree with the workbook. **Collect** the .pbix and a screenshot of the Tests tab.

![A mock of the Families page that the CFO and the production manager will use in the meeting.](../figures/chapter-18-make-buy-or-reprice/IF-18-5-A.pdf)

## Step-by-step solution

### Part 1: The model

**Step 1. Load the tables.** Choose **Home > Get data > Excel workbook**, open Make Buy Reprice.xlsx and select the ItemCosts Table; choose **Transform Data** and keep the columns the report needs. Load T17_SalesInvoiceLine and T16_SalesInvoice from CharlesRiver.xlsx the same way, and add the year with **Add Column > Custom Column**.

```
    #"Removed Other Columns" = Table.SelectColumns(#"Changed Type",{"ItemID", "ItemCode", "ItemName", "Family", "ItemGroup", "SupplyMode", "StandardCost", "Units", "Revenue", "AbsorptionCost", "TimeDrivenCost", "MarginStandard", "MarginAbsorption", "MarginTimeDriven"})
    #"Added Custom" = Table.AddColumn(#"Changed Type1", "Year", each Date.Year([InvoiceDate]))
```

The Capacity and Validation pages load the workbook's Activity, Calendar, FamilyResults, PayClass and Debits1090 Tables the same way. **Check:** 219 item rows, 27,933 invoice lines, 20,914 invoices.

**Step 2. Relate the tables.** In Model view relate the lines to the item costs on ItemID, many to one with a single direction, and the lines to the invoices on SalesInvoiceID. The Costing View table of Step 4 stays unrelated.

**Step 3. Decide the blank.** The lines with no item cost row are the design services. The model keeps them in the totals and out of the Families page: a page filter on Family, and a Validation row that shows them as (Blank). **Check:** the Checks tab's row for lines with no item cost returns 439. **Watch for:** leaving them in the margin. Services carry no standard cost, so the standard margin reads 46.89%, Chapter 14's figure, instead of 44.63%.

### Part 2: The switching measure

**Step 4. Enter the views.** Choose **Home > Enter data** and type View (Standard, Absorption, Time-driven) and Order (1, 2, 3); sort View by Order.

**Step 5. Write the measures.** In the Key Measures table, choose **Modeling > New measure** for each:

```
Revenue = SUM ( SalesInvoiceLine[LineTotal] )

Units = SUM ( SalesInvoiceLine[Quantity] )

Standard Cost = SUMX ( SalesInvoiceLine, SalesInvoiceLine[Quantity] * RELATED ( ItemCosts[StandardCost] ) )

Absorption Cost = SUMX ( SalesInvoiceLine, SalesInvoiceLine[Quantity] * RELATED ( ItemCosts[AbsorptionCost] ) )

Time-Driven Cost = SUMX ( SalesInvoiceLine, SalesInvoiceLine[Quantity] * RELATED ( ItemCosts[TimeDrivenCost] ) )

Product Cost =
SWITCH (
    SELECTEDVALUE ( 'Costing View'[View], "Standard" ),
    "Standard", [Standard Cost],
    "Absorption", [Absorption Cost],
    "Time-driven", [Time-Driven Cost]
)

Margin = [Revenue] - [Product Cost]

Margin % = DIVIDE ( [Margin], [Revenue] )

Cost per Unit = DIVIDE ( [Product Cost], [Units] )
```

**Check:** with a single view selected for the year, revenue $28,543,076.08 and margin $12,739,803.20 (Standard), $10,661,488.03 (Absorption) and $11,731,216.94 (Time-driven). **Watch for:**

- No year filter: the margin percent still looks right, 44.96% against 44.63%, but revenue is $82,927,040.29, three years against one year's costs.
- Two views or none selected: SELECTEDVALUE returns its default, so the report shows Standard without a sign. The Checks tab names it.

### Part 3: The pages and the tests

**Step 6. Build the Families page.** Page filters: the year, and Family is not blank (**Filters on this page**). Add the slicer "Costing view" with **Single select**, a matrix "Margin % and cost per unit by family and costing view, manufactured items, fiscal 2026" (item groups and families in rows, View in columns, Margin % and Cost per Unit as values, manufactured items only), a bar chart "Items ranked by margin under the costing view selected" and a table "Every finished good sold in fiscal 2026, by costing view". **Check:** FUR-TBL reads 41.3%, 30.1% and 36.8%, as in Requirement 4.

**Step 7. Build the Capacity page.** From the workbook's capacity data: a chart "Practical capacity and routing time used (hours)", a table "Capacity and its use by work center, fiscal 2026 (the total is the plant)", a matrix "Routing time used by family and work center, fiscal 2026 (hours)" and cards for the practical capacity, the routing time used, the unused capacity, the committed cost and the rate. The practical share is a typed measure, so it changes with the Assumptions value by hand:

```
Practical Share = 0.8
```

**Step 8. Add About, Validation and Tests.** About holds a text box, the last invoice date and a page navigator. Validation shows "Every invoice line by year (Chapters 13 and 14)", "Fiscal 2026 by item group: (Blank) is the design services (Chapter 6)", "Inputs to 1090, fiscal 2026 (Chapter 10)", and "Each view against the workbook's ItemCosts Table, finished goods, fiscal 2026". The Tests tab (DAX query view) runs 6 tests; this instructor check returns the time-driven margin difference and the blank-line count:

```
EVALUATE
ROW (
    "Time-driven margin less the workbook's", CALCULATE ( [Margin] - [Workbook Margin], SalesInvoice[Year] = 2026, NOT ISBLANK ( ItemCosts[Family] ), 'Costing View'[View] = "Time-driven" ),
    "Lines with no item cost row", COUNTROWS ( FILTER ( SalesInvoiceLine, ISBLANK ( RELATED ( ItemCosts[ItemID] ) ) ) )
)
```

**Check:** a difference of zero and 439 lines. The Checks tab tests the values and each view's tie to the workbook. The layout, the slicer state and how (Blank) displays show only in Desktop.

![A mock of the Tests tab in DAX query view, the check students run before they present.](../figures/chapter-18-make-buy-or-reprice/IF-18-5-B.pdf)

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Item rows; invoice lines; invoices | 219; 27,933; 20,914 | 1 |
| Finished goods revenue; items sold | $28,543,076.08; 207 | 5 |
| Margin: Standard; Absorption; Time-driven | $12,739,803.20; $10,661,488.03; $11,731,216.94 | 5 |
| Lines with no item cost; their revenue | 439; $1,213,344.00 | 3 |
| Checks that agree | 209 and 12 | 8 |

> **Instructor notes, Requirement 5 (CR18 reference model in Desktop 2.158, through the local engine):** Product Cost = SWITCH ( SELECTEDVALUE ( 'Costing View'\[View\], "Standard" ), "Standard", \[Standard Cost\], "Absorption", \[Absorption Cost\], "Time-driven", \[Time-Driven Cost\] ), each cost a SUMX over SalesInvoiceLine of Quantity x RELATED ( the item cost ); with no view selected it falls back to Standard. 2026, the 207 finished goods sold (Services left out, the blank row): revenue 28,543,076.08 (29,756,420.08 less Services 1,213,344.00); margin at standard 12,739,803.20 (standard cost 15,803,272.88, Chapter 14's figure), absorption 10,661,488.02, time-driven 11,731,216.94 (10,562,490.53 after unused capacity); with the year's variance charged 10,474,166.32 (the totals differ through the inventory build and timing). These totals take the item costs at six decimals, as CR18's CSV holds them; unrounded, absorption is 10,661,488.03. Family margins match Requirement 4 (FUR-TBL 41.3 / 30.1 / 36.8%). Optional for strong students: a cumulative-margin curve on a disconnected rank table (GENERATESERIES) with TOPN over ALLSELECTED items, checked in the engine (41 items 51.2 / 50.6 / 50.7%, 100% at 207, blank beyond). Tests: each view's total equals the workbook's; revenue and standard cost equal Chapter 14's; the variances charged equal 5080.

## What a strong answer says

- **One measure, three views.** A disconnected table, SWITCH on SELECTEDVALUE, and Margin and Margin % built on it, so every visual changes with the slicer.
- **The blank is a decision.** The design services are out of the cost views and in the Validation row, with the reason.
- **The report ties out.** Validation reproduces the year's revenue and standard cost of Chapters 13 and 14, the inputs to `1090`, and each view's total against the workbook.
- **The caveats are visible.** The practical share is typed and must follow the workbook; the default view is Standard.

A weak answer builds the visuals without the year filter or the tie to the workbook.

## Common mistakes and how to respond

- **No year filter.** *Symptom:* revenue of $82,927,040.29. *Response:* ask which year the item costs describe.
- **Services in the margin.** *Symptom:* 46.89%. *Response:* ask what standard cost the design services carry.
- **A silent default.** *Symptom:* two views selected, Standard shown. *Response:* ask what SELECTEDVALUE returns.
- **A drifting practical share.** *Symptom:* the Capacity page and the costs disagree after the Assumptions change. *Response:* ask where each file holds the share.
- **A broken source path.** *Symptom:* a refresh error on a new computer. *Response:* point the queries at the files with **Change Source**.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Model and the blank | 25 | Both sources, year, relationships, the services decision stated | Relationships without the year or the decision |
| Switching measure | 25 | Costing View table, Product Cost, Margin and Margin % | Three separate measures |
| Families and Capacity pages | 20 | Matrix, ranked items, slicer; capacity chart and table | Pages without the slicer |
| About, Validation and Tests | 20 | Controls tied to earlier chapters and to the workbook | Validation without a test |
| Documentation | 10 | Sources, caveats and the data-through date on About | Missing |

## Extensions and discussion questions

- Add the cumulative-margin curve of the Concentration page: a rank table from GENERATESERIES and TOPN over the items.
- Add a parameter for the practical share, and say why it cannot move the workbook's costs.
- Discuss: which view should the slicer open on, and who decides?
- Discuss: the services are left out of the cost views. What would a reader miss without the Validation row?
