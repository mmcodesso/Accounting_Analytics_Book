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
    shows: "A twelve-month strip for one collection promotion's year: a short outlined segment for the recorded window with a backward arrow for its end date, a solid bar for the months its lines were ordered, and beneath it a line of the budget's price as a share of list, dipping in those months."
    data: The promotion's recorded dates, the months its lines were ordered, and the budget's monthly ratio for its collection (Step 3).
---
{% set x = case2_g5 %}
# Requirement 5: Test the controls over promotions (Chapter 8)

{{ header() }}

## Purpose and learning outcomes

Requirement 5 is the auditor's turn. Exercise 8.6 flagged promotions whose recorded dates were impossible; here students test every promotion line against four conditions, decide from outside evidence what kind of error an exception shows, and review who approved what. The analytics type is diagnostic, and the judgment is the point: an exception is a symptom, and the case asks what it is a symptom of.

By the end, students can:

- build guarded line-level tests of date, scope and rate and count exceptions by promotion;
- design a completeness test, and see when it passes with nothing to test;
- use evidence outside the record under test to decide what an exception shows;
- trace an out-of-scope line to the master data;
- review approvals for concentration and self-approval, and count stacked discounts;
- classify each exception as a weakness in design or a failure in operation, and state conditions for the next promotion.

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls) and ISC M2 (tests of internal controls and change management); IMA Reporting and Control (internal control); IFAC IES 2 (f), audit, and IES 2 (g), governance, risk management and internal control; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** The queries of Requirement 1 and the months from Requirement 3. Exercises 8.6 and 4.6 introduced the date flags and the override requests.
- **Data conditions.** Promotions {{ x.failing_ids }} have an end date on or before the start date, and no line of theirs was ordered inside it. {{ oos|capitalize }} order lines are outside their promotion's scope, on an item whose CollectionName is blank. No line carries another rate. One employee approved every promotion and every approved override, and {{ pending }} Pending requests were billed.
- **The test of scope needs three different columns.** A collection is tested on CollectionName, an item group on ItemGroup and a segment on CustomerSegment, after the Promo renames of Requirement 1. Students who skipped the renames cannot finish.

## How to run it

Individual or pairs, about 80 minutes: 25 on the tests, 15 on the evidence, 10 on scope, 15 on approvals and stacking, 15 on dispositions and conditions. Hold back the evidence hint ("what other records say when the promotion ran?") until a student has counted the exceptions. **Collect** the table of tests and the dispositions; they are Exhibit 5 of the memo.

{{ figure('IF-C2-5-A') }}

## Step-by-step solution

### Phase 1: Four tests on every promotion line

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

**Watch for:** the guard left out. A count of FALSE over the whole DateOK column reads {{ x.unguarded|count }}, because the {{ x.non_promo|count }} lines with no promotion have no dates to fall inside. And one scope column used for every kind: testing ItemGroup alone flags all {{ x.other_kinds|count }} lines of the collection and segment promotions.

**Step 2. Test completeness.** For each promotion count the lines in its scope ordered in its window that do not carry it:

```
=COUNTIFS(CHOOSE(MATCH($C5,{"Collection","ItemGroup","Segment"},0),OrderLines[CollectionName],OrderLines[ItemGroup],OrderLines[CustomerSegment]),$D5,OrderLines[OrderDate],">="&I5,OrderLines[OrderDate],"<="&J5,OrderLines[PromotionID],"<>"&$A5)
```

The window is the recorded dates, except for a promotion whose lines all fail the date test, whose window is the calendar months in which its lines were ordered (Step 3).

**Check:** zero for every promotion. **Watch for:** the recorded dates used for the failing promotions. The scope holds no line ordered inside them, so the test passes with nothing to test: a result of zero from an empty population is not evidence of completeness.

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

Each end date is on or before its start date, yet every line was ordered in {{ x.evidence[0].ran }}, every collection line of those months carries the promotion, and the budget planned the lower price in those months. The evidence points to a window entered with a wrong end date: a master-data error to correct, not discounts given without authority. Present it as the best reading of the evidence, not a certainty.

{{ figure('IF-C2-5-B') }}

**Step 4. Investigate the lines outside scope.** Filter `OrderLines` where ScopeOK is FALSE, or list them with a formula, and look at the item in `Items`.

**Check:** {{ oos }} lines, SalesOrderLineIDs {{ oos_ids }}, of promotion {{ oos_promo }}, all on item {{ code }}, the {{ base }}, whose CollectionName is blank. The item's name begins with the collection's name, so the discount is right and the item master is incomplete. `Items` lists {{ x.n_blank }} items in the groups that have collections with no CollectionName: {% for b in x.blank %}{{ b.code }} ({{ b.word }}, {{ b.lines }} order lines){% if not loop.last %}; {% endif %}{% endfor %}.

### Phase 3: Approvals, overrides and stacking

**Step 5. Review who approved.** Look up each promotion's approver and approval date in `Employees`, and count the override requests by status and by approver in `Overrides`:

```
=COUNTIFS(Overrides[Status],"Approved",Overrides[ApprovedByEmployeeID],B1,Overrides[RequestedByEmployeeID],B1)
```

**Check:** {{ mgr.name }}, the {{ mgr.title|lower }}, approved all {{ promos }} promotions, each on its start date, and all {{ approved }} approved overrides of {{ x.overrides }} requests, {{ own }} of them the manager's own. The {{ pending }} Pending requests (IDs {{ pending_ids|join(', ') }}) were billed anyway, and {{ n_own_pending }} of them are the manager's own. The other requests came from {{ requesters }}. Finance approves neither promotions nor overrides.

**Step 6. Count the promotions stacked on override prices.** Add `OverrideStatus` to `OrderLines` and `BilledLines`:

```
=IF([@PriceOverrideApprovalID]="","",XLOOKUP([@PriceOverrideApprovalID],Overrides[PriceOverrideApprovalID],Overrides[Status],"Not found"))
```

and count the promotion lines whose status is Approved.

**Check:** the stack is {{ stack_orders }} order lines, {{ stack_billed }} billed lines and ${{ stack_disc|money }} of discount. Whether a negotiated price should also receive a promotion is a question for management, not an exception.

### Phase 4: Dispositions and conditions

**Step 7. Record a disposition for each exception.**

| Exception | Count | Disposition | Design or operation |
|---|---:|---|---|
| Lines of promotions {{ x.failing_ids }} outside their recorded dates | {{ x.tests|sum(attribute='out_dates') }} | Master-data error; evidence from orders and budgets | Design: the system accepts an end date on or before the start date |
| Lines outside their scope | {{ x.tests|sum(attribute='out_scope') }} | Item master incomplete; the discount is right | Design: scope is read from an incomplete master |
| Rate differs; lines missing the promotion | {{ x.tests|sum(attribute='bad_rate') }}; {{ x.tests|sum(attribute='missing') }} | None | Operating as designed |
| Approvals by one employee | {{ approved }} | Concentration; own requests approved | Design (no finance approval) and operation (own requests) |
| Pending requests billed | {{ n_pending }} | Billed at a price nobody approved | Operation, and design (billing does not check) |
| Promotions on override prices | {{ stack_orders }} | A policy question | Design: no stacking rule |

**Step 8. List the conditions for any promotion in {{ x.plan_year }}.** Validated dates (end after start, matching the months meant to run); complete collection data; approval by finance as well as sales, before the start date; independent approval of overrides, with billing waiting for it; a stacking rule; and a post-promotion review against a stated expectation, with the cost shown in a gross-to-net schedule.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions failing the date test; their lines | {{ x.failing_ids }}; {{ x.tests|sum(attribute='out_dates') }} | 1 |
| Lines outside scope; rate exceptions; missing the promotion | {{ x.tests|sum(attribute='out_scope') }}; {{ x.tests|sum(attribute='bad_rate') }}; {{ x.tests|sum(attribute='missing') }} | 1, 2 |
| Approved overrides; the approver's own; pending billed | {{ approved }}; {{ own }}; {{ pending_ids|join(', ') }} | 5 |
| Stacked order lines; billed lines; discount | {{ stack_orders }}; {{ stack_billed }}; ${{ stack_disc|money }} | 6 |

{{ expected() }}

## What a strong answer says

- **Tests.** The counts by promotion for all four conditions, with the guard and a completeness test that is not empty.
- **The date exceptions.** Evidence from the order months and the budgets, and a conclusion that a master-data error is more likely than unauthorized discounts, stated with its limits.
- **Scope.** The item master, not the discount, as the weak point, with the other items named.
- **Approvals.** One person on both promotions and overrides, own requests, pending requests billed, and no finance review, framed as design as well as operation.
- **Conditions.** Each tied to an exception, as controls that would have prevented or detected it.

A weak answer lists exceptions without causes, blames the manager, or calls every exception a failure of operation.

## Common mistakes and how to respond

- **No guard on blank promotions.** *Symptom:* a date exception count of about {{ x.unguarded|count }}. *Response:* ask what a line with no promotion has to be tested against.
- **A scope test on one column.** *Symptom:* every collection and segment line outside scope. *Response:* ask which column defines each kind.
- **A vacuous completeness test.** *Symptom:* zero exceptions for promotions {{ x.failing_ids }} on their recorded dates. *Response:* ask how many lines the test examined.
- **"The discounts were unauthorized".** *Symptom:* a finding with no evidence outside the promotion table. *Response:* ask which other records say when the promotion ran.
- **A wrong discount on the two lines.** *Symptom:* a correction to the discount. *Response:* ask what the item's name says, and what its collection field says.
- **Everything is operation.** *Symptom:* retraining as the only fix. *Response:* ask whether the system would have accepted the record.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Four tests by promotion | 25 | Guarded tests, counts, and a non-empty completeness test | Date and scope tests only |
| Evidence and cause of the date exceptions | 20 | Order months and budgets, a reasoned classification | Counts without a cause |
| Scope investigation | 10 | The item, its master record and the other items | Lines listed without a cause |
| Approvals, overrides and stacking | 20 | Concentration, own requests, pending billed, stacked count | One of the four |
| Dispositions with design or operation | 15 | Each exception placed, with a reason | Placed without reasons |
| Conditions for the next promotion | 10 | Each condition linked to an exception | A generic list |

## Extensions and discussion questions

- Test the segment promotions' scope against each customer's segment at the order date. What would a change of segment do to the test?
- Discuss: a preventive control (date validation) and a detective control (a post-promotion review) both address the date exceptions. Which would you install first?
- Discuss: the sales manager approves promotions and overrides. Who else could, and what would that cost the business?
