# Exercise 2.6: Testing for Duplicate Payments

| | |
|---|---|
| Unit | Chapter 2: Understanding Data in Accounting |
| Item | Exercise 2.6 |
| Perspective | Auditing |
| Tools | Workbook browsing and written work |
| Time | About 75 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Duplicate payments are a classic audit risk, and a first test in Excel is easy to write and easy to over-read. The exercise asks for three tests (a repeated invoice number, a repeated check number, an invoice paid above its total), a judgment about each match, and an honest statement of what the tests cannot find. Its lesson is that a match is a question for the supplier and the payables team, not a finding, and that a clean result is limited by what the test looks at. It is the first exercise to point past the chapter's tools toward SQL. The tests are descriptive procedures.

By the end, students can:

- count repeats with COUNTIFS on a pair of columns and read the result (chapter outcome 4);
- judge a pair of records and name the evidence that would settle it (outcome 5);
- explain what a test that finds nothing does and does not prove (outcome 6);
- write a short memo that states the matches, the conclusions and the limits.

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance) and Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Analysis and Internal Control; IFAC IES 2 (f), audit, and IES 4 (a), professional skepticism and judgment; AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx. PurchaseInvoice has 40,204 rows and DisbursementPayment 40,127, so a COUNTIFS over whole columns recalculates slowly. Tell students to wait, or to switch calculation to manual while they build the columns.
- The exercise relies on these conditions: a few supplier invoice numbers appear twice for the same supplier, a few check numbers appear twice for the same supplier, a payment carries a check number only when its method is Check, and no invoice is paid above its GrandTotal once both sides are rounded to the cent.
- The generator's own log of planted anomalies lists more repeated payment references than the data holds. Do not quote that count to students: the data holds two repeated check numbers, and the note under Expected results says so.
- Requirement (4) asks for rounding to the cent. Students who skip it get false matches.

## How to run it

Individual work, then a pair discussion of requirement (3). For about 75 minutes: 10 on requirement 1, 20 on requirement 2, 15 on requirement 3, 15 on requirement 4, 5 on requirement 5 and 10 on the memo.

**Hints.** If a student reports hundreds of overpaid invoices, ask how the amounts were rounded. If a student concludes that a pair is a duplicate, ask what else would be the same if it were. Hold back the SQL discussion until requirement (5). **Collect** the memo and the helper columns.

## Step-by-step solution

### Requirement (1): Identify the fields

**Step 1. Read the two worksheets and name the fields.** On **PurchaseInvoice**, note SupplierID, InvoiceNumber, InvoiceDate, GrandTotal and PurchaseOrderID. On **DisbursementPayment**, note SupplierID, PurchaseInvoiceID, Amount, PaymentDate, PaymentMethod and CheckNumber.

**Check:** the fields support three tests: a repeated supplier and invoice number, a repeated supplier and check number, and an invoice whose payments exceed its total. A PivotTable of PaymentMethod shows which payments have a check number, and only payments by check carry one, so 27,997 payments cannot be tested that way:

| PaymentMethod | Payments | With a check number |
|---|---:|---:|
| ACH | 24,037 | 0 |
| Check | 12,130 | 12,130 |
| Wire Transfer | 3,960 | 0 |

### Requirement (2): Count the repeats

**Step 2. Count each invoice number for its supplier.**

a. On **PurchaseInvoice**, in the first free column, enter this formula and copy it down:

   ```
   =COUNTIFS(G:G,G2,B:B,B2)
   ```

b. Filter the column for values above 1, and sort by SupplierID and InvoiceNumber.

![A mock of the PurchaseInvoice worksheet with the Count helper column of Step 2, filtered to the repeated invoice numbers.](../figures/chapter-02-understanding-data/IF-02-6-A.pdf)

**Check:** six invoice numbers appear twice, for suppliers 1 and 2, one pair each in every fiscal year.

| Invoice number | Supplier | First invoice (ID, date, amount) | Second invoice (ID, date, amount) |
|---|---:|---|---|
| V0001-2024-000028 | 1 | 28, 2024-01-31, $629.94 | 44, 2024-02-05, $1,504.07 |
| V0001-2025-006944 | 1 | 6944, 2025-01-01, $76.36 | 7323, 2025-01-07, $324.91 |
| V0001-2026-020922 | 1 | 20335, 2026-01-06, $38.20 | 20922, 2026-01-05, $293.09 |
| V0002-2024-000182 | 2 | 182, 2024-02-29, $4,152.60 | 308, 2024-03-04, $3,454.20 |
| V0002-2025-007283 | 2 | 7235, 2025-01-05, $936.16 | 7283, 2025-01-02, $372.70 |
| V0002-2026-020338 | 2 | 20236, 2026-01-09, $135.99 | 20338, 2026-01-08, $382.73 |

**Step 3. Count each check number for its supplier.**

a. On **DisbursementPayment**, in the first free column, enter and copy down:

   ```
   =IF(H2="","",COUNTIFS(D:D,D2,H:H,H2))
   ```

b. Filter the column for 2.

**Check:** two check numbers repeat, both for supplier 1, each on two payments. Payments by ACH or wire show a blank and are left out. **Watch for:** a COUNTIFS on the check number alone, which would count a check number reused by a different supplier as a match.

### Requirement (3): Judge each pair

**Step 4. Compare the two records of each pair.** For the invoice pairs, compare the dates, the amounts and the purchase orders, and look up the payments of each invoice. For the check pairs, compare the payment dates, the invoices paid and the amounts.

**Check, invoice pairs:** the dates differ in six of the six pairs, every pair has different amounts, the two invoices of a pair are on different purchase orders, and each invoice was paid once. That is consistent with a reused number on two different transactions. It does not rule out one obligation entered twice with a changed date or amount, so the pairs stay open until the original invoices, the purchase orders and receipts, or the supplier's statement settle them.

**Check, check pairs:**

| Check number | Payment | Date | Invoice paid | Amount | Invoice total |
|---|---|---|---|---:|---:|
| CHK0006076 | DP-2025-006076 | 2025-01-01 | V0001-2024-003101 | $1,468.04 | $6,992.56 |
| CHK0006076 | DP-2025-006107 | 2025-01-01 | V0001-2024-004070 | $1,104.48 | $7,447.81 |
| CHK0019708 | DP-2026-019708 | 2026-01-01 | V0001-2025-016316 | $1,158.23 | $2,049.65 |
| CHK0019708 | DP-2026-019843 | 2026-01-01 | V0001-2025-017518 | $1,023.55 | $1,978.40 |

Each pair pays two different invoices of different amounts, which is consistent with one check number reused on two payments rather than one payment made twice, but does not settle it. The pairs stay open until the bank's record of the checks that cleared and the payables team's check register, with any void and reissue, settle them.

### Requirement (4): Test each invoice for overpayment

**Step 5. Compare each invoice's payments with its total.**

a. On **PurchaseInvoice**, in the next free column, total the payments of the invoice and subtract its total, both rounded to the cent:

   ```
   =ROUND(SUMIFS(DisbursementPayment!F:F,DisbursementPayment!E:E,A2),2)-ROUND(J2,2)
   ```

b. Copy it down and filter the column for values above 0.

**Check:** no invoice is paid above its total (0 flagged). Of the 40,204 invoices, 36,980 are paid in full, 183 in part, and 3,041 not at all, and 2,641 were paid in installments, which is normal. **Watch for:** two traps. Without the rounding, a comparison flags 259 invoices that are paid exactly, because a sum of many amounts differs from the total by a fraction of a cent (that count is from a SQL comparison; the point is why the book asks for ROUND). And unpaid invoices show a negative difference, which is not an error.

A model answer on what a clean result shows: recorded payments never exceed an invoice. It does not show that the invoices are valid, or that two invoice IDs are two obligations: an invoice entered twice would be paid twice, each within its own total.

### Requirement (5): Judge the approach

**Step 6. Name what the tests would miss.** A model list: the same invoice entered with a slightly different number; a repeat paid with a different amount; a payment by ACH or wire, which has no check number; and the same supplier and amount on two different invoices. Chapter 8 tests that last pattern and finds 113 supplier-and-amount pairs on different dates, 13 within 30 days, none paying the same invoice.

**Check:** the answer gives at least three misses and a reason SQL helps: it can group by several columns, join a table to itself and test near matches in one query over the whole table, without a helper column on tens of thousands of rows, and the query can be saved and rerun.

### Requirement (6): Write the memo

**Step 7. Outline half a page.** A strong memo lists the pairs found and the check numbers (in the attached schedule that requirement (6) allows), the conclusion for each, the overpayment result with its meaning, and the limits, ending with the evidence it would request.

**Check:** it states each conclusion as open or closed and names the evidence that would settle it.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Invoice numbers that appear twice for one supplier | 6 | Step 2 |
| Repeated check numbers; supplier | 2; 1 | Step 3 |
| Payments with no check number | 27,997 | Step 1 |
| Invoices paid above their total, after rounding | 0 | Step 5 |
| Invoices paid in installments | 2,641 | Step 5 |
| Supplier-and-amount pairs on different dates; within 30 days | 113; 13 | Step 6 |

> **Instructor notes, Exercise 2.6:** six supplier invoice numbers appear twice for the same supplier (suppliers 1 and 2, one pair each per year, for example V0002-2024-000182); each pair has different dates and amounts and each invoice was paid once. That is consistent with a reused invoice number, but it does not rule out one obligation entered twice under two IDs with a changed date or amount, so the pairs stay open until the original invoices, the purchase orders and receipts, or the supplier's statement settle them. Two check numbers repeat for supplier 1 (CHK0006076 on payments 6076 and 6107, CHK0019708 on payments 19708 and 19843); each pair pays two different invoices of different amounts. The SUMIFS test, with both sides rounded to the cent, finds no invoice paid above its GrandTotal (2,641 invoices were paid in installments): recorded payments never exceed an invoice, which shows neither that the invoices are valid nor that two invoice IDs are two obligations. The generator's AnomalyLog lists six duplicate payment references, but only these two are present in the data.

## What a strong answer says

- **Requirement (2).** The pairs and the check numbers, found with a formula on supplier and number together.
- **Requirement (3).** Each pair read as open, with the evidence it would take to close it: the original invoices, the purchase orders and receipts, the supplier's statement, the bank's record.
- **Requirement (4).** The rounded test, its clean result, and a statement of what the result cannot show.
- **Requirement (5).** At least three misses and a reason that SQL is better suited.
- **Requirement (6).** A half-page memo with each conclusion marked open or closed.

A weak answer calls the matches duplicate payments, or calls the clean overpayment test proof that no duplicate exists.

## Common mistakes and how to respond

- **A match called a duplicate payment.** *Symptom:* "the supplier was paid twice". *Response:* ask what the dates, amounts and invoices show.
- **No rounding.** *Symptom:* many invoices flagged as overpaid. *Response:* ask how a sum of many cents compares with a total.
- **Check numbers tested alone.** *Symptom:* a COUNTIFS on CheckNumber only. *Response:* ask whether two suppliers can use the same number.
- **ACH and wire counted.** *Symptom:* blanks treated as one big repeat. *Response:* ask what a blank check number means for those methods.
- **A clean result called proof.** *Symptom:* "there are no duplicates". *Response:* ask what a duplicate entered under a different number would do to the test.
- **Unpaid invoices misread.** *Symptom:* negative differences reported as errors. *Response:* ask what a negative difference means.
- **SQL praised without a reason.** *Symptom:* "SQL is faster". *Response:* ask which test it would run that Excel cannot do easily.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: fields and method limit | 10 | Fields named, check numbers limited to checks | Fields without the limit |
| Requirement 2: repeats found | 25 | Both formulas, every pair and check number recorded | One test, or an incomplete list |
| Requirement 3: judgment and evidence | 25 | Each pair read as open with specific evidence to request | Conclusions without evidence |
| Requirement 4: overpayment test | 15 | Rounded test, result, and what it cannot show | Result without the limit |
| Requirements 5 and 6: limits and memo | 25 | Three misses, a reason for SQL, a half page with open or closed conclusions | Limits or memo missing |

## Extensions and discussion questions

- Add a test for the same supplier and amount on two different invoices, and compare your count with Chapter 8's.
- Find the payment dates of the check pairs and say what they have in common.
- Discuss: who should receive the list of open pairs, the payables team, the supplier or the audit committee, and in what order?
- Discuss: when does a control that prevents duplicates (a check on invoice numbers at entry) make this test unnecessary? (Chapter 12 tests the controls and the data.)
