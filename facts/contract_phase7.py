"""Proposed contract checks for the text that a yearly roll rewrites (Phase 7).

facts/contract.py tests the storylines; the text also names single documents and dates (the traced sale of
Chapters 1 and 3, the cutoff error of Exercise 6.1, the two days of Figure 12.9), and a roll rewrites those names
by selection rules (facts/visible.py). A rule that finds nothing, or finds a document with fewer of the properties
the text tells, means the generator must plant the document again or the wording must change. These checks state
that, one per rule; they would join facts/contract.py as checks with the ids below.

    python facts/contract_phase7.py [--db PATH] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))
from db import Data  # noqa: E402
import visible  # noqa: E402

CHECKS = []


def check(cid: str, chapters: str, text: str):
    def register(fn):
        CHECKS.append((cid, chapters, text, fn))
        return fn
    return register


def found(name: str, d: Data):
    """(ok, detail) of one selection rule of facts/visible.py."""
    fn = dict(visible.RULES)[name]
    try:
        out = fn(d)
    except visible.NotFound as exc:
        return False, str(exc)
    return True, f"{len(out)} keys"


@check("T1", "1, 3, 5", "the traced sale exists exactly as the text tells it: a one-line Furniture desk invoice of P for two "
                       "desks, freight and tax, shipped in parts of a larger order, paid by one check that paid several invoices")
def t1(d):
    try:
        out = visible.trace(d)
    except visible.NotFound as exc:
        return False, str(exc)
    return bool(out["id.trace.exact"]), (f"{out['id.trace.invoice']}, {out['id.trace.quantity']:g} units of "
                                        f"{out['id.trace.item_code']}, tier {out['id.trace.tier']}")


@check("T2", "6, 12, 14, 16", "the revenue cutoff story has its shape: invoices numbered in C but dated in P are consecutive, "
                              "are posted on one date, and exactly one of them shipped in P (a cutoff error); the rest shipped in C")
def t2(d):
    ok, detail = found("cutoff_shipment", d)
    if not ok:
        return ok, detail
    invoices = d.q("SELECT DISTINCT si.SalesInvoiceID, si.InvoiceNumber, g.PostingDate FROM SalesInvoice si JOIN GLEntry g "
                   "ON g.SourceDocumentType = 'SalesInvoice' AND g.SourceDocumentID = si.SalesInvoiceID "
                   "WHERE g.FiscalYear = ? AND si.InvoiceDate < ? ORDER BY si.InvoiceNumber", d.C, f"{d.C}-01-01")
    numbers = [int(number.rsplit("-", 1)[1]) for _, number, _ in invoices]
    problems = []
    if len(invoices) < 2:
        problems.append(f"{len(invoices)} invoice(s) dated in {d.P} and posted in {d.C}; the book tells of three")
    if numbers and numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        problems.append(f"the invoice numbers are not consecutive: {numbers}")
    if len({posted for _, _, posted in invoices}) > 1:
        problems.append("they were not posted on one date")
    early = 0
    for sid, number, _ in invoices:
        years = {s[:4] for (s,) in d.q("SELECT s.ShipmentDate FROM SalesInvoiceLine l JOIN ShipmentLine sl ON sl.ShipmentLineID = "
                                         "l.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE l.SalesInvoiceID = ?", sid)}
        early += str(d.P) in years
        if not years <= {str(d.P), str(d.C)}:
            problems.append(f"{number} shipped in a year other than {d.P} and {d.C}")
    if early != 1:
        problems.append(f"{early} of them shipped in {d.P}, not exactly one")
    return not problems, "; ".join(problems) or f"{len(invoices)} consecutive invoices ({numbers[0]}-{numbers[-1]}), one posting date, one shipped in {d.P}"


@check("T3", "2, 5, 9, 10, 11, 12, 16", "the year-end closes, the opening entry, the open pay periods, the Furniture promotion, "
                                        "the invoice dated before its shipment, the oldest open work order, the fan-out invoice, "
                                        "the Chapter 2 shipments and the duplicated supplier invoice can all be selected")
def t3(d):
    bad = []
    for name in ("closes", "opening_entry", "po_after_termination", "open_pay_periods", "furniture_promotion",
                 "invoice_before_shipment", "oldest_open_work_order", "fan_out_invoice", "shipment_examples",
                 "duplicate_supplier_invoice", "data_dates"):
        ok, why = found(name, d)
        if not ok:
            bad.append(f"{name}: {why}")
    return not bad, "; ".join(bad) or "all selected"


@check("T4", "12", "Figure 12.9's two days exist: a normal day (second Tuesday of March of F) before the first surge day, and "
                   "a surge day on or after 10 June of C, with the six sampled Assemblers clocked in on both")
def t4(d):
    return found("ch12_days", d)


@check("T5", "9, 10", "all open work orders were released in C (Chapter 9: the year taken from a work order number is C for every open order)")
def t5(d):
    n = d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate IS NULL AND ReleasedDate NOT BETWEEN ? AND ?",
              f"{d.C}-01-01", f"{d.C}-12-31")
    return n == 0, f"{n} open work orders released outside {d.C}"


@check("T6", "all", "no key of the registry that reads like a year (a document ID such as 2024) falls in the year range of the window")
def t6(d):
    keys = visible.snapshot(d)
    lo, hi = d.F - 1, d.N + 2
    odd = sorted(k for k, v in keys.items() if not k.startswith("fy.") and isinstance(v, int) and not isinstance(v, bool)
                 and lo <= v <= hi)
    return not odd, ", ".join(f"{k}={keys[k]}" for k in odd) or "none"


def main(argv=None) -> int:
    from paths import DB
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    d = Data(a.db)
    results = []
    for cid, chapters, text, fn in CHECKS:
        try:
            ok, detail = fn(d)
        except Exception as exc:  # a check that cannot run is a failure
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        results.append(dict(id=cid, chapters=chapters, text=text, ok=bool(ok), detail=detail))
        print(f"{'ok  ' if ok else 'FAIL'} {cid:3} {text[:92]}\n         {detail}")
    print(f"{sum(r['ok'] for r in results)} of {len(results)} pass, fiscal {d.F}-{d.C}")
    if a.json:
        a.json.write_text(json.dumps(dict(window=[d.F, d.C], checks=results), indent=1), encoding="utf-8")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
