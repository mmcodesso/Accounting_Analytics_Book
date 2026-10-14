# Exercise 9.1: Reviewing the Chart of Accounts

| | |
|---|---|
| Unit | Chapter 9: SQL Essentials for Accounting Analytics |
| Item | Exercise 9.1 |
| Perspective | Financial accounting |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 75 minutes |
| Solution file | Chapter09-exercises-sql.zip: Ex 9.1.sql |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The controller wants the chart of accounts reviewed before the statements are final. This is the first exercise of Part III, so the SQL is one table at a time: SELECT with a sort, DISTINCT, WHERE with grouped conditions, IS NULL and LIKE. The accounting is the point: header accounts only group, contra accounts reverse the balance of the account they reduce, inactive accounts hold nothing, and manufacturing cost sits in one clearing account, not in the accounts named for it. The analytics type is descriptive.

By the end, students can:

- list, sort and DISTINCT the columns of a table to see what it holds (outcome 2);
- filter with `=`, IS NULL, grouped AND and OR conditions and LIKE (outcome 3);
- test a statement about the chart with a second query, such as "no header account has a posting" (outcomes 3 and 6);
- explain header, contra and inactive accounts and say where manufacturing cost is recorded (outcome 6).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 and ISC M4 (accounts and transactions; use and management of data); IMA Reporting and Control (financial recordkeeping) and Data Analytics and Insights (data tools); IFAC IES 2 (a) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** DB Browser for SQLite and CharlesRiver_Work.sqlite from Tutorial 9.1. Each student saves a script `Ex 9.1.sql` with a header comment like the one in Tutorial 9.3.
- **Data conditions.** The Account table holds 104 accounts. AccountSubType holds the text Header exactly, ParentAccountID is NULL (not empty text) on the top-level headers, and IsActive is 0 or 1. The ledger's AccountID is the Account table's surrogate key, so a test of postings needs AccountID, not AccountNumber.
- **Verify first.** `SELECT * FROM Account;` returns 104 rows.

## How to run it

Individual, about 75 minutes: 15 each for requirements (1) and (2), (3), (4), (5) and the memo. Every step follows one routine: leave a blank line at the end of `Ex 9.1.sql`, type the two comment lines and the query, select the query, click **Execute all/selected SQL** (Ctrl+Return) and read the message pane, which reports "Result: N rows returned" (with no thousands separator, and "1 rows" for a single row). Click **Save SQL file** at the end; Ctrl+S is **Write Changes** and saves the database. Steps 5, 8, 10 and 11 are the queries behind statements of the model answer (no postings to headers, inactive accounts or the allowance; what posts to account 1090). The exercise does not ask for them, so use them as hints or as credit for students who test their claims. Hold back the hint about parentheses until a student's answer to (4) has the wrong number of rows. Collect the script and the memo.

## Step-by-step solution

### Requirement (1): Every account, sorted

**Step 1. List the chart by account number.** Type and run the query.

```sql
-- Requirement (1): every account of the chart, sorted by number
-- Population: Account, every row; expected: 104 accounts, Asset 25, Liability 18, Equity 8, Revenue 13, Expense 40
SELECT AccountID, AccountNumber, AccountName, AccountType,
    AccountSubType, ParentAccountID, NormalBalance, IsActive
FROM Account
ORDER BY AccountNumber;
```

**Check:** 104 rows, one for each account, with no value in ParentAccountID on the top-level headers. **Watch for:** a missing ORDER BY goes unnoticed, because AccountID follows AccountNumber here and the rows still look sorted. Say that the order is not guaranteed.

### Requirement (2): Types and subtypes

**Step 2. List the account types.**

```sql
-- Requirement (2): the account types
-- Population: Account; expected: 5 types
SELECT DISTINCT AccountType
FROM Account
ORDER BY AccountType;
```

**Check:** 5 rows, the types of the Expected results.

**Step 3. List the combinations of type and subtype.**

```sql
-- Requirement (2): the combinations of type and subtype
-- Population: Account; expected: 22 combinations of 18 subtypes, a Header subtype in every type
SELECT DISTINCT AccountType, AccountSubType
FROM Account
ORDER BY AccountType, AccountSubType;
```

**Check:** 22 rows for 18 subtypes. Header appears once under every type. **Watch for:** adding AccountName to the list returns 104 rows, because DISTINCT works on the whole row and every account is different.

### Requirement (3): The header accounts

**Step 4. List the headers and their parents.**

```sql
-- Requirement (3): the header accounts and their parents
-- Population: Account, AccountSubType Header; expected: 10 headers, 8 without a ParentAccountID
SELECT AccountID, AccountNumber, AccountName, AccountType,
    ParentAccountID
FROM Account
WHERE AccountSubType = 'Header'
ORDER BY AccountNumber;
```

**Check:** 10 rows. 8 have no ParentAccountID and head a section; the other 2 sit under a top-level header. **Watch for:** `'header'` in small letters returns 0 rows, because `=` compares text exactly. `ParentAccountID = NULL` returns 0 rows where `IS NULL` returns 8.

**Step 5. Test the headers for postings.** Students copy the AccountID values from Step 4.

```sql
-- Requirement (3): postings to the header accounts
-- Population: GLEntry, the header accounts' AccountIDs; expected: no rows
SELECT GLEntryID, PostingDate, AccountID, Debit, Credit
FROM GLEntry
WHERE AccountID IN (1, 11, 21, 31, 35, 41, 49, 57, 80, 85);
```

**Check:** 0 rows. The empty result is the finding. **Watch for:** the same list written with account numbers also returns nothing, for the wrong reason. Ask the student to prove the test by running it for AccountID 92, which returns rows.

### Requirement (4): Opposite normal balances

**Step 6. Group the two conditions with parentheses.**

```sql
-- Requirement (4): accounts whose normal balance is opposite to their type
-- Population: Account; expected: 8 contra accounts
SELECT AccountID, AccountNumber, AccountName, AccountType,
    AccountSubType, NormalBalance
FROM Account
WHERE (AccountType IN ('Asset', 'Expense')
        AND NormalBalance = 'Credit')
    OR (AccountType IN ('Liability', 'Equity', 'Revenue')
        AND NormalBalance = 'Debit')
ORDER BY AccountNumber;
```

![A mock of the result students should reach in Step 6, with the parenthesized condition visible beside it.](../figures/chapter-09-sql-essentials/IF-09-1-A.pdf)

**Check:** 8 rows, 5 assets with a credit balance and 3 liability, equity or revenue accounts with a debit balance, and every one a contra account. **Watch for:** types listed with OR and no parentheses (`AccountType = 'Asset' OR AccountType = 'Expense' AND ...`) return 53 rows, because AND binds first. Only one half of the test returns 5 or 3 rows. The model query is correct even without its outer groups; the habit is the lesson.

### Requirement (5): Inactive accounts and manufacturing

**Step 7. List the inactive accounts.**

```sql
-- Requirement (5): the inactive accounts
-- Population: Account, IsActive 0; expected: 8 accounts
SELECT AccountID, AccountNumber, AccountName, AccountType,
    AccountSubType
FROM Account
WHERE IsActive = 0
ORDER BY AccountNumber;
```

**Check:** 8 rows, among them the manufacturing salaries and factory overhead accounts.

**Step 8. Test the inactive accounts for postings.**

```sql
-- Requirement (5): postings to the inactive accounts
-- Population: GLEntry, the inactive accounts' AccountIDs; expected: no rows
SELECT GLEntryID, PostingDate, AccountID, Debit, Credit
FROM GLEntry
WHERE AccountID IN (48, 56, 74, 94, 95, 80, 81, 84);
```

**Check:** 0 rows. The same trap as Step 5 applies.

**Step 9. Find the active accounts that mention manufacturing.**

```sql
-- Requirement (5): active accounts whose names mention manufacturing
-- Population: Account, IsActive 1; expected: 4 accounts, among them 1090 and 5080
SELECT AccountID, AccountNumber, AccountName, AccountType,
    AccountSubType
FROM Account
WHERE AccountName LIKE '%manufacturing%' AND IsActive = 1
ORDER BY AccountNumber;
```

**Check:** 4 rows: 1090 Manufacturing Cost Clearing; 1185 Manufacturing Equipment; 1186 Accumulated Depreciation - Manufacturing Equipment; 5080 Manufacturing Variance. **Watch for:** without `IsActive = 1` the pattern returns 5 rows, adding the inactive manufacturing salaries account. `=` with the pattern returns no rows. The inactive factory overhead account does not contain the word, so no LIKE on manufacturing finds it; students must reason from the names.

**Step 10. See which documents post to 1090.**

```sql
-- Requirement (5): the source documents that post to 1090
-- Population: GLEntry, AccountID 92; expected: JournalEntry, PayrollSummary, ProductionCompletion and WorkOrderClose
SELECT DISTINCT SourceDocumentType
FROM GLEntry
WHERE AccountID = 92
ORDER BY SourceDocumentType;
```

**Check:** 4 rows: JournalEntry, PayrollSummary, ProductionCompletion, WorkOrderClose. Payroll and overhead entries debit the account, completions and closes relieve it. **Watch for:** the equipment accounts in Step 9 are fixed assets, and 5080 is the variance, not the place where the cost is held.

### Requirement (6): The memo

**Step 11. Test the allowance account.** One more query supports the memo.

```sql
-- Requirement (6): postings to 1030 Allowance for Doubtful Accounts
-- Population: GLEntry, AccountID 4; expected: no rows
SELECT GLEntryID, PostingDate, Debit, Credit, Description
FROM GLEntry
WHERE AccountID = 4;
```

**Check:** 0 rows, so no allowance was recorded in the three years. Outline the memo in "What a strong answer says".

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Accounts, and the five types | 104; Asset 25, Liability 18, Equity 8, Revenue 13, Expense 40 | 1, 2 |
| Combinations of type and subtype, and subtypes | 22; 18 | 3 |
| Header accounts, and those with no parent | 10; 8 | 4 |
| Postings to the header accounts | 0 | 5 |
| Accounts with an opposite normal balance | 8: 5 credit-normal assets, 3 debit-normal | 6 |
| Inactive accounts, and their postings | 8; 0 | 7, 8 |
| Active accounts that mention manufacturing | 4 | 9 |
| AccountID of 1090 and of 5080 | 92; 93 | 10 |
| Postings to 1030 | 0 | 11 |

> **Instructor notes, Exercise 9.1:** 104 accounts: Asset 25, Liability 18, Equity 8, Revenue 13, Expense 40. Eighteen subtypes, including Header (10), Current Asset (11), Fixed Asset (5), Contra Fixed Asset (4), Contra Current Asset (1), Current Liability (13), Long-Term Liability (3), Operating Revenue (6), Contra Revenue (2), COGS (8), Operating Expense (29), Closing (1). Header accounts: 10; eight top-level headers (1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000) have a NULL ParentAccountID, while 1100 Fixed Assets and 2100 Long-Term Liabilities are sub-headers under 1000 and 2000, so the chart has two levels of headers. No header account has a posting. Opposite normal balances (8): 1030 Allowance for Doubtful Accounts, 1150/1160/1170/1186 accumulated depreciation (contra assets, credit); 3040 Dividends or Owner Distributions (contra equity, debit); 4060 Sales Returns and Allowances and 4070 Sales Discounts (contra revenue, debit). The query needs parentheses: (AccountType IN ('Asset','Expense') AND NormalBalance = 'Credit') OR (AccountType IN ('Liability','Equity','Revenue') AND NormalBalance = 'Debit'). Inactive (8), none with any posting: 4070 Sales Discounts, 5070 Inventory Adjustments, 6170 Bad Debt Expense, 6260 Salaries Expense - Manufacturing, 6270 Factory Overhead Expense, 7000 Other Income and Expense (header), 7010 Interest Income, 7040 Foreign Exchange Gain or Loss. Manufacturing salaries and factory overhead are charged to 1090 Manufacturing Cost Clearing (AccountID 92) and reach cost of goods sold through inventory and 5080 Manufacturing Variance. Memo points: 1030 has no postings in the extract, so no allowance was recorded in the three years (Chapter 8); 4070 is inactive with no postings, and the Part II case found the discounts netted in the invoice prices, a presentation to confirm rather than assume. The absence of postings to inactive and header accounts does not rule out misclassified postings among the active accounts.

## What a strong answer says

- **Requirement (2).** The subtypes divide each type as a balance sheet and an income statement do, and every type has its own Header subtype for the accounts that group the rest.
- **Requirement (3).** Two levels of headers: top-level headers head a section and two sub-headers sit under 1000 and 2000. None has a posting, as a grouping account should not.
- **Requirement (4).** Each of the 8 accounts is a contra account: the accumulated depreciation accounts and the allowance reduce assets with a credit, the distributions account reduces equity with a debit, and returns and discounts reduce revenue with a debit.
- **Requirement (5).** Manufacturing salaries and factory overhead are not expensed in their own accounts. Both are charged to Manufacturing Cost Clearing, which payroll and overhead entries debit and which completions and closes relieve, so the cost reaches cost of goods sold through inventory and Manufacturing Variance.
- **Requirement (6).** The structure in two sentences, then the two review points: no allowance is recorded (Chapter 8 estimates one), and the discounts account is inactive and unused. It adds that empty header and inactive accounts do not rule out misclassified postings among the active ones.

A weak memo lists query results without a conclusion, or calls the inactive accounts a defect.

## Common mistakes and how to respond

- **No ORDER BY, or `SELECT *`.** *Symptom:* right rows, wrong columns or order. *Response:* ask which columns the requirement names and whether the order is promised.
- **`= NULL`, or `'header'` in small letters.** *Symptom:* an empty result for a test that must find rows. *Response:* ask what the stored text is and what a comparison with a missing value returns.
- **Account numbers used as AccountIDs.** *Symptom:* an empty posting test that would be just as empty for account 1090. *Response:* ask which key the ledger holds.
- **No parentheses.** *Symptom:* 53 rows in (4). *Response:* ask which condition each AND belongs to.
- **LIKE without IsActive, or the equipment account.** *Symptom:* 5 rows, or 1185 as the answer. *Response:* ask which account payroll debits.
- **A memo with no evidence.** *Response:* ask which query supports each sentence.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the sorted list | 10 | All columns, sorted | Unsorted or `SELECT *` |
| Requirement 2: types and subtypes | 15 | Both queries and a description of the division | Queries without the description |
| Requirement 3: headers | 15 | Query, IS NULL reading, the posting test and the structure | No posting test |
| Requirement 4: opposite balances | 15 | Grouped conditions, eight accounts, each named a contra account | Half of the test |
| Requirement 5: inactive and manufacturing | 20 | Both lists, LIKE with IsActive, 1090 named with the reason | 1090 without the reason |
| Requirement 6: memo | 25 | Structure and both review points with evidence | Structure only |

## Extensions and discussion questions

- Discuss: an account with no posting in three years stays on the chart. Who should decide to close it, and what would they check?
- Discuss: the discounts account is unused because discounts are netted in the invoice prices. Is that a presentation choice or a gap?
