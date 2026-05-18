---
number-sections: false
format:
  html:
    number-sections: false
---

# Preface {.unnumbered}

This book exists because the accounting profession has changed faster than most accounting curricula have adapted. Organizations now generate financial and operational data at a scale that makes traditional manual methods of analysis insufficient. Enterprise resource planning systems capture every transaction, every journal entry, every payment, and every production order in relational databases that contain millions of records. Auditors are expected to test entire populations rather than small samples. Management accountants are asked to explain variances, forecast performance, and identify operational drivers using data that lives in systems they were never trained to access. Financial reporting teams must reconcile, validate, and analyze data that flows from dozens of interconnected tables before it reaches the financial statements. The profession needs practitioners who can work directly with data, and accounting education needs textbooks that teach them how.

This textbook teaches accounting students to extract, prepare, analyze, and visualize data using three tools that are widely used in professional practice. Microsoft Excel serves as the foundation for data preparation, descriptive analytics, statistical modeling, and audit testing. SQL provides the ability to query relational databases directly, joining tables, aggregating results, and performing population-level analysis without relying on pre-built reports. Microsoft Power BI enables the creation of interactive dashboards and reports that communicate analytical findings to diverse audiences. These three tools cover the full analytics workflow from data access through communication of results, and they represent the toolkit that employers consistently identify as most relevant for entry-level accounting professionals (Sledgianowski, Gomaa, and Tan, 2017).

The book is built around one integrated dataset that students use throughout all twenty chapters. The Charles River Accounting Dataset follows a single fictional mid-size home furnishings company through its complete business cycles, and the same data underlies every chapter regardless of which tool that chapter teaches. The About the Dataset section that follows this preface describes the company, the ten table groups, the business cycles, and the distribution formats in full detail.


## Why This Book

Several features distinguish this textbook from other analytics resources available to accounting instructors.

The first is its focus on accounting. General-purpose data analytics textbooks teach techniques using data from marketing, healthcare, sports, or other domains. Those examples are interesting but do not help accounting students see how analytics connects to the work they will actually do. Every example, exercise, and case in this book uses accounting data and addresses accounting questions. Students analyze revenue trends, prepare trial balances, test for duplicate payments, calculate cost variances, perform Benford's Law analysis, and build financial reporting dashboards. The analytical techniques are the same ones taught in general analytics courses, but the context is always accounting, which helps students transfer what they learn to professional practice.

The second is its three-perspective exercise structure. Every chapter includes applied exercises organized into three sections by accounting perspective. Financial Accounting exercises address reporting, disclosure, and compliance questions. Managerial Accounting exercises address costing, budgeting, performance measurement, and decision support questions. Auditing exercises address assurance, control testing, anomaly detection, and risk assessment questions. This structure ensures that students see how the same analytical technique serves different purposes depending on the professional role. An aging analysis, for example, appears as a financial reporting exercise (estimating the allowance for doubtful accounts), a managerial accounting exercise (assessing collection efficiency), and an auditing exercise (evaluating management estimates and selecting balances for confirmation). Students who encounter all three perspectives develop a broader understanding of how analytics creates value across the profession.

The third is its integrated tool progression. Many textbooks teach Excel, SQL, and visualization tools in isolation. This book teaches them as complementary stages of a single workflow. Part II covers Excel. Part III covers SQL. Part IV covers Power BI. Part V brings all three tools together in integrated projects where students extract data using SQL, analyze it in Excel, and present results in Power BI within a single engagement. This progression mirrors how analytics projects work in practice, where no single tool handles every stage.

The fourth is its design as an open educational resource. The book and its companion dataset are freely available, and every tool used in the exercises is either free or included with standard institutional licenses. The Open Access section on the book's landing page describes the licensing terms in detail.


## Pedagogical Design

The book follows a consistent pedagogical structure that reflects research on how students learn technical skills most effectively. Worked examples, immediate practice opportunities, and progressive complexity have been shown to support skill acquisition in technology-intensive courses (Borthick and Jones, 2000). Every chapter in this book applies these principles through a structured sequence.

Each chapter opens with four to six learning objectives written in measurable terms using action verbs drawn from Bloom's taxonomy. The objectives span multiple cognitive levels, from foundational understanding through application and analysis, so that both undergraduate and graduate students find appropriate challenges. Following the objectives, an opening scenario places the student in a realistic professional situation at Charles River, the company whose data students use throughout the book. The scenario names a role, describes a concrete task, and motivates the material that follows by showing students why it matters before they learn how to do it.

The body of each chapter presents concepts in narrative paragraph form, supported by figures, tables, and diagrams. One to three guided tutorials are embedded within the conceptual content at the point where the relevant technique is introduced, so students read about a concept and immediately practice it before moving to the next topic. Each tutorial includes numbered steps, expected outputs, and a checkpoint that allows students to verify their work. Three types of callout boxes appear throughout the narrative. "In Practice" notes describe how the technique is used in professional settings. "Watch Out" notes warn about common errors and pitfalls. "Connecting the Dots" notes link the current topic to material in other chapters or other tools, helping students see the book as an integrated whole.

Each chapter closes with a summary, a list of key terms with definitions, ten to fifteen multiple choice questions spanning recall, application, and judgment, and applied exercises organized by the three accounting perspectives. Five comprehensive cases, one at the end of each of the book's five parts, provide extended multi-tool investigations that integrate material from all chapters in the part.

In-text citations in APA format appear throughout the narrative to support claims about professional practice, technique effectiveness, and adoption trends. Each chapter closes with a Further Reading section containing five to eight annotated references drawn from peer-reviewed journals, professional standards, and practitioner publications.


## Audience and Course Design

This textbook serves both undergraduate and graduate four-credit courses in accounting analytics or accounting information systems. A single text serves both audiences. The instructor controls the depth and rigor of classroom discussions and analyses to match the course level. Undergraduate courses can focus on the guided tutorials and foundational exercises. Graduate courses can emphasize the analytical judgment required by the applied exercises and comprehensive cases, assign additional readings from the Further Reading sections, and incorporate extended discussion of professional standards and research findings.

The book assumes no prior analytics or programming experience. Students need only the accounting knowledge gained from introductory financial and managerial accounting courses. Every technical concept is introduced from the ground up, and every tool is taught through step-by-step instruction before students are asked to work independently. Students who have prior experience with Excel, SQL, or Power BI will move through the early chapters faster and can focus their effort on the accounting applications and the more advanced techniques in later chapters.


## Suggested Course Schedules

The following schedules are suggestions, not prescriptions. Instructors should adapt them to their program's requirements, their students' preparation, and their own areas of emphasis.

For an undergraduate course spanning fifteen weeks, Week 1 covers Chapters 1 and 2, introducing analytics and understanding data through the Charles River order-to-cash tables. Week 2 covers Chapter 3, the accounting data environment, where students explore the full Charles River schema. Weeks 3 through 4 cover Chapters 4 and 5, Excel essentials and data preparation. Weeks 5 through 6 cover Chapters 6 and 7, descriptive analytics and modeling. Week 7 covers Chapter 8, Excel for audit analytics, introducing the Accounting Core and procure-to-pay tables. Weeks 8 through 9 cover Chapters 9 and 10, introduction to SQL and joining data. Week 10 covers Chapters 11 and 12, intermediate SQL and audit analytics. Week 11 covers Chapter 13, visualization principles. Weeks 12 through 13 cover Chapters 14 and 15, Power BI fundamentals and data modeling. Week 14 covers Chapter 16, building accounting dashboards. Week 15 covers selected topics from Chapters 17 through 20, along with the capstone project presentation.

For a graduate course spanning fifteen weeks, the pace is faster and the emphasis shifts toward analytical judgment and integration. Week 1 covers Chapters 1 through 3 as a combined foundational session. Week 2 covers Chapters 4 and 5 at an accelerated pace. Week 3 covers Chapters 6 and 7 with emphasis on modeling and analytical judgment. Week 4 covers Chapter 8 with deeper discussion of audit standards and professional skepticism. Weeks 5 through 6 cover Chapters 9 through 11 with emphasis on CTEs, window functions, and the full Charles River schema. Week 7 covers Chapter 12 with extended case analysis requiring multi-step SQL investigation. Week 8 covers Chapters 13 and 14. Week 9 covers Chapter 15 with advanced DAX and complex multi-group data models. Week 10 covers Chapter 16 with emphasis on dashboard design for different stakeholder audiences. Week 11 covers Chapter 17, financial reporting analytics. Week 12 covers Chapter 18, cost and management accounting analytics. Week 13 covers Chapter 19, forensic accounting and fraud analytics. Week 14 covers Chapter 20, emerging technologies, supplemented by assigned readings from the academic literature. Week 15 involves the capstone project presentation and discussion.


## How This Book Is Organized

The book contains twenty chapters organized into five parts that follow a deliberate progression. Part I (Chapters 1 through 3) builds the conceptual foundation without introducing any tools. Parts II, III, and IV each teach one tool in depth, with Excel covered in Chapters 4 through 8, SQL in Chapters 9 through 12, and Power BI in Chapters 13 through 16. Part V (Chapters 17 through 20) integrates all three tools in applied projects that span financial reporting, cost accounting, forensic analytics, and emerging technologies. A comprehensive case closes each part, requiring students to combine material from all chapters in that part into a multi-component deliverable.

Six appendices provide reference material including a software installation guide, complete dataset documentation with Entity-Relationship diagrams, and quick reference guides for Excel functions, SQL syntax, and DAX functions. Appendix F maps every exercise in the book to the relevant competency areas in the AICPA, IMA, and IFAC frameworks, supporting instructors who need to align their course with accreditation requirements.


## A Note on Professional Standards and Research

This textbook references professional standards and peer-reviewed research throughout its chapters. These references serve two purposes. First, they ground the analytical techniques in the professional context where students will apply them. When a chapter on audit analytics references the AICPA's guidance on data analytics in auditing (AICPA, 2017), students see that the techniques they are learning are not academic exercises but tools that professional standards expect them to use. Second, the references connect the practical instruction to the broader body of knowledge in accounting and information systems. Students who read the annotated Further Reading sections will find pathways into the research literature that informs and extends what the textbook teaches.

The profession's integration of analytics into its competency frameworks has accelerated in recent years. The AICPA has embedded data analytics across its pre-certification curriculum. The IMA has emphasized technology and analytics in the Certified Management Accountant examination content. The IFAC has published guidance on the technology competencies that accounting graduates need (IFAC, 2019). These developments confirm that the skills taught in this book are not supplementary. They are foundational to the practice of accounting in the current environment.

---

# To the Student {.unnumbered}

You are beginning a book that will change how you work with accounting data. The accounting courses you have taken so far taught you to understand financial statements, apply standards, calculate ratios, and interpret results. Those skills remain essential. What this book adds is the ability to work directly with the data that produces those statements, ratios, and results. Instead of receiving a finished trial balance and analyzing it, you will learn to query a database, extract the general ledger entries, and build the trial balance yourself. Instead of reading a variance report, you will learn to calculate the variances from production data and present them in an interactive dashboard. Instead of reviewing a sample of transactions that someone else selected, you will learn to test the entire population and let the data reveal the anomalies.

This book assumes no prior experience with analytics or programming. If you have never written a SQL query, never built a PivotTable, and never opened Power BI, you are exactly the audience this book was written for. Every technique is introduced from the ground up with step-by-step guided tutorials that you can follow at your own pace. The tutorials build on one another, so the output of one often serves as the input for the next, and the complexity increases gradually across chapters.


## What to Expect

The book follows a consistent structure that will become familiar after the first few chapters. Each chapter opens with learning objectives that tell you what you will be able to do after completing the chapter. An opening scenario places you in a professional role and describes a task that motivates the material. The body of the chapter alternates between conceptual explanation and hands-on tutorials. Callout boxes provide practical tips, warnings, and connections to other parts of the book. Each chapter closes with a summary, key terms, review questions, and applied exercises.

The applied exercises at the end of each chapter sit in three sections by accounting perspective, namely financial accounting, managerial accounting, and auditing. You will complete exercises in all three perspectives regardless of which area of accounting interests you most, because analytical techniques transfer across roles and understanding how the same technique serves different purposes will broaden your professional range.


## The Three Tools

You will learn three tools in this book, each suited to a different stage of the analytics workflow.

Microsoft Excel is the tool you will use first. Chapters 4 through 8 teach you to organize data in structured tables, clean and prepare messy data, build PivotTables for summarization, run regression models, and perform audit analytics procedures. Excel is most powerful for ad hoc analysis, financial modeling, and workpaper preparation.

SQL is introduced in Chapters 9 through 12. SQL stands for Structured Query Language, and it is the standard language for retrieving data from relational databases. You will use a free, lightweight database system called SQLite that requires no server and runs on any operating system. SQL is most powerful when working with large datasets, when data spans multiple related tables that must be combined, and when you want to save and reuse your analytical procedures.

Microsoft Power BI is introduced in Chapters 13 through 16. Power BI is a business intelligence platform that lets you build interactive dashboards and reports. You will connect Power BI to the same Charles River data you used in Excel and SQL, create data models, write DAX formulas for calculated measures, and design dashboards that stakeholders can explore on their own.

In Part V of the book, you will use all three tools together. You will extract data with SQL, analyze it in Excel, and present results in Power BI within a single integrated project.


## The Dataset

You will work with one dataset throughout this book, the Charles River Accounting Dataset. Charles River is a fictional mid-size home furnishings company that sells goods, manufactures selected product lines, and provides hourly design services, generating the full range of accounting transactions you will analyze across the chapters. The dataset ships as an SQLite database, an Excel workbook, and a CSV package, so you can use the same data in every tool the book covers. The About the Dataset section that follows describes the company, the table groups, and the formats in full detail.


## How to Succeed

The most important habit you can develop is to do the tutorials yourself rather than reading through them passively. Open the dataset, follow the steps, and verify your results at each checkpoint. When you make an error, diagnosing and correcting it teaches you more than getting it right the first time. The guided tutorials are designed so that you can complete them independently at your own pace, and they prepare you directly for the applied exercises that follow.

A second important habit is to read the conceptual material before jumping to the tutorials. The concepts explain why a technique works and when it is appropriate. The tutorials show you how to execute it. Both are necessary. A student who can execute a Benford's Law analysis without understanding what the results mean or when the test is appropriate has a technical skill but not an analytical one. This book aims to develop both.

Finally, pay attention to the connections across chapters and tools. The "Connecting the Dots" callout boxes link the current topic to material elsewhere in the book. The three-perspective exercise structure shows you how the same technique applies in different contexts. The comprehensive cases at the end of each part ask you to integrate everything you have learned. These connections are where the deepest learning happens, because they move you from knowing how to use a tool to understanding how to solve a problem.

---

# About the Dataset {.unnumbered}

This textbook is built around one integrated dataset, the Charles River Accounting Dataset. Rather than using multiple databases at different levels of complexity, this book uses a single company that students learn deeply over the course of twenty chapters. Every chapter builds on the same data environment, so a customer order analyzed in an Excel chapter appears in the general ledger queried in a SQL chapter and surfaces in a Power BI dashboard built later. This continuity reinforces learning and mirrors real professional practice, where accountants work within one company's data for extended periods.


## The Company

Charles River is a fictional mid-size company situated in the greater Boston area that designs and sells home furnishings through wholesale and direct-to-business channels. The product catalog includes furniture, lighting, textiles, and decorative accessories organized into product families that students can visualize and compare analytically. Charles River manufactures selected product lines in-house from raw materials and packaging, purchases other finished goods from domestic and international suppliers, and warehouses inventory across multiple locations. The company also operates an interior design services practice that bills customers by the hour, giving students a second revenue model within the same business. Charles River employs approximately 60 people across six departments and maintains a full chart of accounts with cost center tracking.

This hybrid operating model is a deliberate design choice. A company that both buys and makes products, sells both goods and services, and manages both manufacturing labor and salaried professionals creates the range of accounting transactions that students need to encounter. Students can compare purchased products with manufactured products, trace how customer demand drives purchasing and production decisions, analyze how labor supports both operations and services, and see how all of these activities flow into the general ledger.


## The Table Groups

The Charles River database contains 77 tables organized into ten groups. The book introduces these groups progressively, starting with the simplest tables in the early chapters and expanding into more complex groups as students build skill. The table below summarizes the ten groups, and the paragraphs that follow describe each group in more detail.

| Table Group | Number of Tables | Key Tables | Primary Accounting Use |
|---|---|---|---|
| Accounting Core | 3 | Account, JournalEntry, GLEntry | Financial reporting, audit analytics, period-close analysis |
| Order-to-Cash (O2C) | 22 | Customer, SalesOrder, SalesOrderLine, Shipment, SalesInvoice, CashReceipt, ServiceEngagement | Revenue analysis, receivables management, design services margin analysis |
| Procure-to-Pay (P2P) | 9 | PurchaseOrder, PurchaseOrderLine, GoodsReceipt, PurchaseInvoice, DisbursementPayment | Purchasing analytics, three-way matching, vendor evaluation, duplicate payment detection |
| Manufacturing | 14 | WorkOrder, BillOfMaterial, MaterialIssue, ProductionCompletion, WorkOrderClose | Standard cost versus actual cost analysis, production performance, material usage variance |
| Payroll and Time | 14 | PayrollRegister, LaborTimeEntry, PayrollPayment, TimeClockEntry | Labor cost analysis, payroll compliance testing, workforce analytics |
| Fixed Assets and Financing | 4 | FixedAsset, FixedAssetEvent, DebtAgreement, DebtScheduleLine | Depreciation analysis, asset lifecycle tracking, debt amortization |
| Master Data | 3 | Item, Warehouse, Employee | Shared reference data for products, locations, and people across all groups |
| Organizational Planning | 3 | CostCenter, Budget, BudgetLine | Departmental budgetary control, responsibility accounting, budget-versus-actual analysis |
| Demand Planning and MRP | 5 | DemandForecast, InventoryPolicy, SupplyPlanRecommendation, MaterialRequirementPlan, RoughCutCapacityPlan | Demand forecasting, inventory optimization, production planning |

The Accounting Core group contains three tables, namely Account, JournalEntry, and GLEntry. These represent the chart of accounts, the finance-controlled journal headers, and the posted ledger detail. Every business cycle in the database ultimately flows into GLEntry, making it the single source of truth for the company's financial position. This group is the anchor for financial reporting, audit analytics, and period-close analysis.

The Order-to-Cash group contains 22 tables covering the full revenue cycle from customer order through cash collection, including sales orders, shipments, invoices, cash receipts, commercial pricing, design service engagements and billing, sales commissions, and a complete returns and credits chain through credit memos and customer refunds. This is the richest group in the database.

The Procure-to-Pay group contains nine tables covering the full purchasing cycle from internal requisition through vendor payment, including purchase orders, goods receipts, supplier invoices, and disbursement payments. This group supports three-way matching, vendor analytics, and accounts payable management.

The Manufacturing group contains 14 tables covering production planning, material usage, labor support, completion, and variance analysis. Tables include bills of material, routings, work centers, work orders, material issues, production completions, and work order close records.

The Payroll and Time group contains 14 tables covering workforce management from shift scheduling through payroll settlement. Tables include shift definitions, employee rosters, time clock entries, labor time entries, payroll registers, payroll payments, and liability remittances. This group supports labor cost analysis and payroll compliance testing.

The Fixed Assets and Financing group contains four tables covering the fixed asset subledger including acquisition, depreciation, and disposal, along with note-payable financing through debt agreements and amortization schedules.

The Master Data group contains three shared reference tables, namely Item, Warehouse, and Employee. These are used across all other groups for product, location, and people information.

The Organizational Planning group contains three tables, namely CostCenter, Budget, and BudgetLine. These support budgetary control and responsibility accounting exercises.

The Demand Planning and MRP group contains five tables covering demand forecasting, inventory policy, supply plan recommendations, material requirements planning, and rough-cut capacity planning.

The Design Services tables are distributed within the Order-to-Cash group but represent a distinct business process. Service engagements, employee assignments, approved time entries, and billing lines give students a complete service revenue cycle alongside the goods revenue cycle.


## The Business Cycles

The table groups map to six business cycles that define how Charles River operates. The Order-to-Cash cycle traces customer demand from sales orders through shipments, invoicing, and cash receipts. The Design Services cycle, a branch within the O2C group, covers hourly consulting engagements that are staffed, approved, and billed monthly, creating a second revenue path alongside product sales. The Procure-to-Pay cycle covers replenishment from requisition through purchasing, goods receipt, and vendor payment. The Manufacturing cycle turns selected products into finished goods through planning, work orders, material issue, labor support, and production completion. The Payroll cycle processes employee time records into payroll registers, payments, and remittances. The Manual Journals and Close cycle handles accruals, reclassifications, and period-end adjustments through the JournalEntry table. Every one of these cycles ultimately flows into GLEntry, where the entire company's financial activity is recorded.


## How the Table Groups Connect

The table groups are not isolated. Cross-group bridge keys connect operational activity to the posted ledger and to shared master data. ItemID links product-level analysis across sales, purchasing, manufacturing, and planning. AccountID connects the general ledger, budgets, and the chart of accounts. EmployeeID links payroll, time, labor entries, and service engagements. CostCenterID connects operating activity, labor, budgets, and reporting by organizational unit. Most importantly, the GLEntry table includes SourceDocumentType, SourceDocumentID, and SourceLineID fields that allow students to trace any ledger posting back to the operational event that created it. This source-to-ledger traceability is one of the most valuable features of the dataset for teaching purposes, because it lets students see exactly how a shipment becomes revenue, how a goods receipt becomes an inventory entry, or how a payroll register becomes a wage expense.


## Progressive Introduction

The book does not ask students to work with all 77 tables from the beginning. Chapters in Part I introduce the company, its business model, and the table group structure at a conceptual level. Part II chapters use primarily the Order-to-Cash core tables (Customer, SalesOrder, SalesOrderLine, Item) for Excel exercises, expanding into Accounting Core and Procure-to-Pay tables for audit analytics in Chapter 8. Part III chapters use progressively larger subsets of the database as SQL skills develop, and by Chapter 12 students work across multiple table groups in a single query. Part IV chapters model relationships across groups in Power BI, building dashboards that span the full database. Part V chapters require students to move fluently across all table groups and all three tools within integrated projects.


## Distribution Formats

The dataset is provided in three formats. The SQLite database is used for all SQL work in Chapters 9 through 12 and for data extraction in Part V. It requires no server installation, runs on any operating system, and works with DB Browser for SQLite, the free database tool used throughout the book. The Excel workbook is used for all spreadsheet work in Chapters 4 through 8. The CSV package provides maximum flexibility for import into any tool, including Power BI. All three formats contain identical data, so students work with the same underlying information regardless of which tool a given chapter uses.

Complete documentation for every table in the database, including column names, data types, primary and foreign key relationships, cross-group bridge keys, and Entity-Relationship diagrams for each table group, appears in Appendix B.

---

## References

AICPA (American Institute of Certified Public Accountants). (2017). *Guide to audit data analytics.* AICPA.

Borthick, A. F., and Jones, D. R. (2000). The motivation for collaborative discovery learning online and its application in an information systems assurance course. *Issues in Accounting Education*, 15(2), 181-210.

IFAC (International Federation of Accountants). (2019). *Technology and the profession: A guide for professional accountancy organizations.* IFAC.

Sledgianowski, D., Gomaa, M., and Tan, C. (2017). Toward integration of Big Data, technology, and information systems competencies into the accounting curriculum. *Journal of Accounting Education*, 38, 81-93.
