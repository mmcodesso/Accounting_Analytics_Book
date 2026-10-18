# Chapter 3: The Accounting Data Environment

| | |
|---|---|
| Unit | Chapter 3: The Accounting Data Environment |
| Tools | Workbook browsing and written work |
| Time | About 150 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part I, Foundations of Accounting Analytics: the third of three chapters, followed by the comprehensive case that closes the Part |
| Analytics types | None is named. The chapter is about structure, and the tests students run (does this key exist, how many rows does it find) are descriptive |
| Tools | Reading ER diagrams (Tutorial 3.1). Excel in the working copy: filters, and for some exercises XLOOKUP or COUNTIFS and a PivotTable. No SQL or Power BI |
| Components | 2 guided tutorials, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 61 slides |
| Files students need | CharlesRiver_Work.xlsx, the working copy that Tutorial 2.1 makes from CharlesRiver.xlsx. The Downloads table lists no start files and no solutions for Chapter 3; the guides in this folder hold the model answers |
| Time | Class: about 150 minutes. Students: about two hours of reading, 30 minutes for Tutorial 3.1, 45 to 60 for Tutorial 3.2, and 60 to 90 minutes for each exercise (assign two or three) |

The chapter depends on these conditions of the data:

- The database has 82 tables, each with one integer surrogate key in its first column and no declared foreign keys, so every relationship is logical and has to be tested. The file declares three types (INTEGER, REAL and TEXT): dates are text and flags are 0 and 1.
- Unique indexes protect OrderNumber, InvoiceNumber, EntryNumber and AccountNumber, but not PurchaseInvoice.InvoiceNumber, which is the supplier's own number.
- The 12 foreign keys of Exercise 3.6 have 0 orphaned values. One source type of the trace has exceptions: 6 ledger rows typed PayrollPayment point to payments that do not exist. The trace is also ambiguous without its type: the key of the traced invoice, 7947, finds 38 ledger rows of 11 source types.
- 9 customers have no orders (all inactive), 12 items with a list price were never ordered, 439 invoice lines (design services) have no shipment line, and 9 shipment lines were never invoiced.
- GLEntry has 815,921 rows and is the largest worksheet, so it filters slowly. The sale of Tutorial 3.2 exists as the chapter tells it: invoice SI-2025-007947 for Sullivan-Mcdonald, one of 8 invoices of order SO-2024-001697.

## What students should be able to do afterward

These outcomes are this guide's own. They follow the chapter's six learning objectives in order, outcome 1 serving objective 1 and so on, each stated with what practices it.

1. Explain how the database stores accounting data: tables, rows, columns, and the three types that the SQLite file declares, with dates as text, flags as 0 and 1, and NULL for a missing value. Practiced in questions 13 and 14 and in the data dictionary of Exercise 3.2.
2. Name the primary key of a table and the foreign keys that connect it, and say which relationships the file declares (none) and which the data follow. Practiced in Tutorial 3.1 (Steps 2 and 3), Exercises 3.1, 3.2, 3.4, 3.5 and 3.6, and questions 1, 2, 8 and 9.
3. Read an ER diagram: the tables, the keys, and the cardinality and optionality at both ends of a line. Practiced in Tutorial 3.1 and Exercises 3.2, 3.3 and 3.4, and questions 3 and 4.
4. Map the chart of accounts, the ledger and the sub-ledgers to tables, and say what a join does to the rows. Practiced in Tutorial 3.2 (Steps 4 and 5), Exercises 3.1 and 3.2, and questions 6, 7, 10 and 11.
5. Compare simple and complex table groups and follow a bridge key across them. Practiced in Exercises 3.3, 3.4 and 3.5, and questions 5 and 15.
6. Use SourceDocumentType, SourceDocumentID and SourceLineID to trace a ledger row to its document, and explain why that link is tested rather than declared. Practiced in Tutorial 3.2, Exercises 3.1, 3.5 and 3.6, and question 12.

## Preparing to teach

**Before the first class**

- Tutorial 3.2 and Exercises 3.1, 3.4 and 3.6 work in CharlesRiver_Work.xlsx, the copy that Tutorial 2.1 makes. A student without it must copy CharlesRiver.xlsx now, because the downloaded workbook has to stay as provided for Parts II and IV.
- Tutorial 3.1 is done on a figure. Print or share Figures 3.4, 3.7, 3.8 and 3.9 large enough to read the symbols; the deck enlarges the two halves of Figure 3.7.
- Do Tutorial 3.2 yourself. It crosses twelve worksheets, and the filter on GLEntry (815,921 rows) is the slow step, so time it.
- Check that students' Excel has XLOOKUP, which Exercise 3.6 offers beside COUNTIFS. An older perpetual version may lack it.
- Get the PowerPoint deck from the Downloads page. Its module slides follow the chapter's sections and every slide has talk-track notes.

**Pitfalls that cost class time**

- **AccountID is not the account number.** In Tutorial 3.2 the revenue row is AccountID 42, which is account 4010. Exercise 3.6 shows the same error as a false orphan.
- **Filtering SourceDocumentID alone.** The demonstration worth doing live: filter GLEntry on SourceDocumentID 7947 and read 38 rows of 11 types, then add SourceDocumentType SalesInvoice and read four.
- **Filters left on.** The tutorial moves through twelve worksheets; ask students to clear each filter before leaving it. Tell them to type a key into the filter's search box rather than scroll a long list.
- **A clean result.** Every integrity test in Exercise 3.6 finds nothing. Say early that a test that finds nothing is a finding the memo must record, as in Chapter 2.

## Teaching approaches

**Plan A: lecture with live demonstrations (two sessions of 75 minutes, 150 minutes in all).** It fits a lecture course with a projector and uses the whole deck. The first session is vocabulary and the second is the two tutorials.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The opening scenario; objectives; records become tables | 2 to 7 |
| 1 | 10 | The relational model, data types and the first Watch out | 8 to 11 |
| 1 | 20 | Keys and relationships; the check and answer slides | 12 to 16 |
| 1 | 20 | Cardinality and the fan-out; the check and answer slides | 17 to 21 |
| 1 | 15 | ER diagrams and crow's foot symbols | 22 to 24 |
| 2 | 5 | The chart of accounts, the ledger and the trace | 25 to 28 |
| 2 | 10 | Table groups: Master Data, Order-to-Cash, Manufacturing | 29 to 32 |
| 2 | 15 | Tutorial 3.1: demonstrate Step 4, students do the rest, then the checkpoint | 33 to 38 |
| 2 | 10 | The Accounting Core; the trace is not a foreign key | 39 to 44 |
| 2 | 25 | Tutorial 3.2: demonstrate Steps 1, 2 and 4, students trace, then the checkpoint | 45 to 50 |
| 2 | 10 | Patterns across groups, the check slide, the summary; assign exercises | 51 to 61 |
| | 150 | Total | |

**Plan B: lab first (one session of 120 minutes).** Students follow a real sale before they meet the vocabulary, so the keys arrive as something they have used. It fits a computer lab. Pair students whose workbook opens slowly.

| Minutes | Activity | Slides |
|---:|---|---|
| 5 | Pose the opening scenario; students list the tables they expect to hold furniture revenue | 5 |
| 45 | Tutorial 3.2 in pairs, to the checkpoint | 45 to 50 |
| 10 | Debrief: the keys they followed, then the trace columns and why the trace is not a foreign key | 13, 14, 28, 43, 44 |
| 20 | Tutorial 3.1 in pairs, to the checkpoint | 33 to 38 |
| 15 | Mini-lecture: cardinality, optionality and the fan-out | 17 to 24 |
| 10 | Table groups and the Accounting Core | 29 to 32, 39 to 42 |
| 10 | Start Exercise 3.6: list the relationships and test the first two | |
| 5 | Assign exercises | 60 |
| 120 | Total | |

**Plan C: flipped, with one 75-minute class.** Students read the chapter and do both tutorials at home. It fits upper-level and graduate classes and depends on students arriving prepared, so open with a quiz.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval quiz on questions 2, 3, 4, 8, 10 and 12 | |
| 20 | Read-aloud workshop: groups read a half of Figure 3.7 in both directions, then settle the check slides | 20, 21, 36, 37 |
| 20 | Trace clinic: students bring their key chain from Tutorial 3.2; demonstrate the type-and-key filter and count the documents behind one sale | 43, 44, 47 to 50 |
| 15 | Start Exercise 3.6 in pairs: choose six relationships and write the test for each | |
| 10 | Discussion prompts 1 and 3; assign exercises | 60 |
| 75 | Total | |

Plan A is the safest. Plan B costs the vocabulary lecture but makes the junction tables and the trace memorable, and it needs a lab. Plan C leaves no time for the fan-out, so assign question 10 and the Watch out as reading.

## Tutorial guide

### Guided Tutorial 3.1: Reading the Charles River O2C Entity-Relationship Diagram

**Purpose.** Students read, rather than build. They name the tables, keys and cardinality of the revenue cycle from Figure 3.7 alone, so the notation is familiar before the exercises need it.

**Time.** About 30 minutes, or 20 if you demonstrate Step 4.

**Demonstrate, then hand over.** Demonstrate Step 4 on the Customer and SalesOrder line: read it aloud from each end, then say what each symbol means. Leave Steps 1 to 3, 5 and 6 to students, with the enlarged halves of the figure (slides 36 and 37).

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | Tables on the diagram | 10, with Item drawn in gray (Master Data) |
| 2 | Primary keys | Each table's name followed by ID, one integer in the first column |
| 3 | Foreign keys of SalesOrderLine | Two on the diagram (SalesOrderID and ItemID). The worksheet has 5, adding PriceListLineID, PromotionID and PriceOverrideApprovalID |
| 4 | Customer to SalesOrder | One to zero or many: 9 of 220 customers have no orders |
| 5 | SalesOrderLine, the junction | One or many lines for every order; 55 of 266 items are on no line, among them materials, packaging and equipment |
| 6 | SalesOrderLine to ShipmentLine | Zero or many: 4,625 order lines were shipped in several shipment lines |
| 6 | ShipmentLine to SalesInvoiceLine | Zero or one at both ends: 9 shipment lines were never invoiced, and 439 invoice lines (design services) have no shipment line |
| 6 | CashReceiptApplication | 5,745 of 7,409 receipts settle several invoices, and 5,801 invoices are settled by several receipts |

**Stumbles to expect**

- Reading a symbol from the wrong end. The symbol describes the table it touches, so the circle and crow's foot at SalesOrder mean zero or many orders.
- Step 3: students list the two foreign keys on the diagram and call them all. The diagram leaves some out to stay readable.
- Step 5: students look for a junction table with no data of its own. SalesOrderLine carries a quantity and a price, and CashReceiptApplication an applied amount.
- Step 6: zero or one at both ends looks like a mistake. It is not: a shipment line is billed at most once, and design services are billed without a shipment.

**The checkpoint to look for.** Two foreign keys on the diagram, SalesOrderLine and CashReceiptApplication as the junction tables, and one customer to zero or many orders. A student who explains the circle has understood it.

### Guided Tutorial 3.2: Tracing a Sale from Sales Order to General Ledger

**Purpose.** Students follow one real sale through twelve worksheets by key, cross into the ledger through the source-document columns, and find that one sale posts from several documents. This is the chapter's central skill; Chapter 1's Figure 1.6 showed its last step.

**Time.** About 45 to 60 minutes. Step 3 (six worksheets) and Step 7 take longest.

**Demonstrate, then hand over.** Demonstrate Steps 1 and 2 to show the pattern: filter, read the keys, write them down. Then do Step 4 in two moves: filter GLEntry on SourceDocumentID alone and show 38 rows of 11 types, then add the type and show four. Leave Steps 3, 5, 6 and 7 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | The invoice | SalesInvoiceID 7947, SalesOrderID 1697, CustomerID 135; SubTotal $688.42, freight $51.00, tax $48.06, GrandTotal $787.48 |
| 2 | The invoice line | Line 10645: 2 units at $344.21; SalesOrderLineID 6522, ShipmentLineID 10449, ItemID 218 |
| 3 | The keys followed | Shipment SH-2025-003603, shipped 2025-03-02, 3 days before the invoice; order SO-2024-001697, placed 2024-11-21 by Sullivan-Mcdonald, a wholesale customer; item FUR-DSK-0075. The order has 6 lines, 5 shipments and 8 invoices |
| 4 | The ledger rows | Four rows on 2025-03-05, debits equal to credits at $787.48; only the revenue row has a SourceLineID |
| 5 | AccountID to number | AccountID 3 is 1020; AccountID 42 is 4010; AccountID 46 is 4050; AccountID 26 is 2050 |
| 6 | The shipment's rows | Four rows: cost of goods sold and finished goods $459.32 each, then freight-out and accrued expenses $47.42 each |
| 7 | The payment | Application 10686 of $787.48 from receipt CR-2025-003043, a check for $23,870.99 that paid 7 invoices; the receipt posts cash and unapplied cash, and the application moves unapplied cash to receivables |

**Stumbles to expect**

- Steps 1 to 3: students lose the key chain across worksheets. Suggest a scratch sheet with a line for each key found.
- Step 3: students assume the order line equals the invoice line. It is for a larger quantity; the order was shipped and invoiced in parts.
- Step 4: filtering SourceDocumentID without the type. Ask them to read the type column of what they found. A SUM over the Debit column of the filtered sheet adds the hidden rows too, which is why the step adds the four rows by hand. Students also ask why only one row has a SourceLineID: the receivable, freight and tax belong to the whole invoice, not to one line.
- Step 5: AccountID read as the account number. The check to stress is that AccountID 42 is also the item's RevenueAccountID.
- Step 7: students expect the receipt to credit receivables. It credits unapplied cash, and the application moves it. The sale posts from 5 documents in all, counting the commission accrual of $10.33 that the checkpoint's optional item finds.

**The checkpoint to look for.** The four bullets of the tutorial. A weak answer says the invoice created all the postings.

## Difficult ideas and misconceptions

**A key's role depends on the table.** CustomerID is the primary key of Customer and a foreign key in SalesOrder. Question 2 tempts with composite key, and question 1's option C describes a foreign key. Ask: whose rows does this column identify?

![A decision tree that sorts a column into primary key, the source-document trace, foreign key (with its self-reference and bridge-key branches) or an ordinary column.](../figures/chapter-03-accounting-data-environment/IF-03-0-B.pdf)

**An identifier is not a quantity.** Account numbers and IDs are integers that tools will add. Exercise 3.6 shows the practical error: testing GLEntry.AccountID against Account.AccountNumber flags every one of the 71 accounts the ledger uses. Ask: would the sum or the average mean anything?

**No declared foreign keys does not mean no relationships.** Question 8 tempts with the join will fail (A) and the database prevents orphans (B). The file records its primary keys only; the relationships are in the data and on the diagram, and an analyst tests them.

**The symbol describes the table it touches.** Students read a line from one end only, or read a circle as no relationship. Cardinality (how many) and optionality (whether at all) are different questions.

**A junction table is not an extra.** Students see SalesOrderLine and CashReceiptApplication as clutter (question 4's options A to C). Ask how one check paying 7 invoices would be stored without one.

**The join multiplies rows.** Question 10 tempts with 10 (the orders) and 55 (the orders added to the lines). A customer with 12 orders has 33 lines, so a join of customers to orders to lines returns 33 rows for that customer. Across the database it returns 22,269 rows, one for each order line, for 211 customers. Counting customers by row overstates them; summing line amounts by line is right.

![What a join of Customer to SalesOrder to SalesOrderLine does to one customer's rows, and why counting customers by row overstates them.](../figures/chapter-03-accounting-data-environment/IF-03-0-A.pdf)

**The trace is not a foreign key.** Question 12 tempts with it uses two columns. The point is that the target table depends on the type, so the key alone is ambiguous, as the live filter in Tutorial 3.2 shows. 6 ledger rows typed PayrollPayment point to a payment that does not exist.

**One sale, several documents.** Students expect the invoice to hold the whole sale. The shipment posts the cost, the invoice the revenue, the receipt the cash, the application the settlement and the commission accrual the commission.

## Discussion prompts

1. **The file declares no foreign keys. Would you rather work with one that declares and enforces them, and what would you still test?** A good discussion reaches that enforcement stops new orphans but not a valid key that is wrong, and does nothing for an extract or for data loaded earlier.
2. **Is SalesOrderLine a table of things or a relationship?** Both: it joins orders to items and holds a quantity and a price. A junction table can carry its own facts.
3. **One sale posts from five documents. Which would you trace first to test that revenue exists, and which to test that it is complete?** The invoice for existence. Completeness starts from the event, the shipment, and asks whether it was invoiced (Exercise 3.5).
4. **A sales order posts nothing. What changes at the shipment and at the invoice?** The order is a commitment; the shipment moves cost, and the invoice records revenue and the receivable.
5. **A colleague joins customers to orders to lines and reports the number of rows as the number of customers. What went wrong?** The fan-out: one row for each line. Count distinct customers, or aggregate at the right grain.
6. **The chart of accounts is a hierarchy and the cost centers are not (Exercise 3.4). What does a report lose?** It cannot roll cost centers up into divisions from the data; the grouping has to be added and maintained outside it.

## Using the exercises

All six exercises end in short written deliverables: Exercise 3.5 allows one to two pages, Exercise 3.4 half a page to a page, and the others about a page. There is no solution workbook; the model answers are in each exercise's guide. The outcome column uses the numbers of the list at the top of this note.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 3.1 Tracing a Purchase Transaction | Financial | Workbook and trace | 75 | Intermediate | 2, 4, 6 |
| 3.2 Mapping the O2C Group to the Revenue Cycle | Financial | Diagram and workbook | 60 | Basic | 1, 2, 3, 4 |
| 3.3 Mapping the Manufacturing Group | Managerial | Diagram and workbook | 75 | Intermediate | 3, 5 |
| 3.4 Mapping the Keys Behind a Budget-Versus-Actual Report | Managerial | Workbook and PivotTable | 75 | Intermediate | 2, 3, 5 |
| 3.5 Planning a Data Extraction Strategy | Auditing | Diagram and workbook | 90 | Advanced | 2, 4, 5, 6 |
| 3.6 Assessing Referential Integrity | Auditing | Workbook and formulas | 90 | Advanced | 2, 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 3.1 and 3.2, managerial students 3.3 and 3.4, auditing students 3.5 and 3.6. A swap discussion lets each track hear the others; Exercise 3.6 is worth showing to everyone.
- *One exercise a session.* Take them in the order 3.2, 3.1, 3.3, 3.4, 3.6, 3.5. Exercise 3.5 is last because it asks students to design with everything the others used.
- *A light load.* Exercises 3.1 and 3.6 take about 165 minutes and cover outcomes 2, 4 and 6. Add Exercise 3.2 for the diagram.

**Grading and discussion.** Each exercise has a rubric in its guide. Exercises 3.2 and 3.3 suit pairs and a gallery walk, and Exercise 3.6 is the one most worth discussing, because its clean result needs a careful memo. Collect the deliverable and the helper columns, since students have no file to check against.

## Multiple-choice questions

Key: 1 A, 2 B, 3 B, 4 D, 5 C, 6 C, 7 A, 8 C, 9 D, 10 C, 11 A, 12 B, 13 A, 14 D, 15 B.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | A | a primary key uniquely identifies each row and cannot be duplicated or blank. |
| 2 | B | CustomerID in SalesOrder refers to the Customer table's primary key, so it is a foreign key. |
| 3 | B | a single bar at one end and a crow's foot at the other is one-to-many. |
| 4 | D | SalesOrderLine resolves the many-to-many relationship between orders and items. |
| 5 | C | the Manufacturing group holds the work orders, completions, and closes with cost and variance data. |
| 6 | C | ParentAccountID points to another row of the same table. |
| 7 | A | a trial balance nets the GLEntry rows posted up to a date by account, labeled from the Account table. |
| 8 | C | undeclared relationships still join, but nothing enforces them, so they must be tested. |
| 9 | D | referential integrity means every foreign key value that is not blank matches an existing primary key. |
| 10 | C | the join returns one row per order line, 45 rows. |
| 11 | A | the chart of accounts hierarchy is a self-referencing table. |
| 12 | B | the target table depends on SourceDocumentType, so no single foreign key can describe it. |
| 13 | A | a relational database organizes tables connected by primary and foreign keys. |
| 14 | D | an INTEGER column stores whole numbers such as 4500. |
| 15 | B | the O2C cycle has many stages, each needing its own tables. |

**Questions where a wrong option tempts**

- **Question 2.** Composite key (C) tempts students who half-remember that keys can have several columns. The question asks for the role of CustomerID in SalesOrder: a foreign key.
- **Question 3.** One-to-one (A) tempts students who count bars. A single bar at one end and a crow's foot at the other is one-to-many.
- **Question 5.** Master Data (D) tempts, because Item holds StandardCost. The variances live in the Manufacturing group.
- **Question 8.** The join will fail (A) and nothing needs testing (B) both tempt. The correct option says the join works and the analyst tests it.
- **Question 10.** The answer is the number of lines, 45. Option D adds the orders to the lines.
- **Question 12.** Two columns (A) is true and beside the point. The reason is that one column points to different tables.
- **Question 14.** A decimal (C) tempts students who forget that INTEGER means whole numbers. In SQLite the declared type is only a preference, which is why the question says a database that enforces types.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1, 2, 3, 6 and 9 make a good quiz of the vocabulary. Questions 4, 10 and 12 cover junction tables, the fan-out and the trace, and 5, 7 and 15 the Charles River table groups.

## Connections

**Builds on.** Chapter 1 introduced the dataset, the table groups and source-to-ledger traceability, and showed the traced sale's revenue posting in its Figure 1.6; this chapter follows the same sale in full. Chapter 2 treated referential integrity as a data quality test; this chapter makes the keys precise.

**The Part I case.** The comprehensive case uses this map to find where the controller's Furniture question lives in the data: revenue in account 4010, cost in account 5010, and the ItemGroup that selects Furniture.

**Later chapters.** Chapter 4 imports these tables into Excel with Power Query. Chapter 8 builds audit tests on them, and Part III turns the keys into JOIN statements: Chapter 10 returns to the fan-out and to the trace, and Chapter 12 tests the whole trace. Chapter 14 defines the relationships of a Power BI model, where cardinality and grain decide what a count means.

**Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each exercise guide names the competencies it practices.
