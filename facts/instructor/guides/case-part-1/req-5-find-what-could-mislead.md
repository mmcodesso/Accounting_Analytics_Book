---
note: case1.r5
uses: [case1.g5]
title: Find what could mislead (Auditing)
kind: requirement
number: '5'
unit: case1
perspective: auditing
tool: conceptual
minutes: 45
solution: ''
figures:
  - id: IF-C1-5-A
    kind: excel-mock
    purpose: The PivotTable that shows what sits behind the naive fourth-quarter revenue.
    shows: A PivotTable on GLEntry with AccountID set to the Furniture revenue account and the quarter's three fiscal periods selected in the filters. Rows list SourceDocumentType, with VoucherNumber expanded under JournalEntry; Values show Sum of Debit and Sum of Credit. Two rows appear, JournalEntry (expanded to its voucher number) with a very large debit and SalesInvoice with a credit of about the quarter's invoicing. The grand total row shows debits far above credits, and a note gives credits less debits, which is negative. The JournalEntry row and its voucher number are outlined, and the grand total row is outlined in a second color.
    data: The GLEntry rows of the Furniture revenue account in the fourth quarter of the current fiscal year, by source document type (the Expected results of this requirement).
  - id: IF-C1-5-B
    kind: chart
    purpose: The naive and the corrected Furniture margin for the two quarters, side by side.
    shows: A clustered bar chart for the third and fourth quarters with two bars in each, "all ledger rows" and "year-end close excluded", and the percentage printed on each bar. The third quarter's bars match; in the fourth the all-rows bar is about the third quarter's and the corrected bar is lower, with a marker on the all-rows bar and a note that its totals are negative. The series differ by pattern (solid and hatched) as well as color.
    data: The naive and the corrected margins of the Expected results of this requirement.
---
{% set g = case1_g5 %}
# Requirement 5: Find what could mislead (Auditing)

{{ header() }}

## Purpose and learning outcomes

Requirement 5 is the case's audit moment. The data ties to the ledger, the quarters are right, and the margin can still be wrong, because the quarter ends on the day the books are closed. The lesson is not about one entry. It is the habit of reading the totals behind a percentage before believing it, and of tracing an odd total to its source document type and its entry type.

By the end, students can:

- compute a margin from all rows of two ledger accounts, and notice when the totals behind it make no sense;
- trace an odd total to a source document type, a voucher and an EntryType;
- explain why the entry does not belong in a quarterly measure, exclude it by a rule, and recompute the margins.

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance); IMA Data Literacy, and Internal Control within Reporting and Control; IFAC IES 4 (a), professional skepticism and professional judgment; AACSB A5 part 5.2. The analytics type is descriptive, applied with an auditor's skepticism.

## Before you assign

- Students need Requirement 4's PivotTable skills, Tutorial 2.2 (Step 6, the last fiscal year's rows by source document type), Tutorial 3.2 (the trace) and the controller's reminder in the case about the quarter's end.
- The requirement relies on these conditions: the third quarter has no journal entry on either Furniture account; the fourth has one close that debits revenue and credits cost by the year's balances; each fiscal year has two closes, only one of which touches the Furniture accounts; and the closes are the only journal entries on those accounts.
- Do not tell students what the entry is. They find it. If they ask for a hint, point them at the source document types in the fourth quarter.

## How to run it

Individual work, 45 minutes: 10 for the all-rows margin, 15 for finding the entry, 10 for the exclusion and the recompute and 10 for the statement. In Plan A it is debriefed live (see the case note); show the PivotTable of Step 2 on the projector and ask what a negative revenue means before anyone says what the entry is. **Collect** the all-rows table, the name and EntryType of the entry, and the corrected margins.

## Step-by-step solution

### Phase 1: The margin from all rows

**Step 1. Total the two accounts with no filter on source document type.** Build the GLEntry PivotTable of Requirement 4 for AccountID {{ revenue.id }} and then {{ cogs.id }}, for the three periods of each quarter, with Sum of Debit and Sum of Credit in **Values** and no filter on SourceDocumentType. Revenue is credits less debits; cost is debits less credits. The margin is:

```
=(Revenue - COGS) / Revenue
```

| Quarter | Revenue ({{ revenue.number }}) | Cost of goods sold ({{ cogs.number }}) | Margin |
|---|---:|---:|---:|
| {{ g.ql3 }} | ${{ g.rev3|money }} | ${{ g.cogs3|money }} | {{ naive_q3|pct(1) }} |
| {{ g.ql4 }} | -${{ (rev_all|abs)|money }} | -${{ (cogs_all|abs)|money }} | {{ naive_q4|pct(1) }} |

**Check:** the margin of {{ g.ql4 }} is {{ naive_vs_q3 }} the margin of {{ g.ql3 }}, so the ratio shows no decline. The totals behind it are negative in {{ g.ql4 }}: a revenue below zero is not a quarter's sales. **Watch for:** students who stop at the percentage, and who reverse the signs so that revenue reads positive and the trap disappears.

### Phase 2: Find the entry

**Step 2. Open up the fourth quarter.** In the revenue PivotTable for {{ g.ql4 }}, put SourceDocumentType in **Rows**. Two rows appear.

{{ figure('IF-C1-5-A') }}

| Source document type | Rows | Debit | Credit |
|---|---:|---:|---:|
{% for r in g.ledger.revenue4 %}
| {{ r.source }} | {{ r.rows|count }} | ${{ r.debit|money }} | ${{ r.credit|money }} |
{% endfor %}

**Check:** SalesInvoice holds the quarter's sales, and a single JournalEntry row holds a debit of ${{ close_debit|money }}, several times the quarter's invoicing. The cost account shows the same pattern, with a credit of ${{ close_credit|money }}.

**Step 3. Name the entry.** Add VoucherNumber under JournalEntry: the voucher is {{ close }}. Its two Furniture rows read:

{% for r in g.close_rows %}
- {{ r.number }}: {{ r.desc }}, debit ${{ r.debit|money }}, credit ${{ r.credit|money }}
{% endfor %}

Then open the JournalEntry worksheet and filter EntryNumber for {{ close }}.

**Check:** the EntryType is "{{ entry_type }}", posted on {{ posted }}, the last day of the fiscal year. **Watch for:** students who report the other close, which has a similar number and an EntryType that begins the same way. Its EntryType is the second of the year's two, and it posts to the income summary and retained earnings, not to a Furniture account.

### Phase 3: Explain it, exclude it, recompute

**Step 4. Explain why it does not belong.** A year-end close transfers the year's revenue and expense balances to an income summary so that the accounts start the next year at zero. It is not a sale or a cost. Here it debits {{ revenue.number }} by ${{ g.year_rev|money }}, which is the account's whole balance for fiscal {{ g.year }} before the close, and credits {{ cogs.number }} by ${{ g.year_cogs|money }}, the cost's whole balance. Both are a year's totals, not a quarter's, and they sit in the last quarter because the entry is dated on its last day. The close is a legitimate entry; it is the quarterly measure that must leave it out. The fiscal years of the extract each have two:

| Entry | Posted | EntryType |
|---|---|---|
{% for c in g.closes %}
| {{ c.number }} | {{ c.posted }} | {{ c.type }} |
{% endfor %}

**Step 5. Exclude it by a rule.** In the PivotTable, clear JournalEntry in the SourceDocumentType filter, or exclude the voucher {{ close }}. The principled rule is by entry type: leave out entries whose EntryType begins "Year-End Close". Here either gives the same rows, because the closes are the only journal entries on the two Furniture accounts. A ledger with adjusting entries would need the EntryType rule, and the model answer says so.

**Step 6. Recompute both margins.**

| Quarter | Revenue (invoices) | Cost (shipments less returns) | Margin |
|---|---:|---:|---:|
| {{ g.ql3 }} | ${{ g.rev3|money }} | ${{ g.cogs3|money }} | {{ m3|pct(2) }} |
| {{ g.ql4 }} | ${{ rev4|money }} | ${{ cogs4|money }} | {{ m4|pct(2) }} |

A cross-check from the sub-ledger at standard cost: add a helper column in SalesInvoiceLine (the first free column after Requirement 4's, {{ g.cols.new_col }}) with the line's cost, and total it as in Requirement 4.

```jinja
=SalesInvoiceLine!{{ g.cols.line_qty }}2*XLOOKUP({{ g.cols.line_item }}2, Item!{{ g.cols.item_id }}:{{ g.cols.item_id }}, Item!{{ g.cols.item_cost }}:{{ g.cols.item_cost }})
```

The margin at standard cost is {{ s3|pct(2) }} in {{ g.ql3 }} and {{ s4|pct(2) }} in {{ g.ql4 }}.

{{ figure('IF-C1-5-B') }}

**Step 7. State what the margins show.** On this measure the Furniture margin fell from {{ m3|pct(2) }} to {{ m4|pct(2) }}, a drop of {{ g.drop|num(2) }} points. Revenue fell {{ (-g.rev_change)|num(1) }}% from {{ g.ql3 }} to {{ g.ql4 }} while cost rose {{ g.cogs_change|num(1) }}%. The measure takes revenue before customer credits, which post to a shared account, and cost after the returned goods, so it overstates the margin, and a model answer says so. The cross-check at standard cost also falls, by {{ g.std_drop|num(2) }} points, but it is a separate measure (the invoice lines before returns), so it supports the direction of the change, not the level. That is the descriptive answer. Why it fell is the Part II question.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Naive revenue and cost, {{ g.ql4 }} | -${{ (rev_all|abs)|money }}; -${{ (cogs_all|abs)|money }} | Step 1 |
| Naive margin, {{ g.ql4 }}; {{ g.ql3 }} | {{ naive_q4|pct(1) }}; {{ naive_q3|pct(1) }} | Step 1 |
| The entry; its EntryType; its posting date | {{ close }}; {{ entry_type }}; {{ posted }} | Step 3 |
| Close: debit to {{ revenue.number }}; credit to {{ cogs.number }} | ${{ close_debit|money }}; ${{ close_credit|money }} | Step 3 |
| Corrected revenue and cost, {{ g.ql4 }} | ${{ rev4|money }}; ${{ cogs4|money }} | Step 6 |
| Corrected margin, {{ g.ql3 }}; {{ g.ql4 }} | {{ m3|pct(1) }}; {{ m4|pct(1) }} | Step 6 |
| Margin at standard cost, {{ g.ql3 }}; {{ g.ql4 }} | {{ s3|pct(1) }}; {{ s4|pct(1) }} | Step 6 |

{{ expected() }}

## What a strong answer says

- **The trap.** Using all rows gives a {{ g.ql4 }} margin of {{ naive_q4|pct(1) }}, {{ naive_vs_q3 }} the {{ g.ql3 }} figure, on negative totals; the percentage hides both the nonsense and the decline.
- **The entry.** {{ close }}, a journal entry of EntryType "{{ entry_type }}", posted on the last day of the year, debiting revenue and crediting cost by the year's balances.
- **The reason.** It is a bookkeeping transfer, not a transaction of the quarter, so it must be excluded from a quarterly margin; the exclusion rule is stated.
- **The result.** {{ m3|pct(1) }} to {{ m4|pct(1) }}, a fall on the stated basis (revenue before customer credits, cost after returned goods). The invoice-line view at standard cost falls too.

A weak answer reports the naive percentage as the result, removes one side of the close only, or drops the entry without saying why.

## Common mistakes and how to respond

- **Stopping at the ratio.** *Symptom:* "the margin rose slightly". *Response:* ask them to read the revenue and cost totals aloud.
- **Sign reversed.** *Symptom:* a {{ g.ql4 }} revenue of ${{ (rev_all|abs)|money }}, positive, because the signs were flipped. *Response:* ask which side of the ledger revenue sits on.
- **Only one side of the close removed.** *Symptom:* a margin far from either quarter. *Response:* ask whether the close posts to one account or two.
- **The wrong close.** *Symptom:* the second close of the year named. *Response:* ask which of the two posts to a Furniture account.
- **A blanket exclusion.** *Symptom:* "drop all journal entries". *Response:* ask what would happen to an accrual or an adjusting entry on the same account.
- **A fix of the ledger.** *Symptom:* "correct the entry". *Response:* the entry is right; the measure is what needs the exclusion.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| The all-rows margins and the totals behind them | 25 | Both percentages, the negative totals and a comment on them | Percentages only |
| The entry and its EntryType | 25 | The voucher, the source document type, the EntryType and the date | The entry without its EntryType |
| Why it is excluded | 20 | A bookkeeping transfer of the year's balances, not an operating transaction; a stated rule | "It is too large" |
| The corrected margins and what they show | 30 | Both margins, the decline in points and the descriptive statement | Margins without the statement, or an error of one side |

## Extensions and discussion questions

- Net the revenue side of returns. The Furniture credit memo lines were ${{ g.ret3|money }} in {{ g.ql3 }} and ${{ g.ret4|money }} in {{ g.ql4 }}. The margin is then {{ g.net3|pct(2) }} and {{ g.net4|pct(2) }}. Does the fall survive?
- Add the Furniture shipment lines of {{ g.ql4 }} with no invoice line to revenue at their order price (${{ g.unbilled.at_order_price|money }}). The margin of {{ g.ql4 }} would be {{ g.billed4|pct(2) }}, still below {{ g.ql3 }}. What does that say about the cutoff?
- Discuss: which test of Chapter 2's checklist, if any, would have flagged this before the margin was computed?
