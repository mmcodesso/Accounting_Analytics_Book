"""Chapter 8 Exercises - Solutions.xlsx: the solutions to the exercises of Chapter 8.

The workbook is a copy of AuditAnalytics.xlsx at the end of Tutorial 8.3 (the "copy ... made after you finish this
chapter's tutorials" the exercises ask for). Each function applies one exercise: its queries (with the Power Query
Editor's step names), its worksheets, formulas, and PivotTables, and a model answer for each requirement that asks
for an explanation, a judgment, or a memo. Its checks compare live formulas with values computed here from
CharlesRiver.sqlite (read-only), independently of Excel; they agree with the instructor notes (facts/notes/ch08.py).

What the builder decides where the text leaves a choice (the workbook says so where a reader would look):
  - The Solution Notes worksheet moves to the end of the workbook (the copy has it after the Tutorial 8.1 sheets, and
    the copy has no slicers), so the exercise worksheets follow the tutorial worksheets.
  - Queries the text does not name get these names: PurchaseOrders (Exercise 8.2, T33_PurchaseOrder with the
    creator's and approver's names from the Employees query of Tutorial 8.3), POApprovals and Requisitions
    (Exercise 8.5), PendingOverrides, PriceLists, PriceListLines, and OrderLines (Exercise 8.6). Approvers is
    loaded to its own worksheet, so the requisition list can look up names in it; the queries that only feed others
    (PaidByInvoice, InvoiceHeaders, Orders) are connection-only. Each loaded worksheet is named after its query.
  - LedgerAP gets an Amount column (Credit - Debit, the sign of a liability) for its PivotTable.
  - Exercise 8.4 adds a FiscalYear column (=YEAR([@PaymentDate])) to the Payments Table, the page filter of its
    PivotTables and the year of its timing formulas.
  - Exercise 8.5's flags are calculated columns of POApprovals, as Tutorial 8.3's are; the flagged orders are pasted
    as values with their dispositions, as Tutorial 8.3 Step 5 does.
  - InvoiceHeaders corrects FreightAmount and OrderLines Discount to Decimal Number in Changed Type, as Exercise 8.6
    tells readers for Discount in InvoiceLines (Power Query detects all three as whole numbers from the first rows).
"""

from __future__ import annotations

import math
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import cached_property
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import db_uri  # noqa: E402
from xlbuild import audit, notes, pq, xl  # noqa: E402
from xlbuild.solutions import COUNT, MONEY, PCT, ExerciseBuild  # noqa: E402

DATE = "yyyy-mm-dd"
AR, ALLOWANCE, AP, BAD_DEBT = 3, 4, 22, 74                       # AccountIDs (asserted below)
LOSS_RATES = {"Current": 0.005, "1-30 days": 0.02, "31-60 days": 0.05, "61-90 days": 0.15, "Over 90 days": 0.40}
SMALL = 10                                                        # Exercise 8.1 (3): balances under $10
BAND_FROM, BAND_WIDTH, BAND_COUNT, BAND_EXAMINED = 4800, 50, 8, 4950   # Exercise 8.5 (4)
CFO = "Chief Financial Officer"
XL_MAX, XL_PERCENT_RUNNING_TOTAL, XL_TABULAR = -4136, 13, 1
MA = "Model answer"


# --- helpers ---------------------------------------------------------------------------------------------------------

def xr(x: float, places: int = 2) -> float:
    """Excel's ROUND: half away from zero."""
    return float(Decimal(repr(round(x, 9))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


def word(n: int, capital: bool = False) -> str:
    """A small count in words, as the book writes it."""
    text = WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"
    return text.capitalize() if capital else text


def series(items) -> str:
    """Items as a list in prose: "1", "1 and 4", "1, 4, and 7"."""
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else " and ".join(items) if len(items) == 2 else \
        ", ".join(items[:-1]) + ", and " + items[-1]


def money(x: float) -> str:
    return f"-${-x:,.2f}" if x < 0 else f"${x:,.2f}"


def before(b: ExerciseBuild) -> str:
    return f"#datetime({b.year + 1}, 1, 1, 0, 0, 0)"


def before_filter(b: ExerciseBuild, column: str) -> str:
    return f"Table.SelectRows({{prev}}, each [{column}] < {before(b)})"


def nav(b: ExerciseBuild, number: int, table: str, corrections: dict | None = None, extra=()) -> str:
    return audit.nav(b, number, table, corrections, extra)


def notes_sheet(b: ExerciseBuild):
    return b.wb.Worksheets(notes.NOTES_SHEET)


def new_sheet(b: ExerciseBuild, name: str):
    return xl.sheet(b.wb, name, before=notes_sheet(b))


def load(b: ExerciseBuild, query: str, sheet_name: str):
    """Load a query to a worksheet named after it, just before the Solution Notes."""
    return xl.load_query(b.wb, query, sheet_name, after=b.wb.Worksheets(notes_sheet(b).Index - 1))


def edit_step(b: ExerciseBuild, query: str, old: str, new: str) -> None:
    """Edit one step of a tutorial query (the copy only), as the Applied Steps pane does."""
    xl.wait_ready(b.wb.Application)

    def run() -> None:
        q = b.wb.Queries(query)
        text = q.Formula
        if new in text and old not in text:               # already edited (a retried call)
            return
        assert text.count(old) == 1, f"{query}: the step to edit was not found once:\n{old}\nin\n{text}"
        q.Formula = text.replace(old, new)
    xl.retry(run)
    xl.wait_ready(b.wb.Application)


def put(ws, cells: dict) -> None:
    for addr, value in cells.items():
        if isinstance(value, str) and value.startswith("="):
            ws.Range(addr).Formula2 = value
        else:
            ws.Range(addr).Value = value


def bold(ws, addr: str) -> None:
    ws.Range(addr).Font.Bold = True


def title(ws, text: str) -> None:
    ws.Range("A1").Value = text
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 13


def heading(ws, row: int, text: str, col: int = 1) -> None:
    ws.Cells(row, col).Value = text
    ws.Cells(row, col).Font.Bold = True
    ws.Cells(row, col).Font.Size = 12


def header(ws, row: int, col: int, names: list[str]) -> None:
    for i, name in enumerate(names):
        ws.Cells(row, col + i).Value = name
    ws.Range(ws.Cells(row, col), ws.Cells(row, col + len(names) - 1)).Font.Bold = True


def fmt(ws, addr: str, number_format: str) -> None:
    ws.Range(addr).NumberFormat = number_format


def text_block(ws, row: int, label: str, paragraphs: list[str], col: int = 1, span: int = 8) -> int:
    """A labeled block of wrapped text, one merged row per paragraph; returns the next free row (after a gap)."""
    ws.Cells(row, col).Value = label
    ws.Cells(row, col).Font.Bold = True
    width = sum(ws.Columns(col + i).ColumnWidth for i in range(span))
    r = row + 1
    for p in paragraphs:
        rng = ws.Range(ws.Cells(r, col), ws.Cells(r, col + span - 1))
        rng.Merge()
        rng.WrapText = True
        rng.VerticalAlignment = -4160                     # top
        ws.Cells(r, col).Value = p
        lines = math.ceil(len(p) * 1.12 / max(width, 20)) + 0.4
        ws.Rows(r).RowHeight = min(409, max(15, 15 * lines))
        r += 1
    return r + 1


def pivot(b: ExerciseBuild, ws, source: str, anchor: str, name: str):
    cache = b.wb.PivotCaches().Create(SourceType=xl.XL_DATABASE, SourceData=source)
    return cache.CreatePivotTable(TableDestination=ws.Range(anchor), TableName=name)


def gpd(data_field: str, sheet: str, anchor: str, *pairs) -> str:
    """A GETPIVOTDATA formula (without the =)."""
    col, row = re.match(r"([A-Z]+)(\d+)", anchor).groups()
    items = "".join(f',"{k}",' + (str(v) if isinstance(v, (int, float)) else '"' + str(v).replace('"', '""') + '"')
                    for k, v in zip(pairs[::2], pairs[1::2]))
    return f"GETPIVOTDATA(\"{data_field}\",'{sheet}'!${col}${row}{items})"


def subtotals_off(field) -> None:
    """Automatic subtotals off for a row field (Field Settings > Subtotals > None)."""
    try:
        field.Subtotals = tuple([False] * 12)
    except Exception:                                    # noqa: BLE001  (late-bound COM: set Subtotals(1) instead)
        field._oleobj_.Invoke(field._oleobj_.GetIDsOfNames("Subtotals"), 0, 4, False, 1, False)


def spill_values(ws, anchor: str):
    """Paste Special > Values over a spilled range; returns the values."""
    rng = ws.Range(anchor).SpillingToRange
    address, values = rng.Address, rng.Value
    ws.Range(anchor).ClearContents()
    ws.Range(address).Value = values
    return values


def q_(sheet: str) -> str:
    return f"'{sheet}'"


# --- the values the solutions must reproduce ----------------------------------------------------------------------

class Facts:
    """Expected values for the checks, from CharlesRiver.sqlite (read-only), independently of Excel."""

    def __init__(self, year: int):
        self.year = year
        self.before = f"{year + 1}-01-01"
        self.base = audit.Facts(year)                     # Tutorials 8.1 to 8.3 (payments, aging, journal entries)
        con = sqlite3.connect(db_uri(), uri=True)
        self.q = lambda sql, *args: con.execute(sql, args).fetchall()
        for account_id, number in ((AR, "1020"), (ALLOWANCE, "1030"), (AP, "2010"), (BAD_DEBT, "6170")):
            got = self.q("SELECT AccountNumber FROM Account WHERE AccountID = ?", account_id)[0][0]
            assert str(got) == number, f"AccountID {account_id} is account {got}, not {number}"
        self.staff = {r[0]: dict(id=r[0], name=r[1], title=r[2], limit=r[3], terminated=r[4], family=r[5]) for r in self.q(
            "SELECT EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount, TerminationDate, JobFamily FROM Employee")}

    # --- Exercise 8.1 ------------------------------------------------------------------------------------------------
    @cached_property
    def ex1(self) -> dict:
        a = self.base.aging
        rows = []
        for _, label in audit.BUCKETS:
            bk = a["buckets"][label]
            rows.append(dict(label=label, count=bk["count"], balance=bk["balance"], rate=LOSS_RATES[label],
                             loss=xr(bk["balance"] * LOSS_RATES[label])))
        loss = sum(r["loss"] for r in rows)
        opening, voucher = a["je"]["amount"], a["je"]["voucher"]
        opening_loss = xr(opening * LOSS_RATES["Over 90 days"])
        small = sorted((i for i in a["invoices"] if i["balance"] < SMALL), key=lambda i: -i["days"])
        after = []
        for r in rows:
            s = [i for i in small if i["bucket"] == r["label"]]
            bal = r["balance"] - sum(i["balance"] for i in s)
            after.append(dict(label=r["label"], count=r["count"] - len(s), balance=bal, small=len(s),
                              loss=xr(bal * r["rate"])))
        old = [i for i in small if i["days"] >= 61]
        gl_rows = sum(v["count"] for (acc, _), v in a["ledger"].items() if acc in (ALLOWANCE, BAD_DEBT))
        return dict(rows=rows, loss=loss, opening=opening, voucher=voucher, opening_loss=opening_loss,
                    with_opening=loss + opening_loss, small=small, small_total=sum(i["balance"] for i in small),
                    small_current=[i for i in small if i["bucket"] == "Current"], old=old,
                    old_low=min(i["balance"] for i in old), old_high=max(i["balance"] for i in old),
                    after=after, after_loss=sum(r["loss"] for r in after), gl_rows=gl_rows,
                    total=a["subledger"], count=len(a["invoices"]))

    # --- Exercise 8.2 ------------------------------------------------------------------------------------------------
    @cached_property
    def ex2(self) -> dict:
        paid = defaultdict(float)
        for p in self.base.payments:
            paid[p["invoice_id"]] += p["amount"]
        open_ = {}
        for pid, number, total, po, supplier in self.q(
                "SELECT PurchaseInvoiceID, InvoiceNumber, GrandTotal, PurchaseOrderID, SupplierID FROM PurchaseInvoice "
                "WHERE InvoiceDate < ? ORDER BY PurchaseInvoiceID", self.before):
            raw = total - paid[pid]
            assert abs(abs(raw) * 100 % 1 - 0.5) > 1e-4, f"{number}: open balance {raw!r} is near a half cent"
            balance = audit.round_even(raw)
            if balance > 0:
                open_[pid] = dict(number=number, total=total, balance=balance, po=po, supplier=supplier)
        sources = {s: dict(count=n, amount=v) for s, n, v in self.q(
            "SELECT SourceDocumentType, COUNT(*), SUM(Credit - Debit) FROM GLEntry WHERE AccountID = ? AND PostingDate < ? "
            "GROUP BY 1", AP, self.before)}
        assert set(sources) == {"PurchaseInvoice", "DisbursementPayment", "JournalEntry"}, sources
        balance = sum(v["amount"] for v in sources.values())
        je = []
        for voucher, gl_text, amount in self.q(
                "SELECT VoucherNumber, Description, Credit - Debit FROM GLEntry WHERE AccountID = ? AND PostingDate < ? "
                "AND SourceDocumentType = 'JournalEntry' ORDER BY PostingDate, GLEntryID", AP, self.before):
            kind, text = self.q("SELECT EntryType, Description FROM JournalEntry WHERE EntryNumber = ?", voucher)[0]
            m = re.search(r"invoice (\d+)", text)
            item = dict(voucher=voucher, gl_text=gl_text, amount=amount, kind=kind, text=text, invoice_id=None)
            if m:
                pid = int(m.group(1))
                inv = open_[pid]                                   # the reclassified invoice is still open in the detail
                po = self.q("SELECT PONumber, OrderDate, OrderTotal, CreatedByEmployeeID, ApprovedByEmployeeID "
                            "FROM PurchaseOrder WHERE PurchaseOrderID = ?", inv["po"])[0]
                item.update(invoice_id=pid, invoice=inv, po=dict(id=inv["po"], number=po[0], date=po[1], total=po[2],
                                                                 creator=self.staff[po[3]], approver=self.staff[po[4]]),
                            payments=self.q("SELECT COUNT(*) FROM DisbursementPayment WHERE PurchaseInvoiceID = ?",
                                            pid)[0][0])
                assert kind == "Debt Reclass" and abs(inv["balance"] + amount) < 0.005 and item["payments"] == 0
            je.append(item)
        opening = [j for j in je if j["kind"] == "Opening"]
        assert len(opening) == 1 and len(je) == 3, je
        cash = self.q("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                      "WHERE a.AccountNumber = 1010 AND g.VoucherNumber = ?", opening[0]["voucher"])[0][0]
        open_total = sum(v["balance"] for v in open_.values())
        reclass = [j for j in je if j["invoice_id"]]
        assert abs(balance - opening[0]["amount"] - sum(j["amount"] for j in reclass) - open_total) < 0.005
        return dict(open=open_, open_total=open_total, sources=sources, balance=balance,
                    rows=sum(v["count"] for v in sources.values()), je=je, opening=opening[0], reclass=reclass,
                    cash=cash)

    # --- Exercise 8.3 ------------------------------------------------------------------------------------------------
    @cached_property
    def ex3(self) -> dict:
        a = self.base.aging
        cust = {r[0]: dict(id=r[0], name=r[1], limit=r[2], terms=r[3], segment=r[4]) for r in self.q(
            "SELECT CustomerID, CustomerName, CreditLimit, PaymentTerms, CustomerSegment FROM Customer")}
        bal, due = defaultdict(float), defaultdict(float)
        for i in a["invoices"]:
            bal[i["customer"]] += i["balance"]
            if i["days"] > 0:
                due[i["customer"]] += i["balance"]
        ranked = sorted(bal.items(), key=lambda kv: -kv[1])
        total = sum(bal.values())
        over = [dict(cust[k], balance=v, past_due=due[k]) for k, v in ranked if v > cust[k]["limit"]]
        seg, terms = defaultdict(lambda: [0.0, 0.0, set()]), defaultdict(lambda: [0.0, 0.0, set()])
        for i in a["invoices"]:
            c = cust[i["customer"]]
            for group, key in ((seg, c["segment"]), (terms, c["terms"])):
                group[key][0] += i["balance"]
                group[key][2].add(i["customer"])
                if i["days"] > 0:
                    group[key][1] += i["balance"]
        names = Counter(cust[k]["name"] for k in bal)
        mismatch = self.q("SELECT COUNT(*) FROM SalesInvoice si JOIN Customer c USING (CustomerID) WHERE "
                          "CAST(REPLACE(c.PaymentTerms, 'Net ', '') AS INTEGER) <> "
                          "CAST(julianday(si.DueDate) - julianday(si.InvoiceDate) AS INTEGER)")[0][0]
        return dict(customers=len(bal), total=total, ranked=[(cust[k], v) for k, v in ranked], over=over,
                    top5=sum(v for _, v in ranked[:5]) / total, top10=sum(v for _, v in ranked[:10]) / total,
                    segments={k: (v[0], v[1], len(v[2])) for k, v in seg.items()},
                    terms={k: (v[0], v[1], len(v[2])) for k, v in terms.items()},
                    shared_names={n: c for n, c in names.items() if c > 1}, mismatch=mismatch)

    # --- Exercise 8.4 ------------------------------------------------------------------------------------------------
    @cached_property
    def ex4(self) -> dict:
        rows = self.q("SELECT s.SupplierName, s.SupplierCategory, p.Amount, julianday(p.PaymentDate) - julianday(pi.DueDate) "
                      "FROM DisbursementPayment p JOIN PurchaseInvoice pi USING (PurchaseInvoiceID) "
                      "JOIN Supplier s ON s.SupplierID = p.SupplierID WHERE p.PaymentDate >= ? AND p.PaymentDate < ?",
                      f"{self.year}-01-01", self.before)
        spend, category = defaultdict(float), defaultdict(float)
        for name, cat, amount, _ in rows:
            spend[name] += amount
            category[cat] += amount
        total = sum(spend.values())
        ranked = sorted(spend.items(), key=lambda kv: -kv[1])
        marks, running = {}, 0.0
        for rank, (_, amount) in enumerate(ranked, start=1):
            running += amount
            for share in (0.5, 0.8, 0.9):
                if share not in marks and running >= share * total:
                    marks[share] = rank
        days = [r[3] for r in rows]
        assert all(float(d).is_integer() for d in days)
        top = ranked[0][0]
        return dict(n=len(rows), suppliers=len(spend), total=total, marks=marks, top=top, top_share=ranked[0][1] / total,
                    top_category=next(r[1] for r in rows if r[0] == top),
                    categories=sorted(category.items(), key=lambda kv: -kv[1]),
                    early=sum(1 for d in days if d < 0), on=sum(1 for d in days if d == 0),
                    late=sum(1 for d in days if d > 0), late_value=sum(r[2] for r in rows if r[3] > 0) / total,
                    median=statistics.median(days), mean=statistics.mean(days), late30=sum(1 for d in days if d > 30))

    # --- Exercise 8.5 ------------------------------------------------------------------------------------------------
    @cached_property
    def capital(self) -> dict[str, dict]:
        """The note-financed capital purchases of Exercise 8.2, by purchase order number."""
        return {j["po"]["number"]: j for j in self.ex2["reclass"]}

    @cached_property
    def orders(self) -> list[dict]:
        out = []
        for number, ordered, creator, approver, total in self.q(
                "SELECT PONumber, OrderDate, CreatedByEmployeeID, ApprovedByEmployeeID, OrderTotal FROM PurchaseOrder "
                "ORDER BY PurchaseOrderID"):
            a = self.staff[approver]
            flags = dict(self=creator == approver, above=total > a["limit"],
                         term=a["terminated"] is not None and a["terminated"] < ordered)
            out.append(dict(number=number, date=ordered, total=total, creator=self.staff[creator], approver=a,
                            flags=flags, score=sum(flags.values())))
        return out

    def disposition(self, o: dict) -> tuple[str, str]:
        """(design or operation, disposition) for a flagged purchase order. Each rule tests every condition its text
        states, so an order the text does not fit falls through and fails."""
        f, a, c = o["flags"], o["approver"], o["creator"]
        only = lambda *names: o["score"] == len(names) and all(f[n] for n in names)  # noqa: E731
        cap = self.capital.get(o["number"])
        if only("self", "above") and cap and a["title"] == "Purchasing Manager" and o["total"] > 10 * a["limit"]:
            return ("Design and operation",
                    f"Follow up: the note-financed capital purchase behind invoice {cap['invoice']['number']} "
                    f"(Exercise 8.2), {money(o['total'])}, created and approved by the purchasing manager, {a['name']}, "
                    f"far above the approval limit of {money(a['limit'])}. Request the approval of the purchase and of "
                    "the note by someone with the authority (the chief financial officer or the board), and agree the "
                    "asset to the fixed-asset register.")
        if only("self", "above") and a["limit"] == 0 and a["family"] == "Purchasing and Procurement" \
                and o["date"][5:7] == "01":
            return ("Design and operation",
                    f"Follow up: created and approved by the same {a['title'].lower()}, {a['name']}, whose approval "
                    f"limit is $0, on {o['date']}. Nobody with authority approved the "
                    f"order of {money(o['total'])}. Vouch it to its receipt and invoice, and ask why the system "
                    "accepted the creator's own approval.")
        if only("self") and a["title"] == "Purchasing Manager" and o["total"] <= a["limit"]:
            return ("Design",
                    f"Follow up, low risk: created and approved by the purchasing manager, {a['name']}, within the "
                    f"limit of {money(a['limit'])}. The amount is within authority, but no second person approved the "
                    "order, a gap in segregation of duties. Vouch it to its receipt and invoice.")
        if only("above", "term") and a["limit"] == 0:
            return ("Design and operation",
                    f"Follow up: approved by {a['name']}, {audit.article(a['title'].lower())} terminated on "
                    f"{a['terminated']}, on an order dated {o['date']}, created by {c['name']}. The approver had "
                    "left and had no approval authority ($0); the login was still active. Find out who used it, vouch "
                    "the order, and report the access failure.")
        if only("above") and a["limit"] > 0:
            return ("Operation",
                    f"Follow up: approved by the {a['title'].lower()}, {a['name']}, for {money(o['total'])}, "
                    f"{money(o['total'] - a['limit'])} above the limit of {money(a['limit'])}, on {o['date']}. Ask why "
                    "the order was not sent to an approver with enough authority.")
        raise AssertionError(f"no disposition rule fits {o['number']} ({o['flags']})")

    @cached_property
    def ex5(self) -> dict:
        orders = self.orders
        flagged = [o for o in orders if o["score"] >= 1]
        dispositions = {o["number"]: self.disposition(o) for o in flagged}
        invoices = self.q("SELECT PurchaseInvoiceID, InvoiceNumber, GrandTotal, ApprovedByEmployeeID FROM PurchaseInvoice "
                          "ORDER BY PurchaseInvoiceID")
        other = [dict(id=r[0], number=r[1], total=r[2], approver=self.staff[r[3]]) for r in invoices
                 if self.staff[r[3]]["title"] != CFO]
        reqs = self.q("SELECT RequisitionID, RequisitionNumber, RequestedByEmployeeID, ApprovedByEmployeeID, Status, "
                      "Quantity * EstimatedUnitCost, RequestDate, ItemID, Quantity, EstimatedUnitCost, ApprovedDate "
                      "FROM PurchaseRequisition ORDER BY RequisitionID")
        for r in reqs:
            for k in range(BAND_COUNT + 1):
                assert abs(r[5] - (BAND_FROM + k * BAND_WIDTH)) > 1e-6, f"{r[1]} is on a band boundary"
        bands = [sum(1 for r in reqs if low <= r[5] < low + BAND_WIDTH)
                 for low in range(BAND_FROM, BAND_FROM + BAND_COUNT * BAND_WIDTH, BAND_WIDTH)]
        band = [r for r in reqs if BAND_EXAMINED <= r[5] < BAND_EXAMINED + BAND_WIDTH]
        groups, cur = [], [band[0]]                 # runs of consecutive requisition numbers with the same value
        for x in band[1:]:
            if x[0] == cur[-1][0] + 1 and x[5] == cur[-1][5]:
                cur.append(x)
            else:
                groups.append(cur)
                cur = [x]
        groups = [g for g in groups + [cur] if len(g) > 1]
        runs = {x[0] for g in groups for x in g}
        approvers = Counter(r[3] for r in reqs if r[3] is not None)
        pays = self.base.payments
        same = Counter((p["supplier"], p["amount"]) for p in pays)
        same_inv = Counter((p["supplier"], p["amount"], p["invoice_id"]) for p in pays)
        dates = defaultdict(list)
        for p in pays:
            dates[(p["supplier"], p["amount"])].append(date.fromisoformat(p["date"][:10]))
        pairs = [g for g in dates.values() if len(g) > 1]
        assert max(len(g) for g in pairs) == 2
        gaps = []
        for y in range(self.year - 2, self.year + 1):
            seqs = [int(o["number"][-6:]) for o in orders if int(o["number"][3:7]) == y]
            gaps.append(dict(year=y, n=len(seqs), low=min(seqs), high=max(seqs)))
        return dict(orders=len(orders), cfo=sum(1 for o in orders if o["approver"]["title"] == CFO),
                    flags={k: sum(1 for o in orders if o["flags"][k]) for k in ("self", "above", "term")},
                    scores=Counter(o["score"] for o in orders), flagged=flagged, dispositions=dispositions,
                    invoices=len(invoices), other=other, bands=bands, band=band, runs=runs, groups=groups,
                    unapproved=sum(1 for r in reqs if r[3] is None), approvers=approvers,
                    five=[e for e in self.staff.values() if e["limit"] == 5000],
                    same=sum(c for c in same.values() if c > 1), same_invoice=sum(c for c in same_inv.values() if c > 1),
                    pairs=len(pairs), within30=sum(1 for g in pairs if abs((g[1] - g[0]).days) <= 30), gaps=gaps)

    # --- Exercise 8.6 ------------------------------------------------------------------------------------------------
    @cached_property
    def ex6(self) -> dict:
        promos = {r[0]: dict(id=r[0], code=r[1], start=r[2], end=r[3], approver=self.staff[r[4]], approved=r[5],
                             pct=r[6], name=r[7]) for r in self.q(
            "SELECT PromotionID, PromotionCode, EffectiveStartDate, EffectiveEndDate, ApprovedByEmployeeID, ApprovedDate, "
            "DiscountPct, PromotionName FROM PromotionProgram ORDER BY PromotionID")}
        flagged = [p for p in promos.values() if p["end"] <= p["start"]]
        lines = self.q("SELECT l.PromotionID, o.OrderDate, si.InvoiceDate, l.Quantity * l.UnitPrice * l.Discount "
                       "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                       "JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID WHERE l.PromotionID IS NOT NULL")
        by = defaultdict(lambda: dict(n=0, outside=0, discount=0.0, first=None, last=None, invoiced=None))
        outside_all = 0
        for pid, ordered, invoiced, discount in lines:
            p, s = promos[pid], by[pid]
            s["n"] += 1
            s["discount"] += discount
            s["first"] = min(s["first"] or ordered, ordered)
            s["last"] = max(s["last"] or ordered, ordered)
            s["invoiced"] = max(s["invoiced"] or invoiced, invoiced)
            if not p["start"] <= ordered <= p["end"]:
                s["outside"] += 1
                outside_all += 1
        pending = []
        for oid, sol, reference, approved in self.q(
                "SELECT PriceOverrideApprovalID, SalesOrderLineID, ReferenceUnitPrice, ApprovedUnitPrice "
                "FROM PriceOverrideApproval WHERE Status = 'Pending' ORDER BY PriceOverrideApprovalID"):
            for number, qty, price, method, approval in self.q(
                    "SELECT si.InvoiceNumber, l.Quantity, l.UnitPrice, l.PricingMethod, l.PriceOverrideApprovalID "
                    "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) WHERE l.SalesOrderLineID = ?", sol):
                pending.append(dict(id=oid, sol=sol, number=number, qty=qty, price=price, method=method,
                                    approval=approval, reference=reference, approved=approved,
                                    below=(reference - price) * qty))
        lists = {r[0]: dict(id=r[0], name=r[1], scope=r[2], customer=r[3], segment=r[4], start=r[5], end=r[6],
                            status=r[7]) for r in self.q(
            "SELECT PriceListID, PriceListName, ScopeType, CustomerID, CustomerSegment, EffectiveStartDate, "
            "EffectiveEndDate, Status FROM PriceList ORDER BY PriceListID")}
        flagged_lists = [x for x in lists.values() if x["status"] == "Expired" or x["end"] < x["start"]]
        order_lines = self.q("SELECT l.SalesOrderLineID, pll.PriceListID, o.OrderDate, l.LineTotal, o.CustomerID, "
                             "l.PricingMethod, l.UnitPrice, pll.UnitPrice, l.ItemID FROM SalesOrderLine l "
                             "JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
                             "LEFT JOIN PriceListLine pll ON pll.PriceListLineID = l.PriceListLineID")
        after = [r for r in order_lines if r[1] is not None and r[2] > lists[r[1]]["end"]]
        grid = {(x["id"], y): sum(1 for r in after if r[1] == x["id"] and int(r[2][:4]) == y)
                for x in flagged_lists for y in range(self.year - 2, self.year + 1)}
        assert sum(grid.values()) == len(after), "lines priced after the end of a list that is not flagged"
        later = sum(1 for x in flagged_lists for o in lists.values()
                    if (o["scope"], o["segment"], o["customer"]) == (x["scope"], x["segment"], x["customer"])
                    and o["end"] > x["end"])
        used = Counter(r[1] for r in order_lines)
        n_lines = Counter(r[0] for r in self.q("SELECT PriceListID FROM PriceListLine"))
        unused = [x for x in lists.values() if x["status"] == "Active" and used[x["id"]] == 0]
        own_list = {x["customer"]: x["id"] for x in lists.values() if x["scope"] == "Customer"}
        own = []
        for sol, cited, ordered, _, customer, method, price, cited_price, item in order_lines:
            if customer in own_list and method not in ("Customer Price List", "Approved Override"):
                own_price = self.q("SELECT UnitPrice FROM PriceListLine WHERE PriceListID = ? AND ItemID = ? "
                                   "ORDER BY PriceListLineID", own_list[customer], item)[0][0]
                own.append(dict(sol=sol, customer=customer, date=ordered, method=method, cited=cited, price=price,
                                cited_price=cited_price, own_list=own_list[customer], own_price=own_price))
        return dict(flagged=flagged, by=by, outside_all=outside_all, pending=pending, flagged_lists=flagged_lists,
                    grid=grid, after=len(after), after_total=sum(r[3] for r in after), later=later, unused=unused,
                    unused_lines=sum(n_lines[x["id"]] for x in unused), own=own,
                    customer=self.q("SELECT CustomerName, CustomerSegment FROM Customer WHERE CustomerID = ?",
                                    own[0]["customer"])[0] if own else None)


_FACTS: dict[int, Facts] = {}


def facts(b: ExerciseBuild) -> Facts:
    if b.year not in _FACTS:
        _FACTS[b.year] = Facts(b.year)
    return _FACTS[b.year]


# --- Exercise 8.1 ----------------------------------------------------------------------------------------------------

def ex8_1(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b).ex1
    ns = notes_sheet(b)
    if wb.SlicerCaches.Count == 0 and ns.Index < wb.Worksheets.Count:
        ns.Move(None, wb.Worksheets(wb.Worksheets.Count))           # the exercise sheets follow the tutorial sheets

    # (1) the LossRate column of the Buckets Table, and the expected loss of each bucket on the Aging worksheet.
    ag = wb.Worksheets("Aging")
    bk = xl.table(wb, "Buckets")
    col = bk.ListColumns.Add()
    col.Name = "LossRate"
    labels = bk.ListColumns("Bucket").DataBodyRange
    for i in range(1, bk.ListRows.Count + 1):
        col.DataBodyRange.Cells(i, 1).Value = LOSS_RATES[labels.Cells(i, 1).Value]
    col.DataBodyRange.NumberFormat = "0.0%"
    assert ag.Range("A3").Value == "Bucket" and ag.Range("A9").Value == "Total"
    put(ag, {"E3": "Expected credit loss"})
    ag.Range("E4:E8").Formula2 = "=ROUND(C4*XLOOKUP(A4,Buckets[Bucket],Buckets[LossRate]),2)"
    put(ag, {"E9": "=SUM(E4:E8)"})
    fmt(ag, "E4:E9", MONEY)
    bold(ag, "E3")
    ag.Columns("E").ColumnWidth = 20
    ag.Columns("H").ColumnWidth = 10

    ws = new_sheet(b, "Ex 8.1")
    for c, w in zip("ABCDEFGH", (46, 30, 14, 12, 14, 14, 14, 14)):
        ws.Columns(c).ColumnWidth = w
    title(ws, "Exercise 8.1: Estimating the Allowance for Credit Losses")
    put(ws, {"A2": "As-of date", "B2": "=AsOfDate"})
    fmt(ws, "B2", DATE)
    ws.Range("B2").HorizontalAlignment = -4131
    heading(ws, 4, "(1) Expected credit losses on the aging")
    put(ws, {"A5": "Allowance from the aging (Aging!E9)", "B5": "=Aging!E9",
             "A6": "The LossRate column is in the Buckets Table (Aging!H3:H8); the expected loss of each bucket is in "
                   "Aging!E4:E8, rounded to cents."})
    fmt(ws, "B5", MONEY)

    heading(ws, 8, "(2) With the opening balance treated as more than 90 days past due")
    put(ws, {"A9": "Opening balance of account 1020 with no invoice detail",
             "B9": f'=SUMIFS(LedgerAR[Amount],LedgerAR[AccountID],{AR},LedgerAR[SourceDocumentType],"JournalEntry")',
             "C9": f'=FILTER(LedgerAR[VoucherNumber],(LedgerAR[AccountID]={AR})*(LedgerAR[SourceDocumentType]="JournalEntry"))',
             "A10": "Loss rate, more than 90 days past due", "B10": '=XLOOKUP("Over 90 days",Buckets[Bucket],Buckets[LossRate])',
             "A11": "Expected loss on the opening balance", "B11": "=ROUND(B9*B10,2)",
             "A12": "Allowance with the opening balance", "B12": "=B5+B11"})
    fmt(ws, "B9", MONEY)
    fmt(ws, "B10", "0.0%")
    fmt(ws, "B11:B12", MONEY)
    row = text_block(ws, 14, f"{MA}, requirement (2)", [
        f"Treating the {money(f['opening'])} as more than 90 days past due adds {money(f['opening_loss'])} and raises "
        f"the allowance from {money(f['loss'])} to {money(f['with_opening'])}. But its age cannot be known from the "
        f"data: {f['voucher']} posted it to account 1020 as a single line on the conversion date, with no customer, "
        "invoice, invoice date, or due date behind it, and no cash application has ever reduced it, because every "
        "receipt is applied to an invoice. A balance with no customer detail cannot be aged, confirmed, or collected, so "
        "the real question is whether it belongs in receivables at all. It should not simply be aged: the controller "
        "should obtain the customer-level detail from the conversion date and age that detail, or, if no support "
        "exists, remove the balance (a correction of the opening balances) rather than reserve 40 percent of it."])

    # (3) the open invoices under $10, and the aging without them.
    heading(ws, row, f"(3) Open invoices with a balance under ${SMALL}")
    put(ws, {f"A{row + 1}": f"Open invoices with a balance under ${SMALL}",
             f"B{row + 1}": f'=COUNTIF(OpenInvoices[OpenBalance],"<{SMALL}")',
             f"A{row + 2}": "Their total", f"B{row + 2}": f'=SUMIF(OpenInvoices[OpenBalance],"<{SMALL}")'})
    fmt(ws, f"B{row + 1}", COUNT)
    fmt(ws, f"B{row + 2}", MONEY)
    small_row = row + 4
    header(ws, small_row, 1, ["InvoiceNumber", "CustomerName", "DueDate", "DaysPastDue", "Bucket", "OpenBalance"])
    ws.Range(f"A{small_row + 1}").Formula2 = (
        f"=LET(k,OpenInvoices[OpenBalance]<{SMALL},SORTBY(FILTER(HSTACK(OpenInvoices[InvoiceNumber],"
        "OpenInvoices[CustomerName],OpenInvoices[DueDate],OpenInvoices[DaysPastDue],OpenInvoices[Bucket],"
        "OpenInvoices[OpenBalance]),k),FILTER(OpenInvoices[DaysPastDue],k),-1))")
    n_small = len(f["small"])
    fmt(ws, f"C{small_row + 1}:C{small_row + n_small}", DATE)
    fmt(ws, f"F{small_row + 1}:F{small_row + n_small}", MONEY)
    wo = small_row + n_small + 3
    ws.Cells(wo - 1, 1).Value = "The aging if they were written off"
    ws.Cells(wo - 1, 1).Font.Italic = True
    header(ws, wo, 1, ["Bucket", "Invoices", "Open balance", "Written off", "Invoices after", "Balance after",
                       "Loss rate", "Expected loss after"])
    for i in range(len(audit.BUCKETS)):
        r, ar = wo + 1 + i, 4 + i
        put(ws, {f"A{r}": f"=Aging!A{ar}", f"B{r}": f"=Aging!B{ar}", f"C{r}": f"=Aging!C{ar}",
                 f"D{r}": f'=COUNTIFS(OpenInvoices[Bucket],A{r},OpenInvoices[OpenBalance],"<{SMALL}")',
                 f"E{r}": f"=B{r}-D{r}",
                 f"F{r}": f'=C{r}-SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[Bucket],A{r},OpenInvoices[OpenBalance],"<{SMALL}")',
                 f"G{r}": f"=XLOOKUP(A{r},Buckets[Bucket],Buckets[LossRate])", f"H{r}": f"=ROUND(F{r}*G{r},2)"})
    tot = wo + 1 + len(audit.BUCKETS)
    put(ws, {f"A{tot}": "Total"})
    for c in "BCDEFH":
        put(ws, {f"{c}{tot}": f"=SUM({c}{wo + 1}:{c}{tot - 1})"})
    for c in "BDE":
        fmt(ws, f"{c}{wo + 1}:{c}{tot}", COUNT)
    for c in "CFH":
        fmt(ws, f"{c}{wo + 1}:{c}{tot}", MONEY)
    fmt(ws, f"G{wo + 1}:G{tot - 1}", "0.0%")
    bold(ws, f"A{tot}:H{tot}")
    old = f["old"]
    current = f["small_current"]
    assert len(current) + len(old) == n_small, "a balance under $10 is 1 to 60 days past due"
    after_61 = [r for r in f["after"] if r["label"] in ("61-90 days", "Over 90 days")]
    row = text_block(ws, tot + 2, f"{MA}, requirement (3)", [
        f"{word(n_small, True)} open invoices have balances under ${SMALL}, together {money(f['small_total'])}. "
        + (f"One is current ({', '.join(i['number'] + ' ' + money(i['balance']) for i in current)}); "
           if len(current) == 1 else f"{word(len(current), True)} are current; ")
        + f"the other {word(len(old))} are 61 or more days past due, from {money(f['old_low'])} to {money(f['old_high'])}: "
        "residuals left after the customers paid, not amounts anyone is disputing. Writing them off removes "
        f"{word(n_small)} invoices and {money(f['small_total'])} from the aging and lowers the expected loss from "
        f"{money(f['loss'])} to {money(f['after_loss'])}. The amounts are trivial, but the write-off matters for the "
        f"aging itself: after it, the two oldest buckets hold {sum(r['count'] for r in after_61)} invoices instead of "
        f"{sum(r['count'] + r['small'] for r in after_61)}, so what is left there is worth a collection call."])

    # (4) the adjusting entry.
    heading(ws, row, "(4) Adjusting journal entry")
    e = row + 1
    header(ws, e, 1, ["Account", "Debit", "Credit"])
    put(ws, {f"A{e + 1}": "6170 Bad Debt Expense", f"B{e + 1}": "=Aging!E9",
             f"A{e + 2}": "1030 Allowance for Doubtful Accounts", f"C{e + 2}": "=Aging!E9",
             f"A{e + 3}": "Total", f"B{e + 3}": f"=SUM(B{e + 1}:B{e + 2})", f"C{e + 3}": f"=SUM(C{e + 1}:C{e + 2})",
             f"A{e + 4}": "Dated at the as-of date (Ex 8.1!B2). To record the allowance for credit losses on the open "
                          "invoices at the rates proposed by the credit department (Aging!E9).",
             f"A{e + 5}": "GL rows in accounts 1030 and 6170 to date (LedgerAR)",
             f"B{e + 5}": f"=COUNTIF(LedgerAR[AccountID],{ALLOWANCE})+COUNTIF(LedgerAR[AccountID],{BAD_DEBT})"})
    fmt(ws, f"B{e + 1}:C{e + 3}", MONEY)
    fmt(ws, f"B{e + 5}", COUNT)
    bold(ws, f"A{e + 3}:C{e + 3}")
    entry = e
    row = text_block(ws, e + 7, f"{MA}, requirement (4)", [
        f"Dr 6170 Bad Debt Expense {money(f['loss'])}; Cr 1030 Allowance for Doubtful Accounts {money(f['loss'])}. "
        "The recommended allowance covers the invoices only; the opening balance is resolved separately, as "
        "requirement (2) explains. Neither account has ever had a posting, so this would be the first allowance.",
        "The credit loss standard (FASB, 2016; ASC 326-20) accepts an aging schedule as a method of estimating expected "
        "credit losses, and it requires an allowance even when the risk of loss is remote. The rates must start from "
        "historical loss experience for each bucket and then be adjusted for current conditions and reasonable and "
        "supportable forecasts (the standard's illustration of an aging schedule does exactly that). Charles River has "
        "no write-off history, so the proposed rates are not its own experience: document their source, then raise "
        "them if customers' industries or the economy weaken, or if forecast conditions are worse than the period the "
        "rates come from, and lower them only with evidence. The adjustment is a judgment the controller documents and "
        "revisits every reporting date."])

    # (5) the memo.
    pct_ar = f["loss"] / f["total"]
    row = text_block(ws, row, f"{MA}, requirement (5): memo to the controller", [
        f"To: the controller. Subject: allowance for credit losses at {date(b.year, 12, 31).isoformat()}.",
        f"Estimate. Applying the credit department's loss rates to the aging of the {f['count']:,} open invoices "
        f"({money(f['total'])}) gives an expected credit loss of {money(f['loss'])}, {pct_ar:.2%} of the open balance. "
        f"Almost all of it comes from the current bucket ({money(f['rows'][0]['loss'])}) and the 1 to 30 days bucket "
        f"({money(f['rows'][1]['loss'])}), because customers pay mostly on time. I recommend recording it: Dr 6170 Bad "
        f"Debt Expense, Cr 1030 Allowance for Doubtful Accounts, {money(f['loss'])}. Charles River has never recorded an "
        "allowance, and the credit loss standard requires one even when the risk is low; the rates should be documented "
        "and adjusted for current conditions and forecasts.",
        f"Opening balance. Account 1020 also holds {money(f['opening'])} posted by {f['voucher']} with no invoice detail. "
        f"If it were aged as more than 90 days past due, the allowance would rise to {money(f['with_opening'])}, but "
        "its age and collectability cannot be determined, and no customer can be asked to pay it. I recommend not "
        "reserving it as if it were a receivable: obtain the customer detail from the conversion date, or, if none "
        "exists, remove the balance as a correction of the opening balances.",
        f"Small balances. {word(n_small, True)} open invoices carry residual balances under ${SMALL}, together "
        f"{money(f['small_total'])}, most of them more than 60 days past due. I recommend writing them off, which leaves "
        "the oldest buckets with the balances that deserve collection effort."])

    t = "8.1"
    for i, r in enumerate(f["rows"]):
        b.check(t, f"expected credit loss, {r['label']} (Aging!E{4 + i})", r["loss"], f"=Aging!E{4 + i}")
    b.check(t, "allowance from the aging (Aging!E9)", round(f["loss"], 2), "=Aging!E9")
    b.check(t, "loss rates in the Buckets Table", round(sum(LOSS_RATES.values()), 4), "=SUM(Buckets[LossRate])", 1e-9,
            "0.000")
    b.check(t, "opening balance of account 1020 without invoices (Ex 8.1!B9)", round(f["opening"], 2), "='Ex 8.1'!B9")
    b.check(t, "its voucher (Ex 8.1!C9)", f["voucher"], "='Ex 8.1'!C9")
    b.check(t, "allowance with the opening balance at 40% (Ex 8.1!B12)", round(f["with_opening"], 2), "='Ex 8.1'!B12")
    b.check(t, f"open invoices under ${SMALL}", n_small, f"='Ex 8.1'!B{small_row - 3}", 0, COUNT)
    b.check(t, "their total", round(f["small_total"], 2), f"='Ex 8.1'!B{small_row - 2}")
    b.check(t, "rows listed", n_small, f"=ROWS('Ex 8.1'!A{small_row + 1}#)", 0, COUNT)
    b.check(t, f"current invoices under ${SMALL}", len(current),
            f'=COUNTIFS(OpenInvoices[OpenBalance],"<{SMALL}",OpenInvoices[Bucket],"Current")', 0, COUNT)
    b.check(t, f"smallest balance under ${SMALL}, 61 or more days past due", f["old_low"],
            f'=MINIFS(OpenInvoices[OpenBalance],OpenInvoices[OpenBalance],"<{SMALL}",OpenInvoices[DaysPastDue],">=61")')
    b.check(t, f"largest balance under ${SMALL}, 61 or more days past due", f["old_high"],
            f'=MAXIFS(OpenInvoices[OpenBalance],OpenInvoices[OpenBalance],"<{SMALL}",OpenInvoices[DaysPastDue],">=61")')
    b.check(t, "invoices after the write-off", f["count"] - n_small, f"='Ex 8.1'!E{tot}", 0, COUNT)
    b.check(t, "open balance after the write-off", round(f["total"] - f["small_total"], 2), f"='Ex 8.1'!F{tot}")
    b.check(t, "expected loss after the write-off", round(f["after_loss"], 2), f"='Ex 8.1'!H{tot}")
    b.check(t, "entry: debit to 6170", round(f["loss"], 2), f"='Ex 8.1'!B{entry + 1}")
    b.check(t, "entry: debits less credits", 0, f"='Ex 8.1'!B{entry + 3}-'Ex 8.1'!C{entry + 3}")
    b.check(t, "GL rows in accounts 1030 and 6170", f["gl_rows"], f"='Ex 8.1'!B{entry + 5}", 0, COUNT)


# --- Exercise 8.2 ----------------------------------------------------------------------------------------------------

def ex8_2(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b).ex2
    # (1) the open supplier invoices.
    xl.add_query(wb, "PaidByInvoice", pq.steps_query([
        ("Source", "Payments"),
        ("Grouped Rows", 'Table.Group({prev}, {"PurchaseInvoiceID"}, {{"PaidTotal", each List.Sum([Amount]), '
                         'type nullable number}})')]))
    xl.add_query(wb, "OpenPayables", nav(b, 37, "PurchaseInvoice", extra=[
        ("Filtered Rows", before_filter(b, "InvoiceDate")),
        ("Merged Queries", pq.merge("PaidByInvoice", "PurchaseInvoiceID", "PurchaseInvoiceID", "PaidByInvoice")),
        ("Expanded PaidByInvoice", pq.expand("PaidByInvoice", ["PaidTotal"])),
        ("Replaced Value", 'Table.ReplaceValue({prev},null,0,Replacer.ReplaceValue,{"PaidTotal"})'),
        ("Added Custom", pq.add_custom("OpenBalance", "[GrandTotal] - [PaidTotal]")),
        ("Changed Type1", pq.transform_types([("OpenBalance", "type number")])),
        ("Rounded Off", 'Table.TransformColumns({prev},{{"OpenBalance", each Number.Round(_, 2), type number}})'),
        ("Filtered Rows1", "Table.SelectRows({prev}, each [OpenBalance] > 0)")]))
    # (2) account 2010 in the ledger, filtered first.
    kept = audit.table_order(b, "GLEntry", ["GLEntryID", "PostingDate", "AccountID", "VoucherNumber",
                                            "SourceDocumentType", "Description", "Debit", "Credit"])
    xl.add_query(wb, "LedgerAP", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", f"Table.SelectRows({{prev}}, each [AccountID] = {AP})"),
        ("Filtered Rows1", before_filter(b, "PostingDate")),
        ("Removed Other Columns", pq.select_columns(kept)),
        ("Added Custom", pq.add_custom("Amount", "[Credit] - [Debit]")),
        ("Changed Type1", pq.transform_types([("Amount", "type number")]))]))
    # (4) the purchase orders, with who created and approved them (the Employees query of Tutorial 8.3).
    xl.add_query(wb, "PurchaseOrders", nav(b, 33, "PurchaseOrder", extra=[
        ("Merged Queries", pq.merge("Employees", "CreatedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", pq.expand("Employees", ["EmployeeName", "JobTitle"])),
        ("Renamed Columns", pq.rename([("EmployeeName", "CreatorName"), ("JobTitle", "CreatorTitle")])),
        ("Merged Queries1", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees1", pq.expand("Employees", ["EmployeeName", "JobTitle", "MaxApprovalAmount"])),
        ("Renamed Columns1", pq.rename([("EmployeeName", "ApproverName"), ("JobTitle", "ApproverTitle"),
                                        ("MaxApprovalAmount", "ApproverLimit")]))]))

    ws = new_sheet(b, "Ex 8.2")
    op = load(b, "OpenPayables", "OpenPayables")
    for c in ("SubTotal", "TaxAmount", "GrandTotal", "PaidTotal", "OpenBalance"):
        op.ListColumns(c).DataBodyRange.NumberFormat = MONEY
    la = load(b, "LedgerAP", "LedgerAP")
    for c in ("Debit", "Credit", "Amount"):
        la.ListColumns(c).DataBodyRange.NumberFormat = MONEY
    po = load(b, "PurchaseOrders", "PurchaseOrders")
    po.ListColumns("OrderTotal").DataBodyRange.NumberFormat = MONEY

    # (3) the PivotTable by source document, and Show Details for the JournalEntry rows.
    pv = xl.sheet(wb, "Ex 8.2 Pivot", after=ws)
    pt = pivot(b, pv, "LedgerAP", "A3", "PivotEx82")
    pt.PivotFields("SourceDocumentType").Orientation = xl.XL_ROW
    pt.AddDataField(pt.PivotFields("GLEntryID"), "Count of GLEntryID", xl.XL_COUNT).NumberFormat = COUNT
    pt.AddDataField(pt.PivotFields("Amount"), "Sum of Amount", xl.XL_SUM).NumberFormat = MONEY
    pv.Range("A1").Value = "Account 2010 (AccountID 22) by source document; Amount is Credit - Debit"
    pv.Columns("A:C").AutoFit()
    pt.GetPivotData("Sum of Amount", "SourceDocumentType", "JournalEntry").ShowDetail = True
    detail = wb.ActiveSheet
    assert detail.Name != pv.Name and detail.ListObjects.Count == 1, "Show Details made no worksheet"
    detail.Name = "Ex 8.2 JE Rows"
    detail.ListObjects(1).Name = "APJournalRows"
    detail.Columns.AutoFit()

    # (5) the reconciliation workpaper.
    for c, w in zip("ABCDEFGH", (54, 16, 44, 16, 20, 16, 70, 26)):
        ws.Columns(c).ColumnWidth = w
    title(ws, "Exercise 8.2: Reconciling Accounts Payable to the Ledger")
    put(ws, {"A2": "As-of date", "B2": "=AsOfDate"})
    fmt(ws, "B2", DATE)
    ws.Range("B2").HorizontalAlignment = -4131
    heading(ws, 4, "(1) and (2) The two balances")
    header(ws, 5, 1, ["Source", "Rows", "", "", "", "Amount"])
    put(ws, {"A6": "Open supplier invoices (OpenPayables)", "B6": "=ROWS(OpenPayables[OpenBalance])",
             "F6": "=SUM(OpenPayables[OpenBalance])",
             "A7": f"Account 2010 Accounts Payable, AccountID {AP} (LedgerAP), credits less debits",
             "B7": "=ROWS(LedgerAP[GLEntryID])", "F7": "=SUM(LedgerAP[Credit])-SUM(LedgerAP[Debit])"})
    fmt(ws, "B6:B7", COUNT)
    fmt(ws, "F6:F7", MONEY)

    heading(ws, 9, "(3) and (5) Reconciliation of account 2010 to the open invoices")
    put(ws, {"A10": "The ledger rows by source document are on the Ex 8.2 Pivot worksheet; Show Details listed its "
                    "JournalEntry rows on Ex 8.2 JE Rows."})
    header(ws, 11, 1, ["Item", "Voucher", "Entry description (JournalEntries)", "PurchaseInvoiceID", "InvoiceNumber",
                       "Amount", "What it is", "Correction belongs in"])
    put(ws, {"A12": "Balance of account 2010 per the ledger", "F12": "=F7"})
    opening = f["opening"]
    items = [(opening, "Less: opening balance with no invoice detail",
              f"The opening balance entry credited accounts payable with {money(opening['amount'])} on the conversion "
              "date, with no supplier invoices behind it. No payment has ever been applied to it (every payment pays "
              f"an invoice). The same entry debited cash with exactly {money(f['cash'])}, a coincidence worth a "
              "question. Unsupported, like the opening receivables of Tutorial 8.2.",
              "The ledger, unless the conversion-date supplier detail supports it")]
    for j in f["reclass"]:
        items.append((j, "Add: invoice reclassified to notes payable, still open in the detail",
                      f"{j['kind']} entry: the note-financed capital invoice {j['invoice']['number']} "
                      f"({money(j['invoice']['total'])}) was moved from 2010 to 2110 Notes Payable when a note financed "
                      "it. No supplier payment will ever settle it, so it stays open in the invoice detail.",
                      "The invoice detail: close or flag the invoice as settled by the note"))
    for i, (j, label, what, where) in enumerate(items):
        r = 13 + i
        put(ws, {f"A{r}": label, f"B{r}": j["voucher"],
                 f"C{r}": f"=XLOOKUP(B{r},JournalEntries[EntryNumber],JournalEntries[Description])",
                 f"F{r}": f"=-SUMIFS(LedgerAP[Amount],LedgerAP[VoucherNumber],B{r})", f"G{r}": what, f"H{r}": where})
        if j.get("invoice_id"):
            put(ws, {f"D{r}": f'=--TEXTBEFORE(TEXTAFTER(C{r},"invoice ")," ")',
                     f"E{r}": f"=XLOOKUP(D{r},OpenPayables[PurchaseInvoiceID],OpenPayables[InvoiceNumber])"})
    last = 13 + len(items) - 1
    adj, inv, diff = last + 1, last + 2, last + 3
    put(ws, {f"A{adj}": "Ledger balance after the reconciling items", f"F{adj}": f"=F12+SUM(F13:F{last})",
             f"A{inv}": "Open supplier invoices (OpenPayables)", f"F{inv}": "=F6",
             f"A{diff}": "Unexplained difference", f"F{diff}": f"=ROUND(F{adj}-F{inv},2)"})
    fmt(ws, f"F12:F{diff}", MONEY)
    bold(ws, f"A{diff}:F{diff}")
    ws.Range(f"G13:H{last}").WrapText = True
    cash_row = diff + 2
    put(ws, {f"A{cash_row}": f"Cash debited by {opening['voucher']} (JournalLines, account 1010)",
             f"F{cash_row}": f'=SUMIFS(JournalLines[Debit],JournalLines[VoucherNumber],"{opening["voucher"]}",'
                             'JournalLines[AccountNumber],1010)'})
    fmt(ws, f"F{cash_row}", MONEY)

    heading(ws, cash_row + 2, "(4) The purchase orders behind the reconciling invoices (PurchaseOrders)")
    h = cash_row + 3
    cols = ["PurchaseInvoiceID", "InvoiceNumber", "GrandTotal", "OpenBalance", "Payments", "PONumber", "OrderDate",
            "OrderTotal", "CreatorName", "CreatorTitle", "ApproverName", "ApproverTitle", "ApproverLimit"]
    header(ws, h, 1, cols)
    po_rows = {}
    for i, j in enumerate(f["reclass"]):
        r, src = h + 1 + i, 13 + 1 + i
        po_rows[j["voucher"]] = r
        lookup = lambda col: f"XLOOKUP($A{r},OpenPayables[PurchaseInvoiceID],OpenPayables[{col}])"  # noqa: E731
        by_po = lambda col: f"XLOOKUP({lookup('PurchaseOrderID')},PurchaseOrders[PurchaseOrderID],PurchaseOrders[{col}])"  # noqa: E731
        put(ws, {f"A{r}": f"=D{src}", f"B{r}": f"={lookup('InvoiceNumber')}", f"C{r}": f"={lookup('GrandTotal')}",
                 f"D{r}": f"={lookup('OpenBalance')}", f"E{r}": f"=COUNTIF(Payments[PurchaseInvoiceID],A{r})",
                 f"F{r}": f"={by_po('PONumber')}", f"G{r}": f"={by_po('OrderDate')}", f"H{r}": f"={by_po('OrderTotal')}",
                 f"I{r}": f"={by_po('CreatorName')}", f"J{r}": f"={by_po('CreatorTitle')}",
                 f"K{r}": f"={by_po('ApproverName')}", f"L{r}": f"={by_po('ApproverTitle')}",
                 f"M{r}": f"={by_po('ApproverLimit')}"})
    end = h + len(f["reclass"])
    fmt(ws, f"C{h + 1}:D{end}", MONEY)
    fmt(ws, f"G{h + 1}:G{end}", DATE)
    fmt(ws, f"H{h + 1}:H{end}", MONEY)
    fmt(ws, f"M{h + 1}:M{end}", MONEY)
    cap = f["reclass"]
    approver = cap[0]["po"]["approver"]
    row = text_block(ws, end + 2, f"{MA}, requirement (4)", [
        f"Opening balance ({opening['voucher']}, {money(opening['amount'])}): accounts payable carried over at "
        "conversion with no invoice detail and never paid since. The ledger may be right only if the conversion-date "
        "supplier detail supports it; request that detail. Until it is found, the balance is unsupported and the "
        "correction belongs in the ledger, the same finding as the opening receivables. That the same entry debits "
        "cash with exactly the same amount is a coincidence that adds to the question.",
        "Debt reclassifications (" + "; ".join(
            f"{j['voucher']}, {money(j['invoice']['total'])}, invoice {j['invoice']['number']}" for j in cap)
        + f"): each moved a note-financed capital invoice from 2010 to 2110 Notes Payable. The ledger is right; the "
        "invoice detail is not, because no supplier payment will ever close these invoices. The correction belongs in "
        "the invoice detail: close them, or mark them settled by the note, so the open-invoice list stops overstating "
        "what Charles River owes its suppliers.",
        "Purchase orders: " + "; ".join(
            f"{j['po']['number']} ({money(j['po']['total'])}, {j['po']['date']})" for j in cap)
        + f", both created and approved by {approver['name']}, the {approver['title'].lower()}, whose approval limit "
        f"is {money(approver['limit'])}. One person ordered and approved capital equipment for more than ten times "
        "that limit, a question for Exercise 8.5 and for the chief financial officer."])
    row = text_block(ws, row, f"{MA}, requirement (5): workpaper conclusion", [
        f"Objective: reconcile the open supplier invoices at {date(b.year, 12, 31).isoformat()} to account 2010. "
        f"Result: the ledger balance of {money(f['balance'])} exceeds the open invoices of {money(f['open_total'])} by "
        f"{money(f['balance'] - f['open_total'])}, explained by three journal entries: the unsupported opening balance "
        f"(+{money(opening['amount'])}) and the two note-financed invoices that remain open in the detail "
        f"(-{money(sum(j['invoice']['total'] for j in cap))}). Unexplained difference: none. Conclusion: the "
        "reclassifications are explained and need a fix in the invoice detail; the opening balance is unsupported "
        "and goes to the audit committee with the receivables finding."])

    t = "8.2"
    b.check(t, "open supplier invoices (Ex 8.2!B6)", len(f["open"]), "='Ex 8.2'!B6", 0, COUNT)
    b.check(t, "their open balance (Ex 8.2!F6)", round(f["open_total"], 2), "='Ex 8.2'!F6")
    b.check(t, "account 2010 rows before the as-of date (Ex 8.2!B7)", f["rows"], "='Ex 8.2'!B7", 0, COUNT)
    b.check(t, "balance of account 2010, credits less debits (Ex 8.2!F7)", round(f["balance"], 2), "='Ex 8.2'!F7")
    for source, v in sorted(f["sources"].items()):
        b.check(t, f"PivotTable: {source} amount", round(v["amount"], 2),
                "=" + gpd("Sum of Amount", "Ex 8.2 Pivot", "A3", "SourceDocumentType", source))
    b.check(t, "PivotTable: JournalEntry rows", f["sources"]["JournalEntry"]["count"],
            "=" + gpd("Count of GLEntryID", "Ex 8.2 Pivot", "A3", "SourceDocumentType", "JournalEntry"), 0, COUNT)
    b.check(t, "Show Details: rows listed", len(f["je"]), "=ROWS(APJournalRows)", 0, COUNT)
    for i, (j, *_) in enumerate(items):
        b.check(t, f"reconciling item {j['voucher']} (Ex 8.2!F{13 + i})", round(-j["amount"], 2), f"='Ex 8.2'!F{13 + i}")
    b.check(t, f"ledger balance after the reconciling items (Ex 8.2!F{adj})", round(f["open_total"], 2),
            f"='Ex 8.2'!F{adj}")
    b.check(t, f"unexplained difference (Ex 8.2!F{diff})", 0, f"='Ex 8.2'!F{diff}")
    b.check(t, f"cash debited by {opening['voucher']}", round(f["cash"], 2), f"='Ex 8.2'!F{cash_row}")
    for j in cap:
        r = po_rows[j["voucher"]]
        b.check(t, f"{j['voucher']}: the invoice", j["invoice"]["number"], f"='Ex 8.2'!B{r}")
        b.check(t, f"{j['voucher']}: its open balance", round(j["invoice"]["balance"], 2), f"='Ex 8.2'!D{r}")
        b.check(t, f"{j['voucher']}: payments of the invoice", 0, f"='Ex 8.2'!E{r}", 0, COUNT)
        b.check(t, f"{j['voucher']}: its purchase order", j["po"]["number"], f"='Ex 8.2'!F{r}")
        b.check(t, f"{j['po']['number']}: created by", j["po"]["creator"]["name"], f"='Ex 8.2'!I{r}")
        b.check(t, f"{j['po']['number']}: approved by", j["po"]["approver"]["name"], f"='Ex 8.2'!K{r}")
        b.check(t, f"{j['po']['number']}: the approver's limit", j["po"]["approver"]["limit"], f"='Ex 8.2'!M{r}")


# --- Exercise 8.3 ----------------------------------------------------------------------------------------------------

def ex8_3(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b).ex3
    # (1) CustomerSegment and PaymentTerms through the Customers query into OpenInvoices.
    def keep(cols):
        return pq.select_columns(audit.table_order(b, "Customer", cols)).replace(pq.PREV, '#"Changed Type"')
    edit_step(b, "Customers", keep(["CustomerID", "CustomerName", "CreditLimit"]),
              keep(["CustomerID", "CustomerName", "CreditLimit", "PaymentTerms", "CustomerSegment"]))
    expanded = audit.table_order(b, "Customer", ["CustomerName", "CreditLimit", "PaymentTerms", "CustomerSegment"])
    edit_step(b, "OpenInvoices",
              pq.expand("Customers", ["CustomerName", "CreditLimit"]).replace(pq.PREV, '#"Merged Queries2"'),
              pq.expand("Customers", expanded).replace(pq.PREV, '#"Merged Queries2"'))
    inv = xl.retry(xl.table, wb, "OpenInvoices")
    xl.retry(lambda: inv.QueryTable.Refresh(False))
    xl.wait_ready(wb.Application)
    for c in ("PaymentTerms", "CustomerSegment"):
        assert inv.ListColumns(c) is not None

    ws = new_sheet(b, "Ex 8.3")
    title(ws, "Exercise 8.3: Customer Credit Exposure")
    pt = pivot(b, ws, "OpenInvoices", "A3", "PivotEx83")
    pt.RowAxisLayout(XL_TABULAR)
    for name in ("CustomerID", "CustomerName"):
        pt.PivotFields(name).Orientation = xl.XL_ROW
    subtotals_off(pt.PivotFields("CustomerID"))
    pt.AddDataField(pt.PivotFields("OpenBalance"), "Sum of OpenBalance", xl.XL_SUM).NumberFormat = MONEY
    pt.AddDataField(pt.PivotFields("CreditLimit"), "Max of CreditLimit", XL_MAX).NumberFormat = MONEY
    pt.PivotFields("CustomerID").AutoSort(xl.XL_DESCENDING, "Sum of OpenBalance")
    body = pt.DataBodyRange
    first, n = body.Row, body.Rows.Count
    last = first + n - 2                                   # the last customer row (the Grand Total row follows)
    assert n - 1 == f["customers"], (n, f["customers"])
    assert body.Column == 3 and pt.RowRange.Column == 1, "the PivotTable is not in columns A to D"
    rng = lambda c: f"{c}{first}:{c}{last}"  # noqa: E731
    ws.Cells(first - 1, 5).Value = "Balance % of limit"
    ws.Cells(first - 1, 5).Font.Bold = True
    ws.Range(rng("E")).Formula = f'=IF(D{first}>0,C{first}/D{first},"")'
    fmt(ws, rng("E"), "0.0%")
    for c, w in zip("ABCDE", (12, 34, 20, 20, 18)):
        ws.Columns(c).ColumnWidth = w

    # (2) the customers over their limit.
    G = 7
    for i, w in enumerate((16, 34, 16, 14, 16, 16, 12, 14, 12, 12)):
        ws.Columns(G + i).ColumnWidth = w
    heading(ws, first - 2, "(2) Customers whose balance exceeds their credit limit", G)
    header(ws, first - 1, G, ["CustomerID", "CustomerName", "CustomerSegment", "PaymentTerms", "Balance", "CreditLimit",
                              "% of limit", "Past due"])
    ov = f"G{first}"
    ws.Range(ov).Formula2 = (
        f"=LET(id,{rng('A')},nm,{rng('B')},bal,{rng('C')},lim,{rng('D')},k,bal>lim,i,FILTER(id,k),"
        "HSTACK(i,FILTER(nm,k),XLOOKUP(i,OpenInvoices[CustomerID],OpenInvoices[CustomerSegment]),"
        "XLOOKUP(i,OpenInvoices[CustomerID],OpenInvoices[PaymentTerms]),FILTER(bal,k),FILTER(lim,k),FILTER(bal/lim,k),"
        'SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[CustomerID],i,OpenInvoices[DaysPastDue],">0")))')
    n_over = len(f["over"])
    fmt(ws, f"K{first}:L{first + n_over}", MONEY)
    fmt(ws, f"M{first}:M{first + n_over}", "0.0%")
    fmt(ws, f"N{first}:N{first + n_over}", MONEY)

    # (3) concentration, and the balances by segment and by terms.
    c0 = first + n_over + 2
    heading(ws, c0, "(3) Concentration", G)
    put(ws, {f"G{c0 + 1}": "Customers with an open balance", f"K{c0 + 1}": f"=COUNT({rng('A')})",
             f"G{c0 + 2}": "Open balance", f"K{c0 + 2}": "=" + gpd("Sum of OpenBalance", "Ex 8.3", "A3"),
             f"G{c0 + 3}": "Largest customer", f"H{c0 + 3}": f"=B{first}", f"K{c0 + 3}": f"=C{first}",
             f"L{c0 + 3}": f"=K{c0 + 3}/K{c0 + 2}",
             f"G{c0 + 4}": "Five largest customers", f"K{c0 + 4}": f"=SUM(LARGE({rng('C')},SEQUENCE(5)))",
             f"L{c0 + 4}": f"=K{c0 + 4}/K{c0 + 2}",
             f"G{c0 + 5}": "Ten largest customers", f"K{c0 + 5}": f"=SUM(LARGE({rng('C')},SEQUENCE(10)))",
             f"L{c0 + 5}": f"=K{c0 + 5}/K{c0 + 2}"})
    fmt(ws, f"K{c0 + 1}", COUNT)
    fmt(ws, f"K{c0 + 2}:K{c0 + 5}", MONEY)
    fmt(ws, f"L{c0 + 3}:L{c0 + 5}", "0.0%")
    s0 = c0 + 7
    header(ws, s0, G, ["CustomerSegment", "Open balance", "Past due", "Past due %", "Customers"])
    group_formula = (
        "=LET(s,UNIQUE(OpenInvoices[{col}]),o,SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[{col}],s),"
        'p,SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[{col}],s,OpenInvoices[DaysPastDue],">0"),'
        "c,MAP(s,LAMBDA(x,ROWS(UNIQUE(FILTER(OpenInvoices[CustomerID],OpenInvoices[{col}]=x))))),"
        "SORTBY(HSTACK(s,o,p,p/o,c),{key}))")
    ws.Range(f"G{s0 + 1}").Formula2 = group_formula.format(col="CustomerSegment", key="o,-1")
    n_seg = len(f["segments"])
    t0 = s0 + n_seg + 3
    header(ws, t0, G, ["PaymentTerms", "Open balance", "Past due", "Past due %", "Customers"])
    ws.Range(f"G{t0 + 1}").Formula2 = group_formula.format(col="PaymentTerms", key='--SUBSTITUTE(s,"Net ",""),1')
    n_terms = len(f["terms"])
    for r0, n_ in ((s0, n_seg), (t0, n_terms)):
        fmt(ws, f"H{r0 + 1}:I{r0 + n_}", MONEY)
        fmt(ws, f"J{r0 + 1}:J{r0 + n_}", "0.0%")
        fmt(ws, f"K{r0 + 1}:K{r0 + n_}", COUNT)
    m0 = t0 + n_terms + 2
    put(ws, {f"G{m0}": "Open invoices whose due date does not follow the customer's PaymentTerms",
             f"M{m0}": '=SUMPRODUCT(--(OpenInvoices[DueDate]-OpenInvoices[InvoiceDate]<>--SUBSTITUTE('
                       'OpenInvoices[PaymentTerms],"Net ","")))'})
    fmt(ws, f"M{m0}", COUNT)

    # (4) the memo.
    over = f["over"]
    top = f["ranked"][0]
    largest_segment = max(f["segments"].items(), key=lambda kv: kv[1][0])
    terms = sorted(f["terms"].items(), key=lambda kv: int(kv[0].split()[-1]))
    by_rate = sorted(terms, key=lambda kv: -kv[1][1] / kv[1][0])
    worst = by_rate[0]
    assert f["mismatch"] == 0, "an invoice's due date does not follow its customer's terms"
    top5_segments = {c["segment"] for c, _ in f["ranked"][:5]}
    assert all(o["past_due"] < 0.005 for o in over), "a customer over the limit has a past-due balance"
    text_block(ws, m0 + 2, f"{MA}, requirement (4): memo to the credit manager", col=G, span=8, paragraphs=[
        f"To: the credit manager. Subject: credit exposure at {date(b.year, 12, 31).isoformat()}.",
        f"Concentration. {f['customers']} customers owe {money(f['total'])}. The receivables are spread out: the largest "
        f"customer, {top[0]['name']}, owes {money(top[1])} ({top[1] / f['total']:.1%}), the five largest hold "
        f"{f['top5']:.1%} and the ten largest {f['top10']:.1%}. "
        + (f"All five of the largest are {top5_segments.pop()} customers. " if len(top5_segments) == 1 else "")
        + f"By segment, {largest_segment[0]} customers owe the most ({money(largest_segment[1][0])}).",
        f"Customers over their limits. {word(len(over), True)} customers owe more than their credit limit: "
        + "; ".join(f"{o['name']} {money(o['balance'])} against {money(o['limit'])} ({o['segment']}, {o['terms']})"
                    for o in over)
        + ". None of them has any past-due balance: they are over the limit because of recent billing, not slow "
          "payment.",
        "Payment behavior. Past-due balances are "
        + ("concentrated in the shorter terms" if [k for k, _ in by_rate] == [k for k, _ in terms] else "uneven")
        + f": {worst[0]} customers have "
        f"{worst[1][1] / worst[1][0]:.1%} of their balance past due, against "
        + series(f"{k} {v[1] / v[0]:.1%}" for k, v in terms if k != worst[0])
        + ". Every open invoice's due date follows its customer's terms.",
        "Recommendations. (1) Review the limits of the customers over them rather than stopping their shipments: "
        "they pay on time, so raise the limits where their volume justifies it, and otherwise require approval of new "
        "orders until the balance falls. (2) Make the system block or route for approval any order that would take a "
        f"customer over its limit, since {word(len(over))} exceeded theirs unnoticed. (3) Focus collection effort on the "
        f"past-due balances of the {by_rate[0][0]} and {by_rate[1][0]} customers. (4) Watch the largest balances, which are not dangerously "
        "concentrated today but would hurt most if a large customer failed."])

    t = "8.3"
    b.check(t, "customers with an open balance (rows of the PivotTable)", f["customers"], f"='Ex 8.3'!K{c0 + 1}", 0,
            COUNT)
    b.check(t, "PivotTable total", round(f["total"], 2), f"='Ex 8.3'!K{c0 + 2}")
    for name, count in f["shared_names"].items():
        b.check(t, f"customers named {name}, kept apart by CustomerID", count,
                f'=COUNTIF(\'Ex 8.3\'!{rng("B")},"{name}")', 0, COUNT)
    b.check(t, "customers over their credit limit (rows spilled from G)", n_over, f"=ROWS('Ex 8.3'!{ov}#)", 0, COUNT)
    for o in over:
        b.check(t, f"{o['name']} (CustomerID {o['id']}): balance", round(o["balance"], 2),
                "=" + gpd("Sum of OpenBalance", "Ex 8.3", "A3", "CustomerID", o["id"], "CustomerName", o["name"]))
        b.check(t, f"{o['name']}: credit limit", round(o["limit"], 2),
                "=" + gpd("Max of CreditLimit", "Ex 8.3", "A3", "CustomerID", o["id"], "CustomerName", o["name"]))
    b.check(t, "past-due balance of the customers over their limit", 0, f"=SUM(INDEX('Ex 8.3'!{ov}#,0,8))")
    b.check(t, "largest customer", top[0]["name"], f"='Ex 8.3'!H{c0 + 3}")
    b.check(t, "its balance", round(top[1], 2), f"='Ex 8.3'!K{c0 + 3}")
    b.check(t, "share of the five largest customers", f["top5"], f"='Ex 8.3'!L{c0 + 4}", 1e-9, PCT)
    b.check(t, "share of the ten largest customers", f["top10"], f"='Ex 8.3'!L{c0 + 5}", 1e-9, PCT)
    for anchor, groups in ((f"G{s0 + 1}", f["segments"]), (f"G{t0 + 1}", f["terms"])):
        for key, (open_, due, n_cust) in sorted(groups.items()):
            look = lambda col: f"=XLOOKUP(\"{key}\",INDEX('Ex 8.3'!{anchor}#,0,1),INDEX('Ex 8.3'!{anchor}#,0,{col}))"  # noqa: E731
            b.check(t, f"{key}: open balance", round(open_, 2), look(2))
            b.check(t, f"{key}: past due", round(due, 2), look(3))
            b.check(t, f"{key}: customers", n_cust, look(5), 0, COUNT)
    b.check(t, "open invoices whose due date does not follow the terms", 0, f"='Ex 8.3'!M{m0}", 0, COUNT)


# --- Exercise 8.4 ----------------------------------------------------------------------------------------------------

def ex8_4(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b).ex4
    # (1) SupplierCategory and DueDate through the lookup queries into Payments.
    def keep(table, cols):
        return pq.select_columns(audit.table_order(b, table, cols)).replace(pq.PREV, '#"Changed Type"')
    edit_step(b, "Suppliers", keep("Supplier", ["SupplierID", "SupplierName"]),
              keep("Supplier", ["SupplierID", "SupplierName", "SupplierCategory"]))
    edit_step(b, "PurchaseInvoices", keep("PurchaseInvoice", ["PurchaseInvoiceID", "InvoiceNumber", "GrandTotal"]),
              keep("PurchaseInvoice", ["PurchaseInvoiceID", "InvoiceNumber", "DueDate", "GrandTotal"]))
    edit_step(b, "Payments",
              pq.expand("PurchaseInvoices", ["InvoiceNumber", "GrandTotal"]).replace(pq.PREV, '#"Merged Queries"'),
              pq.expand("PurchaseInvoices", ["InvoiceNumber", "DueDate", "GrandTotal"]).replace(pq.PREV,
                                                                                               '#"Merged Queries"'))
    edit_step(b, "Payments", pq.expand("Suppliers", ["SupplierName"]).replace(pq.PREV, '#"Merged Queries1"'),
              pq.expand("Suppliers", ["SupplierName", "SupplierCategory"]).replace(pq.PREV, '#"Merged Queries1"'))
    pay = xl.retry(xl.table, wb, "Payments")
    xl.retry(lambda: pay.QueryTable.Refresh(False))
    xl.wait_ready(wb.Application)
    pay.ListColumns("DueDate").DataBodyRange.NumberFormat = DATE
    xl.add_column(pay, "FiscalYear", "=YEAR([@PaymentDate])", "0")
    # (3) days after the due date.
    xl.add_column(pay, "DaysAfterDue", "=[@PaymentDate]-[@DueDate]", "0")

    ws = new_sheet(b, "Ex 8.4")
    pt = pivot(b, ws, "Payments", "A3", "PivotEx84")
    page = pt.PivotFields("FiscalYear")
    page.Orientation = xl.XL_PAGE
    page.CurrentPage = str(b.year)
    pt.PivotFields("SupplierName").Orientation = xl.XL_ROW
    pt.AddDataField(pt.PivotFields("Amount"), "Sum of Amount", xl.XL_SUM).NumberFormat = MONEY
    running = pt.AddDataField(pt.PivotFields("Amount"), "Running share of spending", xl.XL_SUM)
    running.Calculation = XL_PERCENT_RUNNING_TOTAL
    running.BaseField = "SupplierName"
    running.NumberFormat = "0.00%"
    pt.PivotFields("SupplierName").AutoSort(xl.XL_DESCENDING, "Sum of Amount")
    body = pt.DataBodyRange
    first, n = body.Row, body.Rows.Count
    last = first + n - 2
    assert body.Column == 2 and n - 1 == f["suppliers"], (body.Column, n)
    put(ws, {"E1": "FiscalYear (=YEAR([@PaymentDate]), added to the Payments Table) filters both PivotTables to one "
                   "fiscal year; Charles River's fiscal year is the calendar year."})
    ws.Range("E1").Font.Italic = True
    for c, w in zip("ABC", (36, 18, 18)):
        ws.Columns(c).ColumnWidth = w
    for c, w in zip("EFGHIJ", (44, 18, 12, 18, 12, 12)):
        ws.Columns(c).ColumnWidth = w

    # (2) concentration and categories.
    heading(ws, 3, "(2) Concentration of the spending", 5)
    rr = f"C{first}:C{last}"
    put(ws, {"E4": "Payments in the year", "F4": f"=COUNTIFS(Payments[FiscalYear],{b.year})",
             "E5": "Suppliers paid", "F5": f"=COUNTA(A{first}:A{last})",
             "E6": "Spending", "F6": "=" + gpd("Sum of Amount", "Ex 8.4", "A3"),
             "E7": "Suppliers making up 50% of spending", "F7": f'=COUNTIF({rr},"<"&0.5)+1',
             "E8": "Suppliers making up 80% of spending", "F8": f'=COUNTIF({rr},"<"&0.8)+1',
             "E9": "Suppliers making up 90% of spending", "F9": f'=COUNTIF({rr},"<"&0.9)+1',
             "E10": "Largest supplier", "F10": f"=A{first}",
             "E11": "Its share of spending", "F11": f"=B{first}/F6",
             "E12": "Its category", "F12": "=XLOOKUP(F10,Payments[SupplierName],Payments[SupplierCategory])"})
    fmt(ws, "F4:F5", COUNT)
    fmt(ws, "F6", MONEY)
    fmt(ws, "F7:F9", COUNT)
    fmt(ws, "F11", "0.00%")
    ws.Range("F4:F12").HorizontalAlignment = -4152
    cat_anchor = "E16"
    heading(ws, 13, "Spending by SupplierCategory", 5)
    pc = b.wb.PivotCaches().Create(SourceType=xl.XL_DATABASE, SourceData="Payments")
    pt2 = pc.CreatePivotTable(TableDestination=ws.Range(cat_anchor), TableName="PivotEx84Category")
    page2 = pt2.PivotFields("FiscalYear")
    page2.Orientation = xl.XL_PAGE
    page2.CurrentPage = str(b.year)
    pt2.PivotFields("SupplierCategory").Orientation = xl.XL_ROW
    pt2.AddDataField(pt2.PivotFields("Amount"), "Sum of Amount", xl.XL_SUM).NumberFormat = MONEY
    pt2.PivotFields("SupplierCategory").AutoSort(xl.XL_DESCENDING, "Sum of Amount")
    assert pt2.TableRange2.Row >= 14

    # (3) payment timing.
    t0 = 16 + len(f["categories"]) + 4
    heading(ws, t0, "(3) Payment timing", 5)
    yr = f"F{t0 + 1}"
    put(ws, {f"E{t0 + 1}": "Fiscal year", yr: b.year,
             f"E{t0 + 2}": "Payments in the year", f"F{t0 + 2}": f"=COUNTIFS(Payments[FiscalYear],{yr})",
             f"E{t0 + 3}": "Paid before the due date",
             f"F{t0 + 3}": f'=COUNTIFS(Payments[FiscalYear],{yr},Payments[DaysAfterDue],"<0")',
             f"E{t0 + 4}": "Paid on the due date",
             f"F{t0 + 4}": f"=COUNTIFS(Payments[FiscalYear],{yr},Payments[DaysAfterDue],0)",
             f"E{t0 + 5}": "Paid after the due date",
             f"F{t0 + 5}": f'=COUNTIFS(Payments[FiscalYear],{yr},Payments[DaysAfterDue],">0")',
             f"E{t0 + 6}": "Share paid after the due date, by count", f"F{t0 + 6}": f"=F{t0 + 5}/F{t0 + 2}",
             f"E{t0 + 7}": "Share paid after the due date, by value",
             f"F{t0 + 7}": f'=SUMIFS(Payments[Amount],Payments[FiscalYear],{yr},Payments[DaysAfterDue],">0")'
                           f"/SUMIFS(Payments[Amount],Payments[FiscalYear],{yr})",
             f"E{t0 + 8}": "Median days after due",
             f"F{t0 + 8}": f"=MEDIAN(FILTER(Payments[DaysAfterDue],Payments[FiscalYear]={yr}))",
             f"E{t0 + 9}": "Mean days after due",
             f"F{t0 + 9}": f"=AVERAGEIFS(Payments[DaysAfterDue],Payments[FiscalYear],{yr})",
             f"E{t0 + 10}": "Paid more than 30 days late",
             f"F{t0 + 10}": f'=COUNTIFS(Payments[FiscalYear],{yr},Payments[DaysAfterDue],">30")'})
    fmt(ws, f"F{t0 + 2}:F{t0 + 5}", COUNT)
    fmt(ws, f"F{t0 + 6}:F{t0 + 7}", "0.0%")
    fmt(ws, f"F{t0 + 8}:F{t0 + 9}", "0.0")
    fmt(ws, f"F{t0 + 10}", COUNT)
    ws.Range(f"F{t0 + 1}:F{t0 + 10}").HorizontalAlignment = -4152

    # (4) the memo.
    cats = f["categories"]
    marks = f["marks"]
    text_block(ws, t0 + 12, f"{MA}, requirement (4): memo to the treasurer", col=5, span=6, paragraphs=[
        f"To: the treasurer. Subject: supplier payments in fiscal {b.year}.",
        f"Concentration. Charles River paid {money(f['total'])} to {f['suppliers']} suppliers in {f['n']:,} payments. "
        f"Spending is not concentrated: {marks[0.5]} suppliers make up half of it, {marks[0.8]} make up 80 percent, and "
        f"{marks[0.9]} make up 90 percent, and the largest supplier, {f['top']} ({f['top_category']}), receives only "
        f"{f['top_share']:.2%}. The dependence is on categories rather than on single suppliers: {cats[0][0]} takes "
        f"{cats[0][1] / f['total']:.1%} of the spending and {cats[1][0]} {cats[1][1] / f['total']:.1%}. Supplier risk is "
        f"therefore low for any one supplier, but a disruption in {cats[0][0].lower()} would reach many suppliers at "
        "once.",
        f"Timing. {f['late']:,} payments ({f['late'] / f['n']:.1%}, holding {f['late_value']:.1%} of the value) were made "
        f"after the due date, {f['on']:,} on it, and {f['early']:,} before it. The median payment is {f['median']:.0f} "
        f"days late and the mean {f['mean']:.1f} days; {f['late30']:,} payments were more than 30 days late.",
        "What it means for cash. Paying late keeps cash in the business a few days longer, but it risks late fees, "
        "credit holds, worse prices, and strained relationships, and the payments more than 30 days late are the ones "
        "suppliers notice. Paying early gives up cash with nothing in return: the data records no early-payment "
        "discounts, so an early payment is a free loan to the supplier. Recommendation: schedule payment runs by due "
        "date, so that invoices are paid on time rather than early or late; negotiate discounts or longer terms with "
        "the largest suppliers if cash is tight; and investigate why so many payments are late, whether approval delays "
        "or cash planning."])

    t = "8.4"
    b.check(t, f"payments in fiscal {b.year}", f["n"], "='Ex 8.4'!F4", 0, COUNT)
    b.check(t, "suppliers paid (rows of the PivotTable)", f["suppliers"], "='Ex 8.4'!F5", 0, COUNT)
    b.check(t, "spending (PivotTable total)", round(f["total"], 2), "='Ex 8.4'!F6")
    for r, share in zip((7, 8, 9), (0.5, 0.8, 0.9)):
        b.check(t, f"suppliers making up {share:.0%} of spending", f["marks"][share], f"='Ex 8.4'!F{r}", 0, COUNT)
    b.check(t, "largest supplier", f["top"], "='Ex 8.4'!F10")
    b.check(t, "its share of spending", f["top_share"], "='Ex 8.4'!F11", 1e-9, PCT)
    b.check(t, "its category", f["top_category"], "='Ex 8.4'!F12")
    for cat, amount in cats:
        b.check(t, f"spending on {cat}", round(amount, 2),
                "=" + gpd("Sum of Amount", "Ex 8.4", cat_anchor, "SupplierCategory", cat))
    b.check(t, "paid before the due date", f["early"], f"='Ex 8.4'!F{t0 + 3}", 0, COUNT)
    b.check(t, "paid on the due date", f["on"], f"='Ex 8.4'!F{t0 + 4}", 0, COUNT)
    b.check(t, "paid after the due date", f["late"], f"='Ex 8.4'!F{t0 + 5}", 0, COUNT)
    b.check(t, "share paid after the due date, by count", f["late"] / f["n"], f"='Ex 8.4'!F{t0 + 6}", 1e-9, PCT)
    b.check(t, "share paid after the due date, by value", f["late_value"], f"='Ex 8.4'!F{t0 + 7}", 1e-9, PCT)
    b.check(t, "median days after due", f["median"], f"='Ex 8.4'!F{t0 + 8}", 1e-9, "0.0")
    b.check(t, "mean days after due", f["mean"], f"='Ex 8.4'!F{t0 + 9}", 1e-9, "0.000")
    b.check(t, "paid more than 30 days late", f["late30"], f"='Ex 8.4'!F{t0 + 10}", 0, COUNT)


# --- Exercise 8.5 ----------------------------------------------------------------------------------------------------

PO_FLAGS = {"SelfApproved": "=[@CreatedByEmployeeID]=[@ApprovedByEmployeeID]",
            "AboveLimit": "=[@OrderTotal]>[@ApproverLimit]",
            "AfterTermination": '=AND([@ApproverTerminationDate]<>"",[@ApproverTerminationDate]<[@OrderDate])'}
FLAG_KEYS = {"SelfApproved": "self", "AboveLimit": "above", "AfterTermination": "term"}


def ex8_5(b: ExerciseBuild) -> None:
    wb, fx = b.wb, facts(b)
    f = fx.ex5
    # (1) the purchase orders with their approvers and creators.
    xl.add_query(wb, "Approvers", nav(b, 74, "Employee", extra=[
        ("Removed Other Columns", pq.select_columns(audit.table_order(
            b, "Employee", ["EmployeeID", "EmployeeName", "JobTitle", "MaxApprovalAmount", "TerminationDate"])))]))
    approver_cols = audit.table_order(b, "Employee", ["EmployeeName", "JobTitle", "MaxApprovalAmount", "TerminationDate"])
    xl.add_query(wb, "POApprovals", nav(b, 33, "PurchaseOrder", extra=[
        ("Merged Queries", pq.merge("Approvers", "ApprovedByEmployeeID", "EmployeeID", "Approvers")),
        ("Expanded Approvers", pq.expand("Approvers", approver_cols)),
        ("Renamed Columns", pq.rename([("EmployeeName", "ApproverName"), ("JobTitle", "ApproverTitle"),
                                       ("TerminationDate", "ApproverTerminationDate"),
                                       ("MaxApprovalAmount", "ApproverLimit")])),
        ("Merged Queries1", pq.merge("Approvers", "CreatedByEmployeeID", "EmployeeID", "Approvers")),
        ("Expanded Approvers1", pq.expand("Approvers", ["EmployeeName"])),
        ("Renamed Columns1", pq.rename([("EmployeeName", "CreatorName")]))]))
    # (3) the supplier invoices with their approvers.
    xl.add_query(wb, "InvoiceApprovals", nav(b, 37, "PurchaseInvoice", extra=[
        ("Merged Queries", pq.merge("Approvers", "ApprovedByEmployeeID", "EmployeeID", "Approvers")),
        ("Expanded Approvers", pq.expand("Approvers", audit.table_order(
            b, "Employee", ["EmployeeName", "JobTitle", "MaxApprovalAmount"]))),
        ("Renamed Columns", pq.rename([("EmployeeName", "ApproverName"), ("JobTitle", "ApproverTitle"),
                                       ("MaxApprovalAmount", "ApproverLimit")]))]))
    # (4) the requisitions.
    xl.add_query(wb, "Requisitions", nav(b, 32, "PurchaseRequisition"))

    ws = new_sheet(b, "Ex 8.5")
    wr = xl.sheet(wb, "Ex 8.5 Requisitions", after=ws)
    wp = xl.sheet(wb, "Ex 8.5 Payments", after=wr)
    ap = load(b, "Approvers", "Approvers")
    ap.ListColumns("TerminationDate").DataBodyRange.NumberFormat = DATE
    po = load(b, "POApprovals", "POApprovals")
    po.ListColumns("OrderTotal").DataBodyRange.NumberFormat = MONEY
    po.ListColumns("ApproverTerminationDate").DataBodyRange.NumberFormat = DATE
    # (2) the flags and the risk score; (6) the year and sequence number of each PONumber.
    for name, formula in PO_FLAGS.items():
        xl.add_column(po, name, formula)
    xl.add_column(po, "RiskScore", "=[@SelfApproved]+[@AboveLimit]+[@AfterTermination]", "0")
    xl.add_column(po, "POYear", "=--MID([@PONumber],4,4)", "0")
    xl.add_column(po, "POSeq", "=--RIGHT([@PONumber],6)", "0")
    ia = load(b, "InvoiceApprovals", "InvoiceApprovals")
    ia.ListColumns("GrandTotal").DataBodyRange.NumberFormat = MONEY
    xl.add_column(ia, "AboveLimit", "=[@GrandTotal]>[@ApproverLimit]")
    rq = load(b, "Requisitions", "Requisitions")
    xl.add_column(rq, "RequisitionValue", "=[@Quantity]*[@EstimatedUnitCost]", MONEY)
    # (5) near-duplicate payments, with the formulas the exercise gives.
    pay = xl.table(wb, "Payments")
    xl.add_column(pay, "SameAmount", "=COUNTIFS([SupplierID],[@SupplierID],[Amount],[@Amount])>1")
    xl.add_column(pay, "SameInvoice", "=COUNTIFS([SupplierID],[@SupplierID],[Amount],[@Amount],"
                                      "[PurchaseInvoiceID],[@PurchaseInvoiceID])>1")
    xl.wait_ready(wb.Application)

    # --- Ex 8.5: purchase orders and supplier invoices ---------------------------------------------------------------
    title(ws, "Exercise 8.5: Testing Purchasing and Payment Controls")
    for c, w in zip("ABCDEFGHIJKLMN", (18, 12, 14, 20, 20, 22, 12, 13, 12, 11, 15, 10, 90, 20)):
        ws.Columns(c).ColumnWidth = w
    heading(ws, 3, "(1) and (2) Purchase order approvals (POApprovals)")
    put(ws, {"A4": "Purchase orders", "D4": "=ROWS(POApprovals[PONumber])",
             "A5": "Approved by the chief financial officer", "D5": f'=COUNTIF(POApprovals[ApproverTitle],"{CFO}")',
             "E5": "=D5/D4"})
    for i, name in enumerate(PO_FLAGS):
        put(ws, {f"A{6 + i}": name, f"D{6 + i}": f"=COUNTIF(POApprovals[{name}],TRUE)"})
    for s in range(4):
        put(ws, {f"A{9 + s}": f"Orders with a RiskScore of {s}", f"D{9 + s}": f"=COUNTIF(POApprovals[RiskScore],{s})"})
    fmt(ws, "D4:D12", COUNT)
    fmt(ws, "E5", "0.00%")
    d0 = 14
    ws.Cells(d0, 1).Value = "Flagged orders, sorted by RiskScore, pasted as values with a disposition (as in Tutorial 8.3)"
    ws.Cells(d0, 1).Font.Italic = True
    cols = ["PONumber", "OrderDate", "OrderTotal", "CreatorName", "ApproverName", "ApproverTitle", "ApproverLimit",
            "ApproverTerminationDate", "SelfApproved", "AboveLimit", "AfterTermination", "RiskScore"]
    header(ws, d0 + 1, 1, cols + ["Disposition", "Design or operation"])
    pick = ",".join(f'IF(POApprovals[{c}]="","",POApprovals[{c}])' if c == "ApproverTerminationDate"
                    else f"POApprovals[{c}]" for c in cols)
    anchor = f"A{d0 + 2}"
    ws.Range(anchor).Formula2 = (f"=LET(k,POApprovals[RiskScore]>=1,SORTBY(FILTER(HSTACK({pick}),k),"
                                 "FILTER(POApprovals[RiskScore],k),-1,FILTER(POApprovals[PONumber],k),1))")
    xl.wait_ready(wb.Application)
    rows = spill_values(ws, anchor)
    assert len(rows) == len(f["flagged"]), (len(rows), len(f["flagged"]))
    for i, row in enumerate(rows):
        weakness, text = f["dispositions"][row[0]]
        put(ws, {f"M{d0 + 2 + i}": text, f"N{d0 + 2 + i}": weakness})
    d_last = d0 + 1 + len(rows)
    ws.Range(anchor).AddComment("Pasted as values from a FILTER of the orders with a RiskScore of 1 or more, as Tutorial "
                                "8.3 Step 5 does; the dispositions are the builder's model answers.")
    fmt(ws, f"B{d0 + 2}:B{d_last}", DATE)
    fmt(ws, f"C{d0 + 2}:C{d_last}", MONEY)
    fmt(ws, f"G{d0 + 2}:G{d_last}", MONEY)
    fmt(ws, f"H{d0 + 2}:H{d_last}", DATE)
    ws.Range(f"M{d0 + 2}:M{d_last}").WrapText = True
    ws.Range(f"A{d0 + 2}:N{d_last}").VerticalAlignment = -4160
    ws.Rows(f"{d0 + 2}:{d_last}").AutoFit()

    i0 = d_last + 2
    heading(ws, i0, "(3) Supplier invoices approved by anyone other than the chief financial officer (InvoiceApprovals)")
    put(ws, {f"A{i0 + 1}": "Supplier invoices", f"D{i0 + 1}": "=ROWS(InvoiceApprovals[InvoiceNumber])",
             f"A{i0 + 2}": "Approved by the chief financial officer",
             f"D{i0 + 2}": f'=COUNTIF(InvoiceApprovals[ApproverTitle],"{CFO}")',
             f"A{i0 + 3}": "Approved by anyone else", f"D{i0 + 3}": f"=D{i0 + 1}-D{i0 + 2}",
             f"A{i0 + 4}": "Of those, above the approver's limit", f"D{i0 + 4}": f"=COUNTIF(INDEX(A{i0 + 7}#,0,8),TRUE)"})
    fmt(ws, f"D{i0 + 1}:D{i0 + 4}", COUNT)
    inv_cols = ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "GrandTotal", "ApproverName", "ApproverTitle",
                "ApproverLimit", "AboveLimit"]
    header(ws, i0 + 6, 1, inv_cols + ["", "", "", "", "Does the approver's role belong in invoice approval?"])
    ws.Range(f"A{i0 + 7}").Formula2 = (
        f"=LET(k,InvoiceApprovals[ApproverTitle]<>\"{CFO}\",SORTBY(FILTER(HSTACK("
        + ",".join(f"InvoiceApprovals[{c}]" for c in inv_cols) + "),k),FILTER(InvoiceApprovals[PurchaseInvoiceID],k),1))")
    other = f["other"]
    i_last = i0 + 6 + len(other)
    roles = {}
    for o in other:
        a = o["approver"]
        roles.setdefault(a["title"], (a, []))[1].append(o)
    role_text = {}
    for t_, (a, invs) in roles.items():
        above = all(o["total"] > a["limit"] for o in invs)
        within = all(o["total"] <= a["limit"] for o in invs)
        cap = all(o["id"] in {j["invoice_id"] for j in fx.ex2["reclass"]} for o in invs)
        if a["limit"] == 0:
            role_text[t_] = (f"No. {audit.article(t_.lower()).capitalize()} in {a['family']} has no purchasing or "
                             "accounting role and no approval authority (limit $0); the invoices need a proper "
                             "approval after the fact.")
        elif within and a["family"] not in ("Purchasing and Procurement", "Finance and Accounting"):
            role_text[t_] = (f"No. The amounts are within the {money(a['limit'])} limit, but {audit.article(t_.lower())} "
                             f"in {a['family']} is outside purchasing and accounting: operations staff can confirm "
                             "receipt, not approve payment.")
        elif above and cap:
            role_text[t_] = (f"No, not for these. The {t_.lower()} also created and approved their purchase orders "
                             f"(Exercise 8.2), so approving the invoices removes the last independent check, and both "
                             f"are far above the {money(a['limit'])} limit.")
        else:
            raise AssertionError(f"no role assessment fits the approver {a['name']} ({t_})")
    rt = i0 + 7
    put(ws, {f"P{i0 + 6}": "ApproverTitle", f"Q{i0 + 6}": "Assessment"})
    bold(ws, f"P{i0 + 6}:Q{i0 + 6}")
    for k, (t_, text) in enumerate(sorted(role_text.items())):
        put(ws, {f"P{rt + k}": t_, f"Q{rt + k}": text})
    ws.Columns("P").ColumnWidth = 22
    ws.Columns("Q").ColumnWidth = 60
    ws.Range(f"Q{rt}:Q{rt + len(role_text) - 1}").WrapText = True
    ws.Range(f"M{i0 + 7}").Formula2 = f"=XLOOKUP(INDEX(A{i0 + 7}#,0,6),P{rt}:P{rt + len(role_text) - 1},Q{rt}:Q{rt + len(role_text) - 1})"
    ws.Range(f"P{i0 + 5}").Value = "Model answer (3): the assessment of each approver's role, looked up in column M"
    ws.Range(f"P{i0 + 5}").Font.Bold = True
    fmt(ws, f"C{i0 + 7}:C{i_last}", DATE)
    fmt(ws, f"D{i0 + 7}:D{i_last}", MONEY)
    fmt(ws, f"G{i0 + 7}:G{i_last}", MONEY)
    ws.Range(f"M{i0 + 7}:M{i_last}").WrapText = True
    ws.Range(f"A{i0 + 7}:Q{i_last}").VerticalAlignment = -4160

    # --- Ex 8.5 Requisitions --------------------------------------------------------------------------------------------
    title(wr, "Exercise 8.5 (4): Requisition amounts around $5,000")
    for c, w in zip("ABCDEFGHIJKLMN", (20, 12, 12, 18, 20, 14, 18, 12, 16, 9, 10, 12, 14, 34)):
        wr.Columns(c).ColumnWidth = w
    header(wr, 3, 1, ["Band", "From", "Up to", "Requisitions"])
    for k in range(BAND_COUNT):
        low = BAND_FROM + k * BAND_WIDTH
        r = 4 + k
        put(wr, {f"A{r}": f"{low:,} to {low + BAND_WIDTH - 0.01:,.2f}", f"B{r}": low, f"C{r}": low + BAND_WIDTH - 0.01,
                 f"D{r}": f'=COUNTIFS(Requisitions[RequisitionValue],">="&B{r},'
                          f'Requisitions[RequisitionValue],"<"&B{r}+{BAND_WIDTH})'})
    band_last = 3 + BAND_COUNT
    fmt(wr, f"B4:C{band_last}", MONEY)
    fmt(wr, f"D4:D{band_last}", COUNT)
    shape = wr.Shapes.AddChart2(-1, xl.XL_COLUMN_CLUSTERED, wr.Range("F3").Left, wr.Range("F3").Top, 520, 260)
    chart = shape.Chart
    chart.SetSourceData(wr.Range(f"A3:A{band_last},D3:D{band_last}"))
    chart.HasTitle = True
    chart.ChartTitle.Text = "Requisitions by $50 band of RequisitionValue"
    chart.HasLegend = False
    e0 = band_last + 8
    put(wr, {f"A{e0}": "Band examined, from", f"B{e0}": BAND_EXAMINED})
    fmt(wr, f"B{e0}", MONEY)
    bold(wr, f"A{e0}")
    lcols = ["RequisitionNumber", "RequestDate", "RequestedBy", "Requester", "RequesterTitle", "ApprovedBy",
             "Approver", "ApprovedDate", "Status", "ItemID", "Quantity", "EstimatedUnitCost", "RequisitionValue",
             "Consecutive numbers with the same value"]
    header(wr, e0 + 2, 1, lcols)
    look = lambda col: f"XLOOKUP(id,Requisitions[RequisitionID],Requisitions[{col}])"  # noqa: E731
    list_anchor = f"A{e0 + 3}"
    wr.Range(list_anchor).Formula2 = (
        f"=LET(k,(Requisitions[RequisitionValue]>=B{e0})*(Requisitions[RequisitionValue]<B{e0}+{BAND_WIDTH}),"
        "id,SORT(FILTER(Requisitions[RequisitionID],k)),v," + look("RequisitionValue") + ","
        "rq," + look("RequestedByEmployeeID") + ",ap," + look("ApprovedByEmployeeID") + ",ad," + look("ApprovedDate") + ","
        "same,(DROP(id,1)=DROP(id,-1)+1)*(DROP(v,1)=DROP(v,-1)),run,VSTACK(0,same)+VSTACK(same,0),"
        "HSTACK(" + look("RequisitionNumber") + "," + look("RequestDate") + ",rq,"
        "XLOOKUP(rq,Approvers[EmployeeID],Approvers[EmployeeName],\"\"),XLOOKUP(rq,Approvers[EmployeeID],Approvers[JobTitle],\"\"),"
        "IF(ap=0,\"\",ap),XLOOKUP(ap,Approvers[EmployeeID],Approvers[EmployeeName],\"(no approver)\"),IF(ad=0,\"\",ad),"
        + look("Status") + "," + look("ItemID") + "," + look("Quantity") + "," + look("EstimatedUnitCost") + ",v,"
        "IF(run>0,\"Run of consecutive numbers, same value\",\"\")))")
    band = f["band"]
    l_last = e0 + 2 + len(band)
    fmt(wr, f"B{e0 + 3}:B{l_last}", DATE)
    fmt(wr, f"H{e0 + 3}:H{l_last}", DATE)
    fmt(wr, f"L{e0 + 3}:M{l_last}", MONEY)
    s0 = l_last + 2
    put(wr, {f"A{s0}": "Requisitions in the band", f"D{s0}": f"=ROWS({list_anchor}#)",
             f"A{s0 + 1}": "Converted to PO", f"D{s0 + 1}": f'=COUNTIF(INDEX({list_anchor}#,0,9),"Converted to PO")',
             f"A{s0 + 2}": "Without an approver", f"D{s0 + 2}": f'=COUNTIF(INDEX({list_anchor}#,0,7),"(no approver)")',
             f"A{s0 + 3}": "Requisitions without an approver, all amounts",
             f"D{s0 + 3}": "=COUNTBLANK(Requisitions[ApprovedByEmployeeID])",
             f"A{s0 + 4}": "In runs of consecutive numbers with the same value",
             f"D{s0 + 4}": f'=COUNTIF(INDEX({list_anchor}#,0,14),"Run*")',
             f"A{s0 + 5}": "Twice the largest neighboring band?",
             f"D{s0 + 5}": f"=D{4 + (BAND_EXAMINED - BAND_FROM) // BAND_WIDTH}>=2*MAX(D{3 + (BAND_EXAMINED - BAND_FROM) // BAND_WIDTH},"
                           f"D{5 + (BAND_EXAMINED - BAND_FROM) // BAND_WIDTH})"})
    fmt(wr, f"D{s0}:D{s0 + 4}", COUNT)
    a0 = s0 + 7
    heading(wr, a0, "Approval limits in the Employee table (Approvers)")
    header(wr, a0 + 1, 1, ["EmployeeID", "EmployeeName", "", "JobTitle", "", "MaxApprovalAmount", "Requisitions approved"])
    wr.Range(f"A{a0 + 2}").Formula2 = (
        "=LET(e,FILTER(Approvers[EmployeeID],(Approvers[MaxApprovalAmount]=5000)+(COUNTIF(Requisitions[ApprovedByEmployeeID],"
        "Approvers[EmployeeID])>0)),x,EXPAND(\"\",ROWS(e),1,\"\"),SORTBY(HSTACK(e,XLOOKUP(e,Approvers[EmployeeID],"
        "Approvers[EmployeeName]),x,XLOOKUP(e,Approvers[EmployeeID],Approvers[JobTitle]),x,XLOOKUP(e,Approvers[EmployeeID],"
        "Approvers[MaxApprovalAmount]),COUNTIF(Requisitions[ApprovedByEmployeeID],e)),XLOOKUP(e,Approvers[EmployeeID],"
        "Approvers[MaxApprovalAmount]),-1))")
    n_lim = len({e["id"] for e in f["five"]} | set(f["approvers"]))
    fmt(wr, f"F{a0 + 2}:F{a0 + 1 + n_lim}", MONEY)
    fmt(wr, f"G{a0 + 2}:G{a0 + 1 + n_lim}", COUNT)
    unapproved = [r for r in band if r[3] is None]
    bands = f["bands"]
    k_ex = (BAND_EXAMINED - BAND_FROM) // BAND_WIDTH
    five = f["five"]
    groups = f["groups"]
    req_approvers = sorted(f["approvers"].items(), key=lambda kv: -kv[1])
    # the wording of the runs, tested against the data
    assert bands[k_ex] >= 2 * max(bands[k_ex - 1], bands[k_ex + 1])
    assert {r[0] for r in unapproved} == {r[0] for r in band if r[3] is None} and len(unapproved) == f["unapproved"]
    assert all(r[4] == "Converted to PO" for r in band)
    assert len({len(g) for g in groups}) == 1 and all(r[6][5:] == "01-01" for g in groups for r in g)
    assert len({(r[8], r[9]) for g in groups for r in g}) == 1, "the runs differ in quantity or unit cost"
    assert all(len({r[7] for r in g}) == len(g) for g in groups), "a run repeats an item"
    assert all(g[-1][3] is not None and all(r[3] is None for r in g[:-1]) for g in groups), "approvals in the runs"
    run_approvers = {fx.staff[g[-1][3]]["title"] for g in groups}
    assert len(run_approvers) == 1
    next_day = all(date.fromisoformat(g[-1][10][:10]) == date.fromisoformat(g[-1][6][:10]).replace(day=2)
                   for g in groups)
    requesters = [len({r[2] for r in g}) for g in groups]
    who = ("different requesters" if all(n == len(g) for n, g in zip(requesters, groups)) else
           "mostly different requesters")
    limits_above = all(fx.staff[k]["limit"] > 5000 for k in f["approvers"])
    text_block(wr, a0 + 3 + n_lim, f"{MA}, requirement (4)", [
        f"The ${BAND_EXAMINED:,} to ${BAND_EXAMINED + BAND_WIDTH - 0.01:,.2f} band holds {bands[k_ex]} requisitions, "
        f"against {bands[k_ex - 1]} and {bands[k_ex + 1]} in the bands on either side (counts from ${BAND_FROM:,}: "
        + ", ".join(str(x) for x in bands) + "), twice any neighbor. All " + f"{len(band)} were converted to purchase "
        f"orders, and {word(len(unapproved))} of them have no approver at all (" + ", ".join(r[1] for r in unapproved)
        + "), the requisitions of Exercise 2.5; no requisition outside the band lacks an approver.",
        f"The band holds {word(len(groups))} runs of {word(len(groups[0]))} consecutive requisition numbers with the same value: "
        + " and ".join(f"{g[0][1]} to {g[-1][1]}" for g in groups)
        + f", each dated January 1 and each for {groups[0][0][8]:,.0f} units at ${groups[0][0][9]:,.2f} "
        f"({money(groups[0][0][5])}), for different items and {who}. In each run only the last requisition has an "
        f"approver, the {run_approvers.pop().lower()}" + (", the next day" if next_day else "") + ".",
        f"Approval limits: {word(len(five))} employees have a limit of $5,000.00, the only limit just above the band: "
        + series(f"{e['name']} ({e['title']})" for e in five) + ". Requisitions are approved by "
        + series(f"the {fx.staff[k]['title'].lower()} ({n:,})" for k, n in req_approvers)
        + (", all with limits well above $5,000" if limits_above else "")
        + ". Amounts clustered just under a threshold, runs of identical consecutive requisitions, and requisitions "
        "converted to orders without any approval are the signs of a purchase split to stay below a review level. "
        "Follow up: ask whether requisitions under $5,000 are treated as needing no approval, obtain the purchase "
        f"orders behind the {word(len(unapproved))} unapproved requisitions and the needs behind each run, and require an approval before "
        "any requisition becomes an order (a design fix)."])

    # --- Ex 8.5 Payments: near-duplicates and the gap test --------------------------------------------------------------
    title(wp, "Exercise 8.5 (5) and (6): Near-duplicate payments and purchase order numbers")
    for c, w in zip("ABCDEFGH", (40, 30, 14, 16, 12, 18, 14, 14)):
        wp.Columns(c).ColumnWidth = w
    heading(wp, 3, "(5) Near-duplicate payments (Payments Table, SameAmount and SameInvoice)")
    put(wp, {"A4": "Payments flagged SameAmount", "C4": "=COUNTIF(Payments[SameAmount],TRUE)",
             "A5": "Payments flagged SameInvoice", "C5": "=COUNTIF(Payments[SameInvoice],TRUE)",
             "A6": "Pairs of same-supplier, same-amount payments", "C6": "=C4/2",
             "A7": "Pairs at most 30 days apart", "C7": '=COUNTIF(INDEX(A11#,0,7),"<=30")/2'})
    fmt(wp, "C4:C7", COUNT)
    header(wp, 10, 1, ["SupplierID", "SupplierName", "Amount", "PaymentNumber", "PaymentDate", "PurchaseInvoiceID",
                       "Days from the other payment"])
    wp.Range("A11").Formula2 = (
        "=LET(k,Payments[SameAmount],s,FILTER(Payments[SupplierID],k),a,FILTER(Payments[Amount],k),"
        "n,FILTER(Payments[PaymentNumber],k),d,FILTER(Payments[PaymentDate],k),"
        'o,MAXIFS(Payments[PaymentDate],Payments[SupplierID],s,Payments[Amount],a,Payments[PaymentNumber],"<>"&n),'
        "SORTBY(HSTACK(s,FILTER(Payments[SupplierName],k),a,n,d,FILTER(Payments[PurchaseInvoiceID],k),ABS(d-o)),"
        "s,1,a,1,d,1))")
    n_dup = f["same"]
    fmt(wp, f"C11:C{10 + n_dup}", MONEY)
    fmt(wp, f"E11:E{10 + n_dup}", DATE)
    fmt(wp, f"G11:G{10 + n_dup}", "0")
    put(wp, {"E3": MA + ", requirement (5)"})
    bold(wp, "E3")
    rng5 = wp.Range("E4:H8")
    rng5.Merge()
    rng5.WrapText = True
    rng5.VerticalAlignment = -4160
    wp.Range("E4").Value = (
        f"SameAmount flags {n_dup} payments, {f['pairs']} pairs of payments to the same supplier for the same amount "
        f"(no group is larger than two; {f['within30']} pairs are at most 30 days apart). SameInvoice flags "
        f"{word(f['same_invoice']) if f['same_invoice'] else 'none'}: no pair also pays the same invoice. The difference shows that every pair pays two "
        "different invoices for the same amount, repeat purchases at the same price, and that no invoice was paid "
        "twice. The duplicate payment test is clean; the close pairs deserve only a glance at their invoices.")
    g0 = 12 + n_dup + 2
    heading(wp, g0, "(6) Gap test on the purchase order numbers (POApprovals, POYear and POSeq)")
    header(wp, g0 + 1, 1, ["Year", "Orders", "Smallest number", "Largest number", "Largest - smallest + 1", "Missing",
                           "Continues from the year before"])
    for k, g in enumerate(f["gaps"]):
        r = g0 + 2 + k
        put(wp, {f"A{r}": g["year"], f"B{r}": f"=COUNTIF(POApprovals[POYear],A{r})",
                 f"C{r}": f"=MINIFS(POApprovals[POSeq],POApprovals[POYear],A{r})",
                 f"D{r}": f"=MAXIFS(POApprovals[POSeq],POApprovals[POYear],A{r})", f"E{r}": f"=D{r}-C{r}+1",
                 f"F{r}": f"=E{r}-B{r}", f"G{r}": "" if k == 0 else f"=C{r}=D{r - 1}+1"})
    g_last = g0 + 1 + len(f["gaps"])
    fmt(wp, f"B{g0 + 2}:F{g_last}", COUNT)
    wp.Range(f"A{g0 + 2}:A{g_last}").HorizontalAlignment = -4131
    gaps = f["gaps"]
    row = text_block(wp, g_last + 2, f"{MA}, requirement (6)", [
        "; ".join(f"{g['year']}: numbers {g['low']:,} to {g['high']:,}, {g['n']:,} orders" for g in gaps)
        + ". In every year the count equals the range, so no number is missing, and each year starts where the year "
        "before ended: the sequence runs on across years instead of restarting in January, which a reader of the "
        "PONumber prefix might not expect."])

    # --- the memo (7), on Ex 8.5 -------------------------------------------------------------------------------------
    fl = f["flags"]
    sc = f["scores"]
    cap = fx.ex2["reclass"]
    term = [o for o in f["flagged"] if o["flags"]["term"]]
    assert set(roles) == {"Product Analyst", "Production Supervisor", "Purchasing Manager"}, roles
    assert len(cap) == 2 and len({o["approver"]["name"] for o in term}) == 1
    text_block(ws, i_last + 2, f"{MA}, requirement (7): memo to the chief audit executive", [
        f"Exceptions. Of {f['orders']:,} purchase orders, the chief financial officer approved {f['cfo']:,} "
        f"({f['cfo'] / f['orders']:.1%}). {sc[2] + sc[1]} orders fail at least one test: {fl['self']} were approved "
        f"by their creator, {fl['above']} exceed the approver's limit, and {fl['term']} were approved after the "
        f"approver's termination ({sc[2]} fail two tests, {sc[1]} one). They include the two note-financed capital "
        "purchases (" + ", ".join(f"{j['po']['number']} {money(j['po']['total'])}" for j in cap)
        + f"), created and approved by the purchasing manager with a {money(cap[0]['po']['approver']['limit'])} "
        f"limit, and {word(len(term))} orders approved by "
        f"{term[0]['approver']['name']}, {audit.article(term[0]['approver']['title'].lower())} who left on "
        f"{term[0]['approver']['terminated']}. Of {f['invoices']:,} supplier invoices, {word(len(f['other']))} were approved "
        "by someone other than the chief financial officer: a product analyst with no approval authority, a "
        "production supervisor outside the purchasing and accounting roles, and the purchasing manager, on the two "
        f"capital invoices. The requisitions cluster just below $5,000, with {word(f['unapproved'])} converted to orders "
        "without approval.",
        "Design or operation. The design is weak: the systems accept an approval by the person who created the "
        "document, by someone whose limit is $0 or below the amount, and by a terminated employee, and they convert "
        "requisitions to orders without an approval. Approval limits exist in the Employee table but nothing enforces "
        "them. Operation failed too: managers approved above their limits, and the access of departed employees was "
        "not removed. Because every exception got through a control that should have stopped it, fixing the design "
        "matters more than retraining.",
        f"Clean results. The near-duplicate test flags {f['same']} payments in {f['pairs']} pairs of the same supplier "
        "and amount, but none pays the same invoice, so no invoice was paid twice. Purchase order numbers have no gaps in "
        "any year and continue across years.",
        "Follow-up. Obtain the approvals of the two capital purchases and their notes; find out who used the "
        "terminated employee's login; vouch the self-approved and above-limit orders to receipts and invoices; ask "
        "whether a $5,000 practice exempts requisitions from approval; and recommend system controls that block "
        "self-approval, enforce limits, require an approved requisition, and disable users at termination."])

    t = "8.5"
    b.check(t, "purchase orders", f["orders"], "='Ex 8.5'!D4", 0, COUNT)
    b.check(t, "approved by the chief financial officer", f["cfo"], "='Ex 8.5'!D5", 0, COUNT)
    for i, name in enumerate(PO_FLAGS):
        b.check(t, f"{name} flags", fl[FLAG_KEYS[name]], f"='Ex 8.5'!D{6 + i}", 0, COUNT)
    for s in range(4):
        b.check(t, f"orders with a RiskScore of {s}", sc[s], f"='Ex 8.5'!D{9 + s}", 0, COUNT)
    b.check(t, "flagged orders with a disposition", len(f["flagged"]), f"=COUNTA('Ex 8.5'!M{d0 + 2}:M{d_last})", 0, COUNT)
    b.check(t, "flagged orders pasted (RiskScore 1 or more)", len(f["flagged"]),
            f'=COUNTIF(\'Ex 8.5\'!L{d0 + 2}:L{d_last},">=1")', 0, COUNT)
    b.check(t, f"orders approved after termination by {term[0]['approver']['name']}", len(term),
            f"=COUNTIFS(POApprovals[AfterTermination],TRUE,POApprovals[ApproverName],\"{term[0]['approver']['name']}\")",
            0, COUNT)
    for j in cap:
        b.check(t, f"{j['po']['number']} is self-approved and above the limit (RiskScore)", 2,
                f"=XLOOKUP(\"{j['po']['number']}\",POApprovals[PONumber],POApprovals[RiskScore])", 0, COUNT)
    b.check(t, "supplier invoices", f["invoices"], f"='Ex 8.5'!D{i0 + 1}", 0, COUNT)
    b.check(t, "supplier invoices approved by the chief financial officer", f["invoices"] - len(other),
            f"='Ex 8.5'!D{i0 + 2}", 0, COUNT)
    b.check(t, "supplier invoices approved by anyone else (rows listed)", len(other), f"=ROWS('Ex 8.5'!A{i0 + 7}#)", 0,
            COUNT)
    b.check(t, "of those, above the approver's limit", sum(1 for o in other if o["total"] > o["approver"]["limit"]),
            f"='Ex 8.5'!D{i0 + 4}", 0, COUNT)
    b.check(t, "their total", round(sum(o["total"] for o in other), 2), f"=SUM(INDEX('Ex 8.5'!A{i0 + 7}#,0,4))")
    b.check(t, "each has a role assessment", len(other), f"=COUNTA('Ex 8.5'!M{i0 + 7}:M{i_last})", 0, COUNT)
    for k in range(BAND_COUNT):
        low = BAND_FROM + k * BAND_WIDTH
        b.check(t, f"requisitions of {low:,} to {low + BAND_WIDTH - 0.01:,.2f}", bands[k], f"='Ex 8.5 Requisitions'!D{4 + k}",
                0, COUNT)
    b.check(t, "requisitions listed for the band examined", len(band), f"=ROWS('Ex 8.5 Requisitions'!{list_anchor}#)", 0,
            COUNT)
    b.check(t, "of them, converted to PO", sum(1 for r in band if r[4] == "Converted to PO"),
            f"='Ex 8.5 Requisitions'!D{s0 + 1}", 0, COUNT)
    b.check(t, "of them, without an approver", len(unapproved), f"='Ex 8.5 Requisitions'!D{s0 + 2}", 0, COUNT)
    b.check(t, "requisitions without an approver, all amounts", f["unapproved"], f"='Ex 8.5 Requisitions'!D{s0 + 3}", 0,
            COUNT)
    b.check(t, "requisitions in runs of consecutive numbers with the same value", len(f["runs"]),
            f"='Ex 8.5 Requisitions'!D{s0 + 4}", 0, COUNT)
    b.check(t, "employees with a 5,000 approval limit", len(five), "=COUNTIF(Approvers[MaxApprovalAmount],5000)", 0, COUNT)
    b.check(t, "payments flagged SameAmount", f["same"], "='Ex 8.5 Payments'!C4", 0, COUNT)
    b.check(t, "payments flagged SameInvoice", f["same_invoice"], "='Ex 8.5 Payments'!C5", 0, COUNT)
    b.check(t, "pairs at most 30 days apart", f["within30"], "='Ex 8.5 Payments'!C7", 0, COUNT)
    for k, g in enumerate(gaps):
        r = g0 + 2 + k
        b.check(t, f"PO-{g['year']}: orders", g["n"], f"='Ex 8.5 Payments'!B{r}", 0, COUNT)
        b.check(t, f"PO-{g['year']}: smallest number", g["low"], f"='Ex 8.5 Payments'!C{r}", 0, COUNT)
        b.check(t, f"PO-{g['year']}: largest number", g["high"], f"='Ex 8.5 Payments'!D{r}", 0, COUNT)
        b.check(t, f"PO-{g['year']}: missing numbers", 0, f"='Ex 8.5 Payments'!F{r}", 0, COUNT)


# --- Exercise 8.6 ----------------------------------------------------------------------------------------------------

def ex8_6(b: ExerciseBuild) -> None:
    wb, fx = b.wb, facts(b)
    f = fx.ex6
    # (1) the promotions, with the approver's name (the Employees query of Tutorial 8.3).
    xl.add_query(wb, "Promotions", nav(b, 7, "PromotionProgram", extra=[
        ("Merged Queries", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", pq.expand("Employees", ["EmployeeName", "JobTitle"])),
        ("Renamed Columns", pq.rename([("EmployeeName", "ApproverName"), ("JobTitle", "ApproverTitle")]))]))
    # (2) invoice lines with their order dates and their promotion's dates.
    xl.add_query(wb, "InvoiceHeaders", nav(b, 16, "SalesInvoice", {"FreightAmount": "type number"}))
    xl.add_query(wb, "Orders", nav(b, 9, "SalesOrder"))
    xl.add_query(wb, "InvoiceLines", nav(b, 17, "SalesInvoiceLine", {"Discount": "type number"}, extra=[
        ("Merged Queries", pq.merge("InvoiceHeaders", "SalesInvoiceID", "SalesInvoiceID", "InvoiceHeaders")),
        ("Expanded InvoiceHeaders", pq.expand("InvoiceHeaders", ["InvoiceNumber", "InvoiceDate", "SalesOrderID"])),
        ("Merged Queries1", pq.merge("Orders", "SalesOrderID", "SalesOrderID", "Orders")),
        ("Expanded Orders", pq.expand("Orders", ["OrderDate"])),
        ("Merged Queries2", pq.merge("Promotions", "PromotionID", "PromotionID", "Promotions")),
        ("Expanded Promotions", pq.expand("Promotions", ["EffectiveStartDate", "EffectiveEndDate"]))]))
    # (3) the pending override requests.
    xl.add_query(wb, "PendingOverrides", nav(b, 8, "PriceOverrideApproval", extra=[
        ("Filtered Rows", 'Table.SelectRows({prev}, each [Status] = "Pending")')]))
    # (4) the price lists, their lines, and the order lines with their list and order date.
    xl.add_query(wb, "PriceLists", nav(b, 5, "PriceList"))
    xl.add_query(wb, "PriceListLines", nav(b, 6, "PriceListLine"))
    xl.add_query(wb, "OrderLines", nav(b, 10, "SalesOrderLine", {"Discount": "type number"}, extra=[
        ("Merged Queries", pq.merge("PriceListLines", "PriceListLineID", "PriceListLineID", "PriceListLines")),
        ("Expanded PriceListLines", 'Table.ExpandTableColumn({prev}, "PriceListLines", {"PriceListID", "UnitPrice"}, '
                                    '{"PriceListID", "ListUnitPrice"})'),
        ("Merged Queries1", pq.merge("PriceLists", "PriceListID", "PriceListID", "PriceLists")),
        ("Expanded PriceLists", 'Table.ExpandTableColumn({prev}, "PriceLists", {"EffectiveEndDate"}, {"ListEndDate"})'),
        ("Merged Queries2", pq.merge("Orders", "SalesOrderID", "SalesOrderID", "Orders")),
        ("Expanded Orders", pq.expand("Orders", ["OrderDate", "CustomerID"]))]))

    ws = new_sheet(b, "Ex 8.6")
    wl = xl.sheet(wb, "Ex 8.6 Price Lists", after=ws)
    pr = load(b, "Promotions", "Promotions")
    for c in ("EffectiveStartDate", "EffectiveEndDate", "ApprovedDate"):
        pr.ListColumns(c).DataBodyRange.NumberFormat = DATE
    xl.add_column(pr, "EndOnOrBeforeStart", "=[@EffectiveEndDate]<=[@EffectiveStartDate]")
    il = load(b, "InvoiceLines", "InvoiceLines")
    for c in ("InvoiceDate", "OrderDate", "EffectiveStartDate", "EffectiveEndDate"):
        il.ListColumns(c).DataBodyRange.NumberFormat = DATE
    xl.add_column(il, "DiscountAmount", "=[@Quantity]*[@UnitPrice]*[@Discount]", MONEY)
    xl.add_column(il, "OrderedInWindow", '=IF([@PromotionID]="","",AND([@OrderDate]>=[@EffectiveStartDate],'
                                         '[@OrderDate]<=[@EffectiveEndDate]))')
    load(b, "PendingOverrides", "PendingOverrides")
    pl = load(b, "PriceLists", "PriceLists")
    for c in ("EffectiveStartDate", "EffectiveEndDate", "ApprovedDate"):
        pl.ListColumns(c).DataBodyRange.NumberFormat = DATE
    xl.add_column(pl, "Flagged", '=OR([@Status]="Expired",[@EffectiveEndDate]<[@EffectiveStartDate])')
    load(b, "PriceListLines", "PriceListLines")
    ol = load(b, "OrderLines", "OrderLines")
    for c in ("OrderDate", "ListEndDate"):
        ol.ListColumns(c).DataBodyRange.NumberFormat = DATE
    xl.add_column(ol, "OrderYear", "=YEAR([@OrderDate])", "0")
    xl.add_column(ol, "AfterListEnd", '=IF([@PriceListID]="",FALSE,[@OrderDate]>[@ListEndDate])')
    xl.wait_ready(wb.Application)

    # --- Ex 8.6: promotions and pending overrides ------------------------------------------------------------------------
    title(ws, "Exercise 8.6: Testing Pricing Controls")
    for c, w in zip("ABCDEFGHIJ", (16, 18, 34, 14, 16, 16, 18, 18, 22, 14)):
        ws.Columns(c).ColumnWidth = w
    heading(ws, 3, "(1) Promotions whose EffectiveEndDate is on or before their EffectiveStartDate (Promotions)")
    header(ws, 4, 1, ["PromotionID", "PromotionCode", "PromotionName", "DiscountPct", "EffectiveStartDate",
                      "EffectiveEndDate", "ApprovedByEmployeeID", "ApproverName", "ApproverTitle", "ApprovedDate"])
    pcols = ["PromotionID", "PromotionCode", "PromotionName", "DiscountPct", "EffectiveStartDate", "EffectiveEndDate",
             "ApprovedByEmployeeID", "ApproverName", "ApproverTitle", "ApprovedDate"]
    ws.Range("A5").Formula2 = ("=FILTER(HSTACK(" + ",".join(f"Promotions[{c}]" for c in pcols)
                               + "),Promotions[EndOnOrBeforeStart])")
    flagged = f["flagged"]
    n_f = len(flagged)
    fmt(ws, f"D5:D{4 + n_f}", "0%")
    fmt(ws, f"E5:F{4 + n_f}", DATE)
    fmt(ws, f"J5:J{4 + n_f}", DATE)
    p0 = 4 + n_f + 2
    heading(ws, p0, "(2) Their invoice lines, with each line's OrderDate from Orders (InvoiceLines)")
    header(ws, p0 + 1, 1, ["PromotionID", "Lines", "Ordered outside the dates", "Discount", "First OrderDate",
                           "Last OrderDate", "Last InvoiceDate"])
    ws.Range(f"A{p0 + 2}").Formula2 = (
        "=LET(id,FILTER(Promotions[PromotionID],Promotions[EndOnOrBeforeStart]),HSTACK(id,"
        "COUNTIFS(InvoiceLines[PromotionID],id),COUNTIFS(InvoiceLines[PromotionID],id,InvoiceLines[OrderedInWindow],FALSE),"
        "SUMIFS(InvoiceLines[DiscountAmount],InvoiceLines[PromotionID],id),"
        "MINIFS(InvoiceLines[OrderDate],InvoiceLines[PromotionID],id),MAXIFS(InvoiceLines[OrderDate],InvoiceLines[PromotionID],id),"
        "MAXIFS(InvoiceLines[InvoiceDate],InvoiceLines[PromotionID],id)))")
    pt_ = p0 + 2 + n_f
    put(ws, {f"A{pt_}": "Total", f"B{pt_}": f"=SUM(B{p0 + 2}:B{pt_ - 1})", f"C{pt_}": f"=SUM(C{p0 + 2}:C{pt_ - 1})",
             f"D{pt_}": f"=SUM(D{p0 + 2}:D{pt_ - 1})",
             f"A{pt_ + 1}": "Promotion lines of every promotion ordered outside its promotion's dates",
             f"C{pt_ + 1}": "=COUNTIF(InvoiceLines[OrderedInWindow],FALSE)"})
    bold(ws, f"A{pt_}:D{pt_}")
    fmt(ws, f"B{p0 + 2}:C{pt_ + 1}", COUNT)
    fmt(ws, f"D{p0 + 2}:D{pt_}", MONEY)
    fmt(ws, f"E{p0 + 2}:G{pt_ - 1}", DATE)

    o0 = pt_ + 3
    heading(ws, o0, "(3) Pending override requests (PendingOverrides) and the invoice lines of their SalesOrderLineIDs")
    put(ws, {f"A{o0 + 1}": "Pending requests", f"C{o0 + 1}": "=ROWS(PendingOverrides[PriceOverrideApprovalID])"})
    ocols = ["PriceOverrideApprovalID", "SalesOrderLineID", "InvoiceNumber", "Quantity", "UnitPrice",
             "ReferenceUnitPrice", "ApprovedUnitPrice", "PricingMethod", "PriceOverrideApprovalID on the line",
             "Billed below reference"]
    header(ws, o0 + 3, 1, ocols)
    oa = f"A{o0 + 4}"
    ws.Range(oa).Formula2 = (
        "=LET(k,ISNUMBER(XMATCH(InvoiceLines[SalesOrderLineID],PendingOverrides[SalesOrderLineID])),"
        "sol,FILTER(InvoiceLines[SalesOrderLineID],k),q,FILTER(InvoiceLines[Quantity],k),p,FILTER(InvoiceLines[UnitPrice],k),"
        "ref,XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[ReferenceUnitPrice]),"
        "SORTBY(HSTACK(XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[PriceOverrideApprovalID]),sol,"
        "FILTER(InvoiceLines[InvoiceNumber],k),q,p,ref,"
        "XLOOKUP(sol,PendingOverrides[SalesOrderLineID],PendingOverrides[ApprovedUnitPrice]),"
        'FILTER(InvoiceLines[PricingMethod],k),FILTER(IF(InvoiceLines[PriceOverrideApprovalID]="","(blank)",'
        "InvoiceLines[PriceOverrideApprovalID]),k),(ref-p)*q),FILTER(InvoiceLines[InvoiceNumber],k),1))")
    pend = f["pending"]
    o_last = o0 + 3 + len(pend)
    put(ws, {f"A{o_last + 1}": "Total billed below the reference prices", f"J{o_last + 1}": f"=SUM(INDEX({oa}#,0,10))",
             f"A{o_last + 2}": "Lines billed at the pending ApprovedUnitPrice",
             f"J{o_last + 2}": f"=SUM(--(INDEX({oa}#,0,5)=INDEX({oa}#,0,7)))"})
    fmt(ws, f"D{o0 + 4}:D{o_last}", "0.00")
    fmt(ws, f"E{o0 + 4}:G{o_last}", MONEY)
    fmt(ws, f"J{o0 + 4}:J{o_last + 1}", MONEY)
    fmt(ws, f"J{o_last + 2}", COUNT)
    bold(ws, f"A{o_last + 1}:J{o_last + 1}")

    # --- Ex 8.6 Price Lists ------------------------------------------------------------------------------------------
    title(wl, "Exercise 8.6 (4) and (5): Price lists")
    for c, w in zip("ABCDEFGHIJKLM", (14, 36, 14, 16, 16, 16, 12, 14, 16, 16, 12, 14, 14)):
        wl.Columns(c).ColumnWidth = w
    heading(wl, 3, "(4) Price lists that are Expired or end before they start (PriceLists[Flagged])")
    header(wl, 4, 1, ["PriceListID", "PriceListName", "ScopeType", "CustomerSegment", "EffectiveStartDate",
                      "EffectiveEndDate", "Status", "Later lists for its scope"])
    wl.Range("A5").Formula2 = (
        "=LET(k,PriceLists[Flagged],id,FILTER(PriceLists[PriceListID],k),seg,FILTER(PriceLists[CustomerSegment],k),"
        "sc,FILTER(PriceLists[ScopeType],k),e,FILTER(PriceLists[EffectiveEndDate],k),"
        "HSTACK(id,FILTER(PriceLists[PriceListName],k),sc,seg,FILTER(PriceLists[EffectiveStartDate],k),e,"
        'FILTER(PriceLists[Status],k),COUNTIFS(PriceLists[ScopeType],sc,PriceLists[CustomerSegment],seg,'
        'PriceLists[EffectiveEndDate],">"&e)))')
    fl = f["flagged_lists"]
    n_l = len(fl)
    fmt(wl, f"E5:F{4 + n_l}", DATE)
    years = list(range(b.year - 2, b.year + 1))
    g0 = 4 + n_l + 2
    wl.Cells(g0, 1).Value = "Order lines dated after their price list's EffectiveEndDate (OrderLines[AfterListEnd]), by year"
    wl.Cells(g0, 1).Font.Italic = True
    header(wl, g0 + 1, 1, ["PriceListID"] + [str(y) for y in years] + ["Lines", "LineTotal"])
    yrange = ",".join(str(y) for y in years)
    wl.Range(f"A{g0 + 2}").Formula2 = (
        f"=LET(id,FILTER(PriceLists[PriceListID],PriceLists[Flagged]),c,COUNTIFS(OrderLines[PriceListID],id,"
        f"OrderLines[OrderYear],{{{yrange}}},OrderLines[AfterListEnd],TRUE),HSTACK(id,c,BYROW(c,LAMBDA(r,SUM(r))),"
        "SUMIFS(OrderLines[LineTotal],OrderLines[PriceListID],id,OrderLines[AfterListEnd],TRUE)))")
    gt = g0 + 2 + n_l
    ncol = len(years) + 3
    put(wl, {f"A{gt}": "Total"})
    for c in range(2, ncol + 1):
        col = audit.letter(c)
        put(wl, {f"{col}{gt}": f"=SUM({col}{g0 + 2}:{col}{gt - 1})"})
    put(wl, {f"A{gt + 1}": "All order lines after their list's end", f"{audit.letter(ncol - 1)}{gt + 1}":
             "=COUNTIF(OrderLines[AfterListEnd],TRUE)",
             f"{audit.letter(ncol)}{gt + 1}": "=SUMIFS(OrderLines[LineTotal],OrderLines[AfterListEnd],TRUE)"})
    fmt(wl, f"B{g0 + 2}:{audit.letter(ncol - 1)}{gt + 1}", COUNT)
    fmt(wl, f"{audit.letter(ncol)}{g0 + 2}:{audit.letter(ncol)}{gt + 1}", MONEY)
    bold(wl, f"A{gt}:{audit.letter(ncol)}{gt}")
    u0 = gt + 3
    wl.Cells(u0, 1).Value = "Active price lists that no order line uses"
    wl.Cells(u0, 1).Font.Italic = True
    header(wl, u0 + 1, 1, ["PriceListID", "PriceListName", "ScopeType", "CustomerSegment", "EffectiveStartDate",
                           "EffectiveEndDate", "Price list lines"])
    ua = f"A{u0 + 2}"
    wl.Range(ua).Formula2 = (
        '=LET(k,(PriceLists[Status]="Active")*(COUNTIF(OrderLines[PriceListID],PriceLists[PriceListID])=0),'
        "FILTER(HSTACK(PriceLists[PriceListID],PriceLists[PriceListName],PriceLists[ScopeType],PriceLists[CustomerSegment],"
        "PriceLists[EffectiveStartDate],PriceLists[EffectiveEndDate],COUNTIF(PriceListLines[PriceListID],"
        "PriceLists[PriceListID])),k))")
    unused = f["unused"]
    u_last = u0 + 1 + len(unused)
    fmt(wl, f"E{u0 + 2}:F{u_last}", DATE)
    c0 = u_last + 2
    heading(wl, c0, "(5) Order lines of customers with their own price list, priced by another method")
    ccols = ["SalesOrderLineID", "OrderDate", "CustomerID", "ItemID", "PricingMethod", "Cited PriceListID",
             "Cited list price", "UnitPrice", "Own PriceListID", "Own list price", "Equals own list",
             "Equals cited list"]
    header(wl, c0 + 1, 1, ccols)
    ca = f"A{c0 + 2}"
    wl.Range(ca).Formula2 = (
        '=LET(cl,FILTER(PriceLists[CustomerID],PriceLists[ScopeType]="Customer"),'
        'k,ISNUMBER(XMATCH(OrderLines[CustomerID],cl))*(OrderLines[PricingMethod]<>"Customer Price List")'
        '*(OrderLines[PricingMethod]<>"Approved Override"),'
        "c,FILTER(OrderLines[CustomerID],k),it,FILTER(OrderLines[ItemID],k),up,FILTER(OrderLines[UnitPrice],k),"
        "cp,FILTER(OrderLines[ListUnitPrice],k),"
        'own,XLOOKUP(c,FILTER(PriceLists[CustomerID],PriceLists[ScopeType]="Customer"),'
        'FILTER(PriceLists[PriceListID],PriceLists[ScopeType]="Customer")),'
        "op,MAP(own,it,LAMBDA(l,i,XLOOKUP(1,(PriceListLines[PriceListID]=l)*(PriceListLines[ItemID]=i),"
        "PriceListLines[UnitPrice]))),"
        "SORTBY(HSTACK(FILTER(OrderLines[SalesOrderLineID],k),FILTER(OrderLines[OrderDate],k),c,it,"
        "FILTER(OrderLines[PricingMethod],k),FILTER(OrderLines[PriceListID],k),cp,up,own,op,up=op,up=cp),"
        "FILTER(OrderLines[SalesOrderLineID],k),1))")
    own = f["own"]
    c_last = c0 + 1 + len(own)
    fmt(wl, f"B{c0 + 2}:B{c_last}", DATE)
    fmt(wl, f"G{c0 + 2}:H{c_last}", MONEY)
    fmt(wl, f"J{c0 + 2}:J{c_last}", MONEY)
    cust_name, cust_segment = f["customer"]
    exp_lists = {x["id"]: x for x in fl}
    cited = exp_lists.get(own[0]["cited"])
    assert cited is not None and len({o["cited"] for o in own}) == 1 and len({o["customer"] for o in own}) == 1
    stale = [o for o in own if o["date"] > cited["end"]]
    backwards = [x for x in fl if x["end"] < x["start"]]
    assert all(x["status"] == "Expired" for x in fl) and f["later"] == 0
    assert all(u["segment"] == "Design Trade" and u["scope"] == "Segment" for u in unused)
    row = text_block(wl, c_last + 2, f"{MA}, requirement (5)", [
        f"{word(len(own), True)} order lines ({', '.join(str(o['sol']) for o in own)}) belong to customer "
        f"{own[0]['customer']}, {cust_name} ({cust_segment}), which has its own list {own[0]['own_list']}. They are "
        f"recorded under {own[0]['method']} and cite list {cited['id']}, the {cited['segment']} segment list, which "
        f"ended on {cited['end']}. Their UnitPrice equals the customer's own list ("
        + ", ".join(f"{o['price']:,.2f}" for o in own) + "), not the list they cite ("
        + ", ".join(f"{o['cited_price']:,.2f}" for o in own) + "). The customer paid its contract price, so nothing "
        "was overcharged or undercharged; the pricing record is wrong: it names a list that did not set the price"
        + (f", and for the lines of {' and '.join(sorted({o['date'][:4] for o in stale}))} a list that had already "
           "expired" if stale else "")
        + ". No other customer with its own list has lines priced another way."])
    row = text_block(wl, row, f"{MA}, requirement (4)", [
        "; ".join(f"{'L' if i == 0 else 'l'}ist {x['id']} ({x['name']}) ends {x['end']}" for i, x in enumerate(fl))
        + f": all {word(len(fl))} are Expired"
        + (", " + " and ".join(f"list {x['id']}" for x in backwards) + " even ends before it starts" if backwards else "")
        + f", and none has a later list for its segment. Yet {f['after']:,} order lines dated after the lists' end "
        f"dates ({money(f['after_total'])}) were priced from them: " + "; ".join(
            f"list {x['id']}: " + ", ".join(f"{f['grid'][(x['id'], y)]:,} in {y}" for y in years if f["grid"][(x["id"], y)])
            for x in fl)
        + f". The system prices from lists that have expired. Lists {series(x['id'] for x in unused)} are "
        "Active copies of the Design Trade list, with no lines, that price nothing: clutter that makes it harder to see "
        "which list is in force."])

    # --- the classification (6) and the memo (7), on Ex 8.6 -------------------------------------------------------------
    pt_rows = f["flagged"]
    lines_total = sum(f["by"][p["id"]]["n"] for p in pt_rows)
    disc_total = sum(f["by"][p["id"]]["discount"] for p in pt_rows)
    below = sum(p["below"] for p in pend)
    n_req = len({p["id"] for p in pend})
    assert all(p["price"] == p["approved"] and p["approval"] is None for p in pend)
    months = sorted({int(f["by"][p["id"]][k][5:7]) for p in pt_rows for k in ("first", "last")})
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                   "November", "December"]
    ordered_in = " and ".join(month_names[m - 1] for m in months)
    list_ids = series(x["id"] for x in fl)
    k0 = o_last + 4
    heading(ws, k0, f"{MA}, requirement (6): design or operation")
    header(ws, k0 + 1, 1, ["Exception", "", "", "Design", "Operation", "Why"])
    classes = [
        (f"Promotions {series(p['id'] for p in pt_rows)}: end dates on or before their start dates",
         "Yes", "Yes",
         "The system accepts an end date that is not after the start date (design), and the sales manager approved "
         "the promotions that way on their start dates; their discount was then granted on every collection line "
         f"ordered in {ordered_in} (operation)."),
        (f"{word(n_req, True)} pending override requests, billed at their ApprovedUnitPrice on "
         f"{len(pend)} invoice lines", "Yes", "Yes",
         "An order line can carry the price of an override that is still Pending, under a price-list PricingMethod "
         "and with no PriceOverrideApprovalID (design); nobody approved or rejected the requests (operation)."),
        (f"Expired price lists {list_ids} pricing {f['after']:,} order lines after their end dates", "Yes", "Yes",
         "The system prices from expired lists and accepts a list that ends before it starts (design); nobody "
         "renewed or replaced the segment lists (operation)."),
        (f"Lists {series(x['id'] for x in unused)}: Active copies with no lines", "Yes", "",
         "Duplicate master data that nothing uses: a weakness in how price lists are set up and retired."),
        (f"Customer {own[0]['customer']}'s lines citing list {cited['id']}", "Yes", "",
         "The price is right, but the record names the wrong list: the system does not check that the cited list "
         "set the price."),
    ]
    width = sum(ws.Columns(c).ColumnWidth for c in "FGHIJ")
    for k, (exc, design, op, why) in enumerate(classes):
        r = k0 + 2 + k
        put(ws, {f"A{r}": exc, f"D{r}": design, f"E{r}": op, f"F{r}": why})
        ws.Range(f"A{r}:C{r}").Merge()
        ws.Range(f"F{r}:J{r}").Merge()
        ws.Range(f"A{r}:J{r}").WrapText = True
        ws.Range(f"A{r}:J{r}").VerticalAlignment = -4160
        ws.Rows(r).RowHeight = min(409, 15 * (math.ceil(len(why) * 1.12 / width) + 0.4))
    text_block(ws, k0 + 3 + len(classes), f"{MA}, requirement (7): memo to the sales manager and the controller", [
        "To: the sales manager and the controller. Subject: pricing controls, fiscal "
        f"{b.year - 2} to {b.year}.",
        f"Promotions. Promotions {series(p['id'] for p in pt_rows)}, the {pt_rows[0]['pct']:.0%} collection "
        "promotions of each spring, were entered with end dates on or before their start dates and approved that way. "
        f"All {lines_total} of their invoice lines ({money(disc_total)} of discount) were ordered outside the recorded "
        f"dates, in {ordered_in}. The discounts were probably intended, but no valid record authorizes them.",
        f"Override requests. {word(n_req, True)} price override requests are still Pending, yet their order "
        f"lines were billed at the pending ApprovedUnitPrice on {word(len(pend))} invoice lines, "
        f"{money(below)} below the reference prices, under a price-list pricing method with no approval recorded.",
        f"Price lists. {word(len(fl), True)} segment lists have expired with no successor, but "
        f"{f['after']:,} order lines worth {money(f['after_total'])} were priced from them after their end dates"
        + (f"; {word(len(backwards))} of them ends before it starts" if backwards else "")
        + f". {word(len(unused), True)} Active copies of the Design Trade list are unused. Customer "
        f"{own[0]['customer']}'s contract prices were recorded as if they came from the {cited['segment']} segment list.",
        "Recommendations. Reject promotions and price lists whose end date is not after the start date; block "
        "pricing from expired lists, and renew or retire the segment lists; allow an override price only after the "
        "request is approved, and link the approval to the line; remove the unused copies; and review the promotion "
        "and price-list setups each year before they take effect. Most exceptions are design weaknesses: the system "
        "let them through, so the fixes belong in the system, with a periodic review as the detective control."])

    t = "8.6"
    b.check(t, "promotions flagged EndOnOrBeforeStart", n_f, "=COUNTIF(Promotions[EndOnOrBeforeStart],TRUE)", 0, COUNT)
    b.check(t, "rows listed in (1)", n_f, "=ROWS('Ex 8.6'!A5#)", 0, COUNT)
    approvers = {p["approver"]["name"] for p in flagged}
    assert len(approvers) == 1
    b.check(t, f"flagged promotions approved by {flagged[0]['approver']['name']}", n_f,
            f"=COUNTIF(INDEX('Ex 8.6'!A5#,0,8),\"{flagged[0]['approver']['name']}\")", 0, COUNT)
    b.check(t, "flagged promotions approved on their start date", sum(1 for p in flagged if p["approved"] == p["start"]),
            "=SUM(--(INDEX('Ex 8.6'!A5#,0,10)=INDEX('Ex 8.6'!A5#,0,5)))", 0, COUNT)
    for k, p in enumerate(flagged):
        r = p0 + 2 + k
        s = f["by"][p["id"]]
        b.check(t, f"{p['code']}: invoice lines", s["n"], f"='Ex 8.6'!B{r}", 0, COUNT)
        b.check(t, f"{p['code']}: lines ordered outside the dates", s["outside"], f"='Ex 8.6'!C{r}", 0, COUNT)
        b.check(t, f"{p['code']}: discount", s["discount"], f"='Ex 8.6'!D{r}")
    b.check(t, "flagged promotions: lines", lines_total, f"='Ex 8.6'!B{pt_}", 0, COUNT)
    b.check(t, "flagged promotions: discount", disc_total, f"='Ex 8.6'!D{pt_}")
    b.check(t, "promotion lines of every promotion ordered outside its dates", f["outside_all"], f"='Ex 8.6'!C{pt_ + 1}",
            0, COUNT)
    b.check(t, "pending override requests", n_req, f"='Ex 8.6'!C{o0 + 1}", 0, COUNT)
    b.check(t, "invoice lines of their SalesOrderLineIDs", len(pend), f"=ROWS('Ex 8.6'!{oa}#)", 0, COUNT)
    b.check(t, "lines billed at the pending ApprovedUnitPrice", sum(1 for p in pend if p["price"] == p["approved"]),
            f"='Ex 8.6'!J{o_last + 2}", 0, COUNT)
    b.check(t, "lines with a blank PriceOverrideApprovalID", sum(1 for p in pend if p["approval"] is None),
            f"=COUNTIF(INDEX('Ex 8.6'!{oa}#,0,9),\"(blank)\")", 0, COUNT)
    b.check(t, "billed below the reference prices", below, f"='Ex 8.6'!J{o_last + 1}")
    b.check(t, "price lists flagged", n_l, "=ROWS('Ex 8.6 Price Lists'!A5#)", 0, COUNT)
    b.check(t, "later lists for the flagged lists' scopes", f["later"], f"=SUM(INDEX('Ex 8.6 Price Lists'!A5#,0,8))", 0,
            COUNT)
    for k, x in enumerate(fl):
        for j, y in enumerate(years):
            b.check(t, f"list {x['id']}: order lines of {y} after its end", f["grid"][(x["id"], y)],
                    f"='Ex 8.6 Price Lists'!{audit.letter(2 + j)}{g0 + 2 + k}", 0, COUNT)
    b.check(t, "order lines after their list's end", f["after"], f"='Ex 8.6 Price Lists'!{audit.letter(ncol - 1)}{gt}",
            0, COUNT)
    b.check(t, "their LineTotal", round(f["after_total"], 2), f"='Ex 8.6 Price Lists'!{audit.letter(ncol)}{gt}")
    b.check(t, "all order lines after their list's end (every one on a flagged list)", f["after"],
            f"='Ex 8.6 Price Lists'!{audit.letter(ncol - 1)}{gt + 1}", 0, COUNT)
    b.check(t, "active price lists no order line uses", len(unused), f"=ROWS('Ex 8.6 Price Lists'!{ua}#)", 0, COUNT)
    b.check(t, "their price list lines", f["unused_lines"], f"=SUM(INDEX('Ex 8.6 Price Lists'!{ua}#,0,7))", 0, COUNT)
    b.check(t, "customer-list lines priced by another method", len(own), f"=ROWS('Ex 8.6 Price Lists'!{ca}#)", 0, COUNT)
    b.check(t, "of them, priced at the customer's own list", sum(1 for o in own if o["price"] == o["own_price"]),
            f"=SUM(--INDEX('Ex 8.6 Price Lists'!{ca}#,0,11))", 0, COUNT)
    b.check(t, "of them, priced at the list they cite", sum(1 for o in own if o["price"] == o["cited_price"]),
            f"=SUM(--INDEX('Ex 8.6 Price Lists'!{ca}#,0,12))", 0, COUNT)


EXERCISES = [("8.1", ex8_1), ("8.2", ex8_2), ("8.3", ex8_3), ("8.4", ex8_4), ("8.5", ex8_5), ("8.6", ex8_6)]
