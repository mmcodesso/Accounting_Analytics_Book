# Requirement 5: Classify, measure, and judge the adjustments (Chapters 4, 6, and 8)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 5 |
| Perspective | Financial accounting |
| Tools | More than one tool |
| Time | About 180 minutes |
| Solution file | Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheets Adjustments (the schedule, the AdjustmentLines Table, materiality and the passed items) and Working TB (the adjustments and adjusted balances); Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 5 (the receivables aging, the allowance, returns after the year-end, the current portion of the notes) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This requirement turns the measurements of Requirements 3 and 4 into numbered entries, decides the period each belongs to, and judges which to record and which to pass. The workbook suits it: a working trial balance keeps the recorded balances, the adjustments and the adjusted balances side by side, each traceable to its evidence. The analytics type is prescriptive.

Students can:

- write each adjustment's entries for both year-ends, with the effect on opening equity, on each year's income and on the balance sheet (Part 1);
- classify each as an error, a change in estimate or a reclassification, and assign it to a period (Parts 1 and 2);
- compute materiality and judge the adjustments individually and in aggregate, on size and on other grounds (Part 3).

**Competencies practiced.** CPA Evolution Core S2 M7 (materiality) and Core S1 M1 to M3; IMA Reporting and Control (financial statement preparation); IFAC IES 2 (a) and IES 4 (a) (professional skepticism and judgment); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** The workbook with Requirements 1, 3 and 4 done, and `LenderPackage.sql` for the aging, returns and notes queries.
- **Data conditions.** No tax account exists, so income before income taxes is recorded net income. The shareholders received statements for 2025, so correcting 2025 is a restatement. Only the first note existed at the end of 2025.
- **Verify first.** Each entry balances, and no line touches cash.

## How to run it

Individual or pairs, about 180 minutes: 60 for the schedule and entries, 25 for the classification, 35 for the reclassifications and passed items, 40 for materiality and the judgment, 20 for the checks. Hold back the reversal point until students have totaled the year-end balances. **Collect** the schedule and the Table.

![A mock of the schedule of adjustments, the one exhibit the CFO approves entry by entry.](../figures/chapter-17-statements-for-a-lender/IF-17-5-A.pdf)

## Step-by-step solution

### Part 1: Number each adjustment and write its entries

**Step 1. Put A1 to A4 on the schedule and write their entries.** One row for each adjustment, in the case's layout. A year's income effect is the amount at that year-end less the one before, because the earlier error reverses. Keep the entry lines in the AdjustmentLines Table, one row for each account and year-end, as debits less credits. The model's formulas: A1's effect on the last year's income, then four lines of the last year-end's entries (the 2025 accrual into retained earnings, the increase to `5080`, the credit to `2030`, the debit to receivables for the cutoff):

```
=-(Payroll_2026-Payroll_2025)
=Payroll_2025
=PayMfg_2026-PayMfg_2025
=-PayGross_2026
=Cutoff_2026
```

**Check:** the effect of each adjustment on opening retained earnings, 2025 income and 2026 income is in the instructor note below; in total -$175,240.12, -$76,459.90 and +$68,475.84. A1 alone is -$302,568.90, -$63,352.29 and -$17,123.63. **Watch for:** two errors. Taking each year-end's amount as the year's effect gives -$183,224.18 for 2026, the equity effect, where the income effect is +$68,475.84. Booking the whole payroll accrual in 2026 gives -$383,044.82, where only -$17,123.63 is new.

**Step 2. Classify and assign a period.** A1, A2 and A4 correct errors: the facts existed at each year-end. A3 corrects an error if the evidence shows nothing was owed at each year-end, and is otherwise a change in estimate of the year it goes stale. Because the shareholders received 2025 statements, present 2025 as restated, with the Topic 250 disclosures: opening retained earnings fall by $175,240.12 and 2025 income by $76,459.90 (a reasoned "revised" presentation is acceptable).

**Check:** adjusted income before income taxes is $5,057,894.81 for 2025 and $4,572,087.08 for 2026.

### Part 2: Reclassifications and passed items

**Step 3. Record R1 and R2.** R1 moves the principal due within a year out of the long-term notes: the script's R1 query sums the principal of each note's payments dated within a year after the year-end, for the notes originated by then.

**Check:** $89,243.61 at the end of 2025 (the first note only) and $147,503.76 at the end of 2026. **Watch for:** the next year's scheduled payments, which include interest: $168,532.44, not the principal. R2 nets the credit balance of `1090`, $46,730.55 at the last year-end, into work in process ($61,095.34 before), because `1090` clears conversion cost into it; no income changes.

**Step 4. Measure P1 to P3 and pass them.** P1 is an allowance at Exercise 8.1's rates on the open invoices.

```sql
-- Requirement 5: passed item P1, an allowance at Exercise 8.1's rates at each year-end
-- Population: the view OpenReceivables; rates 0.5%, 2%, 5%, 15%, 40%; expected: 34,659.34 (2025) and 34,106.25 (2026)
WITH Buckets AS (
    SELECT AsOfDate, BucketOrder,
        ROUND(SUM(Balance), 2) AS Balance
    FROM OpenReceivables
    GROUP BY AsOfDate, BucketOrder
)
SELECT AsOfDate,
    ROUND(SUM(ROUND(Balance * CASE BucketOrder
        WHEN 1 THEN 0.005 WHEN 2 THEN 0.02 WHEN 3 THEN 0.05
        WHEN 4 THEN 0.15 ELSE 0.40 END, 2)), 2) AS Allowance
FROM Buckets
GROUP BY AsOfDate
ORDER BY AsOfDate;
```

**Check:** P1 is -$34,106.25 at the last year-end and -$34,659.34 a year earlier, so +$553.09 on 2026 income. P2, the returns expected after the year-end, is estimated from the 14 returns made in 2026 on 2025's deliveries ($16,319.03 of revenue less $9,545.90 of cost): -$6,773.13. P3, the full cost of the damaged returns restocked, is -$61,146.00. In aggregate -$102,025.38, 45% of materiality. **Watch for:** letting the aging take in the opening receivable. At the top rate it adds $152,000.00, $186,106.25 in all, for a balance that is a question for evidence, not an aging bucket.

### Part 3: Materiality and the judgment

**Step 5. Compute materiality for each year.** Five percent of income before income taxes as the ledger records it (the model workbook's formula is `=ROUND(C6*5%,2)`, with the recorded income in C6).

**Check:** $256,717.74 for 2025 and $225,180.56 for 2026, and $11,259.03 as clearly trivial. **Watch for:** adjusted income as the base, which gives $228,604.35 and a circular rule.

**Step 6. Judge individually and in aggregate.** The effect on 2026 income, +$68,475.84, is 30% of materiality, but other grounds say record: the payroll liability alone, $383,044.82, exceeds materiality; current liabilities rise by $227,705.29 before the reclassification and working capital falls by $330,727.94 after it; at the end of 2025 they were understated by $271,240.88, above that year's materiality; and the error recurs every year. Pass P1 to P3 for approval; list the freight residual, $3,719.65, as clearly trivial.

**Step 7. Show the adjusted trial balances balance and that no adjustment touches cash.** Add two columns to Working TB, the adjustment for each account and the adjusted balance:

```
=SUMIFS(AdjustmentLines[Amount],AdjustmentLines[Account],[@AccountNumber],AdjustmentLines[YearEnd],YE_2026)
=ROUND([@Recorded2026]+[@Adj2026],2)
```

**Check:** the largest imbalance of any entry is zero, no line has account `1010`, and the adjusted statements follow in Requirement 6. Holding A3 for evidence instead lowers income before income taxes by $57,021.15 in 2025 and $61,297.21 in 2026.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| A1 to A4: effect on income, 2025; 2026 | -$76,459.90; +$68,475.84 | 1 |
| Equity effect at the year-ends, 2025; 2026 | -$251,700.02; -$183,224.18 | 1 |
| Adjusted income before income taxes, 2025; 2026 | $5,057,894.81; $4,572,087.08 | 2 |
| Current portion of the notes, 2025; 2026 | $89,243.61; $147,503.76 | 3 |
| P1, P2, P3 and the aggregate | -$34,106.25; -$6,773.13; -$61,146.00; -$102,025.38 | 4 |
| Materiality, 2025; 2026 | $256,717.74; $225,180.56 | 5 |

> **Instructor notes, Requirement 5:** recorded adjustments, effect on retained earnings at 1 January 2025 / 2025 income / 2026 income: A1 payroll accrual -302,568.90 / -63,352.29 (cost of goods sold +47,825.24, operating expense +15,527.05) / -17,123.63 (cost of goods sold +17,295.54, operating expense -171.91); A2 revenue cutoff +90,138.93 / -70,598.07 / +24,940.25 (4010 +22,504.23, 4020 -633.05, 4030 +1,709.84, 4040 +1,359.23); A3 old accruals +39,028.43 / +57,021.15 / +61,297.21; A4 interest -1,838.58 / +469.31 / -637.99. Totals -175,240.12 / -76,459.90 / +68,475.84; equity effect at 2025 / 2026 year-ends -251,700.02 / -183,224.18. Adjusted income before income taxes 2025 5,057,894.81, 2026 4,572,087.08 (recorded 4,503,611.24 + 68,475.84); with the old accruals kept (A3 held for evidence) 5,000,873.66 and 4,510,789.87. Entries at 2026-12-31 (debits = credits): A1 Dr retained earnings 365,921.19, Dr 5080 17,295.54, Cr operating expense 171.91, Cr 2030 336,456.34, Cr 2032 25,738.93, Cr 2033 20,849.55; A2 Dr 1020 44,481.11, Cr retained earnings 19,540.86, Cr revenue 24,940.25; A3 Dr 2040 157,346.79, Cr retained earnings 96,049.58, Cr operating expense 61,297.21; A4 Dr retained earnings 1,369.27, Dr 7030 637.99, Cr 2080 2,007.26. Reclassifications: R1 the current portion of the notes, 89,243.61 at 2025 (note 1 only; note 2 began in 2026) and 147,503.76 at 2026; R2 the credit balance of 1090 (-49,102.81 / -46,730.55) netted into work in process (1046 63,392.97 / 61,095.34), because 1090 clears conversion cost into work in process, not because a credit cannot sit among current assets (contra assets do); how its variances belong between inventory and cost of goods sold is the cost study of Requirement 9. Materiality 225,180.56 (2026, on recorded income as the controller set it) and 256,717.74 (2025). Judgment: 2026's income effect is 30% of materiality, but the payroll liability (383,044.82) exceeds it; current liabilities at 2026 rise by 227,705.29 before the reclassification and working capital falls by 330,727.94 after it; at 2025 current liabilities were understated by 271,240.88, above 2025 materiality, and the missing payroll accrual recurs every year. Record A1, A2, A4, R1, and R2; record A3 once the suppliers' evidence supports it, or hold it, as a retained-liability answer does. Present 2025 as restated, with the Topic 250 disclosures, because the shareholders received 2025 statements (a reasoned "revised" presentation is acceptable). Passed items, at the 2026 year-end and, for the two estimates, on 2026 income once the same estimate at the end of 2025 reverses: P1 an allowance at Chapter 8's rates, -34,106.25 (-34,659.34 at the end of 2025, so +553.09 on 2026 income), on the invoice aging (4,418,804.32) only: the adjusted receivables also hold the 380,000.00 opening line, a question for evidence rather than an aging bucket, and the 44,481.11 of deliveries not yet invoiced; P2 expected returns, from 2026's returns of 2025 deliveries (14 returns, 16,319.03 of revenue less 9,545.90 of cost; 13 in 2025 for 2024 deliveries, 13,985.96 less 8,113.31), about -6,773.13 (about -900.48 on 2026 income), as an entry Dr 4060 and Cr a refund liability for the revenue, Dr a returns recovery asset and Cr cost of goods sold for the cost, if those amounts and the goods' value are supported (not Cr 1020); P3 the full standard cost of the Damaged and Quality Concern returns of 2026 restocked, -61,146.00 (137,606.43 since 2024: 24,429.94 / 52,030.49 / 61,146.00), the exposure if none of them can be sold: the reason code does not show whether the goods are still on hand or what they would realize, so a count and a net realizable value review measure the write-down; aggregate -102,025.38, 45% of materiality (-61,493.39 on 2026 income). Pass all three and list them for the CFO's approval; list the freight residual of 3,719.65 as trivial, since the controller wants every adjustment listed.

## What a strong answer says

- **Classification.** Each entry typed by what the facts were at the year-end, and the assumption of A3 stated.
- **Periods.** Each year-end's amount reversing the one before, 2025 restated because the shareholders received its statements.
- **Judgment.** Materiality by size and other grounds, the recurring error noted, the passed items listed in aggregate.

A weak answer records or passes everything on the size of one year's income effect.

## Common mistakes and how to respond

- **No reversal.** *Symptom:* a 2026 income effect of -$183,224.18. *Response:* ask what the 2025 entry already took out of retained earnings.
- **The whole accrual in one year.** *Symptom:* -$383,044.82 in 2026. *Response:* ask which part of it was owed at the end of 2025.
- **Aging the opening line.** *Symptom:* an allowance of $186,106.25. *Response:* ask which bucket a balance with no invoice belongs to.
- **Size alone.** *Symptom:* "less than a third of materiality, so pass it." *Response:* ask what the liability does to working capital.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Schedule and entries | 30 | A1 to A4 numbered, entries for both year-ends, effects by year, in a Table | One year-end |
| Classification and periods | 20 | Type and period for each; 2025 restated | Types without periods |
| Reclassifications and passed items | 20 | R1, R2 and P1 to P3 measured | Not described |
| Materiality and judgment | 20 | Both years; size and other grounds; aggregate | Size alone |
| Checks | 10 | Entries balance; no cash line | Not shown |

## Extensions and discussion questions

- Rebuild the schedule for the retained-liability answer to A3 and compare the two presentations of 2025.
- Show that the adjustments change lines of the cash flow reconciliation but not its totals (Requirement 6).
- Discuss: why does a recurring error of modest size deserve attention?
