# Exercise C.1: Control Totals by Quarter

| | |
|---|---|
| Unit | Appendix C: Power BI in the Browser |
| Item | Exercise C.1 |
| Perspective | Financial accounting |
| Tools | The Power BI service in a browser (the model editor and DAX query view) |
| Time | About 60 minutes |
| Solution file | No solution file, because the projects open only in Desktop. The model answer is Steps 1 to 6 of this guide, built from Guided Tutorial C.3 (the Revenue measure and its test), the Key Measures formulas of Chapter 14 as the Appendix B project holds them, and the Checks tab of Chapter13-exercises-pbi.zip for the fiscal totals |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial C.1's Validation page proved the model once, by fiscal year, on a page. The exercise proves it by quarter in a query kept in a file, which depends on no page and survives a redesign of the report. It is also further practice with the measures introduced in Tutorial C.3. The four quarters must add to the year, and the one difference that remains is a lesson in rounding, not an error to chase. The analytics type is descriptive.

Students can:

- add measures to Key Measures and format them (Requirement 1);
- write a DAX query that returns control totals by quarter and keep it outside the browser (Requirements 2 and 5);
- tie the quarters to the Validation page and explain a one-cent difference (Requirement 3);
- find the quarter that holds the discounts and name the promotions behind it (Requirement 4).

**Competencies practiced.** Appendix D maps this exercise to CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and M8 T2 (extracting, transforming and cleansing financial data); to the IMA competency data tools and techniques; to IFAC IES 2 (a) and (i); and to AACSB A5 part 5.1, with part 5.3 when the instructor adds an independent-learning task.

## Before you assign

- **Files and software.** A browser, and the student's Charles River Reports semantic model and report after Tutorial C.3, with Tests.dax saved. There is no model file: build the three measures and the query once in your own account.
- **Data conditions.** SalesInvoice.Period reads like 2026-Q1. DiscountAmount is Quantity times UnitPrice times Discount, left unrounded, so rounding each quarter's sum can differ from rounding the year's sum.
- **Verify first.** The Validation page's fiscal 2026 row, which Requirement 3 compares with, reads 9,522 lines and $29,756,420.08.
- **Not run in a service.** The query below is the book's Tutorial C.3 test extended with the measures of Requirement 1. Run it once before you assign.

## How to run it

Individual, about 60 minutes: 10 for (1), 15 for (2), 10 for (3), 10 for (4), 10 for (5), 5 spare. Hold back the rounding explanation until the totals are compared, and the promotion names until the quarter is found. Hint 1, after 10 minutes on (2): "Tutorial C.3's test groups by one column. Which two columns of SalesInvoice name a fiscal quarter?" Hint 2, for (4): "Which promotions invoice in the last three months?" Collect Tests.dax, with a comment line naming the exercise and each result in a comment under its query, so that the file still runs, and the short answers.

## Step-by-step solution

### Requirement (1): Three measures in Key Measures

**Step 1. Open the model for editing.**

a. In **My workspace**, open the **Charles River Reports** item whose type is Semantic model.
b. If the menu at the top right reads **Viewing**, open it and choose **Editing**.

**Step 2. Add the measures.**

a. Select **Key Measures** in the **Data** pane, and choose **New measure** on the ribbon.
b. In the formula bar, replace the text with one formula below, and press Enter. Repeat for the other two.
c. Select List Amount, then Discounts, and under **Properties > Formatting** turn on **Thousands separator** and check that **Decimal places** reads 2.

```dax
List Amount = SUM ( SalesInvoiceLine[ListAmount] )
Discounts = SUM ( SalesInvoiceLine[DiscountAmount] )
Invoice Lines = COUNTROWS ( SalesInvoiceLine )
```

**Check:** Key Measures holds Revenue and the three new measures. **Watch for:** **New measure** adds the measure to the table selected in the **Data** pane. With another table selected the measure lands there, and the query below still runs, because it names measures without a table, so the mistake passes the test. Look at the **Data** pane. The format cannot be checked in DAX query view, whose grid shows raw values: check **Properties**, or a table visual.

### Requirement (2): The query

**Step 3. Write and run the query.**

a. Select **DAX query view** at the bottom of the model editor.
b. Replace the sample query with the query below, and click **Run**.
c. Copy the query into Tests.dax, under a comment line that names the exercise.

```dax
// Exercise C.1, requirement (2): the control totals of each quarter
EVALUATE
SUMMARIZECOLUMNS (
    SalesInvoice[FiscalYear],
    SalesInvoice[Period],
    "Invoice lines", [Invoice Lines],
    "Revenue", ROUND ( [Revenue], 2 ),
    "List amount", ROUND ( [List Amount], 2 ),
    "Discounts", ROUND ( [Discounts], 2 )
)
ORDER BY SalesInvoice[FiscalYear], SalesInvoice[Period]
```

**Check:** the status reports 6 columns and 12 rows, ordered by year and quarter, and the four rows of fiscal 2026 are those of the Expected results.

![A mock of DAX query view after the Exercise C.1 query has run, the end state of Requirement 2.](../figures/appendix-c-power-bi-browser/IF-AC-1-A.pdf)

**Watch for:** grouping by FiscalQuarter alone, which returns four rows that add the three years (the fourth reads 7,135 lines and $22,032,440.83), so no fiscal 2026 row can be read. Counting with DISTINCTCOUNT instead of COUNTROWS returns invoices, not lines: 1,845 in the first quarter against 2,472 lines.

### Requirement (3): The tie to the Validation page

**Step 4. Add the quarters and compare.**

a. Add the four quarters' lines, revenue, list amount and discounts.
b. Open the report's **Validation** page (Reading view is enough) and read its fiscal 2026 row.

**Check:** lines, revenue and list amount agree exactly. The discounts differ by $0.01: the rounded quarters add to $362,110.74, and the page shows $362,110.75. The cause is rounding, not an error, because the discount of each line is unrounded and each quarter was rounded on its own. Unrounded, the four quarters add to the year exactly. Rounding every line to the cent first would give $362,110.79, a different calculation from the book's unrounded DiscountAmount, so neither the query nor the data is changed. The instructor check reads the year straight from the lines:

```dax
EVALUATE
ROW ( "Discounts, current fiscal year", ROUND ( CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SalesInvoice[FiscalYear] = 2026 ), 2 ) )
```

**Watch for:** a student who adjusts a quarter to force agreement, rounds the lines to make the cent disappear, or reports the cent as unexplained.

### Requirement (4): The quarter that holds the discounts

**Step 5. Compute each quarter's share and name the promotions.** Divide each quarter's discounts by the year's.

**Check:** quarter 4 holds 63.0%. The promotions are Furniture Seasonal Promotion ($200,056.61) and Design Trade Customer Promotion ($28,057.57). The model has no promotion table, so accept the names from Chapter 6 and Exercise 13.3, or from your own lookup of PromotionID and PromotionName, which the student task allows. Loading T7_PromotionProgram, as the appendix's last section describes, is an optional extension that can show the amounts. **Watch for:** naming the third quarter because the Furniture promotion's dates are September and October. Its orders are invoiced through December, so the third quarter holds 26.6% of the year's discounts and the fourth 63.0%, and the first two quarters together hold the remaining 10.4%.

### Requirement (5): Why a query remains evidence

**Step 6. Write the explanation.** The model answer has four points: a query reads the model, not any visual, so a page edit cannot change it; a changed measure or relationship will change it, which is what the test detects; DAX query view in the browser discards its tabs on close, so the file is the record; and the comment line says which exercise and which question the query answers. The query alone shows which test was specified, and the result and date written under it show that the model passed it on that day.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Quarter 1 of fiscal 2026: lines; revenue; list amount; discounts | 2,472; $7,546,851.67; $8,432,384.12; $15,118.02 | 3 |
| Quarter 2 of fiscal 2026: lines; revenue; list amount; discounts | 2,377; $7,654,417.42; $8,579,566.07; $22,524.82 | 3 |
| Quarter 3 of fiscal 2026: lines; revenue; list amount; discounts | 2,341; $7,267,963.31; $8,212,248.05; $96,353.72 | 3 |
| Quarter 4 of fiscal 2026: lines; revenue; list amount; discounts | 2,332; $7,287,187.68; $8,364,939.21; $228,114.18 | 3 |
| Quarters' discounts against the year | $362,110.74 against $362,110.75 | 4 |
| Largest quarter | Quarter 4, 63.0% of the discounts | 5 |

> **Instructor notes, Exercise C.1:** fiscal 2026 by quarter (lines, revenue, list amount, discounts): Q1 2,472, 7,546,851.67, 8,432,384.12, 15,118.02; Q2 2,377, 7,654,417.42, 8,579,566.07, 22,524.82; Q3 2,341, 7,267,963.31, 8,212,248.05, 96,353.72; Q4 2,332, 7,287,187.68, 8,364,939.21, 228,114.18. The quarters add up to the Validation row: 9,522 lines, 29,756,420.08, 33,589,137.45, 362,110.75 (the sum of the rounded quarters' discounts can differ from the year's by a cent, while the unrounded quarters add up to it exactly, so the cent is rounding). (4) Q4 carries 63.0% of the year's discounts: Furniture Seasonal Promotion 200,056.61; Design Trade Customer Promotion 28,057.57. The Furniture Seasonal Promotion ran in September and October, but its orders were invoiced through December. (5) A query in Tests.dax does not change when a page is edited, and DAX query view in the browser discards its tabs on close.

## What a strong answer says

- **(1), (2)** Three measures in Key Measures, two formatted with a thousands separator and two decimal places; one query, twelve rows, in Tests.dax with a comment, and the four rows of fiscal 2026 written as a comment with the date of the run.
- **(3)** Three totals agree exactly and the fourth differs by a cent, with the cause named: sums of unrounded amounts, rounded separately.
- **(4)** The quarter, its share, both promotions, and the remark that invoicing lags the order dates.
- **(5)** The four points above. A strong answer adds that the test would catch a changed measure that no page shows.

## Common mistakes and how to respond

- **Four rows, not twelve.** *Symptom:* the status reads four rows. *Cause:* FiscalQuarter without FiscalYear. *Response:* ask which year the first row belongs to.
- **Invoices instead of lines.** *Symptom:* the first quarter shows 1,845. *Response:* ask what the measure counts.
- **A forced tie.** *Symptom:* a quarter adjusted by a cent. *Response:* ask which numbers were rounded before they were added.
- **The wrong quarter.** *Symptom:* the third quarter named. *Response:* ask on which date the invoices carry the discount.
- **A measure in the wrong table.** *Symptom:* Key Measures lacks one. *Response:* ask which table was selected before **New measure**.
- **A query that exists only in the browser.** *Symptom:* no file, or an empty tab after the model is reopened. *Response:* the tab is discarded on close; paste it back from Tests.dax.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 15 | Three measures in Key Measures, two formatted | Measures exist in another table, or no format |
| Requirement 2 | 25 | Twelve rows, rounded, ordered, in Tests.dax with a comment | Right rows, no file |
| Requirement 3 | 20 | Exact tie of three totals, the cent explained | Tie stated, no cause |
| Requirement 4 | 20 | Quarter, share and both promotions | Quarter and share only |
| Requirement 5 | 20 | The four points | Two or three |

## Extensions and discussion questions

- Add an Invoices measure with DISTINCTCOUNT of SalesInvoiceID and extend the query. Why does it differ from the lines?
- Explain the first quarter by promotion. It holds Textiles Seasonal Promotion and Wholesale Customer Promotion, promotions of the prior year, together with the Harbor Collection Promotion. The Wholesale Customer Promotion is invoiced through March 6, so the prior-year promotions' invoices are not confined to January. The Harbor Collection Promotion contributes $7,596.99 to the first quarter and is the only promotion with discounts in the second. Its end date precedes its start, the data-quality issue of Exercise 13.3.
- Add T7_PromotionProgram by the steps of the appendix's last section, relate it on PromotionID, and show the fourth quarter by promotion.
- Discuss: when should a controller stop chasing a cent?
- Discuss: where should a team keep its tests, and what does each place lose?
