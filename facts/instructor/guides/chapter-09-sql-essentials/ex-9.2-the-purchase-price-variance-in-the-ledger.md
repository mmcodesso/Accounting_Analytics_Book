---
note: ch09.ex2
uses: [ch09.g2]
title: The Purchase Price Variance in the Ledger
kind: exercise
number: '9.2'
unit: '9'
perspective: financial
tool: sql
minutes: 60
solution: "Chapter09-exercises-sql.zip: Ex 9.2.sql"
figures:
  - id: IF-09-2-A
    kind: sql-mock
    purpose: The ten largest unfavorable purchase variances of the year, with the tie-break visible.
    shows: "The Execute SQL tab on the tab Ex 9.2.sql. The editor holds the comment lines and the query of Step 5 with ORDER BY Debit DESC, PostingDate, VoucherNumber and LIMIT 10. The grid shows GLEntryID, PostingDate, VoucherNumber, Debit and Description for ten rows, with the two rows that share an amount outlined. The message pane reports ten rows returned."
    data: GLEntry for the purchase price variance account in the current fiscal year, the Step 5 query, run read-only on the dataset.
---
{% set g = ch09_g2 %}
# Exercise 9.2: The Purchase Price Variance in the Ledger

{{ header() }}

## Purpose and learning outcomes

Cost of goods sold holds a second variance account, and the controller wants to know what it records and how it differs from the manufacturing variance of the tutorials. Students repeat the tutorial's pattern on a new account: find the AccountID, list the source document types, set the closing entry apart, and rank the postings. The new ideas are matching a stored description exactly and counting with the message pane. The analytics type is descriptive.

By the end, students can:

- filter the ledger by AccountID and fiscal year and explain why a missing year changes the answer (outcome 3);
- use DISTINCT to learn the values a column holds before filtering on one (outcomes 2 and 3);
- sort and limit to rank postings, and break a tie (outcome 5);
- say what a debit and a credit to the account mean, and how this variance arises compared with the manufacturing variance (outcome 6).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S1 M1 to M3; IMA Reporting and Control (cost accounting) and Data Analytics and Insights (data tools); IFAC IES 2 (a) and (b); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** CharlesRiver_Work.sqlite and Tutorial 9.2's pattern. Students save `Ex 9.2.sql`.
- **Data conditions.** The account has postings in three fiscal years ({{ g.all_rows|count }} rows in all, {{ g.year_rows|count }} in the current year), so FiscalYear matters. The text of Description is matched exactly. Only the close is a JournalEntry posting; the rest are PurchaseInvoice postings.
- **Verify first.** The Account table gives AccountID {{ g.ppv }} for account {{ g.no5060 }}.

## How to run it

Individual, about 60 minutes: 10 for requirements (1) and (2), 10 for (3), 15 for (4), 10 for (5) and 15 for (6). The routine of Exercise 9.1 applies: type the comment lines and query at the end of the script, select it, click **Execute all/selected SQL** and read the message pane. Hold back the point that unfavorable contains favorable until a student's counts in (5) do not add up, and the tie-break until the ten largest differ between two students. Collect the script and the comparison.

## Step-by-step solution

### Requirement (1): The AccountID

**Step 1. Look up AccountID by account number.**

```sql
-- Requirement (1): the AccountID of account 5060
-- Population: Account; expected: AccountID 55
SELECT AccountID, AccountNumber, AccountName
FROM Account
WHERE AccountNumber = 5060;
```

**Check:** one row, AccountID {{ g.ppv }}; the message pane says "1 rows". **Watch for:** the account number used as AccountID in later steps returns {{ g.as_id }} rows, because no ledger row has that key.

### Requirement (2): The source documents and the close

**Step 2. List the source document types of the year.**

```sql
-- Requirement (2): the source document types of 5060's postings in fiscal 2026
-- Population: GLEntry, AccountID 55, fiscal 2026; expected: JournalEntry and PurchaseInvoice
SELECT DISTINCT SourceDocumentType
FROM GLEntry
WHERE AccountID = 55 AND FiscalYear = 2026
ORDER BY SourceDocumentType;
```

**Check:** {{ g.kinds }} rows, JournalEntry and PurchaseInvoice.

**Step 3. Look at the journal entry.**

```sql
-- Requirement (2): the JournalEntry posting, which the analysis excludes
-- Population: GLEntry, AccountID 55, fiscal 2026, JournalEntry; expected: the close JE-2026-000296
SELECT GLEntryID, PostingDate, Debit, Credit, VoucherNumber,
    Description
FROM GLEntry
WHERE AccountID = 55 AND FiscalYear = 2026
    AND SourceDocumentType = 'JournalEntry';
```

**Check:** one row: {{ close }}, a credit of ${{ close_amount|money }} dated {{ g.close_date }}. It brings the account to zero for the new year, so a total over every row of the year is zero.

### Requirement (3): The descriptions

**Step 4. List the descriptions of the remaining postings.**

```sql
-- Requirement (3): the descriptions of the remaining postings
-- Population: GLEntry, AccountID 55, fiscal 2026, PurchaseInvoice; expected: three descriptions
SELECT DISTINCT Description
FROM GLEntry
WHERE AccountID = 55 AND FiscalYear = 2026
    AND SourceDocumentType = 'PurchaseInvoice'
ORDER BY Description;
```

**Check:** 3 rows: unfavorable purchase variance, favorable purchase variance and nonrecoverable purchase tax. **Watch for:** without the SourceDocumentType condition there are {{ g.desc_all }} values, the close's description among them.

### Requirement (4): The ten largest unfavorable variances

**Step 5. Rank the unfavorable postings.**

```sql
-- Requirement (4): the ten largest unfavorable purchase variances
-- Population: GLEntry, AccountID 55, fiscal 2026, unfavorable variances; expected: largest 796.29
SELECT GLEntryID, PostingDate, VoucherNumber, Debit, Description
FROM GLEntry
WHERE AccountID = 55 AND FiscalYear = 2026
    AND Description = 'Record unfavorable purchase variance'
ORDER BY Debit DESC, PostingDate, VoucherNumber
LIMIT 10;
```

{{ figure('IF-09-2-A') }}

**Check:** 10 rows, the largest ${{ largest|money }} dated {{ postings[0].date }} on voucher {{ postings[0].voucher }}, then ${{ next[0]|money }} and ${{ next[1]|money }}. Two postings share ${{ g.tie|money }}, so their order depends on the tie-break; the tenth amount is not tied, so the ten postings are the same for everyone. **Watch for:** without the year condition the ranking mixes fiscal years and starts at ${{ g.top_all_first|money }}. `ORDER BY Debit` without DESC starts at ${{ g.smallest|money }}. Sorting on Credit leaves the rows in no order, because every unfavorable posting has a credit of zero. The description must be typed exactly as stored; `'Unfavorable purchase variance'` returns no rows.

### Requirement (5): Counting each description

**Step 6. Count the three kinds of posting.** The message pane gives the count, because COUNT comes in Chapter 10.

a. Type and run the three queries below, one at a time.
b. Read "Result: N rows returned" for each.

```sql
-- Requirement (5): the postings described as unfavorable purchase variance (count in the message pane)
-- Population: GLEntry, AccountID 55, fiscal 2026; expected: 12,389 debits, 167,063.83
SELECT GLEntryID, PostingDate, VoucherNumber, Debit, Credit
FROM GLEntry
WHERE AccountID = 55 AND FiscalYear = 2026
    AND Description = 'Record unfavorable purchase variance';
```

```sql
-- Requirement (5): the postings described as favorable purchase variance (count in the message pane)
-- Population: GLEntry, AccountID 55, fiscal 2026; expected: 7,270 credits, 57,497.25
SELECT GLEntryID, PostingDate, VoucherNumber, Debit, Credit
FROM GLEntry
WHERE AccountID = 55 AND FiscalYear = 2026
    AND Description = 'Record favorable purchase variance';
```

```sql
-- Requirement (5): the postings described as nonrecoverable purchase tax (count in the message pane)
-- Population: GLEntry, AccountID 55, fiscal 2026; expected: 3,897 debits, 66,444.78
SELECT GLEntryID, PostingDate, VoucherNumber, Debit, Credit
FROM GLEntry
WHERE AccountID = 55 AND FiscalYear = 2026
    AND Description = 'Record nonrecoverable purchase tax';
```

**Check:** {{ unf.n|count }}, {{ fav.n|count }} and {{ tax.n|count }} rows, {{ pi_rows|count }} in all, with no thousands separator in the pane. The unfavorable and tax rows carry only debits and the favorable rows only credits. **Watch for:** without the year condition the unfavorable count is {{ g.unf_all|count }}. `Description LIKE '%favorable%'` returns {{ g.like_fav|count }} rows, the favorable and the unfavorable together, because unfavorable contains favorable.

### Requirement (6): The comparison

**Step 7. Outline the comparison.** See "What a strong answer says". A student can copy the three results into Excel with **Copy with Headers** and add the debits and credits; SUM in SQL comes in Chapter 10.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| AccountID of the account | {{ g.ppv }} | 1 |
| Source document types; the close | 2; {{ close }}, a credit of ${{ close_amount|money }} | 2, 3 |
| Descriptions of the PurchaseInvoice postings | 3 | 4 |
| Largest unfavorable variance, with the next two | ${{ largest|money }}; ${{ next[0]|money }}; ${{ next[1]|money }} | 5 |
| Unfavorable, favorable and tax postings | {{ unf.n|count }}; {{ fav.n|count }}; {{ tax.n|count }} | 6 |
| Their amounts, and the net equal to the close | ${{ unf.amount|money }}; ${{ fav.amount|money }}; ${{ tax.amount|money }}; ${{ net|money }} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The close is excluded because it clears the account, so the year nets to zero with it; a journal entry that adjusted the variance would stay. This is the trap of Tutorial 9.2 and of the Part I case.
- **Requirement (3).** The account holds two kinds of cost: the invoice price against the purchase-order price at which the goods were received (goods received not invoiced is cleared at the receipt value), and purchase tax that cannot be recovered.
- **Requirement (5).** A credit means the supplier billed below the order price, a favorable variance. A handful of one-cent debits and credits on lines billed at the order price are rounding ({{ rounding }}).
- **Requirement (6).** Purchase price variance arises when a supplier invoice is posted, from PurchaseInvoice documents; manufacturing variance arises when a work order closes, from WorkOrderClose documents. One measures buying, the other making.

A weak answer calls the account a loss, or misses that the total includes the close.

## Common mistakes and how to respond

- **The account number as AccountID.** *Symptom:* {{ g.as_id }} rows. *Response:* ask which key GLEntry holds.
- **No year, or the close left in.** *Symptom:* {{ g.unf_all|count }} unfavorable postings in place of {{ unf.n|count }}, or a total of zero. *Response:* ask which fiscal year the controller asked about, and what the close does.
- **A LIKE on favorable.** *Symptom:* {{ g.like_fav|count }} rows in place of {{ fav.n|count }}. *Response:* ask what the word unfavorable contains.
- **A description typed from memory.** *Symptom:* no rows. *Response:* run DISTINCT on Description and copy it.
- **The sort in the wrong direction or column.** *Symptom:* cents, or no order. *Response:* ask what ASC means and what Credit holds on these rows.
- **No tie-break.** *Symptom:* two students list the fifth and sixth postings in a different order. *Response:* add the date and voucher number.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the AccountID | 10 | AccountID found by account number | Read from the grid |
| Requirement 2: types and close | 20 | Both queries, the close identified and the exclusion explained | Close found, no reason |
| Requirement 3: descriptions | 20 | DISTINCT on the right population, two kinds of cost | Descriptions listed only |
| Requirement 4: ranking | 20 | Exact description, DESC, tie-break, LIMIT | Ranking without a tie-break |
| Requirement 5: counts | 15 | Three counts, and what a credit means | Counts only |
| Requirement 6: comparison | 15 | Source documents and the buying and making contrast | Definitions without the contrast |

## Extensions and discussion questions

- In Chapter 10, total the three descriptions with SUM and tie the net to the close.
- Discuss: the account holds unrecoverable tax as well as price variances. Should a controller report them together?
- Discuss: which variance would you review first at a month-end, and what would you ask for?
