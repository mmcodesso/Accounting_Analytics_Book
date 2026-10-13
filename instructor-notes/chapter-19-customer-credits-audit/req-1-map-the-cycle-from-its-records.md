# Requirement 1: Map the cycle from its records (Chapters 3, 10, and 12)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 1 |
| Perspective | Auditing |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 120 minutes |
| Solution file | Chapter19-capstone-sql.zip: Credits.sql, the queries headed Requirement 1 (tests M1 to M8); Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Cycle Map (the same map, in formulas, for the report's appendix) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Every later test rests on a picture of the cycle that comes from its records, not from how the process is described. The picture is a profile of each table, a test of every link in both directions, a trace of each document to the ledger and back, and a list of who records what. Joins, anti-joins and counts over the whole cycle fit a query, which repeats exactly. The analytics type is descriptive. The requirement ends with the audit's first judgment: for each control point, what the records can evidence and what must still be asked outside the database.

Students can profile a table and read the profile as evidence (Part 1), test a link both ways and say what a clean result proves (Part 2), map a document to its postings and its recorders (Part 3), and state the limits of the evidence at each control point (Part 4).

**Competencies practiced.** CPA Evolution Core S2 M4 (information technology and IT controls) and ISC M4 (use and management of data); IMA Data Analytics and Insights (data literacy); IFAC IES 2 (g) and IES 3 (a); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite, a copy of the download, with Credits.sql open in DB Browser for SQLite and its header complete. Credits Audit.xlsx is needed only for the appendix version of the map.
- **Data conditions.** The returns, credits, refunds and commission tables are new to students' queries. A document's ledger rows are found by SourceDocumentType and SourceDocumentID together, because the IDs of different documents overlap, and GLEntry.AccountID is the surrogate key of Account. The tables end on different dates: returns 2026-12-24, credits 2026-12-26, refunds 2026-12-22, receipts 2026-12-31. The generator plants no anomaly in this cycle, so the map is clean; the patterns found later come from how the data were produced.
- **Verify first.** Run M1 to M8 on a copy: each returns in a fraction of a second, and M4 to M6 show no orphan, no unposted document and no gap.

## How to run it

Pairs, about 120 minutes: 25 for the profiles, 30 for the links and the numbering, 25 for the matrix and the people, 25 for the marked figure, 15 for the appendix map. The routine for every query: type it at the end of Credits.sql under its two comment lines, select it, choose **Execute all/selected SQL**, read the row count in the message pane. Hold back the second direction of each link until a student reports "no orphans" from one anti-join. **Collect** Credits.sql and the marked figure.

## Step-by-step solution

### Part 1: Profile each table (tests M1 to M3)

**Step 1. Profile the tables.** M1 is one SELECT for each table, joined by UNION ALL: records, distinct document numbers, first and last date, customers, amount and a count of rows missing a key. The first block shows the pattern.

```sql
SELECT 'SalesReturn' AS TableName, COUNT(*) AS Records,
    COUNT(DISTINCT ReturnNumber) AS DistinctKeys,
    MIN(ReturnDate) AS FirstDate, MAX(ReturnDate) AS LastDate,
    COUNT(DISTINCT CustomerID) AS Customers, NULL AS Amount,
    SUM(CASE WHEN ReturnDate IS NULL OR CustomerID IS NULL
        OR ReceivedByEmployeeID IS NULL THEN 1 ELSE 0 END) AS Missing
FROM SalesReturn
```

**Check:** 11 rows; Records equals DistinctKeys in every row and Missing is zero. M2 (15 rows) lists the values of each status, reason and method column.

**Step 2. Read the days between the steps (M3).** Credits are dated 0 to 3 days after the return (mean 1.4), every approval carries the credit's date, and refunds come 2 to 94 days after the credit, clearing 0 to 3 days later. **Check:** 4 rows. The lags say how long to wait before a period's returns are complete (Requirement 5), and the records hold dates, not times (Requirement 4).

### Part 2: Test every link (tests M4 to M6)

**Step 3. Test each link both ways with an anti-join (M4).** Each link is tested from the parent and from the child. Two of the tests show the pattern.

```sql
SELECT 'Credits without a return', COUNT(*)
FROM CreditMemo AS x
    LEFT JOIN SalesReturn AS y
        ON y.SalesReturnID = x.SalesReturnID
WHERE y.SalesReturnID IS NULL
```

```sql
SELECT 'Refunded credits without a refund', COUNT(*)
FROM CreditMemo AS x
    LEFT JOIN CustomerRefund AS y
        ON y.CreditMemoID = x.CreditMemoID
WHERE y.CustomerRefundID IS NULL
    AND x.Status = 'Refunded'
```

**Check:** 15 rows, every Orphans value zero. **Watch for:**

- Every credit anti-joined to the refunds returns 390 rows. They are not orphans: credits in status Applied or Issued have no refund, so the test adds the status. The 390 also proves the anti-join can find rows.
- An anti-join written with INNER JOIN returns 0 rows whatever the data hold.

**Step 4. Trace each document to the ledger and back (M5).** Count the ledger rows with no document and the documents with no ledger rows, matching on the type and the ID together.

```sql
SELECT 'CreditMemo',
    (SELECT COUNT(*)
     FROM GLEntry AS gl
        LEFT JOIN CreditMemo AS x
            ON x.CreditMemoID = gl.SourceDocumentID
     WHERE gl.SourceDocumentType = 'CreditMemo'
        AND x.CreditMemoID IS NULL),
    (SELECT COUNT(*)
     FROM CreditMemo AS x
     WHERE NOT EXISTS (
        SELECT 1
        FROM GLEntry AS gl
        WHERE gl.SourceDocumentType = 'CreditMemo'
            AND gl.SourceDocumentID = x.CreditMemoID))
```

**Check:** 6 rows, every column zero. **Watch for:** the ID alone. The credits' own 1,988 ledger rows become 33,352 rows of 19 document types, and the join can run for minutes, because the ledger's index starts with the type.

**Step 5. Test the numbering (M6).** Read the year and the sequence out of each number, then list for each series and year the first and last number, the gaps and the break from the previous year.

```sql
SELECT Series, FiscalYear, FirstNumber, LastNumber, Documents,
    LastNumber - FirstNumber + 1 - DistinctNumbers AS Gaps,
    Documents - DistinctNumbers AS Repeats,
    FirstNumber - 1 - LAG(LastNumber) OVER (
        PARTITION BY Series ORDER BY FiscalYear) AS BreakFromLastYear
FROM ByYear
ORDER BY Series, FiscalYear
```

**Check:** 12 rows, no gap, no repeat, and each year starts where the last ended (the credits run 1-158, 159-390, 391-612). **Watch for:** a test that restarts at 1 each year flags 8 of the 12 series-years falsely; and the clawback numbers have a four-letter prefix, so the position that works for the other series reads their year as zero in all 637 rows. Numbering finds gaps inside a series, not a document that was never numbered.

### Part 3: Postings and people (tests M7 and M8)

**Step 6. Build the posting matrix (M7).** One row for each source document and account, joining Account for the account number.

```sql
SELECT gl.SourceDocumentType, a.AccountNumber, a.AccountName,
    SUM(CASE WHEN gl.Debit > 0 THEN 1 ELSE 0 END) AS DebitRows,
    ROUND(SUM(gl.Debit), 2) AS Debits,
    SUM(CASE WHEN gl.Credit > 0 THEN 1 ELSE 0 END) AS CreditRows,
    ROUND(SUM(gl.Credit), 2) AS Credits
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
```

**Check:** 18 rows. A credit debits `4060`, `4050` and `2050` and credits `1020`, `2060` or both: 28 credits post to both, so the credit rows on the two accounts (415 and 225) outnumber the 612 credits. Every receipt credits `2060` and every application debits it (14,818 and 54,234 rows): the hub. **Watch for:** `AccountID = 4060` returns no rows, because `4060` is AccountID 47.

**Step 7. Say who records each document (M8).** Union the person each document names, join Employee and CostCenter, and count by job title.

```sql
SELECT p.Document, p.Role, e.JobTitle, cc.CostCenterName,
    COUNT(*) AS Documents, COUNT(DISTINCT p.EmployeeID) AS Employees
FROM People AS p
    INNER JOIN Employee AS e ON e.EmployeeID = p.EmployeeID
    LEFT JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
GROUP BY p.Document, p.Role, e.JobTitle, cc.CostCenterName
ORDER BY p.Document, Documents DESC
```

**Check:** 14 rows. The warehouse receives the returns (Inventory Specialists: 243; Shipping Clerks: 240; the Warehouse Manager: 129). Customer service approves the credits (414 by representatives, 198 by the manager), records the receipts and applies every payment. Administration approves the refunds. **Watch for:** GLEntry.CreatedByEmployeeID as the preparer. On every row of the cycle it names the document's own approver or recorder (test T5 of Requirement 4).

### Part 4: Mark the figure

**Step 8. For each control point, say what the records evidence.** Students mark the book's map of the cycle with its nine control points. The model answer:

| Point | The records evidence | Outside the database |
|---|---|---|
| C1 | Every credit traces to a return the warehouse received | Inspection of the goods, a carrier claim |
| C2 | The approver and the general limit on each credit | The delegation of authority, the preparer |
| C3 | Each credit line against its return, shipment and invoice | Nothing material |
| C4 | Who recorded and who applied each receipt | Cash handled outside the system |
| C5 | A clawback for each line, with base, rate and amount | Whether representatives were told |
| C6 | The refund's approver, title and limit | The delegation for refunds, the preparer |
| C7 | The refund date against the payments applied | Bank clearance, the customer's request |
| C8 | The refund's method against the receipts', open balances | The payee, the account, the request |
| C9 | Receipt, deposit and application dates | Remittance advices, bank records |

> **[Figure placeholder IF-19-1-A]** The book's map of the cycle marked up the way Part 4 asks, the end state of the requirement.
> Kind: diagram · Shows: The five documents of the cycle with their departments and the hub account, and the nine control-point badges in three styles: the records evidence it, the records evidence part of it (the missing evidence written beside the badge), the evidence lies outside the database. A legend names the styles and does not rely on color alone. · Data: The nine control-point rows of the Cycle Map worksheet (what the records evidence, what they cannot show). · Status: planned

**Check:** the Cycle Map worksheet holds the same table beside the exceptions the later tests find; C1, C3, C5, C9 show none. Its populations and matrix are formulas on the Tables loaded from CharlesRiver.xlsx, for example a matrix cell:

```
=SUMIFS(Ledger[Debit],Ledger[SourceDocumentType],$A48,Ledger[AccountNumber],B$47)-SUMIFS(Ledger[Credit],Ledger[SourceDocumentType],$A48,Ledger[AccountNumber],B$47)
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Returns; lines; customers | 612; 637; 162 | 1 |
| Credits; refunds; clawbacks | 612; 222; 637 | 1 |
| Receipts; applications | 7,409; 27,117 | 1 |
| Orphans, unposted documents, gaps | none in M4 to M6 | 3 to 5 |
| Credits posting to both `1020` and `2060` | 28 | 6 |

> **Instructor notes, Requirement 1:** returns 612 (637 lines), 2024-01-25 to 2026-12-24, 162 customers; Credited 390, Refunded 222; reasons Late Delivery 141, Wrong Item 120, Customer Remorse 119, Damaged 117, Quality Concern 115; received by Inventory Specialists 243, Shipping Clerks 240, the Warehouse Manager 129. Credit memos 612 (637 lines), 2024-01-28 to 2026-12-26: Applied 387 (385,514.61), Refunded 222 (243,317.84), Issued 3 (3,413.46), total 632,245.91; approved by Customer Service Representatives 414 and the Customer Service Manager 198; ApprovedDate equals CreditMemoDate on all 612; 0-3 days after the return (mean 1.4, 175 the same day). Refunds 222 (216,718.42), one per refunded credit, 2024-02-17 to 2026-12-22, 2-94 days after the credit (mean 11.0; 14 over 30 days), cleared 0-3 days later; approved by Administrative Specialists 84, Staff Accountants 79, the Accounting Manager 59. Clawbacks 637 (10,832.09), one per credit line, same date and approver as the credit. Receipts 7,409 (87,896,623.29) recorded by customer service (manager 2,493, representatives 4,916); 27,117 applications, all by customer service. No orphans in any direction; numbers run without gaps and continue across years (SR and CM 1-158, 159-390, 391-612; RF 1-55, 56-139, 140-222; SCAJ 1-167, 168-405, 406-637). Posting matrix (GL rows): CreditMemo Dr 4060 637 rows 589,524.29, Dr 4050 99 rows 4,133.82, Dr 2050 612 rows 38,587.80, Cr 1020 415 rows 412,114.03, Cr 2060 225 rows 220,131.88 (28 credits post to both); SalesReturn Dr 1040 325,840.19, Cr 5010-5040; CustomerRefund Dr 2060, Cr 1010 216,718.42; SalesCommissionAdjustment Dr 2034, Cr 6290 10,832.09; CashReceipt Dr 1010, Cr 2060 (14,818 rows); CashReceiptApplication Dr 2060, Cr 1020 (54,234 rows). GLEntry.CreatedByEmployeeID equals the document's approver, recorder, or applier on 100% of the cycle's rows (and is the CEO on every SalesInvoice row, the CFO on every DisbursementPayment row), and neither CreditMemo nor CustomerRefund has a preparer column: the records cannot show who prepared a credit or a refund, which is not evidence of self-approval. No document was recorded by anyone before hire or after termination. The records cannot evidence C1's inspection of the goods, C8's payee and account, or the customer's request; the generator's AnomalyLog plants nothing in this cycle, so every pattern found here comes from how the data were produced, which the notes below name where it matters.

## What a strong answer says

- **The map comes from the records:** every link tested both ways, every document traced to the ledger and back, the numbering tested, each result reported with its population, clean or not.
- **A clean result is bounded.** An anti-join finds a record that points at nothing, not the record never made; completeness rests on the numbering and on Requirement 2.
- **The limits are named by control point** and carried forward to the sample (Requirement 6) and the report (Requirement 9).
- **The duties are seen:** customer service records receipts, applies cash and approves credits and clawbacks.

A weak answer reports zero orphans without the test, takes the process from the narrative, or reads the ledger's creator as the preparer.

## Common mistakes and how to respond

- **Every credit without a refund.** *Symptom:* 390 orphans. *Response:* ask which credits should have a refund.
- **An anti-join with INNER JOIN.** *Symptom:* zero rows for every link. *Response:* ask what the test would show if a row were missing.
- **The ID alone.** *Symptom:* 33,352 ledger rows for the credits, or a query that will not finish. *Response:* ask which pair of columns identifies a document.
- **A gap test that restarts each year.** *Symptom:* false gaps in 8 series-years. *Response:* ask where the second year starts, and look at the clawback prefix.
- **The ledger's creator as preparer.** *Symptom:* "the approver prepared every credit". *Response:* ask what the same column says on the sales invoices.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Profiles and timing (M1 to M3) | 20 | Every table, keys, dates, statuses, lags | No lags or end dates |
| Links and ledger trace (M4, M5) | 30 | Both directions, type and ID together, the clean result explained | One direction, or a join that cannot fail |
| Numbering (M6) | 10 | Gaps, repeats and the break between years | Gaps in one year only |
| Postings and people (M7, M8) | 20 | Matrix by account number, roles by job title, the hub seen | Rows without the reading |
| Marked map | 20 | Nine points, each with evidence and limits | Evidence without limits |

## Extensions and discussion questions

- Discuss: no orphan, no gap, every document posted. What could still be wrong with the cycle?
- Discuss: one department records the cash and approves the credits. Which control point does that touch, and which test will measure it?
