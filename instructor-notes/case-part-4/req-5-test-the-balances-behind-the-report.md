# Requirement 5: Test the balances behind the report (Chapters 14 to 16; auditing)

| | |
|---|---|
| Unit | Case Part 4: Finding the Cash Behind the Profit |
| Item | Requirement 5 |
| Perspective | Auditing |
| Tools | Power BI Desktop |
| Time | About 150 minutes |
| Solution file | PartIV-case.zip: Charles River Cash Case.pbip, page Reconciliations, the Findings table, Tests 4 and 5 of the Tests tab and the Requirement 5 rows of the Checks tab |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A report is only as good as the balances under it. The requirement rolls each working-capital account forward by its sources, reconciles receivables and payables to their open items, tests the cutoff and the sales tax account, and records every difference as a finding that the report itself tests. The words matter: each finding states what the records show, never what anyone did. The analytics type is diagnostic, with the dispositions as the judgment.

Students can:

- roll accounts forward by source document and name the parts no subledger supports (Step 1);
- reconcile receivables and payables to open items and explain each difference (Step 2);
- explain the billing differences with the cutoff findings of Chapters 6 and 12, and age the payables (Steps 3 and 4);
- test account `2050` and name the outside evidence (Step 5);
- record findings with dispositions and add tests that tie them to the differences (Step 6).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Reporting and Control (internal control); IFAC IES 2 (f), audit; AACSB A5 part 5.1.

## Before you assign

- **Files.** Requirements 1 to 4 done. The model answer is in PartIV-case.zip: the page, the Findings table and Tests 4 and 5.
- **From earlier work.** Exercise 16.1's open balance, Exercise 8.2's payables, Chapter 8's dispositions, Chapter 16's dispositions table and the cutoff findings of Chapters 6 and 12.
- **Data conditions.** The opening entry JE-2024-000001 carries balances no document supports; two supplier invoices were moved to notes payable while the subledger still shows them open; one supplier invoice crosses a year-end; account `2050` has no debit except credit memos.
- **Verify first.** The 81 Requirement 5 rows of the Checks tab agree.

## How to run it

Pairs, about 150 minutes: 25 for the roll-forward, 40 for the reconciliations, 25 for billing and aging, 20 for the sales tax, 30 for the findings and tests, 10 spare. Hold back the finding signs until a pair sees Test 4 fail. **Collect** the .pbix with the Findings table.

## Step-by-step solution

The Checks tab proves every value; the matrix layout is visible only in Desktop.

### Part 1: The roll-forward

**Step 1. Roll the accounts forward.** Add a **Matrix** titled "Working-capital accounts at the end of fiscal 2026, by source document" with AccountNumber on **Rows** (the six accounts), SourceDocumentType on **Columns** and Balance in **Values**, filtered to the current year.

**Check:** the JournalEntry column is what no subledger document supports: receivables $380,000.00, materials $3,587,025.70, finished goods $4,111,795.76 and payables -$1,456,371.12, which are the opening lines and, in payables, the two reclassifications to notes.

### Part 2: Reconciliations

**Step 2. Reconcile to the open items.**

a. Build ARInvoices and APInvoices as the project does, with the open balance, and relate them to Date.
b. Add cards titled "Ledger against open items at the end of fiscal 2026" with the ledger balance, the open items and their difference.

```m
    #"Added Custom" = Table.AddColumn(#"Expanded ARCredits", "OpenBalance", each Number.Round([GrandTotal] - (if [Applied] = null then 0 else [Applied]) - (if [Credited] = null then 0 else [Credited]), 2))
```

**Check:** 1,079 open invoices total $4,418,804.32 against $4,798,804.32 in the ledger, a difference of $380,000.00, the opening line. The 225 negative balances (-$220,131.88) are credit memos on paid invoices, refunded except 3 ($3,413.46) still in account `2060` at the year-end. Payables: 3,462 invoices total $4,781,095.54 against $6,237,466.66, a difference of $1,456,371.12: the opening payables, $2,096,371.12, less $640,000.00 on PI 3160 and 21692. **Watch for:** two silent errors. A subtraction that lets a null through returns null: only 6 open invoices ($6,413.86) keep a balance, because almost every invoice has no credit memo (20,302 of 20,914). The Payables step of the bridge includes account `2020`, so reconciling it to the open invoices adds -$1,020,992.06 of goods received and not invoiced and a difference of $2,477,363.18.

![A mock of the Reconciliations page of the model answer, where each difference sits beside the findings that explain it.](../figures/case-part-4/IF-C4-5-A.pdf)

### Part 3: Cutoff and aging

**Step 3. Compare billing with the invoices dated in each year.** Add a **Table** titled "Billing by invoice date against the ledger" with Year, billing by invoice date, billing in the ledger and the difference.

**Check:** the differences are 2024 $791.35; 2025 $4,119.16; 2026 -$4,910.51. Invoices dated in one year and posted on 1 January of the next explain them; only SI-2026-013742 shipped in 2025 (Chapter 6's cutoff error), so for the others the ledger is right and the dates are wrong.

**Step 4. Age the payables.** Add `Bucket` and `MovedToNotes` columns in APInvoices and a **Table** titled "Open payables aged, without the invoices moved to notes".

```m
    #"Added Custom4" = Table.AddColumn(#"Changed Type5", "MovedToNotes", each List.Contains({3160, 21692}, [PurchaseInvoiceID]))
```

**Check:** $2,089,989.68 is past due with the two note invoices and $1,449,989.68 of $4,141,095.54 (35.0%) without them. **Watch for:** the invoice date in place of the received date. The ledger posts supplier invoices on their received date, which makes no difference at the current year-end but moves $3,266.27 (ASV0050-2025-040073) at the end of 2025.

### Part 4: Sales tax

**Step 5. Test account `2050`.** Add a **Matrix** titled "Account 2050 by source and year" with SourceDocumentType on **Rows**, Year on **Columns** and the credits and debits as **Values**.

**Check:** credits come only from SalesInvoice ($1,787,832.54, $1,923,180.10, $1,948,415.82, equal to the invoices' TaxAmount) and debits only from CreditMemo; no payment or journal entry ever posts to it, leaving $5,620,840.66. The records show no remittance; the sales tax returns filed, the tax authority's account, the bank statements and a bank reconciliation would show whether it was remitted.

### Part 5: Findings and tests

**Step 6. Record the findings and test them.**

a. Choose **Home > Enter data** and type the table below as `Findings`, with Account, Finding, Amount, Disposition and Reconciles.
b. Add the measures and Tests 4 and 5 in **DAX query view**.

| Account | Finding | Amount | Disposition | Reconciles |
|---|---|---:|---|---|
| 1020 | Opening receivables with no invoice (JE-2024-000001) | $380,000.00 | Follow up | Receivables |
| 2010 | Opening payables with no invoice (JE-2024-000001) | $2,096,371.12 | Follow up | Payables |
| 2010 | Invoices moved to notes payable still open in the subledger (PI 3160 and 21692); close them against the notes | -$640,000.00 | Expected | Payables |
| 2050 | No remittance of the sales tax recorded | $5,620,840.66 | Follow up |  |
| 2110 | Current portion of the notes classified as long-term (due 2027) | $147,503.76 | Misstatement |  |
| 1010 and 2010 | Supplier payments posted after Data Through | $271,327.17 | Expected |  |
| 2030 | Payroll accrual not recorded at the year-end (Part III case) | $383,044.82 | Misstatement |  |

```dax
Payables Findings = CALCULATE ( [Findings Amount], Findings[Reconciles] = "Payables" )

Unexplained Payables = [Payables Difference] - [Payables Findings]
```

**Check:** both differences equal their findings to the cent, and in Test 5 the 4 quarters after Data Through show no value. The dispositions follow Chapter 8: expected, follow up, or a misstatement to report. **Watch for:** the note invoices entered as +$640,000.00. The payables findings read $2,736,371.12 against $1,456,371.12, and Test 4 shows -$1,280,000.00 unexplained.

![The two reconciliations as one picture, so students see that each difference is a short list of recorded items.](../figures/case-part-4/IF-C4-5-B.pdf)

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax
EVALUATE
ROW (
    "Receivables difference", ROUND ( CALCULATE ( [Receivables Difference], 'Date'[Year] = 2026 ), 2 ),
    "Unexplained receivables", ROUND ( CALCULATE ( [Unexplained Receivables], 'Date'[Year] = 2026 ), 2 ),
    "Payables difference", ROUND ( CALCULATE ( [Payables Difference], 'Date'[Year] = 2026 ), 2 ),
    "Unexplained payables", ROUND ( CALCULATE ( [Unexplained Payables], 'Date'[Year] = 2026 ), 2 ),
    "Sales tax debits", [Sales Tax Debits] - CALCULATE ( [Sales Tax Debits], GLEntry[SourceDocumentType] = "CreditMemo" )
)
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Receivables difference; payables difference | $380,000.00; $1,456,371.12 | 2 |
| Past due without the notes; share | $1,449,989.68; 35.0% | 4 |
| Sales tax payable; debits to it other than credit memos | $5,620,840.66; none | 5 |
| Rows after Data Through; their amount | 526; $271,327.17 | 6 |

> **Instructor notes, Requirement 5:** balances at 2026-12-31 by source: 1020 SalesInvoice 92,727,541.64, CashReceiptApplication -87,896,623.29, CreditMemo -412,114.03, JournalEntry 380,000.00 (4,798,804.32); 1045 GoodsReceipt 38,891,819.55, MaterialIssue -30,727,191.33, JournalEntry 3,587,025.70 (11,751,653.92); 1040 JournalEntry 4,111,795.76, GoodsReceipt 13,295,060.67, ProductionCompletion 40,099,313.03, SalesReturn 325,840.19, Shipment -45,662,307.91 (12,169,701.74); 2010 PurchaseInvoice -56,461,312.87, DisbursementPayment +51,680,217.33, JournalEntry -1,456,371.12 (-2,096,371.12 opening + 360,000 + 280,000 moved to notes), -6,237,466.66; 2020 GoodsReceipt -53,336,880.22, PurchaseInvoice +52,315,888.16 (-1,020,992.06, Chapter 12); 2050 SalesInvoice -5,659,428.46, CreditMemo +38,587.80. Open items: receivables 1,079 invoices, 4,418,804.32 (positive balances; 225 negative balances, -220,131.88, are credit memos on paid invoices, credited to 2060 and refunded, except 3 (3,413.46) not yet refunded at the year-end); difference 380,000.00, the opening line of JE-2024-000001. The same rebuild at 2024-12-31 and 2025-12-31 differs by 379,208.65 and 375,089.49, the cutoff invoices below. Payables: 3,462 invoices received and unpaid at 2026-12-31, 4,781,095.54; difference 1,456,371.12 = opening payables 2,096,371.12 less the 640,000.00 of PI 3160 and PI 21692, which the ledger moved to notes payable but the subledger still shows open (past due since 2024-07-30 and 2026-01-26). Aging: past due 2,089,989.68 with them, 1,449,989.68 of 4,141,095.54 (35.0%) without them. Reconcile payables on ReceivedDate, as the ledger posts them; on InvoiceDate, 2025-12-31 differs by ASV0050-2025-040073 (3,266.27). Billing by invoice date less the ledger: +791.35 (2024; SI-2025-006733 to 006735, dated November-December 2024, posted 2025-01-01), +4,119.16 (2025), -4,910.51 (2026; SI-2026-013741 to 013743, posted 2026-01-01); only SI-2026-013742 shipped in 2025 (Chapter 6's cutoff error), and the other dates are wrong, not the ledger. Sales tax: credits only from SalesInvoice (1,787,832.54 / 1,923,180.10 / 1,948,415.82, equal to the invoices' TaxAmount), debits only from CreditMemo; no payment and no journal entry ever posts to 2050. Evidence outside the database: the sales tax returns filed, the tax authority's account, the bank statements, and a bank reconciliation. Findings: 1020 opening receivables with no invoice, 380,000.00, follow up; 2010 opening payables with no invoice, 2,096,371.12, follow up; 2010 note invoices still open in the subledger, 640,000.00, expected, close them against the notes; 2050 no remittance recorded, 5,620,840.66, follow up; 2110 current portion classified as long-term, 147,503.76, misstatement; 1010 and 2010 supplier payments after Data Through, 271,327.17, expected. The Part III case's unrecorded payroll accrual at 2026-12-31 (383,044.82) belongs in the same list. Tests: both differences equal their findings to the cent, the bridge equals the change in cash in 2025 and 2026, 526 rows fall after Data Through, and every measure is blank in 2027.

## What a strong answer says

- **Roll-forward.** The journal-entry parts are the opening balances and the reclassifications; everything else comes from a subledger document.
- **Reconciliations.** Each difference equals its recorded items to the cent, with a disposition in Chapter 8's terms.
- **Cutoff.** The billing differences are invoices posted a year later; only one shipped in the earlier year.
- **Sales tax.** Posted, never remitted in the records, with the outside evidence named; the wording is "no remittance is recorded", not "unpaid" or "withheld".

A strong submission ties the findings to Tests 4 and 5. A weak one lists the differences without recording them.

## Common mistakes and how to respond

- **A null in the open balance.** *Symptom:* $6,413.86 of open receivables. *Response:* ask what a subtraction with a null returns.
- **Payables with `2020`.** *Symptom:* a difference of $2,477,363.18. *Response:* ask what account `2020` holds.
- **Sign of the notes finding.** *Symptom:* -$1,280,000.00 unexplained. *Response:* ask which way the invoices move the difference.
- **Notes left in the aging.** *Symptom:* $2,089,989.68 past due. *Response:* ask which invoices the ledger already moved.
- **Accusing wording.** *Symptom:* a finding that says someone failed to remit. *Response:* ask what the ledger shows and what it cannot.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Roll-forward | 15 | Six accounts by source; unsupported parts named | Balances without the reading |
| Reconciliations | 30 | Both differences explained to the cent | One reconciled |
| Cutoff and aging | 20 | Billing differences explained; aging without notes | Differences without the cause |
| Sales tax | 15 | Posts and non-posts; outside evidence | Balance only |
| Findings and tests | 20 | Table with dispositions; Tests 4 and 5 agree | Findings without tests |

## Extensions and discussion questions

- Add the payroll accrual of the Part III case to the findings and say which difference it explains.
- Reconcile the same two accounts at the end of 2025 and explain why the differences move.
- Discuss: which of these findings would you tell the committee first, and in what words?
