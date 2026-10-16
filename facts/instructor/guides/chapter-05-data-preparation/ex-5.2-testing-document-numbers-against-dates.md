---
note: ch05.ex2
uses: [ch05.g2]
title: Testing Document Numbers Against Dates
kind: exercise
number: '5.2'
unit: '5'
perspective: financial
tool: excel
minutes: 60
solution: "Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheet Ex 5.2 (the test columns are on the SalesInvoice worksheet)"
figures:
  - id: IF-05-2-A
    kind: excel-mock
    purpose: The invoices flagged by either test, beside Tutorial 2.1's list of invoices dated before their first shipment.
    shows: "A list headed InvoiceNumber, InvoiceDate, OrderDate, NumberYear, NumberYearMatches, BeforeOrder and In Tutorial 2.1 list, with one row for each flagged invoice, sorted by number. Below it, after a blank row, a second list headed Tutorial 2.1 InvoiceNumber, InvoiceDate and First ShipmentDate, typed as values. In the first list the rows whose NumberYearMatches is FALSE are outlined as one group and the rows whose BeforeOrder is TRUE as another, so no row is in both. Above the first list sit four counts: invoices whose number year differs, invoices dated before their order, invoices flagged by either test, and Tutorial 2.1 invoices that neither test flags."
    data: SalesInvoice, SalesOrder and the first shipment of each order (the Expected results table).
---
{% set g = ch05_g2 %}
# Exercise 5.2: Testing Document Numbers Against Dates

{{ header() }}

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
- **Data conditions.** {{ g.n_invoices|count }} invoices. Order and shipment numbers always carry the year of their date, so the mismatch is peculiar to invoices. The flagged invoices are dated in November, December or the first days of January.
- **Where the columns go.** Tutorial 5.1 ended at column {{ g.letters.StandardTerms }} (StandardTerms). The exercise adds NumberYearText in column {{ g.letters.NumberYearText }}, NumberYear in {{ g.letters.NumberYear }}, NumberYearMatches in {{ g.letters.NumberYearMatches }}, OrderDate in {{ g.letters.OrderDate }} and BeforeOrder in {{ g.letters.BeforeOrder }}. Exercise 5.4 adds OrderToInvoiceDays in {{ g.letters.OrderToInvoiceDays }}.

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

**Check:** {{ g.n_prefix|count }} invoices, each numbered for the year after its date: {% for y in g.by_year %}{{ y.numbers }} are dated in {{ y.dated }} and numbered {{ y.numbered }}{{ '; ' if not loop.last else '' }}{% endfor %}. **Watch for:** a comparison of the text year with YEAR. Excel never treats the text 2025 as equal to the number 2025, so every one of the {{ g.n_invoices|count }} invoices comes out FALSE. A count equal to the whole Table is the symptom.

### Requirement (3): The order test

**Step 3. Look up the order date and flag.** Add `OrderDate` with the formula below, formatted as a date, then `BeforeOrder`, and count:

```
=XLOOKUP([@SalesOrderID],SalesOrder[SalesOrderID],SalesOrder[OrderDate],"No match")
=[@InvoiceDate]<[@OrderDate]
=COUNTIF(SalesInvoice[BeforeOrder],TRUE)
```

**Check:** {{ g.n_before|count }} invoices, each dated a day before its order. No invoice reads "No match". **Watch for:** an unmatched lookup. Excel orders text above numbers, so an invoice date compares as less than "No match" and the row is flagged. Count "No match" before reading the flags.

### Requirement (4): The combined list

**Step 4. List the invoices flagged by either test.** The model answer spills the list with one formula; a student without HSTACK filters the Table twice (NumberYearMatches FALSE, then BeforeOrder TRUE) and copies each result.

```
=SORT(FILTER(HSTACK(SalesInvoice[InvoiceNumber],SalesInvoice[InvoiceDate],SalesInvoice[OrderDate],SalesInvoice[NumberYear],SalesInvoice[NumberYearMatches],SalesInvoice[BeforeOrder]),(SalesInvoice[NumberYearMatches]=FALSE)+(SalesInvoice[BeforeOrder]=TRUE)),1)
```

**Step 5. Compare with Tutorial 2.1.** In CharlesRiver_Work.xlsx filter the Check column of the SalesInvoice worksheet for "Check", and put the result beside the list.

**Check:** {{ w_both }} invoices flagged, the same {{ w_shipment }} as Tutorial 2.1. The two tests share {{ w_overlap }} invoices, and each finds only part of the nine. **Watch for:** a student who stops after the first test and calls the numbers reliable. The three invoices that carry the right prefix would be missed.

### Requirement (5): The memo

**Step 6. Write the half page.** The outline: the two tests and what each compares; the results, with the nine invoices and which test finds which; the effect on cutoff (a revenue period could be wrong, in either direction); and the evidence to request. The six invoices with the next year's prefix carry ${{ g.pre_sub|money }} of subtotal and all nine ${{ g.all_sub|money }}. The evidence: invoice creation logs, shipping documents and customer acknowledgments, and how the billing system assigns invoice numbers and dates.

**Check:** the memo states that neither test shows who dated the invoices or why.

## Expected results

| Invoice | InvoiceDate | OrderDate | First shipment | Number year differs | Before order |
|---|---|---|---|:---:|:---:|
{% for r in g.nine %}
| {{ r.number }} | {{ r.date }} | {{ r.order }} | {{ r.ship }} | {{ 'TRUE' if r.prefix else 'FALSE' }} | {{ 'TRUE' if r.before else 'FALSE' }} |
{% endfor %}
| Invoices flagged by each test; by either | | | | {{ g.n_prefix|count }} | {{ g.n_before|count }}; {{ (g.n_prefix + g.n_before)|count }} |
| Order and shipment numbers whose year differs from their date; lookups not matched | 0; 0 | | | | |

{{ figure('IF-05-2-A') }}

{{ expected() }}

## What a strong answer says

- **Requirements (2) and (3).** Two counts, with the reason that a text year needs VALUE and that a lookup is checked for "No match" before its result is used.
- **Requirement (4).** The two tests find different invoices and together find exactly Tutorial 2.1's. The findings are consistent with invoices dated earlier than the events they record, which the evidence the memo requests would test.
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
| Requirement 2: comparison | 20 | A flag column and a count of {{ g.n_prefix|count }} | Count without a flag column |
| Requirement 3: order test | 20 | A lookup, a flag, a count of {{ g.n_before|count }} | Lookup failures not counted |
| Requirement 4: the list | 20 | All {{ w_both }} invoices, compared with Tutorial 2.1 | List without the comparison |
| Requirement 5: the memo | 25 | Tests, results, cutoff effect, evidence to request, limits stated | Results without the limits |

## Extensions and discussion questions

- Add a flag for invoices dated before their first shipment by loading the Shipment Table and using MINIFS, as Tutorial 2.1 did, and show that it finds the same {{ w_shipment }}.
- Test the order numbers and the shipment numbers in the same way and report why a clean result is still a finding.
- Discuss: Exercise 6.1 and Exercise 12.1 return to these invoices through the ledger. What would you check there that this workbook cannot show?
- Discuss: an invoice date is typed or assigned by a system. Which would you expect, and what evidence would tell you?
