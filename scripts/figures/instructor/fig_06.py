"""Instructor figures of Chapter 6 (guides in facts/instructor/guides/chapter-06-descriptive-analytics/)."""

from __future__ import annotations

import math

import ctx
import excel as xl
import kit
from check_figures import text_width
from drawio import (AMBER_TINT, BLUE, BLUE_TINT, CORAL, FONT, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL, TEAL_TINT, WHITE,
                    Diagram, esc)

MINUS = "−"
WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


# -- shared drawing helpers (Excel pieces copied from fig_04 and fig_05) ----------------------------------------------------

def _money(x: float) -> str:
    return f"{x:,.2f}"


def _general(x: float) -> str:
    """A number as Excel's General format shows it: 0.0 reads 0, and a sum such as 29756420.079999983 reads 29756420.08."""
    return f"{x:.15g}"


def _signed(x: float, places: int = 2) -> str:
    return (MINUS if x < 0 else "+") + f"${abs(x):,.{places}f}"


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


def _gap(d: Diagram, x: float, y: float, w: float, text: str, h: float = 24) -> float:
    """A band that stands for the rows of a long worksheet that the figure leaves out."""
    d.box(f"<i>{esc(text)}</i>", x, y, w, h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, rounded=False, dashed=True)
    return y + h


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


def _swatch(d: Diagram, x: float, y: float, fill: str, stroke: str = GRAY, size: float = 14) -> None:
    d.box("", x, y, size, size, fill=fill, stroke=stroke, rounded=False)


def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def nowrap(text: str) -> str:
    """A label that must not break at its hyphens (a document number)."""
    return f'<span style="white-space:nowrap">{esc(text)}</span>'


def _word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def _and(items: list[str]) -> str:
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# -- IF-06-0-A: the revenue ladder -------------------------------------------------------------------------------------------

def if_06_0_a() -> Diagram:
    """From the invoice lines of the Profile worksheet to the net revenue of the income statement (Exercises 6.1 and 6.2)."""
    g1, g2, ex1 = ctx.values("ch06.g1"), ctx.values("ch06.g2"), ctx.values("ch06.ex1")
    y = g2["y"]
    lines_total, cutoff, freight, opr = g2["grand"], g2["cutoff"], g2["freight"], g2["opr"]
    contra, net = ex1["contra"], ex1["net_rev"]
    product = sum(r["balance"] for r in ex1["recon"])
    assert abs(product - (lines_total + cutoff)) < 0.01, "the product revenue accounts are the invoice lines plus the cutoff invoices"
    assert abs(product + freight - opr) < 0.01 and abs(opr + contra - net) < 0.01, "the ladder adds up to net revenue"
    assert abs(cutoff - sum(r["diff"] for r in ex1["recon"])) < 0.01 and abs(freight - ex1["freight"]) < 0.01
    invoices = sorted(ex1["invoices"], key=lambda i: i["number"])
    numbers = [i["number"] for i in invoices]
    early = ex1["early"]
    accounts = _and([r["account"] for r in ex1["recon"]])
    d = Diagram("From the Invoice Lines to Net Revenue")
    bw, bh, gap = 340, 70, 88
    rungs = [
        ("Invoice lines of fiscal %d" % y, lines_total, "InvoiceLines: the control total of the Profile worksheet", "gray"),
        ("Product revenue accounts", product, f"TrialBalance: accounts {accounts}", "blue"),
        ("Operating revenue", opr, "TrialBalance: every Operating Revenue account", "blue"),
        ("Net revenue", net, "IncomeStatement: operating revenue less returns and allowances", "teal"),
    ]
    ids = []
    for i, (title, amount, source, tone) in enumerate(rungs):
        fill, stroke = kit.tint(tone)
        top = i * (bh + gap)
        ids.append(d.box(f"<b>{esc(title)}</b><br><b>${amount:,.2f}</b><br>{esc(source)}", 0, top, bw, bh, fill=fill, stroke=stroke,
                         stroke_width=1.5, size=SMALL))
    steps = [
        (cutoff, f"The {_word(len(invoices))} cutoff invoices, {nowrap(numbers[0])} to {nowrap(numbers[-1])}, dated {y - 1} and posted "
                 f"{esc(ex1['posted'])}. The ledger has them in {y}; InvoiceLines does not. Only {nowrap(early['number'])} "
                 f"(${early['amount']:,.2f}) was delivered in {y - 1}."),
        (freight, f"Freight revenue, account {g1['acct']['freight']}, net of freight credits. It is billed on the invoice header, so no invoice line carries it."),
        (contra, f"Sales returns and allowances, account {g1['acct']['returns']}: the credit memos, in a contra revenue account."),
    ]
    for i, (amount, text) in enumerate(steps):
        top = i * (bh + gap) + bh
        d.arrow(ids[i], ids[i + 1], exit=(0.5, 1), entry=(0.5, 0), width=2)
        mid = top + gap / 2
        text_h = max(kit.height_for(f"<b>{_signed(amount)}</b> {text}", 470, SMALL, pad=14), 44)
        d.line_sample(bw / 2, mid, 372 - bw / 2, color=GRAY, width=1.5)
        d.box(f"<b>{_signed(amount)}</b>&nbsp;&nbsp;{text}", 372, mid - text_h / 2, 488, text_h, fill=WHITE, stroke=GRAY, size=SMALL,
              align="left", stroke_width=1.5)
    bottom = 3 * (bh + gap) + bh
    _note(d, "Gray: the invoice lines. Blue: balances of the trial balance of Exercise 6.1. Teal: the line of the income statement. "
             "Each arrow carries one reconciling item, signed as it changes the amount above it. The ladder is as recorded, "
             "before correction of the cutoff error.", bottom + 14)
    return d


# -- IF-06-0-B: why a calculated field cannot multiply two fields -------------------------------------------------------------

def if_06_0_b() -> Diagram:
    """A calculated field multiplies the two sums; a custom column multiplies each line and the PivotTable adds the products."""
    lines = [("A", 2, 10), ("B", 3, 20), ("C", 5, 30)]                       # invented: line, quantity, unit price
    qty, price = sum(q for _, q, _ in lines), sum(p for _, _, p in lines)
    products = [q * p for _, q, p in lines]
    wrong, right = qty * price, sum(products)
    assert wrong != right
    d = Diagram("Why a Calculated Field Cannot Multiply Two Fields")
    pw = 418

    def panel(x: float, head: str, fill: str, columns: list[str], widths: list[float], body: list[list[str]], total: list[str],
              tint_col: int | None, stage: str, result: str, result_fill: str) -> None:
        d.box(head, x, 0, pw, 48, fill=fill, stroke=fill, color=WHITE, size=SMALL, rounded=False)
        xs = [x]
        for w in widths[:-1]:
            xs.append(xs[-1] + w)
        top = 62
        for c, (cx, w, name) in enumerate(zip(xs, widths, columns)):
            d.box(f"<b>{esc(name)}</b>", cx, top, w, 26, fill=BLUE_TINT, stroke=RULE, size=SMALL, rounded=False, align="left")
        for r, row in enumerate(body):
            for c, (cx, w, value) in enumerate(zip(xs, widths, row)):
                d.box(esc(value), cx, top + 26 * (r + 1), w, 26, fill=TEAL_TINT if c == tint_col else WHITE, stroke=RULE, size=SMALL,
                      rounded=False, align="left" if c == 0 else "right")
        foot = top + 26 * (len(body) + 1)
        for c, (cx, w, value) in enumerate(zip(xs, widths, total)):
            d.box(f"<b>{esc(value)}</b>", cx, foot, w, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False,
                  align="left" if c == 0 else "right")
        sum_row = d.container(x, foot, pw, 26)
        step = d.box(stage, x, foot + 50, pw, 56, fill=WHITE, stroke=GRAY, size=SMALL, stroke_width=1.5, align="left")
        out = d.box(result, x, foot + 50 + 56 + 28, pw, 64, fill=result_fill, stroke=result_fill, color=WHITE, size=13, rounded=False)
        d.arrow(sum_row, step, exit=(0.5, 1), entry=(0.5, 0), width=2)
        d.arrow(step, out, exit=(0.5, 1), entry=(0.5, 0), width=2)

    left_cols, left_w = ["Line", "Quantity", "UnitPrice"], [100, 150, 168]
    right_cols, right_w = ["Line", "Quantity", "UnitPrice", "LineAmount"], [70, 110, 110, 128]
    panel(0, "<b>A calculated field</b><br>Quantity*UnitPrice", GRAY, left_cols, left_w,
          [[n, str(q), str(p)] for n, q, p in lines], ["Sum", str(qty), str(price)], None,
          f"<b>Sums first, multiplies last.</b><br>Sum of Quantity × Sum of UnitPrice = {qty} × {price}",
          f"<b>{wrong:,}: wrong</b><br>No line was multiplied; the result is not the revenue.", CORAL)
    panel(442, "<b>A custom column in the source</b><br>LineAmount = Quantity*UnitPrice", BLUE, right_cols, right_w,
          [[n, str(q), str(p), str(q * p)] for n, q, p in lines], ["Sum", str(qty), str(price), str(right)], 3,
          f"<b>Multiplies first, sums last.</b><br>{' + '.join(f'{q} × {p}' for _, q, p in lines)} = {' + '.join(map(str, products))}",
          f"<b>{right:,}: correct</b><br>Each line was multiplied, then the PivotTable added the products.", TEAL)
    bottom = 62 + 26 * 4 + 50 + 56 + 28 + 64
    _note(d, f"An illustration with {_word(len(lines))} invented lines, not Charles River values. A calculated field is evaluated on the totals of the "
             "fields it names. Tutorial 6.2 adds StdCostAmount to the source for that reason.", bottom + 14)
    return d


# -- IF-06-0-C: the same change in the Furniture margin at two levels ------------------------------------------------------------

def if_06_0_c() -> Diagram:
    """Volume, mix, price and cost, at the Furniture level (Tutorial 6.3) and product type by product type (Exercise 6.4)."""
    d_ = ctx.data()
    g4, ex4 = ctx.values("ch06.g4"), ctx.values("ch06.ex4")
    cats = ["Volume", "Mix", "Price", "Cost"]
    furniture = [g4["t_volume"], g4["t_mix"], g4["t_price"], 0.0]
    by_type = [ex4["volume"], ex4["mix"], ex4["price"], ex4["cost"]]
    assert abs(sum(furniture) - g4["change"]) < 0.01 and abs(sum(by_type) - g4["change"]) < 0.01, "both bridges sum to the change"
    assert abs(furniture[0] - by_type[0]) < 0.01, "volume is the same at both levels"
    lo, hi = min(furniture + by_type), max(furniture + by_type)
    step = 40000                                       # a step that leaves room above the tallest bar for its label
    ticks = list(range(int(math.floor((lo - 0.08 * (hi - lo)) / step) * step),
                       int(math.ceil((hi + 0.1 * (hi - lo)) / step) * step) + step, step))
    money_k = lambda v: "$0" if v == 0 else (MINUS if v < 0 else "") + f"${abs(v) / 1000:,.0f}K"
    d = Diagram("The Same Change in the Furniture Margin at Two Levels")
    key_y = 0
    _swatch(d, 0, key_y + 3, BLUE, BLUE)
    d.text("Furniture as a whole (Tutorial 6.3): price is price lists plus promotions", 20, key_y, 420, 20, size=SMALL, valign="middle")
    d.box("", 450, key_y + 3, 14, 14, fill=BLUE_TINT, stroke=BLUE, stroke_width=2, rounded=False)
    d.text("Product type by product type (Exercise 6.4)", 470, key_y, 390, 20, size=SMALL, valign="middle")
    d.text(f"<b>Effects on the change in the Furniture margin, fiscal {d_.C} third quarter to fourth quarter "
           f"({_signed(g4['change'], 0)})</b>", 0, 32, 860, 20, size=SMALL)
    plot = kit.Plot(d, 0, 56, 860, 400, None, y_ticks=ticks, categories=cats, y_fmt=money_k, bottom=30)
    d.box("", plot.px, plot.y_of(0) - 1, plot.pw, 2, fill=INK, stroke=INK, rounded=False)        # the zero line, where the bars start
    slot = plot.pw / len(cats)
    bw = slot * 0.30
    for i in range(len(cats)):
        cx = plot.px + slot * (i + 0.5)
        for j, (value, fill, stroke, width) in enumerate(((furniture[i], BLUE, BLUE, 1), (by_type[i], BLUE_TINT, BLUE, 2))):
            bx = cx - bw - 2 + j * (bw + 4)
            y0, y1 = plot.y_of(0), plot.y_of(value)
            top, height = min(y0, y1), abs(y1 - y0)
            if height >= 1:
                d.box("", bx, top, bw, height, fill=fill, stroke=stroke, stroke_width=width, rounded=False)
            label = "$0" if value == 0 else _signed(value, 0)
            lw = text_width(f"<b>{label}</b>", SMALL, False) + 8                       # a white label hides the gridline behind it
            d.vertex(f"<b>{label}</b>", f"text;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;fontSize={SMALL};fontColor={INK};"
                     f"{FONT}spacing=0;fillColor={WHITE};strokeColor=none;", bx + bw / 2 - lw / 2,
                     top - 22 if value >= 0 else top + height + 3, lw, 18)
    cost_slot = plot.px + slot * (cats.index("Cost") + 0.5)
    d.text("<i>Zero by construction: every item has one standard cost.</i>", cost_slot - slot / 2 + 8, plot.y_of(0) + 10, slot - 16, 50,
           size=SMALL, color=GRAY)
    bottom = 56 + 400
    _note(d, f"Both sets of effects add up to the same change, {_signed(g4['change'], 0)}, and volume is the same at both levels "
             f"({_signed(furniture[0], 0)}). The rest divides differently because the level differs: at the product-type level, shifts "
             f"between items within a type appear as price and cost, not as mix. Every bar starts at the zero line.", bottom + 10)
    return d


# -- IF-06-1-A: the Power Query Editor with the TrialBalance query -----------------------------------------------------------------

def _trial_balance(rows: int) -> tuple[list[tuple], int]:
    """The first accounts of the TrialBalance query as Exercise 6.1 builds it: the postings before the next
    fiscal year, without the two closes of the current year, grouped by account and merged with the chart."""
    d = ctx.data()
    close1, close2 = d.closes_of(d.C)
    found = d.q(
        "SELECT g.AccountID, ROUND(SUM(g.Debit), 2), ROUND(SUM(g.Credit), 2), a.AccountNumber, a.AccountName, "
        "a.AccountType, a.AccountSubType FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        "WHERE g.PostingDate < ? AND g.VoucherNumber NOT IN (?, ?) GROUP BY g.AccountID ORDER BY a.AccountNumber",
        f"{d.N}-01-01", close1, close2)
    return found[:rows], len(found)


def if_06_1_a() -> Diagram:
    """The Power Query Editor with the applied steps of TrialBalance after Step 4 (Exercise 6.1)."""
    shown, total = _trial_balance(8)
    d = Diagram("The TrialBalance Query in the Power Query Editor")
    xl.title_bar(d, 0, 0, 860, "TrialBalance - Power Query Editor")
    d.box("›", 0, 34, 14, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False)       # the collapsed Queries pane
    px, pw = 690, 170                                                                        # the Query Settings pane
    gx, gright = 20, px - 8                                                                  # the preview grid
    formula = '= Table.Sort(#"Expanded ChartOfAccounts",{{"AccountNumber", Order.Ascending}})'
    d.box("<i>fx</i>", gx, 34, 26, 26, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(esc(formula), gx + 28, 34, gright - gx - 28, 26, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    heads = ["", "AccountID", "Debit", "Credit", "AccountNumber", "AccountName", "AccountType", "AccountSubType"]
    values = [[str(r + 1), str(row[0]), _general(row[1]), _general(row[2]), str(row[3]), row[4], row[5], row[6]]
              for r, row in enumerate(shown)]
    tight = 3
    # Every column but AccountName takes its widest value or its header; the name takes what is left and is cut to it.
    need = lambda c: max([text_width(heads[c], SMALL, False)] + [text_width(v[c], SMALL, False) for v in values]) + 2 * tight + 2
    widths = [26] + [round(need(c)) for c in range(1, 8)]
    widths[5] = (gright - gx) - (sum(widths) - widths[5])
    assert widths[5] >= 110, widths
    xs = [gx]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    for cx, w, head in zip(xs, widths, heads):
        _box(d, esc(head), cx, 68, w, 26, fill=GRAY_TINT, align="left", spacing=tight)
    for r, row in enumerate(values):
        for c, (cx, w, v) in enumerate(zip(xs, widths, row)):
            _box(d, esc(_clip(v, w, margin=2 * tight + 14) if c == 5 else v), cx, 94 + r * 24, w, 24, fill=GRAY_TINT if c == 0 else WHITE,
                 color=GRAY if c == 0 else INK, align="left" if c >= 5 else "right", spacing=tight)
    grid_bottom = 94 + len(values) * 24
    # Query Settings pane with the Applied Steps.
    d.box("<b>Query Settings</b>", px, 34, pw, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.text("<b>Name</b>", px + 6, 66, pw - 12, 20, size=SMALL)
    d.box("TrialBalance", px + 6, 86, pw - 12, 24, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.text("<b>Applied Steps</b>", px + 6, 118, pw - 12, 20, size=SMALL)
    steps = ["Source", "Navigation", "Filtered Rows", "Filtered Rows1", "Grouped Rows", "Merged Queries",
             "Expanded ChartOfAccounts", "Sorted Rows"]
    for i, name in enumerate(steps):
        last = i == len(steps) - 1
        _box(d, f"<b>{name}</b>" if last else name, px + 6, 140 + i * 24, pw - 12, 24, fill=BLUE_TINT if last else WHITE,
             align="left", spacing=tight)
    xl.emphasis(d, px + 6, 140 + 2 * 24, pw - 12, 24 * 3)                      # the two filters and the grouping of Steps 2 and 3
    bottom = max(grid_bottom, 140 + len(steps) * 24) + 12
    xl.status_bar(d, 0, bottom, 860, f"7 COLUMNS, {total} ROWS")
    _note(d, "Outlined: the three steps that Steps 2 and 3 of the exercise add, the two filters (the dates before the next year, and "
             "the two closes) and the grouping by account. The grid shows the first accounts by number, without data type icons, and "
             "cuts a long account name to its column; the preview is not the whole query.", bottom + 32)
    return d


# -- IF-06-1-B: the reconciliation of Requirement 5 --------------------------------------------------------------------------------

def _hd(text: str, align: str = "left") -> dict:
    """A heading cell of a plain grid: light blue, bold."""
    return dict(html=f"<b>{text}</b>", fill=BLUE_TINT, align=align)


def if_06_1_b() -> Diagram:
    """Ex 6.1: the product revenue accounts against InvoiceLines, and the three invoices dated in the year before."""
    data = ctx.data()
    ex1 = ctx.values("ch06.ex1")
    y, p = data.C, data.P
    recon = ex1["recon"]
    invoices = sorted(ex1["invoices"], key=lambda i: i["number"])
    explained = [round(sum(i["amounts"].get(r["group"], 0.0) for i in invoices), 2) for r in recon]
    unexplained = [round(r["diff"] - e, 2) + 0.0 for r, e in zip(recon, explained)]
    assert all(u == 0 for u in unexplained), "each difference is exactly the invoices of its group"
    differing = [i for i, r in enumerate(recon) if abs(r["diff"]) >= 0.005]
    assert len(differing) == len(invoices), "one invoice for each account with a difference"
    ids = {i["number"]: data.one("SELECT SalesInvoiceID FROM SalesInvoice WHERE InvoiceNumber = ?", i["number"]) for i in invoices}
    d = Diagram("The Reconciliation of Requirement 5 on the Worksheet Ex 6.1")
    _formula_bar(d, 0, 0, 860, "D5", esc(f"=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$B5,InvoiceLines[FiscalYear],{y})"))
    widths = [34, 100, 108, 128, 128, 98, 150, 110]
    letters = list("ABCDEFG")
    total = lambda values: _money(round(sum(values), 2) + 0.0)
    rows = [dict(n="3", cells=[dict(text=f"Revenue reconciliation, fiscal {y}: product revenue accounts against InvoiceLines", bold=True,
                                    span=7, clip=False)]),
            dict(n="4", h=52, cells=[_hd("Account"), _hd("Item group"), _hd("Account<br>balance", "right"),
                                     _hd(f"InvoiceLines<br>{y}", "right"), _hd("Difference", "right"),
                                     _hd("Explained by<br>the invoices<br>below", "right"), _hd("Unexplained", "right")])]
    first_data = len(rows)
    for r, e, u in zip(recon, explained, unexplained):
        rows.append(dict(n=str(len(rows) + 3), cells=[dict(text=r["account"], align="left"), r["group"], _money(r["balance"]),
                                                      _money(r["lines"]), _money(r["diff"]), _money(e), _money(u)]))
    rows.append(dict(n=str(len(rows) + 3), cells=[dict(text="Total", bold=True), "",
                                                 *[dict(text=total(v), bold=True) for v in (
                                                     [r["balance"] for r in recon], [r["lines"] for r in recon],
                                                     [r["diff"] for r in recon], explained, unexplained)]]))
    rows.append(dict(n=str(len(rows) + 3), cells=[]))
    rows.append(dict(n=str(len(rows) + 3), cells=[dict(text=f"Invoices numbered in fiscal {y} but dated in fiscal {p} (Exercise 5.2)",
                                                      bold=True, span=7, clip=False)]))
    rows.append(dict(n=str(len(rows) + 3), cells=[_hd("SalesInvoiceID"), _hd("InvoiceNumber"), _hd("InvoiceDate", "right"),
                                                 _hd("Item group"), _hd("Line total", "right")]))
    for inv in invoices:
        rows.append(dict(n=str(len(rows) + 3), cells=[dict(text=str(ids[inv["number"]]), align="left"), inv["number"],
                                                     dict(text=inv["date"], align="right"), dict(text=inv["group"], align="left"),
                                                     _money(inv["amount"])]))
    geo = _sheet(d, 0, 40, letters, widths, rows)
    xl.select(d, *geo[(first_data, 3)])                                              # D5, the cell whose formula shows in the bar
    for i in differing:
        x0, y0, _, h = geo[(first_data + i, 0)]
        _mark(d, x0, y0, sum(widths[1:]), h, CORAL, inset=1.5)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["TrialBalance", "IncomeStatement", "JournalEntries", "Ex 6.1"], "Ex 6.1")
    _note(d, f"Rows 1 and 2, which hold the title, are scrolled out of view. Selected: D5, whose formula shows in the bar. Outlined: the "
             f"{_word(len(differing))} accounts that exceed the invoice lines, {_and([recon[i]['account'] for i in differing])}. Each "
             f"difference equals one of the {_word(len(invoices))} invoices below, which the ledger posted on {ex1['posted']}, so nothing "
             f"is left unexplained.", bottom + 34)
    return d


# -- IF-06-2-A: the second PivotTable of Exercise 6.2 --------------------------------------------------------------------------

def if_06_2_a() -> Diagram:
    """Ex 6.2: revenue by segment, item group and year, with the change from the previous year, and the Field List's areas."""
    from notes.ch06 import lines
    data = ctx.data()
    g2 = ctx.values("ch06.g2")
    p, y = data.P, data.C
    revenue: dict = {}
    for year in (p, y):
        for r in lines(data, year):
            key = (r["segment"], r["grp"], year)
            revenue[key] = revenue.get(key, 0.0) + r["R"]
    groups = sorted({g for _, g, _ in revenue})                                     # as a PivotTable lists the items
    segments = sorted({s for s, _, _ in revenue})
    assert groups == ["Accessories", "Furniture", "Lighting", "Services", "Textiles"] and len(segments) == 5
    n = len(groups) + 1                                                             # five groups and the year's total
    assert len({(s_, g) for s_, g, _ in revenue}) == g2["n_combos"], "the combinations the guide counts"
    services_only = {s_ for s_, g, _ in revenue if g == "Services"}
    assert len(services_only) == 1 and all(g == "Services" for s_, g, _ in revenue if s_ in services_only),         "one segment buys Services, and buys nothing else"
    services_segment = services_only.pop()

    def total(seg: str | None, grp: str | None, year: int) -> float | None:
        vals = [v for (s_, g, yr), v in revenue.items() if yr == year and (seg is None or s_ == seg) and (grp is None or g == grp)]
        return sum(vals) if vals else None

    def row_values(seg: str | None) -> list[str]:
        """Revenue in thousands under each year's groups and total, columns B to M; blank where the combination has none."""
        out = []
        for year in (p, y):
            for grp in groups + [None]:
                v = total(seg, grp, year)
                out.append("" if v is None else f"{v / 1000:,.0f}")
        return out

    def change_values(seg: str | None) -> list[str]:
        """The change from the earlier year: blank under the earlier year, filled under the report year (columns B to M)."""
        out = [""] * n
        for grp in groups + [None]:
            a, b = total(seg, grp, p), total(seg, grp, y)
            out.append("" if a is None or b is None else f"{b / a - 1:.1%}")
        return out

    d = Diagram("The Second PivotTable of Exercise 6.2")
    year_w = [73, 59, 55, 57, 54, 69]                                       # Accessories, Furniture, Lighting, Services, Textiles, total
    widths = [26, 100] + year_w * 2
    assert sum(widths) <= 860, sum(widths)
    letters = list("ABCDEFGHIJKLM")
    tight = 3
    tint = dict(fill=BLUE_TINT)
    nbsp = "&nbsp;&nbsp;"
    rows = []
    r0 = 16                                                                         # the worksheet row of the first pivot row shown

    def add(cells: list) -> int:
        rows.append(dict(n=str(r0 + len(rows)), cells=cells))
        return len(rows) - 1

    add([dict(text="", **tint), dict(html=xl.bold("Column Labels ▾"), span=12, align="left", **tint)])
    years_cells = [dict(text="", **tint)]
    for year in (p, y):
        years_cells += [dict(text=str(year), align="left", **tint)] + [dict(text="", **tint)] * (len(groups) - 1) + \
                       [dict(text=f"{year} Total", align="left", **tint)]
    add(years_cells)
    head_cells = [dict(html=xl.bold("Row Labels ▾"), align="left", **tint)]
    for _ in (p, y):
        head_cells += [dict(text=g, align="left", **tint) for g in groups] + [dict(text="", **tint)]
    add(head_cells)
    change_row = {}
    for s_ in segments:
        add([dict(text=s_, bold=True, span=2, clip=False)])
        add([dict(html=f"{nbsp}Revenue", align="left")] + [dict(text=v, align="right") for v in row_values(s_)])
        # the label of a change row overflows into column B, which is empty, so it spans A and B
        change_row[s_] = add([dict(html=f"{nbsp}Change from {p}", align="left", span=2, clip=False)] +
                             [dict(text=v, align="right") for v in change_values(s_)[1:]])
    add([dict(text="Total Revenue", bold=True, **tint)] + [dict(text=v, bold=True, align="right", **tint) for v in row_values(None)])
    add([dict(text=f"Total Change from {p}", bold=True, span=1 + n, clip=False, **tint)] +
        [dict(text=v, bold=True, align="right", **tint) for v in change_values(None)[n:]])
    geo = _sheet(d, 0, 0, letters, widths, rows, spacing=tight)
    x0, y0, _, h = geo[(change_row["Wholesale"], 0)]
    _mark(d, x0, y0, sum(widths[1:]), h, CORAL)                                     # the change row that is blank under the earlier year
    bottom = geo["bottom"] + 6
    xl.sheet_tabs(d, 0, bottom, ["Ex 6.1", "Ex 6.2", "Ex 6.3"], "Ex 6.2")
    # The Field List's areas, below the PivotTable.
    fy = bottom + 40
    xl.title_bar(d, 0, fy, 860, "PivotTable Fields")
    d.text("Drag fields between areas below:", 6, fy + 32, 400, 20, size=SMALL)
    areas = [("Filters", []), ("Columns", ["FiscalYear", "ItemGroup"]), ("Rows", ["CustomerSegment", "Σ Values"]),
             ("Values", ["Revenue", f"Change from {p}"])]
    aw, ay = (860 - 3 * 8) / 4, fy + 56
    for i, (name, items) in enumerate(areas):
        ax = i * (aw + 8)
        d.box(f"<b>{name}</b>", ax, ay, aw, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        d.box("", ax, ay + 24, aw, 62, fill=WHITE, stroke=RULE, rounded=False)
        for k, item in enumerate(items):
            d.box(esc(item), ax + 6, ay + 30 + k * 26, aw - 12, 24, fill=WHITE, stroke=GRAY, size=SMALL, align="left", rounded=False)
            d.text("▾", ax + aw - 28, ay + 30 + k * 26, 16, 24, size=SMALL, color=GRAY, align="center", valign="middle")
        if name == "Columns":
            _mark(d, ax, ay, aw, 86, CORAL)
    pane_bottom = ay + 86
    d.box("", 0, fy + 28, 860, pane_bottom - fy - 28, fill="none", stroke=RULE, rounded=False)
    _note(d, f"Revenue is in thousands of dollars so that {_word(2 * n)} columns fit; the PivotTable shows whole dollars. Rows 1 to 15, which hold "
             f"the first PivotTable, and column N, the Grand Total of the two years, are not shown. Blank cells are combinations with no "
             f"revenue: only {services_segment} buys Services. Outlined: the Columns area, where FiscalYear sits above ItemGroup, and the "
             f"Change from {p} row of Wholesale, blank under {p} and filled under {y}.", pane_bottom + 10)
    return d


# -- IF-06-4-A: the two bridges side by side ------------------------------------------------------------------------------------------

def if_06_4_a() -> Diagram:
    """Ex 6.4: the bridge by product type beside Tutorial 6.3's Furniture bridge, with the check row and the discounts."""
    data = ctx.data()
    g4, ex4 = ctx.values("ch06.g4"), ctx.values("ch06.ex4")
    y = data.C
    q3, q4, change = g4["q3"], g4["q4"], g4["change"]
    typ = dict(price=ex4["price"], cost=ex4["cost"], volume=ex4["volume"], mix=ex4["mix"], promo=g4["promo_type"])
    fur = dict(price=g4["t_price"], cost=0.0, volume=g4["t_volume"], mix=g4["t_mix"], promo=g4["t_promo"])
    for side in (typ, fur):
        side["sum"] = side["price"] + side["cost"] + side["volume"] + side["mix"]
        side["check"] = round(side["sum"] - change, 2) + 0.0
        assert side["check"] == 0, "the four effects add up to the change at both levels"
    assert abs(g4["t_price"] - (g4["t_lists"] + g4["t_promo"])) < 0.01, "price at the Furniture level is price lists plus promotions"
    d = Diagram("The Two Bridges of Exercise 6.4 Side by Side")
    margin3, margin4 = f"{y}-Q3 margin", f"{y}-Q4 margin"
    labels = [margin3, margin4, "Change in margin", "Price", "Cost", "Volume", "Mix", "Sum of the four effects",
              "Check: sum of effects less the change", "of which promotional discounts, in the price effect"]
    first = 32
    row_of = {label: first + i for i, label in enumerate(labels)}
    assert row_of["Change in margin"] == 34 and row_of["Sum of the four effects"] == 39, "the guide says B39 and B34"
    values = {margin3: (q3, q3), margin4: (q4, q4), "Change in margin": (change, change), "Price": (typ["price"], fur["price"]),
              "Cost": (typ["cost"], fur["cost"]), "Volume": (typ["volume"], fur["volume"]), "Mix": (typ["mix"], fur["mix"]),
              "Sum of the four effects": (typ["sum"], fur["sum"]), labels[8]: (typ["check"], fur["check"]),
              labels[9]: (typ["promo"], fur["promo"])}
    widths = [34, 410, 200, 216]
    _formula_bar(d, 0, 0, 860, f"B{row_of[labels[8]]}", esc("=ROUND(B39-B34,2)"))
    shown = lambda label, v: _general(v) if label.startswith("Check") or v == 0 else _money(v)
    rows = [dict(n=str(first - 1), cells=[dict(text="(3), (4) The four effects, and Tutorial 6.3's bridge", bold=True, fill=BLUE_TINT, clip=False),
                                          _hd("Product types", "right"), _hd("Tutorial 6.3 (Furniture)", "right")])]
    for label in labels:
        a, b = values[label]
        rows.append(dict(n=str(row_of[label]), cells=[dict(text=label, align="left", bold=label in ("Change in margin", "Sum of the four effects")),
                                                      dict(text=shown(label, a)), dict(text=shown(label, b))]))
    top = 40
    letters = _sheet(d, 0, top, ["A", "B", "C"], widths, [])                           # the column letters
    y0 = _gap(d, 0, letters["bottom"], 860, f"rows 1 to {first - 2} hold the PivotTable, the per-unit measures and the effects of each product type; not shown")
    geo = _sheet(d, 0, y0, ["A", "B", "C"], widths, rows, show_letters=False)
    cx, cy, cw, ch = geo[(1 + labels.index("Cost"), 1)]
    _mark(d, cx, cy, cw, ch, CORAL)
    xl.select(d, *geo[(1 + labels.index(labels[8]), 1)])
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 6.3", "Ex 6.4", "Ex 6.5"], "Ex 6.4")
    _note(d, f"Selected: B{row_of[labels[8]]}, the check, which reads zero in both columns. Outlined: the cost effect by product type, "
             f"{_signed(typ['cost'], 2)}, where Tutorial 6.3 reads zero because every item has one standard cost. The two columns share the "
             f"margins, the change and the volume effect; price lists and promotions together make the Furniture-level price "
             f"({_signed(g4['t_lists'], 2)} and {_signed(g4['t_promo'], 2)}).", bottom + 34)
    return d


# -- IF-06-5-A: the expectation worksheet of Exercise 6.5 ------------------------------------------------------------------------------

def if_06_5_a() -> Diagram:
    """Ex 6.5 Expectation: the thresholds, the grid with the flagged rows shaded, the list of flagged differences and its count."""
    data = ctx.data()
    g5 = ctx.values("ch06.g5")
    p, y = data.P, data.C
    pct_threshold, usd_threshold = 0.1, 50000                                        # B3 and B4 of the worksheet (Step 2)
    rows5 = g5["rows"]
    assert len(rows5) == g5["n_cells"] == 20
    flagged = [abs(r["diff"]) > pct_threshold * r["exp"] and abs(r["diff"]) > usd_threshold for r in rows5]
    assert [(r["group"], r["q"]) for r, f in zip(rows5, flagged) if f] == [(r["group"], r["q"]) for r in g5["both"]], \
        "the thresholds flag the rows the guide lists"
    listed = [r for r, f in zip(rows5, flagged) if f]
    d = Diagram("The Expectation Worksheet of Exercise 6.5")
    first_flag = flagged.index(True)
    sel_row = 7 + first_flag
    _formula_bar(d, 0, 0, 860, f"G{sel_row}", esc(f"=AND(ABS(E{sel_row})>$B$3*C{sel_row},ABS(E{sel_row})>$B$4)"))
    tight = 2
    letters = ["A", "B", "C", "D", "E", "F", "G", "", "I", "J", "M", "N"]             # H is a narrow gap; columns K and L of the list are hidden
    grid_vals = [[r["group"], str(r["q"]), _money(r["exp"]), _money(r["act"]), _money(r["diff"]), f"{r['pct']:.1%}"] for r in rows5]
    list_vals = [[r["group"], str(r["q"]), _money(r["diff"]), f"{r['pct']:.1%}"] for r in listed]

    def fit(texts: list[str], bold: bool = False) -> float:
        return max(text_width(t, SMALL, bold) for t in texts) + 2 * tight + 4

    widths = [26,
              fit(["Percentage threshold", "ItemGroup"] + [v[0] for v in grid_vals]),            # A
              fit(["Quarter"], True), fit(["Expectation"] + [v[2] for v in grid_vals], True),   # B, C
              fit(["Recorded"] + [v[3] for v in grid_vals], True), fit(["Difference"] + [v[4] for v in grid_vals], True),    # D, E
              fit(["Difference"] + [v[5] for v in grid_vals], True), fit(["Flagged", "FALSE"], True),                          # F, G
              8,                                                                                 # H, the gap
              max(fit(["Differences flagged"] + [v[0] for v in list_vals]), fit(["ItemGroup"], True)),   # I
              fit(["Quarter"], True), fit(["Difference"] + [v[2] for v in list_vals], True),     # J, M
              fit(["Difference"] + [v[3] for v in list_vals], True)]                             # N
    widths = [round(w) for w in widths]
    assert sum(widths) <= 860, (sum(widths), widths)
    widths[9] += min(6, 860 - sum(widths))                                              # a little air for the longest label of I
    blue = dict(color=BLUE, bold=True, fill=BLUE_TINT)
    shade = lambda f: dict(fill=AMBER_TINT) if f else {}
    hd = lambda t, a="right": _hd(t, a)
    rows = [dict(n="1", cells=[dict(text="Exercise 6.5: A Substantive Analytical Procedure on Quarterly Revenue", bold=True, span=7, clip=False)]),
            dict(n="2", cells=[]),
            dict(n="3", cells=["Percentage threshold", dict(text="0.1", **blue)]),
            dict(n="4", cells=["Dollar threshold", dict(text="50000", **blue)]),
            dict(n="5", cells=[dict(text="")] * 8 + [dict(text="(3) Differences over both thresholds", bold=True, span=4, clip=False)]),
            dict(n="6", h=36, cells=[hd("ItemGroup", "left"), hd("Quarter"), hd(f"Expectation<br>({p})"), hd(f"Recorded<br>({y})"),
                                     hd("Difference"), hd("Difference<br>%"), hd("Flagged"), dict(text=""),
                                     hd("ItemGroup", "left"), hd("Quarter"), hd("Difference"), hd("Difference<br>%")])]
    for k, (r, f) in enumerate(zip(rows5, flagged)):
        v = grid_vals[k]
        cells = [dict(text=v[0], **shade(f)), dict(text=v[1], **shade(f)), dict(text=v[2], **shade(f)), dict(text=v[3], **shade(f)),
                 dict(text=v[4], **shade(f)), dict(text=v[5], align="right", **shade(f)),
                 dict(text="TRUE" if f else "FALSE", bold=f, align="right", **shade(f))]
        if k < len(listed):
            cells += [dict(text="")] + [dict(text=t, align="left" if i == 0 else "right") for i, t in enumerate(list_vals[k])]
        elif k == 8:
            cells += [dict(text=""), dict(text="Differences flagged", clip=False), dict(text=str(len(listed)), bold=True)]
        rows.append(dict(n=str(7 + k), cells=cells))
    geo = _sheet(d, 0, 40, letters, widths, rows, spacing=tight)
    xl.select(d, *geo[(5 + 1 + first_flag, 6)])
    for rr in (2, 3):                                                                # the two input cells
        x0, y0, w0, h0 = geo[(rr, 1)]
        _mark(d, x0, y0, w0, h0, TEAL, inset=1.5)
    cx, cy, cw, chh = geo[(6 + 8, 9)]                                               # the cell that counts the flagged rows
    _mark(d, cx, cy, cw, chh, TEAL)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 6.4", "Ex 6.5", "Ex 6.5 Expectation", "Ex 6.6"], "Ex 6.5 Expectation")
    ky = bottom + 34
    _swatch(d, 0, ky + 3, AMBER_TINT)
    d.text("Flagged rows: a conditional formatting rule based on column G", 20, ky, 420, 20, size=SMALL, valign="middle")
    d.text(f"<i>Blue font: the two input cells (outlined in teal). Selected: G{sel_row}, the first flagged row, whose formula shows in the "
           f"bar. The list at the right is filled by a formula from the grid, and the outlined cell counts its rows. Columns K and L of the "
           f"list, the expectation and the recorded amount, are hidden.</i>", 0, ky + 28, 860, 52, size=SMALL, color=GRAY)
    return d


FIGURES = {"IF-06-0-A": if_06_0_a, "IF-06-0-B": if_06_0_b, "IF-06-0-C": if_06_0_c, "IF-06-1-A": if_06_1_a,
           "IF-06-1-B": if_06_1_b, "IF-06-2-A": if_06_2_a, "IF-06-4-A": if_06_4_a, "IF-06-5-A": if_06_5_a}
