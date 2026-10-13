# Chapter 4: Excel Essentials for Accounting Analytics

| | |
|---|---|
| Unit | Chapter 4: Excel Essentials for Accounting Analytics |
| Tools | Excel |
| Time | About 180 minutes of class time |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part II, Accounting Analytics with Excel: the first Excel chapter. It builds the workbook the rest of Part II extends |
| Analytics types | None is named. The controller's question is diagnostic, but the work here is descriptive (control totals, summaries, counts) and sets the question up for Chapter 5 |
| Tools | Excel for Windows or Microsoft 365 for Mac, with Power Query. No SQL or Power BI |
| Components | 3 guided tutorials, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 63 slides |
| Files students need | CharlesRiver.xlsx, never edited. Tutorial 4.1 creates Charles River Furniture Analysis.xlsx. Chapter04-companion.zip holds the workbook at the start of Tutorials 4.2 and 4.3 and at the end of the chapter, and Chapter04-exercises.zip holds the model answers. The companion files read `C:\CharlesRiver\CharlesRiver.xlsx` |
| Time | Class: about 180 minutes. Students: about two hours of reading, 50 to 60 minutes for Tutorial 4.1, 35 to 40 for Tutorial 4.2, 45 for Tutorial 4.3, and 60 to 90 minutes for each exercise (assign two or three) |

The chapter depends on these conditions of the data:

- The invoice lines (27,933) belong to 20,914 invoices, and the lines add up to the invoice subtotals ($86,446,845.84), so Tutorial 4.1's control total difference is zero.
- Power Query types a column from its first 200 rows. The first 200 invoice lines carry no promotion, so Discount can arrive as a whole number, and FreightAmount is whole on the first 200 invoices and fractional later.
- 223 of the 266 items have a list price and are kept. The 9 promotion programs run at three rates, and promotion 8, the Furniture Seasonal Promotion, has the most lines (576) and the most discount dollars ($296,053.57).
- Promotions 1, 4, and 7 end on or before their start dates. Exercise 4.2 asks students to report these as questions, not to correct them, and Chapter 8 and the Part II case return to them.
- The exercises add a shipment extract with blank tracking numbers and stale In Transit statuses, and a price override table with 3 Pending requests and one approver. Each exercise guide lists its own conditions.

## What students should be able to do afterward

1. Explain why a workbook's structure is a control, citing the spreadsheet error research. Practiced in the Documentation worksheet of Tutorial 4.3, Exercise 4.1 (5), Exercise 4.5 (2), and questions 13 and 14.
2. Build an analysis workbook with Power Query, Tables, structured references and calculated columns. Practiced in Tutorial 4.1, Exercises 4.2 to 4.6, and questions 1, 3, 6 and 7.
3. Use relative, absolute and mixed references and named cells to build a grid from one formula. Practiced in Tutorial 4.2, Exercises 4.1, 4.2, 4.4 and 4.6, and questions 4, 5 and 15.
4. Explore transaction data with sorts, filters, slicers and SUBTOTAL. Practiced in Tutorial 4.3, Exercises 4.3 to 4.6, and questions 2, 8 and 9.
5. Surface exceptions with conditional formatting and protect inputs with data validation. Practiced in Tutorial 4.3, Exercises 4.1 to 4.6, and questions 10, 11 and 12.
6. Organize and document a workbook so a reviewer can trace each number. Practiced in Tutorial 4.3 (Steps 7 to 9), Exercises 4.2, 4.5 and 4.6 (the memos), and question 14.

## Preparing to teach

**Before the first class**

- Students need desktop Excel with Power Query. On a Mac the Power Query Editor requires Excel for Microsoft 365, and the commands sit in different places. Excel for the web will not do: the workbook is too large. XLOOKUP is used in Exercises 4.2, 4.4 and 4.6 and in every model answer, so check versions.
- CharlesRiver.xlsx must be the downloaded master, unchanged. Chapter 4 reads it through Power Query, so students do not open it. Tutorial 4.1 saves the new workbook beside it. The start files read `C:\CharlesRiver\CharlesRiver.xlsx`; a student who uses one must choose **Data > Get Data > Data Source Settings**, **Change Source**, and then **Data > Refresh All**.
- Do Tutorial 4.1 yourself and time the import and the first refresh. Decide whether late students take the start files: Tutorials 4.2 and 4.3 each begin from the previous tutorial's workbook.
- Get the PowerPoint deck from the Downloads page. Its modules follow the chapter's sections, and the three tutorial modules show each step list with the figures.

**Pitfalls that cost class time**

- **The 200-row type trap.** If Discount is typed as a whole number, DiscountAmount is zero on every line, and Tutorial 4.2's grid puts all 27,933 lines in the 0 column. The fix is **Replace current** in the Changed Type step, not **Add new step**.
- **Typing next to a Table.** The Table grows. Keep summaries on their own worksheets.
- **The rule's column letter.** In the SalesInvoiceLine Table with every column kept, Discount is column J, which is what Tutorial 4.3's rule uses. A student who removed columns has another letter, and A2 must be the active cell when the rule is written.

## Teaching approaches

**Plan A: lecture with live demonstration (two sessions of 90 minutes, 180 minutes in all).** It fits a lecture course with a projector and a lab or home time for the tutorials. You demonstrate the steps that carry the ideas and leave the rest to students.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The opening scenario, objectives, "build it to hand to someone else" | 2 to 5 |
| 1 | 10 | Why structure matters; structure is a control | 6 to 8 |
| 1 | 15 | Tables, structured references and the Watch out | 9 to 14 |
| 1 | 10 | Power Query and the type check | 15 to 17 |
| 1 | 35 | Tutorial 4.1: demonstrate Steps 2 to 6, 9 and 10; students finish at home | 18 to 24 |
| 1 | 10 | Cell references and the check and answer slides | 25 to 29 |
| 2 | 5 | Named cells | 30 |
| 2 | 25 | Tutorial 4.2: Steps 1 to 3 live, the grid by paste | 31 to 35 |
| 2 | 15 | Sorting, filters, slicers and SUBTOTAL, with the check and answer | 36 to 40 |
| 2 | 15 | Conditional formatting and data validation | 41 to 47 |
| 2 | 10 | Layers and documentation, with the check and answer | 48 to 52 |
| 2 | 15 | Tutorial 4.3: Steps 1, 2, 4 and 5 live, then the documentation | 53 to 57 |
| 2 | 5 | Looking ahead; assign the exercises | 58 to 63 |
| | 180 | Total | |

**Plan B: lab first (one session of 150 minutes).** Students build the workbook before the vocabulary, so the ideas arrive as problems they have met. It fits a computer lab, and it needs a start file for students who fall behind.

| Minutes | Activity | Slides |
|---:|---|---|
| 5 | Pose the scenario; ask what would make students trust someone else's workbook | 5 |
| 50 | Tutorial 4.1 in pairs, to the checkpoint | 19 to 24 |
| 10 | Debrief: Tables, structured references and what the control total cannot show | 10 to 17, 24 |
| 10 | Mini-lecture: references, the fill Watch out, named cells | 26 to 30 |
| 30 | Tutorial 4.2, to the checkpoint | 32 to 35 |
| 35 | Tutorial 4.3, to the checkpoint | 54 to 57 |
| 10 | Debrief: documentation and validation limits; assign | 49 to 52, 58 to 63 |
| 150 | Total | |

**Plan C: flipped, with one 75-minute class.** Students read the chapter and build the three tutorials at home. It fits upper-level and graduate classes and depends on prepared students, so it opens with a quiz.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Quiz on questions 2, 4, 5, 10, 11 and 12 | |
| 15 | Review clinic: students swap workbooks and trace one number on the Analysis worksheet to its source using only the Documentation worksheet | 49, 50 |
| 20 | Break it: type beside a Table, fill instead of paste, paste over a validation, filter with This Quarter | 14, 29, 37, 47 |
| 20 | Start Exercise 4.1 or 4.5 in pairs: build the parameter cell and its validation | |
| 10 | Discussion prompts 1 and 2; assign the exercises | 62 |
| 75 | Total | |

Plan A is the safest. Plan B trades the vocabulary lecture for ownership of the workbook and needs a lab. Plan C leaves no time for the demonstrations, so assign Tutorial 4.1, Step 6 as required reading.

## Tutorial guide

### Guided Tutorial 4.1: Building the Furniture Analysis Workbook with Power Query

**Purpose.** Students build the workbook the rest of Part II extends: four Tables imported, filtered and typed, two calculated columns, and control totals.

**Time.** About 50 to 60 minutes. The Navigator and the type check take longest.

**Demonstrate, then hand over.** Demonstrate Steps 2 to 6 (the Navigator, **Transform Data**, **Applied Steps**, and the type icons) and Step 10, and read the difference cell aloud. Leave Steps 1, 7 to 9 and 11 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2 | Four Tables selected | T16_SalesInvoice, T17_SalesInvoiceLine, T44_Item and T7_PromotionProgram |
| 4, 5 | The Item query | 223 items of 266, with 11 columns kept |
| 6 | Types in Changed Type | Dates as Date; FreightAmount and Discount as Decimal Number, set with **Replace current** |
| 7 | Rows loaded | 20,914 invoices, 27,933 lines, 223 items and 9 programs |
| 9 | Calculated columns | ListAmount in column P and DiscountAmount in column Q |
| 10 | Control totals | Lines 27,933; invoices 20,914; line total $86,446,845.84; invoice subtotal $86,446,845.84; difference 0; discount taken $723,253.29; list amount $97,215,747.18 |
| 11 | Refresh | Row counts and totals unchanged, calculated columns still filled |

**Stumbles to expect**

- Step 6: students skip the check, then see a zero discount. Ask them to read the type icon before loading.
- Step 7: the plain **Close & Load**, which loads several new queries to the Data Model. Use **Close & Load To**, **Table** and **New worksheet**.
- Step 9: the new column header typed away from the Table, so it does not join it. It must be in the first empty cell right of the last header.
- Step 10: students read the zero difference as proof that nothing is missing. Remove one invoice and its lines in a thought experiment and ask what the difference shows.

**The checkpoint to look for.** Four data worksheets and an Analysis worksheet, a difference of zero, a list amount well above the line total, and a discount that is small but not zero. A strong student also says what the zero does not show.

### Guided Tutorial 4.2: Parameters, Named Cells, and a Summary Grid

**Purpose.** Students name a parameter, derive a threshold from the data, and fill a two-way grid from one formula with mixed references.

**Time.** About 35 to 40 minutes.

**Demonstrate, then hand over.** Demonstrate Steps 1 to 3, changing the percentile to 0.95 and watching the threshold and the large-line measures move, then putting it back. Leave the grid to students, with the paste rule from the Watch out.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2 | Large-line threshold at 0.9 | $7,104.62, the 90th percentile of LineTotal |
| 3 | Large lines; their share of the line total | 2,794; 30.7% |
| 3d | At 0.95 | threshold $8,695.30, 1,397 large lines |
| 5, 6 | The grid | Rows Approved Override, Base List, Customer Price List and Segment Price List; columns 0, 0.08, 0.1 and 0.12; totals by column 25,825, 222, 1,235, 651; grand total 27,933 |
| 7 | Shares | Segment Price List with no discount 81.6%; the block adds to 100 percent |

**Stumbles to expect**

- Step 1: the name typed in the cell, not the **Name Box**, or a name with a space.
- Step 4: a pricing method spelled differently from the data, so the grid total does not equal the lines.
- Step 5: the fill handle instead of copy and paste. Ask students to click E19 and read the formula bar.
- Step 3f: students forget to put the percentile back to 0.9.

**The checkpoint to look for.** The grid total equals the number of invoice lines and the shares add to 100 percent. A good answer reads the grid: a promotion is a discount on top of a price, so Base List alone has no discounted lines.

### Guided Tutorial 4.3: Surfacing Promotions and Documenting the Workbook

**Purpose.** Students protect the parameter, shade the promotion lines, sort and slice them, measure the lines in view, and document the workbook so a reviewer can follow it.

**Time.** About 45 minutes. The documentation step is the one students rush.

**Demonstrate, then hand over.** Demonstrate Step 2 (select from A2 with A2 active) and Step 5 (SUM beside SUBTOTAL while clicking slicer buttons). Leave validation, sorting and the documentation to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | A validated parameter | 1.5 is refused; the input message shows on selection |
| 2 | Shaded rows | 2,108 lines with a discount, the promotion lines, scattered through the Table |
| 3 | After the sort | Promotion lines first, by promotion; blank PromotionID at the bottom |
| 4 | The slicer | One button for each promotion and a blank button covering 25,825 lines |
| 5 | SUBTOTAL against SUM | The discount, all lines, stays at $723,253.29 while the SUBTOTAL cells follow the slicer |
| 6 | Promotion 8 | PROMO-2026-008, Furniture Seasonal Promotion, 10%, September 1, 2026 to October 31, 2026; 576 lines and $296,053.57, 40.9% of all discount dollars |
| 7, 8 | The Documentation worksheet | Eleven labels from Purpose to Open questions, with the open question naming promotion 8 |

**Stumbles to expect**

- Step 2: the rule written with another active cell, or the wrong column letter, so the shading is off.
- Step 4: the slicer buried under the Table. Move it beside the data.
- Step 5: students expect the SUM to follow the slicer.
- Step 8: a documentation sheet that says "done". Ask what a reviewer who never met the preparer would still need.
- Step 9: saving on the wrong worksheet. Excel opens the workbook where it was saved.

**The checkpoint to look for.** The four bullets of the tutorial. A strong student adds that the promotion is only a clue: no invoice date or item group is on the lines yet.

## Difficult ideas and misconceptions

**A zero difference is not completeness.** Tutorial 4.1 compares two Tables that came through the same import. If an invoice and all its lines were dropped, the difference would still be zero. Only evidence from outside the import, such as the row count of the source Table, can show that nothing is missing. Ask: what would have to be true for the difference to be zero and the import to be wrong?

> **[Figure placeholder IF-04-0-B]** Why a zero difference in a control total does not show that the import is complete.
> Kind: diagram · Shows: Two boxes, the SalesInvoice Table and the SalesInvoiceLine Table, each drawn as a short stack of rows with one invoice and its lines missing from both. Between them a cell shows the difference of the two totals as zero. On the left, in dashed amber, a third box, the source Table in CharlesRiver.xlsx, with a count of its rows compared with the count in the import. A caption says that agreement inside the import cannot reveal what both sides lack. · Data: No values; the structure of Tutorial 4.1, Step 10 and the Control total key term. · Status: planned

**Filling is not copying.** A structured reference moves to the next column of the Table when filled across, with no error. In Tutorial 4.2 a COUNTIFS on the PricingMethod column drifts to ListAmount. In Exercise 4.4 the grid's amounts are not adjacent (FreightCost is column J, then BillableFreightAmount, FreightTerms and FreightMargin), so a fill gives text in the last column. Ask: where did this formula come from?

> **[Figure placeholder IF-04-0-A]** What a fill across does to a structured reference, and the two ways to avoid it.
> Kind: excel-mock · Shows: The right edge of the SalesInvoiceLine Table with the headers Discount, PromotionID and PricingMethod, then ListAmount and DiscountAmount. Below it three grid cells, each with its formula bar. The first holds a COUNTIFS on the PricingMethod column. The second is the same formula after a fill one column to the right, and its formula bar names the next column of the Table. The third is the pasted formula, which still names PricingMethod. A note shows the locked form that stays put when filled. · Data: The SalesInvoiceLine Table and the grid of Tutorial 4.2; the Table's own column names only. · Status: planned

**A filter hides rows; it does not remove them from a formula.** Question 2 tempts with a conditional SUMIFS and with a formula that uses `[@LineTotal]` outside the Table. Exercise 4.3 and 4.5 show it: COUNTIFS counts hidden rows, SUBTOTAL does not. Ask: which cells on this sheet change when I click the slicer?

**Date filters count from today.** Question 8 tempts with "no dates in the last quarter". Relative filters are measured from today, so a historical extract needs explicit dates, which is why Exercise 4.5 names a review date.

**A rule needs its active cell and its dollar sign.** A formula rule is written for the active cell and adjusted for every other cell. Question 10 tempts with "all references must be absolute" and with the claim that the dollar sign limits the rule to column J. Questions 11 and 12 test the rule order and the Warning style.

**Validation guards typing, not data.** Pasted values, fills and formula results pass without an alert. Question 12 tempts with the opposite claim, that validation checks only pasted values.

**Blank is not approved by someone else.** In Exercise 4.6, a formula that tests only the approver counts the 3 Pending requests, whose approver is blank, as approvals by someone else. Ask: what does Status say?

## Discussion prompts

1. **What would make you trust a workbook someone else built?** A good discussion reaches that trust comes from visible structure (source, steps, parameters, checks), not from appearance.
2. **A control total's difference is zero. What can you say, and what can't you?** The two Tables agree with each other. Completeness needs an outside count or a gap test, which Chapter 8 introduces.
3. **Where is each assumption in your workbook?** A good answer finds named, validated cells on one worksheet, with a description and a reviewer who can change one and watch the results move.
4. **Highlighting found the exceptions. Where do you record them?** In a flag column, a COUNTIFS total or a filtered list, because color alone cannot be counted or printed reliably.
5. **A validation rule is on a parameter. When does it not protect you?** When a value is pasted or filled, when the style is Warning, and when a formula produces the value.
6. **Why import with Power Query instead of copying the data?** The source is never changed, the steps are recorded, and a refresh repeats them. The cost is a dependence on the source's location.
7. **A clean test result: is it a finding?** Yes. Exercise 4.2's rate test shows each line carries its program's rate, not that it was billed inside the program's dates; the memo says so.

## Using the exercises

All six exercises are Excel builds with a model answer in Chapter04-exercises.zip, on a worksheet named after the exercise. The outcome column uses the numbers of the list at the top of this note.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 4.1 A Billing Schedule by Fiscal Year | Financial | Excel | 75 | Intermediate | 1, 3, 5 |
| 4.2 Reviewing Promotional Discounts | Financial | Excel | 60 | Basic | 2, 3, 5, 6 |
| 4.3 List-Price Margins by Product Group | Managerial | Excel | 75 | Intermediate | 2, 4, 5 |
| 4.4 Freight Billed Versus Freight Incurred | Managerial | Excel | 75 | Intermediate | 2, 3, 4, 5 |
| 4.5 A Refreshable Shipment Exception Report | Auditing | Excel | 90 | Advanced | 2, 4, 5, 6 |
| 4.6 Reviewing Price Override Approvals | Auditing | Excel | 90 | Advanced | 2, 3, 4, 5, 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 4.1 and 4.2, managerial students 4.3 and 4.4, auditing students 4.5 and 4.6. A swap lets each track hear the others; Exercise 4.5 is worth showing to everyone.
- *One exercise a session.* Take them in the order 4.2, 4.1, 4.3, 4.4, 4.5, 4.6, from the lightest to the longest.
- *A light load.* Exercises 4.2 and 4.5 take about 150 minutes and cover outcomes 2 to 6. Add Exercise 4.1 for the grid and outcome 1.

**Grading and discussion.** Each exercise guide holds a rubric. Exercises 4.1, 4.3 and 4.4 suit grading from the workbook, since the formulas are the evidence. Exercises 4.2, 4.5 and 4.6 end in a memo and suit a class discussion of what a clean or odd result does and does not show. Collect the workbook, not a screenshot. The exercises work in a copy of the analysis workbook, and Exercises 4.5 and 4.6 in a new one.

## Multiple-choice questions

Key: 1 C, 2 A, 3 B, 4 D, 5 C, 6 B, 7 A, 8 D, 9 B, 10 A, 11 C, 12 D, 13 A, 14 B, 15 C.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | C | a Table lets formulas use Table and column names, and it includes rows added later. |
| 2 | A | SUBTOTAL with 109 sums only the rows a filter leaves visible. |
| 3 | B | \[@Quantity\] is the Quantity in the formula's own row. |
| 4 | D | \$C\$500 locks both the column and the row, so it is absolute. |
| 5 | C | pasting one column right moves B\$15 to C\$15, while \$A16 stays in column A. |
| 6 | B | a refresh repeats every applied step on the source, which is never changed. |
| 7 | A | a Table already defines its header row and extent. |
| 8 | D | relative date filters are measured from today's date, not from the data. |
| 9 | B | a slicer filters the Table, hiding the other rows without deleting them. |
| 10 | A | the dollar sign fixes the column while the row adjusts, so each row is tested on its own value. |
| 11 | C | a new rule goes to the top of the list and wins when two rules set the same property. |
| 12 | D | the Warning style only cautions the user, who can accept an invalid entry. |
| 13 | A | a formula typed beside a Table extends it; summaries belong on a separate worksheet. |
| 14 | B | documentation lets someone with no connection to the work understand and review it. |
| 15 | C | a threshold derived from the data and stated in one named place updates with the data and shows its logic. |

**Questions where a wrong option tempts**

- **Question 2.** A conditional SUMIFS (B) looks like it respects a filter, and a count (C) is the wrong function. SUBTOTAL is the one that sees only the visible rows.
- **Question 5.** The option that changes nothing (B) tempts students who forget that a paste adjusts the unlocked part. The right answer moves the column of B$15 only.
- **Question 10.** The option that limits the rule to column J (D) confuses the dollar sign with the range the rule applies to.
- **Question 11.** The option that the first rule always wins (A) is the reverse of Excel's behavior: a new rule goes to the top of the list.
- **Question 12.** The option that validation checks only pasted values (C) reverses the limit. Typed values are checked, pasted ones are not.
- **Question 14.** The option that accounting standards require a documentation worksheet (D) overstates: the PCAOB standard is about audit documentation.
- **Questions 1, 6, 8, 9, 12, 13, and 15.** The correct option is also the longest. If you grade with these, ask students to explain their answer or reword the options.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 3, 4, 5 and 10 make a good quiz of the referencing ideas, questions 2, 8, 9 and 12 of filters and validation, and 1, 6, 7 and 13 to 15 of the structure and Power Query ideas.

## Connections

**Builds on.** Chapter 1 introduced the controller's question and the dataset. Chapter 2 treated tests such as blank values and stale statuses as data quality tests, and Tutorial 2.1's filters become Exercise 4.5's exception report. Chapter 3 gave the Table names (a number and the database table) and the keys the exercises' lookups use. The Part I case ends with the data readiness memo that opens this chapter.

**Later chapters.** Chapter 5 combines the invoice lines with the invoices, items and customers into one table in this workbook. Chapter 6 measures the Furniture bridge that promotion 8 starts. Chapter 8 adds the gap tests that Tutorial 4.1 points to. The Part II case applies the same techniques in a new workbook, and Part IV carries slicers and Validation pages into Power BI.

**Appendices.** The quick reference lists every Excel function the chapter uses. **Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard; each exercise guide names the competencies it practices.
