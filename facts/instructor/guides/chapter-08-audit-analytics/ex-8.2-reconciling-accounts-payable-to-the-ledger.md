---
note: ch08.ex2
uses: [ch08.g2]
title: Reconciling Accounts Payable to the Ledger
kind: exercise
number: '8.2'
unit: '8'
perspective: financial
tool: excel
minutes: 90
solution: "Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheet Ex 8.2, with Ex 8.2 Pivot, Ex 8.2 JE Rows and the queries OpenPayables, PaidByInvoice, LedgerAP and PurchaseOrders"
figures:
  - id: IF-08-2-A
    kind: excel-mock
    purpose: The reconciliation workpaper of account 2010 to the open supplier invoices, with every reconciling item explained.
    shows: "The Ex 8.2 worksheet from the ledger balance down to the unexplained difference. Columns Item, Voucher, Entry description, PurchaseInvoiceID, InvoiceNumber, Amount, What it is and Correction belongs in. Three reconciling rows: the opening entry as a negative amount and the two reclassifications as positive amounts. The unexplained difference of zero is outlined."
    data: GLEntry for account 2010 by journal entry, and the open supplier invoices at the as-of date (the Expected results table).
---
{% set g = ch08_g2 %}
# Exercise 8.2: Reconciling Accounts Payable to the Ledger

{{ header() }}

## Purpose and learning outcomes

Tutorial 8.2 reconciled receivables and found one unsupported line. This exercise repeats the method on payables and adds two things: reconciling items that run in both directions, and a correction that belongs in the invoice detail and not in the ledger. It also plants a coincidence for students to notice and a link to Exercise 8.5. It practices Group By, merges, a rounding step, a date cutoff, a PivotTable with Show Details, XLOOKUP and a workpaper. The analytics type is descriptive, with a diagnostic step in requirements (3) and (4).

By the end, students can:

- build the open-invoice detail of a liability and the ledger balance it should equal, on one cutoff (outcome 1);
- identify each reconciling item and decide whether the correction belongs in the ledger, the detail or neither (outcomes 1 and 6);
- trace a reconciling invoice to the order behind it and to the people who created and approved it (outcome 6);
- write a reconciliation workpaper with no unexplained difference (outcome 6).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S2 M9 (audit procedures, analytical procedures and data analytics); IMA Reporting and Control (financial recordkeeping, statement preparation and internal control); IFAC IES 2 (a) and (f); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3, which holds the Payments query (already filtered to the three fiscal years) and the Employees and JournalEntries queries. The model answer merges Employees twice for the order's creator and approver; students may look the names up instead.
- **Data conditions.** Account 2010 is AccountID {{ g.ap_id }}. Its ledger rows come from PurchaseInvoice, DisbursementPayment and JournalEntry documents, and the JournalEntry rows are {{ rows }}: the opening balance entry and two Debt Reclass entries. Both reclassified invoices are from {{ g.supplier }} (SupplierID {{ g.supplier_id }}) and have no payments. {{ g.after_n|count }} supplier payments dated after the as-of date already sit in the ledger, and each pays an invoice dated on or before it.
- **Verify first.** Run the comparison once. The difference between the two sides is ${{ (gl - open_ap)|money }}, and the three entries explain all of it.

## How to run it

Pairs or individual, about 90 minutes: 25 for the two queries (requirements 1 and 2), 15 for the PivotTable and Show Details (3), 25 for the reconciling items and the orders (4) and 25 for the workpaper (5). Hold back the hint that the entries are the explanation until the PivotTable shows only a few rows. Collect the workbook.

## Step-by-step solution

### Requirement (1): The open supplier invoices

**Step 1. Group the payments by invoice.**

a. In the Power Query Editor, right-click the Payments query in the **Queries** pane, choose **Reference** and name the new query `PaidByInvoice`.
b. Choose **Transform > Group By**, group by PurchaseInvoiceID, name the new column `PaidTotal` and choose **Sum** of Amount. One grouping column and one aggregation need no **Advanced**.

**Step 2. Build OpenPayables.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx, select **T37_PurchaseInvoice** and click **Transform Data**. Name the query `OpenPayables` and filter InvoiceDate to dates before `{{ d.N }}-01-01`.
b. Merge OpenPayables with **PaidByInvoice** on PurchaseInvoiceID, with a left outer join, and expand PaidTotal without the prefix.
c. Replace `null` in PaidTotal with `0`, add a custom column `OpenBalance` with `[GrandTotal] - [PaidTotal]`, set its type to **Decimal Number** and round it to `2` places with **Transform > Rounding > Round**.
d. Filter OpenBalance to values greater than 0, then load the query to a worksheet as a Table.

**Check:** {{ g.open_n|count }} invoices with a total of ${{ open_ap|money }}. **Watch for:** the rounding step left out. The sums of payments leave residues of a fraction of a cent, so {{ g.residue|count }} fully paid invoices look open and the total moves by cents.

### Requirement (2): The ledger balance

**Step 3. Import account 2010.** Import **T3_GLEntry** with **Transform Data**, never **Load**, and name the query `LedgerAP`. Filter AccountID equal to `{{ g.ap_id }}` and PostingDate before `{{ d.N }}-01-01`, then add a custom column `Amount` with `[Credit] - [Debit]` (the sign of a liability) and load it. On the worksheet `Ex 8.2` calculate the balance and the invoice total:

```
=SUM(LedgerAP[Credit])-SUM(LedgerAP[Debit])
=SUM(OpenPayables[OpenBalance])
```

**Check:** the balance of account 2010 is ${{ gl|money }} on {{ g.gl_rows|count }} rows, against ${{ open_ap|money }} of open invoices. **Watch for:** the AccountID typed as the account number (an AccountID of 2010 returns nothing), and the date filter left out. The {{ g.after_n|count }} payments of {{ d.N }} then pull the balance down by ${{ (g.after_amount|abs)|money }}, and the reconciliation shows an extra difference of that size.

### Requirement (3): The ledger by source

**Step 4. Build the PivotTable and list the journal entry rows.**

a. Select a cell in the LedgerAP Table, choose **Insert > PivotTable** and place it on a new worksheet.
b. Drag SourceDocumentType to the **Rows** area, and GLEntryID (set to **Count**) and Amount to the **Values** area.
c. Double-click the Sum of Amount for JournalEntry. **Show Details** lists {{ rows }} rows on a new worksheet.

**Check:** PurchaseInvoice {{ g.sources.PurchaseInvoice|count }} rows and ${{ pi|money }}; DisbursementPayment {{ g.sources.DisbursementPayment|count }} rows and -${{ (dp|abs)|money }}; JournalEntry {{ g.sources.JournalEntry|count }} rows and ${{ je|money }}.

### Requirement (4): The reconciling items

**Step 5. Reconcile.** On `Ex 8.2` list the ledger balance, the three entries and the invoices (layout in the figure). Look the description up and read the invoice number from it, then take each amount from the ledger with a sign that makes the sum work:

```
=XLOOKUP(B13,JournalEntries[EntryNumber],JournalEntries[Description])
=--TEXTBEFORE(TEXTAFTER(C14,"invoice ")," ")
=-SUMIFS(LedgerAP[Amount],LedgerAP[VoucherNumber],B13)
=ROUND(F16-F17,2)
```

The model answer's items are the opening entry (less the credit that has no invoice detail) and the two reclassifications (added back, because the detail still shows the invoices as open).

{{ figure('IF-08-2-A') }}

**Check:** the unexplained difference is 0. **Watch for:** the signs. A student who subtracts the reclassifications ends ${{ (2 * reclassed)|money }} away.

**Step 6. Explain each item.** The opening entry has no supplier invoices behind it, and no payment reduces it because every payment names an invoice. The same entry debits cash with exactly the same amount (${{ opening|money }}), which students should flag as a question. The reclassifications moved note-financed capital invoices to `2110` Notes Payable, so the ledger is right and the invoice detail should be closed or marked settled by the note.

**Step 7. Look up the orders.** Import **T33_PurchaseOrder** as `PurchaseOrders` with the creator's and approver's names, then look up each invoice's order. One formula pattern serves for every column:

```
=XLOOKUP(XLOOKUP($A24,OpenPayables[PurchaseInvoiceID],OpenPayables[PurchaseOrderID]),PurchaseOrders[PurchaseOrderID],PurchaseOrders[ApproverName])
```

**Check:** both orders were created and approved by the {{ g.approver_title|lower }}, {{ g.approver }}, whose limit is ${{ g.approver_limit|money }}.

### Requirement (5): The workpaper

**Step 8. Write the conclusion.** An outline: objective; the two balances and the difference; the three entries with the correction each needs; no unexplained difference; the request for the conversion-date detail; and the control observation about the orders.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Open supplier invoices, count and total | {{ g.open_n|count }}; ${{ open_ap|money }} | 2 |
| Account 2010, rows and balance | {{ g.gl_rows|count }}; ${{ gl|money }} | 3 |
| {{ g.recon[0].voucher }}, the opening balance | -${{ (g.recon[0].amount|abs)|money }} | 5 |
{% for r in g.recon[1:] %}
| {{ r.voucher }}, invoice {{ r.invoice }} | ${{ r.amount|money }} | 5 |
{% endfor %}
| Ledger after the items, and the unexplained difference | ${{ open_ap|money }}; zero | 5 |
{% for r in g.recon[1:] %}
| {{ r.po }}, dated {{ r.po_date }} | ${{ r.po_total|money }} | 7 |
{% endfor %}
| Payments dated after the as-of date | {{ g.after_n|count }}; -${{ (g.after_amount|abs)|money }} | 3 |

{{ expected() }}

## What a strong answer says

- **Requirement (4).** The opening balance is unsupported by the extract's detail, and whether it belongs in the ledger or in missing invoice detail depends on the conversion records. The reclassifications are explained: the ledger is right and the invoice detail is wrong. The orders were created and approved by one person for more than ten times that person's limit, which goes to Exercise 8.5 and to the chief financial officer.
- **Requirement (5).** Objective, both balances, three explained items, no unexplained difference, and a conclusion that separates the reclassifications (a fix in the detail) from the opening balance (goes to the audit committee with the receivables finding).

A weak answer calls the opening balance an error and proposes to correct the ledger, or leaves the two reclassified invoices on the open list as if they were owed to the supplier.

## Common mistakes and how to respond

- **No rounding.** *Symptom:* hundreds of open invoices with balances of a fraction of a cent. *Response:* ask what the cent is for in a reconciliation.
- **No date cutoff on the ledger.** *Symptom:* an extra difference equal to the later payments. *Response:* ask which payments a December balance may include.
- **The account number as AccountID.** *Symptom:* an empty query. *Response:* ask which key the GLEntry table holds.
- **A liability with debits less credits.** *Symptom:* a negative balance and mirror-image items. *Response:* ask which side increases a liability.
- **The reclassification treated as a ledger error.** *Symptom:* a proposal to reverse the entries. *Response:* ask who owes the supplier after a note finances the invoice.
- **The opening balance explained away.** *Symptom:* "timing" or "opening entry, fine". *Response:* ask what invoice detail supports it.
- **Orders not traced.** *Symptom:* a finding about invoices only. *Response:* ask who created and approved the order.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: OpenPayables | 20 | Grouped, merged, nulls replaced, rounded, filtered | Not rounded |
| Requirement 2: LedgerAP | 15 | Account and cutoff right, sign of a liability | Cutoff missing |
| Requirement 3: PivotTable and Show Details | 20 | Source types, the journal entry rows listed | PivotTable without the rows |
| Requirement 4: items and orders | 25 | Each item explained, the correction placed, orders traced | Items without orders |
| Requirement 5: workpaper | 20 | Zero difference, conclusion, request for the detail | No conclusion |

## Extensions and discussion questions

- Use the payments dated after the as-of date as subsequent-disbursement evidence: all of them pay invoices open at the year-end, so what do they say about unrecorded liabilities?
- Age the open payables by days past due and compare the picture with the receivables aging.
- Discuss: why is the same cash amount on the debit side of the opening entry worth a question?
- Discuss: who should approve a purchase of this size, and what should the system do when the approver's limit is lower?
