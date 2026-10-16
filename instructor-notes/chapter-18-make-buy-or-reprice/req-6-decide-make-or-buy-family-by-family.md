# Requirement 6: Decide make or buy, family by family (Chapter 7)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 6 |
| Perspective | Managerial accounting |
| Tools | More than one tool |
| Time | About 150 minutes |
| Solution file | Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Make or Buy; Chapter18-capstone-sql.zip: MakeBuy.sql, Q22 |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The decision for each family is a few lines of arithmetic that turn on two assumptions: the quote and what happens to the crew. Students separate the costs that stop from those that stay, carry the one-time costs into a two-year view, and see why the CFO's absorption view buys more than the facts support. Excel fits because the decision makers change the quote and the crew and watch the answer move. The analytics type is prescriptive.

Students can:

- compute each family's relevant cost with the crew kept and reduced, the annual effect of buying, and the two-year effect after tooling and severance (Parts 1 and 2);
- find break-even quotes with Goal Seek and build a two-way Data Table on the quote and the crew share (Part 3);
- explain why the absorption view disagrees, and name what the numbers leave out (Parts 4 and 5).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning, and Performance (decision analysis); IFAC IES 2 (b); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with Requirement 4's Costs sheet and the Assumptions sheet that holds the quote; for Part 5, MakeBuy.sql on CharlesRiver_Capstone.sqlite in DB Browser for SQLite.
- **Data conditions.** The quote is the case's assumption, not data. Its volumes are within 4.0% of the base year's sales for every family, so the minimum purchase does not bind in the base year. Q22 reads GoodsReceiptLine, MaterialIssueLine and the ledger's materials account.
- **Verify first.** With the crew kept no family is worth buying; with it reduced, three are. An error in Requirement 4 carries into every cell here.

## How to run it

Individual work, about 150 minutes: 35 for costs and effects, 20 for one-time costs, 40 for Goal Seek and the Data Table, 20 for the CFO's view, 20 for the query and the terms, 15 for documentation. Hold back the crew-reduced column until students see that the crew-kept case buys nothing. **Collect** the workbook and MakeBuy.sql.

![A mock of the Make or Buy table, where each quoted family's delivered quote meets its relevant cost under both crew cases.](../figures/chapter-18-make-buy-or-reprice/IF-18-6-A.pdf)

## Step-by-step solution

### Part 1: The relevant cost and the annual effect

**Step 1. Look up each family's costs and the delivered quote.** The Make or Buy sheet has a row for each quoted family from row 10.

a. Look up the quote's price, volume and tooling and the family's units, absorption cost, relevant costs and routing time from the Quote Table and the Costs sheet with XLOOKUP.
b. Compute the delivered quote, the price plus the inbound freight.

```
Delivered quote      =F10*(1+Freight)
Cost, crew kept      =XLOOKUP($A10,FamCostFamily,FamCostKept)
Cost, crew reduced   =XLOOKUP($A10,FamCostFamily,FamCostReduced)
```

**Check:** for BNH the delivered quote is $334.75. The cost that stops with the crew kept is $332.16: standard material times 1.0106 plus Factory Overhead per standard hour, $18.99. Reducing the crew adds $34.11 per practical hour times the routing time: $389.22. **Watch for:** a quote without its freight: five families then look worth buying with the crew reduced, because SDB and SCN cross over.

**Step 2. Compute the annual effect under each view, and decide.** The effect is the cost that stops, less the delivered quote, times the units sold: positive means buying saves.

```
Absorption view   =(H10-G10)*C10
Crew kept         =(I10-G10)*C10
Crew reduced      =(J10-G10)*C10
Decision          =IF(M10>0,"Buy",IF(N10>0,"Buy only with the crew reduced","Make"))
```

**Check:** BNH reads +$154,853, -$3,773 and +$79,249 a year, and the decision cell says to buy only with the crew reduced. Three families read that way (BNH, NGT, TBL); SDB, SCN, PIL read Make. **Watch for:** the crew charged at the whole time-driven rate. Supervision and depreciation then count as stopping, and SDB and SCN flip to Buy.

### Part 2: The one-time costs and the two years

**Step 3. Count the positions and add tooling and severance.** The hours freed are the routing time of the families bought, on the base year's sales. A position's practical hours and the severance rule are on the Assumptions sheet.

```
Severance, all positions   =BuyPositions*SeverancePerPosition
Tooling                    =SUMPRODUCT('Make or Buy'!$P$10:$P$15,'Make or Buy'!$W$10:$W$15)
Two-year effect            =PriceYears*BuyGain-BuySeverance-BuyTooling
```

**Check:** 17,299 routing hours are 10.56 positions of 1,638.4 hours. Severance is $9,723 a position, $102,660 in all; tooling is $70,000. Two years of $255,481 less those costs leave $338,302, before taxes and undiscounted. With the crew kept the same purchase costs $334,636 a year. **Watch for:**

- Positions on the available hours of a position: 8.45 positions and $82,128 of severance.
- One year of savings against the one-time costs: a net of $82,821; two years with no one-time costs read $510,962.

### Part 3: Break-even quotes and the two-way table

**Step 4. Find each break-even quote with Goal Seek.** The block under the table holds a quote cell and an effect cell for each family and crew case; the effect cell recomputes the annual effect from the quote beside it.

a. Choose **Data > What-If Analysis > Goal Seek**.
b. Enter the effect cell (C19 for the first family, crew kept) in **Set cell**, `0` in **To value** and the quote cell (B19) in **By changing cell**.
c. Repeat for the crew-reduced pair (E19, D19) and each family, then compare columns Q and R, which compute the same quotes directly.

```
Effect at the quote   =(I10-B19*(1+Freight))*C10
Direct, crew kept     =I10/(1+Freight)
```

**Check:** BNH breaks even at $322.48 crew kept and $377.88 crew reduced, against a quote of $325: the quote beats only the second. **Watch for:** a break-even quote that ignores the freight: it equals the relevant cost, $332.16 with the crew kept.

**Step 5. Build the two-way Data Table.** A Data Table's input cells must be on its own sheet, so the two sensitivity inputs sit at the top of the sheet (B5, the quote adjustment, and B6, the share of the freed crew time removed), and column V reads them.

a. In A41 enter the sum of column V over the families to buy, the table's corner.
b. Type the quote adjustments `-0.1`, `0` and `0.1` across B41:D41 and the shares `0`, `0.5` and `1` down A42:A44.
c. Select A41:D44, choose **Data > What-If Analysis > Data Table**, and enter B5 as the **Row input cell** and B6 as the **Column input cell**.

```
Corner     =SUMPRODUCT('Make or Buy'!$P$10:$P$15,'Make or Buy'!$V$10:$V$15)
Column V   =(I10+CrewRemoved*CrewRate*K10-F10*(1+QuoteAdjustment)*(1+Freight))*C10
```

**Check:** the bottom row's middle cell, all the crew time removed at the quote as it is, equals the annual effect, $255,481; the top row's, none removed, is -$334,636. **Watch for:** the two input cells swapped. That cell then reads -$3,328,369, because the table doubles the quote instead of removing the crew.

![A mock of the two-way Data Table of the quote against the share of the freed crew time removed.](../figures/chapter-18-make-buy-or-reprice/IF-18-6-B.pdf)

### Part 4: The CFO's view beside the answer

**Step 6. Count what the absorption view would buy.** Column L is the effect under the CFO's absorption cost. **Check:** it is positive for five of the six families ($933,649 a year in all); relevant costs buy three, only with the crew reduced. The explanation is in the strong answer below.

### Part 5: What the numbers leave out

**Step 7. Measure the materials the families draw, and list the terms.** Routine: type the query at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Q22 compares the standard material in the completions with the material issued to the families' work orders; its core is those issues:

```sql
FamilyIssues AS (
    SELECT mil.ItemID, mil.ExtendedStandardCost
    FROM MaterialIssueLine AS mil
        INNER JOIN MaterialIssue AS mi
            ON mi.MaterialIssueID = mil.MaterialIssueID
        INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = mi.WorkOrderID
        INNER JOIN Item AS i ON i.ItemID = wo.ItemID
    WHERE mi.IssueDate BETWEEN '2026-01-01' AND '2026-12-31'
        AND SUBSTR(i.ItemCode, 1, 7) IN ('FUR-BNH', 'FUR-NGT', 'FUR-TBL')
)
```

**Check:** one row of four values: the standard material in the completions, $2,465,128; these issues, $2,485,927, of which $1,782,126 is the six raw materials whose stock grew most in the year; and all the year's issues, $10,161,205. The families' share is 24.5%. **Watch for:** the families grouped by the three-letter product type. The table lamps join the dining tables and the issues read $2,868,991.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Annual effect for BNH, crew kept; crew reduced | -$3,773; +$79,249 | 2 |
| Positions freed; severance; tooling | 10.56; $102,660; $70,000 | 3 |
| Annual effect, crew reduced; two-year effect | +$255,481; +$338,302 | 3 |
| Materials issued to the families' work orders; share of all issues | $2,485,927; 24.5% | 7 |

> **Instructor notes, Requirement 6:** per unit (crew kept / crew reduced / delivered quote; annual effect of buying at 2026 volume under absorption / crew kept / crew reduced; break-even quote kept / reduced): FUR-BNH 332.16 / 389.22 / 334.75; +154,853 / -3,773 / +79,249; 322.48 / 377.88. FUR-NGT 243.27 / 299.09 / 278.10; +192,550 / -111,432 / +67,149; 236.18 / 290.38. FUR-SDB 267.98 / 327.81 / 334.75; +144,571 / -252,392 / -26,237; 260.17 / 318.26. FUR-TBL 280.42 / 346.34 / 324.45; +356,123 / -219,431 / +109,084; 272.26 / 336.25. LGT-SCN 143.68 / 181.72 / 185.40; +85,551 / -191,571 / -16,917; 139.49 / 176.42. TXT-PIL 138.64 / 174.02 / 226.60; -22,341 / -59,222 / -35,404; 134.60 / 168.95. (Relevant cost kept = material x 1.0106 + 18.99 x standard hours; reduced adds 34.11 x routing hours per unit.) The CFO's absorption view says buy five of six; on relevant costs, buy only BNH, NGT, and TBL, and only with the crew reduced: +255,481 a year; their routing time at 2026 volume 17,299 hours, 10.56 positions of 1,638.4 hours; severance 8 weeks x 40 hours x 30.38 = 9,722.90 a position, 102,660; tooling 70,000; two-year net about +338,302. With the crew kept, buying the three costs 334,636 a year. Two-way table (crew removed 0 / 50 / 100%; quote -10 / 0 / +10%): -35,263 / -334,636 / -634,009; +259,796 / -39,578 / -338,951; +554,854 / +255,481 / -43,892. Make SDB, SCN, and PIL under any crew case. Left out: the 80% minimum (the quoted volumes are within 4% of 2026 sales, family by family), quality and the 1.5% defect threshold, lead time and inventory, the designs and bills of material shared with a supplier, the price risk after two years, and the materials stock of the Part IV case (the three families used 2,465,127.57 of standard material in their 2026 completions; their work orders drew 2,485,926.61, 24% of the year's issues of 10,161,204.64, of which 1,782,126 was the six raw materials that carry the Part IV build, so buying them slows its drawdown).

## What a strong answer says

- **The cost that stops.** Materials and the overhead that varies stop at once. The crew's time stops only if the crew is reduced in step with the hours freed, which is the production manager's decision. Supervision and depreciation stay.
- **The two sentences on the CFO's view.** Absorption cost includes supervision, depreciation and the crew's idle hours, which do not stop when a family is bought, so it makes buying look better than it is. Relevant cost counts only what stops: BNH, NGT, TBL pass only with the crew reduced, and the others fail either way.
- **The terms left out.** The minimum purchase (it would bind if sales fell), quality and the defect credit, lead time and inventory, designs and bills of material shared with a supplier, the price risk after two years, and the materials stock: the three families draw 24% of the year's issues, so buying them slows the drawdown of stock built up in the year.

## Common mistakes and how to respond

- **Absorption as the cost that stops.** *Symptom:* five families to buy. *Response:* ask which costs stop when the family goes.
- **The freight left out, or the whole time-driven rate.** *Symptom:* SDB and SCN look worth buying. *Response:* ask what Charles River pays for the delivered unit, and whether depreciation stops.
- **Positions on available hours.** *Symptom:* 8.45 positions. *Response:* ask which hours the assumptions table counts for a position.
- **One year against the one-time costs.** *Symptom:* a two-year effect of $82,821. *Response:* ask how long the prices are fixed.
- **Swapped input cells.** *Symptom:* a table whose centre is not the annual effect. *Response:* ask which variable runs across.
- **A decision without a crew case.** *Symptom:* "buy" with no condition. *Response:* ask who can reduce the crew, and by when.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Relevant costs and annual effects | 25 | Both crew cases for each family, freight included | One crew case, or no freight |
| One-time costs and two-year effect | 15 | Positions on practical hours, severance, tooling, two years | One year, or no severance |
| Break-even quotes | 15 | Goal Seek for each family and crew case | Typed quotes |
| Two-way Data Table | 15 | Inputs on the sheet; centre equals the annual effect | A table that does not reproduce it |
| The CFO's view explained | 15 | Two sentences that name the costs that stay | A comparison with no reason |
| Terms left out and the query | 10 | The list, with Q22's materials | The list alone |
| Documentation | 5 | Named inputs, notes | Missing |

## Extensions and discussion questions

- Use Goal Seek on the corner cell, changing B6: the three families break even at 57% of the freed crew time. The one-time costs are covered in about 8.1 months.
- Discuss: who owns the crew decision, and what must that person see before agreeing?
- Discuss: when would the CFO's view be right, and which term of the quote would you ask the supplier to change?
