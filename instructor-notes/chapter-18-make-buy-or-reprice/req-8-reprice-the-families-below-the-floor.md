# Requirement 8: Reprice the families below the floor (Chapter 7)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 8 |
| Perspective | Managerial accounting |
| Tools | More than one tool |
| Time | About 120 minutes |
| Solution file | Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Prices; Chapter18-capstone-sql.zip: MakeBuy.sql, Q24 to Q26 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A price increase is judged by the volume it can afford to lose, and that threshold is not a forecast. The requirement asks students to find the floor price of each family, measure the contribution at stake over the costs that stop, and set the result against what the records show about how customers respond to price, including the dates and use of the price lists. SQL extracts the order and price-list evidence, Excel does the pricing arithmetic. The analytics type is predictive, with a prescriptive recommendation.

Students can:

- find each family's floor price with Goal Seek, the increase it needs and the share of volume it can lose (Part 1);
- screen past promotions for a volume response and check the price lists, and say what the evidence cannot show (Part 2);
- recommend increases and how the lists should be rebuilt, and show what changes for the families bought (Part 3).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning, and Performance (decision analysis); IFAC IES 2 (b); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with the family costs of Requirement 4 and the decisions of Requirement 6, and MakeBuy.sql on CharlesRiver_Capstone.sqlite.
- **Data conditions.** The floor is the case's assumption, a margin on time-driven cost before unused capacity. Promotion lines carry a PromotionID; 3 of the 9 promotions have an end date on or before their start (a master-data error), so their months come from the orders. The price lists are in PriceList and PriceListLine, and overrides in PriceOverrideApproval.
- **Verify first.** Seven families fall below the floor, and the increases bring in $556,535 a year if volume holds.

## How to run it

Individual or pairs, about 120 minutes: 40 for the floor prices and thresholds, 40 for the evidence and its queries, 25 for the recommendation, 15 for documentation. Hold back the interpretation of the promotion screen until students have the lifts. **Collect** the Prices sheet and the three queries.

## Step-by-step solution

### Part 1: Floor prices and the volume each increase can lose

**Step 1. Flag the families below the floor.** On the Prices sheet each family's row looks up its units, price and time-driven cost from the Costs sheet.

```
Margin        =1-D6/C6
Below floor   =E6<MarginFloor
```

**Check:** seven families have a margin below the floor; BNH reads 34.5%.

**Step 2. Find each floor price with Goal Seek.** The sheet gives a target price cell (G) and a check cell (H) that returns the family's margin above the floor, in dollars a year.

a. Choose **Data > What-If Analysis > Goal Seek**.
b. Enter H6 in **Set cell**, `0` in **To value** and G6 in **By changing cell**, and repeat for each family below the floor.
c. Compare with column I, which computes the same price directly.

```
Check      =IF(F6,B6*(G6*(1-MarginFloor)-D6),"")
Direct     =IF(F6,D6/(1-MarginFloor),"")
```

**Check:** BNH reaches the floor at $665.02, against $608.92 today. **Watch for:** a markup on cost instead of a margin on price: marking the cost up by the floor percentage gives a price below today's for every family (BNH -8.3%), and the margin at that price is under the floor.

**Step 3. Compute the increase and the volume it can lose.** Contribution is measured over the relevant cost with the crew kept. The volume the increase can lose is one minus the contribution per unit now, over that contribution plus the increase per unit: beyond it the family earns less contribution than today.

```
Increase      =IF(F6,G6/C6-1,"")
Contribution  =C6-K6
Volume lost   =IF(F6,1-L6/(L6+G6-C6),"")
```

**Check:** BNH needs 9.21% and can lose 16.9% of its volume; the table of Expected results gives the rest. **Watch for:** contribution over the time-driven cost: BNH then reads 21.1% against 16.9%, an overstated threshold, because the committed costs inside the time-driven cost stay when volume is lost.

![A mock of the Prices sheet's table of floor prices, increases and the volume each increase can lose.](../figures/chapter-18-make-buy-or-reprice/IF-18-8-A.pdf)

### Part 2: What the records say about customers' response

**Step 4. Screen the promotions for a volume response (Q24).** Routine: type the query at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Q24 sums the list-price order value of each promotion's scope by month of its year; the months of the promotion are the months in which promotion lines were ordered:

```sql
(SELECT GROUP_CONCAT(M, ',')
     FROM (SELECT DISTINCT CAST(SUBSTR(o.OrderDate, 6, 2) AS INTEGER) AS M
           FROM Orders AS o
           WHERE o.PromotionID = p.PromotionID
           ORDER BY M)) AS PromotionMonths,
```

Paste the result into the Table PromotionVolume and add the columns that compare the promotion's months with the year's other months:

```
Expected   =AVERAGE(FILTER(PromotionVolume[[#This Row],[M01]:[M12]],NOT(ISNUMBER(SEARCH(","&SEQUENCE(1,12)&",",","&[@PromotionMonths]&",")))))*[@Months]
Lift       =[@PromotionValue]/[@Expected]-1
Z          =([@PromotionValue]-[@Expected])/(STDEV.S(FILTER(PromotionVolume[[#This Row],[M01]:[M12]],NOT(ISNUMBER(SEARCH(","&SEQUENCE(1,12)&",",","&[@PromotionMonths]&",")))))*SQRT([@Months]))
```

**Check:** 9 rows, one for each promotion. No lift passes a z of 2 (the largest, Accessories 2024, reads 1.65); five of the nine are positive and four negative, down to -20.7%. **Watch for:** months taken from the effective dates: 2 promotions end before they start and so have no months at all, and one ends on its start date, which gives one month although its orders ran for two.

**Step 5. Check the price lists and the overrides (Q25 and Q26).** Q25 returns each list with its dates, the range of its prices against list, and the count of order lines priced after its end date:

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

**Check:** 14 lists. The active lists run at 0.84 to 0.94 of list and all end on 2026-12-31; lists 1, 2, 4 are expired, and 8,135 order lines were priced from them after their end dates. One approver, the Sales Manager, approved 409 overrides. **Watch for:** treating a z below 2 as proof that customers do not respond: the screen reads list-price order value in the promotions' months, which seasonality, mix and targeting also move, and a discount is not an increase.

### Part 3: The recommendation, and the families bought

**Step 6. Recommend, and show what changes if families are bought.** Raise each family below the floor by its increase through new, approved price lists with stated end dates, renegotiate the customer-specific lists rather than inheriting them, and stage the increases against the loss each can absorb. The totals block shows the revenue if volume holds and, for the families bought in Requirement 6, which families still need an increase.

```
Still to reprice   =TEXTJOIN(", ",TRUE,FILTER(A5:A20,F5:F20*ISNA(XMATCH(A5:A20,FILTER('Make or Buy'!$A$10:$A$15,'Make or Buy'!$P$10:$P$15=1))),"none"))
Their revenue      =SUMPRODUCT(--F5:F20,ISNA(XMATCH(A5:A20,FILTER('Make or Buy'!$A$10:$A$15,'Make or Buy'!$P$10:$P$15=1)))*1,N5:N20)
```

**Check:** the families bought (BNH, NGT, TBL) deliver margins of 45.0%, 43.2%, 42.7% at the delivered cost, above the floor; four families still need increases (BKC, CTB, SDB, CHD), worth $246,311 a year. **Watch for:** the whole table's $556,535 read as the revenue of the path that buys: the families bought clear the floor and need no increase.

## Expected results

| Family | Increase | Volume it can lose | Revenue a year |
|---|---:|---:|---:|
| BKC | 6.97% | 12.7% | $80,662 |
| BNH | 9.21% | 16.9% | $81,609 |
| CTB | 3.32% | 6.1% | $81,312 |
| NGT | 5.13% | 9.3% | $80,265 |
| SDB | 2.44% | 4.5% | $50,779 |
| TBL | 5.26% | 9.4% | $148,350 |
| CHD | 4.94% | 9.2% | $33,558 |

> **Instructor notes, Requirement 8:** families below the 40% floor on time-driven cost and the increase that reaches it (volume loss the increase absorbs, on the crew-kept contribution margin): FUR-BKC +6.97% (12.7%), FUR-BNH +9.21% (16.9%), FUR-CTB +3.32% (6.1%), FUR-NGT +5.13% (9.3%), FUR-SDB +2.44% (4.5%), FUR-TBL +5.26% (9.4%), LGT-CHD +4.94% (9.2%); +556,535 of revenue a year if volume holds. If BNH, NGT, and TBL are bought, their delivered margins are 45.0%, 43.2%, and 42.7%, so only BKC, CTB, SDB, and CHD need increases. Evidence: no promotion's lift passes a z of 2 (the Part II case's screen; the largest, Accessories 2024, is 1.65), while five of the nine lifts are positive (Accessories 2024 +11.9%, Wholesale 2025 +2.5%, Harbor 2026 +0.4%, Furniture 2026 +0.3%, Design Trade 2026 +3.1%) and four negative, down to -20.7%. It is a descriptive screen of list-price order value in the promotions' months, which seasonality, mix, and targeting also move, not an estimate of how customers would answer an increase: the loss each increase can absorb is a threshold, not a forecast, so the increases are tested, staged and watched against it. Active price lists run at 0.84 to 0.94 of list and every one ended 2026-12-31, and lists 1, 2, and 4 had expired yet were still used (Exercise 8.6); the Sales Manager approves overrides; so the increases need new, approved lists for 2028 with stated end dates, and customer-specific lists should be renegotiated, not inherited. The floor is a price realized after discounts and overrides, so the lists and the override rules together decide whether an increase reaches it.

## What a strong answer says

- **Each increase beside its threshold.** The threshold is the volume the family can lose before it earns less contribution than now; it is not a forecast.
- **The evidence and its limits.** No promotion shows a lift beyond chance, and most are small. That is a screen of past discounts, so it cannot measure the response to an increase; recommend staged increases and watch each family's volume against its threshold.
- **The lists.** Prices reach invoices only through the lists, and the records show expired lists still in use and one approver for every override: new, approved lists with end dates, and customer lists renegotiated.
- **The families bought.** They clear the floor at the delivered price, so only BKC, CTB, SDB, CHD need increases.

A weak answer lists the increases without their thresholds, or reads the promotion screen as a forecast.

## Common mistakes and how to respond

- **A markup for a margin.** *Symptom:* a floor price below today's. *Response:* ask what share of the price the margin is.
- **Contribution over the wrong cost.** *Symptom:* BNH can lose 21.1%. *Response:* ask which costs stop if volume is lost.
- **A threshold read as a forecast.** *Symptom:* "customers will accept it". *Response:* ask what evidence would show their response.
- **No price lists.** *Symptom:* increases stated without how they reach invoices. *Response:* ask who sets the price on an order line.
- **Increases for the families bought.** *Symptom:* $556,535 for the path that buys. *Response:* ask what margin those families earn at the delivered cost.

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
