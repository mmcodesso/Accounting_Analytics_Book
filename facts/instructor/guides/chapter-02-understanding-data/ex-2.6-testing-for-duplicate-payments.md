---
note: ch02.ex6
uses: [ch02.ex6g, ch08.ex5]
title: Testing for Duplicate Payments
kind: exercise
number: '2.6'
unit: '2'
perspective: auditing
tool: conceptual
minutes: 75
solution: ''
figures:
  - id: IF-02-6-A
    kind: excel-mock
    purpose: The PurchaseInvoice worksheet with the Count helper column of Step 2, filtered to the repeated invoice numbers.
    shows: The PurchaseInvoice Table with PurchaseInvoiceID, InvoiceNumber, InvoiceDate, SupplierID and GrandTotal visible (other columns hidden) and a helper column headed Count at the right, filtered for a Count above 1, which leaves only the value 2, and sorted by SupplierID and InvoiceNumber as Step 2 asks. The remaining rows come in adjacent pairs that share a supplier and an invoice number but differ in date and amount, and the row numbers are blue because the Table is filtered. The formula bar shows the COUNTIFS formula and the status bar shows how many records match the filter.
    data: PurchaseInvoice, with the COUNTIFS formula of Step 2 on SupplierID and InvoiceNumber.
---
# Exercise 2.6: Testing for Duplicate Payments

{{ header() }}

## Purpose and learning outcomes

Duplicate payments are a classic audit risk, and a first test in Excel is easy to write and easy to over-read. The exercise asks for three tests (a repeated invoice number, a repeated check number, an invoice paid above its total), a judgment about each match, and an honest statement of what the tests cannot find. Its lesson is that a match is a question for the supplier and the payables team, not a finding, and that a clean result is limited by what the test looks at. It is the first exercise to point past the chapter's tools toward SQL. The tests are descriptive procedures.

By the end, students can:

- count repeats with COUNTIFS on a pair of columns and read the result (outcome 4);
- judge a pair of records and name the evidence that would settle it (outcome 5);
- explain what a test that finds nothing does and does not prove (outcome 6);
- write a short memo that states the matches, the conclusions and the limits.

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance) and Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Analysis and Internal Control; IFAC IES 2 (f), audit, and IES 4 (a), professional skepticism and judgment; AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx. PurchaseInvoice has {{ ch02_ex6g.invoices|count }} rows and DisbursementPayment {{ ch02_ex6g.payments|count }}, so a COUNTIFS over whole columns recalculates slowly. Tell students to wait. A student who switches calculation to manual must press F9 before filtering or recording a result, switch back to automatic, and check the first and last formulas.
- The exercise relies on these conditions: a few supplier invoice numbers appear twice for the same supplier, a few check numbers appear twice for the same supplier, a payment carries a check number only when its method is Check, and no invoice is paid above its GrandTotal once both sides are rounded to the cent.
- The generator's own log of planted anomalies lists more repeated payment references than the data holds. Do not quote that count to students: the data holds {{ checks }} repeated check numbers, and the note under Expected results says so.
- Requirement (4) asks for rounding to the cent. Students who skip it get false matches.

## How to run it

Individual work, then a pair discussion of requirement (3). For about 75 minutes: 10 on requirement 1, 20 on requirement 2, 15 on requirement 3, 15 on requirement 4, 5 on requirement 5 and 10 on the memo.

**Hints.** If a student reports hundreds of overpaid invoices, ask how the amounts were rounded. If a student concludes that a pair is a duplicate, ask what else would be the same if it were. Hold back the SQL discussion until requirement (5). **Collect** the memo and the helper columns.

## Step-by-step solution

### Requirement (1): Identify the fields

**Step 1. Read the two worksheets and name the fields.** On **PurchaseInvoice**, note SupplierID, InvoiceNumber, InvoiceDate, GrandTotal and PurchaseOrderID. On **DisbursementPayment**, note SupplierID, PurchaseInvoiceID, Amount, PaymentDate, PaymentMethod and CheckNumber.

**Check:** the fields support three tests: a repeated supplier and invoice number, a repeated supplier and check number, and an invoice whose payments exceed its total. A PivotTable of PaymentMethod shows which payments have a check number, and only payments by check carry one, so {{ ch02_ex6g.no_check|count }} payments cannot be tested that way:

| PaymentMethod | Payments | With a check number |
|---|---:|---:|
{% for m in ch02_ex6g.methods %}
| {{ m[0] }} | {{ m[1]|count }} | {{ m[2]|count }} |
{% endfor %}

### Requirement (2): Count the repeats

**Step 2. Count each invoice number for its supplier.**

a. On **PurchaseInvoice**, in the first free column, enter this formula and copy it down:

   ```
   =COUNTIFS(G:G,G2,B:B,B2)
   ```

b. Filter the column for values above 1, and sort by SupplierID and InvoiceNumber.

{{ figure('IF-02-6-A') }}

**Check:** {{ invoice_numbers }} invoice numbers appear twice, for suppliers {{ suppliers }}, one pair each in every fiscal year.

| Invoice number | Supplier | First invoice (ID, date, amount) | Second invoice (ID, date, amount) |
|---|---:|---|---|
{% for p in ch02_ex6g.pairs %}
| {{ p.number }} | {{ p.supplier }} | {{ p.first[0] }}, {{ p.first[1] }}, ${{ p.first[2]|money }} | {{ p.second[0] }}, {{ p.second[1] }}, ${{ p.second[2]|money }} |
{% endfor %}

**Step 3. Count each check number for its supplier.**

a. On **DisbursementPayment**, in the first free column, enter and copy down:

   ```
   =IF(H2="","",COUNTIFS(D:D,D2,H:H,H2))
   ```

b. Filter the column for values above 1.

**Check:** {{ checks }} check numbers repeat, both for supplier {{ check_suppliers }}, each on two payments. Payments by ACH or wire show a blank and are left out. **Watch for:** a COUNTIFS on the check number alone. It answers a different question, a check number used for two suppliers, which is not harmless either (a check register should not repeat a number from one bank account), but these columns do not say which account issued a check, so the requested test is within a supplier. No check number is shared by two suppliers here.

### Requirement (3): Judge each pair

**Step 4. Compare the two records of each pair.** For the invoice pairs, compare the dates, the amounts and the purchase orders, and look up the payments of each invoice. For the check pairs, compare the payment dates, the invoices paid and the amounts.

**Check, invoice pairs:** the dates differ in {{ dated_apart }} of the {{ invoice_numbers }} pairs, every pair has different amounts, the two invoices of a pair are on different purchase orders, and each invoice was paid once. That is consistent with a reused number on two different transactions. It does not rule out one obligation entered twice with a changed date or amount, so the pairs stay open until the original invoices, the purchase orders and receipts, or the supplier's statement settle them.

**Check, check pairs:**

| Check number | Payment | Date | Invoice paid | Amount | Invoice total |
|---|---|---|---|---:|---:|
{% for c in ch02_ex6g.check_rows %}
{% for p in c.payments %}
| {{ c.check }} | {{ p.number }} | {{ p.date }} | {{ p.invoice }} | ${{ p.amount|money }} | ${{ p.total|money }} |
{% endfor %}
{% endfor %}

Each pair pays two different invoices of different amounts on the same day, which is consistent with one check number reused on two payments, or with one check that paid both invoices and was recorded as two payments, rather than one payment made twice, but does not settle it. Compare each pair's combined amount with the cleared check. The pairs stay open until the bank's record of the checks that cleared and the payables team's check register, with any void and reissue, settle them.

### Requirement (4): Test each invoice for overpayment

**Step 5. Compare each invoice's payments with its total.**

a. On **PurchaseInvoice**, in the next free column, total the payments of the invoice and subtract its total, both rounded to the cent:

   ```
   =ROUND(SUMIFS(DisbursementPayment!F:F,DisbursementPayment!E:E,A2),2)-ROUND(J2,2)
   ```

b. Copy it down and filter the column for values above 0.

**Check:** no invoice is paid above its total ({{ ch02_ex6g.rounded }} flagged). Of the {{ ch02_ex6g.invoices|count }} invoices, {{ ch02_ex6g.full|count }} are paid in full, {{ ch02_ex6g.less|count }} in part, and {{ ch02_ex6g.unpaid|count }} not at all, and {{ installments|count }} were paid in installments, which is normal. **Watch for:** two traps. Without the rounding, a comparison flags {{ ch02_ex6g.raw|count }} invoices that are paid exactly, because a sum of many amounts differs from the total by a fraction of a cent (that count is from a SQL comparison; the point is why the book asks for ROUND). And unpaid invoices show a negative difference, which is not an error.

A model answer on what a clean result shows: recorded payments never exceed an invoice. It does not show that the invoices are valid, or that two invoice IDs are two obligations: an invoice entered twice would be paid twice, each within its own total.

### Requirement (5): Judge the approach

**Step 6. Name what the tests would miss.** A model list: the same invoice entered with a slightly different number; a repeat paid with a different amount; a payment by ACH or wire, which the check-number test cannot see (the overpayment test includes every method); and the same supplier and amount on two different invoices. Chapter 8 tests that last pattern on the payments dated through {{ d.C }} and finds {{ ch08_ex5.pairs }} supplier-and-amount pairs on different dates, {{ ch08_ex5.within30 }} within 30 days, none paying the same invoice (the whole extract, with the payments of early {{ d.N }}, holds a few more).

**Check:** the answer gives at least three misses and a reason SQL helps: it can group by several columns, join a table to itself and test near matches in one query over the whole table, without a helper column on tens of thousands of rows, and the query can be saved and rerun. SQL helps with repeatability and scale, but it does not supply evidence the records lack.

### Requirement (6): Write the memo

**Step 7. Outline half a page.** A strong memo lists the pairs found and the check numbers (in the attached schedule that requirement (6) allows), the conclusion for each, the overpayment result with its meaning, and the limits, ending with the evidence it would request.

**Check:** it states each conclusion as open or closed and names the evidence that would settle it.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Invoice numbers that appear twice for one supplier | {{ pairs }} | Step 2 |
| Repeated check numbers; supplier | {{ n_checks }}; {{ check_suppliers }} | Step 3 |
| Payments with no check number | {{ ch02_ex6g.no_check|count }} | Step 1 |
| Invoices paid above their total, after rounding | {{ ch02_ex6g.rounded }} | Step 5 |
| Invoices paid in installments | {{ installments|count }} | Step 5 |
| Supplier-and-amount pairs on different dates, payments through {{ d.C }}; within 30 days | {{ ch08_ex5.pairs }}; {{ ch08_ex5.within30 }} | Step 6 |

{{ expected() }}

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
- **Check numbers tested alone.** *Symptom:* a COUNTIFS on CheckNumber only. *Response:* ask which question the exercise asks, and what a repeat across suppliers would need (the account that issued the check).
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
