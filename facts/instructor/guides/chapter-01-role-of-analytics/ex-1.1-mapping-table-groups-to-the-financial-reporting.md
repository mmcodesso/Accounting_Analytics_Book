---
note: ch01.ex1
title: Mapping Table Groups to the Financial Reporting Cycle
kind: exercise
number: '1.1'
unit: '1'
perspective: financial
tool: conceptual
minutes: 60
solution: ''
figures: []
---
# Exercise 1.1: Mapping Table Groups to the Financial Reporting Cycle

{{ header() }}

## Purpose and learning outcomes

This is the first time students put a question to the whole workbook: for four reporting needs, where does the data live? The exercise practices the second stage of the workflow, identifying and accessing the data, and it prepares every later exercise, because a student who can name the tables behind revenue, receivables, inventory and cost of goods sold, and the ledger, knows where Part II starts. The analytics type is descriptive: each reporting need summarizes what happened.

By the end, students can:

- name the tables and columns that hold the data for revenue, accounts receivable, inventory and cost of goods sold, and general ledger reporting (outcome 4);
- explain that a header table, its line table, the master data that classifies them and the ledger that records them are different tables, often in different groups;
- identify a reporting task that needs the Order-to-Cash group and the Accounting Core together, and say why neither is enough alone;
- present the mapping in a one-page memo for a named reader (workflow stage 6).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and ISC M4 (use and management of data); IMA Data Literacy, and Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.2, judging a technology and communicating its results.

## Before you assign

- Students need CharlesRiver.xlsx and nothing else. Remind them to browse and close without saving.
- They should have done Tutorial 1.1 and read Table 1.3 and Figure 1.4. Without the tutorial they lose time finding worksheets.
- The exercise relies on these conditions, which you can confirm on the worksheets: invoices and shipments have a header table and a line table (SalesInvoice and SalesInvoiceLine, Shipment and ShipmentLine); the Item worksheet holds StandardCost and the three account IDs (RevenueAccountID, InventoryAccountID, COGSAccountID) that route a product's activity to the ledger; revenue and receivables post when an invoice is recorded, and cost of goods sold and inventory post when goods are shipped; a sales order posts nothing.
- Do requirement 3 yourself first. It takes five minutes, and it tells you whether a task a student proposes is feasible with these tables.

## How to run it

Individual work, in or out of class. A time budget for about 60 minutes: 20 minutes of browsing (requirement 1), 20 on the tables and columns (requirement 2), 10 on the cross-group task (requirement 3) and 10 for the memo (requirement 4).

Hold back two hints. After ten minutes, if a student lists only the tables of Table 1.3, say that the table shows key tables and ask where the lines of an invoice are. When writing the memo, if a student names a column they did not open, ask them to show you the worksheet. Collect the memo. A one-line list of the worksheets opened is a useful extra for checking that the browsing happened.

## Step-by-step solution

### Requirement (1): Find the tables behind each reporting area

**Step 1. Open one worksheet from each of the four groups.**

a. Open CharlesRiver.xlsx.
b. Click **SalesInvoice** (Order-to-Cash), **Item** (Master Data), **GLEntry** (Accounting Core) and **WorkOrder** (Manufacturing).
c. Read the headers in row 1 of each, and ask which of the four reporting areas each column could feed.

**Check:** every group gives at least one table. Item shows StandardCost and the three account IDs, and GLEntry shows Debit, Credit and the source columns.

**Step 2. Assign tables to areas.** Use the sheet tabs and Table 1.3, and add the line tables and the master data that the table does not list. A model answer:

| Reporting area | Order-to-Cash | Master Data | Accounting Core | Manufacturing |
|---|---|---|---|---|
| Revenue | SalesInvoice, SalesInvoiceLine, CreditMemo | Item | GLEntry, Account | None |
| Accounts receivable | SalesInvoice, CashReceipt, CashReceiptApplication, CreditMemo, Customer | None | GLEntry, Account | None |
| Inventory and cost of goods sold | Shipment, ShipmentLine | Item | GLEntry, Account | WorkOrder, MaterialIssue, ProductionCompletion, WorkOrderClose |
| General ledger reporting | The sources that post to it | None | Account, GLEntry, JournalEntry | The sources that post to it |

**Check:** each area has tables from more than one group, and Manufacturing appears only for inventory and cost. **Watch for:** students who put Item under Order-to-Cash. Item is Master Data.

### Requirement (2): Name the tables and columns and explain each area

**Step 3. List the columns for each area, and write two or three sentences.** The columns below are the ones to expect. The explanations are model outlines.

| Area | Tables and columns | What a good explanation says |
|---|---|---|
| Revenue | SalesInvoice: InvoiceDate, SubTotal, FreightAmount, TaxAmount, GrandTotal. SalesInvoiceLine: ItemID, Quantity, UnitPrice, Discount, LineTotal. Item: ItemGroup | Revenue is billed on invoices, and the lines let you group it by product. The invoice total splits across several ledger accounts (revenue, freight revenue and sales tax payable), so SubTotal and GrandTotal differ |
| Receivables | SalesInvoice: InvoiceNumber, InvoiceDate, DueDate, CustomerID, GrandTotal. CashReceiptApplication: SalesInvoiceID, ApplicationDate, AppliedAmount. CreditMemo: OriginalSalesInvoiceID, CreditMemoDate, GrandTotal. Customer: CustomerName, CreditLimit, PaymentTerms | A balance is what was billed, less what was applied and credited, as of a date. The age comes from DueDate. The control account is {{ ar }} |
| Inventory and cost of goods sold | Item: StandardCost, SupplyMode, InventoryAccountID, COGSAccountID. ShipmentLine: ItemID, QuantityShipped, ExtendedStandardCost. Shipment: ShipmentDate. Inventory movements: GoodsReceiptLine (purchases received into inventory), MaterialIssueLine (materials moved into production), ProductionCompletionLine (finished goods completed), with ExtendedStandardCost or ExtendedStandardTotalCost. WorkOrderClose: TotalVarianceAmount | Cost of goods sold is recorded when goods ship, at standard cost. Manufactured items add the Manufacturing tables, and the difference between actual and standard cost sits in WorkOrderClose and its own ledger account |
| General ledger | Account: AccountNumber, AccountName, AccountType, AccountSubType, ParentAccountID, NormalBalance. GLEntry: PostingDate, AccountID, Debit, Credit, FiscalYear, FiscalPeriod, SourceDocumentType. JournalEntry: EntryType, TotalAmount | A statement is a sum of GLEntry by account and period. Account gives the names, classes and hierarchy. Adjustments, accruals, depreciation and closes arrive as journal entries |

**Check:** a student explanation names a worksheet and at least two columns it actually has. **Watch for:** AccountID read as the account number. AccountID is the key of Account, and the statement number is AccountNumber.

### Requirement (3): Name a task that combines two groups

**Step 4. Propose a task that cannot be done in one group.** Accept any of these, and ask for the tables from each group and the reason.

- *Revenue tie-out.* SalesInvoiceLine, SalesInvoice and Item (Order-to-Cash and Master Data) against GLEntry and Account (Accounting Core), by fiscal year. The invoice side has items and customers, and the ledger side has the accounts and the periods. Neither can show that the other is complete.
- *Receivables to the control account.* The open invoices (SalesInvoice, CashReceiptApplication, CreditMemo) against the balance of account {{ ar }} in GLEntry.
- *Cost of goods sold to shipments.* ShipmentLine (ExtendedStandardCost) against GLEntry postings to the cost accounts.

**Check:** the answer says why: the documents explain a number, the ledger classifies and totals it, and only the two together show whether they agree. For the first task, the reference values are in the Expected results table.

### Requirement (4): Write the memo

**Step 5. Outline a one-page memo.** A strong memo has, in order: a header (to, from, date, subject); one sentence on purpose; the four-row table of area, tables and columns; the cross-group task with its tables; and, as a plus the requirement does not ask for, one closing line on what would come next, such as testing the keys that join the tables. Students who copy Table 1.3 into the memo have not done the exercise.

**Check:** the memo fits one page, names worksheets and columns, and is written for the supervisor, who is not looking at the workbook.

## Expected results

There are no calculated answers, but a student who opens the worksheets sees these sizes, and a student who does the tie-out finds the figures below.

| Quantity | Value | Where |
|---|---:|---|
| Rows in SalesInvoice | {{ rows.SalesInvoice|count }} | Step 1 |
| Rows in SalesInvoiceLine | {{ rows.SalesInvoiceLine|count }} | Step 2 |
| Rows in CashReceiptApplication | {{ rows.CashReceiptApplication|count }} | Step 3 |
| Rows in Item | {{ rows.Item|count }} | Step 1 |
| Rows in GLEntry | {{ rows.GLEntry|count }} | Step 1 |
| Rows in JournalEntry | {{ rows.JournalEntry|count }} | Step 3 |
| Invoice lines for fiscal {{ year }} (by invoice date) | {{ lines|money }} | Step 4 |
| Ledger credits to {{ revenue_accounts }} from invoices, fiscal {{ year }} | {{ ledger|money }} | Step 4 |
| Difference | {{ gap|money }} | Step 4 |

The ledger exceeds the invoice lines by a small amount because {{ cutoff_n }} invoices dated in fiscal {{ prior }} were posted on the first day of fiscal {{ year }}. Chapter 6 and Chapter 12 explain it. At this stage it is enough that students see that the documents and the ledger are close but not identical.

## What a strong answer says

- **Requirements (1) and (2).** The answer names the line tables and the master data, not only the tables of Table 1.3. It puts revenue and receivables at the invoice, and cost of goods sold at the shipment, and says why they can fall in different periods. It names real columns and reads the account numbers through Account.
- **Requirement (3).** The task has a reason for the second group: the ledger is the control total, or the documents are the detail behind it.
- **Requirement (4).** The memo is organized for a reader, with a table and a short explanation. A recommended next step is a plus.

A weak answer lists table names from memory, copies the "Primary Accounting Use" column of Table 1.3, or describes areas without worksheets.

## Common mistakes and how to respond

- **Only the tables of Table 1.3.** *Symptom:* no SalesInvoiceLine, ShipmentLine or Item. *Cause:* the table lists key tables only. *Response:* ask where the quantity and the item of an invoice are recorded.
- **A sales order as the source of revenue.** *Symptom:* SalesOrder and SalesOrderLine under revenue. *Cause:* orders feel like sales. *Response:* ask which worksheet's rows reach GLEntry; orders post nothing.
- **Item placed in Order-to-Cash.** *Symptom:* Master Data is empty in the answer. *Response:* point to the group column of Table 1.3.
- **Groups without columns.** *Symptom:* "O2C has the revenue data". *Response:* ask for the column a formula would add up.
- **AccountID taken as the account number.** *Symptom:* "account 42". *Response:* open Account and ask which column has the number on a statement.
- **Receivables from SalesInvoice alone.** *Symptom:* no receipt or credit table. *Response:* ask what happens to an invoice when the customer pays.
- **A memo that runs over a page, or has no reader.** *Response:* ask what the supervisor needs to decide.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: tables for each group and area | 25 | Tables from four groups, with line and master tables | Key tables only, or a group missing |
| Requirement 2: tables, columns and explanation for four areas | 30 | Real columns and two or three sentences for each area | Columns not checked, or no explanation |
| Requirement 3: a cross-group task | 20 | A task with tables from both groups and the reason | A task from one group, or no reason |
| Requirement 4: memo | 25 | One page, organized for the supervisor | Over a page, or a list with no reasoning |

## Extensions and discussion questions

- Add a column to the memo for the ledger accounts that each area's postings reach, and check one account number against the Account worksheet.
- Say which of the four areas the ledger alone could answer without the documents, and what it would lose.
- Find an area of reporting, such as property and equipment or payroll, that needs a group not used here, and map it in the same way.
- Discuss: the memo says where the data is. What would you test before trusting it? (Chapter 2 answers this with data quality dimensions.)
- Discuss: which key columns would you use to join the invoice lines to the ledger? (Chapter 3 teaches keys and tracing.)
