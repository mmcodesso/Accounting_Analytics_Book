"""Chapter 8 figures."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import date
from functools import lru_cache

import excel as xl
from check_figures import text_width
from data import one, q, require_columns
from drawio import (BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, ROW_H, RULE, SMALL, WHITE, Diagram,
                    esc)

END = "2026-12-31"   # the end of the period under review: fiscal 2024 through fiscal 2026
NBSP = "&nbsp;&nbsp;&nbsp;"
# Nigrini's first-digit MAD ranges: (upper limit, conclusion).
MAD_RANGES = [(0.006, "Close conformity"), (0.012, "Acceptable conformity"),
              (0.015, "Marginally acceptable conformity"), (math.inf, "Nonconformity")]
BUCKETS = [(-9999, "Current"), (1, "1-30 days"), (31, "31-60 days"), (61, "61-90 days"),
           (91, "Over 90 days")]


# -- data -------------------------------------------------------------------------------

def lead_digit(amount: float) -> int:
    """The first significant digit, as =--LEFT(TEXT(x,"0.00000000E+00"),1) returns it."""
    return int(f"{amount:.8E}"[0])


def conformity(mad: float) -> str:
    return next(label for limit, label in MAD_RANGES if mad < limit)


@lru_cache(maxsize=1)
def payments() -> list[dict]:
    """Tutorial 8.1's Payments query: supplier payments through fiscal 2026 with their invoices."""
    require_columns("DisbursementPayment", ["PaymentNumber", "PaymentDate", "SupplierID",
                                            "PurchaseInvoiceID", "Amount"])
    rows = [dict(number=n, date=d, supplier=s, invoice=i, amount=a, total=g, name=name)
            for n, d, s, i, a, g, name in q(
                "SELECT d.PaymentNumber, d.PaymentDate, d.SupplierID, d.PurchaseInvoiceID, d.Amount, "
                "pi.GrandTotal, s.SupplierName FROM DisbursementPayment d "
                "JOIN PurchaseInvoice pi USING (PurchaseInvoiceID) JOIN Supplier s ON s.SupplierID = d.SupplierID "
                "WHERE d.PaymentDate <= ?", END)]
    # The population reconciles to the cash credits the payments posted (account 1010, AccountID 2).
    n, credits = one("SELECT COUNT(*), SUM(g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                     "WHERE g.SourceDocumentType = 'DisbursementPayment' AND a.AccountNumber = 1010 "
                     "AND g.PostingDate <= ?", END)
    assert n == len(rows) and abs(credits - sum(r["amount"] for r in rows)) < 0.005
    assert all(r["amount"] <= r["total"] for r in rows), "no payment exceeds its invoice"
    return rows


def benford(amounts: list[float]) -> dict:
    counts = Counter(lead_digit(a) for a in amounts)
    n = sum(counts.values())
    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    actual = {d: counts[d] / n for d in range(1, 10)}
    mad = sum(abs(actual[d] - expected[d]) for d in range(1, 10)) / 9
    return dict(n=n, counts=counts, expected=expected, actual=actual, mad=mad)


@lru_cache(maxsize=1)
def aging() -> dict:
    """Tutorial 8.2: open sales invoices at the end of fiscal 2026, aged by due date."""
    require_columns("CashReceiptApplication", ["SalesInvoiceID", "AppliedAmount", "ApplicationDate"])
    require_columns("CreditMemo", ["OriginalSalesInvoiceID", "GrandTotal", "CreditMemoDate"])
    applied, credited = defaultdict(float), defaultdict(float)
    for sid, amount in q("SELECT SalesInvoiceID, AppliedAmount FROM CashReceiptApplication "
                         "WHERE ApplicationDate <= ?", END):
        applied[sid] += amount
    for sid, amount in q("SELECT OriginalSalesInvoiceID, GrandTotal FROM CreditMemo "
                         "WHERE CreditMemoDate <= ?", END):
        credited[sid] += amount
    as_of = date.fromisoformat(END)
    out = defaultdict(lambda: [0, 0.0])
    for sid, due, total in q("SELECT SalesInvoiceID, DueDate, GrandTotal FROM SalesInvoice "
                             "WHERE InvoiceDate <= ?", END):
        balance = xl.xround(total - applied[sid] - credited[sid])
        if balance <= 0:
            continue
        days = (as_of - date.fromisoformat(due)).days
        bucket = [label for low, label in BUCKETS if days >= low][-1]
        out[bucket][0] += 1
        out[bucket][1] += balance
    ledger = dict(q("SELECT SourceDocumentType, SUM(Debit - Credit) FROM GLEntry "
                    "WHERE AccountID = 3 AND PostingDate <= ? GROUP BY 1", END))
    counts = dict(q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry "
                    "WHERE AccountID = 3 AND PostingDate <= ? GROUP BY 1", END))
    assert one("SELECT AccountNumber FROM Account WHERE AccountID = 3")[0] == 1020
    other = one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (4, 74)")[0]
    assert other == 0, "the allowance (1030) and bad-debt (6170) accounts have no postings"
    subledger = sum(v[1] for v in out.values())
    gl = sum(ledger.values())
    assert abs(gl - subledger - 380_000) < 0.005, gl - subledger
    return dict(buckets=out, ledger=ledger, counts=counts, subledger=subledger, gl=gl)


@lru_cache(maxsize=1)
def journal_entries() -> list[dict]:
    """Tutorial 8.3's JournalEntries query with its five flags and the risk score."""
    require_columns("JournalEntry", ["EntryNumber", "PostingDate", "EntryType", "TotalAmount",
                                     "CreatedByEmployeeID", "CreatedDate", "ApprovedByEmployeeID"])
    require_columns("Employee", ["EmployeeID", "MaxApprovalAmount"])
    limit = dict(q("SELECT EmployeeID, MaxApprovalAmount FROM Employee"))
    rows = []
    for number, posted, kind, total, creator, created, approver in q(
            "SELECT EntryNumber, PostingDate, EntryType, TotalAmount, CreatedByEmployeeID, CreatedDate, "
            "ApprovedByEmployeeID FROM JournalEntry ORDER BY EntryNumber"):
        flags = dict(Weekend=date.fromisoformat(created[:10]).weekday() >= 5,
                     Backdated=created[:10] > posted,
                     SelfApproved=creator == approver,
                     AboveLimit=total > limit[approver],
                     RoundAmount=abs(total % 1000) < 0.005)
        rows.append(dict(number=number, kind=kind, total=total, flags=flags,
                         score=sum(flags.values())))
    scores = Counter(r["score"] for r in rows)
    assert scores[4] == 1 and max(scores) == 4, scores
    top = max(rows, key=lambda r: r["score"])
    assert top["number"] == "JE-2024-000001"
    return rows


# -- drawing helpers --------------------------------------------------------------------

def seg(d: Diagram, x1: float, y1: float, x2: float, y2: float, color: str, width: float = 2) -> None:
    """A straight line between two points."""
    d._track(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    style = f"endArrow=none;startArrow=none;html=1;strokeColor={color};strokeWidth={width:g};"
    d.cells.append(
        f'<mxCell id="{d._id("s")}" value="" style="{style}" edge="1" parent="1">'
        f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1:g}" y="{y1:g}" as="sourcePoint"/>'
        f'<mxPoint x="{x2:g}" y="{y2:g}" as="targetPoint"/></mxGeometry></mxCell>')


def dot(d: Diagram, x: float, y: float, color: str, size: float = 8) -> None:
    d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={color};", x - size / 2, y - size / 2,
             size, size)


def digit_chart(d: Diagram, x: float, y: float, w: float, h: float, b: dict, top: float = 0.35,
                step: float = 0.05) -> None:
    """Actual first-digit shares as bars, Benford's expected shares as a line with dots."""
    left = x + 48
    y_of = lambda v: y + (top - v) * h / top
    v = 0.0
    while v <= top + 1e-9:
        d.box("", left, y_of(v), x + w - left, 1, fill=RULE, stroke=RULE, rounded=False)
        d.text(f"{100 * v:.0f}%", x, y_of(v) - 11, 42, 22, size=SMALL, align="right", valign="middle")
        v += step
    slot = (x + w - left) / 9
    bar = slot * 0.56
    centers = []
    for digit in range(1, 10):
        cx = left + (digit - 0.5) * slot
        centers.append(cx)
        share = b["actual"][digit]
        d.box("", cx - bar / 2, y_of(share), bar, y_of(0) - y_of(share), fill=BLUE, stroke=BLUE,
              rounded=False)
        d.text(str(digit), cx - 15, y + h + 4, 30, 20, size=SMALL, align="center")
    points = [(cx, y_of(b["expected"][dg])) for cx, dg in zip(centers, range(1, 10))]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        seg(d, x1, y1, x2, y2, CORAL, 2.5)
    for px, py in points:
        dot(d, px, py, CORAL)


def chart_legend(d: Diagram, x: float, y: float) -> None:
    d.box("", x, y + 5, 16, 14, fill=BLUE, stroke=BLUE, rounded=False)
    d.text("Actual share of payments", x + 22, y, 220, 24, size=SMALL, valign="middle")
    seg(d, x + 260, y + 12, x + 296, y + 12, CORAL, 2.5)
    dot(d, x + 278, y + 12, CORAL)
    d.text("Expected by Benford's Law", x + 304, y, 220, 24, size=SMALL, valign="middle")


def header_style(header_rows: set[int], total_rows: set[int] = frozenset(),
                 left_cols: set[int] = frozenset({0})):
    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c in left_cols else {}
        if r in header_rows:
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>")
        elif r in total_rows:
            out.update(label=f"<b>{esc(value)}</b>")
        return out
    return style


def note(d: Diagram, y: float, text: str, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


# -- figures ----------------------------------------------------------------------------

def fig_08_01() -> Diagram:
    d = Diagram("An Audit Analytics Workflow")
    steps = [("1. Objective", "State the risk or assertion the test addresses and what an exception "
                               "would look like."),
             ("2. Population", "Import the data and agree its count and total to the ledger before "
                               "you test it."),
             ("3. Tests", "Stratify, profile, and flag the records that meet each criterion."),
             ("4. Exceptions", "Examine each flagged record against its source documents."),
             ("5. Disposition", "Classify each exception: expected, with evidence; follow up; or "
                                "misstatement."),
             ("6. Workpaper", "Record the source, steps, results, and conclusion for a reviewer.")]
    w, gap, top, body_h = 128, (860 - 6 * 128) / 5, 10, 150
    ids = []
    for i, (title, text) in enumerate(steps):
        x = i * (w + gap)
        d.header_box(esc(title), x, top, w, 34, fill=BLUE, size=13)
        ids.append(d.box(esc(text), x, top + 34, w, body_h, fill=WHITE, stroke=RULE, size=13,
                         valign="top"))
    for a, b in zip(ids, ids[1:]):
        d.arrow(a, b, color=GRAY, exit=(1, 0.3), entry=(0, 0.3))
    # Refining a test that produces mostly false positives sends you back to step 3.
    bottom = top + 34 + body_h
    x3, x4 = 2 * (w + gap) + w / 2, 3 * (w + gap) + w / 2
    d.arrow(ids[3], ids[2], color=GRAY, dashed=True, exit=(0.5, 1), entry=(0.5, 1),
            points=[(x4, bottom + 34), (x3, bottom + 34)])
    d.text("Refine the test and rerun it when most exceptions are false positives", x3 - 40,
           bottom + 40, x4 - x3 + 80, 40, size=SMALL, align="center")
    note(d, bottom + 90, "Solid arrows show the order of the work; the dashed arrow shows the loop "
         "back from the exceptions to the tests.")
    return d


def fig_08_02() -> Diagram:
    d = Diagram("Supplier Payments Stratified by Amount")
    p = payments()
    amounts = [r["amount"] for r in p]
    bounds = [0, 1000, 10000, 50000, 100000]
    upper = bounds[1:] + [xl.xround(max(amounts) + 0.01)]
    total_n, total_v = len(amounts), sum(amounts)
    body = [("1", ["Lower bound", "Upper bound", "Payments", "Share of payments", "Value",
                   "Share of value"])]
    strata = []
    for low, high in zip(bounds, upper):
        s = [a for a in amounts if low <= a < high]
        strata.append((len(s), sum(s)))
        body.append((str(len(body) + 1), [xl.num(low), xl.num(high), f"{len(s):,}",
                                          f"{100 * len(s) / total_n:.2f}%", xl.num(sum(s)),
                                          f"{100 * sum(s) / total_v:.2f}%"]))
    assert sum(n for n, _ in strata) == total_n
    assert strata[0][0] / total_n > 0.7 and strata[0][1] / total_v < 0.25
    assert strata[3][0] + strata[4][0] == 4
    body.append(("7", ["Total", "", f"{total_n:,}", "100.00%", xl.num(total_v), "100.00%"]))
    xl.formula_bar(d, 0, 0, 860, "C2", '=COUNTIFS(Payments[Amount],">="&A2,Payments[Amount],"<"&B2)')
    widths = [36, 124, 124, 110, 150, 170, 146]
    geo = xl.sheet(d, 0, 40, ["A", "B", "C", "D", "E", "F"], widths, body,
                   header_style({0}, {6}, set()))
    x0, y0, _, _ = geo[(4, 0)]
    xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H * 2)
    bottom = 40 + 22 + ROW_H * len(body)
    note(d, bottom + 8, "Supplier payments dated in fiscal 2024 through 2026. Each upper bound is the "
         "next lower bound, and B6 is =MAX(Payments[Amount])+0.01, so the top stratum includes the "
         "largest payment. Outlined: the two top strata, which hold only four payments.")
    return d


def fig_08_03() -> Diagram:
    d = Diagram("A First-Digit Test of Supplier Payments")
    b = benford([r["amount"] for r in payments()])
    assert conformity(b["mad"]) == "Marginally acceptable conformity", b["mad"]
    body = [("1", ["Digit", "Expected", "Payments", "Actual", "Difference"])]
    for dg in range(1, 10):
        body.append((str(dg + 1), [str(dg), f"{100 * b['expected'][dg]:.2f}%", f"{b['counts'][dg]:,}",
                                   f"{100 * b['actual'][dg]:.2f}%",
                                   f"{100 * abs(b['actual'][dg] - b['expected'][dg]):.2f}%"]))
    body.append(("11", ["Total", "100.00%", f"{b['n']:,}", "100.00%", ""]))
    body.append(("12", ["MAD", "", "", "", f"{b['mad']:.5f}"]))
    xl.formula_bar(d, 0, 0, 860, "C2", "=COUNTIF(Payments[LeadDigit],A2)")
    widths = [36, 90, 120, 120, 120, 120]
    geo = xl.sheet(d, 0, 40, ["A", "B", "C", "D", "E"], widths, body,
                   header_style({0}, {10, 11}, set()))
    xl.emphasis(d, *geo[(11, 4)])
    xl.select(d, *geo[(1, 2)])
    chart_top = 40 + 22 + ROW_H * len(body) + 24
    digit_chart(d, 0, chart_top, 860, 240, b)
    chart_legend(d, 48, chart_top + 270)
    note(d, chart_top + 300, "Supplier payments dated in fiscal 2024 through 2026. Actual is each digit's "
         "count divided by the total; Difference is the absolute difference from Expected, formatted as a "
         "percentage; MAD is the average of the nine differences. Outlined: the MAD.")
    return d


def fig_08_04() -> Diagram:
    d = Diagram("First Digits of Full and Partial Payments")
    p = payments()
    full = benford([r["amount"] for r in p if not r["amount"] < r["total"]])
    part = benford([r["amount"] for r in p if r["amount"] < r["total"]])
    assert conformity(full["mad"]) == "Acceptable conformity", full["mad"]
    assert conformity(part["mad"]) == "Nonconformity", part["mad"]
    assert min(r["total"] for r in p if r["amount"] < r["total"]) >= 1000
    for i, (label, b) in enumerate([("Full payments: Partial is FALSE", full),
                                    ("Partial payments: Partial is TRUE", part)]):
        x = i * 440
        d.text(f"<b>{esc(label)}</b>", x, 0, 420, 22, size=13)
        d.text(esc(f"MAD {b['mad']:.5f}: {conformity(b['mad']).lower()}"), x, 22, 420, 22, size=SMALL)
        digit_chart(d, x, 60, 420, 250, b)
    chart_legend(d, 0, 344)
    note(d, 376, "Supplier payments dated in fiscal 2024 through 2026, split by the Partial column "
         "(a payment smaller than its invoice). Every partial payment belongs to an invoice of $1,000 or "
         "more, and most of those invoices are between $1,000 and $2,000, so their parts start with "
         "digits from 3 to 9 far more often than Benford's Law expects.", h=56)
    return d


def fig_08_05() -> Diagram:
    d = Diagram("The Receivables Aging Reconciled to the Ledger")
    a = aging()
    body = [("1", ["As-of date", "2026-12-31", "", ""]),
            ("2", ["", "", "", ""]),
            ("3", ["Bucket", "Invoices", "Open balance", "Share of balance"])]
    for _, label in BUCKETS:
        n, v = a["buckets"][label]
        body.append((str(len(body) + 1), [label, f"{n:,}", xl.num(v), f"{100 * v / a['subledger']:.2f}%"]))
    body.append(("9", ["Total", f"{sum(v[0] for v in a['buckets'].values()):,}", xl.num(a["subledger"]),
                       "100.00%"]))
    body += [("10", ["", "", "", ""]),
             ("11", ["Open invoices (sub-ledger)", "", xl.num(a["subledger"]), ""]),
             ("12", ["Account 1020 (AccountID 3)", "", xl.num(a["gl"]), ""]),
             ("13", ["Difference", "", xl.num(a["gl"] - a["subledger"]), ""])]
    assert a["buckets"]["Current"][1] / a["subledger"] > 0.8

    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c == 0 else {}
        if r == 0 and c == 1:
            out.update(color=BLUE, label=f"<b>{esc(value)}</b>", align="right")
        if r == 2:
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>")
        elif r in (8, 12):
            out.update(label=f"<b>{esc(value)}</b>")
        return out

    xl.formula_bar(d, 0, 0, 860, "C12", "=SUMIFS(LedgerAR[Amount],LedgerAR[AccountID],3)")
    widths = [36, 250, 120, 170, 170]
    geo = xl.sheet(d, 0, 40, ["A", "B", "C", "D"], widths, body, style)
    xl.select(d, *geo[(11, 2)])
    x0, y0, _, _ = geo[(12, 0)]
    xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H)
    bottom = 40 + 22 + ROW_H * len(body)
    note(d, bottom + 8, "B1 is named AsOfDate; blue marks the input. The buckets count days past the due "
         "date at the as-of date. Outlined: the difference between the ledger and the open invoices.")
    return d


def fig_08_06() -> Diagram:
    d = Diagram("Accounts Receivable in the Ledger by Source Document")
    a = aging()
    order = ["CashReceiptApplication", "CreditMemo", "JournalEntry", "SalesInvoice"]
    assert set(a["ledger"]) == set(order), a["ledger"]
    assert a["counts"]["JournalEntry"] == 1
    body = [("3", ["Row Labels ▾", "Count of GLEntryID", "Sum of Amount"]),
            ("4", ["3", f"{sum(a['counts'].values()):,}", xl.num(a["gl"])])]
    for kind in order:
        body.append((str(len(body) + 3), [kind, f"{a['counts'][kind]:,}", xl.num(a["ledger"][kind])]))
    body.append((str(len(body) + 3), ["Grand Total", f"{sum(a['counts'].values()):,}", xl.num(a["gl"])]))
    je_row = 2 + order.index("JournalEntry")

    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c == 0 else {}
        if r == 0:
            out.update(fill=BLUE_TINT, label=f"<b>{esc(value)}</b>", align="left")
        elif r in (1, len(body) - 1):
            out.update(label=f"<b>{esc(value)}</b>", fill=BLUE_TINT if r == len(body) - 1 else WHITE)
        elif c == 0:
            out.update(label=f"{NBSP}{esc(value)}")
        return out

    widths = [36, 260, 170, 170]
    geo = xl.sheet(d, 0, 0, ["A", "B", "C"], widths, body, style)
    xl.emphasis(d, *geo[(je_row, 2)])
    y = 22 + ROW_H * len(body) + 24
    d.text("<b>Show Details for the outlined value, on a new worksheet</b>", 0, y, 860, 22, size=SMALL)
    gl_id, posted, voucher, desc, debit = one(
        "SELECT GLEntryID, PostingDate, VoucherNumber, Description, Debit FROM GLEntry "
        "WHERE AccountID = 3 AND SourceDocumentType = 'JournalEntry'")
    assert voucher == "JE-2024-000001" and abs(debit - 380_000) < 0.005
    # The LedgerAR query keeps these columns, in this order, and adds Amount; Show Details lists them
    # all, and the mock shows five of them under their own column letters.
    kept = ["GLEntryID", "PostingDate", "AccountID", "VoucherNumber", "SourceDocumentType",
            "Description", "Debit", "Credit", "Amount"]
    require_columns("GLEntry", kept[:-1])
    heads = ["GLEntryID", "PostingDate", "VoucherNumber", "Description", "Amount"]
    letters = [chr(65 + kept.index(h)) for h in heads]
    widths2 = [36, 100, 110, 140, 320, 120]
    xl.table_view(d, 0, y + 24, letters, widths2, heads,
                  [("2", [str(gl_id), posted, voucher, desc, xl.num(debit)])])
    bottom = y + 24 + 22 + ROW_H * 2
    note(d, bottom + 8, "The PivotTable has AccountID and SourceDocumentType in the Rows area. The "
         "LedgerAR query also kept AccountIDs 4 and 74, accounts 1030 and 6170, but no rows exist for "
         "them. On the detail sheet, columns C, E, G, and H are hidden.")
    return d


def fig_08_07() -> Diagram:
    d = Diagram("Journal Entries Sorted by Risk Score")
    rows = sorted(journal_entries(), key=lambda r: (-r["score"], r["number"]))
    shown = [r for r in rows if r["score"] >= 2]
    assert len(shown) == 8, len(shown)
    names = ["Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"]
    heads = ["EntryNumber", "EntryType", "TotalAmount", *names, "RiskScore"]
    body = [(str(i + 2), [r["number"], r["kind"], xl.num(r["total"]),
                          *("TRUE" if r["flags"][n] else "FALSE" for n in names), str(r["score"])])
            for i, r in enumerate(shown)]
    body.append((str(len(body) + 2), ["...", "", "", "", "", "", "", "", ""]))

    def extra(r: int, c: int, value: str) -> dict:
        if value == "TRUE":
            return dict(color=CORAL, label="<b>TRUE</b>", align="center")
        if value == "FALSE":
            return dict(align="center", color=GRAY)
        if c == 8:
            return dict(label=f"<b>{esc(value)}</b>", align="center")
        return {}

    xl.formula_bar(d, 0, 0, 860, "I2", "=[@Weekend]+[@Backdated]+[@SelfApproved]+[@AboveLimit]+[@RoundAmount]")
    widths = [32, 108, 144, 104, 64, 74, 92, 80, 92, 70]
    geo = xl.table_view(d, 0, 40, [chr(65 + i) for i in range(9)], widths, heads, body, extra=extra)
    xl.emphasis(d, *geo[(1, 0)][:2], sum(widths[1:]), ROW_H)
    bottom = 40 + 22 + ROW_H * (len(body) + 1)
    note(d, bottom + 8, "The JournalEntries Table sorted by RiskScore from largest to smallest, with the "
         "entries that score 2 or more; other columns are hidden. Outlined: the only entry with four "
         "flags, the opening balance entry.")
    return d


def fig_08_08() -> Diagram:
    d = Diagram("The Ledger Lines of the Opening Balance Entry")
    lines = q("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit FROM GLEntry g "
              "JOIN Account a USING (AccountID) WHERE g.VoucherNumber = 'JE-2024-000001' "
              "AND g.SourceDocumentType = 'JournalEntry' ORDER BY g.GLEntryID")
    assert len(lines) == 18 and abs(sum(r[2] for r in lines) - sum(r[3] for r in lines)) < 0.005
    body = [("1", ["Entry number", "JE-2024-000001", "", ""]),
            ("2", ["", "", "", ""]),
            ("3", ["AccountNumber", "AccountName", "Debit", "Credit"])]
    for number, name, debit, credit in lines:
        body.append((str(len(body) + 1), [str(number), name, xl.num(debit), xl.num(credit)]))
    ar_row = next(i for i, (_, v) in enumerate(body) if v[0] == "1020")

    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c == 1 or r in (0, 2) else {}
        if r == 0 and c == 1:
            out.update(color=BLUE, label=f"<b>{esc(value)}</b>")
        if r == 2:
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>")
        return out

    xl.formula_bar(d, 0, 0, 860, "A4", "=FILTER(JournalLines[[AccountNumber]:[Credit]],"
                   "JournalLines[VoucherNumber]=B1)")
    widths = [36, 124, 380, 140, 140]
    geo = xl.sheet(d, 0, 40, ["A", "B", "C", "D"], widths, body, style)
    xl.select(d, *geo[(3, 0)])
    x0, y0, _, _ = geo[(ar_row, 0)]
    xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H)
    bottom = 40 + 22 + ROW_H * len(body)
    note(d, bottom + 8, "The formula in A4 spills the eighteen ledger lines of the entry typed in B1. "
         "Outlined: the accounts receivable line, the difference found in Tutorial 8.2.")
    return d


def fig_08_09() -> Diagram:
    d = Diagram("A Workpaper for the Journal Entry Tests")
    rows = journal_entries()
    n = len(rows)
    scores = Counter(r["score"] for r in rows)
    flagged = n - scores[0]
    years = one("SELECT MIN(substr(PostingDate, 1, 4)), MAX(substr(PostingDate, 1, 4)) FROM JournalEntry")
    assert years == ("2024", "2026")
    je_total, gl_debits = one("SELECT (SELECT SUM(TotalAmount) FROM JournalEntry), (SELECT SUM(Debit) "
                              "FROM GLEntry WHERE SourceDocumentType = 'JournalEntry')")
    assert abs(je_total - gl_debits) < 0.01
    entries = [
        ("Objective", "Identify journal entries with characteristics of management override (AS 2401) "
                      "for follow-up."),
        ("Source", f"T2_JournalEntry and T74_Employee in CharlesRiver.xlsx; all {n:,} entries posted in "
                   "fiscal 2024 through 2026."),
        ("Population check", f"{n:,} entries; their TotalAmount agrees with the debits of the ledger's "
                             "JournalEntry lines."),
        ("Procedure", "Entries by creator and type; five flags on each entry (weekend creation, created after "
                      "the posting date, same creator and approver, above the approver's limit, round "
                      "thousands); RiskScore is their sum."),
        ("Parameters", "Weekend: WEEKDAY(CreatedDate,2)>5. Limit: Employee MaxApprovalAmount of the "
                       "approver. Round: MOD(TotalAmount,1000)=0."),
        ("Results", f"{flagged} entries flagged: {scores[1]} with one flag, {scores[2]} with two, and "
                    f"{scores[4]} with four."),
        ("Exceptions and disposition", "Expected, with evidence: weekend depreciation at month-ends, "
                                       "year-end closes (no approval limit covers them). Follow up: the "
                                       "opening entry, the backdated entries, the self-approved entries, and "
                                       "the two debt reclasses. Details on the Dispositions worksheet."),
        ("Conclusion", "The approval of opening and recurring entries needs follow-up before a conclusion "
                       "on the control can be reached."),
        ("Prepared by", "Your name and date"),
        ("Reviewed by", "Reviewer's name and date"),
    ]
    x_label, w_label, w_text = 0, 200, 660
    y = 0
    d.box("<b>Workpaper</b>", x_label, y, w_label, 28, fill=GRAY, stroke=GRAY, color=WHITE,
          size=SMALL, align="left", rounded=False)
    d.box("<b>Journal entry tests, fiscal 2024 to 2026</b>", w_label, y, w_text, 28, fill=GRAY,
          stroke=GRAY, color=WHITE, size=SMALL, align="left", rounded=False)
    y += 28
    for i, (label, text) in enumerate(entries):
        lines = max(1, math.ceil(text_width(esc(text), SMALL, False) / (w_text - 14)))
        h = 8 + 17 * lines
        fill = WHITE if i % 2 == 0 else GRAY_TINT
        d.box(f"<b>{esc(label)}</b>", x_label, y, w_label, h, fill=fill, stroke=RULE, size=SMALL,
              align="left", valign="top", rounded=False)
        d.box(esc(text), w_label, y, w_text, h, fill=fill, stroke=RULE, size=SMALL, align="left",
              valign="top", rounded=False)
        y += h
    note(d, y + 8, "The WP Journals worksheet of AuditAnalytics.xlsx, with the labels in column A and "
         "the entries in column B, formatted with Wrap Text.")
    return d


FIGURES = {
    "fig-08-01-audit-analytics-workflow": fig_08_01,
    "fig-08-02-payment-strata": fig_08_02,
    "fig-08-03-benford-all-payments": fig_08_03,
    "fig-08-04-benford-by-payment-type": fig_08_04,
    "fig-08-05-ar-aging-reconciliation": fig_08_05,
    "fig-08-06-ar-ledger-by-source": fig_08_06,
    "fig-08-07-journal-entry-flags": fig_08_07,
    "fig-08-08-journal-entry-drilldown": fig_08_08,
    "fig-08-09-audit-workpaper": fig_08_09,
}
