# Exercise 4.2: Reviewing Promotional Discounts

| | |
|---|---|
| Unit | Chapter 4: Excel Essentials for Accounting Analytics |
| Item | Exercise 4.2 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 60 minutes |
| Solution file | Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheet Ex 4.2 |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise turns Tutorial 4.3's clue into a summary the sales director can read: which promotions ran, what they gave away, and whether each was applied at its approved rate. It practices lookups and COUNTIFS on Tables, an absolute reference to a total, data bars, and a consistency test. It also teaches the limit of that test: a matching rate shows only that each line carries its program's rate. The analytics type is descriptive.

By the end, students can:

- summarize a Table by a key held in another Table, with one row for each key (outcome 2);
- use an absolute reference for a share of a total (outcome 3);
- apply data bars to a column (outcome 5);
- design a consistency test, read a clean result, and say what it does not show (outcomes 1 and 6).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S1 M8 T3 to T4 (data mining and analysis); IMA Data Analysis, and Financial Recordkeeping; IFAC IES 2 (a) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and Tables.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 4.3, with the SalesInvoiceLine Table (its DiscountAmount calculated column) and the PromotionProgram Table of 9 rows.
- **The type trap.** If Discount was left as a whole number in Tutorial 4.1, Step 6, DiscountAmount is zero on every line and the rate test flags all 2,108 promotion lines. A student whose summary shows this has found the trap; send them to Replace current in the Changed Type step.
- **Data conditions.** Every promotion line carries its promotion's DiscountPct, no line has a discount without a PromotionID, and every PromotionID on the lines is in PromotionProgram, so the test finds no differences. Promotions 4 and 7 end before they start, and promotion 1 is effective for a single day. The exercise asks students to list these as questions, not to correct them.

## How to run it

Pairs or individual, about 60 minutes: 20 on the summary (requirement 1), 10 on shares and data bars (2), 10 on the rate test (3), 5 on the largest promotion (4) and 15 on the memo (5). Hold back the absolute-reference hint until a student sees the share column change down the rows. Collect the worksheet and the memo.

## Step-by-step solution

### Requirement (1): One row for each promotion

**Step 1. Lay out the summary.**

a. Insert a worksheet named `Ex 4.2`. In row 3 type `PromotionID`, `PromotionCode`, `PromotionName`, `Invoice lines`, `LineTotal`, `DiscountAmount`, `Share of discount dollars`, `DiscountPct` and `Lines at another rate`.
b. In A4 to A12 enter the PromotionIDs 1 to 9, one for each row of the PromotionProgram Table.

**Step 2. Fill the lookups and the totals.** In B4 enter the formula below, and repeat it in C4 for PromotionName and in H4 for DiscountPct:

```
=XLOOKUP($A4,PromotionProgram[PromotionID],PromotionProgram[PromotionCode])
```

In D4 enter `=COUNTIFS(SalesInvoiceLine[PromotionID],$A4)`, in E4 `=SUMIFS(SalesInvoiceLine[LineTotal],SalesInvoiceLine[PromotionID],$A4)` and in F4 the same SUMIFS on DiscountAmount. Fill each down. In row 13 enter `Total` and a SUM for D, E and F.

**Check:** 2,108 promotion lines with a LineTotal of $6,326,390.36 and a DiscountAmount of $723,253.29. **Watch for:** a student who filters the Table by hand instead of writing formulas. The summary then cannot refresh.

### Requirement (2): Shares and data bars

**Step 3. Add the share and the bars.**

a. In G4 enter `=F4/$F$13` and fill down. Format column G as a percentage.
b. Select F4 to F12 and choose **Home > Conditional Formatting > Data Bars**.

**Check:** the shares add up to 100 percent, and the longest bar is on promotion 8, with 40.9%. **Watch for:** `F13` without the dollar signs. It moves down the column, and the shares turn to errors or nonsense. This is the absolute reference of Tutorial 4.2.

### Requirement (3): The rate test

**Step 4. Count the lines at another rate.** In I4 enter the formula below, fill it down, and total column I:

```
=COUNTIFS(SalesInvoiceLine[PromotionID],$A4,SalesInvoiceLine[Discount],"<>"&H4)
```

Add two integrity rows below the summary: `=COUNTIFS(SalesInvoiceLine[PromotionID],"",SalesInvoiceLine[Discount],"<>0")` for discounts with no promotion, and `=COUNTIFS(SalesInvoiceLine[PromotionID],"<>")-D13` for promotion lines the summary leaves out.

**Check:** every cell of column I and both integrity rows show 0, so no promotion was applied at a rate other than its approved rate. **Watch for:** a student who reports a clean test as a finished audit. It shows that rates are consistent, not that a line was eligible or billed within the promotion's dates.

### Requirement (4): The largest promotion

**Step 5. Look it up.** In a cell below the test, find the promotion with the largest share:

```
=XLOOKUP(MAX($G$4:$G$12),$G$4:$G$12,$A$4:$A$12)
```

Then look up its PromotionCode, ScopeType, ItemGroup, DiscountPct, EffectiveStartDate and EffectiveEndDate in PromotionProgram with the same XLOOKUP pattern.

**Check:** promotion 8, the Furniture Seasonal Promotion (PROMO-2026-008): ScopeType ItemGroup, so every item in the Furniture item group, a rate of 10%, effective September 1, 2026 to October 31, 2026, with 40.9% of the discount dollars.

### Requirement (5): The memo

**Step 6. Write the half page.** A model memo has four paragraphs: what ran (the programs, their rates and the total given away), the largest and the runner-up, the consistency test and what a matching rate does and does not show, and the follow-up questions. The runner-up is promotion 6, the Wholesale Customer Promotion, with $150,920.03. The questions are the dates: promotions 4 and 7 end before they start, and promotion 1 is a single day. The invoice lines carry no invoice date, so this workbook cannot test whether a line was billed inside its promotion's dates.

**Check:** the memo lists the dates as questions and does not change them.

## Expected results

| Promotion | Lines | LineTotal | DiscountAmount | Share | Where |
|---|---:|---:|---:|---:|---|
| 1 Alder Collection Promotion | 80 | $323,434.84 | $28,124.79 | 3.9% | Steps 2 and 3 |
| 2 Accessories Seasonal Promotion | 431 | $337,900.23 | $37,544.57 | 5.2% | Steps 2 and 3 |
| 3 Strategic Customer Promotion | 149 | $494,666.68 | $67,454.54 | 9.3% | Steps 2 and 3 |
| 4 Brookside Collection Promotion | 74 | $374,091.50 | $32,529.70 | 4.5% | Steps 2 and 3 |
| 5 Textiles Seasonal Promotion | 228 | $468,808.77 | $52,089.91 | 7.2% | Steps 2 and 3 |
| 6 Wholesale Customer Promotion | 414 | $1,106,747.14 | $150,920.03 | 20.9% | Steps 2 and 3 |
| 7 Harbor Collection Promotion | 68 | $350,503.51 | $30,478.53 | 4.2% | Steps 2 and 3 |
| 8 Furniture Seasonal Promotion | 576 | $2,664,482.15 | $296,053.57 | 40.9% | Steps 2 and 3 |
| 9 Design Trade Customer Promotion | 88 | $205,755.54 | $28,057.65 | 3.9% | Steps 2 and 3 |
| All promotions | 2,108 | $6,326,390.36 | $723,253.29 | 100% | Step 2 |
| Lines at another rate; discounts with no PromotionID | 0; 0 | | | | Step 4 |
| Promotions ending before they start; effective for one day | 2; 1 | | | | Step 6 |

> **[Figure placeholder IF-04-2-A]** The promotion summary on Ex 4.2 with data bars, the rate test and the lookup of the largest promotion.
> Kind: excel-mock · Shows: A table with one row for each PromotionID and a Total row. Its columns are PromotionID, PromotionCode, PromotionName, Invoice lines, LineTotal, DiscountAmount, Share of discount dollars, DiscountPct and Lines at another rate. Data bars sit in the DiscountAmount column, the longest bar on the row of the largest promotion. Below the table a three-line block reports the rate test with a result sentence, and a block lists the largest promotion's code, name, scope, rate and dates. · Data: SalesInvoiceLine and PromotionProgram, by promotion (the Expected results table). · Status: planned

> **Instructor notes, Exercise 4.2:** lines / LineTotal / DiscountAmount by promotion (DiscountAmount = ROUND(Quantity\*UnitPrice\*Discount,2); Excel rounding may move totals by a few cents): 1 Alder Collection 80 / 323,434.84 / 28,124.79; 2 Accessories Seasonal 431 / 337,900.23 / 37,544.57; 3 Strategic Customer 149 / 494,666.68 / 67,454.54; 4 Brookside Collection 74 / 374,091.50 / 32,529.70; 5 Textiles Seasonal 228 / 468,808.77 / 52,089.91; 6 Wholesale Customer 414 / 1,106,747.14 / 150,920.03; 7 Harbor Collection 68 / 350,503.51 / 30,478.53; 8 Furniture Seasonal 576 / 2,664,482.15 / 296,053.57; 9 Design Trade Customer 88 / 205,755.54 / 28,057.65; all 2,108 lines / 723,253.29. Promotion 8 holds about 41 percent of the discount dollars. The consistency test finds no differences: every promotion line carries its promotion's DiscountPct, and no line has a discount without a PromotionID. A matching rate shows only that each line carries its program's rate, not that the line was eligible or billed within the program's dates. Students may notice that promotions 4 and 7 have an EffectiveEndDate earlier than their EffectiveStartDate and promotion 1 is effective for a single day; testing billing dates against the effective dates needs the invoice dates, which a later chapter brings onto the lines.

## What a strong answer says

- **Requirement (3).** Zero differences, stated with the test's three parts, and the limit: the test compares rates, not dates or eligibility.
- **Requirement (4).** The promotion, its scope, its rate and its dates, taken from the PromotionProgram Table by lookup, not typed.
- **Requirement (5).** The memo separates what the data show from what the workbook cannot yet show, and lists the odd dates as questions.

A weak answer says the promotions were all valid, or corrects the end dates.

## Common mistakes and how to respond

- **Typed totals.** *Symptom:* a share that does not change when the data refresh. *Response:* ask the student to refresh and watch column G.
- **A moving total.** *Symptom:* shares that fail after the first row. *Response:* press F4 on the reference and read the formula down the column.
- **Every discount zero.** *Cause:* Discount typed as a whole number. *Response:* Tutorial 4.1, Step 6d, Replace current.
- **The rate test read as approval.** *Response:* ask whether a line billed outside the dates would fail it.
- **Fixing the dates.** *Response:* the exercise asks for questions; a data owner corrects master data.
- **Data bars on the wrong column.** *Response:* the bars show discount dollars, the share column is the percentage.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the summary | 25 | One row for each promotion, built with lookups and COUNTIFS or SUMIFS, with totals that tie | Correct but typed or filtered by hand |
| Requirement 2: shares and bars | 15 | Absolute reference, shares add to 100 percent, bars on the discount column | Relative reference or no bars |
| Requirement 3: the test | 20 | A count for each promotion and a stated result | Count without the integrity rows |
| Requirement 4: the largest | 15 | Promotion, scope, rate and dates by lookup | Typed from memory |
| Requirement 5: the memo | 25 | The four paragraphs, the limit of the test, the dates as questions | Findings without the limit, or the dates corrected |

## Extensions and discussion questions

- Add a column for the average rate paid, LineTotal divided by the price before discount, and compare it with DiscountPct.
- Count each promotion's lines by pricing method with a mixed-reference grid, as Tutorial 4.2 does.
- Discuss: Chapter 5 brings the invoice date onto the lines. Which promotions would you test first, and why?
- Discuss: promotion 8 straddles two quarters. What do you expect that to do to a margin bridge?
