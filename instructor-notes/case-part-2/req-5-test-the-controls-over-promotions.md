# Requirement 5: Test the controls over promotions (Chapter 8)

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Item | Requirement 5 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 80 minutes |
| Solution file | PartII-case.zip: Charles River Promotion Case.xlsx, sheet R5 Controls and the calculated columns DateOK, ScopeOK, RateOK and OverrideStatus of OrderLines, with the queries Promotions, Items, Overrides, Employees and BudgetPrices |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

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
- **Data conditions.** Promotions 1, 4, and 7 have an end date on or before the start date, and no line of theirs was ordered inside it. Two order lines are outside their promotion's scope, on an item whose CollectionName is blank. No line carries another rate. One employee approved every promotion and every approved override, and three Pending requests were billed.
- **The test of scope needs three different columns.** A collection is tested on CollectionName, an item group on ItemGroup and a segment on CustomerSegment, after the Promo renames of Requirement 1. Students who skipped the renames cannot finish.

## How to run it

Individual or pairs, about 80 minutes: 25 on the tests, 15 on the evidence, 10 on scope, 15 on approvals and stacking, 15 on dispositions and conditions. Hold back the evidence hint ("what other records say when the promotion ran?") until a student has counted the exceptions. **Collect** the table of tests and the dispositions; they are Exhibit 5 of the memo.

> **[Figure placeholder IF-C2-5-A]** The four tests counted by promotion, as the student's R5 Controls sheet shows them.
> Kind: excel-mock · Shows: A table with a row for each promotion and the columns Lines, Outside the recorded dates, Outside the scope, Rate differs, Window start, Window end and In scope and window without the promotion, and a total row. The collection promotions' date counts equal their line counts and are outlined, as are the two scope exceptions; every other count is zero. · Data: The Expected results of this requirement (the tests by promotion). · Status: planned

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
| 1 Alder | collection | 61 | 61 | 2 | 0 |
| 2 Accessories | item group | 318 | 0 | 0 | 0 |
| 3 Strategic | segment | 120 | 0 | 0 | 0 |
| 4 Brookside | collection | 63 | 63 | 0 | 0 |
| 5 Textiles | item group | 168 | 0 | 0 | 0 |
| 6 Wholesale | segment | 315 | 0 | 0 | 0 |
| 7 Harbor | collection | 54 | 54 | 0 | 0 |
| 8 Furniture | item group | 467 | 0 | 0 | 0 |
| 9 Design Trade | segment | 84 | 0 | 0 | 0 |

**Watch for:** the guard left out. A count of FALSE over the whole DateOK column reads 20,797, because the 20,619 lines with no promotion have no dates to fall inside. And one scope column used for every kind: testing ItemGroup alone flags all 697 lines of the collection and segment promotions.

**Step 2. Test completeness.** For each promotion count the lines in its scope ordered in its window that do not carry it:

```
=COUNTIFS(CHOOSE(MATCH($C5,{"Collection","ItemGroup","Segment"},0),OrderLines[CollectionName],OrderLines[ItemGroup],OrderLines[CustomerSegment]),$D5,OrderLines[OrderDate],">="&I5,OrderLines[OrderDate],"<="&J5,OrderLines[PromotionID],"<>"&$A5)
```

The window is the recorded dates, except for a promotion whose lines all fail the date test, whose window is the calendar months in which its lines were ordered (Step 3).

**Check:** zero for every promotion. **Watch for:** the recorded dates used for the failing promotions. The scope holds no line ordered inside them, so the test passes with nothing to test: a result of zero from an empty population is not evidence of completeness.

### Phase 2: What kind of error

**Step 3. Find evidence of when the failing promotions were meant to run.** For promotions 1, 4, and 7 list the recorded dates, the first and last order and the budget's planned price for the collection by month:

```
=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[CollectionName],$B17,BudgetPrices[FiscalYear],YEAR($F17),BudgetPrices[Month],H$16)/SUMIFS(BudgetPrices[ListAmount],BudgetPrices[CollectionName],$B17,BudgetPrices[FiscalYear],YEAR($F17),BudgetPrices[Month],H$16)
```

**Check:**

| Promotion | Recorded dates | Lines ordered | Highest budget ratio in those months | Lowest in months with no promotion |
|---|---|---|---:|---:|
| 1 Alder | 2024-03-01 to 2024-03-01 | 2024-03-03 to 2024-04-30 | 0.8806 | 0.9274 |
| 4 Brookside | 2025-03-01 to 2025-02-27 | 2025-03-01 to 2025-04-30 | 0.8806 | 0.9270 |
| 7 Harbor | 2026-03-01 to 2026-02-28 | 2026-03-02 to 2026-04-30 | 0.8806 | 0.9259 |

Each end date is on or before its start date, yet every line was ordered in March and April, every collection line of those months carries the promotion, and the budget planned the lower price in those months. The evidence points to a window entered with a wrong end date: a master-data error to correct, not discounts given without authority. Present it as the best reading of the evidence, not a certainty.

> **[Figure placeholder IF-C2-5-B]** The evidence from outside the record under test for one failing promotion, to place beside its recorded dates.
> Kind: chart · Shows: A twelve-month strip for one collection promotion's year: a short outlined segment for the recorded window with a backward arrow for its end date, a solid bar for the months its lines were ordered, and beneath it a line of the budget's price as a share of list, dipping in those months. · Data: The promotion's recorded dates, the months its lines were ordered, and the budget's monthly ratio for its collection (Step 3). · Status: planned

**Step 4. Investigate the lines outside scope.** Filter `OrderLines` where ScopeOK is FALSE, or list them with a formula, and look at the item in `Items`.

**Check:** two lines, SalesOrderLineIDs 1249 and 2142, of promotion 1, all on item FUR-CON-0003, the Alder Console Table, whose CollectionName is blank. The item's name begins with the collection's name, so the discount is right and the item master is incomplete. `Items` lists 3 items in the groups that have collections with no CollectionName: FUR-SDB-0002 (Willow, 174 order lines); FUR-CON-0003 (Alder, 51 order lines); FUR-DSK-0004 (Summit, 43 order lines).

### Phase 3: Approvals, overrides and stacking

**Step 5. Review who approved.** Look up each promotion's approver and approval date in `Employees`, and count the override requests by status and by approver in `Overrides`:

```
=COUNTIFS(Overrides[Status],"Approved",Overrides[ApprovedByEmployeeID],B1,Overrides[RequestedByEmployeeID],B1)
```

**Check:** Carrie Schultz, the sales manager, approved all nine promotions, each on its start date, and all 409 approved overrides of 412 requests, 106 of them the manager's own. The three Pending requests (IDs 2, 165, 294) were billed anyway, and three of them are the manager's own. The other requests came from account executives and sales representatives. Finance approves neither promotions nor overrides.

**Step 6. Count the promotions stacked on override prices.** Add `OverrideStatus` to `OrderLines` and `BilledLines`:

```
=IF([@PriceOverrideApprovalID]="","",XLOOKUP([@PriceOverrideApprovalID],Overrides[PriceOverrideApprovalID],Overrides[Status],"Not found"))
```

and count the promotion lines whose status is Approved.

**Check:** the stack is 34 order lines, 45 billed lines and $16,006.78 of discount. Whether a negotiated price should also receive a promotion is a question for management, not an exception.

### Phase 4: Dispositions and conditions

**Step 7. Record a disposition for each exception.**

| Exception | Count | Disposition | Design or operation |
|---|---:|---|---|
| Lines of promotions 1, 4, and 7 outside their recorded dates | 178 | Master-data error; evidence from orders and budgets | Design: the system accepts an end date on or before the start date |
| Lines outside their scope | 2 | Item master incomplete; the discount is right | Design: scope is read from an incomplete master |
| Rate differs; lines missing the promotion | 0; 0 | None | Operating as designed |
| Approvals by one employee | 409 | Concentration; own requests approved | Design (no finance approval) and operation (own requests) |
| Pending requests billed | 3 | Billed at a price nobody approved | Operation, and design (billing does not check) |
| Promotions on override prices | 34 | A policy question | Design: no stacking rule |

**Step 8. List the conditions for any promotion in 2027.** Validated dates (end after start, matching the months meant to run); complete collection data; approval by finance as well as sales, before the start date; independent approval of overrides, with billing waiting for it; a stacking rule; and a post-promotion review against a stated expectation, with the cost shown in a gross-to-net schedule.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions failing the date test; their lines | 1, 4, and 7; 178 | 1 |
| Lines outside scope; rate exceptions; missing the promotion | 2; 0; 0 | 1, 2 |
| Approved overrides; the approver's own; pending billed | 409; 106; 2, 165, 294 | 5 |
| Stacked order lines; billed lines; discount | 34; 45; $16,006.78 | 6 |

> **Instructor notes, Requirement 5:** dates: every line of promotions 1 (Alder, recorded 2024-03-01 to 2024-03-01), 4 (Brookside, 2025-03-01 to 2025-02-27), and 7 (Harbor, 2026-03-01 to 2026-02-28) fails, and every line of the other six passes (Exercise 8.6). All their lines were ordered between March 1 and April 30, every line of the collection ordered in those months carries the promotion, and each year's budget planned the collection's discount in March and April. The evidence points to a March-April window with a wrong end date, a master-data error, rather than discounts given without authority. The generator's AnomalyLog records these end dates as changed to fall before the order dates. Scope: two promotion 1 order lines (SalesOrderLineIDs 1249 and 2142) are on item 11, FUR-CON-0003, the Alder Console Table, whose CollectionName is blank. The discount is right and the item master is incomplete; FUR-SDB-0002 (Willow) and FUR-DSK-0004 (Summit) also lack a collection. Rate: every promotion line carries its promotion's DiscountPct. Completeness: no line in a promotion's scope and months lacks the promotion, with collection months taken as March-April. Approvals: EmployeeID 6 (Carrie Schultz, Sales Manager) approved all nine promotions, each on its start date, and approved all 409 approved override requests, 106 of them the manager's own. The manager's three other requests are still Pending (IDs 2, 165, 294), yet they were billed (Exercises 4.6 and 8.6); the other requests came from account executives and sales representatives. Pricing authority sits with one person, and finance approves neither promotions nor overrides. Stacking: 34 order lines (45 billed lines) carry both an approved override and a promotion, 16,006.78 of discount; whether a negotiated price should also receive a promotion is a policy question. Design: the system accepts end dates before start dates and scope from an incomplete item master; operation: approvals by the person who requested them. Conditions: validated dates, complete collection data, approval of promotions by finance as well as sales, independent approval of overrides, a stacking rule, and a post-promotion review.

## What a strong answer says

- **Tests.** The counts by promotion for all four conditions, with the guard and a completeness test that is not empty.
- **The date exceptions.** Evidence from the order months and the budgets, and a conclusion that a master-data error is more likely than unauthorized discounts, stated with its limits.
- **Scope.** The item master, not the discount, as the weak point, with the other items named.
- **Approvals.** One person on both promotions and overrides, own requests, pending requests billed, and no finance review, framed as design as well as operation.
- **Conditions.** Each tied to an exception, as controls that would have prevented or detected it.

A weak answer lists exceptions without causes, blames the manager, or calls every exception a failure of operation.

## Common mistakes and how to respond

- **No guard on blank promotions.** *Symptom:* a date exception count of about 20,797. *Response:* ask what a line with no promotion has to be tested against.
- **A scope test on one column.** *Symptom:* every collection and segment line outside scope. *Response:* ask which column defines each kind.
- **A vacuous completeness test.** *Symptom:* zero exceptions for promotions 1, 4, and 7 on their recorded dates. *Response:* ask how many lines the test examined.
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
