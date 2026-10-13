# Requirement 3: Rebuild Accrued Expenses at each year-end (Chapters 3, 10, and 12)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 3 |
| Perspective | Auditing |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 150 minutes |
| Solution file | Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 3 and the view OpenAccruals; Chapter17-capstone-excel.zip: worksheet Accrued Expenses, the same rebuild in formulas, as a cross-check |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Account `2040` has grown every year, and its recorded balance says nothing about what it holds. Students rebuild it from the postings that reach it, prove the parts add up to the ledger at three dates, and decide which old accruals are still owed. The habit it teaches: measure what cleared an accrual from the ledger's postings, never from a document's total. The analytics type is diagnostic, with a small prescriptive step in the decision.

Students can:

- split the balance into its parts and reconcile them to the ledger at each year-end (Parts 1 and 4);
- subtract from each accrual what cleared it by each date (Part 2);
- measure the clearing lag and age the open accruals against the longest wait (Part 3);
- decide which old accruals to treat as owed, stating the assumption and the evidence that would confirm it (Part 5).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 and Core S2 M9 (audit procedures, analytical procedures, and audit data analytics); IMA Reporting and Control (financial recordkeeping; financial statement preparation); IFAC IES 2 (a); AACSB A5 part 5.1 (technology integration: SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite with `LenderPackage.sql` open in DB Browser for SQLite. The Excel sheet Accrued Expenses is a cross-check.
- **Data conditions.** Each Accrual entry credits `2040` and debits one expense account. PurchaseInvoiceLine.AccrualJournalEntryID names the accrual on 355 lines, never two lines for one accrual, and JournalEntry.ReversesJournalEntryID names the accrual that each of 149 Accrual Adjustment entries clears. Shipments credit `2040` for freight and a monthly settlement pays the carriers. The opening entry has a `2040` line with no document.
- **Verify first.** The reconciliation's Difference column is zero at all three dates.

## How to run it

Pairs, about 150 minutes: 20 for the populations, 40 for the clearing and the view, 15 for the lag, 30 for the parts, 35 for the aging and the decision, 10 to write the assumption. The routine for every query: type it at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the view until students have tried to subtract invoice totals. **Collect** the script and the written assumption.

> **[Figure placeholder IF-17-3-A]** The reconciliation of account 2040 to the ledger at the three year-ends, the result every student must reach before deciding anything.
> Kind: sql-mock · Shows: The tab LenderPackage.sql at the reconciliation query. Three rows, one for each year-end, with the columns AsOfDate, Opening, FreightNotSettled, DecemberFreight, YoungAccruals, OldAccruals, Parts, Ledger and Difference. The Difference cells are outlined; the message pane reports three rows. · Data: The reconciliation query, run read-only after the view OpenAccruals is created. · Status: planned

## Step-by-step solution

### Part 1: What reaches the account

**Step 1. Profile the populations.** One query counts the Accrual entries and their credits, the invoice lines that refer to an accrual and the debits they post to `2040`, the lines with no reference, and the adjustment entries.

**Check:** 396 accruals of $4,052,446.62; 355 lines clearing $3,646,702.22; 40,293 lines with no reference; 149 adjustments on 149 accruals, $54,615.91. **Watch for:** a join from the accruals to the ledger on the document ID alone. It returns 792 rows and $4,115,186.54 instead of 396 and $4,052,446.62, because the freight postings of shipments share the numbers. Join on the document type and the ID together.

### Part 2: What had cleared each accrual

**Step 2. Subtract what cleared each accrual by each date, and save the result as a view.** The Clearing CTE unions the two sources, the invoice debits to `2040` for the lines that refer to the accrual and the Accrual Adjustment debits that reverse it. The view OpenAccruals then lists each accrual still open at each year-end with its age and an IsOld flag.

```sql
Clearing AS (
    SELECT pil.AccrualJournalEntryID AS JournalEntryID,
        gl.PostingDate, gl.Debit AS Amount, 'Invoice' AS Kind
    FROM PurchaseInvoiceLine AS pil
        INNER JOIN GLEntry AS gl
            ON gl.SourceDocumentType = 'PurchaseInvoice'
            AND gl.SourceDocumentID = pil.PurchaseInvoiceID
            AND gl.SourceLineID = pil.PILineID
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE pil.AccrualJournalEntryID IS NOT NULL
        AND a.AccountNumber = 2040
    UNION ALL
    SELECT je.ReversesJournalEntryID, je.PostingDate, gl.Debit,
        'Adjustment'
    FROM JournalEntry AS je
        INNER JOIN GLEntry AS gl
            ON gl.SourceDocumentType = 'JournalEntry'
            AND gl.SourceDocumentID = je.JournalEntryID
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE je.EntryType = 'Accrual Adjustment'
        AND a.AccountNumber = 2040
),
```

**Check:** the excess of invoices over their accruals went to expense, $24,489.89, $26,702.96 and $34,364.32, and does not reduce the accrual. **Watch for:** clearing by the invoice line's total. Overbilled accruals go negative and net against the others, so the open amount is short by $24,489.89, $51,192.85 and $85,557.17 at the three year-ends.

### Part 3: The lag and the age

**Step 3. Measure how long invoices took, and age the open accruals.** The lag is the days from an accrual to its first invoice posting; a ranking CTE gives the shortest, median and longest. IsOld compares an open accrual's age with the longest lag.

**Check:** the lag runs from 15 to 62 days, median 39, and four accruals cleared at exactly 62, so the rule is older than 62 days. Old items at the three year-ends: 7, 15 and 22, worth $39,028.43, $96,049.58 and $157,346.79. **Watch for:**

- A round rule of older than 30 days flags 30 items worth $233,714.42 at the last year-end, more than materiality by itself.
- A rule of older than the last two month-ends flags JE-2025-000188, 61 days old at the end of 2025, though ASV0050-2025-040073 cleared it on 2026-01-01.

### Part 4: The parts and the reconciliation

**Step 4. Split `2040` and reconcile.** The opening line, the shipment credits less the settlements, and the open accruals by age, beside the ledger. Only the closing SELECT is shown; its CTEs sum the opening entry, the freight and the ledger.

```sql
SELECT pa.AsOfDate, ROUND(pa.Opening, 2) AS Opening,
    ROUND(pa.Freight, 2) AS FreightNotSettled,
    ROUND(pa.DecemberFreight, 2) AS DecemberFreight,
    ROUND(SUM(CASE WHEN oa.IsOld = 0 THEN oa.OpenAmount ELSE 0 END), 2)
        AS YoungAccruals,
    ROUND(SUM(CASE WHEN oa.IsOld = 1 THEN oa.OpenAmount ELSE 0 END), 2)
        AS OldAccruals,
    ROUND(pa.Opening + pa.Freight + SUM(oa.OpenAmount), 2) AS Parts,
    ROUND(pa.Ledger, 2) AS Ledger,
    ROUND(pa.Opening + pa.Freight + SUM(oa.OpenAmount)
        - pa.Ledger, 2) AS Difference
FROM Parts AS pa
    INNER JOIN OpenAccruals AS oa ON oa.AsOfDate = pa.AsOfDate
GROUP BY pa.AsOfDate, pa.Opening, pa.Freight, pa.DecemberFreight,
    pa.Ledger
ORDER BY pa.AsOfDate
```

**Check:** the difference is zero at each year-end, and the total is $325,172.77, $396,988.71 and $480,552.36. **Watch for:** taking only December's freight, which leaves a difference at each date, $3,416.20, $5,725.82 and $3,719.65, the estimates above the settlements. And counting the opening line among the old items, which makes them $242,346.79 at the last year-end.

### Part 5: The decision

**Step 5. Decide which old accruals are still owed.** Age shows that an accrual has gone unbilled, not that nothing is owed. The model answer reverses them at each year-end (A3) on the stated assumption that they will never be billed, and names the evidence that would confirm it: the suppliers' statements or confirmations, the service contracts, any later invoice or settlement, and the support for the original estimate.

**Check:** 22 old items at the last year-end, none ever invoiced, 3 of them partly cleaned up by adjustments (JE-2024-000264, JE-2025-000286, JE-2026-000295). Reversing at each year-end moves $39,028.43 into opening retained earnings and $57,021.15 and $61,297.21 into the income of 2025 and 2026. **Watch for:** reversing only at the last year-end, which puts $157,346.79 into that year's income. A retained-liability answer, which keeps them until the evidence is in hand, is equally acceptable if it states its assumption.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Accruals; their amount | 396; $4,052,446.62 | 1 |
| Lag: shortest, median, longest | 15; 39; 62 days | 3 |
| Old items at each year-end | 7; 15; 22 | 3 |
| Account `2040`, rebuilt | $325,172.77; $396,988.71; $480,552.36 | 4 |
| A3 on opening retained earnings; 2025 income; 2026 income | $39,028.43; $57,021.15; $61,297.21 | 5 |

> **Instructor notes, Requirement 3:** populations: 396 Accrual entries, 4,052,446.62, each crediting 2040 and debiting one expense account (6100-6220); 355 invoice lines refer to them, at most one per accrual, all on the ASV service invoices with no purchase order, and clear 3,646,702.22 through their 2040 debits; AccrualJournalEntryID is NULL on the other 40,293 invoice lines; 149 Accrual Adjustment entries, 149 distinct targets, 54,615.91. The excess of invoices over their accruals went to expense: 24,489.89 / 26,702.96 / 34,364.32 (60 / 65 / 84 lines). Clearing lag (accrual date to invoice posting): 15 to 62 days, median 39; four cleared at exactly 62 days, so "older than 62 days" is the rule; a rule of "older than the last two month-ends" would wrongly flag JE-2025-000188, 61 days old at the end of 2025 and cleared on 2026-01-01 by ASV0050-2025-040073. Composition of 2040 at 2024 / 2025 / 2026 year-ends: opening line 85,000.00 (no document); freight not yet settled 48,797.21 / 47,290.49 / 44,423.87 (December's freight 45,381.01 / 41,564.67 / 40,704.22 plus estimates above settlements 3,416.20 / 5,725.82 / 3,719.65; settlements post on the first weekday of the next month, so December 2026's falls outside the data; shipment credits to 2040 equal the 5050 debits, 1,477,398.06; 35 settlements, 1,432,974.19); open accruals 62 days old or less 152,347.13 / 168,648.64 / 193,781.70; open accruals more than 62 days old 39,028.43 (7) / 96,049.58 (15) / 157,346.79 (22); total 325,172.77 / 396,988.71 / 480,552.36, equal to the ledger. The 22 old items at 2026 were never invoiced; 3 were partly cleared by "Partial cleanup" adjustments with no invoice (JE-2024-000264, JE-2025-000286, JE-2026-000295). By year recorded 2024 68,844.44 (11), 2025 32,795.49 (5), 2026 55,706.86 (6); by expense account 6110 22,616.85, 6120 26,261.26, 6140 5,572.08, 6160 17,895.82, 6180 9,569.93, 6190 10,368.12, 6200 15,120.25, 6210 25,601.55, 6220 24,340.93. Of the young items open at the end of 2024, 32,929.99 was never invoiced (JE-2024-000188, -000206, -000210, -000214); of those at the end of 2025, 5,590.35 (JE-2025-000202, 10,198.72 open, partly cleaned up in 2026). Model answer (A3), on an assumption the records cannot prove: that the old items will never be billed and nothing is owed. Their age and the missing invoice show that an accrual has gone unbilled past the longest clearing lag, not that the service was never received or that the supplier released the company; the evidence that would settle it is the suppliers' statements or confirmations, the service contracts, any later invoice or settlement, and the support for the original estimate. Under that assumption an accrual past the invoicing window at a year-end is treated as an error at that year-end (retained earnings at 1 January 2025 +39,028.43; 2025 expense -57,021.15; 2026 expense -61,297.21); an accrual within the window is an estimate, and one that later proves unneeded is a change in estimate in the year it goes stale. Accept equally a retained-liability answer that keeps the old items until that evidence is in hand: accrued expenses are then 396,988.71 and 480,552.36, and income before income taxes is 57,021.15 lower in 2025 and 61,297.21 lower in 2026 than in the model answer, with retained earnings at 1 January 2025 39,028.43 lower (Requirement 6 gives the statements); what matters is that the decision states its assumption and its evidence. Allocating by year of origin (68,844.44 / 32,795.49 / 55,706.86) is acceptable if argued, but it uses hindsight on the November and December items of 2024 and 2025 that it cannot apply to 2026. Keep the 193,781.70 of young 2026 accruals, and leave the 85,000.00 to Requirement 9.

## What a strong answer says

- **The rebuild.** Opening line, freight not yet settled and open accruals, reconciled to the ledger at each date, with clearing measured from the postings.
- **The window.** The longest observed wait, and the item that a shorter rule would wrongly flag.
- **The decision.** A stated assumption, the evidence that would settle it, and the effect of the other choice; the opening line left to the memo.

A weak answer calls the old accruals "stale" and reverses them without evidence.

## Common mistakes and how to respond

- **Invoice totals as clearing.** *Symptom:* open amounts short by $85,557.17. *Response:* ask what the ledger debited for an invoice larger than its accrual.
- **An ID-only join.** *Symptom:* 792 accrual rows. *Response:* ask what else carries the same document number.
- **A round aging rule.** *Symptom:* $233,714.42 of old items. *Response:* ask what the longest observed wait was.
- **One year-end only.** *Symptom:* $157,346.79 in one year's income. *Response:* ask what the same accruals were a year earlier.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Populations and joins | 15 | Counts correct; joins on type and ID | Join on the ID alone |
| Clearing and the view | 25 | Invoice debits and adjustments by date | Invoice totals used |
| Lag and aging | 20 | Longest wait observed; old items at each year-end | A round rule |
| Reconciliation | 25 | Parts equal the ledger at all three dates | One date, or a difference left |
| Decision | 15 | Assumption and evidence stated; effect by year | Reversal with no evidence |

## Extensions and discussion questions

- Compute the lag by expense account and say whether one account's accruals take longer to invoice.
- Measure the lag from the last invoice posting instead of the first and say which accruals move.
- Discuss: when does an accrual that was never invoiced become income, and who decides?
- Discuss: why does the case keep the opening line out of the estimate?
