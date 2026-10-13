---
note: ch01.ex5
uses: [ch08.ex1, ch02.ex6]
title: Assessing Data Availability for Audit Testing
kind: exercise
number: '1.5'
unit: '1'
perspective: auditing
tool: conceptual
minutes: 70
solution: ''
figures: []
---
# Exercise 1.5: Assessing Data Availability for Audit Testing

{{ header() }}

## Purpose and learning outcomes

The exercise asks a planning question before any test is run: for three common audit tests, does the data exist, in which tables, and in which columns? An auditor who can answer that can write a data request, scope a procedure and say what a test cannot show. It also gives students the first use of the source columns of GLEntry, to separate postings made by documents from journal entries. The three tests are descriptive procedures (a stratification, a search for repeats, and a screen of entries), and the exercise is practice in judging whether the data can support them (chapter outcome 6).

By the end, students can:

- name the table group, the tables and the columns that support an aging of receivables, a duplicate payment test and a journal entry test (chapter outcome 4);
- use SourceDocumentType to separate journal entries from postings that documents generate (chapter outcome 5);
- identify a test that needs the Order-to-Cash group and the Accounting Core together, and say why neither is enough;
- document the data for each test in a one-page planning memo.

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics) and ISC M4 (use and management of data); IMA Data Literacy and Internal Control; IFAC IES 2 (f), audit, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.2.

## Before you assign

- Students need CharlesRiver.xlsx and Tutorial 1.1 (the filter on SourceDocumentType). Table 1.3 lists the groups.
- The requirement (1) text is long. Read it aloud once, since it carries hints about dates and the control account that students skip.
- The exercise relies on these conditions: SalesInvoice, CashReceiptApplication and CreditMemo hold what is needed to age receivables; DisbursementPayment and PurchaseInvoice hold what is needed for duplicate payments; JournalEntry has its lines in GLEntry, under the source type JournalEntry; and Employee holds the approval limits. Part of the data is imperfect, as the chapters on audit show, but the exercise only asks whether the data is there.
- Nobody is asked to calculate an aging. If a student starts calculating, tell them the plan is the product.

## How to run it

Individual work, followed by a ten-minute comparison in pairs. For about 70 minutes: 30 minutes browsing and planning the three tests (requirement 1), 10 on the source column (requirement 2), 10 on the cross-group test (requirement 3) and 20 for the memo (requirement 4).

**Hints.** After 15 minutes on the aging, if a student has no date columns, ask what has to be true of a receipt before it counts at the reporting date. Hold back the Employee worksheet for the journal entry test until a student asks where approval limits are kept.

**Collect** the memo.

## Step-by-step solution

### Requirement (1): Name the tables and columns for each test

**Step 1. Plan the aging of receivables.**

a. Open **SalesInvoice**, **Customer**, **CashReceipt**, **CashReceiptApplication**, **CreditMemo** and **GLEntry**.
b. For what was billed and to whom, note SalesInvoice (InvoiceNumber, InvoiceDate, DueDate, CustomerID, GrandTotal) and Customer (CustomerName, CreditLimit, PaymentTerms).
c. For what reduced each invoice, note CashReceiptApplication (SalesInvoiceID, ApplicationDate, AppliedAmount) and CreditMemo (OriginalSalesInvoiceID, CreditMemoDate, GrandTotal). CashReceipt (ReceiptDate, Amount) records the receipt itself.
d. For the dates, the reporting date is compared with InvoiceDate (billed by then), ApplicationDate and CreditMemoDate (applied or credited by then) and DueDate (for the age).
e. For the check, use GLEntry (PostingDate, AccountID, Debit, Credit) and Account to read the receivables account.

**Check:** the plan names the applications and the credit memos, and the date columns that decide what counts. **Watch for:** two traps.

- *Status and PaymentDate.* SalesInvoice has Status ({{ statuses }}) and PaymentDate. They describe each invoice at the end of the data. At the last date, {{ asof }}, the invoices that are Submitted or Partially Settled are exactly the {{ open_n|count }} that have an open balance, but for an earlier reporting date the columns would age the wrong invoices.
- *CashReceipt.SalesInvoiceID.* It is filled for {{ direct|count }} of the {{ receipts|count }} receipts, the ones that pay a single invoice. The other receipts pay several invoices, and only the applications record that.

**Step 2. Plan the duplicate payment test.**

a. Open **DisbursementPayment**, **PurchaseInvoice** and **Supplier** (the Procure-to-Pay group).
b. Note DisbursementPayment (PaymentNumber, PaymentDate, SupplierID, PurchaseInvoiceID, Amount, PaymentMethod, CheckNumber) and PurchaseInvoice (InvoiceNumber, InvoiceDate, SupplierID, GrandTotal).
c. List the repeat patterns the columns allow: the same supplier and invoice number on two invoices; one invoice with two payments; the same supplier and amount within a few days; a check number used twice for one supplier; a payment above the invoice total.

**Check:** at least three patterns, each with its columns. The data has {{ payments|count }} payments against {{ purchase_invoices|count }} supplier invoices, so the test needs a population method, not a visual scan. Exercise 2.6 finds {{ ch02_ex6.invoice_numbers }} supplier invoice numbers that appear twice for one supplier and {{ ch02_ex6.checks }} check numbers that repeat, a result that students meet in Chapter 2.

**Step 3. Plan the journal entry test.**

a. Open **JournalEntry** and **GLEntry**, and **Employee** (Master Data).
b. Note JournalEntry (EntryNumber, PostingDate, EntryType, Description, TotalAmount, CreatedByEmployeeID, CreatedDate, ApprovedByEmployeeID, ApprovedDate, ReversesJournalEntryID).
c. The entry's lines are in GLEntry, the rows whose SourceDocumentType is JournalEntry and whose SourceDocumentID is the entry's key. Employee (JobTitle, MaxApprovalAmount) gives the approver's role and limit.

**Check:** the plan finds the lines in GLEntry, not in a separate line worksheet. Exercise 1.6 goes into the columns.

### Requirement (2): Explain what SourceDocumentType shows

**Step 4. Filter GLEntry on SourceDocumentType and read the list.** The ledger has {{ n_source_types }} source types. Rows whose type is JournalEntry are {{ je_rows|count }} of {{ gl_rows|count }}, and they tie to {{ entries|count }} journal entries. Every other type names a document that the system posts when a business event happens (an invoice, a shipment, a payment, a payroll run).

A model answer: SourceDocumentType says what kind of document created the row. Rows of type JournalEntry are entries that people key and approve. Rows of every other type are generated from a document. The auditor can therefore test journal entries as a population of their own and treat the others as the ledger side of the cycles that have their own controls.

**Check:** the answer names the JournalEntry value and says that the other values are system postings. **Watch for:** two points. A journal entry is not necessarily unusual: the type JournalEntry includes routine rent, depreciation and accrual entries, so the filter finds the entries made by people, not the entries to worry about. And CreatedByEmployeeID is no help in telling the two apart, because for every sales invoice row it names the {{ creator }}, not a preparer.

### Requirement (3): Name a test that needs two groups

**Step 5. Choose the test and say why one group is not enough.** Accept the aging checked against the receivables account, or a revenue cutoff test (invoice and shipment dates against the ledger's posting dates), or any test that compares a document with its posting.

For the aging, a model reason: the invoice detail shows who owes what and how old it is, and the ledger shows the balance recorded in the books. Only together can the auditor see whether the detail supports the balance. In this dataset, the open invoices at {{ asof }} number {{ ch08_ex1.n|count }} and total {{ ch08_ex1.total|money }}, and the ledger balance of the receivables account is {{ ar_ledger|money }}. The difference of {{ ch08_ex1.opening|money }} is the opening balance line of {{ ch08_ex1.entry }}. Students are not expected to find this, but it shows that the ledger check is worth planning. Exercise 8.1 builds the aging.

**Check:** the answer gives a reason that is about the comparison, not about convenience.

### Requirement (4): Write the planning memo

**Step 6. Outline a one-page memo.** A strong memo has: a header and the purpose; a table with one row for each test (the tables and group, the columns, the date or key logic, and a limitation); the cross-group test with its reason; and a closing line on what is needed that the tables do not hold, such as a policy threshold for journal entries or a cutoff date.

**Check:** the memo fits a page, and its table is specific enough that someone else could write the data request from it.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Open invoices at {{ asof }} | {{ ch08_ex1.n|count }} | Step 5 |
| Open balance of those invoices | {{ ch08_ex1.total|money }} | Step 5 |
| Ledger balance of the receivables account at {{ asof }} | {{ ar_ledger|money }} | Step 5 |
| Difference, the opening balance line of {{ ch08_ex1.entry }} | {{ ch08_ex1.opening|money }} | Step 5 |
| Receipts; those with a SalesInvoiceID | {{ receipts|count }}; {{ direct|count }} | Step 1 |
| Payments; supplier invoices | {{ payments|count }}; {{ purchase_invoices|count }} | Step 2 |
| Source types in GLEntry | {{ n_source_types }} | Step 4 |
| Ledger rows of type JournalEntry; journal entries | {{ je_rows|count }}; {{ entries|count }} | Step 4 |

## What a strong answer says

- **Requirement (1).** For each test, tables with columns, the dates that decide what counts, and a note on what the table cannot do (Status for a past date, a receipt that pays several invoices).
- **Requirement (2).** SourceDocumentType, the JournalEntry value against the others, and a caveat that JournalEntry is not the same as unusual.
- **Requirement (3).** A test with tables from both groups and a reason about the comparison.
- **Requirement (4).** A planning memo specific enough to be a data request.

A weak answer names groups without tables, or tables without columns, or plans an aging from SalesInvoice alone.

## Common mistakes and how to respond

- **Aging from Status or PaymentDate.** *Symptom:* "filter the open invoices". *Response:* ask what the status would have been on the reporting date.
- **No applications or credit memos.** *Symptom:* receipts matched to invoices by CashReceipt alone. *Response:* ask how a receipt that pays several invoices is recorded.
- **No date logic.** *Symptom:* columns named but no reporting date. *Response:* ask which rows count on the date.
- **The ledger check missing.** *Symptom:* no GLEntry in the aging plan. *Response:* ask how the auditor knows the invoices explain the balance.
- **Duplicates by amount alone.** *Symptom:* "same amount means duplicate". *Response:* ask what else would be the same, and what could differ.
- **Journal entries from JournalEntry only.** *Symptom:* no GLEntry. *Response:* ask where the debits and credits are.
- **JournalEntry read as manual and wrong.** *Response:* ask which entries are routine.
- **A memo as a list of table names.** *Response:* ask what a colleague would need to pull the data.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: three tests with tables, columns and dates | 35 | Tables, columns and date logic for all three, with the traps noted | One test missing, or no date logic |
| Requirement 2: SourceDocumentType | 20 | The JournalEntry value against the others, with the caveat | The column without the explanation |
| Requirement 3: a cross-group test | 20 | Tables from both groups and a reason about the comparison | One group, or no reason |
| Requirement 4: the planning memo | 25 | One page, specific, with limits and gaps | A list with no limits |

## Extensions and discussion questions

- Plan a fourth test, such as a payroll test, and name its group and tables.
- Write the data request for the journal entry test as a list of fields, and say which are in the workbook.
- Discuss: why is a test of every journal entry still not proof that none is missing? (Chapter 2 treats completeness, and Chapter 12 tests it.)
- Discuss: which of the three plans would you start first, and why? (Chapter 8 builds all three in Excel.)
