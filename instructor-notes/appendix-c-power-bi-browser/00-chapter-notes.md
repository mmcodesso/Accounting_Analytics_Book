# Appendix C: Power BI in the Browser

| | |
|---|---|
| Unit | Appendix C: Power BI in the Browser |
| Tools | The Power BI service in a browser (Power Query Online, the model editor, the report editor) |
| Time | About 180 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | An appendix, a companion to Part IV. It rebuilds Chapter 13's model and its Sales and Discounts page in the Power BI service and adds one measure from Chapter 14, for students who have no Windows computer or no Desktop |
| Analytics types | None named. The exercises are descriptive (control totals, a pattern of discounts) and one is a change control |
| Tools | The Power BI service at app.powerbi.com in a supported browser: Power Query Online, the model editor in Editing mode (with DAX query view), and the report editor |
| Components | Three guided tutorials (11, 9 and 5 steps), three exercises (one for each perspective) and eight multiple-choice questions. No slide deck, no companion files and no solution files: the Power BI projects open only in Desktop |
| What students need | A school account, CharlesRiver.xlsx (the service reports about 123 MB), and a text editor for Tests.dax |
| License | None beyond a school account, except Exercise C.3, which needs a Pro license for version history |
| Time | Class: about 180 minutes (Plan A). Students: about 90, 60 and 30 minutes for Tutorials C.1 to C.3 (180 in all), and 60, 45 and 45 for the exercises (150), so about five and a half hours before setup and prerequisite reading. Class time is tutorial work and counts toward those times, not as homework on top of them. Estimates: time them yourself with your cohort |

The appendix depends on these conditions of the data:

- The workbook stores InvoiceDate, and nearly every date column, as an Excel date. Power Query Online reads the bare number: the first invoice's date is 45292 and the last is 46387.
- Power Query types a column from its first 200 rows. Discount is zero there (a whole number) and PromotionID is empty (no type). The profile of the first 1,000 rows shows PromotionID empty everywhere; the entire data set has it empty on 25,825 of 27,933 lines and Discount with 4 values.
- 223 items have a ListPrice, in 5 item groups, and no invoice line is left without an item.
- Fiscal 2026 has 9,522 invoice lines and 7,171 invoices, so a count of the key on the lines overstates the invoices.
- The autumn Furniture promotion and the November Design Trade promotion produce the discount pattern. The Design Services segment buys only Services, which carry no promotion.

## What students should be able to do afterward

1. Build Chapter 13's model in the service: upload the workbook, shape four Tables in Power Query Online, set the types the service reads wrongly, and relate the tables. Practiced in Tutorial C.1, proved by Exercise C.1 (3), and questions 1, 2 and 8.
2. Build a report page in the report editor and find the four commands that differ from Desktop: the missing card, a counted key, the display units, and the sort of a month axis. Practiced in Tutorial C.2, Exercise C.2 (2) and (3), and questions 3, 5 and 6.
3. Write a measure in the model editor, test it in DAX query view, and keep the test outside the browser. Practiced in Tutorial C.3, Exercise C.1 (1), (2) and (5), and questions 4 and 7.
4. Prove a model's totals by quarter, explain a one-cent difference, and read a promotion pattern by segment and month. Practiced in Exercise C.1 (3) and (4) and Exercise C.2 (4) and (5).
5. Change a model, restore it, and log the change, saying what version history records and what it leaves out. Practiced in Exercise C.3.

## Preparing to teach

**Accounts and licenses.** Students sign in with a school account; a personal address does not work. A free license builds models and reports in My workspace, a personal area, which is all the tutorials and Exercises C.1 and C.2 need. A Pro license adds sharing, shared workspaces and version history. Exercise C.3 uses version history, and Guided Tutorial B.2 of the publishing appendix needs the model in a shared workspace, preferably an exercise workspace your institution approves, which a student chooses at Step 7 of C.1.

**What can block the work.** The appendix names one tenant setting, *Users can edit semantic models in the Power BI service*, and says a feature turned off there is unavailable whatever the license. The steps may also depend on the **Get Data** tile, on permission to create a semantic model, and on OneDrive for work or school, because the upload goes there. The book does not say which other settings an administrator may have changed. Before the term, have a student-licensed test account, not your instructor account, do what students will do: the upload and **Choose data** (Steps 1 and 2 of C.1), **Transform data** and **Save** in Power Query Online (Step 7 of C.1, **Create a semantic model only**, and Step 2 of C.3), opening the model in **Editing**, **Run** in DAX query view (Microsoft's page says it needs write permission on the model and the tenant setting for editing models, so a workspace Viewer cannot run it), **New measure** (Step 3 of C.3), the Sales and Discounts page and the matrix, legend and slicers of Exercise C.2, a report **Save** and a reopen, and, when you assign Exercise C.3, **Save to version history** and a restore (which need Write and Build permission on the model, and a license above free). A menu that appears, or an instructor account that works, is not proof that a student can. If one step stops, ask the administrator to allow a group that holds your students. If the answer is no, use Plan C, or send students to Desktop in a lab or a Windows virtual machine, as the appendix advises.

**What was read, where and when.** The service steps were read in one account, the author's school account, in My workspace, on October 6, 2026, in one browser session. The account showed the two version history commands, so it holds a Pro license or its equivalent; the license itself was not read. The service changes without notice, so labels and timings in your tenant may differ. Of the author's timings, the upload took under a minute and the model editor opened in under a minute. The dated observations describe what was seen in one account, and the record that holds them is `facts/instructor/observations/appendix-c-service-observations-2026-10-06.md`. The numerical checks of these guides (the totals, the quarters, the promotions) come from the public dataset and do not independently establish those interface observations, so repeat a representative student-account run of the appendix before you teach it. Confirm these before class:

| Not confirmed | Why |
|---|---|
| The description box of **Save to version history** and the restore labels of the version history pane (Exercise C.3) | The test read the two commands on the **File** menu, not their windows |
| Whether a free-license account sees the same **File** menu | The tested account was Pro or equivalent |
| The matrix, clustered bar chart and dropdown slicers (Tutorial C.2 Step 7, Exercise C.2) | The test did not build them, and the line chart with a legend |
| The query of Exercise C.1 and the DAX checks in the exercise guides | Built from the book's test and from Desktop-verified expressions, not run in a service |
| A relationship to a Table added later (Exercise C.1 extension) | The test added T7_PromotionProgram and stopped at Save |
| A change to an Enter data table saved in Power Query Online | The test reopened **Create table** from the Source step and saved nothing, and Microsoft's Enter data page documents such changes only in Desktop, so a browser reader reads Guided Tutorial B.2, Steps 1 and 4 |
| Test as role for Guided Tutorial B.1's checks as a manager, and from My workspace | Not run; Test as role views a role or a person of the organization and, as Microsoft's page says, evaluates dynamic rules with the tester's own identity, so it cannot play the fictional addresses of the security table |

**What the book rests on.** The statements that cite Microsoft Learn are the upload through OneDrive, the type detection from the first rows, the column profile, the report editor, version history (the license, the capture on opening in Editing mode, the five versions and the 14-day restore), DAX query view (the write permission and the tenant setting in the web), the editing setting, the saves of the model editor and Power Query Online, and the free license. The other differences the tutorials meet (dates read as numbers, the missing card, display units set card by card, a month axis sorted by value, the model editor's commands) rest on the author's test alone, and two of them differ from Learn. Learn's upload page has the student change Anonymous to Organizational account and sign in, where the test found it set already, and Learn's card page puts the display units under Callout values > Values for all cards. The tutorials now say what the test saw and what to do when a tenant shows the other state.

**The week before.**

- Run the account checks above with a student-licensed account, so that a blocked account is found before the class, not at its first session or clinic.
- Do the three tutorials in your own account and keep the semantic model as your reference answer. There is no model file. Chapter13-exercises-pbi.zip holds the same model for Desktop with a Checks tab, a way to compare numbers if you have Desktop.
- Have each student upload CharlesRiver.xlsx before class, from the Downloads page. Uploads of about 123 MB from a whole class on one network are slow, and the service renames a second copy, so a student may have CharlesRiver 1.xlsx.
- Ask students to create a text file named Tests.dax now, because the service discards DAX query tabs on close.
- Point students to the appendix's two tables, one of Desktop and the service and one of Desktop commands and their browser names: they are the lookup for everything the three tutorials do not cover.

**Pitfalls that cost class time.**

- Choose data lists 164 items, each Table and its worksheet, in text order (T1, T10, T11 and so on), so the four Tables take scrolling.
- A model reopened later may be in Viewing mode; commands are unavailable until it is switched to **Editing**.
- **Choose data** has no load button, and **Create a report** has no Next: students look for Desktop's buttons.
- A report opens in Reading view after its first save; **Edit** returns it to the editor.

## Teaching approaches

![A decision path from a student's account to the plan that fits, so an instructor can see what a class can do before the first session.](../figures/appendix-c-power-bi-browser/IF-AC-0-A.pdf)

**Plan A: instructor-led lab (two sessions, 180 minutes).** It fits a lab where every student has an account that works.

| Session | Minutes | Activity |
|---|---:|---|
| 1 | 10 | Sign in, find **Create > Get Data**, check that the editor opens in **Editing**; decide who needs Plan C |
| 1 | 10 | What differs (the table of Desktop and the service): dates as numbers, types from the first rows |
| 1 | 20 | Tutorial C.1 Steps 1 to 4, live, students following |
| 1 | 35 | Students: Steps 5 to 8 (custom columns, the profile, the semantic model, the defaults) |
| 1 | 10 | Debrief: the profile on the first rows and on the entire data set |
| 1 | 5 | Students who have not finished Steps 5 to 8 finish them before Session 2; Steps 9 to 11 are Session 2 work, not homework |
| 2 | 20 | Steps 9 and 10 (relationships, properties) in pairs |
| 2 | 10 | Step 11 and the checkpoint: each pair reads the fiscal 2026 row of the Validation page |
| 2 | 25 | Tutorial C.2 Steps 1 to 6 (the page, the slicer, the card, the display units, the sort) |
| 2 | 10 | Steps 7 to 9 |
| 2 | 20 | Tutorial C.3: the measure, the test, Tests.dax |
| 2 | 5 | Questions 2, 3, 5 and 6 as clickers |
| | 180 | Total |

**Plan B: flipped (one clinic, 75 minutes).** Students do the three tutorials at home, about 180 minutes. It fits students who work on their own computers. Run the account checks of Preparing to teach before the tutorials go home, because the clinic is too late to find a blocked account. The exercises are assigned at the end of the clinic and done afterward, and the clinic's work on C.1 counts toward them once.

| Minutes | Activity |
|---:|---|
| 10 | Quiz on all eight questions |
| 25 | Pairs compare their model with the checkpoints of C.1 and C.2 and fix the commonest faults (types, relationships, the missing card) |
| 25 | Run the query of Exercise C.1 together and discuss the cent |
| 15 | Assign the exercises, and the rules of Exercise C.3 |
| 75 | Total |

**Plan C: instructor demonstration (60 minutes).** It fits a tenant that blocks student editing, or a class with few accounts. Students then do the exercises in Desktop, Exercise C.3 by hand, as without a Pro license, because Desktop has no version history. Their starting model is Charles River Reports at the end of Tutorial 13.2, which is the Start of Tutorial 13.3 folder of the Chapter 13 start files (Chapter13-companion.zip), pointed at their copy of CharlesRiver.xlsx. It already holds the model and the Sales and Discounts page. The adaptation is the Key Measures table and the Revenue measure of Tutorial C.3, which they add with **Home > Enter data** and **Home > New measure**, and the exercises' queries and the manual repair of C.3 run in Desktop's DAX query view as in the service.

| Minutes | Activity |
|---:|---|
| 10 | What the service needs and what a license adds |
| 15 | C.1 Steps 1 to 4 on your account |
| 10 | C.1 Steps 7 to 9 |
| 10 | The differences of C.2: the card, the display units, the sort |
| 10 | C.3: the measure, the test, and why the tab is lost on close |
| 5 | Questions 1, 2 and 4 |
| 60 | Total |

Plan A is the safest and the longest. Plan B is the cheapest in class time, and a blocked account is discovered only at the clinic. Plan C leaves students without hands-on work.

## Tutorial guide

### Guided Tutorial C.1: Building the Chapter 13 Model in the Browser

**Purpose.** Students reproduce Tutorial 13.1 and meet where the service differs. **Time.** About 90 minutes. **Demonstrate, then hand over.** Demonstrate Steps 1 to 4, and let students do Steps 5 to 11.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | **Upload successful**; four Tables ticked from 164 items | the copy is renamed when one exists |
| 3 | Discount typed **Decimal number** with **Replace current**; PromotionID **Whole number** with no prompt | 0, 0.08, 0.10, 0.12 are the rates it keeps |
| 4 | Item holds 223 rows; InvoiceDate shows five-digit numbers, then dates | SI-2024-000001 reads 45292 |
| 6 | PromotionID empty on every row of the first 1,000, then on 25,825 lines | Discount with 4 values |
| 8 | **Manage relationships** reads "There are no relationships defined yet." | the defaults created none |
| 11 | Fiscal 2026 row | 9,522 lines, $29,756,420.08, $33,589,137.45, $362,110.75 |

**Stumbles.** Step 1: a personal account, or a slow upload. Step 3: **Add new step** in place of **Replace current**, which rounds every rate to zero before the fix. Step 4: the date left as a number, so the custom columns of Step 5 cannot take a year from it. Step 5: the **Data type** box is set in the dialog, so no separate typing step follows. Step 6: the profile options stay unavailable until **Enable column profile** is on. Step 9: the column is chosen by clicking it in the preview. Step 11: SalesInvoiceLineID left at the visual's default, which can be Sum, so the table shows a sum of IDs instead of the line count. **Checkpoint to look for.** The tutorial's checkpoint, and an item group table with 5 rows and no (Blank).

### Guided Tutorial C.2: Building the Sales and Discounts Page in the Browser

**Purpose.** Students build Tutorial 13.2's page and meet four differences. **Time.** About 60 minutes. **Demonstrate, then hand over.** Demonstrate Step 3 (**Restore default visuals**), Step 5 (display units) and Step 6 (the sort); leave the rest.

| Step | Look for | Value |
|---|---|---|
| 2 | The slicer starts as **Between**; **Tile** and **Single select** give a button | fiscal 2026 selected |
| 4 | The invoice card counts **Count (Distinct)** | 7,171 invoices against 9,522 lines |
| 5 | **Display units** set card by card | revenue $29,756,420.08 in full once set to **None**, abbreviated before |
| 6 | Sorted by value the axis starts Oct, Sep, Nov, Dec | by **Month** the line is near zero, then rises |
| 9 | Furniture leads the bar chart | 96.1% of the discounts |

**Stumbles.** Step 3: the default visuals restored add a second card and a multi-row card; use the card whose wells are **Value**, **Categories** and **Tooltips**, which the test saw between **Gauge** and **KPI**, and pick it by name and wells, not by position. Step 4: ticking the key puts it in **Categories** and splits the card into one card for each of 7,171 invoices. Step 5: **Display units** appears only when **Apply settings to** names one card. Step 6: a line that falls reads as a trend. **Checkpoint to look for.** The cards equal the Validation page, and the invoice card is lower than its line count.

### Guided Tutorial C.3: Adding a Measures Table and a First Measure

**Purpose.** Students add Key Measures, a first measure and a test. **Time.** About 30 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (**Transform data**, **Enter data**, **Save**); leave the rest.

| Step | Look for | Value |
|---|---|---|
| 2 | **Create table** dialog; **Save** applies the table | Key Measures appears in the **Data** pane |
| 3 | Select Key Measures before **New measure** | the measure lands in that table |
| 4 | **Is hidden** on Column1 | Key Measures moves to the top |
| 5 | The Results grid shows one row for each year | 2024: 27,313,723.48; 2025: 29,376,702.28; 2026: 29,756,420.08 |

**Stumbles.** Step 2: **Save** is at the bottom right of Power Query Online, not **Close & Apply**. Step 5: the tab is gone when the model closes, so the query belongs in Tests.dax. **Checkpoint to look for.** The query's revenue equals the Validation page's line total for each year.

## Difficult ideas and misconceptions

**The service reads a workbook date as a number.** Tutorial C.1 Step 4, question 2. The cells are dates in the workbook and numbers in Power Query Online. Students conclude that the upload damaged the file. Ask: which step fails if the type stays a number?

**Types come from the first rows.** Question 8. Discount is zero in the rows Power Query inspects, so it arrives whole and rounds every rate to zero, exactly as in Chapter 13. Ask: why does **Replace current** matter?

**A key is a category, not a count.** Tutorial C.2 Step 4, question 5. Ticking a key that a relationship uses puts it in **Categories**. Ask: what do the thousands of small cards show?

**A sorted line looks like a trend.** Tutorial C.2 Step 6, question 6. With months sorted by value, discounts fall from Oct to Jul across the chart. Ask: how would a reader know?

**The browser saves as you work.** Tutorial C.3, Exercise C.3. Editing mode keeps each change at once, with no undo. Ask: what is the way back?

**A test lives outside the report.** Tutorial C.3 Step 5, Exercise C.1 (5). A query reads the model, so a page change cannot alter it; a model change can. Ask: which would the cards of Tutorial C.2 detect?

**A license is not a permission.** The section on what the browser needs. A tenant setting beats a Pro license. Ask: who can switch it on?

## Discussion prompts

1. **A student reports that the model editor will not let them edit.** A good discussion reaches Viewing against Editing, the tenant setting, and the fallbacks.
2. **The discount line falls from left to right.** It reaches the axis labels, the sort, and who checks a chart before it is shown.
3. **Dates arrive as numbers.** It reaches silent type problems, Chapter 4's rule about the first rows, and a check on every date column.
4. **The service keeps five versions.** It reaches what version history proves and what a project under version control, as in Chapter 16, adds.
5. **Where should a team keep its tests?** It reaches the query tab, a text file, and a repository, and what is lost with each.
6. **The uploaded copy is not the master workbook.** It reaches lineage, refresh, and which file the model reads.
7. **A one-cent difference between quarters and year.** It reaches rounding, materiality, and when to stop chasing a number.

## Using the exercises

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| C.1 Control Totals by Quarter | Financial | Power BI service | 60 | Intermediate | 1, 3, 4 |
| C.2 Which Customers Got the Discounts, and When | Managerial | Power BI service | 45 | Basic | 2, 4 |
| C.3 A Change, Recorded and Restored | Auditing | Power BI service | 45 | Intermediate | 5 |

**Assignment bundles.**

- *Three tracks.* Financial students do C.1, managerial students C.2 and auditing students C.3, then swap their answers.
- *All three.* About two and a half hours, covering outcomes 2 to 5. Outcome 1 comes from the tutorials.
- *Without Pro.* C.1 and C.2, and C.3 by the manual route: the formula and baseline result recorded first, the formula retyped, the method labeled manual repair.

**Grading and discussion.** C.1's Tests.dax and C.3's change log suit grading, and so do C.2's saved page and the screenshot or table that students attach to it. The rubrics grade only what each requirement asks, so a clean extra, such as promotion amounts read from T7_PromotionProgram, is a plus. C.2's fifth requirement and C.3's comparison suit class discussion. Do C.3 last: it changes the Revenue measure that C.1's query reads.

## Multiple-choice questions

Key: 1 C, 2 A, 3 D, 4 B, 5 B, 6 D, 7 C, 8 A.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | C | Power Query Online reads uploaded files from the user's OneDrive for work or school. |
| 2 | A | the workbook stores InvoiceDate as an Excel date; the first invoice reads 45292, which is 2024-01-01 once typed as Date. |
| 3 | D | Restore default visuals, under the … below the visual types, brings the card back. |
| 4 | B | DAX query view in the browser discards its tabs on close; keep the tests in a text file. |
| 5 | B | keys used by relationships are set not to summarize, so the field lands in Categories; drag it to Value and choose Count (Distinct). |
| 6 | D | the chart is sorted by its values; More options \> Sort by \> Month, then Sort ascending. |
| 7 | C | Power Query Online's Save applies its changes to the model; Close & Apply is Desktop's. |
| 8 | A | with automatic type detection enabled, Power Query Online types each column from its first 200 rows, where Discount is zero. |

**Questions where a wrong option tempts**

- **Question 1.** Option A: the service reads Tables, and Choose data lists them.
- **Question 2.** Options B and D blame the upload or accept the number.
- **Question 3.** Option A treats a missing card as a missing feature; **Restore default visuals** brings it back.
- **Question 4.** Option C blames the mode; the book's reason is the close.
- **Question 6.** Option A agrees with what the sorted line shows, so it is the dangerous one.
- **Question 7.** Option A is Desktop's command, and option D is the first save only.

Use the questions as a ten-minute quiz or as clickers after each tutorial.

## Connections

**Builds on.** Chapter 13, whose model and Sales and Discounts page the tutorials rebuild; Chapter 14, whose Key Measures table and Revenue measure Tutorial C.3 starts; Chapter 4, which taught the first-rows rule; and Chapter 6, which the Validation page reconciles to.

**Later.** Students who continue Part IV in the browser use the appendix's last section and its table of command names. It sends them through Tutorial 13.3 before Chapter 14, has them keep the Key Measures table, Revenue and Exercise C.1's measures when Tutorial 14.2 creates them, and has them rewrite their saved tests on the Date table's fields after Tutorial 14.1. Chapter 16's Audit Monitoring is a second model, read from the uploaded copy. In the appendix on publishing and securing reports, Test as role takes the place of **View as**, but it evaluates dynamic rules with the tester's own identity and cannot play the fictional addresses of Guided Tutorial B.1's security table. Students define B.1's roles with Manage roles, record the identity on the Who Am I card, and read or watch you demonstrate B.1's checks as the Sales, Warehouse and Production managers, unless you supply a separately tested exercise with real sign-in names. A student who is not mapped should see no protected rows, and that blank result verifies denial for that identity, not the manager-specific results. For a model in a shared workspace, which should be an exercise workspace you approve, Guided Tutorial B.2 skips Publish, and the student reads Steps 1 and 4, which change the security table in Desktop, does the rest, and removes only the role members the test added. A student whose model is in My workspace reads its Steps 1 to 4 and does Step 5. Chapter 16's change control is what Exercise C.3 compares with. The Part II case and Chapter 15 use the promotions that Exercise C.2 reads.

**Appendix D.** It maps each exercise to the professional frameworks, and each exercise guide names the competencies it practices.
