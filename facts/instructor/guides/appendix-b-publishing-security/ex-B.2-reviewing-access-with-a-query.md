---
note: appendix_b.ex2
uses: [appB.g2]
title: Reviewing Access with a Query
kind: exercise
number: B.2
unit: appB
perspective: auditing
tool: powerbi
minutes: 75
solution: "AppendixB-exercises-pbi.zip: Appendix B Exercises - Solutions.pbip, page Ex B.2, the DAX query tab Ex B.2, and the query AccessEmployees"
figures:
  - id: IF-AB-2-A
    kind: pbi-mock
    purpose: The result of query (4), the review a student runs every quarter, so an instructor sees what a clean review looks like.
    shows: "DAX query view on the model answer, the tab Ex B.2 selected, the third query selected in the editor with the lines it leaves out marked, and a result grid under it with nine rows, one for each user of the security table. Columns: the user name, CostCenterID, EmployeeID, EmployeeName, JobTitle, EmploymentStatus, TerminationDate, OwnCostCenterID and Flag. The grid is wider than the window, so it is drawn twice, before and after scrolling right. TerminationDate and Flag are empty in every row, and CostCenterID equals OwnCostCenterID in every row."
    data: The security table of Guided Tutorial B.1 and the employee records (the Expected results quantities), read-only.
  - id: IF-AB-2-B
    kind: pbi-mock
    purpose: The page Ex B.2 viewed as the Sales Manager, the leak that requirement (5) asks students to find.
    shows: "Report view, page Ex B.2, with the bar above the page naming the role Cost Center Managers and the Sales Manager. A table titled 'AccessEmployees, as any role member sees it' lists EmployeeName, JobTitle, EmploymentStatus and TerminationDate for every employee, with the terminated employees' dates filled in, and a scroll bar showing that the list is long (the picture shows the top of the list). A text box beside it reads 'Model answer'."
    data: The Employee table (all employees, with status and termination date), read-only.
---
{% set x = appB_g2 %}
# Exercise B.2: Reviewing Access with a Query

{{ header() }}

## Purpose and learning outcomes

Tutorial B.1 Step 4 checked the security table by eye. Internal audit wants the check as a query it can run each quarter, so that every change to the table is tested against the employee records. The exercise is a small continuous-monitoring test in the style of Chapter 16: a list of authorizations compared with the master data, with exceptions flagged. The analytics type is diagnostic, and the last requirement is prescriptive: what to do about the table that the review itself added to the file.

Students can:

- import a table that stays unrelated on purpose (Requirement 1);
- find the cost centers a security table leaves out, and the users it maps twice (Requirements 2 and 3);
- match each user to an employee with `LOOKUPVALUE` and flag three failures (Requirement 4);
- show what a role leaves visible in a table that no relationship reaches (Requirement 5);
- report what the review found, how often to run it, and what to do before publishing (Requirement 6).

**Competencies practiced.** Appendix D maps this exercise to tests of internal controls, logical access and change management (CPA Evolution ISC M2) and information security (ISC M5); to the IMA competencies for securing data and for internal control; to IFAC IES 2 (i) on judging the adequacy of information and communications technology controls and IES 2 (g) on governance, risk management and internal control; and to AACSB A5 part 5.1.

## Before you assign

- **Files.** The copy of Charles River Reports after Tutorial B.1, with its roles and its Security table. The model answer is the DAX query tab Ex B.2, the page Ex B.2 and the query AccessEmployees of AppendixB-exercises-pbi.zip.
- **Data conditions.** Every employee has a distinct Email, so `LOOKUPVALUE` on Email finds one row. Of the {{ x.n_employees }} employees, {{ x.n_terminated }} are terminated, with a TerminationDate. Security is hidden but can be queried in DAX query view, and it has no relationship to any table.
- **Verify first.** Security holds {{ users }} rows in the order of the tutorial, and Model view shows no relationship line to AccessEmployees. A relationship to CostCenter or Employee would let the role's rules filter the table, and Requirement (5) would show a false pass.

## How to run it

Pairs, about 75 minutes: 5 for Requirement (1), 10 for (2), 5 for (3), 20 for (4), 15 for (5), 15 for (6), 5 spare. Hold back the flag's logic until the pair has the three-layer shape. Hint 1, after 10 minutes on (2): "Security is not related to CostCenter. Which function asks whether any row of Security has this cost center?" Hint 2, for (4): "Build it in three layers: the matched EmployeeID, the looked-up columns, the flag." Collect the query tab, the page and the note.

## Step-by-step solution

### Requirement (1): The unrelated table

**Step 1. Import the employees.**

a. Choose **Home > Get data > Excel workbook**, select **T74_Employee**, and click **Transform Data**.
b. Rename the query `AccessEmployees`, and use **Choose Columns** to keep EmployeeID, EmployeeName, Email, JobTitle, CostCenterID, EmploymentStatus and TerminationDate.
c. Type TerminationDate as a date, and choose **Home > Close & Apply**.
d. Open **Model view** and confirm that no relationship line touches AccessEmployees.

**Check:** {{ x.n_employees }} rows in **Table view**, and an isolated table in Model view. **Watch for:** a relationship the file created on its own. Delete it.

### Requirement (2): The cost center with no row

**Step 2. List the cost centers that Security leaves out.**

a. In DAX query view, add a query tab and rename it `Ex B.2`.
b. Enter the first query of the model answer, comment line included.

```dax jinja
{{ x.q2 }}
```

c. Choose **Run**.

**Check:** one row, {{ x.center_id }}, {{ x.center }}. Its manager of record is {{ x.manager.name }}, {{ an }} {{ x.manager.title|lower }}, and it has {{ x.in_unmapped }} employees. **Watch for:** `RELATEDTABLE`, which needs a relationship that Security does not have. An `EXCEPT` of the two lists of IDs also finds it and is accepted.

### Requirement (3): Users mapped twice

**Step 3. List the users with more than one cost center.**

a. Add the second query below the first, and run it.

```dax jinja
{{ x.q3 }}
```

**Check:** no rows, because the table has {{ users }} users and {{ ccs }} cost centers. **Watch for:** an empty result that is empty because the query is wrong. In a copy of the Security table, add a second row for one user with another cost center, and the query lists that user with 2. A row that repeats an existing mapping exactly is not listed, because the query counts each user's distinct cost centers, not rows.

### Requirement (4): The matching and the flag

**Step 4. Build the review in three layers.**

a. Add the third query below the second.
b. Read it from the inside out. Users lists each user once, with the cost centers mapped to the user and the EmployeeID whose Email matches, Matched looks up five more columns by that ID, and the last layer adds the flag, which marks a user if any of those cost centers is not the employee's own.
c. Choose **Run**.

```dax jinja
{{ x.q4 }}
```

{{ figure('IF-AB-2-A') }}

**Check:** {{ users }} rows, the Flag blank in every row. The matched employees are{% for i, t in matches %} {{ i }} ({{ t }}){{ "," if not loop.last else "." }}{% endfor %} Each is in the cost center the table gives. **Watch for:** a flag that passes here and fails elsewhere. Every user is clean on this data, so a flag with a missing or misordered test also reads blank. Test it with three rows added to a copy of Security:

| Row added | Expected flag | Why |
|---|---|---|
{% for t in x.tests %}
| `{{ t.upn }}` on cost center {{ t.cc }} | {{ t.flag }} | {{ "no Email matches" if t.emp is none else t.emp.name ~ ", " ~ t.emp.title|lower ~ (", terminated " ~ t.emp.terminated if t.emp.terminated else ", own cost center " ~ t.emp.cc) }} |
{% endfor %}

The order of the SWITCH matters: with the Terminated test first, the row that matches no employee reads {{ x.wrong_order }}, because a blank status is not "Active". A security table typed with the cost centers in sequence is caught the same way: {{ x.seq_flagged|length }} users read Mapped to another cost center, and Requirement (2) names {{ x.seq_unmapped[0] }} as the cost center left out.

### Requirement (5): What a manager can see

**Step 5. View as the Sales Manager.**

a. Add a page named `Ex B.2` with a **Table** visual of EmployeeName, JobTitle, EmploymentStatus and TerminationDate from AccessEmployees, titled "{{ x.title_table }}".
b. Choose **Modeling > View as**, select **Other user**, type `employee006@charlesriver.example`, select **Cost Center Managers**, and click **OK**.
c. Read the table, then choose **Stop viewing**.

{{ figure('IF-AB-2-B') }}

**Check:** all {{ x.n_employees }} employees appear, with their termination dates, while Employee itself shows only the {{ x.s_employees }} of the Sales cost center. No rule filters a table that no relationship reaches. In **Manage roles**, a rule of `FALSE ()` on AccessEmployees for Cost Center Managers empties it for the role, though its name and columns stay visible, which object-level security would hide too. Keeping the table out of the published file removes it. **Watch for:** the review run under a manager's role. It sees one cost center and one row of Security, so Requirement (2) returns nothing and the gap disappears. Run the review as the file's author.

### Requirement (6): The note

**Step 6. Report.** Mark the note against "What a strong answer says".

**Instructor check.** In DAX query view, run this and compare it with the Expected results.

```dax jinja
EVALUATE ROW ( "Unmapped", {{ x.dax_unmapped }}, "Users matched", {{ x.dax_matched }}, "AccessEmployees rows", {{ x.dax_rows }} )
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Cost center with no row in the security table | {{ x.center_id }} {{ x.center }} | 2 |
| Its manager of record; its employees | {{ x.manager.name }}, {{ x.manager.title }}; {{ x.in_unmapped }} | 2 |
| Users mapped to more than one cost center | none | 3 |
| Users in the table; matched to an active employee | {{ x.n_users }}; {{ x.n_users }} | 4 |
| Users flagged | 0 | 4 |
{% for t in x.tests %}
| Test row `{{ t.upn }}` | {{ t.flag }} | 4 |
{% endfor %}
| Typed in sequence: users flagged; cost center left out | {{ x.seq_flagged|length }}; {{ x.seq_unmapped[0] }} | 4 |
| AccessEmployees rows a manager sees; terminated among them | {{ x.n_employees }}; {{ x.n_terminated }} | 5 |
| Employee rows the Sales Manager sees | {{ x.s_employees }} | 5 |

{{ expected() }}

## What a strong answer says

- **(2) to (4)** The review found one cost center without a user, {{ x.center }}, which agrees with Tutorial B.1, where no department manager sees it until the controller names its manager. It found no user mapped twice and no user who is unmatched, terminated or in another cost center.
- **(5)** A manager sees every row of AccessEmployees, including the e-mail addresses and termination dates of {{ x.n_employees }} employees, because no rule or relationship filters it. The fix is leaving the table out of the published file, or a rule of `FALSE ()` for the role, which empties the table but leaves its name and columns visible.
- **(6)** Run the review whenever the security table changes and at least quarterly, with the controller's approval recorded, and by someone other than the person who maintains the table.
- The limits: the review tests status and cost center on the day it runs, and Email stands in for the sign-in name, which the service may spell differently.

A strong answer reports a clean review without calling it proof, and ties the frequency to the events that change the table. A weak one lists the query results and stops.

## Common mistakes and how to respond

- **`RELATEDTABLE`.** *Symptom:* the query fails. *Response:* ask whether Security is related to CostCenter.
- **A flag nobody tested.** *Symptom:* "zero flagged, so it works". *Response:* ask for the test rows and their flags.
- **The wrong order.** *Symptom:* the unmatched test row reads {{ x.wrong_order }}. *Response:* ask what a missing employee's status is.
- **Rows counted, not cost centers.** *Symptom:* a user whose mapping was typed twice is listed in (3), or appears twice in (4). *Response:* ask what (3) and (4) ask about, a cost center or a row.
- **An auto-created relationship.** *Symptom:* the Sales Manager sees {{ x.s_employees }} employees of the {{ x.n_employees }}, and the student reports no leak. *Response:* ask Model view what reaches the table.
- **The review run under a role.** *Symptom:* an empty list of unmapped cost centers. *Response:* ask which rows the role hides.
- **Findings ignored.** *Symptom:* a table typed in sequence, {{ x.seq_flagged|length }} users flagged, and a note that says all is well. *Response:* ask who sees what.
- **A one-time review.** *Symptom:* a note with no frequency. *Response:* ask when the table next changes.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 10 | Seven columns, typed, unrelated | A related table |
| Requirement 2 | 15 | The cost center left out, by name | The ID only |
| Requirement 3 | 10 | The query, and its empty result explained | The query without a test |
| Requirement 4 | 25 | One row per user, the lookups, a flag with the three tests in order | A flag with fewer tests |
| Requirement 5 | 15 | All employees seen, the reason, a fix | The leak found without a fix |
| Requirement 6 | 25 | Findings, a frequency with a trigger, the fix before publishing | One of the three |

## Extensions and discussion questions

- Add a measure that counts the flagged users, so the review has a number of record, and place it on a page of Audit Monitoring as a rule test of Chapter 16.
- Add the job title to the flag: it reads "not a manager" when the title does not end in Manager. Say what the test finds on the access review of Tutorial B.1.
- Discuss: who should run the review, the person who maintains the table, the person who approves it, or internal audit?
- Discuss: Email stands in for the sign-in name. What does the review miss if the two differ?
