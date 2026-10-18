---
note: ch05.ex4
uses: [ch05.g4]
title: How Long Orders Take to Be Invoiced
kind: exercise
number: '5.4'
unit: '5'
perspective: managerial
tool: excel
minutes: 75
solution: "Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheet Ex 5.4 (the lag column is on the SalesInvoice worksheet)"
figures:
  - id: IF-05-4-A
    kind: excel-mock
    purpose: The promotion table of Exercise 5.4, with the dates that need a question before the counts can be read.
    shows: "A table with one row for each promotion and the columns PromotionID, PromotionCode, EffectiveStartDate, EffectiveEndDate, Invoice lines, Invoiced after end date and Share after end date. Three rows are outlined: the promotion whose start and end dates are the same day, and the two whose end date comes before their start date. In those three rows the share reads 100 percent; in the other six it is between about a quarter and a half. Above the table, a block shows the lag for all invoices: the count, the average, the median and the 90th percentile, with the average above the median."
    data: SalesInvoice with its lag column, PromotionProgram and SalesInvoiceLine (the Expected results table).
---
{% set g = ch05_g4 %}
# Exercise 5.4: How Long Orders Take to Be Invoiced

{{ header() }}

## Purpose and learning outcomes

Tutorial 5.2 showed that a promotion's lines can be invoiced after the promotion ends. This exercise measures how long invoicing normally takes, checks that the lag is stable, and then asks the question the chapter keeps returning to: before reading a count as evidence about billing, check the master data it depends on. It ends in a recommendation for the controller's margin analysis. It practices a date subtraction, COUNTIFS and AVERAGEIFS, MEDIAN, and an honest reading of skewed data. The analytics type is descriptive.

By the end, students can:

- measure the time between two events by subtracting dates, and format the result correctly (outcome 3);
- summarize the lag by period with COUNTIFS and AVERAGEIFS, and explain a mean above a median (outcomes 3 and 4);
- test the dates of a master record before interpreting a count built on them (outcomes 1 and 6);
- recommend which date assigns revenue to a period and which explains a price (outcome 1).

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis) and Core S1 M4 (financial statement analysis and performance measures); IMA Data Analysis, and Performance Management; IFAC IES 2 (b) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook after Tutorial 5.3, with the SalesOrder Table (Tutorial 5.2) and the Period column on SalesInvoice (Tutorial 5.1). The quarter in the model answer is the quarter of the InvoiceDate, which is what the Period column holds.
- **Exercise 5.2.** Requirement (1) says to reuse the OrderDate column from Exercise 5.2 if it exists. Students who did not do it add the same lookup. The new column, OrderToInvoiceDays, goes in the first empty column of the Table, after every existing column, BeforeOrder included: column {{ g.letters.OrderToInvoiceDays }} in the model answer, which holds Exercise 5.2's columns too, and column {{ g.direct_letters.OrderToInvoiceDays }} for a student who comes straight from the tutorials (OrderDate then in {{ g.direct_letters.OrderDate }}).
- **Data conditions.** Every invoice has an order. Three invoices are dated a day before their order, so the lag has a minimum of minus one. {{ g.n_promos|count }} promotions: promotions {{ g.flagged_ids }} have every line invoiced after the end date, because their recorded dates do not span their sales. The others have between about a quarter and a half of their lines invoiced after the end date.

## How to run it

Individual or pairs, about 75 minutes: 10 on the lag column (requirement 1), 20 on the summary (2), 15 on the promotions (3), 15 on the memo (4) and 15 on checking and formatting. Hold back the hint about checking the dates until a student writes that three promotions were billed late. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The lag

**Step 1. Measure the days from order to invoice.** If the SalesInvoice Table has no OrderDate yet, add it in the first empty cell right of the last header with `=XLOOKUP([@SalesOrderID],SalesOrder[SalesOrderID],SalesOrder[OrderDate],"No match")` and format it as a date. Then, again in the first empty cell right of the last header, type `OrderToInvoiceDays` and enter the formula below. Format the column as a number with no decimals.

```
=[@InvoiceDate]-[@OrderDate]
```

**Check:** the lag is a whole number of days, and the smallest is minus one. **Watch for:** a lag typed over an existing column. After Exercise 5.2 the cell to the right of OrderDate holds BeforeOrder, so "the next column" would overwrite it. **Watch for:** a column that Excel formats as a date. A lag of 30 days reads as the date `1900-01-30`. Tutorial 5.1, Step 4b, has the same fix.

### Requirement (2): The summary

**Step 2. Summarize all invoices.** On `Ex 5.4` enter the four formulas below, one under another, for the count, the average, the median and the 90th percentile, and count the negative lags with `=COUNTIF(SalesInvoice[OrderToInvoiceDays],"<0")`.

```
=COUNT(SalesInvoice[OrderToInvoiceDays])
=AVERAGE(SalesInvoice[OrderToInvoiceDays])
=MEDIAN(SalesInvoice[OrderToInvoiceDays])
=PERCENTILE.INC(SalesInvoice[OrderToInvoiceDays],0.9)
```

**Step 3. Summarize by quarter.** Type the four period labels as text in A12 to A15 and enter, in B12 and C12, the two formulas below. Fill down. The model answer adds a median with `=MEDIAN(FILTER(SalesInvoice[OrderToInvoiceDays],SalesInvoice[Period]=$A12))`. FILTER is in every Excel version that has XLOOKUP, though the complete model answer also uses HSTACK, TAKE and CHOOSECOLS, which need a newer version, as the chapter note says.

```
=COUNTIFS(SalesInvoice[Period],$A12)
=AVERAGEIFS(SalesInvoice[OrderToInvoiceDays],SalesInvoice[Period],$A12)
```

**Check:** the Expected results. **Watch for:** a quarter taken from the order date. The model answer uses the invoice's period, as the memo recommends for recorded revenue, and a student who uses the order date should say so.

**Step 4. Interpret.** Across all {{ g.n_invoices|count }} invoices in the extract, the average, {{ mean|num(1) }} days, is above the median, {{ median }}. A minority of invoices come much later than their orders, so a long right tail pulls the average up, while the median is less sensitive to it; the 90th percentile is {{ p90 }} days. The measures are per invoice: the {{ g.n_invoices|count }} invoices come from {{ g.n_orders|count }} orders, so an order with several invoices counts once for each. Across the four quarters of the year, by the quarter of the InvoiceDate, the averages run from {{ g.lowest|num(1) }} to {{ g.highest|num(1) }} days, a spread of {{ g.spread|num(1) }}, so the lag is fairly stable.

### Requirement (3): The promotions

**Step 5. Read the dates first, then count.** On `Ex 5.4` type the headings PromotionID, PromotionCode, EffectiveStartDate, EffectiveEndDate, Invoice lines, Invoiced after end date and Share after end date in A19 to G19. In A20 spill the promotions with `=PromotionProgram[PromotionID]`, and in B20, C20 and D20 the same for code, start and end. In E20, F20 and G20 enter the count, the late count and the share, and keep the cells below row 20 empty, or the spills return #SPILL!:

```
=COUNTIFS(SalesInvoiceLine[PromotionID],A20#)
=COUNTIFS(SalesInvoiceLine[PromotionID],A20#,SalesInvoiceLine[InvoiceDate],">"&D20#)
=F20#/E20#
```

A student without dynamic arrays types or copies the promotions into rows 20 to {{ g.last_promo_row }} and fills the same three formulas down, with `A20` and `D20` in place of `A20#` and `D20#`.

**Check:** the nine rows of the Expected results. Promotions {{ g.flagged_ids }} read 100 percent. **Watch for:** reading a hundred percent as billing lag. Promotion {{ g.one_day.id }} is recorded for a single day, {{ g.one_day.start_long }}, while its lines come from orders dated {{ g.one_day.order_span }}, and promotions {{ g.backwards_ids }} end before they start. In all three the recorded dates do not span the orders, so every line falls after the end date and the share says nothing about billing. Under the chapter's convention that the order date sets the price, the discounts on those orders need an explanation. The memo names them as questions for the data owner, about each promotion's eligibility rule and approved dates. A single day or a line invoiced after the end date does not by itself show an unauthorized discount.

### Requirement (4): The recommendation

**Step 6. Write three to five sentences.** Assign promotional revenue by invoice date. The ledger records revenue on the invoice, so for recorded revenue the invoice date ties the analysis to it. Use the order date to explain the price, because a promotional price is set when the order is placed. Promotion {{ g.top.id }}, the {{ g.top.name }}, had {{ g.top.after|count }} of its {{ g.top.lines|count }} lines invoiced after its end date, which is not an error. The averages are similar from quarter to quarter, but that does not make the share of a promotion's orders invoiced in the next quarter predictable, because it also depends on when in the promotion the orders were placed. Promotions {{ g.flagged_ids }} are the exception, and the dates are for the data owner.

**Check:** the memo recommends one date for revenue and one for price, and states the limit: the invoice date is not proof of delivery.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Invoices; average lag; median; 90th percentile | {{ invoices|count }}; {{ mean|num(1) }}; {{ median }}; {{ p90 }} | Step 2 |
| Invoices with a negative lag | {{ negative|lower }} | Step 2 |
{% for q in quarters %}
| Quarter {{ q.q }}: invoices; average; median | {{ q.invoices|count }}; {{ q.mean|num(1) }}; {{ q.median }} | Step 3 |
{% endfor %}

| Promotion | Effective dates | Lines | Invoiced after end date | Share | Date check |
|---|---|---:|---:|---:|---|
{% for p in g.promos %}
| {{ p.code }} | {{ p.start }} to {{ p.end }} | {{ p.lines|count }} | {{ p.after|count }} | {{ p.share|pct(0) }} | {{ p.kind or 'span the sales' }} |
{% endfor %}

{{ figure('IF-05-4-A') }}

{{ expected() }}

## What a strong answer says

- **Requirement (2).** A skewed distribution of invoices, with the average above the median and the long tail named. Stability is a claim about the quarterly averages, with the range.
- **Requirement (3).** Before the counts, the dates. Three promotions have recorded dates that do not span their orders, one a single day and two that end before they start, so their late lines say nothing about billing and their dates are a question for the data owner. The other six have between a quarter and a half of their lines invoiced after the end date, which is consistent with the usual lag for orders placed in the last weeks of a promotion.
- **Requirement (4).** A split recommendation, with the reason for each date and the limit of the invoice date.

A weak answer calls the three promotions "billed late", or recommends the order date for revenue because the price follows it.

## Common mistakes and how to respond

- **A lag shown as a date.** *Symptom:* dates in the first weeks of the year `1900`. *Response:* change the number format.
- **A "No match" in the subtraction.** *Symptom:* #VALUE!. *Response:* count the lookup's failures first.
- **Average and median swapped, or only one reported.** *Response:* ask which one the typical invoice looks like.
- **Late lines read as billing delays for every promotion.** *Response:* ask what the end date of promotions {{ g.flagged_ids }} says.
- **The order date for revenue.** *Response:* ask which date the ledger follows.
- **A negative lag dropped.** *Response:* count it and refer to Exercise 5.2.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the lag | 15 | A numeric lag column | Formatted as a date |
| Requirement 2: the summary | 30 | COUNTIFS, AVERAGEIFS, MEDIAN, the skew explained, stability stated | Numbers without the explanation |
| Requirement 3: promotions | 30 | Counts for each promotion, dates checked, three flagged as master-data questions | Counts without the date check |
| Requirement 4: recommendation | 25 | Invoice date for revenue, order date for price, with reasons | One date, or no reason |

## Extensions and discussion questions

- Chart the distribution of the lag in bins of ten days and say where the median and the average fall.
- Count, for promotion {{ g.top.id }}, the lines invoiced after the end date by month, and compare with the lag.
- Discuss: Chapter 6 bridges the Furniture margin. How would you treat a promotion line invoiced after its end date in that bridge?
- Discuss: Chapter 8 returns to the three promotions' dates. What would you ask the sales manager?
