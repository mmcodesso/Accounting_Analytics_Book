---
uses: [appB.g1]
title: Securing Pay Data
kind: exercise
number: B.1
unit: appB
perspective: managerial
tool: powerbi
minutes: 75
solution: "AppendixB-exercises-pbi.zip: Appendix B Exercises - Solutions.pbip, page Ex B.1, the TMDL view tab Ex B.1, the role Cost Center Managers, and the measure Labor Cost"
figures:
  - id: IF-AB-1-A
    kind: pbi-mock
    purpose: The model answer's page Ex B.1 as the Finance role sees it, the table every student builds in requirement (1).
    shows: "Report view, page Ex B.1. A table titled 'Hours and labor cost by job title, fiscal' with the year, with the columns JobTitle, Manufacturing Hours and Labor Cost, sorted by Labor Cost, largest first. Seven rows: Assembler, Machine Operator and Quality Technician with hours and cost, then four non-manufacturing job titles with a cost and an empty hours cell, and a total row. Under it the card of Labor Cost, and beside both the text box Model answer. Above the page, a bar names the role Finance."
    data: The Expected results quantities (hours and cost by job title for the current fiscal year), read-only.
  - id: IF-AB-1-B
    kind: pbi-mock
    purpose: The same page viewed as the Production Manager after the column permission is applied, so an instructor knows what a correct failure looks like.
    shows: "Report view, page Ex B.1, with the bar above the page naming the role Cost Center Managers and the user. The table and the card are replaced by an error message that says a field cannot be found or used; the rest of the page, a text box, is unchanged. A small inset shows the Plant page of the same view, with its two hours per standard hour cards and its direct hours by work center visible, and a note beside it says what a correct failure is."
    data: The Plant page values of the Production Manager (hours and hours per standard hour for the current fiscal year), read-only.
---
{% set x = appB_g1 %}
# Exercise B.1: Securing Pay Data

{{ header() }}

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
- **Data conditions.** LaborTimeEntry has ExtendedLaborCost and is related to Employee, so the role's rule on Employee filters it. Fiscal {{ x.y }} lists {{ x.n_titles }} job titles: {{ x.n_manuf }} with manufacturing hours and {{ x.n_other }} whose time is all non-manufacturing, so their hours are blank and their cost is ${{ x.other_cost|money }}.
- **Verify first.** **Modeling > Manage roles** lists Cost Center Managers with rules on CostCenter, Employee, Item and Security. A student who skipped Tutorial B.1 Step 6 has no role to script.

## How to run it

Individually, about 75 minutes: 10 for Requirement (1), 20 for (2), 15 for (3), 10 for (4), 15 for (5), 5 spare. The exercise points students to the syntax on Microsoft's object-level security page. Show your own copy of the lines only after students have opened the script and seen `createOrReplace`. Collect the .pbix, the script, the comparison and the note.

## Step-by-step solution

### Requirement (1): The measure and the page

**Step 1. Add the measure.**

a. Select the **Key Measures** table in the **Data** pane, and choose **Modeling > New measure**.
b. Enter the formula below.

```dax jinja
{{ x.m_cost }}
```

**Step 2. Build the page.**

a. Add a page named `Ex B.1` and a **Table** visual.
b. Put JobTitle, Manufacturing Hours and Labor Cost in it, sorted by Labor Cost.
c. Under **Filters on this visual**, filter Year to {{ x.y }}, and title the visual "{{ x.t_table }}".

{{ figure('IF-AB-1-A') }}

**Check:** {{ x.w_titles }} rows. The first three are {% for t in x.manuf %}{{ t.title }} (${{ t.cost|money }}, {{ t.hours|num(0) }} hours){{ ", " if not loop.last else "" }}{% endfor %}; then {{ x.w_other }} non-manufacturing titles with cost and blank hours, ${{ x.total|money }} in all. **Watch for:** the year filter. Without it the table adds all three fiscal years, ${{ x.all_years|money }}. Blank hours are correct: Manufacturing Hours leaves out the NonManufacturing labor type, with KEEPFILTERS.

### Requirement (2): The column permission

**Step 3. Script the role and hide the column.**

a. In **TMDL view**, drag Cost Center Managers from the **Model** tab of the **Data** pane into a new script tab. The script opens with `createOrReplace` and holds the role with its {{ x.w_rules }} rules.
b. After the rules, add the three lines below, indented like the other `tablePermission` lines.
c. Choose **Preview**, read the change, and choose **Apply**.

```jinja
{{ x.tmdl }}
```

**Check:** **Manage roles** still shows the rules on CostCenter, Employee, Item and Security. In DAX query view, this instructor check returns {{ x.n_ols }} for the permission and {{ x.total|round(2) }} for the cost (the grid ignores the format string), because DAX query view runs as the author, whom no role limits.

```dax jinja
EVALUATE ROW ( "Labor Cost", {{ x.dax_cost }}, "Columns set to none", {{ x.dax_ols }} )
```

**Watch for:** three wrong versions.

- *A script written from scratch.* `createOrReplace` replaces the role. With only the column permission, the role keeps the pay column hidden and loses every row rule. The Sales Manager's Cost centers shown card then lists all {{ x.w_centers }} cost centers and net income is ${{ x.company|money }}, and the former employee of Tutorial B.1 sees every sale.
- *Preview without Apply.* The role is unchanged, and the Production Manager's table still shows the pay of {{ x.n_people }} people, ${{ x.pm_cost|money }} by job title.
- *The table hidden in place of the column.* Every visual that reads LaborTimeEntry would fail, the Plant page's hours with them. It is the opposite of the requirement.

### Requirement (3): Viewing as the manager and as finance

**Step 4. View as the Production Manager.**

a. Choose **Modeling > View as**, select **Other user**, type `employee004@charlesriver.example`, select **Cost Center Managers**, and click **OK**.
b. Open the page Ex B.1, and then the Plant page. Record both.
c. Choose **Stop viewing**, and repeat with **Finance** selected in place of the role.

{{ figure('IF-AB-1-B') }}

**Check:** as the Production Manager the table and the card of Labor Cost fail, the table as a whole with its hours column. The Plant page works, with {{ x.p.hours|num(0) }} hours and {{ x.p.ratio|num(2) }} hours per standard hour, because no measure on it reads the cost. With Finance the table shows all {{ x.w_titles|lower }} titles, ${{ x.total|money }}. **Watch for:** the wording of the error. The model answer's note records the engine's message, that the column cannot be found or may not be used in this expression. This guide has not verified the visual's wording in your build, so ask students to quote what they see. A student who selects the role without **Other user** sees an empty Plant page, because their own sign-in is not in the security table.

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
| Job titles in the table: with hours; cost only | {{ x.n_titles }}: {{ x.n_manuf }}; {{ x.n_other }} | 2 |
{% for t in x.manuf %}
| {{ t.title }}: Labor Cost; hours | ${{ t.cost|money }}; {{ t.hours|num(0) }} | 2 |
{% endfor %}
| Labor Cost of the cost-only titles | ${{ x.other_cost|money }} | 2 |
| Labor Cost, fiscal {{ x.y }}; with no year filter | ${{ x.total|money }}; ${{ x.all_years|money }} | 2 |
| Column permissions set to none | {{ x.n_ols }} | 3 |
| Production Manager without the permission: cost, share of the total | ${{ x.pm_cost|money }}; {{ x.pm_share|pct(1) }} | 3 |
| The same, by person: lowest and highest of {{ x.n_people }} | ${{ x.person_low|money }}; ${{ x.person_high|money }} | 3 |
| Production Manager, Labor Cost table and card | an error | 4 |
| Production Manager, Plant page | {{ x.p.hours|num(0) }} hours; {{ x.p.ratio|num(2) }} | 4 |
| Finance, Labor Cost | ${{ x.total|money }} | 4 |

## What a strong answer says

- **(2)** The script keeps the {{ x.w_rules }} row rules and adds one column permission, and it was applied.
- **(3)** The table and card fail for the manager; the hours and the Plant page work; finance sees all of it. The student names the cause: a visual that reads a hidden column cannot be built for the role.
- **(4)** A comparison of the same visuals over repeated recordings, with the difference observed and a reason (the role's filters travel with every query, and the fewer rows it leaves can make a query faster).
- **(5)** Row-level security removes rows, and the manager needs the plant's rows. Pay is a column, so object-level security is the tool, and it hides the column from the role as if it did not exist. The failures are not a bug: the controller keeps cost measures off the pages managers read, or puts them in a finance report on the same semantic model, and tests each role with **View as** before release. Neither security layer limits the people who can edit the model, so the list of editors is part of the control.

A strong answer ends with a recommendation. A weak one proposes a rule on Employee, which hides people and not pay.

## Common mistakes and how to respond

- **A script from scratch.** *Symptom:* the Sales Manager's card lists every cost center. *Response:* ask what `createOrReplace` does to a role it finds.
- **Preview only.** *Symptom:* the Production Manager's table shows ${{ x.pm_cost|money }}. *Response:* ask what **Apply** does.
- **Role without a user.** *Symptom:* an empty Plant page and "I broke the report". *Response:* ask whose sign-in the rules read.
- **No year filter.** *Symptom:* ${{ x.all_years|money }} in the table. *Response:* ask which years the Date table holds.
- **Blank hours read as an error.** *Symptom:* a student fills the blanks. *Response:* ask which labor type the four titles carry.
- **Row-level security proposed.** *Symptom:* a note that filters Employee. *Response:* ask which rows the manager must keep.
- **A note that stops at the failure.** *Symptom:* "the visual breaks". *Response:* ask what the controller does on Monday.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 15 | Measure, page, year filter and all {{ x.n_titles }} titles | A table of three titles, or all years |
| Requirement 2 | 25 | Script keeps the rules, adds the permission, applied | Permission added to a role that lost its rules, or not applied |
| Requirement 3 | 20 | Both views recorded, with the cause of the failure | One view, or the failure without a cause |
| Requirement 4 | 10 | The same visuals compared over repeated recordings, the observed difference stated | One recording |
| Requirement 5 | 30 | Rows against columns, the cost of the failure, a recommendation | One of the three |

## Extensions and discussion questions

- Add EmployeeName to the table before the script, view as the Production Manager, and say what the {{ x.n_people }} names would have shown without the permission.
- Run Performance analyzer as Finance and as a manager, and say which role costs more and why.
- Discuss: should the pay column be in the model at all? What does leaving it out in Power Query give that a permission does not?
- Discuss: the role script is a reviewable change. How does Chapter 16's change control apply to it?
