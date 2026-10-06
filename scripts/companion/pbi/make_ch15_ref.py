"""Write the chapter 15 reference model (chapter 14 plus Tutorials 15.1-15.3) as a Power BI project (PBIP, TMDL + PBIR).

It mirrors Tutorials 13.1 and 14.1-14.3: the sales star (SalesInvoiceLine with the invoice header
merged in, Item, Customer, Date), the ledger star (GLEntry with the close flag, Account,
CostCenter, Date), and every measure the chapter prints. SalesInvoice and JournalEntry are
staging queries (Enable load cleared), stored as shared expressions.
"""
import json
import shutil
import uuid
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, XLSX as _XLSX  # noqa: E402

OUT = REFERENCE_MODELS / "ch15_ref"
NAME = "CR15"
XLSX = str(_XLSX)
T = "\t"


def src(table: str) -> str:
    return (f'Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),\n'
            f'    Data = Source{{[Item="{table}",Kind="Table"]}}[Data]')


def m_block(body: str, level: int) -> str:
    """Indent an M expression for a partition source (level = tabs of the property)."""
    pad = T * (level + 1)
    return "\n".join(pad + line if line else "" for line in body.strip("\n").split("\n"))


def column(name, dtype, source=None, fmt=None, summarize="none", hidden=False, extra=()):
    q = f"'{name}'" if any(c in name for c in " .=:'") else name
    lines = [f"{T}column {q}", f"{T*2}dataType: {dtype}"]
    if fmt:
        lines.append(f"{T*2}formatString: {fmt}")
    if hidden:
        lines.append(f"{T*2}isHidden")
    lines.append(f"{T*2}summarizeBy: {summarize}")
    lines.append(f"{T*2}sourceColumn: {source or name}")
    lines += [f"{T*2}{e}" for e in extra]
    return "\n".join(lines) + "\n"


def measure(name, dax, fmt=None, desc=None):
    q = f"'{name}'" if any(c in name for c in " .=:'%&") else name
    out = []
    if desc:
        out.append(f"{T}/// {desc}")
    dax = dax.strip("\n")
    if "\n" in dax:
        out.append(f"{T}measure {q} =")
        out += [T * 3 + line for line in dax.split("\n")]
    else:
        out.append(f"{T}measure {q} = {dax}")
    if fmt:
        out.append(f"{T*2}formatString: {fmt}")
    return "\n".join(out) + "\n"


def table(name, columns, partition_m=None, partition_dax=None, measures=(), props=()):
    q = f"'{name}'" if " " in name else name
    out = [f"table {q}"] + [f"{T}{p}" for p in props] + [""]
    out += [m for m in measures]
    out += [c for c in columns]
    if partition_m:
        out.append(f"{T}partition {q} = m\n{T*2}mode: import\n{T*2}source =\n{m_block(partition_m, 2)}\n")
    if partition_dax:
        body = "\n".join(T * 3 + line for line in partition_dax.strip("\n").split("\n"))
        out.append(f"{T}partition {q} = calculated\n{T*2}mode: import\n{T*2}source =\n{body}\n")
    return "\n".join(out) + "\n"


MONEY = "#,0.00"
tables = {}

tables["Customer"] = table("Customer", [
    column("CustomerID", "int64", hidden=True),
    column("CustomerName", "string"),
    column("CustomerSegment", "string"),
    column("Region", "string"),
], partition_m=f"""
let
    {src("T4_Customer")},
    Kept = Table.SelectColumns(Data, {{"CustomerID", "CustomerName", "CustomerSegment", "Region"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"CustomerID", Int64.Type}}, {{"CustomerName", type text}},
        {{"CustomerSegment", type text}}, {{"Region", type text}}}})
in
    Typed
""")

tables["Item"] = table("Item", [
    column("ItemID", "int64", hidden=True),
    column("ItemCode", "string"),
    column("ItemName", "string"),
    column("ItemGroup", "string"),
    column("StandardCost", "double", fmt=MONEY),
    column("ListPrice", "double", fmt=MONEY),
    column("ProductType", "string"),
    column("StandardLaborHoursPerUnit", "double"),
], partition_m=f"""
let
    {src("T44_Item")},
    Kept = Table.SelectColumns(Data, {{"ItemID", "ItemCode", "ItemName", "ItemGroup", "StandardCost", "ListPrice",
        "StandardLaborHoursPerUnit"}}),
    Sellable = Table.SelectRows(Kept, each [ListPrice] <> null),
    WithType = Table.AddColumn(Sellable, "ProductType", each Text.Middle([ItemCode], 4, 3), type text),
    Typed = Table.TransformColumnTypes(WithType, {{{{"ItemID", Int64.Type}}, {{"ItemCode", type text}},
        {{"ItemName", type text}}, {{"ItemGroup", type text}}, {{"StandardCost", type number}}, {{"ListPrice", type number}},
        {{"StandardLaborHoursPerUnit", type number}}}})
in
    Typed
""")

sales_measures = [
    measure("Revenue", "SUM ( SalesInvoiceLine[LineTotal] )", MONEY, "Invoiced revenue: the sum of LineTotal."),
    measure("List Amount", "SUM ( SalesInvoiceLine[ListAmount] )", MONEY),
    measure("Discounts", "SUM ( SalesInvoiceLine[DiscountAmount] )", MONEY),
    measure("Price Before Discount", "SUMX ( SalesInvoiceLine, SalesInvoiceLine[Quantity] * SalesInvoiceLine[UnitPrice] )", MONEY),
    measure("Discount Rate", "DIVIDE ( [Discounts], [Price Before Discount] )", "0.00%"),
    measure("Average of Discount", "AVERAGE ( SalesInvoiceLine[Discount] )", "0.00%"),
    measure("Invoices", "DISTINCTCOUNT ( SalesInvoiceLine[SalesInvoiceID] )", "#,0"),
    measure("Invoice Lines", "COUNTROWS ( SalesInvoiceLine )", "#,0"),
    measure("Standard Cost", "SUMX (\n    SalesInvoiceLine,\n    SalesInvoiceLine[Quantity] * RELATED ( 'Item'[StandardCost] )\n)", MONEY),
    measure("Gross Margin", "[Revenue] - [Standard Cost]", MONEY),
    measure("Margin %", "VAR Rev = [Revenue]\nRETURN\n    DIVIDE ( Rev - [Standard Cost], Rev )", "0.00%"),
    measure("Furniture Revenue", """CALCULATE ( [Revenue], 'Item'[ItemGroup] = "Furniture" )""", MONEY),
    measure("Share of Revenue", "DIVIDE ( [Revenue], CALCULATE ( [Revenue], REMOVEFILTERS ( 'Item' ) ) )", "0.00%"),
    measure("Share with ALL", "DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALL ( SalesInvoiceLine ) ) )", "0.00%"),
    measure("Revenue PY", "CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )", MONEY),
    measure("Revenue YoY %", "DIVIDE ( [Revenue] - [Revenue PY], [Revenue PY] )", "0.00%"),
    measure("Revenue YTD", "TOTALYTD ( [Revenue], 'Date'[Date] )", MONEY),
    measure("Margin % PY", "CALCULATE ( [Margin %], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )", "0.00%"),
    measure("Revenue by Ship Date", "CALCULATE ( [Revenue], USERELATIONSHIP ( SalesInvoiceLine[ShipmentDate], 'Date'[Date] ) )", MONEY),
]
tables["SalesInvoiceLine"] = table("SalesInvoiceLine", [
    column("SalesInvoiceLineID", "int64", hidden=True),
    column("SalesInvoiceID", "int64", hidden=True),
    column("ItemID", "int64", hidden=True),
    column("Quantity", "double", summarize="sum"),
    column("BaseListPrice", "double", fmt=MONEY),
    column("UnitPrice", "double", fmt=MONEY),
    column("Discount", "double"),
    column("LineTotal", "double", fmt=MONEY, summarize="sum"),
    column("PromotionID", "int64", hidden=True),
    column("ShipmentLineID", "int64", hidden=True),
    column("PricingMethod", "string"),
    column("ListAmount", "double", fmt=MONEY, summarize="sum"),
    column("DiscountAmount", "double", fmt=MONEY, summarize="sum"),
    column("InvoiceNumber", "string"),
    column("InvoiceDate", "dateTime", fmt="Short Date"),
    column("CustomerID", "int64", hidden=True),
    column("ShipmentDate", "dateTime", fmt="Short Date"),
], partition_m=f"""
let
    {src("T17_SalesInvoiceLine")},
    Kept = Table.SelectColumns(Data, {{"SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "BaseListPrice",
        "UnitPrice", "Discount", "LineTotal", "PromotionID", "ShipmentLineID", "PricingMethod"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"SalesInvoiceLineID", Int64.Type}}, {{"SalesInvoiceID", Int64.Type}},
        {{"ItemID", Int64.Type}}, {{"Quantity", type number}}, {{"BaseListPrice", type number}}, {{"UnitPrice", type number}},
        {{"Discount", type number}}, {{"LineTotal", type number}}, {{"PromotionID", Int64.Type}}, {{"ShipmentLineID", Int64.Type}},
        {{"PricingMethod", type text}}}}),
    ListAmount = Table.AddColumn(Typed, "ListAmount", each [Quantity] * [BaseListPrice], type number),
    DiscountAmount = Table.AddColumn(ListAmount, "DiscountAmount", each [Quantity] * [UnitPrice] * [Discount], type number),
    Merged = Table.NestedJoin(DiscountAmount, {{"SalesInvoiceID"}}, SalesInvoice, {{"SalesInvoiceID"}}, "Header", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Header", {{"InvoiceNumber", "InvoiceDate", "CustomerID"}}),
    Shipped = Table.NestedJoin(Expanded, {{"ShipmentLineID"}}, ShipDates, {{"ShipmentLineID"}}, "Ship", JoinKind.LeftOuter),
    WithShip = Table.ExpandTableColumn(Shipped, "Ship", {{"ShipmentDate"}})
in
    WithShip
""", measures=sales_measures)

tables["Date"] = table("Date", [
    column("Date", "dateTime", source="[Date]", fmt="Short Date", extra=("isKey",)),
    column("Year", "int64", source="[Year]"),
    column("Quarter", "string", source="[Quarter]"),
    column("YearQuarter", "string", source="[YearQuarter]"),
    column("YearMonth", "string", source="[YearMonth]"),
    column("MonthNumber", "int64", source="[MonthNumber]"),
    column("MonthName", "string", source="[MonthName]", extra=("sortByColumn: MonthNumber",)),
], partition_dax="""
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2027, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "YearQuarter", YEAR ( [Date] ) & "-Q" & QUARTER ( [Date] ),
    "YearMonth", FORMAT ( [Date], "yyyy-mm" ),
    "MonthNumber", MONTH ( [Date] ),
    "MonthName", FORMAT ( [Date], "mmm" )
)
""", props=("dataCategory: Time",))

gl_measures = [
    measure("GL Amount", "CALCULATE (\n    SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ),\n    GLEntry[IsYearEndClose] = FALSE ()\n)", MONEY,
            "Debits less credits, without the year-end closing entries."),
    measure("P&L Amount", "- [GL Amount]", MONEY, "Credit-positive: revenue positive, expenses negative."),
    measure("P&L Amount with Closes", "SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] )", MONEY),
    measure("Net Income", 'CALCULATE ( [P&L Amount], Account[AccountType] IN { "Revenue", "Expense" } )', MONEY),
    measure("Net Income with Closes", 'CALCULATE ( [P&L Amount with Closes], Account[AccountType] IN { "Revenue", "Expense" } )', MONEY),
    measure("Operating Expense", 'CALCULATE ( [GL Amount], Account[AccountSubType] = "Operating Expense" )', MONEY),
    measure("Operating Expense PY", "CALCULATE ( [Operating Expense], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )", MONEY),
    measure("Operating Expense YTD", "TOTALYTD ( [Operating Expense], 'Date'[Date] )", MONEY),
    measure("Expected Operating Expense", """
VAR MonthStart = MIN ( 'Date'[Date] )
VAR PriorMonths =
    DATESBETWEEN ( 'Date'[Date], EDATE ( MonthStart, -3 ), MonthStart - 1 )
VAR MonthsInWindow =
    COUNTROWS ( CALCULATETABLE ( VALUES ( 'Date'[YearMonth] ), PriorMonths ) )
RETURN
    IF (
        HASONEVALUE ( 'Date'[YearMonth] )
            && NOT ISBLANK ( [Operating Expense] )
            && MonthsInWindow > 0,
        DIVIDE ( CALCULATE ( [Operating Expense], PriorMonths ), MonthsInWindow )
    )
""", MONEY,
            "The average operating expense of the three months before the month shown."),
    measure("Operating Expense Deviation", "DIVIDE ( [Operating Expense] - [Expected Operating Expense], [Expected Operating Expense] )", "0.0%"),
]
tables["GLEntry"] = table("GLEntry", [
    column("GLEntryID", "int64", hidden=True),
    column("PostingDate", "dateTime", fmt="Short Date"),
    column("AccountID", "int64", hidden=True),
    column("Debit", "double", fmt=MONEY, summarize="sum"),
    column("Credit", "double", fmt=MONEY, summarize="sum"),
    column("VoucherNumber", "string"),
    column("SourceDocumentType", "string"),
    column("CostCenterID", "int64", hidden=True),
    column("EntryType", "string"),
    column("IsYearEndClose", "boolean"),
], partition_m=f"""
let
    {src("T3_GLEntry")},
    Kept = Table.SelectColumns(Data, {{"GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber",
        "SourceDocumentType", "CostCenterID"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"GLEntryID", Int64.Type}}, {{"PostingDate", type date}}, {{"AccountID", Int64.Type}},
        {{"Debit", type number}}, {{"Credit", type number}}, {{"VoucherNumber", type text}}, {{"SourceDocumentType", type text}},
        {{"CostCenterID", Int64.Type}}}}),
    Merged = Table.NestedJoin(Typed, {{"VoucherNumber"}}, JournalEntry, {{"EntryNumber"}}, "Entry", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Entry", {{"EntryType"}}),
    Flagged = Table.AddColumn(Expanded, "IsYearEndClose",
        each [EntryType] <> null and Text.StartsWith([EntryType], "Year-End Close"), type logical)
in
    Flagged
""", measures=gl_measures)

tables["Account"] = table("Account", [
    column("AccountID", "int64", hidden=True),
    column("AccountNumber", "int64"),
    column("AccountName", "string"),
    column("AccountType", "string"),
    column("AccountSubType", "string"),
    column("NormalBalance", "string"),
], partition_m=f"""
let
    {src("T1_Account")},
    Kept = Table.SelectColumns(Data, {{"AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType", "NormalBalance"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"AccountID", Int64.Type}}, {{"AccountNumber", Int64.Type}}, {{"AccountName", type text}},
        {{"AccountType", type text}}, {{"AccountSubType", type text}}, {{"NormalBalance", type text}}}})
in
    Typed
""")

tables["CostCenter"] = table("CostCenter", [
    column("CostCenterID", "int64", hidden=True),
    column("CostCenterName", "string"),
], partition_m=f"""
let
    {src("T75_CostCenter")},
    Kept = Table.SelectColumns(Data, {{"CostCenterID", "CostCenterName"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"CostCenterID", Int64.Type}}, {{"CostCenterName", type text}}}})
in
    Typed
""")

# -- Chapter 15 ------------------------------------------------------------------------------

tables["PromotionProgram"] = table("PromotionProgram", [
    column("PromotionID", "int64", hidden=True),
    column("PromotionCode", "string"),
    column("PromotionName", "string"),
    column("ScopeType", "string"),
    column("DiscountPct", "double", fmt="0%"),
    column("EffectiveStartDate", "dateTime", fmt="Short Date"),
    column("EffectiveEndDate", "dateTime", fmt="Short Date"),
], partition_m=f"""
let
    {src("T7_PromotionProgram")},
    Kept = Table.SelectColumns(Data, {{"PromotionID", "PromotionCode", "PromotionName", "ScopeType", "DiscountPct",
        "EffectiveStartDate", "EffectiveEndDate"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"PromotionID", Int64.Type}}, {{"PromotionCode", type text}},
        {{"PromotionName", type text}}, {{"ScopeType", type text}}, {{"DiscountPct", type number}},
        {{"EffectiveStartDate", type date}}, {{"EffectiveEndDate", type date}}}})
in
    Typed
""")

tables["Steps"] = table("Steps", [
    column("Step", "string", source="[Step]", extra=("sortByColumn: Order",)),
    column("Order", "int64", source="[Order]"),
], partition_dax="""
DATATABLE (
    "Step", STRING,
    "Order", INTEGER,
    {
        { "At list price", 1 },
        { "Price lists and overrides", 2 },
        { "Promotions", 3 }
    }
)
""")

budget_measures = [
    measure("Gross to Net", """
SWITCH (
    SELECTEDVALUE ( Steps[Step] ),
    "At list price", [List Amount],
    "Price lists and overrides", [Price Before Discount] - [List Amount],
    "Promotions", [Revenue] - [Price Before Discount],
    [Revenue]
)
""", MONEY),
    measure("Budget", "SUM ( BudgetLine[BudgetAmount] )", MONEY),
    measure("Actual", "[GL Amount]", MONEY),
    measure("Variance", "[Actual] - [Budget]", MONEY),
    measure("Variance %", "DIVIDE ( [Variance], [Budget] )", "0.0%"),
    measure("Flexed Budget", """
VAR CommissionBudget =
    CALCULATE ( [Budget], KEEPFILTERS ( Account[AccountNumber] = 6290 ) )
VAR CommissionRate =
    DIVIDE (
        CALCULATE ( [Budget], REMOVEFILTERS ( Account ), REMOVEFILTERS ( CostCenter ),
            Account[AccountNumber] = 6290 ),
        CALCULATE ( [Budget], REMOVEFILTERS ( Account ), REMOVEFILTERS ( CostCenter ),
            Account[AccountNumber] IN { 4010, 4020, 4030, 4040 } )
    )
VAR ProductRevenue =
    CALCULATE ( [Revenue], 'Item'[ItemGroup] <> "Services" )
RETURN
    [Budget] - CommissionBudget
        + IF ( NOT ISBLANK ( CommissionBudget ), CommissionRate * ProductRevenue )
""", MONEY),
    measure("Volume Effect", "[Flexed Budget] - [Budget]", MONEY),
    measure("Classification Effect", """
CALCULATE ( [Actual] - [Budget], KEEPFILTERS ( Account[AccountNumber] = 6130 ) )
""", MONEY),
    measure("Remaining Variance", "[Variance] - [Volume Effect] - [Classification Effect]", MONEY),
    measure("Remaining %", "DIVIDE ( [Remaining Variance], [Flexed Budget] )", "0.0%"),
]
tables["BudgetLine"] = table("BudgetLine", [
    column("BudgetLineID", "int64", hidden=True),
    column("FiscalYear", "int64"),
    column("Month", "int64"),
    column("AccountID", "int64", hidden=True),
    column("CostCenterID", "int64", hidden=True),
    column("ItemID", "int64", hidden=True),
    column("BudgetAmount", "double", fmt=MONEY, summarize="sum"),
    column("BudgetCategory", "string"),
    column("DriverType", "string"),
    column("BudgetDate", "dateTime", fmt="Short Date"),
], partition_m=f"""
let
    {src("T77_BudgetLine")},
    Kept = Table.SelectColumns(Data, {{"BudgetLineID", "FiscalYear", "Month", "AccountID", "CostCenterID", "ItemID",
        "BudgetAmount", "BudgetCategory", "DriverType"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"BudgetLineID", Int64.Type}}, {{"FiscalYear", Int64.Type}},
        {{"Month", Int64.Type}}, {{"AccountID", Int64.Type}}, {{"CostCenterID", Int64.Type}}, {{"ItemID", Int64.Type}},
        {{"BudgetAmount", type number}}, {{"BudgetCategory", type text}}, {{"DriverType", type text}}}}),
    PandL = Table.SelectRows(Typed, each [BudgetCategory] <> "Balance Sheet"),
    Dated = Table.AddColumn(PandL, "BudgetDate", each #date([FiscalYear], [Month], 1), type date)
in
    Dated
""", measures=budget_measures)

plant_measures = [
    measure("Manufacturing Hours", """
CALCULATE (
    SUM ( LaborTimeEntry[RegularHours] ) + SUM ( LaborTimeEntry[OvertimeHours] ),
    LaborTimeEntry[LaborType] <> "NonManufacturing"
)
""", "#,0"),
    measure("Direct Hours", """CALCULATE ( [Manufacturing Hours], LaborTimeEntry[LaborType] = "Direct Manufacturing" )""", "#,0"),
    measure("Indirect Hours", """CALCULATE ( [Manufacturing Hours], LaborTimeEntry[LaborType] = "Indirect Manufacturing" )""", "#,0"),
    measure("Overtime Hours", """
CALCULATE (
    SUM ( LaborTimeEntry[OvertimeHours] ),
    LaborTimeEntry[LaborType] <> "NonManufacturing"
)
""", "#,0"),
    measure("Standard Hours", """
SUMX (
    ProductionCompletionLine,
    ProductionCompletionLine[QuantityCompleted] * RELATED ( 'Item'[StandardLaborHoursPerUnit] )
)
""", "#,0"),
    measure("Standard Hours to Cut-off", """
VAR LastTimeRecord =
    CALCULATE ( MAX ( LaborTimeEntry[WorkDate] ), REMOVEFILTERS () )
RETURN
    CALCULATE ( [Standard Hours], KEEPFILTERS ( 'Date'[Date] <= LastTimeRecord ) )
""", "#,0"),
    measure("Hours per Standard Hour", "DIVIDE ( [Manufacturing Hours], [Standard Hours to Cut-off] )", "0.00"),
    measure("Hours per Standard Hour TTM", """
VAR Window =
    DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -12, MONTH )
VAR MonthsInWindow =
    COUNTROWS ( CALCULATETABLE ( VALUES ( 'Date'[YearMonth] ), Window ) )
RETURN
    IF (
        MonthsInWindow = 12 && NOT ISBLANK ( [Manufacturing Hours] ),
        DIVIDE (
            CALCULATE ( [Manufacturing Hours], Window ),
            CALCULATE ( [Standard Hours to Cut-off], Window )
        )
    )
""", "0.00"),
    measure("Overtime Share", "DIVIDE ( [Overtime Hours], [Manufacturing Hours] )", "0.0%"),
]
tables["LaborTimeEntry"] = table("LaborTimeEntry", [
    column("LaborTimeEntryID", "int64", hidden=True),
    column("EmployeeID", "int64", hidden=True),
    column("WorkOrderOperationID", "int64", hidden=True),
    column("WorkDate", "dateTime", fmt="Short Date"),
    column("LaborType", "string"),
    column("RegularHours", "double", summarize="sum"),
    column("OvertimeHours", "double", summarize="sum"),
    column("ExtendedLaborCost", "double", fmt=MONEY, summarize="sum"),
    column("WorkCenterID", "int64", hidden=True),
], partition_m=f"""
let
    {src("T60_LaborTimeEntry")},
    Kept = Table.SelectColumns(Data, {{"LaborTimeEntryID", "EmployeeID", "WorkOrderOperationID", "WorkDate", "LaborType",
        "RegularHours", "OvertimeHours", "ExtendedLaborCost"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"LaborTimeEntryID", Int64.Type}}, {{"EmployeeID", Int64.Type}},
        {{"WorkOrderOperationID", Int64.Type}}, {{"WorkDate", type date}}, {{"LaborType", type text}},
        {{"RegularHours", type number}}, {{"OvertimeHours", type number}}, {{"ExtendedLaborCost", type number}}}}),
    Merged = Table.NestedJoin(Typed, {{"WorkOrderOperationID"}}, Operations, {{"WorkOrderOperationID"}}, "Op", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Op", {{"WorkCenterID"}})
in
    Expanded
""", measures=plant_measures)

tables["ProductionCompletionLine"] = table("ProductionCompletionLine", [
    column("ProductionCompletionLineID", "int64", hidden=True),
    column("ProductionCompletionID", "int64", hidden=True),
    column("ItemID", "int64", hidden=True),
    column("QuantityCompleted", "double", summarize="sum"),
    column("CompletionDate", "dateTime", fmt="Short Date"),
], partition_m=f"""
let
    {src("T57_ProductionCompletionLine")},
    Kept = Table.SelectColumns(Data, {{"ProductionCompletionLineID", "ProductionCompletionID", "ItemID", "QuantityCompleted"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"ProductionCompletionLineID", Int64.Type}}, {{"ProductionCompletionID", Int64.Type}},
        {{"ItemID", Int64.Type}}, {{"QuantityCompleted", type number}}}}),
    Merged = Table.NestedJoin(Typed, {{"ProductionCompletionID"}}, Completions, {{"ProductionCompletionID"}}, "H", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "H", {{"CompletionDate"}})
in
    Expanded
""")

tables["Employee"] = table("Employee", [
    column("EmployeeID", "int64", hidden=True),
    column("EmployeeName", "string"),
    column("JobTitle", "string"),
    column("PayClass", "string"),
], partition_m=f"""
let
    {src("T74_Employee")},
    Kept = Table.SelectColumns(Data, {{"EmployeeID", "EmployeeName", "JobTitle", "PayClass"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"EmployeeID", Int64.Type}}, {{"EmployeeName", type text}},
        {{"JobTitle", type text}}, {{"PayClass", type text}}}})
in
    Typed
""")

tables["WorkCenter"] = table("WorkCenter", [
    column("WorkCenterID", "int64", hidden=True),
    column("WorkCenterCode", "string"),
    column("WorkCenterName", "string"),
], partition_m=f"""
let
    {src("T47_WorkCenter")},
    Kept = Table.SelectColumns(Data, {{"WorkCenterID", "WorkCenterCode", "WorkCenterName"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"WorkCenterID", Int64.Type}}, {{"WorkCenterCode", type text}},
        {{"WorkCenterName", type text}}}})
in
    Typed
""")

expressions = f"""expression SalesInvoice =
		let
		    Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),
		    Data = Source{{[Item="T16_SalesInvoice",Kind="Table"]}}[Data],
		    Kept = Table.SelectColumns(Data, {{"SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID"}}),
		    Typed = Table.TransformColumnTypes(Kept, {{{{"SalesInvoiceID", Int64.Type}}, {{"InvoiceNumber", type text}},
		        {{"InvoiceDate", type date}}, {{"CustomerID", Int64.Type}}}})
		in
		    Typed
	annotation PBI_ResultType = Table

expression JournalEntry =
		let
		    Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),
		    Data = Source{{[Item="T2_JournalEntry",Kind="Table"]}}[Data],
		    Kept = Table.SelectColumns(Data, {{"EntryNumber", "EntryType"}}),
		    Typed = Table.TransformColumnTypes(Kept, {{{{"EntryNumber", type text}}, {{"EntryType", type text}}}})
		in
		    Typed
	annotation PBI_ResultType = Table

expression ShipDates =
		let
		    Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),
		    Lines = Source{{[Item="T15_ShipmentLine",Kind="Table"]}}[Data],
		    Headers = Source{{[Item="T14_Shipment",Kind="Table"]}}[Data],
		    KeptLines = Table.SelectColumns(Lines, {{"ShipmentLineID", "ShipmentID"}}),
		    KeptHeaders = Table.SelectColumns(Headers, {{"ShipmentID", "ShipmentDate"}}),
		    Merged = Table.NestedJoin(KeptLines, {{"ShipmentID"}}, KeptHeaders, {{"ShipmentID"}}, "H", JoinKind.LeftOuter),
		    Expanded = Table.ExpandTableColumn(Merged, "H", {{"ShipmentDate"}}),
		    Typed = Table.TransformColumnTypes(Expanded, {{{{"ShipmentLineID", Int64.Type}}, {{"ShipmentDate", type date}}}})
		in
		    Typed
	annotation PBI_ResultType = Table

expression Operations =
		let
		    Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),
		    Data = Source{{[Item="T52_WorkOrderOperation",Kind="Table"]}}[Data],
		    Kept = Table.SelectColumns(Data, {{"WorkOrderOperationID", "WorkCenterID"}}),
		    Typed = Table.TransformColumnTypes(Kept, {{{{"WorkOrderOperationID", Int64.Type}}, {{"WorkCenterID", Int64.Type}}}})
		in
		    Typed
	annotation PBI_ResultType = Table

expression Completions =
		let
		    Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),
		    Data = Source{{[Item="T56_ProductionCompletion",Kind="Table"]}}[Data],
		    Kept = Table.SelectColumns(Data, {{"ProductionCompletionID", "CompletionDate"}}),
		    Typed = Table.TransformColumnTypes(Kept, {{{{"ProductionCompletionID", Int64.Type}}, {{"CompletionDate", type date}}}})
		in
		    Typed
	annotation PBI_ResultType = Table
"""


def rel(frm, to, active=True):
    lines = [f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, f"{NAME}/{frm}/{to}")}", f"{T}fromColumn: {frm}", f"{T}toColumn: {to}"]
    if not active:
        lines.append(f"{T}isActive: false")
    return "\n".join(lines) + "\n"


relationships = "\n".join([
    rel("SalesInvoiceLine.ItemID", "Item.ItemID"),
    rel("SalesInvoiceLine.CustomerID", "Customer.CustomerID"),
    rel("SalesInvoiceLine.InvoiceDate", "Date.Date"),
    rel("SalesInvoiceLine.ShipmentDate", "Date.Date", active=False),
    rel("GLEntry.AccountID", "Account.AccountID"),
    rel("GLEntry.CostCenterID", "CostCenter.CostCenterID"),
    rel("GLEntry.PostingDate", "Date.Date"),
    rel("SalesInvoiceLine.PromotionID", "PromotionProgram.PromotionID"),
    rel("BudgetLine.AccountID", "Account.AccountID"),
    rel("BudgetLine.CostCenterID", "CostCenter.CostCenterID"),
    rel("BudgetLine.BudgetDate", "Date.Date"),
    rel("LaborTimeEntry.EmployeeID", "Employee.EmployeeID"),
    rel("LaborTimeEntry.WorkCenterID", "WorkCenter.WorkCenterID"),
    rel("LaborTimeEntry.WorkDate", "Date.Date"),
    rel("ProductionCompletionLine.ItemID", "Item.ItemID"),
    rel("ProductionCompletionLine.CompletionDate", "Date.Date"),
])

model = """model Model
	culture: en-US
	defaultPowerBIDataSourceVersion: powerBI_V3
	sourceQueryCulture: en-US
	dataAccessOptions
		legacyRedirects
		returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 0

annotation PBI_QueryOrder = ["Customer","Item","SalesInvoice","SalesInvoiceLine","JournalEntry","GLEntry","Account","CostCenter","ShipDates","PromotionProgram","BudgetLine","Operations","LaborTimeEntry","Completions","ProductionCompletionLine","Employee","WorkCenter"]
"""

database = "database CR15\n\tcompatibilityLevel: 1601\n"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


sm = OUT / f"{NAME}.SemanticModel"
rp = OUT / f"{NAME}.Report"
write(OUT / f"{NAME}.pbip", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
    "settings": {"enableAutoRecovery": True}}, indent=2))
write(sm / "definition.pbism", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2", "settings": {}}, indent=2))
write(sm / "definition" / "database.tmdl", database)
write(sm / "definition" / "model.tmdl", model)
write(sm / "definition" / "expressions.tmdl", expressions)
write(sm / "definition" / "relationships.tmdl", relationships)
for name, text in tables.items():
    write(sm / "definition" / "tables" / f"{name}.tmdl", text)
write(rp / "definition.pbir", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2))
write(rp / "definition" / "version.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0"}, indent=2))
write(rp / "definition" / "report.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY26SU09", "reportVersionAtImport": {
        "visual": "2.12.0", "page": "2.1.0", "report": "3.3.0"}, "type": "SharedResources"}}}, indent=2))
write(rp / "definition" / "pages" / "pages.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "pageOrder": ["validation"], "activePageName": "validation"}, indent=2))
write(rp / "definition" / "pages" / "validation" / "page.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": "validation", "displayName": "Validation", "displayOption": "FitToPage",
    "height": 720, "width": 1280}, indent=2))
print("wrote", OUT)
for p in sorted(OUT.rglob("*")):
    if p.is_file():
        print("  ", p.relative_to(OUT))
