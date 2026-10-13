---
note: ch17.r3
uses: [ch17.g3]
title: Rebuild Accrued Expenses at each year-end (Chapters 3, 10, and 12)
kind: requirement
number: '3'
unit: '17'
perspective: auditing
tool: sql
minutes: 150
solution: "Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 3 and the view OpenAccruals; Chapter17-capstone-excel.zip: worksheet Accrued Expenses, the same rebuild in formulas, as a cross-check"
figures:
  - id: IF-17-3-A
    kind: sql-mock
    purpose: The reconciliation of account 2040 to the ledger at the three year-ends, the result every student must reach before deciding anything.
    shows: "The tab LenderPackage.sql at the reconciliation query. Three rows, one for each year-end, with the columns AsOfDate, Opening, FreightNotSettled, DecemberFreight, YoungAccruals, OldAccruals, Parts, Ledger and Difference. The Difference cells are outlined; the message pane reports three rows."
    data: The reconciliation query, run read-only after the view OpenAccruals is created.
---
{% set g = ch17_g3 %}
# Requirement 3: Rebuild Accrued Expenses at each year-end (Chapters 3, 10, and 12)

{{ header() }}

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
- **Data conditions.** Each Accrual entry credits `2040` and debits one expense account. PurchaseInvoiceLine.AccrualJournalEntryID names the accrual on {{ n_lines|count }} lines, never two lines for one accrual, and JournalEntry.ReversesJournalEntryID names the accrual that each of {{ n_adj }} Accrual Adjustment entries clears. Shipments credit `2040` for freight and a monthly settlement pays the carriers. The opening entry has a `2040` line with no document.
- **Verify first.** The reconciliation's Difference column is zero at all three dates.

## How to run it

Pairs, about 150 minutes: 20 for the populations, 40 for the clearing and the view, 15 for the lag, 30 for the parts, 35 for the aging and the decision, 10 to write the assumption. The routine for every query: type it at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the view until students have tried to subtract invoice totals. **Collect** the script and the written assumption.

{{ figure('IF-17-3-A') }}

## Step-by-step solution

### Part 1: What reaches the account

**Step 1. Profile the populations.** One query counts the Accrual entries and their credits, the invoice lines that refer to an accrual and the debits they post to `2040`, the lines with no reference, and the adjustment entries.

**Check:** {{ n }} accruals of ${{ amount|money }}; {{ n_lines|count }} lines clearing ${{ cleared|money }}; {{ null_lines|count }} lines with no reference; {{ n_adj }} adjustments on {{ targets }} accruals, ${{ adj_amount|money }}. **Watch for:** a join from the accruals to the ledger on the document ID alone. It returns {{ g.ids_rows }} rows and ${{ g.ids_amount|money }} instead of {{ g.typed_rows }} and ${{ g.typed_amount|money }}, because the freight postings of shipments share the numbers. Join on the document type and the ID together.

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

**Check:** the excess of invoices over their accruals went to expense, ${{ excess[0]|money }}, ${{ excess[1]|money }} and ${{ excess[2]|money }}, and does not reduce the accrual. **Watch for:** clearing by the invoice line's total. Overbilled accruals go negative and net against the others, so the open amount is short by ${{ g.netted[0]|abs|money }}, ${{ g.netted[1]|abs|money }} and ${{ g.netted[2]|abs|money }} at the three year-ends.

### Part 3: The lag and the age

**Step 3. Measure how long invoices took, and age the open accruals.** The lag is the days from an accrual to its first invoice posting; a ranking CTE gives the shortest, median and longest. IsOld compares an open accrual's age with the longest lag.

**Check:** the lag runs from {{ lag_low }} to {{ lag_high }} days, median {{ median }}, and {{ at_window }} accruals cleared at exactly {{ window }}, so the rule is older than {{ window }} days. Old items at the three year-ends: {{ g.comps[0].n_old }}, {{ g.comps[1].n_old }} and {{ g.comps[2].n_old }}, worth ${{ g.comps[0].old|money }}, ${{ g.comps[1].old|money }} and ${{ g.comps[2].old|money }}. **Watch for:**

- A round rule of older than 30 days flags {{ g.t30[2][1] }} items worth ${{ g.t30[2][0]|money }} at the last year-end, more than materiality by itself.
- A rule of older than the last two month-ends flags {{ wrong[0].number }}, {{ wrong[0].age }} days old at the end of {{ wrong[0].year }}, though {{ wrong[0].invoice }} cleared it on {{ wrong[0].cleared }}.

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

**Check:** the difference is zero at each year-end, and the total is ${{ comp[0].total|money }}, ${{ comp[1].total|money }} and ${{ comp[2].total|money }}. **Watch for:** taking only December's freight, which leaves a difference at each date, ${{ comp[0].excess|money }}, ${{ comp[1].excess|money }} and ${{ comp[2].excess|money }}, the estimates above the settlements. And counting the opening line among the old items, which makes them ${{ g.with_opening|money }} at the last year-end.

### Part 5: The decision

**Step 5. Decide which old accruals are still owed.** Age shows that an accrual has gone unbilled, not that nothing is owed. The model answer reverses them at each year-end (A3) on the stated assumption that they will never be billed, and names the evidence that would confirm it: the suppliers' statements or confirmations, the service contracts, any later invoice or settlement, and the support for the original estimate.

**Check:** {{ n_old }} old items at the last year-end, none ever invoiced, {{ cleanups|count }} of them partly cleaned up by adjustments ({{ cleanup_entries|join(', ') }}). Reversing at each year-end moves ${{ a3.re|money }} into opening retained earnings and ${{ a3.P|money }} and ${{ a3.C|money }} into the income of {{ d.P }} and {{ d.C }}. **Watch for:** reversing only at the last year-end, which puts ${{ g.only_last|money }} into that year's income. A retained-liability answer, which keeps them until the evidence is in hand, is equally acceptable if it states its assumption.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Accruals; their amount | {{ n }}; ${{ amount|money }} | 1 |
| Lag: shortest, median, longest | {{ lag_low }}; {{ median }}; {{ lag_high }} days | 3 |
| Old items at each year-end | {{ g.comps[0].n_old }}; {{ g.comps[1].n_old }}; {{ g.comps[2].n_old }} | 3 |
| Account `2040`, rebuilt | ${{ comp[0].total|money }}; ${{ comp[1].total|money }}; ${{ comp[2].total|money }} | 4 |
| A3 on opening retained earnings; {{ d.P }} income; {{ d.C }} income | ${{ a3.re|money }}; ${{ a3.P|money }}; ${{ a3.C|money }} | 5 |

{{ expected() }}

## What a strong answer says

- **The rebuild.** Opening line, freight not yet settled and open accruals, reconciled to the ledger at each date, with clearing measured from the postings.
- **The window.** The longest observed wait, and the item that a shorter rule would wrongly flag.
- **The decision.** A stated assumption, the evidence that would settle it, and the effect of the other choice; the opening line left to the memo.

A weak answer calls the old accruals "stale" and reverses them without evidence.

## Common mistakes and how to respond

- **Invoice totals as clearing.** *Symptom:* open amounts short by ${{ g.netted[2]|abs|money }}. *Response:* ask what the ledger debited for an invoice larger than its accrual.
- **An ID-only join.** *Symptom:* {{ g.ids_rows }} accrual rows. *Response:* ask what else carries the same document number.
- **A round aging rule.** *Symptom:* ${{ g.t30[2][0]|money }} of old items. *Response:* ask what the longest observed wait was.
- **One year-end only.** *Symptom:* ${{ g.only_last|money }} in one year's income. *Response:* ask what the same accruals were a year earlier.

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
