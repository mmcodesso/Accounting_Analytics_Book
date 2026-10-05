"""The registry of the literals a yearly roll rewrites in the text: years, document IDs, dates, and values.

Phase 7 of the companion-files and yearly-roll program keeps readable literals in the source (fiscal 2026,
SI-2025-007947, 2026-12-11, $29,756,420.08). At each roll, scripts/roll_text.py rewrites each classified
literal from its value in the old edition's snapshot to its value in the new one. This module computes a
snapshot from a dataset:

    snapshot(d) -> {key: value}       d is a facts/db.Data window (F, P, C, N)

- fy.*    the role years: fy.F, fy.P, fy.C, fy.N, the years next to the window (fy.Fm1, fy.N1, fy.N2), and
          fy.edition (the edition's year, which is C);
- id.*    document IDs and codes, each found by a selection rule that picks the document with the same role in
          any build (the close of year C that posts to 5080, the traced sale of Chapters 1 and 3, ...);
- date.*  specific dates (the last day of the time records, the date the traced invoice was posted, ...),
          as ISO text;
- val.*   the exact values, from facts/visible_values.py (values(d)).

A rule that finds nothing on a dataset leaves its keys out and records why (missing(d)); roll_text.py then
refuses to rewrite those literals and lists them for the impact review. Each rule's docstring states the
properties of the document that the text relies on; contract checks that would keep them planted in the
generator are proposed in the Phase 7 report.

    python scripts/facts.py visible [--db PATH] --out facts/visible-2026.json
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from db import Data  # noqa: E402

RULES: list[tuple[str, Callable]] = []


class NotFound(LookupError):
    """A selection rule found no document with the properties the text relies on."""


def rule(fn: Callable) -> Callable:
    RULES.append((fn.__name__, fn))
    return fn


def first(d: Data, sql: str, *args, what: str = "a document"):
    rows = d.q(sql, *args)
    if not rows:
        raise NotFound(f"no {what}")
    return rows[0]


# --- years ---------------------------------------------------------------------------------------

@rule
def years(d: Data) -> dict:
    """The window: F, P, C (the last year with sales invoices posted), N = C + 1, and the years next to it."""
    return {"fy.Fm1": d.F - 1, "fy.F": d.F, "fy.P": d.P, "fy.C": d.C, "fy.N": d.N, "fy.N1": d.N + 1,
            "fy.N2": d.N + 2, "fy.edition": d.C}


# --- document IDs ----------------------------------------------------------------------------------

@rule
def trace(d: Data) -> dict:
    """The sale traced in Chapter 1 (Figure 1.6), Tutorial 3.2 and Figure 3.10 (SI-2025-007947 in the 2026 edition).

    The text relies on: an invoice of fiscal P "for two desks": one line, a Furniture desk (FUR-DSK-...), exactly
    2 units, with freight and sales tax (so the invoice posts four GL rows: receivables, revenue, freight, tax);
    the order line covers a larger quantity ("shipped and invoiced in several parts"), and one shipment line of
    the same 2 units, shipped a few days before the invoice date; a wholesale customer; paid in full by one
    application of a check that paid several invoices (a junction table). The earliest such invoice is chosen."""
    P = d.P
    row = first(d, f"""
        SELECT s.SalesInvoiceID, s.InvoiceNumber, s.InvoiceDate, s.SalesOrderID, s.CustomerID,
               l.SalesInvoiceLineID, l.SalesOrderLineID, l.ShipmentLineID, l.ItemID, i.ItemCode,
               sl.ShipmentID, sh.ShipmentNumber, sh.ShipmentDate, o.OrderNumber, o.OrderDate,
               a.CashReceiptApplicationID, a.CashReceiptID, a.ApplicationDate, cr.ReceiptNumber
        FROM SalesInvoice s
        JOIN SalesInvoiceLine l ON l.SalesInvoiceID = s.SalesInvoiceID
        JOIN Item i ON i.ItemID = l.ItemID
        JOIN SalesOrderLine ol ON ol.SalesOrderLineID = l.SalesOrderLineID
        JOIN SalesOrder o ON o.SalesOrderID = s.SalesOrderID
        JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID
        JOIN Shipment sh ON sh.ShipmentID = sl.ShipmentID
        JOIN Customer c ON c.CustomerID = s.CustomerID
        JOIN CashReceiptApplication a ON a.SalesInvoiceID = s.SalesInvoiceID
        JOIN CashReceipt cr ON cr.CashReceiptID = a.CashReceiptID
        WHERE s.InvoiceDate BETWEEN '{P}-01-01' AND '{P}-12-31'
          AND s.FreightAmount > 0 AND s.TaxAmount > 0
          AND (SELECT COUNT(*) FROM SalesInvoiceLine x WHERE x.SalesInvoiceID = s.SalesInvoiceID) = 1
          AND i.ItemCode LIKE 'FUR-DSK-%' AND l.Quantity = 2 AND sl.QuantityShipped = 2
          AND ol.Quantity > l.Quantity AND sh.ShipmentDate < s.InvoiceDate
          AND c.CustomerSegment = 'Wholesale'
          AND (SELECT COUNT(*) FROM GLEntry g WHERE g.SourceDocumentType = 'SalesInvoice'
               AND g.SourceDocumentID = s.SalesInvoiceID) = 4
          AND (SELECT COUNT(*) FROM CashReceiptApplication x WHERE x.SalesInvoiceID = s.SalesInvoiceID) = 1
          AND ABS(a.AppliedAmount - s.GrandTotal) < 0.005
          AND cr.PaymentMethod = 'Check'
          AND (SELECT COUNT(*) FROM CashReceiptApplication x WHERE x.CashReceiptID = cr.CashReceiptID) >= 3
        ORDER BY s.InvoiceDate, s.SalesInvoiceID""", what="invoice of fiscal P with the traced sale's properties")
    (sid, number, idate, so_id, cust, line, so_line, sh_line, item, code, sh_id, sh_no, sh_date, so_no, so_date,
     app, rec, app_date, rec_no) = row
    gl = first(d, "SELECT GLEntryID, PostingDate FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' "
                  "AND SourceDocumentID = ? AND SourceLineID = ?", sid, line, what="revenue posting of the trace")
    return {"id.trace.invoice": number, "id.trace.order": so_no, "id.trace.shipment": sh_no,
            "id.trace.receipt": rec_no, "id.trace.item_code": code,
            "id.trace.invoice_id": sid, "id.trace.order_id": so_id, "id.trace.customer_id": cust,
            "id.trace.line_id": line, "id.trace.order_line_id": so_line, "id.trace.shipment_line_id": sh_line,
            "id.trace.shipment_id": sh_id, "id.trace.item_id": item, "id.trace.application_id": app,
            "id.trace.receipt_id": rec, "id.trace.gl_revenue_id": gl[0],
            "date.trace.invoice": idate, "date.trace.posting": gl[1], "date.trace.shipment": sh_date,
            "date.trace.order": so_date, "date.trace.application": app_date[:10]}


@rule
def closes(d: Data) -> dict:
    """The year-end closes of F, P and C: the entry that closes revenue and expense to income summary (the
    only journal entry to 5080 and 5060 in its year) and the entry that closes income summary to retained
    earnings (equal to the year's net income)."""
    out = {}
    for role, year in (("F", d.F), ("P", d.P), ("C", d.C)):
        for kind, like in (("pl", "Year-End Close - P&L%"), ("re", "Year-End Close - Income Summary%")):
            row = first(d, "SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE ? AND PostingDate = ? "
                           "ORDER BY EntryNumber", like, f"{year}-12-31", what=f"{kind} close of {year}")
            out[f"id.close.{kind}.{role}"] = row[0]
    return out


@rule
def opening_entry(d: Data) -> dict:
    """JE-2024-000001 in the 2026 edition: the opening-balance journal entry of F (EntryType Opening), the
    only entry the CFO created, and the one entry with risk score 4 in Chapter 8."""
    row = first(d, "SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' AND PostingDate = ? "
                   "ORDER BY EntryNumber", f"{d.F}-01-01", what="opening entry on the first day of F")
    return {"id.je.opening": row[0]}


@rule
def po_after_termination(d: Data) -> dict:
    """The purchase orders approved by an employee after the approver's termination (employee 81 in the 2026
    edition): the first of each fiscal year F, P and C (Tutorial 16.3's Deficiency dispositions)."""
    out = {}
    for role, year in (("F", d.F), ("P", d.P), ("C", d.C)):
        row = first(d, "SELECT po.PONumber FROM PurchaseOrder po JOIN Employee e ON e.EmployeeID = po.ApprovedByEmployeeID "
                       "WHERE e.TerminationDate IS NOT NULL AND po.OrderDate > e.TerminationDate "
                       "AND po.OrderDate BETWEEN ? AND ? ORDER BY po.PONumber",
                    f"{year}-01-01", f"{year}-12-31", what=f"PO of {year} approved after termination")
        out[f"id.po_after_termination.{role}"] = row[0]
    return out


@rule
def open_pay_periods(d: Data) -> dict:
    """The pay periods still Open at the end of the data (PP-2026-078 and 079 in the 2026 edition): the last two
    pay periods of C, which carry no registers, so the time records end before the year does."""
    rows = d.q("SELECT PeriodNumber FROM PayrollPeriod WHERE Status = 'Open' ORDER BY PeriodStartDate")
    if len(rows) < 2:
        raise NotFound("fewer than two Open pay periods")
    return {"id.pay_period.open.1": rows[0][0], "id.pay_period.open.2": rows[1][0]}


@rule
def furniture_promotion(d: Data) -> dict:
    """PROMO-2026-008 in the 2026 edition: the Furniture item-group promotion of C (September and October),
    whose discounts make Furniture's Q3 to Q4 margin fall."""
    row = first(d, "SELECT PromotionCode, EffectiveStartDate, EffectiveEndDate FROM PromotionProgram "
                   "WHERE ItemGroup = 'Furniture' AND EffectiveStartDate BETWEEN ? AND ? ORDER BY PromotionID",
                f"{d.C}-01-01", f"{d.C}-12-31", what="Furniture promotion of C")
    return {"id.promo.furniture": row[0], "date.promo.furniture.start": row[1], "date.promo.furniture.end": row[2]}


@rule
def invoice_before_shipment(d: Data) -> dict:
    """SI-2024-000001 in the 2026 edition: the first invoice of F (by number) dated before its order's first
    shipment (Tutorial 2.1's MINIFS check), with its date and the date the order first shipped."""
    row = first(d, """
        SELECT s.InvoiceNumber, s.InvoiceDate,
               (SELECT MIN(sh.ShipmentDate) FROM Shipment sh WHERE sh.SalesOrderID = s.SalesOrderID) AS FirstShip
        FROM SalesInvoice s
        WHERE s.InvoiceNumber LIKE ? AND s.InvoiceDate <
              (SELECT MIN(sh.ShipmentDate) FROM Shipment sh WHERE sh.SalesOrderID = s.SalesOrderID)
        ORDER BY s.InvoiceNumber""", f"SI-{d.F}-%", what="invoice of F dated before its order's first shipment")
    return {"id.invoice_before_shipment": row[0], "date.invoice_before_shipment": row[1],
            "date.invoice_before_shipment.first_ship": row[2]}


@rule
def oldest_open_work_order(d: Data) -> dict:
    """WO-2026-011512 in the 2026 edition: the open work order (no ClosedDate) released first. Chapter 9 relies on
    every open work order being a work order of C."""
    row = first(d, "SELECT WorkOrderNumber, ReleasedDate, DueDate FROM WorkOrder WHERE ClosedDate IS NULL "
                   "ORDER BY ReleasedDate, WorkOrderNumber", what="open work order")
    return {"id.wo.oldest_open": row[0], "date.wo.oldest_open.released": row[1], "date.wo.oldest_open.due": row[2]}


@rule
def fan_out_invoice(d: Data) -> dict:
    """SI-2026-019134 in the 2026 edition: the first invoice of C's fourth quarter with exactly three lines
    (Figure 10.4, fan-out)."""
    row = first(d, "SELECT s.InvoiceNumber FROM SalesInvoice s JOIN SalesInvoiceLine l ON l.SalesInvoiceID = s.SalesInvoiceID "
                   "WHERE s.InvoiceDate BETWEEN ? AND ? GROUP BY s.SalesInvoiceID HAVING COUNT(*) = 3 "
                   "ORDER BY s.InvoiceDate, s.SalesInvoiceID", f"{d.C}-10-01", f"{d.C}-12-31",
                what="three-line invoice in C's fourth quarter")
    return {"id.invoice.fan_out": row[0]}


@rule
def shipment_examples(d: Data) -> dict:
    """The shipments of Figure 2's data-quality panels (shared/calculations/foundations.py):
    - missing: the shipment just before the first one with a blank TrackingNumber, and the first two blanks;
    - status: the first shipment, and the first two still In Transit (their DeliveryDate long past);
    - outliers: the first three shipments, and the one with the largest FreightCost."""
    first_nums = [r[0] for r in d.q("SELECT ShipmentNumber FROM Shipment ORDER BY ShipmentNumber LIMIT 3")]
    blanks = d.q("SELECT ShipmentID, ShipmentNumber FROM Shipment WHERE TrackingNumber IS NULL ORDER BY ShipmentNumber LIMIT 2")
    transit = [r[0] for r in d.q("SELECT ShipmentNumber FROM Shipment WHERE Status = 'In Transit' "
                                  "ORDER BY ShipmentNumber LIMIT 2")]
    if len(first_nums) < 3 or len(blanks) < 2 or len(transit) < 2:
        raise NotFound("too few shipments for the Chapter 2 panels")
    before = first(d, "SELECT ShipmentNumber FROM Shipment WHERE ShipmentNumber < ? ORDER BY ShipmentNumber DESC",
                   blanks[0][1], what="shipment before the first blank tracking number")[0]
    top = first(d, "SELECT ShipmentNumber FROM Shipment ORDER BY FreightCost DESC, ShipmentNumber")[0]
    return {"id.ship.first.1": first_nums[0], "id.ship.first.2": first_nums[1], "id.ship.first.3": first_nums[2],
            "id.ship.blank_tracking.before": before, "id.ship.blank_tracking.1": blanks[0][1],
            "id.ship.blank_tracking.2": blanks[1][1], "id.ship.in_transit.1": transit[0],
            "id.ship.in_transit.2": transit[1], "id.ship.max_freight": top}


@rule
def duplicate_supplier_invoice(d: Data) -> dict:
    """V0002-2024-000182 in the 2026 edition: supplier 2's invoice number of F that is recorded twice (Figure 2's
    duplicate panel, Exercise 2.6), and the supplier's next invoice after the pair (V0002-2024-000204)."""
    num, last = first(d, "SELECT InvoiceNumber, MAX(InvoiceDate) FROM PurchaseInvoice WHERE SupplierID = 2 "
                         "AND InvoiceDate BETWEEN ? AND ? GROUP BY InvoiceNumber HAVING COUNT(*) > 1 ORDER BY MIN(InvoiceDate)",
                      f"{d.F}-01-01", f"{d.F}-12-31", what="duplicated invoice number of supplier 2 in F")
    nxt = first(d, "SELECT InvoiceNumber FROM PurchaseInvoice WHERE SupplierID = 2 AND InvoiceNumber <> ? "
                   "AND InvoiceDate > ? ORDER BY InvoiceDate, PurchaseInvoiceID", num, last,
                what="supplier 2's invoice after the duplicate pair")[0]
    return {"id.supplier_invoice.duplicate": num, "id.supplier_invoice.after_duplicate": nxt}


# --- dates ---------------------------------------------------------------------------------------

@rule
def data_dates(d: Data) -> dict:
    """Dates the text states about the data's extent:
    - date.time_records_end: the last WorkDate of the time records (2026-12-11), before year-end because the
      last two pay periods are Open; date.time_records_end.monday: the Monday of that week (the last Monday
      week of the Part III case);
    - date.payroll.last_pay: the last pay date with registers (Chapter 16's Data Through, 2026-12-18);
    - date.gl.end: the last posting date of the ledger (2027-02-23, supplier payments of N);
    - date.je.backdated_created: the day the first backdated journal entry was keyed (the first Saturday of F,
      shown as 2024-01-06 10:00:00)."""
    end = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    monday = (dt.date.fromisoformat(end) - dt.timedelta(days=dt.date.fromisoformat(end).weekday())).isoformat()
    pay = d.one("SELECT MAX(pp.PayDate) FROM PayrollRegister r JOIN PayrollPeriod pp ON pp.PayrollPeriodID = r.PayrollPeriodID")
    gl = d.one("SELECT MAX(PostingDate) FROM GLEntry")
    created = first(d, "SELECT CreatedDate FROM JournalEntry WHERE date(CreatedDate) > PostingDate "
                       "ORDER BY CreatedDate, EntryNumber", what="backdated journal entry")[0]
    return {"date.time_records_end": end, "date.time_records_end.monday": monday, "date.payroll.last_pay": pay,
            "date.gl.end": gl, "date.je.backdated_created": created[:10], "time.je.backdated_created": created[11:]}


@rule
def cutoff_shipment(d: Data) -> dict:
    """The revenue cutoff error of Exercise 6.1 and Chapter 12's multiple choice (SI-2026-013742 in the 2026
    edition): an invoice dated in P and posted in C whose goods shipped in P; its shipment date (2025-12-06)."""
    row = first(d, f"""
        SELECT s.InvoiceNumber, MIN(sh.ShipmentDate)
        FROM SalesInvoice s
        JOIN GLEntry g ON g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID = s.SalesInvoiceID
        JOIN SalesInvoiceLine l ON l.SalesInvoiceID = s.SalesInvoiceID
        JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID
        JOIN Shipment sh ON sh.ShipmentID = sl.ShipmentID
        WHERE s.InvoiceDate BETWEEN '{d.P}-01-01' AND '{d.P}-12-31' AND g.FiscalYear = {d.C}
        GROUP BY s.SalesInvoiceID HAVING MAX(sh.ShipmentDate) <= '{d.P}-12-31'
        ORDER BY s.InvoiceNumber""", what="invoice of P posted in C for goods shipped in P")
    return {"id.invoice.cutoff_error": row[0], "date.invoice.cutoff_error.shipped": row[1]}


# --- the snapshot --------------------------------------------------------------------------------

def compute(d: Data) -> tuple[dict, dict]:
    """(keys, missing): every key the rules find, and why a rule found nothing."""
    out: dict[str, object] = {}
    missing: dict[str, str] = {}
    for name, fn in RULES:
        try:
            out.update(fn(d))
        except NotFound as exc:
            missing[name] = str(exc)
    return out, missing


def values(d: Data) -> tuple[dict, str | None]:
    """val.* from agent B's facts/visible_values.py, or ({}, why) if it is not available."""
    try:
        import visible_values
    except ImportError as exc:
        return {}, f"facts/visible_values.py not importable ({exc})"
    try:
        return dict(visible_values.values(d)), None
    except Exception as exc:  # report and keep the snapshot of the other kinds
        return {}, f"visible_values.values failed: {type(exc).__name__}: {exc}"


def snapshot(d: Data) -> dict[str, object]:
    """Every key the rewriter can change, on the dataset of `d` (rules that find nothing are left out)."""
    keys, _ = compute(d)
    vals, _ = values(d)
    keys.update(vals)
    return keys


def snapshot_file(d: Data) -> dict:
    """The snapshot as `facts.py visible` writes it: the window, the dataset, the keys, and what is missing."""
    import hashlib
    keys, missing = compute(d)
    vals, why = values(d)
    if why:
        missing["values"] = why
    h = hashlib.sha256()
    with Path(d.path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return {"db": str(d.path), "sha256": h.hexdigest(), "window": [d.F, d.C],
            "keys": dict(sorted({**keys, **vals}.items())), "missing": missing}
