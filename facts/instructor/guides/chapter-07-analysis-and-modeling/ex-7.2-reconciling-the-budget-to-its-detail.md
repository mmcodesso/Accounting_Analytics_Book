---
note: ch07.ex2
uses: [ch07.g2]
title: Reconciling the Budget to Its Detail
kind: exercise
number: '7.2'
unit: '7'
perspective: financial
tool: excel
minutes: 60
solution: "Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.2, with the queries BudgetSummary and BudgetLineAll"
figures: []
---
{% set g = ch07_g2 %}
# Exercise 7.2: Reconciling the Budget to Its Detail

{{ header() }}

## Purpose and learning outcomes

The Watch out of the chapter says that a summary does not always hold all of its detail. This exercise makes students prove it: two Power Query totals, a reconciliation by account and by year, and a memo that names the cause and the control. It practices Group By with several columns, a merge, a dynamic-array comparison and a short written finding. The analytics type is descriptive, with a diagnostic step in requirement 3.

By the end, students can:

- total a Table by two columns with **Group By** and attach account names with a merge (outcome 3);
- reconcile a summary to its detail by account and find what the differences have in common (outcome 3);
- write a finding that says which source to use and which control would have caught the problem (outcome 3).

**Competencies practiced.** CPA Evolution Core S1 M4 (financial statement analysis and performance measures) and Core S1 M8 T2 (financial data: extraction, transformation and cleansing); IMA Budgeting and Forecasting, and Data Literacy; IFAC IES 2 (b) and IES 3 (a); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, with the BudgetLine and Account queries of Tutorial 7.2. The model answer uses LET, VSTACK, HSTACK and XLOOKUP. VSTACK and HSTACK need a newer Excel than the tutorials do, as the chapter note says.
- **Data conditions.** The Budget Table (T76_Budget) summarizes the budget by cost center and account for {{ g.years[0].year }} to {{ d.N }}, so it has {{ g.summary_rows|count }} rows in {{ d.C }}. BudgetLine (T77_BudgetLine) holds every line. Only operating-expense lines can have a blank CostCenterID, and the accounts concerned are budgeted only that way, so they are missing from the summary altogether.
- **Verify first.** Run the comparison once. The gap is about one percent of the budget in every year, which is why a total-to-total glance at the summary would not alarm anyone.

## How to run it

Pairs or individual, about 60 minutes: 20 for the two queries (requirements 1 and 2), 15 for the comparison by account (3), 5 for the other years (4) and 20 for the memo (5). Hold back the blank-cost-center hint until a student has listed the differing accounts and has asked what they share. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The budget summary

**Step 1. Import and group T76_Budget.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx, select the **T76_Budget** Table in the **Navigator** and click **Transform Data**. Name the query `BudgetSummary`.
b. Choose **Transform > Group By** and **Advanced**. Group by FiscalYear and AccountID, and add the aggregation Sum of BudgetAmount, named BudgetAmount. The model answer adds a row count named Rows, which students may skip.
c. Choose **Home > Merge Queries**, merge with the Account query on AccountID with a left outer join, and expand AccountNumber and AccountName without the prefix.

**Check:** the query has {{ g.n_summary|count }} rows, one for each year and account. **Watch for:** **Group By** without **Advanced**, which offers one grouping column.

### Requirement (2): The budget lines

**Step 2. Import T77_BudgetLine again as BudgetLineAll.** Tutorial 7.2's BudgetLine query holds only {{ d.C }}.

a. Import **T77_BudgetLine** with **Transform Data** and name the query `BudgetLineAll`.
b. Filter BudgetCategory to clear **Balance Sheet**, which keeps Revenue, COGS and Operating Expense.
c. Group by FiscalYear and AccountID with the sum of BudgetAmount, as in Step 1.
d. Load both new queries together: **Close & Load To**, **Table**, **New worksheet**. The choice applies to both.

**Check:** the query has {{ g.n_detail|count }} rows. **Watch for:** the Balance Sheet category left in, which makes the detail total far larger than the summary's and the difference many times the real gap.

### Requirement (3): The comparison and the cause

**Step 3. Total both queries for {{ d.C }}.** On a worksheet named `Ex 7.2` type the year in B2 in blue, then:

```
=SUMIFS(BudgetSummary[BudgetAmount],BudgetSummary[FiscalYear],$B$2)
=SUMIFS(BudgetLineAll[BudgetAmount],BudgetLineAll[FiscalYear],$B$2)
=ROUND(B5-B4,2)
```

**Check:** ${{ summary|money }} against ${{ detail|money }}, a difference of ${{ gap|money }}.

**Step 4. Compare by account.** List every account that appears in either query once, with its two totals and the difference, rounded to the cent. The model answer builds the list of account IDs with one formula, in A13:

```
=LET(ids,UNIQUE(VSTACK(FILTER(BudgetSummary[AccountID],BudgetSummary[FiscalYear]=$B$2),FILTER(BudgetLineAll[AccountID],BudgetLineAll[FiscalYear]=$B$2))),SORTBY(ids,XLOOKUP(ids,Account[AccountID],Account[AccountNumber])))
```

It adds the two totals with SUMIFS and `=ROUND(E13#-D13#,2)`, then lists the rows whose difference is not zero with `FILTER(...,ABS(F13#)>0.005)`.

**Check:** {{ g.accounts_union|count }} accounts in all, {{ accounts|length }} of them with a difference, each missing from the summary entirely. **Watch for:** a difference left unrounded. The two sums differ by a fraction of a cent on accounts that agree, so every account looks different.

**Step 5. Find what the differences share.** Open Tutorial 7.2's BudgetLine query and count the rows of these accounts with no cost center, and total their BudgetAmount:

```
=COUNTIFS(BudgetLine[CostCenterID],"")
=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[CostCenterID],"")
```

**Check:** {{ blank_rows|count }} rows, twelve months for each of {{ accounts|length }} accounts, totaling ${{ gap|money }}, the whole gap.

### Requirement (4): The other years

**Step 6. Repeat for each year.** Put {{ d.F }}, {{ d.P }} and {{ d.C }} in D5:D7 and total both queries by year, with the difference rounded.

**Check:** the differences are ${{ earlier[0][1]|money }} in {{ earlier[0][0] }}, ${{ earlier[1][1]|money }} in {{ earlier[1][0] }} and ${{ gap|money }} in {{ d.C }}.

### Requirement (5): The memo

**Step 7. Write it.** An outline: to the controller; the two totals and the difference; the cause, with the evidence of Step 5; the same gap in every year; which Table the bank's summary should come from; one control.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Budget Table total, {{ d.C }} | ${{ summary|money }} | 3 |
| Budget lines (revenue, COGS, operating expense) | ${{ detail|money }} | 3 |
| Difference | ${{ gap|money }} | 3 |
| Rows of the Budget Table in {{ d.C }}; BudgetLine rows with no cost center | {{ rows|count }}; {{ blank_rows|count }} | 3, 5 |
{% for n, name, amount in accounts %}
| Difference on {{ n }} {{ name }} | ${{ amount|money }} | 4 |
{% endfor %}
{% for y, x in earlier %}
| Difference, {{ y }} | ${{ x|money }} | 6 |
{% endfor %}

{{ expected() }}

## What a strong answer says

- **Requirement (3).** The differing accounts, the common feature (no cost center, operating expense, twelve months) and the fact that every other account agrees to the cent.
- **Requirement (5).** The two totals and the difference in the first paragraph, the cause in the second, and a recommendation that names the source for the bank (BudgetLine, or the summary after the unassigned lines are assigned) and a control: reconcile the summary to the detail by year and account, with a zero-difference check, review and sign-off before a summary leaves the company, and a cost center required on every line or an Unassigned cost center that reaches the summary. It says the effect: budgeted operating expenses are understated and budgeted profit overstated by about ${{ g.years[2].gap|money }} a year.

A weak answer calls the gap an error without saying where it comes from, or recommends fixing the numbers once with no control.

## Common mistakes and how to respond

- **Balance Sheet lines left in.** *Symptom:* a difference many times the gap. *Response:* ask which categories the summary contains.
- **Group By without Advanced.** *Symptom:* totals by year, no accounts. *Response:* ask how many columns the question groups by.
- **A comparison by year only.** *Symptom:* the gap found, the cause missed. *Response:* ask which accounts it is made of.
- **Unrounded differences.** *Symptom:* every account differs by a tiny amount. *Response:* ask what the cent is for in a reconciliation.
- **A memo without a control.** *Symptom:* "fix the Budget Table". *Response:* ask what would have caught it last year.
- **Blaming the budget.** *Symptom:* "the budget is wrong". *Response:* ask whether the lines or the summary are incomplete.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: BudgetSummary | 15 | Grouped by year and account, names merged | Names missing |
| Requirement 2: BudgetLineAll | 15 | Balance Sheet excluded, grouped as in 1 | Categories wrong |
| Requirement 3: comparison and cause | 30 | Differing accounts listed, blank cost center named, rows counted | The difference without the cause |
| Requirement 4: other years | 10 | All three years, differences rounded | One year missing |
| Requirement 5: memo | 30 | Totals, cause, source, effect and control | Control missing |

## Extensions and discussion questions

- Reconcile by cost center and month as well. Where else does the summary diverge from the detail?
- Compare {{ d.N }} the same way. Is the gap still there?
- Discuss: who should own the monthly reconciliation, the staff that prepares the budget or someone independent of it?
- Discuss: the covenant report to the bank used this summary. Does the gap change what the controller tells the bank about last year's report?
