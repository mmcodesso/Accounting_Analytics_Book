# Requirement 1: Test the CFO's numbers and the premises behind them (Chapters 9 to 11)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 1 |
| Perspective | Managerial accounting |
| Tools | More than one tool |
| Time | About 90 minutes |
| Solution file | Chapter18-capstone-sql.zip: MakeBuy.sql, the queries headed Requirement 1 (Q1 to Q9); Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Families |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The CFO's case rests on one comparison, so this requirement tests it before anything is costed: the families' margins, the premise that neither prices nor standards changed, and the tie to the ledger. The comparison joins invoice lines, work orders, closes and completions, and each join can fan out, so a query fits: written once, it repeats exactly and reconciles to the manufacturing variance account (`5080`). The workbook receives the result and does the margins. The analytics type is descriptive.

Students can:

- build family results from sales, closes and completions without fan-out, and say which units each ratio divides by (Parts 1 and 2);
- compute three margins and say what each measures (Part 2);
- say what the records show about a premise and what they cannot show (Part 3);
- reconcile a study to the ledger before reading a margin from it (Part 4).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S1 M8 (data mining and analysis); IMA Data Analytics and Insights and Reporting and Control (cost accounting); IFAC IES 2 (b) and IES 4 (a); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** CharlesRiver_Capstone.sqlite, a copy of the download, with MakeBuy.sql open in DB Browser for SQLite, and Make Buy Reprice.xlsx with its Assumptions sheet.
- **Data conditions.** The family is the first seven characters of ItemCode; the three-letter type merges two families of different item groups. One manufactured family (ACC-CDL) was neither sold nor made in the year. WorkOrderClose holds closes of earlier work, so the units to divide by are a choice to state. Quantities are fractional. The dataset keeps no history of its master data.
- **Verify first.** In Q7 the families' variance and the ledger's `5080` are both $2,265,636.88. The records end at different dates: invoices 2026-12-31, completions 2026-12-31, closes 2026-12-15, time records 2026-12-11.

## How to run it

Pairs, about 90 minutes: 30 for the family results, 15 for the margins, 20 for the premises, 10 for the reconciliation, 15 for the workbook. The routine for every query: type it at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the CTE pattern until students have seen a total that looks wrong, and the choice of units until two margins agree. **Collect** the script and the Families sheet.

## Step-by-step solution

### Part 1: The family results

**Step 1. Find the dates the records run to.** Run Q1 and copy the four dates above to the Documentation sheet; the time records end first.

**Step 2. Build the family results, one CTE for each fact.** Sales, closes and completions are aggregated to the family separately and joined last, so no fact repeats another. The model saves the whole query as the view FamilyResults (Q2) and keeps it with **Write Changes** (Ctrl+S); the `Closes` CTE shows the pattern, and `Sold`, `Made` and the final SELECT, which left joins them and a second copy of `Sold` for the purchased products, follow it.

```sql
Closes AS (
    SELECT fg.Family, COUNT(*) AS Closes,
        SUM(woc.MaterialVarianceAmount) AS MaterialVariance,
        SUM(woc.DirectLaborVarianceAmount) AS LaborVariance,
        SUM(woc.OverheadVarianceAmount) AS OverheadVariance,
        SUM(woc.TotalVarianceAmount) AS TotalVariance
    FROM WorkOrderClose AS woc
        INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = woc.WorkOrderID
        INNER JOIN FinishedGoods AS fg ON fg.ItemID = wo.ItemID
    WHERE woc.CloseDate BETWEEN '2026-01-01' AND '2026-12-31'
    GROUP BY fg.Family
),
```

**Check:** 16 rows, one for each family sold. **Watch for:**

- One join chain from the sales lines through the work orders to the closes repeats each close once for every sold line of its item: the variance reads $151,484,770.68, 66.9 times the ledger's.
- Grouping by the three-letter type gives 15 rows, and `TBL` merges a dining table and a table lamp from two item groups.
- Starting from every manufactured family (17) keeps the unsold one as a row of NULLs.
- Counting rows as units: 5,535 lines against 46,786.01 units.

### Part 2: The three margins

**Step 3. Compute the margins from the view.** The variance per unit completed is the closes' variance over the units the year completed; the three margins differ in how much of the variance they charge.

```sql
-- Requirement 1, Q4: each family's variance per unit completed and three margins, purchased beside
-- Population: the view FamilyResults; expected: the variance lowers every margin, few beat purchased
SELECT Family, ItemGroup,
    ROUND(TotalVariance / StandardCostCompleted, 4)
        AS ShareOfStandardCompleted,
    ROUND(TotalVariance / UnitsCompleted, 2) AS VariancePerUnit,
    ROUND(1 - StandardCost / Revenue, 4) AS MarginAtStandard,
    ROUND(1 - (StandardCost + TotalVariance / UnitsCompleted * Units)
        / Revenue, 4) AS MarginAfterPerUnit,
    ROUND(1 - (StandardCost + TotalVariance) / Revenue, 4)
        AS MarginWithYearVariance,
    ROUND(1 - PurchasedStandardCost / PurchasedRevenue, 4)
        AS PurchasedMarginAtStandard
FROM FamilyResults
ORDER BY Family;
```

**Check:** Furniture, the group of the CFO's comparison: 42.33% at standard, 32.56% after the variance per unit completed and 31.64% with the year's variance, 10.7 points below standard. **Watch for:** dividing by the units sold. The variance per unit times the units sold is the whole variance, so the second and third margins coincide for every family. The units completed are the base because the variance is the cost of making them; 88 of the year's closes belong to work orders that completed nothing in it, so say which base you use.

**Step 4. Set the purchased products beside them and move the result to Excel.** Only TXT-PIL beats its purchased benchmark on both measures; a family with no purchased products shows `none`. Copy the results with **Copy with Headers** (Ctrl+Shift+C) into the Families sheet as a Table named FamilyResults, and add the margins as Table columns:

```
VariancePerUnit   =[@TotalVariance]/[@UnitsCompleted]
MarginStandard    =1-[@StandardCost]/[@Revenue]
MarginPerUnit     =1-([@StandardCost]+[@VariancePerUnit]*[@Units])/[@Revenue]
MarginYear        =1-([@StandardCost]+[@TotalVariance])/[@Revenue]
```

**Check:** the sheet's group rows reproduce the Step 3 margins (Furniture's per-unit margin is `=1-(C26+E26)/B26`).

### Part 3: The premises

**Step 5. Test the second premise.** Q9 counts the invoice lines whose list price differs from the item's and the shipment lines whose standard cost differs from quantity times the item's (shown), then the largest completion difference and the items sold in every year, which follow the same pattern. Q8 (what Charles River paid for purchased products) calibrates the quote.

```sql
(SELECT COUNT(*)
     FROM SalesInvoiceLine AS sil
        INNER JOIN Item AS i ON i.ItemID = sil.ItemID
     WHERE sil.BaseListPrice IS NULL OR i.ListPrice IS NULL
        OR ABS(sil.BaseListPrice - i.ListPrice) > 0.004)
        AS ListPriceDiffers,
    (SELECT COUNT(*)
     FROM ShipmentLine AS sl
        INNER JOIN Item AS i ON i.ItemID = sl.ItemID
     WHERE sl.ExtendedStandardCost IS NULL
        OR ABS(sl.ExtendedStandardCost
            - ROUND(sl.QuantityShipped * i.StandardCost, 2)) > 0.011)
        AS ShipmentCostDiffers,
```

**Check:** 27,933 invoice lines, none with a different list price or shipment cost, a largest completion difference of `0.02` (component rounding), and 198 items sold in each of the three years. Purchased cost averages 1.01 times standard, from 0.95 to 1.07.

The records agree with today's master data, which supports the premise for what was sold and made. They cannot show a change made and reversed, or a change to an item no line used, because the dataset keeps no dated history. A dated price and standard record or a change log would settle it. What customers paid is a separate question (Requirement 8).

### Part 4: Reconcile to account 5080

**Step 6. Reconcile the families to the ledger.** Q7 sets the families' variance beside `5080` with the year-end closes left out.

```sql
-- Requirement 1, Q7: the families' variances reconciled to account 5080
-- Population: the view FamilyResults and the 5080 postings; expected: no difference
SELECT
    (SELECT ROUND(SUM(TotalVariance), 2)
     FROM FamilyResults) AS FamilyVariance,
    (SELECT ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2)
     FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
     WHERE a.AccountNumber = 5080 AND gl.FiscalYear = 2026
        AND gl.VoucherNumber NOT IN (
            SELECT EntryNumber
            FROM JournalEntry
            WHERE EntryType LIKE 'Year-End Close%')) AS Variance5080;
```

**Check:** both $2,265,636.88, difference zero, as on the workbook's Families sheet (material $106,498.85, labor -$14,074.81, overhead $2,173,212.84). Do this before anyone reads a margin.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Families sold; not sold | 16; ACC-CDL | 2 |
| Total variance, equal to `5080` | $2,265,636.88 | 6 |
| Furniture margins: standard; per unit; year | 42.33%; 32.56%; 31.64% | 3 |
| Families beating the purchased benchmark | TXT-PIL | 4 |
| Invoice lines tested; items sold every year | 27,933; 198 | 5 |

> **Instructor notes, Requirement 1:** families of manufactured finished goods (Item.SupplyMode 'Manufactured'), first seven characters of ItemCode; ACC-CDL was not made or sold in 2026. Fiscal 2026 by InvoiceDate; variance = TotalVarianceAmount of closes dated in 2026 (material 106,498.85, labor -14,074.81, overhead 2,173,212.84; total 2,265,636.88, equal to 5080). Variance per unit completed = the family's 2026 close variance / its 2026 units completed. Family / units sold / revenue / closes / variance / share of standard completed / per unit completed / margin at standard / after per-unit variance / with the year's variance / purchased margin at standard: FUR-BKC 1,955.0 / 1,158,000.85 / 179 / 106,587.95 / 14.5% / 52.33 / 39.4 / 30.5 / 30.2 / none; FUR-BNH 1,454.9 / 885,941.44 / 152 / 111,599.30 / 16.1% / 62.48 / 37.8 / 27.5 / 25.2 / 47.6; FUR-CON 1,321.7 / 822,620.94 / 165 / 104,967.73 / 15.4% / 55.48 / 45.9 / 37.0 / 33.2 / 42.8; FUR-CTB 4,361.0 / 2,452,336.51 / 490 / 280,253.94 / 16.5% / 53.27 / 42.4 / 32.9 / 30.9 / 38.1; FUR-DSK 4,567.4 / 2,982,469.82 / 439 / 235,254.95 / 14.6% / 49.23 / 44.3 / 36.8 / 36.4 / 45.1; FUR-NGT 3,198.9 / 1,565,380.69 / 331 / 167,618.64 / 18.3% / 52.33 / 41.6 / 30.9 / 30.9 / 44.5; FUR-SDB 3,780.0 / 2,079,063.38 / 370 / 259,360.59 / 20.1% / 62.23 / 43.5 / 32.2 / 31.0 / 40.9; FUR-TBL 4,984.1 / 2,822,552.50 / 462 / 313,491.13 / 18.7% / 63.62 / 41.3 / 30.1 / 30.2 / 44.0; LGT-CHD 2,167.1 / 678,919.89 / 138 / 52,219.07 / 12.9% / 23.12 / 41.7 / 34.3 / 34.0 / 48.3; LGT-FLR 4,404.4 / 1,085,286.98 / 321 / 113,365.27 / 17.6% / 21.75 / 47.9 / 39.1 / 37.5 / 46.3; LGT-PND 2,773.2 / 1,081,462.36 / 207 / 104,786.77 / 16.2% / 33.98 / 45.9 / 37.2 / 36.2 / 41.8; LGT-SCN 4,591.4 / 1,500,136.53 / 274 / 170,490.55 / 20.9% / 34.12 / 48.0 / 37.6 / 36.6 / 45.9; LGT-TBL 2,976.2 / 864,006.77 / 213 / 80,274.14 / 16.5% / 24.24 / 49.4 / 41.0 / 40.1 / 44.4; TXT-CRT 1,657.0 / 720,512.88 / 99 / 52,879.36 / 12.8% / 29.45 / 47.1 / 40.3 / 39.8 / 49.0; TXT-PIL 673.3 / 246,514.48 / 27 / 17,307.85 / 21.8% / 34.56 / 56.6 / 47.2 / 49.6 / 41.0; TXT-THR 1,920.5 / 1,115,802.11 / 93 / 95,179.64 / 17.6% / 48.91 / 52.2 / 43.8 / 43.7 / 44.6. Groups (standard / per unit / year): Furniture revenue 14,768,366.13, 42.33% / 32.56% / 31.64% (variance 1,579,134.23); Lighting 5,209,812.53, 46.96% / 37.96% / 36.96% (521,135.80); Textiles 2,082,829.47, 50.96% / 42.99% / 43.02% (165,366.85). The CFO's "ten points" is Furniture's 42.3% against 31.6%; only TXT-PIL beats its purchased benchmark after the variance. Premises: BaseListPrice equals Item.ListPrice on all 27,933 invoice lines; every ShipmentLine standard cost equals quantity x StandardCost; completion lines differ by at most 0.02 (component rounding); 198 items were sold in each of the three years. So the transactions show no change in list prices or standards: they agree with today's master data, which supports the premise for what was sold and made but cannot show that nothing was changed and changed back, or changed for an item no line used. The dataset keeps no history of its master data, so dated price and standard records, or a change log, are the evidence the CFO's stronger claim needs; the prices customers paid are a separate question (the price lists of Requirement 8). Purchased cost to list in 2026 for the quoted families: BNH 0.472, NGT 0.478, SDB 0.517, TBL 0.485, SCN 0.486, PIL 0.540 (the quote's calibration); purchased cost averages 1.011 times standard (0.95 to 1.07). The CFO's premise holds as arithmetic and fails as a diagnosis: Requirement 2.

## What a strong answer says

- **The comparison holds as arithmetic.** Furniture earns 42.3% at standard and 31.6% once the year's variance is charged, while the purchased furniture earns about what its standards say.
- **The premise is supported, not proved.** Prices and standards agree with the master data on every line; a change made and reversed would leave no record; the evidence needed is dated history.
- **The units are stated and the tie comes first.** Units completed; the families' variance equals `5080` before any margin is read.

A weak answer reports margins without the reconciliation, or calls the premise true because the lines agree.

## Common mistakes and how to respond

- **A fanned-out join.** *Symptom:* a variance of $151,484,770.68. *Response:* ask what the total should equal, then which join repeats a row.
- **Units sold as the base.** *Symptom:* two margins that match. *Response:* ask what the variance is the cost of making.
- **The three-letter type.** *Symptom:* 15 rows and a `TBL` row in two groups. *Response:* ask what the first seven characters name.
- **A family with no sales.** *Symptom:* a row of NULLs. *Response:* ask which table decides who is a family of the year.
- **Premise proved.** *Symptom:* "no change" with no limits. *Response:* ask what a change reversed in March would leave.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Family results without fan-out | 30 | One row for each family sold; facts aggregated before joining; units stated | Right totals by a join chain that happens to work |
| Three margins | 30 | Each margin as defined, purchased beside them, Furniture's gap found | Margins on the units sold, or one measure missing |
| The premises | 25 | All three tests and the limits of what they show; the evidence that would settle it | Tests without the limits |
| Reconciliation and workbook | 15 | Families tie to `5080`; Table, formulas and Documentation in the sheet | Tie without documentation |

## Extensions and discussion questions

- Repeat the margins by item and list the five items with the widest gap between standard and the year's variance.
- Rerun the per-unit variance on the units of the work orders closed in the year and say how far the answer moves.
- Discuss: the CFO says overhead is applied at about a third of what it costs. Which of these results would you want before agreeing?
