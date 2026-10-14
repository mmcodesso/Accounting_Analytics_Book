---
note: ch01.ex2
title: Tracing the Revenue Path from Order to Ledger
kind: exercise
number: '1.2'
unit: '1'
perspective: financial
tool: conceptual
minutes: 50
solution: ''
figures:
  - id: IF-01-2-A
    kind: diagram
    purpose: The path of the traced sale through the seven worksheets, with the one-to-many links and the ledger postings.
    shows: Left to right, boxes for SalesOrder (with its lines), Shipment, SalesInvoice, CashReceipt and CashReceiptApplication, each carrying the document number and date of the traced sale. Labels on the arrows give how many shipments and invoices the order has and how many invoices the receipt paid. Beneath them a GLEntry box receives dashed amber arrows from the shipment, the invoice, the receipt and the application, each labeled with the accounts debited and credited. The sales order and its lines have no arrow to the ledger, and a note says so.
    data: The traced sale of Figure 1.6 and its order, shipment, receipt and application, from the Expected results table of this guide.
  - id: IF-01-2-B
    kind: excel-mock
    purpose: The GLEntry worksheet filtered to the four rows of the traced invoice, the model answer to requirement 3.
    shows: The GLEntry worksheet with the SourceDocumentType filter list open and SalesInvoice ticked, and the table narrowed to the four rows of the traced invoice by that filter and a filter on SourceDocumentID. The filter list is drawn below the rows, joined to its filter button, so that it does not cover them. Columns B (PostingDate) and F (VoucherType) are hidden so that the text stays legible; the other columns from GLEntryID to SourceLineID are visible, with the receivables debit equal to the three credits. The SourceDocumentType header and the revenue row's SourceLineID cell are outlined.
    data: The four GLEntry rows of the traced invoice (the table in Step 4).
---
# Exercise 1.2: Tracing the Revenue Path from Order to Ledger

{{ header() }}

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

**A ten-minute demonstration.** Open GLEntry and filter SourceDocumentType to SalesInvoice and SourceDocumentID to {{ ids.invoice }}: four rows. Note that SourceDocumentID is the invoice's key and VoucherNumber holds its number, {{ numbers.invoice }}. Open SalesInvoice and find the row with that key, then the line in SalesInvoiceLine, then the shipment and the receipt application for the same invoice. Ask students to predict each next worksheet before you open it. This previews Tutorial 3.2, so do not explain the keys.

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
| SalesOrder | A customer places an order | OrderDate | {{ numbers.order }}, placed {{ order_date }}, for {{ numbers.customer }} |
| SalesOrderLine | One item, quantity and price is added to the order | (the order's date) | {{ order.lines }} lines on the order |
| Shipment | The warehouse ships all or part of an order | ShipmentDate | {{ numbers.shipment }} on {{ ship_date }}, one of {{ order.shipments }} for the order |
| SalesInvoice | Charles River bills what was shipped | InvoiceDate | {{ numbers.invoice }} on {{ invoice.date }}, one of {{ order.invoices }} for the order; total {{ invoice.total|money }} |
| CashReceipt | A customer's payment arrives | ReceiptDate | {{ numbers.receipt }} on {{ receipt.date }}, {{ receipt.amount|money }} by {{ receipt.method|lower }} |
| CashReceiptApplication | Staff apply all or part of a receipt to an invoice | ApplicationDate | {{ receipt.applied_here|money }} applied to this invoice on {{ receipt.applied_date }} |
| GLEntry | A document is posted to the ledger | PostingDate | Four rows for the invoice |

{{ figure('IF-01-2-A') }}

**Check:** each answer is an event ("the warehouse ships goods"), not a description ("stores shipments"). **Watch for:** students who treat the invoice as the first event. The order comes first, and nothing in the ledger records it.

**Step 2. Mark which events post to the ledger.** Open the filter list of SourceDocumentType in GLEntry. The ledger has {{ n_source_types }} source types. Shipment, SalesInvoice, CashReceipt and CashReceiptApplication are among them, and SalesOrder is not.

**Check:** the order and its lines post nothing, because no financial effect has happened yet. The ledger rows start with the shipment, which records cost of goods sold, and the invoice, which records revenue and receivables.

### Requirement (2): Write the narrative

**Step 3. Write a paragraph for each table: what it records, and what it leads to.** The outline below is what a strong paragraph contains.

| Table | Records | Leads to |
|---|---|---|
| SalesOrder and SalesOrderLine | The customer, the date, the status and the total, and on the lines the item, quantity and price | Shipments. An order is shipped in parts: the traced order has {{ order.shipments }} shipments and {{ order.invoices }} invoices |
| Shipment | Goods leaving a warehouse, with its date, status and delivery date | An invoice. It posts the cost of the goods to cost of goods sold and finished goods, and the freight to freight-out expense |
| SalesInvoice | What is billed: the customer, the dates, subtotal, freight, tax and total | The receipt. It posts receivables, revenue, freight revenue and sales tax payable |
| CashReceipt | A payment: the date, amount and method | The application. It posts cash and unapplied cash |
| CashReceiptApplication | The part of a receipt applied to an invoice | The end of the path. It moves the amount from unapplied cash to receivables. One receipt can pay several invoices: the traced receipt paid {{ receipt.applications }} |
| GLEntry | The debits and credits that each event created | Every financial statement |

Across the data, {{ multi_orders|count }} of the {{ orders|count }} invoiced orders have more than one invoice, and {{ multi_receipts|count }} of the {{ receipts|count }} receipts pay more than one invoice, so the one-to-many links are the rule.

**Check:** every paragraph names the link to the next step in words. **Watch for:** a student who draws a straight line, one order to one invoice to one receipt. Show the traced order.

### Requirement (3): Find the origin column

**Step 4. Filter GLEntry by source.**

a. Click the **GLEntry** worksheet tab.
b. Click the filter button on **SourceDocumentType** and choose SalesInvoice only.
c. Read SourceDocumentID and SourceLineID, the next two columns.
d. To see one invoice, also filter SourceDocumentID to {{ ids.invoice }}.

{{ figure('IF-01-2-B') }}

The four rows of the traced invoice:

| GLEntryID | AccountID | Account | Debit | Credit | SourceLineID |
|---:|---:|---|---:|---:|---:|
{% for r in gl %}
| {{ r.id }} | {{ r.account_id }} | {{ r.number }} {{ r.name }} | {{ r.debit|money if r.debit else '' }} | {{ r.credit|money if r.credit else '' }} | {{ r.line if r.line else '' }} |
{% endfor %}

**Check:** the answer is SourceDocumentType. SourceDocumentID identifies the document and SourceLineID the line, which only the revenue row carries here. The receivables debit equals the three credits. VoucherType repeats SourceDocumentType on every row, so a student who names it is right about the data; the book's column is SourceDocumentType. **Watch for:** CreatedByEmployeeID offered as the origin. It names the employee on the row, and for the rows of a sales invoice it names the {{ creator }}, not a preparer.

### Requirement (4): Compare the invoice with its ledger rows

**Step 5. List what each table holds that the other lacks.**

| SalesInvoice and its lines hold | GLEntry holds |
|---|---|
| The customer (CustomerID), the invoice and due dates, the link to the order, the status and the payment date | The account (AccountID), a debit or a credit, the cost center, the fiscal year and period |
| The split of the total into SubTotal, FreightAmount, TaxAmount and GrandTotal on one row | One row for each amount posted, so the same invoice appears in {{ gl|length }} rows |
| On the lines, the item, quantity, unit price and discount | Rows from every other kind of document |

**Check:** a strong paragraph says that the invoice explains a number (who owes it, for what, due when) and the ledger classifies and totals it (which account, which period). An analyst needs both to reconcile them, as in the invoice above where {{ invoice.total|money }} is the sum of the revenue, the freight and the tax, and to answer a question that spans them, such as revenue by customer (invoice) against revenue by account and period (ledger).

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Lines, shipments and invoices of the traced order | {{ order.lines }}, {{ order.shipments }} and {{ order.invoices }} | Step 1 |
| Invoices paid by the traced receipt | {{ receipt.applications }} | Step 1 |
| Source types in the ledger | {{ n_source_types }} | Step 2 |
| Ledger rows for the traced invoice | {{ gl|length }} | Step 4 |
| Traced invoice: subtotal, freight, tax, total | {{ invoice.subtotal|money }}, {{ invoice.freight|money }}, {{ invoice.tax|money }}, {{ invoice.total|money }} | Steps 1 and 4 |
| Traced receipt: amount, and the part applied to the invoice | {{ receipt.amount|money }}; {{ receipt.applied_here|money }} | Step 1 |
| Rows in SalesOrder, SalesOrderLine, Shipment, SalesInvoice | {{ rows.SalesOrder|count }}; {{ rows.SalesOrderLine|count }}; {{ rows.Shipment|count }}; {{ rows.SalesInvoice|count }} | Step 1 |
| Rows in CashReceipt, CashReceiptApplication, GLEntry | {{ rows.CashReceipt|count }}; {{ rows.CashReceiptApplication|count }}; {{ rows.GLEntry|count }} | Steps 1 and 4 |

The traced shipment posts {% for r in ship_gl %}{{ 'debit' if r.debit else 'credit' }} {{ r.number }} {{ r.name }} {{ (r.debit or r.credit)|money }}{{ '; ' if not loop.last else '.' }}{% endfor %} The receipt posts accounts {% for r in gl_receipt %}{{ r.number }}{{ ' and ' if not loop.last else '' }}{% endfor %}, and its application posts accounts {% for r in gl_app %}{{ r.number }}{{ ' and ' if not loop.last else '' }}{% endfor %}.

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
