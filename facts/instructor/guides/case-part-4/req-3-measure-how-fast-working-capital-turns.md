---
note: case4.r3
uses: [case4.g3]
title: Measure how fast working capital turns (Chapters 14 and 15; managerial accounting)
kind: requirement
number: '3'
unit: case4
perspective: managerial
tool: powerbi
minutes: 180
solution: "PartIV-case.zip: Charles River Cash Case.pbip, page Working Capital and its hidden tooltip page WC Tooltip, the field parameter table WC Measure, the display folders Working capital, Working capital (average balance) and Policy targets, and the Requirement 3 rows of the Checks tab"
figures:
  - id: IF-C4-3-A
    kind: pbi-mock
    purpose: The Working Capital page of the model answer, the exhibit with the measures at each quarter-end.
    shows: "Report view, page Working Capital. A slicer of the six measures with the cycle selected; a line chart of the chosen measure by quarter; a matrix with a row for each quarter-end and columns for DSO, DIO, materials and finished goods days with their targets, and DPO, the days of supply carrying icons; a table of year-end measures beside their average-balance versions."
    data: The Expected results quantities (the measures by quarter and the average-balance versions), read-only.
  - id: IF-C4-3-B
    kind: chart
    purpose: Which component moved the cycle, so students see that receivables and payables are flat beside inventory.
    shows: "A chart by quarter-end with three lines, DSO, DIO and DPO, and the cash conversion cycle as a fourth, heavier line. DIO and the cycle rise steeply; DSO and DPO stay nearly flat. A note marks the first quarter, where the opening entry's lines are in the balances."
    data: The Expected results quantities (DSO, DIO, DPO and the cycle at each quarter-end), read-only.
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = case4_g3 %}
{% set q0 = qs[0] %}
{% set q1 = qs[-1] %}
# Requirement 3: Measure how fast working capital turns (Chapters 14 and 15; managerial accounting)

{{ header() }}

## Purpose and learning outcomes

Balances say how much cash is tied up; days say how long it stays. The requirement writes four measures of days, each a quarter-end balance over its own flow for the twelve months before, with a guard for the months that do not exist. Its lessons are that every ratio needs a stated definition, that each balance needs its own flow, and that an opening entry can hide what 2024 shows. The analytics type is diagnostic, with a predictive edge in the targets.

Students can:

- write the four measures and the cycle with a guard that blanks incomplete windows (Steps 1 and 2);
- add days of supply for materials and finished goods and compare them with the policy targets (Step 3);
- build a field-parameter page with a tooltip and icons (Step 4);
- compare versions with and without the opening entry and on the average balance, and say which the committee should see (Step 5).

**Competencies practiced.** CPA Evolution BAR M9 (financial statement analysis and working capital) and Core S1 M4 (financial statement analysis and performance measures); IMA Reporting and Control (financial statement analysis) and Strategy, Planning, and Performance (performance management); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Requirements 1 and 2 done, with Data Through. The model answer is in PartIV-case.zip: the page and tooltip above.
- **From earlier work.** Tutorial 15.3's twelve-month guard, Exercise 15.3's field parameter, Tutorial 15.1's tooltip and Chapter 15's conditional formatting.
- **Data conditions.** Cost of goods sold includes freight-out and the variances, and the closes credit it; each policy target is one number for raw materials and one for packaging; every policy ends at the year-end of the current fiscal year; the Date table runs past Data Through.
- **Verify first.** The {{ g.n_checks }} Requirement 3 rows of the Checks tab agree.

## How to run it

Pairs, about 180 minutes: 40 for the measures, 25 for days of supply, 55 for the page, 40 for the comparison and discussion, 20 spare. Hold back the opening-entry question until the first quarter is on the chart. **Collect** the .pbix and a half page on which version to show.

## Step-by-step solution

The Checks tab proves every value; the icons, the tooltip and the parameter slicer are visible only in Desktop.

### Part 1: The measures

**Step 1. Write the window and the flows.** Choose **Modeling > New measure** for each. Every flow reads the twelve months that end on the last date in the filter context.

```dax jinja
{{ g.d_flows }}
```

**Check:** the guard is true only when twelve months exist and end by Data Through, so {{ g.first_label }} is the first quarter with a value. **Watch for:** a quarter's flow in place of the year's, which makes DSO {{ g.dso_quarter|num(1) }} against {{ q1.dso|num(1) }} in {{ g.label }}; revenue in place of billing, {{ g.dso_rev|num(1) }}, because receivables carry tax and freight; and a cost of goods sold that keeps the closes. Debits less credits reads {{ g.dio_q3|num(1) }} days of DIO in {{ g.q3_label }}, where a window holds an old close, and nothing at all in {{ g.label }}, where the window holds its own.

**Step 2. Write the days and the cycle.**

```dax jinja
{{ g.d_days }}
```

**Check:** from {{ q0.label }} to {{ q1.label }} DSO runs {{ q0.dso|num(1) }} to {{ q1.dso|num(1) }}, DIO {{ q0.dio|num(1) }} to {{ q1.dio|num(1) }}, DPO {{ q0.dpo|num(1) }} to {{ q1.dpo|num(1) }} and the cycle {{ q0.ccc|num(1) }} to {{ q1.ccc|num(1) }}. **Watch for:** one flow for every balance. Materials against cost of goods sold read {{ g.mat_cogs|num(1) }} days in {{ g.label }} where the right flow gives {{ q1.mat|num(1) }}, and payables against it read {{ g.dpo_cogs|num(1) }} against {{ q1.dpo|num(1) }}.

### Part 2: Days of supply

**Step 3. Compare with the targets.** Add the target measures and their ratios to the days of supply, then read raw materials at {{ raw }} days, packaging at {{ pack }}, and finished goods at {{ made[0] }} to {{ made[1] }} (manufactured) and {{ bought[0] }} to {{ bought[1] }} (purchased).

**Check:** materials stand at {{ q1.mat|num(1) }} days in {{ q1.label }}, against {{ q0.mat|num(1) }} in {{ q0.label }}, and finished goods at {{ q1.fg|num(1) }} against {{ q0.fg|num(1) }}. Every policy ends at the current year-end, so targets for the next year need approval.

### Part 3: The page

**Step 4. Build the page.**

a. Choose **Modeling > New parameter > Fields**, name it `WC Measure`, and add the six measures in order; keep the slicer.
b. Add a **Line chart** with YearQuarter on the **X-axis** and the parameter on the **Y-axis**, titled "{{ g.t_line }}".
c. Add a tooltip page: **Canvas settings** Type Tooltip, **Page information** **Tooltip** on, and a table of each balance beside its flow. In the line chart's **Format visual > General > Tooltips**, choose that page.
d. Add a **Matrix** titled "{{ g.t_matrix }}", with **Conditional formatting > Icons** (**Format style** **Rules**) on the days of supply: up from {{ g.icon_up|num(2) }} times the target, down at {{ g.icon_down|num(1) }} or below.

```dax jinja
{{ g.param }}
```

**Check:** the slicer, titled "{{ g.t_slicer }}", changes the line; hovering shows a balance and its flow. **Watch for:** a missing guard. {{ g.early_label }} then reads {{ g.early|num(1) }} days of DSO, with under a year of billing behind it, and {{ g.late_label }}, which lies after Data Through, reads {{ g.late|num(1) }} where the model answer is blank. Test 5 of Requirement 5 finds the second.

{{ figure('IF-C4-3-A') }}

### Part 4: The comparison

**Step 5. Test the opening entry and the average.** Add the measures that leave out the lines of {{ entry }} and the average-balance versions, and a **Table** titled "{{ g.t_average }}".

```dax jinja
{{ g.d_open }}
```

**Check:** without the opening line DSO runs {{ q0.dso_x|num(1) }} to {{ q1.dso_x|num(1) }} and DPO {{ q0.dpo_x|num(1) }} to {{ q1.dpo_x|num(1) }}. The cycle moves {{ g.d_ccc|num(1) }} days as recorded and {{ g.d_ccc_x|num(1) }} without the opening line; DIO moves {{ g.d_dio|num(1) }}, DSO {{ g.d_dso|num(1) }} and DPO {{ g.d_dpo|num(1) }}. The average-balance materials days are {{ avg[0].mat|num(1) }} in {{ d.F }} and {{ avg[-1].mat|num(1) }} in {{ d.C }}.

{{ figure('IF-C4-3-B') }}

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax jinja
{{ g.dax_check }}
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| DSO, DIO, DPO, cycle in {{ q1.label }} | {{ q1.dso|num(1) }}; {{ q1.dio|num(1) }}; {{ q1.dpo|num(1) }}; {{ q1.ccc|num(1) }} | 2 |
| Materials days; finished goods days | {{ q1.mat|num(1) }}; {{ q1.fg|num(1) }} | 3 |
| Cycle without the opening line, {{ q0.label }} and {{ q1.label }} | {{ q0.ccc_x|num(1) }}; {{ q1.ccc_x|num(1) }} | 5 |
| Average-balance DSO, DIO, materials, DPO, {{ d.C }} | {{ avg[-1].dso|num(1) }}; {{ avg[-1].dio|num(1) }}; {{ avg[-1].mat|num(1) }}; {{ avg[-1].dpo|num(1) }} | 5 |

{{ expected() }}

## What a strong answer says

- **Definitions.** Each flow named: billing with tax and freight, cost of goods sold without the closes, issues, shipments, supplier invoices.
- **Movement.** Receivables and payables barely move, and the cycle grows through inventory, materials above all, far beyond the targets; the apparent fall of DPO is the unsupported opening payables diluted by purchases.
- **Which version.** The quarter-end versions on full windows, without the opening lines where they distort; {{ d.F }} shows only its last quarter, and the average lags a fast build.

A weak answer reports the numbers without saying which flow each uses.

## Common mistakes and how to respond

- **A quarter's flow.** *Symptom:* DSO of {{ g.dso_quarter|num(1) }}. *Response:* ask how many quarters the balance is compared with.
- **Closes in the cost of goods sold.** *Symptom:* DIO of {{ g.dio_q3|num(1) }} or blank. *Response:* ask what a close does to the account.
- **One flow for every balance.** *Symptom:* materials of {{ g.mat_cogs|num(1) }} days. *Response:* ask what consumes materials.
- **No guard.** *Symptom:* {{ g.early|num(1) }} days in {{ g.early_label }}. *Response:* ask how much billing the window holds.
- **Average balance on the first year.** *Symptom:* materials days of {{ avg[0].mat|num(1) }} for a year-end of {{ q0.mat|num(1) }}. *Response:* ask what the beginning balance stands for.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Measures and guard | 30 | Four days and the cycle; own flows; guard blanks early and late quarters | Right values, no guard |
| Days of supply and targets | 15 | Both days of supply; targets compared | Days without targets |
| Page | 25 | Parameter, tooltip, matrix with icons, titled | Chart without tooltip or icons |
| Comparison and explanation | 30 | Both versions; component named; version chosen with reasons | Versions without the choice |

## Extensions and discussion questions

- Add finished goods at the target as a measure and say what it leaves out.
- Remove the guard from one measure, rerun Test 5 of Requirement 5 and report what it shows.
- Discuss: customers pay in about {{ customers|num(0) }} days by terms and suppliers are paid in about {{ suppliers|num(0) }}. What does it mean that both run beyond terms?
- Discuss: why is a day count a better measure for a committee than a balance?
