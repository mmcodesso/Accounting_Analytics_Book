"""Charles River Cash Case.pbip: the instructor solution to the Part IV comprehensive case, "Finding the Cash Behind
the Profit" (cases/part-4-case.qmd), built in a new project as the case tells the reader to.

Each function answers one requirement as a strong submission would: the queries the case names, with the Power Query
Editor's step names; the ledger star of Tutorial 14.3 with the Date table of Tutorial 14.1; every measure in the Key
Measures table with a description that states its definition; the pages; and a "Model answer" text box for the
written parts, built from computed values. The DAX the chapters print (the Date table, GL Amount, P&L Amount, Net
Income, Exercise 14.1's Balance, and Tutorial 14.3's IsYearEndClose formula) is read from their .qmd files. The checks
compare the model with every value of the case's instructor notes, computed read-only from CharlesRiver.sqlite by
facts/notes/case4.py (or by SQL here).

Two tables go beyond the queries the case lists, because the notes' findings need them: OrderLines (the purchase order
lines, which Receipts reaches its requisitions through, loaded so that the order lines still open at the year-end can
be measured), and Components, an Enter data table that lets the tooltip page list each balance beside its flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pbibuild.audit_monitoring import drillthrough
from pbibuild.ex15 import ParamVisual
from pbibuild.ex16 import group
from pbibuild.model import DATE_FORMAT, MEASURES_TABLE, Column, Measure, Model, Query, Table, query_table
from pbibuild.pbir import Page, Report, Visual, col, lit, meas, textbox
from pbibuild.project import Project
from pbibuild.reports import (CH14, MONEY, card, claim, code_after, dax_blocks, definitions, entered, hide, icon_rules,
                              keep, money, one, rows, slicer)

from db import Data  # noqa: E402  (facts/ is on sys.path through pbibuild.reports)
from notes import case4  # noqa: E402

FILE = "Charles River Cash Case"
KM = MEASURES_TABLE
M = lambda n: meas(KM, n)                 # noqa: E731
DAYS, RATIO, PCT, COUNT, UNITS, DAY = "0.0", "0.00", "0.0%", "#,0", "#,0.0", "yyyy-mm-dd"
MATERIALS = ("Raw Materials", "Packaging")
SHORT, PLAN, OTHER = "Work-order shortfall", "Supply plan", "Other"
CHANNEL = {"Shortfall": SHORT, "Supply plan": PLAN, "Other": OTHER}      # case4.py's channel names -> the model's
STEPS = [("net_income", "Net income"), ("depreciation", "Depreciation"), ("receivables", "Receivables"),
         ("inventories", "Inventories"), ("other_ca", "Other current assets"), ("payables", "Payables"),
         ("sales_tax", "Sales tax"), ("other_cl", "Other current liabilities"), ("fixed", "Fixed assets"),
         ("debt_equity", "Debt and equity")]
WC = ["DSO", "DIO", "DPO", "Cash Conversion Cycle", "Materials Days", "Finished Goods Days"]
GUARDED = ["DSO", "DSO without Opening", "DIO", "Materials Days", "Finished Goods Days", "DPO", "DPO without Opening",
           "Cash Conversion Cycle", "Cycle without Opening"]
ROLL = ["1020", "1040", "1045", "2010", "2020", "2050"]
CH14_EX = CH14 / "_exercises.qmd"


@dataclass
class Build:
    xlsx: Path
    exp: object
    year: int
    project: Project = None
    tests: list = field(default_factory=list)

    def __post_init__(self):
        self.project = Project(FILE, Model(FILE), Report())
        self.d = Data()
        self.ctx = {k: getattr(case4, k)(self.d, claim) for k in ("r1", "r2", "r3", "r4", "r5", "r6")}

    @property
    def model(self) -> Model:
        return self.project.model

    @property
    def report(self) -> Report:
        return self.project.report

    def check(self, section: str, label: str, expected, dax: str, tolerance: float = 0.005) -> None:
        self.project.check(section, label, expected, dax, tolerance)

    def measure(self, folder: str, name: str, dax: str, fmt: str | None, description: str) -> None:
        mt = self.model.tables[KM]
        assert all(m.name != name for m in mt.measures), f"measure {name} exists already"
        mt.measures.append(Measure(name, dax.strip("\n"), fmt, description, display_folder=folder))

    def add_test(self, comment: str, query: str) -> None:
        """A query typed at the end of the Tests tab, under its comment line (the tab kept before Checks)."""
        self.tests.append(f"// {comment}\n{query.strip()}")
        self.project.queries["Tests"] = "\n\n".join(self.tests) + "\n"
        if "Checks" in self.project.queries:
            self.project.queries["Checks"] = self.project.queries.pop("Checks")


# --- small helpers ---------------------------------------------------------------------------------------------------

def mdate(day: str) -> str:
    y, m, d = day.split("-")
    return f"#date({int(y)}, {int(m)}, {int(d)})"


def ddate(day: str) -> str:
    y, m, d = day.split("-")
    return f"DATE ( {int(y)}, {int(m)}, {int(d)} )"


def signed(x: float) -> str:
    return ("+" if x > 0 else "") + money(x)


def pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


def answer(name: str, x, y, w, h, lines: list, size: int = 10, title: str = "Model answer") -> Visual:
    return textbox(name, x, y, w, h, [(title, True)] + lines, size=size)


def blank(dax: str) -> str:
    return f"IF ( ISBLANK ( {dax} ), \"blank\", \"not blank\" )"


def fmt_date(dax: str) -> str:
    return f"FORMAT ( {dax}, \"yyyy-mm-dd\" )"


def rows_expanded(levels: list[dict]) -> dict:
    """A matrix's Rows with every level expanded (Expand all down one level)."""
    from pbibuild.pbir import _ref
    return {"expansionStates": [{"roles": ["Rows"], "levels": [
        {"queryRefs": [_ref(levels[0])[1]], "isCollapsed": False, "identityKeys": [levels[0]], "isPinned": True},
        {"queryRefs": [_ref(levels[1])[1]], "isCollapsed": True, "isPinned": True}]}]}


def text_measure(path: Path, kind: str, name: str) -> str:
    return dict(d for body in dax_blocks(path, kind) for d in definitions(body))[name]


def entered_table(name: str, columns: list[tuple[str, str]], data: list[list], fmts: dict | None = None) -> Table:
    """An Enter data table with the column types set after typing (text, whole number, decimal number)."""
    cols = [Column(c, t, fmt=(fmts or {}).get(c), summarize="sum" if t == "double" else "none") for c, t in columns]
    return Table(name, cols, entered=[[str(v) for v in r] for r in data])


# --- Requirement 1: the queries, the model, Validation, About, Data Through --------------------------------------

STEP_RULES = [("1010", None, "Cash"), (None, "type:Revenue|Expense", "Net income"),
              (None, "Contra Fixed Asset", "Depreciation"), ("1020|1030", None, "Receivables"),
              ("1040|1045|1046", None, "Inventories"), (None, "Current Asset|Contra Current Asset", "Other current assets"),
              ("2010|2020", None, "Payables"), ("2050", None, "Sales tax"), (None, "Current Liability", "Other current liabilities"),
              (None, "Fixed Asset|Noncurrent Asset", "Fixed assets")]


def step_formula() -> str:
    """The if-then-else chain of Tutorial 16.1, on account numbers first where the case separates them."""
    parts = []
    for numbers, subtypes, step in STEP_RULES:
        if numbers:
            test = " or ".join(f"[AccountNumber] = {n}" for n in numbers.split("|"))
        elif subtypes.startswith("type:"):
            test = " or ".join(f'[AccountType] = "{t}"' for t in subtypes[5:].split("|"))
        else:
            test = " or ".join(f'[AccountSubType] = "{s}"' for s in subtypes.split("|"))
        parts.append(f'if {test} then "{step}"')
    return " else ".join(parts) + ' else "Debt and equity"'


def r1(b: Build) -> None:
    d, m, x, c1 = b.d, b.model, b.xlsx, b.ctx["r1"]
    end = mdate(c1["thru"])
    # the ledger star of Tutorial 14.3: GLEntry with all its rows and the columns the model needs, the closes flagged
    journal = Query.navigator("JournalEntry", x, 2, "JournalEntry").select(["EntryNumber", "EntryType"])
    gl = (Query.navigator("GLEntry", x, 3, "GLEntry")
          .select(["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType"])
          .types({"PostingDate": "type date"})
          .merge(journal, "VoucherNumber", "EntryNumber", ["EntryType"]))
    gl.custom("IsYearEndClose", code_after(CH14 / "_tutorial-03.qmd", "name the column `IsYearEndClose`"), "type logical")
    account = Query.navigator("Account", x, 1, "Account").select(
        ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"])
    account.custom("Step", step_formula(), "type text")
    account.custom("Activity", 'if [Step] = "Cash" then "Cash" else if [Step] = "Fixed assets" then "Investing" '
                               'else if [Step] = "Debt and equity" then "Financing" else "Operating"', "type text")
    account.custom("StepOrder", " else ".join(f'if [Step] = "{s}" then {i + 1}' for i, (_, s) in enumerate(STEPS))
                   + " else 0", "Int64.Type")
    m.stage(journal)
    ledger = m.add(query_table(gl, formats={"Debit": MONEY, "Credit": MONEY}))
    hide(ledger, "GLEntryID", "AccountID")
    acc = m.add(query_table(account, summarize={"AccountNumber": "none", "StepOrder": "none"},
                            sort_by={"Step": "StepOrder"}))
    hide(acc, "AccountID", "StepOrder")
    # the Date table of Tutorial 14.1, marked as a date table
    ((name, expr),) = definitions(dax_blocks(CH14 / "_tutorial-01.qmd", "table")[0])
    assert name == "Date"
    m.add(Table("Date", [
        Column("Date", "dateTime", "[Date]", DATE_FORMAT, extra=("isKey",)),
        Column("Year", "int64", "[Year]"), Column("Quarter", "string", "[Quarter]"),
        Column("YearQuarter", "string", "[YearQuarter]"), Column("YearMonth", "string", "[YearMonth]"),
        Column("MonthNumber", "int64", "[MonthNumber]"),
        Column("MonthName", "string", "[MonthName]", sort_by="MonthNumber")], dax=expr, props=("dataCategory: Time",)))
    # Requisitions, with the channel from the justification, the work order it names, and the two employees' titles
    employee = Query.navigator("Employee", x, 74, "Employee").select(["EmployeeID", "JobTitle"])
    work = (Query.navigator("WorkOrder", x, 51, "WorkOrder").select(["WorkOrderID", "WorkOrderNumber", "DueDate", "CompletedDate"])
            .types({"DueDate": "type date", "CompletedDate": "type date"}))
    req = (Query.navigator("Requisitions", x, 32, "PurchaseRequisition")
           .select(["RequisitionID", "RequisitionNumber", "RequestDate", "RequestedByEmployeeID", "ItemID", "Quantity",
                    "EstimatedUnitCost", "Justification", "ApprovedByEmployeeID", "Status", "SupplyPlanRecommendationID"])
           .types({"RequestDate": "type date"}))
    req.custom("Channel", f'if Text.StartsWith([Justification], "WO-COMPONENT-SHORTFALL") then "{SHORT}" '
                          f'else if Text.StartsWith([Justification], "Supply plan") then "{PLAN}" else "{OTHER}"', "type text")
    req.custom("EstimatedValue", "[Quantity] * [EstimatedUnitCost]", "type number")
    req.custom("WorkOrderID", f'if [Channel] = "{SHORT}" then Number.From(Text.BetweenDelimiters([Justification], '
                              '"WO=", " |")) else null', "Int64.Type")
    req.merge(work, "WorkOrderID", "WorkOrderID", ["WorkOrderNumber", "DueDate", "CompletedDate"])
    req.merge(employee, "RequestedByEmployeeID", "EmployeeID", ["JobTitle"]).rename({"JobTitle": "RequesterTitle"})
    req.merge(employee, "ApprovedByEmployeeID", "EmployeeID", ["JobTitle"]).rename({"JobTitle": "ApproverTitle"})
    # Item, with its policy target grouped by item first (one policy row per item and warehouse)
    policy = (Query.navigator("InventoryPolicy", x, 79, "InventoryPolicy")
              .select(["ItemID", "TargetDaysSupply", "EffectiveEndDate"]).types({"EffectiveEndDate": "type date"}))
    group(policy, ["ItemID"], [("TargetDaysSupply", "List.Max([TargetDaysSupply])", "Int64.Type"),
                               ("PolicyEnd", "List.Max([EffectiveEndDate])", "type date")])
    item = (Query.navigator("Item", x, 44, "Item").select(["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "SupplyMode"])
            .merge(policy, "ItemID", "ItemID", ["TargetDaysSupply", "PolicyEnd"]))
    # Receipts: receipt lines with the receipt date, the order line's requisition, and the requisition's channel
    receipt = (Query.navigator("GoodsReceipt", x, 35, "GoodsReceipt").select(["GoodsReceiptID", "ReceiptDate"])
               .types({"ReceiptDate": "type date"}))
    order = (Query.navigator("PurchaseOrder", x, 33, "PurchaseOrder").select(["PurchaseOrderID", "OrderDate", "RequisitionID"])
             .types({"OrderDate": "type date"}).rename({"RequisitionID": "HeaderRequisitionID"}))
    lines = (Query.navigator("OrderLines", x, 34, "PurchaseOrderLine")
             .select(["POLineID", "PurchaseOrderID", "RequisitionID", "ItemID", "Quantity", "UnitCost"])
             .merge(order, "PurchaseOrderID", "PurchaseOrderID", ["OrderDate", "HeaderRequisitionID"])
             .merge(item, "ItemID", "ItemID", ["ItemGroup"]))
    receipts = (Query.navigator("Receipts", x, 36, "GoodsReceiptLine")
                .select(["GoodsReceiptLineID", "GoodsReceiptID", "POLineID", "ItemID", "QuantityReceived", "ExtendedStandardCost"])
                .merge(receipt, "GoodsReceiptID", "GoodsReceiptID", ["ReceiptDate"])
                .merge(lines, "POLineID", "POLineID", ["RequisitionID"])
                .merge(req, "RequisitionID", "RequisitionID", ["Channel"]))
    # Issues: issue lines with the issue date, the work order, and the justification text the work order and item make
    issue = (Query.navigator("MaterialIssue", x, 54, "MaterialIssue").select(["MaterialIssueID", "IssueDate", "WorkOrderID"])
             .types({"IssueDate": "type date"}))
    issues = (Query.navigator("Issues", x, 55, "MaterialIssueLine")
              .select(["MaterialIssueLineID", "MaterialIssueID", "ItemID", "QuantityIssued", "ExtendedStandardCost"])
              .merge(issue, "MaterialIssueID", "MaterialIssueID", ["IssueDate", "WorkOrderID"]))
    issues.custom("PairKey", '"WO-COMPONENT-SHORTFALL | WO=" & Text.From([WorkOrderID]) & " | ITEM=" & Text.From([ItemID])',
                  "type text")
    # Requirement 4's groups: shortfall requisitions by justification, with what was issued to the same work order and item
    issued = group(Query.reference("IssuedByPair", issues), ["PairKey"], [
        ("IssuedQty", "List.Sum([QuantityIssued])", "type number"), ("IssuedCost", "List.Sum([ExtendedStandardCost])", "type number")])
    pairs = Query.reference("ShortfallPairs", req).filter(f'([Channel] = "{SHORT}")')
    group(pairs, ["Justification", "WorkOrderNumber", "ItemID"], [
        ("RequisitionCount", "Table.RowCount(_)", "Int64.Type"), ("RequisitionedQty", "List.Sum([Quantity])", "type number"),
        ("EstimatedValue", "List.Sum([EstimatedValue])", "type number"), ("FirstRequest", "List.Min([RequestDate])", "type date"),
        ("LastRequest", "List.Max([RequestDate])", "type date"), ("DueDate", "List.Min([DueDate])", "type date"),
        ("CompletedDate", "List.Min([CompletedDate])", "type date")])
    pairs.merge(issued, "Justification", "PairKey", ["IssuedQty", "IssuedCost"])
    # receivables and payables at the end of the year, as Exercise 16.1 and Exercise 8.2 rebuilt them
    apps = group(Query.navigator("ARApplications", x, 20, "CashReceiptApplication")
                 .select(["SalesInvoiceID", "ApplicationDate", "AppliedAmount"]).types({"ApplicationDate": "type date"})
                 .filter(f"[ApplicationDate] <= {end}"),
                 ["SalesInvoiceID"], [("Applied", "List.Sum([AppliedAmount])", "type nullable number")])
    credits = group(Query.navigator("ARCredits", x, 23, "CreditMemo")
                    .select(["OriginalSalesInvoiceID", "CreditMemoDate", "GrandTotal"]).types({"CreditMemoDate": "type date"})
                    .filter(f"[CreditMemoDate] <= {end}"),
                    ["OriginalSalesInvoiceID"], [("Credited", "List.Sum([GrandTotal])", "type nullable number")])
    ar = (Query.navigator("ARInvoices", x, 16, "SalesInvoice")
          .select(["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "CustomerID", "TaxAmount", "GrandTotal"])
          .types({"InvoiceDate": "type date", "DueDate": "type date"})
          .merge(apps, "SalesInvoiceID", "SalesInvoiceID", ["Applied"])
          .merge(credits, "SalesInvoiceID", "OriginalSalesInvoiceID", ["Credited"])
          .custom("OpenBalance", "Number.Round([GrandTotal] - (if [Applied] = null then 0 else [Applied]) "
                                 "- (if [Credited] = null then 0 else [Credited]), 2)", "type number")
          .filter(f"[InvoiceDate] <= {end}"))
    paid = group(Query.navigator("APPayments", x, 39, "DisbursementPayment")
                 .select(["PurchaseInvoiceID", "PaymentDate", "Amount"]).types({"PaymentDate": "type date"})
                 .filter(f"[PaymentDate] <= {end}"),
                 ["PurchaseInvoiceID"], [("Paid", "List.Sum([Amount])", "type nullable number")])
    notes_ids = ", ".join(str(c["id"]) for c in b.ctx["r5"]["capital"])
    ap = (Query.navigator("APInvoices", x, 37, "PurchaseInvoice")
          .select(["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "ReceivedDate", "DueDate", "SupplierID", "GrandTotal"])
          .types({"InvoiceDate": "type date", "ReceivedDate": "type date", "DueDate": "type date"})
          .merge(paid, "PurchaseInvoiceID", "PurchaseInvoiceID", ["Paid"])
          .custom("OpenBalance", "Number.Round([GrandTotal] - (if [Paid] = null then 0 else [Paid]), 2)", "type number")
          .filter(f"[ReceivedDate] <= {end} and [OpenBalance] > 0"))
    ap.custom("DaysPastDue", f"Duration.Days({end} - [DueDate])", "Int64.Type")
    ap.custom("Bucket", 'if [DaysPastDue] <= 0 then "Current" else if [DaysPastDue] <= 30 then "1-30 days" '
                        'else if [DaysPastDue] <= 60 then "31-60 days" else if [DaysPastDue] <= 90 then "61-90 days" '
                        'else "Over 90 days"', "type text")
    ap.custom("BucketOrder", 'if [DaysPastDue] <= 0 then 1 else if [DaysPastDue] <= 30 then 2 else if [DaysPastDue] <= 60 '
                             'then 3 else if [DaysPastDue] <= 90 then 4 else 5', "Int64.Type")
    ap.custom("MovedToNotes", f"List.Contains({{{notes_ids}}}, [PurchaseInvoiceID])", "type logical")
    debt = (Query.navigator("DebtSchedule", x, 43, "DebtScheduleLine")
            .select(["DebtScheduleLineID", "DebtAgreementID", "PaymentDate", "PrincipalAmount", "InterestAmount",
                     "EndingPrincipal", "Status"]).types({"PaymentDate": "type date"}))
    # the queries that only feed others, then the loaded tables
    for q in (employee, work, policy, receipt, order, issue, issued, apps, credits, paid):
        m.stage(q)
    keys = lambda *names: {n: "none" for n in names}        # noqa: E731
    t = m.add(query_table(req, formats={"EstimatedUnitCost": MONEY, "EstimatedValue": MONEY},
                          summarize=keys("RequisitionID", "RequestedByEmployeeID", "ItemID", "ApprovedByEmployeeID",
                                         "SupplyPlanRecommendationID", "WorkOrderID")))
    hide(t, "RequisitionID", "RequestedByEmployeeID", "ItemID", "ApprovedByEmployeeID", "SupplyPlanRecommendationID", "WorkOrderID")
    t = m.add(query_table(item, summarize=keys("ItemID", "TargetDaysSupply")))
    hide(t, "ItemID")
    t = m.add(query_table(lines, formats={"UnitCost": MONEY}, summarize=keys("POLineID", "PurchaseOrderID", "RequisitionID",
                                                                             "ItemID", "HeaderRequisitionID")))
    hide(t, "POLineID", "PurchaseOrderID", "RequisitionID", "ItemID", "HeaderRequisitionID")
    t = m.add(query_table(receipts, formats={"ExtendedStandardCost": MONEY},
                          summarize=keys("GoodsReceiptLineID", "GoodsReceiptID", "POLineID", "ItemID", "RequisitionID")))
    hide(t, "GoodsReceiptLineID", "GoodsReceiptID", "POLineID", "ItemID", "RequisitionID")
    t = m.add(query_table(issues, formats={"ExtendedStandardCost": MONEY},
                          summarize=keys("MaterialIssueLineID", "MaterialIssueID", "ItemID", "WorkOrderID")))
    hide(t, "MaterialIssueLineID", "MaterialIssueID", "ItemID", "WorkOrderID")
    t = m.add(query_table(pairs, formats={"EstimatedValue": MONEY, "IssuedCost": MONEY, "RequisitionedQty": UNITS,
                                          "IssuedQty": UNITS}, summarize=keys("ItemID", "RequisitionCount")))
    hide(t, "ItemID")
    t = m.add(query_table(ar, formats={"TaxAmount": MONEY, "GrandTotal": MONEY, "Applied": MONEY, "Credited": MONEY,
                                       "OpenBalance": MONEY}, summarize=keys("SalesInvoiceID", "CustomerID")))
    hide(t, "SalesInvoiceID", "CustomerID")
    t = m.add(query_table(ap, formats={"GrandTotal": MONEY, "Paid": MONEY, "OpenBalance": MONEY},
                          summarize=keys("PurchaseInvoiceID", "SupplierID", "DaysPastDue", "BucketOrder"),
                          sort_by={"Bucket": "BucketOrder"}))
    hide(t, "SupplierID", "BucketOrder")
    t = m.add(query_table(debt, formats={"PrincipalAmount": MONEY, "InterestAmount": MONEY, "EndingPrincipal": MONEY},
                          summarize=keys("DebtScheduleLineID", "DebtAgreementID", "EndingPrincipal")))
    hide(t, "DebtScheduleLineID")
    for many, one_ in [("GLEntry.AccountID", "Account.AccountID"), ("GLEntry.PostingDate", "Date.Date"),
                       ("Requisitions.ItemID", "Item.ItemID"), ("Requisitions.RequestDate", "Date.Date"),
                       ("Receipts.ItemID", "Item.ItemID"), ("Receipts.ReceiptDate", "Date.Date"),
                       ("Receipts.POLineID", "OrderLines.POLineID"),
                       ("Issues.ItemID", "Item.ItemID"), ("Issues.IssueDate", "Date.Date"),
                       ("ShortfallPairs.ItemID", "Item.ItemID"), ("ARInvoices.InvoiceDate", "Date.Date"),
                       ("APInvoices.ReceivedDate", "Date.Date"), ("DebtSchedule.PaymentDate", "Date.Date")]:
        m.relate(many, one_)
    # the Key Measures table
    mt = m.add(entered(KM, [("Column1", "string")], []))
    m.query_order.append(KM)
    hide(mt, "Column1")

    t14 = CH14 / "_tutorial-03.qmd"
    L = "Ledger"
    b.measure(L, "GL Amount", text_measure(t14, "measure", "GL Amount"), MONEY,
              "Debits less credits, without the year-end closing entries (Tutorial 14.3).")
    b.measure(L, "P&L Amount", text_measure(t14, "measure", "P&L Amount"), MONEY,
              "GL Amount with its sign reversed: revenue positive, expenses negative.")
    b.measure(L, "Net Income", text_measure(t14, "measure", "Net Income"), MONEY,
              "P&L Amount over the revenue and expense accounts: the net income of the period, without the closes.")
    b.measure(L, "Balance", text_measure(CH14_EX, "measure", "Balance"), MONEY,
              "Exercise 14.1's balance at the last date in the filter context: every posting up to that date, debits "
              "less credits, with a closing entry left out only when it is dated on that day.")
    b.measure(L, "Total Assets", 'CALCULATE ( [Balance], Account[AccountType] = "Asset" )', MONEY,
              "Balance of the Asset accounts at the last date in the filter context.")
    V = "Validation"
    mat = '{ "' + '", "'.join(MATERIALS) + '" }'
    b.measure(V, "Materials Received", f"CALCULATE (\n    SUM ( Receipts[ExtendedStandardCost] ),\n"
              f"    KEEPFILTERS ( 'Item'[ItemGroup] IN {mat} )\n)", MONEY,
              "Receipt lines of Raw Materials and Packaging items at standard cost, by receipt date.")
    b.measure(V, "Materials Issued", f"CALCULATE (\n    SUM ( Issues[ExtendedStandardCost] ),\n"
              f"    KEEPFILTERS ( 'Item'[ItemGroup] IN {mat} )\n)", MONEY,
              "Material issue lines to production at standard cost, by issue date.")
    b.measure(V, "Receipts to 1045", 'CALCULATE (\n    SUM ( GLEntry[Debit] ),\n    Account[AccountNumber] = 1045,\n'
              '    GLEntry[SourceDocumentType] = "GoodsReceipt"\n)', MONEY,
              "The GoodsReceipt debits to account 1045 Inventory - Materials and Packaging.")
    b.measure(V, "Issues from 1045", 'CALCULATE (\n    SUM ( GLEntry[Credit] ),\n    Account[AccountNumber] = 1045,\n'
              '    GLEntry[SourceDocumentType] = "MaterialIssue"\n)', MONEY,
              "The MaterialIssue credits to account 1045 Inventory - Materials and Packaging.")
    b.measure(V, "Receipt Lines", "COUNTROWS ( Receipts )", COUNT, "The number of goods receipt lines.")
    b.measure(V, "Receipts without a Requisition", "COUNTROWS ( FILTER ( Receipts, ISBLANK ( Receipts[RequisitionID] ) ) ) + 0",
              COUNT, "Receipt lines whose order line names no requisition (the link test of Requirement 1).")
    b.measure(V, "Issue Lines", "COUNTROWS ( Issues )", COUNT, "The number of material issue lines.")
    b.measure(V, "Issues without a Work Order", "COUNTROWS ( FILTER ( Issues, ISBLANK ( Issues[WorkOrderID] ) ) ) + 0",
              COUNT, "Issue lines whose issue names no work order (the link test of Requirement 1).")
    b.measure(V, "Requisition Count", "COUNTROWS ( Requisitions )", COUNT, "The number of purchase requisitions.")
    DT = "Data currency"
    sources = ["SalesInvoice", "CashReceiptApplication", "PurchaseInvoice", "DisbursementPayment", "GoodsReceipt",
               "MaterialIssue", "Shipment"]
    claim(sources == list(case4.DATA_SOURCES), "Data Through takes the documents the note names")
    lasts = ",\n".join(f'            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "{s}" )'
                       for s in sources)
    b.measure(DT, "Data Through", f"CALCULATE (\n    MINX (\n        {{\n{lasts}\n        }},\n        [Value]\n    ),\n"
              "    REMOVEFILTERS ()\n)", DAY,
              "The earliest of the last posting dates of the documents behind the working-capital accounts (sales "
              "invoices, cash applications, supplier invoices and payments, goods receipts, material issues, "
              "shipments): the date through which every one of them is complete. Payroll is left out: its last two "
              "pay periods are open, so it ends in mid-December.")
    b.measure(DT, "Last Ledger Posting", "CALCULATE ( MAX ( GLEntry[PostingDate] ), REMOVEFILTERS () )", DAY,
              "The last posting date in the ledger, whatever the filters: not the date through which the report runs.")
    b.measure(DT, "Rows after Data Through", "VAR ThroughDate = [Data Through]\nRETURN\n    CALCULATE ( COUNTROWS ( GLEntry ), "
              "REMOVEFILTERS (), GLEntry[PostingDate] > ThroughDate ) + 0", COUNT,
              "Ledger rows posted after Data Through.")
    b.measure(DT, "Postings after Data Through", "VAR ThroughDate = [Data Through]\nRETURN\n    CALCULATE ( SUM ( GLEntry[Debit] ), "
              "REMOVEFILTERS (), GLEntry[PostingDate] > ThroughDate )", MONEY,
              "The debits posted after Data Through (each supplier payment debits 2010 and credits 1010).")

    # About page
    y, P, F = d.C, d.P, d.F
    about = b.report.add(Page("about", "About"))
    about.add(card("dataThrough", 880, 20, 380, 110, [M("Data Through"), M("Last Ledger Posting")], title="Data currency"))
    about.add(textbox("aboutText", 20, 20, 840, 680, [
        (FILE, True),
        f"Purpose: to show the audit committee where the cash went in fiscal {y}: the bridge from net income to the "
        "change in cash, the balances that absorbed it and how fast they turn, the materials build behind them, and "
        "the reconciliations that test those balances. Prepared by the staff accountant for the controller, June "
        f"{d.N}.",
        "Sources: CharlesRiver.xlsx through Power Query: the ledger (GLEntry with Account and JournalEntry, the closes "
        "flagged), receipts with their requisitions and channels, material issues with their work orders, the "
        "requisitions, the items with their policy targets, the open sales and supplier invoices at the year-end, and "
        "the debt schedule.",
        f"Period: fiscal {F} to {y}. Data Through: {c1['thru']}, the earliest of the last posting dates of the sales "
        "invoices, cash applications, supplier invoices and payments, goods receipts, material issues, and shipments.",
        f"Why not the last posting date: the ledger runs to {c1['last']}, but only because {c1['n_pay']} supplier "
        f"payments of {y} invoices ({money(c1['pay_amount'])}, {c1['rows_after']} rows) were posted after the year. "
        f"A balance taken on {c1['last']} shows cash of {money(c1['cash_last'])} and payables of "
        f"{money(c1['ap_last'])}, and a bridge for {d.N} shows a fall in cash of {money(c1['fall'])} that only "
        "means the data stop.",
        f"Payroll is left out of Data Through: payroll summaries and payments end on {c1['payroll_end']} (the last "
        f"{c1['n_open']} pay periods are open), so including them would date the report {c1['payroll_end']} and blank "
        f"the last quarter of {y}.",
        "Definitions: every measure is in the Key Measures table with its definition as its description. Balances "
        "follow Exercise 14.1 (closes left out only on the as-of date); flows leave the closes out; the "
        "working-capital measures divide a quarter-end balance by the ledger flow of the twelve months that end on "
        "that date, times 365, and are blank before a full twelve months and after Data Through.",
        "Checks: the Validation page reproduces the control totals, the Tests tab in DAX query view holds the tests, "
        "and the Data Through card states the date through which the data run."], size=11))
    about.expect = [FILE, "Data Through", c1["thru"], c1["last"]]
    b.report.active = "about"

    # Validation page
    years = d.years
    page = b.report.add(Page("validation", "Validation"))
    yr = col("Date", "Year")
    page.add(Visual("controlTotals", "tableEx", 20, 20, 1240, 150, {"Values": [
        yr, M("Net Income"), M("Total Assets"), M("Materials Received"), M("Receipts to 1045"), M("Materials Issued"),
        M("Issues from 1045")]}, title="Control totals by fiscal year", filters=[keep("ctYears", yr, years)]))
    page.add(card("linkCards", 20, 190, 1240, 110, [M("Receipt Lines"), M("Receipts without a Requisition"),
                                                    M("Issue Lines"), M("Issues without a Work Order"),
                                                    M("Requisition Count")], title="Links tested"))
    r4c = b.ctx["r4"]
    page.add(answer("profileAnswer", 20, 320, 1240, 380, [
        f"Profiles on the entire data set (Column profiling based on entire data set): Requisitions {c1['requisitions']:,} "
        f"rows, Justification never empty; {c1['shortfall']:,} work-order shortfall requisitions (WO-COMPONENT-SHORTFALL "
        f"| WO=<id> | ITEM=<id>, the ITEM always equal to ItemID), {c1['supply']:,} supply-plan requisitions (all but "
        f"{c1['no_rec']} with a SupplyPlanRecommendationID), and {c1['n_other']} other requests (capital items). "
        f"{c1['no_approver']} requisitions have no approver (Exercise 2.5); {c1['unordered']} are Approved and on no "
        f"order line, all work-order shortfall requisitions of December {y}.",
        f"Links: all {c1['receipt_lines']:,} receipt lines find their order line, and every one of the "
        f"{c1['po_lines']:,} order lines names exactly one requisition; the purchase order header's RequisitionID is "
        f"blank on {c1['blank_header']:,} orders, which is why Receipts reaches the requisition through the line. "
        f"Issues: {c1['issue_lines']:,} lines on {c1['issues_with_lines']:,} issues, every issue with its work order; "
        f"{c1['empty_issues']} issue headers have no lines (Chapter 12), an isolated exception not pursued.",
        "Control totals: net income by year equals Tutorial 14.3; total assets at each year-end equal Exercise 14.1; "
        "the materials received (receipt lines of Raw Materials and Packaging items) and issued equal the GoodsReceipt "
        "debits and MaterialIssue credits to 1045 in every year, so the new tables tie to the ledger.",
        f"The closes: GLEntry keeps all {c1['gl_rows']:,} rows; the {c1['n_closes']} year-end closes "
        f"({'; '.join(c1['closes'])}) post {c1['close_rows']} rows, flagged by IsYearEndClose and left out of every "
        f"flow. Materials stock at the opening ({money(r4c['opening_materials'])}) came in through the opening entry, "
        "with no item detail."], size=10))
    page.expect = ["Control totals by fiscal year", money(c1["ni"][-1]), money(c1["assets"][-1]), money(c1["received"][-1]),
                   money(c1["issued"][-1]), "Model answer"]

    # Tests 1 and 2
    yl = ", ".join(map(str, years))
    b.add_test("Test 1: control totals by fiscal year: net income, total assets, and the materials against account 1045",
               "EVALUATE\nSUMMARIZECOLUMNS (\n    'Date'[Year],\n    TREATAS ( { " + yl + " }, 'Date'[Year] ),\n"
               "    \"Net Income\", ROUND ( [Net Income], 2 ),\n    \"Total Assets\", ROUND ( [Total Assets], 2 ),\n"
               "    \"Materials Received\", ROUND ( [Materials Received], 2 ),\n"
               "    \"Receipts to 1045\", ROUND ( [Receipts to 1045], 2 ),\n"
               "    \"Materials Issued\", ROUND ( [Materials Issued], 2 ),\n"
               "    \"Issues from 1045\", ROUND ( [Issues from 1045], 2 )\n)\nORDER BY 'Date'[Year]")
    b.add_test("Test 2: the date through which the data run, and what the ledger holds after it",
               "EVALUATE\nROW (\n    \"Data Through\", [Data Through],\n    \"Last Ledger Posting\", [Last Ledger Posting],\n"
               "    \"Rows after Data Through\", [Rows after Data Through],\n"
               "    \"Postings after Data Through\", ROUND ( [Postings after Data Through], 2 )\n)")

    # checks
    s = "Requirement 1"
    b.check(s, "GLEntry rows (all of them)", c1["gl_rows"], "COUNTROWS ( GLEntry )", 0)
    b.check(s, "postings flagged IsYearEndClose", c1["close_rows"], "COUNTROWS ( FILTER ( GLEntry, GLEntry[IsYearEndClose] ) )", 0)
    b.check(s, "the closing entries", ", ".join(sorted(d.closes)),
            "CONCATENATEX ( CALCULATETABLE ( VALUES ( GLEntry[VoucherNumber] ), GLEntry[IsYearEndClose] ), "
            "GLEntry[VoucherNumber], \", \", GLEntry[VoucherNumber], ASC )")
    b.check(s, "Requisitions rows", c1["requisitions"], "COUNTROWS ( Requisitions )", 0)
    by_channel = dict(rows(f"SELECT {case4.CHANNEL}, COUNT(*) FROM PurchaseRequisition r GROUP BY 1"))
    for k, v in by_channel.items():
        b.check(s, f"requisitions, channel {CHANNEL[k]}", v,
                f"CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Channel] = \"{CHANNEL[k]}\" )", 0)
    claim(by_channel["Shortfall"] == c1["shortfall"] and by_channel["Supply plan"] == c1["supply"], "the channel counts agree")
    b.check(s, "supply-plan requisitions without a SupplyPlanRecommendationID", c1["no_rec"],
            f"CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Channel] = \"{PLAN}\", "
            "ISBLANK ( Requisitions[SupplyPlanRecommendationID] ) )", 0)
    b.check(s, "shortfall justifications whose ITEM differs from ItemID", 0,
            f"COUNTROWS ( FILTER ( Requisitions, Requisitions[Channel] = \"{SHORT}\" && VALUE ( MID ( "
            "Requisitions[Justification], SEARCH ( \"ITEM=\", Requisitions[Justification] ) + 5, 10 ) ) <> "
            "Requisitions[ItemID] ) ) + 0", 0)
    b.check(s, "shortfall requisitions whose work order was found", c1["shortfall"],
            f"CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Channel] = \"{SHORT}\", "
            "NOT ISBLANK ( Requisitions[WorkOrderNumber] ) )", 0)
    b.check(s, "requisitions with no approver", c1["no_approver"],
            "COUNTROWS ( FILTER ( Requisitions, ISBLANK ( Requisitions[ApprovedByEmployeeID] ) ) )", 0)
    b.check(s, "requisitions on no order line", c1["unordered"],
            "COUNTROWS ( EXCEPT ( VALUES ( Requisitions[RequisitionID] ), VALUES ( OrderLines[RequisitionID] ) ) )", 0)
    b.check(s, "... all Approved, work-order shortfall, December", c1["unordered"],
            f"CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Status] = \"Approved\", Requisitions[Channel] = \"{SHORT}\", "
            f"'Date'[YearMonth] = \"{y}-12\" )", 0)
    b.check(s, "Receipts rows", c1["receipt_lines"], "COUNTROWS ( Receipts )", 0)
    b.check(s, "receipt lines without their order line", 0,
            "COUNTROWS ( FILTER ( Receipts, ISBLANK ( RELATED ( OrderLines[POLineID] ) ) ) ) + 0", 0)
    b.check(s, "receipt lines without a requisition", 0, "[Receipts without a Requisition]", 0)
    b.check(s, "receipt lines without a channel", 0, "COUNTROWS ( FILTER ( Receipts, ISBLANK ( Receipts[Channel] ) ) ) + 0", 0)
    b.check(s, "receipt lines without a receipt date", 0,
            "COUNTROWS ( FILTER ( Receipts, ISBLANK ( Receipts[ReceiptDate] ) ) ) + 0", 0)
    b.check(s, "order lines", c1["po_lines"], "COUNTROWS ( OrderLines )", 0)
    b.check(s, "order lines without a requisition", 0,
            "COUNTROWS ( FILTER ( OrderLines, ISBLANK ( OrderLines[RequisitionID] ) ) ) + 0", 0)
    b.check(s, "order lines whose requisition is missing", 0,
            "COUNTROWS ( EXCEPT ( VALUES ( OrderLines[RequisitionID] ), VALUES ( Requisitions[RequisitionID] ) ) ) + 0", 0)
    b.check(s, "requisitions on the order lines (one line each)", one("SELECT COUNT(DISTINCT RequisitionID) FROM PurchaseOrderLine"),
            "DISTINCTCOUNT ( OrderLines[RequisitionID] )", 0)
    b.check(s, "orders whose header RequisitionID is blank", c1["blank_header"],
            "CALCULATE ( DISTINCTCOUNT ( OrderLines[PurchaseOrderID] ), ISBLANK ( OrderLines[HeaderRequisitionID] ) )", 0)
    b.check(s, "Issues rows", c1["issue_lines"], "COUNTROWS ( Issues )", 0)
    b.check(s, "issues with lines", c1["issues_with_lines"], "DISTINCTCOUNT ( Issues[MaterialIssueID] )", 0)
    b.check(s, "issue lines without a work order", 0, "[Issues without a Work Order]", 0)
    b.check(s, "issue lines without an issue date", 0, "COUNTROWS ( FILTER ( Issues, ISBLANK ( Issues[IssueDate] ) ) ) + 0", 0)
    b.check(s, "items (one row each after the grouped policy merge)", one("SELECT COUNT(*) FROM Item"), "COUNTROWS ( 'Item' )", 0)
    for i, yy in enumerate(years):
        cy = f"'Date'[Year] = {yy}"
        b.check(s, f"{yy} Net Income", c1["ni"][i], f"CALCULATE ( [Net Income], {cy} )", 0.01)
        b.check(s, f"{yy} total assets at the year-end", c1["assets"][i], f"CALCULATE ( [Total Assets], {cy} )", 0.01)
        b.check(s, f"{yy} materials received", c1["received"][i], f"CALCULATE ( [Materials Received], {cy} )", 0.01)
        b.check(s, f"{yy} GoodsReceipt debits to 1045", c1["received"][i], f"CALCULATE ( [Receipts to 1045], {cy} )", 0.01)
        b.check(s, f"{yy} materials issued", c1["issued"][i], f"CALCULATE ( [Materials Issued], {cy} )", 0.01)
        b.check(s, f"{yy} MaterialIssue credits to 1045", c1["issued"][i], f"CALCULATE ( [Issues from 1045], {cy} )", 0.01)
    b.check(s, "Data Through", c1["thru"], fmt_date("[Data Through]"))
    b.check(s, "Data Through under a year filter (unchanged)", c1["thru"], fmt_date(f"CALCULATE ( [Data Through], 'Date'[Year] = {F} )"))
    b.check(s, "the ledger's last posting", c1["last"], fmt_date("[Last Ledger Posting]"))
    b.check(s, "rows after Data Through", c1["rows_after"], "[Rows after Data Through]", 0)
    b.check(s, "supplier payments after Data Through", c1["n_pay"],
            f"CALCULATE ( DISTINCTCOUNT ( GLEntry[VoucherNumber] ), GLEntry[PostingDate] > {ddate(c1['thru'])}, "
            "GLEntry[SourceDocumentType] = \"DisbursementPayment\" )", 0)
    b.check(s, "their amount (debits after Data Through)", c1["pay_amount"], "[Postings after Data Through]", 0.01)
    b.check(s, "rows after Data Through that are not supplier payments to 2010 and 1010", 0,
            f"[Rows after Data Through] - CALCULATE ( COUNTROWS ( GLEntry ), GLEntry[PostingDate] > {ddate(c1['thru'])}, "
            "GLEntry[SourceDocumentType] = \"DisbursementPayment\", Account[AccountNumber] IN { 1010, 2010 } )", 0)
    last = f"'Date'[Date] = {ddate(c1['last'])}"
    b.check(s, f"cash on {c1['last']}", c1["cash_last"],
            f"CALCULATE ( [Balance], {last}, Account[AccountNumber] = 1010 )", 0.01)
    b.check(s, f"payables on {c1['last']}", c1["ap_last"],
            f"- CALCULATE ( [Balance], {last}, Account[AccountNumber] = 2010 )", 0.01)
    b.check(s, f"the change in cash of {d.N} (the data stop)", -c1["fall"],
            f"CALCULATE ( CALCULATE ( [GL Amount], Account[AccountNumber] = 1010 ), 'Date'[Year] = {d.N} )", 0.01)
    b.check(s, "last payroll summary or payment", c1["payroll_end"],
            fmt_date("CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] IN { \"PayrollSummary\", "
                     "\"PayrollPayment\" } )"))
    b.check(s, "last payroll liability remittance", c1["remit_end"],
            fmt_date("CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = \"PayrollLiabilityRemittance\" )"))


# --- Requirement 2: the balance sheet, the bridge, the restated sections ----------------------------------------

def r2(b: Build) -> None:
    d, c, c1 = b.d, b.ctx["r2"], b.ctx["r1"]
    y, P, F = d.C, d.P, d.F
    years = d.years
    BS, BR = "Balance sheet", "Cash bridge"
    b.measure(BS, "Statement Balance", "IF (\n    HASONEVALUE ( Account[AccountType] ),\n"
              "    IF ( SELECTEDVALUE ( Account[AccountType] ) = \"Asset\", [Balance], - [Balance] )\n)", MONEY,
              "Balance signed by account type, as a balance sheet shows it: assets positive; liabilities, equity, and "
              "the year's revenue and expenses (before closing) with the sign reversed. Blank on a total of types.")
    for name, dax, f, desc in [
        ("Current Assets", 'CALCULATE ( [Balance], Account[AccountSubType] IN { "Current Asset", "Contra Current Asset" } )',
         MONEY, "Balance of the Current Asset and Contra Current Asset accounts."),
        ("Current Liabilities", '- CALCULATE ( [Balance], Account[AccountSubType] = "Current Liability" )', MONEY,
         "Balance of the Current Liability accounts, as a positive amount."),
        ("Working Capital", "[Current Assets] - [Current Liabilities]", MONEY, "Current assets less current liabilities."),
        ("Current Ratio", "DIVIDE ( [Current Assets], [Current Liabilities] )", RATIO,
         "Current assets divided by current liabilities."),
        ("Quick Ratio", "DIVIDE ( CALCULATE ( [Balance], Account[AccountNumber] IN { 1010, 1020 } ), [Current Liabilities] )",
         RATIO, "Cash (1010) and receivables (1020) divided by current liabilities: the current ratio without the inventories."),
        ("Cash", "CALCULATE ( [Balance], Account[AccountNumber] = 1010 )", MONEY, "Balance of 1010 Cash and Cash Equivalents."),
        ("Inventories", "CALCULATE ( [Balance], Account[AccountNumber] IN { 1040, 1045, 1046 } )", MONEY,
         "Balance of the inventory accounts: finished goods (1040), materials and packaging (1045), work in process (1046)."),
        ("Inventories Share", "DIVIDE ( [Inventories], [Current Assets] )", PCT, "Inventories as a share of current assets."),
        ("Cash Net of Sales Tax", "CALCULATE ( [Balance], Account[AccountNumber] IN { 1010, 2050 } )", MONEY,
         "Cash less the sales tax collected and not remitted (the credit balance of 2050)."),
        ("Sales Tax Payable", "- CALCULATE ( [Balance], Account[AccountNumber] = 2050 )", MONEY,
         "Balance of 2050 Sales Tax Payable, as a positive amount."),
        ("Notes Payable", "- CALCULATE ( [Balance], Account[AccountNumber] = 2110 )", MONEY,
         "Balance of 2110 Notes Payable, as a positive amount."),
        ("Scheduled Principal Outstanding", "VAR AsOf = MAX ( 'Date'[Date] )\nRETURN\n    CALCULATE (\n"
         "        SUM ( DebtSchedule[PrincipalAmount] ),\n        REMOVEFILTERS ( 'Date' ),\n        DebtSchedule[PaymentDate] > AsOf\n    )",
         MONEY, "The principal of the scheduled payments after the last date in the filter context: the notes "
                "outstanding by the debt schedule, filtered on PaymentDate because the schedule runs past the Date table."),
        ("Principal Due within a Year", "VAR AsOf = MAX ( 'Date'[Date] )\nRETURN\n    CALCULATE (\n"
         "        SUM ( DebtSchedule[PrincipalAmount] ),\n        REMOVEFILTERS ( 'Date' ),\n        DebtSchedule[PaymentDate] > AsOf,\n"
         "        DebtSchedule[PaymentDate] <= EDATE ( AsOf, 12 )\n    )", MONEY,
         "The principal the debt schedule pays in the twelve months after the last date in the filter context: the "
         "current portion of the notes.")]:
        b.measure(BS, name, dax, f, desc)
    for name, dax, f, desc in [
        ("Cash Effect", 'CALCULATE ( - [GL Amount], KEEPFILTERS ( Account[Step] <> "Cash" ) )', MONEY,
         "Each step's effect on cash: credits less debits of its accounts in the period, without the closes; KEEPFILTERS "
         "keeps the step a visual groups by. Over all the steps it is the change in cash."),
        ("Change in Cash", 'CALCULATE ( [GL Amount], Account[Step] = "Cash" )', MONEY,
         "Debits less credits to 1010 in the period, without the closes."),
        ("Cash Effect without Opening", 'CALCULATE ( [Cash Effect], GLEntry[VoucherNumber] <> "' + c["entry"] + '" )',
         MONEY, f"Cash Effect without the lines of the opening entry {c['entry']}."),
        ("Depreciation Recorded", "CALCULATE (\n    SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] ),\n    REMOVEFILTERS ( Account ),\n"
         '    Account[AccountSubType] = "Contra Fixed Asset",\n    GLEntry[EntryType] = "Depreciation"\n)', MONEY,
         "The Depreciation journal entries' credits to accumulated depreciation, whatever account a visual groups by."),
        ("Disposal Write-off", "CALCULATE (\n    SUM ( GLEntry[Debit] ),\n    REMOVEFILTERS ( Account ),\n"
         '    Account[AccountSubType] = "Contra Fixed Asset",\n    GLEntry[EntryType] = "Asset Disposal"\n)', MONEY,
         "Accumulated depreciation written off by the Asset Disposal entries: noncash, so the indirect method adds it back."),
        ("Disposal Loss", "CALCULATE (\n    [GL Amount],\n    REMOVEFILTERS ( Account ),\n"
         '    Account[AccountType] IN { "Revenue", "Expense" },\n    GLEntry[EntryType] = "Asset Disposal"\n)', MONEY,
         "The loss (a debit) or gain (a credit) the Asset Disposal entries post to the income statement."),
        ("Disposal Cost", "CALCULATE (\n    SUM ( GLEntry[Credit] ),\n    REMOVEFILTERS ( Account ),\n"
         '    Account[AccountSubType] = "Fixed Asset",\n    GLEntry[EntryType] = "Asset Disposal"\n)', MONEY,
         "The cost of the assets the Asset Disposal entries remove."),
        ("Disposal Proceeds", "CALCULATE (\n    [GL Amount],\n    REMOVEFILTERS ( Account ),\n"
         "    Account[AccountNumber] = 1010,\n    GLEntry[EntryType] = \"Asset Disposal\"\n)", MONEY,
         "The cash the Asset Disposal entries received."),
        ("Financed by Notes", "CALCULATE (\n    SUM ( GLEntry[Credit] ),\n    REMOVEFILTERS ( Account ),\n"
         "    Account[AccountNumber] = 2110,\n    GLEntry[EntryType] = \"Debt Reclass\"\n)", MONEY,
         "Equipment invoices the Debt Reclass entries moved from payables to notes payable: an investing and financing "
         "activity with no cash, disclosed apart."),
        ("Restated Cash Flow", "VAR Recorded = [Cash Effect]\nRETURN\n    SWITCH (\n        SELECTEDVALUE ( Account[Activity] ),\n"
         "        \"Operating\", Recorded + [Disposal Write-off] + [Disposal Loss],\n"
         "        \"Investing\", Recorded + [Financed by Notes] - [Disposal Cost] + [Disposal Proceeds],\n"
         "        \"Financing\", Recorded - [Financed by Notes],\n        Recorded\n    )", MONEY,
         "The indirect method's sections: operating adds back the write-off and the loss of the disposals; investing "
         "shows only cash paid for equipment and received from disposals; financing leaves out the notes that "
         "financed equipment."),
        ("Operating Cash Flow without Sales Tax", 'CALCULATE ( [Restated Cash Flow], Account[Activity] = "Operating" )'
         ' - CALCULATE ( [Cash Effect], Account[Step] = "Sales tax" )', MONEY,
         "The restated operating cash flow without the sales tax collected and not remitted.")]:
        b.measure(BR, name, dax, f, desc)

    # the Balance Sheet page
    yr, types = col("Date", "Year"), [col("Account", "AccountType"), col("Account", "AccountSubType")]
    cur, pri, first, fx = c["cur"], c["pri"], c["first"], c["first_x"]
    ye = c["ye"]
    page = b.report.add(Page("balanceSheet", "Balance Sheet", height=800))
    page.add(Visual("bsMatrix", "pivotTable", 20, 20, 760, 520, {"Rows": types, "Columns": [yr], "Values": [M("Statement Balance")]},
                    title="Balances at each fiscal year-end, before that day's closing entries",
                    filters=[keep("bsYears", yr, years)], extra=rows_expanded(types), active=("Rows",)))
    page.add(Visual("ratios", "tableEx", 20, 560, 1240, 220, {"Values": [
        yr, M("Current Assets"), M("Current Liabilities"), M("Working Capital"), M("Current Ratio"), M("Quick Ratio"),
        M("Inventories Share"), M("Cash Net of Sales Tax")]}, title="Working capital at each fiscal year-end",
        filters=[keep("ratioYears", yr, years)]))
    page.add(answer("bsAnswer", 800, 20, 460, 520, [
        f"Working capital grew every year ({', '.join(money(v['wc']) for v in ye)}), and the current ratio barely "
        f"moved ({', '.join(f'{v['current']:.2f}' for v in ye)}): it hides the change. The quick ratio, which leaves the "
        f"inventories out, fell from {ye[0]['quick']:.2f} to {ye[1]['quick']:.2f} and {ye[2]['quick']:.2f}: at the end "
        f"of {y} cash and receivables no longer covered the current liabilities.",
        f"Inventories were {pct(c['inv_share'], 0)} of current assets at the end of {y}. Account 1090 Manufacturing Cost "
        f"Clearing has a credit balance of {money(c['a1090'])} and sits, with 8020, among the other current assets.",
        f"Sales tax payable of {money(c['tax_c'])} is a current liability that no remittance has reduced: cash net of it "
        f"was {money(c['net'][-1])} at the end of {y} ({money(c['net'][1])} a year earlier).",
        f"The notes payable ({money(c['outstanding'])}, equal to the debt schedule) sit entirely in 2110, a Long-Term "
        f"Liability, although {money(c['due_next'])} of principal is due in {d.N}: reclassified to current, it lowers "
        f"working capital by that amount."], size=10))
    page.expect = ["AccountType", "Long-Term Liability", "Working Capital", money(ye[-1]["wc"]), f"{ye[-1]['current']:.2f}",
                   f"{ye[-1]['quick']:.2f}", "Model answer"]

    # the Cash Bridge page and its drill-through page
    step, act = col("Account", "Step"), col("Account", "Activity")
    page = b.report.add(Page("cashBridge", "Cash Bridge", height=1000))
    page.add(slicer("bridgeYear", 20, 20, 400, 64, yr, [y], style="tile", single=True, title="Fiscal year"))
    page.add(Visual("waterfall", "waterfallChart", 20, 100, 760, 380, {"Category": [step], "Y": [M("Cash Effect")]},
                    title="From net income to the change in cash, in the year selected",
                    filters=[keep("wfNoCash", step, ["Cash"], exclude=True)], sort=[(step, "Ascending")],
                    alt_text="A waterfall from net income to the change in cash: the inventories absorb far more cash "
                             "than the year earned, and the unremitted sales tax and the payables hold some of it back."))
    page.add(Visual("bridgeMatrix", "pivotTable", 800, 20, 460, 460, {"Rows": [step], "Columns": [yr], "Values": [M("Cash Effect")]},
                    title="The bridge by year (drill through on a step to its postings)",
                    filters=[keep("bmYears", yr, years), keep("bmNoCash", step, ["Cash"], exclude=True)]))
    page.add(Visual("restated", "pivotTable", 20, 500, 760, 200, {"Rows": [act], "Columns": [yr],
                                                                   "Values": [(M("Cash Effect"), "As recorded"), M("Restated Cash Flow")]},
                    title="Cash flows by activity, as recorded and restated by the indirect method",
                    filters=[keep("rsYears", yr, [P, y]), keep("rsActivities", act, ["Operating", "Investing", "Financing"])]))
    page.add(card("cashCards", 20, 720, 760, 110, [M("Cash Net of Sales Tax"), M("Sales Tax Payable"), M("Notes Payable"),
                                                   M("Principal Due within a Year"), M("Financed by Notes")],
                  units_none=True, title=f"At the end of fiscal {y}", filters=[keep("ccYear", yr, [y])]))
    page.add(Visual("cashByYear", "tableEx", 20, 850, 760, 130, {"Values": [yr, M("Cash"), M("Change in Cash"), M("Cash Effect")]},
                    title="Cash at each year-end, its change, and the sum of the steps", filters=[keep("cbyYears", yr, years)]))
    rc, rp, disp, dp = c["rc"], c["rp"], c["disp"], c["disp_p"]
    page.add(answer("bridgeAnswer", 800, 500, 460, 480, [
        f"Fiscal {y}: net income {money(cur['net_income'])} and depreciation {signed(cur['depreciation'])}, but "
        f"inventories absorbed {money(-cur['inventories'])}; payables ({signed(cur['payables'])}) and the unremitted "
        f"sales tax ({signed(cur['sales_tax'])}) held cash up, and cash fell {money(-cur['cash'])} "
        f"({money(c['cash_from'])} to {money(c['cash_to'])}). Fiscal {P}: the inventories took {money(-pri['inventories'])} "
        f"and cash rose {money(pri['cash'])}.",
        f"Fiscal {F} cannot be read the same way: the opening entry {c['entry']} ({c['entry_lines']} lines) is a {F} "
        f"posting, so the bridge starts from zero cash, shows {signed(first['cash'])}, and puts "
        f"{money(first['financing'])} in debt and equity. Without it the change is {signed(fx['cash'])} from the opening "
        f"cash line of {money(c['open_cash'])}, and receivables of {money(fx['receivables'])} only fill the ledger from "
        "its opening line.",
        f"Entries that moved no cash (drill-through on Fixed assets and Debt and equity): {c['gr']} received "
        f"{money(c['financed'])} of equipment (debit {c['gr_account']}), and {c['reclass']} moved its invoice (PI "
        f"{c['reclass_invoice']}) from 2010 to 2110, a note; {disp['entry']} wrote off {money(disp['cost'])} of cost "
        f"and {money(disp['written'])} of depreciation with a {money(disp['loss'])} loss in {disp['loss_account']} and no "
        f"proceeds. The depreciation entries were {money(rc['depreciation'])}, so the recorded step is net of the "
        "write-off.",
        f"Restated {y}: operating {money(rc['operating'])}, investing {money(rc['investing'])}, financing "
        f"{money(rc['financing'])} ({c['n_principal']} principal payments); {money(rc['notes_financed'])} of equipment "
        f"acquired by a note is disclosed apart (ASC Topic 230). Restated {P}: operating {money(rp['operating'])}, "
        f"investing {money(rp['investing'])} ({money(c['capex_total'])} of equipment paid in cash less proceeds of "
        f"{money(dp['proceeds'])} on {dp['entry']}), financing {money(rp['financing'])}.",
        f"Without the unremitted tax, the operating cash flow of {y} would have been {money(c['without_tax'])}."], size=9))
    page.extra = {"visualInteractions": [{"source": "bridgeYear", "target": t, "type": "NoFilter"}
                                         for t in ("bridgeMatrix", "restated", "cashCards", "cashByYear")]}
    page.expect = ["Cash Effect", "Restated Cash Flow", money(cur["net_income"]), money(cur["inventories"]),
                   money(rc["operating"]), money(rc["financing"]), "Model answer"]
    detail = b.report.add(Page("bridgeDetail", "Bridge Detail", hidden=True))
    drillthrough(detail, step, "Fixed assets")
    detail.add(Visual("postings", "tableEx", 20, 70, 1240, 630, {"Values": [
        col("GLEntry", "PostingDate"), col("GLEntry", "VoucherNumber"), col("GLEntry", "EntryType"),
        col("GLEntry", "SourceDocumentType"), col("Account", "AccountNumber"), col("Account", "AccountName"), M("Cash Effect")]},
        title="Postings behind the step drilled through", sort=[(col("GLEntry", "PostingDate"), "Ascending")]))
    detail.expect = ["VoucherNumber", c["gr"], disp["entry"], dp["entry"]]

    # Tests 3
    b.add_test("Test 3: the bridge ends at the change in cash",
               "EVALUATE\nSUMMARIZECOLUMNS (\n    'Date'[Year],\n    TREATAS ( { " + f"{P}, {y}" + " }, 'Date'[Year] ),\n"
               "    \"Sum of the Steps\", ROUND ( [Cash Effect], 2 ),\n    \"Change in Cash\", ROUND ( [Change in Cash], 2 ),\n"
               "    \"Agrees\", ROUND ( [Cash Effect] - [Change in Cash], 2 ) = 0\n)\nORDER BY 'Date'[Year]")

    s = "Requirement 2"
    for yy, v in zip(years, ye):
        cy = f"'Date'[Year] = {yy}"
        b.check(s, f"{yy} current assets", v["ca"], f"CALCULATE ( [Current Assets], {cy} )", 0.01)
        b.check(s, f"{yy} current liabilities", v["cl"], f"CALCULATE ( [Current Liabilities], {cy} )", 0.01)
        b.check(s, f"{yy} working capital", v["wc"], f"CALCULATE ( [Working Capital], {cy} )", 0.01)
        b.check(s, f"{yy} current ratio (2 decimals)", v["current"], f"CALCULATE ( [Current Ratio], {cy} )", 0.0051)
        b.check(s, f"{yy} quick ratio (2 decimals)", v["quick"], f"CALCULATE ( [Quick Ratio], {cy} )", 0.0051)
    b.check(s, f"{y} inventories share of current assets", round(c["inv_share"], 6),
            f"CALCULATE ( [Inventories Share], 'Date'[Year] = {y} )", 0.000005)
    b.check(s, f"1090 credit balance at the end of {y}", c["a1090"],
            f"- CALCULATE ( [Balance], 'Date'[Year] = {y}, Account[AccountNumber] = 1090 )", 0.01)
    b.check(s, "1090 and 8020 fall in Other current assets", 2,
            "COUNTROWS ( FILTER ( Account, Account[AccountNumber] IN { 1090, 8020 } && Account[Step] = \"Other current assets\" ) )", 0)
    b.check(s, "1030 and 1020 fall in Receivables", 2,
            "COUNTROWS ( FILTER ( Account, Account[AccountNumber] IN { 1020, 1030 } && Account[Step] = \"Receivables\" ) )", 0)
    b.check(s, "2110 Notes Payable is a Long-Term Liability (in Debt and equity)",
            one("SELECT AccountSubType FROM Account WHERE AccountNumber = 2110") + ", Debt and equity",
            "CALCULATE ( MAX ( Account[AccountSubType] ), Account[AccountNumber] = 2110 ) & \", \" & "
            "CALCULATE ( MAX ( Account[Step] ), Account[AccountNumber] = 2110 )")
    for yy, br in ((y, cur), (P, pri), (F, first)):
        cy = f"'Date'[Year] = {yy}"
        for key, stp in STEPS:
            b.check(s, f"{yy} step {stp}", br[key], f"CALCULATE ( [Cash Effect], {cy}, Account[Step] = \"{stp}\" )", 0.01)
        b.check(s, f"{yy} change in cash", br["cash"], f"CALCULATE ( [Change in Cash], {cy} )", 0.01)
        b.check(s, f"{yy} the steps add up to the change in cash", br["cash"], f"CALCULATE ( [Cash Effect], {cy} )", 0.01)
        for a, key in (("Operating", "operating"), ("Investing", "investing"), ("Financing", "financing")):
            b.check(s, f"{yy} {a.lower()} as recorded", br[key], f"CALCULATE ( [Cash Effect], {cy}, Account[Activity] = \"{a}\" )", 0.01)
    b.check(s, f"cash at the end of {P}", c["cash_from"], f"CALCULATE ( [Cash], 'Date'[Year] = {P} )", 0.01)
    b.check(s, f"cash at the end of {y}", c["cash_to"], f"CALCULATE ( [Cash], 'Date'[Year] = {y} )", 0.01)
    b.check(s, f"without KEEPFILTERS, the Inventories step of {y} shows the change in cash", cur["cash"],
            f"CALCULATE ( CALCULATE ( - [GL Amount], Account[Step] <> \"Cash\" ), 'Date'[Year] = {y}, Account[Step] = \"Inventories\" )",
            0.01)
    b.check(s, f"a bridge from Balance differences: its {y} net income step is {y}'s less {P}'s",
            round(cur["net_income"] - pri["net_income"], 2),
            f"VAR AtYearEnd = CALCULATE ( [Balance], 'Date'[Year] = {y}, Account[AccountType] IN {{ \"Revenue\", \"Expense\" }} ) "
            f"VAR AtPriorYearEnd = CALCULATE ( [Balance], 'Date'[Year] = {P}, Account[AccountType] IN {{ \"Revenue\", \"Expense\" }} ) "
            "RETURN - ( AtYearEnd - AtPriorYearEnd )", 0.01)
    b.check(s, f"{F} change in cash without the opening entry", fx["cash"],
            f"CALCULATE ( [Cash Effect without Opening], 'Date'[Year] = {F} )", 0.01)
    b.check(s, f"{F} receivables step without the opening entry", fx["receivables"],
            f"CALCULATE ( [Cash Effect without Opening], 'Date'[Year] = {F}, Account[Step] = \"Receivables\" )", 0.01)
    oe = f"GLEntry[VoucherNumber] = \"{c['entry']}\""
    b.check(s, "the opening entry's cash line", c["open_cash"], f"CALCULATE ( [GL Amount], {oe}, Account[AccountNumber] = 1010 )", 0.01)
    b.check(s, "the opening entry's lines", c["entry_lines"], f"CALCULATE ( COUNTROWS ( GLEntry ), {oe} )", 0)
    b.check(s, f"{c['gr']}: equipment debited to {c['gr_account']}", c["financed"],
            f"CALCULATE ( SUM ( GLEntry[Debit] ), GLEntry[VoucherNumber] = \"{c['gr']}\", Account[AccountNumber] = {c['gr_account']} )", 0.01)
    rv = f"GLEntry[VoucherNumber] = \"{c['reclass']}\""
    b.check(s, f"{c['reclass']}: debit to 2010", c["financed"], f"CALCULATE ( SUM ( GLEntry[Debit] ), {rv}, Account[AccountNumber] = 2010 )", 0.01)
    b.check(s, f"{c['reclass']}: credit to 2110", c["financed"], f"CALCULATE ( SUM ( GLEntry[Credit] ), {rv}, Account[AccountNumber] = 2110 )", 0.01)
    dv = f"GLEntry[VoucherNumber] = \"{disp['entry']}\""
    b.check(s, f"{disp['entry']}: cost credited to {disp['cost_account']}", disp["cost"],
            f"CALCULATE ( SUM ( GLEntry[Credit] ), {dv}, Account[AccountNumber] = {disp['cost_account']} )", 0.01)
    b.check(s, f"{disp['entry']}: depreciation debited to {disp['written_account']}", disp["written"],
            f"CALCULATE ( SUM ( GLEntry[Debit] ), {dv}, Account[AccountNumber] = {disp['written_account']} )", 0.01)
    b.check(s, f"{disp['entry']}: loss in {disp['loss_account']}", disp["loss"],
            f"CALCULATE ( SUM ( GLEntry[Debit] ), {dv}, Account[AccountNumber] = {disp['loss_account']} )", 0.01)
    for yy, r, dd in ((y, rc, disp), (P, rp, dp)):
        cy = f"'Date'[Year] = {yy}"
        b.check(s, f"{yy} depreciation entries", r["depreciation"], f"CALCULATE ( [Depreciation Recorded], {cy} )", 0.01)
        b.check(s, f"{yy} disposal write-off", dd["written"], f"CALCULATE ( [Disposal Write-off], {cy} )", 0.01)
        b.check(s, f"{yy} disposal loss ({dd['entry']})", dd["loss"], f"CALCULATE ( [Disposal Loss], {cy} )", 0.01)
        b.check(s, f"{yy} disposal proceeds", dd["proceeds"], f"CALCULATE ( [Disposal Proceeds], {cy} ) + 0", 0.01)
        b.check(s, f"{yy} equipment financed by notes", r["notes_financed"], f"CALCULATE ( [Financed by Notes], {cy} ) + 0", 0.01)
        for a, key in (("Operating", "operating"), ("Investing", "investing"), ("Financing", "financing")):
            b.check(s, f"{yy} {a.lower()} restated", r[key],
                    f"CALCULATE ( [Restated Cash Flow], {cy}, Account[Activity] = \"{a}\" )", 0.01)
        b.check(s, f"{yy} restated sections add up to the change in cash", round(r["operating"] + r["investing"] + r["financing"], 2),
                f"CALCULATE ( SUMX ( VALUES ( Account[Activity] ), [Restated Cash Flow] ), {cy}, "
                "Account[Activity] IN { \"Operating\", \"Investing\", \"Financing\" } )", 0.01)
    b.check(s, f"{y} principal payments", c["n_principal"],
            f"CALCULATE ( DISTINCTCOUNT ( GLEntry[VoucherNumber] ), GLEntry[EntryType] = \"Debt Principal Payment\", 'Date'[Year] = {y} )", 0)
    b.check(s, f"{P} equipment received (GoodsReceipt to fixed assets)", c["capex_total"],
            f"CALCULATE ( SUM ( GLEntry[Debit] ), GLEntry[SourceDocumentType] = \"GoodsReceipt\", "
            f"Account[AccountSubType] IN {{ \"Fixed Asset\", \"Noncurrent Asset\" }}, 'Date'[Year] = {P} )", 0.01)
    for yy, v, tax in zip(years, c["net"], c["tax_steps"]):
        b.check(s, f"{yy} cash net of sales tax payable", v, f"CALCULATE ( [Cash Net of Sales Tax], 'Date'[Year] = {yy} )", 0.01)
        b.check(s, f"{yy} unremitted sales tax added to cash", tax,
                f"CALCULATE ( [Cash Effect], 'Date'[Year] = {yy}, Account[Step] = \"Sales tax\" )", 0.01)
    b.check(s, f"sales tax payable at the end of {y}", c["tax_c"], f"CALCULATE ( [Sales Tax Payable], 'Date'[Year] = {y} )", 0.01)
    b.check(s, f"{y} operating cash flow without the sales tax", c["without_tax"],
            f"CALCULATE ( [Operating Cash Flow without Sales Tax], 'Date'[Year] = {y} )", 0.01)
    b.check(s, f"notes payable at the end of {y} (2110)", c["outstanding"], f"CALCULATE ( [Notes Payable], 'Date'[Year] = {y} )", 0.01)
    b.check(s, "... equal to the debt schedule", c["outstanding"],
            f"CALCULATE ( [Scheduled Principal Outstanding], 'Date'[Year] = {y} )", 0.01)
    for agreement, v in enumerate(c["schedule"], start=1):
        b.check(s, f"note {agreement} outstanding by the schedule", v,
                f"CALCULATE ( [Scheduled Principal Outstanding], 'Date'[Year] = {y}, DebtSchedule[DebtAgreementID] = {agreement} )",
                0.01)
    b.check(s, f"principal due in {d.N}", c["due_next"], f"CALCULATE ( [Principal Due within a Year], 'Date'[Year] = {y} )", 0.01)


# --- Requirement 3: the working-capital measures ----------------------------------------------------------------

def r3(b: Build) -> None:
    d, c = b.d, b.ctx["r3"]
    y, F = d.C, d.F
    W = "Working capital"
    window = "DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -12, MONTH )"

    def flow(name, expr, filters, desc):
        b.measure(W, name, f"CALCULATE (\n    {expr},\n" + "".join(f"    {f_},\n" for f_ in filters) + f"    {window}\n)",
                  MONEY, desc)
    b.measure(W, "Full Twelve Months", "VAR Window =\n    " + window + "\nVAR MonthsInWindow =\n"
              "    COUNTROWS ( CALCULATETABLE ( VALUES ( 'Date'[YearMonth] ), Window ) )\nRETURN\n"
              "    MonthsInWindow = 12 && MAX ( 'Date'[Date] ) <= [Data Through]", None,
              "TRUE when the twelve months that end on the last date in the filter context all lie in the Date table and "
              "end by Data Through (Tutorial 15.3's guard).")
    flow("Billing TTM", "SUM ( GLEntry[Debit] )", ["Account[AccountNumber] = 1020", 'GLEntry[SourceDocumentType] = "SalesInvoice"'],
         "What was billed in the twelve months that end on the last date in the filter context: SalesInvoice debits to "
         "1020, tax and freight included, as the receivables are.")
    flow("COGS TTM", "[GL Amount]", ['Account[AccountSubType] = "COGS"'],
         "Cost of goods sold of the twelve months, without the closes (GL Amount on the COGS accounts, freight-out and "
         "the variances included).")
    flow("Issues TTM", "SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] )",
         ["Account[AccountNumber] = 1045", 'GLEntry[SourceDocumentType] = "MaterialIssue"'],
         "Materials issued to production in the twelve months: MaterialIssue credits to 1045.")
    flow("Shipments TTM", "SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] )",
         ["Account[AccountNumber] = 1040", 'GLEntry[SourceDocumentType] = "Shipment"'],
         "Finished goods shipped in the twelve months at standard cost: Shipment credits to 1040.")
    flow("Supplier Invoices TTM", "SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] )",
         ["Account[AccountNumber] = 2010", 'GLEntry[SourceDocumentType] = "PurchaseInvoice"'],
         "Supplier invoices of the twelve months: PurchaseInvoice credits to 2010.")
    for name, dax, desc in [
        ("Receivables", "CALCULATE ( [Balance], Account[AccountNumber] = 1020 )", "Balance of 1020 Accounts Receivable."),
        ("Materials", "CALCULATE ( [Balance], Account[AccountNumber] = 1045 )", "Balance of 1045 Inventory - Materials and Packaging."),
        ("Finished Goods", "CALCULATE ( [Balance], Account[AccountNumber] = 1040 )", "Balance of 1040 Inventory - Finished Goods."),
        ("Payables", "- CALCULATE ( [Balance], Account[AccountNumber] = 2010 )", "Balance of 2010 Accounts Payable, positive.")]:
        b.measure(W, name, dax, MONEY, desc)
    op = f'GLEntry[VoucherNumber] <> "{c["entry"]}"'
    for name, dax, desc in [
        ("DSO", "IF ( [Full Twelve Months], DIVIDE ( [Receivables], [Billing TTM] ) * 365 )",
         "Days sales outstanding: receivables at the end of the period over the twelve months' billing, times 365."),
        ("DSO without Opening", f"IF (\n    [Full Twelve Months],\n    DIVIDE ( CALCULATE ( [Receivables], {op} ), [Billing TTM] ) * 365\n)",
         f"DSO with the receivables line of the opening entry {c['entry']} left out."),
        ("DIO", "IF ( [Full Twelve Months], DIVIDE ( [Inventories], [COGS TTM] ) * 365 )",
         "Days inventory outstanding: the inventories at the end of the period over the twelve months' cost of goods sold, times 365."),
        ("Materials Days", "IF ( [Full Twelve Months], DIVIDE ( [Materials], [Issues TTM] ) * 365 )",
         "Days of materials supply: materials and packaging at the end of the period over the twelve months' issues, times 365."),
        ("Finished Goods Days", "IF ( [Full Twelve Months], DIVIDE ( [Finished Goods], [Shipments TTM] ) * 365 )",
         "Days of finished goods supply: finished goods at the end of the period over the twelve months' shipments, times 365."),
        ("DPO", "IF ( [Full Twelve Months], DIVIDE ( [Payables], [Supplier Invoices TTM] ) * 365 )",
         "Days payables outstanding: payables at the end of the period over the twelve months' supplier invoices, times 365."),
        ("DPO without Opening", f"IF (\n    [Full Twelve Months],\n    DIVIDE ( CALCULATE ( [Payables], {op} ), [Supplier Invoices TTM] ) * 365\n)",
         f"DPO with the payables line of the opening entry {c['entry']} left out."),
        ("Cash Conversion Cycle", "IF ( [Full Twelve Months], [DSO] + [DIO] - [DPO] )", "DSO plus DIO less DPO, in days."),
        ("Cycle without Opening", "IF ( [Full Twelve Months], [DSO without Opening] + [DIO] - [DPO without Opening] )",
         "The cash conversion cycle with the opening entry's receivables and payables left out.")]:
        b.measure(W, name, dax, DAYS, desc)
    A = "Working capital (average balance)"
    b.measure(A, "Opening Balance", "VAR YearStart = MIN ( 'Date'[Date] )\nRETURN\n"
              "    CALCULATE ( SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ), REMOVEFILTERS ( 'Date' ), 'Date'[Date] < YearStart )\n"
              "        + CALCULATE (\n            SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ),\n"
              "            REMOVEFILTERS ( 'Date' ),\n            'Date'[Date] >= YearStart,\n"
              f"            GLEntry[VoucherNumber] = \"{c['entry']}\"\n        )", MONEY,
              f"The balance before the first date in the filter context; in {F}, the lines of the opening entry "
              f"{c['entry']}, which stand for the balances brought forward.")
    b.measure(A, "Average Balance", "DIVIDE ( [Opening Balance] + [Balance], 2 )", MONEY,
              "The average of the opening and the closing balance of the period.")
    guard = "HASONEVALUE ( 'Date'[Year] ) && MAX ( 'Date'[Date] ) <= [Data Through]"
    for name, acc, flow_, desc in [
        ("DSO on Average Balance", "Account[AccountNumber] = 1020",
         'CALCULATE ( SUM ( GLEntry[Debit] ), Account[AccountNumber] = 1020, GLEntry[SourceDocumentType] = "SalesInvoice" )',
         "DSO on the year's average receivables and the year's billing."),
        ("DIO on Average Balance", "Account[AccountNumber] IN { 1040, 1045, 1046 }",
         'CALCULATE ( [GL Amount], Account[AccountSubType] = "COGS" )',
         "DIO on the year's average inventories and the year's cost of goods sold."),
        ("Materials Days on Average Balance", "Account[AccountNumber] = 1045",
         'CALCULATE ( SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] ), Account[AccountNumber] = 1045, '
         'GLEntry[SourceDocumentType] = "MaterialIssue" )',
         "Days of materials supply on the year's average materials and the year's issues."),
        ("DPO on Average Balance", "Account[AccountNumber] = 2010",
         'CALCULATE ( SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] ), Account[AccountNumber] = 2010, '
         'GLEntry[SourceDocumentType] = "PurchaseInvoice" )',
         "DPO on the year's average payables and the year's supplier invoices.")]:
        sign = "- " if "2010" in acc else ""
        b.measure(A, name, f"IF (\n    {guard},\n    DIVIDE ( {sign}CALCULATE ( [Average Balance], {acc} ), {flow_} ) * 365\n)",
                  DAYS, desc + " Blank unless one fiscal year is in the filter context.")
    T = "Policy targets"
    for name, dax, desc in [
        ("Materials Target Days", "IF (\n    [Full Twelve Months],\n    CALCULATE ( MAX ( 'Item'[TargetDaysSupply] ), "
                                  f"KEEPFILTERS ( 'Item'[ItemGroup] IN {{ \"{MATERIALS[0]}\", \"{MATERIALS[1]}\" }} ) )\n)",
         "The largest TargetDaysSupply of the materials items (raw materials 28 days, packaging 24), shown where the "
         "days of supply are."),
        ("Finished Goods Target Days", "IF (\n    [Full Twelve Months],\n    CALCULATE ( MAX ( 'Item'[TargetDaysSupply] ), "
                                       "KEEPFILTERS ( 'Item'[ItemType] = \"Finished Good\" ) )\n)",
         "The largest TargetDaysSupply of the finished goods (12-16 days manufactured, 24-28 purchased), shown where the "
         "days of supply are."),
        ("Materials Days to Target", "DIVIDE ( [Materials Days], [Materials Target Days] )",
         "Days of materials supply as a multiple of the target: the basis of the matrix's icons."),
        ("Finished Goods Days to Target", "DIVIDE ( [Finished Goods Days], [Finished Goods Target Days] )",
         "Days of finished goods supply as a multiple of the target: the basis of the matrix's icons.")]:
        b.measure(T, name, dax, DAYS if "Target Days" in name else RATIO, desc)
    # the tooltip's components
    comps = [("Receivables", "[Receivables]", "[Billing TTM]"), ("Inventories", "[Inventories]", "[COGS TTM]"),
             ("Materials", "[Materials]", "[Issues TTM]"), ("Finished goods", "[Finished Goods]", "[Shipments TTM]"),
             ("Payables", "[Payables]", "[Supplier Invoices TTM]")]
    b.model.add(entered_table("Components", [("Component", "string"), ("Order", "int64")],
                              [[n, i + 1] for i, (n, _, _) in enumerate(comps)]))
    b.model.tables["Components"].column("Component").sort_by = "Order"
    b.model.tables["Components"].column("Order").hidden = True
    b.model.query_order.append("Components")
    sw = lambda k: ("SWITCH (\n    SELECTEDVALUE ( Components[Component] ),\n" +   # noqa: E731
                    "".join(f"    \"{n}\", {v if k == 1 else f_},\n" for n, v, f_ in comps) + "    BLANK ()\n)")
    b.measure(W, "Component Balance", sw(1), COUNT, "The balance of the component in the row, at the end of the period.")
    b.measure(W, "Component Flow TTM", sw(2), COUNT, "The twelve-month flow the component is measured against.")
    # the field parameter (Modeling > New parameter > Fields), as Exercise 15.3 built it
    p = "WC Measure"
    tuples = ",\n".join(f"    (\"{n}\", NAMEOF ( '{KM}'[{n}] ), {i})" for i, n in enumerate(WC))
    b.model.add(Table(p, [
        Column(p, "string", "[Value1]", sort_by=f"{p} Order", extra=(f"relatedColumnDetails\n\t\t\tgroupByColumn: '{p} Fields'",)),
        Column(f"{p} Fields", "string", "[Value2]", hidden=True, sort_by=f"{p} Order",
               extra=('extendedProperty ParameterMetadata = {"version":3,"kind":2}',)),
        Column(f"{p} Order", "int64", "[Value3]", fmt="0", summarize="sum", hidden=True)], dax="{\n" + tuples + "\n}"))

    # the Working Capital page and its tooltip page
    qs, avg = c["qs"], c["avg"]
    last, first_q = qs[-1], qs[0]
    yq, yr = col("Date", "YearQuarter"), col("Date", "Year")
    pf = col(p, p)
    page = b.report.add(Page("workingCapital", "Working Capital", height=1180))
    page.add(slicer("wcMeasure", 20, 20, 300, 230, pf, ["Cash Conversion Cycle"], title="Measure"))
    page.add(ParamVisual("wcLine", "lineChart", 340, 20, 920, 300, {"Category": [yq], "Y": [M(n) for n in WC]},
                         title="The measure chosen, at each quarter-end (hover for the balances and flows)",
                         filters=[keep("wcLineYears", yr, d.years)], params={"Y": pf},
                         container_objects={"visualTooltip": [{"properties": {
                             "show": lit(True), "type": lit("ReportPage"), "section": lit("wcTooltip")}}]}))
    shown = ["DSO", "DSO without Opening", "DIO", "Materials Days", "Materials Target Days", "Finished Goods Days",
             "Finished Goods Target Days", "DPO", "DPO without Opening", "Cash Conversion Cycle", "Cycle without Opening"]
    icons = (icon_rules(M("Materials Days to Target"), f"{KM}.Materials Days", 1.25, 0.8)["values"] +
             icon_rules(M("Finished Goods Days to Target"), f"{KM}.Finished Goods Days", 1.25, 0.8)["values"])
    page.add(Visual("wcMatrix", "pivotTable", 20, 340, 1240, 330, {"Rows": [yq], "Values": [M(n) for n in shown]},
                    title="The measures at each quarter-end (icons: days of supply against the policy target)",
                    filters=[keep("wcMatrixYears", yr, d.years)], objects={"values": icons}))
    page.add(Visual("wcAverage", "tableEx", 20, 690, 1240, 150, {"Values": [
        yr, M("DSO"), M("DSO on Average Balance"), M("DIO"), M("DIO on Average Balance"), M("Materials Days"),
        M("Materials Days on Average Balance"), M("DPO"), M("DPO on Average Balance")]},
        title="Year-end measures against the versions on the year's average balance", filters=[keep("wcAvgYears", yr, d.years)]))
    ends = c["ends"]
    page.add(answer("wcAnswer", 20, 860, 1240, 300, [
        f"From {first_q['label']} to {last['label']} the cycle grew from {first_q['ccc']:.1f} to {last['ccc']:.1f} days "
        f"({first_q['ccc_x']:.1f} to {last['ccc_x']:.1f} without the opening entry), and it grew entirely through "
        f"inventory: DIO {first_q['dio']:.1f} to {last['dio']:.1f}, materials {first_q['mat']:.1f} to {last['mat']:.1f} "
        f"days against a target of {c['raw']} (packaging {c['pack']}), finished goods {first_q['fg']:.1f} to "
        f"{last['fg']:.1f} against {c['made'][0]}-{c['made'][1]} days (manufactured, lot-for-lot) and "
        f"{c['bought'][0]}-{c['bought'][1]} (purchased). Every policy ends {d.C}-12-31.",
        f"Receivables and payables barely moved: DSO {first_q['dso']:.1f} to {last['dso']:.1f} ({first_q['dso_x']:.1f} "
        f"to {last['dso_x']:.1f} without the opening line); DPO as recorded fell from {c['dpo_from']:.1f} to "
        f"{c['dpo_to']:.1f}, but without the opening line it stayed at {first_q['dpo_x']:.1f} to {last['dpo_x']:.1f}: "
        f"the apparent fall is the constant {c['opening_ap']:.1f} million of unsupported opening payables diluted by "
        f"growing purchases. With customers' terms of about {c['customers']:.0f} days and suppliers' of about "
        f"{c['suppliers']:.0f} (value-weighted), receivables without the opening line run {c['ar_beyond']} beyond "
        f"terms ({c['ar_recorded']:.0f} days as recorded) and payables {c['ap_beyond']} beyond.",
        f"The average-balance versions lag a fast build ({c['build_avg']:.1f} against {c['build_end']:.1f} materials days "
        f"in {d.C}) and in {F} rest on the opening entry, so materials look like {c['first_avg']:.0f} days when the "
        f"year-end stock stood at {c['first_end']:.0f}. The committee should see the quarter-end versions on full "
        f"twelve-month windows, without the opening lines where those distort; {F} can show only its last quarter.",
        f"COGS is GL Amount on the COGS accounts: the close {c['close']} credits COGS by {c['close_millions']:.2f} million, "
        "so a window that included a close would read zero without GL Amount."], size=10))
    page.expect = ["Cash Conversion Cycle", f"{last['ccc']:.1f}", f"{first_q['dio']:.1f}", f"{last['mat']:.1f}",
                   "Gray up arrow", f"{avg[-1]['mat']:.1f}", "Model answer"]
    tip = b.report.add(Page("wcTooltip", "WC Tooltip", width=320, height=240, hidden=True))
    tip.page_type = "Tooltip"
    tip.extra = {"pageBinding": {"name": "wcTooltipBinding", "type": "Tooltip", "referenceScope": "Default"},
                 "objects": {"pageSize": [{"properties": {"pageSizeTypes": lit("Tooltip")}}]}}
    tip.add(Visual("tipTable", "tableEx", 0, 0, 320, 240, {"Values": [
        col("Components", "Component"), (M("Component Balance"), "Balance"), (M("Component Flow TTM"), "12-month flow")]}))
    tip.expect = ["Component", "Receivables", "Payables"]

    s = "Requirement 3"
    keys = [("dso", "DSO"), ("dso_x", "DSO without Opening"), ("dio", "DIO"), ("mat", "Materials Days"),
            ("fg", "Finished Goods Days"), ("dpo", "DPO"), ("dpo_x", "DPO without Opening"), ("ccc", "Cash Conversion Cycle"),
            ("ccc_x", "Cycle without Opening")]
    for q in qs:
        for k, n in keys:
            b.check(s, f"{q['label']} {n} (1 decimal)", q[k], f"CALCULATE ( [{n}], 'Date'[YearQuarter] = \"{q['label']}\" )", 0.0501)
    for label in [f"{F}-Q1", f"{F}-Q2", f"{F}-Q3"] + [f"{d.N}-Q{i}" for i in range(1, 5)]:
        for n in ("DSO", "Cash Conversion Cycle"):
            b.check(s, f"{label} {n} (blank)", "blank", blank(f"CALCULATE ( [{n}], 'Date'[YearQuarter] = \"{label}\" )"))
    for a in avg:
        cy = f"'Date'[Year] = {a['year']}"
        for k, n in (("dso", "DSO"), ("dio", "DIO"), ("mat", "Materials Days"), ("dpo", "DPO")):
            b.check(s, f"{a['year']} {n} on the average balance (1 decimal)", a[k],
                    f"CALCULATE ( [{n} on Average Balance], {cy} )", 0.0501)
    b.check(s, f"{d.N} average-balance DSO (blank)", "blank", blank(f"CALCULATE ( [DSO on Average Balance], 'Date'[Year] = {d.N} )"))
    close_credit = one("SELECT SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                       "WHERE a.AccountSubType = 'COGS' AND g.VoucherNumber = ?", c["close"])
    claim(abs(close_credit / 1e6 - c["close_millions"]) < 0.01, "the close's COGS credit agrees")
    b.check(s, f"{c['close']}: credit to COGS", round(close_credit, 2),
            f"CALCULATE ( SUM ( GLEntry[Credit] ), GLEntry[VoucherNumber] = \"{c['close']}\", Account[AccountSubType] = \"COGS\" )", 0.01)
    b.check(s, f"{y} COGS with the closes (zero)", 0,
            f"CALCULATE ( SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ), Account[AccountSubType] = \"COGS\", 'Date'[Year] = {y} )", 0.01)
    for label, where, v in [("raw materials target", "'Item'[ItemGroup] = \"Raw Materials\"", c["raw"]),
                            ("packaging target", "'Item'[ItemGroup] = \"Packaging\"", c["pack"])]:
        b.check(s, f"{label} (min)", v, f"CALCULATE ( MIN ( 'Item'[TargetDaysSupply] ), {where} )", 0)
        b.check(s, f"{label} (max)", v, f"CALCULATE ( MAX ( 'Item'[TargetDaysSupply] ), {where} )", 0)
    for label, mode, (lo, hi) in (("manufactured finished goods", "Manufactured", c["made"]),
                                  ("purchased finished goods", "Purchased", c["bought"])):
        where = f"'Item'[ItemType] = \"Finished Good\", 'Item'[SupplyMode] = \"{mode}\""
        b.check(s, f"{label}: lowest target", lo, f"CALCULATE ( MIN ( 'Item'[TargetDaysSupply] ), {where} )", 0)
        b.check(s, f"{label}: highest target", hi, f"CALCULATE ( MAX ( 'Item'[TargetDaysSupply] ), {where} )", 0)
    b.check(s, "items with a policy target", one("SELECT COUNT(DISTINCT ItemID) FROM InventoryPolicy"),
            "COUNTROWS ( FILTER ( 'Item', NOT ISBLANK ( 'Item'[TargetDaysSupply] ) ) )", 0)
    b.check(s, "the earliest policy end", f"{d.C}-12-31", fmt_date("MIN ( 'Item'[PolicyEnd] )"))
    b.check(s, "the latest policy end", f"{d.C}-12-31", fmt_date("MAX ( 'Item'[PolicyEnd] )"))
    b.check(s, f"Materials Target Days ({y})", c["raw"], f"CALCULATE ( [Materials Target Days], 'Date'[Year] = {y} )", 0)
    b.check(s, f"Finished Goods Target Days ({y})", c["bought"][1],
            f"CALCULATE ( [Finished Goods Target Days], 'Date'[Year] = {y} )", 0)
    b.check(s, f"targets blank before a full window ({F}-Q3)", "blank",
            blank(f"CALCULATE ( [Materials Target Days], 'Date'[YearQuarter] = \"{F}-Q3\" )"))
    q4 = f"'Date'[YearQuarter] = \"{last['label']}\""
    b.check(s, f"tooltip: materials balance at {last['label']}", round(last["mat_balance"], 0),
            f"CALCULATE ( [Component Balance], {q4}, Components[Component] = \"Materials\" )", 0.5)
    b.check(s, f"tooltip: materials issued in the twelve months to {last['label']}", round(last["issues"], 0),
            f"CALCULATE ( [Component Flow TTM], {q4}, Components[Component] = \"Materials\" )", 0.5)
    b.check(s, "the field parameter's measures, in order", ", ".join(WC),
            f"CONCATENATEX ( '{p}', '{p}'[{p}], \", \", '{p}'[{p} Order], ASC )")


# --- Requirement 4: the materials build and a 2027 target ---------------------------------------------------------

def r4(b: Build) -> None:
    d, c, c3 = b.d, b.ctx["r4"], b.ctx["r3"]
    y = d.C
    MB = "Materials"
    for name, dax, f, desc in [
        ("Materials Build", "[Materials Received] - [Materials Issued]", MONEY, "Materials received less materials issued."),
        ("Supply Plan Receipts", f'CALCULATE ( [Materials Received], Receipts[Channel] = "{PLAN}" )', MONEY,
         "Materials received on requisitions the supply plan raised."),
        ("Shortfall Receipts", f'CALCULATE ( [Materials Received], Receipts[Channel] = "{SHORT}" )', MONEY,
         "Materials received on work-order shortfall requisitions."),
        ("Shortfall Requisitions", f'CALCULATE ( COUNTROWS ( Requisitions ), KEEPFILTERS ( Requisitions[Channel] = "{SHORT}" ) )',
         COUNT, "The number of work-order shortfall requisitions."),
        ("Requisitioned Value", "SUM ( Requisitions[EstimatedValue] )", MONEY,
         "Quantity times EstimatedUnitCost of the requisitions."),
        ("Self-requested", "COUNTROWS ( FILTER ( Requisitions, Requisitions[RequestedByEmployeeID] = Requisitions[ApprovedByEmployeeID] ) ) + 0",
         COUNT, "Requisitions approved by the employee who requested them."),
        ("Open Requisitions", 'CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Status] = "Approved" ) + 0', COUNT,
         "Requisitions approved and not converted to an order (Status Approved)."),
        ("Open Requisition Value", 'CALCULATE ( [Requisitioned Value], Requisitions[Status] = "Approved" )', MONEY,
         "The estimated value of the open requisitions."),
        ("Late Shortfall Requisitions", "COUNTROWS (\n    FILTER (\n        Requisitions,\n"
         "        NOT ISBLANK ( Requisitions[DueDate] ) && Requisitions[RequestDate] > Requisitions[DueDate]\n    )\n) + 0",
         COUNT, "Shortfall requisitions dated after the due date of the work order they name."),
        ("Late Shortfall Value", "SUMX (\n    FILTER (\n        Requisitions,\n"
         "        NOT ISBLANK ( Requisitions[DueDate] ) && Requisitions[RequestDate] > Requisitions[DueDate]\n    ),\n"
         "    Requisitions[EstimatedValue]\n)", MONEY, "The estimated value of the late shortfall requisitions."),
        ("Pairs", "COUNTROWS ( ShortfallPairs )", COUNT, "Work order and item pairs with a shortfall requisition."),
        ("Repeated Pairs", "COUNTROWS ( FILTER ( ShortfallPairs, ShortfallPairs[RequisitionCount] > 1 ) )", COUNT,
         "Pairs requisitioned more than once."),
        ("Requisitions in Repeated Pairs",
         "SUMX ( FILTER ( ShortfallPairs, ShortfallPairs[RequisitionCount] > 1 ), ShortfallPairs[RequisitionCount] )", COUNT,
         "The requisitions of the pairs requisitioned more than once."),
        ("Most Requisitions for a Pair", "MAX ( ShortfallPairs[RequisitionCount] )", COUNT,
         "The most shortfall requisitions raised for one work order and item."),
        ("Pairs with Issues", "COUNTROWS ( FILTER ( ShortfallPairs, NOT ISBLANK ( ShortfallPairs[IssuedQty] ) ) )", COUNT,
         "Pairs whose work order was issued the item."),
        ("Requisitioned Units", "SUM ( ShortfallPairs[RequisitionedQty] )", UNITS, "Units the shortfall requisitions asked for."),
        ("Issued Units", "SUM ( ShortfallPairs[IssuedQty] )", UNITS, "Units issued to the same work orders and items."),
        ("Issued Cost", "SUM ( ShortfallPairs[IssuedCost] )", MONEY, "The issues to the same pairs at standard cost."),
        ("Pair Estimated Value", "SUM ( ShortfallPairs[EstimatedValue] )", MONEY, "The estimated value of the pairs' requisitions."),
        ("Open Order Lines", "VAR AsOf = [Data Through]\nRETURN\n    COUNTROWS (\n        FILTER (\n"
         "            FILTER ( OrderLines, OrderLines[OrderDate] <= AsOf ),\n"
         "            OrderLines[Quantity]\n                - CALCULATE ( SUM ( Receipts[QuantityReceived] ), REMOVEFILTERS ( 'Date' ), "
         "Receipts[ReceiptDate] <= AsOf ) > 0.0001\n        )\n    )", COUNT,
         "Order lines dated by Data Through and not fully received by then."),
        ("Open Order Value", "VAR AsOf = [Data Through]\nRETURN\n    SUMX (\n        FILTER ( OrderLines, OrderLines[OrderDate] <= AsOf ),\n"
         "        VAR OpenQty = OrderLines[Quantity]\n            - CALCULATE ( SUM ( Receipts[QuantityReceived] ), "
         "REMOVEFILTERS ( 'Date' ), Receipts[ReceiptDate] <= AsOf )\n"
         "        RETURN IF ( OpenQty > 0.0001, OpenQty * OrderLines[UnitCost] )\n    )", MONEY,
         "The ordered quantity not yet received at Data Through, at the order's unit cost.")]:
        b.measure(MB, name, dax, f, desc)
    # the what-if parameter (Modeling > New parameter > Numeric range), the policy target as its default
    TD = "Target Days"
    b.model.add(Table(TD, [Column(TD, "int64", "[Value]", fmt="0", summarize="none",
                                  extra=('extendedProperty ParameterMetadata = {"version":0}',))],
                      measures=[Measure(f"{TD} Value", f"SELECTEDVALUE ( '{TD}'[{TD}], {c3['raw']} )", "0",
                                        "The target days of materials supply chosen on the slider; the policy target "
                                        f"({c3['raw']} days) until one is chosen.")],
                      dax="GENERATESERIES ( 7, 120, 1 )"))
    for name, dax, f, desc in [
        ("Allowed Materials", f"DIVIDE ( [Issues TTM], 365 ) * [{TD} Value]", MONEY,
         "The materials the target allows at the twelve months' rate of issue."),
        ("Excess Materials", "[Materials] - [Allowed Materials]", MONEY, "Materials on hand above what the target allows."),
        ("Months of Issues in Excess", "DIVIDE ( [Excess Materials], DIVIDE ( [Issues TTM], 12 ) )", RATIO,
         "The excess in months of issues at the twelve months' rate."),
        ("Finished Goods at Target", "DIVIDE ( [Shipments TTM], 365 ) * [Finished Goods Target Days]", MONEY,
         "The finished goods the policy target allows at the twelve months' rate of shipment.")]:
        b.measure(MB, name, dax, f, desc)

    # the Materials Build page
    ym, yr = col("Date", "YearMonth"), col("Date", "Year")
    ig, code = col("Item", "ItemGroup"), col("Item", "ItemCode")
    ch = col("Requisitions", "Channel")
    page = b.report.add(Page("materialsBuild", "Materials Build", height=1100))
    page.add(Visual("receiptsIssues", "lineClusteredColumnComboChart", 20, 20, 820, 280, {
        "Category": [ym], "Y": [M("Supply Plan Receipts"), M("Shortfall Receipts")], "Y2": [M("Materials Issued")]},
        title="Materials received by channel (columns) and issued (line), by month",
        filters=[keep("riYears", yr, d.years)]))
    page.add(Visual("channelByYear", "tableEx", 20, 320, 820, 140, {"Values": [
        yr, M("Supply Plan Receipts"), M("Shortfall Receipts"), M("Materials Received"), M("Materials Issued"), M("Materials Build")]},
        title="Materials by year and channel", filters=[keep("cbyYears", yr, d.years)]))
    levels = [ig, code]
    page.add(Visual("buildMatrix", "pivotTable", 20, 480, 400, 420, {"Rows": levels, "Values": [M("Materials Build")]},
                    title=f"The build of fiscal {y} by item group and item",
                    filters=[keep("bmYear", yr, [y]), keep("bmGroups", ig, list(MATERIALS))],
                    sort=[(M("Materials Build"), "Descending")], extra=rows_expanded(levels), active=("Rows",)))
    page.add(Visual("approvals", "pivotTable", 440, 480, 400, 240, {
        "Rows": [ch, col("Requisitions", "ApproverTitle")], "Values": [M("Requisition Count"), M("Self-requested")]},
        title="Who approved the requisitions of each channel", extra=rows_expanded([ch, col("Requisitions", "ApproverTitle")]),
        active=("Rows",)))
    page.add(Visual("requesters", "tableEx", 440, 740, 400, 200, {"Values": [
        col("Requisitions", "RequesterTitle"), M("Shortfall Requisitions")]}, title="Who requested the shortfall requisitions",
        filters=[keep("rqChannel", ch, [SHORT])], sort=[(M("Shortfall Requisitions"), "Descending")]))
    by = {r["year"]: r for r in c["by_year"]}
    top = c["top_items"]
    names = [t_["name"] or t_["plural"] for t_ in top if t_["name"] or t_["plural"]]
    page.add(answer("buildAnswer", 860, 20, 400, 1060, [
        "Receipts by channel (supply plan / work-order shortfall): " + "; ".join(
            f"{yy} {money(by[yy]['plan'][1])} ({by[yy]['plan'][0]:,} lines) / {money(by[yy]['short'][1])} "
            f"({by[yy]['short'][0]:,} lines)" for yy in d.years) +
        f". Issues stayed near {round(c['ttm'] / 1e6):.0f} million a year ({y}: raw materials {money(c['raw_issued'])}, "
        f"packaging {money(c['pack_issued'])}). The supply plan's receipts stay below production's use, which holds "
        "steady; the work-order shortfall channel carries the build.",
        f"The build of {y} was {money(c['build'])}; six raw materials make up {pct(c['share'], 0)}: " + ", ".join(
            f"{t_['code']} {signed(t_['amount'])}" for t_ in top) + f" ({', '.join(names)}); packaging nets "
        f"{money(c['packaging'])}. Stock by item cannot be rebuilt: the opening materials ({money(c['opening_materials'])}) "
        "carry no item detail.",
        "Shortfall requisitions: " + ", ".join(f"{n:,}" for n in c["short_counts"]) + " a year, estimated at " +
        ", ".join(money(v) for v in c["short_values"]) + f". Of the {c['pairs']:,} work order and item pairs, "
        f"{c['repeated']:,} were requisitioned more than once, holding {c['in_repeated']:,} requisitions; the most for one "
        f"pair is {c['most']} ({c['wo']} and {c['item']}), every month from {c['first_request']} to {c['last_request']}, "
        f"though the work order was due {c['due']} and completed {c['completed']}.",
        f"Against the issues: {c['matched']:,} pairs matched and {c['unmatched']} with nothing issued; {c['units']:,.1f} "
        f"units requisitioned (estimated {money(c['estimated'])}) against {c['units_issued']:,.1f} issued to the same "
        f"pairs ({money(c['issued_cost'])} at standard). Receipts from shortfall requisitions over the three years: "
        f"{money(c['short_receipts'])}.",
        f"Approvals: every shortfall requisition ({c['n_short']:,}) was approved by employee {c['approver']}, the "
        f"{c['approver_title']}, who also requested {c['self_requested']} of them; production staff requested the rest ("
        + ", ".join(f"{t_} {n:,}" for t_, n in c["requester_titles"]) + f"). The CFO approved {c['cfo_plan']:,} supply-plan "
        f"requisitions and {c['no_plan']} have no approver; the capital requests were approved by "
        + " and ".join(f"the {t_} ({n})" for t_, n in c["other_app"]) + ". One manager both runs production and approves "
        "every purchase it asks for, with no check against stock on hand or open orders."], size=9))
    page.expect = ["Shortfall Receipts", money(by[y]["short"][1]), top[0]["code"], money(top[0]["amount"]),
                   c["approver_title"], "Model answer"]

    # the Materials Target page
    td = col(TD, TD)
    page = b.report.add(Page("materialsTarget", "Materials Target", height=1100))
    page.add(card("pairCards", 20, 20, 820, 110, [M("Pairs"), M("Repeated Pairs"), M("Requisitions in Repeated Pairs"),
                                                  M("Most Requisitions for a Pair"), M("Pairs with Issues"),
                                                  M("Requisitioned Units"), M("Issued Units")], units_none=True,
                  title="Shortfall requisitions by work order and item"))
    rc = col("ShortfallPairs", "RequisitionCount")
    page.add(Visual("topPairs", "tableEx", 20, 150, 820, 300, {"Values": [
        col("ShortfallPairs", "WorkOrderNumber"), code, rc, col("ShortfallPairs", "FirstRequest"),
        col("ShortfallPairs", "LastRequest"), col("ShortfallPairs", "DueDate"), col("ShortfallPairs", "RequisitionedQty"),
        col("ShortfallPairs", "IssuedQty")]}, title="The pairs requisitioned most often", sort=[(rc, "Descending")]))
    page.add(Visual("targetSlider", "slicer", 20, 470, 400, 100, {"Values": [td]}, title="Target days of materials supply",
                    objects={"data": [{"properties": {"mode": lit("Single")}}]}))
    page.add(card("whatIfCards", 440, 470, 400, 100, [meas(TD, f"{TD} Value"), M("Allowed Materials"), M("Excess Materials"),
                                                      M("Months of Issues in Excess")], units_none=True,
                  filters=[keep("wicYear", yr, [y])]))
    page.add(Visual("whatIfTable", "tableEx", 20, 590, 820, 160, {"Values": [
        td, M("Allowed Materials"), M("Excess Materials"), M("Months of Issues in Excess")]},
        title=f"Targets tested at the end of fiscal {y}", filters=[keep("witYear", yr, [y]), keep("witDays", td, [28, 60, 90])]))
    page.add(card("leftOut", 20, 770, 820, 110, [M("Finished Goods"), M("Finished Goods at Target"), M("Open Requisitions"),
                                                 M("Open Requisition Value"), M("Open Order Lines"), M("Open Order Value")],
                  units_none=True, title="What the estimate leaves out", filters=[keep("loYear", yr, [y])]))
    page.extra = {"visualInteractions": [{"source": "targetSlider", "target": "whatIfTable", "type": "NoFilter"}]}
    wi = c["whatif"]
    fall = -b.ctx["r2"]["cur"]["cash"]
    page.add(answer("targetAnswer", 860, 20, 400, 1060, [
        f"At the twelve months' rate of issue ({money(c['ttm'])}), the target allows: " + "; ".join(
            f"{w['days']} days {money(w['allowed'])}, an excess of {money(w['excess'])} ({w['months']:.2f} months of "
            "issues)" for w in wi) + f". Even at {wi[-1]['days']} days the excess is about {c['multiple']} times the "
        f"year's fall in cash ({money(fall)}).",
        f"A 2027 target: the policy's {c3['raw']} days for raw materials ({c3['pack']} for packaging), reached by "
        "buying less than production uses until the stock falls to it, with an interim target (60 or 90 days) for the "
        "audit committee to follow each quarter.",
        "What the estimate assumes: issues continue at the year's rate, the stock is usable and valued at standard, "
        "and purchases can fall below use without stopping production. What it leaves out: "
        f"finished goods, which at {FG(c)} days of shipments would be {money(c['fg_target'])} against "
        f"{money(c['fg'])}; {c['n_never']} approved, unordered shortfall requisitions ({money(c['never_value'])}); "
        f"{c['open_lines']} purchase order lines not fully received at the year-end ({money(c['open_value'])}, of which "
        f"materials {money(c['open_materials'])}); and every inventory policy ended {d.C}-12-31, so the 2027 targets "
        "need approval.",
        "The cash comes back only as purchases fall below use, over 2027 and beyond, and only if the stock can be "
        "used: at the current rate a year's issues would consume less than the stock on hand.",
        "Shortfall requisitions dated after their work order's due date: " + ", ".join(
            f"{yy} {n:,} ({money(v)})" for yy, (n, v) in zip(d.years, c["late"])) + "."], size=10))
    page.expect = ["Most Requisitions for a Pair", c["wo"], money(wi[0]["excess"]), money(wi[-1]["excess"]),
                   "Months of Issues in Excess", "Model answer"]

    s = "Requirement 4"
    mats = "'Item'[ItemGroup] IN { \"Raw Materials\", \"Packaging\" }"
    for r in c["by_year"]:
        cy = f"'Date'[Year] = {r['year']}"
        for label, ch_, (n, v) in (("supply plan", PLAN, r["plan"]), ("shortfall", SHORT, r["short"])):
            b.check(s, f"{r['year']} materials receipt lines, {label}", n,
                    f"CALCULATE ( COUNTROWS ( Receipts ), {cy}, Receipts[Channel] = \"{ch_}\", {mats} )", 0)
            b.check(s, f"{r['year']} materials received, {label}", v,
                    f"CALCULATE ( [Materials Received], {cy}, Receipts[Channel] = \"{ch_}\" )", 0.01)
    cy = f"'Date'[Year] = {y}"
    b.check(s, f"{y} issues, raw materials", c["raw_issued"], f"CALCULATE ( [Materials Issued], {cy}, 'Item'[ItemGroup] = \"Raw Materials\" )", 0.01)
    b.check(s, f"{y} issues, packaging", c["pack_issued"], f"CALCULATE ( [Materials Issued], {cy}, 'Item'[ItemGroup] = \"Packaging\" )", 0.01)
    b.check(s, f"{y} build", c["build"], f"CALCULATE ( [Materials Build], {cy} )", 0.01)
    for t_ in top:
        b.check(s, f"{y} build {t_['code']}", t_["amount"], f"CALCULATE ( [Materials Build], {cy}, 'Item'[ItemCode] = \"{t_['code']}\" )", 0.01)
    six = ", ".join(f"\"{t_['code']}\"" for t_ in top)
    b.check(s, "the six items' share of the build", round(c["share"], 6),
            f"DIVIDE ( CALCULATE ( [Materials Build], {cy}, 'Item'[ItemCode] IN {{ {six} }} ), CALCULATE ( [Materials Build], {cy} ) )",
            0.000005)
    b.check(s, f"{y} build, packaging", c["packaging"], f"CALCULATE ( [Materials Build], {cy}, 'Item'[ItemGroup] = \"Packaging\" )", 0.01)
    b.check(s, "opening materials (the opening entry, no item detail)", c["opening_materials"],
            f"CALCULATE ( [GL Amount], Account[AccountNumber] = 1045, GLEntry[VoucherNumber] = \"{b.ctx['r3']['entry']}\" )", 0.01)
    for yy, n, v in zip(d.years, c["short_counts"], c["short_values"]):
        b.check(s, f"{yy} shortfall requisitions", n, f"CALCULATE ( [Shortfall Requisitions], 'Date'[Year] = {yy} )", 0)
        b.check(s, f"{yy} shortfall requisitions, estimated", v,
                f"CALCULATE ( [Requisitioned Value], 'Date'[Year] = {yy}, Requisitions[Channel] = \"{SHORT}\" )", 0.01)
    for label, key, measure_, tol in [("pairs", "pairs", "Pairs", 0), ("repeated pairs", "repeated", "Repeated Pairs", 0),
                                      ("requisitions in repeated pairs", "in_repeated", "Requisitions in Repeated Pairs", 0),
                                      ("most requisitions for a pair", "most", "Most Requisitions for a Pair", 0),
                                      ("pairs matched to issues", "matched", "Pairs with Issues", 0),
                                      ("units requisitioned", "units", "Requisitioned Units", 0.05),
                                      ("estimated value", "estimated", "Pair Estimated Value", 0.01),
                                      ("units issued to the same pairs", "units_issued", "Issued Units", 0.05),
                                      ("issued at standard", "issued_cost", "Issued Cost", 0.01)]:
        b.check(s, label, c[key], f"[{measure_}]", tol)
    b.check(s, "pairs with nothing issued", c["unmatched"], "[Pairs] - [Pairs with Issues]", 0)
    claim(c["n_top"] == "one", "one pair has the most requisitions")
    top_pair = f"FILTER ( ShortfallPairs, ShortfallPairs[RequisitionCount] = {c['most']} )"
    b.check(s, "the pair with the most: work order", c["wo"], f"MAXX ( {top_pair}, ShortfallPairs[WorkOrderNumber] )")
    b.check(s, "the pair with the most: item", c["item"], f"MAXX ( {top_pair}, RELATED ( 'Item'[ItemCode] ) )")
    for label, k, column in (("first request", "first_request", "FirstRequest"), ("last request", "last_request", "LastRequest"),
                             ("work order due", "due", "DueDate"), ("work order completed", "completed", "CompletedDate")):
        b.check(s, f"the pair with the most: {label}", c[k], fmt_date(f"MAXX ( {top_pair}, ShortfallPairs[{column}] )"))
    months = rows("SELECT substr(r.RequestDate, 1, 7), COUNT(*) FROM PurchaseRequisition r JOIN WorkOrder w "
                  "ON w.WorkOrderNumber = ? JOIN Item i ON i.ItemCode = ? WHERE r.Justification = "
                  "'WO-COMPONENT-SHORTFALL | WO=' || w.WorkOrderID || ' | ITEM=' || i.ItemID GROUP BY 1", c["wo"], c["item"])
    claim(len(months) and max(n for _, n in months) <= 2, "the pair was requisitioned once or twice a month")
    just = (f"VAR J = MAXX ( {top_pair}, ShortfallPairs[Justification] ) VAR R = FILTER ( Requisitions, "
            "Requisitions[Justification] = J ) RETURN ")
    ms = "DISTINCT ( SELECTCOLUMNS ( R, \"RequestMonth\", FORMAT ( Requisitions[RequestDate], \"yyyy-mm\" ) ) )"
    b.check(s, "the pair with the most: months with a requisition", len(months), just + f"COUNTROWS ( {ms} )", 0)
    b.check(s, "the pair with the most: at most per month", max(n for _, n in months),
            just + f"MAXX ( {ms}, VAR Mo = [RequestMonth] RETURN COUNTROWS ( FILTER ( R, FORMAT ( Requisitions[RequestDate], "
            "\"yyyy-mm\" ) = Mo ) ) )", 0)
    b.check(s, "receipts from shortfall requisitions, all years", c["short_receipts"], "[Shortfall Receipts]", 0.01)
    b.check(s, "shortfall requisitions approved by the one approver", c["n_short"],
            f"CALCULATE ( [Shortfall Requisitions], Requisitions[ApprovedByEmployeeID] = {c['approver']} )", 0)
    b.check(s, "approvers of shortfall requisitions", 1,
            f"CALCULATE ( DISTINCTCOUNT ( Requisitions[ApprovedByEmployeeID] ), Requisitions[Channel] = \"{SHORT}\" )", 0)
    b.check(s, "the shortfall approver's title", c["approver_title"],
            f"CALCULATE ( MAX ( Requisitions[ApproverTitle] ), Requisitions[Channel] = \"{SHORT}\" )")
    b.check(s, "shortfall requisitions the approver requested", c["self_requested"],
            f"CALCULATE ( [Self-requested], Requisitions[Channel] = \"{SHORT}\" )", 0)
    raw_titles = rows(f"SELECT e.JobTitle, COUNT(*) FROM PurchaseRequisition r JOIN Employee e ON e.EmployeeID = "
                      f"r.RequestedByEmployeeID WHERE r.Justification LIKE 'WO-COMPONENT-SHORTFALL%' AND "
                      f"r.RequestedByEmployeeID <> ? GROUP BY 1", c["approver"])
    claim(sorted(n for _, n in raw_titles) == sorted(n for _, n in c["requester_titles"]), "the requester counts agree")
    for t_, n in raw_titles:
        b.check(s, f"shortfall requisitions requested by {t_}s", n,
                f"CALCULATE ( [Shortfall Requisitions], Requisitions[RequesterTitle] = \"{t_}\" )", 0)
    b.check(s, "supply-plan requisitions approved by the CFO", c["cfo_plan"],
            f"CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Channel] = \"{PLAN}\", "
            "Requisitions[ApproverTitle] = \"Chief Financial Officer\" )", 0)
    b.check(s, "supply-plan requisitions with no approver", c["no_plan"],
            f"CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Channel] = \"{PLAN}\", ISBLANK ( Requisitions[ApproverTitle] ) )", 0)
    full = {v: k for k, v in case4.SHORT_TITLES.items()}
    for t_, n in c["other_app"]:
        b.check(s, f"capital requests approved by the {t_}", n,
                f"CALCULATE ( COUNTROWS ( Requisitions ), Requisitions[Channel] = \"{OTHER}\", "
                f"Requisitions[ApproverTitle] = \"{full.get(t_, t_)}\" )", 0)
    b.check(s, f"{y} materials issued in the twelve months", c["ttm"], f"CALCULATE ( [Issues TTM], {cy} )", 0.01)
    b.check(s, "Target Days rows", 114, f"COUNTROWS ( '{TD}' )", 0)
    b.check(s, "the slider's default (the policy target)", c3["raw"], f"[{TD} Value]", 0)
    for w in wi:
        f_ = f"{cy}, '{TD}'[{TD}] = {w['days']}"
        b.check(s, f"{w['days']} days: allowed", w["allowed"], f"CALCULATE ( [Allowed Materials], {f_} )", 0.01)
        b.check(s, f"{w['days']} days: excess", w["excess"], f"CALCULATE ( [Excess Materials], {f_} )", 0.01)
        b.check(s, f"{w['days']} days: months of issues (2 decimals)", w["months"],
                f"CALCULATE ( [Months of Issues in Excess], {f_} )", 0.0051)
    b.check(s, f"the excess at {wi[-1]['days']} days over the fall in cash (rounded)", round(wi[-1]["excess"] / fall),
            f"ROUND ( DIVIDE ( CALCULATE ( [Excess Materials], {cy}, '{TD}'[{TD}] = {wi[-1]['days']} ), "
            f"- CALCULATE ( [Change in Cash], {cy} ) ), 0 )", 0)
    b.check(s, f"finished goods at {FG(c)} days of shipments", c["fg_target"], f"CALCULATE ( [Finished Goods at Target], {cy} )", 0.01)
    b.check(s, "finished goods at the year-end", c["fg"], f"CALCULATE ( [Finished Goods], {cy} )", 0.01)
    b.check(s, "approved, unordered requisitions", c["n_never"], "[Open Requisitions]", 0)
    b.check(s, "... all of them work-order shortfall requisitions", c["never_short"],
            f"CALCULATE ( [Open Requisitions], Requisitions[Channel] = \"{SHORT}\" )", 0)
    b.check(s, "... their estimated value", c["never_value"], "[Open Requisition Value]", 0.01)
    b.check(s, "order lines not fully received at the year-end", c["open_lines"], "[Open Order Lines]", 0)
    b.check(s, "... their value", c["open_value"], "[Open Order Value]", 0.01)
    b.check(s, "... of which materials", c["open_materials"],
            f"CALCULATE ( [Open Order Value], OrderLines[ItemGroup] IN {{ \"Raw Materials\", \"Packaging\" }} )", 0.01)
    for yy, (n, v) in zip(d.years, c["late"]):
        f_ = f"'Date'[Year] = {yy}, Requisitions[Channel] = \"{SHORT}\""
        b.check(s, f"{yy} shortfall requisitions after their work order's due date (optional)", n,
                f"CALCULATE ( [Late Shortfall Requisitions], {f_} )", 0)
        b.check(s, f"{yy} ... estimated (optional)", v, f"CALCULATE ( [Late Shortfall Value], {f_} )", 0.01)


def FG(c: dict) -> int:
    return case4.FG_TARGET


# --- Requirement 5: the roll-forward, the reconciliations, the findings -------------------------------------------

def r5(b: Build) -> None:
    d, c, c1 = b.d, b.ctx["r5"], b.ctx["r1"]
    y, P, F = d.C, d.P, d.F
    R = "Reconciliation"
    for name, dax, f, desc in [
        ("Open Receivables", "CALCULATE ( SUM ( ARInvoices[OpenBalance] ), ARInvoices[OpenBalance] > 0, REMOVEFILTERS ( 'Date' ) )",
         MONEY, "The positive open balances of the sales invoices at the end of the fiscal year (Exercise 16.1)."),
        ("Open Receivable Invoices", "CALCULATE ( COUNTROWS ( ARInvoices ), ARInvoices[OpenBalance] > 0, REMOVEFILTERS ( 'Date' ) )",
         COUNT, "The sales invoices with a positive open balance at the end of the fiscal year."),
        ("Credit Balances", "CALCULATE ( SUM ( ARInvoices[OpenBalance] ), ARInvoices[OpenBalance] < 0, REMOVEFILTERS ( 'Date' ) )",
         MONEY, "Invoices whose applications and credits exceed their total: credit memos on paid invoices."),
        ("Credit Balance Invoices", "CALCULATE ( COUNTROWS ( ARInvoices ), ARInvoices[OpenBalance] < 0, REMOVEFILTERS ( 'Date' ) )",
         COUNT, "The number of invoices with a credit balance."),
        ("Receivables Difference", "[Receivables] - [Open Receivables]", MONEY,
         "Account 1020 less the open invoices: what the subledger does not support."),
        ("Open Payables", "CALCULATE ( SUM ( APInvoices[OpenBalance] ), REMOVEFILTERS ( 'Date' ) )", MONEY,
         "The open balances of the supplier invoices received by the end of the fiscal year (Exercise 8.2)."),
        ("Open Payable Invoices", "CALCULATE ( COUNTROWS ( APInvoices ), REMOVEFILTERS ( 'Date' ) )", COUNT,
         "The supplier invoices received and not fully paid at the end of the fiscal year."),
        ("Payables Difference", "[Payables] - [Open Payables]", MONEY,
         "Account 2010 less the open supplier invoices."),
        ("Past Due Payables", "CALCULATE ( [Open Payables], APInvoices[DaysPastDue] > 0 )", MONEY,
         "Open supplier invoices past their due date at the end of the fiscal year."),
        ("Past Due Share without Notes", "DIVIDE (\n    CALCULATE ( [Past Due Payables], APInvoices[MovedToNotes] = FALSE () ),\n"
         "    CALCULATE ( [Open Payables], APInvoices[MovedToNotes] = FALSE () )\n)", PCT,
         "The past-due share of the open payables, without the invoices the ledger moved to notes payable."),
        ("Billing by Invoice Date", "SUM ( ARInvoices[GrandTotal] )", MONEY, "The sales invoices' GrandTotal by invoice date."),
        ("Billing in Ledger", 'CALCULATE ( SUM ( GLEntry[Debit] ), Account[AccountNumber] = 1020, GLEntry[SourceDocumentType] = "SalesInvoice" )',
         MONEY, "SalesInvoice debits to 1020 by posting date."),
        ("Billing Difference", "[Billing by Invoice Date] - [Billing in Ledger]", MONEY,
         "Invoices dated in the period less what the ledger billed in it: the cutoff findings."),
        ("Sales Tax Credits", "CALCULATE ( SUM ( GLEntry[Credit] ), Account[AccountNumber] = 2050 )", MONEY, "Credits to 2050."),
        ("Sales Tax Debits", "CALCULATE ( SUM ( GLEntry[Debit] ), Account[AccountNumber] = 2050 )", MONEY, "Debits to 2050."),
        ("Findings Amount", "SUM ( Findings[Amount] )", MONEY, "The amounts of the findings recorded in the Findings table."),
        ("Receivables Findings", 'CALCULATE ( [Findings Amount], Findings[Reconciles] = "Receivables" )', MONEY,
         "The findings recorded as reconciling items of receivables."),
        ("Payables Findings", 'CALCULATE ( [Findings Amount], Findings[Reconciles] = "Payables" )', MONEY,
         "The findings recorded as reconciling items of payables."),
        ("Unexplained Receivables", "[Receivables Difference] - [Receivables Findings]", MONEY,
         "The receivables difference the findings do not explain (zero when reconciled)."),
        ("Unexplained Payables", "[Payables Difference] - [Payables Findings]", MONEY,
         "The payables difference the findings do not explain (zero when reconciled).")]:
        b.measure(R, name, dax, f, desc)
    # the Findings table (Enter data): account, finding, amount (its effect on the ledger less the subledger where it
    # reconciles a difference), disposition in Chapter 8's terms, and the difference it reconciles
    cap = c["capital"]
    findings = [
        ["1020", f"Opening receivables with no invoice ({c['entry']})", c["opening_ar"], "Follow up", "Receivables"],
        ["2010", f"Opening payables with no invoice ({c['entry']})", c["opening_ap"], "Follow up", "Payables"],
        ["2010", "Invoices moved to notes payable still open in the subledger (PI " +
         " and ".join(str(x["id"]) for x in cap) + "); close them against the notes", -c["notes_total"], "Expected", "Payables"],
        ["2050", "No remittance of the sales tax recorded", c["tax_balance"], "Follow up", ""],
        ["2110", f"Current portion of the notes classified as long-term (due {d.N})", c["current_portion"], "Misstatement", ""],
        ["1010 and 2010", "Supplier payments posted after Data Through", c["after_amount"], "Expected", ""],
        ["2030", "Payroll accrual not recorded at the year-end (Part III case)", c["accrual"], "Misstatement", ""]]
    b.model.add(entered_table("Findings", [("Account", "string"), ("Finding", "string"), ("Amount", "double"),
                                           ("Disposition", "string"), ("Reconciles", "string")],
                              [[a, f_, f"{amt:.2f}", disp, rec] for a, f_, amt, disp, rec in findings], fmts={"Amount": MONEY}))
    b.model.query_order.append("Findings")

    # the Reconciliations page
    yr, num = col("Date", "Year"), col("Account", "AccountNumber")
    page = b.report.add(Page("reconciliations", "Reconciliations", height=1200))
    page.add(Visual("rollForward", "pivotTable", 20, 20, 1240, 300, {
        "Rows": [num], "Columns": [col("GLEntry", "SourceDocumentType")], "Values": [M("Balance")]},
        title=f"Working-capital accounts at the end of fiscal {y}, by source document",
        filters=[keep("rfYear", yr, [y]), keep("rfAccounts", num, [int(n) for n in ROLL])]))
    page.add(card("reconCards", 20, 340, 820, 110, [M("Receivables"), M("Open Receivables"), M("Receivables Difference"),
                                                    M("Payables"), M("Open Payables"), M("Payables Difference")],
                  units_none=True, title=f"Ledger against open items at the end of fiscal {y}", filters=[keep("rcYear", yr, [y])]))
    page.add(Visual("billing", "tableEx", 20, 470, 400, 160, {"Values": [
        yr, M("Billing by Invoice Date"), M("Billing in Ledger"), M("Billing Difference")]},
        title="Billing by invoice date against the ledger", filters=[keep("blYears", yr, d.years)]))
    bucket = col("APInvoices", "Bucket")
    page.add(Visual("aging", "tableEx", 440, 470, 400, 200, {"Values": [bucket, M("Open Payables"), M("Open Payable Invoices")]},
                    title="Open payables aged, without the invoices moved to notes",
                    filters=[keep("agNotes", col("APInvoices", "MovedToNotes"), [False])],
                    sort=[(col("APInvoices", "BucketOrder"), "Ascending")]))
    page.add(Visual("salesTax", "pivotTable", 20, 650, 400, 160, {"Rows": [col("GLEntry", "SourceDocumentType")],
                                                                  "Columns": [yr], "Values": [M("Sales Tax Credits"), M("Sales Tax Debits")]},
                    title="Account 2050 by source and year", filters=[keep("stYears", yr, d.years)]))
    page.add(Visual("findings", "tableEx", 20, 830, 820, 300, {"Values": [
        col("Findings", "Account"), col("Findings", "Finding"), col("Findings", "Amount"), col("Findings", "Disposition"),
        col("Findings", "Reconciles")]}, title="Findings"))
    roll = c["roll"]
    bill = c["billing"]
    page.add(answer("reconAnswer", 860, 340, 400, 840, [
        f"Roll-forward at {year_end(y)}: " + "; ".join(
            f"{n} " + ", ".join(f"{k} {money(v)}" for k, v in roll[n]["parts"].items()) + f" ({money(roll[n]['total'])})"
            for n in ROLL) + ". The JournalEntry parts are the balances no subledger document supports: the opening "
        "entry's lines (and, in 2010, the two reclassifications to notes).",
        f"Receivables: {c['n_ar']:,} open invoices, {money(c['open_ar'])}, against 1020 {money(roll['1020']['total'])}; "
        f"the difference, {money(c['ar_diff'])}, is the opening line of {c['entry']}. The {c['n_neg']} negative balances "
        f"({money(c['neg'])}) are credit memos on paid invoices, credited to 2060 and refunded, except "
        f"{c['waiting']['n']} ({money(c['waiting']['amount'])}) not yet refunded at the year-end.",
        f"Payables: {c['n_ap']:,} invoices received and unpaid, {money(c['ap_total'])}, against 2010 "
        f"{money(-roll['2010']['total'])}; the difference, {money(c['ap_diff'])}, is the opening payables "
        f"({money(c['opening_ap'])}) less the {money(c['notes_total'])} of PI " + " and PI ".join(str(x["id"]) for x in cap) +
        ", which the ledger moved to notes payable but the subledger still shows open (past due since " +
        " and ".join(x["due"] for x in cap) + f"). Past due: {money(c['past_due'])} with them, {money(c['past_due_x'])} of "
        f"{money(c['total_x'])} ({pct(c['past_due_share'])}) without them.",
        "Billing by invoice date less the ledger: " + "; ".join(f"{x['year']} {signed(x['diff'])}" for x in bill) +
        f". Invoices dated in one year and posted on 1 January of the next; only {c['shipped']} shipped in "
        f"{c['shipped_year']} (Chapter 6's cutoff error), so the other dates are wrong, not the ledger.",
        "Sales tax: 2050 receives credits only from SalesInvoice (" + ", ".join(money(v) for v in c["tax"]) +
        ", equal to the invoices' TaxAmount) and debits only from CreditMemo; no payment and no journal entry ever posts "
        "to it. Evidence outside the database: the sales tax returns filed, the tax authority's account, the bank "
        "statements, and a bank reconciliation.",
        "Each finding carries a disposition in Chapter 8's terms. The Tests tab shows both differences equal their "
        f"findings to the cent, the bridge equal to the change in cash in {P} and {y}, {c['after_rows']} rows after "
        f"Data Through, and every measure blank in {d.N}."], size=9))
    page.expect = ["SourceDocumentType", money(roll["1020"]["total"]), money(c["ar_diff"]), money(c["ap_diff"]),
                   "Misstatement", "Over 90 days", "Model answer"]

    # Tests 4 and 5
    b.add_test("Test 4: each reconciliation difference equals the findings recorded for it",
               "EVALUATE\nCALCULATETABLE (\n    ROW (\n        \"Receivables Difference\", ROUND ( [Receivables Difference], 2 ),\n"
               "        \"Receivables Findings\", ROUND ( [Receivables Findings], 2 ),\n"
               "        \"Payables Difference\", ROUND ( [Payables Difference], 2 ),\n"
               "        \"Payables Findings\", ROUND ( [Payables Findings], 2 )\n    ),\n    'Date'[Year] = " + str(y) + "\n)")
    tests = " || ".join(f"NOT ISBLANK ( [{n}] )" for n in GUARDED)
    later = ("VAR ThroughDate = [Data Through]\nVAR LaterQuarters =\n    FILTER ( VALUES ( 'Date'[YearQuarter] ), "
             "CALCULATE ( MIN ( 'Date'[Date] ) ) > ThroughDate )\nRETURN\n")
    b.add_test("Test 5: every working-capital measure is blank after Data Through",
               "EVALUATE\n" + later + "    ROW (\n        \"Quarters after Data Through\", COUNTROWS ( LaterQuarters ),\n"
               f"        \"Quarters with a value\", COUNTROWS ( FILTER ( LaterQuarters, {tests} ) ) + 0\n    )")

    s = "Requirement 5"
    for n in ROLL:
        for src, v in roll[n]["parts"].items():
            b.check(s, f"{n} at {year_end(y)}: {src}", v,
                    f"CALCULATE ( [Balance], 'Date'[Year] = {y}, Account[AccountNumber] = {n}, GLEntry[SourceDocumentType] = \"{src}\" )", 0.01)
        b.check(s, f"{n} at {year_end(y)}", roll[n]["total"], f"CALCULATE ( [Balance], 'Date'[Year] = {y}, Account[AccountNumber] = {n} )", 0.01)
        b.check(s, f"{n}: sources", len(roll[n]["parts"]),
                f"CALCULATE ( COUNTROWS ( SUMMARIZE ( GLEntry, GLEntry[SourceDocumentType] ) ), Account[AccountNumber] = {n}, "
                f"GLEntry[PostingDate] <= {ddate(year_end(y))} )", 0)
    cy = f"'Date'[Year] = {y}"
    b.check(s, "open receivable invoices", c["n_ar"], "[Open Receivable Invoices]", 0)
    b.check(s, "open receivables", c["open_ar"], "[Open Receivables]", 0.01)
    b.check(s, "invoices with a credit balance", c["n_neg"], "[Credit Balance Invoices]", 0)
    b.check(s, "their total", c["neg"], "[Credit Balances]", 0.01)
    b.check(s, f"2060 at the year-end (credits awaiting a refund)", round(c["waiting"]["amount"], 2),
            f"- CALCULATE ( [Balance], {cy}, Account[AccountNumber] = 2060 )", 0.01)
    b.check(s, "receivables difference", c["ar_diff"], f"CALCULATE ( [Receivables Difference], {cy} )", 0.01)
    b.check(s, f"... the opening line of {c['entry']}", c["opening_ar"],
            f"CALCULATE ( [GL Amount], Account[AccountNumber] = 1020, GLEntry[VoucherNumber] = \"{c['entry']}\" )", 0.01)
    b.check(s, "open payable invoices", c["n_ap"], "[Open Payable Invoices]", 0)
    b.check(s, "open payables", c["ap_total"], "[Open Payables]", 0.01)
    b.check(s, "payables difference", c["ap_diff"], f"CALCULATE ( [Payables Difference], {cy} )", 0.01)
    b.check(s, f"... the opening payables line of {c['entry']}", c["opening_ap"],
            f"- CALCULATE ( [GL Amount], Account[AccountNumber] = 2010, GLEntry[VoucherNumber] = \"{c['entry']}\" )", 0.01)
    ids = ", ".join(str(x["id"]) for x in cap)
    b.check(s, "the note invoices still open in the subledger", c["notes_total"],
            f"CALCULATE ( [Open Payables], APInvoices[PurchaseInvoiceID] IN {{ {ids} }} )", 0.01)
    b.check(s, "... flagged MovedToNotes", len(cap), "CALCULATE ( [Open Payable Invoices], APInvoices[MovedToNotes] = TRUE () )", 0)
    for x in cap:
        b.check(s, f"PI {x['id']} due date", x["due"],
                fmt_date(f"CALCULATE ( MIN ( APInvoices[DueDate] ), APInvoices[PurchaseInvoiceID] = {x['id']} )"))
        b.check(s, f"{x['entry']}: PI {x['id']} moved to 2110", x["amount"],
                f"CALCULATE ( SUM ( GLEntry[Credit] ), GLEntry[VoucherNumber] = \"{x['entry']}\", Account[AccountNumber] = 2110 )", 0.01)
    b.check(s, "past due payables", c["past_due"], "[Past Due Payables]", 0.01)
    b.check(s, "past due without the note invoices", c["past_due_x"],
            "CALCULATE ( [Past Due Payables], APInvoices[MovedToNotes] = FALSE () )", 0.01)
    b.check(s, "open payables without the note invoices", c["total_x"],
            "CALCULATE ( [Open Payables], APInvoices[MovedToNotes] = FALSE () )", 0.01)
    b.check(s, "past due share without them", round(c["past_due_share"], 6), "[Past Due Share without Notes]", 0.000005)
    for x in bill:
        b.check(s, f"{x['year']} billing by invoice date less the ledger", x["diff"],
                f"CALCULATE ( [Billing Difference], 'Date'[Year] = {x['year']} )", 0.01)
    for yy in (F, P):
        inv = case4.cross_year(d, yy)
        b.check(s, f"invoices dated in {yy} and posted in {yy + 1}", ", ".join(i["number"] for i in inv),
                f"CONCATENATEX ( FILTER ( ARInvoices, YEAR ( ARInvoices[InvoiceDate] ) = {yy} && "
                f"LEFT ( ARInvoices[InvoiceNumber], 7 ) <> \"SI-{yy}\" ), ARInvoices[InvoiceNumber], \", \", "
                "ARInvoices[InvoiceNumber], ASC )")
    for yy, v in zip(d.years, c["tax"]):
        b.check(s, f"{yy} sales tax credits from SalesInvoice", v,
                f"CALCULATE ( [Sales Tax Credits], 'Date'[Year] = {yy}, GLEntry[SourceDocumentType] = \"SalesInvoice\" )", 0.01)
    b.check(s, "sources that post to 2050", "CreditMemo, SalesInvoice",
            "CONCATENATEX ( CALCULATETABLE ( VALUES ( GLEntry[SourceDocumentType] ), Account[AccountNumber] = 2050 ), "
            "GLEntry[SourceDocumentType], \", \", GLEntry[SourceDocumentType], ASC )")
    b.check(s, "debits to 2050 from SalesInvoice", 0, "CALCULATE ( [Sales Tax Debits], GLEntry[SourceDocumentType] = \"SalesInvoice\" ) + 0", 0.01)
    b.check(s, "credits to 2050 from CreditMemo", 0, "CALCULATE ( [Sales Tax Credits], GLEntry[SourceDocumentType] = \"CreditMemo\" ) + 0", 0.01)
    b.check(s, "the invoices' TaxAmount equals the SalesInvoice credits to 2050", -roll["2050"]["parts"]["SalesInvoice"],
            "CALCULATE ( SUM ( ARInvoices[TaxAmount] ), REMOVEFILTERS ( 'Date' ) )", 0.01)
    b.check(s, f"sales tax payable at {year_end(y)}", c["tax_balance"], f"CALCULATE ( [Sales Tax Payable], {cy} )", 0.01)
    b.check(s, "Findings rows", len(findings), "COUNTROWS ( Findings )", 0)
    for a, f_, amt, disp, rec in findings:
        b.check(s, f"finding: {f_[:60]}", round(amt, 2), f"CALCULATE ( [Findings Amount], Findings[Finding] = \"{f_}\" )", 0.005)
    b.check(s, "Test 4: the receivables difference equals its findings", 0, f"CALCULATE ( [Unexplained Receivables], {cy} )", 0.005)
    b.check(s, "Test 4: the payables difference equals its findings", 0, f"CALCULATE ( [Unexplained Payables], {cy} )", 0.005)
    for yy in (P, y):
        b.check(s, f"Test 3: the bridge equals the change in cash, {yy}", 0,
                f"CALCULATE ( [Cash Effect] - [Change in Cash], 'Date'[Year] = {yy} )", 0.005)
    b.check(s, "Test 2: rows after Data Through", c["after_rows"], "[Rows after Data Through]", 0)
    b.check(s, "Test 2: their debits", c["after_amount"], "[Postings after Data Through]", 0.01)
    b.check(s, "Test 5: quarters after Data Through", 4,
            later.replace("\n", " ") + "COUNTROWS ( LaterQuarters )", 0)
    b.check(s, "Test 5: quarters after Data Through with a value", 0,
            later.replace("\n", " ") + f"COUNTROWS ( FILTER ( LaterQuarters, {tests} ) ) + 0", 0)


def year_end(y: int) -> str:
    return f"{y}-12-31"


# --- Requirement 6: the memo ---------------------------------------------------------------------------------------

def r6(b: Build) -> None:
    d = b.d
    c1, c2, c3, c4, c5 = (b.ctx[k] for k in ("r1", "r2", "r3", "r4", "r5"))
    y, P = d.C, d.P
    cur, rc = c2["cur"], c2["rc"]
    last, firstq = c3["qs"][-1], c3["qs"][0]
    wi = c4["whatif"]
    page = b.report.add(Page("memo", "Memo", height=1400))
    left = [
        "To: the Controller. From: the staff accountant. Subject: where the cash went in fiscal " + str(y) +
        f" (data through {c1['thru']}).",
        ("Financial reporting", True),
        f"The profit was real but went into inventories. Net income was {money(cur['net_income'])}, yet cash fell "
        f"{money(-cur['cash'])}, from {money(c2['cash_from'])} to {money(c2['cash_to'])}, after rising "
        f"{money(c2['pri']['cash'])} in {P}. The inventories absorbed {money(-cur['inventories'])}, while unremitted "
        f"sales tax ({signed(cur['sales_tax'])}) and growing payables ({signed(cur['payables'])}) held cash up.",
        f"Restated by the indirect method, operating activities used {money(-rc['operating'])}, investing used none, "
        f"and financing used {money(-rc['financing'])} in principal payments; {money(rc['notes_financed'])} of "
        f"equipment acquired by a note ({c2['reclass']}) and the disposal {c2['disp']['entry']} moved no cash and are "
        f"disclosed apart. Without the unremitted tax, operating cash flow would have been {money(c2['without_tax'])}.",
        f"The balance sheet needs three things. Sales tax payable of {money(c2['tax_c'])} has no remittance recorded "
        f"in the ledger, so the cash on the balance sheet overstates what the company can use: net of it, cash was "
        f"{money(c2['net'][-1])}. {money(c2['due_next'])} of the notes is due in {d.N} but classified as long-term; "
        f"reclassified, it lowers working capital. And the opening receivables ({money(c5['opening_ar'])}) and "
        f"payables ({money(c5['opening_ap'])}) are balances that no document supports.",
        ("Managerial accounting", True),
        f"Receivables and payables barely moved (DSO {firstq['dso']:.1f} to {last['dso']:.1f} days; DPO without the "
        f"opening line {firstq['dpo_x']:.1f} to {last['dpo_x']:.1f}). The cash conversion cycle grew from "
        f"{firstq['ccc']:.1f} to {last['ccc']:.1f} days entirely through inventory: materials stood at "
        f"{last['mat']:.1f} days of issues against a policy target of {c3['raw']}, and finished goods at "
        f"{last['fg']:.1f} days.",
        f"The build came through the work-order shortfall channel: receipts from shortfall requisitions rose to "
        f"{money(c4['by_year'][-1]['short'][1])} in {y} while issues held near {round(c4['ttm'] / 1e6):.0f} million. "
        f"Requisitions were repeated for one work order and item ({c4['repeated']:,} of {c4['pairs']:,} pairs, up to "
        f"{c4['most']} for {c4['wo']} and {c4['item']}), and {c4['units']:,.1f} units were requisitioned against "
        f"{c4['units_issued']:,.1f} issued to the same pairs.",
        f"A 2027 target: at {wi[0]['days']} days the materials allowed are {money(wi[0]['allowed'])} and the excess "
        f"{money(wi[0]['excess'])} ({wi[0]['months']:.2f} months of issues); even at {wi[-1]['days']} days the excess "
        f"({money(wi[-1]['excess'])}) is about {c4['multiple']} times the year's fall in cash. The estimate assumes "
        "issues continue at the year's rate and the stock is usable; it leaves out the finished goods, the "
        f"{c4['n_never']} approved, unordered requisitions ({money(c4['never_value'])}), and the open orders "
        f"({money(c4['open_value'])}). The cash comes back only as purchases fall below use, over 2027 and beyond."]
    right = [
        ("Auditing", True),
        f"Receivables reconcile to the open invoices except the {money(c5['ar_diff'])} opening line; payables except "
        f"{money(c5['ap_diff'])}, the opening payables less the two note invoices still open in the subledger. "
        "Dispositions: the opening balances, follow up (supporting schedules from the prior system and confirmations); "
        "the note invoices, expected (close them against the notes); the sales tax, follow up (the returns filed, the "
        "tax authority's account, the bank statements and reconciliation); the current portion and the unrecorded "
        f"payroll accrual ({money(c5['accrual'])}), misstatements; the supplier payments after Data Through, expected.",
        f"Controls over requisitions: one manager, the {c4['approver_title']}, approved every shortfall requisition, "
        f"{c4['self_requested']} of them his or her own, with no check against stock on hand or open orders.",
        "Controls over the report: the Tests tab and the Data Through card must be rerun on every refresh, the "
        "Validation totals must agree with the ledger, and changes to the file should be reviewed before the committee "
        "relies on it each quarter.",
        ("Recommendation", True),
        "Settle the sales tax position first, because it decides how much of the cash is available. Check every "
        "shortfall requisition against stock on hand and open orders before it is converted, route it through the "
        f"supply plan with an approver outside production, and review the {c4['n_never']} open requisitions. Approve "
        "2027 inventory targets, since the policies ended with " + str(y) + ", and a materials purchase budget that "
        "draws the stock down toward them. Present the restated cash flow with its noncash disclosure and reclassify "
        "the current portion of the notes. Follow up the unsupported opening balances with Chapter 8's findings, and "
        "keep the Tests tab and the Data Through check for every refresh of the report.",
        "A question, not a conclusion: whether materials of more than a year of issues are still worth their standard "
        "cost (ASC Topic 330)."]
    page.add(answer("memoLeft", 20, 20, 610, 1360, left, size=10, title="Model answer: decision memo"))
    page.add(textbox("memoRight", 650, 20, 610, 1360, right, size=10))
    page.expect = ["Model answer: decision memo", "Recommendation", money(cur["net_income"]), money(c2["tax_c"])]
    s = "Requirement 6"
    b.check(s, "materials on hand exceed a year of issues", round(last["mat_balance"] - last["issues"], 2),
            f"CALCULATE ( [Materials] - [Issues TTM], 'Date'[Year] = {y} )", 0.01)
    b.check(s, "the inventories absorbed more than the year's net income", round(-cur["inventories"] - cur["net_income"], 2),
            f"CALCULATE ( - CALCULATE ( [Cash Effect], Account[Step] = \"Inventories\" ) - [Net Income], 'Date'[Year] = {y} )", 0.01)
    b.check(s, "open requisitions to review", b.ctx["r6"]["n_never"], "[Open Requisitions]", 0)


EXERCISES = [("Requirement 1", r1), ("Requirement 2", r2), ("Requirement 3", r3), ("Requirement 4", r4),
             ("Requirement 5", r5), ("Requirement 6", r6)]
