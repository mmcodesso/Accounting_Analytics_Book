"""Chapter 15 figures (reports for management decisions).

Every value is computed here from the dataset with the logic of the chapter's measures: the gross
to net of Tutorial 15.1 (List Amount, Price Before Discount, Revenue), the budget of Tutorial 15.2
(BudgetLine without the balance-sheet lines, operating expense by AccountSubType, the ledger with
the year-end closes excluded, the commission budget flexed at the budget's monthly rate on invoiced
product revenue), and the plant measures of Tutorial 15.3 (direct and indirect hours per standard
hour of output, the output cut off at the last work date). The same values were checked against
Power BI Desktop 2.158's engine on a reference model of the tutorials.
"""

from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

import excel as xl
import powerbi as pbi
from ch13 import lines as lines13, total as total13
from data import one, q, require_columns
from data import connection
from shared.calculations import bi_ch15 as public_calculations
from drawio import (AMBER, BLUE, BLUE_TINT, CORAL, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc)

NOCLOSE = public_calculations.NOCLOSE
MONTHS_2026 = [f"2026-{m:02d}" for m in range(1, 13)]


def money(v: float) -> str:
    return pbi.amount(v) if abs(v) >= 0.005 else "0.00"


def pct(v: float, places: int = 1) -> str:
    return f"{100 * v:.{places}f}%"


# -- data: promotions ------------------------------------------------------------------------

@lru_cache(maxsize=1)
def gross_to_net() -> tuple[float, float, float]:
    return public_calculations.gross_to_net(connection())


@lru_cache(maxsize=1)
def promotion_discounts() -> list[tuple[str, float, int]]:
    return public_calculations.promotion_discounts(connection())


def promotion_by_month(name: str) -> list[tuple[str, float, int]]:
    return public_calculations.promotion_by_month(connection() ,name)


# -- data: budget ----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def budget_data() -> dict:
    return public_calculations.budget_data(connection())


# -- data: plant -----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def plant_months() -> dict:
    return public_calculations.plant_months(connection())


def ttm(month: str, first: str = "2024-01") -> float | None:
    return public_calculations.ttm(connection() ,month, first)


# -- fig-15-01 --------------------------------------------------------------------------------

def fig_15_01() -> Diagram:
    d = Diagram("The Reporting Package and Its Readers")
    about = d.box("", 0, 40, 150, 240, fill=WHITE, stroke=GRAY, stroke_width=2)
    d.header_box("About", 0, 40, 150, 30, fill=GRAY, size=SMALL)
    d.text("The first page: purpose, readers, source, period, and where each KPI is defined and tested. "
           "It holds the page navigator, as every visible page does.", 6, 76, 138, 200, size=SMALL)
    d.box("<b>Page navigator</b>: one button for each visible page", 190, 0, 670, 28, fill=BLUE_TINT,
          stroke=BLUE, size=SMALL)
    pages = [("Promotions", "Sales manager", "Revenue from list price to net; discounts by promotion"),
             ("Budget", "Department managers", "Operating expense against the budget, flexed for volume"),
             ("Plant", "Production manager", "Hours per standard hour over twelve months, against 2024"),
             ("Validation", "Controller", "Control totals of the earlier chapters; the Tests tab")]
    boxes = {}
    for i, (name, reader, kpi) in enumerate(pages):
        x = 190 + i * 170
        boxes[name] = d.box("", x, 56, 156, 160, fill=WHITE, stroke=BLUE, stroke_width=2)
        d.header_box(esc(name), x, 56, 156, 30, fill=BLUE, size=SMALL)
        d.text(f"<b>{esc(reader)}</b>", x + 6, 90, 144, 20, size=SMALL)
        d.text(esc(kpi), x + 6, 112, 144, 100, size=SMALL)
    details = [("Promotion Detail", "Drill-through: one promotion's terms, months, and lines", 190, 270,
                "Promotions"),
               ("Promotion Tooltip", "Tooltip: one promotion's discounts by month", 190, 400, "Promotions"),
               ("Cost Center Detail", "Drill-through: one cost center's accounts", 360, 270, "Budget")]
    for name, text, x, y, parent in details:
        box = d.box("", x, y, 156, 100, fill=GRAY_TINT, stroke=GRAY, dashed=True)
        d.text(f"<b>{esc(name)}</b>", x + 6, y + 6, 144, 22, size=SMALL)
        d.text(esc(text), x + 6, y + 30, 144, 66, size=SMALL)
        if name == "Promotion Tooltip":
            d.arrow(boxes[parent], box, exit=(0, 0.9), entry=(0, 0.5), points=[(174, 200), (174, 450)])
        else:
            d.arrow(boxes[parent], box, exit=(0.5, 1), entry=(0.5, 0))
    d.text("<i>Solid boxes are the visible pages, reached from the navigator; dashed boxes are hidden "
           "detail pages, reached from the page above them by drill-through or by pointing at a data point, "
           "and left by the back button or by moving the pointer away.</i>", 0, 520, 860, 40, size=SMALL,
           color=GRAY)
    return d


# -- fig-15-02 --------------------------------------------------------------------------------

def fig_15_02() -> Diagram:
    d = Diagram("Drill-Down Within a Visual and Drill-Through to Another Page")
    d.text("<b>Drill-down: the same visual, one level lower</b>", 0, 0, 420, 22, size=SMALL)
    types = sorted({r["pt"] for r in lines13() if r["grp"] == "Furniture"})
    rows = [(0, "Accessories", [money(total13("rev", fy=2026, grp="Accessories"))], "+"),
            (0, "Furniture", [money(total13("rev", fy=2026, grp="Furniture"))], "-")]
    rows += [(1, pt, [money(total13("rev", fy=2026, grp="Furniture", pt=pt))], "") for pt in types[:5]]
    rows += [(1, "…", [""], "")]
    assert abs(total13("rev", fy=2026, grp="Furniture") - 17395054.38) < 0.005
    pbi.matrix_visual(d, 0, 28, ["ItemGroup", "Revenue, 2026"], [190, 170], rows)
    d.text("<b>Drill-through: another page, filtered to one item</b>", 440, 0, 420, 22, size=SMALL)
    disc = promotion_discounts()
    names = [n for n, _, _ in disc][:3]
    pbi.bar_chart(d, 440, 28, 420, 150, None, names, [v for _, v, _ in disc][:3], "K",
                  pbi.nice_ticks(0, disc[0][1], 3), label_w=200, highlight=names[0])
    d.text("Right-click the first bar:", 440, 194, 160, 22, size=SMALL)
    menu = d.box("<b>Drillthrough</b> ▸ <b>Promotion Detail</b>", 610, 190, 240, 28, fill=WHITE, stroke=INK,
                 size=SMALL, align="left")
    page = d.box("", 560, 250, 300, 140, fill=WHITE, stroke=BLUE, stroke_width=2, rounded=False)
    pbi.back_button(d, 568, 258)
    d.text(f"<b>Promotion Detail</b>: {esc(names[0])} only", 646, 260, 210, 40, size=SMALL)
    d.text("Its terms, its discounts by month, and its invoice lines", 568, 304, 284, 60, size=SMALL)
    d.arrow(menu, page, exit=(0.5, 1), entry=(0.5, 0))
    d.text("<i>Left: expanding Furniture shows its product types in the same matrix. Right: right-clicking "
           "a promotion's bar and choosing Drillthrough opens a separate page filtered to that promotion, "
           "with a back button.</i>", 0, 396, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-15-03 --------------------------------------------------------------------------------

STEPS = ["At list price", "Price lists and overrides", "Promotions"]


def fig_15_03() -> Diagram:
    d = Diagram("The Promotions Page")
    lst, pbd, rev = gross_to_net()
    steps = [lst, pbd - lst, rev - pbd]
    assert abs(sum(steps) - 29756420.08) < 0.005 and abs(steps[2] + 362110.06) < 0.005, steps
    pbi.canvas(d, 0, 0, 860, 650)
    pbi.slicer_tiles(d, 16, 16, "Year", ["2024", "2025", "2026"], "2026", tile_w=56)
    pbi.waterfall_chart(d, 16, 84, 828, 300, "Revenue from list price to net, fiscal 2026", STEPS, steps, "M",
                        pbi.nice_ticks(0, lst, 4))
    disc = promotion_discounts()
    assert disc[0][0] == "Furniture Seasonal Promotion" and abs(disc[0][1] - 296053.58) < 0.005
    pbi.bar_chart(d, 16, 396, 828, 238, "Promotional discounts by promotion", [n for n, _, _ in disc],
                  [v for _, v, _ in disc], "K", pbi.nice_ticks(0, disc[0][1], 3), label_w=210)
    pbi.page_tabs(d, 4, 654, ["Income Statement", "Promotions"], "Promotions")
    d.text("<i>Fiscal 2026. The waterfall's last column is the total that Power BI adds, equal to revenue; "
           "increases are teal and decreases coral, each with a signed label. Two promotions of fiscal 2025 "
           "appear because their last orders were invoiced in 2026.</i>", 0, 686, 860, 40, size=SMALL,
           color=GRAY)
    return d


# -- fig-15-04 --------------------------------------------------------------------------------

def fig_15_04() -> Diagram:
    d = Diagram("The Promotion Detail Drill-Through Page")
    name = "Furniture Seasonal Promotion"
    pid, code, scope, pctv, start, end = one("SELECT PromotionID, PromotionCode, ScopeType, DiscountPct, "
                                             "EffectiveStartDate, EffectiveEndDate FROM PromotionProgram "
                                             "WHERE PromotionName = ?", name)
    months = promotion_by_month(name)
    assert [m for m, _, _ in months] == ["2026-09", "2026-10", "2026-11", "2026-12"] and end == "2026-10-31"
    lines_n = sum(n for _, _, n in months)
    disc = sum(v for _, v, _ in months)
    pbi.canvas(d, 0, 0, 860, 410)
    pbi.back_button(d, 16, 16)
    fmt = lambda s: f"{int(s[5:7])}/{int(s[8:10])}/{s[:4]}"
    pbi.table_visual(d, 100, 14, ["PromotionName", "ScopeType", "DiscountPct", "EffectiveStartDate",
                                  "EffectiveEndDate"], [196, 90, 96, 136, 130],
                     [[name, scope, f"{pctv:.0%}", fmt(start), fmt(end)]])
    pbi.frame(d, 16, 90, 300, 84, None)
    pbi.card(d, 22, 96, 140, 72, "Invoice Lines", f"{lines_n:,}")
    pbi.card(d, 170, 96, 140, 72, "Discounts", money(disc))
    chart = pbi.column_chart(d, 330, 90, 514, 300, "Discounts by YearMonth", [m for m, _, _ in months],
                             [v for _, v, _ in months], "K", pbi.nice_ticks(0, max(v for _, v, _ in months), 4),
                             labels=True)
    step = chart["width"] / 4
    xl.emphasis(d, chart["left"] + step * 2 + 4, chart["top"], step * 2 - 8, chart["height"] + 22)
    d.text("Outlined: invoiced after the promotion's end date", 330, 394, 514, 20, size=SMALL, color=CORAL,
           align="center")
    pbi.page_tabs(d, 4, 414, ["Promotions", "Promotion Detail"], "Promotion Detail")
    d.text("<i>The page reached by drilling through on the Furniture Seasonal Promotion. Power BI added the "
           "back button when the drill-through field was placed.</i>", 0, 446, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-15-05 --------------------------------------------------------------------------------

def fig_15_05() -> Diagram:
    d = Diagram("A Report-Page Tooltip")
    disc = promotion_discounts()
    pbi.canvas(d, 0, 0, 860, 330)
    pbi.bar_chart(d, 16, 16, 470, 296, "Promotional discounts by promotion", [n for n, _, _ in disc],
                  [v for _, v, _ in disc], "K", pbi.nice_ticks(0, disc[0][1], 3), label_w=210,
                  highlight=disc[0][0])
    d.vertex("", f"ellipse;html=1;fillColor={INK};strokeColor={WHITE};", 400, 58, 12, 12)
    months = promotion_by_month(disc[0][0])
    tip = d.box("", 500, 30, 340, 270, fill=WHITE, stroke=INK, stroke_width=1.5, rounded=False)
    d.text(f"<b>{esc(disc[0][0])}</b>", 508, 36, 324, 22, size=SMALL)
    pbi.column_chart(d, 508, 60, 324, 232, "Discounts by YearMonth", [m for m, _, _ in months],
                     [v for _, v, _ in months], "K", pbi.nice_ticks(0, max(v for _, v, _ in months), 3),
                     labels=True)
    d.text("<i>The pointer rests on the Furniture Seasonal Promotion's bar (the dot), and the Promotion Tooltip "
           "page appears beside it, filtered to that promotion.</i>", 0, 340, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-15-06 --------------------------------------------------------------------------------

def fig_15_06() -> Diagram:
    d = Diagram("The Visual Calculation Editor")
    monthly = budget_data()["monthly"]
    ytd, run = [], 0.0
    for v in monthly:
        run += v
        ytd.append(run)
    assert monthly[0] > 0 and monthly[6] > 0 and all(v < 0 for i, v in enumerate(monthly) if i not in (0, 6))

    def preview(dd, x, y, w, h):
        pbi.table_visual(dd, x, y, ["YearMonth", "Variance to Flexed", "YTD Variance"], [120, 160, 160],
                         [[m, money(v), money(t)] for m, v, t in zip(MONTHS_2026[:3], monthly, ytd)])
        dd.text("<i>Preview of the visual (first rows)</i>", x + 470, y + 4, w - 470, 40, size=SMALL, color=GRAY)

    out = pbi.visual_calc_editor(d, 0, 0, 860, "YTD Variance = RUNNINGSUM ( [Variance to Flexed] )", preview,
                                 120, ["YearMonth", "Variance to Flexed", "YTD Variance"], [140, 200, 200],
                                 [[m, money(v), money(t)] for m, v, t in zip(MONTHS_2026, monthly, ytd)])
    g = out["geometry"]
    for r in (0, 6):
        x0, y0, _, _ = g[(r, 0)]
        xl.emphasis(d, x0, y0, 540, pbi.ROW)
    d.text("<i>The table of Tutorial 15.2, Step 10, in edit mode. Outlined: January and July 2026, the months "
           "with three pay dates, when the year-to-date variance against the flexed budget rises.</i>", 0,
           out["bottom"] + 10, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-15-07 --------------------------------------------------------------------------------

BUDGET_COLS = ["AccountID", "BudgetAmount", "BudgetCategory", "BudgetDate", "BudgetLineID", "CostCenterID",
               "DriverType", "FiscalYear", "Month"]
GL_COLS = ["AccountID", "CostCenterID", "Credit", "Debit", "EntryType", "GLEntryID", "IsYearEndClose",
           "PostingDate", "SourceDocumentType", "VoucherNumber"]


def fig_15_07() -> Diagram:
    d = Diagram("The Budget Beside the Ledger in Model View")
    n_null = one("SELECT COUNT(*) FROM BudgetLine WHERE FiscalYear = 2026 AND BudgetCategory <> 'Balance Sheet' "
                 "AND CostCenterID IS NULL")[0]
    assert n_null == 168, n_null
    bl = pbi.model_table(d, "BudgetLine", 0, 40, BUDGET_COLS, w=160, marked=("BudgetDate",))
    acct = pbi.model_table(d, "Account", 340, 0, ["AccountID", "AccountName", "AccountNumber", "AccountSubType",
                                                  "AccountType", "NormalBalance"], w=160)
    cc = pbi.model_table(d, "CostCenter", 340, 186, ["CostCenterID", "CostCenterName"], w=160)
    dt = pbi.model_table(d, "Date", 340, 286, ["Date", "MonthName", "MonthNumber", "Quarter", "Year",
                                               "YearMonth", "YearQuarter"], w=160)
    gl = pbi.model_table(d, "GLEntry", 680, 40, GL_COLS, w=180)
    pbi.relationship(d, acct.left("AccountID"), bl.right("AccountID"),
                     [(250, acct.rows["AccountID"]), (250, bl.rows["AccountID"])])
    pbi.relationship(d, cc.left("CostCenterID"), bl.right("CostCenterID"),
                     [(270, cc.rows["CostCenterID"]), (270, bl.rows["CostCenterID"])])
    pbi.relationship(d, dt.left("Date"), bl.right("BudgetDate"),
                     [(230, dt.rows["Date"]), (230, bl.rows["BudgetDate"])])
    pbi.relationship(d, acct.right("AccountID"), gl.left("AccountID"),
                     [(590, acct.rows["AccountID"]), (590, gl.rows["AccountID"])])
    pbi.relationship(d, cc.right("CostCenterID"), gl.left("CostCenterID"),
                     [(610, cc.rows["CostCenterID"]), (610, gl.rows["CostCenterID"])])
    pbi.relationship(d, dt.right("Date"), gl.left("PostingDate"),
                     [(630, dt.rows["Date"]), (630, gl.rows["PostingDate"])])
    y = max(dt.y + dt.h, gl.y + gl.h) + 16
    d.box("", 0, y + 3, 16, 16, fill="#FEF5E7", stroke=RULE, rounded=False)
    d.text("BudgetDate, the first day of each budget month, added in Tutorial 15.2 &nbsp;&nbsp;<b>1</b>&nbsp;the "
           "table that holds the key &nbsp;&nbsp;<b>*</b>&nbsp;the table that refers to it", 22, y, 838, 22, size=SMALL)
    d.text("<i>Part of the model: the other tables are not shown. Account, CostCenter, and Date each filter both "
           "fact tables, so a visual grouped by cost center or month can place the budget beside the ledger. "
           "Budget lines without a cost center, and ledger postings without one, meet in the (Blank) row.</i>",
           0, y + 26, 860, 56, size=SMALL, color=GRAY)
    return d


# -- fig-15-08 --------------------------------------------------------------------------------

def fig_15_08() -> Diagram:
    d = Diagram("The Budget Matrix With Variance Markers")
    data = budget_data()
    rows, centers = data["rows"], data["centers"]
    pbi.canvas(d, 0, 0, 860, 420)
    pbi.slicer_tiles(d, 16, 16, "Year", ["2024", "2025", "2026"], "2026", tile_w=56)
    table_rows, kinds = [], []
    for cc in centers:
        r = rows[cc]
        vp = r["variance"] / r["budget"]
        kinds.append("up" if vp >= 0.05 else "down" if vp <= -0.05 else "neutral")
        table_rows.append([cc, money(r["budget"]), money(r["actual"]), money(r["variance"]), pct(vp)])
    tb = sum(r["budget"] for r in rows.values())
    ta = sum(r["actual"] for r in rows.values())
    widths = [210, 140, 140, 140, 130]
    t = pbi.table_visual(d, 16, 84, ["CostCenterName", "Budget", "Actual", "Variance", "Variance %"], widths,
                         table_rows, total=["Total", money(tb), money(ta), money(ta - tb), pct((ta - tb) / tb)])
    for i, kind in enumerate(kinds):
        x0, y0, _, _ = t["geometry"][(i, 4)]
        pbi.variance_icon(d, x0 + 10, y0 + 5, kind)
    assert [c for c, k in zip(centers, kinds) if k != "neutral"] == ["Administration", "Sales", "Warehouse"]
    for i, cc in enumerate(centers):
        if cc in ("Administration", "Sales", "Warehouse"):
            x0, y0, _, _ = t["geometry"][(i, 0)]
            xl.emphasis(d, x0, y0, sum(widths), pbi.ROW)
    y = t["bottom"] + 8
    pbi.variance_icon(d, 16, y + 4, "up")
    d.text("5% or more over budget", 32, y, 180, 20, size=SMALL)
    pbi.variance_icon(d, 220, y + 4, "neutral")
    d.text("within 5%", 236, y, 100, 20, size=SMALL)
    pbi.variance_icon(d, 340, y + 4, "down")
    d.text("5% or more under budget", 356, y, 200, 20, size=SMALL)
    d.text("<i>Operating expense for fiscal 2026, variance as actual less budget. Outlined: the three cost "
           "centers whose markers point up or down.</i>", 0, 430, 860, 40, size=SMALL, color=GRAY)
    return d


# -- fig-15-09 --------------------------------------------------------------------------------

def fig_15_09() -> Diagram:
    d = Diagram("The Variance Reconciliation by Cost Center")
    data = budget_data()
    rows, centers = data["rows"], data["centers"]
    table_rows = []
    for cc in centers:
        r = rows[cc]
        table_rows.append([cc, money(r["variance"]), money(r["volume"]),
                           "" if r["classification"] is None else money(r["classification"]),
                           money(r["remaining"]), pct(r["remaining"] / r["flexed"])])
    tot = {k: sum(r[k] or 0 for r in rows.values()) for k in ("variance", "volume", "classification", "remaining",
                                                              "flexed")}
    assert abs(tot["remaining"] + 174758.97) < 0.05 and abs(tot["classification"]) < 0.01, tot
    widths = [184, 128, 128, 140, 136, 100]
    pbi.canvas(d, 0, 0, 860, 340)
    t = pbi.table_visual(d, 16, 16, ["CostCenterName", "Variance", "Volume Effect", "Classification Effect",
                                     "Remaining Variance", "Remaining %"], widths, table_rows,
                         total=["Total", money(tot["variance"]), money(tot["volume"]), money(tot["classification"]),
                                money(tot["remaining"]), pct(tot["remaining"] / tot["flexed"])])
    x0, y0, w0, _ = t["geometry"][(-1, 3)]
    xl.emphasis(d, x0, y0, w0, pbi.ROW * (len(table_rows) + 2))
    d.text("<i>Fiscal 2026 operating expense. Variance = Volume Effect + Classification Effect + Remaining "
           "Variance. Outlined: the classification column, which moves depreciation between Administration and "
           "the Warehouse and totals zero. Remaining % divides by the flexed budget.</i>", 0, 350, 860, 40,
           size=SMALL, color=GRAY)
    return d


# -- fig-15-10 --------------------------------------------------------------------------------

def fig_15_10() -> Diagram:
    d = Diagram("The Trailing Ratio as a Measure and as a Visual Calculation")
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    measure = [ttm(m) for m in months]
    visual = [ttm(m, first="2025-01") for m in months]
    assert f"{measure[0]:.3f}" == "1.121" and f"{visual[0]:.3f}" == "1.375"
    assert abs(measure[-1] - visual[-1]) < 1e-9 and all(abs(a - b) > 0.001 for a, b in zip(measure[:-1], visual[:-1]))
    chart = pbi.line_chart(d, 0, 0, 860, 360, "Hours per standard hour, trailing twelve months, 2025", months,
                           [("Measure (DATESINPERIOD)", measure, BLUE),
                            ("Visual calculation on an axis starting in January 2025", visual, AMBER)],
                           "ratio", [1.0, 1.2, 1.4, 1.6, 1.8], legend=True)
    xs, y_of = chart["xs"], chart["y_of"]
    step = chart["width"] / 12
    d.box("", chart["left"] + 2, chart["top"] - 4, step * 11 - 4, chart["height"] + 8, fill="none",
          stroke=GRAY, stroke_width=1.5, dashed=True, rounded=False)
    d.text("Measure", xs[0] - 30, y_of(measure[0]) + 6, 70, 20, size=SMALL, color=BLUE, align="center")
    d.text("Visual calculation", xs[7] - 20, y_of(max(visual[7], visual[8])) - 26, 130, 20, size=SMALL, color=AMBER)
    d.text("<i>Inside the dashed frame: January to November 2025, when the visual calculation's window holds fewer than twelve "
           "months. The two agree from December 2025. The value axis starts at 1.0.</i>", 0, 370, 860, 40,
           size=SMALL, color=GRAY)
    return d


# -- fig-15-11 --------------------------------------------------------------------------------

def fig_15_11() -> Diagram:
    d = Diagram("The Plant Page")
    p = plant_months()
    months = [m for m in p["months"] if m >= "2024-12"]
    series = [ttm(m) for m in months]
    assert [f"{ttm(m):.2f}" for m in ("2024-12", "2025-12", "2026-12")] == ["1.18", "1.41", "1.51"]
    pbi.canvas(d, 0, 0, 860, 650)
    pbi.frame(d, 16, 16, 450, 80, None)
    pbi.card(d, 22, 22, 216, 68, "Hours per Standard Hour TTM", f"{series[-1]:.2f}")
    pbi.card(d, 244, 22, 216, 68, "Hours per Standard Hour 2024", f"{ttm('2024-12'):.2f}")
    pbi.line_chart(d, 478, 16, 366, 280, "Hours per Standard Hour TTM", months,
                   [("TTM", series, BLUE)], "ratio", [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6], every=6)
    wc = q("SELECT COALESCE(wc.WorkCenterName, '(Blank)'), SUM(l.RegularHours + l.OvertimeHours) "
           "FROM LaborTimeEntry l LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID "
           "LEFT JOIN WorkCenter wc ON wc.WorkCenterID = o.WorkCenterID "
           "WHERE l.LaborType = 'Direct Manufacturing' AND l.WorkDate BETWEEN '2026-01-01' AND '2026-12-31' "
           "GROUP BY 1 ORDER BY 2 DESC")
    assert wc[0][0] == "Packing Work Center"
    pbi.bar_chart(d, 16, 110, 450, 186, "Direct Hours by WorkCenterName, 2026",
                  [n.replace(" Work Center", "") for n, _ in wc], [v for _, v in wc], "K",
                  pbi.nice_ticks(0, wc[0][1], 3), label_w=118)
    # Overtime share by job title and year, a clustered column chart drawn here.
    titles = ["Assembler", "Machine Operator", "Quality Technician"]
    shares = {}
    for t, y, ot, tot in q("SELECT e.JobTitle, substr(l.WorkDate, 1, 4), SUM(l.OvertimeHours), "
                           "SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l JOIN Employee e "
                           "ON e.EmployeeID = l.EmployeeID WHERE l.LaborType <> 'NonManufacturing' GROUP BY 1, 2"):
        shares[(t, y)] = ot / tot
    ix, iy, iw, ih = pbi.frame(d, 16, 310, 828, 320, "Overtime Share by JobTitle and Year")
    years, colors = ["2024", "2025", "2026"], [GRAY, BLUE, TEAL]
    lx = ix
    for yname, color in zip(years, colors):
        d.box("", lx, iy + 4, 12, 12, fill=color, stroke=color, rounded=False)
        d.text(yname, lx + 16, iy - 2, 50, 20, size=SMALL)
        lx += 70
    top, plot_h, left = iy + 30, ih - 64, ix + 48
    ticks = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
    y_of = lambda v: top + (ticks[-1] - v) * plot_h / ticks[-1]
    for t in ticks:
        d.box("", left, y_of(t), iw - 56, 1, fill=RULE, stroke=RULE, rounded=False)
        d.text(f"{t:.0%}", ix, y_of(t) - 10, 44, 20, size=SMALL, color=GRAY, align="right", valign="middle")
    group_w = (iw - 56) / 3
    for gi, title in enumerate(titles):
        gx = left + gi * group_w + 30
        for yi, (yname, color) in enumerate(zip(years, colors)):
            v = shares[(title, yname)]
            bx = gx + yi * 70
            d.box("", bx, y_of(v), 56, y_of(0) - y_of(v), fill=color, stroke=color, rounded=False)
            d.text(pct(v), bx - 6, y_of(v) - 20, 68, 20, size=SMALL, align="center")
        d.text(esc(title), left + gi * group_w, top + plot_h + 4, group_w, 20, size=SMALL, color=GRAY,
               align="center")
    assert all(shares[(t, "2026")] > 1.5 * shares[(t, "2024")] for t in titles)
    d.text("<i>The plant page of Tutorial 15.3. The card sets the trailing figure at December 2026 beside the "
           "2024 level; the (Blank) work center holds the few direct lines without an operation.</i>", 0, 660, 860,
           40, size=SMALL, color=GRAY)
    return d


# -- fig-15-12 --------------------------------------------------------------------------------

PAGES = ["About", "Sales and Discounts", "Validation", "Review", "Margins", "Income Statement", "Promotions",
         "Budget", "Plant"]


def fig_15_12() -> Diagram:
    d = Diagram("The About Page With Its Page Navigator")
    first, last = one("SELECT MIN(InvoiceDate), MAX(InvoiceDate) FROM SalesInvoice WHERE InvoiceDate < '2027-01-01'")
    work_last = one("SELECT MAX(WorkDate) FROM LaborTimeEntry")[0]
    assert first == "2024-01-01" and work_last == "2026-12-11"
    pbi.canvas(d, 0, 0, 860, 420)
    text = ("<b>Charles River Reports: the monthly reporting package</b><br>"
            "<b>Purpose.</b> Fiscal 2026 results for three readers: the sales manager (Promotions), the "
            "department managers (Budget), and the production manager (Plant).<br>"
            "<b>Source.</b> CharlesRiver.xlsx, fiscal years 2024 to 2026; time records end on December 11, 2026, "
            "while the last pay periods are open.<br>"
            "<b>Definitions.</b> Every measure has a description: point at it in the Data pane.<br>"
            "<b>Validation.</b> The Validation page and the Tests tab in DAX query view reproduce the control "
            "totals of the earlier chapters.")
    d.box(text, 16, 16, 828, 190, fill=WHITE, stroke=RULE, size=SMALL, align="left", valign="top",
          rounded=False)
    right = pbi.page_navigator(d, 16, 222, PAGES[:5], "About")
    right2 = pbi.page_navigator(d, 16, 258, PAGES[5:], "About")
    assert right <= 860 and right2 <= 860
    d.text("<i>The page navigator, in two rows, one button for each visible page.</i>", 16, 294, 828, 20,
           size=SMALL, color=GRAY)
    pbi.page_tabs(d, 4, 424, PAGES[:6], "About")
    d.text("<i>The About page of Tutorial 15.3. The page tabs continue with Promotions, Budget, and Plant; the "
           "three detail pages are hidden, so neither the tabs nor the navigator list them.</i>", 0, 456, 860, 40,
           size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-15-01-package-plan": fig_15_01,
    "fig-15-02-drill-down-through": fig_15_02,
    "fig-15-03-promotions-page": fig_15_03,
    "fig-15-04-promotion-detail": fig_15_04,
    "fig-15-05-promotion-tooltip": fig_15_05,
    "fig-15-06-visual-calc-editor": fig_15_06,
    "fig-15-07-budget-model": fig_15_07,
    "fig-15-08-budget-matrix": fig_15_08,
    "fig-15-09-variance-reconciliation": fig_15_09,
    "fig-15-10-measure-vs-visual-calc": fig_15_10,
    "fig-15-11-plant-page": fig_15_11,
    "fig-15-12-about-page": fig_15_12,
}
