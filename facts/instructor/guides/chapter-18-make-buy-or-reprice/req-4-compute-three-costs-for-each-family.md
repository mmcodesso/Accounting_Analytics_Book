---
note: ch18.r4
uses: [ch18.g4]
title: Compute three costs for each family (Chapter 7)
kind: requirement
number: '4'
unit: '18'
perspective: managerial
tool: mixed
minutes: 180
solution: "Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheets Costs, ItemCosts and RoutingHours (the Assumptions sheet holds every input); Chapter18-capstone-sql.zip: MakeBuy.sql, Q21"
figures:
  - id: IF-18-4-A
    kind: excel-mock
    purpose: The reconciliation block of the Costs sheet, where the products and the unused capacity are tied to the inputs to 1090.
    shows: "Rows from the routing time used to the difference, in two columns of label and value: the products' conversion, the unused capacity and its crew part, the products plus unused capacity beside the inputs to 1090 with a difference of zero, then the three lines of the setup-allocation bridge and its own zero difference."
    data: The Costs sheet of the model workbook, rows for the reconciliation.
---
{% set g = ch18_g4 %}
# Requirement 4: Compute three costs for each family (Chapter 7)

{{ header() }}

## Purpose and learning outcomes

Each cost is a formula over a handful of inputs that the decision makers will want to change, which is the job of a workbook: one Assumptions sheet, every cost a formula, every assumption a cell. One query (Q21) supplies the committed pay and Power Query the item data; everything else is Excel. The three views (standard, the case's proxy for actual absorption, and time-driven) answer three different questions, and time-driven costing reports the unused capacity as a cost of the plant. The analytics type is diagnostic.

Students can:

- compute the committed capacity cost and the rate per practical hour from the ledger's payroll and depreciation (Part 1);
- build each finished good's cost under the three views as formulas over the Assumptions sheet, in an Excel Table Power BI can load (Part 2);
- show the unused capacity as its own line and reconcile products plus unused capacity to the inputs to `1090` (Part 3);
- summarize by family and find the top fifth's share of margin (Part 4);
- use a Data Table to show how the practical share divides one committed cost (Part 5).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Reporting and Control (cost accounting) and Strategic Cost Management; IFAC IES 2 (b); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Make Buy Reprice.xlsx with the results of Requirements 1 to 3 (FamilyResults, the Cost Behavior and Activities sheets), CharlesRiver.xlsx for Power Query, and Excel for Microsoft 365 (the model uses XLOOKUP, LET and FILTER).
- **Data conditions.** Item holds a standard cost, its conversion part, standard hours and a routing; material is the standard cost less the conversion part. The design services are not finished goods and carry no standard cost. Setup is spread over each family's average batch, which does not quite match the setup the work orders ran.
- **Verify first.** The committed cost is ${{ committed|money }} and the Item query returns {{ g.n_fg|count }} finished goods.

## How to run it

Individual work, about 180 minutes: 20 for the assumptions and the pay class, 50 for the item data and cost columns, 25 for the reconciliation, 30 for the summary, 30 for the Data Table, 25 for documentation. Hold back the unused capacity line until products plus unused fail to tie to the inputs. **Collect** the workbook; the ItemCosts Table is what Requirement 5 loads.

## Step-by-step solution

### Part 1: The committed cost and the rate

**Step 1. Put every input in a named cell on Assumptions.** The quote, the practical share, the labor rate, the burden and the plan values sit in blue cells with defined names (PracticalShare, LaborRate), so no formula holds a typed constant.

**Step 2. Return the pay class and compute the rate.** Q21 gives the hourly crew and the salaried staff with their employer costs.

```sql
-- Requirement 4, Q21: the committed cost of the crew and supervision: payroll by pay class
-- Population: Manufacturing payroll registers of 2026; expected: the hourly crew, a few salaried
SELECT e.PayClass, COUNT(DISTINCT pr.EmployeeID) AS Employees,
    (SELECT COUNT(*)
     FROM Employee AS x
        INNER JOIN CostCenter AS y ON y.CostCenterID = x.CostCenterID
     WHERE y.CostCenterName = 'Manufacturing'
        AND x.PayClass = e.PayClass) AS EmployeesOnRecord,
    ROUND(SUM(pr.GrossPay), 2) AS GrossPay,
    ROUND(SUM(pr.EmployerPayrollTax), 2) AS EmployerTax,
    ROUND(SUM(pr.EmployerBenefits), 2) AS Benefits
FROM PayrollRegister AS pr
    INNER JOIN PayrollPeriod AS pp
        ON pp.PayrollPeriodID = pr.PayrollPeriodID
    INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = 2026
GROUP BY e.PayClass
ORDER BY e.PayClass;
```

Paste it as the Table PayClass; the Costs sheet then computes:

```jinja
Committed cost         {{ g.cells.committed }}
Practical hours        {{ g.cells.practical }}
Time-driven rate       {{ g.cells.rate }}
```

**Check:** the crew ${{ crew.total|money }} ({{ crew.n|count }} employees), the salaried staff ${{ sal.total|money }} and depreciation ${{ dep|money }} make ${{ committed|money }}; over {{ pract|num(1) }} practical hours that is ${{ td_rate|num(2) }} an hour, ${{ crew_rate|num(2) }} of it the crew. **Watch for:** the rate on the available hours, ${{ g.rate_avail|num(2) }}: the products then carry less and the unused capacity more.

### Part 2: The item costs

**Step 3. Build the ItemCosts Table with Power Query.** Start from Item filtered to finished goods, add the family (the first seven characters of ItemCode), merge the routing's run and setup hours, the year's sales by item (**Transform > Group By**) and the year's completions by item (**Home > Merge Queries**), replace an absent aggregate with zero (**Transform > Replace Values**) only where absence means no activity, as with an item that had no sales or no completions in the year, and load the result as a Table. A missing key, routing or assumption is flagged apart (a check column, or a row of the Tests), never turned into a zero. **Check:** {{ g.n_fg|count }} rows, one for each finished good. **Watch for:** a missing year filter on the sales or the completions: revenue reads ${{ g.rev_all|money }} and manufactured units {{ g.units_all|num(2) }} against {{ g.units_year|num(2) }}, three years of sales against one year's costs.

**Step 4. Add the cost columns as Table formulas.** Material at the actual rate, the cost with the crew kept, and the three views:

```jinja
Material         {{ g.cols.Material }}
MaterialAtActual {{ g.cols.MaterialAtActual }}
CostKept         {{ g.cols.CostKept }}
RoutingTime      {{ g.cols.RoutingTime }}
AbsorptionCost   {{ g.cols.AbsorptionCost }}
TimeDrivenCost   {{ g.cols.TimeDrivenCost }}
```

Standard is the item's own StandardCost. **Check:** for {{ example }} at the year's mix, price ${{ g.ex.price|num(2) }}, standard ${{ g.ex.std|num(2) }}, absorption ${{ g.ex.absorp|num(2) }}, time-driven ${{ g.ex.td|num(2) }}. **Watch for:** leaving setup out of the routing time: the time-driven cost falls to ${{ g.td_no_setup|num(2) }}. Absorption takes the family's variance per unit from Requirement 1, per unit completed.

### Part 3: The unused capacity

**Step 5. Show the unused capacity and reconcile.** The products carry the routing time they used at the rate plus the Factory Overhead entries; the practical hours not used belong to the plant.

```jinja
Products' conversion     {{ g.cells.products }}
Unused capacity cost     {{ g.cells.unused }}
Setup difference         {{ g.cells.setup_diff }}
```

**Check:** products' conversion ${{ conv|money }}, unused {{ unused_h|num(1) }} hours at ${{ unused|money }} (the crew's part ${{ unused_crew|money }}), together ${{ total|money }}, the inputs to `1090`. The item costs applied to the year's completions give ${{ item_conv|money }}, and the setup that the family-average batch leaves out, ${{ bridge|money }}, closes the gap: a line of its own, not rounding. **Watch for:** a rate built on the committed cost plus the Factory Overhead entries, with those entries charged again per standard hour: the total misses by exactly ${{ g.twice_gap|money }}.

{{ figure('IF-18-4-A') }}

### Part 4: The summary by family

**Step 6. Summarize at the year's mix and find the top fifth.** Weight each family's cost by the units sold (SUMPRODUCT on the Table), margin under each view, purchased products at standard in every view. The top fifth is the share of margin earned by the {{ top_n|count }} largest of the {{ n_items|count }} finished goods sold:

```jinja
{{ g.cells.top }}
```

**Check:** time-driven margins Furniture {{ groups[0].m_td|pct(2) }}, Lighting {{ groups[1].m_td|pct(2) }}, Textiles {{ groups[2].m_td|pct(2) }}; the top fifth earns {{ tops.std.share|pct(1) }} (standard), {{ tops.absorp.share|pct(1) }} (absorption) and {{ tops.td.share|pct(1) }} (time-driven); no item loses money. **Watch for:** a plain mean of the families' margins: Furniture reads {{ g.mean_td|pct(2) }}, not {{ g.group_td|pct(2) }}.

### Part 5: Practical capacity and the Data Table

**Step 7. Vary the practical share.** Excel takes a Data Table's input cell only from the table's own sheet, so Costs!B14 reads the Assumptions share (`=PracticalShare`) and every cost formula reads B14 (the name PracticalUsed). Type the shares down a column, point the corner row at the rate, the unused cost and the example family's cost, select the block, choose **Data > What-If Analysis > Data Table**, and enter `$B$14` as the **Column input cell**.

**Check:** the rate falls from ${{ table[0].rate|num(2) }} to ${{ table[3].rate|num(2) }} and {{ example }}'s cost by ${{ span|num(2) }}, while the unused capacity rises by ${{ unused_span|money }}: the same committed cost, divided differently. **Watch for:** an input cell on another sheet, which Excel rejects.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Committed cost; time-driven rate; crew's part | ${{ committed|money }}; ${{ td_rate|num(2) }}; ${{ crew_rate|num(2) }} | 2 |
| Products' conversion; unused capacity cost | ${{ conv|money }}; ${{ unused|money }} | 5 |
| Group margins, time-driven: Furniture; Lighting; Textiles | {{ groups[0].m_td|pct(2) }}; {{ groups[1].m_td|pct(2) }}; {{ groups[2].m_td|pct(2) }} | 6 |
| Top fifth of margin: standard; absorption; time-driven | {{ tops.std.share|pct(1) }}; {{ tops.absorp.share|pct(1) }}; {{ tops.td.share|pct(1) }} | 6 |

{{ expected() }}

## What a strong answer says

- **Three views, three questions.** Time-driven cost lies between standard and absorption for every family. The standards miss ${{ td_over|money }} of cost (the rate increase, supervision and depreciation); the absorption proxy charges them the year's closed variance, idle capacity included. The ${{ absorp_over|money }} between the time-driven and proxy margins is not the measured cost of unused capacity, ${{ unused|money }}, because the proxy's populations (closes, completions, sales) differ. It sits nearer standard for {{ near_std|join(', ') }} and nearer absorption for {{ near_absorp|join(', ') }}.
- **Unused capacity is the plant's.** Products plus unused capacity equal the inputs, with the setup difference shown.
- **The Data Table.** The choice of practical capacity moves cost between the products and the unused capacity and leaves the total alone.

A weak answer reports three costs without the reconciliation, or hides assumptions inside formulas. The top fifth earns about half the margin under every view.

## Common mistakes and how to respond

- **The rate on available hours.** *Symptom:* ${{ g.rate_avail|num(2) }} an hour. *Response:* ask which capacity the assumptions table names.
- **Overhead counted twice.** *Symptom:* a reconciliation off by ${{ g.twice_gap|money }}. *Response:* ask what the difference equals.
- **Setup left out.** *Symptom:* {{ example }} at ${{ g.td_no_setup|num(2) }}. *Response:* ask what a changeover costs.
- **No year filter.** *Symptom:* revenue of ${{ g.rev_all|money }}. *Response:* ask which year the costs describe.
- **A typed constant.** *Symptom:* the Data Table does not move the costs. *Response:* ask where the share lives.
- **A plain mean of margins.** *Symptom:* {{ g.mean_td|pct(2) }}. *Response:* ask what weights a group's margin.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Assumptions and committed cost | 15 | Named blue cells; crew, staff, depreciation; rate per practical hour | Typed constants |
| Three costs for each item | 30 | Formulas over the Assumptions sheet; a Table; setup over the average batch | Costs for families only, or values |
| Unused capacity and reconciliation | 20 | Its own line; products plus unused equal the inputs; the setup bridge | Reconciliation with a plug |
| Summary and top fifth | 15 | Weighted by units; three margins; the top fifth's share | Unweighted means |
| Data Table and explanation | 15 | Input cell on the sheet; the explanation of the split | A table without the explanation |
| Documentation | 5 | Sources, assumptions, date on the Documentation sheet | Missing |

## Extensions and discussion questions

- Find the practical share at which each family crosses the margin floor of Requirement 8.
- Discuss: which of the three costs would you quote to a customer, and why not the others?
- Discuss: what does it mean for a cost system that the unused capacity is not a product's cost?
