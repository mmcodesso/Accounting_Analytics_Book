"""Chapter 1's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 1's exercises are conceptual (the reader browses CharlesRiver.xlsx), so the contexts do two jobs:

- they supply the values a model answer can quote (row counts of the worksheets a student opens, the traced sale's path,
  the facts of the journal entry data), and
- they check, with claim(), every table and column the guide names and every statement about the data that another
  dataset could falsify, so a roll or a schema change flags the wording instead of leaving it stale.

The tables and columns written in a template as plain names are the ones listed in the SCHEMA dictionaries below.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

from guide_contexts import context

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "01-role-of-analytics"
DECK = REPO / "slides" / "chapter-01" / "index.qmd"
FINISHED_GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories"]      # Tutorial 1.1, Step 4
TUTORIAL_SOURCE_TYPES = ["SalesInvoice", "Shipment", "PurchaseInvoice", "PayrollPayment", "JournalEntry"]  # Step 6


# --- helpers -------------------------------------------------------------------------------------------------------

def and_join(items) -> str:
    items = [str(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    return items[0] + " and " + items[1] if len(items) == 2 else ", ".join(items[:-1]) + ", and " + items[-1]


def schema(d, claim, spec: dict[str, list[str]]) -> dict[str, list[str]]:
    """The columns of each table the guide names; a claim fails when a table or a named column is missing."""
    have = {}
    for table, names in spec.items():
        cols = [r[1] for r in d.q(f"PRAGMA table_info({table})")]
        have[table] = cols
        missing = [n for n in names if n not in cols]
        claim(bool(cols) and not missing, f"{table} has the columns the guide names"
              + (f" (missing: {', '.join(missing)})" if cols else " (the table does not exist)"))
    return have


def rows_of(d, tables: list[str]) -> dict[str, int]:
    return {t: d.one(f"SELECT COUNT(*) FROM {t}") for t in tables}


def table_groups() -> list[tuple[str, list[str]]]:
    """Chapter 1's Table 1.3: each table group with its key tables, read from the chapter's text."""
    out, inside = [], False
    for line in (CHAPTER / "chapter.qmd").read_text(encoding="utf-8").splitlines():
        if line.startswith("| Table Group |"):
            inside = True
            continue
        if inside:
            if not line.startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells[0].startswith("---"):
                out.append((cells[0], [t.strip() for t in cells[1].split(",")]))
    return out


def in_group(claim, expected: dict[str, str]) -> None:
    """Claims that each table is a key table of the group the guide puts it in, as Table 1.3 of the chapter says."""
    found = {t: g for g, tables in table_groups() for t in tables}
    wrong = {t: found.get(t) for t, g in expected.items() if not (found.get(t) or "").startswith(g)}
    claim(not wrong, f"Table 1.3 places the tables where the guide does (differs: {wrong})")


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise \d+\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


def trace_ids(d) -> dict:
    import visible
    return visible.trace(d)


# --- the chapter note and Tutorial 1.1 ---------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "Customer": ["CustomerID", "CustomerName", "CustomerSegment", "Region", "CreditLimit", "PaymentTerms"],
    "SalesOrder": ["SalesOrderID", "CustomerID", "OrderDate", "RequestedDeliveryDate", "SalesRepEmployeeID", "Status"],
    "Item": ["ItemID", "ItemName", "ItemGroup", "SupplyMode", "StandardCost", "ListPrice"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "ParentAccountID"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "SourceDocumentType", "SourceDocumentID",
                "SourceLineID", "CostCenterID"],
    "WorkOrder": ["ItemID", "PlannedQuantity", "ReleasedDate", "DueDate", "CompletedDate", "Status"],
    "PayrollRegister": ["GrossPay", "EmployeeWithholdings", "EmployerPayrollTax", "EmployerBenefits", "NetPay"],
}


@context("ch01.chapter")
def chapter(d, claim):
    schema(d, claim, CHAPTER_SCHEMA)
    tables = [r[0] for r in d.q("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    groups = table_groups()
    claim(len(groups) > 1, "Table 1.3 of the chapter lists the table groups")
    missing = [t for _, key in groups for t in key if t not in tables]
    claim(not missing, f"every key table of Table 1.3 exists in the database (missing: {', '.join(missing)})")

    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType IS NULL OR SourceDocumentID IS NULL") == 0,
          "every ledger row names the type and the key of its source document")
    segments = [r[0] for r in d.q("SELECT CustomerSegment FROM Customer GROUP BY 1 ORDER BY COUNT(*) DESC")]
    claim(set(segments) == {"Wholesale", "Small Business", "Design Trade", "Strategic", "Design Services"},
          "the customer segments are the five that Tutorial 1.1 Step 2 names")
    finished = [r[0] for r in d.q("SELECT ItemGroup FROM Item WHERE ItemType = 'Finished Good' GROUP BY 1")]
    claim(sorted(finished) == sorted(FINISHED_GROUPS), "the finished-goods item groups are Furniture, Lighting, Textiles and Accessories")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE ItemType = 'Finished Good' AND (ListPrice IS NULL OR ListPrice <= 0)") == 0,
          "every finished good has a list price")
    other = [r[0] for r in d.q("SELECT ItemGroup FROM Item WHERE ItemType <> 'Finished Good' GROUP BY 1 ORDER BY 1")]
    claim(sorted(other) == ["Capex", "Packaging", "Raw Materials", "Services"],
          "the other item groups are Services, Raw Materials, Packaging and Capex, as Step 4 says")
    modes = [r[0] for r in d.q("SELECT SupplyMode FROM Item GROUP BY 1 ORDER BY 1")]
    claim(modes == ["Manufactured", "Purchased"], "SupplyMode is Purchased or Manufactured")
    types = [r[0] for r in d.q("SELECT AccountType FROM Account GROUP BY 1 ORDER BY 1")]
    claim(types == ["Asset", "Equity", "Expense", "Liability", "Revenue"], "AccountType has the five classes of Step 5")
    source_types = [r[0] for r in d.q("SELECT SourceDocumentType FROM GLEntry GROUP BY 1 ORDER BY COUNT(*) DESC")]
    claim(all(t in source_types for t in TUTORIAL_SOURCE_TYPES), "the SourceDocumentType filter list shows the types Step 6 names")
    gl_rows = d.one("SELECT COUNT(*) FROM GLEntry")
    je_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    sheets = rows_of(d, ["Customer", "SalesOrder", "Item", "Account", "WorkOrder", "PayrollRegister"])
    largest = d.q("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
    sizes = sorted(((d.one(f"SELECT COUNT(*) FROM {t[0]}"), t[0]) for t in largest), reverse=True)
    claim(sizes[0][1] == "GLEntry", "GLEntry is the largest worksheet, so it is the one that opens and filters slowly")
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    trace = trace_ids(d)
    claim(trace["id.trace.exact"], "the traced sale of Figure 1.6 exists exactly as the chapter tells it")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType IN ('SalesOrder', 'SalesOrderLine')") == 0,
          "a sales order and its lines post nothing to the ledger")
    return dict(
        n_tables=len(tables), n_groups=len(groups), groups=groups, sheets=sheets, gl_rows=gl_rows,
        je_rows=je_rows, je_share=je_rows / gl_rows, segments=and_join(segments), n_segments=len(segments),
        finished=and_join(FINISHED_GROUPS), other_groups=and_join(["Services", "Raw Materials", "Packaging", "Capex"]),
        n_item_groups=len(finished) + len(other), modes=and_join(modes), types=and_join(t.lower() for t in types),
        n_source_types=len(source_types), tutorial_types=and_join(TUTORIAL_SOURCE_TYPES),
        n_questions=len(re.findall(r"^\*\*\d+\.\*\*", (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8"), re.M)),
        n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(),
        trace_invoice=trace["id.trace.invoice"], trace_order=trace["id.trace.order"])


# --- Exercise 1.1: mapping table groups to the financial reporting cycle -----------------------------------------------

EX1_SCHEMA = {
    "SalesInvoice": ["InvoiceNumber", "InvoiceDate", "DueDate", "CustomerID", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal", "Status"],
    "SalesInvoiceLine": ["ItemID", "Quantity", "UnitPrice", "Discount", "LineTotal"],
    "CreditMemo": ["CreditMemoDate", "OriginalSalesInvoiceID", "SubTotal", "GrandTotal"],
    "CashReceipt": ["ReceiptDate", "CustomerID", "Amount"],
    "CashReceiptApplication": ["CashReceiptID", "SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "Customer": ["CustomerName", "CreditLimit", "PaymentTerms"],
    "Item": ["StandardCost", "ItemGroup", "SupplyMode", "RevenueAccountID", "InventoryAccountID", "COGSAccountID"],
    "WorkOrder": ["WorkOrderNumber"], "MaterialIssue": ["IssueDate"], "ProductionCompletion": ["CompletionDate"],
    "Shipment": ["ShipmentDate", "SalesOrderID"],
    "ShipmentLine": ["ItemID", "QuantityShipped", "ExtendedStandardCost"],
    "GoodsReceiptLine": ["ItemID", "QuantityReceived", "ExtendedStandardCost"],
    "MaterialIssueLine": ["ItemID", "QuantityIssued", "ExtendedStandardCost"],
    "ProductionCompletionLine": ["ItemID", "QuantityCompleted", "ExtendedStandardTotalCost"],
    "WorkOrderClose": ["TotalVarianceAmount"],
    "Account": ["AccountNumber", "AccountName", "AccountType", "AccountSubType", "ParentAccountID", "NormalBalance"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "FiscalYear", "FiscalPeriod", "SourceDocumentType"],
    "JournalEntry": ["EntryType", "TotalAmount", "PostingDate", "CreatedByEmployeeID", "ApprovedByEmployeeID"],
}
REVENUE_ACCOUNTS = ("4010", "4020", "4030", "4040", "4080")


@context("ch01.ex1")
def ex1(d, claim):
    schema(d, claim, EX1_SCHEMA)
    in_group(claim, {"Customer": "Order-to-Cash", "SalesInvoice": "Order-to-Cash", "CashReceipt": "Order-to-Cash", "Shipment": "Order-to-Cash",
                     "Item": "Master Data", "Account": "Accounting Core", "GLEntry": "Accounting Core", "JournalEntry": "Accounting Core",
                     "WorkOrder": "Manufacturing", "MaterialIssue": "Manufacturing", "ProductionCompletion": "Manufacturing",
                     "WorkOrderClose": "Manufacturing"})
    names = dict(d.q("SELECT AccountNumber, AccountName FROM Account WHERE AccountNumber IN (1020, 1040, 1045, 4010, 4050, 4060, 5010)"))
    claim(len(names) == 7, "accounts 1020, 1040, 1045, 4010, 4050, 4060 and 5010 exist")
    claim(names.get(1020) == "Accounts Receivable" and names.get(4010) == "Sales Revenue - Furniture" and names.get(4050) == "Freight Revenue"
          and names.get(4060) == "Sales Returns and Allowances", "1020 is receivables, 4010 furniture revenue, 4050 freight revenue and 4060 returns")
    posts = {t: sorted(r[0] for r in d.q("SELECT DISTINCT a.AccountNumber FROM GLEntry g JOIN Account a USING (AccountID) "
                                         "WHERE g.SourceDocumentType = ?", t)) for t in ("SalesInvoice", "Shipment")}
    claim({1020, 4010, 4050, 2050} <= set(posts["SalesInvoice"]),
          "a sales invoice posts to receivables (1020), revenue (4010 and the other revenue accounts), freight revenue (4050) and sales tax payable (2050)")
    claim(1040 in posts["Shipment"] and 5010 in posts["Shipment"], "a shipment posts to finished goods inventory (1040) and to cost of goods sold (5010)")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType IN ('SalesOrder', 'SalesOrderLine')") == 0,
          "a sales order posts nothing to the ledger")
    lines = d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice s USING (SalesInvoiceID) "
                  "WHERE s.InvoiceDate BETWEEN ? AND ?", f"{d.C}-01-01", f"{d.C}-12-31")
    ledger = d.one("SELECT SUM(g.Credit - g.Debit) FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.SourceDocumentType = "
                   "'SalesInvoice' AND g.FiscalYear = ? AND a.AccountNumber IN (4010, 4020, 4030, 4040, 4080)", d.C)
    claim(0 < ledger - lines < 0.001 * lines, "the ledger's revenue credits from invoices exceed the invoice lines by a small amount (the cutoff invoices)")
    cutoff = d.one("SELECT COUNT(DISTINCT s.SalesInvoiceID) FROM SalesInvoice s JOIN GLEntry g ON g.SourceDocumentType = 'SalesInvoice' "
                   "AND g.SourceDocumentID = s.SalesInvoiceID WHERE g.FiscalYear = ? AND s.InvoiceDate < ?", d.C, f"{d.C}-01-01")
    claim(0 < cutoff <= 5, "a few invoices dated before the year began are posted in it")
    return dict(rows=rows_of(d, ["SalesInvoice", "SalesInvoiceLine", "CashReceipt", "CashReceiptApplication", "CreditMemo", "Customer",
                                 "Item", "Shipment", "ShipmentLine", "Account", "GLEntry", "JournalEntry"]),
                lines=lines, ledger=ledger, gap=ledger - lines, year=d.C, prior=d.P, cutoff_n=cutoff, ar=d.one("SELECT AccountNumber FROM Account WHERE AccountName = 'Accounts Receivable'"), revenue_accounts=and_join(REVENUE_ACCOUNTS))


# --- Exercise 1.2: tracing the revenue path from order to ledger -------------------------------------------------------

EX2_SCHEMA = {
    "SalesOrder": ["OrderNumber", "OrderDate", "CustomerID", "Status", "OrderTotal", "FreightTerms"],
    "SalesOrderLine": ["SalesOrderID", "ItemID", "Quantity", "UnitPrice", "Discount", "LineTotal"],
    "Shipment": ["ShipmentNumber", "SalesOrderID", "ShipmentDate", "WarehouseID", "Status", "DeliveryDate"],
    "SalesInvoice": ["InvoiceNumber", "InvoiceDate", "DueDate", "SalesOrderID", "CustomerID", "SubTotal", "FreightAmount", "TaxAmount",
                     "GrandTotal", "Status", "PaymentDate"],
    "CashReceipt": ["ReceiptNumber", "ReceiptDate", "CustomerID", "Amount", "PaymentMethod", "DepositDate"],
    "CashReceiptApplication": ["CashReceiptID", "SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "VoucherType", "VoucherNumber", "SourceDocumentType",
                "SourceDocumentID", "SourceLineID", "CostCenterID", "Description"],
}


def gl_rows_of(d, source: str, document_id: int) -> list[dict]:
    return [dict(id=r[0], date=r[1], number=r[2], name=r[3], debit=r[4], credit=r[5], line=r[6], account_id=r[7])
            for r in d.q("SELECT g.GLEntryID, g.PostingDate, a.AccountNumber, a.AccountName, g.Debit, g.Credit, g.SourceLineID, g.AccountID "
                         "FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.SourceDocumentType = ? AND g.SourceDocumentID = ? "
                         "ORDER BY g.GLEntryID", source, document_id)]


@context("ch01.ex2")
def ex2(d, claim):
    have = schema(d, claim, EX2_SCHEMA)
    t = trace_ids(d)
    claim(t["id.trace.exact"], "the traced sale exists exactly as Chapter 1 tells it")
    so, inv, sh, rec, app = (t["id.trace.order_id"], t["id.trace.invoice_id"], t["id.trace.shipment_id"],
                             t["id.trace.receipt_id"], t["id.trace.application_id"])
    order = dict(lines=d.one("SELECT COUNT(*) FROM SalesOrderLine WHERE SalesOrderID = ?", so),
                 shipments=d.one("SELECT COUNT(*) FROM Shipment WHERE SalesOrderID = ?", so),
                 invoices=d.one("SELECT COUNT(*) FROM SalesInvoice WHERE SalesOrderID = ?", so))
    claim(order["shipments"] > 1 and order["invoices"] > 1, "the traced order was shipped and invoiced in several parts")
    si = d.q("SELECT InvoiceDate, DueDate, SubTotal, FreightAmount, TaxAmount, GrandTotal, Status, PaymentDate FROM SalesInvoice "
             "WHERE SalesInvoiceID = ?", inv)[0]
    invoice = dict(date=si[0], due=si[1], subtotal=si[2], freight=si[3], tax=si[4], total=si[5], status=si[6], paid=si[7])
    line = d.q("SELECT Quantity, UnitPrice, LineTotal FROM SalesInvoiceLine WHERE SalesInvoiceLineID = ?", t["id.trace.line_id"])[0]
    invoice.update(quantity=line[0], unit_price=line[1], line_total=line[2])
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE SalesInvoiceID = ?", inv) == 1, "the traced invoice has one line")
    gl = gl_rows_of(d, "SalesInvoice", inv)
    revenue = d.q("SELECT g.AccountID, a.AccountNumber, a.AccountName FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.GLEntryID = ?",
                  t["id.trace.gl_revenue_id"])[0]
    revenue = dict(account_id=revenue[0], number=revenue[1], name=revenue[2], gl_id=t["id.trace.gl_revenue_id"])
    claim(len(gl) == 4, "the traced invoice posts four ledger rows")
    creators = d.q("SELECT DISTINCT e.JobTitle FROM GLEntry g JOIN Employee e ON e.EmployeeID = g.CreatedByEmployeeID WHERE g.SourceDocumentType = 'SalesInvoice'")
    claim(len(creators) == 1, "every ledger row from a sales invoice names the same creator")
    claim(abs(sum(r["debit"] for r in gl) - sum(r["credit"] for r in gl)) < 0.005, "the invoice's ledger rows balance")
    ship_gl = gl_rows_of(d, "Shipment", sh)
    claim({r["number"] for r in ship_gl} == {5010, 1040, 5050, 2040},
          "a shipment posts cost of goods sold (5010) against finished goods (1040), and freight-out (5050) against accrued expenses (2040)")
    claim({r["number"] for r in gl} == {1020, 4010, 4050, 2050},
          "an invoice posts receivables (1020), revenue (4010), freight revenue (4050) and sales tax payable (2050)")
    receipt = d.q("SELECT ReceiptDate, Amount, PaymentMethod FROM CashReceipt WHERE CashReceiptID = ?", rec)[0]
    apps = d.q("SELECT COUNT(*), SUM(AppliedAmount) FROM CashReceiptApplication WHERE CashReceiptID = ?", rec)[0]
    this_app = d.q("SELECT ApplicationDate, AppliedAmount FROM CashReceiptApplication WHERE CashReceiptApplicationID = ?", app)[0]
    claim(apps[0] > 1, "the traced receipt paid several invoices")
    claim(abs(this_app[1] - invoice["total"]) < 0.005, "the application to the traced invoice equals its total")
    receipt = dict(date=receipt[0], amount=receipt[1], method=receipt[2], applications=apps[0], applied=apps[1],
                   applied_here=this_app[1], applied_date=this_app[0][:10])
    gl_receipt, gl_app = gl_rows_of(d, "CashReceipt", rec), gl_rows_of(d, "CashReceiptApplication", app)
    claim({r["number"] for r in gl_receipt} == {1010, 2060} and {r["number"] for r in gl_app} == {2060, 1020},
          "a receipt posts to cash (1010) and unapplied cash (2060), and its application moves that amount from 2060 to receivables (1020)")
    source_types = [r[0] for r in d.q("SELECT SourceDocumentType FROM GLEntry GROUP BY 1 ORDER BY COUNT(*) DESC")]
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherType <> SourceDocumentType") == 0,
          "VoucherType repeats SourceDocumentType on every ledger row")
    claim(all(x not in source_types for x in ("SalesOrder", "SalesOrderLine")), "no ledger row names a sales order as its source")
    multi_orders = d.one("SELECT COUNT(*) FROM (SELECT SalesOrderID FROM SalesInvoice GROUP BY 1 HAVING COUNT(*) > 1)")
    orders = d.one("SELECT COUNT(DISTINCT SalesOrderID) FROM SalesInvoice")
    multi_receipts = d.one("SELECT COUNT(*) FROM (SELECT CashReceiptID FROM CashReceiptApplication GROUP BY 1 HAVING COUNT(*) > 1)")
    receipts = d.one("SELECT COUNT(DISTINCT CashReceiptID) FROM CashReceiptApplication")
    claim(multi_orders / orders > 0.3 and multi_receipts / receipts > 0.3,
          "many orders have more than one invoice and many receipts pay more than one invoice")
    absent = ["CustomerID", "InvoiceDate", "DueDate", "SalesOrderID", "Status", "PaymentDate"]
    claim(all(c in have["SalesInvoice"] and c not in have["GLEntry"] for c in absent),
          "SalesInvoice has, and GLEntry lacks, the columns CustomerID, InvoiceDate, DueDate, SalesOrderID, Status and PaymentDate")
    numbers = dict(order=t["id.trace.order"], shipment=t["id.trace.shipment"], invoice=t["id.trace.invoice"], receipt=t["id.trace.receipt"],
                   customer=t["id.trace.customer_name"], item=t["id.trace.item_code"], item_label=t["id.trace.item_label"])
    ids = dict(order=so, invoice=inv, line=t["id.trace.line_id"], shipment=sh, receipt=rec, application=app, customer=t["id.trace.customer_id"])
    return dict(creator=creators[0][0].lower() if creators else '', t=t, numbers=numbers, ids=ids, order=order, invoice=invoice, revenue=revenue, gl=gl, ship_gl=ship_gl, receipt=receipt, gl_receipt=gl_receipt, gl_app=gl_app,
                source_types=and_join(source_types), n_source_types=len(source_types),
                rows=rows_of(d, ["SalesOrder", "SalesOrderLine", "Shipment", "SalesInvoice", "CashReceipt", "CashReceiptApplication", "GLEntry"]),
                multi_orders=multi_orders, orders=orders, multi_receipts=multi_receipts, receipts=receipts,
                ship_date=t["date.trace.shipment"], order_date=t["date.trace.order"], gl_cols=len(have["GLEntry"]))


# --- Exercise 1.3: evaluating table groups for cost analysis ------------------------------------------------------------

EX3_SCHEMA = {
    "WorkOrder": ["WorkOrderNumber", "ItemID", "BOMID", "PlannedQuantity", "ReleasedDate", "DueDate", "CompletedDate", "ClosedDate", "Status", "CostCenterID"],
    "BillOfMaterial": ["ParentItemID", "StandardBatchQuantity"],
    "BillOfMaterialLine": ["ComponentItemID", "QuantityPerUnit", "ScrapFactorPct"],
    "MaterialIssue": ["WorkOrderID", "IssueDate"],
    "MaterialIssueLine": ["ItemID", "QuantityIssued", "ExtendedStandardCost"],
    "ProductionCompletion": ["WorkOrderID", "CompletionDate"],
    "ProductionCompletionLine": ["QuantityCompleted", "ExtendedStandardMaterialCost", "ExtendedStandardConversionCost", "ExtendedStandardTotalCost"],
    "WorkOrderClose": ["WorkOrderID", "CloseDate", "MaterialVarianceAmount", "DirectLaborVarianceAmount", "OverheadVarianceAmount",
                       "ConversionVarianceAmount", "TotalVarianceAmount"],
    "Item": ["StandardCost", "StandardLaborHoursPerUnit", "StandardDirectLaborCost", "StandardVariableOverheadCost",
             "StandardFixedOverheadCost", "StandardConversionCost"],
    "CostCenter": ["CostCenterID", "CostCenterName", "ParentCostCenterID", "ManagerID"],
    "Budget": ["FiscalYear", "Month", "CostCenterID", "AccountID", "BudgetAmount"],
    "BudgetLine": ["FiscalYear", "Month", "AccountID", "CostCenterID", "ItemID", "WarehouseID", "Quantity", "UnitAmount", "BudgetAmount",
                   "BudgetCategory", "DriverType"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "FiscalYear", "FiscalPeriod", "CostCenterID"],
    "LaborTimeEntry": ["EmployeeID", "WorkOrderID", "WorkOrderOperationID", "WorkDate", "LaborType", "RegularHours", "OvertimeHours",
                       "HourlyRateUsed", "ExtendedLaborCost"],
    "PayrollRegister": ["PayrollPeriodID", "EmployeeID", "CostCenterID", "GrossPay", "NetPay"],
    "WorkOrderOperation": ["PlannedLoadHours"],
    "RoughCutCapacityPlan": ["PlannedLoadHours"],
    "Employee": ["JobTitle"],
}


@context("ch01.ex3")
def ex3(d, claim):
    schema(d, claim, EX3_SCHEMA)
    in_group(claim, {"WorkOrder": "Manufacturing", "BillOfMaterial": "Manufacturing", "MaterialIssue": "Manufacturing",
                     "ProductionCompletion": "Manufacturing", "WorkOrderClose": "Manufacturing", "CostCenter": "Organizational Planning",
                     "Budget": "Organizational Planning", "BudgetLine": "Organizational Planning", "LaborTimeEntry": "Payroll and Time",
                     "PayrollRegister": "Payroll and Time", "RoughCutCapacityPlan": "Demand Planning", "Item": "Master Data",
                     "Employee": "Master Data"})
    claim(d.one("SELECT COUNT(*) FROM Budget WHERE CostCenterID IS NULL") == 0, "every Budget row has a cost center")
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Budget GROUP BY FiscalYear, Month, CostCenterID, AccountID HAVING COUNT(*) > 1)") == 0,
          "Budget has one row for each fiscal year, month, cost center and account")
    line_blank = d.one("SELECT COUNT(*) FROM BudgetLine WHERE CostCenterID IS NULL")
    claim(line_blank > 0, "some BudgetLine rows have no cost center")
    claim(d.one("SELECT MAX(FiscalYear) FROM Budget") == d.N, "the budget runs one year past the last year of actuals")
    claim([r[0] for r in d.q(f"SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE FiscalYear = {d.N}")] == ["DisbursementPayment"],
          "the ledger's rows of the year after the last full year are supplier payments only")
    # expense postings outside the year-end closes, by rows and by amount (debits less credits)
    expense, blank, amount, blank_amount, blank_opex = d.q(
        "SELECT COUNT(*), SUM(g.CostCenterID IS NULL), SUM(g.Debit - g.Credit), "
        "SUM(CASE WHEN g.CostCenterID IS NULL THEN g.Debit - g.Credit ELSE 0 END), "
        "SUM(CASE WHEN g.CostCenterID IS NULL AND a.AccountSubType = 'Operating Expense' THEN g.Debit - g.Credit ELSE 0 END) "
        f"FROM GLEntry g JOIN Account a USING (AccountID) WHERE a.AccountType = 'Expense' AND g.{d.no_closes()}")[0]
    claim(0 < blank / expense < 0.02, "outside the closes, a small share of the expense postings has no cost center")
    claim(blank_amount / amount > 4 * blank / expense, "the postings with no cost center carry a far larger share of the expense amount than of its rows")
    claim(blank_opex > 0.9 * blank_amount, "nearly all of the expense amount with no cost center is operating expense")
    claim(d.one("SELECT COUNT(*) FROM Budget b JOIN Account a USING (AccountID) WHERE a.AccountType NOT IN ('Expense', 'Revenue')") == 0,
          "Budget holds revenue and expense accounts only")
    claim(d.one("SELECT COUNT(*) FROM BudgetLine b JOIN Account a USING (AccountID) WHERE a.AccountType IN ('Asset', 'Liability', 'Equity')") > 0,
          "BudgetLine also holds balance sheet accounts")
    claim(d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE WorkOrderID IS NOT NULL") > 0, "labor time entries name a work order")
    centers = [r[0] for r in d.q("SELECT CostCenterName FROM CostCenter ORDER BY CostCenterID")]
    claim("Manufacturing" in centers, "Manufacturing is a cost center")
    return dict(rows=rows_of(d, ["WorkOrder", "BillOfMaterial", "MaterialIssue", "ProductionCompletion", "WorkOrderClose", "CostCenter",
                                 "Budget", "BudgetLine", "LaborTimeEntry", "PayrollRegister", "GLEntry"]),
                n_centers=len(centers), centers=and_join(centers), line_blank=line_blank, expense=expense, blank=blank,
                blank_share=blank / expense, blank_amount_share=blank_amount / amount, budget_first=d.one("SELECT MIN(FiscalYear) FROM Budget"),
                budget_last=d.one("SELECT MAX(FiscalYear) FROM Budget"))


# --- Exercise 1.4: framing production questions ------------------------------------------------------------------------

EX4_SCHEMA = {
    "ProductionCompletion": ["CompletionDate", "WorkOrderID"],
    "ProductionCompletionLine": ["ItemID", "QuantityCompleted"],
    "WorkOrderClose": ["CloseDate", "TotalVarianceAmount"],
    "WorkOrder": ["ItemID", "PlannedQuantity", "DueDate", "CompletedDate", "Status"],
    "Item": ["ItemGroup", "SupplyMode", "StandardLaborHoursPerUnit"],
    "DemandForecast": ["ForecastWeekStartDate", "ItemID", "ForecastQuantity", "ForecastMethod"],
    "WorkCenter": ["WorkCenterName", "NominalDailyCapacityHours"],
    "WorkCenterCalendar": ["WorkCenterID", "CalendarDate", "AvailableHours", "ExceptionReason"],
    "RoutingOperation": ["WorkCenterID", "StandardSetupHours", "StandardRunHoursPerUnit"],
    "RoughCutCapacityPlan": ["WorkCenterID", "PlannedLoadHours", "AvailableHours", "UtilizationPct"],
    "LaborTimeEntry": ["WorkOrderID", "RegularHours", "OvertimeHours"],
}


def quarter_bounds(day: str) -> tuple[str, str, str]:
    year, month = int(day[:4]), int(day[5:7])
    q = (month - 1) // 3 + 1
    end_month = q * 3
    end_day = {3: 31, 6: 30, 9: 30, 12: 31}[end_month]
    return f"Q{q} {year}", f"{year}-{3 * q - 2:02d}-01", f"{year}-{end_month:02d}-{end_day}"


@context("ch01.ex4")
def ex4(d, claim):
    schema(d, claim, EX4_SCHEMA)
    in_group(claim, {"DemandForecast": "Demand Planning", "RoughCutCapacityPlan": "Demand Planning", "WorkOrderClose": "Manufacturing",
                     "LaborTimeEntry": "Payroll and Time", "Item": "Master Data"})
    claim(d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured' AND COALESCE(StandardFixedOverheadCost, 0) <= 0") == 0,
          "the standard cost of every manufactured item includes fixed overhead")
    last_day = d.one("SELECT MAX(CompletionDate) FROM ProductionCompletion")
    label, start, end = quarter_bounds(last_day)
    claim(last_day == end, "the completion records run to the end of a quarter, so the last quarter is a whole one")
    prev_label, prev_start, prev_end = quarter_bounds((date.fromisoformat(start) - timedelta(days=1)).isoformat())
    by_group = {}
    for g, a, b in d.q("SELECT i.ItemGroup, SUM(CASE WHEN p.CompletionDate BETWEEN ?1 AND ?2 THEN l.QuantityCompleted ELSE 0 END), "
                       "SUM(CASE WHEN p.CompletionDate BETWEEN ?3 AND ?4 THEN l.QuantityCompleted ELSE 0 END) FROM ProductionCompletion p "
                       "JOIN ProductionCompletionLine l USING (ProductionCompletionID) JOIN Item i ON i.ItemID = l.ItemID GROUP BY 1 "
                       "HAVING SUM(CASE WHEN p.CompletionDate BETWEEN ?1 AND ?4 THEN l.QuantityCompleted ELSE 0 END) > 0 ORDER BY 2 DESC",
                       prev_start, prev_end, start, end):
        by_group[g] = dict(prev=a, last=b)
    claim(len(by_group) >= 2, "two or more item groups were completed in the last two quarters")
    units = [(y, d.one("SELECT SUM(l.QuantityCompleted) FROM ProductionCompletion p JOIN ProductionCompletionLine l USING "
                       "(ProductionCompletionID) WHERE substr(p.CompletionDate, 1, 4) = ?", str(y))) for y in d.years]
    variance = [(y, d.one("SELECT SUM(TotalVarianceAmount) FROM WorkOrderClose WHERE substr(CloseDate, 1, 4) = ?", str(y))) for y in d.years]
    units_change = units[-1][1] / units[0][1] - 1
    variance_change = variance[-1][1] / variance[0][1] - 1
    claim(d.one("SELECT COUNT(*) FROM ProductionCompletionLine WHERE QuantityCompleted <> ROUND(QuantityCompleted)") > 0,
          "some quantities completed are not whole numbers")
    claim(abs(units_change) < 0.10, "units completed are about the same in the last year as in the first")
    claim(variance_change > 0.5, "the total variance on closed work orders rose by more than half over the window")
    work_centers = [r[0] for r in d.q("SELECT WorkCenterName FROM WorkCenter ORDER BY WorkCenterID")]
    scrap = [(t, c) for (t,) in d.q("SELECT name FROM sqlite_master WHERE type = 'table'")
             for c in [r[1] for r in d.q(f"PRAGMA table_info({t})")] if re.search(r"scrap|defect|reject|downtime|yield", c, re.I)]
    claim(scrap == [("BillOfMaterialLine", "ScrapFactorPct")], "the only scrap, defect or downtime column is the planned scrap factor of BillOfMaterialLine")
    claim(d.one("SELECT COUNT(*) FROM WorkCenterCalendar WHERE ExceptionReason = 'Maintenance'") > 0, "the work center calendar marks maintenance days")
    return dict(last_quarter=label, prev_quarter=prev_label, by_group=by_group, total_last=sum(v["last"] for v in by_group.values()),
                total_prev=sum(v["prev"] for v in by_group.values()), units=units, variance=variance, units_change=units_change,
                variance_change=variance_change, first=d.F, last=d.C, work_centers=and_join(work_centers), n_work_centers=len(work_centers),
                forecast_methods=and_join(r[0] for r in d.q("SELECT ForecastMethod FROM DemandForecast GROUP BY 1 ORDER BY 1")),
                rows=rows_of(d, ["ProductionCompletionLine", "WorkOrderClose", "DemandForecast", "WorkCenterCalendar", "RoughCutCapacityPlan"]))


# --- Exercise 1.5: assessing data availability for audit testing ------------------------------------------------------------

EX5_SCHEMA = {
    "SalesInvoice": ["InvoiceNumber", "InvoiceDate", "DueDate", "CustomerID", "GrandTotal", "Status", "PaymentDate"],
    "Customer": ["CustomerName", "CreditLimit", "PaymentTerms"],
    "CashReceipt": ["ReceiptDate", "Amount"],
    "CashReceiptApplication": ["SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "CreditMemo": ["CreditMemoDate", "OriginalSalesInvoiceID", "GrandTotal"],
    "PurchaseInvoice": ["InvoiceNumber", "InvoiceDate", "SupplierID", "GrandTotal"],
    "DisbursementPayment": ["PaymentNumber", "PaymentDate", "SupplierID", "PurchaseInvoiceID", "Amount", "PaymentMethod", "CheckNumber"],
    "Supplier": ["SupplierName"],
    "JournalEntry": ["EntryNumber", "PostingDate", "EntryType", "Description", "TotalAmount", "CreatedByEmployeeID", "CreatedDate",
                     "ApprovedByEmployeeID", "ApprovedDate", "ReversesJournalEntryID"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "SourceDocumentType", "SourceDocumentID", "CreatedByEmployeeID", "CreatedDate"],
    "Employee": ["EmployeeName", "JobTitle", "MaxApprovalAmount"],
}


@context("ch01.ex5")
def ex5(d, claim):
    schema(d, claim, EX5_SCHEMA)
    in_group(claim, {"DisbursementPayment": "Procure-to-Pay", "PurchaseInvoice": "Procure-to-Pay", "SalesInvoice": "Order-to-Cash",
                     "CashReceipt": "Order-to-Cash", "JournalEntry": "Accounting Core", "GLEntry": "Accounting Core", "Employee": "Master Data"})
    from notes.ch08 import open_invoices
    open_ids = {i["id"] for i in open_invoices(d)}
    status_ids = {r[0] for r in d.q("SELECT SalesInvoiceID FROM SalesInvoice WHERE Status IN ('Submitted', 'Partially Settled')")}
    claim(open_ids == status_ids, "at the last date of the data, the invoices with an open balance are those whose Status is Submitted or Partially Settled")
    statuses = [r[0] for r in d.q("SELECT Status FROM SalesInvoice GROUP BY 1 ORDER BY COUNT(*) DESC")]
    claim(sorted(statuses) == ["Partially Settled", "Settled", "Submitted"], "SalesInvoice.Status has three values")
    types = [r[0] for r in d.q("SELECT SourceDocumentType FROM GLEntry GROUP BY 1")]
    je_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    entries = d.one("SELECT COUNT(*) FROM JournalEntry")
    claim(d.one("SELECT COUNT(DISTINCT SourceDocumentID) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'") == entries,
          "every journal entry has ledger rows, and the ledger rows of that type name no other entries")
    creators = d.one("SELECT COUNT(DISTINCT CreatedByEmployeeID) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice'")
    claim(creators == 1, "every ledger row from a sales invoice names the same creator")
    receipts = d.one("SELECT COUNT(*) FROM CashReceipt")
    direct = d.one("SELECT COUNT(*) FROM CashReceipt WHERE SalesInvoiceID IS NOT NULL")
    claim(0 < direct < 0.2 * receipts, "CashReceipt.SalesInvoiceID is filled for only a small share of the receipts")
    claim(d.one("SELECT COUNT(*) FROM CashReceipt r WHERE r.SalesInvoiceID IS NOT NULL AND (SELECT COUNT(*) FROM CashReceiptApplication a "
                "WHERE a.CashReceiptID = r.CashReceiptID) <> 1") == 0,
          "a receipt with a SalesInvoiceID is one that has a single application")
    # the converse does not hold: a blank link can be a receipt that pays one invoice or several
    paid = dict(d.q("SELECT n, COUNT(*) FROM (SELECT (SELECT COUNT(DISTINCT a.SalesInvoiceID) FROM CashReceiptApplication a "
                    "WHERE a.CashReceiptID = r.CashReceiptID) AS n FROM CashReceipt r WHERE r.SalesInvoiceID IS NULL) "
                    "GROUP BY CASE WHEN n > 1 THEN 2 ELSE n END"))
    blank_single = paid.get(1, 0)
    blank_multi = sum(v for k, v in paid.items() if k > 1)
    claim(0 not in paid, "every receipt with a blank SalesInvoiceID has at least one application")
    claim(blank_single > 0 and blank_multi > 0, "receipts with a blank SalesInvoiceID include some that pay one invoice and some that pay several")
    return dict(n_source_types=len(types), je_rows=je_rows, entries=entries, gl_rows=d.one("SELECT COUNT(*) FROM GLEntry"),
                payments=d.one("SELECT COUNT(*) FROM DisbursementPayment"), receipts=receipts, direct=direct, blank_single=blank_single, blank_multi=blank_multi, purchase_invoices=d.one("SELECT COUNT(*) FROM PurchaseInvoice"),
                statuses=and_join(statuses), open_n=len(open_ids), asof=f"{d.C}-12-31", ar_ledger=d.balance(["1020"], f"{d.C}-12-31"),
                creator=d.q("SELECT e.JobTitle FROM Employee e WHERE e.EmployeeID = (SELECT CreatedByEmployeeID FROM GLEntry WHERE "
                            "SourceDocumentType = 'SalesInvoice' LIMIT 1)")[0][0].lower())


# --- Exercise 1.6: evaluating journal entry data for audit purposes -----------------------------------------------------------

EX6_SCHEMA = {
    "JournalEntry": ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "Description", "TotalAmount", "CreatedByEmployeeID",
                     "CreatedDate", "ApprovedByEmployeeID", "ApprovedDate", "ReversesJournalEntryID"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherType", "VoucherNumber", "SourceDocumentType",
                "SourceDocumentID", "SourceLineID", "CostCenterID", "Description", "CreatedByEmployeeID", "CreatedDate", "FiscalYear", "FiscalPeriod"],
    "Employee": ["EmployeeName", "JobTitle", "MaxApprovalAmount", "AuthorizationLevel"],
}


@context("ch01.ex6")
def ex6(d, claim):
    have = schema(d, claim, EX6_SCHEMA)
    claim(have["JournalEntry"] == EX6_SCHEMA["JournalEntry"], "the JournalEntry worksheet has exactly the columns the guide lists")
    claim(have["GLEntry"] == EX6_SCHEMA["GLEntry"], "the GLEntry worksheet has exactly the columns the guide lists")
    entries = d.one("SELECT COUNT(*) FROM JournalEntry")
    je_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    times = d.q("SELECT substr(CreatedDate, 12), COUNT(*) FROM JournalEntry GROUP BY 1 ORDER BY 2 DESC")
    claim(len(times) <= 3, "journal entries are created at only a few distinct clock times")
    after_hours = d.one("SELECT COUNT(*) FROM JournalEntry WHERE substr(CreatedDate, 12, 5) < '08:00' OR substr(CreatedDate, 12, 5) > '17:00'")
    claim(after_hours == 0, "no journal entry is created before 08:00 or after 17:00")
    approved_times = [r[0] for r in d.q("SELECT substr(ApprovedDate, 12) FROM JournalEntry GROUP BY 1 ORDER BY COUNT(*) DESC")]
    claim(len(approved_times) <= 3, "journal entries are approved at only a few distinct clock times")
    claim(d.one("SELECT COUNT(*) FROM JournalEntry WHERE ROUND((julianday(ApprovedDate) - julianday(CreatedDate)) * 24, 6) <> 1") == 0,
          "every journal entry is approved exactly one hour after it is created")
    gl_times = d.q("SELECT substr(CreatedDate, 12), COUNT(*) FROM GLEntry GROUP BY 1")
    claim(len(gl_times) == 2, "ledger rows carry one clock time for journal entries and one for every other source")
    weekend = d.one("SELECT COUNT(*) FROM JournalEntry WHERE strftime('%w', substr(CreatedDate, 1, 10)) IN ('0', '6')")
    claim(weekend > 0, "some journal entries are created on a weekend")
    whole = d.one("SELECT COUNT(*) FROM JournalEntry WHERE TotalAmount = ROUND(TotalAmount)")
    thousands = [r for r in d.q("SELECT EntryNumber, TotalAmount FROM JournalEntry WHERE TotalAmount >= 1000 AND TotalAmount = ROUND(TotalAmount / 1000) * 1000 "
                                "ORDER BY PostingDate, EntryNumber")]
    claim(0 < len(thousands) < whole, "fewer entries are exact multiples of 1,000 than are whole-dollar amounts")
    approvers = [dict(title=r[0], limit=r[1], entries=r[2]) for r in
                 d.q("SELECT e.JobTitle, e.MaxApprovalAmount, COUNT(*) FROM JournalEntry j JOIN Employee e ON e.EmployeeID = j.ApprovedByEmployeeID "
                     "GROUP BY 1, 2 ORDER BY 3 DESC")]
    above = d.one("SELECT COUNT(*) FROM JournalEntry j JOIN Employee e ON e.EmployeeID = j.ApprovedByEmployeeID WHERE j.TotalAmount > e.MaxApprovalAmount")
    near = d.q("SELECT j.EntryNumber, j.EntryType, j.TotalAmount, e.MaxApprovalAmount FROM JournalEntry j JOIN Employee e ON e.EmployeeID = "
               "j.ApprovedByEmployeeID WHERE j.TotalAmount > 0.9 * e.MaxApprovalAmount AND j.TotalAmount <= e.MaxApprovalAmount ORDER BY 1")
    claim(len(near) > 0 and all(r[1] == "Rent" for r in near), "the entries just below an approver's limit are ordinary rent entries")
    claim(above > 0, "some entries are above their approver's limit")
    reversing = d.q("SELECT r.EntryType, o.EntryType, r.TotalAmount, o.TotalAmount, julianday(r.PostingDate) - julianday(o.PostingDate), "
                    "substr(r.PostingDate, 1, 4) <> substr(o.PostingDate, 1, 4) FROM JournalEntry r JOIN JournalEntry o ON "
                    "o.JournalEntryID = r.ReversesJournalEntryID")
    claim(len(reversing) == d.one("SELECT COUNT(*) FROM JournalEntry WHERE ReversesJournalEntryID IS NOT NULL"), "every reversal names an existing entry")
    claim({r[0] for r in reversing} == {"Accrual Adjustment"} and {r[1] for r in reversing} == {"Accrual"},
          "every entry that names another entry it reverses is an Accrual Adjustment of an Accrual")
    claim(all(r[2] < r[3] for r in reversing), "no reversing entry equals its original in amount: each is smaller")
    claim(d.one("SELECT COUNT(*) FROM JournalEntry WHERE ReversesJournalEntryID IS NOT NULL AND Description NOT LIKE '%residual%'") == 0,
          "the description of every reversing entry mentions a residual accrual")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID WHERE g.SourceDocumentType = "
                "'JournalEntry' AND g.CreatedByEmployeeID <> j.CreatedByEmployeeID") == 0,
          "the ledger rows of a journal entry name the entry's own creator")
    return dict(entries=entries, je_rows=je_rows, times=[(t, n) for t, n in times], n_times=len(times), after_hours=after_hours,
                approved_times=approved_times,
                gl_je_time=d.one("SELECT substr(CreatedDate, 12) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry' LIMIT 1"),
                gl_other_time=d.one("SELECT substr(CreatedDate, 12) FROM GLEntry WHERE SourceDocumentType <> 'JournalEntry' LIMIT 1"),
                weekend=weekend, round_unit=1000, whole=whole, thousands=thousands, n_thousands=len(thousands), approvers=approvers, above=above, near=near,
                n_reversing=len(reversing),
                gap_min=min(r[4] for r in reversing), gap_max=max(r[4] for r in reversing), across_years=sum(1 for r in reversing if r[5]),
                je_cols=len(have["JournalEntry"]), gl_cols=len(have["GLEntry"]))
