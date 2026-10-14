# Requirement 2: Reconcile each population to the ledger (Chapters 8 and 12)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 2 |
| Perspective | Auditing |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 120 minutes |
| Solution file | Chapter19-capstone-sql.zip: Credits.sql, the queries headed Requirement 2 (tests G1 to G9); Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Reconciliation (the same reconciliations, in formulas, for the report's appendix) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Every later test assumes that the populations are complete, and Requirement 1's anti-joins cannot show that a document was never made. A reconciliation can: each document population is totaled by year from its own table and from the ledger, and the two sides must agree to the cent. Two-sided totals by year, without the closes, are a query. The analytics type is descriptive. The requirement also teaches the hub account: 2060 passes tens of millions a year and ends each year with a few thousand, so it must be reconciled flow by flow, and its balance named item by item.

Students can reconcile credits, returns, refunds, clawbacks, receipts and applications to the accounts they post to (Part 1), roll the hub forward and name its items, reconcile commissions payable (Part 2), and state what was excluded and why (Part 3).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Reporting and Control (financial recordkeeping, internal control); IFAC IES 2 (f); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** The same as Requirement 1. Credits Audit.xlsx is needed for the appendix version.
- **Data conditions.** Documents are dated by their own date and the ledger by posting date, which agree by year here. The year-end closes post to `4060` and `6290` under the source type JournalEntry, so a filter on the credit's source type leaves them out and a filter on the account alone does not. Some credits post to receivables and to customer deposits (`2060`) both. 3 credits are still in status Issued.
- **Verify first.** Run G1 to G9 on a copy: every difference column is zero in every year.

## How to run it

Pairs, about 120 minutes: 30 for G1 to G5, 30 for G6 and G7, 20 for G8 and G9, 20 for the exclusions and the written statement, 20 for the appendix. The routine for every query: type it at the end of Credits.sql under its two comment lines, select it, choose **Execute all/selected SQL**, read the result. Hold back the source-type filter until a student's 4060 total looks wrong. **Collect** Credits.sql and the Reconciliation sheet.

## Step-by-step solution

### Part 1: The five populations (tests G1 to G5)

**Step 1. Reconcile the credits (G1).** One CTE totals the credits by the year of their own date. The other totals the ledger rows of the credit memos, so the closes stay out.

```sql
SUM(CASE WHEN a.AccountNumber = 4060 THEN gl.Debit ELSE 0 END)
            AS Dr4060,
        SUM(CASE WHEN a.AccountNumber = 4050 THEN gl.Debit ELSE 0 END)
            AS Dr4050,
        SUM(CASE WHEN a.AccountNumber = 2050 THEN gl.Debit ELSE 0 END)
            AS Dr2050,
        SUM(CASE WHEN a.AccountNumber = 1020 THEN gl.Credit ELSE 0 END)
            AS Cr1020,
        SUM(CASE WHEN a.AccountNumber = 2060 THEN gl.Credit ELSE 0 END)
            AS Cr2060
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType = 'CreditMemo'
```

**Check:** 3 rows, both difference columns zero. The SubTotal equals `4060` (145,655.35, 201,104.38, 242,764.56 by year), freight equals `4050`, tax equals `2050`, and the GrandTotal equals `1020` plus `2060`. **Watch for:**

- A GrandTotal tied to `1020` alone: the difference is the part posted to `2060`, $220,131.88 in all.
- `4060` read by account alone, as debits less credits over every source: zero in every year, because the close credits it back.

**Step 2. Reconcile the returns (G2).** The return lines at standard cost against the debits to `1040` and the credits to the four cost of goods sold accounts. **Check:** 3 rows; the cost is $325,840.19 over the three years. **Watch for:** tying the cost to `5010` alone, which leaves $42,102.68 in the last year.

**Step 3. Reconcile the refunds and the clawbacks (G3, G4).** Refunds against the credits to cash (`1010`) and the debits to `2060`; clawbacks against the debits to `2034` and the credits to `6290`, with the year's accruals and payments beside them. **Check:** 3 rows each; refunds total $45,028.75, $86,581.85, $85,107.82 and clawbacks $2,694.49, $3,768.06, $4,369.54. **Watch for:** every credit to `6290`, whatever its source. It reads $521,989.10 in the first year, the year's accruals, because the close credits the expense account for its net cost.

**Step 4. Reconcile the receipts and the applications (G5).** Receipts against the debits to cash and the credits to `2060`; applications against the debits to `2060` and the credits to `1020`. **Check:** 3 rows; receipts equal applications each year ($24,574,608.36, $31,633,933.20, $31,688,081.73).

### Part 2: The hub and the payable (tests G6 to G8)

**Step 5. Roll `2060` forward (G6).** Flows by source document, an opening and a closing balance from a running sum.

```sql
ROUND(SUM(NetChange) OVER (ORDER BY FiscalYear) - NetChange, 2)
        AS Opening,
    ROUND(Receipts, 2) AS Receipts, ROUND(Credits, 2) AS Credits,
    ROUND(Applications, 2) AS Applications, ROUND(Refunds, 2) AS Refunds,
    ROUND(Other, 2) AS Other,
    ROUND(SUM(NetChange) OVER (ORDER BY FiscalYear), 2) AS Closing
```

**Check:** 3 rows; the closing balances are $3,105.75, $1,008.67 and $3,413.46, the Other column is zero, and the last year's receipts alone are $31,688,081.73. A balance that small hides large flows, so each flow ties in Steps 1 to 4.

![A mock of the roll-forward of account 2060 in the Reconciliation worksheet, the picture of a hub account.](../figures/chapter-19-customer-credits-audit/IF-19-2-A.pdf)

**Step 6. Name the items in each balance (G7).** The credits' postings to `2060` less the refunds dated by each year-end, kept when more than half a cent is left.

```sql
WHERE p.Posted - COALESCE(rd.Refunded, 0) > 0.005
ORDER BY p.FiscalYear, cm.CreditMemoNumber
```

**Check:** 8 rows: 2 credits at the first year-end, 3 at the second, 3 at the last, which equal the balances. **Watch for:** today's status. The credits in status Issued are 3 items, $3,413.46, and explain only the last balance; the earlier credits were refunded after their year-end, so the balance must be read as of the date.

**Step 7. Reconcile `2034` (G8).** The balance at the last year-end against the accruals, less the payments and the clawbacks. **Check:** one row, balance $48,858.55; 18 clawbacks are not yet netted in a payment. **Watch for:** leaving out the clawbacks: a difference of $10,832.09.

### Part 3: What was excluded (test G9)

**Step 8. List the exclusions and say why.**

```sql
-- Requirement 2, test G9: what the reconciliations leave out: the year-end closes on 4060 and 6290
-- Population: the closes' rows on the two accounts; expected: one row a year on each
SELECT a.AccountNumber, je.EntryNumber, je.PostingDate,
    ROUND(SUM(gl.Debit), 2) AS Debits, ROUND(SUM(gl.Credit), 2) AS Credits
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    INNER JOIN JournalEntry AS je ON je.EntryNumber = gl.VoucherNumber
WHERE a.AccountNumber IN (4060, 6290)
    AND je.EntryType LIKE 'Year-End Close%'
GROUP BY a.AccountNumber, je.EntryNumber, je.PostingDate
ORDER BY a.AccountNumber, je.PostingDate;
```

**Check:** 6 rows, one close a year on each account (`4060`: $589,524.29; `6290`: $1,650,773.32). The statement names the six closing entries, which move the year's result to equity, and the ledger rows after the last year-end, which hold supplier payments only.

**Step 9. Build the appendix version.** The Reconciliation sheet repeats each test as formulas on the Ledger Table: a total from the document Table, one from the ledger, and their difference.

```
=SUMIFS(Ledger[Debit],Ledger[AccountNumber],4060,Ledger[SourceDocumentType],"CreditMemo",Ledger[FiscalYear],C$4,Ledger[IsYearEndClose],FALSE)
=C7-C8
```

**Watch for:** a difference such as `8.6e-08` in a cell, a floating-point residue; `IF(x=0, ...)` calls it an exception, so test `ABS(x)<0.005`.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Credits by year; SubTotal equal to `4060` | 158 / 232 / 222; $589,524.29 | 1 |
| Returns at standard; refunds; clawbacks | $325,840.19; $216,718.42; $10,832.09 | 2, 3 |
| Balance of `2060` at each year-end | $3,105.75; $1,008.67; $3,413.46 | 5 |
| Balance of `2034`, last year-end | $48,858.55 | 7 |
| Closes excluded | 3 on `4060`, 3 on `6290` | 8 |

> **Instructor notes, Requirement 2 (2024 / 2025 / 2026, all to the cent):** credits 158 / 232 / 222; SubTotal = 4060 145,655.35 / 201,104.38 / 242,764.56 (589,524.29); freight = 4050 1,227.26 / 1,109.93 / 1,796.63; tax = 2050 9,547.39 / 13,143.88 / 15,896.53 (38,587.80); GrandTotal 156,430.00 / 215,358.19 / 260,457.72 = Cr 1020 108,295.50 / 130,873.42 / 172,945.11 + Cr 2060 48,134.50 / 84,484.77 / 87,512.61. Returns at standard = 1040 76,390.25 / 111,321.12 / 138,128.82 (325,840.19); COGS credits 5010 40,502.86 / 73,787.18 / 96,026.14, 5020 16,781.43 / 17,985.54 / 25,386.87, 5030 13,125.13 / 12,655.71 / 11,366.42, 5040 5,980.83 / 6,892.69 / 5,349.39. Refunds 55 / 84 / 83 = 45,028.75 / 86,581.85 / 85,107.82 to 1010 and 2060. Clawbacks 2,694.49 / 3,768.06 / 4,369.54 to 2034 and 6290 (accruals 521,989.10 / 568,898.84 / 570,717.47; payments 470,066.75 / 566,286.93 / 565,561.09). Receipts = applications = 24,574,608.36 / 31,633,933.20 / 31,688,081.73, Dr 1010 and Cr 1020. 2060 at the year-ends 3,105.75 (CM-2024-000147 2,641.08; CM-2024-000158 464.67) / 1,008.67 (CM-2025-000329, -000375, -000376) / 3,413.46 (Issued CM-2026-000583 1,503.06, -000605 912.97, -000607 997.43). 2034 at 2026-12-31 48,858.55. Excluded: the closes on 4060 (3 rows, 589,524.29) and 6290 (3 rows).

## What a strong answer says

- **Every population ties to the cent, in every year, from both sides,** and the answer says which date each side uses.
- **The hub is reconciled flow by flow,** and each year-end balance is named by credit.
- **The exclusions are stated and justified:** the closes, and the rows after the last year-end.
- **A tie is evidence of completeness, not of correctness:** the amounts are tested in Requirement 7.

A weak answer reconciles totals over three years at once, ties the balance alone, or leaves the closes in.

## Common mistakes and how to respond

- **GrandTotal against `1020`.** *Symptom:* a yearly difference equal to the part posted to `2060`. *Response:* ask which accounts a credit on a paid invoice can post to.
- **`4060` by account alone.** *Symptom:* zero in each year. *Response:* ask which entry credits the account at the year-end.
- **`6290` from every source.** *Symptom:* $521,989.10 against $2,694.49. *Response:* ask what the close does to an expense account.
- **Status instead of date.** *Symptom:* 3 items, and balances left unexplained. *Response:* ask what the status was at the year-end.
- **Floating residue.** *Symptom:* a difference flagged in the workbook. *Response:* round, or test against half a cent.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Five populations (G1 to G5) | 35 | Each ties by year from both sides, closes out | Some tie, or only in total |
| The hub (G6, G7) | 25 | Flows and balances, items named by year-end | Balance only |
| Commissions payable (G8) | 10 | Accruals, payments and clawbacks | Without clawbacks |
| Exclusions (G9) | 15 | Closes and later rows named, with reasons | Closes only |
| Appendix | 15 | Formulas tie, differences rounded | Pasted values with no tie |

## Extensions and discussion questions

- Reconcile the refunds by the month of the refund and say where clearing dates would change the answer.
- Discuss: the books reconcile. What has been shown, and what has not?
- Discuss: why is the hub's balance the wrong place to look for an error?
