---
note: ch19.r4
uses: [ch19.g4]
title: Test the controls on every document (Chapters 10 to 12)
kind: requirement
number: '4'
unit: '19'
perspective: auditing
tool: sql
minutes: 240
solution: "Chapter19-capstone-sql.zip: Credits.sql, the queries headed Requirement 4 (tests T1 to T12, T10 is the export RefundFlags.csv); Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheets Tests and RefundFlags (the same results by year, as live flags and as pasted values)"
figures:
  - id: IF-19-4-A
    kind: diagram
    purpose: The dates around one refund, the picture behind the definition of a refund paid before the customer's payment.
    shows: "A time line for one invoice in three lanes: the invoice date and the due date, two receipts with the applications of those receipts a day or two after each, and the credit and the refund, with the refund date (the day of the last receipt) marked through the lanes. An enlarged strip of the days around the refund carries three brackets that name the three readings: the last application (the case's definition), the last receipt, and the same-day case in which the order is unknown because the records hold dates and not times. A note says that the bank clearing date is in no table."
    data: One refund of the BeforePayment test (T6) chosen from the refunds the two definitions part on, with its invoice, receipts and applications.
---
{% set g = ch19_g4 %}
# Requirement 4: Test the controls on every document (Chapters 10 to 12)

{{ header() }}

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

**Check:** {{ g.t1 }} rows. Credits above the limit: {{ cm_above.n }} (${{ cm_above.amt|money }}), all approved by {{ above_title }} with a limit of {{ above_limit }}; the manager's limit of {{ manager_limit|count }} is never exceeded. Refunds above the limit: {{ rf_above.n }} (${{ rf_above.amt|money }}), by {{ rf_groups[0][0] }} and {{ rf_groups[1][0] }}; the {{ within.n }} of the {{ within_title }} are within it. T2, every document against its person's hire and termination dates, returns no rows. **Watch for:** COALESCE. Every approver has a limit today ({{ g.null_limit }} blanks), so it changes nothing, but a blank limit would make the comparison false and hide every exception.

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

**Check:** {{ g.t3 }} rows of credits whose approver recorded or applied the cash; the applied-only subset is {{ cc.n }} credits (${{ cc.amt|money }}), {{ cc_early.n }} of them on or before the credit date, and the register of Requirement 10 uses it. State which you use. T4 is one row of zeros: no refund approved by the credit's approver, no return received by it, none received outside the warehouse. **Watch for:** counting the joined rows. {{ g.rows_applied }} rows describe {{ cc.n }} credits.

T5 asks whom GLEntry.CreatedByEmployeeID names. **Check:** the approver on all {{ g.prep_rows[0]|count }} credit rows and {{ g.prep_rows[1] }} refund rows, and one person on all {{ g.ceo_rows|count }} sales invoice rows. The preparer cannot be tested, and the answer says why. Reading the column as the preparer says that every credit approved itself.

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

{{ figure('IF-19-4-A') }}

**Check:** {{ before.n }} refunds (${{ before.amt|money }}), {{ before.years[0] }}, {{ before.years[1] }} and {{ before.years[2] }} by year; by the receipts' dates {{ rcpt.n }} (${{ rcpt.amt|money }}), accepted when stated; {{ nothing.n }} before any application. T7 gives the cause: {{ to_2060 }} credits post a part to `2060`, {{ unpaid_2060 }} of them when nothing had been paid. **Watch for:** `>=`, which flags {{ g.same_day }}. The order within a day is unknown for the {{ same.n }} refunds dated the day of the last receipt, and no table shows when a payment cleared the bank.

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

**Check:** {{ pd1.n }} refunds with a past-due balance, {{ pd2.n }} past due by at least the refund. **Watch for:** today's balances. No invoice that was past due on a refund date is still open, so they find {{ g.lifetime }} refunds. The method flag (no receipt on the invoice used the refund's method) finds {{ mism.n }}; a method chosen at random among {{ n_methods }} would mismatch about as often, so it is an anomaly to follow up, not a rule.

**Step 5. Test the clawbacks and the refunds (T8, T9).** T8 finds {{ g.t8 }} clawbacks whose amount differs by a cent from SQLite's ROUND of base times rate ({{ off|join(', ') }}), exact half-cent products stored just below the half in binary floating point: roundings, not errors. T9 finds {{ n_refunds }} refunds on {{ n_refunds }} credits, each equal to the credit's part posted to `2060` ({{ equal_2060 }}). **Watch for:** a refund compared with the credit's total: {{ g.vs_total }} differ, the credits that posted to both accounts.

### Part 3: Combine and export

**Step 6. Combine the exceptions and export the flags (T11, T10).** UNION ALL stacks the four tests under a TestID.

```sql
SELECT CAST(strftime('%Y', DocumentDate) AS INTEGER) AS FiscalYear,
    TestID, DocumentNumber, DocumentDate, ROUND(Amount, 2) AS Amount
FROM Exceptions
ORDER BY FiscalYear, TestID, DocumentNumber
```

**Check:** {{ g.t11 }} rows, {{ g.by_year[0] }}, {{ g.by_year[1] }} and {{ g.by_year[2] }} by year. Run T10, choose **Save the results view**, then Export to CSV, and name the file RefundFlags.csv: {{ g.t10 }} rows, the file Requirement 5 loads.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Credits above limit; refunds above limit | {{ cm_above.n }}; {{ rf_above.n }} | 1 |
| Credits whose approver applied the cash | {{ cc.n }} | 2 |
| Refunds before the last application; by receipt date | {{ before.n }}; {{ rcpt.n }} | 3 |
| Past due on the refund date; at least the refund | {{ pd1.n }}; {{ pd2.n }} | 4 |
| Method mismatches; rows of the combined list | {{ mism.n }}; {{ g.t11 }} | 4, 6 |

{{ expected() }}

## What a strong answer says

- **Each test states its population and definition first:** which approver's limit, applied or recorded cash, application or receipt date, balances as of the refund date.
- **Clean results are reported:** employment, the refund approver never the credit approver, returns received in the warehouse, one refund per credit, the clawbacks complete.
- **Patterns are worded as what the records show.** The limit is a general one and the delegation is outside the database; a method mismatch is an anomaly, not a rule.
- **The preparer test is declared not testable,** with the reason.

A weak answer reports counts without definitions, or states a finding as what someone did.

## Common mistakes and how to respond

- **Joined rows counted.** *Symptom:* {{ g.rows_applied }} for {{ cc.n }}. *Response:* ask what one credit is.
- **`>=` for "before".** *Symptom:* {{ g.same_day }} refunds. *Response:* ask what the records say about the order within a day.
- **Today's balances.** *Symptom:* {{ g.lifetime }} past-due refunds. *Response:* ask what the customer owed on the refund date.
- **The ledger's creator as preparer.** *Symptom:* every credit self-approved. *Response:* ask what the column says on the sales invoices.
- **Rounding as error.** *Symptom:* {{ g.t8 }} wrong clawbacks. *Response:* ask which half-cent rule produced the stored cent.

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

- Test the Accounting Manager's share of approvals across the cycle and payroll (T12): {{ g.am['Commission rates approved'][1] }} of {{ g.am['Commission rates approved'][0] }} commission rates, {{ g.am['Refunds approved'][1] }} of {{ g.am['Refunds approved'][0] }} refunds.
- Discuss: the approver applied the cash and no false credit was found. Is that a deficiency?
