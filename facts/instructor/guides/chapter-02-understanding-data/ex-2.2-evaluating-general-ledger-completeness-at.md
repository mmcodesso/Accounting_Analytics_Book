---
note: ch02.t2
title: Evaluating General Ledger Completeness at Charles River
kind: exercise
number: '2.2'
unit: '2'
perspective: financial
tool: conceptual
minutes: 50
solution: ''
figures:
  - id: IF-02-2-A
    kind: excel-mock
    purpose: The PivotTable of ledger rows by fiscal year and fiscal period, with the three small periods marked.
    shows: A PivotTable with FiscalYear and FiscalPeriod in the rows area and the count of GLEntryID in the values area, scrolled to show the first period of the first year and the last periods of the data. The first period and the last two periods are outlined, and each count is visibly smaller than the periods around it. A note beside the table says that the outlined periods sit at the edges of the extract.
    data: GLEntry, counted by FiscalYear and FiscalPeriod (the Step 3 PivotTable).
---
# Exercise 2.2: Evaluating General Ledger Completeness at Charles River

{{ header() }}

## Purpose and learning outcomes

The exercise asks whether the ledger is complete before the financial statements are prepared. It repeats the tests of Tutorial 2.2 and then asks what they prove. Students total the ledger, read its date range and its periods, and list its source types, and they have to say what each result does and does not show. The tests are descriptive.

By the end, students can:

- total debits and credits across a large worksheet and judge the result (chapter outcome 4);
- read a PivotTable of periods and tell the edges of an extract from missing transactions (outcome 3);
- say what equal totals and a full list of source types do and do not show (outcome 6);
- write a one-page completeness assessment with a figure behind every statement.

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (cleansing financial data) and Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Data Literacy and Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx and Tutorial 2.2. Their tutorial totals and PivotTables answer requirements (1) to (3), so let them reuse that work and spend the time on the memo.
- GLEntry has {{ gl_rows|count }} rows. Warn students against formulas copied down every row, and tell them to use a PivotTable.
- The exercise relies on these conditions: total debits equal total credits in GLEntry, and so does every document's set of rows; the ledger begins with a small first period and runs into the next fiscal year with supplier payments only; every fiscal year under review has rows of every source type; and a few ledger rows have neither a debit nor a credit.
- Verify one thing yourself: a difference of two sums of floating-point amounts can leave a residue of a tiny fraction of a cent. Round to the cent before judging.

## How to run it

Individual work with a short pair comparison. For about 50 minutes: 10 on requirement 1, 15 on requirement 2, 10 on requirement 3 and 15 on the memo.

**Hints.** If a student calls the last periods missing transactions, ask what the rows in them are. Hold back the case of the documents that never reached the ledger until the debrief.

## Step-by-step solution

### Requirement (1): Total debits and credits

**Step 1. Total both columns and compare.**

a. On **GLEntry**, sum the Debit column and the Credit column as Tutorial 2.2 Step 4 does, or enter `=SUM(T3_GLEntry[Debit])` and `=SUM(T3_GLEntry[Credit])` anywhere outside the Table.
b. Subtract one from the other, and round the result: `=ROUND(SUM(T3_GLEntry[Debit])-SUM(T3_GLEntry[Credit]),2)`.

**Check:** debits ${{ debit|money }}, credits ${{ credit|money }}, difference ${{ difference|money }}, so the ledger is in balance as a whole. **Watch for:** two traps. A student who counts the rows of each column, not the amounts, gets a meaningless result. And a total that balances does not show that each entry balances, or that no entry is missing: it is the first test, not the last.

### Requirement (2): Date range and periods

**Step 2. Read the range of dates.** Sort **GLEntry** by PostingDate and note the earliest and latest.

**Check:** postings run from {{ first_day }} to {{ last_day }}. The first date is the first day of the first fiscal year, and the last falls in the following fiscal year.

**Step 3. Count the rows in each period.**

a. Insert a PivotTable from **GLEntry** with FiscalYear and FiscalPeriod in the **Rows** area and the count of GLEntryID in the **Values** area.
b. Read the counts and compare each with its neighbors.
c. Filter to the latest fiscal year and read the SourceDocumentType of its rows.

{{ figure('IF-02-2-A') }}

**Check:** {{ periods }} periods. The ordinary ones hold between {{ ordinary_min|count }} and {{ ordinary_max|count }} rows, and the typical one about {{ typical|num(0) }}. Three are far smaller:

| FiscalYear | FiscalPeriod | Rows |
|---:|---:|---:|
{% for r in low %}
| {{ r[0] }} | {{ r[1] }} | {{ r[2]|count }} |
{% endfor %}

The first is the start of the records, the start-up month that Chapter 7 names. The last two hold only supplier payments (DisbursementPayment) that settle invoices of the year before, so they are the edge of the extract and not missing sales or purchases. They do not belong in an analysis of the years under review. **Watch for:** "missing transactions" as the explanation, and a memo that mentions the small periods without the reason.

### Requirement (3): Source types

**Step 4. Count the rows by source type.** Insert a PivotTable with SourceDocumentType in the **Rows** area and the count of GLEntry rows in **Values**, then add FiscalYear to the columns.

**Check:** {{ n_source }} source types, from {{ largest[0] }} ({{ largest[1]|count }} rows) down to {{ smallest[0] }} ({{ smallest[1]|count }}). The six that the exercise names ({{ exercise_types }}) are all present, in every fiscal year under review. In the latest fiscal year only the payments appear. If a type that should post were missing from a period in which the activity took place, that would be a completeness problem: a whole cycle that failed to post.

**Step 5. Say what a full list shows and does not show.** A model answer: every source type appears in every fiscal year under review, so no cycle is absent from the ledger. The list cannot show that every document of each type posted, or that each posted in full. Only a test that starts from the documents can. For example, {{ unposted.MaterialIssue }} material issue headers have no ledger rows and no lines, so there was nothing to post; a count of source types would not reveal them, and a student cannot be expected to find them in Excel. By contrast, all {{ invoices|count }} sales invoices reconcile to the receivable that their rows debit, which is the evidence behind the chapter's traceability section.

**Check:** the answer names what the test shows (each cycle posts) and what it does not (each document posted, accurately and in the right period).

**Step 6. Add the two Tutorial 2.2 checks, if the memo has room.** The ledger holds {{ used }} distinct AccountIDs against {{ n_accounts }} accounts in the chart, and no AccountID is missing from the chart ({{ orphans }} unmatched). {{ zero[1] }} rows have neither a debit nor a credit; all are {{ zero[0] }} rows, on {{ zero_accounts }}, posted on one date ({{ zero[3] }}).

**Check:** the reference test is a clean result worth recording, and the zero rows are reported, not explained away.

### Requirement (4): Write the memo

**Step 7. Outline a one-page memo.** A strong memo has a header and the purpose, then the conclusion up front. The conclusion says that the tests found no gap in the years under review (the ledger balances in total, every period has entries, the edges are explained and every source type appears) and that a completeness conclusion for the financial statements still needs a test that starts from the documents, the extract's specification and the source system's control totals. A table follows with one row per test (what was tested, the result with its figure, and what it shows), then the limits (balance in total, types not documents) and a closing line on what would close the gap, such as a document-to-ledger reconciliation.

**Check:** every statement in the memo has a number or a worksheet behind it.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Total debits | ${{ debit|money }} | Step 1 |
| Total credits | ${{ credit|money }} | Step 1 |
| Difference | ${{ difference|money }} | Step 1 |
| Earliest and latest posting dates | {{ first_day }}; {{ last_day }} | Step 2 |
| Fiscal periods in the ledger | {{ periods }} | Step 3 |
| Rows in the first period, and in the last two | {{ low[0][2]|count }}; {{ low[1][2]|count }} and {{ low[2][2]|count }} | Step 3 |
| Source types in the ledger | {{ n_source }} | Step 4 |
| Distinct AccountIDs; unmatched in the chart | {{ used }}; {{ orphans }} | Step 6 |
| Rows with neither a debit nor a credit | {{ zero[1] }} | Step 6 |

## What a strong answer says

- **Requirement (1).** The totals, the rounded difference, and the limit: balance in total does not show that no entry is missing.
- **Requirement (2).** The date range, the three small periods with their cause, and the conclusion that they are the edges of the extract and fall outside the years under review.
- **Requirement (3).** The source types present, the years in which they appear, and what a full list does and does not show.
- **Requirement (4).** A memo with evidence for each claim and a stated limit.

A weak answer reports "the ledger is complete" from the totals alone, or explains the small periods as missing data.

## Common mistakes and how to respond

- **Balance read as completeness.** *Symptom:* "debits equal credits, so nothing is missing". *Response:* ask what an entry left out with both of its sides would do to the totals.
- **The edges read as gaps.** *Symptom:* "the ledger is missing transactions in the last periods". *Response:* ask what source type is in them.
- **The first period ignored.** *Symptom:* the memo mentions only the last two. *Response:* ask why the first period is small and what the data begins with.
- **Formulas on every row.** *Symptom:* Excel stops responding. *Response:* ask what a PivotTable does with the same rows.
- **Rows counted instead of amounts.** *Symptom:* a count of Debit cells reported as a total. *Response:* ask what a SUM shows that a count does not.
- **Source types listed without a conclusion.** *Symptom:* the list pasted into the memo. *Response:* ask what the reader should conclude from it.
- **A clean test left out.** *Symptom:* no mention of the reference test. *Response:* ask what the reader knows if it is missing.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: totals and balance | 20 | Both totals, a rounded difference and the limit of the test | Totals without a conclusion or a limit |
| Requirement 2: date range and periods | 30 | Range, the three small periods and their cause, the edges separated from the years under review | Periods noted without the cause, or the edges called gaps |
| Requirement 3: source types | 25 | Types present by year, and what a full list does not show | The list without the interpretation |
| Requirement 4: memo | 25 | One page, conclusion first, a figure behind every statement | Narrative without figures |

## Extensions and discussion questions

- Pick one VoucherNumber, filter GLEntry to it and show that its debits equal its credits. Say what that test shows that the total does not.
- Count the rows by source type for each fiscal year in one PivotTable and describe any type whose volume changes a lot.
- Discuss: if the extract had stopped in the middle of a month, which of the tests would have caught it?
- Discuss: what would you request from the accounting team to test that every invoice reached the ledger? (Chapter 3's traced sale and Chapter 12 do it.)
