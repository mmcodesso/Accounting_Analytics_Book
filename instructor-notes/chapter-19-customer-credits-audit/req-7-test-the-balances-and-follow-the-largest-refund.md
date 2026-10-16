# Requirement 7: Test the balances, and follow the largest refund (Chapters 8 and 12)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 7 |
| Perspective | Auditing |
| Tools | More than one tool |
| Time | About 150 minutes |
| Solution file | Chapter19-capstone-sql.zip: Credits.sql, the queries headed Requirement 7 (tests S1 to S6); Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Timeline (the largest refund live, the timeline, the restocking by reason, the results and the disposition) |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 4 tested the controls; this one tests the amounts. A substantive test asks whether a balance is right, and sharing a population with a control test does not make its result evidence for the other. Students recompute every credit from its sources, value the restocked goods, test for lapping, and follow the largest refund. The analytics type is diagnostic. SQL fits the recomputation and lapping tests, which repeat exactly over the whole population; Excel fits the timeline, a sequence with roles and a disposition that the committee reads.

Students can recompute a document from its sources and state a tolerance (Part 1), value restocked goods by reason (Part 2), test and explain lapping and a first-digit test's limits (Part 3), and build a timeline worded as what the records show (Part 4).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Reporting and Control (internal control); IFAC IES 2 (f) and IES 4 (a); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite and Credits.sql, and Credits Audit.xlsx with the Refunds, Credits and ReturnLines Tables of Requirement 4.
- **Data conditions.** Stored LineTotal values are rounded, so a tolerance is a decision. Credits with freight carry tax on the freight. Receipts can arrive before their invoice. One refund is the largest.
- **Verify first.** Run S1 to S6: each returns at once, S1 and S5 one row, S3 3 rows, S6 10.

## How to run it

Pairs, about 150 minutes: 25 for S1, 20 for S2, 10 for S3, 20 for S4, 25 for S5 and the first-digit reasoning, 35 for S6 and the Timeline sheet, 15 for the disposition. The routine for every query: type it under its two comment lines, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the disposition until the timeline is complete. **Collect** Credits.sql and the Timeline sheet.

## Step-by-step solution

### Part 1: Recompute each credit line and credit (S1 to S3)

**Step 1. Trace and recompute every credit line (S1).** One row of counts joins each line to its return, shipment and invoice line; the test of the stored total is the one to read.

```sql
SUM(CASE WHEN ABS(LineTotal
        - ROUND(Quantity * UnitPrice * (1 - Discount), 2)) > 0.004
        THEN 1 ELSE 0 END) AS LineTotalOff,
```

**Check:** 637 of 637 lines traced, none above the quantity shipped or returned, none returned twice, none off the invoice's price or discount, and 1 stored total off by a half cent (credit line 84). Rounded half up on the exact product, credit lines 248, 290, 626 differ instead: a rounding difference, not an error. **Watch for:** the stored total compared with the unrounded product at a tolerance below half a cent, which flags 88 lines.

**Step 2. Recompute every credit (S2).** Its tax test reads the rate from the credits themselves and applies it to the subtotal plus the freight credited.

```sql
SUM(CASE WHEN ABS(TaxAmount - ROUND((SubTotal + FreightCreditAmount)
        * (SELECT TaxRate FROM Rate), 2)) > 0.005 THEN 1 ELSE 0 END)
        AS TaxOff,
```

**Check:** 612 credits on as many invoices, none above its invoice, each subtotal equal to its lines, tax at 6.5% on every credit, no freight credit above the invoice's. The rate is read from the credits, a diagnostic that every invoice's tax at the same rate corroborates. The freight test is only an upper bound, so the answer asks for the freight policy for partial returns. **Watch for:** tax tested on the subtotal alone, which flags 99 credits, exactly those with freight.

**Step 3. List the open items in 2060 (S3).** The credits whose part posted to 2060 is not refunded by the last year-end.

**Check:** 3 credits, CM-2026-000583 ($1,503.06); CM-2026-000605 ($912.97); CM-2026-000607 ($997.43), adding up to the account's balance at the year-end.

### Part 2: Measure the restocking by reason (S4)

**Step 4. Group the return lines by reason and year (S4).** The query adds each line's recorded cost and compares it with quantity times the item's standard cost.

```sql
SUM(CASE WHEN ABS(srl.ExtendedStandardCost
        - ROUND(srl.QuantityReturned * i.StandardCost, 2)) > 0.011
        THEN 1 ELSE 0 END) AS LinesOffStandard,
```

**Check:** goods returned Damaged went back at $77,248.17 over the three years, and with Quality Concern $61,146.00 in the last year; no account writes them down. These are gross flows, not the inventory still held: a valuation follow-up. **Watch for:** 17 lines of less than one unit sit $547.29 below standard ($175.48 Damaged or Quality Concern). Recomputing at the item's cost calls them errors; the records cost a whole shipment line at the quantity times its extended cost.

### Part 3: Test for lapping, and explain the first-digit test (S5)

**Step 5. Test receipts against invoices, deposits and applications (S5).** One row of subqueries, the first of which compares the customer on the receipt with the customer on the invoice.

```sql
(SELECT SUM(CASE WHEN ReceiptCustomer <> InvoiceCustomer
        THEN 1 ELSE 0 END) FROM Applied) AS OtherCustomersInvoice,
```

**Check:** no application to another customer's invoice, deposits 0 to 2 days after receipt, applications 0 to 28 days after their receipt (those over two days all of receipts dated before their invoice) and within 2 days of the later of receipt and invoice date, every receipt fully applied. 491 receipts ($395,196.29) were applied to invoices dated after them: deposits held in 2060, not lapping, as far as these tests reach. **Watch for:** either delay shown alone. The raw delay, up to 28 days on 486 applications, is the observation, and the receipts dated before their invoice explain it, so the answer shows both.

**Step 6. Explain why a first-digit test does not suit these populations.** Use Chapter 8's criteria for populations that suit the test: the credits and refunds are subsets selected by an event, and their amounts follow the invoice lines they reverse, so they cannot spread across the digits as the law expects.

**Check:** a population of 222 refunds that followed the law exactly would show a mean absolute deviation of about 0.0158 by chance, beyond the 0.015 of nonconformity, and one of 612 credits about 0.0095. The actual values, 0.0119 and 0.0105, are of that size, so a departure could not be told from chance. **Watch for:** the result read as assurance or as a finding.

### Part 4: Follow the largest refund (S6 and the Timeline sheet)

**Step 7. Build the steps in date order (S6).** The query stacks one step for each document with its date, a step order and who did it, and sorts by date, step order and document. Joined from the invoice's lines, the shipment would repeat; DISTINCT stops that.

```sql
SELECT DISTINCT s.ShipmentDate AS StepDate, 1 AS StepOrder,
        'Shipment' AS Step, s.ShipmentNumber AS Document,
```

**Check:** 10 rows: the shipment, the invoice, 3 receipts, the return, the credit, the clawbacks and the refund. **Watch for:** DISTINCT missing, because invoice SI-2025-008932 has 2 lines on 1 shipment, and a sort on the date alone, which leaves the credit and its clawbacks, dated the same day, in no fixed order.

**Step 8. Lay out the timeline and the disposition in Excel.**

a. On the Timeline sheet, build the live block that finds the largest refund and its facts; its first formulas are below (B4, B5 and B7, with the refund date in B6).
b. Paste S6's rows with **Copy with Headers** below it, with a note naming the query, and type the last step, the invoice settled.
c. Write the disposition and the evidence outside the database.

```
=MAX(Refunds[Amount])
=XLOOKUP(B4,Refunds[Amount],Refunds[RefundNumber])
=TEXT(B6,"dddd")
```

![The picture behind the disposition.](../figures/chapter-19-customer-credits-audit/IF-19-7-A.pdf)

**Check:** RF-2025-000097, $17,745.96, the largest refund, of the largest credit; $13,081.41 of the invoice was unpaid on the refund date (the sequence is in the note below). The disposition is follow up, not a conclusion; the evidence to request is the wire confirmation's beneficiary and account against the customer's known bank details, and an explanation of why the refund went by wire to a customer who paid this invoice by check, and why before its checks arrived. **Watch for:** the Sunday read as evidence. Weekend dates hold 62 of the 222 refunds, about the share of the week they are. The timeline shows what the records say and proves no act.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Lines traced; stored totals off by a half cent | 637 of 637; 1 | 1 |
| Credits recomputed; tax rate; credits with freight | 612; 6.5%; 99 | 2 |
| Damaged restocked; Damaged and Quality Concern, last year | $77,248.17; $61,146.00 | 4 |
| Receipts applied before their invoice; amount | 491; $395,196.29 | 5 |
| Largest refund; unpaid on its invoice | $17,745.96; $13,081.41 | 8 |

> **Instructor notes, Requirement 7:** substantive tests clean on the recorded documents: 637 of 637 credit lines trace to their return, shipment, and invoice lines; no quantity above shipped, credited quantity equal to the returned quantity on every line, and no shipment line returned twice; price and discount equal the invoice line's; LineTotal = ROUND(Q x P x (1 - D), 2) except a half-cent on credit line 84, while by exact decimal rounding half up lines 248, 290, 626 are a cent lower instead, so the stored totals follow no single rule on exact half-cents: rounding differences, not errors; 612 credits on 612 distinct invoices, none above its invoice; SubTotal = the lines; tax = 6.5% of (SubTotal + freight credit) on all 612 (a test on SubTotal alone falsely flags the 99 credits with freight), a rate read from the credits' own totals, which every invoice's tax corroborates (the same rate on SubTotal plus freight), though whether the rate is right in law lies outside the records; no freight credit above the invoice's freight, an upper bound rather than a recomputation, since nothing in the records says how freight is credited on a partial return, so the answer reports that limit and asks for the policy. Restocked at standard cost, except 17 return lines of less than one unit, costed at the quantity times the shipment line's extended cost (547.29 below standard, 175.48 of it Damaged and Quality Concern): Damaged 77,248.17 (11,606.17 / 25,617.84 / 40,024.16) and Damaged plus Quality Concern 137,606.43 (2026: 61,146.00): a valuation follow-up. Lapping clean: no application to another customer's invoice; deposits 0-2 days after receipt; applications 0-28 days after their receipt, the 486 over two days all of receipts dated before their invoice, and every application within 2 days of the later of receipt and invoice date; every receipt fully applied; 491 receipts (526 applications, 395,196.29) were applied to invoices dated after the receipt, deposits held in 2060, not lapping, as far as these tests reach. First digits: a weak procedure here, not one ruled out by a minimum count: the credits and refunds are subsets selected by events (a return, then the part of a credit posted to customer deposits), their amounts follow the invoice lines they reverse, and with 222 refunds a population that followed Benford's Law exactly would show a MAD of about 0.0158 by chance alone, beyond the 0.015 of nonconformity, and the 612 credits about 0.0095; their MADs, 0.0119 and 0.0105, are of that size, so a departure could not be told from chance. Timeline: SH-2025-004100 shipped 2025-04-27 (FedEx Freight), delivered 04-30; SI-2025-008932 dated 04-30, 18,774.16, due 06-14 (customer 128); CR-2025-003258 05-17, check, 5,692.75 applied (recorded and applied by the Customer Service Manager); SR-2025-000255 06-06, Damaged (15.71 of 15.71 FUR-DSK-0071; 2.62 of 6.86 FUR-CTB-0045), received by a Shipping Clerk; CM-2025-000255 06-09, 17,745.96, the largest credit of the three years, approved by representative 115 with a limit of 0, all to 2060 while 13,081.41 of the invoice was unpaid; clawbacks SCAJ-2025-000268/269 (321.33 and 11.93); RF-2025-000097 06-15, a Sunday, wire, approved by the Accounting Manager (within the 25,000 limit), cleared 06-18; CR-2025-003473 06-17, check, 9,891.91 applied (recorded and applied on 06-19 by the Customer Service Manager); CR-2025-003342 06-18, check, 3,189.50 applied (recorded by representative 97, applied on 06-19 by representative 115, the credit's approver); the invoice was settled on 06-19. Disposition: follow up, not a conclusion. Evidence: the wire confirmation's beneficiary and account against the customer's known bank details; a confirmation from the customer of the credit and the refund; the receiving and inspection record and any carrier claim; the customer's written request; why the refund went by wire to a customer who paid this invoice by check, and why before its checks arrived.

## What a strong answer says

- **Each recomputation states its tolerance and names the rounding,** and finds no error.
- **Restocking is a flow at standard cost with no write-down,** reported as a valuation follow-up, not a misstatement.
- **The lapping tests are stated, and the deposits are explained.**
- **The first-digit test is reasoned about with Chapter 8's criteria,** not run and believed.
- **The timeline gives each step a date, a document and a role,** and the disposition is follow up with the evidence that would settle it.

A weak answer reports the rounding as errors, reads the deposits as lapping, or words the timeline as an accusation.

## Common mistakes and how to respond

- **The unrounded product.** *Symptom:* 88 lines "wrong". *Response:* ask what the stored total is rounded to.
- **Tax on the subtotal alone.** *Symptom:* 99 credits flagged. *Response:* ask what they have in common.
- **Restocking errors.** *Symptom:* 17 lines. *Response:* ask what a line of less than one unit costs.
- **Delay from the receipt.** *Symptom:* 486 late applications. *Response:* ask which came first, receipt or invoice.
- **Deposits as lapping.** *Symptom:* 491 receipts flagged. *Response:* ask whose receipts they were.
- **A first-digit result as assurance.** *Symptom:* "conforms, so clean". *Response:* ask what chance alone would show.
- **An accusation.** *Symptom:* "diverted refund" as the finding. *Response:* ask what the records show.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Recomputation (S1 to S3) | 25 | Every credit traced, tolerance and rounding named | Counts without a tolerance |
| Restocking by reason | 15 | By reason and year, below-standard lines explained | Totals only |
| Lapping tests | 15 | Customer, deposit and application tests, deposits explained | One test |
| First-digit reasoning | 10 | Chapter 8's criteria, chance MAD | Run and reported |
| Timeline | 20 | Every step dated, with its document and role | Steps without roles |
| Disposition and evidence | 15 | Follow up, evidence listed, wording neutral | A conclusion |

## Extensions and discussion questions

- Build the same timeline for the next largest refund and compare the two.
- Test for a write-down: what record would show the damaged goods' value, and where would it live?
- Discuss: how would you word the finding on the largest refund for the committee?
- Discuss: lapping leaves a trace in the dates; which trace here is only a deposit, and what shows it?
