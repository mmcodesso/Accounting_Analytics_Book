---
note: ch05.chapter
uses: [ch05.ex1]
title: 'Chapter 5: Data Preparation and Cleaning in Excel'
kind: chapter-notes
unit: '5'
minutes: 180
tool: excel
figures:
  - id: IF-05-0-A
    kind: diagram
    purpose: Which way a lookup may follow a relationship, and what to use instead when the other table is on the many side.
    shows: "Three boxes in a row: SalesInvoiceLine, SalesInvoice and SalesOrder, joined by two arrows labeled with the lookup keys SalesInvoiceID and SalesOrderID and marked many-to-one, the arrows pointing toward the one side and labeled XLOOKUP. Below SalesOrder a fourth box, Shipment, joined by a one-to-many line labeled with the key SalesOrderID. Two short rows of shipment dates under it stand for two shipments of one order. Beside that box, a note reads MINIFS, SUMIFS or COUNTIFS instead of a lookup, with a crossed-out XLOOKUP. A legend gives the line styles from Chapter 3's notation."
    data: No values. The relationships of the SalesInvoiceLine, SalesInvoice, SalesOrder and Shipment tables, from the notation of Chapter 3.
  - id: IF-05-0-B
    kind: diagram
    purpose: The row-count test for a merge, and what a repeated key in the second table does to it.
    shows: "Two panels side by side. On the left a left outer merge of SalesInvoice with Customer on CustomerID: a row count box before and the same row count after, labeled each key appears once. On the right a merge of SalesInvoice with Shipment on SalesOrderID: a row count box before and a larger one after, labeled the key repeats in the second table, with one invoice drawn as two rows after the merge. Under each panel a verdict reads count unchanged, no row repeated, or count grew, the key repeats. A note beneath says the count cannot show that every invoice found a match, which a left anti merge tests."
    data: The row counts of SalesInvoice, and of SalesInvoice merged with Shipment on SalesOrderID (the Difficult ideas section).
---
# Chapter 5: Data Preparation and Cleaning in Excel

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part II, Accounting Analytics with Excel: the second Excel chapter. It turns the Chapter 4 workbook into one prepared table, InvoiceLines, that Chapters 6 and 7 analyze |
| Analytics types | None is named. The work is preparation for descriptive and diagnostic analysis, and each tutorial ends in a check |
| Tools | Excel for Windows or Microsoft 365 for Mac, with Power Query. No SQL or Power BI |
| Components | {{ unit.tutorials|length }} guided tutorials, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.xlsx, never edited, and Charles River Furniture Analysis.xlsx as it stands at the end of Chapter 4. Chapter05-companion.zip holds the workbook at the start of Tutorials 5.1, 5.2 and 5.3 and at the end of the chapter, and Chapter05-exercises.zip the model answers. The companion files read `C:\CharlesRiver\CharlesRiver.xlsx` |
| Time | Class: about 180 minutes. Students: about two hours of reading, 45 minutes for Tutorial 5.1, 60 for Tutorial 5.2, 60 for Tutorial 5.3 and 60 to 100 for each exercise (assign two or three). The tutorial times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The Item Table keeps {{ t1.items_sold }} of {{ t1.items_all }} items (those with a list price). Every kept item has a code of the form GRP-TYP-9999, so Tutorial 5.1's code check returns zero failures. The {{ t1.fail_all }} codes that would fail belong to supplier services and capital items, which the Chapter 4 filter removes. The check passes because of that filter.
- Every invoice has one of four payment terms: 30, 45, 60 or 90 days. The bands of Tutorial 5.1 hold {{ t1.up30|count }}, {{ t1.mid|count }} and {{ t1.over60|count }} invoices, and no invoice fails the standard-terms test. The invoices fill the {{ t1.n_labels }} quarters from {{ t1.first_label }} to {{ t1.last_label }}.
- The lookups of Tutorial 5.2 find every match. Many orders have several shipments ({{ t2.multi_ship|count }}) and several invoices ({{ t2.multi_invoice|count }}), so the direction of a lookup matters.
- {{ t2.promo.after|count }} of the {{ t2.promo.lines|count }} lines of promotion {{ t2.promo.id }}, the {{ t2.promo.name }}, are invoiced after its end date, {{ t2.promo.nov|count }} in November and {{ t2.promo.dec|count }} in December, and every one comes from an order placed while the promotion ran.
- {{ t3.fractional|count }} of {{ t3.lines|count }} invoice lines carry a fractional quantity, which is the validity finding of Tutorial 5.3.
- The exercises add credit memos, invoices numbered for the next year or dated before their order, promotions {{ backwards_ids }} that end before they start and promotion {{ one_day_ids }} that lasts a day, suppliers that share an address with an employee, and item master fields that conflict with the sales. Each exercise guide lists its own conditions.

## What students should be able to do afterward

1. Explain why accounting data must be prepared before it is analyzed, and document each step with a check so that a reviewer can repeat it. Practiced in the Documentation steps of all three tutorials, in the memos of Exercises 5.1 to 5.6, and in question 15.
2. Use text and logical functions to extract, standardize, classify and validate fields. Practiced in Tutorial 5.1 (Steps 1, 2 and 5), Exercises 5.2, 5.3, 5.5 and 5.6, and questions 1, 2 and 14.
3. Use date functions to assign periods and measure the time between events. Practiced in Tutorial 5.1 (Steps 3 and 4), Exercises 5.1, 5.2, 5.4 and 5.6, and questions 3 and 4.
4. Combine tables with XLOOKUP and with INDEX and MATCH, and recognize when a lookup should be a summary. Practiced in Tutorial 5.2, Exercises 5.1, 5.2, 5.4, 5.5 and 5.6, and questions 5 to 7.
5. Build a repeatable Power Query workflow with merges and custom columns. Practiced in Tutorial 5.3, in the loading steps of Exercises 5.1, 5.5 and 5.6, and in questions 10 to 13. No exercise requires a merge; Exercise 5.1 allows one, so ask for it as an extension.
6. Tell a meaningful blank, an invalid value and missing information apart, and report a clean result as a finding. Practiced in Tutorial 5.3 (Step 6), Exercises 5.2, 5.3, 5.4 and 5.6, and questions 8, 9 and 15.

## Preparing to teach

**Before the first class**

- Students need a supported desktop Excel with Power Query, Microsoft 365 recommended, as the Preface's What You Need says. On a Mac the Power Query Editor needs Excel for Microsoft 365. XLOOKUP is in Excel for Microsoft 365, Excel 2024 and Excel 2021, whose support ended in October 2026. INDEX and MATCH is the fallback for older versions, and the chapter shows both. The model answers also use HSTACK, TAKE and CHOOSECOLS, so open them in Microsoft 365 or Excel 2024.
- Each tutorial begins from the previous one's workbook. Late students take the start file for the tutorial they begin with, from Chapter05-companion.zip. The start files read `C:\CharlesRiver\CharlesRiver.xlsx`; a student who uses one chooses **Data > Get Data > Data Source Settings**, **Change Source**, and then **Data > Refresh All**.
- Do the tutorials yourself and time them. Tutorial 5.2 adds six formula columns to a Table of {{ t3.lines|count }} rows, so time the recalculation on your students' machines.
- Get the PowerPoint deck from the Downloads page. Its modules follow the chapter's sections.

**Pitfalls that cost class time**

- **The first empty cell.** A new column starts in the first empty cell right of the last header, or it does not join the Table. On the Item Table the new columns are {{ item.ProductType }} and {{ item.CodeCheck }}, on SalesInvoice {{ si.FiscalYear }} to {{ si.StandardTerms }}, and on SalesInvoiceLine the lookups of Tutorial 5.2 run from {{ sil.InvoiceDate }} to {{ sil.ProductType }}. Step 5 of Tutorial 5.2 counts "No match" over those six adjacent columns, so a column inserted between them is counted too.
- **Fill against paste.** Tutorial 5.2's Furniture formula uses `B$44`; copy and paste it, as Chapter 4 taught.
- **Two queries, one load.** In Tutorial 5.3 Step 6 the choice of **Close & Load To**, **Table** and **New worksheet** applies to both new queries. A plain **Close & Load** sends them to the Data Model.
- **The merge dialog.** The **Use original column name as prefix** box is cleared on every expansion, or later formulas cannot find the plain names. The match message is an estimate. The loaded row count shows whether a line was repeated, and only a left anti merge that returns no rows shows that every line found its match.
- **Zero-based and one-based.** MID counts from one and Text.Middle from zero. The product type starts at 5 in Excel and 4 in M.

## Teaching approaches

**Plan A: lecture with live demonstration (two sessions of 90 minutes, 180 minutes in all).** It fits a lecture course with a projector and lab or home time for the tutorials. You demonstrate the steps that carry the ideas and leave the rest to students.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The scenario, the objectives and why preparation comes first | 2 to 8 |
| 1 | 5 | The destination table | 9 to 11 |
| 1 | 20 | Text functions and date functions, with the two Watch outs | 12 to 20 |
| 1 | 15 | Conditional logic, with the check and the answer | 21 to 26 |
| 1 | 30 | Tutorial 5.1: Steps 1, 3 and 5 live; students finish at home | 27 to 31 |
| 1 | 10 | Lookup functions and XLOOKUP | 32 to 34 |
| 2 | 15 | Two keys away, the first-match Watch out, the check and the answer | 35 to 38 |
| 2 | 25 | Tutorial 5.2: Steps 2, 5 and 7 live | 39 to 42 |
| 2 | 10 | Missing, meaningful and invalid values, with the check and the answer | 43 to 47 |
| 2 | 10 | Power Query for repeatable preparation | 48 to 51 |
| 2 | 20 | Tutorial 5.3: Steps 3 to 6 live | 52 to 57 |
| 2 | 10 | Looking ahead; assign the exercises | 58 to 63 |
| | 180 | Total | |

**Plan B: lab first (one session of 150 minutes).** Students build the workbook before the vocabulary, so the ideas arrive as problems they have met. It fits a computer lab. The tutorials take longer than the time allowed here, so students work in pairs and take the start file for the next tutorial when they fall behind.

| Minutes | Activity | Slides |
|---|---|---|
| 5 | Pose the scenario; ask which Tables hold the date, the group and the customer | 5 |
| 35 | Tutorial 5.1 in pairs, to the checkpoint | 28 to 31 |
| 10 | Debrief: text, date and logical functions; a clean test is a finding | 13 to 16, 18 to 20, 22 to 26 |
| 40 | Tutorial 5.2 in pairs, to the checkpoint | 40 to 42 |
| 10 | Debrief: lookups toward the one side, and the first-match Watch out | 33 to 38 |
| 40 | Tutorial 5.3 in pairs, to the checkpoint | 53 to 57 |
| 10 | Debrief: merges, join kinds and meaningful blanks; assign | 44 to 51, 58 to 63 |
| 150 | Total | |

**Plan C: flipped, with one 75-minute class.** Students read the chapter and build the three tutorials at home. It fits upper-level and graduate classes and depends on prepared students, so it opens with a quiz.

| Minutes | Activity | Slides |
|---|---|---|
| 10 | Quiz on questions 1, 3, 4, 8, 10 and 12 | |
| 15 | Review clinic: students swap workbooks and check a partner's InvoiceLines against the row count, the line total and the Documentation worksheet | 56, 57 |
| 20 | Break it: a lookup toward the many side, PROPER on supplier names, a text year compared with a number, a merge on a repeated key | 16, 36, 50 |
| 20 | Start Exercise 5.2 or 5.5 in pairs | |
| 10 | Discussion prompts 1 and 3; assign the exercises | 59 to 62 |
| 75 | Total | |

Plan A is the safest. Plan B trades the vocabulary lecture for ownership of the workbook and needs a lab. Plan C leaves no time for demonstration, so assign the merge in Tutorial 5.3, Step 3, as required reading.

## Tutorial guide

### Guided Tutorial 5.1: Adding Text, Date, and Logical Columns

**Purpose.** Students add the two attributes the invoice lines lack, the product type and the period, and the checks that protect them.

**Time.** About 45 minutes.

**Demonstrate, then hand over.** Demonstrate Step 1 (MID, with the formula bar) and Step 5 (IFS, with its last TRUE). Leave Steps 3 and 4 and the Documentation step to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1, 2 | A product type for every item; the code check | DSK for a desk and SDB for the sideboard; B40 reads 0 failures among {{ t1.items_sold }} items |
| 3 | The period labels | {{ t1.n_labels }} labels, {{ t1.first_label }} to {{ t1.last_label }} |
| 4 | DaysToDue | Whole numbers: 30, 45, 60 and 90 |
| 5 | The bands; the standard-terms test | Up to 30 days {{ t1.up30|count }}; 31 to 60 days {{ t1.mid|count }}; over 60 days {{ t1.over60|count }}; B39 reads 0 |
| 7 | Documentation | Every new column and both checks listed |

**Stumbles to expect**

- Step 1: the header typed away from the Table, so the formula does not fill.
- Step 4: the difference formatted as a date. Step 4b says to change the format.
- Step 5: bands tested out of order, or the final TRUE missing, which returns #N/A.
- Step 2: students expect failures. The zero comes from the Chapter 4 filter, not from the check.

**The checkpoint to look for.** The four bullets of the tutorial. A strong student says that the standard-terms test shows the terms conform, not who calculated the due dates.

### Guided Tutorial 5.2: Bringing Dates and Groups onto the Invoice Lines

**Purpose.** Students bring six attributes onto the lines by lookup, count the failures, reconcile the Furniture revenue to the Part I case and find the promotion lines invoiced after the end date.

**Time.** About 60 minutes. Import and the chain of lookups take longest.

**Demonstrate, then hand over.** Demonstrate Step 3 (the two-key chain, with the INDEX and MATCH form) and Step 7 (the filter and the status bar). Leave the import and the documentation to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | The SalesOrder Table | {{ t2.orders|count }} orders |
| 2 to 4 | Six lookup columns on SalesInvoiceLine | Columns {{ sil.InvoiceDate }} to {{ sil.ProductType }}, no "No match" |
| 5 | Lookups not matched | B41 reads 0 |
| 6 | Furniture revenue by quarter, {{ y }} | ${{ ch05_ex1.gross[0]|money }}; ${{ ch05_ex1.gross[1]|money }}; ${{ ch05_ex1.gross[2]|money }}; ${{ ch05_ex1.gross[3]|money }}; the last two agree with the Part I case |
| 7 | Promotion {{ t2.promo.id }} lines invoiced after {{ t2.promo.end_long }} | {{ t2.promo.after|count }} in the status bar and in B47 |
| 8 | Documentation | SalesOrder and the six columns listed, and the open question rewritten |

**Stumbles to expect**

- Step 3: the OrderDate column shows a number such as a date serial. It needs a date format.
- Step 5: the COUNTIF range covers six adjacent columns, so a student who moved a column counts the wrong cells.
- Step 6: the formula filled instead of pasted, or the labels typed with a space, so SUMIFS returns zero.
- Step 7: the Date Filters entry needs a real date. Ask students to read the OrderDate of the lines in view: every one falls inside the promotion.

**The checkpoint to look for.** The four bullets. A strong student states the finding in the tutorial's closing paragraph: revenue follows the invoice date and the promotional price follows the order date.

### Guided Tutorial 5.3: Building InvoiceLines in Power Query

**Purpose.** Students rebuild the preparation as one recorded, refreshable query and reconcile it with the lookups.

**Time.** About 60 minutes. The merges and the reconciliation take longest.

**Demonstrate, then hand over.** Demonstrate Step 2 (Reference), Step 3 (the Merge dialog, with its message and the expansion without the prefix) and Step 6b (the row count against B3). Leave the custom columns and the documentation to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | The Customer query | {{ t3.customers|count }} customers, four columns |
| 3, 4 | The merges | Each message estimates that every row matches; no rows added |
| 5 | Five custom columns | FiscalYear, FiscalQuarter, Period, ProductType and WholeQuantity |
| 6 | Rows and total | {{ t3.lines|count }} lines; ${{ t3.line_total|money }}, equal to B3 and B5 |
| 6c | Furniture revenue by quarter | The same four figures as Tutorial 5.2 |
| 6d | Lines with a fractional quantity | {{ t3.fractional|count }} of {{ t3.lines|count }}, {{ t3.fractional_share|pct(0) }} |
| 7 | Refresh | Counts and totals unchanged |

**Stumbles to expect**

- Step 3d: the prefix box left checked, so later formulas cannot find the plain names.
- Step 4c: the merge with Customer made before the CustomerID column exists. Step 3 adds it.
- Step 5: the type of each new column not set, or Text.Middle started at 5.
- Step 6a: a plain **Close & Load**, which sends the queries to the Data Model.

**The checkpoint to look for.** The four bullets. A strong student says that agreement with the lookups is consistency, not proof, and that the Furniture totals test the item group and the quarter, not the customer segment.

## Difficult ideas and misconceptions

**A lookup follows a relationship toward its one side.** Toward the many side it returns the first match and says nothing. Question 7 tempts with "no problem", and the chapter's Watch out has the case: an order with several shipments on different dates, where {{ t2.multi_ship|count }} orders have more than one shipment. Ask: which side of the relationship am I on, and what does the other table contain for this key?

{{ figure('IF-05-0-A') }}

**A merge repeats rows when the key repeats in the second table.** Merging SalesInvoice with Customer on CustomerID keeps the row count. Merging SalesInvoice with Shipment on SalesOrderID turns {{ t1.invoices|count }} invoices into {{ t2.fanout|count }} rows. Question 11 asks about it. The row count after loading tests the repetition, not the match, because a left outer merge keeps a row that finds nothing, so a left anti merge that returns no rows is the test of the match. Ask: what does each row of the result represent now?

{{ figure('IF-05-0-B') }}

**A clean test is a finding.** Tutorial 5.1's code check and Exercise 5.6's duplicate test return zero, and a student feels cheated. The result is evidence that the field is free of the problem tested, and recording it is a step. Exercise 5.6's PROPER is the mirror image: standardizing a consistent field damages it (question 2).

**Agreement of totals is not correctness.** The lookups and the query agree to the cent (Tutorials 5.2 and 5.3), and both start from the same keys. Ask: what error would leave both totals unchanged?

**Blank, missing and invalid are three different things.** A blank PromotionID is a fact, a blank TrackingNumber is a gap, and a fractional quantity for an item sold by the unit is a present value that fails its purpose (questions 8, 9 and 15). Ask what the next action is in each case.

**Excel comparisons are quiet.** Text and numbers compare unequal, text is "greater" than any number, and `=` ignores case. Exercise 5.2's text year and Exercise 5.6's `<>` fail without an error (question 14 is the cousin).

**Position counting differs.** MID counts from one and Text.Middle from zero. Question 1's option B is the off-by-one, and question 12 asks why.

## Discussion prompts

1. **What would you check first in someone else's prepared table?** A good discussion reaches the row count against the source and a total that must agree, then the documentation of each step.
2. **A lookup returns a value. How do you know it is the right row?** It reaches the key's uniqueness, the "No match" count and the side of the relationship.
3. **A test finds nothing. What do you write in the workpapers?** What was tested, on what population, that it found nothing, and what it cannot show.
4. **Why would a controller prefer the invoice date for revenue and the order date for a promotion's price?** It reaches the ledger and the moment the price was set, and the limit that an invoice date is not delivery.
5. **When is it wrong to standardize a field?** When the field is already consistent, as in Exercise 5.6, or when the change loses information.
6. **Which is better for a lasting analysis, lookup columns or a query?** Recorded steps and refresh against the transparency of formulas. Tutorial 5.3 keeps the lookups as the check.
7. **A match on an address is not proof of a related party. What else could explain it?** Employees who own or run suppliers legitimately, shared buildings, data entry errors; and what evidence tells them apart.

## Using the exercises

All six exercises are Excel builds with a model answer in Chapter05-exercises.zip, on a worksheet named after the exercise. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 5.1 Net Furniture Revenue by Quarter | Financial | Excel | 75 | Intermediate | 1, 3, 4, 5 |
| 5.2 Testing Document Numbers Against Dates | Financial | Excel | 60 | Basic | 1, 2, 3, 4, 6 |
| 5.3 The Furniture Product Mix | Managerial | Excel | 75 | Intermediate | 1, 2, 4, 6 |
| 5.4 How Long Orders Take to Be Invoiced | Managerial | Excel | 75 | Intermediate | 1, 3, 4, 6 |
| 5.5 Testing for Related-Party Suppliers | Auditing | Excel | 75 | Intermediate | 1, 2, 4, 5 |
| 5.6 Reviewing the Supplier and Item Master Files | Auditing | Excel | 100 | Advanced | 1, 2, 3, 4, 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 5.1 and 5.2, managerial students 5.3 and 5.4, auditing students 5.5 and 5.6. A swap lets each track hear the others; Exercise 5.2 is worth showing to everyone.
- *One exercise a session.* Take them in the order 5.2, 5.1, 5.3, 5.4, 5.5, 5.6, from the lightest to the longest.
- *A light load.* Exercises 5.2 and 5.5 take about 135 minutes and cover outcomes 1 to 6, with outcome 5 only through loading. Add Exercise 5.3 for the grid and the rule.

**Grading and discussion.** Each exercise guide holds a rubric. Exercises 5.1, 5.3 and 5.4 suit grading from the workbook. Exercises 5.2, 5.5 and 5.6 end in a memo and suit a class discussion of what a match or a clean result does and does not show. Collect the workbook, not a screenshot.

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 1.** Option B, -DS, is the off-by-one that a student who starts at the hyphen produces.
- **Question 2.** Option A, that PROPER leaves capitals alone, and option C, which confuses it with UPPER.
- **Question 3.** Option D, the first quarter, applies the calendar quarter to a fiscal year that starts in April.
- **Question 6.** Option A uses the line's invoice key against the SalesOrder Table, which has no such column.
- **Question 7.** Option D, "no problem", is the silent failure.
- **Question 8.** Option D, that ISBLANK is TRUE because the cell looks blank, is the visual trap.
- **Question 9.** Option B, a blank TrackingNumber on a delivered shipment, is missing information, the case the chapter sets against a meaningful blank.
- **Question 11.** Option C, blank keys that match every row, sounds technical; the repeated key is what multiplies rows.
- **Question 14.** Option B returns "Late" because the line carries a discount, and ignores the date test.
- **Question 15.** Option A, rounding every quantity, changes the data to suit the analysis.
{% if n_longest %}
- **Questions {{ longest_correct }}.** The correct option is also the longest. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1, 2, 3, 4 and 14 make a quiz of the functions, questions 5 to 7 of lookups, and questions 8 to 13 and 15 of blanks, merges and Power Query.

## Connections

**Builds on.** Chapter 2 named missing values, duplicates and the quality dimensions that the checks apply, and Tutorial 2.1 found the invoices dated before their shipments that Exercise 5.2 rediscovers. Chapter 3 gave the keys and the cardinality that tell a lookup its direction. Chapter 4 built the workbook, the Documentation worksheet and the habit of Replace current in the type step. The Part I case reconciled the Furniture revenue that Tutorial 5.2 reproduces.

**Later chapters.** Chapter 6 summarizes InvoiceLines and bridges the Furniture margin from the third to the fourth quarter. Chapter 7 forecasts from it. Chapter 8 returns to the promotion dates and the duplicate tests, and Exercise 6.1 and Exercise 12.1 return to the invoices of Exercise 5.2. Parts III and IV carry the same idea of following a key. A join in SQL combines tables in a query result, as this chapter's lookups and merges do, while a relationship in Power BI keeps the tables separate and passes filters between them.

**Appendices.** The quick reference lists every Excel and Power Query function the chapter uses. **Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard; each exercise guide names the competencies it practices.
