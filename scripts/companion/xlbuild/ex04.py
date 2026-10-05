"""Chapter 4 Exercises - Solutions.xlsx: the solutions to the exercises of Chapter 4.

build.py --solutions --chapter 4 copies the verified workbook at the end of Tutorial 4.3 (the "copy of your analysis
workbook" the exercises start from) and applies one function per exercise, in book order. Each function adds the
exercise's worksheets, queries, calculated columns, names, validation, conditional formatting, and slicers as the
requirements describe them, writes a model answer where a requirement asks for a written explanation, and adds its
checks: every result the instructor note states, as a live formula against the value CharlesRiver.sqlite gives
(read-only), computed here with SQL and independently of Excel.

Exercises 4.5 and 4.6 ask for a new workbook. Their solutions live in this file on worksheets of their own, and the
names they would have in a new workbook (a Shipment query, Parameters and Analysis worksheets) are prefixed or changed
where this file already uses them; a cell note on each solution says so. The tutorial queries are never edited.

Where a requirement has the reader click a slicer and read SUBTOTAL, the builder selects each slicer button in turn,
records what SUBTOTAL shows as values (as the reader would note them), and clears the slicer; a cell note says so, and
a live formula beside each recorded value gives the same result without the slicer.
"""

from __future__ import annotations

import math
import sqlite3
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path

import pythoncom

from xlbuild import pq, xl
from xlbuild.expected import xround
from xlbuild.notes import NOTES_SHEET
from xlbuild.solutions import COUNT, MONEY, PCT, ExerciseBuild

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import db_uri  # noqa: E402

XL_VALIDATE_DECIMAL, XL_VALIDATE_LIST, XL_VALIDATE_DATE = 2, 3, 4
XL_BETWEEN, XL_GREATER_EQUAL = 1, 7
XL_FILL_DEFAULT = 0
TOP = -4160
DATEF = "yyyy-mm-dd"
AMBER = xl.LIGHT_FILL            # #FEF2E7 as BGR
CORAL = 0xECEDFD                 # #FDEDEC as BGR
BLUE_TINT = 0xF8F2EA             # #EAF2F8 as BGR
TEXT = "General"


# --- the expected values, from CharlesRiver.sqlite (read-only) --------------------------------------------------------

@lru_cache(maxsize=None)
def facts() -> dict:
    con = sqlite3.connect(db_uri(), uri=True)
    q = lambda sql, *a: con.execute(sql, a).fetchall()           # noqa: E731
    one = lambda sql, *a: con.execute(sql, a).fetchone()[0]      # noqa: E731
    out = {}

    # Exercise 4.1: billing by fiscal year (InvoiceDate), and the credit memos the schedule leaves out
    years = [int(y) for (y,) in q("SELECT DISTINCT substr(InvoiceDate, 1, 4) FROM SalesInvoice ORDER BY 1")]
    by_year = {int(y): dict(n=n, sub=s, frt=f, tax=t, gt=g) for y, n, s, f, t, g in q(
        "SELECT substr(InvoiceDate, 1, 4), COUNT(*), SUM(SubTotal), SUM(FreightAmount), SUM(TaxAmount), "
        "SUM(GrandTotal) FROM SalesInvoice GROUP BY 1")}
    n, s, f, t, g = q("SELECT COUNT(*), SUM(SubTotal), SUM(FreightAmount), SUM(TaxAmount), SUM(GrandTotal) "
                      "FROM SalesInvoice")[0]
    memos = {int(y): dict(n=c, sub=v) for y, c, v in q(
        "SELECT substr(CreditMemoDate, 1, 4), COUNT(*), SUM(SubTotal) FROM CreditMemo GROUP BY 1")}
    out["ex1"] = dict(years=years, by_year=by_year, total=dict(n=n, sub=s, frt=f, tax=t, gt=g), memos=memos,
                      unbalanced=one("SELECT COUNT(*) FROM SalesInvoice "
                                     "WHERE ABS(SubTotal + FreightAmount + TaxAmount - GrandTotal) > 0.005"))

    # Exercise 4.2: invoice lines and discount dollars by promotion (DiscountAmount rounded per line, as Excel's ROUND)
    programs = [dict(id=r[0], code=r[1], name=r[2], scope=r[3], segment=r[4], group=r[5], collection=r[6], pct=r[7],
                     start=r[8], end=r[9]) for r in q(
        "SELECT PromotionID, PromotionCode, PromotionName, ScopeType, CustomerSegment, ItemGroup, CollectionName, "
        "DiscountPct, EffectiveStartDate, EffectiveEndDate FROM PromotionProgram ORDER BY PromotionID")]
    lines = q("SELECT PromotionID, Quantity, UnitPrice, Discount, LineTotal FROM SalesInvoiceLine "
              "WHERE PromotionID IS NOT NULL")
    for p in programs:
        mine = [r for r in lines if r[0] == p["id"]]
        p.update(lines=len(mine), total=sum(r[4] for r in mine), discount=sum(xround(r[1] * r[2] * r[3]) for r in mine),
                 other_rate=sum(1 for r in mine if abs(r[3] - p["pct"]) > 1e-9))
    disc_all = sum(p["discount"] for p in programs)
    out["ex2"] = dict(
        programs=programs, lines=len(lines), total=sum(p["total"] for p in programs), discount=disc_all,
        top=max(programs, key=lambda p: p["discount"]),
        second=sorted(programs, key=lambda p: -p["discount"])[1],
        no_promo_discount=one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE Discount <> 0 AND PromotionID IS NULL"),
        orphans=one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL AND PromotionID NOT IN "
                    "(SELECT PromotionID FROM PromotionProgram)"),
        backwards=[p["id"] for p in programs if p["end"] < p["start"]],
        single=[p["id"] for p in programs if p["end"] == p["start"]])

    # Exercise 4.3: list-price margins of the items with a list price (the Item Table of Tutorial 4.1)
    items = [dict(id=r[0], code=r[1], group=r[2], type=r[3], cost=r[4], list=r[5]) for r in q(
        "SELECT ItemID, ItemCode, ItemGroup, ItemType, StandardCost, ListPrice FROM Item WHERE ListPrice IS NOT NULL")]
    for i in items:
        i["margin"] = i["list"] - i["cost"]
        i["pct"] = i["margin"] / i["list"]
    goods = [i for i in items if i["type"] == "Finished Good"]
    groups = {}
    for name in sorted({i["group"] for i in goods}):
        mine = [i for i in goods if i["group"] == name]
        groups[name] = dict(n=len(mine), margin=sum(i["margin"] for i in mine) / len(mine),
                            pct=sum(i["pct"] for i in mine) / len(mine), below=sum(1 for i in mine if i["pct"] < 0.45))
    ordered = sorted(items, key=lambda i: (i["group"], -i["pct"]))
    services = [i for i in items if i["type"] != "Finished Good"]
    out["ex3"] = dict(items=len(items), goods=len(goods), groups=groups, services=services,
                      low=min(i["pct"] for i in goods), high=max(i["pct"] for i in goods),
                      below=sum(1 for i in goods if i["pct"] < 0.45), below30=sum(1 for i in goods if i["pct"] < 0.30),
                      first=ordered[0]["code"], first_unique=ordered[0]["pct"] != ordered[1]["pct"])

    # Exercise 4.4: freight billed against freight paid, by the sales order's FreightTerms
    rows = q("SELECT o.FreightTerms, s.FreightCost, s.BillableFreightAmount FROM Shipment s "
             "LEFT JOIN SalesOrder o ON o.SalesOrderID = s.SalesOrderID")
    terms = {}
    for term in sorted({r[0] for r in rows}):
        mine = [r for r in rows if r[0] == term]
        terms[term] = dict(n=len(mine), cost=sum(r[1] for r in mine), billed=sum(r[2] for r in mine),
                           margin=sum(r[2] - r[1] for r in mine), avg_cost=sum(r[1] for r in mine) / len(mine),
                           above=sum(1 for r in mine if r[2] - r[1] > 0), below=sum(1 for r in mine if r[2] - r[1] < 0),
                           equal=sum(1 for r in mine if r[2] - r[1] == 0), billing=sum(1 for r in mine if r[2] > 0),
                           ratio=sum(r[2] / r[1] for r in mine) / len(mine))
        terms[term]["recovered"] = terms[term]["billed"] / terms[term]["cost"]
    negative = [r[2] - r[1] for r in rows if r[2] - r[1] < 0]
    out["ex4"] = dict(n=len(rows), terms=terms, margin=sum(r[2] - r[1] for r in rows), cost=sum(r[1] for r in rows),
                      billed=sum(r[2] for r in rows), negative=len(negative), negative_total=sum(negative),
                      low=min(r[1] for r in rows), high=max(r[1] for r in rows),
                      unmatched=sum(1 for r in rows if r[0] is None))

    # Exercise 4.5: shipment exceptions at the review date
    review, review2 = f"{years[-1]}-12-31", f"{years[-1]}-12-01"
    blank = "(TrackingNumber IS NULL OR TrackingNumber = '')"
    status = dict(q("SELECT Status, COUNT(*) FROM Shipment GROUP BY 1"))
    out["ex5"] = dict(
        n=one("SELECT COUNT(*) FROM Shipment"), status=status, review=review, review2=review2,
        blank=one(f"SELECT COUNT(*) FROM Shipment WHERE {blank}"),
        blank_by=dict(q(f"SELECT Status, COUNT(*) FROM Shipment WHERE {blank} GROUP BY 1")),
        transit_by_year={int(y): c for y, c in q("SELECT substr(ShipmentDate, 1, 4), COUNT(*) FROM Shipment "
                                                 "WHERE Status = 'In Transit' GROUP BY 1")},
        late=one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", review),
        late2=one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", review2),
        due_on_or_after=one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate >= ?", review),
        both=one(f"SELECT COUNT(*) FROM Shipment WHERE {blank} AND Status = 'In Transit' AND DeliveryDate < ?", review),
        blank_dates=one("SELECT COUNT(*) FROM Shipment WHERE ShipmentDate IS NULL OR ShipmentDate = '' "
                        "OR DeliveryDate IS NULL OR DeliveryDate = ''"),
        first_late=one("SELECT MIN(ShipmentDate) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", review))

    # Exercise 4.6: price override approvals
    req = [dict(id=r[0], line=r[1], by=r[2], appr=r[3], status=r[4], ref=r[5], price=r[6]) for r in q(
        "SELECT PriceOverrideApprovalID, SalesOrderLineID, RequestedByEmployeeID, ApprovedByEmployeeID, Status, "
        "ReferenceUnitPrice, ApprovedUnitPrice FROM PriceOverrideApproval ORDER BY PriceOverrideApprovalID")]
    for r in req:
        r["disc"] = 1 - r["price"] / r["ref"]
    names = {e: (n_, t_) for e, n_, t_ in q("SELECT EmployeeID, EmployeeName, JobTitle FROM Employee")}
    requesters = sorted({r["by"] for r in req})
    pending = [r for r in req if r["status"] == "Pending"]
    for r in pending:
        billed = q("SELECT UnitPrice, PricingMethod FROM SalesInvoiceLine WHERE SalesOrderLineID = ?", r["line"])
        r.update(invoiced=len(billed), at_price=sum(1 for u, _ in billed if abs(u - r["price"]) < 0.005),
                 method=billed[0][1] if billed else None, methods={m for _, m in billed})
    by_disc = sorted(req, key=lambda r: -r["disc"])
    out["ex6"] = dict(
        n=len(req), status={s: sum(1 for r in req if r["status"] == s) for s in sorted({r["status"] for r in req})},
        approvers=sorted({r["appr"] for r in req if r["appr"] is not None}), names=names,
        grid=[dict(id=e, name=names[e][0], title=names[e][1], n=sum(1 for r in req if r["by"] == e),
                   other=sum(1 for r in req if r["by"] == e and r["appr"] is not None and r["appr"] != e),
                   own=sum(1 for r in req if r["by"] == e and r["appr"] == e),
                   open=sum(1 for r in req if r["by"] == e and r["appr"] is None)) for e in requesters],
        blank=sum(1 for r in req if r["appr"] is None), self=sum(1 for r in req if r["appr"] == r["by"]),
        blank_by={s: sum(1 for r in req if r["appr"] is None and r["status"] == s) for s in ("Approved", "Pending")},
        self_by={s: sum(1 for r in req if r["appr"] == r["by"] and r["status"] == s) for s in ("Approved", "Pending")},
        pending=pending, low=min(r["disc"] for r in req), high=max(r["disc"] for r in req),
        top=by_disc[0], top_unique=by_disc[0]["disc"] != by_disc[1]["disc"])
    con.close()
    return out


# --- small helpers -----------------------------------------------------------------------------------------------

def letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def col(lo, name: str) -> str:
    """The worksheet column letter of a Table column."""
    return letter(lo.ListColumns(name).Range.Column)


def serial(iso: str) -> int:
    return (date.fromisoformat(iso) - date(1899, 12, 30)).days


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d:%B} {d.day}, {d.year}"


WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def money(x: float) -> str:
    return f"{x:,.2f}"


def pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


def and_join(items) -> str:
    items = [str(i) for i in items]
    return " and ".join(items) if len(items) <= 2 else ", ".join(items[:-1]) + ", and " + items[-1]


def values(ws, cells: dict) -> None:
    for addr, v in cells.items():
        ws.Range(addr).Value = v


def formulas(ws, cells: dict) -> None:
    for addr, f in cells.items():
        ws.Range(addr).Formula2 = f


def new_sheet(b: ExerciseBuild, name: str, after=None):
    """A worksheet before the Solution Notes (or right after a given one)."""
    if after is not None:
        return xl.sheet(b.wb, name, after=after)
    return xl.sheet(b.wb, name, before=b.wb.Worksheets(NOTES_SHEET))


def heading(ws, cell: str, text: str, size: int = 12) -> None:
    ws.Range(cell).Value = text
    ws.Range(cell).Font.Bold = True
    ws.Range(cell).Font.Size = size


def bold(ws, rng: str) -> None:
    ws.Range(rng).Font.Bold = True


def put_date(cell, iso: str) -> None:
    """A typed date, as a reader enters it (Excel stores the serial number)."""
    cell.NumberFormat = DATEF
    cell.Formula = iso
    assert cell.Value2 == serial(iso), f"{iso} was not stored as a date ({cell.Value2!r})"


def validate(cell, kind: int, operator: int | None = None, f1: str | None = None, f2: str | None = None,
             title: str = "", message: str = "", error: str = "") -> None:
    v = cell.Validation
    v.Delete()
    # Operator is always passed: late-bound Validation.Add with named arguments fails without it, even for a List
    # rule, which ignores it (as the macro recorder writes it: Operator:=xlBetween)
    args = dict(Type=kind, AlertStyle=xl.XL_VALID_ALERT_STOP, Operator=XL_BETWEEN if operator is None else operator)
    if f1 is not None:
        args["Formula1"] = f1
    if f2 is not None:
        args["Formula2"] = f2
    v.Add(**args)
    if title:
        v.InputTitle = title
        v.ErrorTitle = title
    if message:
        v.InputMessage = message
        v.ShowInput = True
    if error:
        v.ErrorMessage = error
    v.ShowError = True


def ready(obj) -> None:
    """Wait until Excel has finished what the last call started (a filter, a sort, a recalculation)."""
    xl.wait_ready(obj.Application)


def row_rule(ws, rng, formula: str, color: int):
    """A formula-based conditional formatting rule, read relative to the top-left cell of the range."""
    ready(ws)
    xl.retry(ws.Activate)
    xl.retry(rng.Cells(1, 1).Select)            # COM reads a relative rule formula from the active cell
    rule = xl.retry(rng.FormatConditions.Add, xl.XL_EXPRESSION, 1, formula)
    rule.Interior.Color = color
    ready(ws)
    return rule


def add_column(lo, name: str, formula: str, number_format: str | None = None):
    """xl.add_column with each step retried against a busy Excel (a retry of the whole would add a second column)."""
    ready(lo)
    column = xl.retry(lo.ListColumns.Add)
    xl.retry(lambda: setattr(column, "Name", name))
    xl.retry(lambda: setattr(column.DataBodyRange, "Formula2", formula))
    if number_format:
        xl.retry(lambda: setattr(column.DataBodyRange, "NumberFormat", number_format))
    ready(lo)
    return column


def sort_table(lo, keys: list[tuple[str, int]]) -> None:
    ready(lo)
    s = lo.Sort
    s.SortFields.Clear()
    for name, order in keys:
        s.SortFields.Add(Key=lo.ListColumns(name).Range, SortOn=0, Order=order)
    s.Header = xl.XL_YES
    xl.retry(s.Apply)
    ready(lo)


def load(b: ExerciseBuild, query: str, sheet_name: str, after):
    """Load a query as a Table on a new worksheet placed after `after` (Close & Load)."""
    xl.wait_ready(b.wb.Application)
    lo = xl.load_query(b.wb, query, sheet_name, after=after)
    xl.wait_ready(b.wb.Application)
    return lo


def nav(b: ExerciseBuild, number: int, table: str, corrections: dict | None = None, extra=()) -> str:
    return pq.navigator_query(b.src, number, table, list(pq.detected_types(b.xlsx, table)), corrections, list(extra))


def note(ws, cell: str, text: str) -> None:
    rng = ws.Range(cell)
    if rng.Comment is not None:
        rng.Comment.Delete()
    rng.AddComment(text)


def answer(ws, row: int, label: str, paragraphs: list[str], first: str = "B", last: str = "H") -> int:
    """A model answer: a bold label in column A and each paragraph in a merged, wrapped row. Returns the next row."""
    ws.Cells(row, 1).Value = label
    ws.Cells(row, 1).Font.Bold = True
    ws.Cells(row, 1).VerticalAlignment = TOP
    width = sum(ws.Columns(letter(c)).ColumnWidth for c in range(ord(first) - 64, ord(last) - 63))
    for text in paragraphs:
        assert not text[:1] in "=+-@", text
        rng = ws.Range(f"{first}{row}:{last}{row}")
        rng.Merge()
        rng.WrapText = True
        rng.VerticalAlignment = TOP
        rng.Cells(1, 1).Value = text
        lines = math.ceil(len(text) / (width * 1.05)) + (1 if len(text) > width else 0)
        ws.Rows(row).RowHeight = min(409, max(15, 15 * lines))
        row += 1
    return row + 1


def add_slicer(b: ExerciseBuild, lo, column: str, ws, name: str, cell: str, height: float = 110):
    ready(ws)
    cache = xl.retry(b.wb.SlicerCaches.Add2, lo, column)
    # late-bound Slicers.Add ignores its named arguments (the slicer lands at Excel's default place, with a default
    # name), so the name, caption, and position are set on the slicer afterwards
    slicer = xl.retry(cache.Slicers.Add, ws)
    for attr, value in (("Name", name), ("Caption", column), ("Top", ws.Range(cell).Top + 2),
                        ("Left", ws.Range(cell).Left + 3), ("Width", 150), ("Height", height)):
        xl.retry(lambda a=attr, v=value: setattr(slicer, a, v))     # Top and Left inside the cell: Excel rounds to pixels
    ready(ws)
    assert slicer.Shape.TopLeftCell.GetAddress(False, False) == cell, slicer.Shape.TopLeftCell.GetAddress(False, False)
    return cache


def record_with_slicer(b: ExerciseBuild, cache, lo, column: str, items: list[str], ws, cells: list[str]) -> dict:
    """Select each slicer button in turn, read the SUBTOTAL cells, and clear the slicer. Returns item -> values.
    Every call waits for Excel to finish filtering and recalculating the Table before the next one."""
    app = b.wb.Application
    out = {}
    for name in items:
        try:
            buttons = xl.retry(lambda: [(it, it.Name) for it in cache.SlicerItems])
            target = [it for it, n in buttons if n == name]
            assert target, f"no slicer button {name}"
            xl.retry(lambda: setattr(target[0], "Selected", True))
            ready(ws)
            for it, n in buttons:
                if n != name:
                    xl.retry(lambda it=it: setattr(it, "Selected", False))
                    ready(ws)
        except pythoncom.com_error as exc:          # a Table slicer filters through the Table's AutoFilter
            if exc.hresult in xl.BUSY:
                raise
            print(f"  slicer buttons not selectable; filtering {column} = {name} with the Table's AutoFilter")
            xl.retry(lo.Range.AutoFilter, lo.ListColumns(column).Index, f"={name}")
            ready(ws)
        xl.retry(app.Calculate)
        ready(ws)
        out[name] = [xl.retry(lambda c=c: ws.Range(c).Value) for c in cells]
        xl.retry(cache.ClearManualFilter)
        ready(ws)
        if xl.retry(lambda: lo.AutoFilter is not None and lo.AutoFilter.FilterMode):
            xl.retry(lo.AutoFilter.ShowAllData)
            ready(ws)
    xl.retry(app.Calculate)
    ready(ws)
    return out


def settle(b: ExerciseBuild, quiet: float = 3.0, timeout: float = 600.0) -> None:
    """Recalculate and wait until Excel has stayed ready for a few seconds, so that the calls build.py makes next (the
    Solution Notes, CalculateFull, reading the checks) do not meet an Excel still busy with this exercise's work."""
    import time
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


def widths(ws, spec: dict[str, float]) -> None:
    for cols, w in spec.items():
        ws.Columns(cols).ColumnWidth = w


# --- Exercise 4.1 ------------------------------------------------------------------------------------------------

def ex4_1(b: ExerciseBuild) -> None:
    fx = facts()["ex1"]
    years, by_year, tot = fx["years"], fx["by_year"], fx["total"]
    first, c = years[0], b.year
    assert years[-1] == c, (years, c)
    ws = new_sheet(b, "Ex 4.1")
    heading(ws, "A1", "Exercise 4.1: A Billing Schedule by Fiscal Year", 14)
    widths(ws, {"A": 50, "B:E": 17, "F": 3, "G": 12, "H": 12})

    # (2) the period parameters, validated as dates within the data's fiscal years
    values(ws, {"A3": "Parameter", "B3": "Value", "C3": "Description",
                "A4": "PeriodStart", "C4": f"First day of the period (a date from {first}-01-01 to {c}-12-31)",
                "A5": "PeriodEnd", "C5": f"Last day of the period; fiscal {c} is the calendar year {c}"})
    bold(ws, "A3:C3")
    put_date(ws.Range("B4"), f"{c}-01-01")
    put_date(ws.Range("B5"), f"{c}-12-31")
    ws.Range("B4:B5").Font.Color = xl.BLUE
    xl.name_cell(b.wb, "PeriodStart", "'Ex 4.1'!$B$4")
    xl.name_cell(b.wb, "PeriodEnd", "'Ex 4.1'!$B$5")
    for addr, which in (("B4", "PeriodStart"), ("B5", "PeriodEnd")):
        validate(ws.Range(addr), XL_VALIDATE_DATE, XL_BETWEEN, f"=DATE({first},1,1)", f"=DATE({c},12,31)",
                 title=which, message=f"Enter a date from January 1, {first}, to December 31, {c}.",
                 error=f"{which} must be a date from January 1, {first}, to December 31, {c}.")

    # (3) the period's billing with COUNTIFS and SUMIFS on the named cells
    period = 'SalesInvoice[InvoiceDate],">="&PeriodStart,SalesInvoice[InvoiceDate],"<="&PeriodEnd'
    heading(ws, "A7", "Billing for the period (PeriodStart to PeriodEnd)", 11)
    measures = ["SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"]
    values(ws, {"A8": "Invoices"})
    formulas(ws, {"B8": f"=COUNTIFS({period})"})
    for i, m in enumerate(measures):
        values(ws, {f"A{9 + i}": m})
        formulas(ws, {f"B{9 + i}": f"=SUMIFS(SalesInvoice[{m}],{period})"})
    values(ws, {"A13": "SubTotal + FreightAmount + TaxAmount - GrandTotal",
                "A14": "Invoices (whole Table) whose parts do not add up to GrandTotal"})
    formulas(ws, {"B13": "=ROUND(B9+B10+B11-B12,2)",
                  "B14": "=SUMPRODUCT(--(ABS(SalesInvoice[SubTotal]+SalesInvoice[FreightAmount]+SalesInvoice[TaxAmount]"
                         "-SalesInvoice[GrandTotal])>0.005))"})
    ws.Range("B8").NumberFormat = COUNT
    ws.Range("B9:B13").NumberFormat = MONEY
    ws.Range("B14").NumberFormat = COUNT

    # (4) the grid: one SUMIFS with mixed references, entered in B18 and filled right and down
    heading(ws, "A16", "Billing by fiscal year", 11)
    values(ws, {"A17": "Fiscal year", "G17": "Invoices"})
    for j, m in enumerate(measures):
        ws.Cells(17, 2 + j).Value = m
    bold(ws, "A17:G17")
    rows = list(range(18, 18 + len(years)))
    for r, y in zip(rows, years):
        ws.Range(f"A{r}").Value = y
        ws.Range(f"A{r}").HorizontalAlignment = -4131
    last = rows[-1]
    tmpl = ('=SUMIFS(SalesInvoice[{m}],SalesInvoice[[InvoiceDate]:[InvoiceDate]],">="&DATE($A{r},1,1),'
            'SalesInvoice[[InvoiceDate]:[InvoiceDate]],"<="&DATE($A{r},12,31))')
    ws.Range("B18").Formula2 = tmpl.format(m="SubTotal", r=18)
    filled = False
    try:
        ws.Range("B18").AutoFill(ws.Range("B18:E18"), XL_FILL_DEFAULT)
        ws.Range("B18:E18").AutoFill(ws.Range(f"B18:E{last}"), XL_FILL_DEFAULT)
        filled = all(ws.Range(f"{letter(2 + j)}{r}").Formula2 == tmpl.format(m=m, r=r)
                     for j, m in enumerate(measures) for r in rows)
    except pythoncom.com_error:
        pass
    if not filled:                               # the end state of the fill, written cell by cell
        print("  Ex 4.1: AutoFill did not shift the sum column as the text says; writing the filled formulas")
        for j, m in enumerate(measures):
            for r in rows:
                ws.Range(f"{letter(2 + j)}{r}").Formula2 = tmpl.format(m=m, r=r)
    else:
        print("  Ex 4.1: filling right shifted SalesInvoice[SubTotal] to FreightAmount, TaxAmount, GrandTotal")
    note(ws, "B18", "One formula, entered here and filled right and down (the fill handle). Filling across shifts the "
                    "plain reference SalesInvoice[SubTotal] to the next column of the Table, so the grid's columns "
                    "follow the Table's: FreightAmount, TaxAmount, GrandTotal. InvoiceDate is locked with "
                    "[[InvoiceDate]:[InvoiceDate]] so it does not shift, and $A18 keeps each row on its year while "
                    "DATE builds the year's first and last day. Copying and pasting instead leaves every reference as "
                    "it is, so each column's sum column must then be changed by hand.")
    for r in rows:
        ws.Range(f"G{r}").Formula2 = (f'=COUNTIFS(SalesInvoice[InvoiceDate],">="&DATE($A{r},1,1),'
                                      f'SalesInvoice[InvoiceDate],"<="&DATE($A{r},12,31))')
    tr, er, dr = last + 1, last + 2, last + 3
    values(ws, {f"A{tr}": "Total", f"A{er}": "Entire SalesInvoice Table", f"A{dr}": "Difference"})
    for j, m in enumerate(measures):
        cl = letter(2 + j)
        formulas(ws, {f"{cl}{tr}": f"=SUM({cl}18:{cl}{last})", f"{cl}{er}": f"=SUM(SalesInvoice[{m}])",
                      f"{cl}{dr}": f"=ROUND({cl}{tr}-{cl}{er},2)"})
    formulas(ws, {f"G{tr}": f"=SUM(G18:G{last})", f"G{er}": "=ROWS(SalesInvoice[SalesInvoiceID])",
                  f"G{dr}": f"=G{tr}-G{er}"})
    bold(ws, f"A{tr}:G{tr}")
    ws.Range(f"B18:E{dr}").NumberFormat = MONEY
    ws.Range(f"G18:G{dr}").NumberFormat = COUNT
    note(ws, "G17", "Not part of the grid the exercise asks for: the number of invoices of each fiscal year, with "
                    "COUNTIFS, so the schedule shows the counts the period block gives for one year at a time.")

    # (5) the model answer
    cm = fx["memos"].get(c, dict(n=0, sub=0.0))
    yr = by_year[c]
    answer(ws, dr + 3, "Model answer (5)", [
        f"This schedule shows what Charles River billed, not the revenue it reports. It does not net the credit memos "
        f"(the CreditMemo worksheet holds {cm['n']:,} credit memos dated in {c}, with a SubTotal of "
        f"{money(cm['sub'])}), which reduce revenue for returns and allowances. Its GrandTotal includes sales tax "
        f"({money(yr['tax'])} in {c}), a liability collected for the government rather than revenue, and freight billed "
        f"({money(yr['frt'])}), which the ledger records in its own revenue account (4050) rather than in product "
        f"sales, so only SubTotal, net of credit memos, approaches the sales revenue of the financial statements."])

    settle(b)
    e = "4.1"
    b.check(e, f"invoices in the period, fiscal {c} (Ex 4.1!B8)", yr["n"], "='Ex 4.1'!B8", 0, COUNT)
    for i, m in enumerate(measures):
        key = ("sub", "frt", "tax", "gt")[i]
        b.check(e, f"{m} in the period (Ex 4.1!B{9 + i})", round(yr[key], 2), f"='Ex 4.1'!B{9 + i}")
    b.check(e, "SubTotal + FreightAmount + TaxAmount - GrandTotal (Ex 4.1!B13)", 0, "='Ex 4.1'!B13")
    b.check(e, "invoices whose parts do not add up (Ex 4.1!B14)", fx["unbalanced"], "='Ex 4.1'!B14", 0, COUNT)
    for r, y in zip(rows, years):
        for j, m in enumerate(measures):
            key = ("sub", "frt", "tax", "gt")[j]
            cl = letter(2 + j)
            b.check(e, f"{m}, fiscal {y} (Ex 4.1!{cl}{r})", round(by_year[y][key], 2), f"='Ex 4.1'!{cl}{r}")
        b.check(e, f"invoices, fiscal {y} (Ex 4.1!G{r})", by_year[y]["n"], f"='Ex 4.1'!G{r}", 0, COUNT)
    for j, m in enumerate(measures):
        key = ("sub", "frt", "tax", "gt")[j]
        cl = letter(2 + j)
        b.check(e, f"{m}, total row (Ex 4.1!{cl}{tr})", round(tot[key], 2), f"='Ex 4.1'!{cl}{tr}")
        b.check(e, f"{m}, total row less the entire Table (Ex 4.1!{cl}{dr})", 0, f"='Ex 4.1'!{cl}{dr}")
    b.check(e, f"invoices, all years (Ex 4.1!G{tr})", tot["n"], f"='Ex 4.1'!G{tr}", 0, COUNT)
    b.check(e, f"invoices, total row less the Table's rows (Ex 4.1!G{dr})", 0, f"='Ex 4.1'!G{dr}", 0, COUNT)


# --- Exercise 4.2 ------------------------------------------------------------------------------------------------

def ex4_2(b: ExerciseBuild) -> None:
    fx = facts()["ex2"]
    progs = fx["programs"]
    ws = new_sheet(b, "Ex 4.2")
    heading(ws, "A1", "Exercise 4.2: Reviewing Promotional Discounts", 14)
    heads = ["PromotionID", "PromotionCode", "PromotionName", "Invoice lines", "LineTotal", "DiscountAmount",
             "Share of discount dollars", "DiscountPct", "Lines at another rate"]
    for j, h in enumerate(heads):
        ws.Cells(3, 1 + j).Value = h
    bold(ws, "A3:I3")
    first = 4
    rows = list(range(first, first + len(progs)))
    tot = rows[-1] + 1
    lk = "PromotionProgram[PromotionID]"
    for r, p in zip(rows, progs):
        ws.Range(f"A{r}").Value = p["id"]
        formulas(ws, {
            f"B{r}": f"=XLOOKUP($A{r},{lk},PromotionProgram[PromotionCode])",
            f"C{r}": f"=XLOOKUP($A{r},{lk},PromotionProgram[PromotionName])",
            f"D{r}": f"=COUNTIFS(SalesInvoiceLine[PromotionID],$A{r})",
            f"E{r}": f"=SUMIFS(SalesInvoiceLine[LineTotal],SalesInvoiceLine[PromotionID],$A{r})",
            f"F{r}": f"=SUMIFS(SalesInvoiceLine[DiscountAmount],SalesInvoiceLine[PromotionID],$A{r})",
            f"G{r}": f"=F{r}/$F${tot}",
            f"H{r}": f"=XLOOKUP($A{r},{lk},PromotionProgram[DiscountPct])",
            f"I{r}": f'=COUNTIFS(SalesInvoiceLine[PromotionID],$A{r},SalesInvoiceLine[Discount],"<>"&H{r})'})
    values(ws, {f"A{tot}": "Total"})
    for cl in "DEFGI":
        ws.Range(f"{cl}{tot}").Formula2 = f"=SUM({cl}{first}:{cl}{rows[-1]})"
    bold(ws, f"A{tot}:I{tot}")
    ws.Range(f"A{first}:A{rows[-1]}").HorizontalAlignment = -4131
    ws.Range(f"D{first}:D{tot}").NumberFormat = COUNT
    ws.Range(f"E{first}:F{tot}").NumberFormat = MONEY
    ws.Range(f"G{first}:G{tot}").NumberFormat = "0.0%"
    ws.Range(f"H{first}:H{rows[-1]}").NumberFormat = "0%"
    ws.Range(f"I{first}:I{tot}").NumberFormat = COUNT
    ws.Range(f"F{first}:F{rows[-1]}").FormatConditions.AddDatabar()
    note(ws, f"G{first}", f"Each promotion's discount dollars over the grand total in F{tot}, an absolute reference "
                          f"($F${tot}), so the formula fills down unchanged.")

    # (3) the consistency test
    r0 = tot + 2
    heading(ws, f"A{r0}", "Rate consistency test", 11)
    values(ws, {f"A{r0 + 1}": "Lines at a rate other than their promotion's DiscountPct (column I)",
                f"A{r0 + 2}": "Lines with a discount and no PromotionID",
                f"A{r0 + 3}": "Promotion lines left out of the summary (PromotionID not in PromotionProgram)",
                f"A{r0 + 4}": "Result"})
    formulas(ws, {f"B{r0 + 1}": f"=I{tot}",
                  f"B{r0 + 2}": '=COUNTIFS(SalesInvoiceLine[PromotionID],"",SalesInvoiceLine[Discount],"<>0")',
                  f"B{r0 + 3}": f'=COUNTIFS(SalesInvoiceLine[PromotionID],"<>")-D{tot}',
                  f"B{r0 + 4}": f'=IF(B{r0 + 1}+B{r0 + 2}+B{r0 + 3}=0,"No promotion was applied at a rate other '
                                f'than its approved rate","Differences found")'})
    ws.Range(f"B{r0 + 1}:B{r0 + 3}").NumberFormat = COUNT

    # (4) the promotion with the largest share, and its scope, rate, and dates from PromotionProgram
    r1 = r0 + 6
    heading(ws, f"A{r1}", "The promotion with the largest share of the discount dollars", 11)
    rng = f"$G${first}:$G${rows[-1]}"
    fields = [("PromotionCode", None), ("PromotionName", None), ("ScopeType", None), ("ItemGroup", None),
              ("CustomerSegment", None), ("CollectionName", None), ("DiscountPct", "0%"),
              ("EffectiveStartDate", DATEF), ("EffectiveEndDate", DATEF)]
    values(ws, {f"A{r1 + 1}": "PromotionID"})
    formulas(ws, {f"B{r1 + 1}": f"=XLOOKUP(MAX({rng}),{rng},$A${first}:$A${rows[-1]})"})
    ws.Range(f"B{r1 + 1}").HorizontalAlignment = -4131
    for i, (fld, fmt) in enumerate(fields, start=2):
        values(ws, {f"A{r1 + i}": fld})
        tail = "" if fmt else '&""'                 # a blank scope field reads as empty text, not 0
        formulas(ws, {f"B{r1 + i}": f"=XLOOKUP($B${r1 + 1},{lk},PromotionProgram[{fld}]){tail}"})
        if fmt:
            ws.Range(f"B{r1 + i}").NumberFormat = fmt
            ws.Range(f"B{r1 + i}").HorizontalAlignment = -4131
    rs = r1 + len(fields) + 2
    values(ws, {f"A{rs}": "Share of the discount dollars"})
    formulas(ws, {f"B{rs}": f"=MAX({rng})"})
    ws.Range(f"B{rs}").NumberFormat = "0.0%"
    ws.Range(f"B{rs}").HorizontalAlignment = -4131
    values(ws, {f"A{rs + 2}": "Promotions whose EffectiveEndDate is before their EffectiveStartDate",
                f"A{rs + 3}": "Promotions effective for a single day"})
    formulas(ws, {f"B{rs + 2}": "=SUMPRODUCT(--(PromotionProgram[EffectiveEndDate]<PromotionProgram[EffectiveStartDate]))",
                  f"B{rs + 3}": "=SUMPRODUCT(--(PromotionProgram[EffectiveEndDate]=PromotionProgram[EffectiveStartDate]))"})
    widths(ws, {"A": 34, "B": 17, "C": 30, "D": 12, "E:F": 15, "G": 14, "H": 11, "I": 12})
    ws.Columns("A").WrapText = False

    # the model answers
    top, second = fx["top"], fx["second"]
    target = top["group"] or top["segment"] or top["collection"]
    scope = {"ItemGroup": f"every item in the {target} item group", "Segment": f"every customer in the {target} segment",
             "Collection": f"the items of the {target} collection"}.get(top["scope"], f"{top['scope']} {target}")
    share = top["discount"] / fx["discount"]
    nxt = answer(ws, rs + 5, "Model answer (4)", [
        f"Promotion {top['id']}, the {top['name']} ({top['code']}), holds {pct(share)} of the discount dollars "
        f"({money(top['discount'])} of {money(fx['discount'])}). Its scope is {scope} (ScopeType {top['scope']}), its "
        f"rate is {top['pct']:.0%}, and it was effective from {long_date(top['start'])} to {long_date(top['end'])}."])
    by_year = {}
    for p in progs:
        by_year.setdefault(p["start"][:4], []).append(p)
    pattern = all(len(v) == 3 for v in by_year.values())
    oddities = []
    if fx["backwards"]:
        oddities.append(f"promotion{'s' if len(fx['backwards']) > 1 else ''} {and_join(fx['backwards'])} "
                        f"{'have' if len(fx['backwards']) > 1 else 'has'} an EffectiveEndDate earlier than "
                        f"{'their' if len(fx['backwards']) > 1 else 'its'} EffectiveStartDate")
    if fx["single"]:
        oddities.append(f"promotion{'s' if len(fx['single']) > 1 else ''} {and_join(fx['single'])} "
                        f"{'are' if len(fx['single']) > 1 else 'is'} effective for a single day")
    rates = sorted({p["pct"] for p in progs})
    answer(ws, nxt, "Model answer (5): memo", [
        "To: Sales director. From: Finance. Subject: Promotion programs and their discounts.",
        f"Charles River ran {word(len(progs))} promotion programs in fiscal {min(by_year)} to {max(by_year)}"
        f"{', three a year' if pattern else ''}, at rates of {and_join(f'{r:.0%}' for r in rates)}. Together they "
        f"discounted {fx['lines']:,} invoice lines, with a LineTotal of {money(fx['total'])}, by "
        f"{money(fx['discount'])}. Promotion {top['id']}, the {top['name']}, gave away {money(top['discount'])}, "
        f"{pct(share)} of all discount dollars, followed by promotion {second['id']}, the {second['name']} "
        f"({money(second['discount'])}). The summary on this worksheet lists every promotion, and the data bars "
        "show how far the largest stands above the others.",
        "Consistency test: for each promotion I counted the invoice lines whose Discount differs from the promotion's "
        "DiscountPct. The count is zero for every promotion, no invoice line carries a discount without a "
        "PromotionID, and every PromotionID on the lines is in the PromotionProgram Table. Every promotion was "
        "therefore applied at its approved rate.",
        "What the analysis cannot yet show: the invoice lines carry no invoice date, so this workbook cannot test "
        "whether each discounted line was billed within its promotion's effective dates. That test matters here, "
        f"because the PromotionProgram Table itself is suspect: {and_join(oddities)}, so the recorded dates "
        "cannot be relied on as they stand. Bringing the invoice dates onto the lines, a lookup a later chapter "
        "builds, will show when each discounted line was billed and whether any discount was given outside its "
        "promotion's window."])

    settle(b)
    e = "4.2"
    for r, p in zip(rows, progs):
        b.check(e, f"promotion {p['id']}: invoice lines (Ex 4.2!D{r})", p["lines"], f"='Ex 4.2'!D{r}", 0, COUNT)
        b.check(e, f"promotion {p['id']}: LineTotal (Ex 4.2!E{r})", round(p["total"], 2), f"='Ex 4.2'!E{r}")
        b.check(e, f"promotion {p['id']}: DiscountAmount (Ex 4.2!F{r})", round(p["discount"], 2), f"='Ex 4.2'!F{r}")
    b.check(e, "rows of the PromotionProgram Table", len(progs), "=ROWS(PromotionProgram[PromotionID])", 0, COUNT)
    b.check(e, "summary rows less the rows of PromotionProgram (one row per PromotionID)", 0,
            f"=COUNT('Ex 4.2'!A{first}:A{rows[-1]})-ROWS(PromotionProgram[PromotionID])", 0, COUNT)
    b.check(e, f"all promotion lines (Ex 4.2!D{tot})", fx["lines"], f"='Ex 4.2'!D{tot}", 0, COUNT)
    b.check(e, f"all LineTotal (Ex 4.2!E{tot})", round(fx["total"], 2), f"='Ex 4.2'!E{tot}")
    b.check(e, f"all discount dollars (Ex 4.2!F{tot})", round(fx["discount"], 2), f"='Ex 4.2'!F{tot}")
    b.check(e, f"shares add up to 100% (Ex 4.2!G{tot})", 1, f"='Ex 4.2'!G{tot}", 1e-9, PCT)
    b.check(e, f"lines at another rate, all promotions (Ex 4.2!I{tot})",
            sum(p["other_rate"] for p in progs), f"='Ex 4.2'!I{tot}", 0, COUNT)
    b.check(e, f"lines with a discount and no PromotionID (Ex 4.2!B{r0 + 2})", fx["no_promo_discount"],
            f"='Ex 4.2'!B{r0 + 2}", 0, COUNT)
    b.check(e, f"promotion lines left out of the summary (Ex 4.2!B{r0 + 3})", fx["orphans"], f"='Ex 4.2'!B{r0 + 3}",
            0, COUNT)
    b.check(e, f"promotion with the largest share (Ex 4.2!B{r1 + 1})", top["id"], f"='Ex 4.2'!B{r1 + 1}", 0, COUNT)
    b.check(e, f"its share of the discount dollars (Ex 4.2!B{rs})", round(share, 9), f"='Ex 4.2'!B{rs}", 1e-9, PCT)
    b.check(e, f"its PromotionCode (Ex 4.2!B{r1 + 2})", top["code"], f"='Ex 4.2'!B{r1 + 2}", 0, TEXT)
    b.check(e, f"its ScopeType (Ex 4.2!B{r1 + 4})", top["scope"], f"='Ex 4.2'!B{r1 + 4}", 0, TEXT)
    b.check(e, f"its ItemGroup (Ex 4.2!B{r1 + 5})", top["group"] or "", f"='Ex 4.2'!B{r1 + 5}", 0, TEXT)
    b.check(e, f"its DiscountPct (Ex 4.2!B{r1 + 8})", top["pct"], f"='Ex 4.2'!B{r1 + 8}", 1e-9, PCT)
    b.check(e, f"its EffectiveStartDate (Ex 4.2!B{r1 + 9})", serial(top["start"]), f"='Ex 4.2'!B{r1 + 9}", 0, DATEF)
    b.check(e, f"its EffectiveEndDate (Ex 4.2!B{r1 + 10})", serial(top["end"]), f"='Ex 4.2'!B{r1 + 10}", 0, DATEF)
    b.check(e, f"promotions ending before they start (Ex 4.2!B{rs + 2})", len(fx["backwards"]), f"='Ex 4.2'!B{rs + 2}",
            0, COUNT)
    b.check(e, f"promotions effective for a single day (Ex 4.2!B{rs + 3})", len(fx["single"]), f"='Ex 4.2'!B{rs + 3}",
            0, COUNT)


# --- Exercise 4.3 ------------------------------------------------------------------------------------------------

def ex4_3(b: ExerciseBuild) -> None:
    fx = facts()["ex3"]
    wb = b.wb
    item = xl.table(wb, "Item")
    iws = wb.Worksheets("Item")
    # (1) the two calculated columns
    add_column(item, "UnitMargin", "=[@ListPrice]-[@StandardCost]", MONEY)
    add_column(item, "MarginPct", "=[@UnitMargin]/[@ListPrice]", "0.0%")
    mp = col(item, "MarginPct")

    ws = new_sheet(b, "Ex 4.3")
    heading(ws, "A1", "Exercise 4.3: List-Price Margins by Product Group", 14)
    widths(ws, {"A": 46, "B": 16, "C": 16, "D": 16, "E": 18, "F:H": 12})
    # (4) the margin target, validated as a decimal between 0 and 1
    values(ws, {"A3": "Parameter", "B3": "Value", "C3": "Description", "A4": "MarginTarget", "B4": 0.45,
                "C4": "Items below this MarginPct are highlighted on the Item worksheet (a decimal from 0 to 1)",
                "A5": "ProductGroup", "B5": "Furniture",
                "C5": "Product group for the AVERAGEIFS results below (a list of the four groups)"})
    bold(ws, "A3:C3")
    ws.Range("B4").NumberFormat = "0.00"
    ws.Range("B4:B5").Font.Color = xl.BLUE
    xl.name_cell(wb, "MarginTarget", "'Ex 4.3'!$B$4")
    xl.name_cell(wb, "ProductGroup", "'Ex 4.3'!$B$5")
    validate(ws.Range("B4"), XL_VALIDATE_DECIMAL, XL_BETWEEN, "0", "1", title="MarginTarget",
             message="Enter the margin target as a decimal from 0 to 1, such as 0.45.",
             error="MarginTarget must be a decimal from 0 to 1.")
    groups = list(fx["groups"])
    validate(ws.Range("B5"), XL_VALIDATE_LIST, None, ",".join(groups), title="ProductGroup",
             message="Choose a product group.", error="Choose one of the four product groups from the list.")

    # (3)-(4) on the Item Table: the color scale, then the highlight rule (on the columns left of MarginPct, so the
    # color scale stays visible), then the sort, then the filter of (2)
    item.ListColumns("MarginPct").DataBodyRange.FormatConditions.AddColorScale(3)
    body = item.DataBodyRange
    left = iws.Range(body.Cells(1, 1), body.Cells(body.Rows.Count, item.ListColumns("MarginPct").Index - 1))
    row_rule(iws, left, f"=${mp}2<MarginTarget", AMBER)
    sort_table(item, [("ItemGroup", xl.XL_ASCENDING), ("MarginPct", xl.XL_DESCENDING)])
    xl.retry(item.Range.AutoFilter, item.ListColumns("ItemType").Index, "Finished Good")
    ready(iws)
    iws.Range("A1").Select()

    crit = 'Item[ItemType],"Finished Good"'
    heading(ws, "A7", "Finished goods (the Item Table filtered to ItemType Finished Good)", 11)
    rows = {"A8": ("Finished goods in view (SUBTOTAL)", "=SUBTOTAL(103,Item[ItemID])", COUNT),
            "A9": ("Below MarginTarget", f'=COUNTIFS({crit},Item[MarginPct],"<"&MarginTarget)', COUNT),
            "A10": ("Below 30 percent", f'=COUNTIFS({crit},Item[MarginPct],"<0.3")', COUNT),
            "A11": ("Lowest MarginPct", f"=MINIFS(Item[MarginPct],{crit})", "0.0%"),
            "A12": ("Highest MarginPct", f"=MAXIFS(Item[MarginPct],{crit})", "0.0%"),
            "A13": ("Design services (not finished goods)", '=COUNTIFS(Item[ItemType],"<>Finished Good")', COUNT),
            "A14": ("their StandardCost (total)", '=SUMIFS(Item[StandardCost],Item[ItemType],"<>Finished Good")', MONEY),
            "A15": ("their average MarginPct", '=AVERAGEIFS(Item[MarginPct],Item[ItemType],"<>Finished Good")', "0.0%")}
    for addr, (label, f, fmt) in rows.items():
        r = addr[1:]
        values(ws, {addr: label})
        formulas(ws, {f"B{r}": f})
        ws.Range(f"B{r}").NumberFormat = fmt

    # (5) the group selector and AVERAGEIFS, and the results recorded for each group
    heading(ws, "A17", "The selected product group (ProductGroup)", 11)
    sel = f"{crit},Item[ItemGroup],ProductGroup"
    values(ws, {"A18": "Average UnitMargin", "A19": "Average MarginPct", "A20": "Finished goods",
                "A21": "Below MarginTarget"})
    formulas(ws, {"B18": f"=AVERAGEIFS(Item[UnitMargin],{sel})", "B19": f"=AVERAGEIFS(Item[MarginPct],{sel})",
                  "B20": f"=COUNTIFS({sel})", "B21": f'=COUNTIFS({sel},Item[MarginPct],"<"&MarginTarget)'})
    ws.Range("B18").NumberFormat = MONEY
    ws.Range("B19").NumberFormat = "0.0%"
    heading(ws, "A23", "Results recorded for each group", 11)
    values(ws, {"A24": "Product group", "B24": "Finished goods", "C24": "Average UnitMargin", "D24": "Average MarginPct",
                "E24": "Below MarginTarget"})
    bold(ws, "A24:E24")
    grow = {}
    for i, g in enumerate(groups):
        r = 25 + i
        grow[g] = r
        gc = f"{crit},Item[ItemGroup],$A{r}"
        values(ws, {f"A{r}": g})
        formulas(ws, {f"B{r}": f"=COUNTIFS({gc})", f"C{r}": f"=AVERAGEIFS(Item[UnitMargin],{gc})",
                      f"D{r}": f"=AVERAGEIFS(Item[MarginPct],{gc})",
                      f"E{r}": f'=COUNTIFS({gc},Item[MarginPct],"<"&MarginTarget)'})
    tr = 25 + len(groups)
    values(ws, {f"A{tr}": "Total"})
    formulas(ws, {f"B{tr}": f"=SUM(B25:B{tr - 1})", f"E{tr}": f"=SUM(E25:E{tr - 1})"})
    bold(ws, f"A{tr}:E{tr}")
    ws.Range(f"C25:C{tr}").NumberFormat = MONEY
    ws.Range(f"D25:D{tr}").NumberFormat = "0.0%"
    note(ws, "A24", "Each row is the selector's AVERAGEIFS with the group in column A instead of ProductGroup: the "
                    "results a reader records by choosing each group in B5 in turn, kept live so they refresh.")

    # the model answers
    g = fx["groups"]
    most = max(g, key=lambda k: g[k]["margin"])
    least = min(g, key=lambda k: g[k]["margin"])
    hi_pct = max(g, key=lambda k: g[k]["pct"])
    lo_pct = min(g, key=lambda k: g[k]["pct"])
    below = sorted(((k, v["below"]) for k, v in g.items() if v["below"]), key=lambda kv: (-kv[1], kv[0]))
    none_below = [k for k, v in g.items() if not v["below"]]
    svc = fx["services"]
    assert svc and all(s["cost"] == 0 for s in svc), "the design services no longer have a StandardCost of 0"
    nxt = answer(ws, tr + 3, "Model answer (2)", [
        f"The {word(len(svc))} design services are billed by the hour and carry a StandardCost of 0, because the designers' "
        "time is paid through payroll rather than held as a product cost. Their MarginPct is therefore 100 percent, "
        "which says nothing about their profitability: included in the comparison, they would sit at the top of "
        "every ranking and pull up the averages, so the comparison is limited to the finished goods, whose "
        "StandardCost measures what an item costs to make or buy."])
    first_sentence = (f"{most} earns the most per unit (an average UnitMargin of {money(g[most]['margin'])}) "
                      + (f"but has the lowest average percentage ({pct(g[most]['pct'])})" if most == lo_pct else
                         f"at an average of {pct(g[most]['pct'])}")
                      + f", while {least} earns the least per unit ({money(g[least]['margin'])})"
                      + (f" at the highest percentage ({pct(g[least]['pct'])})." if least == hi_pct else
                         f" at {pct(g[least]['pct'])}."))
    answer(ws, nxt, "Model answer (6)", [
        first_sentence + f" MarginPct runs from {pct(fx['low'])} to {pct(fx['high'])}, so no item is below 30 "
        f"percent, but {fx['below']} items are below the 0.45 target: "
        + and_join(f"{k} {v}" for k, v in below)
        + (f", and no {and_join(none_below)} item." if none_below else ".")
        + " A margin at list price is not what Charles River earns: most sales are billed at price-list prices "
        "below list, some lines carry promotional discounts on top, and StandardCost is a standard, not the actual "
        "cost, so realized margins are lower and differ by customer and period."])

    settle(b)
    e = "4.3"
    b.check(e, "finished goods in view after the filter (Ex 4.3!B8)", fx["goods"], "='Ex 4.3'!B8", 0, COUNT)
    b.check(e, "rows of the Item Table (all items with a list price)", fx["items"], "=ROWS(Item[ItemID])", 0, COUNT)
    b.check(e, "finished goods below MarginTarget (Ex 4.3!B9)", fx["below"], "='Ex 4.3'!B9", 0, COUNT)
    b.check(e, "finished goods below 30 percent (Ex 4.3!B10)", fx["below30"], "='Ex 4.3'!B10", 0, COUNT)
    b.check(e, "lowest MarginPct (Ex 4.3!B11)", round(fx["low"], 9), "='Ex 4.3'!B11", 1e-9, PCT)
    b.check(e, "highest MarginPct (Ex 4.3!B12)", round(fx["high"], 9), "='Ex 4.3'!B12", 1e-9, PCT)
    b.check(e, "design services (Ex 4.3!B13)", len(svc), "='Ex 4.3'!B13", 0, COUNT)
    b.check(e, "their StandardCost (Ex 4.3!B14)", 0, "='Ex 4.3'!B14")
    b.check(e, "their MarginPct, 100 percent (Ex 4.3!B15)", 1, "='Ex 4.3'!B15", 1e-9, PCT)
    for k, r in grow.items():
        b.check(e, f"{k}: finished goods (Ex 4.3!B{r})", g[k]["n"], f"='Ex 4.3'!B{r}", 0, COUNT)
        b.check(e, f"{k}: average UnitMargin (Ex 4.3!C{r})", round(g[k]["margin"], 6), f"='Ex 4.3'!C{r}", 1e-6)
        b.check(e, f"{k}: average MarginPct (Ex 4.3!D{r})", round(g[k]["pct"], 9), f"='Ex 4.3'!D{r}", 1e-9, PCT)
        b.check(e, f"{k}: below MarginTarget (Ex 4.3!E{r})", g[k]["below"], f"='Ex 4.3'!E{r}", 0, COUNT)
    b.check(e, "selector (Furniture): average UnitMargin (Ex 4.3!B18)", round(g["Furniture"]["margin"], 6),
            "='Ex 4.3'!B18", 1e-6)
    b.check(e, "selector (Furniture): average MarginPct (Ex 4.3!B19)", round(g["Furniture"]["pct"], 9),
            "='Ex 4.3'!B19", 1e-9, PCT)
    if fx["first_unique"]:
        b.check(e, "the Item Table's first row after the sort (Accessories, highest MarginPct)", fx["first"],
                "=INDEX(Item[ItemCode],1)", 0, TEXT)


# --- Exercise 4.4 ------------------------------------------------------------------------------------------------

def ex4_4(b: ExerciseBuild) -> None:
    fx = facts()["ex4"]
    wb = b.wb
    ws = new_sheet(b, "Ex 4.4")
    # (1) the Shipment and SalesOrder Tables, imported with Power Query
    xl.add_query(wb, "Shipment", nav(b, 14, "Shipment"))
    xl.add_query(wb, "SalesOrder", nav(b, 9, "SalesOrder"))
    sh = load(b, "Shipment", "Ex 4.4 Shipment", after=ws)
    so = load(b, "SalesOrder", "Ex 4.4 SalesOrder", after=wb.Worksheets("Ex 4.4 Shipment"))
    assert so.ListRows.Count > 0
    sws = wb.Worksheets("Ex 4.4 Shipment")
    # (2) the two calculated columns
    add_column(sh, "FreightTerms", "=XLOOKUP([@SalesOrderID],SalesOrder[SalesOrderID],SalesOrder[FreightTerms])")
    add_column(sh, "FreightMargin", "=[@BillableFreightAmount]-[@FreightCost]", MONEY)
    fm = col(sh, "FreightMargin")
    # (3) the highlight rule on negative FreightMargin
    row_rule(sws, sh.DataBodyRange, f"=${fm}2<0", CORAL)
    sws.Range("A1").Select()

    heading(ws, "A1", "Exercise 4.4: Freight Billed Versus Freight Incurred", 14)
    widths(ws, {"A": 44, "B:F": 17, "G": 3})
    heading(ws, "A3", "Shipments with a negative FreightMargin (highlighted on the Ex 4.4 Shipment worksheet)", 11)
    values(ws, {"A4": "Shipments", "A5": "Total FreightMargin", "A6": "FreightTerms not found (lookup errors)"})
    formulas(ws, {"B4": '=COUNTIFS(Shipment[FreightMargin],"<0")',
                  "B5": '=SUMIFS(Shipment[FreightMargin],Shipment[FreightMargin],"<0")',
                  "B6": "=SUMPRODUCT(--ISNA(Shipment[FreightTerms]))"})
    ws.Range("B4").NumberFormat = COUNT
    ws.Range("B5").NumberFormat = MONEY
    ws.Range("B6").NumberFormat = COUNT

    # (4) the grid by FreightTerms
    heading(ws, "A8", "Freight by FreightTerms", 11)
    values(ws, {"A9": "FreightTerms", "B9": "Shipments", "C9": "FreightCost", "D9": "BillableFreightAmount",
                "E9": "FreightMargin"})
    bold(ws, "A9:E9")
    terms = list(fx["terms"])
    trow = {}
    lock = "Shipment[[FreightTerms]:[FreightTerms]]"
    for i, t in enumerate(terms):
        r = 10 + i
        trow[t] = r
        values(ws, {f"A{r}": t})
        formulas(ws, {f"B{r}": f"=COUNTIFS({lock},$A{r})",
                      f"C{r}": f"=SUMIFS(Shipment[FreightCost],{lock},$A{r})",
                      f"D{r}": f"=SUMIFS(Shipment[BillableFreightAmount],{lock},$A{r})",
                      f"E{r}": f"=SUMIFS(Shipment[FreightMargin],{lock},$A{r})"})
    tr = 10 + len(terms)
    values(ws, {f"A{tr}": "Total", f"A{tr + 1}": "Entire Shipment Table", f"A{tr + 2}": "Difference"})
    for cl, src in zip("BCDE", ("ROWS(Shipment[ShipmentID])", "SUM(Shipment[FreightCost])",
                                "SUM(Shipment[BillableFreightAmount])", "SUM(Shipment[FreightMargin])")):
        formulas(ws, {f"{cl}{tr}": f"=SUM({cl}10:{cl}{tr - 1})", f"{cl}{tr + 1}": f"={src}",
                      f"{cl}{tr + 2}": f"=ROUND({cl}{tr}-{cl}{tr + 1},2)"})
    bold(ws, f"A{tr}:E{tr}")
    ws.Range(f"B10:B{tr + 2}").NumberFormat = COUNT
    ws.Range(f"C10:E{tr + 2}").NumberFormat = MONEY
    note(ws, "B10", "Each formula locks the row label's column ($A10) and the FreightTerms column "
                    "([[FreightTerms]:[FreightTerms]]), so it can be copied down and across the grid; only the sum "
                    "column differs from one column of the grid to the next.")

    # the detail behind the interpretation
    pa, pp = "Prepaid and Add", "Prepaid"
    assert set(terms) == {pp, pa}, terms
    r0 = tr + 4
    heading(ws, f"A{r0}", "Freight billed against its cost", 11)
    rows = [(f"{pp}: shipments that bill freight", f'=COUNTIFS(Shipment[FreightTerms],"{pp}",'
                                                    'Shipment[BillableFreightAmount],">0")', COUNT),
            (f"{pa}: billed above cost", f'=COUNTIFS(Shipment[FreightTerms],"{pa}",Shipment[FreightMargin],">0")', COUNT),
            (f"{pa}: billed below cost", f'=COUNTIFS(Shipment[FreightTerms],"{pa}",Shipment[FreightMargin],"<0")', COUNT),
            (f"{pa}: billed at cost", f'=COUNTIFS(Shipment[FreightTerms],"{pa}",Shipment[FreightMargin],0)', COUNT),
            (f"{pa}: billed freight over FreightCost (totals)", f"=D{trow[pa]}/C{trow[pa]}", "0.0%"),
            (f"{pa}: average of the shipments' ratios", '=AVERAGE(FILTER(Shipment[BillableFreightAmount]/'
                                                       f'Shipment[FreightCost],Shipment[FreightTerms]="{pa}"))', "0.0%"),
            ("Smallest FreightCost", "=MIN(Shipment[FreightCost])", MONEY),
            ("Largest FreightCost", "=MAX(Shipment[FreightCost])", MONEY)]
    for i, (label, f, fmt) in enumerate(rows, start=1):
        values(ws, {f"A{r0 + i}": label})
        formulas(ws, {f"B{r0 + i}": f})
        ws.Range(f"B{r0 + i}").NumberFormat = fmt
    d = {label: r0 + i for i, (label, _, _) in enumerate(rows, start=1)}

    # (5) the slicer on FreightTerms with SUBTOTAL, and the averages recorded under each term
    r1 = r0 + len(rows) + 2
    heading(ws, f"A{r1}", "The slicer on FreightTerms (click a term; SUBTOTAL follows the rows in view)", 11)
    values(ws, {f"A{r1 + 1}": "Shipments in view", f"A{r1 + 2}": "Average FreightCost in view"})
    formulas(ws, {f"B{r1 + 1}": "=SUBTOTAL(103,Shipment[ShipmentID])",
                  f"B{r1 + 2}": "=SUBTOTAL(101,Shipment[FreightCost])"})
    ws.Range(f"B{r1 + 1}").NumberFormat = COUNT
    ws.Range(f"B{r1 + 2}").NumberFormat = MONEY
    cache = add_slicer(b, sh, "FreightTerms", ws, "FreightTerms", f"F{r1}", height=96)
    rec = record_with_slicer(b, cache, sh, "FreightTerms", terms, ws, [f"B{r1 + 1}", f"B{r1 + 2}"])
    r2 = r1 + 4
    values(ws, {f"A{r2}": "Recorded with the slicer", f"B{r2}": "Shipments in view",
                f"C{r2}": "Average FreightCost in view", f"D{r2}": "AVERAGEIFS (live)"})
    bold(ws, f"A{r2}:D{r2}")
    rrow = {}
    for i, t in enumerate(terms):
        r = r2 + 1 + i
        rrow[t] = r
        values(ws, {f"A{r}": t, f"B{r}": rec[t][0], f"C{r}": rec[t][1]})
        formulas(ws, {f"D{r}": f"=AVERAGEIFS(Shipment[FreightCost],Shipment[FreightTerms],$A{r})"})
    ws.Range(f"B{r2 + 1}:B{r2 + len(terms)}").NumberFormat = COUNT
    ws.Range(f"C{r2 + 1}:D{r2 + len(terms)}").NumberFormat = MONEY
    note(ws, f"A{r2}", "Recorded values: the builder clicked each slicer button in turn and copied what the two "
                       "SUBTOTAL cells above showed, as a reader notes them, then cleared the slicer. Column D gives "
                       "the same average with AVERAGEIFS, which does not need the slicer.")

    # (6) the model answer
    tp, ta = fx["terms"][pp], fx["terms"][pa]
    assert tp["billing"] == 0 and ta["billing"] > 0, "the model answer says Prepaid bills no freight"
    more = "more" if ta["below"] > ta["above"] else "fewer"
    absorbed = tp["margin"] / fx["margin"]
    answer(ws, r2 + len(terms) + 3, "Model answer (6)", [
        f"Of the {fx['n']:,} shipments, {tp['n']:,} were on Prepaid orders and bill no freight at all, so their "
        f"FreightMargin of {money(tp['margin'])} is freight Charles River absorbs by design: on Prepaid terms the "
        f"seller pays the carrier and does not recover the cost, an average of {money(tp['avg_cost'])} a shipment. The "
        f"{ta['n']:,} Prepaid and Add shipments bill freight to the customer, and in total the freight billed covers "
        f"{pct(ta['recovered'], 0)} of the carrier cost, a shortfall of only {money(-ta['margin'])}. The shortfall is "
        f"spread across many shipments: {ta['below']:,} are billed below cost and {ta['above']:,} above it "
        f"({more} below than above), and the shipments' own ratios of billed freight to cost average "
        f"{pct(ta['ratio'], 0)}. Absorbed freight on Prepaid orders is therefore {pct(absorbed, 0)} of the total "
        f"FreightMargin of {money(fx['margin'])}, and the discussion of freight terms should start with which orders "
        "are granted Prepaid terms rather than with the rates charged on Prepaid and Add orders."])

    settle(b)
    e = "4.4"
    b.check(e, "shipments (rows of the Shipment Table)", fx["n"], "=ROWS(Shipment[ShipmentID])", 0, COUNT)
    b.check(e, "FreightTerms lookups not found (Ex 4.4!B6)", fx["unmatched"], "='Ex 4.4'!B6", 0, COUNT)
    b.check(e, "shipments with a negative FreightMargin (Ex 4.4!B4)", fx["negative"], "='Ex 4.4'!B4", 0, COUNT)
    b.check(e, "their total FreightMargin (Ex 4.4!B5)", round(fx["negative_total"], 2), "='Ex 4.4'!B5")
    for t, r in trow.items():
        v = fx["terms"][t]
        b.check(e, f"{t}: shipments (Ex 4.4!B{r})", v["n"], f"='Ex 4.4'!B{r}", 0, COUNT)
        b.check(e, f"{t}: FreightCost (Ex 4.4!C{r})", round(v["cost"], 2), f"='Ex 4.4'!C{r}")
        b.check(e, f"{t}: BillableFreightAmount (Ex 4.4!D{r})", round(v["billed"], 2), f"='Ex 4.4'!D{r}")
        b.check(e, f"{t}: FreightMargin (Ex 4.4!E{r})", round(v["margin"], 2), f"='Ex 4.4'!E{r}")
    b.check(e, f"total FreightMargin (Ex 4.4!E{tr})", round(fx["margin"], 2), f"='Ex 4.4'!E{tr}")
    for cl, label in zip("BCDE", ("shipments", "FreightCost", "BillableFreightAmount", "FreightMargin")):
        b.check(e, f"grid total less the entire Table, {label} (Ex 4.4!{cl}{tr + 2})", 0, f"='Ex 4.4'!{cl}{tr + 2}")
    b.check(e, "Prepaid shipments that bill freight", tp["billing"], f"='Ex 4.4'!B{d[f'{pp}: shipments that bill freight']}",
            0, COUNT)
    for key, label in (("above", "billed above cost"), ("below", "billed below cost"), ("equal", "billed at cost")):
        r = d[f"{pa}: {label}"]
        b.check(e, f"{pa}: {label} (Ex 4.4!B{r})", ta[key], f"='Ex 4.4'!B{r}", 0, COUNT)
    r = d[f"{pa}: billed freight over FreightCost (totals)"]
    b.check(e, f"{pa}: billed freight over cost (Ex 4.4!B{r})", round(ta["recovered"], 9), f"='Ex 4.4'!B{r}", 1e-9, PCT)
    r = d[f"{pa}: average of the shipments' ratios"]
    b.check(e, f"{pa}: average of the shipments' ratios (Ex 4.4!B{r})", round(ta["ratio"], 9), f"='Ex 4.4'!B{r}",
            1e-9, PCT)
    b.check(e, "smallest FreightCost", round(fx["low"], 2), f"='Ex 4.4'!B{d['Smallest FreightCost']}")
    b.check(e, "largest FreightCost", round(fx["high"], 2), f"='Ex 4.4'!B{d['Largest FreightCost']}")
    b.check(e, "shipments in view with the slicer cleared (SUBTOTAL)", fx["n"], f"='Ex 4.4'!B{r1 + 1}", 0, COUNT)
    for t, r in rrow.items():
        v = fx["terms"][t]
        b.check(e, f"{t}: shipments in view, recorded with the slicer (Ex 4.4!B{r})", v["n"], f"='Ex 4.4'!B{r}", 0, COUNT)
        b.check(e, f"{t}: average FreightCost, recorded with the slicer (Ex 4.4!C{r})", round(v["avg_cost"], 6),
                f"='Ex 4.4'!C{r}", 1e-6)
        b.check(e, f"{t}: average FreightCost with AVERAGEIFS (Ex 4.4!D{r})", round(v["avg_cost"], 6),
                f"='Ex 4.4'!D{r}", 1e-6)


# --- Exercise 4.5 ------------------------------------------------------------------------------------------------

def ex4_5(b: ExerciseBuild) -> None:
    fx = facts()["ex5"]
    wb = b.wb
    review, review2 = fx["review"], fx["review2"]
    par = new_sheet(b, "Ex 4.5 Parameters")
    an = new_sheet(b, "Ex 4.5 Analysis", after=par)
    # (1) the Shipment Table with its two dates as the Date type (query ShipmentReview: Shipment is taken here)
    xl.add_query(wb, "ShipmentReview", nav(b, 14, "Shipment", {"ShipmentDate": "type date", "DeliveryDate": "type date"}))
    lo = load(b, "ShipmentReview", "Ex 4.5 Shipment", after=an)
    tws = wb.Worksheets("Ex 4.5 Shipment")
    note(tws, "A1", "Exercise 4.5 loads the Shipment Table into a new workbook, where its query would be named "
                    "Shipment. In this solutions file, which already holds Exercise 4.4's Shipment query, it is named "
                    "ShipmentReview; its steps are those of a new import with ShipmentDate and DeliveryDate changed "
                    "to the Date type.")
    for c in ("ShipmentDate", "DeliveryDate"):
        lo.ListColumns(c).DataBodyRange.NumberFormat = DATEF

    # (2) the review date
    heading(par, "A1", "Exercise 4.5: A Refreshable Shipment Exception Report (Parameters)", 14)
    values(par, {"A3": "Parameter", "B3": "Value", "C3": "Note", "A4": "ReviewDate"})
    bold(par, "A3:C3")
    put_date(par.Range("B4"), review)
    par.Range("B4").Font.Color = xl.BLUE
    xl.name_cell(wb, "ReviewDate", "'Ex 4.5 Parameters'!$B$4")
    validate(par.Range("B4"), XL_VALIDATE_DATE, XL_GREATER_EQUAL, "=DATE(1900,1,1)", title="ReviewDate",
             message="Enter the review date, the last day of the extract.", error="ReviewDate must be a date.")
    par.Range("C4").Value = (
        f"The review date is the last day of the extract, {long_date(review)}, not TODAY(). A shipment is late only "
        "relative to the date of the data: with a fixed date the counts stay the same every time the report is "
        "refreshed or reviewed, so the work can be re-performed and the workpaper agrees with the evidence, while "
        "TODAY() would change the results every day and, long after the extract, flag every In Transit shipment. "
        "Change ReviewDate when the next extract arrives.")
    widths(par, {"A": 16, "B": 14, "C": 90})
    par.Range("C4").WrapText = True
    par.Rows(4).AutoFit()
    par.Range("A4:C4").VerticalAlignment = TOP
    note(par, "A1", "Exercise 4.5 asks for a Parameters and an Analysis worksheet in a new workbook. This solutions "
                    "file already holds the tutorials' Parameters and Analysis worksheets, so these are named "
                    "Ex 4.5 Parameters and Ex 4.5 Analysis.")

    # (3) the two highlight rules
    tn, st, dd = col(lo, "TrackingNumber"), col(lo, "Status"), col(lo, "DeliveryDate")
    row_rule(tws, lo.DataBodyRange, f'=${tn}2=""', AMBER)
    row_rule(tws, lo.DataBodyRange, f'=AND(${st}2="In Transit",${dd}2<ReviewDate)', CORAL)
    tws.Range("A1").Select()

    # (4) the counts
    S = "ShipmentReview"
    heading(an, "A1", "Exercise 4.5: A Refreshable Shipment Exception Report (Analysis)", 14)
    widths(an, {"A": 52, "B:D": 16, "E:H": 12})
    late = f'{S}[Status],"In Transit",{S}[DeliveryDate],"<"&ReviewDate'
    values(an, {"A3": "Shipments", "A4": "ReviewDate", "A6": "Exception category", "B6": "Shipments",
                "A7": "Blank TrackingNumber (amber)", "A8": "In Transit with a DeliveryDate before ReviewDate (coral)",
                "A9": "In both categories"})
    bold(an, "A6:B6")
    formulas(an, {"B3": f"=ROWS({S}[ShipmentID])", "B4": "=ReviewDate",
                  "B7": f'=COUNTIFS({S}[TrackingNumber],"")', "B8": f"=COUNTIFS({late})",
                  "B9": f'=COUNTIFS({S}[TrackingNumber],"",{late})'})
    an.Range("B4").NumberFormat = DATEF
    an.Range("B3").NumberFormat = COUNT
    an.Range("B7:B9").NumberFormat = COUNT
    statuses = sorted(fx["status"])
    values(an, {"A11": "Blank TrackingNumber by Status", "B11": "Shipments"})
    bold(an, "A11:B11")
    srow = {}
    for i, s in enumerate(statuses):
        r = 12 + i
        srow[s] = r
        values(an, {f"A{r}": s})
        formulas(an, {f"B{r}": f'=COUNTIFS({S}[TrackingNumber],"",{S}[Status],$A{r})'})
    tr = 12 + len(statuses)
    values(an, {f"A{tr}": "Total"})
    formulas(an, {f"B{tr}": f"=SUM(B12:B{tr - 1})"})
    bold(an, f"A{tr}:B{tr}")
    an.Range(f"B12:B{tr}").NumberFormat = COUNT
    years = sorted(fx["transit_by_year"])
    y0 = tr + 2
    values(an, {f"A{y0}": "In Transit shipments by year shipped", f"B{y0}": "Shipments"})
    bold(an, f"A{y0}:B{y0}")
    yrow = {}
    for i, y in enumerate(years):
        r = y0 + 1 + i
        yrow[y] = r
        values(an, {f"A{r}": y})
        an.Range(f"A{r}").HorizontalAlignment = -4131
        formulas(an, {f"B{r}": f'=COUNTIFS({S}[Status],"In Transit",{S}[ShipmentDate],">="&DATE($A{r},1,1),'
                               f'{S}[ShipmentDate],"<="&DATE($A{r},12,31))'})
    yt = y0 + 1 + len(years)
    values(an, {f"A{yt}": "Total In Transit", f"A{yt + 1}": "In Transit, due on or after ReviewDate",
                f"A{yt + 2}": "Blank ShipmentDate or DeliveryDate"})
    formulas(an, {f"B{yt}": f"=SUM(B{y0 + 1}:B{yt - 1})",
                  f"B{yt + 1}": f'=COUNTIFS({S}[Status],"In Transit",{S}[DeliveryDate],">="&ReviewDate)',
                  f"B{yt + 2}": f"=COUNTBLANK({S}[ShipmentDate])+COUNTBLANK({S}[DeliveryDate])"})
    bold(an, f"A{yt}:B{yt}")
    an.Range(f"B{y0 + 1}:B{yt + 2}").NumberFormat = COUNT

    # (5) the slicer on Status, SUBTOTAL, and the second count at another review date
    r1 = yt + 4
    heading(an, f"A{r1}", "The slicer on Status (click a status; SUBTOTAL follows the rows in view)", 11)
    values(an, {f"A{r1 + 1}": "Shipments in view", f"A{r1 + 2}": "With a TrackingNumber, in view",
                f"A{r1 + 3}": "Blank TrackingNumber, in view"})
    formulas(an, {f"B{r1 + 1}": f"=SUBTOTAL(103,{S}[ShipmentID])", f"B{r1 + 2}": f"=SUBTOTAL(103,{S}[TrackingNumber])",
                  f"B{r1 + 3}": f"=B{r1 + 1}-B{r1 + 2}"})
    an.Range(f"B{r1 + 1}:B{r1 + 3}").NumberFormat = COUNT
    cache = add_slicer(b, lo, "Status", an, "ShipmentStatus", f"D{r1}", height=80)
    rec = record_with_slicer(b, cache, lo, "Status", statuses, an, [f"B{r1 + 1}", f"B{r1 + 3}"])
    r2 = r1 + 5
    values(an, {f"A{r2}": "Recorded with the slicer", f"B{r2}": "Shipments in view", f"C{r2}": "Blank TrackingNumber"})
    bold(an, f"A{r2}:C{r2}")
    rrow = {}
    for i, s in enumerate(statuses):
        r = r2 + 1 + i
        rrow[s] = r
        values(an, {f"A{r}": s, f"B{r}": rec[s][0], f"C{r}": rec[s][1]})
    an.Range(f"B{r2 + 1}:C{r2 + len(statuses)}").NumberFormat = COUNT
    note(an, f"A{r2}", "Recorded values: the builder clicked each Status button in turn and copied what the SUBTOTAL "
                       "cells above showed, then cleared the slicer. They agree with the COUNTIFS results above (the blank "
                       "tracking numbers by Status, and the In Transit total by year).")
    r3 = r2 + len(statuses) + 2
    values(an, {f"A{r3}": "Second count with ReviewDate changed to", f"A{r3 + 1}": "In Transit, DeliveryDate before it",
                f"A{r3 + 2}": "Change from the count at ReviewDate"})
    put_date(an.Range(f"B{r3}"), review2)
    formulas(an, {f"B{r3 + 1}": f'=COUNTIFS({S}[Status],"In Transit",{S}[DeliveryDate],"<"&B{r3})',
                  f"B{r3 + 2}": f"=B{r3 + 1}-B8"})
    an.Range(f"B{r3 + 1}:B{r3 + 2}").NumberFormat = COUNT
    note(an, f"A{r3}", f"The exercise has the reader change ReviewDate to {long_date(review2)} and watch B8. This cell "
                       "holds that date so the second count stays visible while ReviewDate keeps the extract's last "
                       "day.")

    # the model answers
    drop = fx["late"] - fx["late2"]
    d2, d1 = date.fromisoformat(review2), date.fromordinal(date.fromisoformat(review).toordinal() - 1)
    window = (f"{d2:%B} {d2.day} to {d1:%B} {d1.day}, {d1.year}" if d2.year == d1.year
              else f"{long_date(review2)} to {long_date(d1.isoformat())}")
    nxt = answer(an, r3 + 4, "Model answer (5)", [
        f"With the slicer on In Transit, SUBTOTAL shows {fx['status']['In Transit']:,} shipments, "
        f"{fx['blank_by'].get('In Transit', 0)} of them without a tracking number; on Delivered it shows "
        f"{fx['status']['Delivered']:,}, {fx['blank_by'].get('Delivered', 0)} without one, the same counts COUNTIFS "
        f"gives. With ReviewDate on {long_date(review2)}, the In Transit shipments past their DeliveryDate fall from "
        f"{fx['late']:,} to {fx['late2']:,}: the {drop} shipments due from {window} are not yet late on the earlier "
        "date. The second category depends on the review date, "
        "which is why it is a validated parameter rather than TODAY()."])
    by_year = and_join(f"{y}: {fx['transit_by_year'][y]:,}" for y in years)
    answer(an, nxt, "Model answer (6): memo", [
        f"To: Audit senior. Subject: Shipment exceptions at {long_date(review)} ({fx['n']:,} shipments).",
        f"1. Blank tracking number: {fx['blank']:,} shipments ({fx['blank_by'].get('Delivered', 0)} Delivered, "
        f"{fx['blank_by'].get('In Transit', 0)} In Transit) have no TrackingNumber, a completeness problem. Likely "
        "cause: shipments recorded without the carrier's reference (manual entry, customer pickup, or a field the "
        "system does not require). Without it, delivery cannot be traced to the carrier. Evidence: the carrier's "
        "bills of lading or invoices and proof of delivery for a sample, and the shipping procedure for recording "
        "tracking numbers.",
        f"2. Stale In Transit status: {fx['late']:,} of the {fx['status']['In Transit']:,} In Transit shipments have "
        f"a DeliveryDate before the review date, and they come from every year of the data ({by_year}). The status "
        "was not updated when the goods arrived, a consistency and timeliness problem (Chapter 2). Likely cause: no "
        "process or interface updates the status on delivery. Evidence: proof of delivery or carrier tracking for a "
        "sample, the customers' receipt of the goods, and the process that is meant to close a shipment.",
        f"3. Both: all {fx['both']} In Transit shipments without a tracking number are past their DeliveryDate, so "
        "neither the system nor the carrier shows that they arrived. They are the first items to confirm with "
        "customers, because revenue and receivables for them rest on deliveries no record supports.",
        "The report is refreshable: the same rules and counts apply to the next extract once ReviewDate is changed."])

    settle(b)
    e = "4.5"
    b.check(e, "shipments (Ex 4.5 Analysis!B3)", fx["n"], "='Ex 4.5 Analysis'!B3", 0, COUNT)
    b.check(e, "ReviewDate (Ex 4.5 Parameters!B4)", serial(review), "=ReviewDate", 0, DATEF)
    b.check(e, "ShipmentDate holds dates (first row)", True, f"=ISNUMBER(INDEX({S}[ShipmentDate],1))", 0, TEXT)
    b.check(e, "blank TrackingNumber (Ex 4.5 Analysis!B7)", fx["blank"], "='Ex 4.5 Analysis'!B7", 0, COUNT)
    b.check(e, f"In Transit with a DeliveryDate before {review} (Ex 4.5 Analysis!B8)", fx["late"],
            "='Ex 4.5 Analysis'!B8", 0, COUNT)
    b.check(e, "in both categories (Ex 4.5 Analysis!B9)", fx["both"], "='Ex 4.5 Analysis'!B9", 0, COUNT)
    for s, r in srow.items():
        b.check(e, f"blank TrackingNumber, {s} (Ex 4.5 Analysis!B{r})", fx["blank_by"].get(s, 0),
                f"='Ex 4.5 Analysis'!B{r}", 0, COUNT)
    for y, r in yrow.items():
        b.check(e, f"In Transit shipped in {y} (Ex 4.5 Analysis!B{r})", fx["transit_by_year"][y],
                f"='Ex 4.5 Analysis'!B{r}", 0, COUNT)
    b.check(e, f"In Transit, all years (Ex 4.5 Analysis!B{yt})", fx["status"]["In Transit"],
            f"='Ex 4.5 Analysis'!B{yt}", 0, COUNT)
    b.check(e, f"In Transit, due on or after ReviewDate (Ex 4.5 Analysis!B{yt + 1})", fx["due_on_or_after"],
            f"='Ex 4.5 Analysis'!B{yt + 1}", 0, COUNT)
    b.check(e, f"blank ShipmentDate or DeliveryDate (Ex 4.5 Analysis!B{yt + 2})", fx["blank_dates"],
            f"='Ex 4.5 Analysis'!B{yt + 2}", 0, COUNT)
    b.check(e, "shipments in view with the slicer cleared (SUBTOTAL)", fx["n"], f"='Ex 4.5 Analysis'!B{r1 + 1}", 0, COUNT)
    for s, r in rrow.items():
        b.check(e, f"{s}: shipments in view, recorded with the slicer (Ex 4.5 Analysis!B{r})", fx["status"][s],
                f"='Ex 4.5 Analysis'!B{r}", 0, COUNT)
        b.check(e, f"{s}: blank TrackingNumber in view, recorded (Ex 4.5 Analysis!C{r})", fx["blank_by"].get(s, 0),
                f"='Ex 4.5 Analysis'!C{r}", 0, COUNT)
    b.check(e, f"second count, ReviewDate {review2} (Ex 4.5 Analysis!B{r3 + 1})", fx["late2"],
            f"='Ex 4.5 Analysis'!B{r3 + 1}", 0, COUNT)
    b.check(e, f"change from the first count (Ex 4.5 Analysis!B{r3 + 2})", fx["late2"] - fx["late"],
            f"='Ex 4.5 Analysis'!B{r3 + 2}", 0, COUNT)


# --- Exercise 4.6 ------------------------------------------------------------------------------------------------

def ex4_6(b: ExerciseBuild) -> None:
    fx = facts()["ex6"]
    wb = b.wb
    ws = new_sheet(b, "Ex 4.6")
    # (1) the approvals, with the two dates as the Date type; the Employee Table for the names and titles of (4)
    xl.add_query(wb, "PriceOverrideApproval", nav(b, 8, "PriceOverrideApproval",
                                                  {"RequestDate": "type date", "ApprovedDate": "type date"}))
    xl.add_query(wb, "Employee", nav(b, 74, "Employee", extra=[
        ("Removed Other Columns", pq.select_columns(["EmployeeID", "EmployeeName", "JobTitle"]))]))
    lo = load(b, "PriceOverrideApproval", "Ex 4.6 PriceOverrideApproval", after=ws)
    emp = load(b, "Employee", "Ex 4.6 Employee", after=wb.Worksheets("Ex 4.6 PriceOverrideApproval"))
    assert emp.ListRows.Count > 0
    tws = wb.Worksheets("Ex 4.6 PriceOverrideApproval")
    for c in ("RequestDate", "ApprovedDate"):
        lo.ListColumns(c).DataBodyRange.NumberFormat = DATEF
    note(tws, "A1", "Exercise 4.6 loads this Table into a new workbook; here it shares the solutions file. The "
                    "Employee query (EmployeeID, EmployeeName, JobTitle) imports the Employee worksheet of "
                    "CharlesRiver.xlsx for the names and job titles of requirement (4).")
    # (2) the discount from the reference price, and a helper column for the self-approval count of (3)
    add_column(lo, "DiscountFromReference", "=1-[@ApprovedUnitPrice]/[@ReferenceUnitPrice]", "0.0%")
    add_column(lo, "SelfApproved", "=[@RequestedByEmployeeID]=[@ApprovedByEmployeeID]")
    rq, ap = col(lo, "RequestedByEmployeeID"), col(lo, "ApprovedByEmployeeID")
    # (3) the two highlight rules
    row_rule(tws, lo.DataBodyRange, f'=${ap}2=""', AMBER)
    row_rule(tws, lo.DataBodyRange, f"=${rq}2=${ap}2", CORAL)
    # (5) the sort
    sort_table(lo, [("DiscountFromReference", xl.XL_DESCENDING)])
    tws.Range("A1").Select()

    P = "PriceOverrideApproval"
    heading(ws, "A1", "Exercise 4.6: Reviewing Price Override Approvals", 14)
    widths(ws, {"A": 40, "B": 18, "C": 22, "D": 12, "E": 16, "F": 16, "G": 14, "H": 12})
    values(ws, {"A3": "Requests", "A4": "Blank ApprovedByEmployeeID (amber)",
                "A5": "Approved by the requester (coral; SelfApproved column)", "A6": "Distinct approvers",
                "A7": "Approver (EmployeeID)"})
    formulas(ws, {"B3": f"=ROWS({P}[PriceOverrideApprovalID])", "B4": f'=COUNTIFS({P}[ApprovedByEmployeeID],"")',
                  "B5": f"=COUNTIFS({P}[SelfApproved],TRUE)",
                  "B6": f'=COUNTA(UNIQUE(FILTER({P}[ApprovedByEmployeeID],{P}[ApprovedByEmployeeID]<>"")))',
                  "B7": f'=TEXTJOIN(", ",TRUE,UNIQUE(FILTER({P}[ApprovedByEmployeeID],{P}[ApprovedByEmployeeID]<>"")))'})
    ws.Range("B3:B6").NumberFormat = COUNT
    ws.Range("B7").HorizontalAlignment = -4152
    note(ws, "A5", "COUNTIFS cannot compare two columns of the same row, so the SelfApproved calculated column "
                   "(=[@RequestedByEmployeeID]=[@ApprovedByEmployeeID]) carries the comparison, and COUNTIFS counts "
                   "its TRUE values. The coral rule uses the same comparison.")
    statuses = sorted(fx["status"])
    values(ws, {"A9": "Status", "B9": "Requests", "C9": "Blank approver", "D9": "Self-approved"})
    bold(ws, "A9:D9")
    srow = {}
    for i, s in enumerate(statuses):
        r = 10 + i
        srow[s] = r
        values(ws, {f"A{r}": s})
        formulas(ws, {f"B{r}": f"=COUNTIFS({P}[Status],$A{r})",
                      f"C{r}": f'=COUNTIFS({P}[Status],$A{r},{P}[ApprovedByEmployeeID],"")',
                      f"D{r}": f"=COUNTIFS({P}[Status],$A{r},{P}[SelfApproved],TRUE)"})
    tr = 10 + len(statuses)
    values(ws, {f"A{tr}": "Total"})
    for cl in "BCD":
        ws.Range(f"{cl}{tr}").Formula2 = f"=SUM({cl}10:{cl}{tr - 1})"
    bold(ws, f"A{tr}:D{tr}")
    ws.Range(f"B10:D{tr}").NumberFormat = COUNT

    # the slicer on Status, with SUBTOTAL, recorded for each status
    r1 = tr + 2
    heading(ws, f"A{r1}", "The slicer on Status (click a status; SUBTOTAL follows the rows in view)", 11)
    values(ws, {f"A{r1 + 1}": "Requests in view", f"A{r1 + 2}": "With an approver, in view"})
    formulas(ws, {f"B{r1 + 1}": f"=SUBTOTAL(103,{P}[PriceOverrideApprovalID])",
                  f"B{r1 + 2}": f"=SUBTOTAL(103,{P}[ApprovedByEmployeeID])"})
    ws.Range(f"B{r1 + 1}:B{r1 + 2}").NumberFormat = COUNT
    cache = add_slicer(b, lo, "Status", ws, "RequestStatus", f"F{r1}", height=80)
    rec = record_with_slicer(b, cache, lo, "Status", statuses, ws, [f"B{r1 + 1}", f"B{r1 + 2}"])
    r2 = r1 + 4
    values(ws, {f"A{r2}": "Recorded with the slicer", f"B{r2}": "Requests in view", f"C{r2}": "With an approver"})
    bold(ws, f"A{r2}:C{r2}")
    rrow = {}
    for i, s in enumerate(statuses):
        r = r2 + 1 + i
        rrow[s] = r
        values(ws, {f"A{r}": s, f"B{r}": rec[s][0], f"C{r}": rec[s][1]})
    ws.Range(f"B{r2 + 1}:C{r2 + len(statuses)}").NumberFormat = COUNT
    note(ws, f"A{r2}", "Recorded values: the builder clicked each Status button in turn and copied what the SUBTOTAL "
                       "cells showed, then cleared the slicer. Every Pending request lacks an approver, and every "
                       "Approved request has one.")

    # (4) the grid by requester, with names and job titles from the Employee Table
    g0 = r2 + len(statuses) + 2
    heading(ws, f"A{g0}", "Requests by requesting employee", 11)
    heads = ["RequestedByEmployeeID", "EmployeeName", "JobTitle", "Requests", "Approved by someone else",
             "Approved by the requester", "Not yet approved"]
    for j, h in enumerate(heads):
        ws.Cells(g0 + 1, 1 + j).Value = h
    bold(ws, f"A{g0 + 1}:G{g0 + 1}")
    ws.Range(f"A{g0 + 1}:G{g0 + 1}").WrapText = True
    grow = {}
    for i, row in enumerate(fx["grid"]):
        r = g0 + 2 + i
        grow[row["id"]] = r
        req = f"{P}[RequestedByEmployeeID],$A{r}"
        values(ws, {f"A{r}": row["id"]})
        ws.Range(f"A{r}").HorizontalAlignment = -4131
        formulas(ws, {f"B{r}": f"=XLOOKUP($A{r},Employee[EmployeeID],Employee[EmployeeName])",
                      f"C{r}": f"=XLOOKUP($A{r},Employee[EmployeeID],Employee[JobTitle])",
                      f"D{r}": f"=COUNTIFS({req})",
                      f"E{r}": f'=COUNTIFS({req},{P}[ApprovedByEmployeeID],"<>"&$A{r},{P}[ApprovedByEmployeeID],"<>")',
                      f"F{r}": f"=COUNTIFS({req},{P}[ApprovedByEmployeeID],$A{r})",
                      f"G{r}": f'=COUNTIFS({req},{P}[ApprovedByEmployeeID],"")'})
    gt = g0 + 2 + len(fx["grid"])
    values(ws, {f"A{gt}": "Total"})
    for cl in "DEFG":
        ws.Range(f"{cl}{gt}").Formula2 = f"=SUM({cl}{g0 + 2}:{cl}{gt - 1})"
    bold(ws, f"A{gt}:G{gt}")
    ws.Range(f"D{g0 + 2}:G{gt}").NumberFormat = COUNT
    note(ws, f"G{g0 + 1}", "Added so that each row adds up: requests with no approver yet (the Pending ones).")

    # (5) the range of discounts, and (6) the evidence for the follow-up on the pending requests
    d0 = gt + 2
    heading(ws, f"A{d0}", "DiscountFromReference (the Table is sorted from largest to smallest)", 11)
    values(ws, {f"A{d0 + 1}": "Smallest", f"A{d0 + 2}": "Largest", f"A{d0 + 3}": "Request with the largest (first row)"})
    formulas(ws, {f"B{d0 + 1}": f"=MIN({P}[DiscountFromReference])", f"B{d0 + 2}": f"=MAX({P}[DiscountFromReference])",
                  f"B{d0 + 3}": f"=INDEX({P}[PriceOverrideApprovalID],1)"})
    ws.Range(f"B{d0 + 1}:B{d0 + 2}").NumberFormat = "0.0%"
    p0 = d0 + 5
    heading(ws, f"A{p0}", "Follow-up: were the pending requests used on sales? (SalesInvoiceLine filtered on "
                          "SalesOrderLineID)", 11)
    heads = ["PriceOverrideApprovalID", "SalesOrderLineID", "ApprovedUnitPrice", "Invoice lines",
             "At the ApprovedUnitPrice", "PricingMethod"]
    for j, h in enumerate(heads):
        ws.Cells(p0 + 1, 1 + j).Value = h
    bold(ws, f"A{p0 + 1}:F{p0 + 1}")
    ws.Range(f"A{p0 + 1}:F{p0 + 1}").WrapText = True
    prow = {}
    for i, p in enumerate(fx["pending"]):
        r = p0 + 2 + i
        prow[p["id"]] = r
        sil = f"SalesInvoiceLine[SalesOrderLineID],$B{r}"
        values(ws, {f"A{r}": p["id"]})
        ws.Range(f"A{r}").HorizontalAlignment = -4131
        formulas(ws, {f"B{r}": f"=XLOOKUP($A{r},{P}[PriceOverrideApprovalID],{P}[SalesOrderLineID])",
                      f"C{r}": f"=XLOOKUP($A{r},{P}[PriceOverrideApprovalID],{P}[ApprovedUnitPrice])",
                      f"D{r}": f"=COUNTIFS({sil})",
                      f"E{r}": f'=COUNTIFS({sil},SalesInvoiceLine[UnitPrice],">="&($C{r}-0.005),'
                               f'SalesInvoiceLine[UnitPrice],"<="&($C{r}+0.005))',
                      f"F{r}": f'=TEXTJOIN(", ",TRUE,UNIQUE(FILTER(SalesInvoiceLine[PricingMethod],'
                               f'SalesInvoiceLine[SalesOrderLineID]=$B{r})))'})
        ws.Range(f"B{r}").HorizontalAlignment = -4131
    ws.Range(f"C{p0 + 2}:C{p0 + 1 + len(fx['pending'])}").NumberFormat = MONEY

    # the model answers
    top = fx["top"]
    pend = fx["pending"]
    ids = and_join(p["id"] for p in pend)
    lines = and_join(p["line"] for p in pend)
    n_inv = sum(p["invoiced"] for p in pend)
    methods = sorted(set().union(*(p["methods"] for p in pend)))
    approver = fx["approvers"][0] if len(fx["approvers"]) == 1 else None
    assert approver is not None, "more than one approver: the memo's wording no longer holds"
    a_name, a_title = fx["names"][approver]
    own = next(r for r in fx["grid"] if r["id"] == approver)
    assert own["open"] == len(pend), "the memo says the approver requested every pending request"
    nxt = answer(ws, p0 + 3 + len(pend), "Model answer (5)", [
        f"Sorted from the largest, the approved prices run from {pct(fx['high'])} below the reference price "
        f"(request {top['id']}) down to {pct(fx['low'])}: every override is a modest reduction of about "
        f"{round(100 * fx['low'])} to {round(100 * fx['high'])} percent, none of them extreme, so the risk lies in "
        "who approved them rather than in their size."])
    answer(ws, nxt, "Model answer (6): memo", [
        f"To: Audit senior. Subject: Preliminary review of price override approvals ({fx['n']} requests; "
        f"{fx['status'].get('Approved', 0)} Approved, {fx['status'].get('Pending', 0)} Pending).",
        f"Exception 1, approvals made by the requester: all {fx['status'].get('Approved', 0)} approvals were made by "
        f"one person, EmployeeID {approver} ({a_name}, {a_title}), who also requested {own['n']} of the "
        f"{fx['n']} overrides and approved {own['own']} of her own requests. A control in which the only approver is "
        "also a requester is not designed to prevent an unjustified price: nobody independent reviews the "
        "manager's own overrides, and nobody can approve when she is the requester.",
        f"Exception 2, requests without an approval: requests {ids} are Pending, with no approver and no approval "
        f"date, and all {len(pend)} were requested by the {a_title}. A pending request should never reach an "
        "invoice, so the design question is whether the system blocks a price until it is approved.",
        "Follow-up procedures: (a) obtain the pricing policy and authority matrix, and ask who may approve "
        f"overrides and whether self-approval is allowed; (b) for the pending requests, filter SalesInvoiceLine on "
        f"their SalesOrderLineIDs ({lines}) and compare the billed UnitPrice with the ApprovedUnitPrice: this "
        f"workbook finds {n_inv} invoice lines billed at the pending prices under "
        f"{and_join(methods)} pricing methods, so the overrides were used without approval and the invoices hide "
        "them; (c) for a sample of the self-approved overrides, inspect the documented reason and the customer "
        "agreement; (d) recommend an independent approver, such as the controller, for the manager's own requests "
        "and a system block on unapproved prices."])

    settle(b)
    e = "4.6"
    b.check(e, "requests (Ex 4.6!B3)", fx["n"], "='Ex 4.6'!B3", 0, COUNT)
    b.check(e, "RequestDate holds dates (first row)", True, f"=ISNUMBER(INDEX({P}[RequestDate],1))", 0, TEXT)
    b.check(e, "blank ApprovedByEmployeeID (Ex 4.6!B4)", fx["blank"], "='Ex 4.6'!B4", 0, COUNT)
    b.check(e, "approved by the requester (Ex 4.6!B5)", fx["self"], "='Ex 4.6'!B5", 0, COUNT)
    b.check(e, "distinct approvers (Ex 4.6!B6)", len(fx["approvers"]), "='Ex 4.6'!B6", 0, COUNT)
    b.check(e, "the approver's EmployeeID (Ex 4.6!B7, TEXTJOIN of the approvers)", approver, "=--'Ex 4.6'!B7", 0, COUNT)
    for s, r in srow.items():
        b.check(e, f"{s} requests (Ex 4.6!B{r})", fx["status"][s], f"='Ex 4.6'!B{r}", 0, COUNT)
        b.check(e, f"{s}: blank approver (Ex 4.6!C{r})", fx["blank_by"].get(s, 0), f"='Ex 4.6'!C{r}", 0, COUNT)
        b.check(e, f"{s}: self-approved (Ex 4.6!D{r})", fx["self_by"].get(s, 0), f"='Ex 4.6'!D{r}", 0, COUNT)
    b.check(e, "requests in view with the slicer cleared (SUBTOTAL)", fx["n"], f"='Ex 4.6'!B{r1 + 1}", 0, COUNT)
    for s, r in rrow.items():
        b.check(e, f"{s}: requests in view, recorded with the slicer (Ex 4.6!B{r})", fx["status"][s], f"='Ex 4.6'!B{r}",
                0, COUNT)
        b.check(e, f"{s}: with an approver, recorded (Ex 4.6!C{r})", fx["status"][s] - fx["blank_by"].get(s, 0),
                f"='Ex 4.6'!C{r}", 0, COUNT)
    for row in fx["grid"]:
        r = grow[row["id"]]
        b.check(e, f"requester {row['id']}: name (Ex 4.6!B{r})", row["name"], f"='Ex 4.6'!B{r}", 0, TEXT)
        b.check(e, f"requester {row['id']}: job title (Ex 4.6!C{r})", row["title"], f"='Ex 4.6'!C{r}", 0, TEXT)
        b.check(e, f"requester {row['id']}: requests (Ex 4.6!D{r})", row["n"], f"='Ex 4.6'!D{r}", 0, COUNT)
        b.check(e, f"requester {row['id']}: approved by someone else (Ex 4.6!E{r})", row["other"], f"='Ex 4.6'!E{r}",
                0, COUNT)
        b.check(e, f"requester {row['id']}: approved by the requester (Ex 4.6!F{r})", row["own"], f"='Ex 4.6'!F{r}",
                0, COUNT)
        b.check(e, f"requester {row['id']}: not yet approved (Ex 4.6!G{r})", row["open"], f"='Ex 4.6'!G{r}", 0, COUNT)
    b.check(e, f"grid total equals the requests (Ex 4.6!D{gt})", fx["n"], f"='Ex 4.6'!D{gt}", 0, COUNT)
    b.check(e, f"smallest DiscountFromReference (Ex 4.6!B{d0 + 1})", round(fx["low"], 9), f"='Ex 4.6'!B{d0 + 1}",
            1e-9, PCT)
    b.check(e, f"largest DiscountFromReference (Ex 4.6!B{d0 + 2})", round(fx["high"], 9), f"='Ex 4.6'!B{d0 + 2}",
            1e-9, PCT)
    if fx["top_unique"]:
        b.check(e, f"first row after the sort, the largest discount (Ex 4.6!B{d0 + 3})", top["id"],
                f"='Ex 4.6'!B{d0 + 3}", 0, COUNT)
    for p in pend:
        r = prow[p["id"]]
        b.check(e, f"pending request {p['id']}: SalesOrderLineID (Ex 4.6!B{r})", p["line"], f"='Ex 4.6'!B{r}", 0, COUNT)
        b.check(e, f"pending request {p['id']}: invoice lines (Ex 4.6!D{r})", p["invoiced"], f"='Ex 4.6'!D{r}", 0, COUNT)
        b.check(e, f"pending request {p['id']}: billed at the ApprovedUnitPrice (Ex 4.6!E{r})", p["at_price"],
                f"='Ex 4.6'!E{r}", 0, COUNT)


EXERCISES = [("4.1", ex4_1), ("4.2", ex4_2), ("4.3", ex4_3), ("4.4", ex4_4), ("4.5", ex4_5), ("4.6", ex4_6)]
