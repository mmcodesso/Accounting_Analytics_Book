"""Public Chapter 13 tutorial calculations, shared by book figures and slides.

The caller supplies a read-only SQLite connection. No files are opened or modified.
"""
from __future__ import annotations
import sqlite3
import datetime as dt
from collections import Counter, defaultdict
from shared.calculations.excel_analysis import _access

MONTHS_2026 = [f"2026-{m:02d}" for m in range(1, 13)]

def lines(db: sqlite3.Connection) -> list[dict]:
    """The invoice lines with what the tutorials' model relates to them."""
    q, one, require_columns = _access(db)
    require_columns("SalesInvoiceLine", ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity",
                                         "BaseListPrice", "UnitPrice", "Discount", "LineTotal",
                                         "PromotionID", "PricingMethod"])
    require_columns("SalesInvoice", ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID"])
    require_columns("Item", ["ItemID", "ItemCode", "ItemGroup", "ListPrice", "StandardCost"])
    require_columns("Customer", ["CustomerID", "CustomerName", "CustomerSegment", "Region"])
    rows = q("SELECT l.SalesInvoiceLineID, l.SalesInvoiceID, si.InvoiceDate, i.ItemGroup, "
             "substr(i.ItemCode, 5, 3), c.CustomerSegment, c.Region, l.LineTotal, "
             "l.Quantity * l.BaseListPrice, l.Quantity * l.UnitPrice * l.Discount, i.ListPrice "
             "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
             "JOIN Item i USING (ItemID) JOIN Customer c ON c.CustomerID = si.CustomerID")
    total = one("SELECT COUNT(*) FROM SalesInvoiceLine")[0]
    assert len(rows) == total, "every line finds its invoice, item, and customer"
    assert all(r[10] is not None for r in rows), "no line refers to an item without a list price"
    out = []
    for r in rows:
        date = r[2]
        out.append(dict(id=r[0], inv=r[1], fy=int(date[:4]), month=date[:7],
                        period=f"{date[:4]}-Q{(int(date[5:7]) + 2) // 3}", grp=r[3], pt=r[4],
                        seg=r[5], reg=r[6], rev=r[7], list=r[8], disc=r[9]))
    return out

def total(db: sqlite3.Connection, field: str, **match) -> float:
    q, one, require_columns = _access(db)
    return sum(r[field] for r in lines(db) if all(r[k] == v for k, v in match.items()))

def count(db: sqlite3.Connection, **match) -> int:
    q, one, require_columns = _access(db)
    return sum(1 for r in lines(db) if all(r[k] == v for k, v in match.items()))

def monthly(db: sqlite3.Connection, field: str, year: int = 2026, **match) -> list[float]:
    q, one, require_columns = _access(db)
    by = defaultdict(float)
    for r in lines(db):
        if r["fy"] == year and all(r[k] == v for k, v in match.items()):
            by[r["month"]] += r[field]
    return [by[m] for m in MONTHS_2026]

def _profile(db: sqlite3.Connection, sample: int | None) -> dict:
    """Column quality and distribution of SalesInvoiceLine on the first rows or all of them."""
    q, one, require_columns = _access(db)
    src = ("(SELECT * FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT {})".format(sample)
           if sample else "SalesInvoiceLine")
    n, promo_empty, d_distinct, lt_distinct = one(
        f"SELECT COUNT(*), SUM(PromotionID IS NULL), COUNT(DISTINCT Discount), COUNT(DISTINCT LineTotal) FROM {src}")
    d_unique = one(f"SELECT COUNT(*) FROM (SELECT Discount FROM {src} GROUP BY Discount HAVING COUNT(*) = 1)")[0]
    first = q(f"SELECT Discount, PromotionID, LineTotal FROM {src} ORDER BY SalesInvoiceLineID LIMIT 4")
    return dict(n=n, promo_empty=promo_empty, d_distinct=d_distinct, d_unique=d_unique, first=first)
