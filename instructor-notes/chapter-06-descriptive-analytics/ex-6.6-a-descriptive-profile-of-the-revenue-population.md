# Exercise 6.6: A Descriptive Profile of the Revenue Population

| | |
|---|---|
| Unit | Chapter 6: Descriptive and Diagnostic Analytics in Excel |
| Item | Exercise 6.6 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheets Ex 6.6 and Ex 6.6 Customers |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Before an audit team designs detailed tests of revenue, it profiles the population: what a normal line looks like, where the revenue is concentrated and how the lines were priced. This exercise applies the whole chapter to that task: statistics by group, a PivotTable of customers, pricing methods and promotions, and a written profile that points to matters for the audit. The analytics type is descriptive.

By the end, students can:

- profile a population by group with counts, totals, averages and medians, and say why the average exceeds the median (outcome 1);
- measure concentration by customer and by pricing method with PivotTables (outcomes 2 and 3);
- write a profile that distinguishes a description from a finding and names matters for the audit (outcome 5).

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis of financial data) and Core S2 M9 (audit procedures and audit data analytics); IMA Statistical Analysis and Data Analysis; IFAC IES 2 (f) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3. The model answer uses FILTER, SORT, UNIQUE and TEXTJOIN (Microsoft 365).
- **Data conditions.** The year has 9,522 lines and 209 customers invoiced. Two customers invoiced in the year share the name Brown LLC (customers 5 and 173), so a PivotTable by name merges them. 796 lines carry a promotion and 8,726 do not, so the blank PromotionID row is the large one and is meaningful. Two promotions of the year before (Textiles Seasonal Promotion and Wholesale Customer Promotion) have lines invoiced in the report year.
- **Matters the profile may name.** The late-invoiced promotion lines, a promotion whose end date is before its start date, and the approved overrides. Chapter 8 returns to them, so the profile should notice and not resolve them.

## How to run it

Individual, about 90 minutes: 15 on requirement 1, 20 on requirement 2, 15 on requirement 3, 20 on requirement 4 and 20 on the profile. Hold back the two-condition FILTER until a student's median is the same in every row. Collect the workbook and the profile.

## Step-by-step solution

### Requirement (1): Statistics by item group

**Step 1. Build the table.** On `Ex 6.6`, list the five item groups from row 5. For each group enter the count, the total, the average and the median, and add a total row.

```
=COUNTIFS(InvoiceLines[ItemGroup],$A5,InvoiceLines[FiscalYear],2026)
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$A5,InvoiceLines[FiscalYear],2026)
=AVERAGEIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$A5,InvoiceLines[FiscalYear],2026)
=MEDIAN(FILTER(InvoiceLines[LineTotal],(InvoiceLines[FiscalYear]=2026)*(InvoiceLines[ItemGroup]=A5)))
```

**Check:** Furniture 3,496 lines, $17,395,054.38, average $4,975.70, median $4,467.08; Lighting 2,496 lines, $5,997,536.93, average $2,402.86, median $2,006.90; Textiles 1,359 lines, $3,278,211.11, average $2,412.22, median $1,778.18; Accessories 2,027 lines, $1,872,273.66, average $923.67, median $815.28; Services 144 lines, $1,213,344.00, average $8,426.00, median $7,803.20. **Watch for:** the same median in every row, from a FILTER with no group condition, or an error from conditions joined with a comma or `&`. Two conditions in FILTER are multiplied.

### Requirement (2): Customer concentration

**Step 2. Build the customer PivotTable.** On `Ex 6.6 Customers`, insert a PivotTable with FiscalYear in **Filters** (select 2026), CustomerID in **Rows** and LineTotal in **Values**, and sort CustomerID by revenue from largest to smallest.

**Step 3. Add names and shares.** Beside the PivotTable look up each customer's name and segment from the Customer Table with XLOOKUP on CustomerID, divide each revenue by the grand total and accumulate the shares.

**Check:** the five largest hold 9.9% and the ten largest 17.8% of revenue, all in the Strategic segment. The five are Glenn-Estrada; Wright PLC; Eaton, Robertson and Grant; Richardson, Porter and Chavez; Thomas Ltd. **Watch for:** the ranking by name. Grouped by name, Brown LLC (customers 5 and 173, $468,165.51 together) ranks number 9 and the ten largest hold 18.0%, not 17.8%. Customers are identified by key.

### Requirement (3): Pricing methods

**Step 4. Build the pricing PivotTable.** Insert a PivotTable with FiscalYear in **Filters**, PricingMethod in **Rows**, ItemGroup in **Columns**, and SalesInvoiceLineID (as a count), LineTotal and LineTotal as **% of Grand Total** in **Values**.

**Check:** Segment Price List 83.6% of revenue (8,405 lines); Customer Price List 10.7% of revenue (816 lines); Base List 4.1% of revenue (144 lines); Approved Override 1.6% of revenue (157 lines). **Watch for:** the count field summed. SalesInvoiceLineID is a number, so Excel sums it until it is changed to **Count**. The base list prices only the hourly design services.

### Requirement (4): Promotions

**Step 5. Build the promotion PivotTable.** Insert a PivotTable with FiscalYear in **Filters**, PromotionID in **Rows**, and the count of lines and the sum of DiscountAmount in **Values**.

**Step 6. Share and dates.** Next to it calculate each group's promotion lines over its lines (for example `=COUNTIFS(InvoiceLines[ItemGroup],$A57,InvoiceLines[FiscalYear],2026,InvoiceLines[PromotionID],"<>")`), and look up each promotion's name and dates from PromotionProgram to see which ran in the year before.

**Check:** promotions 5 (10 lines, $662.89); 6 (54 lines, $6,858.14); 7 (68 lines, $30,478.57); 8 (576 lines, $296,053.58); 9 (88 lines, $28,057.57). Promotion lines as a share of each group's lines: Furniture 19.9%, Textiles 2.1%, Accessories 1.7%, Lighting 1.5%, Services 0.0%. The promotions of the year before are 5 (Textiles, September to October 2025) and 6 (Wholesale, November 2025), invoiced from January to March. **Watch for:** a promotion with no lines in the year left out of the lookup, and the blank row (8,726 lines) read as missing data. It means no promotion.

### Requirement (5): The profile

**Step 7. Write three to five paragraphs.** Population (lines, revenue, a normal line by group, the average above the median in every group), concentration (Furniture's share of revenue, the shares of the largest customers), pricing (the methods and the promotions), and matters for the audit.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Lines; revenue; customers invoiced | 9,522; $29,756,420.08; 209 | 1, 2 |
| Top five and top ten customers, share of revenue | 9.9%; 17.8% | 3 |
| Share of revenue by pricing method | 83.6%; 10.7%; 4.1%; 1.6% | 4 |
| Promotion lines; discounts | 796; $362,110.75 | 5 |
| Largest promotion: lines; discount | 8: 576; $296,053.58 | 5 |
| Promotion with end date before start date | 7: 2026-03-01 to 2026-02-28 | 6 |

> **Instructor notes, Exercise 6.6:** 2026 by group (lines, revenue, average, median): Furniture 3,496, 17,395,054.38, 4,975.70, 4,467.08; Lighting 2,496, 5,997,536.93, 2,402.86, 2,006.90; Textiles 1,359, 3,278,211.11, 2,412.22, 1,778.18; Accessories 2,027, 1,872,273.66, 923.67, 815.28; Services 144, 1,213,344.00, 8,426.00, 7,803.20. 209 customers invoiced in 2026; top 5 hold 9.9% and top 10 hold 17.8% of revenue, all in the Strategic segment (largest: Glenn-Estrada, Wright PLC, Eaton, Robertson and Grant, Richardson, Porter and Chavez, Thomas Ltd), a modest concentration by this measure, which by itself says nothing about credit or audit risk (related customers, receivables, and trends would). Pricing by revenue: Segment Price List 83.6% (8,405 lines), Customer Price List 10.7% (816), Base List 4.1% (144, the hourly design services only), Approved Override 1.6% (157). Promotions in 2026 (lines, discount): 5: 10, 662.89; 6: 54, 6,858.14; 7: 68, 30,478.57; 8: 576, 296,053.58; 9: 88, 28,057.57. Promotion lines as a share of each group's lines: Furniture 19.9%, Textiles 2.1%, Accessories 1.7%, Lighting 1.5%, Services 0%. Promotions 5 (Textiles, September to October 2025) and 6 (Wholesale, November 2025) have lines invoiced in January to March 2026, the same late-invoicing pattern as promotion 8. Promotion 7's effective dates are left for the audit work later in Part II.

## What a strong answer says

- **Population.** A normal line is a few thousand dollars and depends on the group. Design services are fewer and larger. In every group the average exceeds the median, consistent with a right tail of large lines. The largest lines can be tested on their own, with procedures for the rest designed for the audit objective, so the profile alone does not set a sample.
- **Concentration.** Revenue is concentrated in Furniture, not in customers, and the ten largest customers are modest in share. The profile does not infer risk from the share alone.
- **Pricing.** Segment price lists carry most of the revenue, and approved overrides, the one manual path, are small.
- **Matters for the audit.** Discounts are billed after promotions ended, one promotion's dates are inconsistent, and overrides are natural targets. The profile names them as questions, not conclusions.

A weak profile repeats the PivotTable values without reading them, or states findings the data cannot show.

## Common mistakes and how to respond

- **One median for every group.** *Symptom:* the same value in all rows. *Response:* ask which rows the FILTER returned.
- **Ranking by name.** *Symptom:* Brown LLC among the ten largest as one customer. *Response:* ask what identifies a customer.
- **Shares of the wrong total.** *Symptom:* shares that do not reach 100 percent. *Response:* check the year filter on the PivotTable.
- **A summed count.** *Symptom:* a "count" of millions. *Response:* open **Value Field Settings**.
- **A blank read as missing.** *Symptom:* a note asking where the promotion went. *Response:* ask what a line with no promotion has in this column.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: statistics | 20 | Counts, totals, averages and medians by group, FILTER with two conditions | Median of the whole year |
| Requirement 2: customers | 20 | By CustomerID, names looked up, top five and ten shares | By name, or no shares |
| Requirement 3: pricing | 15 | Counts and shares by method and group | Revenue only |
| Requirement 4: promotions | 20 | Counts, discounts, group shares, late promotions named | One part missing |
| Requirement 5: the profile | 25 | Population, concentration, pricing and audit matters, each tied to a number | Descriptive only |

## Extensions and discussion questions

- Add the bins of Tutorial 6.1 for each group and compare the shapes.
- Rank the largest lines and say what share of revenue the top tenth of lines holds, and compare it with the customer concentration.
- Discuss: why does modest concentration by customer say nothing about credit or audit risk by itself?
- Discuss: Chapter 8 tests the promotion dates and the overrides. Which would you test first, and why?
