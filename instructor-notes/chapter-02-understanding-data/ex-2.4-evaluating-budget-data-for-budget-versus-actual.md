# Exercise 2.4: Evaluating Budget Data for Budget-Versus-Actual Analysis

| | |
|---|---|
| Unit | Chapter 2: Understanding Data in Accounting |
| Item | Exercise 2.4 |
| Perspective | Managerial accounting |
| Tools | Workbook browsing and written work |
| Time | About 45 minutes |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A budget-versus-actual report needs a budget at the grain of the actuals, and the Charles River workbook has two budget tables. The exercise asks what each holds, whether they can be added, and what the rows without a cost center do to a comparison by cost center. It also connects the chapter's tidy data idea to the layout of a report a manager asks for. The analytics type is descriptive, in preparation for the variance work of Chapters 7 and 15.

By the end, students can:

- say what one row of each budget table represents, and whether the tables add (outcome 6);
- explain why a wide report breaks tidy principles and why the stored form suits analysis (outcome 6);
- count blanks in two tables and judge them by what the rows are, not by their share (outcomes 4 and 5);
- recommend the preparation steps for a budget-versus-actual comparison.

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (cleansing financial data); IMA Data Literacy and Budgeting and Forecasting; IFAC IES 2 (b), management accounting, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx, the chapter's section on tidy data and Figure 2.6, and the PivotTable skills of Tutorial 2.2.
- The exercise relies on these conditions: Budget has one row for each fiscal year, month, cost center and account; each Budget row equals the sum of the BudgetLine rows with the same key; BudgetLine also holds lines that Budget leaves out; and CostCenterID is blank on some rows of BudgetLine and of GLEntry, for different reasons.
- The last complete operating year is 2026. The budget extends through 2027, while the actuals of 2027 are only a tail of supplier payments, so a comparison covers only the years that have both.
- Requirement (3) invites students to quote raw counts. Decide beforehand that you want the rows classified, as Step 5 does.

## How to run it

Individual work, then a ten-minute pair comparison of the memos. For about 45 minutes: 10 on requirement 1, 10 on requirement 2, 15 on requirement 3 and 10 on the memo.

**Hints.** If students say the tables add, ask which accounts appear in both. Hold back the AccountType lookup of Step 5 until a student asks why the ledger has so many blank rows.

## Step-by-step solution

### Requirement (1): What a row is, and whether the tables add

**Step 1. Read one row of each table.** Open **Budget** and **BudgetLine** and read the columns of the first rows.

**Check:** a Budget row is one amount for one account, cost center and month of a fiscal year. A BudgetLine row is one driver line: an account and a month, with the cost center, item and warehouse where they apply, a BudgetCategory, and on the revenue and cost of goods sold lines a Quantity and UnitAmount whose product is BudgetAmount. Both tables are tidy: each variable has a column, including Month, and each row is one observation.

**Step 2. Test whether the amounts add.**

a. On **Budget**, in the first free column, enter this formula, which finds the BudgetLine amount for the same year, cost center, month and account and subtracts the Budget amount:

   ```
   =ROUND(SUMIFS(BudgetLine!J:J,BudgetLine!B:B,B2,BudgetLine!C:C,E2,BudgetLine!D:D,D2,BudgetLine!E:E,C2)-F2,2)
   ```

b. Copy it down and filter the column for anything other than 0.

![How BudgetLine rolls up to Budget, and what Budget leaves out.](../figures/chapter-02-understanding-data/IF-02-4-A.pdf)

**Check:** no rows. Every Budget row equals the sum of its BudgetLine rows, so Budget is a roll-up of BudgetLine for the 21 accounts it carries (4 revenue and 17 expense), and the two tables cannot be added: the amounts would be counted twice. BudgetLine holds more than Budget: item and warehouse detail, 14 operating expense accounts that have no cost center (168 lines, $2,024,273.70 in 2026), and balance sheet rollforward lines. Budget has 348 rows in 2026. **Watch for:** students who test only one row.

### Requirement (2): The report a manager asks for

**Step 3. Sketch the wide report and name what it breaks.** Draw one cost center for fiscal 2026, Administration: its 4 accounts down the side and twelve month columns across the top.

**Check:** the stored table has 48 rows for that cost center and year, one for each account and month. The wide report breaks two principles at once: the month is a variable stored in the column headers, and each row holds twelve observations. The tidy form is better for analysis because a new month is a new row, the month is a field to group and filter, and it joins to the actual results on fiscal year, fiscal period, account and cost center. The wide layout can still be made from the tidy one with a PivotTable, which is the direction students should take. **Watch for:** students who say a wide report is wrong. It is the right output and the wrong storage.

### Requirement (3): Rows without a cost center

**Step 4. Count the blanks in both tables.**

a. On **BudgetLine**, filter CostCenterID for blank cells and read the status bar, or enter `=COUNTBLANK(T77_BudgetLine[CostCenterID])`.
b. Do the same on **GLEntry**, with `=COUNTBLANK(T3_GLEntry[CostCenterID])`.

**Check:** BudgetLine has 1,625 blank rows of 31,426: 672 operating expense and 953 balance sheet. GLEntry has 115,623 of 815,921, 14.2%. A student who stops here and recommends dropping the rows has not asked what they are.

**Step 5. Find out which accounts the blanks are on.**

a. Insert a PivotTable from **GLEntry** with AccountID in the **Rows** area, CostCenterID in the columns area, and the count of GLEntryID in **Values** (Count, not Sum).
b. Read the column for the blank cost center. A PivotTable ignores the worksheet's filters, so it must carry the blank entry itself.
c. Next to the AccountIDs with blank entries, look up the AccountType and the account number in the **Account** worksheet, as in Tutorial 2.2 Step 5.
d. For the money, add FiscalYear and VoucherNumber to the PivotTable's **Filters** area, keep 2026, and clear the year's closing entries (JE-2026-000296 and JE-2026-000297) from VoucherNumber. Add Sum of Debit and Sum of Credit to **Values**, and compute the net expense of the blank and of all expense rows as debits less credits beside the PivotTable.

**Check:** most of the blank ledger rows are on balance sheet accounts such as receivables, payables and cash, which do not use cost centers. Only 903 expense rows are blank outside the year-end closes, and 102 more are in the closes, which a budget comparison excludes. In 2026, 318 of 55,099 expense rows outside the closes (0.6%) have no cost center, but they are $2,069,862.95 of $25,134,946.68 of expense (8.2%). The row count understates the money. They are on 15 accounts: the 14 that BudgetLine plans with no cost center, plus Interest Expense, which Budget puts in the Administration cost center and the ledger posts with none. On those 14 accounts the actual of $2,040,916.48 is close to the budget of $2,024,273.70.

**Step 6. Recommend how to handle them.** A model answer, in order: (1) aggregate the relevant BudgetLine lines (revenue, cost of goods sold and operating expense) and the actual ledger rows separately to fiscal year, month or fiscal period, account and cost center, because Budget alone leaves out the 14 accounts BudgetLine plans with no cost center; use Budget as a control for the combinations it holds, and never add the two tables; (2) leave the balance sheet lines out, because they are balances, not flows; (3) exclude the year-end closes from the actual side; (4) keep the rows with no cost center as an explicit "No cost center" bucket on both sides; (5) decide where the interest account belongs, so the budget and the actual use the same cost center; (6) match on all four fields, keep the combinations that only one side has, and reconcile the totals before and after matching to the whole budget and the whole ledger.

**Check:** the answer keeps the rows, names the bucket, matches on four fields, and reconciles to a total.

### Requirement (4): Write the memorandum

**Step 7. Outline half a page to a page.** A strong memo has a header and the purpose; a conclusion up front (the data can support the comparison after the steps below); the structure of each table; the treatment of the blank rows with the figures of Step 5; and the preparation steps numbered as in Step 6.

**Check:** the steps are specific enough that a colleague could carry them out.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Budget rows in 2026; accounts in Budget | 348; 21 | Steps 1 and 2 |
| Budget rows that differ from their BudgetLine sum | 0 | Step 2 |
| Rows for Administration; accounts | 48; 4 | Step 3 |
| BudgetLine rows; blank cost center | 31,426; 1,625 | Step 4 |
| BudgetLine blanks, operating expense; balance sheet | 672; 953 | Step 4 |
| GLEntry rows; blank cost center | 815,921; 115,623 | Step 4 |
| Blank expense rows outside the closes; in the closes | 903; 102 | Step 5 |
| Expense rows of 2026 with no cost center; their share of the rows; of the money | 318; 0.6%; 8.2% | Step 5 |
| Budget lines with no cost center, operating expense, 2026; actual on the same accounts | $2,024,273.70; $2,040,916.48 | Step 5 |

## What a strong answer says

- **Requirement (1).** One row of each table in a sentence, the test that Budget is a roll-up, and the conclusion that adding the tables double counts.
- **Requirement (2).** The wide layout's two violations, and the reasons the stored form is better, with the PivotTable as the way back.
- **Requirement (3).** The blanks classified by account type, the difference between row share and money share, and a recommendation that keeps the rows in a named bucket.
- **Requirement (4).** Numbered preparation steps with the figures behind them.

A weak answer says the tables are tidy or messy without a test, recommends deleting the blank rows, or quotes the 14% share without classifying them.

## Common mistakes and how to respond

- **Adding the two tables.** *Symptom:* a total of Budget and BudgetLine. *Response:* ask which accounts appear in both.
- **A wide report called wrong.** *Symptom:* "the manager's layout is messy". *Response:* ask which layout is the output and which is the storage.
- **Rows dropped for being blank.** *Symptom:* "delete rows with no cost center". *Response:* ask what share of the money they are and what the totals would then miss.
- **The share quoted from raw counts.** *Symptom:* "14% of the ledger has no cost center". *Response:* ask which accounts the rows are on.
- **The closes forgotten.** *Symptom:* credits to expense accounts with no cost center in the actual. *Response:* ask what entry makes a credit to an expense account at year end.
- **The balance sheet lines kept.** *Symptom:* rollforward balances compared with ledger flows. *Response:* ask whether a balance and a flow can be compared.
- **A memo that restates the exercise.** *Response:* ask for the decision and the evidence.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: rows and whether the tables add | 30 | Rows described, the roll-up tested, double counting named | Descriptions without a test |
| Requirement 2: the report layout | 20 | Both principles named, the stored form justified, the PivotTable as the route back | Layout drawn without the principles |
| Requirement 3: blank cost centers | 30 | Both counts, classified by account, money against rows, a recommendation that keeps the rows | Counts without classification |
| Requirement 4: memorandum | 20 | Numbered steps, evidence, half a page to a page | A narrative with no steps |

## Extensions and discussion questions

- Compare the budget with the actual for one cost center and one month using a PivotTable of each, and say what is still missing before the comparison is fair.
- Find an account that is in the ledger and not in Budget, and say what a report by cost center would show for it.
- Discuss: who should decide where an account without a cost center belongs, the budget owner or the accountant?
- Discuss: when would you want the BudgetLine detail in a comparison? (Chapter 7 uses it for the flexible budget.)
