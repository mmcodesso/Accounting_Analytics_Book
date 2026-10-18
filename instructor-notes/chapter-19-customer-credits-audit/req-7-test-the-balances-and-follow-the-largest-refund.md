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

Requirement 4 tested the controls; this one tests the amounts. A substantive test asks whether a balance is right, and sharing a population with a control test does not make its result evidence for the other. Students recompute every credit from its sources, value the restocked goods, test for lapping, and follow the largest refund. The analytics type is diagnostic. SQL fits the recomputation and lapping tests; Excel fits the timeline the committee reads.

Students can recompute a document from its sources (Part 1), value restocked goods (Part 2), test lapping and explain a first-digit test's limits (Part 3), and build a timeline worded as what the records show (Part 4).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Reporting and Control (internal control); IFAC IES 2 (f) and IES 4 (a); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite and Credits.sql. Before this requirement, load the Refunds, Credits and ReturnLines Tables with the case note's build contract, or open the model workbook: Requirement 4's SQL output alone does not create these Excel Tables.
- **Data conditions.** Stored LineTotal values are rounded, so a tolerance is a decision. Credits with freight carry tax on the freight. Receipts can arrive before their invoice.
- **Verify first.** Run S1 to S6: each returns at once, S1 and S5 one row, S3 3 rows, S6 10.

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

**Check:** 637 of 637 lines traced, none above the quantity shipped or returned, none returned twice, none off the invoice's price or discount, and 1 stored total one cent off SQLite's rounded result at an exact half-cent tie (credit line 84: exact product 495.405, stored 495.41, ROUND 495.40); rounded half up, credit lines 248, 290, 626 differ instead. State the rounding convention and document the differences, none an error. **Watch for:** the stored total compared with the unrounded product at a tolerance below half a cent, which flags 88 lines.

**Step 2. Recompute every credit against its original invoice (S2).** Join each credit to its original invoice and first corroborate that the invoice's tax is 6.5% of its SubTotal plus freight, rounded to cents, reporting any invoice that does not agree. Then test the credit's tax at that rate on the credit's subtotal plus freight credited.

```sql
SUM(CASE WHEN ABS(InvoiceTax - ROUND((InvoiceSubTotal + InvoiceFreight)
        * (SELECT TaxRate FROM Rate), 2)) > 0.005 THEN 1 ELSE 0 END)
        AS InvoiceTaxOff,
```

**Check:** 612 credits on as many invoices; InvoiceTaxOff is zero (a changed invoice tax would show there) and tax at 6.5% holds on every credit; none above its invoice, each subtotal equal to its lines, no freight credit above the invoice's. The credits' own effective rate is only a diagnostic, and the rate and taxability need the approved policy before a conclusion on legal correctness. The freight test is an upper bound, so the answer asks for the freight policy. **Watch for:** tax tested on the subtotal alone, which flags 99 credits, exactly those with freight.

**Step 3. List the open items in 2060 (S3).** The credits whose part posted to 2060 is not refunded by the last year-end.

**Check:** 3 credits, CM-2026-000583 ($1,503.06); CM-2026-000605 ($912.97); CM-2026-000607 ($997.43), adding up to the account's balance at the year-end.

### Part 2: Measure the restocking by reason (S4)

**Step 4. Group the return lines by reason and year (S4, complete in Credits.sql).** The query adds each line's recorded cost and compares it with quantity times the item's standard cost.

**Check:** goods returned Damaged went back at $77,248.17 over the three years, and with Quality Concern $61,146.00 in the last year; no account writes them down. These are gross flows, not the inventory still held: a valuation follow-up. **Watch for:** 17 complete returns of shipment lines below one unit are recorded at the quantity times the shipment line's already extended cost, $547.29 below quantity times the item's unit standard cost, including $175.48 for Damaged or Quality Concern goods. Reconcile the recorded amounts, list the differences apart and obtain the costing policy. The pattern explains how the records were produced, not that the valuation is correct.

### Part 3: Test for lapping, and explain the first-digit test (S5)

**Step 5. Test receipts against invoices, deposits and applications (S5, complete in Credits.sql).** One row of subqueries, the first of which compares the customer on the receipt with the customer on the invoice.

**Check:** no application to another customer's invoice, short delays, every receipt fully applied. 491 receipts ($395,196.29) were applied to invoices dated after them: deposits held in 2060, not lapping, as far as these tests reach. **Watch for:** either delay shown alone. The raw delay, up to 28 days on 486 applications, is the observation, and receipts dated before their invoice explain it.

**Step 6. Explain why a first-digit test is not established as suitable for these populations.** Use Chapter 8's criteria for populations that suit the test: the credits and refunds are event-selected reversals of invoice amounts, so their amounts follow the invoice lines they reverse and a conformity test has no basis here.

**Check:** the suitability argument and its limits earn the credit; the chance-MAD comparison in the note is an untaught, optional extension. **Watch for:** the result read as assurance or as a finding.

### Part 4: Follow the largest refund (S6 and the Timeline sheet)

**Step 7. Build the steps in date order (S6, complete in Credits.sql).** The query stacks one step for each document with its date, a step order and who did it, and sorts by date, step order and document. Joined from the invoice's lines, the shipment would repeat; DISTINCT stops that.

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

**Check:** RF-2025-000097, $17,745.96, the largest refund, of the largest credit; $13,081.41 of the invoice was unpaid on the refund date. The disposition is follow up, not a conclusion, with the evidence the note lists. **Watch for:** the Sunday read as evidence. Weekend dates hold 62 of the 222 refunds, about the share of the week they are.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Lines traced; one-cent differences from SQLite at a half-cent tie | 637 of 637; 1 | 1 |
| Credits recomputed; tax rate; credits with freight | 612; 6.5%; 99 | 2 |
| Damaged restocked; Damaged and Quality Concern, last year | $77,248.17; $61,146.00 | 4 |
| Receipts applied before their invoice; amount | 491; $395,196.29 | 5 |
| Largest refund; unpaid on its invoice | $17,745.96; $13,081.41 | 8 |

> **Instructor notes, Requirement 7:** substantive tests clean on the recorded documents: 637 of 637 credit lines trace to their return, shipment, and invoice lines; no quantity above shipped, credited quantity equal to the returned quantity on every line, and no shipment line returned twice; price and discount equal the invoice line's; LineTotal = ROUND(Q x P x (1 - D), 2) except a one-cent difference on credit line 84 caused by an exact half-cent tie (line 84: exact product 495.405, stored 495.41, SQLite's ROUND 495.40), while by exact decimal half up lines 248, 290, 626 are a cent lower instead: rounding differences, not errors, to document with the convention stated; 612 credits on 612 distinct invoices, none above its invoice; SubTotal = the lines; each credit is joined to its original invoice, whose tax is first corroborated at 6.5% of its SubTotal plus freight (all 612 original invoices agree within half a cent), and then the credit's tax = 6.5% of (SubTotal + freight credit) on all 612 (SubTotal alone falsely flags the 99 credits with freight); the credits' own effective rate is a diagnostic that agrees, and the rate's legal correctness needs the approved policy; no freight credit above the invoice's freight, an upper bound rather than a recomputation, since nothing in the records says how freight is credited on a partial return, so the answer reports that limit and asks for the policy. Restocked at standard cost, except 17 return lines of less than one unit, costed at the quantity times the shipment line's extended cost (547.29 below quantity x unit standard cost, 175.48 of it Damaged and Quality Concern; return line 115 of SR-2024-000108 returns all 0.10 units at 184.00 a unit, which proportionate costing reverses at 18.40, and it is recorded at 1.84): the pattern explains how the records were produced, not that the valuation is right, so reconcile, list the differences apart, ask which field is a unit cost and which an extended cost, and obtain the costing policy; it is neither rounding nor, by itself, a misstatement of the stock still held: Damaged 77,248.17 (11,606.17 / 25,617.84 / 40,024.16) and Damaged plus Quality Concern 137,606.43 (2026: 61,146.00): a valuation follow-up. Lapping clean: no application to another customer's invoice; deposits 0-2 days after receipt; applications 0-28 days after their receipt, the 486 over two days all of receipts dated before their invoice, and every application within 2 days of the later of receipt and invoice date; every receipt fully applied; 491 receipts (526 applications, 395,196.29) were applied to invoices dated after the receipt, deposits held in 2060, not lapping, as far as these tests reach. First digits: these event-selected reversals of invoice amounts are not established as suitable for a Benford conformity test (Chapter 8's criteria; grade the suitability argument and its limits). An untaught, optional extension: by chance alone 222 refunds that followed the law would show a MAD near 0.0158 (actual 0.0119), 612 credits 0.0095 (actual 0.0105). Timeline: SH-2025-004100 shipped 2025-04-27 (FedEx Freight), delivered 04-30; SI-2025-008932 dated 04-30, 18,774.16, due 06-14 (customer 128); CR-2025-003258 05-17, check, 5,692.75 applied (recorded and applied by the Customer Service Manager); SR-2025-000255 06-06, Damaged (15.71 of 15.71 FUR-DSK-0071; 2.62 of 6.86 FUR-CTB-0045), received by a Shipping Clerk; CM-2025-000255 06-09, 17,745.96, the largest credit of the three years, approved by representative 115 with a limit of 0, all to 2060 while 13,081.41 of the invoice was unpaid; clawbacks SCAJ-2025-000268/269 (321.33 and 11.93); RF-2025-000097 06-15, a Sunday, wire, approved by the Accounting Manager (within the 25,000 limit), cleared 06-18; CR-2025-003473 06-17, check, 9,891.91 applied (recorded and applied on 06-19 by the Customer Service Manager); CR-2025-003342 06-18, check, 3,189.50 applied (recorded by representative 97, applied on 06-19 by representative 115, the credit's approver); the invoice was settled on 06-19. Disposition: follow up, not a conclusion. Evidence: the wire confirmation's beneficiary and account against the customer's known bank details; a confirmation from the customer of the credit and the refund; the receiving and inspection record and any carrier claim; the customer's written request; why the refund went by wire to a customer who paid this invoice by check, and why before its checks arrived.

## What a strong answer says

- **Each recomputation states its tolerance and names the rounding,** and finds no error.
- **Restocking is a flow at standard cost with no write-down,** a valuation follow-up with the lines below proportionate cost listed apart.
- **The lapping tests are stated, and the deposits are explained.**
- **The first-digit test is reasoned about with Chapter 8's criteria,** not run and believed.
- **The timeline gives each step a date, a document and a role,** and the disposition is follow up with the evidence that would settle it.

A weak answer reports the rounding as errors, reads the deposits as lapping, or words the timeline as an accusation.

## Common mistakes and how to respond

- **The unrounded product.** *Symptom:* 88 lines "wrong". *Response:* ask what the stored total is rounded to.
- **Tax on the subtotal alone.** *Symptom:* 99 credits flagged. *Response:* ask what they have in common.
- **Restocking errors or rounding.** *Symptom:* 17 lines called errors, or rounding. *Response:* ask which field is a unit cost and which an extended cost. A complete return of 0.10 units at 184.00 a unit would reverse 18.40 under proportionate costing, and 1.84 needs an explanation. Do not change the data or dismiss the gap.
- **Delay from the receipt.** *Symptom:* 486 late applications. *Response:* ask which came first, receipt or invoice.
- **Deposits as lapping.** *Symptom:* 491 receipts flagged. *Response:* ask whose receipts they were.
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
