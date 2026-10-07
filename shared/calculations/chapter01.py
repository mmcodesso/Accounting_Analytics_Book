"""Chapter 1 semantics shared by the book's figure builders."""

from __future__ import annotations

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
