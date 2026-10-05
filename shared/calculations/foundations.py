"""Public examples shared by Chapters 2–3 book figures and teaching decks.

Callers supply a read-only connection. These helpers never write data or import
assessment solutions. Selection IDs identify examples already shown in the book.
"""
from __future__ import annotations

import re
import sqlite3


def quality_examples(db: sqlite3.Connection) -> dict:
    def shipments(numbers, columns):
        rows = db.execute(f"SELECT {columns} FROM Shipment WHERE ShipmentNumber IN "
                          f"({','.join('?' for _ in numbers)}) ORDER BY ShipmentNumber", numbers).fetchall()
        if len(rows) != len(numbers): raise ValueError('Public shipment example changed')
        return rows
    return {
        'missing': shipments(['SH-2024-000028','SH-2024-000029','SH-2024-000049'],
                             'ShipmentNumber, ShipmentDate, FreightCost, TrackingNumber'),
        'duplicates': db.execute("SELECT SupplierID, InvoiceNumber, InvoiceDate, GrandTotal "
            "FROM PurchaseInvoice WHERE SupplierID = 2 AND InvoiceNumber IN "
            "('V0002-2024-000182', 'V0002-2024-000204') ORDER BY InvoiceDate").fetchall(),
        'status': shipments(['SH-2024-000001','SH-2024-000004','SH-2024-000038'],
                            'ShipmentNumber, ShipmentDate, Status, DeliveryDate'),
        'outliers': shipments(['SH-2024-000001','SH-2024-000002','SH-2024-000003','SH-2026-008319'],
                              'ShipmentNumber, WarehouseID, FreightCost'),
        'freight_summary': db.execute('SELECT AVG(FreightCost), MAX(FreightCost) FROM Shipment').fetchone(),
    }


def budget_example(db: sqlite3.Connection) -> list[tuple]:
    rows = db.execute("SELECT cc.CostCenterName, b.Month, b.BudgetAmount FROM Budget b "
        "JOIN CostCenter cc USING (CostCenterID) JOIN Account a USING (AccountID) "
        "WHERE b.FiscalYear = 2025 AND b.Month <= 3 AND a.AccountNumber IN (6010, 6030, 6240) "
        "ORDER BY cc.CostCenterID, b.Month").fetchall()
    if len(rows) != 9: raise ValueError('Public budget example changed')
    return rows


def key_example(db: sqlite3.Connection) -> dict:
    return {'orders': db.execute("SELECT SalesOrderID, OrderNumber, CustomerID FROM SalesOrder "
        "WHERE SalesOrderID IN (59, 62, 85) ORDER BY CustomerID, SalesOrderID").fetchall(),
        'customers': db.execute("SELECT CustomerID, CustomerName FROM Customer "
        "WHERE CustomerID IN (1, 4) ORDER BY CustomerID").fetchall()}


def relationship(db: sqlite3.Connection, parent: str, pk: str, child: str, fk: str) -> tuple[str, str]:
    """The same observed-cardinality markers used by the book ER diagrams."""
    for name in (parent, pk, child, fk):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name): raise ValueError('Invalid schema identifier')
    nulls = db.execute(f'SELECT COUNT(*) FROM {child} WHERE {fk} IS NULL').fetchone()[0]
    minimum, maximum = db.execute(
        f'SELECT MIN(COALESCE(x.c, 0)), MAX(COALESCE(x.c, 0)) FROM {parent} p LEFT JOIN '
        f'(SELECT {fk} AS k, COUNT(*) AS c FROM {child} WHERE {fk} IS NOT NULL GROUP BY {fk}) x '
        f'ON x.k = p.{pk}').fetchone()
    if minimum is None: raise ValueError('Cannot infer cardinality from empty parent table')
    child_end = ('ERzeroToOne' if maximum <= 1 else 'ERzeroToMany') if minimum == 0 else (
        'ERmandOne' if maximum == 1 else 'ERoneToMany')
    return ('ERzeroToOne' if nulls else 'ERmandOne'), child_end


def sale_trace(db: sqlite3.Connection) -> dict:
    """The complete sale already taught in public Tutorial 3.2 and Figure 3.10."""
    def one(sql, *values):
        rows = db.execute(sql, values).fetchall()
        if len(rows) != 1: raise ValueError('Public sale trace no longer resolves uniquely')
        return rows[0]
    sid = 7947
    inv = one('SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate, SalesOrderID, CustomerID, '
              'GrandTotal FROM SalesInvoice WHERE SalesInvoiceID = ?', sid)
    sil = one('SELECT SalesInvoiceLineID, SalesOrderLineID, ShipmentLineID, ItemID, Quantity, '
              'UnitPrice, LineTotal FROM SalesInvoiceLine WHERE SalesInvoiceID = ?', sid)
    shl = one('SELECT ShipmentLineID, ShipmentID, QuantityShipped FROM ShipmentLine '
              'WHERE ShipmentLineID = ?', sil[2])
    shp = one('SELECT ShipmentNumber, ShipmentDate FROM Shipment WHERE ShipmentID = ?', shl[1])
    sol = one('SELECT SalesOrderLineID, SalesOrderID FROM SalesOrderLine WHERE SalesOrderLineID = ?', sil[1])
    so = one('SELECT OrderNumber, OrderDate FROM SalesOrder WHERE SalesOrderID = ?', sol[1])
    cus = one('SELECT CustomerID, CustomerName FROM Customer WHERE CustomerID = ?', inv[4])
    itm = one('SELECT ItemCode, ItemName, StandardCost FROM Item WHERE ItemID = ?', sil[3])
    glr = db.execute("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit, g.SourceLineID, "
        "a.AccountType, g.AccountID FROM GLEntry g JOIN Account a USING (AccountID) "
        "WHERE SourceDocumentType = 'SalesInvoice' AND SourceDocumentID = ? ORDER BY GLEntryID", (sid,)).fetchall()
    gls = db.execute("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit FROM GLEntry g "
        "JOIN Account a USING (AccountID) WHERE SourceDocumentType = 'Shipment' "
        "AND SourceDocumentID = ? AND SourceLineID = ? ORDER BY GLEntryID", (shl[1], shl[0])).fetchall()
    app = one('SELECT CashReceiptApplicationID, CashReceiptID, AppliedAmount, ApplicationDate '
              'FROM CashReceiptApplication WHERE SalesInvoiceID = ?', sid)
    rct = one('SELECT ReceiptNumber, Amount FROM CashReceipt WHERE CashReceiptID = ?', app[1])
    if abs(sum(r[2] for r in glr)-inv[5]) > .005 or abs(sum(r[3] for r in glr)-inv[5]) > .005:
        raise ValueError('Public invoice trace does not balance to its total')
    return dict(inv=inv, sil=sil, shl=shl, shp=shp, sol=sol, so=so, cus=cus,
                itm=itm, glr=glr, gls=gls, app=app, rct=rct)
