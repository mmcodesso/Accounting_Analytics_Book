---
note: ch08.ex5
uses: [ch08.g5]
title: Testing Purchasing and Payment Controls
kind: exercise
number: '8.5'
unit: '8'
perspective: auditing
tool: excel
minutes: 150
solution: "Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheets Ex 8.5, Ex 8.5 Requisitions and Ex 8.5 Payments, with the queries Approvers, POApprovals, InvoiceApprovals and Requisitions"
figures:
  - id: IF-08-5-A
    kind: chart
    purpose: Requisitions by 50-dollar band around the 5,000-dollar approval limit, the chart of requirement 4.
    shows: "A column chart of the eight bands, each labeled with its range and its count. The band just below the approval limit is about twice as tall as any other and is drawn in the highlight color; the rest are gray."
    data: PurchaseRequisition, RequisitionValue as Quantity times EstimatedUnitCost, counted in 50-dollar bands (the Expected results table).
  - id: IF-08-5-B
    kind: excel-mock
    purpose: The flagged purchase orders pasted as values with their dispositions, as the model answer lays them out.
    shows: "The flagged orders sorted by RiskScore, with the three flag columns, RiskScore, Disposition and Design or operation. The two capital orders are outlined. Disposition cells hold a wrapped sentence that starts with Follow up."
    data: POApprovals filtered to RiskScore 1 or more (the Expected results table).
---
{% set x = ch08_g5 %}
# Exercise 8.5: Testing Purchasing and Payment Controls

{{ header() }}

## Purpose and learning outcomes

Tutorial 8.3 tested journal entries with flags, a score and dispositions. This exercise applies the same method to purchase orders and supplier invoices, then adds the three tests the chapter only describes: threshold bands, near-duplicates and a gap test. It ends where an auditor's report ends: weakness in the design of a control or failure in its operation, and the clean results recorded with the exceptions. The analytics type is diagnostic, with recommendations.

By the end, students can:

- join approvers to orders and invoices and flag self-approval, approval above a limit and approval after termination (outcome 4);
- evaluate who approves supplier invoices (outcome 4);
- test for amounts just below a threshold and for identical consecutive documents (outcome 5);
- run near-duplicate and gap tests and report their clean results (outcome 5);
- classify exceptions as design or operation and say why the classification is provisional (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls), Core S2 M5 (risk of fraud and noncompliance) and ISC M2 (tests of internal controls, logical access and change management); IMA Reporting and Control (internal control); IFAC IES 2 (f) and (g); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3, with the Payments Table of Tutorial 8.1 and the Employees query of Tutorial 8.3. Exercise 2.5 and Exercise 8.2 help but are not required.
- **Data conditions.** The chief financial officer approved nearly all of the {{ orders|count }} purchase orders. Only a few employees have a TerminationDate, so for {{ x.no_term|count }} orders the approver's date is blank. The requisitions table holds {{ x.n_reqs|count }} rows. The Payments Table holds {{ x.payments|count }} payments.
- **Verify first.** Run the three flags once. The capital purchase orders of Exercise 8.2 should score 2, and AfterTermination should flag {{ term|length }} orders.

## How to run it

Pairs, about 150 minutes, best over two sessions: 20 for requirement (1), 25 for (2), 20 for (3), 25 for (4), 15 for (5), 10 for (6) and 35 for the memo (7). Hold back the blank-date hint until a flag count is far too large, and the consecutive-numbers hint until the band count is charted. Collect the workbook and the memo.

{{ figure('IF-08-5-A') }}

## Step-by-step solution

### Requirement (1): Orders with their approvers

**Step 1. Build Approvers and POApprovals.**

a. Import **T74_Employee** with **Transform Data**, name the query `Approvers` and keep EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount and TerminationDate.
b. Import **T33_PurchaseOrder** as `POApprovals`. Merge Approvers on ApprovedByEmployeeID, with a left outer join, and expand EmployeeName, JobTitle, MaxApprovalAmount and TerminationDate without the prefix. Rename them `ApproverName`, `ApproverTitle`, `ApproverLimit` and `ApproverTerminationDate`.
c. Merge Approvers again on CreatedByEmployeeID, expand EmployeeName and rename it `CreatorName`. Load both queries as Tables.

**Check:** {{ orders|count }} rows. **Watch for:** the first expanded columns left unrenamed, so that the second EmployeeName arrives with a suffix.

### Requirement (2): Flags and dispositions

**Step 2. Add the flags and the score.** Add the four columns below to the POApprovals Table.

```
=[@CreatedByEmployeeID]=[@ApprovedByEmployeeID]
=[@OrderTotal]>[@ApproverLimit]
=AND([@ApproverTerminationDate]<>"",[@ApproverTerminationDate]<[@OrderDate])
=[@SelfApproved]+[@AboveLimit]+[@AfterTermination]
```

**Check:** {{ selfs|length }} self-approved orders, {{ n_above }} above the limit and {{ term|length }} approved after termination; {{ s2 }} orders score 2 and {{ s1 }} score 1. **Watch for:** the blank guard left out of AfterTermination. An empty cell compares as earlier than any date, so the flag is TRUE for nearly every order.

**Step 3. Record a disposition for each flagged order.** Sort by RiskScore, filter to 1 or more, paste the rows as values with **Paste Special > Values** and add a `Disposition` column and a `Design or operation` column, as in Tutorial 8.3 Step 5. The model answer's groups:

- {{ x.kinds.capital }} note-financed capital purchases, created and approved by the {{ big_role|lower }} (limit ${{ big_limit|money }}): follow up, design and operation; ask for the board's approval.
- {{ x.kinds.self_zero }} orders created and approved by the same person, among the {{ zero_titles|join(' and ')|lower }}, whose limit is $0: follow up, design and operation.
- {{ x.kinds.terminated }} orders approved under the ID of {{ term_name }}, {{ term_title|lower }}, terminated on {{ term_date }}: follow up; ask for the approval timestamp and the access log.
- {{ x.kinds.self_within }} order created and approved by the purchasing manager within the limit: follow up at low risk, a design gap in segregation of duties.
- {{ x.kinds.above_only }} orders approved above the approver's limit by someone with a limit above $0: follow up, operation.

{{ figure('IF-08-5-B') }}

### Requirement (3): Supplier invoices

**Step 4. Build InvoiceApprovals.** Import **T37_PurchaseInvoice** as `InvoiceApprovals`, merge Approvers on ApprovedByEmployeeID, expand the name, title and limit, add `AboveLimit` as `=[@GrandTotal]>[@ApproverLimit]` and list the invoices whose ApproverTitle is not Chief Financial Officer. **Check:** {{ inv_other }} of {{ inv_total|count }} invoices have another approver ({{ inv_cfo|count }} were approved by the chief financial officer), together ${{ x.other_total|money }}. They fall into three groups:

- {{ g.zero.name }}, {{ g.zero.title }}, limit ${{ g.zero.limit|money }}: {{ g.zero.ids|length }} invoices. No: a role with no approval authority.
- {{ g.within.name }}, {{ g.within.title }}, limit ${{ g.within.limit|money }}: {{ g.within.ids|length }} invoices, within the limit. No: a role outside purchasing and accounting can confirm receipt, not approve payment.
- {{ g.beyond.name }}, {{ g.beyond.title }}, limit ${{ g.beyond.limit|money }}: {{ g.beyond.ids|length }} invoices, above the limit. No: the same person created and approved their orders.

### Requirement (4): Requisitions near an approval limit

**Step 5. Count the bands and chart them.** Import **T32_PurchaseRequisition** as `Requisitions` and add `RequisitionValue` as `=[@Quantity]*[@EstimatedUnitCost]`. On a new worksheet list the lower bounds of the {{ x.n_bands }} bands in a column and count each with the formula below, then insert a column chart.

```
=COUNTIFS(Requisitions[RequisitionValue],">="&B4,Requisitions[RequisitionValue],"<"&B4+50)
```

**Check:** the counts from ${{ x.first_band|money }} are {{ bands|join(', ') }}, so the band from ${{ x.band_examined|money }} holds {{ band }}, twice any neighbor.

**Step 6. Examine the band.** Filter the Table to the band, sort by RequisitionNumber and list each requisition with requester, approver, dates and status. **Check:** all {{ band }} were converted to orders, and {{ unapproved|length }} have no approver ({{ unapproved|join(', ') }}), the requisitions of Exercise 2.5. There are {{ x.n_runs_word }} runs of {{ run_len }} consecutive numbers with the same value ({% for r in runs %}{{ r.first }} to {{ r.last }}{% if not loop.last %} and {% endif %}{% endfor %}), each for {{ qty|num(0) }} units at ${{ cost|money }} (${{ value|money }}), for different items and {{ requesters }}. In each run only the last requisition has an approver. {{ n_five }} employees have a limit of ${{ x.band_edge|money }} ({{ five|join(' and ')|lower }}), the only limit just above the band.

### Requirement (5): Near-duplicate payments

**Step 7. Add the two flags and count them.** Enter the two COUNTIFS formulas of the exercise as `SameAmount` and `SameInvoice` in the Payments Table, then count them. **Check:** SameAmount flags {{ n_payments }} payments in {{ pairs }} pairs, {{ within30 }} pairs at most 30 days apart; SameInvoice flags none, so every pair pays two different invoices. **Watch for:** the slow recalculation, because each payment is compared with every other, and a count of pairs by halving the flags, which holds only because no group is larger than two.

### Requirement (6): Gap test on order numbers

**Step 8. Test each year.** Add `POYear` and `POSeq` as the exercise gives, then for each year count the orders, find the smallest and largest sequence number and count the distinct numbers.

```
=COUNTIF(POApprovals[POYear],A5)
=MINIFS(POApprovals[POSeq],POApprovals[POYear],A5)
=MAXIFS(POApprovals[POSeq],POApprovals[POYear],A5)
=ROWS(UNIQUE(FILTER(POApprovals[POSeq],POApprovals[POYear]=A5)))
```

**Check:**

{% for gp in gaps %}
- {{ gp.year }}: {{ gp.n|count }} orders, numbers {{ gp.low|count }} to {{ gp.high|count }}, {{ gp.distinct|count }} distinct, none missing.
{% endfor %}

Each year starts where the year before ended, which a reader of the prefix might not expect.

### Requirement (7): The memo

**Step 9. Outline the memo.** To the chief audit executive: the exceptions with counts; design weaknesses (self-approval, a terminated employee's ID and unapproved requisitions were all accepted) against operation failures (managers approving above their limits); the clean results with what they exclude; follow-up requests; and a note that the classification is provisional until the policy, the configuration and the access logs are seen.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Purchase orders, and the share approved by the chief financial officer | {{ orders|count }}; {{ cfo_share|pct(1) }} | 2 |
| Self-approved, above the limit, after termination | {{ selfs|length }}; {{ n_above }}; {{ term|length }} | 2 |
| Orders scoring 2 and 1 | {{ s2 }}; {{ s1 }} | 2 |
| Invoices approved by another approver, and their total | {{ inv_other }}; ${{ x.other_total|money }} | 4 |
| Requisitions in the band, and without an approver | {{ band }}; {{ unapproved|length }} | 6 |
| SameAmount payments, pairs, pairs within 30 days, SameInvoice | {{ n_payments }}; {{ pairs }}; {{ within30 }}; 0 | 7 |

{{ expected() }}

## What a strong answer says

- **Requirements (2) and (3).** Each flagged order with the evidence that would clear it, never "expected" without evidence; the capital orders singled out; the terminated approver's orders called provisional.
- **Requirement (4).** The band's count against its neighbors, the unapproved requisitions tied to Exercise 2.5, the identical consecutive requisitions and the limit just above the band, read together as a possible split to stay under a review level.
- **Requirement (7).** Design and operation separated, the clean results recorded with what they exclude, and follow-up that names a document or a log.

A weak answer lists counts without a classification, treats every exception as fraud, or leaves out the clean tests.

## Common mistakes and how to respond

- **Colliding merge columns.** *Symptom:* a numbered duplicate of EmployeeName and no CreatorName. *Response:* ask which merge it came from.
- **No blank guard.** *Symptom:* about {{ x.no_term|count }} orders flagged AfterTermination. *Response:* ask what an empty cell is as a date.
- **"Expected" without evidence.** *Symptom:* a disposition of "fine". *Response:* ask which document clears it.
- **Invoices flagged, roles not judged.** *Symptom:* a list with no assessment. *Response:* ask whether the role belongs in invoice approval.
- **A band count with no neighbors.** *Symptom:* "18 is a lot". *Response:* ask how many are on either side.
- **Pairs read as duplicate payments.** *Symptom:* "{{ n_payments }} duplicates". *Response:* ask what SameInvoice shows.
- **A gap test that expects a restart.** *Symptom:* a reported gap at each January. *Response:* ask whether the series is meant to restart.
- **Cause stated as fact.** *Symptom:* "the system failed". *Response:* ask what you would need to see.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: queries | 10 | Both merges, names renamed | Columns missing |
| Requirement 2: flags and dispositions | 20 | Three flags, score, reasoned dispositions | Flags without dispositions |
| Requirement 3: invoices | 15 | List, limit flag, role assessment | No assessment |
| Requirement 4: requisitions | 20 | Bands, chart, band examined, links to Exercise 2.5 | Bands only |
| Requirement 5: near-duplicates | 10 | Both counts, the difference explained | Counts only |
| Requirement 6: gap test | 10 | Per-year checks, clean result stated | One check missing |
| Requirement 7: memo | 15 | Design and operation separated, clean results, follow-up | One element missing |

## Extensions and discussion questions

- Count orders in narrow bands around the Production Manager's limit. Is there a concentration below it?
- Discuss: should a system ever accept an approval by the person who created the document?
- Discuss: the capital purchase orders exceed every approval limit in the Employee table. Who should have approved them, and where would the record be?
