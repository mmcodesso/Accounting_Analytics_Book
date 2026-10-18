---
note: case2.r5
uses: [case2.g5]
title: Test the controls over promotions (Chapter 8)
kind: requirement
number: '5'
unit: case2
perspective: auditing
tool: excel
minutes: 80
solution: "PartII-case.zip: Charles River Promotion Case.xlsx, sheet R5 Controls and the calculated columns DateOK, ScopeOK, RateOK and OverrideStatus of OrderLines, with the queries Promotions, Items, Overrides, Employees and BudgetPrices"
figures:
  - id: IF-C2-5-A
    kind: excel-mock
    purpose: The four tests counted by promotion, as the student's R5 Controls sheet shows them.
    shows: "A table with a row for each promotion and the columns Lines, Outside the recorded dates, Outside the scope, Rate differs, Window start, Window end and In scope and window without the promotion, and a total row. The collection promotions' date counts equal their line counts and are outlined, as are the two scope exceptions; every other count is zero."
    data: The Expected results of this requirement (the tests by promotion).
  - id: IF-C2-5-B
    kind: chart
    purpose: The evidence from outside the record under test for one failing promotion, to place beside its recorded dates.
    shows: "A twelve-month strip for one failing collection promotion's year: a short outlined segment for the recorded window with its two dates written beside it and an arrow from the start back to the end date, a solid bar for the months its lines were ordered, and beneath it a line of the budget's price as a share of list, dipping in those months."
    data: The promotion's recorded dates, the months its lines were ordered, and the budget's monthly ratio for its collection (Step 3).
---
{% set x = case2_g5 %}
# Requirement 5: Test the controls over promotions (Chapter 8)

{{ header() }}

## Purpose and learning outcomes

Requirement 5 is the auditor's turn. Exercise 8.6 flagged promotions whose recorded dates were impossible; here students test every promotion line against three conditions and every order line for completeness, decide from outside evidence what an exception most likely shows, and review who approved what. The analytics type is diagnostic: an exception is a symptom of something.

By the end, students can:

- build guarded line-level tests of date, scope and rate and count exceptions by promotion;
- design a completeness test that starts from all order lines, and see when it passes with nothing to test;
- use evidence outside the record under test to decide what an exception shows;
- trace an out-of-scope line to the master data;
- review approvals for concentration and self-approval, and count stacked discounts;
- classify each exception provisionally, and state conditions for the next promotion.

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls) and ISC M2 (tests of internal controls and change management); IMA Reporting and Control (internal control); IFAC IES 2 (f), audit, and IES 2 (g), governance, risk management and internal control; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** The queries of Requirement 1 and the months from Requirement 3. Exercises 8.6 and 4.6 began the date and override tests.
- **Data conditions.** Promotions {{ x.failing_ids }} have an end date on or before the start date, and no line of theirs was ordered inside it. {{ oos|capitalize }} order lines are outside their promotion's scope, on an item whose CollectionName is blank. One employee approved every promotion and approved override, and {{ pending }} Pending requests were billed.
- **Scope needs three columns.** CollectionName for a collection, ItemGroup for an item group and CustomerSegment for a segment, after the Promo renames of Requirement 1.

## How to run it

Individual or pairs, about 80 minutes: 25 on the tests, 15 on the evidence, 10 on scope, 15 on approvals and stacking, 15 on dispositions and conditions. **Collect** the table of tests and the dispositions; they are Exhibit 5 of the memo.

{{ figure('IF-C2-5-A') }}

## Step-by-step solution

### Phase 1: The four tests

**Step 1. Add the line tests to `OrderLines`.** Add three calculated columns to the loaded Table, each guarded for lines with no promotion:

```
DateOK:  =IF([@PromotionID]="","",AND([@OrderDate]>=[@EffectiveStartDate],[@OrderDate]<=[@EffectiveEndDate]))
ScopeOK: =IF([@PromotionID]="","",SWITCH([@ScopeType],"Collection",[@CollectionName]=[@PromoCollection],"ItemGroup",[@ItemGroup]=[@PromoItemGroup],"Segment",[@CustomerSegment]=[@PromoSegment],FALSE))
RateOK:  =IF([@PromotionID]="","",ABS([@Discount]-[@DiscountPct])<0.0000001)
```

SWITCH is not taught in Chapters 4 to 8; a nested IF on ScopeType gives the same result. Then count by promotion, for example `=COUNTIFS(OrderLines[PromotionID],$A5,OrderLines[DateOK],FALSE)`.

**Check:**

| Promotion | Kind | Lines | Outside dates | Outside scope | Rate differs |
|---|---|---:|---:|---:|---:|
{% for t in x.tests %}
| {{ t.id }} {{ t.label }} | {{ t.kind }} | {{ t.lines }} | {{ t.out_dates }} | {{ t.out_scope }} | {{ t.bad_rate }} |
{% endfor %}

**Watch for:** the guard left out. A count of FALSE over DateOK reads {{ x.unguarded|count }}, because the {{ x.non_promo|count }} lines with no promotion have no dates to fall inside. And one scope column used for every kind: testing ItemGroup alone flags all {{ x.other_kinds|count }} lines of the collection and segment promotions.

**Step 2. Test completeness.** Start from all order lines, not only the promotion lines. For each promotion count the lines in its scope ordered in its window that do not carry it, with a blank or another PromotionID:

```
=COUNTIFS(CHOOSE(MATCH($C5,{"Collection","ItemGroup","Segment"},0),OrderLines[CollectionName],OrderLines[ItemGroup],OrderLines[CustomerSegment]),$D5,OrderLines[OrderDate],">="&I5,OrderLines[OrderDate],"<="&J5,OrderLines[PromotionID],"<>"&$A5)
```

Run it twice for a promotion whose lines all fail the date test: on its recorded dates, which hold no order line of its scope, the result stays unresolved, and on the months its lines were ordered in (Step 3) the test is labeled provisional. The model answer's window columns hold the provisional window.

**Check:** on the recorded dates, promotions {{ x.failing_ids }} have no eligible line, so their result is unresolved, not zero. In the provisional March-April windows they have {% for v in x.provisional %}{{ v.lines }} {{ v.label }}{% if not loop.last %}, {% endif %}{% endfor %} eligible lines, none missing the promotion or carrying another PromotionID under the current item classification. The other {{ x.n_other }} promotions have eligible lines in their recorded windows, none missing. Confirm the calendar and item classification before a final conclusion.

### Phase 2: What kind of error

**Step 3. Find evidence of when the failing promotions were meant to run.** For promotions {{ x.failing_ids }} list the recorded dates, the first and last order and the budget's planned price for the collection by month:

```
=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[CollectionName],$B17,BudgetPrices[FiscalYear],YEAR($F17),BudgetPrices[Month],H$16)/SUMIFS(BudgetPrices[ListAmount],BudgetPrices[CollectionName],$B17,BudgetPrices[FiscalYear],YEAR($F17),BudgetPrices[Month],H$16)
```

**Check:**

| Promotion | Recorded dates | Lines ordered | Highest budget ratio in those months | Lowest in months with no promotion |
|---|---|---|---:|---:|
{% for e in x.evidence %}
| {{ e.id }} {{ e.label }} | {{ e.start }} to {{ e.end }} | {{ e.first }} to {{ e.last }} | {{ e.high|num(4) }} | {{ e.low|num(4) }} |
{% endfor %}

Each end date is on or before its start date, yet every line was ordered in {{ x.evidence[0].ran }}, every collection line of those months carries the promotion, and the budget planned the lower price then. That points to a likely wrong end date rather than discounts given without authority, to be confirmed by the approved calendar and change history, so present it provisionally.

{{ figure('IF-C2-5-B') }}

**Step 4. Investigate the lines outside scope.** Filter `OrderLines` where ScopeOK is FALSE, or list them with a formula, and look at the item in `Items`.

**Check:** {{ oos }} lines, SalesOrderLineIDs {{ oos_ids }}, of promotion {{ oos_promo }}, all on item {{ code }}, the {{ base }}, whose CollectionName is blank. The name begins with the collection's, which suggests an incomplete item master rather than a wrong discount; the item's classification when sold and the approved scope would settle it. `Items` lists {{ x.n_blank }} items in the groups that have collections with no CollectionName: {% for b in x.blank %}{{ b.code }} ({{ b.word }}, {{ b.lines }} order lines){% if not loop.last %}; {% endif %}{% endfor %}.

### Phase 3: Approvals, overrides and stacking

**Step 5. Review who approved.** Look up each promotion's approver and approval date in `Employees`, and count the override requests by status and by approver in `Overrides`:

```
=COUNTIFS(Overrides[Status],"Approved",Overrides[ApprovedByEmployeeID],B1,Overrides[RequestedByEmployeeID],B1)
```

The billed lines carry no override link, so a lookup of their blank PriceOverrideApprovalID cannot find the Pending requests' billing. Add a helper to `Overrides` and count the Pending requests with `BilledLineCount` above 0:

```
BilledLineCount: =COUNTIF(BilledLines[SalesOrderLineID],[@SalesOrderLineID])
```

**Check:** {{ mgr.name }}, the {{ mgr.title|lower }}, approved all {{ promos }} promotions, each on its start date, and all {{ approved }} approved overrides of {{ x.overrides }} requests, {{ own }} of them the manager's own. The {{ pending }} Pending requests (IDs {{ pending_ids|join(', ') }}) were billed anyway, on {{ x.n_pending_lines }} lines (SalesInvoiceLineIDs {{ x.pending_lines|join(', ') }}), and {{ n_own_pending }} of them are the manager's own. Each billed unit price equals the request's stored ApprovedUnitPrice, a field filled although the status is Pending and no approver is recorded, so the field name is not proof of a completed approval. No approval by anyone in finance is recorded, and whether the self-approvals break a rule depends on the authority matrix.

**Step 6. Count the promotions stacked on override prices.** Add `OverrideStatus` to `OrderLines` and `BilledLines`:

```
=IF([@PriceOverrideApprovalID]="","",XLOOKUP([@PriceOverrideApprovalID],Overrides[PriceOverrideApprovalID],Overrides[Status],"Not found"))
```

and count the promotion lines whose status is Approved.

**Check:** the stack is {{ stack_orders }} order lines, {{ stack_billed }} billed lines and ${{ stack_disc|money }} of discount. Whether a negotiated price should also receive a promotion is for management to decide.

### Phase 4: Dispositions and conditions

**Step 7. Record a disposition for each exception.**

| Exception | Count | Disposition | Provisional classification |
|---|---:|---|---|
| Lines of promotions {{ x.failing_ids }} outside their recorded dates | {{ x.tests|sum(attribute='out_dates') }} | Likely wrong end dates, from the orders and budgets, to confirm with the approved calendar | Possible date-validation or calendar-maintenance weakness{% if x.n_reversed %}: {{ 'promotion' if x.n_reversed == 1 else 'promotions' }} {{ x.reversed_ids }} {{ 'ends' if x.n_reversed == 1 else 'end' }} before {{ 'it starts' if x.n_reversed == 1 else 'they start' }}{% endif %}{% if x.n_same_day %}{{ ', and' if x.n_reversed else ':' }} {{ 'promotion' if x.n_same_day == 1 else 'promotions' }} {{ x.same_day_ids }} {{ 'is a one-day window' if x.n_same_day == 1 else 'are one-day windows' }} that {{ 'does' if x.n_same_day == 1 else 'do' }} not contain the observed orders{% endif %}. Obtain the authorized calendar, change history and validation rules to distinguish design from operation |
| Lines outside their scope | {{ x.tests|sum(attribute='out_scope') }} | Likely an incomplete item master, to confirm from the item's classification and the approved scope | Possibly design: scope is read from an incomplete master |
| Rate differs | {{ x.tests|sum(attribute='bad_rate') }} | None found on the promotion lines | None |
| Lines missing the promotion | {{ x.tests|sum(attribute='missing') }} | Unresolved on the recorded dates of promotions {{ x.failing_ids }} (no eligible line). None in their provisional windows or in the other promotions | Not assessed until the calendar and item classification are confirmed |
| Approvals by one employee | {{ approved }} | One recorded approver, own requests approved, no finance approval | Design if no rule requires an independent approver, operation if one does |
| Pending requests billed | {{ n_pending }} | Billed with no completed approval in this extract | Possible approval-workflow weakness: no completed approval is recorded in this extract. Obtain approval history and billing timestamps to determine whether billing preceded authorization |
| Promotions on override prices | {{ stack_orders }} | A policy question | Possibly design: no stacking rule is recorded |

**Step 8. List the conditions for any promotion in {{ x.plan_year }}.** Validated dates (no end date before the start, a rule on whether a promotion may last one day, and dates matching the months meant to run); complete collection data; approval by finance as well as sales; independent approval of overrides, with billing waiting for it; a stacking rule; and a post-promotion review against a stated expectation, with the cost shown in a gross-to-net schedule.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions failing the date test; their lines | {{ x.failing_ids }}; {{ x.tests|sum(attribute='out_dates') }} | 1 |
| Lines outside scope; rate exceptions | {{ x.tests|sum(attribute='out_scope') }}; {{ x.tests|sum(attribute='bad_rate') }} | 1 |
| Eligible lines in the provisional windows of promotions {{ x.failing_ids }}; missing the promotion; eligible on the recorded dates | {% for v in x.provisional %}{{ v.lines }}{% if not loop.last %}, {% endif %}{% endfor %}; {{ x.tests|sum(attribute='missing') }}; none | 2 |
| Approved overrides; the approver's own; pending requests and their billed lines | {{ approved }}; {{ own }}; {{ pending_ids|join(', ') }}, {{ x.n_pending_lines }} lines | 5 |
| Stacked order lines; billed lines; discount | {{ stack_orders }}; {{ stack_billed }}; ${{ stack_disc|money }} | 6 |

{{ expected() }}

## What a strong answer says

- **Tests.** Counts by promotion for all four conditions, with the guard, completeness from all order lines, and the recorded-date result kept as unresolved.
- **The date exceptions.** Evidence from the order months and the budgets, and a master-data error judged more likely than unauthorized discounts, with its limits.
- **Scope.** The item master as the likely weak point, the record that would confirm it, and the other items named.
- **Approvals and conditions.** One person on promotions and overrides, own requests, pending requests billed, no finance review, classified provisionally, and each condition tied to an exception.

A weak answer lists exceptions without causes, blames the manager, or calls every exception a failure of operation.

## Common mistakes and how to respond

- **No guard, or one scope column.** *Symptom:* a date exception count of about {{ x.unguarded|count }}, or every collection and segment line outside scope. *Response:* ask what a line with no promotion is tested against, and which column defines each kind.
- **A vacuous completeness test.** *Symptom:* zero exceptions for promotions {{ x.failing_ids }} on their recorded dates. *Response:* ask how many lines the test examined.
- **"The discounts were unauthorized".** *Symptom:* a finding with no evidence outside the promotion table. *Response:* ask which other records say when the promotion ran.
- **A wrong discount on the two lines.** *Symptom:* a correction to the discount. *Response:* ask what the item's name and its collection field say.
- **Everything is operation.** *Symptom:* retraining as the only fix. *Response:* ask whether the system would have accepted the record.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Four tests by promotion | 25 | Guarded tests, counts, and a non-empty completeness test | Date and scope tests only |
| Evidence and cause of the date exceptions | 20 | Order months, budgets, a reasoned classification | Counts without a cause |
| Scope investigation | 10 | The item, its master record and the other items | Lines listed without a cause |
| Approvals, overrides and stacking | 20 | Concentration, own requests, pending billed, stacked count | One of the four |
| Dispositions | 15 | Each exception classified provisionally, with the confirming evidence | Placed without reasons |
| Conditions for the next promotion | 10 | Each condition linked to an exception | A generic list |

## Extensions and discussion questions

- Discuss: a preventive control (date validation) and a detective one (a post-promotion review) both address the date exceptions. Which first?
