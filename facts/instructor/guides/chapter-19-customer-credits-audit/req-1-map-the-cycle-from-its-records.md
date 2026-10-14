---
note: ch19.r1
uses: [ch19.g1]
title: Map the cycle from its records (Chapters 3, 10, and 12)
kind: requirement
number: '1'
unit: '19'
perspective: auditing
tool: sql
minutes: 120
solution: "Chapter19-capstone-sql.zip: Credits.sql, the queries headed Requirement 1 (tests M1 to M8); Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Cycle Map (the same map, in formulas, for the report's appendix)"
figures:
  - id: IF-19-1-A
    kind: diagram
    purpose: The book's map of the cycle marked up the way Part 4 asks, the end state of the requirement.
    shows: "The five documents of the cycle with their departments and the hub account, and the nine control-point badges in three styles: the records evidence it, the records evidence part of it, the evidence lies outside the database. Below the map the nine control points are listed with the missing evidence written beside each badge. A legend names the styles and does not rely on color alone."
    data: The nine control-point rows of the Cycle Map worksheet (what the records evidence, what they cannot show).
---
{% set g = ch19_g1 %}
# Requirement 1: Map the cycle from its records (Chapters 3, 10, and 12)

{{ header() }}

## Purpose and learning outcomes

Every later test rests on a picture of the cycle that comes from its records, not from how the process is described. The picture is a profile of each table, a test of every link in both directions, a trace of each document to the ledger and back, and a list of who records what. Joins, anti-joins and counts over the whole cycle fit a query, which repeats exactly. The analytics type is descriptive. The requirement ends with the audit's first judgment: for each control point, what the records can evidence and what must still be asked outside the database.

Students can profile a table and read the profile as evidence (Part 1), test a link both ways and say what a clean result proves (Part 2), map a document to its postings and its recorders (Part 3), and state the limits of the evidence at each control point (Part 4).

**Competencies practiced.** CPA Evolution Core S2 M4 (information technology and IT controls) and ISC M4 (use and management of data); IMA Data Analytics and Insights (data literacy); IFAC IES 2 (g) and IES 3 (a); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite, a copy of the download, with Credits.sql open in DB Browser for SQLite and its header complete. Credits Audit.xlsx is needed only for the appendix version of the map.
- **Data conditions.** The returns, credits, refunds and commission tables are new to students' queries. A document's ledger rows are found by SourceDocumentType and SourceDocumentID together, because the IDs of different documents overlap, and GLEntry.AccountID is the surrogate key of Account. The tables end on different dates: returns {{ g.last.SalesReturn }}, credits {{ g.last.CreditMemo }}, refunds {{ g.last.CustomerRefund }}, receipts {{ g.last.CashReceipt }}. The generator plants no anomaly in this cycle, so the map is clean; the patterns found later come from how the data were produced.
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

**Check:** {{ g.m1 }} rows; Records equals DistinctKeys in every row and Missing is zero. M2 ({{ g.m2 }} rows) lists the values of each status, reason and method column.

**Step 2. Read the days between the steps (M3).** Credits are dated {{ lag.lo }} to {{ lag.hi }} days after the return (mean {{ lag.mean|num(1) }}), every approval carries the credit's date, and refunds come {{ rf.lo }} to {{ rf.hi }} days after the credit, clearing {{ rf.clo }} to {{ rf.chi }} days later. **Check:** {{ g.m3 }} rows. The lags say how long to wait before a period's returns are complete (Requirement 5), and the records hold dates, not times (Requirement 4).

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

**Check:** {{ g.m4 }} rows, every Orphans value zero. **Watch for:**

- Every credit anti-joined to the refunds returns {{ g.no_refund|count }} rows. They are not orphans: credits in status Applied or Issued have no refund, so the test adds the status. The {{ g.no_refund|count }} also proves the anti-join can find rows.
- An anti-join written with INNER JOIN returns {{ g.inner }} rows whatever the data hold.

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

**Check:** {{ g.m5 }} rows, every column zero. **Watch for:** the ID alone. The credits' own {{ g.own_rows|count }} ledger rows become {{ g.id_rows|count }} rows of {{ g.id_types }} document types, and the join can run for minutes, because the ledger's index starts with the type.

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

**Check:** {{ g.m6 }} rows, no gap, no repeat, and each year starts where the last ended (the credits run {{ nums['CreditMemo'] }}). **Watch for:** a test that restarts at 1 each year flags {{ g.restart }} of the {{ g.m6 }} series-years falsely; and the clawback numbers have a four-letter prefix, so the position that works for the other series reads their year as zero in all {{ g.scaj_zero|count }} rows. Numbering finds gaps inside a series, not a document that was never numbered.

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

**Check:** {{ g.m7 }} rows. A credit debits `4060`, `4050` and `2050` and credits `1020`, `2060` or both: {{ g.both }} credits post to both, so the credit rows on the two accounts ({{ g.rows_1020 }} and {{ g.rows_2060 }}) outnumber the {{ cm.n }} credits. Every receipt credits `2060` and every application debits it ({{ rows['CashReceipt']|count }} and {{ rows['CashReceiptApplication']|count }} rows): the hub. **Watch for:** `AccountID = 4060` returns no rows, because `4060` is AccountID {{ g.id_4060 }}.

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

**Check:** {{ g.m8 }} rows. The warehouse receives the returns ({{ receivers[0][0] }}: {{ receivers[0][1] }}; {{ receivers[1][0] }}: {{ receivers[1][1] }}; {{ receivers[2][0] }}: {{ receivers[2][1] }}). Customer service approves the credits ({{ approvers[0][1] }} by representatives, {{ approvers[1][1] }} by the manager), records the receipts and applies every payment. Administration approves the refunds. **Watch for:** GLEntry.CreatedByEmployeeID as the preparer. On every row of the cycle it names the document's own approver or recorder (test T5 of Requirement 4).

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

{{ figure('IF-19-1-A') }}

**Check:** the Cycle Map worksheet holds the same table beside the exceptions the later tests find; {{ g.none_found|join(', ') }} show none. Its populations and matrix are formulas on the Tables loaded from CharlesRiver.xlsx, for example a matrix cell:

```jinja
{{ g.f_matrix }}
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Returns; lines; customers | {{ sr.n|count }}; {{ sr.lines|count }}; {{ sr.customers|count }} | 1 |
| Credits; refunds; clawbacks | {{ cm.n|count }}; {{ rf.n|count }}; {{ cb.n|count }} | 1 |
| Receipts; applications | {{ receipts|count }}; {{ apps|count }} | 1 |
| Orphans, unposted documents, gaps | none in M4 to M6 | 3 to 5 |
| Credits posting to both `1020` and `2060` | {{ g.both }} | 6 |

{{ expected() }}

## What a strong answer says

- **The map comes from the records:** every link tested both ways, every document traced to the ledger and back, the numbering tested, each result reported with its population, clean or not.
- **A clean result is bounded.** An anti-join finds a record that points at nothing, not the record never made; completeness rests on the numbering and on Requirement 2.
- **The limits are named by control point** and carried forward to the sample (Requirement 6) and the report (Requirement 9).
- **The duties are seen:** customer service records receipts, applies cash and approves credits and clawbacks.

A weak answer reports zero orphans without the test, takes the process from the narrative, or reads the ledger's creator as the preparer.

## Common mistakes and how to respond

- **Every credit without a refund.** *Symptom:* {{ g.no_refund|count }} orphans. *Response:* ask which credits should have a refund.
- **An anti-join with INNER JOIN.** *Symptom:* zero rows for every link. *Response:* ask what the test would show if a row were missing.
- **The ID alone.** *Symptom:* {{ g.id_rows|count }} ledger rows for the credits, or a query that will not finish. *Response:* ask which pair of columns identifies a document.
- **A gap test that restarts each year.** *Symptom:* false gaps in {{ g.restart }} series-years. *Response:* ask where the second year starts, and look at the clawback prefix.
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
