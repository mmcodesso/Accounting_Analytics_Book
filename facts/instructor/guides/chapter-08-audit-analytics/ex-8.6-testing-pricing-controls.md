---
note: ch08.ex6
uses: [ch08.g6]
title: Testing Pricing Controls
kind: exercise
number: '8.6'
unit: '8'
perspective: auditing
tool: excel
minutes: 135
solution: "Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheets Ex 8.6 and Ex 8.6 Price Lists, with the queries Promotions, InvoiceLines, PendingOverrides, PriceLists, PriceListLines and OrderLines"
figures:
  - id: IF-08-6-A
    kind: diagram
    purpose: The three flagged promotions, with the dates they were approved for and the months in which their lines were ordered.
    shows: "A timeline with a row for each flagged promotion. A short outlined segment marks the recorded effective window (a point for the one-day promotion, a backward arrow for the other two). A solid bar marks the months in which its lines were ordered, and a lighter bar extends to the last month in which they were invoiced."
    data: PromotionProgram and the order and invoice dates of its invoice lines (the Expected results table).
  - id: IF-08-6-B
    kind: chart
    purpose: Order lines dated after the end of their price list, by list and year, for the discussion of requirement 4.
    shows: "A clustered column chart with a group for each expired price list and a column for each fiscal year, counting order lines. Each group is labeled with the list's end date."
    data: SalesOrderLine, PriceListLine, PriceList and SalesOrder, counted by list and year (the Expected results table).
---
{% set x = ch08_g6 %}
# Exercise 8.6: Testing Pricing Controls

{{ header() }}

## Purpose and learning outcomes

This exercise tests three pricing controls against the transactions: a promotion's dates against the order dates of its lines, an override request's status against the price billed, and a price list's dates against the lines that cite it. For every exception it asks whether the control was badly designed, badly operated or both. The analytics type is diagnostic.

By the end, students can:

- compare transactions with the approval records that govern them, and quantify what was billed outside an approval (outcome 5);
- build date-window flags guarded against blank dates (outcome 5);
- classify each exception as design, operation or both, and recommend fixes in the right place (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls) and ISC M2 (tests of internal controls, logical access and change management); IMA Reporting and Control (internal control); IFAC IES 2 (f) and (g); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3, with the Employees query. The exercise imports every other Table as a new query.
- **Data conditions.** The date test flags {{ flagged|length }} promotions with reversed or one-day date windows, and none of their lines was ordered inside the recorded dates. The Pending override requests number {{ x.n_pending }}, and the Expired price lists {{ expired|length }}, with no successor.

## How to run it

Pairs, about 135 minutes, best over two sessions: 10 for requirement (1), 30 for (2), 20 for (3), 30 for (4), 15 for (5), 10 for (6) and 20 for the memo (7). Hold back the guard hint until a price-list count is far too large.

{{ figure('IF-08-6-A') }}

## Step-by-step solution

### Requirement (1): Promotions with reversed or one-day date windows

**Step 1. Flag the promotions.** Import **T7_PromotionProgram** as `Promotions`, merge the approver's name from the Employees query, add `EndOnOrBeforeStart` as `=[@EffectiveEndDate]<=[@EffectiveStartDate]` and list the flagged promotions with approver and approval date.

**Check:** {{ flagged|length }} promotions: {% for p in flagged %}{{ p.code }} ({{ p.collection }}){% if not loop.last %}, {% endif %}{% endfor %}. They are the {{ pct|pct(0) }} collection promotions of each spring, approved by {{ approver.name }}, the {{ approver.title|lower }}, on their start dates. Promotion {{ same_day|join(', ') }} ends on its start date, which a policy could allow as a one-day promotion; the others end before they start.

### Requirement (2): Their invoice lines

**Step 2. Bring in the order dates.**

a. Import **T17_SalesInvoiceLine**, **T16_SalesInvoice** and **T9_SalesOrder** as `InvoiceLines`, `InvoiceHeaders` and `Orders`, and set Discount in InvoiceLines to **Decimal Number** with **Replace current**, as in Tutorial 4.1 Step 6, because Power Query can type it as a whole number and round the rates to 0.
b. Merge InvoiceLines with InvoiceHeaders on SalesInvoiceID, expand InvoiceNumber, InvoiceDate and SalesOrderID (Step 4 needs the number), merge with Orders on SalesOrderID and expand OrderDate, and merge with Promotions on PromotionID and expand the two effective dates.

**Step 3. Add the amount and the window test, and summarize.** Add `DiscountAmount` as `=[@Quantity]*[@UnitPrice]*[@Discount]` and `OrderedInWindow` as below, then count the lines and total the discount for each flagged promotion with COUNTIFS and SUMIFS.

```
=IF([@PromotionID]="","",AND([@OrderDate]>=[@EffectiveStartDate],[@OrderDate]<=[@EffectiveEndDate]))
```

**Check:** {% for p in flagged %}{{ p.code }}, {{ flagged_lines[loop.index0].n }} lines and ${{ flagged_lines[loop.index0].discount|money }} of discount{% if not loop.last %}; {% endif %}{% endfor %}, all ordered outside the dates. No line of any other promotion was ordered outside its dates. **Watch for:** the type trap (a discount total of zero) and a strict inequality, which counts {{ x.boundary|count }} lines of the other promotions, ordered on a start or end date, as outside their dates.

### Requirement (3): Pending overrides

**Step 4. Find the lines billed at a pending price.** The key is the order line, because the PriceOverrideApprovalID on these invoice lines is blank. Import **T8_PriceOverrideApproval** as `PendingOverrides`, filter Status to Pending and check that each SalesOrderLineID appears once. Match InvoiceLines.SalesOrderLineID to it and keep every matching invoice line, so request {{ x.shipped_twice[0] }} keeps both of its shipments. List the request ID, SalesOrderLineID, InvoiceNumber, Quantity, UnitPrice, reference price, pending price, PricingMethod, recorded approval ID and the difference (Quantity times ReferenceUnitPrice less UnitPrice), and total the difference. The model answer spills them from A21 with one formula.

```
=LET(k,ISNUMBER(XMATCH(InvoiceLines[SalesOrderLineID],PendingOverrides[SalesOrderLineID])),sol,FILTER(InvoiceLines[SalesOrderLineID],k),q,FILTER(InvoiceLines[Quantity],k),p,FILTER(InvoiceLines[UnitPrice],k),ref,XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[ReferenceUnitPrice]),SORTBY(HSTACK(XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[PriceOverrideApprovalID]),sol,FILTER(InvoiceLines[InvoiceNumber],k),q,p,ref,XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[ApprovedUnitPrice]),FILTER(InvoiceLines[PricingMethod],k),FILTER(IF(InvoiceLines[PriceOverrideApprovalID]="","(blank)",InvoiceLines[PriceOverrideApprovalID]),k),(ref-p)*q),FILTER(InvoiceLines[InvoiceNumber],k),1))
=SUM(INDEX(A21#,0,10))
```

**Check:** {{ x.n_pending }} requests on {{ billed }} invoice lines, each billed at the pending ApprovedUnitPrice, under {{ methods|join(' or ') }} and with a blank PriceOverrideApprovalID, ${{ below|money }} below the reference prices in total. Total the unrounded differences ({{ x.below_exact|num(4) }}) and format to cents, because rounding each request's subtotal first gives ${{ x.below_by_request|money }}. The result is a billed-price difference from the reference, not a proven loss.

### Requirement (4): Price lists

**Step 5. Flag the lists and bring them to the order lines.** Import **T5_PriceList**, **T6_PriceListLine** and **T10_SalesOrderLine** as `PriceLists`, `PriceListLines` and `OrderLines`. In OrderLines, left-join PriceListLineID to PriceListLines (expand PriceListID and UnitPrice, renamed `ListUnitPrice` so that the line's UnitPrice is kept), PriceListID to PriceLists (expand EffectiveEndDate as `ListEndDate`) and SalesOrderID to Orders (expand OrderDate and CustomerID). Set the date types and check that the row count is still {{ x.order_lines|count }}. The {{ x.no_list|count }} lines with no price list line are a population the test cannot evaluate. Add `Flagged` to PriceLists, and `OrderYear` and `AfterListEnd` to OrderLines.

```
=OR([@Status]="Expired",[@EffectiveEndDate]<[@EffectiveStartDate])
=YEAR([@OrderDate])
=IF([@PriceListID]="",FALSE,[@OrderDate]>[@ListEndDate])
```

The guard's FALSE avoids a spurious comparison, and does not show that the line passed a pricing-control test.

**Step 6. Count by list and year.** On Ex 8.6 Price Lists put PriceListID in A10, {{ d.F }}, {{ d.P }} and {{ d.C }} in B10:D10, Lines in E10 and Order value in F10, and the flagged list IDs ({% for pl in per_list %}{{ pl.id }}{{ ', ' if not loop.last }}{% endfor %}) in A11:A13. Copy B11 across and down and E11:F11 down, and total the numeric columns in row 14. Then list the Active lists with no order lines.

```
B11 =COUNTIFS(OrderLines[PriceListID],$A11,OrderLines[OrderYear],B$10,OrderLines[AfterListEnd],TRUE)
E11 =SUM(B11:D11)
F11 =SUMIFS(OrderLines[LineTotal],OrderLines[PriceListID],A11,OrderLines[AfterListEnd],TRUE)
```

**Check:** {{ expired|length }} flagged lists, none with a later list for its segment, and {{ after|count }} order lines after their list's end, with an order value of ${{ after_total|money }} (value, not a loss).

The counts by list and year are in the note below.

{{ n_unused|capitalize }} Active lists ({{ unused|join(', ') }}) copy list {{ original.id }} and have no lines. **Watch for:** the guard left out. The {{ x.no_list|count }} order lines with no price list line then count as after the end.

{{ figure('IF-08-6-B') }}

### Requirement (5): Customers with their own list

**Step 7. Compare the prices.** Among the customers with a list of ScopeType Customer, filter the order lines whose PricingMethod is neither Customer Price List nor Approved Override. Match each line's customer and ItemID to the customer's own list in PriceListLines, verifying that exactly one row applies. Segment lists carry quantity tiers, so a general lookup also applies the quantity and date rules. Retrieve the cited price by its exact PriceListLineID, never by the first row for a list and an item.

**Check:** {{ n_own }} lines, all of customer {{ customers[0].id }}, {{ customers[0].name }} ({{ customers[0].segment }}), which has its own list {{ customers[0].list }}. They are order lines {{ x.own_lines|map(attribute='line')|join(', ') }}, recorded under {{ method }} and citing list {{ cited }} through its lines {{ x.own_lines|map(attribute='cited_line')|join(', ') }}, while the customer's own list holds lines {{ x.own_lines|map(attribute='own_line')|join(', ') }}. The UnitPrice equals the customer's own list and not the cited one (prices in the note below), so the record names the wrong list, and in {{ stale|join(' and ') }} an expired one.

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
| Promotions flagged, and the approver | {{ flagged|length }}; {{ approver.name }} | 1 |
| Lines and discount of the flagged promotions | {{ n_lines }}; ${{ discount|money }} | 3 |
| Pending requests, invoice lines and amount billed below reference | {{ x.n_pending }}; {{ billed }}; ${{ below|money }} | 4 |
| Order lines after their list's end, and their order value | {{ after|count }}; ${{ after_total|money }} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The counts and discount of the flagged promotions, every line ordered outside the dates, and the reading that the discounts may have been intended while the recorded dates do not authorize them.
- **Requirement (6).** Each exception placed in design, operation or both with the reason and the evidence that would confirm it, marked provisional.
- **Requirement (7).** Amounts on each finding, an order value described as value and not loss, and fixes placed in the system with a periodic review as the detective control.

A weak answer reports the exceptions as losses, blames individuals, or recommends retraining where the system accepted an impossible date.

## Common mistakes and how to respond

- **The type trap.** *Symptom:* a discount total of zero. *Response:* ask what Power Query did to the Discount column.
- **No guard on blank dates.** *Symptom:* about {{ x.no_list|count }} extra lines after a list's end. *Response:* ask what an empty date compares as.
- **A strict inequality in the window.** *Symptom:* lines on the boundary dates counted outside. *Response:* ask whether the end date is inside the promotion.
- **Value read as loss.** *Symptom:* "${{ after_total|money }} lost". *Response:* ask what the lines show about price, not revenue.
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
