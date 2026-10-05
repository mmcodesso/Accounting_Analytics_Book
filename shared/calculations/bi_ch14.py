"""Public Chapter 14 tutorial calculations, shared by book figures and slides.

The caller supplies a read-only SQLite connection. No files are opened or modified.
"""
from __future__ import annotations
import sqlite3
import datetime as dt
from collections import Counter, defaultdict
from shared.calculations.excel_analysis import _access

CALENDAR = (dt.date(2024, 1, 1), dt.date(2027, 12, 31))

CLOSE = "j.EntryType LIKE 'Year-End Close%'"

def lines(db: sqlite3.Connection) -> list[dict]:
    """The fact table of the star: one row per invoice line with the merged header columns."""
    q, one, require_columns = _access(db)
    require_columns("SalesInvoiceLine", ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity",
                                         "LineTotal"])
    require_columns("SalesInvoice", ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID"])
    require_columns("Item", ["ItemID", "ItemGroup", "StandardCost", "ListPrice"])
    rows = q("SELECT l.SalesInvoiceLineID, si.InvoiceDate, si.CustomerID, i.ItemGroup, l.Quantity, "
             "l.LineTotal, l.Quantity * i.StandardCost FROM SalesInvoiceLine l "
             "JOIN SalesInvoice si USING (SalesInvoiceID) JOIN Item i USING (ItemID)")
    assert len(rows) == one("SELECT COUNT(*) FROM SalesInvoiceLine")[0], "every line finds its invoice"
    out = []
    for r in rows:
        d = r[1]
        out.append(dict(id=r[0], date=d, cust=r[2], grp=r[3], qty=r[4], rev=r[5], cost=r[6],
                        year=int(d[:4]), quarter=f"{d[:4]}-Q{(int(d[5:7]) + 2) // 3}"))
    return out

def total(db: sqlite3.Connection, field: str, **match) -> float:
    q, one, require_columns = _access(db)
    return sum(r[field] for r in lines(db) if all(r[k] == v for k, v in match.items()))

def margin_pct(db: sqlite3.Connection, **match) -> float:
    q, one, require_columns = _access(db)
    rev = total(db, "rev", **match)
    return (rev - total(db, "cost", **match)) / rev

def pnl(db: sqlite3.Connection) -> dict:
    """Credit less debit by fiscal year, account type and subtype, with and without the closes."""
    q, one, require_columns = _access(db)
    rows = q("SELECT g.FiscalYear, a.AccountType, a.AccountSubType, "
             f"CASE WHEN {CLOSE} THEN 1 ELSE 0 END, SUM(g.Credit - g.Debit) "
             "FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
             "LEFT JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
             "WHERE a.AccountType IN ('Revenue', 'Expense') GROUP BY 1, 2, 3, 4")
    out = defaultdict(float)
    for year, typ, sub, close, value in rows:
        out[(year, typ, sub, "all")] += value
        if not close:
            out[(year, typ, sub, "open")] += value
    return out

def pnl_total(db: sqlite3.Connection, year: int, kind: str, typ: str | None = None, sub: str | None = None) -> float:
    q, one, require_columns = _access(db)
    return sum(v for (y, t, s, k), v in pnl(db).items()
               if y == year and k == kind and typ in (None, t) and sub in (None, s))
