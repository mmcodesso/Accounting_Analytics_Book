---
note: ch13.chapter
uses: [ch13.t1, ch13.t2, ch13.t3]
title: 'Chapter 13: Power BI Essentials for Accounting Analytics'
kind: chapter-notes
unit: '13'
minutes: 300
tool: powerbi
figures:
  - id: IF-13-0-A
    kind: diagram
    purpose: The build sequence of the chapter and the pages of the model answer, so an instructor sees where each tutorial and exercise sits.
    shows: "Left to right: the four Tables, the queries in Power Query, the model with three relationships, then the three report pages (Validation, Sales and Discounts, Review). Branches from the model lead to the six exercise pages, each labeled with the query it adds (InvoiceHeaders for 13.1, PromotionProgram for 13.3, four Profile queries that do not load, with a typed table of their figures, for 13.5) and with the tutorial it extends."
    data: None; the boxes cite the tutorials, exercises and the model answer's queries and pages.
  - id: IF-13-0-B
    kind: pbi-mock
    purpose: The model answer in Model view, with the unrelated control table beside the related ones.
    shows: "Model view of the model answer. SalesInvoiceLine in the middle, related to SalesInvoice, Item and PromotionProgram, SalesInvoice related to Customer, each line with 1 and an asterisk and an arrow toward the lines. InvoiceHeaders stands apart with no relationship line, as does the small table that holds the figures attached to the memo of Exercise 13.5. Key columns are listed in each table."
    data: None; the tables, columns and relationships of the model answer.
  - id: IF-13-0-C
    kind: pbi-mock
    purpose: The Checks tab in DAX query view, the fast way to check a student's number against the model answer.
    shows: "DAX query view on the model answer with the tab Checks selected, a Run button, and a result grid whose columns are Section, Check, Expected, Actual and Agrees, scrolled to the rows of Exercise 13.2, with Agrees true in each."
    data: The Checks tab of the solution project, run after a refresh; the rows of Exercise 13.2.
---
{% set t1 = ch13_t1 %}
{% set t2 = ch13_t2 %}
{% set t3 = ch13_t3 %}
# Chapter 13: Power BI Essentials for Accounting Analytics

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part IV, Accounting Analytics with Power BI: the first of four chapters, before the Part IV case. It builds the report file that Chapters 14 to 16 extend, and the appendix on Power BI in the browser rebuilds its model in the service |
| Analytics types | Descriptive, with the first step toward diagnostic: a reader who clicks Furniture sees where the discounts went |
| Tools | Power BI Desktop {{ version }} on Windows, reading CharlesRiver.xlsx: Power Query, Model view, Report view and the Filters pane |
| Components | {{ unit.tutorials|length }} guided tutorials that build Charles River Reports.pbix, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.xlsx. Chapter13-companion.zip holds Charles River Reports, a Power BI project, at the start of Tutorials 13.2 and 13.3 and at the end of the chapter. Chapter13-exercises-pbi.zip holds the model answer |
| Time | Class: about 300 minutes. Students: about 90 minutes of reading, 75 to 90 for Tutorial 13.1, 50 to 60 for 13.2, 40 to 50 for 13.3, and 60 to 90 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- Four Tables load: {{ t1.n_lines|count }} invoice lines, {{ t1.n_invoices|count }} invoices, {{ t1['items'] }} items (of {{ t1.items_all }}, after the list-price filter) and {{ t1.customers }} customers. Fiscal {{ y }} reads {{ t1.years[-1].n|count }} lines and ${{ t1.years[-1].rev|money }}, Chapter 6's control total.
- The lines are stored in billing order, so the first {{ top_rows|count }} end at {{ top_to }}, before any promotion: PromotionID is empty on every one of them and Discount has one value, against {{ t1.empty|count }} empty lines and {{ t1.discounts|length }} rates on the entire data set.
- Power Query types a column from its first {{ detect_rows }} rows. Discount and FreightAmount come in as whole numbers and PromotionID untyped, so Tutorial 13.1 and Exercises 13.1 and 13.5 correct a type, and Exercise 13.3 depends on one.
- Fiscal {{ y }} has {{ n_lines|count }} lines but {{ n_invoices|count }} invoices. January {{ f }}, the start-up month, has {{ t3.jan_invoices }} invoices against {{ t3.others_low }} to {{ t3.others_high }} in the other months. Discounts peak in {{ t3.top.month }} at {{ t3.top.share|pct }} of that month's revenue.
- Two customer names each belong to two customers, one promotion of the year ends before it starts, and services carry no promotion.

## What students should be able to do afterward

1. Load Tables with Power Query and correct the types that the first {{ detect_rows }} rows get wrong. Practiced in Tutorial 13.1 (Steps 2 to 5), Exercises 13.1 (2), 13.3 (1) and 13.5 (1).
2. Profile columns over the entire data set and say what a sample describes. Practiced in Tutorial 13.1 (Step 6), Exercise 13.5 and question 3.
3. Relate tables, test the relationships and say which way a filter flows. Practiced in Tutorial 13.1 (Steps 8 and 11), Tutorial 13.2 (Step 8), Exercises 13.1 (4) and 13.3 (1), and questions 4 and 6.
4. Reconcile a report to control totals before anyone reads it, and tell revenue from the other amounts on an invoice. Practiced in Tutorial 13.1 (Step 10), Exercises 13.1 and 13.2.
5. Choose the summary and the visual for the reader's task, build a page, and control how its visuals filter one another. Practiced in Tutorial 13.2, Exercises 13.2 and 13.4, and questions 1, 5, 7, 9 and 15.
6. Review a page for misleading axes, scales, periods and hidden filters, and apply the chapter's accessibility practices. Practiced in Tutorial 13.3, Exercises 13.3 (5) and 13.6, and questions 8 and 10 to 14.

These outcomes are this guide's own and are numbered differently from the chapter's six learning objectives. Outcomes 1 to 3 serve objective 2, outcome 3's filter direction and outcome 5 serve objective 3, outcome 4 serves objective 4, outcomes 5 and 6 serve objective 5, and outcome 6 serves objective 6. Objective 1, what a reporting tool adds and the vocabulary of Desktop, the service, reports and dashboards, is met by the reading and questions 1 and 2.

## Preparing to teach

**Before the first class**

- Students need Windows and Power BI Desktop {{ version }}; **Help > About** shows the version. A Mac student works in a lab or a virtual machine, or in the Power BI service in a browser when the license and the school allow it (the appendix on Power BI in the browser). Settle this in the first week.
- Do the three tutorials yourself in order and save Charles River Reports.pbix. **Close & Apply** on the large workbook takes a minute or more: tell students to start it before a break.
- Show students **File > Options and settings > Options > Global**, where clearing Auto date/time for new files saves Step 1's setting in later reports. Tutorial 13.1 sets it for the current file only.
- A late student takes Charles River Reports from Chapter13-companion.zip, from the folder of the tutorial they start. Its README gives the steps: copy the folder, open the .pbip, point the queries at CharlesRiver.xlsx (they read `C:\CharlesRiver\CharlesRiver.xlsx`, or use **Home > Transform data > Data source settings > Change Source**), choose **Home > Refresh**, and **File > Save as** a .pbix. The deck has a checkpoint slide for each tutorial.
- Open the model answer once. Its pages are Sales and Discounts, Validation and Review (the end of the tutorials), Ex 13.1 to Ex 13.5, Ex 13.6 Draft, Ex 13.6 Revised and Notes. In **DAX query view**, the Checks tab tests the control values listed on the Notes page after a refresh: choose **Run**. The figures of Exercise 13.5's Profile queries, which do not load, are checked in Power Query, not by the tab.
- If a student's window shows separate Build and Format panes instead of Visualizations, the on-object interaction preview is on. The tutorials describe the default panes.

**Pitfalls that cost class time**

- **The type trap.** Discount typed as a whole number rounds every rate to zero, so DiscountAmount is zero on every line and the Validation page shows no discounts for fiscal {{ y }} instead of ${{ t1.years[-1].disc|money }}. The fix is **Replace current**: **Add new step** converts after the rounding.
- **Lines or invoices.** Count on the lines' SalesInvoiceID reads {{ n_lines|count }} for fiscal {{ y }}; Count (Distinct) reads {{ n_invoices|count }}.
- **Summed years.** A table whose FiscalYear still sums shows one number, {{ year_sum|count }}, in place of three years.
- **Where a filter stops.** With Furniture selected, the invoice count taken from the lines reads {{ t2.f_invoices|count }}, and the count from SalesInvoice stays {{ t2.header|count }}.
- **Display units.** A card shows its amounts abbreviated until **Display units** is set to **None**.
- **A forgotten basis.** The profile returns to the top rows when the editor is reopened: read the status bar first.

{{ figure('IF-13-0-B') }}

## Teaching approaches

**Plan A: lecture with live demonstration (three sessions of 100 minutes, 300 minutes in all).** It fits a lecture course with the exercises at home.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 25 | The controller's request, why a reporting tool, Desktop, the window; check | 2 to 16 |
| 1 | 20 | Getting the data, the profile trap, the two defaults, relationships | 17 to 25 |
| 1 | 55 | Tutorial 13.1: Steps 2, 3 and 6 live; Steps 7 to 11 for students | 26 to 30 |
| 2 | 25 | How visuals summarize and filter; check | 31 to 37 |
| 2 | 50 | Tutorial 13.2: Steps 2, 3 and 8 live; the rest for students | 38 to 44 |
| 2 | 25 | Honest visuals: encodings, cognitive fit, three misleading choices | 45 to 49 |
| 3 | 20 | Check on charts; accessible design | 50 to 55 |
| 3 | 50 | Tutorial 13.3: Steps 1, 2, 5 and 6 live | 56 to 63 |
| 3 | 30 | What the report cannot answer; assign; quiz on questions 3, 6, 7 and 12 | 64 to 70 |
| | 300 | Total | |

**Plan B: lab first (two sessions of 150 minutes, 300 minutes in all).** Students build before they hear the vocabulary. It fits a computer lab; a pair that falls behind takes the next tutorial's start file.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Pose the request | 5 |
| 1 | 60 | Tutorial 13.1 in pairs | 27 to 30 |
| 1 | 15 | Debrief: the profile, the two defaults, the tie to Chapter 6 | 20, 21, 29 |
| 1 | 15 | Short lecture on summaries and interactions | 32 to 35 |
| 1 | 50 | Tutorial 13.2 in pairs | 39 to 44 |
| 2 | 10 | Which of the draft charts has a wrong number? | 49 |
| 2 | 60 | Tutorial 13.3 in pairs | 57 to 63 |
| 2 | 20 | Debrief: the choices that mislead | 49 to 51 |
| 2 | 15 | Accessible design | 53 to 55 |
| 2 | 30 | Start Exercise 13.6 in pairs | 69 |
| 2 | 15 | What the report cannot answer; assign | 64 to 67 |
| | 300 | Total | |

**Plan C: flipped, with one 120-minute class.** Students build the tutorials at home. It fits upper-level and graduate classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 15 | Quiz on questions 3, 5, 6, 7, 10 and 12 | |
| 30 | Review clinic: partners compare the Validation page and the counts {{ n_lines|count }} and {{ n_invoices|count }} | 29, 43 |
| 25 | Break it: the type trap, Count against Count (Distinct), the axis, the second axis | 20, 33, 58, 60 |
| 35 | Start Exercise 13.1, 13.5 or 13.6 in pairs | |
| 15 | Discussion prompts 1 and 2; assign | 66, 69 |
| 120 | Total | |

Plan A is the safest: the stumbles of this chapter are about reading what a visual summarizes, and a demonstration shows how. Plan B lets students meet the traps themselves and needs a lab. Plan C leaves no time to demonstrate, and fails for students who arrive without a finished report. Tutorial 13.1 takes students 75 to 90 minutes, more than the 55 or 60 minutes that Plans A and B give it in class, so both plans assume that students set it up and start before class or finish it afterward. Tell them which steps are due at each point, and do not expect all six exercises to fit the class plan.

{{ figure('IF-13-0-A') }}

## Tutorial guide

### Guided Tutorial 13.1: Loading, Relating, and Reconciling the Sales Tables

**Purpose.** Students load four Tables, shape and profile them, relate them and reconcile the model to Chapter 6 on a Validation page. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 3 (the type correction with **Replace current**) and Step 6 (the two profiles). Leave Steps 1, 2, 4, 5 and 7 to 11 to students.

| Step | Look for | Value |
|---|---|---|
| 1 to 5 | Two defaults off; four queries renamed, typed and trimmed | {{ t1['items'] }} of {{ t1.items_all }} items; {{ t1.customers }} customers |
| 6 | The two profiles | top rows: PromotionID {{ t1.first_empty|pct(0) }} empty, {{ t1.first_discounts|length }} Discount value; entire: {{ t1.empty|count }} empty, {{ t1.discounts|length }} rates |
| 7 | The row count in Table view | {{ t1.n_lines|count }} lines |
| 8, 9 | Three relationships; years not summed | filters flow toward the lines |
| 10 | The Validation page | {% for yr in t1.years %}{{ yr.year }}: {{ yr.n|count }} lines, ${{ yr.rev|money }}, list ${{ yr.list|money }}, discounts ${{ yr.disc|money }}{{ "; " if not loop.last else "" }}{% endfor %} |
| 11 | No (Blank) item group | five groups |

**Stumbles to expect**

- Step 3: Discount left whole, or corrected with **Add new step**. The Validation page shows no discounts. PromotionID untyped is quieter: nothing fails until Exercise 13.3 relates it.
- Step 4: the Item filter forgotten. The totals still tie, because no invoice line refers to an item without a list price, so a wrong filter is invisible here.
- Step 6: stopping at the first profile. Ask what the status bar says.
- Step 9: FiscalYear left at Sum, which shows one number, {{ year_sum|count }}.
- Step 10: the fiscal {{ f }} or {{ p }} row compared with Chapter 6's fiscal {{ y }} figures.

**The checkpoint to look for.** The four bullets of the tutorial. A strong student says the model ties to Chapter 6 and says what that does not prove.

### Guided Tutorial 13.2: Building the Sales and Discounts Page

**Purpose.** Students build the controller's page: slicers, cards, charts and a matrix, and find where a filter stops. **Time.** About 50 to 60 minutes. **Demonstrate, then hand over.** Demonstrate Step 3 (the cards, with the distinct count) and Step 8 (where a filter stops). Leave the rest to students.

| Step | Look for | Value |
|---|---|---|
| 2, 3 | Four cards for fiscal {{ y }} | revenue ${{ t2.rev|money }}; at list price ${{ t2.list|money }}; discounts ${{ t2.disc|money }}; {{ t2.invoices|count }} invoices |
| 4 | Discounts by month and group | peak in {{ t3.top.month }}, ${{ t3.top.disc|money }}; Furniture ${{ t2.groups[0][1]|money }} |
| 5 | The matrix | Furniture by quarter: {% for q, v in t2.quarters %}${{ v|money }}{{ "; " if not loop.last else "" }}{% endfor %} |
| 7 | Clicking Furniture | revenue ${{ t2.f_rev|money }}, discounts ${{ t2.f_disc|money }}, {{ t2.f_invoices|count }} invoices |
| 8 | Where a filter stops | {{ t2.f_invoices|count }} from the lines, {{ t2.header|count }} from SalesInvoice |

**Stumbles to expect**

- Step 2: the year never clicked in the tile slicer, so every year shows.
- Step 3: the invoice count taken from SalesInvoice, which equals the distinct count until Furniture is selected; Count in place of Count (Distinct), which reads {{ n_lines|count }}; amounts abbreviated until **Display units** is **None**.
- Step 7: expecting the line chart to change much when Furniture is clicked. It follows nearly the same path, because nearly all the discounts were on Furniture.

**The checkpoint to look for.** The three cards match the Validation page and the invoice card is lower than its line count. A strong student explains the Step 8 result from the direction of the relationship.

### Guided Tutorial 13.3: Correcting Three Misleading Charts

**Purpose.** Students rebuild a colleague's three draft charts, correct each and describe the charts for screen-reader users. **Time.** About 40 to 50 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (the axis minimum) and Step 6 (one axis). Leave the rest to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | A narrow band on a default axis | {{ t3.low_month }} ${{ t3.low|money }} to {{ t3.high_month }} ${{ t3.high|money }}, {{ t3.range|pct(0) }} of the mean |
| 3 | Growth from two starting points | ${{ t3.jan|money }}, ${{ t3.feb|money }} and ${{ t3.dec|money }}: {{ t3.from_jan|spct }} and {{ t3.from_feb|spct }} |
| 4 | Whole years | {% for c in t3.changes %}{{ c|spct }}{{ " then " if not loop.last else "" }}{% endfor %} |
| 5, 6 | Discounts on two axes, then one | {{ t3.top.month }} discounts ${{ t3.top.disc|money }} are {{ t3.top.share|pct }} of ${{ t3.top.rev|money }} |
| 7, 8 | A chart of the discounts alone; alt text on each chart | four charts |

**Stumbles to expect**

- Step 1: the year filter missing, so the line spans every month of the window.
- Step 5: reading the right-hand axis as if it shared the left one.
- Step 6: DiscountAmount left in **Secondary y-axis**, so the line still climbs.
- Step 8: alternative text that names the chart's type and not what it shows.

**The checkpoint to look for.** The four bullets. A strong student says that none of the draft's numbers was wrong.

## Difficult ideas and misconceptions

**A profile describes the rows it reads.** Tutorial 13.1 Step 6, Question 3, Exercise 13.5. A student who profiles the first rows concludes that no line carries a promotion. Ask: what is the status bar telling you, and why are the first rows not typical?

**A type from the first rows is a guess.** Tutorial 13.1 Step 3, Exercises 13.1 and 13.5. Whole-number Discount hides every discount, and the profile on the entire data set cannot show it. Ask: what would a rate of `0.08` become?

**Count counts rows; invoices need a distinct count.** Tutorial 13.2 Step 3, Question 6. The distinct count of the lines' invoice number is the only invoice count that follows an Item filter. Ask: which table does the key come from?

**A filter flows one way.** Tutorial 13.2 Step 8, Question 6, Exercise 13.1 (4). The Item filter reaches the lines and stops there; an unrelated table is never reached. Ask: which way does the arrow point?

**A name is not a key.** Exercise 13.2. Grouping by name merged two customers and moved a real customer out of the top ten. Ask: which identifier would you ship to a reviewer?

**An average of rates is not the rate.** Question 7, Exercise 13.6. The card weights each line equally. Ask: which two totals would you divide?

**Totals that agree prove less than they seem.** Exercise 13.1. Annual SubTotal equals the line total, and single invoices could still differ (Tutorial 4.1, Step 10). Ask: what would an invoice-by-invoice test need?

**A blank has a reason.** Exercises 13.3 and 13.5. A (Blank) row of lines without a promotion is meaningful, an open invoice has no payment date, and a Settled one with none is a follow-up. Ask: who would know why it is blank?

**Honest numbers can still mislead.** Questions 10 to 12, Exercise 13.6. The start-up month makes growth look large and the fitted axis makes a band look volatile. Ask: what would a reader conclude, and from which choice?

**What the reader cannot see.** Questions 13 and 15, Exercises 13.4 and 13.6. A Filters pane entry, a color and a missing alt text are invisible to someone. Ask: who is not served by this page?

## Discussion prompts

1. **The report ties to Chapter 6 to the cent. Is it ready to share?** A good discussion reaches what a tie shows (the model reproduces known totals), what it does not (every visual is right, nothing misleads) and the review of Tutorial 13.3.
2. **A profile on the first rows says no promotions. When is a sample enough?** It reaches the order of the data, the basis stated in the memo and a profile on the entire data set as the default.
3. **Should the model count invoices from the lines or from SalesInvoice?** It reaches filter direction, what a card should answer when a filter is on, and Chapter 14's measures.
4. **Two customers share one name. Who fixes the master data?** It reaches keys over names and who owns the customer table.
5. **Growth of almost four-fifths is arithmetically true. Is it misleading?** It reaches the starting period, whole years, and saying why a chart starts where it does.
6. **Why does a Top N filter belong in the title?** It reaches hidden filters and the reader's need to know what was left out.
7. **Which draft defect would a board act on?** It reaches the cost of a misleading chart and the reviewer's checklist.
8. **What would you remove from a page to make it honest?** It reaches decoration, defaults and the discipline of the title.

## Using the exercises

All six exercises are Power BI pages with a model answer in Chapter13-exercises-pbi.zip. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 13.1 Revenue Control Totals by Year and Item Group | Financial | Power BI | 60 | Intermediate | 1, 3, 4 |
| 13.2 Customer Concentration by Name or by Key | Financial | Power BI | 60 | Intermediate | 4, 5 |
| 13.3 Promotions in the Report | Managerial | Power BI | 75 | Intermediate | 1, 3, 6 |
| 13.4 A Page for the Sales Manager | Managerial | Power BI | 70 | Basic | 5 |
| 13.5 Profiling the Sales Tables on the Entire Data Set | Auditing | Power BI | 90 | Advanced | 1, 2 |
| 13.6 Reviewing a Draft Report Page | Auditing | Power BI | 90 | Intermediate | 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 13.1 and 13.2, managerial students 13.3 and 13.4, auditing students 13.5 and 13.6. A swap of notes lets each track see the others' traps.
- *One exercise a session.* Take the basic one first: 13.4, 13.1, 13.2, 13.3, 13.6, 13.5.
- *A light load.* Exercises 13.1 and 13.6 take about two and a half hours and cover outcomes 1, 3, 4 and 6.

**Grading and discussion.** The pages of Exercises 13.1 to 13.4 suit grading from the saved report, with the Checks tab to compare a number. The notes, memos and review notes suit class discussion, and Exercise 13.6's review notes suit peer review. Collect the .pbix, not screenshots: the Applied Steps and the Filters pane show choices a screenshot hides. Grade what each requirement asks. The model answers go further in places, such as the likely season of Exercise 13.3's odd promotion or Exercise 13.1's remark that annual totals can agree while single invoices differ, and those count as a plus, not as conditions for full credit.

{{ figure('IF-13-0-C') }}

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 3.** Option D is a sensible next step for a profile that shows no promotions and does not answer the question asked.
- **Question 4.** Options B and C are claims about Power BI that the chapter never makes.
- **Question 6.** Option A is what students expect; the filter stops at the lines.
- **Question 7.** Option B blames rounding, and the cause is the weighting.
- **Question 9.** Option C is a good chart for another task.
- **Question 11.** Option A adds labels and color to a scale problem.
- **Question 12.** Option B sounds plausible, but December is the largest month in only {{ dec_n }} of the {{ n_years }} years.
- **Question 13.** Options A to C change the colors and leave a reader who cannot tell them apart without a cue.
- **Question 14.** Option A inverts the finding.
{% if n_longest %}
- **Length.** The correct option is also the longest in {{ n_longest }} of the {{ n_questions }} questions ({{ longest_correct }}), so wording alone can give it away. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 and 2 make a quiz on the vocabulary, 3 to 7 on loading, relating and summarizing, and 8 to 15 on honest and accessible visuals.

## Connections

**Builds on.** Chapter 1's business intelligence tools and Chapter 3's keys and relationships; Chapters 4 and 5, which taught Power Query, merges and the (Blank) as a meaningful blank; Chapter 6's control totals and honest charts; Chapter 7's narrow band and start-up month; Chapter 10's data profile; and the Part II case's gross to net and promotions.

**Later chapters.** Chapter 14 builds the star model, a date table and DAX measures, and removes the limits named in Looking Ahead. Chapter 15 extends this report for management; Chapter 16 uses the same Power Query skills to monitor exceptions.

**Appendices.** The appendix on publishing and security takes Charles River Reports to the service. The appendix on Power BI in the browser rebuilds this chapter's model there. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
