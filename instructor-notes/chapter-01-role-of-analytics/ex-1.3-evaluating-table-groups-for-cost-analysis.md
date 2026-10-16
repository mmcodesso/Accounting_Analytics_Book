# Exercise 1.3: Evaluating Table Groups for Cost Analysis

| | |
|---|---|
| Unit | Chapter 1: The Role of Analytics in Accounting |
| Item | Exercise 1.3 |
| Perspective | Managerial accounting |
| Tools | Workbook browsing and written work |
| Time | About 60 minutes |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise separates two kinds of cost analysis that students tend to blur. Product cost analysis compares a standard with what production actually cost, and that data lives in the Manufacturing group. Departmental budget analysis compares a plan with what a department spent, and the plan lives in Organizational Planning while the spending lives in the ledger. Students also find that the plan tables hold only the plan, and that real production cost needs a second group. The type of analytics is descriptive, and the exercise prepares the diagnostic variance work of Part III.

By the end, students can:

- list the Manufacturing tables and the columns that carry standard cost, material usage, completions and variances (chapter outcome 4);
- name the Organizational Planning tables and columns for a departmental budget, and the GLEntry columns that supply the actual spending for the same cost center, account and period;
- explain which group suits product-level cost analysis and which suits departmental budget analysis, with the limit of each (chapter outcome 6);
- propose a question that needs Manufacturing together with Payroll and Time.

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and ISC M4 (use and management of data); IMA Data Literacy and Cost Accounting; IFAC IES 2 (b), management accounting, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.2.

## Before you assign

- Students need CharlesRiver.xlsx and Tutorial 1.1. Table 1.3 and Figure 1.4 help.
- The exercise relies on these conditions: the Manufacturing worksheets hold work orders, material issues, completions and closes, and the close holds the variance amounts; Item holds the standard cost and its components; Budget has one row for a cost center, an account and a month of a fiscal year, and no row without a cost center; BudgetLine holds the driver detail (item, quantity, unit amount, category) and has some rows with no cost center; the CostCenter worksheet has 10 cost centers; LaborTimeEntry names the work order that the time was spent on.
- Do not ask students to decide whether Budget and BudgetLine overlap or can be added. Exercise 2.4 asks that. Here they list the columns.
- Check first that you can read the grain of Budget and BudgetLine on the worksheets, so you can answer questions about one row.

## How to run it

Individual work. For about 60 minutes: 15 minutes on the Manufacturing worksheets (requirement 1), 15 on the planning worksheets and the ledger columns (requirement 2), 15 on the comparison (requirement 3) and 15 on the cross-group question (requirement 4).

**Hints.** After ten minutes, if requirement 2 is stuck, ask what the budget does not have that a manager needs next. If requirement 3 comes back as a verdict with no reasons, ask for one sentence on the data each group lacks. Hold back the name of LaborTimeEntry until a student has tried requirement 4.

**Collect** the written assessment, with the table of tables and columns attached.

## Step-by-step solution

### Requirement (1): Find the cost data in Manufacturing

**Step 1. Open the manufacturing worksheets and list the columns that carry cost.**

a. Click **WorkOrder**, **BillOfMaterial**, **MaterialIssue**, **ProductionCompletion** and **WorkOrderClose**.
b. Add **Item** from Master Data, and the line worksheets that hold the amounts (BillOfMaterialLine, MaterialIssueLine, ProductionCompletionLine).
c. For each, read row 1 and note the columns that carry a quantity, a cost or a variance.

| Table | Cost columns | What they show |
|---|---|---|
| Item | StandardCost, StandardLaborHoursPerUnit, StandardDirectLaborCost, StandardVariableOverheadCost, StandardFixedOverheadCost, StandardConversionCost | The standard cost per unit and its parts |
| WorkOrder | PlannedQuantity, ReleasedDate, DueDate, CompletedDate, ClosedDate, Status | What was planned and when it was finished |
| BillOfMaterial and BillOfMaterialLine | ComponentItemID, QuantityPerUnit, ScrapFactorPct | The planned materials and the planned scrap |
| MaterialIssue and MaterialIssueLine | QuantityIssued, ExtendedStandardCost | Materials issued to a work order, valued at standard cost |
| ProductionCompletion and line | QuantityCompleted, ExtendedStandardMaterialCost, ExtendedStandardConversionCost, ExtendedStandardTotalCost | Output and its standard cost |
| WorkOrderClose | MaterialVarianceAmount, DirectLaborVarianceAmount, OverheadVarianceAmount, ConversionVarianceAmount, TotalVarianceAmount | The difference between actual and standard cost when the work order closes |

**Check:** the answer names standard cost (Item, the completion lines and the issues) and the variance (WorkOrderClose), and notes that the planned scrap is a planned amount only. **Watch for:** a student who copies every column of every sheet. Ask which ones a cost analyst would add up or compare.

### Requirement (2): Find the budget and the actuals

**Step 2. Read the grain of the planning worksheets.**

a. Click **CostCenter**, then **Budget**, then **BudgetLine**.
b. Read one row of each and say what it represents.

| Table | Columns | One row is |
|---|---|---|
| CostCenter | CostCenterID, CostCenterName, ParentCostCenterID, ManagerID | A department: Executive, Sales, Warehouse, Manufacturing, Purchasing, Administration, Customer Service, Research and Development, Marketing, and Design Services |
| Budget | FiscalYear, Month, CostCenterID, AccountID, BudgetAmount | The plan for one cost center, one account and one month |
| BudgetLine | FiscalYear, Month, AccountID, CostCenterID, ItemID, WarehouseID, Quantity, UnitAmount, BudgetAmount, BudgetCategory, DriverType | A planned amount with its drivers: an item, a quantity and a unit amount |

**Check:** Budget covers fiscal years 2024 through 2027, so it also holds the plan for the year after the last year of actuals (2027). **Watch for:** students who say Budget holds the actual amounts. It has BudgetAmount only.

**Step 3. Name the GLEntry columns that give the actuals.** Open **GLEntry**. The actual spending for a budget row is the sum of debits less credits of the rows with the same CostCenterID and AccountID in the same fiscal year and period. The columns are CostCenterID, AccountID, FiscalYear, FiscalPeriod (or PostingDate), Debit and Credit.

![How a budget row lines up with the ledger rows that give its actual spending.](../figures/chapter-01-role-of-analytics/IF-01-3-A.pdf)

**Check:** the three join columns are named, and the amount is debits less credits. **Watch for:** blank cost centers. 1,005 of the 142,869 expense rows in GLEntry, 0.7%, have no CostCenterID, and 1,625 rows of BudgetLine have none, so a comparison by department leaves a small remainder. Mention it, but do not let it derail the exercise.

### Requirement (3): Decide which group suits which analysis

**Step 4. Write the comparison in three to five sentences.** A model outline:

1. *Product cost.* Manufacturing is better suited: it holds the standard cost of each item and of each work order's output, the materials issued, and the variance when the work order closes.
2. *Its limit.* It does not hold the hours and pay of the people who did the work. Time and pay are in Payroll and Time, so actual conversion cost needs both groups.
3. *Departmental budget.* Organizational Planning is better suited for the plan, with the cost center as the organizing key.
4. *Its limit.* The planning tables hold only the plan, so actual spending has to come from GLEntry by cost center, account and period.
5. *Verdict.* Each group answers its own question with the help of one more group, so neither group is enough alone.

**Check:** two matches, each with a reason and a limit. **Watch for:** an answer that picks Manufacturing for both because it "has costs".

### Requirement (4): Name a question across Manufacturing and Payroll and Time

**Step 5. Propose a question and the tables.** Accept either of these, or a similar one:

- *Did direct labor hours on work orders stay within the standard hours of the units completed?* Manufacturing: ProductionCompletionLine (QuantityCompleted), Item (StandardLaborHoursPerUnit), WorkOrder. Payroll and Time: LaborTimeEntry (WorkOrderID, WorkOrderOperationID, LaborType, RegularHours, OvertimeHours, ExtendedLaborCost).
- *Did overtime pay rise in the months when output rose?* Manufacturing: ProductionCompletion (CompletionDate), ProductionCompletionLine. Payroll and Time: PayrollRegister (PayrollPeriodID, CostCenterID, GrossPay) and LaborTimeEntry.

**Check:** the tables come from both groups, and the answer says what each contributes: the standard or the output from Manufacturing, the hours or the pay from Payroll and Time.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Rows in WorkOrder, WorkOrderClose | 13,668; 12,998 | Step 1 |
| Rows in MaterialIssue, ProductionCompletion | 19,240; 17,352 | Step 1 |
| Cost centers | 10 | Step 2 |
| Rows in Budget, BudgetLine | 1,385; 31,426 | Step 2 |
| Rows in LaborTimeEntry, PayrollRegister | 68,859; 8,197 | Step 5 |
| Expense rows of GLEntry; those with no cost center | 142,869; 1,005 (0.7%) | Step 3 |
| Budget rows with no cost center | 0 | Step 2 |

## What a strong answer says

- **Requirement (1).** The answer groups the cost columns by purpose (standard, planned, variance) and puts the variance in WorkOrderClose.
- **Requirement (2).** It says that Budget and BudgetLine are plan tables, and it names the GLEntry columns for the actuals.
- **Requirement (3).** It gives each group a reason and a limit, and it does not claim that either group is complete.
- **Requirement (4).** It names a question that really needs both groups, with the role of each.

A weak answer lists every table, says the budget tables hold actual spending, or recommends one group without reasons.

## Common mistakes and how to respond

- **The budget as actuals.** *Symptom:* "compare Budget with BudgetAmount". *Response:* ask where the actual amount is stored.
- **Standard cost taken as actual cost.** *Symptom:* Item.StandardCost alone for product cost. *Response:* ask where the difference between standard and actual is.
- **No join columns for the actuals.** *Symptom:* "GLEntry has the actuals" with no columns. *Response:* ask which three columns would match a budget row.
- **A cost center taken from the wrong table.** *Symptom:* Employee cited as the source of the department. *Response:* point to CostCenterID on GLEntry.
- **A verdict with no reason.** *Response:* ask what data the other group lacks.
- **A question needing one group only.** *Symptom:* "How many work orders closed last month?" *Response:* ask what the second group would add.
- **Every column listed.** *Response:* ask which ones the analyst would add up or compare.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: Manufacturing tables and cost columns | 25 | Tables and columns grouped as standard, planned and variance | Tables without columns, or all columns |
| Requirement 2: planning tables and the GLEntry columns | 25 | The grain of each plan table, and the join columns for actuals | Plan tables only, or no ledger columns |
| Requirement 3: the comparison | 30 | A match for each analysis, with a reason and a limit | A verdict without reasons |
| Requirement 4: the cross-group question | 20 | A question that needs both groups, with the role of each | A question for one group, or no roles |

## Extensions and discussion questions

- Name a column in each of two groups that shows the hours planned for a work center. PlannedLoadHours appears in WorkOrderOperation (Manufacturing) and in RoughCutCapacityPlan (Demand Planning and MRP).
- Open CostCenter, find the manager of the Manufacturing cost center, and look that person up in Employee. What is their job title?
- Discuss: from fiscal 2024 to fiscal 2026, the total variance on closed work orders rose by 75% while the units completed changed by -2.1%. Which tables, from which groups, could explain that? (Chapters 9 to 12 take this question up.)
- Discuss: which of the two analyses would a department manager ask for, and which would a plant manager ask for?
