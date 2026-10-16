---
note: case2.r2
uses: [case2.g2]
title: Measure what the promotions cost and where the cost appears (Chapter 6)
kind: requirement
number: '2'
unit: case2
perspective: financial
tool: excel
minutes: 75
solution: "PartII-case.zip: Charles River Promotion Case.xlsx, sheets R2 Cost (PivotTable PromotionCost) and R2 Gross to Net, with the queries BilledLines, RevenuePostings, LedgerActivity, Accounts and Items"
figures:
  - id: IF-C2-2-A
    kind: excel-mock
    purpose: The PivotTable of promotional discount and billed lines by promotion and invoice year, with a chart of the yearly totals beneath it.
    shows: "A PivotTable with PromotionID down the rows and the three invoice years across, each holding Sum of DiscountAmount and Count of lines, with grand totals and no blank row. The second column of discount of the promotions invoiced in the year after they ran is outlined. A column chart of the yearly totals, with each year's share of billed revenue, sits beneath it."
    data: The Expected results of this requirement (discount and lines by promotion and year, from BilledLines).
  - id: IF-C2-2-B
    kind: chart
    purpose: The report year's gross-to-net walk, from list amount to net billed.
    shows: "A waterfall chart with five labeled bars: List amount, Price lists and overrides and Promotional discounts as decreases, Line rounding as a sliver, and Net billed."
    data: The report year's gross-to-net totals (the Expected results, Step 3).
---
{% set x = case2_g2 %}
# Requirement 2: Measure what the promotions cost and where the cost appears (Chapter 6)

{{ header() }}

## Purpose and learning outcomes

Requirement 2 answers the controller's first question, the financial reporting one: what did three years of promotions cost, and where does the cost show in the statements? It puts Chapter 6 to work on a cost that no ledger account records, so students must build the number from the invoice lines and then explain why the ledger cannot show it. The analytics type is descriptive.

By the end, students can:

- summarize a cost by promotion and year with a PivotTable and express it as a share of revenue;
- build a gross-to-net schedule that separates price-list and override reductions from promotional discounts;
- tie billed revenue to the ledger by account and explain the difference by the invoices that caused it;
- say what the income statement shows and does not show about a price reduction.

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and M8 T3 to T4 (data mining and analysis); IMA Reporting and Control (financial recordkeeping) and strategic cost management; IFAC IES 2 (a), financial accounting and reporting; AACSB A5 part 5.1.

## Before you assign

- **From Requirement 1.** The `BilledLines`, `RevenuePostings`, `Accounts` and `Items` queries with their checks agreeing. From Chapter 6 the PivotTable and the tie from ledger to statements. Exercise 6.1 introduced the three invoices dated in the prior year and posted on January 1.
- **Data conditions.** Only promotion lines carry a discount, so the discount total is the cost of the promotions ({{ x.promo_billed|count }} billed lines of {{ x.billed_lines|count }}). The design services carry no reductions and no discounts. Each item group posts its revenue to one account through Item.RevenueAccountID. Account {{ x.discount_account }}, {{ x.discount_name }}, exists and has no postings.
- **A limit of the case's queries.** `RevenuePostings` holds only the report year's sales-invoice postings, so it can show that no invoice posted to {{ x.discount_account }} that year. The claim that the account was never used, in any year, needs the ledger across years; the model answer adds a `LedgerActivity` query for it. Accept the narrower statement from a student who states its scope.

## How to run it

Individual work, about 75 minutes: 20 on the PivotTable and chart, 20 on gross to net, 20 on the tie and the discount account, 15 on the quarters. Hold back the cutoff hint until a student has a difference and cannot place it. **Collect** the three tables (cost by year, gross to net, the tie) for the appendix.

{{ figure('IF-C2-2-A') }}

## Step-by-step solution

### Phase 1: The cost by promotion and year

**Step 1. Build the PivotTable.**

a. Select a cell in `BilledLines` and choose **Insert > PivotTable**; place it on a new worksheet (the model answer names it `R2 Cost`).
b. Drag PromotionID to **Rows**, InvoiceYear to **Columns**, DiscountAmount to **Values** (Sum) and SalesInvoiceLineID to **Values** (Count), and rename the count `Count of lines`.
c. Open the PromotionID filter and clear (blank), the lines with no promotion.

**Check:** the grand total is ${{ x.pivot_total|money }} of discount on {{ lines|count }} lines. Promotions {{ x.spill }} show a second column of discount: their orders were invoiced in the year after they ran. The PivotTable sums unrounded amounts, so its total is a cent or so from the ${{ total|money }} that the yearly table of Step 2 gets by rounding each year.

**Watch for:** the (blank) row left in. It adds {{ x.blank_billed|count }} lines and no discount, and the line total reads {{ x.billed_lines|count }}.

**Step 2. Express each year as a share of billed revenue, and chart it.**

a. For each invoice year, with the year in column A (`FirstYear` and then one more each row), enter:

```
=ROUND(SUMIFS(BilledLines[DiscountAmount],BilledLines[InvoiceYear],A21),2)
=SUMIFS(BilledLines[LineTotal],BilledLines[InvoiceYear],A21)
```

b. Divide the first by the second for the share.
c. Select the years and the discounts and choose **Insert > Insert Column or Bar Chart > Clustered Column**.

**Check:**

{% for y in years %}
- {{ y.year }}: ${{ y.disc|money }}, {{ y.share|pct(2) }} of ${{ y.rev|money }} billed.
{% endfor %}

The cost {{ grew }} in {{ span }} years. Rounding each line before summing, as Exercise 4.2 did, gives ${{ rounded|money }} in all against ${{ total|money }}; both are correct, and the memo should state which it uses.

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
{% for g in groups %}
| {{ g.group }} | ${{ g.list|money }} | ${{ g.red|money }} | ${{ g.disc|money }} | ${{ g.net|money }} |
{% endfor %}
| Total | ${{ list|money }} | ${{ red|money }} | ${{ disc|money }} | ${{ net|money }} |

List less reductions less promotions is ${{ after|money }}, and the ${{ rounding|money }} to the net is the rounding of LineTotal line by line. The schedule measures the reductions, not their authorization. They include lines billed on Pending override requests, which carry a price-list label and no completed approval (Requirement 5), so a label such as "approved overrides" would claim more than the data show. **Watch for:** reductions computed as list less LineTotal. That counts the promotional discount twice, once in the reductions and once in its own column, so the schedule is off by exactly the discount.

{{ figure('IF-C2-2-B') }}

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
{% for t in x.tie %}
| {{ t.number }} {{ t.name }} | {{ t.group }} | ${{ t.credit|money }} | ${{ t.net|money }} | ${{ t.diff|money }} |
{% endfor %}

The ledger is ${{ ledger_total|money }} against ${{ net|money }}, a difference of ${{ difference|money }}. It is the invoices {{ first }} to {{ last }}, dated late in {{ x.prior_year }} and posted on {{ cutoff_posted }}, a cutoff matter from Exercise 6.1. The ledger selects by posting date and `BilledLines` by invoice date, so the posting date is the evidence that places them in the report year's ledger, and the invoice number's year is only the clue that finds them. **Watch for:** freight and sales tax. {{ freight_name }} ({{ x.freight_account }}) comes from the invoice header, not the lines, so a student who adds it to the revenue accounts reads a difference of ${{ x.with_freight|money }} instead; account {{ x.tax_account }} holds the sales tax.

**Step 5. Say where the cost appears.** In `Accounts` find {{ x.discount_account }} {{ discounts_name }}, a contra revenue account, and look for it in `RevenuePostings` and the ledger: there are no postings. Each invoice line is recorded at its net price, so the revenue accounts already exclude every price reduction and the income statement shows net revenue and nothing about the promotions. The cost becomes visible only in a gross-to-net schedule, or if revenue were recorded at the price before the promotion and the discount in {{ x.discount_account }}. **Watch for:** {{ x.returns_account }} {{ x.returns_name }}, which records returns, offered as the discount account.

**Step 6. Place the proposal's discounts in quarters.** Use SUMIFS on `BilledLines` by PromotionID, the report year and InvoiceQuarter. These are invoice quarters, and the ledger's quarter follows the posting date, which differs only for invoices like those of Step 4.

**Check:**

| Promotion | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
{% for r in x.quarter_rows %}
| {{ r.name }} | ${{ r.q[0]|money }} | ${{ r.q[1]|money }} | ${{ r.q[2]|money }} | ${{ r.q[3]|money }} |
{% endfor %}

The three promotions billed ${{ prop_total|money }}, of which ${{ q4|money }} ({{ q4_share|pct(0) }}) fell in the fourth quarter, because the {{ x.fall_label }} promotion's orders are invoiced after it ends ({{ x.fall_after|count }} of its lines were) and the segment promotion runs in November. **Watch for:** `OrderLines` as the source. By order date the fourth quarter holds only {{ x.q4_ordered|pct(0) }}, and the lag, the point of the step, disappears.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Discount in all; billed lines | ${{ total|money }}; {{ lines|count }} | 1 |
| Share of billed revenue, first and last year | {{ years[0].share|pct(2) }}; {{ years[-1].share|pct(2) }} | 2 |
| Ledger credits; difference to net billed | ${{ ledger_total|money }}; ${{ difference|money }} | 4 |
| The proposal's discount; fourth-quarter share | ${{ prop_total|money }}; {{ q4_share|pct(0) }} | 6 |

{{ expected() }}

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
- **Freight in the tie.** *Symptom:* a difference far above the cutoff invoices. *Response:* ask where account {{ x.freight_account }} gets its amount.
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
