"""Chapter 6 figures."""

from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.calculations.invoice_margin import invoice_lines, period

import excel as xl
from data import connection, one, q, require_columns
from shared.calculations.excel_analysis import margin_bridge as shared_margin_bridge
from drawio import (BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK, ROW_H, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

PIVOT_GROUPS = ["Accessories", "Furniture", "Lighting", "Services", "Textiles"]  # sorted, as a PivotTable lists them
TYPED_GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories"]  # the four product lines of Tutorial 6.1
QUARTERS = ["2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"]
NBSP = "&nbsp;&nbsp;&nbsp;"
PROMO_COLUMNS = [r[1] for r in q("PRAGMA table_info(PromotionProgram)")]


@lru_cache(maxsize=1)
def lines() -> list[dict]:
    """InvoiceLines as Tutorial 5.3 builds it, with chapter 6's unrounded custom columns:
    StdCostAmount = Quantity * StandardCost, ListAmount = Quantity * BaseListPrice and
    DiscountAmount = Quantity * UnitPrice * Discount."""
    require_columns("SalesInvoiceLine", ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity",
                                         "BaseListPrice", "UnitPrice", "Discount", "LineTotal",
                                         "PromotionID"])
    require_columns("SalesInvoice", ["SalesInvoiceID", "InvoiceDate", "CustomerID"])
    require_columns("Item", ["ItemID", "ItemGroup", "StandardCost"])
    require_columns("Customer", ["CustomerID", "CustomerSegment"])
    return invoice_lines(connection())


def total(field: str, **match) -> float:
    return sum(r[field] for r in lines() if all(r[k] == v for k, v in match.items()))


def count(**match) -> int:
    return sum(1 for r in lines() if all(r[k] == v for k, v in match.items()))


def margin_pct(**match) -> float:
    revenue = total("R", **match)
    return (revenue - total("C", **match)) / revenue


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def signed_pct(value: float) -> str:
    return f"{'+' if value >= 0 else '−'}{abs(100 * value):.2f}%"


@lru_cache(maxsize=1)
def bridge() -> dict:
    return shared_margin_bridge(connection())


def pivot_style(header_rows: set[int], bold_rows: set[int], total_rows: set[int],
                indent_rows: set[int] = frozenset(), tints: dict | None = None):
    """A cell style for xl.sheet() that looks like a PivotTable in Excel's default style."""
    def style(r: int, c: int, value: str) -> dict:
        # Row labels, headers, and the report filter are left-aligned, as Excel shows them.
        out: dict = dict(align="left") if (c == 0 or r == 0 or r in header_rows) else {}
        if r in header_rows:
            out.update(fill=BLUE_TINT, label=f"<b>{esc(value)}</b>")
        elif r in total_rows:
            out.update(fill=BLUE_TINT, label=f"<b>{esc(value)}</b>")
        elif r in bold_rows and c == 0:
            out.update(label=f"<b>{esc(value)}</b>")
        if r in indent_rows and c == 0:
            out.update(label=f"{NBSP}{esc(value)}")
        if tints and (r, c) in tints:
            out.update(fill=tints[(r, c)])
        return out
    return style


def fig_06_01() -> Diagram:
    d = Diagram("A Profile of Fiscal 2026 Invoice Lines with a Control Total")
    fy = [r["R"] for r in lines() if r["fy"] == 2026]
    stats = [
        ("Invoice lines", f"{len(fy):,}"),
        ("Line total", xl.num(sum(fy))),
        ("Average line", xl.num(statistics.mean(fy))),
        ("Median line", xl.num(statistics.median(fy))),
        ("Standard deviation", xl.num(statistics.stdev(fy))),
        ("Smallest line", xl.num(min(fy))),
        ("Largest line", xl.num(max(fy))),
        ("90th percentile", xl.num(xl.percentile_inc(fy, 0.9))),
    ]
    assert statistics.mean(fy) > statistics.median(fy), "the profile describes a right skew"
    body = [("1", ["Fiscal year", "2026", "", ""])]
    body += [(str(i + 2), [label, value, "", ""]) for i, (label, value) in enumerate(stats)]
    body.append(("10", ["", "", "", ""]))
    body.append(("11", ["Item group", "Lines", "Revenue", "Average line"]))
    groups = TYPED_GROUPS + ["Services"]
    for i, g in enumerate(groups):
        n, rev = count(fy=2026, grp=g), total("R", fy=2026, grp=g)
        body.append((str(12 + i), [g, f"{n:,}", xl.num(rev), xl.num(rev / n)]))
    n_all = sum(count(fy=2026, grp=g) for g in groups)
    rev_all = sum(total("R", fy=2026, grp=g) for g in groups)
    assert n_all == len(fy) and abs(rev_all - sum(fy)) < 0.005
    body.append(("17", ["Total of groups", f"{n_all:,}", xl.num(rev_all), ""]))
    body.append(("18", ["Difference from control total", f"{n_all - len(fy):,}",
                        xl.num(round(rev_all - sum(fy), 2) + 0.0), ""]))
    xl.formula_bar(d, 0, 0, 860, "B5",
                   "=MEDIAN(FILTER(InvoiceLines[LineTotal],InvoiceLines[FiscalYear]=ReportYear))")
    widths = [36, 250, 130, 170, 130]
    services = 12 + groups.index("Services") - 1   # data-row index of the Services row

    def style(r: int, c: int, value: str) -> dict:
        if c == 0:
            return dict(align="left", **({"label": f"<b>{esc(value)}</b>", "fill": GRAY_TINT}
                                        if r == 10 else {"fill": TEAL_TINT} if r == services
                                        else {"label": f"<b>{esc(value)}</b>"} if r in (16, 17)
                                        else {}))
        if r == 10:
            return dict(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>")
        if r == services:
            return dict(fill=TEAL_TINT)
        if r in (16, 17) and c < 3:
            return dict(label=f"<b>{esc(value)}</b>")
        return {}

    geo = xl.sheet(d, 0, 40, ["A", "B", "C", "D"], widths, body, style)
    xl.select(d, *geo[(4, 1)])
    x0, y0, _, _ = geo[(services, 0)]
    xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H)
    x0, y0, _, _ = geo[(17, 0)]
    xl.emphasis(d, x0, y0, sum(widths[1:4]), ROW_H)
    bottom = 40 + 22 + ROW_H * len(body)
    d.text("<i>Outlined: the Services row, added after the difference revealed the missing group, and "
           "the difference, which is zero once every group is listed.</i>", 0, bottom + 8, 860, 40,
           size=SMALL, color=GRAY)
    return d


def fig_06_histogram() -> Diagram:
    d = Diagram("The Distribution of Fiscal 2026 Line Totals")
    fy = [r["R"] for r in lines() if r["fy"] == 2026]
    bounds = list(range(0, 16000, 1000))
    counts = []
    for i, low in enumerate(bounds):
        high = bounds[i + 1] if i + 1 < len(bounds) else None
        counts.append(sum(1 for v in fy if v >= low and (high is None or v < high)))
    assert sum(counts) == len(fy)
    assert counts[0] == max(counts) and counts[-2] < counts[0] / 50, "a right-skewed distribution"
    body = [("1", ["From", "Lines"])]
    for i, (low, n) in enumerate(zip(bounds, counts)):
        body.append((str(i + 2), [xl.num(low, 0), f"{n:,}"]))
    body.append((str(len(bounds) + 2), ["Total", f"{sum(counts):,}"]))
    xl.formula_bar(d, 0, 0, 860, "G2", '=COUNTIFS(InvoiceLines[FiscalYear],ReportYear,'
                   'InvoiceLines[LineTotal],">="&F2,InvoiceLines[LineTotal],"<"&F3)')

    def style(r: int, c: int, value: str) -> dict:
        if r == 0:
            return dict(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>", align="left" if c == 0 else "right")
        if r == len(body) - 1:
            return dict(label=f"<b>{esc(value)}</b>", align="left" if c == 0 else "right")
        return {}

    widths = [36, 100, 90]
    geo = xl.sheet(d, 0, 40, ["F", "G"], widths, body, style, row_h=22)
    xl.select(d, *geo[(1, 1)])
    # The column chart with no gap between the bars, beside the table.
    left, right, top, height = 300, 850, 70, 330
    peak = 2500
    y_of = lambda v: top + (peak - v) * height / peak
    for tick in range(0, peak + 1, 500):
        d.box("", left, y_of(tick), right - left, 1, fill=RULE, stroke=RULE, rounded=False)
        d.text(f"{tick:,}", left - 50, y_of(tick) - 11, 44, 22, size=SMALL, align="right", valign="middle")
    slot = (right - left) / len(counts)
    for i, n in enumerate(counts):
        x = left + i * slot
        d.box("", x, y_of(n), slot, y_of(0) - y_of(n), fill=BLUE, stroke=WHITE, rounded=False)
    for i in range(0, len(counts), 3):
        label = "0" if i == 0 else f"{bounds[i] // 1000}k"
        d.text(label, left + i * slot - 10, top + height + 4, slot + 20, 20, size=SMALL, align="center")
    d.text("15k+", left + (len(counts) - 1) * slot - 10, top + height + 4, slot + 20, 20, size=SMALL,
           align="center")
    d.text("Line total, lower bound of the $1,000 bin", left, top + height + 26, right - left, 22,
           size=SMALL, align="center")
    d.text("Lines", left - 50, top - 30, 60, 22, size=SMALL, align="right")
    bottom = 40 + 22 + 22 * len(body)
    d.text("<i>Invoice lines of fiscal 2026. F2:F17 hold the lower bound of each bin; G17, the last bin, "
           "counts every line of $15,000 or more. The chart is a clustered column chart of G2:G17 with a "
           "gap width of 0.</i>", 0, bottom + 10, 860, 40, size=SMALL, color=GRAY)
    return d


@lru_cache(maxsize=1)
def trial_balance() -> list[tuple]:
    """The pre-closing trial balance at the end of fiscal 2026, as the ledger section builds it:
    GLEntry through 2026-12-31 without the two 2026 closing entries, grouped by account."""
    require_columns("GLEntry", ["AccountID", "Debit", "Credit", "PostingDate", "VoucherNumber"])
    require_columns("Account", ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"])
    closes = [r[0] for r in q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' "
                              "AND PostingDate LIKE '2026%' ORDER BY EntryNumber")]
    assert closes == ["JE-2026-000296", "JE-2026-000297"], closes
    rows = q("SELECT a.AccountNumber, a.AccountName, a.AccountType, a.AccountSubType, SUM(g.Debit), SUM(g.Credit) "
             "FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.PostingDate < '2027-01-01' "
             "AND g.VoucherNumber NOT IN (?, ?) GROUP BY a.AccountID ORDER BY a.AccountNumber", *closes)
    debit = sum(max(0.0, r[4] - r[5]) for r in rows)
    credit = sum(max(0.0, r[5] - r[4]) for r in rows)
    assert abs(debit - credit) < 0.01, (debit, credit)
    return rows


def income_statement() -> list[tuple[str, float]]:
    tb = trial_balance()
    by = defaultdict(float)
    for _, _, _, subtype, dr, cr in tb:
        by[subtype] += dr - cr
    revenue = -by["Operating Revenue"]
    returns = by["Contra Revenue"]
    net = revenue - returns
    cogs = by["COGS"]
    opex = by["Operating Expense"]
    other = by["Other Income or Expense"] + by["Other Expense"] - by["Other Income"]
    income = net - cogs - opex - other
    close = one("SELECT TotalAmount FROM JournalEntry WHERE EntryNumber = 'JE-2026-000297'")[0]
    assert abs(income - close) < 0.01, (income, close)
    return [("Operating revenue", revenue), ("Sales returns and allowances", -returns), ("Net revenue", net),
            ("Cost of goods sold", -cogs), ("Gross margin", net - cogs), ("Operating expenses", -opex),
            ("Operating income", net - cogs - opex), ("Other income and expense", -other),
            ("Net income", income)]


def fig_06_ledger() -> Diagram:
    d = Diagram("From the Trial Balance to the Income Statement")
    tb = trial_balance()
    kept = ["AccountID", "Debit", "Credit", "AccountNumber", "AccountName", "AccountType", "AccountSubType",
            "Balance", "DebitBalance", "CreditBalance"]
    heads = ["AccountNumber", "AccountName", "AccountSubType", "DebitBalance", "CreditBalance"]
    letters = [chr(65 + kept.index(h)) for h in heads]
    rows = []
    for i, (number, name, _, subtype, dr, cr) in enumerate(tb[:6]):
        bal = dr - cr
        rows.append((str(i + 2), [str(number), name, subtype, xl.num(max(0.0, bal)), xl.num(max(0.0, -bal))]))
    rows.append(("…", ["…", "", "", "", ""]))
    debit = sum(max(0.0, r[4] - r[5]) for r in tb)
    credit = sum(max(0.0, r[5] - r[4]) for r in tb)
    rows.append((str(len(tb) + 2), ["Total", "", "", xl.num(debit), xl.num(credit)]))

    def extra(r: int, c: int, value: str) -> dict:
        if r == len(rows) - 1:
            return dict(label=f"<b>{esc(value)}</b>", fill=GRAY_TINT)
        return {}

    widths = [36, 116, 250, 150, 150, 150]
    d.text("<b>TrialBalance worksheet</b>", 0, 0, 860, 22, size=SMALL)
    geo = xl.table_view(d, 0, 24, letters, widths, heads, rows, extra=extra)
    x0, y0, _, _ = geo[(len(rows), 3)]
    xl.emphasis(d, x0, y0, widths[4] + widths[5], ROW_H)
    y = 24 + 22 + ROW_H * (len(rows) + 1) + 26
    d.text("<b>IncomeStatement worksheet</b>", 0, y, 860, 22, size=SMALL)
    statement = income_statement()
    net = statement[2][1]
    body = [("1", ["Fiscal 2026", "Amount", "% of net revenue"])]
    for i, (label, value) in enumerate(statement):
        body.append((str(i + 2), [label, xl.num(value), f"{100 * value / net:.2f}%"]))
    totals = {"Net revenue", "Gross margin", "Operating income", "Net income"}

    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c == 0 else {}
        if r == 0:
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>")
        elif body[r][1][0] in totals:
            out.update(label=f"<b>{esc(value)}</b>")
        return out

    xl.formula_bar(d, 0, y + 24, 860, "B2",
                   '=-SUMIFS(TrialBalance[Balance],TrialBalance[AccountSubType],"Operating Revenue")')
    geo2 = xl.sheet(d, 0, y + 64, ["A", "B", "C"], [36, 280, 170, 170], body, style)
    xl.select(d, *geo2[(1, 1)])
    x0, y0, _, _ = geo2[(len(body) - 1, 0)]
    xl.emphasis(d, x0, y0, 280 + 170 + 170, ROW_H)
    bottom = y + 64 + 22 + ROW_H * len(body)
    d.text("<i>The trial balance holds one row for each account with postings through 2026-12-31, without the "
           "2026 closing entries, and a Total Row; columns such as Debit, Credit, and Balance are hidden. Outlined: the equal "
           "debit and credit balances, and net income, which equals the 2026 closing entry to retained "
           "earnings.</i>", 0, bottom + 8, 860, 56, size=SMALL, color=GRAY)
    return d


def fig_06_02() -> Diagram:
    d = Diagram("How the PivotTable Fields Areas Build a PivotTable")
    # Left: the PivotTable Fields pane.
    pw = 250
    xl.title_bar(d, 0, 0, pw, "PivotTable Fields")
    d.text("Choose fields to add to report:", 6, 32, pw - 12, 20, size=SMALL)
    fields = [("SalesInvoiceLineID", False), ("Quantity", False), ("LineTotal", True),
              ("PromotionID", False), ("ItemGroup", True), ("CustomerSegment", False),
              ("FiscalYear", True), ("Period", True), ("ProductType", False)]
    y = 56
    for name, on in fields:
        xl.checkbox(d, 8, y + 4, on)
        d.text(f"<b>{name}</b>" if on else name, 28, y, pw - 34, 22, size=SMALL, valign="middle")
        y += 22
    d.text("Drag fields between areas below:", 6, y + 6, pw - 12, 20, size=SMALL)
    y += 30
    areas = [("1", "Filters", "FiscalYear"), ("2", "Columns", "Period"),
             ("3", "Rows", "ItemGroup"), ("4", "Values", "Sum of LineTotal")]
    aw = (pw - 6) / 2
    for i, (num, area, field) in enumerate(areas):
        ax = (i % 2) * (aw + 6)
        ay = y + (i // 2) * 74
        d.box(f"<b>{area}</b>", ax, ay, aw, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              align="left", rounded=False)
        d.box(esc(field), ax, ay + 24, aw, 44, fill=WHITE, stroke=RULE, size=SMALL, align="left",
              valign="top", rounded=False)
        d.marker(num, ax + aw - 26, ay + 2, size=20)
    pane_bottom = y + 2 * 74
    d.box("", 0, 28, pw, pane_bottom - 28, fill="none", stroke=RULE, rounded=False)

    # Right: the PivotTable those areas produce. Whole dollars keep the columns narrow.
    px = 290
    widths = [120, 90, 90, 90, 90, 90]
    whole = lambda v: f"{v:,.0f}"
    rows = [["FiscalYear", "2026 ▾", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["Sum of LineTotal", "Column Labels ▾"],
            ["Row Labels ▾", *QUARTERS, "Grand Total"]]
    for g in PIVOT_GROUPS:
        rows.append([g, *(whole(total("R", grp=g, per=p)) for p in QUARTERS),
                     whole(total("R", grp=g, fy=2026))])
    rows.append(["Grand Total", *(whole(total("R", per=p)) for p in QUARTERS),
                 whole(total("R", fy=2026))])
    xs = [px]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    top = 30
    for r, values in enumerate(rows):
        header = r in (2, 3)
        grand = r == len(rows) - 1
        cells = list(zip(values, xs, widths))
        if r == 2:   # the column-labels caption spans the value columns
            cells = [(values[0], xs[0], widths[0]), (values[1], xs[1], sum(widths[1:]))]
        for c, (value, cx, w) in enumerate(cells):
            numeric = value[:1].isdigit() and r > 3
            label = f"<b>{esc(value)}</b>" if header or grand else esc(value)
            fill = BLUE_TINT if header or grand else WHITE
            d.box(label, cx, top + r * ROW_H, w, ROW_H, fill=fill, stroke=RULE, size=SMALL,
                  align="right" if numeric else "left", rounded=False)
    # Markers keyed to the areas in the pane.
    right = px + sum(widths)
    d.marker("1", xs[2] + 4, top + 2, size=20)
    d.marker("2", xs[3] + 4, top + 2 * ROW_H + 2, size=20)
    d.marker("3", xs[0] + widths[0] - 24, top + 4 * ROW_H + 2, size=20)
    d.marker("4", xs[1] + 4, top + 4 * ROW_H + 2, size=20)
    bottom = max(pane_bottom, top + len(rows) * ROW_H)
    legend = [
        ("1", "Filters: FiscalYear limits the whole PivotTable to fiscal 2026."),
        ("2", "Columns: each Period becomes a column, and Excel adds a Grand Total column."),
        ("3", "Rows: each ItemGroup becomes a row, and Excel adds a Grand Total row."),
        ("4", "Values: LineTotal is summed for every combination of row and column."),
    ]
    y = bottom + 16
    for i, (num, text) in enumerate(legend):
        d.marker(num, 0, y + i * 28, size=22)
        d.text(esc(text), 30, y + i * 28, 830, 24)
    assert right <= 860
    return d


def _mini_pivot(d: Diagram, x: float, y: float, title: str, cols: list[str],
                rows: list[tuple[str, list[str]]], note: str, mark: str) -> None:
    widths = [96, 90, 90]
    d.text(f"<b>{esc(title)}</b>", x, y, sum(widths), 22, size=SMALL)
    xs = [x, x + widths[0], x + widths[0] + widths[1]]
    head = ["Row Labels", *cols]
    for cx, w, h in zip(xs, widths, head):
        d.box(f"<b>{esc(h)}</b>", cx, y + 24, w, ROW_H, fill=BLUE_TINT, stroke=RULE, size=SMALL,
              align="left" if cx == x else "right", rounded=False)
    for r, (label, values) in enumerate(rows):
        grand = label == "Grand Total"
        ry = y + 24 + (r + 1) * ROW_H
        for c, (cx, w, v) in enumerate(zip(xs, widths, [label, *values])):
            d.box(f"<b>{esc(v)}</b>" if grand else esc(v), cx, ry, w, ROW_H,
                  fill=BLUE_TINT if grand else WHITE, stroke=RULE, size=SMALL,
                  align="left" if c == 0 else "right", rounded=False)
        if label == mark:
            xl.emphasis(d, xs[2], ry, widths[2], ROW_H)
    d.text(f"<i>{esc(note)}</i>", x, y + 24 + (len(rows) + 1) * ROW_H + 4, sum(widths), 40,
           size=SMALL, color=GRAY)


def fig_06_03() -> Diagram:
    d = Diagram("One PivotTable Shown Three Ways with Show Values As")
    cols = ["2026-Q3", "2026-Q4"]
    rev = {(g, p): total("R", grp=g, per=p) for g in PIVOT_GROUPS for p in QUARTERS}
    col_total = {p: total("R", per=p) for p in QUARTERS}
    plain = [(g, [xl.num(rev[(g, p)]) for p in cols]) for g in PIVOT_GROUPS]
    plain.append(("Grand Total", [xl.num(col_total[p]) for p in cols]))
    share = [(g, [pct(rev[(g, p)] / col_total[p]) for p in cols]) for g in PIVOT_GROUPS]
    share.append(("Grand Total", ["100.00%", "100.00%"]))
    prev = {"2026-Q3": "2026-Q2", "2026-Q4": "2026-Q3"}
    diff = [(g, [signed_pct(rev[(g, p)] / rev[(g, prev[p])] - 1) for p in cols]) for g in PIVOT_GROUPS]
    diff.append(("Grand Total", [signed_pct(col_total[p] / col_total[prev[p]] - 1) for p in cols]))
    assert rev[("Furniture", "2026-Q4")] < rev[("Furniture", "2026-Q3")]
    _mini_pivot(d, 0, 0, "No Calculation", cols, plain,
                "Sum of LineTotal, as the PivotTable first shows it.", "Furniture")
    _mini_pivot(d, 292, 0, "% of Column Total", cols, share,
                "Each group's share of the quarter's revenue.", "Furniture")
    _mini_pivot(d, 584, 0, "% Difference From", cols, diff,
                "The change from the previous Period (the Base item).", "Furniture")
    d.text("<i>The same Sum of LineTotal value field, fiscal 2026. Outlined: Furniture in the fourth "
           "quarter, read three ways.</i>", 0, 24 + 7 * ROW_H + 52, 860, 20, size=SMALL, color=GRAY)
    return d


def fig_06_04() -> Diagram:
    d = Diagram("The Insert Calculated Field Dialog")
    xl.title_bar(d, 0, 0, 860, "Insert Calculated Field")
    d.text("<b>Name:</b>", 16, 44, 90, 24, size=SMALL, valign="middle")
    d.box("MarginPct ▾", 110, 44, 520, 26, fill=WHITE, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    d.text("<b>Formula:</b>", 16, 80, 90, 24, size=SMALL, valign="middle")
    d.box("=(LineTotal-StdCostAmount)/LineTotal", 110, 80, 520, 26, fill=WHITE, stroke=RULE,
          size=SMALL, align="left", rounded=False)
    xl.emphasis(d, 110, 44, 520, 62)
    xl.button(d, 650, 44, 90, "Add")
    xl.button(d, 650, 80, 90, "Delete")
    d.text("<b>Fields:</b>", 16, 120, 200, 20, size=SMALL)
    fields = ["SalesInvoiceLineID", "Quantity", "UnitPrice", "Discount", "LineTotal", "PromotionID",
              "ItemGroup", "StandardCost", "FiscalYear", "Period", "StdCostAmount"]
    for i, name in enumerate(fields):
        on = name in ("LineTotal", "StdCostAmount")
        d.box(f"<b>{name}</b>" if on else name, 110, 142 + i * 22, 300, 22,
              fill=BLUE_TINT if on else WHITE, stroke=RULE, size=SMALL, align="left",
              rounded=False)
    list_bottom = 142 + len(fields) * 22
    xl.button(d, 110, list_bottom + 8, 110, "Insert Field")
    xl.button(d, 650, list_bottom + 8, 90, "OK", primary=True)
    xl.button(d, 750, list_bottom + 8, 90, "Close")
    d.box("", 0, 28, 860, list_bottom + 44 - 28, fill="none", stroke=RULE, rounded=False)
    d.text("<i>Only some of the fields are shown. Outlined: the name and the formula. A "
           "calculated field divides the sum of the margin by the sum of LineTotal for each cell of "
           "the PivotTable.</i>", 0, list_bottom + 52, 860, 40, size=SMALL, color=GRAY)
    return d


def fig_06_05() -> Diagram:
    d = Diagram("Revenue and Margin at Standard Cost by Item Group and Quarter")
    body = [("1", ["FiscalYear", "2026 ▾", "", "", "", ""]),
            ("2", ["", "", "", "", "", ""]),
            ("3", ["", "Column Labels ▾", "", "", "", ""]),
            ("4", ["Row Labels ▾", *QUARTERS, "Grand Total"])]
    group_rows, indent, marks = set(), set(), {}
    for g in PIVOT_GROUPS:
        group_rows.add(len(body))
        body.append((str(len(body) + 1), [g, "", "", "", "", ""]))
        indent.add(len(body))
        body.append((str(len(body) + 1), ["Sum of LineTotal",
                                          *(xl.num(total("R", grp=g, per=p)) for p in QUARTERS),
                                          xl.num(total("R", grp=g, fy=2026))]))
        indent.add(len(body))
        marks[g] = len(body)
        body.append((str(len(body) + 1), ["Sum of MarginPct",
                                          *(pct(margin_pct(grp=g, per=p)) for p in QUARTERS),
                                          pct(margin_pct(grp=g, fy=2026))]))
    totals = {len(body), len(body) + 1}
    body.append((str(len(body) + 1), ["Total Sum of LineTotal", *(xl.num(total("R", per=p)) for p in QUARTERS),
                                      xl.num(total("R", fy=2026))]))
    body.append((str(len(body) + 1), ["Total Sum of MarginPct", *(pct(margin_pct(per=p)) for p in QUARTERS),
                                      pct(margin_pct(fy=2026))]))
    assert margin_pct(grp="Furniture", per="2026-Q4") < margin_pct(grp="Furniture", per="2026-Q3")
    assert abs(margin_pct(grp="Services", fy=2026) - 1) < 1e-12, "Services carries no standard cost"
    style = pivot_style(header_rows={2, 3}, bold_rows=group_rows, total_rows=totals,
                        indent_rows=indent)
    widths = [36, 214, 118, 118, 118, 118, 118]
    geo = xl.sheet(d, 0, 0, ["A", "B", "C", "D", "E", "F"], widths, body, style)
    for g in ("Furniture", "Services"):
        x0, y0, _, _ = geo[(marks[g], 0)]
        xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H)
    bottom = 22 + ROW_H * len(body)
    d.text("<i>Σ Values is in the Rows area, so each group shows its revenue and its margin. Outlined: "
           "the Furniture margin, which falls in the fourth quarter, and the Services margin, which is "
           "100 percent only because design services carry no standard cost.</i>", 0, bottom + 8,
           860, 40, size=SMALL, color=GRAY)
    return d


def fig_06_06() -> Diagram:
    d = Diagram("The Furniture Driver PivotTable for the Third and Fourth Quarters")
    t = bridge()["drivers"]
    a, b = t["2026-Q3"], t["2026-Q4"]
    measures = [
        ("Sum of Quantity", a["U"], b["U"], "num"),
        ("Sum of ListAmount", a["L"], b["L"], "num"),
        ("Sum of LineTotal", a["R"], b["R"], "num"),
        ("Sum of DiscountAmount", a["D"], b["D"], "num"),
        ("Sum of StdCostAmount", a["C"], b["C"], "num"),
        ("Sum of PricePerUnit", a["R"] / a["U"], b["R"] / b["U"], "num"),
        ("Sum of ListPerUnit", a["L"] / a["U"], b["L"] / b["U"], "num"),
        ("Sum of CostPerUnit", a["C"] / a["U"], b["C"] / b["U"], "num"),
        ("Sum of MarginPct", (a["R"] - a["C"]) / a["R"], (b["R"] - b["C"]) / b["R"], "pct"),
        ("Sum of MarginBeforeDiscountPct", (a["R"] + a["D"] - a["C"]) / (a["R"] + a["D"]),
         (b["R"] + b["D"] - b["C"]) / (b["R"] + b["D"]), "pct"),
    ]
    body = [("1", ["ItemGroup", "Furniture ▾", ""]),
            ("2", ["", "", ""]),
            ("3", ["", "Column Labels ▾", ""]),
            ("4", ["Values", "2026-Q3", "2026-Q4"])]
    changes = []
    for label, v3, v4, kind in measures:
        fmt = xl.num if kind == "num" else pct
        body.append((str(len(body) + 1), [label, fmt(v3), fmt(v4)]))
        if kind == "num":
            changes.append(signed_pct(v4 / v3 - 1))
        else:
            points = 100 * (v4 - v3)
            changes.append(f"{'+' if points >= 0 else '−'}{abs(points):.2f} points")
    style = pivot_style(header_rows={2, 3}, bold_rows=set(), total_rows=set())
    widths = [36, 250, 140, 140]
    geo = xl.sheet(d, 0, 0, ["A", "B", "C"], widths, body, style)
    cx = sum(widths) + 24
    _, hy, _, _ = geo[(3, 0)]
    d.text("<b>Q4 against Q3</b>", cx, hy, 860 - cx, ROW_H, size=SMALL, color=GRAY, valign="middle")
    for i, change in enumerate(changes):
        _, ry, _, _ = geo[(4 + i, 0)]
        d.text(f"<i>{esc(change)}</i>", cx, ry, 860 - cx, ROW_H, size=SMALL, color=GRAY,
               valign="middle")
    for label in ("Sum of DiscountAmount", "Sum of PricePerUnit", "Sum of MarginBeforeDiscountPct"):
        r = 4 + [m[0] for m in measures].index(label)
        x0, y0, _, _ = geo[(r, 0)]
        xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H)
    bottom = 22 + ROW_H * len(body)
    d.text("<i>Grand totals are turned off. The gray column at the right was added for this figure and "
           "is not part of the PivotTable. Outlined: the discounts and the price per unit, which move, "
           "and the margin before discounts, which does not fall.</i>", 0, bottom + 8, 860, 40,
           size=SMALL, color=GRAY)
    return d


def fig_06_07() -> Diagram:
    d = Diagram("The Furniture Margin Bridge from the Third to the Fourth Quarter")
    b = bridge()
    steps = [("2026-Q3<br>margin", b["q3"], "total"), ("Volume", b["volume"], "step"),
             ("Mix", b["mix"], "step"), ("Price lists", b["price lists"], "step"),
             ("Promotions", b["promotions"], "step"), ("Cost", b["cost"], "step"),
             ("2026-Q4<br>margin", b["q4"], "total")]
    lo, hi, step = 1_600_000, 1_850_000, 50_000
    top, height = 20, 400
    left, right = 96, 856
    scale = height / (hi - lo)
    y_of = lambda v: top + (hi - v) * scale
    for tick in range(lo, hi + 1, step):
        ty = y_of(tick)
        d.box("", left, ty, right - left, 1, fill=RULE, stroke=RULE, rounded=False)
        d.text(f"${tick:,}", 0, ty - 11, left - 8, 22, size=SMALL, color=INK, align="right",
               valign="middle")
    slot = (right - left) / len(steps)
    bar_w = 64
    level = 0.0
    tops = []
    for i, (label, value, kind) in enumerate(steps):
        bx = left + i * slot + (slot - bar_w) / 2
        if kind == "total":
            y0, y1 = y_of(value), y_of(lo)
            fill, stroke = BLUE, BLUE
            level = value
            text = f"${value:,.0f}"
        else:
            start, end = level, level + value
            y0, y1 = y_of(max(start, end)), y_of(min(start, end))
            fill, stroke = (TEAL, TEAL) if value > 0 else (CORAL, CORAL)
            if value == 0:
                fill, stroke = GRAY, GRAY
            level = end
            sign = "+" if value > 0 else "−" if value < 0 else ""
            text = f"{sign}${abs(value):,.0f}"
        h = max(y1 - y0, 2)
        d.box("", bx, y0, bar_w, h, fill=fill, stroke=stroke, rounded=False)
        above = kind == "total" or value >= 0
        ly = y0 - 24 if above else y0 + h + 2
        d.text(f"<b>{esc(text)}</b>", bx - 22, ly, bar_w + 44, 22, size=SMALL, align="center",
               valign="middle")
        d.text(f"<b>{label}</b>", bx - 22, top + height + 6, bar_w + 44, 36, size=SMALL,
               align="center")
        tops.append((bx, y_of(level)))
    # Connectors between bars at the running level.
    for (x1, y1), (x2, _) in zip(tops, tops[1:]):
        a = d.anchor(x1 + bar_w, y1)
        c = d.anchor(x2, y1)
        d.edge(a, c, color=GRAY, width=1.5)
    y = top + height + 50
    legend = [(BLUE, "Margin at standard cost"), (TEAL, "Increase (+)"),
              (CORAL, "Decrease (−)"), (GRAY, "No effect")]
    x = left
    for fill, text in legend:
        d.box("", x, y + 4, 16, 16, fill=fill, stroke=fill, rounded=False)
        d.text(esc(text), x + 22, y, 160, 24, size=SMALL, valign="middle")
        x += 185
    d.text("<i>The vertical axis starts at $1,600,000 so that the small effects are visible. The "
           "effects sum exactly to the change in margin.</i>", 0, y + 30, 860, 40, size=SMALL,
           color=GRAY)
    return d


def fig_06_08() -> Diagram:
    d = Diagram("Furniture Discounts by Promotion and Quarter")
    cols = ["2026-Q3", "2026-Q4"]
    agg = defaultdict(lambda: [0, 0.0])
    for r in lines():
        if r["grp"] == "Furniture" and r["per"] in cols:
            key = (r["promo"], r["per"])
            agg[key][0] += 1
            agg[key][1] += r["D"]
    promos = sorted({k[0] for k in agg}, key=lambda p: (p is not None, p or 0))
    assert max(promos[1:], key=lambda p: agg[(p, "2026-Q4")][1]) == 8
    body = [("1", ["ItemGroup", "Furniture ▾", "", "", ""]),
            ("2", ["", "", "", "", ""]),
            ("3", ["", "Column Labels ▾", "", "", ""]),
            ("4", ["", "2026-Q3", "", "2026-Q4", ""]),
            ("5", ["Row Labels ▾", "Count of Lines", "Sum of Discount", "Count of Lines",
                   "Sum of Discount"])]
    mark_rows = {}
    for p in promos:
        values = []
        for c in cols:
            n, disc = agg.get((p, c), [0, 0.0])
            values += [f"{n:,}" if n else "", xl.num(disc) if n else ""]
        mark_rows[p] = len(body)
        body.append((str(len(body) + 1), ["(blank)" if p is None else str(p), *values]))
    style = pivot_style(header_rows={2, 3, 4}, bold_rows=set(), total_rows=set())
    widths = [36, 150, 150, 150, 150, 150]
    geo = xl.sheet(d, 0, 0, ["A", "B", "C", "D", "E"], widths, body, style)
    x0, y0, _, _ = geo[(mark_rows[8], 0)]
    xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H)
    x0, y0, _, _ = geo[(mark_rows[9], 3)]
    xl.emphasis(d, x0, y0, widths[4] + widths[5], ROW_H)
    y = 22 + ROW_H * len(body) + 20
    d.text("<b>PromotionProgram Table</b>", 0, y, 860, 22, size=SMALL)
    promo_rows = q("SELECT PromotionID, PromotionCode, PromotionName, ScopeType, DiscountPct "
                   "FROM PromotionProgram WHERE PromotionID IN (" +
                   ",".join(str(p) for p in promos if p) + ") ORDER BY 1")
    heads = ["PromotionID", "PromotionCode", "PromotionName", "ScopeType", "DiscountPct"]
    body2 = [(str(pid + 1), [str(pid), code, name, scope, f"{disc:.2f}"])
             for pid, code, name, scope, disc in promo_rows]
    widths2 = [36, 110, 150, 290, 120, 110]
    letters2 = [chr(65 + PROMO_COLUMNS.index(h)) for h in heads]
    xl.table_view(d, 0, y + 24, letters2, widths2, heads, body2)
    bottom = y + 24 + 22 + ROW_H * (len(body2) + 1)
    d.text("<i>The Count of Lines and Sum of Discount headings are custom names for Count of "
           "SalesInvoiceLineID and Sum of DiscountAmount; columns E through G of the PromotionProgram "
           "Table are hidden. Outlined: promotion 8 in both quarters and "
           "promotion 9, which began in November.</i>", 0, bottom + 8, 860, 40, size=SMALL,
           color=GRAY)
    return d


FIGURES = {
    "fig-06-01-fiscal-2026-profile": fig_06_01,
    "fig-06-02-line-total-histogram": fig_06_histogram,
    "fig-06-03-pivottable-areas": fig_06_02,
    "fig-06-04-show-values-as": fig_06_03,
    "fig-06-05-calculated-field": fig_06_04,
    "fig-06-06-revenue-margin-pivot": fig_06_05,
    "fig-06-07-ledger-to-income-statement": fig_06_ledger,
    "fig-06-08-furniture-drivers": fig_06_06,
    "fig-06-09-margin-bridge": fig_06_07,
    "fig-06-10-discounts-by-promotion": fig_06_08,
}
