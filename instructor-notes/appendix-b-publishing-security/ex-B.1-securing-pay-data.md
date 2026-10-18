# Exercise B.1: Securing Pay Data

| | |
|---|---|
| Unit | Appendix B: Publishing, Securing, and Sharing Reports |
| Item | Exercise B.1 |
| Perspective | Managerial accounting |
| Tools | Power BI Desktop |
| Time | About 75 minutes |
| Solution file | AppendixB-exercises-pbi.zip: Appendix B Exercises - Solutions.pbip, page Ex B.1, the TMDL view tab Ex B.1, the role Cost Center Managers, and the measure Labor Cost |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

After Tutorial B.1 the controller asks whether department managers could see what individual employees are paid. LaborTimeEntry carries the cost of each line of labor time, and the Production Manager should see the plant's hours but not its pay. Row-level security cannot do this: it removes rows, and the manager needs the rows. Object-level security hides one column from the role, and the exercise's lesson is its price: every measure and visual that reads the column fails for the role. The analytics type is prescriptive: the point of requirement (5) is a recommendation.

Students can:

- build a table by job title that shows hours and cost, and say why some titles have cost and no hours (Requirement 1);
- script a change to a role in TMDL view without losing the role's rules (Requirement 2);
- view the report as a manager and as finance, and predict which visuals fail (Requirement 3);
- compare the durations of a page with and without a role (Requirement 4);
- explain why object-level security is the tool, and what to do about the failures (Requirement 5).

**Competencies practiced.** Appendix D maps this exercise to information security and data ethics in the CPA Evolution model curriculum (ISC M5, Core S1 M8 T7), to the IMA's cybersecurity and data privacy competency (securing data), to IFAC IES 2 (g) on governance, risk management and internal control and IES 4 (b) on ethical principles in handling data, and to AACSB A5 part 5.1 on technology integration.

## Before you assign

- **Files.** A copy of Charles River Reports after Tutorial B.1, saved with **File > Save as**. The folder Start of Tutorial B.2 in AppendixB-companion.zip holds that project. The model answer is page Ex B.1, the TMDL view tab Ex B.1 and the measure Labor Cost of AppendixB-exercises-pbi.zip.
- **Software.** Power BI Desktop with **TMDL view**. The exercise says to drag the role from the **Model** tab of the **Data** pane into a new script tab, and to choose **Preview** and then **Apply**.
- **Data conditions.** LaborTimeEntry has ExtendedLaborCost and is related to Employee, so the role's rule on Employee filters it. Fiscal 2026 lists 7 job titles: 3 with manufacturing hours and 4 whose time is all non-manufacturing, so their hours are blank and their cost is $382,650.93.
- **Verify first.** **Modeling > Manage roles** lists Cost Center Managers with rules on CostCenter, Employee, Item and Security. A student who skipped Tutorial B.1 Step 6 has no role to script.

## How to run it

Individually, about 75 minutes: 10 for Requirement (1), 20 for (2), 15 for (3), 10 for (4), 15 for (5), 5 spare. The exercise points students to the syntax on Microsoft's object-level security page. Show your own copy of the lines only after students have opened the script and seen `createOrReplace`. Collect the .pbix, the script, the test log with the comparison, and the note.

## Step-by-step solution

### Requirement (1): The measure and the page

**Step 1. Add the measure.**

a. Select the **Key Measures** table in the **Data** pane, and choose **Modeling > New measure**.
b. Enter the formula below.

```dax
Labor Cost = SUM ( LaborTimeEntry[ExtendedLaborCost] )
```

**Step 2. Build the page.**

a. Add a page named `Ex B.1` and a **Table** visual.
b. Put JobTitle, Manufacturing Hours and Labor Cost in it, sorted by Labor Cost.
c. Under **Filters on this visual**, filter Year to 2026, and title the visual "Hours and labor cost by job title, fiscal 2026".
d. Below it, add a **Card** of Labor Cost with the same year filter.

![A mock of the model answer's page Ex B.1 as the Finance role sees it, the table every student builds in requirement (1).](../figures/appendix-b-publishing-security/IF-AB-1-A.pdf)

**Check:** Seven rows and a card equal to their total. The first three are Assembler ($1,051,663.65, 37,199 hours), Machine Operator ($1,019,655.73, 35,285 hours), Quality Technician ($890,423.13, 28,753 hours); then four non-manufacturing titles with cost and blank hours, $3,344,393.44 in all. **Watch for:** the year filter. Without it the table adds all three fiscal years, $9,176,404.49. Blank hours are correct: Manufacturing Hours leaves out the NonManufacturing labor type, with KEEPFILTERS.

### Requirement (2): The column permission

**Step 3. Script the role and hide the column.**

a. In **TMDL view**, drag Cost Center Managers from the **Model** tab of the **Data** pane into a new script tab. The script opens with `createOrReplace` and holds the role with its four rules.
b. After the rules, add the three lines below, indented like the other `tablePermission` lines.
c. Choose **Preview**, read the change, and choose **Apply**.

```
tablePermission LaborTimeEntry
	columnPermission ExtendedLaborCost
		metadataPermission: none
```

**Check:** **Manage roles** still shows the rules on CostCenter, Employee, Item and Security, also after the file is saved and reopened. In DAX query view, this instructor check returns 1 for the permission and 3344393.44 for the cost (the grid ignores the format string), because DAX query view runs as the author, whom no role limits.

```dax
EVALUATE ROW ( "Labor Cost", CALCULATE ( [Labor Cost], 'Date'[Year] = 2026 ), "Columns set to none", COUNTROWS ( FILTER ( INFO.COLUMNPERMISSIONS (), [MetadataPermission] = 1 ) ) )
```

**Watch for:** three wrong versions.

- *A script written from scratch.* `createOrReplace` replaces the role. With only the column permission, the role keeps the pay column hidden and loses every row rule. The Sales Manager's Cost centers shown card then lists all ten cost centers and net income is $4,503,611.24, and the former employee of Tutorial B.1 sees every sale.
- *Preview without Apply.* The role is unchanged, and the Production Manager's table still shows the pay of 64 people, $2,961,742.51 by job title.
- *The table hidden in place of the column.* Every visual that reads LaborTimeEntry would fail, the Plant page's hours with them. It is the opposite of the requirement.

### Requirement (3): Viewing as the manager and as finance

**Step 4. View as the Production Manager.**

a. Choose **Modeling > View as**, select **Other user**, type `employee004@charlesriver.example`, select **Cost Center Managers**, and click **OK**.
b. Open the page Ex B.1, and then the Plant page. Record both.
c. Choose **Stop viewing**, and repeat with **Finance** selected in place of the role.

![A mock of the same page viewed as the Production Manager after the column permission is applied, so an instructor knows what a correct failure looks like.](../figures/appendix-b-publishing-security/IF-AB-1-B.pdf)

**Check:** as the Production Manager the table and the card of Labor Cost fail, the table as a whole with its hours column. The Plant page works, with 101,237 hours and 1.51 hours per standard hour, because no measure on it reads the cost. With Finance the table shows all seven titles, $3,344,393.44. **Watch for:** the wording of the error. The model answer's note records the engine's message, that the column cannot be found or may not be used in this expression. This guide has not verified the visual's wording in your build, so ask students to quote what they see. A student who selects the role without **Other user** sees an empty Plant page, because their own sign-in is not in the security table.

### Requirement (4): Performance analyzer

**Step 5. Compare the durations.**

a. Open the Budget page, choose **Optimize > Review > Performance analyzer**, and record the page's visuals.
b. Choose **Modeling > View as**, view as the Sales Manager, and record the same visuals again.
c. Compare the durations of the matrix, the tables and the card by name.

**Check:** durations can be longer under **View as**, because every query carries the role's filters, or shorter, because the role leaves fewer rows. Ask for two recordings of each, so the cache does not decide the comparison. **Watch for:** exact times or a required direction. Durations vary by machine and from run to run, so grade the comparison and not the milliseconds. The label for starting a recording is not verified here.

### Requirement (5): The note

**Step 6. Explain the choice.** Mark the note against the outline in "What a strong answer says".

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Job titles in the table: with hours; cost only | 7: 3; 4 | 2 |
| Assembler: Labor Cost; hours | $1,051,663.65; 37,199 | 2 |
| Machine Operator: Labor Cost; hours | $1,019,655.73; 35,285 | 2 |
| Quality Technician: Labor Cost; hours | $890,423.13; 28,753 | 2 |
| Labor Cost of the cost-only titles | $382,650.93 | 2 |
| Labor Cost, fiscal 2026; with no year filter | $3,344,393.44; $9,176,404.49 | 2 |
| Column permissions set to none: role Cost Center Managers, table LaborTimeEntry, column ExtendedLaborCost; row rules kept | 1; four | 3 |
| Production Manager without the permission: cost, share of the total | $2,961,742.51; 88.6% | 3 |
| The same, by person: lowest and highest of 64 | $38,719.83; $57,887.43 | 3 |
| Production Manager, Labor Cost table and card | an error | 4 |
| Production Manager, Plant page | 101,237 hours; 1.51 | 4 |
| Finance, Labor Cost | $3,344,393.44 | 4 |

## What a strong answer says

- **(2)** The script keeps the four row rules and adds one column permission, and it was applied.
- **(3)** The test log names the role, user and result of each view. The table and card fail for the manager; the hours and the Plant page work; finance sees all of it. The student names the cause: a visual that reads a hidden column cannot be built for the role.
- **(4)** A comparison of the same visuals over repeated recordings, with the difference observed and a reason (the role's filters travel with every query, and the fewer rows it leaves can make a query faster).
- **(5)** Row-level security removes rows, and the manager needs the plant's rows. Pay is a column, so object-level security is the tool, and it hides the column from the role as if it did not exist. The failures are not a bug: the controller keeps cost measures off the pages managers read, or puts them in a finance report on the same semantic model, and tests each role with **View as** before release. Neither security layer limits the people who can edit the model, so the list of editors is part of the control.

A strong answer ends with a recommendation. A weak one proposes a rule on Employee, which hides people and not pay.

## Common mistakes and how to respond

- **A script from scratch.** *Symptom:* the Sales Manager's card lists every cost center. *Response:* ask what `createOrReplace` does to a role it finds.
- **Preview only.** *Symptom:* the Production Manager's table shows $2,961,742.51. *Response:* ask what **Apply** does.
- **Role without a user.** *Symptom:* an empty Plant page and "I broke the report". *Response:* ask whose sign-in the rules read.
- **No year filter.** *Symptom:* $9,176,404.49 in the table. *Response:* ask which years the Date table holds.
- **Blank hours read as an error.** *Symptom:* a student fills the blanks. *Response:* ask which labor type the four titles carry.
- **Row-level security proposed.** *Symptom:* a note that filters Employee. *Response:* ask which rows the manager must keep.
- **A note that stops at the failure.** *Symptom:* "the visual breaks". *Response:* ask what the controller does on Monday.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 15 | Measure, page with the table and the card, year filter and all 7 titles | A table of three titles, no card, or all years |
| Requirement 2 | 25 | Script names the role, table and column, keeps the four row rules, and was applied | Permission added to a role that lost its rules, or not applied |
| Requirement 3 | 20 | The table, the card and the Plant page recorded for both roles and compared | One role, or the Plant page left out |
| Requirement 4 | 10 | The Budget page's visuals recorded without and with a role, and the durations compared | One recording |
| Requirement 5 | 30 | Rows against columns, the cost of the failure, a recommendation | One of the three |

The cause of the failure in (3) and repeated recordings in (4) are a plus.

## Extensions and discussion questions

- Add EmployeeName to the table before the script, view as the Production Manager, and say what the 64 names would have shown without the permission.
- Run Performance analyzer as Finance and as a manager, and say which role costs more and why.
- Discuss: should the pay column be in the model at all? What does leaving it out in Power Query give that a permission does not?
- Discuss: the role script is a reviewable change. How does Chapter 16's change control apply to it?
