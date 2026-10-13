"""Chapter 8's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 8 is the fifth and last Excel chapter (audit analytics: population checks, stratification, Benford's Law, aging and
confirmations, journal entry tests, duplicate, gap and threshold tests), so, as in Chapters 4 to 7, the contexts do three jobs:

- they supply the values the tutorials' checkpoints show (the Population, Strata, Benford, Aging, Confirmations, JE Summary and
  Drilldown worksheets of AuditAnalytics.xlsx), which no registered note covers,
- they supply what each exercise's steps need beyond its registered note (ch08.ex1 to ch08.ex6): the values of a model answer's
  intermediate tables, the symptoms of the mistakes a guide names (a missing year filter, a missing guard on a blank date),
- they check, with claim(), every table and column the guides name and every statement about the data that another dataset
  could falsify, so a roll flags the wording instead of leaving it stale.

Keys: ch08.chapter (the chapter note and its three tutorials) and ch08.g1 to ch08.g6 (the exercises; each is used next to the
registered note ch08.ex1 to ch08.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter08-exercises (Chapter 8 Exercises - Solutions.xlsx).
"""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from notes.ch08 import BUCKETS, asof, bucket_of, capital_invoices, open_invoices, opening_entry, word, xr

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "08-audit-analytics"
DECK = REPO / "slides" / "chapter-08" / "index.qmd"
LABELS = ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]      # tbl-08-02
RATES = [rate for _, rate in BUCKETS]                                                # Exercise 8.1
STRATA = [0, 1000, 10000, 50000, 100000]                                             # Tutorial 8.1, Step 3
KEY_ITEM, SAMPLE = 50000, 20                                                         # Tutorial 8.2, Step 7
MAD_RANGES = [(0.006, "close conformity"), (0.012, "acceptable conformity"),         # tbl-08-01
              (0.015, "marginally acceptable conformity"), (math.inf, "nonconformity")]
BAND_FROM, BAND_WIDTH, BAND_COUNT, BAND_EXAMINED = 4800, 50, 8, 4950                 # Exercise 8.5 (4)


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


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import package
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/08-audit-analytics/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 8\b")
    letters, _ = package.answer_key(comment)
    key = {i: a for i, a in enumerate(letters, 1)}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def and_list(items) -> str:
    items = [str(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    return items[0] + " and " + items[1] if len(items) == 2 else ", ".join(items[:-1]) + ", and " + items[-1]


def lead(amount: float) -> int:
    """The first significant digit, as =--LEFT(TEXT(x,"0.00000000E+00"),1) returns it."""
    return int(f"{amount:.8E}"[0])


def mad(counts: Counter) -> float:
    n = sum(counts.values())
    return sum(abs(counts[k] / n - math.log10(1 + 1 / k)) for k in range(1, 10)) / 9


def conformity(value: float) -> str:
    return next(label for limit, label in MAD_RANGES if value <= limit)


def round0(x: float) -> int:
    """Excel's TEXT(x, "0"): half away from zero."""
    return int(Decimal(repr(x)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def employees(d) -> dict[int, dict]:
    return {r[0]: dict(id=r[0], name=r[1], title=r[2], limit=r[3], terminated=r[4], family=r[5]) for r in d.q(
        "SELECT EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount, TerminationDate, JobFamily FROM Employee")}


# --- the chapter note and its tutorials ------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "DisbursementPayment": ["DisbursementID", "PaymentNumber", "PaymentDate", "SupplierID", "PurchaseInvoiceID", "Amount",
                            "CheckNumber", "PaymentMethod"],
    "PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "GrandTotal", "ApprovedByEmployeeID",
                        "PurchaseOrderID", "SupplierID"],
    "Supplier": ["SupplierID", "SupplierName", "SupplierCategory"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType",
                "SourceDocumentID", "Description"],
    "Account": ["AccountID", "AccountNumber", "AccountName"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "CustomerID", "GrandTotal", "FreightAmount"],
    "CashReceiptApplication": ["SalesInvoiceID", "ApplicationDate", "AppliedAmount"],
    "CreditMemo": ["OriginalSalesInvoiceID", "CreditMemoDate", "GrandTotal"],
    "Customer": ["CustomerID", "CustomerName", "CreditLimit", "PaymentTerms", "CustomerSegment"],
    "JournalEntry": ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount", "CreatedByEmployeeID",
                     "CreatedDate", "ApprovedByEmployeeID", "Description"],
    "Employee": ["EmployeeID", "EmployeeName", "JobTitle", "MaxApprovalAmount", "TerminationDate", "JobFamily"],
}


def tutorial_81(d, claim) -> dict:
    cut = f"{d.N}-01-01"
    rows = d.q("SELECT p.Amount, i.GrandTotal, p.SupplierID, p.PurchaseInvoiceID FROM DisbursementPayment p "
               "JOIN PurchaseInvoice i ON i.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate < ?", cut)
    claim(len(rows) == d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PaymentDate < ?", cut),
          "every payment before the cutoff pays an invoice that is in PurchaseInvoice")
    cash = d.account("1010")
    ledger_n, ledger_total = d.q("SELECT COUNT(*), SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'DisbursementPayment' "
                                 "AND AccountID = ? AND PostingDate < ?", cash, cut)[0]
    amounts = [r[0] for r in rows]
    total = sum(amounts)
    claim(ledger_n == len(rows) and abs(ledger_total - total) < 0.005,
          "the payments agree with the cash credits of the ledger in count and total")
    after = d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PaymentDate >= ?", cut)
    claim(after > 0, f"the ledger already holds supplier payments dated in {d.N}, which the date filters leave out")
    bounds = STRATA + [max(amounts) + 0.01]
    strata = []
    for low, high in zip(bounds, bounds[1:]):
        s = [a for a in amounts if low <= a < high]
        strata.append(dict(low=low, high=high, count=len(s), value=sum(s), share_n=len(s) / len(amounts),
                           share_v=sum(s) / total))
    top = [r for r in rows if r[0] >= KEY_ITEM]
    claim(all(abs(r[0] - r[1]) < 0.005 for r in top), f"each payment of {KEY_ITEM:,} or more pays its invoice in full")
    claim(len({r[3] for r in top}) == len(top), "no invoice receives two of the largest payments")
    claim(len({r[2] for r in top}) < len(top), "the largest payments went to fewer suppliers than there are payments")
    claim(strata[0]["share_n"] > 0.7 and strata[0]["share_v"] < 0.25,
          "about three-quarters of the payments are under 1,000 and hold less than a quarter of the value")
    claim(strata[2]["count"] < 1000 and 0.3 < strata[2]["share_v"] < 0.4,
          "fewer than a thousand payments between 10,000 and 50,000 hold about a third of the value")

    def test(xs):
        c = Counter(lead(a) for a in xs)
        return dict(n=len(xs), counts=c, mad=mad(c), label=conformity(mad(c)))
    part = [r for r in rows if r[0] < r[1]]
    full = [r[0] for r in rows if not r[0] < r[1]]
    all_t, full_t, part_t = test(amounts), test(full), test([r[0] for r in part])
    inv_t = test([x for (x,) in d.q("SELECT GrandTotal FROM PurchaseInvoice")])
    claim(all_t["label"] == "marginally acceptable conformity", "the MAD of all payments is in the marginally acceptable range")
    claim(full_t["label"] == "acceptable conformity", "the MAD of the full payments is in the acceptable range")
    claim(part_t["label"] == "nonconformity", "the MAD of the partial payments is in the nonconformity range")
    claim(inv_t["label"] == "close conformity", "the first digits of the supplier invoices conform closely")
    claim(all(r[0] <= r[1] + 0.005 for r in rows), "no payment is above its invoice's GrandTotal, so Partial is FALSE only for full payments")
    expected = {k: math.log10(1 + 1 / k) for k in range(1, 10)}
    share = {k: all_t["counts"][k] / all_t["n"] for k in range(1, 10)}
    claim(all(share[k] < expected[k] for k in (1, 2)) and all(share[k] > expected[k] for k in range(5, 10)),
          "digits 1 and 2 appear less often than Benford's Law expects, and digits 5 to 9 more often")
    part_invoices = {r[3]: r[1] for r in part}
    claim(min(part_invoices.values()) >= 1000, "only invoices of 1,000 or more are paid in parts")
    under2000 = sum(1 for v in part_invoices.values() if v < 2000) / len(part_invoices)
    claim(under2000 > 0.5, "most invoices paid in parts are under 2,000")
    zero = sum(1 for a in amounts if lead(a) == 0)
    claim(zero == 0, "no payment has a first digit of 0")
    below1 = sum(1 for a in amounts if a < 1)
    wrong_text = sum(1 for a in amounts if str(round0(a))[0] != str(lead(a)))
    wrong_either = sum(1 for a in amounts if str(round0(a))[0] != str(lead(a)) or str(a)[0] != str(lead(a)))
    claim(below1 > 100 and wrong_text > 300, "the two shortcut formulas misclassify several hundred payments between them")
    return dict(n=len(rows), total=total, ledger_n=ledger_n, ledger_total=ledger_total, after=after, strata=strata,
                top_n=len(top), top_suppliers=len({r[2] for r in top}), top_total=sum(r[0] for r in top),
                all=all_t, full=full_t, part=part_t, inv=inv_t, part_invoices=len(part_invoices),
                min_part=min(part_invoices.values()), under2000=under2000, zero=zero, below1=below1, wrong_text=wrong_text,
                wrong_either=wrong_either, cash_id=cash, digit1=share[1], digit1_expected=expected[1],
                digit9=share[9], digit9_expected=expected[9])


def balances(d) -> list[dict]:
    """Every invoice's balance at the as-of date (Tutorial 8.2's formula, before the filter), with its credit memos."""
    end = asof(d)
    return [dict(id=r[0], balance=xr(r[1]), credits=r[2]) for r in d.q(
        "SELECT si.SalesInvoiceID, si.GrandTotal - COALESCE((SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a "
        "WHERE a.SalesInvoiceID = si.SalesInvoiceID AND a.ApplicationDate <= ?1), 0) - COALESCE((SELECT SUM(c.GrandTotal) "
        "FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID AND c.CreditMemoDate <= ?1), 0), "
        "(SELECT COUNT(*) FROM CreditMemo c2 WHERE c2.OriginalSalesInvoiceID = si.SalesInvoiceID) "
        "FROM SalesInvoice si WHERE si.InvoiceDate <= ?1", end)]


def tutorial_82(d, claim) -> dict:
    end = asof(d)
    inv = open_invoices(d)
    total = xr(sum(i["balance"] for i in inv))
    buckets = [dict(label=l, n=0, amount=0.0) for l in LABELS]
    for i in inv:
        b = buckets[bucket_of(i["days"])]
        b["n"] += 1
        b["amount"] += i["balance"]
    for b in buckets:
        b["amount"] = xr(b["amount"])
        b["share"] = b["amount"] / total
    claim(buckets[0]["share"] > 0.7, "most of the open balance is current")
    claim(buckets[1]["amount"] > sum(b["amount"] for b in buckets[2:]) * 10,
          "most of the balance past due is 1 to 30 days past due; the older buckets hold very little")
    old = [i for i in inv if i["days"] > 60]
    claim(len(old) > 0 and sum(1 for i in old if i["balance"] < 10) > len(old) / 2,
          "most of the invoices more than 60 days past due carry residual balances of a few dollars")
    received = {r[0] for r in d.q("SELECT SalesInvoiceID FROM CashReceiptApplication WHERE ApplicationDate <= ?", end)}
    credited = {r[0] for r in d.q("SELECT OriginalSalesInvoiceID FROM CreditMemo WHERE CreditMemoDate <= ?", end)}
    neither = sum(1 for i in inv if i["id"] not in received and i["id"] not in credited)
    claim(neither > len(inv) / 2, "most open invoices have neither a receipt application nor a credit memo, so a null breaks their subtraction")
    neg = [b for b in balances(d) if b["balance"] < 0]
    claim(all(b["credits"] > 0 for b in neg), "every invoice with a negative balance has a credit memo (it was paid, then credited)")
    ar = d.account("1020")
    gl = d.balance(["1020"], end)
    entry = opening_entry(d)
    opening = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?", ar, entry)
    claim(abs(gl - total - opening) < 0.005, "the ledger exceeds the open invoices by exactly the opening balance line")
    sources = {r[0]: r[1] for r in d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ? GROUP BY 1",
                                       ar, end)}
    claim(set(sources) == {"SalesInvoice", "CashReceiptApplication", "CreditMemo", "JournalEntry"} and sources["JournalEntry"] == 1,
          "account 1020 holds sales invoices, receipt applications, credit memos and one journal entry line")
    allow = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (?, ?)", d.account("1030"), d.account("6170"))
    claim(allow == 0, "accounts 1030 and 6170 have no GL rows")
    cust = defaultdict(float)
    for i in inv:
        cust[i["customer"]] += i["balance"]
    key = {k: v for k, v in cust.items() if v >= KEY_ITEM}
    names = Counter(d.one("SELECT CustomerName FROM Customer WHERE CustomerID = ?", k) for k in cust)
    shared = sorted(n for n, c in names.items() if c > 1)
    claim(len(shared) == 1 and names[shared[0]] == 2, "two different customers share one name among those with an open balance")
    claim(0.35 < sum(key.values()) / total < 0.5 and len(cust) - len(key) > SAMPLE,
          "the key items hold about two-fifths of the balance, and more than the sample size of customers remain")
    return dict(n=len(inv), total=total, buckets=buckets, gl=gl, diff=xr(gl - total), entry=entry, opening=opening,
                neg_n=len(neg), customers=len(cust), key_n=len(key), key_share=sum(key.values()) / total,
                others_n=len(cust) - len(key), sample=SAMPLE, neither=neither, shared=shared[0], ar_id=ar,
                allowance_id=d.account("1030"), bad_debt_id=d.account("6170"), ar_sources=sorted(sources),
                ar_rows=sum(sources.values()))


def journal(d, claim) -> dict:
    emp = employees(d)
    rows = []
    for number, posted, kind, total, cr, created, ap in d.q(
            "SELECT EntryNumber, PostingDate, EntryType, TotalAmount, CreatedByEmployeeID, CreatedDate, ApprovedByEmployeeID "
            "FROM JournalEntry ORDER BY JournalEntryID"):
        made = datetime.fromisoformat(created)
        f = dict(Weekend=made.isoweekday() > 5, Backdated=made.date() > date.fromisoformat(posted[:10]), SelfApproved=cr == ap,
                 AboveLimit=total > emp[ap]["limit"], RoundAmount=total % 1000 == 0)
        rows.append(dict(number=number, kind=kind, total=total, f=f, score=sum(f.values()), creator=emp[cr], approver=emp[ap]))

    def category(r):
        on, kind = tuple(k for k, v in r["f"].items() if v), r["kind"]
        if r["score"] == 4:
            return "opening"
        if on == ("Weekend", "Backdated"):
            return "backdated"
        if on == ("AboveLimit",) and kind.startswith("Year-End Close"):
            return "close"
        if on == ("AboveLimit", "RoundAmount") and kind == "Debt Reclass":
            return "reclass"
        if on == ("Weekend",) and kind == "Depreciation":
            return "depreciation"
        if on == ("SelfApproved",) and kind in ("Rent", "Utilities"):
            return "self"
        if on == ("RoundAmount",) and kind == "Asset Disposal":
            return "disposal"
        return "other"
    flagged = [r for r in rows if r["score"] >= 1]
    groups = Counter(category(r) for r in flagged)
    claim(groups["other"] == 0, "every flagged entry belongs to one of the seven patterns the tutorial explains")
    scores = [sum(1 for r in rows if r["score"] == s) for s in range(5)]
    claim(scores[3] == 0 and scores[4] == 1, "no entry scores 3 and one entry scores 4")
    top = next(r for r in rows if r["score"] == 4)
    claim(top["kind"] == "Opening" and top["creator"]["title"] == "Chief Financial Officer",
          "the entry with four flags is the opening balance entry, created by the chief financial officer")
    by_title = Counter(r["creator"]["title"] for r in rows)
    claim(by_title.most_common(1)[0][0] == "Accounting Manager", "the accounting manager creates most of the entries")
    claim(by_title["Chief Financial Officer"] == 1, "the chief financial officer created exactly one entry")
    claim({r["creator"]["title"] for r in rows if r["kind"] == "Depreciation" or r["kind"].startswith("Year-End Close")} == {"Controller"},
          "the controller creates the depreciation entries and the year-end closes")
    claim({r["creator"]["title"] for r in rows if r["kind"] == "Factory Overhead"} == {"Production Manager"},
          "the production manager creates the factory overhead entries")
    limit = max(e["limit"] for e in emp.values())
    claim(all(r["total"] > limit for r in rows if r["kind"].startswith("Year-End Close")),
          "every year-end close exceeds the highest approval limit of any employee")
    entry_total = sum(r["total"] for r in rows)
    lines, debits = d.q("SELECT COUNT(*), SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")[0]
    claim(abs(entry_total - debits) < 0.005 and lines > len(rows), "the entries' totals equal the debits of their ledger lines")
    olines, odebit = d.q("SELECT COUNT(*), SUM(Debit) FROM GLEntry g JOIN Account a USING (AccountID) "
                         "WHERE g.SourceDocumentType = 'JournalEntry' AND g.VoucherNumber = ? AND a.AccountNumber = 1020", top["number"])[0]
    olines = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry' AND VoucherNumber = ?", top["number"])
    flags = {k: sum(1 for r in rows if r["f"][k]) for k in top["f"]}
    claim(all(r["approver"]["limit"] is not None for r in rows), "every approver has an approval limit")
    claim(all(r["approver"]["title"] != "Controller" or r["kind"] != "Debt Reclass" or r["total"] > r["approver"]["limit"]
              for r in rows), "the two debt reclassifications exceed the controller's limit")
    return dict(n=len(rows), total=entry_total, flags=flags, scores=scores, flagged=len(flagged), number=top["number"],
                top_title=top["creator"]["title"], top_total=top["total"], top_limit=top["approver"]["limit"], lines=lines,
                debits=debits, olines=olines, ar_line=odebit, groups=dict(groups), expected=groups["close"] + groups["depreciation"] + groups["disposal"],
                follow=groups["opening"] + groups["backdated"] + groups["reclass"] + groups["self"], max_limit=limit,
                n_am=by_title["Accounting Manager"], n_pm=by_title["Production Manager"])


@context("ch08.chapter")
def chapter(d, claim):
    schema(d, claim, CHAPTER_SCHEMA)
    t1 = tutorial_81(d, claim)
    t2 = tutorial_82(d, claim)
    t3 = journal(d, claim)
    claim(abs(t2["opening"] - d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?",
                                    d.account("1020"), t3["number"])) < 0.005,
          "the receivables difference is a line of the highest-scoring journal entry")
    ap = d.account("2010")
    t3["ap_opening"] = d.one("SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?", ap, t3["number"])
    claim(t3["ap_opening"] > 0, "the same entry credits accounts payable")
    gl_n = d.one("SELECT COUNT(*) FROM GLEntry")
    claim(gl_n > 100_000, "the ledger table has hundreds of thousands of rows, so the tutorials import it with Transform Data")
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    return dict(y=d.C, p=d.P, f=d.F, n=d.N, asof=asof(d), n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0),
                slides=slide_count(), gl_n=gl_n, n_questions=n_q, longest_correct=and_list(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3)


# --- Exercise 8.1: estimating the allowance -----------------------------------------------------------------------------

@context("ch08.g1")
def g1(d, claim):
    schema(d, claim, {"GLEntry": ["AccountID", "VoucherNumber", "SourceDocumentType", "Debit", "Credit"],
                      "Account": ["AccountID", "AccountNumber"]})
    inv = open_invoices(d)
    rows = [dict(label=l, rate=r, n=0, amount=0.0) for l, r in zip(LABELS, RATES)]
    for i in inv:
        rows[bucket_of(i["days"])]["n"] += 1
        rows[bucket_of(i["days"])]["amount"] += i["balance"]
    for r in rows:
        r["amount"] = xr(r["amount"])
        r["loss"] = xr(r["amount"] * r["rate"])
    loss = xr(sum(r["loss"] for r in rows))
    total = xr(sum(r["amount"] for r in rows))
    text = (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8")
    claim(all(re.search(rf"(?<![\d.]){r * 100:g} percent", text) for r in RATES),
          "the exercise text proposes the five loss rates the model answer uses")
    claim(rows[0]["loss"] + rows[1]["loss"] > 0.9 * loss, "the current and 1 to 30 days buckets carry most of the expected loss")
    ar = d.account("1020")
    entry = opening_entry(d)
    opening = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?", ar, entry)
    opening_loss = xr(opening * RATES[-1])
    small = sorted((i for i in inv if i["balance"] < 10), key=lambda i: -i["days"])
    current = [i for i in small if bucket_of(i["days"]) == 0]
    old = [i for i in small if i["days"] >= 61]
    claim(len(current) + len(old) == len(small), "every balance under 10 dollars is either current or 61 or more days past due")
    claim(len(current) >= 1 and current[0]["days"] < 0, "an open invoice under 10 dollars is not yet due, so the write-off must keep it")

    def expected_after(removed) -> float:
        out = 0.0
        for k, r in enumerate(rows):
            gone = sum(i["balance"] for i in removed if bucket_of(i["days"]) == k)
            out += xr((r["amount"] - gone) * r["rate"])
        return xr(out)
    after_all, after_old = expected_after(small), expected_after(old)
    old_total = xr(sum(i["balance"] for i in old))
    old_before = rows[3]["n"] + rows[4]["n"]
    old_after = old_before - len(old)
    claim(old_after > 0, "some invoices remain in the two oldest buckets after the small balances go")
    return dict(rows=rows, loss=loss, total=total, share=loss / total, ar_id=ar, allowance_id=d.account("1030"),
                bad_debt_id=d.account("6170"), opening=opening, opening_loss=opening_loss, current=current[0], n_small=len(small),
                n_old=len(old), old_total=old_total, old_low=min(i["balance"] for i in old), old_high=max(i["balance"] for i in old),
                small_total=xr(sum(i["balance"] for i in small)), after_all=after_all, after_old=after_old,
                remaining=xr(loss - old_total), topup=xr(after_old - (loss - old_total)), old_before=old_before,
                old_after=old_after, gl_rows=d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (?, ?)", d.account("1030"), d.account("6170")),
                sum_rates=sum(RATES))


# --- Exercise 8.2: accounts payable --------------------------------------------------------------------------------------

@context("ch08.g2")
def g2(d, claim):
    schema(d, claim, {"PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "GrandTotal", "PurchaseOrderID"],
                      "DisbursementPayment": ["PurchaseInvoiceID", "Amount", "PaymentDate", "DisbursementID"],
                      "PurchaseOrder": ["PurchaseOrderID", "PONumber", "OrderDate", "OrderTotal", "CreatedByEmployeeID", "ApprovedByEmployeeID"],
                      "JournalEntry": ["EntryNumber", "EntryType", "Description"], "Supplier": ["SupplierID", "SupplierName"]})
    end = asof(d)
    ap = d.account("2010")
    paid = defaultdict(float)
    for pid, amount in d.q("SELECT PurchaseInvoiceID, Amount FROM DisbursementPayment WHERE PaymentDate <= ? ORDER BY DisbursementID", end):
        paid[pid] += amount
    raw = [t - paid[pid] for pid, t in d.q("SELECT PurchaseInvoiceID, GrandTotal FROM PurchaseInvoice WHERE InvoiceDate <= ?", end)]
    open_n = sum(1 for r in raw if xr(r) > 0)
    residue = sum(1 for r in raw if r > 0 and xr(r) <= 0)
    claim(residue >= 100, "without the rounding step, hundreds of fully paid invoices keep a residue of a fraction of a cent")
    sources = {r[0]: r[1] for r in d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ? GROUP BY 1", ap, end)}
    after_n, after_amount = d.q("SELECT COUNT(*), SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND PostingDate > ?", ap, end)[0]
    claim(after_n > 0 and after_amount < 0, "account 2010 already holds debits for supplier payments dated after the as-of date")
    after_open = d.one("SELECT COUNT(*) FROM DisbursementPayment p JOIN PurchaseInvoice i ON i.PurchaseInvoiceID = p.PurchaseInvoiceID "
                       "WHERE p.PaymentDate > ? AND i.InvoiceDate <= ?", end, end)
    claim(after_open == after_n, "every payment dated after the as-of date pays an invoice dated on or before it")
    emp = employees(d)
    capital = capital_invoices(d)
    recon = []
    opening = opening_entry(d)
    recon.append(dict(kind="opening", voucher=opening, amount=-d.one(
        "SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?", ap, opening)))
    for c in capital:
        po = d.q("SELECT OrderDate FROM PurchaseOrder WHERE PONumber = ?", c["po"])[0][0]
        recon.append(dict(kind="reclass", voucher=c["entry"], amount=c["amount"], invoice=c["number"], invoice_id=c["id"], po=c["po"],
                          po_date=po, po_total=c["total"], supplier=c["supplier_name"]))
    claim(len(recon) == 3, "three journal entries post to account 2010")
    approver = emp[capital[0]["approver"]]
    claim(all(c["creator"] == c["approver"] for c in capital), "the same employee created and approved both capital purchase orders")
    claim(all(c["total"] > 10 * approver["limit"] for c in capital), "each capital order is more than ten times the approver's limit")
    claim(all("invoice" in d.one("SELECT Description FROM JournalEntry WHERE EntryNumber = ?", c["entry"]).lower() for c in capital),
          "each Debt Reclass entry's description names its invoice, so TEXTAFTER can read the PurchaseInvoiceID")
    return dict(open_n=open_n, residue=residue, ap_id=ap, gl_rows=sum(sources.values()), sources=sources, after_n=after_n, after_open=after_open,
                after_amount=after_amount, recon=recon, approver=approver["name"], approver_title=approver["title"],
                approver_limit=approver["limit"], supplier=capital[0]["supplier_name"], supplier_id=capital[0]["supplier"],
                invoice_rows=d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE InvoiceDate <= ?", end))


# --- Exercise 8.3: customer credit exposure ------------------------------------------------------------------------------

@context("ch08.g3")
def g3(d, claim):
    schema(d, claim, {"Customer": ["CustomerID", "CustomerName", "CreditLimit", "PaymentTerms", "CustomerSegment"]})
    inv = open_invoices(d)
    cust = {r[0]: dict(name=r[1], limit=r[2], terms=r[3], segment=r[4]) for r in d.q(
        "SELECT CustomerID, CustomerName, CreditLimit, PaymentTerms, CustomerSegment FROM Customer")}
    bal, past, groups = defaultdict(float), defaultdict(float), {"segment": {}, "terms": {}}
    for i in inv:
        c = cust[i["customer"]]
        bal[i["customer"]] += i["balance"]
        if i["days"] > 0:
            past[i["customer"]] += i["balance"]
        for kind in groups:
            g = groups[kind].setdefault(c[kind], dict(label=c[kind], open=0.0, past=0.0, who=set()))
            g["open"] += i["balance"]
            g["who"].add(i["customer"])
            if i["days"] > 0:
                g["past"] += i["balance"]
    for kind in groups:
        for g in groups[kind].values():
            g["pct"], g["customers"] = g["past"] / g["open"], len(g["who"])
            del g["who"]
    segments = sorted(groups["segment"].values(), key=lambda g: -g["open"])
    terms = sorted(groups["terms"].values(), key=lambda g: int(g["label"].split()[-1]))
    claim([g["pct"] for g in terms] == sorted((g["pct"] for g in terms), reverse=True),
          "the share of the balance that is past due falls as the payment terms lengthen")
    total, past_total = sum(bal.values()), sum(past.values())
    claim(len(inv) / len(bal) > 3, "a customer has several open invoices on average, so summing CreditLimit multiplies the limit")
    ranked = sorted(bal, key=lambda k: -bal[k])
    claim(min(bal) != ranked[0], "the customer with the lowest CustomerID is not the one with the largest balance (a PivotTable sorts by ID at first)")
    names = len({cust[k]["name"] for k in bal})
    claim(names == len(bal) - 1, "grouping by name alone merges two customers into one row")
    over = [k for k in ranked if bal[k] > cust[k]["limit"]]
    claim(all(past[k] < 0.005 for k in over), "no customer over its limit has a past-due balance")
    claim(all(abs(bal[k] - past[k]) > 0 for k in over), "the balances over the limits are current billing")
    return dict(segments=segments, terms=terms, total=total, past_total=past_total, past_pct=past_total / total, names=names,
                customers=len(bal), n_invoices=len(inv), per_customer=len(inv) / len(bal), over_ids=over,
                over_share=sum(bal[k] for k in over) / total, first_id=min(bal), largest=ranked[0],
                lines=len(inv))


# --- Exercise 8.4: supplier concentration and timing ----------------------------------------------------------------------

@context("ch08.g4")
def g4(d, claim):
    schema(d, claim, {"DisbursementPayment": ["SupplierID", "Amount", "PaymentDate", "PurchaseInvoiceID"],
                      "PurchaseInvoice": ["PurchaseInvoiceID", "DueDate"], "Supplier": ["SupplierID", "SupplierName", "SupplierCategory"]})
    rows = d.q("SELECT p.SupplierID, p.Amount, julianday(p.PaymentDate) - julianday(pi.DueDate), substr(p.PaymentDate, 1, 4) "
               "FROM DisbursementPayment p JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate < ?",
               f"{d.N}-01-01")

    def marks(rs):
        spend = defaultdict(float)
        for r in rs:
            spend[r[0]] += r[1]
        total, running, out = sum(spend.values()), 0.0, {}
        for rank, (_, a) in enumerate(sorted(spend.items(), key=lambda kv: -kv[1]), 1):
            running += a
            for share in (0.5, 0.8, 0.9):
                if share not in out and running >= share * total:
                    out[share] = rank
        return dict(n=len(rs), suppliers=len(spend), total=total, n50=out[0.5], n80=out[0.8], n90=out[0.9])
    year = marks([r for r in rows if r[3] == str(d.C)])
    allyears = marks(rows)
    claim(allyears["n50"] > year["n50"] and allyears["n90"] > year["n90"],
          "without the year filter, more suppliers are needed to reach half and 90 percent of the spending")
    claim(all(float(r[2]).is_integer() for r in rows), "every payment is a whole number of days from its due date")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE DueDate IS NULL") == 0, "every supplier invoice has a DueDate")
    category = dict(d.q("SELECT SupplierID, SupplierCategory FROM Supplier"))
    cats = defaultdict(float)
    for sid, amount, _, y in rows:
        if y == str(d.C):
            cats[category[sid]] += amount
    ranked = sorted(cats.items(), key=lambda kv: -kv[1])
    claim(len(ranked) == 8, "the suppliers fall into eight categories")
    names = dict(d.q("SELECT SupplierID, SupplierName FROM Supplier"))
    spend = defaultdict(float)
    for r in rows:
        if r[3] == str(d.C):
            spend[names[r[0]]] += r[1]
    running, alpha50 = 0.0, 0
    for rank, name in enumerate(sorted(spend), 1):
        running += spend[name]
        if running >= 0.5 * sum(spend.values()):
            alpha50 = rank
            break
    claim(alpha50 > 2 * year["n50"], "sorted by name, the running total reaches half of the spending far later than sorted by amount")
    inv_counts = Counter(lead(x) for (x,) in d.q("SELECT GrandTotal FROM PurchaseInvoice WHERE InvoiceDate < ?", f"{d.N}-01-01"))
    inv_mad = mad(inv_counts)
    claim(conformity(inv_mad) == "close conformity", "the first digits of the supplier invoice totals conform closely")
    days_all = statistics.median(r[2] for r in rows)
    days_year = statistics.median(r[2] for r in rows if r[3] == str(d.C))
    return dict(year=year, allyears=allyears, categories=[dict(name=k, amount=v, share=v / year["total"]) for k, v in ranked],
                n_categories=len(ranked), top_share=ranked[0][1] / year["total"], second_share=ranked[1][1] / year["total"],
                median_all=days_all, median_year=days_year, n_years=len(d.years), years_word=word(len(d.years)), categories_word=word(len(ranked)), alpha50=alpha50, inv_mad=inv_mad)


# --- Exercise 8.5: purchasing and payment controls --------------------------------------------------------------------------

@context("ch08.g5")
def g5(d, claim):
    schema(d, claim, {"PurchaseOrder": ["PurchaseOrderID", "PONumber", "OrderDate", "OrderTotal", "CreatedByEmployeeID", "ApprovedByEmployeeID"],
                      "PurchaseRequisition": ["RequisitionID", "RequisitionNumber", "RequestDate", "RequestedByEmployeeID",
                                              "ApprovedByEmployeeID", "ApprovedDate", "Status", "Quantity", "EstimatedUnitCost", "ItemID"],
                      "DisbursementPayment": ["SupplierID", "Amount", "PurchaseInvoiceID", "PaymentDate", "PaymentNumber"],
                      "Employee": ["EmployeeID", "EmployeeName", "JobTitle", "MaxApprovalAmount", "TerminationDate"]})
    emp = employees(d)
    cfo_id = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Chief Financial Officer'")
    orders = d.q("SELECT PONumber, OrderDate, OrderTotal, CreatedByEmployeeID, ApprovedByEmployeeID FROM PurchaseOrder ORDER BY PurchaseOrderID")
    no_term = sum(1 for o in orders if emp[o[4]]["terminated"] is None)
    claim(no_term > 0.99 * len(orders), "almost every purchase order was approved by an employee with no termination date")
    # the model answer's classification of the flagged orders
    capital = {c["po"] for c in capital_invoices(d)}
    kinds = Counter()
    for number, ordered, total, cr, ap in orders:
        a = emp[ap]
        flags = dict(self=cr == ap, above=total > a["limit"], term=a["terminated"] is not None and a["terminated"] < ordered)
        if not any(flags.values()):
            continue
        on = tuple(k for k, v in flags.items() if v)
        if on == ("self", "above") and number in capital:
            kinds["capital"] += 1
        elif on == ("self", "above") and a["limit"] == 0:
            kinds["self_zero"] += 1
        elif on == ("above", "term") and a["limit"] == 0:
            kinds["terminated"] += 1
        elif on == ("self",) and total <= a["limit"]:
            kinds["self_within"] += 1
        elif on == ("above",) and a["limit"] > 0:
            kinds["above_only"] += 1
        else:
            kinds["other"] += 1
    claim(kinds["other"] == 0, "every flagged purchase order belongs to one of the five groups the model answer's dispositions describe")
    bands = []
    reqs = d.q("SELECT RequisitionNumber, Quantity * EstimatedUnitCost, ApprovedByEmployeeID, ApprovedDate, RequestDate, Status, RequisitionID "
               "FROM PurchaseRequisition ORDER BY RequisitionID")
    for k in range(BAND_COUNT):
        low = BAND_FROM + k * BAND_WIDTH
        bands.append(dict(low=low, high=low + BAND_WIDTH - 0.01, count=sum(1 for r in reqs if low <= r[1] < low + BAND_WIDTH)))
    claim(not any(abs(r[1] - (BAND_FROM + k * BAND_WIDTH)) < 1e-6 for r in reqs for k in range(BAND_COUNT + 1)),
          "no requisition value falls exactly on a band boundary")
    band = [r for r in reqs if BAND_EXAMINED <= r[1] < BAND_EXAMINED + BAND_WIDTH]
    unapproved = [r for r in band if r[2] is None]
    runs, current = [], [band[0]]
    for r in band[1:]:
        if r[6] == current[-1][6] + 1 and r[1] == current[-1][1]:
            current.append(r)
        else:
            runs.append(current)
            current = [r]
    runs = [run for run in runs + [current] if len(run) > 1]
    claim(len(runs) >= 1 and all(all(r[2] is None for r in run[:-1]) and run[-1][2] == cfo_id and
                                 date.fromisoformat(run[-1][3][:10]).toordinal() - date.fromisoformat(run[-1][4][:10]).toordinal() == 1
                                 for run in runs),
          "in each run of identical consecutive requisitions only the last has an approver, the chief financial officer, the day after the request")
    invoices = d.q("SELECT PurchaseInvoiceID, GrandTotal, ApprovedByEmployeeID FROM PurchaseInvoice")
    other = [r for r in invoices if r[2] != cfo_id]
    pays = d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PaymentDate < ?", f"{d.N}-01-01")
    return dict(orders=len(orders), no_term=no_term, kinds=dict(kinds), bands=bands, n_reqs=len(reqs), n_band=len(band),
                n_band_unapproved=len(unapproved), n_runs=len(runs), n_runs_word=word(len(runs)), run_len=len(runs[0]), other_total=sum(r[1] for r in other), n_other=len(other),
                payments=pays, n_bands=BAND_COUNT, first_band=BAND_FROM, band_examined=BAND_EXAMINED, band_edge=BAND_EXAMINED + BAND_WIDTH)


# --- Exercise 8.6: pricing controls --------------------------------------------------------------------------------------------

@context("ch08.g6")
def g6(d, claim):
    schema(d, claim, {"PromotionProgram": ["PromotionID", "PromotionCode", "PromotionName", "DiscountPct", "EffectiveStartDate",
                                           "EffectiveEndDate", "ApprovedByEmployeeID", "ApprovedDate"],
                      "PriceOverrideApproval": ["PriceOverrideApprovalID", "SalesOrderLineID", "Status", "ReferenceUnitPrice", "ApprovedUnitPrice"],
                      "PriceList": ["PriceListID", "PriceListName", "ScopeType", "CustomerID", "CustomerSegment", "EffectiveStartDate",
                                    "EffectiveEndDate", "Status"],
                      "PriceListLine": ["PriceListLineID", "PriceListID", "ItemID", "UnitPrice"],
                      "SalesOrderLine": ["SalesOrderLineID", "SalesOrderID", "ItemID", "PriceListLineID", "PricingMethod", "UnitPrice", "Discount", "LineTotal"],
                      "SalesInvoiceLine": ["SalesOrderLineID", "SalesInvoiceID", "Quantity", "UnitPrice", "Discount", "PromotionID",
                                           "PricingMethod", "PriceOverrideApprovalID"]})
    no_list = d.one("SELECT COUNT(*) FROM SalesOrderLine WHERE PriceListLineID IS NULL")
    claim(no_list > 0, "some order lines have no price list line (overrides and the Base List design services), so their list end date is blank")
    pending = []
    for oid, sol, ref, approved in d.q("SELECT PriceOverrideApprovalID, SalesOrderLineID, ReferenceUnitPrice, ApprovedUnitPrice FROM "
                                       "PriceOverrideApproval WHERE Status = 'Pending' ORDER BY PriceOverrideApprovalID"):
        for number, qty, price in d.q("SELECT si.InvoiceNumber, l.Quantity, l.UnitPrice FROM SalesInvoiceLine l JOIN SalesInvoice si "
                                      "ON si.SalesInvoiceID = l.SalesInvoiceID WHERE l.SalesOrderLineID = ? ORDER BY si.InvoiceNumber", sol):
            pending.append(dict(id=oid, line=sol, invoice=number, qty=qty, price=price, reference=ref, approved=approved,
                                below=(ref - price) * qty))
    claim(all(p["price"] == p["approved"] for p in pending), "every invoice line of a pending request is billed at its ApprovedUnitPrice")
    claim(all(p["price"] < p["reference"] for p in pending), "every such line is billed below the reference price")
    lists = d.q("SELECT PriceListID, EffectiveStartDate, EffectiveEndDate FROM PriceList WHERE Status = 'Expired' OR EffectiveEndDate < EffectiveStartDate")
    backwards = [r[0] for r in lists if r[2] < r[1]]
    claim(len(backwards) == 1, "one price list ends before it starts")
    promo_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL")
    boundary = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                     "JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                     "WHERE p.EffectiveEndDate > p.EffectiveStartDate AND (o.OrderDate = p.EffectiveStartDate OR o.OrderDate = p.EffectiveEndDate)")
    claim(boundary > 0, "some lines of the other promotions were ordered exactly on a start or end date, so a strict inequality would count them outside")
    return dict(no_list=no_list, pending=pending, n_pending=len({p["id"] for p in pending}), flagged_lists=[r[0] for r in lists],
                backwards=backwards, promo_lines=promo_lines, boundary=boundary, order_lines=d.one("SELECT COUNT(*) FROM SalesOrderLine"),
                invoice_lines=d.one("SELECT COUNT(*) FROM SalesInvoiceLine"))
