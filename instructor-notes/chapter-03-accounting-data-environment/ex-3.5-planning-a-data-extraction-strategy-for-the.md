# Exercise 3.5: Planning a Data Extraction Strategy for the Charles River Audit

| | |
|---|---|
| Unit | Chapter 3: The Accounting Data Environment |
| Item | Exercise 3.5 |
| Perspective | Auditing |
| Tools | Workbook browsing and written work |
| Time | About 90 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The first technical decision in an audit that uses data is what to extract. This exercise asks for three plans that need different structures. Revenue completeness is a question about the direction of a test: starting from invoices cannot show that a sale was never invoiced. The purchasing match joins three line tables on one key and has a gap in the middle. The journal entry analysis needs a table that holds the entry and another that holds its lines, with no key between them. Students plan from the diagrams and the worksheets, and they are not asked to run the tests. The analytics type is descriptive, and the workflow stage is identifying and accessing the data.

By the end, students can:

- choose the table group, the tables and the population for a procedure (chapter outcome 5);
- name the keys that connect them, and the direction in which a completeness test must run (outcomes 2 and 4);
- explain how a journal entry reaches its ledger rows when GLEntry has no JournalEntryID (outcome 6);
- say which columns sit in which table, and so which table each filter must read;
- write a one-to-two page extraction plan with controls.

**Competencies practiced.** CPA Evolution ISC M4 (use and management of data) and Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Governance and Data Literacy; IFAC IES 2 (f), audit, and IES 3 (a), evaluating data and information from several sources; AACSB A5 part 5.2.

## Before you assign

- Students need Figures 3.7 and 3.9 and the workbook, and they should have done Exercise 1.6, whose columns of JournalEntry and GLEntry the plan reuses, and Exercise 3.1, whose trace of a purchase shows the three documents.
- The exercise relies on these conditions. Every sales invoice has ledger rows, and every ledger row of that type names an invoice. A handful of shipment lines were never invoiced. The billable hours of the service time entries equal the hours billed. The goods receipt line carries no unit cost of its own. Some purchase order lines are received or billed in parts, and some invoice lines have no order line. GLEntry has no JournalEntryID, and a journal entry's ledger rows carry its EntryNumber as VoucherNumber.
- This is the hardest exercise of the chapter, because it asks for design. Give students the three procedures in advance, and run a ten-minute brainstorm on the direction of a completeness test before they start.

## How to run it

Individual work, followed by a pair swap in which each student critiques a classmate's plan. For about 90 minutes: 20 on revenue (requirement 1), 20 on purchasing (requirement 2), 20 on journal entries (requirement 3) and 30 on the written plan (requirement 4).

**Hints.** For requirement (1), ask what a sale that was never invoiced would look like in SalesInvoice. For requirement (2), ask which column of GoodsReceiptLine holds a price. For requirement (3), ask which table holds the lines of an entry. **Collect** the plan.

## Step-by-step solution

### Requirement (1): Revenue completeness

**Step 1. Choose the population and the joins.** The group is Order-to-Cash, with Customer and Item. The population of recorded revenue is SalesInvoice (20,914 invoices) and SalesInvoiceLine (27,933 lines). The keys: SalesInvoiceLine.SalesInvoiceID to SalesInvoice, SalesInvoice.CustomerID to Customer, and SalesInvoiceLine.ItemID to Item. The amount is LineTotal on the line, or SubTotal on the invoice.

**Check:** the plan names the three keys and the amount, and says that a valid customer and a valid item are tests of the keys (orphan tests, as in Exercise 3.6).

**Step 2. Test that each invoice reached the ledger.** Filter GLEntry for SourceDocumentType SalesInvoice and join its SourceDocumentID to SalesInvoice.SalesInvoiceID. The model result: 0 invoices have no ledger rows, and no ledger row of the type names a missing invoice. The control total is the invoice's SubTotal against the revenue credits of its rows.

**Check:** the type and the key are used together. **Watch for:** SourceDocumentID without the type.

**Step 3. Explain why that test is not enough, and name an independent population.** The posting test starts from invoices that exist. A sale that was never invoiced has no row in SalesInvoice, so no test that starts there can find it. Completeness needs a population of events from outside the invoices.

- *Goods.* Shipment and ShipmentLine: join ShipmentLine to SalesInvoiceLine on ShipmentLineID and keep the shipment lines with no match. The model result is 9 of 27,503 shipment lines, all shipped in the last month of shipments (the last shipment is dated 2026-12-31):

| Shipment | Shipped | Standard cost |
|---|---|---:|
| SH-2026-009455 | 2026-12-01 | $57.76 |
| SH-2026-009461 | 2026-12-01 | $1,678.56 |
| SH-2026-009486 | 2026-12-03 | $680.70 |
| SH-2026-009584 | 2026-12-09 | $6,748.80 |
| SH-2026-009650 | 2026-12-21 | $1,104.68 |
| SH-2026-009660 | 2026-12-23 | $3,606.78 |
| SH-2026-009667 | 2026-12-25 | $5,307.93 |
| SH-2026-009689 | 2026-12-31 | $2,790.04 |
| SH-2026-009703 | 2026-12-31 | $920.53 |

- *Design services.* The invoice lines with no shipment line are the 439 service billing lines. The independent population is ServiceTimeEntry: its billable hours (19,627.49) equal the hours billed on ServiceBillingLine.
- *Orders.* SalesOrder is a third population, a commitment that should end in an invoice.

> **[Figure placeholder IF-03-5-A]** The three extraction plans on one page, each with its population, the tables joined, the keys and the direction of the test.
> Kind: diagram · Shows: Three horizontal lanes, one for each procedure. The revenue lane starts at the Shipment and ShipmentLine boxes (the independent population), with an arrow to SalesInvoiceLine labeled ShipmentLineID and a second arrow from SalesInvoice to GLEntry labeled SourceDocumentType and SourceDocumentID, so the two directions of the test are visible and labeled completeness and posting. The purchasing lane shows PurchaseOrderLine in the center with GoodsReceiptLine and PurchaseInvoiceLine each joined to it by POLineID, and the invoice line also joined to the receipt line by GoodsReceiptLineID. The journal entry lane shows JournalEntry and GLEntry joined by the dashed amber trace, with Employee joined to JournalEntry by the approver's key. Each lane ends in a small box for its control total. · Data: The tables and keys of Steps 1 to 7; the diagram carries no counts. · Status: planned

**Check:** the answer reverses the direction (from events to invoices) and names a table of events. **Watch for:** the plan that tests completeness by counting invoices.

### Requirement (2): The three-way match

**Step 4. Choose the tables and the keys.** The group is Procure-to-Pay, with Supplier and Item. The line tables carry the keys: GoodsReceiptLine.POLineID and PurchaseInvoiceLine.POLineID both point to PurchaseOrderLine.POLineID, and PurchaseInvoiceLine.GoodsReceiptLineID points to GoodsReceiptLine. The headers repeat PurchaseOrderID. The quantities to compare are PurchaseOrderLine.Quantity, GoodsReceiptLine.QuantityReceived and PurchaseInvoiceLine.Quantity, and the prices are PurchaseOrderLine.UnitCost and PurchaseInvoiceLine.UnitCost.

**Check:** the match is made at the line level. Joining the headers on PurchaseOrderID alone multiplies the rows, as the chapter's Watch out warns.

**Step 5. Name the gaps.**

- GoodsReceiptLine has no unit cost. It has ExtendedStandardCost, which equals the quantity received times the order line's UnitCost, so the receipt carries the order's price and cannot confirm the invoice's.
- The match is not one to one. 4,655 order lines are received in parts, 9,477 receipt lines are billed on more than one invoice line, and 277 of 24,842 order lines were never received, so quantities have to be summed for each order line before they are compared.
- 355 invoice lines have no order line and no receipt line. They are tied to an accrual journal entry instead, so a three-way match cannot test them.
- 39,928 invoice lines are billed at a unit cost that differs from the order's, so the price comparison needs a tolerance and a reading of the variance.

**Check:** the plan names the key at each link, says the comparison is at the order line with sums, and lists at least one gap beyond the missing price.

### Requirement (3): The journal entry analysis

**Step 6. Choose the tables and the link.** The group is the Accounting Core, with Employee from Master Data. JournalEntry has one row for each entry (851 entries, 11 columns). The lines are the 2,821 GLEntry rows whose SourceDocumentType is JournalEntry, out of 815,921 rows. The link is the trace: GLEntry.SourceDocumentID is the JournalEntryID when the type is JournalEntry. The ledger rows also carry the entry's EntryNumber as VoucherNumber and its PostingDate, and the entry's TotalAmount equals their debits.

**Check:** the answer says that GLEntry has no JournalEntryID, names the pair of columns, and notes that the key alone is ambiguous. **Watch for:** a join on SourceDocumentID without the type.

**Step 7. Sort the columns by the table that holds them.** From Exercise 1.6:

| Question | Columns in JournalEntry | Columns in GLEntry or Employee |
|---|---|---|
| Who | CreatedByEmployeeID, ApprovedByEmployeeID | Employee: JobTitle and MaxApprovalAmount of the approver |
| When | CreatedDate, PostingDate, ApprovedDate | PostingDate, CreatedDate (repeating the entry's) |
| How much | TotalAmount | Debit and Credit of each line |
| What | EntryType, Description | AccountID, CostCenterID and the line's Description |

**Check:** the entry-level filters (who, when, how much in total, what kind) read JournalEntry, and the line-level ones (which account, which cost center) read GLEntry. A filter on the approver's limit needs Employee. **Watch for:** GLEntry's own CreatedByEmployeeID and CreatedDate used as the preparer's. For these rows they repeat the entry's, but for other types they are system values.

### Requirement (4): Write the plan

**Step 8. Write one to two pages.** A model plan has a table for each procedure with these rows: objective; population (table and filter); tables joined and the keys; period; direction of the test; controls; known limits. For example, for the journal entries: population JournalEntry in the period; joined to GLEntry on type and key and to Employee on the approver; controls that the count of entries and the sum of TotalAmount agree with the debits of the ledger rows; limits that GLEntry's creator column is not the preparer.

**Check:** each procedure has a population, keys, a control total and a limit, and the plan asks for only the tables it needs.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Sales invoices; invoice lines | 20,914; 27,933 | Step 1 |
| Invoices with no ledger rows | 0 | Step 2 |
| Shipment lines never invoiced; of | 9; 27,503 | Step 3 |
| Billable service hours; billed hours | 19,627.49; 19,627.49 | Step 3 |
| Order lines never received; received in parts | 277; 4,655 | Step 5 |
| Receipt lines billed in parts; invoice lines with no order line | 9,477; 355 | Step 5 |
| Journal entries; their ledger rows | 851; 2,821 | Step 6 |

## What a strong answer says

- **Requirement (1).** The tables and keys of the invoice population, the posting test through the type and key, the reason it falls short, and an independent population from shipments, service time and orders.
- **Requirement (2).** The line-level keys, the comparisons, and the gaps: no receipt price, parts, and lines with no order line.
- **Requirement (3).** The two tables, the logical link with its two columns, and the columns sorted by the table that holds them.
- **Requirement (4).** A plan with populations, keys, direction, controls and limits.

A weak answer names tables with no keys, tests completeness from the invoices, joins headers instead of lines, or says to extract everything.

## Common mistakes and how to respond

- **Completeness from invoices.** *Symptom:* "count the invoices and compare to the ledger". *Response:* ask where an uninvoiced sale would show.
- **Headers joined for the three-way match.** *Symptom:* an inflated row count. *Response:* ask how many lines an order has.
- **The receipt's price assumed.** *Response:* ask which column of GoodsReceiptLine holds a unit cost.
- **A JournalEntryID looked for in GLEntry.** *Response:* ask which two columns identify the document.
- **The key without the type.** *Response:* show the rows the same number finds in other types.
- **No control totals.** *Symptom:* a list of tables only. *Response:* ask how they will know the extract is complete.
- **Everything extracted.** *Response:* ask which tables the procedure reads.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: revenue completeness | 30 | Tables and keys, the posting test, the reversed direction and an independent population | Tables without the direction |
| Requirement 2: the three-way match | 25 | Line-level keys, the comparisons and at least two gaps | Keys without gaps |
| Requirement 3: the journal entries | 25 | The two tables, the logical link and the columns sorted | The tables without the link |
| Requirement 4: the plan | 20 | A table for each procedure with controls and limits | A narrative without controls |

## Extensions and discussion questions

- Add a fourth plan: payroll, from PayrollRegister to PayrollPayment to the ledger. Which rows have no payment, and which direction does the test run? (Chapter 12's tests and Exercise 3.6's extension look at the trace.)
- Write the control totals for the extract of each procedure, and say what each would catch.
- Discuss: why is the receipt's missing price a problem for a three-way match that wants independent evidence?
- Discuss: who should provide the extract, the auditor or the client's IT staff, and what would you ask to see about how it was made?
