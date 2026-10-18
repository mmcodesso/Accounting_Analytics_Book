---
note: ch09.ex1
uses: [ch09.g1]
title: Reviewing the Chart of Accounts
kind: exercise
number: '9.1'
unit: '9'
perspective: financial
tool: sql
minutes: 75
solution: "Chapter09-exercises-sql.zip: Ex 9.1.sql"
figures:
  - id: IF-09-1-A
    kind: sql-mock
    purpose: The result students should reach in Step 6, with the parenthesized condition visible beside it.
    shows: "The Execute SQL tab of DB Browser for SQLite on the tab Ex 9.1.sql. The editor holds the two comment lines and the query of Step 6 with the two parenthesized groups. The result grid shows the contra accounts with AccountID, AccountNumber, AccountName, AccountType, AccountSubType and NormalBalance, and the message pane reports the number of rows returned."
    data: Account, the opposite-balance query of Step 6, run read-only on the dataset (the Expected results give the accounts).
---
{% set g = ch09_g1 %}
# Exercise 9.1: Reviewing the Chart of Accounts

{{ header() }}

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
- **Data conditions.** The Account table holds {{ n }} accounts. AccountSubType holds the text Header exactly, ParentAccountID is NULL (not empty text) on the top-level headers, and IsActive is 0 or 1. The ledger's AccountID is the Account table's surrogate key, so a test of postings needs AccountID, not AccountNumber.
- **Verify first.** `SELECT * FROM Account;` returns {{ n }} rows.

## How to run it

Individual, about 75 minutes: 15 each for requirements (1) and (2), (3), (4), (5) and the memo. Every step follows one routine: leave a blank line at the end of `Ex 9.1.sql`, type the two comment lines and the query, select the query, click **Execute all/selected SQL** (Ctrl+Return) and read the message pane, which reports "Result: N rows returned" (with no thousands separator, and "1 rows" for a single row). Click **Save SQL file** at the end; Ctrl+S is **Write Changes** and saves the database. Steps 5, 8, 10 and 11 are the queries behind statements of the model answer (no postings to headers, inactive accounts or the allowance; what posts to account {{ g.no.clearing }}). The exercise does not ask for them, so use them as hints, and count them as a plus for students who test their claims, never as a condition for full credit. Hold back the hint about parentheses until a student's answer to (4) has the wrong number of rows. Collect the script and the memo.

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

**Check:** {{ g.n }} rows, one for each account, with no value in ParentAccountID on the top-level headers. **Watch for:** without ORDER BY, the database promises no order. Do not infer one from AccountID, because the IDs do not follow the account numbers (AccountID {{ g.clearing_id }} is account {{ g.no.clearing }} and AccountID {{ g.variance_id }} is account {{ g.no.variance }}, while AccountID {{ g.before.id }} is account {{ g.before.number }}). Check that the query sorts on AccountNumber.

### Requirement (2): Types and subtypes

**Step 2. List the account types.**

```sql
-- Requirement (2): the account types
-- Population: Account; expected: 5 types
SELECT DISTINCT AccountType
FROM Account
ORDER BY AccountType;
```

**Check:** {{ types|length }} rows, the types of the Expected results.

**Step 3. List the combinations of type and subtype.**

```sql
-- Requirement (2): the combinations of type and subtype
-- Population: Account; expected: 22 combinations of 18 subtypes, a Header subtype in every type
SELECT DISTINCT AccountType, AccountSubType
FROM Account
ORDER BY AccountType, AccountSubType;
```

**Check:** {{ g.pairs }} rows for {{ g.n_sub }} subtypes. Header appears once under every type. **Watch for:** adding AccountName to the list returns {{ g.n }} rows, because DISTINCT works on the whole row and every account is different.

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

**Check:** {{ headers }} rows. {{ g.parent_is }} have no ParentAccountID and head a section; the other {{ subs|length }} sit under a top-level header. **Watch for:** `'header'` in small letters returns {{ g.header_lower }} rows, because `=` compares text exactly. `ParentAccountID = NULL` returns {{ g.parent_eq }} rows where `IS NULL` returns {{ g.parent_is }}.

**Step 5. Test the headers for postings.** The requirement does not ask for this test, which corroborates the structure. A student who runs it copies the AccountID values from Step 4.

```sql
-- Requirement (3): postings to the header accounts
-- Population: GLEntry, the header accounts' AccountIDs; expected: no rows
SELECT GLEntryID, PostingDate, AccountID, Debit, Credit
FROM GLEntry
WHERE AccountID IN (1, 11, 21, 31, 35, 41, 49, 57, 80, 85);
```

**Check:** {{ g.header_postings }} rows. The empty result is the finding. **Watch for:** the same list written with account numbers also returns nothing, for the wrong reason. Ask the student to prove the test by running it for AccountID {{ g.clearing_id }}, which returns rows.

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

{{ figure('IF-09-1-A') }}

**Check:** {{ n_opposite }} rows, {{ g.credit_half }} assets with a credit balance and {{ g.debit_half }} liability, equity or revenue accounts with a debit balance, and every one a contra account. **Watch for:** types listed with OR and no parentheses (`AccountType = 'Asset' OR AccountType = 'Expense' AND ...`) return {{ g.unparenthesized }} rows, because AND binds first. Only one half of the test returns {{ g.credit_half }} or {{ g.debit_half }} rows. The model query is correct even without its outer groups; the habit is the lesson.

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

**Check:** {{ n_inactive }} rows, among them the manufacturing salaries and factory overhead accounts.

**Step 8. Test the inactive accounts for postings.**

```sql
-- Requirement (5): postings to the inactive accounts
-- Population: GLEntry, the inactive accounts' AccountIDs; expected: no rows
SELECT GLEntryID, PostingDate, AccountID, Debit, Credit
FROM GLEntry
WHERE AccountID IN (48, 56, 74, 94, 95, 80, 81, 84);
```

**Check:** {{ g.inactive_postings }} rows. The same trap as Step 5 applies.

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

**Check:** {{ g.n_like_active }} rows: {{ g.like_text }}. **Watch for:** without `IsActive = 1` the pattern returns {{ g.n_like_all }} rows, adding the inactive manufacturing salaries account. `=` with the pattern returns no rows. The inactive factory overhead account does not contain the word, so no LIKE on manufacturing finds it; students must reason from the names.

**Step 10. See which documents post to {{ g.no.clearing }}.**

```sql
-- Requirement (5): the source documents that post to 1090
-- Population: GLEntry, AccountID 92; expected: JournalEntry, PayrollSummary, ProductionCompletion and WorkOrderClose
SELECT DISTINCT SourceDocumentType
FROM GLEntry
WHERE AccountID = 92
ORDER BY SourceDocumentType;
```

**Check:** {{ g.sources_1090|length }} rows: {{ g.sources_1090|join(", ") }}. Payroll and overhead entries debit the account, completions and closes relieve it. **Watch for:** the equipment accounts in Step 9 are fixed assets, and {{ g.no.variance }} is the variance, not the place where the cost is held.

### Requirement (6): The memo

**Step 11. Test the allowance account.** One more query supports the memo.

```sql
-- Requirement (6): postings to 1030 Allowance for Doubtful Accounts
-- Population: GLEntry, AccountID 4; expected: no rows
SELECT GLEntryID, PostingDate, Debit, Credit, Description
FROM GLEntry
WHERE AccountID = 4;
```

**Check:** {{ g.allowance_postings }} rows, so account {{ g.no.allowance }} has no postings in the three years of the extract. Outline the memo in "What a strong answer says".

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Accounts, and the five types | {{ n }}; {% for t in types %}{{ t[0] }} {{ t[1] }}{{ ", " if not loop.last else "" }}{% endfor %} | 1, 2 |
| Combinations of type and subtype, and subtypes | {{ g.pairs }}; {{ g.n_sub }} | 3 |
| Header accounts, and those with no parent | {{ headers }}; {{ g.parent_is }} | 4 |
| Postings to the header accounts | {{ g.header_postings }} | 5 |
| Accounts with an opposite normal balance | {{ n_opposite }}: {{ g.credit_half }} credit-normal assets, {{ g.debit_half }} debit-normal | 6 |
| Inactive accounts, and their postings | {{ n_inactive }}; {{ g.inactive_postings }} | 7, 8 |
| Active accounts that mention manufacturing | {{ g.n_like_active }} | 9 |
| AccountID of {{ g.no.clearing }} and of {{ g.no.variance }} | {{ clearing }}; {{ g.variance_id }} | 10 |
| Postings to {{ g.no.allowance }} | {{ g.allowance_postings }} | 11 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The subtypes divide each type as a balance sheet and an income statement do, and every type has its own Header subtype for the accounts that group the rest.
- **Requirement (3).** Two levels of headers: top-level headers head a section and two sub-headers sit under {{ subs[0].parent }} and {{ subs[1].parent }}. The posting test of Step 5, which shows that none has a posting, as a grouping account should not, is a plus.
- **Requirement (4).** Each of the {{ n_opposite }} accounts is a contra account: the accumulated depreciation accounts and the allowance reduce assets with a credit, the distributions account reduces equity with a debit, and returns and discounts reduce revenue with a debit.
- **Requirement (5).** Manufacturing salaries and factory overhead are not expensed in their own accounts. Both are charged to {{ clearing_name }}, which payroll and overhead entries debit and which completions and closes relieve, so the cost reaches cost of goods sold through inventory and {{ variance_name }}.
- **Requirement (6).** The structure in two sentences, then the points to review that the queries support, such as the inactive accounts (among them the discounts account) and whether they should stay on the chart. The posting tests of Steps 8 and 11 are a plus, showing that the inactive accounts are unused and that the allowance account has no postings in the extract (to be read with Chapter 8's estimate of the allowance), and so is the remark that empty header and inactive accounts do not rule out misclassified postings among the active ones.

A weak memo lists query results without a conclusion, or calls the inactive accounts a defect.

## Common mistakes and how to respond

- **No ORDER BY, or `SELECT *`.** *Symptom:* right rows, wrong columns or order. *Response:* ask which columns the requirement names and whether the order is promised.
- **`= NULL`, or `'header'` in small letters.** *Symptom:* an empty result for a test that must find rows. *Response:* ask what the stored text is and what a comparison with a missing value returns.
- **Account numbers used as AccountIDs.** *Symptom:* an empty posting test that would be just as empty for account {{ g.no.clearing }}. *Response:* ask which key the ledger holds.
- **No parentheses.** *Symptom:* {{ g.unparenthesized }} rows in (4). *Response:* ask which condition each AND belongs to.
- **LIKE without IsActive, or the equipment account.** *Symptom:* {{ g.n_like_all }} rows, or {{ g.no.equipment }} as the answer. *Response:* ask which account payroll debits.
- **A memo with no evidence.** *Response:* ask which query supports each sentence.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the sorted list | 10 | All columns, sorted | Unsorted or `SELECT *` |
| Requirement 2: types and subtypes | 15 | Both queries and a description of the division | Queries without the description |
| Requirement 3: headers | 15 | Header query, the headers with and without a ParentAccountID told apart, and what the difference means for the structure | List without the parent distinction or the structure |
| Requirement 4: opposite balances | 15 | Grouped conditions, eight accounts, each named a contra account | Half of the test |
| Requirement 5: inactive and manufacturing | 20 | Both lists, LIKE with IsActive, {{ g.no.clearing }} named with the reason | {{ g.no.clearing }} without the reason |
| Requirement 6: memo | 25 | Structure and the points to review, each supported by a query | Structure only |

## Extensions and discussion questions

- Discuss: an account with no posting in three years stays on the chart. Who should decide to close it, and what would they check?
- Discuss: the discounts account is unused because discounts are netted in the invoice prices. Is that a presentation choice or a gap?

