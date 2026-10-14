# Chapter 1: The Role of Analytics in Accounting

| | |
|---|---|
| Unit | Chapter 1: The Role of Analytics in Accounting |
| Tools | Workbook browsing and written work |
| Time | About 150 minutes of class time |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part I, Foundations of Accounting Analytics: the first of three chapters, closed by a comprehensive case |
| Analytics types | All four are named and defined. Table 1.1 gives an example of each for financial accounting, managerial accounting and auditing. Students classify questions here; they do not yet perform the analyses |
| Tools | Excel, only to browse CharlesRiver.xlsx. SQL and Power BI are introduced in words (Table 1.2, Figure 1.3) |
| Components | 1 guided tutorial, 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 43 slides |
| Files students need | CharlesRiver.xlsx, from the Charles River Accounting Dataset (Excel) link on the Downloads page. The Downloads table lists no start files and no solutions for Chapter 1; the guides in this folder hold the model answers |
| Time | Class: about 150 minutes. Students: about two hours of reading, 35 minutes for the tutorial, and 45 to 70 minutes for each exercise (assign two or three) |

The chapter depends on these conditions of the data, all visible in the workbook:

- The workbook has one worksheet for each of the 82 tables, and each stores its data as an Excel Table with the filter buttons already on.
- Every GLEntry row names the document that created it. The ledger has 20 source types, and journal entries are a small share of its rows (0.3%).
- The sale that Figure 1.6 traces, invoice SI-2025-007947, exists as drawn. Exercise 1.2 gives its whole path.
- The timestamps and the reversal column that Exercise 1.6 asks about behave in a particular way, which that guide describes.
- The Manufacturing group holds completions, work order closes and labor time, but no table of actual scrap, defects or downtime (Exercise 1.4).

## What students should be able to do afterward

1. Classify a question as descriptive, diagnostic, predictive or prescriptive, and write one of each type. Practiced in Exercise 1.4 and questions 2, 3, 4 and 15.
2. Place a task at its stage of the six-stage workflow and say why defining the question comes first. Practiced in Exercise 1.4 (requirement 4) and questions 5 and 12.
3. Choose among Excel, SQL and Power BI for a task and give the reason. Practiced in questions 7 and 10 and the discussion prompts; no exercise asks for it directly.
4. Map a financial reporting, cost or audit need to table groups, tables and columns of the dataset. Practiced in Exercises 1.1, 1.3 and 1.5.
5. Describe how a revenue transaction moves from order to ledger, and use SourceDocumentType, SourceDocumentID and SourceLineID to trace a posting and to separate postings made by documents from journal entries. Practiced in Exercises 1.2 and 1.5 (requirement 2) and question 11.
6. Judge whether the data on hand can support a planned test, and name what is missing. Practiced in Exercises 1.3 (requirement 3), 1.5 and 1.6.

## Preparing to teach

**Before the first class**

- Ask students to download CharlesRiver.xlsx the week before and open it once. It is a large file, and opening it in class costs the first ten minutes.
- Open it yourself and rehearse the demonstration in Exercise 1.2: the SalesInvoice row for SI-2025-007947 and its rows in GLEntry. Rehearse the filter on SourceDocumentType in GLEntry, the largest worksheet, so you know how long it takes on your machine.
- Get the PowerPoint deck from the Downloads page, which also links a browser version. Each module slide matches a section of the chapter, and every slide has talk-track notes.
- Part II needs Power Query, so confirm now that every student has a version of Excel that has it. Chapter 1 only opens and reads the workbook.

**Keep the downloaded workbook unchanged.** Tutorial 2.1 asks students to copy CharlesRiver.xlsx and name the copy CharlesRiver_Work.xlsx for Part I, and the tutorials of Parts II and IV read the downloaded workbook with Power Query. A student who sorts or edits the original and saves it hands later chapters a changed file. Tell students to browse and close without saving, or to work in a copy from the start.

**Pitfalls that cost class time**

- GLEntry has 815,921 rows. Filtering it takes a moment, so say so before students think Excel has frozen.
- The filter buttons are already on, as Step 2 of the tutorial says. Do not tell students to use Data > Filter, which would switch them off, or Ctrl+T, which these sheets do not need.
- A file downloaded from the internet may open in a read-only protected mode, where the filter buttons do not respond until editing is allowed. This is Excel's behavior; the book does not mention it.
- Students leave filters on and misread the next worksheet. Ask them to clear a filter before moving on.
- AccountID is not the account number, and SourceDocumentID is the document's key, not its number. VoucherNumber holds the number (for example SI-2025-007947). Say this in the demonstration and again at Exercise 1.2.
- Say out loud that the dataset is fictional and cleaner than a real system. Later chapters also find problems in these tables, so students should not assume a ledger row or a document is correct because it is there.

## Teaching approaches

**Plan A: lecture with a live workbook demonstration (two sessions of 75 minutes, 150 minutes in all).** It fits a lecture course with a projector and covers the whole deck. Students listen for the first session and touch the workbook only in the second, so keep the demonstration short and the tutorial on their own machines.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | The opening scenario: what would students need before they could answer the controller? Read the five objectives | 2 to 4 |
| 1 | 15 | The changing landscape and the definition of accounting analytics | 5 to 9 |
| 1 | 15 | The four types, with the classification check and its answers | 10 to 12 |
| 1 | 10 | Analytics across roles; the controller's question as the diagnostic cell of Table 1.1 | 13 to 15 |
| 1 | 15 | The workflow, the stage-by-stage table and the preparation check | 16 to 20 |
| 1 | 10 | The tools (Table 1.2, Figure 1.3) and the tool check | 21 to 25 |
| 2 | 15 | The dataset: table groups, Figures 1.4 to 1.6 and the Watch out | 26 to 33 |
| 2 | 10 | Live demonstration: follow the traced sale from SalesInvoice to GLEntry | |
| 2 | 30 | Tutorial 1.1 at students' machines, ending with the checkpoint | 34 to 37 |
| 2 | 10 | How the book is organized; the summary and key terms | 38 to 41 |
| 2 | 10 | Assign exercises; students start Exercise 1.2 | 42, 43 |
| | 150 | Total | |

**Plan B: lab first (one session of 90 minutes).** Students open the workbook before they hear the vocabulary. It fits a computer lab or a class with laptops, and it lets the data motivate the definitions. The landscape and roles slides (5 to 9, 13 to 15) are left to reading, and students slow to open GLEntry fall behind, so pair them.

| Minutes | Activity | Slides |
|---:|---|---|
| 5 | Pose the controller's question; students list what they would look at | 4 |
| 35 | Tutorial 1.1 in pairs, stopping at the checkpoint | 34 to 37 |
| 15 | Debrief and the traced-sale demonstration; students predict which worksheets hold rows for the sale | 28, 31, 32 |
| 25 | Mini-lecture on the types, workflow and tools, with the three checks | 10 to 12, 17 to 20, 22 to 25 |
| 10 | Table 1.3 and the book's organization; assign exercises | 29, 30, 39, 42 |
| 90 | Total | |

**Plan C: flipped, with one 75-minute class.** Students read the chapter and do the tutorial at home. It fits upper-level and graduate classes, and it depends on students arriving prepared, so open with a quiz.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval quiz on questions 2, 3, 4, 11 and 15 | |
| 20 | Classification workshop: groups sort the cells of Table 1.1 and their own questions into the four types, then defend the sorting | 10 to 12, 15 |
| 20 | The traced sale at the board and in the workbook; students say what the next row will be before you click | 31, 32 |
| 15 | Start Exercise 1.4 (requirements 1 and 2) in pairs | |
| 10 | Discussion prompts 3 and 5; assign exercises | |
| 75 | Total | |

## Tutorial guide

### Guided Tutorial 1.1: Exploring the Charles River Database

**Purpose.** Every student gets a first look at the workbook before an exercise asks them to use it. They see the customer, order, item, account, ledger, manufacturing and payroll worksheets and meet primary and foreign keys in a real pair of tables. Nothing in it needs a calculation.

**Time.** About 35 minutes in class with the checkpoint discussion, or 20 if students arrive having read the steps. The deck's notes suggest ten to fifteen minutes for browsing alone.

**Demonstrate, then hand over.** Demonstrate Step 3 (CustomerID is a primary key in Customer and a foreign key in SalesOrder) and Step 6 (the filter list of SourceDocumentType in GLEntry). Leave Steps 1, 2, 4, 5 and 7 to students. In Step 6 show the filter list: the ledger has 20 source types, and the tutorial names SalesInvoice, Shipment, PurchaseInvoice, PayrollPayment, and JournalEntry among them.

**What students should see.**

| Worksheet | Look for | Value |
|---|---|---|
| Customer | Rows; segments in the filter list | 220 rows; Wholesale, Small Business, Design Trade, Strategic, and Design Services |
| SalesOrder | Rows | 5,819 |
| Item | Rows; finished-goods groups; other groups; SupplyMode | 266 rows; Furniture, Lighting, Textiles, and Accessories; Services, Raw Materials, Packaging, and Capex; Manufactured and Purchased |
| Account | Rows; AccountType values | 104 rows; asset, equity, expense, liability, and revenue |
| GLEntry | Rows; source types in the filter list | 815,921 rows; 20 types |
| WorkOrder, PayrollRegister | Rows | 13,668 and 8,197 |

**Stumbles to expect**

- Step 1: students scroll the tab strip for one table at a time. The tutorial says the worksheets are arranged by table group, so send them to Table 1.3 first.
- Step 4: students ask why Services is among the items. The tutorial explains that it holds design services that Charles River sells and operating services that it buys.
- Steps 5 and 6: students read AccountID as the account number. It is the key of Account, and the traced sale's revenue row carries AccountID 42 for account 4010.
- Any step: a student sorts a Table or leaves a filter on. Show how to clear it, and remind them not to save.

**The checkpoint to look for.** The answers are in the tutorial: the four finished-goods groups (Furniture, Lighting, Textiles, and Accessories); SourceDocumentType, SourceDocumentID and SourceLineID; and the Account worksheet. A student who names AccountID for the second answer has found a key, not the source columns: send them back to Step 6.

## Difficult ideas and misconceptions

**Descriptive is not "basic", and the types are not a ladder.** Students read Figure 1.1 as a ranking and treat prescriptive work as the goal. The chapter's Watch out says most accounting analytics is descriptive and that a poor summary can mislead as much as a model. Ask which type the controller's question is and what descriptive work has to come first.

**Telling the type by the tool or the first step.** Question 15 describes a PivotTable summary, then a breakdown and a trace of the largest changes. Students choose descriptive because the PivotTable came first, but the work ends by asking why. Question 2 reverses it: quarter-to-quarter percentage changes tempt students toward diagnostic, though nothing in it explains why.

**Predictive and prescriptive.** In question 3 an auditor builds an expected range for monthly revenue. Students who choose prescriptive hear "expected range" as a recommendation. An expectation says what to expect; a recommendation chooses an action under an objective and constraints, as Solver does in question 4.

![A decision aid for sorting a question into one of the four types of analytics.](../figures/chapter-01-role-of-analytics/IF-01-0-B.pdf)

**The workflow as a straight line.** Students guess that analysis takes longest (question 12), and the slide notes anticipate it. The chapter says preparation and cleaning often take longest. Use the controller's question: an invoice line not linked to a product has to be fixed before any margin is calculated.

**A table group is not a table.** Table 1.3 lists key tables only. Students confine an exercise to them and miss the line tables (SalesInvoiceLine, ShipmentLine) and the master data (Item). Question 6 shows the opposite error: Master Data seems a natural home for the chart of accounts, but Account is in the Accounting Core.

**Not every document posts.** Students expect a sales order in the ledger. A sales order and its lines post nothing; the shipment, the invoice, the receipt and its application do. The chapter says operational records without a financial effect stay outside the ledger.

**One order, one invoice, one receipt.** In the data an order is often shipped and invoiced in parts and a receipt often pays several invoices. Exercise 1.2 shows the traced order and receipt.

**The ledger is the answer.** The chapter calls GLEntry central but not complete, and says later chapters reconcile it to the source documents. After Exercises 1.5 and 1.6, students should say that a test run on the ledger cannot find a document that never reached it.

## Discussion prompts

1. **A test of every transaction cannot miss an exception the way a sample can. What can it still miss?** A good discussion reaches the chapter's own limit: testing a whole population does not show that the records are complete or genuine.
2. **If software drafts analyses and flags unusual transactions, what is left for the accountant?** Framing the question, judging whether the data is reliable, and professional judgment; and why understanding the data helps in spotting a wrong classification.
3. **The controller asks why Furniture margin fell. Which type is that, and what do you need before you start?** Diagnostic, after a descriptive summary, with the data of the opening scenario: invoiced sales, product costs and the revenue and cost ledger accounts.
4. **Pick a cell of Table 1.1 and say how the same technique serves another perspective.** The In Practice example is duplicate payments: controls assurance, vendor management and cash review use the same method.
5. **Which workflow stage would you most want help with, and is the order fixed?** Expect data preparation or communication. Steer toward later stages sending work back to earlier ones, and the first stage shaping the rest.
6. **Take a task from an internship or a job. Which of Excel, SQL and Power BI fits, and why?** Table 1.2: a population or a join points to SQL, a model a reviewer must trace to Excel, an audience that explores to Power BI.
7. **Why does it matter that each ledger row names its source?** An analyst can trace a number to a document, reconcile the ledger to its documents, and separate journal entries from automatic postings.
8. **What would real company data have that Charles River does not?** The Watch out names hundreds of tables, custom fields and harder data quality problems; ask what that means for preparation and judgment.

## Using the exercises

All six exercises are conceptual: students browse the workbook, write short answers, and write a memo in four of them. There is no solution workbook, so the model answers are in the guide for each exercise. The outcome column uses the numbers of the list at the top of this note.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1.1 Mapping Table Groups to the Financial Reporting Cycle | Financial | Workbook and memo | 60 | Basic | 4 |
| 1.2 Tracing the Revenue Path from Order to Ledger | Financial | Workbook and written work | 50 | Basic | 5 |
| 1.3 Evaluating Table Groups for Cost Analysis | Managerial | Workbook and written work | 60 | Intermediate | 4, 6 |
| 1.4 Framing Production Questions with the Four Types | Managerial | Workbook and memo | 45 | Intermediate | 1, 2 |
| 1.5 Assessing Data Availability for Audit Testing | Auditing | Workbook and memo | 70 | Intermediate | 4, 5, 6 |
| 1.6 Evaluating Journal Entry Data for Audit Purposes | Auditing | Workbook and written work | 50 | Advanced | 6 |

![Which table groups each exercise's model answer draws on.](../figures/chapter-01-role-of-analytics/IF-01-0-A.pdf)

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 1.1 and 1.2, managerial students 1.3 and 1.4, auditing students 1.5 and 1.6, about two hours each. Swap the tracks in a short discussion so each student hears the other perspectives.
- *One exercise a session.* Take them in the order 1.2 (after the lecture), 1.1, 1.4, 1.3, 1.5, 1.6. The order rises in difficulty, and Exercise 1.2 prepares the source columns that 1.5 and 1.6 use.
- *A light load.* Exercises 1.2 and 1.4 take about 95 minutes and cover outcomes 1, 2 and 5. Add Exercise 1.6 for an auditing course.

**Grading and discussion.** Exercises 1.1, 1.3 and 1.5 end in a memo or written assessment and suit grading with the rubrics in their guides. Exercises 1.2 and 1.4 have short answers and suit pairs and an in-class review. Exercise 1.6 is the one most worth discussing, because its answers rest on judgment about what the data can show. Collect work in class or through your course system, since students cannot check themselves against a file.

## Multiple-choice questions

Key: 1 D, 2 A, 3 C, 4 D, 5 A, 6 C, 7 B, 8 A, 9 C, 10 D, 11 B, 12 A, 13 C, 14 B, 15 B.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | D | data volume and complexity have outgrown traditional manual methods of analysis. |
| 2 | A | summarizing past costs and their changes describes what happened. |
| 3 | C | an expectation of future results built from past data is predictive. |
| 4 | D | Solver recommends the best product mix under constraints, which is prescriptive. |
| 5 | A | the workflow runs from the question through access, preparation, analysis, and visualization to communication. |
| 6 | C | Accounting Core holds the chart of accounts, journal entries, and ledger detail. |
| 7 | B | SQL queries relational databases directly. |
| 8 | A | the book builds from the most accessible table groups to the more complex ones. |
| 9 | C | the IMA competency framework includes technology and analytics as a core domain. |
| 10 | D | Power BI builds interactive dashboards with filters and drill-down. |
| 11 | B | SourceDocumentType, SourceDocumentID, and SourceLineID trace a ledger row to its source. |
| 12 | A | data preparation and cleaning usually takes the most time. |
| 13 | C | the Manufacturing group holds work orders, production, and variance data. |
| 14 | B | one company's data, learned deeply, connects the same transactions across the tools. |
| 15 | B | breaking a change down to find its cause is diagnostic analytics. |

**Questions where a wrong option tempts**

- **Questions 2, 3, 4 and 15 (the types)** carry most of the chapter's concept. Ask students to underline the verb of the scenario (calculates and compares, builds an expected range, determines the best combination, breaks down and traces) before they choose. Use the decision aid above.
- **Question 6.** Master Data tempts because a chart of accounts feels like reference data. The chapter places Account, JournalEntry and GLEntry in the Accounting Core.
- **Question 7.** Students who have used Excel's data connections choose Excel. The question asks which tool is most appropriate for extracting data directly from a relational database, which the chapter says is SQL.
- **Question 9.** The FASB and the SEC tempt students who read "professional organization" as "standard setter". The chapter names the IMA for the framework of management accountants.
- **Question 11.** AccountID and CostCenterID tempt students who think of keys in general. Only the three source columns name the document.
- **Question 13.** Accounting Core tempts because variances reach the ledger, but the Manufacturing group is where production variances are computed.
- **Questions 1, 8 and 14.** The correct option is also the fullest sentence, so a test-wise student can guess it. If you grade with these, ask students to explain their answer or reword the options.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 2, 3, 4, 11 and 15 make a good quiz of the types and the source columns. Questions 5 and 12 test the workflow, 7 and 10 the tools, and 6 and 13 the table groups.

## Connections

**Builds on.** Nothing earlier in the book. It builds on students' accounting coursework: debits and credits, the chart of accounts and the source document.

**Chapters 2 and 3.** Chapter 2 takes up the quality of accounting data, and its tutorials start with the working copy CharlesRiver_Work.xlsx. Chapter 3 teaches primary and foreign keys, and Tutorial 3.2 traces SI-2025-007947 through every table it touches. Exercise 1.2 previews that tracing without asking for it.

**The Part I case.** The comprehensive case that closes Part I, Getting the Data Ready for the Furniture Margin Question, uses the three chapters on the controller's question. Chapter 6 answers that question with Excel.

**Later chapters.** Exercise 1.5 previews the audit tests of Chapters 8 and 12 and the monitoring of Chapter 16. Exercise 1.6 previews the journal entry tests of Chapters 8, 11 and 16. Exercises 1.3 and 1.4 preview the manufacturing variance work of Part III. Parts II to IV teach the tools of Table 1.2, and the capstone cases of Part V ask students to choose among them.

**Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each exercise guide names the competencies it practices.
