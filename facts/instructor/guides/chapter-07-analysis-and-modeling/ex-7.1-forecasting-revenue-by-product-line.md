---
note: ch07.ex1
uses: [ch07.g1]
title: Forecasting Revenue by Product Line
kind: exercise
number: '7.1'
unit: '7'
perspective: financial
tool: excel
minutes: 90
solution: "Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.1"
figures:
  - id: IF-07-1-A
    kind: excel-mock
    purpose: The backtest grid of Requirement 2, with the lowest error of each item group outlined.
    shows: "The worksheet Ex 7.1, rows 42 to 49. A header row with the five item groups. Five rows of percentages, one for each method: trend, mean, same quarter last year, trend without the first quarter, mean without the first quarter. The lowest value in each column outlined, and the two rows below that name the lowest method of the first three and of all five."
    data: The mean absolute percentage errors of the backtest (the Expected results).
---
{% set g = ch07_g1 %}
{% set fu = g.groups[0] %}
{% set li = g.groups[1] %}
{% set tx = g.groups[2] %}
{% set ac = g.groups[3] %}
{% set sv = g.groups[4] %}
# Exercise 7.1: Forecasting Revenue by Product Line

{{ header() }}

## Purpose and learning outcomes

Tutorial 7.1 tested three methods on the company's monthly revenue. This exercise repeats the test on five series that behave differently, because the bank will rely on the forecast and the method that wins for the company need not win for a product line. It practices FORECAST.LINEAR, the mean absolute percentage error, the choice between methods and the honest statement of a range. The analytics type is predictive.

By the end, students can:

- build a backtest that fits earlier quarters and forecasts held-back ones, for several series at once (outcome 2);
- choose a method for each series and justify it from the errors and from what they know about the data (outcome 2);
- state a forecast as a range with its source, and compare it with a forecast made at another level (outcome 2).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models) and BAR M10 (advanced data analytics); IMA Data Analytics and Insights: Applied Forecasting, and Strategy, Planning, and Performance: Budgeting and Forecasting; IFAC IES 2 (b) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook at the end of Tutorial 7.1, with the InvoiceLines Table and the Forecast worksheet, whose B47 supplies the company forecast. The model answer uses SWITCH and dynamic arrays (Microsoft 365).
- **Data conditions.** InvoiceLines carries Period, the fiscal quarter of each line as text. The first quarter of {{ d.F }} holds the start-up month and is the company's lowest quarter. Lighting grew in {{ d.C }}, Services is volatile under every method, and its revenue is billed design hours. Check that every group has revenue in every quarter.
- **A point to settle.** The sample is four quarters per group. Say before students start that a MAPE over four points is a weak basis for a choice, and that the exercise asks them to defend one anyway.

## How to run it

Individual or pairs, about 90 minutes: 15 on the quarterly table (requirement 1), 30 on the backtest (2), 15 on the choice (3) and 20 on the forecast and the comparison (4), with 10 to collect. Hold back the idea of leaving out the first quarter until students have the first three methods, then ask what the first quarter contains. Collect the workbook and the table of choices with their reasons.

## Step-by-step solution

### Requirement (1): The quarterly table

**Step 1. Build the table.**

a. Add a worksheet named `Ex 7.1`. In A3:H3 type `QuarterIndex`, `Period`, the five item groups in the order Furniture, Lighting, Textiles, Accessories, Services, and `Total`.
b. Format B4:B15 as text, then type `2024-Q1` to `2026-Q4` in B4:B15 and the indexes 1 to 12 in A4:A15.
c. In C4, enter this formula and fill it to G15, then enter `=SUM(C4:G4)` in H4 and fill down:

```
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],C$3,InvoiceLines[Period],$B4)
```

d. In A16 type `Control total`, and in H16 enter `=SUM(H4:H15)-SUM(InvoiceLines[LineTotal])`.

**Check:** H16 is zero. The company's revenue is ${{ totals[0]|money }} in the first quarter and ${{ totals[11]|money }} in the last. **Watch for:** a Period typed with a space or in another format. SUMIFS then returns zero for the row and H16 shows the missing revenue.

### Requirement (2): The backtest

**Step 2. Forecast the four quarters of {{ d.C }} with three methods.** Fit each method to QuarterIndex 1 to 8 and forecast 9 to 12, in rows 20 to 31 (columns C to G, one block of four rows for each method).

a. Trend, in rows 20 to 23: `=FORECAST.LINEAR($A20,C$4:C$11,$A$4:$A$11)`.
b. Mean, in rows 24 to 27: `=AVERAGE(C$4:C$11)`.
c. Same quarter last year, in rows 28 to 31: `=C8`, `=C9`, `=C10` and `=C11`.
d. Repeat the trend and the mean in rows 32 to 39, fitted to rows 5 to 11, which leaves out the first quarter.

**Step 3. Measure the errors.** In row 43 and below, one row for each method, enter the mean absolute percentage error of the four quarters, then pick the lowest.

```
=AVERAGE(ABS(C20:C23-C$12:C$15)/C$12:C$15)
=INDEX($B$43:$B$45,MATCH(MIN(C43:C45),C43:C45,0))
```

{{ figure('IF-07-1-A') }}

**Check:** the errors are those of the Expected results. **Watch for:** a trend fitted to all twelve quarters (the forecast has then seen the answer, and the errors shrink), a MAPE without `ABS` (positive and negative errors cancel), and a same-quarter block that points at the wrong year.

### Requirement (3): The choice

**Step 4. Read rows 48 and 49 and choose.** The model answer chooses {{ fu.method|lower }} for Furniture, {{ li.method|lower }} for Lighting and {{ tx.method|lower }} for Textiles, Accessories and Services. Each choice has a reason:

- Furniture: with all eight quarters the same quarter last year is lowest of the first three ({{ fu.errors['Same quarter last year']|pct(1) }} against {{ fu.errors['Mean']|pct(1) }}), but the mean fitted without the first quarter is lowest of all five ({{ fu.errors['Mean without the first quarter']|pct(1) }}).
- Lighting: the trend ({{ li.errors['Trend']|pct(1) }}), because its revenue grew in {{ d.C }}; it stays lowest without the first quarter ({{ li.errors['Trend without the first quarter']|pct(1) }}).
- Textiles: the mean, with or without the first quarter ({{ tx.errors['Mean']|pct(1) }} and {{ tx.errors['Mean without the first quarter']|pct(1) }}).
- Accessories: the mean ({{ ac.errors['Mean']|pct(1) }}), narrowly ahead of the same quarter last year ({{ ac.errors['Same quarter last year']|pct(1) }}). The trend without the first quarter is lower ({{ ac.errors['Trend without the first quarter']|pct(1) }}), but the series rises and falls with no steady direction.
- Services: the mean ({{ sv.errors['Mean']|pct(1) }}), though every method misses by {{ sv.span[0]|pct(0) }} to {{ sv.span[1]|pct(0) }}.

The first quarter of {{ d.F }}: leave it out of the forecasts. It holds the start-up month. Leaving it out lowers {{ g.n_lowered }} of the {{ g.n_changes }} trend and mean errors and raises the others, the largest drop being the {{ g.best_drop.group }} {{ g.best_drop.method }} ({{ g.best_drop.before|pct(1) }} to {{ g.best_drop.after|pct(1) }}).

### Requirement (4): The forecast of {{ d.N }} Q1

**Step 5. Forecast and give the range.** Fit the chosen method to QuarterIndex 2 to 12. In row 53 type the method for each group in blue, then:

```
=SWITCH(C53,"Trend",FORECAST.LINEAR(13,C5:C15,$A$5:$A$15),"Mean",AVERAGE(C5:C15),"Same quarter last year",C12)
=SWITCH(C53,"Trend",C46,"Mean",C47,"Same quarter last year",C45)
```

Enter the first formula in row 54 and the second, the chosen method's backtest error, in row 55. Then enter `=C54*(1-C55)` in row 56 for the low end and `=C54*(1+C55)` in row 57 for the high end, and sum the groups in column H.

**Step 6. Compare with the company forecast.** Compare H54 with Forecast!B47, the forecast of Tutorial 7.1.

**Check:** the item groups sum to ${{ g.total|money }}, which is ${{ g.diff|money }} ({{ g.diff_pct|spct(1) }}) above the company forecast of ${{ g.company|money }}. Most of the gap is Lighting's trend, which carries its growth forward. With the mean for every group the sum would be ${{ g.means_without|money }} ({{ g.means_diff|spct(1) }}). **Watch for:** adding the groups' lows and highs to give a range for the total. Those sums (${{ g.low_sum|money }} and ${{ g.high_sum|money }}) hold only if every group misses by its full error in the same direction.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Control total | 0 | 1 |
| Company revenue, {{ d.F }} Q1 and {{ d.C }} Q4 | ${{ totals[0]|money }}; ${{ totals[11]|money }} | 1 |
| Forecast of {{ d.N }} Q1, sum of the groups | ${{ g.total|money }} | 5 |
| Company forecast of Tutorial 7.1 | ${{ g.company|money }} | 6 |
| Difference | ${{ g.diff|money }} ({{ g.diff_pct|spct(1) }}) | 6 |

| Group | Trend | Mean | Same quarter | Trend without {{ d.F }} Q1 | Mean without {{ d.F }} Q1 |
|---|---:|---:|---:|---:|---:|
{% for x in g.groups %}
| {{ x.group }} | {{ x.errors['Trend']|pct(1) }} | {{ x.errors['Mean']|pct(1) }} | {{ x.errors['Same quarter last year']|pct(1) }} | {{ x.errors['Trend without the first quarter']|pct(1) }} | {{ x.errors['Mean without the first quarter']|pct(1) }} |
{% endfor %}

| Group | Method | Forecast, {{ d.N }} Q1 | Low | High |
|---|---|---:|---:|---:|
{% for x in g.groups %}
| {{ x.group }} | {{ x.method }} | ${{ x.forecast|money }} | ${{ x.low|money }} | ${{ x.high|money }} |
{% endfor %}

{{ expected() }}

## What a strong answer says

- **Requirement (3).** A method for each group, with the error that supports it and the reason beyond the error: Lighting's growth, Accessories' lack of direction, Services' volatility. It says that four quarters are a small sample and that the first quarter of {{ d.F }} was left out, with the reason.
- **Requirement (4).** Forecasts labeled as billed revenue by invoice date, each with a range described as the backtest error and not a confidence interval, and a sentence on why the item groups need not add up to the company forecast: the methods differ.

A weak answer picks the lowest number in each column without a reason, forecasts with a method fitted on all twelve quarters, or presents the ranges as bounds the revenue will stay within.

## Common mistakes and how to respond

- **Fitting to {{ d.C }}.** *Symptom:* a trend error of a few percent in every group. *Cause:* the fit range includes the quarters being forecast. *Response:* ask what you knew on the day of the forecast.
- **Signed errors.** *Symptom:* tiny errors, some negative. *Cause:* no `ABS`. *Response:* ask what an overforecast and an underforecast of equal size do to the average.
- **Mismatched Period.** *Symptom:* zeros in the quarterly table and a nonzero control total. *Response:* ask what the control total in H16 is for.
- **Choosing by the lowest number alone.** *Symptom:* Furniture's same quarter last year chosen without comment. *Response:* ask what that method does when the first quarter is in the history.
- **A range as a confidence interval.** *Symptom:* "95 percent certain". *Response:* ask what the range was computed from.
- **A sum of ranges.** *Symptom:* a total range as the sum of lows and highs. *Response:* ask whether all five groups would miss in the same direction.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the table | 15 | Five groups by twelve quarters, control total zero | No control total |
| Requirement 2: the backtest | 30 | Three methods fitted to eight quarters, MAPE with ABS, errors correct | Fitted to all quarters, or signed errors |
| Requirement 3: the choice | 25 | A method for each group with a reason, and a decision on the first quarter | A choice by the lowest number only |
| Requirement 4: the forecast | 30 | Forecast and range for each group, the comparison and the labeling | No range, or no comparison |

## Extensions and discussion questions

- Add the naive and drift forecasts of the chapter's benchmark table. Does either beat the mean for any group?
- Hold back two quarters instead of four and repeat the choice. Which choices survive?
- Discuss: the covenant forecast goes to the bank. Which of your caveats would you state in the covenant report, and which would you keep in the working paper?
- Discuss: Exercise 7.6 tests management's forecast. What would you ask management about the method behind it?
