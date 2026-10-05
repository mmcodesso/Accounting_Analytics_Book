"""Charles River Promotion Case.xlsx: the solution to the Part II comprehensive case (cases/part-2-case.qmd).

The case tells the reader to build a new workbook that reads CharlesRiver.xlsx, so the builder starts from a blank
workbook: its one worksheet becomes Documentation. Each function answers one Requirement with the queries (and the
Power Query Editor's step names), worksheets, formulas, PivotTables, what-if tools, and model answers it asks for, and
adds its checks to the Solution Notes: live formulas against values computed here, independently of Excel.

Expected values come from the facts registry of the case's instructor notes (facts/notes/case2.py and facts/db.py,
loaded here without the notes package, which needs jinja2), so the checks and the notes compute each value the same
way, and from further read-only queries of CharlesRiver.sqlite for the values the notes do not state.

What the builder decides where the case leaves a choice (the Documentation worksheet says so too):
  - Two queries the case does not name: LedgerActivity (T3_GLEntry for the case's three fiscal years, grouped by
    account, year, source document type, and journal entry, kept for the income-statement accounts: the commission
    rate's numerator and the postings to account 4070) and SourceCounts (the row count of each source Table, read from
    CharlesRiver.xlsx, so the completeness checks compare live counts).
  - Invoices is connection-only (it only feeds BilledLines); every other query is loaded to a worksheet named after it.
  - Changed Type corrections (Replace current): Discount to Decimal Number and PromotionID to Whole Number in OrderLines
    and BilledLines (from the first 200 rows, which carry no promotion, Power Query detects Discount as a whole number and
    PromotionID as Any), FreightAmount to Decimal Number in Invoices, and the date columns to Date.
  - The commission rate is calculated on the Parameters worksheet (Tutorial 7.3's formula, from LedgerActivity and
    BilledLines) rather than typed, so it is black, not blue.
  - Frozen values, each labeled where it sits: the break-even lifts Goal Seek found on R4 Model (the formula beside them
    stays live), the Furniture discount Goal Seek found, and the memo's text.
"""

from __future__ import annotations

import importlib.util
import math
import sys
import time
import types
from decimal import ROUND_HALF_UP, Decimal

import pythoncom

from paths import REPO
from xlbuild import notes, pq, xl
from xlbuild.solutions import COUNT, MONEY, PCT, RATIO, ExerciseBuild

DATE = "yyyy-mm-dd"
MA = "Model answer"
TOP = -4160                                                   # xlTop
R1, R2, R3, R4, R5, R6 = (f"Requirement {n}" for n in range(1, 7))
SCOPES = '{"Collection","ItemGroup","Segment"}'               # the ScopeType values, in CHOOSE's order
GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories", "Services"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December"]
PLAIN = (1, 2, 5, 6, 7, 8, 12)                                # months no promotion ran in, in any year
DOC_LABELS = ["Purpose", "Source", "Query steps", "Last refreshed", "Parameters", "Calculated columns", "Worksheets",
              "Conventions", "Prepared by", "Reviewed by", "Open questions"]
DOC_CHECKS = 17                                               # first row of the completeness checks on Documentation
LOADED = ["Promotions", "Orders", "Items", "Customers", "OrderLines", "BilledLines", "Accounts", "RevenuePostings",
          "LedgerActivity", "BudgetPrices", "Overrides", "Employees", "SourceCounts"]


# --- the instructor notes' own computations ---------------------------------------------------------------------------

def _registry():
    """facts/db.py and facts/notes/case2.py, loaded without the notes package (it imports jinja2, which the Excel
    environment lacks): the notes' @note decorator is replaced by one that leaves the function as it is."""
    stub = types.ModuleType("notes")
    stub.note = lambda *args, **kwargs: (lambda fn: fn)
    saved = sys.modules.get("notes")
    sys.modules["notes"] = stub
    try:
        loaded = []
        for name, path in (("case2_facts_db", REPO / "facts" / "db.py"),
                           ("case2_facts_notes", REPO / "facts" / "notes" / "case2.py")):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            loaded.append(module)
    finally:
        if saved is None:
            sys.modules.pop("notes", None)
        else:
            sys.modules["notes"] = saved
    return loaded


class Facts:
    """Every value the checks compare with, from CharlesRiver.sqlite (read-only)."""

    def __init__(self, year: int):
        dbmod, reg = _registry()
        self.reg = reg
        d = self.d = dbmod.Data()
        if d.C != year:
            raise SystemExit(f"case2: the report year is {year}, but the facts registry's window ends in {d.C}")
        claims: list[tuple[bool, str]] = []

        def claim(ok, text):
            claims.append((bool(ok), text))
        self.n1 = reg.r1(d, claim)
        self.n2 = reg.r2(d, claim)
        self.n3 = reg.r3(d, claim)
        self.n4 = reg.r4(d, claim)
        self.n5 = reg.r5(d, claim)
        self.n6 = reg.r6(d, claim)
        failed = [text for ok, text in claims if not ok]
        if failed:
            raise SystemExit("case2: claims of the instructor notes fail on this dataset: " + "; ".join(failed))
        q, one = d.q, d.one
        F, P, C, N = d.F, d.P, d.C, d.N
        ORD, BIL, BUD = reg.ORDERS, reg.BILLED, reg.BUDGET
        self.F, self.P, self.C, self.N = F, P, C, N
        self.promos = {p["id"]: p for p in reg.promotions(d)}
        self.ids = sorted(self.promos)
        self.proposal = reg.proposal(d)                              # scope type -> promotion of the report year
        self.rate = self.n1["rate"]

        # Requirement 1
        self.orders_total = one("SELECT SUM(OrderTotal) FROM SalesOrder")
        self.accounts = one("SELECT COUNT(*) FROM Account")
        self.order_mismatch = one(
            "SELECT COUNT(*) FROM SalesOrder o LEFT JOIN (SELECT SalesOrderID, SUM(LineTotal) AS s FROM SalesOrderLine "
            "GROUP BY 1) t ON t.SalesOrderID = o.SalesOrderID WHERE t.s IS NULL OR ABS(o.OrderTotal - t.s) >= 0.005")
        self.discounted_without = (one("SELECT COUNT(*) FROM SalesOrderLine WHERE PromotionID IS NULL AND Discount <> 0"),
                                   one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NULL AND Discount <> 0"))
        rates = sorted({r for (r,) in q("SELECT DISTINCT Discount FROM SalesOrderLine")})
        self.rates_text = ", ".join(f"{r:g}" for r in rates)
        promo_rates = sorted({0.0} | {p["rate"] for p in self.promos.values()})
        assert rates == promo_rates, (rates, promo_rates)
        self.ledger_debits, self.ledger_credits = q(
            "SELECT SUM(Debit), SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' "
            "AND PostingDate BETWEEN ? AND ?", f"{C}-01-01", f"{C}-12-31")[0]
        self.revenue_postings_accounts = one(
            "SELECT COUNT(DISTINCT AccountID) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' "
            "AND PostingDate BETWEEN ? AND ?", f"{C}-01-01", f"{C}-12-31")

        # Requirement 2
        self.year_lines = {int(y): n for y, n in q(
            f"SELECT substr(i.InvoiceDate, 1, 4), COUNT(*) {BIL} WHERE l.PromotionID IS NOT NULL GROUP BY 1")}
        self.promo_lines_billed = {pid: n for pid, n in q(
            "SELECT PromotionID, COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL GROUP BY 1")}
        self.cutoff = q(f"SELECT i.InvoiceNumber, i.InvoiceDate, COUNT(*), SUM(l.LineTotal) {BIL} "
                        f"WHERE substr(i.InvoiceDate, 1, 4) = ? AND substr(i.InvoiceNumber, 1, 7) = ? GROUP BY 1, 2 "
                        f"ORDER BY 1", str(P), f"SI-{C}")
        assert [r[0] for r in self.cutoff][0] == self.n2["first"] and self.cutoff[-1][0].endswith(self.n2["last"])
        self.cutoff_by_group = {g: v for g, v in q(
            f"SELECT it.ItemGroup, SUM(l.LineTotal) {BIL} JOIN Item it ON it.ItemID = l.ItemID "
            f"WHERE substr(i.InvoiceDate, 1, 4) = ? AND substr(i.InvoiceNumber, 1, 7) = ? GROUP BY 1", str(P), f"SI-{C}")}
        self.posted = {n: (dr, cr) for n, dr, cr in q(
            "SELECT a.AccountNumber, SUM(g.Debit), SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
            "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.PostingDate BETWEEN ? AND ? GROUP BY 1",
            f"{C}-01-01", f"{C}-12-31")}
        self.revenue_accounts = q("SELECT AccountNumber, AccountName, AccountSubType FROM Account WHERE AccountType = "
                                  "'Revenue' AND AccountSubType <> 'Header' ORDER BY AccountNumber")
        self.revenue_net = {(n, y): v for n, y, v in q(
            "SELECT a.AccountNumber, g.FiscalYear, SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a "
            "ON a.AccountID = g.AccountID WHERE a.AccountType = 'Revenue' AND g.SourceDocumentType <> 'JournalEntry' "
            "AND g.FiscalYear BETWEEN ? AND ? GROUP BY 1, 2", F, C)}
        self.discount_accounts = q("SELECT AccountNumber, AccountName, AccountType, AccountSubType FROM Account "
                                   "WHERE AccountName LIKE '%discount%' ORDER BY AccountNumber")
        self.account_postings = {n: c for n, c in q(
            "SELECT a.AccountNumber, COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
            "WHERE g.FiscalYear BETWEEN ? AND ? GROUP BY 1", F, C)}
        self.group_account = {g: n for g, n in q(
            "SELECT DISTINCT i.ItemGroup, a.AccountNumber FROM Item i JOIN Account a ON a.AccountID = i.RevenueAccountID")}

        # Requirement 3
        self.within = {pid: one(f"SELECT COUNT(*) {ORD} WHERE l.PromotionID = ? AND o.OrderDate BETWEEN ? AND ?",
                                pid, p["start"], p["end"]) for pid, p in self.promos.items()}
        for p in self.promos.values():
            m = p["months"]
            assert m == list(range(m[0], m[-1] + 1)) and p["lo"][:4] == p["hi"][:4], p
        self.vol = {v["id"]: v for v in reg.volume(d)}
        first = q("SELECT CustomerID, MIN(OrderDate) FROM SalesOrder GROUP BY 1")
        since = dict(q("SELECT CustomerID, CustomerSince FROM Customer"))
        self.first_early = sum(1 for _, dt in first if dt <= f"{F}-04-30")
        self.first_late = sum(1 for _, dt in first if dt > f"{F}-06-30")
        self.first_last = max(dt for _, dt in first)
        self.since = sum(1 for c, _ in first if since[c] >= f"{F}-01-01")
        self.since_before = sum(1 for c, dt in first if since[c] >= f"{F}-01-01" and dt < since[c])
        assert (self.since, self.since_before, len(first)) == (self.n3["since"], self.n3["since_before"],
                                                               self.n3["customers"])
        self.first_by_month = {}
        for _, dt in first:
            self.first_by_month[dt[:7]] = self.first_by_month.get(dt[:7], 0) + 1

        # Requirement 4
        c = self.rate
        self.models = {pid: reg.unit_model(d, pid) for pid in self.ids}
        self.be = reg.breakevens(d)
        self.model_c = {s: reg.unit_model(d, p["id"], C) for s, p in self.proposal.items()}
        fur = self.model_c["ItemGroup"]
        self.without = fur["units"] * (fur["price"] * (1 - c) - fur["cost"])

        def difference(rate: float, lift: float) -> float:
            return fur["units"] * (1 + lift) * (fur["price"] * (1 - rate) * (1 - c) - fur["cost"]) - self.without
        self.difference = difference
        self.be_at = {r: reg.breakeven(fur["price"], fur["cost"], r, c) for r in (0.05, 0.08, 0.10, 0.12)}
        self.best, self.goal_discount = reg.goal_seek(d)
        self.budget_all = {(y, m): r for y, m, r in q(
            f"SELECT b.FiscalYear, b.Month, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) {BUD} GROUP BY 1, 2")}
        self.budget_year = {y: r for y, r in q(
            f"SELECT b.FiscalYear, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) {BUD} GROUP BY 1")}
        self.budget_groups = [g for (g,) in q(f"SELECT DISTINCT i.ItemGroup {BUD}")]
        self.budget_groups = [g for g in GROUPS if g in self.budget_groups]
        self.budget_group = {(y, g, m): r for y, g, m, r in q(
            f"SELECT b.FiscalYear, i.ItemGroup, b.Month, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) {BUD} "
            f"GROUP BY 1, 2, 3")}
        self.november_not_lower = sum(
            1 for y in d.years for g in self.budget_groups
            if not self.budget_group[(y, g, 11)] < min(self.budget_group[(y, g, m)] for m in PLAIN))
        self.max_dev = max(abs(self.budget_all[(N, m)] - self.budget_year[N]) for m in range(1, 13))
        self.promoted = []                                       # (promotion, ratio in its months, in the others)
        tot = [0.0, 0.0]
        for pid in self.ids:
            p = self.promos[pid]
            if p["scope"] not in ("Collection", "ItemGroup") or p["year"] > C:
                continue
            column = "i.CollectionName" if p["scope"] == "Collection" else "i.ItemGroup"
            m1, m2 = p["months"][0], p["months"][-1]
            a, b_ = q(f"SELECT SUM(b.BudgetAmount), SUM(b.Quantity * i.ListPrice) {BUD} AND b.FiscalYear = ? "
                      f"AND {column} = ? AND b.Month BETWEEN ? AND ?", p["year"], p["label"], m1, m2)[0]
            a2, b2 = q(f"SELECT SUM(b.BudgetAmount), SUM(b.Quantity * i.ListPrice) {BUD} AND b.FiscalYear = ? "
                       f"AND {column} = ? AND b.Month NOT BETWEEN ? AND ?", p["year"], p["label"], m1, m2)[0]
            self.promoted.append(dict(id=pid, ratio=a / b_, other=a2 / b2))
            tot[0] += a
            tot[1] += b_
        self.promoted_ratio = tot[0] / tot[1]
        assert abs(self.promoted_ratio - self.n4["promoted"]) < 1e-12
        self.cfo_name, self.cfo_title = q("SELECT EmployeeName, JobTitle FROM Employee WHERE EmployeeID = ?",
                                          self.n4["cfo"])[0]
        self.prop_quarters = dict(self.n4["quarters"])
        self.prop_quarters_exact = {}
        for p in self.n2["prop"]:
            for qn, v in p["quarters"]:
                self.prop_quarters_exact[qn] = self.prop_quarters_exact.get(qn, 0.0) + v

        # Requirement 5
        self.scope_exc = {pid: n for pid, n in q(
            f"SELECT l.PromotionID, COUNT(*) {ORD} JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
            f"WHERE NOT {reg.IN_SCOPE} GROUP BY 1")}
        self.rate_exc = one(f"SELECT COUNT(*) {ORD} JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                            f"WHERE ABS(l.Discount - p.DiscountPct) > 1e-9")
        self.oos = q(f"SELECT l.SalesOrderLineID, l.PromotionID, o.OrderDate, i.ItemCode, i.ItemName {ORD} "
                     f"JOIN PromotionProgram p ON p.PromotionID = l.PromotionID WHERE NOT {reg.IN_SCOPE} "
                     f"ORDER BY l.SalesOrderLineID")
        self.no_collection = q("SELECT ItemCode, ItemName FROM Item WHERE CollectionName IS NULL AND ItemGroup IN "
                               "(SELECT ItemGroup FROM Item WHERE CollectionName IS NOT NULL) ORDER BY ItemID")
        collections = {r for (r,) in q("SELECT DISTINCT CollectionName FROM Item WHERE CollectionName IS NOT NULL")}
        self.named_for = sum(1 for _, name in self.no_collection if name.split()[0] in collections)
        self.bad = [p["id"] for p in self.n5["bad"]]
        self.end_not_after = sum(1 for p in self.promos.values() if p["end"] <= p["start"])
        self.collection_ratios = {pid: reg.monthly_ratios(d, self.promos[pid]["year"], "i.CollectionName",
                                                          self.promos[pid]["label"]) for pid in self.bad}
        self.budget_planned = sum(1 for pid in self.bad for r in [self.collection_ratios[pid]]
                                  if max(r[m] for m in self.promos[pid]["months"]) < min(r[m] for m in PLAIN) - 0.02)
        self.pending_requested = one("SELECT COUNT(*) FROM PriceOverrideApproval WHERE Status = 'Pending' "
                                     "AND RequestedByEmployeeID = ?", self.n5["mgr"]["id"])
        self.pending_billed = one("SELECT COUNT(*) FROM PriceOverrideApproval a WHERE a.Status = 'Pending' AND EXISTS "
                                  "(SELECT 1 FROM SalesInvoiceLine l WHERE l.SalesOrderLineID = a.SalesOrderLineID)")
        self.requesters = ", ".join(sorted({t for (t,) in q(
            "SELECT DISTINCT e.JobTitle FROM PriceOverrideApproval a JOIN Employee e ON e.EmployeeID = "
            "a.RequestedByEmployeeID WHERE a.RequestedByEmployeeID <> ?", self.n5["mgr"]["id"])}, key=str.lower))
        self.overrides_total = one("SELECT COUNT(*) FROM PriceOverrideApproval")

    # --- shared --------------------------------------------------------------------------------------------------
    def promo(self, scope: str) -> dict:
        return self.proposal[scope]


def facts(b: ExerciseBuild) -> Facts:
    if "facts" not in b.found:
        b.found["facts"] = Facts(b.year)
    return b.found["facts"]


# --- text -------------------------------------------------------------------------------------------------------------

def _half_up(x: float, places: int) -> Decimal:
    return Decimal(repr(float(f"{x:.15g}"))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def money(x: float, places: int = 2) -> str:
    return f"{_half_up(x, places):,.{places}f}"


def pct(x: float, places: int = 1) -> str:
    return f"{_half_up(100 * x, places):.{places}f}%"


def spct(x: float, places: int = 1) -> str:
    return ("+" if x >= 0 else "-") + pct(abs(x), places)


WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


def word(n: int, capital: bool = False) -> str:
    text = WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"
    return text[0].upper() + text[1:] if capital else text


def series(items) -> str:
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else " and ".join(items) if len(items) == 2 else \
        ", ".join(items[:-1]) + ", and " + items[-1]


def serial(iso: str) -> int:
    """An ISO date as Excel's date serial (a date-like text would be turned into a date by Excel)."""
    from datetime import date
    return (date.fromisoformat(iso[:10]) - date(1899, 12, 30)).days


def long_date(iso: str) -> str:
    y, m, d = (int(x) for x in iso[:10].split("-"))
    return f"{MONTH_NAMES[m - 1]} {d}, {y}"


# --- worksheet helpers ------------------------------------------------------------------------------------------------

def col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def put(ws, cells: dict) -> None:
    for addr, value in cells.items():
        if isinstance(value, str) and value.startswith("="):
            ws.Range(addr).Formula2 = value
        else:
            ws.Range(addr).Value = value


def fmt(ws, addr: str, number_format: str) -> None:
    ws.Range(addr).NumberFormat = number_format


def bold(ws, addr: str) -> None:
    ws.Range(addr).Font.Bold = True


def blue(ws, addr: str) -> None:
    ws.Range(addr).Font.Color = xl.BLUE


def title(ws, text: str) -> None:
    ws.Range("A1").Value = text
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 13


def heading(ws, row: int, text: str, column: int = 1) -> None:
    ws.Cells(row, column).Value = text
    ws.Cells(row, column).Font.Bold = True
    ws.Cells(row, column).Font.Size = 12


def header(ws, row: int, column: int, names: list) -> None:
    for i, name in enumerate(names):
        ws.Cells(row, column + i).Value = name
    rng = ws.Range(ws.Cells(row, column), ws.Cells(row, column + len(names) - 1))
    rng.Font.Bold = True
    rng.WrapText = True
    rng.VerticalAlignment = TOP


def widths(ws, spec: dict) -> None:
    for cols, w in spec.items():
        ws.Columns(cols).ColumnWidth = w


def note(ws, addr: str, text: str) -> None:
    ws.Range(addr).AddComment(text)
    ws.Range(addr).Comment.Shape.Width = 300
    ws.Range(addr).Comment.Shape.Height = 120


def text_block(ws, row: int, label: str, paragraphs: list[str], span: int = 10, column: int = 1) -> int:
    """A labeled block of wrapped text, one merged row per paragraph; returns the next free row (after a gap)."""
    ws.Cells(row, column).Value = label
    ws.Cells(row, column).Font.Bold = True
    width = sum(ws.Columns(column + i).ColumnWidth for i in range(span))
    r = row + 1
    for p in paragraphs:
        rng = ws.Range(ws.Cells(r, column), ws.Cells(r, column + span - 1))
        rng.Merge()
        rng.WrapText = True
        rng.VerticalAlignment = TOP
        ws.Cells(r, column).Value = p
        lines = sum(math.ceil(max(1, len(part)) * 1.12 / max(width, 20)) for part in p.split("\n")) + 0.4
        ws.Rows(r).RowHeight = min(409, max(15, 15 * lines))
        r += 1
    return r + 1


def new_sheet(b: ExerciseBuild, name: str):
    """A worksheet just before the Solution Notes (or last, before the notes exist)."""
    names = [ws.Name for ws in b.wb.Worksheets]
    if notes.NOTES_SHEET in names:
        return xl.sheet(b.wb, name, before=b.wb.Worksheets(notes.NOTES_SHEET))
    return xl.sheet(b.wb, name)


def q_(sheet: str) -> str:
    return f"'{sheet}'"


def settle(b: ExerciseBuild, quiet: float = 3.0, timeout: float = 900.0) -> None:
    """Recalculate and wait until Excel has stayed ready for a few seconds."""
    app = b.wb.Application
    xl.retry(app.CalculateFull)
    deadline = time.time() + timeout
    calm = None
    while time.time() < deadline:
        try:
            ready = app.Ready and app.CalculationState == 0
        except pythoncom.com_error as exc:
            if exc.hresult not in xl.BUSY:
                raise
            ready = False
        now = time.time()
        if not ready:
            calm = None
        elif calm is None:
            calm = now
        elif now - calm >= quiet:
            return
        time.sleep(0.25)
    raise TimeoutError("Excel stayed busy")


def nav(b: ExerciseBuild, number: int, table: str, corrections: dict | None = None, extra=()) -> str:
    return pq.navigator_query(b.src, number, table, list(pq.detected_types(b.xlsx, table)), corrections, list(extra))


def group_rows(keys: list[str], aggregates: list[tuple[str, str, str]]) -> str:
    """Group By (Advanced): the keys, and (new column, M expression over the group, type) aggregates."""
    k = "{" + ", ".join(pq.m_string(c) for c in keys) + "}"
    a = "{" + ", ".join("{" + f"{pq.m_string(n)}, each {e}, {t}" + "}" for n, e, t in aggregates) + "}"
    return f"Table.Group({{prev}}, {k}, {a})"


def sort_rows(columns: list[str]) -> str:
    return "Table.Sort({prev},{" + ", ".join("{" + f"{pq.m_string(c)}, Order.Ascending" + "}" for c in columns) + "})"


def date_columns(lo, names: list[str]) -> None:
    for name in names:
        lo.ListColumns(name).DataBodyRange.NumberFormat = DATE


def gpd(field: str, sheet: str, anchor: str, *pairs) -> str:
    """A GETPIVOTDATA formula (without the =)."""
    items = "".join(f',"{k}",{v}' if isinstance(v, (int, float)) else f',"{k}","{v}"' for k, v in zip(pairs[::2], pairs[1::2]))
    return f'GETPIVOTDATA("{field}",{q_(sheet)}!{anchor}{items})'


def scope_range(table: str) -> str:
    """The column a promotion's scope is read from, chosen by its ScopeType (CHOOSE returns a reference for SUMIFS)."""
    return f"{table}[CollectionName],{table}[ItemGroup],{table}[CustomerSegment]"


# --- Documentation ------------------------------------------------------------------------------------------------------

def write_doc(b: ExerciseBuild) -> None:
    """(Re)write the Documentation entries (rows 1 to 15); the completeness checks below them are written once."""
    st = b.found["doc"]
    ws = b.wb.Worksheets("Documentation")
    ws.Range(f"A1:B{DOC_CHECKS - 2}").ClearContents()
    order = [s.Name for s in b.wb.Worksheets if s.Name in st["sheets"]]
    st["entries"]["Worksheets"] = "; ".join(f"{s}: {st['sheets'][s]}" for s in order)
    st["entries"]["Last refreshed"] = "'" + pq.today()
    rows = [(label, st["entries"].get(label, "")) for label in DOC_LABELS] + [tuple(x) for x in st["extra"]]
    assert len(rows) <= DOC_CHECKS - 2, "the Documentation entries reach the checks below them"
    for i, (label, text) in enumerate(rows, start=1):
        ws.Cells(i, 1).Value = label
        ws.Cells(i, 2).Value = text
        ws.Cells(i, 1).Font.Bold = True
        ws.Cells(i, 2).WrapText = True
    ws.Range(f"A1:B{len(rows)}").VerticalAlignment = TOP
    ws.Range(f"A1:A{len(rows)}").Rows.AutoFit()
    for i in range(1, len(rows) + 1):
        ws.Rows(i).AutoFit()


# --- Requirement 1 ------------------------------------------------------------------------------------------------------

def dates(*names: str) -> dict:
    return {n: "type date" for n in names}


AMOUNTS = [("Added Custom2", pq.add_custom("ListAmount", "[Quantity] * [BaseListPrice]")),
           ("Added Custom3", pq.add_custom("GrossAmount", "[Quantity] * [UnitPrice]")),
           ("Added Custom4", pq.add_custom("DiscountAmount", "[GrossAmount] * [Discount]"))]
LINE_TYPES = {"Discount": "type number", "PromotionID": "Int64.Type"}      # Replace current, in Changed Type
SOURCES = {"Promotions": "T7_PromotionProgram", "Orders": "T9_SalesOrder", "Items": "T44_Item",
           "Customers": "T4_Customer", "OrderLines": "T10_SalesOrderLine", "BilledLines": "T17_SalesInvoiceLine",
           "Accounts": "T1_Account", "BudgetPrices": "T77_BudgetLine", "Overrides": "T8_PriceOverrideApproval",
           "Employees": "T74_Employee"}
KEYS = {"Promotions": "PromotionID", "Orders": "SalesOrderID", "Items": "ItemID", "Customers": "CustomerID",
        "OrderLines": "SalesOrderLineID", "BilledLines": "SalesInvoiceLineID", "Accounts": "AccountID",
        "BudgetPrices": "BudgetLineID", "Overrides": "PriceOverrideApprovalID", "Employees": "EmployeeID"}
DATE_COLUMNS = {"Promotions": ["EffectiveStartDate", "EffectiveEndDate", "ApprovedDate"], "Orders": ["OrderDate"],
                "Items": ["LaunchDate"], "Customers": ["CustomerSince"],
                "OrderLines": ["OrderDate", "EffectiveStartDate", "EffectiveEndDate"], "BilledLines": ["InvoiceDate"],
                "BudgetPrices": ["ApprovedDate"], "Overrides": ["RequestDate", "ApprovedDate"],
                "Employees": ["HireDate", "TerminationDate"]}


def add_queries(b: ExerciseBuild) -> None:
    wb, y, F = b.wb, b.year, b.year - 2
    xl.add_query(wb, "Employees", nav(b, 74, "Employee", dates("HireDate", "TerminationDate"), extra=[
        ("Removed Other Columns", pq.select_columns(["EmployeeID", "EmployeeName", "CostCenterID", "JobTitle", "HireDate",
                                                     "EmploymentStatus", "TerminationDate", "MaxApprovalAmount"]))]))
    xl.add_query(wb, "Promotions", nav(b, 7, "PromotionProgram", dates("EffectiveStartDate", "EffectiveEndDate",
                                                                       "ApprovedDate"), extra=[
        ("Renamed Columns", pq.rename([("CustomerSegment", "PromoSegment"), ("ItemGroup", "PromoItemGroup"),
                                       ("CollectionName", "PromoCollection")]))]))
    xl.add_query(wb, "Orders", nav(b, 9, "SalesOrder", dates("OrderDate", "RequestedDeliveryDate"), extra=[
        ("Removed Other Columns", pq.select_columns(["SalesOrderID", "OrderNumber", "OrderDate", "CustomerID", "Status",
                                                     "OrderTotal"]))]))
    xl.add_query(wb, "Invoices", nav(b, 16, "SalesInvoice", {**dates("InvoiceDate", "DueDate", "PaymentDate"),
                                                              "FreightAmount": "type number"}, extra=[
        ("Removed Other Columns", pq.select_columns(["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SalesOrderID",
                                                     "CustomerID", "SubTotal", "FreightAmount"]))]))
    xl.add_query(wb, "Items", nav(b, 44, "Item", dates("LaunchDate"), extra=[
        ("Removed Other Columns", pq.select_columns(["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType",
                                                     "StandardCost", "ListPrice", "StandardFixedOverheadCost",
                                                     "RevenueAccountID", "CollectionName", "PrimaryMaterial",
                                                     "LifecycleStatus", "LaunchDate", "IsActive"]))]))
    xl.add_query(wb, "Customers", nav(b, 4, "Customer", dates("CustomerSince"), extra=[
        ("Removed Other Columns", pq.select_columns(["CustomerID", "CustomerName", "CustomerSince", "CustomerSegment",
                                                     "Region", "IsActive"]))]))
    xl.add_query(wb, "Accounts", nav(b, 1, "Account", extra=[
        ("Removed Other Columns", pq.select_columns(["AccountID", "AccountNumber", "AccountName", "AccountType",
                                                     "AccountSubType", "NormalBalance", "IsActive"]))]))
    xl.add_query(wb, "OrderLines", nav(b, 10, "SalesOrderLine", LINE_TYPES, extra=[
        ("Merged Queries", pq.merge("Orders", "SalesOrderID", "SalesOrderID", "Orders")),
        ("Expanded Orders", pq.expand("Orders", ["OrderDate", "CustomerID"])),
        ("Merged Queries1", pq.merge("Items", "ItemID", "ItemID", "Items")),
        ("Expanded Items", pq.expand("Items", ["ItemCode", "ItemName", "ItemGroup", "CollectionName", "StandardCost"])),
        ("Merged Queries2", pq.merge("Customers", "CustomerID", "CustomerID", "Customers")),
        ("Expanded Customers", pq.expand("Customers", ["CustomerSegment"])),
        ("Merged Queries3", pq.merge("Promotions", "PromotionID", "PromotionID", "Promotions")),
        ("Expanded Promotions", pq.expand("Promotions", ["ScopeType", "PromoItemGroup", "PromoCollection", "PromoSegment",
                                                         "DiscountPct", "EffectiveStartDate", "EffectiveEndDate"])),
        ("Added Custom", pq.add_custom("OrderYear", "Date.Year([OrderDate])")),
        ("Added Custom1", pq.add_custom("OrderMonth", "Date.Month([OrderDate])")),
        *AMOUNTS,
        ("Changed Type1", pq.transform_types([("OrderYear", "Int64.Type"), ("OrderMonth", "Int64.Type"),
                                              ("ListAmount", "type number"), ("GrossAmount", "type number"),
                                              ("DiscountAmount", "type number")]))]))
    xl.add_query(wb, "BilledLines", nav(b, 17, "SalesInvoiceLine", LINE_TYPES, extra=[
        ("Merged Queries", pq.merge("Invoices", "SalesInvoiceID", "SalesInvoiceID", "Invoices")),
        ("Expanded Invoices", pq.expand("Invoices", ["InvoiceNumber", "InvoiceDate"])),
        ("Merged Queries1", pq.merge("Items", "ItemID", "ItemID", "Items")),
        ("Expanded Items", pq.expand("Items", ["ItemGroup", "StandardCost"])),
        ("Added Custom", pq.add_custom("InvoiceYear", "Date.Year([InvoiceDate])")),
        ("Added Custom1", pq.add_custom("InvoiceQuarter", "Date.QuarterOfYear([InvoiceDate])")),
        *AMOUNTS,
        ("Changed Type1", pq.transform_types([("InvoiceYear", "Int64.Type"), ("InvoiceQuarter", "Int64.Type"),
                                              ("ListAmount", "type number"), ("GrossAmount", "type number"),
                                              ("DiscountAmount", "type number")]))]))
    # T3_GLEntry with Transform Data: filtered before anything is loaded, then grouped
    xl.add_query(wb, "RevenuePostings", nav(b, 3, "GLEntry", dates("PostingDate"), extra=[
        ("Filtered Rows", pq.select_rows('([SourceDocumentType] = "SalesInvoice")')),
        ("Filtered Rows1", pq.select_rows(f"Date.Year([PostingDate]) = {y}")),
        ("Merged Queries", pq.merge("Accounts", "AccountID", "AccountID", "Accounts")),
        ("Expanded Accounts", pq.expand("Accounts", ["AccountNumber"])),
        ("Grouped Rows", group_rows(["AccountNumber"], [("Credit", "List.Sum([Credit])", "type nullable number"),
                                                         ("Debit", "List.Sum([Debit])", "type nullable number")])),
        ("Sorted Rows", sort_rows(["AccountNumber"]))]))
    xl.add_query(wb, "LedgerActivity", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", pq.select_rows(f"[FiscalYear] >= {F} and [FiscalYear] <= {y}")),
        ("Added Custom", pq.add_custom("JournalEntry",
                                       'if [SourceDocumentType] = "JournalEntry" then [VoucherNumber] else null')),
        ("Grouped Rows", group_rows(["AccountID", "FiscalYear", "SourceDocumentType", "JournalEntry"],
                                    [("Postings", "Table.RowCount(_)", "Int64.Type"),
                                     ("Debit", "List.Sum([Debit])", "type nullable number"),
                                     ("Credit", "List.Sum([Credit])", "type nullable number")])),
        ("Merged Queries", pq.merge("Accounts", "AccountID", "AccountID", "Accounts")),
        ("Expanded Accounts", pq.expand("Accounts", ["AccountNumber", "AccountName", "AccountType"])),
        ("Filtered Rows1", pq.select_rows('([AccountType] = "Revenue" or [AccountType] = "Expense")')),
        ("Changed Type1", pq.transform_types([("JournalEntry", "type text")])),
        ("Sorted Rows", sort_rows(["AccountNumber", "FiscalYear", "SourceDocumentType"]))]))
    xl.add_query(wb, "BudgetPrices", nav(b, 77, "BudgetLine", dates("ApprovedDate"), extra=[
        ("Filtered Rows", pq.select_rows('([BudgetCategory] = "Revenue")')),
        ("Removed Other Columns", pq.select_columns(["BudgetLineID", "FiscalYear", "Month", "ItemID", "Quantity",
                                                     "UnitAmount", "BudgetAmount", "BudgetCategory",
                                                     "ApprovedByEmployeeID", "ApprovedDate"])),
        ("Merged Queries", pq.merge("Items", "ItemID", "ItemID", "Items")),
        ("Expanded Items", pq.expand("Items", ["ItemCode", "ItemGroup", "CollectionName", "ListPrice"])),
        ("Added Custom", pq.add_custom("ListAmount", "[Quantity] * [ListPrice]")),
        ("Changed Type1", pq.transform_types([("ListAmount", "type number")]))]))
    xl.add_query(wb, "Overrides", nav(b, 8, "PriceOverrideApproval", dates("RequestDate", "ApprovedDate"), extra=[
        ("Merged Queries", pq.merge("Employees", "RequestedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees", pq.expand("Employees", ["EmployeeName", "JobTitle"])),
        ("Renamed Columns", pq.rename([("EmployeeName", "RequesterName"), ("JobTitle", "RequesterTitle")])),
        ("Merged Queries1", pq.merge("Employees", "ApprovedByEmployeeID", "EmployeeID", "Employees")),
        ("Expanded Employees1", pq.expand("Employees", ["EmployeeName", "JobTitle"])),
        ("Renamed Columns1", pq.rename([("EmployeeName", "ApproverName"), ("JobTitle", "ApproverTitle")]))]))
    tables = ", ".join(pq.m_string(t) for t in SOURCES.values())
    xl.add_query(wb, "SourceCounts", pq.steps_query([
        ("Source", f"Excel.Workbook(File.Contents({pq.m_string(b.src)}), null, true)"),
        ("Filtered Rows", 'Table.SelectRows({prev}, each [Kind] = "Table" and List.Contains({' + tables + '}, [Name]))'),
        ("Added Custom", 'Table.AddColumn({prev}, "Rows", each Table.RowCount([Data]), Int64.Type)'),
        ("Added Custom1", 'Table.AddColumn({prev}, "RevenueRows", each if [Name] = "T77_BudgetLine" then Table.RowCount('
                          'Table.SelectRows([Data], each [BudgetCategory] = "Revenue")) else null, Int64.Type)'),
        ("Removed Other Columns", pq.select_columns(["Name", "Rows", "RevenueRows"])),
        ("Sorted Rows", sort_rows(["Name"]))]))


def parameters(b: ExerciseBuild, ws) -> None:
    wb = b.wb
    put(ws, {"A1": "Parameter", "B1": "Value", "C1": "Name", "D1": "Description"})
    rows = [
        (3, "Harbor Collection discount, proposed", 0.08, "HarborRate",
         "The proposal: 8 percent off the items of the Harbor collection in March and April"),
        (4, "Furniture Seasonal discount, proposed", 0.10, "FurnitureRate",
         "The proposal: 10 percent off every Furniture item in September and October"),
        (5, "Design Trade Customer discount, proposed", 0.12, "DesignTradeRate",
         "The proposal: 12 percent off every order from Design Trade customers in November"),
        (6, "Commission rate", "=B18/B19", "CommissionRate",
         "Tutorial 7.3: the report year's commission expense over its invoice-line revenue (rows 18 and 19)"),
        (7, "Report year", b.year, "ReportYear", "The fiscal year whose promotion calendar the proposal repeats"),
        (8, "First year of the data", "=ReportYear-2", "FirstYear", "The first fiscal year of the case"),
        (9, "Plan year", "=ReportYear+1", "PlanYear", "The year of the proposal and of the budget it is costed against"),
    ]
    for r, label, value, name, text in rows:
        put(ws, {f"A{r}": label, f"B{r}": value, f"C{r}": name, f"D{r}": text})
        xl.name_cell(wb, name, f"Parameters!$B${r}")
    blue(ws, "B3:B5")
    blue(ws, "B7")
    fmt(ws, "B3:B5", "0%")
    fmt(ws, "B6", "0.000%")
    fmt(ws, "B7:B9", "0")
    put(ws, {"A11": "Promotion the proposal repeats", "B11": "PromotionID", "C11": "Name",
             "D11": "Its DiscountPct in the report year"})
    for r, label, scope, name in ((12, "Harbor Collection Promotion", "Collection", "HarborPromotion"),
                                  (13, "Furniture Seasonal Promotion", "ItemGroup", "FurniturePromotion"),
                                  (14, "Design Trade Customer Promotion", "Segment", "DesignTradePromotion")):
        put(ws, {f"A{r}": label, f"C{r}": name,
                 f"B{r}": f'=XLOOKUP(1,(Promotions[ScopeType]="{scope}")*(YEAR(Promotions[EffectiveStartDate])='
                          f"ReportYear),Promotions[PromotionID])",
                 f"D{r}": f"=XLOOKUP(B{r},Promotions[PromotionID],Promotions[DiscountPct])"})
        xl.name_cell(wb, name, f"Parameters!$B${r}")
    fmt(ws, "D12:D14", "0%")
    put(ws, {"A17": "How the commission rate is calculated (Tutorial 7.3)",
             "A18": "Commission expense, report year: account 6290 without journal entries (LedgerActivity)",
             "B18": ('=SUMIFS(LedgerActivity[Debit],LedgerActivity[AccountNumber],6290,LedgerActivity[FiscalYear],'
                     'ReportYear,LedgerActivity[SourceDocumentType],"<>JournalEntry")-SUMIFS(LedgerActivity[Credit],'
                     'LedgerActivity[AccountNumber],6290,LedgerActivity[FiscalYear],ReportYear,'
                     'LedgerActivity[SourceDocumentType],"<>JournalEntry")'),
             "A19": "Invoice-line revenue, report year (BilledLines)",
             "B19": "=SUMIFS(BilledLines[LineTotal],BilledLines[InvoiceYear],ReportYear)",
             "A20": "Journal entries posting to 6290 in the report year (left out: the year-end close)",
             "B20": ('=TEXTJOIN(", ",TRUE,FILTER(LedgerActivity[JournalEntry],(LedgerActivity[AccountNumber]=6290)*'
                     '(LedgerActivity[FiscalYear]=ReportYear)*(LedgerActivity[SourceDocumentType]="JournalEntry"),'
                     '"none"))')})
    fmt(ws, "B18:B19", MONEY)
    bold(ws, "A1:D1")
    bold(ws, "A11:D11")
    bold(ws, "A17")
    widths(ws, {"A": 62, "B": 18, "C": 22, "D": 80})


def doc_checks(b: ExerciseBuild, ws) -> int:
    """The completeness checks of Requirement 1, below the Documentation entries; returns the next free row."""
    r0 = DOC_CHECKS
    heading(ws, r0, "Completeness checks (Requirement 1): each query against its source, before the analysis uses it")
    header(ws, r0 + 1, 1, ["Check", "Compared with", "Query", "Source", "Agrees"])
    rows = []
    for q, t in SOURCES.items():
        source = (f'=XLOOKUP("{t}",SourceCounts[Name],SourceCounts[RevenueRows])' if q == "BudgetPrices"
                  else f'=XLOOKUP("{t}",SourceCounts[Name],SourceCounts[Rows])')
        what = (f"{t}: rows with BudgetCategory Revenue (SourceCounts)" if q == "BudgetPrices"
                else f"{t}: rows (SourceCounts)")
        rows.append((f"{q}: rows loaded", what, f"=ROWS({q}[{KEYS[q]}])", source, COUNT, "eq"))
    rows += [
        ("OrderLines: total LineTotal", "Orders: total OrderTotal", "=SUM(OrderLines[LineTotal])",
         "=SUM(Orders[OrderTotal])", MONEY, "round"),
        ("Orders whose OrderTotal differs from their own lines (Orders[LinesAgree])", "none expected",
         "=COUNTIF(Orders[LinesAgree],FALSE)", 0, COUNT, "eq"),
        ("Order lines without a PromotionID that carry a discount", "none expected",
         '=COUNTIFS(OrderLines[PromotionID],"",OrderLines[Discount],"<>0")', 0, COUNT, "eq"),
        ("Billed lines without a PromotionID that carry a discount", "none expected",
         '=COUNTIFS(BilledLines[PromotionID],"",BilledLines[Discount],"<>0")', 0, COUNT, "eq"),
        ("Discount rates in OrderLines (the decimal type keeps them)", "zero and the promotions' DiscountPct",
         '=TEXTJOIN(", ",TRUE,SORT(UNIQUE(OrderLines[Discount])))',
         '=TEXTJOIN(", ",TRUE,SORT(UNIQUE(VSTACK(0,Promotions[DiscountPct]))))', "General", "eq"),
        ("Discount rates in BilledLines", "zero and the promotions' DiscountPct",
         '=TEXTJOIN(", ",TRUE,SORT(UNIQUE(BilledLines[Discount])))',
         '=TEXTJOIN(", ",TRUE,SORT(UNIQUE(VSTACK(0,Promotions[DiscountPct]))))', "General", "eq"),
        ("OrderLines lookups not matched (OrderDate, ItemCode, CustomerSegment, a promotion's ScopeType)",
         "none expected",
         ('=COUNTBLANK(OrderLines[OrderDate])+COUNTBLANK(OrderLines[ItemCode])+COUNTBLANK(OrderLines[CustomerSegment])'
          '+COUNTIFS(OrderLines[PromotionID],"<>",OrderLines[ScopeType],"")'), 0, COUNT, "eq"),
        ("BilledLines lookups not matched (InvoiceDate, ItemGroup)", "none expected",
         "=COUNTBLANK(BilledLines[InvoiceDate])+COUNTBLANK(BilledLines[ItemGroup])", 0, COUNT, "eq"),
        ("RevenuePostings: total debits", "RevenuePostings: total credits (each sales invoice posts in balance)",
         "=SUM(RevenuePostings[Debit])", "=SUM(RevenuePostings[Credit])", MONEY, "round"),
    ]
    first = r0 + 2
    for i, (label, what, query, source, number_format, kind) in enumerate(rows):
        r = first + i
        put(ws, {f"A{r}": label, f"B{r}": what, f"C{r}": query, f"D{r}": source})
        ws.Range(f"E{r}").Formula = f"=ROUND(C{r}-D{r},2)=0" if kind == "round" else f"=C{r}=D{r}"
        fmt(ws, f"C{r}:D{r}", number_format)
    last = first + len(rows) - 1
    put(ws, {f"A{last + 1}": "All completeness checks agree", f"E{last + 1}": f"=AND(E{first}:E{last})"})
    bold(ws, f"A{last + 1}:E{last + 1}")
    xl.name_cell(b.wb, "DocChecksAgree", f"Documentation!$E${last + 1}")
    r = last + 3
    heading(ws, r, "Control totals")
    totals = [("Order lines that carry a PromotionID", '=COUNTIF(OrderLines[PromotionID],"<>")', COUNT),
              ("Their DiscountAmount (unrounded GrossAmount x Discount)",
               '=SUMIFS(OrderLines[DiscountAmount],OrderLines[PromotionID],"<>")', MONEY),
              ("BilledLines: total LineTotal", "=SUM(BilledLines[LineTotal])", MONEY),
              ("RevenuePostings: accounts the report year's sales invoices post to",
               "=ROWS(RevenuePostings[AccountNumber])", COUNT)]
    for i, (label, formula, number_format) in enumerate(totals, start=1):
        put(ws, {f"A{r + i}": label, f"C{r + i}": formula})
        fmt(ws, f"C{r + i}", number_format)
    end = r + len(totals)
    ws.Range(f"A{r0}:E{end}").WrapText = True
    ws.Range(f"A{r0}:E{end}").VerticalAlignment = TOP
    for i in range(r0, end + 1):
        ws.Rows(i).AutoFit()
    return end + 1


def r1(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    y, F = b.year, f.F
    doc = wb.Worksheets(1)
    doc.Name = "Documentation"
    par = xl.sheet(wb, "Parameters", after=doc)
    add_queries(b)
    last, tables = par, {}
    for name in LOADED:
        lo = xl.load_query(wb, name, name, after=last)
        xl.wait_ready(wb.Application)
        tables[name] = lo
        last = lo.Parent
        for c in DATE_COLUMNS.get(name, []):
            lo.ListColumns(c).DataBodyRange.NumberFormat = DATE
    for name in ("OrderLines", "BilledLines"):
        for c in ("ListAmount", "GrossAmount", "DiscountAmount"):
            tables[name].ListColumns(c).DataBodyRange.NumberFormat = MONEY
    orders = tables["Orders"]
    xl.add_column(orders, "LinesTotal", "=SUMIFS(OrderLines[LineTotal],OrderLines[SalesOrderID],[@SalesOrderID])", MONEY)
    xl.add_column(orders, "LinesAgree", "=ABS([@OrderTotal]-[@LinesTotal])<0.005")
    parameters(b, par)

    widths(doc, {"A": 34, "B": 100, "C": 18, "D": 18, "E": 10})
    doc_checks(b, doc)
    bad = series(str(i) for i in f.bad)
    b.found["doc"] = dict(entries={
        "Purpose": (f"Decide whether Charles River should run the sales team's proposed {f.N} promotion calendar (the "
                    f"{y} calendar repeated at the same rates), for the controller: what three years of promotions "
                    "cost and where the cost appears, whether they brought in sales, what the calendar would do to the "
                    f"{f.N} plan, and whether the controls over promotions are good enough to run one."),
        "Source": ("CharlesRiver.xlsx (in C:\\CharlesRiver); Tables T7_PromotionProgram, T9_SalesOrder, T16_SalesInvoice, "
                   "T44_Item, T4_Customer, T10_SalesOrderLine, T17_SalesInvoiceLine, T3_GLEntry, T1_Account, "
                   "T77_BudgetLine, T8_PriceOverrideApproval, and T74_Employee, imported with Power Query (Data > Get "
                   "Data > From File > From Excel Workbook, Transform Data)."),
        "Query steps": (
            "Changed Type corrections (Replace current): Discount to Decimal Number and PromotionID to Whole Number in "
            "OrderLines and BilledLines (the first 200 rows carry no promotion, so Power Query detects Discount as a "
            "whole number, which would round every rate to 0, and PromotionID as Any); FreightAmount to Decimal Number "
            "in Invoices; the date columns to Date. Promotions renames ItemGroup, CollectionName, and CustomerSegment "
            "to PromoItemGroup, PromoCollection, and PromoSegment, so they can be merged beside the item's and the "
            "customer's own columns. Orders, Invoices, Items, Customers, Accounts, and Employees keep the columns the "
            "analysis uses. OrderLines (T10_SalesOrderLine) merges Orders (OrderDate, CustomerID), Items (ItemCode, "
            "ItemName, ItemGroup, CollectionName, StandardCost), Customers (CustomerSegment), and Promotions "
            "(ScopeType, the three scope columns, DiscountPct, and the effective dates), all expanded without the "
            "prefix, and adds OrderYear = Date.Year([OrderDate]), OrderMonth = Date.Month([OrderDate]), ListAmount = "
            "[Quantity] * [BaseListPrice], GrossAmount = [Quantity] * [UnitPrice], and DiscountAmount = [GrossAmount] "
            "* [Discount], unrounded. BilledLines (T17_SalesInvoiceLine) merges Invoices (InvoiceNumber, InvoiceDate) "
            "and Items (ItemGroup, StandardCost) and adds InvoiceYear = Date.Year([InvoiceDate]), InvoiceQuarter = "
            "Date.QuarterOfYear([InvoiceDate]), and the same three amounts. RevenuePostings: T3_GLEntry with Transform "
            f"Data, filtered to SourceDocumentType SalesInvoice and PostingDate in {y} before anything is loaded, "
            "merged with Accounts, and grouped by AccountNumber (Advanced: sum of Credit, sum of Debit). "
            f"LedgerActivity: T3_GLEntry filtered to fiscal {F} to {y}, with a JournalEntry column (the VoucherNumber "
            "of journal-entry postings), grouped by AccountID, FiscalYear, SourceDocumentType, and JournalEntry "
            "(count of rows, sums of Debit and Credit), merged with Accounts, and kept for the Revenue and Expense "
            "accounts. BudgetPrices: T77_BudgetLine filtered to BudgetCategory Revenue, merged with Items (ItemCode, "
            "ItemGroup, CollectionName, ListPrice), with ListAmount = [Quantity] * [ListPrice]. Overrides: "
            "T8_PriceOverrideApproval merged twice with Employees, for the requester's and the approver's name and "
            "job title. SourceCounts reads the row count of each source Table for the completeness checks. Invoices "
            "is connection-only (Enable Load cleared), because it only feeds BilledLines."),
        "Parameters": ("HarborRate, FurnitureRate, and DesignTradeRate (inputs, Parameters!B3:B5); CommissionRate "
                       "(Parameters!B6, Tutorial 7.3's formula, rows 18 to 20); ReportYear (input, B7), FirstYear and "
                       "PlanYear (B8:B9); HarborPromotion, FurniturePromotion, and DesignTradePromotion (B12:B14, the "
                       "report year's promotions the proposal repeats); LargestLift (R3 Volume); DocChecksAgree "
                       "(the completeness checks below)."),
        "Calculated columns": ("Orders: LinesTotal, SUMIFS of its OrderLines; LinesAgree, ABS([@OrderTotal]-"
                               "[@LinesTotal])<0.005."),
        "Conventions": ("Blue font marks input cells; black font marks formulas. Power Query amounts are unrounded; "
                        "the yearly promotion costs are rounded to the cent. A promotion applies to a line by its order "
                        "date, so timing and volume use OrderLines; revenue and the ledger follow the invoice date, in "
                        "BilledLines. The worksheets R2 to R5 answer their Requirements, and Memo holds Requirement 6."),
        "Prepared by": "Accounting Analytics instructor solution (model answer)",
        "Reviewed by": "",
        "Open questions": (f"The recorded end dates of promotions {bad} fall on or before their start dates "
                           "(Requirement 5). CustomerSince cannot date a customer's first purchase: for most customers "
                           f"with a CustomerSince in {F} or later, the first order came before it (Requirement 3). "
                           "Quantities are fractional even for items sold by the unit (Chapter 5).")},
        extra=[], sheets={
            "Documentation": "what the workbook is, how it was built, and the completeness checks of Requirement 1",
            "Parameters": "the proposal's rates, the commission rate, the years, and the promotions the proposal repeats",
            "Promotions": "the promotions (query Promotions)", "Orders": "the sales orders (query Orders)",
            "Items": "the item master (query Items)", "Customers": "the customers (query Customers)",
            "OrderLines": "what customers ordered, with order dates, items, segments, and promotions (query OrderLines)",
            "BilledLines": "what was billed, with invoice dates and items (query BilledLines)",
            "Accounts": "the chart of accounts (query Accounts)",
            "RevenuePostings": f"the {y} sales-invoice postings by account (query RevenuePostings)",
            "LedgerActivity": f"income-statement postings by account, year, and source, {F} to {y} (query LedgerActivity)",
            "BudgetPrices": "the revenue budget lines with list prices (query BudgetPrices)",
            "Overrides": "the price override requests with requester and approver (query Overrides)",
            "Employees": "the employees (query Employees)",
            "SourceCounts": "the row counts of the source Tables (query SourceCounts)"})
    write_doc(b)
    settle(b)

    n1 = f.n1
    t = R1
    expected = {"Promotions": n1["promotions"], "Orders": n1["orders"], "Items": n1["items"],
                "Customers": n1["customers"], "OrderLines": n1["order_lines"], "BilledLines": n1["billed"],
                "Accounts": f.accounts, "BudgetPrices": n1["budget_rows"], "Overrides": n1["overrides"],
                "Employees": n1["employees"]}
    for q in SOURCES:
        b.check(t, f"{q} rows", expected[q], f"=ROWS({q}[{KEYS[q]}])", 0, COUNT)
    b.check(t, "every completeness check on the Documentation worksheet agrees", True, "=DocChecksAgree", 0, "General")
    b.check(t, "OrderLines total LineTotal", round(n1["order_total"], 2), "=SUM(OrderLines[LineTotal])")
    b.check(t, "Orders total OrderTotal (equal)", round(f.orders_total, 2), "=SUM(Orders[OrderTotal])")
    b.check(t, "orders whose OrderTotal differs from their own lines", f.order_mismatch,
            "=COUNTIF(Orders[LinesAgree],FALSE)", 0, COUNT)
    b.check(t, "order lines that carry a PromotionID", n1["promo_lines"], '=COUNTIF(OrderLines[PromotionID],"<>")', 0,
            COUNT)
    b.check(t, "their DiscountAmount", round(n1["promo_disc"], 2),
            '=SUMIFS(OrderLines[DiscountAmount],OrderLines[PromotionID],"<>")')
    b.check(t, "order lines without a PromotionID that carry a discount", f.discounted_without[0],
            '=COUNTIFS(OrderLines[PromotionID],"",OrderLines[Discount],"<>0")', 0, COUNT)
    b.check(t, "billed lines without a PromotionID that carry a discount", f.discounted_without[1],
            '=COUNTIFS(BilledLines[PromotionID],"",BilledLines[Discount],"<>0")', 0, COUNT)
    b.check(t, "discount rates in OrderLines (Decimal Number in Changed Type)", f.rates_text,
            '=TEXTJOIN(", ",TRUE,SORT(UNIQUE(OrderLines[Discount])))', 0, "General")
    b.check(t, "BilledLines total LineTotal", round(n1["billed_total"], 2), "=SUM(BilledLines[LineTotal])")
    b.check(t, "RevenuePostings accounts", f.revenue_postings_accounts, "=ROWS(RevenuePostings[AccountNumber])", 0,
            COUNT)
    b.check(t, "RevenuePostings total debits", round(f.ledger_debits, 2), "=SUM(RevenuePostings[Debit])")
    b.check(t, "RevenuePostings total credits", round(f.ledger_credits, 2), "=SUM(RevenuePostings[Credit])")
    b.check(t, f"commission expense {y}, 6290 without the close (Parameters!B18)", round(n1["comm"], 2),
            "=Parameters!B18")
    b.check(t, f"invoice-line revenue {y} (Parameters!B19)", round(n1["rev"], 2), "=Parameters!B19")
    b.check(t, "the journal entry left out of 6290 is the year-end close (Parameters!B20)", n1["close"],
            "=Parameters!B20", 0, "General")
    b.check(t, "CommissionRate (Parameters!B6)", n1["rate"], "=CommissionRate", 1e-9, "0.0000%")
    for scope, name in (("Collection", "HarborPromotion"), ("ItemGroup", "FurniturePromotion"),
                        ("Segment", "DesignTradePromotion")):
        b.check(t, f"{name}, the {y} {scope} promotion", f.promo(scope)["id"], f"={name}", 0, COUNT)


# --- Requirement 2 ------------------------------------------------------------------------------------------------------

def r2(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    y, F, P = b.year, f.F, f.P
    n2 = f.n2
    reg = f.reg

    # --- R2 Cost: the PivotTable, the yearly cost, and its chart ---------------------------------------------------
    ws = new_sheet(b, "R2 Cost")
    title(ws, "Requirement 2: what the promotions cost (BilledLines)")
    heading(ws, 3, "(1) Promotional discount and lines by promotion and invoice year (PivotTable of BilledLines; "
                   "DiscountAmount is unrounded)")
    cache = wb.PivotCaches().Create(SourceType=xl.XL_DATABASE, SourceData="BilledLines")
    pt = cache.CreatePivotTable(TableDestination=ws.Range("A5"), TableName="PromotionCost")
    pt.PivotFields("PromotionID").Orientation = xl.XL_ROW
    pt.PivotFields("InvoiceYear").Orientation = xl.XL_COLUMN
    pt.AddDataField(pt.PivotFields("DiscountAmount"), "Sum of DiscountAmount", xl.XL_SUM).NumberFormat = MONEY
    pt.AddDataField(pt.PivotFields("SalesInvoiceLineID"), "Count of lines", xl.XL_COUNT).NumberFormat = COUNT
    pt.PivotFields("PromotionID").PivotItems("(blank)").Visible = False
    xl.wait_ready(wb.Application)
    end = pt.TableRange2.Row + pt.TableRange2.Rows.Count - 1
    h = end + 2
    heading(ws, h, "(2) The cost by fiscal year, against billed revenue")
    header(ws, h + 1, 1, ["Invoice year", "Promotional discount", "Promotion lines", "Billed revenue (LineTotal)",
                          "Discount as % of billed revenue", "Discount rounded line by line (Exercise 4.2)"])
    s0 = h + 2
    for i in range(3):
        r = s0 + i
        put(ws, {f"A{r}": "=FirstYear" if i == 0 else f"=A{r - 1}+1",
                 f"B{r}": f"=ROUND(SUMIFS(BilledLines[DiscountAmount],BilledLines[InvoiceYear],A{r}),2)",
                 f"C{r}": f'=COUNTIFS(BilledLines[InvoiceYear],A{r},BilledLines[PromotionID],"<>")',
                 f"D{r}": f"=SUMIFS(BilledLines[LineTotal],BilledLines[InvoiceYear],A{r})",
                 f"E{r}": f"=B{r}/D{r}",
                 f"F{r}": f"=SUMPRODUCT((BilledLines[InvoiceYear]=A{r})*ROUND(BilledLines[DiscountAmount],2))"})
    tr = s0 + 3
    put(ws, {f"A{tr}": "Total", f"B{tr}": f"=SUM(B{s0}:B{tr - 1})", f"C{tr}": f"=SUM(C{s0}:C{tr - 1})",
             f"D{tr}": f"=SUM(D{s0}:D{tr - 1})", f"E{tr}": f"=B{tr}/D{tr}", f"F{tr}": f"=SUM(F{s0}:F{tr - 1})",
             f"A{tr + 1}": "Last year's cost over the first year's", f"B{tr + 1}": f"=B{tr - 1}/B{s0}",
             f"A{tr + 2}": "PivotTable grand total (unrounded)",
             f"B{tr + 2}": "=" + gpd("Sum of DiscountAmount", "R2 Cost", "$A$5"),
             f"A{tr + 3}": "PivotTable lines", f"B{tr + 3}": "=" + gpd("Count of lines", "R2 Cost", "$A$5")})
    fmt(ws, f"A{s0}:A{tr - 1}", "0")
    fmt(ws, f"B{s0}:B{tr}", MONEY)
    fmt(ws, f"C{s0}:C{tr}", COUNT)
    fmt(ws, f"D{s0}:D{tr}", MONEY)
    fmt(ws, f"E{s0}:E{tr}", PCT)
    fmt(ws, f"F{s0}:F{tr}", MONEY)
    fmt(ws, f"B{tr + 1}", "0.00")
    fmt(ws, f"B{tr + 2}", MONEY)
    fmt(ws, f"B{tr + 3}", COUNT)
    bold(ws, f"A{tr}:F{tr}")
    widths(ws, {"A": 16, "B": 18, "C": 14, "D": 18, "E": 16, "F": 18, "G": 14, "H": 16, "I": 14})
    shape = ws.Shapes.AddChart2(-1, xl.XL_COLUMN_CLUSTERED, ws.Range("L3").Left, ws.Range("L3").Top, 420, 260)
    chart = shape.Chart
    chart.SetSourceData(ws.Range(f"B{s0}:B{tr - 1}"))
    chart.SeriesCollection(1).XValues = ws.Range(f"A{s0}:A{tr - 1}")
    chart.SeriesCollection(1).Name = "Promotional discount"
    chart.HasTitle = True
    chart.ChartTitle.Text = "Promotional discount billed, by fiscal year"
    chart.HasLegend = False

    # --- R2 Gross to Net: the schedule, the ledger, the discount account, the quarters --------------------------------
    g = new_sheet(b, "R2 Gross to Net")
    title(g, "Requirement 2: gross to net, the ledger, and where the cost appears (report year: Parameters!ReportYear)")
    heading(g, 3, "(1) Gross to net by item group, report year (BilledLines)")
    header(g, 4, 1, ["Item group", "List amount", "Price-list and override reductions", "Promotional discounts",
                     "Net billed (LineTotal)", "Line rounding", "Discounts as % of list"])
    crit = "BilledLines[ItemGroup],$A{r},BilledLines[InvoiceYear],ReportYear"
    for i, grp in enumerate(GROUPS):
        r = 5 + i
        c = crit.format(r=r)
        put(g, {f"A{r}": grp, f"B{r}": f"=SUMIFS(BilledLines[ListAmount],{c})",
                f"C{r}": f"=B{r}-SUMIFS(BilledLines[GrossAmount],{c})",
                f"D{r}": f"=SUMIFS(BilledLines[DiscountAmount],{c})", f"E{r}": f"=SUMIFS(BilledLines[LineTotal],{c})",
                f"F{r}": f"=E{r}-(B{r}-C{r}-D{r})", f"G{r}": f"=IF(B{r}=0,0,D{r}/B{r})"})
    put(g, {"A10": "Total", "B10": "=SUM(B5:B9)", "C10": "=SUM(C5:C9)", "D10": "=SUM(D5:D9)", "E10": "=SUM(E5:E9)",
            "F10": "=SUM(F5:F9)", "G10": "=D10/B10",
            "A11": "Gross less promotional discounts (B - C - D)", "E11": "=B10-C10-D10",
            "A12": "Net billed, every line of the year (no item group left out)",
            "E12": "=SUMIFS(BilledLines[LineTotal],BilledLines[InvoiceYear],ReportYear)"})
    fmt(g, "B5:F12", MONEY)
    fmt(g, "G5:G10", PCT)
    bold(g, "A10:G10")
    widths(g, {"A": 40, "B": 18, "C": 18, "D": 18, "E": 18, "F": 18, "G": 30, "H": 14, "I": 16})
    put(g, {"I4": "Waterfall", "J4": "Amount", "I5": "List amount", "J5": "=B10", "I6": "Price lists and overrides",
            "J6": "=-C10", "I7": "Promotional discounts", "J7": "=-D10", "I8": "Line rounding", "J8": "=F10",
            "I9": "Net billed", "J9": "=E10"})
    fmt(g, "J5:J9", MONEY)
    bold(g, "I4:J4")
    shape = g.Shapes.AddChart2(-1, xl.XL_WATERFALL, g.Range("L3").Left, g.Range("L3").Top, 420, 260)
    chart = shape.Chart
    chart.SetSourceData(g.Range("I5:J9"))
    pts = chart.FullSeriesCollection(1)
    pts.Points(1).IsTotal = True
    pts.Points(5).IsTotal = True
    chart.HasTitle = True
    chart.ChartTitle.Text = "From list to net billed, report year"

    heading(g, 15, "(2) Net billed against the revenue the ledger records from sales invoices (RevenuePostings)")
    header(g, 16, 1, ["Account", "Account name", "Item group (Items[RevenueAccountID])", "Ledger credits",
                      "Net billed (BilledLines)", "Difference",
                      "Lines of invoices dated the year before but numbered in the report year"])
    accounts = sorted((n, grp) for grp, n in f.group_account.items() if grp in GROUPS)
    a0 = 17
    for i, (number, grp) in enumerate(accounts):
        r = a0 + i
        put(g, {f"A{r}": number, f"B{r}": f"=XLOOKUP(A{r},Accounts[AccountNumber],Accounts[AccountName])",
                f"C{r}": f"=XLOOKUP(XLOOKUP(A{r},Accounts[AccountNumber],Accounts[AccountID]),Items[RevenueAccountID],"
                         "Items[ItemGroup])",
                f"D{r}": f"=SUMIFS(RevenuePostings[Credit],RevenuePostings[AccountNumber],A{r})",
                f"E{r}": f"=SUMIFS(BilledLines[LineTotal],BilledLines[ItemGroup],C{r},BilledLines[InvoiceYear],ReportYear)",
                f"F{r}": f"=D{r}-E{r}",
                f"G{r}": (f"=SUMIFS(BilledLines[LineTotal],BilledLines[ItemGroup],C{r},BilledLines[InvoiceYear],"
                          f'ReportYear-1,BilledLines[InvoiceNumber],"SI-"&ReportYear&"-*")')})
    at = a0 + len(accounts)
    put(g, {f"A{at}": "Total", f"D{at}": f"=SUM(D{a0}:D{at - 1})", f"E{at}": f"=SUM(E{a0}:E{at - 1})",
            f"F{at}": f"=SUM(F{a0}:F{at - 1})", f"G{at}": f"=SUM(G{a0}:G{at - 1})",
            f"A{at + 1}": "Difference less the lines of those invoices", f"F{at + 1}": f"=F{at}-G{at}"})
    fmt(g, f"D{a0}:G{at + 1}", MONEY)
    bold(g, f"A{at}:G{at}")
    v0 = at + 3
    heading(g, v0, "(3) The invoices that make the difference: dated in the year before, numbered (and posted) in the "
                   "report year")
    header(g, v0 + 1, 1, ["InvoiceNumber", "InvoiceDate", "Lines", "LineTotal"])
    va = f"A{v0 + 2}"
    put(g, {va: ('=LET(k,(BilledLines[InvoiceYear]=ReportYear-1)*(LEFT(BilledLines[InvoiceNumber],7)="SI-"&ReportYear),'
                 "n,SORT(UNIQUE(FILTER(BilledLines[InvoiceNumber],k))),HSTACK(n,XLOOKUP(n,BilledLines[InvoiceNumber],"
                 "BilledLines[InvoiceDate]),COUNTIFS(BilledLines[InvoiceNumber],n),SUMIFS(BilledLines[LineTotal],"
                 "BilledLines[InvoiceNumber],n)))")})
    nv = len(f.cutoff)
    fmt(g, f"B{v0 + 2}:B{v0 + 1 + nv}", DATE)
    fmt(g, f"D{v0 + 2}:D{v0 + 1 + nv}", MONEY)
    o0 = v0 + 3 + nv
    heading(g, o0, "(4) The other accounts the report year's sales invoices post to (RevenuePostings)")
    header(g, o0 + 1, 1, ["Account", "Account name", "", "Debit", "Credit"])
    oa = f"A{o0 + 2}"
    put(g, {oa: (f"=LET(a,RevenuePostings[AccountNumber],n,FILTER(a,ISNA(XMATCH(a,$A${a0}:$A${at - 1}))),"
                 "HSTACK(n,XLOOKUP(n,Accounts[AccountNumber],Accounts[AccountName]),IF(n,\"\"),"
                 "XLOOKUP(n,a,RevenuePostings[Debit]),XLOOKUP(n,a,RevenuePostings[Credit])))")})
    others = sorted(n for n in f.posted if n not in {a for a, _ in accounts})
    no = len(others)
    fmt(g, f"D{o0 + 2}:E{o0 + 1 + no}", MONEY)
    d0 = o0 + 3 + no
    heading(g, d0, "(5) Where a discount could be recorded: accounts named for discounts (Accounts), and their "
                   "postings by fiscal year (LedgerActivity)")
    header(g, d0 + 1, 1, ["Account", "Account name", "AccountType", "AccountSubType", "Postings, first year",
                          "Postings, second year", "Postings, report year"])
    da = f"A{d0 + 2}"
    put(g, {da: ('=LET(k,ISNUMBER(SEARCH("discount",Accounts[AccountName])),n,FILTER(Accounts[AccountNumber],k),'
                 "p,LAMBDA(yr,SUMIFS(LedgerActivity[Postings],LedgerActivity[AccountNumber],n,LedgerActivity[FiscalYear],"
                 "yr)),HSTACK(n,FILTER(Accounts[AccountName],k),FILTER(Accounts[AccountType],k),"
                 "FILTER(Accounts[AccountSubType],k),p(FirstYear),p(FirstYear+1),p(ReportYear)))")})
    nd = len(f.discount_accounts)
    r0 = d0 + 3 + nd
    heading(g, r0, "(6) The revenue accounts: net credits by fiscal year, without the year-end closes (LedgerActivity)")
    header(g, r0 + 1, 1, ["Account", "Account name", "AccountSubType", "First year", "Second year", "Report year",
                          "Postings, three years"])
    ra = f"A{r0 + 2}"
    put(g, {ra: ('=LET(k,(Accounts[AccountType]="Revenue")*(Accounts[AccountSubType]<>"Header"),'
                 "n,SORT(FILTER(Accounts[AccountNumber],k)),"
                 "net,LAMBDA(yr,SUMIFS(LedgerActivity[Credit],LedgerActivity[AccountNumber],n,LedgerActivity[FiscalYear],"
                 'yr,LedgerActivity[SourceDocumentType],"<>JournalEntry")-SUMIFS(LedgerActivity[Debit],'
                 "LedgerActivity[AccountNumber],n,LedgerActivity[FiscalYear],yr,LedgerActivity[SourceDocumentType],"
                 '"<>JournalEntry")),HSTACK(n,XLOOKUP(n,Accounts[AccountNumber],Accounts[AccountName]),'
                 "XLOOKUP(n,Accounts[AccountNumber],Accounts[AccountSubType]),net(FirstYear),net(FirstYear+1),"
                 "net(ReportYear),SUMIFS(LedgerActivity[Postings],LedgerActivity[AccountNumber],n)))")})
    nr = len(f.revenue_accounts)
    fmt(g, f"D{r0 + 2}:F{r0 + 1 + nr}", MONEY)
    fmt(g, f"G{r0 + 2}:G{r0 + 1 + nr}", COUNT)
    q0 = r0 + 3 + nr
    heading(g, q0, "(7) The proposal's promotions: discounts billed in the report year, by invoice quarter (BilledLines)")
    header(g, q0 + 1, 1, ["PromotionID", "Promotion", "Q1", "Q2", "Q3", "Q4", "Year"])
    for i, name in enumerate(("HarborPromotion", "FurniturePromotion", "DesignTradePromotion")):
        r = q0 + 2 + i
        put(g, {f"A{r}": f"={name}", f"B{r}": f"=XLOOKUP(A{r},Promotions[PromotionID],Promotions[PromotionName])",
                f"G{r}": f"=SUM(C{r}:F{r})"})
        for k in range(4):
            put(g, {f"{col(3 + k)}{r}": (f"=SUMIFS(BilledLines[DiscountAmount],BilledLines[PromotionID],$A{r},"
                                         f"BilledLines[InvoiceYear],ReportYear,BilledLines[InvoiceQuarter],{k + 1})")})
    qt = q0 + 5
    put(g, {f"A{qt}": "Total"})
    for k in range(5):
        c = col(3 + k)
        put(g, {f"{c}{qt}": f"=SUM({c}{q0 + 2}:{c}{qt - 1})", f"{c}{qt + 1}": f"={c}{qt}/$G${qt}"})
    put(g, {f"A{qt + 1}": "Share of the year"})
    fmt(g, f"C{q0 + 2}:G{qt}", MONEY)
    fmt(g, f"C{qt + 1}:G{qt + 1}", PCT)
    bold(g, f"A{qt}:G{qt}")
    b.found["r2"] = dict(s0=s0, tr=tr, a0=a0, at=at, v0=v0, d0=d0, r0=r0, q0=q0, qt=qt)

    years = n2["years"]
    groups = {x["group"]: x for x in n2["groups"]}
    ledger = {x["number"]: x["credit"] for x in n2["ledger"]}
    cut = {x["number"]: x["credit"] for x in n2["cutoff_accounts"]}
    pq_ = f.prop_quarters_exact
    q4 = pq_.get(4, 0.0)
    fur = groups["Furniture"]
    disc_name = f.discount_accounts[0]
    text_block(g, qt + 4, f"{MA}, Requirement 2", [
        f"Cost. Over fiscal {F} to {y}, the nine promotions gave customers {money(n2['total'])} of discounts on "
        f"{n2['lines']:,} billed lines, and the cost {n2['grew']} in {n2['span']} years: {money(years[0]['disc'])} in "
        f"{F} ({pct(years[0]['share'], 2)} of billed revenue), {money(years[1]['disc'])} in {F + 1} "
        f"({pct(years[1]['share'], 2)}), and {money(years[2]['disc'])} in {y} ({pct(years[2]['share'], 2)}). Rounding "
        f"each line's discount to the cent, as Exercise 4.2 did, gives {money(n2['rounded'])}.",
        f"Gross to net. In fiscal {y}, list prices would have billed {money(n2['list'])}. Price lists and approved "
        f"overrides took off {money(n2['red'])} and the promotions {money(n2['disc'])}, leaving {money(n2['net'])} "
        f"billed; gross less discounts is {money(n2['after'])}, and the {money(n2['rounding'])} between them is the "
        f"rounding of LineTotal line by line. Furniture carried {money(fur['disc'])} of the promotional discount.",
        f"Ledger. The sales-invoice credits to the revenue accounts total {money(n2['ledger_total'])}, "
        f"{money(n2['difference'])} more than the lines billed in {y}. The difference is invoices {n2['first']} to "
        f"{n2['last']}, dated in late {P} but posted on {n2['cutoff_posted']} (Exercise 6.1): "
        + ", ".join(f"{money(v)} to {n}" for n, v in sorted(cut.items()))
        + f". Account 4050 {n2['freight_name']} ({money(n2['freight'])}) comes from the invoice header, not from the "
        "lines, and account 2050 holds the sales tax.",
        f"Where the cost appears. The chart of accounts has {disc_name[0]} {disc_name[1]}, a "
        f"{disc_name[3].lower()} account, but it has no postings in any year. Each invoice line is recorded at its net "
        "price, so the revenue accounts already exclude every price reduction. The income statement therefore shows "
        "net revenue and nothing about the promotions: their cost is visible only in a gross-to-net schedule like (1), "
        f"or if revenue were recorded at the price before the promotion and the promotional discount in "
        f"{disc_name[0]}.",
        f"Timing. The proposal's three promotions were billed {money(pq_.get(1, 0))} in the first quarter of {y}, "
        f"{money(pq_.get(2, 0))} in the second, {money(pq_.get(3, 0))} in the third, and {money(q4)} in the fourth: "
        f"{pct(n2['q4_share'], 0)} of their {money(n2['prop_total'])} landed in the fourth quarter, because the fall "
        "promotion's orders are invoiced after it ends, and the segment promotion runs in November."], span=7)

    t = R2
    for i, yr in enumerate(years):
        r = s0 + i
        b.check(t, f"promotional discount {yr['year']} (R2 Cost!B{r})", reg.xround(yr["disc"]), f"='R2 Cost'!B{r}")
        b.check(t, f"promotion lines billed {yr['year']}", f.year_lines[yr["year"]], f"='R2 Cost'!C{r}", 0, COUNT)
        b.check(t, f"billed revenue {yr['year']}", round(yr["rev"], 2), f"='R2 Cost'!D{r}")
        b.check(t, f"discount as % of billed revenue {yr['year']}", reg.xround(yr["disc"]) / yr["rev"],
                f"='R2 Cost'!E{r}", 1e-9, "0.0000%")
    b.check(t, "total of the yearly discounts (R2 Cost)", n2["total"], f"='R2 Cost'!B{tr}")
    b.check(t, "promotion lines billed, all years", n2["lines"], f"='R2 Cost'!C{tr}", 0, COUNT)
    b.check(t, "discount rounded line by line (Exercise 4.2)", n2["rounded"], f"='R2 Cost'!F{tr}")
    b.check(t, "PivotTable grand total, unrounded (one cent below the total of the rounded years)",
            sum(x["disc"] for x in n2["by_promo"]), f"='R2 Cost'!B{tr + 2}")
    b.check(t, "PivotTable lines", n2["lines"], f"='R2 Cost'!B{tr + 3}", 0, COUNT)
    b.check(t, "last year's cost over the first year's", reg.xround(years[-1]["disc"]) / reg.xround(years[0]["disc"]),
            f"='R2 Cost'!B{tr + 1}", 1e-9, "0.0000")
    for x in n2["by_promo"]:
        b.check(t, f"promotion {x['id']}: discount, all years (PivotTable)", round(x["disc"], 2),
                "=" + gpd("Sum of DiscountAmount", "R2 Cost", "$A$5", "PromotionID", x["id"]))
        b.check(t, f"promotion {x['id']}: billed lines (PivotTable)", f.promo_lines_billed[x["id"]],
                "=" + gpd("Count of lines", "R2 Cost", "$A$5", "PromotionID", x["id"]), 0, COUNT)
    for i, grp in enumerate(GROUPS):
        r, x = 5 + i, groups[grp]
        b.check(t, f"{grp}: list amount (R2 Gross to Net!B{r})", x["list"], f"='R2 Gross to Net'!B{r}")
        b.check(t, f"{grp}: price-list and override reductions", x["red"], f"='R2 Gross to Net'!C{r}")
        b.check(t, f"{grp}: promotional discounts", x["disc"], f"='R2 Gross to Net'!D{r}")
        b.check(t, f"{grp}: net billed", round(x["net"], 2), f"='R2 Gross to Net'!E{r}")
    b.check(t, "total list amount", round(n2["list"], 2), "='R2 Gross to Net'!B10")
    b.check(t, "total reductions", round(n2["red"], 2), "='R2 Gross to Net'!C10")
    b.check(t, "total promotional discounts", round(n2["disc"], 2), "='R2 Gross to Net'!D10")
    b.check(t, "total net billed", round(n2["net"], 2), "='R2 Gross to Net'!E10")
    b.check(t, "gross less discounts", n2["after"], "='R2 Gross to Net'!E11")
    b.check(t, "line rounding", round(n2["rounding"], 2), "='R2 Gross to Net'!F10")
    b.check(t, "net billed, every line of the year", round(n2["net"], 2), "='R2 Gross to Net'!E12")
    for i, (number, grp) in enumerate(accounts):
        r = a0 + i
        b.check(t, f"{number}: item group of its items", grp, f"='R2 Gross to Net'!C{r}", 0, "General")
        b.check(t, f"{number}: ledger credits", round(ledger[number], 2), f"='R2 Gross to Net'!D{r}")
        b.check(t, f"{number}: difference from net billed", round(cut.get(number, 0.0), 2), f"='R2 Gross to Net'!F{r}")
    b.check(t, "ledger credits to the revenue accounts", round(n2["ledger_total"], 2), f"='R2 Gross to Net'!D{at}")
    b.check(t, "difference from net billed", round(n2["difference"], 2), f"='R2 Gross to Net'!F{at}")
    b.check(t, "difference less the cutoff invoices' lines", 0, f"='R2 Gross to Net'!F{at + 1}")
    b.check(t, "invoices dated the year before and numbered in the report year", nv,
            f"=ROWS('R2 Gross to Net'!{va}#)", 0, COUNT)
    b.check(t, "the first of them", n2["first"], f"=INDEX('R2 Gross to Net'!{va}#,1,1)", 0, "General")
    b.check(t, "the last of them", f.cutoff[-1][0], f"=INDEX('R2 Gross to Net'!{va}#,{nv},1)", 0, "General")
    b.check(t, "their lines' total", round(sum(r[3] for r in f.cutoff), 2), f"=SUM(INDEX('R2 Gross to Net'!{va}#,0,4))")
    b.check(t, f"4050 {n2['freight_name']}: credits from the invoice header", round(n2["freight"], 2),
            f"=XLOOKUP(4050,INDEX('R2 Gross to Net'!{oa}#,0,1),INDEX('R2 Gross to Net'!{oa}#,0,5))")
    b.check(t, "2050: the invoices' sales tax", round(f.posted[2050][1], 2),
            f"=XLOOKUP(2050,INDEX('R2 Gross to Net'!{oa}#,0,1),INDEX('R2 Gross to Net'!{oa}#,0,5))")
    b.check(t, "accounts named for discounts", nd, f"=ROWS('R2 Gross to Net'!{da}#)", 0, COUNT)
    b.check(t, "the account for discounts", f"{disc_name[0]} {disc_name[1]}",
            f"=INDEX('R2 Gross to Net'!{da}#,1,1)&\" \"&INDEX('R2 Gross to Net'!{da}#,1,2)", 0, "General")
    b.check(t, f"{disc_name[0]}: postings in the three years", f.account_postings.get(disc_name[0], 0),
            f"=SUM(INDEX('R2 Gross to Net'!{da}#,1,5),INDEX('R2 Gross to Net'!{da}#,1,6),INDEX('R2 Gross to Net'!{da}#,1,7))",
            0, COUNT)
    for k, (number, name, _) in enumerate(f.revenue_accounts):
        if number in (4060, 4070):
            for j, yr in enumerate((F, F + 1, y)):
                b.check(t, f"{number} {name}: net credits {yr}", round(f.revenue_net.get((number, yr), 0.0), 2),
                        f"=INDEX('R2 Gross to Net'!{ra}#,{k + 1},{4 + j})")
    for i, scope in enumerate(("Collection", "ItemGroup", "Segment")):
        p = f.promo(scope)
        qs = dict(next(x for x in n2["prop"] if x["id"] == p["id"])["quarters"])
        r = q0 + 2 + i
        for k in range(4):
            b.check(t, f"promotion {p['id']}: discount billed in Q{k + 1}", round(qs.get(k + 1, 0.0), 2),
                    f"='R2 Gross to Net'!{col(3 + k)}{r}")
    b.check(t, "the proposal's discounts billed in Q4", round(q4, 2), f"='R2 Gross to Net'!F{qt}")
    b.check(t, "the proposal's discounts in the report year", round(n2["prop_total"], 2), f"='R2 Gross to Net'!G{qt}")
    b.check(t, "share billed in Q4", n2["q4_share"], f"='R2 Gross to Net'!F{qt + 1}", 1e-9, PCT)

    st = b.found["doc"]
    st["sheets"]["R2 Cost"] = "Requirement 2: the promotional discount by promotion and year (PivotTable), and by year"
    st["sheets"]["R2 Gross to Net"] = ("Requirement 2: the gross-to-net schedule, the tie to the ledger, the discount "
                                       "account, and the proposal's discounts by quarter")
    write_doc(b)
    settle(b)


# --- Requirement 3 ------------------------------------------------------------------------------------------------------

CAL = 5                                                      # first row of the calendar on R3 Volume


def r3_rows(n: int) -> dict:
    """Row positions on R3 Volume for n promotions: the calendar, the two monthly grids, and the comparison."""
    g0 = CAL + n + 1                                         # heading of the grid of the promotion's year
    p0 = g0 + n + 3                                          # heading of the grid of the year before
    k0 = p0 + n + 3                                          # heading of the comparison
    return dict(c=CAL, g0=g0, gh=g0 + 1, g=g0 + 2, p0=p0, ph=p0 + 1, p=p0 + 2, k0=k0, kh=k0 + 1, k=k0 + 2,
                s=k0 + 2 + n + 1)


def r3(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    F = f.F
    n3 = f.n3
    n = len(f.ids)
    R = r3_rows(n)
    ws = new_sheet(b, "R3 Volume")
    title(ws, "Requirement 3: did the promotions bring in sales? (OrderLines, by order date)")
    heading(ws, 3, "(1) When each promotion ran: the order dates of its lines against its recorded dates")
    header(ws, 4, 1, ["PromotionID", "PromotionName", "ScopeType", "Scope", "DiscountPct", "Recorded start",
                      "Recorded end", "Lines", "First order", "Last order", "Year", "First month", "Last month", "Months",
                      "Lines within the recorded dates", "First and last order in one year"])
    c = f"A{CAL}"
    lk = lambda column: f"XLOOKUP({c}#,Promotions[PromotionID],Promotions[{column}])"
    put(ws, {c: "=SORT(Promotions[PromotionID])", f"B{CAL}": "=" + lk("PromotionName"), f"C{CAL}": "=" + lk("ScopeType"),
             f"D{CAL}": (f"=XLOOKUP({c}#,Promotions[PromotionID],Promotions[PromoCollection]&Promotions[PromoItemGroup]&"
                         "Promotions[PromoSegment])"),
             f"E{CAL}": "=" + lk("DiscountPct"), f"F{CAL}": "=" + lk("EffectiveStartDate"),
             f"G{CAL}": "=" + lk("EffectiveEndDate"), f"H{CAL}": f"=COUNTIFS(OrderLines[PromotionID],{c}#)",
             f"I{CAL}": f"=MINIFS(OrderLines[OrderDate],OrderLines[PromotionID],{c}#)",
             f"J{CAL}": f"=MAXIFS(OrderLines[OrderDate],OrderLines[PromotionID],{c}#)",
             f"K{CAL}": f"=YEAR(I{CAL}#)", f"L{CAL}": f"=MONTH(I{CAL}#)", f"M{CAL}": f"=MONTH(J{CAL}#)",
             f"N{CAL}": f"=M{CAL}#-L{CAL}#+1",
             f"O{CAL}": (f'=COUNTIFS(OrderLines[PromotionID],{c}#,OrderLines[OrderDate],">="&F{CAL}#,'
                         f'OrderLines[OrderDate],"<="&G{CAL}#)'),
             f"P{CAL}": f"=YEAR(I{CAL}#)=YEAR(J{CAL}#)"})
    last = CAL + n - 1
    fmt(ws, f"E{CAL}:E{last}", "0%")
    for cc in "FGIJ":
        fmt(ws, f"{cc}{CAL}:{cc}{last}", DATE)
    widths(ws, {"A": 12, "B": 34, "C": 13, "D": 14, "E": 11})
    for k in range(6, 17):
        ws.Columns(k).ColumnWidth = 13
    months = f"$E${R['gh']}:$P${R['gh']}"
    sc = lambda r: f"CHOOSE(MATCH($B{r},{SCOPES},0),{scope_range('OrderLines')})"
    for block, h0, hh, first, prior in (("grid", R["g0"], R["gh"], R["g"], False), ("prior", R["p0"], R["ph"], R["p"], True)):
        heading(ws, h0, "(2) List-price volume ordered in each promotion's scope, by month of its year (OrderLines"
                        "[ListAmount])" if not prior else
                        "(3) The same scope, the year before (blank where the data has no earlier year)")
        header(ws, hh, 1, ["PromotionID", "ScopeType", "Scope", "Year"] + list(range(1, 13)))
        for i in range(n):
            r, cr = first + i, CAL + i
            put(ws, {f"A{r}": f"=$A{cr}", f"B{r}": f"=$C{cr}", f"C{r}": f"=$D{cr}",
                     f"D{r}": f"=$K{cr}-1" if prior else f"=$K{cr}"})
            for m in range(12):
                cm = col(5 + m)
                total = (f"SUMIFS(OrderLines[ListAmount],{sc(r)},$C{r},OrderLines[OrderYear],$D{r},"
                         f"OrderLines[OrderMonth],{cm}${hh})")
                put(ws, {f"{cm}{r}": f'=IF($D{r}<FirstYear,"",{total})' if prior else f"={total}"})
        fmt(ws, f"E{first}:P{first + n - 1}", "#,##0")
    heading(ws, R["k0"], "(4) Volume in each promotion's months against two expectations, and the scope's normal "
                         "variation")
    header(ws, R["kh"], 1, ["PromotionID", "Scope", "Months", "Volume in the promotion's months",
                            "Expectation: the other months' average x months", "Difference from the expectation",
                            "The same months a year earlier", "Difference from a year earlier",
                            "Standard deviation of the other months (STDEV.S)", "As % of their mean",
                            "Difference in standard deviations of a total of that many months",
                            "Beyond two standard deviations"])
    for i in range(n):
        r, cr, gr, pr = R["k"] + i, CAL + i, R["g"] + i, R["p"] + i
        grow, prow = f"$E{gr}:$P{gr}", f"$E{pr}:$P{pr}"
        inside = f"({months}>=$L{cr})*({months}<=$M{cr})"
        other = f"({months}<$L{cr})+({months}>$M{cr})"
        put(ws, {f"A{r}": f"=$A{cr}", f"B{r}": f"=$D{cr}", f"C{r}": f"=$N{cr}",
                 f"D{r}": f"=SUMPRODUCT({inside}*{grow})",
                 f"E{r}": f"=AVERAGE(FILTER({grow},{other}))*C{r}",
                 f"F{r}": f"=D{r}/E{r}-1",
                 f"G{r}": f'=IF($D{pr}<FirstYear,"",SUMPRODUCT({inside}*{prow}))',
                 f"H{r}": f'=IF(G{r}="","n/a",D{r}/G{r}-1)',
                 f"I{r}": f"=STDEV.S(FILTER({grow},{other}))",
                 f"J{r}": f"=I{r}/AVERAGE(FILTER({grow},{other}))",
                 f"K{r}": f"=(D{r}-E{r})/(I{r}*SQRT(C{r}))",
                 f"L{r}": f"=ABS(K{r})>=2"})
    k1, k2, s = R["k"], R["k"] + n - 1, R["s"]
    fmt(ws, f"D{k1}:E{k2}", "#,##0")
    fmt(ws, f"G{k1}:G{k2}", "#,##0")
    fmt(ws, f"I{k1}:I{k2}", "#,##0")
    fmt(ws, f"F{k1}:F{k2}", "+0.0%;-0.0%")
    fmt(ws, f"H{k1}:H{k2}", "+0.0%;-0.0%")
    fmt(ws, f"J{k1}:J{k2}", "0.0%")
    fmt(ws, f"K{k1}:K{k2}", "+0.00;-0.00")
    put(ws, {f"A{s}": "Largest difference from the expectation", f"C{s}": f"=XLOOKUP(F{s},F{k1}:F{k2},A{k1}:A{k2})",
             f"F{s}": f"=MAX(F{k1}:F{k2})", f"K{s}": f"=XLOOKUP(F{s},F{k1}:F{k2},K{k1}:K{k2})",
             f"A{s + 1}": "Smallest difference from the expectation",
             f"C{s + 1}": f"=XLOOKUP(F{s + 1},F{k1}:F{k2},A{k1}:A{k2})", f"F{s + 1}": f"=MIN(F{k1}:F{k2})",
             f"A{s + 2}": "Differences beyond two standard deviations", f"L{s + 2}": f"=COUNTIF(L{k1}:L{k2},TRUE)",
             f"B{s}": "promotion", f"B{s + 1}": "promotion"})
    fmt(ws, f"F{s}:F{s + 1}", "+0.0%;-0.0%")
    fmt(ws, f"K{s}", "+0.00;-0.00")
    xl.name_cell(wb, "LargestLift", f"'R3 Volume'!$F${s}")
    top, low = n3["top"], n3["low"]
    text_block(ws, s + 4, f"{MA}, Requirement 3 (volume)", [
        f"When they ran. Every promotion's lines were ordered within one calendar year: collections in March and "
        "April, item groups in September and October, and segments in November. The recorded dates of promotions "
        f"{n3['bad']} cannot be right, because none of their lines falls inside them (Requirement 5). The scopes are "
        "a collection (spring), an item group (fall), and a customer segment (November).",
        "Why the list amount. ListAmount is Quantity times BaseListPrice, and list prices did not change, so it moves "
        "only with the quantity and the mix ordered: it measures volume at constant prices. The net amount billed "
        "falls by the discount itself, so in a promotion's months it would show a fall in sales even with no change "
        "in volume; it also follows the invoice date, which lags the order that the promotion applied to.",
        f"Against the expectations. The differences from the average of the other months run from "
        f"{spct(low['lift'])} (promotion {low['id']}, {low['label']}) to {spct(top['lift'])} (promotion {top['id']}, "
        f"{top['label']}), and against the same months a year earlier from "
        f"{spct(min(v['py'] for v in f.vol.values() if v['py'] is not None))} to "
        f"{spct(max(v['py'] for v in f.vol.values() if v['py'] is not None))}. None is unusual: the largest, "
        f"{spct(top['lift'])}, is {top['z']:.1f} standard deviations of a {n3['sd_total']}, and promotion "
        f"{low['id']}'s fall is within its segment's normal swings ({pct(low['sd'])} a month). Every difference is far "
        "below the promotion's break-even increase (Requirement 4): no promotion brought in sales that would not "
        "otherwise have been made."], span=10)

    # --- R3 Customers ---------------------------------------------------------------------------------------------
    cu = new_sheet(b, "R3 Customers")
    title(cu, "Requirement 3: did promotions bring in new customers? (first orders in OrderLines)")
    header(cu, 4, 1, ["CustomerID", "First order date", "First order included a promotion line", "CustomerSince",
                      "First order before CustomerSince", "CustomerName"])
    put(cu, {"A5": "=SORT(UNIQUE(OrderLines[CustomerID]))",
             "B5": "=MINIFS(OrderLines[OrderDate],OrderLines[CustomerID],A5#)",
             "C5": '=COUNTIFS(OrderLines[CustomerID],A5#,OrderLines[OrderDate],B5#,OrderLines[PromotionID],"<>")>0',
             "D5": "=XLOOKUP(A5#,Customers[CustomerID],Customers[CustomerSince])", "E5": "=B5#<D5#",
             "F5": "=XLOOKUP(A5#,Customers[CustomerID],Customers[CustomerName])"})
    nc = n3["customers"]
    fmt(cu, f"B5:B{4 + nc}", DATE)
    fmt(cu, f"D5:D{4 + nc}", DATE)
    heading(cu, 3, "First order of each customer")
    heading(cu, 3, "Summary", column=8)
    summary = [("Customers who ordered", "=ROWS(A5#)", COUNT),
               ("First orders that included a promotion line", "=SUM(--C5#)", COUNT),
               ("First orders in January to April of the first year",
                '=COUNTIFS(B5#,">="&DATE(FirstYear,1,1),B5#,"<="&DATE(FirstYear,4,30))', COUNT),
               ("First orders after June of the first year", '=COUNTIF(B5#,">"&DATE(FirstYear,6,30))', COUNT),
               ("Last first order", "=MAX(B5#)", DATE),
               ("Customers with a CustomerSince in the first year or later", '=COUNTIF(D5#,">="&DATE(FirstYear,1,1))',
                COUNT),
               ("...of them, first order before CustomerSince", '=COUNTIFS(D5#,">="&DATE(FirstYear,1,1),E5#,TRUE)',
                COUNT)]
    for i, (label, formula, number_format) in enumerate(summary):
        put(cu, {f"H{5 + i}": label, f"I{5 + i}": formula})
        fmt(cu, f"I{5 + i}", number_format)
    heading(cu, 14, "First orders by month", column=8)
    header(cu, 15, 8, ["Month", "Customers"])
    put(cu, {"H16": "=LET(m,DATE(YEAR(B5#),MONTH(B5#),1),u,SORT(UNIQUE(m)),HSTACK(u,MAP(u,LAMBDA(x,SUM(--(m=x))))))"})
    nm = len(f.first_by_month)
    fmt(cu, f"H16:H{15 + nm}", "mmm yyyy")
    widths(cu, {"A": 12, "B": 14, "C": 16, "D": 14, "E": 16, "F": 30, "G": 3, "H": 52, "I": 14})
    text_block(cu, 17 + nm + 2, f"{MA}, Requirement 3 (new customers)", [
        f"{n3['customers']} customers ordered, and no customer's first order in the data included a promotion line. "
        f"First orders cluster in January to April {F} ({f.first_early} of {n3['customers']}) only because the data "
        f"begins in January {F}: customers who had bought before then appear as new. Just {n3['late']} first orders "
        f"came after June {F}, the last in {n3['last']}, so the data holds almost no new customers to test the claim "
        "on, and none of them came through a promotion. The data cannot show that promotions never attract customers, "
        "but it gives no support to the claim.",
        f"CustomerSince cannot replace the first order: for {n3['since_before']} of the {n3['since']} customers with a "
        f"CustomerSince in {F} or later, the first order came before it."], span=4, column=8)

    t = R3
    vol = f.vol
    for i, pid in enumerate(f.ids):
        p, v, cr, kr = f.promos[pid], vol[pid], CAL + i, R["k"] + i
        b.check(t, f"promotion {pid}: lines ordered", p["lines"], f"='R3 Volume'!H{cr}", 0, COUNT)
        ran = " to ".join(dict.fromkeys(MONTH_NAMES[m - 1] for m in (p["months"][0], p["months"][-1])))
        b.check(t, f"promotion {pid}: months it ran ({ran})", len(p["months"]), f"='R3 Volume'!N{cr}", 0, COUNT)
        b.check(t, f"promotion {pid}: first month", p["months"][0], f"='R3 Volume'!L{cr}", 0, COUNT)
        b.check(t, f"promotion {pid}: lines within its recorded dates", f.within[pid], f"='R3 Volume'!O{cr}", 0, COUNT)
        b.check(t, f"promotion {pid} ({v['label']}): difference from the other months", v["lift"],
                f"='R3 Volume'!F{kr}", 1e-9, "0.0000%")
        b.check(t, f"promotion {pid}: standard deviation as % of the mean", v["sd"], f"='R3 Volume'!J{kr}", 1e-9,
                "0.0000%")
        b.check(t, f"promotion {pid}: difference in standard deviations", v["z"], f"='R3 Volume'!K{kr}", 1e-9, "0.0000")
        if v["py"] is not None:
            b.check(t, f"promotion {pid}: difference from a year earlier", v["py"], f"='R3 Volume'!H{kr}", 1e-9,
                    "0.0000%")
        else:
            b.check(t, f"promotion {pid}: no earlier year in the data", "n/a", f"='R3 Volume'!H{kr}", 0, "General")
    b.check(t, "largest difference (LargestLift)", top["lift"], "=LargestLift", 1e-9, "0.0000%")
    b.check(t, "its promotion", top["id"], f"='R3 Volume'!C{s}", 0, COUNT)
    b.check(t, "smallest difference", low["lift"], f"='R3 Volume'!F{s + 1}", 1e-9, "0.0000%")
    b.check(t, "its promotion", low["id"], f"='R3 Volume'!C{s + 1}", 0, COUNT)
    b.check(t, "differences beyond two standard deviations", sum(1 for v in vol.values() if abs(v["z"]) >= 2),
            f"='R3 Volume'!L{s + 2}", 0, COUNT)
    b.check(t, "customers who ordered", nc, "='R3 Customers'!I5", 0, COUNT)
    b.check(t, "first orders that included a promotion line", n3["promoted"], "='R3 Customers'!I6", 0, COUNT)
    b.check(t, f"first orders in January to April {F}", f.first_early, "='R3 Customers'!I7", 0, COUNT)
    b.check(t, f"first orders after June {F}", f.first_late, "='R3 Customers'!I8", 0, COUNT)
    b.check(t, "last first order", serial(f.first_last), "='R3 Customers'!I9", 0, DATE)
    b.check(t, f"customers with a CustomerSince in {F} or later", n3["since"], "='R3 Customers'!I10", 0, COUNT)
    b.check(t, "...of them, first order before CustomerSince", n3["since_before"], "='R3 Customers'!I11", 0, COUNT)
    b.check(t, "months with first orders", nm, "=ROWS('R3 Customers'!H16#)", 0, COUNT)

    st = b.found["doc"]
    st["sheets"]["R3 Volume"] = ("Requirement 3: when each promotion ran, the list-price volume of its scope by month, "
                                 "and the comparison with two expectations")
    st["sheets"]["R3 Customers"] = "Requirement 3: each customer's first order and whether it included a promotion"
    write_doc(b)
    settle(b)


# --- Requirement 4 ------------------------------------------------------------------------------------------------------

PROPOSAL = [("B", "Collection", "Harbor Collection", "HarborPromotion", "HarborRate"),
            ("C", "ItemGroup", "Furniture Seasonal", "FurniturePromotion", "FurnitureRate"),
            ("D", "Segment", "Design Trade Customer", "DesignTradePromotion", "DesignTradeRate")]
LIFTS = [round(0.05 * i, 2) for i in range(9)]
RATES = [0.05, 0.08, 0.10, 0.12]


def r4(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    y, N = b.year, f.N
    n4 = f.n4
    n = len(f.ids)
    R = r3_rows(n)
    cal = lambda column: f"'R3 Volume'!${column}${CAL}:${column}${CAL + n - 1}"
    k1, k2 = R["k"], R["k"] + n - 1

    # --- R4 Model ----------------------------------------------------------------------------------------------------
    ws = new_sheet(b, "R4 Model")
    title(ws, "Requirement 4: the contribution margin model of the proposed calendar (Tutorial 7.3, one column each)")
    header(ws, 3, 1, ["Input or result", "Harbor Collection", "Furniture Seasonal", "Design Trade Customer", "Total",
                      "Source"])
    labels = {4: "Promotion it repeats (report year)", 5: "Discount rate", 6: "Volume lift",
              7: "Units on the report year's billed lines", 8: "Price before discount per unit",
              9: "Standard cost per unit", 10: "Fixed overhead in the standard cost, per unit", 11: "Commission rate",
              13: "Contribution without promotion", 14: "Contribution with promotion", 15: "Difference",
              16: "Break-even lift (formula)", 17: "Break-even lift, fixed overhead treated as fixed",
              18: "Break-even lift found by Goal Seek (value)", 19: "Discount at the report year's volume",
              20: "Contribution given up, after the commissions saved"}
    sources = {4: "Parameters (the report year's promotion of that scope)", 5: "Parameters (the proposal's rates)",
               6: "Assumption; Requirement 3 found no increase", 7: "BilledLines, the promotion's lines",
               8: "BilledLines: GrossAmount over units", 9: "BilledLines: Quantity x StandardCost over units",
               10: "Items[StandardFixedOverheadCost] of the lines' items", 11: "Parameters (Tutorial 7.3)",
               13: "Units x (price x (1 - commission) - cost)", 14: "Formula", 15: "With less without",
               16: "(P(1-c) - S) / (P(1-d)(1-c) - S) - 1", 17: "The same with S less the fixed overhead",
               18: "Goal Seek: Difference to 0 by changing the lift; the lift then returned to 0",
               19: "Units x price x discount rate", 20: "The discount less the commission it saves"}
    for r, label in labels.items():
        put(ws, {f"A{r}": label, f"F{r}": sources[r]})
    yr = "BilledLines[InvoiceYear],ReportYear"
    for c, scope, name, promo_name, rate_name in PROPOSAL:
        k = f"(BilledLines[PromotionID]={c}$4)*(BilledLines[InvoiceYear]=ReportYear)"
        put(ws, {
            f"{c}4": f"={promo_name}", f"{c}5": f"={rate_name}", f"{c}6": 0,
            f"{c}7": f"=SUMIFS(BilledLines[Quantity],BilledLines[PromotionID],{c}$4,{yr})",
            f"{c}8": f"=SUMIFS(BilledLines[GrossAmount],BilledLines[PromotionID],{c}$4,{yr})/{c}7",
            f"{c}9": f"=SUMPRODUCT({k}*BilledLines[Quantity]*BilledLines[StandardCost])/{c}7",
            f"{c}10": (f"=LET(k,{k},SUM(FILTER(BilledLines[Quantity],k)*XLOOKUP(FILTER(BilledLines[ItemID],k),"
                       f"Items[ItemID],Items[StandardFixedOverheadCost],0)))/{c}7"),
            f"{c}11": "=CommissionRate",
            f"{c}13": f"={c}7*({c}8*(1-{c}11)-{c}9)",
            f"{c}14": f"={c}7*(1+{c}6)*({c}8*(1-{c}5)*(1-{c}11)-{c}9)",
            f"{c}15": f"={c}14-{c}13",
            f"{c}16": f"=({c}8*(1-{c}11)-{c}9)/({c}8*(1-{c}5)*(1-{c}11)-{c}9)-1",
            f"{c}17": f"=({c}8*(1-{c}11)-({c}9-{c}10))/({c}8*(1-{c}5)*(1-{c}11)-({c}9-{c}10))-1",
            f"{c}19": f"={c}7*{c}8*{c}5", f"{c}20": f"={c}19*(1-{c}11)"})
    for r in (13, 14, 15, 19, 20):
        put(ws, {f"E{r}": f"=SUM(B{r}:D{r})"})
    blue(ws, "B6:D6")
    fmt(ws, "B4:D4", "0")
    fmt(ws, "B5:D6", "0.0%")
    fmt(ws, "B7:D7", MONEY)
    fmt(ws, "B8:D10", MONEY)
    fmt(ws, "B11:D11", "0.000%")
    fmt(ws, "B13:E15", MONEY)
    fmt(ws, "B16:D18", PCT)
    fmt(ws, "B19:E20", MONEY)
    widths(ws, {"A": 50, "B": 18, "C": 18, "D": 18, "E": 18, "F": 60, "G": 14})
    xl.wait_ready(wb.Application)
    found = {}
    for c, *_ in PROPOSAL:                                # Goal Seek each column, then return the lift to 0
        xl.retry(ws.Range(f"{c}15").GoalSeek, 0, ws.Range(f"{c}6"))
        found[c] = ws.Range(f"{c}6").Value
        ws.Range(f"{c}18").Value = found[c]
        ws.Range(f"{c}6").Value = 0
    note(ws, "B18", "Frozen values: what Goal Seek found (Set cell row 15, To value 0, By changing cell row 6) before "
                    "the lift was returned to 0. Row 16 computes the same lift with a formula, live.")

    heading(ws, 22, "(2) All nine promotions: break-even lift against the difference measured in Requirement 3")
    header(ws, 23, 1, ["PromotionID", "Scope", "DiscountPct", "Units billed", "Price before discount",
                       "Standard cost per unit", "Break-even lift", "Measured difference (R3 Volume)",
                       "Share of the break-even reached"])
    put(ws, {"A24": "=SORT(Promotions[PromotionID])"})
    for i in range(n):
        r = 24 + i
        put(ws, {f"B{r}": (f"=XLOOKUP($A{r},Promotions[PromotionID],Promotions[PromoCollection]&"
                           "Promotions[PromoItemGroup]&Promotions[PromoSegment])"),
                 f"C{r}": f"=XLOOKUP($A{r},Promotions[PromotionID],Promotions[DiscountPct])",
                 f"D{r}": f"=SUMIFS(BilledLines[Quantity],BilledLines[PromotionID],$A{r})",
                 f"E{r}": f"=SUMIFS(BilledLines[GrossAmount],BilledLines[PromotionID],$A{r})/D{r}",
                 f"F{r}": f"=SUMPRODUCT((BilledLines[PromotionID]=$A{r})*BilledLines[Quantity]*BilledLines[StandardCost])/D{r}",
                 f"G{r}": f"=(E{r}*(1-CommissionRate)-F{r})/(E{r}*(1-C{r})*(1-CommissionRate)-F{r})-1",
                 f"H{r}": f"=XLOOKUP($A{r},'R3 Volume'!$A${k1}:$A${k2},'R3 Volume'!$F${k1}:$F${k2})",
                 f"I{r}": f"=H{r}/G{r}"})
    e9 = 24 + n
    put(ws, {f"A{e9}": "Lowest break-even lift", f"G{e9}": f"=MIN(G24:G{e9 - 1})",
             f"A{e9 + 1}": "Highest break-even lift", f"G{e9 + 1}": f"=MAX(G24:G{e9 - 1})",
             f"A{e9 + 2}": "Largest share of its break-even any promotion reached", f"I{e9 + 2}": f"=MAX(I24:I{e9 - 1})"})
    fmt(ws, f"C24:C{e9 - 1}", "0%")
    fmt(ws, f"D24:F{e9 - 1}", MONEY)
    fmt(ws, f"G24:G{e9 + 1}", PCT)
    fmt(ws, f"H24:H{e9 - 1}", "+0.0%;-0.0%")
    fmt(ws, f"I24:I{e9 + 2}", "0.0%")

    d0 = e9 + 4
    heading(ws, d0, "(3) The Furniture promotion: difference in contribution by discount rate (across) and volume lift "
                    "(down), a data table")
    put(ws, {f"A{d0 + 1}": "Discount rate (the data table's row input cell)", f"C{d0 + 1}": 0.1,
             f"A{d0 + 2}": "Volume lift (the data table's column input cell)", f"C{d0 + 2}": 0,
             f"A{d0 + 3}": "Difference at these inputs",
             f"C{d0 + 3}": f"=$C$7*(1+C{d0 + 2})*($C$8*(1-C{d0 + 1})*(1-$C$11)-$C$9)-$C$13"})
    blue(ws, f"C{d0 + 1}:C{d0 + 2}")
    fmt(ws, f"C{d0 + 1}:C{d0 + 2}", "0%")
    fmt(ws, f"C{d0 + 3}", MONEY)
    t0 = d0 + 5                                              # the data table's top row
    put(ws, {f"A{t0}": "Lift (down) by discount rate (across)", f"B{t0}": f"=C{d0 + 3}"})
    for j, rate in enumerate(RATES):
        ws.Cells(t0, 3 + j).Value = rate
    for i, lift in enumerate(LIFTS):
        ws.Cells(t0 + 1 + i, 2).Value = lift
    ws.Range(f"B{t0}:{col(2 + len(RATES))}{t0 + len(LIFTS)}").Table(ws.Range(f"C{d0 + 1}"), ws.Range(f"C{d0 + 2}"))
    tb = t0 + len(LIFTS) + 1
    put(ws, {f"A{tb}": "Break-even lift at this rate"})
    for j in range(len(RATES)):
        c = col(3 + j)
        put(ws, {f"{c}{tb}": f"=($C$8*(1-$C$11)-$C$9)/($C$8*(1-{c}${t0})*(1-$C$11)-$C$9)-1"})
    last_c = col(2 + len(RATES))
    fmt(ws, f"C{t0}:{last_c}{t0}", "0%")
    fmt(ws, f"B{t0 + 1}:B{t0 + len(LIFTS)}", "0%")
    fmt(ws, f"B{t0}", "#,##0")
    fmt(ws, f"C{t0 + 1}:{last_c}{t0 + len(LIFTS)}", "#,##0")
    fmt(ws, f"C{tb}:{last_c}{tb}", PCT)
    rule = ws.Range(f"C{t0 + 1}:{last_c}{t0 + len(LIFTS)}").FormatConditions.Add(1, 5, "=0")   # Cell Value > 0
    rule.Interior.Color = xl.LIGHT_FILL

    g0 = tb + 3
    heading(ws, g0, "(4) Goal Seek: the Furniture discount at which the largest increase measured in Requirement 3 "
                    "would just pay for the promotion")
    put(ws, {f"A{g0 + 1}": "Largest increase measured (R3 Volume, LargestLift)", f"C{g0 + 1}": "=LargestLift",
             f"A{g0 + 2}": "Furniture discount rate (Goal Seek's changing cell; the value it found)", f"C{g0 + 2}": 0.1,
             f"A{g0 + 3}": "Difference at that discount and increase",
             f"C{g0 + 3}": f"=$C$7*(1+C{g0 + 1})*($C$8*(1-C{g0 + 2})*(1-$C$11)-$C$9)-$C$13"})
    fmt(ws, f"C{g0 + 1}", "0.00%")
    fmt(ws, f"C{g0 + 2}", "0.00%")
    fmt(ws, f"C{g0 + 3}", MONEY)
    xl.wait_ready(wb.Application)
    xl.retry(ws.Range(f"C{g0 + 3}").GoalSeek, 0, ws.Range(f"C{g0 + 2}"))
    note(ws, f"C{g0 + 2}", f"A frozen value: Goal Seek set C{g0 + 3} to 0 by changing this cell, and the result was kept "
                           "(OK in the Goal Seek Status dialog).")

    a0 = g0 + 6
    assumptions = [
        ("Assumption", "Value used", "Basis", "Sensitivity"),
        ("Discount rates", "8%, 10%, 12%", "The proposal, which repeats the report year's rates",
         f"At 5% the Furniture promotion needs a {pct(f.be_at[0.05])} increase instead of {pct(n4['grp']['be'])}"),
        ("Volume lift", "0%", "Requirement 3: no promotion's months showed an unusual increase",
         "The break-even lifts in row 16 are the increases each promotion would need"),
        ("Orders without the promotion", "Same orders at the price before discount",
         "Promotion lines carry the customer's usual price, with the discount on top",
         "If some orders would have been lost without the promotion, its cost is lower"),
        ("Units, price, and cost", "The report year's billed lines of each promotion",
         "BilledLines: the promotion's lines repeat in the plan year at the same volume and mix",
         "The Design Trade promotion depends on which customers order; its volume is the least certain"),
        ("Variable cost per unit", "Standard cost per unit", "Item standard costs, including fixed overhead",
         f"Treating fixed overhead as fixed lowers the Furniture break-even to {pct(n4['grp']['be_variable'])}"),
        ("Commission rate", f"{pct(f.rate, 3)}", "Tutorial 7.3: commission expense over all revenue",
         "Small; commissions fall with the discount")]
    for i, row in enumerate(assumptions):
        for j, v in enumerate(row):
            ws.Cells(a0 + i, 1 + j).Value = v
    bold(ws, f"A{a0}:D{a0}")
    ws.Range(f"A{a0}:D{a0 + len(assumptions) - 1}").WrapText = True
    ws.Range(f"A{a0}:D{a0 + len(assumptions) - 1}").VerticalAlignment = TOP
    b.found["r4"] = dict(e9=e9, d0=d0, t0=t0, tb=tb, g0=g0)

    # --- R4 Budgets --------------------------------------------------------------------------------------------------
    bu = new_sheet(b, "R4 Budgets")
    title(bu, "Requirement 4: how the budgets planned the promotions, and what the proposal would cost (BudgetPrices)")
    heading(bu, 3, "(1) Budgeted revenue over the budgeted quantity at list price, by fiscal year and month")
    header(bu, 4, 1, ["Fiscal year"] + list(range(1, 13)) + ["Year"])
    years = [f.F, f.F + 1, y, N]
    for i in range(4):
        r = 5 + i
        put(bu, {f"A{r}": "=FirstYear" if i == 0 else ("=PlanYear" if i == 3 else f"=A{r - 1}+1"),
                 f"N{r}": (f"=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[FiscalYear],$A{r})/"
                           f"SUMIFS(BudgetPrices[ListAmount],BudgetPrices[FiscalYear],$A{r})")})
        for m in range(12):
            c = col(2 + m)
            put(bu, {f"{c}{r}": (f"=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[FiscalYear],$A{r},BudgetPrices[Month],"
                                 f"{c}$4)/SUMIFS(BudgetPrices[ListAmount],BudgetPrices[FiscalYear],$A{r},"
                                 f"BudgetPrices[Month],{c}$4)")})
    put(bu, {"A9": "Largest monthly difference from the year's ratio, plan year", "N9": "=MAX(ABS(B8:M8-N8))"})
    fmt(bu, "A5:A8", "0")
    fmt(bu, "B5:N9", "0.0000")
    heading(bu, 11, "(2) The same by item group: November against the months no promotion ran in (1, 2, 5 to 8, 12)")
    header(bu, 12, 1, ["Fiscal year", "Item group"] + list(range(1, 13)) + ["Lowest in months with no promotion",
                                                                           "November below it"])
    groups = f.budget_groups
    r = 13
    for yy in range(3):
        for grp in groups:
            put(bu, {f"A{r}": "=FirstYear" if yy == 0 else f"=FirstYear+{yy}", f"B{r}": grp,
                     f"O{r}": f"=MIN(CHOOSECOLS(C{r}:N{r},1,2,5,6,7,8,12))", f"P{r}": f"=M{r}<O{r}"})
            for m in range(12):
                c = col(3 + m)
                put(bu, {f"{c}{r}": (f"=SUMIFS(BudgetPrices[BudgetAmount],BudgetPrices[FiscalYear],$A{r},"
                                     f"BudgetPrices[ItemGroup],$B{r},BudgetPrices[Month],{c}$12)/SUMIFS("
                                     f"BudgetPrices[ListAmount],BudgetPrices[FiscalYear],$A{r},BudgetPrices[ItemGroup],"
                                     f"$B{r},BudgetPrices[Month],{c}$12)")})
            r += 1
    nv = r
    put(bu, {f"A{nv}": "Years and groups where November is not below the months with no promotion",
             f"P{nv}": f"=COUNTIF(P13:P{nv - 1},FALSE)"})
    fmt(bu, f"A13:A{nv - 1}", "0")
    fmt(bu, f"C13:O{nv - 1}", "0.0000")
    p0 = nv + 2
    heading(bu, p0, "(3) The promoted items in their promotion months (the collection and item-group promotions, "
                    "months from R3 Volume)")
    header(bu, p0 + 1, 1, ["PromotionID", "ScopeType", "Scope", "Year", "First month", "Last month",
                           "Budgeted revenue", "At list price", "Ratio in the promotion months",
                           "Ratio of the same items in the other months"])
    pa = p0 + 2
    put(bu, {f"A{pa}": f'=FILTER({cal("A")},({cal("C")}<>"Segment")*({cal("K")}<=ReportYear))'})
    npr = len(f.promoted)
    two = '{"Collection","ItemGroup"}'
    for i in range(npr):
        r = pa + i
        scope = (f"CHOOSE(MATCH($B{r},{two},0),BudgetPrices[CollectionName],BudgetPrices[ItemGroup]),$C{r},"
                 f"BudgetPrices[FiscalYear],$D{r}")
        window = f'BudgetPrices[Month],">="&$E{r},BudgetPrices[Month],"<="&$F{r}'
        put(bu, {f"B{r}": f"=XLOOKUP($A{r},{cal('A')},{cal('C')})", f"C{r}": f"=XLOOKUP($A{r},{cal('A')},{cal('D')})",
                 f"D{r}": f"=XLOOKUP($A{r},{cal('A')},{cal('K')})", f"E{r}": f"=XLOOKUP($A{r},{cal('A')},{cal('L')})",
                 f"F{r}": f"=XLOOKUP($A{r},{cal('A')},{cal('M')})",
                 f"G{r}": f"=SUMIFS(BudgetPrices[BudgetAmount],{scope},{window})",
                 f"H{r}": f"=SUMIFS(BudgetPrices[ListAmount],{scope},{window})", f"I{r}": f"=G{r}/H{r}",
                 f"J{r}": (f"=(SUMIFS(BudgetPrices[BudgetAmount],{scope})-G{r})/"
                           f"(SUMIFS(BudgetPrices[ListAmount],{scope})-H{r})")})
    pt_ = pa + npr
    put(bu, {f"A{pt_}": "All of them", f"G{pt_}": f"=SUM(G{pa}:G{pt_ - 1})", f"H{pt_}": f"=SUM(H{pa}:H{pt_ - 1})",
             f"I{pt_}": f"=G{pt_}/H{pt_}"})
    fmt(bu, f"G{pa}:H{pt_}", MONEY)
    fmt(bu, f"I{pa}:J{pt_}", "0.0000")
    bold(bu, f"A{pt_}:J{pt_}")
    b0 = pt_ + 3
    heading(bu, b0, "(4) The plan year's budget")
    plan = [("Approved by (EmployeeID)",
             '=TEXTJOIN(", ",TRUE,UNIQUE(FILTER(BudgetPrices[ApprovedByEmployeeID],BudgetPrices[FiscalYear]=PlanYear)))',
             "General"),
            ("Name and job title", f'=XLOOKUP(--B{b0 + 1},Employees[EmployeeID],Employees[EmployeeName])&", "&'
                                   f"XLOOKUP(--B{b0 + 1},Employees[EmployeeID],Employees[JobTitle])", "General"),
            ("Approved on", ('=LET(d,FILTER(BudgetPrices[ApprovedDate],BudgetPrices[FiscalYear]=PlanYear),'
                             'IF(ROWS(UNIQUE(d))=1,MIN(d),"several dates"))'), DATE),
            ("Budgeted revenue over list, the whole year", "=N8", "0.0000"),
            ("Largest monthly difference from it", "=N9", "0.0000")]
    for i, (label, formula, number_format) in enumerate(plan, start=1):
        put(bu, {f"A{b0 + i}": label, f"B{b0 + i}": formula})
        fmt(bu, f"B{b0 + i}", number_format)
    c0 = b0 + len(plan) + 3
    heading(bu, c0, "(5) What the proposed calendar would cost against the plan year's budget, at the report year's "
                    "volumes with no increase")
    header(bu, c0 + 1, 1, ["Promotion", "PromotionID", "Proposed rate", "Q1", "Q2", "Q3", "Q4", "Year"])
    for i, (_, scope, name, promo_name, rate_name) in enumerate(PROPOSAL):
        r = c0 + 2 + i
        put(bu, {f"A{r}": name, f"B{r}": f"={promo_name}", f"C{r}": f"={rate_name}", f"H{r}": f"=SUM(D{r}:G{r})"})
        for k in range(4):
            put(bu, {f"{col(4 + k)}{r}": (f"=$C{r}*SUMIFS(BilledLines[GrossAmount],BilledLines[PromotionID],$B{r},"
                                          f"BilledLines[InvoiceYear],ReportYear,BilledLines[InvoiceQuarter],{k + 1})")})
    ct = c0 + 5
    put(bu, {f"A{ct}": "Discounts given", f"A{ct + 1}": "Rounded to hundreds",
             f"A{ct + 2}": "Contribution given up, after the commissions saved"})
    for k in range(5):
        c = col(4 + k)
        put(bu, {f"{c}{ct}": f"=SUM({c}{c0 + 2}:{c}{ct - 1})", f"{c}{ct + 1}": f"=ROUND({c}{ct},-2)",
                 f"{c}{ct + 2}": f"={c}{ct}*(1-CommissionRate)"})
    fmt(bu, f"C{c0 + 2}:C{ct - 1}", "0%")
    fmt(bu, f"D{c0 + 2}:H{ct + 2}", MONEY)
    fmt(bu, f"D{ct + 1}:H{ct + 1}", "#,##0")
    bold(bu, f"A{ct}:H{ct}")
    v0 = ct + 5
    heading(bu, v0, "(6) Why the estimate does not use the budget's quantities")
    fg = "XLOOKUP(FurniturePromotion,Promotions[PromotionID],Promotions[PromoItemGroup])"
    basis = [("The Furniture promotion's first and last month (R3 Volume)",
              f"=XLOOKUP(FurniturePromotion,{cal('A')},{cal('L')})", f"=XLOOKUP(FurniturePromotion,{cal('A')},{cal('M')})",
              "0"),
             ("Furniture units in the plan year's budget for those months",
              (f'=SUMIFS(BudgetPrices[Quantity],BudgetPrices[FiscalYear],PlanYear,BudgetPrices[ItemGroup],{fg},'
               f'BudgetPrices[Month],">="&B{v0 + 1},BudgetPrices[Month],"<="&C{v0 + 1})'), None, "#,##0.00"),
             ("Furniture units ordered in those months of the report year (OrderLines)",
              (f'=SUMIFS(OrderLines[Quantity],OrderLines[ItemGroup],{fg},OrderLines[OrderYear],ReportYear,'
               f'OrderLines[OrderMonth],">="&B{v0 + 1},OrderLines[OrderMonth],"<="&C{v0 + 1})'), None, "#,##0.00"),
             ("The budget's units over the units ordered", f"=B{v0 + 2}/B{v0 + 3}", None, "0.00"),
             ("Columns of BudgetPrices that identify a customer",
              '=SUM(--ISNUMBER(SEARCH("Customer",BudgetPrices[#Headers])))', None, "0")]
    for i, (label, f1, f2, number_format) in enumerate(basis, start=1):
        put(bu, {f"A{v0 + i}": label, f"B{v0 + i}": f1})
        if f2:
            put(bu, {f"C{v0 + i}": f2})
        fmt(bu, f"B{v0 + i}:C{v0 + i}", number_format)
    widths(bu, {"A": 58, "B": 14, "C": 14})
    for k in range(4, 17):
        bu.Columns(k).ColumnWidth = 12
    b.found["r4b"] = dict(nv=nv, pa=pa, pt=pt_, b0=b0, c0=c0, ct=ct, v0=v0)

    fur = n4["grp"]
    best = f.best
    text_block(ws, a0 + len(assumptions) + 1, f"{MA}, Requirement 4 (model)", [
        f"Break-even increases. With the commission rate of {pct(f.rate, 3)}, the proposal's promotions need "
        f"{pct(n4['coll']['be'])} more volume (Harbor), {pct(fur['be'])} (Furniture; {pct(fur['be_variable'])} if the "
        f"fixed overhead in the standard cost is treated as fixed, as Tutorial 7.3 noted), and {pct(n4['seg']['be'])} "
        f"(Design Trade) to pay for themselves. Across all nine promotions the break-even increases run from "
        f"{pct(n4['be_low'], 0)} to {pct(n4['be_high'], 0)}, and no measured difference reached half of one.",
        f"Data table and Goal Seek. At a 10% discount the Furniture promotion turns positive only between a 30% and a "
        f"35% increase; at 5% it needs {pct(f.be_at[0.05])}. Goal Seek at the largest increase measured in "
        f"Requirement 3 (promotion {best['id']}'s {spct(best['lift'])}) gives a Furniture discount of about "
        f"{pct(f.goal_discount)}: the most generous discount the best response on record would pay for."], span=6)
    pq_ = f.prop_quarters
    text_block(bu, v0 + len(basis) + 2, f"{MA}, Requirement 4 (budgets and the cost of the calendar)", [
        f"The budgets. The {f.F} to {y} budgets planned their promotions: the promoted items are budgeted at "
        f"{n4['promoted']:.4f} of list in their promotion months (the year's collection in March and April, the "
        f"year's item group in September and October), against {min(x['other'] for x in f.promoted):.2f} to "
        f"{max(x['other'] for x in f.promoted):.2f} for the same items in their other months, and every item group "
        f"is budgeted lower in November, the segment promotion's month. The {N} budget, approved by the "
        f"{f.cfo_title.lower()} (EmployeeID {n4['cfo']}) on {n4['approved']}, is flat at about {n4['flat']:.4f} of "
        "list in every month: it plans no promotion.",
        f"The cost of the calendar. At the {y} volumes and with no increase, the three promotions would give "
        f"{money(n4['cost'])} of discounts, or {money(n4['contribution'])} of contribution after the commissions saved, "
        f"against a budget without promotions. The discounts would land about {money(pq_[1], 0)} in the first quarter, "
        f"{money(pq_[2], 0)} in the second, {money(pq_[3], 0)} in the third, and {money(pq_[4], 0)} in the fourth, "
        "because the fall promotion's orders are invoiced after it ends.",
        f"The volume basis. The estimate uses the {y} billed lines, not the budget's quantities, because the budget's "
        f"volume is several times actual (Chapter 7): it plans {n4['budget_units']:,.0f} Furniture units for "
        f"September and October {N} against {n4['ordered']:,.0f} ordered in those months of {y}, so a cost taken from "
        "it would be overstated almost fourfold. BudgetLine has no customer dimension, so the Design Trade promotion "
        "cannot be costed from the budget at all."], span=8)

    t = R4
    for c, scope, name, *_ in PROPOSAL:
        m = f.model_c[scope]
        key = {"Collection": "coll", "ItemGroup": "grp", "Segment": "seg"}[scope]
        b.check(t, f"{name}: units ({c}7)", round(m["units"], 2), f"='R4 Model'!{c}7")
        b.check(t, f"{name}: price before discount per unit ({c}8)", m["price"], f"='R4 Model'!{c}8", 1e-6)
        b.check(t, f"{name}: standard cost per unit ({c}9)", m["cost"], f"='R4 Model'!{c}9", 1e-6)
        b.check(t, f"{name}: break-even lift, formula ({c}16)", n4[key]["be"], f"='R4 Model'!{c}16", 1e-9, "0.0000%")
        b.check(t, f"{name}: break-even lift, Goal Seek ({c}18, frozen)", n4[key]["be"], f"='R4 Model'!{c}18", 1e-4,
                "0.0000%")
    b.check(t, "Furniture: fixed overhead per unit (C10)", fur["fixed"], "='R4 Model'!C10", 1e-6)
    b.check(t, "Furniture: break-even lift with fixed overhead treated as fixed (C17)", fur["be_variable"],
            "='R4 Model'!C17", 1e-9, "0.0000%")
    b.check(t, "commission rate in the model (C11)", f.rate, "='R4 Model'!C11", 1e-12, "0.0000%")
    b.check(t, "difference of the three at no increase (E15)", -n4["contribution"], "='R4 Model'!E15", 0.01)
    b.check(t, "their discounts at the report year's volume (E19)", round(n4["cost"], 2), "='R4 Model'!E19")
    b.check(t, "contribution given up after commissions (E20)", round(n4["contribution"], 2), "='R4 Model'!E20")
    b.check(t, "lowest break-even of the nine promotions", n4["be_low"], f"='R4 Model'!G{e9}", 1e-9, "0.0000%")
    b.check(t, "highest break-even of the nine promotions", n4["be_high"], f"='R4 Model'!G{e9 + 1}", 1e-9, "0.0000%")
    share = max(f.vol[pid]["lift"] / f.be[pid] for pid in f.ids)
    b.check(t, "largest share of its break-even any promotion reached (under half)", share, f"='R4 Model'!I{e9 + 2}",
            1e-9, "0.0000%")
    for i, pid in enumerate(f.ids):
        b.check(t, f"promotion {pid}: break-even lift", f.be[pid], f"='R4 Model'!G{24 + i}", 1e-9, "0.0000%")
    for rate in RATES:
        b.check(t, f"Furniture break-even lift at {rate:.0%}", f.be_at[rate], f"='R4 Model'!{col(3 + RATES.index(rate))}{tb}",
                1e-9, "0.0000%")
    for rate, lift in ((0.10, 0.30), (0.10, 0.35), (0.05, 0.15), (0.12, 0.40), (0.08, 0.0)):
        cell = f"{col(3 + RATES.index(rate))}{t0 + 1 + LIFTS.index(lift)}"
        b.check(t, f"data table: difference at {rate:.0%} and a {lift:.0%} lift ({cell})", f.difference(rate, lift),
                f"='R4 Model'!{cell}", 0.01)
    b.check(t, "Goal Seek: the largest increase measured", best["lift"], f"='R4 Model'!C{g0 + 1}", 1e-9, "0.0000%")
    b.check(t, "Goal Seek: the Furniture discount it supports (frozen)", f.goal_discount, f"='R4 Model'!C{g0 + 2}", 1e-6,
            "0.0000%")
    b.check(t, "Goal Seek: the difference at that discount", 0, f"='R4 Model'!C{g0 + 3}", 0.01)
    for i, yy in enumerate(years):
        b.check(t, f"budgeted revenue over list, {yy}", f.budget_year[yy], f"='R4 Budgets'!N{5 + i}", 1e-9, RATIO)
    b.check(t, f"largest monthly difference from the {N} ratio", f.max_dev, "='R4 Budgets'!N9", 1e-9, RATIO)
    b.check(t, "years and groups where November is not lower", f.november_not_lower, f"='R4 Budgets'!P{nv}", 0, COUNT)
    for i, x in enumerate(f.promoted):
        b.check(t, f"promotion {x['id']}: budgeted at a share of list in its months", x["ratio"],
                f"='R4 Budgets'!I{pa + i}", 1e-9, RATIO)
        b.check(t, f"promotion {x['id']}: the same items in the other months", x["other"], f"='R4 Budgets'!J{pa + i}",
                1e-9, RATIO)
    b.check(t, "the promoted items in their promotion months, all", n4["promoted"], f"='R4 Budgets'!I{pt_}", 1e-9, RATIO)
    b.check(t, f"{N} budget approved by (EmployeeID)", n4["cfo"], f"=--'R4 Budgets'!B{b0 + 1}", 0, COUNT)
    b.check(t, "...name and job title", f"{f.cfo_name}, {f.cfo_title}", f"='R4 Budgets'!B{b0 + 2}", 0, "General")
    b.check(t, "...on", serial(n4["approved"]), f"='R4 Budgets'!B{b0 + 3}", 0, DATE)
    pqe = f.prop_quarters_exact
    for k in range(4):
        b.check(t, f"the calendar's discounts in Q{k + 1}", round(pqe.get(k + 1, 0.0), 2), f"='R4 Budgets'!{col(4 + k)}{ct}")
        b.check(t, f"...rounded to hundreds, Q{k + 1}", pq_[k + 1], f"='R4 Budgets'!{col(4 + k)}{ct + 1}", 0, "#,##0")
    b.check(t, "the calendar's discounts in the plan year", round(n4["cost"], 2), f"='R4 Budgets'!H{ct}")
    b.check(t, "contribution given up after the commissions saved", round(n4["contribution"], 2),
            f"='R4 Budgets'!H{ct + 2}")
    b.check(t, f"Furniture units budgeted for September and October {N}", n4["budget_units"], f"='R4 Budgets'!B{v0 + 2}",
            0.005, "#,##0.00")
    b.check(t, f"Furniture units ordered in September and October {y}", round(n4["ordered"], 2),
            f"='R4 Budgets'!B{v0 + 3}", 0.005, "#,##0.00")
    b.check(t, "BudgetPrices columns that identify a customer", 0, f"='R4 Budgets'!B{v0 + 5}", 0, COUNT)

    st = b.found["doc"]
    st["sheets"]["R4 Model"] = ("Requirement 4: the contribution margin model of the three proposed promotions, every "
                                "promotion's break-even, the Furniture data table, and Goal Seek")
    st["sheets"]["R4 Budgets"] = ("Requirement 4: the budgets' planned prices by month, the plan year's budget, and the "
                                  "cost of the proposed calendar by quarter")
    write_doc(b)
    settle(b)



# --- Requirement 5 ------------------------------------------------------------------------------------------------------

def r5(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    n5 = f.n5
    n = len(f.ids)
    ol, bl = xl.table(wb, "OrderLines"), xl.table(wb, "BilledLines")
    xl.add_column(ol, "DateOK", '=IF([@PromotionID]="","",AND([@OrderDate]>=[@EffectiveStartDate],'
                                '[@OrderDate]<=[@EffectiveEndDate]))')
    xl.add_column(ol, "ScopeOK", '=IF([@PromotionID]="","",SWITCH([@ScopeType],"Collection",[@CollectionName]='
                                 '[@PromoCollection],"ItemGroup",[@ItemGroup]=[@PromoItemGroup],"Segment",'
                                 '[@CustomerSegment]=[@PromoSegment],FALSE))')
    xl.add_column(ol, "RateOK", '=IF([@PromotionID]="","",ABS([@Discount]-[@DiscountPct])<0.0000001)')
    status = ('=IF([@PriceOverrideApprovalID]="","",XLOOKUP([@PriceOverrideApprovalID],'
              'Overrides[PriceOverrideApprovalID],Overrides[Status],"Not found"))')
    xl.add_column(ol, "OverrideStatus", status)
    xl.add_column(bl, "OverrideStatus", status)
    xl.wait_ready(wb.Application)

    ws = new_sheet(b, "R5 Controls")
    title(ws, "Requirement 5: the controls over promotions (OrderLines, Promotions, Items, Overrides)")
    heading(ws, 3, "(1) Four tests of every promotion line, by promotion (OrderLines columns DateOK, ScopeOK, RateOK)")
    header(ws, 4, 1, ["PromotionID", "PromotionName", "ScopeType", "Scope", "Lines", "Outside the recorded dates",
                      "Outside the scope", "Rate differs from DiscountPct", "Window start", "Window end",
                      "In scope and window without the promotion"])
    put(ws, {"A5": "=SORT(Promotions[PromotionID])"})
    for i in range(n):
        r = 5 + i
        mine = f"OrderLines[PromotionID],$A{r}"
        put(ws, {f"B{r}": f"=XLOOKUP($A{r},Promotions[PromotionID],Promotions[PromotionName])",
                 f"C{r}": f"=XLOOKUP($A{r},Promotions[PromotionID],Promotions[ScopeType])",
                 f"D{r}": (f"=XLOOKUP($A{r},Promotions[PromotionID],Promotions[PromoCollection]&Promotions[PromoItemGroup]&"
                           "Promotions[PromoSegment])"),
                 f"E{r}": f"=COUNTIFS({mine})", f"F{r}": f"=COUNTIFS({mine},OrderLines[DateOK],FALSE)",
                 f"G{r}": f"=COUNTIFS({mine},OrderLines[ScopeOK],FALSE)",
                 f"H{r}": f"=COUNTIFS({mine},OrderLines[RateOK],FALSE)",
                 f"I{r}": (f"=IF(F{r}>0,EOMONTH(MINIFS(OrderLines[OrderDate],{mine}),-1)+1,"
                           f"XLOOKUP($A{r},Promotions[PromotionID],Promotions[EffectiveStartDate]))"),
                 f"J{r}": (f"=IF(F{r}>0,EOMONTH(MAXIFS(OrderLines[OrderDate],{mine}),0),"
                           f"XLOOKUP($A{r},Promotions[PromotionID],Promotions[EffectiveEndDate]))"),
                 f"K{r}": (f"=COUNTIFS(CHOOSE(MATCH($C{r},{SCOPES},0),{scope_range('OrderLines')}),$D{r},"
                           f'OrderLines[OrderDate],">="&I{r},OrderLines[OrderDate],"<="&J{r},'
                           f'OrderLines[PromotionID],"<>"&$A{r})')})
    tr = 5 + n
    put(ws, {f"A{tr}": "Total"})
    for c in "EFGHK":
        put(ws, {f"{c}{tr}": f"=SUM({c}5:{c}{tr - 1})"})
    fmt(ws, f"I5:J{tr - 1}", DATE)
    fmt(ws, f"E5:H{tr}", COUNT)
    fmt(ws, f"K5:K{tr}", COUNT)
    bold(ws, f"A{tr}:K{tr}")
    note(ws, "I4", "The recorded effective dates, except for a promotion whose lines all fail the date test: its window "
                   "is then the calendar months in which its lines were ordered (the evidence in (2)).")

    e0 = tr + 2
    heading(ws, e0, "(2) The promotions whose recorded dates fail: when were they meant to run? (the order months, and "
                    "each year's budget for the collection, BudgetPrices)")
    header(ws, e0 + 1, 1, ["PromotionID", "Scope", "Recorded start", "Recorded end", "End on or before start",
                           "First order", "Last order"] + list(range(1, 13))
           + ["Highest budget ratio in the order months", "Lowest in months with no promotion",
              "Budget planned a discount in those months"])
    ea = e0 + 2
    put(ws, {f"A{ea}": f"=FILTER(A5:A{tr - 1},F5:F{tr - 1}>0)"})
    nb = len(f.bad)
    mh = f"$H${e0 + 1}:$S${e0 + 1}"
    for i in range(nb):
        r = ea + i
        put(ws, {f"B{r}": f"=XLOOKUP($A{r},$A$5:$A${tr - 1},$D$5:$D${tr - 1})",
                 f"C{r}": f"=XLOOKUP($A{r},Promotions[PromotionID],Promotions[EffectiveStartDate])",
                 f"D{r}": f"=XLOOKUP($A{r},Promotions[PromotionID],Promotions[EffectiveEndDate])",
                 f"E{r}": f"=D{r}<=C{r}",
                 f"F{r}": f"=MINIFS(OrderLines[OrderDate],OrderLines[PromotionID],$A{r})",
                 f"G{r}": f"=MAXIFS(OrderLines[OrderDate],OrderLines[PromotionID],$A{r})",
                 f"T{r}": f"=MAX(FILTER(H{r}:S{r},({mh}>=MONTH($F{r}))*({mh}<=MONTH($G{r}))))",
                 f"U{r}": f"=MIN(CHOOSECOLS(H{r}:S{r},1,2,5,6,7,8,12))", f"V{r}": f"=T{r}<U{r}-0.02"})
        for m in range(12):
            c = col(8 + m)
            crit = (f"BudgetPrices[CollectionName],$B{r},BudgetPrices[FiscalYear],YEAR($F{r}),BudgetPrices[Month],"
                    f"{c}${e0 + 1}")
            put(ws, {f"{c}{r}": f"=SUMIFS(BudgetPrices[BudgetAmount],{crit})/SUMIFS(BudgetPrices[ListAmount],{crit})"})
    eb = ea + nb
    put(ws, {f"A{eb}": "Promotions whose recorded end date is on or before the start date (Promotions)",
             f"E{eb}": "=SUM(--(Promotions[EffectiveEndDate]<=Promotions[EffectiveStartDate]))",
             f"A{eb + 1}": "Failing promotions whose budget planned the discount in their order months",
             f"V{eb + 1}": f"=COUNTIF(V{ea}:V{eb - 1},TRUE)"})
    fmt(ws, f"C{ea}:D{eb - 1}", DATE)
    fmt(ws, f"F{ea}:G{eb - 1}", DATE)
    fmt(ws, f"H{ea}:U{eb - 1}", "0.0000")

    s0 = eb + 3
    heading(ws, s0, "(3) The lines outside their promotion's scope (ScopeOK is FALSE), and the item master")
    header(ws, s0 + 1, 1, ["SalesOrderLineID", "PromotionID", "OrderDate", "ItemCode", "ItemName",
                           "CollectionName (Items)", "The promotion's collection"])
    sa = f"A{s0 + 2}"
    put(ws, {sa: ("=LET(k,OrderLines[ScopeOK]=FALSE,c,FILTER(OrderLines[CollectionName],k),SORT(HSTACK("
                  "FILTER(OrderLines[SalesOrderLineID],k),FILTER(OrderLines[PromotionID],k),FILTER(OrderLines[OrderDate],k),"
                  'FILTER(OrderLines[ItemCode],k),FILTER(OrderLines[ItemName],k),IF(c="","(blank)",c),'
                  "FILTER(OrderLines[PromoCollection],k))))")})
    no = len(f.oos)
    fmt(ws, f"C{s0 + 2}:C{s0 + 1 + no}", DATE)
    i0 = s0 + 3 + no
    put(ws, {f"A{i0}": "Items with no CollectionName in the item groups that have collections (Items)"})
    bold(ws, f"A{i0}")
    header(ws, i0 + 1, 1, ["ItemCode", "ItemName", "ItemGroup", "First word of the name", "It is a collection",
                           "Order lines"])
    ia = f"A{i0 + 2}"
    put(ws, {ia: ('=LET(g,UNIQUE(FILTER(Items[ItemGroup],Items[CollectionName]<>"")),'
                  'k,(Items[CollectionName]="")*ISNUMBER(XMATCH(Items[ItemGroup],g)),c,FILTER(Items[ItemCode],k),'
                  'n,FILTER(Items[ItemName],k),w,TEXTBEFORE(n," "),HSTACK(c,n,FILTER(Items[ItemGroup],k),w,'
                  "ISNUMBER(XMATCH(w,Items[CollectionName])),COUNTIFS(OrderLines[ItemCode],c)))")})
    ni = len(f.no_collection)

    a0 = i0 + 3 + ni
    heading(ws, a0, "(4) Who approved each promotion, and when (Promotions, Employees)")
    header(ws, a0 + 1, 1, ["PromotionID", "PromotionName", "Approved by", "Name", "Job title", "ApprovedDate",
                           "EffectiveStartDate", "Approved on the start date"])
    aa = f"A{a0 + 2}"
    put(ws, {aa: ("=LET(id,SORT(Promotions[PromotionID]),a,XLOOKUP(id,Promotions[PromotionID],"
                  "Promotions[ApprovedByEmployeeID]),d,XLOOKUP(id,Promotions[PromotionID],Promotions[ApprovedDate]),"
                  "s,XLOOKUP(id,Promotions[PromotionID],Promotions[EffectiveStartDate]),HSTACK(id,XLOOKUP(id,"
                  "Promotions[PromotionID],Promotions[PromotionName]),a,XLOOKUP(a,Employees[EmployeeID],"
                  "Employees[EmployeeName]),XLOOKUP(a,Employees[EmployeeID],Employees[JobTitle]),d,s,d=s))")})
    fmt(ws, f"F{a0 + 2}:G{a0 + 1 + n}", DATE)
    o0 = a0 + 3 + n
    heading(ws, o0, "Price override requests (Overrides)")
    who = f"--B{o0 + 1}"
    overrides = [
        ("EmployeeID who approved the promotions", '=TEXTJOIN(", ",TRUE,UNIQUE(Promotions[ApprovedByEmployeeID]))',
         "General"),
        ("Name and job title", f'=XLOOKUP({who},Employees[EmployeeID],Employees[EmployeeName])&", "&'
                               f"XLOOKUP({who},Employees[EmployeeID],Employees[JobTitle])", "General"),
        ("Override requests", "=ROWS(Overrides[PriceOverrideApprovalID])", COUNT),
        ("Approved", '=COUNTIF(Overrides[Status],"Approved")', COUNT),
        ("Approved by the same employee", f'=COUNTIFS(Overrides[Status],"Approved",Overrides[ApprovedByEmployeeID],{who})',
         COUNT),
        ("...of them, the employee's own requests",
         f'=COUNTIFS(Overrides[Status],"Approved",Overrides[ApprovedByEmployeeID],{who},'
         f"Overrides[RequestedByEmployeeID],{who})", COUNT),
        ("Pending", '=COUNTIF(Overrides[Status],"Pending")', COUNT),
        ("Pending request IDs", '=TEXTJOIN(", ",TRUE,FILTER(Overrides[PriceOverrideApprovalID],Overrides[Status]="Pending"))',
         "General"),
        ("Pending requests made by the same employee",
         f'=COUNTIFS(Overrides[Status],"Pending",Overrides[RequestedByEmployeeID],{who})', COUNT),
        ("Pending requests whose order line was billed anyway",
         '=SUM(--(COUNTIF(BilledLines[SalesOrderLineID],FILTER(Overrides[SalesOrderLineID],'
         'Overrides[Status]="Pending"))>0))', COUNT),
        ("Job titles of the other requesters",
         f'=TEXTJOIN(", ",TRUE,SORT(UNIQUE(FILTER(Overrides[RequesterTitle],Overrides[RequestedByEmployeeID]<>{who}))))',
         "General")]
    for i, (label, formula, number_format) in enumerate(overrides, start=1):
        put(ws, {f"A{o0 + i}": label, f"B{o0 + i}": formula})
        fmt(ws, f"B{o0 + i}", number_format)
    k0 = o0 + len(overrides) + 2
    heading(ws, k0, "Stacking: promotion lines priced from an approved override (OverrideStatus)")
    stacking = [("Order lines", '=COUNTIFS(OrderLines[PromotionID],"<>",OrderLines[OverrideStatus],"Approved")', COUNT),
                ("Billed lines", '=COUNTIFS(BilledLines[PromotionID],"<>",BilledLines[OverrideStatus],"Approved")', COUNT),
                ("Their promotional discount", ('=SUMIFS(BilledLines[DiscountAmount],BilledLines[PromotionID],"<>",'
                                                'BilledLines[OverrideStatus],"Approved")'), MONEY)]
    for i, (label, formula, number_format) in enumerate(stacking, start=1):
        put(ws, {f"A{k0 + i}": label, f"B{k0 + i}": formula})
        fmt(ws, f"B{k0 + i}", number_format)

    mgr = n5["mgr"]
    bad = [f.promos[pid] for pid in f.bad]
    bad_lines = sum(p["lines"] for p in bad)
    d0 = k0 + len(stacking) + 3
    heading(ws, d0, f"(5) Dispositions ({MA})")
    header(ws, d0 + 1, 1, ["Exception", "Count", "Disposition", "Design or operation", "Action"])
    disp = [
        (f"Promotions {series(f.bad)}: every line ordered outside the recorded dates", f"=F{tr}",
         "Master-data error, not discounts given without authority: the lines were ordered in March and April, every "
         "collection line of those months carries the promotion, and each year's budget planned the discount then.",
         "Design: the system accepts an end date on or before the start date",
         "Correct the end dates; reject a promotion whose end date is not after its start"),
        (f"Order lines {n5['oos_ids']} (promotion {n5['oos_promo']}) outside the scope", f"=G{tr}",
         f"The discount is right; the item master is incomplete: {n5['code']}, the {n5['base']}, has no CollectionName "
         f"({n5['others']} also lack one).",
         "Design: the scope is read from an incomplete item master",
         "Complete CollectionName; check scope data before a promotion runs"),
        ("Rates that differ from DiscountPct", f"=H{tr}", "None: every promotion line carries its promotion's rate.",
         "Operating as designed", "None"),
        ("Lines in scope and window without the promotion (completeness)", f"=K{tr}",
         "None: every line in a promotion's scope and months carries it (collection months taken as March and April).",
         "Operating as designed", "None"),
        (f"Promotions and approved overrides all approved by {mgr['name']}, {mgr['title']}", f"=B{o0 + 5}",
         f"{n5['own']} of the approved overrides were the manager's own requests; finance approves neither promotions "
         "nor overrides.",
         "Design (no finance approval) and operation (approvals by the person who requested them)",
         "Finance co-approves promotions; overrides approved by someone other than the requester"),
        (f"Pending override requests billed anyway (IDs {', '.join(str(i) for i in n5['pending_ids'])})",
         f"=B{o0 + 10}", "Billed at a price nobody approved; requested by the same manager.",
         "Operation (and design: billing does not check the approval)", "Block billing until a request is approved"),
        ("Promotion lines on top of an approved override (stacking)", f"=B{k0 + 1}",
         f"{n5['stack_billed']} billed lines, {money(n5['stack_disc'])} of discount: whether a negotiated price should "
         "also receive a promotion is a policy question for management.", "Design: no stacking rule",
         "Decide and enforce a stacking rule")]
    for i, row in enumerate(disp):
        r = d0 + 2 + i
        for j, v in enumerate(row):
            put(ws, {f"{col(1 + j)}{r}": v})
    dl = d0 + 1 + len(disp)
    ws.Range(f"A{d0 + 1}:E{dl}").WrapText = True
    ws.Range(f"A{d0 + 1}:E{dl}").VerticalAlignment = TOP
    fmt(ws, f"B{d0 + 2}:B{dl}", COUNT)
    widths(ws, {"A": 46, "B": 30, "C": 54, "D": 36, "E": 40})
    for k in range(6, 23):
        ws.Columns(k).ColumnWidth = 12
    for r in range(d0 + 2, dl + 1):
        ws.Rows(r).AutoFit()
    c0 = dl + 3
    text_block(ws, c0, f"{MA}, Requirement 5: the conditions to meet before any promotion runs in {f.N}", [
        "1. Validated dates: the system rejects a promotion whose end date is not after its start date, and the "
        "recorded dates match the months the promotion is meant to run.",
        "2. Complete scope data: every item of a collection carries its CollectionName before a collection promotion "
        "runs.",
        "3. Approval by finance as well as sales: the controller (or the chief financial officer) approves each "
        "promotion, its rate, its scope, and its expected effect, before its start date.",
        "4. Independent approval of overrides: nobody approves their own request, and billing waits for an approval.",
        "5. A stacking rule: management decides whether a negotiated override price can also receive a promotion.",
        "6. A post-promotion review: volume in the promotion's months is compared with a stated expectation, and the "
        "cost is reported in a gross-to-net schedule."], span=5)
    text_block(ws, c0 + 9, f"{MA}, Requirement 5 (findings)", [
        f"Dates. All {bad_lines} lines of promotions {series(f.bad)} ({series(p['label'] for p in bad)}) fail the date "
        f"test, and every line of the other {n5['good']} passes. Their recorded end dates fall on or before their start "
        "dates, yet all their lines were ordered from March 1 to April 30, every collection line ordered in those "
        "months carries the promotion, and each year's budget planned the collection's discount in March and April. "
        "The evidence points to a March-April window entered with a wrong end date: a master-data error, not discounts "
        "given without authority.",
        f"Scope. Two order lines of promotion {n5['oos_promo']} (SalesOrderLineIDs {n5['oos_ids']}) are on "
        f"{n5['code']}, the {n5['base']}, whose CollectionName is blank: the discount is right and the item master is "
        f"incomplete ({n5['others']} also lack a collection). Rate and completeness: no exceptions.",
        f"Approvals. {mgr['name']} ({mgr['title']}, EmployeeID {mgr['id']}) approved all {n5['promos']} promotions, each "
        f"on its start date, and all {n5['approved']} approved override requests, {n5['own']} of them her own. Her "
        f"{n5['pending']} other requests are still Pending, yet they were billed (Exercises 4.6 and 8.6); the other "
        f"requests came from {n5['requesters']}. Pricing authority sits with one person, and finance approves neither "
        f"promotions nor overrides. Stacking: {n5['stack_orders']} order lines ({n5['stack_billed']} billed lines) carry "
        f"both an approved override and a promotion, {money(n5['stack_disc'])} of discount."], span=5)
    b.found["r5"] = dict(tr=tr, ea=ea, eb=eb, sa=sa, ia=ia, aa=aa, o0=o0, k0=k0, d0=d0)

    t = R5
    for i, pid in enumerate(f.ids):
        r = 5 + i
        p = f.promos[pid]
        b.check(t, f"promotion {pid}: lines outside the recorded dates", p["lines"] - f.within[pid],
                f"='R5 Controls'!F{r}", 0, COUNT)
        b.check(t, f"promotion {pid}: lines outside the scope", f.scope_exc.get(pid, 0), f"='R5 Controls'!G{r}", 0, COUNT)
    b.check(t, "lines outside the recorded dates, all", sum(p["lines"] for p in bad), f"='R5 Controls'!F{tr}", 0, COUNT)
    b.check(t, "rates that differ from DiscountPct", f.rate_exc, f"='R5 Controls'!H{tr}", 0, COUNT)
    b.check(t, "in scope and window without the promotion (completeness)", 0, f"='R5 Controls'!K{tr}", 0, COUNT)
    b.check(t, "promotions whose recorded dates fail", nb, f"=ROWS('R5 Controls'!A{ea}#)", 0, COUNT)
    for i, p in enumerate(bad):
        b.check(t, f"promotion {p['id']}: first order", serial(p["lo"]), f"='R5 Controls'!F{ea + i}", 0, DATE)
        b.check(t, f"promotion {p['id']}: last order", serial(p["hi"]), f"='R5 Controls'!G{ea + i}", 0, DATE)
    b.check(t, "promotions whose end date is on or before the start date", f.end_not_after, f"='R5 Controls'!E{eb}", 0,
            COUNT)
    b.check(t, "failing promotions whose budget planned the discount in their order months", f.budget_planned,
            f"='R5 Controls'!V{eb + 1}", 0, COUNT)
    b.check(t, "lines outside the scope", len(f.oos), f"=ROWS('R5 Controls'!{sa}#)", 0, COUNT)
    b.check(t, "their SalesOrderLineIDs", ", ".join(str(r[0]) for r in f.oos),
            f"=TEXTJOIN(\", \",TRUE,INDEX('R5 Controls'!{sa}#,0,1))", 0, "General")
    b.check(t, "their item", n5["code"], f"=TEXTJOIN(\", \",TRUE,UNIQUE(INDEX('R5 Controls'!{sa}#,0,4)))", 0, "General")
    b.check(t, "its CollectionName in the item master", "(blank)",
            f"=TEXTJOIN(\", \",TRUE,UNIQUE(INDEX('R5 Controls'!{sa}#,0,6)))", 0, "General")
    b.check(t, "items with no collection in groups that have collections", ni, f"=ROWS('R5 Controls'!{ia}#)", 0, COUNT)
    b.check(t, "...whose name begins with a collection's name", f.named_for, f"=SUM(--INDEX('R5 Controls'!{ia}#,0,5))",
            0, COUNT)
    b.check(t, "promotions approved on their start date", n, f"=SUM(--INDEX('R5 Controls'!{aa}#,0,8))", 0, COUNT)
    b.check(t, "the promotions' approver (EmployeeID)", mgr["id"], f"=--'R5 Controls'!B{o0 + 1}", 0, COUNT)
    b.check(t, "...name and job title", f"{mgr['name']}, {mgr['title']}", f"='R5 Controls'!B{o0 + 2}", 0, "General")
    b.check(t, "override requests", f.overrides_total, f"='R5 Controls'!B{o0 + 3}", 0, COUNT)
    b.check(t, "approved override requests", n5["approved"], f"='R5 Controls'!B{o0 + 4}", 0, COUNT)
    b.check(t, "...approved by the promotions' approver", n5["approved"], f"='R5 Controls'!B{o0 + 5}", 0, COUNT)
    b.check(t, "...the approver's own requests", n5["own"], f"='R5 Controls'!B{o0 + 6}", 0, COUNT)
    b.check(t, "pending requests", n5["n_pending"], f"='R5 Controls'!B{o0 + 7}", 0, COUNT)
    b.check(t, "pending request IDs", ", ".join(str(i) for i in n5["pending_ids"]), f"='R5 Controls'!B{o0 + 8}", 0,
            "General")
    b.check(t, "pending requests made by the approver", f.pending_requested, f"='R5 Controls'!B{o0 + 9}", 0, COUNT)
    b.check(t, "pending requests billed anyway", f.pending_billed, f"='R5 Controls'!B{o0 + 10}", 0, COUNT)
    b.check(t, "job titles of the other requesters", f.requesters, f"='R5 Controls'!B{o0 + 11}", 0, "General")
    b.check(t, "stacking: order lines", n5["stack_orders"], f"='R5 Controls'!B{k0 + 1}", 0, COUNT)
    b.check(t, "stacking: billed lines", n5["stack_billed"], f"='R5 Controls'!B{k0 + 2}", 0, COUNT)
    b.check(t, "stacking: promotional discount", round(n5["stack_disc"], 2), f"='R5 Controls'!B{k0 + 3}")

    st = b.found["doc"]
    st["entries"]["Calculated columns"] += (
        " OrderLines (Requirement 5): DateOK, the order date within the promotion's recorded dates; ScopeOK, the item's "
        "collection or group, or the customer's segment, equal to the promotion's scope (SWITCH on ScopeType); RateOK, "
        "Discount equal to DiscountPct; OverrideStatus, the Status of the line's override request (XLOOKUP on "
        "Overrides). BilledLines: OverrideStatus.")
    st["sheets"]["R5 Controls"] = ("Requirement 5: the four tests by promotion, the evidence on the dates, the lines out "
                                   "of scope, approvals, overrides, stacking, dispositions, and conditions")
    write_doc(b)
    settle(b)


# --- Requirement 6 ------------------------------------------------------------------------------------------------------

def memo_text(f: Facts) -> list[str]:
    n2, n3, n4, n5 = f.n2, f.n3, f.n4, f.n5
    y, P, F, N = f.C, f.P, f.F, f.N
    years = n2["years"]
    top, low = n3["top"], n3["low"]
    grp = n4["grp"]
    bad = [f.promos[pid] for pid in f.bad]
    mgr = n5["mgr"]
    pq_ = f.prop_quarters
    disc_name = f.discount_accounts[0]

    def usd(x: float, places: int = 0) -> str:
        return "$" + money(x, places)
    return [
        "To: The Controller",
        "From: Staff Accountant",
        f"Date: January {N}",
        f"Subject: The proposed {N} promotion calendar",
        f"The sales team proposes to repeat the {y} promotion calendar in {N} at the same rates: the Harbor Collection "
        "Promotion (8 percent, March and April), the Furniture Seasonal Promotion (10 percent, September and October), "
        "and the Design Trade Customer Promotion (12 percent, November). This memo answers your four questions from "
        f"the order, invoice, ledger, and budget data of fiscal {F} to {y}. Exhibits 1 to 5 follow.",
        "FINANCIAL REPORTING",
        f"In three years, nine promotions gave customers {usd(n2['total'], 0)} of discounts on {n2['lines']:,} billed "
        f"lines, and the cost {n2['grew']}: {usd(years[0]['disc'], 0)} in {F} ({pct(years[0]['share'], 2)} of billed "
        f"revenue), {usd(years[1]['disc'], 0)} in {F + 1} ({pct(years[1]['share'], 2)}), and "
        f"{usd(years[2]['disc'], 0)} in {y} ({pct(years[2]['share'], 2)}) (Exhibit 1).",
        f"The ledger does not show this cost. Each invoice line is recorded at its net price, so the revenue accounts "
        f"already exclude every price reduction, and account {disc_name[0]} {disc_name[1]} has never been used. The "
        "income statement shows net revenue and nothing about the promotions. The cost is visible only in a gross-to-net "
        f"schedule (Exhibit 2): in {y}, list prices would have billed {usd(n2['list'], 0)}, price lists and approved "
        f"overrides took off {usd(n2['red'], 0)}, and the promotions {usd(n2['disc'], 0)}, leaving "
        f"{usd(n2['net'], 0)}. That amount ties to the sales-invoice revenue in the ledger, except "
        f"{usd(n2['difference'], 2)} of three invoices dated in late {P} and posted in {y} ({n2['first']} to "
        f"{n2['last']}), a cutoff matter already reported.",
        "A promotion applies by order date, but revenue follows the invoice date, so its discounts reach the quarterly "
        f"results late: of the {usd(n2['prop_total'], 0)} the three proposed promotions cost in {y}, "
        f"{usd(n2['q4'], 0)} ({pct(n2['q4_share'], 0)}) was billed in the fourth quarter.",
        "MANAGERIAL ACCOUNTING",
        "No promotion brought in sales that would not otherwise have been made. Measured at list price in each "
        "promotion's scope and months, against the other months of the same year and the same months a year earlier, "
        f"the differences run from {spct(low['lift'])} to {spct(top['lift'])}, all within the scope's normal "
        f"month-to-month variation (the largest is {top['z']:.1f} standard deviations; Exhibit 3). No customer's first "
        f"order in the data included a promotion line. First orders cluster in early {F} because the data begins then, "
        f"and only {n3['late']} came after June {F}, so the data cannot prove that promotions never attract customers, "
        "but it gives the claim no support.",
        f"To pay for itself, the proposed calendar would need {pct(n4['coll']['be'])} more volume for Harbor, "
        f"{pct(grp['be'])} for Furniture, and {pct(n4['seg']['be'])} for Design Trade; across all nine promotions the "
        f"break-even increases run from {pct(n4['be_low'], 0)} to {pct(n4['be_high'], 0)}, and no measured difference "
        "came close (Exhibit 4).",
        f"The {N} budget, approved by the chief financial officer, plans no promotions: it prices every month at about "
        f"{n4['flat']:.1%} of list, where the {F} to {y} budgets planned the promoted items at {n4['promoted']:.1%} in "
        f"their months. At {y} volumes, the calendar would cost about {usd(n4['cost'], 0)} of discounts, or "
        f"{usd(n4['contribution'], 0)} of contribution after commissions, against that budget: about "
        f"{usd(pq_[1], 0)} in the first quarter, {usd(pq_[2], 0)} in the second, {usd(pq_[3], 0)} in the third, "
        f"and {usd(pq_[4], 0)} in the fourth. I did not use the budget's quantities, which run several times actual "
        f"(it plans {n4['budget_units']:,.0f} Furniture units for September and October against {n4['ordered']:,.0f} "
        f"ordered in {y}), and the budget has no customer dimension to cost the Design Trade promotion.",
        f"An alternative worth testing: one promotion, in one scope, at a discount near {pct(f.goal_discount)}, the "
        f"rate at which the best increase ever measured ({spct(top['lift'])}) would pay for itself, compared with a "
        "similar scope or period and reviewed afterward.",
        "AUDITING",
        f"Extending the Exercise 8.6 tests to all {f.n1['promo_lines']:,} promotion lines (Exhibit 5): all "
        f"{sum(p['lines'] for p in bad)} lines of the collection promotions ({series(p['label'] for p in bad)}) fall "
        "outside their recorded dates, because the end dates were entered on or before the start dates. The lines were "
        "ordered in March and April, every collection line of those months carries the promotion, and each budget "
        "planned the discount then: a master-data error, to be corrected, not discounts without authority. Two lines "
        f"of the Alder promotion are on {n5['code']}, whose CollectionName is blank: the discount is right and the item "
        "master is incomplete. Rates and completeness show no exceptions.",
        f"{mgr['name']}, the {mgr['title'].lower()}, approved all nine promotions on their start dates and all "
        f"{n5['approved']} approved price overrides, {n5['own']} of them her own requests; her {n5['pending']} pending "
        f"requests were billed without approval. Finance approves neither. A promotion was also given on top of an "
        f"approved override on {n5['stack_orders']} order lines ({usd(n5['stack_disc'])} of discount), a policy "
        "question for management. The dates and scope data are design weaknesses; the self-approvals and the billing "
        "of pending requests are failures in operation.",
        f"Before any promotion runs in {N}: validated dates, complete collection data, approval by finance as well as "
        "sales, independent approval of overrides, a stacking rule, and a post-promotion review against a stated "
        "expectation.",
        "RECOMMENDATION",
        "Decline the calendar as proposed. It would cost about "
        f"{usd(round(n4['contribution'], -4))} of contribution against the {N} budget, most of it in the fourth "
        "quarter, for increases in volume the data has never shown. If the sales team wants evidence, approve one small, "
        f"measured test at a discount near {pct(f.goal_discount)}, and only after the control changes above are in "
        "place."]


def r6(b: ExerciseBuild) -> None:
    wb, f = b.wb, facts(b)
    ws = new_sheet(b, "Memo")
    ws.Columns("A").ColumnWidth = 120
    ws.Range("A1").Value = f"{MA}: the decision memorandum (Requirement 6)"
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 13
    paragraphs = memo_text(f)
    r = 3
    for p in paragraphs:
        cell = ws.Cells(r, 1)
        cell.Value = p
        cell.WrapText = True
        cell.VerticalAlignment = TOP
        if p.isupper():
            cell.Font.Bold = True
        r += 1
    for i in range(3, r):
        ws.Rows(i).AutoFit()
    end = r - 1
    words = sum(len(p.split()) for p in paragraphs)
    put(ws, {f"A{end + 2}": "Words in the memo (two pages hold about 1,000)",
             f"B{end + 2}": (f'=SUMPRODUCT((LEN(TRIM(A3:A{end}))>0)*(LEN(TRIM(A3:A{end}))-'
                             f'LEN(SUBSTITUTE(TRIM(A3:A{end})," ",""))+1))')})
    ws.Columns("B").ColumnWidth = 14
    for c in range(3, 9):
        ws.Columns(c).ColumnWidth = 16

    R = r3_rows(len(f.ids))
    r2_, r4_, r5_ = b.found["r2"], b.found["r4"], b.found["r5"]
    x = end + 5
    ws.Cells(x - 1, 1).Value = "Appendix: exhibits (live links to the analysis worksheets)"
    ws.Cells(x - 1, 1).Font.Bold = True
    exhibits = [
        ("Exhibit 1. Promotional discount by fiscal year (R2 Cost)", ["Year", "Discount", "Lines", "Billed revenue",
                                                                     "% of revenue"],
         f"='R2 Cost'!A{r2_['s0']}:E{r2_['tr']}", 4, [(2, MONEY), (3, COUNT), (4, MONEY), (5, PCT)]),
        ("Exhibit 2. Gross to net, report year (R2 Gross to Net)", ["Item group", "List", "Price lists and overrides",
                                                                  "Promotions", "Net billed"],
         "='R2 Gross to Net'!A5:E10", 6, [(2, MONEY), (3, MONEY), (4, MONEY), (5, MONEY)]),
        ("Exhibit 3. Volume in each promotion's months (R3 Volume)", ["PromotionID", "Scope",
                                                                     "Against the other months",
                                                                     "Against a year earlier",
                                                                     "Standard deviations"],
         f"=CHOOSECOLS('R3 Volume'!A{R['k']}:K{R['k'] + len(f.ids) - 1},1,2,6,8,11)", len(f.ids),
         [(3, "+0.0%;-0.0%"), (4, "+0.0%;-0.0%"), (5, "+0.00;-0.00")]),
        ("Exhibit 4. Break-even increase and measured difference (R4 Model)", ["PromotionID", "Scope", "Rate",
                                                                               "Break-even lift",
                                                                               "Measured difference"],
         f"=CHOOSECOLS('R4 Model'!A24:H{r4_['e9'] - 1},1,2,3,7,8)", len(f.ids),
         [(3, "0%"), (4, PCT), (5, "+0.0%;-0.0%")]),
        ("Exhibit 5. Exceptions and dispositions (R5 Controls)", ["Exception", "Count", "Disposition"],
         f"=CHOOSECOLS('R5 Controls'!A{r5_['d0'] + 2}:E{r5_['d0'] + 8},1,2,3)", 7, [(2, COUNT)])]
    anchors = {}
    for label, heads, formula, rows, formats in exhibits:
        ws.Cells(x, 1).Value = label
        ws.Cells(x, 1).Font.Bold = True
        header(ws, x + 1, 2, heads)
        ws.Range(f"B{x + 2}").Formula2 = formula
        for c, number_format in formats:
            fmt(ws, f"{col(1 + c)}{x + 2}:{col(1 + c)}{x + 1 + rows}", number_format)
        anchors[label[:10]] = x + 2
        x += rows + 4
    ws.Range(f"B{anchors['Exhibit 5.'] }:D{anchors['Exhibit 5.'] + 6}").WrapText = True

    t = R6
    b.check(t, "the memo fits two pages (words, at most 1,000)", words, f"=Memo!B{end + 2}", 0, COUNT)
    b.check(t, "the memo's words are at most 1,000", True, f"=Memo!B{end + 2}<=1000", 0, "General")
    e1, e2 = anchors["Exhibit 1."], anchors["Exhibit 2."]
    b.check(t, "Exhibit 1: total promotional discount", f.n2["total"], f"=Memo!C{e1 + 3}")
    b.check(t, "Exhibit 2: net billed in the report year", round(f.n2["net"], 2), f"=Memo!F{e2 + 5}")
    b.check(t, "Exhibit 3: largest difference", f.n3["top"]["lift"], f"=MAX(Memo!D{anchors['Exhibit 3.']}:D"
                                                                        f"{anchors['Exhibit 3.'] + len(f.ids) - 1})",
            1e-9, "0.0000%")
    b.check(t, "Exhibit 4: highest break-even", f.n4["be_high"], f"=MAX(Memo!E{anchors['Exhibit 4.']}:E"
                                                                 f"{anchors['Exhibit 4.'] + len(f.ids) - 1})",
            1e-9, "0.0000%")
    b.check(t, "Exhibit 5: lines outside the recorded dates", sum(f.promos[p]["lines"] for p in f.bad),
            f"=Memo!C{anchors['Exhibit 5.']}", 0, COUNT)

    st = b.found["doc"]
    st["sheets"]["Memo"] = "Requirement 6: the decision memorandum (model answer) and its exhibits"
    st["extra"] = [["Recommendation",
                    f"Decline the calendar as proposed: no promotion came near its break-even increase, and the three "
                    f"would cost about {money(round(f.n4['contribution'], -4), 0)} of contribution against the {f.N} "
                    f"budget, most of it in the fourth quarter. A small, measured test at a discount near "
                    f"{pct(f.goal_discount)} is worth considering, and only after the control changes of "
                    "Requirement 5."]]
    write_doc(b)
    doc = wb.Worksheets("Documentation")
    doc.Activate()
    doc.Range("A1").Select()
    settle(b)


EXERCISES = [(R1, r1), (R2, r2), (R3, r3), (R4, r4), (R5, r5), (R6, r6)]
