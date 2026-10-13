---
note: appendix_c.ex1
uses: [appC.g1]
title: Control Totals by Quarter
kind: exercise
number: C.1
unit: appC
perspective: financial
tool: powerbi
tool_label: The Power BI service in a browser (the model editor and DAX query view)
minutes: 60
solution: "No solution file, because the projects open only in Desktop. The model answer is Steps 1 to 6 of this guide, built from Guided Tutorial C.3 (the Revenue measure and its test), the Key Measures formulas of Chapter 14 as the Appendix B project holds them, and the Checks tab of Chapter13-exercises-pbi.zip for the fiscal totals"
figures:
  - id: IF-AC-1-A
    kind: pbi-mock
    purpose: DAX query view after the Exercise C.1 query has run, the end state of Requirement 2.
    shows: "DAX query view of the model editor in the Power BI service: the banner that DAX queries are discarded on close, the query in the editor, and the Results grid with one row for each fiscal quarter of the three years (fiscal year, period, invoice lines, revenue, list amount, discounts), the four rows of the current year outlined, and the status with the number of columns and rows. The Data pane lists Key Measures first, with Revenue, List Amount, Discounts and Invoice Lines inside it."
    data: The four quarters of the current year from the Expected results quantities, and the other rows from the same read-only twin.
---
{% set g = appC_g1 %}
{% set y = g.y %}
# Exercise C.1: Control Totals by Quarter

{{ header() }}

## Purpose and learning outcomes

Tutorial C.1's Validation page proved the model once, by fiscal year, on a page. The exercise proves it by quarter in a query kept in a file, which depends on no page and survives a redesign of the report. It is also the first use of measures in the browser. The four quarters must add to the year, and the one difference that remains is a lesson in rounding, not an error to chase. The analytics type is descriptive.

Students can:

- add measures to Key Measures and format them (Requirement 1);
- write a DAX query that returns control totals by quarter and keep it outside the browser (Requirements 2 and 5);
- tie the quarters to the Validation page and explain a one-cent difference (Requirement 3);
- find the quarter that holds the discounts and name the promotions behind it (Requirement 4).

**Competencies practiced.** Appendix D maps this exercise to CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and M8 T2 (extracting, transforming and cleansing financial data); to the IMA competencies for financial recordkeeping, financial statement preparation and data tools and techniques; to IFAC IES 2 (a) and (i); and to AACSB A5 parts 5.1 and 5.3.

## Before you assign

- **Files and software.** A browser, and the student's Charles River Reports semantic model and report after Tutorial C.3, with Tests.dax saved. There is no model file: build the three measures and the query once in your own account.
- **Data conditions.** SalesInvoice.Period reads like {{ g.quarters[0].label }}. DiscountAmount is Quantity times UnitPrice times Discount, left unrounded, so rounding each quarter's sum can differ from rounding the year's sum.
- **Verify first.** The Validation page's fiscal {{ y }} row, which Requirement 3 compares with, reads {{ year.n|count }} lines and ${{ year.rev|money }}.
- **Not run in a service.** The query below is the book's Tutorial C.3 test extended with the measures of Requirement 1. Run it once before you assign.

## How to run it

Individual, about 60 minutes: 10 for (1), 15 for (2), 10 for (3), 10 for (4), 10 for (5), 5 spare. Hold back the rounding explanation until the totals are compared, and the promotion names until the quarter is found. Hint 1, after 10 minutes on (2): "Tutorial C.3's test groups by one column. Which two columns of SalesInvoice name a fiscal quarter?" Hint 2, for (4): "Which promotions invoice in the last three months?" Collect Tests.dax, with a comment line naming the exercise, and the short answers.

## Step-by-step solution

### Requirement (1): Three measures in Key Measures

**Step 1. Open the model for editing.**

a. In **My workspace**, open the **Charles River Reports** item whose type is Semantic model.
b. If the menu at the top right reads **Viewing**, open it and choose **Editing**.

**Step 2. Add the measures.**

a. Select **Key Measures** in the **Data** pane, and choose **New measure** on the ribbon.
b. In the formula bar, replace the text with one formula below, and press Enter. Repeat for the other two.
c. Select List Amount, then Discounts, and under **Properties > Formatting** turn on **Thousands separator**.

```dax jinja
{{ g.m_list }}
{{ g.m_disc }}
{{ g.m_lines }}
```

**Check:** Key Measures holds Revenue and the three new measures. **Watch for:** **New measure** adds the measure to the table selected in the **Data** pane. With another table selected the measure lands there, and the query below still runs, because it names measures without a table, so the mistake passes the test. Look at the **Data** pane. The format cannot be checked in DAX query view, whose grid shows raw values: check **Properties**, or a table visual.

### Requirement (2): The query

**Step 3. Write and run the query.**

a. Select **DAX query view** at the bottom of the model editor.
b. Replace the sample query with the query below, and click **Run**.
c. Copy the query into Tests.dax, under a comment line that names the exercise.

```dax jinja
{{ g.query }}
```

**Check:** the status reports {{ g.n_cols }} columns and {{ g.n_rows }} rows, ordered by year and quarter, and the four rows of fiscal {{ y }} are those of the Expected results.

{{ figure('IF-AC-1-A') }}

**Watch for:** grouping by FiscalQuarter alone, which returns four rows that add the three years (the fourth reads {{ g.by_q[3].n|count }} lines and ${{ g.by_q[3].rev|money }}), so no fiscal {{ y }} row can be read. Counting with DISTINCTCOUNT instead of COUNTROWS returns invoices, not lines: {{ g.q1.invoices|count }} in the first quarter against {{ g.q1.n|count }} lines.

### Requirement (3): The tie to the Validation page

**Step 4. Add the quarters and compare.**

a. Add the four quarters' lines, revenue, list amount and discounts.
b. Open the report's **Validation** page (Reading view is enough) and read its fiscal {{ y }} row.

**Check:** lines, revenue and list amount agree exactly. The discounts differ by ${{ g.cent|money }}: the rounded quarters add to ${{ g.rounded_sum|money }}, and the page shows ${{ year.disc|money }}. The cause is rounding, not an error, because the discount of each line is unrounded and each quarter was rounded on its own. The instructor check reads the year straight from the lines:

```dax jinja
EVALUATE
ROW ( "Discounts, current fiscal year", ROUND ( {{ g.dax_disc }}, 2 ) )
```

**Watch for:** a student who adjusts a quarter to force agreement, or reports the cent as unexplained.

### Requirement (4): The quarter that holds the discounts

**Step 5. Compute each quarter's share and name the promotions.** Divide each quarter's discounts by the year's.

**Check:** quarter {{ top.q }} holds {{ share|pct(1) }}. The promotions are {% for name, v in top.promos[:2] %}{{ name }} (${{ v|money }}){{ " and " if not loop.last else "" }}{% endfor %}. The model has no promotion table, so accept the names from Chapter 6 and Exercise 13.3; a student who adds T7_PromotionProgram, as the appendix's last section describes, can show the amounts. **Watch for:** naming the third quarter because the Furniture promotion's dates are {{ g.autumn_start }} and {{ g.autumn_end }}. Its orders are invoiced through December, so the third quarter holds {{ (quarters[2].disc / year.disc)|pct(1) }} and the fourth the rest.

### Requirement (5): Why a query remains evidence

**Step 6. Write the explanation.** The model answer has four points: a query reads the model, not any visual, so a page edit cannot change it; a changed measure or relationship will change it, which is what the test detects; DAX query view in the browser discards its tabs on close, so the file is the record; and the comment line says which exercise and which question the query answers.

## Expected results

| Quantity | Value | Step |
|---|---|---|
{% for q in quarters %}
| Quarter {{ q.q }} of fiscal {{ y }}: lines; revenue; list amount; discounts | {{ q.n|count }}; ${{ q.rev|money }}; ${{ q.list|money }}; ${{ q.disc|money }} | 3 |
{% endfor %}
| Quarters' discounts against the year | ${{ g.rounded_sum|money }} against ${{ year.disc|money }} | 4 |
| Largest quarter | Quarter {{ top.q }}, {{ share|pct(1) }} of the discounts | 5 |

{{ expected() }}

## What a strong answer says

- **(1), (2)** Three measures in Key Measures, two formatted; one query, twelve rows, in Tests.dax with a comment.
- **(3)** Three totals agree exactly and the fourth differs by a cent, with the cause named: sums of unrounded amounts, rounded separately.
- **(4)** The quarter, its share, both promotions, and the remark that invoicing lags the order dates.
- **(5)** The four points above. A strong answer adds that the test would catch a changed measure that no page shows.

## Common mistakes and how to respond

- **Four rows, not twelve.** *Symptom:* the status reads four rows. *Cause:* FiscalQuarter without FiscalYear. *Response:* ask which year the first row belongs to.
- **Invoices instead of lines.** *Symptom:* the first quarter shows {{ g.q1.invoices|count }}. *Response:* ask what the measure counts.
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
- Explain the first quarter: {{ g.q1_old }} are promotions of the prior year invoiced in January, and the second quarter holds only {{ g.harbor }}, whose end date precedes its start (Exercise 13.3).
- Add T7_PromotionProgram by the steps of the appendix's last section, relate it on PromotionID, and show the fourth quarter by promotion.
- Discuss: when should a controller stop chasing a cent?
- Discuss: where should a team keep its tests, and what does each place lose?
