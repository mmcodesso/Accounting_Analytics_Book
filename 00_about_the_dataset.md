---
format:
  html:
    number-sections: false
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
