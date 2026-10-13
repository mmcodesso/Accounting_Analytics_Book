---
note: ch06.ex3
uses: [ch06.g3]
title: Product-Line Profitability at Standard Cost
kind: exercise
number: '6.3'
unit: '6'
perspective: managerial
tool: excel
minutes: 60
solution: "Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheet Ex 6.3"
figures: []
---
{% set g = ch06_g3 %}
# Exercise 6.3: Product-Line Profitability at Standard Cost

{{ header() }}

## Purpose and learning outcomes

Tutorial 6.2 built a margin percentage for each quarter. This exercise turns it into a profitability ranking for one year, adds a dollar margin, and asks which lines contribute more margin than revenue. It is the lightest exercise of the chapter and the one that most directly practices calculated fields. The analytics type is descriptive.

By the end, students can:

- define a margin in dollars and a margin percentage as calculated fields, and explain why the percentage is a weighted margin (outcome 4);
- compare each line's share of revenue with its share of margin, and say why Services must be treated separately (outcome 3);
- rank the Furniture product types by margin percentage and read the codes of Chapter 5 (outcome 3).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Cost Accounting and Performance Management; IFAC IES 2 (b) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3, with the StdCostAmount column and the MarginPct calculated field. The solution reads the PivotTable with GETPIVOTDATA for the shares.
- **Data conditions.** Services items carry a standard cost of 0, so the Services margin is 100 percent and the grand total's margin percentage (${{ g.grand_margin|money }} on ${{ g.grand_revenue|money }}, {{ g.grand_pct|pct(2) }}) is higher than that of the product lines alone ({{ (g.product_margin / g.product_revenue)|pct(2) }}). The Furniture product types differ by only {{ g.type_gap_pts|num(1) }} points of margin. The code TBL is also used outside Furniture, so the Furniture filter matters.
- **The cost definition.** Requirement 4 has no single answer. The model answer compares two definitions, which is the point.

## How to run it

Individual, about 60 minutes: 15 on requirement 1, 15 on requirement 2, 15 on requirement 3 and 15 on the explanation. Hold back the shares-without-Services idea until students have seen the Services row. Collect the workbook and the explanation.

## Step-by-step solution

### Requirement (1): Revenue, margin and margin percentage

**Step 1. Build the PivotTable.**

a. Insert a PivotTable from the InvoiceLines Table on a new worksheet named `Ex 6.3`. Drag FiscalYear to **Filters** and select {{ d.C }}, and ItemGroup to **Rows**.
b. Choose **PivotTable Analyze > Fields, Items, & Sets > Calculated Field**, name it `Margin` and enter `=LineTotal-StdCostAmount`.
c. Drag LineTotal, Margin and MarginPct to **Values**, rename them `Revenue`, `Margin (dollars)` and `Margin %`, and format them.

**Check:** the Expected results table. **Watch for:** a per-row ratio column averaged in the PivotTable. That is an unweighted margin and differs from the calculated field, which divides total margin by total revenue.

### Requirement (2): Shares without Services

**Step 2. Compute the shares.** Beside the PivotTable list the four product lines, read each line's revenue and margin with GETPIVOTDATA, total them without Services, and divide. Flag the lines whose share of margin exceeds their share of revenue with `=K6>J6` and the like. A student can instead clear Services in the ItemGroup filter and show two extra value fields as **% of Column Total**.

**Check:** shares of revenue and margin: {% for s in shares %}{{ s[0] }} {{ s[1]|pct(1) }} and {{ s[2]|pct(1) }}{% if not loop.last %}; {% endif %}{% endfor %}. The lines with the larger margin share are {{ more }}. **Watch for:** Services left in the denominators. Its 100 percent margin then changes the answer for {{ g.flips }}: its margin share becomes {{ g.with_services.Lighting[1]|pct(1) }} against a revenue share of {{ g.with_services.Lighting[0]|pct(1) }}.

### Requirement (3): Furniture product types

**Step 3. Switch to product type.** Build a second PivotTable with ItemGroup in **Filters** set to Furniture, ProductType in **Rows** and the three value fields, and sort the types by Margin % from largest to smallest. Read the two highest and the two lowest, and name them with the codes of Chapter 5.

**Check:** the order is {% for t in g.types %}{{ t[0] }} ({{ t[1] }}) {{ t[2]|pct(2) }}{% if not loop.last %}, {% endif %}{% endfor %}. **Watch for:** the Furniture filter missing. TBL then mixes in the other lines that use the code, and its margin reads {{ g.tbl_all|pct(2) }} instead of {{ g.tbl_furniture|pct(2) }}.

### Requirement (4): The Services margin

**Step 4. Explain it.** Three to five sentences. The model answer says that the PivotTable values every line at its item's standard cost, that the design-service items carry a standard cost of 0, and that the cost of a design service is the time of the design staff, recorded in the time records and in payroll. To measure the margin you need the cost of the hours behind the services billed. The model answer offers two measures: the time records' extended cost for the year (${{ time_cost|money }}, a margin of about {{ time_pct|pct(0) }}) or the year's Design Services salaries expense (${{ salaries|money }}, about {{ salaries_pct|pct(0) }}). The gap shows that the margin depends on the cost definition, which a report must state.

**Check:** the explanation names the missing standard cost and one cost source. **Watch for:** the 100 percent read as a finding. Neither of the two sources is loaded in the student workbook, so students describe the data they would ask for.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
{% for b in by_margin %}
| {{ b.group }}: revenue; margin; margin percentage | ${{ b.revenue|money }}; ${{ b.margin|money }}; {{ b.pct|pct(2) }} | 1 |
{% endfor %}
| Services: revenue; margin percentage | ${{ g.groups.Services.revenue|money }}; {{ g.groups.Services.pct|pct(0) }} | 1 |
| Grand total margin percentage | {{ g.grand_pct|pct(2) }} | 1 |
| Highest and lowest Furniture type | {{ high[0][0] }} {{ high[0][2]|pct(2) }}; {{ low[0][0] }} {{ low[0][2]|pct(2) }} | 3 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** {{ more }} contribute more margin than revenue, because their margins are above Furniture's. The shares exclude Services, whose margin percentage is an artifact.
- **Requirement (3).** The two highest types are {{ high[0][1] }}s and {{ high[1][1] }}s and the two lowest are {{ low[0][1] }}s and {{ low[1][1] }}s, with the margin spread across types small.
- **Requirement (4).** The missing standard cost, the two cost definitions with their margins, and a statement that the report must say which one it uses.

A weak answer calls Services the most profitable line, or gives a cost number without a source.

## Common mistakes and how to respond

- **An averaged ratio.** *Symptom:* group percentages that differ from the calculated field. *Response:* ask what an average of row margins weights equally.
- **Services in the shares.** *Symptom:* Lighting's margin share below its revenue share. *Response:* ask what the Services row contributes to the margin denominator.
- **No Furniture filter.** *Symptom:* the TBL margin is off. *Response:* ask which item groups use the code.
- **Ranking by dollars.** *Symptom:* the largest types by margin dollars named as the most profitable. *Response:* ask which column answers a question about margin relative to revenue.
- **A cost invented.** *Symptom:* a Services margin from a typed rate. *Response:* ask where the cost is recorded.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the PivotTable | 25 | Year filter, a calculated field for the dollar margin, correct percentages | Margins by group without the calculated field |
| Requirement 2: the shares | 25 | Services excluded, lines with the larger margin share named | Shares with Services in the denominator |
| Requirement 3: product types | 25 | Furniture filter, four types named with codes | Types without the filter |
| Requirement 4: Services | 25 | Missing standard cost and a cost source, stated definition | The 100 percent explained without a source |

## Extensions and discussion questions

- Rank the groups by MarginBeforeDiscountPct from Tutorial 6.3 and say which group the promotions touch most.
- Compare the standard-cost margin of the product lines with the gross margin of Exercise 6.1, and list what the ledger's cost of goods sold adds.
- Discuss: which margin would you give the vice president of sales, the grand total's or the product lines'?
- Discuss: Chapter 10 traces the manufacturing variance that a standard-cost margin leaves out. Would this ranking change?
