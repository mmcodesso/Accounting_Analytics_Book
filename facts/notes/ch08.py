"""Chapter 8's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from notes import note

EXERCISES = "chapters/08-audit-analytics/_exercises.qmd"
MCQ = "chapters/08-audit-analytics/_multiple-choice.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
# Exercise 8.1's buckets (Tutorial 8.2, tbl-08-02) with the loss rates the exercise proposes.
BUCKETS = [(-10**9, 0.005), (1, 0.02), (31, 0.05), (61, 0.15), (91, 0.40)]


def word(n: int) -> str:
    return WORDS[n] if n < len(WORDS) else f"{n:,}"


def xr(x: float, places: int = 2) -> float:
    """Round half away from zero, as Excel's ROUND does."""
    return float(Decimal(repr(round(x, 9))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def asof(d) -> str:
    return f"{d.C}-12-31"


def open_invoices(d) -> list[dict]:
    """Tutorial 8.2's OpenInvoices: sales invoices at the as-of date, less the receipts applied and the credit memos
    dated on or before it, rounded to cents and kept if greater than zero."""
    rows = d.q("SELECT si.SalesInvoiceID, si.InvoiceNumber, si.DueDate, si.CustomerID, si.GrandTotal "
               "- COALESCE((SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a WHERE a.SalesInvoiceID = "
               "si.SalesInvoiceID AND a.ApplicationDate <= ?1), 0) "
               "- COALESCE((SELECT SUM(c.GrandTotal) FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID "
               "AND c.CreditMemoDate <= ?1), 0) FROM SalesInvoice si WHERE si.InvoiceDate <= ?1 ORDER BY si.SalesInvoiceID",
               asof(d))
    end = date.fromisoformat(asof(d))
    out = []
    for sid, number, due, customer, balance in rows:
        balance = xr(balance)
        if balance > 0:
            out.append(dict(id=sid, number=number, due=due, customer=customer, balance=balance,
                            days=(end - date.fromisoformat(due)).days))
    return out


def bucket_of(days: int) -> int:
    return [i for i, (low, _) in enumerate(BUCKETS) if days >= low][-1]


def opening_entry(d) -> str:
    return d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")


def capital_invoices(d) -> list[dict]:
    """The supplier invoices reclassified to notes payable by the Debt Reclass entries (Exercise 8.2), in posting order.
    Each entry's description names the invoice's PurchaseInvoiceID."""
    out = []
    for number, total, text in d.q("SELECT EntryNumber, TotalAmount, Description FROM JournalEntry "
                                   "WHERE EntryType = 'Debt Reclass' AND PostingDate <= ? ORDER BY PostingDate", asof(d)):
        pid = int(re.search(r"invoice (\d+)", text).group(1))
        inv = d.q("SELECT pi.InvoiceNumber, pi.SupplierID, s.SupplierName, pi.GrandTotal, po.PONumber, "
                  "po.CreatedByEmployeeID, po.ApprovedByEmployeeID FROM PurchaseInvoice pi "
                  "JOIN Supplier s ON s.SupplierID = pi.SupplierID JOIN PurchaseOrder po ON po.PurchaseOrderID = pi.PurchaseOrderID "
                  "WHERE pi.PurchaseInvoiceID = ?", pid)[0]
        payments = d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PurchaseInvoiceID = ?", pid)
        out.append(dict(entry=number, amount=total, id=pid, number=inv[0], supplier=inv[1], supplier_name=inv[2],
                        total=inv[3], po=inv[4], creator=inv[5], approver=inv[6], payments=payments))
    return out


def abbreviated(numbers: list[str], full: set[str] = frozenset()) -> list[str]:
    """Document numbers as the notes list them: a number in the same year as the one before it is shortened to its
    sequence ("-000002"), unless it is in `full`."""
    out, previous = [], None
    for n in numbers:
        prefix, seq = n.rsplit("-", 1)
        out.append(n if n in full or prefix != previous else f"-{seq}")
        previous = prefix
    return out


# --- Exercise 8.1 --------------------------------------------------------------------------------

@note("ch08.ex1", EXERCISES)
def ex1(d, claim):
    invoices = open_invoices(d)
    buckets = [dict(n=0, amount=0.0) for _ in BUCKETS]
    for inv in invoices:
        b = buckets[bucket_of(inv["days"])]
        b["n"] += 1
        b["amount"] += inv["balance"]
    for b, (_, rate) in zip(buckets, BUCKETS):
        b["amount"] = xr(b["amount"])
        b["loss"] = xr(b["amount"] * rate)
    loss = xr(sum(b["loss"] for b in buckets))
    entry = opening_entry(d)
    ar = d.account("1020")
    opening = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?", ar, entry)
    total = xr(sum(i["balance"] for i in invoices))
    ledger = d.balance(["1020"], asof(d))
    claim(abs(ledger - total - opening) < 0.005,
          "the ledger exceeds the open invoices by exactly the opening balance line of account 1020")
    claim(d.one("SELECT COUNT(*) FROM CashReceiptApplication a LEFT JOIN SalesInvoice si ON si.SalesInvoiceID = "
                "a.SalesInvoiceID WHERE si.SalesInvoiceID IS NULL") == 0,
          "every cash application is to an invoice, so none reduces the opening balance")
    small = sorted((i for i in invoices if i["balance"] < 10), key=lambda i: i["days"])
    current = [i for i in small if i["days"] <= 0]
    claim(len(current) == 1, "exactly one balance under $10 is current")
    cur = current[0] if current else small[0]
    others = [i for i in small if i is not cur]
    claim(all(i["days"] >= 61 for i in others), "the other balances under $10 are 61 or more days past due")
    rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (?, ?)", d.account("6170"), d.account("1030"))
    claim(rows == 0, "neither 6170 nor 1030 has any GL rows")
    return dict(asof=asof(d), b=buckets, n=len(invoices), total=total, loss=loss, opening=opening, entry=entry,
                loss_with=xr(loss + opening * BUCKETS[-1][1]), small=len(small),
                small_total=xr(sum(i["balance"] for i in small)), cur=dict(number=cur["number"], balance=cur["balance"]),
                low=min(i["balance"] for i in others), high=max(i["balance"] for i in others))


# --- Exercise 8.2 --------------------------------------------------------------------------------

@note("ch08.ex2", EXERCISES)
def ex2(d, claim):
    end = asof(d)
    open_ap = xr(d.one("SELECT SUM(b) FROM (SELECT pi.GrandTotal - COALESCE((SELECT SUM(p.Amount) FROM DisbursementPayment p "
                       "WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID AND p.PaymentDate <= ?1), 0) AS b "
                       "FROM PurchaseInvoice pi WHERE pi.InvoiceDate <= ?1) WHERE b > 0", end))
    ap = d.account("2010")
    sources = dict(d.q("SELECT SourceDocumentType, ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry "
                       "WHERE AccountID = ? AND PostingDate <= ? GROUP BY 1", ap, end))
    claim(set(sources) == {"PurchaseInvoice", "DisbursementPayment", "JournalEntry"},
          "account 2010 holds only PurchaseInvoice, DisbursementPayment, and JournalEntry rows")
    gl = xr(sum(sources.values()))
    je_rows = d.q("SELECT g.VoucherNumber, g.Debit, g.Credit, j.EntryType FROM GLEntry g JOIN JournalEntry j "
                  "ON j.JournalEntryID = g.SourceDocumentID WHERE g.SourceDocumentType = 'JournalEntry' AND g.AccountID = ? "
                  "AND g.PostingDate <= ? ORDER BY g.PostingDate, g.GLEntryID", ap, end)
    entry = opening_entry(d)
    opening = [r for r in je_rows if r[0] == entry]
    claim(len(opening) == 1 and opening[0][1] == 0, f"the opening entry {entry} has one credit line to 2010")
    opening_credit = opening[0][2] if opening else 0.0
    cash = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?",
                 d.account("1010"), entry)
    claim(abs(cash - opening_credit) < 0.005, "the opening entry debits cash with exactly the amount it credits to 2010")
    claim(d.one("SELECT COUNT(*) FROM DisbursementPayment p LEFT JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = "
                "p.PurchaseInvoiceID WHERE pi.PurchaseInvoiceID IS NULL") == 0,
          "every supplier payment pays an invoice, so the opening payables have never been paid")
    capital = capital_invoices(d)
    reclass = [r for r in je_rows if r[0] != entry]
    claim(len(reclass) == len(capital) == 2 and all(r[3] == "Debt Reclass" and r[2] == 0 for r in reclass),
          "the other JournalEntry rows are two Debt Reclass debits")
    notes = d.account("2110")
    claim(all(abs(d.one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?",
                        notes, c["entry"]) - c["amount"]) < 0.005 for c in capital),
          "each Debt Reclass entry credits 2110 Notes Payable")
    claim(all(abs(c["total"] - c["amount"]) < 0.005 for c in capital), "each reclass equals its capital invoice's total")
    claim(len({c["supplier"] for c in capital}) == 1, "both capital invoices are from the same supplier")
    claim(all(c["payments"] == 0 for c in capital), "the capital invoices have no supplier payments")
    reclassed = sum(c["amount"] for c in capital)
    claim(abs(open_ap - reclassed + opening_credit - gl) < 0.005,
          "open invoices less the reclasses plus the opening balance equal the ledger")
    titles = {r[0]: (r[1], r[2]) for r in d.q("SELECT EmployeeID, JobTitle, MaxApprovalAmount FROM Employee")}
    claim(all(c["creator"] == c["approver"] for c in capital), "the purchase orders were created and approved by one employee")
    claim(len({titles[c["approver"]] for c in capital}) == 1, "the same role approved both purchase orders")
    role, limit = titles[capital[0]["approver"]]
    return dict(asof=asof(d), open_ap=open_ap, gl=gl, pi=sources["PurchaseInvoice"], dp=sources["DisbursementPayment"],
                je=sources["JournalEntry"], rows=word(len(je_rows)), entry=entry, opening=opening_credit,
                capital=capital, reclassed=reclassed, role=role, limit=limit)


# --- Exercise 8.3 --------------------------------------------------------------------------------

@note("ch08.ex3", EXERCISES)
def ex3(d, claim):
    invoices = open_invoices(d)
    customers = {r[0]: dict(name=r[1], limit=r[2], terms=r[3], segment=r[4]) for r in d.q(
        "SELECT CustomerID, CustomerName, CreditLimit, PaymentTerms, CustomerSegment FROM Customer")}
    balance, past_due = defaultdict(float), defaultdict(float)
    for i in invoices:
        balance[i["customer"]] += i["balance"]
        if i["days"] > 0:
            past_due[i["customer"]] += i["balance"]
    total = sum(balance.values())
    over = sorted(((k, v) for k, v in balance.items() if v > customers[k]["limit"]), key=lambda kv: -kv[1])
    claim(all(abs(past_due[k]) < 0.005 for k, _ in over), "none of the customers over their limit has a past-due balance")
    ranked = sorted(balance.items(), key=lambda kv: -kv[1])
    top = [dict(name=customers[k]["name"], balance=v, over=k in dict(over)) for k, v in ranked[:5]]
    segments_top = {customers[k]["segment"] for k, _ in ranked[:5]}
    claim(len(segments_top) == 1, "the five largest balances are all in one segment")
    segment = defaultdict(float)
    for k, v in balance.items():
        segment[customers[k]["segment"]] += v
    terms = defaultdict(lambda: [0.0, 0.0, set()])
    for i in invoices:
        t = terms[customers[i["customer"]]["terms"]]
        t[0] += i["balance"]
        t[2].add(i["customer"])
        if i["days"] > 0:
            t[1] += i["balance"]
    mismatch = d.one("SELECT COUNT(*) FROM SalesInvoice si JOIN Customer c ON c.CustomerID = si.CustomerID "
                     "WHERE CAST(REPLACE(c.PaymentTerms, 'Net ', '') AS INTEGER) <> "
                     "CAST(julianday(si.DueDate) - julianday(si.InvoiceDate) AS INTEGER)")
    claim(mismatch == 0, "every invoice's due date matches its customer's PaymentTerms")
    return dict(asof=asof(d), customers=len(balance), n_over=word(len(over)).capitalize(),
                over=[dict(customers[k], balance=v) for k, v in over], top=top, segment_top=segments_top.pop(),
                top5=sum(v for _, v in ranked[:5]) / total, top10=sum(v for _, v in ranked[:10]) / total,
                segments=sorted(segment.items(), key=lambda kv: -kv[1]),
                terms=[(t, v[0], v[1], len(v[2])) for t, v in sorted(terms.items(), key=lambda kv: int(kv[0].split()[-1]))])


# --- Exercise 8.4 --------------------------------------------------------------------------------

@note("ch08.ex4", EXERCISES)
def ex4(d, claim):
    rows = d.q("SELECT p.SupplierID, p.Amount, julianday(p.PaymentDate) - julianday(pi.DueDate), s.SupplierName, "
               "s.SupplierCategory FROM DisbursementPayment p JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = "
               "p.PurchaseInvoiceID JOIN Supplier s ON s.SupplierID = p.SupplierID WHERE p.PaymentDate BETWEEN ? AND ?",
               f"{d.C}-01-01", f"{d.C}-12-31")
    spend = defaultdict(float)
    for r in rows:
        spend[r[0]] += r[1]
    total = sum(spend.values())
    marks, running = {}, 0.0
    for rank, (_, amount) in enumerate(sorted(spend.items(), key=lambda kv: -kv[1]), 1):
        running += amount
        for share in (0.5, 0.8, 0.9):
            if share not in marks and running >= share * total:
                marks[share] = rank
    largest = max(spend, key=spend.get)
    name, category = next((r[3], r[4]) for r in rows if r[0] == largest)
    share = spend[largest] / total
    claim(share < 0.05 and marks[0.5] >= 10, "concentration is low (the largest supplier under 5%, ten or more for half)")
    categories = defaultdict(float)
    for r in rows:
        categories[r[4]] += r[1]
    days = [r[2] for r in rows]
    after = [r for r in rows if r[2] > 0]
    median = statistics.median(days)
    claim(median > 0, "the median payment is after the due date")
    claim(all(t.startswith("Net ") for (t,) in d.q("SELECT DISTINCT PaymentTerms FROM Supplier")),
          "no supplier's terms offer an early-payment discount")
    return dict(n=len(rows), suppliers=len(spend), total=total, n50=marks[0.5], n80=marks[0.8], n90=marks[0.9],
                top=dict(name=name, category=category, share=share),
                categories=sorted(categories.items(), key=lambda kv: -kv[1]),
                before=sum(1 for x in days if x < 0), on=sum(1 for x in days if x == 0), after=len(after),
                after_share=len(after) / len(rows), after_value=sum(r[1] for r in after) / total,
                median=median, mean=statistics.mean(days), late30=sum(1 for x in days if x > 30))


# --- Exercise 8.5 --------------------------------------------------------------------------------

@note("ch08.ex5", EXERCISES)
def ex5(d, claim):
    emp = {r[0]: dict(name=r[1], title=r[2], limit=r[3], terminated=r[4]) for r in d.q(
        "SELECT EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount, TerminationDate FROM Employee")}
    cfo = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Chief Financial Officer'")
    orders = []
    for pid, number, ordered, creator, approver, total in d.q(
            "SELECT PurchaseOrderID, PONumber, OrderDate, CreatedByEmployeeID, ApprovedByEmployeeID, OrderTotal "
            "FROM PurchaseOrder ORDER BY PurchaseOrderID"):
        a = emp[approver]
        orders.append(dict(number=number, total=total, approver=approver, creator=creator,
                           self=creator == approver, above=total > a["limit"],
                           term=a["terminated"] is not None and a["terminated"] < ordered))
    capital = capital_invoices(d)
    big = {c["po"] for c in capital}
    selfs = [o for o in orders if o["self"]]
    claim(big <= {o["number"] for o in selfs}, "the capital purchase orders are self-approved")
    big_roles = {emp[o["approver"]]["title"] for o in orders if o["number"] in big}
    claim(len(big_roles) == 1, "one role created and approved the capital purchase orders")
    big_approver = next(o["approver"] for o in orders if o["number"] in big)
    above = [o for o in orders if o["above"]]
    zero = sorted({emp[o["approver"]]["title"] for o in above if o["self"] and emp[o["approver"]]["limit"] == 0})
    claim(all(emp[o["approver"]]["limit"] == 0 or o["number"] in big for o in above if o["self"]),
          "the self-approved orders above the limit are the capital orders or approved with a limit of 0")
    others = [dict(number=o["number"], title=emp[o["approver"]]["title"], total=o["total"],
                   limit=emp[o["approver"]]["limit"]) for o in above if not o["self"] and not o["term"]]
    claim(all(o["limit"] > 0 for o in others), "the other orders above the limit had approvers with a nonzero limit")
    term = [o for o in orders if o["term"]]
    claim(len({o["approver"] for o in term}) == 1, "one approver approved all the orders after termination")
    t = emp[term[0]["approver"]]
    scores = Counter(o["self"] + o["above"] + o["term"] for o in orders)
    claim(max(scores) == 2, "no order fails all three tests")
    # requisitions
    reqs = d.q("SELECT RequisitionID, RequisitionNumber, RequestDate, RequestedByEmployeeID, ApprovedByEmployeeID, Status, "
               "Quantity * EstimatedUnitCost, ItemID, Quantity, EstimatedUnitCost FROM PurchaseRequisition ORDER BY RequisitionID")
    bands = [sum(1 for r in reqs if low <= r[6] < low + 50) for low in range(4800, 5200, 50)]
    claim(bands[3] >= 2 * max(bands[2], bands[4]), "the 4,950-4,999.99 band has twice the count of any neighbor")
    band = [r for r in reqs if 4950 <= r[6] < 5000]
    claim(all(r[5] == "Converted to PO" for r in band), "all the band's requisitions were converted to POs")
    unapproved = [r for r in band if r[4] is None]
    claim({r[0] for r in unapproved} == {r[0] for r in reqs if r[4] is None},
          "the band's requisitions without an approver are all the requisitions without one (Exercise 2.5)")
    runs, current = [], [band[0]]
    for r in band[1:]:
        if r[0] == current[-1][0] + 1 and r[6] == current[-1][6]:
            current.append(r)
        else:
            runs.append(current)
            current = [r]
    runs = [run for run in runs + [current] if len(run) > 1]
    claim(len(runs) >= 1 and len({len(run) for run in runs}) == 1, "the runs of consecutive requisitions have one length")
    claim(all(r[2][5:] == "01-01" for run in runs for r in run), "the runs are dated January 1")
    claim(len({(r[8], r[9]) for run in runs for r in run}) == 1, "all the runs' requisitions have the same quantity and unit cost")
    claim(all(len({r[7] for r in run}) == len(run) for run in runs), "each run is for different items")
    claim(all(len({r[3] for r in run}) >= 2 for run in runs)
          and any(len({r[3] for r in run}) < len(run) for run in runs), "the runs have mostly (not all) different requesters")
    five = [emp[k]["title"] for k in sorted(emp) if emp[k]["limit"] == 5000]
    # supplier invoices
    invoices = d.q("SELECT PurchaseInvoiceID, ApprovedByEmployeeID, GrandTotal FROM PurchaseInvoice ORDER BY PurchaseInvoiceID")
    not_cfo = [r for r in invoices if r[1] != cfo]
    by = defaultdict(list)
    for r in not_cfo:
        by[r[1]].append(r)
    zero_inv = [k for k in by if emp[k]["limit"] == 0]
    within = [k for k in by if emp[k]["limit"] > 0 and all(r[2] <= emp[k]["limit"] for r in by[k])]
    beyond = [k for k in by if emp[k]["limit"] > 0 and all(r[2] > emp[k]["limit"] for r in by[k])]
    claim(len(zero_inv) == len(within) == len(beyond) == 1 and len(by) == 3,
          "three approvers other than the CFO: one with a limit of 0, one within a limit, one above a limit")
    family = d.one("SELECT JobFamily FROM Employee WHERE EmployeeID = ?", within[0])
    claim(family not in ("Purchasing and Procurement", "Finance and Accounting"),
          "the approver within the limit is outside the purchasing and accounting roles")
    claim([r[0] for r in by[beyond[0]]] == [c["id"] for c in capital] and beyond[0] == big_approver,
          "the invoices above the limit are the note-financed capital invoices, approved by the capital orders' approver")
    groups = {}
    for key, k in (("zero", zero_inv[0]), ("within", within[0]), ("beyond", beyond[0])):
        groups[key] = dict(emp[k], ids=[r[0] for r in by[k]], totals=[r[2] for r in by[k]])
    # near-duplicate payments
    pays = d.q("SELECT SupplierID, Amount, PurchaseInvoiceID, PaymentDate FROM DisbursementPayment WHERE PaymentDate < ?",
               f"{d.N}-01-01")
    same = defaultdict(list)
    for p in pays:
        same[(p[0], p[1])].append(p)
    pairs = [v for v in same.values() if len(v) > 1]
    claim(max(len(v) for v in pairs) == 2, "no group of same-supplier, same-amount payments is larger than two")
    within30 = sum(1 for v in pairs if abs((date.fromisoformat(v[1][3]) - date.fromisoformat(v[0][3])).days) <= 30)
    same_invoice = sum(c for c in Counter((p[0], p[1], p[2]) for p in pays).values() if c > 1)
    claim(same_invoice == 0, "SameInvoice flags no payment")
    # purchase order numbers
    gaps = []
    for y in d.years:
        n, low, high = d.q("SELECT COUNT(*), MIN(CAST(substr(PONumber, 9) AS INTEGER)), MAX(CAST(substr(PONumber, 9) AS INTEGER)) "
                           "FROM PurchaseOrder WHERE substr(PONumber, 4, 4) = ?", str(y))[0]
        gaps.append(dict(year=y, n=n, low=low, high=high))
    claim(all(g["n"] == g["high"] - g["low"] + 1 for g in gaps), "no purchase order numbers are missing")
    claim(all(b["low"] == a["high"] + 1 for a, b in zip(gaps, gaps[1:])), "the sequence continues across years")
    claim(sum(g["n"] for g in gaps) == len(orders), "every purchase order is in a fiscal year of the window")
    return dict(orders=len(orders), cfo_share=sum(1 for o in orders if o["approver"] == cfo) / len(orders),
                selfs=[dict(number=n, total=o["total"], big=o["number"] in big)
                       for n, o in zip(abbreviated([o["number"] for o in selfs], big), selfs)],
                n_big=word(len(big)), big_role=big_roles.pop(), big_limit=emp[big_approver]["limit"],
                n_above=len(above), zero_titles=[z + "s" for z in zero], others=others,
                term=[o["number"] for o in term], term_name=t["name"], term_title=t["title"], term_date=t["terminated"],
                s2=scores[2], s1=scores[1], bands=bands, band=len(band),
                unapproved=abbreviated([r[1] for r in unapproved]),
                runs=[dict(first=run[0][1], last="-" + run[-1][1].rsplit("-", 1)[1]) for run in runs],
                run_len=word(len(runs[0])), qty=runs[0][0][8], cost=runs[0][0][9], value=runs[0][0][6],
                five=five, n_five=word(len(five)).capitalize(),
                inv_total=len(invoices), inv_cfo=len(invoices) - len(not_cfo), inv_other=len(not_cfo), g=groups,
                n_payments=sum(len(v) for v in pairs), pairs=len(pairs), within30=within30, gaps=gaps)


# --- Exercise 8.6 --------------------------------------------------------------------------------

@note("ch08.ex6", EXERCISES)
def ex6(d, claim):
    promos = {r[0]: dict(id=r[0], code=r[1], collection=r[2], scope=r[3], pct=r[4], start=r[5], end=r[6], approver=r[7],
                         approved=r[8]) for r in d.q(
        "SELECT PromotionID, PromotionCode, CollectionName, ScopeType, DiscountPct, EffectiveStartDate, EffectiveEndDate, "
        "ApprovedByEmployeeID, ApprovedDate FROM PromotionProgram ORDER BY PromotionID")}
    flagged = [p for p in promos.values() if p["end"] <= p["start"]]
    claim(len({p["pct"] for p in flagged}) == 1, "the flagged promotions have one discount rate")
    claim(all(p["scope"] == "Collection" for p in flagged), "the flagged promotions are collection promotions")
    claim(len({p["approver"] for p in flagged}) == 1, "one employee approved the flagged promotions")
    claim(all(p["approved"] == p["start"] for p in flagged), "each was approved on its start date")
    approver = d.q("SELECT EmployeeID, EmployeeName, JobTitle FROM Employee WHERE EmployeeID = ?", flagged[0]["approver"])[0]
    lines = d.q("SELECT l.PromotionID, o.OrderDate, si.InvoiceDate, l.Quantity * l.UnitPrice * l.Discount "
                "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                "JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID WHERE l.PromotionID IS NOT NULL")
    outside = defaultdict(list)
    inside = defaultdict(int)
    for pid, ordered, invoiced, discount in lines:
        p = promos[pid]
        if p["start"] <= ordered <= p["end"]:
            inside[pid] += 1
        else:
            outside[pid].append((ordered, invoiced, discount))
    claim(all(inside[p["id"]] == 0 for p in flagged), "all of the flagged promotions' lines were ordered outside the dates")
    claim(set(outside) == {p["id"] for p in flagged}, "every line of the other promotions was ordered within its dates")
    flagged_lines = [dict(n=len(outside[p["id"]]), discount=sum(x[2] for x in outside[p["id"]])) for p in flagged]
    order_months = [{int(x[0][5:7]) for x in outside[p["id"]]} for p in flagged]
    claim(len({frozenset(m) for m in order_months}) == 1, "each flagged promotion's lines were ordered in the same months")
    claim(all({int(x[0][:4]) for x in outside[p["id"]]} == {int(p["start"][:4])} for p in flagged),
          "each promotion's lines were ordered in its own year")
    last = sorted({int(max(x[1] for x in outside[p["id"]])[5:7]) for p in flagged})
    # pending overrides
    pending = d.q("SELECT PriceOverrideApprovalID, SalesOrderLineID, ReferenceUnitPrice, ApprovedUnitPrice "
                  "FROM PriceOverrideApproval WHERE Status = 'Pending' ORDER BY PriceOverrideApprovalID")
    overrides, methods, below, billed = [], [], 0.0, 0
    for oid, line, reference, approved in pending:
        rows = d.q("SELECT si.InvoiceNumber, l.UnitPrice, l.Quantity, l.PricingMethod, l.PriceOverrideApprovalID, "
                   "l.ShipmentLineID FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "WHERE l.SalesOrderLineID = ? ORDER BY si.InvoiceNumber", line)
        claim(all(r[1] == approved for r in rows), f"override {oid}'s lines were billed at the pending ApprovedUnitPrice")
        claim(all(r[4] is None for r in rows), f"override {oid}'s lines carry a blank PriceOverrideApprovalID")
        claim(len({r[5] for r in rows}) == len(rows), f"override {oid}'s invoice lines are separate shipments")
        methods += [r[3] for r in rows if r[3] not in methods]
        below += sum((reference - r[1]) * r[2] for r in rows)
        billed += len(rows)
        overrides.append(dict(id=oid, line=line, approved=approved, invoices=[r[0] for r in rows],
                              shipments=word(len(rows))))
    claim(all(m.endswith("Price List") for m in methods), "the lines carry a price-list PricingMethod")
    # price lists
    lists = {r[0]: dict(id=r[0], name=r[1], scope=r[2], customer=r[3], segment=r[4], start=r[5], end=r[6], status=r[7],
                        lines=r[8]) for r in d.q(
        "SELECT pl.PriceListID, pl.PriceListName, pl.ScopeType, pl.CustomerID, pl.CustomerSegment, pl.EffectiveStartDate, "
        "pl.EffectiveEndDate, pl.Status, (SELECT COUNT(*) FROM PriceListLine x WHERE x.PriceListID = pl.PriceListID) "
        "FROM PriceList pl ORDER BY pl.PriceListID")}
    order_lines = d.q("SELECT pll.PriceListID, o.OrderDate, l.LineTotal FROM SalesOrderLine l "
                      "JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
                      "JOIN PriceListLine pll ON pll.PriceListLineID = l.PriceListLineID")
    after = [r for r in order_lines if r[1] > lists[r[0]]["end"]]
    expired = [lst for lst in lists.values() if lst["status"] == "Expired"]
    claim({r[0] for r in after} == {lst["id"] for lst in expired}, "the lines priced after their list's end are on the Expired lists")
    claim(all(lst["scope"] == "Segment" for lst in expired), "the Expired lists are segment lists")
    claim(not any((o["scope"], o["segment"], o["customer"]) == (lst["scope"], lst["segment"], lst["customer"])
                  and o["id"] != lst["id"] and o["end"] > lst["end"] for lst in expired for o in lists.values()),
          "no Expired list has a successor for its segment")
    used = Counter(r[0] for r in order_lines)
    per_list = []
    for lst in expired:
        years = sorted(Counter(r[1][:4] for r in after if r[0] == lst["id"]).items())
        everything = sum(n for _, n in years) == used[lst["id"]]
        if not everything:
            end_year = [n for y, n in years if y == lst["end"][:4]]
            claim(not end_year or lst["end"][5:7] == "12" and int(lst["end"][8:]) >= 20,
                  f"list {lst['id']}'s lines after its end in its last year are in late December")
        per_list.append(dict(id=lst["id"], all=everything, n=used[lst["id"]], end_year=lst["end"][:4],
                             years=[(int(y), n) for y, n in years]))
    unused = [lst for lst in lists.values() if lst["status"] == "Active" and lst["lines"] == 0]
    claim(all(used[lst["id"]] == 0 for lst in unused), "the Active lists without lines price nothing")
    original = [lst for lst in lists.values() if lst["status"] == "Active" and lst["lines"] > 0 and lst["scope"] == "Segment"
                and unused and lst["segment"] == unused[0]["segment"]]
    claim(len(original) == 1, "the unused lists copy one segment list")
    claim(all(u["segment"] == original[0]["segment"] and (u["start"], u["end"]) == (original[0]["start"], original[0]["end"])
              and u["scope"] == "Segment" and u["name"].endswith("Overlap") for u in unused),
          "the unused lists are copies of that list named Overlap, with its dates")
    # customer lists
    own = d.q("SELECT o.CustomerID, c.CustomerName, c.CustomerSegment, mine.PriceListID, l.SalesOrderLineID, o.OrderDate, "
              "l.PricingMethod, pll.PriceListID, l.UnitPrice, (SELECT x.UnitPrice FROM PriceListLine x WHERE x.PriceListID = "
              "mine.PriceListID AND x.ItemID = l.ItemID), pll.UnitPrice FROM SalesOrderLine l "
              "JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID JOIN Customer c ON c.CustomerID = o.CustomerID "
              "JOIN PriceList mine ON mine.CustomerID = o.CustomerID AND mine.ScopeType = 'Customer' "
              "LEFT JOIN PriceListLine pll ON pll.PriceListLineID = l.PriceListLineID "
              "WHERE l.PricingMethod NOT IN ('Customer Price List', 'Approved Override') ORDER BY l.SalesOrderLineID")
    claim(len({r[0] for r in own}) == 1, "one customer with its own list has lines under another pricing method")
    claim(len({(r[6], r[7]) for r in own}) == 1, "those lines have one PricingMethod and cite one list")
    claim(all(r[8] == r[9] and r[8] != r[10] for r in own),
          "their UnitPrice equals the customer's own list, not the list they cite")
    cited = lists[own[0][7]]
    stale = sorted({int(r[5][:4]) for r in own if r[5] > cited["end"]})
    claim(0 < len(stale) < len(own), "the cited list had expired for some, but not all, of the lines")
    return dict(flagged=flagged, pct=flagged[0]["pct"], approver=dict(id=approver[0], name=approver[1], title=approver[2]),
                flagged_lines=flagged_lines, n_lines=sum(f["n"] for f in flagged_lines),
                discount=sum(f["discount"] for f in flagged_lines),
                order_months=[MONTHS[m - 1] for m in sorted(order_months[0])], last_months=[MONTHS[m - 1] for m in last],
                overrides=overrides, billed=word(billed), methods=methods, below=below,
                expired=expired, after=len(after), after_total=sum(r[2] for r in after), per_list=per_list,
                unused=[u["id"] for u in unused], n_unused=word(len(unused)), original=original[0],
                customer=dict(id=own[0][0], name=own[0][1], segment=own[0][2], list=own[0][3]),
                own=[dict(line=r[4], date=r[5], price=r[8], cited=r[10]) for r in own], n_own=word(len(own)),
                method=own[0][6], cited=cited["id"], stale=stale)


# --- Multiple-choice answer key ------------------------------------------------------------------

@note("ch08.mcq", MCQ)
def mcq(d, claim):
    rows = d.q("SELECT p.Amount, i.GrandTotal, p.PaymentNumber, p.CheckNumber, p.PaymentMethod FROM DisbursementPayment p "
               "JOIN PurchaseInvoice i ON i.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate <= ?", asof(d))
    digits = Counter(int(f"{a:.8E}"[0]) for a, *_ in rows if a > 0)
    n = sum(digits.values())
    mad = sum(abs(digits[k] / n - math.log10(1 + 1 / k)) for k in range(1, 10)) / 9
    claim(0.012 <= mad < 0.015, "the payments' MAD is in the marginally acceptable range (0.012 to 0.015)")
    claim(round(mad, 3) == 0.013, "the MAD rounds to the 0.013 of question 5's stem")
    partial = [g for a, g, *_ in rows if a < g - 0.005]
    claim(min(partial) >= 1000, "partial payments come only from invoices of $1,000 or more")
    checks = [(p, c) for _, _, p, c, m in rows if m == "Check"]
    follows = sum(1 for p, c in checks if c and int(re.search(r"\d+$", c).group()) == int(re.search(r"\d+$", p).group()))
    claim(follows >= 0.99 * len(checks), "check numbers follow the numbering of all payments")
    claim(all(not c for _, _, _, c, m in rows if m != "Check") and any(m != "Check" for *_, m in rows),
          "ACH and wire payments carry no check number, so they leave the gaps")
    return dict(mad=mad)
