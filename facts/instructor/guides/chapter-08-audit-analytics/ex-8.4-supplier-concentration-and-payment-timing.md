---
note: ch08.ex4
uses: [ch08.g4]
title: Supplier Concentration and Payment Timing
kind: exercise
number: '8.4'
unit: '8'
perspective: managerial
tool: excel
minutes: 75
solution: "Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheet Ex 8.4, with the PivotTables PivotEx84 and PivotEx84Category and the FiscalYear and DaysAfterDue columns of the Payments Table"
figures:
  - id: IF-08-4-A
    kind: excel-mock
    purpose: The supplier PivotTable with the running share of spending, the step where students most often go wrong.
    shows: "A PivotTable with FiscalYear in the filter area set to the current year, SupplierName in rows from the largest payment total down, and the columns Sum of Amount and Running share of spending. The row where the share first reaches 50 percent is outlined. Beside it, the number of suppliers that make up 50, 80 and 90 percent."
    data: DisbursementPayment by supplier for the current fiscal year (the Expected results table).
---
{% set g = ch08_g4 %}
# Exercise 8.4: Supplier Concentration and Payment Timing

{{ header() }}

## Purpose and learning outcomes

The treasurer asks how dependent Charles River is on its suppliers and whether it pays them on time. The exercise gives students a running-share PivotTable and a timing analysis that look easy and fail quietly when the fiscal year is not fixed. Its finding is a surprise worth discussing: dollar concentration is low, and most payments are made after the due date. It practices editing tutorial queries in the copy, a calculated Table column, a PivotTable with a page filter and **Show Values As**, COUNTIFS, MEDIAN with FILTER and a memo. The analytics type is descriptive.

By the end, students can:

- measure concentration with a cumulative share and read how many suppliers make up half, 80 and 90 percent of spending (outcome 1);
- summarize spending by category and relate the dollars to a dependence on a category (outcome 1);
- compute days after the due date and describe timing by count, value, median and tail (outcome 1);
- state what paying early or late gains and costs (outcome 1).

**Competencies practiced.** CPA Evolution BAR M9 (financial statement analysis and working capital) and Core S1 M8 T3 to T4 (data mining and analysis of financial data); IMA Data Analytics and Insights (data analysis) and Strategy, Planning and Performance (performance management); IFAC IES 2 (b) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3, with the Payments, Suppliers and PurchaseInvoices queries of Tutorial 8.1. The exercise adds columns to them in the copy.
- **Data conditions.** The Payments Table holds {{ g.years_word }} fiscal years and {{ g.allyears.n|count }} payments, so the fiscal year must be fixed for every figure. The year in question has {{ n|count }} payments to {{ suppliers }} suppliers. Every invoice has a DueDate, and every payment is a whole number of days from it.
- **Verify first.** Without the year filter, the PivotTable's total is ${{ g.allyears.total|money }} and its marks are {{ g.allyears.n50 }}, {{ g.allyears.n80 }} and {{ g.allyears.n90 }}. Know these, because students will report them.

## How to run it

Individual or pairs, about 75 minutes: 25 for the queries and the PivotTable (1), 15 for the marks and categories (2), 20 for timing (3) and 15 for the memo (4). Hold back the hint about the page filter until a student's marks differ from the answer. Collect the worksheet and the memo.

{{ figure('IF-08-4-A') }}

## Step-by-step solution

### Requirement (1): The supplier ranking

**Step 1. Carry the columns into Payments.**

a. In the Power Query Editor, reopen the step of Suppliers that keeps columns and add SupplierCategory, and the step of PurchaseInvoices that keeps columns and add DueDate.
b. In Payments, reopen the two steps that expand those queries and tick the new columns, without the prefix. Choose **Close & Load** and **Data > Refresh All**.
c. In the Payments Table add a column `FiscalYear` with `=YEAR([@PaymentDate])`.

**Step 2. Build the PivotTable.**

a. Select a cell in the Payments Table, choose **Insert > PivotTable** and place it on a new worksheet `Ex 8.4`.
b. Drag FiscalYear to the **Filters** area and choose {{ d.C }}. Drag SupplierName to the **Rows** area and Amount to the **Values** area.
c. Sort the suppliers from the largest Sum of Amount to the smallest.
d. Drag Amount to the **Values** area again, open its **Value Field Settings**, choose **Show Values As > % Running Total In** and the base field SupplierName.

**Check:** {{ suppliers }} suppliers and ${{ total|money }}. **Watch for:** the year filter left on all years, which gives {{ g.allyears.n|count }} payments and ${{ g.allyears.total|money }}; and the running share added before the sort, or sorted by name, which reaches half of the spending only after {{ g.alpha50 }} suppliers.

### Requirement (2): Concentration and categories

**Step 3. Read the marks.** Count the suppliers whose running share is below each mark and add one. In the model answer the running share is column C, rows 4 to 106.

```
=COUNTIF(C4:C106,"<"&0.5)+1
```

**Check:** {{ n50 }} suppliers make up 50 percent, {{ n80 }} make up 80 percent and {{ n90 }} make up 90 percent. The largest, {{ top.name }} ({{ top.category }}), has {{ top.share|pct(2) }}.

**Step 4. Summarize by category.** Insert a second PivotTable from the Payments Table with the same year filter, SupplierCategory in rows and the Sum of Amount sorted from the largest. **Check:** {{ g.categories_word }} categories, the largest {{ g.categories[0].name }} at {{ g.top_share|pct(1) }} and {{ g.categories[1].name }} at {{ g.second_share|pct(1) }}.

### Requirement (3): Payment timing

**Step 5. Compute the days after the due date.** In the Payments Table add `DaysAfterDue` with `=[@PaymentDate]-[@DueDate]` and format it as a whole number. Excel shows the difference of two dates as a date until you do.

**Step 6. Count and summarize.** Put the year in a cell and use it in each formula, so the table can be rerun for another year.

```
=COUNTIFS(Payments[FiscalYear],F21,Payments[DaysAfterDue],"<0")
=COUNTIFS(Payments[FiscalYear],F21,Payments[DaysAfterDue],0)
=COUNTIFS(Payments[FiscalYear],F21,Payments[DaysAfterDue],">0")
=MEDIAN(FILTER(Payments[DaysAfterDue],Payments[FiscalYear]=F21))
=AVERAGEIFS(Payments[DaysAfterDue],Payments[FiscalYear],F21)
```

**Check:** {{ before|count }} before the due date, {{ on|count }} on it and {{ after|count }} after, {{ after_share|pct(1) }} by count and {{ after_value|pct(1) }} by value; the median is {{ median|num(0) }} days after, the mean {{ mean|num(1) }}, and {{ late30|count }} payments are more than 30 days late. **Watch for:** the year criterion left out of a COUNTIFS, which counts all {{ g.allyears.n|count }} payments.

### Requirement (4): The memo

**Step 7. Outline the memo.** To the treasurer. Concentration: no supplier is large in dollars, and the weight lies in categories, but dollars do not measure operational dependence. A low-spend supplier can still be critical, and whether one disruption could reach many suppliers of a category is a question the data cannot answer. Timing: most payments are late, a tail is more than a month late, and no supplier's recorded terms offer an early-payment discount, so paying early is a free loan unless a contract says otherwise. Recommendation: pay by due date, ask why so many payments are late, and negotiate discounts or longer terms with the largest suppliers if cash is tight.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Payments, suppliers and spending in the year | {{ n|count }}; {{ suppliers }}; ${{ total|money }} | 2 |
| Suppliers making up 50, 80 and 90 percent | {{ n50 }}; {{ n80 }}; {{ n90 }} | 3 |
| Largest supplier and its share | {{ top.name }}; {{ top.share|pct(2) }} | 3 |
{% for c, amount in categories %}
| Spending on {{ c }} | ${{ amount|money }} | 4 |
{% endfor %}
| Paid before, on and after the due date | {{ before|count }}; {{ on|count }}; {{ after|count }} | 6 |
| Median and mean days after the due date | {{ median|num(0) }}; {{ mean|num(1) }} | 6 |
| Paid more than 30 days late | {{ late30|count }} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The three marks read as concentration in dollars, with the largest supplier's share, and the finding that spending is spread across suppliers and weighted by category, which dollars alone do not turn into a measure of dependence.
- **Requirement (4).** Both findings in the first paragraph, with numbers. The gains and losses of paying late (cash kept longer; late fees, credit holds, worse prices, strained relationships) and of paying early (cash used sooner, a free loan to the supplier without a discount), and a recommendation to schedule runs by due date and to find out why payments are late.

A weak answer calls the company healthy because it pays late, or concentrated because a category is large.

## Common mistakes and how to respond

- **No fiscal year.** *Symptom:* the marks are {{ g.allyears.n50 }}, {{ g.allyears.n80 }} and {{ g.allyears.n90 }}. *Response:* ask how many years the Table holds.
- **Not sorted by amount.** *Symptom:* half of the spending needs {{ g.alpha50 }} suppliers. *Response:* ask what a running total of an alphabetical list means.
- **A share of the total, not a running total.** *Symptom:* each row shows its own share, and the marks formula returns the number of suppliers plus one. *Response:* ask what cumulative means.
- **Days as a date.** *Symptom:* DaysAfterDue shows dates in January of `1900`. *Response:* ask what the difference of two dates is.
- **Unfiltered timing formulas.** *Symptom:* counts of all years. *Response:* ask where the year is in the formula.
- **Late read as healthy.** *Symptom:* "we conserve cash". *Response:* ask what the supplier does.
- **Early and late both treated as problems.** *Symptom:* a memo with no recommendation. *Response:* ask what the target is.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: queries, filter and running share | 30 | Year fixed, sorted by amount, running share on SupplierName | Right table for all years |
| Requirement 2: marks and categories | 20 | Three marks, category table | One mark wrong |
| Requirement 3: timing | 25 | Whole-number days, counts, median, tail, year-specific | Counts without the median |
| Requirement 4: memo | 25 | Both findings, gains and losses, a recommendation | No recommendation |

## Extensions and discussion questions

- Run Tutorial 8.1's first-digit test on the supplier invoice totals. The MAD should be about {{ g.inv_mad|num(4) }}, close conformity, which is the contrast the chapter draws with the partial payments.
- Compute the share of payments after the due date by supplier category. Which category is paid latest?
- Discuss: a supplier with a small share of spending supplies a part that stops the plant. How would you find it in this data?
- Discuss: when would paying early be worth it, and what would the data have to show?
