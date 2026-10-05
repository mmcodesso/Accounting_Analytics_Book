"""Public Chapter 16 tutorial calculations, shared by book figures and slides.

The caller supplies a read-only SQLite connection. No files are opened or modified.
"""
from __future__ import annotations
import sqlite3
import datetime as dt
from collections import Counter, defaultdict
from shared.calculations.excel_analysis import _access

JE_FLAGS = ["Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"]

TESTS = ["JE Weekend", "JE Backdated", "JE SelfApproved", "JE AboveLimit", "JE RoundAmount",
         "PO SelfApproved", "PO AboveLimit", "PO AfterTermination",
         "PR PaidBeforeApproval", "PR AfterTermination", "PR SelfApproved"]

PROCESS = {"JE": "Journal entries", "PO": "Purchase orders", "PR": "Payroll"}

DISPOSITIONS = (
    [("JE AboveLimit", n, "Expected", "Year-end close")
     for n in ["JE-2024-000265", "JE-2024-000266", "JE-2025-000287", "JE-2025-000288", "JE-2026-000296",
               "JE-2026-000297"]]
    + [("PO AfterTermination", n, "Deficiency", "Approver had left")
       for n in ["PO-2024-000474", "PO-2025-003922", "PO-2026-010467"]]
    + [("PR AfterTermination", n, "Deficiency", "Payee had left")
       for n in ["Register 840", "Register 2646", "Register 5420"]]
    + [("PR PaidBeforeApproval", n, "Follow up", "Paid before approval")
       for n in ["Register 2", "Register 2647", "Register 5421"]])

def journal_entries(db: sqlite3.Connection) -> list[dict]:
    """Every journal entry with Chapter 8's five flags and its risk score (Tutorial 16.1)."""
    q, one, require_columns = _access(db)
    require_columns("JournalEntry", ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount",
                                     "CreatedByEmployeeID", "CreatedDate", "ApprovedByEmployeeID"])
    out = []
    for jid, num, pd, et, amt, cb, cd, ab, lim in q(
            "SELECT j.JournalEntryID, j.EntryNumber, j.PostingDate, j.EntryType, j.TotalAmount, "
            "j.CreatedByEmployeeID, j.CreatedDate, j.ApprovedByEmployeeID, e.MaxApprovalAmount "
            "FROM JournalEntry j LEFT JOIN Employee e ON e.EmployeeID = j.ApprovedByEmployeeID "
            "ORDER BY j.EntryNumber"):
        created = dt.datetime.fromisoformat(cd)
        flags = dict(Weekend=int(created.weekday() >= 5), Backdated=int(created.date().isoformat() > pd),
                     SelfApproved=int(cb == ab), AboveLimit=int(amt > lim),
                     RoundAmount=int(round(amt % 1000, 6) == 0))
        out.append(dict(id=jid, number=num, posting=pd, type=et, amount=amt, approver=ab, limit=lim,
                        flags=flags, score=sum(flags.values())))
    assert len(out) == 851
    assert [sum(e["flags"][f] for e in out) for f in JE_FLAGS] == [17, 6, 7, 9, 4]
    assert sorted(Counter(e["score"] for e in out).items()) == [(0, 818), (1, 25), (2, 7), (4, 1)]
    return out

def register(db: sqlite3.Connection) -> list[dict]:
    """The exception register of Tutorial 16.2: one row per exception per test."""
    q, one, require_columns = _access(db)
    rows = []
    for e in journal_entries(db):
        for f in JE_FLAGS:
            if e["flags"][f]:
                rows.append(dict(test=f"JE {f}", doc=e["number"], date=e["posting"], amount=e["amount"],
                                 employee=e["approver"]))
    for num, od, tot, cb, ab, lim, term in q(
            "SELECT p.PONumber, p.OrderDate, p.OrderTotal, p.CreatedByEmployeeID, p.ApprovedByEmployeeID, "
            "e.MaxApprovalAmount, e.TerminationDate FROM PurchaseOrder p "
            "LEFT JOIN Employee e ON e.EmployeeID = p.ApprovedByEmployeeID"):
        for test, failed in [("PO SelfApproved", cb == ab), ("PO AboveLimit", tot > lim),
                             ("PO AfterTermination", term is not None and od > term)]:
            if failed:
                rows.append(dict(test=test, doc=num, date=od, amount=tot, employee=ab))
    for rid, emp, net, ab, ad, paid, pend, pay, term in q(
            "SELECT r.PayrollRegisterID, r.EmployeeID, r.NetPay, r.ApprovedByEmployeeID, r.ApprovedDate, "
            "pp.PaymentDate, pe.PeriodEndDate, pe.PayDate, e.TerminationDate FROM PayrollRegister r "
            "LEFT JOIN PayrollPayment pp ON pp.PayrollRegisterID = r.PayrollRegisterID "
            "LEFT JOIN PayrollPeriod pe ON pe.PayrollPeriodID = r.PayrollPeriodID "
            "LEFT JOIN Employee e ON e.EmployeeID = r.EmployeeID"):
        for test, failed in [("PR PaidBeforeApproval", paid is not None and paid < ad),
                             ("PR AfterTermination", term is not None and pend > term),
                             ("PR SelfApproved", emp == ab)]:
            if failed:
                rows.append(dict(test=test, doc=f"Register {rid}", date=pay, amount=net, employee=ab))
    counts = Counter(r["test"] for r in rows)
    assert [counts[t] for t in TESTS] == [17, 6, 7, 9, 4, 9, 13, 3, 3, 3, 77], counts
    assert len({(r["test"], r["doc"]) for r in rows}) == len(rows) == 151
    return rows

def populations(db: sqlite3.Connection) -> dict[str, int]:
    q, one, require_columns = _access(db)
    return {"Journal entries": one("SELECT COUNT(*) FROM JournalEntry")[0],
            "Purchase orders": one("SELECT COUNT(*) FROM PurchaseOrder")[0],
            "Payroll": one("SELECT COUNT(*) FROM PayrollRegister")[0]}

def employees(db: sqlite3.Connection) -> dict[int, tuple[str, str]]:
    q, one, require_columns = _access(db)
    return {i: (n, t) for i, n, t in q("SELECT EmployeeID, EmployeeName, JobTitle FROM Employee")}

def reviewed_register(db: sqlite3.Connection) -> list[dict]:
    """The register of Tutorial 16.3: each exception with the disposition merged on the test and the document."""
    q, one, require_columns = _access(db)
    disp = {(t, n): (d, note) for t, n, d, note in DISPOSITIONS}
    rows = [dict(r, disposition=disp.get((r["test"], r["doc"]), (None, None))[0]) for r in register(db)]
    # Test 3: every disposition found its exception.
    assert sum(1 for r in rows if r["disposition"]) == len(DISPOSITIONS) == 15
    return rows
