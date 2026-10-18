# Requirement 9: Revise the standards, and measure what they mean for the statements (Chapter 9)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 9 |
| Perspective | Financial accounting |
| Tools | More than one tool |
| Time | About 150 minutes |
| Solution file | Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Standards; Chapter18-capstone-sql.zip: MakeBuy.sql, Q27 to Q31 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Standards serve inventory as well as decisions. Students rebuild a standard rate on normal capacity, revalue the finished goods the old standards carry, measure the effect on statements already issued against the materiality screen, and say what evidence would show whether those statements were wrong. The revaluation is a sensitivity, and the recommendation depends on telling an error from a change in estimate. The analytics type is diagnostic, ending in a prescriptive recommendation.

Students can:

- build the rate from the plan and compare it with the current, time-driven and actual rates (Part 1);
- rebuild the stock from the movements and revalue it at each year-end (Part 2);
- measure the effect against the screen, test it against normal capacity and indirect hours, and recommend how to report it (Parts 3 and 4).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S2 M7 (materiality); IMA Reporting and Control (cost accounting and financial statement preparation); IFAC IES 2 (a) and (b); AACSB A5 part 5.1 (Excel; SQL).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with Requirements 2 and 4, and MakeBuy.sql on CharlesRiver_Capstone.sqlite.
- **Data conditions.** The finished goods on the opening entry have no item detail, so the stock is rebuilt from completions less shipments plus returns, which counts it as made since the opening only if shipments drew on new production first. The ledger records no income tax, and the closes net revenue and expense to zero.
- **Verify first.** The plan figures typed on Assumptions must equal the records: the sheet's three checks (B19:B21) read TRUE.
- **Authority.** Topic 330, Subtopic 10, section 30 (initial measurement), and Topic 250, Subtopic 10, sections 20, 45 and 50 (definitions, reporting of errors and changes in estimate, disclosures). Read the Codification itself before teaching a definitive conclusion. Charles River is not treated as an SEC registrant, so Staff Accounting Bulletins 99 and 108 only illustrate what else bears on materiality.

## How to run it

Individual work, about 150 minutes: 30 for the rate, 20 for the comparisons, 35 for the stock, 25 for the revaluation and the screen, 25 for the sensitivities, 15 for the recommendation. Hold back the sensitivities until students have the base effect, and the evidence question until they say the statements were wrong. **Collect** the Standards sheet and the recommendation.

## Step-by-step solution

### Part 1: The rate on normal capacity

**Step 1. Build the proposed rate.** Five components per standard hour: the labor rate with burden for direct hours, the overhead that varies (Requirement 2), indirect labor at the plan's indirect hours, and the plan's supervision and depreciation over the plan volume.

```
Direct labor    =LaborRate*(1+Burden)
Indirect labor  =IndirectHours*B5
Supervision     =PlanSalaries*(1+Burden)/PlanVolume
Depreciation    =PlanDepreciation/PlanVolume
Rate            =SUM(B5:B9)
```

**Check:** 30.38 + 18.99 + 5.47 + 4.36 + 4.26 = 63.46 an hour, on 68,912.79 standard hours at 1.18 hours per standard hour and a labor rate of 26.62 with 14.14% burden. **Watch for:** supervision without the burden, a rate of 62.92, and the base year's depreciation instead of the plan year's, 63.61. Q27 returns the plan year's depreciation of the assets charged to the clearing account, $293,499.96.

**Step 2. Compare it with the other rates.** Put the rates on one basis, the standard hours completed. The current rate is the standard conversion released. The time-driven rate is the Factory Overhead entries plus the committed cost of the routing time used, and leaves out the unused capacity. The actual rate is all the inputs to `1090`, so it adds the unused capacity's cost to the time-driven conversion. The committed cost per practical routing hour, $39.97, is a separate rate.

```
Current   =ConversionReleased/StdHours
Actual    =Inputs1090/StdHours
```

**Check:** the proposed rate $63.46 against $47.40 today, $61.81 time-driven and $78.77 actual; the time-driven rate plus the unused capacity's $16.96 an hour is the actual rate. A standard on actual cost would carry the capacity left unused and the hours recorded above the routings into inventory. Topic 330 charges abnormal costs, such as idle facility expense, to the period, but hours above the routings count only if the routing standard, the normal support work and the actual conditions show them abnormal, which the records do not settle.

![A mock of the top of the Standards sheet, where the proposed rate is built and set beside the other rates.](../figures/chapter-18-make-buy-or-reprice/IF-18-9-A.pdf)

### Part 2: The stock and its revaluation

**Step 3. Rebuild the stock at each year-end (Q28 and Q29).** Routine: type the query at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Q28 returns the units of each manufactured finished good at the three year-ends; Q29 totals them, leaving out the items with a negative balance. The block is a fragment of Q29 (run the complete query), the sum of the movements up to each year-end:

```sql
OnHand AS (
    SELECT ye.FiscalYear, mv.ItemID, SUM(mv.Quantity) AS Units
    FROM YearEnds AS ye
        INNER JOIN Moves AS mv ON mv.MoveDate <= ye.YearEnd
    GROUP BY ye.FiscalYear, mv.ItemID
)
```

**Check:** Q28 returns 83 rows, Q29 75, 79, 82 items at the three year-ends. FUR-SDB-0006 goes negative at the end of 2024; FUR-DSK-0044 goes negative at the end of 2026. The opening stock was drawn on, and item-level opening balances would say which layers remain. Paste Q28 into the Table OnHand and add the standard hours, conversion and standard cost per unit by lookup.

**Step 4. Revalue at the proposed rate.** The revaluation is the standard hours in stock at the new rate, less the conversion already in them.

```
Standard hours (first year-end)   =SUMPRODUCT((OnHand[OnHand2024]>0)*OnHand[OnHand2024]*OnHand[StdHoursPerUnit])
Revaluation      =B36*NewRate-B37
```

**Check:** at the three year-ends the revaluation is +$257,435, +$369,596, +$471,117. **Watch for:** the stock valued at the new rate and not netted against the conversion in it: $1,873,625 for the last year-end.

### Part 3: The effect on the statements

**Step 5. Measure it against the screen (Q30 and Q31).** Q30 returns income before income taxes for each year, leaving the closes out of revenue and expense.

Q31 returns the opening entry's finished goods, $4,111,795.76, which has no item detail and is left out. The effects follow from the revaluations: retained earnings at the start of the prior year, each year's income, and each balance.

**Check:** the screens are $256,717.74 and $225,180.56. Retained earnings change by +$257,435, the prior year's income by +$112,161 and the current year's by +$101,521; the balances, +$369,596 and +$471,117, are above their screens and the income effects below. **Watch for:** the closes left in, a screen of $0.00; and a balance read as an income effect: +$471,117 against +$101,521.

**Step 6. Test the answer.** Normal capacity changes the volume that supervision and depreciation are spread over; the indirect hours the rate allows are a separate question of labor content.

**Check:** normal capacity at 90% and 110% of the plan volume gives rates of 64.42 and 62.68, and balance effects of +$499,387 and +$447,987 at the last year-end, above the screen. With no indirect hours the rate is 58.00: the prior year's balance, +$243,171, falls below its screen and the last year's, +$309,655, stays above.

![The revaluation of the stock at the two year-ends against each year's materiality screen, the picture behind the recommendation.](../figures/chapter-18-make-buy-or-reprice/IF-18-9-B.pdf)

### Part 4: Error or estimate

**Step 7. Say what evidence would settle it, and recommend.** The rates are the plan's applied to earlier stock: a sensitivity, not an established error. The outline is in the strong answer.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Proposed rate; current; time-driven; actual | $63.46; $47.40; $61.81; $78.77 | 1, 2 |
| Revaluation at each year-end | +$257,435; +$369,596; +$471,117 | 4 |
| Screens, prior year and current | $256,717.74; $225,180.56 | 5 |
| Rate with no indirect hours; at the two normal capacities | $58.00; $64.42; $62.68 | 6 |

> **Instructor notes, Requirement 9:** proposed rate per standard hour on the Part III plan (68,912.79 standard hours, a planning target of 1.18 hours per standard hour): direct labor 26.62 x 1.1414 = 30.38; overhead that varies 18.99; indirect labor at plan 0.18 x 30.38 = 5.47; supervision 263,191.24 x 1.1414 / 68,912.79 = 4.36; depreciation 293,499.96 / 68,912.79 = 4.26; total 63.46. Current 47.40; time-driven 61.81; 2026 actual 78.77, which includes the capacity left unused and the hours recorded above the routings (Part III): idle facility expense is an abnormal cost that Topic 330 charges to the period, while hours above the routings count only if the routing standard, normal support work and actual conditions show them abnormal. Revised standard costs (time-driven beside): BNH 398.17 (399.01), NGT 306.99 (308.67), SDB 337.91 (338.07), TBL 358.19 (357.64), SCN 189.74 (188.24), PIL 180.97 (180.09). Manufactured finished goods made since the opening and on hand, as the movements can rebuild them (completions less shipments plus returns, by item, the items with a positive balance): that counts the stock as made since the opening only if shipments drew on new production first, and FUR-SDB-0006 at 2024 and FUR-DSK-0044 at 2026 go negative, so the opening stock was drawn on and item-level opening balances are needed to know which layers remain: 2024 11,880.3 units, 16,482.8 standard hours, conversion 788,641.14 (47.85 an hour); 2025 17,103.3, 23,116.1, 1,097,455.36; 2026 21,883.6, 29,522.4, 1,402,508.30 (5,627,028.26 at standard). Revaluation at 63.46: +257,435 / +369,596 / +471,117. What is treated as normal capacity, the volume over which supervision and depreciation (8.62 an hour at plan) are spread, moves it: at 90% and 110% of the plan volume the rate is 64.42 and 62.68, and the revaluation +273,219 / +391,731 / +499,387 and +244,521 / +351,485 / +447,987. The indirect hours the rate allows are a different question, of labor content: with none (1.0 hours, 58.00) the revaluation is +167,288 / +243,171 / +309,655, and the 2025 balance (243,171) falls below the 5% screen while 2026's (309,655) stays above. Time-driven +230,093 / +331,251 / +422,145; at 2026 actual +922,829 (capitalizing idle capacity). Effect on the fiscal 2025 and 2026 statements at 63.46: retained earnings at January 1, 2025, +257,435, 2025 income +112,161, 2026 income +101,521; balance sheet +369,596 (2025) and +471,117 (2026), both above the 5% screen of tbl-18-02 (256,717.74 and 225,180.56) at either end of the normal-capacity range, while the income effects are below it. The 5% is a first, quantitative screen: a strong answer also weighs the nature of the item, the aggregate with other misstatements, the line items and periods it touches, and the tax effect the ledger cannot supply. The rates are 2027's plan applied to 2024-2026 stock: a sensitivity, not an established error. Before calling the difference an error, a strong answer asks whether the standards in use, the normal capacity of those years, and the costs known when each set of statements was prepared would have given a materially different inventory under Topic 330, names that evidence (period costs and volumes, the variances' disposition, counts and item-level opening balances), and recommends accordingly: revised statements if a material prior-period error is established (inventories, retained earnings, and income corrected, with the correction disclosed), the new standard prospectively if the difference is a change in estimate, and, for an error established but immaterial to those years, a correction in the next statements only if recording it there would not itself materially misstate that year, judged on amount and nature (otherwise the comparatives are revised), all under ASC Topic 250. The decision is the CFO's. Only manufactured finished goods revalue, because purchased ones are carried at their receipt cost. The opening 4,111,795.76 of finished goods has no item detail and is left out.

## What a strong answer says

- **The rate.** Normal capacity at the plan volume, with supervision and depreciation spread over it; a standard on actual cost would capitalize idle capacity.
- **The effect.** The balance effects exceed the screen and the income effects do not, at either end of the normal-capacity range; with no indirect hours the prior year's balance falls below it.
- **Materiality is more than the screen.** The item's nature, its aggregate with other misstatements, the lines and periods it touches, and the tax effect the ledger cannot supply.
- **Evidence before correction.** Would the standards in use, the normal capacity of those years and the costs then known have given a materially different inventory under Topic 330? Name the period costs and volumes, the variances' disposition, counts and item-level opening balances.
- **The recommendation.** A material prior-period error: revised statements, with the correction disclosed. A change in estimate: the new standard from now on. An error immaterial to the earlier years: corrected in the next statements only if recording it there would not itself materially misstate that year, judged on amount and nature, and otherwise by revising the comparatives (ASC Topic 250). The decision is the CFO's, and the shareholders hear which.

A weak answer calls the revaluation an error, or stops at the screen.

## Common mistakes and how to respond

- **A standard on actual cost.** *Symptom:* a revaluation of +$922,829. *Response:* ask whether idle capacity is part of what a unit costs.
- **Burden left out, or the wrong year's depreciation.** *Symptom:* a rate of 62.92 or 63.61. *Response:* ask which year the plan covers and what burden is.
- **The closes left in.** *Symptom:* a screen of $0.00. *Response:* ask what the closes do to revenue and expense.
- **A balance read as income.** *Symptom:* an income effect above the screen. *Response:* ask what changed during the year.
- **A sensitivity called an error.** *Symptom:* "restate the statements". *Response:* ask what evidence at the time would show it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| The rate and its comparisons | 20 | Five components, three comparisons, the reason for normal capacity | A rate without the reason |
| The stock and the revaluation | 25 | Rebuilt from the movements, negatives noted, netted against current conversion | Totals without the caveat |
| Effect against the screen | 20 | Opening, income and balances, the screen, closes left out | Balances only |
| Sensitivities | 15 | Normal capacity and indirect hours, kept apart | One sensitivity |
| Error or estimate | 15 | The evidence named and the recommendation by case | A recommendation without evidence |
| Documentation | 5 | Plan checks and sources | Missing |

## Extensions and discussion questions

- Revalue at the rate for normal capacity at the plan volume of another year, and compare the effects.
- Discuss: what would you ask the controller for before telling the shareholders anything?
- Discuss: why does the same revaluation call for different action as an error and as a change in estimate?
