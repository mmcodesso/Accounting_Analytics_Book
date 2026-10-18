# Exercise 2.2: Evaluating General Ledger Completeness at Charles River

| | |
|---|---|
| Unit | Chapter 2: Understanding Data in Accounting |
| Item | Exercise 2.2 |
| Perspective | Financial accounting |
| Tools | Workbook browsing and written work |
| Time | About 50 minutes |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise asks whether the ledger is complete before the financial statements are prepared. It repeats the tests of Tutorial 2.2 and then asks what they prove. Students total the ledger, read its date range and its periods, and list its source types, and they have to say what each result does and does not show. The tests are descriptive.

By the end, students can:

- total debits and credits across a large worksheet and judge the result (outcome 4);
- read a PivotTable of periods and tell the edges of an extract from missing transactions (outcome 3);
- say what equal totals and a full list of source types do and do not show (outcome 6);
- write a one-page completeness assessment with a figure behind every statement.

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (cleansing financial data) and Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Data Literacy and Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx and Tutorial 2.2. Their tutorial totals and PivotTables answer requirements (1) to (3), so let them reuse that work and spend the time on the memo.
- GLEntry has 815,921 rows. Warn students against formulas copied down every row, and tell them to use a PivotTable.
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

**Check:** debits $731,949,908.31, credits $731,949,908.31, difference $0.00, so the ledger is in balance as a whole. **Watch for:** two traps. A student who counts the rows of each column, not the amounts, gets a meaningless result. And a total that balances does not show that each entry balances, or that no entry is missing: it is the first test, not the last.

### Requirement (2): Date range and periods

**Step 2. Read the range of dates.** Sort **GLEntry** by PostingDate and note the earliest and latest.

**Check:** postings run from 2024-01-01 to 2027-02-23. The first date is the first day of the first fiscal year, and the last falls in the following fiscal year.

**Step 3. Count the rows in each period.**

a. Insert a PivotTable from **GLEntry** with FiscalYear and FiscalPeriod in the **Rows** area and the count of GLEntryID in the **Values** area.
b. Read the counts and compare each with its neighbors.
c. Filter to the latest fiscal year and read the SourceDocumentType of its rows.

![A mock of the PivotTable of ledger rows by fiscal year and fiscal period, with the three small periods marked.](../figures/chapter-02-understanding-data/IF-02-2-A.pdf)

**Check:** 38 periods. The ordinary ones hold between 17,555 and 28,605 rows, and the median of all the periods is 22,601. Three are far smaller:

| FiscalYear | FiscalPeriod | Rows |
|---:|---:|---:|
| 2024 | 1 | 6,162 |
| 2027 | 1 | 444 |
| 2027 | 2 | 82 |

The first is the first month of the extract, the start-up month that Chapter 7 names; the records do not say when the company began. It is part of the first fiscal year, so it stays in an analysis of the years under review, and its low volume is a question for the extract's specification, not evidence of missing records. The last two hold only supplier payments (DisbursementPayment) that settle invoices of the year before. They fall outside the years under review and stay out of their annual totals, but a procedure on settlements after year-end uses them. **Watch for:** "missing transactions" as the explanation, and a memo that mentions the small periods without the reason.

### Requirement (3): Source types

**Step 4. Count the rows by source type.** Insert a PivotTable with SourceDocumentType in the **Rows** area and the count of GLEntry rows in **Values**, then add FiscalYear to the columns.

**Check:** 20 source types, from MaterialIssue (140,252 rows) down to SalesCommissionPayment (392). The six that the exercise names (SalesInvoice, Shipment, PurchaseInvoice, JournalEntry, PayrollPayment, and WorkOrderClose) are all present, in every fiscal year under review. In the latest fiscal year only the payments appear. If a type that should post were missing from a period in which the activity took place, that would be a completeness problem: a whole cycle that failed to post.

**Step 5. Say what a full list shows and does not show.** A model answer: every source type that appears in the ledger appears in every fiscal year under review. That shows activity from each of those sources, not that every expected cycle is there or that every transaction posted. Only a test that starts from the documents can show that each posted, in full. For example, 6 material issue headers have no ledger rows and no lines, though all carry the status Issued; whether they are valid empty documents or missing detail needs the source records and an explanation of the status. A count of source types would not reveal them, and students need not hunt for them (an instructor extension). By contrast, all 20,914 sales invoices reconcile to the receivable that their rows debit, which is the evidence behind the chapter's traceability section. It cannot test a sale that was never invoiced.

**Check:** the answer names what the test shows (each cycle posts) and what it does not (each document posted, accurately and in the right period).

**Step 6. Add the two Tutorial 2.2 checks, if the memo has room.** The ledger holds 71 distinct AccountIDs against 104 accounts in the chart, and no AccountID is missing from the chart (0 unmatched). 128 rows have neither a debit nor a credit; all are PayrollPayment rows, on 1010 Cash and Cash Equivalents and 2030 Accrued Payroll, posted on one date (2024-01-19).

**Check:** the reference test is a clean result worth recording, and the zero rows are reported, not explained away.

### Requirement (4): Write the memo

**Step 7. Outline a one-page memo.** The scenario's statements are for fiscal 2026, so the memo reads the tests on the whole extract as profiling and draws its conclusion for fiscal 2026. A strong memo has a header and the purpose, then the conclusion up front. The conclusion says that the tests found no gap in the years under review (the ledger balances in total, every period has entries, the edges are explained and every source type appears) and that a completeness conclusion for the financial statements still needs a test that starts from the documents, the extract's specification and the source system's control totals. A table follows with one row per test (what was tested, the result with its figure, and what it shows), then the limits (balance in total, types not documents) and a closing line on what would close the gap, such as a document-to-ledger reconciliation.

**Check:** every statement in the memo has a number or a worksheet behind it.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Total debits | $731,949,908.31 | Step 1 |
| Total credits | $731,949,908.31 | Step 1 |
| Difference | $0.00 | Step 1 |
| Earliest and latest posting dates | 2024-01-01; 2027-02-23 | Step 2 |
| Fiscal periods in the ledger | 38 | Step 3 |
| Rows in the first period, and in the last two | 6,162; 444 and 82 | Step 3 |
| Source types in the ledger | 20 | Step 4 |
| Distinct AccountIDs; unmatched in the chart | 71; 0 | Step 6 |
| Rows with neither a debit nor a credit | 128 | Step 6 |

## What a strong answer says

- **Requirement (1).** The totals, the rounded difference, and the limit: balance in total does not show that no entry is missing.
- **Requirement (2).** The date range, the three small periods with their cause, and the conclusion that the first is the extract's first month and stays in the period, while the last two are payments after it.
- **Requirement (3).** The source types present, the years in which they appear, and what a full list does and does not show.
- **Requirement (4).** A memo with evidence for each claim and a stated limit.

A weak answer reports "the ledger is complete" from the totals alone, or explains the small periods as missing data.

## Common mistakes and how to respond

- **Balance read as completeness.** *Symptom:* "debits equal credits, so nothing is missing". *Response:* ask what an entry left out with both of its sides would do to the totals.
- **The edges read as gaps.** *Symptom:* "the ledger is missing transactions in the last periods". *Response:* ask what source type is in them.
- **The first period ignored, or dropped.** *Symptom:* the memo mentions only the last two, or leaves the first month out of the year. *Response:* ask why the first period is small, what the data begins with, and whether its rows belong to the year.
- **Formulas on every row.** *Symptom:* Excel stops responding. *Response:* ask what a PivotTable does with the same rows.
- **Rows counted instead of amounts.** *Symptom:* a count of Debit cells reported as a total. *Response:* ask what a SUM shows that a count does not.
- **Source types listed without a conclusion.** *Symptom:* the list pasted into the memo. *Response:* ask what the reader should conclude from it.
- **A clean test left out.** *Symptom:* no mention of the reference test. *Response:* ask what the reader knows if it is missing.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: totals and balance | 20 | Both totals, a rounded difference and the limit of the test | Totals without a conclusion or a limit |
| Requirement 2: date range and periods | 30 | Range, the three small periods and their cause, the payments after year-end separated from the years under review | Periods noted without the cause, or the edges called gaps |
| Requirement 3: source types | 25 | Types present by year, and what a full list does not show | The list without the interpretation |
| Requirement 4: memo | 25 | One page, conclusion first, a figure behind every statement | Narrative without figures |

## Extensions and discussion questions

- Pick one VoucherNumber, filter GLEntry to it and show that its debits equal its credits. Say what that test shows that the total does not.
- Count the rows by source type for each fiscal year in one PivotTable and describe any type whose volume changes a lot.
- Discuss: if the extract had stopped in the middle of a month, which of the tests would have caught it?
- Discuss: what would you request from the accounting team to test that every invoice reached the ledger? (Chapter 3's traced sale and Chapter 12 do it.)
