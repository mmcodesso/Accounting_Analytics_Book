# Exercise 1.2: Tracing the Revenue Path from Order to Ledger

| | |
|---|---|
| Unit | Chapter 1: The Role of Analytics in Accounting |
| Item | Exercise 1.2 |
| Perspective | Financial accounting |
| Tools | Workbook browsing and written work |
| Time | About 50 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise makes one idea concrete: a ledger posting is the last step of a business event, and each table of the revenue path records one event. Students follow a sale from the customer's order to the cash that pays for it, and then name the columns that tie a ledger row back to its document. It sets up Chapter 3, where the same invoice is traced through every table by key. The analytics type is descriptive, and the workflow stage is identifying and accessing the data.

By the end, students can:

- name the business event that creates a row in each of the seven worksheets (chapter outcome 5);
- say which of those events post to the ledger and which do not;
- explain, in a paragraph per table, what the table records and how it leads to the next step;
- identify SourceDocumentType as the column that says what kind of document created a ledger row, and say what SourceDocumentID and SourceLineID add;
- compare what an invoice holds with what its ledger rows hold, and say why an analyst needs both.

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and ISC M4 (use and management of data); IMA Data Literacy, and Financial Recordkeeping and Financial Statement Preparation; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (i), using information technology to analyze data; AACSB A5 part 5.2.

## Before you assign

- Students need CharlesRiver.xlsx and Tutorial 1.1, especially Step 6, the filter on SourceDocumentType. Figures 1.5 and 1.6 are the reference pictures.
- The exercise does not ask students to trace the key columns that join the tables. Chapter 3 teaches that, so if a student starts joining tables, tell them that descriptions are enough here.
- It relies on these conditions: every ledger row names its source in SourceDocumentType (VoucherType repeats it); a sales order and its lines post nothing; and the sale that Figure 1.6 traces exists as drawn. The traced order was shipped and invoiced in parts, and the traced receipt paid several invoices, so the one-to-one chain that students expect does not hold.
- Rehearse the demonstration below. It takes ten minutes.

## How to run it

Individual work, or pairs, and it also works as a class demonstration. For about 50 minutes: 20 minutes browsing and naming events (requirement 1), 15 writing the paragraphs (requirement 2), 5 on the origin column (requirement 3) and 10 on the comparison (requirement 4).

**Hints.** For requirement 1, if a student describes a table instead of an event, ask who in the company did something to create the row. For requirement 3, tell them to open the filter list on GLEntry and read the types.

**A ten-minute demonstration.** Open GLEntry and filter SourceDocumentType to SalesInvoice and SourceDocumentID to 7947: four rows. Note that SourceDocumentID is the invoice's key and VoucherNumber holds its number, SI-2025-007947. Open SalesInvoice and find the row with that key, then the line in SalesInvoiceLine, then the shipment and the receipt application for the same invoice. Ask students to predict each next worksheet before you open it. This previews Tutorial 3.2, so do not explain the keys.

**Collect** the written paragraphs for requirement 2 and the sentences for requirement 4.

## Step-by-step solution

### Requirement (1): Name the event behind each row

**Step 1. Open the seven worksheets in order, and name the event.**

a. Click **SalesOrder**, **SalesOrderLine**, **Shipment**, **SalesInvoice**, **CashReceipt**, **CashReceiptApplication** and **GLEntry**, in that order.
b. For each, ask what happened in the business to create one row.
c. Note the date column that records when it happened.

A model answer, with the traced sale as the example:

| Worksheet | The event that adds a row | Date column | The traced sale |
|---|---|---|---|
| SalesOrder | A customer places an order | OrderDate | SO-2024-001697, placed 2024-11-21, for Sullivan-Mcdonald |
| SalesOrderLine | One item, quantity and price is added to the order | (the order's date) | 6 lines on the order |
| Shipment | The warehouse ships all or part of an order | ShipmentDate | SH-2025-003603 on 2025-03-02, one of 5 for the order |
| SalesInvoice | Charles River bills what was shipped | InvoiceDate | SI-2025-007947 on 2025-03-05, one of 8 for the order; total 787.48 |
| CashReceipt | A customer's payment arrives | ReceiptDate | CR-2025-003043 on 2025-04-17, 23,870.99 by check |
| CashReceiptApplication | Staff apply all or part of a receipt to an invoice | ApplicationDate | 787.48 applied to this invoice on 2025-04-17 |
| GLEntry | A document is posted to the ledger | PostingDate | Four rows for the invoice |

![The path of the traced sale through the seven worksheets, with the one-to-many links and the ledger postings.](../figures/chapter-01-role-of-analytics/IF-01-2-A.pdf)

**Check:** each answer is an event ("the warehouse ships goods"), not a description ("stores shipments"). **Watch for:** students who treat the invoice as the first event. The order comes first, and nothing in the ledger records it.

**Step 2. Mark which events post to the ledger.** Open the filter list of SourceDocumentType in GLEntry. The ledger has 20 source types. Shipment, SalesInvoice, CashReceipt and CashReceiptApplication are among them, and SalesOrder is not.

**Check:** the order and its lines post nothing, because no financial effect has happened yet. The ledger rows start with the shipment, which records cost of goods sold, and the invoice, which records revenue and receivables.

### Requirement (2): Write the narrative

**Step 3. Write a paragraph for each table: what it records, and what it leads to.** The outline below is what a strong paragraph contains.

| Table | Records | Leads to |
|---|---|---|
| SalesOrder and SalesOrderLine | The customer, the date, the status and the total, and on the lines the item, quantity and price | Shipments. An order is shipped in parts: the traced order has 5 shipments and 8 invoices |
| Shipment | Goods leaving a warehouse, with its date, status and delivery date | An invoice. It posts the cost of the goods to cost of goods sold and finished goods, and the freight to freight-out expense |
| SalesInvoice | What is billed: the customer, the dates, subtotal, freight, tax and total | The receipt. It posts receivables, revenue, freight revenue and sales tax payable |
| CashReceipt | A payment: the date, amount and method | The application. It posts cash and unapplied cash |
| CashReceiptApplication | The part of a receipt applied to an invoice | The end of the path. It moves the amount from unapplied cash to receivables. One receipt can pay several invoices: the traced receipt paid 7 |
| GLEntry | The debits and credits that each event created | Every financial statement |

Across the data, 5,209 of the 5,768 invoiced orders have more than one invoice, and 5,745 of the 7,409 receipts pay more than one invoice, so the one-to-many links are the rule.

**Check:** every paragraph names the link to the next step in words. **Watch for:** a student who draws a straight line, one order to one invoice to one receipt. Show the traced order.

### Requirement (3): Find the origin column

**Step 4. Filter GLEntry by source.**

a. Click the **GLEntry** worksheet tab.
b. Click the filter button on **SourceDocumentType** and choose SalesInvoice only.
c. Read SourceDocumentID and SourceLineID, the next two columns.
d. To see one invoice, also filter SourceDocumentID to 7947.

![A mock of the GLEntry worksheet filtered to the four rows of the traced invoice, the model answer to requirement 3.](../figures/chapter-01-role-of-analytics/IF-01-2-B.pdf)

The four rows of the traced invoice:

| GLEntryID | AccountID | Account | Debit | Credit | SourceLineID |
|---:|---:|---|---:|---:|---:|
| 126311 | 3 | 1020 Accounts Receivable | 787.48 |  |  |
| 126312 | 42 | 4010 Sales Revenue - Furniture |  | 688.42 | 10645 |
| 126313 | 46 | 4050 Freight Revenue |  | 51.00 |  |
| 126314 | 26 | 2050 Sales Tax Payable |  | 48.06 |  |

**Check:** the answer is SourceDocumentType. SourceDocumentID identifies the document and SourceLineID the line, which only the revenue row carries here. The receivables debit equals the three credits. VoucherType repeats SourceDocumentType on every row, so a student who names it is right about the data; the book's column is SourceDocumentType. **Watch for:** CreatedByEmployeeID offered as the origin. It names the employee on the row, and for the rows of a sales invoice it names the chief executive officer, not a preparer.

### Requirement (4): Compare the invoice with its ledger rows

**Step 5. List what each table holds that the other lacks.**

| SalesInvoice and its lines hold | GLEntry holds |
|---|---|
| The customer (CustomerID), the invoice and due dates, the link to the order, the status and the payment date | The account (AccountID), a debit or a credit, the cost center, the fiscal year and period |
| The split of the total into SubTotal, FreightAmount, TaxAmount and GrandTotal on one row | One row for each amount posted, so the same invoice appears in 4 rows |
| On the lines, the item, quantity, unit price and discount | Rows from every other kind of document |

**Check:** a strong paragraph says that the invoice explains a number (who owes it, for what, due when) and the ledger classifies and totals it (which account, which period). An analyst needs both to reconcile them, as in the invoice above where 787.48 is the sum of the revenue, the freight and the tax, and to answer a question that spans them, such as revenue by customer (invoice) against revenue by account and period (ledger).

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Lines, shipments and invoices of the traced order | 6, 5 and 8 | Step 1 |
| Invoices paid by the traced receipt | 7 | Step 1 |
| Source types in the ledger | 20 | Step 2 |
| Ledger rows for the traced invoice | 4 | Step 4 |
| Traced invoice: subtotal, freight, tax, total | 688.42, 51.00, 48.06, 787.48 | Steps 1 and 4 |
| Traced receipt: amount, and the part applied to the invoice | 23,870.99; 787.48 | Step 1 |
| Rows in SalesOrder, SalesOrderLine, Shipment, SalesInvoice | 5,819; 22,269; 9,707; 20,914 | Step 1 |
| Rows in CashReceipt, CashReceiptApplication, GLEntry | 7,409; 27,117; 815,921 | Steps 1 and 4 |

The traced shipment posts debit 5010 COGS - Furniture 459.32; credit 1040 Inventory - Finished Goods 459.32; debit 5050 Freight-Out Expense 47.42; credit 2040 Accrued Expenses 47.42. The receipt posts accounts 1010 and 2060, and its application posts accounts 2060 and 1020.

## What a strong answer says

- **Requirement (1).** An event for each table, with its date column, and the observation that the order and its lines come first and post nothing.
- **Requirement (2).** Each paragraph says what the table records and what it leads to, notes the parts (an order shipped and invoiced in parts, a receipt that pays several invoices), and says which events post.
- **Requirement (3).** SourceDocumentType, with its values (SalesInvoice, JournalEntry, PayrollSummary and so on), and SourceDocumentID and SourceLineID to complete the trace.
- **Requirement (4).** What only the invoice has (customer, dates, status, item detail) and what only the ledger has (account, period, cost center, other documents), and why reconciliation needs both.

A weak answer retells the headers of the worksheets, draws a one-to-one chain, or says the ledger "contains" the sales order.

## Common mistakes and how to respond

- **A one-to-one chain.** *Symptom:* "the order becomes an invoice, which becomes a payment". *Response:* show the traced order's shipments and invoices.
- **The order posts to the ledger.** *Symptom:* GLEntry rows from SalesOrder. *Response:* ask them to find SalesOrder in the SourceDocumentType filter list.
- **A receipt posting straight to receivables.** *Symptom:* "cash debit, receivables credit" for the receipt. *Cause:* the application is skipped. *Response:* show the unapplied cash account in the receipt's rows.
- **AccountID read as the account number.** *Response:* open Account and compare.
- **SourceDocumentID read as the invoice number.** *Response:* show VoucherNumber, which holds the number.
- **The origin column named as CreatedByEmployeeID or Description.** *Response:* ask which column holds the document type.
- **Skipping CashReceiptApplication.** *Symptom:* receipt linked directly to invoice. *Response:* ask how a receipt of several invoices would be recorded.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: an event for each of the seven worksheets | 25 | Seven events, with dates, as events | Descriptions of tables, or a worksheet missing |
| Requirement 2: a paragraph per table | 35 | What each table records and how it links to the next, with the posting noted | Paragraphs that do not link, or a one-to-one chain |
| Requirement 3: the origin column | 15 | SourceDocumentType, with the document ID and line columns | Another column, or the type without the explanation |
| Requirement 4: the comparison | 25 | What each holds, and why both are needed | A list with no reason |

## Extensions and discussion questions

- Choose a second invoice, and trace it in the same way. Find an order with only one shipment and one invoice, and say how it differs.
- Find a ledger row of a type other than the ones in the path, and say what event it records.
- Discuss: revenue posts when the invoice is recorded and cost when the goods ship. What could go wrong at a year-end? (Chapter 6 and Chapter 12 test this.)
- Discuss: if an invoice never reached the ledger, which of the seven worksheets would still show the sale? (Chapter 2 treats completeness.)
- Discuss: what keys would you need to follow the sale without the document numbers? (Chapter 3.)
