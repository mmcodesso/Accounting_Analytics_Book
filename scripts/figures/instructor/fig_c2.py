"""Instructor figures of the Part II case (guides in facts/instructor/guides/case-part-2/)."""

from __future__ import annotations

import calendar
import re
from datetime import date

import ctx
import excel as xl
import kit
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, BODY, CORAL, CORAL_TINT, FONT, GRAY, GRAY_TINT, HEAD, INK, RULE,
                    SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

CASE = ctx.REPO / "cases" / "part-2-case.qmd"
GUIDES = ctx.REPO / "facts" / "instructor" / "guides" / "case-part-2"
MEMO_GUIDE = GUIDES / "req-6-write-the-decision-memo.md"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
               "December"]
MINUS = "−"
STRAIGHT = "edgeStyle=none;"
DASHED_CORAL = "rounded=0;html=1;fillColor=none;strokeColor=%s;strokeWidth=2;dashed=1;dashPattern=6 3;" % CORAL


# -- shared drawing helpers (Excel pieces copied from fig_08) -------------------------------------------------------------------

def _money(x: float) -> str:
    return f"{xl.xround(x, 2):,.2f}"


def _signed(x: float, places: int = 1) -> str:
    """A signed percentage with a true minus sign."""
    return (MINUS if x < 0 else "+") + f"{abs(x) * 100:.{places}f}%"


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow worksheet column shows it."""
    if text_width(text, size, bold) <= width - margin:
        return text
    while text and text_width(text + "…", size, bold) > width - margin:
        text = text[:-1]
    return text + "…"


def _wrap(text: str, width: float, size: int = SMALL, bold: bool = False) -> list[str]:
    """A greedy word wrap measured with text_width."""
    out, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if not cur or text_width(trial, size, bold) <= width:
            cur = trial
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    return out


def _wrapped(text: str, width: float, bold: bool = False, **kw) -> dict:
    """A cell that wraps its text over as many lines as the column needs (the cell's lines are kept in "lines")."""
    lines = _wrap(text, width - 16, bold=bold)
    html = "<br>".join(esc(line) for line in lines)
    return dict(html=f"<b>{html}</b>" if bold else html, lines=len(lines), **kw)


def _dropdown(d: Diagram, geo: tuple, fill: str = GRAY) -> None:
    """The filter button of a PivotTable field or a Table header: a small triangle."""
    hx, hy, hw, hh = geo
    d.vertex("", f"triangle;direction=south;html=1;fillColor={fill};strokeColor=none;", hx + hw - 16, hy + hh / 2 - 3.5, 9, 7)


def _gap(d: Diagram, x: float, y: float, w: float, text: str, h: float = 24) -> float:
    """A band that stands for the rows of a worksheet that the figure leaves out."""
    d.box(f"<i>{esc(text)}</i>", x, y, w, h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, rounded=False, dashed=True)
    return y + h


def _sheet(d: Diagram, x: float, y: float, letters: list[str], widths: list[float], rows: list[dict],
           number_color: str = GRAY, show_letters: bool = True, row_h: float = 22) -> dict:
    """A worksheet with a letter row and rows of any height.

    widths[0] is the row-number column; letters label the others.  A row is {"n": row number, "cells": [cell, ...],
    "h": height}, its cells taken in order from the first column (a cell with span uses that many columns); a cell is a
    string or a dict: text, bold, italic, align ("left", "right", "center"), color, fill, stroke, html (a ready label),
    span (columns the text overflows across), clip (False keeps a long text whole), valign, filter (True draws the filter
    button).  A cell made by _wrapped() sets the row's height when the row has no "h".  Returns
    {(row index, column): (x, y, w, h)} and "bottom"."""
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
        lines = max([c.get("lines", 1) for c in row["cells"] if isinstance(c, dict)] or [1])
        h = row.get("h", max(row_h, lines * 15 + 8))
        d.box(esc(row["n"]), xs[0], ry, widths[0], h, fill=GRAY_TINT, stroke=RULE, color=row.get("number_color", number_color),
              size=SMALL, rounded=False)
        cells = list(row["cells"])
        c = idx = 0
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
            d.box(label, cx, ry, cw, h, fill=cell.get("fill", WHITE), stroke=cell.get("stroke", RULE), color=cell.get("color", INK),
                  size=SMALL, rounded=False, align=align, valign=cell.get("valign", "middle"))
            geo[(i, c)] = (cx, ry, cw, h)
            if cell.get("filter"):
                _dropdown(d, geo[(i, c)])
            c += span
        ry += h
    geo["bottom"] = ry
    return geo


def _hd(text: str, align: str = "left", **kw) -> dict:
    """A heading cell of a plain range: light blue, bold."""
    return dict(html=f"<b>{esc(text)}</b>", fill=BLUE_TINT, align=align, **kw)


def _mark(d: Diagram, x: float, y: float, w: float, h: float, color: str = CORAL, inset: float = 0) -> str:
    """An outline like xl.emphasis in a chosen color; inset pulls it inward so two outlines on adjacent cells do not touch."""
    left, top = max(0, x - 2 + inset), max(0, y - 2 + inset)
    return d.outline(left, top, min(860, x + w + 2 - inset) - left, y + h + 2 - inset - top, color, width=2.5, front=True)


def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def _swatch(d: Diagram, x: float, y: float, fill: str, stroke: str | None = None, size: float = 14) -> None:
    d.box("", x, y, size, size, fill=fill, stroke=stroke or fill, rounded=False)


def _label(d: Diagram, text: str, cx: float, y: float, bold: bool = True, color: str = INK) -> None:
    """A white-backed text label centered on cx, so a gridline does not strike through it."""
    shown = f"<b>{text}</b>" if bold else text
    lw = text_width(shown, SMALL, False) + 8
    d.box(shown, cx - lw / 2, y, lw, 18, fill=WHITE, stroke=WHITE, color=color, size=SMALL, rounded=False)


def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str = BLUE, width: float = 3, dashed: bool = False) -> None:
    """One edge through the points, drawn straight between them (separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, dashed=dashed, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _formula_bar(d: Diagram, x: float, y: float, w: float, name: str, formula_html: str, h: float = 28) -> None:
    """The Name Box, the fx label and a formula bar."""
    d.box(esc(name), x, y, 90, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<i>fx</i>", x + 94, y, 30, 28, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(formula_html, x + 128, y, w - 128, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)


def _words(n: int) -> str:
    return ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][n] if 0 <= n <= 10 else str(n)


def _month_name(iso: str) -> str:
    return MONTH_NAMES[int(iso[5:7]) - 1]


def _day_x(iso: str, x0: float, mw: float) -> float:
    """The x of a date on a twelve-month strip whose months are mw wide, within its month by the day."""
    y, m, dd = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
    return x0 + (m - 1) * mw + (dd - 1) / calendar.monthrange(y, m)[1] * mw


# -- what the case text says ------------------------------------------------------------------------------------------------------

def _requirements() -> list[dict]:
    """Each requirement of the case text: number, title, the chapter tag ('Chapters 4 and 5', or None) and the perspective."""
    found = []
    for m in re.finditer(r"^\*\*Requirement (\d+): ([^*]+?)\.\*\*", CASE.read_text(encoding="utf-8"), re.M):
        title, tag, persp = m.group(2), None, None
        parts = re.fullmatch(r"(.+?) \(([^)]*)\)", title)
        if parts:
            title = parts.group(1)
            bits = [b.strip() for b in parts.group(2).split(";")]
            tag = bits[0] if bits[0].startswith("Chapter") else None
            persp = bits[1] if len(bits) > 1 else None
        found.append(dict(n=int(m.group(1)), title=title, tag=tag, perspective=persp))
    assert [r["n"] for r in found] == list(range(1, len(found) + 1)), found
    return found


def _memo_sections() -> list[str]:
    """The three headed sections of the memo, as Requirement 6 names them, and the exhibits of the Deliverable."""
    text = CASE.read_text(encoding="utf-8")
    block = text[text.index("**Requirement 6"):text.index("**Deliverable")]
    return re.findall(r"^- \*\*([A-Z][A-Za-z ]+):\*\*", block, re.M)


def _exhibits() -> list[str]:
    text = CASE.read_text(encoding="utf-8")
    m = re.search(r"appendix of exhibits: (.+?)\.", text)
    items = re.split(r", (?:and )?", m.group(1))
    return [re.sub(r"^(?:and )?the ", "", i).strip() for i in items]


# -- IF-C2-0-A: how the six requirements build the memo -----------------------------------------------------------------------------

def if_c2_0_a() -> Diagram:
    """The requirements with their chapters, the workbook feeding all, the memo's sections and the five exhibits."""
    reqs = _requirements()
    sections = _memo_sections()
    exhibits = _exhibits()
    assert len(reqs) == 6 and len(sections) == 3 and len(exhibits) == 5, (len(reqs), sections, exhibits)
    by_persp = {s.lower(): s for s in sections}
    assert all(reqs[k]["perspective"] in by_persp for k in (1, 2, 3, 4)), reqs
    d = Diagram("How the Six Requirements Build the Memo and Its Appendix")
    W, GAP, TOP, H = 130.0, 16.0, 52.0, 118.0
    xs = [i * (W + GAP) for i in range(6)]
    cx = [x + W / 2 for x in xs]
    d.text("<b>Requirement 1's workbook feeds every other requirement</b>", 150, 0, 560, 20, size=SMALL, align="center")
    req_ids = []
    for i, r in enumerate(reqs):
        tag = r["tag"] or "no chapter tag"
        text = f"<b>Requirement {r['n']}</b><br>{esc(r['title'])}<br><i>{esc(tag)}</i>"
        assert kit.height_for(text, W, SMALL) <= H, (r, kit.height_for(text, W, SMALL))
        req_ids.append(d.box(text, xs[i], TOP, W, H, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL))
    # The bus: Requirement 1 into every other box.
    bus_y = 30.0
    bus = [d.anchor(x, bus_y) for x in cx]
    d.edge(req_ids[0], bus[0], color=GRAY, width=1.5, exit=(0.5, 0), meta=STRAIGHT)
    for a, b in zip(bus, bus[1:]):
        d.edge(a, b, color=GRAY, width=1.5, meta=STRAIGHT)
    for k in range(1, 6):
        d.arrow(bus[k], req_ids[k], entry=(0.5, 0), meta=STRAIGHT)
    # The memo: its frame, the three sections and the opening with the recommendation.
    fx, fy, fw, fh = xs[1] - 22, TOP + H + 66, 860 - xs[1] + 22, 130.0
    frame = d.box("", fx, fy, fw, fh, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5, rounded=False)
    d.text("<b>The memo</b> (Requirement 6): three sections, at most two pages", fx + 10, fy + fh - 26, fw - 20, 22, size=SMALL)
    sy, sh = fy + 16, 78.0
    targets = {}
    spans = {sections[0]: (1, 1), sections[1]: (2, 3), sections[2]: (4, 4)}
    for name, (a, b) in spans.items():
        sx, sw = xs[a], xs[b] + W - xs[a]
        feeders = [r["n"] for r in reqs[1:5] if by_persp[r["perspective"]] == name]
        who = " and ".join(str(n) for n in feeders)
        targets[name] = (d.box(f"<b>{esc(name)}</b><br><i>from Requirement{'s' if len(feeders) > 1 else ''} {who}</i>", sx, sy, sw,
                               sh, fill=WHITE, stroke=BLUE, stroke_width=1.5), sx, sw)
    ox, ow = xs[5], W - 10
    opening = d.box("<b>Opening and recommendation</b><br><i>written in Requirement 6</i>", ox, sy, ow, sh, fill=WHITE, stroke=BLUE,
                    stroke_width=1.5, size=SMALL)
    for r in reqs[1:5]:
        tid, sx, sw = targets[by_persp[r["perspective"]]]
        d.arrow(req_ids[r["n"] - 1], tid, exit=(0.5, 1), entry=((cx[r["n"] - 1] - sx) / sw, 0), meta=STRAIGHT)
    d.arrow(req_ids[5], opening, exit=(0.5, 1), entry=((cx[5] - ox) / ow, 0), meta=STRAIGHT)
    # Requirement 1 also goes with the memo.
    d.arrow(req_ids[0], frame, exit=(0.5, 1), entry=(0, 0.35), meta="edgeStyle=orthogonalEdgeStyle;")
    d.text("the workbook is submitted with the memo", 0, fy + fh / 2 + 18, 118, 52, size=SMALL, color=GRAY)
    # The appendix and its five exhibits.
    ay = fy + fh + 40
    gap_x, ew = 12.0, (860 - 12.0 * 4) / 5
    d.box("", 0, ay, 860, 128, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False, dashed=True)
    d.text("<b>The one-page appendix</b> (Requirement 6): five numbered exhibits, each made in an earlier requirement", 10, ay + 4, 800,
           22, size=SMALL)
    maker = _exhibit_makers()
    assert len(maker) == 5, maker
    for k, name in enumerate(exhibits):
        ex = k * (ew + gap_x)
        label = name[0].upper() + name[1:]
        d.box(f"<b>Exhibit {k + 1}</b><br>{esc(label)}", ex + 6, ay + 30, ew - 12, 56, fill=TEAL_TINT, stroke=TEAL,
              stroke_width=1.5, size=SMALL)
        d.box(f"<b>from Requirement {maker[k]}</b>", ex + 6, ay + 94, ew - 12, 24, fill=BLUE_TINT, stroke=BLUE, size=SMALL)
    app = d.container(0, ay, 860, 128)
    d.arrow(app, frame, exit=(0.5, 0), entry=((430 - fx) / fw, 1), meta=STRAIGHT)
    d.text("each exhibit is cited in the memo", 442, fy + fh + 8, 260, 22, size=SMALL, valign="middle")
    d.text("<i>Requirements 2 to 5 each supply the section named in their perspective; the arrows into a section show which "
           "requirements it draws on. Requirement 6 writes the opening and the recommendation and assembles the appendix. "
           "Requirement 2 makes Exhibits 1 and 2, Requirement 3 Exhibit 3, Requirement 4 Exhibit 4 and Requirement 5 Exhibit 5.</i>",
           0, ay + 138, 860, 50, size=SMALL, color=GRAY)
    return d


# -- IF-C2-0-B: the two dates of a promotion ---------------------------------------------------------------------------------------

def if_c2_0_b() -> Diagram:
    """The proposed promotions' order months and invoice months on a twelve-month strip, with the discount billed by quarter."""
    data = ctx.data()
    g = ctx.values("case2.chapter")
    g2 = ctx.values("case2.g2")
    year = g["report_year"]
    promos = {p["id"]: p for p in g["promos"]}
    prop = g["proposal"]
    assert len(prop) == 3
    ordered, invoiced = {}, {}
    for p in prop:
        ordered[p["id"]] = sorted({int(m) for (m,) in data.q(
            "SELECT DISTINCT substr(o.OrderDate, 6, 2) FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
            "WHERE l.PromotionID = ? AND substr(o.OrderDate, 1, 4) = ?", p["id"], str(year))})
        invoiced[p["id"]] = sorted({int(m) for (m,) in data.q(
            "SELECT DISTINCT substr(i.InvoiceDate, 6, 2) FROM SalesInvoiceLine l JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID "
            "WHERE l.PromotionID = ? AND substr(i.InvoiceDate, 1, 4) = ?", p["id"], str(year))})
        total_lines = data.one("SELECT COUNT(*) FROM SalesOrderLine WHERE PromotionID = ?", p["id"])
        in_year = data.one("SELECT COUNT(*) FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID "
                           "WHERE l.PromotionID = ? AND substr(o.OrderDate, 1, 4) = ?", p["id"], str(year))
        assert total_lines == in_year == promos[p["id"]]["lines"], "every line was ordered in the report year"
        assert min(invoiced[p["id"]]) >= min(ordered[p["id"]]), "invoices follow the orders"
    quarters = [sum(r["q"][k] for r in g2["quarter_rows"]) for k in range(4)]
    total = sum(quarters)
    assert quarters[3] == max(quarters), "the fourth quarter is the tallest"
    failing = next(p for p in prop if promos[p["id"]]["kind"] == "collection")
    fp = promos[failing["id"]]
    assert fp["end"] < fp["start"], "the collection promotion's recorded end date falls before its start"

    d = Diagram("The Two Dates of a Promotion")
    x0, mw = 192.0, 55.5
    right = x0 + 12 * mw
    hy = 0.0
    for m in range(12):
        d.box(f"<b>{MONTHS[m]}</b>", x0 + m * mw, hy, mw, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False)
    d.text(f"<b>{year}</b>", 0, hy, 186, 24, size=SMALL, valign="middle")
    ry0, rh, rgap = 30.0, 38.0, 8.0
    rows_bottom = ry0 + 3 * (rh + rgap) - rgap
    chart_top, base_y, max_h = rows_bottom + 56, rows_bottom + 56 + 190, 150.0
    for m in range(13):                                                   # month lines, heavier at the quarters
        q = m % 3 == 0
        d.box("", x0 + m * mw - (0.75 if q else 0.5), ry0 - 4, 1.5 if q else 1, rows_bottom + 4 - (ry0 - 4), fill=GRAY if q else RULE,
              stroke=GRAY if q else RULE, rounded=False)
    for k, p in enumerate(prop):
        info = promos[p["id"]]
        y = ry0 + k * (rh + rgap)
        d.box(f"<b>{esc(info['label'])} {info['kind']}</b><br>{info['rate'] * 100:.0f}% off", 0, y, 186, rh, fill=WHITE, stroke=RULE,
              size=SMALL, align="left", rounded=False)
        for m in invoiced[p["id"]]:
            d.box("", x0 + (m - 1) * mw + 2, y, mw - 4, rh, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, rounded=False)
        for m in ordered[p["id"]]:
            d.box("", x0 + (m - 1) * mw + 2, y, mw - 4, rh, fill=BLUE, stroke=BLUE, rounded=False)
    # The recorded end date of the collection promotion, which falls before its own start.
    fy_row = ry0 + [p["id"] for p in prop].index(failing["id"]) * (rh + rgap)
    ex = _day_x(fp["end"], x0, mw)
    d.vertex("", DASHED_CORAL, ex - 1, 0, 2, fy_row + rh)
    d.box(f"<b>Recorded end</b><br>{fp['end']}", ex - 106, fy_row + 2, 100, rh - 4, fill=WHITE, stroke=CORAL, stroke_width=1.5, size=SMALL,
          rounded=False)
    # The discount billed in each quarter, aligned to the months above.
    d.text(f"<b>Discount billed in each quarter</b>, the three promotions together: ${total:,.2f} in all", 0, chart_top - 30, 860, 22,
           size=SMALL)
    scale = max_h / max(quarters)
    d.box("", x0, base_y, 12 * mw, 2, fill=INK, stroke=INK, rounded=False)
    for k, v in enumerate(quarters):
        bx, bw = x0 + k * 3 * mw + 28, 3 * mw - 56
        h = max(v * scale, 2)
        d.box("", bx, base_y - h, bw, h, fill=CORAL if k == 3 else GRAY, stroke=CORAL if k == 3 else GRAY, rounded=False)
        d.box(f"<b>${v:,.0f}</b><br>{v / total:.0%}", bx - 6, base_y - h - 36, bw + 12, 34, fill=WHITE, stroke=WHITE, size=SMALL,
              rounded=False)
        d.text(f"<b>Q{k + 1}</b>", bx, base_y + 4, bw, 18, size=SMALL, align="center", color=GRAY)
    d.text(f"<b>By invoice date,</b> {quarters[3] / total:.0%} of the proposal's discount reaches Q4. "
           f"<b>By order date</b> the same discount puts {g2['q4_ordered']:.0%} there.", 0, chart_top - 4, 186, 140, size=SMALL)
    ly = base_y + 32
    cx = 0.0
    for fill, stroke, label in ((BLUE, BLUE, "Months in which its lines were ordered"),
                                (BLUE_TINT, BLUE, "Months in which they were invoiced")):
        _swatch(d, cx, ly + 3, fill, stroke)
        w = text_width(label, SMALL, False) + 8
        d.text(label, cx + 20, ly, w, 20, size=SMALL, valign="middle")
        cx += 20 + w + 22
    d.line_sample(cx, ly + 10, 28, color=CORAL, dashed=True, width=2)
    d.text("Recorded end date", cx + 34, ly, 130, 20, size=SMALL, valign="middle")
    days = (date.fromisoformat(fp["start"]) - date.fromisoformat(fp["end"])).days
    names = lambda ms: " and ".join(MONTH_NAMES[m - 1] for m in ms) if len(ms) <= 2 else f"{MONTH_NAMES[ms[0] - 1]} to {MONTH_NAMES[ms[-1] - 1]}"
    mid = prop[1]
    mid_info = promos[mid["id"]]
    mid_q = next(r for r in g2["quarter_rows"] if r["id"] == mid["id"])["q"]
    gaps = [(promos[p["id"]]["label"], [m for m in range(min(invoiced[p["id"]]), max(invoiced[p["id"]])) if m not in invoiced[p["id"]]])
            for p in prop]
    gap_text = " ".join(f"{label} has no invoices in {names(ms)}, so that month is left clear." for label, ms in gaps if ms)
    _note(d, f"{fp['label']}'s recorded dates run from {fp['start']} to {fp['end']}, so the end falls {days} day{'s' if days != 1 else ''} before "
             f"the start, yet its lines were ordered in {names(ordered[failing['id']])}. The discount is billed with the invoice: "
             f"{mid_info['label']}'s orders of {names(ordered[mid['id']])} are invoiced through {MONTH_NAMES[invoiced[mid['id']][-1] - 1]}, "
             f"which puts {mid_q[3] / sum(mid_q):.0%} of its discount in the fourth quarter. {gap_text}", ly + 28)
    return d


# -- IF-C2-1-A: the completeness checks on the Documentation sheet ------------------------------------------------------------------

def if_c2_1_a() -> Diagram:
    """Rows 17 to 38 of the Documentation sheet: each query against its source Table, the totals, the discount checks."""
    data = ctx.data()
    g1 = ctx.values("case2.g1")
    r1 = ctx.values("case2.r1")
    rows_of = {s["query"]: s["rows"] for s in g1["sources"]}
    rows_of["BudgetPrices"] = r1["budget_rows"]
    source_of = {s["query"]: s["table"] for s in g1["sources"]}
    order = ["Promotions", "Orders", "Items", "Customers", "OrderLines", "BilledLines", "Accounts", "BudgetPrices", "Overrides",
             "Employees"]
    assert set(order) == set(rows_of), rows_of
    source_of["BudgetPrices"] = "T77_BudgetLine"
    count = lambda n: f"{n:,}"
    checks: list[tuple[str, str, str, str]] = []
    for q in order:
        what = f"{source_of[q]}: rows with BudgetCategory Revenue (SourceCounts)" if q == "BudgetPrices" else f"{source_of[q]}: rows (SourceCounts)"
        checks.append((f"{q}: rows loaded", what, count(rows_of[q]), count(rows_of[q])))
    lines_total = data.one("SELECT SUM(LineTotal) FROM SalesOrderLine")
    orders_total = data.one("SELECT SUM(OrderTotal) FROM SalesOrder")
    assert abs(lines_total - orders_total) < 0.005 and abs(lines_total - r1["order_total"]) < 0.005
    checks.append(("OrderLines: total LineTotal", "Orders: total OrderTotal", _money(lines_total), _money(orders_total)))
    differ = data.one("SELECT COUNT(*) FROM SalesOrder o LEFT JOIN (SELECT SalesOrderID, SUM(LineTotal) AS s FROM SalesOrderLine GROUP BY 1) t "
                      "ON t.SalesOrderID = o.SalesOrderID WHERE t.s IS NULL OR ABS(o.OrderTotal - t.s) > 0.005")
    ghost_o = data.one("SELECT COUNT(*) FROM SalesOrderLine WHERE PromotionID IS NULL AND Discount <> 0")
    ghost_b = data.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NULL AND Discount <> 0")
    assert differ == ghost_o == ghost_b == 0
    checks.append(("Orders whose OrderTotal differs from their own lines (Orders[LinesAgree])", "none expected", "0", "0"))
    checks.append(("Order lines without a PromotionID that carry a discount", "none expected", "0", "0"))
    checks.append(("Billed lines without a PromotionID that carry a discount", "none expected", "0", "0"))
    rates = lambda sql: ", ".join(f"{r[0]:g}" for r in data.q(sql))
    promo_rates = ", ".join(f"{r:g}" for r in sorted({r[0] for r in data.q("SELECT DISTINCT DiscountPct FROM PromotionProgram")} | {0}))
    o_rates, b_rates = rates("SELECT DISTINCT Discount FROM SalesOrderLine ORDER BY 1"), rates("SELECT DISTINCT Discount FROM SalesInvoiceLine ORDER BY 1")
    assert o_rates == b_rates == promo_rates == g1["rate_list"], (o_rates, b_rates, promo_rates)
    checks.append(("Discount rates in OrderLines (the decimal type keeps them)", "zero and the promotions' DiscountPct", o_rates, promo_rates))
    checks.append(("Discount rates in BilledLines", "zero and the promotions' DiscountPct", b_rates, promo_rates))
    lost_o = data.one("SELECT COUNT(*) FROM SalesOrderLine l LEFT JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID LEFT JOIN Item i ON i.ItemID = l.ItemID "
                      "WHERE o.SalesOrderID IS NULL OR i.ItemID IS NULL")
    lost_b = data.one("SELECT COUNT(*) FROM SalesInvoiceLine l LEFT JOIN SalesInvoice v ON v.SalesInvoiceID = l.SalesInvoiceID LEFT JOIN Item i "
                      "ON i.ItemID = l.ItemID WHERE v.SalesInvoiceID IS NULL OR i.ItemID IS NULL")
    assert lost_o == lost_b == 0
    checks.append(("OrderLines lookups not matched (OrderDate, ItemCode, CustomerSegment, a promotion's ScopeType)", "none expected", "0", "0"))
    checks.append(("BilledLines lookups not matched (InvoiceDate, ItemGroup)", "none expected", "0", "0"))
    year = str(g1["year"])
    debits = data.one("SELECT SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND substr(PostingDate, 1, 4) = ?", year)
    credits = data.one("SELECT SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND substr(PostingDate, 1, 4) = ?", year)
    assert abs(debits - credits) < 0.005
    checks.append(("RevenuePostings: total debits", "RevenuePostings: total credits (each sales invoice posts in balance)", _money(debits),
                   _money(credits)))
    agree = [a == b for _, _, a, b in checks]
    assert all(agree) and len(checks) == 19, "every check agrees"

    widths = [30, 258, 258, 116, 116, 60]                                 # row numbers, then A to E
    letters = list("ABCDE")
    d = Diagram("The Completeness Checks of the Documentation Sheet")
    geo = _sheet(d, 0, 0, letters, widths, [], show_letters=True)
    y = 22.0
    y = _gap(d, 0, y, sum(widths), "Rows 1 to 16: Purpose, Source, Query steps and the other documentation entries", 22)
    title = "Completeness checks (Requirement 1): each query against its source, before the analysis uses it"
    rows: list[dict] = [dict(n="17", cells=[dict(text=title, bold=True, span=5, clip=False)], h=22),
                        dict(n="18", cells=[_hd(t, a) for t, a in (("Check", "left"), ("Compared with", "left"), ("Query", "right"),
                                                                    ("Source", "right"), ("Agrees", "center"))], h=22)]
    for k, (label, other, q, s) in enumerate(checks):
        rows.append(dict(n=str(19 + k), cells=[_wrapped(label, widths[1]), _wrapped(other, widths[2]),
                                               dict(text=q, align="right"), dict(text=s, align="right"),
                                               dict(text="TRUE", align="center", fill=TEAL_TINT, bold=True)]))
    rows.append(dict(n=str(19 + len(checks)), cells=[dict(text="All completeness checks agree", bold=True, fill=BLUE_TINT), dict(fill=BLUE_TINT),
                                                     dict(fill=BLUE_TINT), dict(fill=BLUE_TINT),
                                                     dict(text="TRUE", align="center", fill=TEAL_TINT, bold=True)], h=22))
    geo = _sheet(d, 0, y, [], widths, rows, show_letters=False)
    n = len(checks)
    x4, y4, w4, _ = geo[(2, 4)]
    _, y_last, _, h_last = geo[(len(rows) - 1, 4)]
    _mark(d, x4, y4, w4, y_last + h_last - y4, TEAL)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Documentation", "Parameters", "Promotions", "Orders", "Items"], "Documentation")
    _note(d, f"Outlined: the Agrees column, TRUE in every row. Each Query cell counts the loaded query with ROWS or a SUM, each Source cell "
             f"reads {esc('SourceCounts')} or the source Table, and Agrees is the test that the two are equal; the totals are shown to the cent. "
             f"Rows 40 to 44, the control totals, are not shown.", bottom + 34)
    return d


# -- IF-C2-2-A: the PivotTable of the discount by promotion and year -----------------------------------------------------------------

def if_c2_2_a() -> Diagram:
    """The PivotTable on BilledLines (promotions down, invoice years across) and the chart of the yearly totals."""
    data = ctx.data()
    g2 = ctx.values("case2.g2")
    r2 = ctx.values("case2.r2")
    years = r2["years"]
    ys = [y["year"] for y in years]
    cells: dict[tuple[int, int], tuple[float, int]] = {}
    for pid, yr, disc, n in data.q(
            "SELECT l.PromotionID, CAST(substr(i.InvoiceDate, 1, 4) AS INTEGER), SUM(l.Quantity * l.UnitPrice * l.Discount), COUNT(*) "
            "FROM SalesInvoiceLine l JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID WHERE l.PromotionID IS NOT NULL GROUP BY 1, 2"):
        cells[(pid, yr)] = (disc, n)
    pids = sorted({p for p, _ in cells})
    assert len(pids) == 9 and all(y in ys for _, y in cells), pids
    total_disc = sum(v[0] for v in cells.values())
    total_n = sum(v[1] for v in cells.values())
    assert abs(total_disc - g2["pivot_total"]) < 0.005 and total_n == r2["lines"], (total_disc, total_n)
    spill_ids = [p for p in pids if sum(1 for y in ys if (p, y) in cells) > 1]
    assert set(map(int, re.findall(r"\d+", g2["spill"]))) == set(spill_ids), (spill_ids, g2["spill"])
    sumw, cntw = 112, 68
    widths = [28, 100] + [sumw, cntw] * 4                                   # row numbers, A, then four value pairs
    letters = [chr(65 + i) for i in range(9)]
    d = Diagram("The PivotTable of the Promotional Discount by Promotion and Invoice Year")
    geo = _sheet(d, 0, 0, letters, widths, [], show_letters=True)
    y = 22.0
    y = _gap(d, 0, y, sum(widths), "Rows 1 to 4: the title and the PivotTable's report area", 22)
    rows: list[dict] = []
    rows.append(dict(n="5", cells=[dict(text=""), dict(text="Column Labels", bold=True, fill=BLUE_TINT, span=2, filter=True)], h=22))
    rows.append(dict(n="6", cells=[dict(text="")] + [dict(text=str(yr), bold=True, fill=BLUE_TINT, span=2, align="left") for yr in ys]
                     + [_wrapped("Total Sum of DiscountAmount", sumw, bold=True, fill=BLUE_TINT, align="left"),
                        _wrapped("Total Count of lines", cntw, bold=True, fill=BLUE_TINT, align="left")]))
    head = [dict(text="Row Labels", bold=True, fill=BLUE_TINT, filter=True)]
    for _ in ys:
        head += [_wrapped("Sum of DiscountAmount", sumw, bold=True, fill=BLUE_TINT), _wrapped("Count of lines", cntw, bold=True, fill=BLUE_TINT)]
    head += [dict(text="", fill=BLUE_TINT), dict(text="", fill=BLUE_TINT)]
    rows.append(dict(n="7", cells=head))
    start_row = 8
    for k, pid in enumerate(pids):
        row = [dict(text=str(pid), align="left")]
        for yr in ys:
            v = cells.get((pid, yr))
            row += [dict(text=_money(v[0]) if v else ""), dict(text=f"{v[1]:,}" if v else "")]
        tot = sum(cells[(pid, yr)][0] for yr in ys if (pid, yr) in cells)
        totn = sum(cells[(pid, yr)][1] for yr in ys if (pid, yr) in cells)
        row += [dict(text=_money(tot)), dict(text=f"{totn:,}")]
        rows.append(dict(n=str(start_row + k), cells=row, h=22))
    grand = [dict(text="Grand Total", bold=True, fill=BLUE_TINT, align="left")]
    for yr in ys:
        s = sum(cells[(p, yr)][0] for p in pids if (p, yr) in cells)
        c = sum(cells[(p, yr)][1] for p in pids if (p, yr) in cells)
        grand += [dict(text=_money(s), bold=True, fill=BLUE_TINT), dict(text=f"{c:,}", bold=True, fill=BLUE_TINT)]
    grand += [dict(text=_money(total_disc), bold=True, fill=BLUE_TINT), dict(text=f"{total_n:,}", bold=True, fill=BLUE_TINT)]
    rows.append(dict(n=str(start_row + len(pids)), cells=grand, h=22))
    geo = _sheet(d, 0, y, [], widths, rows, show_letters=False)
    # The second column of discount of the promotions that were also invoiced in the year after they ran.
    for k, pid in enumerate(pids):
        if pid not in spill_ids:
            continue
        later = [yr for yr in ys if (pid, yr) in cells][1:]
        for yr in later:
            c = ys.index(yr)
            x1, y1, w1, h1 = geo[(3 + k, 1 + 2 * c)]
            x2, _, w2, _ = geo[(3 + k, 2 + 2 * c)]
            _mark(d, x1, y1, x2 + w2 - x1, h1, CORAL, inset=1.5)
    sheet_bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, sheet_bottom, ["SourceCounts", "R2 Cost", "R2 Gross to Net"], "R2 Cost")
    # The chart of the yearly totals (Step 2) and what to read in the PivotTable.
    cy = sheet_bottom + 46
    d.text("<b>Promotional discount by invoice year</b>, rounded by year as in Step 2", 0, cy, 560, 20, size=SMALL)
    tops = [y["disc"] for y in years]
    ymax = 500000
    ticks = [0, 100000, 200000, 300000, 400000, 500000]
    assert max(tops) < ymax - 80000
    plot = kit.Plot(d, 0, cy + 24, 560, 250, None, y_ticks=ticks, categories=[str(y) for y in ys], y_fmt=lambda v: f"${v / 1000:,.0f}K",
                    bottom=26)
    plot.bars([xl.xround(v, 2) for v in tops], color=BLUE, ratio=0.5)
    slot = plot.pw / len(ys)
    for k, yd in enumerate(years):
        top = plot.y_of(yd["disc"])
        d.box(f"<b>${xl.xround(yd['disc'], 2):,.2f}</b><br>{yd['share'] * 100:.2f}% of billed revenue", plot.px + slot * k + slot / 2 - 90, top - 38,
              180, 34, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
    px = 590
    rounded_sum = sum(xl.xround(v, 2) for v in tops)
    off = abs(rounded_sum - total_disc)
    assert off < 0.025, off
    cent_text = "less than a cent" if off < 0.005 else "a cent" if off < 0.015 else "two cents"
    kit.callout(d, f"<b>Grand total:</b> ${_money(total_disc)} of discount on {total_n:,} lines, so every promotion line is in a row and no "
                   f"(blank) row remains. The yearly totals in the chart are the PivotTable's column totals, rounded year by year, so they add to "
                   f"${_money(rounded_sum)}, {cent_text} from the unrounded grand total.", px, cy + 24, 270, color="blue")
    kit.callout(d, f"<b>Outlined:</b> the second column of discount of promotions {g2['spill']}. Their orders were invoiced in the year after "
                   f"they ran.", px, cy + 150, 270, color="coral")
    _note(d, "The PromotionID filter has (blank), the lines with no promotion, cleared, so they are not counted.", cy + 24 + 250 + 4)
    return d


# -- IF-C2-2-B: the gross-to-net walk of the report year ------------------------------------------------------------------------------

def if_c2_2_b() -> Diagram:
    """List amount, the price-list and override reductions, the promotional discounts, the line rounding and the net billed."""
    r2 = ctx.values("case2.r2")
    year = ctx.values("case2.chapter")["report_year"]
    lst, red, disc, rounding, net = r2["list"], r2["red"], r2["disc"], r2["rounding"], r2["net"]
    assert abs(lst - red - disc + rounding - net) < 0.01, "the walk adds up"
    assert red > 0 and disc > 0 and 0 < rounding < 1, "two decreases and a rounding of less than a dollar"
    steps = [("List amount", 0.0, lst, "total", lst),
             ("Price lists and overrides", lst, lst - red, "decrease", -red),
             ("Promotional discounts", lst - red, lst - red - disc, "decrease", -disc),
             ("Line rounding", lst - red - disc, lst - red - disc + rounding, "increase", rounding),
             ("Net billed", 0.0, net, "total", net)]
    top = 35e6
    assert lst < top
    d = Diagram("The Gross-to-Net Walk")
    d.text(f"<b>Fiscal {year}: from the list amount to the net billed, all item groups</b>", 0, 0, 860, 20, size=SMALL)
    plot = kit.Plot(d, 0, 26, 860, 420, None, y_ticks=[0, 5e6, 10e6, 15e6, 20e6, 25e6, 30e6, 35e6], categories=[s[0] for s in steps],
                    y_fmt=lambda v: f"${v / 1e6:.0f}M", bottom=30)
    slot = plot.pw / len(steps)
    bw = max(slot * 0.5, text_width(f"${lst:,.2f}", SMALL, True) + 20)
    d.box("", plot.px, plot.y_of(0) - 1, plot.pw, 2, fill=INK, stroke=INK, rounded=False)
    fills = {"total": BLUE, "decrease": CORAL, "increase": TEAL}
    ends = []
    for i, (name, a, b, kind, amount) in enumerate(steps):
        x0 = plot.px + slot * i + (slot - bw) / 2
        hi, lo = max(a, b), min(a, b)
        d.box("", x0, plot.y_of(hi), bw, max(plot.y_of(lo) - plot.y_of(hi), 1.5), fill=fills[kind], stroke=fills[kind], rounded=False)
        ends.append((x0, x0 + bw, b))
    for (x0, x1, level), (nx0, _, _) in zip(ends, ends[1:]):
        d.box("", x1, plot.y_of(level) - 0.75, nx0 - x1, 1.5, fill=GRAY, stroke=GRAY, rounded=False)
    for i, (name, a, b, kind, amount) in enumerate(steps):
        x0, x1, _ = ends[i]
        cx = (x0 + x1) / 2
        text = f"${amount:,.2f}" if kind == "total" else (MINUS if amount < 0 else "+") + f"${abs(amount):,.2f}"
        if kind == "total":
            d.text(f"<b>{text}</b>", x0, plot.y_of(max(a, b)) + 6, bw, 20, size=SMALL, color=WHITE, align="center")
        else:
            top_y = plot.y_of(max(a, b))
            d.box(f"<b>{text}</b>", cx - 62, top_y - 24, 124, 18, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
    gx0, gx1 = ends[1][0], ends[3][1]
    mid = plot.y_of(15e6)
    d.box(f"<b>{red / lst:.1%} of the list amount</b> goes to the price lists and overrides, and <b>{disc / lst:.1%}</b> goes to "
          f"promotions. The line rounding, {rounding:.2f} dollars in all, is the cent each LineTotal is rounded to.", gx0 - 10, mid - 30,
          gx1 - gx0 + 20, 66, fill=AMBER_TINT, stroke=AMBER, size=SMALL, rounded=False, align="left")
    ly = 26 + 420 + 12
    cx = 0.0
    for fill, label in ((BLUE, "A total"), (CORAL, "A reduction"), (TEAL, "An addition")):
        _swatch(d, cx, ly + 3, fill)
        w = text_width(label, SMALL, False) + 8
        d.text(label, cx + 20, ly, w, 20, size=SMALL, valign="middle")
        cx += 20 + w + 22
    _note(d, f"The bars are drawn to scale from zero, so the promotional discounts are a thin bar and the rounding a sliver; the amounts are labeled "
             f"to the cent. List less reductions less promotions is ${r2['after']:,.2f}, and the rounding is what separates it from the net billed.",
          ly + 28)
    return d


# -- IF-C2-3-A: the comparison table of the volume test -----------------------------------------------------------------------------

def if_c2_3_a() -> Diagram:
    """Rows 39 to 49 of R3 Volume: volume in each promotion's months against its two expectations and the normal variation."""
    import statistics as st
    data = ctx.data()
    g = ctx.values("case2.chapter")
    g3 = ctx.values("case2.g3")
    promos = {p["id"]: p for p in g["promos"]}
    scope_sql = {"collection": "i.CollectionName", "item group": "i.ItemGroup", "segment": "c.CustomerSegment"}
    orders = ("FROM SalesOrderLine l JOIN SalesOrder o ON o.SalesOrderID = l.SalesOrderID JOIN Item i ON i.ItemID = l.ItemID "
              "JOIN Customer c ON c.CustomerID = o.CustomerID")
    first_year = g3["first_year"]
    table = []
    for row in g3["rows"]:
        p = promos[row["id"]]
        by_month = {(int(y), int(m)): v for y, m, v in data.q(
            f"SELECT substr(o.OrderDate, 1, 4), substr(o.OrderDate, 6, 2), SUM(l.Quantity * l.BaseListPrice) {orders} "
            f"WHERE {scope_sql[p['kind']]} = ? GROUP BY 1, 2", p["label"])}
        months = list(range(int(p["first"][5:7]), int(p["last"][5:7]) + 1))
        y = p["year"]
        window = sum(by_month.get((y, m), 0.0) for m in months)
        other = [by_month.get((y, m), 0.0) for m in range(1, 13) if m not in months]
        expected, sd = st.mean(other) * len(months), st.stdev(other)
        prior = sum(by_month.get((y - 1, m), 0.0) for m in months) if y - 1 >= first_year else None
        diff, z = window / expected - 1, (window - expected) / (sd * len(months) ** 0.5)
        assert abs(diff - row["lift"]) < 1e-9 and abs(z - row["z"]) < 1e-9 and (prior is None) == (row["py"] is None)
        table.append(dict(id=row["id"], label=p["label"], months=len(months), window=window, expected=expected, diff=diff, prior=prior,
                          py=None if prior is None else window / prior - 1, sd=sd, z=z, beyond=abs(z) >= 2))
    assert not any(t["beyond"] for t in table), "every last cell reads FALSE"
    hi = max(range(len(table)), key=lambda i: table[i]["diff"])
    lo = min(range(len(table)), key=lambda i: table[i]["diff"])
    assert hi != lo and g3["cmp"]["cmp"] == 41, g3["cmp"]
    letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L"]            # column J, the standard deviation as a share of the mean, is hidden
    widths = [28, 86, 92, 48, 78, 78, 70, 78, 70, 78, 72, 72]
    whole = lambda v: f"{xl.xround(v, 0):,.0f}"
    pct = lambda v: f"{xl.xround(v * 100, 1):.1f}%"
    heads = ["PromotionID", "Scope", "Months", "Volume in the promotion's months", "Expectation", "Difference", "The same months a year earlier",
             "Difference from a year earlier", "Standard deviation of the other months", "Difference in standard deviations",
             "Beyond two standard deviations"]
    d = Diagram("The Comparison Table of the Volume Test")
    xl.sheet(d, 0, 0, letters, widths, [], None, show_letters=True)
    y = 22.0
    y = _gap(d, 0, y, sum(widths), "Rows 1 to 38: the months and the monthly grids of the promotions", 22)
    rows = [dict(n="39", cells=[dict(text="(4) Volume in each promotion's months against two expectations, and the scope's normal variation", bold=True,
                                     span=11, clip=False)], h=22),
            dict(n="40", cells=[_wrapped(h, w, bold=True, fill=BLUE_TINT, align="left" if i < 2 else "right") for i, (h, w) in
                                enumerate(zip(heads, widths[1:]))])]
    for k, t in enumerate(table):
        rows.append(dict(n=str(41 + k), cells=[dict(text=str(t["id"]), align="left"), dict(text=t["label"]),
                                               dict(text=str(t["months"]), align="right"), dict(text=whole(t["window"])),
                                               dict(text=whole(t["expected"])), dict(text=pct(t["diff"])),
                                               dict(text="" if t["prior"] is None else whole(t["prior"])),
                                               dict(text="n/a" if t["py"] is None else pct(t["py"]), align="right"),
                                               dict(text=whole(t["sd"])), dict(text=f"{xl.xround(t['z'], 2):.2f}", align="right"),
                                               dict(text="FALSE" if not t["beyond"] else "TRUE", align="center")], h=24))
    geo = _sheet(d, 0, y, [], widths, rows, show_letters=False)
    for idx, color in ((hi, CORAL), (lo, TEAL)):
        cols = (5, 9) if idx == hi else (5,)
        for c in cols:
            x1, y1, w1, h1 = geo[(2 + idx, c)]
            _mark(d, x1, y1, w1, h1, color, inset=1.5)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["R2 Gross to Net", "R3 Volume", "R3 Customers"], "R3 Volume")
    t_hi, t_lo = table[hi], table[lo]
    n_first = sum(1 for t in table if t["py"] is None)
    _note(d, f"Outlined in coral: the largest difference from the expectation, promotion {t_hi['id']} ({t_hi['label']}), {pct(t_hi['diff'])}, "
             f"which is {t_hi['z']:.2f} standard deviations. Outlined in teal: the smallest, promotion {t_lo['id']} ({t_lo['label']}), {pct(t_lo['diff'])}. "
             f"The {_words(n_first)} promotions of {first_year} have no year earlier, so their comparison reads n/a. Volume is the list amount ordered in the "
             f"scope. Column J, the standard deviation as a share of the mean, is hidden.", bottom + 34)
    return d


# -- IF-C2-4-A: the Furniture promotion's data table ---------------------------------------------------------------------------------

def if_c2_4_a() -> Diagram:
    """Rows 37 to 52 of R4 Model: the inputs, the result cell and the data table of the difference in contribution."""
    g4 = ctx.values("case2.g4")
    fur, c = g4["fur"], g4["c"]
    units, price, cost = fur["units"], fur["price"], fur["cost"]
    rates, lifts = [0.05, 0.08, 0.10, 0.12], [round(i * 0.05, 2) for i in range(9)]
    without = units * (price * (1 - c) - cost)
    diff = lambda rate, lift: units * (1 + lift) * (price * (1 - rate) * (1 - c) - cost) - without
    be = lambda rate: (price * (1 - c) - cost) / (price * (1 - rate) * (1 - c) - cost) - 1
    rw = g4["rows"]
    assert (rw["rate"], rw["lift"], rw["diff"], rw["top"], rw["first"], rw["last"], rw["tb"]) == (38, 39, 40, 42, 43, 51, 52), rw
    assert abs(diff(0.05, 0.0) - g4["corner"]) < 1e-6 and abs(be(0.10) - fur["be"]) < 1e-9
    stairs = {r: next(l for l in lifts if diff(r, l) > 0) for r in rates}
    assert [stairs[r] for r in rates] == [p["lift"] for p in g4["positives"]], (stairs, g4["positives"])
    default_rate, default_lift = fur["rate"], 0.0
    assert abs(default_rate - 0.10) < 1e-9
    whole = lambda v: f"{xl.xround(v, 0):,.0f}"
    pct = lambda v, p=0: f"{xl.xround(v * 100, p):.{p}f}%"
    widths = [28, 296, 100, 109, 109, 109, 109]                          # row numbers, then A to F
    d = Diagram("The Data Table of the Furniture Promotion")
    formula = esc(f"=$C$7*(1+C{rw['lift']})*($C$8*(1-C{rw['rate']})*(1-$C$11)-$C$9)-$C$13")
    _formula_bar(d, 0, 0, 860, f"C{rw['diff']}", formula)
    sy = 40.0
    xl.sheet(d, 0, sy, list("ABCDEF"), widths, [], None, show_letters=True)
    y = sy + 22
    y = _gap(d, 0, y, sum(widths), "Rows 1 to 36: the model of the three proposed promotions", 22)
    blue_input = lambda text: dict(text=text, align="right", color=BLUE, bold=True)
    rows = [dict(n="37", cells=[dict(text="(3) The Furniture promotion: difference in contribution by discount rate (across) and volume lift (down), a data table",
                                     bold=True, span=6, clip=False)], h=22),
            dict(n="38", cells=[dict(text="Discount rate (the data table's row input cell)"), dict(), blue_input(pct(default_rate))]),
            dict(n="39", cells=[dict(text="Volume lift (the data table's column input cell)"), dict(), blue_input(pct(default_lift))]),
            dict(n="40", cells=[dict(text="Difference at these inputs"), dict(), dict(text=whole(diff(default_rate, default_lift)), align="right",
                                                                                     fill=BLUE_TINT)]),
            dict(n="41", cells=[])]
    rows.append(dict(n="42", cells=[dict(text="Lift (down) by discount rate (across)", bold=True, fill=BLUE_TINT),
                                    dict(text=whole(diff(default_rate, default_lift)), align="right", fill=BLUE_TINT)]
                     + [dict(text=pct(r), bold=True, fill=BLUE_TINT, align="right") for r in rates]))
    for k, lift in enumerate(lifts):
        cells = [dict(), dict(text=pct(lift), bold=True, fill=BLUE_TINT, align="right")]
        for r in rates:
            v = diff(r, lift)
            cells.append(dict(text=whole(v), align="right", fill=TEAL_TINT if v > 0 else WHITE, bold=v > 0, stroke=TEAL if v > 0 else RULE))
        rows.append(dict(n=str(43 + k), cells=cells))
    rows.append(dict(n="52", cells=[dict(text="Break-even lift at this rate", bold=True, fill=AMBER_TINT), dict(fill=AMBER_TINT)]
                     + [dict(text=pct(be(r), 1), bold=True, fill=AMBER_TINT, align="right") for r in rates]))
    geo = _sheet(d, 0, y, [], widths, rows, show_letters=False)
    xl.select(d, *geo[(3, 2)])
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["R3 Customers", "R4 Model", "R4 Budgets"], "R4 Model")
    d.box("", 0, bottom + 36, 14, 14, fill=TEAL_TINT, stroke=TEAL, rounded=False)
    d.text("A positive difference: the promotion earns more than it gives up at that discount and lift", 20, bottom + 33, 520, 20, size=SMALL,
           valign="middle")
    _note(d, f"The inputs, in blue, are C{rw['rate']} and C{rw['lift']}; they sit on this sheet because a data table's input cells must. C{rw['diff']} is the "
             f"result cell, selected, and B{rw['top']} repeats it. Every grid cell is the one array formula {{=TABLE(C{rw['rate']},C{rw['lift']})}}. "
             f"The shaded cells begin at the first lift above each break-even: {', '.join(f'{pct(r)} at {pct(stairs[r])}' for r in rates)}.",
          bottom + 62)
    return d


# -- IF-C2-4-B: the measured difference against the break-even of each promotion ------------------------------------------------------

def if_c2_4_b() -> Diagram:
    """A row for each promotion: the measured difference as a bar and the break-even lift as a marker to its right."""
    g = ctx.values("case2.chapter")
    g4 = ctx.values("case2.g4")
    nine = g4["nine"]
    promos = {p["id"]: p for p in g["promos"]}
    proposed = {p["id"] for p in g["proposal"]}
    assert len(nine) == 9 and len(proposed) == 3
    assert all(n["lift"] < n["be"] for n in nine) and max(n["share"] for n in nine) < 0.5, "no difference reaches half of its break-even"
    lo, hi = -0.30, 0.50
    x0, x1 = 214.0, 690.0
    x_of = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    assert min(n["lift"] for n in nine) > lo + 0.05 and max(n["be"] for n in nine) < hi - 0.08
    d = Diagram("Each Promotion's Measured Difference and Its Break-Even Lift")
    top, rh = 34.0, 38.0
    n = len(nine)
    bottom = top + n * rh
    d.text("<b>Measured difference in volume and break-even lift, each promotion</b>", 0, 0, 640, 20, size=SMALL)
    d.box("<b>Share of its<br>break-even reached</b>", x1 + 12, 0, 860 - x1 - 12, 32, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
    for k, r in enumerate(nine):
        y = top + k * rh
        if r["id"] in proposed:
            d.box("", 0, y, 860, rh, fill=AMBER_TINT, stroke=AMBER_TINT, rounded=False)
    ticks = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
    for t in ticks:
        d.box("", x_of(t) - 0.5, top, 1, n * rh, fill=INK if t == 0 else RULE, stroke=INK if t == 0 else RULE, rounded=False)
        d.text(f"{t * 100:.0f}%" if t >= 0 else f"{MINUS}{abs(t) * 100:.0f}%", x_of(t) - 26, bottom + 4, 52, 18, size=SMALL, color=GRAY,
               align="center")
    d.text("Volume lift (measured difference or break-even)", x0, bottom + 24, x1 - x0, 18, size=SMALL, color=GRAY, align="center")
    best = max(nine, key=lambda r: r["share"])
    for k, r in enumerate(nine):
        y = top + k * rh
        p = promos[r["id"]]
        tag = r["id"] in proposed
        d.text(f"<b>{r['id']}  {esc(p['label'])}</b>" + (" (proposed)" if tag else ""), 6, y + 3, 206, 18, size=SMALL)
        d.text(f"{esc(p['kind'])}, {p['year']}, {r['rate'] * 100:.0f}% off", 6, y + 19, 206, 18, size=SMALL, color=GRAY)
        d.box("", x_of(0), y + rh / 2 - 1.5, x_of(r["be"]) - x_of(0), 3, fill=RULE, stroke=RULE, rounded=False)
        a, b = sorted((x_of(0), x_of(r["lift"])))
        d.box("", a, y + 8, max(b - a, 1.5), rh - 16, fill=BLUE, stroke=BLUE, rounded=False)
        d.vertex("", f"rhombus;html=1;fillColor={AMBER};strokeColor={WHITE};strokeWidth=1.5;", x_of(r["be"]) - 9, y + rh / 2 - 9, 18, 18)
        d.text(f"<b>{r['be'] * 100:.1f}%</b>", x_of(r["be"]) + 12, y + rh / 2 - 10, 52, 20, size=SMALL, valign="middle")
        text = _signed(r["lift"])
        bg = AMBER_TINT if tag else WHITE
        tw = text_width(f"<b>{text}</b>", SMALL, True) + 10
        if r["lift"] >= 0:
            d.box(f"<b>{text}</b>", b + 3, y + rh / 2 - 10, tw, 20, fill=bg, stroke=bg, size=SMALL, rounded=False)
        else:
            d.box(f"<b>{text}</b>", a - tw - 3, y + rh / 2 - 10, tw, 20, fill=bg, stroke=bg, size=SMALL, rounded=False)
        share = f"{r['share'] * 100:.0f}%".replace("-", MINUS)
        d.text(f"<b>{share}</b>" if r is best else share, x1 + 12, y + rh / 2 - 10, 60, 20, size=SMALL, valign="middle")
    ly = bottom + 50
    cx = 0.0
    _swatch(d, cx, ly + 3, BLUE)
    d.text("Measured difference from the expectation", cx + 20, ly, 270, 20, size=SMALL, valign="middle")
    cx += 310
    d.vertex("", f"rhombus;html=1;fillColor={AMBER};strokeColor={WHITE};strokeWidth=1.5;", cx, ly + 1, 18, 18)
    d.text("Break-even lift", cx + 24, ly, 110, 20, size=SMALL, valign="middle")
    cx += 150
    _swatch(d, cx, ly + 3, AMBER_TINT, AMBER)
    d.text("A promotion in the 2027 proposal", cx + 20, ly, 220, 20, size=SMALL, valign="middle")
    _note(d, f"No measured difference reaches half of its break-even: the largest share is {best['share']:.0%}, promotion {best['id']} "
             f"({promos[best['id']]['label']}). A break-even is the lift the promotion needs, not a forecast of what it will bring; the gray "
             f"track runs from zero to it.", ly + 28)
    return d



# -- IF-C2-5-A: the four tests counted by promotion ------------------------------------------------------------------------------------

def _last_day(iso_month: str) -> str:
    y, m = int(iso_month[:4]), int(iso_month[5:7])
    return f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"


def if_c2_5_a() -> Diagram:
    """Rows 3 to 14 of R5 Controls: lines, the three line tests, the completeness test and its window, by promotion."""
    g = ctx.values("case2.chapter")
    g5 = ctx.values("case2.g5")
    promos = {p["id"]: p for p in g["promos"]}
    tests = g5["tests"]
    assert len(tests) == 9
    rows_in = []
    for t in tests:
        p = promos[t["id"]]
        if t["fails"]:                       # the window is the calendar months in which the lines were ordered
            start, end = p["first"][:8] + "01", _last_day(p["last"])
        else:
            start, end = p["start"], p["end"]
        assert t["window"][0] == start, (t["window"], start)
        rows_in.append(dict(id=t["id"], label=p["label"], lines=t["lines"], dates=t["out_dates"], scope=t["out_scope"], rate=t["bad_rate"],
                            start=start, end=end, missing=t["missing"], fails=t["fails"]))
    total = {k: sum(r[k] for r in rows_in) for k in ("lines", "dates", "scope", "rate", "missing")}
    assert total["lines"] == sum(p["lines"] for p in promos.values())
    assert all(r["dates"] == r["lines"] for r in rows_in if r["fails"]) and all(r["dates"] == 0 for r in rows_in if not r["fails"])
    assert total["scope"] > 0 and total["rate"] == 0 and total["missing"] == 0
    letters = ["A", "D", "E", "F", "G", "H", "I", "J", "K"]                  # columns B and C, the name and the kind of scope, are hidden
    widths = [28, 86, 96, 56, 98, 84, 84, 92, 92, 124]
    heads = ["PromotionID", "Scope", "Lines", "Outside the recorded dates", "Outside the scope", "Rate differs", "Window start", "Window end",
             "In scope and window without the promotion"]
    d = Diagram("The Four Tests Counted by Promotion")
    _formula_bar(d, 0, 0, 860, "F5", esc("=COUNTIFS(OrderLines[PromotionID],$A5,OrderLines[DateOK],FALSE)"))
    sy = 40.0
    xl.sheet(d, 0, sy, letters, widths, [], None, show_letters=True)
    y = sy + 22
    y = _gap(d, 0, y, sum(widths), "Rows 1 and 2: the title of the sheet", 22)
    rows = [dict(n="3", cells=[dict(text="(1) Four tests by promotion: three on every promotion line, and completeness from all order lines",
                                    bold=True, span=9, clip=False)], h=22),
            dict(n="4", cells=[_wrapped(h, w, bold=True, fill=BLUE_TINT, align="left" if i < 2 else "right") for i, (h, w) in
                               enumerate(zip(heads, widths[1:]))])]
    for k, r in enumerate(rows_in):
        rows.append(dict(n=str(5 + k), cells=[dict(text=str(r["id"]), align="left"), dict(text=r["label"]), dict(text=f"{r['lines']:,}"),
                                              dict(text=str(r["dates"])), dict(text=str(r["scope"])), dict(text=str(r["rate"])),
                                              dict(text=r["start"], align="right"), dict(text=r["end"], align="right"),
                                              dict(text=str(r["missing"]))], h=24))
    rows.append(dict(n=str(5 + len(rows_in)), cells=[dict(text="Total", bold=True, fill=BLUE_TINT, align="left"), dict(fill=BLUE_TINT),
                                                       dict(text=f"{total['lines']:,}", bold=True, fill=BLUE_TINT),
                                                       dict(text=str(total["dates"]), bold=True, fill=BLUE_TINT),
                                                       dict(text=str(total["scope"]), bold=True, fill=BLUE_TINT),
                                                       dict(text=str(total["rate"]), bold=True, fill=BLUE_TINT), dict(fill=BLUE_TINT),
                                                       dict(fill=BLUE_TINT), dict(text=str(total["missing"]), bold=True, fill=BLUE_TINT)], h=24))
    geo = _sheet(d, 0, y, [], widths, rows, show_letters=False)
    xl.select(d, *geo[(2, 3)])                                               # F5, the cell whose formula shows in the bar
    for k, r in enumerate(rows_in):
        if r["fails"]:
            _mark(d, *geo[(2 + k, 3)], CORAL, inset=1.5)
        if r["scope"]:
            _mark(d, *geo[(2 + k, 4)], TEAL, inset=1.5)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["R4 Budgets", "R5 Controls", "Memo"], "R5 Controls")
    failing = [r for r in rows_in if r["fails"]]
    names = ", ".join(str(r["id"]) for r in failing[:-1]) + f" and {failing[-1]['id']}"
    oos = next(r for r in rows_in if r["scope"])
    _note(d, f"Outlined in coral: the count outside the recorded dates for promotions {names}, which equals their line counts. Outlined in teal: the "
             f"{_words(oos['scope'])} lines of promotion {oos['id']} outside their scope. Every other count is zero. For a promotion whose lines all "
             f"fail the date test, the window is the calendar months in which they were ordered, a provisional test, because its recorded dates hold "
             f"no order line of its scope. Columns B and C, the promotion's name and its kind of scope, are hidden.", bottom + 34)
    return d


# -- IF-C2-5-B: the evidence from outside the record under test --------------------------------------------------------------------------

def if_c2_5_b() -> Diagram:
    """One failing collection promotion's year: its recorded window, the months its lines were ordered, and the budget's price."""
    data = ctx.data()
    g5 = ctx.values("case2.g5")
    names = {p["id"]: p["name"] for p in ctx.values("case2.chapter")["promos"]}
    plain_months = (1, 2, 5, 6, 7, 8, 12)                                          # the months no promotion ran in

    def ratios(e: dict) -> dict[int, float]:
        return {int(m): r for m, r in data.q(
            "SELECT b.Month, SUM(b.BudgetAmount) / SUM(b.Quantity * i.ListPrice) FROM BudgetLine b JOIN Item i ON i.ItemID = b.ItemID "
            "WHERE b.BudgetCategory = 'Revenue' AND b.FiscalYear = ? AND i.CollectionName = ? GROUP BY 1", e["year"], e["label"])}

    cands = []
    for e in g5["evidence"]:
        order_months = list(range(int(e["first"][5:7]), int(e["last"][5:7]) + 1))
        rt = ratios(e)
        plain = [m for m in plain_months if m not in order_months]
        plain_min = min(rt[m] for m in plain)
        assert all(rt[m] < plain_min - 0.02 for m in order_months), "the budget plans the lower price in the months its lines were ordered"
        extra = [m for m in range(1, 13) if m not in order_months and m not in plain and rt[m] < plain_min - 0.03]
        if e["end"] < e["start"]:
            cands.append((len(extra), -e["year"], e, rt, order_months, plain))
    assert cands, "a failing promotion whose recorded end date falls before its start"
    _, _, e, rt, order_months, plain = min(cands, key=lambda c: c[:2])
    others = [x["id"] for x in g5["evidence"] if x["id"] != e["id"]]
    year = e["year"]
    d = Diagram("The Evidence for a Failing Collection Promotion")
    x0, mw, lw = 190.0, 55.5, 132.0
    d.text(f"<b>{esc(names[e['id']])}, fiscal {year}</b>: its recorded dates against the orders and the budget", 0, 0, 860, 20,
           size=SMALL)
    hy = 28.0
    for m in range(12):
        d.box(f"<b>{MONTHS[m]}</b>", x0 + m * mw, hy, mw, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False)
    r1, r2 = hy + 34, hy + 34 + 74
    c0, ch = r2 + 44 + 14, 170.0
    ymin, ymax = 0.86, 0.94
    y_of = lambda v: c0 + 14 + (ymax - v) * (ch - 36) / (ymax - ymin)
    chart_bottom = y_of(ymin) + 8
    # the months its lines were ordered, as a band behind the three rows
    bx0, bx1 = x0 + (order_months[0] - 1) * mw, x0 + order_months[-1] * mw
    d.box("", bx0, r1 - 6, bx1 - bx0, chart_bottom - r1 + 6, fill=AMBER_TINT, stroke=AMBER_TINT, rounded=False)
    for m in range(13):
        d.box("", x0 + m * mw - 0.5, r1 - 6, 1, chart_bottom - r1 + 6, fill=RULE, stroke=RULE, rounded=False)
    d.box("<b>Recorded dates</b><br>the Promotions table", 0, r1, lw, 62, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<b>Lines ordered</b><br>the order dates", 0, r2, lw, 44, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<b>Budget price as a share of list</b><br>the collection's items", 0, c0, lw, 62, fill=WHITE, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    # row 1: the recorded window is two days wide at most, so the two dates are written beside it and the end points back
    xs_, xe_ = _day_x(e["start"], x0, mw), _day_x(e["end"], x0, mw)
    seg_l, seg_r = min(xs_, xe_) - 5, max(xs_, xe_) + 5
    d.box("", seg_l, r1 + 36, seg_r - seg_l, 22, fill=WHITE, stroke=INK, stroke_width=2.5, rounded=False)
    fw, fh = 92.0, 32.0
    end_flag = d.box(f"ends<br><b>{e['end']}</b>", seg_l - fw - 14, r1 + 1, fw, fh, fill=WHITE, stroke=CORAL, stroke_width=1.5, size=SMALL,
                     rounded=False)
    start_flag = d.box(f"starts<br><b>{e['start']}</b>", seg_r + 14, r1 + 1, fw, fh, fill=WHITE, stroke=INK, stroke_width=1.5, size=SMALL,
                       rounded=False)
    d.edge(start_flag, end_flag, end="blockThin", color=CORAL, width=2.5, exit=(0, 0.5), entry=(1, 0.5), meta=STRAIGHT)
    days = (date.fromisoformat(e["start"]) - date.fromisoformat(e["end"])).days
    d.text(f"<i>the end date is {days} days before the start</i>", seg_r + 14 + fw + 10, r1 + 8, 240, 20, size=SMALL, color=CORAL)
    # row 2: the months its lines were ordered
    d.box(f"<b>{e['lines']} lines</b>", bx0 + 1, r2 + 4, bx1 - bx0 - 2, 36, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
    d.text(f"ordered {e['first']} to {e['last']}", bx1 + 8, r2 + 12, 260, 20, size=SMALL, valign="middle")
    # row 3: the budget's price as a share of list
    for t in (0.86, 0.88, 0.90, 0.92, 0.94):
        d.box("", x0, y_of(t) - 0.5, 12 * mw, 1, fill=RULE, stroke=RULE, rounded=False)
        d.text(f"{t * 100:.0f}%", x0 - 50, y_of(t) - 9, 44, 18, size=SMALL, color=GRAY, align="right")
    pts = [(x0 + (m - 0.5) * mw, y_of(rt[m])) for m in range(1, 13)]
    _polyline(d, pts, BLUE, 3)
    for m, (px, py) in zip(range(1, 13), pts):
        d.vertex("", f"ellipse;html=1;fillColor={BLUE if m in order_months else WHITE};strokeColor={BLUE};strokeWidth=2;", px - 5, py - 5, 10, 10)
    for m in (order_months[0], order_months[-1]):
        px, py = pts[m - 1]
        _label(d, f"{rt[m] * 100:.1f}%", px, py + 8)
    jan = plain[0]
    _label(d, f"{rt[jan] * 100:.1f}%", pts[jan - 1][0], pts[jan - 1][1] - 28)
    ly = chart_bottom + 14
    cx = 0.0
    d.box("", cx, ly + 3, 18, 14, fill=WHITE, stroke=INK, stroke_width=2.5, rounded=False)
    d.text("The recorded window", cx + 24, ly, 150, 20, size=SMALL, valign="middle")
    cx += 190
    _swatch(d, cx, ly + 3, BLUE)
    d.text("Months its lines were ordered", cx + 20, ly, 190, 20, size=SMALL, valign="middle")
    cx += 224
    d.line_sample(cx, ly + 10, 28, color=BLUE, width=3)
    d.text("Budget price as a share of list", cx + 34, ly, 220, 20, size=SMALL, valign="middle")
    _note(d, f"The budget planned {rt[order_months[0]] * 100:.1f}% of list in {_month_name(e['first'])} and {_month_name(e['last'])}, against at least "
             f"{e['low'] * 100:.1f}% in the months with no promotion, so it planned a discount when the promotion ran; November is a little lower in every "
             f"budget, the segment promotion's month. The recorded end date, then, looks like a wrong entry, not discounts given outside the window. "
             f"Promotions {' and '.join(map(str, others))} show the same pattern. The axis starts at 86%.", ly + 28)
    return d


# -- IF-C2-6-A: the layout of the memo and its appendix ------------------------------------------------------------------------------

def _exhibit_makers() -> list[int]:
    """The requirement that makes each exhibit, from the Requirement 6 guide's Step 7 ('the cost by year (R2 Cost), ...')."""
    text = MEMO_GUIDE.read_text(encoding="utf-8")
    step = text[text.index("**Step 7."):]
    step = step[:step.index("\n")]
    return [int(n) for n in re.findall(r"\(R(\d) [A-Za-z0-9 ]+\)", step)]


def _recommendation_sources() -> list[int]:
    text = MEMO_GUIDE.read_text(encoding="utf-8")
    m = re.search(r"^\| Recommendation \|.*\| ((?:R\d(?:, )?)+) \|$", text, re.M)
    return [int(n) for n in re.findall(r"R(\d)", m.group(1))]


def if_c2_6_a() -> Diagram:
    """Two memo pages and the smaller appendix page, each section and exhibit tagged with the requirement that produced it."""
    reqs = _requirements()
    sections = _memo_sections()
    exhibits = _exhibits()
    makers = _exhibit_makers()
    rec = _recommendation_sources()
    assert len(sections) == 3 and len(exhibits) == 5 and len(makers) == 5 and rec == [4, 5], (sections, exhibits, makers, rec)
    by_persp = {s.lower(): s for s in sections}
    feeders = {s: [r["n"] for r in reqs[1:5] if by_persp[r["perspective"]] == s] for s in sections}
    assert [feeders[s] for s in sections] == [[2], [3, 4], [5]], feeders
    chip_w, chip_h, arrow = 92.0, 36.0, 14.0
    PW, AW, PH, AH = 182.0, 156.0, 272.0, 252.0
    p1x = chip_w + arrow
    c2x = p1x + PW + 8
    p2x = c2x + chip_w + arrow
    c3x = p2x + PW + 8
    ax = c3x + chip_w + arrow
    assert ax + AW <= 860, ax + AW
    top = 30.0
    d = Diagram("The Layout of the Memo and Its Appendix")
    d.text("<b>The memo</b>: page 1", p1x, 0, PW, 22, size=SMALL)
    d.text("<b>The memo</b>: page 2", p2x, 0, PW, 22, size=SMALL)
    d.text("<b>The appendix</b>: one page", ax, 0, AW, 22, size=SMALL)
    for x, w, h in ((p1x, PW, PH), (p2x, PW, PH), (ax, AW, AH)):
        d.box("", x, top, w, h, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)

    def chip(x: float, cy: float, nums: list[int], target: str) -> None:
        who = " and ".join(str(n) for n in nums)
        cid = d.box(f"<b>Requirement{'s' if len(nums) > 1 else ''}</b><br>{who}", x, cy - chip_h / 2, chip_w, chip_h, fill=BLUE_TINT, stroke=BLUE,
                    stroke_width=1.5, size=SMALL)
        d.arrow(cid, target, exit=(1, 0.5), entry=(0, 0.5), meta=STRAIGHT)

    def lines(x: float, y: float, w: float, h: float) -> None:
        k, row = 0, y
        while row + 6 <= y + h:
            d.box("", x, row, w * (0.62 if k % 4 == 3 else 1.0), 4, fill=RULE, stroke=RULE, rounded=False)
            row += 10
            k += 1

    def block(px: float, y: float, h: float, title: str, fill: str, stroke: str) -> str:
        bid = d.box("", px + 10, y, PW - 20, h, fill=fill, stroke=stroke, stroke_width=1.5, rounded=False)
        d.text(f"<b>{esc(title)}</b>", px + 16, y + 3, PW - 32, 20, size=SMALL)
        lines(px + 18, y + 28, PW - 36, h - 32)
        return bid

    # page 1: the header lines, the opening, Financial reporting and Managerial accounting
    y = top + 10
    for k, label in enumerate(("To:", "From:", "Date:", "Re:")):
        d.box(f"<b>{label}</b>", p1x + 10 + (k % 2) * ((PW - 20) / 2), y + (k // 2) * 20, (PW - 20) / 2, 20, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              align="left", rounded=False)
    y += 40 + 8
    plan = [(p1x, 46.0, "Opening paragraph", GRAY_TINT, GRAY, [6]), (p1x, 62.0, sections[0], BLUE_TINT, BLUE, feeders[sections[0]]),
            (p1x, 80.0, sections[1], BLUE_TINT, BLUE, feeders[sections[1]])]
    for px, h, title, fill, stroke, nums in plan:
        bid = block(px, y, h, title, fill, stroke)
        chip(0, y + h / 2, nums, bid)
        y += h + 8
    # page 2: Auditing and the recommendation, then the room left in the two pages
    y = top + 10
    for h, title, fill, stroke, nums in ((80.0, sections[2], BLUE_TINT, BLUE, feeders[sections[2]]), (64.0, "Recommendation", GRAY_TINT, GRAY, rec)):
        bid = block(p2x, y, h, title, fill, stroke)
        chip(c2x, y + h / 2, nums, bid)
        y += h + 8
    d.text("<i>At most two pages in all: the rest of page 2 may stay empty.</i>", p2x + 10, y + 6, PW - 20, 36, size=SMALL, color=GRAY)
    # the appendix: five numbered exhibits
    y = top + 10
    for k, name in enumerate(exhibits):
        label = name[0].upper() + name[1:]
        bid = d.box(f"<b>{k + 1}</b>  {esc(label)}", ax + 8, y, AW - 16, 34, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, size=SMALL, align="left")
        chip(c3x, y + 17, [makers[k]], bid)
        y += 46
    ny = top + PH + 12
    _note(d, "Each section is built from the requirements named beside it, and each exhibit comes from the requirement that made it: Requirement 2 for "
             "Exhibits 1 and 2, Requirement 3 for Exhibit 3, Requirement 4 for Exhibit 4 and Requirement 5 for Exhibit 5. The opening is written in "
             "Requirement 6 once the rest is known, and the recommendation rests on Requirements 4 and 5. Block heights are schematic.", ny)
    return d



FIGURES = {
    "IF-C2-0-A": if_c2_0_a,
    "IF-C2-0-B": if_c2_0_b,
    "IF-C2-1-A": if_c2_1_a,
    "IF-C2-2-A": if_c2_2_a,
    "IF-C2-2-B": if_c2_2_b,
    "IF-C2-3-A": if_c2_3_a,
    "IF-C2-4-A": if_c2_4_a,
    "IF-C2-4-B": if_c2_4_b,
    "IF-C2-5-A": if_c2_5_a,
    "IF-C2-5-B": if_c2_5_b,
    "IF-C2-6-A": if_c2_6_a,
}
