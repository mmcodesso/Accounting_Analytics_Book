# Requirement 2: Take the overhead apart (Chapters 7, 10, and 11)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 2 |
| Perspective | Managerial accounting |
| Tools | More than one tool |
| Time | About 150 minutes |
| Solution file | Chapter18-capstone-sql.zip: MakeBuy.sql, the queries headed Requirement 2 (Q10 to Q14); Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Cost Behavior |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

"Overhead at a third of its cost" is a claim about cost behavior, and behavior is tested, not assumed. SQL extracts what flowed into account `1090` and what the standards released from it, because the extract must tie to the ledger; the regressions go in the workbook, as in Chapter 7, where the reasoning shows. The analytics type is diagnostic.

Students can:

- split the year's inputs to `1090` by source and by type of pay, tie them to the ledger, and state them per standard hour (Part 1);
- build monthly series that can be tested and say what the start-up month and the three-pay-date months do to a test (Part 2);
- classify each input as varying with output, committed, or neither, with evidence, and say what the evidence does not prove (Part 3).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Reporting and Control (cost accounting) and Strategic Cost Management; IFAC IES 2 (b); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** MakeBuy.sql on CharlesRiver_Capstone.sqlite and Make Buy Reprice.xlsx; Requirement 1's results are not needed.
- **Data conditions.** The debits to `1090` are payroll, Factory Overhead entries, depreciation and the debits that favorable closes post back. Payroll posts on its pay dates with no month-end accrual, so some months carry a third payroll. The start-up month posted no payroll to `1090` (its one payroll went to `5080`). One completion is dated in another year than its credit posts.
- **Verify first.** Q10 sums to $3,815,397.14, the payroll posted to `1090`, and Q11 to $5,427,932.83.

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

**Check:** seven rows (regular and overtime earnings, direct and indirect, salaries, employer tax and benefits) totaling $3,815,397.14.

**Step 2. Extract the debits to 1090 by source.** Q11 groups them by the journal entry's type (or the source document's type) and leaves out the closes. **Check:** three rows, payroll $3,815,397.14, Factory Overhead $1,308,869.06 and depreciation $303,666.63, $5,427,932.83 in all. **Watch for:** leaving the favorable closes' debits in: the total grows by $311,526.62.

**Step 3. Set the inputs against what completions released, per standard hour.** Q12 returns the standard hours completed, the standard cost released by part and the credits to `1090`. Paste it into the workbook with Q10 and Q11 and divide by the hours (`=C20/StdHours`). **Check:** 68,912.79 standard hours; released $47.40 an hour (labor $28.28, overhead $19.12); actual inputs $78.77; actual overhead (the inputs less the direct earnings) $50.67, 2.65 times the overhead applied, so the applied overhead is 38% of it: the CFO's "a third", a comparison of totals that says nothing yet about behavior. The credits exceed the completion lines by $0.59: completion PC-2026-014592 is dated 2024-05-30 and posted 2026-07-01. Name it as a date exception; it is not rounding.

### Part 2: The monthly extract and the tests

**Step 4. Extract each input by month.** The ledger posts payroll on the pay date, so the payroll lines are grouped by the month of the pay date, and the parts then add up to the posted payroll in every month. Q14 builds `Made` (standard hours by completion month), `Posted` (the 1090 debits by posting month, with the pay dates counted) and `Paid`, whose first part is shown; its other six sums repeat the CASE for the other lines.

```sql
Paid AS (
    SELECT strftime('%Y-%m', pp.PayDate) AS Month,
        SUM(CASE WHEN prl.LineType = 'Regular Earnings'
                AND lte.LaborType = 'Direct Manufacturing'
            THEN prl.Amount ELSE 0 END) AS DirectRegular,
```

**Check:** 36 rows from the start-up month; 6 months show three pay dates (2024-03, 2024-08, 2025-01, 2025-08, 2026-01, 2026-07). **Watch for:** grouping by the month of the period's end. The direct regular earnings then correlate 0.92 with output, which reads as "direct labor is variable", and the parts no longer tie to the ledger (largest monthly gap $128,723.72).

**Step 5. Test which inputs move with output, from the second month on.** Paste Q14 as a Table named Monthly and put the first month of the test in one cell (TestFrom, the second month). Regress each series on StandardHours over the months from TestFrom, with SLOPE, INTERCEPT, CORREL and RSQ (the Data Analysis ToolPak's regression is equally acceptable):

```
=SLOPE(FILTER(Monthly[FactoryOverhead],Monthly[Month]>=TestFrom),FILTER(Monthly[StandardHours],Monthly[Month]>=TestFrom))
=CORREL(FILTER(Monthly[StandardHours],Monthly[Month]>=TestFrom),FILTER(Monthly[FactoryOverhead],Monthly[Month]>=TestFrom))
```

**Check:** over 35 months, the Factory Overhead entries give r = 0.975 and R Square 0.951, with a slope of 19.66 an hour, about the rate the standards apply (the entries run at 1.001, 1.003 and 0.993 of the overhead applied in the three years). Payroll to `1090` gives r = 0.066, R Square 0.004: it does not move with output. **Watch for:**

- Including the start-up month: payroll reads r = 0.396, because one month low on both axes makes the line slope. The overhead line looks better still (0.983), so nothing flags the error.
- Leaving out the 6 months with three pay dates changes nothing important: the other 29 months give r = 0.20, still unrelated. Mark them anyway, since each carries a third payroll with no more output.
- Reading depreciation's r = -0.51 as a relation: it follows an asset schedule with three levels, so the sign is the schedule's.

### Part 3: Classify each input

**Step 6. Write a sentence for each input.** Test each part of payroll the same way (the rows below the payroll test), then classify. The model's sentences follow in the strong answer.

> **[Figure placeholder IF-18-2-B]** Two scatter plots that show the finding before any regression is run.
> Kind: chart · Shows: Two panels with the standard hours completed each month on the horizontal axis, February to the last month of the data. Left: the Factory Overhead entries with the fitted line rising. Right: the payroll to 1090 with a flat fitted line and the six three-pay-date months marked. The start-up month is plotted apart from the line in both. · Data: The monthly extract of Q14 (Factory Overhead, Payroll, StandardHours, PayDates). · Status: planned

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Inputs to `1090`; released at standard | $5,427,932.83; $3,266,422.54 | 2, 3 |
| Inputs and released, per standard hour | $78.77; $47.40 | 3 |
| Overhead applied as a share of actual overhead | 38% | 3 |
| Factory Overhead r; payroll r; with the start-up month | 0.975; 0.066; 0.396 | 5 |
| Months with three pay dates | 2024-03, 2024-08, 2025-01, 2025-08, 2026-01, 2026-07 | 4 |

> **Instructor notes, Requirement 2:** inputs to 1090 in fiscal 2026 (PayrollSummary, Factory Overhead and Depreciation entries; the favorable closes' debits excluded): direct labor regular 47,020.5 hours 1,253,247.29, overtime 17,105.1 hours 682,821.11; indirect regular 38,030.5 hours 1,011,567.67, overtime 3,306.0 hours 131,908.30; salaries 263,191.24; employer payroll tax 255,719.16; employer benefits 216,942.37 (payroll 3,815,397.14); Factory Overhead entries 1,308,869.06; depreciation 303,666.63; total 5,427,932.83. Released at standard (ProductionCompletion credits 3,266,422.54; completion lines 3,266,421.95; the 0.59 between them is PC-2026-014592, a completion dated 2024-05-30 whose credit posted on 2026-07-01, a date exception to name in the bridge, not rounding): labor 1,948,859.23, variable overhead 746,606.73, fixed overhead 570,955.99, on 68,912.79 standard hours: 47.40 per standard hour (labor 28.28, overhead 19.12). Actual: 78.77 per standard hour; overhead (inputs less direct earnings of 1,936,068.40) 3,491,864.43, 50.67 per standard hour, 2.65 times applied: the CFO's "a third" is 0.38, a comparison of totals that does not say what the overhead that varies costs. Behavior, 35 months February 2024 to December 2026, on standard hours completed (payroll by its pay dates, the other inputs by posting date): Factory Overhead entries slope 19.66, intercept -3,122, r 0.975, R-squared 0.951 (variable, at about the applied rate: their ratio to applied overhead is 1.001, 1.003, 0.993 by year); payroll to 1090 slope 3.06, intercept 268,143, r 0.066, R-squared 0.004, but its parts move differently: direct regular earnings r 0.676 (slope 17.08), indirect regular -0.463, indirect overtime -0.449, direct overtime 0.078, salaries 0.027, employer tax 0.066, benefits 0.067. That is consistent with the same crew's hours being recorded as direct when there is work and as indirect when there is not, so its total pay does not move with output. The crew is a committed capacity cost while it is kept; whether any of its pay would stop is a staffing decision that no correlation shows, and the direct earnings' r does not make them a variable rate. With January 2024, payroll's r is 0.396: the start-up month posted no payroll and no Factory Overhead entry to 1090 (its one payroll, 11,520.94 on 2024-01-19, went to 5080), only 20,875.00 of depreciation, on 491 standard hours, a point low on both axes that alone makes payroll look as if it moved with output. Depreciation follows its schedule (24,625.00; 26,958.33 in February to May; 24,458.33 from June 2026), a committed equipment cost, and its r of -0.515 is spurious. The months with three pay dates (2024-03, 2024-08, 2025-01, 2025-08, 2026-01, 2026-07) carry a third payroll with no more output: compare by pay period, or mark them, before reading a slope. Conclusion: the overhead the standards apply already covers the overhead that varies; the gap is the crew and supervision, which do not move with output, plus depreciation, spread over a plant that runs well below its capacity. So the products are not "under-costed" by the variable overhead rate; the question is what the committed capacity is for.

## What a strong answer says

| Input | Class | Evidence |
|---|---|---|
| Factory Overhead entries | Varies with output | r = 0.98, slope about the applied rate, ratios near one every year |
| Direct regular earnings | Committed while the crew is kept | r = 0.68, but the crew's hours are recorded as direct when there is work: direct and indirect regular pay together give r = 0.12 |
| Indirect regular and overtime earnings | Committed | r = -0.46 and -0.45: they rise when direct time falls |
| Direct overtime | Neither | r = 0.08: scheduled, not driven by output |
| Salaries, employer tax, benefits | Committed | r near zero; tax and benefits follow the pay they are charged on |
| Depreciation | Committed | The asset schedule, three levels |

The conclusion: the overhead the standards apply already covers the overhead that varies. The gap between inputs and standards is the crew and supervision, which do not move with output, plus depreciation, spread over a plant that runs well below its capacity (Requirement 3). Committed is conditional: while the crew is kept. Whether any of its pay would stop is a staffing decision that no correlation shows.

## Common mistakes and how to respond

- **The closes' debits left in.** *Symptom:* inputs $311,526.62 too high. *Response:* ask what a favorable close posts to `1090`.
- **January in the test.** *Symptom:* payroll r = 0.40. *Response:* ask what one month low on both axes does to a slope.
- **Parts by the period's month.** *Symptom:* r = 0.92 and parts that miss the ledger. *Response:* ask which date the ledger posts on.
- **Classifying by name.** *Symptom:* "direct labor is variable". *Response:* ask what the same crew's indirect pay did over the same months.
- **Depreciation's r read as behavior.** *Symptom:* "falls as output rises". *Response:* ask what the schedule did in those months.
- **The date exception called rounding.** *Symptom:* a difference of $0.59 waved away. *Response:* find the completion dated in one year and posted in the next.

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
