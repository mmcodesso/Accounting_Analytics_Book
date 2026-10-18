# Requirement 7: Value the capacity that buying would free (Chapter 7)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 7 |
| Perspective | Managerial accounting |
| Tools | More than one tool |
| Time | About 120 minutes |
| Solution file | Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheets Capacity, Growth 40%, Growth 40% Sensitivity, Growth 50% and Growth 50% Sensitivity; Chapter18-capstone-sql.zip: MakeBuy.sql, Q23 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Buying a family frees hours, and freed hours are an opportunity, not a saving. The requirement asks students to measure them by work center, set them against the capacity the plant already leaves unused, and see that fitting the crew to the work is the larger question. The optional Solver test asks which families to buy if volume grew, and teaches that a relaxed model's answer is a benchmark. The analytics type is predictive.

Students can:

- measure the hours buying frees at each work center and the plant's use afterwards, with Q23 (Part 1);
- compare them with the unused capacity in hours and positions, and show what happens to the remaining families if the crew is kept (Parts 2 and 3);
- optionally, run Solver on growth, report the binding work center and its shadow price, and test the answer against the quote's terms (Part 4).

**Competencies practiced.** CPA Evolution BAR M8 (planning techniques, forecasting and decision models); IMA Strategy, Planning, and Performance (decision analysis, strategic cost management); IFAC IES 2 (b); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with Requirements 4 and 6, and MakeBuy.sql with Requirement 3's view FamilyActivity saved: Q23 fails with `no such table` without it. Part 4 needs the Solver add-in.
- **Data conditions.** Routings (RoutingOperation) give each family's run and setup hours at each work center; the calendar gives the hours available.
- **Verify first.** Solver was not run when the model workbook was built: its optima were computed by the bounded simplex method and written as values, and the model is saved on each growth sheet. Run Solver on one sheet before class and compare the objective with the Expected results.

## How to run it

Individual work, about 120 minutes: 25 for the freed hours, 15 for the comparison, 15 for the crew-kept case, 55 for the optional Solver test, 10 for documentation. Hold back the unused-capacity comparison until students have the freed hours. **Collect** the Capacity sheet and, if attempted, the growth sheets.

## Step-by-step solution

### Part 1: The hours freed and the use afterwards

**Step 1. Return the hours freed with Q23.** Routine: type the query at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. It sums each work center's run and setup hours for the families to buy over FamilyActivity, once per work center. The block is a fragment, the Cutting column, and the complete statement is Q23:

```sql
ROUND(SUM(CASE WHEN Family IN ('FUR-BNH', 'FUR-NGT', 'FUR-TBL')
        THEN Cutting ELSE 0 END), 1) AS CuttingFreed,
```

**Check:** one row. The five freed columns add up to 17,795 hours, UseBefore reads 0.716 and UseAfter 0.544. **Watch for:** only the run hours (the standard labor hours): 16,481 hours, because setup is left out. Measured on the available hours the use reads 57.3% falling to 43.5%, not the practical figures.

**Step 2. Build the Capacity table.** On the Capacity sheet the freed hours of each work center are a SUMPRODUCT over the Activity Table, weighted by whether the family is bought.

```
Freed, Cutting   =SUMPRODUCT(XLOOKUP(Activity[Family],'Make or Buy'!$A$10:$A$15,'Make or Buy'!$P$10:$P$15,0),Activity[CuttingRun]+Activity[CuttingSetup])
Use before       =B6/E6
Use after        =D6/E6
```

**Check:** the sheet agrees with Q23 center by center: Cutting 3,884, Assembly 7,607, Finishing 4,596, Packing 1,708, and nothing at Quality Assurance. The hours freed here use the year's completions, the base of the capacity table. Requirement 6's positions use the routing time of the year's sales (17,299 hours), a different base, so both numbers are right as long as each is labeled and neither is mixed with the other.

![A mock of the Capacity sheet's table of hours freed at each work center, with the plant's use before and after buying.](../figures/chapter-18-make-buy-or-reprice/IF-18-7-A.pdf)

### Part 2: Freed hours against the unused capacity

**Step 3. Compare, in hours and positions.** The Costs sheet holds the practical hours the plant leaves unused; a position is the practical hours on the Assumptions sheet.

```
Unused, in positions   =UnusedHours/PositionHours
```

**Check:** on the completions basis the plant leaves 29,243.7 practical hours unused, 17.85 position-equivalents, against 10.86 freed by buying (10.56 on Requirement 6's sales basis). So fitting the crew to the work is the larger question, and the two reductions add up only if both can be made. The production manager is right that idle capacity is not the products' fault, but it is still a cost. **Watch for:** the hours read as a staffing plan. They are annual hours from standard times. The rough-cut plan's 49 weekly buckets from 2026-01-05 through 2026-12-07 (to the week of the last time record, a subset of the year's plan) put 6 weeks above the plant's available hours and 21 work-center weeks above their own (up to 132.1% at Finishing). Across all 52 buckets that start in the year, the last ending 2027-01-03, the counts are 7 and 24. Planned hours are not recorded work, so a position-equivalent is not a removable job until the weeks, skills and coverage are checked.

### Part 3: If the crew is kept

**Step 4. Show what stays.** A family bought takes only materials and the overhead that varies with it. The crew's time on it and the supervision and equipment it carried stay.

```
Crew's cost of that time   =BuyHours*CrewRate
Supervision and equipment  =BuyHours*SupportRate
```

**Check:** on the sales basis, the crew's cost of the 17,299 hours is $590,117 and the supervision and equipment $101,246. Spread over the remaining families' 50,252 routing hours, absorption cost rises $13.76 an hour. Time-driven costs do not move, and on the completions basis of the capacity table the unused capacity cost grows from $1,168,726 to $1,879,909. **Watch for:** $1,860,089, the unused hours of the completions basis plus the hours freed on the sales basis, two populations in one figure.

### Part 4: The optional growth test

**Step 5. Set up the model on a growth sheet.** The sheets Growth 40% and Growth 50% each hold one model: the load of the year's sales at the growth rate, the hours each unit bought frees, and an amber column of units bought (L14:L19).

a. Compute the headroom first, practical capacity over the load of the year's sales, work center by work center (`=B30/C30`). **Check:** growth of about 40% reaches the first limit.
b. Open **Data > Solver**. Minimize the total added cost (B21) by changing L14:L19, subject to the hours used at each work center (E6:E10) not above its practical capacity (B6:B10) and the units bought (L14:L19) not above the units at growth (C14:C19); use the Simplex LP method, with unconstrained variables non-negative. Keep the solution and ask for the Sensitivity report.

```
Added cost per unit bought   =D14-E14
Hours used after buying      =D6-SUMPRODUCT(G$14:G$19,$L$14:$L$19)
```

**Check:** at 40%, Finishing binds, an hour is worth $6.01, and Solver buys 151 BNH for $391. At 50%, Assembly binds at $49.98 and it buys 2,182 BNH and 2,311 NGT for $86,177. The Sensitivity report reads the shadow prices as negative numbers, because the model minimizes.

**Watch for:** Solver set to maximize (it then buys all 6 families, added cost $1,172,949), the units bought left unbounded (at 50% it buys 4,435 BNH, more than twice its demand of 2,182), and the limit set at the available hours (it buys nothing).

![A mock of the growth sheet that holds Solver's model, with its variable cells, constraints and objective marked.](../figures/chapter-18-make-buy-or-reprice/IF-18-7-B.pdf)

**Step 6. Test the answer against the quote.** The model leaves out the minimum purchase and the tooling. **Check:** the relaxed plan buys BNH below the minimum at 40% and NGT at 50%, which the supplier would not accept. Solved with the minimum and the tooling, the plan the supplier would accept is 1,160 BNH at 40% ($24,017 over the two years, no work center binding) and 1,940 BNH and 2,560 NGT at 50% ($228,417, Assembly binding at $3.63). The relaxed model's shadow prices do not carry over to it.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Hours freed; use of practical capacity before and after | 17,795; 71.6% and 54.4% | 1 |
| Unused hours; position-equivalents unused and freed (completions basis) | 29,243.7; 17.85 and 10.86 | 3 |
| Unused capacity cost before and after buying (completions basis) | $1,168,726; $1,879,909 | 4 |
| Crew's cost kept; supervision and equipment | $590,117; $101,246 | 4 |
| Solver: binding center, added cost | Finishing, $391; Assembly, $86,177 | 5 |

> **Instructor notes, Requirement 7:** buying BNH, NGT, and TBL frees, on the 2026 completions that the capacity table counts, Cutting 3,884, Assembly 7,607, Finishing 4,596, Packing 1,708 hours, 17,795 in all, 10.86 position-equivalents (Requirement 6 counts 10.56 on the 2026 sales, 17,299 hours); plant use of practical capacity falls from 71.6% to 54.4%. On the same base the routings leave 29,243.7 practical hours unused, 17.85 position-equivalents, more than buying would free, so fitting the crew to the work is a larger question than outsourcing (the two reductions add up only if both can be made), and the production manager's point that idle capacity is not the products' fault is right but cuts both ways, because it is still a cost. These are annual hours from standard times, not proof that anyone did no work and not a staffing plan: of the rough-cut plan's 49 weekly buckets from 2026-01-05 through 2026-12-07 (to the week of the last time record, a time-record-aligned subset of the year's plan), 6 are above the plant's available hours and 21 work-center weeks above their own (up to 118.4% for the plant and 132.1% at Finishing, both in the week of 2026-11-16); across all 52 buckets that start in 2026, the last ending 2027-01-03, 7 plant weeks and 24 work-center weeks are above them. So positions are checked week by week, by work center and skill, before any is removed. If the crew is kept, the crew's cost of those families' routing time (about 590,117 on the sales basis) and the supervision and equipment the three families carried (about 101,246) stay and spread over the rest, so their absorption cost rises; their time-driven cost does not move, and the unused capacity cost rises, on the completions basis, from 1,168,726 to 1,879,909. Practical capacity over 2026 use (sales basis): Cutting 1.80, Assembly 1.40, Finishing 1.40, Packing 1.58, QA 10.24, so growth of about 40% reaches the first limit. Solver (Simplex LP, buying the quoted families at their crew-kept extra cost, each family's units free between zero and its demand at growth: a relaxed benchmark, with the quote's minimum and tooling left out, and an annual one, not a production schedule): +40%, Finishing binds (shadow price about 6.01 an hour), buy about 151 BNH, extra cost about 391; +50%, Assembly binds (about 49.98), buy all 2,182 BNH and about 2,311 NGT, extra cost about 86,177. These plans buy BNH below the 80% minimum at +40% and NGT below the 80% minimum at +50%, so the supplier could not accept them. With the minimum and the tooling kept (every choice of families solved, keeping the least cost over the two years the prices are fixed): +40%, buy 1,160 BNH (the minimum), about 3,008 a year of added cost plus 18,000 of tooling, 24,017 over the two years, no work center binding; +50%, buy 1,940 BNH and 2,560 NGT (the minimum), about 94,209 a year of added cost plus 40,000 of tooling, 228,417 over the two years, Assembly binding (about 3.63 an hour, for that choice of families). The relaxed model's shadow prices hold for that model only.

## What a strong answer says

- **Freed hours are not a saving.** Buying frees 17,795 hours and lowers the plant's use, but the plant already leaves more hours unused, on the same base. The comparison moves the decision from outsourcing to fitting the crew to the work, which is the production manager's, week by week and work center by work center.
- **If the crew is kept,** the products bought take only materials and the overhead that varies; the crew's time, supervision and equipment stay. Under absorption they land on the families that remain.
- **The growth test is a benchmark.** Capacity binds only after growth of about 40%; Solver's plan ignores the minimum and the tooling, so cost the plan the supplier would accept. An annual model is not a production schedule.

A weak answer reports the freed hours without the comparison, or presents Solver's plan as the decision.

## Common mistakes and how to respond

- **Run hours only.** *Symptom:* 16,481 hours freed. *Response:* ask what a changeover costs.
- **Use on available hours.** *Symptom:* 57.3% before buying. *Response:* ask which capacity the assumptions name.
- **Freed hours read as savings.** *Symptom:* a saving equal to hours times a rate. *Response:* ask who stops being paid.
- **Solver mis-set.** *Symptom:* a maximum, an unbounded purchase, or no purchase at all. *Response:* read the objective and the limits aloud.
- **A shadow price read as a saving.** *Symptom:* a negative shadow price quoted as a loss. *Response:* ask what the model minimizes.
- **Solver's plan taken as the decision.** *Symptom:* BNH bought below the minimum. *Response:* ask whether the supplier would accept it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Hours freed and use | 25 | By work center, setup included, practical capacity | Run hours, or available hours |
| Comparison with unused capacity | 25 | Hours and positions, with the meaning for the decision | Numbers without the meaning |
| The crew-kept case | 20 | What stays, and how the remaining families' cost moves | Only the absorption effect |
| Solver test (optional) | 25 | Model, binding center, shadow price, check against the minimum | Model without the check |
| Documentation | 5 | Sources and the saved model | Missing |

Without the Solver test, score the required components out of 75, divide the points earned by 75 and multiply by 100, then apply the case weight; a student who skips it takes no penalty.

## Extensions and discussion questions

- Add the tooling and the minimum to Solver with a binary cell for each family, and compare with the plan above.
- Discuss: if growth never comes, what is the quote worth?
- Discuss: who would you ask to confirm that the unused hours can be released?
