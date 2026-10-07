"""Public invoice-line measures shared by the book figures.

Callers supply an already-open, read-only SQLite connection. These helpers issue
SELECT statements only; they never generate data or import instructor tooling.
Invoice margin is based on invoice LineTotal and Item.StandardCost, not ledger
gross profit or historical actual cost. Retain unrounded values until display.
"""

from __future__ import annotations

import sqlite3


def period(date_text: str) -> str:
    return f"{date_text[:4]}-Q{(int(date_text[5:7]) + 2) // 3}"


def invoice_lines(connection: sqlite3.Connection) -> list[dict]:
    """Tutorial 5.3's joined rows with Chapter 6's unrounded measures."""
    rows = connection.execute(
        "SELECT l.SalesInvoiceLineID, l.Quantity, l.BaseListPrice, l.UnitPrice, l.Discount, "
        "l.LineTotal, l.PromotionID, si.InvoiceDate, i.ItemGroup, i.StandardCost, c.CustomerSegment "
        "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
        "JOIN Item i USING (ItemID) JOIN Customer c ON c.CustomerID = si.CustomerID"
    ).fetchall()
    return [dict(id=r[0], U=r[1], L=r[1] * r[2], R=r[5], D=r[1] * r[3] * r[4], C=r[1] * r[9],
                 promo=r[6], per=period(r[7]), fy=int(r[7][:4]), grp=r[8], seg=r[10]) for r in rows]
