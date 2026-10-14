"""Instructor figures of Chapter 7 (guides in facts/instructor/guides/chapter-07-analysis-and-modeling/)."""

from __future__ import annotations

import statistics

import ctx
import excel as xl
import kit
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, BODY, CORAL, CORAL_TINT, FONT, GRAY, GRAY_TINT, HEAD, HIGHLIGHT, INK,
                    RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

MINUS = "−"
WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


# -- shared drawing helpers (Excel pieces copied from fig_06) ---------------------------------------------------------------

def _signed(x: float, places: int = 0) -> str:
    return (MINUS if x < 0 else "+") + f"${abs(x):,.{places}f}"


def _spct(x: float, places: int = 1) -> str:
    """A signed percentage with a true minus sign."""
    return (MINUS if x < 0 else "+") + f"{abs(x) * 100:.{places}f}%"


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow worksheet column shows it."""
    if text_width(text, size, bold) <= width - margin:
        return text
    while text and text_width(text + "…", size, bold) > width - margin:
        text = text[:-1]
    return text + "…"


def _box(d: Diagram, label: str, x: float, y: float, w: float, h: float, fill: str = WHITE, stroke: str = RULE,
         color: str = INK, align: str = "center", valign: str = "middle", spacing: float = 6, size: int = SMALL) -> str:
    """A square cell.  Diagram.box keeps 6 px of spacing on each side, so a label wraps when it comes within 12 px of the
    cell's width; a dense grid passes a smaller spacing and keeps its columns narrow."""
    if spacing == 6:
        return d.box(label, x, y, w, h, fill=fill, stroke=stroke, color=color, size=size, rounded=False, align=align,
                     valign=valign)
    style = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=1;fontColor={color};"
             f"fontSize={size};fontStyle=0;align={align};verticalAlign={valign};{FONT}spacingLeft={spacing:g};"
             f"spacingRight={spacing:g};")
    return d.vertex(label, style, x, y, w, h)


def _sheet(d: Diagram, x: float, y: float, letters: list[str], widths: list[float], rows: list[dict],
           number_color: str = GRAY, show_letters: bool = True, row_h: float = 22, spacing: float = 6) -> dict:
    """A worksheet with a letter row and rows of any height.

    widths[0] is the row-number column; letters label the others.  A row is {"n": row number, "cells": [cell, ...],
    "h": height}, its cells taken in order from the first column (a cell with span uses that many columns); a cell is a
    string or a dict: text, bold, italic, align ("left", "right", "center"), color, fill, stroke, html (a ready label),
    span (columns the text overflows across, as Excel text does when the cells beside it are empty), clip (False keeps
    a long text whole).  Returns {(row index, column): (x, y, w, h)} and "bottom"."""
    xs = [x]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    top = 22 if show_letters else 0
    if show_letters:
        for cx, w, letter in zip(xs, widths, ["", *letters]):
            _box(d, esc(letter), cx, y, w, 22, fill=GRAY_TINT, color=GRAY, spacing=spacing)
    geo: dict = {}
    ry = y + top
    for i, row in enumerate(rows):
        h = row.get("h", row_h)
        _box(d, esc(row["n"]), xs[0], ry, widths[0], h, fill=GRAY_TINT, color=row.get("number_color", number_color),
             spacing=spacing)
        cells = list(row["cells"])
        c = idx = 0                                   # cells are taken in order; a spanning cell uses several columns
        while c < len(widths) - 1:
            cell = cells[idx] if idx < len(cells) else ""
            idx += 1
            if isinstance(cell, str):
                cell = {"text": cell}
            span = cell.get("span", 1)
            cx = xs[c + 1]
            cw = sum(widths[c + 1:c + 1 + span])
            text = cell.get("text", "")
            numeric = text[:1].isdigit() or text[:1] in "-$" and text[1:2].isdigit()
            align = cell.get("align", "right" if numeric else "left")
            bold = cell.get("bold", False)
            if "html" in cell:
                label = cell["html"]
            else:
                shown = _clip(text, cw, bold=bold, margin=cell.get("margin", 2 * spacing + 2)) if cell.get("clip", True) else text
                label = esc(shown)
                if bold:
                    label = f"<b>{label}</b>"
                if cell.get("italic"):
                    label = f"<i>{label}</i>"
            _box(d, label, cx, ry, cw, h, fill=cell.get("fill", WHITE), stroke=cell.get("stroke", RULE),
                 color=cell.get("color", INK), align=align, valign=cell.get("valign", "middle"), spacing=spacing)
            geo[(i, c)] = (cx, ry, cw, h)
            c += span
        ry += h
    geo["bottom"] = ry
    return geo


def _formula_bar(d: Diagram, x: float, y: float, w: float, name: str, formula_html: str, h: float = 28) -> None:
    """The Name Box, the fx label and a formula bar."""
    d.box(esc(name), x, y, 90, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<i>fx</i>", x + 94, y, 30, 28, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(formula_html, x + 128, y, w - 128, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)


def _mark(d: Diagram, x: float, y: float, w: float, h: float, color: str = CORAL, inset: float = 0) -> str:
    """An outline like xl.emphasis (2 px outside the marked area) in a chosen color; inset pulls it inward so two
    outlines on adjacent rows do not touch."""
    left, top = max(0, x - 2 + inset), max(0, y - 2 + inset)
    return d.outline(left, top, min(860, x + w + 2 - inset) - left, y + h + 2 - inset - top, color, width=2.5, front=True)


def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def _hd(text: str, align: str = "left") -> dict:
    """A heading cell of a plain grid: light blue, bold."""
    return dict(html=f"<b>{text}</b>", fill=BLUE_TINT, align=align)


def _swatch(d: Diagram, x: float, y: float, fill: str, stroke: str | None = None, size: float = 14) -> None:
    d.box("", x, y, size, size, fill=fill, stroke=stroke or fill, rounded=False)


def nowrap(text: str) -> str:
    """A label that must not break at its sign or its comma (a signed amount)."""
    return f'<span style="white-space:nowrap">{esc(text)}</span>'


def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str = BLUE, width: float = 3) -> None:
    """One edge through the points, drawn straight between them (60 separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _label(d: Diagram, text: str, cx: float, y: float, bold: bool = True, color: str = INK, w: float | None = None) -> None:
    """A white-backed text label centered on cx, so a gridline does not strike through it."""
    shown = f"<b>{text}</b>" if bold else text
    lw = w or text_width(shown, SMALL, False) + 8
    d.vertex(shown, f"text;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;fontSize={SMALL};fontColor={color};"
                    f"{FONT}spacing=0;fillColor={WHITE};strokeColor=none;", cx - lw / 2, y, lw, 18)


def _per_hour() -> tuple[list[tuple[str, float, str]], float, float]:
    """Contribution per Assembly hour of each manufactured item sold, as Exercise 7.4's model computes it,
    with the verdict of the linear program: reduced, part (made in part) or kept; and the shadow price of an
    Assembly hour and the half-capacity constraint's level."""
    import numpy as np
    from scipy.optimize import linprog
    from notes.ch07 import commission_rate
    d = ctx.data()
    rate = commission_rate(d)[0]
    items = d.q("SELECT i.ItemID, i.ItemCode, i.ItemGroup, i.StandardCost - i.StandardFixedOverheadCost, i.RoutingID, "
                "SUM(l.Quantity), SUM(l.LineTotal) FROM Item i JOIN SalesInvoiceLine l USING (ItemID) "
                "JOIN SalesInvoice si USING (SalesInvoiceID) WHERE i.SupplyMode = 'Manufactured' "
                "AND substr(si.InvoiceDate, 1, 4) = ? GROUP BY 1 ORDER BY 1", str(d.C))
    centers = d.q("SELECT WorkCenterID, WorkCenterName FROM WorkCenter ORDER BY WorkCenterID")
    short = {w: name.replace(" Work Center", "") for w, name in centers}
    available = dict(d.q("SELECT WorkCenterID, SUM(AvailableHours) FROM WorkCenterCalendar "
                         "WHERE substr(CalendarDate, 1, 4) = ? GROUP BY 1", str(d.C)))
    hours = {(r, w): h for r, w, h in d.q("SELECT RoutingID, WorkCenterID, SUM(StandardRunHoursPerUnit) "
                                          "FROM RoutingOperation GROUP BY 1, 2")}
    demand = np.array([r[5] for r in items])
    price = np.array([r[6] / r[5] for r in items])
    unit = price - np.array([r[3] for r in items]) - rate * price
    A = np.array([[hours.get((r[4], w), 0.0) for r in items] for w, _ in centers])
    cap = np.array([available[w] / 2 for w, _ in centers])
    res = linprog(-unit, A_ub=A, b_ub=cap, bounds=[(0, q) for q in demand], method="highs")
    assert res.status == 0
    assembly = next(i for i, (w, _) in enumerate(centers) if short[w] == "Assembly")
    shadow = float(-res.ineqlin.marginals[assembly])
    out = []
    for i, r in enumerate(items):
        if A[assembly][i] <= 0:
            continue
        verdict = ("kept" if res.x[i] >= demand[i] - 1e-6 else "part" if res.x[i] > 1e-6 else "reduced")
        out.append((r[1], float(unit[i] / A[assembly][i]), verdict))
    out.sort(key=lambda t: -t[1])
    return out, shadow, float(cap[assembly])


def if_07_4_a() -> Diagram:
    """Items ranked by contribution per Assembly hour against the shadow price (Exercise 7.4)."""
    ranked, shadow, _ = _per_hour()
    d = Diagram("Why Solver Cuts the Items It Cuts")
    top = max(v for _, v, _ in ranked)
    ticks = [0, 200, 400, 600, 800, 1000] if top <= 1000 else [0, 250, 500, 750, 1000, 1250]
    plot = kit.Plot(d, 0, 0, 860, 380, "Contribution per Assembly hour, each manufactured item sold, highest to lowest",
                    y_ticks=ticks, categories=[""] * len(ranked), y_fmt=lambda v: f"${v:,.0f}",
                    y_title="Dollars per Assembly hour", bottom=34)
    colors = [CORAL if verdict != "kept" else BLUE for _, _, verdict in ranked]
    plot.bars([v for _, v, _ in ranked], colors=colors, ratio=0.8)
    n = len(ranked)
    plot.line([(-0.5, shadow), (n - 0.5, shadow)], color=AMBER, width=2, dashed=True)       # a categorical axis centers x = 0 on its first slot
    slot, ratio = plot.pw / n, 0.8
    cut = [i for i, (_, _, v) in enumerate(ranked) if v != "kept"]
    assert cut == list(range(cut[0], n)), "the items Solver reduces are the last bars, the lowest per Assembly hour"
    n_cut = len(cut)
    part = [c for c, _, v in ranked if v == "part"]
    # the shadow price: a label with a leader that comes down onto the dashed line over the coral bars, where the plot is clear
    arrow_x = plot.px + slot * (cut[0] + n_cut / 2)
    label = d.box(f"<b>Shadow price of an Assembly hour: ${shadow:,.2f}</b><br>(the dashed line)", 520, 96, 316, 40, fill=AMBER_TINT,
                  stroke=AMBER, color=INK, size=SMALL, stroke_width=1.5)
    tip = d.anchor(arrow_x, plot.y_of(shadow) - 4)
    d.edge(label, tip, end="blockThin", color=AMBER, width=2, exit=((arrow_x - 520) / 316, 1), meta="edgeStyle=none;")
    # a bracket under the axis, below the coral bars, names what Solver does with them
    bx0, bx1 = plot.px + slot * cut[0] + slot * (1 - ratio) / 2, plot.px + slot * n - slot * (1 - ratio) / 2
    by = plot.y_of(0) + 12
    for x1, y1, w1, h1 in ((bx0, by, bx1 - bx0, 2), (bx0, by - 6, 2, 8), (bx1 - 2, by - 6, 2, 8)):
        d.box("", x1, y1, w1, h1, fill=CORAL, stroke=CORAL, rounded=False)
    d.text(f"<b>Reduced by Solver:</b> {n_cut - len(part)} to nothing, {', '.join(part)} in part", bx0 - 400, by - 9, 392, 20, size=SMALL,
           color=INK, align="right")
    d.text("Blue items are made in full. Solver gives each Assembly hour to the item that earns the most per hour until the hours run out; "
           "the items that earn no more than the shadow price are the ones it reduces.", 0, 392, 860, 36, size=SMALL, color=INK)
    kit.legend(d, 0, 436, [("Made in full", BLUE, "box"), ("Reduced or made in part", CORAL, "box"),
                           ("Shadow price", AMBER, "dashed")])
    return d


# -- IF-07-1-A: the backtest grid of Exercise 7.1 ---------------------------------------------------------------------------------

def if_07_1_a() -> Diagram:
    """Ex 7.1, rows 42 to 49: the mean absolute percentage error of five methods for each item group, the lowest of each
    group outlined, and the two rows that name the lowest method."""
    data = ctx.data()
    g1 = ctx.values("ch07.g1")
    first = f"{data.F}-Q1"
    sheet_name = {"Trend": "Trend", "Mean": "Mean", "Same quarter last year": "Same quarter last year",
                  "Trend without the first quarter": f"Trend without {first}",
                  "Mean without the first quarter": f"Mean without {first}"}
    methods = list(g1["methods"])
    assert methods[:3] == ["Trend", "Mean", "Same quarter last year"] and len(methods) == 5, methods
    groups = g1["groups"]
    assert len(groups) == 5, "five item groups, columns C to G"
    letters = list("BCDEFG")                                                    # column A, the quarter index, is hidden
    tight = 3
    widths = [30, 146] + [134] * 5
    errors = [[x["errors"][m] for x in groups] for m in methods]                # rows 43 to 47 by column
    pct = lambda v: f"{xl.xround(v * 100, 2):.2f}%"
    lowest5 = [min(range(5), key=lambda r: errors[r][c]) for c in range(5)]
    lowest3 = [min(range(3), key=lambda r: errors[r][c]) for c in range(5)]
    assert [methods[r] for r in lowest3] == [x["best3"] for x in groups] and [methods[r] for r in lowest5] == [x["best5"] for x in groups]
    rows = [dict(n="42", cells=[_hd("Method")] + [_hd(x["group"], "left") for x in groups])]
    for r, m in enumerate(methods):
        rows.append(dict(n=str(43 + r), cells=[sheet_name[m]] + [dict(text=pct(errors[r][c]), align="right") for c in range(5)]))
    rows.append(dict(n="48", cells=["Lowest of the first three"] + [dict(text=sheet_name[methods[r]], align="left") for r in lowest3]))
    rows.append(dict(n="49", cells=["Lowest of all five"] + [dict(text=sheet_name[methods[r]], align="left") for r in lowest5]))
    d = Diagram("The Backtest Grid of Exercise 7.1")
    _formula_bar(d, 0, 0, 860, "C48", esc("=INDEX($B$43:$B$45,MATCH(MIN(C43:C45),C43:C45,0))"))
    geo = _sheet(d, 0, 40, letters, widths, rows, spacing=tight)
    xl.select(d, *geo[(6, 1)])
    for c, r in enumerate(lowest5):
        x0, y0, w0, h0 = geo[(1 + r, 1 + c)]
        _mark(d, x0, y0, w0, h0, CORAL, inset=1.5)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 7.1", "Ex 7.2"], "Ex 7.1")
    names = ", ".join(f"{x['group']} {pct(errors[lowest5[c]][c])}" for c, x in enumerate(groups))
    _note(d, f"Selected: C48, whose formula shows in the bar. Outlined: the lowest error of the five methods in each column, {names}. "
             f"Column A, the quarter index, is hidden, and the row above the heading, which names the error, is not shown. "
             f"Row 48 chooses among the first three methods only, so for Furniture it differs from row 49.", bottom + 34)
    return d


# -- IF-07-3-A: the two-variable data table of Exercise 7.3 --------------------------------------------------------------------------

def if_07_3_a() -> Diagram:
    """Ex 7.3, D2:O12: break-even revenue for each contribution margin ratio (across) and fixed costs (down), the cell nearest
    the model's own assumptions outlined."""
    g3 = ctx.values("ch07.g3")
    e3 = ctx.values("ch07.ex3")
    ratio, fixed2, own = g3["ratio"], g3["fixed2"], e3["breakeven2"]
    ratios = [round(0.40 + 0.01 * i, 2) for i in range(11)]                    # E3:O3, as Step 6a types them
    fixeds = [6_000_000 + 500_000 * i for i in range(9)]                       # D4:D12
    assert abs(own - fixed2 / ratio) < 0.01, "the corner cell D3 is B24, the break-even revenue with the added items"
    ci = min(range(len(ratios)), key=lambda i: abs(ratios[i] - ratio))
    ri = min(range(len(fixeds)), key=lambda i: abs(fixeds[i] - fixed2))
    assert ratios[0] <= ratio <= ratios[-1] and fixeds[0] <= fixed2 <= fixeds[-1], "the model sits inside the table"
    letters = [chr(ord("D") + i) for i in range(12)]                           # D to O
    tight = 2
    widths = [26] + [69] * 12
    whole = lambda v: f"{xl.xround(v, 0):,.0f}"
    rows = [dict(n="2", cells=[dict(text="Break-even revenue: fixed costs (down) by contribution margin ratio (across)", bold=True,
                                    span=12, clip=False)]),
            dict(n="3", cells=[dict(text=whole(own), align="right")] + [dict(text=f"{round(r * 100)}%", align="right") for r in ratios])]
    for f in fixeds:
        rows.append(dict(n=str(len(rows) + 2), cells=[dict(text=whole(f), align="right")] + [dict(text=whole(f / r), align="right") for r in ratios]))
    d = Diagram("The Data Table of Exercise 7.3")
    _formula_bar(d, 0, 0, 860, "D3", esc("=B24"))
    geo = _sheet(d, 0, 40, letters, widths, rows, spacing=tight)
    xl.select(d, *geo[(1, 0)])
    x0, y0, w0, h0 = geo[(2 + ri, 1 + ci)]
    _mark(d, x0, y0, w0, h0, CORAL)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 7.2", "Ex 7.3", "Ex 7.4"], "Ex 7.3")
    d.box("<b>Outlined: the cell nearest the model's own ratio and fixed costs</b>", 460, bottom, 400, 24, fill=CORAL, stroke=CORAL,
          color=WHITE, size=SMALL, rounded=False)
    _note(d, f"Selected: D3, which holds =B24, the break-even revenue with the added items ({whole(own)}). Outlined: the cell for "
             f"{round(ratios[ci] * 100)}% and {whole(fixeds[ri])}, the nearest to the model's own ratio ({ratio * 100:.1f}%) and fixed costs "
             f"({whole(fixed2)}); it reads {whole(fixeds[ri] / ratios[ci])}. The table is built with B9 as the row input cell and B23 as the "
             f"column input cell, and every grid cell is the one array formula {{=TABLE(B9,B23)}}. Columns A to C hold the model and are not shown.",
          bottom + 34)
    return d


# -- IF-07-5-A: the commission differences of Exercise 7.5 --------------------------------------------------------------------------------

def _commission_differences() -> list[dict]:
    """The Difference % column of Ex 7.5 for the report year: recorded commission less the expectation from the earlier
    years' regression on revenue, as a share of the expectation (Steps 4 and 5)."""
    from notes.ch07 import MONTHS, fit, revenue_by_month
    d = ctx.data()
    revenue = revenue_by_month(d)
    commission = dict(d.q("SELECT substr(PostingDate, 1, 7), SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? "
                          "AND SourceDocumentType <> 'JournalEntry' GROUP BY 1", d.account("6290")))
    months = sorted(revenue)
    fitted = [m for m in months if m[:4] in (str(d.F), str(d.P))]
    line = fit([revenue[m] for m in fitted], [commission[m] for m in fitted])
    out = []
    for m in months:
        if m[:4] == str(d.C):
            expected = line["a"] + line["b"] * revenue[m]
            out.append(dict(month=MONTHS[int(m[5:]) - 1], diff=commission[m] - expected, pct=(commission[m] - expected) / expected))
    assert len(out) == 12
    return out


def if_07_5_a() -> Diagram:
    """Twelve columns of difference % against the plus and minus 3 percent threshold of Step 5, with the offsetting pair bracketed."""
    d_ = ctx.data()
    e5 = ctx.values("ch07.ex5")
    months = _commission_differences()
    threshold = 0.03                                                          # Step 5: =IF(ABS(G28)>0.03,"Investigate","")
    flagged = [abs(m["pct"]) > threshold for m in months]
    assert [m["month"] for m, f in zip(months, flagged) if f] == [r["month"] for r in e5["flagged"]], "the months the guide flags"
    assert all(abs(m["pct"] - r["pct"]) < 1e-9 for m, r in zip((m for m, f in zip(months, flagged) if f), e5["flagged"]))
    assert all(-0.06 < m["pct"] < 0.06 for m in months), "the axis runs from minus 6 to plus 9 percent, with headroom for the bracket"
    pair = [next(m for m in months if m["month"] == name) for name in e5["pair"]]
    first = next(i for i, m in enumerate(months) if m["month"] == pair[0]["month"])
    assert months[first + 1]["month"] == pair[1]["month"] and pair[0]["diff"] * pair[1]["diff"] < 0, "consecutive months, opposite signs"
    d = Diagram("The Commission Differences of Exercise 7.5")
    d.text(f"<b>Recorded commission expense less the expectation, as a percent of the expectation, fiscal {d_.C}</b>", 0, 0, 860, 20,
           size=SMALL)
    ticks = [-0.06, -0.03, 0.0, 0.03, 0.06, 0.09]
    plot = kit.Plot(d, 0, 26, 860, 380, None, y_ticks=ticks, categories=[m["month"][:3] for m in months],
                    y_fmt=lambda v: "0%" if v == 0 else _spct(v, 0), bottom=26)
    slot = plot.pw / 12
    bw = slot * 0.6
    d.box("", plot.px, plot.y_of(0) - 1, plot.pw, 2, fill=INK, stroke=INK, rounded=False)            # the zero line, where the bars start
    for i, (m, f) in enumerate(zip(months, flagged)):
        top, base = (plot.y_of(m["pct"]), plot.y_of(0)) if m["pct"] >= 0 else (plot.y_of(0), plot.y_of(m["pct"]))
        d.box("", plot.px + slot * i + (slot - bw) / 2, top, bw, base - top, fill=CORAL if f else GRAY, stroke=CORAL if f else GRAY,
              rounded=False)
    for level in (threshold, -threshold):                                      # a categorical axis centers x = 0 on its first slot
        plot.line([(-0.5, level), (11.5, level)], color=INK, width=2, dashed=True)
    for i, (m, f) in enumerate(zip(months, flagged)):
        cx = plot.px + slot * (i + 0.5)
        y_label = plot.y_of(m["pct"]) - 22 if m["pct"] >= 0 else plot.y_of(m["pct"]) + 4
        _label(d, _spct(m["pct"]), cx, y_label, bold=f)
    # the bracket over the pair, in the headroom above the tallest bar
    bx0 = plot.px + slot * first + (slot - bw) / 2
    bx1 = plot.px + slot * (first + 2) - (slot - bw) / 2
    by = plot.y_of(0.072)
    for (x1, y1, x2, y2) in ((bx0, by, bx1, by), (bx0, by, bx0, by + 10), (bx1, by, bx1, by + 10)):
        d.box("", min(x1, x2), min(y1, y2), max(abs(x2 - x1), 2), max(abs(y2 - y1), 2), fill=INK, stroke=INK, rounded=False)
    d.box(f"<b>An offsetting pair:</b> {pair[0]['month']} {_signed(pair[0]['diff'])} and {pair[1]['month']} {_signed(pair[1]['diff'])}",
          min(bx0 - 10, 860 - 390), plot.y_of(0.086), 390, 20, fill=WHITE, stroke=WHITE, size=SMALL, align="left", rounded=False)
    ly = 26 + 380 + 12
    cx = 0
    for fill, label in ((CORAL, "Beyond the threshold: investigate"), (GRAY, "Within the threshold")):
        _swatch(d, cx, ly + 3, fill)
        w = text_width(label, SMALL, False) + 8
        d.text(label, cx + 20, ly, w, 20, size=SMALL, valign="middle")
        cx += 20 + w + 22
    d.line_sample(cx, ly + 10, 28, color=INK, dashed=True, width=2)
    d.text("Plus and minus 3 percent of the expectation", cx + 34, ly, 320, 20, size=SMALL, valign="middle")
    within = max(abs(m["pct"]) for m, f in zip(months, flagged) if not f)
    n_flag = sum(flagged)
    _note(d, f"{WORDS[n_flag].capitalize()} of the twelve months are beyond the threshold; every other month is within {within * 100:.1f}%. "
             f"The two consecutive flagged months differ in sign and nearly cancel, which a shift of commission from one month to the "
             f"other would do; the records show the customer mix instead (Step 6). The axis includes zero, and each column starts there.",
          ly + 30)
    return d


# -- IF-07-6-A: forecast against orders by group and year (Exercise 7.6) ------------------------------------------------------------------

def if_07_6_a() -> Diagram:
    """Forecast units over ordered units for the four product groups and, apart, for Services (Requirement 3)."""
    d_ = ctx.data()
    g6 = ctx.values("ch07.g6")
    e6 = ctx.values("ch07.ex6")
    years = d_.years
    table = g6["table"]
    products, services = table[:4], table[4]
    assert services["group"] == "Services" and len(products) == 4
    assert all(r["ratio"][0] < r["ratio"][1] < r["ratio"][2] for r in products), "the bars rise in every group"
    assert max(services["ratio"]) < 1 < min(min(r["ratio"]) for r in products), "Services below the line, the products above it"
    top = 4
    assert max(max(r["ratio"]) for r in products) < top - 0.4
    ticks = [0, 1, 2, 3, 4]
    fills = [(BLUE_TINT, BLUE, 2), (GRAY, GRAY, 1), (BLUE, BLUE, 1)]
    d = Diagram("The Forecast Against Orders")
    d.text("<b>Forecast units divided by units ordered, by item group and year</b>", 0, 0, 860, 20, size=SMALL)
    y0, h = 26, 400
    main_w, gap = 618, 14
    p1 = kit.Plot(d, 0, y0, main_w, h, None, y_ticks=ticks, categories=[r["group"] for r in products], y_fmt=lambda v: f"{v:g}",
                  y_title="Ratio: forecast units ÷ ordered units", bottom=28)
    p2 = kit.Plot(d, main_w + gap, y0, 860 - main_w - gap, h, None, y_ticks=ticks, categories=["Services (hours)"],
                  y_fmt=lambda v: f"{v:g}", y_title="Same scale, hours not units", bottom=28)

    def cluster(plot: kit.Plot, rows: list[dict]) -> None:
        slot = plot.pw / len(rows)
        bw = min(38, (slot * 0.82 - 8) / 3)
        for i, r in enumerate(rows):
            x0 = plot.px + slot * (i + 0.5) - (3 * bw + 8) / 2
            for k, v in enumerate(r["ratio"]):
                fill, stroke, width = fills[k]
                bx = x0 + k * (bw + 4)
                d.box("", bx, plot.y_of(v), bw, plot.y_of(0) - plot.y_of(v), fill=fill, stroke=stroke, stroke_width=width, rounded=False)
                _label(d, f"{v:.2f}", bx + bw / 2, plot.y_of(v) - 22, bold=False)
    cluster(p1, products)
    cluster(p2, [services])
    for plot in (p1, p2):
        d.box("", plot.px, plot.y_of(1) - 1.25, plot.pw, 2.5, fill=HIGHLIGHT, stroke=HIGHLIGHT, rounded=False)
    d.box("<b>1 = the forecast<br>equals the orders</b>", p2.px + 6, p2.y_of(1) - 46, 136, 38, fill=WHITE, stroke=HIGHLIGHT,
          stroke_width=1.5, size=SMALL, rounded=False)
    ly = y0 + h + 12
    cx = 0
    for (fill, stroke, width), year in zip(fills, years):
        _swatch(d, cx, ly + 3, fill, stroke)
        d.text(str(year), cx + 20, ly, 44, 20, size=SMALL, valign="middle")
        cx += 78
    d.box("", cx, ly + 8, 28, 3, fill=HIGHLIGHT, stroke=HIGHLIGHT, rounded=False)
    d.text("A forecast equal to the orders", cx + 34, ly, 220, 20, size=SMALL, valign="middle")
    ratios = [y["ratio"] for y in e6["years"]]
    _note(d, f"In every product group the ratio is above 2 in every year and rises from {years[0]} to {years[-1]}; the four groups together "
             f"run {ratios[0]:.2f}, {ratios[1]:.2f} and {ratios[2]:.2f}. Services runs the other way, at {min(services['ratio']):.2f} to "
             f"{max(services['ratio']):.2f}, and is forecast and ordered in hours of design work, so it is kept apart and never added to "
             f"product units. Every bar starts at zero.", ly + 30)
    return d


# -- IF-07-0-B: the break-even lift against the discount (Tutorial 7.3) -------------------------------------------------------------------

def if_07_0_b() -> Diagram:
    """The volume lift at which the promotion breaks even, for discounts from 0 to 15 percent, as the Model worksheet computes it."""
    c = ctx.values("ch07.chapter")["t3"]
    price, cost, rate, ran = c["price"], c["cost"], c["rate"], c["discount"]

    def lift(disc: float) -> float:
        """Contribution per unit before the lift against after the discount: the lift that makes both totals equal."""
        return disc * price * (1 - rate) / (price * (1 - disc) * (1 - rate) - cost)
    assert abs(lift(ran) - c["lift"]) < 1e-9 and abs(lift(0.05) - c["lift5"]) < 1e-9 and abs(lift(0.15) - c["lift15"]) < 1e-9
    steps = [i * 0.0025 for i in range(0, 61)]
    top = 0.7
    assert lift(0.15) < top - 0.1
    d = Diagram("The Break-Even Lift of the Promotion")
    d.text("<b>The volume lift at which the promotion breaks even, by discount rate</b>", 0, 0, 860, 20, size=SMALL)
    pct0 = lambda v: f"{v * 100:.0f}%"
    plot = kit.Plot(d, 0, 26, 840, 400, None, y_ticks=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], x_ticks=[0, 0.05, 0.10, 0.15],
                    x_fmt=pct0, y_fmt=pct0, x_title="Discount rate", y_title="Volume lift at which the promotion breaks even", left=60,
                    bottom=48)
    _polyline(d, [(plot.x_of(s), plot.y_of(lift(s))) for s in steps], BLUE, 3)
    for s in (0.05, ran, 0.15):                                              # drop lines to both axes
        for a, b in (((s, 0), (s, lift(s))), ((0, lift(s)), (s, lift(s)))):
            plot.line([a, b], color=CORAL if s == ran else GRAY, width=1.5, dashed=True)
    for s in (0.05, 0.15):
        plot.points([(s, lift(s))], color=BLUE, size=12)
    plot.points([(ran, lift(ran))], color=CORAL, size=16)
    for s, text, dx in ((0.05, f"<b>5% discount</b><br>needs a lift of {lift(0.05) * 100:.1f}%", -168),
                        (ran, f"<b>{ran * 100:.0f}% discount: the promotion as it ran</b><br>needs a lift of {lift(ran) * 100:.1f}%", -250),
                        (0.15, f"<b>15% discount</b><br>needs a lift of {lift(0.15) * 100:.1f}%", -168)):
        w = 242 if s == ran else 158
        d.box(text, plot.x_of(s) + dx, plot.y_of(lift(s)) - 54, w, 40, fill=CORAL if s == ran else WHITE,
              stroke=CORAL if s == ran else GRAY, color=WHITE if s == ran else INK, size=SMALL, rounded=False)
    d.text("<i>Above the line, the promotion pays for itself.</i>", plot.px + 22, plot.y_of(0.66), 300, 20, size=SMALL, color=GRAY)
    d.text("<i>Below the line, it does not.</i>", plot.x_of(0.108), plot.y_of(0.12), 200, 20, size=SMALL, color=GRAY)
    _note(d, f"From the Model worksheet's inputs: {c['units']:,.2f} units on the promotion's lines, ${price:,.2f} price before discount, "
             f"${cost:,.2f} variable cost and a commission rate of {rate * 100:.2f}%. The break-even lift is the lift at which the contribution "
             f"with the discount equals the contribution without it; fixed costs do not enter. At the {ran * 100:.0f}% discount the "
             f"Furniture units ordered in the promotion's months were {_spct(c['promo_vs_other'])} against the other months.", 26 + 400 + 10)
    return d


# -- IF-07-0-C: static budget, flexible budget and actual margin in one walk ---------------------------------------------------------

def if_07_0_c() -> Diagram:
    """The Total column of the BudgetReport worksheet as a bridge from the static budget margin to the actual margin."""
    t = ctx.values("ch07.chapter")["t2"]["fb"]["total"]
    static, svv, flex, gap, disc, actual = t["static_margin"], t["svv"], t["flex_margin"], t["gap"], t["discounts"], t["margin"]
    assert abs(static + svv - flex) < 0.01 and abs(flex + gap - disc - actual) < 0.01, "the walk adds up"
    assert svv < 0 and gap < 0 and disc > 0
    steps = [("Static budget<br>margin", 0.0, static, "total", static),
             ("Sales-volume<br>variance", static, flex, "variance", svv),
             ("Flexible budget<br>margin", 0.0, flex, "total", flex),
             ("Price gap before<br>discounts", flex, flex + gap, "variance", gap),
             ("Promotional<br>discounts", flex + gap, actual, "variance", -disc),
             ("Actual<br>margin", 0.0, actual, "total", actual)]
    top = 50e6
    assert static < top
    d = Diagram("From the Static Budget to the Actual Margin")
    d.text("<b>Margin of the four product lines, fiscal %d (Total column of the BudgetReport worksheet)</b>" % ctx.data().C, 0, 0, 860, 20,
           size=SMALL)
    plot = kit.Plot(d, 0, 26, 860, 400, None, y_ticks=[0, 10e6, 20e6, 30e6, 40e6, 50e6], categories=[s[0] for s in steps],
                    y_fmt=lambda v: f"${v / 1e6:.0f}M", bottom=44)
    slot = plot.pw / len(steps)
    bw = slot * 0.62
    d.box("", plot.px, plot.y_of(0) - 1, plot.pw, 2, fill=INK, stroke=INK, rounded=False)
    levels = []
    for i, (name, a, b, kind, amount) in enumerate(steps):
        x0 = plot.px + slot * i + (slot - bw) / 2
        hi, lo = max(a, b), min(a, b)
        fill = BLUE if kind == "total" else CORAL
        d.box("", x0, plot.y_of(hi), bw, max(plot.y_of(lo) - plot.y_of(hi), 1.5), fill=fill, stroke=fill, rounded=False)
        levels.append((x0, x0 + bw, b))
    for (x0, x1, level), (nx0, _, _) in zip(levels, levels[1:]):
        d.box("", x1, plot.y_of(level) - 0.75, nx0 - x1, 1.5, fill=GRAY, stroke=GRAY, rounded=False)
    for i, (name, a, b, kind, amount) in enumerate(steps):
        x0, x1, _ = levels[i]
        cx = (x0 + x1) / 2
        text = f"${amount:,.0f}" if kind == "total" else _signed(amount)
        if kind == "total":                                                         # inside the bar, white on blue
            d.text(f"<b>{text}</b>", x0, plot.y_of(max(a, b)) + 6, bw, 20, size=SMALL, color=WHITE, align="center")
        elif abs(a - b) > 8e6:                                                      # the tall variance: inside, white on coral
            d.text(f"<b>{text}</b>", x0, (plot.y_of(a) + plot.y_of(b)) / 2 - 10, bw, 20, size=SMALL, color=WHITE, align="center")
        else:                                                                       # a sliver: the label sits above it
            _label(d, text, cx, plot.y_of(max(a, b)) - 24)
    small = abs(gap) + disc
    _swatch(d, 0, 26 + 400 + 12 + 3, BLUE)
    d.text("A margin (a total)", 20, 26 + 400 + 12, 150, 20, size=SMALL, valign="middle")
    _swatch(d, 190, 26 + 400 + 12 + 3, CORAL)
    d.text("A variance, signed: the minus sign says it lowers the margin", 210, 26 + 400 + 12, 460, 20, size=SMALL, valign="middle")
    _note(d, f"Drawn to scale from zero. The sales-volume variance is {abs(svv) / small:.0f} times the price gap and the discounts together, "
             f"which add up to the flexible-budget variance ({nowrap(_signed(gap - disc))}), so those two bars are slivers. The budget plans "
             f"{t['unit_ratio']:.1f} times the units sold.", 26 + 400 + 38)
    return d


# -- IF-07-0-A: which what-if tool answers which question --------------------------------------------------------------------------------

def if_07_0_a() -> Diagram:
    """The chapter's table of what-if tools as a decision tree, with the example of Tutorial 7.3 or Exercise 7.4 under each tool."""
    branches = [
        ("What are the results under each of several named sets of inputs?", "Scenario Manager",
         "Data > What-If Analysis > Scenario Manager",
         "Tutorial 7.3: the promotion's difference when it repeats as it ran, repeats with a lift, or runs with a deeper discount."),
        ("How does a result change across a range of values of one or two inputs?", "Data table",
         "Data > What-If Analysis > Data Table",
         "Tutorial 7.3: the promotion's difference at each discount and each lift. Exercise 7.3: break-even revenue at each ratio and fixed cost."),
        ("What value of one input produces a target result?", "Goal Seek",
         "Data > What-If Analysis > Goal Seek",
         "Tutorial 7.3: the lift at which the promotion breaks even. Exercise 7.3: the revenue for a target operating income."),
        ("What values of several inputs give the best result within a set of constraints?", "Solver",
         "Data > Solver, after loading the Solver add-in",
         "Exercise 7.4: how many of each item to make when Assembly hours run short."),
    ]
    d = Diagram("Which What-If Tool Answers Which Question")
    n, gap = len(branches), 20
    bw = (860 - gap * (n - 1)) / n
    root_w = 330
    root = d.box("<b>What do you want to know?</b>", (860 - root_w) / 2, 0, root_w, 44, fill=BLUE, stroke=BLUE, color=WHITE, size=HEAD,
                 stroke_width=1.5)
    qh = max(kit.height_for(b[0], bw, BODY) for b in branches)
    th = max(kit.height_for(f"<b>{b[1]}</b><br>{b[2]}", bw, SMALL, pad=12) for b in branches) + 6
    eh = max(kit.height_for(b[3], bw, SMALL, pad=14) for b in branches)
    qy, ty, ey = 44 + 44, 44 + 44 + qh + 44, 44 + 44 + qh + 44 + th + 44
    for i, (question, tool, path, example) in enumerate(branches):
        x = i * (bw + gap)
        q = d.box(question, x, qy, bw, qh, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=BODY)
        t = d.box(f"<b>{tool}</b><br>{esc(path)}", x, ty, bw, th, fill=TEAL, stroke=TEAL, color=WHITE, size=SMALL, stroke_width=1.5)
        e = d.box(esc(example), x, ey, bw, eh, fill=TEAL_TINT, stroke=TEAL, size=SMALL, align="left", stroke_width=1.5)
        d.arrow(root, q, exit=(0.5, 1), entry=(0.5, 0), width=2)
        d.arrow(q, t, exit=(0.5, 1), entry=(0.5, 0), width=2)
        d.arrow(t, e, exit=(0.5, 1), entry=(0.5, 0), width=2)
    _note(d, "The questions and the menu paths are those of the chapter's table of what-if tools. Each example is the decision it answers in "
             "Tutorial 7.3 or in an exercise, named without its numbers.", ey + eh + 12)
    return d


FIGURES = {"IF-07-0-A": if_07_0_a, "IF-07-0-B": if_07_0_b, "IF-07-0-C": if_07_0_c, "IF-07-1-A": if_07_1_a, "IF-07-3-A": if_07_3_a,
           "IF-07-4-A": if_07_4_a, "IF-07-5-A": if_07_5_a, "IF-07-6-A": if_07_6_a}
