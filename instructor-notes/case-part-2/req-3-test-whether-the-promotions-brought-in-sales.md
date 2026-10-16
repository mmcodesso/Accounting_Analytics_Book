# Requirement 3: Test whether the promotions brought in sales (Chapters 6 and 7)

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Item | Requirement 3 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | PartII-case.zip: Charles River Promotion Case.xlsx, sheets R3 Volume and R3 Customers, with the queries OrderLines, Promotions and Customers |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 3 tests the sales team's first argument, that promotions bring in sales that would not otherwise be made, and its second, that they bring in new customers. It is the case's inference requirement: students must decide when a difference counts as an increase, which they can do only by comparing it with the variation the data shows when nothing special happens. The analytics type is diagnostic, since the work tests a claimed cause.

By the end, students can:

- find the months in which a promotion ran from its transactions and compare them with its recorded dates;
- measure volume at constant prices and explain why net revenue would mislead;
- compare a promotion's months with two expectations and judge the difference against the scope's variation, like for like;
- test a claim about new customers from first orders and say what the start of the data limits.

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis) and BAR M8 (planning techniques, forecasting and decision models); IMA Data Analytics and Insights (statistical analysis) and Decision Analysis; IFAC IES 2 (b), management accounting, and IES 3 (a), evaluating information from several sources; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** `OrderLines` from Requirement 1, with OrderYear, OrderMonth and ListAmount. From Chapter 7, the two expectations (the average of the other months, and the same period a year earlier) and Tutorial 7.3 Step 7, which looked at one promotion's orders in a PivotTable.
- **Data conditions.** Each promotion's lines were ordered in one calendar year, in two months for collections and item groups and in one month for segments, and the recorded dates of promotions 1, 4, and 7 do not contain them (Requirement 5). The data begins in 2024, so promotions 1, 2, and 3 have no year earlier to compare with. Scope depends on the kind: Items.CollectionName for a collection, Items.ItemGroup for an item group, Customers.CustomerSegment for a segment.
- **The customer test.** Of the customers, 211 ordered; the 9 that never did are inactive. The Customers table carries a CustomerSince that does not match the orders.

## How to run it

Individual or pairs, about 90 minutes: 15 for the months and scope, 25 for the monthly grids, 25 for the comparison, 20 for the customers and 5 to write the conclusion. Ask "is that big?" about the largest difference before giving any hint about variation. If a student compares a two-month total's difference with one month's standard deviation, ask them to compare like with like, the promotion's average month with the other months or the total with the variation scaled to its months. **Collect** the comparison table, which is Exhibit 3 of the memo.

![A mock of the comparison table of the volume test, one row for each promotion.](../figures/case-part-2/IF-C2-3-A.pdf)

## Step-by-step solution

### Phase 1: When each promotion ran

**Step 1. List the promotions with their months and scope.** On a worksheet named `R3 Volume`, list the PromotionIDs and look up each promotion's name, ScopeType, scope (the Promo column that is not blank), rate and recorded dates in `Promotions`. Beside them put the order dates of its lines and the months they cover:

```
=MINIFS(OrderLines[OrderDate],OrderLines[PromotionID],A5)
=MAXIFS(OrderLines[OrderDate],OrderLines[PromotionID],A5)
=COUNTIFS(OrderLines[PromotionID],A5,OrderLines[OrderDate],">="&F5,OrderLines[OrderDate],"<="&G5)
```

with the first, last and number of months from MONTH, and the last formula counting the lines inside the recorded dates.

**Check:**

| Promotion | Kind | Scope | Months of its orders | Recorded dates |
|---|---|---|---|---|
| 1 | collection | Alder | March and April | 2024-03-01 to 2024-03-01 |
| 2 | item group | Accessories | September and October | 2024-09-01 to 2024-10-31 |
| 3 | segment | Strategic | November | 2024-11-01 to 2024-11-30 |
| 4 | collection | Brookside | March and April | 2025-03-01 to 2025-02-27 |
| 5 | item group | Textiles | September and October | 2025-09-01 to 2025-10-31 |
| 6 | segment | Wholesale | November | 2025-11-01 to 2025-11-30 |
| 7 | collection | Harbor | March and April | 2026-03-01 to 2026-02-28 |
| 8 | item group | Furniture | September and October | 2026-09-01 to 2026-10-31 |
| 9 | segment | Design Trade | November | 2026-11-01 to 2026-11-30 |

Promotions 1, 4, and 7 have no line inside their recorded dates; their months come from the orders.

### Phase 2: Volume by month

**Step 2. Total the scope's list amount for each month of the promotion's year.** One row for each promotion and a column for each month, 1 to 12. The scope column depends on the kind, so one formula chooses it:

```
=SUMIFS(OrderLines[ListAmount],CHOOSE(MATCH($B17,{"Collection","ItemGroup","Segment"},0),OrderLines[CollectionName],OrderLines[ItemGroup],OrderLines[CustomerSegment]),$C17,OrderLines[OrderYear],$D17,OrderLines[OrderMonth],E$16)
```

Columns B, C and D hold the kind, the scope and the year. CHOOSE and MATCH are not taught in Chapters 4 to 8; an IF on the kind that picks one of three SUMIFS does the same. A PivotTable on `OrderLines` gives the same numbers, with the scope field in **Filters**, OrderYear in **Rows**, OrderMonth in **Columns** and ListAmount in **Values**; the scope must be a PivotTable filter, because a PivotTable ignores the worksheet's own filters.

**Step 3. Repeat for the year before.** Use the same formula with the year less one, wrapped as `=IF($D29<FirstYear,"",...)`, so that the first year's promotions show a blank.

**Check:** the first-year promotions (1, 2, and 3) have an empty prior grid, not zeros.

### Phase 3: The comparison

**Step 4. Compare each promotion with its two expectations.** For the promotion in grid row 17 and calendar row 5 (columns L and M hold its first and last month), with the months in row 16:

```
Volume in its months:   =SUMPRODUCT((($E$16:$P$16>=$L5)*($E$16:$P$16<=$M5))*$E17:$P17)
Expectation:            =AVERAGE(FILTER($E17:$P17,($E$16:$P$16<$L5)+($E$16:$P$16>$M5)))*C41
Difference:             =D41/E41-1
Normal variation:       =STDEV.S(FILTER($E17:$P17,($E$16:$P$16<$L5)+($E$16:$P$16>$M5)))
Average month, in SDs:  =(D41-E41)/(C41*I41)
In standard deviations: =(D41-E41)/(I41*SQRT(C41))
```

The first of the last two compares the promotion's average month with the other months' mean, in monthly standard deviations, and needs only Chapter 6's STDEV.S. The model answer uses the second, which scales the monthly standard deviation by the square root of the number of months. That scaling assumes independent, comparable months and is not taught in Chapters 4 to 8, so accept either; here they give the same verdict.

The year-earlier column is the same SUMPRODUCT on the prior grid, divided into the volume. A student without FILTER can blank the promotion's months in a helper row (`=IF(AND(month>=first,month<=last),"",value)`), because AVERAGE and STDEV.S ignore the empty text.

**Check:**

| Promotion | Months | Against other months | Against a year earlier | Monthly variation | Average month, SDs | Total, SDs |
|---|---:|---:|---:|---:|---:|---:|
| 1 Alder | 2 | -3.3% | n/a | 14.2% | -0.23 | -0.33 |
| 2 Accessories | 2 | +11.9% | n/a | 10.2% | 1.17 | 1.65 |
| 3 Strategic | 1 | -20.7% | n/a | 18.4% | -1.12 | -1.12 |
| 4 Brookside | 2 | -15.4% | -9.8% | 19.2% | -0.80 | -1.13 |
| 5 Textiles | 2 | -5.8% | -5.9% | 10.3% | -0.57 | -0.81 |
| 6 Wholesale | 1 | +2.5% | +0.9% | 9.5% | 0.27 | 0.27 |
| 7 Harbor | 2 | +0.4% | -21.1% | 14.3% | 0.03 | 0.04 |
| 8 Furniture | 2 | +0.3% | +2.9% | 4.6% | 0.08 | 0.11 |
| 9 Design Trade | 1 | +3.1% | -17.1% | 18.0% | 0.17 | 0.17 |

The differences run from -20.7% to +11.9%. None is beyond two standard deviations either way. The largest, promotion 2 (Accessories), is about 1.2 for its average month and 1.6 standard deviations of a two-month total (the monthly sd times the square root of 2). Read this as an informal screen, not a test of significance, because seasonality, other promotions in the other months and the choice of the largest of several results all limit it. Every difference is far below its promotion's break-even increase (Requirement 4).

**Watch for:** a two-month total's difference compared with one month's standard deviation, which puts promotion 2 beyond two. Comparing the average month, or scaling the deviation by the square root of the months, is the fix.

### Phase 4: New customers

**Step 5. Find each customer's first order.** On `R3 Customers`:

```
=SORT(UNIQUE(OrderLines[CustomerID]))
=MINIFS(OrderLines[OrderDate],OrderLines[CustomerID],A5#)
=COUNTIFS(OrderLines[CustomerID],A5#,OrderLines[OrderDate],B5#,OrderLines[PromotionID],"<>")>0
```

Look up CustomerSince and name, and summarize: customers who ordered, first orders that included a promotion line, first orders in the first four months of the data, first orders after June of the first year, and the last first order.

**Check:** 211 customers ordered, and zero first orders included a promotion line. Of the first orders, 195 fall in the first four months of the data (107 in the first month), only because the data begins then: customers who had bought before appear as new. Just seven came after June 2024, the last in July 2025. Of the 31 customers with a CustomerSince in 2024 or later, 27 placed their first order before that date, so CustomerSince cannot date a first purchase.

**Step 6. State the conclusion.** No difference is beyond the scope's normal variation or near its break-even increase, and no customer's first order came through a promotion. The comparisons describe the orders and cannot show what would have been ordered without a promotion, which a comparison group or a designed test would need. The data cannot show that promotions never attract customers either, because almost no new customers appear in it. The evidence gives the sales team's two arguments no support, which is not proof that the promotions had no effect.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions whose recorded dates contain none of their lines | 1, 4, and 7 | 1 |
| Largest and smallest difference; the largest in standard deviations | +11.9%; -20.7%; 1.6 | 4 |
| Customers who ordered; first orders with a promotion line | 211; 0 | 5 |
| CustomerSince in the first year or later; first order earlier | 31; 27 | 5 |

> **Instructor notes, Requirement 3:** every promotion's lines were ordered within two calendar months (collections March-April, item groups September-October) or one (segments, November). Promotions 1, 4, and 7 have recorded dates that cannot be right (see Requirement 5). The list amount holds price constant, so it moves only with quantity and mix; the net amount falls by the discount itself. Volume in the promotion's months against the average of the other months of the same year (against the same months a year earlier), with the other months' standard deviation (STDEV.S) as a percentage of their mean: 1 Alder -3.3% (sd 14.2%); 2 Accessories +11.9% (10.2%); 3 Strategic -20.7% (18.4%); 4 Brookside -15.4% (-9.8%; 19.2%); 5 Textiles -5.8% (-5.9%; 10.3%); 6 Wholesale +2.5% (+0.9%; 9.5%); 7 Harbor +0.4% (-21.1%; 14.3%); 8 Furniture +0.3% (+2.9%; 4.6%); 9 Design Trade +3.1% (-17.1%; 18.0%). No difference is unusual: the largest, promotion 2's +11.9%, is about 1.6 standard deviations of a two-month total (the monthly sd times the square root of 2), and promotion 3's fall is within the Strategic segment's normal swings. Every difference is far below the promotion's break-even increase (Requirement 4, which asks for the three proposed promotions and leaves the other six as corroboration). This is an informal screen, not a test of significance, because it assumes comparable, independent months, and the other months can carry seasonality or other promotions. Compared month for month (the promotion's average month against the other months' mean, in monthly standard deviations, which Chapter 6's STDEV.S supports), the largest is about 1.2, and either route is acceptable. The comparisons describe the orders and cannot show what would have been ordered without a promotion, so the answer is no evidence of an increase near the break-even, not proof of none, and a comparison group or a designed test would be needed to measure one. New customers: 211 customers ordered, and no customer's first order in the data included a promotion line. First orders cluster in January to April 2024 only because the data begins in January 2024, and just seven first orders came after June 2024 (the last in July 2025). Students should not rely on CustomerSince: for 27 of the 31 customers with a CustomerSince in 2024 or later, the first order came before that date.

## What a strong answer says

- **When and what.** The months and scope of each promotion from the order dates, with the recorded dates shown to disagree for 1, 4, and 7.
- **Why list amount.** It holds price constant, so it moves only with quantity and mix; the net amount falls by the discount itself and follows the invoice date.
- **The judgment.** Each difference against its expectation and the scope's variation, none unusual on this informal screen and all far below break-even.
- **The customers.** No promotional first order, with the limits of data that begins in 2024 and an unreliable CustomerSince.
- **Humility.** The result is the absence of evidence of a lift, not proof of none.

A weak answer calls the largest difference a success, or calls every difference a failure, without the standard deviation.

## Common mistakes and how to respond

- **Net amount as volume.** *Symptom:* nearly every promotion shows a fall, from -30.2% to +0.9%, with 1 above zero. *Response:* ask what the discount does to LineTotal in the promotion's months.
- **Variation not scaled.** *Symptom:* promotion 2 flagged as unusual. *Response:* ask what a two-month total's variation is, against one month's.
- **Recorded dates for the months.** *Symptom:* little or no volume in the months of promotions 1, 4, and 7. *Response:* ask which lines carry the promotion, and when they were ordered.
- **No guard on the year before.** *Symptom:* a division error or a nonsense fall for promotions 1, 2, and 3. *Response:* ask what the data holds before 2024.
- **CustomerSince as the first purchase.** *Symptom:* a count of new customers. *Response:* have them compare it with the first order date.
- **Overclaiming.** *Symptom:* "promotions do not work". *Response:* ask what this data could and could not show.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Months and scope | 15 | Each promotion's months, scope and the date disagreement | Months from the recorded dates |
| Volume measure | 20 | List amount by month and the reason | Net amount, or no reason |
| The comparison | 30 | Both expectations, each difference compared like for like with the monthly variation | One expectation, or no variation |
| New customers | 20 | First orders, promotion flag, and the limits of the data | Flag without limits |
| Conclusion | 15 | Stated with its scope and humility | Overclaimed in either direction |

## Extensions and discussion questions

- Repeat the comparison with the order count instead of the list amount, and say whether a promotion could change the mix without changing the total.
- Discuss: an increase of about a tenth in the best month is inside the normal variation. What size of increase could this data detect?
- Discuss: how would a control group (a similar scope with no promotion) make the next test stronger? This leads into the model of Requirement 4.
