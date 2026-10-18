# Exercise 4.1: A Billing Schedule by Fiscal Year

| | |
|---|---|
| Unit | Chapter 4: Excel Essentials for Accounting Analytics |
| Item | Exercise 4.1 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheet Ex 4.1 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This is the chapter's first free-standing build. It uses the chapter's tools in one small schedule: named and validated parameter cells, COUNTIFS and SUMIFS on structured references, and a grid filled from one formula with mixed references. It is also a lesson in what a schedule is not. The totals tie to the invoice detail, and requirement (5) asks why they are still not revenue. The analytics type is descriptive.

By the end, students can:

- name a parameter cell and protect it with data validation (outcome 5);
- total a Table by period with COUNTIFS and SUMIFS on named cells (outcomes 2 and 3);
- fill a two-way grid from one formula and lock the Table column that must not move (outcome 3);
- tie a schedule to its source and say what it leaves out (outcomes 1 and 6).

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (extracting, transforming and cleansing financial data) and Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Data Tools and Techniques, and Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (i), analyzing data with technology; AACSB A5 part 5.1.

## Before you assign

- **Files.** Each student needs a copy of Charles River Furniture Analysis.xlsx made after Tutorial 4.3, or the End of Chapter 4 folder of Chapter04-companion.zip. Its queries must point at the student's CharlesRiver.xlsx (**Data > Get Data > Data Source Settings**, **Change Source**, then **Data > Refresh All**). The exercise works on a new worksheet named `Ex 4.1`; the tutorials' queries stay as they are.
- **From Tutorial 4.1.** SalesInvoice has its date columns as the Date type and FreightAmount as a decimal number (Step 6). Ask students to check FreightAmount first: 414 of the 20,914 invoices carry cents of freight, which Changed Type would round to whole dollars if the column was left as a whole number.
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

**Check:** the Table is named SalesInvoice and holds 20,914 rows. The dates show without a time, and FreightAmount keeps its cents.

### Requirement (2): Name and validate the period cells

**Step 2. Create the two named cells.**

a. Insert a worksheet named `Ex 4.1`. In row 3 type `Parameter`, `Value` and `Description`, and in A4 and A5 type `PeriodStart` and `PeriodEnd`.
b. Enter 2026-01-01 in B4 and 2026-12-31 in B5, as dates. Fiscal 2026 is the calendar year 2026.
c. Select B4, click the **Name Box**, type `PeriodStart` and press Enter. Name B5 `PeriodEnd` in the same way.
d. Set the font of both cells to blue, the input convention of Tutorial 4.2.

**Check:** the **Name Box** shows PeriodStart when B4 is selected, and `=ISNUMBER(PeriodStart)` and `=ISNUMBER(PeriodEnd)` return TRUE. **Watch for:** a date typed as text. ISNUMBER returns FALSE, and every SUMIFS below returns zero. A text date usually sits left-aligned, but alignment is only a clue, because a cell can be aligned by hand.

**Step 3. Validate both cells.**

a. Select B4 and choose **Data > Data Validation**.
b. On the **Settings** tab, allow **Date**, with the earliest date January 1, 2024 and the latest December 31, 2026. The model answer enters them as `=DATE(2024,1,1)` and `=DATE(2026,12,31)`.
c. On the **Input Message** tab, add a title and a message that states the allowed range. On the **Error Alert** tab, choose the **Stop** style.
d. Repeat for B5.
e. Test B4 with a date before 2024, then click **Cancel**.

**Check:** Excel refuses the entry and the cell keeps its date. **Watch for:** the Warning style, which lets the user accept the bad date, and a Date rule with no range. Validation tests each cell on its own, so a PeriodStart later than PeriodEnd passes both rules, and the period block then shows zeros while its parts check still reads 0, as if all were well. An optional status cell beside the parameters catches it. Test it with the dates reversed, then restore fiscal 2026:

```
=IF(AND(ISNUMBER(PeriodStart),ISNUMBER(PeriodEnd),PeriodStart>=DATE(2024,1,1),PeriodEnd<=DATE(2026,12,31),PeriodStart<=PeriodEnd),"Period valid","Check period dates")
```

### Requirement (3): The period's billing

**Step 4. Count the invoices and total the four amounts.** Type `Invoices`, `SubTotal`, `FreightAmount`, `TaxAmount` and `GrandTotal` in A8 to A12. In B8 enter:

```
=COUNTIFS(SalesInvoice[InvoiceDate],">="&PeriodStart,SalesInvoice[InvoiceDate],"<="&PeriodEnd)
```

In B9 enter the same criteria in a SUMIFS, and repeat it in B10 to B12 with the sum column changed:

```
=SUMIFS(SalesInvoice[SubTotal],SalesInvoice[InvoiceDate],">="&PeriodStart,SalesInvoice[InvoiceDate],"<="&PeriodEnd)
```

**Check:** 7,171 invoices, SubTotal $29,756,420.08, FreightAmount $214,588.22, TaxAmount $1,948,116.12 and GrandTotal $31,919,124.42.

**Step 5. Confirm that the parts add up.** In B13 enter `=ROUND(B9+B10+B11-B12,2)`. For the whole Table, in B14 enter:

```
=SUMPRODUCT(--(ABS(SalesInvoice[SubTotal] + SalesInvoice[FreightAmount] + SalesInvoice[TaxAmount] - SalesInvoice[GrandTotal]) > 0.005))
```

The spaces around the operators are optional, and the solution file writes the formula without them.

**Check:** both cells show 0. **Watch for:** a small nonzero B13. It usually means FreightAmount was rounded to whole dollars by Changed Type, so send the student back to Tutorial 4.1, Step 6c.

### Requirement (4): The grid by fiscal year

**Step 6. Lay out the grid.**

a. In A17 type `Fiscal year`, and in B17 to E17 type `SubTotal`, `FreightAmount`, `TaxAmount` and `GrandTotal`, spelled as the Table spells them.
b. In A18 to A20 enter the years 2024, 2025, 2026 as numbers, because DATE needs numbers.
c. Optional: in G17 type `Invoices`, and count each year's invoices with the same date window.

**Step 7. Enter the formula once and fill it.** In B18 enter:

```
=SUMIFS(SalesInvoice[SubTotal],SalesInvoice[[InvoiceDate]:[InvoiceDate]],">="&DATE($A18,1,1),SalesInvoice[[InvoiceDate]:[InvoiceDate]],"<="&DATE($A18,12,31))
```

`$A18` locks the year's column, `DATE` builds the year's first and last day, and `[[InvoiceDate]:[InvoiceDate]]` locks the date column. SalesInvoice[SubTotal] is left to shift. Fill B18 right to E18, then select B18:E18 and fill down to row 20.

**Check:** click E18. Its sum column reads SalesInvoice[GrandTotal], and InvoiceDate has not moved. Row 20 equals the period block. **Watch for:** two silent failures. A pasted formula keeps SubTotal in every column, so each year shows $29,756,420.08 four times in 2026. A formula without the lock moves its date criterion to the next column of the Table, so the numbers drift or turn to zero without an error.

**Step 8. Add the total row and the tie-out.** In row 21 enter `Total` and `=SUM(B18:B20)`, filled right. In row 22 enter `Entire SalesInvoice Table` and `=SUM(SalesInvoice[SubTotal])`, filled right (it shifts along the amounts, which is what the row needs). In B23 enter `=ROUND(B21-B22,2)` and fill it right to E23.

**Check:** row 23 is zero in all four columns, and the total row reads SubTotal $86,446,845.84, FreightAmount $621,267.34, TaxAmount $5,659,428.46 and GrandTotal $92,727,541.64.

### Requirement (5): Why this is not revenue

**Step 9. Write the note.** Three points, in two or three sentences. Credit memos are not netted: the CreditMemo worksheet holds 222 credit memos dated in 2026, with a SubTotal of $242,764.56. GrandTotal includes sales tax ($1,948,116.12), which is billed to customers and owed to the tax authority, so it is a liability. The ledger records freight billed ($214,588.22) in its own revenue account, 4050, and the tax in account 2050. Only SubTotal, net of credit memos, approaches product revenue.

**Check:** the note names all three, with the worksheet or account that shows each.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Invoices in the period (2026) | 7,171 | Step 4 |
| SubTotal, FreightAmount, TaxAmount, GrandTotal in the period | $29,756,420.08; $214,588.22; $1,948,116.12; $31,919,124.42 | Step 4 |
| SubTotal + FreightAmount + TaxAmount - GrandTotal | 0 | Step 5 |
| Fiscal 2024: invoices; SubTotal; GrandTotal | 6,735; $27,313,723.48; $29,293,739.11 | Step 7 |
| Fiscal 2025: invoices; SubTotal; GrandTotal | 7,008; $29,376,702.28; $31,514,678.11 | Step 7 |
| Fiscal 2026: invoices; SubTotal; GrandTotal | 7,171; $29,756,420.08; $31,919,124.42 | Step 7 |
| Total row: invoices; SubTotal; FreightAmount; TaxAmount; GrandTotal | 20,914; $86,446,845.84; $621,267.34; $5,659,428.46; $92,727,541.64 | Step 8 |
| Credit memos dated in 2026; SubTotal | 222; $242,764.56 | Step 9 |

![A mock of the Ex 4.1 worksheet at the end of the exercise, with the period cells, the period's billing and the billing schedule by fiscal year.](../figures/chapter-04-excel-essentials/IF-04-1-A.pdf)

> **Instructor notes, Exercise 4.1:** invoices by fiscal year 2024 / 2025 / 2026: 6,735 / 7,008 / 7,171 (20,914 in all). SubTotal 27,313,723.48 / 29,376,702.28 / 29,756,420.08 (86,446,845.84); FreightAmount 192,134.79 / 214,544.33 / 214,588.22; TaxAmount 1,787,880.84 / 1,923,431.50 / 1,948,116.12; GrandTotal 29,293,739.11 / 31,514,678.11 / 31,919,124.42. SubTotal + Freight + Tax = GrandTotal on every invoice. Limitations: credit memos are not netted (158 / 232 / 222 credit memos, SubTotal 145,655.35 / 201,104.38 / 242,764.56), sales tax billed to customers is owed to the tax authority, a liability rather than revenue, and freight billed is recorded in its own revenue account (4050). Grid formula, for example =SUMIFS(SalesInvoice\[SubTotal\],SalesInvoice\[\[InvoiceDate\]:\[InvoiceDate\]\],"\>="&DATE(\$A5,1,1),SalesInvoice\[\[InvoiceDate\]:\[InvoiceDate\]\],"\<="&DATE(\$A5,12,31)), entered once and filled right and down: filling across shifts SubTotal to the adjacent FreightAmount, TaxAmount, and GrandTotal columns, as the grid needs, while the locked \[\[InvoiceDate\]:\[InvoiceDate\]\] and the mixed \$A5 stay put (the Watch out on structured references). Pasted instead of filled, the formula keeps SubTotal in every column.

## What a strong answer says

- **Requirement (3).** Every total comes from COUNTIFS or SUMIFS on the named cells, and the difference check is zero.
- **Requirement (4).** One formula, filled, with the year and the date column locked, and a total row tied to the entire Table.
- **Requirement (5).** Credit memos not netted, sales tax as a liability, freight in its own revenue account, and the conclusion that SubTotal net of credit memos, not GrandTotal, is the starting point for revenue.

A weak answer calls GrandTotal revenue, lists only one limitation, or ties the total row to itself.

## Common mistakes and how to respond

- **A grid that repeats SubTotal.** *Symptom:* the four columns of a year show one number. *Cause:* the formula was pasted, not filled. *Response:* ask the student to click E18 and read the formula bar.
- **A date criterion that drifts.** *Symptom:* amounts that look right but differ from the period block. *Cause:* a fill across with InvoiceDate unlocked. *Response:* compare row 20 with B9 to B12 and read the formula.
- **Dates typed as text.** *Symptom:* zeros. *Response:* test the cells with ISNUMBER and check the **Settings** tab of the validation.
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
