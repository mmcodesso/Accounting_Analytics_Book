"""Credits Analytics.pbip: the Power BI part of the solution to the Chapter 19 capstone case ("Auditing the Customer
Credits Cycle"), the report Requirement 5 asks for.

The case starts a new Power BI file (Getting Started) and lists what Requirement 5 loads: the credit lines with their
reason, customer, approver, shipment date, and carrier; revenue from the invoice lines; Item, Customer, and Date; GLEntry
and Account for the Tests tab; and the refunds with the flags of RefundFlags.csv. The credit lines take their credit
memo, return, and shipment by Merge Queries; the invoice lines their invoice date and shipment date. Each fact relates
to Date by its own document date, and by its shipment date through an inactive relationship, so the return rate can be
read by the month of the credit and, with USERELATIONSHIP, by the month of the shipment (Chapter 14). The refunds take
the flags by RefundNumber, their credit and invoice by merges, and the report scores each refund one point a flag; a
drill-through page follows a refund to its credit, its invoice, and the receipts applied to that invoice (a table with
no relationship, read through TREATAS). As Part V's cases do, people appear by job title and employee ID only.

RefundFlags.csv is what Credits.sql exports (Requirement 4). `prepare` runs the query below read-only on
CharlesRiver.sqlite and writes the file where the manifest's also_sources says; the shipped project reads
C:\\CharlesRiver\\RefundFlags.csv, and the zip carries the file. The query applies the case's definitions, and
`prepare` stops unless every flag agrees with the instructor notes (facts/notes/ch19.py, which computes them in Python).

Checks: every value of the instructor notes of Requirement 5 and Milestone 2 that the report shows, and the refund flags
of Requirement 4 it loads, computed by facts/notes/ch19.py or by read-only SQL here, never typed from the text.
"""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from functools import cached_property
from pathlib import Path

from paths import REPO
from pbibuild.audit_monitoring import dax_blocks, definitions, drillthrough
from pbibuild.model import MEASURES_TABLE, Column, Measure, Model, Query, Table, query_table
from pbibuild.pbir import Page, Report, Visual, agg, col, lit, meas, textbox
from pbibuild.project import Project
from pbibuild.reports import COUNT, MONEY, card, claim, entered, hide, keep, money
from xlbuild import pq
from xlbuild.expected import Expected

from db import Data  # noqa: E402  (facts/ is on sys.path through pbibuild.reports)
from notes import ch19  # noqa: E402

FILE = "Credits Analytics"
FLAGS_CSV = "RefundFlags.csv"
NEUTRAL_CSV = "C:\\CharlesRiver\\" + FLAGS_CSV        # where the shipped project looks for the refund flags
DEFAULT_CSV = REPO / "outputs" / "companion" / "instructor-2026" / "Chapter19-capstone-pbi" / FLAGS_CSV
RATE = "0.000%"
KM = MEASURES_TABLE
M = lambda n: meas(KM, n)                 # noqa: E731
# The columns of RefundFlags.csv, as the Excel part of the solution pastes them (its RefundFlags sheet), with the type
# each is given in Power Query's Changed Type step (amounts as Decimal Number, whatever their first 200 rows hold).
FLAG_COLUMNS = [("RefundNumber", "type text"), ("RefundDate", "type date"), ("FiscalYear", "Int64.Type"),
                ("CustomerID", "Int64.Type"), ("Amount", "type number"), ("AboveLimit", "Int64.Type"),
                ("CreditAboveLimit", "Int64.Type"), ("MethodMismatch", "Int64.Type"), ("BeforePayment", "Int64.Type"),
                ("PastDue", "type number"), ("PastDueAtLeastRefund", "Int64.Type"), ("PastDueAny", "Int64.Type"),
                ("Score", "Int64.Type")]
FLAGS = ["AboveLimit", "CreditAboveLimit", "MethodMismatch", "BeforePayment", "PastDueAtLeastRefund"]
FLAG_NAMES = ["Refund above authority", "Credit above authority", "Method mismatch", "Before payment",
              "Past due at least the refund"]

# Credits.sql's export (Requirement 4): one row per refund with its five flags and its score. A refund precedes the
# customer's payment if it is dated before the last application on the credited invoice; the customer is past due on the
# refund date if an invoice dated by then, less the applications and credits dated by then, is open with its DueDate
# before the refund date; the method mismatches if no receipt applied to the credited invoice used the refund's method.
# Credits.sql (sqlbuild/cap19.py) holds this text verbatim, in the book's SQL style.
REFUND_FLAGS_SQL = """
WITH LastPayment AS (
    SELECT SalesInvoiceID, MAX(ApplicationDate) AS LastPaymentDate
    FROM CashReceiptApplication
    GROUP BY SalesInvoiceID
),
InvoiceMethods AS (
    SELECT DISTINCT cra.SalesInvoiceID, cr.PaymentMethod
    FROM CashReceiptApplication AS cra
        INNER JOIN CashReceipt AS cr ON cr.CashReceiptID = cra.CashReceiptID
),
DueInvoices AS (
    SELECT rf.CustomerRefundID, rf.RefundDate, si.SalesInvoiceID,
        si.GrandTotal
    FROM CustomerRefund AS rf
        INNER JOIN SalesInvoice AS si
            ON si.CustomerID = rf.CustomerID
            AND si.InvoiceDate <= rf.RefundDate
            AND si.DueDate < rf.RefundDate
),
PaidThen AS (
    SELECT di.CustomerRefundID, di.SalesInvoiceID,
        SUM(cra.AppliedAmount) AS Paid
    FROM DueInvoices AS di
        INNER JOIN CashReceiptApplication AS cra
            ON cra.SalesInvoiceID = di.SalesInvoiceID
            AND cra.ApplicationDate <= di.RefundDate
    GROUP BY di.CustomerRefundID, di.SalesInvoiceID
),
CreditedThen AS (
    SELECT di.CustomerRefundID, di.SalesInvoiceID,
        SUM(cm.GrandTotal) AS Credited
    FROM DueInvoices AS di
        INNER JOIN CreditMemo AS cm
            ON cm.OriginalSalesInvoiceID = di.SalesInvoiceID
            AND cm.CreditMemoDate <= di.RefundDate
    GROUP BY di.CustomerRefundID, di.SalesInvoiceID
),
PastDue AS (
    SELECT di.CustomerRefundID,
        SUM(di.GrandTotal - COALESCE(pt.Paid, 0)
            - COALESCE(ct.Credited, 0)) AS PastDue
    FROM DueInvoices AS di
        LEFT JOIN PaidThen AS pt
            ON pt.CustomerRefundID = di.CustomerRefundID
            AND pt.SalesInvoiceID = di.SalesInvoiceID
        LEFT JOIN CreditedThen AS ct
            ON ct.CustomerRefundID = di.CustomerRefundID
            AND ct.SalesInvoiceID = di.SalesInvoiceID
    WHERE di.GrandTotal - COALESCE(pt.Paid, 0)
        - COALESCE(ct.Credited, 0) > 0.005
    GROUP BY di.CustomerRefundID
),
Flags AS (
    SELECT rf.RefundNumber, rf.RefundDate, rf.CustomerID, rf.Amount,
        CASE WHEN rf.Amount > COALESCE(ra.MaxApprovalAmount, 0)
            THEN 1 ELSE 0 END AS AboveLimit,
        CASE WHEN cm.GrandTotal > COALESCE(ca.MaxApprovalAmount, 0)
            THEN 1 ELSE 0 END AS CreditAboveLimit,
        CASE WHEN EXISTS (
                SELECT 1
                FROM InvoiceMethods AS im
                WHERE im.SalesInvoiceID = cm.OriginalSalesInvoiceID
                    AND im.PaymentMethod = rf.PaymentMethod)
            THEN 0 ELSE 1 END AS MethodMismatch,
        CASE WHEN lp.LastPaymentDate > rf.RefundDate
            THEN 1 ELSE 0 END AS BeforePayment,
        COALESCE(pd.PastDue, 0) AS PastDue
    FROM CustomerRefund AS rf
        INNER JOIN Employee AS ra ON ra.EmployeeID = rf.ApprovedByEmployeeID
        INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
        INNER JOIN Employee AS ca ON ca.EmployeeID = cm.ApprovedByEmployeeID
        LEFT JOIN LastPayment AS lp
            ON lp.SalesInvoiceID = cm.OriginalSalesInvoiceID
        LEFT JOIN PastDue AS pd
            ON pd.CustomerRefundID = rf.CustomerRefundID
)
SELECT RefundNumber, RefundDate,
    CAST(strftime('%Y', RefundDate) AS INTEGER) AS FiscalYear,
    CustomerID, Amount, AboveLimit, CreditAboveLimit, MethodMismatch,
    BeforePayment, ROUND(PastDue, 2) AS PastDue,
    CASE WHEN PastDue >= Amount THEN 1 ELSE 0 END
        AS PastDueAtLeastRefund,
    CASE WHEN PastDue > 0 THEN 1 ELSE 0 END AS PastDueAny,
    AboveLimit + CreditAboveLimit + MethodMismatch + BeforePayment
        + CASE WHEN PastDue >= Amount THEN 1 ELSE 0 END AS Score
FROM Flags
ORDER BY RefundNumber;
"""


def sqlite_text(v) -> str:
    """A value as DB Browser's Export to CSV writes it: REAL with 15 significant digits (.0 kept on whole numbers)."""
    if isinstance(v, float):
        s = f"{v:.15g}"
        return s if any(ch in s for ch in ".e") else s + ".0"
    return str(v)


def refund_flags(d: Data) -> list[tuple]:
    rows = d.q(REFUND_FLAGS_SQL)
    c, t = ch19.cycle(d), ch19.tests(d)
    by_number = {r["num"]: k for k, r in c.rf.items()}
    claim(len(rows) == len(c.rf), "RefundFlags holds one row per refund")
    for r in rows:
        k = by_number[r[0]]
        claim([r[5], r[6], r[7], r[8], r[10]] == [int(x) for x in t.flags[k]] and r[12] == t.score[k]
              and abs(r[9] - round(t.pdue[k], 2)) < 0.001, f"{r[0]}: the exported flags equal the notes' definitions")
    return rows


def prepare(sources: dict) -> None:
    """Write RefundFlags.csv, the export of Credits.sql's refund flags, where the build reads it (read-only on the
    database)."""
    target = Path(sources.get(NEUTRAL_CSV, DEFAULT_CSV))
    target.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow([c for c, _ in FLAG_COLUMNS])
    for r in refund_flags(Data()):
        w.writerow([sqlite_text(v) for v in r])
    target.write_bytes(buf.getvalue().encode("utf-8"))


class CsvQuery(Query):
    """Home > Get data > Text/CSV: Source, Promoted Headers, and Changed Type. It always reads the neutral path; build.py
    points the verification copy at the built file."""

    @classmethod
    def csv(cls, name: str, columns: list[tuple[str, str]]) -> "CsvQuery":
        q = cls(name)
        q.columns = dict(columns)
        q.source = ("csv", columns)
        q._counts["Changed Type"] = 1
        return q

    def m(self, path: str) -> str:
        cols = self.source[1]
        return pq.steps_query([
            ("Source", f"Csv.Document(File.Contents({pq.m_string(NEUTRAL_CSV)}),[Delimiter=\",\", Columns={len(cols)}, "
                       "Encoding=65001, QuoteStyle=QuoteStyle.None])"),
            ("Promoted Headers", "Table.PromoteHeaders(Source, [PromoteAllScalars=true])"),
            ("Changed Type", f"Table.TransformColumnTypes(#\"Promoted Headers\",{pq.type_list(cols)})")] + self.steps)


@dataclass
class Build:
    xlsx: Path
    exp: Expected
    year: int
    sources: dict = field(default_factory=dict)        # neutral path -> real path of the other sources (also_sources)
    project: Project = None

    def __post_init__(self):
        self.project = Project(FILE, Model(FILE), Report())

    @property
    def model(self) -> Model:
        return self.project.model

    @property
    def report(self) -> Report:
        return self.project.report

    def check(self, section: str, label: str, expected, dax: str, tolerance: float = 0.005) -> None:
        self.project.check(section, label, expected, dax, tolerance)

    @cached_property
    def data(self) -> Data:
        return Data()


# --- report pieces -----------------------------------------------------------------------------------------------

def answer(name: str, x, y, w, h, title: str, lines: list, size: int = 10) -> Visual:
    return textbox(name, x, y, w, h, [(f"Model answer: {title}", True)] + lines, size=size)


def above(name: str, f: dict, value: float) -> dict:
    """Filters on this visual: show items when the measure is greater than `value`."""
    kind = next(iter(f))
    entity = f[kind]["Expression"]["SourceRef"]["Entity"]
    ref = {kind: {"Expression": {"SourceRef": {"Source": "k"}}, "Property": f[kind]["Property"]}}
    return {"name": name, "field": f, "type": "Advanced", "howCreated": "User",
            "filter": {"Version": 2, "From": [{"Name": "k", "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"Comparison": {"ComparisonKind": 1, "Left": ref,
                                                                 "Right": {"Literal": {"Value": f"{value}D"}}}}}]}}


NO_COLUMN_TOTALS = {"subTotals": [{"properties": {"columnSubtotals": lit(False)}}]}


def pct(x: float, places: int = 3) -> str:
    return f"{x:.{places}%}"


def yr(y: int) -> str:
    return f"'Date'[Year] = {y}"


# --- Requirement 5 -----------------------------------------------------------------------------------------------

def r5(b: Build) -> None:
    d, m, x = b.data, b.model, b.xlsx
    ctx = ch19.r5(d, claim)
    r4 = ch19.r4(d, claim)
    c, t = ch19.cycle(d), ch19.tests(d)
    y_c, years = d.C, d.years

    # Queries. Staging queries (Enable load cleared) feed the merges.
    emp = Query.navigator("Employee", x, 74, "Employee").select(["EmployeeID", "JobTitle", "MaxApprovalAmount"])
    wh = Query.navigator("Warehouse", x, 73, "Warehouse").select(["WarehouseID", "WarehouseName"])
    ship = (Query.navigator("Shipment", x, 14, "Shipment")
            .select(["ShipmentID", "ShipmentNumber", "ShipmentDate", "WarehouseID", "ShippedBy", "DeliveryDate"])
            .types({"ShipmentDate": "type date", "DeliveryDate": "type date"})
            .merge(wh, "WarehouseID", "WarehouseID", ["WarehouseName"]))
    ship_lines = (Query.navigator("ShipmentLine", x, 15, "ShipmentLine").select(["ShipmentLineID", "ShipmentID"])
                  .merge(ship, "ShipmentID", "ShipmentID",
                         ["ShipmentNumber", "ShipmentDate", "ShippedBy", "DeliveryDate", "WarehouseName"])
                  .rename({"ShippedBy": "Carrier", "WarehouseName": "Warehouse"}))
    returns = (Query.navigator("SalesReturn", x, 21, "SalesReturn")
               .select(["SalesReturnID", "ReturnNumber", "ReturnDate", "ReasonCode"]).types({"ReturnDate": "type date"}))
    return_lines = Query.navigator("SalesReturnLine", x, 22, "SalesReturnLine").select(["SalesReturnLineID", "ShipmentLineID"])
    invoices = (Query.navigator("SalesInvoice", x, 16, "SalesInvoice")
                .select(["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "CustomerID", "GrandTotal"])
                .types({"InvoiceDate": "type date", "DueDate": "type date"}))
    receipts = (Query.navigator("CashReceipt", x, 19, "CashReceipt")
                .select(["CashReceiptID", "ReceiptNumber", "ReceiptDate", "PaymentMethod", "RecordedByEmployeeID"])
                .types({"ReceiptDate": "type date"}))
    flags_q = (CsvQuery.csv("RefundFlags", FLAG_COLUMNS).select(["RefundNumber"] + FLAGS[:4] + ["PastDue", FLAGS[4], "Score"])
               .rename({"Score": "ExportedScore"}))         # the score Credits.sql exported, beside the one computed here
    # Loaded queries
    item = (Query.navigator("Item", x, 44, "Item").select(["ItemID", "ItemCode", "ItemName", "ItemGroup"])
            .custom("Family", "Text.Start([ItemCode], 7)", "type text"))
    customer = Query.navigator("Customer", x, 4, "Customer").select(
        ["CustomerID", "CustomerName", "CustomerSegment", "PaymentTerms"])
    cm = (Query.navigator("CreditMemo", x, 23, "CreditMemo")
          .select(["CreditMemoID", "CreditMemoNumber", "CreditMemoDate", "SalesReturnID", "CustomerID",
                   "OriginalSalesInvoiceID", "SubTotal", "GrandTotal", "Status", "ApprovedByEmployeeID"])
          .types({"CreditMemoDate": "type date"})
          .merge(returns, "SalesReturnID", "SalesReturnID", ["ReturnNumber", "ReturnDate", "ReasonCode"])
          .merge(emp, "ApprovedByEmployeeID", "EmployeeID", ["JobTitle"]).rename({"JobTitle": "ApproverTitle"}))
    lines = (Query.navigator("CreditMemoLine", x, 24, "CreditMemoLine")
             .select(["CreditMemoLineID", "CreditMemoID", "SalesReturnLineID", "ItemID", "Quantity", "LineTotal"])
             .merge(cm, "CreditMemoID", "CreditMemoID", ["CreditMemoNumber", "CreditMemoDate", "CustomerID", "ReturnDate",
                                                        "ReasonCode", "ApprovedByEmployeeID", "ApproverTitle"])
             .merge(return_lines, "SalesReturnLineID", "SalesReturnLineID", ["ShipmentLineID"])
             .merge(ship_lines, "ShipmentLineID", "ShipmentLineID",
                    ["ShipmentNumber", "ShipmentDate", "Carrier", "DeliveryDate", "Warehouse"])
             .custom("DaysAfterShipment", "Duration.Days([ReturnDate] - [ShipmentDate])", "Int64.Type")
             .custom("DaysAfterDelivery", "if [DeliveryDate] = null then null else Duration.Days([ReturnDate] - [DeliveryDate])",
                     "Int64.Type"))
    inv_lines = (Query.navigator("SalesInvoiceLine", x, 17, "SalesInvoiceLine")
                 .select(["SalesInvoiceLineID", "SalesInvoiceID", "ShipmentLineID", "ItemID", "LineTotal"])
                 .merge(invoices, "SalesInvoiceID", "SalesInvoiceID", ["InvoiceNumber", "InvoiceDate", "CustomerID"])
                 .merge(ship_lines, "ShipmentLineID", "ShipmentLineID", ["ShipmentDate"]))
    refunds = (Query.navigator("CustomerRefund", x, 25, "CustomerRefund")
               .select(["CustomerRefundID", "RefundNumber", "RefundDate", "CustomerID", "CreditMemoID", "Amount",
                        "PaymentMethod", "ApprovedByEmployeeID", "ClearedDate"])
               .types({"RefundDate": "type date", "ClearedDate": "type date"})
               .rename({"ApprovedByEmployeeID": "RefundApproverID"})
               .merge(emp, "RefundApproverID", "EmployeeID", ["JobTitle", "MaxApprovalAmount"])
               .rename({"JobTitle": "RefundApproverTitle", "MaxApprovalAmount": "RefundApproverLimit"})
               .merge(cm, "CreditMemoID", "CreditMemoID", ["CreditMemoNumber", "CreditMemoDate", "OriginalSalesInvoiceID",
                                                          "GrandTotal", "ReasonCode", "ApprovedByEmployeeID", "ApproverTitle"])
               .rename({"GrandTotal": "CreditTotal", "ApprovedByEmployeeID": "CreditApproverID",
                        "ApproverTitle": "CreditApproverTitle"})
               .merge(invoices, "OriginalSalesInvoiceID", "SalesInvoiceID", ["InvoiceNumber", "InvoiceDate", "DueDate",
                                                                            "GrandTotal"])
               .rename({"GrandTotal": "InvoiceTotal"}))
    apps = (Query.navigator("CashReceiptApplication", x, 20, "CashReceiptApplication")
            .select(["CashReceiptApplicationID", "CashReceiptID", "SalesInvoiceID", "ApplicationDate", "AppliedAmount",
                     "AppliedByEmployeeID"])
            .types({"ApplicationDate": "type date"})
            .merge(receipts, "CashReceiptID", "CashReceiptID", ["ReceiptNumber", "ReceiptDate", "PaymentMethod",
                                                                "RecordedByEmployeeID"])
            .merge(emp, "AppliedByEmployeeID", "EmployeeID", ["JobTitle"]).rename({"JobTitle": "AppliedByTitle"}))
    account = Query.navigator("Account", x, 1, "Account").select(["AccountID", "AccountNumber", "AccountName", "AccountType"])
    gl = (Query.navigator("GLEntry", x, 3, "GLEntry")
          .filter('[SourceDocumentType] = "CreditMemo" or [SourceDocumentType] = "CustomerRefund" or '
                  '[SourceDocumentType] = "SalesInvoice"')
          .select(["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType",
                   "SourceDocumentID"])
          .types({"PostingDate": "type date"}))

    none = lambda *cols: {k: "none" for k in cols}             # noqa: E731
    t_item = m.add(query_table(item, summarize=none("ItemID")))
    hide(t_item, "ItemID")
    t_cust = m.add(query_table(customer, summarize=none("CustomerID")))
    t_cm = m.add(query_table(cm, formats={"SubTotal": MONEY, "GrandTotal": MONEY},
                             summarize=none("CreditMemoID", "SalesReturnID", "CustomerID", "OriginalSalesInvoiceID",
                                            "ApprovedByEmployeeID")))
    hide(t_cm, "CreditMemoID", "SalesReturnID", "OriginalSalesInvoiceID")
    t_lines = m.add(query_table(lines, formats={"LineTotal": MONEY, "Quantity": "#,0.00"},
                                summarize=none("CreditMemoLineID", "CreditMemoID", "SalesReturnLineID", "ItemID",
                                               "CustomerID", "ApprovedByEmployeeID", "ShipmentLineID",
                                               "DaysAfterShipment", "DaysAfterDelivery")))
    hide(t_lines, "CreditMemoLineID", "CreditMemoID", "SalesReturnLineID", "ItemID", "CustomerID", "ShipmentLineID")
    t_il = m.add(query_table(inv_lines, formats={"LineTotal": MONEY},
                             summarize=none("SalesInvoiceLineID", "SalesInvoiceID", "ShipmentLineID", "ItemID", "CustomerID")))
    hide(t_il, "SalesInvoiceLineID", "SalesInvoiceID", "ShipmentLineID", "ItemID", "CustomerID")
    t_rf = m.add(query_table(refunds, formats={"Amount": MONEY, "CreditTotal": MONEY, "InvoiceTotal": MONEY,
                                              "RefundApproverLimit": MONEY},
                             summarize=none("CustomerRefundID", "CustomerID", "CreditMemoID", "RefundApproverID",
                                            "RefundApproverLimit", "CreditApproverID", "OriginalSalesInvoiceID")))
    hide(t_rf, "CustomerRefundID", "CreditMemoID", "OriginalSalesInvoiceID")
    # the score: one point a flag, a calculated column over the related row of RefundFlags (the CSV is related, not
    # merged, so Power Query never combines the two sources)
    t_rf.columns.append(Column("Score", "int64", expression=" + ".join(f"RELATED ( RefundFlags[{f}] )" for f in FLAGS),
                               fmt="0", summarize="none"))
    m.add(query_table(flags_q, formats={"PastDue": MONEY}, summarize=none(*FLAGS, "ExportedScore")))
    t_apps = m.add(query_table(apps, formats={"AppliedAmount": MONEY},
                               summarize=none("CashReceiptApplicationID", "CashReceiptID", "SalesInvoiceID",
                                              "AppliedByEmployeeID", "RecordedByEmployeeID")))
    hide(t_apps, "CashReceiptApplicationID", "CashReceiptID")
    t_acct = m.add(query_table(account, summarize=none("AccountID", "AccountNumber")))
    hide(t_acct, "AccountID")
    t_gl = m.add(query_table(gl, formats={"Debit": MONEY, "Credit": MONEY},
                             summarize=none("GLEntryID", "AccountID", "SourceDocumentID")))
    hide(t_gl, "GLEntryID", "AccountID", "SourceDocumentID")
    for q in (emp, wh, ship, ship_lines, returns, return_lines, invoices, receipts):
        m.stage(q)
    (date_body,) = dax_blocks("_tutorial-01.qmd", "table")       # the Date table of Tutorials 14.1 and 16.1
    (name, expr), = definitions(date_body)
    assert name == "Date"
    m.add(Table("Date", [
        Column("Date", "dateTime", source="[Date]", fmt="Short Date", extra=("isKey",)),
        Column("Year", "int64", source="[Year]"), Column("Quarter", "string", source="[Quarter]"),
        Column("YearQuarter", "string", source="[YearQuarter]"), Column("YearMonth", "string", source="[YearMonth]"),
        Column("MonthNumber", "int64", source="[MonthNumber]"),
        Column("MonthName", "string", source="[MonthName]", sort_by="MonthNumber")],
        dax=expr, props=("dataCategory: Time",)))
    for many, one_, active in [
            ("CreditMemoLine.CreditMemoDate", "Date.Date", True), ("CreditMemoLine.ShipmentDate", "Date.Date", False),
            ("CreditMemoLine.ItemID", "Item.ItemID", True), ("CreditMemoLine.CustomerID", "Customer.CustomerID", True),
            ("CreditMemo.CreditMemoDate", "Date.Date", True), ("CreditMemo.CustomerID", "Customer.CustomerID", True),
            ("SalesInvoiceLine.InvoiceDate", "Date.Date", True), ("SalesInvoiceLine.ShipmentDate", "Date.Date", False),
            ("SalesInvoiceLine.ItemID", "Item.ItemID", True), ("SalesInvoiceLine.CustomerID", "Customer.CustomerID", True),
            ("CustomerRefund.RefundDate", "Date.Date", True), ("CustomerRefund.CustomerID", "Customer.CustomerID", True),
            ("CustomerRefund.RefundNumber", "RefundFlags.RefundNumber", True),
            ("GLEntry.PostingDate", "Date.Date", True), ("GLEntry.AccountID", "Account.AccountID", True)]:
        m.relate(many, one_, active)
    # Enter data: the Flags table (the five flags in order; a disconnected table, as Tutorial 15.1's Steps), Key Measures
    ft = m.add(entered("Flags", [("Flag", "string"), ("Order", "int64")],
                       [[n, str(i + 1)] for i, n in enumerate(FLAG_NAMES)]))
    ft.column("Flag").sort_by = "Order"
    hide(ft, "Order")
    m.query_order.append("Flags")
    mt = m.add(entered(KM, [("Column1", "string")], []))
    m.query_order.append(KM)
    hide(mt, "Column1")
    switch = lambda base: ("SWITCH (\n    SELECTEDVALUE ( Flags[Flag] ),\n" + ",\n".join(          # noqa: E731
        f"    \"{n}\", CALCULATE ( {base}, RefundFlags[{f}] = 1 )" for n, f in zip(FLAG_NAMES, FLAGS)) + "\n)")
    paid = ("VAR Invoice = SELECTEDVALUE ( CustomerRefund[OriginalSalesInvoiceID] )\n"
            "VAR RefundDay = SELECTEDVALUE ( CustomerRefund[RefundDate] )\nRETURN\n"
            "    IF (\n        NOT ISBLANK ( Invoice ),\n        CALCULATE (\n"
            "            SUM ( CashReceiptApplication[AppliedAmount] ),\n"
            "            CashReceiptApplication[SalesInvoiceID] = Invoice,\n"
            "            CashReceiptApplication[ApplicationDate] <= RefundDay\n        ) + 0\n    )")
    later = "FILTER ( CreditMemoLine, YEAR ( CreditMemoLine[ReturnDate] ) > YEAR ( CreditMemoLine[ShipmentDate] ) )"
    measures = [
        # (folder, name, DAX, format, description)
        ("Returns", "Credits", "SUM ( CreditMemoLine[LineTotal] )", MONEY,
         "Credit memo lines at their line total (the credits' SubTotal, which posts to 4060)."),
        ("Returns", "Credit Lines", "COUNTROWS ( CreditMemoLine )", COUNT, "Credit memo lines."),
        ("Returns", "Credit Memos", "COUNTROWS ( CreditMemo )", COUNT, "Credit memos, by the credit memo date."),
        ("Returns", "Credit Memo Total", "SUM ( CreditMemo[GrandTotal] )", MONEY, "Credit memos at their grand total."),
        ("Returns", "Revenue", "SUM ( SalesInvoiceLine[LineTotal] )", MONEY, "Invoice lines at their line total."),
        ("Returns", "Return Rate", "DIVIDE ( [Credits], [Revenue] )", RATE,
         "Credits as a share of revenue, each by its own date (the month of the credit)."),
        ("Returns", "Credits by Ship Date", "CALCULATE ( [Credits], USERELATIONSHIP ( CreditMemoLine[ShipmentDate], "
                                           "'Date'[Date] ) )", MONEY, "Credits by the date the goods were shipped."),
        ("Returns", "Revenue by Ship Date", "CALCULATE ( [Revenue], USERELATIONSHIP ( SalesInvoiceLine[ShipmentDate], "
                                            "'Date'[Date] ) )", MONEY,
         "Revenue of the shipped lines by the date they were shipped (design services ship nothing)."),
        ("Returns", "Return Rate by Ship Date", "DIVIDE ( [Credits by Ship Date], [Revenue by Ship Date] )", RATE,
         "Credits on the goods shipped in a period as a share of the revenue of those shipments."),
        ("Returns", "Fewest Days after Shipment", "MIN ( CreditMemoLine[DaysAfterShipment] )", "0",
         "The shortest time from shipment to return, in days."),
        ("Returns", "Average Days after Shipment", "AVERAGE ( CreditMemoLine[DaysAfterShipment] )", "0.0",
         "The average time from shipment to return, in days (per credit line)."),
        ("Returns", "Most Days after Shipment", "MAX ( CreditMemoLine[DaysAfterShipment] )", "0",
         "The longest time from shipment to return, in days."),
        ("Returns", "Lines Returned in a Later Year", f"COUNTROWS ( {later} )", COUNT,
         "Credit lines whose goods came back in a later year than they were shipped."),
        ("Returns", "Credits Returned in a Later Year", f"CALCULATE ( [Credits], {later} )", MONEY,
         "Credits on goods that came back in a later year than they were shipped."),
        ("Refunds", "Refunds", "COUNTROWS ( CustomerRefund )", COUNT, "Customer refunds, by the refund date."),
        ("Refunds", "Refund Amount", "SUM ( CustomerRefund[Amount] )", MONEY, "Customer refunds paid."),
        ("Refunds", "Flagged Refunds", switch("[Refunds]"), COUNT,
         "The refunds with the flag on the row of the Flags table (RefundFlags.csv)."),
        ("Refunds", "Flagged Amount", switch("[Refund Amount]"), MONEY, "The amount of the refunds with the flag."),
        ("Refunds", "High-Score Refunds", "CALCULATE ( [Refunds], CustomerRefund[Score] >= 4 )", COUNT,
         "Refunds with four or five of the five flags: the first to review."),
        ("Refunds", "High-Score Amount", "CALCULATE ( [Refund Amount], CustomerRefund[Score] >= 4 )", MONEY,
         "The amount of the refunds that score 4 or 5."),
        ("Refunds", "Invoice Paid by Refund Date", paid, MONEY,
         "Receipts applied to the credited invoice on or before the refund date (one refund selected)."),
        ("Refunds", "Invoice Unpaid at Refund Date",
         "IF (\n    HASONEVALUE ( CustomerRefund[RefundNumber] ),\n"
         "    SELECTEDVALUE ( CustomerRefund[InvoiceTotal] ) - [Invoice Paid by Refund Date]\n)", MONEY,
         "The credited invoice's total less the receipts applied by the refund date (one refund selected)."),
        ("Refunds", "Applied to the Invoice", "CALCULATE (\n    SUM ( CashReceiptApplication[AppliedAmount] ),\n"
                                             "    TREATAS ( VALUES ( CustomerRefund[OriginalSalesInvoiceID] ), "
                                             "CashReceiptApplication[SalesInvoiceID] )\n)", MONEY,
         "Receipts applied to the invoices the refunds selected credited (the receipts table has no relationship)."),
        ("Validation", "Ledger Credits 4060", "CALCULATE (\n    SUM ( GLEntry[Debit] ),\n    Account[AccountNumber] = 4060,\n"
                                              "    GLEntry[SourceDocumentType] = \"CreditMemo\"\n)", MONEY,
         "Debits of credit memos to 4060 Sales Returns and Allowances (the closes are not loaded)."),
        ("Validation", "Credits less 4060", "[Credits] - [Ledger Credits 4060]", MONEY, "Must be zero in every year."),
        ("Validation", "Credit Memo Subtotal", "SUM ( CreditMemo[SubTotal] )", MONEY, "Credit memos at their SubTotal."),
        ("Validation", "Ledger Refunds 1010", "CALCULATE (\n    SUM ( GLEntry[Credit] ),\n    Account[AccountNumber] = 1010,\n"
                                              "    GLEntry[SourceDocumentType] = \"CustomerRefund\"\n)", MONEY,
         "Credits of customer refunds to cash, 1010."),
        ("Validation", "Refunds Flagged", "COUNTROWS ( FILTER ( CustomerRefund, NOT ISBLANK ( RELATED ( RefundFlags[ExportedScore] ) ) ) )",
         COUNT, "Refunds that found their row of RefundFlags.csv."),
        ("Validation", "Scores Different", "COUNTROWS ( FILTER ( CustomerRefund, CustomerRefund[Score] <> "
                                           "RELATED ( RefundFlags[ExportedScore] ) ) ) + 0", COUNT,
         "Refunds whose score here differs from the score Credits.sql exported: must be zero."),
    ]
    mt.measures += [Measure(n, dax, fmt, desc, display_folder=folder) for folder, n, dax, fmt, desc in measures]

    # the expected values ---------------------------------------------------------------------------------------
    sales_year = dict(d.q("SELECT CAST(substr(si.InvoiceDate, 1, 4) AS INTEGER), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                          "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID GROUP BY 1"))
    cred_year = dict(d.q("SELECT CAST(substr(cm.CreditMemoDate, 1, 4) AS INTEGER), SUM(l.LineTotal) FROM CreditMemoLine l "
                         "JOIN CreditMemo cm ON cm.CreditMemoID = l.CreditMemoID GROUP BY 1"))
    rate_year = {y: cred_year[y] / sales_year[y] for y in years}
    group_sales = {(g, y): v for g, y, v in d.q(
        "SELECT i.ItemGroup, CAST(substr(si.InvoiceDate, 1, 4) AS INTEGER), SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN "
        "SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID GROUP BY 1, 2")}
    top = ctx["top"]
    prefix = d.one("SELECT DISTINCT substr(ItemCode, 1, 3) FROM Item WHERE ItemGroup = ?", top)
    fam_sales = dict(d.q("SELECT substr(i.ItemCode, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON "
                         "si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID WHERE si.InvoiceDate "
                         "BETWEEN ? AND ? GROUP BY 1", f"{y_c}-01-01", f"{y_c}-12-31"))
    lines_ = ch19.credit_lines(d)
    carriers = Counter(l["carrier"] for l in lines_ if l["reason"] == "Damaged")
    whs = dict(d.q("SELECT WarehouseID, WarehouseName FROM Warehouse"))
    by_wh = Counter(whs[l["warehouse"]] for l in lines_)
    big = ch19.largest_refund(d)
    big_k = big["id"]
    big_cm = c.cm[big["cm"]]
    big_inv = c.inv[big_cm["inv"]]
    big_apps = sorted(c.apps[big_inv["id"]])
    paid_then = sum(a[1] for a in big_apps if a[0] <= big["date"])
    nothing = [r for r in c.rf.values() if not any(a[0] <= r["date"] for a in c.apps[c.cm[r["cm"]]["inv"]])]
    months_ship = {}                                                    # the C months by shipment month
    ship_rev = defaultdict(float)
    for day, lt in d.q("SELECT s.ShipmentDate, sil.LineTotal FROM SalesInvoiceLine sil JOIN ShipmentLine sl ON "
                       "sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID"):
        ship_rev[day[:7]] += lt
    ret_ship = defaultdict(float)
    for l in lines_:
        ret_ship[l["ship_date"][:7]] += l["total"]
    for k in sorted(ship_rev):
        if int(k[:4]) == y_c:
            months_ship[k] = (ret_ship[k], ship_rev[k], ret_ship[k] / ship_rev[k])
    dec_key = f"{y_c}-12"
    hi_ids = [k for k, s in t.score.items() if s >= 4]
    focus = ctx["focus"]
    focus_name = d.one("SELECT CustomerName FROM Customer WHERE CustomerID = ?", focus)
    titles = sorted({c.emp[r["appr"]]["title"] for r in c.rf.values()})
    rf_titles = {(ti, y): sum(1 for r in c.rf.values() if c.emp[r["appr"]]["title"] == ti and int(r["date"][:4]) == y)
                 for ti in titles for y in years}
    claim([[rf_titles[(ti, y)] for y in years] for ti in titles] == [xs for _, xs in ctx["approvers"]],
          "the note's refund approvers by year are the job titles in name order")
    flag_rows = {f: [r for k, r in c.rf.items() if t.flags[k][i]] for i, f in enumerate(FLAGS)}
    last_credit, last_refund = max(m_["date"] for m_ in c.cm.values()), max(r["date"] for r in c.rf.values())
    last_ship = d.one("SELECT MAX(ShipmentDate) FROM Shipment")

    # About --------------------------------------------------------------------------------------------------------
    about = b.report.add(Page("about", "About"))
    about.add(textbox("aboutText", 20, 20, 1240, 520, [
        (FILE, True),
        "Purpose: the returns analytics and the refund ranking of the audit of the customer credits cycle (Requirement "
        f"5), for the audit committee: where returns grow and which refunds deserve a second look, from fiscal "
        f"{years[0]} to {years[-1]}.",
        "Return rate: the credits (credit memo lines at their line total, the SubTotal that posts to 4060) as a share "
        "of revenue (invoice lines). By the month of the credit, each is read by its own document date; by the month of "
        "the shipment, both are read by the date the goods were shipped, through inactive relationships to Date that "
        "the measures switch on with USERELATIONSHIP. Design services ship nothing, so revenue by ship date leaves them out.",
        f"Refund flags: RefundFlags.csv, the export of the refund flags of Credits.sql (Requirement 4), related to the "
        "refunds by RefundNumber (a relationship, so Power Query never combines the CSV with the workbook). Each refund scores one point for each flag: refund above the approver's authority, credit above "
        "the approver's authority, a refund method unlike the receipts on the credited invoice, a refund dated before "
        "the customer's last payment on the invoice, and a past-due balance on the refund date at least as large as "
        "the refund. The report recomputes the score and the Validation page compares it with the export.",
        "Drill-through: on the Refund Ranking page, right-click a refund and choose Drill through > Refund Detail to see "
        "its credit, its invoice, and the receipts applied to that invoice (CashReceiptApplication has no relationship; "
        "the measure Applied to the Invoice reads it through TREATAS).",
        f"Data: CharlesRiver.xlsx (credits through {last_credit}, refunds through {last_refund}, shipments through "
        f"{last_ship}); GLEntry is loaded only for the credit memo, refund, and sales invoice postings, so the "
        "year-end closes are left out. People appear by job title and employee ID."], size=11))
    about.add(Visual("pageNavigator", "pageNavigator", 20, 560, 1240, 60, objects={"pages": [{"properties": {
        "showHiddenPages": lit(False), "showTooltipPages": lit(False)}}]}))
    about.expect = [FILE, "Returns", "Refund Ranking", last_credit]
    b.report.active = "about"

    # Returns ------------------------------------------------------------------------------------------------------
    year_col, group_col = col("Date", "Year"), col("Item", "ItemGroup")
    reason_col = col("CreditMemoLine", "ReasonCode")
    page = b.report.add(Page("returns", "Returns"))
    page.add(Visual("byYear", "tableEx", 20, 20, 600, 130, {"Values": [
        year_col, M("Credit Lines"), M("Credits"), M("Revenue"), M("Return Rate")]},
        title="Credits and return rate by year of the credit"))
    page.add(Visual("byGroup", "pivotTable", 640, 20, 620, 180, {
        "Rows": [group_col], "Columns": [year_col], "Values": [M("Credits"), M("Return Rate")]},
        title="By item group", objects=NO_COLUMN_TOTALS))
    page.add(Visual("byReason", "pivotTable", 20, 165, 600, 190, {
        "Rows": [reason_col], "Columns": [year_col], "Values": [M("Credits")]}, title="By reason"))
    page.add(Visual("families", "tableEx", 640, 215, 620, 175, {"Values": [
        col("Item", "Family"), M("Credits"), M("Revenue"), M("Return Rate")]},
        title=f"{top} families, fiscal {y_c}", sort=[(M("Credits"), "Descending")],
        filters=[keep("famGroup", group_col, [top]), keep("famYear", year_col, [y_c])]))
    page.add(Visual("damaged", "pivotTable", 20, 370, 600, 170, {
        "Rows": [group_col], "Columns": [year_col], "Values": [M("Credits")]},
        title="Credits coded Damaged, by item group", filters=[keep("dmgReason", reason_col, ["Damaged"])]))
    page.add(Visual("bySegment", "pivotTable", 640, 405, 620, 135, {
        "Rows": [col("Customer", "CustomerSegment")], "Columns": [year_col], "Values": [M("Credits")]},
        title="By customer segment"))
    g_first, g_last = ctx["by_group"][0][1], ctx["by_group"]
    fams = ", ".join(f"{prefix}-{f} {money(v)}" for f, v in ctx["families"])
    page.add(answer("returnsAnswer", 20, 555, 1240, 160, "where returns grow", [
        f"Credits grew from {money(cred_year[years[0]])} to {money(cred_year[years[-1]])} while revenue grew from "
        f"{money(sales_year[years[0]])} to {money(sales_year[years[-1]])}: a return rate of "
        + " / ".join(pct(rate_year[y]) for y in years) + f". {top} carries the growth: {money(g_first[0])} to "
        f"{money(g_first[-1])}, " + " / ".join(pct(v) for v in ctx["top_rates"]) + f" of its revenue (account "
        f"{ctx['top_account']}), while " + ", ".join(f"{g} {money(xs[0])} to {money(xs[-1])}" for g, xs in g_last[1:]) + ".",
        f"Damaged returns rose from {money(ctx['damaged'][0])} to {money(ctx['damaged'][-1])}, and {top}'s from "
        f"{money(ctx['top_damaged'][0])} to {money(ctx['top_damaged'][-1])}: the reason to follow up with the warehouse "
        f"and the carriers. In fiscal {y_c} the largest {top} families are {fams}. By segment, {ctx['top_segment']} "
        "customers return the most (" + " / ".join(money(v) for v in ctx["segment"]) + ")."]))
    page.expect = ["Return Rate", "Damaged", f"{prefix}-{ctx['families'][0][0]}", money(g_first[-1]),
                   pct(rate_year[years[-1]]), money(ctx["damaged"][-1]), money(ctx["segment"][-1])]

    # Timing -------------------------------------------------------------------------------------------------------
    page = b.report.add(Page("timing", "Timing"))
    ym = col("Date", "YearMonth")
    page.add(Visual("rateByMonth", "lineChart", 20, 20, 800, 330, {
        "Category": [ym], "Y": [M("Return Rate"), M("Return Rate by Ship Date")]},
        title="Return rate by month of the credit and by month of the shipment",
        alt_text="Two lines by month. By the month of the credit, the first months of the first year are low because "
                 "nothing had been sold long enough to come back; by the month of the shipment, the last month falls "
                 "close to zero because its returns arrive after the data end."))
    page.add(Visual("rateYears", "tableEx", 840, 20, 420, 130, {"Values": [
        year_col, M("Return Rate"), M("Return Rate by Ship Date")]}, title="Return rate by year"))
    page.add(Visual("shipMonths", "tableEx", 840, 165, 420, 360, {"Values": [
        ym, M("Credits by Ship Date"), M("Revenue by Ship Date"), M("Return Rate by Ship Date")]},
        title=f"Fiscal {y_c} by month of the shipment", filters=[keep("smYear", year_col, [y_c])]))
    page.add(card("lagCards", 20, 365, 800, 110, [
        M("Fewest Days after Shipment"), M("Average Days after Shipment"), M("Most Days after Shipment"),
        M("Lines Returned in a Later Year"), M("Credits Returned in a Later Year")], units_none=True))
    lag = ctx["lag"]
    others = [v[2] for k, v in months_ship.items() if k != dec_key]
    page.add(answer("timingAnswer", 20, 490, 800, 225, "why the last months and the first year mislead", [
        f"Returns come {lag['lo']} to {lag['hi']} days after shipment (mean {lag['mean']:.1f}; {lag['dlo']} to "
        f"{lag['dhi']} after delivery), so a period's credits belong to earlier shipments. Fiscal {years[0]} had no "
        f"earlier sales to return: by the month of the credit its first months are low and its rate, "
        f"{pct(rate_year[years[0]])}, understates. At the other end, the shipments of December {y_c} show "
        f"{pct(ctx['dec'], 2)}, against {pct(min(others), 2)} to {pct(max(others), 2)} for the other months of {y_c}, "
        "because their returns arrive after the data end: censored, not good news.",
        f"By the year of the shipment the rates are " + " / ".join(pct(v) for v in ctx["by_ship_year"]) +
        f"; {ctx['cross']} return lines ({money(ctx['cross_amt'])}) came back in a later year than they shipped, and "
        f"fiscal {years[0]} has no carry-in from {years[0] - 1}. Compare rates over complete windows: by the month of "
        f"the shipment, leaving out the last month or two, and not against fiscal {years[0]}'s first months."]))
    page.expect = ["Return Rate by Ship Date", dec_key, pct(ctx["dec"]), pct(ctx["by_ship_year"][-1]),
                   f"Average Days after Shipment, {lag['mean']:.1f} card", money(ctx["cross_amt"])]

    # Concentration --------------------------------------------------------------------------------------------------
    page = b.report.add(Page("concentration", "Concentration"))
    page.add(Visual("carriers", "pivotTable", 20, 20, 620, 175, {
        "Rows": [col("CreditMemoLine", "Carrier")], "Columns": [reason_col], "Values": [M("Credit Lines")]},
        title="Credit lines by carrier and reason"))
    page.add(Visual("warehouses", "tableEx", 660, 20, 600, 110, {"Values": [
        col("CreditMemoLine", "Warehouse"), M("Credit Lines"), M("Credits")]}, title="By warehouse that shipped"))
    page.add(card("overall", 660, 140, 600, 55, [(M("Return Rate"), "Credits on sales, all customers")], units_none=True))
    page.add(Visual("customers", "tableEx", 20, 210, 820, 500, {"Values": [
        col("Customer", "CustomerID"), col("Customer", "CustomerName"), col("Customer", "CustomerSegment"), M("Credits"),
        M("Revenue"), M("Return Rate"), M("Credit Memos"), M("Refunds")]},
        title="Customers by credits as a share of their sales (all three years)", sort=[(M("Return Rate"), "Descending")],
        filters=[above("custCredits", M("Credits"), 0)]))
    higher = ctx["higher"]
    small = sum(1 for _, _, s in higher if s < ctx["focus_sales"] / 10)
    page.add(answer("concAnswer", 860, 210, 400, 500, "concentration", [
        f"No concentration by carrier (Damaged lines {ctx['car_lo']} to {ctx['car_hi']} per carrier) or by warehouse "
        f"({' and '.join(f'{n:,}' for n in ctx['warehouses'])} lines).",
        f"By customer, as a share of each customer's sales: customer {focus}, {focus_name} ({ctx['seg']}, "
        f"{ctx['terms']}), has the largest credits, {money(ctx['focus_cred'])} on sales of {money(ctx['focus_sales'])}, "
        f"{pct(ctx['rate'], 2)} against {pct(ctx['overall'])} for all customers: {ctx['focus_n']} credits "
        f"({money(ctx['focus_gt'])}), {ctx['top_two']} of them approved by {ctx['two']}, and {ctx['focus_rf']} refunds "
        f"({money(ctx['focus_rf_amt'])}), {'all' if ctx['focus_before'] == ctx['focus_rf'] else ctx['focus_before']} "
        "dated before the customer's payment.",
        "Customers " + ", ".join(f"{k} ({pct(r, 2)} on sales of {money(s)})" for k, r, s in higher) +
        f" rank higher by rate, {small} of them on sales under a tenth of customer {focus}'s, so the rate alone "
        f"overstates small customers. Customer {focus} is the one to follow up: the credits, their approvers, and the "
        "refunds paid before the customer paid."]))
    page.expect = ["Carrier", "Warehouse", "CustomerName", f"{higher[0][1]:.3%}", f"{ctx['rate']:.3%}",
                   money(ctx["focus_cred"]), f"{ctx['overall']:.3%} card"]

    # Refund Ranking -------------------------------------------------------------------------------------------------
    page = b.report.add(Page("ranking", "Refund Ranking"))
    score = col("CustomerRefund", "Score")
    page.add(Visual("scores", "clusteredBarChart", 20, 20, 300, 300, {"Category": [score], "Y": [M("Refunds")]},
                    sort=[(score, "Ascending")], title="Refunds by score (one point a flag)",
                    alt_text="Bars of the number of refunds at each score from 0 to 5; most refunds score 2 to 4."))
    page.add(Visual("flagYears", "pivotTable", 340, 20, 920, 180, {
        "Rows": [col("Flags", "Flag")], "Columns": [year_col], "Values": [M("Flagged Refunds"), M("Flagged Amount")]},
        title="Refunds by flag and year (RefundFlags.csv)"))
    page.add(Visual("approvers", "pivotTable", 340, 215, 600, 105, {
        "Rows": [col("CustomerRefund", "RefundApproverTitle")], "Columns": [year_col], "Values": [M("Refunds")]},
        title="Refunds by approver's job title"))
    page.add(card("highCards", 960, 215, 300, 105, [M("High-Score Refunds"), M("High-Score Amount")], units_none=True))
    rf_cols = [col("CustomerRefund", "RefundNumber"), col("CustomerRefund", "RefundDate"), col("CustomerRefund", "CustomerID"),
               (agg("CustomerRefund", "Amount"), "Amount")] + [(col("RefundFlags", f), n) for f, n in zip(FLAGS, FLAG_NAMES)] + [
               score]
    page.add(Visual("refunds", "tableEx", 20, 335, 1240, 240, {"Values": rf_cols},
                    title="Every refund, by score (right-click a refund: Drill through > Refund Detail)",
                    sort=[(score, "Descending"), (agg("CustomerRefund", "Amount"), "Descending")]))
    sc = ctx["scores"]
    page.add(answer("rankAnswer", 20, 590, 1240, 125, "the ranking", [
        f"Scores 0 to 5: {', '.join(str(n) for n in sc)} refunds. The {ctx['hi']} refunds that score 4 or 5 "
        f"({money(ctx['hi_amt'])}) are the first to review, with the documents outside the database (the customer's "
        f"request, the payee, the inspection). The largest refund, {ctx['big']}, scores {ctx['big_score']} (its "
        f"approver was {'above' if ctx['big_above'] else 'within'} limit). Refund approvers by year: "
        + "; ".join(f"{ti} {' / '.join(str(v) for v in xs)}" for ti, xs in ctx["approvers"]) +
        f". Weekend dates are spread evenly ({ctx['weekend_rf']} refunds, {ctx['weekend_cm']} credits), so they are not "
        "a useful flag here."]))
    page.expect = ["Refunds by score", "Refund above authority", "Past due at least the refund",
                   f"{len(flag_rows['AboveLimit']):,}", money(r4["rf_above"]["amt"]),
                   f"High-Score Refunds, {ctx['hi']} card", f"High-Score Amount, {money(ctx['hi_amt'])} card"]

    # Refund Detail (drill-through, as left after drilling through on the largest refund) ----------------------------
    page = b.report.add(Page("refundDetail", "Refund Detail"))
    drillthrough(page, col("CustomerRefund", "RefundNumber"), big["num"])
    R = lambda f: col("CustomerRefund", f)         # noqa: E731
    page.add(Visual("refund", "tableEx", 80, 20, 1180, 75, {"Values": [
        R("RefundNumber"), R("RefundDate"), R("PaymentMethod"), R("RefundApproverID"), R("RefundApproverTitle"),
        (R("RefundApproverLimit"), "Approver limit"), (agg("CustomerRefund", "Amount"), "Amount"), R("ClearedDate"),
        score]}, title="The refund"))
    page.add(Visual("flags", "tableEx", 80, 105, 1180, 75, {"Values": [R("RefundNumber")] + [
        (col("RefundFlags", f), n) for f, n in zip(FLAGS, FLAG_NAMES)] + [
        (col("RefundFlags", "PastDue"), "Past due on the refund date")]},
        title="Its flags (RefundFlags.csv)"))
    page.add(Visual("credit", "tableEx", 20, 190, 1240, 75, {"Values": [
        R("CreditMemoNumber"), R("CreditMemoDate"), R("ReasonCode"), R("CreditApproverID"), R("CreditApproverTitle"),
        (agg("CustomerRefund", "CreditTotal"), "Credit total")]}, title="Its credit"))
    page.add(Visual("invoice", "tableEx", 20, 275, 1240, 75, {"Values": [
        R("InvoiceNumber"), R("InvoiceDate"), R("DueDate"), (agg("CustomerRefund", "InvoiceTotal"), "Invoice total"),
        M("Invoice Paid by Refund Date"), M("Invoice Unpaid at Refund Date")]}, title="Its invoice"))
    A = lambda f: col("CashReceiptApplication", f)  # noqa: E731
    page.add(Visual("receipts", "tableEx", 20, 360, 1240, 190, {"Values": [
        A("ReceiptNumber"), A("ReceiptDate"), A("PaymentMethod"), A("RecordedByEmployeeID"), A("ApplicationDate"),
        A("AppliedByEmployeeID"), A("AppliedByTitle"), M("Applied to the Invoice")]},
        title="Receipts applied to the credited invoice", sort=[(A("ApplicationDate"), "Ascending")]))
    first_after = next((a for a in big_apps if a[0] > big["date"]), None)
    page.add(answer("detailAnswer", 20, 560, 1240, 155, f"{big['num']}, the largest refund", [
        f"{big['num']} ({money(big['amt'])}, {big['method']}, dated {big['date']}, approved by the "
        f"{c.emp[big['appr']]['title']}) refunds {big_cm['num']} ({money(big_cm['gt'])}, approved on {big_cm['date']} by "
        f"{ch19.title_of(d, big_cm['appr']).lower()} {big_cm['appr']} with a limit of {c.emp[big_cm['appr']]['limit']:,.0f}). "
        f"Its invoice, {big_inv['num']} ({money(big_inv['gt'])}, due {big_inv['due']}), had received "
        f"{money(paid_then)} by the refund date, so {money(big_inv['gt'] - paid_then)} was unpaid when the refund was paid"
        + (f"; the next receipt was applied on {first_after[0]}." if first_after else "."),
        f"It scores {t.score[big_k]} of 5. Disposition: follow up, not a conclusion. The evidence that would settle it lies "
        "outside the database: the wire confirmation's beneficiary and account against the customer's known bank "
        "details, a confirmation from the customer, the receiving and inspection record, and the customer's request."]))
    page.expect = [big["num"], money(big["amt"]), big_cm["num"], big_inv["num"], money(big_inv["gt"] - paid_then),
                   money(paid_then), c.rcpt[big_apps[0][3]]["num"]]

    # Validation -----------------------------------------------------------------------------------------------------
    page = b.report.add(Page("validation", "Validation"))
    page.add(Visual("tieOut", "tableEx", 20, 20, 1240, 150, {"Values": [
        year_col, M("Credits"), M("Credit Memo Subtotal"), M("Ledger Credits 4060"), M("Credits less 4060"),
        M("Refund Amount"), M("Ledger Refunds 1010")]}, title="Credits to 4060 and refunds to 1010, by year (Tests 1 and 2)"))
    page.add(card("flagCards", 20, 185, 1240, 100, [M("Refunds"), M("Refunds Flagged"), M("Scores Different"),
                                                    M("Credit Lines"), M("Credit Memos")], units_none=True))
    l4060 = {y: ch19.gl_year(d, "CreditMemo", "4060", y, "Dr") for y in years}
    l1010 = {y: ch19.gl_year(d, "CustomerRefund", "1010", y, "Cr") for y in years}
    rf_year = {y: sum(r["amt"] for r in c.rf.values() if int(r["date"][:4]) == y) for y in years}
    page.add(answer("valAnswer", 20, 300, 1240, 150, "what the totals mean", [
        "The credits equal the debits of credit memos to 4060 in every year (" +
        "; ".join(f"{y} {money(l4060[y])}" for y in years) + "), and the refunds the credits of refunds to cash (" +
        "; ".join(f"{y} {money(l1010[y])}" for y in years) + "): the populations the analytics read are complete. "
        "GLEntry holds only the credit memo, refund, and sales invoice postings, so the year-end closes, which also post "
        "to 4060, are left out.",
        f"Every one of the {len(c.rf)} refunds found its row of RefundFlags.csv, and the score recomputed here equals the "
        "score Credits.sql exported."]))
    page.expect = [money(l4060[years[-1]]), money(l1010[years[-1]]), f"Refunds Flagged, {len(c.rf)} card",
                   "Scores Different, 0 card"]

    # The Tests tab ------------------------------------------------------------------------------------------------
    tests = [
        ("Test 1: the credits must tie to account 4060 by year (credit memo postings; the closes are not loaded)",
         "SUMMARIZECOLUMNS (\n    'Date'[Year],\n    \"Credits\", ROUND ( [Credits], 2 ),\n"
         "    \"Credit memo subtotal\", ROUND ( [Credit Memo Subtotal], 2 ),\n"
         "    \"Ledger 4060\", ROUND ( [Ledger Credits 4060], 2 ),\n"
         "    \"Difference\", ROUND ( [Credits less 4060], 2 )\n)", "'Date'[Year]", len(years)),
        ("Test 2: the refunds must tie to the credits of refunds to cash, 1010, by year",
         "SUMMARIZECOLUMNS (\n    'Date'[Year],\n    \"Refunds\", [Refunds],\n"
         "    \"Refund amount\", ROUND ( [Refund Amount], 2 ),\n    \"Ledger 1010\", ROUND ( [Ledger Refunds 1010], 2 )\n)",
         "'Date'[Year]", len(years)),
        ("Test 3: every refund must find its flags in RefundFlags.csv, with the same score",
         "ROW (\n    \"Refunds\", [Refunds],\n    \"With flags\", [Refunds Flagged],\n"
         "    \"Scores different\", [Scores Different]\n)", None, 1),
    ]
    b.project.queries["Tests"] = "\n\n".join(
        f"// {c_}\nEVALUATE\n{expr}" + (f"\nORDER BY {order}" if order else "") for c_, expr, order, _ in tests) + "\n"

    # checks ------------------------------------------------------------------------------------------------------
    s = "Requirement 5"
    n_gl = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType IN ('CreditMemo', 'CustomerRefund', 'SalesInvoice')")
    for label, n, table in (("CreditMemoLine rows", len(lines_), "CreditMemoLine"), ("CreditMemo rows", len(c.cm), "CreditMemo"),
                            ("CustomerRefund rows", len(c.rf), "CustomerRefund"),
                            ("SalesInvoiceLine rows", d.one("SELECT COUNT(*) FROM SalesInvoiceLine"), "SalesInvoiceLine"),
                            ("CashReceiptApplication rows", sum(len(v) for v in c.apps.values()), "CashReceiptApplication"),
                            ("GLEntry rows (credit memo, refund, and sales invoice postings)", n_gl, "GLEntry"),
                            ("Item rows", d.one("SELECT COUNT(*) FROM Item"), "'Item'"),
                            ("Customer rows", d.one("SELECT COUNT(*) FROM Customer"), "Customer")):
        b.check(s, label, n, f"COUNTROWS ( {table} )", 0)
    b.check(s, "credit lines without a shipment", 0,
            "COUNTROWS ( FILTER ( CreditMemoLine, ISBLANK ( CreditMemoLine[ShipmentDate] ) ) )", 0)
    b.check(s, "credit lines without a reason", 0,
            "COUNTROWS ( FILTER ( CreditMemoLine, ISBLANK ( CreditMemoLine[ReasonCode] ) ) )", 0)
    b.check(s, "refunds with their flags (Test 3)", len(c.rf), "[Refunds Flagged]", 0)
    b.check(s, "scores different from the export (Test 3)", 0, "[Scores Different]", 0)
    b.check(s, "refunds without their invoice", 0,
            "COUNTROWS ( FILTER ( CustomerRefund, ISBLANK ( CustomerRefund[InvoiceNumber] ) ) )", 0)
    for y in years:
        b.check(s, f"Test 1: {y} credits equal 4060", round(l4060[y], 2), f"CALCULATE ( [Credits], {yr(y)} )")
        b.check(s, f"Test 1: {y} 4060 debits of credit memos", round(l4060[y], 2), f"CALCULATE ( [Ledger Credits 4060], {yr(y)} )")
        b.check(s, f"Test 1: {y} credits less 4060", 0, f"CALCULATE ( [Credits less 4060], {yr(y)} )")
        b.check(s, f"Test 2: {y} refunds equal 1010", round(rf_year[y], 2), f"CALCULATE ( [Ledger Refunds 1010], {yr(y)} )")
        b.check(s, f"{y} revenue (invoice lines)", round(sales_year[y], 2), f"CALCULATE ( [Revenue], {yr(y)} )")
        b.check(s, f"{y} return rate by the year of the credit", round(rate_year[y], 9),
                f"CALCULATE ( [Return Rate], {yr(y)} )", 1e-7)
    for g, xs in ctx["by_group"]:
        for y, v in zip(years, xs):
            gy = f"'Item'[ItemGroup] = \"{g}\", {yr(y)}"
            b.check(s, f"{g} credits {y}", v, f"CALCULATE ( [Credits], {gy} )")
            b.check(s, f"{g} return rate {y} (invoice lines)", round(v / group_sales[(g, y)], 9),
                    f"CALCULATE ( [Return Rate], {gy} )", 1e-7)
    for y, v in zip(years, ctx["top_rates"]):
        b.check(s, f"{top} return rate {y}, in percent to three decimals (the note's rate of {ctx['top_account']})",
                round(100 * v, 3), f"ROUND ( 100 * CALCULATE ( [Return Rate], 'Item'[ItemGroup] = \"{top}\", {yr(y)} ), 3 )", 0)
    for y, v, w in zip(years, ctx["damaged"], ctx["top_damaged"]):
        b.check(s, f"Damaged credits {y}", v, f"CALCULATE ( [Credits], CreditMemoLine[ReasonCode] = \"Damaged\", {yr(y)} )")
        b.check(s, f"{top} Damaged credits {y}", w, f"CALCULATE ( [Credits], CreditMemoLine[ReasonCode] = \"Damaged\", "
                                                   f"'Item'[ItemGroup] = \"{top}\", {yr(y)} )")
    ff = f"'Item'[ItemGroup] = \"{top}\", {yr(y_c)}"
    for f, v in ctx["families"]:
        b.check(s, f"{top} family {prefix}-{f} credits {y_c}", v, f"CALCULATE ( [Credits], 'Item'[Family] = \"{prefix}-{f}\", {yr(y_c)} )")
        b.check(s, f"{top} family {prefix}-{f} return rate {y_c}", round(v / fam_sales[f"{prefix}-{f}"], 9),
                f"CALCULATE ( [Return Rate], 'Item'[Family] = \"{prefix}-{f}\", {yr(y_c)} )", 1e-7)
    b.check(s, f"the {len(ctx['families'])} largest {top} families of {y_c}, by credits",
            ", ".join(f"{prefix}-{f}" for f, _ in ctx["families"]),
            f"CALCULATE ( CONCATENATEX ( TOPN ( {len(ctx['families'])}, FILTER ( VALUES ( 'Item'[Family] ), NOT ISBLANK ( "
            f"[Credits] ) ), [Credits], DESC ), 'Item'[Family], \", \", [Credits], DESC ), {ff} )")
    for y, v in zip(years, ctx["segment"]):
        b.check(s, f"{ctx['top_segment']} credits {y}", v,
                f"CALCULATE ( [Credits], Customer[CustomerSegment] = \"{ctx['top_segment']}\", {yr(y)} )")
    b.check(s, "the segment with the most credits", ctx["top_segment"],
            "CONCATENATEX ( TOPN ( 1, VALUES ( Customer[CustomerSegment] ), [Credits], DESC ), Customer[CustomerSegment] )")
    for carrier, n in sorted(carriers.items()):
        b.check(s, f"Damaged lines shipped by {carrier}", n,
                f"CALCULATE ( [Credit Lines], CreditMemoLine[Carrier] = \"{carrier}\", CreditMemoLine[ReasonCode] = \"Damaged\" )", 0)
    dmg = "CALCULATETABLE ( VALUES ( CreditMemoLine[Carrier] ), CreditMemoLine[ReasonCode] = \"Damaged\" )"
    b.check(s, "fewest Damaged lines of a carrier", ctx["car_lo"],
            f"MINX ( {dmg}, CALCULATE ( [Credit Lines], CreditMemoLine[ReasonCode] = \"Damaged\" ) )", 0)
    b.check(s, "most Damaged lines of a carrier", ctx["car_hi"],
            f"MAXX ( {dmg}, CALCULATE ( [Credit Lines], CreditMemoLine[ReasonCode] = \"Damaged\" ) )", 0)
    claim(sorted(by_wh.values()) == sorted(ctx["warehouses"]), "the note's warehouse lines are the two warehouses'")
    for w, n in sorted(by_wh.items()):
        b.check(s, f"credit lines shipped from {w}", n, f"CALCULATE ( [Credit Lines], CreditMemoLine[Warehouse] = \"{w}\" )", 0)
    b.check(s, "fewest days from shipment to return", lag["lo"], "[Fewest Days after Shipment]", 0)
    b.check(s, "most days from shipment to return", lag["hi"], "[Most Days after Shipment]", 0)
    b.check(s, "average days from shipment to return", round(lag["mean"], 9), "[Average Days after Shipment]", 1e-6)
    b.check(s, "fewest days from delivery to return", lag["dlo"], "MIN ( CreditMemoLine[DaysAfterDelivery] )", 0)
    b.check(s, "most days from delivery to return", lag["dhi"], "MAX ( CreditMemoLine[DaysAfterDelivery] )", 0)
    for y, v in zip(years, ctx["by_ship_year"]):
        b.check(s, f"return rate by shipment year {y}", round(v, 9), f"CALCULATE ( [Return Rate by Ship Date], {yr(y)} )", 1e-7)
    b.check(s, f"return rate of the shipments of {dec_key} (censored)", round(ctx["dec"], 9),
            f"CALCULATE ( [Return Rate by Ship Date], 'Date'[YearMonth] = \"{dec_key}\" )", 1e-7)
    months_dax = (f"FILTER ( VALUES ( 'Date'[YearMonth] ), LEFT ( 'Date'[YearMonth], 4 ) = \"{y_c}\" && "
                  f"'Date'[YearMonth] <> \"{dec_key}\" )")
    b.check(s, f"lowest monthly return rate by shipment, {y_c} without December", round(ctx["mlo"], 9),
            f"MINX ( {months_dax}, [Return Rate by Ship Date] )", 1e-7)
    b.check(s, f"highest monthly return rate by shipment, {y_c} without December", round(ctx["mhi"], 9),
            f"MAXX ( {months_dax}, [Return Rate by Ship Date] )", 1e-7)
    for k, (cr, rv, _) in months_ship.items():
        b.check(s, f"credits on the shipments of {k}", round(cr, 2), f"CALCULATE ( [Credits by Ship Date], 'Date'[YearMonth] = \"{k}\" )")
        b.check(s, f"revenue of the shipments of {k}", round(rv, 2), f"CALCULATE ( [Revenue by Ship Date], 'Date'[YearMonth] = \"{k}\" )")
    b.check(s, "return lines in a later year than their shipment", ctx["cross"], "[Lines Returned in a Later Year]", 0)
    b.check(s, "credits returned in a later year than their shipment", ctx["cross_amt"], "[Credits Returned in a Later Year]")
    b.check(s, f"credit lines shipped before {years[0]} (no carry-in)", 0,
            f"COUNTROWS ( FILTER ( CreditMemoLine, CreditMemoLine[ShipmentDate] < DATE ( {years[0]}, 1, 1 ) ) )", 0)
    b.check(s, "credits on sales, all customers and years", round(ctx["overall"], 9), "[Return Rate]", 1e-7)
    fc = f"Customer[CustomerID] = {focus}"
    b.check(s, f"customer {focus}: the largest credits", focus,
            "MAXX ( TOPN ( 1, VALUES ( Customer[CustomerID] ), [Credits], DESC ), Customer[CustomerID] )", 0)
    b.check(s, f"customer {focus}: credits", round(ctx["focus_cred"], 2), f"CALCULATE ( [Credits], {fc} )")
    b.check(s, f"customer {focus}: sales", round(ctx["focus_sales"], 2), f"CALCULATE ( [Revenue], {fc} )")
    b.check(s, f"customer {focus}: credits on sales", round(ctx["rate"], 9), f"CALCULATE ( [Return Rate], {fc} )", 1e-7)
    b.check(s, f"customer {focus}: segment", ctx["seg"], f"CALCULATE ( SELECTEDVALUE ( Customer[CustomerSegment] ), {fc} )")
    b.check(s, f"customer {focus}: payment terms", ctx["terms"], f"CALCULATE ( SELECTEDVALUE ( Customer[PaymentTerms] ), {fc} )")
    b.check(s, f"customer {focus}: credit memos", ctx["focus_n"], f"CALCULATE ( [Credit Memos], {fc} )", 0)
    b.check(s, f"customer {focus}: credit memo grand total", ctx["focus_gt"], f"CALCULATE ( [Credit Memo Total], {fc} )")
    b.check(s, f"customer {focus}: credits approved by the top two approvers", ctx["top_two"],
            f"CALCULATE ( SUMX ( TOPN ( 2, VALUES ( CreditMemo[ApprovedByEmployeeID] ), [Credit Memos], DESC ), "
            f"[Credit Memos] ), {fc} )", 0)
    b.check(s, f"customer {focus}: refunds", ctx["focus_rf"], f"CALCULATE ( [Refunds], {fc} )", 0)
    b.check(s, f"customer {focus}: refund amount", ctx["focus_rf_amt"], f"CALCULATE ( [Refund Amount], {fc} )")
    b.check(s, f"customer {focus}: refunds dated before the customer's payment", ctx["focus_before"],
            f"CALCULATE ( [Refunds], {fc}, RefundFlags[BeforePayment] = 1 )", 0)
    b.check(s, f"customers with a higher rate than customer {focus}", len(higher),
            f"VAR Focus = CALCULATE ( [Return Rate], {fc} ) RETURN COUNTROWS ( FILTER ( VALUES ( Customer[CustomerID] ), "
            "[Return Rate] > Focus ) )", 0)
    for k, r, sl in higher:
        b.check(s, f"customer {k}: credits on sales", round(r, 9), f"CALCULATE ( [Return Rate], Customer[CustomerID] = {k} )", 1e-7)
        b.check(s, f"customer {k}: sales", round(sl, 2), f"CALCULATE ( [Revenue], Customer[CustomerID] = {k} )")
    for ti in titles:
        for y in years:
            b.check(s, f"refunds approved by {ti} in {y}", rf_titles[(ti, y)],
                    f"CALCULATE ( [Refunds], CustomerRefund[RefundApproverTitle] = \"{ti}\", {yr(y)} )", 0)
    for sc_, n in enumerate(sc):
        b.check(s, f"refunds scoring {sc_}", n, f"CALCULATE ( [Refunds], CustomerRefund[Score] = {sc_} )", 0)
    b.check(s, "refunds scoring 4 or 5", ctx["hi"], "[High-Score Refunds]", 0)
    b.check(s, "amount of the refunds scoring 4 or 5", ctx["hi_amt"], "[High-Score Amount]")
    bf = f"CustomerRefund[RefundNumber] = \"{ctx['big']}\""
    b.check(s, f"{ctx['big']} score", ctx["big_score"], f"CALCULATE ( MAX ( CustomerRefund[Score] ), {bf} )", 0)
    b.check(s, f"{ctx['big']} refund above authority (0 = within limit)", int(ctx["big_above"]),
            f"CALCULATE ( MAX ( RefundFlags[AboveLimit] ), RefundFlags[RefundNumber] = \"{ctx['big']}\" )", 0)
    b.check(s, "refunds dated on a weekend", ctx["weekend_rf"],
            "COUNTROWS ( FILTER ( CustomerRefund, WEEKDAY ( CustomerRefund[RefundDate], 2 ) >= 6 ) )", 0)
    b.check(s, "credit memos dated on a weekend", ctx["weekend_cm"],
            "COUNTROWS ( FILTER ( CreditMemo, WEEKDAY ( CreditMemo[CreditMemoDate], 2 ) >= 6 ) )", 0)
    # the refund flags RefundFlags.csv brings (Requirement 4's values, as the ranking shows them)
    s4 = "Requirement 5 (the flags of Requirement 4)"
    for key, f in (("rf_above", "AboveLimit"), ("before", "BeforePayment"), ("pd2", "PastDueAtLeastRefund"),
                   ("mism", "MethodMismatch")):
        v = r4[key]
        n = FLAG_NAMES[FLAGS.index(f)]
        fl = f"Flags[Flag] = \"{n}\""
        b.check(s4, f"{n}: refunds", v["n"], f"CALCULATE ( [Flagged Refunds], {fl} )", 0)
        b.check(s4, f"{n}: amount", v["amt"], f"CALCULATE ( [Flagged Amount], {fl} )")
        b.check(s4, f"{n}: refunds in {y_c}", v["cur"][0], f"CALCULATE ( [Flagged Refunds], {fl}, {yr(y_c)} )", 0)
        b.check(s4, f"{n}: amount in {y_c}", v["cur"][1], f"CALCULATE ( [Flagged Amount], {fl}, {yr(y_c)} )")
        if "years" in v:
            for y, k in zip(years, v["years"]):
                b.check(s4, f"{n}: refunds in {y}", k, f"CALCULATE ( [Flagged Refunds], {fl}, {yr(y)} )", 0)
    n_cab = len(flag_rows["CreditAboveLimit"])
    b.check(s4, "Credit above authority: refunds", n_cab, "CALCULATE ( [Flagged Refunds], Flags[Flag] = \"Credit above authority\" )", 0)
    b.check(s4, "refunds with a past-due balance on the refund date", r4["pd1"]["n"],
            "CALCULATE ( [Refunds], RefundFlags[PastDue] > 0 )", 0)
    b.check(s4, "amount of the refunds with a past-due balance", r4["pd1"]["amt"],
            "CALCULATE ( [Refund Amount], RefundFlags[PastDue] > 0 )")
    unpaid_any = "FILTER ( CustomerRefund, CALCULATE ( [Invoice Paid by Refund Date] ) = 0 )"
    b.check(s4, "refunds dated before any payment on the credited invoice", len(nothing), f"COUNTROWS ( {unpaid_any} )", 0)
    b.check(s4, "amount of the refunds dated before any payment", round(sum(r["amt"] for r in nothing), 2),
            f"SUMX ( {unpaid_any}, CustomerRefund[Amount] )")
    # the drill-through page
    b.check(s, f"{big['num']}: receipts applied to its invoice by the refund date", round(paid_then, 2),
            f"CALCULATE ( [Invoice Paid by Refund Date], {bf} )")
    b.check(s, f"{big['num']}: receipts applied to its invoice, all", round(sum(a[1] for a in big_apps), 2),
            f"CALCULATE ( [Applied to the Invoice], {bf} )")
    b.check(s, f"{big['num']}: receipts on its invoice", len({a[3] for a in big_apps}),
            f"CALCULATE ( COUNTROWS ( FILTER ( VALUES ( CashReceiptApplication[ReceiptNumber] ), NOT ISBLANK ( "
            f"[Applied to the Invoice] ) ) ), {bf} )", 0)
    b.check(s, f"{big['num']}: its credit", big_cm["num"], f"CALCULATE ( SELECTEDVALUE ( CustomerRefund[CreditMemoNumber] ), {bf} )")
    b.check(s, f"{big['num']}: its invoice", big_inv["num"], f"CALCULATE ( SELECTEDVALUE ( CustomerRefund[InvoiceNumber] ), {bf} )")
    b.check(s, f"{big['num']}: its credit's approver", big_cm["appr"],
            f"CALCULATE ( MAX ( CustomerRefund[CreditApproverID] ), {bf} )", 0)
    b.check(s, "last credit memo date", last_credit, "FORMAT ( MAX ( CreditMemo[CreditMemoDate] ), \"yyyy-mm-dd\" )")
    b.check(s, "last refund date", last_refund, "FORMAT ( MAX ( CustomerRefund[RefundDate] ), \"yyyy-mm-dd\" )")
    for c_, expr, _, n in tests:
        b.check(s, f"Tests tab: {c_.split(':')[0]} returns {n} rows", n, f"COUNTROWS ( {' '.join(expr.split())} )", 0)
    b.facts = dict(big=big, big_cm=big_cm, big_inv=big_inv, paid_then=paid_then)


# --- Milestone 2: the checkpoints the report shows ----------------------------------------------------------------

def m2(b: Build) -> None:
    d = b.data
    ctx = ch19.m2(d, claim)
    s = "Milestone 2"
    fl = lambda n: f"Flags[Flag] = \"{n}\""     # noqa: E731
    b.check(s, "refunds above the approver's limit", ctx["rf_above"], f"CALCULATE ( [Flagged Refunds], {fl(FLAG_NAMES[0])} )", 0)
    b.check(s, "refunds above the approver's limit: amount", ctx["rf_above_total"],
            f"CALCULATE ( [Flagged Amount], {fl(FLAG_NAMES[0])} )")
    b.check(s, "refunds dated before the customer's payment", ctx["before"],
            f"CALCULATE ( [Flagged Refunds], {fl(FLAG_NAMES[3])} )", 0)
    b.check(s, "refunds dated before the customer's payment: amount", ctx["before_total"],
            f"CALCULATE ( [Flagged Amount], {fl(FLAG_NAMES[3])} )")
    b.check(s, "the largest refund", ctx["big"],
            "MAXX ( TOPN ( 1, CustomerRefund, CustomerRefund[Amount], DESC ), CustomerRefund[RefundNumber] )")
    b.check(s, "the largest refund: amount", ctx["big_amount"], "MAX ( CustomerRefund[Amount] )")
    b.check(s, "the largest refund: unpaid on its invoice when it was paid", round(ctx["unpaid"], 2),
            f"CALCULATE ( [Invoice Unpaid at Refund Date], CustomerRefund[RefundNumber] = \"{ctx['big']}\" )")


EXERCISES = [("Requirement 5", r5), ("Milestone 2", m2)]
