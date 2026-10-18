---
note: ch18.r8
uses: [ch18.g8]
title: Reprice the families below the floor (Chapter 7)
kind: requirement
number: '8'
unit: '18'
perspective: managerial
tool: mixed
minutes: 120
solution: "Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Prices; Chapter18-capstone-sql.zip: MakeBuy.sql, Q24 to Q26"
figures:
  - id: IF-18-8-A
    kind: excel-mock
    purpose: The Prices sheet's table of floor prices, increases and the volume each increase can lose.
    shows: "One row for each manufactured family with units, price, time-driven cost and margin, a Below the floor flag, the target price, the increase, the contribution per unit, the volume the increase can lose and the revenue a year; the rows below the floor are outlined, and a totals block below the table."
    data: The Prices sheet of the model workbook, the first table and its totals.
---
{% set g = ch18_g8 %}
{% set ex = (reprice|selectattr('short', 'equalto', g.example)|list)[0] %}
{% set mk = (g.mk|selectattr('short', 'equalto', g.example)|list)[0] %}
{% set ltd = (g.loss_td|selectattr('short', 'equalto', g.example)|list)[0] %}
# Requirement 8: Reprice the families below the floor (Chapter 7)

{{ header() }}

## Purpose and learning outcomes

A price increase is judged by the volume it can afford to lose, and that threshold is not a forecast. The requirement asks students to find the floor price of each family, measure the contribution at stake over the costs that stop, and set the result against what the records show about how customers respond to price, including the dates and use of the price lists. SQL extracts the order and price-list evidence, Excel does the pricing arithmetic. The analytics type is predictive, with a prescriptive recommendation.

Students can:

- find each family's floor price with Goal Seek, the increase it needs and the share of volume it can lose (Part 1);
- screen past promotions for a volume response and check the price lists, and say what the evidence cannot show (Part 2);
- recommend increases and how the lists should be rebuilt, and show what changes for the families bought (Part 3).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning, and Performance (decision analysis); IFAC IES 2 (b); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with the family costs of Requirement 4 and the decisions of Requirement 6, and MakeBuy.sql on CharlesRiver_Capstone.sqlite.
- **Data conditions.** The floor is the case's assumption, a margin on time-driven cost before unused capacity. Promotion lines carry a PromotionID; {{ g.n_inverted|count }} of the {{ g.n_q24|count }} promotions have an end date on or before their start (a master-data error), so their months come from the orders. The price lists are in PriceList and PriceListLine, and overrides in PriceOverrideApproval.
- **Verify first.** {{ g.n_below|capitalize }} families fall below the floor, and the increases bring in ${{ revenue|num(0) }} a year if volume holds.

## How to run it

Individual or pairs, about 120 minutes: 40 for the floor prices and thresholds, 40 for the evidence and its queries, 25 for the recommendation, 15 for documentation. Hold back the interpretation of the promotion screen until students have the lifts. **Collect** the Prices sheet and the three queries.

## Step-by-step solution

### Part 1: Floor prices and the volume each increase can lose

**Step 1. Flag the families below the floor.** On the Prices sheet each family's row looks up its units, price and time-driven cost from the Costs sheet.

```jinja
Margin        {{ g.f.margin }}
Below floor   {{ g.f.below }}
```

**Check:** {{ g.n_below }} families have a margin below the floor; {{ g.example }} reads {{ g.ex.margin|pct(1) }}.

**Step 2. Find each floor price with Goal Seek.** The sheet gives a target price cell (G) and a check cell (H) that returns the family's margin above the floor, in dollars a year.

a. Choose **Data > What-If Analysis > Goal Seek**.
b. Enter H6 in **Set cell**, `0` in **To value** and G6 in **By changing cell**, and repeat for each family below the floor.
c. Compare with column I, which computes the same price directly.{% if g.agrees %} The increase, the volume it can lose and the revenue read column I, so they follow the floor and the costs, and column O says whether the Goal Seek result still agrees.{% endif %}

```jinja
Check      {{ g.f.check }}
Direct     {{ g.f.direct }}
```

**Check:** {{ g.example }} reaches the floor at ${{ g.ex.new|num(2) }}, against ${{ g.ex.price|num(2) }} today. **Watch for:** a markup on cost instead of a margin on price: marking the cost up by the floor percentage gives a price below today's for every family ({{ g.example }} {{ mk.incr|pct(1) }}), and the margin at that price is under the floor.

**Step 3. Compute the increase and the volume it can lose.** Contribution is measured over the relevant cost with the crew kept. The volume the increase can lose is one minus the contribution per unit now, over that contribution plus the increase per unit: beyond it the family earns less contribution than today.

```jinja
Increase      {{ g.f.incr }}
Contribution  {{ g.f.contrib }}
Volume lost   {{ g.f.loss }}
```

**Check:** {{ g.example }} needs {{ ex.increase|pct(2) }} and can lose {{ ex.loss|pct(1) }} of its volume; the table of Expected results gives the rest. **Watch for:** contribution over the time-driven cost: {{ g.example }} then reads {{ ltd.loss|pct(1) }} against {{ ex.loss|pct(1) }}, an overstated threshold, because the committed costs inside the time-driven cost stay when volume is lost.

{{ figure('IF-18-8-A') }}

### Part 2: What the records say about customers' response

**Step 4. Screen the promotions for a volume response (Q24).** Routine: type the query at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Q24 sums the list-price order value of each promotion's scope by month of its year, a list-price-weighted order-value proxy for volume; the months of the promotion are the months in which promotion lines were ordered. The block is a fragment, the `PromotionMonths` column, and the complete statement is Q24:

```sql
(SELECT GROUP_CONCAT(M, ',')
     FROM (SELECT DISTINCT CAST(SUBSTR(o.OrderDate, 6, 2) AS INTEGER) AS M
           FROM Orders AS o
           WHERE o.PromotionID = p.PromotionID
           ORDER BY M)) AS PromotionMonths,
```

Paste the result into the Table PromotionVolume and add the columns that compare the promotion's months with the year's other months:

```jinja
Expected   {{ g.f.expected }}
Lift       {{ g.f.lift }}
Z          {{ g.f.z }}
```

**Check:** {{ g.n_q24|count }} rows, one for each promotion. No lift passes the descriptive z of 2 screen (the largest, {{ top.label }} {{ top.year }}, reads {{ top.z|num(2) }}); {{ n_up }} of the {{ n_promos }} are positive and {{ n_down }} negative, down to {{ lowest|pct(1) }}. **Watch for:** months taken from the effective dates: {{ g.n_before|count }} promotions end before they start and so have no months at all, and one ends on its start date, which gives one month although its orders ran for two.

**Step 5. Check the price lists and the overrides (Q25 and Q26).** Q25 returns each list with its dates, the range of its prices against list, and the count of order lines priced after its end date. The block is a fragment, the last column, and the complete statement is Q25:

```sql
(SELECT COUNT(*)
     FROM SalesOrderLine AS sol
        INNER JOIN SalesOrder AS so ON so.SalesOrderID = sol.SalesOrderID
        INNER JOIN PriceListLine AS pll
            ON pll.PriceListLineID = sol.PriceListLineID
     WHERE pll.PriceListID = pl.PriceListID
        AND so.OrderDate > pl.EffectiveEndDate) AS OrderLinesAfterEnd
```

```sql
-- Requirement 8, Q26: approved price overrides by the approver's job title
-- Population: PriceOverrideApproval, status Approved; expected: one approver
SELECT e.JobTitle AS ApproverJobTitle, COUNT(*) AS ApprovedOverrides
FROM PriceOverrideApproval AS poa
    INNER JOIN Employee AS e ON e.EmployeeID = poa.ApprovedByEmployeeID
WHERE poa.Status = 'Approved'
GROUP BY e.JobTitle
ORDER BY ApprovedOverrides DESC;
```

**Check:** {{ g.n_q25|count }} lists. The active lists run at {{ low|num(2) }} to {{ high|num(2) }} of list and all end on {{ g.end_date }}; lists {{ expired|join(', ') }} are expired, and {{ g.lines_after|count }} order lines were priced from them after their end dates. One approver, the {{ g.approver }}, approved {{ g.approved|count }} overrides. **Watch for:** treating a z below 2 as proof that customers do not respond: the screen reads list-price order value in the promotions' months, which seasonality, mix and targeting also move, and a discount is not an increase.

### Part 3: The recommendation, and the families bought

**Step 6. Recommend, and show what changes if families are bought.** Raise each family below the floor by its increase through new, approved price lists with stated end dates, renegotiate the customer-specific lists rather than inheriting them, and stage the increases against the loss each can absorb. The totals block shows the revenue if volume holds and, for the families bought in Requirement 6, which families still need an increase.

```jinja
Still to reprice   {{ g.f.still }}
Their revenue      {{ g.f.still_rev }}
```

**Check:** the families bought ({{ buy|map(attribute='short')|join(', ') }}) deliver margins of {% for q in buy %}{{ q.margin|pct(1) }}{{ ", " if not loop.last else "" }}{% endfor %} at the delivered cost, above the floor; {{ g.n_rest }} families still need increases ({{ need|join(', ') }}), worth ${{ g.kept_rev|num(0) }} a year. **Watch for:** the whole table's ${{ g.all_rev|num(0) }} read as the revenue of the path that buys: the families bought clear the floor and need no increase.

## Expected results

| Family | Increase | Volume it can lose | Revenue a year |
|---|---:|---:|---:|
{% for r in reprice %}
| {{ r.short }} | {{ r.increase|pct(2) }} | {{ r.loss|pct(1) }} | ${{ r.revenue|num(0) }} |
{% endfor %}

{{ expected() }}

## What a strong answer says

- **Each increase beside its threshold.** The threshold is the volume the family can lose before it earns less contribution than now; it is not a forecast.
- **The evidence and its limits.** None of the {{ n_promos }} promotion scopes passes the descriptive z of 2 screen: {{ n_up }} lifts are positive and {{ n_down }} negative. The comparison of list-price-weighted order value is a proxy for volume that mix, seasonality and targeting also move. It does not establish significance, that a promotion caused a lift, that a result arose by chance, or that customers will accept a permanent increase. Recommend staged increases, and monitor realized net price, units and contribution against each family's loss threshold.
- **The lists.** Prices reach invoices only through the lists, and the records show expired lists still in use and one approver for every override: new, approved lists with end dates, and customer lists renegotiated.
- **The families bought.** They clear the floor at the delivered price, so only {{ need|join(', ') }} need increases.

A weak answer lists the increases without their thresholds, or reads the promotion screen as a forecast.

## Common mistakes and how to respond

- **A markup for a margin.** *Symptom:* a floor price below today's. *Response:* ask what share of the price the margin is.
- **Contribution over the wrong cost.** *Symptom:* {{ g.example }} can lose {{ ltd.loss|pct(1) }}. *Response:* ask which costs stop if volume is lost.
- **A threshold read as a forecast.** *Symptom:* "customers will accept it". *Response:* ask what evidence would show their response.
- **No price lists.** *Symptom:* increases stated without how they reach invoices. *Response:* ask who sets the price on an order line.
- **Increases for the families bought.** *Symptom:* ${{ g.all_rev|num(0) }} for the path that buys. *Response:* ask what margin those families earn at the delivered cost.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Floor prices and increases | 25 | Goal Seek for each family below the floor, checked directly | Prices without the margin test |
| Volume each increase can lose | 20 | Contribution over the relevant cost | Another cost basis |
| The promotion screen | 20 | Lifts and z, read as a screen only | Lifts read as a forecast |
| Price lists and overrides | 15 | Dates, use, approver, and the consequence | Facts without a consequence |
| Recommendation and the families bought | 15 | Staged, with new lists and the changed list | Increases for all families |
| Documentation | 5 | Sources and Goal Seek notes | Missing |

## Extensions and discussion questions

- Stage the increases in two steps and ask what volume loss the first must show before the second.
- Discuss: what evidence would you collect from a price test?
- Discuss: who should approve a customer-specific price list, and who reviews the approvals?
