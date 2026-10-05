"""Chapter 7 figures."""

from __future__ import annotations

import html
import math
import statistics
from collections import defaultdict
from functools import lru_cache

import excel as xl
from data import connection, one, q, require_columns
from shared.calculations.excel_analysis import (forecast_backtest, _betacf, _betai, t_two_sided, t_critical, regression, monthly_revenue as shared_monthly_revenue, flex as shared_flex, promotion_model as shared_promotion_model)
from drawio import (BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, ROW_H, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc)

GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CLOSE_2026 = "JE-2026-000296"


# -- statistics without third-party packages ------------------------------------------


def general(value: float, digits: int = 10) -> str:
    """Roughly how Excel's General format shows a number in a column about 11 characters wide."""
    if value == int(value) and abs(value) < 10 ** digits:
        return f"{int(value)}"
    if abs(value) < 1e-4:
        return f"{value:.2E}".replace("E-0", "E-")
    if abs(value) >= 10 ** 9:
        return f"{value:.4E}".replace("E+0", "E+").replace("E+", "E+")
    whole = len(str(int(abs(value))))
    return f"{value:.{max(0, digits - whole - (value < 0))}f}".rstrip("0").rstrip(".")


# -- data -------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def monthly_revenue() -> list[tuple[str, float]]:
    return shared_monthly_revenue(connection())


@lru_cache(maxsize=1)
def flex() -> dict:
    return shared_flex(connection())


@lru_cache(maxsize=1)
def promotion_model() -> dict:
    return shared_promotion_model(connection())


# -- drawing helpers --------------------------------------------------------------------

def seg(d: Diagram, x1: float, y1: float, x2: float, y2: float, color: str, width: float = 2,
        dashed: bool = False) -> None:
    """A straight line between two points (charts need diagonal segments, not routed edges)."""
    d._track(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    style = (f"endArrow=none;startArrow=none;html=1;strokeColor={color};strokeWidth={width:g};"
             f"{'dashed=1;dashPattern=6 4;' if dashed else ''}")
    d.cells.append(
        f'<mxCell id="{d._id("s")}" value="" style="{style}" edge="1" parent="1">'
        f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1:g}" y="{y1:g}" as="sourcePoint"/>'
        f'<mxPoint x="{x2:g}" y="{y2:g}" as="targetPoint"/></mxGeometry></mxCell>')


def dot(d: Diagram, x: float, y: float, color: str, size: float = 7) -> None:
    d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={color};", x - size / 2, y - size / 2,
             size, size)


def axis(d: Diagram, left: float, right: float, top: float, height: float, lo: float, hi: float,
         step: float, fmt) -> callable:
    y_of = lambda v: top + (hi - v) * height / (hi - lo)
    v = lo
    while v <= hi + 1e-9:
        ty = y_of(v)
        d.box("", left, ty, right - left, 1, fill=RULE, stroke=RULE, rounded=False)
        d.text(esc(fmt(v)), 0, ty - 11, left - 8, 22, size=SMALL, align="right", valign="middle")
        v += step
    return y_of


def legend(d: Diagram, x: float, y: float, items: list[tuple[str, bool, str]], gap: float = 280) -> None:
    for color, dashed, label in items:
        seg(d, x, y + 12, x + 36, y + 12, color, 2.5, dashed)
        d.text(esc(label), x + 44, y, gap - 50, 24, size=SMALL, valign="middle")
        x += gap


# -- figures ----------------------------------------------------------------------------

def fig_07_01() -> Diagram:
    d = Diagram("Monthly Revenue with Two Fitted Trends")
    rows = monthly_revenue()
    ys = [v for _, v in rows]
    xs = list(range(1, 37))
    full, trimmed = regression(xs, ys), regression(xs[1:], ys[1:])
    assert full["p_b"] < 0.05 < trimmed["p_b"], (full["p_b"], trimmed["p_b"])
    left, right, top, height = 96, 846, 20, 380
    y_of = axis(d, left, right, top, height, 1_200_000, 2_800_000, 400_000,
                lambda v: f"${v / 1e6:.1f}M")
    x_of = lambda i: left + 10 + (i - 1) * (right - left - 20) / 35
    for i in range(1, 36):
        seg(d, x_of(i), y_of(ys[i - 1]), x_of(i + 1), y_of(ys[i]), BLUE, 2)
    for i, y in enumerate(ys, 1):
        dot(d, x_of(i), y_of(y), BLUE)
    seg(d, x_of(1), y_of(full["a"] + full["b"]), x_of(36), y_of(full["a"] + 36 * full["b"]), CORAL, 2.5,
        dashed=True)
    seg(d, x_of(2), y_of(trimmed["a"] + 2 * trimmed["b"]), x_of(36), y_of(trimmed["a"] + 36 * trimmed["b"]),
        TEAL, 2.5)
    d.text("January 2024,<br>the start-up month", x_of(1) + 10, y_of(ys[0]) - 18, 160, 36, size=SMALL,
           color=INK)
    for i, (month, _) in enumerate(rows, 1):
        if month[5:] in ("01", "07"):
            d.text(f"{MONTHS[int(month[5:]) - 1]} {month[:4]}", x_of(i) - 40, top + height + 6, 80, 20,
                   size=SMALL, align="center")
    y = top + height + 36
    legend(d, 0, y, [(BLUE, False, "Monthly revenue"),
                     (CORAL, True, f"Trend, all 36 months (R² {full['r2']:.2f})"),
                     (TEAL, False, f"Trend without January 2024 (R² {trimmed['r2']:.2f})")], gap=285)
    d.text("<i>Revenue is the total of the invoice lines in each month. The dashed line's upward slope "
           "comes mostly from the first month.</i>", 0, y + 32, 860, 40, size=SMALL, color=GRAY)
    return d


def fig_07_02() -> Diagram:
    d = Diagram("Regression Output from the Data Analysis ToolPak")
    ys = [v for _, v in monthly_revenue()]
    r = regression(list(range(1, 37)), ys)
    rows = [("1", ["SUMMARY OUTPUT", "", "", "", "", "", ""]),
            ("2", ["", "", "", "", "", "", ""]),
            ("3", ["Regression Statistics", "", "", "", "", "", ""]),
            ("4", ["Multiple R", general(math.sqrt(r["r2"])), "", "", "", "", ""]),
            ("5", ["R Square", general(r["r2"]), "", "", "", "", ""]),
            ("6", ["Adjusted R Square", general(r["adj"]), "", "", "", "", ""]),
            ("7", ["Standard Error", general(r["se"]), "", "", "", "", ""]),
            ("8", ["Observations", str(r["n"]), "", "", "", "", ""]),
            ("9", ["", "", "", "", "", "", ""]),
            ("10", ["ANOVA", "", "", "", "", "", ""]),
            ("11", ["", "df", "SS", "MS", "F", "Significance F", ""]),
            ("12", ["Regression", "1", general(r["ssr"]), general(r["ssr"]), general(r["f"]),
                    general(r["p_b"]), ""]),
            ("13", ["Residual", str(r["df"]), general(r["sse"]), general(r["sse"] / r["df"]), "", "", ""]),
            ("14", ["Total", str(r["n"] - 1), general(r["sst"]), "", "", "", ""]),
            ("15", ["", "", "", "", "", "", ""]),
            ("16", ["", "Coefficients", "Standard Error", "t Stat", "P-value", "Lower 95%", "Upper 95%"]),
            ("17", ["Intercept", general(r["a"]), general(r["se_a"]), general(r["t_a"]), general(r["p_a"]),
                    general(r["a"] - r["tcrit"] * r["se_a"]), general(r["a"] + r["tcrit"] * r["se_a"])]),
            ("18", ["MonthIndex", general(r["b"]), general(r["se_b"]), general(r["t_b"]), general(r["p_b"]),
                    general(r["b"] - r["tcrit"] * r["se_b"]), general(r["b"] + r["tcrit"] * r["se_b"])])]
    bold = {0, 2, 9, 10, 15}

    def style(rr: int, c: int, value: str) -> dict:
        if rr in bold and value:
            return dict(label=f"<b>{esc(value)}</b>", align="left" if c == 0 else "right")
        if c == 0:
            return dict(align="left")
        return {}

    widths = [30, 150, 112, 112, 112, 112, 112, 112]
    geo = xl.sheet(d, 0, 0, ["A", "B", "C", "D", "E", "F", "G"], widths, rows, style, row_h=22)
    marks = [("1", 4, 1, 1), ("2", 11, 5, 1), ("3", 17, 1, 1), ("4", 17, 4, 1)]
    for num, rr, c, span in marks:
        x0, y0, w, h = geo[(rr, c)]
        xl.emphasis(d, x0, y0, w * span, h)
        d.marker(num, x0 + 2, y0 + 1, size=20)
    bottom = 22 + 22 * len(rows)
    legend_rows = [
        ("1", f"R Square: the month index explains about {100 * r['r2']:.0f} percent of the month-to-month "
              "variation in revenue."),
        ("2", "Significance F: with one X variable, the same p-value as the slope."),
        ("3", "The slope: the average change in revenue from one month to the next along the fitted line."),
        ("4", "The slope's p-value, below 0.05 here, but only because of the start-up month."),
    ]
    y = bottom + 14
    for i, (num, text) in enumerate(legend_rows):
        d.marker(num, 0, y + i * 28, size=22)
        d.text(esc(text), 30, y + i * 28, 830, 24)
    return d


def fig_07_03() -> Diagram:
    d = Diagram("Backtesting Three Forecasts of the Fourth Quarter of 2026")
    backtest = forecast_backtest(connection())
    actual, methods = backtest["actual"], backtest["methods"]
    body = [("40", ["Method", "Oct 2026", "Nov 2026", "Dec 2026", "Quarter", "Error", "Monthly error"])]
    body.append(("41", ["Actual", *(xl.num(v, 0) for v in actual), xl.num(sum(actual), 0), "", ""]))
    errors = {}
    for i, (name, f) in enumerate(methods):
        err = sum(f) / sum(actual) - 1
        mape = statistics.mean(abs(fi - ai) / ai for fi, ai in zip(f, actual))
        errors[name] = (err, mape)
        body.append((str(42 + i), [name, *(xl.num(v, 0) for v in f), xl.num(sum(f), 0), f"{100 * err:+.2f}%",
                                   f"{100 * mape:.2f}%"]))
    assert abs(errors["Mean"][0]) < abs(errors["Trend"][0])

    def style(r: int, c: int, value: str) -> dict:
        if r == 0:
            return dict(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>", align="left" if c == 0 else "right")
        if r == 1:
            return dict(fill=BLUE_TINT, label=f"<b>{esc(value)}</b>", align="left" if c == 0 else "right")
        return dict(align="left") if c == 0 else dict(align="right")

    widths = [36, 230, 96, 96, 96, 100, 90, 112]
    geo = xl.sheet(d, 0, 0, ["A", "B", "C", "D", "E", "F", "G"], widths, body, style)
    x0, y0, _, _ = geo[(2, 5)]
    xl.emphasis(d, x0, y0, widths[6] + widths[7], ROW_H * 3)
    bottom = 22 + ROW_H * len(body)
    d.text("<i>Every method is fitted to February 2024 through September 2026 and compared with the "
           "actual fourth quarter: Trend with FORECAST.LINEAR, Mean as the average of the fitted months. Error "
           "is the quarter's forecast against its actual; monthly error is the average absolute percentage "
           "error of the three months. Outlined: the errors.</i>", 0,
           bottom + 8, 860, 60, size=SMALL, color=GRAY)
    return d


def fig_07_04() -> Diagram:
    d = Diagram("Static Budget, Flexible Budget, and Actual Results")
    f = flex()
    static = f[("Furniture", "static Revenue")] - f[("Furniture", "static COGS")]
    flexible = f[("Furniture", "flex")] - f[("Furniture", "cost")]
    actual = f[("Furniture", "actual")] - f[("Furniture", "cost")]
    boxes = [("Static budget", "Planned volume at planned prices and standard costs", static, BLUE),
             ("Flexible budget", "Actual volume at planned prices and standard costs", flexible, TEAL),
             ("Actual results", "Actual volume at actual prices, costed at standard", actual, GRAY)]
    w, gap, top = 240, 70, 40
    ids = []
    for i, (title, text, value, fill) in enumerate(boxes):
        x = i * (w + gap)
        d.header_box(esc(title), x, top, w, 34, fill=fill)
        ids.append(d.box(f"{esc(text)}<br><br><b>Furniture margin, fiscal 2026:<br>${value / 1e6:,.2f} million</b>",
                         x, top + 34, w, 120, fill=WHITE, stroke=RULE, align="center"))
    for i, (label, value) in enumerate([("Sales-volume variance", flexible - static),
                                        ("Flexible-budget variance", actual - flexible)]):
        x = i * (w + gap) + w / 2
        span = w + gap
        d.box(f"<b>{esc(label)}</b><br>{'−' if value < 0 else '+'}${abs(value) / 1e6:,.2f} million",
              x + 20, top + 190, span - 40, 52, fill=GRAY_TINT, stroke=RULE)
        seg(d, x, top + 154, x, top + 216, GRAY, 1.5)
        seg(d, x + span, top + 154, x + span, top + 216, GRAY, 1.5)
        seg(d, x, top + 216, x + 20, top + 216, GRAY, 1.5)
        seg(d, x + span - 20, top + 216, x + span, top + 216, GRAY, 1.5)
    d.text("<b>Measures the effect of volume:</b> what the plan's volume assumption was worth. At Charles "
           "River, the planned volume was several times what was sold.", 0, top + 260, 400, 60, size=SMALL)
    d.text("<b>Measures the effect of prices:</b> actual revenue against the plan's prices for the same "
           "units. Costs are at standard in both, so no cost effect appears here.", 440, top + 260, 420, 60,
           size=SMALL)
    d.text("<i>The flexible budget keeps the plan's prices and costs per unit but uses the actual quantity "
           "of each item sold in each month.</i>", 0, top + 330, 860, 40, size=SMALL, color=GRAY)
    return d


def fig_07_05() -> Diagram:
    d = Diagram("The Flexible-Budget Report by Product Line")
    f = flex()
    cols = GROUPS + ["Total"]

    def val(g: str, key: str) -> float:
        return sum(f[(x, key)] for x in GROUPS) if g == "Total" else f[(g, key)]

    lines = [
        ("Static budget revenue", lambda g: val(g, "static Revenue")),
        ("Static budget COGS", lambda g: val(g, "static COGS")),
        ("Static budget margin", lambda g: val(g, "static Revenue") - val(g, "static COGS")),
        ("Flexible budget revenue", lambda g: val(g, "flex")),
        ("Flexible budget COGS", lambda g: val(g, "cost")),
        ("Flexible budget margin", lambda g: val(g, "flex") - val(g, "cost")),
        ("Actual revenue", lambda g: val(g, "actual")),
        ("Actual COGS at standard", lambda g: val(g, "cost")),
        ("Actual margin", lambda g: val(g, "actual") - val(g, "cost")),
        ("Sales-volume variance", lambda g: val(g, "flex") - val(g, "cost") - val(g, "static Revenue")
         + val(g, "static COGS")),
        ("Flexible-budget variance", lambda g: val(g, "actual") - val(g, "flex")),
        ("Promotional discounts", lambda g: val(g, "discount")),
        ("Price gap before discounts", lambda g: val(g, "actual") - val(g, "flex") + val(g, "discount")),
        ("Budgeted units", lambda g: val(g, "static units")),
        ("Actual units", lambda g: val(g, "units")),
    ]
    body = [("3", ["", *cols])]
    for i, (label, fn) in enumerate(lines):
        body.append((str(4 + i), [label, *(f"{fn(g):,.0f}" for g in cols)]))
    for g in cols:
        static_m = val(g, "static Revenue") - val(g, "static COGS")
        flex_m, act_m = val(g, "flex") - val(g, "cost"), val(g, "actual") - val(g, "cost")
        assert abs(static_m + lines[9][1](g) + lines[10][1](g) - act_m) < 0.01, g
    for g in GROUPS:
        gap = (val(g, "actual") - val(g, "flex") + val(g, "discount")) / val(g, "flex")
        assert -0.045 < gap < -0.02, (g, gap)
    margin_rows = {3, 6, 9}
    variance_rows = {10, 11}

    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c == 0 else {}
        if r == 0:
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>", align="left" if c == 0 else "right")
        elif r in margin_rows:
            out.update(label=f"<b>{esc(value)}</b>")
        elif r in variance_rows:
            out.update(fill=TEAL_TINT, label=f"<b>{esc(value)}</b>")
        return out

    widths = [36, 222, 118, 118, 118, 118, 126]
    geo = xl.sheet(d, 0, 0, ["A", "B", "C", "D", "E", "F"], widths, body, style)
    x0, y0, _, _ = geo[(10, 0)]
    xl.emphasis(d, x0, y0, sum(widths[1:]), ROW_H * 2)
    bottom = 22 + ROW_H * len(body)
    d.text("<i>Whole dollars and units for fiscal 2026; Services, which the budget does not plan, is "
           "excluded. Outlined: the two variances. The price gap before discounts is the flexible-budget "
           "variance with the promotional discounts added back.</i>", 0, bottom + 8, 860, 40, size=SMALL,
           color=GRAY)
    return d


def fig_07_06() -> Diagram:
    d = Diagram("Planned and Actual Furniture Prices by Month")
    f = flex()
    planned = [f[("Furniture", m, "flex")] / f[("Furniture", m, "list")] for m in range(1, 13)]
    before = [(f[("Furniture", m, "actual")] + f[("Furniture", m, "discount")]) / f[("Furniture", m, "list")]
              for m in range(1, 13)]
    actual = [f[("Furniture", m, "actual")] / f[("Furniture", m, "list")] for m in range(1, 13)]
    assert min(range(12), key=lambda i: planned[i]) in (8, 9), planned
    assert actual[10] < before[10] - 0.01, "promotion discounts continue in November"
    left, right, top, height = 96, 846, 20, 360
    y_of = axis(d, left, right, top, height, 0.80, 0.96, 0.04, lambda v: f"{100 * v:.0f}%")
    x_of = lambda i: left + 30 + i * (right - left - 60) / 11
    for series, color, dashed in ((planned, GRAY, True), (before, TEAL, False), (actual, CORAL, False)):
        for i in range(11):
            seg(d, x_of(i), y_of(series[i]), x_of(i + 1), y_of(series[i + 1]), color, 2.5, dashed)
        for i, v in enumerate(series):
            dot(d, x_of(i), y_of(v), color)
    for i, name in enumerate(MONTHS):
        d.text(name, x_of(i) - 30, top + height + 6, 60, 20, size=SMALL, align="center")
    d.text("Promotion months<br>in the budget", x_of(8) - 40, top + 4, 110, 36, size=SMALL, align="center")
    y = top + height + 34
    legend(d, 0, y, [(GRAY, True, "Planned net price (budget)"),
                     (TEAL, False, "Actual price before promotions"),
                     (CORAL, False, "Actual price after promotions")], gap=285)
    d.text("<i>Each point is revenue divided by the list value of the Furniture units invoiced in the "
           "month of fiscal 2026. The budget lowered its planned price in September and October; the actual "
           "discounts started in September and continued into November and December.</i>", 0, y + 32, 860,
           40, size=SMALL, color=GRAY)
    return d


def fig_07_07() -> Diagram:
    d = Diagram("The Promotion Model on the Model Worksheet")
    m = promotion_model()
    rows = [
        ("1", ["Input or result", "Value", "Name", "Source"]),
        ("2", ["Discount rate", "10.00%", "Discount", "PromotionProgram, promotion 8"]),
        ("3", ["Volume lift", "0.00%", "Lift", "Assumption; order data shows none"]),
        ("4", ["Units on promotion lines", xl.num(m["units"]), "PromoUnits", "InvoiceLines, promotion 8"]),
        ("5", ["Price before discount per unit", xl.num(m["price"]), "PriceBeforeDiscount",
               "InvoiceLines, promotion 8"]),
        ("6", ["Variable cost per unit", xl.num(m["cost"]), "VariableCost", "Standard cost per unit"]),
        ("7", ["Commission rate", f"{100 * m['rate']:.2f}%", "CommissionRate", "Tutorial 7.2, actual 2026"]),
        ("8", ["", "", "", ""]),
        ("9", ["Contribution without promotion", xl.num(m["without"]), "ContributionWithout", "Formula"]),
        ("10", ["Contribution with promotion", xl.num(m["with"](0.10, 0)), "ContributionWith", "Formula"]),
        ("11", ["Difference", xl.num(m["with"](0.10, 0) - m["without"]), "Difference", "Formula"]),
    ]

    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c != 1 else {}
        if r == 0:
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>")
        elif r in (1, 2) and c == 1:
            out.update(color=BLUE, label=f"<b>{esc(value)}</b>")
        elif r == 10:
            out.update(label=f"<b>{esc(value)}</b>")
        return out

    xl.formula_bar(d, 0, 0, 860, "B11", "=ContributionWith-ContributionWithout")
    widths = [36, 240, 120, 170, 290]
    geo = xl.sheet(d, 0, 40, ["A", "B", "C", "D"], widths, rows, style)
    xl.select(d, *geo[(10, 1)])
    x0, y0, _, _ = geo[(1, 1)]
    xl.emphasis(d, x0, y0, widths[2], ROW_H * 2)
    bottom = 40 + 22 + ROW_H * len(rows)
    d.text("<i>Blue values are inputs; every other value is a formula on the named cells in column C. "
           "Outlined: the two inputs that the scenarios change.</i>", 0, bottom + 8, 860, 40, size=SMALL,
           color=GRAY)
    return d


def fig_07_08() -> Diagram:
    d = Diagram("The Scenario Summary Report")
    m = promotion_model()
    scenarios = [("End the promotion", 0.0, 0.0), ("Repeat as in 2026", 0.10, 0.0),
                 ("Repeat with 15% lift", 0.10, 0.15), ("Deeper discount", 0.15, 0.15)]
    current = (0.10, 0.0)
    cols = [("Current Values:", *current)] + scenarios
    head = ["", *(c[0] for c in cols)]
    body = [("2", ["Scenario Summary", "", "", "", "", ""]),
            ("3", head),
            ("4", ["Changing Cells:", "", "", "", "", ""]),
            ("5", ["Discount", *(f"{100 * c[1]:.0f}%" for c in cols)]),
            ("6", ["Lift", *(f"{100 * c[2]:.0f}%" for c in cols)]),
            ("7", ["Result Cells:", "", "", "", "", ""]),
            ("8", ["ContributionWith", *(xl.num(m["with"](c[1], c[2])) for c in cols)]),
            ("9", ["Difference", *(xl.num(m["with"](c[1], c[2]) - m["without"] + 0.0) for c in cols)])]
    assert all(m["with"](dd, ll) < m["without"] for _, dd, ll in scenarios[1:])

    def style(r: int, c: int, value: str) -> dict:
        out: dict = dict(align="left") if c == 0 else {}
        if r == 0 and c == 0:
            out.update(label=f"<b>{esc(value)}</b>", fill=GRAY, color=WHITE)
        elif r == 0:
            out.update(fill=GRAY)
        elif r == 1:
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>", align="left" if c == 0 else "right")
        elif r in (2, 5):
            out.update(fill=GRAY_TINT, label=f"<b>{esc(value)}</b>" if value else "")
        elif r in (3, 4) and c >= 2:
            out.update(fill=GRAY_TINT)
        if r in (3, 4, 6, 7) and c == 0:
            out.update(label=f"&nbsp;&nbsp;&nbsp;{esc(value)}")
        return out

    widths = [36, 170, 132, 132, 132, 136, 122]
    geo = xl.sheet(d, 0, 0, ["B", "C", "D", "E", "F", "G"], widths, body, style)
    x0, y0, _, _ = geo[(7, 2)]
    xl.emphasis(d, x0, y0, sum(widths[3:]), ROW_H)
    bottom = 22 + ROW_H * len(body)
    d.text("<i>Excel's report on a new worksheet, with the notes it adds below the table left out. Current "
           "Values are the inputs on the Model worksheet when the report was created; the changing cells of "
           "each scenario are shaded. Outlined: the difference each scenario makes to the contribution of the "
           "promotion's orders.</i>", 0, bottom + 8, 860, 60, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-07-01-monthly-revenue-trend": fig_07_01,
    "fig-07-02-regression-output": fig_07_02,
    "fig-07-03-forecast-backtest": fig_07_03,
    "fig-07-04-flexible-budget-levels": fig_07_04,
    "fig-07-05-flexible-budget-report": fig_07_05,
    "fig-07-06-furniture-price-by-month": fig_07_06,
    "fig-07-07-promotion-model": fig_07_07,
    "fig-07-08-scenario-summary": fig_07_08,
}
