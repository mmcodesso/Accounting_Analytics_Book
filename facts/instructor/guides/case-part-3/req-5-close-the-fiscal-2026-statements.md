---
note: case3.r5
uses: [case3.g5]
title: Close the fiscal 2026 statements (Chapters 11 and 12; financial reporting)
kind: requirement
number: '5'
unit: case3
perspective: financial
tool: sql
minutes: 140
solution: "PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 5 (the views PayrollAccrual, PriorYearWork and CutoffItems, the reruns of tests L5, L6 and L8, and the summary of adjustments), and the Requirement 5 model answer in its closing comments"
figures:
  - id: IF-C3-5-A
    kind: diagram
    purpose: Why recording both payroll accruals moves the liability far more than income.
    shows: "Two columns, Income and Balance sheet. Under Income, two bars side by side, the expense for the work after the time records end and the expense for the prior year's work paid in the year, nearly equal, with the small net difference marked. Under Balance sheet, one tall bar for the liability at the year-end and one bar for the fall in opening retained earnings, with the small fall in the year's income stacked on it in the same amber as the net difference, so the two together reach the height of the liability."
    data: The accrual and prior-year queries of Steps 1 and 3.
---
{% set g = case3_g5 %}
# Requirement 5: Close the fiscal 2026 statements (Chapters 11 and 12; financial reporting)

{{ header() }}

## Purpose and learning outcomes

This requirement estimates the year-end payroll accrual by working day, measures the same error a year earlier, and shows that the two almost cancel in income and do not on the balance sheet. It then decides where the cost of the surge hours belongs (the inventory standard) and reruns Chapter 12's cutoff tests. The analytics type is descriptive and prescriptive.

Students can:

- estimate an accrual by working day, by cost center, with the accounts to debit and credit (Steps 1 and 2);
- measure the prior year's unrecorded work and separate the effect on income from the effect on the balance sheet (Steps 3 and 4);
- decide what to do with an old balance that no payroll cleared (Step 5);
- apply the inventory standard to idle capacity (Step 7), and judge materiality (Step 8).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Reporting and Control (financial recordkeeping and statement preparation); IFAC IES 2 (a); AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql, Audit.sql (tests L5, L6, L8), Tutorial 11.2's pay dates and Chapter 6's net income of {{ d.C }}.
- **Data conditions.** The last two periods of {{ d.C }} are Open with no registers; WorkCenterCalendar has a row for each work center and date, so working days are counted by `COUNT(DISTINCT CalendarDate)`.

## How to run it

Pairs, about 140 minutes: 35 for the accrual and entries, 30 for the prior year and the effect, 15 for account 2030, 25 for the inventory standard, 25 for the cutoff reruns, 10 for the materiality judgment. Hold back the prior-year view until the first accrual is right ({{ p.left }} working days left). **Collect** the script and the adjustments table.

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

**Check:** periods {{ p.ids|first }} to {{ p.ids|last }}, {{ p.start }} to {{ p.end }}, cost {{ p.cost|money }} over {{ p.wd }} working days, {{ p.daily|money }} a day; {{ p.left }} days left (the {{ holidays|join(' and ') }} holiday is not a working day); accrual {{ p.accrual|money }}: gross pay {{ p.gross|money }}, employer taxes {{ p.tax|money }}, benefits {{ p.ben|money }}. **Watch for:** two wrong versions.

- Without the `Status` filter the last eight periods include the Open ones, no day is left after the last, and the accrual is {{ g.no_status[6]|money }}.
- Counting calendar rows instead of dates, on one side only, scales the accrual by the {{ g.work_centers }} work centers: {{ g.period_rows[6]|money }} or {{ g.left_rows[6]|money }}.

**Step 2. Write the adjusting entries.** Query the debits of {{ d.C }}'s payroll postings (`SourceDocumentType = 'PayrollSummary'`) by cost center and account, joining Account on `AccountID`.

**Check:** Manufacturing is debited to account {{ g.accounts.Manufacturing|join(', ') }} alone, for its whole cost ({{ mfg_all_in|money }}, with {{ mfg_employer|money }} of employer costs); each of the other {{ p.centers|length - 1 }} cost centers goes to one salary account for gross pay ({% for cc, nums in g.accounts.items() %}{% if cc != 'Manufacturing' %}{{ cc }} {{ nums|reject('equalto', 6060)|first }}{{ ", " if not loop.last else "" }}{% endif %}{% endfor %}), {{ other_gross|money }} in all, and to {{ g.names[3][0] }} {{ g.names[3][1] }} for its employer costs only, {{ other_employer|money }}. A student who debits {{ g.names[3][0] }} for every employer cost counts Manufacturing's twice. The credits are {{ g.names[0][0] }} {{ g.names[0][1] }} for gross pay, {{ g.names[1][0] }} for employer taxes and {{ g.names[2][0] }} for benefits. The Manufacturing part stays in {{ g.accounts.Manufacturing|join(', ') }} until it is cleared, because no completion releases standard cost against it. On the case's reading that it is a cost of the period, a second entry moves it to account {{ g.variance_account }} (debit {{ g.variance_account }}, credit {{ g.accounts.Manufacturing|join(', ') }}), once the accountant has judged how much is normal cost.

{{ figure('IF-C3-5-A') }}

### Part 2: The year before

**Step 3. Build PriorYearWork from the pay periods that cross the year-end.** Take periods that start by December 31 and were paid after it, and apportion each by working days inside the year.

```sql
    FROM PayrollPeriod AS pp
    WHERE pp.PeriodStartDate <= '2025-12-31'
        AND pp.PayDate > '2025-12-31'
```

**Check:** period {{ prior.full.id }} ({{ prior.full.start }} to {{ prior.full.end }}, paid {{ prior.full.pay }}) is all {{ d.P }} work, {{ prior.full.cost|money }}; period {{ prior.cross.id }} has {{ prior.cross.inside }} of {{ prior.cross.days }} working days in {{ d.P }}: {{ prior.cross.cost|money }} times {{ prior.cross.inside }}/{{ prior.cross.days }} is {{ prior.cross.share|money }}. Total {{ prior.total|money }} of {{ d.P }} work charged to {{ d.C }}, {{ prior.mfg|money }} of it Manufacturing. **Watch for:** `PeriodEndDate > '2025-12-31'` finds only period {{ prior.cross.id }} and {{ g.by_end[7]|money }}: the earlier period was paid in {{ d.C }} for work all done in {{ d.P }}.

**Step 4. Separate the effect on income from the effect on the balance sheet.** Start from Chapter 6's net income and add the payroll and cutoff effects.

```sql
SELECT NetIncome,
    ROUND(AccrualYearBefore - AccrualAtYearEnd, 2) AS PayrollEffect,
    ROUND(RevenueToAdd - RevenueToRemove, 2) AS CutoffEffect,
    ROUND(NetIncome + AccrualYearBefore - AccrualAtYearEnd
        + RevenueToAdd - RevenueToRemove, 2) AS AdjustedNetIncome,
```

**Check:** {{ d.C }} expense rises by only {{ change|money }} ({{ p.accrual|money }} less {{ prior.total|money }}), while the liability rises by {{ p.accrual|money }} and opening retained earnings fall by {{ prior.total|money }}: the errors counterbalance in income and not on the balance sheet. **Watch for:** with the closes left in, net income is zero and the adjusted figure {{ g.closes_in[3]|money }}; recording only the {{ d.C }} accrual gives {{ g.only_new|money }}.

**Step 5. Decide on account 2030's old balance.** Group the account by source document type (test L8).

```sql
SELECT gl.SourceDocumentType, COUNT(*) AS Postings,
    ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE a.AccountNumber = 2030 AND gl.PostingDate <= '2026-12-31'
GROUP BY gl.SourceDocumentType;
```

**Check:** {{ opening|money }} remains from {{ entry }} alone, and the payroll postings net to zero. It is not the year-end accrual. Investigate it with the other unsupported opening balances of Chapter 8, and reverse it against opening retained earnings only if the investigation shows it is not owed, never against the new accrual.

### Part 3: Inventory and cutoff

**Step 6. Apply the inventory standard.** Compare the year's actual conversion cost per standard hour with the standard, and read the finished goods balance (account `1040` to the year-end, summed on `AccountNumber`).

**Check:** actual {{ actual_rate|num(2) }} against the standard {{ std_rate|num(2) }} per standard hour; finished goods {{ fg|money }}. The actual figure is a pay-year ledger cost over the year's output. Raising the standards to absorb it would carry idle capacity and unsupported hours into inventory, and defer them to later years. The part that comes from idle capacity or hours beyond the work is abnormal and belongs in {{ d.C }}'s cost of goods sold, and measuring it needs Requirement 4's overhead analysis, because nominal employee-hours are not normal capacity. **Watch for:** `FiscalYear = 2026` returns the year's movement, {{ g.fg_year|money }}, not the balance.

**Step 7. Rerun the revenue cutoff tests.** Test L5 finds the invoices posted in another year than their delivery, test L6 the shipments never invoiced.

**Check:** {{ delivered|money }} of {{ d.P }} deliveries is in {{ d.C }}'s revenue, and {{ n_uninv }} shipment lines were never invoiced, {{ uninv|money }} at order price with {{ uninv_std|money }} of standard cost already in cost of goods sold: net {{ net_rev|money }} more {{ d.C }} revenue, receivables {{ uninv|money }} higher, opening retained earnings {{ delivered|money }} higher. **Watch for:** the {{ g.before_ship[2] }} invoices dated before their shipment ({{ g.before_ship[3]|money }}) were posted in the year of delivery; they are no cutoff error.

**Step 8. Summarize the adjustments and judge materiality.** {{ ni|money }} less {{ change|money }} plus {{ net_rev|money }} is {{ adj_ni|money }}, a net change of {{ share|pct(2) }}, which does not make the errors immaterial. Judge the liability left out ({{ liab_ni|pct(1) }} of net income), the prior-year error and the recurring deficiency each on its own. The supplier invoice {{ asv[0].number }} ({{ asv[0].total|money }}, received {{ asv[0].received }}) is not a payables cutoff item: {{ asv[0].je }} carried its liability.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Accrual: cost a day; amount | {{ p.daily|money }}; {{ p.accrual|money }} | 1 |
| Prior-year work paid in {{ d.C }} | {{ prior.total|money }} | 3 |
| Effect on {{ d.C }} income; liability | {{ change|money }}; {{ p.accrual|money }} | 4 |
| Adjusted net income | {{ adj_ni|money }} | 8 |
| Actual against standard conversion per hour | {{ actual_rate|num(2) }}; {{ std_rate|num(2) }} | 6 |

{{ expected() }}

## What a strong answer says

- **The accrual.** By working day and cost center, with Manufacturing's whole cost in {{ g.accounts.Manufacturing|join(', ') }}, cleared by a second entry.
- **Income against balance sheet.** Two accruals that almost cancel in income and not on the balance sheet.
- **Account 2030.** An unsupported opening balance to investigate, not an accrual to net.
- **Inventory and materiality.** No standard raised to absorb abnormal cost, and each error judged on its own.

## Common mistakes and how to respond

- **Open periods in the last eight, or rows for dates.** *Symptom:* an accrual of {{ g.no_status[6]|money }}, or a fifth or five times too much. *Response:* ask which periods have registers, and how many rows a date has.
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

- Accrue by the hours worked instead of by working days, as Exercise 12.1 does for hourly labor ({{ hours|num }} for the prior year), and compare.
- Discuss: small in income, large on the balance sheet, and recurring. Is it a misstatement, a control deficiency, or both?
