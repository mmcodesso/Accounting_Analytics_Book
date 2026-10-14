# Requirement 2: Map the data (Chapter 3)

| | |
|---|---|
| Unit | Case Part 1: Getting the Data Ready for the Furniture Margin Question |
| Item | Requirement 2 |
| Tools | Workbook browsing and written work |
| Time | About 45 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 2 is the case's second stage, identifying and accessing the data. The controller's question lives in the data in three places: a selection (which items are Furniture), two accounts (where the revenue and the cost post) and a set of joins that connects the documents to the ledger. The map becomes the first half of the appendix.

By the end, students can:

- find the column that marks Furniture items and the three account columns that follow from it, and translate AccountIDs into account numbers;
- name the key and the cardinality of each join from the invoice lines, the shipment lines and the ledger;
- say where a return posts its cost and where it posts its revenue, and what that means for a product-line margin.

**Competencies practiced.** CPA Evolution ISC M4 (use and management of data) and Core S2 M4 (information technology and IT controls); IMA Data Literacy; IFAC IES 3 (a), evaluating data and information from several sources; AACSB A5 part 5.2. The analytics type is descriptive, at the stage of identifying and accessing the data.

## Before you assign

- Students need the working copy, with the Item, Account, SalesInvoice, SalesInvoiceLine, Shipment, ShipmentLine and GLEntry worksheets, and Chapter 3: Figures 3.7 and 3.9 and Tutorial 3.2. Exercise 3.2 is the closest practice.
- The requirement relies on these conditions: the 85 Furniture items share one revenue, one cost of goods sold and one inventory account; every AccountID is smaller than every account number, so a filter on an account number in the AccountID column finds nothing; the postings of a sales invoice and of a shipment carry the key of their line; and the Sales Discounts account has no postings, so discounts are already inside the invoice lines' LineTotal.

## How to run it

Individual work or pairs, 45 minutes: 15 on the Item and Account worksheets, 20 on the joins and 10 on returns. **Hints to hold back.** For the joins, say "read each line aloud from the parent, then from the child", and do not name the keys. For returns, say "filter GLEntry by source document type", and do not name the accounts. **Collect** the data map (a sketch is fine; the appendix needs a clean version) and three sentences on returns.

## Step-by-step solution

### Phase 1: Find the Furniture accounts

**Step 1. Select the Furniture items.** In the **Item** worksheet, open the filter list of ItemGroup and keep Furniture. Read the status bar for the count.

**Check:** the status bar reads 85 items. The filter buttons are already on, as in the Part I tutorials; do not use Data > Filter, which would switch them off.

**Step 2. Read the three account columns.** With the filter on, open the filter lists of RevenueAccountID (column R), COGSAccountID (column S) and InventoryAccountID (column Q).

**Check:** each list holds one value: 42, 50 and 5. One value in each means the mapping is by product line, so every Furniture sale and shipment posts to the same accounts. **Watch for:** students who read these numbers as account numbers. They are keys of the Account table.

**Step 3. Look the keys up in the Account worksheet.** Use the lookup you used in Tutorial 3.2, or filter AccountID. A formula for the first:

```
=XLOOKUP(42, Account!A:A, Account!B:B)
```

| AccountID | AccountNumber | AccountName | Role |
|---:|---:|---|---|
| 42 | 4010 | Sales Revenue - Furniture | Revenue of the product line |
| 50 | 5010 | COGS - Furniture | Cost of goods sold of the product line |
| 5 | 1040 | Inventory - Finished Goods | Inventory that a shipment relieves and a return restores |

**Check:** the data map and the memo use account numbers. **Watch for:** filtering GLEntry's AccountID column for the account number: it finds no rows, because the AccountIDs are smaller than any account number.

### Phase 2: Sketch the join paths

**Step 4. Name each join, its key and its cardinality.** Read each relationship from the parent and from the child, as in Exercise 3.2. The five joins the requirement names are:

| Join (child to parent) | Key | Cardinality | What the data show |
|---|---|---|---|
| SalesInvoiceLine to SalesInvoice | SalesInvoiceLine.SalesInvoiceID = SalesInvoice.SalesInvoiceID | One SalesInvoice to one or many SalesInvoiceLine rows | Every parent has a child; the largest has 7; orphaned keys 0 |
| SalesInvoiceLine to Item | SalesInvoiceLine.ItemID = Item.ItemID | One Item to zero or many SalesInvoiceLine rows | Some parents have no child; the largest has 362; orphaned keys 0 |
| ShipmentLine to Shipment | ShipmentLine.ShipmentID = Shipment.ShipmentID | One Shipment to one or many ShipmentLine rows | Every parent has a child; the largest has 7; orphaned keys 0 |
| ShipmentLine to Item | ShipmentLine.ItemID = Item.ItemID | One Item to zero or many ShipmentLine rows | Some parents have no child; the largest has 363; orphaned keys 0 |
| GLEntry to Account | GLEntry.AccountID = Account.AccountID | One Account to zero or many GLEntry rows | Some parents have no child; the largest has 100,464; orphaned keys 0 |

![The model data map of the Furniture margin, from the documents to the two Furniture accounts.](../figures/case-part-1/IF-C1-2-A.pdf)

**Check:** each join names a key on both sides and the cardinality from the parent's end. Every invoice and shipment has a line, so the first and third joins are one to one-or-many. An item may never be invoiced (55 items have no invoice line) and an account may have no postings (33 of 104), so the others are one to zero-or-many. **Watch for:** "one to many" with no optionality, the arrow drawn from the wrong table, and the cardinality read from the child end ("many invoices to one line").

**Step 5. Add the account mapping and the trace.** A strong map also shows two links that are not foreign keys between documents. Item.RevenueAccountID, COGSAccountID and InventoryAccountID each join Account on AccountID. And the ledger reaches a document through SourceDocumentType, SourceDocumentID and SourceLineID: a revenue posting names its invoice and invoice line, and a cost posting names its shipment and shipment line. Requirement 4 uses these logical links.

**Check:** the map shows a path from a document line to the ledger row.

### Phase 3: Where returns post

**Step 6. Filter GLEntry by the two document types.** Filter SourceDocumentType for SalesReturn and read the accounts it posts to; then do the same for CreditMemo.

a. A return posts its cost: it credits 5010 (the cost of goods sold of the product line, reduced) and debits 1040 (the inventory restored). 2026 Q3 has 28 Furniture return lines posted to 5010, and 2026 Q4 has 25.
b. A credit memo posts the revenue side: it debits 4060, Sales Returns and Allowances, which every product line shares. It also debits 4050, Freight Revenue, in 99 postings over the whole ledger, which reverse billed freight.

**Check:** the cost side stays by product line and the revenue side does not. A Furniture margin built from 4010 and 5010 therefore has revenue before returns and cost after them, so it overstates the margin by the revenue that returned goods reversed. **Watch for:** the claim that returns do not affect the margin, and the claim that the margin is unaffected because the account is "contra revenue".

**Step 7. Say how large the limit is, if you can.** The postings to 4060 carry the key of their credit memo line (SourceLineID), and a credit memo line names an item. So the Furniture part of the shared account is recoverable through the trace. In 2026 Q3 the credit memos posted $77,380.82 to 4060 on 63 lines, of which $55,437.94 (28 lines) were Furniture; in 2026 Q4, $68,575.94 on 66 lines, of which $39,719.44 (25 lines) were. The case does not ask for this figure. A student who finds it has applied Chapter 3 beyond the requirement.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Furniture items | 85 | Step 1 |
| Revenue, cost and inventory accounts | 4010, 5010, 1040 (AccountIDs 42, 50, 5) | Steps 2 and 3 |
| Joins checked, and orphaned keys among them | 5, 0 | Step 4 |
| Items never invoiced; accounts with no ledger rows | 55; 33 | Step 4 |
| Postings to 4060, by quarter | 63; 66 | Step 7 |
| Furniture part of those postings | $55,437.94; $39,719.44 | Step 7 |

> **Instructor notes, Requirement 2:** Item.ItemGroup = 'Furniture' (85 items); every Furniture item has RevenueAccountID 42 (account 4010 Sales Revenue - Furniture) and COGSAccountID 50 (account 5010 COGS - Furniture); InventoryAccountID 5 (1040). Joins: SalesInvoice 1 to 1..many SalesInvoiceLine (SalesInvoiceID); Item 1 to 0..many SalesInvoiceLine (ItemID); Shipment 1 to 1..many ShipmentLine (ShipmentID); Item 1 to 0..many ShipmentLine (ItemID); Account 1 to 0..many GLEntry (AccountID). Returns: SalesReturn postings reduce 5010 (and restore inventory 1040), so the cost side stays by product line; the revenue side of a return is recorded by CreditMemo postings to 4060 Sales Returns and Allowances, which is shared by all product lines (credit memos also reverse billed freight, 99 debits to 4050 Freight Revenue), so a Furniture margin built from 4010 and 5010 is a gross margin before returns. Account 4070 Sales Discounts has no postings.

## What a strong answer says

- **The accounts.** The ItemGroup column selects Furniture, the three account columns hold one key each, and the Account worksheet turns them into account numbers.
- **The joins.** Five joins, each with its key and its cardinality read from the parent, with optionality, and the ledger's link to a document named as a logical one.
- **Returns.** The cost of a return posts to the product line's cost account and restores inventory, and the revenue side goes to 4060, which all product lines share. So the Furniture margin from 4010 and 5010 is a measure before the revenue side of returns. A strong answer adds that the trace can size the effect.

A weak answer reports AccountIDs as account numbers, draws joins with no keys, or says returns post only to Furniture accounts.

## Common mistakes and how to respond

- **AccountID as account number.** *Symptom:* a map with 42 where 4010 belongs. *Response:* ask which column of the Account worksheet a financial statement shows.
- **No cardinality, or one end only.** *Symptom:* "one to many" for every line. *Response:* ask which items were never invoiced.
- **Joins drawn from the wrong table.** *Symptom:* "many invoices to one line". *Response:* have them read the line aloud from the parent.
- **The Item account columns missed.** *Symptom:* no path from Item to Account. *Response:* ask how the system knows to post a desk to 4010.
- **Returns on one side only.** *Symptom:* "returns reduce Furniture cost". *Response:* ask which account receives the credit memo.
- **Filtering the ledger on the wrong key.** *Symptom:* an empty filter. *Response:* point to the Watch out and ask what the AccountID of 4010 is.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| The Furniture accounts | 25 | The selecting column, the three account columns and the account numbers | IDs reported as numbers, or one account missing |
| The five joins | 40 | Each with its key and its cardinality, with optionality (8 points each) | Key without cardinality, or the wrong direction |
| Returns | 35 | Cost side by product line, revenue side shared, and the consequence for the margin | One side only, or no consequence stated |

## Extensions and discussion questions

- Add the trace links to the map, and write the path from a Furniture invoice line to its revenue posting.
- Use the credit memo lines to size the Furniture part of 4060 in each quarter, and say whether it changes the comparison.
- Discuss: why would a company post the revenue side of returns to one shared account while the cost side follows the product?
- Discuss: Requirement 4 reconciles totals through this map. Which join do you trust least, and what would you test first?
