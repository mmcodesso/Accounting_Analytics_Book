# Chapter 5: Data Preparation and Cleaning in Excel

| | |
|---|---|
| Unit | Chapter 5: Data Preparation and Cleaning in Excel |
| Tools | Excel |
| Time | About 180 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part II, Accounting Analytics with Excel: the second Excel chapter. It turns the Chapter 4 workbook into one prepared table, InvoiceLines, that Chapters 6 and 7 analyze |
| Analytics types | None is named. The work is preparation for descriptive and diagnostic analysis, and each tutorial ends in a check |
| Tools | Excel for Windows or Microsoft 365 for Mac, with Power Query. No SQL or Power BI |
| Components | 3 guided tutorials, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 63 slides |
| Files students need | CharlesRiver.xlsx, never edited, and Charles River Furniture Analysis.xlsx as it stands at the end of Chapter 4. Chapter05-companion.zip holds the workbook at the start of Tutorials 5.1, 5.2 and 5.3 and at the end of the chapter, and Chapter05-exercises.zip the model answers. The companion files read `C:\CharlesRiver\CharlesRiver.xlsx` |
| Time | Class: about 180 minutes. Students: about two hours of reading, 45 minutes for Tutorial 5.1, 60 for Tutorial 5.2, 60 for Tutorial 5.3 and 60 to 100 for each exercise (assign two or three). The tutorial times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The Item Table keeps 223 of 266 items (those with a list price). Every kept item has a code of the form GRP-TYP-9999, so Tutorial 5.1's code check returns zero failures. The 22 codes that would fail belong to supplier services and capital items, which the Chapter 4 filter removes. The check passes because of that filter.
- Every invoice has one of four payment terms: 30, 45, 60 or 90 days. The bands of Tutorial 5.1 hold 8,368, 11,912 and 634 invoices, and no invoice fails the standard-terms test. The invoices fill the 12 quarters from 2024-Q1 to 2026-Q4.
- The lookups of Tutorial 5.2 find every match. Many orders have several shipments (3,186) and several invoices (5,209), so the direction of a lookup matters.
- 160 of the 576 lines of promotion 8, the Furniture Seasonal Promotion, are invoiced after its end date, 119 in November and 41 in December, and every one comes from an order placed while the promotion ran.
- 26,797 of 27,933 invoice lines carry a fractional quantity, which is the validity finding of Tutorial 5.3.
- The exercises add credit memos, invoices numbered for the next year or dated before their order, promotions 4 and 7 that end before they start and promotion 1 that lasts a day, suppliers that share an address with an employee, and item master fields that conflict with the sales. Each exercise guide lists its own conditions.

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
- Do the tutorials yourself and time them. Tutorial 5.2 adds six formula columns to a Table of 27,933 rows, so time the recalculation on your students' machines.
- Get the PowerPoint deck from the Downloads page. Its modules follow the chapter's sections.

**Pitfalls that cost class time**

- **The first empty cell.** A new column starts in the first empty cell right of the last header, or it does not join the Table. On the Item Table the new columns are L and M, on SalesInvoice M to R, and on SalesInvoiceLine the lookups of Tutorial 5.2 run from R to W. Step 5 of Tutorial 5.2 counts "No match" over those six adjacent columns, so a column inserted between them is counted too.
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
| 1, 2 | A product type for every item; the code check | DSK for a desk and SDB for the sideboard; B40 reads 0 failures among 223 items |
| 3 | The period labels | 12 labels, 2024-Q1 to 2026-Q4 |
| 4 | DaysToDue | Whole numbers: 30, 45, 60 and 90 |
| 5 | The bands; the standard-terms test | Up to 30 days 8,368; 31 to 60 days 11,912; over 60 days 634; B39 reads 0 |
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
| 1 | The SalesOrder Table | 5,819 orders |
| 2 to 4 | Six lookup columns on SalesInvoiceLine | Columns R to W, no "No match" |
| 5 | Lookups not matched | B41 reads 0 |
| 6 | Furniture revenue by quarter, 2026 | $4,354,122.83; $4,600,820.85; $4,283,322.86; $4,156,787.84; the last two agree with the Part I case |
| 7 | Promotion 8 lines invoiced after October 31, 2026 | 160 in the status bar and in B47 |
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
| 1 | The Customer query | 220 customers, four columns |
| 3, 4 | The merges | Each message estimates that every row matches; no rows added |
| 5 | Five custom columns | FiscalYear, FiscalQuarter, Period, ProductType and WholeQuantity |
| 6 | Rows and total | 27,933 lines; $86,446,845.84, equal to B3 and B5 |
| 6c | Furniture revenue by quarter | The same four figures as Tutorial 5.2 |
| 6d | Lines with a fractional quantity | 26,797 of 27,933, 96% |
| 7 | Refresh | Counts and totals unchanged |

**Stumbles to expect**

- Step 3d: the prefix box left checked, so later formulas cannot find the plain names.
- Step 4c: the merge with Customer made before the CustomerID column exists. Step 3 adds it.
- Step 5: the type of each new column not set, or Text.Middle started at 5.
- Step 6a: a plain **Close & Load**, which sends the queries to the Data Model.

**The checkpoint to look for.** The four bullets. A strong student says that agreement with the lookups is consistency, not proof, and that the Furniture totals test the item group and the quarter, not the customer segment.

## Difficult ideas and misconceptions

**A lookup follows a relationship toward its one side.** Toward the many side it returns the first match and says nothing. Question 7 tempts with "no problem", and the chapter's Watch out has the case: an order with several shipments on different dates, where 3,186 orders have more than one shipment. Ask: which side of the relationship am I on, and what does the other table contain for this key?

![Which way a lookup may follow a relationship, and what to use instead when the other table is on the many side.](../figures/chapter-05-data-preparation/IF-05-0-A.pdf)

**A merge repeats rows when the key repeats in the second table.** Merging SalesInvoice with Customer on CustomerID keeps the row count. Merging SalesInvoice with Shipment on SalesOrderID turns 20,914 invoices into 41,408 rows. Question 11 asks about it. The row count after loading tests the repetition, not the match, because a left outer merge keeps a row that finds nothing, so a left anti merge that returns no rows is the test of the match. Ask: what does each row of the result represent now?

![The row-count test for a merge, and what a repeated key in the second table does to it.](../figures/chapter-05-data-preparation/IF-05-0-B.pdf)

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

Key: 1 D, 2 B, 3 A, 4 C, 5 B, 6 D, 7 C, 8 A, 9 D, 10 C, 11 B, 12 A, 13 C, 14 A, 15 B.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | D | MID returns 3 characters starting at position 5, the product type DSK. |
| 2 | B | PROPER capitalizes the first letter of each word and lowers the rest, so LLC becomes Llc. |
| 3 | A | with a fiscal year starting April 1, January to March is the fourth quarter. |
| 4 | C | TODAY changes when the workbook recalculates on a later day, so the results cannot be reproduced, while an as-of date is fixed. |
| 5 | B | the fourth argument is the value returned when the key is not found. |
| 6 | D | the order date is two keys away: invoice first, then order. |
| 7 | C | a lookup returns the first match; on the many side, MINIFS returns the earliest date. |
| 8 | A | ISBLANK is FALSE for a cell that holds a formula, even one that returns empty text. |
| 9 | D | a blank PromotionID records the fact that the line carried no promotion. |
| 10 | C | a left anti join returns the rows of the first query with no match in the second. |
| 11 | B | a key repeated in the second table makes a left outer merge add rows once the merged column is expanded. |
| 12 | A | Text.Middle counts positions from zero, MID from one. |
| 13 | C | a reference query leaves the original unchanged and is rebuilt from its result on every refresh. |
| 14 | A | AND needs both tests true; the invoice date is before PromoEnd, so the result is OK. |
| 15 | B | record the limitation, raise it with the system owners, and avoid conclusions that need whole units. |

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

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1, 2, 3, 4 and 14 make a quiz of the functions, questions 5 to 7 of lookups, and questions 8 to 13 and 15 of blanks, merges and Power Query.

## Connections

**Builds on.** Chapter 2 named missing values, duplicates and the quality dimensions that the checks apply, and Tutorial 2.1 found the invoices dated before their shipments that Exercise 5.2 rediscovers. Chapter 3 gave the keys and the cardinality that tell a lookup its direction. Chapter 4 built the workbook, the Documentation worksheet and the habit of Replace current in the type step. The Part I case reconciled the Furniture revenue that Tutorial 5.2 reproduces.

**Later chapters.** Chapter 6 summarizes InvoiceLines and bridges the Furniture margin from the third to the fourth quarter. Chapter 7 forecasts from it. Chapter 8 returns to the promotion dates and the duplicate tests, and Exercise 6.1 and Exercise 12.1 return to the invoices of Exercise 5.2. Parts III and IV carry the same idea of following a key. A join in SQL combines tables in a query result, as this chapter's lookups and merges do, while a relationship in Power BI keeps the tables separate and passes filters between them.

**Appendices.** The quick reference lists every Excel and Power Query function the chapter uses. **Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard; each exercise guide names the competencies it practices.
