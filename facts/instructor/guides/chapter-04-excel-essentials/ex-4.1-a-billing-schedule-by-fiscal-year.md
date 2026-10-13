---
note: ch04.ex1
uses: [ch04.g1]
title: A Billing Schedule by Fiscal Year
kind: exercise
number: '4.1'
unit: '4'
perspective: financial
tool: excel
minutes: 75
solution: "Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheet Ex 4.1"
figures:
  - id: IF-04-1-A
    kind: excel-mock
    purpose: The Ex 4.1 worksheet at the end of the exercise, with the period cells, the period's billing and the billing schedule by fiscal year.
    shows: "Rows 3 to 5 hold the two named parameter cells in blue font with their descriptions. Rows 7 to 14 hold the invoice count and the four totals for the period, then the difference check. Rows 16 to 23 hold the grid with the fiscal years down column A and SubTotal, FreightAmount, TaxAmount and GrandTotal across, a Total row, an Entire SalesInvoice Table row and a Difference row of zeros. Cell E18 is selected and the formula bar shows the GrandTotal formula, with the InvoiceDate column locked."
    data: SalesInvoice grouped by the year of InvoiceDate (the Expected results table).
---
{% set g = ch04_g1 %}
# Exercise 4.1: A Billing Schedule by Fiscal Year

{{ header() }}

## Purpose and learning outcomes

This is the chapter's first free-standing build. It uses the chapter's tools in one small schedule: named and validated parameter cells, COUNTIFS and SUMIFS on structured references, and a grid filled from one formula with mixed references. It is also a lesson in what a schedule is not. The totals tie to the invoice detail, and requirement (5) asks why they are still not revenue. The analytics type is descriptive.

By the end, students can:

- name a parameter cell and protect it with data validation (chapter outcome 5);
- total a Table by period with COUNTIFS and SUMIFS on named cells (outcomes 2 and 3);
- fill a two-way grid from one formula and lock the Table column that must not move (outcome 3);
- tie a schedule to its source and say what it leaves out (outcomes 1 and 6).

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (extracting, transforming and cleansing financial data) and Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Data Tools and Techniques, and Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (i), analyzing data with technology; AACSB A5 part 5.1.

## Before you assign

- **Files.** Each student needs a copy of Charles River Furniture Analysis.xlsx made after Tutorial 4.3, or the End of Chapter 4 folder of Chapter04-companion.zip. Its queries must point at the student's CharlesRiver.xlsx (**Data > Get Data > Data Source Settings**, **Change Source**, then **Data > Refresh All**). The exercise works on a new worksheet named `Ex 4.1`; the tutorials' queries stay as they are.
- **From Tutorial 4.1.** SalesInvoice has its date columns as the Date type and FreightAmount as a decimal number (Step 6). Ask students to check FreightAmount first: {{ g.fractional|count }} of the {{ g.total.n|count }} invoices carry cents of freight, which Changed Type would round to whole dollars if the column was left as a whole number.
- **Data conditions.** SubTotal plus FreightAmount plus TaxAmount equals GrandTotal on every invoice, and every invoice is dated in one of the three fiscal years, so the grid's total row equals the Table. SubTotal, FreightAmount, TaxAmount and GrandTotal are adjacent columns of the Table, in that order. The analysis workbook has no CreditMemo Table; requirement (5) sends students to the CreditMemo worksheet in CharlesRiver.xlsx.
- **The solution file** holds the model answer on the sheet Ex 4.1, with each check listed on its Solution Notes sheet. Cell addresses below are the solution's; students' will differ.

## How to run it

Individual work, about 75 minutes: 15 on the parameter cells (requirement 2), 15 on the period block (3), 25 on the grid (4), 10 on the written note (5) and 10 on the tie-out. Hold back the fill hint for requirement (4) until a student has pasted the formula and read the numbers: the discovery is the lesson. Collect the workbook, not a screenshot, because the formulas are the evidence.

## Step-by-step solution

### Requirement (1): Start from the SalesInvoice Table

**Step 1. Confirm the Table.**

a. Open your copy of the analysis workbook and go to the **SalesInvoice** worksheet.
b. Click a cell in the data and read the **Table Name** box on the **Table Design** tab.
c. Scroll to InvoiceDate, DueDate, PaymentDate and FreightAmount.

**Check:** the Table is named SalesInvoice and holds {{ g.total.n|count }} rows. The dates show without a time, and FreightAmount keeps its cents.

### Requirement (2): Name and validate the period cells

**Step 2. Create the two named cells.**

a. Insert a worksheet named `Ex 4.1`. In row 3 type `Parameter`, `Value` and `Description`, and in A4 and A5 type `PeriodStart` and `PeriodEnd`.
b. Enter {{ g.start }} in B4 and {{ g.end }} in B5, as dates. Fiscal {{ g.c }} is the calendar year {{ g.c }}.
c. Select B4, click the **Name Box**, type `PeriodStart` and press Enter. Name B5 `PeriodEnd` in the same way.
d. Set the font of both cells to blue, the input convention of Tutorial 4.2.

**Check:** the **Name Box** shows PeriodStart when B4 is selected, and both dates are right-aligned. **Watch for:** a date typed as text. It sits left-aligned, and every SUMIFS below returns zero.

**Step 3. Validate both cells.**

a. Select B4 and choose **Data > Data Validation**.
b. On the **Settings** tab, allow **Date**, with the earliest date January 1, {{ g.first }} and the latest {{ g.end_long }}. The model answer enters them as `=DATE({{ g.first }},1,1)` and `=DATE({{ g.c }},12,31)`.
c. On the **Input Message** tab, add a title and a message that states the allowed range. On the **Error Alert** tab, choose the **Stop** style.
d. Repeat for B5.
e. Test B4 with a date before {{ g.first }}, then click **Cancel**.

**Check:** Excel refuses the entry and the cell keeps its date. **Watch for:** the Warning style, which lets the user accept the bad date, and a Date rule with no range.

### Requirement (3): The period's billing

**Step 4. Count the invoices and total the four amounts.** Type `Invoices`, `SubTotal`, `FreightAmount`, `TaxAmount` and `GrandTotal` in A8 to A12. In B8 enter:

```
=COUNTIFS(SalesInvoice[InvoiceDate],">="&PeriodStart,SalesInvoice[InvoiceDate],"<="&PeriodEnd)
```

In B9 enter the same criteria in a SUMIFS, and repeat it in B10 to B12 with the sum column changed:

```
=SUMIFS(SalesInvoice[SubTotal],SalesInvoice[InvoiceDate],">="&PeriodStart,SalesInvoice[InvoiceDate],"<="&PeriodEnd)
```

**Check:** {{ g.year.n|count }} invoices, SubTotal ${{ g.year.sub|money }}, FreightAmount ${{ g.year.frt|money }}, TaxAmount ${{ g.year.tax|money }} and GrandTotal ${{ g.year.gt|money }}.

**Step 5. Confirm that the parts add up.** In B13 enter `=ROUND(B9+B10+B11-B12,2)`. For the whole Table, in B14 enter:

```
=SUMPRODUCT(--(ABS(SalesInvoice[SubTotal]+SalesInvoice[FreightAmount]+SalesInvoice[TaxAmount]-SalesInvoice[GrandTotal])>0.005))
```

**Check:** both cells show 0. **Watch for:** a small nonzero B13. It usually means FreightAmount was rounded to whole dollars by Changed Type, so send the student back to Tutorial 4.1, Step 6c.

### Requirement (4): The grid by fiscal year

**Step 6. Lay out the grid.**

a. In A17 type `Fiscal year`, and in B17 to E17 type `SubTotal`, `FreightAmount`, `TaxAmount` and `GrandTotal`, spelled as the Table spells them.
b. In A18 to A20 enter the years {{ g.rows|map(attribute='year')|join(', ') }} as numbers, because DATE needs numbers.
c. Optional: in G17 type `Invoices`, and count each year's invoices with the same date window.

**Step 7. Enter the formula once and fill it.** In B18 enter:

```
=SUMIFS(SalesInvoice[SubTotal],SalesInvoice[[InvoiceDate]:[InvoiceDate]],">="&DATE($A18,1,1),SalesInvoice[[InvoiceDate]:[InvoiceDate]],"<="&DATE($A18,12,31))
```

`$A18` locks the year's column, `DATE` builds the year's first and last day, and `[[InvoiceDate]:[InvoiceDate]]` locks the date column. SalesInvoice[SubTotal] is left to shift. Fill B18 right to E18, then select B18:E18 and fill down to row 20.

**Check:** click E18. Its sum column reads SalesInvoice[GrandTotal], and InvoiceDate has not moved. Row 20 equals the period block. **Watch for:** two silent failures. A pasted formula keeps SubTotal in every column, so each year shows ${{ g.year.sub|money }} four times in {{ g.c }}. A formula without the lock moves its date criterion to the next column of the Table, so the numbers drift or turn to zero without an error.

**Step 8. Add the total row and the tie-out.** In row 21 enter `Total` and `=SUM(B18:B20)`, filled right. In row 22 enter `Entire SalesInvoice Table` and `=SUM(SalesInvoice[SubTotal])`, filled right (it shifts along the amounts, which is what the row needs). In row 23 enter `=ROUND(B21-B22,2)`.

**Check:** row 23 is zero in all four columns, and the total row reads SubTotal ${{ g.total.sub|money }}, FreightAmount ${{ g.total.frt|money }}, TaxAmount ${{ g.total.tax|money }} and GrandTotal ${{ g.total.gt|money }}.

### Requirement (5): Why this is not revenue

**Step 9. Write the note.** Three points, in two or three sentences. Credit memos are not netted: the CreditMemo worksheet holds {{ g.cm_n|count }} credit memos dated in {{ g.c }}, with a SubTotal of ${{ g.cm_sub|money }}. GrandTotal includes sales tax (${{ g.year.tax|money }}), a liability collected for the government. The ledger records freight billed (${{ g.year.frt|money }}) in its own revenue account, {{ g.freight_account }}, and the tax in account {{ g.tax_account }}. Only SubTotal, net of credit memos, approaches product revenue.

**Check:** the note names all three, with the worksheet or account that shows each.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Invoices in the period ({{ g.c }}) | {{ g.year.n|count }} | Step 4 |
| SubTotal, FreightAmount, TaxAmount, GrandTotal in the period | ${{ g.year.sub|money }}; ${{ g.year.frt|money }}; ${{ g.year.tax|money }}; ${{ g.year.gt|money }} | Step 4 |
| SubTotal + FreightAmount + TaxAmount - GrandTotal | 0 | Step 5 |
{% for r in g.rows %}
| Fiscal {{ r.year }}: invoices; SubTotal; GrandTotal | {{ r.n|count }}; ${{ r.sub|money }}; ${{ r.gt|money }} | Step 7 |
{% endfor %}
| Total row: invoices; SubTotal; FreightAmount; TaxAmount; GrandTotal | {{ g.total.n|count }}; ${{ g.total.sub|money }}; ${{ g.total.frt|money }}; ${{ g.total.tax|money }}; ${{ g.total.gt|money }} | Step 8 |
| Credit memos dated in {{ g.c }}; SubTotal | {{ g.cm_n|count }}; ${{ g.cm_sub|money }} | Step 9 |

{{ figure('IF-04-1-A') }}

{{ expected() }}

## What a strong answer says

- **Requirement (3).** Every total comes from COUNTIFS or SUMIFS on the named cells, and the difference check is zero.
- **Requirement (4).** One formula, filled, with the year and the date column locked, and a total row tied to the entire Table.
- **Requirement (5).** Credit memos not netted, sales tax as a liability, freight in its own revenue account, and the conclusion that SubTotal net of credit memos, not GrandTotal, is the starting point for revenue.

A weak answer calls GrandTotal revenue, lists only one limitation, or ties the total row to itself.

## Common mistakes and how to respond

- **A grid that repeats SubTotal.** *Symptom:* the four columns of a year show one number. *Cause:* the formula was pasted, not filled. *Response:* ask the student to click E18 and read the formula bar.
- **A date criterion that drifts.** *Symptom:* amounts that look right but differ from the period block. *Cause:* a fill across with InvoiceDate unlocked. *Response:* compare row 20 with B9 to B12 and read the formula.
- **Dates typed as text.** *Symptom:* zeros. *Response:* check the alignment and the **Settings** tab of the validation.
- **A nonzero tie-out.** *Cause:* FreightAmount rounded by Changed Type. *Response:* Tutorial 4.1, Step 6c.
- **A total row that sums itself.** *Response:* ask what the Entire SalesInvoice Table row is compared with.
- **GrandTotal named as revenue.** *Response:* ask which part of GrandTotal Charles River keeps.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the Table | 5 | The Table is confirmed with its date and amount types | Used without checking |
| Requirement 2: parameters | 20 | Two named date cells, validated, with a Stop alert and the right range | Named but not validated, or a Warning alert |
| Requirement 3: period block | 25 | COUNTIFS and SUMIFS on the named cells, and the parts check | Hard-coded dates, or no check |
| Requirement 4: grid | 30 | One formula, filled, with locked year and date, and a total row tied to the Table | Pasted columns edited by hand, or no tie-out |
| Requirement 5: limitations | 20 | Credit memos, tax and freight, each with its source | One or two of the three |

## Extensions and discussion questions

- Load the CreditMemo Table with Power Query, as Exercise 4.4 does for shipments, and add credit memo SubTotal and a net SubTotal to the grid.
- Extend the grid to quarters: put the quarter start dates across a row and write one SUMIFS with mixed references.
- Discuss: the schedule refreshes and ties to the detail. What else would a reviewer ask for before relying on it?
- Discuss: Chapter 6 reconciles invoice lines to the ledger. Which part of this schedule will the ledger contradict first?
