"""Chapter 6 Exercises - Solutions.xlsx: the solutions to the exercises of Chapter 6.

The workbook is a copy of Charles River Furniture Analysis.xlsx at the end of Tutorial 6.3 (the "fresh copy of your
analysis workbook" the exercises start from). Each function works one exercise as a reader would:

- the queries the exercise names, with the Power Query Editor's step names (Exercise 6.1's TrialBalance and
  ChartOfAccounts), and no tutorial query renamed or edited;
- the worksheets the exercise names (TrialBalance and IncomeStatement in Exercise 6.1), otherwise "Ex 6.N";
- PivotTables on the pivot cache of the tutorials' InvoiceLines PivotTables, so Tutorial 6.2's MarginPct calculated
  field is at hand, read with GETPIVOTDATA;
- model answers for the written requirements, their numbers computed from the dataset.

Expected values for the checks are computed here from CharlesRiver.sqlite (read-only), independently of Excel. They
agree with the instructor notes, which facts/notes/ch06.py generates from the same data.
"""

from __future__ import annotations

import math
import sqlite3
import statistics
from collections import defaultdict
from functools import lru_cache

from paths import db_uri
from xlbuild import pq, xl
from xlbuild.analysis import first_cache, nav, only_items
from xlbuild.expected import xround
from xlbuild.solutions import COUNT, MONEY, PCT, ExerciseBuild, exercise_info

NOTES = "Solution Notes"
GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories", "Services"]     # the book's order of the item groups
REVENUE_ACCOUNTS = [(4010, "Furniture"), (4020, "Lighting"), (4030, "Textiles"), (4040, "Accessories"),
                    (4080, "Services")]                                         # Exercise 6.1 (5): 4010 to 4040 and 4080
CHART_COLUMNS = ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"]
TYPE_NAMES = {"BKC": "bookcase", "BNH": "bench", "CON": "console table", "CTB": "coffee table", "DSK": "desk",
              "NGT": "nightstand", "SDB": "sideboard", "TBL": "dining table"}   # Chapter 5's Furniture product types
XL_PERCENT_OF_TOTAL = 8                                                         # xlPercentOfTotal (% of Grand Total)
XL_TOTALS_SUM = 1                                                               # xlTotalsCalculationSum
GENERAL = "General"
PRICING = {"Segment Price List": "from segment price lists", "Customer Price List": "from customer price lists",
           "Base List": "from the base list", "Approved Override": "through approved overrides"}   # PricingMethod in prose
DATE = "yyyy-mm-dd"


# --- expected values, from CharlesRiver.sqlite --------------------------------------------------------------------

def _q(sql: str, *args) -> list[tuple]:
    con = sqlite3.connect(db_uri(), uri=True)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


@lru_cache(maxsize=None)
def invoice_lines() -> tuple[dict, ...]:
    """InvoiceLines as Tutorials 5.3 to 6.3 build it: each line with its invoice, item, and customer, the fiscal year
    and quarter of its InvoiceDate, and the unrounded StdCostAmount and DiscountAmount columns."""
    rows = _q("SELECT l.SalesInvoiceLineID, si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate, i.ItemGroup, i.ItemCode, "
              "i.StandardCost, l.Quantity, l.LineTotal, l.UnitPrice, l.Discount, l.PricingMethod, l.PromotionID, "
              "si.CustomerID, c.CustomerName, c.CustomerSegment, c.Region "
              "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
              "JOIN Item i ON i.ItemID = l.ItemID LEFT JOIN Customer c ON c.CustomerID = si.CustomerID")
    out = []
    for lid, sid, number, d, grp, code, std, qty, lt, up, disc, method, promo, cid, name, seg, reg in rows:
        out.append(dict(id=lid, inv=sid, number=number, date=d, year=int(d[:4]), q=(int(d[5:7]) + 2) // 3, grp=grp,
                        type=code[4:7], qty=qty, lt=lt, std=qty * (std or 0), disc=qty * up * disc, method=method,
                        promo=promo, customer=cid, name=name, segment=seg, region=reg))
    return tuple(out)


def year_lines(y: int) -> list[dict]:
    return [r for r in invoice_lines() if r["year"] == y]


def closes_of(y: int) -> list[str]:
    return [r[0] for r in _q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' "
                             "AND PostingDate = ? ORDER BY EntryNumber", f"{y}-12-31")]


@lru_cache(maxsize=None)
def facts_6_1(y: int) -> dict:
    closes = closes_of(y)
    assert len(closes) == 2, closes
    tb = _q("SELECT a.AccountNumber, a.AccountName, a.AccountType, a.AccountSubType, SUM(g.Debit), SUM(g.Credit) "
            "FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.PostingDate < ? "
            "AND g.VoucherNumber NOT IN (?, ?) GROUP BY g.AccountID ORDER BY a.AccountNumber", f"{y + 1}-01-01", *closes)
    accounts = [dict(number=n, name=nm, type=t, sub=s, bal=dr - cr) for n, nm, t, s, dr, cr in tb]
    bal = {a["number"]: a["bal"] for a in accounts}
    sub = lambda *names: sum(a["bal"] for a in accounts if a["sub"] in names)
    typ = lambda name: sum(a["bal"] for a in accounts if a["type"] == name)
    lines = {}
    lines["opr"] = -sub("Operating Revenue")
    lines["contra"] = -sub("Contra Revenue")
    lines["net"] = lines["opr"] + lines["contra"]
    lines["cogs"] = -sub("COGS")
    lines["gm"] = lines["net"] + lines["cogs"]
    lines["opex"] = -sub("Operating Expense")
    lines["oi"] = lines["gm"] + lines["opex"]
    lines["other"] = -sub("Other Income or Expense", "Other Expense")
    lines["ni"] = lines["oi"] + lines["other"]
    closing = _q("SELECT TotalAmount FROM JournalEntry WHERE EntryNumber = ?", closes[1])[0][0]
    rows = year_lines(y)
    recon = []
    for number, group in REVENUE_ACCOUNTS:
        ledger = -bal.get(number, 0.0)
        il = sum(r["lt"] for r in rows if r["grp"] == group)
        recon.append(dict(account=number, group=group, ledger=ledger, lines=il, diff=round(ledger - il, 2)))
    odd = []
    for sid, number, d in _q("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) = ? "
                             "AND InvoiceNumber LIKE ? ORDER BY SalesInvoiceID", str(y - 1), f"SI-{y}-%"):
        mine = [r for r in invoice_lines() if r["inv"] == sid]
        groups = sorted({r["grp"] for r in mine})
        assert len(groups) == 1, (number, groups)
        posted = _q("SELECT DISTINCT PostingDate FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' "
                    "AND SourceDocumentID = ?", sid)
        shipped = _q("SELECT DISTINCT s.ShipmentDate FROM SalesInvoiceLine l JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID "
                     "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE l.SalesInvoiceID = ? ORDER BY 1", sid)
        odd.append(dict(id=sid, number=number, date=d, group=groups[0], amount=sum(r["lt"] for r in mine),
                        posted=[p[0] for p in posted], shipped=[s[0] for s in shipped]))
    std = sum(r["std"] for r in rows if r["grp"] != "Services")
    product = sum(r["lt"] for r in rows if r["grp"] != "Services")
    total = sum(r["lt"] for r in rows)
    return dict(closes=closes, earlier=[closes_of(y - 2), closes_of(y - 1)], accounts=len(accounts),
                zero=sum(1 for a in accounts if round(a["bal"], 2) == 0),
                debits=sum(max(0.0, a["bal"]) for a in accounts), credits=sum(max(0.0, -a["bal"]) for a in accounts),
                lines=lines, closing=closing, assets=typ("Asset"), liabilities=-typ("Liability"), equity=-typ("Equity"),
                bal=bal, recon=recon, odd=odd,
                cogs_accounts=[(a["number"], a["name"], a["bal"]) for a in accounts if a["sub"] == "COGS"],
                std_margin=(total - sum(r["std"] for r in rows)) / total, product_std_margin=(product - std) / product)


@lru_cache(maxsize=None)
def facts_6_2(y: int) -> dict:
    p = y - 1
    combos: dict[tuple, list] = defaultdict(lambda: [0.0, 0.0])
    for r in invoice_lines():
        if r["year"] in (p, y):
            combos[(r["segment"], r["grp"])][r["year"] - p] += r["lt"]
    grand = sum(v[1] for v in combos.values())
    segs = sorted({k[0] for k in combos}, key=lambda s: -sum(v[1] for k, v in combos.items() if k[0] == s))
    order = sorted(combos, key=lambda k: (segs.index(k[0]), GROUPS.index(k[1])))
    ranked = sorted(combos.items(), key=lambda kv: -kv[1][1])
    large = [(k, v[0], v[1], v[1] / v[0] - 1) for k, v in combos.items() if v[0] >= 500000]
    by = lambda key: {k: sum(r["lt"] for r in invoice_lines() if r["year"] == y and r[key] == k) /
                      sum(r["lt"] for r in invoice_lines() if r["year"] == p and r[key] == k) - 1
                      for k in {r[key] for r in invoice_lines() if r["year"] == y}}
    tot = lambda yr: sum(r["lt"] for r in invoice_lines() if r["year"] == yr)
    seg_share = {s: sum(v[1] for k, v in combos.items() if k[0] == s) / grand for s in segs}
    grp_share = {g: sum(v[1] for k, v in combos.items() if k[1] == g) / grand for g in GROUPS}
    return dict(combos=dict(combos), order=order, grand=grand,
                top=[(k, v[1] / grand, v[1]) for k, v in ranked[:5]],
                up=sorted(large, key=lambda t: -t[3])[:2], down=sorted(large, key=lambda t: t[3])[:2],
                segments=by("segment"), regions=by("region"), total_change=tot(y) / tot(p) - 1,
                seg_share=seg_share, grp_share=grp_share, total=tot(y),
                design_services_only=({k[1] for k in combos if k[0] == "Design Services"} == {"Services"}))


@lru_cache(maxsize=None)
def facts_6_3(y: int) -> dict:
    rows = year_lines(y)
    groups = {}
    for g in GROUPS:
        rev = sum(r["lt"] for r in rows if r["grp"] == g)
        cost = sum(r["std"] for r in rows if r["grp"] == g)
        groups[g] = dict(revenue=rev, margin=rev - cost, pct=(rev - cost) / rev)
    products = [g for g in GROUPS if g != "Services"]
    by_revenue = sorted(products, key=lambda g: -groups[g]["revenue"])
    rev = sum(groups[g]["revenue"] for g in products)
    mar = sum(groups[g]["margin"] for g in products)
    shares = {g: (groups[g]["revenue"] / rev, groups[g]["margin"] / mar) for g in products}
    more = [g for g in by_revenue if shares[g][1] > shares[g][0]]
    types: dict[str, list] = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        if r["grp"] == "Furniture":
            types[r["type"]][0] += r["lt"]
            types[r["type"]][1] += r["std"]
    tpct = {t: (v[0] - v[1]) / v[0] for t, v in types.items()}
    ranked = sorted(tpct, key=lambda t: -tpct[t])
    time_cost = _q("SELECT SUM(ExtendedCost) FROM ServiceTimeEntry WHERE WorkDate BETWEEN ? AND ?",
                   f"{y}-01-01", f"{y}-12-31")[0][0]
    salaries = _q("SELECT SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                  "WHERE a.AccountNumber = 6280 AND g.FiscalYear = ? AND g.VoucherNumber NOT IN (?, ?)", y, *closes_of(y))[0][0]
    services = groups["Services"]["revenue"]
    return dict(groups=groups, by_revenue=by_revenue, shares=shares, more=more, tpct=tpct, types=sorted(types),
                high=ranked[:2], low=ranked[::-1][:2], time_cost=time_cost, time_pct=1 - time_cost / services,
                salaries=salaries, salaries_pct=1 - salaries / services)


@lru_cache(maxsize=None)
def facts_6_4(y: int) -> dict:
    agg: dict[tuple, dict] = defaultdict(lambda: dict(U=0.0, R=0.0, C=0.0, D=0.0))
    for r in year_lines(y):
        if r["grp"] == "Furniture" and r["q"] in (3, 4):
            a = agg[(r["type"], r["q"])]
            a["U"] += r["qty"]
            a["R"] += r["lt"]
            a["C"] += r["std"]
            a["D"] += r["disc"]
    types = sorted({t for t, _ in agg})
    a, b = {t: agg[(t, 3)] for t in types}, {t: agg[(t, 4)] for t in types}
    u3, u4 = sum(v["U"] for v in a.values()), sum(v["U"] for v in b.values())
    q3, q4 = sum(v["R"] - v["C"] for v in a.values()), sum(v["R"] - v["C"] for v in b.values())
    per = lambda v, k: v[k] / v["U"]
    price = sum(b[t]["U"] * (per(b[t], "R") - per(a[t], "R")) for t in types)
    cost = -sum(b[t]["U"] * (per(b[t], "C") - per(a[t], "C")) for t in types)
    volume = (u4 - u3) * q3 / u3
    mix = sum((b[t]["U"] - u4 * a[t]["U"] / u3) * (a[t]["R"] - a[t]["C"]) / a[t]["U"] for t in types)
    promotions = -sum(b[t]["U"] * (per(b[t], "D") - per(a[t], "D")) for t in types)
    top = max(types, key=lambda t: abs(per(b[t], "C") - per(a[t], "C")))
    return dict(types=types, a=a, b=b, q3=q3, q4=q4, change=q4 - q3, price=price, cost=cost, volume=volume, mix=mix,
                promotions=promotions, top=top, p3=per(a[top], "R"), p4=per(b[top], "R"), c3=per(a[top], "C"),
                c4=per(b[top], "C"))


@lru_cache(maxsize=None)
def facts_6_5(y: int) -> dict:
    rows = []
    for g in GROUPS:
        for k in range(1, 5):
            exp = sum(r["lt"] for r in year_lines(y - 1) if r["grp"] == g and r["q"] == k)
            act = sum(r["lt"] for r in year_lines(y) if r["grp"] == g and r["q"] == k)
            diff = act - exp
            rows.append(dict(group=g, q=k, exp=exp, act=act, diff=diff, pct=diff / exp,
                             flagged=abs(diff) > 0.10 * exp and abs(diff) > 50000))
    flagged = [r for r in rows if r["flagged"]]
    missed = sorted((r for r in rows if not r["flagged"]), key=lambda r: -abs(r["diff"]))[:2]
    return dict(rows=rows, flagged=flagged, missed=missed)


@lru_cache(maxsize=None)
def facts_6_6(y: int) -> dict:
    rows = year_lines(y)
    groups = {}
    for g in GROUPS:
        v = [r["lt"] for r in rows if r["grp"] == g]
        promo = sum(1 for r in rows if r["grp"] == g and r["promo"] is not None)
        groups[g] = dict(lines=len(v), revenue=sum(v), mean=statistics.mean(v), median=statistics.median(v),
                         promo_share=promo / len(v))
    revenue = sum(r["lt"] for r in rows)
    customers: dict[int, list] = {}
    for r in rows:
        customers.setdefault(r["customer"], [r["name"], r["segment"], 0.0])[2] += r["lt"]
    ranked = sorted(customers.values(), key=lambda c: -c[2])
    methods: dict[str, list] = defaultdict(lambda: [0, 0.0])
    for r in rows:
        methods[r["method"]][0] += 1
        methods[r["method"]][1] += r["lt"]
    promos: dict[int, list] = defaultdict(lambda: [0, 0.0, [], ""])
    for r in rows:
        if r["promo"] is not None:
            p = promos[r["promo"]]
            p[0] += 1
            p[1] += r["disc"]
            p[2].append(r["date"])
    starts = {pid: (s, e) for pid, s, e in _q("SELECT PromotionID, EffectiveStartDate, EffectiveEndDate FROM PromotionProgram")}
    late = [pid for pid in sorted(promos) if starts[pid][0][:4] == str(y - 1)]
    late_dates = [d for pid in late for d in promos[pid][2]]
    return dict(groups=groups, revenue=revenue, lines=len(rows), customers=len(customers),
                top5=sum(c[2] for c in ranked[:5]) / revenue, top10=sum(c[2] for c in ranked[:10]) / revenue,
                top10_segments=sorted({c[1] for c in ranked[:10]}), largest=[c[0] for c in ranked[:5]],
                methods={m: (v[0], v[1] / revenue) for m, v in methods.items()},
                promos={pid: (v[0], v[1], min(v[2]), max(v[2])) for pid, v in promos.items()}, starts=starts,
                late=late, late_first=min(late_dates), late_last=max(late_dates),
                promo_lines=sum(v[0] for v in promos.values()), promo_discount=sum(v[1] for v in promos.values()),
                reversed=[pid for pid in sorted(promos) if starts[pid][1] < starts[pid][0]])


# --- workbook helpers ----------------------------------------------------------------------------------------------

def money(x: float) -> str:
    """An amount as Excel displays it (rounded half away from zero, so a median of 2,006.895 reads 2,006.90)."""
    return f"{xround(x, 2):,.2f}"


def pct(x: float, places: int = 1) -> str:
    return f"{xround(100 * x, places):.{places}f}%"


def spct(x: float, places: int = 1) -> str:
    return f"{xround(100 * x, places):+.{places}f}%"


def words(n: int, capital: bool = False) -> str:
    text = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][n] if n <= 10 else str(n)
    return text[0].upper() + text[1:] if capital else text


def month_name(iso: str) -> str:
    import calendar
    return calendar.month_name[int(iso[5:7])]


def serial(iso: str) -> int:
    """An ISO date as Excel's serial number (a date written into a cell as text would turn into one)."""
    from datetime import date
    return (date.fromisoformat(iso[:10]) - date(1899, 12, 30)).days


def q(text: str) -> str:
    """A text argument of a formula."""
    return '"' + text.replace('"', '""') + '"'


def gpd(data: str, anchor: str, *pairs) -> str:
    """GETPIVOTDATA(data, anchor, field, item, ...); items are formula text (a quoted string, a number, or a cell)."""
    return f"GETPIVOTDATA({q(data)},{anchor}" + "".join(f",{q(f)},{v}" for f, v in pairs) + ")"


def ref(ws, pt) -> str:
    """The sheet-qualified top-left cell of a PivotTable, the reference GETPIVOTDATA needs."""
    return f"'{ws.Name}'!{pt.TableRange1.Cells(1, 1).Address}"


def local(pt) -> str:
    return pt.TableRange1.Cells(1, 1).Address


def end_row(pt) -> int:
    rng = pt.TableRange2
    return rng.Row + rng.Rows.Count - 1


def end_col(pt) -> int:
    rng = pt.TableRange2
    return rng.Column + rng.Columns.Count - 1


def col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def put(ws, cells: dict[str, object]) -> None:
    for addr, v in cells.items():
        if isinstance(v, str) and v.startswith("="):
            ws.Range(addr).Formula2 = v
        else:
            ws.Range(addr).Value = v


def bold(ws, addr: str) -> None:
    ws.Range(addr).Font.Bold = True


def heading(ws, addr: str, text: str) -> None:
    ws.Range(addr).Value = text
    ws.Range(addr).Font.Bold = True


def title(ws, chapter: int, n: int) -> None:
    ws.Range("A1").Value = f"Exercise {chapter}.{n}: {exercise_info(chapter, n)['title']}"
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 13


def new_sheet(b: ExerciseBuild, name: str):
    return xl.sheet(b.wb, name, before=b.wb.Worksheets(NOTES))


def pivot(b: ExerciseBuild, ws, cell: str, name: str):
    """A PivotTable of InvoiceLines on the cache the tutorials' PivotTables share (with their calculated fields)."""
    return first_cache(b).CreatePivotTable(TableDestination=ws.Range(cell), TableName=name)


def page(pt, field: str, item: str) -> None:
    pf = pt.PivotFields(field)
    pf.Orientation = xl.XL_PAGE
    pf.CurrentPage = item


def years(pt, keep: tuple[int, ...]) -> None:
    for item in pt.PivotFields("FiscalYear").PivotItems():
        if int(float(item.Name)) not in keep:
            item.Visible = False


def data_field(pt, field: str, caption: str, fmt: str, function: int = xl.XL_SUM):
    df = pt.AddDataField(pt.PivotFields(field), caption, function)
    df.NumberFormat = fmt
    return df


def load_to(wb, name: str, ws, cell: str):
    """Load a query as an Excel Table at a cell of an existing worksheet (Close & Load To, Existing worksheet)."""
    connection = (f"OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location={name};"
                  "Extended Properties=\"\"")
    lo = ws.ListObjects.Add(xl.XL_SRC_EXTERNAL, connection, None, xl.XL_YES, ws.Range(cell))
    qt = lo.QueryTable
    qt.CommandType = xl.XL_CMD_SQL
    qt.CommandText = [f"SELECT * FROM [{name}]"]
    qt.RowNumbers = False
    qt.FillAdjacentFormulas = False
    qt.PreserveFormatting = True
    qt.RefreshOnFileOpen = False
    qt.BackgroundQuery = False
    qt.AdjustColumnWidth = True
    qt.PreserveColumnInfo = True
    qt.Refresh(False)
    lo.Name = name
    conn = qt.WorkbookConnection
    conn.Name = f"Query - {name}"
    conn.Description = f"Connection to the '{name}' query in the workbook."
    return lo


def model_answer(ws, row: int, label: str, paragraphs: list[str], last_col: int = 8, note: str | None = None) -> int:
    """A labeled model answer: one merged, wrapped cell per paragraph across columns A to last_col, each tall enough
    for its text. Returns the next free row."""
    ws.Cells(row, 1).Value = label
    ws.Cells(row, 1).Font.Bold = True
    if note:
        ws.Cells(row, 1).AddComment(note)
    width = sum(ws.Columns(c).ColumnWidth for c in range(1, last_col + 1))
    r = row + 1
    for text in paragraphs:
        rng = ws.Range(ws.Cells(r, 1), ws.Cells(r, last_col))
        rng.Merge()
        rng.WrapText = True
        rng.VerticalAlignment = -4160                       # top
        ws.Cells(r, 1).Value = text
        lines = math.ceil(len(text) / max(20.0, width * 1.05)) + 1
        ws.Rows(r).RowHeight = min(409, 15 * lines)
        r += 1
    return r + 1


def widths(ws, spec: dict[str, float]) -> None:
    for cols, w in spec.items():
        ws.Columns(cols).ColumnWidth = w


# --- Exercise 6.1 ----------------------------------------------------------------------------------------------------

def ex6_1(b: ExerciseBuild) -> None:
    wb, y = b.wb, b.year
    f = facts_6_1(y)
    c1, c2 = f["closes"]
    L = f["lines"]

    # (1) the trial balance query and the chart of accounts
    group_by = ('Table.Group({prev}, {"AccountID"}, {{"Debit", each List.Sum([Debit]), type nullable number}, '
                '{"Credit", each List.Sum([Credit]), type nullable number}})')
    xl.add_query(wb, "TrialBalance", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", pq.select_rows(f"[PostingDate] < #datetime({y + 1}, 1, 1, 0, 0, 0)")),
        ("Filtered Rows1", pq.select_rows(f'([VoucherNumber] <> "{c1}" and [VoucherNumber] <> "{c2}")')),
        ("Grouped Rows", group_by),
        ("Merged Queries", pq.merge("ChartOfAccounts", "AccountID", "AccountID", "ChartOfAccounts")),
        ("Expanded ChartOfAccounts", pq.expand("ChartOfAccounts", CHART_COLUMNS[1:])),
        ("Sorted Rows", 'Table.Sort({prev},{{"AccountNumber", Order.Ascending}})')]))
    xl.add_query(wb, "ChartOfAccounts", nav(b, 1, "Account", extra=[
        ("Removed Other Columns", pq.select_columns(CHART_COLUMNS))]))          # Enable Load cleared: not loaded
    tb_ws = new_sheet(b, "TrialBalance")
    lo = load_to(wb, "TrialBalance", tb_ws, "A1")

    # (2) balances and the Total Row
    xl.add_column(lo, "Balance", "=[@Debit]-[@Credit]", MONEY)
    xl.add_column(lo, "DebitBalance", "=MAX(0,[@Balance])", MONEY)
    xl.add_column(lo, "CreditBalance", "=MAX(0,-[@Balance])", MONEY)
    for name in ("Debit", "Credit"):
        lo.ListColumns(name).DataBodyRange.NumberFormat = MONEY
    lo.ShowTotals = True
    for name in ("DebitBalance", "CreditBalance"):
        lo.ListColumns(name).TotalsCalculation = XL_TOTALS_SUM
    lo.TotalsRowRange.Cells(1, 1).Value = "Total"
    lo.TotalsRowRange.NumberFormat = MONEY
    tb_ws.Columns("A:J").AutoFit()

    # (3) the common-size income statement, (4) its two checks
    ist = new_sheet(b, "IncomeStatement")
    # requirement (4): the journal entries, imported as the query JournalEntries (as the exercise says), so that the
    # comparison with the closing entry's TotalAmount stays live
    xl.add_query(wb, "JournalEntries", nav(b, 2, "JournalEntry", extra=[
        ("Removed Other Columns", pq.select_columns(["EntryNumber", "PostingDate", "EntryType", "TotalAmount"]))]))
    ce = load_to(wb, "JournalEntries", new_sheet(b, "JournalEntries"), "A1")
    ce.ListColumns("PostingDate").DataBodyRange.NumberFormat = DATE
    ce.ListColumns("TotalAmount").DataBodyRange.NumberFormat = MONEY
    sumifs = lambda kind, key: f"SUMIFS(TrialBalance[Balance],TrialBalance[{kind}],{q(key)})"
    put(ist, {"A1": f"Fiscal {y}", "B1": "Amount", "C1": "% of net revenue",
              "A2": "Operating revenue", "B2": f"=-{sumifs('AccountSubType', 'Operating Revenue')}",
              "A3": "Sales returns and allowances", "B3": f"=-{sumifs('AccountSubType', 'Contra Revenue')}",
              "A4": "Net revenue", "B4": "=B2+B3",
              "A5": "Cost of goods sold", "B5": f"=-{sumifs('AccountSubType', 'COGS')}",
              "A6": "Gross margin", "B6": "=B4+B5",
              "A7": "Operating expenses", "B7": f"=-{sumifs('AccountSubType', 'Operating Expense')}",
              "A8": "Operating income", "B8": "=B6+B7",
              "A9": "Other income and expense",
              "B9": f"=-{sumifs('AccountSubType', 'Other Income or Expense')}-{sumifs('AccountSubType', 'Other Expense')}",
              "A10": "Net income", "B10": "=B8+B9"})
    for r in range(2, 11):
        ist.Range(f"C{r}").Formula = f"=B{r}/$B$4"
    ist.Range("B2:B10").NumberFormat = MONEY
    ist.Range("C2:C10").NumberFormat = PCT
    for addr in ("A1:C1", "A4:C4", "A6:C6", "A8:C8", "A10:C10"):
        bold(ist, addr)
    heading(ist, "A12", "Balance sheet check (SUMIFS by AccountType)")
    put(ist, {"A13": "Assets", "B13": f"={sumifs('AccountType', 'Asset')}",
              "A14": "Liabilities", "B14": f"=-{sumifs('AccountType', 'Liability')}",
              "A15": "Equity", "B15": f"=-{sumifs('AccountType', 'Equity')}",
              "A16": "Net income", "B16": "=B10",
              "A17": "Liabilities and equity, with net income", "B17": "=SUM(B14:B16)",
              "A18": "Difference", "B18": "=ROUND(B13-B17,2)"})
    heading(ist, "A20", f"Closing entry check ({c2})")
    put(ist, {"A21": f"TotalAmount of {c2}", "B21": f'=SUMIFS(JournalEntries[TotalAmount],JournalEntries[EntryNumber],"{c2}")',
              "A22": "Net income less the closing entry", "B22": "=ROUND(B10-B21,2)"})
    ist.Range("B13:B22").NumberFormat = MONEY
    heading(ist, "A24", "Cost of goods sold by account")
    put(ist, {"A25": "AccountNumber", "B25": "AccountName", "C25": "Balance",
              "A26": '=FILTER(HSTACK(TrialBalance[AccountNumber],TrialBalance[AccountName],TrialBalance[Balance]),'
                     'TrialBalance[AccountSubType]="COGS")'})
    bold(ist, "A25:C25")
    ist.Range("C26:C40").NumberFormat = MONEY
    widths(ist, {"A": 40, "B": 30, "C": 18, "E:H": 18})
    ist.Columns("G").ColumnWidth = 48

    # (5) the revenue reconciliation, on Ex 6.1
    ws = new_sheet(b, "Ex 6.1")
    title(ws, 6, 1)
    heading(ws, "A12", f"Invoices numbered in fiscal {y} but dated in fiscal {y - 1} (Exercise 5.2)")
    put(ws, {"A13": "SalesInvoiceID", "B13": "InvoiceNumber", "C13": "InvoiceDate", "D13": "Item group",
             "E13": "Line total",
             "A14": (f'=FILTER(SalesInvoice[[SalesInvoiceID]:[InvoiceDate]],(SalesInvoice[FiscalYear]={y - 1})*'
                     f'(LEFT(SalesInvoice[InvoiceNumber],7)="SI-{y}"))'),
             "D14": "=XLOOKUP(CHOOSECOLS(A14#,1),InvoiceLines[SalesInvoiceID],InvoiceLines[ItemGroup])",
             "E14": "=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[SalesInvoiceID],CHOOSECOLS(A14#,1))"})
    heading(ws, "A3", f"Revenue reconciliation, fiscal {y}: product revenue accounts against InvoiceLines")
    heads = ["Account", "Item group", "Account balance", f"InvoiceLines {y}", "Difference",
             "Explained by the invoices below", "Unexplained"]
    for i, h in enumerate(heads):
        ws.Cells(4, 1 + i).Value = h
    bold(ws, "A4:G4")
    for i, (number, group) in enumerate(REVENUE_ACCOUNTS):
        r = 5 + i
        put(ws, {f"A{r}": number, f"B{r}": group,
                 f"C{r}": f"=-SUMIFS(TrialBalance[Balance],TrialBalance[AccountNumber],$A{r})",
                 f"D{r}": f"=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$B{r},InvoiceLines[FiscalYear],{y})",
                 f"E{r}": f"=ROUND(C{r}-D{r},2)",
                 f"F{r}": (f"=SUM(SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$B{r},"
                           f"InvoiceLines[SalesInvoiceID],CHOOSECOLS($A$14#,1)))"),
                 f"G{r}": f"=ROUND(E{r}-F{r},2)"})
    put(ws, {"A10": "Total", **{f"{c}10": f"=SUM({c}5:{c}9)" for c in "CDEFG"}})
    bold(ws, "A10:G10")
    ws.Range("C5:G10").NumberFormat = MONEY
    bold(ws, "A13:E13")
    ws.Range("C14:C20").NumberFormat = DATE
    ws.Range("E14:E20").NumberFormat = MONEY
    widths(ws, {"A": 16, "B": 18, "C": 18, "D": 18, "E": 16, "F": 30, "G": 14, "H": 4})

    # written answers: (2), (5), and (6)
    e1, e2 = f["earlier"]
    odd = f["odd"]
    early = [i for i in odd if any(s[:4] == str(y - 1) for s in i["shipped"])]
    later = [i for i in odd if i not in early]
    assert len(early) == 1 and later and all(len(set(i["posted"])) == 1 for i in odd), odd
    e = early[0]
    later_dates = sorted({s for i in later for s in i["shipped"]})
    posted = odd[0]["posted"][0]
    diffs = [r for r in f["recon"] if r["diff"] != 0]
    net = L["net"]
    cogs = {n: v for n, _, v in f["cogs_accounts"]}
    std_cogs = sum(v for n, v in cogs.items() if n in (5010, 5020, 5030, 5040))
    gap = lambda n: cogs.get(n, 0.0)
    row = 18
    row = model_answer(ws, row, "Model answer, requirement (2): why revenue and expense accounts show one year", [
        f"The query keeps every posting through December 31, {y}, but the revenue and expense accounts were closed to "
        f"retained earnings at the end of fiscal {y - 2} ({' and '.join(e1)}) and fiscal {y - 1} "
        f"({' and '.join(e2)}). Those closing entries left every revenue and expense account at zero, so what remains "
        f"in them is the activity of fiscal {y} alone; only the {y} closing entries ({c1} and {c2}) were filtered out, "
        "which is what makes this a pre-closing trial balance. The balance sheet accounts are never closed, so they "
        f"carry their balances forward from the opening balance entry of January {y - 2}. The trial balance has "
        f"{f['accounts']} accounts ({f['zero']} of them at zero), and its debit and credit balances are both "
        f"{money(f['debits'])}."],
        note="The earlier closing entries are on the JournalEntries worksheet (EntryType Year-End Close); their figures "
             "were also checked against CharlesRiver.sqlite when the solution was built.")
    ship_note = ("Shipment dates and posting dates come from the Shipment, ShipmentLine, and GLEntry tables of "
                 "CharlesRiver.sqlite, which this workbook does not load; they were queried when the solution was built.")
    row = model_answer(ws, row, "Model answer, requirement (5): the reconciling differences", [
        f"{words(len(diffs), True)} accounts exceed the {y} revenue of their item groups in InvoiceLines: "
        + ", ".join(f"{r['account']} ({r['group']}) by {money(r['diff'])}" for r in diffs)
        + f"; {' and '.join(str(r['account']) for r in f['recon'] if r['diff'] == 0)} agree. The differences are exactly "
        f"the {words(len(odd))} invoices that Exercise 5.2 found numbered in fiscal {y} but dated in fiscal {y - 1}: "
        + "; ".join(f"{i['number']} ({i['group']}, dated {i['date']}, {money(i['amount'])})" for i in odd)
        + f". The ledger posted them on {posted}, in fiscal {y}; InvoiceLines assigns them to fiscal {y - 1} by their "
        "invoice dates.",
        "Neither the invoice number nor the invoice date should decide the period. Revenue is recognized when control "
        "of the goods passes to the customer, which for Charles River is delivery, and every shipment is delivered in "
        f"the year it ships. The shipment records show that only {e['number']} shipped in {y - 1} (on "
        f"{e['shipped'][0]}), so its {money(e['amount'])} belongs in fiscal {y - 1} and is a revenue cutoff error in "
        f"the ledger; the other {words(len(later))} shipped on {', '.join(later_dates)}, so the ledger's period is right and their "
        f"invoice dates are wrong. Freight revenue (4050, {money(-f['bal'].get(4050, 0.0))}) is billed on the invoice "
        "header and has no invoice line, so it is not part of the comparison."], note=ship_note)
    row = model_answer(ws, row, "Model answer, requirement (6): memo to the controller", [
        f"To: Controller. From: Staff accountant. Subject: Fiscal {y} income statement from the general ledger.",
        f"I prepared the attached income statement from the pre-closing trial balance at December 31, {y}: every "
        f"posting through that date except the two {y} closing entries, grouped by account ({f['accounts']} accounts, "
        f"debit and credit balances of {money(f['debits'])} each). Net income is {money(L['ni'])}, "
        f"{pct(L['ni'] / net, 2)} of net revenue, and it equals the amount closing entry {c2} moved to retained "
        f"earnings; the balance sheet balances once net income is added to equity (assets {money(f['assets'])}).",
        f"The common-size statement shows the cost structure: of each dollar of net revenue ({money(net)}), cost of "
        f"goods sold takes {pct(-L['cogs'] / net, 1)}, leaving a gross margin of {pct(L['gm'] / net, 1)}; operating "
        f"expenses take {pct(-L['opex'] / net, 1)}, so operating income is {pct(L['oi'] / net, 1)}, and other items "
        f"(a {money(f['bal'].get(7020, 0.0))} loss on an asset disposal and {money(f['bal'].get(7030, 0.0))} of "
        f"interest) take another {pct(-L['other'] / net, 1)}. Returns and allowances are small "
        f"({pct(-L['contra'] / L['opr'], 1)} of operating revenue). The gross margin is well below the margin at "
        f"standard cost on product sales in the invoice lines ({pct(f['product_std_margin'], 1)} without the design "
        f"services), because cost of goods sold carries, besides the standard cost of the goods shipped ({money(std_cogs)}), freight-out "
        f"({money(gap(5050))}), the purchase price variance ({money(gap(5060))}), and the manufacturing variance "
        f"({money(gap(5080))}), which is the largest cost to explain.",
        f"Product revenue in the ledger agrees with the invoice lines except for "
        f"{money(sum(r['diff'] for r in diffs))} in {words(len(diffs))} accounts: {words(len(odd))} invoices dated in December {y - 1} "
        f"but numbered and posted in {y}. One of them, {e['number']} ({money(e['amount'])}), shipped in {y - 1} and is "
        "a cutoff error that belongs in the prior year; it is immaterial, but the invoicing and posting dates should "
        f"be reviewed at every year-end. The other {words(len(later))} shipped in {month_name(later_dates[0])} "
        f"{later_dates[0][:4]}, so only their invoice dates are wrong."])


def checks_6_1(b: ExerciseBuild) -> None:
    y, f = b.year, facts_6_1(b.year)
    L, c2 = f["lines"], f["closes"][1]
    e = "6.1"
    b.check(e, "accounts in the trial balance (rows of TrialBalance)", f["accounts"], "=ROWS(TrialBalance[AccountID])",
            0, COUNT)
    b.check(e, "accounts with a zero balance", f["zero"], "=SUMPRODUCT(--(ROUND(TrialBalance[Balance],2)=0))", 0, COUNT)
    b.check(e, "Total Row, DebitBalance", round(f["debits"], 2), "=TrialBalance[[#Totals],[DebitBalance]]", 0.01)
    b.check(e, "Total Row, CreditBalance", round(f["credits"], 2), "=TrialBalance[[#Totals],[CreditBalance]]", 0.01)
    b.check(e, "debit less credit balances", 0,
            "=ROUND(TrialBalance[[#Totals],[DebitBalance]]-TrialBalance[[#Totals],[CreditBalance]],2)")
    labels = [("opr", "operating revenue"), ("contra", "sales returns and allowances"), ("net", "net revenue"),
              ("cogs", "cost of goods sold"), ("gm", "gross margin"), ("opex", "operating expenses"),
              ("oi", "operating income"), ("other", "other income and expense"), ("ni", "net income")]
    for r, (key, label) in enumerate(labels, start=2):
        b.check(e, f"{label} (IncomeStatement!B{r})", round(L[key], 2), f"=IncomeStatement!B{r}", 0.01)
    for r, (key, label) in enumerate(labels, start=2):
        if key in ("opr", "cogs", "gm", "opex", "oi", "ni"):
            b.check(e, f"{label}, % of net revenue (IncomeStatement!C{r})", L[key] / L["net"], f"=IncomeStatement!C{r}",
                    1e-6, PCT)
    for number, label in ((7020, "loss on asset disposal (7020)"), (7030, "interest expense (7030)")):
        b.check(e, f"{label} balance", round(f["bal"][number], 2),
                f"=SUMIFS(TrialBalance[Balance],TrialBalance[AccountNumber],{number})", 0.01)
    b.check(e, f"TotalAmount of {c2} (IncomeStatement!B21)", round(f["closing"], 2), "=IncomeStatement!B21")
    b.check(e, f"net income less {c2} (IncomeStatement!B22)", 0, "=IncomeStatement!B22")
    b.check(e, "assets (IncomeStatement!B13)", round(f["assets"], 2), "=IncomeStatement!B13", 0.01)
    b.check(e, "liabilities (IncomeStatement!B14)", round(f["liabilities"], 2), "=IncomeStatement!B14", 0.01)
    b.check(e, "equity (IncomeStatement!B15)", round(f["equity"], 2), "=IncomeStatement!B15", 0.01)
    b.check(e, "assets less liabilities, equity, and net income (IncomeStatement!B18)", 0, "=IncomeStatement!B18")
    for i, r in enumerate(f["recon"]):
        row = 5 + i
        b.check(e, f"account {r['account']} balance ('Ex 6.1'!C{row})", round(r["ledger"], 2), f"='Ex 6.1'!C{row}", 0.01)
        b.check(e, f"{r['group']} revenue {y} in InvoiceLines ('Ex 6.1'!D{row})", round(r["lines"], 2),
                f"='Ex 6.1'!D{row}", 0.01)
        b.check(e, f"difference, account {r['account']} ('Ex 6.1'!E{row})", r["diff"], f"='Ex 6.1'!E{row}")
    b.check(e, "differences not explained by the invoices ('Ex 6.1'!G10)", 0, "='Ex 6.1'!G10")
    for i, inv in enumerate(f["odd"]):
        row = 14 + i
        b.check(e, f"invoice {i + 1} numbered in {y}, dated {y - 1} ('Ex 6.1'!B{row})", inv["number"],
                f"='Ex 6.1'!B{row}", 0, GENERAL)
        b.check(e, f"{inv['number']}: invoice date", serial(inv["date"]), f"='Ex 6.1'!C{row}", 0, DATE)
        b.check(e, f"{inv['number']}: item group", inv["group"], f"='Ex 6.1'!D{row}", 0, GENERAL)
        b.check(e, f"{inv['number']}: line total", round(inv["amount"], 2), f"='Ex 6.1'!E{row}")
    b.check(e, "freight revenue, 4050 (no invoice line)", round(-f["bal"][4050], 2),
            "=-SUMIFS(TrialBalance[Balance],TrialBalance[AccountNumber],4050)", 0.01)


# --- Exercise 6.2 ----------------------------------------------------------------------------------------------------

def ex6_2(b: ExerciseBuild) -> None:
    y, p = b.year, b.year - 1
    f = facts_6_2(y)
    ws = new_sheet(b, "Ex 6.2")
    title(ws, 6, 2)
    change = f"Change from {p}"

    # (1) shares of the grand total, fiscal y
    pt1 = pivot(b, ws, "A5", "Ex62Share")
    page(pt1, "FiscalYear", str(y))
    pt1.PivotFields("CustomerSegment").Orientation = xl.XL_ROW
    pt1.PivotFields("ItemGroup").Orientation = xl.XL_COLUMN
    share = data_field(pt1, "LineTotal", "Share of revenue", PCT)
    share.Calculation = XL_PERCENT_OF_TOTAL
    share.NumberFormat = PCT

    # (2) the year-over-year change by segment and product line
    top2 = end_row(pt1) + 4
    pt2 = pivot(b, ws, f"A{top2}", "Ex62Change")
    pt2.PivotFields("CustomerSegment").Orientation = xl.XL_ROW
    pt2.PivotFields("FiscalYear").Orientation = xl.XL_COLUMN
    pt2.PivotFields("ItemGroup").Orientation = xl.XL_COLUMN
    data_field(pt2, "LineTotal", "Revenue", MONEY)
    ch = data_field(pt2, "LineTotal", change, PCT)
    years(pt2, (p, y))
    ch.Calculation = xl.XL_PERCENT_DIFFERENCE_FROM
    ch.BaseField = "FiscalYear"
    ch.BaseItem = "(previous)"
    ch.NumberFormat = PCT
    pt2.DataPivotField.Orientation = xl.XL_ROW
    pt2.DataPivotField.Position = 2
    pt2.DisplayErrorString = True              # % Difference From has no base where a combination had no revenue
    pt2.ErrorString = ""

    # (3) the same comparison by region
    top3 = end_row(pt2) + 4
    pt3 = pivot(b, ws, f"A{top3}", "Ex62Region")
    pt3.PivotFields("Region").Orientation = xl.XL_ROW
    pt3.PivotFields("FiscalYear").Orientation = xl.XL_COLUMN
    pt3.PivotFields("ItemGroup").Orientation = xl.XL_COLUMN
    data_field(pt3, "LineTotal", "Revenue", MONEY)
    ch3 = data_field(pt3, "LineTotal", change, PCT)
    years(pt3, (p, y))
    ch3.Calculation = xl.XL_PERCENT_DIFFERENCE_FROM
    ch3.BaseField = "FiscalYear"
    ch3.BaseItem = "(previous)"
    ch3.NumberFormat = PCT
    pt3.DataPivotField.Orientation = xl.XL_ROW
    pt3.DataPivotField.Position = 2
    pt3.DisplayErrorString = True
    pt3.ErrorString = ""

    # the combinations, read from the PivotTables, and the rankings
    c0 = max(end_col(pt1), end_col(pt2), end_col(pt3)) + 2
    C = [col(c0 + i) for i in range(6)]          # Segment, ItemGroup, revenue p, revenue y, share y, change
    heading(ws, f"{C[0]}3", "Combinations of segment and product line (read from the PivotTables)")
    for i, h in enumerate(["Segment", "Item group", f"Revenue {p}", f"Revenue {y}", f"Share of {y}", change]):
        ws.Range(f"{C[i]}4").Value = h
    bold(ws, f"{C[0]}4:{C[5]}4")
    r1, r2 = local(pt1), local(pt2)
    first = 5
    for i, (s, g) in enumerate(f["order"]):
        r = first + i
        args = (("CustomerSegment", f"${C[0]}{r}"), ("ItemGroup", f"${C[1]}{r}"))
        put(ws, {f"{C[0]}{r}": s, f"{C[1]}{r}": g,
                 f"{C[2]}{r}": f"=IFERROR({gpd('Revenue', r2, *args, ('FiscalYear', p))},0)",
                 f"{C[3]}{r}": f"=IFERROR({gpd('Revenue', r2, *args, ('FiscalYear', y))},0)",
                 f"{C[4]}{r}": f"=IFERROR({gpd('Share of revenue', r1, *args)},0)",
                 f"{C[5]}{r}": f'=IF({C[2]}{r}=0,"",{C[3]}{r}/{C[2]}{r}-1)'})
    last = first + len(f["order"]) - 1
    ws.Range(f"{C[2]}{first}:{C[3]}{last}").NumberFormat = MONEY
    ws.Range(f"{C[4]}{first}:{C[5]}{last}").NumberFormat = PCT
    rng = lambda k: f"${C[k]}${first}:${C[k]}${last}"
    label = f"{rng(0)}&\"-\"&{rng(1)}"
    D = [col(c0 + 7 + i) for i in range(4)]
    put(ws, {f"{D[0]}3": f"Minimum {p} revenue for the change ranking", f"{D[2]}3": 500000})
    bold(ws, f"{D[0]}3")
    ws.Range(f"{D[2]}3").Font.Color = xl.BLUE
    ws.Range(f"{D[2]}3").NumberFormat = MONEY
    minimum = f"${D[2]}$3"
    heading(ws, f"{D[0]}5", f"(1) The five largest combinations, fiscal {y}")
    put(ws, {f"{D[0]}6": "Combination", f"{D[1]}6": "Share of revenue",
             f"{D[0]}7": f"=TAKE(SORTBY(HSTACK({label},{rng(4)}),{rng(4)},-1),5)"})
    heading(ws, f"{D[0]}13", f"(2) The two largest increases from {p}")
    flt = f"{rng(2)}>={minimum}"
    rows = f"FILTER(HSTACK({label},{rng(2)},{rng(3)},{rng(5)}),{flt})"
    put(ws, {f"{D[0]}14": "Combination", f"{D[1]}14": f"Revenue {p}", f"{D[2]}14": f"Revenue {y}", f"{D[3]}14": change,
             f"{D[0]}15": f"=TAKE(SORTBY({rows},FILTER({rng(5)},{flt}),-1),2)"})
    heading(ws, f"{D[0]}18", f"(2) The two largest decreases from {p}")
    put(ws, {f"{D[0]}19": "Combination", f"{D[1]}19": f"Revenue {p}", f"{D[2]}19": f"Revenue {y}", f"{D[3]}19": change,
             f"{D[0]}20": f"=TAKE(SORTBY({rows},FILTER({rng(5)},{flt}),1),2)"})
    for r in (6, 14, 19):
        bold(ws, f"{D[0]}{r}:{D[3]}{r}")
    ws.Range(f"{D[1]}7:{D[1]}11").NumberFormat = PCT
    ws.Range(f"{D[1]}15:{D[2]}21").NumberFormat = MONEY
    ws.Range(f"{D[3]}15:{D[3]}21").NumberFormat = PCT
    heading(ws, f"{D[0]}23", f"(2), (3) Change from {p} by segment and by region")
    put(ws, {f"{D[0]}24": "Segment", f"{D[1]}24": change})
    segs = sorted(f["segments"], key=lambda s: -f["segments"][s])
    for i, s in enumerate(segs):
        r = 25 + i
        put(ws, {f"{D[0]}{r}": s, f"{D[1]}{r}": f"={gpd(change, r2, ('CustomerSegment', f'{D[0]}{r}'), ('FiscalYear', y))}"})
    rt = 25 + len(segs)
    put(ws, {f"{D[0]}{rt}": "Total", f"{D[1]}{rt}": f"={gpd(change, r2, ('FiscalYear', y))}"})
    r3 = local(pt3)
    rr = rt + 2
    put(ws, {f"{D[0]}{rr}": "Region", f"{D[1]}{rr}": change})
    regions = sorted(f["regions"], key=lambda s: -f["regions"][s])
    for i, reg in enumerate(regions):
        r = rr + 1 + i
        put(ws, {f"{D[0]}{r}": reg, f"{D[1]}{r}": f"={gpd(change, r3, ('Region', f'{D[0]}{r}'), ('FiscalYear', y))}"})
    bold(ws, f"{D[0]}24:{D[1]}24")
    bold(ws, f"{D[0]}{rr}:{D[1]}{rr}")
    ws.Range(f"{D[1]}25:{D[1]}{rr + len(regions)}").NumberFormat = PCT
    ws.Columns(f"A:{col(c0 - 1)}").AutoFit()
    widths(ws, {f"{C[0]}:{C[1]}": 16, f"{C[2]}:{C[5]}": 15, f"{D[0]}:{D[0]}": 30, f"{D[1]}:{D[3]}": 16})
    b.found["6.2"] = dict(sheet=ws.Name, r1=ref(ws, pt1), r2=ref(ws, pt2), r3=ref(ws, pt3), D=D, segs=segs,
                          seg_total=rt, regions=regions, region_head=rr)

    # (4) the disclosure paragraph
    top = f["top"]
    up, down = f["up"], f["down"]
    seg = f["segments"]
    reg = f["regions"]
    name = lambda k: f"{k[0]}-{k[1]}"
    gs = f["grp_share"]
    ss = sorted(f["seg_share"].items(), key=lambda kv: -kv[1])
    para = (
        f"Disaggregation of revenue. The Company disaggregates revenue by product line and by type of customer, the "
        "categories management uses to plan its assortment and its sales coverage, and the ones that best show how "
        "economic factors affect the nature, amount, and timing of revenue: goods are recognized on delivery, while "
        f"design services are billed by the hour. Revenue from invoice lines was ${f['total'] / 1e6:,.2f} million in "
        f"fiscal {y}: Furniture {pct(gs['Furniture'])}, Lighting {pct(gs['Lighting'])}, Textiles "
        f"{pct(gs['Textiles'])}, Accessories {pct(gs['Accessories'])}, and design services {pct(gs['Services'])}; by "
        f"customer type, {', '.join(f'{s} {pct(v)}' for s, v in ss[:-1])}, and {ss[-1][0]} {pct(ss[-1][1])}. The "
        f"largest combinations were {name(top[0][0])} ({pct(top[0][1])} of revenue), {name(top[1][0])} "
        f"({pct(top[1][1])}), and {name(top[2][0])} ({pct(top[2][1])}). Revenue "
        f"{'rose' if f['total_change'] >= 0 else 'fell'} {pct(abs(f['total_change']))} from "
        f"fiscal {p}: {', '.join(f'{s} {spct(seg[s])}' for s in segs)}. Among the combinations with at least "
        f"$500,000 of revenue in {p}, the largest increases were {name(up[0][0])} ({spct(up[0][3])}) and "
        f"{name(up[1][0])} ({spct(up[1][3])}), and the largest decreases {name(down[0][0])} ({spct(down[0][3])}) and "
        f"{name(down[1][0])} ({spct(down[1][3])}). By region, revenue changed "
        f"{', '.join(f'{r} {spct(reg[r])}' for r in regions)}, which the Company presents as supplementary "
        "information, because it sets its price lists and promotions by customer type and product line, not by region.")
    why = ("Why these categories: product line and type of customer are how Charles River manages and prices its "
           "business (price lists by segment, promotions by item group and segment), and they separate revenues with "
           "different economic characteristics. Design Services buys only design services, so for that segment the "
           "customer type and the product line coincide; presenting the two categories as separate splits, rather "
           "than as a full cross-table, avoids repeating that revenue.")
    widths(ws, {"A": max(ws.Columns("A").ColumnWidth, 18)})
    model_answer(ws, end_row(pt3) + 3, "Model answer, requirement (4): disclosure paragraph", [para, why],
                 last_col=c0 - 2)


def checks_6_2(b: ExerciseBuild) -> None:
    y, p, f = b.year, b.year - 1, facts_6_2(b.year)
    k = b.found["6.2"]
    D = k["D"]
    s = lambda x: q(x)
    e = "6.2"
    change = f"Change from {p}"
    combos, grand = f["combos"], f["grand"]
    for (seg, grp), _, _ in f["top"][:3]:
        b.check(e, f"{seg}-{grp}, % of grand total {y} (PivotTable)", combos[(seg, grp)][1] / grand,
                "=" + gpd("Share of revenue", k["r1"], ("CustomerSegment", s(seg)), ("ItemGroup", s(grp))), 1e-9, PCT)
        b.check(e, f"{seg}-{grp}, revenue {y}", round(combos[(seg, grp)][1], 2),
                "=" + gpd("Revenue", k["r2"], ("CustomerSegment", s(seg)), ("ItemGroup", s(grp)), ("FiscalYear", y)), 0.01)
    sheet = f"'{k['sheet']}'!"
    for i, ((seg, grp), share, _) in enumerate(f["top"]):
        r = 7 + i
        b.check(e, f"ranked combination {i + 1} ({D[0]}{r})", f"{seg}-{grp}", f"={sheet}{D[0]}{r}", 0, GENERAL)
        b.check(e, f"ranked combination {i + 1}, share ({D[1]}{r})", share, f"={sheet}{D[1]}{r}", 1e-9, PCT)
    for start, items, kind in ((15, f["up"], "increase"), (20, f["down"], "decrease")):
        for i, ((seg, grp), a, bb, c) in enumerate(items):
            r = start + i
            b.check(e, f"largest {kind} {i + 1} ({D[0]}{r})", f"{seg}-{grp}", f"={sheet}{D[0]}{r}", 0, GENERAL)
            b.check(e, f"largest {kind} {i + 1}, revenue {p}", round(a, 2), f"={sheet}{D[1]}{r}", 0.01)
            b.check(e, f"largest {kind} {i + 1}, revenue {y}", round(bb, 2), f"={sheet}{D[2]}{r}", 0.01)
            b.check(e, f"largest {kind} {i + 1}, change", c, f"={sheet}{D[3]}{r}", 1e-9, PCT)
    for seg in k["segs"]:
        b.check(e, f"{seg}, change from {p}", f["segments"][seg],
                "=" + gpd(change, k["r2"], ("CustomerSegment", s(seg)), ("FiscalYear", y)), 1e-9, PCT)
    b.check(e, f"total revenue, change from {p}", f["total_change"], "=" + gpd(change, k["r2"], ("FiscalYear", y)),
            1e-9, PCT)
    for reg in k["regions"]:
        b.check(e, f"{reg} region, change from {p}", f["regions"][reg],
                "=" + gpd(change, k["r3"], ("Region", s(reg)), ("FiscalYear", y)), 1e-9, PCT)


# --- Exercise 6.3 ----------------------------------------------------------------------------------------------------

def ex6_3(b: ExerciseBuild) -> None:
    y = b.year
    f = facts_6_3(y)
    ws = new_sheet(b, "Ex 6.3")
    title(ws, 6, 3)

    # (1) revenue, margin, and margin percentage by item group
    pt = pivot(b, ws, "A5", "Ex63Groups")
    pt.CalculatedFields().Add("Margin", "=LineTotal-StdCostAmount", True)
    page(pt, "FiscalYear", str(y))
    pt.PivotFields("ItemGroup").Orientation = xl.XL_ROW
    data_field(pt, "LineTotal", "Revenue", MONEY)
    data_field(pt, "Margin", "Margin (dollars)", MONEY)
    data_field(pt, "MarginPct", "Margin %", PCT)
    r1 = local(pt)

    # (2) shares without Services
    heading(ws, "G4", "(2) Shares without Services")
    put(ws, {"G5": "Item group", "H5": "Revenue", "I5": "Margin", "J5": "Share of revenue", "K5": "Share of margin",
             "L5": "Margin share larger"})
    bold(ws, "G5:L5")
    for i, g in enumerate(f["by_revenue"]):
        r = 6 + i
        put(ws, {f"G{r}": g, f"H{r}": f"={gpd('Revenue', r1, ('ItemGroup', f'$G{r}'))}",
                 f"I{r}": f"={gpd('Margin (dollars)', r1, ('ItemGroup', f'$G{r}'))}",
                 f"J{r}": f"=H{r}/H$10", f"K{r}": f"=I{r}/I$10", f"L{r}": f"=K{r}>J{r}"})
    put(ws, {"G10": "Total without Services", "H10": "=SUM(H6:H9)", "I10": "=SUM(I6:I9)", "J10": "=SUM(J6:J9)",
             "K10": "=SUM(K6:K9)",
             "G12": "Product lines with a larger share of margin than of revenue",
             "G13": '=TEXTJOIN(", ",TRUE,FILTER(G6:G9,L6:L9))'})
    bold(ws, "G12")
    ws.Range("H6:I10").NumberFormat = MONEY
    ws.Range("J6:K10").NumberFormat = PCT

    # (3) Furniture by product type
    top = end_row(pt) + 6
    pt2 = pivot(b, ws, f"A{top}", "Ex63Types")
    page(pt2, "FiscalYear", str(y))
    page(pt2, "ItemGroup", "Furniture")
    pt2.PivotFields("ProductType").Orientation = xl.XL_ROW
    data_field(pt2, "LineTotal", "Revenue", MONEY)
    data_field(pt2, "Margin", "Margin (dollars)", MONEY)
    data_field(pt2, "MarginPct", "Margin %", PCT)
    pt2.PivotFields("ProductType").AutoSort(xl.XL_DESCENDING, "Margin %")
    r2 = local(pt2)
    t0 = pt2.TableRange1.Row
    heading(ws, f"G{t0 - 1}", "(3) Furniture product types, fiscal " + str(y))
    put(ws, {f"G{t0}": "ProductType", f"H{t0}": "Product type", f"I{t0}": "Margin %"})
    bold(ws, f"G{t0}:I{t0}")
    for i, t in enumerate(f["types"]):
        r = t0 + 1 + i
        put(ws, {f"G{r}": t, f"H{r}": TYPE_NAMES.get(t, ""), f"I{r}": f"={gpd('Margin %', r2, ('ProductType', f'$G{r}'))}"})
    tl = t0 + len(f["types"])
    ws.Range(f"I{t0 + 1}:I{tl}").NumberFormat = PCT
    put(ws, {f"G{tl + 2}": "Highest margin %", f"H{tl + 2}": f"=TAKE(SORTBY(G{t0 + 1}:G{tl},I{t0 + 1}:I{tl},-1),2)",
             f"G{tl + 4}": "Lowest margin %", f"H{tl + 4}": f"=TAKE(SORTBY(G{t0 + 1}:G{tl},I{t0 + 1}:I{tl},1),2)",
             f"I{tl + 2}": f"=XLOOKUP(H{tl + 2}#,G{t0 + 1}:G{tl},I{t0 + 1}:I{tl})",
             f"I{tl + 4}": f"=XLOOKUP(H{tl + 4}#,G{t0 + 1}:G{tl},I{t0 + 1}:I{tl})"})
    bold(ws, f"G{tl + 2}")
    bold(ws, f"G{tl + 4}")
    ws.Range(f"I{tl + 2}:I{tl + 5}").NumberFormat = PCT
    widths(ws, {"A": 18, "B:D": 17, "E:F": 3, "G": 24, "H:K": 16, "L": 18})
    b.found["6.3"] = dict(sheet=ws.Name, r1=ref(ws, pt), r2=ref(ws, pt2), rank=tl + 2)

    # (4) the Services margin
    g = f["groups"]["Services"]
    model_answer(ws, max(end_row(pt2), tl + 5) + 3, "Model answer, requirement (4): the Services margin", [
        f"The PivotTable shows Services at a {pct(g['pct'], 0)} margin because it values every line at the item's "
        "standard cost, and the design-service items carry a StandardCost of 0. The cost of a design service is the "
        "time of the design staff, which is paid through payroll and recorded in the time records and the ledger, not "
        "in the item master, so the invoice lines cannot show it. To measure the margin you need the cost of the hours "
        f"behind the services billed: for example, ServiceTimeEntry.ExtendedCost for {y} work dates "
        f"({money(f['time_cost'])}, a margin of about {pct(f['time_pct'], 0)} on {money(g['revenue'])} of revenue), or "
        f"the {y} Design Services salaries in account 6280 ({money(f['salaries'])}, about "
        f"{pct(f['salaries_pct'], 0)}). The gap between the two (time charged to engagements against all of the "
        "staff's pay, including unbilled time) shows that the answer depends on the cost definition, which the "
        "report must state."], last_col=6,
        note="ServiceTimeEntry and account 6280 are not loaded in this workbook; their totals were queried from "
             "CharlesRiver.sqlite when the solution was built.")


def checks_6_3(b: ExerciseBuild) -> None:
    y, f = b.year, facts_6_3(b.year)
    k = b.found["6.3"]
    sheet = f"'{k['sheet']}'!"
    e = "6.3"
    for g in GROUPS:
        x = f["groups"][g]
        b.check(e, f"{g} margin % {y}", x["pct"], "=" + gpd("Margin %", k["r1"], ("ItemGroup", q(g))), 1e-9, PCT)
        if g != "Services":
            b.check(e, f"{g} margin (dollars)", round(x["margin"], 2),
                    "=" + gpd("Margin (dollars)", k["r1"], ("ItemGroup", q(g))), 0.01)
            b.check(e, f"{g} revenue", round(x["revenue"], 2), "=" + gpd("Revenue", k["r1"], ("ItemGroup", q(g))), 0.01)
    for i, g in enumerate(f["by_revenue"]):
        r = 6 + i
        rs, ms = f["shares"][g]
        b.check(e, f"{g} share of revenue without Services (J{r})", rs, f"={sheet}J{r}", 1e-9, PCT)
        b.check(e, f"{g} share of margin without Services (K{r})", ms, f"={sheet}K{r}", 1e-9, PCT)
    b.check(e, "product lines with a larger share of margin than of revenue (G13)", ", ".join(f["more"]),
            f"={sheet}G13", 0, GENERAL)
    r = k["rank"]
    for i, t in enumerate(f["high"]):
        b.check(e, f"highest Furniture margin % {i + 1} (H{r + i})", t, f"={sheet}H{r + i}", 0, GENERAL)
        b.check(e, f"{t} margin %", f["tpct"][t], f"={sheet}I{r + i}", 1e-9, PCT)
    for i, t in enumerate(f["low"]):
        b.check(e, f"lowest Furniture margin % {i + 1} (H{r + 2 + i})", t, f"={sheet}H{r + 2 + i}", 0, GENERAL)
        b.check(e, f"{t} margin %", f["tpct"][t], f"={sheet}I{r + 2 + i}", 1e-9, PCT)


# --- Exercise 6.4 ----------------------------------------------------------------------------------------------------

def ex6_4(b: ExerciseBuild) -> None:
    y = b.year
    f = facts_6_4(y)
    q3, q4 = f"{y}-Q3", f"{y}-Q4"
    ws = new_sheet(b, "Ex 6.4")
    title(ws, 6, 4)

    # (1) the PivotTable, read with GETPIVOTDATA
    pt = pivot(b, ws, "A5", "Ex64Types")
    page(pt, "ItemGroup", "Furniture")
    pt.PivotFields("ProductType").Orientation = xl.XL_ROW
    pt.PivotFields("Period").Orientation = xl.XL_COLUMN
    only_items(pt.PivotFields("Period"), [q3, q4])
    for fld in ("Quantity", "LineTotal", "StdCostAmount"):
        data_field(pt, fld, f"Sum of {fld}", MONEY)
    pt.RowGrand = False
    r1 = local(pt)

    # (2) per-unit values and shares, (3) the effects by type
    h = end_row(pt) + 3
    heading(ws, f"A{h - 1}", f"(2), (3) The product-type bridge, {q3} to {q4} (values read with GETPIVOTDATA)")
    heads = ["ProductType", f"{q3} units", f"{q3} revenue", f"{q3} standard cost", f"{q4} units", f"{q4} revenue",
             f"{q4} standard cost", f"{q3} price per unit", f"{q3} cost per unit", f"{q3} margin per unit",
             f"{q4} price per unit", f"{q4} cost per unit", f"{q4} margin per unit", f"{q3} share of units",
             "Price effect", "Cost effect", "Mix effect", "Change in cost per unit", f"{q3} discount", f"{q4} discount",
             "Discount part of price effect"]
    for i, t in enumerate(heads):
        ws.Cells(h, 1 + i).Value = t
    ws.Range(f"A{h}:U{h}").Font.Bold = True
    ws.Range(f"A{h}:U{h}").WrapText = True
    n = len(f["types"])
    r0, rt = h + 1, h + n + 1
    for i, t in enumerate(f["types"]):
        r = r0 + i
        g = lambda fld, period: gpd(f"Sum of {fld}", r1, ("ProductType", f"$A{r}"), ("Period", q(period)))
        disc = lambda period: (f'=SUMIFS(InvoiceLines[DiscountAmount],InvoiceLines[ItemGroup],"Furniture",'
                               f'InvoiceLines[ProductType],$A{r},InvoiceLines[Period],"{period}")')
        put(ws, {f"A{r}": t, f"B{r}": "=" + g("Quantity", q3), f"C{r}": "=" + g("LineTotal", q3),
                 f"D{r}": "=" + g("StdCostAmount", q3), f"E{r}": "=" + g("Quantity", q4), f"F{r}": "=" + g("LineTotal", q4),
                 f"G{r}": "=" + g("StdCostAmount", q4), f"H{r}": f"=C{r}/B{r}", f"I{r}": f"=D{r}/B{r}",
                 f"J{r}": f"=H{r}-I{r}", f"K{r}": f"=F{r}/E{r}", f"L{r}": f"=G{r}/E{r}", f"M{r}": f"=K{r}-L{r}",
                 f"N{r}": f"=B{r}/$B${rt}", f"O{r}": f"=E{r}*(K{r}-H{r})", f"P{r}": f"=-E{r}*(L{r}-I{r})",
                 f"Q{r}": f"=(E{r}-$E${rt}*N{r})*J{r}", f"R{r}": f"=L{r}-I{r}", f"S{r}": disc(q3), f"T{r}": disc(q4),
                 f"U{r}": f"=-E{r}*(T{r}/E{r}-S{r}/B{r})"})
    put(ws, {f"A{rt}": "Furniture", **{f"{c}{rt}": f"=SUM({c}{r0}:{c}{rt - 1})" for c in "BCDEFGNOPQSTU"},
             f"H{rt}": f"=C{rt}/B{rt}", f"I{rt}": f"=D{rt}/B{rt}", f"J{rt}": f"=H{rt}-I{rt}",
             f"K{rt}": f"=F{rt}/E{rt}", f"L{rt}": f"=G{rt}/E{rt}", f"M{rt}": f"=K{rt}-L{rt}"})
    ws.Range(f"A{rt}:U{rt}").Font.Bold = True
    ws.Range(f"B{r0}:U{rt}").NumberFormat = MONEY
    ws.Range(f"N{r0}:N{rt}").NumberFormat = PCT

    s0 = rt + 3
    heading(ws, f"A{s0}", "(3), (4) The four effects, and Tutorial 6.3's bridge")
    put(ws, {f"B{s0}": "Product types", f"C{s0}": "Tutorial 6.3 (Furniture)"})
    bold(ws, f"B{s0}:C{s0}")
    rows = [(f"{q3} margin", f"=C{rt}-D{rt}", "=Bridge!B16"),
            (f"{q4} margin", f"=F{rt}-G{rt}", "=Bridge!B22"),
            ("Change in margin", f"=B{s0 + 2}-B{s0 + 1}", f"=C{s0 + 2}-C{s0 + 1}"),
            ("Price", f"=O{rt}", "=Bridge!B19+Bridge!B20"),
            ("Cost", f"=P{rt}", "=Bridge!B21"),
            ("Volume", f"=(E{rt}-B{rt})*J{rt}", "=Bridge!B17"),
            ("Mix", f"=Q{rt}", "=Bridge!B18"),
            ("Sum of the four effects", f"=SUM(B{s0 + 4}:B{s0 + 7})", f"=SUM(C{s0 + 4}:C{s0 + 7})"),
            ("Check: sum of effects less the change", f"=ROUND(B{s0 + 8}-B{s0 + 3},2)", f"=ROUND(C{s0 + 8}-C{s0 + 3},2)"),
            ("of which promotional discounts, in the price effect", f"=U{rt}", "=Bridge!B20")]
    for i, (label, a, c) in enumerate(rows):
        r = s0 + 1 + i
        put(ws, {f"A{r}": label, f"B{r}": a, f"C{r}": c})
    ws.Range(f"B{s0 + 1}:C{s0 + 10}").NumberFormat = MONEY
    k0 = s0 + 13
    heading(ws, f"A{k0}", "(4) The product type with the largest change in cost per unit")
    rng = lambda c: f"{c}{r0}:{c}{rt - 1}"
    put(ws, {f"A{k0 + 1}": "ProductType", f"B{k0 + 1}": f"=INDEX({rng('A')},XMATCH(MAX(ABS({rng('R')})),ABS({rng('R')})))",
             f"A{k0 + 2}": f"{q3} price per unit", f"B{k0 + 2}": f"=XLOOKUP(B{k0 + 1},{rng('A')},{rng('H')})",
             f"A{k0 + 3}": f"{q4} price per unit", f"B{k0 + 3}": f"=XLOOKUP(B{k0 + 1},{rng('A')},{rng('K')})",
             f"A{k0 + 4}": f"{q3} cost per unit", f"B{k0 + 4}": f"=XLOOKUP(B{k0 + 1},{rng('A')},{rng('I')})",
             f"A{k0 + 5}": f"{q4} cost per unit", f"B{k0 + 5}": f"=XLOOKUP(B{k0 + 1},{rng('A')},{rng('L')})"})
    ws.Range(f"B{k0 + 2}:B{k0 + 5}").NumberFormat = MONEY
    ws.Columns("A").ColumnWidth = 44
    ws.Columns("B:U").ColumnWidth = 14
    ws.Rows(h).RowHeight = 45
    b.found["6.4"] = dict(sheet=ws.Name, r0=r0, rt=rt, s0=s0, k0=k0)

    # (4) and (5) written answers
    a, bb = f["a"], f["b"]
    top = f["top"]
    same = [t for t in f["types"] if t != top and bb[t]["R"] / bb[t]["U"] < a[t]["R"] / a[t]["U"]
            and bb[t]["C"] / bb[t]["U"] < a[t]["C"] / a[t]["U"]]
    rose = [t for t in f["types"] if bb[t]["R"] / bb[t]["U"] > a[t]["R"] / a[t]["U"]
            and bb[t]["C"] / bb[t]["U"] > a[t]["C"] / a[t]["U"]]
    from xlbuild import expected
    from xlbuild.expected import Expected
    t63 = expected.bridge(Expected(y), y)
    r = k0 + 8
    r = model_answer(ws, r, "Model answer, requirement (4): comparison with Tutorial 6.3", [
        f"Both bridges explain the same change in the Furniture margin, {money(f['q3'])} to {money(f['q4'])} "
        f"({money(f['change'])}). Volume is the same in both ({money(f['volume'])}), because both value the change in "
        f"total units at the third quarter's Furniture margin per unit. The rest divides differently: at the Furniture "
        f"level, mix {money(t63['mix'])}, price {money(t63['price'] + t63['promotions'])} (price lists "
        f"{money(t63['price'])}, promotions {money(t63['promotions'])}), and cost zero; product type by product type, "
        f"mix {money(f['mix'])}, price {money(f['price'])}, of which about {round(f['promotions'], -2):,.0f} is "
        f"promotional discounts, and cost {money(f['cost'])}.",
        "The cost effect is no longer zero, although no item's standard cost changed, because a product type's "
        "average standard cost per unit depends on which of its items were sold. "
        f"{top} ({TYPE_NAMES.get(top, top)}s) has the largest change in cost per unit: its price per unit fell from "
        f"{money(f['p3'])} to {money(f['p4'])} and its cost per unit from {money(f['c3'])} to {money(f['c4'])}, because "
        f"cheaper {TYPE_NAMES.get(top, top)}s made up more of the fourth quarter. That shift between items within the "
        "type shows up as an unfavorable price effect and a favorable cost effect, while at the Furniture level it "
        "is part of mix. "
        + (f"{' and '.join(same)} move the same way, " if same else "")
        + (f"and price and cost per unit rose together for {' and '.join(rose)}." if rose else "")])
    model_answer(ws, r, "Model answer, requirement (5): recommendation", [
        "Present Tutorial 6.3's Furniture-level bridge as the headline, because each of its effects has one meaning: "
        "price is the change in price-list reductions and promotional discounts on the same items, cost is zero "
        "because standard costs did not change, and mix captures every shift between items. The product-type bridge "
        "is useful supporting detail for the sales team, which plans its assortment by type, but at that level item "
        "mix within each type appears as price and cost, so it should be labeled as such. Whichever level the report "
        "uses, it should state it."], last_col=8)


def checks_6_4(b: ExerciseBuild) -> None:
    y, f = b.year, facts_6_4(b.year)
    k = b.found["6.4"]
    sheet = f"'{k['sheet']}'!"
    s0, k0, r0 = k["s0"], k["k0"], k["r0"]
    e = "6.4"
    for i, (key, label) in enumerate([("q3", f"{y}-Q3 margin"), ("q4", f"{y}-Q4 margin"), ("change", "change in margin"),
                                      ("price", "price effect"), ("cost", "cost effect"), ("volume", "volume effect"),
                                      ("mix", "mix effect")]):
        b.check(e, f"{label} (B{s0 + 1 + i})", round(f[key], 2), f"={sheet}B{s0 + 1 + i}", 0.01)
    b.check(e, f"effects sum to the change (B{s0 + 9})", 0, f"={sheet}B{s0 + 9}")
    b.check(e, f"Tutorial 6.3 bridge sums to the same change (C{s0 + 9})", 0, f"={sheet}C{s0 + 9}")
    b.check(e, "volume effect equals Tutorial 6.3's", 0, f"=ROUND({sheet}B{s0 + 6}-{sheet}C{s0 + 6},2)")
    b.check(e, "promotional discounts in the price effect, to the nearest hundred", round(f["promotions"], -2),
            f"=ROUND({sheet}B{s0 + 10},-2)", 0, MONEY)
    b.check(e, f"type with the largest change in cost per unit (B{k0 + 1})", f["top"], f"={sheet}B{k0 + 1}", 0, GENERAL)
    for i, key in enumerate(("p3", "p4", "c3", "c4")):
        b.check(e, f"{f['top']} {key[0] == 'p' and 'price' or 'cost'} per unit, Q{key[1]} (B{k0 + 2 + i})",
                round(f[key], 6), f"={sheet}B{k0 + 2 + i}", 1e-6)
    units = sorted(f["types"], key=lambda t: f["b"][t]["U"] - f["a"][t]["U"])
    for t in units[:2] + units[::-1][:2]:
        r = r0 + f["types"].index(t)
        b.check(e, f"{t} units, Q3 (B{r})", round(f["a"][t]["U"], 4), f"={sheet}B{r}", 1e-4)
        b.check(e, f"{t} units, Q4 (E{r})", round(f["b"][t]["U"], 4), f"={sheet}E{r}", 1e-4)


# --- Exercise 6.5 ----------------------------------------------------------------------------------------------------

def ex6_5(b: ExerciseBuild) -> None:
    y, p = b.year, b.year - 1
    f = facts_6_5(y)
    ws = new_sheet(b, "Ex 6.5")
    title(ws, 6, 5)
    pt = pivot(b, ws, "A3", "Ex65Quarters")
    pt.PivotFields("ItemGroup").Orientation = xl.XL_ROW
    pt.PivotFields("FiscalQuarter").Orientation = xl.XL_COLUMN
    pt.PivotFields("FiscalYear").Orientation = xl.XL_COLUMN
    years(pt, (p, y))
    data_field(pt, "LineTotal", "Sum of LineTotal", MONEY)
    pt.RowGrand = False
    ws.Columns("A").ColumnWidth = 16
    ws.Columns("B:M").ColumnWidth = 14
    r1 = ref(ws, pt)

    ex = new_sheet(b, "Ex 6.5 Expectation")
    title(ex, 6, 5)
    put(ex, {"A3": "Percentage threshold", "B3": 0.1, "A4": "Dollar threshold", "B4": 50000})
    ex.Range("B3").NumberFormat = "0%"
    ex.Range("B4").NumberFormat = MONEY
    ex.Range("B3:B4").Font.Color = xl.BLUE
    heads = ["ItemGroup", "Quarter", f"Expectation ({p})", f"Recorded ({y})", "Difference", "Difference %", "Flagged"]
    for i, h in enumerate(heads):
        ex.Cells(6, 1 + i).Value = h
    bold(ex, "A6:G6")
    for i, row in enumerate(f["rows"]):
        r = 7 + i
        args = (("ItemGroup", f"$A{r}"), ("FiscalQuarter", f"$B{r}"))
        put(ex, {f"A{r}": row["group"], f"B{r}": row["q"],
                 f"C{r}": "=" + gpd("Sum of LineTotal", r1, *args, ("FiscalYear", p)),
                 f"D{r}": "=" + gpd("Sum of LineTotal", r1, *args, ("FiscalYear", y)),
                 f"E{r}": f"=D{r}-C{r}", f"F{r}": f"=E{r}/C{r}",
                 f"G{r}": f"=AND(ABS(E{r})>$B$3*C{r},ABS(E{r})>$B$4)"})
    last = 6 + len(f["rows"])
    ex.Range(f"C7:E{last}").NumberFormat = MONEY
    ex.Range(f"F7:F{last}").NumberFormat = "0.0%"
    ex.Activate()
    ex.Range("A7").Select()                 # a formula rule is read relative to the active cell
    flag = ex.Range(f"A7:G{last}").FormatConditions.Add(xl.XL_EXPRESSION, 1, "=$G7")
    flag.Interior.Color = xl.LIGHT_FILL
    grid = f"A7:F{last}"
    heading(ex, "I5", "(3) Differences over both thresholds")
    put(ex, {"I6": "ItemGroup", "J6": "Quarter", "K6": "Expectation", "L6": "Recorded", "M6": "Difference",
             "N6": "Difference %", "I7": f"=FILTER({grid},G7:G{last})",
             "I15": "Differences flagged", "J15": f"=COUNTIF(G7:G{last},TRUE)"})
    heading(ex, "I17", "(4) The largest differences in dollars not flagged")
    put(ex, {"I18": "ItemGroup", "J18": "Quarter", "K18": "Expectation", "L18": "Recorded", "M18": "Difference",
             "N18": "Difference %",
             "I19": f"=TAKE(SORTBY(FILTER({grid},NOT(G7:G{last})),ABS(FILTER(E7:E{last},NOT(G7:G{last}))),-1),2)"})
    bold(ex, "I6:N6")
    bold(ex, "I15")
    bold(ex, "I18:N18")
    ex.Range("K7:M20").NumberFormat = MONEY
    ex.Range("N7:N20").NumberFormat = "0.0%"
    widths(ex, {"A": 16, "B": 9, "C:E": 16, "F": 13, "G": 9, "H": 3, "I": 14, "J": 9, "K:M": 16, "N": 13})
    b.found["6.5"] = dict(sheet=ex.Name, r1=r1, last=last)

    fl, ms = f["flagged"], f["missed"]
    lab = lambda r: f"{r['group']} Q{r['q']}"
    sv = [r for r in fl if r["group"] == "Services"]
    row = model_answer(ex, last + 3, "Model answer, requirement (4): the design of the threshold", [
        f"{words(len(fl), True)} differences exceed both thresholds: "
        + "; ".join(f"{lab(r)} {money(r['diff'])} ({spct(r['pct'])})" for r in fl)
        + f". The largest difference in dollars, {lab(ms[0])} {money(ms[0]['diff'])} ({spct(ms[0]['pct'])}), is not "
        f"flagged, and neither is {lab(ms[1])} {money(ms[1]['diff'])} ({spct(ms[1]['pct'])}). Both are several times "
        "the $50,000 threshold but below 10 percent, because Furniture is by far the largest product line: requiring "
        "both conditions lets the percentage test screen out large dollar differences in large lines, while small "
        "lines such as Services are flagged for differences that matter less in dollars. A threshold based on a "
        "tolerable amount derived from materiality, or an expectation that reflects known changes such as the "
        f"promotions of {y}, would treat them differently; prior-year revenue is also a weak expectation, because it "
        "ignores growth and known events."], last_col=7)
    pick = sv[-1] if sv else fl[0]
    model_answer(ex, row, "Model answer, requirement (5): follow-up of one flagged difference", [
        f"{lab(pick)}: recorded revenue of {money(pick['act'])} against an expectation of {money(pick['exp'])} "
        f"({spct(pick['pct'])}). Evidence: the design-service invoice lines of the quarter by engagement and customer, "
        "compared with the same quarter of the prior year; the engagement records and the time records (hours by "
        "engagement and work date) behind the hours billed, agreed to the invoices for a sample of lines; the billing "
        "rates against the approved rate list; and invoices dated near the quarter-end, checked against the dates the "
        "work was performed, for cutoff. Questions for management: which engagements started or ended in the quarter, "
        "whether rates or staffing changed, whether any work was billed in advance or late, and why the other "
        f"quarters of {y} were below the prior year. For the unflagged {lab(ms[0])} difference, the promotion "
        "discounts measured in Tutorial 6.3 and the late-invoiced promotion lines found in Tutorial 5.2 would be the "
        "first evidence to obtain."], last_col=7)


def checks_6_5(b: ExerciseBuild) -> None:
    y, f = b.year, facts_6_5(b.year)
    k = b.found["6.5"]
    sheet = f"'{k['sheet']}'!"
    e = "6.5"
    b.check(e, "differences flagged (J15)", len(f["flagged"]), f"={sheet}J15", 0, COUNT)
    for start, items, kind in ((7, f["flagged"], "flagged"), (19, f["missed"], "not flagged")):
        for i, r in enumerate(items):
            row = start + i
            b.check(e, f"{kind} {i + 1}: item group (I{row})", r["group"], f"={sheet}I{row}", 0, GENERAL)
            b.check(e, f"{kind} {i + 1}: quarter (J{row})", r["q"], f"={sheet}J{row}", 0, COUNT)
            b.check(e, f"{r['group']} Q{r['q']}: difference (M{row})", round(r["diff"], 2), f"={sheet}M{row}", 0.01)
            b.check(e, f"{r['group']} Q{r['q']}: difference % (N{row})", r["pct"], f"={sheet}N{row}", 1e-9, PCT)


# --- Exercise 6.6 ----------------------------------------------------------------------------------------------------

def ex6_6(b: ExerciseBuild) -> None:
    y = b.year
    f = facts_6_6(y)
    ws = new_sheet(b, "Ex 6.6")
    title(ws, 6, 6)

    # (1) lines, revenue, average, and median by item group
    heading(ws, "A3", f"(1) Invoice lines of fiscal {y} by item group")
    put(ws, {"A4": "ItemGroup", "B4": "Lines", "C4": "Revenue", "D4": "Average line", "E4": "Median line"})
    bold(ws, "A4:E4")
    for i, g in enumerate(GROUPS):
        r = 5 + i
        crit = f"InvoiceLines[ItemGroup],$A{r},InvoiceLines[FiscalYear],{y}"
        put(ws, {f"A{r}": g, f"B{r}": f"=COUNTIFS({crit})", f"C{r}": f"=SUMIFS(InvoiceLines[LineTotal],{crit})",
                 f"D{r}": f"=AVERAGEIFS(InvoiceLines[LineTotal],{crit})",
                 f"E{r}": (f"=MEDIAN(FILTER(InvoiceLines[LineTotal],(InvoiceLines[FiscalYear]={y})*"
                           f"(InvoiceLines[ItemGroup]=A{r})))")})
    put(ws, {"A10": "Total", "B10": "=SUM(B5:B9)", "C10": "=SUM(C5:C9)", "D10": "=C10/B10",
             "E10": f"=MEDIAN(FILTER(InvoiceLines[LineTotal],InvoiceLines[FiscalYear]={y}))"})
    bold(ws, "A10:E10")
    ws.Range("B5:B10").NumberFormat = COUNT
    ws.Range("C5:E10").NumberFormat = MONEY

    # (3) pricing method by item group
    heading(ws, "A13", f"(3) Lines and revenue by pricing method and item group, fiscal {y}")
    pt3 = pivot(b, ws, "A17", "Ex66Pricing")
    page(pt3, "FiscalYear", str(y))
    pt3.PivotFields("PricingMethod").Orientation = xl.XL_ROW
    pt3.PivotFields("ItemGroup").Orientation = xl.XL_COLUMN
    data_field(pt3, "SalesInvoiceLineID", "Lines", COUNT, xl.XL_COUNT)
    data_field(pt3, "LineTotal", "Revenue", MONEY)
    sh = data_field(pt3, "LineTotal", "Share of revenue", PCT)
    sh.Calculation = XL_PERCENT_OF_TOTAL
    sh.NumberFormat = PCT
    pt3.DataPivotField.Orientation = xl.XL_ROW

    # (4) promotions
    top4 = end_row(pt3) + 6
    heading(ws, f"A{top4 - 4}", f"(4) Lines and discounts by promotion, fiscal {y}")
    pt4 = pivot(b, ws, f"A{top4}", "Ex66Promotions")
    page(pt4, "FiscalYear", str(y))
    pt4.PivotFields("PromotionID").Orientation = xl.XL_ROW
    data_field(pt4, "SalesInvoiceLineID", "Lines", COUNT, xl.XL_COUNT)
    data_field(pt4, "DiscountAmount", "Discount amount", MONEY)
    c = end_col(pt4) + 2
    P = [col(c + i) for i in range(7)]
    p0 = pt4.TableRange1.Row
    heading(ws, f"{P[0]}{p0 - 1}", f"Promotions with lines invoiced in {y}")
    for i, h in enumerate(["PromotionID", "PromotionName", "EffectiveStartDate", "EffectiveEndDate",
                           f"First invoice, {y}", f"Last invoice, {y}", f"Ran in {y - 1}"]):
        ws.Range(f"{P[i]}{p0}").Value = h
    bold(ws, f"{P[0]}{p0}:{P[6]}{p0}")
    ids = f"{P[0]}{p0 + 1}#"
    crit = f"InvoiceLines[PromotionID],{ids},InvoiceLines[FiscalYear],{y}"
    put(ws, {f"{P[0]}{p0 + 1}": (f'=SORT(UNIQUE(FILTER(InvoiceLines[PromotionID],(InvoiceLines[FiscalYear]={y})*'
                                 f'(InvoiceLines[PromotionID]<>""))))'),
             f"{P[1]}{p0 + 1}": f"=XLOOKUP({ids},PromotionProgram[PromotionID],PromotionProgram[PromotionName])",
             f"{P[2]}{p0 + 1}": f"=XLOOKUP({ids},PromotionProgram[PromotionID],PromotionProgram[EffectiveStartDate])",
             f"{P[3]}{p0 + 1}": f"=XLOOKUP({ids},PromotionProgram[PromotionID],PromotionProgram[EffectiveEndDate])",
             f"{P[4]}{p0 + 1}": f"=MINIFS(InvoiceLines[InvoiceDate],{crit})",
             f"{P[5]}{p0 + 1}": f"=MAXIFS(InvoiceLines[InvoiceDate],{crit})",
             f"{P[6]}{p0 + 1}": f"=YEAR({P[2]}{p0 + 1}#)={y - 1}"})
    ws.Range(f"{P[2]}{p0 + 1}:{P[5]}{p0 + 12}").NumberFormat = DATE
    n = len(f["promos"])
    lr = p0 + n + 2
    late = f"FILTER({ids},{P[6]}{p0 + 1}#)"
    put(ws, {f"{P[0]}{lr}": f"Promotions of {y - 1} with lines invoiced in {y}",
             f"{P[2]}{lr}": f'=TEXTJOIN(", ",TRUE,{late})',
             f"{P[0]}{lr + 1}": "Their lines were invoiced from",
             f"{P[2]}{lr + 1}": f'=TEXT(MIN(FILTER({P[4]}{p0 + 1}#,{P[6]}{p0 + 1}#)),"mmmm yyyy")',
             f"{P[0]}{lr + 2}": "to",
             f"{P[2]}{lr + 2}": f'=TEXT(MAX(FILTER({P[5]}{p0 + 1}#,{P[6]}{p0 + 1}#)),"mmmm yyyy")'})
    bold(ws, f"{P[0]}{lr}")
    g0 = max(end_row(pt4), lr + 2) + 3
    heading(ws, f"A{g0}", "(4) Share of each item group's lines that carry a promotion")
    put(ws, {f"A{g0 + 1}": "ItemGroup", f"B{g0 + 1}": "Lines", f"C{g0 + 1}": "Promotion lines",
             f"D{g0 + 1}": "Share"})
    bold(ws, f"A{g0 + 1}:D{g0 + 1}")
    for i, g in enumerate(GROUPS):
        r = g0 + 2 + i
        crit = f"InvoiceLines[ItemGroup],$A{r},InvoiceLines[FiscalYear],{y}"
        put(ws, {f"A{r}": g, f"B{r}": f"=COUNTIFS({crit})", f"C{r}": f'=COUNTIFS({crit},InvoiceLines[PromotionID],"<>")',
                 f"D{r}": f"=C{r}/B{r}"})
    ws.Range(f"B{g0 + 2}:C{g0 + 6}").NumberFormat = COUNT
    ws.Range(f"D{g0 + 2}:D{g0 + 6}").NumberFormat = "0.0%"
    widths(ws, {"A": 22, "B:H": 15})
    for cc in P:
        ws.Columns(cc).ColumnWidth = 16
    ws.Columns(P[1]).ColumnWidth = 34
    ws.Columns(P[0]).ColumnWidth = 22

    # (2) customers, on their own worksheet
    cs = new_sheet(b, "Ex 6.6 Customers")
    title(cs, 6, 6)
    ptc = pivot(b, cs, "A5", "Ex66Customers")
    page(ptc, "FiscalYear", str(y))
    ptc.PivotFields("CustomerID").Orientation = xl.XL_ROW
    data_field(ptc, "LineTotal", "Revenue", MONEY)
    ptc.PivotFields("CustomerID").AutoSort(xl.XL_DESCENDING, "Revenue")
    body = ptc.DataBodyRange
    first, count = body.Row, f["customers"]
    lastc = first + count - 1
    head = first - 1
    rc = local(ptc)
    put(cs, {f"C{head}": "CustomerName", f"D{head}": "CustomerSegment", f"E{head}": "Share of revenue",
             f"F{head}": "Cumulative share"})
    bold(cs, f"C{head}:F{head}")
    cs.Range(f"C{first}:C{lastc}").Formula2 = f"=XLOOKUP($A{first},Customer[CustomerID],Customer[CustomerName])"
    cs.Range(f"D{first}:D{lastc}").Formula2 = f"=XLOOKUP($A{first},Customer[CustomerID],Customer[CustomerSegment])"
    cs.Range(f"E{first}:E{lastc}").Formula2 = f"=B{first}/{gpd('Revenue', rc)}"
    cs.Range(f"F{first}:F{lastc}").Formula2 = f"=SUM($E${first}:E{first})"
    cs.Range(f"E{first}:F{lastc}").NumberFormat = "0.0%"
    heading(cs, "H4", f"(2) Concentration, fiscal {y}")
    put(cs, {"H5": f"Customers invoiced in {y}",
             "I5": f"=ROWS(UNIQUE(FILTER(InvoiceLines[CustomerID],InvoiceLines[FiscalYear]={y})))",
             "H6": "Share of the five largest", "I6": f"=SUM(B{first}:B{first + 4})/{gpd('Revenue', rc)}",
             "H7": "Share of the ten largest", "I7": f"=SUM(B{first}:B{first + 9})/{gpd('Revenue', rc)}",
             "H8": "Segments of the ten largest", "I8": f'=TEXTJOIN(", ",TRUE,UNIQUE(D{first}:D{first + 9}))',
             "H9": "The five largest", "I9": f'=TEXTJOIN("; ",TRUE,C{first}:C{first + 4})'})
    cs.Range("I6:I7").NumberFormat = "0.0%"
    widths(cs, {"A": 14, "B": 16, "C": 32, "D": 18, "E:F": 14, "G": 3, "H": 30, "I": 60})
    b.found["6.6"] = dict(sheet=ws.Name, customers=cs.Name, r3=ref(ws, pt3), r4=ref(ws, pt4), P=P, p0=p0, lr=lr,
                          g0=g0, first=first)

    # (5) the written profile
    gr = f["groups"]
    meth = sorted(f["methods"].items(), key=lambda kv: -kv[1][1])
    big = max(f["promos"], key=lambda pid: f["promos"][pid][0])
    late = f["late"]
    rev = list(f["reversed"])
    starts = f["starts"]
    paragraphs = [
        f"Population. In fiscal {y} Charles River billed {f['lines']:,} invoice lines totaling {money(f['revenue'])} to "
        f"{f['customers']} customers. A normal invoice line is worth a few thousand dollars, depending on the item "
        "group: "
        + "; ".join(f"{g} {gr[g]['lines']:,} lines, average {money(gr[g]['mean'])}, median {money(gr[g]['median'])}"
                    for g in GROUPS[:4])
        + f". Design services are fewer and larger ({gr['Services']['lines']} lines, average "
        f"{money(gr['Services']['mean'])}). In every group the average is above the median, so the distribution is "
        "skewed to the right, with a tail of large lines that a sample should cover in full.",
        f"Concentration. Revenue is concentrated in Furniture ({pct(gr['Furniture']['revenue'] / f['revenue'])} of the "
        f"year), not in customers: the five largest customers hold {pct(f['top5'])} of revenue and the ten largest "
        f"{pct(f['top10'])}, all of them {', '.join(f['top10_segments'])} accounts (the largest are "
        f"{', '.join(f['largest'][:-1])}, and {f['largest'][-1]}). No single customer is material to the population "
        "on its own.",
        "Pricing. By revenue, "
        + ", ".join(f"{pct(s)}{' was priced' if i == 0 else ''} {PRICING.get(m, m)} ({n:,} lines)"
                    for i, (m, (n, s)) in enumerate(meth[:-1]))
        + f", and {pct(meth[-1][1][1])} {PRICING.get(meth[-1][0], meth[-1][0])} ({meth[-1][1][0]:,} lines)"
        + ". The base list is used only for the hourly design services, and approved overrides, the one manual pricing "
        f"path, are a small share. Of the year's lines, {f['promo_lines']:,} carry a promotion, with "
        f"{money(f['promo_discount'])} of "
        f"discounts; promotion {big} alone accounts for {f['promos'][big][0]} lines and "
        f"{money(f['promos'][big][1])}. Promotions touch about a fifth of Furniture lines "
        f"({pct(gr['Furniture']['promo_share'])}) and very few lines in the other groups.",
        "Matters for the audit. "
        + f"Promotions {' and '.join(str(p) for p in late)}, which ran in {y - 1}, have lines invoiced from "
        f"{month_name(f['late_first'])} to {month_name(f['late_last'])} {y}, the same late-invoicing pattern as "
        f"promotion {big}, so discounts are being billed after the promotions ended; the audit should test whether "
        "those lines were ordered within the promotion periods. "
        + (f"Promotion {rev[0]}'s recorded end date ({starts[rev[0]][1]}) is before its start date "
           f"({starts[rev[0]][0]}), a master-data question for the audit work later in Part II. " if rev else "")
        + "The approved overrides and the largest lines are natural targets for tests of pricing authority and "
          "accuracy."]
    model_answer(ws, g0 + 9, "Model answer, requirement (5): profile of the revenue population", paragraphs, last_col=8)


def checks_6_6(b: ExerciseBuild) -> None:
    y, f = b.year, facts_6_6(b.year)
    k = b.found["6.6"]
    sheet, cs = f"'{k['sheet']}'!", f"'{k['customers']}'!"
    e = "6.6"
    for i, g in enumerate(GROUPS):
        r = 5 + i
        x = f["groups"][g]
        b.check(e, f"{g} lines (B{r})", x["lines"], f"={sheet}B{r}", 0, COUNT)
        b.check(e, f"{g} revenue (C{r})", round(x["revenue"], 2), f"={sheet}C{r}", 0.01)
        b.check(e, f"{g} average line (D{r})", x["mean"], f"={sheet}D{r}", 1e-6)
        b.check(e, f"{g} median line (E{r})", x["median"], f"={sheet}E{r}", 1e-6)
    b.check(e, f"customers invoiced in {y}", f["customers"], f"={cs}I5", 0, COUNT)
    b.check(e, "share of the five largest customers", f["top5"], f"={cs}I6", 1e-9, PCT)
    b.check(e, "share of the ten largest customers", f["top10"], f"={cs}I7", 1e-9, PCT)
    b.check(e, "segments of the ten largest customers", ", ".join(f["top10_segments"]), f"={cs}I8", 0, GENERAL)
    b.check(e, "the five largest customers", "; ".join(f["largest"]), f"={cs}I9", 0, GENERAL)
    for m, (n, s) in f["methods"].items():
        b.check(e, f"{m}: lines", n, "=" + gpd("Lines", k["r3"], ("PricingMethod", q(m))), 0, COUNT)
        b.check(e, f"{m}: share of revenue", s, "=" + gpd("Share of revenue", k["r3"], ("PricingMethod", q(m))), 1e-9, PCT)
    for pid, (n, disc, _, _) in sorted(f["promos"].items()):
        b.check(e, f"promotion {pid}: lines", n, "=" + gpd("Lines", k["r4"], ("PromotionID", pid)), 0, COUNT)
        b.check(e, f"promotion {pid}: discount", round(disc, 2), "=" + gpd("Discount amount", k["r4"], ("PromotionID", pid)), 0.01)
    for i, g in enumerate(GROUPS):
        r = k["g0"] + 2 + i
        b.check(e, f"{g}: share of lines with a promotion (D{r})", f["groups"][g]["promo_share"], f"={sheet}D{r}", 1e-9, PCT)
    P, lr, p0 = k["P"], k["lr"], k["p0"]
    late = f"FILTER({sheet}{P[0]}{p0 + 1}#,{sheet}{P[6]}{p0 + 1}#)"
    b.check(e, f"promotions of {y - 1} with lines invoiced in {y}", len(f["late"]), f"=ROWS({late})", 0, COUNT)
    for i, pid in enumerate(f["late"]):
        b.check(e, f"promotion of {y - 1} invoiced in {y}, {i + 1}", pid, f"=INDEX({late},{i + 1})", 0, COUNT)
    b.check(e, "their first invoice date", serial(f["late_first"]),
            f"=MIN(FILTER({sheet}{P[4]}{p0 + 1}#,{sheet}{P[6]}{p0 + 1}#))", 0, DATE)
    b.check(e, "their last invoice date", serial(f["late_last"]),
            f"=MAX(FILTER({sheet}{P[5]}{p0 + 1}#,{sheet}{P[6]}{p0 + 1}#))", 0, DATE)


# --- the exercises, in book order ---------------------------------------------------------------------------------

def _with_checks(apply, checks):
    def run(b: ExerciseBuild) -> None:
        apply(b)
        checks(b)
    run.__name__ = apply.__name__
    return run


EXERCISES = [("6.1", _with_checks(ex6_1, checks_6_1)), ("6.2", _with_checks(ex6_2, checks_6_2)),
             ("6.3", _with_checks(ex6_3, checks_6_3)), ("6.4", _with_checks(ex6_4, checks_6_4)),
             ("6.5", _with_checks(ex6_5, checks_6_5)), ("6.6", _with_checks(ex6_6, checks_6_6))]
