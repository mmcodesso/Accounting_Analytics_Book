# Requirement 4: Test the controls on every document (Chapters 10 to 12)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 4 |
| Perspective | Auditing |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 240 minutes |
| Solution file | Chapter19-capstone-sql.zip: Credits.sql, the queries headed Requirement 4 (tests T1 to T12, T10 is the export RefundFlags.csv); Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheets Tests and RefundFlags (the same results by year, as live flags and as pasted values) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This is the heart of the audit's test of controls. Each test joins a document to the people who handled it and to the cash on the invoice behind it, over the whole population, so no sampling risk remains. A query fits because every test repeats exactly and states its population and expected result in two comment lines, as Audit.sql did in Chapter 12. The analytics type is diagnostic. The requirement also trains the definition habit: the records hold dates without times, so each test says which date it uses and as of when.

Students can test authority, employment and separation of duties over a population (Part 1), define and test timing against the payments on an invoice (Part 2), test completeness and accuracy of the clawbacks, and combine the exceptions and export the flags (Part 3).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls) and ISC M2 (tests of internal controls, logical access and change management); IMA Reporting and Control (internal control); IFAC IES 2 (f) and (g); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite and Credits.sql, with the results of Requirements 1 and 2 behind it.
- **Data conditions.** MaxApprovalAmount is a general limit, not a delegation of authority. An invoice can have several receipts and applications on different dates. Neither the credit memo nor the refund records a preparer. A credit on a paid invoice posts to `2060`, which is how a refund can precede the customer's payment.
- **Verify first.** Run T1 to T12: each returns in a fraction of a second, T2 returns no rows and T4 three zeros.

## How to run it

Pairs, about 240 minutes: 40 for authority and employment, 50 for separation of duties, 60 for timing and the past-due balance, 30 for the clawbacks, 30 for the list and the export, 30 to write each definition. The routine for every query: type it under its two comment lines, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the definition of "before the payment" until students have a count, then ask which date they used. **Collect** Credits.sql and RefundFlags.csv.

## Step-by-step solution

### Part 1: Authority, people and cash

**Step 1. Test authority and employment (T1, T2).** Credits and refunds are stacked in one CTE and each amount is compared with its approver's limit.

```sql
SUM(CASE WHEN ap.Amount > COALESCE(e.MaxApprovalAmount, 0)
        THEN 1 ELSE 0 END) AS AboveLimit,
    ROUND(SUM(CASE WHEN ap.Amount > COALESCE(e.MaxApprovalAmount, 0)
        THEN ap.Amount ELSE 0 END), 2) AS AboveLimitAmount
```

**Check:** 5 rows. Credits above the limit: 414 ($421,606.55), all approved by customer service representatives with a limit of 0; the manager's limit of 25,000 is never exceeded. Refunds above the limit: 163 ($145,938.94), by Staff Accountants and Administrative Specialists; the 59 of the Accounting Manager are within it. T2, every document against its person's hire and termination dates, returns no rows. **Watch for:** COALESCE. Every approver has a limit today (0 blanks), so it changes nothing, but a blank limit would make the comparison false and hide every exception.

**Step 2. Test separation of duties (T3 to T5).** For each credit, did its approver apply, or record, cash on the credited invoice?

```sql
MAX(CASE WHEN cra.AppliedByEmployeeID = cm.ApprovedByEmployeeID
            THEN 1 ELSE 0 END) AS AppliedCash,
        MAX(CASE WHEN cra.AppliedByEmployeeID = cm.ApprovedByEmployeeID
                AND cra.ApplicationDate <= cm.CreditMemoDate
            THEN 1 ELSE 0 END) AS AppliedByCreditDate,
        MAX(CASE WHEN cr.RecordedByEmployeeID = cm.ApprovedByEmployeeID
            THEN 1 ELSE 0 END) AS RecordedCash
    FROM CreditMemo AS cm
        INNER JOIN CashReceiptApplication AS cra
            ON cra.SalesInvoiceID = cm.OriginalSalesInvoiceID
        INNER JOIN CashReceipt AS cr ON cr.CashReceiptID = cra.CashReceiptID
    GROUP BY cm.CreditMemoID
```

**Check:** 356 rows of credits whose approver recorded or applied the cash; the applied-only subset is 206 credits ($214,824.39), 44 of them on or before the credit date, and the register of Requirement 10 uses it. State which you use. T4 is one row of zeros: no refund approved by the credit's approver, no return received by it, none received outside the warehouse. **Watch for:** counting the joined rows. 224 rows describe 206 credits.

T5 asks whom GLEntry.CreatedByEmployeeID names. **Check:** the approver on all 1,988 credit rows and 444 refund rows, and one person on all 74,443 sales invoice rows. The preparer cannot be tested, and the answer says why. Reading the column as the preparer says that every credit approved itself.

### Part 2: Timing, balances and method

**Step 3. Define and test "refunded before the payment" (T6, T7).** The refund date against the last application of payments to the credited invoice, and the last receipt beside it.

```sql
WITH LastPayment AS (
    SELECT SalesInvoiceID, MAX(ApplicationDate) AS LastPaymentDate
    FROM CashReceiptApplication
    GROUP BY SalesInvoiceID
),
LastReceipt AS (
    SELECT cra.SalesInvoiceID, MAX(cr.ReceiptDate) AS LastReceiptDate
    FROM CashReceiptApplication AS cra
        INNER JOIN CashReceipt AS cr ON cr.CashReceiptID = cra.CashReceiptID
    GROUP BY cra.SalesInvoiceID
```

The test keeps the refunds with `lp.LastPaymentDate > rf.RefundDate`.

![The dates around one refund, the picture behind the definition of a refund paid before the customer's payment.](../figures/chapter-19-customer-credits-audit/IF-19-4-A.pdf)

**Check:** 58 refunds ($71,306.30), 10, 29 and 19 by year; by the receipts' dates 51 ($67,833.13), accepted when stated; 41 before any application. T7 gives the cause: 225 credits post a part to `2060`, 106 of them when nothing had been paid. **Watch for:** `>=`, which flags 64. The order within a day is unknown for the 7 refunds dated the day of the last receipt, and no table shows when a payment cleared the bank.

**Step 4. Test the past-due balance on the refund date (T10).** The flags query carries the as-of rule: only applications and credits dated by the refund date reduce each invoice.

```sql
DueInvoices AS (
    SELECT rf.CustomerRefundID, rf.RefundDate, si.SalesInvoiceID,
        si.GrandTotal
    FROM CustomerRefund AS rf
        INNER JOIN SalesInvoice AS si
            ON si.CustomerID = rf.CustomerID
            AND si.InvoiceDate <= rf.RefundDate
            AND si.DueDate < rf.RefundDate
),
PaidThen AS (
    SELECT di.CustomerRefundID, di.SalesInvoiceID,
        SUM(cra.AppliedAmount) AS Paid
    FROM DueInvoices AS di
        INNER JOIN CashReceiptApplication AS cra
            ON cra.SalesInvoiceID = di.SalesInvoiceID
            AND cra.ApplicationDate <= di.RefundDate
    GROUP BY di.CustomerRefundID, di.SalesInvoiceID
```

**Check:** 132 refunds with a past-due balance, 124 past due by at least the refund. **Watch for:** today's balances. No invoice that was past due on a refund date is still open, so they find 0 refunds. The method flag (no receipt on the invoice used the refund's method) finds 153; a method chosen at random among four would mismatch about as often, so it is an anomaly to follow up, not a rule.

**Step 5. Test the clawbacks and the refunds (T8, T9).** T8 finds 3 clawbacks whose amount differs by a cent from SQLite's ROUND of base times rate (SCAJ-2024-000128, SCAJ-2025-000347, -000368), exact half-cent products stored just below the half in binary floating point: roundings, not errors. T9 finds 222 refunds on 222 credits, each equal to the credit's part posted to `2060` (222). **Watch for:** a refund compared with the credit's total: 28 differ, the credits that posted to both accounts.

### Part 3: Combine and export

**Step 6. Combine the exceptions and export the flags (T11, T10).** UNION ALL stacks the four tests under a TestID.

```sql
SELECT CAST(strftime('%Y', DocumentDate) AS INTEGER) AS FiscalYear,
    TestID, DocumentNumber, DocumentDate, ROUND(Amount, 2) AS Amount
FROM Exceptions
ORDER BY FiscalYear, TestID, DocumentNumber
```

**Check:** 841 rows, 217, 324 and 300 by year. Run T10, choose **Save the results view**, then Export to CSV, and name the file RefundFlags.csv: 222 rows, the file Requirement 5 loads.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Credits above limit; refunds above limit | 414; 163 | 1 |
| Credits whose approver applied the cash | 206 | 2 |
| Refunds before the last application; by receipt date | 58; 51 | 3 |
| Past due on the refund date; at least the refund | 132; 124 | 4 |
| Method mismatches; rows of the combined list | 153; 841 | 4, 6 |

> **Instructor notes, Requirement 4 (three years; fiscal 2026 in brackets):** credits above the approver's recorded general limit (MaxApprovalAmount) 414 / 421,606.55 (104 / 157 / 153 a year) \[153 / 172,307.40\], all approved by customer service representatives with a limit of 0; the manager's 25,000 is never exceeded; whether a delegation of authority for credits sets other limits lies outside the records. Credit approver also applied cash to the credited invoice: 206 / 214,824.39 (60 / 77 / 69) \[69 / 68,514.82\]; on or before the credit date 44 / 42,044.83 \[14\]; recorded or applied 356 / 376,965.42. Refunds above the limit 163 / 145,938.94 (Staff Accountants 79 / 71,555.36, Administrative Specialists 84 / 74,383.58; 43 / 61 / 59 a year) \[59 / 56,131.84\]; the Accounting Manager's 59 (70,779.48) are within limit. Refunds dated before the last application of the customer's payments to the credited invoice (the case's BeforePayment) 58 / 71,306.30 (10 / 29 / 19) \[19 / 24,893.21\]; before any application 41 / 36,034.57 \[14 / 16,670.59\]; 28 also before the invoice's due date; the last application came 1-19 days later (mean 5.6). By the receipts' own dates, an accepted definition when stated: 51 / 67,833.13 (9 / 24 / 18) \[18 / 24,094.64\], 37 / 34,662.75 before any receipt; the 7 refunds the two definitions part on (RF-2024-000011, RF-2025-000066, -000081, -000086, -000087, -000136, RF-2026-000167; 3,473.17) are dated the day of the invoice's last receipt, applied 1-2 days later, and the records hold no times, so their order that day is unknown; neither date shows when the cash cleared the bank. An answer that compares each refund with the credit balance the cash received by the refund date supports (the invoice's receipts and credits by then, less its total and earlier refunds) flags the same 51, by 61,107.80 in all: a timing exposure, not a loss. Cause: credits are split between 1020 and 2060 by the invoice's final payments, so 106 of the 225 credits to 2060 were posted when nothing had been paid; this is how the records were produced, but the control does not check it. Past due at the refund date (as of the refund date: GrandTotal less applications and credits dated by then, DueDate before the refund date, each credit at its full amount, the balance after the return): 132 / 132,999.46; past due at least the refund 124 / 127,395.76 \[48 / 52,039.44\]; on the receivable as posted (only each credit's 1020 part) 29 balances differ and 133 refunds have a past-due balance, but the refunds past due by at least the refund are the same; label the basis, and whether a balance could be offset depends on the customer's terms and any dispute. Method mismatch 153 / 161,000.36 \[56 / 62,483.48\], against every receipt ever applied to the invoice (retrospective: 13 refunds, 13,060.05, match only on receipts dated after the refund): no customer pays by one method only, and a refund method chosen at random across four methods would mismatch about this often, so it is an anomaly to follow up, not a rule, and a different method does not show a different payee. Clean: employment dates; refund approver never the credit approver; returns always received in the warehouse; one refund per credit, equal to the credit's 2060 part (222 of 222); a clawback for every credit line (637), base = line total and rate = the accrual's; amount = base x rate rounded half up (SQLite's ROUND(base x rate, 2) gives a cent less on SCAJ-2024-000128, SCAJ-2025-000347, -000368, exact half-cent products stored just below the half in binary floating point); 619 clawbacks netted in later commission payments, 18 pending at the end of 2026. Optional design note: the Accounting Manager approved all 8 commission rates (whose recorded end date, 2026-12-31, is the end of the data), created all 27,933 accruals, and approved all 196 commission payments.

## What a strong answer says

- **Each test states its population and definition first:** which approver's limit, applied or recorded cash, application or receipt date, balances as of the refund date.
- **Clean results are reported:** employment, the refund approver never the credit approver, returns received in the warehouse, one refund per credit, the clawbacks complete.
- **Patterns are worded as what the records show.** The limit is a general one and the delegation is outside the database; a method mismatch is an anomaly, not a rule.
- **The preparer test is declared not testable,** with the reason.

A weak answer reports counts without definitions, or states a finding as what someone did.

## Common mistakes and how to respond

- **Joined rows counted.** *Symptom:* 224 for 206. *Response:* ask what one credit is.
- **`>=` for "before".** *Symptom:* 64 refunds. *Response:* ask what the records say about the order within a day.
- **Today's balances.** *Symptom:* 0 past-due refunds. *Response:* ask what the customer owed on the refund date.
- **The ledger's creator as preparer.** *Symptom:* every credit self-approved. *Response:* ask what the column says on the sales invoices.
- **Rounding as error.** *Symptom:* 3 wrong clawbacks. *Response:* ask which half-cent rule produced the stored cent.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Authority and employment (T1, T2) | 15 | Every credit and refund, the limit stated | Totals without job titles |
| Separation of duties (T3 to T5) | 20 | Cash by credit, definition stated, preparer not testable | Rows counted, no definition |
| Timing (T6, T7) | 25 | Dates defined, same-day case, the cause | One reading, no definition |
| Past due and method (T10) | 15 | As of the refund date; the method as an anomaly | Today's balances |
| Clawbacks and one refund per credit (T8, T9) | 10 | Completeness, accuracy, roundings explained | Counts only |
| List and export (T11, T10) | 15 | UNION ALL by year; the CSV opens in Requirement 5 | A list with no TestID |

## Extensions and discussion questions

- Test the Accounting Manager's share of approvals across the cycle and payroll (T12): 8 of 8 commission rates, 59 of 222 refunds.
- Discuss: the approver applied the cash and no false credit was found. Is that a deficiency?
