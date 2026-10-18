---
note: case4.r5
uses: [case4.g5]
title: Test the balances behind the report (Chapters 14 to 16; auditing)
kind: requirement
number: '5'
unit: case4
perspective: auditing
tool: powerbi
minutes: 150
solution: "PartIV-case.zip: Charles River Cash Case.pbip, page Reconciliations, the Findings table, Tests 4 and 5 of the Tests tab and the Requirement 5 rows of the Checks tab"
figures:
  - id: IF-C4-5-A
    kind: pbi-mock
    purpose: The Reconciliations page of the model answer, where each difference sits beside the findings that explain it.
    shows: "Report view, page Reconciliations, the upper part. A matrix of six working-capital accounts on rows and source document types on columns with the balance in each cell and a Total column, drawn in two panes because it is wider than the frame, the JournalEntry column outlined; below it a row of cards for receivables, open receivables, their difference, payables, open payables and their difference, the two differences outlined."
    data: The Expected results quantities (the balances by source and the two differences), read-only.
  - id: IF-C4-5-C
    kind: pbi-mock
    purpose: The lower part of the Reconciliations page, where the cutoff, the aging and the Findings table sit.
    shows: "Report view, page Reconciliations, the lower part. A table of billing by invoice date against the ledger by year with the difference; the aged open payables without the invoices moved to notes; and the Findings table with account, finding, amount and disposition, its rows in the order the table lists them."
    data: The Expected results quantities (the billing differences, the aged payables and the findings), read-only.
  - id: IF-C4-5-B
    kind: diagram
    purpose: The two reconciliations as one picture, so students see that each difference is a short list of recorded items.
    shows: "Two columns of stacked bars. Receivables: the ledger balance, then the open invoices with one segment for the opening line. Payables: the ledger balance, then the open invoices with two segments, the opening payables and the two note invoices, the second drawn below the axis. Each segment carries its disposition, Follow up or Expected."
    data: The Expected results quantities (the balances, open items and findings), read-only.
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = case4_g5 %}
# Requirement 5: Test the balances behind the report (Chapters 14 to 16; auditing)

{{ header() }}

## Purpose and learning outcomes

A report is only as good as the balances under it. The requirement breaks the working-capital balances down by source document, reconciles receivables and payables to their open items, tests the cutoff and the sales tax account, and records every difference as a finding that the report itself tests. The words matter: each finding states what the records show, never what anyone did. The analytics type is diagnostic, with the dispositions as the judgment.

Students can:

- break balances down by source document, trace the journal-entry parts and say that the breakdown tests nothing by itself (Step 1);
- reconcile receivables and payables to open items and explain each difference (Step 2);
- explain the billing differences with the cutoff findings of Chapters 6 and 12, and age the payables (Steps 3 and 4);
- test account `2050` and name the outside evidence (Step 5);
- record findings with dispositions and add tests that tie them to the differences (Step 6).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Reporting and Control (internal control); IFAC IES 2 (f), audit; AACSB A5 part 5.1.

## Before you assign

- **Files.** Requirements 1 to 4 done. The model answer is in PartIV-case.zip: the page, the Findings table and Tests 4 and 5.
- **From earlier work.** Exercise 16.1's open balance, Exercise 8.2's payables, Chapter 8's dispositions, Chapter 16's dispositions table and the cutoff findings of Chapters 6 and 12.
- **Data conditions.** The opening entry {{ entry }} carries balances no document in the extract supports; two supplier invoices were moved to notes payable while the subledger still shows them open; one supplier invoice crosses a year-end; account `2050` has no debit except credit memos.
- **Verify first.** The {{ g.n_checks }} Requirement 5 rows of the Checks tab agree.

## How to run it

Pairs, about 150 minutes: 25 for the roll-forward, 40 for the reconciliations, 25 for billing and aging, 20 for the sales tax, 30 for the findings and tests, 10 spare. Hold back the finding signs until a pair sees Test 4 fail. **Collect** the .pbix with the Findings table.

## Step-by-step solution

The Checks tab proves every value; the matrix layout is visible only in Desktop.

### Part 1: The roll-forward

**Step 1. Break the balances down by source.** Add a **Matrix** titled "{{ g.t_roll }}" with AccountNumber on **Rows** (the six accounts), SourceDocumentType on **Columns** and Balance in **Values**, filtered to the current year.

**Check:** the JournalEntry column holds the opening entry's lines, which no subledger document in the extract supports (receivables ${{ roll['1020'].parts.JournalEntry|money }}, materials ${{ roll['1045'].parts.JournalEntry|money }}, finished goods ${{ roll['1040'].parts.JournalEntry|money }}), and payables of {{ sm(roll['2010'].parts.JournalEntry) }}, the opening line less the two reclassifications to notes. The matrix only decomposes the ledger, and Step 2 and the Validation page carry the evidence.

### Part 2: Reconciliations

**Step 2. Reconcile to the open items.**

a. Build ARInvoices and APInvoices with the open balance, and relate them to Date. Use the fixed report date, {{ d.C }}-12-31. Leave out cash applications, credit memos and supplier payments dated later, group each by its invoice, merge the totals into the invoices and replace a missing total with zero, as the expression below does for receivables. Keep the sales invoices dated by the report date, reconcile their positive balances and examine the negative ones apart, and keep the supplier invoices received by it that are still open.
b. Add cards titled "{{ g.t_cards }}" with the ledger balance, the open items and their difference.

```m jinja
{{ g.ar_e }}
```

**Check:** {{ n_ar|count }} open invoices total ${{ open_ar|money }} against ${{ roll['1020'].total|money }} in the ledger, a difference of ${{ ar_diff|money }}, the opening line. The {{ n_neg|count }} negative balances ({{ sm(neg) }}) are credit memos on paid invoices, refunded except {{ waiting.n }} (${{ waiting.amount|money }}) still in account `2060` at the year-end. Payables: {{ n_ap|count }} invoices total ${{ ap_total|money }} against ${{ (roll['2010'].total|abs)|money }}, a difference of ${{ ap_diff|money }}: the opening payables, ${{ opening_ap|money }}, less ${{ notes_total|money }} on PI {% for c in capital %}{{ c.id }}{{ " and " if not loop.last else "" }}{% endfor %}. **Watch for:** two silent errors. A subtraction that lets a null through returns null: only {{ g.wrong_n }} open invoices (${{ g.wrong_sum|money }}) keep a balance, because almost every invoice has no credit memo ({{ g.no_credit|count }} of {{ g.rows|count }}). The Payables step of the bridge includes account `2020`, so reconciling it to the open invoices adds ${{ (-g.gr_ni)|money }} of goods received and not invoiced to the liability (a {{ sm(g.gr_ni) }} debit-minus-credit balance) and raises the difference to ${{ g.step_diff|money }}.

{{ figure('IF-C4-5-A') }}

### Part 3: Cutoff and aging

**Step 3. Compare billing with the invoices dated in each year.** Add a **Table** titled "{{ g.t_billing }}" with Year, billing by invoice date, billing in the ledger and the difference.

**Check:** the differences are{% for b in billing %} {{ b.year }} {{ sm(b.diff) }}{{ ";" if not loop.last else "." }}{% endfor %} Invoices dated in one year and posted on January 1 of the next explain them, and only {{ shipped }} shipped in {{ shipped_year }} (Chapter 6's cutoff error), so for the others the ledger is right and the dates are wrong.

**Step 4. Age the payables.** Add `Bucket` and `MovedToNotes` columns in APInvoices and a **Table** titled "{{ g.t_aging }}". The expression below, typed with the two invoice identifiers, is a manual finding to update in a later quarter.

```m jinja
{{ g.ap_moved }}
```

**Check:** ${{ past_due|money }} is past due with the two note invoices and ${{ past_due_x|money }} of ${{ total_x|money }} ({{ past_due_share|pct(1) }}) without them. **Watch for:** the invoice date in place of the received date. The ledger posts supplier invoices on their received date, which makes no difference at the current year-end but moves ${{ g.crossing.total|money }} ({{ g.crossing.number }}) at the end of {{ g.crossing.year }}.

{{ figure('IF-C4-5-C') }}

### Part 4: Sales tax

**Step 5. Test account `2050`.** Add a **Matrix** titled "{{ g.t_tax }}" with SourceDocumentType on **Rows**, Year on **Columns** and the credits and debits as **Values**.

**Check:** credits come only from SalesInvoice ({% for v in tax %}${{ v|money }}{{ ", " if not loop.last else "" }}{% endfor %} by ledger posting year, equal to the TaxAmount of the invoices posted in those years; by invoice date they differ by the cutoff invoices of Step 3) and debits only from CreditMemo; no payment or journal entry ever posts to it, leaving ${{ tax_balance|money }}. The records show no remittance; the sales tax returns filed, the tax authority's account, the bank statements and a bank reconciliation would show whether it was remitted.

### Part 5: Findings and tests

**Step 6. Record the findings and test them.**

a. Choose **Home > Enter data** and type the table below as `Findings`, with Account, Finding, Amount, Disposition and Reconciles.
b. Add the measures and Tests 4 and 5 in **DAX query view**.

| Account | Finding | Amount | Disposition | Reconciles |
|---|---|---:|---|---|
{% for r in g.findings %}
| {{ r[0] }} | {{ r[1] }} | {{ sm(r[2]|float) }} | {{ r[3] }} | {{ r[4] }} |
{% endfor %}

```dax jinja
{{ g.d_find }}
```

**Check:** both differences equal their findings to the cent, and in Test 5 the quarter-end measures and the average-balance measures of Requirement 3 show no value in the {{ g.later_quarters }} quarters after Data Through. The Part III payroll estimate (${{ g.accrual_parts.gross|money }} gross pay, ${{ g.accrual_parts.tax|money }} employer taxes and ${{ g.accrual_parts.benefits|money }} benefits, in accounts {{ g.accrual_parts.accounts|join(', ') }}) is a separate finding that reconciles neither difference. The dispositions follow Chapter 8: expected, follow up, or a misstatement to report. The opening inventories (${{ opening_inv|money }}) are recorded for follow-up with no difference to reconcile, so Test 4 leaves them out. **Watch for:** the note invoices entered as +${{ notes_total|money }}. The payables findings read ${{ g.wrong_find|money }} against ${{ g.right_find|money }}, and Test 4 shows {{ sm(-g.wrong_gap) }} unexplained.

{{ figure('IF-C4-5-B') }}

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax jinja
{{ g.dax_check }}
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Receivables difference; payables difference | ${{ ar_diff|money }}; ${{ ap_diff|money }} | 2 |
| Past due without the notes; share | ${{ past_due_x|money }}; {{ past_due_share|pct(1) }} | 4 |
| Sales tax payable; debits to it other than credit memos | ${{ tax_balance|money }}; none | 5 |
| Rows after Data Through; their amount | {{ after_rows|count }}; ${{ after_amount|money }} | 6 |

{{ expected() }}

## What a strong answer says

- **Breakdown.** The journal-entry parts are the opening balances and the reclassifications, and the matrix only decomposes the ledger, so the reconciliations carry the evidence.
- **Opening balances.** All four recorded for follow-up, with the evidence to request.
- **Reconciliations.** Each difference equals its recorded items to the cent, with a disposition in Chapter 8's terms.
- **Cutoff.** The billing differences are invoices posted a year later; only one shipped in the earlier year.
- **Sales tax.** Posted when billed, with no remittance recorded, with the outside evidence named; the wording is "no remittance is recorded", not "unpaid" or "withheld".

A strong submission ties the findings to Tests 4 and 5. A weak one lists the differences without recording them.

## Common mistakes and how to respond

- **A null in the open balance.** *Symptom:* ${{ g.wrong_sum|money }} of open receivables. *Response:* ask what a subtraction with a null returns.
- **Payables with `2020`.** *Symptom:* a difference of ${{ g.step_diff|money }}. *Response:* ask what account `2020` holds.
- **Sign of the notes finding.** *Symptom:* {{ sm(-g.wrong_gap) }} unexplained. *Response:* ask which way the invoices move the difference.
- **Notes left in the aging.** *Symptom:* ${{ past_due|money }} past due. *Response:* ask which invoices the ledger already moved.
- **Accusing wording.** *Symptom:* a finding that says someone failed to remit. *Response:* ask what the ledger shows and what it cannot.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Breakdown by source | 15 | Six accounts by source; journal-entry parts traced; read as a decomposition | Balances without the reading |
| Reconciliations | 30 | Both differences explained to the cent | One reconciled |
| Cutoff and aging | 20 | Billing differences explained; aging without notes | Differences without the cause |
| Sales tax | 15 | Posts and non-posts; outside evidence | Balance only |
| Findings and tests | 20 | Table with dispositions; Tests 4 and 5 agree | Findings without tests |

## Extensions and discussion questions

- Carry the Part III payroll estimate forward as an unposted proposal, and explain why it is a separate finding that reconciles neither receivables nor payables.
- Reconcile the same two accounts at the end of {{ d.P }} and explain why the differences move.
- Discuss: which of these findings would you tell the committee first, and in what words?
