# Exercise 3.1: Tracing a Purchase Transaction Through the Charles River Database

| | |
|---|---|
| Unit | Chapter 3: The Accounting Data Environment |
| Item | Exercise 3.1 |
| Perspective | Financial accounting |
| Tools | Workbook browsing and written work |
| Time | About 75 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial 3.2 followed a sale. This exercise asks students to follow a purchase on their own, in the same way: from a supplier's invoice back to the receipt and the order that it bills, and forward to the payment and the three sets of ledger rows. The pattern is the one they know, headers and lines joined by keys and a ledger reached through SourceDocumentType and SourceDocumentID. What is new is the middle of the cycle: the receipt posts first, the invoice then clears a liability that the receipt created, and the price difference goes to its own account. The analytics type is descriptive, and the workflow stage is identifying and accessing the data.

By the end, students can:

- follow the foreign keys of an invoice line to its receipt line, order line, order and supplier, and name each key (chapter outcome 2);
- find the ledger rows of three different documents with the type-and-key filter (outcome 6);
- translate each AccountID into an account and say what the posting means (outcome 4);
- explain why the invoice debits goods received not invoiced and not inventory, and where the price difference goes;
- write the path as a one-page trace that an auditor could re-perform.

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and BAR M10 (advanced data analytics, including data models and joins); IMA Data Literacy, and Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (i), using information technology to analyze data; AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx and Tutorial 3.2, whose filter pattern they repeat. PurchaseInvoice has 40,204 rows, PurchaseInvoiceLine 40,648 and DisbursementPayment 40,127, so filters work without delay.
- The exercise relies on these conditions. Most paid invoices have a single line (36,581 of 36,980). Each invoice line names either a receipt line or an accrual journal entry: the 355 lines with an accrual have no receipt line and no order line, which is a dead end for this exercise, as requirement (2) warns. Every purchase invoice credits accounts payable for its GrandTotal, and the ledger rows of each of the three documents balance.
- Real invoices are untidy. 9,477 receipt lines are billed on more than one invoice line, so a student may find an invoiced quantity that differs from the received one; some invoices are paid in two or three payments. Neither is an error. Ask the student to explain it. Some invoices also carry purchase tax (7,226 of the paid single-line invoices). Such an invoice posts the tax to the purchase price variance account in a row of its own, with no SourceLineID, so its price variance is the line total less the receipt value, not the GrandTotal less it. The model invoice has none.
- Do the trace once yourself on a different invoice from the model below, so you can answer questions about the unusual ones.

## How to run it

Individual work, and each student picks a different invoice, so compare two traces at the end. For about 75 minutes: 10 choosing the invoice (requirement 1), 20 following the keys (requirement 2), 20 on the ledger rows (requirement 3), 10 on the payment (requirement 4) and 15 writing the page.

**Hints.** If a student cannot find the receipt, ask which column of the invoice line names it. For requirement (3), tell them to open the filter list of SourceDocumentType and read its values before they filter. Hold back the explanation of goods received not invoiced until they have found the rows. **Collect** the trace and the scratch notes of keys.

## Step-by-step solution

### Requirement (1): Choose an invoice

**Step 1. Pick a paid invoice with one line and a receipt line.**

a. On **PurchaseInvoice**, filter Status for Paid.
b. Choose a row and record PurchaseInvoiceID, InvoiceNumber, SupplierID and GrandTotal.
c. On **PurchaseInvoiceLine**, filter PurchaseInvoiceID for that number. Confirm that there is one row and that GoodsReceiptLineID is filled; if it is blank, the line is tied to an accrual, so choose another invoice.

**Check:** the model invoice is V0065-2026-020254 (PurchaseInvoiceID 20254) from Bell, Pruitt and David, SupplierID 65, with a GrandTotal of $829.51. **Watch for:** an invoice whose Status is Approved or Partially Paid, which has no payment or only a part to trace, and an invoice number copied into a filter on the wrong column.

### Requirement (2): Follow the keys

**Step 2. Follow the invoice line's keys, one worksheet at a time.** Record each key and the row it leads to.

| From | Key | To | The model row |
|---|---|---|---|
| PurchaseInvoiceLine | GoodsReceiptLineID 12860 | GoodsReceiptLine | 18.67 units received, ExtendedStandardCost $825.77 |
| GoodsReceiptLine | GoodsReceiptID 12260 | GoodsReceipt | GR-2025-012260, received 2025-10-06 |
| PurchaseInvoiceLine | POLineID 10839 | PurchaseOrderLine | 18.67 units ordered at $44.23 |
| PurchaseOrderLine | PurchaseOrderID 8900 | PurchaseOrder | PO-2025-008900, ordered 2025-10-01 |
| PurchaseOrder | SupplierID 65 | Supplier | Bell, Pruitt and David |
| PurchaseInvoiceLine | ItemID 177 | Item | RAW-CTN-0010, Cotton Fabric Roll |

![The model purchase traced from the supplier through the order, the receipt and the invoice to the payment, with the key on each link and the ledger postings of the three documents.](../figures/chapter-03-accounting-data-environment/IF-03-1-A.pdf)

**Check:** the keys agree three ways. The invoice line and the receipt line name the same POLineID, and the invoice, the receipt and the order name the same PurchaseOrderID and the same supplier. The invoice bills 18.67 units at $44.43 against the order's $44.23, and the receipt covers the same 18.67 units. **Watch for:** a student who follows the header's PurchaseOrderID and misses the line-level keys. The line carries the keys that matter, and the header repeats the order.

### Requirement (3): Read the ledger rows

**Step 3. Find the invoice's ledger rows.**

a. On **GLEntry**, filter SourceDocumentType for PurchaseInvoice and SourceDocumentID for 20254, the invoice's key and not its number.
b. Record GLEntryID, AccountID, Debit, Credit and SourceLineID of each row.
c. On **Account**, look up each AccountID and write the account number and name.
d. Total the Debit and Credit columns.

| GLEntryID | AccountID | Account | Debit | Credit | SourceLineID |
|---:|---:|---|---:|---:|---:|
| 671775 | 23 | 2020 Goods Received Not Invoiced | 825.77 |  | 20458 |
| 671776 | 55 | 5060 Purchase Price Variance | 3.74 |  | 20458 |
| 671777 | 22 | 2010 Accounts Payable |  | 829.51 |  |

**Check:** debits equal credits, and the credit to accounts payable is the GrandTotal. The invoice posted on 2026-01-13, its ReceivedDate, not on the invoice date. **Watch for:** two traps. Filtering SourceDocumentID alone finds 14 rows of 6 types, because other documents have the same number. And the ledger's VoucherNumber is the invoice number for almost every invoice, but not for 6: those are the second invoice of each supplier number that repeats (Exercise 2.6), so use the key, not the number, to find ledger rows.

**Step 4. Find the receipt's ledger rows.** Filter SourceDocumentType for GoodsReceipt and SourceDocumentID for 12260.

| GLEntryID | AccountID | Account | Debit | Credit | SourceLineID |
|---:|---:|---|---:|---:|---:|
| 573232 | 6 | 1045 Inventory - Materials and Packaging | 825.77 |  | 12860 |
| 573233 | 23 | 2020 Goods Received Not Invoiced |  | 825.77 | 12860 |

**Check:** the receipt posted on 2025-10-06, before the invoice. It debits the item's inventory account (the InventoryAccountID of RAW-CTN-0010 in Item) and credits goods received not invoiced for $825.77, the receipt value. Its SourceLineID is the receipt line's key, where the invoice's row carries the invoice line's key.

**Step 5. Explain why the invoice debits goods received not invoiced.** A model answer: when the goods arrived, Charles River owed the supplier but had no invoice, so the receipt recorded the inventory and a liability, goods received not invoiced, at the order price. The invoice does not bring the goods in again. It clears that liability for the $825.77 received and records what the supplier now bills, $829.51, as accounts payable. The $3.74 between them is purchase price variance, an unfavorable one here, because the invoice price is above the order price; it has its own row. Debiting inventory again would count the goods twice.

**Check:** the answer says that the receipt, not the invoice, brings in the inventory, that the liability moves from one account to another, and where the difference goes. **Watch for:** "the invoice records the purchase". It records what is owed, not what was received.

### Requirement (4): Follow the payment and write the trace

**Step 6. Find the payment and its ledger rows.**

a. On **DisbursementPayment**, filter PurchaseInvoiceID for 20254.
b. Record the payment, its date, the amount and the method.
c. On **GLEntry**, filter SourceDocumentType for DisbursementPayment and SourceDocumentID for 22688.

| GLEntryID | AccountID | Account | Debit | Credit |
|---:|---:|---|---:|---:|
| 780908 | 22 | 2010 Accounts Payable | 829.51 |  |
| 780909 | 2 | 1010 Cash and Cash Equivalents |  | 829.51 |

**Check:** payment DP-2026-022688 of $829.51 on 2026-03-01 by ACH pays the invoice in full. Its debit to accounts payable equals the credit that the invoice made, so the payable for this invoice nets to zero. A student whose invoice has a second payment adds its rows the same way.

**Step 7. Write the one-page trace.** A model outline: a path line (supplier, order, receipt, invoice, payment) with each document's number and date; a table of the keys followed; a table of the accounts, amounts and dates for the three documents; the explanation of goods received not invoiced; and one observation. For the model the observation is timing: the receipt is dated 2025-10-06, the invoice was received 2026-01-13 and the payment made 2026-03-01, so the liability sat in goods received not invoiced until the invoice arrived.

**Check:** every table, key, account and amount in the path appears, and each amount can be re-performed from the worksheets.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Model invoice; supplier | V0065-2026-020254; Bell, Pruitt and David | Step 1 |
| GrandTotal | $829.51 | Step 1 |
| Receipt value (ExtendedStandardCost) | $825.77 | Step 2 |
| Order unit cost; invoice unit cost | $44.23; $44.43 | Step 2 |
| Ledger rows of the invoice; of the receipt; of the payment | 3; 2; 2 | Steps 3, 4 and 6 |
| Purchase price variance | $3.74, unfavorable | Step 5 |
| Invoices paid in one payment; in more than one | 34,522; 2,641 | Requirement (4) |
| Ledger rows found by the invoice's key alone; their types | 14; 6 | Step 3 |

## What a strong answer says

- **Requirement (1).** An invoice that qualifies, with its four fields recorded.
- **Requirement (2).** Each key and the table it leads to, in order, with the observation that the keys agree and that quantity and price can differ between the documents.
- **Requirement (3).** The rows of both documents, accounts looked up through AccountID, the balance check, and an explanation of goods received not invoiced that separates the receipt from the invoice and names the variance.
- **Requirement (4).** The payment, its rows, and the statement that payable nets to zero; a trace that someone else could follow.

A weak answer lists tables without keys, reads AccountID as the account number, says the invoice records inventory, or stops at the invoice.

## Common mistakes and how to respond

- **AccountID read as the account number.** *Symptom:* account numbers that do not exist, or the wrong account. *Response:* ask which column of Account matches the AccountID.
- **The invoice number in the wrong filter.** *Symptom:* no rows in GLEntry. *Cause:* the number is in VoucherNumber, and SourceDocumentID holds the key. *Response:* ask which column holds the document's key.
- **SourceDocumentID without the type.** *Symptom:* rows of several types mixed together. *Response:* ask them to read the type column of what they found.
- **An invoice with an accrual line.** *Symptom:* a blank GoodsReceiptLineID. *Response:* tell them to choose again, and keep the case for the extension.
- **Inventory debited by the invoice.** *Symptom:* "the invoice records the purchase of inventory". *Response:* ask what the receipt posted earlier.
- **The variance row missed.** *Symptom:* the entry does not balance in their sum. *Response:* ask for the account of every row and what it is for.
- **A partial payment treated as full.** *Symptom:* the payable does not net to zero. *Response:* ask how many payments the invoice has.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: a qualifying invoice | 10 | A paid single-line invoice with a receipt line, fields recorded | An invoice that fails a condition |
| Requirement 2: the keys | 25 | Every key and table, and the agreement between the documents | Tables without keys, or a link missing |
| Requirement 3: the ledger rows | 30 | Both documents' rows, accounts looked up, a balanced check, and the explanation | Rows without accounts, or no explanation |
| Requirement 4: the payment | 15 | The payment, its rows, and the payable netting to zero | The payment without its ledger rows |
| The written trace | 20 | One page that another person could re-perform | Correct but unclear or over a page |

## Extensions and discussion questions

- Trace an invoice with two payments, and show that the payments add to the GrandTotal.
- Find an invoice line with an accrual journal entry and no receipt line, and trace it through AccrualJournalEntryID to the journal entry. Say what changes in the accounts.
- Find an invoice whose price is below the order price and compare its variance row with the model's.
- Discuss: the receipt and the invoice can fall in different fiscal years. What does goods received not invoiced hold at a year-end, and who should test it? (Chapter 12 tests it.)
- Discuss: which of the three documents would you sample to test that a liability exists, and which to test that it is complete?
