# Requirement 4: Compute three costs for each family (Chapter 7)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 4 |
| Perspective | Managerial accounting |
| Tools | More than one tool |
| Time | About 180 minutes |
| Solution file | Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheets Costs, ItemCosts and RoutingHours (the Assumptions sheet holds every input); Chapter18-capstone-sql.zip: MakeBuy.sql, Q21 |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

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
- **Verify first.** The committed cost is $4,119,063.77 and the Item query returns 219 finished goods.

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

```
Committed cost         =CrewCost+SalariedCost+Depreciation1090
Practical hours        =AvailableHours*PracticalUsed
Time-driven rate       =CommittedCost/PracticalHours
```

**Check:** the crew $3,515,852.70 (64 employees), the salaried staff $299,544.44 and depreciation $303,666.63 make $4,119,063.77; over 103,066.6 practical hours that is $39.97 an hour, $34.11 of it the crew. **Watch for:** the rate on the available hours, $31.97: the products then carry less and the unused capacity more.

### Part 2: The item costs

**Step 3. Build the ItemCosts Table with Power Query.** Start from Item filtered to finished goods, add the family (the first seven characters of ItemCode), merge the routing's run and setup hours, the year's sales by item (**Transform > Group By**) and the year's completions by item (**Home > Merge Queries**), replace the nulls with zero (**Transform > Replace Values**) and load the result as a Table. **Check:** 219 rows, one for each finished good. **Watch for:** a missing year filter on the sales or the completions: revenue reads $82,927,040.29 and manufactured units 131,379.38 against 46,786.01, three years of sales against one year's costs.

**Step 4. Add the cost columns as Table formulas.** Material at the actual rate, the cost with the crew kept, and the three views:

```
Material         =[@StandardCost]-[@StandardConversionCost]
MaterialAtActual =IF([@Costed],[@Material]*(1+MaterialVarianceRate),"")
CostKept         =IF([@Costed],[@MaterialAtActual]+FORate*[@StandardLaborHoursPerUnit],"")
RoutingTime      =IF([@Costed],[@RunHours]+[@SetupHours]/[@Batch],"")
AbsorptionCost   =IF([@Costed],[@StandardCost]+[@VariancePerUnit],[@StandardCost])
TimeDrivenCost   =IF([@Costed],[@CostKept]+TDRate*[@RoutingTime],[@StandardCost])
```

Standard is the item's own StandardCost. **Check:** for FUR-TBL at the year's mix, price $566.31, standard $332.28, absorption $395.90, time-driven $357.64. **Watch for:** leaving setup out of the routing time: the time-driven cost falls to $352.63. Absorption takes the family's variance per unit from Requirement 1, per unit completed.

### Part 3: The unused capacity

**Step 5. Show the unused capacity and reconcile.** The products carry the routing time they used at the rate plus the Factory Overhead entries; the practical hours not used belong to the plant.

```
Products' conversion     =UsedHours*TDRate+FactoryOverhead
Unused capacity cost     =UnusedHours*TDRate
Setup difference         =(SetupHoursUsed-SetupHoursAssigned)*TDRate
```

**Check:** products' conversion $4,259,206.41, unused 29,243.7 hours at $1,168,726.42 (the crew's part $997,573.76), together $5,427,932.83, the inputs to `1090`. The item costs applied to the year's completions give $4,258,921.01, and the setup that the family-average batch leaves out, $285.41, closes the gap: a line of its own, not rounding. **Watch for:** a rate built on the committed cost plus the Factory Overhead entries, with those entries charged again per standard hour: the total misses by exactly $1,308,869.06.

![A mock of the reconciliation block of the Costs sheet, where the products and the unused capacity are tied to the inputs to 1090.](../figures/chapter-18-make-buy-or-reprice/IF-18-4-A.pdf)

### Part 4: The summary by family

**Step 6. Summarize at the year's mix and find the top fifth.** Weight each family's cost by the units sold (SUMPRODUCT on the Table), margin under each view, purchased products at standard in every view. The top fifth is the share of margin earned by the 41 largest of the 207 finished goods sold:

```
=LET(m,FILTER(ItemCosts[MarginStandard],ItemCosts[Units]>0),n,ROUND(ROWS(m)*0.2,0),SUM(LARGE(m,SEQUENCE(n)))/SUM(m))
```

**Check:** time-driven margins Furniture 38.23%, Lighting 41.23%, Textiles 45.96%; the top fifth earns 51.2% (standard), 50.6% (absorption) and 50.7% (time-driven); no item loses money. **Watch for:** a plain mean of the families' margins: Furniture reads 38.04%, not 38.23%.

### Part 5: Practical capacity and the Data Table

**Step 7. Vary the practical share.** Excel takes a Data Table's input cell only from the table's own sheet, so Costs!B14 reads the Assumptions share (`=PracticalShare`) and every cost formula reads B14 (the name PracticalUsed). Type the shares down a column, point the corner row at the rate, the unused cost and the example family's cost, select the block, choose **Data > What-If Analysis > Data Table**, and enter `$B$14` as the **Column input cell**.

**Check:** the rate falls from $42.63 to $35.52 and FUR-TBL's cost by $13.73, while the unused capacity rises by $524,504.42: the same committed cost, divided differently. **Watch for:** an input cell on another sheet, which Excel rejects.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Committed cost; time-driven rate; crew's part | $4,119,063.77; $39.97; $34.11 | 2 |
| Products' conversion; unused capacity cost | $4,259,206.41; $1,168,726.42 | 5 |
| Group margins, time-driven: Furniture; Lighting; Textiles | 38.23%; 41.23%; 45.96% | 6 |
| Top fifth of margin: standard; absorption; time-driven | 51.2%; 50.6%; 50.7% | 6 |

> **Instructor notes, Requirement 4:** committed cost 4,119,063.77 = hourly crew 3,515,852.70 (64 employees; gross 3,079,544.37, employer tax 235,585.02, benefits 200,723.31) + salaried staff 299,544.44 (3; gross 263,191.24) + depreciation 303,666.63; practical capacity 103,066.6 hours; rate 39.9651 an hour (crew 34.1124, supervision and equipment 5.8526); Factory Overhead 18.9931 per standard hour; material variance rate 1.059% of standard material completed. Products' conversion 4,259,206.41; unused capacity 29,243.7 hours, 1,168,726.42 (crew 997,573.76); total 5,427,932.83 = the inputs to 1090. The item costs themselves, applied to the year's completions, give 4,258,921.01: setup spread over each family's average batch assigns 4,902.97 hours where the work orders ran 4,910.11, and the difference at 39.9651 an hour, 285.41, is a setup-allocation line of its own in the reconciliation (4,258,921.01 + 285.41 + 1,168,726.42 = 5,427,932.83), not rounding. Per unit at the 2026 mix (price / standard / absorption, the case's proxy of standard plus the family's close variance per unit completed / time-driven / time-driven margin): FUR-BKC 592.33 / 359.14 / 411.47 / 380.16 / 35.8%; FUR-BNH 608.92 / 378.70 / 441.18 / 399.01 / 34.5%; FUR-CON 622.40 / 336.49 / 391.97 / 356.34 / 42.7%; FUR-CTB 562.33 / 324.10 / 377.37 / 348.59 / 38.0%; FUR-DSK 652.99 / 363.51 / 412.74 / 385.34 / 41.0%; FUR-NGT 489.36 / 285.97 / 338.29 / 308.67 / 36.9%; FUR-SDB 550.02 / 310.77 / 373.00 / 338.07 / 38.5%; FUR-TBL 566.31 / 332.28 / 395.90 / 357.64 / 36.8%; LGT-CHD 313.29 / 182.68 / 205.79 / 197.27 / 37.0%; LGT-FLR 246.41 / 128.35 / 150.10 / 145.67 / 40.9%; LGT-PND 389.96 / 210.83 / 244.81 / 231.18 / 40.7%; LGT-SCN 326.73 / 169.92 / 204.03 / 188.24 / 42.4%; LGT-TBL 290.31 / 146.93 / 171.17 / 163.79 / 43.6%; TXT-CRT 434.82 / 230.04 / 259.49 / 251.98 / 42.0%; TXT-PIL 366.13 / 158.86 / 193.42 / 180.09 / 50.8%; TXT-THR 580.99 / 277.64 / 326.55 / 305.55 / 47.4%. Group time-driven margins: Furniture 38.23%, Lighting 41.23%, Textiles 45.96%. Time-driven sits between standard and absorption for every family: the products cost more than their standards say (the standards miss the rate increase, supervision, and depreciation; 1,008,586.26 in total) but less than the absorption proxy says (it charges them the year's closed variance, idle capacity included; the 1,069,728.92 between the time-driven and proxy margins is not the measured cost of unused capacity, 1,168,726.42), nearer standard for Furniture and nearer absorption for Lighting and Textiles. Top fifth of the 207 finished goods sold (41 items) earns 51.2% of margin at standard, 50.6% under absorption, 50.7% time-driven; no item loses money under any view (lowest under absorption LGT-SCN-0011, 12.6%). Data Table at 75 / 80 / 85 / 90%: rate 42.63 / 39.97 / 37.61 / 35.52; unused capacity 972,037 / 1,168,726 / 1,342,276 / 1,496,542; FUR-TBL 362.79 / 357.64 / 353.10 / 349.06. The choice of practical capacity divides the same committed cost between the products and the unused capacity: FUR-TBL's cost falls 13.73 across the table while the unused capacity rises by 524,504, and the total does not change; at 75%, LGT-FLR also falls below the floor.

## What a strong answer says

- **Three views, three questions.** Time-driven cost lies between standard and absorption for every family. The standards miss $1,008,586.26 of cost (the rate increase, supervision and depreciation); the absorption proxy charges them the year's closed variance, idle capacity included. The $1,069,728.92 between the time-driven and proxy margins is not the measured cost of unused capacity, $1,168,726.42, because the proxy's populations (closes, completions, sales) differ. It sits nearer standard for Furniture and nearer absorption for Lighting, Textiles.
- **Unused capacity is the plant's.** Products plus unused capacity equal the inputs, with the setup difference shown.
- **The Data Table.** The choice of practical capacity moves cost between the products and the unused capacity and leaves the total alone.

A weak answer reports three costs without the reconciliation, or hides assumptions inside formulas. The top fifth earns about half the margin under every view.

## Common mistakes and how to respond

- **The rate on available hours.** *Symptom:* $31.97 an hour. *Response:* ask which capacity the assumptions table names.
- **Overhead counted twice.** *Symptom:* a reconciliation off by $1,308,869.06. *Response:* ask what the difference equals.
- **Setup left out.** *Symptom:* FUR-TBL at $352.63. *Response:* ask what a changeover costs.
- **No year filter.** *Symptom:* revenue of $82,927,040.29. *Response:* ask which year the costs describe.
- **A typed constant.** *Symptom:* the Data Table does not move the costs. *Response:* ask where the share lives.
- **A plain mean of margins.** *Symptom:* 38.04%. *Response:* ask what weights a group's margin.

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
