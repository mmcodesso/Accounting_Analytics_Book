---
note: ch04.ex2
uses: [ch04.g2]
title: Reviewing Promotional Discounts
kind: exercise
number: '4.2'
unit: '4'
perspective: financial
tool: excel
minutes: 60
solution: "Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheet Ex 4.2"
figures:
  - id: IF-04-2-A
    kind: excel-mock
    purpose: The promotion summary on Ex 4.2 with data bars, the rate test and the lookup of the largest promotion.
    shows: "A table with one row for each PromotionID and a Total row. Its columns are PromotionID, PromotionName, Invoice lines, LineTotal, DiscountAmount, Share of discount dollars, DiscountPct and Lines at another rate, with PromotionCode (column B) hidden to fit the figure. Data bars sit in the DiscountAmount column, the longest bar on the row of the largest promotion. Below the table a three-line block reports the rate test with a result sentence, and a block lists the largest promotion's code, name, scope, rate and dates."
    data: SalesInvoiceLine and PromotionProgram, by promotion (the Expected results table).
---
{% set g = ch04_g2 %}
# Exercise 4.2: Reviewing Promotional Discounts

{{ header() }}

## Purpose and learning outcomes

The exercise turns Tutorial 4.3's clue into a summary the sales director can read: which promotions ran, what they gave away, and whether each was applied at its approved rate. It practices lookups and COUNTIFS on Tables, an absolute reference to a total, data bars, and a consistency test. It also teaches the limit of that test: a matching rate shows only that each line carries its program's rate. The analytics type is descriptive.

By the end, students can:

- summarize a Table by a key held in another Table, with one row for each key (outcome 2);
- use an absolute reference for a share of a total (outcome 3);
- apply data bars to a column (outcome 5);
- design a consistency test, read a clean result, and say what it does not show (outcomes 1 and 6).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S1 M8 T3 to T4 (data mining and analysis); IMA Data Analysis; IFAC IES 2 (a) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and Tables.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 4.3, with the SalesInvoiceLine Table (its DiscountAmount calculated column) and the PromotionProgram Table of {{ g.n_promos }} rows.
- **The type trap.** If Discount was left as a whole number in Tutorial 4.1, Step 6, DiscountAmount is zero on every line and the rate test flags all {{ g.lines|count }} promotion lines. A student whose summary shows this has found the trap; send them to Replace current in the Changed Type step.
- **Data conditions.** Every promotion line carries its promotion's DiscountPct, no line has a discount without a PromotionID, and every PromotionID on the lines is in PromotionProgram, so the test finds no differences. Promotions {{ g.backwards_ids }} end before they start, and promotion {{ g.single_ids }} is effective for a single day. The exercise asks students to list these as questions, not to correct them.

## How to run it

Pairs or individual, about 60 minutes: 20 on the summary (requirement 1), 10 on shares and data bars (2), 10 on the rate test (3), 5 on the largest promotion (4) and 15 on the memo (5). Hold back the absolute-reference hint until a student sees the share column change down the rows. Collect the worksheet and the memo.

## Step-by-step solution

### Requirement (1): One row for each promotion

**Step 1. Lay out the summary.**

a. Insert a worksheet named `Ex 4.2`. In row 3 type `PromotionID`, `PromotionCode`, `PromotionName`, `Invoice lines`, `LineTotal`, `DiscountAmount`, `Share of discount dollars`, `DiscountPct` and `Lines at another rate`.
b. In A4 to A{{ 3 + g.n_promos }} enter the PromotionIDs 1 to {{ g.n_promos }}, one for each row of the PromotionProgram Table.

**Step 2. Fill the lookups and the totals.** In B4 enter the formula below, and repeat it in C4 for PromotionName and in H4 for DiscountPct:

```
=XLOOKUP($A4,PromotionProgram[PromotionID],PromotionProgram[PromotionCode])
```

In D4 enter `=COUNTIFS(SalesInvoiceLine[PromotionID],$A4)`, in E4 `=SUMIFS(SalesInvoiceLine[LineTotal],SalesInvoiceLine[PromotionID],$A4)` and in F4 the same SUMIFS on DiscountAmount. Fill each down. In row {{ 4 + g.n_promos }} enter `Total` and a SUM for D, E and F.

**Check:** {{ g.lines|count }} promotion lines with a LineTotal of ${{ g.total|money }} and a DiscountAmount of ${{ g.discount|money }}. **Watch for:** a student who filters the Table by hand instead of writing formulas. The summary then cannot refresh.

### Requirement (2): Shares and data bars

**Step 3. Add the share and the bars.**

a. In G4 enter `=F4/$F${{ 4 + g.n_promos }}` and fill down. Format column G as a percentage.
b. Select F4 to F{{ 3 + g.n_promos }} and choose **Home > Conditional Formatting > Data Bars**.

**Check:** the shares add up to 100 percent, and the longest bar is on promotion {{ g.top.id }}, with {{ g.top.share|pct }}. **Watch for:** `F{{ 4 + g.n_promos }}` without the dollar signs. It moves down the column, and the shares turn to errors or nonsense. This is the absolute reference of Tutorial 4.2.

### Requirement (3): The rate test

**Step 4. Count the lines at another rate.** In I4 enter the formula below, fill it down, and total column I:

```
=COUNTIFS(SalesInvoiceLine[PromotionID],$A4,SalesInvoiceLine[Discount],"<>"&H4)
```

Add two integrity rows below the summary: `=COUNTIFS(SalesInvoiceLine[PromotionID],"",SalesInvoiceLine[Discount],"<>0")` for discounts with no promotion, and `=COUNTIFS(SalesInvoiceLine[PromotionID],"<>")-D{{ 4 + g.n_promos }}` for promotion lines the summary leaves out.

**Check:** every cell of column I and both integrity rows show 0, so no promotion was applied at a rate other than the rate the PromotionProgram Table records for it. **Watch for:** a student who reports a clean test as a finished audit. It shows that the lines' rates agree with that Table, not that the Table's rates were authorized, or that a line was eligible or billed within the promotion's dates.

### Requirement (4): The largest promotion

**Step 5. Look it up.** In a cell below the test, find the promotion with the largest share:

```
=XLOOKUP(MAX($G$4:$G$12),$G$4:$G$12,$A$4:$A$12)
```

Then look up its PromotionCode, ScopeType, ItemGroup, DiscountPct, EffectiveStartDate and EffectiveEndDate in PromotionProgram with the same XLOOKUP pattern.

**Check:** promotion {{ g.top.id }}, the {{ g.top.name }} ({{ g.top.code }}): ScopeType {{ g.top.scope }}, so {{ g.scope_phrase }}, a rate of {{ g.top.rate|pct(0) }}, effective {{ g.top.start_long }} to {{ g.top.end_long }}, with {{ g.top.share|pct }} of the discount dollars.

### Requirement (5): The memo

**Step 6. Write the half page.** A model memo has four paragraphs: what ran (the programs, their rates and the total given away), the largest and the runner-up, the consistency test and what a matching rate does and does not show, and the follow-up questions. The runner-up is promotion {{ g.second.id }}, the {{ g.second.name }}, with ${{ g.second.discount|money }}. The questions are the dates: promotions {{ g.backwards_ids }} end before they start, and promotion {{ g.single_ids }} is a single day. The invoice lines carry no invoice date, so this workbook cannot test whether a line was billed inside its promotion's dates.

**Check:** the memo lists the dates as questions and does not change them.

## Expected results

| Promotion | Lines | LineTotal | DiscountAmount | Share | Where |
|---|---:|---:|---:|---:|---|
{% for p in g.promos %}
| {{ p.id }} {{ p.name }} | {{ p.lines|count }} | ${{ p.total|money }} | ${{ p.discount|money }} | {{ p.share|pct }} | Steps 2 and 3 |
{% endfor %}
| All promotions | {{ g.lines|count }} | ${{ g.total|money }} | ${{ g.discount|money }} | {{ (g.promos|sum(attribute='share'))|pct(0) }} | Step 2 |
| Lines at another rate; discounts with no PromotionID | 0; 0 | | | | Step 4 |
| Promotions ending before they start; effective for one day | {{ g.backwards|length }}; {{ g.single|length }} | | | | Step 6 |

{{ figure('IF-04-2-A') }}

{{ expected() }}

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
- Discuss: promotion {{ g.top.id }} straddles two quarters. What do you expect that to do to a margin bridge?
