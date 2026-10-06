"""Write the Part IV case reference model, CC4, as a Power BI project (PBIP): the ledger with the closes flagged,
Account with the cash-bridge Step and Activity columns, Date, materials Receipts (with the requisition channel),
Issues (with the work-order pair key), Requisitions, ShortfallPairs (grouped and merged with the issues), Item
(with the policy target), open AR and AP at 2026-12-31, and the debt schedule."""
import json
import uuid
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, XLSX as _XLSX  # noqa: E402

OUT = REFERENCE_MODELS / "case4_ref"
NAME = "CC4"
XLSX = str(_XLSX)
T = "\t"


def src(table):
    return (f'Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),\n'
            f'    Data = Source{{[Item="{table}",Kind="Table"]}}[Data]')


def m_block(body, level):
    pad = T * (level + 1)
    return "\n".join(pad + line if line else "" for line in body.strip("\n").split("\n"))


def column(name, dtype, source=None, fmt=None, summarize="none"):
    q = f"'{name}'" if any(ch in name for ch in " .=:'") else name
    lines = [f"{T}column {q}", f"{T*2}dataType: {dtype}"]
    if fmt:
        lines.append(f"{T*2}formatString: {fmt}")
    lines += [f"{T*2}summarizeBy: {summarize}", f"{T*2}sourceColumn: {source or name}"]
    return "\n".join(lines) + "\n"


def table(name, columns, partition_m=None, partition_dax=None, props=()):
    q = f"'{name}'" if " " in name else name
    out = [f"table {q}"] + [f"{T}{p}" for p in props] + [""] + list(columns)
    if partition_m:
        out.append(f"{T}partition {q} = m\n{T*2}mode: import\n{T*2}source =\n{m_block(partition_m, 2)}\n")
    if partition_dax:
        body = "\n".join(T * 3 + line for line in partition_dax.strip("\n").split("\n"))
        out.append(f"{T}partition {q} = calculated\n{T*2}mode: import\n{T*2}source =\n{body}\n")
    return "\n".join(out) + "\n"


def expr(name, body):
    lines = body.strip("\n").split("\n")
    q = f"'{name}'" if " " in name else name
    return f"expression {q} =\n" + "\n".join(T * 2 + line for line in lines) + f"\n{T}annotation PBI_ResultType = Table\n"


def rel(frm, to):
    return f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, f"{NAME}/{frm}/{to}")}\n{T}fromColumn: {frm}\n{T}toColumn: {to}\n"


MONEY = "#,0.00"
tables = {}

tables["GLEntry"] = table("GLEntry", [
    column("GLEntryID", "int64"), column("PostingDate", "dateTime", fmt="Short Date"), column("AccountID", "int64"),
    column("Debit", "double", fmt=MONEY, summarize="sum"), column("Credit", "double", fmt=MONEY, summarize="sum"),
    column("VoucherNumber", "string"), column("SourceDocumentType", "string"), column("SourceDocumentID", "int64"),
    column("EntryType", "string"), column("IsYearEndClose", "boolean"),
], partition_m=f"""
let
    {src("T3_GLEntry")},
    Kept = Table.SelectColumns(Data, {{"GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber",
        "SourceDocumentType", "SourceDocumentID"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"GLEntryID", Int64.Type}}, {{"PostingDate", type date}}, {{"AccountID", Int64.Type}},
        {{"Debit", type number}}, {{"Credit", type number}}, {{"VoucherNumber", type text}}, {{"SourceDocumentType", type text}},
        {{"SourceDocumentID", Int64.Type}}}}),
    Merged = Table.NestedJoin(Typed, {{"VoucherNumber"}}, JournalEntry, {{"EntryNumber"}}, "JE", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "JE", {{"EntryType"}}),
    Flag = Table.AddColumn(Expanded, "IsYearEndClose", each [EntryType] <> null and Text.StartsWith([EntryType], "Year-End Close"), type logical)
in
    Flag
""")

STEP = """if [AccountNumber] = 1010 then "Cash"
        else if [AccountType] = "Revenue" or [AccountType] = "Expense" then "Net income"
        else if [AccountSubType] = "Contra Fixed Asset" then "Depreciation"
        else if [AccountNumber] = 1020 or [AccountNumber] = 1030 then "Receivables"
        else if [AccountNumber] = 1040 or [AccountNumber] = 1045 or [AccountNumber] = 1046 then "Inventories"
        else if [AccountSubType] = "Current Asset" or [AccountSubType] = "Contra Current Asset" then "Other current assets"
        else if [AccountNumber] = 2010 or [AccountNumber] = 2020 then "Payables"
        else if [AccountNumber] = 2050 then "Sales tax"
        else if [AccountSubType] = "Current Liability" then "Other current liabilities"
        else if [AccountSubType] = "Fixed Asset" or [AccountSubType] = "Noncurrent Asset" then "Fixed assets"
        else "Debt and equity\""""
tables["Account"] = table("Account", [
    column("AccountID", "int64"), column("AccountNumber", "int64"), column("AccountName", "string"),
    column("AccountType", "string"), column("AccountSubType", "string"), column("Step", "string"), column("Activity", "string"),
], partition_m=f"""
let
    {src("T1_Account")},
    Kept = Table.SelectColumns(Data, {{"AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"AccountID", Int64.Type}}, {{"AccountNumber", Int64.Type}}, {{"AccountName", type text}},
        {{"AccountType", type text}}, {{"AccountSubType", type text}}}}),
    Step = Table.AddColumn(Typed, "Step", each {STEP}, type text),
    Activity = Table.AddColumn(Step, "Activity", each if [Step] = "Cash" then "Cash" else if [Step] = "Fixed assets" then "Investing"
        else if [Step] = "Debt and equity" then "Financing" else "Operating", type text)
in
    Activity
""")

tables["Date"] = table("Date", [
    column("Date", "dateTime", source="[Date]", fmt="Short Date"), column("Year", "int64", source="[Year]"),
    column("YearQuarter", "string", source="[YearQuarter]"), column("YearMonth", "string", source="[YearMonth]"),
], partition_dax="""
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2027, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "YearQuarter", YEAR ( [Date] ) & "-Q" & QUARTER ( [Date] ),
    "YearMonth", FORMAT ( [Date], "yyyy-mm" )
)
""", props=("dataCategory: Time",))

tables["Item"] = table("Item", [
    column("ItemID", "int64"), column("ItemCode", "string"), column("ItemName", "string"), column("ItemGroup", "string"),
    column("TargetDaysSupply", "int64"),
], partition_m=f"""
let
    {src("T44_Item")},
    Kept = Table.SelectColumns(Data, {{"ItemID", "ItemCode", "ItemName", "ItemGroup"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"ItemID", Int64.Type}}, {{"ItemCode", type text}}, {{"ItemName", type text}}, {{"ItemGroup", type text}}}}),
    Merged = Table.NestedJoin(Typed, {{"ItemID"}}, Targets, {{"ItemID"}}, "P", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "P", {{"TargetDaysSupply"}})
in
    Expanded
""")

tables["Requisitions"] = table("Requisitions", [
    column("RequisitionID", "int64"), column("RequestDate", "dateTime", fmt="Short Date"), column("ItemID", "int64"),
    column("Quantity", "double", summarize="sum"), column("EstimatedUnitCost", "double"), column("Justification", "string"),
    column("Status", "string"), column("Channel", "string"), column("ApproverTitle", "string"),
], partition_m="""
let
    Source = RequisitionsStaged
in
    Source
""")

tables["Receipts"] = table("Receipts", [
    column("GoodsReceiptLineID", "int64"), column("ItemID", "int64"), column("QuantityReceived", "double", summarize="sum"),
    column("ExtendedStandardCost", "double", fmt=MONEY, summarize="sum"), column("ReceiptDate", "dateTime", fmt="Short Date"),
    column("RequisitionID", "int64"), column("Channel", "string"),
], partition_m=f"""
let
    {src("T36_GoodsReceiptLine")},
    Kept = Table.SelectColumns(Data, {{"GoodsReceiptLineID", "GoodsReceiptID", "POLineID", "ItemID", "QuantityReceived", "ExtendedStandardCost"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"GoodsReceiptLineID", Int64.Type}}, {{"GoodsReceiptID", Int64.Type}}, {{"POLineID", Int64.Type}},
        {{"ItemID", Int64.Type}}, {{"QuantityReceived", type number}}, {{"ExtendedStandardCost", type number}}}}),
    M1 = Table.NestedJoin(Typed, {{"GoodsReceiptID"}}, ReceiptHeaders, {{"GoodsReceiptID"}}, "H", JoinKind.LeftOuter),
    E1 = Table.ExpandTableColumn(M1, "H", {{"ReceiptDate"}}),
    M2 = Table.NestedJoin(E1, {{"POLineID"}}, POLines, {{"POLineID"}}, "P", JoinKind.LeftOuter),
    E2 = Table.ExpandTableColumn(M2, "P", {{"RequisitionID"}}),
    M3 = Table.NestedJoin(E2, {{"RequisitionID"}}, RequisitionsStaged, {{"RequisitionID"}}, "R", JoinKind.LeftOuter),
    E3 = Table.ExpandTableColumn(M3, "R", {{"Channel"}}),
    Out = Table.RemoveColumns(E3, {{"GoodsReceiptID", "POLineID"}})
in
    Out
""")

tables["Issues"] = table("Issues", [
    column("MaterialIssueLineID", "int64"), column("ItemID", "int64"), column("QuantityIssued", "double", summarize="sum"),
    column("ExtendedStandardCost", "double", fmt=MONEY, summarize="sum"), column("IssueDate", "dateTime", fmt="Short Date"),
    column("WorkOrderID", "int64"), column("PairKey", "string"),
], partition_m="""
let
    Source = IssuesStaged
in
    Source
""")

tables["ShortfallPairs"] = table("ShortfallPairs", [
    column("Justification", "string"), column("Requisitions", "int64", summarize="sum"),
    column("RequisitionedQty", "double", summarize="sum"), column("EstimatedValue", "double", fmt=MONEY, summarize="sum"),
    column("FirstRequest", "dateTime", fmt="Short Date"), column("LastRequest", "dateTime", fmt="Short Date"),
    column("IssuedQty", "double", summarize="sum"), column("IssuedCost", "double", fmt=MONEY, summarize="sum"),
], partition_m="""
let
    Source = Table.SelectRows(RequisitionsStaged, each [Channel] = "Work-order shortfall"),
    Value = Table.AddColumn(Source, "EstimatedValue", each [Quantity] * [EstimatedUnitCost], type number),
    Grouped = Table.Group(Value, {"Justification"}, {{"Requisitions", each Table.RowCount(_), Int64.Type},
        {"RequisitionedQty", each List.Sum([Quantity]), type number}, {"EstimatedValue", each List.Sum([EstimatedValue]), type number},
        {"FirstRequest", each List.Min([RequestDate]), type date}, {"LastRequest", each List.Max([RequestDate]), type date}}),
    IssuedByPair = Table.Group(IssuesStaged, {"PairKey"}, {{"IssuedQty", each List.Sum([QuantityIssued]), type number},
        {"IssuedCost", each List.Sum([ExtendedStandardCost]), type number}}),
    Merged = Table.NestedJoin(Grouped, {"Justification"}, IssuedByPair, {"PairKey"}, "I", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Merged, "I", {"IssuedQty", "IssuedCost"})
in
    Expanded
""")

tables["ARInvoices"] = table("ARInvoices", [
    column("SalesInvoiceID", "int64"), column("InvoiceDate", "dateTime", fmt="Short Date"), column("DueDate", "dateTime", fmt="Short Date"),
    column("GrandTotal", "double", fmt=MONEY, summarize="sum"), column("OpenBalance", "double", fmt=MONEY, summarize="sum"),
], partition_m=f"""
let
    {src("T16_SalesInvoice")},
    Kept = Table.SelectColumns(Data, {{"SalesInvoiceID", "InvoiceDate", "DueDate", "GrandTotal"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"SalesInvoiceID", Int64.Type}}, {{"InvoiceDate", type date}}, {{"DueDate", type date}}, {{"GrandTotal", type number}}}}),
    Dated = Table.SelectRows(Typed, each [InvoiceDate] <= #date(2026, 12, 31)),
    M1 = Table.NestedJoin(Dated, {{"SalesInvoiceID"}}, ARApplied, {{"SalesInvoiceID"}}, "A", JoinKind.LeftOuter),
    E1 = Table.ExpandTableColumn(M1, "A", {{"AppliedTotal"}}),
    M2 = Table.NestedJoin(E1, {{"SalesInvoiceID"}}, ARCredited, {{"OriginalSalesInvoiceID"}}, "C", JoinKind.LeftOuter),
    E2 = Table.ExpandTableColumn(M2, "C", {{"CreditedTotal"}}),
    Open = Table.AddColumn(E2, "OpenBalance", each Number.Round([GrandTotal] - (if [AppliedTotal] = null then 0 else [AppliedTotal])
        - (if [CreditedTotal] = null then 0 else [CreditedTotal]), 2), type number),
    Kept2 = Table.SelectRows(Table.RemoveColumns(Open, {{"AppliedTotal", "CreditedTotal"}}), each [OpenBalance] > 0)
in
    Kept2
""")

tables["APInvoices"] = table("APInvoices", [
    column("PurchaseInvoiceID", "int64"), column("ReceivedDate", "dateTime", fmt="Short Date"), column("DueDate", "dateTime", fmt="Short Date"),
    column("GrandTotal", "double", fmt=MONEY, summarize="sum"), column("OpenBalance", "double", fmt=MONEY, summarize="sum"),
], partition_m=f"""
let
    {src("T37_PurchaseInvoice")},
    Kept = Table.SelectColumns(Data, {{"PurchaseInvoiceID", "ReceivedDate", "DueDate", "GrandTotal"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"PurchaseInvoiceID", Int64.Type}}, {{"ReceivedDate", type date}}, {{"DueDate", type date}}, {{"GrandTotal", type number}}}}),
    Dated = Table.SelectRows(Typed, each [ReceivedDate] <= #date(2026, 12, 31)),
    M1 = Table.NestedJoin(Dated, {{"PurchaseInvoiceID"}}, APPaid, {{"PurchaseInvoiceID"}}, "P", JoinKind.LeftOuter),
    E1 = Table.ExpandTableColumn(M1, "P", {{"PaidTotal"}}),
    Open = Table.AddColumn(E1, "OpenBalance", each Number.Round([GrandTotal] - (if [PaidTotal] = null then 0 else [PaidTotal]), 2), type number),
    Kept2 = Table.SelectRows(Table.RemoveColumns(Open, {{"PaidTotal"}}), each [OpenBalance] > 0)
in
    Kept2
""")

tables["DebtSchedule"] = table("DebtSchedule", [
    column("DebtScheduleLineID", "int64"), column("DebtAgreementID", "int64"), column("PaymentDate", "dateTime", fmt="Short Date"),
    column("PrincipalAmount", "double", fmt=MONEY, summarize="sum"), column("InterestAmount", "double", fmt=MONEY, summarize="sum"),
    column("EndingPrincipal", "double", fmt=MONEY), column("Status", "string"),
], partition_m=f"""
let
    {src("T43_DebtScheduleLine")},
    Kept = Table.SelectColumns(Data, {{"DebtScheduleLineID", "DebtAgreementID", "PaymentDate", "PrincipalAmount", "InterestAmount", "EndingPrincipal", "Status"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"DebtScheduleLineID", Int64.Type}}, {{"DebtAgreementID", Int64.Type}}, {{"PaymentDate", type date}},
        {{"PrincipalAmount", type number}}, {{"InterestAmount", type number}}, {{"EndingPrincipal", type number}}, {{"Status", type text}}}})
in
    Typed
""")

CHANNEL = """if Text.StartsWith([Justification], "WO-COMPONENT-SHORTFALL") then "Work-order shortfall"
            else if Text.StartsWith([Justification], "Supply plan") then "Supply plan" else "Other\""""
expressions = "\n".join([
    expr("JournalEntry", f"""
let
    {src("T2_JournalEntry")},
    Kept = Table.SelectColumns(Data, {{"EntryNumber", "EntryType"}})
in
    Kept
"""),
    expr("Targets", f"""
let
    {src("T79_InventoryPolicy")},
    Typed = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"ItemID", "TargetDaysSupply"}}), {{{{"ItemID", Int64.Type}}, {{"TargetDaysSupply", Int64.Type}}}}),
    Grouped = Table.Group(Typed, {{"ItemID"}}, {{{{"TargetDaysSupply", each List.Max([TargetDaysSupply]), Int64.Type}}}})
in
    Grouped
"""),
    expr("Approvers", f"""
let
    {src("T74_Employee")},
    Kept = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"EmployeeID", "JobTitle"}}), {{{{"EmployeeID", Int64.Type}}}})
in
    Kept
"""),
    expr("RequisitionsStaged", f"""
let
    {src("T32_PurchaseRequisition")},
    Kept = Table.SelectColumns(Data, {{"RequisitionID", "RequestDate", "ItemID", "Quantity", "EstimatedUnitCost", "Justification",
        "ApprovedByEmployeeID", "Status"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"RequisitionID", Int64.Type}}, {{"RequestDate", type date}}, {{"ItemID", Int64.Type}},
        {{"Quantity", type number}}, {{"EstimatedUnitCost", type number}}, {{"Justification", type text}}, {{"ApprovedByEmployeeID", Int64.Type}}}}),
    Channel = Table.AddColumn(Typed, "Channel", each {CHANNEL}, type text),
    M1 = Table.NestedJoin(Channel, {{"ApprovedByEmployeeID"}}, Approvers, {{"EmployeeID"}}, "E", JoinKind.LeftOuter),
    E1 = Table.ExpandTableColumn(M1, "E", {{"JobTitle"}}, {{"ApproverTitle"}}),
    Out = Table.RemoveColumns(E1, {{"ApprovedByEmployeeID"}})
in
    Out
"""),
    expr("ReceiptHeaders", f"""
let
    {src("T35_GoodsReceipt")},
    Kept = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"GoodsReceiptID", "ReceiptDate"}}), {{{{"GoodsReceiptID", Int64.Type}}, {{"ReceiptDate", type date}}}})
in
    Kept
"""),
    expr("POLines", f"""
let
    {src("T34_PurchaseOrderLine")},
    Kept = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"POLineID", "RequisitionID"}}), {{{{"POLineID", Int64.Type}}, {{"RequisitionID", Int64.Type}}}})
in
    Kept
"""),
    expr("IssuesStaged", f"""
let
    {src("T55_MaterialIssueLine")},
    Kept = Table.SelectColumns(Data, {{"MaterialIssueLineID", "MaterialIssueID", "ItemID", "QuantityIssued", "ExtendedStandardCost"}}),
    Typed = Table.TransformColumnTypes(Kept, {{{{"MaterialIssueLineID", Int64.Type}}, {{"MaterialIssueID", Int64.Type}}, {{"ItemID", Int64.Type}},
        {{"QuantityIssued", type number}}, {{"ExtendedStandardCost", type number}}}}),
    M1 = Table.NestedJoin(Typed, {{"MaterialIssueID"}}, IssueHeaders, {{"MaterialIssueID"}}, "H", JoinKind.LeftOuter),
    E1 = Table.ExpandTableColumn(M1, "H", {{"IssueDate", "WorkOrderID"}}),
    Key = Table.AddColumn(E1, "PairKey", each "WO-COMPONENT-SHORTFALL | WO=" & Text.From([WorkOrderID]) & " | ITEM=" & Text.From([ItemID]), type text),
    Out = Table.RemoveColumns(Key, {{"MaterialIssueID"}})
in
    Out
"""),
    expr("IssueHeaders", f"""
let
    {src("T54_MaterialIssue")},
    Kept = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"MaterialIssueID", "IssueDate", "WorkOrderID"}}),
        {{{{"MaterialIssueID", Int64.Type}}, {{"IssueDate", type date}}, {{"WorkOrderID", Int64.Type}}}})
in
    Kept
"""),
    expr("ARApplied", f"""
let
    {src("T20_CashReceiptApplication")},
    Typed = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"SalesInvoiceID", "ApplicationDate", "AppliedAmount"}}),
        {{{{"SalesInvoiceID", Int64.Type}}, {{"ApplicationDate", type date}}, {{"AppliedAmount", type number}}}}),
    Dated = Table.SelectRows(Typed, each [ApplicationDate] <= #date(2026, 12, 31)),
    Grouped = Table.Group(Dated, {{"SalesInvoiceID"}}, {{{{"AppliedTotal", each List.Sum([AppliedAmount]), type number}}}})
in
    Grouped
"""),
    expr("ARCredited", f"""
let
    {src("T23_CreditMemo")},
    Typed = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"OriginalSalesInvoiceID", "CreditMemoDate", "GrandTotal"}}),
        {{{{"OriginalSalesInvoiceID", Int64.Type}}, {{"CreditMemoDate", type date}}, {{"GrandTotal", type number}}}}),
    Dated = Table.SelectRows(Typed, each [CreditMemoDate] <= #date(2026, 12, 31)),
    Grouped = Table.Group(Dated, {{"OriginalSalesInvoiceID"}}, {{{{"CreditedTotal", each List.Sum([GrandTotal]), type number}}}})
in
    Grouped
"""),
    expr("APPaid", f"""
let
    {src("T39_DisbursementPayment")},
    Typed = Table.TransformColumnTypes(Table.SelectColumns(Data, {{"PurchaseInvoiceID", "PaymentDate", "Amount"}}),
        {{{{"PurchaseInvoiceID", Int64.Type}}, {{"PaymentDate", type date}}, {{"Amount", type number}}}}),
    Dated = Table.SelectRows(Typed, each [PaymentDate] <= #date(2026, 12, 31)),
    Grouped = Table.Group(Dated, {{"PurchaseInvoiceID"}}, {{{{"PaidTotal", each List.Sum([Amount]), type number}}}})
in
    Grouped
"""),
])

relationships = "\n".join([
    rel("GLEntry.AccountID", "Account.AccountID"), rel("GLEntry.PostingDate", "Date.Date"),
    rel("Receipts.ItemID", "Item.ItemID"), rel("Receipts.ReceiptDate", "Date.Date"),
    rel("Issues.ItemID", "Item.ItemID"), rel("Issues.IssueDate", "Date.Date"),
    rel("Requisitions.ItemID", "Item.ItemID"),
])
order = ["JournalEntry", "GLEntry", "Account", "Targets", "Item", "Approvers", "RequisitionsStaged", "Requisitions",
         "ReceiptHeaders", "POLines", "Receipts", "IssueHeaders", "IssuesStaged", "Issues", "ShortfallPairs",
         "ARApplied", "ARCredited", "ARInvoices", "APPaid", "APInvoices", "DebtSchedule"]
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


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


sm = OUT / f"{NAME}.SemanticModel"
rp = OUT / f"{NAME}.Report"
write(OUT / f"{NAME}.pbip", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
write(sm / "definition.pbism", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2", "settings": {}}, indent=2))
write(sm / "definition" / "database.tmdl", f"database {NAME}\n\tcompatibilityLevel: 1601\n")
write(sm / "definition" / "model.tmdl", model)
write(sm / "definition" / "expressions.tmdl", expressions)
write(sm / "definition" / "relationships.tmdl", relationships)
for n, text in tables.items():
    write(sm / "definition" / "tables" / f"{n}.tmdl", text)
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
    "name": "validation", "displayName": "Validation", "displayOption": "FitToPage", "height": 720, "width": 1280}, indent=2))
print("wrote", OUT)
