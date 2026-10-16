# Exercise 6.2: Disaggregating Revenue by Segment and Product Line

| | |
|---|---|
| Unit | Chapter 6: Descriptive and Diagnostic Analytics in Excel |
| Item | Exercise 6.2 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheet Ex 6.2 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The revenue standard asks a company to break revenue into categories that show how economic factors affect it, and offers product lines and types of customer as examples. This exercise asks students to prepare that first cut from InvoiceLines with PivotTables, to read it against the previous year, and to say what stands between an invoice-based schedule and the number in the financial statements. It practices two-dimensional PivotTables, Show Values As and a disclosure paragraph. The analytics type is descriptive.

By the end, students can:

- build a PivotTable by two dimensions and show it as a share of the grand total (outcome 3);
- compare two years with % Difference From and choose which changes deserve a mention (outcomes 3 and 5);
- justify the categories of a disclosure and list what must be reconciled before it could be used (outcome 5).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S1 M8 T5 to T6 (visualization and communicating results); IMA Data Visualization and Financial Statement Analysis; IFAC IES 2 (a) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3. The solution puts all three PivotTables on one worksheet, `Ex 6.2`, with the calculated fields of the tutorials in the shared pivot cache.
- **Data conditions.** Segments crossed with item groups give 17 combinations with revenue, not the full grid: Design Services buys only Services, and only Design Services buys Services. Of these, 12 had at least $500,000 in fiscal 2025, and every combination with revenue in fiscal 2026 also had revenue in fiscal 2025, so % Difference From always finds a base. Customers are spread over 4 regions.
- **Requirement 5.** It needs the reconciling items of Exercise 6.1. Assign that exercise first, or give students the amounts in the Expected results.

## How to run it

Individual, about 75 minutes: 15 on requirement 1, 25 on requirements 2 and 3, 20 on the paragraph, 15 on the reconciliation. Hold back the Show Values As route for the change column until a student has tried to compute it by hand. Collect the workbook and the paragraph.

## Step-by-step solution

### Requirement (1): Shares of the grand total

**Step 1. Build the first PivotTable.**

a. Select a cell in the InvoiceLines Table and choose **Insert > PivotTable**. Place it on a new worksheet named `Ex 6.2`.
b. Drag FiscalYear to **Filters** and select 2026, CustomerSegment to **Rows**, ItemGroup to **Columns** and LineTotal to **Values**.
c. Open **Value Field Settings**, and on the **Show Values As** tab choose **% of Grand Total**. Format the field as a percentage.

**Check:** the grand total reads 100 percent and the largest combinations are Wholesale-Furniture (31.68%, $9,427,365.72), Strategic-Furniture (18.24%) and Wholesale-Lighting (10.59%). **Watch for:** the FiscalYear filter left on (All), which gives shares of three years.

### Requirement (2): Change from the previous year

**Step 2. Build the second PivotTable.**

a. Insert a second PivotTable below the first. Drag CustomerSegment to **Rows**, FiscalYear and then ItemGroup to **Columns**, and LineTotal to **Values** twice.
b. Open the **Column Labels** filter and clear 2024, so that 2025 and 2026 remain.
c. Open **Value Field Settings** of the second LineTotal field, type `Change from 2025` in **Custom Name**, and on **Show Values As** choose **% Difference From** with FiscalYear as the **Base field** and **(previous)** as the **Base item**.
d. Drag **Σ Values** from **Columns** to **Rows**, below CustomerSegment.

![A mock of the second PivotTable of Requirement 2, with the year above the item group in the columns and the change as a second value row.](../figures/chapter-06-descriptive-analytics/IF-06-2-A.pdf)

**Check:** the change appears only under 2026.

**Step 3. Rank the combinations.** Among the 12 combinations with at least $500,000 in fiscal 2025, find the largest and smallest changes. The two largest increases are Strategic-Lighting (+13.3%, $1,732,738.56 to $1,962,917.54) and Wholesale-Lighting (+9.3%). The two largest decreases are Strategic-Accessories (-17.8%) and Design Trade-Furniture (-11.4%).

**Watch for:** the $500,000 floor forgotten. Small Business-Accessories (+19.9% on $75,949.13) and Design Trade-Textiles (+15.6%) change more in percent, on small bases.

### Requirement (3): The same comparison by region

**Step 4. Repeat with Region.** Insert a third PivotTable with Region in **Rows** instead of CustomerSegment, and the same year filter and change field.

**Check:** the changes are West +9.9%, Northeast +9.2%, Midwest -2.0% and South -7.2%, and the segments Wholesale +6.0%, Small Business +3.9%, Strategic -2.9%, Design Services -3.8% and Design Trade -6.7%. Total revenue changes +1.29%. **Watch for:** the design services row of the region table. It swings by more than 100 percent in one region (South: +240%; West: -70%) on a small base, so a region-by-product reading overstates the news.

### Requirement (4): The disclosure paragraph

**Step 5. Write four to six sentences.** The model path: state the categories (product line and type of customer) and why; give the year's revenue and the shares (Furniture 58.5%, Lighting 20.2%, Textiles 11.0%, Accessories 6.3%, design services 4.1%; Wholesale 51.3% of revenue by customer type); name the largest combinations; summarize the changes; and present the region as supplementary.

### Requirement (5): What must be reconciled

**Step 6. Build the ladder.** Start from the invoice lines ($29,756,420.08), add the cutoff invoices that the ledger records in fiscal 2026 ($4,582.37) and freight revenue, which has no invoice line ($212,820.03), to reach operating revenue ($29,973,822.48), then deduct sales returns and allowances ($242,764.56) to reach net revenue ($29,731,057.92).

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Largest combination, share of revenue | Wholesale-Furniture, 31.68% | 1 |
| Second and third | Strategic-Furniture 18.24%; Wholesale-Lighting 10.59% | 1 |
| Largest increase, 2026 on 2025 | +13.3% | 3 |
| Largest decrease | -17.8% | 3 |
| Total revenue, 2026; 2025 | $29,756,420.08; $29,376,702.28 | 4 |
| Reconciling items to net revenue | $4,582.37; $212,820.03; -$242,764.56 | 6 |

> **Instructor notes, Exercise 6.2:** 2026 shares of grand total: Wholesale-Furniture 31.68% (9,427,365.72), Strategic-Furniture 18.24% (5,426,213.53), Wholesale-Lighting 10.59% (3,149,776.65); then Strategic-Lighting 6.60% and Design Trade-Furniture 6.05%. Changes from 2025 for combinations with at least \$500,000 in 2025: increases Strategic-Lighting +13.3% (1,732,739 to 1,962,918) and Wholesale-Lighting +9.3% (2,882,869 to 3,149,777); decreases Strategic-Accessories -17.8% (693,226 to 569,622) and Design Trade-Furniture -11.4% (2,030,430 to 1,799,124). Segments: Wholesale +5.99%, Small Business +3.85%, Strategic -2.86%, Design Services -3.81%, Design Trade -6.66%; total +1.29%. Regions: West +9.9%, Northeast +9.2%, Midwest -2.0%, South -7.2%. Design Services buys only Services, so the segment and the product line coincide there. Requirement (5): the invoice-based revenue differs from the revenue the income statement reports by freight revenue (4050, which has no invoice line), sales returns and allowances (4060, the credit memos), and the three cutoff invoices of Exercise 6.1, which the ledger records in a different year from their invoice dates. A nonpublic entity may elect not to give the quantitative disaggregation (ASC 606-10-50-7); the exercise treats the disclosure as if it were required.

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
