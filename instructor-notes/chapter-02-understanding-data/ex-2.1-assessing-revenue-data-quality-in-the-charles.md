# Exercise 2.1: Assessing Revenue Data Quality in the Charles River O2C Tables

| | |
|---|---|
| Unit | Chapter 2: Understanding Data in Accounting |
| Item | Exercise 2.1 |
| Perspective | Financial accounting |
| Tools | Workbook browsing and written work |
| Time | About 60 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise is a readiness check before any revenue analysis: can the order, invoice and customer tables support a revenue figure? It asks for three kinds of evidence. Some tests find problems (dates that disagree across tables), some find none (line totals, references to customers), and some blanks are by design. The memo asks for a recommendation, not a list. The tests are descriptive; the analytics types come after.

By the end, students can:

- classify each problem by dimension and say when it touches two (chapter outcome 3);
- test a line total against its parts with a tolerance for rounding, and test a reference between two tables (outcome 4);
- separate a blank that is by design from one that is missing information (outcome 5);
- recommend, in one page, whether revenue can be reported and what must be resolved first.

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (extracting, transforming and cleansing financial data); IMA Data Literacy; IFAC IES 2 (i), using technology to analyze data, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.1.

## Before you assign

- Students need their working copy CharlesRiver_Work.xlsx and Tutorial 2.1. The tutorial's Check column on SalesInvoice answers the shipment-date question, and the exercise's worksheet list leaves Shipment out. Send students who skipped the tutorial back to Steps 6 and 7.
- The exercise relies on these conditions: SalesOrder has no blank OrderDate, CustomerID or Status; SalesInvoiceLine.LineTotal agrees with Quantity, UnitPrice and Discount to within rounding; every CustomerID in SalesOrder exists in Customer; the dates and numbers of a few invoices disagree with their orders and ledger postings; and several columns are blank by design (SalesOrder.Notes, SalesInvoice.PaymentDate, SalesInvoiceLine.ShipmentLineID, PromotionID and PriceOverrideApprovalID).
- Requirement (2) tells students that Discount is a rate and that a cent of difference is rounding. Give the tolerance of Step 6 only if a student reports hundreds of mismatches.
- The helper columns run over 27,933 invoice lines and 5,819 orders, which is quick.

## How to run it

Individual work, then a ten-minute comparison in pairs. For about 60 minutes: 25 on requirement 1, 10 on requirement 2, 10 on requirement 3 and 15 on the memo.

**Hints.** After ten minutes, if students have looked only at one worksheet at a time, ask which columns of two tables describe the same event. Give the pricing-method hint only when asked. **Collect** the memo and a copy of the helper columns, so you can check the counts.

## Step-by-step solution

### Requirement (1): Find and classify the problems

**Step 1. Test the required fields of SalesOrder.**

a. On **SalesOrder**, use the filter button of OrderDate, CustomerID and Status in turn to show only blank cells.
b. Read the count in the status bar each time, then clear the filter.
c. Do the same for Notes.

**Check:** no blanks in OrderDate, CustomerID or Status among 5,819 orders. Notes is blank on 5,580 orders, by design, because it is optional free text. **Watch for:** students who list the blank Notes as a completeness problem.

**Step 2. Compare the customers that share a name.** Sort **Customer** by CustomerName, find the adjacent pairs, and compare City, Region, CustomerSegment and the orders of each (filter SalesOrder by CustomerID).

The Customer table has 2 shared names:

| Name | CustomerID | City | Region | Segment | Orders | Active |
|---|---:|---|---|---|---:|---|
| Brown LLC | 5 | Moniqueborough | West | Design Trade | 20 | yes |
| Brown LLC | 173 | Kingfurt | Midwest | Strategic | 51 | yes |
| Smith Ltd | 170 | Rachelberg | Northeast | Small Business | 11 | yes |
| Smith Ltd | 220 | Dustinfurt | Northeast | Small Business | 0 | no |

**Check:** the model conclusion is two different companies in each pair, not duplicates, because the cities, contacts and addresses differ. The pair that shares a region and a segment is the harder one: students must go to the city and the activity. This is a consistency risk. A report grouped by name would merge the pair into one line.

**Step 3. Read the Item blanks.** Filter **Item** for a blank ListPrice and read ItemGroup.

**Check:** 43 blank list prices, in Capex (11), Packaging (10), Raw Materials (11), and Services (11). The 223 other items are the ones sold. These are by design: Charles River buys these items. In the same table, 15 item names are shared by 35 items with different codes and costs; Exercise 2.3 examines them.

**Step 4. Compare dates and numbers across tables.**

a. On **SalesInvoice**, in the first free column after Tutorial 2.1's Check column, look up each invoice's order date:

   ```
   =XLOOKUP(E2, SalesOrder!A:A, SalesOrder!C:C)
   ```

b. In the next column, flag an invoice dated before its order: `=C2<O2`.
c. In a third column, flag an invoice number whose year differs from the invoice date's year: `=VALUE(MID(B2,4,4))<>YEAR(C2)`.
d. Filter each flag for TRUE, and filter Tutorial 2.1's Check column for "Check".

**Check:** 3 invoices are dated before their order, 9 before the first shipment on their order, and 6 carry a year in their number that differs from their date.

| Invoice | InvoiceDate | Year of the ledger posting |
|---|---|---|
| SI-2025-006733 | 2024-11-23 | 2025 |
| SI-2025-006734 | 2024-12-05 | 2025 |
| SI-2025-006735 | 2024-12-15 | 2025 |
| SI-2026-013741 | 2025-11-29 | 2026 |
| SI-2026-013742 | 2025-12-04 | 2026 |
| SI-2026-013743 | 2025-12-03 | 2026 |

These invoices are dated in one fiscal year and numbered and posted in the next, so revenue by invoice date and revenue by posting date differ for them. That is an accuracy problem with a cutoff consequence, and Exercise 6.1 returns to it. The invoices dated before their order are the first invoices of the data. **Watch for:** students who stop at "the dates look odd" without saying what changes in a revenue total.

**Step 5. Record the blanks that are by design.** Filter the Table columns in turn and note: ShipmentLineID blank on 439 invoice lines (the design service lines, which ship nothing), PromotionID on 25,825, PriceOverrideApprovalID on 27,419, and PaymentDate on 911 invoices.

**Check:** each is explained by the business. 866 of the invoices with no PaymentDate are Submitted and unpaid, 35 were settled by a credit memo, and 10 are partly settled.

### Requirement (2): Test LineTotal and the pricing method

**Step 6. Test LineTotal against its parts.**

a. On **SalesInvoiceLine**, add a column headed `Difference` with the unrounded line amount less LineTotal, in absolute value:

   ```
   =ABS(G2*I2*(1-J2)-K2)
   ```

b. Copy it down, then read the largest value with `=MAX(P:P)` and the count above one cent with `=COUNTIF(P:P,">0.01")`.
c. Sort the column from largest to smallest and look at the top rows.

![A mock of the SalesInvoiceLine worksheet with the Difference helper column of Step 6, sorted largest first.](../figures/chapter-02-understanding-data/IF-02-1-A.pdf)

**Check:** the largest difference is 0.005, half a cent, and 0 of 27,933 lines differ by more than a cent. The columns are all filled, so the table holds what is needed to calculate revenue: LineTotal is the amount billed before freight, tax and later credits. **Watch for:** a formula that uses Discount in place of 1 − Discount, which flags thousands of lines, and an `=` comparison that flags rounding.

**Step 7. Count the lines by PricingMethod.** Insert a PivotTable of counts by PricingMethod, or filter the column.

| PricingMethod | Lines |
|---|---:|
| Segment Price List | 24,697 |
| Customer Price List | 2,283 |
| Approved Override | 514 |
| Base List | 439 |

**Check:** 514 lines are priced by approved override, with a total of $1,655,302.02. They deserve closer review because they leave the price lists: an approval authorizes the price. Each carries an override approval key, so the next test is whether the approval exists and sits within authority, which Chapter 8 takes up.

### Requirement (3): Test the reference to Customer

**Step 8. Count the matches for every order.**

a. On **SalesOrder**, in the first free column, add `=COUNTIFS(Customer!A:A, D2)` (or XLOOKUP).
b. Filter the column for 0.

**Check:** no rows: 0 of 5,819 orders are orphaned. A clean result says that every order names a customer who exists. It does not say that the customer is the right one, or that every customer has ordered: 9 customers have no order, and all are inactive. Record the test, the population and the result.

### Requirement (4): Write the memo

**Step 9. Outline a one-page memo.** A strong memo has a header and the purpose; a short conclusion up front (the data can support revenue reporting once the cutoff items are resolved); a table with one row per finding (table and column, dimension, count, error or by design); the tests that found nothing; and recommended resolutions: decide the date basis for the 6 year-end invoices, group by CustomerID and not by name, and report design service revenue separately because it has no shipment.

**Check:** the conclusion is stated before the evidence, and the memo separates errors from judgments.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Orders; blanks in OrderDate, CustomerID and Status | 5,819; 0, 0, 0 | Step 1 |
| Same-name pairs | 2 | Step 2 |
| Blank list prices; items sold | 43; 223 | Step 3 |
| Invoices dated before their order | 3 | Step 4 |
| Invoices dated before the first shipment | 9 | Step 4 |
| Invoice numbers with a different year from the date | 6 | Step 4 |
| Invoice lines; lines over one cent; largest difference | 27,933; 0; 0.005 | Step 6 |
| Lines by approved override; their total | 514; $1,655,302.02 | Step 7 |
| Orphaned orders; customers with no orders | 0; 9 | Step 8 |

## What a strong answer says

- **Requirement (1).** Each problem with its table, column, dimension and count; the same-name pairs treated as different companies on evidence; the date problems tied to cutoff; the blanks sorted into by design and missing.
- **Requirement (2).** A tolerance of one cent with the reason, the result that the table agrees with itself, and the override lines named for review with a next step.
- **Requirement (3).** The result and what it does not show.
- **Requirement (4).** A recommendation that follows from the evidence and names what must be settled first.

A weak answer lists problems with no counts, calls every blank an error, or recommends "the data is fine" or "the data is unusable" without conditions.

## Common mistakes and how to respond

- **The same-name pair called a duplicate.** *Symptom:* "merge them". *Response:* ask what in the rest of the record says they are one company.
- **Every blank called an error.** *Symptom:* Notes or ListPrice in the problems list. *Response:* ask who would fill the value in, and whether the business needs it.
- **Rounding flagged as an error.** *Symptom:* hundreds of mismatched lines. *Response:* ask how much a cent of rounding can move a total, and what tolerance the exercise gave.
- **Date problems without a consequence.** *Symptom:* "invoice dated before shipment" and nothing more. *Response:* ask which period's revenue changes.
- **A clean result left out.** *Symptom:* no mention of the orphan test. *Response:* ask what the reader of the memo knows if the test is missing.
- **Orphans mistaken for blanks.** *Symptom:* "no blank customers, so references are fine". *Response:* ask the difference between a blank reference and a reference to a record that does not exist.
- **A memo that is a log.** *Symptom:* a list of steps in the order run. *Response:* ask for the conclusion first, then evidence by dimension.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: problems found, classified and counted | 35 | Cross-table dates, same-name pairs and by-design blanks, each with table, column, dimension and count | Single-table checks only, or no counts |
| Requirement 2: LineTotal and PricingMethod | 25 | Tolerance stated, result reported, override lines flagged with a next step | Test without a tolerance, or no override discussion |
| Requirement 3: orphan test | 15 | Test, result and what a clean result does not show | Result only |
| Requirement 4: memo | 25 | One page, conclusion first, errors separated from judgments, conditions named | A list of findings with no recommendation |

## Extensions and discussion questions

- Test that each invoice's SubTotal equals the sum of its lines (SUMIFS on SalesInvoiceLine) and say what the result shows.
- Add the ledger's posting date for the 6 year-end invoices and recompute revenue for each fiscal year on both bases.
- Discuss: should revenue be dated by invoice, by shipment or by the ledger's posting date, and who decides? (Chapters 6 and 12 return to it.)
- Discuss: which of the findings would you raise with the sales team, and which with the accounting team?
