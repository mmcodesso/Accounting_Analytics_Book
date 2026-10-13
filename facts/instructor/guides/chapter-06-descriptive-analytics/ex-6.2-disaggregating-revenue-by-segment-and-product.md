---
note: ch06.ex2
uses: [ch06.g2, ch06.ex1]
title: Disaggregating Revenue by Segment and Product Line
kind: exercise
number: '6.2'
unit: '6'
perspective: financial
tool: excel
minutes: 75
solution: "Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheet Ex 6.2"
figures:
  - id: IF-06-2-A
    kind: excel-mock
    purpose: The second PivotTable of Requirement 2, with the year above the item group in the columns and the change as a second value row.
    shows: "A PivotTable on the worksheet Ex 6.2. Columns: the two years, each with the five item groups and a year total. Rows: the five customer segments, each with two value rows, Revenue and Change from the previous year. The change row is blank under the earlier year and filled under the report year. The Field List shows FiscalYear above ItemGroup in Columns, CustomerSegment in Rows, and LineTotal twice in Values."
    data: Revenue by segment, item group and year, and the percentage changes (the Expected results).
---
{% set g = ch06_g2 %}
# Exercise 6.2: Disaggregating Revenue by Segment and Product Line

{{ header() }}

## Purpose and learning outcomes

The revenue standard asks a company to break revenue into categories that show how economic factors affect it, and offers product lines and types of customer as examples. This exercise asks students to prepare that first cut from InvoiceLines with PivotTables, to read it against the previous year, and to say what stands between an invoice-based schedule and the number in the financial statements. It practices two-dimensional PivotTables, Show Values As and a disclosure paragraph. The analytics type is descriptive.

By the end, students can:

- build a PivotTable by two dimensions and show it as a share of the grand total (outcome 3);
- compare two years with % Difference From and choose which changes deserve a mention (outcomes 3 and 5);
- justify the categories of a disclosure and list what must be reconciled before it could be used (outcome 5).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S1 M8 T5 to T6 (visualization and communicating results); IMA Data Visualization and Financial Statement Analysis; IFAC IES 2 (a) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3. The solution puts all three PivotTables on one worksheet, `Ex 6.2`, with the calculated fields of the tutorials in the shared pivot cache.
- **Data conditions.** Segments crossed with item groups give {{ g.n_combos }} combinations with revenue, not the full grid: Design Services buys only Services, and only Design Services buys Services. Of these, {{ g.n_big }} had at least $500,000 in fiscal {{ g.p }}, and every combination with revenue in fiscal {{ g.y }} also had revenue in fiscal {{ g.p }}, so % Difference From always finds a base. Customers are spread over {{ g.n_regions }} regions.
- **Requirement 5.** It needs the reconciling items of Exercise 6.1. Assign that exercise first, or give students the amounts in the Expected results.

## How to run it

Individual, about 75 minutes: 15 on requirement 1, 25 on requirements 2 and 3, 20 on the paragraph, 15 on the reconciliation. Hold back the Show Values As route for the change column until a student has tried to compute it by hand. Collect the workbook and the paragraph.

## Step-by-step solution

### Requirement (1): Shares of the grand total

**Step 1. Build the first PivotTable.**

a. Select a cell in the InvoiceLines Table and choose **Insert > PivotTable**. Place it on a new worksheet named `Ex 6.2`.
b. Drag FiscalYear to **Filters** and select {{ g.y }}, CustomerSegment to **Rows**, ItemGroup to **Columns** and LineTotal to **Values**.
c. Open **Value Field Settings**, and on the **Show Values As** tab choose **% of Grand Total**. Format the field as a percentage.

**Check:** the grand total reads 100 percent and the largest combinations are {{ shares[0][0] }}-{{ shares[0][1] }} ({{ shares[0][2]|pct(2) }}, ${{ shares[0][3]|money }}), {{ shares[1][0] }}-{{ shares[1][1] }} ({{ shares[1][2]|pct(2) }}) and {{ shares[2][0] }}-{{ shares[2][1] }} ({{ shares[2][2]|pct(2) }}). **Watch for:** the FiscalYear filter left on (All), which gives shares of three years.

### Requirement (2): Change from the previous year

**Step 2. Build the second PivotTable.**

a. Insert a second PivotTable below the first. Drag CustomerSegment to **Rows**, FiscalYear and then ItemGroup to **Columns**, and LineTotal to **Values** twice.
b. Open the **Column Labels** filter and clear {{ d.F }}, so that {{ g.p }} and {{ g.y }} remain.
c. Open **Value Field Settings** of the second LineTotal field, type `Change from {{ g.p }}` in **Custom Name**, and on **Show Values As** choose **% Difference From** with FiscalYear as the **Base field** and **(previous)** as the **Base item**.
d. Drag **Σ Values** from **Columns** to **Rows**, below CustomerSegment.

{{ figure('IF-06-2-A') }}

**Check:** the change appears only under {{ g.y }}.

**Step 3. Rank the combinations.** Among the {{ g.n_big }} combinations with at least $500,000 in fiscal {{ g.p }}, find the largest and smallest changes. The two largest increases are {{ up[0][0] }}-{{ up[0][1] }} ({{ up[0][4]|spct(1) }}, ${{ up[0][2]|money }} to ${{ up[0][3]|money }}) and {{ up[1][0] }}-{{ up[1][1] }} ({{ up[1][4]|spct(1) }}). The two largest decreases are {{ down[0][0] }}-{{ down[0][1] }} ({{ down[0][4]|spct(1) }}) and {{ down[1][0] }}-{{ down[1][1] }} ({{ down[1][4]|spct(1) }}).

**Watch for:** the $500,000 floor forgotten. {{ g.small[0].segment }}-{{ g.small[0].group }} ({{ g.small[0].change|spct(1) }} on ${{ g.small[0].prior|money }}) and {{ g.small[1].segment }}-{{ g.small[1].group }} ({{ g.small[1].change|spct(1) }}) change more in percent, on small bases.

### Requirement (3): The same comparison by region

**Step 4. Repeat with Region.** Insert a third PivotTable with Region in **Rows** instead of CustomerSegment, and the same year filter and change field.

**Check:** the changes are {{ regions[0][0] }} {{ regions[0][1]|spct(1) }}, {{ regions[1][0] }} {{ regions[1][1]|spct(1) }}, {{ regions[2][0] }} {{ regions[2][1]|spct(1) }} and {{ regions[3][0] }} {{ regions[3][1]|spct(1) }}, and the segments {{ segments[0][0] }} {{ segments[0][1]|spct(1) }}, {{ segments[1][0] }} {{ segments[1][1]|spct(1) }}, {{ segments[2][0] }} {{ segments[2][1]|spct(1) }}, {{ segments[3][0] }} {{ segments[3][1]|spct(1) }} and {{ segments[4][0] }} {{ segments[4][1]|spct(1) }}. Total revenue changes {{ total_change|spct(2) }}. **Watch for:** the design services row of the region table. It swings by more than 100 percent in one region ({{ g.svc[0].region }}: {{ g.svc[0].change|spct(0) }}; {{ g.svc[1].region }}: {{ g.svc[1].change|spct(0) }}) on a small base, so a region-by-product reading overstates the news.

### Requirement (4): The disclosure paragraph

**Step 5. Write four to six sentences.** The model path: state the categories (product line and type of customer) and why; give the year's revenue and the shares (Furniture {{ g.grp_share.Furniture|pct(1) }}, Lighting {{ g.grp_share.Lighting|pct(1) }}, Textiles {{ g.grp_share.Textiles|pct(1) }}, Accessories {{ g.grp_share.Accessories|pct(1) }}, design services {{ g.grp_share.Services|pct(1) }}; {{ g.seg_share[0][0] }} {{ g.seg_share[0][1]|pct(1) }} of revenue by customer type); name the largest combinations; summarize the changes; and present the region as supplementary.

### Requirement (5): What must be reconciled

**Step 6. Build the ladder.** Start from the invoice lines (${{ g.grand|money }}), add the cutoff invoices that the ledger records in fiscal {{ g.y }} (${{ g.cutoff|money }}) and freight revenue, which has no invoice line (${{ g.freight|money }}), to reach operating revenue (${{ g.opr|money }}), then deduct sales returns and allowances (${{ (ch06_ex1.contra|abs)|money }}) to reach net revenue (${{ ch06_ex1.net_rev|money }}).

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Largest combination, share of revenue | {{ shares[0][0] }}-{{ shares[0][1] }}, {{ shares[0][2]|pct(2) }} | 1 |
| Second and third | {{ shares[1][0] }}-{{ shares[1][1] }} {{ shares[1][2]|pct(2) }}; {{ shares[2][0] }}-{{ shares[2][1] }} {{ shares[2][2]|pct(2) }} | 1 |
| Largest increase, {{ g.y }} on {{ g.p }} | {{ up[0][4]|spct(1) }} | 3 |
| Largest decrease | {{ down[0][4]|spct(1) }} | 3 |
| Total revenue, {{ g.y }}; {{ g.p }} | ${{ g.grand|money }}; ${{ g.prior_total|money }} | 4 |
| Reconciling items to net revenue | ${{ g.cutoff|money }}; ${{ g.freight|money }}; -${{ (ch06_ex1.contra|abs)|money }} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirements (1) and (2).** The three largest combinations and the four changes are read from the PivotTables, with the $500,000 floor stated.
- **Requirement (4).** The categories follow how Charles River prices and manages the business: price lists by segment, promotions by item group and segment, goods recognized on delivery and design services billed by the hour. The region is supplementary because nothing is priced by it. The paragraph says the amounts are invoice-based.
- **Requirement (5).** Three kinds of item: the cutoff invoices (a period question, settled by delivery), freight revenue (no invoice line) and returns (credit memos).

A weak paragraph lists numbers without a reason for the categories, or presents the PivotTable total as the company's revenue.

## Common mistakes and how to respond

- **A filter left on All.** *Symptom:* shares of three years. *Response:* ask what the grand total should equal.
- **A floor forgotten.** *Symptom:* a small combination ranked first. *Response:* ask what a percentage on a small base says.
- **A change computed by hand.** *Symptom:* a column of formulas that breaks when the layout moves. *Response:* show **% Difference From**.
- **Region as the first category.** *Symptom:* no reason beyond availability. *Response:* ask which decisions the region informs.
- **No reconciliation.** *Symptom:* the paragraph equates the schedule with revenue. *Response:* point to Exercise 6.1's difference.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: shares | 20 | Filtered to the year, shares of the grand total, three largest named | Wrong year or no ranking |
| Requirement 2: changes | 25 | Year above group, **% Difference From**, floor applied, four combinations | Changes by hand, or no floor |
| Requirement 3: region | 10 | Same method by region | Dollars instead of percent |
| Requirement 4: paragraph | 25 | Categories with reasons, shares, changes, invoice basis | Numbers without reasons |
| Requirement 5: reconciliation | 20 | Cutoff, freight and returns named with amounts | Items without amounts |

## Extensions and discussion questions

- Add a slicer on CustomerSegment to the second PivotTable and show the Services rows with and without it.
- Show the first PivotTable as **% of Row Total** and say what the segment mix reveals.
- Discuss: would you present region in a disclosure for a company that sets prices by segment?
- Discuss: Chapter 7 forecasts revenue. Which of these categories would you forecast separately?
