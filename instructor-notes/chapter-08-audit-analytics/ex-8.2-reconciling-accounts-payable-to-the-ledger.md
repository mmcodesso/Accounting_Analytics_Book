# Exercise 8.2: Reconciling Accounts Payable to the Ledger

| | |
|---|---|
| Unit | Chapter 8: Audit Analytics in Excel |
| Item | Exercise 8.2 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheet Ex 8.2, with Ex 8.2 Pivot, Ex 8.2 JE Rows and the queries OpenPayables, PaidByInvoice, LedgerAP and PurchaseOrders |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

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
- **Data conditions.** Account 2010 is AccountID 22. Its ledger rows come from PurchaseInvoice, DisbursementPayment and JournalEntry documents, and the JournalEntry rows are three: the opening balance entry and two Debt Reclass entries. Both reclassified invoices are from Nelson-Rocha (SupplierID 5) and have no payments. 263 supplier payments dated after the as-of date already sit in the ledger, and each pays an invoice dated on or before it.
- **Verify first.** Run the comparison once. The difference between the two sides is $1,456,371.12, and the three entries explain all of it.

## How to run it

Pairs or individual, about 90 minutes: 25 for the two queries (requirements 1 and 2), 15 for the PivotTable and Show Details (3), 25 for the reconciling items and the orders (4) and 25 for the workpaper (5). Hold back the hint that the entries are the explanation until the PivotTable shows only a few rows. Collect the workbook.

## Step-by-step solution

### Requirement (1): The open supplier invoices

**Step 1. Group the payments by invoice.**

a. In the Power Query Editor, right-click the Payments query in the **Queries** pane, choose **Reference** and name the new query `PaidByInvoice`.
b. Choose **Transform > Group By**, group by PurchaseInvoiceID, name the new column `PaidTotal` and choose **Sum** of Amount. One grouping column and one aggregation need no **Advanced**.

**Step 2. Build OpenPayables.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx, select **T37_PurchaseInvoice** and click **Transform Data**. Name the query `OpenPayables` and filter InvoiceDate to dates before `2027-01-01`.
b. Merge OpenPayables with **PaidByInvoice** on PurchaseInvoiceID, with a left outer join, and expand PaidTotal without the prefix.
c. Replace `null` in PaidTotal with `0`, add a custom column `OpenBalance` with `[GrandTotal] - [PaidTotal]`, set its type to **Decimal Number** and round it to `2` places with **Transform > Rounding > Round**.
d. Filter OpenBalance to values greater than 0, then load the query to a worksheet as a Table.

**Check:** 3,462 invoices with a total of $4,781,095.54. **Watch for:** the rounding step left out. The sums of payments leave residues of a fraction of a cent, so 301 fully paid invoices look open and the total moves by cents.

### Requirement (2): The ledger balance

**Step 3. Import account 2010.** Import **T3_GLEntry** with **Transform Data**, never **Load**, and name the query `LedgerAP`. Filter AccountID equal to `22` and PostingDate before `2027-01-01`, then add a custom column `Amount` with `[Credit] - [Debit]` (the sign of a liability) and load it. On the worksheet `Ex 8.2` calculate the balance and the invoice total:

```
=SUM(LedgerAP[Credit])-SUM(LedgerAP[Debit])
=SUM(OpenPayables[OpenBalance])
```

**Check:** the balance of account 2010 is $6,237,466.66 on 80,071 rows, against $4,781,095.54 of open invoices. **Watch for:** the AccountID typed as the account number (an AccountID of 2010 returns nothing), and the date filter left out. The 263 payments of 2027 then pull the balance down by $271,327.17, and the reconciliation shows an extra difference of that size.

### Requirement (3): The ledger by source

**Step 4. Build the PivotTable and list the journal entry rows.**

a. Select a cell in the LedgerAP Table, choose **Insert > PivotTable** and place it on a new worksheet.
b. Drag SourceDocumentType to the **Rows** area, and GLEntryID (set to **Count**) and Amount to the **Values** area.
c. Double-click the Sum of Amount for JournalEntry. **Show Details** lists three rows on a new worksheet.

**Check:** PurchaseInvoice 40,204 rows and $56,461,312.87; DisbursementPayment 39,864 rows and -$51,680,217.33; JournalEntry 3 rows and $1,456,371.12.

### Requirement (4): The reconciling items

**Step 5. Reconcile.** On `Ex 8.2` list the ledger balance, the three entries and the invoices (layout in the figure). Look the description up and read the invoice number from it, then take each amount from the ledger with a sign that makes the sum work:

```
=XLOOKUP(B13,JournalEntries[EntryNumber],JournalEntries[Description])
=--TEXTBEFORE(TEXTAFTER(C14,"invoice ")," ")
=-SUMIFS(LedgerAP[Amount],LedgerAP[VoucherNumber],B13)
=ROUND(F16-F17,2)
```

The model answer's items are the opening entry (less the credit that has no invoice detail) and the two reclassifications (added back, because the detail still shows the invoices as open).

> **[Figure placeholder IF-08-2-A]** The reconciliation workpaper of account 2010 to the open supplier invoices, with every reconciling item explained.
> Kind: excel-mock · Shows: The Ex 8.2 worksheet from the ledger balance down to the unexplained difference. Columns Item, Voucher, Entry description, PurchaseInvoiceID, InvoiceNumber, Amount, What it is and Correction belongs in. Three reconciling rows: the opening entry as a negative amount and the two reclassifications as positive amounts. The unexplained difference of zero is outlined. · Data: GLEntry for account 2010 by journal entry, and the open supplier invoices at the as-of date (the Expected results table). · Status: planned

**Check:** the unexplained difference is 0. **Watch for:** the signs. A student who subtracts the reclassifications ends $1,280,000.00 away.

**Step 6. Explain each item.** The opening entry has no supplier invoices behind it, and no payment reduces it because every payment names an invoice. The same entry debits cash with exactly the same amount ($2,096,371.12), which students should flag as a question. The reclassifications moved note-financed capital invoices to `2110` Notes Payable, so the ledger is right and the invoice detail should be closed or marked settled by the note.

**Step 7. Look up the orders.** Import **T33_PurchaseOrder** as `PurchaseOrders` with the creator's and approver's names, then look up each invoice's order. One formula pattern serves for every column:

```
=XLOOKUP(XLOOKUP($A24,OpenPayables[PurchaseInvoiceID],OpenPayables[PurchaseOrderID]),PurchaseOrders[PurchaseOrderID],PurchaseOrders[ApproverName])
```

**Check:** both orders were created and approved by the purchasing manager, Jennifer Cole, whose limit is $25,000.00.

### Requirement (5): The workpaper

**Step 8. Write the conclusion.** An outline: objective; the two balances and the difference; the three entries with the correction each needs; no unexplained difference; the request for the conversion-date detail; and the control observation about the orders.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Open supplier invoices, count and total | 3,462; $4,781,095.54 | 2 |
| Account 2010, rows and balance | 80,071; $6,237,466.66 | 3 |
| JE-2024-000001, the opening balance | -$2,096,371.12 | 5 |
| JE-2024-000103, invoice V0005-2024-003160 | $360,000.00 | 5 |
| JE-2026-000001, invoice V0005-2026-021692 | $280,000.00 | 5 |
| Ledger after the items, and the unexplained difference | $4,781,095.54; zero | 5 |
| PO-2024-001942, dated 2024-07-11 | $360,000.00 | 7 |
| PO-2026-011104, dated 2026-01-07 | $280,000.00 | 7 |
| Payments dated after the as-of date | 263; -$271,327.17 | 3 |

> **Instructor notes, Exercise 8.2:** open invoices at 2026-12-31: 4,781,095.54. GL 2010 (credit minus debit): 6,237,466.66, made up of PurchaseInvoice 56,461,312.87, DisbursementPayment -51,680,217.33, and JournalEntry +1,456,371.12. The JournalEntry rows are three: (a) JE-2024-000001, the opening balance entry, credits 2010 with 2,096,371.12, accounts payable with no invoice detail in the extract, which no payment in the extract reduces (every payment names an invoice); the same entry debits cash with exactly the same amount, a coincidence worth a question; (b) JE-2024-000103 (Debt Reclass, 360,000.00) and (c) JE-2026-000001 (Debt Reclass, 280,000.00) debit 2010 and credit 2110 Notes Payable, reclassifying note-financed capital invoices V0005-2024-003160 and V0005-2026-021692 (supplier 5, Nelson-Rocha), which have no supplier payments and therefore still appear open in the invoice detail. Reconciliation: 4,781,095.54 - 640,000.00 + 2,096,371.12 = 6,237,466.66. The reclasses are explained (the invoice detail should be closed or flagged as settled by a note), while the opening balance is unsupported by the extract's detail, the same finding as accounts receivable: the conversion-date supplier detail is the evidence to request before deciding on a correction. The purchase orders behind the two capital invoices, PO-2024-001942 and PO-2026-011104, were created and approved by the Purchasing Manager, whose limit is 25,000 (Exercise 8.5).

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
