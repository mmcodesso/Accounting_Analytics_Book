---
note: ch18.r9
uses: [ch18.g9]
title: Revise the standards, and measure what they mean for the statements (Chapter 9)
kind: requirement
number: '9'
unit: '18'
perspective: financial
tool: mixed
minutes: 150
solution: "Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Standards; Chapter18-capstone-sql.zip: MakeBuy.sql, Q27 to Q31"
figures:
  - id: IF-18-9-A
    kind: excel-mock
    purpose: The top of the Standards sheet, where the proposed rate is built and set beside the other rates.
    shows: "Five component rows (direct labor, the overhead that varies, indirect labor, supervision, depreciation) with their basis, then the proposed rate, the labor-content case, the current standard, the time-driven rate, the base year's actual cost and the two rates at the ends of the normal-capacity range; the proposed rate is outlined."
    data: The Standards sheet of the model workbook, rows for the rate and its comparisons.
  - id: IF-18-9-B
    kind: chart
    purpose: The revaluation of the stock at the two year-ends against each year's materiality screen, the picture behind the recommendation.
    shows: "Two groups of bars, one for each year-end, with the revaluation at the proposed rate, with no indirect hours, and at each end of the normal-capacity range; a horizontal mark in each group shows that year's screen, so the one bar below it, the earlier year with no indirect hours, is visible. Dollar labels on the bars."
    data: The revaluation rows and the materiality screens of the Standards sheet.
---
{% set g = ch18_g9 %}
{% macro sg(x) %}{{ "-" if x < 0 else "+" }}${{ (x|abs)|num(0) }}{% endmacro %}
# Requirement 9: Revise the standards, and measure what they mean for the statements (Chapter 9)

{{ header() }}

## Purpose and learning outcomes

Standards serve inventory as well as decisions. Students rebuild a standard rate on normal capacity, revalue the finished goods the old standards carry, measure the effect on statements already issued against the materiality screen, and say what evidence would show whether those statements were wrong. The revaluation is a sensitivity, and the recommendation depends on telling an error from a change in estimate. The analytics type is diagnostic, ending in a prescriptive recommendation.

Students can:

- build the rate from the plan and compare it with the current, time-driven and actual rates (Part 1);
- rebuild the stock from the movements and revalue it at each year-end (Part 2);
- measure the effect against the screen, test it against normal capacity and indirect hours, and recommend how to report it (Parts 3 and 4).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S2 M7 (materiality); IMA Reporting and Control (cost accounting, financial recordkeeping, financial statement preparation); IFAC IES 2 (a) and (b); AACSB A5 part 5.1 (Excel; SQL).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with Requirements 2 and 4, and MakeBuy.sql on CharlesRiver_Capstone.sqlite.
- **Data conditions.** The finished goods on the opening entry have no item detail, so the stock is rebuilt from completions less shipments plus returns, which counts it as made since the opening only if shipments drew on new production first. The ledger records no income tax, and the year-end closes net revenue and expense to zero.
- **Verify first.** The plan figures typed on Assumptions must equal the records: the sheet's three checks (B19:B21) read TRUE.

## How to run it

Individual work, about 150 minutes: 30 for the rate, 20 for the comparisons, 35 for the stock, 25 for the revaluation and the screen, 25 for the sensitivities, 15 for the recommendation. Hold back the sensitivities until students have the base effect, and the evidence question until they say the statements were wrong. **Collect** the Standards sheet and the recommendation.

## Step-by-step solution

### Part 1: The rate on normal capacity

**Step 1. Build the proposed rate.** Five components per standard hour: the labor rate with burden for direct hours, the overhead that varies (Requirement 2), indirect labor at the plan's indirect hours, and the plan's supervision and depreciation over the plan volume.

```jinja
Direct labor    {{ g.f.direct }}
Indirect labor  {{ g.f.indirect }}
Supervision     {{ g.f.supervision }}
Depreciation    {{ g.f.depreciation }}
Rate            {{ g.f.rate }}
```

**Check:** {{ p.direct|num(2) }} + {{ p.variable|num(2) }} + {{ p.indirect|num(2) }} + {{ p.supervision|num(2) }} + {{ p.depreciation|num(2) }} = {{ new_rate|num(2) }} an hour, on {{ plan_stdh|num(2) }} standard hours at {{ plan_hours|num(2) }} hours per standard hour and a labor rate of {{ rate|num(2) }} with {{ burden|pct(2) }} burden. **Watch for:** supervision without the burden, a rate of {{ g.rate_nb|num(2) }}, and the base year's depreciation instead of the plan year's, {{ g.rate_dep|num(2) }}. Q27 returns the plan year's depreciation of the assets charged to the clearing account, ${{ plan_dep|num(2) }}:

```sql
SELECT ROUND(SUM(Monthly * (ToMonth - FromMonth + 1)), 2)
    AS PlanYearDepreciation
FROM InPlanYear
WHERE ToMonth >= FromMonth;
```

**Step 2. Compare it with the other rates.** The current rate is the conversion released per standard hour, the time-driven rate adds the unused capacity's cost back, and the actual rate is the year's inputs per standard hour.

```jinja
Current   {{ g.f.current }}
Actual    {{ g.f.actual }}
```

**Check:** the proposed rate ${{ new_rate|num(2) }} against ${{ current|num(2) }} today, ${{ td_std|num(2) }} time-driven and ${{ actual|num(2) }} actual. A standard on actual cost would carry the idle capacity and the hours paid beyond the work into inventory, and Topic 330 charges abnormal costs of that kind to the period.

{{ figure('IF-18-9-A') }}

### Part 2: The stock and its revaluation

**Step 3. Rebuild the stock at each year-end (Q28 and Q29).** Routine: type the query at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Q28 returns the units of each manufactured finished good at the three year-ends; Q29 totals them, leaving out the items with a negative balance. The core of Q29 sums the movements up to each year-end:

```sql
OnHand AS (
    SELECT ye.FiscalYear, mv.ItemID, SUM(mv.Quantity) AS Units
    FROM YearEnds AS ye
        INNER JOIN Moves AS mv ON mv.MoveDate <= ye.YearEnd
    GROUP BY ye.FiscalYear, mv.ItemID
)
```

**Check:** Q28 returns {{ g.n_q28|count }} rows, Q29 {{ g.n_items|join(', ') }} items at the three year-ends. {% for n in g.neg %}{{ n[1] }} goes negative at the end of {{ n[0] }}{{ "; " if not loop.last else "." }}{% endfor %} The opening stock was drawn on, and item-level opening balances would say which layers remain. Paste Q28 into the Table OnHand and add the standard hours, conversion and standard cost per unit by lookup.

**Step 4. Revalue at the proposed rate.** The revaluation is the standard hours in stock at the new rate, less the conversion already in them.

```jinja
Standard hours (first year-end)   {{ g.f.hours }}
Revaluation      {{ g.f.reval }}
```

**Check:** at the three year-ends the revaluation is {% for s in stock %}{{ sg(s.plan) }}{{ ", " if not loop.last else "" }}{% endfor %}. **Watch for:** the stock valued at the new rate and not netted against the conversion in it: ${{ g.full_value|num(0) }} for the last year-end.

### Part 3: The effect on the statements

**Step 5. Measure it against the screen (Q30 and Q31).** Q30 returns income before income taxes for each year, leaving the closes out:

```sql
WHERE a.AccountType IN ('Revenue', 'Expense')
    AND gl.FiscalYear BETWEEN 2024 AND 2026
    AND gl.VoucherNumber NOT IN (
        SELECT EntryNumber
        FROM JournalEntry
        WHERE EntryType LIKE 'Year-End Close%')
```

Q31 returns the opening entry's finished goods, ${{ opening_fg|num(2) }}, which has no item detail and is left out. The effects follow from the revaluations: retained earnings at the start of the prior year, each year's income, and each balance.

**Check:** the screens are ${{ mat_p|money }} and ${{ mat_c|money }}. Retained earnings change by {{ sg(stock[0].plan) }}, the prior year's income by {{ sg(s_p.plan - s_f.plan) }} and the current year's by {{ sg(s_c.plan - s_p.plan) }}; the balances, {{ sg(s_p.plan) }} and {{ sg(s_c.plan) }}, are above their screens and the income effects below. **Watch for:** the closes left in, a screen of ${{ g.with_closes|money }}; and a balance read as an income effect: {{ sg(s_c.plan) }} against {{ sg(s_c.plan - s_p.plan) }}.

**Step 6. Test the answer.** Normal capacity changes the volume that supervision and depreciation are spread over; the indirect hours the rate allows are a separate question of labor content.

**Check:** normal capacity at {{ normal[0].share|pct(0) }} and {{ normal[1].share|pct(0) }} of the plan volume gives rates of {{ normal[0].rate|num(2) }} and {{ normal[1].rate|num(2) }}, and balance effects of {{ sg(s_c.normal[0]) }} and {{ sg(s_c.normal[1]) }} at the last year-end, above the screen. With no indirect hours the rate is {{ one_rate|num(2) }}: the prior year's balance, {{ sg(s_p.one) }}, falls below its screen and the last year's, {{ sg(s_c.one) }}, stays above.

{{ figure('IF-18-9-B') }}

### Part 4: Error or estimate

**Step 7. Say what evidence would settle it, and recommend.** The rates are the plan's applied to earlier stock: a sensitivity, not an established error. The outline is in the strong answer.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Proposed rate; current; time-driven; actual | ${{ new_rate|num(2) }}; ${{ current|num(2) }}; ${{ td_std|num(2) }}; ${{ actual|num(2) }} | 1, 2 |
| Revaluation at each year-end | {% for s in stock %}{{ sg(s.plan) }}{{ "; " if not loop.last else "" }}{% endfor %} | 4 |
| Screens, prior year and current | ${{ mat_p|money }}; ${{ mat_c|money }} | 5 |
| Rate with no indirect hours; at the two normal capacities | ${{ one_rate|num(2) }}; ${{ normal[0].rate|num(2) }}; ${{ normal[1].rate|num(2) }} | 6 |

{{ expected() }}

## What a strong answer says

- **The rate.** Normal capacity at the plan volume, with supervision and depreciation spread over it; a standard on actual cost would capitalize idle capacity.
- **The effect.** The balance effects exceed the screen and the income effects do not, at either end of the normal-capacity range; with no indirect hours the prior year's balance falls below it.
- **Materiality is more than the screen.** The nature of the item, its aggregate with other misstatements, the line items and periods it touches, and the tax effect the ledger cannot supply bear on it.
- **Evidence before correction.** Would the standards in use, the normal capacity of those years and the costs known when each set of statements was prepared have given a materially different inventory under Topic 330? Name the period costs and volumes, the variances' disposition, counts and item-level opening balances.
- **The recommendation.** A material prior-period error: revised statements, with inventories, retained earnings and income corrected and the correction disclosed. A change in estimate: the new standard from now on. An immaterial error: correct it in the next statements, with disclosure. The decision is the CFO's, and the shareholders hear which.

A weak answer calls the revaluation an error, or stops at the screen.

## Common mistakes and how to respond

- **A standard on actual cost.** *Symptom:* a revaluation of {{ sg(s_c.actual) }}. *Response:* ask whether idle capacity is part of what a unit costs.
- **Burden left out, or the wrong year's depreciation.** *Symptom:* a rate of {{ g.rate_nb|num(2) }} or {{ g.rate_dep|num(2) }}. *Response:* ask which year the plan covers and what burden is.
- **The closes left in.** *Symptom:* a screen of ${{ g.with_closes|money }}. *Response:* ask what the closes do to revenue and expense.
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
