---
note: case2.r3
uses: [case2.g3]
title: Test whether the promotions brought in sales (Chapters 6 and 7)
kind: requirement
number: '3'
unit: case2
perspective: managerial
tool: excel
minutes: 90
solution: "PartII-case.zip: Charles River Promotion Case.xlsx, sheets R3 Volume and R3 Customers, with the queries OrderLines, Promotions and Customers"
figures:
  - id: IF-C2-3-A
    kind: excel-mock
    purpose: The comparison table of the volume test, one row for each promotion.
    shows: "A worksheet block with a row for each promotion and the columns Months, Volume in the promotion's months, Expectation, Difference, The same months a year earlier, Difference from a year earlier, Standard deviation of the other months, Difference in standard deviations and Beyond two standard deviations. The largest and smallest differences are outlined, the first-year promotions read n/a for the year earlier, and every last cell reads FALSE."
    data: The Expected results of this requirement (volume by promotion and month from OrderLines, ListAmount).
---
{% set x = case2_g3 %}
# Requirement 3: Test whether the promotions brought in sales (Chapters 6 and 7)

{{ header() }}

## Purpose and learning outcomes

Requirement 3 tests the sales team's first argument, that promotions bring in sales that would not otherwise be made, and its second, that they bring in new customers. It is the case's inference requirement: students must decide when a difference counts as an increase, which they can do only by comparing it with the variation the data shows when nothing special happens. The analytics type is diagnostic, since the work tests a claimed cause.

By the end, students can:

- find the months in which a promotion ran from its transactions and compare them with its recorded dates;
- measure volume at constant prices and explain why net revenue would mislead;
- compare a promotion's months with two expectations and judge the difference against the scope's variation, scaled to the number of months;
- test a claim about new customers from first orders and say what the start of the data limits.

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis) and BAR M8 (planning techniques, forecasting and decision models); IMA Data Analytics and Insights (statistical analysis) and Decision Analysis; IFAC IES 2 (b), management accounting, and IES 3 (a), evaluating information from several sources; AACSB A5 part 5.1.

## Before you assign

- **From earlier work.** `OrderLines` from Requirement 1, with OrderYear, OrderMonth and ListAmount. From Chapter 7, the two expectations (the average of the other months, and the same period a year earlier) and Tutorial 7.3 Step 7, which looked at one promotion's orders in a PivotTable.
- **Data conditions.** Each promotion's lines were ordered in one calendar year, in two months for collections and item groups and in one month for segments, and the recorded dates of promotions {{ bad }} do not contain them (Requirement 5). The data begins in {{ x.first_year }}, so promotions {{ x.no_py }} have no year earlier to compare with. Scope depends on the kind: Items.CollectionName for a collection, Items.ItemGroup for an item group, Customers.CustomerSegment for a segment.
- **The customer test.** Of the customers, {{ customers }} ordered; the {{ x.never }} that never did are inactive. The Customers table carries a CustomerSince that does not match the orders.

## How to run it

Individual or pairs, about 90 minutes: 15 for the months and scope, 25 for the monthly grids, 25 for the comparison, 20 for the customers and 5 to write the conclusion. Ask "is that big?" about the largest difference before giving any hint about variation. Hold back the scaling by the square root of the months until a student calls a promotion unusual. **Collect** the comparison table, which is Exhibit 3 of the memo.

{{ figure('IF-C2-3-A') }}

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
{% for r in x.rows %}
| {{ r.id }} | {{ r.kind }} | {{ r.label }} | {{ r.ran }} | {{ r.recorded_start }} to {{ r.recorded_end }} |
{% endfor %}

Promotions {{ bad }} have no line inside their recorded dates; their months come from the orders.

### Phase 2: Volume by month

**Step 2. Total the scope's list amount for each month of the promotion's year.** One row for each promotion and a column for each month, 1 to 12. The scope column depends on the kind, so one formula chooses it:

```jinja
=SUMIFS(OrderLines[ListAmount],CHOOSE(MATCH($B{{ x.cmp.grid }},{"Collection","ItemGroup","Segment"},0),OrderLines[CollectionName],OrderLines[ItemGroup],OrderLines[CustomerSegment]),$C{{ x.cmp.grid }},OrderLines[OrderYear],$D{{ x.cmp.grid }},OrderLines[OrderMonth],E${{ x.cmp.grid_head }})
```

Columns B, C and D hold the kind, the scope and the year. CHOOSE and MATCH are not taught in Chapters 4 to 8; an IF on the kind that picks one of three SUMIFS does the same. A PivotTable on `OrderLines` gives the same numbers, with the scope field in **Filters**, OrderYear in **Rows**, OrderMonth in **Columns** and ListAmount in **Values**; the scope must be a PivotTable filter, because a PivotTable ignores the worksheet's own filters.

**Step 3. Repeat for the year before.** Use the same formula with the year less one, wrapped as `=IF($D{{ x.cmp.prior }}<FirstYear,"",...)`, so that the first year's promotions show a blank.

**Check:** the first-year promotions ({{ x.no_py }}) have an empty prior grid, not zeros.

### Phase 3: The comparison

**Step 4. Compare each promotion with its two expectations.** For the promotion in grid row {{ x.cmp.grid }} and calendar row {{ x.cmp.cal }} (columns L and M hold its first and last month), with the months in row {{ x.cmp.grid_head }}:

```jinja
Volume in its months:   =SUMPRODUCT((($E${{ x.cmp.grid_head }}:$P${{ x.cmp.grid_head }}>=$L{{ x.cmp.cal }})*($E${{ x.cmp.grid_head }}:$P${{ x.cmp.grid_head }}<=$M{{ x.cmp.cal }}))*$E{{ x.cmp.grid }}:$P{{ x.cmp.grid }})
Expectation:            =AVERAGE(FILTER($E{{ x.cmp.grid }}:$P{{ x.cmp.grid }},($E${{ x.cmp.grid_head }}:$P${{ x.cmp.grid_head }}<$L{{ x.cmp.cal }})+($E${{ x.cmp.grid_head }}:$P${{ x.cmp.grid_head }}>$M{{ x.cmp.cal }})))*C{{ x.cmp.cmp }}
Difference:             =D{{ x.cmp.cmp }}/E{{ x.cmp.cmp }}-1
Normal variation:       =STDEV.S(FILTER($E{{ x.cmp.grid }}:$P{{ x.cmp.grid }},($E${{ x.cmp.grid_head }}:$P${{ x.cmp.grid_head }}<$L{{ x.cmp.cal }})+($E${{ x.cmp.grid_head }}:$P${{ x.cmp.grid_head }}>$M{{ x.cmp.cal }})))
In standard deviations: =(D{{ x.cmp.cmp }}-E{{ x.cmp.cmp }})/(I{{ x.cmp.cmp }}*SQRT(C{{ x.cmp.cmp }}))
```

The year-earlier column is the same SUMPRODUCT on the prior grid, divided into the volume. A student without FILTER can blank the promotion's months in a helper row (`=IF(AND(month>=first,month<=last),"",value)`), because AVERAGE and STDEV.S ignore the empty text.

**Check:**

| Promotion | Months | Against other months | Against a year earlier | Monthly variation | Standard deviations |
|---|---:|---:|---:|---:|---:|
{% for r in x.rows %}
| {{ r.id }} {{ r.label }} | {{ r.n_months }} | {{ r.lift|spct }} | {{ 'n/a' if r.py is none else r.py|spct }} | {{ r.sd|pct(1) }} | {{ r.z|num(2) }} |
{% endfor %}

The differences run from {{ x.lift_low|spct }} to {{ x.lift_high|spct }}. None is beyond two standard deviations: the largest, promotion {{ top.id }} ({{ top.label }}), is about {{ top.z|num(1) }} standard deviations of a {{ sd_total }}. Every difference is far below its promotion's break-even increase (Requirement 4).

**Watch for:** the variation not scaled to the months. A two-month total compared with one month's standard deviation puts promotion {{ x.naive_flagged }} beyond two. Multiplying the monthly standard deviation by the square root of the number of months is the fix, because a total of independent months varies by about that factor.

### Phase 4: New customers

**Step 5. Find each customer's first order.** On `R3 Customers`:

```
=SORT(UNIQUE(OrderLines[CustomerID]))
=MINIFS(OrderLines[OrderDate],OrderLines[CustomerID],A5#)
=COUNTIFS(OrderLines[CustomerID],A5#,OrderLines[OrderDate],B5#,OrderLines[PromotionID],"<>")>0
```

Look up CustomerSince and name, and summarize: customers who ordered, first orders that included a promotion line, first orders in the first four months of the data, first orders after June of the first year, and the last first order.

**Check:** {{ customers }} customers ordered, and {{ n_promoted }} first orders included a promotion line. Of the first orders, {{ x.early }} fall in the first four months of the data ({{ x.jan }} in the first month), only because the data begins then: customers who had bought before appear as new. Just {{ late }} came after June {{ x.first_year }}, the last in {{ last }}. Of the {{ since }} customers with a CustomerSince in {{ x.first_year }} or later, {{ since_before }} placed their first order before that date, so CustomerSince cannot date a first purchase.

**Step 6. State the conclusion.** The differences show no sign of an increase, and no customer's first order came through a promotion. The data cannot show that promotions never attract customers, because almost no new customers appear in it, and the comparison cannot show what orders would have been without the promotion. It gives the sales team's two arguments no support.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Promotions whose recorded dates contain none of their lines | {{ bad }} | 1 |
| Largest and smallest difference; the largest in standard deviations | {{ x.lift_high|spct }}; {{ x.lift_low|spct }}; {{ top.z|num(1) }} | 4 |
| Customers who ordered; first orders with a promotion line | {{ customers }}; {{ promoted }} | 5 |
| CustomerSince in the first year or later; first order earlier | {{ since }}; {{ since_before }} | 5 |

{{ expected() }}

## What a strong answer says

- **When and what.** The months and scope of each promotion from the order dates, with the recorded dates shown to disagree for {{ bad }}.
- **Why list amount.** It holds price constant, so it moves only with quantity and mix; the net amount falls by the discount itself and follows the invoice date.
- **The judgment.** Each difference against its expectation and the scope's variation: none unusual, all far below break-even.
- **The customers.** No promotional first order, with the limits of data that begins in {{ x.first_year }} and an unreliable CustomerSince.
- **Humility.** The result is the absence of evidence of a lift, not proof of none.

A weak answer calls the largest difference a success, or calls every difference a failure, without the standard deviation.

## Common mistakes and how to respond

- **Net amount as volume.** *Symptom:* nearly every promotion shows a fall, from {{ x.net_low|spct }} to {{ x.net_high|spct }}, with {{ x.n_net_up }} above zero. *Response:* ask what the discount does to LineTotal in the promotion's months.
- **Variation not scaled.** *Symptom:* promotion {{ x.naive_flagged }} flagged as unusual. *Response:* ask what a two-month total's variation is, against one month's.
- **Recorded dates for the months.** *Symptom:* little or no volume in the months of promotions {{ bad }}. *Response:* ask which lines carry the promotion, and when they were ordered.
- **No guard on the year before.** *Symptom:* a division error or a nonsense fall for promotions {{ x.no_py }}. *Response:* ask what the data holds before {{ x.first_year }}.
- **CustomerSince as the first purchase.** *Symptom:* a count of new customers. *Response:* have them compare it with the first order date.
- **Overclaiming.** *Symptom:* "promotions do not work". *Response:* ask what this data could and could not show.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Months and scope | 15 | Each promotion's months, scope and the date disagreement | Months from the recorded dates |
| Volume measure | 20 | List amount by month and the reason | Net amount, or no reason |
| The comparison | 30 | Both expectations, variation scaled, difference in standard deviations | One expectation, or no variation |
| New customers | 20 | First orders, promotion flag, and the limits of the data | Flag without limits |
| Conclusion | 15 | Stated with its scope and humility | Overclaimed in either direction |

## Extensions and discussion questions

- Repeat the comparison with the order count instead of the list amount, and say whether a promotion could change the mix without changing the total.
- Discuss: an increase of about a tenth in the best month is inside the normal variation. What size of increase could this data detect?
- Discuss: how would a control group (a similar scope with no promotion) make the next test stronger? This leads into the model of Requirement 4.
