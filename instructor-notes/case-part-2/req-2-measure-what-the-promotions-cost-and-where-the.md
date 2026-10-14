# Requirement 2: Measure what the promotions cost and where the cost appears (Chapter 6)

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Item | Requirement 2 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | PartII-case.zip: Charles River Promotion Case.xlsx, sheets R2 Cost (PivotTable PromotionCost) and R2 Gross to Net, with the queries BilledLines, RevenuePostings, LedgerActivity, Accounts and Items |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 2 answers the controller's first question, the financial reporting one: what did three years of promotions cost, and where does the cost show in the statements? It puts Chapter 6 to work on a cost that no ledger account records, so students must build the number from the invoice lines and then explain why the ledger cannot show it. The analytics type is descriptive.

By the end, students can:

- summarize a cost by promotion and year with a PivotTable and express it as a share of revenue;
- build a gross-to-net schedule that separates price-list and override reductions from promotional discounts;
- tie billed revenue to the ledger by account and explain the difference by the invoices that caused it;
- say what the income statement shows and does not show about a price reduction.

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and M8 T3 to T4 (data mining and analysis); IMA Reporting and Control (financial recordkeeping, financial statement preparation) and strategic cost management; IFAC IES 2 (a), financial accounting and reporting; AACSB A5 part 5.1.

## Before you assign

- **From Requirement 1.** The `BilledLines`, `RevenuePostings`, `Accounts` and `Items` queries with their checks agreeing. From Chapter 6 the PivotTable and the tie from ledger to statements; Exercise 6.1 introduced the three invoices dated in the prior year and posted on 1 January.
- **Data conditions.** Only promotion lines carry a discount, so the discount total is the cost of the promotions (2,108 billed lines of 27,933). The design services carry no reductions and no discounts. Each item group posts its revenue to one account through Item.RevenueAccountID. Account 4070, Sales Discounts, exists and has no postings.
- **A limit of the case's queries.** `RevenuePostings` holds only the report year's sales-invoice postings, so it can show that no invoice posted to 4070 that year. The claim that the account was never used, in any year, needs the ledger across years; the model answer adds a `LedgerActivity` query for it. Accept the narrower statement from a student who states its scope.

## How to run it

Individual work, about 75 minutes: 20 on the PivotTable and chart, 20 on gross to net, 20 on the tie and the discount account, 15 on the quarters. Hold back the cutoff hint until a student has a difference and cannot place it. **Collect** the three tables (cost by year, gross to net, the tie) for the appendix.

![A mock of the PivotTable of promotional discount and billed lines by promotion and invoice year, with a chart of the yearly totals beneath it.](../figures/case-part-2/IF-C2-2-A.pdf)

## Step-by-step solution

### Phase 1: The cost by promotion and year

**Step 1. Build the PivotTable.**

a. Select a cell in `BilledLines` and choose **Insert > PivotTable**; place it on a new worksheet (the model answer names it `R2 Cost`).
b. Drag PromotionID to **Rows**, InvoiceYear to **Columns**, DiscountAmount to **Values** (Sum) and SalesInvoiceLineID to **Values** (Count), and rename the count `Count of lines`.
c. Open the PromotionID filter and clear (blank), the lines with no promotion.

**Check:** the grand total is $723,253.10 of discount on 2,108 lines. Promotions 2, 3, 5, and 6 show a second column of discount: their orders were invoiced in the year after they ran. The PivotTable sums unrounded amounts, so its total is a cent or so from the $723,253.11 that the yearly table of Step 2 gets by rounding each year.

**Watch for:** the (blank) row left in. It adds 25,825 lines and no discount, and the line total reads 27,933.

**Step 2. Express each year as a share of billed revenue, and chart it.**

a. For each invoice year, with the year in column A (`FirstYear` and then one more each row), enter:

```
=ROUND(SUMIFS(BilledLines[DiscountAmount],BilledLines[InvoiceYear],A21),2)
=SUMIFS(BilledLines[LineTotal],BilledLines[InvoiceYear],A21)
```

b. Divide the first by the second for the share.
c. Select the years and the discounts and choose **Insert > Insert Column or Bar Chart > Clustered Column**.

**Check:**

- 2024: $126,607.64, 0.46% of $27,313,723.48 billed.
- 2025: $234,534.72, 0.80% of $29,376,702.28 billed.
- 2026: $362,110.75, 1.22% of $29,756,420.08 billed.

The cost nearly tripled in two years. Rounding each line before summing, as Exercise 4.2 did, gives $723,253.29 in all against $723,253.11; both are correct, and the memo should state which it uses.

### Phase 2: Gross to net

**Step 3. Build the schedule by item group for the report year.** One row for each item group, with these columns:

```
List amount:         =SUMIFS(BilledLines[ListAmount],BilledLines[ItemGroup],$A5,BilledLines[InvoiceYear],ReportYear)
Price-list and override reductions:  =B5-SUMIFS(BilledLines[GrossAmount],BilledLines[ItemGroup],$A5,BilledLines[InvoiceYear],ReportYear)
Promotional discounts:  =SUMIFS(BilledLines[DiscountAmount],BilledLines[ItemGroup],$A5,BilledLines[InvoiceYear],ReportYear)
Net billed:          =SUMIFS(BilledLines[LineTotal],BilledLines[ItemGroup],$A5,BilledLines[InvoiceYear],ReportYear)
Line rounding:       =E5-(B5-C5-D5)
```

Add a total row and, optionally, a waterfall from the total row.

**Check:**

| Item group | List | Reductions | Promotions | Net billed |
|---|---:|---:|---:|---:|
| Furniture | $19,878,268.16 | $2,135,349.32 | $347,864.64 | $17,395,054.38 |
| Lighting | $6,726,924.19 | $721,561.68 | $7,825.54 | $5,997,536.93 |
| Textiles | $3,672,558.39 | $390,249.46 | $4,098.06 | $3,278,211.11 |
| Accessories | $2,098,042.72 | $223,446.85 | $2,322.51 | $1,872,273.66 |
| Services | $1,213,344.00 | $0.00 | $0.00 | $1,213,344.00 |
| Total | $33,589,137.45 | $3,470,607.31 | $362,110.75 | $29,756,420.08 |

List less reductions less promotions is $29,756,419.39; the $0.69 to the net is the rounding of LineTotal line by line. **Watch for:** reductions computed as list less LineTotal. That counts the promotional discount twice, once in the reductions and once in its own column, so the schedule is off by exactly the discount.

![The report year's gross-to-net walk, from list amount to net billed.](../figures/case-part-2/IF-C2-2-B.pdf)

### Phase 3: The ledger and where the cost appears

**Step 4. Tie net billed to the ledger.**

a. List the revenue accounts the item groups post to: look each group's RevenueAccountID up in `Items`, then its AccountNumber and AccountName in `Accounts`.
b. For each account, total its credits in `RevenuePostings` and compare with the group's net billed. To find the invoices behind a difference, total the lines whose invoice date is in the prior year but whose number carries the report year:

```
=SUMIFS(BilledLines[LineTotal],BilledLines[ItemGroup],C17,BilledLines[InvoiceYear],ReportYear-1,BilledLines[InvoiceNumber],"SI-"&ReportYear&"-*")
```

**Check:**

| Account | Group | Ledger credits | Net billed | Difference |
|---|---|---:|---:|---:|
| 4010 Sales Revenue - Furniture | Furniture | $17,398,287.56 | $17,395,054.38 | $3,233.18 |
| 4020 Sales Revenue - Lighting | Lighting | $5,998,649.16 | $5,997,536.93 | $1,112.23 |
| 4030 Sales Revenue - Textiles | Textiles | $3,278,211.11 | $3,278,211.11 | $0.00 |
| 4040 Sales Revenue - Accessories | Accessories | $1,872,510.62 | $1,872,273.66 | $236.96 |
| 4080 Sales Revenue - Design Services | Services | $1,213,344.00 | $1,213,344.00 | $0.00 |

The ledger is $29,761,002.45 against $29,756,420.08, a difference of $4,582.37. It is the invoices SI-2026-013741 to 013743, dated late in 2025 and posted on 2026-01-01, a cutoff matter from Exercise 6.1. **Watch for:** freight and sales tax. Freight Revenue (4050) comes from the invoice header, not the lines, so a student who adds it to the revenue accounts reads a difference of $219,199.03 instead; account 2050 holds the sales tax.

**Step 5. Say where the cost appears.** In `Accounts` find 4070 Sales Discounts, a contra revenue account, and look for it in `RevenuePostings` and the ledger: there are no postings. Each invoice line is recorded at its net price, so the revenue accounts already exclude every price reduction and the income statement shows net revenue and nothing about the promotions. The cost becomes visible only in a gross-to-net schedule, or if revenue were recorded at the price before the promotion and the discount in 4070. **Watch for:** 4060 Sales Returns and Allowances, which records returns, offered as the discount account.

**Step 6. Place the proposal's discounts in quarters.** Use SUMIFS on `BilledLines` by PromotionID, the report year and InvoiceQuarter.

**Check:**

| Promotion | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Harbor Collection Promotion | $7,596.99 | $22,524.82 | $356.75 | $0.00 |
| Furniture Seasonal Promotion | $0.00 | $0.00 | $95,996.97 | $200,056.61 |
| Design Trade Customer Promotion | $0.00 | $0.00 | $0.00 | $28,057.57 |

The three promotions billed $354,589.72, of which $228,114.18 (64%) fell in the fourth quarter, because the Furniture promotion's orders are invoiced after it ends (160 of its lines were) and the segment promotion runs in November. **Watch for:** `OrderLines` as the source. By order date the fourth quarter holds only 51%, and the lag, the point of the step, disappears.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Discount in all; billed lines | $723,253.11; 2,108 | 1 |
| Share of billed revenue, first and last year | 0.46%; 1.22% | 2 |
| Ledger credits; difference to net billed | $29,761,002.45; $4,582.37 | 4 |
| The proposal's discount; fourth-quarter share | $354,589.72; 64% | 6 |

> **Instructor notes, Requirement 2:** promotional discounts on billed lines (unrounded Quantity x UnitPrice x Discount): 2024 126,607.64 (0.46% of billed revenue of 27,313,723.48), 2025 234,534.72 (0.80% of 29,376,702.28), 2026 362,110.75 (1.22% of 29,756,420.08), in all 723,253.11 on 2,108 lines (Exercise 4.2's line-rounded total is 723,253.29). The cost nearly tripled in two years. By promotion: 1 28,124.77; 2 37,544.46; 3 67,454.55; 4 32,529.69; 5 52,089.86; 6 150,920.06; 7 30,478.57; 8 296,053.58; 9 28,057.57. Gross-to-net 2026 (list / price-list and override reductions / promotional discounts / net): Furniture 19,878,268.16 / 2,135,349.32 / 347,864.64 / 17,395,054.38; Lighting 6,726,924.19 / 721,561.68 / 7,825.54 / 5,997,536.93; Textiles 3,672,558.39 / 390,249.46 / 4,098.06 / 3,278,211.11; Accessories 2,098,042.72 / 223,446.85 / 2,322.51 / 1,872,273.66; Services 1,213,344.00 / 0 / 0 / 1,213,344.00; total 33,589,137.45 / 3,470,607.31 / 362,110.75 / 29,756,420.08. Gross less discounts is 29,756,419.39: the 0.69 difference is the rounding of LineTotal line by line. Ledger: SalesInvoice credits in 2026 to 4010 17,398,287.56, 4020 5,998,649.16, 4030 3,278,211.11, 4040 1,872,510.62, and 4080 1,213,344.00 total 29,761,002.45. The 4,582.37 difference is SI-2026-013741 to 013743 (3,233.18 to 4010, 1,112.23 to 4020, 236.96 to 4040), dated in late 2025 but posted 2026-01-01 (Exercise 6.1). Account 4050 Freight Revenue (214,616.66) comes from the invoice header, not from the lines, and account 2050 holds sales tax. Account 4070 Sales Discounts has no postings in any year: revenue is recorded net of every price reduction, so the income statement shows net revenue and nothing about the promotions. A gross-to-net schedule, or recording promotional discounts in 4070, would make the cost visible. Quarters of 2026 for the proposal's promotions: 7 Q1 7,596.99, Q2 22,524.82, Q3 356.75; 8 Q3 95,996.97, Q4 200,056.61; 9 Q4 28,057.57. That puts 228,114.18 of the 354,589.72 (about 64%) in the fourth quarter, because the fall promotion's orders are invoiced after it ends.

## What a strong answer says

- **Cost.** The yearly discounts and their share of revenue, with the growth stated.
- **Gross to net.** A schedule that foots, reductions kept apart from promotions, and the rounding residual named.
- **Ledger.** A tie by account, the difference placed in the three cutoff invoices, freight and tax kept out.
- **Where it shows.** Revenue is booked net and the discount account is unused, so the income statement cannot show the cost. The best answers add that recording discounts separately would change presentation, not net income.
- **Timing.** The lag from order to invoice puts most of the proposal's cost in the fourth quarter.

A weak answer reports the cost without the share, forces the tie by plugging a number, or says the ledger records the discounts in the returns account.

## Common mistakes and how to respond

- **The blank promotion row left in.** *Symptom:* a line total equal to every billed line. *Response:* ask which lines are the promotion's cost.
- **Reductions against LineTotal.** *Symptom:* a schedule that does not foot by the discount. *Response:* ask which price the reductions are measured to.
- **Freight in the tie.** *Symptom:* a difference far above the cutoff invoices. *Response:* ask where account 4050 gets its amount.
- **A forced tie.** *Symptom:* a plug row labeled "other". *Response:* ask the student to find the invoices behind the difference.
- **The wrong account.** *Symptom:* returns named as the discount account. *Response:* have them read the account names in `Accounts`.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| PivotTable and yearly cost | 25 | Discount and lines by promotion and year, chart, share of revenue | Totals without shares |
| Gross-to-net schedule | 25 | Footing schedule by group with rounding named | Reductions and promotions mixed |
| Tie to the ledger | 25 | By account, the difference traced to the invoices | A difference left unexplained |
| Where the cost appears | 15 | The discount account, net recording and what the statement hides | Statement without evidence |
| Quarters of the proposal | 10 | By invoice date, with the lag explained | By order date |

## Extensions and discussion questions

- Chart the proposal's discounts by quarter against the quarter's billed revenue, and say how much of the quarter's margin they take.
- Discuss: should discounts be recorded in a contra revenue account? What would change on the income statement, and what would not?
- Discuss: the cutoff invoices appear again here. How would Part III test cutoff for every year-end at once?
