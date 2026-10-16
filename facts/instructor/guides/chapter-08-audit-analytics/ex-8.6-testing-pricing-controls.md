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
- **Data conditions.** The date test flags {{ flagged|length }} promotions, and all of their lines were ordered outside the recorded dates. The Pending override requests number {{ x.n_pending }}, and the Expired price lists {{ expired|length }}, with no successor. The {{ x.order_lines|count }} order lines include {{ x.no_list|count }} with no price list line.

## How to run it

Pairs, about 135 minutes, best over two sessions: 10 for requirement (1), 30 for (2), 20 for (3), 30 for (4), 15 for (5), 10 for (6) and 20 for the memo (7). Hold back the guard hint until a price-list count is far too large. Collect the workbook and the memo.

{{ figure('IF-08-6-A') }}

## Step-by-step solution

### Requirement (1): Promotions with impossible dates

**Step 1. Flag the promotions.** Import **T7_PromotionProgram** as `Promotions`, merge the approver's name from the Employees query (or look it up), add `EndOnOrBeforeStart` as `=[@EffectiveEndDate]<=[@EffectiveStartDate]` and list the flagged promotions with approver and approval date.

**Check:** {{ flagged|length }} promotions: {% for p in flagged %}{{ p.code }} ({{ p.collection }}){% if not loop.last %}, {% endif %}{% endfor %}. They are the {{ pct|pct(0) }} collection promotions of each spring, approved by {{ approver.name }}, the {{ approver.title|lower }}, on their start dates. Promotion {{ same_day|join(', ') }} ends on its start date; the others end before they start.

### Requirement (2): Their invoice lines

**Step 2. Bring in the order dates.**

a. Import **T17_SalesInvoiceLine**, **T16_SalesInvoice** and **T9_SalesOrder** as `InvoiceLines`, `InvoiceHeaders` and `Orders`, and set Discount in InvoiceLines to **Decimal Number** with **Replace current**.
b. Merge InvoiceLines with InvoiceHeaders on SalesInvoiceID, expand InvoiceDate and SalesOrderID, merge with Orders on SalesOrderID and expand OrderDate, and merge with Promotions on PromotionID and expand the two effective dates.

**Step 3. Add the amount and the window test, and summarize.** Add `DiscountAmount` as `=[@Quantity]*[@UnitPrice]*[@Discount]` and `OrderedInWindow` as below, then count the lines and total the discount for each flagged promotion with COUNTIFS and SUMIFS.

```
=IF([@PromotionID]="","",AND([@OrderDate]>=[@EffectiveStartDate],[@OrderDate]<=[@EffectiveEndDate]))
```

**Check:**

{% for p in flagged %}
- {{ p.code }}: {{ flagged_lines[loop.index0].n }} lines and ${{ flagged_lines[loop.index0].discount|money }} of discount, all ordered outside the dates.
{% endfor %}

Together {{ n_lines }} lines and ${{ discount|money }}, ordered in {{ order_months|join(' and ') }} and invoiced through {{ last_months|join(' or ') }}. No line of any other promotion was ordered outside its dates. Both end dates count as inside, so the one-day promotion's lines would count if any had been ordered that day. **Watch for:** the type trap (a discount total of zero) and a strict inequality, which counts {{ x.boundary|count }} lines of the other promotions, ordered on a start or end date, as outside their dates.

### Requirement (3): Pending overrides

**Step 4. Find the lines billed at a pending price.** Import **T8_PriceOverrideApproval** as `PendingOverrides`, filtered to Pending. List the InvoiceLines whose SalesOrderLineID is in it, show UnitPrice beside the request's ReferenceUnitPrice and ApprovedUnitPrice, add PricingMethod and PriceOverrideApprovalID, and total the amount billed below the reference (in the model answer the list spills from A21).

```
=SUM(INDEX(A21#,0,10))
```

**Check:** {{ x.n_pending }} requests on {{ billed }} invoice lines, each billed at the pending ApprovedUnitPrice, under {{ methods|join(' or ') }} and with a blank PriceOverrideApprovalID, ${{ below|money }} below the reference prices in total. An order line shipped in two parts has two invoice lines.

### Requirement (4): Price lists

**Step 5. Flag the lists and their lines.**

a. Import **T5_PriceList**, **T6_PriceListLine** and **T10_SalesOrderLine** as `PriceLists`, `PriceListLines` and `OrderLines`. Add `Flagged` to PriceLists as `=OR([@Status]="Expired",[@EffectiveEndDate]<[@EffectiveStartDate])`.
b. In OrderLines merge PriceListLines (PriceListID) and PriceLists (the list's EffectiveEndDate), then Orders (OrderDate and CustomerID). Add `OrderYear` as `=YEAR([@OrderDate])` and `AfterListEnd`.

```
=IF([@PriceListID]="",FALSE,[@OrderDate]>[@ListEndDate])
```

**Step 6. Count by list and year.** Use COUNTIFS on the list, the year and AfterListEnd, and list the Active lists with no order lines.

**Check:** {{ expired|length }} flagged lists, none with a later list for its segment, and {{ after|count }} order lines after their list's end, with an order value of ${{ after_total|money }} (value, not a loss).

{% for pl in per_list %}
- List {{ pl.id }}: {% for yr, n in pl.years %}{{ n|count }} in {{ yr }}{% if not loop.last %}, {% endif %}{% endfor %}.
{% endfor %}

{{ n_unused|capitalize }} Active lists ({{ unused|join(', ') }}) copy list {{ original.id }} and have no lines. **Watch for:** the guard left out. The {{ x.no_list|count }} order lines with no price list line then count as after the end, because an empty date is earlier than any date.

{{ figure('IF-08-6-B') }}

### Requirement (5): Customers with their own list

**Step 7. Compare the prices.** Among the customers with a list of ScopeType Customer, filter the order lines whose PricingMethod is neither Customer Price List nor Approved Override. Look up each line's price on the customer's own list and on the list it cites, and compare.

**Check:** {{ n_own }} lines, all of customer {{ customers[0].id }}, {{ customers[0].name }} ({{ customers[0].segment }}), which has its own list {{ customers[0].list }}. They are recorded under {{ method }} and cite list {{ cited }}. The UnitPrice equals the customer's own list ({% for o in own %}${{ o.price|money }}{% if not loop.last %}, {% endif %}{% endfor %}) and not the cited list ({% for o in own %}${{ o.cited|money }}{% if not loop.last %}, {% endif %}{% endfor %}). The price is the contract price; the record names the wrong list, and in {{ stale|join(' and ') }} an expired one.

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
| Promotions flagged, and the approver | {{ flagged|length }}; {{ approver.name }} | 1 |
| Lines and discount of the flagged promotions | {{ n_lines }}; ${{ discount|money }} | 3 |
| Pending requests, invoice lines and amount billed below reference | {{ x.n_pending }}; {{ billed }}; ${{ below|money }} | 4 |
| Order lines after their list's end, and their order value | {{ after|count }}; ${{ after_total|money }} | 6 |
| Active lists with no lines | {{ unused|join(', ') }} | 6 |
| Customer-list lines priced another way | {{ n_own }} | 7 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The counts and discount of the flagged promotions, every line ordered outside the dates, and the reading that the discounts may have been intended while the recorded dates do not authorize them, so the approved campaign terms are the evidence to request.
- **Requirement (6).** Each exception placed in design, operation or both with the reason and the evidence that would confirm it, marked provisional.
- **Requirement (7).** Amounts on each finding, an order value described as value and not loss, and fixes placed in the system with a periodic review as the detective control.

A weak answer reports the exceptions as losses, blames individuals, or recommends retraining where the system accepted an impossible date.

## Common mistakes and how to respond

- **The type trap.** *Symptom:* a discount total of zero. *Response:* ask what Power Query did to the Discount column.
- **No guard on blank dates.** *Symptom:* about {{ x.no_list|count }} extra lines after a list's end. *Response:* ask what an empty date compares as.
- **A strict inequality in the window.** *Symptom:* lines on the boundary dates counted outside. *Response:* ask whether the end date is inside the promotion.
- **Value read as loss.** *Symptom:* "${{ after_total|money }} lost". *Response:* ask what the lines show about price, not revenue.
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
