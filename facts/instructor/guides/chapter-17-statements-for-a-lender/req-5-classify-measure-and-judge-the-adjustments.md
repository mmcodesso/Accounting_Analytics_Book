---
note: ch17.r5
uses: [ch17.g5]
title: Classify, measure, and judge the adjustments (Chapters 4, 6, and 8)
kind: requirement
number: '5'
unit: '17'
perspective: financial
tool: mixed
minutes: 180
solution: "Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheets Adjustments (the schedule, the AdjustmentLines Table, materiality and the passed items) and Working TB (the adjustments and adjusted balances); Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 5 (the receivables aging, the allowance, returns after the year-end, the current portion of the notes)"
figures:
  - id: IF-17-5-A
    kind: excel-mock
    purpose: The schedule of adjustments, the one exhibit the CFO approves entry by entry.
    shows: "The Adjustments worksheet at its top block. Rows A1 to A4 with a total row, then R1 and R2, then P1 to P3 and a row for the passed items in aggregate. Columns: No., Adjustment, Accounts, Evidence, retained earnings at the start of the comparative year, income for each of the two years, balance at each year-end, Type and Decision. The total row and the adjusted net income row are outlined."
    data: The effects of A1 to A4, R1, R2 and P1 to P3 (the Expected results).
---
{% macro sm(x) %}{{ "-" if x < 0 else "+" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = ch17_g5 %}
# Requirement 5: Classify, measure, and judge the adjustments (Chapters 4, 6, and 8)

{{ header() }}

## Purpose and learning outcomes

This requirement turns the measurements of Requirements 3 and 4 into numbered entries, decides the period each belongs to, and judges which to record and which to pass. The workbook suits it: a working trial balance keeps the recorded balances, the adjustments and the adjusted balances side by side, each traceable to its evidence. The analytics type is prescriptive.

Students can:

- write each adjustment's entries for both year-ends, with the effect on opening equity, on each year's income and on the balance sheet (Part 1);
- classify each as an error, a change in estimate or a reclassification, and assign it to a period (Parts 1 and 2);
- compute materiality and judge the adjustments individually and in aggregate, on size and on other grounds (Part 3).

**Competencies practiced.** CPA Evolution Core S2 M7 (materiality) and Core S1 M1 to M3; IMA Reporting and Control (financial recordkeeping and financial statement preparation); IFAC IES 2 (a) and IES 4 (a) (professional skepticism and judgment); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** The workbook with Requirements 1, 3 and 4 done, and `LenderPackage.sql` for the aging, returns and notes queries.
- **Data conditions.** No tax account exists, so the ledger's net income is also its income before income taxes. Only the first note existed at the end of {{ d.P }}.
- **Verify first.** Each entry balances, and no line touches cash.

## How to run it

Individual or pairs, about 180 minutes: 60 for the schedule and entries, 25 for the classification, 35 for the reclassifications and passed items, 40 for materiality and the judgment, 20 for the checks. Hold back the reversal point until students have totaled the year-end balances. **Collect** the schedule and the Table.

{{ figure('IF-17-5-A') }}

## Step-by-step solution

### Part 1: Number each adjustment and write its entries

**Step 1. Put A1 to A4 on the schedule and write their entries.** One row for each adjustment, in the case's layout. A year's income effect is the amount at that year-end less the one before, because the earlier error reverses. Keep the entry lines in the AdjustmentLines Table, one row for each account and year-end, as debits less credits. The model's formulas: A1's effect on the last year's income, then four lines of the last year-end's entries (the {{ d.P }} accrual into retained earnings, the increase to `5080`, the credit to `2030`, the debit to receivables for the cutoff):

```jinja
{{ g.f.a1_c }}
{{ g.f.line_re }}
{{ g.f.line_cogs }}
{{ g.f.line_liab }}
{{ g.f.line_rev }}
```

**Check:** the effect of each adjustment on opening retained earnings, {{ d.P }} income and {{ d.C }} income is in the instructor note below; in total {{ sm(total.re) }}, {{ sm(total.P) }} and {{ sm(total.C) }}. A1 alone is {{ sm(a.A1.re) }}, {{ sm(a.A1.P) }} and {{ sm(a.A1.C) }}. **Watch for:** two errors. Taking each year-end's amount as the year's effect gives {{ sm(g.no_reversal) }} for {{ d.C }}, the equity effect, where the income effect is {{ sm(total.C) }}. Booking the whole payroll accrual in {{ d.C }} gives -${{ g.whole_a1|money }}, where only {{ sm(a.A1.C) }} is new.

**Step 2. Classify and assign a period.** A1, A2 and A4 correct errors: the facts existed at each year-end. A3 corrects errors only on its case assumption that the facts at each original preparation supported the release, and is otherwise a change in estimate of the year they became known. The errors are material to the {{ d.P }} statements the shareholders received, on the balance sheet at least, so present {{ d.P }} as restated, with the Topic 250 disclosures: opening retained earnings fall by ${{ (total.re|abs)|money }} and {{ d.P }} income by ${{ (total.P|abs)|money }}.

**Check:** adjusted income before income taxes is ${{ adj_ni_p|money }} for {{ d.P }} and ${{ adj_ni_c|money }} for {{ d.C }}.

### Part 2: Reclassifications and passed items

**Step 3. Record R1 and R2.** R1 moves the principal due within a year out of the long-term notes, for the notes originated by the year-end.

**Check:** ${{ cur_p|money }} at the end of {{ d.P }} (the first note only) and ${{ cur_c|money }} at the end of {{ d.C }}. **Watch for:** the next year's scheduled payments, which include interest: ${{ g.with_interest|money }}, not the principal. R2 nets the credit balance of `1090`, ${{ (-c1090_c)|money }} at the last year-end, into work in process (${{ wip_c|money }} before), because `1090` clears conversion cost into it; no income changes.

**Step 4. Measure P1 to P3 as candidates to pass.** P1 is an allowance at Exercise 8.1's rates on the open invoices, each taken by its first posting date.

```sql
-- Requirement 5: passed item P1, an allowance at Exercise 8.1's rates at each year-end
-- Population: the view OpenReceivables; rates 0.5%, 2%, 5%, 15%, 40%; expected: 34,634.79 (2025) and 34,106.25 (2026)
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

**Check:** P1 is {{ sm(p1) }} at the last year-end and {{ sm(p1_prior) }} a year earlier, so {{ sm(p1_income) }} on {{ d.C }} income. P2, the returns expected after the year-end, is estimated from the {{ p2.n }} returns made in {{ d.C }} on {{ d.P }}'s deliveries (${{ p2.rev|money }} of revenue less ${{ p2.cost|money }} of cost): {{ sm(p2.effect) }}. P1 and P2 are estimates, {{ sm(g.p12) }} together. P3, the full cost of the damaged returns restocked, {{ sm(p3.effect) }}, is an exposure, not a measured loss, until a count and a net realizable value review measure it. Together, {{ sm(aggregate) }} ({{ agg_share|pct(0) }} of materiality) is a screen, not a measured misstatement. **Watch for:** two errors. Letting the aging take in the opening receivable adds ${{ (g.with_opening - g.allowance)|money }} at the top rate, ${{ g.with_opening|money }} in all. And selecting by InvoiceDate takes in {{ late_posted|join(', ') }}, posted in {{ d.C }}, so the {{ d.P }} aging no longer equals `1020` less its opening line.

**For the instructor.** The rates are the case's assumptions, not GAAP's. ASU 2025-05 (prospective, {{ g.asu.effective }}) lets any entity assume, for current receivables and contract assets from Topic 606, that year-end conditions persist, and lets a private company also count later collections, disclosing the date used. Neither election removes the opening receivable from the assessment.

### Part 3: Materiality and the judgment

**Step 5. Compute materiality for each year.** Five percent of income before income taxes as the ledger records it (the model workbook's formula is `{{ g.f.mat }}`, with the recorded income in C6).

**Check:** ${{ mat_p|money }} for {{ d.P }} and ${{ mat_c|money }} for {{ d.C }}, and ${{ g.trivial|money }} as clearly trivial. **Watch for:** adjusted income as the base, which gives ${{ g.adjusted_mat|money }} and a circular rule.

**Step 6. Judge individually and in aggregate.** The effect on {{ d.C }} income, {{ sm(total.C) }}, is {{ share|pct(0) }} of materiality, but other grounds say record: the payroll liability alone, ${{ pay_c.total|money }}, exceeds materiality; current liabilities rise by ${{ rise|money }} before the reclassification and working capital falls by ${{ wc_fall|money }} after it; at the end of {{ d.P }} they were understated by ${{ under_p|money }}, above that year's materiality; and the error recurs every year. List P1 to P3 for approval as candidates to pass. List the freight residual, ${{ residual|money }}, as clearly trivial.

**Step 7. Show the adjusted trial balances balance and that no adjustment touches cash.** Add two columns to Working TB, the adjustment for each account and the adjusted balance:

```jinja
{{ g.f.adj }}
{{ g.f.adjusted }}
```

**Check:** the largest imbalance of any entry is zero, no line has account `1010`, and the adjusted statements follow in Requirement 6.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| A1 to A4: effect on income, {{ d.P }}; {{ d.C }} | {{ sm(total.P) }}; {{ sm(total.C) }} | 1 |
| Equity effect at the year-ends, {{ d.P }}; {{ d.C }} | {{ sm(equity_p) }}; {{ sm(equity_c) }} | 1 |
| Adjusted income before income taxes, {{ d.P }}; {{ d.C }} | ${{ adj_ni_p|money }}; ${{ adj_ni_c|money }} | 2 |
| Current portion of the notes, {{ d.P }}; {{ d.C }} | ${{ cur_p|money }}; ${{ cur_c|money }} | 3 |
| P1, P2, P3 and their combined screen | {{ sm(p1) }}; {{ sm(p2.effect) }}; {{ sm(p3.effect) }}; {{ sm(aggregate) }} | 4 |
| Materiality, {{ d.P }}; {{ d.C }} | ${{ mat_p|money }}; ${{ mat_c|money }} | 5 |

{{ expected() }}

## What a strong answer says

- **Classification.** Each entry typed by what the facts were at the year-end, and the assumption of A3 stated.
- **Periods.** Each year-end's amount reversing the one before, {{ d.P }} restated because the errors are material to the statements the shareholders received.
- **Judgment.** Materiality by size and other grounds, the recurring error noted, the estimates and the exposure listed apart.

A weak answer records or passes everything on the size of one year's income effect.

## Common mistakes and how to respond

- **No reversal.** *Symptom:* a {{ d.C }} income effect of {{ sm(g.no_reversal) }}. *Response:* ask what the {{ d.P }} entry already took out of retained earnings.
- **The whole accrual in one year.** *Symptom:* -${{ g.whole_a1|money }} in {{ d.C }}. *Response:* ask which part of it was owed at the end of {{ d.P }}.
- **Aging the opening line.** *Symptom:* an allowance of ${{ g.with_opening|money }}. *Response:* ask which bucket a balance with no invoice belongs to.
- **Size alone.** *Symptom:* "less than a third of materiality, so pass it." *Response:* ask what the liability does to working capital.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Schedule and entries | 30 | A1 to A4 numbered, entries for both year-ends, effects by year, in a Table | One year-end |
| Classification and periods | 20 | A reasoned type and period for each, {{ d.P }} restated or, with reasons, revised | Types without periods |
| Reclassifications and passed items | 20 | R1, R2 and P1 to P3 measured | Not described |
| Materiality and judgment | 20 | Both years; size and other grounds; aggregate | Size alone |
| Checks | 10 | Entries balance; no cash line | Not shown |

## Extensions and discussion questions

- Rebuild the schedule for the retained-liability answer to A3 and compare the two presentations of {{ d.P }}.
- Discuss: why does a recurring error of modest size deserve attention?
