"""Public Chapter 1 semantics shared by book and presentation figure builders."""

from __future__ import annotations

import sqlite3

WORKFLOW_STAGES = (
    ("1. Define the question", "Translate the business need into a specific analytical question"),
    ("2. Access the data", "Identify sources, extract relevant tables and columns"),
    ("3. Prepare and clean", "Resolve missing values, duplicates, inconsistent formatting"),
    ("4. Analyze", "Summarize, compare, model, detect anomalies"),
    ("5. Visualize and present", "Charts, dashboards, interactive reports for stakeholders"),
    ("6. Communicate findings", "Memoranda, presentations, and reports to decision makers"),
)

SALESORDER_COLUMNS = (
    "SalesOrderID", "OrderNumber", "OrderDate", "CustomerID", "RequestedDeliveryDate",
    "Status", "SalesRepEmployeeID",
)

TRACE_GLENTRY_ID = 126312


def source_trace(connection: sqlite3.Connection) -> dict:
    """The single revenue posting used in the public Chapter 1 worked example."""
    row = connection.execute(
        "SELECT g.GLEntryID, g.PostingDate, g.Debit, g.Credit, g.SourceDocumentType, "
        "g.SourceDocumentID, g.SourceLineID, a.AccountNumber, a.AccountName, "
        "s.InvoiceNumber, s.InvoiceDate, l.Quantity, l.UnitPrice, l.LineTotal, i.ItemCode "
        "FROM GLEntry g JOIN Account a USING (AccountID) "
        "JOIN SalesInvoice s ON g.SourceDocumentID = s.SalesInvoiceID "
        "JOIN SalesInvoiceLine l ON g.SourceLineID = l.SalesInvoiceLineID "
        "AND l.SalesInvoiceID = s.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
        "WHERE g.GLEntryID = ? AND g.SourceDocumentType = 'SalesInvoice'",
        (TRACE_GLENTRY_ID,),
    ).fetchone()
    if row is None:
        raise ValueError("The public Chapter 1 source trace no longer resolves.")
    fields = ("gl_entry_id", "posting_date", "debit", "credit", "source_type", "invoice_id",
              "invoice_line_id", "account_number", "account_name", "invoice_number", "invoice_date",
              "quantity", "unit_price", "line_total", "item_code")
    result = dict(zip(fields, row))
    if (result["invoice_id"], result["invoice_line_id"], result["quantity"], result["unit_price"]
            ) != (7947, 10645, 2, 344.21):
        raise ValueError("The fixed Chapter 1 worked example changed; review the book and deck together.")
    if abs(result["quantity"] * result["unit_price"] - result["line_total"]) > 0.005:
        raise ValueError("The Chapter 1 multiplication example needs editorial review.")
    if abs(result["credit"] - result["line_total"]) > 0.005 or result["debit"] != 0:
        raise ValueError("The Chapter 1 example is no longer one matching revenue credit.")
    return result


def salesorder_sample(connection: sqlite3.Connection) -> list[dict]:
    """First three worksheet rows, plus the customer each key identifies."""
    rows = connection.execute(
        "SELECT o.SalesOrderID, o.OrderNumber, o.OrderDate, o.CustomerID, c.CustomerName "
        "FROM SalesOrder o JOIN Customer c USING (CustomerID) ORDER BY o.SalesOrderID LIMIT 3"
    ).fetchall()
    if len(rows) != 3:
        raise ValueError("The Chapter 1 worksheet view requires three example orders.")
    keys = ("sales_order_id", "order_number", "order_date", "customer_id", "customer_name")
    return [dict(zip(keys, row)) for row in rows]
