---
note: ch03.chapter
uses: [ch03.t1, ch03.t2, ch03.ex6]
title: 'Chapter 3: The Accounting Data Environment'
kind: chapter-notes
unit: '3'
minutes: 150
tool: conceptual
figures:
  - id: IF-03-0-A
    kind: diagram
    purpose: What a join of Customer to SalesOrder to SalesOrderLine does to one customer's rows, and why counting customers by row overstates them.
    shows: Three boxes from left to right. The first holds one Customer row with a real CustomerID and name. The second holds the customer's orders, drawn as a column of order numbers, and the third draws the order lines of those orders as one small square for each line, in a row beside each order, so the third box holds more squares than the second has rows. Arrows between the boxes carry the join columns (CustomerID, then SalesOrderID). Below them is a sketch of the joined result in which the customer's name repeats on every line row. Two counters beside the sketch compare the rows of the result with the one customer, and a note says that summing line amounts by line is right and counting customers by row is wrong.
    data: The customer chosen by the Difficult ideas context (one with about ten orders), with its numbers of orders and lines; the diagram carries those two counts and no amounts.
  - id: IF-03-0-B
    kind: diagram
    purpose: A decision tree that sorts a column into primary key, foreign key, bridge key or the source-document trace.
    shows: A vertical tree of four yes-or-no questions. Does the column identify the rows of its own table? Yes leads to primary key, with SalesOrderID in SalesOrder as the example. Does it hold the key values of another table? Yes leads to foreign key, with CustomerID in SalesOrder, and a side branch asks whether the same column reaches into another table group, which makes it a bridge key, with ItemID in SalesOrderLine. Does the meaning of its value depend on another column? Yes leads to a logical reference, not a key, with SourceDocumentID in GLEntry read together with SourceDocumentType. Each leaf shows its example as a small table header (the logical reference shows SourceDocumentType and SourceDocumentID together), and the leaf for the logical reference is drawn with the dashed amber style that the chapter's diagrams use for the trace. A column that none of the questions fits is an ordinary column.
    data: The examples named in the chapter (SalesOrder, SalesOrderLine, GLEntry); no counts.
---
# Chapter 3: The Accounting Data Environment

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part I, Foundations of Accounting Analytics: the third of three chapters, followed by the comprehensive case that closes the Part |
| Analytics types | None is named. The chapter is about structure, and the tests students run (does this key exist, how many rows does it find) are descriptive |
| Tools | Reading ER diagrams (Tutorial 3.1). Excel in the working copy: filters, and for some exercises XLOOKUP or COUNTIFS and a PivotTable. No SQL or Power BI |
| Components | {{ unit.tutorials|length }} guided tutorials, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver_Work.xlsx, the working copy that Tutorial 2.1 makes from CharlesRiver.xlsx. The Downloads table lists no start files and no solutions for Chapter 3; the guides in this folder hold the model answers |
| Time | Class: about 150 minutes. Students: about two hours of reading, 30 minutes for Tutorial 3.1, 45 to 60 for Tutorial 3.2, and 60 to 90 minutes for each exercise (assign two or three) |

The chapter depends on these conditions of the data:

- The database has {{ n_tables }} tables, each with one integer surrogate key in its first column and no declared foreign keys, so every relationship is logical and has to be tested. The file declares three types (INTEGER, REAL and TEXT): dates are text and flags are 0 and 1.
- Unique indexes protect OrderNumber, InvoiceNumber, EntryNumber and AccountNumber, but not PurchaseInvoice.InvoiceNumber, which is the supplier's own number.
- The {{ ch03_ex6.n_tests }} foreign keys of Exercise 3.6 have {{ ch03_ex6.n_orphans }} orphaned values. The one orphan in the data is in the source-document trace: {{ orphan_rows }} ledger rows typed PayrollPayment point to payments that do not exist. The trace is also ambiguous without its type: the key of the traced invoice, {{ invoice_id }}, finds {{ same_id_rows }} ledger rows of {{ same_id_types }} source types.
- {{ no_orders }} customers have no orders (all inactive), {{ unsold }} items with a list price were never ordered, {{ unshipped|count }} invoice lines (design services) have no shipment line, and {{ uninvoiced }} shipment lines were never invoiced.
- GLEntry has {{ gl_rows|count }} rows and is the largest worksheet, so it filters slowly. The sale of Tutorial 3.2 exists as the chapter tells it: invoice {{ ch03_t2.inv.number }} for {{ ch03_t2.customer.name }}, one of {{ ch03_t2.order.invoices }} invoices of order {{ ch03_t2.order.number }}.

## What students should be able to do afterward

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
- Do Tutorial 3.2 yourself. It crosses twelve worksheets, and the filter on GLEntry ({{ gl_rows|count }} rows) is the slow step, so time it.
- Check that students' Excel has XLOOKUP, which Exercise 3.6 offers beside COUNTIFS. An older perpetual version may lack it.
- Get the PowerPoint deck from the Downloads page. Its module slides follow the chapter's sections and every slide has talk-track notes.

**Pitfalls that cost class time**

- **AccountID is not the account number.** In Tutorial 3.2 the revenue row is AccountID {{ ch03_t2.gl_inv[1].account_id }}, which is account {{ ch03_t2.gl_inv[1].number }}. Exercise 3.6 shows the same error as a false orphan.
- **Filtering SourceDocumentID alone.** The demonstration worth doing live: filter GLEntry on SourceDocumentID {{ invoice_id }} and read {{ same_id_rows }} rows of {{ same_id_types }} types, then add SourceDocumentType SalesInvoice and read four.
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
| 1 | Tables on the diagram | {{ ch03_t1.n_tables }}, with Item drawn in gray (Master Data) |
| 2 | Primary keys | Each table's name followed by ID, one integer in the first column |
| 3 | Foreign keys of SalesOrderLine | Two on the diagram (SalesOrderID and ItemID). The worksheet has {{ ch03_t1.n_fk_columns }}, adding PriceListLineID, PromotionID and PriceOverrideApprovalID |
| 4 | Customer to SalesOrder | One to zero or many: {{ ch03_t1.customers_none }} of {{ ch03_t1.customers }} customers have no orders |
| 5 | SalesOrderLine, the junction | One or many lines for every order; {{ ch03_t1.items_none }} of {{ ch03_t1.n_items }} items are on no line, among them materials, packaging and equipment |
| 6 | SalesOrderLine to ShipmentLine | Zero or many: {{ ch03_t1.part|count }} order lines were shipped in several shipment lines |
| 6 | ShipmentLine to SalesInvoiceLine | Zero or one at both ends: {{ ch03_t1.uninvoiced }} shipment lines were never invoiced, and {{ ch03_t1.design_lines }} invoice lines (design services) have no shipment line |
| 6 | CashReceiptApplication | {{ ch03_t1.multi_receipts|count }} of {{ ch03_t1.receipts|count }} receipts settle several invoices, and {{ ch03_t1.multi_invoices|count }} invoices are settled by several receipts |

**Stumbles to expect**

- Reading a symbol from the wrong end. The symbol describes the table it touches, so the circle and crow's foot at SalesOrder mean zero or many orders.
- Step 3: students list the two foreign keys on the diagram and call them all. The diagram leaves some out to stay readable.
- Step 5: students look for a junction table with no data of its own. SalesOrderLine carries a quantity and a price, and CashReceiptApplication an applied amount.
- Step 6: zero or one at both ends looks like a mistake. It is not: a shipment line is billed at most once, and design services are billed without a shipment.

**The checkpoint to look for.** Two foreign keys on the diagram, SalesOrderLine and CashReceiptApplication as the junction tables, and one customer to zero or many orders. A student who explains the circle has understood it.

### Guided Tutorial 3.2: Tracing a Sale from Sales Order to General Ledger

**Purpose.** Students follow one real sale through twelve worksheets by key, cross into the ledger through the source-document columns, and find that one sale posts from several documents. This is the chapter's central skill; Chapter 1's Figure 1.6 showed its last step.

**Time.** About 45 to 60 minutes. Step 3 (six worksheets) and Step 7 take longest.

**Demonstrate, then hand over.** Demonstrate Steps 1 and 2 to show the pattern: filter, read the keys, write them down. Then do Step 4 in two moves: filter GLEntry on SourceDocumentID alone and show {{ ch03_t2.same_id_rows }} rows of {{ ch03_t2.same_id_types }} types, then add the type and show four. Leave Steps 3, 5, 6 and 7 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | The invoice | SalesInvoiceID {{ ch03_t2.inv.id }}, SalesOrderID {{ ch03_t2.inv.order_id }}, CustomerID {{ ch03_t2.inv.customer_id }}; SubTotal ${{ ch03_t2.inv.subtotal|money }}, freight ${{ ch03_t2.inv.freight|money }}, tax ${{ ch03_t2.inv.tax|money }}, GrandTotal ${{ ch03_t2.inv.total|money }} |
| 2 | The invoice line | Line {{ ch03_t2.line.id }}: {{ ch03_t2.line.quantity|num(0) }} units at ${{ ch03_t2.line.price|money }}; SalesOrderLineID {{ ch03_t2.line.order_line }}, ShipmentLineID {{ ch03_t2.line.shipment_line }}, ItemID {{ ch03_t2.line.item_id }} |
| 3 | The keys followed | Shipment {{ ch03_t2.shipment.number }}, shipped {{ ch03_t2.shipment.date }}, {{ ch03_t2.shipment.days_before }} days before the invoice; order {{ ch03_t2.order.number }}, placed {{ ch03_t2.order.date }} by {{ ch03_t2.customer.name }}, a {{ ch03_t2.customer.segment }} customer; item {{ ch03_t2.item.code }}. The order has {{ ch03_t2.order.order_lines }} lines, {{ ch03_t2.order.shipments }} shipments and {{ ch03_t2.order.invoices }} invoices |
| 4 | The ledger rows | Four rows on {{ ch03_t2.inv.date }}, debits equal to credits at ${{ ch03_t2.inv.total|money }}; only the revenue row has a SourceLineID |
| 5 | AccountID to number | {% for r in ch03_t2.gl_inv %}AccountID {{ r.account_id }} is {{ r.number }}{{ '; ' if not loop.last else '' }}{% endfor %} |
| 6 | The shipment's rows | Four rows: cost of goods sold and finished goods ${{ ch03_t2.shipment_line.cost|money }} each, then freight-out and accrued expenses ${{ ch03_t2.freight|money }} each |
| 7 | The payment | Application {{ ch03_t2.application.id }} of ${{ ch03_t2.application.amount|money }} from receipt {{ ch03_t2.receipt.number }}, a {{ ch03_t2.receipt.method }} for ${{ ch03_t2.receipt.amount|money }} that paid {{ ch03_t2.receipt.applications }} invoices; the receipt posts cash and unapplied cash, and the application moves unapplied cash to receivables |

**Stumbles to expect**

- Steps 1 to 3: students lose the key chain across worksheets. Suggest a scratch sheet with a line for each key found.
- Step 3: students assume the order line equals the invoice line. It is for a larger quantity; the order was shipped and invoiced in parts.
- Step 4: filtering SourceDocumentID without the type. Ask them to read the type column of what they found. A SUM over the Debit column of the filtered sheet adds the hidden rows too, which is why the step adds the four rows by hand. Students also ask why only one row has a SourceLineID: the receivable, freight and tax belong to the whole invoice, not to one line.
- Step 5: AccountID read as the account number. The check to stress is that AccountID {{ ch03_t2.gl_inv[1].account_id }} is also the item's RevenueAccountID.
- Step 7: students expect the receipt to credit receivables. It credits unapplied cash, and the application moves it. The sale posts from {{ ch03_t2.documents }} documents in all, counting the commission accrual of ${{ ch03_t2.commission|money }} that the checkpoint's optional item finds.

**The checkpoint to look for.** The four bullets of the tutorial. A weak answer says the invoice created all the postings.

## Difficult ideas and misconceptions

**A key's role depends on the table.** CustomerID is the primary key of Customer and a foreign key in SalesOrder. Question 2 tempts with composite key, and question 1's option C describes a foreign key. Ask: whose rows does this column identify?

{{ figure('IF-03-0-B') }}

**An identifier is not a quantity.** Account numbers and IDs are integers that tools will add. Exercise 3.6 shows the practical error: testing GLEntry.AccountID against Account.AccountNumber flags every one of the {{ ch03_ex6.used }} accounts the ledger uses. Ask: would the sum or the average mean anything?

**No declared foreign keys does not mean no relationships.** Question 8 tempts with the join will fail (A) and the database prevents orphans (B). The file records its primary keys only; the relationships are in the data and on the diagram, and an analyst tests them.

**The symbol describes the table it touches.** Students read a line from one end only, or read a circle as no relationship. Cardinality (how many) and optionality (whether at all) are different questions.

**A junction table is not an extra.** Students see SalesOrderLine and CashReceiptApplication as clutter (question 4's options A to C). Ask how one check paying {{ ch03_t2.receipt.applications }} invoices would be stored without one.

**The join multiplies rows.** Question 10 tempts with 10 (the orders) and 55 (the orders added to the lines). A customer with {{ fan.orders }} orders has {{ fan.lines }} lines, so a join of customers to orders to lines returns {{ fan.lines }} rows for that customer. Across the database it returns {{ fan.rows|count }} rows, one for each order line, for {{ fan.customers }} customers. Counting customers by row overstates them; summing line amounts by line is right.

{{ figure('IF-03-0-A') }}

**The trace is not a foreign key.** Question 12 tempts with it uses two columns. The point is that the target table depends on the type, so the key alone is ambiguous, as the live filter in Tutorial 3.2 shows. {{ orphan_rows }} PayrollPayment rows point to a payment that does not exist.

**One sale, several documents.** Students expect the invoice to hold the whole sale. The shipment posts the cost, the invoice the revenue, the receipt the cash, the application the settlement and the commission accrual the commission.

## Discussion prompts

1. **The file declares no foreign keys. Would you rather work with one that declares and enforces them, and what would you still test?** A good discussion reaches that enforcement stops new orphans but not a valid key that is wrong, and does nothing for an extract or for data loaded earlier.
2. **Is SalesOrderLine a table of things or a relationship?** Both: it joins orders to items and holds a quantity and a price. A junction table can carry its own facts.
3. **One sale posts from five documents. Which would you trace first to test that revenue exists, and which to test that it is complete?** The invoice for existence. Completeness starts from the event, the shipment, and asks whether it was invoiced (Exercise 3.5).
4. **A sales order posts nothing. What changes at the shipment and at the invoice?** The order is a commitment; the shipment moves cost, and the invoice records revenue and the receivable.
5. **A colleague joins customers to orders to lines and reports the number of rows as the number of customers. What went wrong?** The fan-out: one row for each line. Count distinct customers, or aggregate at the right grain.
6. **The chart of accounts is a hierarchy and the cost centers are not (Exercise 3.4). What does a report lose?** It cannot roll cost centers up into divisions from the data; the grouping has to be added and maintained outside it.

## Using the exercises

All six exercises end in a one-page written deliverable. There is no solution workbook; the model answers are in each exercise's guide. The outcome column uses the numbers of the list at the top of this note.

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

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 2.** Composite key (C) tempts students who half-remember that keys can have several columns. The question asks for the role of CustomerID in SalesOrder: a foreign key.
- **Question 3.** One-to-one (A) tempts students who count bars. A single bar at one end and a crow's foot at the other is one-to-many.
- **Question 5.** Master Data (D) tempts, because Item holds StandardCost. The variances live in the Manufacturing group.
- **Question 8.** The join will fail (A) and nothing needs testing (B) both tempt. The correct option says the join works and the analyst tests it.
- **Question 10.** The answer is the number of lines, 45. Option D adds the orders to the lines.
- **Question 12.** Two columns (A) is true and beside the point. The reason is that one column points to different tables.
- **Question 14.** A decimal (C) tempts students who forget that INTEGER means whole numbers. In SQLite the declared type is only a preference, which is why the question says a database that enforces types.
{% if n_longest %}- **Question{{ 's' if n_longest > 1 else '' }} {{ longest_correct }}.** The correct option is also the longest. If you grade with {{ 'these' if n_longest > 1 else 'it' }}, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1, 2, 3, 6 and 9 make a good quiz of the vocabulary. Questions 4, 10 and 12 cover junction tables, the fan-out and the trace, and 5, 7 and 15 the Charles River table groups.

## Connections

**Builds on.** Chapter 1 introduced the dataset, the table groups and source-to-ledger traceability, and showed the traced sale's revenue posting in its Figure 1.6; this chapter follows the same sale in full. Chapter 2 treated referential integrity as a data quality test; this chapter makes the keys precise.

**The Part I case.** The comprehensive case uses this map to find where the controller's Furniture question lives in the data: revenue in account 4010, cost in account 5010, and the ItemGroup that selects Furniture.

**Later chapters.** Chapter 4 imports these tables into Excel with Power Query. Chapter 8 builds audit tests on them, and Part III turns the keys into JOIN statements: Chapter 10 returns to the fan-out and to the trace, and Chapter 12 tests the whole trace. Chapter 14 defines the relationships of a Power BI model, where cardinality and grain decide what a count means.

**Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each exercise guide names the competencies it practices.

