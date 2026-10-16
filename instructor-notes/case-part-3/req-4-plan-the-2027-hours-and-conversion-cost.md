# Requirement 4: Plan the 2027 hours and conversion cost (Chapter 11, with the planning of Chapter 7; managerial accounting)

| | |
|---|---|
| Unit | Case Part 3: Planning the Plant's Hours for 2027 |
| Item | Requirement 4 |
| Perspective | Managerial accounting |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 150 minutes |
| Solution file | PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 4 (the view PlantAssets, the depreciation schedule, the standard cost of the output, the Params and Scenarios CTEs and the variance at standard hours), and the Requirement 4 model answer in its closing comments |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The plan turns the case's findings into a decision for 2027: how many hours, how much overtime, what conversion cost, and whether the standards should change. It is Chapter 7's documented model written in SQL: every assumption sits in one row of a Params CTE with its value, source and effect, and three scenarios show what the main assumption, hours per standard hour, is worth. The analytics type is predictive, with a prescriptive close.

Students can:

- reproduce a past charge from master data before projecting it forward (Step 1);
- choose a volume and justify rejecting the budget's (Step 2);
- document assumptions in one place and check the plan against capacity (Step 3);
- build scenarios with `UNION ALL` and read the expected variance (Step 4);
- explain a variance that remains at standard hours and decide on the standards (Step 5).

**Competencies practiced.** CPA Evolution BAR M8 (planning, forecasting and decision models) and M5 (cost accounting and variance analysis); IMA Strategy, Planning and Performance (budgeting and forecasting); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql with the views from Requirements 1 and 3 (PlantEntries, PlantLedger), saved with **Write Changes**. It builds on Chapter 7's documented model (Tutorial 7.3) and Chapter 11's CTEs.
- **Data conditions.** FixedAsset names the account each asset's depreciation is charged to; the WorkCenterCalendar covers only 3 months of 2027; the budget plans about three times the units the plant completed, and the plant's own budget lines are cost of goods sold only.
- **Verify first.** The scenarios query returns 3 rows, and the schedule rebuilt from FixedAsset equals the ledger's depreciation of 2026 to the cent.

## How to run it

Pairs, about 150 minutes: 30 for the depreciation, 20 for the volume and standards, 35 for Params and capacity, 35 for the scenarios, 30 for the variance and the standards decision. The routine: type the two comment lines and the query, select it, click **Execute all/selected SQL**, read the message pane. Hold back Params until a pair has listed its assumptions on paper. **Collect** the Params CTE with its comments, and the scenario table.

## Step-by-step solution

### Part 1: The assumptions

**Step 1. Rebuild the depreciation of the plant's equipment from FixedAsset.** PlantAssets lists the assets whose depreciation is charged to 1090, with a first and last month counted as year times 12 plus month. Depreciation starts the month after the in-service date and ends the month before disposal. Count the months of 2026 from the calendar, and those of 2027 as the same months plus twelve.

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

**Check:** the 2026 total is 303,666.63, equal to the ledger; 2027 is 293,499.96, 24,458.33 a month, and MFG-0005 reaches the end of its life in December 2027. The monthly charge is 24,625.00 in January, 26,958.33 from February (MFG-0007, in service 2026-01-14) and 24,458.33 from June. The two newest assets trace to PO-2024-001942 and PO-2026-011104, each above its approver's limit. **Watch for:** starting in the in-service month totals 305,999.96, 2,333.33 over the ledger, which fails the reproduction; taking 2027's months from the calendar finds only 3 and a charge of 73,374.99.

**Step 2. Choose the volume.** The standard hours of 2026's completions are the base: 68,913 hours at a standard conversion cost of 3,266,422.54 released on the ledger, 47.40 an hour. The completion lines dated in the year carry 3,266,421.95, and PC-2026-014592, dated 2024-05-30 and posted in 2026, makes the difference, so name both bases. The budget plans 3.09 times the units completed and the demand forecast 2.88 times the units ordered, and the Manufacturing cost center's budget lines are cost of goods sold only: no labor or overhead is budgeted. **Watch for:** the budget's volume needs 212,975 hours at standard and 81,903 more than the regular capacity, and reads as a plan that needs heavy overtime.

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

**Check:** the rest of the row: a target of 1.18 hours per standard hour, a straight-time rate of 26.62 and a burden of 14.14%, salaried staff (Production Manager, Planner, Supervisor) at 263,191.24, Factory Overhead at 1,308,869.06, depreciation from Step 1. Capacity is 64 employees times 8 hours times 256 days, 131,072 hours, against 68,913, 81,317 and 104,127. On the year's total no scenario needs overtime, so the plan allows none as a routine. The total is a screen, because weeks and work centers can still bind (Requirement 2), so exceptions are approved against a dated plan. The labor cost assumes that paid hours follow scheduled hours, and the target of 1.18 is a planning target to test. **Watch for:** the whole cost center (137,216 hours of capacity) overstates it; the plan year's few calendar days give 30,208 hours and make every scenario need overtime (38,705, 51,109, 73,919).

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

![The hours each scenario needs against the plant's regular capacity, the picture behind the decision to allow no routine overtime.](../figures/case-part-3/IF-C3-4-A.pdf)

**Check:** conversion cost 3,996,855, 4,373,789, 5,371,136; expected variance 730,432, 1,107,366, 2,104,714; the last is close to 2026's actual conversion variance of 2,159,138.03. Its overtime premium is 266,521 before burden. **Watch for:** `UNION` gives the same rows here, because the ratios differ; write `UNION ALL` anyway, because a repeated scenario would vanish.

**Step 5. Explain the variance at standard hours, and decide on the standards.** The final query sets the plan's rates against the standard's.

```sql
    ROUND(Rate * (1 + Burden), 2) AS RateWithBurden,
    ROUND(StandardLabor / StandardHours, 2)
        AS StandardRate,
    ROUND(Rate * (1 + Burden) * StandardHours
        - StandardLabor, 0) AS LaborExcess,
```

**Check:** the labor rate with burden is 30.39 against the standard 28.28, about 145,220; overhead of 1,902,776 (salaried staff, Factory Overhead, depreciation) is set against 1,317,563 applied at 19.12 an hour, about 585,213. The applied overhead is 746,607 variable and 570,956 fixed, and the output is 53% of the regular employee-hours, which are not the normal capacity of the inventory standard, so the overhead residual is not all idle capacity. Decision: keep the direct-hour standards, which the records give no reason to revise. Direct time stayed below them (62,764 against 66,998, and 59,133 against 66,120 counted on both sides to 2026-12-04), a comparison of period totals that does not validate them. Review the rates, and do not raise the fixed overhead rate to absorb idle capacity (Requirement 5).

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Depreciation, 2026 and 2027 | 303,666.63; 293,499.96 | 1 |
| Volume; conversion per standard hour | 68,913 hours; 47.40 | 2 |
| Regular capacity; hours needed | 131,072; 68,913, 81,317, 104,127 | 3 |
| Expected variance, three scenarios | 730,432, 1,107,366, 2,104,714 | 4 |
| Excess from labor rate; from overhead | 145,220; 585,213 | 5 |

> **Instructor notes, Requirement 4:** volume: 2026 completions of 68,912.79 standard hours. Completions released 3,266,422.54 of standard conversion cost to 1090 (47.40 per standard hour), and the completion lines dated in 2026 carry 3,266,421.95, the 0.59 between them being PC-2026-014592, dated 2024-05-30 and posted 2026-07-01. The budget plans about three times the units the plant completed and the demand forecast two to three times the units ordered (Chapter 7), and no year has a manufacturing labor or overhead budget, only cost of goods sold at standard. Rate: 26.62 an hour (2026, hours-weighted base rate), burden 14.14%; salaried manufacturing staff 263,191.24 gross (Production Manager, Planner, Supervisor). Factory Overhead entries 1,308,869.06 in 2026. Depreciation: monthly OriginalCost / UsefulLifeMonths from the month after the in-service date, through the month before disposal, for assets whose DepreciationDebitAccountID is 92 (account 1090): 24,625.00 in January 2026, 26,958.33 from February (MFG-0007, in service 2026-01-14), 24,458.33 from June (MFG-0004 disposed 2026-06-05), 303,666.63 for the year, equal to the ledger; 2027: 24,458.33 a month, 293,499.96, and MFG-0005 reaches the end of its life in December 2027. MFG-0006 and MFG-0007 are the purchases behind PO-2024-001942 and PO-2026-011104, approved above authority in Tutorial 12.2. Capacity: 64 employees x 8 hours x 256 working days = 131,072 regular hours (the calendar's available hours were 128,833.25 in 2026); the plan needs 68,913 hours at 1.0, 81,317 at 1.18, and 104,127 at the 2026 level of 1.511, so on the year's total no scenario needs overtime, and the plan should allow none as a routine. The total is a screen, because weeks and work centers can still bind (Requirement 2 found surge weeks planned above capacity), so exceptions are approved against a dated plan. The labor cost assumes that paid hours follow the hours scheduled, and the 1.18 target is a planning target to test, not a measure of what the work requires. Conversion cost and expected variance: at 1.0, 3,996,855 and 730,432; at 1.18, 4,373,789 and 1,107,366; at the 2026 level with its overtime premium (266,521.04, 304,207.11 with burden), 5,371,136 and 2,104,714, close to the 2,159,138.03 conversion variance of 2026. The variance left at standard hours comes from the labor rate with burden above the standard rate (30.39 against 28.28 an hour, about 145,000), and from overhead of 1,902,776 (salaried staff, factory overhead, depreciation) against 1,317,563 applied at 19.12 per standard hour (746,607 variable and 570,956 fixed, about 585,000). The output is about 53% of the plant's regular employee-hours, but those hours are not the normal capacity of the inventory standard, and part of the applied overhead is variable, so the residual is not all idle capacity until the overhead is analyzed into fixed and variable, normal and abnormal. Standards: the records give no reason to revise the direct-hour standards. Direct time stayed below the standard hours (62,764 against 66,998 to 2026-12-11, and 59,133 against 66,120 counted on both sides to 2026-12-04, the day indirect time ends), but that compares period totals and does not validate them. Review the rates, and do not raise the fixed overhead rate to absorb idle capacity (Requirement 5).

## What a strong answer says

- **Volume.** The output of 2026, with the reason for rejecting the budget and the forecast, which run well above what the plant made.
- **Documentation.** Each assumption stated once with its value, source and effect, so a reader can change one and rerun.
- **Capacity.** The plan fits regular capacity on the year's total; routine overtime is not needed, and any overtime would be a decision against a dated plan, not a default.
- **Variance and standards.** A variance remains even at standard hours, from the rate with burden and from fixed overhead over few hours; the direct-hour standards stand for now, the rates are reviewed, and idle capacity is not absorbed into the rate.

## Common mistakes and how to respond

- **Depreciation from the in-service month, or the plan year from the calendar.** *Symptom:* a total that misses the ledger by one month, or 73,374.99. *Response:* ask what the schedule must reproduce first, and how many months the calendar holds.
- **The cost center as the headcount, or the plan year's days.** *Symptom:* capacity of 137,216 or 30,208 hours. *Response:* ask who clocks in, and which year's working days are known.
- **The budget's volume.** *Symptom:* a plan 81,903 hours beyond regular capacity. *Response:* ask what the budget's units were compared with the plant's output.
- **Raising the overhead rate.** *Symptom:* a standard that makes the variance vanish. *Response:* ask who bears the cost of idle capacity (Requirement 5).
- **A scenario read as a forecast.** *Symptom:* "the variance will be" one figure. *Response:* ask what each ratio assumes.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Assumptions in one Params CTE | 25 | Value, source and effect for each; volume justified | Values without sources |
| Depreciation reproduced | 15 | Matches the ledger to the cent; 2027 projected | Total off by a month |
| Capacity check and overtime decision | 15 | Capacity from hourly staff and 2026's days; no routine overtime | Wrong headcount or days |
| Scenarios and variance | 25 | `UNION ALL`; premium in the last only; variance read | Costs without the variance |
| Variance at standard hours; standards | 20 | Rate and overhead causes; standards decision | Cause without a decision |

## Extensions and discussion questions

- Add a fourth scenario at the 2025 level of hours per standard hour and say where it falls.
- Find the volume, in standard hours, above which the first-year level needs overtime: the capacity divided by its ratio, 111,078.
- Discuss: the plan allows no overtime, yet the plant used a great deal. What control would keep the plan?
- Discuss: why is hours per standard hour the assumption worth testing, and who owns it?
