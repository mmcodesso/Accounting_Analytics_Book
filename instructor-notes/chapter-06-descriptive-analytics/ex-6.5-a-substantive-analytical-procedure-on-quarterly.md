# Exercise 6.5: A Substantive Analytical Procedure on Quarterly Revenue

| | |
|---|---|
| Unit | Chapter 6: Descriptive and Diagnostic Analytics in Excel |
| Item | Exercise 6.5 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 60 minutes |
| Solution file | Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheets Ex 6.5 and Ex 6.5 Expectation |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The chapter ends by saying that interpretation starts from an expectation. This exercise puts the auditor's version of that sentence into a worksheet: develop an expectation for each product line and quarter, compare, flag what exceeds a threshold set in advance, and follow up. It practices a PivotTable read with GETPIVOTDATA, threshold cells, a flag formula and a judgment about the design of the test. The analytics type is diagnostic.

By the end, students can:

- build an expectation grid from a PivotTable and flag differences with a two-condition rule that handles increases and decreases (outcomes 3 and 5);
- say what a threshold misses and why (outcome 5);
- plan the evidence for one flagged difference (outcome 5).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Analysis and Statistical Analysis; IFAC IES 2 (f) and IES 4 (a); AACSB A5 parts 5.1 and 5.2.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3, with FiscalQuarter and FiscalYear on InvoiceLines. The model answer uses FILTER, TAKE and SORTBY (Microsoft 365), but a sorted copy of the grid does the same.
- **Data conditions.** The expectation grid has 20 cells, one for each of 5 item groups and four quarters. The thresholds flag 6 of them, 3 increases and 3 decreases. Every difference over 10 percent also exceeds $50,000, so the percentage condition decides: a dollar threshold alone, or an either-or rule, would flag 13. The largest difference in dollars is Furniture's fourth quarter, the quarter of the promotion discounts of Tutorial 6.3.
- **A point to settle.** Prior-year revenue is the expectation the exercise prescribes, although question 15 of the chapter warns against replacing an expectation with the prior year. The exercise asks students to name the weakness, which is the lesson.

## How to run it

Individual, about 60 minutes: 10 on the PivotTable (requirement 1), 15 on the grid (2), 10 on the flags (3), 10 on the design of the threshold (4) and 15 on the follow-up (5). Hold back the ABS hint until a student has flagged only increases. Collect the workbook and the half-page explanation.

## Step-by-step solution

### Requirement (1): The PivotTable

**Step 1. Build it.** Insert a PivotTable from the InvoiceLines Table on a worksheet named `Ex 6.5`. Drag ItemGroup to **Rows**, FiscalQuarter and then FiscalYear to **Columns**, and LineTotal to **Values**. Open the **Column Labels** filter and keep 2025 and 2026. Remove the Grand Total column at the right.

**Check:** each group has four quarters under each year. **Watch for:** FiscalYear above FiscalQuarter, which groups the quarters under the years and changes the labels the formulas need.

### Requirement (2): The expectation grid

**Step 2. Put the thresholds in cells.** On `Ex 6.5 Expectation` enter `0.1` as the percentage threshold in B3 and `50000` as the dollar threshold in B4, both in blue.

**Step 3. Build the grid.**

a. List each item group with each quarter, one row for each, from row 7.
b. In the expectation column read the prior year's revenue from the PivotTable, in the recorded column the report year's, and calculate the difference and the percentage of the expectation.

```
=GETPIVOTDATA("Sum of LineTotal",'Ex 6.5'!$A$3,"ItemGroup",$A7,"FiscalQuarter",$B7,"FiscalYear",2025)
=E7/C7
```

**Check:** the grid has 20 rows, and Furniture's first quarter reads $4,301,703.57 against $4,354,122.83. **Watch for:** a percentage divided by the recorded amount, not the expectation.

### Requirement (3): Flag the differences

**Step 4. Enter the flag.** In column G enter the rule, and shade the flagged rows with a conditional formatting rule based on column G.

```
=AND(ABS(E7)>$B$3*C7,ABS(E7)>$B$4)
```

**Step 5. List the flagged differences.** Filter the grid on the flag, or use a formula that returns the flagged rows, and count them with `=COUNTIF(G7:G26,TRUE)`.

> **[Figure placeholder IF-06-5-A]** The expectation worksheet of Requirements 2 and 3, with the flagged rows highlighted and the list of flagged differences beside the grid.
> Kind: excel-mock · Shows: The worksheet Ex 6.5 Expectation. Two input cells in blue at the top, a percentage threshold and a dollar threshold. Below, a grid with columns item group, quarter, expectation, recorded, difference, difference percent and flagged, one row for each group and quarter, with the flagged rows shaded. To the right, a list of the flagged differences filled by a formula, and a cell that counts them. · Data: The expectation grid and the flagged rows (the Expected results). · Status: planned

**Check:** 6 flagged: Lighting Q1 +$215,084.80 (+15.9%); Textiles Q4 +$166,764.46 (+24.4%); Accessories Q2 -$76,547.35 (-15.0%); Services Q2 -$66,187.40 (-20.9%); Services Q3 -$52,688.80 (-16.4%); Services Q4 +$77,195.65 (+26.9%). **Watch for:** `ABS` missing. The test then flags only the increases and misses the decreases.

### Requirement (4): The design of the threshold

**Step 6. Find the largest unflagged difference.** Sort the unflagged rows by the absolute difference (a helper column with `ABS`, or SORTBY). The largest are Furniture Q4 (-$315,983.47, -7.1%) and Furniture Q2 (+$266,724.77, +6.2%).

**Check:** the model answer says that both are several times the dollar threshold and below 10 percent, because Furniture is the largest product line. Requiring both conditions lets the percentage test screen out large dollar differences in the largest line, while small lines such as Services are flagged for differences that matter less in dollars. A tolerable amount from materiality, or an expectation that reflects known changes, would treat them differently.

### Requirement (5): The follow-up

**Step 7. Plan the evidence.** Pick one flagged difference. The model answer picks Services Q4: $363,913.55 against an expectation of $286,717.90 (+26.9%). Evidence: the design-service invoice lines of the quarter by engagement and customer, the engagement and time records behind the hours billed, the rates against the approved list, and invoices near the quarter-end checked for cutoff. Questions for management: which engagements started or ended, whether rates or staffing changed, and whether any work was billed in advance or late. The note's example, Lighting Q1, is mostly volume (units +15.2%, price per unit +0.6%), so the evidence is its lines by customer and item traced to orders and shipping documents.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Cells in the grid; flagged | 20; 6 | 3, 5 |
| Lighting Q1: expectation; recorded; difference | $1,354,295.75; $1,569,380.55; $215,084.80 | 5 |
| Textiles Q4: expectation; recorded; difference | $683,468.96; $850,233.42; $166,764.46 | 5 |
| Accessories Q2: expectation; recorded; difference | $509,910.16; $433,362.81; -$76,547.35 | 5 |
| Services Q2: expectation; recorded; difference | $316,256.50; $250,069.10; -$66,187.40 | 5 |
| Services Q3: expectation; recorded; difference | $320,830.05; $268,141.25; -$52,688.80 | 5 |
| Services Q4: expectation; recorded; difference | $286,717.90; $363,913.55; $77,195.65 | 5 |
| Largest unflagged difference | Furniture Q4, -$315,983.47 | 6 |
| Total revenue growth, the context of the expectation | +1.29% | 6 |

> **Instructor notes, Exercise 6.5:** flagged (over 10% and over \$50,000): Lighting Q1 +215,084.80 (+15.9%), Textiles Q4 +166,764.46 (+24.4%), Accessories Q2 -76,547.35 (-15.0%), Services Q2 -66,187.40 (-20.9%), Services Q3 -52,688.80 (-16.4%), Services Q4 +77,195.65 (+26.9%). Not flagged: Furniture Q4 -315,983.47 (-7.1%), the largest dollar difference, and Furniture Q2 +266,724.77 (+6.2%). A percentage test alone misses large dollar differences in the largest product line; a tolerable amount based on materiality, or an expectation that reflects known changes such as the promotion, would treat them differently. Prior-year revenue is a weak expectation because it ignores growth and known events, which students may note. Follow-up examples: Lighting Q1, the largest flagged difference, is mostly volume (units +15.2%, price per unit +0.6%), so the evidence is its invoice lines by customer and item, traced to their orders and shipping documents, and the question is which customers bought more and why; for Services, engagement and time records by quarter. Furniture Q4, which the threshold misses, would still call for the promotion discounts (Tutorial 6.3) and the late-invoiced promotion lines (Tutorial 5.2).

## What a strong answer says

- **Requirement (4).** The threshold reads two conditions, and the percentage condition decides: it misses Furniture Q4 although that is the largest difference in dollars. The explanation adds that the quarter holds the promotion discounts of Tutorial 6.3, that a threshold from materiality or an expectation adjusted for known events would behave differently, and that prior-year revenue ignores growth and events.
- **Requirement (5).** A specific population (the lines of the quarter by customer or engagement), specific documents (orders, shipments, time records, rates) and questions for management that name what changed. A follow-up that ends at "ask management" is weak.

A weak answer calls the threshold wrong without saying what it was designed to do, or follows up with a generic list.

## Common mistakes and how to respond

- **Only increases flagged.** *Symptom:* 3 flags. *Response:* ask what a revenue shortfall means for the test.
- **Either-or.** *Symptom:* 13 flags, including small percentages. *Response:* ask what each condition is for.
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

- Adjust the expectation by the company's growth of 1.29%. The number flagged is 6: what does that say about the weakness of the expectation?
- Replace the dollar threshold with a share of the line's own revenue and compare.
- Discuss: which flagged or unflagged difference would you test first, and why?
- Discuss: Chapter 7 develops better expectations (trends and forecasts). What would change in this exercise?
