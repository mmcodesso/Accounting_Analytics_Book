# Requirement 5: Close the fiscal 2026 statements (Chapters 11 and 12; financial reporting)

| | |
|---|---|
| Unit | Case Part 3: Planning the Plant's Hours for 2027 |
| Item | Requirement 5 |
| Perspective | Financial accounting |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 140 minutes |
| Solution file | PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 5 (the views PayrollAccrual, PriorYearWork and CutoffItems, the reruns of tests L5, L6 and L8, and the summary of adjustments), and the Requirement 5 model answer in its closing comments |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This requirement estimates the year-end payroll accrual by working day, measures the same error a year earlier, and shows that the two almost cancel in income and do not on the balance sheet. It then decides where the cost of the surge hours belongs (the inventory standard) and reruns Chapter 12's cutoff tests. The analytics type is descriptive and prescriptive.

Students can:

- estimate an accrual by working day, by cost center, with the accounts to debit and credit (Steps 1 and 2);
- measure the prior year's unrecorded work and separate the effect on income from the effect on the balance sheet (Steps 3 and 4);
- decide what to do with an old balance that no payroll cleared (Step 5);
- apply the inventory standard to idle capacity (Step 7), and judge materiality (Step 8).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Reporting and Control (financial recordkeeping and statement preparation); IFAC IES 2 (a); AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql, Audit.sql (tests L5, L6, L8), Tutorial 11.2's pay dates and Chapter 6's net income of 2026.
- **Data conditions.** The last two periods of 2026 are Open with no registers; WorkCenterCalendar has a row for each work center and date, so working days are counted by `COUNT(DISTINCT CalendarDate)`.

## How to run it

Pairs, about 140 minutes: 35 for the accrual and entries, 30 for the prior year and the effect, 15 for account 2030, 25 for the inventory standard, 25 for the cutoff reruns, 10 for the materiality judgment. Hold back the prior-year view until the first accrual is right (13 working days left). **Collect** the script and the adjustments table.

## Step-by-step solution

### Part 1: The accrual at the year-end

**Step 1. Build PayrollAccrual from the last eight processed periods.** The cost per working day is those periods' payroll, by cost center, over the working days they span; multiply by the working days left in the year.

```sql
WITH Periods AS (
    SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate
    FROM PayrollPeriod
    WHERE Status = 'Processed'
    ORDER BY PeriodEndDate DESC
    LIMIT 8
),
```

```sql
        (SELECT COUNT(DISTINCT c.CalendarDate)
         FROM WorkCenterCalendar AS c
         WHERE c.IsWorkingDay = 1
             AND c.CalendarDate > sp.LastDay
             AND c.CalendarDate <= '2026-12-31') AS DaysLeft
```

**Check:** periods 70 to 77, 2026-08-24 to 2026-12-13, cost 2,298,268.90 over 78 working days, 29,464.99 a day; 13 days left (the December 25 holiday is not a working day); accrual 383,044.82: gross pay 336,456.34, employer taxes 25,738.93, benefits 20,849.55. **Watch for:** two wrong versions.

- Without the `Status` filter the last eight periods include the Open ones, no day is left after the last, and the accrual is 0.00.
- Counting calendar rows instead of dates, on one side only, scales the accrual by the 5 work centers: 76,608.96 or 1,915,224.08.

**Step 2. Write the adjusting entries.** Query the debits of 2026's payroll postings (`SourceDocumentType = 'PayrollSummary'`) by cost center and account, joining Account on `AccountID`.

**Check:** Manufacturing is debited to account 1090 alone, for its whole cost (197,970.68, with 24,530.56 of employer costs); each of the other 9 cost centers goes to one salary account for gross pay (Administration 6030, Customer Service 6040, Design Services 6280, Executive 6050, Marketing 6240, Purchasing 6230, Research and Development 6250, Sales 6010, Warehouse 6020), 163,016.22 in all, and to 6060 Payroll Taxes and Benefits for its employer costs only, 22,057.92. A student who debits 6060 for every employer cost counts Manufacturing's twice. The credits are 2030 Accrued Payroll for gross pay, 2032 for employer taxes and 2033 for benefits. The Manufacturing part stays in 1090 until it is cleared, because no completion releases standard cost against it. On the case's reading that it is a cost of the period, a second entry moves it to account 5080 (debit 5080, credit 1090), once the accountant has judged how much is normal cost.

![Why recording both payroll accruals moves the liability far more than income.](../figures/case-part-3/IF-C3-5-A.pdf)

### Part 2: The year before

**Step 3. Build PriorYearWork from the pay periods that cross the year-end.** Take periods that start by December 31 and were paid after it, and apportion each by working days inside the year.

```sql
    FROM PayrollPeriod AS pp
    WHERE pp.PeriodStartDate <= '2025-12-31'
        AND pp.PayDate > '2025-12-31'
```

**Check:** period 52 (2025-12-15 to 2025-12-28, paid 2026-01-02) is all 2025 work, 263,426.72; period 53 has 3 of 9 working days in 2025: 307,483.41 times 3/9 is 102,494.47. Total 365,921.19 of 2025 work charged to 2026, 180,675.14 of it Manufacturing. **Watch for:** `PeriodEndDate > '2025-12-31'` finds only period 53 and 102,494.47: the earlier period was paid in 2026 for work all done in 2025.

**Step 4. Separate the effect on income from the effect on the balance sheet.** Start from Chapter 6's net income and add the payroll and cutoff effects.

```sql
SELECT NetIncome,
    ROUND(AccrualYearBefore - AccrualAtYearEnd, 2) AS PayrollEffect,
    ROUND(RevenueToAdd - RevenueToRemove, 2) AS CutoffEffect,
    ROUND(NetIncome + AccrualYearBefore - AccrualAtYearEnd
        + RevenueToAdd - RevenueToRemove, 2) AS AdjustedNetIncome,
```

**Check:** 2026 expense rises by only 17,123.63 (383,044.82 less 365,921.19), while the liability rises by 383,044.82 and opening retained earnings fall by 365,921.19: the errors counterbalance in income and not on the balance sheet. **Watch for:** with the closes left in, net income is zero and the adjusted figure 7,816.62; recording only the 2026 accrual gives 4,145,506.67.

**Step 5. Decide on account 2030's old balance.** Group the account by source document type (test L8).

```sql
SELECT gl.SourceDocumentType, COUNT(*) AS Postings,
    ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE a.AccountNumber = 2030 AND gl.PostingDate <= '2026-12-31'
GROUP BY gl.SourceDocumentType;
```

**Check:** 95,000.00 remains from JE-2024-000001 alone, and the payroll postings net to zero. It is not the year-end accrual. Investigate it with the other unsupported opening balances of Chapter 8, and reverse it against opening retained earnings only if the investigation shows it is not owed, never against the new accrual.

### Part 3: Inventory and cutoff

**Step 6. Apply the inventory standard.** Compare the year's actual conversion cost per standard hour with the standard, and read the finished goods balance (account `1040` to the year-end, summed on `AccountNumber`).

**Check:** actual 78.77 against the standard 47.40 per standard hour; finished goods 12,169,701.74. The actual figure is a pay-year ledger cost over the year's output. Raising the standards to absorb it would carry idle capacity and unsupported hours into inventory, and defer them to later years. The part that comes from idle capacity or hours beyond the work is abnormal and belongs in 2026's cost of goods sold, and measuring it needs Requirement 4's overhead analysis, because nominal employee-hours are not normal capacity. **Watch for:** `FiscalYear = 2026` returns the year's movement, 1,339,881.52, not the balance.

**Step 7. Rerun the revenue cutoff tests.** Test L5 finds the invoices posted in another year than their delivery, test L6 the shipments never invoiced.

**Check:** 19,540.86 of 2025 deliveries is in 2026's revenue, and 9 shipment lines were never invoiced, 44,481.11 at order price with 22,895.78 of standard cost already in cost of goods sold: net 24,940.25 more 2026 revenue, receivables 44,481.11 higher, opening retained earnings 19,540.86 higher. **Watch for:** the 2 invoices dated before their shipment (1,349.19) were posted in the year of delivery; they are no cutoff error.

**Step 8. Summarize the adjustments and judge materiality.** 4,503,611.24 less 17,123.63 plus 24,940.25 is 4,511,427.86, a net change of 0.17%, which does not make the errors immaterial. Judge the liability left out (8.5% of net income), the prior-year error and the recurring deficiency each on its own. The supplier invoice ASV0050-2025-040073 (3,266.27, received 2026-01-01) is not a payables cutoff item: JE-2025-000188 carried its liability.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Accrual: cost a day; amount | 29,464.99; 383,044.82 | 1 |
| Prior-year work paid in 2026 | 365,921.19 | 3 |
| Effect on 2026 income; liability | 17,123.63; 383,044.82 | 4 |
| Adjusted net income | 4,511,427.86 | 8 |
| Actual against standard conversion per hour | 78.77; 47.40 | 6 |

> **Instructor notes, Requirement 5:** the last eight processed periods (70-77, 2026-08-24 to 2026-12-13) cost 2,298,268.90 over 78 working days, 29,464.99 a day; December 14-31, 2026, has 13 working days (December 25 is a holiday), so the accrual is 383,044.82: gross pay 336,456.34, employer payroll taxes 25,738.93, benefits 20,849.55. By cost center: Manufacturing 197,970.68 (gross 173,440.12), Executive 42,080.32, Design Services 27,818.05, Sales 23,206.37, Administration 19,301.65, Purchasing 18,982.21, Warehouse 17,730.79, Marketing 14,333.19, Customer Service 11,338.71, Research and Development 10,282.84. Entries: debit 1090 for Manufacturing's whole cost, 197,970.68 (its gross pay and 24,530.56 of employer costs), the salary accounts of the other cost centers (6010-6050, 6230, 6240, 6250, 6280) for their gross pay, 163,016.22, and 6060 Payroll Taxes and Benefits for their employer costs only, 22,057.92; credit 2030 Accrued Payroll for gross pay, 2032 for employer taxes, and 2033 for benefits. The manufacturing part stays in 1090 until it is cleared, because no completion releases standard cost against it. On the case's reading that it is a cost of the period, a second entry moves it to 5080 (debit 5080, credit 1090), once the accountant has judged how much of it is normal cost that the standards should carry. The 2025 year-end: period 52 (2025-12-15 to 12-28, paid 2026-01-02) is all 2025 work, 263,426.72, and 3 of the 9 working days of period 53 (2025-12-29 to 2026-01-11) fall in 2025, 307,483.41 x 3/9 = 102,494.47, so 365,921.19 of 2025 work (manufacturing 180,675.14) was charged to fiscal 2026. Recording both: fiscal 2026 expense rises by only 17,123.63 (383,044.82 less 365,921.19), while the liability at 2026-12-31 rises by 383,044.82 and opening retained earnings fall by 365,921.19; the errors counterbalance in income but not on the balance sheet. (Allocating by the hours actually worked, as Exercise 12.1 does for hourly labor, gives about 335,000 for 2025.) The 95,000 in 2030 is the opening line of JE-2024-000001; no payroll in the data ever cleared it, so it is not the year-end accrual: investigate it with the other unsupported opening balances of Chapter 8, and reverse it against opening retained earnings only if the investigation shows it is not owed (no payment in the records does not show that), rather than netting it against the new accrual. ASC 330: 2026's conversion cost on the ledger was 78.77 per standard hour of the year's output against the standard 47.40 (a pay-year cost over output, not a matching of hours to work); raising the standards to absorb it would carry idle capacity and unsupported hours into finished goods (1040, 12,169,701.74 at year-end) and defer them to later years. Standards that approximate actual cost are acceptable, and an ordinary variance from out-of-date standards could be spread between inventory and cost of sales, so the argument rests on the causes. The part of the cost that comes from idle capacity or from hours beyond the work is abnormal and belongs in 2026's cost of goods sold, and measuring that part needs Requirement 4's analysis of the overhead. Cutoff (L5, L6): fiscal 2026 revenue includes 19,540.86 of December 2025 deliveries and excludes 9 shipment lines of December 2026 never invoiced, 44,481.11 at order price, whose standard cost (22,895.78) is already in cost of goods sold; the net effect on 2026 revenue is +24,940.25, with receivables +44,481.11 and opening retained earnings +19,540.86. Adjusted 2026 net income: 4,503,611.24 - 17,123.63 + 24,940.25 = 4,511,427.86 (the ledger records no income tax). Materiality: the net effect on income, 7,816.62, is under 0.2% of net income, but that does not make the errors immaterial. The liability left out, 383,044.82, is 8.5% of net income and 2.8% of current liabilities, the prior-year error moves opening retained earnings, and the missing year-end accrual is a deficiency in the close that recurs every year, so each is judged on its own and together with the qualitative factors (the case gives no threshold); the supplier invoice ASV0050-2025-040073 (3,266.27, received 2026-01-01) is not a payables cutoff item: its October 2025 accrual, JE-2025-000188, carried the liability at the year-end.

## What a strong answer says

- **The accrual.** By working day and cost center, with Manufacturing's whole cost in 1090, cleared by a second entry.
- **Income against balance sheet.** Two accruals that almost cancel in income and not on the balance sheet.
- **Account 2030.** An unsupported opening balance to investigate, not an accrual to net.
- **Inventory and materiality.** No standard raised to absorb abnormal cost, and each error judged on its own.

## Common mistakes and how to respond

- **Open periods in the last eight, or rows for dates.** *Symptom:* an accrual of 0.00, or a fifth or five times too much. *Response:* ask which periods have registers, and how many rows a date has.
- **One accrual only.** *Symptom:* income down by the full liability. *Response:* ask what the opening balance would then claim.
- **Netting 2030.** *Symptom:* the old balance cleared against the new accrual. *Response:* ask what the payroll postings did to the account.
- **Raising the standards.** *Symptom:* a variance that disappears. *Response:* ask where idle capacity goes.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Accrual by cost center and entries | 25 | Working days; correct accounts; Manufacturing part explained | Calendar days, or no entries |
| Prior-year work; income against balance sheet | 25 | Both accruals; the difference explained | One accrual, or no explanation |
| Account 2030 | 10 | Investigated, not netted | Netted |
| Inventory standard | 20 | Abnormal costs expensed; effect on finished goods | Conclusion without the reason |
| Cutoff and summary | 20 | L5 and L6 rerun; net effect; materiality judged | Rerun without the summary |

## Extensions and discussion questions

- Accrue by the hours worked instead of by working days, as Exercise 12.1 does for hourly labor (335,000 for the prior year), and compare.
- Discuss: small in income, large on the balance sheet, and recurring. Is it a misstatement, a control deficiency, or both?
