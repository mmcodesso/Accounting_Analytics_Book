---
note: ch06.ex5
uses: [ch06.g5]
title: A Substantive Analytical Procedure on Quarterly Revenue
kind: exercise
number: '6.5'
unit: '6'
perspective: auditing
tool: excel
minutes: 60
solution: "Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheets Ex 6.5 and Ex 6.5 Expectation"
figures:
  - id: IF-06-5-A
    kind: excel-mock
    purpose: The expectation worksheet of Requirements 2 and 3, with the flagged rows highlighted and the list of flagged differences beside the grid.
    shows: "The worksheet Ex 6.5 Expectation. Two input cells in blue at the top, a percentage threshold and a dollar threshold. Below, a grid with columns item group, quarter, expectation, recorded, difference, difference percent and flagged, one row for each group and quarter, with the flagged rows shaded. To the right, a list of the flagged differences filled by a formula, and a cell that counts them."
    data: The expectation grid and the flagged rows (the Expected results).
---
{% set g = ch06_g5 %}
# Exercise 6.5: A Substantive Analytical Procedure on Quarterly Revenue

{{ header() }}

## Purpose and learning outcomes

The chapter ends by saying that interpretation starts from an expectation. This exercise puts the auditor's version of that sentence into a worksheet: develop an expectation for each product line and quarter, compare, flag what exceeds a threshold set in advance, and follow up. It practices a PivotTable read with GETPIVOTDATA, threshold cells, a flag formula and a judgment about the design of the test. The analytics type is diagnostic.

By the end, students can:

- build an expectation grid from a PivotTable and flag differences with a two-condition rule that handles increases and decreases (outcomes 3 and 5);
- say what a threshold misses and why (outcome 5);
- plan the evidence for one flagged difference (outcome 5).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Analysis and Statistical Analysis; IFAC IES 2 (f) and IES 4 (a); AACSB A5 parts 5.1 and 5.2.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3, with FiscalQuarter and FiscalYear on InvoiceLines. The model answer uses FILTER, TAKE and SORTBY (Microsoft 365), but a sorted copy of the grid does the same.
- **Data conditions.** The expectation grid has {{ g.n_cells }} cells, one for each of {{ g.n_groups }} item groups and four quarters. The thresholds flag {{ g.both|length }} of them, {{ g.n_inc }} increases and {{ g.n_dec }} decreases. Every difference over 10 percent also exceeds $50,000, so the percentage condition decides: a dollar threshold alone, or an either-or rule, would flag {{ g.n_or }}. The largest difference in dollars is Furniture's fourth quarter, the quarter of the promotion discounts of Tutorial 6.3.
- **A point to settle.** Prior-year revenue is the expectation the exercise prescribes, although question 15 of the chapter warns against replacing an expectation with the prior year. The exercise asks students to name the weakness, which is the lesson.

## How to run it

Individual, about 60 minutes: 10 on the PivotTable (requirement 1), 15 on the grid (2), 10 on the flags (3), 10 on the design of the threshold (4) and 15 on the follow-up (5). Hold back the ABS hint until a student has flagged only increases. Collect the workbook and the half-page explanation.

## Step-by-step solution

### Requirement (1): The PivotTable

**Step 1. Build it.** Insert a PivotTable from the InvoiceLines Table on a worksheet named `Ex 6.5`. Drag ItemGroup to **Rows**, FiscalQuarter and then FiscalYear to **Columns**, and LineTotal to **Values**. Open the **Column Labels** filter and keep {{ d.P }} and {{ d.C }}. Remove the Grand Total column at the right.

**Check:** each group has four quarters under each year. **Watch for:** FiscalYear above FiscalQuarter, which groups the quarters under the years and changes the labels the formulas need.

### Requirement (2): The expectation grid

**Step 2. Put the thresholds in cells.** On `Ex 6.5 Expectation` enter `0.1` as the percentage threshold in B3 and `50000` as the dollar threshold in B4, both in blue.

**Step 3. Build the grid.**

a. List each item group with each quarter, one row for each, from row 7.
b. In the expectation column read the prior year's revenue from the PivotTable, in the recorded column the report year's, and calculate the difference and the percentage of the expectation.

```jinja
=GETPIVOTDATA("Sum of LineTotal",'Ex 6.5'!$A$3,"ItemGroup",$A7,"FiscalQuarter",$B7,"FiscalYear",{{ d.P }})
=E7/C7
```

**Check:** the grid has {{ g.n_cells }} rows, and Furniture's first quarter reads ${{ g.rows[0].exp|money }} against ${{ g.rows[0].act|money }}. **Watch for:** a percentage divided by the recorded amount, not the expectation.

### Requirement (3): Flag the differences

**Step 4. Enter the flag.** In column G enter the rule, and shade the flagged rows with a conditional formatting rule based on column G.

```
=AND(ABS(E7)>$B$3*C7,ABS(E7)>$B$4)
```

**Step 5. List the flagged differences.** Filter the grid on the flag, or use a formula that returns the flagged rows, and count them with `=COUNTIF(G7:G26,TRUE)`.

{{ figure('IF-06-5-A') }}

**Check:** {{ g.both|length }} flagged: {% for r in g.both %}{{ r.group }} Q{{ r.q }} {% if r.diff < 0 %}-${{ (r.diff|abs)|money }}{% else %}+${{ r.diff|money }}{% endif %} ({{ r.pct|spct(1) }}){% if not loop.last %}; {% endif %}{% endfor %}. **Watch for:** `ABS` missing. The test then flags only the increases and misses the decreases.

### Requirement (4): The design of the threshold

**Step 6. Find the largest unflagged difference.** Sort the unflagged rows by the absolute difference (a helper column with `ABS`, or SORTBY). The largest are {{ missed[0].group }} Q{{ missed[0].q }} (-${{ (missed[0].diff|abs)|money }}, {{ missed[0].pct|spct(1) }}) and {{ missed[1].group }} Q{{ missed[1].q }} (+${{ missed[1].diff|money }}, {{ missed[1].pct|spct(1) }}).

**Check:** the model answer says that both are several times the dollar threshold and below 10 percent, because Furniture is {{ lines }}. Requiring both conditions lets the percentage test screen out large dollar differences in the largest line, while small lines such as Services are flagged for differences that matter less in dollars. A tolerable amount from materiality, or an expectation that reflects known changes, would treat them differently.

### Requirement (5): The follow-up

**Step 7. Plan the evidence.** Pick one flagged difference. The model answer picks {{ g.pick.group }} Q{{ g.pick.q }}: ${{ g.pick.act|money }} against an expectation of ${{ g.pick.exp|money }} ({{ g.pick.pct|spct(1) }}). Evidence: the design-service invoice lines of the quarter by engagement and customer, the engagement and time records behind the hours billed, the rates against the approved list, and invoices near the quarter-end checked for cutoff. Questions for management: which engagements started or ended, whether rates or staffing changed, and whether any work was billed in advance or late. The note's example, {{ example.group }} Q{{ example.q }}, is mostly volume (units {{ example.units|spct(1) }}, price per unit {{ example.price|spct(1) }}), so the evidence is its lines by customer and item traced to orders and shipping documents.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Cells in the grid; flagged | {{ g.n_cells }}; {{ g.both|length }} | 3, 5 |
{% for r in g.both %}
| {{ r.group }} Q{{ r.q }}: expectation; recorded; difference | ${{ r.exp|money }}; ${{ r.act|money }}; {% if r.diff < 0 %}-${{ (r.diff|abs)|money }}{% else %}${{ r.diff|money }}{% endif %} | 5 |
{% endfor %}
| Largest unflagged difference | {{ missed[0].group }} Q{{ missed[0].q }}, -${{ (missed[0].diff|abs)|money }} | 6 |
| Total revenue growth, the context of the expectation | {{ g.growth|spct(2) }} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirement (4).** The threshold reads two conditions, and the percentage condition decides: it misses {{ missed[0].group }} Q{{ missed[0].q }} although that is the largest difference in dollars. The explanation adds that the quarter holds the promotion discounts of Tutorial 6.3, that a threshold from materiality or an expectation adjusted for known events would behave differently, and that prior-year revenue ignores growth and events.
- **Requirement (5).** A specific population (the lines of the quarter by customer or engagement), specific documents (orders, shipments, time records, rates) and questions for management that name what changed. A follow-up that ends at "ask management" is weak.

A weak answer calls the threshold wrong without saying what it was designed to do, or follows up with a generic list.

## Common mistakes and how to respond

- **Only increases flagged.** *Symptom:* {{ g.n_inc }} flags. *Response:* ask what a revenue shortfall means for the test.
- **Either-or.** *Symptom:* {{ g.n_or }} flags, including small percentages. *Response:* ask what each condition is for.
- **Percentage on the recorded amount.** *Symptom:* slightly different percentages. *Response:* ask what the expectation is.
- **Thresholds typed into the formula.** *Symptom:* the same numbers in twenty cells. *Response:* ask how the senior would change the threshold.
- **A follow-up with no evidence.** *Symptom:* "ask management why". *Response:* ask which document would show it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the PivotTable | 10 | Groups by quarter and year, two years | Wrong layout |
| Requirement 2: the grid | 20 | Expectation, recorded, difference, percentage from threshold cells | Thresholds typed into formulas |
| Requirement 3: the flags | 20 | Both conditions with ABS, flagged list correct | One condition or only increases |
| Requirement 4: the threshold | 25 | Largest unflagged difference and the reason | The difference without the reason |
| Requirement 5: the follow-up | 25 | Specific evidence and questions | Generic follow-up |

## Extensions and discussion questions

- Adjust the expectation by the company's growth of {{ g.growth|pct(2) }}. The number flagged is {{ g.n_adjusted }}: what does that say about the weakness of the expectation?
- Replace the dollar threshold with a share of the line's own revenue and compare.
- Discuss: which flagged or unflagged difference would you test first, and why?
- Discuss: Chapter 7 develops better expectations (trends and forecasts). What would change in this exercise?
