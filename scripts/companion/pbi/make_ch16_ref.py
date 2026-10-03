"""Write the chapter 16 reference model, Audit Monitoring (AM16), as a Power BI project (PBIP).

It mirrors Tutorials 16.1 and 16.2: JournalEntry with Chapter 8's five flags and a risk score,
the journal lines from the ledger, PurchaseOrder and PayrollRegister with their flags, three
exception queries (Unpivot, staging), the appended Exceptions register, the Tests table, Date,
Employee, and the cost-center review table of Tutorial 16.3 Step 1.
"""
import json
import uuid
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, XLSX as _XLSX  # noqa: E402

OUT = REFERENCE_MODELS / "ch16_ref"
NAME = "AM16"
XLSX = str(_XLSX)
T = "\t"


def src(table: str) -> str:
    return (f'Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),\n'
            f'    Data = Source{{[Item="{table}",Kind="Table"]}}[Data]')


def m_block(body: str, level: int) -> str:
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


def measure(name, dax, fmt=None):
    q = f"'{name}'" if any(c in name for c in " .=:'%&,") else name
    dax = dax.strip("\n")
    if "\n" in dax:
        out = [f"{T}measure {q} ="] + [T * 3 + line for line in dax.split("\n")]
    else:
        out = [f"{T}measure {q} = {dax}"]
    if fmt:
        out.append(f"{T*2}formatString: {fmt}")
    return "\n".join(out) + "\n"


def table(name, columns, partition_m=None, partition_dax=None, measures=(), props=()):
    q = f"'{name}'" if " " in name else name
    out = [f"table {q}"] + [f"{T}{p}" for p in props] + [""]
    out += list(measures) + list(columns)
    if partition_m:
        out.append(f"{T}partition {q} = m\n{T*2}mode: import\n{T*2}source =\n{m_block(partition_m, 2)}\n")
    if partition_dax:
        body = "\n".join(T * 3 + line for line in partition_dax.strip("\n").split("\n"))
        out.append(f"{T}partition {q} = calculated\n{T*2}mode: import\n{T*2}source =\n{body}\n")
    return "\n".join(out) + "\n"


MONEY = "#,0.00"


def staged(name):
    return f"let\n    Source = {name}\nin\n    Source"

tables = {}

# --- Employee (dimension) ------------------------------------------------------------------
tables["Employee"] = table("Employee", [
    column("EmployeeID", "int64", hidden=True),
    column("EmployeeName", "string"),
    column("JobTitle", "string"),
    column("CostCenterID", "int64", hidden=True),
    column("EmploymentStatus", "string"),
    column("TerminationDate", "dateTime", fmt="Short Date"),
    column("MaxApprovalAmount", "double", fmt=MONEY),
], partition_m=f"""
let
    {src("T74_Employee")},
    Kept = Table.SelectColumns(Data, {{"EmployeeID", "EmployeeName", "JobTitle", "CostCenterID", "EmploymentStatus",
        "TerminationDate", "MaxApprovalAmount"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"EmployeeID", Int64.Type}}, {{"EmployeeName", type text}},
        {{"JobTitle", type text}}, {{"CostCenterID", Int64.Type}}, {{"EmploymentStatus", type text}},
        {{"TerminationDate", type date}}, {{"MaxApprovalAmount", type number}}}})
in
    Typed
""")

# --- JournalEntry with the five flags (Tutorial 16.1) ---------------------------------------
je_flags = ["Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"]
je_measures = [
    measure("Entries", "COUNTROWS ( JournalEntry )", "#,0"),
    measure("Entry Amount", "SUM ( JournalEntry[TotalAmount] )", MONEY),
    measure("Line Debits", "SUM ( JournalLines[Debit] )", MONEY),
]
tables["JournalEntry"] = table("JournalEntry", [
    column("JournalEntryID", "int64", hidden=True),
    column("EntryNumber", "string"),
    column("PostingDate", "dateTime", fmt="Short Date"),
    column("EntryType", "string"),
    column("TotalAmount", "double", fmt=MONEY, summarize="sum"),
    column("CreatedByEmployeeID", "int64", hidden=True),
    column("CreatedDate", "dateTime", fmt="General Date"),
    column("ApprovedByEmployeeID", "int64", hidden=True),
    column("ApproverLimit", "double", fmt=MONEY),
] + [column(f, "int64") for f in je_flags] + [column("RiskScore", "int64")],
    partition_m=staged("JournalEntryFlags"), measures=je_measures)

tables["JournalLines"] = table("JournalLines", [
    column("GLEntryID", "int64", hidden=True),
    column("PostingDate", "dateTime", fmt="Short Date"),
    column("SourceDocumentID", "int64", hidden=True),
    column("AccountNumber", "int64"),
    column("AccountName", "string"),
    column("Debit", "double", fmt=MONEY, summarize="sum"),
    column("Credit", "double", fmt=MONEY, summarize="sum"),
], partition_m=f"""
let
    {src("T3_GLEntry")},
    Kept = Table.SelectColumns(Data, {{"GLEntryID", "PostingDate", "AccountID", "Debit", "Credit",
        "SourceDocumentType", "SourceDocumentID"}}),
    Journal = Table.SelectRows(Kept, each [SourceDocumentType] = "JournalEntry"),
    Typed = Table.TransformColumnTypes(Journal, {{{{"GLEntryID", Int64.Type}}, {{"PostingDate", type date}},
        {{"AccountID", Int64.Type}}, {{"Debit", type number}}, {{"Credit", type number}}, {{"SourceDocumentID", Int64.Type}}}}),
    Merged = Table.NestedJoin(Typed, {{"AccountID"}}, Account, {{"AccountID"}}, "Account", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Account", {{"AccountNumber", "AccountName"}}),
    Removed = Table.RemoveColumns(Expanded, {{"AccountID", "SourceDocumentType"}})
in
    Removed
""")

# --- Purchase orders and payroll (Tutorial 16.2) --------------------------------------------
tables["PurchaseOrder"] = table("PurchaseOrder", [
    column("PurchaseOrderID", "int64", hidden=True),
    column("PONumber", "string"),
    column("OrderDate", "dateTime", fmt="Short Date"),
    column("OrderTotal", "double", fmt=MONEY, summarize="sum"),
    column("CreatedByEmployeeID", "int64", hidden=True),
    column("ApprovedByEmployeeID", "int64", hidden=True),
    column("ApproverLimit", "double", fmt=MONEY),
    column("ApproverTermination", "dateTime", fmt="Short Date"),
    column("SelfApproved", "int64"), column("AboveLimit", "int64"), column("AfterTermination", "int64"),
], partition_m=staged("PurchaseOrderFlags"))

tables["PayrollRegister"] = table("PayrollRegister", [
    column("PayrollRegisterID", "int64", hidden=True),
    column("EmployeeID", "int64", hidden=True),
    column("NetPay", "double", fmt=MONEY, summarize="sum"),
    column("ApprovedByEmployeeID", "int64", hidden=True),
    column("ApprovedDate", "dateTime", fmt="Short Date"),
    column("PaymentDate", "dateTime", fmt="Short Date"),
    column("PeriodEndDate", "dateTime", fmt="Short Date"),
    column("PayDate", "dateTime", fmt="Short Date"),
    column("TerminationDate", "dateTime", fmt="Short Date"),
    column("PaidBeforeApproval", "int64"), column("AfterTermination", "int64"), column("SelfApproved", "int64"),
], partition_m=staged("PayrollFlags"))

reg_measures = [
    measure("Exceptions", "COUNTROWS ( Exceptions )", "#,0"),
    measure("Population", """
SWITCH (
    SELECTEDVALUE ( Tests[Process] ),
    "Journal entries", COUNTROWS ( JournalEntry ),
    "Purchase orders", COUNTROWS ( PurchaseOrder ),
    "Payroll", COUNTROWS ( PayrollRegister )
)""", "#,0"),
    measure("Rate per 1,000", "DIVIDE ( [Exceptions], [Population] ) * 1000", "0.0"),
]

DISPOSITIONS = (
    [("JE AboveLimit", n, "Expected", "Year-end close")
     for n in ["JE-2024-000265", "JE-2024-000266", "JE-2025-000287", "JE-2025-000288", "JE-2026-000296",
               "JE-2026-000297"]]
    + [("PO AfterTermination", n, "Deficiency", "Approver had left")
       for n in ["PO-2024-000474", "PO-2025-003922", "PO-2026-010467"]]
    + [("PR AfterTermination", n, "Deficiency", "Payee had left")
       for n in ["Register 840", "Register 2646", "Register 5420"]]
    + [("PR PaidBeforeApproval", n, "Follow up", "Paid before approval")
       for n in ["Register 2", "Register 2647", "Register 5421"]])
disp_m = ",\n        ".join("{" + ", ".join(f'"{v}"' for v in r) + "}" for r in DISPOSITIONS)

tables["Dispositions"] = table("Dispositions", [
    column("TestID", "string"), column("DocumentNumber", "string"), column("Disposition", "string"),
    column("Note", "string"),
], partition_m=f"""
let
    Source = #table(type table [TestID = text, DocumentNumber = text, Disposition = text, Note = text], {{
        {disp_m}
    }})
in
    Source
""", props=("isHidden",))

tables["Exceptions"] = table("Exceptions", [
    column("TestID", "string"),
    column("DocumentNumber", "string"),
    column("EventDate", "dateTime", fmt="Short Date"),
    column("Amount", "double", fmt=MONEY, summarize="sum"),
    column("EmployeeID", "int64", hidden=True),
    column("Disposition", "string"),
    column("Note", "string"),
], partition_m="""
let
    Source = Table.Combine({#"JE Exceptions", #"PO Exceptions", #"Payroll Exceptions"}),
    Typed = Table.TransformColumnTypes(Source, {{"EventDate", type date}}),
    Merged = Table.NestedJoin(Typed, {"TestID", "DocumentNumber"}, Dispositions, {"TestID", "DocumentNumber"},
        "Dispositions", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Dispositions", {"Disposition", "Note"})
in
    Expanded
""", measures=reg_measures)

tests_rows = [
    ("JE Weekend", "Entry created on a weekend", "Journal entries", "Chapter 8"),
    ("JE Backdated", "Entry created after its posting date", "Journal entries", "Chapter 8"),
    ("JE SelfApproved", "Entry approved by its creator", "Journal entries", "Chapter 8"),
    ("JE AboveLimit", "Entry above its approver's limit", "Journal entries", "Chapter 8"),
    ("JE RoundAmount", "Entry in whole thousands", "Journal entries", "Chapter 8"),
    ("PO SelfApproved", "Order approved by its creator", "Purchase orders", "Chapter 12"),
    ("PO AboveLimit", "Order above its approver's limit", "Purchase orders", "Chapter 12"),
    ("PO AfterTermination", "Order approved after the approver left", "Purchase orders", "Chapter 12"),
    ("PR PaidBeforeApproval", "Pay made before the register was approved", "Payroll", "Exercise 12.5"),
    ("PR AfterTermination", "Pay period ending after termination", "Payroll", "Exercise 12.5"),
    ("PR SelfApproved", "Register approved by its own employee", "Payroll", "Exercise 12.5"),
]
rows_m = ",\n        ".join("{" + ", ".join(f'"{v}"' for v in r) + "}" for r in tests_rows)
tables["Tests"] = table("Tests", [
    column("TestID", "string"), column("Test", "string"), column("Process", "string"), column("Source", "string"),
], partition_m=f"""
let
    Source = #table(type table [TestID = text, Test = text, Process = text, Source = text], {{
        {rows_m}
    }})
in
    Source
""")

tables["CostCenterReview"] = table("CostCenterReview", [
    column("CostCenterID", "int64"),
    column("CostCenterName", "string"),
    column("ManagerID", "int64"),
    column("EmployeeName", "string"),
    column("JobTitle", "string"),
    column("EmploymentStatus", "string"),
    column("TerminationDate", "dateTime", fmt="Short Date"),
], partition_m=f"""
let
    {src("T75_CostCenter")},
    Kept = Table.SelectColumns(Data, {{"CostCenterID", "CostCenterName", "ManagerID"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"CostCenterID", Int64.Type}}, {{"CostCenterName", type text}}, {{"ManagerID", Int64.Type}}}}),
    Merged = Table.NestedJoin(Typed, {{"ManagerID"}}, Employee, {{"EmployeeID"}}, "Manager", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Manager", {{"EmployeeName", "JobTitle", "EmploymentStatus", "TerminationDate"}})
in
    Expanded
""")

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


def expr(name, body):
    lines = body.strip("\n").split("\n")
    q = f"'{name}'" if " " in name else name
    return f"expression {q} =\n" + "\n".join(T * 2 + line for line in lines) + f"\n{T}annotation PBI_ResultType = Table\n"


expressions = "\n".join([
    expr("Account", f"""
let
    {src("T1_Account")},
    Kept = Table.SelectColumns(Data, {{"AccountID", "AccountNumber", "AccountName"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"AccountID", Int64.Type}}, {{"AccountNumber", Int64.Type}}, {{"AccountName", type text}}}})
in
    Typed
"""),
    expr("JournalEntryFlags", f"""
let
    {src("T2_JournalEntry")},
    Kept = Table.SelectColumns(Data, {{"JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount",
        "CreatedByEmployeeID", "CreatedDate", "ApprovedByEmployeeID"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"JournalEntryID", Int64.Type}}, {{"EntryNumber", type text}},
        {{"PostingDate", type date}}, {{"EntryType", type text}}, {{"TotalAmount", type number}},
        {{"CreatedByEmployeeID", Int64.Type}}, {{"CreatedDate", type datetime}}, {{"ApprovedByEmployeeID", Int64.Type}}}}),
    Merged = Table.NestedJoin(Typed, {{"ApprovedByEmployeeID"}}, Employee, {{"EmployeeID"}}, "Approver", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Approver", {{"MaxApprovalAmount"}}, {{"ApproverLimit"}}),
    Weekend = Table.AddColumn(Expanded, "Weekend", each if Date.DayOfWeek([CreatedDate], Day.Monday) >= 5 then 1 else 0, Int64.Type),
    Backdated = Table.AddColumn(Weekend, "Backdated", each if Date.From([CreatedDate]) > [PostingDate] then 1 else 0, Int64.Type),
    SelfApproved = Table.AddColumn(Backdated, "SelfApproved", each if [CreatedByEmployeeID] = [ApprovedByEmployeeID] then 1 else 0, Int64.Type),
    AboveLimit = Table.AddColumn(SelfApproved, "AboveLimit", each if [TotalAmount] > [ApproverLimit] then 1 else 0, Int64.Type),
    RoundAmount = Table.AddColumn(AboveLimit, "RoundAmount", each if Number.Mod([TotalAmount], 1000) = 0 then 1 else 0, Int64.Type),
    Score = Table.AddColumn(RoundAmount, "RiskScore", each [Weekend] + [Backdated] + [SelfApproved] + [AboveLimit] + [RoundAmount], Int64.Type)
in
    Score
"""),
    expr("JE Exceptions", """
let
    Source = JournalEntryFlags,
    Unpivoted = Table.Unpivot(Source, {"Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"}, "Attribute", "Value"),
    Flagged = Table.SelectRows(Unpivoted, each [Value] = 1),
    TestID = Table.AddColumn(Flagged, "TestID", each "JE " & [Attribute], type text),
    Kept = Table.SelectColumns(TestID, {"TestID", "EntryNumber", "PostingDate", "TotalAmount", "ApprovedByEmployeeID"}),
    Renamed = Table.RenameColumns(Kept, {{"EntryNumber", "DocumentNumber"}, {"PostingDate", "EventDate"},
        {"TotalAmount", "Amount"}, {"ApprovedByEmployeeID", "EmployeeID"}})
in
    Renamed
"""),
    expr("PurchaseOrderFlags", f"""
let
    {src("T33_PurchaseOrder")},
    Kept = Table.SelectColumns(Data, {{"PurchaseOrderID", "PONumber", "OrderDate", "OrderTotal", "CreatedByEmployeeID",
        "ApprovedByEmployeeID"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"PurchaseOrderID", Int64.Type}}, {{"PONumber", type text}},
        {{"OrderDate", type date}}, {{"OrderTotal", type number}}, {{"CreatedByEmployeeID", Int64.Type}},
        {{"ApprovedByEmployeeID", Int64.Type}}}}),
    Merged = Table.NestedJoin(Typed, {{"ApprovedByEmployeeID"}}, Employee, {{"EmployeeID"}}, "Approver", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "Approver", {{"MaxApprovalAmount", "TerminationDate"}},
        {{"ApproverLimit", "ApproverTermination"}}),
    SelfApproved = Table.AddColumn(Expanded, "SelfApproved", each if [CreatedByEmployeeID] = [ApprovedByEmployeeID] then 1 else 0, Int64.Type),
    AboveLimit = Table.AddColumn(SelfApproved, "AboveLimit", each if [OrderTotal] > [ApproverLimit] then 1 else 0, Int64.Type),
    AfterTermination = Table.AddColumn(AboveLimit, "AfterTermination",
        each if [ApproverTermination] <> null and [OrderDate] > [ApproverTermination] then 1 else 0, Int64.Type)
in
    AfterTermination
"""),
    expr("PO Exceptions", """
let
    Source = PurchaseOrderFlags,
    Unpivoted = Table.Unpivot(Source, {"SelfApproved", "AboveLimit", "AfterTermination"}, "Attribute", "Value"),
    Flagged = Table.SelectRows(Unpivoted, each [Value] = 1),
    TestID = Table.AddColumn(Flagged, "TestID", each "PO " & [Attribute], type text),
    Kept = Table.SelectColumns(TestID, {"TestID", "PONumber", "OrderDate", "OrderTotal", "ApprovedByEmployeeID"}),
    Renamed = Table.RenameColumns(Kept, {{"PONumber", "DocumentNumber"}, {"OrderDate", "EventDate"},
        {"OrderTotal", "Amount"}, {"ApprovedByEmployeeID", "EmployeeID"}})
in
    Renamed
"""),
    expr("PayrollPayment", f"""
let
    {src("T71_PayrollPayment")},
    Kept = Table.SelectColumns(Data, {{"PayrollRegisterID", "PaymentDate"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"PayrollRegisterID", Int64.Type}}, {{"PaymentDate", type date}}}})
in
    Typed
"""),
    expr("PayrollPeriod", f"""
let
    {src("T59_PayrollPeriod")},
    Kept = Table.SelectColumns(Data, {{"PayrollPeriodID", "PeriodEndDate", "PayDate"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"PayrollPeriodID", Int64.Type}}, {{"PeriodEndDate", type date}}, {{"PayDate", type date}}}})
in
    Typed
"""),
    expr("PayrollFlags", f"""
let
    {src("T69_PayrollRegister")},
    Kept = Table.SelectColumns(Data, {{"PayrollRegisterID", "PayrollPeriodID", "EmployeeID", "NetPay",
        "ApprovedByEmployeeID", "ApprovedDate"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"PayrollRegisterID", Int64.Type}}, {{"PayrollPeriodID", Int64.Type}},
        {{"EmployeeID", Int64.Type}}, {{"NetPay", type number}}, {{"ApprovedByEmployeeID", Int64.Type}}, {{"ApprovedDate", type date}}}}),
    Paid = Table.NestedJoin(Typed, {{"PayrollRegisterID"}}, PayrollPayment, {{"PayrollRegisterID"}}, "Payment", JoinKind.LeftOuter),
    PaidExpanded = Table.ExpandTableColumn(Paid, "Payment", {{"PaymentDate"}}),
    Period = Table.NestedJoin(PaidExpanded, {{"PayrollPeriodID"}}, PayrollPeriod, {{"PayrollPeriodID"}}, "Period", JoinKind.LeftOuter),
    PeriodExpanded = Table.ExpandTableColumn(Period, "Period", {{"PeriodEndDate", "PayDate"}}),
    Payee = Table.NestedJoin(PeriodExpanded, {{"EmployeeID"}}, Employee, {{"EmployeeID"}}, "Payee", JoinKind.LeftOuter),
    PayeeExpanded = Table.ExpandTableColumn(Payee, "Payee", {{"TerminationDate"}}),
    PaidBefore = Table.AddColumn(PayeeExpanded, "PaidBeforeApproval",
        each if [PaymentDate] <> null and [PaymentDate] < [ApprovedDate] then 1 else 0, Int64.Type),
    AfterTermination = Table.AddColumn(PaidBefore, "AfterTermination",
        each if [TerminationDate] <> null and [PeriodEndDate] > [TerminationDate] then 1 else 0, Int64.Type),
    SelfApproved = Table.AddColumn(AfterTermination, "SelfApproved", each if [EmployeeID] = [ApprovedByEmployeeID] then 1 else 0, Int64.Type),
    Removed = Table.RemoveColumns(SelfApproved, {{"PayrollPeriodID"}})
in
    Removed
"""),
    expr("Payroll Exceptions", """
let
    Source = PayrollFlags,
    Unpivoted = Table.Unpivot(Source, {"PaidBeforeApproval", "AfterTermination", "SelfApproved"}, "Attribute", "Value"),
    Flagged = Table.SelectRows(Unpivoted, each [Value] = 1),
    TestID = Table.AddColumn(Flagged, "TestID", each "PR " & [Attribute], type text),
    Number = Table.AddColumn(TestID, "DocumentNumber", each "Register " & Text.From([PayrollRegisterID]), type text),
    Kept = Table.SelectColumns(Number, {"TestID", "DocumentNumber", "PayDate", "NetPay", "ApprovedByEmployeeID"}),
    Renamed = Table.RenameColumns(Kept, {{"PayDate", "EventDate"}, {"NetPay", "Amount"}, {"ApprovedByEmployeeID", "EmployeeID"}})
in
    Renamed
"""),
])


def rel(frm, to, active=True):
    lines = [f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, f"{NAME}/{frm}/{to}")}", f"{T}fromColumn: {frm}", f"{T}toColumn: {to}"]
    if not active:
        lines.append(f"{T}isActive: false")
    return "\n".join(lines) + "\n"


relationships = "\n".join([
    rel("JournalEntry.PostingDate", "Date.Date"),
    rel("JournalEntry.ApprovedByEmployeeID", "Employee.EmployeeID"),
    rel("JournalLines.SourceDocumentID", "JournalEntry.JournalEntryID"),
    rel("PurchaseOrder.OrderDate", "Date.Date"),
    rel("PayrollRegister.PayDate", "Date.Date"),
    rel("Exceptions.EventDate", "Date.Date"),
    rel("Exceptions.TestID", "Tests.TestID"),
    rel("Exceptions.EmployeeID", "Employee.EmployeeID"),
])

order = ["Employee", "Account", "JournalEntryFlags", "JournalEntry", "JournalLines", "JE Exceptions",
         "PurchaseOrderFlags", "PurchaseOrder", "PO Exceptions", "PayrollPayment", "PayrollPeriod",
         "PayrollFlags", "PayrollRegister", "Payroll Exceptions", "Dispositions", "Exceptions", "Tests", "CostCenterReview"]
model = f"""model Model
	culture: en-US
	defaultPowerBIDataSourceVersion: powerBI_V3
	sourceQueryCulture: en-US
	dataAccessOptions
		legacyRedirects
		returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 0

annotation PBI_QueryOrder = {json.dumps(order)}
"""


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
write(sm / "definition" / "database.tmdl", f"database {NAME}\n\tcompatibilityLevel: 1601\n")
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
