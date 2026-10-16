# Exercise 5.4: How Long Orders Take to Be Invoiced

| | |
|---|---|
| Unit | Chapter 5: Data Preparation and Cleaning in Excel |
| Item | Exercise 5.4 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheet Ex 5.4 (the lag column is on the SalesInvoice worksheet) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

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
- **Exercise 5.2.** Requirement (1) says to reuse the OrderDate column from Exercise 5.2 if it exists. Students who did not do it add the same lookup. The new column is OrderToInvoiceDays in column X.
- **Data conditions.** Every invoice has an order. Three invoices are dated a day before their order, so the lag has a minimum of minus one. 9 promotions: promotions 1, 4, and 7 have every line invoiced after the end date, because their recorded dates do not span their sales. The others have between about a quarter and a half of their lines invoiced after the end date.

## How to run it

Individual or pairs, about 75 minutes: 10 on the lag column (requirement 1), 20 on the summary (2), 15 on the promotions (3), 15 on the memo (4) and 15 on checking and formatting. Hold back the hint about checking the dates until a student writes that three promotions were billed late. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The lag

**Step 1. Measure the days from order to invoice.** If the SalesInvoice Table has no OrderDate yet, add it with `=XLOOKUP([@SalesOrderID],SalesOrder[SalesOrderID],SalesOrder[OrderDate],"No match")` and format it as a date. In the next column type `OrderToInvoiceDays` and enter the formula below. Format the column as a number with no decimals.

```
=[@InvoiceDate]-[@OrderDate]
```

**Check:** the lag is a whole number of days, and the smallest is minus one. **Watch for:** a column that Excel formats as a date. A lag of 30 days reads as the date `1900-01-30`. Tutorial 5.1, Step 4b, has the same fix.

### Requirement (2): The summary

**Step 2. Summarize all invoices.** On `Ex 5.4` enter the four formulas below, one under another, for the count, the average, the median and the 90th percentile, and count the negative lags with `=COUNTIF(SalesInvoice[OrderToInvoiceDays],"<0")`.

```
=COUNT(SalesInvoice[OrderToInvoiceDays])
=AVERAGE(SalesInvoice[OrderToInvoiceDays])
=MEDIAN(SalesInvoice[OrderToInvoiceDays])
=PERCENTILE.INC(SalesInvoice[OrderToInvoiceDays],0.9)
```

**Step 3. Summarize by quarter.** Type the four period labels as text in A12 to A15 and enter, in B12 and C12, the two formulas below. Fill down. The model answer adds a median with `=MEDIAN(FILTER(SalesInvoice[OrderToInvoiceDays],SalesInvoice[Period]=$A12))`, which needs Microsoft 365.

```
=COUNTIFS(SalesInvoice[Period],$A12)
=AVERAGEIFS(SalesInvoice[OrderToInvoiceDays],SalesInvoice[Period],$A12)
```

**Check:** the Expected results. **Watch for:** a quarter taken from the order date. The model answer uses the invoice's period, as the memo recommends for recorded revenue, and a student who uses the order date should say so.

**Step 4. Interpret.** The average, 21.3 days, is above the median, 12. A minority of orders take much longer, so a long right tail pulls the average up and leaves the median alone; the 90th percentile is 52 days. Across the four quarters of the year the averages, which count each invoice once, run from 20.5 to 23.1 days, a spread of 2.6, so the lag is fairly stable.

### Requirement (3): The promotions

**Step 5. Read the dates first, then count.** On `Ex 5.4` spill the promotions with `=PromotionProgram[PromotionID]` and the same for code, start and end. Beside them enter the count and the late count, and the share:

```
=COUNTIFS(SalesInvoiceLine[PromotionID],A20#)
=COUNTIFS(SalesInvoiceLine[PromotionID],A20#,SalesInvoiceLine[InvoiceDate],">"&D20#)
=F20#/E20#
```

A student without dynamic arrays fills the same three formulas down with a row reference instead of the spill.

**Check:** the nine rows of the Expected results. Promotions 1, 4, and 7 read 100 percent. **Watch for:** reading a hundred percent as billing lag. Promotion 1 is effective for a single day, and promotions 4 and 7 end before they start, so every line of the three falls after its recorded end date, because those dates do not span the sales. The memo should name them as master-data questions.

### Requirement (4): The recommendation

**Step 6. Write three to five sentences.** Assign promotional revenue by invoice date. The ledger records revenue on the invoice, so for recorded revenue the invoice date ties the analysis to it. Use the order date to explain the price, because a promotional price is set when the order is placed. Promotion 8, the Furniture Seasonal Promotion, had 160 of its 576 lines invoiced after its end date, which is not an error. The averages are similar from quarter to quarter, but that does not make the share of a promotion's orders invoiced in the next quarter predictable, because it also depends on when in the promotion the orders were placed. Promotions 1, 4, and 7 are the exception, and the dates are for the data owner.

**Check:** the memo recommends one date for revenue and one for price, and states the limit: the invoice date is not proof of delivery.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Invoices; average lag; median; 90th percentile | 20,914; 21.3; 12; 52 | Step 2 |
| Invoices with a negative lag | three | Step 2 |
| Quarter 1: invoices; average; median | 1,845; 23.1; 13 | Step 3 |
| Quarter 2: invoices; average; median | 1,782; 20.5; 11 | Step 3 |
| Quarter 3: invoices; average; median | 1,756; 21.4; 13 | Step 3 |
| Quarter 4: invoices; average; median | 1,788; 21.6; 12 | Step 3 |

| Promotion | Effective dates | Lines | Invoiced after end date | Share | Date check |
|---|---|---:|---:|---:|---|
| PROMO-2024-001 | 2024-03-01 to 2024-03-01 | 80 | 80 | 100% | lasts one day |
| PROMO-2024-002 | 2024-09-01 to 2024-10-31 | 431 | 147 | 34% | span the sales |
| PROMO-2024-003 | 2024-11-01 to 2024-11-30 | 149 | 74 | 50% | span the sales |
| PROMO-2025-004 | 2025-03-01 to 2025-02-27 | 74 | 74 | 100% | ends before it starts |
| PROMO-2025-005 | 2025-09-01 to 2025-10-31 | 228 | 74 | 32% | span the sales |
| PROMO-2025-006 | 2025-11-01 to 2025-11-30 | 414 | 201 | 49% | span the sales |
| PROMO-2026-007 | 2026-03-01 to 2026-02-28 | 68 | 68 | 100% | ends before it starts |
| PROMO-2026-008 | 2026-09-01 to 2026-10-31 | 576 | 160 | 28% | span the sales |
| PROMO-2026-009 | 2026-11-01 to 2026-11-30 | 88 | 27 | 31% | span the sales |

![A mock of the promotion table of Exercise 5.4, with the dates that need a question before the counts can be read.](../figures/chapter-05-data-preparation/IF-05-4-A.pdf)

> **Instructor notes, Exercise 5.4:** order-to-invoice lag across all 20,914 invoices: median 12 days, mean 21.3 (90th percentile 52 days); the mean exceeds the median because a minority of orders take much longer to invoice (right skew). Fiscal 2026 by quarter, invoices and average lag: Q1 1,845, 23.1 days; Q2 1,782, 20.5; Q3 1,756, 21.4; Q4 1,788, 21.6 (medians 13, 11, 13, 12): fairly stable. Promotion lines invoiced after the end date: PROMO-2024-001 80 of 80, PROMO-2024-002 147 of 431, PROMO-2024-003 74 of 149, PROMO-2025-004 74 of 74, PROMO-2025-005 74 of 228, PROMO-2025-006 201 of 414, PROMO-2026-007 68 of 68, PROMO-2026-008 160 of 576, PROMO-2026-009 27 of 88. Promotions 001, 004, and 007 have every line after the end date because their recorded dates do not span their sales (a one-day promotion, and two whose end dates precede their start dates); these are left for the audit analytics chapter. For this analysis of recorded revenue, the invoice date assigns the quarter; the order date explains the price. Three invoices have a negative lag (Exercise 5.2).

## What a strong answer says

- **Requirement (2).** A skewed distribution, with the average above the median and the long tail named. Stability is a claim about the quarterly averages, with the range.
- **Requirement (3).** Before the counts, the dates. Three promotions fail a simple test of their own dates, so their late lines say nothing about billing. The other six have between a quarter and a half of their lines invoiced after the end date, which is consistent with the usual lag for orders placed in the last weeks of a promotion.
- **Requirement (4).** A split recommendation, with the reason for each date and the limit of the invoice date.

A weak answer calls the three promotions "billed late", or recommends the order date for revenue because the price follows it.

## Common mistakes and how to respond

- **A lag shown as a date.** *Symptom:* dates in the first weeks of the year `1900`. *Response:* change the number format.
- **A "No match" in the subtraction.** *Symptom:* #VALUE!. *Response:* count the lookup's failures first.
- **Average and median swapped, or only one reported.** *Response:* ask which one the typical invoice looks like.
- **Late lines read as billing delays for every promotion.** *Response:* ask what the end date of promotions 1, 4, and 7 says.
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
- Count, for promotion 8, the lines invoiced after the end date by month, and compare with the lag.
- Discuss: Chapter 6 bridges the Furniture margin. How would you treat a promotion line invoiced after its end date in that bridge?
- Discuss: Chapter 8 returns to the three promotions' dates. What would you ask the sales manager?
