---
note: appB.chapter
uses: [appendix_b.t1, appendix_b.ex2, appB.g2]
title: 'Appendix B: Publishing, Securing, and Sharing Reports'
kind: chapter-notes
unit: appB
minutes: 150
tool: powerbi
figures:
  - id: IF-AB-0-A
    kind: diagram
    purpose: A decision path that helps an instructor choose how much of the appendix to teach.
    shows: "A decision tree. Start: students have Power BI Desktop and the Charles River Reports project. First question: do you and a partner have Pro or Premium Per User licenses and a shared workspace where you are Admin? Yes leads to Scope 3 (Scope 2 plus Steps 1 to 4 of Tutorial B.2 with a colleague). No leads to a second question, whether to add the Publishing and Sharing section as reading with Step 5 of Tutorial B.2 as a workshop. No gives Scope 1 (Tutorial B.1, both exercises), yes gives Scope 2. Each end box lists what students do, what it needs, its class minutes and the questions it covers, as the Teaching approaches table does."
    data: None; the scopes, minutes and question numbers are read from the Teaching approaches table of this guide.
  - id: IF-AB-0-B
    kind: pbi-mock
    purpose: The Checks tab of the model answer, the fast way to compare a student's numbers with what each manager should see.
    shows: "DAX query view on the model answer with the tab Checks selected, a Run button, and a result grid with the columns Section, Check, Expected, Actual and Agrees, scrolled to the eight rows that start 'as employee006 (Sales Manager)'. Each row has Agrees true: Cost Centers Shown, the budget, the actual, the flexed budget, the net income, the revenue of every sale, Manufacturing Hours as blank, and the employees. The outline marks the Agrees column."
    data: The Checks tab of the solution project after a refresh; the rows of Guided Tutorial B.1 for the Sales Manager.
---
{% set t1 = appendix_b_t1 %}
{% set e2 = appendix_b_ex2 %}
{% set g2 = appB_g2 %}
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
# Appendix B: Publishing, Securing, and Sharing Reports

{{ header() }}

## At a glance

| | |
|---|---|
| Part | An appendix, read after Chapters 15 and 16. It continues their story: the controller releases Charles River Reports to the department managers, and internal audit reviews who will see what before it goes out |
| Analytics types | The appendix names none. If you map it to the four types, the access review is diagnostic (a list compared with the records) and the memos are prescriptive |
| Tools | Power BI Desktop {{ version }} on Windows: **Modeling > Manage roles**, **Modeling > View as**, TMDL view, DAX query view and **Optimize > Review > Performance analyzer**. The Power BI service, for Steps 1 to 4 of Tutorial B.2 only |
| Components | Two guided tutorials (B.1 has {{ w_steps1 }} steps and B.2 has {{ w_steps2 }}), {{ w_exercises }} exercises (one managerial, one auditing), and {{ w_questions }} multiple-choice questions. There is no slide deck |
| Files students need | CharlesRiver.xlsx. AppendixB-companion.zip holds Charles River Reports and Audit Monitoring at the start of Tutorial B.1 and Charles River Reports at the start of B.2. AppendixB-exercises-pbi.zip holds the model answer |
| License | Tutorial B.1 and both exercises need no license. Steps 1 to 4 of Tutorial B.2 need a work or school account, a workspace where the student is Admin, and a Pro or Premium Per User license for the student and for a colleague in the same organization (both Premium Per User in a Premium Per User workspace). Step 5 needs none |
| Time | Class: about 150 minutes (Plan A below). Students: about 60 minutes of reading, 75 to 90 for Tutorial B.1, 45 to 60 for B.2 (about 20 without a license), and about 75 for each exercise. The times are estimates for the activities, not an extra homework total: decide which tutorial work happens in class and subtract it from the homework. Plan B assigns the two exercises after the lab. For a lighter load, assign one exercise and keep the role-test memo |

The appendix depends on these conditions of the data:

- The CostCenter table records a manager for each of {{ t1.n_centers }} cost centers. {{ w_flagged }} of them are wrong for access: {{ w_terminated }} managers of record are terminated employees whose jobs were not managerial, and one is an analyst. The managers who run Sales and Warehouse are not recorded at all.
- The approved security table maps {{ e2.users }} users to {{ e2.ccs }} cost centers, and every address is the Email of an active employee in that cost center. {{ g2.center }} is left out on purpose: it has {{ g2.in_unmapped }} employees and no approved manager.
- Manufacturing's costs are budgeted as cost of goods sold, so the Budget page is empty for the Production Manager. Employees of the Sales cost center record no labor time, so the Plant page is empty for the Sales Manager.
- No relationship joins the invoice lines to CostCenter or Employee. Only the rule on Item restricts sales, which is why the role denies by default.
- LaborTimeEntry holds pay as ExtendedLaborCost. Some job titles have only non-manufacturing time, so they show cost and no hours (Exercise B.1).

## What students should be able to do afterward

1. Build a dynamic row-level security role from a security table, and say which tables each rule reaches and which it leaves alone. Practiced in Tutorial B.1 (Steps 3, 5 and 6), Exercise B.2 (5), and questions 1 and 4.
2. View a report as several users, and say what each one's pages silently leave out and how a card tells the reader. Practiced in Tutorial B.1 (Steps 7 to 10), Exercise B.1 (3), and question 8.
3. Compare an access list with the employee records as a repeatable query, and report what it finds. Practiced in Tutorial B.1 (Steps 1 and 4), Exercise B.2 (1) to (4) and (6), and question 3.
4. Hide a column from a role with object-level security in TMDL view, and say what that breaks. Practiced in Exercise B.1 (2), (3) and (5), and question 5.
5. Recommend workspace roles, a home for the finance pages, a refresh arrangement, and a position on Publish to web and sensitivity labels. Practiced in Tutorial B.2 (Step 5) and questions 2, 6, 7 and 8.

## Preparing to teach

**The week before**

- Students need Windows and Power BI Desktop {{ version }}. **Help > About** shows the version. **Manage roles**, **View as**, TMDL view and Performance analyzer are Desktop features. A Mac student works in a lab or a virtual machine.
- Do Tutorial B.1 yourself, and Step 5 of B.2. Do Steps 1 to 4 too if you have a license and a colleague, because the service's pages cannot be rehearsed from Desktop.
- Open the model answer once. Its pages are the report of the chapters plus Ex B.1, Ex B.2 and Notes; its roles are Cost Center Managers and Finance; its TMDL view tab Ex B.1 holds the exercise's script; its DAX query tabs are Tests, Ex B.2 and Checks. Change the source if CharlesRiver.xlsx is not at `C:\CharlesRiver\CharlesRiver.xlsx`, choose **Home > Refresh**, then run Checks.
- A late student takes the start files from AppendixB-companion.zip. Its README gives the steps: copy the folder, open the .pbip, point the queries at CharlesRiver.xlsx, refresh, and **File > Save as** a .pbix.
- Open the **View as** window once on a lab machine. This guide names its fields as the tutorial does (**Other user**, a role check box, **OK**, **Stop viewing**), and they are not verified here for your build.
- Decide the scope (see Teaching approaches). If you want Steps 1 to 4 of B.2, ask the institution for an exercise workspace for each pair, or unique file names, holding only synthetic material, and pair students so that each has a colleague with no stronger access (see the Step 4 stumble).

**Checking a student's roles.** The Checks tab has {{ n_checks_t1 }} rows for Tutorial B.1, {{ n_checks_e1 }} for Exercise B.1 and {{ n_checks_e2 }} for Exercise B.2. It runs in DAX query view as the file's author, so no role applies. Of the {{ n_checks_t1 }}, {{ n_role_rows }} are role rows: each repeats the role's rules as filters with the user's name typed in, so they prove the rules' logic and the numbers, not that a student's saved role is right. The model answer was also run through Desktop's engine under copies of the role with the name typed in, which is the same idea. Only **View as** shows what a student's own role does. The row below is the Sales Manager's.

```dax jinja
{{ dax_role }}
```

Use these rows to read what a correct role shows. To grade a student's role, read the test log and look at the role in **Manage roles**. Screens of **View as** support the log.

{{ figure('IF-AB-0-B') }}

**Pitfalls that cost class time**

- **Viewing as yourself.** Choosing a role in **View as** without **Other user** evaluates the rules for your own sign-in, which is not in the security table, so every page built on the protected tables is empty. Outside View as, record the actual Who Am I value for the current account and build. On a local account it can be the machine and user name.
- **A rule on CostCenter only.** Without the rule on Employee, the Sales Manager's Plant page shows the plant's {{ plant_hours|num(0) }} hours instead of an empty page.
- **No rule on Item.** A person added to the role by mistake, or the former employee of Step 8, sees every sale: ${{ leak_revenue|money }} of revenue. The ledger pages are empty, because their lines reach CostCenter.
- **IDs typed in sequence.** In the security table the cost center IDs are 1 to 7, 9 and 10. Typed as 1 to 9, the Marketing Manager sees {{ g2.seq_flagged[0].see }} and the Design Services Manager sees {{ g2.seq_flagged[1].see }}. Exercise B.2's review catches both.
- **A role written from scratch.** Exercise B.1 replaces the role if its script starts from nothing, and the rules are lost (see that guide).

{{ figure('IF-AB-0-A') }}

## Teaching approaches

**Decide the scope first.** The security half needs only Desktop. The publishing half needs a license, a workspace and a colleague, which many courses cannot give. Teach the half you can check.

| Scope | Students do | Needs | Class time |
|---|---|---|---|
| 1. Desktop security | Tutorial B.1, Exercises B.1 and B.2, questions 1, 3, 4, 5 and 8 | Desktop only | about 100 minutes (Plan B) |
| 2. Security and sharing as reading | Scope 1, the Publishing and Sharing section, Step 5 of Tutorial B.2, questions 2, 6 and 7 | Desktop only | about 150 minutes (Plan A, workshop in session 2) |
| 3. Full | Scope 2 plus Steps 1 to 4 of Tutorial B.2 with a colleague | Pro or Premium Per User for both, and a shared workspace where you are Admin | about 150 minutes (Plan A) plus 45 to 60 minutes of student time |

**Plan A: lecture with live demonstration (two sessions, 150 minutes).** It fits a lecture course. Session 2 is optional.

| Session | Minutes | Activity |
|---|---:|---|
| 1 | 15 | The controller's request, the layers of protection, static and dynamic roles |
| 1 | 10 | The access review: Step 1 live, and why the managers of record cannot be the list |
| 1 | 30 | Tutorial B.1 Steps 3, 5 and 6 live: the security table, the four rules, deny by default |
| 1 | 20 | Steps 7 and 8 live: view as the Sales Manager, the Production Manager and the former employee |
| 1 | 15 | What each manager saw; the memo; quiz on questions 1, 3 and 4 |
| 2 | 20 | Publishing and sharing: licenses, workspace roles, apps, refresh, Publish to web |
| 2 | 25 | Tutorial B.2 Steps 2 to 4 live with a volunteer as the colleague, or without a license a workshop on Step 5 in pairs |
| 2 | 15 | Debrief of the recommendations; quiz on questions 2, 6, 7 and 8 |
| | 150 | Total |

**Plan B: lab first (one session, 100 minutes).** Scope 1 only. It fits a computer lab with the start files ready.

| Minutes | Activity |
|---:|---|
| 10 | Pose the problem: what should the Sales Manager see? |
| 60 | Tutorial B.1 Steps 2 to 8 in pairs, from the start file; Step 1 is homework |
| 10 | Steps 9 and 10, the cards that tell a reader what the page shows |
| 15 | Debrief: each pair fills the table of what each user saw |
| 5 | Assign Exercises B.1 and B.2 |
| 100 | Total |

**Plan C: flipped (one session, 60 minutes).** Students do Tutorial B.1 at home. It fits upper-level and graduate classes.

| Minutes | Activity |
|---:|---|
| 10 | Quiz on questions 1, 3, 4, 5 and 8 |
| 20 | Review clinic: partners compare their table of what each user saw and the memo's three recommendations |
| 20 | Break it, on your own copy: delete the rule on Item and view as the former employee, then hide the pay column in TMDL view and view as the Production Manager |
| 10 | Assign Exercises B.1 and B.2 |
| 60 | Total |

Plan A is the safest for a course that will teach the publishing half. Plan B keeps students in Desktop and skips the service. Plan C leaves no time to build, and fails for students who arrive without a finished role.

## Tutorial guide

### Guided Tutorial B.1: Securing the Reporting Package

**Purpose.** Students review the access the controller plans, build a dynamic role, and see what each manager sees. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 5 (a rule in the DAX editor) and Step 7 (**View as** with **Other user**). Leave Steps 1 to 4 and 9 to 11 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | The review: {{ w_flagged|lower }} of {{ t1.n_centers }} rows flagged | {% for r in t1.flagged %}{{ r.center }}: {{ r.name }}, {{ r.title }}, {{ r.status|lower }}{{ "; " if not loop.last else "" }}{% endfor %} |
| 2 | Employee gains CostCenterID | Plant labor time can reach a cost center |
| 3, 4 | Nine rows, checked against the review | the cost center left out: {{ g2.center }} |
| 5, 6 | Four rules and an empty Finance role | rules on CostCenter, Employee, Item and Security |
| 9, 10 | Cost Centers Shown names the cost centers a page covers | Sales Manager: {{ t1.s.centers|join(", ") }}; Warehouse Manager: {{ t1.w.centers|join(", ") }} |
| 11 | The memo | maintainer, approver and reviewer named; pages that become partial named |

What each user sees in Steps 7 and 8, and what to look for on the screen:

| Viewer | Cost centers | Budget page (budget, actual) | Income Statement net income | Plant page | Sales and Discounts |
|---|---|---|---|---|---|
| Sales Manager | {{ t1.s.centers|join(", ") }} | ${{ t1.s.budget|money }}, ${{ t1.s.actual|money }}; flexed ${{ t1.s.flexed|money }} | ${{ t1.s.ni|money }}, {{ t1.times|num(2) }} times the company's | empty | every sale |
| Warehouse Manager | {{ t1.w.centers|join(", ") }} | ${{ t1.w.budget|money }}, ${{ t1.w.actual|money }} | {{ sm(t1.w.ni) }}, a loss | hours blank | every sale |
| Production Manager | {{ t1.p.centers|join(", ") }} | empty | {{ sm(t1.p.ni) }} | {{ t1.p.hours|num(0) }} hours, {{ t1.p.ratio|num(2) }} per standard hour | every sale |
| {{ t1.former }}, in no role row | none | empty | empty | empty | empty; the Customer table still lists {{ t1.customers }} customers |
| Finance, or no role | all {{ t1.n_centers }} | all | ${{ company|money }} | full | ${{ t1.revenue|money }} |

**Stumbles to expect**

- Step 1: EmploymentStatus and TerminationDate left out of the expansion, so the table shows the manager's name but not that the manager left, which is the finding.
- Step 3: a typo in an address. A user typed wrongly sees none of the protected data in Step 8, like the former employee. Compare with the Email column before moving on.
- Step 5: a rule typed on one table only (see the pitfalls). The Employee rule is the one students forget.
- Step 6: the rule on Item is the deny-by-default rule, and students read it as filtering items. Ask: what is it true for?
- Step 7: **View as** with the role but no **Other user**, and a page that looks empty.
- Step 9: `VALUES` in place of `DISTINCT` in Cost Centers Shown. The ledger has lines with no cost center, which add a blank member.

**The checkpoint to look for.** The four bullets of the tutorial. A strong student also says that a page can be correct and still partial, and that the card is the only sign.

### Guided Tutorial B.2: Publishing and Sharing the Package

**Purpose.** Students publish the package, assign the role to real sign-ins, test it, and recommend how the package is shared. **Time.** About 45 to 60 minutes with a license, about 20 for Step 5 alone. **Demonstrate, then hand over.** With a license, demonstrate Step 3 (**Test as role**) and let pairs do Step 4. Without one, hold Step 5 as a workshop.

| Step | Look for | Value |
|---|---|---|
| 1 | Two real sign-in names added to Security | your own on cost center 2 and the colleague's on cost center 3 |
| 2 | The report and the semantic model in the workspace | the role has no members yet |
| 3 | **Test as role** shows Sales only, with your sign-in name on Who Am I | budget ${{ t1.s.budget|money }}, as in Step 7 of B.1 |
| 4 | The colleague, a Viewer, sees Warehouse only | budget ${{ t1.w.budget|money }}, actual ${{ t1.w.actual|money }} |
| 5 | The recommendations | see the outline below |

**Stumbles to expect**

- Steps 1 to 4 with a free license: publishing works to **My workspace**, where nothing can be shared.
- Step 3: expecting Test as role to show the colleague's view. Even set to a specific person, it may evaluate the dynamic rule with your own identity, so the Who Am I card shows which name was compared, and only the colleague signed in shows their own view for certain.
- Step 3: as the workspace Admin you see every row when you open the report normally. Row-level security does not apply to the editing roles.
- Step 4: the colleague does not see the change until the next sign-in.
- Step 4: a cleanup that stops at the rows, or removes more than the test added. The colleague's workspace access, both role memberships and the two Security rows are separate grants. Each is removed, and only what the test created, judged against the access record of step a.
- Step 4: a colleague who already has a stronger grant (Admin, Member, Contributor, Write on the model, or another model role such as Finance) sees every row, and the Warehouse-only result fails. Read the record before you add the Viewer.

**The memo to look for.** Managers as readers of the app with no workspace role, because an audience cannot hide an item from someone with a workspace role, who opens every item; the controller's staff as Members or Contributors, who bypass the rules, so the list of editors is itself reviewed; the Income Statement and Validation pages in a separate report on the same semantic model, hidden from the managers' audience; a gateway, or the queries connected to the workbook's address in OneDrive or SharePoint (a copy in a synced local folder still needs the gateway), with failure notifications to the package's owner; Publish to web disabled by the administrator; a Confidential label where labels are enabled, noting that .pbip projects do not support them and that labels need the organization's Purview licensing and a published policy. Strong memos also keep the app's **Access to hidden content** off, grant sharing and Build permission only for a documented need, and say how audit will check what an approved manager can open and see.

## Difficult ideas and misconceptions

**Roles do not apply to the person who built them.** Tutorial B.1 Step 9, Question 2. In Desktop without View as, Cost Centers Shown lists all {{ t1.n_centers }} cost centers and net income is ${{ company|money }}. Members and Contributors of a workspace are not filtered either. Ask: whose view is this?

**A rule filters through relationships, and only through them.** Question 1, Exercise B.2 (5). The rule on CostCenter reaches the ledger and the budget; an unrelated table is never filtered. The Customer table still lists {{ t1.customers }} customers for the former employee, and AccessEmployees lists all {{ g2.n_employees }} employees. Ask: which tables does the rule reach?

**Deny by default is a rule, not a setting.** Tutorial B.1 Step 6, Question 4. The role has no row for a person missing from the table until the rule on Item says so, and even then it denies the protected tables only. Customer still lists its {{ t1.customers }} customers. Ask: what does the former employee see if the Item rule is removed, and what does the former employee still see with it?

**A partial page looks whole.** Tutorial B.1 Steps 7 and 10, Question 8. The Sales Manager's income statement shows ${{ t1.s.ni|money }}, {{ t1.times|num(2) }} times the company's, and nothing says why. Ask: how would the reader know?

**The master data is not the access list.** Question 3. {{ w_terminated|capitalize }} managers of record are terminated, one is an analyst, and two real managers are absent. Ask: what would a role built on ManagerID give access to?

**Rows are not columns.** Exercise B.1, Question 5. Row-level security keeps the Production Manager's rows and cannot hide their pay. Object-level security hides the column, and every visual that reads it fails. Ask: what should the controller do about the failure?

**Testing as yourself is not testing as them.** Tutorial B.2 Step 3. **Test as role** may evaluate a dynamic rule with your identity even when set to a person, and the Who Am I card shows which. Ask: how do you learn what the colleague sees?

**An audience cannot revoke broader access.** Tutorial B.2 Step 5, Question 8. An app audience grants access to what the app shows. It cannot cancel a workspace role, whose holders open every item in the workspace, a Viewer included, or any other permission a person holds apart from the app. Ask: who can open the finance report if the managers are made workspace Viewers?

**A security table is a control that needs a control.** Tutorial B.1 Steps 4 and 11, Exercise B.2. Someone maintains it, someone approves it, someone reviews it. Ask: who may do two of the three?

## Discussion prompts

1. **The controller wants to release the package tomorrow, and {{ g2.center }} has no approved manager.** A good discussion reaches release with that cost center empty, who decides, and how the gap is recorded.
2. **Who should maintain the security table?** It reaches segregation of duties for access (Chapter 8), the controller's staff as maintainers, the controller as approver, and internal audit as reviewer.
3. **The Sales Manager's income statement shows ${{ t1.s.ni|money }}.** It reaches whether a card is enough, a separate finance report, and what a manager does with a number that is not the company's.
4. **A manager changes jobs in the middle of the quarter.** It reaches the review frequency, event-driven changes, and who learns of the change.
5. **Is hiding the pay column enough?** It reaches object-level security, the visuals that then fail, and leaving cost measures out of the managers' pages.
6. **A student proposes Publish to web for a sales dashboard.** It reaches what the option exposes, what the question asks about the data, and who can turn it off.
7. **Roles are tested with names typed in a window.** It reaches Test as role in the service, the colleague's own view, and what no test inside Desktop can show.

## Using the exercises

Both exercises extend a copy of the report after Tutorial B.1 and have a model answer in AppendixB-exercises-pbi.zip. The outcome column uses the numbers above. The rubrics grade only what each requirement asks, and anything more is a plus.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| B.1 Securing Pay Data | Managerial | Power BI | 75 | Advanced | 2, 4 |
| B.2 Reviewing Access with a Query | Auditing | Power BI | 75 | Intermediate | 1, 3 |

**Assignment bundles**

- *Two tracks.* Managerial students do Exercise B.1 and auditing students Exercise B.2, then swap their notes.
- *Both exercises.* About two and a half hours, covering outcomes 1 to 4. Outcome 5 comes from Tutorial B.2 Step 5 and the questions.
- *A light load.* Exercise B.2 alone, with Tutorial B.1 Step 4, for a course that treats the appendix as an audit topic.

**Grading and discussion.** Exercise B.1's script and Exercise B.2's query tab suit grading from the saved file, with the Checks tab to compare a number. The notes of both suit class discussion. Ask for the saved .pbix, the role script and query tab, and a short test log naming the role, identity, filters, expected result and observed result. Screenshots support the log. They do not replace the editable file.

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 1.** Option B is what students expect: the rule filters the table it is written on. The filter flows to the tables on the many side.
- **Question 2.** Options A and C both assume the role governs a Member. Roles restrict readers.
- **Question 3.** Options A and B sound technical and are false. The finding is in the master data.
- **Question 4.** Option A reads the rule as filtering items. It is true for every item or none.
- **Question 5.** Option B is the right family and the wrong tool: it hides rows, not a column.
- **Question 6.** Option A is the convenient answer and the wrong one.
- **Question 8.** Option A is the most tempting. A hidden page can still be reached, so hiding it is not security.
{% if n_longest %}
- **Length.** The correct option is also the longest in {{ n_longest }} of the {{ n_questions }} questions ({{ longest_correct }}), so wording alone can give it away.
{% endif %}

Use the questions as a ten-minute quiz or as clickers. Questions 1, 3, 4 and 5 test the security design, and 2, 6, 7 and 8 the sharing.

## Connections

**Builds on.** Chapter 8's segregation of duties and exception tests; Chapters 13 to 15, which built Charles River Reports; Chapter 16, whose Audit Monitoring file holds the access review and whose rule tests the exercises echo; and Chapter 14's DAX for the rules.

**Later.** Nothing builds on it in the book. The appendix on Power BI in the browser rebuilds Chapter 13's model in the service, where **View as** becomes Test as role.

**Appendix D.** It maps each exercise to the professional frameworks, and each exercise guide names the competencies it practices.
