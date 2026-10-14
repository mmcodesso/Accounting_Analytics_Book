# Exercise 8.5: Testing Purchasing and Payment Controls

| | |
|---|---|
| Unit | Chapter 8: Audit Analytics in Excel |
| Item | Exercise 8.5 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 150 minutes |
| Solution file | Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheets Ex 8.5, Ex 8.5 Requisitions and Ex 8.5 Payments, with the queries Approvers, POApprovals, InvoiceApprovals and Requisitions |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

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
- **Data conditions.** The chief financial officer approved nearly all of the 18,832 purchase orders. Only a few employees have a TerminationDate, so for 18,826 orders the approver's date is blank. The requisitions table holds 25,364 rows. The Payments Table holds 39,864 payments.
- **Verify first.** Run the three flags once. The capital purchase orders of Exercise 8.2 should score 2, and AfterTermination should flag 3 orders.

## How to run it

Pairs, about 150 minutes, best over two sessions: 20 for requirement (1), 25 for (2), 20 for (3), 25 for (4), 15 for (5), 10 for (6) and 35 for the memo (7). Hold back the blank-date hint until a flag count is far too large, and the consecutive-numbers hint until the band count is charted. Collect the workbook and the memo.

![Requisitions by 50-dollar band around the 5,000-dollar approval limit, the chart of requirement 4.](../figures/chapter-08-audit-analytics/IF-08-5-A.pdf)

## Step-by-step solution

### Requirement (1): Orders with their approvers

**Step 1. Build Approvers and POApprovals.**

a. Import **T74_Employee** with **Transform Data**, name the query `Approvers` and keep EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount and TerminationDate.
b. Import **T33_PurchaseOrder** as `POApprovals`. Merge Approvers on ApprovedByEmployeeID, with a left outer join, and expand EmployeeName, JobTitle, MaxApprovalAmount and TerminationDate without the prefix. Rename them `ApproverName`, `ApproverTitle`, `ApproverLimit` and `ApproverTerminationDate`.
c. Merge Approvers again on CreatedByEmployeeID, expand EmployeeName and rename it `CreatorName`. Load both queries as Tables.

**Check:** 18,832 rows. **Watch for:** the first expanded columns left unrenamed, so that the second EmployeeName arrives with a suffix.

### Requirement (2): Flags and dispositions

**Step 2. Add the flags and the score.** Add the four columns below to the POApprovals Table.

```
=[@CreatedByEmployeeID]=[@ApprovedByEmployeeID]
=[@OrderTotal]>[@ApproverLimit]
=AND([@ApproverTerminationDate]<>"",[@ApproverTerminationDate]<[@OrderDate])
=[@SelfApproved]+[@AboveLimit]+[@AfterTermination]
```

**Check:** 9 self-approved orders, 13 above the limit and 3 approved after termination; 11 orders score 2 and 3 score 1. **Watch for:** the blank guard left out of AfterTermination. An empty cell compares as earlier than any date, so the flag is TRUE for nearly every order.

**Step 3. Record a disposition for each flagged order.** Sort by RiskScore, filter to 1 or more, paste the rows as values with **Paste Special > Values** and add a `Disposition` column and a `Design or operation` column, as in Tutorial 8.3 Step 5. The model answer's groups:

- 2 note-financed capital purchases, created and approved by the purchasing manager (limit $25,000.00): follow up, design and operation; ask for the board's approval.
- 6 orders created and approved by the same person, among the buyers and procurement analysts, whose limit is $0: follow up, design and operation.
- 3 orders approved under the ID of Daniel Diaz, account executive, terminated on 2024-04-26: follow up; ask for the approval timestamp and the access log.
- 1 order created and approved by the purchasing manager within the limit: follow up at low risk, a design gap in segregation of duties.
- 2 orders approved above the approver's limit by someone with a limit above $0: follow up, operation.

![A mock of the flagged purchase orders pasted as values with their dispositions, as the model answer lays them out.](../figures/chapter-08-audit-analytics/IF-08-5-B.pdf)

### Requirement (3): Supplier invoices

**Step 4. Build InvoiceApprovals.** Import **T37_PurchaseInvoice** as `InvoiceApprovals`, merge Approvers on ApprovedByEmployeeID, expand the name, title and limit, add `AboveLimit` as `=[@GrandTotal]>[@ApproverLimit]` and list the invoices whose ApproverTitle is not Chief Financial Officer. **Check:** 8 of 40,204 invoices have another approver (40,196 were approved by the chief financial officer), together $646,691.67. They fall into three groups:

- Melinda Murphy, Product Analyst, limit $0.00: 4 invoices. No: a role with no approval authority.
- Daniel Odom, Production Supervisor, limit $5,000.00: 2 invoices, within the limit. No: a role outside purchasing and accounting can confirm receipt, not approve payment.
- Jennifer Cole, Purchasing Manager, limit $25,000.00: 2 invoices, above the limit. No: the same person created and approved their orders.

### Requirement (4): Requisitions near an approval limit

**Step 5. Count the bands and chart them.** Import **T32_PurchaseRequisition** as `Requisitions` and add `RequisitionValue` as `=[@Quantity]*[@EstimatedUnitCost]`. On a new worksheet list the lower bounds of the 8 bands in a column and count each with the formula below, then insert a column chart.

```
=COUNTIFS(Requisitions[RequisitionValue],">="&B4,Requisitions[RequisitionValue],"<"&B4+50)
```

**Check:** the counts from $4,800.00 are 7, 8, 4, 18, 9, 4, 9, 4, so the band from $4,950.00 holds 18, twice any neighbor.

**Step 6. Examine the band.** Filter the Table to the band, sort by RequisitionNumber and list each requisition with requester, approver, dates and status. **Check:** all 18 were converted to orders, and 6 have no approver (PR-2024-000001, -000002, PR-2025-004714, -004715, PR-2026-013258, -013259), the requisitions of Exercise 2.5. There are two runs of three consecutive numbers with the same value (PR-2025-004714 to -004716 and PR-2026-013258 to -013260), each for 627 units at $7.96 ($4,990.92), for different items and mostly different requesters. In each run only the last requisition has an approver. Two employees have a limit of $5,000.00 (production supervisor and production planner), the only limit just above the band.

### Requirement (5): Near-duplicate payments

**Step 7. Add the two flags and count them.** Enter the two COUNTIFS formulas of the exercise as `SameAmount` and `SameInvoice` in the Payments Table, then count them. **Check:** SameAmount flags 226 payments in 113 pairs, 13 pairs at most 30 days apart; SameInvoice flags none, so every pair pays two different invoices. **Watch for:** the slow recalculation, because each payment is compared with every other, and a count of pairs by halving the flags, which holds only because no group is larger than two.

### Requirement (6): Gap test on order numbers

**Step 8. Test each year.** Add `POYear` and `POSeq` as the exercise gives, then for each year count the orders, find the smallest and largest sequence number and count the distinct numbers.

```
=COUNTIF(POApprovals[POYear],A5)
=MINIFS(POApprovals[POSeq],POApprovals[POYear],A5)
=MAXIFS(POApprovals[POSeq],POApprovals[POYear],A5)
=ROWS(UNIQUE(FILTER(POApprovals[POSeq],POApprovals[POYear]=A5)))
```

**Check:**

- 2024: 3,921 orders, numbers 1 to 3,921, 3,921 distinct, none missing.
- 2025: 6,545 orders, numbers 3,922 to 10,466, 6,545 distinct, none missing.
- 2026: 8,366 orders, numbers 10,467 to 18,832, 8,366 distinct, none missing.

Each year starts where the year before ended, which a reader of the prefix might not expect.

### Requirement (7): The memo

**Step 9. Outline the memo.** To the chief audit executive: the exceptions with counts; design weaknesses (self-approval, a terminated employee's ID and unapproved requisitions were all accepted) against operation failures (managers approving above their limits); the clean results with what they exclude; follow-up requests; and a note that the classification is provisional until the policy, the configuration and the access logs are seen.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Purchase orders, and the share approved by the chief financial officer | 18,832; 99.9% | 2 |
| Self-approved, above the limit, after termination | 9; 13; 3 | 2 |
| Orders scoring 2 and 1 | 11; 3 | 2 |
| Invoices approved by another approver, and their total | 8; $646,691.67 | 4 |
| Requisitions in the band, and without an approver | 18; 6 | 6 |
| SameAmount payments, pairs, pairs within 30 days, SameInvoice | 226; 113; 13; 0 | 7 |

> **Instructor notes, Exercise 8.5:** 18,832 purchase orders; the CFO approved 99.9% of them. SelfApproved: 9 (PO-2024-000001, -000002, -000003, PO-2024-001942 for 360,000.00, PO-2025-003923, -003924, PO-2026-010468, -010469, and PO-2026-011104 for 280,000.00; the two large ones were created and approved by the Purchasing Manager, limit 25,000, and are the note-financed capital purchases of Exercise 8.2). AboveLimit: 13, including orders approved by Buyers and Procurement Analysts with a limit of 0, PO-2024-000040 (Production Manager, 26,027.28 against 25,000) and PO-2024-000042 (Production Supervisor, 13,737.60 against 5,000). AfterTermination: 3 (PO-2024-000474, PO-2025-003922, PO-2026-010467), all approved by Daniel Diaz, an Account Executive terminated on 2024-04-26. Risk scores: 11 orders score 2 and 3 score 1. Requisition bands from 4,800: 7, 8, 4, 18, 9, 4, 9, 4, so the 4,950-4,999.99 band has twice the count of any neighbor. Its 18 requisitions were all converted to POs; 6 have no approver (PR-2024-000001, -000002, PR-2025-004714, -004715, PR-2026-013258, -013259, the requisitions of Exercise 2.5). PR-2025-004714 to -004716 and PR-2026-013258 to -013260 are three consecutive requisitions each, dated January 1, all for 627 units at 7.96 (4,990.92), for different items and mostly different requesters. Two employees have a 5,000 limit (a Production Supervisor and a Production Planner). Supplier invoices: the CFO approved 40,196 of 40,204; the other 8 are PI 7038, 7047, 20345, and 20399 (200.69, 3,102.49, 794.96, 23.20), approved by Melinda Murphy, a Product Analyst with a limit of 0; PI 7122 and 20452 (1,301.21, 1,269.12), approved by Daniel Odom, a Production Supervisor, within the 5,000 limit but outside the purchasing and accounting roles; and PI 3160 and 21692 (360,000.00 and 280,000.00), approved by Jennifer Cole, the Purchasing Manager, above the 25,000 limit, the note-financed capital invoices of Exercise 8.2. Near-duplicates, payments dated before 2027-01-01: SameAmount flags 226 payments in 113 pairs (no group larger than two; 13 pairs at most 30 days apart); SameInvoice flags none, so every pair pays two different invoices; the test does not exclude a bill entered under two invoice numbers or an invoice overpaid in unequal parts, which are other tests. Gap test: PO-2024 runs 1 to 3,921 (3,921 orders), PO-2025 3,922 to 10,466 (6,545), PO-2026 10,467 to 18,832 (8,366); the numbers are unique, none is missing, and the sequence continues across years rather than restarting.

## What a strong answer says

- **Requirements (2) and (3).** Each flagged order with the evidence that would clear it, never "expected" without evidence; the capital orders singled out; the terminated approver's orders called provisional.
- **Requirement (4).** The band's count against its neighbors, the unapproved requisitions tied to Exercise 2.5, the identical consecutive requisitions and the limit just above the band, read together as a possible split to stay under a review level.
- **Requirement (7).** Design and operation separated, the clean results recorded with what they exclude, and follow-up that names a document or a log.

A weak answer lists counts without a classification, treats every exception as fraud, or leaves out the clean tests.

## Common mistakes and how to respond

- **Colliding merge columns.** *Symptom:* a numbered duplicate of EmployeeName and no CreatorName. *Response:* ask which merge it came from.
- **No blank guard.** *Symptom:* about 18,826 orders flagged AfterTermination. *Response:* ask what an empty cell is as a date.
- **"Expected" without evidence.** *Symptom:* a disposition of "fine". *Response:* ask which document clears it.
- **Invoices flagged, roles not judged.** *Symptom:* a list with no assessment. *Response:* ask whether the role belongs in invoice approval.
- **A band count with no neighbors.** *Symptom:* "18 is a lot". *Response:* ask how many are on either side.
- **Pairs read as duplicate payments.** *Symptom:* "226 duplicates". *Response:* ask what SameInvoice shows.
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
