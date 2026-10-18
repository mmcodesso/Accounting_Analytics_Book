# Exercise 3.2: Mapping the Charles River O2C Group to the Revenue Cycle

| | |
|---|---|
| Unit | Chapter 3: The Accounting Data Environment |
| Item | Exercise 3.2 |
| Perspective | Financial accounting |
| Tools | Workbook browsing and written work |
| Time | About 60 minutes |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A data dictionary is the first document an analyst writes about a source, and the one that later chapters keep returning to. This exercise has students write the revenue cycle's excerpt. It asks for three things that Tutorial 3.1 and Tutorial 3.2 taught separately: read the O2C diagram at both ends of every line, name the keys, and find what the cycle's own tables cannot tell you without the Accounting Core. The analytics type is descriptive, and the workflow stage is identifying and accessing the data.

By the end, students can:

- name the tables of the revenue cycle and state what each records (outcome 1);
- name the foreign key of each link and read its cardinality and optionality at both ends (outcomes 2 and 3);
- say which revenue information lives only in the Accounting Core, and which keys reach it (outcome 4);
- turn the findings into a one-page data dictionary excerpt that a colleague could use.

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S2 M4 (information technology and IT controls); IMA Data Literacy, and Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 3 (a), evaluating data and information from several sources; AACSB A5 part 5.2.

## Before you assign

- Students need Figure 3.7 and Figure 3.9, the workbook and Tutorials 3.1 and 3.2. The figure draws 12 relationships among 10 tables, counting Item from Master Data.
- The exercise relies on these conditions: no table of the cycle has an account column, so the postings and the account classes come from outside it; SalesOrder is the only one with a CostCenterID, and its cost center reaches the revenue rows of the invoice's ledger entries; the account mapping of a product sits in Item; invoice lines for design services have no shipment line; and the receipt's own SalesInvoiceID is filled for only 531 of 7,409 receipts, so the application table is the real link.
- Accept extra tables (price lists, service engagements, returns) if the student gives their role. The exercise asks for the path from order to cash, not for every table of the group.

## How to run it

Pairs work well, and it also suits a gallery walk. For about 60 minutes: 15 listing the tables (requirement 1), 20 on the relationships (requirement 2), 15 on the gaps (requirement 3) and 10 on the page (requirement 4).

**Hints.** For requirement (2), tell students to read each line aloud from the parent and then from the child. For requirement (3), ask them to open GLEntry and put its column headers next to SalesInvoice's. **Collect** the one-page excerpt.

## Step-by-step solution

### Requirement (1): List the tables and their roles

**Step 1. Name each table and say what one row records.** Open the worksheets of Figure 3.7 in order. A model answer:

| Table | One row records | Rows |
|---|---|---:|
| Customer | A customer, with segment, credit limit and payment terms | 220 |
| SalesOrder | An order, with date, status, total and cost center | 5,819 |
| SalesOrderLine | One item, quantity and price on an order | 22,269 |
| Shipment | Goods leaving a warehouse, with tracking and freight | 9,707 |
| ShipmentLine | The quantity of an order line that left in one shipment | 27,503 |
| SalesInvoice | What is billed: subtotal, freight, tax and total | 20,914 |
| SalesInvoiceLine | One billed line, with price and discount and the keys to its order line and shipment line | 27,933 |
| CashReceipt | A payment received | 7,409 |
| CashReceiptApplication | The part of a receipt applied to an invoice | 27,117 |
| Item (Master Data) | A product or service, with its prices, costs and account mapping | 266 |

**Check:** each entry says what event adds a row, not only what the table is for. **Watch for:** the cycle drawn as a chain of six core tables with no lines, and the junction tables skipped. Ask what stores a receipt that pays several invoices.

### Requirement (2): State each relationship

**Step 2. For each pair, name the foreign key and read both ends.** The parent holds the primary key and the child the foreign key. The model answer, with what the data show for each, is:

| Parent to child | Foreign key | At the parent end | At the child end | Parents with no child | Parents with several | Blank keys |
|---|---|---|---|---:|---:|---:|
| Customer to SalesOrder | SalesOrder.CustomerID | exactly one | zero or many | 9 | 211 | 0 |
| SalesOrder to SalesOrderLine | SalesOrderLine.SalesOrderID | exactly one | one or many | 0 | 5,405 | 0 |
| Item to SalesOrderLine | SalesOrderLine.ItemID | exactly one | zero or many | 55 | 211 | 0 |
| SalesOrder to Shipment | Shipment.SalesOrderID | exactly one | zero or many | 290 | 3,186 | 0 |
| Shipment to ShipmentLine | ShipmentLine.ShipmentID | exactly one | one or many | 0 | 6,550 | 0 |
| SalesOrderLine to ShipmentLine | ShipmentLine.SalesOrderLineID | exactly one | zero or many | 452 | 4,625 | 0 |
| SalesOrder to SalesInvoice | SalesInvoice.SalesOrderID | exactly one | zero or many | 51 | 5,209 | 0 |
| SalesInvoice to SalesInvoiceLine | SalesInvoiceLine.SalesInvoiceID | exactly one | one or many | 0 | 4,835 | 0 |
| ShipmentLine to SalesInvoiceLine | SalesInvoiceLine.ShipmentLineID | zero or one | zero or one | 9 | 0 | 439 |
| SalesOrderLine to SalesInvoiceLine | SalesInvoiceLine.SalesOrderLineID | exactly one | zero or many | 220 | 4,772 | 0 |
| CashReceipt to CashReceiptApplication | CashReceiptApplication.CashReceiptID | exactly one | one or many | 0 | 5,745 | 0 |
| SalesInvoice to CashReceiptApplication | CashReceiptApplication.SalesInvoiceID | exactly one | zero or many | 911 | 5,801 | 0 |

**Check:** each pair has a key and both ends. The ends that carry a circle are the ones with parents that have no child (customers with no orders, items never ordered, orders never shipped, invoices not yet paid) or a blank key (the design-service invoice lines, which have no shipment line). SalesOrderLine and CashReceiptApplication are the junction tables: each has two foreign keys and resolves a many-to-many relationship (orders and items, receipts and invoices). **Watch for:** answers that say one-to-many and stop. The exercise asks for optionality too. And a student who gives the receipt's own SalesInvoiceID as the link between receipt and invoice: only 531 receipts fill it, and the application table holds the real link.

### Requirement (3): Find what the cycle lacks

**Step 3. Put the O2C columns beside the ledger's, and list the gaps.** Open GLEntry beside SalesInvoice. The cycle records what was sold, to whom and when. It does not record the debits and credits or their accounts. A model answer:

| What the revenue analysis needs | Where it lives | The join |
|---|---|---|
| The debits and credits of each sale | GLEntry (Debit, Credit) | The trace: SourceDocumentType SalesInvoice and SourceDocumentID equal to SalesInvoiceID. A logical link |
| The account number, name and class (asset, liability, revenue) | Account | GLEntry.AccountID to Account.AccountID |
| The account that a product posts to | Item (RevenueAccountID, COGSAccountID, InventoryAccountID), then Account | Item.RevenueAccountID to Account.AccountID |
| The fiscal year and period of the posting | GLEntry (FiscalYear, FiscalPeriod) | Carried by the ledger row |
| The name of the cost center | CostCenter, in Organizational Planning | SalesOrder.CostCenterID to CostCenter.CostCenterID |

SalesOrder is the O2C table that already carries a cost center: 5,580 orders belong to Sales and 239 to Design Services. The ledger repeats it. On an invoice's ledger rows the revenue rows carry its order's cost center, and the receivable and the sales tax rows carry none.

**Check:** the student names the missing information, the table that holds it (Accounting Core, or CostCenter in Organizational Planning for the cost center's name), and the column. **Watch for:** the claim that the invoice stores the revenue account (it stores the amounts; the account is in the ledger and the item's mapping), and the claim that no O2C table has a cost center.

### Requirement (4): Write the data dictionary excerpt

**Step 4. Write one page.** A model page has three parts: a table entry for each table (purpose, primary key, foreign keys with their parents), a relationship table, and a paragraph on the links to the Accounting Core. The main columns with their types and the number of rows are a plus, not a requirement, unless a full column-level dictionary is assigned, and the types come from the database file: the worksheet shows values, not the declared types. A model entry for SalesInvoice, with the types the file declares:

| Column | Type | Role |
|---|---|---|
| SalesInvoiceID | INTEGER | primary key |
| InvoiceNumber | TEXT | unique document number |
| InvoiceDate | TEXT |  |
| DueDate | TEXT |  |
| SalesOrderID | INTEGER | foreign key to SalesOrder |
| CustomerID | INTEGER | foreign key to Customer |
| SubTotal | REAL |  |
| FreightAmount | REAL |  |
| TaxAmount | REAL |  |
| GrandTotal | REAL |  |
| Status | TEXT |  |
| PaymentDate | TEXT |  |

Dates are text in year-month-day form, money is REAL and keys are INTEGER. The relationships are logical: the file declares none, so the dictionary should say that they are tested rather than enforced.

**Check:** the page is usable by someone who has not seen the diagram, shows the keys, and says which links are not foreign keys. For example, the link to the ledger is a logical one and a trace that has to be tested.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Tables of the revenue cycle, with Item | 10 | Step 1 |
| Relationships on the diagram | 12 | Step 2 |
| Orphaned keys among them | 0 | Step 2 |
| Customers with no orders; invoice lines with no shipment line | 9; 439 | Step 2 |
| Orders in the first cost center; in the second | 5,580; 239 | Step 3 |
| Receipts that fill SalesInvoiceID | 531 of 7,409 | Step 2 |
| Invoices with no ledger rows | 0 | Step 3 |

## What a strong answer says

- **Requirement (1).** An event for each table, and the two junction tables named as such.
- **Requirement (2).** A foreign key and both ends for each pair, the optional ends with a reason, and the observation that two links are many-to-many through a junction table.
- **Requirement (3).** The postings, the account classes, the item's account mapping, the period and the cost center, each with the table and column that supply it.
- **Requirement (4).** A usable page that says the keys are logical.

A weak answer lists the tables without roles, gives one-to-many for every line, or says the invoice holds the ledger postings.

## Common mistakes and how to respond

- **Cardinality without optionality.** *Symptom:* one-to-many for every line. *Response:* ask which customers have no orders.
- **Reading from the wrong end.** *Symptom:* many customers to one order. *Response:* read the line aloud from the parent.
- **The receipt's SalesInvoiceID taken as the link.** *Response:* ask how a receipt of several invoices would be stored.
- **A junction table missing.** *Symptom:* a six-table chain. *Response:* ask where a quantity on an order line lives.
- **Postings placed in the cycle.** *Symptom:* "SalesInvoice records revenue and receivable". *Response:* ask which table has Debit and Credit.
- **The account mapping missed.** *Symptom:* no mention of Item's account columns. *Response:* ask how the revenue of a desk reaches the furniture account.
- **A dictionary with no types.** *Response:* ask what the file stores a date as.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the tables | 20 | Every table of the path with the event it records | Tables without roles, or a junction table missing |
| Requirement 2: the relationships | 30 | A key and both ends for each pair, with optionality | Cardinality only, or a pair missing |
| Requirement 3: the gaps | 25 | Each gap with its table and column, and the cost center noted | Gaps named without the join |
| Requirement 4: the excerpt | 25 | A usable page with the table roles, the keys and the links to the Accounting Core | Correct but not usable alone |

## Extensions and discussion questions

- Add the pricing tables (price lists, promotions) to the dictionary, and say which foreign keys of an order line reach them.
- Write the join path from a receipt to the ledger rows of its application, and say why it passes through a junction table.
- Discuss: if the file declared foreign keys, what would your dictionary say differently, and what would you still test?
- Discuss: Exercise 3.5 asks you to plan extractions from these tables. Which relationships would you most want to test first? (Exercise 3.6 does.)
