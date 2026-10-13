"""Chapter 3's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 3 teaches the structure of the database (keys, cardinality, ER diagrams, the source-document trace), so the
contexts do two jobs:

- they supply the values a model answer can quote (the rows a filter finds when a student follows a key, the
  cardinality of each relationship read from the data, the counts of the integrity tests), and
- they check, with claim(), every table and column the guide names and every statement about the data that another
  dataset could falsify, so a roll or a schema change flags the wording instead of leaving it stale.

Keys: ch03.chapter (the chapter note), ch03.t1 and ch03.t2 (the two tutorials) and ch03.ex1 to ch03.ex6 (the exercises).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, gl_rows_of, in_group, rows_of, schema, trace_ids

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "03-accounting-data-environment"
DECK = REPO / "slides" / "chapter-03" / "index.qmd"
O2C_DIAGRAM = ["Customer", "SalesOrder", "SalesOrderLine", "Item", "Shipment", "ShipmentLine", "SalesInvoice",
               "SalesInvoiceLine", "CashReceipt", "CashReceiptApplication"]            # Figure 3.7, Tutorial 3.1 Step 1


# --- helpers -------------------------------------------------------------------------------------------------------

def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise \d+\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def col_letter(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def letter(have: dict[str, list[str]], table: str, column: str) -> str:
    """The Excel column letter of a column, as the workbook lists the columns in the database's order."""
    return col_letter(have[table].index(column) + 1)


def card(d, child: str, fk: str, parent: str, pk: str) -> dict:
    """What the data say about one relationship: blanks, orphans, childless parents, parents with several children."""
    rows = d.one(f"SELECT COUNT(*) FROM {child}")
    blank = d.one(f"SELECT COUNT(*) FROM {child} WHERE {fk} IS NULL")
    orphans = d.one(f"SELECT COUNT(*) FROM {child} WHERE {fk} IS NOT NULL AND {fk} NOT IN (SELECT {pk} FROM {parent})")
    parents = d.one(f"SELECT COUNT(*) FROM {parent}")
    childless = d.one(f"SELECT COUNT(*) FROM {parent} WHERE {pk} NOT IN (SELECT {fk} FROM {child} WHERE {fk} IS NOT NULL)")
    many = d.one(f"SELECT COUNT(*) FROM (SELECT {fk} FROM {child} WHERE {fk} IS NOT NULL GROUP BY 1 HAVING COUNT(*) > 1)")
    biggest = d.one(f"SELECT COALESCE(MAX(n), 0) FROM (SELECT COUNT(*) n FROM {child} WHERE {fk} IS NOT NULL GROUP BY {fk})")
    distinct = d.one(f"SELECT COUNT(DISTINCT {fk}) FROM {child}")
    child_end = ("zero or many" if childless and many else "zero or one" if childless else "one or many" if many else "exactly one")
    parent_end = "zero or one" if blank else "exactly one"
    return dict(child=child, fk=fk, parent=parent, pk=pk, rows=rows, blank=blank, orphans=orphans, parents=parents,
                childless=childless, many=many, biggest=biggest, distinct=distinct, child_end=child_end, parent_end=parent_end)


def mcq_facts(chapter: Path) -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import source
    text = (chapter / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/03-accounting-data-environment/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 3\b")
    letters = re.findall(r"(\d+) ([A-D])[,.]", comment.split("\n", 2)[1])
    key = {int(n): a for n, a in letters}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


# --- the chapter note ----------------------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "Customer": ["CustomerID", "CustomerName", "CustomerSegment", "IsActive"],
    "SalesOrder": ["SalesOrderID", "OrderNumber", "CustomerID", "CostCenterID"],
    "SalesOrderLine": ["SalesOrderLineID", "SalesOrderID", "ItemID"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ShipmentLineID"],
    "ShipmentLine": ["ShipmentLineID"],
    "PurchaseInvoice": ["InvoiceNumber", "SupplierID"],
    "Account": ["AccountID", "AccountNumber", "ParentAccountID", "AccountSubType"],
    "GLEntry": ["AccountID", "SourceDocumentType", "SourceDocumentID", "SourceLineID", "VoucherNumber", "CostCenterID"],
    "Item": ["ItemID", "ItemGroup", "ListPrice"],
    "WorkOrder": ["WorkOrderID"],
    "WorkOrderClose": ["WorkOrderID"],
    "PayrollPayment": ["PayrollPaymentID"],
}
UNIQUE_DOCUMENT_NUMBERS = {"SalesOrder": "OrderNumber", "SalesInvoice": "InvoiceNumber", "JournalEntry": "EntryNumber",
                           "Account": "AccountNumber"}


def unique_columns(d, table: str) -> set[str]:
    out = set()
    for idx in d.q(f"PRAGMA index_list({table})"):
        cols = [r[2] for r in d.q(f"PRAGMA index_info({idx[1]})")]
        if idx[2] and len(cols) == 1:
            out.add(cols[0])
    return out


@context("ch03.chapter")
def chapter(d, claim):
    schema(d, claim, CHAPTER_SCHEMA)
    tables = [r[0] for r in d.q("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    types, declared, bad_pk = set(), 0, []
    for t in tables:
        info = d.q(f"PRAGMA table_info({t})")
        types |= {r[2] for r in info}
        declared += len(d.q(f"PRAGMA foreign_key_list({t})"))
        pk = [r for r in info if r[5]]
        if not (len(pk) == 1 and pk[0][2] == "INTEGER" and pk[0][0] == 0):
            bad_pk.append(t)
    claim(not bad_pk, f"every table has one INTEGER primary key in its first column (differs: {bad_pk})")
    claim(declared == 0, "the database file declares no foreign keys")
    claim(types == {"INTEGER", "REAL", "TEXT"}, "the file declares three data types: INTEGER, REAL and TEXT")
    claim(all(col in unique_columns(d, t) for t, col in UNIQUE_DOCUMENT_NUMBERS.items()),
          "OrderNumber, InvoiceNumber, EntryNumber and AccountNumber each have a unique index")
    claim("InvoiceNumber" not in unique_columns(d, "PurchaseInvoice"), "PurchaseInvoice.InvoiceNumber has no unique index")
    in_group(claim, {"Customer": "Order-to-Cash", "SalesOrder": "Order-to-Cash", "Item": "Master Data", "Account": "Accounting Core",
                     "GLEntry": "Accounting Core", "WorkOrder": "Manufacturing", "BillOfMaterial": "Manufacturing"})

    # the source-document trace: the one relationship that is not a foreign key
    types_in_gl = d.q("SELECT SourceDocumentType FROM GLEntry GROUP BY 1 ORDER BY COUNT(*) DESC")
    names = [r[0] for r in types_in_gl]
    not_tables = [n for n in names if n not in tables]
    claim(not_tables == ["PayrollSummary"], "every source type but PayrollSummary names a table")
    orphans = {}
    for n in names:
        if n in tables:
            pk = d.q(f"PRAGMA table_info({n})")[0][1]
            k = d.one(f"SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = ? AND SourceDocumentID NOT IN (SELECT {pk} FROM {n})", n)
            if k:
                orphans[n] = k
    claim(list(orphans) == ["PayrollPayment"], "the only ledger rows whose source document is missing are typed PayrollPayment")
    trace = trace_ids(d)
    claim(trace["id.trace.exact"], "the traced sale of Chapters 1 and 3 exists exactly as the chapter tells it")
    same_id = d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE SourceDocumentID = ? GROUP BY 1", trace["id.trace.invoice_id"])
    claim(len(same_id) > 1, "the key of the traced invoice is also the key of documents of other types, so SourceDocumentID alone is ambiguous")

    # fan-out: what a join of customers to orders to lines returns
    fan_rows = d.one("SELECT COUNT(*) FROM Customer c JOIN SalesOrder o USING (CustomerID) JOIN SalesOrderLine l USING (SalesOrderID)")
    fan_customers = d.one("SELECT COUNT(DISTINCT c.CustomerID) FROM Customer c JOIN SalesOrder o USING (CustomerID)")
    lines = d.one("SELECT COUNT(*) FROM SalesOrderLine")
    claim(fan_rows == lines, "every order line belongs to an order of an existing customer, so the three-table join returns one row for each line")
    example = d.q("SELECT c.CustomerID, c.CustomerName, COUNT(DISTINCT o.SalesOrderID), COUNT(*) FROM Customer c JOIN SalesOrder o USING (CustomerID) "
                  "JOIN SalesOrderLine l USING (SalesOrderID) GROUP BY 1, 2 HAVING COUNT(DISTINCT o.SalesOrderID) BETWEEN 8 AND 12 ORDER BY 4 DESC, 1 LIMIT 1")
    claim(len(example) == 1, "some customer has between 8 and 12 orders, so the fan-out has a small example")
    ex_id, ex_name, ex_orders, ex_lines = example[0]
    claim(ex_lines > 2 * ex_orders, "that customer's orders have several lines each, so the join repeats the customer more than the orders")

    # what is optional on each side of the O2C core
    no_orders = d.q("SELECT IsActive FROM Customer WHERE CustomerID NOT IN (SELECT CustomerID FROM SalesOrder)")
    claim(len(no_orders) > 0 and all(a == 0 for (a,) in no_orders), "the customers with no orders are all inactive")
    unsold = d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL AND ItemID NOT IN (SELECT ItemID FROM SalesOrderLine)")
    claim(unsold > 0, "some items that have a list price were never ordered")
    unshipped = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ShipmentLineID IS NULL")
    uninvoiced = d.one("SELECT COUNT(*) FROM ShipmentLine WHERE ShipmentLineID NOT IN (SELECT ShipmentLineID FROM SalesInvoiceLine "
                       "WHERE ShipmentLineID IS NOT NULL)")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i USING (ItemID) WHERE l.ShipmentLineID IS NULL AND i.ItemGroup <> 'Services'") == 0,
          "an invoice line with no shipment line is always a Services line")
    claim(d.one("SELECT COUNT(*) FROM (SELECT ShipmentLineID FROM SalesInvoiceLine WHERE ShipmentLineID IS NOT NULL GROUP BY 1 HAVING COUNT(*) > 1)") == 0,
          "no shipment line is billed on more than one invoice line")
    gl_rows = d.one("SELECT COUNT(*) FROM GLEntry")
    claim(gl_rows == max(d.one(f"SELECT COUNT(*) FROM {t}") for t in tables), "GLEntry is the largest table")
    n_q, longest = mcq_facts(CHAPTER)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    return dict(
        n_tables=len(tables), n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(), n_questions=n_q,
        longest_correct=and_join(longest), n_longest=len(longest), gl_rows=gl_rows,
        n_trace_types=len(names), orphans=orphans, orphan_rows=orphans["PayrollPayment"], same_id=same_id, same_id_rows=sum(n for _, n in same_id),
        same_id_types=len(same_id), invoice_id=trace["id.trace.invoice_id"], invoice=trace["id.trace.invoice"],
        fan=dict(rows=fan_rows, customers=fan_customers, id=ex_id, name=ex_name, orders=ex_orders, lines=ex_lines),
        no_orders=len(no_orders), unsold=unsold, unshipped=unshipped, uninvoiced=uninvoiced,
        rows=rows_of(d, ["Customer", "SalesOrder", "SalesOrderLine", "Account", "GLEntry"]))


# --- Tutorial 3.1: reading the O2C ER diagram -------------------------------------------------------------------------------

T1_RELATIONSHIPS = [("Customer", "CustomerID", "SalesOrder", "CustomerID"), ("SalesOrder", "SalesOrderID", "SalesOrderLine", "SalesOrderID"),
                    ("Item", "ItemID", "SalesOrderLine", "ItemID"), ("SalesOrder", "SalesOrderID", "Shipment", "SalesOrderID"),
                    ("Shipment", "ShipmentID", "ShipmentLine", "ShipmentID"), ("SalesOrderLine", "SalesOrderLineID", "ShipmentLine", "SalesOrderLineID"),
                    ("SalesOrder", "SalesOrderID", "SalesInvoice", "SalesOrderID"), ("SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID"),
                    ("ShipmentLine", "ShipmentLineID", "SalesInvoiceLine", "ShipmentLineID"), ("CashReceipt", "CashReceiptID", "CashReceiptApplication", "CashReceiptID"),
                    ("SalesInvoice", "SalesInvoiceID", "CashReceiptApplication", "SalesInvoiceID")]


@context("ch03.t1")
def t1(d, claim):
    have = schema(d, claim, {t: [f"{t}ID"] for t in O2C_DIAGRAM})
    tables = [r[0] for r in d.q("SELECT name FROM sqlite_master WHERE type = 'table'")]
    pks = []
    for t in O2C_DIAGRAM:
        info = d.q(f"PRAGMA table_info({t})")
        pk = [r for r in info if r[5]]
        claim(len(pk) == 1 and pk[0][1] == f"{t}ID", f"the primary key of {t} is {t}ID")
        pks.append(dict(table=t, key=pk[0][1], columns=len(info), rows=d.one(f"SELECT COUNT(*) FROM {t}")))
    # Step 3: the foreign keys of SalesOrderLine, shown and not shown
    cols = have["SalesOrderLine"]
    fks = {"SalesOrderID": "SalesOrder", "ItemID": "Item", "PriceListLineID": "PriceListLine", "PromotionID": "PromotionProgram",
           "PriceOverrideApprovalID": "PriceOverrideApproval"}
    claim(all(c in cols and t in tables for c, t in fks.items()), "SalesOrderLine has the five foreign key columns the guide names, and their parent tables exist")
    fk_rows = []
    for c, t in fks.items():
        k = card(d, "SalesOrderLine", c, t, c)
        claim(k["orphans"] == 0, f"every non-blank SalesOrderLine.{c} exists in {t}")
        fk_rows.append(dict(column=c, parent=t, blank=k["blank"], orphans=k["orphans"]))
    claim(fk_rows[0]["blank"] == 0 and fk_rows[1]["blank"] == 0, "SalesOrderID and ItemID are never blank on an order line")
    claim(all(r["blank"] > 0 for r in fk_rows[2:]), "the pricing foreign keys of an order line are blank on some lines")
    # Steps 4-6: the cardinality of each relationship, read from the data
    rel = [card(d, c, fk, p, pk) for p, pk, c, fk in T1_RELATIONSHIPS]
    named = {(r["parent"], r["child"], r["fk"]): r for r in rel}
    claim(all(r["orphans"] == 0 for r in rel), "no foreign key of the O2C core has an orphaned value")
    cs = named[("Customer", "SalesOrder", "CustomerID")]
    claim(cs["childless"] > 0 and cs["many"] > 0 and cs["parent_end"] == "exactly one",
          "a customer has zero or many orders and an order has exactly one customer")
    sl = named[("SalesOrder", "SalesOrderLine", "SalesOrderID")]
    claim(sl["child_end"] == "one or many", "an order has one or many lines")
    il = named[("Item", "SalesOrderLine", "ItemID")]
    claim(il["child_end"] == "zero or many", "an item has zero or many order lines")
    sil = named[("ShipmentLine", "SalesInvoiceLine", "ShipmentLineID")]
    claim(sil["child_end"] == "zero or one" and sil["parent_end"] == "zero or one" and sil["biggest"] == 1,
          "a shipment line is billed on zero or one invoice line, and an invoice line has zero or one shipment line")
    cra = named[("CashReceipt", "CashReceiptApplication", "CashReceiptID")]
    inv = named[("SalesInvoice", "CashReceiptApplication", "SalesInvoiceID")]
    claim(cra["many"] > 0 and inv["many"] > 0, "a receipt can settle several invoices, and an invoice can be settled by several receipts")
    part = d.one("SELECT COUNT(*) FROM (SELECT SalesOrderLineID FROM ShipmentLine GROUP BY 1 HAVING COUNT(*) > 1)")
    claim(part > 0, "some order lines are shipped in several shipment lines")
    pairs = d.one("SELECT COUNT(*) FROM (SELECT 1 FROM CashReceiptApplication GROUP BY CashReceiptID, SalesInvoiceID HAVING COUNT(*) > 1)")
    claim(pairs == 0, "a receipt is applied to a given invoice once, so the junction table has one row for each pair")
    return dict(
        pks=pks, fk_rows=fk_rows, n_fk_columns=len(fks), rel=rel, part=part, n_tables=len(O2C_DIAGRAM),
        customers=cs["parents"], customers_none=cs["childless"], n_items=il["parents"], items_none=il["childless"],
        orders=sl["parents"], lines=sl["rows"], design_lines=sil["blank"], uninvoiced=sil["childless"],
        receipts=cra["parents"], multi_receipts=cra["many"], invoices_applied=inv["parents"] - inv["childless"], multi_invoices=inv["many"])


# --- Tutorial 3.2: tracing a sale from the order to the ledger ------------------------------------------------------------

T2_SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SalesOrderID", "CustomerID", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "SalesOrderLineID", "ShipmentLineID", "ItemID", "Quantity", "UnitPrice", "LineTotal"],
    "ShipmentLine": ["ShipmentLineID", "ShipmentID", "SalesOrderLineID", "QuantityShipped", "ExtendedStandardCost"],
    "Shipment": ["ShipmentID", "ShipmentNumber", "ShipmentDate", "SalesOrderID"],
    "SalesOrderLine": ["SalesOrderLineID", "SalesOrderID", "ItemID", "Quantity"],
    "SalesOrder": ["SalesOrderID", "OrderNumber", "OrderDate", "CustomerID"],
    "Customer": ["CustomerID", "CustomerName", "CustomerSegment"],
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "StandardCost", "InventoryAccountID", "RevenueAccountID", "COGSAccountID"],
    "CashReceipt": ["CashReceiptID", "ReceiptNumber", "ReceiptDate", "Amount", "PaymentMethod"],
    "CashReceiptApplication": ["CashReceiptApplicationID", "CashReceiptID", "SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "SalesCommissionAccrual": ["SalesCommissionAccrualID", "SalesInvoiceID", "SalesInvoiceLineID", "CommissionAmount"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "SourceDocumentType", "SourceDocumentID", "SourceLineID", "CostCenterID", "VoucherNumber"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType"],
}


@context("ch03.t2")
def t2(d, claim):
    schema(d, claim, T2_SCHEMA)
    t = trace_ids(d)
    claim(t["id.trace.exact"], "the traced sale exists exactly as Tutorial 3.2 tells it")
    inv, line, so, sol = t["id.trace.invoice_id"], t["id.trace.line_id"], t["id.trace.order_id"], t["id.trace.order_line_id"]
    shl, sh, rec, app, item = t["id.trace.shipment_line_id"], t["id.trace.shipment_id"], t["id.trace.receipt_id"], t["id.trace.application_id"], t["id.trace.item_id"]
    si = d.q("SELECT SalesInvoiceID, SalesOrderID, CustomerID, SubTotal, FreightAmount, TaxAmount, GrandTotal, InvoiceDate FROM SalesInvoice WHERE SalesInvoiceID = ?", inv)[0]
    sil = d.q("SELECT SalesInvoiceLineID, Quantity, UnitPrice, LineTotal, SalesOrderLineID, ShipmentLineID, ItemID FROM SalesInvoiceLine WHERE SalesInvoiceID = ?", inv)
    claim(len(sil) == 1 and sil[0][0] == line, "the traced invoice has one line")
    sil = sil[0]
    claim(sil[4] == sol and sil[5] == shl and sil[6] == item and si[1] == so, "the invoice line carries the keys of the order line, the shipment line and the item")
    shl_row = d.q("SELECT ShipmentID, SalesOrderLineID, QuantityShipped, ExtendedStandardCost FROM ShipmentLine WHERE ShipmentLineID = ?", shl)[0]
    shp = d.q("SELECT ShipmentNumber, ShipmentDate, SalesOrderID FROM Shipment WHERE ShipmentID = ?", sh)[0]
    claim(shl_row[0] == sh and shl_row[1] == sol and shp[2] == so, "the shipment line belongs to the traced shipment and order line")
    sol_row = d.q("SELECT SalesOrderID, Quantity, ItemID FROM SalesOrderLine WHERE SalesOrderLineID = ?", sol)[0]
    claim(sol_row[0] == so and sol_row[1] > sil[1], "the order line covers a larger quantity than the invoice bills")
    ord_row = d.q("SELECT OrderNumber, OrderDate, CustomerID FROM SalesOrder WHERE SalesOrderID = ?", so)[0]
    cust = d.q("SELECT CustomerName, CustomerSegment FROM Customer WHERE CustomerID = ?", si[2])[0]
    claim(ord_row[2] == si[2] and cust[1] == "Wholesale", "the order and the invoice name the same customer, a wholesale one")
    it = d.q("SELECT ItemCode, ItemName, ItemGroup, StandardCost, InventoryAccountID, RevenueAccountID, COGSAccountID FROM Item WHERE ItemID = ?", item)[0]
    claim(it[2] == "Furniture" and it[0].startswith("FUR-DSK"), "the item is a Furniture desk")
    siblings = dict(order_lines=d.one("SELECT COUNT(*) FROM SalesOrderLine WHERE SalesOrderID = ?", so),
                    shipments=d.one("SELECT COUNT(*) FROM Shipment WHERE SalesOrderID = ?", so),
                    invoices=d.one("SELECT COUNT(*) FROM SalesInvoice WHERE SalesOrderID = ?", so))
    claim(siblings["shipments"] > 1 and siblings["invoices"] > 1, "the order was shipped and invoiced in several parts")

    def accounts(source, doc):
        return [dict(id=r["id"], account_id=r["account_id"], number=r["number"], name=r["name"], debit=r["debit"], credit=r["credit"],
                     line=r["line"], cc=d.one("SELECT CostCenterID FROM GLEntry WHERE GLEntryID = ?", r["id"]))
                for r in gl_rows_of(d, source, doc)]
    gl_inv, gl_ship, gl_rec, gl_app = accounts("SalesInvoice", inv), accounts("Shipment", sh), accounts("CashReceipt", rec), accounts("CashReceiptApplication", app)
    claim(len(gl_inv) == 4 and [r["number"] for r in gl_inv] == [1020, 4010, 4050, 2050], "the invoice posts four rows: receivables, revenue, freight revenue and sales tax payable")
    claim(abs(sum(r["debit"] for r in gl_inv) - sum(r["credit"] for r in gl_inv)) < 0.005 and abs(gl_inv[0]["debit"] - si[6]) < 0.005,
          "the invoice's rows balance and the receivable equals its GrandTotal")
    claim([r["line"] for r in gl_inv] == [None, line, None, None], "only the revenue row of the invoice carries a SourceLineID, the invoice line's key")
    claim(all(r["account_id"] != r["number"] for r in gl_inv), "AccountID and AccountNumber are different numbers")
    claim(gl_inv[1]["account_id"] == it[5], "the item's RevenueAccountID is the AccountID that the revenue row posts to")
    claim(gl_inv[0]["cc"] is None and gl_inv[1]["cc"] is not None, "the receivable row has no cost center and the revenue row has one")
    freight = [r for r in gl_ship if r["number"] == 5050]
    claim(len(gl_ship) == 4 and {r["number"] for r in gl_ship} == {5010, 1040, 5050, 2040}, "the shipment posts cost of goods sold and inventory, and freight-out and accrued expenses")
    cogs = [r for r in gl_ship if r["line"] == shl]
    claim(len(cogs) == 2 and {r["account_id"] for r in cogs} == {it[6], it[4]} and all(abs((r["debit"] or r["credit"]) - shl_row[3]) < 0.005 for r in cogs),
          "the two rows with the shipment line's key post the item's COGSAccountID and InventoryAccountID for the line's standard cost")
    claim(abs(shl_row[3] - round(shl_row[2] * it[3], 2)) < 0.005, "the shipment line's cost is the quantity shipped times the item's standard cost")
    claim({r["number"] for r in gl_rec} == {1010, 2060} and {r["number"] for r in gl_app} == {2060, 1020}, "the receipt posts cash and unapplied cash, and its application moves 2060 to receivables")
    rc = d.q("SELECT ReceiptNumber, ReceiptDate, Amount, PaymentMethod FROM CashReceipt WHERE CashReceiptID = ?", rec)[0]
    ap = d.q("SELECT SalesInvoiceID, AppliedAmount, ApplicationDate FROM CashReceiptApplication WHERE CashReceiptApplicationID = ?", app)[0]
    others = d.one("SELECT COUNT(*) FROM CashReceiptApplication WHERE CashReceiptID = ?", rec)
    claim(ap[0] == inv and abs(ap[1] - si[6]) < 0.005, "the application settles the traced invoice for its GrandTotal")
    claim(others > 1 and rc[3] == "Check", "the receipt is a check that paid several invoices")
    ca = d.q("SELECT SalesCommissionAccrualID, CommissionAmount FROM SalesCommissionAccrual WHERE SalesInvoiceLineID = ?", line)
    claim(len(ca) == 1, "the invoice line has one commission accrual")
    gl_comm = accounts("SalesCommissionAccrual", ca[0][0])
    claim({r["number"] for r in gl_comm} == {6290, 2034} and all(r["line"] == line for r in gl_comm), "the commission accrual posts commission expense and commission payable, keyed by the invoice line")
    ids = d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE SourceDocumentID = ? GROUP BY 1 ORDER BY 2 DESC, 1", inv)
    claim(len(ids) > 1 and dict(ids)["SalesInvoice"] == 4, "the invoice's key alone finds ledger rows of several types, four of them the invoice's own")
    docs = sum(1 for g in (gl_inv, gl_ship, gl_rec, gl_app, gl_comm) if g)
    return dict(
        t=t, inv=dict(id=inv, number=t["id.trace.invoice"], date=si[7], order_id=si[1], customer_id=si[2], subtotal=si[3], freight=si[4], tax=si[5], total=si[6]),
        line=dict(id=line, quantity=sil[1], price=sil[2], total=sil[3], order_line=sol, shipment_line=shl, item_id=item),
        shipment_line=dict(id=shl, shipment_id=sh, quantity=shl_row[2], cost=shl_row[3]), shipment=dict(id=sh, number=shp[0], date=shp[1],
        days_before=(date.fromisoformat(si[7]) - date.fromisoformat(shp[1])).days),
        order_line=dict(id=sol, order_id=so, quantity=sol_row[1]), order=dict(id=so, number=ord_row[0], date=ord_row[1], **siblings),
        customer=dict(id=si[2], name=cust[0], segment=cust[1].lower()), item=dict(id=item, code=it[0], name=it[1], group=it[2], cost=it[3], inventory_id=it[4], revenue_id=it[5], cogs_id=it[6]),
        freight=freight[0]["debit"], gl_inv=gl_inv, gl_ship=gl_ship, gl_rec=gl_rec, gl_app=gl_app, gl_comm=gl_comm,
        receipt=dict(id=rec, number=rc[0], date=rc[1], amount=rc[2], method=rc[3].lower(), applications=others),
        application=dict(id=app, amount=ap[1], date=ap[2][:10]), commission=ca[0][1], same_id=ids, same_id_rows=sum(n for _, n in ids), same_id_types=len(ids),
        documents=docs)


# --- Exercise 3.1: tracing a purchase through the P2P tables ---------------------------------------------------------------

EX1_SCHEMA = {
    "PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "PurchaseOrderID", "SupplierID", "SubTotal", "TaxAmount", "GrandTotal", "Status"],
    "PurchaseInvoiceLine": ["PILineID", "PurchaseInvoiceID", "POLineID", "GoodsReceiptLineID", "AccrualJournalEntryID", "ItemID", "Quantity", "UnitCost", "LineTotal"],
    "GoodsReceiptLine": ["GoodsReceiptLineID", "GoodsReceiptID", "POLineID", "ItemID", "QuantityReceived", "ExtendedStandardCost"],
    "GoodsReceipt": ["GoodsReceiptID", "ReceiptNumber", "ReceiptDate", "PurchaseOrderID"],
    "PurchaseOrderLine": ["POLineID", "PurchaseOrderID", "ItemID", "Quantity", "UnitCost", "LineTotal"],
    "PurchaseOrder": ["PurchaseOrderID", "PONumber", "OrderDate", "SupplierID"],
    "Supplier": ["SupplierID", "SupplierName"],
    "DisbursementPayment": ["DisbursementID", "PaymentNumber", "PaymentDate", "SupplierID", "PurchaseInvoiceID", "Amount", "PaymentMethod"],
    "Item": ["ItemID", "ItemCode", "ItemName", "InventoryAccountID"],
}
MODEL_INVOICE = """
    SELECT pi.PurchaseInvoiceID FROM PurchaseInvoice pi
    JOIN PurchaseInvoiceLine l ON l.PurchaseInvoiceID = pi.PurchaseInvoiceID
    JOIN GoodsReceiptLine r ON r.GoodsReceiptLineID = l.GoodsReceiptLineID
    JOIN PurchaseOrderLine o ON o.POLineID = l.POLineID
    WHERE pi.Status = 'Paid' AND pi.InvoiceDate BETWEEN ? AND ? AND pi.TaxAmount = 0
      AND (SELECT COUNT(*) FROM PurchaseInvoiceLine x WHERE x.PurchaseInvoiceID = pi.PurchaseInvoiceID) = 1
      AND l.Quantity = r.QuantityReceived AND l.UnitCost > o.UnitCost
      AND (SELECT COUNT(*) FROM DisbursementPayment p WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID) = 1
      AND (SELECT ABS(p.Amount - pi.GrandTotal) FROM DisbursementPayment p WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID) < 0.005
    ORDER BY pi.PurchaseInvoiceID LIMIT 1"""


@context("ch03.ex1")
def ex1(d, claim):
    have = schema(d, claim, EX1_SCHEMA)
    pid = d.q(MODEL_INVOICE, f"{d.C}-01-01", f"{d.C}-12-31")
    claim(len(pid) == 1, "a paid invoice of the current fiscal year has one line, a receipt line, no tax, one full payment, a received quantity equal to the invoiced one and a price above the order's")
    pid = pid[0][0]
    pi = d.q("SELECT InvoiceNumber, InvoiceDate, PurchaseOrderID, SupplierID, SubTotal, TaxAmount, GrandTotal, Status, ReceivedDate FROM PurchaseInvoice WHERE PurchaseInvoiceID = ?", pid)[0]
    pil = d.q("SELECT PILineID, POLineID, GoodsReceiptLineID, ItemID, Quantity, UnitCost, LineTotal FROM PurchaseInvoiceLine WHERE PurchaseInvoiceID = ?", pid)[0]
    grl = d.q("SELECT GoodsReceiptLineID, GoodsReceiptID, POLineID, QuantityReceived, ExtendedStandardCost FROM GoodsReceiptLine WHERE GoodsReceiptLineID = ?", pil[2])[0]
    gr = d.q("SELECT GoodsReceiptID, ReceiptNumber, ReceiptDate, PurchaseOrderID FROM GoodsReceipt WHERE GoodsReceiptID = ?", grl[1])[0]
    pol = d.q("SELECT POLineID, PurchaseOrderID, Quantity, UnitCost, LineTotal FROM PurchaseOrderLine WHERE POLineID = ?", pil[1])[0]
    po = d.q("SELECT PurchaseOrderID, PONumber, OrderDate, SupplierID FROM PurchaseOrder WHERE PurchaseOrderID = ?", pol[1])[0]
    sup = d.q("SELECT SupplierID, SupplierName FROM Supplier WHERE SupplierID = ?", pi[3])[0]
    it = d.q("SELECT ItemCode, ItemName, InventoryAccountID FROM Item WHERE ItemID = ?", pil[3])[0]
    pay = d.q("SELECT DisbursementID, PaymentNumber, PaymentDate, Amount, PaymentMethod FROM DisbursementPayment WHERE PurchaseInvoiceID = ?", pid)[0]
    claim(grl[2] == pil[1] and gr[3] == pol[1] == po[0] == pi[2] and po[3] == pi[3], "the invoice, the receipt and the order agree on the order line, the order and the supplier")

    def rows(source, doc):
        return [dict(id=r["id"], date=r["date"], account_id=r["account_id"], number=r["number"], name=r["name"], debit=r["debit"], credit=r["credit"], line=r["line"])
                for r in gl_rows_of(d, source, doc)]
    gl_pi, gl_gr, gl_dp = rows("PurchaseInvoice", pid), rows("GoodsReceipt", gr[0]), rows("DisbursementPayment", pay[0])
    for name, g in (("invoice", gl_pi), ("goods receipt", gl_gr), ("payment", gl_dp)):
        claim(abs(sum(r["debit"] for r in g) - sum(r["credit"] for r in g)) < 0.005, f"the ledger rows of the {name} balance")
    claim([r["number"] for r in gl_pi] == [2020, 5060, 2010], "the invoice debits goods received not invoiced and purchase price variance, and credits accounts payable")
    claim([r["number"] for r in gl_gr][1:] == [2020] and gl_gr[0]["account_id"] == it[2], "the receipt debits the item's inventory account and credits goods received not invoiced")
    claim([r["number"] for r in gl_dp] == [2010, 1010], "the payment debits accounts payable and credits cash")
    claim(abs(gl_pi[0]["debit"] - grl[4]) < 0.005 and abs(gl_gr[1]["credit"] - grl[4]) < 0.005, "the invoice clears the receipt value that the receipt credited to 2020")
    variance = round(pil[6] - grl[4], 2)
    claim(abs((gl_pi[1]["debit"] - gl_pi[1]["credit"]) - variance) < 0.005 and abs(gl_pi[2]["credit"] - pi[6]) < 0.005,
          "the price variance is the invoice line's total less the receipt value, and the payable is the GrandTotal")
    claim(gl_pi[0]["line"] == pil[0] and gl_gr[0]["line"] == grl[0] and gl_dp[0]["line"] is None, "the invoice row carries the invoice line's key, the receipt row the receipt line's key, and the payment row none")
    claim(all(r["date"] == pi[8] for r in gl_pi) and all(r["date"] == gr[2] for r in gl_gr) and all(r["date"] == pay[2] for r in gl_dp),
          "the invoice posts on its received date, the receipt on its receipt date and the payment on its payment date")

    # what holds for any invoice a student may pick
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoice p LEFT JOIN (SELECT SourceDocumentID id, SUM(Credit) c FROM GLEntry g JOIN Account a USING (AccountID) "
                "WHERE g.SourceDocumentType = 'PurchaseInvoice' AND a.AccountNumber = 2010 GROUP BY 1) x ON x.id = p.PurchaseInvoiceID "
                "WHERE x.c IS NULL OR ABS(x.c - p.GrandTotal) > 0.005") == 0, "every purchase invoice credits accounts payable for its GrandTotal")
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM GLEntry WHERE SourceDocumentType IN ('PurchaseInvoice', 'GoodsReceipt', 'DisbursementPayment') "
                "GROUP BY SourceDocumentType, SourceDocumentID HAVING ABS(SUM(Debit) - SUM(Credit)) > 0.005)") == 0, "every purchase document's ledger rows balance")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine l JOIN GoodsReceiptLine r USING (GoodsReceiptLineID) WHERE l.POLineID <> r.POLineID") == 0,
          "an invoice line and the receipt line it names are on the same order line")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine WHERE GoodsReceiptLineID IS NULL AND (AccrualJournalEntryID IS NULL OR POLineID IS NOT NULL)") == 0,
          "an invoice line with no receipt line has no order line and names an accrual journal entry")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoice p WHERE TaxAmount > 0 AND NOT EXISTS (SELECT 1 FROM GLEntry g WHERE g.SourceDocumentType = 'PurchaseInvoice' "
                "AND g.SourceDocumentID = p.PurchaseInvoiceID AND g.SourceLineID IS NULL AND ABS(g.Debit - p.TaxAmount) < 0.005)") == 0,
          "an invoice with tax posts the tax to 5060 in a row with no SourceLineID")
    differ = d.q("SELECT p.PurchaseInvoiceID, p.InvoiceNumber, g.VoucherNumber FROM PurchaseInvoice p JOIN GLEntry g ON g.SourceDocumentType = 'PurchaseInvoice' "
                 "AND g.SourceDocumentID = p.PurchaseInvoiceID WHERE g.VoucherNumber <> p.InvoiceNumber GROUP BY 1, 2, 3")
    repeated = d.one("SELECT COUNT(*) FROM (SELECT 1 FROM PurchaseInvoice GROUP BY SupplierID, InvoiceNumber HAVING COUNT(*) > 1)")
    claim(len(differ) == repeated and all(d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE SupplierID = (SELECT SupplierID FROM PurchaseInvoice WHERE PurchaseInvoiceID = ?) "
                                                "AND InvoiceNumber = ?", r[0], r[1]) == 2 for r in differ),
          "the ledger's VoucherNumber differs from the InvoiceNumber only for the invoices whose supplier number repeats, one for each repeated number")
    paid_one = d.one("SELECT COUNT(*) FROM PurchaseInvoice pi WHERE pi.Status = 'Paid' AND (SELECT COUNT(*) FROM PurchaseInvoiceLine x WHERE x.PurchaseInvoiceID = pi.PurchaseInvoiceID) = 1")
    paid = d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE Status = 'Paid'")
    claim(paid_one / paid > 0.9, "nearly every paid invoice has a single line")
    accrual = d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine WHERE GoodsReceiptLineID IS NULL")
    claim(accrual > 0, "some invoice lines have no receipt line")
    pays = d.q("SELECT n, COUNT(*) FROM (SELECT COUNT(*) n FROM DisbursementPayment GROUP BY PurchaseInvoiceID) GROUP BY 1 ORDER BY 1")
    claim(len(pays) > 1, "some invoices are paid in more than one payment")
    split = d.one("SELECT COUNT(*) FROM (SELECT GoodsReceiptLineID FROM PurchaseInvoiceLine WHERE GoodsReceiptLineID IS NOT NULL GROUP BY 1 HAVING COUNT(*) > 1)")
    claim(split > 0, "some receipt lines are billed on more than one invoice line")
    same = d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE SourceDocumentID = ? GROUP BY 1 ORDER BY 2 DESC, 1", pid)
    claim(len(same) > 1, "the invoice's key alone also finds ledger rows of other document types")
    return dict(
        pid=pid, pi=dict(number=pi[0], date=pi[1], received=pi[8], order_id=pi[2], supplier_id=pi[3], subtotal=pi[4], total=pi[6], status=pi[7]),
        pil=dict(id=pil[0], po_line=pil[1], receipt_line=pil[2], item_id=pil[3], quantity=pil[4], cost=pil[5], total=pil[6]),
        grl=dict(id=grl[0], receipt_id=grl[1], quantity=grl[3], cost=grl[4]), gr=dict(id=gr[0], number=gr[1], date=gr[2], order_id=gr[3]),
        pol=dict(id=pol[0], order_id=pol[1], quantity=pol[2], cost=pol[3], total=pol[4]), po=dict(id=po[0], number=po[1], date=po[2], supplier_id=po[3]),
        supplier=dict(id=sup[0], name=sup[1]), item=dict(code=it[0], name=it[1]), pay=dict(id=pay[0], number=pay[1], date=pay[2], amount=pay[3], method=pay[4]),
        gl_pi=gl_pi, gl_gr=gl_gr, gl_dp=gl_dp, variance=variance, variance_abs=abs(variance), variance_side="unfavorable" if variance > 0 else "favorable",
        paid_one=paid_one, paid=paid, accrual=accrual, pays=pays, single=dict(pays)[1], multi=sum(n for k, n in pays if k > 1), split=split, same=same, same_rows=sum(n for _, n in same), same_types=len(same),
        differ=len(differ), repeated=repeated,
        rows=rows_of(d, ["PurchaseInvoice", "PurchaseInvoiceLine", "GoodsReceiptLine", "PurchaseOrderLine", "DisbursementPayment"]))


# --- Exercise 3.2: mapping the O2C group -----------------------------------------------------------------------------------

EX2_ROLES = [("Customer", "CustomerID", "SalesOrder", "CustomerID"), ("SalesOrder", "SalesOrderID", "SalesOrderLine", "SalesOrderID"),
             ("Item", "ItemID", "SalesOrderLine", "ItemID"), ("SalesOrder", "SalesOrderID", "Shipment", "SalesOrderID"),
             ("Shipment", "ShipmentID", "ShipmentLine", "ShipmentID"), ("SalesOrderLine", "SalesOrderLineID", "ShipmentLine", "SalesOrderLineID"),
             ("SalesOrder", "SalesOrderID", "SalesInvoice", "SalesOrderID"), ("SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID"),
             ("ShipmentLine", "ShipmentLineID", "SalesInvoiceLine", "ShipmentLineID"), ("SalesOrderLine", "SalesOrderLineID", "SalesInvoiceLine", "SalesOrderLineID"),
             ("CashReceipt", "CashReceiptID", "CashReceiptApplication", "CashReceiptID"), ("SalesInvoice", "SalesInvoiceID", "CashReceiptApplication", "SalesInvoiceID")]


@context("ch03.ex2")
def ex2(d, claim):
    have = schema(d, claim, {t: [f"{t}ID"] for t in O2C_DIAGRAM} | {"SalesOrder": ["CostCenterID", "CustomerID"], "CostCenter": ["CostCenterID", "CostCenterName"],
                                                                    "GLEntry": ["AccountID", "CostCenterID", "SourceDocumentType", "SourceDocumentID", "Debit", "Credit", "FiscalYear", "FiscalPeriod"],
                                                                    "Account": ["AccountType", "AccountSubType"], "Item": ["RevenueAccountID", "COGSAccountID", "InventoryAccountID"]})
    in_group(claim, {"Customer": "Order-to-Cash", "SalesOrder": "Order-to-Cash", "SalesOrderLine": "Order-to-Cash", "Shipment": "Order-to-Cash",
                     "SalesInvoice": "Order-to-Cash", "CashReceipt": "Order-to-Cash", "Item": "Master Data", "GLEntry": "Accounting Core"})
    rel = [card(d, c, fk, p, pk) for p, pk, c, fk in EX2_ROLES]
    claim(all(r["orphans"] == 0 for r in rel), "no foreign key of the revenue cycle has an orphaned value")
    claim(sum(1 for r in rel if r["blank"]) == 1 and next(r for r in rel if r["blank"])["child"] == "SalesInvoiceLine", "only SalesInvoiceLine.ShipmentLineID is ever blank among the cycle's keys")
    claim(next(r for r in rel if r["child"] == "SalesInvoiceLine" and r["fk"] == "SalesOrderLineID")["blank"] == 0, "every invoice line names an order line")
    # what the O2C tables lack
    no_account = [t for t in O2C_DIAGRAM if t != "Item" and not any("AccountID" in c for c in have.get(t, []))]
    claim(len(no_account) == len(O2C_DIAGRAM) - 1, "no O2C table of the diagram has an account column")
    cc_tables = [t for t in O2C_DIAGRAM if t != "Item" and "CostCenterID" in [r[1] for r in d.q(f"PRAGMA table_info({t})")]]
    claim(cc_tables == ["SalesOrder"], "SalesOrder is the only O2C table of the diagram with a CostCenterID")
    cc = d.q("SELECT c.CostCenterName, COUNT(*) FROM SalesOrder o JOIN CostCenter c USING (CostCenterID) GROUP BY 1 ORDER BY 2 DESC")
    claim(len(cc) == 2, "orders belong to two cost centers")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN SalesInvoice i ON i.SalesInvoiceID = g.SourceDocumentID JOIN SalesOrder o ON o.SalesOrderID = i.SalesOrderID "
                "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.CostCenterID IS NOT NULL AND g.CostCenterID <> o.CostCenterID") == 0,
          "the cost center on an invoice's ledger rows is the cost center of its order")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.SourceDocumentType = 'SalesInvoice' AND a.AccountNumber IN (1020, 2050) AND g.CostCenterID IS NOT NULL") == 0
          and d.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.SourceDocumentType = 'SalesInvoice' AND a.AccountNumber NOT IN (1020, 2050) AND g.CostCenterID IS NULL") == 0,
          "an invoice's receivable and sales tax rows carry no cost center, and its revenue rows carry one")
    sales_acct = d.q("SELECT a.AccountType, COUNT(*) FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.SourceDocumentType = 'SalesInvoice' GROUP BY 1 ORDER BY 1")
    claim([a for a, _ in sales_acct] == ["Asset", "Liability", "Revenue"], "an invoice's ledger rows are on asset, liability and revenue accounts")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE ItemGroup <> 'Services' AND ListPrice IS NOT NULL AND (RevenueAccountID IS NULL OR COGSAccountID IS NULL OR InventoryAccountID IS NULL)") == 0,
          "every item with a list price outside Services maps to a revenue, a cost of goods sold and an inventory account")
    posted = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE SalesInvoiceID NOT IN (SELECT SourceDocumentID FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice')")
    claim(posted == 0, "every sales invoice has ledger rows")
    t = trace_ids(d)
    cols = {tb: len(have[tb]) for tb in O2C_DIAGRAM}
    receipts = d.one("SELECT COUNT(*) FROM CashReceipt")
    direct = d.one("SELECT COUNT(*) FROM CashReceipt WHERE SalesInvoiceID IS NOT NULL")
    claim(0 < direct < 0.2 * receipts, "CashReceipt.SalesInvoiceID is filled for only a small share of the receipts")
    roles = {"SalesInvoiceID": "primary key", "InvoiceNumber": "unique document number", "SalesOrderID": "foreign key to SalesOrder", "CustomerID": "foreign key to Customer"}
    si_cols = [dict(name=r[1], type=r[2], role=roles.get(r[1], "")) for r in d.q("PRAGMA table_info(SalesInvoice)")]
    claim(all(c["name"] in [x["name"] for x in si_cols] for c in [dict(name=n) for n in roles]), "SalesInvoice has the columns of the model dictionary entry")
    claim({c["type"] for c in si_cols} == {"INTEGER", "REAL", "TEXT"}, "SalesInvoice uses all three declared types")
    return dict(receipts=receipts, direct=direct, si_cols=si_cols, rel=rel, n_orphans=sum(r["orphans"] for r in rel), rows=rows_of(d, O2C_DIAGRAM + ["GLEntry", "Account"]), cols=cols, cc=cc, cc_name=cc[0][0], cc_other=cc[1][0], cc_orders=cc[0][1],
                cc_other_orders=cc[1][1], sales_accounts=sales_acct, invoices_unposted=posted, invoice=t["id.trace.invoice"], invoice_id=t["id.trace.invoice_id"],
                n_tables=len(O2C_DIAGRAM))


# --- Exercise 3.3: mapping the Manufacturing group -----------------------------------------------------------------------

MFG = ["BillOfMaterial", "BillOfMaterialLine", "WorkOrder", "WorkOrderOperation", "MaterialIssue", "MaterialIssueLine", "ProductionCompletion",
       "ProductionCompletionLine", "WorkOrderClose"]
EX3_SCHEMA = {
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "SupplyMode", "StandardCost", "StandardConversionCost", "LifecycleStatus"],
    "BillOfMaterial": ["BOMID", "ParentItemID", "VersionNumber", "Status", "StandardBatchQuantity"],
    "BillOfMaterialLine": ["BOMLineID", "BOMID", "ComponentItemID", "QuantityPerUnit", "ScrapFactorPct"],
    "WorkOrder": ["WorkOrderID", "ItemID", "BOMID", "PlannedQuantity", "Status", "ClosedDate"],
    "MaterialIssue": ["MaterialIssueID", "WorkOrderID"],
    "MaterialIssueLine": ["MaterialIssueLineID", "MaterialIssueID", "BOMLineID", "ItemID", "QuantityIssued", "ExtendedStandardCost"],
    "ProductionCompletion": ["ProductionCompletionID", "WorkOrderID"],
    "ProductionCompletionLine": ["ProductionCompletionLineID", "ProductionCompletionID", "ItemID", "QuantityCompleted", "ExtendedStandardMaterialCost",
                                 "ExtendedStandardConversionCost", "ExtendedStandardTotalCost"],
    "WorkOrderClose": ["WorkOrderCloseID", "WorkOrderID", "MaterialVarianceAmount", "DirectLaborVarianceAmount", "OverheadVarianceAmount",
                       "ConversionVarianceAmount", "TotalVarianceAmount"],
    "LaborTimeEntry": ["WorkOrderID", "ExtendedLaborCost"], "GLEntry": ["SourceDocumentType", "SourceDocumentID", "Debit", "Credit", "AccountID"],
}


@context("ch03.ex3")
def ex3(d, claim):
    schema(d, claim, EX3_SCHEMA)
    in_group(claim, {"BillOfMaterial": "Manufacturing", "WorkOrder": "Manufacturing", "MaterialIssue": "Manufacturing", "ProductionCompletion": "Manufacturing",
                     "WorkOrderClose": "Manufacturing", "LaborTimeEntry": "Payroll and Time", "Item": "Master Data"})
    claim(all(d.one(f"SELECT COUNT(*) FROM sqlite_master WHERE name = '{t}'") for t in ("Routing", "RoutingOperation", "WorkCenter")),
          "Routing, RoutingOperation and WorkCenter tables exist beyond the focused diagram")
    manufactured = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured'")
    with_bom = d.one("SELECT COUNT(DISTINCT ParentItemID) FROM BillOfMaterial")
    boms = d.one("SELECT COUNT(*) FROM BillOfMaterial")
    no_bom = d.q("SELECT LifecycleStatus FROM Item WHERE SupplyMode = 'Manufactured' AND ItemID NOT IN (SELECT ParentItemID FROM BillOfMaterial)")
    claim(boms == with_bom and with_bom < manufactured, "each manufactured item with a bill has exactly one bill, and a few manufactured items have none")
    claim(all(s == "Discontinued" for (s,) in no_bom) and d.one("SELECT COUNT(*) FROM WorkOrder WHERE ItemID IN (SELECT ItemID FROM Item WHERE SupplyMode = 'Manufactured' "
                                                               "AND ItemID NOT IN (SELECT ParentItemID FROM BillOfMaterial))") == 0,
          "the manufactured items with no bill are discontinued and were never put on a work order")
    claim(d.one("SELECT COUNT(*) FROM BillOfMaterialLine WHERE ComponentItemID IN (SELECT ParentItemID FROM BillOfMaterial)") == 0,
          "no component is itself a parent item, so each bill has one level")
    comp_groups = [r[0] for r in d.q("SELECT i.ItemGroup FROM BillOfMaterialLine l JOIN Item i ON i.ItemID = l.ComponentItemID GROUP BY 1 ORDER BY 1")]
    claim(comp_groups == ["Packaging", "Raw Materials"], "the components are raw materials and packaging")
    claim(d.one("SELECT COUNT(*) FROM BillOfMaterial WHERE StandardBatchQuantity <> 1") == 0, "every bill is for a batch of one unit")
    roll = d.q("""SELECT i.ItemID, i.StandardCost, i.StandardConversionCost, (SELECT SUM(l.QuantityPerUnit * (1 + l.ScrapFactorPct) * c.StandardCost)
                  FROM BillOfMaterialLine l JOIN Item c ON c.ItemID = l.ComponentItemID JOIN BillOfMaterial b ON b.BOMID = l.BOMID WHERE b.ParentItemID = i.ItemID),
                  (SELECT SUM(l.QuantityPerUnit * c.StandardCost) FROM BillOfMaterialLine l JOIN Item c ON c.ItemID = l.ComponentItemID
                   JOIN BillOfMaterial b ON b.BOMID = l.BOMID WHERE b.ParentItemID = i.ItemID) FROM Item i WHERE i.ItemID IN (SELECT ParentItemID FROM BillOfMaterial)""")
    claim(all(abs(r[1] - (r[2] + r[3])) < 0.02 for r in roll), "an item's StandardCost is its conversion cost plus the bill's material cost, with each line's quantity raised by its scrap factor")
    claim(not any(abs(r[1] - (r[2] + r[4])) < 0.02 for r in roll), "the same roll-up without the scrap factor never reproduces StandardCost")
    # the model product: the first manufactured item by code with a bill and at least one closed work order
    mid = d.q("SELECT i.ItemID, i.ItemCode, i.ItemName, i.ItemGroup, i.StandardCost, i.StandardConversionCost, b.BOMID, b.VersionNumber, b.Status FROM Item i "
              "JOIN BillOfMaterial b ON b.ParentItemID = i.ItemID WHERE i.ItemID IN (SELECT w.ItemID FROM WorkOrder w JOIN WorkOrderClose c USING (WorkOrderID)) "
              "ORDER BY i.ItemCode LIMIT 1")
    claim(len(mid) == 1, "a manufactured item has a bill and closed work orders")
    mid = mid[0]
    lines = [dict(line=r[0], code=r[1], name=r[2], group=r[3], cost=r[4], quantity=r[5], scrap=r[6])
             for r in d.q("SELECT l.LineNumber, c.ItemCode, c.ItemName, c.ItemGroup, c.StandardCost, l.QuantityPerUnit, l.ScrapFactorPct FROM BillOfMaterialLine l "
                          "JOIN Item c ON c.ItemID = l.ComponentItemID WHERE l.BOMID = ? ORDER BY l.LineNumber", mid[6])]
    material = sum(x["quantity"] * (1 + x["scrap"]) * x["cost"] for x in lines)
    claim(abs(mid[4] - (mid[5] + material)) < 0.02, "the model item's StandardCost is its conversion cost plus its material roll-up")
    per_unit = d.one("SELECT SUM(ExtendedStandardMaterialCost) / SUM(QuantityCompleted) FROM ProductionCompletionLine WHERE ItemID = ?", mid[0])
    claim(abs(per_unit - material) < 0.02, "the standard material cost per unit on the completion lines equals the bill's roll-up")
    # work orders, completions, closes
    statuses = d.q("SELECT Status, COUNT(*), SUM(ClosedDate IS NOT NULL) FROM WorkOrder GROUP BY 1 ORDER BY 2 DESC")
    claim(sum(n for s, n, c in statuses if c) == d.one("SELECT COUNT(*) FROM WorkOrderClose") and all((c == n) if s == "Closed" else c == 0 for s, n, c in statuses),
          "a work order has a close exactly when its status is Closed")
    claim(d.one("SELECT COUNT(*) FROM (SELECT WorkOrderID FROM WorkOrderClose GROUP BY 1 HAVING COUNT(*) > 1)") == 0, "no work order is closed twice")
    claim(d.one("SELECT COUNT(*) FROM ProductionCompletionLine l JOIN ProductionCompletion p USING (ProductionCompletionID) JOIN WorkOrder w USING (WorkOrderID) "
                "WHERE l.ItemID <> w.ItemID") == 0, "a completion line is for the item of its work order")
    claim(d.one("SELECT COUNT(*) FROM (SELECT ProductionCompletionID FROM ProductionCompletionLine GROUP BY 1 HAVING COUNT(*) <> 1)") == 0, "each completion has exactly one line")
    spread = d.q("SELECT n, COUNT(*) FROM (SELECT COUNT(p.ProductionCompletionID) n FROM WorkOrder w LEFT JOIN ProductionCompletion p USING (WorkOrderID) GROUP BY w.WorkOrderID) GROUP BY 1 ORDER BY 1")
    claim(any(n > 1 for n, _ in spread), "some work orders are completed in several parts")
    plan = d.one("SELECT COUNT(*) FROM WorkOrder w JOIN (SELECT p.WorkOrderID, SUM(l.QuantityCompleted) q FROM ProductionCompletion p JOIN ProductionCompletionLine l USING "
                 "(ProductionCompletionID) GROUP BY 1) x USING (WorkOrderID) WHERE w.Status IN ('Closed', 'Completed') AND ABS(w.PlannedQuantity - x.q) > 0.0001")
    claim(plan == 0, "on every closed or completed work order the quantity completed equals the planned quantity")
    claim(d.one("SELECT COUNT(*) FROM WorkOrderClose WHERE ABS(TotalVarianceAmount - (MaterialVarianceAmount + ConversionVarianceAmount)) > 0.011 "
                "OR ABS(ConversionVarianceAmount - (DirectLaborVarianceAmount + OverheadVarianceAmount)) > 0.011") == 0,
          "a close's total variance is its material variance plus its conversion variance, and the conversion variance is labor plus overhead")
    claim(d.one("SELECT COUNT(*) FROM WorkOrderClose c WHERE ABS(c.MaterialVarianceAmount - (COALESCE((SELECT SUM(ml.ExtendedStandardCost) FROM MaterialIssue m JOIN MaterialIssueLine ml "
                "USING (MaterialIssueID) WHERE m.WorkOrderID = c.WorkOrderID), 0) - COALESCE((SELECT SUM(pl.ExtendedStandardMaterialCost) FROM ProductionCompletion p "
                "JOIN ProductionCompletionLine pl USING (ProductionCompletionID) WHERE p.WorkOrderID = c.WorkOrderID), 0))) > 0.011") == 0,
          "a close's material variance is the material issued at standard less the standard material of the units completed")
    claim(d.one("SELECT COUNT(*) FROM WorkOrderClose c WHERE ABS(c.TotalVarianceAmount - COALESCE((SELECT SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                "WHERE g.SourceDocumentType = 'WorkOrderClose' AND g.SourceDocumentID = c.WorkOrderCloseID AND a.AccountNumber = 5080), 0)) > 0.011") == 0,
          "a close's total variance is the net debit that it posts to 5080, so a positive amount is unfavorable")
    v = d.q("SELECT COUNT(*), SUM(c.MaterialVarianceAmount), SUM(c.DirectLaborVarianceAmount), SUM(c.OverheadVarianceAmount), SUM(c.ConversionVarianceAmount), "
            "SUM(c.TotalVarianceAmount) FROM WorkOrderClose c JOIN WorkOrder w USING (WorkOrderID) WHERE w.ItemID = ?", mid[0])[0]
    units = d.one("SELECT SUM(l.QuantityCompleted) FROM ProductionCompletionLine l JOIN ProductionCompletion p USING (ProductionCompletionID) JOIN WorkOrder w USING (WorkOrderID) "
                  "JOIN WorkOrderClose c USING (WorkOrderID) WHERE w.ItemID = ?", mid[0])
    released = d.one("SELECT SUM(l.ExtendedStandardTotalCost) FROM ProductionCompletionLine l JOIN ProductionCompletion p USING (ProductionCompletionID) JOIN WorkOrder w USING "
                     "(WorkOrderID) JOIN WorkOrderClose c USING (WorkOrderID) WHERE w.ItemID = ?", mid[0])
    labor_hours = d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE WorkOrderID IN (SELECT WorkOrderID FROM WorkOrder WHERE ItemID = ?)", mid[0])
    claim(labor_hours > 0, "the model item's work orders have labor time entries, which live in the Payroll and Time group")
    return dict(
        sm=lambda x: ("-" if x < 0 else "") + "$" + f"{abs(x):,.2f}",
        rows=rows_of(d, MFG), manufactured=manufactured, with_bom=with_bom, no_bom=len(no_bom), n_roll=len(roll),
        item=dict(id=mid[0], code=mid[1], name=mid[2], group=mid[3], cost=mid[4], conversion=mid[5], bom=mid[6], version=mid[7], status=mid[8].lower()),
        lines=lines, material=material, noscrap=sum(x["quantity"] * x["cost"] for x in lines), per_unit=per_unit, no_completion=dict(spread).get(0, 0), statuses=statuses, spread=spread, one_completion=dict(spread).get(1, 0),
        open_orders=sum(n for s, n, c in statuses if not c), closes=d.one("SELECT COUNT(*) FROM WorkOrderClose"),
        v=dict(closes=v[0], material=v[1], labor=v[2], overhead=v[3], conversion=v[4], total=v[5], units=units, released=released, per_unit=v[5] / units),
        labor_entries=labor_hours, components=and_join(x.lower() for x in comp_groups))


# --- Exercise 3.4: the keys behind a budget-versus-actual report ----------------------------------------------------------

EX4_SCHEMA = {
    "CostCenter": ["CostCenterID", "CostCenterName", "ParentCostCenterID", "ManagerID", "IsActive"],
    "Budget": ["BudgetID", "FiscalYear", "Month", "CostCenterID", "AccountID", "BudgetAmount"],
    "BudgetLine": ["BudgetLineID", "FiscalYear", "Month", "AccountID", "CostCenterID", "ItemID", "WarehouseID", "BudgetAmount", "BudgetCategory"],
    "GLEntry": ["AccountID", "CostCenterID", "FiscalYear", "FiscalPeriod", "VoucherNumber"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType"],
    "Employee": ["EmployeeID", "JobTitle"],
}


@context("ch03.ex4")
def ex4(d, claim):
    schema(d, claim, EX4_SCHEMA)
    in_group(claim, {"CostCenter": "Organizational Planning", "Budget": "Organizational Planning", "BudgetLine": "Organizational Planning", "GLEntry": "Accounting Core"})
    C = d.C
    cc = d.q("SELECT CostCenterID, CostCenterName, ParentCostCenterID, ManagerID FROM CostCenter ORDER BY CostCenterID")
    claim(all(r[2] is None for r in cc), "no cost center has a parent: the cost centers form a flat list")
    claim(all(r[3] is not None for r in cc) and d.one("SELECT COUNT(*) FROM CostCenter WHERE ManagerID NOT IN (SELECT EmployeeID FROM Employee)") == 0,
          "every cost center names an existing employee as its manager")
    claim(d.one("SELECT COUNT(*) FROM Account WHERE ParentAccountID IS NOT NULL") > 0, "the chart of accounts, unlike the cost centers, has parent accounts")
    # the relationships
    gl_cc = card(d, "GLEntry", "CostCenterID", "CostCenter", "CostCenterID")
    claim(gl_cc["orphans"] == 0 and gl_cc["blank"] > 0 and gl_cc["childless"] == 0, "a ledger row has zero or one cost center, and every cost center has ledger rows")
    bud_cc = card(d, "Budget", "CostCenterID", "CostCenter", "CostCenterID")
    bud_acct = card(d, "Budget", "AccountID", "Account", "AccountID")
    line_cc = card(d, "BudgetLine", "CostCenterID", "CostCenter", "CostCenterID")
    line_acct = card(d, "BudgetLine", "AccountID", "Account", "AccountID")
    claim(bud_cc["blank"] == 0 and bud_acct["blank"] == 0 and bud_cc["orphans"] == 0 and bud_acct["orphans"] == 0, "every Budget row names a cost center and an account that exist")
    claim(line_cc["blank"] > 0 and line_cc["orphans"] == 0 and line_acct["orphans"] == 0, "some BudgetLine rows have no cost center, and none names a missing one")
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Budget GROUP BY FiscalYear, Month, CostCenterID, AccountID HAVING COUNT(*) > 1)") == 0,
          "Budget has one row for each fiscal year, month, cost center and account")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE FiscalPeriod < 1 OR FiscalPeriod > 12") == 0, "GLEntry.FiscalPeriod is a month number, the same as Budget.Month")
    # the accounts each table covers
    b_accounts = d.one("SELECT COUNT(DISTINCT AccountID) FROM Budget")
    types = [r[0] for r in d.q("SELECT a.AccountType FROM Budget b JOIN Account a USING (AccountID) GROUP BY 1 ORDER BY 1")]
    claim(types == ["Expense", "Revenue"], "Budget covers revenue and expense accounts only")
    line_cats = d.q("SELECT BudgetCategory, COUNT(DISTINCT AccountID), COUNT(*), SUM(CostCenterID IS NULL), SUM(ItemID IS NULL) FROM BudgetLine GROUP BY 1 ORDER BY 1")
    claim([c for c, *_ in line_cats] == ["Balance Sheet", "COGS", "Operating Expense", "Revenue"], "BudgetLine has balance sheet, cost of goods sold, operating expense and revenue lines")
    line_accounts = d.one("SELECT COUNT(DISTINCT AccountID) FROM BudgetLine")
    claim(line_accounts > b_accounts, "BudgetLine covers more accounts than Budget")
    claim(d.one("SELECT COUNT(*) FROM Budget b LEFT JOIN (SELECT FiscalYear, Month, CostCenterID, AccountID, SUM(BudgetAmount) s FROM BudgetLine GROUP BY 1, 2, 3, 4) l "
                "USING (FiscalYear, Month, CostCenterID, AccountID) WHERE ABS(b.BudgetAmount - COALESCE(l.s, 0)) > 0.01") == 0,
          "every Budget row is the sum of the BudgetLine rows with the same year, month, cost center and account")
    # (4) every budgeted account has ledger activity
    in_gl = d.one("SELECT COUNT(DISTINCT AccountID) FROM Budget WHERE AccountID IN (SELECT AccountID FROM GLEntry)")
    claim(in_gl == b_accounts, "every account in Budget has ledger rows")
    unbudgeted = d.q("SELECT a.AccountNumber, a.AccountName FROM Account a WHERE a.AccountType IN ('Revenue', 'Expense') AND a.AccountID IN (SELECT AccountID FROM GLEntry) "
                     "AND a.AccountID NOT IN (SELECT AccountID FROM Budget) ORDER BY 1")
    claim(len(unbudgeted) > 0, "some revenue and expense accounts have ledger rows and no Budget rows")
    grain = d.q("SELECT b.FiscalYear, COUNT(*), SUM(EXISTS (SELECT 1 FROM GLEntry g WHERE g.FiscalYear = b.FiscalYear AND g.FiscalPeriod = b.Month AND "
                "g.CostCenterID = b.CostCenterID AND g.AccountID = b.AccountID)) FROM Budget b WHERE b.FiscalYear <= ? GROUP BY 1 ORDER BY 1", C)
    claim(all(m < n for _, n, m in grain), "some budgeted combinations of month, cost center and account have no ledger row")
    quiet = d.one("SELECT COUNT(*) FROM Budget WHERE FiscalYear = ?", C) - [m for y, n, m in grain if y == C][0]
    next_year = d.one("SELECT COUNT(*) FROM Budget WHERE FiscalYear = ?", d.N)
    matched_next = d.one("SELECT COUNT(*) FROM Budget b WHERE b.FiscalYear = ? AND EXISTS (SELECT 1 FROM GLEntry g WHERE g.FiscalYear = b.FiscalYear AND g.FiscalPeriod = b.Month "
                         "AND g.CostCenterID = b.CostCenterID AND g.AccountID = b.AccountID)", d.N)
    claim(next_year > 0 and matched_next == 0, "no Budget row of the next fiscal year has a matching ledger row, because the ledger holds only supplier payments for that year")
    return dict(
        cc=[dict(id=r[0], name=r[1], manager=r[3]) for r in cc], n_cc=len(cc), gl_cc=gl_cc, bud_cc=bud_cc, line_cc=line_cc, line_acct=line_acct,
        n_budget_accounts=b_accounts, n_line_accounts=line_accounts, line_cats=[dict(category=r[0], accounts=r[1], rows=r[2], no_cc=r[3], no_item=r[4]) for r in line_cats],
        n_unbudgeted=len(unbudgeted), unbudgeted_first=and_join(f"{n} {name}" for n, name in unbudgeted[:4]), gl_accounts=d.one("SELECT COUNT(DISTINCT AccountID) FROM GLEntry"), budget_rows=d.one("SELECT COUNT(*) FROM Budget"), line_rows=d.one("SELECT COUNT(*) FROM BudgetLine"),
        year=C, matched=[m for y, n, m in grain if y == C][0], budget_year=[n for y, n, m in grain if y == C][0], quiet=quiet, next_year=d.N, next_rows=next_year,
        in_gl=in_gl)


# --- Exercise 3.5: a data extraction plan for three audit procedures -----------------------------------------------------

EX5_SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "CustomerID", "GrandTotal"], "SalesInvoiceLine": ["SalesInvoiceID", "ItemID", "ShipmentLineID", "LineTotal"],
    "Shipment": ["ShipmentID", "SalesOrderID"], "ShipmentLine": ["ShipmentLineID", "ShipmentID", "ItemID", "QuantityShipped", "ExtendedStandardCost"],
    "ServiceTimeEntry": ["ServiceEngagementID", "BillableHours", "BillingStatus"], "ServiceBillingLine": ["ServiceEngagementID", "SalesInvoiceLineID", "BilledHours"],
    "PurchaseOrderLine": ["POLineID", "PurchaseOrderID", "Quantity", "UnitCost"], "GoodsReceiptLine": ["GoodsReceiptLineID", "POLineID", "QuantityReceived", "ExtendedStandardCost"],
    "PurchaseInvoiceLine": ["PILineID", "POLineID", "GoodsReceiptLineID", "AccrualJournalEntryID", "Quantity", "UnitCost"],
    "JournalEntry": ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount", "CreatedByEmployeeID", "CreatedDate", "ApprovedByEmployeeID", "ApprovedDate"],
    "GLEntry": ["SourceDocumentType", "SourceDocumentID", "VoucherNumber", "AccountID", "Debit", "Credit", "CostCenterID", "PostingDate"],
    "Employee": ["EmployeeID", "JobTitle", "MaxApprovalAmount"],
}


@context("ch03.ex5")
def ex5(d, claim):
    have = schema(d, claim, EX5_SCHEMA)
    in_group(claim, {"SalesInvoice": "Order-to-Cash", "Shipment": "Order-to-Cash", "PurchaseOrder": "Procure-to-Pay", "GoodsReceipt": "Procure-to-Pay",
                     "PurchaseInvoice": "Procure-to-Pay", "JournalEntry": "Accounting Core", "GLEntry": "Accounting Core", "Employee": "Master Data"})
    # (1) revenue completeness
    invoices = d.one("SELECT COUNT(*) FROM SalesInvoice")
    unposted = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE SalesInvoiceID NOT IN (SELECT SourceDocumentID FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice')")
    stray = d.one("SELECT COUNT(DISTINCT SourceDocumentID) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND SourceDocumentID NOT IN (SELECT SalesInvoiceID FROM SalesInvoice)")
    claim(unposted == 0 and stray == 0, "every sales invoice has ledger rows, and every ledger row of that type names an invoice")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice WHERE CustomerID NOT IN (SELECT CustomerID FROM Customer)") == 0 and
          d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ItemID NOT IN (SELECT ItemID FROM Item)") == 0, "every invoice names a customer and every invoice line an item that exist")
    lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    shipped = d.one("SELECT COUNT(*) FROM ShipmentLine")
    uninvoiced = d.q("SELECT s.ShipmentNumber, s.ShipmentDate, l.ExtendedStandardCost FROM ShipmentLine l JOIN Shipment s USING (ShipmentID) WHERE l.ShipmentLineID NOT IN "
                     "(SELECT ShipmentLineID FROM SalesInvoiceLine WHERE ShipmentLineID IS NOT NULL) ORDER BY s.ShipmentDate, l.ShipmentLineID")
    claim(0 < len(uninvoiced) <= 20, "a handful of shipment lines were never invoiced")
    last_ship = d.one("SELECT MAX(ShipmentDate) FROM Shipment")
    claim(all(r[1][:7] == last_ship[:7] for r in uninvoiced), "every shipment line never invoiced was shipped in the last month of shipments")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ShipmentLineID IS NULL") == d.one("SELECT COUNT(*) FROM ServiceBillingLine"),
          "the invoice lines with no shipment line are the service billing lines")
    hours = d.q("SELECT (SELECT SUM(BillableHours) FROM ServiceTimeEntry), (SELECT SUM(BilledHours) FROM ServiceBillingLine)")[0]
    claim(abs(hours[0] - hours[1]) < 0.005, "the billable hours recorded on service time entries equal the hours billed")
    claim(d.one("SELECT COUNT(*) FROM Customer c WHERE c.CustomerID NOT IN (SELECT CustomerID FROM SalesOrder)") > 0, "some customers have no orders")
    # (2) three-way match
    claim(d.one("SELECT COUNT(*) FROM GoodsReceiptLine r JOIN PurchaseOrderLine p USING (POLineID) WHERE ABS(r.ExtendedStandardCost - ROUND(r.QuantityReceived * p.UnitCost, 2)) > 0.011") == 0,
          "a receipt line's ExtendedStandardCost is its quantity times the order line's UnitCost, so the receipt records no price of its own")
    claim("UnitCost" not in have["GoodsReceiptLine"], "GoodsReceiptLine has no unit cost column")
    po_lines = d.one("SELECT COUNT(*) FROM PurchaseOrderLine")
    unreceived = d.one("SELECT COUNT(*) FROM PurchaseOrderLine WHERE POLineID NOT IN (SELECT POLineID FROM GoodsReceiptLine)")
    parts = d.one("SELECT COUNT(*) FROM (SELECT POLineID FROM GoodsReceiptLine GROUP BY 1 HAVING COUNT(*) > 1)")
    split = d.one("SELECT COUNT(*) FROM (SELECT GoodsReceiptLineID FROM PurchaseInvoiceLine WHERE GoodsReceiptLineID IS NOT NULL GROUP BY 1 HAVING COUNT(*) > 1)")
    unmatched = d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine WHERE POLineID IS NULL")
    claim(unreceived > 0 and parts > 0 and split > 0 and unmatched > 0,
          "some order lines are never received, some are received in parts, some receipt lines are billed in parts, and some invoice lines have no order line")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine WHERE POLineID IS NULL AND (AccrualJournalEntryID IS NULL OR GoodsReceiptLineID IS NOT NULL)") == 0,
          "an invoice line with no order line names an accrual journal entry and no receipt line")
    price = d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine l JOIN PurchaseOrderLine p USING (POLineID) WHERE l.UnitCost <> p.UnitCost")
    claim(price > 0, "some invoice lines are billed at a unit cost that differs from the order line's")
    # (3) journal entry analysis
    entries = d.one("SELECT COUNT(*) FROM JournalEntry")
    je_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID WHERE g.SourceDocumentType = 'JournalEntry' "
                "AND (g.VoucherNumber <> j.EntryNumber OR g.PostingDate <> j.PostingDate)") == 0,
          "a journal entry's ledger rows carry its EntryNumber as VoucherNumber and its PostingDate")
    claim(d.one("SELECT COUNT(*) FROM JournalEntry j JOIN (SELECT SourceDocumentID id, SUM(Debit) s FROM GLEntry WHERE SourceDocumentType = 'JournalEntry' GROUP BY 1) g "
                "ON g.id = j.JournalEntryID WHERE ABS(g.s - j.TotalAmount) > 0.005") == 0 and d.one("SELECT COUNT(DISTINCT SourceDocumentID) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'") == entries,
          "every journal entry has ledger rows, and its TotalAmount is the total of their debits")
    claim("JournalEntryID" not in have["GLEntry"], "GLEntry has no JournalEntryID column")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID WHERE g.SourceDocumentType = 'JournalEntry' "
                "AND g.CreatedByEmployeeID <> j.CreatedByEmployeeID") == 0, "the ledger rows of a journal entry name the entry's creator")
    claim(d.one("SELECT COUNT(*) FROM JournalEntry WHERE ApprovedByEmployeeID IS NULL OR CreatedByEmployeeID IS NULL") == 0, "every journal entry names a creator and an approver")
    t = trace_ids(d)
    return dict(
        invoices=invoices, lines=lines, shipped=shipped, uninvoiced=uninvoiced, n_uninvoiced=len(uninvoiced), last_ship=last_ship,
        unposted=unposted, service_lines=d.one("SELECT COUNT(*) FROM ServiceBillingLine"), hours=hours[0],
        po_lines=po_lines, unreceived=unreceived, parts=parts, split=split, unmatched=unmatched, price=price,
        entries=entries, je_rows=je_rows, gl_rows=d.one("SELECT COUNT(*) FROM GLEntry"), je_cols=len(have["JournalEntry"]), gl_cols=len(have["GLEntry"]),
        invoice_id=t["id.trace.invoice_id"],
        rows=rows_of(d, ["SalesInvoice", "ShipmentLine", "PurchaseOrderLine", "GoodsReceiptLine", "PurchaseInvoiceLine", "JournalEntry"]))


# --- Exercise 3.6: referential integrity across the database -------------------------------------------------------------

EX6_TESTS = [
    ("SalesOrder", "CustomerID", "Customer", "CustomerID", "", "Order-to-Cash"),
    ("SalesOrderLine", "ItemID", "Item", "ItemID", "", "cross-group, into Master Data"),
    ("SalesOrderLine", "SalesOrderID", "SalesOrder", "SalesOrderID", "", "Order-to-Cash"),
    ("ShipmentLine", "SalesOrderLineID", "SalesOrderLine", "SalesOrderLineID", "", "Order-to-Cash"),
    ("SalesInvoice", "CustomerID", "Customer", "CustomerID", "", "Order-to-Cash"),
    ("SalesInvoiceLine", "SalesInvoiceID", "SalesInvoice", "SalesInvoiceID", "", "Order-to-Cash"),
    ("SalesInvoiceLine", "ShipmentLineID", "ShipmentLine", "ShipmentLineID", "design services", "Order-to-Cash"),
    ("CashReceiptApplication", "SalesInvoiceID", "SalesInvoice", "SalesInvoiceID", "", "Order-to-Cash"),
    ("CashReceipt", "SalesInvoiceID", "SalesInvoice", "SalesInvoiceID", "the link is in the application table", "Order-to-Cash"),
    ("GLEntry", "AccountID", "Account", "AccountID", "", "cross-group, into the Accounting Core"),
    ("GLEntry", "CostCenterID", "CostCenter", "CostCenterID", "balance sheet and other rows with no cost center", "cross-group, into Organizational Planning"),
    ("Account", "ParentAccountID", "Account", "AccountID", "top-level accounts", "Accounting Core, self-reference"),
]


@context("ch03.ex6")
def ex6(d, claim):
    have = schema(d, claim, {c: [fk] for c, fk, *_ in EX6_TESTS} | {p: [pk] for _, _, p, pk, *_ in EX6_TESTS} | {"GLEntry": ["AccountID", "CostCenterID", "SourceDocumentType", "SourceDocumentID"]})
    tests = []
    for c, fk, p, pk, why, group in EX6_TESTS:
        k = card(d, c, fk, p, pk)
        k.update(reason=why, group=group, child_col=letter(have, c, fk), parent_col=letter(have, p, pk))
        k["formula"] = (f'=IF(RC="","blank",IF(COUNTIFS({p}!{k["parent_col"]}:{k["parent_col"]},RC)=0,"orphan","ok"))'
                        .replace("RC", f"{k['child_col']}2"))
        k["free_col"] = col_letter(len(have[c]) + 1)
        k["count_formula"] = f'=COUNTIF({k["free_col"]}:{k["free_col"]},"orphan")'
        claim(k["orphans"] == 0, f"every non-blank {c}.{fk} exists in {p}")
        claim((k["blank"] > 0) == bool(why), f"{c}.{fk} is blank on {'some rows, for the reason the guide gives' if why else 'no row'}")
        tests.append(k)
    by = {(t["child"], t["fk"]): t for t in tests}
    pivot = {f"{c}.{fk}": by[(c, fk)]["distinct"] for c, fk in (("SalesOrder", "CustomerID"), ("SalesOrderLine", "ItemID"), ("GLEntry", "AccountID"), ("GLEntry", "CostCenterID"))}
    claim(by[("GLEntry", "AccountID")]["distinct"] < by[("GLEntry", "AccountID")]["parents"], "the ledger uses fewer accounts than the chart holds, so the distinct list is shorter than the Account table")
    claim(all(pivot[k] < 300 for k in pivot), "the foreign keys the guide sends through a PivotTable have a few hundred distinct values at most")
    claim(by[("SalesInvoiceLine", "ShipmentLineID")]["distinct"] > 0.9 * by[("SalesInvoiceLine", "ShipmentLineID")]["rows"] - by[("SalesInvoiceLine", "ShipmentLineID")]["blank"],
          "the invoice lines' shipment line keys are nearly all distinct, so a PivotTable would not shorten the test")
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountID IN (SELECT AccountNumber FROM Account)") < d.one("SELECT COUNT(*) FROM Account"),
          "AccountID and AccountNumber are different numbers, so testing one against the other would flag orphans")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (SELECT AccountID FROM Account WHERE AccountSubType = 'Header')") == 0, "the header accounts have no ledger rows")
    wrong = d.one("SELECT COUNT(*) FROM (SELECT DISTINCT AccountID FROM GLEntry) WHERE AccountID NOT IN (SELECT AccountNumber FROM Account)")
    claim(wrong > 0, "testing GLEntry.AccountID against Account.AccountNumber flags every account of the ledger")
    # the trace, as an extension
    trace = []
    for (src,) in d.q("SELECT SourceDocumentType FROM GLEntry GROUP BY 1 ORDER BY COUNT(*) DESC"):
        if d.one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?", src):
            pk = d.q(f"PRAGMA table_info({src})")[0][1]
            n = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = ?", src)
            o = d.one(f"SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = ? AND SourceDocumentID NOT IN (SELECT {pk} FROM {src})", src)
            trace.append(dict(source=src, rows=n, orphans=o))
    bad = [r for r in trace if r["orphans"]]
    claim([r["source"] for r in bad] == ["PayrollPayment"], "the only ledger rows whose source document is missing are typed PayrollPayment")
    claim(d.one("SELECT COUNT(DISTINCT SourceDocumentID) FROM GLEntry WHERE SourceDocumentType = 'PayrollPayment' AND SourceDocumentID NOT IN (SELECT PayrollPaymentID FROM PayrollPayment)") * 2 == bad[0]["orphans"],
          "the missing payment documents come in pairs of ledger rows, a debit and a credit for each")
    claim(d.one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'PayrollSummary'") == 0, "PayrollSummary is a source type but not a table")
    lowest = d.q("SELECT MIN(SourceDocumentID), MAX(SourceDocumentID) FROM GLEntry WHERE SourceDocumentType = 'PayrollSummary'")[0]
    return dict(tests=tests, n_tests=len(tests), n_orphans=sum(t["orphans"] for t in tests), n_blank=sum(1 for t in tests if t["blank"]),
                n_cross=sum(1 for t in tests if t["group"].startswith("cross")), pivot=pivot, trace=trace, bad=bad[0], n_trace=len(trace),
                gl_rows=by[("GLEntry", "AccountID")]["rows"], used=by[("GLEntry", "AccountID")]["distinct"], accounts=by[("GLEntry", "AccountID")]["parents"],
                wrong=wrong, summary_low=lowest[0], summary_high=lowest[1])
