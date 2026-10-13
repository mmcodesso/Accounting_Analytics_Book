---
note: ch19.r3
uses: [ch19.g3]
title: Assess the risks and set materiality (Chapters 6 and 8)
kind: requirement
number: '3'
unit: '19'
perspective: auditing
tool: excel
minutes: 120
solution: "Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheets Materiality and Risks (the Ledger Table feeds the formulas); Chapter19-capstone-sql.zip: Credits.sql, tests P1 and P2, the same rates and the same income in SQL"
figures:
  - id: IF-19-3-A
    kind: excel-mock
    purpose: The Materiality worksheet with the three thresholds and the expectation of returns, the end state of Parts 1 and 2.
    shows: "The top of the Materiality sheet: the parameter block with income, the three rates, overall materiality, performance materiality and the clearly trivial threshold in cells whose names are written beside them; below it the three-year block of revenue, returns and return rate, then the expectation, the recorded returns, the difference, the two comparisons and the conclusion text."
    data: The Materiality worksheet of Credits Audit.xlsx on the pinned dataset (income, thresholds, revenue and returns by year).
---
{% set g = ch19_g3 %}
# Requirement 3: Assess the risks and set materiality (Chapters 6 and 8)

{{ header() }}

## Purpose and learning outcomes

An audit plan keeps its parameters where every later test can read them. This requirement sets three thresholds from the chief audit executive's condition, uses them on a first analytical procedure, and turns the cycle's documents into a list of risks with a test, a tool and a place for the evidence. Excel fits because the parameters are cells that the evaluation of Requirement 8 reads again. The analytics type is predictive in a small way: the expectation assumes that the prior year's return rate still holds. The requirement is also where the case first says that what is tested is not what is exposed: the matrix plans the sample of Requirement 6.

Students can set materiality, performance materiality and a clearly trivial threshold in named cells (Part 1), build and judge an expectation (Part 2), and brainstorm fraud risks and map each to a control point, a test and its evidence (Part 3).

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance) and M7 (materiality); IMA Reporting and Control (internal control); IFAC IES 2 (f) and IES 4 (a); AACSB A5 part 5.2 (technology judgment, interpretation and communication).

## Before you assign

- **Files.** Credits Audit.xlsx with its Documentation sheet, and CharlesRiver.xlsx. Students build the Ledger Table with Power Query, or paste the results of the SQL tests P1 and P2 as values and say so on the sheet; the Table refreshes, the paste does not.
- **Data conditions.** The chart of accounts has no income tax account, so the income the ledger records is income before income taxes. The year-end closes post to every revenue and expense account and zero them. Fiscal {{ d.F }} had no earlier sales to return.
- **Verify first.** On the model workbook, the three threshold cells read ${{ mat|money }}, ${{ perf|money }} and ${{ trivial|money }}.

## How to run it

Individual, about 120 minutes: 35 for the Ledger Table and the thresholds, 30 for the expectation, 25 for the brainstorm, 30 for the matrix. Hold back the clearly trivial comparison until the student states what the difference means. **Collect** the workbook with its named cells.

## Step-by-step solution

### Part 1: The thresholds

**Step 1. Load the Ledger Table.** In the model workbook the ledger is a summary Table that every formula reads.

a. Choose **Data > Get Data > From File > From Excel Workbook**, select T3_GLEntry in CharlesRiver.xlsx and choose **Transform Data**, never Load.

b. Filter PostingDate to dates before the year after the last fiscal year, and keep the columns AccountID, Debit, Credit, VoucherNumber, SourceDocumentType and FiscalYear.

c. Merge the account (AccountNumber, AccountName, AccountType) and, on VoucherNumber and EntryNumber, the journal entry (EntryType), expanding without the prefix.

d. Choose **Add Column > Custom Column** named IsYearEndClose:

```jinja
{{ g.iyec }}
```

e. Choose **Transform > Group By**, then **Advanced**: by FiscalYear, AccountNumber, AccountName, AccountType, SourceDocumentType and IsYearEndClose, summing Debit and Credit and counting rows. Choose **Close & Load To**, select **Table** and **New worksheet**, and name the sheet Ledger.

**Check:** the Ledger Table has {{ g.ledger_rows }} rows. **Watch for:** loading the ledger before filtering it, and keeping the closes as ordinary rows without the flag.

**Step 2. Set the thresholds.** On the Materiality sheet, B4 is income before income taxes, as the ledger records it, for the last fiscal year; B5 is the typed rate; B6 is `=B4*B5`. Performance materiality and the clearly trivial threshold repeat the pattern with their own rates. Select each result cell, click the **Name Box**, type Materiality, PerformanceMateriality or ClearlyTrivial, and press Enter.

```jinja
{{ g.f_income }}
```

The SQL cross-check, test P2, takes the same base straight from the ledger:

```sql
-- Requirement 3, test P2: income before income taxes as recorded (the base of materiality)
-- Population: revenue and expense postings, closes left out (no tax account); expected: one row a year
SELECT gl.FiscalYear,
    ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS IncomeBeforeTaxes
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE a.AccountType IN ('Revenue', 'Expense')
    AND gl.FiscalYear BETWEEN 2024 AND 2026
    AND gl.VoucherNumber NOT IN (
        SELECT EntryNumber
        FROM JournalEntry
        WHERE EntryType LIKE 'Year-End Close%')
GROUP BY gl.FiscalYear
ORDER BY gl.FiscalYear;
```

**Check:** income ${{ income|money }}; materiality ${{ mat|money }}; performance materiality ${{ perf|money }}; clearly trivial ${{ trivial|money }}. **Watch for:**

- The closes left in. Revenue and expenses then net to zero in every year, so materiality reads `{{ 0|money }}`.
- A threshold typed into a later formula. Change the rate in B5 and the Deficiencies sheet no longer follows.

### Part 2: The expectation of returns

**Step 3. Build the return rate.** For each year, revenue is the credits less the debits that sales invoices posted to the product and service revenue accounts; returns are the debits to `4060` without the closes; the rate is their quotient. Revenue repeats the pattern of B4 with SUMIFS and the revenue account numbers as an array constant, and the rate is simply:

```jinja
{{ g.f_rate }}
```

**Check:** rates {{ rates[0]|pct(3) }}, {{ rates[1]|pct(3) }} and {{ rates[2]|pct(3) }}; SQL test P1 returns the same three rows.

**Step 4. Expect, compare, conclude.** The expectation is the last year's revenue times the previous year's rate; the difference is the recorded returns less the expectation, set against the two thresholds.

```jinja
{{ g.f_exp }}
{{ g.f_concl }}
```

{{ figure('IF-19-3-A') }}

**Check:** expected ${{ exp|money }} against ${{ actual|money }} recorded, a difference of ${{ diff|money }} ({{ diff_pct|pct(1) }}); the conclusion text reads "Investigate (Requirement 5)". **Watch for:**

- Comparing the difference with overall materiality: it is {{ g.mat_ratio|pct(0) }} of it, so "immaterial" tempts. Materiality is not the test for investigating; the clearly trivial threshold is, and the difference is above it and below performance materiality.
- The first year's rate. It gives an expectation of ${{ exp_f|money }} and recorded returns {{ f_pct|pct(1) }} above it, because the first year had no earlier sales to return, so its rate understates.

### Part 3: Risks and the matrix

**Step 5. Brainstorm the fraud risks.** For each scheme of the chapter's table ({{ g.brainstorm|join(', ') }}), the Risks sheet records who could commit it, the documents, the incentive, the opportunity in the records, the rationalization, the traces and the test. The opportunity column is where the map pays off: customer service records {{ g.facts[2]|count }} receipts, makes {{ g.facts[3]|count }} applications, approves {{ g.facts[4] }} credits and {{ g.facts[5] }} clawbacks, and {{ g.facts[0] }} people approve every refund, with no preparer recorded.

**Step 6. Build the risk-and-control matrix.** One row for each risk: the risk, the assertion, the control point, the control expected, the test, the tool, whether the evidence lies in the database or outside it, the result and the rating. The sheet has {{ g.matrix_rows }} rows and rates the processes {{ g.ratings[0][0] }} {{ g.ratings[0][1] }}, {{ g.ratings[1][0] }} {{ g.ratings[1][1] }}, {{ g.ratings[2][0] }} {{ g.ratings[2][1] }} and {{ g.ratings[3][0] }} {{ g.ratings[3][1] }}. A last cell checks that every control point appears:

```jinja
{{ g.f_cover }}
```

**Check:** the cell reads {{ g.covered }}. **Watch for:** a rating by amount alone (the clawbacks total {{ g.claw_share|pct(1) }} of materiality yet are part of pay), and a Tool column that says SQL throughout, which leaves the evidence outside the database unplanned.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Income; materiality; performance; clearly trivial | ${{ income|money }}; ${{ mat|money }}; ${{ perf|money }}; ${{ trivial|money }} | 2 |
| Return rate by year | {{ rates[0]|pct(3) }}; {{ rates[1]|pct(3) }}; {{ rates[2]|pct(3) }} | 3 |
| Expected; recorded; difference | ${{ exp|money }}; ${{ actual|money }}; ${{ diff|money }} | 4 |
| Control points covered by the matrix | {{ g.covered }} | 6 |

{{ expected() }}

## What a strong answer says

- **The base and the thresholds are right and visible:** income as the ledger records it, closes out, and three named cells that later formulas read.
- **The expectation is judged, not just computed.** The difference is above clearly trivial and below performance materiality: investigate (Requirement 5 finds where), neither accept nor conclude.
- **The brainstorm uses the records:** the incompatible duties of customer service, the refund approvers with no preparer.
- **The matrix plans the audit:** each risk has a control point, a test, a tool and where the evidence lies, rated by likelihood and magnitude.

A weak answer takes revenue or credits as the base, calls the difference immaterial, or rates by amount.

## Common mistakes and how to respond

- **The closes left in.** *Symptom:* materiality `{{ 0|money }}`. *Response:* ask what the closing entry does to income.
- **Difference against materiality.** *Symptom:* "immaterial, no work". *Response:* ask which threshold decides whether to look.
- **The first year's rate.** *Symptom:* a difference of {{ f_pct|pct(0) }}. *Response:* ask how many earlier sales the first year had.
- **Typed thresholds.** *Symptom:* later sheets disagree after a change. *Response:* ask where each formula reads the number.
- **A matrix of SQL.** *Symptom:* no row says the evidence is outside the database. *Response:* ask what a query cannot show about a refund.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Thresholds | 25 | Right base, three named cells | Right numbers typed in |
| Expectation | 25 | Rates, expectation, both comparisons, the reasoned conclusion | Numbers without the conclusion |
| Brainstorm | 20 | Five schemes, with opportunity from the records | Generic opportunities |
| Matrix | 30 | Nine points, tool and evidence location, ratings argued | Risks without tests or ratings |

## Extensions and discussion questions

- Recompute the expectation at the average of the first two years' rates and say whether the conclusion changes.
- Discuss: why does a difference below performance materiality still deserve work?
- Discuss: is an expectation of returns a test of controls or a substantive test?
