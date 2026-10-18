---
note: ch14.chapter
uses: [ch14.t1, ch14.t2, ch14.t3, ch14.ex1, ch14.ex2, ch14.ex5, ch14.ex6, ch14.mcq]
title: 'Chapter 14: Data Models and DAX Measures'
kind: chapter-notes
unit: '14'
minutes: 360
tool: powerbi
figures:
  - id: IF-14-0-A
    kind: diagram
    purpose: What each tutorial adds to the model, so an instructor sees where each exercise attaches.
    shows: "Left to right: the Chapter 13 report, Tutorial 14.1 (star and Date table), Tutorial 14.2 (Key Measures and the Tests tab), Tutorial 14.3 (ledger star, income statement, Test 3). Below the line, the six exercises as branches, each labeled with what it adds."
    data: None; the boxes cite the tutorials, exercises and the model answer's queries, measures and tabs.
  - id: IF-14-0-B
    kind: pbi-mock
    purpose: The Model view of the model answer, with both stars, the shared Date table and the dashed relationship.
    shows: "Model view with SalesInvoiceLine, Item, Customer, Date, GLEntry, Account, CostCenter, ShippedLines and Key Measures. Each line shows 1 at the dimension and an asterisk at the fact table. The line from ShippedLines.ShipmentDate to Date is dashed. Key Measures stands apart."
    data: None; the tables and relationships of the model answer.
  - id: IF-14-0-C
    kind: pbi-mock
    purpose: The Checks tab, the quick way to compare a student's number with the model answer.
    shows: "DAX query view with the tab Checks, a Run button and a grid with the columns Section, Check, Expected, Actual and Agrees, scrolled to the rows of Exercise 14.4, Agrees true in each."
    data: The Checks tab of the solution project, run after a refresh; the rows of Exercise 14.4.
  - id: IF-14-0-D
    kind: diagram
    purpose: A board sketch of filter context, row context and context transition.
    shows: "Three panels. First, a matrix cell (Furniture, one quarter) with its three filters flowing along relationships to the invoice lines, where SUM adds what remains. Second, a calculated column on Customer with a row context and no arrow to the lines. Third, the same column in CALCULATE: the current customer becomes a filter and the arrow appears."
    data: None; the chapter's own examples, with no values on the board.
---
{% set t1 = ch14_t1 %}
{% set t2 = ch14_t2 %}
{% set t3 = ch14_t3 %}
{% set e1 = ch14_ex1 %}
{% set e2 = ch14_ex2 %}
{% set e5 = ch14_ex5 %}
{% set e6 = ch14_ex6 %}
{% set mq = ch14_mcq %}
# Chapter 14: Data Models and DAX Measures

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part IV, Accounting Analytics with Power BI: the second of four chapters. It turns Chapter 13's report into a model that Chapters 15 and 16 and the Part IV case build on |
| Analytics types | Descriptive, with the first steps of diagnosis: a margin against the same quarter last year, an expense against its own recent history |
| Tools | Power BI Desktop {{ version }} on Windows, reading CharlesRiver.xlsx: Power Query, Model view, Table view, Report view and DAX query view |
| Components | {{ unit.tutorials|length }} guided tutorials ({{ steps[1] }}, {{ steps[2] }} and {{ steps[3] }} steps) that extend Charles River Reports.pbix, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.xlsx. Chapter14-companion.zip holds Charles River Reports, a Power BI project, at the start of Tutorials 14.1, 14.2 and 14.3 and at the end of the chapter. Chapter14-exercises-pbi.zip holds the model answer |
| Time | Class: about 360 minutes. Students: about 100 minutes of reading, 60 to 105 for each tutorial and 60 to 100 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The {{ t1.n_lines|count }} invoice lines each find their invoice in the merge. The Date table holds {{ t1.days|count }} days, from {{ t1.first }} to {{ t1.last }}: whole years, one past the last invoice.
- Fiscal {{ y }} has {{ n_lines|count }} lines but {{ n_invoices|count }} invoices, so the Invoices measure counts distinct invoices on the lines.
- The ledger holds {{ t3.n_gl|count }} postings, among them those of the closing entries, two for each fiscal year, dated December 31. Each year's net income equals what its close transferred, and with the closes kept it is zero.
- Operating expense runs more than a fifth above its expectation in the second month of the data and in {{ t3.n_paydays }} months with three pay dates.
- The {{ e2.n_services|count }} Services lines have no shipment. {{ e6.numbers }} are dated late in {{ d.P }} and posted on the first day of {{ y }}.
- {{ e1.n_contra }} contra accounts sit in the chart, and some have never been posted. The Customer table holds {{ e5.customers|count }} customers; {{ e5.n_invoiced|count }} bought in fiscal {{ y }}.

## What students should be able to do afterward

1. Design a star from the Charles River tables, name its fact tables and grain, and flatten a header-line pair. Practiced in Tutorial 14.1 (Steps 1 and 4), Exercise 14.2 (1) and (2), and questions 1 to 3.
2. Set cardinality and direction, build and mark a date table, and use an inactive relationship for a second date. Practiced in Tutorial 14.1 (Steps 2 to 4), Exercises 14.2 (3) and (4) and 14.5 (2), and questions 4 to 6.
3. Write explicit measures with SUM, DIVIDE, SUMX, RELATED and variables, and choose between a measure, a DAX column and a Power Query column. Practiced in Tutorial 14.2 (Steps 2 to 4), Exercises 14.3 (1) and 14.4 (1) to (3), and questions 7 and 8.
4. Explain filter context, row context and context transition, and change the filter context with CALCULATE. Practiced in Tutorial 14.2 (Step 5), Exercises 14.1 (1) and 14.5 (1) and (3), and questions 9 to 12.
5. Compare periods with time intelligence. Practiced in Tutorial 14.3 (Step 7), Exercises 14.3 and 14.4, and question 14.
6. Model the ledger so that closes and signs are handled once, and test measures against control totals. Practiced in Tutorial 14.3 (Steps 3, 5, 6 and 9), Exercises 14.1 and 14.6, and questions 13 and 15.

These outcomes are this guide's own, and they follow the chapter's six learning objectives one for one, in the same order.

## Preparing to teach

**Before the first class**

- Students need Windows and Power BI Desktop {{ version }} (**Help > About**). A Mac student works in a lab or a virtual machine, as in Chapter 13.
- Do the three tutorials yourself in order and save Charles River Reports.pbix. Tutorial 14.3 loads the ledger with **Transform Data**, and **Close & Apply** takes several minutes: tell students to start it before a break.
- A student who lacks the Chapter 13 report, or falls behind, takes Charles River Reports from Chapter14-companion.zip, from the folder of the tutorial they start. Its README gives the steps: open the .pbip, point the queries at CharlesRiver.xlsx (**Home > Transform data > Data source settings > Change Source**), choose **Home > Refresh**, and **File > Save as** a .pbix. The deck has a checkpoint slide for each tutorial.
- Tell students to save a copy after Tutorial 14.3, such as `Ch14 Exercises.pbix`, for the exercises: one page or query tab and one display folder of measures for each.
- Open the model answer once. Its pages are Sales and Discounts, Validation, Review, Margins and Income Statement (the end of the tutorials), Ex 14.1 to Ex 14.4 and Notes. Exercises 14.5 and 14.6 are DAX query view tabs, Ex 14.5 and Control Totals, beside Tests and Checks. After **Home > Refresh**, choose **Run** on the Checks tab. It holds {{ n_checks|count }} checks, {{ n_checks_mine|count }} of them for this chapter's tutorials and exercises and the rest carried over from Chapter 13's, and its Agrees column shows the result of the run, which is the evidence that the model passed.
- If a student's window shows separate Build and Format panes instead of Visualizations, the on-object interaction preview is on. The tutorials describe the default panes.

**Pitfalls that cost class time**

- **The order of Tutorial 14.1.** Each visual must stop using SalesInvoice before the table leaves the model. A visual that shows an error still holds one of its fields: replace it as in Step 5.
- **Reserved words.** An unquoted Date or Item fails with a syntax error, and the measures built on it show an error too. Choosing a name from the suggestion list adds the quotes.
- **The Measures table.** Desktop rejects a table with that name: the book uses Key Measures.
- **Lines or invoices.** Count rows reads {{ n_lines|count }} lines for fiscal {{ y }}; the Invoices measure reads {{ n_invoices|count }}.
- **The results grid.** It ignores a measure's format, so each test rounds.
- **The wrong table to clear.** `ALL ( SalesInvoiceLine )` in a share removes the year too: Furniture reads {{ t2.all_share|pct(2) }} in place of {{ mq.rf_share|pct(2) }}.
- **The closes.** A measure that keeps them shows a net income of zero.
- **The year after the window.** A prior-year measure shows a row for it.

{{ figure('IF-14-0-B') }}

## Teaching approaches

**Plan A: lecture with live demonstration (four sessions of 90 minutes, 360 minutes in all).** It fits a lecture course with the exercises at home.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 5 | The report's questions | 2 to 5 |
| 1 | 25 | Star, grain, snowflake, relationships, the inactive one; check | 6 to 16 |
| 1 | 15 | The date table and the reserved words | 17 to 19 |
| 1 | 45 | Tutorial 14.1: Steps 2, 3 and 5 live; the rest for students | 20 to 23 |
| 2 | 25 | Measures, evaluation context, context transition; check | 24 to 33 |
| 2 | 20 | CALCULATE, what to remove, the functions | 34 to 39 |
| 2 | 10 | Testing in DAX query view | 40 to 43 |
| 2 | 35 | Tutorial 14.2: Steps 3 and 5 live; the rest for students | 44 to 48 |
| 3 | 20 | Time intelligence and its limits; check | 49 to 53 |
| 3 | 25 | The ledger star, the closes, the signs; check | 54 to 60 |
| 3 | 45 | Tutorial 14.3: Steps 3, 6 and 7 live | 61 to 65 |
| 4 | 10 | Looking ahead and the summary | 66 to 71 |
| 4 | 50 | Exercises 14.1 and 14.4 in pairs | |
| 4 | 15 | Quiz on questions 4, 8, 10, 12, 14 and 15 | |
| 4 | 15 | Discussion prompts 1, 2 and 5 | |
| | 360 | Total | |

**Plan B: lab first (three sessions of 120 minutes, 360 minutes in all).** Students build before they hear the vocabulary. It fits a computer lab; a pair that falls behind takes the next tutorial's start file.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Pose the questions | 5 |
| 1 | 60 | Tutorial 14.1 in pairs | 21 to 23 |
| 1 | 20 | Debrief: snowflake, Both, the inactive relationship | 9 to 14 |
| 1 | 30 | Short lecture on measures and evaluation context | 25 to 31 |
| 2 | 60 | Tutorial 14.2 in pairs | 45 to 48 |
| 2 | 20 | Debrief: ALL against REMOVEFILTERS, the tests | 36, 41 to 43 |
| 2 | 20 | Short lecture on time intelligence | 50 to 53 |
| 2 | 20 | Start Exercise 14.3 | |
| 3 | 75 | Tutorial 14.3 in pairs | 62 to 65 |
| 3 | 20 | Debrief: the closes and the signs | 57, 58 |
| 3 | 25 | Start Exercise 14.6 | |
| | 360 | Total | |

**Plan C: flipped, with one 150-minute class.** Students build the tutorials at home. It fits upper-level and graduate classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 15 | Quiz on questions 4, 5, 8, 10, 12, 14 and 15 | |
| 30 | Review clinic: partners compare Test 1, Test 3 and the Validation page | 43, 65 |
| 30 | Break it: ALL on the fact table, Both on Date, the closes kept, the extra year | 13, 36, 51, 57 |
| 50 | Exercises 14.5 and 14.1, or 14.6, in pairs | |
| 15 | Discussion prompts 3 and 6; assign | |
| 10 | Looking ahead to Chapter 15 | 66, 67 |
| 150 | Total | |

Plan A is the safest: the stumbles are about reading context, and a demonstration shows how. Plan B lets students meet the traps themselves and needs a lab. Plan C leaves no time to demonstrate, and fails for students who arrive without a finished model. The tutorials take students about 60 to 75 minutes for Tutorial 14.1, 75 to 90 for Tutorial 14.2 and 90 to 105 for Tutorial 14.3, more than Plans A and B give them in class, so both plans assume that students finish the steps the class does not reach outside class. Tell them which steps are due at each point, and do not expect all six exercises to fit the class plan.

{{ figure('IF-14-0-A') }}

## Tutorial guide

### Guided Tutorial 14.1: Building the Sales Star and the Date Table

**Purpose.** Students turn the Chapter 13 model into a star and add the calendar. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (the DAX table), Step 3 (Sort by column, Mark as date table) and one field of Step 5. Leave Steps 1, 4 and 6 to 8 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | The merge | {{ t1.n_lines|count }} lines, every one matched |
| 2, 3 | The Date table | {{ t1.days|count }} rows, {{ t1.first }} to {{ t1.last }}; MonthName sorted by MonthNumber; Year and MonthNumber set to Don't summarize |
| 4 | Relationships | Item, Customer and Date to the lines, many to one, **Single** |
| 5, 6 | Visuals re-pointed; SalesInvoice not loaded | no error on any page |
| 7 | Keys hidden | no key in the **Data** pane |
| 8 | The Validation page: lines, line total, list amount, discounts | {% for yr in t1.years %}{{ yr.year }}: {{ yr.lines|count }}, ${{ yr.revenue|money }}, ${{ yr.list|money }}, ${{ yr.discounts|money }}{{ "; " if not loop.last else "" }}{% endfor %} |

**Stumbles to expect**

- Step 4: a relationship accepted with the wrong cardinality or direction, or an old relationship not deleted, which leaves two paths: look for a dashed line in **Model view**. Until Step 5, the year slicer of Sales and Discounts filters nothing.
- Step 5: a field or a visual filter left on SalesInvoice, especially on the Review page's charts. Step 6 then shows an error.
- Step 5d: the slicer or the monthly charts not set back to {{ y }}, so every year shows.
- Step 3: Date left with a time, or the sort order forgotten, so April sorts first. Year left at its default, Sum, which shows as Sum of Year in the Validation table after Step 5.

**The checkpoint to look for.** The three bullets. A strong student says the totals are unchanged and says what that does not prove (offsetting changes, Tutorial 4.1 Step 10).

### Guided Tutorial 14.2: Writing and Testing the Margin Measures

**Purpose.** Students write the sales measures and test them against Chapter 6. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 3 (SUMX with RELATED and a variable) and Step 5 (CALCULATE: one filter fixed, one removed). Leave the rest to students.

| Step | Look for | Value |
|---|---|---|
| 2 | Base measures, fiscal {{ y }} | revenue ${{ t2.rev|money }}; {{ t2.n|count }} lines; {{ t2.invoices|count }} invoices |
| 3 | Cost and margin | cost ${{ t2.cost|money }}; margin ${{ t2.gm|money }}; {% for yr in d.years %}{{ t2.pct[yr]|pct(2) }}{{ ", " if not loop.last else "" }}{% endfor %} by year |
| 4 | Discount Rate | {{ t2.rate|pct(2) }}, against {{ t2.average|pct(2) }} for the average of Discount |
| 5 | Furniture Revenue; Share of Revenue | ${{ t2.furniture|money }} on every row; {% for g, v in t2.shares %}{{ g }} {{ v|pct(2) }}{{ ", " if not loop.last else "" }}{% endfor %} |
| 6 | Furniture margin by quarter | {% for q in t2.quarters %}{{ q.label }} {{ q.pct|pct(2) }}{{ "; " if not loop.last else "" }}{% endfor %} |
| 7, 8 | Test 1 and Test 2 | the fiscal {{ y }} row equals Chapter 6; Test 2 gives the two ends of the bridge, ${{ t2.q3|money }} and ${{ t2.q4|money }} |

**Stumbles to expect**

- Step 1: a table named Measures, which Desktop rejects.
- Step 2: a measure typed with another table selected, or the formats forgotten.
- Step 3: a formula typed on one line with Enter in place of Shift+Enter.
- Step 5: Share of Revenue written with the fact table cleared. It reads {{ t2.all_share|pct(2) }} for Furniture.
- Step 6c: **Edit interactions** forgotten, so the 2026 slicer empties the 2025 columns.
- Step 7: a test with no ROUND, whose raw values do not look like Chapter 6's: the grid ignores formats.

**The checkpoint to look for.** The three bullets. A strong student explains why Margin % in a total row is not an average of its cells.

### Guided Tutorial 14.3: Modeling the Ledger and the Income Statement

**Purpose.** Students add the ledger as a second star, flag the closes, and read the income statement. **Time.** About 90 to 105 minutes. **Demonstrate, then hand over.** Demonstrate Step 3 (the flag), Step 6 (the matrix, then the temporary measure that keeps the closes) and Step 7 (read the expectation slowly). Leave Steps 1, 2, 4, 5, 8 and 9 to students.

| Step | Look for | Value |
|---|---|---|
| 1 to 3 | Four Tables; the flag | {{ t3.n_gl|count }} postings; closes {% for c in t3.closes %}{{ c.number }} ({{ c.postings }}){{ ", " if not loop.last else "" }}{% endfor %} |
| 4 | Relationships | Account, CostCenter and Date to GLEntry |
| 5, 6 | Net income by year | {% for yr, v in t3.ni %}{{ yr }} ${{ v|money }}{{ "; " if not loop.last else "" }}{% endfor %}; with the closes, zero |
| 6 | Fiscal {{ y }} by subtype | operating revenue ${{ t3.sub['Operating Revenue']|money }}; cost of goods sold -${{ (t3.sub['COGS']|abs)|money }}; operating expense -${{ (t3.sub['Operating Expense']|abs)|money }} |
| 7, 8 | The expectation | {{ t3.first_spike.month }} {{ t3.first_spike.dev|spct }}; {% for p in t3.paydays %}{{ p.month }} {{ p.dev|spct }}{{ "; " if not loop.last else "" }}{% endfor %}; the rest {{ t3.low|spct }} to {{ t3.high|spct }}; {{ t3.blank }} blank |
| 9 | Test 3 | {{ t3.accounts }} accounts; debits and credits both ${{ t3.tb|money }} |

**Stumbles to expect**

- Step 1: **Load** in place of **Transform Data**, which loads every posting before it is shaped.
- Step 3: the merge on the wrong columns, or the flag left untyped. Only the journal entries' postings find a match; every other posting gets a null EntryType and a false flag.
- Step 5: GL Amount without the flag, which gives a net income of zero.
- Step 6: the card filtered with a slicer, which filters the matrix too.
- Step 7: a window built with DATESINPERIOD, which returned a stray date for the first month, so the text uses DATESBETWEEN with a guard. Without the guard, a total row compares a year with one month.
- Step 9: a trial balance that keeps the {{ y }} closes. It balances, at ${{ tb_kept|money }} instead of Chapter 6's total.

**The checkpoint to look for.** The four bullets. A strong student explains the second month by its expectation of one month, links the other six to their three pay dates, payroll recorded when paid (Chapter 11), and names a check that would confirm it, such as the payroll postings of those months by pay date.

## Difficult ideas and misconceptions

{{ figure('IF-14-0-D') }}

**The grain decides the table.** Tutorial 14.1 Step 1, questions 1 to 3. A student who keeps SalesInvoice beside the lines has two grains in one model. Ask: what does one row of this table represent?

**Both looks like a fix.** Question 4, Exercise 14.5. The number changes when the setting does, and the change feels like progress. Ask: whose selection changed whose number? With Both, a selection on Item leaves {{ e5.services_word }} days of the ledger for Services.

**A second date needs an inactive relationship.** Question 5, Exercise 14.2. Ask: which line is dashed, and which measure switches it on?

**A date table is whole days of whole years.** Question 6, Tutorial 14.1 Step 2. A table that stops at the last invoice breaks time intelligence. Ask: what would the year-to-date measure do in the last months?

**A column belongs to a row, a measure to a cell.** Question 7. List amount is a row's value, so it is a column; margin percentage changes with the cell, so it is a measure. Ask: does it depend on the reader's selection?

**Totals cannot be multiplied.** Question 8, Tutorial 14.2 Step 3. Ask: which table holds the cost, and what does SUMX do for each line?

**Filter context, row context and context transition.** Questions 9 and 10, Tutorial 14.2 Step 5. The Furniture cell for one quarter carries three filters: the row, the column and the slicer. A row context filters nothing until CALCULATE turns it into a filter. Ask: what is the cell's filter context?

**CALCULATE replaces; what you remove is the measure.** Questions 11 and 12, Exercise 14.5 (3). Ask: which filters does the table you cleared carry with it?

**A prior year can exist for a year with no data.** Question 14, Exercise 14.3 (5). Ask: what is the prior year of the last year of the Date table?

**Where the year's income goes.** Question 15, Tutorial 14.3, Exercises 14.1 and 14.6. The closes move it to retained earnings, so a measure over every posting nets to zero. Ask: which balance sheet does each treatment give?

**A pass is agreement, not proof.** Exercise 14.6, question 13. Ask: what could be wrong that no total would show?

## Discussion prompts

1. **Flattening copies the header's keys and date into the lines. When would you stop?** It reaches keys and attributes, never totals, and Chapter 10's fan-out.
2. **A colleague sets a relationship to Both to fix a count. What do you ask?** It reaches whose selection moves whose number, and counting on the fact table.
3. **Should the Date table stop at the last invoice?** It reaches whole years and fixing the measure, not the visual.
4. **List amount: Power Query column, DAX column or measure?** It reaches where the step is documented and what depends on the reader's selection.
5. **Which treatment of the closes belongs in a balance sheet, and why flag them once?** It reaches pre-closing and post-closing statements, and a fix every visual inherits.
6. **Test 1 to Test 3 pass. Is the report ready to share?** It reaches what agreement shows, what it leaves open, and Exercise 14.6's conclusion.
7. **Revenue by ship date or by invoice date?** It reaches the assumption that control passes on delivery, a rule for Services and disclosure.

## Using the exercises

All six exercises are Power BI work with a model answer in Chapter14-exercises-pbi.zip: four pages and two DAX query view tabs. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 14.1 The Balance Sheet at Any Month-End | Financial | Power BI | 75 | Intermediate | 4, 6 |
| 14.2 Revenue by Invoice Date and by Ship Date | Financial | Power BI | 100 | Advanced | 1, 2 |
| 14.3 Monthly Comparisons with the Prior Year | Managerial | Power BI | 70 | Intermediate | 3, 5 |
| 14.4 The Furniture Bridge as Measures | Managerial | Power BI | 90 | Advanced | 3, 4, 5 |
| 14.5 Testing the Model's Relationships | Auditing | Power BI | 70 | Intermediate | 2, 4 |
| 14.6 A Library of Control Totals | Auditing | Power BI | 60 | Basic | 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 14.1 and 14.2, managerial students 14.3 and 14.4, auditing students 14.5 and 14.6. Each track presents its traps to the others.
- *One exercise a session.* Take the basic one first: 14.6, 14.3, 14.1, 14.5, 14.4, 14.2.
- *A light load.* Exercises 14.1 and 14.4 take about two hours and forty-five minutes and cover outcomes 3 to 6.

**Grading and discussion.** The pages of Exercises 14.1 to 14.4 suit grading from the saved report, and the tabs of Exercises 14.5 and 14.6 from the query text, with the Checks tab to compare a number. The notes suit class discussion, and Exercise 14.6's conclusion suits peer review. Collect the .pbix, not screenshots: the measures, the display folders and the query tabs are the evidence. Grade what each requirement asks. The model answers go further in places, such as the Services revenue by year in the check of Exercise 14.2's matrix, the contra accounts never posted in Exercise 14.1, or the formats of Exercise 14.3's measures, and those count as a plus, not as conditions for full credit.

{{ figure('IF-14-0-C') }}

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 4.** Options A and C are claims the chapter never makes; D is the leak: Services leaves {{ mq.days }} days of the ledger.
- **Question 6.** Option D follows the ledger's last date and fails the full-years rule.
- **Question 8.** Option C: RELATED needs a row context, which the iterator supplies.
- **Question 10.** Option A blames the relationship, which is active. The cause is the context.
- **Question 12.** Option A sounds technical. Furniture reads {{ mq.all_share|pct(2) }} against {{ mq.rf_share|pct(2) }} because the year went with the table.
- **Question 14.** Option A inverts the finding: the first year has revenue and no prior year, and the extra year has a prior year and no revenue.
- **Question 15.** Option B sounds like accounting, but credits less debits on revenue and expense is net income until the closes reverse it.
{% if n_longest %}
- **Length.** The correct option is also the longest in {{ n_longest }} of the {{ n_questions }} questions ({{ longest_correct }}), so wording alone can give it away. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 3 make a quiz on design, 4 to 6 on relationships and the date table, 7 to 12 on measures and context, and 13 to 15 on tests, time and the ledger.

## Connections

**Builds on.** Chapter 3's keys and relationships, read as a star; Chapter 5's merges, which flatten the header; Chapter 6's bridge, trial balance and control totals; Chapter 10's work on 5080; Chapter 11's window functions, the counterpart of time intelligence, and its three-pay-date months; Chapter 12's audit library and cutoff tests; and Chapter 13's report and Validation page.

**Later chapters.** Chapter 15 builds reports for management on this model: a budget, visual calculations, a trailing average and a what-if parameter. Chapter 16 monitors exceptions with the same Power Query and DAX tests. The Part IV case builds a new report with the same techniques.

**Appendices.** The appendix on publishing and security writes its roles as DAX filters on a model like this one. The appendix on Power BI in the browser rebuilds Chapter 13's model and a first measure there. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
