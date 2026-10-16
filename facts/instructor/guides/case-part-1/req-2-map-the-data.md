---
note: case1.r2
uses: [case1.g2]
title: Map the data (Chapter 3)
kind: requirement
number: '2'
unit: case1
perspective: general
tool: conceptual
minutes: 45
solution: ''
figures:
  - id: IF-C1-2-A
    kind: diagram
    purpose: The model data map of the Furniture margin, from the documents to the two Furniture accounts.
    shows: Seven tables in Chapter 3's crow's foot notation. SalesInvoice and SalesInvoiceLine stand at the left and Shipment and ShipmentLine at the right, with Item between the two line tables and Account and GLEntry below it. SalesInvoiceLine joins SalesInvoice on SalesInvoiceID and Item on ItemID; ShipmentLine joins Shipment on ShipmentID and Item on ItemID; Item reaches Account three times through RevenueAccountID, COGSAccountID and InventoryAccountID, with the Furniture values shown in the Item rows and the three Furniture rows of Account highlighted with their AccountID and account number; GLEntry joins Account on AccountID. Two dashed amber lines, in the figure standard's style for the source-document trace, run from SalesInvoiceLine and ShipmentLine to the GLEntry columns SourceDocumentType, SourceDocumentID and SourceLineID. Each solid line carries its cardinality at both ends.
    data: The cardinality and optionality of each join, computed from the data as in the Expected results, and the account numbers of the Furniture items.
---
{% set g = case1_g2 %}
# Requirement 2: Map the data (Chapter 3)

{{ header() }}

## Purpose and learning outcomes

Requirement 2 is the case's second stage, identifying and accessing the data. The controller's question lives in the data in three places: a selection (which items are Furniture), two accounts (where the revenue and the cost post) and a set of joins that connects the documents to the ledger. The map becomes the first half of the appendix.

By the end, students can:

- find the column that marks Furniture items and the three account columns that follow from it, and translate AccountIDs into account numbers;
- name the key and the cardinality of each join from the invoice lines, the shipment lines and the ledger;
- say where a return posts its cost and where it posts its revenue, and what that means for a product-line margin.

**Competencies practiced.** CPA Evolution ISC M4 (use and management of data) and Core S2 M4 (information technology and IT controls); IMA Data Literacy; IFAC IES 3 (a), evaluating data and information from several sources; AACSB A5 part 5.2. The analytics type is descriptive, at the stage of identifying and accessing the data.

## Before you assign

- Students need the working copy, with the Item, Account, SalesInvoice, SalesInvoiceLine, Shipment, ShipmentLine and GLEntry worksheets, and Chapter 3: Figures 3.7 and 3.9 and Tutorial 3.2. Exercise 3.2 is the closest practice.
- The requirement relies on these conditions: the {{ items }} Furniture items share one revenue, one cost of goods sold and one inventory account; every AccountID is smaller than every account number, so a filter on an account number in the AccountID column finds nothing; the postings of a sales invoice and of a shipment carry the key of their line; and the {{ discounts }} account has no postings, so discounts are already inside the invoice lines' LineTotal.

## How to run it

Individual work or pairs, 45 minutes: 15 on the Item and Account worksheets, 20 on the joins and 10 on returns. **Hints to hold back.** For the joins, say "read each line aloud from the parent, then from the child", and do not name the keys. For returns, say "filter GLEntry by source document type", and do not name the accounts. **Collect** the data map (a sketch is fine; the appendix needs a clean version) and three sentences on returns.

## Step-by-step solution

### Phase 1: Find the Furniture accounts

**Step 1. Select the Furniture items.** In the **Item** worksheet, open the filter list of ItemGroup and keep Furniture. Read the status bar for the count.

**Check:** the status bar reads {{ items }} items. The filter buttons are already on, as in the Part I tutorials; do not use Data > Filter, which would switch them off.

**Step 2. Read the three account columns.** With the filter on, open the filter lists of RevenueAccountID (column {{ g.cols.RevenueAccountID }}), COGSAccountID (column {{ g.cols.COGSAccountID }}) and InventoryAccountID (column {{ g.cols.InventoryAccountID }}).

**Check:** each list holds one value: {{ revenue.id }}, {{ cogs.id }} and {{ inventory.id }}. One value in each means the mapping is by product line, so every Furniture sale and shipment posts to the same accounts. **Watch for:** students who read these numbers as account numbers. They are keys of the Account table.

**Step 3. Look the keys up in the Account worksheet.** Use the lookup you used in Tutorial 3.2, or filter AccountID. A formula for the first:

```jinja
=XLOOKUP({{ revenue.id }}, Account!A:A, Account!B:B)
```

| AccountID | AccountNumber | AccountName | Role |
|---:|---:|---|---|
| {{ revenue.id }} | {{ revenue.number }} | {{ revenue.name }} | Revenue of the product line |
| {{ cogs.id }} | {{ cogs.number }} | {{ cogs.name }} | Cost of goods sold of the product line |
| {{ inventory.id }} | {{ inventory.number }} | {{ inventory.name }} | Inventory that a shipment relieves and a return restores |

**Check:** the data map and the memo use account numbers. **Watch for:** filtering GLEntry's AccountID column for the account number: it finds no rows, because the AccountIDs are smaller than any account number.

### Phase 2: Sketch the join paths

**Step 4. Name each join, its key and its cardinality.** Read each relationship from the parent and from the child, as in Exercise 3.2. The five joins the requirement names are:

| Join (child to parent) | Key | Cardinality | What the data show |
|---|---|---|---|
{% for j in joins %}
| {{ j.child }} to {{ j.parent }} | {{ j.child }}.{{ j.key }} = {{ j.parent }}.{{ j.key }} | One {{ j.parent }} to {{ 'one or many' if j.lo >= 1 else 'zero or many' }} {{ j.child }} rows | {{ 'Every parent has a child' if j.lo >= 1 else 'Some parents have no child' }}; the largest has {{ j.hi|count }}; orphaned keys {{ j.orphans }} |
{% endfor %}

{{ figure('IF-C1-2-A') }}

**Check:** each join names a key on both sides and the cardinality from the parent's end. Every invoice and shipment has a line, so the first and third joins are one to one-or-many. An item may never be invoiced ({{ g.unsold }} items have no invoice line) and an account may have no postings ({{ g.unposted }} of {{ g.account_rows }}), so the others are one to zero-or-many. **Watch for:** "one to many" with no optionality, the arrow drawn from the wrong table, and the cardinality read from the child end ("many invoices to one line").

**Step 5. Add the account mapping and the trace.** A strong map also shows two links that are not foreign keys between documents. Item.RevenueAccountID, COGSAccountID and InventoryAccountID each join Account on AccountID. And the ledger reaches a document through SourceDocumentType, SourceDocumentID and SourceLineID: a revenue posting names its invoice and invoice line, and a cost posting names its shipment and shipment line. Requirement 4 uses these logical links.

**Check:** the map shows a path from a document line to the ledger row.

### Phase 3: Where returns post

**Step 6. Filter GLEntry by the two document types.** Filter SourceDocumentType for SalesReturn and read the accounts it posts to; then do the same for CreditMemo.

a. A return posts its cost: it credits {{ cogs.number }} (the cost of goods sold of the product line, reduced) and debits {{ inventory.number }} (the inventory restored). {{ g.ql3 }} has {{ g.quarters.q3.cogs_rows }} Furniture return lines posted to {{ cogs.number }}, and {{ g.ql4 }} has {{ g.quarters.q4.cogs_rows }}.
b. A credit memo posts the revenue side: it debits {{ returns.number }}, {{ returns.name }}, which every product line shares. It also debits {{ freight.number }}, {{ freight.name }}, in {{ freight.rows }} postings over the whole ledger, which reverse billed freight.

**Check:** the cost side stays by product line and the revenue side does not. A Furniture margin built from {{ revenue.number }} and {{ cogs.number }} therefore takes revenue before customer credits and cost after the returned goods, so it overstates the margin by the Furniture part of the credits. **Watch for:** the claim that returns do not affect the margin, and the claim that the margin is unaffected because the account is "contra revenue".

**Step 7. Say how large the limit is, if you can.** The postings to {{ returns.number }} carry the key of their credit memo line (SourceLineID), and a credit memo line names an item. So the Furniture part of the shared account is recoverable through the trace. In {{ g.ql3 }} the credit memos posted ${{ g.quarters.q3.posted|money }} to {{ returns.number }} on {{ g.quarters.q3.rows }} lines, of which ${{ g.quarters.q3.furniture|money }} ({{ g.quarters.q3.furniture_rows }} lines) were Furniture; in {{ g.ql4 }}, ${{ g.quarters.q4.posted|money }} on {{ g.quarters.q4.rows }} lines, of which ${{ g.quarters.q4.furniture|money }} ({{ g.quarters.q4.furniture_rows }} lines) were. The case does not ask for this figure. A student who finds it has applied Chapter 3 beyond the requirement.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Furniture items | {{ items }} | Step 1 |
| Revenue, cost and inventory accounts | {{ revenue.number }}, {{ cogs.number }}, {{ inventory.number }} (AccountIDs {{ revenue.id }}, {{ cogs.id }}, {{ inventory.id }}) | Steps 2 and 3 |
| Joins checked, and orphaned keys among them | {{ joins|length }}, {{ joins|map(attribute='orphans')|sum }} | Step 4 |
| Items never invoiced; accounts with no ledger rows | {{ g.unsold }}; {{ g.unposted }} | Step 4 |
| Postings to {{ returns.number }}, by quarter | {{ g.quarters.q3.rows }}; {{ g.quarters.q4.rows }} | Step 7 |
| Furniture part of those postings | ${{ g.quarters.q3.furniture|money }}; ${{ g.quarters.q4.furniture|money }} | Step 7 |

{{ expected() }}

## What a strong answer says

- **The accounts.** The ItemGroup column selects Furniture, the three account columns hold one key each, and the Account worksheet turns them into account numbers.
- **The joins.** Five joins, each with its key and its cardinality read from the parent, with optionality, and the ledger's link to a document named as a logical one.
- **Returns.** The cost of a return posts to the product line's cost account and restores inventory, and the revenue side goes to {{ returns.number }}, which all product lines share. So the Furniture margin from {{ revenue.number }} and {{ cogs.number }} takes revenue before customer credits and cost after the returned goods, which overstates it. A strong answer adds that the trace can size the effect.

A weak answer reports AccountIDs as account numbers, draws joins with no keys, or says returns post only to Furniture accounts.

## Common mistakes and how to respond

- **AccountID as account number.** *Symptom:* a map with {{ revenue.id }} where {{ revenue.number }} belongs. *Response:* ask which column of the Account worksheet a financial statement shows.
- **No cardinality, or one end only.** *Symptom:* "one to many" for every line. *Response:* ask which items were never invoiced.
- **Joins drawn from the wrong table.** *Symptom:* "many invoices to one line". *Response:* have them read the line aloud from the parent.
- **The Item account columns missed.** *Symptom:* no path from Item to Account. *Response:* ask how the system knows to post a desk to {{ revenue.number }}.
- **Returns on one side only.** *Symptom:* "returns reduce Furniture cost". *Response:* ask which account receives the credit memo.
- **Filtering the ledger on the wrong key.** *Symptom:* an empty filter. *Response:* point to the Watch out and ask what the AccountID of {{ revenue.number }} is.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| The Furniture accounts | 25 | The selecting column, the three account columns and the account numbers | IDs reported as numbers, or one account missing |
| The five joins | 40 | Each with its key and its cardinality, with optionality (8 points each) | Key without cardinality, or the wrong direction |
| Returns | 35 | Cost side by product line, revenue side shared, and the consequence for the margin | One side only, or no consequence stated |

## Extensions and discussion questions

- Add the trace links to the map, and write the path from a Furniture invoice line to its revenue posting.
- Use the credit memo lines to size the Furniture part of {{ returns.number }} in each quarter, and say whether it changes the comparison.
- Discuss: why would a company post the revenue side of returns to one shared account while the cost side follows the product?
- Discuss: Requirement 4 reconciles totals through this map. Which join do you trust least, and what would you test first?
