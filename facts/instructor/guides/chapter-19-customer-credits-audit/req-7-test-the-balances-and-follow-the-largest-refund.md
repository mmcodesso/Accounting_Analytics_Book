---
note: ch19.r7
uses: [ch19.g7]
title: Test the balances, and follow the largest refund (Chapters 8 and 12)
kind: requirement
number: '7'
unit: '19'
perspective: auditing
tool: mixed
minutes: 150
solution: "Chapter19-capstone-sql.zip: Credits.sql, the queries headed Requirement 7 (tests S1 to S6); Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Timeline (the largest refund live, the timeline, the restocking by reason, the results and the disposition)"
figures:
  - id: IF-19-7-A
    kind: diagram
    purpose: The picture behind the disposition.
    shows: "A time line from the shipment to the settling of the invoice, one lane for each department, with the shipment, invoice, receipts, return, credit, clawbacks and refund at their dates, and the unpaid balance marked on the credit date and on the refund date."
    data: Test S6 of Credits.sql for the largest refund.
---
{% set g = ch19_g7 %}
# Requirement 7: Test the balances, and follow the largest refund (Chapters 8 and 12)

{{ header() }}

## Purpose and learning outcomes

Requirement 4 tested the controls; this one tests the amounts. A substantive test asks whether a balance is right, and sharing a population with a control test does not make its result evidence for the other. Students recompute every credit from its sources, value the restocked goods, test for lapping, and follow the largest refund. The analytics type is diagnostic. SQL fits the recomputation and lapping tests; Excel fits the timeline the committee reads.

Students can recompute a document from its sources (Part 1), value restocked goods (Part 2), test lapping and explain a first-digit test's limits (Part 3), and build a timeline worded as what the records show (Part 4).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Reporting and Control (internal control); IFAC IES 2 (f) and IES 4 (a); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite and Credits.sql. Before this requirement, load the Refunds, Credits and ReturnLines Tables with the case note's build contract, or open the model workbook: Requirement 4's SQL output alone does not create these Excel Tables.
- **Data conditions.** Stored LineTotal values are rounded, so a tolerance is a decision. Credits with freight carry tax on the freight. Receipts can arrive before their invoice.
- **Verify first.** Run S1 to S6: each returns at once, S1 and S5 one row, S3 {{ g.n_open }} rows, S6 {{ g.n_steps }}.

## How to run it

Pairs, about 150 minutes: 25 for S1, 20 for S2, 10 for S3, 20 for S4, 25 for S5 and the first-digit reasoning, 35 for S6 and the Timeline sheet, 15 for the disposition. Hold back the disposition until the timeline is complete. **Collect** Credits.sql and the Timeline sheet.

## Step-by-step solution

### Part 1: Recompute each credit line and credit (S1 to S3)

**Step 1. Trace and recompute every credit line (S1).** One row of counts joins each line to its return, shipment and invoice line.

```sql
SUM(CASE WHEN ABS(LineTotal
        - ROUND(Quantity * UnitPrice * (1 - Discount), 2)) > 0.004
        THEN 1 ELSE 0 END) AS LineTotalOff,
```

**Check:** {{ g.lines }} of {{ g.lines }} lines traced, none above the quantity shipped or returned, none returned twice, none off the invoice's price or discount, and {{ half|length }} stored total one cent off SQLite's rounded result at an exact half-cent tie ({% for h in half_info %}credit line {{ h.id }}: exact product {{ h.exact }}, stored {{ h.stored }}, ROUND {{ h.sqlite }}{{ '; ' if not loop.last }}{% endfor %}); rounded half up, credit lines {{ half_up|join(', ') }} differ instead. State the rounding convention and document the differences, none an error. **Watch for:** the stored total compared with the unrounded product at a tolerance below half a cent, which flags {{ g.unrounded }} lines.

**Step 2. Recompute every credit against its original invoice (S2).** Join each credit to its original invoice and first corroborate that the invoice's tax is {{ sub.inv_rate|pct(1) }} of its SubTotal plus freight, rounded to cents, reporting any invoice that does not agree. Then test the credit's tax at that rate on the credit's subtotal plus freight credited.

```sql
SUM(CASE WHEN ABS(InvoiceTax - ROUND((InvoiceSubTotal + InvoiceFreight)
        * (SELECT TaxRate FROM Rate), 2)) > 0.005 THEN 1 ELSE 0 END)
        AS InvoiceTaxOff,
```

**Check:** {{ n_cm }} credits on as many invoices; InvoiceTaxOff is zero (a changed invoice tax would show there) and tax at {{ rate|pct(1) }} holds on every credit; none above its invoice, each subtotal equal to its lines, no freight credit above the invoice's. The credits' own effective rate is only a diagnostic, and the rate and taxability need the approved policy before a conclusion on legal correctness. The freight test is an upper bound, so the answer asks for the freight policy. **Watch for:** tax tested on the subtotal alone, which flags {{ g.tax_alone }} credits, exactly those with freight.

**Step 3. List the open items in 2060 (S3).** The credits whose part posted to 2060 is not refunded by the last year-end.

**Check:** {{ g.n_open }} credits, {{ g.open_text }}, adding up to the account's balance at the year-end.

### Part 2: Measure the restocking by reason (S4)

**Step 4. Group the return lines by reason and year (S4, complete in Credits.sql).** The query adds each line's recorded cost and compares it with quantity times the item's standard cost.

**Check:** goods returned Damaged went back at ${{ dmg_total|money }} over the three years, and with Quality Concern ${{ both_c|money }} in the last year; no account writes them down. These are gross flows, not the inventory still held: a valuation follow-up. **Watch for:** {{ n_frac }} complete returns of shipment lines below one unit are recorded at the quantity times the shipment line's already extended cost, ${{ frac_gap|money }} below quantity times the item's unit standard cost, including ${{ frac_dq|money }} for Damaged or Quality Concern goods. Reconcile the recorded amounts, list the differences apart and obtain the costing policy. The pattern explains how the records were produced, not that the valuation is correct.

### Part 3: Test for lapping, and explain the first-digit test (S5)

**Step 5. Test receipts against invoices, deposits and applications (S5, complete in Credits.sql).** One row of subqueries, the first of which compares the customer on the receipt with the customer on the invoice.

**Check:** no application to another customer's invoice, short delays, every receipt fully applied. {{ g.early_r }} receipts (${{ g.early_amt|money }}) were applied to invoices dated after them: deposits held in 2060, not lapping, as far as these tests reach. **Watch for:** either delay shown alone. The raw delay, up to {{ g.lag_receipt|num(0) }} days on {{ g.lag_receipt_n }} applications, is the observation, and receipts dated before their invoice explain it.

**Step 6. Explain why a first-digit test is not established as suitable for these populations.** Use Chapter 8's criteria for populations that suit the test: the credits and refunds are event-selected reversals of invoice amounts, so their amounts follow the invoice lines they reverse and a conformity test has no basis here.

**Check:** the suitability argument and its limits earn the credit; the chance-MAD comparison in the note is an untaught, optional extension. **Watch for:** the result read as assurance or as a finding.

### Part 4: Follow the largest refund (S6 and the Timeline sheet)

**Step 7. Build the steps in date order (S6, complete in Credits.sql).** The query stacks one step for each document with its date, a step order and who did it, and sorts by date, step order and document. Joined from the invoice's lines, the shipment would repeat; DISTINCT stops that.

**Check:** {{ g.n_steps }} rows: the shipment, the invoice, {{ g.n_apps }} receipts, the return, the credit, the clawbacks and the refund. **Watch for:** DISTINCT missing, because invoice {{ g.big_inv }} has {{ g.inv_lines }} lines on {{ g.ships }} shipment, and a sort on the date alone, which leaves the credit and its clawbacks, dated the same day, in no fixed order.

**Step 8. Lay out the timeline and the disposition in Excel.**

a. On the Timeline sheet, build the live block that finds the largest refund and its facts; its first formulas are below (B4, B5 and B7, with the refund date in B6).
b. Paste S6's rows with **Copy with Headers** below it, with a note naming the query, and type the last step, the invoice settled.
c. Write the disposition and the evidence outside the database.

```jinja
{{ g.f_max }}
{{ g.f_who }}
{{ g.f_dow }}
```

{{ figure('IF-19-7-A') }}

**Check:** {{ g.big }}, ${{ g.big_amount|money }}, the largest refund, of the largest credit; ${{ g.unpaid|money }} of the invoice was unpaid on the refund date. The disposition is follow up, not a conclusion, with the evidence the note lists. **Watch for:** the Sunday read as evidence. Weekend dates hold {{ g.weekend }} of the {{ g.refunds }} refunds, about the share of the week they are.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Lines traced; one-cent differences from SQLite at a half-cent tie | {{ g.lines }} of {{ g.lines }}; {{ half|length }} | 1 |
| Credits recomputed; tax rate; credits with freight | {{ n_cm }}; {{ rate|pct(1) }}; {{ g.with_freight }} | 2 |
| Damaged restocked; Damaged and Quality Concern, last year | ${{ dmg_total|money }}; ${{ both_c|money }} | 4 |
| Receipts applied before their invoice; amount | {{ g.early_r }}; ${{ g.early_amt|money }} | 5 |
| Largest refund; unpaid on its invoice | ${{ g.big_amount|money }}; ${{ g.unpaid|money }} | 8 |

{{ expected() }}

## What a strong answer says

- **Each recomputation states its tolerance and names the rounding,** and finds no error.
- **Restocking is a flow at standard cost with no write-down,** a valuation follow-up with the lines below proportionate cost listed apart.
- **The lapping tests are stated, and the deposits are explained.**
- **The first-digit test is reasoned about with Chapter 8's criteria,** not run and believed.
- **The timeline gives each step a date, a document and a role,** and the disposition is follow up with the evidence that would settle it.

A weak answer reports the rounding as errors, reads the deposits as lapping, or words the timeline as an accusation.

## Common mistakes and how to respond

- **The unrounded product.** *Symptom:* {{ g.unrounded }} lines "wrong". *Response:* ask what the stored total is rounded to.
- **Tax on the subtotal alone.** *Symptom:* {{ g.tax_alone }} credits flagged. *Response:* ask what they have in common.
- **Restocking errors or rounding.** *Symptom:* {{ n_frac }} lines called errors, or rounding. *Response:* ask which field is a unit cost and which an extended cost. A complete return of {{ frac_example.qty|num(2) }} units at {{ frac_example.unit }} a unit would reverse {{ frac_example.proportionate }} under proportionate costing, and {{ frac_example.recorded }} needs an explanation. Do not change the data or dismiss the gap.
- **Delay from the receipt.** *Symptom:* {{ g.lag_receipt_n }} late applications. *Response:* ask which came first, receipt or invoice.
- **Deposits as lapping.** *Symptom:* {{ g.early_r }} receipts flagged. *Response:* ask whose receipts they were.
- **A first-digit result as assurance.** *Symptom:* "conforms, so clean". *Response:* ask whether these amounts suit the test at all.
- **An accusation.** *Symptom:* "diverted refund" as the finding. *Response:* ask what the records show.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Recomputation (S1 to S3) | 25 | Every credit traced, tolerance and rounding named | Counts without a tolerance |
| Restocking by reason | 15 | By reason and year, below-standard lines explained | Totals only |
| Lapping tests | 15 | Customer, deposit and application tests, deposits explained | One test |
| First-digit reasoning | 10 | Chapter 8's criteria applied to these populations, limits stated (the chance MAD is a plus) | Run and reported |
| Timeline | 20 | Every step dated, with its document and role | Steps without roles |
| Disposition and evidence | 15 | Follow up, evidence listed, wording neutral | A conclusion |

## Extensions and discussion questions

- Build the same timeline for the next largest refund and compare the two.
- Discuss: how would you word the finding on the largest refund for the committee?
