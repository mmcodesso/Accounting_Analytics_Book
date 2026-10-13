---
note: ch18.r1
uses: [ch18.g1]
title: Test the CFO's numbers and the premises behind them (Chapters 9 to 11)
kind: requirement
number: '1'
unit: '18'
perspective: managerial
tool: mixed
minutes: 90
solution: "Chapter18-capstone-sql.zip: MakeBuy.sql, the queries headed Requirement 1 (Q1 to Q9); Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Families"
figures: []
---
{% set g = ch18_g1 %}
# Requirement 1: Test the CFO's numbers and the premises behind them (Chapters 9 to 11)

{{ header() }}

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
- **Data conditions.** The family is the first seven characters of ItemCode; the three-letter type merges two families of different item groups. One manufactured family ({{ g.unsold|join(', ') }}) was neither sold nor made in the year. WorkOrderClose holds closes of earlier work, so the units to divide by are a choice to state. Quantities are fractional. The dataset keeps no history of its master data.
- **Verify first.** In Q7 the families' variance and the ledger's `5080` are both ${{ g.q7.ledger|money }}. The records end at different dates: invoices {{ g.dt.invoice }}, completions {{ g.dt.completion }}, closes {{ g.dt.close }}, time records {{ g.dt.time }}.

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

**Check:** {{ g.n_rows }} rows, one for each family sold. **Watch for:**

- One join chain from the sales lines through the work orders to the closes repeats each close once for every sold line of its item: the variance reads ${{ g.fan|money }}, {{ g.fan_times|num(1) }} times the ledger's.
- Grouping by the three-letter type gives {{ g.n_types|count }} rows, and `{{ g.merged }}` merges a dining table and a table lamp from two item groups.
- Starting from every manufactured family ({{ g.every|count }}) keeps the unsold one as a row of NULLs.
- Counting rows as units: {{ g.lines_mfg|count }} lines against {{ g.units_mfg|num(2) }} units.

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

**Check:** Furniture, the group of the CFO's comparison: {{ story.m_std|pct(2) }} at standard, {{ story.m_unit|pct(2) }} after the variance per unit completed and {{ story.m_year|pct(2) }} with the year's variance, {{ g.pts|num(1) }} points below standard. **Watch for:** dividing by the units sold. The variance per unit times the units sold is the whole variance, so the second and third margins coincide for every family. The units completed are the base because the variance is the cost of making them; {{ g.prior|count }} of the year's closes belong to work orders that completed nothing in it, so say which base you use.

**Step 4. Set the purchased products beside them and move the result to Excel.** Only {{ beats|join(', ') }} beats its purchased benchmark on both measures; a family with no purchased products shows `none`. Copy the results with **Copy with Headers** (Ctrl+Shift+C) into the Families sheet as a Table named FamilyResults, and add the margins as Table columns:

```jinja
VariancePerUnit   {{ g.f_vpu }}
MarginStandard    {{ g.f_m1 }}
MarginPerUnit     {{ g.f_m2 }}
MarginYear        {{ g.f_m3 }}
```

**Check:** the sheet's group rows reproduce the Step 3 margins (Furniture's per-unit margin is `{{ g.f_group }}`).

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

**Check:** {{ lines|count }} invoice lines, none with a different list price or shipment cost, a largest completion difference of `{{ max_diff|num(2) }}` (component rounding), and {{ all_years|count }} items sold in each of the {{ n_years }} years. Purchased cost averages {{ avg_ratio|num(2) }} times standard, from {{ low_ratio|num(2) }} to {{ high_ratio|num(2) }}.

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

**Check:** both ${{ g.q7.family|money }}, difference zero, as on the workbook's Families sheet (material ${{ t.material|money }}, labor -${{ (t.labor|abs)|money }}, overhead ${{ t.overhead|money }}). Do this before anyone reads a margin.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Families sold; not sold | {{ g.n_rows }}; {{ g.unsold|join(', ') }} | 2 |
| Total variance, equal to `5080` | ${{ t.total|money }} | 6 |
| Furniture margins: standard; per unit; year | {{ story.m_std|pct(2) }}; {{ story.m_unit|pct(2) }}; {{ story.m_year|pct(2) }} | 3 |
| Families beating the purchased benchmark | {{ beats|join(', ') }} | 4 |
| Invoice lines tested; items sold every year | {{ lines|count }}; {{ all_years|count }} | 5 |

{{ expected() }}

## What a strong answer says

- **The comparison holds as arithmetic.** Furniture earns {{ story.m_std|pct(1) }} at standard and {{ story.m_year|pct(1) }} once the year's variance is charged, while the purchased furniture earns about what its standards say.
- **The premise is supported, not proved.** Prices and standards agree with the master data on every line; a change made and reversed would leave no record; the evidence needed is dated history.
- **The units are stated and the tie comes first.** Units completed; the families' variance equals `5080` before any margin is read.

A weak answer reports margins without the reconciliation, or calls the premise true because the lines agree.

## Common mistakes and how to respond

- **A fanned-out join.** *Symptom:* a variance of ${{ g.fan|money }}. *Response:* ask what the total should equal, then which join repeats a row.
- **Units sold as the base.** *Symptom:* two margins that match. *Response:* ask what the variance is the cost of making.
- **The three-letter type.** *Symptom:* {{ g.n_types|count }} rows and a `{{ g.merged }}` row in two groups. *Response:* ask what the first seven characters name.
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
