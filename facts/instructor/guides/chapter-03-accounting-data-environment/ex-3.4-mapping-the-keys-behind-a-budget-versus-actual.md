---
note: ch03.ex4
uses: [ch02.ex4]
title: Mapping the Keys Behind a Budget-Versus-Actual Report
kind: exercise
number: '3.4'
unit: '3'
perspective: managerial
tool: conceptual
minutes: 75
solution: ''
figures:
  - id: IF-03-4-A
    kind: diagram
    purpose: The join path from the Budget table to the ledger, drawn as two tables that share four columns and no key.
    shows: Two table boxes side by side, Budget and GLEntry, each listing only the columns that matter (FiscalYear, Month or FiscalPeriod, CostCenterID, AccountID, and the amount). Four horizontal connectors pair FiscalYear with FiscalYear, Month with FiscalPeriod, CostCenterID with CostCenterID and AccountID with AccountID, drawn in one style (a line with round ends) and labeled as a match on four columns, not a key. Above and below, solid lines lead from each box to CostCenter and to Account, with crow's foot endpoints computed from the data, and the circle at the CostCenter end of the GLEntry line is marked. A note says that Month and FiscalPeriod hold the same month number under two names.
    data: The relationships of Steps 2 and 3 (the Budget and GLEntry columns, and the cardinality of the two cost center links).
---
# Exercise 3.4: Mapping the Keys Behind a Budget-Versus-Actual Report

{{ header() }}

## Purpose and learning outcomes

A budget-versus-actual report looks simple: two columns of numbers side by side. The keys behind it are not. The budget and the ledger share no key. They share four columns that name the same things under slightly different names, and the cost center is optional on one side. The exercise has students map those links before anyone builds the report, and test the one that the tables allow them to test. Exercise 2.4 asked whether the budget data could be trusted; this one asks how to connect it. The analytics type is descriptive, and the report it prepares is the first step toward a variance analysis.

By the end, students can:

- name the primary key of CostCenter and say whether the cost centers form a hierarchy (outcome 2);
- read the link from GLEntry to CostCenter at both ends and say what the optional end means for a report (outcome 3);
- compare Budget with BudgetLine, and choose the one to join to the ledger and say why (outcome 5);
- test that every budgeted account appears in the ledger, and say what a clean result does not show;
- write a short assessment of the join path and its gaps.

**Competencies practiced.** CPA Evolution BAR M10 (advanced data analytics, including data models and joins); IMA Data Literacy, and Budgeting and Forecasting; IFAC IES 2 (b), management accounting, and IES 2 (i), using information technology to analyze data; AACSB A5 part 5.2.

## Before you assign

- Students need CharlesRiver_Work.xlsx, Tutorial 2.2's PivotTable and lookup method, and Exercise 2.4, whose count of ledger entries with no cost center the exercise reuses. If students skipped it, give them the count from Step 2.
- The exercise relies on these conditions. CostCenter has {{ n_cc }} rows and no row names a parent. Budget has one row for each fiscal year, month, cost center and account, and every row names an account and a cost center that exist. GLEntry.CostCenterID is blank on {{ ch02_ex4.gl_blank|count }} of {{ ch02_ex4.gl_rows|count }} rows. GLEntry.FiscalPeriod is the month number, the same as Budget.Month. Every account in Budget has ledger rows. Every BudgetLine combination that names a cost center has its Budget row, and the {{ n_line_only }} expense accounts that only BudgetLine budgets carry no cost center.
- The scale: Budget has {{ budget_rows|count }} rows, BudgetLine {{ line_rows|count }} and GLEntry {{ ch02_ex4.gl_rows|count }}. Build the PivotTables of requirement (4) on the Budget and GLEntry worksheets, not on formulas copied to every row.

## How to run it

Individual work, with a short class comparison of requirement (3), where answers differ most. For about 75 minutes: 10 on the cost centers (requirement 1), 10 on the ledger link (requirement 2), 20 on Budget and BudgetLine (requirement 3), 20 on the test (requirement 4) and 15 on the assessment (requirement 5).

**Hints.** For requirement (1), ask which column would hold a parent and what it contains. For requirement (3), ask which table has one row for each of the report's rows, and what happens to a budget amount when one budget row meets many ledger rows. For requirement (4), remind them of Tutorial 2.2 Step 5. **Collect** the assessment and the two lists of accounts.

## Step-by-step solution

### Requirement (1): The primary key and the hierarchy

**Step 1. Open CostCenter and read its columns.** The primary key is CostCenterID. The other columns are CostCenterName, ParentCostCenterID, ManagerID and IsActive. Filter ParentCostCenterID for blanks.

| CostCenterID | Name | ManagerID |
|---:|---|---:|
{% for c in cc %}
| {{ c.id }} | {{ c.name }} | {{ c.manager }} |
{% endfor %}

**Check:** ParentCostCenterID is blank on all {{ n_cc }} rows, so the cost centers are a flat list and no cost center is part of another. ManagerID is a foreign key to Employee, a bridge key into Master Data. A report that rolls departments up into divisions cannot use ParentCostCenterID. The grouping has to be added, as a mapping table kept outside the database, and maintained. The chart of accounts is different: Account.ParentAccountID gives it a hierarchy. **Watch for:** a student who assumes ParentCostCenterID works like ParentAccountID without opening it.

### Requirement (2): The link from the ledger to the cost center

**Step 2. Read the relationship between GLEntry and CostCenter.** The foreign key is GLEntry.CostCenterID, which refers to CostCenter.CostCenterID.

**Check:** at the CostCenter end of the line the symbol is {{ gl_cc.parent_end }} (a circle and a bar): a ledger row has at most one cost center, and may have none. At the GLEntry end Figure 3.9 shows {{ gl_cc.child_end }}, and in this extract every cost center has ledger rows. A new cost center need not have any yet, so keep the diagram's reading apart from what the snapshot happens to contain. No cost center ID in the ledger is missing from CostCenter. The optional end matters: {{ ch02_ex4.gl_blank|count }} of {{ ch02_ex4.gl_rows|count }} ledger rows ({{ ch02_ex4.gl_blank_share|pct(1) }}) have no cost center, mostly on balance sheet accounts, as Exercise 2.4 counted. A report by cost center leaves them out, so its total is not the ledger's total unless an unassigned line carries the rest. **Watch for:** blanks called orphans. A blank is allowed here. An orphan is a value that is filled in and has no match.

### Requirement (3): Budget and BudgetLine

**Step 3. Compare the two budget tables.**

| | Budget | BudgetLine |
|---|---|---|
| Primary key | BudgetID | BudgetLineID |
| Foreign keys | CostCenterID, AccountID, ApprovedByEmployeeID | AccountID, CostCenterID, ItemID, WarehouseID, ApprovedByEmployeeID |
| One row is | One fiscal year, month, cost center and account | One detailed budget amount for a fiscal year, month and account, with the cost center, item and warehouse where they apply; BudgetCategory and DriverType give its kind and basis (no two rows share the six fields in this extract, an observed grain, not a declared one) |
| Rows | {{ budget_rows|count }} | {{ line_rows|count }} |
| Accounts | {{ n_budget_accounts }}, revenue and expense only | {{ n_line_accounts }}, in four categories |
| Blank cost center | None | {{ line_cc.blank|count }} rows |

The categories of BudgetLine:

| BudgetCategory | Accounts | Rows | Rows with no cost center |
|---|---:|---:|---:|
{% for c in line_cats %}
| {{ c.category }} | {{ c.accounts }} | {{ c.rows|count }} | {{ c.no_cc|count }} |
{% endfor %}

**Check:** for a comparison by cost center, account and month, use Budget. It has one row for each row of the report, at the grain the ledger can be summed to, and every Budget row is the sum of the BudgetLine rows with the same year, month, cost center and account. BudgetLine is more detailed (by item and warehouse), but it also holds balance sheet lines and operating expense lines with no cost center, which do not belong in a cost-center report. Budget leaves those operating expense lines out. Exercise 2.4 found ${{ ch02_ex4.extra_total|money }} of them in fiscal {{ ch02_ex4.year }}, on the {{ n_line_only }} expense accounts that only BudgetLine budgets. A report of all operating expense keeps them as an unassigned budget line, beside the ledger rows with no cost center.

Whichever table is chosen, the comparison needs both sides at the report's grain, so each is summarized to fiscal year, month, cost center and account before the two are combined, as the requirement says. Matched row to row, a Budget row repeats once for every ledger row of its month, cost center and account. The fiscal {{ year }} row for {{ fan.number }} {{ fan.name }} in {{ fan.cc }} for {{ fan.month }} meets {{ fan.n|count }} ledger rows, so its ${{ fan.amount|money }} would add up to ${{ fan.repeated|money }}. **Watch for:** a student who joins both budget tables to the ledger and counts the budget twice, and a budget joined to the ledger row by row.

### Requirement (4): Test the accounts

**Step 4. Test every budgeted account against the ledger.**

a. On **Budget**, insert a PivotTable with AccountID in **Rows**: {{ n_budget_accounts }} distinct accounts.
b. On **GLEntry**, insert a PivotTable with AccountID in **Rows**: {{ gl_accounts }} distinct accounts.
c. Beside the Budget list, use XLOOKUP or COUNTIFS to look each AccountID up in the ledger's list, and count the misses.

**Check:** all {{ in_gl }} budgeted accounts appear in the ledger, so no budget line refers to an account the ledger never uses. That is a clean result, and it needs recording. It shows less than it seems. It does not show that each budgeted month, cost center and account has actuals: {{ quiet }} of the {{ budget_year }} Budget rows of fiscal {{ year }} have no ledger row in the same month, cost center and account. And the test runs one way: the ledger has {{ n_unbudgeted }} revenue and expense accounts with no Budget rows, including {{ unbudgeted_first }}. The Budget rows of fiscal {{ next_year }} ({{ next_rows|count }} of them) have no actuals at all, because the ledger holds only supplier payments for that year. **Watch for:** the AccountID of the ledger tested against the AccountNumber of Account, and the two lists compared by eye.

### Requirement (5): Write the assessment

**Step 5. Outline half a page to one page.** A model assessment names the join path and then the gaps.

The join: Budget and GLEntry are not related by a key. Leave the year-end close entries out of the ledger. They are the {{ n_closes }} journal entries whose EntryType begins with Year-End Close, and their ledger rows are the GLEntry rows whose SourceDocumentType is JournalEntry and whose SourceDocumentID is one of their JournalEntryIDs. VoucherType reads only JournalEntry, and a filter on a Description containing "close" would also catch an ordinary depreciation entry, so use EntryType, and keep the ordinary adjusting entries. Then summarize its expense rows (debits less credits) to fiscal year, period, cost center and account, and match that summary to Budget on the four columns, FiscalYear to FiscalYear, Month to FiscalPeriod, CostCenterID to CostCenterID and AccountID to AccountID. Budget already has one row at that grain, and its revenue accounts fall outside an expense report. Keep the combinations found on one side only. Each table also relates to CostCenter and to Account through its own foreign keys.

{{ figure('IF-03-4-A') }}

The gaps: no cost center hierarchy; ledger rows with no cost center; budget lines with no cost center that Budget omits; accounts with ledger rows and no budget; budgeted combinations with no ledger row; no actuals for the next year; and the month stored under two names.

**Check:** the assessment states that the budget-to-ledger join is a match of two summaries at a shared grain and not a foreign key, names the accounts and periods in scope and the treatment of the closes, and gives each gap its effect on the report.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Cost centers; with a parent | {{ n_cc }}; 0 | Step 1 |
| Ledger rows with no cost center | {{ ch02_ex4.gl_blank|count }} of {{ ch02_ex4.gl_rows|count }} | Step 2 |
| Accounts in Budget; in BudgetLine | {{ n_budget_accounts }}; {{ n_line_accounts }} | Step 3 |
| BudgetLine rows with no cost center | {{ line_cc.blank|count }} | Step 3 |
| Budgeted accounts found in the ledger | {{ in_gl }} of {{ n_budget_accounts }} | Step 4 |
| Ledger accounts used | {{ gl_accounts }} | Step 4 |
| Revenue and expense accounts with ledger rows and no Budget rows | {{ n_unbudgeted }} | Step 4 |
| Budget rows of fiscal {{ year }} with a ledger row; without | {{ matched|count }}; {{ quiet|count }} | Step 4 |
| Most ledger rows one Budget row of fiscal {{ year }} meets; its amount so repeated | {{ fan.n|count }}; ${{ fan.repeated|money }} | Step 3 |

## What a strong answer says

- **Requirement (1).** The key, the finding that the cost centers have no hierarchy, and what that means for a roll-up.
- **Requirement (2).** The relationship read at both ends, the meaning of the optional end, and the count from Exercise 2.4.
- **Requirement (3).** Each table's keys and row, the accounts compared, Budget chosen with the reason, and both sides summarized to the grain before they are combined.
- **Requirement (4).** The test, the clean result, and what it does not show.
- **Requirement (5).** The join described as a match on four columns, with the scope, the closes and the gaps and their effects.

A weak answer assumes a hierarchy, calls the blanks orphans, joins both budget tables, joins the budget to the ledger row by row, or calls the clean result complete coverage.

## Common mistakes and how to respond

- **A hierarchy assumed.** *Symptom:* a roll-up by ParentCostCenterID. *Response:* ask them to read the column.
- **Blanks called orphans.** *Response:* ask which rows have a value with no match.
- **One key for the budget join.** *Symptom:* "join on BudgetID". *Response:* ask which column of the ledger holds a BudgetID.
- **Both budget tables joined.** *Symptom:* a budget total that is too high. *Response:* ask how Budget relates to BudgetLine.
- **A row-to-row join.** *Symptom:* a budget total many times the budget. *Response:* ask how many ledger rows one budget row meets, and at what grain each side should be summed.
- **AccountID tested against the account number.** *Response:* ask which Account column holds the key.
- **The clean test read as coverage.** *Symptom:* "every budget line has actuals". *Response:* ask them to count the budget rows with a ledger row.
- **Year-end closes forgotten, or found by their description.** *Symptom:* odd actuals in December, or an ordinary entry left out. *Response:* ask what the close entries do to expense accounts, and which column of JournalEntry names them.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: key and hierarchy | 15 | The key, no hierarchy, and the consequence | The key without the finding |
| Requirement 2: the ledger link | 20 | Both ends, the optional end explained, the count reused | Cardinality without the meaning |
| Requirement 3: the budget tables | 25 | Keys and rows of each, accounts compared, Budget chosen with a reason, both sides at one grain | A comparison without the choice |
| Requirement 4: the test | 20 | The lists, the clean result, its limits | The test without the limits |
| Requirement 5: the assessment | 20 | The join as a four-column match of summaries, with the scope and the gaps | A list of gaps without the join |

## Extensions and discussion questions

- List the budgeted combinations of fiscal {{ year }} that have no ledger row, and say which cost centers and accounts they come from.
- Sketch the report: rows of accounts, a column for each cost center, budget and actual side by side. Which keys feed each cell?
- Discuss: who should maintain the mapping of cost centers to divisions, and who should review it? (Chapter 15 builds the budget report in Power BI.)
- Discuss: the ledger rows with no cost center are mostly balance sheet rows. Should an expense row with no cost center be a finding? (Chapter 2's Exercise 2.4 asked it.)
