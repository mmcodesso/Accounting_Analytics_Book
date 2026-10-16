# Exercise 8.6: Testing Pricing Controls

| | |
|---|---|
| Unit | Chapter 8: Audit Analytics in Excel |
| Item | Exercise 8.6 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 135 minutes |
| Solution file | Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheets Ex 8.6 and Ex 8.6 Price Lists, with the queries Promotions, InvoiceLines, PendingOverrides, PriceLists, PriceListLines and OrderLines |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Exercise 4.6 found override requests still recorded as Pending, and the promotion analyses of Chapters 4 to 6 used effective dates without testing them. This exercise tests three pricing controls against the transactions: a promotion's dates against the order dates of its lines, an override request's status against the price billed, and a price list's dates against the lines that cite it. It ends by asking, for every exception, whether the control was badly designed, badly operated or both. The analytics type is diagnostic.

By the end, students can:

- compare transactions with the approval records that should govern them (outcome 5);
- build date-window flags and guard them against blank dates (outcome 5);
- quantify what was billed outside an approval (outcome 5);
- classify each exception as design, operation or both, and recommend fixes in the right place (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls) and ISC M2 (tests of internal controls, logical access and change management); IMA Reporting and Control (internal control); IFAC IES 2 (f) and (g); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3, with the Employees query. The exercise imports every other Table as a new query.
- **The type trap.** Power Query can type SalesInvoiceLine.Discount as a whole number and round the rates to 0. Send a student whose discounts total zero to **Replace current** in the Changed Type step, as in Tutorial 4.1 Step 6.
- **Data conditions.** The date test flags 3 promotions, and all of their lines were ordered outside the recorded dates. The Pending override requests number 3, and the Expired price lists 3, with no successor. The 22,269 order lines include 239 with no price list line.

## How to run it

Pairs, about 135 minutes, best over two sessions: 10 for requirement (1), 30 for (2), 20 for (3), 30 for (4), 15 for (5), 10 for (6) and 20 for the memo (7). Hold back the guard hint until a price-list count is far too large. Collect the workbook and the memo.

![The three flagged promotions, with the dates they were approved for and the months in which their lines were ordered.](../figures/chapter-08-audit-analytics/IF-08-6-A.pdf)

## Step-by-step solution

### Requirement (1): Promotions with impossible dates

**Step 1. Flag the promotions.** Import **T7_PromotionProgram** as `Promotions`, merge the approver's name from the Employees query (or look it up), add `EndOnOrBeforeStart` as `=[@EffectiveEndDate]<=[@EffectiveStartDate]` and list the flagged promotions with approver and approval date.

**Check:** 3 promotions: PROMO-2024-001 (Alder), PROMO-2025-004 (Brookside), PROMO-2026-007 (Harbor). They are the 8% collection promotions of each spring, approved by Carrie Schultz, the sales manager, on their start dates. Promotion 1 ends on its start date; the others end before they start.

### Requirement (2): Their invoice lines

**Step 2. Bring in the order dates.**

a. Import **T17_SalesInvoiceLine**, **T16_SalesInvoice** and **T9_SalesOrder** as `InvoiceLines`, `InvoiceHeaders` and `Orders`, and set Discount in InvoiceLines to **Decimal Number** with **Replace current**.
b. Merge InvoiceLines with InvoiceHeaders on SalesInvoiceID, expand InvoiceDate and SalesOrderID, merge with Orders on SalesOrderID and expand OrderDate, and merge with Promotions on PromotionID and expand the two effective dates.

**Step 3. Add the amount and the window test, and summarize.** Add `DiscountAmount` as `=[@Quantity]*[@UnitPrice]*[@Discount]` and `OrderedInWindow` as below, then count the lines and total the discount for each flagged promotion with COUNTIFS and SUMIFS.

```
=IF([@PromotionID]="","",AND([@OrderDate]>=[@EffectiveStartDate],[@OrderDate]<=[@EffectiveEndDate]))
```

**Check:**

- PROMO-2024-001: 80 lines and $28,124.77 of discount, all ordered outside the dates.
- PROMO-2025-004: 74 lines and $32,529.69 of discount, all ordered outside the dates.
- PROMO-2026-007: 68 lines and $30,478.57 of discount, all ordered outside the dates.

Together 222 lines and $91,133.03, ordered in March and April and invoiced through July or August. No line of any other promotion was ordered outside its dates. Both end dates count as inside, so the one-day promotion's lines would count if any had been ordered that day. **Watch for:** the type trap (a discount total of zero) and a strict inequality, which counts 81 lines of the other promotions, ordered on a start or end date, as outside their dates.

### Requirement (3): Pending overrides

**Step 4. Find the lines billed at a pending price.** Import **T8_PriceOverrideApproval** as `PendingOverrides`, filtered to Pending. List the InvoiceLines whose SalesOrderLineID is in it, show UnitPrice beside the request's ReferenceUnitPrice and ApprovedUnitPrice, add PricingMethod and PriceOverrideApprovalID, and total the amount billed below the reference (in the model answer the list spills from A21).

```
=SUM(INDEX(A21#,0,10))
```

**Check:** 3 requests on four invoice lines, each billed at the pending ApprovedUnitPrice, under Segment Price List or Customer Price List and with a blank PriceOverrideApprovalID, $755.69 below the reference prices in total. An order line shipped in two parts has two invoice lines.

### Requirement (4): Price lists

**Step 5. Flag the lists and their lines.**

a. Import **T5_PriceList**, **T6_PriceListLine** and **T10_SalesOrderLine** as `PriceLists`, `PriceListLines` and `OrderLines`. Add `Flagged` to PriceLists as `=OR([@Status]="Expired",[@EffectiveEndDate]<[@EffectiveStartDate])`.
b. In OrderLines merge PriceListLines (PriceListID) and PriceLists (the list's EffectiveEndDate), then Orders (OrderDate and CustomerID). Add `OrderYear` as `=YEAR([@OrderDate])` and `AfterListEnd`.

```
=IF([@PriceListID]="",FALSE,[@OrderDate]>[@ListEndDate])
```

**Step 6. Count by list and year.** Use COUNTIFS on the list, the year and AfterListEnd, and list the Active lists with no order lines.

**Check:** 3 flagged lists, none with a later list for its segment, and 8,135 order lines after their list's end, with an order value of $31,004,051.07 (value, not a loss).

- List 1: 11 in 2024, 1,340 in 2025, 1,200 in 2026.
- List 2: 33 in 2025, 3,710 in 2026.
- List 4: 550 in 2024, 650 in 2025, 641 in 2026.

Three Active lists (12, 13, 14) copy list 3 and have no lines. **Watch for:** the guard left out. The 239 order lines with no price list line then count as after the end, because an empty date is earlier than any date.

![Order lines dated after the end of their price list, by list and year, for the discussion of requirement 4.](../figures/chapter-08-audit-analytics/IF-08-6-B.pdf)

### Requirement (5): Customers with their own list

**Step 7. Compare the prices.** Among the customers with a list of ScopeType Customer, filter the order lines whose PricingMethod is neither Customer Price List nor Approved Override. Look up each line's price on the customer's own list and on the list it cites, and compare.

**Check:** three lines, all of customer 106, Richardson, Porter and Chavez (Strategic), which has its own list 11. They are recorded under Segment Price List and cite list 1. The UnitPrice equals the customer's own list ($21.88, $913.83, $564.75) and not the cited list ($22.65, $946.08, $584.68). The price is the contract price; the record names the wrong list, and in 2025 and 2026 an expired one.

### Requirement (6): Design or operation

**Step 8. Classify each exception.**

| Exception | Design (provisional) | Operation (provisional) |
|---|---|---|
| Promotions with end dates on or before their start dates | The records show no date check | The discount was granted on every line ordered in the spring |
| Pending requests billed at their price | The records show no link from a price to an approval | The requests are Pending, with blank approval fields in the extract |
| Expired lists cited | No date check in the records, and one list ends before it starts | No successor to the segment lists in the extract |
| Active copies with no lines | Unused master data, whose purpose is the first question | None |
| Customer lists cited wrongly | The records show no check that the cited list set the price | None |

Promotion 1's end date equals its start date, as a one-day promotion would, so only the date policy can make that record invalid. Each classification waits for the system's configuration, the approval history and the pricing policy.

### Requirement (7): The memo

**Step 9. Outline the memo.** To the sales manager and the controller: a paragraph for each family of exception with its count and amount; the classification marked provisional until the configuration and the pricing policy are seen; and recommendations (reject reversed dates and define whether a one-day promotion is allowed, block pricing from expired lists, allow an override price only after approval and link the approval to the line, remove the unused copies, review setups each year).

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions flagged, and the approver | 3; Carrie Schultz | 1 |
| Lines and discount of the flagged promotions | 222; $91,133.03 | 3 |
| Pending requests, invoice lines and amount billed below reference | 3; four; $755.69 | 4 |
| Order lines after their list's end, and their order value | 8,135; $31,004,051.07 | 6 |
| Active lists with no lines | 12, 13, 14 | 6 |
| Customer-list lines priced another way | three | 7 |

> **Instructor notes, Exercise 8.6:** promotions 1 (PROMO-2024-001, Alder Collection, effective 2024-03-01 to 2024-03-01), 4 (PROMO-2025-004, Brookside Collection, 2025-03-01 to 2025-02-27), and 7 (PROMO-2026-007, Harbor Collection, 2026-03-01 to 2026-02-28) are 8% collection promotions approved by EmployeeID 6 (Carrie Schultz, Sales Manager) on their start dates. All of their invoice lines were ordered outside the effective dates (both dates count as inside, and promotion 1, which ends on its start date and could be a one-day promotion, still covers none of its lines): 80 lines with discounts of 28,124.77, 74 lines with 32,529.69, and 68 lines with 30,478.57, a total of 222 lines and 91,133.03, ordered in March and April of each year and invoiced through July or August. Every line of the other promotions was ordered within its dates. Pending overrides: IDs 2, 165, and 294 on SalesOrderLineIDs 147, 8038, and 15033. They were billed on four invoice lines (SI-2024-000054; SI-2025-007015 and SI-2025-007598, two shipments of one order line; SI-2026-013958) at the pending ApprovedUnitPrice (181.00, 102.70, 351.24) under a price-list PricingMethod (Segment Price List or Customer Price List) with a blank PriceOverrideApprovalID, 755.69 below the reference prices in total. Price lists: 1 (Strategic segment, ends 2024-12-29), 2 (Wholesale, ends 2025-12-29), and 4 (Small Business, ends 2023-12-29, before its 2024-01-01 start) are Expired and have no successor, yet 8,135 order lines dated after their end dates cite them (31,004,051.07 of order value, not a loss): list 1 11 in late December 2024, 1,340 in 2025, and 1,200 in 2026; list 2 33 in late December 2025 and 3,710 in 2026; list 4 all 1,841 of its lines (550, 650, 641). Lists 12, 13, and 14, three Active copies of the Design Trade list named Overlap with the same dates as list 3, have no price list lines and price nothing. Customer lists: customer 106 (Richardson, Porter and Chavez, Strategic, list 11) has three order lines under Segment Price List that cite list 1: SalesOrderLineIDs 368 (2024-01-02), 7675 (2025-01-01), and 15031 (2026-01-02). Their UnitPrice equals the customer's own list (21.88, 913.83, 564.75), not list 1 (22.65, 946.08, 584.68): the order line carries the customer's contract price, but the record names the wrong, and in 2025 and 2026 expired, list. No other customer with its own list has Segment Price List lines. The classification stays provisional until the system's configuration, the approval history and the pricing policy are seen. The records hold end dates on or before start dates, order lines carrying a pending price, and lines citing expired lists, with no check in the records that would stop them (a possible design weakness), and the approvals did not stop the discounts while the segment lists have no successor in the extract (a possible operating failure).

## What a strong answer says

- **Requirement (2).** The counts and discount of the flagged promotions, every line ordered outside the dates, and the reading that the discounts may have been intended while the recorded dates do not authorize them, so the approved campaign terms are the evidence to request.
- **Requirement (6).** Each exception placed in design, operation or both with the reason and the evidence that would confirm it, marked provisional.
- **Requirement (7).** Amounts on each finding, an order value described as value and not loss, and fixes placed in the system with a periodic review as the detective control.

A weak answer reports the exceptions as losses, blames individuals, or recommends retraining where the system accepted an impossible date.

## Common mistakes and how to respond

- **The type trap.** *Symptom:* a discount total of zero. *Response:* ask what Power Query did to the Discount column.
- **No guard on blank dates.** *Symptom:* about 239 extra lines after a list's end. *Response:* ask what an empty date compares as.
- **A strict inequality in the window.** *Symptom:* lines on the boundary dates counted outside. *Response:* ask whether the end date is inside the promotion.
- **Value read as loss.** *Symptom:* "$31,004,051.07 lost". *Response:* ask what the lines show about price, not revenue.
- **Pending read as approved.** *Symptom:* the requests are listed as overrides without a flag. *Response:* ask what Status says.
- **Customer lines left out.** *Symptom:* no finding for requirement (5). *Response:* ask which customers have their own list.
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

- Compare each flagged promotion's discount with the discount the budget planned for the same months.
- Discuss: the flagged promotions were approved on their start dates. What control would have caught the dates then?
- Discuss: is an expired list that still prices correctly a data problem or a control problem?
