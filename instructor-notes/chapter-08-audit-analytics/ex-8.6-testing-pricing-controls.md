# Exercise 8.6: Testing Pricing Controls

| | |
|---|---|
| Unit | Chapter 8: Audit Analytics in Excel |
| Item | Exercise 8.6 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 135 minutes |
| Solution file | Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheets Ex 8.6 and Ex 8.6 Price Lists, with the queries Promotions, InvoiceLines, PendingOverrides, PriceLists, PriceListLines and OrderLines |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This exercise tests three pricing controls against the transactions: a promotion's dates against the order dates of its lines, an override request's status against the price billed, and a price list's dates against the lines that cite it. For every exception it asks whether the control was badly designed, badly operated or both. The analytics type is diagnostic.

By the end, students can:

- compare transactions with the approval records that govern them, and quantify what was billed outside an approval (outcome 5);
- build date-window flags guarded against blank dates (outcome 5);
- classify each exception as design, operation or both, and recommend fixes in the right place (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls) and ISC M2 (tests of internal controls, logical access and change management); IMA Reporting and Control (internal control); IFAC IES 2 (f) and (g); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3, with the Employees query. The exercise imports every other Table as a new query.
- **Data conditions.** The date test flags 3 promotions with reversed or one-day date windows, and none of their lines was ordered inside the recorded dates. The Pending override requests number 3, and the Expired price lists 3, with no successor.

## How to run it

Pairs, about 135 minutes, best over two sessions: 10 for requirement (1), 30 for (2), 20 for (3), 30 for (4), 15 for (5), 10 for (6) and 20 for the memo (7). Hold back the guard hint until a price-list count is far too large.

![The three flagged promotions, with the dates they were approved for and the months in which their lines were ordered.](../figures/chapter-08-audit-analytics/IF-08-6-A.pdf)

## Step-by-step solution

### Requirement (1): Promotions with reversed or one-day date windows

**Step 1. Flag the promotions.** Import **T7_PromotionProgram** as `Promotions`, merge the approver's name from the Employees query, add `EndOnOrBeforeStart` as `=[@EffectiveEndDate]<=[@EffectiveStartDate]` and list the flagged promotions with approver and approval date.

**Check:** 3 promotions: PROMO-2024-001 (Alder), PROMO-2025-004 (Brookside), PROMO-2026-007 (Harbor). They are the 8% collection promotions of each spring, approved by Carrie Schultz, the sales manager, on their start dates. Promotion 1 ends on its start date, which a policy could allow as a one-day promotion; the others end before they start.

### Requirement (2): Their invoice lines

**Step 2. Bring in the order dates.**

a. Import **T17_SalesInvoiceLine**, **T16_SalesInvoice** and **T9_SalesOrder** as `InvoiceLines`, `InvoiceHeaders` and `Orders`, and set Discount in InvoiceLines to **Decimal Number** with **Replace current**, as in Tutorial 4.1 Step 6, because Power Query can type it as a whole number and round the rates to 0.
b. Merge InvoiceLines with InvoiceHeaders on SalesInvoiceID, expand InvoiceNumber, InvoiceDate and SalesOrderID (Step 4 needs the number), merge with Orders on SalesOrderID and expand OrderDate, and merge with Promotions on PromotionID and expand the two effective dates.

**Step 3. Add the amount and the window test, and summarize.** Add `DiscountAmount` as `=[@Quantity]*[@UnitPrice]*[@Discount]` and `OrderedInWindow` as below, then count the lines and total the discount for each flagged promotion with COUNTIFS and SUMIFS.

```
=IF([@PromotionID]="","",AND([@OrderDate]>=[@EffectiveStartDate],[@OrderDate]<=[@EffectiveEndDate]))
```

**Check:** PROMO-2024-001, 80 lines and $28,124.77 of discount; PROMO-2025-004, 74 lines and $32,529.69 of discount; PROMO-2026-007, 68 lines and $30,478.57 of discount, all ordered outside the dates. No line of any other promotion was ordered outside its dates. **Watch for:** the type trap (a discount total of zero) and a strict inequality, which counts 81 lines of the other promotions, ordered on a start or end date, as outside their dates.

### Requirement (3): Pending overrides

**Step 4. Find the lines billed at a pending price.** The key is the order line, because the PriceOverrideApprovalID on these invoice lines is blank. Import **T8_PriceOverrideApproval** as `PendingOverrides`, filter Status to Pending and check that each SalesOrderLineID appears once. Match InvoiceLines.SalesOrderLineID to it and keep every matching invoice line, so request 165 keeps both of its shipments. List the request ID, SalesOrderLineID, InvoiceNumber, Quantity, UnitPrice, reference price, pending price, PricingMethod, recorded approval ID and the difference (Quantity times ReferenceUnitPrice less UnitPrice), and total the difference. The model answer spills them from A21 with one formula.

```
=LET(k,ISNUMBER(XMATCH(InvoiceLines[SalesOrderLineID],PendingOverrides[SalesOrderLineID])),sol,FILTER(InvoiceLines[SalesOrderLineID],k),q,FILTER(InvoiceLines[Quantity],k),p,FILTER(InvoiceLines[UnitPrice],k),ref,XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[ReferenceUnitPrice]),SORTBY(HSTACK(XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[PriceOverrideApprovalID]),sol,FILTER(InvoiceLines[InvoiceNumber],k),q,p,ref,XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[ApprovedUnitPrice]),FILTER(InvoiceLines[PricingMethod],k),FILTER(IF(InvoiceLines[PriceOverrideApprovalID]="","(blank)",InvoiceLines[PriceOverrideApprovalID]),k),(ref-p)*q),FILTER(InvoiceLines[InvoiceNumber],k),1))
=SUM(INDEX(A21#,0,10))
```

**Check:** 3 requests on four invoice lines, each billed at the pending ApprovedUnitPrice, under Segment Price List or Customer Price List and with a blank PriceOverrideApprovalID, $755.69 below the reference prices in total. Total the unrounded differences (755.6934) and format to cents, because rounding each request's subtotal first gives $755.68. The result is a billed-price difference from the reference, not a proven loss.

### Requirement (4): Price lists

**Step 5. Flag the lists and bring them to the order lines.** Import **T5_PriceList**, **T6_PriceListLine** and **T10_SalesOrderLine** as `PriceLists`, `PriceListLines` and `OrderLines`. In OrderLines, left-join PriceListLineID to PriceListLines (expand PriceListID and UnitPrice, renamed `ListUnitPrice` so that the line's UnitPrice is kept), PriceListID to PriceLists (expand EffectiveEndDate as `ListEndDate`) and SalesOrderID to Orders (expand OrderDate and CustomerID). Set the date types and check that the row count is still 22,269. The 239 lines with no price list line are a population the test cannot evaluate. Add `Flagged` to PriceLists, and `OrderYear` and `AfterListEnd` to OrderLines.

```
=OR([@Status]="Expired",[@EffectiveEndDate]<[@EffectiveStartDate])
=YEAR([@OrderDate])
=IF([@PriceListID]="",FALSE,[@OrderDate]>[@ListEndDate])
```

The guard's FALSE avoids a spurious comparison, and does not show that the line passed a pricing-control test.

**Step 6. Count by list and year.** On Ex 8.6 Price Lists put PriceListID in A10, 2024, 2025 and 2026 in B10:D10, Lines in E10 and Order value in F10, and the flagged list IDs (1, 2, 4) in A11:A13. Copy B11 across and down and E11:F11 down, and total the numeric columns in row 14. Then list the Active lists with no order lines.

```
B11 =COUNTIFS(OrderLines[PriceListID],$A11,OrderLines[OrderYear],B$10,OrderLines[AfterListEnd],TRUE)
E11 =SUM(B11:D11)
F11 =SUMIFS(OrderLines[LineTotal],OrderLines[PriceListID],A11,OrderLines[AfterListEnd],TRUE)
```

**Check:** 3 flagged lists, none with a later list for its segment, and 8,135 order lines after their list's end, with an order value of $31,004,051.07 (value, not a loss).

The counts by list and year are in the note below.

Three Active lists (12, 13, 14) copy list 3 and have no lines. **Watch for:** the guard left out. The 239 order lines with no price list line then count as after the end.

![Order lines dated after the end of their price list, by list and year, for the discussion of requirement 4.](../figures/chapter-08-audit-analytics/IF-08-6-B.pdf)

### Requirement (5): Customers with their own list

**Step 7. Compare the prices.** Among the customers with a list of ScopeType Customer, filter the order lines whose PricingMethod is neither Customer Price List nor Approved Override. Match each line's customer and ItemID to the customer's own list in PriceListLines, verifying that exactly one row applies. Segment lists carry quantity tiers, so a general lookup also applies the quantity and date rules. Retrieve the cited price by its exact PriceListLineID, never by the first row for a list and an item.

**Check:** three lines, all of customer 106, Richardson, Porter and Chavez (Strategic), which has its own list 11. They are order lines 368, 7675, 15031, recorded under Segment Price List and citing list 1 through its lines 44, 115, 164, while the customer's own list holds lines 2176, 2236, 2276. The UnitPrice equals the customer's own list and not the cited one (prices in the note below), so the record names the wrong list, and in 2025 and 2026 an expired one.

### Requirement (6): Design or operation

**Step 8. Classify each exception.**

| Exception | Design (provisional) | Operation (provisional) |
|---|---|---|
| Promotions with reversed or one-day date windows | A date check that is missing or inadequate | The discount was granted on every line ordered in the spring, possibly a bypassed date or wrong master data |
| Pending requests billed at their price | No link from a price to an approval, if the configuration confirms it | The requests are Pending, with blank approval fields in the extract, possibly an override or an incomplete extract |
| Expired lists cited | A date check that is missing or inadequate; one list ends before it starts | No successor to the segment lists in the extract |
| Active copies with no lines | Unused master data, whose purpose is the first question | None |
| Customer lists cited wrongly | No check that the cited list set the price, if the configuration confirms it | None |

Each exception could reflect a missing or inadequate control, an override, an operating failure or an incorrect extract. Ask for the approved campaign terms, the change history and the control configuration before classifying.

### Requirement (7): The memo

**Step 9. Outline the memo.** To the sales manager and the controller: a paragraph for each family of exception with its count and amount; the classification, marked provisional until the configuration and the pricing policy are seen; and recommendations (reject reversed dates and define whether a one-day promotion is allowed, block pricing from expired lists, allow an override price only after approval and link the approval to the line, confirm the purpose and owner of the unused copies and retire or correct them under the authorized master-data process, review setups each year).

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions flagged, and the approver | 3; Carrie Schultz | 1 |
| Lines and discount of the flagged promotions | 222; $91,133.03 | 3 |
| Pending requests, invoice lines and amount billed below reference | 3; four; $755.69 | 4 |
| Order lines after their list's end, and their order value | 8,135; $31,004,051.07 | 6 |

> **Instructor notes, Exercise 8.6:** promotions 1 (PROMO-2024-001, Alder Collection, effective 2024-03-01 to 2024-03-01), 4 (PROMO-2025-004, Brookside Collection, 2025-03-01 to 2025-02-27), and 7 (PROMO-2026-007, Harbor Collection, 2026-03-01 to 2026-02-28) are 8% collection promotions approved by EmployeeID 6 (Carrie Schultz, Sales Manager) on their start dates. All of their invoice lines were ordered outside the effective dates (both dates count as inside, so promotion 1, which ends on its start date, still covers none of its lines): 80 lines with discounts of 28,124.77, 74 lines with 32,529.69, and 68 lines with 30,478.57, a total of 222 lines and 91,133.03, ordered in March and April of each year and invoiced through July or August. Pending overrides: IDs 2, 165, and 294 on SalesOrderLineIDs 147, 8038, and 15033. They were billed on four invoice lines (SI-2024-000054; SI-2025-007015 and SI-2025-007598, two shipments of one order line; SI-2026-013958) at the pending ApprovedUnitPrice (181.00, 102.70, 351.24) under a price-list PricingMethod (Segment Price List or Customer Price List) with a blank PriceOverrideApprovalID, 755.69 below the reference prices in total. Price lists: 1 (Strategic segment, ends 2024-12-29), 2 (Wholesale, ends 2025-12-29), and 4 (Small Business, ends 2023-12-29, before its 2024-01-01 start) are Expired and have no successor, yet 8,135 order lines dated after their end dates cite them (31,004,051.07 of order value, not a loss): list 1 11 in late December 2024, 1,340 in 2025, and 1,200 in 2026; list 2 33 in late December 2025 and 3,710 in 2026; list 4 all 1,841 of its lines (550, 650, 641). Lists 12, 13, and 14, three Active copies of the Design Trade list named Overlap with the same dates as list 3, have no price list lines and price nothing. Customer lists: customer 106 (Richardson, Porter and Chavez, Strategic, list 11) has three order lines under Segment Price List that cite list 1: SalesOrderLineIDs 368 (2024-01-02), 7675 (2025-01-01), and 15031 (2026-01-02). Their UnitPrice equals the customer's own list (21.88, 913.83, 564.75), not list 1 (22.65, 946.08, 584.68): the order line carries the customer's contract price, but the record names the wrong, and in 2025 and 2026 expired, list. No other customer with its own list has Segment Price List lines. The classification stays provisional until the system's configuration, the approval history and the pricing policy are seen. The extract shows end dates on or before start dates, order lines carrying a pending price, and lines citing expired lists, and it shows no check that stopped them. That could reflect a missing or inadequate control (a possible design weakness), an override or a control not followed (a possible operating failure), or an incorrect extract, and the cause is not established from these records.

## What a strong answer says

- **Requirement (2).** The counts and discount of the flagged promotions, every line ordered outside the dates, and the reading that the discounts may have been intended while the recorded dates do not authorize them.
- **Requirement (6).** Each exception placed in design, operation or both with the reason and the evidence that would confirm it, marked provisional.
- **Requirement (7).** Amounts on each finding, an order value described as value and not loss, and fixes placed in the system with a periodic review as the detective control.

A weak answer reports the exceptions as losses, blames individuals, or recommends retraining where the system accepted an impossible date.

## Common mistakes and how to respond

- **The type trap.** *Symptom:* a discount total of zero. *Response:* ask what Power Query did to the Discount column.
- **No guard on blank dates.** *Symptom:* about 239 extra lines after a list's end. *Response:* ask what an empty date compares as.
- **A strict inequality in the window.** *Symptom:* lines on the boundary dates counted outside. *Response:* ask whether the end date is inside the promotion.
- **Value read as loss.** *Symptom:* "$31,004,051.07 lost". *Response:* ask what the lines show about price, not revenue.
- **Pending read as approved.** *Symptom:* the requests are listed as overrides. *Response:* ask what Status says.
- **Everything is "operation".** *Symptom:* retraining as the only fix. *Response:* ask whether the system would have accepted the record.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: promotions | 10 | Flag, list, approver and date | List without approver |
| Requirement 2: lines of the flagged promotions | 20 | Order dates, window test, counts and discount | Counts without the amount |
| Requirement 3: pending overrides | 15 | Lines found, prices compared, amount below reference | Lines without the amount |
| Requirement 4: price lists | 20 | Flags with guard, counts by list and year, unused lists | Counts without the guard |
| Requirement 5: customer lists | 10 | Lines found, both comparisons, explanation | Lines without comparison |
| Requirement 6: design or operation | 10 | Every exception placed with a reason | Placed without reasons |
| Requirement 7: memo | 15 | Findings, amounts, provisional classification, fixes | Fixes missing |

## Extensions and discussion questions

- Discuss: the flagged promotions were approved on their start dates. What control would have caught the dates then?
- Discuss: is an expired list that still prices correctly a data problem or a control problem?
