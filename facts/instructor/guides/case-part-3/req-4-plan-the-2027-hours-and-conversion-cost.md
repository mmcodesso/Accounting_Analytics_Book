---
note: case3.r4
uses: [case3.g4]
title: Plan the 2027 hours and conversion cost (Chapter 11, with the planning of Chapter 7; managerial accounting)
kind: requirement
number: '4'
unit: case3
perspective: managerial
tool: sql
minutes: 150
solution: "PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 4 (the view PlantAssets, the depreciation schedule, the standard cost of the output, the Params and Scenarios CTEs and the variance at standard hours), and the Requirement 4 model answer in its closing comments"
figures:
  - id: IF-C3-4-A
    kind: chart
    purpose: The hours each scenario needs against the plant's regular capacity, the picture behind the decision to allow no routine overtime.
    shows: "Three columns for the scenarios (standard hours, the first year's level, the last year's level with its overtime), labeled with the hours needed and the share of regular capacity each uses (the standard-hours scenario about half), and a horizontal line for regular capacity well above all three, labeled with its value."
    data: The scenarios query of Step 4, run read-only.
---
{% set g = case3_g4 %}
# Requirement 4: Plan the 2027 hours and conversion cost (Chapter 11, with the planning of Chapter 7; managerial accounting)

{{ header() }}

## Purpose and learning outcomes

The plan turns the case's findings into a decision for {{ d.N }}: how many hours, how much overtime, what conversion cost, and whether the standards should change. It is Chapter 7's documented model written in SQL: every assumption sits in one row of a Params CTE with its value, source and effect, and three scenarios show what the main assumption, hours per standard hour, is worth. The analytics type is predictive, with a prescriptive close.

Students can:

- reproduce a past charge from master data before projecting it forward (Step 1);
- choose a volume and justify rejecting the budget's (Step 2);
- document assumptions in one place and check the plan against capacity (Step 3);
- build scenarios with `UNION ALL` and read the expected variance (Step 4);
- explain a variance that remains at standard hours and decide on the standards (Step 5).

**Competencies practiced.** CPA Evolution BAR M8 (planning, forecasting and decision models) and M5 (cost accounting and variance analysis); IMA Strategy, Planning and Performance (budgeting and forecasting); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql with the views from Requirements 1 and 3 (PlantEntries, PlantLedger), saved with **Write Changes**. It builds on Chapter 7's documented model (Tutorial 7.3) and Chapter 11's CTEs.
- **Data conditions.** FixedAsset names the account each asset's depreciation is charged to; the WorkCenterCalendar covers only {{ g.in_calendar }} months of {{ d.N }}; and the plant's own budget lines are cost of goods sold only.
- **Verify first.** The scenarios query returns {{ g.n.plan }} rows, and the schedule rebuilt from FixedAsset equals the ledger's depreciation of {{ d.C }} to the cent.

## How to run it

Pairs, about 150 minutes: 30 for the depreciation, 20 for the volume and standards, 35 for Params and capacity, 35 for the scenarios, 30 for the variance and the standards decision. The routine: type the two comment lines and the query, select it, click **Execute all/selected SQL**, read the message pane. Hold back Params until a pair has listed its assumptions on paper. **Collect** the Params CTE with its comments, and the scenario table.

## Step-by-step solution

### Part 1: The assumptions

**Step 1. Rebuild the depreciation of the plant's equipment from FixedAsset.** PlantAssets lists the assets whose depreciation is charged to 1090, with a first and last month counted as year times 12 plus month. The case convention, not a universal policy: cost over the useful life with a zero residual value, charged by month from the month after the in-service date to the month before disposal and no longer than the life. Count the months of {{ d.C }} from the calendar, and those of {{ d.N }} as the same months plus twelve.

```sql
SELECT pa.AssetCode, pa.InServiceDate, pa.DisposalDate, pa.Monthly,
    ROUND(pa.Monthly * (SELECT COUNT(*) FROM Months AS m
        WHERE m.MonthIndex BETWEEN pa.FirstMonth AND pa.LastMonth),
        2) AS Depreciation2026,
    ROUND(pa.Monthly * (SELECT COUNT(*) FROM Months AS m
        WHERE m.MonthIndex + 12
            BETWEEN pa.FirstMonth AND pa.LastMonth),
        2) AS Depreciation2027,
```

**Check:** the {{ d.C }} total is {{ dep_c|money }}, equal to the ledger; {{ d.N }} is {{ dep_n|money }}, {{ monthly_n|money }} a month, and {{ ending.code }} reaches the end of its life in {{ ending.month }} {{ d.N }}. The monthly charge is {{ jan|money }} in January, {{ changes[0].amount|money }} from {{ changes[0].month }} ({{ changes[0].code }}, in service {{ changes[0].date }}) and {{ changes[1].amount|money }} from {{ changes[1].month }}. The two newest assets trace to {{ new[0].po }} and {{ new[1].po }}, each above its approver's limit. **Watch for:** starting in the in-service month totals {{ g.total_early|money }}, {{ g.early_gap|money }} over the ledger, which fails the reproduction; taking {{ d.N }}'s months from the calendar finds only {{ g.in_calendar }} and a charge of {{ g.short_dep|money }}.

**Step 2. Choose the volume.** The standard hours of {{ d.C }}'s completions are the base: {{ std|num }} hours at a standard conversion cost of {{ released|money }} released on the ledger, {{ conv_rate|num(2) }} an hour. The completion lines dated in the year carry {{ lines|money }}{% for x in stray %}, and {{ x.number }}, dated {{ x.dated }} and posted in {{ d.C }}, makes the difference{% endfor %}, so name both bases. The budget plans {{ g.volume[-1][1]|num(2) }} times the units completed and the demand forecast {{ g.volume[-1][2]|num(2) }} times the units ordered, and the Manufacturing cost center's budget lines are cost of goods sold only: no labor or overhead is budgeted. The two ratios have different denominators, units completed and units ordered. **Watch for:** weighting each item's budget units by its standard labor hours gives {{ g.budget_hours|num }} standard hours, {{ g.budget_over|num }} more than the regular capacity, so the budget reads as a plan that needs heavy overtime. The figure is an annual screen and does not show a feasible work-center schedule.

**Step 3. Document the assumptions in one Params CTE, and check capacity.** Each assumption has a comment with its value, source and effect, and a scalar subquery.

```sql
        -- volume: the 2026 output in standard hours; the budget's units
        -- run well above the units completed, and the demand forecast
        -- well above the units ordered
        (SELECT StandardHours FROM Output WHERE WorkYear = '2026')
            AS StandardHours,
```

```sql
        -- regular capacity: active hourly employees x 8 hours x the
        -- working days of 2026, because the calendar stops early in 2027
        (SELECT COUNT(*)
         FROM Employee AS e
             INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
         WHERE cc.CostCenterName = 'Manufacturing'
             AND e.PayClass = 'Hourly'
             AND e.IsActive = 1) AS Employees,
```

**Check:** the rest of the row: a target of {{ levels[1]|num(2) }} hours per standard hour, a straight-time rate of {{ rate|num(2) }} and a burden of {{ burden|pct(2) }}, salaried staff ({{ titles }}) at {{ salary|money }}, Factory Overhead at {{ foh|money }}, depreciation from Step 1. Capacity is {{ employees }} employees times 8 hours times {{ days }} days, {{ capacity|count }} hours, against {{ need[0]|num }}, {{ need[1]|num }} and {{ need[2]|num }}. On the year's total no scenario needs overtime, so the plan allows none as a routine. The total is a screen, because weeks and work centers can still bind (Requirement 2), so exceptions are approved against a dated plan. The labor cost assumes that paid hours follow scheduled hours, and the target of {{ levels[1]|num(2) }} is a planning target to test. **Watch for:** the whole cost center ({{ g.emp_all[0][3]|count }} hours of capacity) overstates it; the plan year's few calendar days give {{ g.short_days[0][3]|count }} hours and make every scenario need overtime ({{ g.short_days|map(attribute=4)|map('num')|join(', ') }}).

### Part 2: The scenarios

**Step 4. Build the Scenarios CTE and the expected variance.** Three rows with `UNION ALL`, each carrying every Params column; the conversion cost is hourly labor with burden, the overtime premium (the last scenario only), the salaried staff with burden, Factory Overhead and depreciation, less the standard conversion cost.

```sql
Scenarios AS (
    SELECT 'Standard hours' AS Scenario, 1.0 AS Ratio,
        0 AS WithPremium, p.*
    FROM Params AS p
    UNION ALL
    SELECT '2024 level', p.TargetRatio, 0, p.*
    FROM Params AS p
    UNION ALL
    SELECT '2026 level with its overtime', p.CurrentRatio, 1, p.*
    FROM Params AS p
)
```

{{ figure('IF-C3-4-A') }}

**Check:** conversion cost {{ conv|map('num')|join(', ') }}; expected variance {{ variance|map('num')|join(', ') }}; the last is close to {{ d.C }}'s actual conversion variance of {{ actual|money }}. Its overtime premium is {{ premium|num }} before burden. **Watch for:** `UNION` gives the same rows here, because the ratios differ; write `UNION ALL` anyway, because a repeated scenario would vanish.

**Step 5. Explain the variance at standard hours, and decide on the standards.** The final query sets the plan's rates against the standard's.

```sql
    ROUND(Rate * (1 + Burden), 2) AS RateWithBurden,
    ROUND(StandardLabor / StandardHours, 2)
        AS StandardRate,
    ROUND(Rate * (1 + Burden) * StandardHours
        - StandardLabor, 0) AS LaborExcess,
```

**Check:** the labor rate with burden is {{ g.final[5]|num(2) }} against the standard {{ g.final[6]|num(2) }}, about {{ g.final[7]|num }}; overhead of {{ g.final[8]|num }} (salaried staff, Factory Overhead, depreciation) is set against {{ g.final[9]|num }} applied at {{ oh_rate|num(2) }} an hour, about {{ g.final[10]|num }}. The applied overhead is {{ variable|num }} variable and {{ fixed|num }} fixed, and the output is {{ g.final[11]|pct(0) }} of the regular employee-hours, which are not the normal capacity of the inventory standard, so the overhead residual is not all idle capacity. Decision: keep the direct-hour standards provisionally, since the records give no reason to revise them. Direct time stayed below them ({{ direct|num }} against {{ std_cut|num }}, and {{ direct_common|num }} against {{ std_common|num }} counted on both sides to {{ ind_end }}), a comparison of period totals that neither validates them nor shows they are right. Review the rates on a defensible normal-capacity basis, and do not raise the fixed overhead rate simply to absorb idle capacity (Requirement 5).

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Depreciation, {{ d.C }} and {{ d.N }} | {{ dep_c|money }}; {{ dep_n|money }} | 1 |
| Volume; conversion per standard hour | {{ std|num }} hours; {{ conv_rate|num(2) }} | 2 |
| Regular capacity; hours needed | {{ capacity|count }}; {{ need|map('num')|join(', ') }} | 3 |
| Expected variance, three scenarios | {{ variance|map('num')|join(', ') }} | 4 |
| Excess from labor rate; from overhead | {{ g.final[7]|num }}; {{ g.final[10]|num }} | 5 |

{{ expected() }}

## What a strong answer says

- **Volume.** The output of {{ d.C }} as the stated baseline, with the reasons for rejecting the budget's units ({{ g.volume[-1][1]|num(2) }} times those completed) and the forecast's ({{ g.volume[-1][2]|num(2) }} times those ordered), which have different denominators.
- **Documentation.** Each assumption stated once with its value, source and effect, so a reader can change one and rerun.
- **Capacity.** The plan fits regular capacity on the year's total; routine overtime is not needed, and any overtime would be a decision against a dated plan, not a default.
- **Variance and standards.** A variance remains even at standard hours. The labor-rate difference is separated from the overhead residual, which is analyzed into fixed and variable and normal and abnormal cost before it is called idle capacity. The direct-hour standards stay provisionally, and the fixed rate is not raised simply to absorb idle capacity.

## Common mistakes and how to respond

- **Depreciation from the in-service month, or the plan year from the calendar.** *Symptom:* a total that misses the ledger by one month, or {{ g.short_dep|money }}. *Response:* ask what the schedule must reproduce first, and how many months the calendar holds.
- **The cost center as the headcount, or the plan year's days.** *Symptom:* capacity of {{ g.emp_all[0][3]|count }} or {{ g.short_days[0][3]|count }} hours. *Response:* ask who clocks in, and which year's working days are known.
- **The budget's volume.** *Symptom:* a plan {{ g.budget_over|num }} hours beyond regular capacity. *Response:* ask what the budget's units were compared with the plant's output.
- **Raising the overhead rate.** *Symptom:* a standard that makes the variance vanish. *Response:* ask who bears the cost of idle capacity (Requirement 5).
- **A scenario read as a forecast.** *Symptom:* "the variance will be" one figure. *Response:* ask what each ratio assumes.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Assumptions in one Params CTE | 25 | Value, source and effect for each; volume justified | Values without sources |
| Depreciation reproduced | 15 | Matches the ledger to the cent; {{ d.N }} projected | Total off by a month |
| Capacity check and overtime decision | 15 | Capacity from hourly staff and {{ d.C }}'s days; no routine overtime | Wrong headcount or days |
| Scenarios and variance | 25 | `UNION ALL`; premium in the last only; variance read | Costs without the variance |
| Variance at standard hours; standards | 20 | Rate and overhead causes; standards decision | Cause without a decision |

## Extensions and discussion questions

- Add a fourth scenario at the {{ d.P }} level of hours per standard hour and say where it falls.
- Find the volume, in standard hours, above which the first-year level needs overtime: the capacity divided by its ratio, {{ (capacity / levels[1])|num }}.
- Discuss: the plan allows no overtime, yet the plant used a great deal. What control would keep the plan?
