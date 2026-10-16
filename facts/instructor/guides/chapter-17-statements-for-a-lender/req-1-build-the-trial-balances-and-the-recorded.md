---
note: ch17.r1
uses: [ch17.g1]
title: Build the trial balances and the recorded statements (Chapters 6, 10, and 11)
kind: requirement
number: '1'
unit: '17'
perspective: financial
tool: mixed
minutes: 90
solution: "Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 1; Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheets TB 2024, TB 2025, TB 2026, Working TB and Recorded"
figures:
  - id: IF-17-1-A
    kind: sql-mock
    purpose: The trial-balance query for the last year-end with its result, the check students make before they map anything.
    shows: "The tab LenderPackage.sql at the first query of Requirement 1: the two comment lines, the Params and Closes CTEs, the SELECT and the WHERE clause with its NOT (...) test. The result grid shows AccountNumber, AccountName, AccountType, AccountSubType, Balance, DebitBalance, CreditBalance and Postings for the first accounts, the cash row outlined; the message pane reports one row for each account with postings."
    data: The trial-balance query for the last year-end, run read-only.
---
{% set g = ch17_g1 %}
# Requirement 1: Build the trial balances and the recorded statements (Chapters 6, 10, and 11)

{{ header() }}

## Purpose and learning outcomes

Everything later in the case rests on these trial balances, so this requirement fixes the one rule that makes them comparable: a balance is taken as of a date, and only the closing entries dated on that date are left out. It reuses Chapter 11's Params CTE, Chapter 6's mapping of accounts to statement lines and Chapter 10's anti-join. The analytics type is descriptive.

Students can:

- write one trial-balance query whose as-of date is a parameter, and say which closing entries it leaves out and why (Part 1);
- map every account to a statement line and build recorded statements that agree with control totals they trust (Part 2);
- list the accounts never posted with an anti-join and name what the chart lacks (Part 3).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts, and transactions) and BAR M10 (advanced data analytics); IMA Reporting and Control (financial statement preparation); IFAC IES 2 (a) and 2 (i); AACSB A5 part 5.1 (technology integration: SQL; Excel).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite, a copy of the download, with `LenderPackage.sql` open in DB Browser for SQLite, and Charles River Lender Package.xlsx with its Documentation worksheet.
- **Data conditions.** GLEntry.VoucherNumber holds the EntryNumber of a journal entry, and JournalEntry.EntryType marks the closes: two at each year-end, {{ closes|join(', ') }}. The opening entry belongs to the first fiscal year. The chart has {{ g.headers }} header accounts, which never post. Fiscal {{ d.N }} holds supplier payments only, so a query with no as-of date returns no year-end balance.
- **Verify first.** The query returns {{ rec[0].n }}, {{ rec[1].n }} and {{ rec[2].n }} rows for the three year-ends, with equal debit and credit balances at each.

## How to run it

Pairs, about 90 minutes: 25 for the query, 10 for the reruns and the net income check, 35 for the mapping and statements, 10 for the control totals, 10 for the anti-join. The routine for every query: type it at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the mapping formula until students have listed the subtypes, and Chapter 6's control totals until their balance sheet balances. **Collect** the script and the workbook.

{{ figure('IF-17-1-A') }}

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

**Check:** {{ rec[2].n }} rows, {{ rec[2].zero }} at zero, and debit and credit balances of ${{ rec[2].debits|money }}, Chapter 6's control total.

**Step 2. Rerun it for the other year-ends.** Change only the date in Params and keep each result (**Copy with Headers**, Ctrl+Shift+C).

**Check:** {{ d.F }}: {{ rec[0].n }} accounts, {{ rec[0].zero }} at zero, balances of ${{ rec[0].debits|money }}. {{ d.P }}: {{ rec[1].n }}, {{ rec[1].zero }}, ${{ rec[1].debits|money }}. **Watch for:** four wrong versions, each the model query with one change.

- A strict less-than drops every posting of the last day. It still balances, so nothing flags it, but the total is ${{ g.shortfall|money }} short of Chapter 6.
- Leaving out every close gives {{ g.every.accounts }} accounts, {{ g.every.zero }} at zero and balances of ${{ g.every.debits|money }}. Revenue holds three years (`4010` reads ${{ g.rev_every|money }}, not ${{ g.rev_base|money }}) and retained earnings reads ${{ g.re_every|money }}, not ${{ g.re_base|money }}, because the earlier closes moved those years' income into it.
- Leaving every close in zeroes the revenue and expense accounts: {{ g.none.zero }} accounts at zero.
- Filtering on the fiscal year gives {{ g.year.accounts }} accounts and cash of -${{ (g.cash_change|abs)|money }}, the year's change, because the opening balances are earlier postings.

**Step 3. Check net income against the closes.** The script's net income query sums each year's revenue and expense postings, closes excluded, beside the credit to retained earnings in that year's Income Summary close.

**Check:** ${{ ni[0]|money }}, ${{ ni[1]|money }} and ${{ ni[2]|money }}, each equal to its close.

### Part 2: The workbook

**Step 4. Put each trial balance on its own worksheet.** Paste the results into TB {{ d.F }}, TB {{ d.P }} and TB {{ d.C }}. The model workbook builds the same lists with formulas and a Power Query ledger summary driven by an as-of date, so they refresh; it agrees with the query to the cent, and either is acceptable. Excel fits because the adjustments will sit beside the balances.

**Step 5. Map each account to a statement line.** Add a Working TB Table, one row for each account, with a StatementLine column. The model maps by AccountSubType and account number:

```jinja
{{ g.f_map }}
```

**Check:** every account with postings has a line. **Watch for:** signing each account by its NormalBalance. The contra assets are then added to the assets they reduce: total assets read ${{ g.nb_assets|money }}, not ${{ g.ta|money }}.

**Step 6. Build the recorded balance sheets and statements of income.** Use SUMIFS on the Working TB columns by line: assets as recorded, liabilities and equity reversed. Before the year's close, retained earnings are the negative of account `3030` plus that year's net income.

**Check:** total assets ${{ rec[0].ta|money }}, ${{ rec[1].ta|money }} and ${{ rec[2].ta|money }}, and each balance sheet balances. **Watch for:** retained earnings taken from `3030` alone. The sheet is then out of balance by the year's net income, ${{ g.gap|money }} at the last year-end.

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

**Check:** {{ n_never }} rows, {{ n_active }} active and {{ n_inactive }} inactive. **Watch for:** without the header filter the list has {{ g.no_hdr }} rows; an inner join in place of the left join returns {{ g.inner|count }}, which looks like a complete ledger.

**Step 9. Say what the chart lacks.**

```sql
-- Requirement 1: the accounts named for taxes, to see what the chart lacks
-- Population: the chart; expected: sales tax and payroll taxes only, no income tax account
SELECT AccountNumber, AccountName, AccountType, AccountSubType
FROM Account
WHERE AccountName LIKE '%Tax%'
ORDER BY AccountNumber;
```

**Check:** {{ g.taxes }} rows, sales tax and payroll taxes: the chart has no income tax account, neither an expense nor a payable. Several unused accounts lead to later requirements: interest payable (Requirement 4), the allowance for doubtful accounts (Requirement 5), leases and interest income (Requirement 9).

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Accounts with postings; at zero, {{ d.F }}, {{ d.P }}, {{ d.C }} | {{ rec[0].n }}, {{ rec[1].n }}, {{ rec[2].n }}; {{ rec[0].zero }}, {{ rec[1].zero }}, {{ rec[2].zero }} | 1, 2 |
| Debit balances, equal to the credit balances | ${{ rec[0].debits|money }}; ${{ rec[1].debits|money }}; ${{ rec[2].debits|money }} | 1, 2 |
| Net income | ${{ ni[0]|money }}; ${{ ni[1]|money }}; ${{ ni[2]|money }} | 3 |
| Total assets | ${{ rec[0].ta|money }}; ${{ rec[1].ta|money }}; ${{ rec[2].ta|money }} | 6 |
| Gross margin and operating income, {{ d.C }} | ${{ inc[1].gm|money }}; ${{ inc[1].op|money }} | 6 |
| Never posted; active; inactive | {{ n_never }}; {{ n_active }}; {{ n_inactive }} | 8 |

{{ expected() }}

## What a strong answer says

- **The rule.** A trial balance leaves out only the closes dated on its own as-of date, because earlier closes already moved their income into retained earnings.
- **The mapping.** Lines by AccountSubType and account number, the contra accounts and `1090` placed on purpose, the year's income in retained earnings before the close.
- **The validation.** Agreement with Chapter 6 to the cent, and every trial balance and balance sheet balancing.
- **The gaps.** Accounts never posted, and the missing income tax account named as a matter for the CFO rather than given a number.

A weak answer reports balances without control totals, or lists unused accounts without saying which ones matter.

## Common mistakes and how to respond

- **A strict less-than.** *Symptom:* equal debits and credits, ${{ g.shortfall|money }} short. *Response:* ask where the postings of the last day went.
- **Every close left out.** *Symptom:* revenue that holds three years. *Response:* ask what an earlier close did to that income and where it sits now.
- **Contra accounts added.** *Symptom:* assets ${{ g.nb_extra|money }} too high. *Response:* ask what a contra account reduces.
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
