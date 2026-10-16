# Requirement 1: Build the trial balances and the recorded statements (Chapters 6, 10, and 11)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 1 |
| Perspective | Financial accounting |
| Tools | More than one tool |
| Time | About 90 minutes |
| Solution file | Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 1; Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheets TB 2024, TB 2025, TB 2026, Working TB and Recorded |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Everything later in the case rests on these trial balances, so this requirement fixes the one rule that makes them comparable: a balance is taken as of a date, and only the closing entries dated on that date are left out. It reuses Chapter 11's Params CTE, Chapter 6's mapping of accounts to statement lines and Chapter 10's anti-join. The analytics type is descriptive.

Students can:

- write one trial-balance query whose as-of date is a parameter, and say which closing entries it leaves out and why (Part 1);
- map every account to a statement line and build recorded statements that agree with control totals they trust (Part 2);
- list the accounts never posted with an anti-join and name what the chart lacks (Part 3).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts, and transactions) and BAR M10 (advanced data analytics); IMA Reporting and Control (financial statement preparation); IFAC IES 2 (a) and 2 (i); AACSB A5 part 5.1 (technology integration: SQL; Excel).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite, a copy of the download, with `LenderPackage.sql` open in DB Browser for SQLite, and Charles River Lender Package.xlsx with its Documentation worksheet.
- **Data conditions.** GLEntry.VoucherNumber holds the EntryNumber of a journal entry, and JournalEntry.EntryType marks the closes: two at each year-end, JE-2024-000265/266, JE-2025-000287/288, JE-2026-000296/297. The opening entry belongs to the first fiscal year. The chart has 10 header accounts, which never post. Fiscal 2027 holds supplier payments only, so a query with no as-of date returns no year-end balance.
- **Verify first.** The query returns 69, 71 and 71 rows for the three year-ends, with equal debit and credit balances at each.

## How to run it

Pairs, about 90 minutes: 25 for the query, 10 for the reruns and the net income check, 35 for the mapping and statements, 10 for the control totals, 10 for the anti-join. The routine for every query: type it at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the mapping formula until students have listed the subtypes, and Chapter 6's control totals until their balance sheet balances. **Collect** the script and the workbook.

![A mock of the trial-balance query for the last year-end with its result, the check students make before they map anything.](../figures/chapter-17-statements-for-a-lender/IF-17-1-A.pdf)

## Step-by-step solution

### Part 1: One trial-balance query

**Step 1. Write the query with its date in a Params CTE.** The Closes CTE names the closing entries. The WHERE clause keeps every posting up to the as-of date and drops one only when it belongs to a close dated on that date. SQL fits because the query repeats exactly and a reviewer reads one rule.

```sql
-- Requirement 1: the trial balance at 2026-12-31, one query with its as-of date in a Params CTE
-- Population: GLEntry to 2026-12-31, a close left out only when dated then; expected: 71 accounts, 4 at zero, debit and credit balances of 67,107,722.36
WITH Params AS (
    SELECT '2026-12-31' AS AsOfDate
),
Closes AS (
    SELECT EntryNumber
    FROM JournalEntry
    WHERE EntryType LIKE 'Year-End Close%'
)
SELECT a.AccountNumber, a.AccountName, a.AccountType,
    a.AccountSubType,
    ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Balance,
    CASE WHEN SUM(gl.Debit) - SUM(gl.Credit) > 0
        THEN ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2)
        ELSE 0 END AS DebitBalance,
    CASE WHEN SUM(gl.Debit) - SUM(gl.Credit) < 0
        THEN ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2)
        ELSE 0 END AS CreditBalance,
    COUNT(*) AS Postings
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE gl.PostingDate <= (SELECT AsOfDate FROM Params)
    AND NOT (gl.VoucherNumber IN (SELECT EntryNumber FROM Closes)
        AND gl.PostingDate = (SELECT AsOfDate FROM Params))
GROUP BY a.AccountID, a.AccountNumber, a.AccountName,
    a.AccountType, a.AccountSubType
ORDER BY a.AccountNumber;
```

**Check:** 71 rows, 4 at zero, and debit and credit balances of $67,107,722.36, Chapter 6's control total.

**Step 2. Rerun it for the other year-ends.** Change only the date in Params and keep each result (**Copy with Headers**, Ctrl+Shift+C).

**Check:** 2024: 69 accounts, 2 at zero, balances of $47,565,211.56. 2025: 71, 4, $58,143,212.29. **Watch for:** four wrong versions, each the model query with one change.

- A strict less-than drops every posting of the last day. It still balances, so nothing flags it, but the total is $730,196.69 short of Chapter 6.
- Leaving out every close gives 70 accounts, 3 at zero and balances of $113,953,216.26. Revenue holds three years (`4010` reads $50,553,899.75, not $17,398,287.56) and retained earnings reads $10,183,821.46, not $20,428,484.44, because the earlier closes moved those years' income into it.
- Leaving every close in zeroes the revenue and expense accounts: 46 accounts at zero.
- Filtering on the fiscal year gives 64 accounts and cash of -$941,310.30, the year's change, because the opening balances are earlier postings.

**Step 3. Check net income against the closes.** The script's net income query sums each year's revenue and expense postings, closes excluded, beside the credit to retained earnings in that year's Income Summary close.

**Check:** $5,110,308.27, $5,134,354.71 and $4,503,611.24, each equal to its close.

### Part 2: The workbook

**Step 4. Put each trial balance on its own worksheet.** Paste the results into TB 2024, TB 2025 and TB 2026. The model workbook builds the same lists with formulas and a Power Query ledger summary driven by an as-of date, so they refresh; it agrees with the query to the cent, and either is acceptable. Excel fits because the adjustments will sit beside the balances.

**Step 5. Map each account to a statement line.** Add a Working TB Table, one row for each account, with a StatementLine column. The model maps by AccountSubType and account number:

```
=LET(n,[@AccountNumber],s,[@AccountSubType],t,[@AccountType],
    IFS(
        n=1010,"Cash",
        OR(n=1020,n=1030),"Receivables",
        OR(n=1040,n=1045,n=1046,n=1090),"Inventories",
        OR(s="Current Asset",s="Contra Current Asset"),"Prepaid expenses and other current assets",
        OR(s="Fixed Asset",s="Contra Fixed Asset",s="Noncurrent Asset"),"Property and equipment, net",
        n=2010,"Accounts payable",
        n=2020,"Goods received not invoiced",
        n=2050,"Sales tax payable",
        n=2060,"Customer credits",
        s="Current Liability","Accrued liabilities",
        s="Long-Term Liability","Notes payable, less current portion",
        OR(n=3010,n=3020),"Common stock",
        t="Equity","Retained earnings",
        s="Operating Revenue","Operating revenue",
        s="Contra Revenue","Sales returns and allowances",
        s="COGS","Cost of goods sold",
        s="Operating Expense","Operating expenses",
        n=7030,"Interest expense",
        n=7020,"Loss on disposal of equipment",
        TRUE,"Other income"))
```

**Check:** every account with postings has a line. **Watch for:** signing each account by its NormalBalance. The contra assets are then added to the assets they reduce: total assets read $43,853,037.03, not $39,328,524.11.

**Step 6. Build the recorded balance sheets and statements of income.** Use SUMIFS on the Working TB columns by line: assets as recorded, liabilities and equity reversed. Before the year's close, retained earnings are the negative of account `3030` plus that year's net income.

**Check:** total assets $23,742,720.31, $31,838,684.00 and $39,328,524.11, and each balance sheet balances. **Watch for:** retained earnings taken from `3030` alone. The sheet is then out of balance by the year's net income, $4,503,611.24 at the last year-end.

**Step 7. Validate against control totals you can trace.** Type Chapter 6's pre-closing balances and its net income beside the workbook's, and add the difference.

**Check:** both differences are zero. If the first fails, look at which closes the query left out.

### Part 3: The accounts never posted

**Step 8. List them with an anti-join.** The chart without its headers, left joined to the ledger, keeping the rows where the ledger has none.

```sql
-- Requirement 1: the accounts never posted, with an anti-join
-- Population: the chart without its headers; expected: 23 accounts, 16 active and 7 inactive
SELECT a.AccountNumber, a.AccountName, a.AccountType, a.IsActive
FROM Account AS a
    LEFT JOIN GLEntry AS gl ON gl.AccountID = a.AccountID
WHERE gl.GLEntryID IS NULL
    AND a.AccountSubType <> 'Header'
ORDER BY a.AccountNumber;
```

**Check:** 23 rows, 16 active and 7 inactive. **Watch for:** without the header filter the list has 33 rows; an inner join in place of the left join returns 0, which looks like a complete ledger.

**Step 9. Say what the chart lacks.**

```sql
-- Requirement 1: the accounts named for taxes, to see what the chart lacks
-- Population: the chart; expected: sales tax and payroll taxes only, no income tax account
SELECT AccountNumber, AccountName, AccountType, AccountSubType
FROM Account
WHERE AccountName LIKE '%Tax%'
ORDER BY AccountNumber;
```

**Check:** 4 rows, sales tax and payroll taxes: the chart has no income tax account, neither an expense nor a payable. Several unused accounts lead to later requirements: interest payable (Requirement 4), the allowance for doubtful accounts (Requirement 5), leases and interest income (Requirement 9).

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Accounts with postings; at zero, 2024, 2025, 2026 | 69, 71, 71; 2, 4, 4 | 1, 2 |
| Debit balances, equal to the credit balances | $47,565,211.56; $58,143,212.29; $67,107,722.36 | 1, 2 |
| Net income | $5,110,308.27; $5,134,354.71; $4,503,611.24 | 3 |
| Total assets | $23,742,720.31; $31,838,684.00; $39,328,524.11 | 6 |
| Gross margin and operating income, 2026 | $11,096,754.29; $4,625,057.71 | 6 |
| Never posted; active; inactive | 23; 16; 7 | 8 |

> **Instructor notes, Requirement 1:** WITH Params AS (SELECT '2026-12-31' AS AsOfDate); PostingDate \<= AsOfDate; leave out a posting only if it belongs to a close (JournalEntry.EntryType LIKE 'Year-End Close%': JE-2024-000265/266, JE-2025-000287/288, JE-2026-000296/297) AND is dated on AsOfDate. Year-ends 2024 / 2025 / 2026: 69 / 71 / 71 accounts with postings, 2 / 4 / 4 of them at zero, debit and credit balances 47,565,211.56 / 58,143,212.29 / 67,107,722.36 (the last is Chapter 6's). The earlier closes stay in because they moved earlier years' income into retained earnings; leaving them out would count that income twice. Net income equals each Income Summary close to 3030: 5,110,308.27 / 5,134,354.71 / 4,503,611.24. Recorded year-ends 2024 / 2025 / 2026: total assets 23,742,720.31 / 31,838,684.00 / 39,328,524.11; current assets 21,074,807.78 / 29,358,195.27 / 37,236,780.57; current liabilities 7,621,731.07 / 10,666,774.33 / 13,507,123.75; notes payable (2110, all classified long-term) 326,859.51 / 243,425.23 / 389,304.68; retained earnings before the year's close 10,183,821.46 / 15,294,129.73 / 20,428,484.44; common stock 500,000.00. Recorded income 2025 / 2026: operating revenue 29,586,268.92 / 29,973,822.48; returns (4060) 201,104.38 / 242,764.56; cost of goods sold 17,833,805.16 / 18,634,303.63; gross margin 11,551,359.38 / 11,096,754.29; operating expense 6,355,491.55 / 6,471,696.58; operating income 5,195,867.83 / 4,625,057.71; interest expense 19,513.12 / 28,946.47; loss on disposal (7020) 42,000.00 / 92,500.00. Never posted, headers aside: 23 accounts, 16 active (1030 Allowance for Doubtful Accounts, 1060, 1070, 1080, 1140 Leasehold Improvements, 1180, 1190, 2070 Deferred Revenue, 2080 Interest Payable, 2090, 2120 Lease Liability, 2130, 3020, 3040 Dividends or Owner Distributions, 3050, 8020) and 7 inactive (4070, 5070, 6170 Bad Debt Expense, 6260, 6270, 7010 Interest Income, 7040). The chart has no income tax account at all, neither an expense nor a payable; the accounts named for taxes are sales tax and payroll taxes. The unused 2080, 2120, 1140, 1030, and 7010 each lead to a later requirement.

## What a strong answer says

- **The rule.** A trial balance leaves out only the closes dated on its own as-of date, because earlier closes already moved their income into retained earnings.
- **The mapping.** Lines by AccountSubType and account number, the contra accounts and `1090` placed on purpose, the year's income in retained earnings before the close.
- **The validation.** Agreement with Chapter 6 to the cent, and every trial balance and balance sheet balancing.
- **The gaps.** Accounts never posted, and the missing income tax account named as a matter for the CFO rather than given a number.

A weak answer reports balances without control totals, or lists unused accounts without saying which ones matter.

## Common mistakes and how to respond

- **A strict less-than.** *Symptom:* equal debits and credits, $730,196.69 short. *Response:* ask where the postings of the last day went.
- **Every close left out.** *Symptom:* revenue that holds three years. *Response:* ask what an earlier close did to that income and where it sits now.
- **Contra accounts added.** *Symptom:* assets $4,524,512.92 too high. *Response:* ask what a contra account reduces.
- **Retained earnings without the year.** *Symptom:* a sheet out of balance by the year's net income. *Response:* ask what the close would have added.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| One parameterized query | 25 | Params CTE; only the close dated on the as-of date left out; three dates | Correct for one date, or all closes left out |
| Three trial balances and control totals | 15 | Each balances; the last agrees with Chapter 6 | Balanced, not compared |
| Mapping and recorded statements | 25 | Every account mapped; both statements; retained earnings include the year | Statements that do not balance |
| Validation | 15 | Differences shown and zero; net income tied to the closes | No visible check |
| Anti-join and the chart's gaps | 20 | List correct, headers excluded, income tax gap named | List without the gap |

## Extensions and discussion questions

- Rerun the query with a mid-year as-of date and explain why the revenue accounts show a partial year and no close applies.
- Add a count of postings to each trial balance and mark the accounts with one posting; say what they have in common.
- Discuss: a trial balance balances whether or not it is right. What does it prove, and what does it not?
