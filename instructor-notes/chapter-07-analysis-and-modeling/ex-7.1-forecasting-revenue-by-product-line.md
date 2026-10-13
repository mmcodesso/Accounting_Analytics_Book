# Exercise 7.1: Forecasting Revenue by Product Line

| | |
|---|---|
| Unit | Chapter 7: Forecasting, Budgeting, and What-If Analysis in Excel |
| Item | Exercise 7.1 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheet Ex 7.1 |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial 7.1 tested three methods on the company's monthly revenue. This exercise repeats the test on five series that behave differently, because the bank will rely on the forecast and the method that wins for the company need not win for a product line. It practices FORECAST.LINEAR, the mean absolute percentage error, the choice between methods and the honest statement of a range. The analytics type is predictive.

By the end, students can:

- build a backtest that fits earlier quarters and forecasts held-back ones, for several series at once (outcome 2);
- choose a method for each series and justify it from the errors and from what they know about the data (outcome 2);
- state a forecast as a range with its source, and compare it with a forecast made at another level (outcome 2).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models) and BAR M10 (advanced data analytics); IMA Data Analytics and Insights: Applied Forecasting, and Strategy, Planning, and Performance: Budgeting and Forecasting; IFAC IES 2 (b) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook at the end of Tutorial 7.1, with the InvoiceLines Table and the Forecast worksheet, whose B47 supplies the company forecast. The model answer uses SWITCH and dynamic arrays (Microsoft 365).
- **Data conditions.** InvoiceLines carries Period, the fiscal quarter of each line as text. The first quarter of 2024 holds the start-up month and is the company's lowest quarter. Lighting grew in 2026, Services is volatile under every method, and its revenue is billed design hours. Check that every group has revenue in every quarter.
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

**Check:** H16 is zero. The company's revenue is $5,796,664.16 in the first quarter and $7,287,187.68 in the last. **Watch for:** a Period typed with a space or in another format. SUMIFS then returns zero for the row and H16 shows the missing revenue.

### Requirement (2): The backtest

**Step 2. Forecast the four quarters of 2026 with three methods.** Fit each method to QuarterIndex 1 to 8 and forecast 9 to 12, in rows 20 to 31 (columns C to G, one block of four rows for each method).

a. Trend, in rows 20 to 23: `=FORECAST.LINEAR($A20,C$4:C$11,$A$4:$A$11)`.
b. Mean, in rows 24 to 27: `=AVERAGE(C$4:C$11)`.
c. Same quarter last year, in rows 28 to 31: `=C8`, `=C9`, `=C10` and `=C11`.
d. Repeat the trend and the mean in rows 32 to 39, fitted to rows 5 to 11, which leaves out the first quarter.

**Step 3. Measure the errors.** In row 43 and below, one row for each method, enter the mean absolute percentage error of the four quarters, then pick the lowest.

```
=AVERAGE(ABS(C20:C23-C$12:C$15)/C$12:C$15)
=INDEX($B$43:$B$45,MATCH(MIN(C43:C45),C43:C45,0))
```

> **[Figure placeholder IF-07-1-A]** The backtest grid of Requirement 2, with the lowest error of each item group outlined.
> Kind: excel-mock · Shows: The worksheet Ex 7.1, rows 42 to 49. A header row with the five item groups. Five rows of percentages, one for each method: trend, mean, same quarter last year, trend without the first quarter, mean without the first quarter. The lowest value in each column outlined, and the two rows below that name the lowest method of the first three and of all five. · Data: The mean absolute percentage errors of the backtest (the Expected results). · Status: planned

**Check:** the errors are those of the Expected results. **Watch for:** a trend fitted to all twelve quarters (the forecast has then seen the answer, and the errors shrink), a MAPE without `ABS` (positive and negative errors cancel), and a same-quarter block that points at the wrong year.

### Requirement (3): The choice

**Step 4. Read rows 48 and 49 and choose.** The model answer chooses mean for Furniture, trend for Lighting and mean for Textiles, Accessories and Services. Each choice has a reason:

- Furniture: with all eight quarters the same quarter last year is lowest of the first three (4.2% against 4.6%), but the mean fitted without the first quarter is lowest of all five (2.9%).
- Lighting: the trend (5.5%), because its revenue grew in 2026; it stays lowest without the first quarter (7.4%).
- Textiles: the mean, with or without the first quarter (2.7% and 2.5%).
- Accessories: the mean (5.6%), narrowly ahead of the same quarter last year (5.7%). The trend without the first quarter is lower (4.6%), but the series rises and falls with no steady direction.
- Services: the mean (14.1%), though every method misses by 14% to 18%.

The first quarter of 2024: leave it out of the forecasts. It holds the start-up month. Leaving it out lowers 6 of the 10 trend and mean errors and raises the others, the largest drop being the Furniture trend (13.8% to 6.5%).

### Requirement (4): The forecast of 2027 Q1

**Step 5. Forecast and give the range.** Fit the chosen method to QuarterIndex 2 to 12. In row 53 type the method for each group in blue, then:

```
=SWITCH(C53,"Trend",FORECAST.LINEAR(13,C5:C15,$A$5:$A$15),"Mean",AVERAGE(C5:C15),"Same quarter last year",C12)
=SWITCH(C53,"Trend",C46,"Mean",C47,"Same quarter last year",C45)
```

Enter the first formula in row 54 and the second, the chosen method's backtest error, in row 55. Then enter `=C54*(1-C55)` in row 56 for the low end and `=C54*(1+C55)` in row 57 for the high end, and sum the groups in column H.

**Step 6. Compare with the company forecast.** Compare H54 with Forecast!B47, the forecast of Tutorial 7.1.

**Check:** the item groups sum to $7,417,405.53, which is $128,405.87 (+1.8%) above the company forecast of $7,288,999.66. Most of the gap is Lighting's trend, which carries its growth forward. With the mean for every group the sum would be $7,331,834.70 (+0.6%). **Watch for:** adding the groups' lows and highs to give a range for the total. Those sums ($7,085,593.34 and $7,749,217.72) hold only if every group misses by its full error in the same direction.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Control total | 0 | 1 |
| Company revenue, 2024 Q1 and 2026 Q4 | $5,796,664.16; $7,287,187.68 | 1 |
| Forecast of 2027 Q1, sum of the groups | $7,417,405.53 | 5 |
| Company forecast of Tutorial 7.1 | $7,288,999.66 | 6 |
| Difference | $128,405.87 (+1.8%) | 6 |

| Group | Trend | Mean | Same quarter | Trend without 2024 Q1 | Mean without 2024 Q1 |
|---|---:|---:|---:|---:|---:|
| Furniture | 13.8% | 4.6% | 4.2% | 6.5% | 2.9% |
| Lighting | 5.5% | 9.5% | 8.1% | 7.4% | 8.3% |
| Textiles | 6.0% | 2.7% | 8.4% | 15.4% | 2.5% |
| Accessories | 8.0% | 5.6% | 5.7% | 4.6% | 6.7% |
| Services | 18.4% | 14.1% | 17.3% | 17.3% | 14.4% |

| Group | Method | Forecast, 2027 Q1 | Low | High |
|---|---|---:|---:|---:|
| Furniture | Mean | $4,306,591.81 | $4,181,620.12 | $4,431,563.49 |
| Lighting | Trend | $1,504,563.76 | $1,393,473.65 | $1,615,653.88 |
| Textiles | Mean | $823,775.50 | $803,387.66 | $844,163.34 |
| Accessories | Mean | $484,752.64 | $452,381.72 | $517,123.55 |
| Services | Mean | $297,721.83 | $254,730.19 | $340,713.47 |

> **Instructor notes, Exercise 7.1:** MAPE over 2026 Q1-Q4, fitted on 2024-2025 (trend / mean / same quarter last year): Furniture 13.8% / 4.6% / 4.2%; Lighting 5.5% / 9.5% / 8.1%; Textiles 6.0% / 2.7% / 8.4%; Accessories 8.0% / 5.6% / 5.7%; Services 18.4% / 14.1% / 17.3%. No single method wins: the mean or the same quarter last year suits Furniture, the trend suits Lighting, whose revenue grew in 2026, and the mean suits Textiles, Accessories, and Services (which is volatile under every method). Q1 2024 is depressed by the start-up month, which biases the trend and the Q1 same-quarter forecast for 2025; excluding it is defensible. 2026 actual Q1 by group: Furniture 4,354,123, Lighting 1,569,381, Textiles 816,552, Accessories 475,577, Services 331,220. Mean of all twelve quarters as a reference forecast for 2027 Q1: Furniture 4,212,825 (range of quarters 3,181,390-4,600,821), Lighting 1,403,332, Textiles 814,991, Accessories 479,439, Services 293,317. Company quarterly totals 2024-2026: 5,796,664 / 7,174,741 / 6,907,655 / 7,434,663 / 7,340,014 / 7,376,263 / 7,349,835 / 7,310,590 / 7,546,852 / 7,654,417 / 7,267,963 / 7,287,188. Tutorial 7.1's company forecast is 7,288,999.66.

## What a strong answer says

- **Requirement (3).** A method for each group, with the error that supports it and the reason beyond the error: Lighting's growth, Accessories' lack of direction, Services' volatility. It says that four quarters are a small sample and that the first quarter of 2024 was left out, with the reason.
- **Requirement (4).** Forecasts labeled as billed revenue by invoice date, each with a range described as the backtest error and not a confidence interval, and a sentence on why the item groups need not add up to the company forecast: the methods differ.

A weak answer picks the lowest number in each column without a reason, forecasts with a method fitted on all twelve quarters, or presents the ranges as bounds the revenue will stay within.

## Common mistakes and how to respond

- **Fitting to 2026.** *Symptom:* a trend error of a few percent in every group. *Cause:* the fit range includes the quarters being forecast. *Response:* ask what you knew on the day of the forecast.
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
