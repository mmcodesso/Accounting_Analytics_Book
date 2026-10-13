---
note: ch18.r7
uses: [ch18.g7]
title: Value the capacity that buying would free (Chapter 7)
kind: requirement
number: '7'
unit: '18'
perspective: managerial
tool: mixed
minutes: 120
solution: "Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheets Capacity, Growth 40%, Growth 40% Sensitivity, Growth 50% and Growth 50% Sensitivity; Chapter18-capstone-sql.zip: MakeBuy.sql, Q23"
figures:
  - id: IF-18-7-A
    kind: excel-mock
    purpose: The Capacity sheet's table of hours freed at each work center, with the plant's use before and after buying.
    shows: "One row for each work center and a Plant row, with the routing time used, the hours freed, the hours used after buying, the practical capacity and the use of practical capacity before and after; the Plant row is outlined and the Quality Assurance row shows nothing freed."
    data: The Capacity sheet of the model workbook, the first table.
  - id: IF-18-7-B
    kind: excel-mock
    purpose: The growth sheet that holds Solver's model, with its variable cells, constraints and objective marked.
    shows: "The work-center block with practical capacity, load at growth, hours used after buying, slack and status, the binding row outlined; the family block with the units bought as amber variable cells and the added cost; the total added cost cell marked as the objective."
    data: The sheet Growth 40% of the model workbook.
---
{% set g = ch18_g7 %}
{% macro buys(l) %}{% for b in l.bought %}{{ b.units|num(0) }} {{ b.short }}{{ " and " if not loop.last else "" }}{% endfor %}{% endmacro %}
# Requirement 7: Value the capacity that buying would free (Chapter 7)

{{ header() }}

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

**Step 1. Return the hours freed with Q23.** Routine: type the query at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. It sums each work center's run and setup hours for the families to buy over FamilyActivity, once per work center; the Cutting column shows the pattern:

```sql
ROUND(SUM(CASE WHEN Family IN ('FUR-BNH', 'FUR-NGT', 'FUR-TBL')
        THEN Cutting ELSE 0 END), 1) AS CuttingFreed,
```

**Check:** one row. The five freed columns add up to {{ total|num(0) }} hours, UseBefore reads {{ use_before|num(3) }} and UseAfter {{ use_after|num(3) }}. **Watch for:** only the run hours (the standard labor hours): {{ g.run_only|num(0) }} hours, because setup is left out. Measured on the available hours the use reads {{ g.avail_before|pct(1) }} falling to {{ g.avail_after|pct(1) }}, not the practical figures.

**Step 2. Build the Capacity table.** On the Capacity sheet the freed hours of each work center are a SUMPRODUCT over the Activity Table, weighted by whether the family is bought.

```jinja
Freed, Cutting   {{ g.f.freed }}
Use before       {{ g.f.use }}
Use after        {{ g.f.use_after }}
```

**Check:** the sheet agrees with Q23 center by center: {% for x in freed %}{{ x.short }} {{ x.hours|num(0) }}{{ ", " if not loop.last else "" }}{% endfor %}, and nothing at Quality Assurance. The hours freed here use the year's completions; Requirement 6's positions use the routing time of the year's sales ({{ crew_hours|num(0) }} hours), a different base, so both numbers are right.

{{ figure('IF-18-7-A') }}

### Part 2: Freed hours against the unused capacity

**Step 3. Compare, in hours and positions.** The Costs sheet holds the practical hours the plant leaves unused; a position is the practical hours on the Assumptions sheet.

```jinja
Unused, in positions   {{ g.f.unused_pos }}
```

**Check:** the plant leaves {{ unused_h|num(1) }} practical hours unused, {{ unused_positions|num(2) }} positions, against {{ g.positions|num(2) }} positions freed by buying. So fitting the crew to the work is the larger question, and the two reductions add up only if both can be made. The production manager is right that idle capacity is not the products' fault, but it is still a cost.

### Part 3: If the crew is kept

**Step 4. Show what stays.** A family bought takes only materials and the overhead that varies with it. The crew's time on it and the supervision and equipment it carried stay.

```jinja
Crew's cost of that time   {{ g.f.crew_cost }}
Supervision and equipment  {{ g.f.support }}
```

**Check:** the crew's cost of the {{ crew_hours|num(0) }} hours is ${{ crew_cost|num(0) }} and the supervision and equipment ${{ supervision|num(0) }}. Spread over the remaining families' {{ g.remain_h|num(0) }} routing hours, absorption cost rises ${{ g.spread|num(2) }} an hour; time-driven costs do not move, and the unused capacity grows to ${{ g.unused_after|num(0) }}.

### Part 4: The optional growth test

**Step 5. Set up the model on a growth sheet.** The sheets Growth 40% and Growth 50% each hold one model: the load of the year's sales at the growth rate, the hours each unit bought frees, and an amber column of units bought (L14:L19).

a. Compute the headroom first, practical capacity over the load of the year's sales, work center by work center (`{{ g.f.head }}`). **Check:** growth of about {{ (headroom|map(attribute='ratio')|min - 1)|pct(0) }} reaches the first limit.
b. Open **Data > Solver**. Minimize the total added cost (B21) by changing L14:L19, subject to the hours used at each work center (E6:E10) not above its practical capacity (B6:B10) and the units bought (L14:L19) not above the units at growth (C14:C19); use the Simplex LP method, with unconstrained variables non-negative. Keep the solution and ask for the Sensitivity report.

```jinja
Added cost per unit bought   {{ g.f.extra }}
Hours used after buying      {{ g.f.used }}
```

**Check:** at {{ g.growths[0]|pct(0) }}, {{ lp[0].binding[0].short }} binds, an hour is worth ${{ lp[0].binding[0].price|num(2) }}, and Solver buys {{ buys(lp[0]) }} for ${{ lp[0].cost|num(0) }}. At {{ g.growths[1]|pct(0) }}, {{ lp[1].binding[0].short }} binds at ${{ lp[1].binding[0].price|num(2) }} and it buys {{ buys(lp[1]) }} for ${{ lp[1].cost|num(0) }}. The Sensitivity report reads the shadow prices as negative numbers, because the model minimizes.

**Watch for:** Solver set to maximize (it then buys all {{ g.wrong[0].max_n|count }} families, added cost ${{ g.wrong[0].max_cost|num(0) }}), the units bought left unbounded (at {{ g.growths[1]|pct(0) }} it buys {{ g.wrong[1].over[0].units|num(0) }} {{ g.wrong[1].over[0].short }}, more than twice its demand of {{ g.wrong[1].over[0].demand|num(0) }}), and the limit set at the available hours (it buys nothing).

{{ figure('IF-18-7-B') }}

**Step 6. Test the answer against the quote.** The model leaves out the minimum purchase and the tooling. **Check:** the relaxed plan buys {{ lp[0].short_of|join(' and ') }} below the minimum at {{ g.growths[0]|pct(0) }} and {{ lp[1].short_of|join(' and ') }} at {{ g.growths[1]|pct(0) }}, which the supplier would not accept. Solved with the minimum and the tooling, the plan the supplier would accept is {{ buys(lp[0].contract) }} at {{ g.growths[0]|pct(0) }} (${{ lp[0].contract.total|num(0) }} over the two years, no work center binding) and {{ buys(lp[1].contract) }} at {{ g.growths[1]|pct(0) }} (${{ lp[1].contract.total|num(0) }}, {{ lp[1].contract.binding[0].short }} binding at ${{ lp[1].contract.binding[0].price|num(2) }}). The relaxed model's shadow prices do not carry over to it.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Hours freed; use of practical capacity before and after | {{ total|num(0) }}; {{ use_before|pct(1) }} and {{ use_after|pct(1) }} | 1 |
| Unused hours; positions unused and freed | {{ unused_h|num(1) }}; {{ unused_positions|num(2) }} and {{ g.positions|num(2) }} | 3 |
| Crew's cost kept; supervision and equipment | ${{ crew_cost|num(0) }}; ${{ supervision|num(0) }} | 4 |
| Solver: binding center, added cost | {{ lp[0].binding[0].short }}, ${{ lp[0].cost|num(0) }}; {{ lp[1].binding[0].short }}, ${{ lp[1].cost|num(0) }} | 5 |

{{ expected() }}

## What a strong answer says

- **Freed hours are not a saving.** Buying frees {{ total|num(0) }} hours and lowers the plant's use, but the plant already leaves more hours unused. The comparison moves the decision from outsourcing to fitting the crew to the work, which is the production manager's.
- **If the crew is kept,** the products bought take only materials and the overhead that varies; the crew's time, supervision and equipment stay. Under absorption they land on the families that remain.
- **The growth test is a benchmark.** Capacity binds only after growth of about {{ (headroom|map(attribute='ratio')|min - 1)|pct(0) }}; Solver's plan ignores the minimum and the tooling, so cost the plan the supplier would accept.

A weak answer reports the freed hours without the comparison, or presents Solver's plan as the decision.

## Common mistakes and how to respond

- **Run hours only.** *Symptom:* {{ g.run_only|num(0) }} hours freed. *Response:* ask what a changeover costs.
- **Use on available hours.** *Symptom:* {{ g.avail_before|pct(1) }} before buying. *Response:* ask which capacity the assumptions name.
- **Freed hours read as savings.** *Symptom:* a saving equal to hours times a rate. *Response:* ask who stops being paid.
- **Solver mis-set.** *Symptom:* a maximum, an unbounded purchase, or no purchase at all. *Response:* read the objective and the limits aloud.
- **A shadow price read as a saving.** *Symptom:* a negative shadow price quoted as a loss. *Response:* ask what the model minimizes.
- **Solver's plan taken as the decision.** *Symptom:* {{ lp[0].short_of|join(' and ') }} bought below the minimum. *Response:* ask whether the supplier would accept it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Hours freed and use | 25 | By work center, setup included, practical capacity | Run hours, or available hours |
| Comparison with unused capacity | 25 | Hours and positions, with the meaning for the decision | Numbers without the meaning |
| The crew-kept case | 20 | What stays, and how the remaining families' cost moves | Only the absorption effect |
| Solver test (optional, scaled if skipped) | 25 | Model, binding center, shadow price, check against the minimum | Model without the check |
| Documentation | 5 | Sources and the saved model | Missing |

## Extensions and discussion questions

- Add the tooling and the minimum to Solver with a binary cell for each family, and compare with the plan above.
- Discuss: if growth never comes, what is the quote worth?
- Discuss: who would you ask to confirm that the unused hours can be released?
