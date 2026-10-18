"""Instructor figures of Chapter 4 (guides in facts/instructor/guides/chapter-04-excel-essentials/)."""

from __future__ import annotations

import ctx
import excel as xl
import kit
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HIGHLIGHT, INK, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

ITEM_COLUMNS = ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "StandardCost", "ListPrice", "UnitOfMeasure",
                "SupplyMode", "CollectionName", "LifecycleStatus"]            # Tutorial 4.1, Step 5
STRAIGHT = "edgeStyle=none;"
DASHED_AMBER = "rounded=0;html=1;fillColor=none;strokeColor=%s;strokeWidth=2;dashed=1;dashPattern=6 3;" % AMBER


# -- shared drawing helpers ---------------------------------------------------------------------------------------------

def _money(x: float) -> str:
    return f"{x:,.2f}"


def _general(x: float) -> str:
    """A number as Excel's General format shows it: 0.0 reads 0, 0.08 reads 0.08."""
    return f"{x:.15g}"


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow worksheet column shows it."""
    if text_width(text, size, bold) <= width - margin:
        return text
    while text and text_width(text + "…", size, bold) > width - margin:
        text = text[:-1]
    return text + "…"


def _fit(headers: list[str], rows: list[list[str]], pad: float = 16, filters: set[int] = frozenset(),
         floor: float = 40) -> list[float]:
    """Each column as wide as its bold header (plus room for a filter button) or its widest value, plus padding."""
    out = []
    for c, head in enumerate(headers):
        need = max([text_width(head, SMALL, True) + (18 if c in filters else 0)]
                   + [text_width(r[c], SMALL, False) for r in rows])
        out.append(round(max(floor, need + pad)))
    return out


def _dropdown(d: Diagram, geo: tuple, active: bool = False) -> None:
    """The filter button of a Table header: a small white triangle; an active filter adds a bar under it (a funnel)."""
    hx, hy, hw, hh = geo
    d.vertex("", "triangle;direction=south;html=1;fillColor=#FFFFFF;strokeColor=none;", hx + hw - 16,
             hy + hh / 2 - (5 if active else 3.5), 9, 7)
    if active:
        d.box("", hx + hw - 13, hy + hh / 2 + 3, 3, 5, fill=WHITE, stroke=WHITE, rounded=False)


def _gap(d: Diagram, x: float, y: float, w: float, text: str, h: float = 24) -> float:
    """A band that stands for the rows of a long worksheet that the figure leaves out."""
    d.box(f"<i>{esc(text)}</i>", x, y, w, h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, rounded=False, dashed=True)
    return y + h


def _sheet(d: Diagram, x: float, y: float, letters: list[str], widths: list[float], rows: list[dict],
           number_color: str = GRAY, show_letters: bool = True, row_h: float = 22) -> dict:
    """A worksheet with a letter row and rows of any height.

    widths[0] is the row-number column; letters label the others.  A row is {"n": row number, "cells": [cell, ...],
    "h": height}, its cells taken in order from column A (a cell with span uses that many columns); a cell is a string or a dict: text, bold, italic, align ("left", "right", "center"), color, fill,
    stroke, html (a ready label), span (columns the text overflows across, as Excel text does when the cells beside
    it are empty), clip (False keeps a long text whole), filter (True draws the filter button, "active" a funnel),
    bar (0..1, a data bar behind the value).  Returns {(row index, column): (x, y, w, h)} and "bottom"."""
    xs = [x]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    top = 22 if show_letters else 0
    if show_letters:
        for cx, w, letter in zip(xs, widths, ["", *letters]):
            d.box(esc(letter), cx, y, w, 22, fill=GRAY_TINT, stroke=RULE, color=GRAY, size=SMALL, rounded=False)
    geo: dict = {}
    ry = y + top
    for i, row in enumerate(rows):
        h = row.get("h", row_h)
        d.box(esc(row["n"]), xs[0], ry, widths[0], h, fill=GRAY_TINT, stroke=RULE, color=row.get("number_color", number_color),
              size=SMALL, rounded=False)
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
                shown = _clip(text, cw, bold=bold, margin=cell.get("margin", 22 if cell.get("filter") else 14)) \
                    if cell.get("clip", True) else text
                label = esc(shown)
                if bold:
                    label = f"<b>{label}</b>"
                if cell.get("italic"):
                    label = f"<i>{label}</i>"
            fill = cell.get("fill", WHITE)
            stroke = cell.get("stroke", RULE)
            bar = cell.get("bar")
            d.box("" if bar is not None else label, cx, ry, cw, h, fill=fill, stroke=stroke, color=cell.get("color", INK),
                  size=SMALL, rounded=False, align=align, valign=cell.get("valign", "middle"))
            if bar is not None:
                d.box("", cx + 2, ry + 3, max(1.0, (cw - 4) * bar), h - 6, fill=BLUE_TINT, stroke=BLUE, stroke_width=1,
                      rounded=False)
                d.text(label, cx + 4, ry, cw - 8, h, size=SMALL, align="right", valign="middle")
            geo[(i, c)] = (cx, ry, cw, h)
            if cell.get("filter"):
                _dropdown(d, geo[(i, c)], active=cell["filter"] == "active")
            c += span
        ry += h
    geo["bottom"] = ry
    return geo


def _header(text: str, **kw) -> dict:
    """A Table header cell: blue fill, white bold text."""
    return dict(text=text, bold=True, fill=BLUE, stroke=BLUE, color=WHITE, align="left", **kw)


def _formula_bar(d: Diagram, x: float, y: float, w: float, name: str, formula_html: str, h: float = 28) -> None:
    """The Name Box, the fx label and a formula bar whose formula may carry markup and wrap to a second line."""
    d.box(esc(name), x, y, 90, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<i>fx</i>", x + 94, y, 30, 28, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(formula_html, x + 128, y, w - 128, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)


def _slicer(d: Diagram, x: float, y: float, w: float, title: str, items: list[str], selected: str) -> float:
    """An Excel slicer: a title strip and one button for each value, the selected one filled.  Returns the height."""
    button_h = 22
    h = 32 + len(items) * (button_h + 4) + 4
    d.box("", x, y, w, h, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
    d.box(f"<b>{esc(title)}</b>", x + 1, y + 1, w - 2, 26, fill=GRAY_TINT, stroke=GRAY_TINT, size=SMALL, align="left",
          rounded=False)
    for i, name in enumerate(items):
        on = name == selected
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), x + 6, y + 32 + i * (button_h + 4), w - 12, button_h,
              fill=BLUE if on else WHITE, stroke=BLUE if on else RULE, color=WHITE if on else INK, size=SMALL,
              rounded=False)
    return h


def _hidden_text(visible: list[str], n: int) -> str:
    """'A to I, L and N': the letters among a worksheet's first n columns that the figure hides."""
    letters = [chr(65 + i) for i in range(n) if chr(65 + i) not in visible]
    runs: list[list[str]] = []
    for letter in letters:
        if runs and ord(letter) == ord(runs[-1][-1]) + 1:
            runs[-1].append(letter)
        else:
            runs.append([letter])
    parts = [part for run in runs for part in ([f"{run[0]} to {run[-1]}"] if len(run) > 2 else run)]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def _columns(data, table: str, columns: dict[str, str]) -> int:
    """Each letter holds its column in the worksheet, in the schema's order; returns the number of columns."""
    names = [r[1] for r in data.q(f"PRAGMA table_info({table})")]
    for letter, name in columns.items():
        assert names[ord(letter) - 65] == name, (table, letter, name, names)
    return len(names)


def _mark(d: Diagram, x: float, y: float, w: float, h: float, color: str) -> str:
    """An outline like xl.emphasis in another color (a blue outline would vanish on a blue Table header)."""
    left, top = max(0, x - 2), max(0, y - 2)
    return d.outline(left, top, min(860, x + w + 2) - left, y + h + 2 - top, color, width=2.5, front=True)


def _label(d: Diagram, text: str, x: float, y: float, w: float, h: float = 20, **kw) -> str:
    """A white label that sits over a line or a gap."""
    return d.box(text, x, y, w, h, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False, **kw)


# -- IF-04-0-A: what a fill across does to a structured reference --------------------------------------------------------

def if_04_0_a() -> Diagram:
    """The right edge of SalesInvoiceLine, and the grid formula of Tutorial 4.2 typed, filled across and pasted."""
    data = ctx.data()
    chapter = ctx.values("ch04.chapter")
    n_columns = _columns(data, "SalesInvoiceLine", {"J": "Discount", "K": "LineTotal", "M": "PromotionID", "O": "PricingMethod"})
    letters_of = chapter["letters"]
    assert [letters_of[c] for c in ("Discount", "LineTotal", "PromotionID", "PricingMethod", "ListAmount", "DiscountAmount")] \
        == list("JKMOPQ"), letters_of
    grid = chapter["t2"]["grid"]
    from guide_contexts.ch04 import DISCOUNT_RATES                         # the rates across row 15 of the tutorial's grid
    method, (first_rate, second_rate) = grid[0]["method"], DISCOUNT_RATES[:2]          # A16, and B15 and C15
    typed, pasted = grid[0]["counts"][0], grid[0]["counts"][1]
    # A text criterion never equals a number, so a COUNTIFS that reads the numeric columns finds nothing.
    drifted = data.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE CAST(LineTotal AS TEXT) = ?", method)
    assert drifted == 0 and typed > 0 and pasted > 0
    d = Diagram("What a Fill Across Does to a Structured Reference")

    # The right edge of the Table.
    heads = ["Discount", "LineTotal", "PromotionID", "PricingMethod", "ListAmount", "DiscountAmount"]
    letters = ["J", "K", "M", "O", "P", "Q"]
    rows = data.q("SELECT SalesInvoiceLineID, Quantity, BaseListPrice, Discount, LineTotal, PromotionID, PricingMethod, "
                  "UnitPrice FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT 2")
    body = []
    for _id, qty, price, disc, total, promo, how, unit in rows:
        body.append([_general(disc), _money(total), "" if promo is None else str(promo), how,
                     _money(xl.xround(qty * price)), _money(xl.xround(qty * unit * disc))])
    widths = [40, 100, 110, 130, 190, 130, 160]
    top = 60
    table = [dict(n="1", h=24, cells=[_header(h) for h in heads])]
    for i, values in enumerate(body):
        table.append(dict(n=str(rows[i][0] + 1), cells=[dict(text=v, fill=WHITE if i % 2 else BLUE_TINT,
                                                              align="left" if c == 3 else "right") for c, v in enumerate(values)],
                          h=24))
    geo = _sheet(d, 0, top, letters, widths, table, number_color=GRAY)
    # The columns the formula means (teal) and the columns it reads after a fill across (coral).
    column_h = 22 + 24 * len(table)
    for col, color in ((0, TEAL), (3, TEAL), (1, CORAL), (4, CORAL)):
        cx, _, cw, _ = geo[(0, col)]
        _mark(d, cx, top, cw, column_h, color)
    for col, text, color in ((0, "meant", TEAL), (3, "meant", TEAL), (1, "after the fill", CORAL), (4, "after the fill", CORAL)):
        cx, _, cw, _ = geo[(0, col)]
        d.text(f"<b>{text}</b>", cx, top - 54, cw, 18, size=SMALL, color=color, align="center")
    # Two arrows that show the shift of one column.
    for a, b in ((0, 1), (3, 4)):
        ax, _, aw, _ = geo[(0, a)]
        bx, _, bw, _ = geo[(0, b)]
        d.edge(d.anchor(ax + aw / 2 + 24, top - 30), d.anchor(bx + bw / 2 - 24, top - 30), end="blockThin", color=CORAL, width=2.5,
               meta=STRAIGHT)
    y = top + column_h + 8
    d.text(f"<i>Columns {_hidden_text(letters, n_columns)} of SalesInvoiceLine are hidden. ListAmount and DiscountAmount are the "
           f"calculated columns of Tutorial 4.1.</i>", 0, y, 860, 20, size=SMALL, color=GRAY)

    # The three formulas.
    def pick(name: str, tone: str) -> str:
        return f'<font color="{tone}"><b>{name}</b></font>'

    f1 = (f"=COUNTIFS(SalesInvoiceLine[{pick('PricingMethod', TEAL)}],$A16,SalesInvoiceLine[{pick('Discount', TEAL)}],B$15)")
    f2 = (f"=COUNTIFS(SalesInvoiceLine[{pick('ListAmount', CORAL)}],$A16,SalesInvoiceLine[{pick('LineTotal', CORAL)}],C$15)")
    f3 = (f"=COUNTIFS(SalesInvoiceLine[{pick('PricingMethod', TEAL)}],$A16,SalesInvoiceLine[{pick('Discount', TEAL)}],C$15)")
    panels = [
        ("1", "Typed in B16, as in Step 5 of Tutorial 4.2", "B16", f1, f"B16 shows {typed:,}",
         f"Counts the {method} lines with a discount of {first_rate:.0%}.", GRAY),
        ("2", "Filled one column to the right with the fill handle", "C16", f2, "C16 shows 0",
         "Each column name moved to the next column of the Table. No error appears, and the count is wrong.", CORAL),
        ("3", "Copied from B16 and pasted into C16", "C16", f3, f"C16 shows {pasted:,}",
         f"The column names and $A16 stay as typed, and B$15 becomes C$15, so C16 counts the {second_rate:.0%} lines.", TEAL),
    ]
    y += 30
    for number, title, cell, formula, shows, reading, tone in panels:
        d.marker(number, 0, y, fill=tone)
        d.text(f"<b>{esc(title)}</b>", 34, y + 2, 520, 20, size=SMALL, valign="middle")
        reading_w = 860 - 34 - 168
        d.text(esc(reading), 34, y + 22, reading_w, 20, size=SMALL, color=GRAY)
        d.box(f"<b>{esc(shows)}</b>", 860 - 160, y, 160, 28, fill=WHITE, stroke=BLUE, stroke_width=2.5, size=SMALL, rounded=False)
        _formula_bar(d, 34, y + 46, 826, cell, formula)
        y += 46 + 28 + 18
    # The locked form.
    locked = ("=COUNTIFS(SalesInvoiceLine[" + pick("[PricingMethod]:[PricingMethod]", TEAL) + "],$A16,SalesInvoiceLine["
              + pick("[Discount]:[Discount]", TEAL) + "],B$15)")
    d.text("<b>Two ways to keep the columns where they are</b>", 0, y, 600, 20, size=SMALL)
    d.text("<b>Paste instead of filling.</b> Copy the cell and paste it: structured references stay as they are.", 0, y + 22, 860,
           20, size=SMALL)
    d.text("<b>Lock the column</b> by writing it with a column range, which a fill leaves alone:", 0, y + 44, 860, 20, size=SMALL)
    d.box(locked, 34, y + 68, 826, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.text("<i>Teal outline and teal names (bold): the columns the formula means. Coral outline and coral names (bold): the columns it reads "
           "after a fill across. Click a cell in the middle of the result and read the formula bar: that is how a drift "
           "shows.</i>", 0, y + 106, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-04-0-B: why a zero control total difference does not show completeness ----------------------------------------------

def if_04_0_b() -> Diagram:
    """Two Tables of one import that both lack an invoice, their zero difference, and the count of the source Table."""
    invoices = [("A", 2), ("B", 1), ("C", 2), ("D", 2), ("E", 1)]          # an invoice and its number of lines (generic)
    lost = "C"                                                              # the invoice the import dropped, with its lines
    imported = [(name, n) for name, n in invoices if name != lost]
    line_h = 22
    d = Diagram("Why a Zero Control Total Difference Does Not Show a Complete Import")
    head_h, strip_h = 40, 22
    xs = {"source": (0, 232), "invoice": (286, 200), "line": (610, 250)}
    top_rows = head_h + strip_h

    def column(key: str, head_html: str, head_fill: str, count_text: str) -> None:
        x, w = xs[key]
        d.box(head_html, x, 0, w, head_h, fill=head_fill, stroke=head_fill, color=WHITE, size=SMALL, rounded=False)
        d.box(f"<b>{esc(count_text)}</b>", x, head_h, w, strip_h, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False,
              align="left")

    n_lines_in = sum(n for _, n in imported)
    column("source", "<b>T16_SalesInvoice</b><br>in CharlesRiver.xlsx", GRAY, f"{len(invoices)} rows")
    column("invoice", "<b>SalesInvoice</b><br>Table in the import", BLUE, f"{len(imported)} rows")
    column("line", "<b>SalesInvoiceLine</b><br>Table in the import", BLUE, f"{n_lines_in} rows")
    y = top_rows
    for name, n in invoices:
        h = n * line_h
        missing = name == lost
        sx, sw = xs["source"]
        d.box(f"<b>Invoice {name}: not imported</b>" if missing else f"Invoice {name}", sx, y, sw, h,
              fill=CORAL_TINT if missing else WHITE, stroke=CORAL if missing else RULE, stroke_width=2 if missing else 1,
              size=SMALL, rounded=False, align="left")
        ix, iw = xs["invoice"]
        lx, lw = xs["line"]
        if missing:
            d.box(f"<i>Invoice {name}: missing</i>", ix, y, iw, h, fill=WHITE, stroke=GRAY, color=GRAY, size=SMALL, rounded=False,
                  dashed=True)
            d.box(f"<i>Its {n} lines: missing</i>", lx, y, lw, h, fill=WHITE, stroke=GRAY, color=GRAY, size=SMALL, rounded=False,
                  dashed=True)
        else:
            d.box(f"Invoice {name}", ix, y, iw, h, fill=BLUE_TINT, stroke=RULE, size=SMALL, rounded=False, align="left")
            for k in range(n):
                d.box(f"Invoice {name}, line {k + 1}", lx, y + k * line_h, lw, line_h, fill=BLUE_TINT, stroke=RULE, size=SMALL,
                      rounded=False, align="left")
        y += h
    rows_bottom = y
    # The two Tables' total rows and the difference between them.
    foot_y = rows_bottom
    ix, iw = xs["invoice"]
    lx, lw = xs["line"]
    left_total = d.box("<b>SUM(SubTotal)</b>", ix, foot_y, iw, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False,
                       align="left")
    right_total = d.box("<b>SUM(LineTotal)</b>", lx, foot_y, lw, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False,
                        align="left")
    mid_x = ix + iw
    gap_w = lx - mid_x
    box_w = 92
    bx = mid_x + (gap_w - box_w) / 2
    d.text("<b>Difference</b><br>of the totals", mid_x, foot_y - 52, gap_w, 36, size=SMALL, align="center", valign="bottom")
    diff = d.box("<b>0</b>", bx, foot_y - 6, box_w, 38, fill=WHITE, stroke=BLUE, stroke_width=2.5, size=14, rounded=False)
    d.edge(left_total, diff, color=GRAY, width=1.5, exit=(1, 0.5), entry=(0, 0.5), meta=STRAIGHT)
    d.edge(right_total, diff, color=GRAY, width=1.5, exit=(0, 0.5), entry=(1, 0.5), meta=STRAIGHT)
    # The count of the source against the count of the import: the one check from outside the import.
    sx, sw = xs["source"]
    src = d.container(sx, head_h, sw, strip_h)
    inv = d.container(ix, head_h, iw, strip_h)
    d.edge(src, inv, start="blockThin", end="blockThin", color=AMBER, dashed=True, width=2.5, exit=(1, 0.5), entry=(0, 0.5),
           meta=STRAIGHT)
    _label(d, f"<b>{len(invoices)} ≠ {len(imported)}</b>", sx + sw + 4, head_h - 22, ix - sx - sw - 8, 18, align="center")
    d.vertex("", DASHED_AMBER, sx, 0, sw, rows_bottom, front=True)
    bottom = foot_y + 26 + 18
    callout_bottom = kit.callout(d, "<b>Agreement inside the import cannot reveal what both sides lack.</b> The invoice and its lines were "
                   "dropped together, so the two totals still agree and the difference is zero. Only evidence from outside the "
                   "import, such as the row count of the source Table, shows that something is missing.", 0, bottom, 860,
                color="amber")
    d.text("<i>An illustration with generic invoices, not Charles River's. Dashed amber: the comparison with the source Table "
           "in CharlesRiver.xlsx, which is outside the import. A control total checks the import against itself; a count of "
           "the source checks the import against the source.</i>", 0, callout_bottom + 10, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-04-1-A: the Ex 4.1 worksheet ------------------------------------------------------------------------------------------

def _formula(*parts) -> str:
    """A formula label: plain strings are escaped, ("b", text) pieces are bold."""
    return "".join(f"<b>{esc(p[1])}</b>" if isinstance(p, tuple) else esc(p) for p in parts)


def if_04_1_a() -> Diagram:
    """Ex 4.1 at the end of the exercise: the period cells, the period's billing and the billing grid by fiscal year."""
    data = ctx.data()
    g = ctx.values("ch04.g1")
    _columns(data, "SalesInvoice", {"G": "SubTotal", "H": "FreightAmount", "I": "TaxAmount", "J": "GrandTotal"})
    year, rows, total = g["year"], g["rows"], g["total"]
    assert rows[-1] == year, "the last grid row is the period's fiscal year"
    parts_check = round(year["sub"] + year["frt"] + year["tax"] - year["gt"], 2) + 0.0
    broken = data.one("SELECT COUNT(*) FROM SalesInvoice WHERE ABS(SubTotal + FreightAmount + TaxAmount - GrandTotal) > 0.005")
    entire = {k: data.one(f"SELECT ROUND(SUM({col}), 2) FROM SalesInvoice") for k, col in
              (("sub", "SubTotal"), ("frt", "FreightAmount"), ("tax", "TaxAmount"), ("gt", "GrandTotal"))}
    keys = ["sub", "frt", "tax", "gt"]
    summed = {k: round(sum(r[k] for r in rows), 2) for k in keys}
    difference = {k: round(summed[k] - entire[k], 2) + 0.0 for k in keys}
    assert parts_check == 0 and broken == 0 and all(v == 0 for v in difference.values())
    entire_n = data.one("SELECT COUNT(*) FROM SalesInvoice")
    assert entire_n == total["n"]
    d = Diagram("The Ex 4.1 Worksheet: the Period Cells, the Period's Billing and the Billing by Fiscal Year")
    widths = [34, 330, 106, 106, 106, 106, 72]
    letters = list("ABCDEF")
    formula = _formula('=SUMIFS(SalesInvoice[GrandTotal],SalesInvoice[', ("b", "[InvoiceDate]:[InvoiceDate]"),
                       '],">="&DATE($A18,1,1),SalesInvoice[', ("b", "[InvoiceDate]:[InvoiceDate]"),
                       '],"<="&DATE($A18,12,31))')
    _formula_bar(d, 0, 0, 860, "E18", formula, h=44)
    top = 52

    def head(*texts: str) -> list:
        return [dict(text=t, bold=True, fill=BLUE_TINT, align="left" if i == 0 else "right") for i, t in enumerate(texts)]

    def title(text: str) -> list:
        return [dict(text=text, bold=True, span=5, clip=False)]

    def money_row(label: str, values: list[str], bold: bool = False) -> list:
        return [dict(text=label, bold=bold)] + [dict(text=v, bold=bold) for v in values]

    description_start = f"First day of the period (a date from {g['first']}-01-01 to {g['end']})"
    description_end = f"Last day of the period; fiscal {g['c']} is the calendar year {g['c']}"
    sheet_rows = [
        dict(n="1", cells=title(f"Exercise 4.1: A Billing Schedule by Fiscal Year")),
        dict(n="2", cells=[]),
        dict(n="3", cells=[dict(text="Parameter", bold=True, fill=BLUE_TINT), dict(text="Value", bold=True, fill=BLUE_TINT, align="right"),
                           dict(text="Description", bold=True, fill=BLUE_TINT, span=4)]),
        dict(n="4", cells=["PeriodStart", dict(text=g["start"], color=BLUE), dict(text=description_start, span=4, clip=False)]),
        dict(n="5", cells=["PeriodEnd", dict(text=g["end"], color=BLUE), dict(text=description_end, span=4, clip=False)]),
        dict(n="6", cells=[]),
        dict(n="7", cells=title("Billing for the period (PeriodStart to PeriodEnd)")),
        dict(n="8", cells=["Invoices", f"{year['n']:,}"]),
        dict(n="9", cells=["SubTotal", _money(year["sub"])]),
        dict(n="10", cells=["FreightAmount", _money(year["frt"])]),
        dict(n="11", cells=["TaxAmount", _money(year["tax"])]),
        dict(n="12", cells=["GrandTotal", _money(year["gt"])]),
        dict(n="13", cells=["SubTotal + FreightAmount + TaxAmount - GrandTotal", _general(parts_check)]),
        dict(n="14", cells=["Invoices whose parts do not add up (whole Table)", str(broken)]),
        dict(n="15", cells=[]),
        dict(n="16", cells=title("Billing by fiscal year")),
        dict(n="17", cells=head("Fiscal year", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal")),
    ]
    first_year_row = len(sheet_rows)
    for i, r in enumerate(rows):
        sheet_rows.append(dict(n=str(18 + i), cells=[dict(text=str(r["year"]), align="left")] + [_money(r[k]) for k in keys]))
    sheet_rows.append(dict(n="21", cells=money_row("Total", [_money(summed[k]) for k in keys], bold=True)))
    sheet_rows.append(dict(n="22", cells=money_row("Entire SalesInvoice Table", [_money(entire[k]) for k in keys])))
    sheet_rows.append(dict(n="23", cells=money_row("Difference", [_general(difference[k]) for k in keys])))
    geo = _sheet(d, 0, top, letters, widths, sheet_rows)
    # Emphasis: the selected cell E18 and the Difference row.
    e18 = geo[(first_year_row, 4)]
    assert sheet_rows[first_year_row]["n"] == "18"
    xl.select(d, *e18)
    last = len(sheet_rows) - 1
    first_cell, last_cell = geo[(last, 1)], geo[(last, 4)]
    xl.emphasis(d, first_cell[0], first_cell[1], last_cell[0] + last_cell[2] - first_cell[0], first_cell[3])
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Item", "PromotionProgram", "Parameters", "Analysis", "Ex 4.1"], "Ex 4.1")
    d.text(f"<i>Blue font marks the two input cells, named PeriodStart and PeriodEnd. Selected: E18, whose formula shows in the "
           f"bar above; the InvoiceDate column is locked (bold) and SalesInvoice[GrandTotal] is left to shift. Outlined: the "
           f"Difference row, zero in every column. The Invoices column (G) of the optional Step 6c is not shown.</i>", 0,
           bottom + 34, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-04-2-A: the promotion summary of Ex 4.2 ---------------------------------------------------------------------------

def if_04_2_a() -> Diagram:
    """Ex 4.2: one row for each promotion with data bars, the rate test and the lookup of the largest promotion."""
    data = ctx.data()
    g = ctx.values("ch04.g2")
    promos, top = g["promos"], g["top"]
    _columns(data, "PromotionProgram", {"A": "PromotionID", "B": "PromotionCode", "C": "PromotionName", "D": "ScopeType",
                                         "E": "CustomerSegment", "F": "ItemGroup", "G": "CollectionName", "H": "DiscountPct"})
    at_rate = sum(p["other"] for p in promos)
    no_promotion = data.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NULL AND Discount <> 0")
    left_out = data.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL") - g["lines"]
    assert at_rate == no_promotion == left_out == 0, (at_rate, no_promotion, left_out)
    scope = data.q("SELECT ScopeType, ItemGroup, CustomerSegment, CollectionName FROM PromotionProgram WHERE PromotionID = ?",
                   top["id"])[0]
    assert scope[0] == top["scope"]
    assert abs(sum(p["share"] for p in promos) - 1) < 1e-9 and top["discount"] == max(p["discount"] for p in promos)
    d = Diagram("The Ex 4.2 Worksheet: the Promotion Summary, the Rate Test and the Largest Promotion")
    widths = [28, 88, 204, 62, 88, 112, 108, 86, 84]
    letters = ["A", "C", "D", "E", "F", "G", "H", "I"]
    first = 4
    head = [dict(html=f"<b>{h}</b>", fill=BLUE_TINT, align="left" if i < 2 else "right") for i, h in enumerate(
        ["PromotionID", "PromotionName", "Invoice<br>lines", "LineTotal", "DiscountAmount", "Share of<br>discount dollars",
         "DiscountPct", "Lines at<br>another rate"])]
    rows = [dict(n="3", cells=head, h=36)]
    biggest = max(p["discount"] for p in promos)
    for i, p in enumerate(promos):
        rows.append(dict(n=str(first + i), cells=[
            dict(text=str(p["id"])), p["name"], f"{p['lines']:,}", _money(p["total"]),
            dict(text=_money(p["discount"]), bar=p["discount"] / biggest), f"{p['share']:.1%}", f"{p['rate']:.0%}",
            str(p["other"])]))
    last = first + len(promos)
    assert last == 13, "the Total row is row 13 when there are nine promotions"
    rows.append(dict(n=str(last), cells=[dict(text="Total", bold=True), dict(text=""), dict(text=f"{g['lines']:,}", bold=True),
                                         dict(text=_money(g["total"]), bold=True), dict(text=_money(g["discount"]), bold=True),
                                         dict(text=f"{sum(p['share'] for p in promos):.1%}", bold=True),
                                         dict(text=""), dict(text=str(at_rate), bold=True)]))
    rows.append(dict(n=str(last + 1), cells=[]))
    r = last + 2

    def label(text: str, span: int = 3, bold: bool = False) -> dict:
        return dict(text=text, span=span, bold=bold, clip=False)

    # Columns after a span are skipped, so a label over A, C and D leaves E for its value.
    rows.append(dict(n=str(r), cells=[dict(text="Rate consistency test", bold=True, span=7, clip=False)]))
    rows.append(dict(n=str(r + 1), cells=[label("Lines at a rate other than their DiscountPct", 3), dict(text=str(at_rate))]))
    rows.append(dict(n=str(r + 2), cells=[label("Lines with a discount and no PromotionID", 3), dict(text=str(no_promotion))]))
    rows.append(dict(n=str(r + 3), cells=[label("Promotion lines left out of the summary", 3), dict(text=str(left_out))]))
    verdict = ("No promotion was applied at a rate other than its approved rate" if at_rate + no_promotion + left_out == 0
               else "Differences found")
    rows.append(dict(n=str(r + 4), cells=[label("Result", 3), dict(text=verdict, span=5, clip=False, bold=True)]))
    rows.append(dict(n=str(r + 5), cells=[]))
    rows.append(dict(n=str(r + 6), cells=[dict(text="The promotion with the largest share of the discount dollars", bold=True,
                                                span=7, clip=False)]))
    lookups = [("PromotionID", str(top["id"]), "right"), ("PromotionCode", top["code"], "left"),
               ("PromotionName", top["name"], "left"), ("ScopeType", scope[0], "left"), ("ItemGroup", scope[1] or "", "left"),
               ("CustomerSegment", scope[2] or "", "left"), ("CollectionName", scope[3] or "", "left"),
               ("DiscountPct", f"{top['rate']:.0%}", "right"), ("EffectiveStartDate", top["start"], "right"),
               ("EffectiveEndDate", top["end"], "right"), ("Share of the discount dollars", f"{top['share']:.1%}", "right")]
    for k, (name, value, align) in enumerate(lookups):
        rows.append(dict(n=str(r + 7 + k), cells=[label(name, 3), dict(text=value, align=align, span=3 if align == "left" else 1,
                                                                        clip=False)]))
    _formula_bar(d, 0, 0, 860, f"F{first + promos.index(top)}", esc(f"=SUMIFS(SalesInvoiceLine[DiscountAmount],"
                                                                    f"SalesInvoiceLine[PromotionID],$A{first + promos.index(top)})"))
    geo = _sheet(d, 0, 40, letters, widths, rows)
    top_row = promos.index(top) + 1                       # index of the largest promotion's row in the sheet's rows
    f_cell, g_cell = geo[(top_row, 4)], geo[(top_row, 5)]
    xl.emphasis(d, f_cell[0], f_cell[1], g_cell[0] + g_cell[2] - f_cell[0], f_cell[3])
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Parameters", "Analysis", "Ex 4.1", "Ex 4.2"], "Ex 4.2")
    d.text(f"<i>Column B (PromotionCode) is hidden, and rows 1 and 2, which hold the title, are scrolled out of view. The data "
           f"bars in DiscountAmount start at zero and the longest is on promotion {top['id']}, outlined with its share of the "
           f"discount dollars. The test counts are zero, which shows that every line carries its promotion's rate, not that it "
           f"was billed inside the promotion's dates.</i>", 0, bottom + 34, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-04-3-A: the Item worksheet of Ex 4.3 -------------------------------------------------------------------------------

def _scale_cell(v: float, low: float, mid: float, high: float) -> dict:
    """A three-point color scale (lowest value, 50th percentile, highest value) drawn in three palette steps."""
    t = 0.5 * (v - low) / (mid - low) if v <= mid else 0.5 + 0.5 * (v - mid) / (high - mid)
    if t < 1 / 3:
        return dict(fill=GRAY_TINT)
    if t < 2 / 3:
        return dict(fill=TEAL_TINT)
    return dict(fill=TEAL, color=WHITE)


def _swatch(d: Diagram, x: float, y: float, fill: str, size: float = 14) -> None:
    d.box("", x, y, size, size, fill=fill, stroke=GRAY, rounded=False)


def if_04_3_a() -> Diagram:
    """The Item Table of Ex 4.3, filtered to finished goods and sorted, scrolled to the boundary of two groups."""
    data = ctx.data()
    g = ctx.values("ch04.g3")
    letters = g["letters"]
    # The Item Table keeps the eleven columns of Tutorial 4.1, Step 5, so its calculated columns land in L and M.
    kept = [r[1] for r in data.q("PRAGMA table_info(Item)") if r[1] in ITEM_COLUMNS]
    assert kept == ITEM_COLUMNS, kept
    assert [letters[c] for c in ITEM_COLUMNS] == [chr(65 + i) for i in range(len(ITEM_COLUMNS))], letters
    assert letters["UnitMargin"] == "L" and letters["MarginPct"] == "M", letters
    n_columns = len(ITEM_COLUMNS) + 2
    items = data.q("SELECT ItemID, ItemCode, ItemName, ItemGroup, ItemType, StandardCost, ListPrice FROM Item "
                   "WHERE ListPrice IS NOT NULL ORDER BY ItemID")
    assert len(items) == g["n_items"]
    pct = lambda r: (r[6] - r[5]) / r[6]
    goods = [r for r in items if r[4] == "Finished Good"]
    assert len(goods) == g["n_goods"]
    assert all(r[4] != "Finished Good" for r in items[len(goods):]), "the services sit below the finished goods in the Table"
    ordered = sorted(goods, key=lambda r: (r[3], -pct(r)))                 # Excel's sort keeps ties in worksheet order
    target = g["target"]
    upper, lower = "Furniture", "Lighting"
    assert upper in g["groups"] and lower in g["groups"] and g["groups"].index(lower) == g["groups"].index(upper) + 1
    boundary = max(i for i, r in enumerate(ordered) if r[3] == upper)           # the last Furniture row
    before, after = 7, 5
    shown = ordered[boundary - before + 1: boundary + 1 + after]
    assert all(pct(r) < target for r in shown[:before]) and all(pct(r) >= target for r in shown[before:]),         "the figure shows the Furniture items below the target above the Lighting items above it"
    all_pct = [pct(r) for r in items]
    low, mid, high = min(all_pct), xl.percentile_inc(all_pct, 0.5), max(all_pct)
    headers = ["ItemCode", "ItemGroup", "ItemType", "StandardCost", "ListPrice", "UnitMargin", "MarginPct"]
    cells_of = lambda r: [r[1], r[3], r[4], _money(r[5]), _money(r[6]), _money(r[6] - r[5]), f"{pct(r):.1%}"]
    widths = [44] + _fit(headers, [cells_of(r) for r in shown], pad=22, filters=set(range(7)))
    spare = 860 - sum(widths)
    assert spare >= 0, widths
    widths = [w + spare / (len(widths) - 1) if i else w for i, w in enumerate(widths)]       # share the spare room
    d = Diagram("The Item Worksheet After the Calculated Columns, the Filter, the Sort and the Rules of Ex 4.3")
    visible = ["B", "D", "E", "F", "G", "L", "M"]
    body = [dict(n="1", h=24, cells=[_header(h, filter="active" if h == "ItemType" else True) for h in headers])]
    first_row = ordered.index(shown[0]) + 2                       # the sheet row of the first row shown
    for k, r in enumerate(shown):
        below = pct(r) < target
        band = AMBER_TINT if below else (WHITE if (k + 1) % 2 else BLUE_TINT)
        values = cells_of(r)
        row_cells = [dict(text=v, fill=band, align="right" if c in (3, 4, 5) else "left") for c, v in enumerate(values[:6])]
        row_cells.append(dict(text=values[6], align="right", **_scale_cell(pct(r), low, mid, high)))
        body.append(dict(n=str(first_row + k), cells=row_cells, number_color=BLUE))
    y = 0
    # The header, a gap that stands for the rows scrolled out of view, then the rows near the boundary.
    top = _sheet(d, 0, y, visible, widths, body[:1])
    y = top["bottom"]
    y = _gap(d, 0, y, 860, f"rows 2 to {first_row - 1} are scrolled out of view: Accessories, then Furniture from its highest MarginPct")
    rows_geo = _sheet(d, 0, y, [], widths, body[1:], show_letters=False)
    boundary_row = before                                  # index in rows_geo of the first Lighting row
    # A heavier rule at the boundary of the two groups, and the outline of the MarginPct column.
    line_y = rows_geo[(boundary_row, 0)][1]
    d.box("", 0, line_y - 1, 860, 2, fill=GRAY, stroke=GRAY, rounded=False)
    mx, _, mw, _ = rows_geo[(0, 6)]
    xl.emphasis(d, mx, top[(0, 6)][1], mw, rows_geo["bottom"] - top[(0, 6)][1])
    bottom = rows_geo["bottom"] + 6
    xl.status_bar(d, 0, bottom, 860, f"{g['n_goods']} of {g['n_items']} records found")
    ky = bottom + 36
    _swatch(d, 0, ky + 3, AMBER_TINT)
    d.text(f"MarginPct below the target, {target:.1%} (a rule on columns A to L)", 22, ky, 360, 20, size=SMALL, valign="middle")
    for k, fill in enumerate((GRAY_TINT, TEAL_TINT, TEAL)):
        _swatch(d, 400 + k * 18, ky + 3, fill)
    d.text("Color scale on MarginPct, lowest to highest", 462, ky, 398, 20, size=SMALL, valign="middle")
    below_n = sum(r["below"] for r in g["rows"])
    d.text(f"<i>Columns {_hidden_text(visible, n_columns)} are hidden. The Table is filtered to Finished Good and sorted by "
           f"ItemGroup, then MarginPct from largest to smallest, and the window is scrolled to where {upper} ends and {lower} "
           f"begins. {below_n} finished goods are below the target in all: the rule fills columns A to L, so the scale stays "
           f"visible in MarginPct (outlined). The scale is drawn in three steps. Blue row numbers mark a filtered Table.</i>",
           0, ky + 30, 860, 68, size=SMALL, color=GRAY)
    return d


# -- IF-04-4-A: the freight grid of Ex 4.4 --------------------------------------------------------------------------------

def if_04_4_a() -> Diagram:
    """Ex 4.4: the freight grid by FreightTerms with its three check rows, and the slicer beside the SUBTOTAL cells."""
    data = ctx.data()
    g = ctx.values("ch04.g4")
    n = ctx.values("ch04.ex4")
    _columns(data, "Shipment", {"J": "FreightCost", "K": "BillableFreightAmount"})
    assert [g["letters"][c] for c in ("FreightCost", "BillableFreightAmount", "FreightTerms", "FreightMargin")] == list("JKLM")
    terms = g["terms"]
    assert [t["name"] for t in terms] == ["Prepaid", "Prepaid and Add"]
    entire_n = n["shipments"]
    entire = dict(cost=data.one("SELECT ROUND(SUM(FreightCost), 2) FROM Shipment"),
                  billed=data.one("SELECT ROUND(SUM(BillableFreightAmount), 2) FROM Shipment"))
    entire["margin"] = round(entire["billed"] - entire["cost"], 2)
    totals = dict(n=sum(t["n"] for t in terms), **{k: round(sum(t[k] for t in terms), 2) for k in ("cost", "billed", "margin")})
    diff = {k: round(totals[k] - (entire_n if k == "n" else entire[k]), 2) + 0.0 for k in totals}
    assert all(v == 0 for v in diff.values()) and abs(totals["margin"] - g["total"]) < 0.005
    selected = terms[0]
    d = Diagram("The Ex 4.4 Worksheet: the Freight Grid and the FreightTerms Slicer")
    formula = _formula("=SUMIFS(Shipment[BillableFreightAmount],Shipment[", ("b", "[FreightTerms]:[FreightTerms]"), "],$A10)")
    _formula_bar(d, 0, 0, 860, "D10", formula)
    widths = [28, 250, 90, 100, 160, 104, 128]
    letters = list("ABCDEF")
    keys = ["n", "cost", "billed", "margin"]
    fmt = lambda k, v: f"{v:,}" if k == "n" else _money(v)
    head = [dict(text=t, bold=True, fill=BLUE_TINT, align="left" if i == 0 else "right")
            for i, t in enumerate(["FreightTerms", "Shipments", "FreightCost", "BillableFreightAmount", "FreightMargin"])]
    rows = [dict(n="8", cells=[dict(text="Freight by FreightTerms", bold=True, span=5, clip=False)]), dict(n="9", cells=head)]
    for i, t in enumerate(terms):
        rows.append(dict(n=str(10 + i), cells=[dict(text=t["name"])] + [fmt(k, t[k]) for k in keys]))
    rows.append(dict(n="12", cells=[dict(text="Total", bold=True)] + [dict(text=fmt(k, totals[k]), bold=True) for k in keys]))
    rows.append(dict(n="13", cells=["Entire Shipment Table"] + [fmt(k, entire_n if k == "n" else entire[k]) for k in keys]))
    rows.append(dict(n="14", cells=["Difference"] + [_general(diff[k]) for k in keys]))
    geo = _sheet(d, 0, 40, letters, widths, rows)
    xl.select(d, *geo[(2, 3)])                              # D10, the first term's BillableFreightAmount
    first, last = geo[(6, 1)], geo[(6, 4)]
    xl.emphasis(d, first[0], first[1], last[0] + last[2] - first[0], first[3])
    y = _gap(d, 0, geo["bottom"], sum(widths[:6]), "rows 15 to 25 hold the counts of shipments billed above and below their cost; not shown")
    lower = [dict(n="26", cells=[dict(text="The slicer on FreightTerms (click a term; SUBTOTAL follows the rows in view)", bold=True,
                                       span=5, clip=False)]),
             dict(n="27", cells=["Shipments in view", f"{selected['n']:,}"]),
             dict(n="28", cells=["Average FreightCost in view", _money(selected["avg_cost"])])]
    geo2 = _sheet(d, 0, y, [], widths, lower, show_letters=False)
    cell = geo2[(1, 1)]
    xl.emphasis(d, cell[0], cell[1], cell[2], 44)
    slicer_w = 124
    slicer_h = _slicer(d, 860 - slicer_w - 4, y + 4, slicer_w, "FreightTerms", [t["name"] for t in terms], selected["name"])
    bottom = max(geo2["bottom"], y + 4 + slicer_h) + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 4.3", "Ex 4.4", "Ex 4.4 Shipment", "Ex 4.4 SalesOrder"], "Ex 4.4")
    d.text(f"<i>Selected: D10, whose formula locks the FreightTerms column (bold) and leaves the sum column to be changed by hand: "
           f"FreightMargin (column M) does not follow BillableFreightAmount (column K), because FreightTerms, a text column, "
           f"sits between them, so a fill across fails in one column. Outlined: the Difference row, zero in every column, and the two SUBTOTAL cells. The "
           f"slicer is on the Shipment Table, with {selected['name']} selected.</i>", 0, bottom + 34, 860, 52, size=SMALL,
           color=GRAY)
    return d


# -- IF-04-5-A: the shipment exception report of Ex 4.5 ----------------------------------------------------------------------

def if_04_5_a() -> Diagram:
    """Ex 4.5: the top of the Shipment Table with its two rules, beside the Analysis worksheet with the Status slicer."""
    data = ctx.data()
    g = ctx.values("ch04.g5")
    n = ctx.values("ch04.ex5")
    _columns(data, "Shipment", {"A": "ShipmentID", "D": "ShipmentDate", "G": "TrackingNumber", "H": "Status", "I": "DeliveryDate"})
    assert g["letters"]["TrackingNumber"] == "G" and g["letters"]["Status"] == "H" and g["letters"]["DeliveryDate"] == "I"
    first, last, total = data.q("SELECT MIN(ShipmentID), MAX(ShipmentID), COUNT(*) FROM Shipment")[0]
    assert (first, last) == (1, total), "row numbers assume ShipmentID 1..n in worksheet order"
    review = n["review"]
    found = data.q("SELECT ShipmentID, TrackingNumber, Status, DeliveryDate FROM Shipment WHERE Status = 'In Transit' "
                   "ORDER BY ShipmentID LIMIT 14")
    assert any(not r[1] for r in found), "the top of the filtered Table shows a row with no tracking number"
    in_both = [r for r in found if not r[1] and r[3] < review]
    assert in_both, "the top rows hold a shipment in both categories"
    d = Diagram("The Shipment Table and the Analysis Worksheet of Ex 4.5, with the Status Slicer on In Transit")
    left_w, gap, right_w = 450, 16, 394
    # Left pane: the Shipment worksheet.
    xl.title_bar(d, 0, 0, left_w, "Shipment worksheet")
    headers = ["ShipmentID", "TrackingNumber", "Status", "DeliveryDate"]
    cells_of = lambda r: [str(r[0]), r[1] or "", r[2], r[3]]
    widths = [30] + _fit(headers, [cells_of(r) for r in found], pad=16, filters=set(range(4)))
    spare = left_w - sum(widths)
    assert spare >= 0, widths
    widths = [w + spare / 4 if i else w for i, w in enumerate(widths)]
    body = [dict(n="1", h=24, cells=[_header(h, filter="active" if h == "Status" else True) for h in headers])]
    for r in found:
        blank, late = not r[1], r[3] < review
        fill = HIGHLIGHT if blank else CORAL_TINT if late else WHITE
        body.append(dict(n=str(r[0] + 1), number_color=BLUE, cells=[dict(text=v, fill=fill, align="left") for v in cells_of(r)]))
    geo = _sheet(d, 0, 34, ["A", "G", "H", "I"], widths, body)
    left_bottom = geo["bottom"] + 6
    xl.status_bar(d, 0, left_bottom, left_w, f"{n['transit']} of {n['shipments']} records found")
    ky = left_bottom + 36
    d.box("", 0, ky + 3, 14, 14, fill=HIGHLIGHT, stroke=GRAY, rounded=False)
    d.text("Amber rule: the TrackingNumber is blank", 22, ky, left_w - 22, 20, size=SMALL, valign="middle")
    d.box("", 0, ky + 27, 14, 14, fill=CORAL_TINT, stroke=GRAY, rounded=False)
    d.text("Coral rule: In Transit, and a DeliveryDate before ReviewDate", 22, ky + 24, left_w - 22, 20, size=SMALL, valign="middle")
    both_row = in_both[0][0] + 1
    callout_bottom = kit.callout(d, f"Row {both_row} meets both rules and shows amber, the rule listed first in Manage Rules, so the "
                                    f"colors cannot count the shipments in both categories. COUNTIFS does. The Status filter is set "
                                    f"to In Transit by the slicer.", 0, ky + 54, left_w, color="gray")
    # Right pane: the Analysis worksheet.
    rx = left_w + gap
    xl.title_bar(d, rx, 0, right_w, "Analysis worksheet")
    rw = [28, 196, 76, 94]
    by_year = n["transit_by_year"]
    blank_total = n["blank_delivered"] + n["blank_transit"]
    assert blank_total == n["blank"] and sum(v for _, v in by_year) == n["transit"]
    head2 = lambda text: [dict(text=text, bold=True, fill=BLUE_TINT), dict(text="Shipments", bold=True, fill=BLUE_TINT, align="right")]
    rows = [dict(n="3", cells=["Shipments", f"{n['shipments']:,}"]),
            dict(n="4", cells=["ReviewDate", review]),                  # =ReviewDate, a formula, so black
            dict(n="5", cells=[]),
            dict(n="6", cells=head2("Exception category")),
            dict(n="7", cells=["Blank TrackingNumber (amber)", f"{n['blank']:,}"]),
            dict(n="8", h=38, cells=[dict(html="In Transit with a DeliveryDate<br>before ReviewDate (coral)", align="left"),
                                      dict(text=f"{n['late']:,}")]),
            dict(n="9", cells=["In both categories", f"{n['blank_transit']:,}"]),
            dict(n="10", cells=[]),
            dict(n="11", h=38, cells=[dict(html="<b>Blank TrackingNumber<br>by Status</b>", fill=BLUE_TINT, align="left"),
                                       dict(text="Shipments", bold=True, fill=BLUE_TINT, align="right")]),
            dict(n="12", cells=["Delivered", f"{n['blank_delivered']:,}"]),
            dict(n="13", cells=["In Transit", f"{n['blank_transit']:,}"]),
            dict(n="14", cells=[dict(text="Total", bold=True), dict(text=f"{blank_total:,}", bold=True)]),
            dict(n="15", cells=[]),
            dict(n="16", cells=head2("In Transit by year shipped"))]
    for k, (year, count) in enumerate(by_year):
        rows.append(dict(n=str(17 + k), cells=[dict(text=str(year), align="left"), f"{count:,}"]))
    rows.append(dict(n=str(17 + len(by_year)), cells=[dict(text="Total In Transit", bold=True),
                                                       dict(text=f"{n['transit']:,}", bold=True)]))
    assert 17 + len(by_year) == 20
    rgeo = _sheet(d, rx, 34, ["A", "B", "C"], rw, rows)
    y = _gap(d, rx, rgeo["bottom"], right_w, "rows 21 to 23 are not shown")
    in_view = n["transit"]
    lower = [dict(n="24", cells=[dict(text="Status slicer (SUBTOTAL follows it)", bold=True, span=2, clip=False)]),
             dict(n="25", cells=["Shipments in view", f"{in_view:,}"]),
             dict(n="26", cells=["With a TrackingNumber, in view", f"{in_view - n['blank_transit']:,}"]),
             dict(n="27", cells=["Blank TrackingNumber, in view", f"{n['blank_transit']:,}"])]
    lgeo = _sheet(d, rx, y, [], rw, lower, show_letters=False)
    slicer_x = rx + sum(rw[:3]) + 8
    slicer_y = lgeo[(1, 0)][1] - 2
    slicer_h = _slicer(d, slicer_x, slicer_y, right_w - sum(rw[:3]) - 8, "Status", ["Delivered", "In Transit"], "In Transit")
    # The three exception counts and the SUBTOTAL cells that confirm them.
    c1, c3 = rgeo[(4, 1)], rgeo[(6, 1)]
    xl.emphasis(d, c1[0], c1[1], c1[2], c3[1] + c3[3] - c1[1])
    s1, s3 = lgeo[(1, 1)], lgeo[(3, 1)]
    xl.emphasis(d, s1[0], s1[1], s1[2], s3[1] + s3[3] - s1[1])
    right_bottom = max(lgeo["bottom"], slicer_y + slicer_h) + 8
    bottom = max(right_bottom + 34, callout_bottom + 8)
    xl.sheet_tabs(d, rx, right_bottom, ["Parameters", "Analysis", "Shipment"], "Analysis", max_right=860)
    xl.sheet_tabs(d, 0, right_bottom, ["Parameters", "Analysis", "Shipment"], "Shipment", max_right=left_w)
    d.text(f"<i>Two views of one workbook, side by side. Left: columns B to F and J to K of the Shipment Table are hidden, "
           f"and the first {len(found)} In Transit shipments are shown. Right: rows 1 and 2 are scrolled out of view. The review "
           f"date is {review}, the year-end under review and the last shipment date. Outlined: the three exception counts, and the SUBTOTAL cells, which "
           f"agree with the counts for the status selected.</i>", 0, bottom, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-04-6-A: the requester grid of Ex 4.6 ------------------------------------------------------------------------------------

def if_04_6_a() -> Diagram:
    """Ex 4.6: the counts, the Status slicer beside its SUBTOTAL cells, and the grid of requests by requester."""
    data = ctx.data()
    g = ctx.values("ch04.g6")
    n = ctx.values("ch04.ex6")
    _columns(data, "PriceOverrideApproval", {"E": "RequestedByEmployeeID", "F": "ApprovedByEmployeeID", "M": "Status"})
    grid, own = g["grid"], g["own_row"]
    approver = n["approver"]
    assert own["id"] == approver["id"] and own["own"] == n["self_approved"]
    assert sum(r["n"] for r in grid) == n["requests"] and len({r[0] for r in data.q(
        "SELECT ApprovedByEmployeeID FROM PriceOverrideApproval WHERE ApprovedByEmployeeID IS NOT NULL")}) == 1
    distinct = data.one("SELECT COUNT(DISTINCT ApprovedByEmployeeID) FROM PriceOverrideApproval")
    pending_with = data.one("SELECT COUNT(ApprovedByEmployeeID) FROM PriceOverrideApproval WHERE Status = 'Pending'")
    approved_with = data.one("SELECT COUNT(ApprovedByEmployeeID) FROM PriceOverrideApproval WHERE Status = 'Approved'")
    assert pending_with == 0 and approved_with == n["approved"]
    d = Diagram("The Ex 4.6 Worksheet: the Counts, the Status Slicer and the Grid by Requester")
    widths = [28, 180, 122, 154, 76, 104, 110, 86]
    assert sum(widths) <= 860
    letters = list("ABCDEFG")
    rows = [dict(n="3", cells=["Requests", f"{n['requests']:,}"]),
            dict(n="4", cells=["Blank approver", f"{g['blank']:,}"]),
            dict(n="5", cells=["Approved by the requester", f"{n['self_approved']:,}"]),
            dict(n="6", cells=["Distinct approvers", f"{distinct:,}"]),
            dict(n="7", cells=["Approver (EmployeeID)", str(approver["id"])])]
    geo = _sheet(d, 0, 0, letters, widths, rows)
    y = _gap(d, 0, geo["bottom"], sum(widths), "rows 8 to 13 hold the counts by Status; not shown")
    pending = n["pending"]
    lower = [dict(n="14", cells=[dict(text="The slicer on Status (click a status; SUBTOTAL follows the rows in view)", bold=True,
                                       span=6, clip=False)]),
             dict(n="15", cells=["Requests in view", f"{pending:,}"]),
             dict(n="16", cells=["With an approver, in view", f"{pending_with:,}"]),
             dict(n="17", cells=[]),
             dict(n="18", cells=[dict(text="Recorded with the slicer", bold=True, fill=BLUE_TINT),
                                  dict(text="Requests in view", bold=True, fill=BLUE_TINT, align="right"),
                                  dict(text="With an approver", bold=True, fill=BLUE_TINT, align="right")]),
             dict(n="19", cells=["Approved", f"{n['approved']:,}", f"{approved_with:,}"]),
             dict(n="20", cells=["Pending", f"{pending:,}", f"{pending_with:,}"]),
             dict(n="21", cells=[])]
    geo2 = _sheet(d, 0, y, [], widths, lower, show_letters=False)
    slicer_x = sum(widths[:4]) + 14
    slicer_y = geo2[(1, 0)][1] + 2
    slicer_h = _slicer(d, slicer_x, slicer_y, 140, "Status", ["Approved", "Pending"], "Pending")
    cells = geo2[(1, 1)]
    xl.emphasis(d, cells[0], cells[1], cells[2], 44)
    # The grid by requesting employee.
    heads = ["RequestedByEmployeeID", "EmployeeName", "JobTitle", "Requests", "Approved by<br>someone else",
             "Approved by<br>the requester", "Pending"]
    head_row = [dict(html=f"<b>{h}</b>", fill=BLUE_TINT, align="left" if i < 3 else "right") for i, h in enumerate(heads)]
    grid_rows = [dict(n="22", cells=[dict(text="Requests by requesting employee", bold=True, span=6, clip=False)]),
                 dict(n="23", h=38, cells=head_row)]
    for i, r in enumerate(grid):
        grid_rows.append(dict(n=str(24 + i), cells=[dict(text=str(r["id"]), align="left"), r["name"], r["title"], f"{r['n']:,}",
                                                    f"{r['other']:,}", f"{r['own']:,}", f"{r['open']:,}"]))
    sums = {k: sum(r[k] for r in grid) for k in ("n", "other", "own", "open")}
    assert sums["n"] == n["requests"] and sums["open"] == n["pending"] and sums["own"] == n["self_approved"]
    grid_rows.append(dict(n=str(24 + len(grid)), cells=[dict(text="Total", bold=True), "", "",
                                                       *[dict(text=f"{sums[k]:,}", bold=True) for k in ("n", "other", "own", "open")]]))
    y2 = max(geo2["bottom"], slicer_y + slicer_h + 4)
    geo3 = _sheet(d, 0, y2, [], widths, grid_rows, show_letters=False)
    # The requester who is also the approver: the row, and the cell of the approvals by the requester.
    i = 2 + [r["id"] for r in grid].index(own["id"])
    row_first, row_last = geo3[(i, 0)], geo3[(i, 6)]
    xl.emphasis(d, row_first[0], row_first[1], row_last[0] + row_last[2] - row_first[0], row_first[3])
    xl.select(d, *geo3[(i, 5)])
    bottom = geo3["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["PriceOverrideApproval", "Employee", "Ex 4.6"], "Ex 4.6")
    d.text(f"<i>Rows 1 and 2, and rows 8 to 13, which hold the counts by Status, are not shown. With Pending selected the slicer leaves "
           f"{pending} requests in view and none has an approver. Outlined: the request count and approver count in view, and "
           f"the row of the {approver['title']} (EmployeeID {approver['id']}), who is also the only approver: "
           f"{own['own']} of {own['n']} requests were approved by the requester (selected cell), and {own['open']} are Pending.</i>",
           0, bottom + 34, 860, 52, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "IF-04-0-A": if_04_0_a,
    "IF-04-0-B": if_04_0_b,
    "IF-04-1-A": if_04_1_a,
    "IF-04-2-A": if_04_2_a,
    "IF-04-3-A": if_04_3_a,
    "IF-04-4-A": if_04_4_a,
    "IF-04-5-A": if_04_5_a,
    "IF-04-6-A": if_04_6_a,
}
