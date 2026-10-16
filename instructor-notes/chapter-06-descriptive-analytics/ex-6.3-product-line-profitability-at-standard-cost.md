# Exercise 6.3: Product-Line Profitability at Standard Cost

| | |
|---|---|
| Unit | Chapter 6: Descriptive and Diagnostic Analytics in Excel |
| Item | Exercise 6.3 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 60 minutes |
| Solution file | Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheet Ex 6.3 |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial 6.2 built a margin percentage for each quarter. This exercise turns it into a profitability ranking for one year, adds a dollar margin, and asks which lines contribute more margin than revenue. It is the lightest exercise of the chapter and the one that most directly practices calculated fields. The analytics type is descriptive.

By the end, students can:

- define a margin in dollars and a margin percentage as calculated fields, and explain why the percentage is a weighted margin (outcome 4);
- compare each line's share of revenue with its share of margin, and say why Services must be treated separately (outcome 3);
- rank the Furniture product types by margin percentage and read the codes of Chapter 5 (outcome 3).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Cost Accounting and Performance Management; IFAC IES 2 (b) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3, with the StdCostAmount column and the MarginPct calculated field. The solution reads the PivotTable with GETPIVOTDATA for the shares.
- **Data conditions.** Services items carry a standard cost of 0, so the Services margin is 100 percent and the grand total's margin percentage ($13,953,147.20 on $29,756,420.08, 46.89%) is higher than that of the product lines alone (44.63%). The Furniture product types differ by only 5.3 points of margin. The code TBL is also used outside Furniture, so the Furniture filter matters.
- **The cost definition.** Requirement 4 has no single answer. The model answer compares two definitions, which is the point.

## How to run it

Individual, about 60 minutes: 15 on requirement 1, 15 on requirement 2, 15 on requirement 3 and 15 on the explanation. Hold back the shares-without-Services idea until students have seen the Services row. Collect the workbook and the explanation.

## Step-by-step solution

### Requirement (1): Revenue, margin and margin percentage

**Step 1. Build the PivotTable.**

a. Insert a PivotTable from the InvoiceLines Table on a new worksheet named `Ex 6.3`. Drag FiscalYear to **Filters** and select 2026, and ItemGroup to **Rows**.
b. Choose **PivotTable Analyze > Fields, Items, & Sets > Calculated Field**, name it `Margin` and enter `=LineTotal-StdCostAmount`.
c. Drag LineTotal, Margin and MarginPct to **Values**, rename them `Revenue`, `Margin (dollars)` and `Margin %`, and format them.

**Check:** the Expected results table. **Watch for:** a per-row ratio column averaged in the PivotTable. That is an unweighted margin and differs from the calculated field, which divides total margin by total revenue.

### Requirement (2): Shares without Services

**Step 2. Compute the shares.** Beside the PivotTable list the four product lines, read each line's revenue and margin with GETPIVOTDATA, total them without Services, and divide. Flag the lines whose share of margin exceeds their share of revenue with `=K6>J6` and the like. A student can instead clear Services in the ItemGroup filter and show two extra value fields as **% of Column Total**.

**Check:** shares of revenue and margin: Furniture 60.9% and 57.8%; Lighting 21.0% and 22.0%; Textiles 11.5% and 12.7%; Accessories 6.6% and 7.5%. The lines with the larger margin share are Lighting, Textiles, and Accessories. **Watch for:** Services left in the denominators. Its 100 percent margin then changes the answer for Lighting: its margin share becomes 20.1% against a revenue share of 20.2%.

### Requirement (3): Furniture product types

**Step 3. Switch to product type.** Build a second PivotTable with ItemGroup in **Filters** set to Furniture, ProductType in **Rows** and the three value fields, and sort the types by Margin % from largest to smallest. Read the two highest and the two lowest, and name them with the codes of Chapter 5.

**Check:** the order is DSK (desk) 44.36%, CON (console table) 44.00%, SDB (sideboard) 43.08%, CTB (coffee table) 41.84%, NGT (nightstand) 41.84%, TBL (dining table) 41.46%, BKC (bookcase) 39.37%, BNH (bench) 39.04%. **Watch for:** the Furniture filter missing. TBL then mixes in the other lines that use the code, and its margin reads 43.31% instead of 41.46%.

### Requirement (4): The Services margin

**Step 4. Explain it.** Three to five sentences. The model answer says that the PivotTable values every line at its item's standard cost, that the design-service items carry a standard cost of 0, and that the cost of a design service is the time of the design staff, recorded in the time records and in payroll. To measure the margin you need the cost of the hours behind the services billed. The model answer offers two measures: the time records' extended cost for the year ($220,317.28, a margin of about 82%) or the year's Design Services salaries expense ($471,214.88, about 61%). The gap shows that the margin depends on the cost definition, which a report must state.

**Check:** the explanation names the missing standard cost and one cost source. **Watch for:** the 100 percent read as a finding. Neither of the two sources is loaded in the student workbook, so students describe the data they would ask for.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Accessories: revenue; margin; margin percentage | $1,872,273.66; $954,080.96; 50.96% | 1 |
| Textiles: revenue; margin; margin percentage | $3,278,211.11; $1,621,892.16; 49.47% | 1 |
| Lighting: revenue; margin; margin percentage | $5,997,536.93; $2,798,584.12; 46.66% | 1 |
| Furniture: revenue; margin; margin percentage | $17,395,054.38; $7,365,245.96; 42.34% | 1 |
| Services: revenue; margin percentage | $1,213,344.00; 100% | 1 |
| Grand total margin percentage | 46.89% | 1 |
| Highest and lowest Furniture type | DSK 44.36%; BNH 39.04% | 3 |

> **Instructor notes, Exercise 6.3:** 2026 margin at standard cost: Accessories 50.96% (margin 954,080.96 on 1,872,273.66), Textiles 49.47% (1,621,892.16 on 3,278,211.11), Lighting 46.66% (2,798,584.12 on 5,997,536.93), Furniture 42.34% (7,365,245.96 on 17,395,054.38). Excluding Services, revenue shares are Furniture 60.9%, Lighting 21.0%, Textiles 11.5%, Accessories 6.6%, and margin shares 57.8%, 22.0%, 12.7%, 7.5%, so Lighting, Textiles, and Accessories contribute more margin than revenue. Furniture types: highest DSK (desk) 44.36% and CON (console table) 44.00%; lowest BNH (bench) 39.04% and BKC (bookcase) 39.37%. Services items carry StandardCost 0, so their margin shows 100%; their cost is design staff time. Possible measures: ServiceTimeEntry.ExtendedCost for 2026 work dates (220,317.28, a margin of about 82%) or the 2026 Design Services salaries expense in account 6280 (471,214.88, about 61%). The gap shows that the answer depends on the cost definition, which the report must state.

## What a strong answer says

- **Requirement (2).** Lighting, Textiles, and Accessories contribute more margin than revenue, because their margins are above Furniture's. The shares exclude Services, whose margin percentage is an artifact.
- **Requirement (3).** The two highest types are DSK (desk) and CON (console table) and the two lowest BNH (bench) and BKC (bookcase), with the margin spread across types small.
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
