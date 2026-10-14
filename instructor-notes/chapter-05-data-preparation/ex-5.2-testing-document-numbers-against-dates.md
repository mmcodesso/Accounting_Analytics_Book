# Exercise 5.2: Testing Document Numbers Against Dates

| | |
|---|---|
| Unit | Chapter 5: Data Preparation and Cleaning in Excel |
| Item | Exercise 5.2 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 60 minutes |
| Solution file | Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheet Ex 5.2 (the test columns are on the SalesInvoice worksheet) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise turns two ideas of the chapter into an audit-style test: a number that encodes a year should agree with the date, and a document should not be dated before the event it follows. Students extract the year with MID, convert it with VALUE, look up the order date and compare. They then meet a finding that no single test shows, and write it up as a cutoff risk. The analytics type is descriptive, with a diagnostic question behind it.

By the end, students can:

- extract and convert a field with text functions, and compare it with a date function's result (outcomes 2 and 3);
- bring a date from a related Table with a lookup and flag the rows that fail an order test (outcome 4);
- reconcile two independent tests to an earlier finding and say what each test misses (outcomes 1 and 6);
- write a memo that states the evidence and its limits (outcome 1).

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (financial data: extraction, transformation and cleansing) and Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Literacy, and Financial Recordkeeping; IFAC IES 2 (a) and IES 4 (a), professional skepticism and professional judgment; AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 5.3: the SalesOrder Table from Tutorial 5.2 must be in it, because the order date comes from there.
- **Part I workbook.** Requirement (4) compares the results with Tutorial 2.1's Check column in CharlesRiver_Work.xlsx. A student without that workbook can repeat Tutorial 2.1's MINIFS on the Shipment Table, or you can hand out the list in the Expected results below. The model answer types the list as values, because the analysis workbook never loads the Shipment Table.
- **Data conditions.** 20,914 invoices. Order and shipment numbers always carry the year of their date, so the mismatch is peculiar to invoices. The flagged invoices are dated in November, December or the first days of January.
- **Where the columns go.** Tutorial 5.1 ended at column R (StandardTerms). The exercise adds NumberYearText in column S, NumberYear in T, NumberYearMatches in U, OrderDate in V and BeforeOrder in W. Exercise 5.4 adds OrderToInvoiceDays in X.

## How to run it

Individual or pairs, about 60 minutes: 10 on the year columns (requirement 1), 10 on the comparison (2), 10 on the order test (3), 15 on the list and the comparison with Tutorial 2.1 (4) and 15 on the memo (5). Hold back the hint about VALUE until a student's count equals the number of invoices. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The year in the number

**Step 1. Extract and convert.** In the first empty cell right of the last header of the SalesInvoice Table, type `NumberYearText` and enter `=MID([@InvoiceNumber],4,4)`. In the next column type `NumberYear`, enter `=VALUE([@NumberYearText])` and format the column as a number with no decimals.

**Check:** SI-2025-007947 returns the text 2025 and then the number 2025. **Watch for:** a start position one off. MID then returns three digits and a hyphen, NumberYear is not a year, and every invoice looks mismatched.

### Requirement (2): Compare with the invoice date

**Step 2. Test and count.** Add `NumberYearMatches` with the formula below, then on a sheet named `Ex 5.2` enter the count beneath it:

```
=[@NumberYear]=YEAR([@InvoiceDate])
=COUNTIF(SalesInvoice[NumberYearMatches],FALSE)
```

**Check:** 6 invoices, each numbered for the year after its date: SI-2025-006733, SI-2025-006734, and SI-2025-006735 are dated in 2024 and numbered 2025; SI-2026-013741, SI-2026-013742, and SI-2026-013743 are dated in 2025 and numbered 2026. **Watch for:** a comparison of the text year with YEAR. Excel never treats the text 2025 as equal to the number 2025, so every one of the 20,914 invoices comes out FALSE. A count equal to the whole Table is the symptom.

### Requirement (3): The order test

**Step 3. Look up the order date and flag.** Add `OrderDate` with the formula below, formatted as a date, then `BeforeOrder`, and count:

```
=XLOOKUP([@SalesOrderID],SalesOrder[SalesOrderID],SalesOrder[OrderDate],"No match")
=[@InvoiceDate]<[@OrderDate]
=COUNTIF(SalesInvoice[BeforeOrder],TRUE)
```

**Check:** 3 invoices, each dated a day before its order. No invoice reads "No match". **Watch for:** an unmatched lookup. Excel orders text above numbers, so an invoice date compares as less than "No match" and the row is flagged. Count "No match" before reading the flags.

### Requirement (4): The combined list

**Step 4. List the invoices flagged by either test.** The model answer spills the list with one formula; a student without HSTACK filters the Table twice (NumberYearMatches FALSE, then BeforeOrder TRUE) and copies each result.

```
=SORT(FILTER(HSTACK(SalesInvoice[InvoiceNumber],SalesInvoice[InvoiceDate],SalesInvoice[OrderDate],SalesInvoice[NumberYear],SalesInvoice[NumberYearMatches],SalesInvoice[BeforeOrder]),(SalesInvoice[NumberYearMatches]=FALSE)+(SalesInvoice[BeforeOrder]=TRUE)),1)
```

**Step 5. Compare with Tutorial 2.1.** In CharlesRiver_Work.xlsx filter the Check column of the SalesInvoice worksheet for "Check", and put the result beside the list.

**Check:** nine invoices flagged, the same nine as Tutorial 2.1. The two tests share zero invoices, and each finds only part of the nine. **Watch for:** a student who stops after the first test and calls the numbers reliable. The three invoices that carry the right prefix would be missed.

### Requirement (5): The memo

**Step 6. Write the half page.** The outline: the two tests and what each compares; the results, with the nine invoices and which test finds which; the effect on cutoff (a revenue period could be wrong, in either direction); and the evidence to request. The six invoices with the next year's prefix carry $5,231.42 of subtotal and all nine $12,719.09. The evidence: invoice creation logs, shipping documents and customer acknowledgments, and how the billing system assigns the invoice date.

**Check:** the memo states that neither test shows who dated the invoices or why.

## Expected results

| Invoice | InvoiceDate | OrderDate | First shipment | Number year differs | Before order |
|---|---|---|---|:---:|:---:|
| SI-2024-000001 | 2024-01-01 | 2024-01-02 | 2024-01-03 | FALSE | TRUE |
| SI-2024-000002 | 2024-01-02 | 2024-01-03 | 2024-01-04 | FALSE | TRUE |
| SI-2024-000003 | 2024-01-01 | 2024-01-02 | 2024-01-03 | FALSE | TRUE |
| SI-2025-006733 | 2024-11-23 | 2024-11-21 | 2024-11-25 | TRUE | FALSE |
| SI-2025-006734 | 2024-12-05 | 2024-11-02 | 2024-12-07 | TRUE | FALSE |
| SI-2025-006735 | 2024-12-15 | 2024-12-07 | 2024-12-17 | TRUE | FALSE |
| SI-2026-013741 | 2025-11-29 | 2025-11-14 | 2025-12-01 | TRUE | FALSE |
| SI-2026-013742 | 2025-12-04 | 2025-11-30 | 2025-12-06 | TRUE | FALSE |
| SI-2026-013743 | 2025-12-03 | 2025-11-23 | 2025-12-05 | TRUE | FALSE |
| Invoices flagged by each test; by either | | | | 6 | 3; 9 |
| Order and shipment numbers whose year differs from their date; lookups not matched | 0; 0 | | | | |

![A mock of the invoices flagged by either test, beside Tutorial 2.1's list of invoices dated before their first shipment.](../figures/chapter-05-data-preparation/IF-05-2-A.pdf)

> **Instructor notes, Exercise 5.2:** six invoices carry the next year's number prefix: SI-2025-006733 (2024-11-23), SI-2025-006734 (2024-12-05), SI-2025-006735 (2024-12-15), SI-2026-013741 (2025-11-29), SI-2026-013742 (2025-12-04), SI-2026-013743 (2025-12-03). Three invoices are dated before their order: SI-2024-000001 (2024-01-01, order 2024-01-02), SI-2024-000002 (2024-01-02, order 2024-01-03), SI-2024-000003 (2024-01-01, order 2024-01-02). These nine are exactly the nine invoices dated before their first shipment in Tutorial 2.1. Together they are consistent with invoices dated earlier than the events they record (the six are numbered in the following year but dated in the year before), a revenue cutoff risk, although neither test shows who dated them or why. Order and shipment numbers show no such mismatch. Evidence to request: the invoice creation logs, the shipping documents, and customer acknowledgments.

## What a strong answer says

- **Requirements (2) and (3).** Two counts, with the reason that a text year needs VALUE and that a lookup is checked for "No match" before its result is used.
- **Requirement (4).** The two tests find different invoices and together find exactly Tutorial 2.1's. The findings point one way: these invoices are dated earlier than the events they record.
- **Requirement (5).** A cutoff risk with its limits. The six year-end invoices are the first numbers issued in each following year, yet dated before it began, which suggests dating back into the earlier period. The three invoices dated a day before their order cannot be explained by numbering. Neither test shows who dated them or why, so the memo asks for logs and shipping documents, and it does not call the invoices errors or fraud.

A weak answer reports counts without comparing them with Tutorial 2.1, or states a cause.

## Common mistakes and how to respond

- **Text compared with a number.** *Symptom:* every invoice flagged. *Response:* click NumberYearText and NumberYear and ask which one is left-aligned.
- **A wrong MID start.** *Symptom:* NumberYear is not a four-digit year and every invoice is flagged. *Response:* count the characters of an invoice number against the formula's two arguments.
- **A "No match" flagged as before order.** *Response:* count the lookup's failures first.
- **Stopping at one test.** *Response:* ask what a prefix test cannot see, and which Tutorial 2.1 invoices it misses.
- **Fixing the dates.** *Response:* the exercise asks for evidence, and a data owner corrects records.
- **A memo that names a cause.** *Response:* ask what the data would have to show to support it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: extraction | 15 | MID and VALUE, a numeric column | Text left in the comparison |
| Requirement 2: comparison | 20 | A flag column and a count of 6 | Count without a flag column |
| Requirement 3: order test | 20 | A lookup, a flag, a count of 3 | Lookup failures not counted |
| Requirement 4: the list | 20 | All nine invoices, compared with Tutorial 2.1 | List without the comparison |
| Requirement 5: the memo | 25 | Tests, results, cutoff effect, evidence to request, limits stated | Results without the limits |

## Extensions and discussion questions

- Add a flag for invoices dated before their first shipment by loading the Shipment Table and using MINIFS, as Tutorial 2.1 did, and show that it finds the same nine.
- Test the order numbers and the shipment numbers in the same way and report why a clean result is still a finding.
- Discuss: Exercise 6.1 and Exercise 12.1 return to these invoices through the ledger. What would you check there that this workbook cannot show?
- Discuss: an invoice date is typed or assigned by a system. Which would you expect, and what evidence would tell you?
