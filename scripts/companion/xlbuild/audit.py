"""AuditAnalytics.xlsx: the workbook Guided Tutorials 8.1 to 8.3 build.

Each function applies one tutorial's steps to the workbook as the previous tutorial left it: the same queries (with the
Power Query Editor's step names), worksheets, cell addresses, formulas, names, and formats the tutorial text gives.
Where a step only shows the reader something (a filter applied and cleared, an entry number typed and typed back), the
end state is built. Each tutorial adds its checks to the Solution Notes: the results its checkpoint states, as live
formulas against values computed here from CharlesRiver.sqlite (read-only), independently of Excel.

What the builder decides where the text leaves a choice (the companion file says so where a reader would look):
  - Tutorial 8.2 Step 7 draws the confirmation sample with Excel's own RANDARRAY and pastes it as values, as the step
    says; the draw is frozen in the file, a cell note on Confirmations!I4 says so, and no check depends on it.
  - The worksheets the text leaves unnamed (the PivotTables of Tutorials 8.2 and 8.3 and the Show Details sheet) get
    the names in UNNAMED.
  - The dispositions and the workpaper entries are the builder's model answers, written from the data.
  - Tutorial 8.1 Step 4 copies the header row with the four payments (A10 holds the header), so the Disposition
    column of Step 4d has a heading.
  - Tutorial 8.1 Step 6h: Excel orders a chart's series by their columns, so the series from D1:D10 and B1:B10 come
    out as Expected, then Actual, and Clustered Column - Line would draw Expected as the columns. The builder sets
    the end state the step describes and fig-08-03 shows: Actual as columns, Expected as a line.
  - Tutorial 8.2 Step 3a: the typed as-of date gets the format yyyy-mm-dd, as fig-08-05 shows it (Excel's default
    for a typed ISO date is m/d/yyyy).
  - Tutorial 8.3 Step 5c pastes values; the builder also keeps the number formats, so dates stay readable.
"""

from __future__ import annotations

import math
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from functools import cached_property
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import db_uri  # noqa: E402
from xlbuild import pq, xl  # noqa: E402
from xlbuild.notes import Check  # noqa: E402

FILE = "AuditAnalytics.xlsx"
MONEY, COUNT, PCT, MADF = "#,##0.00", "#,##0", "0.00%", "0.00000"
XL_VISIBLE = 12                                   # xlCellTypeVisible

# Accounts the tutorials name by AccountID (asserted against the chart of accounts).
CASH, AR, ALLOWANCE, BAD_DEBT = 2, 3, 4, 74
ACCOUNT_NUMBERS = {CASH: "1010", AR: "1020", ALLOWANCE: "1030", BAD_DEBT: "6170"}
STRATA = [0, 1000, 10000, 50000, 100000]          # Tutorial 8.1 Step 3
LARGE = 50000                                     # Tutorial 8.1 Step 4: the top two strata
BUCKETS = [(-9999, "Current"), (1, "1-30 days"), (31, "31-60 days"), (61, "61-90 days"), (91, "Over 90 days")]
KEY_ITEM, SAMPLE = 50000, 20                      # Tutorial 8.2 Step 7
FLAGS = {"Weekend": "=WEEKDAY([@CreatedDate],2)>5",            # Tutorial 8.3, tbl-08-04
         "Backdated": "=INT([@CreatedDate])>[@PostingDate]",
         "SelfApproved": "=[@CreatedByEmployeeID]=[@ApprovedByEmployeeID]",
         "AboveLimit": "=[@TotalAmount]>[@ApproverLimit]",
         "RoundAmount": "=MOD([@TotalAmount],1000)=0"}
RISK_SCORE = "=[@Weekend]+[@Backdated]+[@SelfApproved]+[@AboveLimit]+[@RoundAmount]"
MAD_RANGES = [(0.006, "Close conformity"), (0.012, "Acceptable conformity"),        # tbl-08-01
              (0.015, "Marginally acceptable conformity"), (math.inf, "Nonconformity")]
WP_LABELS = ["Objective", "Source", "Population check", "Procedure", "Parameters", "Results",
             "Exceptions and disposition", "Conclusion", "Prepared by", "Reviewed by"]
UNNAMED = {"ar_pivot": "AR by Source",            # Tutorial 8.2 Step 6a: "place it on a new worksheet"
           "ar_details": "AR Details",            # Tutorial 8.2 Step 6d: Show Details' new worksheet
           "je_creators": "JE by Creator",        # Tutorial 8.3 Step 4a
           "je_scores": "JE by Score"}            # Tutorial 8.3 Step 4c
PREPARED = "Accounting Analytics companion file: replace with your name and the date."


def conformity(value: float) -> str:
    return next(label for limit, label in MAD_RANGES if value < limit)


CONFORMITY = ('=IF({c}<0.006,"Close conformity",IF({c}<0.012,"Acceptable conformity",'
              'IF({c}<0.015,"Marginally acceptable conformity","Nonconformity")))')


def lead_digit(amount: float) -> int:
    """The first significant digit, as =--LEFT(TEXT(x,"0.00000000E+00"),1) returns it."""
    return int(f"{amount:.8E}"[0])


def mad(counts: Counter) -> float:
    n = sum(counts.values())
    return sum(abs(counts[d] / n - math.log10(1 + 1 / d)) for d in range(1, 10)) / 9


def round_even(x: float, places: int = 2) -> float:
    """Power Query's Number.Round(x, places): half to even."""
    return float(Decimal(repr(x)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN))


def money(x: float) -> str:
    return f"${x:,.2f}"


def article(noun: str) -> str:
    return ("an " if noun[0] in "aeiou" else "a ") + noun


def iso(d: str) -> date:
    return date.fromisoformat(d[:10])


class Facts:
    """The values the tutorials' results must reproduce, from CharlesRiver.sqlite (read-only)."""

    def __init__(self, year: int):
        self.year = year
        self.end = date(year, 12, 31)                 # the as-of date (Tutorial 8.2 Step 3)
        self.before = f"{year + 1}-01-01"             # the "before" date of every date filter
        con = sqlite3.connect(db_uri(), uri=True)
        self.q = lambda sql, *args: con.execute(sql, args).fetchall()
        for account_id, number in ACCOUNT_NUMBERS.items():
            got = self.q("SELECT AccountNumber FROM Account WHERE AccountID = ?", account_id)[0][0]
            assert str(got) == number, f"AccountID {account_id} is account {got}, not {number}"

    # --- Tutorial 8.1 ----------------------------------------------------------------------------------------------
    @cached_property
    def payments(self) -> list[dict]:
        rows = self.q("SELECT d.PaymentNumber, d.PaymentDate, d.SupplierID, d.PurchaseInvoiceID, d.Amount, "
                      "pi.InvoiceNumber, pi.GrandTotal, s.SupplierName, pi.PurchaseOrderID "
                      "FROM DisbursementPayment d LEFT JOIN PurchaseInvoice pi USING (PurchaseInvoiceID) "
                      "LEFT JOIN Supplier s ON s.SupplierID = d.SupplierID WHERE d.PaymentDate < ? "
                      "ORDER BY d.DisbursementID", self.before)
        out = [dict(number=r[0], date=r[1], supplier=r[2], invoice_id=r[3], amount=r[4], invoice=r[5], total=r[6],
                    name=r[7], po_id=r[8]) for r in rows]
        assert all(p["total"] is not None and p["name"] is not None for p in out), "a payment without its invoice"
        return out

    @cached_property
    def population(self) -> dict:
        amounts = [p["amount"] for p in self.payments]
        n, credited = self.q("SELECT COUNT(*), SUM(Credit) FROM GLEntry WHERE SourceDocumentType = "
                             "'DisbursementPayment' AND AccountID = ? AND PostingDate < ?", CASH, self.before)[0]
        return dict(count=len(amounts), total=sum(amounts), ledger_count=n, ledger_total=credited)

    @cached_property
    def strata(self) -> list[dict]:
        amounts = [p["amount"] for p in self.payments]
        bounds = STRATA + [max(amounts) + 0.01]
        out = []
        for low, high in zip(bounds, bounds[1:]):
            s = [a for a in amounts if low <= a < high]
            out.append(dict(low=low, high=high, count=len(s), value=sum(s)))
        assert sum(s["count"] for s in out) == len(amounts)
        return out

    @cached_property
    def large(self) -> list[dict]:
        out = []
        for p in self.payments:
            if p["amount"] >= LARGE:
                po = self.q("SELECT PONumber FROM PurchaseOrder WHERE PurchaseOrderID = ?", p["po_id"])
                receipts = [r[0] for r in self.q("SELECT ReceiptNumber FROM GoodsReceipt WHERE PurchaseOrderID = ? "
                                                 "ORDER BY GoodsReceiptID", p["po_id"])]
                items = [r[0] for r in self.q("SELECT i.ItemName FROM PurchaseInvoiceLine l JOIN Item i USING (ItemID) "
                                              "WHERE l.PurchaseInvoiceID = ?", p["invoice_id"])]
                out.append(dict(p, po=po[0][0] if po else None, receipts=receipts, items=items))
        return out

    @cached_property
    def benford(self) -> dict:
        def test(amounts):
            counts = Counter(lead_digit(a) for a in amounts)
            return dict(n=len(amounts), counts=counts, mad=mad(counts))
        partial = [p for p in self.payments if p["amount"] < p["total"]]
        invoices = {p["invoice_id"]: p["total"] for p in partial}
        return dict(all=test([p["amount"] for p in self.payments]),
                    full=test([p["amount"] for p in self.payments if not p["amount"] < p["total"]]),
                    partial=test([p["amount"] for p in partial]),
                    smallest_part_invoice=min(invoices.values()),
                    part_invoices=len(invoices),
                    part_under_2000=sum(1 for v in invoices.values() if v < 2000) / len(invoices),
                    zero_digit=sum(1 for p in self.payments if lead_digit(p["amount"]) == 0))

    # --- Tutorial 8.2 ----------------------------------------------------------------------------------------------
    @cached_property
    def aging(self) -> dict:
        applied, credited = defaultdict(float), defaultdict(float)
        for sid, amount in self.q("SELECT SalesInvoiceID, AppliedAmount FROM CashReceiptApplication "
                                  "WHERE ApplicationDate < ? ORDER BY CashReceiptApplicationID", self.before):
            applied[sid] += amount
        for sid, amount in self.q("SELECT OriginalSalesInvoiceID, GrandTotal FROM CreditMemo "
                                  "WHERE CreditMemoDate < ? ORDER BY CreditMemoID", self.before):
            credited[sid] += amount
        names = dict(self.q("SELECT CustomerID, CustomerName FROM Customer"))
        invoices = []
        for sid, number, due, customer, total in self.q(
                "SELECT SalesInvoiceID, InvoiceNumber, DueDate, CustomerID, GrandTotal FROM SalesInvoice "
                "WHERE InvoiceDate < ? ORDER BY SalesInvoiceID", self.before):
            raw = total - applied[sid] - credited[sid]
            cents = abs(raw * 100 - math.floor(raw * 100) - 0.5)
            assert cents > 1e-4, f"invoice {number}: open balance {raw!r} is too close to a half cent"
            balance = round_even(raw)
            if balance > 0:
                days = (self.end - iso(due)).days
                bucket = [label for low, label in BUCKETS if days >= low][-1]
                invoices.append(dict(number=number, days=days, bucket=bucket, balance=balance, customer=customer,
                                     name=names[customer]))
        buckets = {label: dict(count=0, balance=0.0) for _, label in BUCKETS}
        for i in invoices:
            buckets[i["bucket"]]["count"] += 1
            buckets[i["bucket"]]["balance"] += i["balance"]
        subledger = sum(i["balance"] for i in invoices)
        ledger = {(a, s): dict(count=n, amount=v) for a, s, n, v in self.q(
            "SELECT AccountID, SourceDocumentType, COUNT(*), SUM(Debit - Credit) FROM GLEntry "
            "WHERE AccountID IN (?, ?, ?) AND PostingDate < ? GROUP BY 1, 2", AR, ALLOWANCE, BAD_DEBT, self.before)}
        gl = sum(v["amount"] for (a, _), v in ledger.items() if a == AR)
        je = self.q("SELECT GLEntryID, PostingDate, VoucherNumber, Description, Debit - Credit FROM GLEntry "
                    "WHERE AccountID = ? AND SourceDocumentType = 'JournalEntry' AND PostingDate < ?", AR, self.before)
        assert len(je) == 1, je
        assert abs(gl - subledger - je[0][4]) < 0.005, "the difference is not the one journal entry line"
        customers = defaultdict(float)
        for i in invoices:
            customers[(i["customer"], i["name"])] += i["balance"]
        old = [i for i in invoices if i["days"] > 60]
        return dict(invoices=invoices, buckets=buckets, subledger=subledger, ledger=ledger, gl=gl,
                    je=dict(zip(["id", "date", "voucher", "description", "amount"], je[0])), customers=customers,
                    old=old, accounts=sorted({a for a, _ in ledger}))

    # --- Tutorial 8.3 ----------------------------------------------------------------------------------------------
    @cached_property
    def staff(self) -> dict[int, dict]:
        return {r[0]: dict(name=r[1], title=r[2], limit=r[3])
                for r in self.q("SELECT EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount FROM Employee")}

    @cached_property
    def entries(self) -> list[dict]:
        staff = self.staff
        out = []
        for number, posted, kind, total, creator, created, approver in self.q(
                "SELECT EntryNumber, PostingDate, EntryType, TotalAmount, CreatedByEmployeeID, CreatedDate, "
                "ApprovedByEmployeeID FROM JournalEntry ORDER BY JournalEntryID"):
            made = datetime.fromisoformat(created)
            flags = dict(Weekend=made.isoweekday() > 5, Backdated=made.date() > iso(posted),
                         SelfApproved=creator == approver, AboveLimit=total > staff[approver]["limit"],
                         RoundAmount=total % 1000 == 0)
            out.append(dict(number=number, posted=posted, created=made, kind=kind, total=total, flags=flags,
                            score=sum(flags.values()), creator=staff[creator], approver=staff[approver]))
        return out

    @cached_property
    def journal(self) -> dict:
        rows = self.entries
        opening = [r for r in rows if r["kind"] == "Opening"]
        assert len(opening) == 1 and opening[0]["score"] == max(r["score"] for r in rows), "the opening entry"
        lines = self.q("SELECT COUNT(*), SUM(Debit), SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")[0]
        drill = self.q("SELECT a.AccountNumber, g.Debit, g.Credit FROM GLEntry g JOIN Account a USING (AccountID) "
                       "WHERE g.SourceDocumentType = 'JournalEntry' AND g.VoucherNumber = ?", opening[0]["number"])
        return dict(count=len(rows), total=sum(r["total"] for r in rows),
                    flags={f: sum(1 for r in rows if r["flags"][f]) for f in FLAGS},
                    scores=Counter(r["score"] for r in rows), opening=opening[0],
                    by_creator=Counter((r["creator"]["title"], r["kind"]) for r in rows),
                    by_score=Counter((r["kind"], r["score"]) for r in rows),
                    lines=lines[0], debits=lines[1], credits=lines[2],
                    drill=dict(lines=len(drill), ar=sum(d for n, d, _ in drill if str(n) == ACCOUNT_NUMBERS[AR]),
                               debits=sum(d for _, d, _ in drill), credits=sum(c for _, _, c in drill)))

    @cached_property
    def disposals(self) -> dict[str, float]:
        """Asset disposal entries and the original cost of the asset each retires (FixedAsset, by description)."""
        out = {}
        for number, description in self.q("SELECT EntryNumber, Description FROM JournalEntry "
                                                 "WHERE EntryType = 'Asset Disposal'"):
            cost = self.q("SELECT OriginalCost, AssetCode FROM FixedAsset WHERE 'Dispose ' || AssetDescription = ?",
                          description)
            out[number] = (cost[0][0], cost[0][1]) if cost else (None, None)
        return out

    def disposition(self, r: dict) -> tuple[str, str]:
        """(category, text) for a flagged entry: expected, with the evidence, or follow up, with the question. Each
        rule tests every condition its text states, so an entry the text does not fit falls through and fails."""
        f, kind, total, made = r["flags"], r["kind"], r["total"], r["created"]
        posted = iso(r["posted"])
        on = f"{made:%A}, {made:%Y-%m-%d}"
        only = lambda *names: r["score"] == len(names) and all(f[n] for n in names)  # noqa: E731
        top_limit = max(s["limit"] for s in self.staff.values())
        if r is self.journal["opening"] and only("Weekend", "Backdated", "SelfApproved", "AboveLimit"):
            return ("follow:opening",
                    f"Follow up: the opening balance entry, created by the {r['creator']['title'].lower()} on {on}, "
                    f"after its posting date of {r['posted']}, approved under the same employee ID, and "
                    f"{money(total)}, far above the approver's limit of {money(r['approver']['limit'])}. Request the "
                    "support for the opening balances; its accounts receivable line has no invoice behind it "
                    "(Tutorial 8.2).")
        first_saturday = made.weekday() == 5 and made.month == 1 and made.day <= 7
        if only("Weekend", "Backdated") and first_saturday and posted == date(made.year, 1, 1):
            return ("follow:backdated",
                    f"Follow up: {article(kind.lower())} entry created on {on}, the first Saturday of the year, and posted "
                    f"to {r['posted']}, before it was made. Ask why it was recorded after its date and whether the "
                    "period it posts to was still open.")
        carries = {"Year-End Close - P&L to Income Summary": "a whole year's revenue and expenses",
                   "Year-End Close - Income Summary to Retained Earnings": "the year's net income to retained earnings"}
        if only("AboveLimit") and kind in carries and r["approver"]["limit"] == top_limit:
            return ("expected:close",
                    f"Expected: a year-end closing entry of {money(total)}, which carries {carries[kind]}, above the "
                    f"approver's limit of {money(r['approver']['limit'])}, the highest limit of any employee. Report "
                    "the gap in the approval policy for closing entries.")
        if only("AboveLimit", "RoundAmount") and kind == "Debt Reclass" and r["approver"]["title"] == "Controller":
            return ("follow:reclass",
                    f"Follow up: a round debt reclassification of {money(total)}, above the controller's limit of "
                    f"{money(r['approver']['limit'])}. Request the note agreement and the approval of an amount above "
                    "the limit.")
        month_end = (posted + timedelta(days=1)).day == 1
        if only("Weekend") and kind == "Depreciation" and made.date() == posted and month_end:
            return ("expected:depreciation",
                    f"Expected: the monthly depreciation, created by the {r['creator']['title'].lower()} on the last "
                    f"day of the month, {on}, the date it posts to.")
        support = {"Rent": "the lease", "Utilities": "the utility invoice"}
        if only("SelfApproved") and kind in support and r["creator"]["title"] == "Accounting Manager":
            return ("follow:self",
                    f"Follow up: a {kind.lower()} entry created and approved by the accounting manager. Ask "
                    f"who reviews the recurring entries this person records, and request {support[kind]} that "
                    "supports the amount.")
        cost, code = self.disposals.get(r["number"], (None, None))
        if only("RoundAmount") and kind == "Asset Disposal" and cost == total:
            return ("expected:disposal",
                    f"Expected: an asset disposal whose total, {money(total)}, is the original cost of the asset it "
                    f"retires ({code} in the fixed-asset register). Agree the cost and the accumulated depreciation "
                    "to the register.")
        raise AssertionError(f"no disposition rule fits {r['number']} ({kind}, flags {f})")

    @cached_property
    def dispositions(self) -> dict[str, tuple[str, str]]:
        return {r["number"]: self.disposition(r) for r in self.entries if r["score"] >= 1}


@dataclass
class Build:
    wb: object
    src: str                                    # the CharlesRiver.xlsx path the queries read while building
    xlsx: Path                                  # the same workbook, for type detection
    exp: object                                 # expected.Expected (the sales facts; not used here)
    year: int                                   # the last fiscal year under review (2026 in the 2026 edition)
    checks: list = field(default_factory=list)  # (tutorial, Check)
    facts: Facts = None

    def __post_init__(self):
        self.facts = Facts(self.year)

    def check(self, tutorial: str, label: str, expected, actual: str, tolerance: float = 0.005, fmt: str = MONEY):
        self.checks.append((tutorial, Check(label, expected, actual, tolerance, fmt)))

    @property
    def before(self) -> str:
        """The M literal of the date filters' bound: Date Filters > Before 2027-01-01 on a Date/Time column."""
        y = self.year + 1
        return f"#datetime({y}, 1, 1, 0, 0, 0)"


def nav(b: Build, number: int, table: str, corrections: dict | None = None, extra=()) -> str:
    return pq.navigator_query(b.src, number, table, list(pq.detected_types(b.xlsx, table)), corrections, list(extra))


def table_order(b: Build, table: str, columns: list[str], added: list[str] = ()) -> list[str]:
    """Columns as Choose Columns keeps them: in the table's order, not the order they are ticked."""
    order = [c for c, _ in pq.detected_types(b.xlsx, table)] + list(added)
    missing = [c for c in columns if c not in order]
    assert not missing, f"{table} has no column {missing}"
    return sorted(columns, key=order.index)


def before_filter(b: Build, column: str) -> str:
    return f"Table.SelectRows({{prev}}, each [{column}] < {b.before})"


def ws_(b: Build, name: str):
    return b.wb.Worksheets(name)


def formulas(ws, cells: dict[str, str]) -> None:
    for addr, f in cells.items():
        ws.Range(addr).Formula2 = f


def values(ws, cells: dict[str, object]) -> None:
    for addr, v in cells.items():
        ws.Range(addr).Value = v


def letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def workpaper(b: Build, name: str, entries: dict[str, str]) -> None:
    """A workpaper worksheet: the labels of Tutorial 8.1 Step 9 in A1:A10 and an entry beside each."""
    assert list(entries) == WP_LABELS, list(entries)
    ws = xl.sheet(b.wb, name)
    for i, (label, text) in enumerate(entries.items(), start=1):
        ws.Cells(i, 1).Value = label
        ws.Cells(i, 2).Value = text
    ws.Columns("A").Font.Bold = True
    ws.Columns("A").ColumnWidth = 26
    ws.Columns("B").ColumnWidth = 110
    ws.Columns("B").WrapText = True
    ws.Columns("A:B").VerticalAlignment = -4160          # top
    ws.Rows.AutoFit()


def pivot_count(sheet: str, data_field: str, *pairs) -> str:
    """A GETPIVOTDATA formula (without the =) for a PivotTable at A3 of a worksheet."""
    items = "".join(f',"{k}",{v if isinstance(v, int) else chr(34) + v + chr(34)}' for k, v in zip(pairs[::2], pairs[1::2]))
    return f"GETPIVOTDATA(\"{data_field}\",'{sheet}'!$A$3{items})"


# --- Tutorial 8.1 --------------------------------------------------------------------------------------------------

def t8_1(b: Build) -> None:
    wb, fx = b.wb, b.facts
    # Step 1: the payments with their invoices and suppliers; the two lookup queries are not loaded.
    xl.add_query(wb, "PurchaseInvoices", nav(b, 37, "PurchaseInvoice", extra=[
        ("Removed Other Columns", pq.select_columns(
            table_order(b, "PurchaseInvoice", ["PurchaseInvoiceID", "InvoiceNumber", "GrandTotal"])))]))
    xl.add_query(wb, "Suppliers", nav(b, 31, "Supplier", extra=[
        ("Removed Other Columns", pq.select_columns(table_order(b, "Supplier", ["SupplierID", "SupplierName"])))]))
    xl.add_query(wb, "Payments", nav(b, 39, "DisbursementPayment", extra=[
        ("Filtered Rows", before_filter(b, "PaymentDate")),
        ("Merged Queries", pq.merge("PurchaseInvoices", "PurchaseInvoiceID", "PurchaseInvoiceID", "PurchaseInvoices")),
        ("Expanded PurchaseInvoices", pq.expand("PurchaseInvoices", ["InvoiceNumber", "GrandTotal"])),
        ("Merged Queries1", pq.merge("Suppliers", "SupplierID", "SupplierID", "Suppliers")),
        ("Expanded Suppliers", pq.expand("Suppliers", ["SupplierName"]))]))
    blank = wb.Worksheets(1)
    xl.load_query(wb, "Payments", "Payments")
    blank.Delete()

    # Step 2: the ledger's cash credits for supplier payments, grouped before they load.
    xl.add_query(wb, "PaymentPostings", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", 'Table.SelectRows({prev}, each [SourceDocumentType] = "DisbursementPayment")'),
        ("Filtered Rows1", f"Table.SelectRows({{prev}}, each [AccountID] = {CASH})"),
        ("Filtered Rows2", before_filter(b, "PostingDate")),
        ("Grouped Rows", 'Table.Group({prev}, {"SourceDocumentType"}, {{"Postings", each Table.RowCount(_), '
                         'Int64.Type}, {"CashCredited", each List.Sum([Credit]), type nullable number}})')]))
    xl.load_query(wb, "PaymentPostings", "PaymentPostings")
    pop = xl.sheet(wb, "Population")
    values(pop, {"A1": "Source", "B1": "Count", "C1": "Total", "A2": "Payments Table",
                 "A3": "Cash credits in the ledger", "A4": "Difference"})
    formulas(pop, {"B2": "=ROWS(Payments[Amount])", "C2": "=SUM(Payments[Amount])",
                   "B3": "=SUM(PaymentPostings[Postings])", "C3": "=SUM(PaymentPostings[CashCredited])",
                   "B4": "=B2-B3", "C4": "=C2-C3"})

    # Step 3: the strata.
    st = xl.sheet(wb, "Strata")
    for col, head in zip("ABCDEF", ["Lower bound", "Upper bound", "Payments", "Share of payments", "Value",
                                    "Share of value"]):
        st.Range(f"{col}1").Value = head
    for r, low in enumerate(STRATA, start=2):
        st.Range(f"A{r}").Value = low
        st.Range(f"B{r}").Formula2 = f"=A{r + 1}" if r < 6 else "=MAX(Payments[Amount])+0.01"
        formulas(st, {f"C{r}": f'=COUNTIFS(Payments[Amount],">="&A{r},Payments[Amount],"<"&B{r})',
                      f"E{r}": f'=SUMIFS(Payments[Amount],Payments[Amount],">="&A{r},Payments[Amount],"<"&B{r})',
                      f"D{r}": f"=C{r}/C$7", f"F{r}": f"=E{r}/E$7"})
    values(st, {"A7": "Total"})
    formulas(st, {"C7": "=SUM(C2:C6)", "E7": "=SUM(E2:E6)", "D7": "=SUM(D2:D6)", "F7": "=SUM(F2:F6)"})
    st.Range("A2:B6").NumberFormat = MONEY
    st.Range("C2:C7").NumberFormat = COUNT
    st.Range("E2:E7").NumberFormat = MONEY
    st.Range("D2:D7").NumberFormat = PCT
    st.Range("F2:F7").NumberFormat = PCT
    st.Range("A1:F1").Font.Bold = True

    # Step 4: the payments of the top two strata, filtered, copied below the table, and the filter cleared.
    pay = xl.table(wb, "Payments")
    amount = pay.ListColumns("Amount").Index
    pay.Range.AutoFilter(amount, f">={LARGE}")
    pay.Range.SpecialCells(XL_VISIBLE).Copy(st.Range("A10"))
    pay.AutoFilter.ShowAllData()
    ncols = pay.ListColumns.Count
    last = 10 + len(fx.large)
    disp_col = letter(ncols + 1)
    st.Range(f"{disp_col}10").Value = "Disposition"
    number_col = pay.ListColumns("PaymentNumber").Index
    by_number = {p["number"]: p for p in fx.large}
    for r in range(11, last + 1):
        p = by_number[st.Cells(r, number_col).Value]
        assert p["po"] and p["receipts"] and p["items"], f"{p['number']}: no purchase order, receipt, or line"
        st.Range(f"{disp_col}{r}").Value = (
            f"Vouch: {' and '.join(p['items'])} from {p['name']}. Trace the payment to purchase order {p['po']}, "
            f"receiving record {', '.join(p['receipts'])}, and the approval of invoice {p['invoice']}, and confirm "
            f"that each supports {money(p['amount'])}.")
    st.Range(f"A10:{disp_col}10").Font.Bold = True
    st.Columns(f"A:{letter(ncols)}").AutoFit()
    st.Columns(disp_col).ColumnWidth = 90
    st.Range(f"{disp_col}11:{disp_col}{last}").WrapText = True
    st.Columns("A").ColumnWidth = max(st.Columns("A").ColumnWidth, 13)

    # Step 5: the first digit of each payment.
    xl.add_column(pay, "LeadDigit", '=--LEFT(TEXT([@Amount],"0.00000000E+00"),1)')
    values(pop, {"A6": "Payments with LeadDigit 0"})
    formulas(pop, {"B6": "=COUNTIF(Payments[LeadDigit],0)"})
    pop.Range("B2:B6").NumberFormat = COUNT
    pop.Range("C2:C4").NumberFormat = MONEY
    pop.Range("A1:C1").Font.Bold = True
    pop.Columns("A").ColumnWidth = 28
    pop.Columns("B:C").ColumnWidth = 16

    # Step 6: the first digits against Benford's Law, and the combo chart.
    bf = xl.sheet(wb, "Benford")
    for col, head in zip("ABCDE", ["Digit", "Expected", "Payments", "Actual", "Difference"]):
        bf.Range(f"{col}1").Value = head
    for d in range(1, 10):
        r = d + 1
        bf.Range(f"A{r}").Value = d
        formulas(bf, {f"B{r}": f"=LOG10(1+1/A{r})", f"C{r}": f"=COUNTIF(Payments[LeadDigit],A{r})",
                      f"D{r}": f"=C{r}/C$11", f"E{r}": f"=ABS(D{r}-B{r})"})
    values(bf, {"A11": "Total", "A12": "MAD"})
    formulas(bf, {"B11": "=SUM(B2:B10)", "C11": "=SUM(C2:C10)", "D11": "=SUM(D2:D10)", "E12": "=AVERAGE(E2:E10)"})
    for col in "BDE":
        bf.Columns(col).NumberFormat = PCT
    bf.Range("E12").NumberFormat = MADF
    bf.Range("C2:C11").NumberFormat = COUNT
    shape = bf.Shapes.AddChart2(-1, xl.XL_COLUMN_CLUSTERED, bf.Range("A16").Left, bf.Range("A16").Top, 480, 288)
    chart = shape.Chart
    chart.SetSourceData(bf.Range("D1:D10,B1:B10"))
    # Clustered Column - Line: the actual proportions as columns and the expected proportions as a line. Excel orders
    # the series by their columns, Expected first, so the line is set on Expected by name.
    for s in chart.SeriesCollection():
        if s.Name == "Expected":
            s.ChartType = xl.XL_LINE_MARKERS
    assert sorted((s.Name, s.ChartType) for s in chart.SeriesCollection()) == \
        [("Actual", xl.XL_COLUMN_CLUSTERED), ("Expected", xl.XL_LINE_MARKERS)]

    # Steps 7 and 8: full and partial payments, and the conformity of each.
    xl.add_column(pay, "Partial", "=[@Amount]<[@GrandTotal]")
    for col, head in zip("FGHI", ["Full", "Partial", "Full share", "Partial share"]):
        bf.Range(f"{col}1").Value = head
    for r in range(2, 11):
        formulas(bf, {f"F{r}": f"=COUNTIFS(Payments[LeadDigit],A{r},Payments[Partial],FALSE)",
                      f"G{r}": f"=COUNTIFS(Payments[LeadDigit],A{r},Payments[Partial],TRUE)",
                      f"H{r}": f"=F{r}/SUM(F$2:F$10)", f"I{r}": f"=G{r}/SUM(G$2:G$10)"})
    formulas(bf, {"H12": "=AVERAGE(ABS(H2:H10-$B$2:$B$10))", "I12": "=AVERAGE(ABS(I2:I10-$B$2:$B$10))",
                  "I14": "=MINIFS(Payments[GrandTotal],Payments[Partial],TRUE)"})
    values(bf, {"F14": "Smallest invoice paid in parts"})
    bf.Range("F2:G10").NumberFormat = COUNT
    bf.Range("H2:I10").NumberFormat = PCT
    bf.Range("H12:I12").NumberFormat = MADF
    bf.Range("I14").NumberFormat = MONEY
    bf.Range("A1:I1").Font.Bold = True
    bf.Columns("A:I").ColumnWidth = 12

    # Step 9: the workpaper.
    p, s, bn = fx.population, fx.strata, fx.benford
    top = s[3]["count"] + s[4]["count"]
    suppliers = sorted({x["name"] for x in fx.large})
    workpaper(b, "WP Payments", {
        "Objective": f"Test the supplier payments of fiscal {b.year - 2} through {b.year} for completeness against "
                     "the ledger, identify the payments large enough to examine individually, and test whether the "
                     "payment amounts follow Benford's Law.",
        "Source": "CharlesRiver.xlsx: Tables T39_DisbursementPayment, T37_PurchaseInvoice, and T31_Supplier (query "
                  "Payments, with the queries PurchaseInvoices and Suppliers) and T3_GLEntry (query PaymentPostings), "
                  "imported with Power Query.",
        "Population check": f"{p['count']:,} payments totaling {money(p['total'])} agree with the "
                            f"{p['ledger_count']:,} DisbursementPayment credits to account 1010 Cash and Cash "
                            f"Equivalents (AccountID {CASH}) in the ledger, {money(p['ledger_total'])}; both "
                            "differences are zero (Population worksheet).",
        "Procedure": "Stratified the payments by amount (Strata worksheet); listed the payments of the top two strata "
                     "for individual examination (Strata, from row 10); added the first digit of each amount "
                     "(LeadDigit) and compared the first-digit proportions with Benford's Law for all payments, and "
                     "for full and partial payments separately (Benford worksheet).",
        "Parameters": f"Date filter: PaymentDate before {b.year + 1}-01-01 in the query Payments, and PostingDate "
                      f"before {b.year + 1}-01-01 in PaymentPostings. Strata lower bounds 0, 1,000, 10,000, 50,000, "
                      "and 100,000; each upper bound is the next lower bound, and the top one is the largest payment "
                      "plus 0.01. Digit formula: =--LEFT(TEXT([@Amount],\"0.00000000E+00\"),1). Partial payment: "
                      "Amount less than the invoice's GrandTotal. Conformity: Nigrini's MAD ranges for the first-digit "
                      "test (0.006, 0.012, 0.015).",
        "Results": f"{s[0]['count'] / p['count']:.1%} of the payments are under $1,000 and hold "
                   f"{s[0]['value'] / p['total']:.1%} of the value; {s[2]['count']:,} payments of $10,000 to $50,000 "
                   f"hold {s[2]['value'] / p['total']:.1%}; {top} payments are $50,000 or more. MAD of all payments "
                   f"{bn['all']['mad']:.5f} ({conformity(bn['all']['mad']).lower()}); full payments "
                   f"{bn['full']['mad']:.5f} ({conformity(bn['full']['mad']).lower()}); partial payments "
                   f"{bn['partial']['mad']:.5f} ({conformity(bn['partial']['mad']).lower()}). No payment has a "
                   "LeadDigit of 0.",
        "Exceptions and disposition": f"The {top} payments of $50,000 or more go to {len(suppliers)} suppliers "
                                      f"({' and '.join(suppliers)}), and each pays one invoice in full: vouch each to "
                                      "its purchase order, its receiving record, and the approval of its invoice "
                                      "(dispositions on the Strata worksheet). Partial payments: Charles River pays "
                                      "in parts only invoices of $1,000 or more (the smallest is "
                                      f"{money(bn['smallest_part_invoice'])}), {bn['part_under_2000']:.0%} of them "
                                      "under $2,000, so their parts start with the digits 3 to 9 more often than "
                                      "Benford's Law expects; the nonconformity comes from the payment process, not "
                                      "from invented amounts.",
        "Conclusion": "The payments reconcile to the ledger, the largest ones are identified for vouching, and the "
                      "one departure from Benford's Law has an explanation that the data supports. The test found no "
                      "exception that points to an error.",
        "Prepared by": PREPARED,
        "Reviewed by": ""})

    t = "8.1"
    b.check(t, "payments in the Payments Table (Population!B2)", p["count"], "=Population!B2", 0, COUNT)
    b.check(t, "their total (Population!C2)", round(p["total"], 2), "=Population!C2")
    b.check(t, "cash credits in the ledger (Population!B3)", p["ledger_count"], "=Population!B3", 0, COUNT)
    b.check(t, "their total (Population!C3)", round(p["ledger_total"], 2), "=Population!C3")
    b.check(t, "difference in count (Population!B4)", 0, "=Population!B4", 0, COUNT)
    b.check(t, "difference in total (Population!C4)", 0, "=Population!C4")
    for i, row in enumerate(s):
        r = i + 2
        label = f"{row['low']:,} and over" if i == 4 else f"{row['low']:,} to {STRATA[i + 1]:,}"
        b.check(t, f"payments of {label} (Strata!C{r})", row["count"], f"=Strata!C{r}", 0, COUNT)
        b.check(t, f"value of {label} (Strata!E{r})", round(row["value"], 2), f"=Strata!E{r}")
    b.check(t, "stratification count equals the population (Strata!C7 less Population!B2)", 0,
            "=Strata!C7-Population!B2", 0, COUNT)
    b.check(t, "stratification value equals the population (Strata!E7 less Population!C2)", 0,
            "=Strata!E7-Population!C2")
    b.check(t, "shares of payments add up to 100% (Strata!D7)", 1, "=Strata!D7", 1e-9, PCT)
    b.check(t, "shares of value add up to 100% (Strata!F7)", 1, "=Strata!F7", 1e-9, PCT)
    b.check(t, "payments in the top two strata (Strata!C5:C6)", top, "=Strata!C5+Strata!C6", 0, COUNT)
    amt, gt = letter(amount), letter(pay.ListColumns("GrandTotal").Index)
    b.check(t, f"payments copied below the table (Strata!{amt}11:{amt}{last})", top,
            f"=COUNT(Strata!{amt}11:{amt}{last})", 0, COUNT)
    b.check(t, "their amounts equal the top two strata", 0, f"=SUM(Strata!{amt}11:{amt}{last})-Strata!E5-Strata!E6")
    b.check(t, "each pays its invoice in full (Amount = GrandTotal)", top,
            f"=SUMPRODUCT(--(Strata!{amt}11:{amt}{last}=Strata!{gt}11:{gt}{last}))", 0, COUNT)
    b.check(t, "each has a disposition", top, f"=COUNTA(Strata!{disp_col}11:{disp_col}{last})", 0, COUNT)
    b.check(t, "payments with LeadDigit 0 (Population!B6)", bn["zero_digit"], "=Population!B6", 0, COUNT)
    b.check(t, "payments starting with 1 (Benford!C2)", bn["all"]["counts"][1], "=Benford!C2", 0, COUNT)
    b.check(t, "payments starting with 9 (Benford!C10)", bn["all"]["counts"][9], "=Benford!C10", 0, COUNT)
    b.check(t, "digit counts add up to the population (Benford!C11)", p["count"], "=Benford!C11", 0, COUNT)
    b.check(t, "MAD of all payments (Benford!E12)", bn["all"]["mad"], "=Benford!E12", 1e-9, MADF)
    b.check(t, "conformity of all payments", conformity(bn["all"]["mad"]), CONFORMITY.format(c="Benford!E12"))
    b.check(t, "full payments (Benford!F2:F10)", bn["full"]["n"], "=SUM(Benford!F2:F10)", 0, COUNT)
    b.check(t, "partial payments (Benford!G2:G10)", bn["partial"]["n"], "=SUM(Benford!G2:G10)", 0, COUNT)
    b.check(t, "MAD of full payments (Benford!H12)", bn["full"]["mad"], "=Benford!H12", 1e-9, MADF)
    b.check(t, "conformity of full payments", conformity(bn["full"]["mad"]), CONFORMITY.format(c="Benford!H12"))
    b.check(t, "MAD of partial payments (Benford!I12)", bn["partial"]["mad"], "=Benford!I12", 1e-9, MADF)
    b.check(t, "conformity of partial payments", conformity(bn["partial"]["mad"]), CONFORMITY.format(c="Benford!I12"))
    b.check(t, "smallest invoice paid in parts (Benford!I14)", round(bn["smallest_part_invoice"], 2), "=Benford!I14")


# --- Tutorial 8.2 --------------------------------------------------------------------------------------------------

def t8_2(b: Build) -> None:
    wb, fx = b.wb, b.facts
    a = fx.aging
    # Step 1: invoices, receipts applied, credit memos, and customers; only OpenInvoices loads.
    xl.add_query(wb, "Customers", nav(b, 4, "Customer", extra=[
        ("Removed Other Columns", pq.select_columns(
            table_order(b, "Customer", ["CustomerID", "CustomerName", "CreditLimit"])))]))
    xl.add_query(wb, "Applied", nav(b, 20, "CashReceiptApplication", extra=[
        ("Filtered Rows", before_filter(b, "ApplicationDate")),
        ("Grouped Rows", 'Table.Group({prev}, {"SalesInvoiceID"}, {{"AppliedTotal", each List.Sum([AppliedAmount]), '
                         'type nullable number}})')]))
    xl.add_query(wb, "Credited", nav(b, 23, "CreditMemo", extra=[
        ("Filtered Rows", before_filter(b, "CreditMemoDate")),
        ("Grouped Rows", 'Table.Group({prev}, {"OriginalSalesInvoiceID"}, {{"CreditedTotal", '
                         'each List.Sum([GrandTotal]), type nullable number}})')]))
    # Step 2: the open balance of each invoice.
    xl.add_query(wb, "OpenInvoices", nav(b, 16, "SalesInvoice", extra=[
        ("Filtered Rows", before_filter(b, "InvoiceDate")),
        ("Merged Queries", pq.merge("Applied", "SalesInvoiceID", "SalesInvoiceID", "Applied")),
        ("Expanded Applied", pq.expand("Applied", ["AppliedTotal"])),
        ("Merged Queries1", pq.merge("Credited", "SalesInvoiceID", "OriginalSalesInvoiceID", "Credited")),
        ("Expanded Credited", pq.expand("Credited", ["CreditedTotal"])),
        ("Merged Queries2", pq.merge("Customers", "CustomerID", "CustomerID", "Customers")),
        ("Expanded Customers", pq.expand("Customers", ["CustomerName", "CreditLimit"])),
        ("Replaced Value", 'Table.ReplaceValue({prev},null,0,Replacer.ReplaceValue,{"AppliedTotal", "CreditedTotal"})'),
        ("Added Custom", pq.add_custom("OpenBalance", "[GrandTotal] - [AppliedTotal] - [CreditedTotal]")),
        ("Changed Type1", pq.transform_types([("OpenBalance", "type number")])),
        ("Rounded Off", 'Table.TransformColumns({prev},{{"OpenBalance", each Number.Round(_, 2), type number}})'),
        ("Filtered Rows1", "Table.SelectRows({prev}, each [OpenBalance] > 0)")]))
    xl.load_query(wb, "OpenInvoices", "OpenInvoices")
    inv = xl.table(wb, "OpenInvoices")
    inv.ListColumns("OpenBalance").DataBodyRange.NumberFormat = MONEY

    # Step 3: the as-of date, the Buckets Table, and the aging columns.
    ag = xl.sheet(wb, "Aging")
    values(ag, {"A1": "As-of date"})
    ag.Range("B1").Formula = b.facts.end.isoformat()       # typed, so Excel stores the date
    ag.Range("B1").NumberFormat = "yyyy-mm-dd"
    assert ag.Range("B1").Value2 == (b.facts.end - date(1899, 12, 30)).days, "B1 is not a date"
    xl.name_cell(wb, "AsOfDate", "Aging!$B$1")
    values(ag, {"F3": "From", "G3": "Bucket"})
    for r, (low, label) in enumerate(BUCKETS, start=4):
        values(ag, {f"F{r}": low, f"G{r}": label})
    buckets = ag.ListObjects.Add(1, ag.Range("F3:G8"), None, xl.XL_YES)
    buckets.Name = "Buckets"
    xl.add_column(inv, "DaysPastDue", "=AsOfDate-[@DueDate]", "0")
    xl.add_column(inv, "Bucket", "=XLOOKUP([@DaysPastDue],Buckets[From],Buckets[Bucket],,-1)")

    # Step 4: the aging summary, and the invoices sorted from the oldest.
    values(ag, {"A3": "Bucket", "B3": "Invoices", "C3": "Open balance", "D3": "Share of balance", "A9": "Total"})
    for r, (_, label) in enumerate(BUCKETS, start=4):
        values(ag, {f"A{r}": label})
        formulas(ag, {f"B{r}": f"=COUNTIFS(OpenInvoices[Bucket],A{r})",
                      f"C{r}": f"=SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[Bucket],A{r})",
                      f"D{r}": f"=C{r}/C$9"})
    formulas(ag, {"B9": "=SUM(B4:B8)", "C9": "=SUM(C4:C8)", "D9": "=SUM(D4:D8)"})
    srt = inv.Sort
    srt.SortFields.Clear()
    srt.SortFields.Add(Key=inv.ListColumns("DaysPastDue").Range, SortOn=0, Order=xl.XL_DESCENDING)
    srt.Header = xl.XL_YES
    srt.Apply()

    # Step 5: account 1020 in the ledger, with the allowance and bad-debt accounts.
    kept = table_order(b, "GLEntry", ["GLEntryID", "PostingDate", "AccountID", "VoucherNumber", "SourceDocumentType",
                                      "Description", "Debit", "Credit"])
    xl.add_query(wb, "LedgerAR", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", f"Table.SelectRows({{prev}}, each [AccountID] = {AR} or [AccountID] = {ALLOWANCE} or "
                          f"[AccountID] = {BAD_DEBT})"),
        ("Filtered Rows1", before_filter(b, "PostingDate")),
        ("Removed Other Columns", pq.select_columns(kept)),
        ("Added Custom", pq.add_custom("Amount", "[Debit] - [Credit]")),
        ("Changed Type1", pq.transform_types([("Amount", "type number")]))]))
    xl.load_query(wb, "LedgerAR", "LedgerAR")
    values(ag, {"A11": "Open invoices (sub-ledger)", "A12": f"Account 1020 (AccountID {AR})", "A13": "Difference"})
    formulas(ag, {"C11": "=C9", "C12": f"=SUMIFS(LedgerAR[Amount],LedgerAR[AccountID],{AR})", "C13": "=C12-C11"})
    ag.Range("B4:B9").NumberFormat = COUNT
    ag.Range("C4:C13").NumberFormat = MONEY
    ag.Range("D4:D9").NumberFormat = PCT
    ag.Range("A3:D3").Font.Bold = True
    ag.Columns("A").ColumnWidth = 28
    ag.Columns("B:D").ColumnWidth = 16
    ag.Columns("F:G").ColumnWidth = 14

    # Step 6: the ledger rows by source document, and Show Details for the journal entry row.
    cache = wb.PivotCaches().Create(SourceType=xl.XL_DATABASE, SourceData="LedgerAR")
    pv = xl.sheet(wb, UNNAMED["ar_pivot"])
    pt = cache.CreatePivotTable(TableDestination=pv.Range("A3"), TableName="PivotTable1")
    pt.PivotFields("AccountID").Orientation = xl.XL_ROW
    pt.PivotFields("SourceDocumentType").Orientation = xl.XL_ROW
    pt.AddDataField(pt.PivotFields("GLEntryID"), "Count of GLEntryID", xl.XL_COUNT).NumberFormat = COUNT
    pt.AddDataField(pt.PivotFields("Amount"), "Sum of Amount", xl.XL_SUM).NumberFormat = MONEY
    pt.GetPivotData("Sum of Amount", "AccountID", str(AR), "SourceDocumentType", "JournalEntry").ShowDetail = True
    detail = wb.ActiveSheet
    assert detail.Name != pv.Name and detail.ListObjects.Count == 1, "Show Details made no worksheet"
    detail.Name = UNNAMED["ar_details"]
    detail.Columns.AutoFit()
    detail_lo = detail.ListObjects(1)
    voucher_col = letter(detail_lo.ListColumns("VoucherNumber").Index)
    amount_col = letter(detail_lo.ListColumns("Amount").Index)

    # Step 7: balances by customer, the key items, and a random sample of the others, pasted as values.
    xl.add_query(wb, "CustomerBalances", pq.steps_query([
        ("Source", "OpenInvoices"),
        ("Grouped Rows", 'Table.Group({prev}, {"CustomerID", "CustomerName"}, {{"Balance", '
                         'each List.Sum([OpenBalance]), type nullable number}})')]))
    xl.load_query(wb, "CustomerBalances", "CustomerBalances")
    xl.table(wb, "CustomerBalances").ListColumns("Balance").DataBodyRange.NumberFormat = MONEY
    cf = xl.sheet(wb, "Confirmations")
    values(cf, {"A1": "Key item threshold", "B1": KEY_ITEM, "A2": "Sample size", "B2": SAMPLE, "A4": "Key items",
                "E4": "Other customers in random order", "I4": "Random sample"})
    formulas(cf, {"A5": "=FILTER(CustomerBalances,CustomerBalances[Balance]>=B1)",
                  "E5": '=SORTBY(FILTER(CustomerBalances,CustomerBalances[Balance]<B1),'
                        'RANDARRAY(COUNTIF(CustomerBalances[Balance],"<"&B1)))',
                  "I5": "=INDEX(E5#,SEQUENCE(B2),{1,2,3})"})
    wb.Application.Calculate()
    sample = cf.Range(f"I5:K{4 + SAMPLE}")
    drawn = sample.Value
    sample.Value = drawn                                    # Step 7i: Paste Values over the sample
    cf.Range("I4").AddComment(
        "Step 7i froze this sample: Excel's RANDARRAY drew it when the companion file was built, on "
        f"{pq.today()}, and it was pasted as values. Your own draw will differ. The list in column E reshuffles "
        "every time the workbook recalculates.")
    cf.Range("B1").NumberFormat = COUNT
    for col in "CGK":
        cf.Range(f"{col}5:{col}{4 + len(a['customers'])}").NumberFormat = MONEY
    cf.Range("A4:K4").Font.Bold = True
    cf.Columns("A").ColumnWidth = 18
    cf.Columns("B").ColumnWidth = 28
    cf.Columns("C").ColumnWidth = 14
    cf.Columns("E").ColumnWidth = 12
    cf.Columns("F").ColumnWidth = 28
    cf.Columns("G").ColumnWidth = 14
    cf.Columns("I").ColumnWidth = 12
    cf.Columns("J").ColumnWidth = 28
    cf.Columns("K").ColumnWidth = 14

    # Step 8: the workpaper.
    bk, key = a["buckets"], {k: v for k, v in a["customers"].items() if v >= KEY_ITEM}
    others = len(a["customers"]) - len(key)
    selected = "; ".join(f"{name} ({int(cid)}, {money(bal)})" for cid, name, bal in drawn)
    small = [i for i in a["old"] if i["balance"] < 10]
    workpaper(b, "WP Receivables", {
        "Objective": f"Age the receivables at {fx.end.isoformat()}, reconcile the open invoices to account 1020 "
                     "Accounts Receivable, and select customer balances for confirmation.",
        "Source": "CharlesRiver.xlsx: Tables T16_SalesInvoice, T20_CashReceiptApplication, T23_CreditMemo, and "
                  "T4_Customer (queries OpenInvoices, Applied, Credited, and Customers), and T3_GLEntry (query "
                  f"LedgerAR, AccountIDs {AR}, {ALLOWANCE}, and {BAD_DEBT}), imported with Power Query.",
        "Population check": f"{len(a['invoices']):,} open invoices with a total open balance of "
                            f"{money(a['subledger'])} at the as-of date; the aging total equals the sum of the "
                            "OpenBalance column, and no open balance is zero or negative.",
        "Procedure": "Open balance: GrandTotal less the receipts applied and the credit memos issued by the as-of "
                     "date, rounded to cents and kept when positive (query OpenInvoices). Aged by days past due "
                     "(Aging worksheet); reconciled the total to account 1020; analyzed the ledger rows by source "
                     f"document with a PivotTable and Show Details ({UNNAMED['ar_pivot']} and {UNNAMED['ar_details']} "
                     "worksheets); grouped the open balances by customer and selected balances for confirmation "
                     "(Confirmations worksheet).",
        "Parameters": f"As-of date {fx.end.isoformat()} (AsOfDate, Aging!B1); date filters before "
                      f"{b.year + 1}-01-01 on InvoiceDate, ApplicationDate, CreditMemoDate, and PostingDate; aging "
                      "buckets in the Buckets Table (from -9999, 1, 31, 61, and 91 days past due); key item threshold "
                      f"{money(KEY_ITEM)}; sample size {SAMPLE}; sample selected on {pq.today()} with SORTBY and "
                      "RANDARRAY and pasted as values.",
        "Results": "Aging: " + "; ".join(f"{label} {bk[label]['count']:,} invoices, {money(bk[label]['balance'])}"
                                         for _, label in BUCKETS) +
                   f". Account 1020: {money(a['gl'])}; open invoices {money(a['subledger'])}; difference "
                   f"{money(a['gl'] - a['subledger'])}. Confirmations: {len(key)} key items with balances of "
                   f"{money(KEY_ITEM)} or more, holding {sum(key.values()) / a['subledger']:.1%} of the open balance, "
                   f"and a random sample of {SAMPLE} of the other {others} customers: {selected}.",
        "Exceptions and disposition": f"Finding 1: the difference of {money(a['gl'] - a['subledger'])} is the "
                                      f"{a['je']['description'].lower()} in {a['je']['voucher']}, dated "
                                      f"{a['je']['date']}. No invoice stands behind it, and no receipt has been "
                                      "applied to it since. Follow-up: request the customer-level detail behind it "
                                      "and assess whether any of it is still collectible. Finding 2: no allowance "
                                      "for doubtful accounts: accounts 1030 and 6170 have no postings in the three "
                                      "years. The FASB credit loss standard requires an allowance even when the risk "
                                      "of loss is remote, and an aging schedule is one of the methods it accepts. "
                                      f"Finding 3: the {len(a['old'])} invoices more than 60 days past due hold "
                                      f"{money(sum(i['balance'] for i in a['old']))}; {len(small)} of them are "
                                      "residual balances under $10 left after the customer's payment. Write them off "
                                      "or collect them.",
        "Conclusion": "Customers pay mostly on time. Part of the receivables balance is not supported by any invoice, "
                      "and no allowance has been recorded against any of it. Both findings affect the amount at which "
                      "receivables would be reported, and both go to the audit committee with the evidence.",
        "Prepared by": PREPARED,
        "Reviewed by": ""})

    t = "8.2"
    total = round(a["subledger"], 2)
    b.check(t, "open invoices (rows of OpenInvoices)", len(a["invoices"]), "=ROWS(OpenInvoices[OpenBalance])", 0, COUNT)
    b.check(t, "open balances of zero or less", 0, '=COUNTIF(OpenInvoices[OpenBalance],"<=0")', 0, COUNT)
    for r, (_, label) in enumerate(BUCKETS, start=4):
        b.check(t, f"{label}: invoices (Aging!B{r})", bk[label]["count"], f"=Aging!B{r}", 0, COUNT)
        b.check(t, f"{label}: open balance (Aging!C{r})", round(bk[label]["balance"], 2), f"=Aging!C{r}")
    b.check(t, "aging total (Aging!C9)", total, "=Aging!C9")
    b.check(t, "aging total less the sum of the OpenBalance column", 0, "=Aging!C9-SUM(OpenInvoices[OpenBalance])")
    b.check(t, "share of the balance that is current (Aging!D4)", bk["Current"]["balance"] / a["subledger"],
            "=Aging!D4", 1e-9, PCT)
    b.check(t, "account 1020 at the as-of date (Aging!C12)", round(a["gl"], 2), "=Aging!C12")
    b.check(t, "difference (Aging!C13)", round(a["gl"] - a["subledger"], 2), "=Aging!C13")
    pvs = UNNAMED["ar_pivot"]
    b.check(t, "PivotTable: journal entry rows in account 1020", a["ledger"][(AR, "JournalEntry")]["count"],
            "=" + pivot_count(pvs, "Count of GLEntryID", "AccountID", AR, "SourceDocumentType", "JournalEntry"),
            0, COUNT)
    b.check(t, "PivotTable: their amount, the difference", round(a["ledger"][(AR, "JournalEntry")]["amount"], 2),
            "=" + pivot_count(pvs, "Sum of Amount", "AccountID", AR, "SourceDocumentType", "JournalEntry"))
    b.check(t, "PivotTable: rows for accounts 1030 and 6170 (AccountIDs 4 and 74)",
            sum(v["count"] for (acc, _), v in a["ledger"].items() if acc != AR),
            f"=IFERROR({pivot_count(pvs, 'Count of GLEntryID', 'AccountID', ALLOWANCE)},0)"
            f"+IFERROR({pivot_count(pvs, 'Count of GLEntryID', 'AccountID', BAD_DEBT)},0)", 0, COUNT)
    b.check(t, "Show Details: rows listed", 1, f"=ROWS({detail_lo.Name})", 0, COUNT)
    b.check(t, "Show Details: the voucher", a["je"]["voucher"], f"='{UNNAMED['ar_details']}'!{voucher_col}2")
    b.check(t, "Show Details: its amount", round(a["je"]["amount"], 2), f"='{UNNAMED['ar_details']}'!{amount_col}2")
    b.check(t, "customers with an open balance (rows of CustomerBalances)", len(a["customers"]),
            "=ROWS(CustomerBalances[Balance])", 0, COUNT)
    b.check(t, "customer balances add up to the aging total", total, "=SUM(CustomerBalances[Balance])")
    brown = sum(1 for _, name in a["customers"] if name == "Brown LLC")
    b.check(t, "customers named Brown LLC, kept apart by CustomerID", brown,
            '=COUNTIF(CustomerBalances[CustomerName],"Brown LLC")', 0, COUNT)
    b.check(t, "key items (rows spilled from Confirmations!A5)", len(key), "=ROWS(Confirmations!A5#)", 0, COUNT)
    b.check(t, "their share of the open balance", sum(key.values()) / a["subledger"],
            "=SUM(INDEX(Confirmations!A5#,0,3))/SUM(CustomerBalances[Balance])", 1e-9, PCT)
    b.check(t, "other customers (rows spilled from Confirmations!E5)", others, "=ROWS(Confirmations!E5#)", 0, COUNT)
    rng = f"Confirmations!I5:I{4 + SAMPLE}"
    b.check(t, "sampled customers, all different (Confirmations!I5:K24)", SAMPLE, f"=ROWS(UNIQUE({rng}))", 0, COUNT)
    b.check(t, "sampled customers below the key item threshold", SAMPLE,
            f'=SUMPRODUCT(COUNTIFS(CustomerBalances[CustomerID],{rng},CustomerBalances[Balance],"<"&Confirmations!B1))',
            0, COUNT)
    b.check(t, "sampled balances agree with CustomerBalances", 0,
            f"=ROUND(SUM(Confirmations!K5:K{4 + SAMPLE})-SUMPRODUCT(SUMIFS(CustomerBalances[Balance],"
            f"CustomerBalances[CustomerID],{rng})),2)")
    b.check(t, "the sample is pasted as values (I5 holds no formula)", 0, "=--ISFORMULA(Confirmations!I5)", 0, COUNT)


# --- Tutorial 8.3 --------------------------------------------------------------------------------------------------

def t8_3(b: Build) -> None:
    wb, fx = b.wb, b.facts
    j = fx.journal
    # Step 1: the journal entries with their approvers and creators.
    xl.add_query(wb, "Employees", nav(b, 74, "Employee", extra=[
        ("Removed Other Columns", pq.select_columns(
            table_order(b, "Employee", ["EmployeeID", "EmployeeName", "JobTitle", "MaxApprovalAmount"])))]))
    xl.add_query(wb, "Accounts", nav(b, 1, "Account", extra=[
        ("Removed Other Columns", pq.select_columns(
            table_order(b, "Account", ["AccountID", "AccountNumber", "AccountName"])))]))
    xl.add_query(wb, "JournalEntries", nav(b, 2, "JournalEntry", {
        "PostingDate": "type date", "CreatedDate": "type datetime", "ApprovedDate": "type datetime"}, extra=[
        ("Merged Queries", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", pq.expand("Employees", ["EmployeeName", "JobTitle", "MaxApprovalAmount"])),
        ("Renamed Columns", 'Table.RenameColumns({prev},{{"EmployeeName", "ApproverName"}, {"JobTitle", '
                            '"ApproverTitle"}, {"MaxApprovalAmount", "ApproverLimit"}})'),
        ("Merged Queries1", pq.merge("Employees", "CreatedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees1", pq.expand("Employees", ["EmployeeName", "JobTitle"])),
        ("Renamed Columns1", 'Table.RenameColumns({prev},{{"EmployeeName", "CreatorName"}, {"JobTitle", '
                             '"CreatorTitle"}})')]))
    xl.load_query(wb, "JournalEntries", "JournalEntries")
    je = xl.table(wb, "JournalEntries")
    je.ListColumns("TotalAmount").DataBodyRange.NumberFormat = MONEY

    # Steps 2 and 3: the five flags, the risk score, and the summary.
    for name, formula in FLAGS.items():
        xl.add_column(je, name, formula)
    xl.add_column(je, "RiskScore", RISK_SCORE, "0")
    sm = xl.sheet(wb, "JE Summary")
    for r, name in enumerate(FLAGS, start=1):
        values(sm, {f"A{r}": name})
        formulas(sm, {f"B{r}": f"=COUNTIF(JournalEntries[{name}],TRUE)"})
    for r, score in enumerate(range(6), start=8):
        values(sm, {f"A{r}": score})
        formulas(sm, {f"B{r}": f"=COUNTIF(JournalEntries[RiskScore],A{r})"})
    sm.Range("A8:A13").HorizontalAlignment = -4131        # left, like the flag names above them

    # Step 4: who makes journal entries, and which flags come in groups.
    cache = wb.PivotCaches().Create(SourceType=xl.XL_DATABASE, SourceData="JournalEntries")
    p1 = xl.sheet(wb, UNNAMED["je_creators"])
    pt1 = cache.CreatePivotTable(TableDestination=p1.Range("A3"), TableName="PivotTable1")
    pt1.PivotFields("CreatorTitle").Orientation = xl.XL_ROW
    pt1.PivotFields("EntryType").Orientation = xl.XL_ROW
    pt1.AddDataField(pt1.PivotFields("EntryNumber"), "Count of EntryNumber", xl.XL_COUNT)
    p2 = xl.sheet(wb, UNNAMED["je_scores"])
    pt2 = cache.CreatePivotTable(TableDestination=p2.Range("A3"), TableName="PivotTable2")
    pt2.PivotFields("EntryType").Orientation = xl.XL_ROW
    pt2.PivotFields("RiskScore").Orientation = xl.XL_COLUMN
    pt2.AddDataField(pt2.PivotFields("EntryNumber"), "Count of EntryNumber", xl.XL_COUNT)

    # Step 5: sorted by RiskScore, filtered to 1 or more, the visible rows pasted as values, the filter cleared.
    srt = je.Sort
    srt.SortFields.Clear()
    srt.SortFields.Add(Key=je.ListColumns("RiskScore").Range, SortOn=0, Order=xl.XL_DESCENDING)
    srt.Header = xl.XL_YES
    srt.Apply()
    score = je.ListColumns("RiskScore").Index
    first = je.ListColumns("EntryNumber").Index
    je.Range.AutoFilter(score, ">=1")
    jws = ws_(b, "JournalEntries")
    block = jws.Range(jws.Cells(je.Range.Row, je.Range.Column + first - 1),
                      jws.Cells(je.Range.Row + je.Range.Rows.Count - 1, je.Range.Column + score - 1))
    rows = [row for area in block.SpecialCells(XL_VISIBLE).Areas for row in area.Value]
    je.AutoFilter.ShowAllData()
    dp = xl.sheet(wb, "Dispositions")
    width = score - first + 1
    dp.Range(dp.Cells(1, 1), dp.Cells(len(rows), width)).Value = rows        # Paste Special > Values
    heads = list(rows[0])
    for c, head in enumerate(heads, start=1):                                  # keep dates and amounts readable
        fmt = je.ListColumns(head).DataBodyRange.Cells(1, 1).NumberFormat
        dp.Range(dp.Cells(2, c), dp.Cells(len(rows), c)).NumberFormat = fmt
    disp_col = letter(width + 1)
    dp.Range(f"{disp_col}1").Value = "Disposition"
    categories = Counter()
    for r in range(2, len(rows) + 1):
        category, text = fx.dispositions[dp.Cells(r, 1).Value]
        categories[category] += 1
        dp.Range(f"{disp_col}{r}").Value = text
    dp.Rows(1).Font.Bold = True
    dp.Columns(f"A:{letter(width)}").AutoFit()
    dp.Columns(disp_col).ColumnWidth = 100
    dp.Columns(disp_col).WrapText = True
    assert len(rows) - 1 == len(fx.dispositions), (len(rows) - 1, len(fx.dispositions))

    # Step 6: the ledger lines of the journal entries, and the drilldown to the opening entry.
    xl.add_query(wb, "JournalLines", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", 'Table.SelectRows({prev}, each [SourceDocumentType] = "JournalEntry")'),
        ("Merged Queries", pq.merge("Accounts", "AccountID", "AccountID", "Accounts")),
        ("Expanded Accounts", pq.expand("Accounts", ["AccountNumber", "AccountName"])),
        ("Removed Other Columns", pq.select_columns(table_order(
            b, "GLEntry", ["VoucherNumber", "AccountNumber", "AccountName", "Debit", "Credit"],
            added=["AccountNumber", "AccountName"]))),
        ("Reordered Columns", 'Table.ReorderColumns({prev},{"VoucherNumber", "AccountNumber", "AccountName", '
                              '"Debit", "Credit"})')]))
    xl.load_query(wb, "JournalLines", "JournalLines")
    values(sm, {"A15": "Entry totals", "A16": "Ledger debits"})
    formulas(sm, {"B15": "=SUM(JournalEntries[TotalAmount])", "B16": "=SUM(JournalLines[Debit])"})
    sm.Range("B15:B16").NumberFormat = MONEY
    sm.Columns("A").ColumnWidth = 16
    sm.Columns("B").ColumnWidth = 18
    dd = xl.sheet(wb, "Drilldown")
    opening = j["opening"]["number"]
    values(dd, {"A1": "Entry number", "B1": opening, "A3": "AccountNumber", "B3": "AccountName", "C3": "Debit",
                "D3": "Credit"})
    formulas(dd, {"A4": "=FILTER(JournalLines[[AccountNumber]:[Credit]],JournalLines[VoucherNumber]=B1)"})
    dd.Range("C4:D40").NumberFormat = MONEY
    dd.Range("A3:D3").Font.Bold = True
    dd.Columns("A").ColumnWidth = 16
    dd.Columns("B").ColumnWidth = 48
    dd.Columns("C:D").ColumnWidth = 16

    # Step 7: the workpaper.
    sc = j["scores"]
    flagged = j["count"] - sc[0]
    expected = {"expected:depreciation": "depreciation entries created on weekend month-ends, the dates they post to",
                "expected:close": "year-end closes above every approval limit (no limit exceeds $250,000; a gap in "
                                  "the approval policy to report)",
                "expected:disposal": "asset disposals at the round original cost of the asset retired"}
    follow = {"follow:opening": f"the opening entry {opening} (four flags)",
              "follow:backdated": "entries created on the first Saturday of January and posted to January 1",
              "follow:self": "rent and utilities entries created and approved by the accounting manager",
              "follow:reclass": "round debt reclassifications above the controller's limit"}
    assert set(categories) == set(expected) | set(follow), categories

    def summary(kinds: dict) -> str:
        return "; ".join(f"{categories[k]} {v}" if not k.endswith("opening") else v for k, v in kinds.items())

    workpaper(b, "WP Journals", {
        "Objective": "Identify journal entries with characteristics of management override (AS 2401) for follow-up.",
        "Source": "CharlesRiver.xlsx: Tables T2_JournalEntry, T74_Employee, and T1_Account (queries JournalEntries, "
                  f"Employees, and Accounts) and T3_GLEntry (query JournalLines); all {j['count']:,} entries posted "
                  f"in fiscal {b.year - 2} through {b.year}.",
        "Population check": f"{j['count']:,} entries; their TotalAmount, {money(j['total'])}, agrees with the debits "
                            f"of the ledger's {j['lines']:,} JournalEntry lines (JE Summary, B15 and B16).",
        "Procedure": "Entries by creator and type, and by type and risk score (two PivotTables); five flags on each "
                     "entry (weekend creation, created after the posting date, same creator and approver, above the "
                     "approver's limit, round thousands); RiskScore is their sum. A disposition for every entry with "
                     "a score of 1 or more (Dispositions worksheet); the highest-scoring entry traced to its ledger "
                     "lines (Drilldown worksheet).",
        "Parameters": "Weekend: WEEKDAY(CreatedDate,2)>5. Backdated: INT(CreatedDate)>PostingDate. SelfApproved: "
                      "CreatedByEmployeeID=ApprovedByEmployeeID. AboveLimit: TotalAmount above the approver's "
                      "MaxApprovalAmount (Employee). RoundAmount: MOD(TotalAmount,1000)=0.",
        "Results": f"{flagged} entries flagged: {sc[1]} with one flag, {sc[2]} with two, and {sc[4]} with four. "
                   "Flags: " + ", ".join(f"{k} {v}" for k, v in j["flags"].items()) + ".",
        "Exceptions and disposition": f"Expected, with evidence: {summary(expected)}. Follow up: {summary(follow)}. "
                                      "Details on the Dispositions worksheet.",
        "Conclusion": "The tests found no sign of a concealed misstatement in the recurring entries, but they found "
                      "weaknesses in how entries are approved. The opening balance entry, created after its date, "
                      "approved by its own creator, and carrying balances that the detail does not support, is the "
                      "first item for the audit committee; the approval of opening and recurring entries needs "
                      "follow-up before a conclusion on the control can be reached.",
        "Prepared by": PREPARED,
        "Reviewed by": ""})

    t = "8.3"
    b.check(t, "journal entries (rows of JournalEntries)", j["count"], "=ROWS(JournalEntries[EntryNumber])", 0, COUNT)
    b.check(t, "entries with a RiskScore", j["count"], "=COUNT(JournalEntries[RiskScore])", 0, COUNT)
    for r, name in enumerate(FLAGS, start=1):
        b.check(t, f"{name} flags (JE Summary!B{r})", j["flags"][name], f"='JE Summary'!B{r}", 0, COUNT)
    for r, s in enumerate(range(6), start=8):
        b.check(t, f"entries with a score of {s} (JE Summary!B{r})", sc[s], f"='JE Summary'!B{r}", 0, COUNT)
    b.check(t, "the only entry that scores 4", opening,
            "=XLOOKUP(4,JournalEntries[RiskScore],JournalEntries[EntryNumber])")
    c1, c2 = UNNAMED["je_creators"], UNNAMED["je_scores"]
    cfo = j["opening"]["creator"]["title"]
    b.check(t, f"PivotTable: entries created by the {cfo.lower()}", sum(v for (who, _), v in j["by_creator"].items()
                                                                       if who == cfo),
            "=" + pivot_count(c1, "Count of EntryNumber", "CreatorTitle", cfo), 0, COUNT)
    b.check(t, "PivotTable: depreciation entries created by the controller", j["by_creator"][("Controller", "Depreciation")],
            "=" + pivot_count(c1, "Count of EntryNumber", "CreatorTitle", "Controller", "EntryType", "Depreciation"),
            0, COUNT)
    b.check(t, "PivotTable: all entries", j["count"], "=" + pivot_count(c1, "Count of EntryNumber"), 0, COUNT)
    b.check(t, "PivotTable: depreciation entries with a score of 1 (the weekend month-ends)",
            j["by_score"][("Depreciation", 1)],
            "=" + pivot_count(c2, "Count of EntryNumber", "EntryType", "Depreciation", "RiskScore", 1), 0, COUNT)
    closes = sorted({k for k, _ in j["by_score"] if k.startswith("Year-End Close")})
    b.check(t, "PivotTable: year-end closes with a score of 1 (above the limit)",
            sum(j["by_score"][(k, 1)] for k in closes),
            "=" + "+".join(pivot_count(c2, "Count of EntryNumber", "EntryType", k, "RiskScore", 1) for k in closes),
            0, COUNT)
    risk_col = letter(width)
    b.check(t, "entries on the Dispositions worksheet", flagged, "=COUNTA(Dispositions!A:A)-1", 0, COUNT)
    b.check(t, "entries with a score of 0 among them", 0, f"=COUNTIF(Dispositions!{risk_col}:{risk_col},0)", 0, COUNT)
    b.check(t, "entries with a disposition", flagged, f"=COUNTA(Dispositions!{disp_col}:{disp_col})-1", 0, COUNT)
    b.check(t, "dispositions marked Expected", sum(v for k, v in categories.items() if k.startswith("expected")),
            f'=COUNTIF(Dispositions!{disp_col}:{disp_col},"Expected*")', 0, COUNT)
    b.check(t, "dispositions marked Follow up", sum(v for k, v in categories.items() if k.startswith("follow")),
            f'=COUNTIF(Dispositions!{disp_col}:{disp_col},"Follow up*")', 0, COUNT)
    b.check(t, "the first entry on the Dispositions worksheet", opening, "=Dispositions!A2")
    b.check(t, "entry totals (JE Summary!B15)", round(j["total"], 2), "='JE Summary'!B15")
    b.check(t, "ledger debits (JE Summary!B16)", round(j["debits"], 2), "='JE Summary'!B16")
    b.check(t, "entry totals less ledger debits", 0, "='JE Summary'!B15-'JE Summary'!B16")
    b.check(t, "journal entry lines (rows of JournalLines)", j["lines"], "=ROWS(JournalLines[VoucherNumber])", 0, COUNT)
    b.check(t, f"lines of {opening} (spilled from Drilldown!A4)", j["drill"]["lines"], "=ROWS(Drilldown!A4#)", 0, COUNT)
    b.check(t, "its accounts receivable line (account 1020)", round(j["drill"]["ar"], 2),
            "=SUMIFS(INDEX(Drilldown!A4#,0,3),INDEX(Drilldown!A4#,0,1),1020)")
    b.check(t, "its debits equal its credits", round(j["drill"]["debits"] - j["drill"]["credits"], 2),
            "=SUM(INDEX(Drilldown!A4#,0,3))-SUM(INDEX(Drilldown!A4#,0,4))")


TUTORIALS = [("8.1", t8_1), ("8.2", t8_2), ("8.3", t8_3)]
