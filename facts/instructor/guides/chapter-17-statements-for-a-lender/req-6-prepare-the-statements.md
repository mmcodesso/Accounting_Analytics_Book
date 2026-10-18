---
note: ch17.r6
uses: [ch17.g6]
title: Prepare the statements (Chapter 6)
kind: requirement
number: '6'
unit: '17'
perspective: financial
tool: mixed
minutes: 180
solution: "Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheet Statements, built from the Tables WorkingTB and AdjustmentLines; Chapter17-capstone-pbi.zip: Charles River Lender Review, page Package Tests and the Tests 3 to 5 and Checks tabs; Chapter17-capstone-sql.zip: LenderPackage.sql, the two queries headed Requirement 6"
figures:
  - id: IF-17-6-A
    kind: excel-mock
    purpose: The statement of cash flows, where the adjustments must change no total.
    shows: "The cash flow block of the Statements worksheet: columns for the last year, the comparative year restated and each year as recorded; rows from net income to the change in cash and the two check rows, with the operating totals outlined."
    data: The cash flow quantities of the Expected results.
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = ch17_g6 %}
# Requirement 6: Prepare the statements (Chapter 6)

{{ header() }}

## Purpose and learning outcomes

This requirement turns Requirement 5's schedule into the four statements the bank reads and shows that the package agrees with itself. The cash flow statement is where a reviewer looks hardest: no adjustment moves cash or changes how a cash flow is classified, so they may change lines of the reconciliation but no total. The workbook builds the statements; the Review file tests them by recomputing the balances from the ledger. The analytics type is descriptive, with a diagnostic test.

Students can prepare classified balance sheets and statements of income from the adjusted balances (Part 1), roll equity forward with the corrected year labeled restated (Part 2), prepare cash flows by the indirect method while disclosing what moved no cash (Part 3), and test the package against the ledger in a second tool (Part 4).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts, and transactions); IMA Reporting and Control (financial statement preparation); IFAC IES 2 (a); AACSB A5 part 5.1 (technology integration: Excel and Power BI).

## Before you assign

- **Files.** The workbook with Requirements 1 to 5 done (WorkingTB, the AdjustmentLines Table), the Review project of Requirement 2, `LenderPackage.sql` and CharlesRiver.xlsx.
- **Data conditions.** No income tax account exists and no distribution was posted (`3040` is unused); depreciation is charged partly to `1090`, so it never reaches an expense line; in the two years presented, equipment financed by a note and a disposal with no proceeds occur only in {{ d.C }}.
- **Verify first.** Every entry balances and none touches `1010`. The AdjustmentLines Table holds {{ g.n_lines }} lines in {{ g.n_entries }} entries, with a totals row below.

## How to run it

Pairs, about 180 minutes: 50 for the balance sheets and income statements, 15 for equity, 50 for cash flows, 45 for the Review file, 20 for checks. Hold back the noncash entries until a student's sections fail to add up to the change in cash. **Collect** the Statements worksheet and the Review project.

## Step-by-step solution

### Part 1: Balance sheets and statements of income

**Step 1. Build the adjusted balance sheets.** On a worksheet named **Statements** give each year-end a column: {{ d.C }}, {{ d.P }} (restated) and, as the model does, {{ d.F }} (restated), the opening balances of {{ d.P }}, which as a classified column also needs R1's current portion at that year-end. Each line adds what WorkingTB records under its StatementLine to what the adjustment lines add at that year-end; liabilities and equity take the opposite sign. The model's formula for cash:

```jinja
{{ g.f.cash }}
```

**Check:** total assets ${{ s_c.ta|money }} and ${{ s_p.ta|money }}, equal to total liabilities and equity, so each check row is zero. **Watch for:** a retained earnings line without the year's net income, which the ledger has not closed. The check row then reads the income, ${{ i_c.ni|money }} for {{ d.C }}.

**Step 2. Build the statements of income by function.** Lay out operating revenue to net income by function, with the loss on disposals and an income taxes line marked not determined and shown as zero. Net income equals income before income taxes only if the tax expense is determined to be zero, so it is provisional.

**Check:** income before income taxes ${{ i_c.ni|money }} and ${{ i_p.ni|money }}, the recorded income plus the schedule's effect. **Watch for:** the loss on a disposal, a debit on a revenue-type account. Adding it instead of subtracting it overstates income by ${{ g.loss_double[d.C]|money }} in {{ d.C }}.

### Part 2: Changes in stockholders' equity

**Step 3. Roll equity forward from January 1, {{ d.P }}.** Columns for common stock, retained earnings and total. Start from retained earnings as previously reported: the {{ d.F }} trial balance leaves out its own close, so that is `3030` plus {{ d.F }} net income. Add the correction, then each year's net income and distributions (none). The model's first row:

```jinja
{{ g.f.re_reported }}
```

**Check:** ${{ reported|money }} as reported, {{ sm(correction) }} of correction, ${{ restated|money }} as restated; the year-end balances equal the balance sheets' (${{ s_p.re|money }} and ${{ s_c.re|money }}). **Watch for:** a roll-forward without the correction. Retained earnings then differ from the balance sheets by ${{ g.equity_gap|money }} at both year-ends.

### Part 3: Statements of cash flows

**Step 4. Build the indirect statement from the adjusted balances.** Start from adjusted net income, add back depreciation and the loss on disposals, and take the change in each working-capital line from the two adjusted balance sheets (receivables, inventories with `1090`, payables with goods received not invoiced, sales tax payable, accrued and other items). Add a column for each year as recorded. The model's depreciation line adds the expense account's depreciation to the Depreciation entries' debits to `1090`:

```jinja
{{ g.f.dep }}
```

Purchases paid in cash are additions less equipment financed by a note. The script's first Requirement 6 query gives the change in cash and interest paid by year, an independent check.

{{ figure('IF-17-6-A') }}

**Check:** {{ d.C }} operating {{ sm(cf_c.operating) }}, investing {{ sm(cf_c.investing) }}, financing {{ sm(cf_c.financing) }}, change in cash {{ sm(cf_c.cash) }}; {{ d.P }} {{ sm(cf_p.operating) }}, {{ sm(cf_p.investing) }}, {{ sm(cf_p.financing) }}, {{ sm(cf_p.cash) }}. Adjusted and recorded operating totals agree, as offsetting cash lines would too, so Step 8's test of the lines on `1010` is the proof that no adjustment moves cash. **Watch for:** three slips, each caught by the check row. Starting from recorded income leaves the sections ${{ g.start[d.C]|money }} short in {{ d.C }}; adding back only the expense account's depreciation, ${{ g.dep_1090[d.C]|money }} short; leaving out the loss, ${{ g.loss[d.C]|money }} short.

**Step 5. Disclose what moved no cash.** The script's second Requirement 6 query lists the investing events by FixedAssetEvent.FinancingType; read it by that column. In {{ d.C }} a ${{ g.noted|money }} acquisition was financed by a note and one disposal brought no proceeds, so neither is a cash flow; the {{ d.P }} disposal had proceeds, which belong to investing; the {{ d.F }} row falls before the years presented. Add interest paid, income taxes paid (none recorded) and the noncash equipment below the statement.

**Check:** interest paid ${{ cf_c.interest_paid|money }} and ${{ cf_p.interest_paid|money }}; {{ d.P }} purchases paid in cash ${{ cf_p.paid|money }}, proceeds ${{ cf_p.proceeds|money }}; no purchase in {{ d.C }}. **Watch for:** two errors. Reporting the note-financed equipment as a purchase puts ${{ g.noted|money }} in investing, and balancing it with a financing inflow reports cash that never arrived. Interest paid taken from the adjusted expense, ${{ g.interest_adjusted|money }}, is ${{ g.interest_gap|money }} too high: the interest accrual.

### Part 4: The Review file's tests

**Step 6. Load the adjustment lines beside the ledger.** In the Review file choose **Home > Get data > Excel workbook**, select the package workbook, choose the AdjustmentLines Table and **Transform Data**. Keep the columns the file reads, filter out the totals row, type YearEnd as a date and **Close & Apply**. In **Model view** relate AdjustmentLines[Account] to Account[AccountNumber] and AdjustmentLines[YearEnd] to Date[Date], Many to one, **Single**.

**Check:** {{ g.n_lines }} lines. **Watch for:** the totals row, which Power Query reads as one more row. The count reads {{ g.n_lines + 1 }} and an entry named Total appears in the matrix, while debits and credits, each ${{ g.totals_debit|money }} higher, still agree.

**Step 7. Add the measures and the Package Tests page.** Under **Modeling > New measure**:

```jinja
{{ g.d_amount }}
```

The page holds a card visual titled "{{ g.t_cards }}", a matrix of debits and credits by entry, two tables comparing adjusted income and total assets with the workbook, and an adjusted income matrix. Use **Format > Edit interactions** so that no visual filters another.

**Check:** the difference between adjusted income and the workbook's is zero for {{ d.P }} and {{ d.C }}. **Watch for:** without the relationship to Account the adjusted income is the ledger's, and the difference equals the effect on income, ${{ g.effect[d.C]|money }} in {{ d.C }}; with the adjustment added instead of subtracted it is ${{ g.sign_gap[d.C]|money }}.

**Step 8. Run Tests 3 to 5 and the Checks tab.** In **DAX query view** type Tests 3 to 5 at the end of the Tests tab and choose **Run** for each. Test 3 lists each entry's debits, credits and difference, and Test 5 sets adjusted income and total assets by year against the workbook. Test 4, on the measures of the Key Measures table's Package folder, reads:

```dax jinja
{{ g.test4 }}
```

**Check:** each entry nets to zero, no line is on cash, and adjusted income and total assets agree with the workbook; the {{ g.n_checks }} Checks rows of this requirement all agree. The project tests these numbers; how the page renders is visible only in Desktop.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Income before income taxes, {{ d.P }}; {{ d.C }} | ${{ i_p.ni|money }}; ${{ i_c.ni|money }} | 2 |
| Retained earnings, January 1, {{ d.P }}, restated | ${{ restated|money }} | 3 |
| Operating cash flow, {{ d.P }}; {{ d.C }} | {{ sm(cf_p.operating) }}; {{ sm(cf_c.operating) }} | 4 |

{{ expected() }}

## What a strong answer says

- **Statements.** Four statements that agree with one another, the corrected year labeled restated.
- **Cash flows.** Operating cash flow of {{ sm(cf_c.recorded_operating) }} in {{ d.C }}, as the ledger gives it, because no adjustment moves cash; the noncash equipment and the disposal without proceeds disclosed, not reported.
- **Review file.** Tests that fail loudly, and a stated limit: two accounts off by equal and opposite amounts leave a total unchanged.

A weak answer plugs the cash flow sections or skips the tests.

## Common mistakes and how to respond

- **Recorded income in the cash flows.** *Symptom:* sections ${{ g.start[d.C]|money }} short. *Response:* ask which income the adjusted balances produce.
- **Note-financed equipment as a purchase.** *Symptom:* investing of {{ sm(-g.noted) }}. *Response:* ask what cash left the company.
- **No correction in the equity roll-forward.** *Symptom:* retained earnings ${{ g.equity_gap|money }} off the balance sheets. *Response:* ask which balance the shareholders were given.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Balance sheets and income statements | 25 | Both years, classified, balanced, income equal to the schedule | One year, or a plug |
| Equity statement | 15 | Correction shown, restated labels, ties to the balance sheets | No correction |
| Cash flows | 30 | Sections add to the change in cash; adjusted equals recorded | Plugged sections |
| Noncash items and supplemental information | 10 | Disclosed and excluded | Reported as cash |
| Review file tests | 20 | Lines, relationships, measures, Tests 3 to 5, Checks agree | Page without tests |

## Extensions and discussion questions

- Rebuild the statements for the retained-liability answer to A3 (current ratio {{ k_c.cr|num(2) }} against {{ s_c.cr|num(2) }}) and compare the two presentations.
- Discuss: income of {{ sm(i_c.ni) }} against operating cash flow of {{ sm(cf_c.operating) }}. What does each tell the bank?
