---
note: ch06.ex6
uses: [ch06.g6]
title: A Descriptive Profile of the Revenue Population
kind: exercise
number: '6.6'
unit: '6'
perspective: auditing
tool: excel
minutes: 90
solution: "Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheets Ex 6.6 and Ex 6.6 Customers"
figures: []
---
{% set g = ch06_g6 %}
# Exercise 6.6: A Descriptive Profile of the Revenue Population

{{ header() }}

## Purpose and learning outcomes

Before an audit team designs detailed tests of revenue, it profiles the population: what a normal line looks like, where the revenue is concentrated and how the lines were priced. This exercise applies the whole chapter to that task: statistics by group, a PivotTable of customers, pricing methods and promotions, and a written profile that points to matters for the audit. The analytics type is descriptive.

By the end, students can:

- profile a population by group with counts, totals, averages and medians, and say why the average exceeds the median (outcome 1);
- measure concentration by customer and by pricing method with PivotTables (outcomes 2 and 3);
- write a profile that distinguishes a description from a finding and names matters for the audit (outcome 5).

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis of financial data) and Core S2 M9 (audit procedures and audit data analytics); IMA Statistical Analysis and Data Analysis; IFAC IES 2 (f) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of the analysis workbook made after Tutorial 6.3. The model answer uses FILTER, SORT, UNIQUE and TEXTJOIN (Microsoft 365).
- **Data conditions.** The year has {{ g.n_lines|count }} lines and {{ g.n_customers }} customers invoiced. Two customers invoiced in the year share the name {{ g.merged }} (customers {{ g.same[0].ids }}), so a PivotTable by name merges them. {{ g.n_promo|count }} lines carry a promotion and {{ g.n_blank|count }} do not, so the blank PromotionID row is the large one and is meaningful. Two promotions of the year before ({{ g.late_names }}) have lines invoiced in the report year.
- **Matters the profile may name.** The late-invoiced promotion lines, a promotion whose end date is before its start date, and the approved overrides. Chapter 8 returns to them, so the profile should notice and not resolve them.

## How to run it

Individual, about 90 minutes: 15 on requirement 1, 20 on requirement 2, 15 on requirement 3, 20 on requirement 4 and 20 on the profile. The task prints the two-condition FILTER. Before students use it, ask them to explain why the two conditions are multiplied and what a median that is the same in every row would mean. Collect the workbook and the profile.

## Step-by-step solution

### Requirement (1): Statistics by item group

**Step 1. Build the table.** On `Ex 6.6`, list the five item groups from row 5. For each group enter the count, the total, the average and the median. In the total row sum the counts and the revenues, divide the total revenue by the total number of lines for the overall average, and take the overall median from all of the year's lines. Do not sum the group averages or medians, and do not average the five averages without weights.

```jinja
=COUNTIFS(InvoiceLines[ItemGroup],$A5,InvoiceLines[FiscalYear],{{ d.C }})
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$A5,InvoiceLines[FiscalYear],{{ d.C }})
=AVERAGEIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$A5,InvoiceLines[FiscalYear],{{ d.C }})
=MEDIAN(FILTER(InvoiceLines[LineTotal],(InvoiceLines[FiscalYear]={{ d.C }})*(InvoiceLines[ItemGroup]=A5)))
```

**Check:** {% for r in groups %}{{ r[0] }} {{ r[1]|count }} lines, ${{ r[2]|money }}, average ${{ r[3]|money }}, median ${{ r[4]|money }}{% if not loop.last %}; {% endif %}{% endfor %}. **Watch for:** the same median in every row, from a FILTER with no group condition, or an error from conditions joined with a comma or `&`. Two conditions in FILTER are multiplied.

### Requirement (2): Customer concentration

**Step 2. Build the customer PivotTable.** On `Ex 6.6 Customers`, insert a PivotTable with FiscalYear in **Filters** (select {{ d.C }}), CustomerID in **Rows** and LineTotal in **Values**, and sort CustomerID by revenue from largest to smallest.

**Step 3. Add names and shares.** Beside the PivotTable look up each customer's name and segment from the Customer Table with XLOOKUP on CustomerID, divide each revenue by the grand total and accumulate the shares.

**Check:** the five largest hold {{ top5|pct(1) }} and the ten largest {{ top10|pct(1) }} of revenue, all in the {{ segment }} segment. The five are {{ largest|join('; ') }}. **Watch for:** the ranking by name. Grouped by name, {{ g.merged }} (customers {{ g.same[0].ids }}, ${{ g.merged_total|money }} together) ranks number {{ g.rank_name }} and the ten largest hold {{ g.top10_name|pct(1) }}, not {{ g.top10_key|pct(1) }}. Customers are identified by key.

### Requirement (3): Pricing methods

**Step 4. Build the pricing PivotTable.** Insert a PivotTable with FiscalYear in **Filters**, PricingMethod in **Rows**, ItemGroup in **Columns**, and SalesInvoiceLineID (as a count), LineTotal and LineTotal as **% of Grand Total** in **Values**. After placing FiscalYear in **Filters**, select {{ d.C }} explicitly, because a new PivotTable does not inherit another PivotTable's selection.

**Check:** the count totals {{ g.n_lines|count }} and the revenue ${{ g.revenue|money }}. {% for p in pricing %}{{ p[0] }} {{ p[1]|pct(1) }} of revenue ({{ p[2]|count }} lines){% if not loop.last %}; {% endif %}{% endfor %}. **Watch for:** the count field summed. SalesInvoiceLineID is a number, so Excel sums it until it is changed to **Count**. The base list prices only the hourly design services.

### Requirement (4): Promotions

**Step 5. Build the promotion PivotTable.** Insert a PivotTable with FiscalYear in **Filters**, PromotionID in **Rows**, and the count of lines and the sum of DiscountAmount in **Values**. Select {{ d.C }} in the filter explicitly.

**Check:** the counts add up to {{ g.n_lines|count }} lines, {{ g.n_promo|count }} with a promotion and {{ g.n_blank|count }} in the (blank) row.

**Step 6. Share and dates.** Next to it calculate each group's promotion lines over its lines, as one formula (here for the group named in A57, with a line break only for reading), and format it as a percentage. Look up each promotion's name and dates from PromotionProgram to see which ran in the year before.

```jinja
=COUNTIFS(InvoiceLines[ItemGroup],$A57,InvoiceLines[FiscalYear],{{ d.C }},
          InvoiceLines[PromotionID],"<>")
 /COUNTIFS(InvoiceLines[ItemGroup],$A57,InvoiceLines[FiscalYear],{{ d.C }})
```

The controls are {% for x in g.group_counts %}{{ x.group }} {{ x.promo|count }} of {{ x.lines|count }}{{ ', ' if not loop.last }}{% endfor %} lines.

**Check:** promotions {% for p in promos %}{{ p[0] }} ({{ p[1]|count }} lines, ${{ p[2]|money }}){% if not loop.last %}; {% endif %}{% endfor %}. Promotion lines as a share of each group's lines: {% for s in shares %}{{ s[0] }} {{ s[1]|pct(1) }}{% if not loop.last %}, {% endif %}{% endfor %}. The promotions of the year before are {% for l in late %}{{ l.id }} ({{ l.scope }}, {{ l.when }}){% if not loop.last %} and {% endif %}{% endfor %}, invoiced from {{ first }} to {{ last }}. **Watch for:** a promotion with no lines in the year left out of the lookup, and the blank row ({{ g.n_blank|count }} lines) read as missing data. It means no promotion.

### Requirement (5): The profile

**Step 7. Write three to five paragraphs.** Population (lines, revenue, a normal line by group, the average above the median in every group), concentration (Furniture's share of revenue, the shares of the largest customers), pricing (the methods and the promotions), and matters for the audit.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Lines; revenue; customers invoiced | {{ g.n_lines|count }}; ${{ g.revenue|money }}; {{ customers }} | 1, 2 |
| Top five and top ten customers, share of revenue | {{ top5|pct(1) }}; {{ top10|pct(1) }} | 3 |
| Share of revenue by pricing method | {% for p in pricing %}{{ p[1]|pct(1) }}{% if not loop.last %}; {% endif %}{% endfor %} | 4 |
| Promotion lines; discounts | {{ g.n_promo|count }}; ${{ g.promo_discount|money }} | 5 |
| Largest promotion: lines; discount | {{ g.main_id }}: {{ g.main_lines|count }}; ${{ g.main_discount|money }} | 5 |
| Promotion with end date before start date | {{ reversed }}: {{ g.backwards_start }} to {{ g.backwards_end }} | 6 |

{{ expected() }}

## What a strong answer says

- **Population.** A normal line is a few thousand dollars and depends on the group. Design services are fewer and larger. In every group the average exceeds the median, consistent with a right tail of large lines. The largest lines can be tested on their own, with procedures for the rest designed for the audit objective, so the profile alone does not set a sample.
- **Concentration.** Revenue is concentrated in Furniture, not in customers, and the ten largest customers are modest in share. The profile does not infer risk from the share alone.
- **Pricing.** Segment price lists carry most of the revenue, and approved overrides, the one manual path, are small.
- **Matters for the audit.** Discounts are billed after promotions ended, one promotion's dates are inconsistent, and overrides are natural targets. The profile names them as questions, not conclusions.

**A plus, not required.** Each paragraph tied to a number from the summaries.

A weak profile repeats the PivotTable values without reading them, or states findings the data cannot show.

## Common mistakes and how to respond

- **One median for every group.** *Symptom:* the same value in all rows. *Response:* ask which rows the FILTER returned.
- **Ranking by name.** *Symptom:* {{ g.merged }} among the ten largest as one customer. *Response:* ask what identifies a customer.
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
| Requirement 5: the profile | 25 | Population, concentration, pricing and audit matters | Descriptive only |

## Extensions and discussion questions

- Add the bins of Tutorial 6.1 for each group and compare the shapes.
- Rank the largest lines and say what share of revenue the top tenth of lines holds, and compare it with the customer concentration.
- Discuss: why does modest concentration by customer say nothing about credit or audit risk by itself?
- Discuss: Chapter 8 tests the promotion dates and the overrides. Which would you test first, and why?
