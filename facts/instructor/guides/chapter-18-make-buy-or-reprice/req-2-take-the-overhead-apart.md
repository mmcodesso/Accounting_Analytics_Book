---
note: ch18.r2
uses: [ch18.g2]
title: Take the overhead apart (Chapters 7, 10, and 11)
kind: requirement
number: '2'
unit: '18'
perspective: managerial
tool: mixed
minutes: 150
solution: "Chapter18-capstone-sql.zip: MakeBuy.sql, the queries headed Requirement 2 (Q10 to Q14); Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Cost Behavior"
figures:
  - id: IF-18-2-B
    kind: chart
    purpose: Two scatter plots that show the finding before any regression is run.
    shows: "Two panels with the standard hours completed each month on the horizontal axis, February to the last month of the data. Left: the Factory Overhead entries with the fitted line rising. Right: the payroll to 1090 with a flat fitted line and the six three-pay-date months marked. The start-up month is plotted apart from the line in both."
    data: The monthly extract of Q14 (Factory Overhead, Payroll, StandardHours, PayDates).
---
{% set g = ch18_g2 %}
# Requirement 2: Take the overhead apart (Chapters 7, 10, and 11)

{{ header() }}

## Purpose and learning outcomes

"Overhead at a third of its cost" compares totals and leaves cost behavior open, and behavior is tested, not assumed. SQL extracts what flowed into account `1090` and what the standards released from it, because the extract must tie to the ledger; the regressions go in the workbook, as in Chapter 7, where the reasoning shows. The analytics type is diagnostic.

Students can:

- split the year's inputs to `1090` by source and by type of pay, tie them to the ledger, and state them per standard hour (Part 1);
- build monthly series that can be tested and say what the start-up month and the three-pay-date months do to a test (Part 2);
- classify each input as varying with output, committed, or neither, with evidence, and say what the evidence does not prove (Part 3).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Reporting and Control (cost accounting) and Strategic Cost Management; IFAC IES 2 (b); AACSB A5 part 5.1 (SQL and Excel).

## Before you assign

- **Files.** MakeBuy.sql on CharlesRiver_Capstone.sqlite and Make Buy Reprice.xlsx; Requirement 1's results are not needed.
- **Data conditions.** The debits to `1090` are payroll, Factory Overhead entries, depreciation and the debits that favorable closes post back. Payroll posts on its pay dates with no month-end accrual, so some months carry a third payroll. The start-up month posted no payroll to `1090` (its one payroll went to `5080`). One completion is dated in another year than its credit posts.
- **Verify first.** Q10 sums to ${{ payroll|money }}, the payroll posted to `1090`, and Q11 to ${{ inputs|money }}.

## How to run it

Pairs, about 150 minutes: 30 for the extracts, 20 for the per-hour table, 35 for the monthly extract, 30 for the tests, 35 for the classification. Routine for each query: type it, select it, **Execute all/selected SQL**, read the pane. Hold back the pay-date grouping until the parts fail to tie, and the test window until January distorts a line. **Collect** the script and the Cost Behavior sheet.

## Step-by-step solution

### Part 1: The year's inputs against what completions released

**Step 1. Extract the payroll lines.** Q10 groups the Manufacturing registers' lines by type and by the labor type of the time behind them, leaving out the employees' deductions.

```sql
-- Requirement 2, Q10: the inputs to 1090 from payroll, by line type and labor type
-- Population: Manufacturing payroll lines of 2026, deductions left out; expected: the PayrollSummary debits
SELECT prl.LineType, COALESCE(lte.LaborType, '') AS LaborType,
    ROUND(SUM(prl.Hours), 2) AS Hours,
    ROUND(SUM(prl.Amount), 2) AS Amount
FROM PayrollRegisterLine AS prl
    INNER JOIN PayrollRegister AS pr
        ON pr.PayrollRegisterID = prl.PayrollRegisterID
    INNER JOIN PayrollPeriod AS pp
        ON pp.PayrollPeriodID = pr.PayrollPeriodID
    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
    LEFT JOIN LaborTimeEntry AS lte
        ON lte.LaborTimeEntryID = prl.LaborTimeEntryID
WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = 2026
    AND prl.LineType NOT IN ('Benefits Deduction',
        'Employee Tax Withholding')
GROUP BY prl.LineType, lte.LaborType
ORDER BY CASE prl.LineType
        WHEN 'Regular Earnings' THEN 1
        WHEN 'Overtime Earnings' THEN 2
        WHEN 'Salary Earnings' THEN 3
        WHEN 'Employer Payroll Tax' THEN 4
        ELSE 5 END,
    lte.LaborType;
```

**Check:** seven rows (regular and overtime earnings, direct and indirect, salaries, employer tax and benefits) totaling ${{ payroll|money }}.

**Step 2. Extract the debits to 1090 by source.** Q11 groups them by the journal entry's type (or the source document's type) and leaves out the closes. **Check:** three rows, payroll ${{ payroll|money }}, Factory Overhead ${{ foh|money }} and depreciation ${{ dep|money }}, ${{ inputs|money }} in all. **Watch for:** leaving the favorable closes' debits in: the total grows by ${{ g.closes_extra|money }}.

**Step 3. Set the inputs against what completions released, per standard hour.** Q12 returns the standard hours completed, the standard cost released by part and the credits to `1090`. Paste Q10, Q11 and Q12 into the workbook as the Tables PayrollLines, Debits1090 and Released, name the cell that holds Released's StandardHours `StdHours` (`=Released[StandardHours]`), and divide each input by it (`=C20/StdHours`). **Check:** {{ stdh|num(2) }} standard hours; released ${{ conv_rate|num(2) }} an hour (labor ${{ labor_rate|num(2) }}, overhead ${{ oh_rate|num(2) }}); actual inputs ${{ actual_rate|num(2) }}; actual overhead (the inputs less the direct earnings) ${{ actual_oh_rate|num(2) }}, {{ times|num(2) }} times the overhead applied, so the applied overhead is {{ third|pct(0) }} of it: the CFO's "a third", a comparison of totals that says nothing yet about behavior. The credits exceed the completion lines by ${{ off.amount|money }}: completion {{ off.number }} is dated {{ off.date }} and posted {{ off.posted }}. Name it as a date exception; it is not rounding.

### Part 2: The monthly extract and the tests

**Step 4. Extract each input by month.** The ledger posts payroll on the pay date, so the payroll lines are grouped by the month of the pay date, and the parts then add up to the posted payroll in every month. Q14 builds `Made` (standard hours by completion month), `Posted` (the 1090 debits by posting month, with the pay dates counted) and `Paid`. The block is a fragment, the first part of `Paid`, and its other six sums repeat the CASE for the other lines; run the complete Q14 from the script.

```sql
Paid AS (
    SELECT strftime('%Y-%m', pp.PayDate) AS Month,
        SUM(CASE WHEN prl.LineType = 'Regular Earnings'
                AND lte.LaborType = 'Direct Manufacturing'
            THEN prl.Amount ELSE 0 END) AS DirectRegular,
```

**Check:** {{ g.n_q14|count }} rows from the start-up month; {{ three|length|count }} months show three pay dates ({{ g.three|join(', ') }}). **Watch for:** grouping by the month of the period's end. The direct regular earnings then correlate {{ g.r_dreg_alt|num(2) }} with output, which reads as "direct labor is variable", and the parts no longer tie to the ledger (largest monthly gap ${{ g.gap_alt|money }}).

**Step 5. Test which inputs move with output, from the second month on.** Paste Q14 as a Table named Monthly, whose Month column is YYYY-MM text, and put the first month of the test in one cell named TestFrom, the second month, read from the Table itself (`=INDEX(Monthly[Month],2)`), so that both are text and the comparison with `Monthly[Month]` selects the months. A date typed in TestFrom is a different type and selects none. Regress each series on StandardHours over the months from TestFrom, with SLOPE, INTERCEPT, CORREL and RSQ (the Data Analysis ToolPak's regression is equally acceptable):

```jinja
{{ g.f.slope }}
{{ g.f.correl }}
```

**Check:** over {{ g.n_test|count }} months, the Factory Overhead entries give r = {{ fo.r|num(3) }} and R Square {{ fo.r2|num(3) }}, with a slope of {{ fo.slope|num(2) }} an hour, about the rate the standards apply (the entries run at {{ fo_ratio[0]|num(3) }}, {{ fo_ratio[1]|num(3) }} and {{ fo_ratio[2]|num(3) }} of the overhead applied in the three years). Payroll to `1090` gives r = {{ pay.r|num(3) }}, R Square {{ pay.r2|num(3) }}: it does not move with output. **Watch for:**

- Including the start-up month: payroll reads r = {{ pay_start.r|num(3) }}, because one month low on both axes makes the line slope. The overhead line looks better still ({{ g.r_fo_start|num(3) }}), so nothing flags the error.
- Leaving out the {{ three|length|count }} months with three pay dates changes nothing important: the other {{ g.n_no3|count }} months give r = {{ g.r_no3|num(2) }}, still unrelated. Mark them anyway, since each carries a third payroll with no more output.
- Reading depreciation's r = {{ dep_fit.r|num(2) }} as a relation: it follows an asset schedule with three levels, so the sign is the schedule's.

### Part 3: Classify each input

**Step 6. Write a sentence for each input.** Test each part of payroll the same way (the rows below the payroll test), then classify. The model's sentences follow in the strong answer.

{{ figure('IF-18-2-B') }}

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Inputs to `1090`; released at standard | ${{ inputs|money }}; ${{ released_gl|money }} | 2, 3 |
| Inputs and released, per standard hour | ${{ actual_rate|num(2) }}; ${{ conv_rate|num(2) }} | 3 |
| Overhead applied as a share of actual overhead | {{ third|pct(0) }} | 3 |
| Factory Overhead r; payroll r; with the start-up month | {{ fo.r|num(3) }}; {{ pay.r|num(3) }}; {{ pay_start.r|num(3) }} | 5 |
| Months with three pay dates | {{ g.three|join(', ') }} | 4 |

{{ expected() }}

## What a strong answer says

| Input | Class | Evidence |
|---|---|---|
| Factory Overhead entries | Varies with output | r = {{ fo.r|num(2) }}, slope about the applied rate, ratios near one every year |
| Direct regular earnings | Committed while the crew is kept | r = {{ parts.dreg.r|num(2) }}, but the crew's hours are recorded as direct when there is work: direct and indirect regular pay together give r = {{ g.r_reg|num(2) }} |
| Indirect regular and overtime earnings | Committed | r = {{ parts.ireg.r|num(2) }} and {{ parts.iot.r|num(2) }}: they rise when direct time falls |
| Direct overtime | Neither | r = {{ parts.dot.r|num(2) }}: scheduled, not driven by output |
| Salaries, employer tax, benefits | Committed | r near zero; tax and benefits follow the pay they are charged on |
| Depreciation | Committed | The asset schedule, three levels |

The conclusion: the overhead the standards apply already covers the overhead that varies. The gap between inputs and standards is the crew and supervision, which do not move with output, plus depreciation, spread over a plant that runs well below its capacity (Requirement 3). Committed is conditional: while the crew is kept. Whether any of its pay would stop is a staffing decision that no correlation shows.

Three distinctions to hold. The ratio of applied to actual overhead shows an allocation shortfall and does not by itself explain it, so test behavior before explaining the shortfall or using it in a decision. A correlation describes how two series moved together and is not a cash saving. And Neither for direct overtime describes its observed relation to output, while the crew-kept case still assumes that the existing hourly crew's pay stays, so the future overtime and staffing plan must be validated before any pay is called avoidable.

## Common mistakes and how to respond

- **The closes' debits left in.** *Symptom:* inputs ${{ g.closes_extra|money }} too high. *Response:* ask what a favorable close posts to `1090`.
- **January in the test.** *Symptom:* payroll r = {{ pay_start.r|num(2) }}. *Response:* ask what one month low on both axes does to a slope.
- **Parts by the period's month.** *Symptom:* r = {{ g.r_dreg_alt|num(2) }} and parts that miss the ledger. *Response:* ask which date the ledger posts on.
- **Classifying by name.** *Symptom:* "direct labor is variable". *Response:* ask what the same crew's indirect pay did over the same months.
- **Depreciation's r read as behavior.** *Symptom:* "falls as output rises". *Response:* ask what the schedule did in those months.
- **The date exception called rounding.** *Symptom:* a difference of ${{ off.amount|money }} waved away. *Response:* find the completion dated in one year and posted in the next.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Extracts tied to the ledger | 30 | Payroll, sources and released cost; per standard hour; the date exception named | Totals without the tie |
| Monthly series and tests | 30 | Pay-date grouping; tests from the second month; start-up and three-pay-date months handled | Tests with January in, or parts that miss the ledger |
| Classification with evidence | 30 | Every input classified with its r and the limit of the claim | Classification by name, or evidence missing |
| Workbook | 10 | Monthly Table, named cells, documentation | Values without names |

## Extensions and discussion questions

- Regress payroll on the standard hours and the number of pay dates together (LINEST) and read the second coefficient.
- Repeat the tests on each year separately and say whether the classification holds.
- Discuss: if direct and indirect time are one crew, what does "direct labor is variable" mean for standard costing?
- Discuss: which comparison would show the cost of overhead that varies, if not a comparison of totals?
