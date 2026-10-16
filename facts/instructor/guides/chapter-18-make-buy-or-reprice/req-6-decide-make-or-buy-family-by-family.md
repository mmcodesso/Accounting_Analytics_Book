---
note: ch18.r6
uses: [ch18.g6]
title: Decide make or buy, family by family (Chapter 7)
kind: requirement
number: '6'
unit: '18'
perspective: managerial
tool: mixed
minutes: 150
solution: "Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Make or Buy; Chapter18-capstone-sql.zip: MakeBuy.sql, Q22"
figures:
  - id: IF-18-6-A
    kind: excel-mock
    purpose: The Make or Buy table, where each quoted family's delivered quote meets its relevant cost under both crew cases.
    shows: "Six family rows with the delivered quote, the relevant cost with the crew kept and reduced, the annual effect of buying under the absorption view, the crew kept and the crew reduced, and the decision; negative effects show a minus sign and the three families to buy are outlined."
    data: The Make or Buy sheet of the model workbook, the rows of the six quoted families.
  - id: IF-18-6-B
    kind: excel-mock
    purpose: The two-way Data Table of the quote against the share of the freed crew time removed.
    shows: "The two sensitivity inputs above the table, a corner cell, three quote adjustments across, three crew shares down and nine results, with the cell for all the crew time removed at the quote as it is outlined."
    data: The sensitivity inputs and the two-way Data Table of the Make or Buy sheet.
---
{% set g = ch18_g6 %}
{% macro sg(x) %}{{ "-" if x < 0 else "+" }}${{ (x|abs)|num(0) }}{% endmacro %}
# Requirement 6: Decide make or buy, family by family (Chapter 7)

{{ header() }}

## Purpose and learning outcomes

The decision for each family is a few lines of arithmetic that turn on two assumptions: the quote and what happens to the crew. Students separate the costs that stop from those that stay, carry the one-time costs into a two-year view, and see why the CFO's absorption view buys more than the facts support. Excel fits because the decision makers change the quote and the crew and watch the answer move. The analytics type is prescriptive.

Students can:

- compute each family's relevant cost with the crew kept and reduced, the annual effect of buying, and the two-year effect after tooling and severance (Parts 1 and 2);
- find break-even quotes with Goal Seek and build a two-way Data Table on the quote and the crew share (Part 3);
- explain why the absorption view disagrees, and name what the numbers leave out (Parts 4 and 5).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning, and Performance (decision analysis); IFAC IES 2 (b); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with Requirement 4's Costs sheet and the Assumptions sheet that holds the quote; for Part 5, MakeBuy.sql on CharlesRiver_Capstone.sqlite in DB Browser for SQLite.
- **Data conditions.** The quote is the case's assumption, not data. Its volumes are within {{ gap|pct(1) }} of the base year's sales for every family, so the minimum purchase does not bind in the base year. Q22 reads GoodsReceiptLine, MaterialIssueLine and the ledger's materials account.
- **Verify first.** With the crew kept no family is worth buying; with it reduced, {{ n_buy }} are. An error in Requirement 4 carries into every cell here.

## How to run it

Individual work, about 150 minutes: 35 for costs and effects, 20 for one-time costs, 40 for Goal Seek and the Data Table, 20 for the CFO's view, 20 for the query and the terms, 15 for documentation. Hold back the crew-reduced column until students see that the crew-kept case buys nothing. **Collect** the workbook and MakeBuy.sql.

{{ figure('IF-18-6-A') }}

## Step-by-step solution

### Part 1: The relevant cost and the annual effect

**Step 1. Look up each family's costs and the delivered quote.** The Make or Buy sheet has a row for each quoted family from row 10.

a. Look up the quote's price, volume and tooling and the family's units, absorption cost, relevant costs and routing time from the Quote Table and the Costs sheet with XLOOKUP.
b. Compute the delivered quote, the price plus the inbound freight.

```jinja
Delivered quote      {{ g.f.deliv }}
Cost, crew kept      {{ g.f.kept }}
Cost, crew reduced   {{ g.f.reduced }}
```

**Check:** for {{ g.example }} the delivered quote is ${{ buy[0].delivered|num(2) }}. The cost that stops with the crew kept is ${{ buy[0].kept|num(2) }}: standard material times {{ mat_factor|num(4) }} plus Factory Overhead per standard hour, ${{ fo_rate|num(2) }}. Reducing the crew adds ${{ crew_rate|num(2) }} per practical hour times the routing time: ${{ buy[0].reduced|num(2) }}. **Watch for:** a quote without its freight: {{ g.nf_buy }} families then look worth buying with the crew reduced, because {{ g.nf_flip|join(' and ') }} cross over.

**Step 2. Compute the annual effect under each view, and decide.** The effect is the cost that stops, less the delivered quote, times the units sold: positive means buying saves.

```jinja
Absorption view   {{ g.f.abs_eff }}
Crew kept         {{ g.f.kept_eff }}
Crew reduced      {{ g.f.red_eff }}
Decision          {{ g.f.decision }}
```

**Check:** {{ g.example }} reads {{ sg(buy[0].absorp) }}, {{ sg(buy[0].a_kept) }} and {{ sg(buy[0].a_reduced) }} a year, and the decision cell says to buy only with the crew reduced. Three families read that way ({{ buy|map(attribute='short')|join(', ') }}); {{ lose|map(attribute='short')|join(', ') }} read Make. **Watch for:** the crew charged at the whole time-driven rate. Supervision and depreciation then count as stopping, and {{ g.tdw_flip|join(' and ') }} flip to Buy.

### Part 2: The one-time costs and the two years

**Step 3. Count the positions and add tooling and severance.** The hours freed are the routing time of the families bought, on the base year's sales. A position's practical hours and the severance rule are on the Assumptions sheet.

```jinja
Severance, all positions   {{ g.f.severance }}
Tooling                    {{ g.f.tooling }}
Two-year effect            {{ g.f.two_years }}
```

**Check:** {{ hours|num(0) }} routing hours are {{ positions|num(2) }} positions of {{ pos_hours|num(1) }} hours. Severance is ${{ severance|num(0) }} a position, ${{ severance_total|num(0) }} in all; tooling is ${{ tooling|num(0) }}. Two years of ${{ gain|num(0) }} less those costs leave ${{ net|num(0) }}, before taxes and undiscounted. With the crew kept the same purchase costs ${{ kept_cost|num(0) }} a year. **Watch for:**

- Positions on the available hours of a position: {{ g.pos_wrong|num(2) }} positions and ${{ g.sev_wrong|num(0) }} of severance.
- One year of savings against the one-time costs: a net of ${{ g.net_one|num(0) }}; two years with no one-time costs read ${{ g.net_free|num(0) }}.

### Part 3: Break-even quotes and the two-way table

**Step 4. Find each break-even quote with Goal Seek.** The block under the table holds a quote cell and an effect cell for each family and crew case; the effect cell recomputes the annual effect from the quote beside it.

a. Choose **Data > What-If Analysis > Goal Seek**.
b. Enter the effect cell (C19 for the first family, crew kept) in **Set cell**, `0` in **To value** and the quote cell (B19) in **By changing cell**.
c. Repeat for the crew-reduced pair (E19, D19) and each family, then compare columns Q and R, which compute the same quotes directly.

```jinja
Effect at the quote   {{ g.f.gs_kept }}
Direct, crew kept     {{ g.f.be_kept }}
```

**Check:** {{ g.example }} breaks even at ${{ buy[0].be_kept|num(2) }} crew kept and ${{ buy[0].be_reduced|num(2) }} crew reduced, against a quote of ${{ buy[0].price|num(0) }}: the quote beats only the second. **Watch for:** a break-even quote that ignores the freight: it equals the relevant cost, ${{ buy[0].kept|num(2) }} with the crew kept.

**Step 5. Build the two-way Data Table.** A Data Table's input cells must be on its own sheet, so the two sensitivity inputs sit at the top of the sheet (B5, the quote adjustment, and B6, the share of the freed crew time removed), and column V reads them.

a. In A41 enter the sum of column V over the families to buy, the table's corner.
b. Type the quote adjustments `-0.1`, `0` and `0.1` across B41:D41 and the shares `0`, `0.5` and `1` down A42:A44.
c. Select A41:D44, choose **Data > What-If Analysis > Data Table**, and enter B5 as the **Row input cell** and B6 as the **Column input cell**.

```jinja
Corner     {{ g.f.corner }}
Column V   {{ g.f.sens }}
```

**Check:** the bottom row's middle cell, all the crew time removed at the quote as it is, equals the annual effect, ${{ gain|num(0) }}; the top row's, none removed, is {{ sg(-kept_cost) }}. **Watch for:** the two input cells swapped. That cell then reads {{ sg(g.swapped) }}, because the table doubles the quote instead of removing the crew.

{{ figure('IF-18-6-B') }}

### Part 4: The CFO's view beside the answer

**Step 6. Count what the absorption view would buy.** Column L is the effect under the CFO's absorption cost. **Check:** it is positive for {{ absorp_buy }} of the {{ n_quoted }} families (${{ g.absorp_sum|num(0) }} a year in all); relevant costs buy {{ n_buy }}, only with the crew reduced. The explanation is in the strong answer below.

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

**Check:** one row of four values: the standard material in the completions, ${{ buy_material|num(0) }}; these issues, ${{ fam_issued|num(0) }}, of which ${{ six_issued|num(0) }} is the {{ n_six }} raw materials whose stock grew most in the year; and all the year's issues, ${{ issues|num(0) }}. The families' share is {{ share|pct(1) }}. **Watch for:** the families grouped by the three-letter product type. The table lamps join the dining tables and the issues read ${{ g.by_type|num(0) }}.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Annual effect for {{ g.example }}, crew kept; crew reduced | {{ sg(buy[0].a_kept) }}; {{ sg(buy[0].a_reduced) }} | 2 |
| Positions freed; severance; tooling | {{ positions|num(2) }}; ${{ severance_total|num(0) }}; ${{ tooling|num(0) }} | 3 |
| Annual effect, crew reduced; two-year effect | {{ sg(gain) }}; {{ sg(net) }} | 3 |
| Materials issued to the families' work orders; share of all issues | ${{ fam_issued|num(0) }}; {{ share|pct(1) }} | 7 |

{{ expected() }}

## What a strong answer says

- **The cost that stops.** Materials and the overhead that varies stop at once. The crew's time stops only if the crew is reduced in step with the hours freed, which is the production manager's decision. Supervision and depreciation stay.
- **The two sentences on the CFO's view.** Absorption cost includes supervision, depreciation and the crew's idle hours, which do not stop when a family is bought, so it makes buying look better than it is. Relevant cost counts only what stops: {{ buy|map(attribute='short')|join(', ') }} pass only with the crew reduced, and the others fail either way.
- **The terms left out.** The minimum purchase (it would bind if sales fell), quality and the defect credit, lead time and inventory, designs and bills of material shared with a supplier, the price risk after two years, and the materials stock: the three families draw {{ share|pct(0) }} of the year's issues, so buying them slows the drawdown of stock built up in the year.

## Common mistakes and how to respond

- **Absorption as the cost that stops.** *Symptom:* {{ absorp_buy }} families to buy. *Response:* ask which costs stop when the family goes.
- **The freight left out, or the whole time-driven rate.** *Symptom:* {{ g.nf_flip|join(' and ') }} look worth buying. *Response:* ask what Charles River pays for the delivered unit, and whether depreciation stops.
- **Positions on available hours.** *Symptom:* {{ g.pos_wrong|num(2) }} positions. *Response:* ask which hours the assumptions table counts for a position.
- **One year against the one-time costs.** *Symptom:* a two-year effect of ${{ g.net_one|num(0) }}. *Response:* ask how long the prices are fixed.
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

- Use Goal Seek on the corner cell, changing B6: the three families break even at {{ g.be_share|pct(0) }} of the freed crew time. The one-time costs are covered in about {{ g.payback|num(1) }} months.
- Discuss: who owns the crew decision, and what must that person see before agreeing?
- Discuss: when would the CFO's view be right, and which term of the quote would you ask the supplier to change?
