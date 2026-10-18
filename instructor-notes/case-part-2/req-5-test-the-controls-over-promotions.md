# Requirement 5: Test the controls over promotions (Chapter 8)

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Item | Requirement 5 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 80 minutes |
| Solution file | PartII-case.zip: Charles River Promotion Case.xlsx, sheet R5 Controls and the calculated columns DateOK, ScopeOK, RateOK and OverrideStatus of OrderLines, with the queries Promotions, Items, Overrides, Employees and BudgetPrices |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

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
- **Data conditions.** Promotions 1, 4, and 7 have an end date on or before the start date, and no line of theirs was ordered inside it. Two order lines are outside their promotion's scope, on an item whose CollectionName is blank. One employee approved every promotion and approved override, and three Pending requests were billed.
- **Scope needs three columns.** CollectionName for a collection, ItemGroup for an item group and CustomerSegment for a segment, after the Promo renames of Requirement 1.

## How to run it

Individual or pairs, about 80 minutes: 25 on the tests, 15 on the evidence, 10 on scope, 15 on approvals and stacking, 15 on dispositions and conditions. **Collect** the table of tests and the dispositions; they are Exhibit 5 of the memo.

![A mock of the four tests counted by promotion, as the student's R5 Controls sheet shows them.](../figures/case-part-2/IF-C2-5-A.pdf)

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
| 1 Alder | collection | 61 | 61 | 2 | 0 |
| 2 Accessories | item group | 318 | 0 | 0 | 0 |
| 3 Strategic | segment | 120 | 0 | 0 | 0 |
| 4 Brookside | collection | 63 | 63 | 0 | 0 |
| 5 Textiles | item group | 168 | 0 | 0 | 0 |
| 6 Wholesale | segment | 315 | 0 | 0 | 0 |
| 7 Harbor | collection | 54 | 54 | 0 | 0 |
| 8 Furniture | item group | 467 | 0 | 0 | 0 |
| 9 Design Trade | segment | 84 | 0 | 0 | 0 |

**Watch for:** the guard left out. A count of FALSE over DateOK reads 20,797, because the 20,619 lines with no promotion have no dates to fall inside. And one scope column used for every kind: testing ItemGroup alone flags all 697 lines of the collection and segment promotions.

**Step 2. Test completeness.** Start from all order lines, not only the promotion lines. For each promotion count the lines in its scope ordered in its window that do not carry it, with a blank or another PromotionID:

```
=COUNTIFS(CHOOSE(MATCH($C5,{"Collection","ItemGroup","Segment"},0),OrderLines[CollectionName],OrderLines[ItemGroup],OrderLines[CustomerSegment]),$D5,OrderLines[OrderDate],">="&I5,OrderLines[OrderDate],"<="&J5,OrderLines[PromotionID],"<>"&$A5)
```

Run it twice for a promotion whose lines all fail the date test: on its recorded dates, which hold no order line of its scope, the result stays unresolved, and on the months its lines were ordered in (Step 3) the test is labeled provisional. The model answer's window columns hold the provisional window.

**Check:** on the recorded dates, promotions 1, 4, and 7 have no eligible line, so their result is unresolved, not zero. In the provisional March-April windows they have 59 Alder, 63 Brookside, 54 Harbor eligible lines, none missing the promotion or carrying another PromotionID under the current item classification. The other six promotions have eligible lines in their recorded windows, none missing. Confirm the calendar and item classification before a final conclusion.

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

Each end date is on or before its start date, yet every line was ordered in March and April, every collection line of those months carries the promotion, and the budget planned the lower price then. That points to a likely wrong end date rather than discounts given without authority, to be confirmed by the approved calendar and change history, so present it provisionally.

![The evidence from outside the record under test for one failing promotion, to place beside its recorded dates.](../figures/case-part-2/IF-C2-5-B.pdf)

**Step 4. Investigate the lines outside scope.** Filter `OrderLines` where ScopeOK is FALSE, or list them with a formula, and look at the item in `Items`.

**Check:** two lines, SalesOrderLineIDs 1249 and 2142, of promotion 1, all on item FUR-CON-0003, the Alder Console Table, whose CollectionName is blank. The name begins with the collection's, which suggests an incomplete item master rather than a wrong discount; the item's classification when sold and the approved scope would settle it. `Items` lists 3 items in the groups that have collections with no CollectionName: FUR-SDB-0002 (Willow, 174 order lines); FUR-CON-0003 (Alder, 51 order lines); FUR-DSK-0004 (Summit, 43 order lines).

### Phase 3: Approvals, overrides and stacking

**Step 5. Review who approved.** Look up each promotion's approver and approval date in `Employees`, and count the override requests by status and by approver in `Overrides`:

```
=COUNTIFS(Overrides[Status],"Approved",Overrides[ApprovedByEmployeeID],B1,Overrides[RequestedByEmployeeID],B1)
```

The billed lines carry no override link, so a lookup of their blank PriceOverrideApprovalID cannot find the Pending requests' billing. Add a helper to `Overrides` and count the Pending requests with `BilledLineCount` above 0:

```
BilledLineCount: =COUNTIF(BilledLines[SalesOrderLineID],[@SalesOrderLineID])
```

**Check:** Carrie Schultz, the sales manager, approved all nine promotions, each on its start date, and all 409 approved overrides of 412 requests, 106 of them the manager's own. The three Pending requests (IDs 2, 165, 294) were billed anyway, on four lines (SalesInvoiceLineIDs 67, 9373, 10164, 18670), and three of them are the manager's own. Each billed unit price equals the request's stored ApprovedUnitPrice, a field filled although the status is Pending and no approver is recorded, so the field name is not proof of a completed approval. No approval by anyone in finance is recorded, and whether the self-approvals break a rule depends on the authority matrix.

**Step 6. Count the promotions stacked on override prices.** Add `OverrideStatus` to `OrderLines` and `BilledLines`:

```
=IF([@PriceOverrideApprovalID]="","",XLOOKUP([@PriceOverrideApprovalID],Overrides[PriceOverrideApprovalID],Overrides[Status],"Not found"))
```

and count the promotion lines whose status is Approved.

**Check:** the stack is 34 order lines, 45 billed lines and $16,006.78 of discount. Whether a negotiated price should also receive a promotion is for management to decide.

### Phase 4: Dispositions and conditions

**Step 7. Record a disposition for each exception.**

| Exception | Count | Disposition | Provisional classification |
|---|---:|---|---|
| Lines of promotions 1, 4, and 7 outside their recorded dates | 178 | Likely wrong end dates, from the orders and budgets, to confirm with the approved calendar | Possible date-validation or calendar-maintenance weakness: promotions 4 and 7 end before they start, and promotion 1 is a one-day window that does not contain the observed orders. Obtain the authorized calendar, change history and validation rules to distinguish design from operation |
| Lines outside their scope | 2 | Likely an incomplete item master, to confirm from the item's classification and the approved scope | Possibly design: scope is read from an incomplete master |
| Rate differs | 0 | None found on the promotion lines | None |
| Lines missing the promotion | 0 | Unresolved on the recorded dates of promotions 1, 4, and 7 (no eligible line). None in their provisional windows or in the other promotions | Not assessed until the calendar and item classification are confirmed |
| Approvals by one employee | 409 | One recorded approver, own requests approved, no finance approval | Design if no rule requires an independent approver, operation if one does |
| Pending requests billed | 3 | Billed with no completed approval in this extract | Possible approval-workflow weakness: no completed approval is recorded in this extract. Obtain approval history and billing timestamps to determine whether billing preceded authorization |
| Promotions on override prices | 34 | A policy question | Possibly design: no stacking rule is recorded |

**Step 8. List the conditions for any promotion in 2027.** Validated dates (no end date before the start, a rule on whether a promotion may last one day, and dates matching the months meant to run); complete collection data; approval by finance as well as sales; independent approval of overrides, with billing waiting for it; a stacking rule; and a post-promotion review against a stated expectation, with the cost shown in a gross-to-net schedule.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions failing the date test; their lines | 1, 4, and 7; 178 | 1 |
| Lines outside scope; rate exceptions | 2; 0 | 1 |
| Eligible lines in the provisional windows of promotions 1, 4, and 7; missing the promotion; eligible on the recorded dates | 59, 63, 54; 0; none | 2 |
| Approved overrides; the approver's own; pending requests and their billed lines | 409; 106; 2, 165, 294, four lines | 5 |
| Stacked order lines; billed lines; discount | 34; 45; $16,006.78 | 6 |

> **Instructor notes, Requirement 5:** dates: every line of promotions 1 (Alder, recorded 2024-03-01 to 2024-03-01), 4 (Brookside, 2025-03-01 to 2025-02-27), and 7 (Harbor, 2026-03-01 to 2026-02-28) fails, and every line of the other six passes (Exercise 8.6). Promotion 1 starts and ends on the same day, which a policy could allow, while promotions 4 and 7 end before they start. All their lines were ordered between March 1 and April 30, every collection line of those months carries the promotion, and each year's budget planned the discount then, which suggests a wrong end date rather than discounts given without authority, to be confirmed by the approved campaign calendar and the change history. The generator's AnomalyLog is not evidence an auditor would have. Scope: two promotion 1 order lines (SalesOrderLineIDs 1249 and 2142) are on item 11, FUR-CON-0003, the Alder Console Table, whose CollectionName is blank, which suggests an incomplete item master rather than a wrong discount (FUR-SDB-0002 (Willow) and FUR-DSK-0004 (Summit) also lack one). Rate: every promotion line carries its promotion's DiscountPct. Completeness, from all order lines: the recorded dates of promotions 1, 4, and 7 hold no line of their scopes, so that result is unresolved, not a clearance. On the March-April windows, a provisional test, all 59 Alder, 63 Brookside, and 54 Harbor lines in scope carry the promotion, and the other promotions pass on their recorded dates. Approvals: EmployeeID 6 (Carrie Schultz, Sales Manager) approved all nine promotions, each on its start date, and all 409 approved override requests, 106 of them the manager's own. The manager's three other requests are still Pending (IDs 2, 165, 294), yet they were billed with no completed approval in this extract and no override link on the lines. No approval by anyone in finance is recorded. Stacking: 34 order lines (45 billed) carry both an approved override and a promotion, 16,006.78 of discount. Provisional classification: a possible date-validation or calendar-maintenance weakness for the dates, possible design weaknesses for the scope and the stacking, design or operation for the self-approvals depending on whether a rule required an independent approver, and a possible approval-workflow weakness for the Pending requests billed, since no completed approval is recorded in this extract. The system's configuration, the authority matrix, the approval history and the billing times would settle each.

## What a strong answer says

- **Tests.** Counts by promotion for all four conditions, with the guard, completeness from all order lines, and the recorded-date result kept as unresolved.
- **The date exceptions.** Evidence from the order months and the budgets, and a master-data error judged more likely than unauthorized discounts, with its limits.
- **Scope.** The item master as the likely weak point, the record that would confirm it, and the other items named.
- **Approvals and conditions.** One person on promotions and overrides, own requests, pending requests billed, no finance review, classified provisionally, and each condition tied to an exception.

A weak answer lists exceptions without causes, blames the manager, or calls every exception a failure of operation.

## Common mistakes and how to respond

- **No guard, or one scope column.** *Symptom:* a date exception count of about 20,797, or every collection and segment line outside scope. *Response:* ask what a line with no promotion is tested against, and which column defines each kind.
- **A vacuous completeness test.** *Symptom:* zero exceptions for promotions 1, 4, and 7 on their recorded dates. *Response:* ask how many lines the test examined.
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
