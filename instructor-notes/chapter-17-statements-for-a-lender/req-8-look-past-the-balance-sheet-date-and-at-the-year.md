# Requirement 8: Look past the balance-sheet date and at the year ahead (Chapters 8 and 12)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 8 |
| Perspective | Auditing |
| Tools | More than one tool |
| Time | About 90 minutes |
| Solution file | Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 8; Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheet Later Events |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The statements must account for what happened after the year-end, up to the date they are available to be issued, and management must judge whether conditions raise substantial doubt about continuing as a going concern. The database can contribute to both and complete neither. The requirement teaches students to say what a partial extract contains, what it cannot contain, and what evidence outside the database the CFO still needs. The analytics type is diagnostic, with a prescriptive close: what the CFO must evaluate.

Students can profile an extract and state its limits (Part 1), search later payments for liabilities missing at the year-end (Part 2), list the events the CFO must evaluate (Part 3), and weigh going-concern conditions against their mitigating factors (Part 4).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures, and audit data analytics); IMA Reporting and Control (financial statement analysis); IFAC IES 2 (a) and IES 4 (a) (professional skepticism and judgment); AACSB A5 part 5.1 (technology integration: SQL).

## Before you assign

- **Files.** `LenderPackage.sql` and the workbook with Requirements 1 to 6 done; the Later Events worksheet reads the adjusted statements.
- **Data conditions.** GLEntry holds rows after the last fiscal year, all of SourceDocumentType DisbursementPayment; no PurchaseInvoice was received after the year-end; PayrollPeriod has pay dates in the extract's weeks but no PayrollRegister rows for them; DebtScheduleLine payments due in those weeks are Scheduled with no journal entry.
- **Verify first.** Every later row debits `2010` or credits `1010`.

## How to run it

Individual or pairs, about 90 minutes: 20 to profile and compare, 20 to search, 10 for the events, 25 for the conditions, 15 to write. Hold back the weeks the extract covers until a student reads the drop in payments as a change in behavior. **Collect** the queries, the Later Events worksheet and half a page on what the CFO needs.

![A mock of the search for unrecorded liabilities, the query whose empty answer is the finding.](../figures/chapter-17-statements-for-a-lender/IF-17-8-A.pdf)

## Step-by-step solution

### Part 1: Profile the records after the year-end

**Step 1. Profile the records dated after fiscal 2026.** Run one query over the later postings by source document type and account.

```sql
-- Requirement 8: the records dated after fiscal 2026
-- Population: GLEntry after 2026-12-31; expected: 526 supplier-payment rows, 1 January to 23 February 2027, debiting 2010 and crediting 1010
SELECT gl.SourceDocumentType, a.AccountNumber,
    COUNT(*) AS Postings,
    ROUND(SUM(gl.Debit), 2) AS Debits,
    ROUND(SUM(gl.Credit), 2) AS Credits,
    MIN(gl.PostingDate) AS FirstDate, MAX(gl.PostingDate) AS LastDate
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE gl.PostingDate > '2026-12-31'
GROUP BY gl.SourceDocumentType, a.AccountID, a.AccountNumber
ORDER BY a.AccountNumber;
```

**Check:** 526 ledger rows, all supplier payments, from 1 January to 23 February 2027, debiting `2010` and crediting `1010`, 263 payments in all.

**Step 2. Compare them with the same weeks of the year before.** Count the payments of 2026 from 1 January to the extract's last date, and the payables at the year-end that were due in those months.

```sql
-- Requirement 8: the same weeks of 2026, and the payables at 2026-12-31 due in the weeks the extract covers
-- Population: DisbursementPayment and PurchaseInvoice; expected: 2,530 payments, 3,040,077.15 in 2026; 2,665,014.91 due in January and February 2027
SELECT
    (SELECT COUNT(*)
     FROM DisbursementPayment
     WHERE PaymentDate BETWEEN '2026-01-01' AND '2026-02-23')
        AS PaymentsSameWeeks,
    (SELECT ROUND(SUM(Amount), 2)
     FROM DisbursementPayment
     WHERE PaymentDate BETWEEN '2026-01-01' AND '2026-02-23')
        AS AmountSameWeeks,
    (SELECT ROUND(SUM(pi.GrandTotal - COALESCE(
        (SELECT SUM(dp.Amount)
         FROM DisbursementPayment AS dp
         WHERE dp.PurchaseInvoiceID = pi.PurchaseInvoiceID
             AND dp.PaymentDate <= '2026-12-31'), 0)), 2)
     FROM PurchaseInvoice AS pi
     WHERE pi.ReceivedDate <= '2026-12-31'
         AND pi.DueDate BETWEEN '2027-01-01'
             AND date('2027-02-23', 'start of month', '+1 month',
                 '-1 day')) AS PayablesDue;
```

**Check:** 2,530 payments ($3,040,077.15) in the same weeks of 2026 against 263 ($271,327.17); payables due in January and February 2027, $2,665,014.91. **Watch for:** reading the drop to 9% of the year before as a change in payment behavior. The extract is incomplete, which Step 3 shows.

**Step 3. State what the extract cannot contain.** Pay dates and note payments in its weeks, with the records that exist for them:

```sql
-- Requirement 8: what the extract cannot contain, the pay dates and note payments it covers
-- Population: PayrollPeriod and DebtScheduleLine from 2027-01-01 to 2027-02-23; expected: pay periods 78, 79 with no registers; note payments on 2027-01-01, 01-04, 02-01, 02-02, all Scheduled
SELECT 'Pay period' AS Record, pp.PeriodNumber AS Reference,
    pp.PayDate AS DueDate, pp.Status,
    (SELECT COUNT(*)
     FROM PayrollRegister AS pr
     WHERE pr.PayrollPeriodID = pp.PayrollPeriodID) AS Recorded
FROM PayrollPeriod AS pp
WHERE pp.PayDate BETWEEN '2027-01-01' AND '2027-02-23'
UNION ALL
SELECT 'Note payment', da.AgreementNumber, dl.PaymentDate,
    dl.Status,
    CASE WHEN dl.JournalEntryID IS NULL THEN 0 ELSE 1 END
FROM DebtScheduleLine AS dl
    INNER JOIN DebtAgreement AS da
        ON da.DebtAgreementID = dl.DebtAgreementID
WHERE dl.PaymentDate BETWEEN '2027-01-01' AND '2027-02-23'
ORDER BY Record DESC, DueDate;
```

**Check:** pay periods 78 and 79, paid 2027-01-01 and 2027-01-05, have no registers, and the note payments due (2027-01-01, 01-04, 02-01, 02-02) are all Scheduled with no journal entry. The extract holds no payroll, no note payments, no sales and no receipts: it ends, it does not prove the company stopped paying.

### Part 2: The search for unrecorded liabilities

**Step 4. Search the later payments for invoices recorded late.** Group the payments by invoice and compare each invoice's received date with the year-end: an invoice received after it, for goods received before it, would be an unrecorded liability.

```sql
-- Requirement 8: the 2027 supplier payments and the invoices they paid, a search for unrecorded liabilities
-- Population: DisbursementPayment after 2026-12-31; expected: 263 payments, 271,327.17, 262 invoices of 78 suppliers received by 2026-12-31, 238 paid in full
WITH Paid AS (
    SELECT dp.PurchaseInvoiceID, COUNT(*) AS Payments,
        SUM(dp.Amount) AS Amount
    FROM DisbursementPayment AS dp
    WHERE dp.PaymentDate > '2026-12-31'
    GROUP BY dp.PurchaseInvoiceID
)
SELECT SUM(p.Payments) AS Payments, ROUND(SUM(p.Amount), 2) AS Amount,
    COUNT(*) AS Invoices,
    COUNT(DISTINCT pi.SupplierID) AS Suppliers,
    MIN(pi.ReceivedDate) AS FirstReceived,
    MAX(pi.ReceivedDate) AS LastReceived,
    SUM(CASE WHEN ABS(pi.GrandTotal - p.Amount) < 0.005
        THEN 1 ELSE 0 END) AS PaidInFull,
    (SELECT COUNT(*)
     FROM PurchaseInvoice
     WHERE ReceivedDate > '2026-12-31') AS ReceivedAfterYearEnd
FROM Paid AS p
    INNER JOIN PurchaseInvoice AS pi
        ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID;
```

**Check:** 263 payments ($271,327.17) settle 262 invoices of 78 suppliers, received in November to December 2026 and already in payables, 238 of them paid in full; no invoice was received after the year-end, so the search finds none. **Watch for:** reporting the $271,327.17 as unrecorded. It reduces payables the ledger already holds; the payments outnumber the invoices only because one invoice was paid in two parts.

### Part 3: Events the CFO must evaluate

**Step 5. List the events up to the date the statements are available to be issued.** The credit line itself, if it is obtained before then; the sales tax position; and anything the CFO learns about the opening balances that no document supports. The package must also disclose the date; the records cannot supply it.

**Check:** three events and a date, none of them in the records. **Watch for:** taking the ledger's last posting date, 23 February 2027, as that date. A balance at it reads cash of $8,170,928.63, $271,327.17 below the year-end's $8,442,255.80.

### Part 4: Going concern

**Step 6. Measure the conditions and the mitigating factors.** The Later Events worksheet takes them from the adjusted statements. Its formula for the payables due in the extract's months, and one query for the materials on hand against twelve months of issues:

```
=SUMPRODUCT((SupplierInvoices[ReceivedDate]<=YE_2026)*(SupplierInvoices[DueDate]>=DATE(2027,1,1))*(SupplierInvoices[DueDate]<=EOMONTH(AfterLast,0))*(SupplierInvoices[GrandTotal]-SupplierInvoices[PaidByYearEnd]))
```

```sql
-- Requirement 8: materials on hand at 2026-12-31 against twelve months of issues
-- Population: account 1045; expected: 11,751,653.92 on hand against 10,161,204.64 issued in 2026
SELECT
    (SELECT ROUND(SUM(gl.Debit - gl.Credit), 2)
     FROM GLEntry AS gl
         INNER JOIN Account AS a ON a.AccountID = gl.AccountID
     WHERE a.AccountNumber = 1045
         AND gl.PostingDate <= '2026-12-31') AS MaterialsOnHand,
    (SELECT ROUND(SUM(gl.Credit - gl.Debit), 2)
     FROM GLEntry AS gl
         INNER JOIN Account AS a ON a.AccountID = gl.AccountID
     WHERE a.AccountNumber = 1045
         AND gl.SourceDocumentType = 'MaterialIssue'
         AND gl.FiscalYear = 2026) AS IssuedInYear;
```

**Check:** cash net of sales tax payable $2,821,415.14; quick ratio 0.96, down from 1.28; operating cash flow -$807,189.75 against $3,975,026.14; inventories 64% of current assets, with materials ($11,751,653.92) above twelve months of issues ($10,161,204.64), about 13.9 months; $2,096,371.12 of opening payables unchanged for three years. Mitigating: profit, working capital of 23.4 million and debt of $389,304.68. **Watch for:** leading with the current ratio, 2.69, which hides the quick ratio.

**Step 7. State what the evaluation needs beyond the database.** The terms of the credit line, management's plans for the materials, and evidence on the sales tax and the opening payables. Conclude in two sentences: the ledger alone does not establish substantial doubt, but the sales tax and the opening payables could change that.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Later ledger rows; payments; amount | 526; 263; $271,327.17 | 1 |
| Payments in the same weeks of 2026 | 2,530; $3,040,077.15 | 2 |
| Invoices paid; suppliers; received after the year-end | 262; 78; none | 4 |
| Cash net of sales tax; quick ratio | $2,821,415.14; 0.96 | 6 |

> **Instructor notes, Requirement 8:** the 2027 records are 263 supplier payments, 271,327.17, from 1 January to 23 February 2027 (526 ledger rows, Dr 2010, Cr 1010), paying 262 invoices of 78 suppliers, all received from November to December 2026 and recorded in payables at the year-end (238 paid in full); no invoice was received after 2026, so no unrecorded liability is found. The same weeks of 2026 had 2,530 payments, 3,040,077.15; payables at 2026 due in January and February 2027 were 2,665,014.91. The extract has no payroll for periods 78-79 (pay dates 2027-01-01 and 2027-01-05), no note payments (due 2027-01-01, 01-04, 02-01, 02-02, all Scheduled), no December freight settlement, and no rent, sales, or receipts, so it is incomplete: do not read it as the company having stopped paying. Events to evaluate: the credit line itself if obtained before the statements are available to be issued, the sales tax position, and anything the CFO learns about the opening balances; the date the statements are available to be issued must be disclosed. Conditions: cash net of sales tax 2,821,415.14; quick ratio 0.96, down from 1.28; operating cash flow -807,189.75 against +3,975,026.14; inventories 64% of current assets, with materials (11,751,653.92) above twelve months of issues (10,161,204.64); 2,096,371.12 of opening payables unchanged for three years. Mitigating: profit, working capital of 23.4 million, and debt of only 389,304.68. Conclusion: the ledger alone does not establish substantial doubt, but the sales tax and the opening payables could change that, so the CFO's evaluation needs evidence from outside the database.

## What a strong answer says

- **Profile.** What the later records are, and what they cannot contain: payroll, note payments, sales and receipts.
- **Search.** No unrecorded liability found, stated as the result of this test only.
- **Events.** The credit line, the sales tax and the opening balances, and the disclosure of the date.
- **Going concern.** Conditions and mitigating factors both measured, a bounded conclusion and the evidence still needed.

A weak answer concludes either way from the ledger alone.

## Common mistakes and how to respond

- **Extract read as complete.** *Symptom:* "payments fell to 9%". *Response:* ask which payments the extract lacks.
- **Payments as unrecorded liabilities.** *Symptom:* $271,327.17 reported. *Response:* ask where the invoices stood at the year-end.
- **The ledger's last date as the issue date.** *Symptom:* cash of $8,170,928.63. *Response:* ask who decides when the statements are available.
- **The current ratio alone.** *Symptom:* 2.69 called comfortable. *Response:* ask what the inventories are and when they turn into cash.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Profile and comparison | 20 | Contents, same weeks, limits stated | Contents only |
| Search for unrecorded liabilities | 25 | Invoices by received date, result and its limit | Payments counted as liabilities |
| Events and the date | 15 | Three events, the date to be disclosed | Events without the date |
| Conditions and mitigating factors | 25 | Both measured from the adjusted statements | One side |
| Evidence needed and wording | 15 | Bounded conclusion, evidence named | Conclusion stated as fact |

## Extensions and discussion questions

- Repeat the conditions on the assumption that the sales tax is due within the year.
- Discuss: payables due in January and February were $2,665,014.91 and $271,327.17 was paid in the extract. What does the gap tell you, and what does it not?
- Discuss: what evidence would let the CFO conclude on going concern?
