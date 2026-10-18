# Exercise 7.2: Reconciling the Budget to Its Detail

| | |
|---|---|
| Unit | Chapter 7: Forecasting, Budgeting, and What-If Analysis in Excel |
| Item | Exercise 7.2 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 60 minutes |
| Solution file | Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.2, with the queries BudgetSummary and BudgetLineAll |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The Watch out of the chapter says that a summary does not always hold all of its detail. This exercise makes students prove it: two Power Query totals, a reconciliation by account and by year, and a memo that names the cause and the control. It practices Group By with several columns, a merge, a dynamic-array comparison and a short written finding. The analytics type is descriptive, with a diagnostic step in requirement 3.

By the end, students can:

- total a Table by two columns with **Group By** and attach account names with a merge (outcome 3);
- reconcile a summary to its detail by account and find what the differences have in common (outcome 3);
- write a finding that says which source to use and which control would have caught the problem (outcome 3).

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (financial data: extraction, transformation and cleansing); IMA Budgeting and Forecasting, and Data Literacy; IFAC IES 2 (b) and IES 3 (a); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, with the BudgetLine and Account queries of Tutorial 7.2. The model answer uses LET, VSTACK, HSTACK and XLOOKUP. VSTACK and HSTACK need a newer Excel than the tutorials do, as the chapter note says.
- **Data conditions.** The Budget Table (T76_Budget) summarizes the budget by cost center and account for 2024 to 2027, so it has 348 rows in 2026. BudgetLine (T77_BudgetLine) holds every line. Only operating-expense lines can have a blank CostCenterID, and the accounts concerned are budgeted only that way, so they are missing from the summary altogether.
- **Verify first.** Run the comparison once. The gap is about one percent of the budget in every year, which is why a total-to-total glance at the summary would not alarm anyone.

## How to run it

Pairs or individual, about 60 minutes: 20 for the two queries (requirements 1 and 2), 15 for the comparison by account (3), 5 for the other years (4) and 20 for the memo (5). Hold back the blank-cost-center hint until a student has listed the differing accounts and has asked what they share. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The budget summary

**Step 1. Import and group T76_Budget.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx, select the **T76_Budget** Table in the **Navigator** and click **Transform Data**. Name the query `BudgetSummary`.
b. Choose **Transform > Group By** and **Advanced**. Group by FiscalYear and AccountID, and add the aggregation Sum of BudgetAmount, named BudgetAmount. The model answer adds a row count named Rows, which students may skip.
c. Choose **Home > Merge Queries**, merge with the Account query on AccountID with a left outer join, and expand AccountNumber and AccountName without the prefix.

**Check:** the query has 84 rows, one for each year and account. **Watch for:** **Group By** without **Advanced**, which offers one grouping column.

### Requirement (2): The budget lines

**Step 2. Import T77_BudgetLine again as BudgetLineAll.** Tutorial 7.2's BudgetLine query holds only 2026.

a. Import **T77_BudgetLine** with **Transform Data** and name the query `BudgetLineAll`.
b. Filter BudgetCategory to clear **Balance Sheet**, which keeps Revenue, COGS and Operating Expense.
c. Group by FiscalYear and AccountID with the sum of BudgetAmount, as in Step 1.
d. Load both new queries together: **Close & Load To**, **Table**, **New worksheet**. The choice applies to both, so each query becomes its own worksheet Table named after it. Confirm both names in **Queries & Connections**, because the formulas below refer to them.

**Check:** the query has 140 rows. **Watch for:** the Balance Sheet category left in, which makes the detail total far larger than the summary's and the difference many times the real gap.

### Requirement (3): The comparison and the cause

**Step 3. Total both queries for 2026.** On a worksheet named `Ex 7.2` type the year in B2 in blue, and label A4:A6 `Budget summary`, `Budget detail` and `Detail less summary`. Enter the formulas below in B4, B5 and B6.

```
B4  =SUMIFS(BudgetSummary[BudgetAmount],BudgetSummary[FiscalYear],$B$2)
B5  =SUMIFS(BudgetLineAll[BudgetAmount],BudgetLineAll[FiscalYear],$B$2)
B6  =ROUND(B5-B4,2)
```

**Check:** $165,428,777.99 against $167,453,051.69, a difference of $2,024,273.70.

**Step 4. Compare by account.** List every account that appears in either query once, with its two totals and the difference, rounded to the cent. Use the union of the account IDs of both queries, so that an account absent from the summary stays on the list. The model answer builds that list with one formula, in A13:

```
=LET(ids,UNIQUE(VSTACK(FILTER(BudgetSummary[AccountID],BudgetSummary[FiscalYear]=$B$2),FILTER(BudgetLineAll[AccountID],BudgetLineAll[FiscalYear]=$B$2))),SORTBY(ids,XLOOKUP(ids,Account[AccountID],Account[AccountNumber])))
```

It adds the two totals with SUMIFS and `=ROUND(E13#-D13#,2)`, then lists the rows whose difference is not zero with `FILTER(...,ABS(F13#)>0.005)`.

**Check:** 35 accounts in all, 14 of them with a difference, each missing from the summary entirely. **Watch for:** a difference left unrounded. The two sums differ by a fraction of a cent on accounts that agree, so every account looks different.

**Step 5. Find what the differences share.** Inspect the rows of these accounts in Tutorial 7.2's BudgetLine query, in the **Power Query Editor** or in its worksheet Table, where the blank CostCenterID cells show. Then close the editor and count the rows with no cost center, and total their BudgetAmount, with ordinary worksheet formulas and not Power Query custom columns:

```
=COUNTIFS(BudgetLine[CostCenterID],"")
=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[CostCenterID],"")
```

**Check:** 168 rows, twelve months for each of 14 accounts, totaling $2,024,273.70, the whole gap. The model answer keeps the two results in B9 and B10.

### Requirement (4): The other years

**Step 6. Repeat for each year.** Put 2024, 2025 and 2026 in D5:D7 and total both queries by year, with the difference rounded.

**Check:** the differences are $1,884,434.88 in 2024, $1,948,965.44 in 2025 and $2,024,273.70 in 2026.

### Requirement (5): The memo

**Step 7. Write it.** An outline: to the controller; the two totals and the difference; the cause, with the evidence of Step 5; the same omission pattern in every year, with each year's amount stated separately; which Table the bank's summary should come from; one control. The grand total of revenue, cost of goods sold and operating expense adds amounts of different kinds, so it is a completeness control and not a profit subtotal.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Budget Table total, 2026 | $165,428,777.99 | 3 |
| Budget lines (revenue, COGS, operating expense) | $167,453,051.69 | 3 |
| Difference | $2,024,273.70 | 3 |
| Rows of the Budget Table in 2026; BudgetLine rows with no cost center | 348; 168 | 3, 5 |
| Difference on 6070 Rent Expense - Warehouse | $288,065.60 | 4 |
| Difference on 6080 Rent Expense - Office | $216,179.72 | 4 |
| Difference on 6090 Utilities | $120,547.47 | 4 |
| Difference on 6100 Insurance | $53,709.73 | 4 |
| Difference on 6110 Office Supplies | $78,370.66 | 4 |
| Difference on 6120 Repairs and Maintenance | $126,338.75 | 4 |
| Difference on 6140 IT and Software | $71,904.86 | 4 |
| Difference on 6150 Marketing and Promotion | $359,842.35 | 4 |
| Difference on 6160 Travel and Entertainment | $114,548.06 | 4 |
| Difference on 6180 Professional Fees | $60,447.65 | 4 |
| Difference on 6190 Bank Fees | $42,077.99 | 4 |
| Difference on 6200 Miscellaneous Administrative | $96,328.87 | 4 |
| Difference on 6210 Warehouse Supplies | $107,611.71 | 4 |
| Difference on 6220 Research and Development | $288,300.28 | 4 |
| Difference, 2024 | $1,884,434.88 | 6 |
| Difference, 2025 | $1,948,965.44 | 6 |

> **Instructor notes, Exercise 7.2:** 2026 Budget Table total 165,428,777.99 (348 rows) against BudgetLine revenue, COGS, and operating-expense lines 167,453,051.69; difference 2,024,273.70. The difference is exactly the 168 operating-expense BudgetLine rows with a blank CostCenterID, twelve months for each of 14 accounts: 6070 Rent Expense - Warehouse 288,065.60; 6080 Rent Expense - Office 216,179.72; 6090 Utilities 120,547.47; 6100 Insurance 53,709.73; 6110 Office Supplies 78,370.66; 6120 Repairs and Maintenance 126,338.75; 6140 IT and Software 71,904.86; 6150 Marketing and Promotion 359,842.35; 6160 Travel and Entertainment 114,548.06; 6180 Professional Fees 60,447.65; 6190 Bank Fees 42,077.99; 6200 Miscellaneous Administrative 96,328.87; 6210 Warehouse Supplies 107,611.71; 6220 Research and Development 288,300.28. The Budget Table omits these accounts entirely. Gaps in earlier years: 2024 1,884,434.88; 2025 1,948,965.44. BudgetLine holds every budget line, so it is the source to use; a control is a monthly reconciliation of the summary to the detail with a zero-difference check.

## What a strong answer says

- **Requirement (3).** The differing accounts, the common feature (no cost center, operating expense, twelve months) and the fact that every other account agrees to the cent.
- **Requirement (5).** The two totals and the difference in the first paragraph, the cause in the second, and a recommendation that names the source for the bank (BudgetLine, or the summary after the unassigned lines are assigned) and a control: reconcile the summary to the detail by year and account, with a zero-difference check, review and sign-off before a summary leaves the company, and a cost center required on every line or an Unassigned cost center that reaches the summary.
- **A plus.** The effect of the gap on the budget as presented: budgeted operating expenses are understated and budgeted profit overstated by $2,024,273.70 in 2026, $1,884,434.88 in 2024 and $1,948,965.44 in 2025. These are differences in how the budget is presented, not evidence that recorded profit is misstated.

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
| Requirement 3: comparison and cause | 30 | Differing accounts listed, blank cost center named as the common feature | The difference without the cause |
| Requirement 4: other years | 10 | All three years, differences rounded | One year missing |
| Requirement 5: memo | 30 | Totals, cause, source and control | Control missing |

## Extensions and discussion questions

- Reconcile by cost center and month as well. Where else does the summary diverge from the detail?
- Compare 2027 the same way. Is the gap still there?
- Discuss: who should own the monthly reconciliation, the staff that prepares the budget or someone independent of it?
- Discuss: the covenant report to the bank used this summary. Does the gap change what the controller tells the bank about last year's report?
