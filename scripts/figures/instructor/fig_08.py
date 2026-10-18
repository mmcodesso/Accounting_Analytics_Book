"""Instructor figures of Chapter 8 (guides in facts/instructor/guides/chapter-08-audit-analytics/)."""

from __future__ import annotations

from datetime import date, datetime

import ctx
import excel as xl
import kit
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HIGHLIGHT, INK, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
               "December"]
BUCKET_FROM = ["-9999", "1", "31", "61", "91"]                     # the From column of tbl-08-02 (Tutorial 8.2, Step 3)


# -- shared drawing helpers (Excel pieces copied from fig_04) ----------------------------------------------------------------

def _money(x: float) -> str:
    return f"{x:,.2f}"


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow worksheet column shows it."""
    if text_width(text, size, bold) <= width - margin:
        return text
    while text and text_width(text + "…", size, bold) > width - margin:
        text = text[:-1]
    return text + "…"


def _wrap(text: str, width: float, lines: int | None = None, size: int = SMALL, bold: bool = False) -> list[str]:
    """A greedy word wrap measured with text_width; with lines, the text is cut at that many lines and the last ends in an
    ellipsis, as a cell of fixed height shows a long sentence."""
    out, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if not cur or text_width(trial, size, bold) <= width:
            cur = trial
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    if lines and len(out) > lines:
        out = out[:lines]
        last = out[-1]
        while last and text_width(last + "…", size, bold) > width:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        out[-1] = last + "…"
    return out


def _dropdown(d: Diagram, geo: tuple) -> None:
    """The filter button of a Table header: a small white triangle."""
    hx, hy, hw, hh = geo
    d.vertex("", "triangle;direction=south;html=1;fillColor=#FFFFFF;strokeColor=none;", hx + hw - 16, hy + hh / 2 - 3.5, 9, 7)


def _gap(d: Diagram, x: float, y: float, w: float, text: str, h: float = 24) -> float:
    """A band that stands for the rows of a long worksheet that the figure leaves out."""
    d.box(f"<i>{esc(text)}</i>", x, y, w, h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, rounded=False, dashed=True)
    return y + h


def _sheet(d: Diagram, x: float, y: float, letters: list[str], widths: list[float], rows: list[dict],
           number_color: str = GRAY, show_letters: bool = True, row_h: float = 22) -> dict:
    """A worksheet with a letter row and rows of any height.

    widths[0] is the row-number column; letters label the others.  A row is {"n": row number, "cells": [cell, ...],
    "h": height}, its cells taken in order from the first column (a cell with span uses that many columns); a cell is a
    string or a dict: text, bold, italic, align ("left", "right", "center"), color, fill, stroke, html (a ready label),
    span (columns the text overflows across), clip (False keeps a long text whole), valign, filter (True draws the filter
    button of a Table header).  Returns {(row index, column): (x, y, w, h)} and "bottom"."""
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


def _header(text: str, **kw) -> dict:
    """A Table header cell: blue fill, white bold text."""
    return dict(text=text, bold=True, fill=BLUE, stroke=BLUE, color=WHITE, align="left", **kw)


def _head(text: str, align: str = "left", html: str | None = None) -> dict:
    """A heading cell of a plain range: light blue, bold."""
    return dict(html=html or f"<b>{esc(text)}</b>", fill=BLUE_TINT, align=align)


def _formula_bar(d: Diagram, x: float, y: float, w: float, name: str, formula_html: str, h: float = 28) -> None:
    """The Name Box, the fx label and a formula bar."""
    d.box(esc(name), x, y, 90, 28, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.box("<i>fx</i>", x + 94, y, 30, 28, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(formula_html, x + 128, y, w - 128, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)


def _mark(d: Diagram, x: float, y: float, w: float, h: float, color: str = CORAL, inset: float = 0) -> str:
    """An outline like xl.emphasis in a chosen color (a blue outline would vanish on a blue Table header)."""
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


def _lines(text: str, width: float, bold: bool = False) -> int:
    return kit.lines_for(text, width, SMALL, bold)


def _nb(ref: str) -> str:
    """A reference that keeps its number with its word: Exercise 8.5, requirement (6) breaks only at the comma."""
    for word in ("Tutorial", "Exercise", "Exercises", "requirements", "requirement", "Steps", "Step"):
        ref = ref.replace(f"{word} ", f"{word} ")
    return ref.replace(" (", " (").replace(" (2) and (3)", " (2) and (3)")


def _article(word: str) -> str:
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


# -- IF-08-0-A: one entry, three tests -------------------------------------------------------------------------------------

def if_08_0_a() -> Diagram:
    """The opening balance entry at the centre of the receivables reconciliation, the journal entry tests and the payables
    reconciliation."""
    data = ctx.data()
    chapter, ex2 = ctx.values("ch08.chapter"), ctx.values("ch08.ex2")
    t2, t3 = chapter["t2"], chapter["t3"]
    number = t3["number"]
    posted, total, creator, created, approver, title, limit = data.q(
        "SELECT j.PostingDate, j.TotalAmount, j.CreatedByEmployeeID, j.CreatedDate, j.ApprovedByEmployeeID, e.JobTitle, "
        "a.MaxApprovalAmount FROM JournalEntry j JOIN Employee e ON e.EmployeeID = j.CreatedByEmployeeID "
        "JOIN Employee a ON a.EmployeeID = j.ApprovedByEmployeeID WHERE j.EntryNumber = ?", number)[0]
    flags = {"Weekend": datetime.fromisoformat(created).isoweekday() > 5, "Backdated": created[:10] > posted[:10],
             "SelfApproved": creator == approver, "AboveLimit": total > limit, "RoundAmount": total % 1000 == 0}
    on = [k for k, v in flags.items() if v]
    assert len(on) == 4 and t3["scores"][4] == 1 and title == t3["top_title"], (on, t3["scores"])
    lines = {n: (dr, cr) for n, dr, cr in data.q(
        "SELECT a.AccountNumber, SUM(g.Debit), SUM(g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
        "WHERE g.SourceDocumentType = 'JournalEntry' AND g.VoucherNumber = ? AND a.AccountNumber IN (1010, 1020, 2010) "
        "GROUP BY 1", number)}
    ar, ap, cash = lines[1020][0], lines[2010][1], lines[1010][0]
    assert abs(ar - t2["opening"]) < 0.005 and abs(t2["diff"] - ar) < 0.005, "the receivables difference is the entry's line"
    assert abs(ap - ex2["opening"]) < 0.005 and abs(cash - ap) < 0.005, "the payables line is balanced by cash"
    # the payables difference is the opening credit less the two debt reclassifications (the review of 2026-10-16)
    ap_diff, reclassed = ex2["gl"] - ex2["open_ap"], ex2["reclassed"]
    assert abs(ap_diff - (ap - reclassed)) < 0.005 and reclassed > 0, "account 2010 less the open invoices is the opening credit less the reclasses"
    assert abs(total - t3["top_total"]) < 0.005 and t3["olines"] == data.one(
        "SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry' AND VoucherNumber = ?", number)
    d = Diagram("One Journal Entry Reached by Three Tests")
    side_w, hub_x, hub_w = 236, 290, 280
    left_x, right_x = 0, 860 - side_w
    hub_label = (f"<b>{esc(number)}</b><br>Opening balance entry, posted {esc(posted)}<br>"
                 f"Created by the {esc(title.lower())}<br>{t3['olines']} ledger lines, ${total:,.2f} on each side")
    left_label = (f"<b>Receivables reconciliation</b><br>Tutorial 8.2, Step 5<br>Account 1020 less the open invoices: "
                  f"<b>${ar:,.2f}</b>, the entry's debit line to 1020")
    right_label = (f"<b>Payables reconciliation</b><br>Exercise 8.2<br>Account 2010 less the open supplier invoices: "
                   f"<b>${ap_diff:,.2f}</b>. After the two debt reclassifications, ${reclassed:,.2f} in all, the unsupported "
                   f"opening credit to 2010 is <b>${ap:,.2f}</b>. The same entry debits cash by ${cash:,.2f}")
    bottom_label = (f"<b>Journal entry tests</b><br>Tutorial 8.3, Steps 2 and 3<br>The only entry that scores four of five "
                    f"flags: {', '.join(esc(k) for k in on)}. Entry total <b>${total:,.2f}</b>")
    top = 20
    hub_h = kit.height_for(hub_label, hub_w, 13, pad=24)
    side_h = max(kit.height_for(left_label, side_w, 13, pad=20), kit.height_for(right_label, side_w, 13, pad=20), hub_h)
    cy = top + side_h / 2
    hub = d.box(hub_label, hub_x, cy - hub_h / 2, hub_w, hub_h, fill=AMBER_TINT, stroke=AMBER, stroke_width=2.5, align="left")
    left = d.box(left_label, left_x, top, side_w, side_h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, align="left")
    right = d.box(right_label, right_x, top, side_w, side_h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, align="left")
    bot_w = 330
    bot_h = kit.height_for(bottom_label, bot_w, 13, pad=20)
    bot_y = top + side_h + 70
    bot = d.box(bottom_label, 430 - bot_w / 2, bot_y, bot_w, bot_h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, align="left")
    d.arrow(left, hub, exit=(1, 0.5), entry=(0, 0.5), width=2, meta="edgeStyle=none;")
    d.arrow(right, hub, exit=(0, 0.5), entry=(1, 0.5), width=2, meta="edgeStyle=none;")
    d.arrow(bot, hub, exit=(0.5, 0), entry=(0.5, 1), width=2, meta="edgeStyle=none;")
    gap_l, gap_r = hub_x - (left_x + side_w), right_x - (hub_x + hub_w)
    d.text("<b>debit to<br>1020</b>", left_x + side_w, cy - 40, gap_l, 34, size=SMALL, align="center", valign="bottom")
    d.text("<b>credit to<br>2010</b>", hub_x + hub_w, cy - 40, gap_r, 34, size=SMALL, align="center", valign="bottom")
    d.text("<b>score four</b>", 436, (cy + hub_h / 2 + bot_y) / 2 - 10, 120, 20, size=SMALL)
    y = bot_y + bot_h + 18
    _note(d, f"Three routes to one entry. The two reconciliations meet it as an unexplained difference, which for payables is smaller "
             f"than the entry's credit by the two reclassifications, and the journal entry tests as the highest risk score. The other "
             f"amounts are the entry's own lines (the debit to 1020, the credit to 2010 and the matching debit to cash 1010) and its "
             f"total. Amber: the entry; blue: the tests that reach it.", y)
    return d


# -- IF-08-0-B: choosing a test by the kind of records ------------------------------------------------------------------------

def if_08_0_b() -> Diagram:
    """A decision tree read from left to right: the records, then the tests that fit them, each with where the chapter practices it."""
    rows = [
        ("Measured amounts over a wide range",
         [("Strata", "Tutorial 8.1, Steps 3 and 4"), ("First-digit test of the subsets", "Tutorial 8.1, Steps 5 to 8")]),
        ("Documents numbered in a series",
         [("Uniqueness check", "Exercise 8.5, requirement (6)"), ("Gap test", "Exercise 8.5, requirement (6)")]),
        ("Documents approved against a limit",
         [("Flags and a risk score", "Tutorial 8.3, Steps 2 and 3; Exercise 8.5, requirements (2) and (3)"),
          ("Threshold bands", "Exercise 8.5, requirement (4)")]),
        ("Pairs of records that could repeat",
         [("Near-duplicate test on supplier and amount", "Exercise 8.5, requirement (5)"),
          ("The same invoice?", "Exercise 8.5, requirement (5)")]),
        ("A balance that should equal a ledger account",
         [("Reconciliation to the ledger", "Tutorial 8.2, Steps 5 and 6; Exercise 8.2, requirements (2) to (4)"),
          ("Aging", "Tutorial 8.2, Steps 3 and 4; Exercise 8.1, requirement (1)"),
          ("Confirmation sample", "Tutorial 8.2, Step 7")]),
    ]
    rows = [(record, [(name, _nb(ref)) for name, ref in tests]) for record, tests in rows]
    root_w, rec_w, test_w, gap, trunk = 100, 150, 166, 24, 40
    rec_x = root_w + trunk
    test_x = [rec_x + rec_w + gap + k * (test_w + gap) for k in range(3)]
    assert test_x[2] + test_w <= 860
    d = Diagram("Choosing a Test by the Kind of Records")
    row_gap, top = 10, 0
    heights = []
    for record, tests in rows:
        h = max(kit.height_for(f"<b>{record}</b>", rec_w, SMALL, True, pad=14), 46)
        for name, ref in tests:
            h = max(h, (_lines(name, test_w, True) + _lines(ref, test_w)) * 15 + 14)
        heights.append(h)
    total_h = sum(heights) + row_gap * (len(rows) - 1)
    root_h = 56
    root = d.box("<b>What are the records?</b>", 0, top + total_h / 2 - root_h / 2, root_w, root_h, fill=BLUE, stroke=BLUE,
                 color=WHITE, size=SMALL)
    y = top
    for (record, tests), h in zip(rows, heights):
        rec = d.box(f"<b>{record}</b>", rec_x, y, rec_w, h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL)
        d.arrow(root, rec, exit=(1, 0.5), entry=(0, 0.5), width=2)
        previous = rec
        for k, (name, ref) in enumerate(tests):
            fill, stroke = kit.tint("teal")
            box = d.box(f"<b>{esc(name)}</b><br><i>{esc(ref)}</i>", test_x[k], y, test_w, h, fill=fill, stroke=stroke,
                        stroke_width=1.5, size=SMALL)
            d.arrow(previous, box, exit=(1, 0.5), entry=(0, 0.5), width=2, meta="edgeStyle=none;")
            previous = box
        y += h + row_gap
    _note(d, "Read from left to right: the kind of records decides the tests, and each arrow means then. Blue: the records. Teal: the "
             "test, with the tutorial step or exercise requirement that practices it (italic).", y + 6)
    return d


# -- IF-08-1-A: the Aging worksheet of Exercise 8.1 ---------------------------------------------------------------------------

def if_08_1_a() -> Diagram:
    """Exercise 8.1 after requirement 1: the expected credit loss of each bucket beside the aging, and the loss rates in the Buckets Table."""
    data = ctx.data()
    g = ctx.values("ch08.g1")
    rows, total, loss, opening = g["rows"], g["total"], g["loss"], g["opening"]
    asof = f"{data.C}-12-31"
    ledger = data.balance(["1020"], asof)
    assert abs(ledger - total - opening) < 0.005, "the ledger exceeds the open invoices by the opening line"
    assert abs(sum(r["amount"] for r in rows) - total) < 0.005 and abs(sum(r["loss"] for r in rows) - loss) < 0.005
    n_total = sum(r["n"] for r in rows)
    pct = lambda x, places: f"{x * 100:.{places}f}%"
    d = Diagram("The Aging Worksheet with the Expected Credit Loss and the Loss Rates")
    _formula_bar(d, 0, 0, 860, "E4", esc("=ROUND(C4*XLOOKUP(A4,Buckets[Bucket],Buckets[LossRate]),2)"))
    widths = [30, 154, 84, 96, 112, 140, 56, 100, 80]
    letters = list("ABCDEFGH")
    body = [dict(n="1", cells=[dict(text="As-of date", bold=True), dict(text=asof, color=BLUE, bold=True)]),
            dict(n="2", cells=[])]
    head = [_head("Bucket"), _head("Invoices", "right"), _head("Open balance", "right"), _head("Share of balance", "right"),
            _head("Expected credit loss", "right"), _header("From", filter=True), _header("Bucket", filter=True),
            _header("LossRate", filter=True)]
    body.append(dict(n="3", cells=head))
    for i, r in enumerate(rows):
        band = BLUE_TINT if i % 2 == 0 else WHITE
        body.append(dict(n=str(4 + i), cells=[
            dict(text=r["label"], align="left"), f"{r['n']:,}", _money(r["amount"]), pct(r["amount"] / total, 2), _money(r["loss"]),
            dict(text=BUCKET_FROM[i], fill=band), dict(text=r["label"], fill=band, align="left"),
            dict(text=pct(r["rate"], 1), fill=band, color=INK)]))
    body.append(dict(n="9", cells=[dict(text="Total", bold=True), dict(text=f"{n_total:,}", bold=True), dict(text=_money(total), bold=True),
                                   dict(text="100.00%", bold=True), dict(text=_money(loss), bold=True)]))
    body.append(dict(n="10", cells=[]))
    body.append(dict(n="11", cells=[dict(text="Open invoices (sub-ledger)", span=2, clip=False), _money(total)]))
    body.append(dict(n="12", cells=[dict(text="Account 1020 (AccountID 3)", span=2, clip=False), _money(ledger)]))
    body.append(dict(n="13", cells=[dict(text="Difference", span=2, clip=False), _money(ledger - total)]))
    geo = _sheet(d, 0, 36, letters, widths, body)
    xl.select(d, *geo[(3, 4)])                                       # E4
    e9 = geo[(8, 4)]
    xl.emphasis(d, *e9)
    h3, h8 = geo[(2, 7)], geo[(7, 7)]
    _mark(d, h3[0], h3[1], h3[2], h8[1] + h8[3] - h3[1], TEAL)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["OpenInvoices", "Aging", "LedgerAR", "AR Details", "AR by Source"], "Aging")
    _note(d, f"Selected: E4, whose formula is in the bar and is copied to E8. Outlined: the expected credit loss, ${loss:,.2f}, which is "
             f"{pct(loss / total, 2)} of the open balance of ${total:,.2f} (coral), and the LossRate column the exercise adds to the Buckets "
             f"Table, typed as decimals and formatted as percentages (teal). Rows 11 to 13 are the reconciliation of Tutorial 8.2: the "
             f"opening line of ${opening:,.2f} is in neither the aging nor this estimate.", bottom + 34)
    return d


# -- IF-08-2-A: the reconciliation workpaper of Exercise 8.2 -----------------------------------------------------------------

def if_08_2_a() -> Diagram:
    """Exercise 8.2, rows 11 to 18 of the Ex 8.2 worksheet, in two views of the same rows: columns A to F, then G and H."""
    data = ctx.data()
    g, ex2 = ctx.values("ch08.g2"), ctx.values("ch08.ex2")
    recon = g["recon"]
    opening, reclasses = recon[0], recon[1:]
    open_ap, ledger = ex2["open_ap"], ex2["gl"]
    after = ledger + sum(r["amount"] for r in recon)
    assert abs(after - open_ap) < 0.005 and len(reclasses) == 2, "the three items explain the whole difference"
    description = {r["voucher"]: data.one("SELECT Description FROM JournalEntry WHERE EntryNumber = ?", r["voucher"]) for r in recon}
    for r in reclasses:
        assert str(r["invoice_id"]) in description[r["voucher"]], "the entry description names the invoice"
    money = lambda x: f"${x:,.2f}"
    # the explanations, as the model answer words them
    opening_text = (f"The opening balance entry credited accounts payable with {money(-opening['amount'])} on the conversion date, "
                    f"with no supplier invoices behind it. No payment has ever been applied to it (every payment pays an invoice). "
                    f"The same entry debited cash with exactly {money(-opening['amount'])}, a coincidence worth a question. "
                    f"Unsupported, like the opening receivables of Tutorial 8.2.")
    reclass_text = lambda r: (f"Debt Reclass entry: the note-financed capital invoice {r['invoice']} ({money(r['amount'])}) was moved "
                              f"from 2010 to 2110 Notes Payable when a note financed it. No supplier payment will ever settle it, so "
                              f"it stays open in the invoice detail.")
    ledger_fix = ("Unresolved until the conversion records are seen: restore the invoice detail if the liability is valid, "
                  "and correct the ledger only if the balance is shown to be wrong")
    detail_fix = "The invoice detail: close or flag the invoice as settled by the note"
    w1 = [28, 246, 106, 146, 120, 124, 90]
    w2 = [28, 520, 312]
    items = [
        ("Balance of account 2010 per the ledger", "", "", "", "", _money(ledger), "", ""),
        ("Less: opening balance with no invoice detail", opening["voucher"], description[opening["voucher"]], "", "",
         _money(opening["amount"]), opening_text, ledger_fix),
    ] + [("Add: invoice reclassified to notes payable, still open in the detail", r["voucher"], description[r["voucher"]],
          str(r["invoice_id"]), r["invoice"], _money(r["amount"]), reclass_text(r), detail_fix) for r in reclasses] + [
        ("Ledger balance after the reconciling items", "", "", "", "", _money(after), "", ""),
        ("Open supplier invoices (OpenPayables)", "", "", "", "", _money(open_ap), "", ""),
        ("Unexplained difference", "", "", "", "", _money(round(after - open_ap, 2) + 0.0), "", ""),
    ]
    first = 12
    heights = [38]
    for item in items:
        a, _, c, _, _, _, gt, ht = item
        lines = max(_lines(a, w1[1]), _lines(c, w1[3]), _lines(gt, w2[1]) if gt else 1, _lines(ht, w2[2]) if ht else 1)
        heights.append(max(24, lines * 15 + 9))
    d = Diagram("The Ex 8.2 Reconciliation Workpaper")
    _formula_bar(d, 0, 0, 860, f"F{first + len(items) - 1}", esc("=ROUND(F16-F17,2)"))
    heading = [_head("Item"), _head("Voucher"), _head("Entry description (JournalEntries)"), _head("PurchaseInvoiceID", "right"),
               _head("InvoiceNumber"), _head("Amount", "right")]
    rows1 = [dict(n="11", h=heights[0], cells=heading)]
    rows2 = [dict(n="11", h=heights[0], cells=[_head("What it is"), _head("Correction belongs in")])]
    for i, (a, b, c, did, inv, amount, gt, ht) in enumerate(items):
        n = str(first + i)
        total_row = i >= len(items) - 3
        rows1.append(dict(n=n, h=heights[i + 1], cells=[
            dict(text=a, html=f"<b>{esc(a)}</b>" if a.startswith("Unexplained") else esc(a), valign="top"), dict(text=b, valign="top"),
            dict(html=esc(c), valign="top"), dict(text=did, valign="top"), dict(text=inv, valign="top"),
            dict(text=amount, valign="top", bold=total_row and a.startswith("Unexplained"))]))
        rows2.append(dict(n=n, h=heights[i + 1], cells=[dict(html=esc(gt), valign="top"), dict(html=esc(ht), valign="top")]))
    geo = _sheet(d, 0, 36, list("ABCDEF"), w1, rows1)
    last = len(items)                                                    # the index of the difference row
    xl.select(d, *geo[(last, 5)])
    xl.emphasis(d, *geo[(last, 5)])
    y = geo["bottom"] + 12
    d.text("<b>The same rows after scrolling right</b>", 0, y, 400, 20, size=SMALL)
    geo2 = _sheet(d, 0, y + 22, ["G", "H"], w2, rows2)
    bottom = geo2["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 8.1", "Ex 8.2", "Ex 8.2 JE Rows", "Ex 8.2 Pivot", "OpenPayables"], "Ex 8.2")
    _note(d, f"Rows 11 to 18 of the Ex 8.2 worksheet in two views, columns A to F and then G and H. Selected and outlined: F{first + len(items) - 1}, "
             f"whose formula is in the bar, the unexplained difference of zero. The three reconciling rows are the opening entry, a "
             f"negative amount, and the two Debt Reclass entries, positive amounts, because the invoice detail still shows those invoices "
             f"as open. PurchaseInvoiceID is read from each entry's description.", bottom + 34)
    return d


# -- IF-08-4-A: the supplier PivotTable of Exercise 8.4 ---------------------------------------------------------------------------

def if_08_4_a() -> Diagram:
    """The PivotTable of Exercise 8.4: suppliers by payments, the running share, the row that reaches half, and the marks beside it."""
    data = ctx.data()
    g, ex4 = ctx.values("ch08.g4"), ctx.values("ch08.ex4")
    year = str(data.C)
    rows = data.q("SELECT s.SupplierName, SUM(p.Amount) FROM DisbursementPayment p JOIN Supplier s ON s.SupplierID = p.SupplierID "
                  "WHERE substr(p.PaymentDate, 1, 4) = ? GROUP BY s.SupplierName ORDER BY 2 DESC", year)
    ranked = [(name, round(amount, 2)) for name, amount in rows]
    n = len(ranked)
    total = sum(a for _, a in ranked)
    assert n == ex4["suppliers"] == g["year"]["suppliers"] and abs(total - ex4["total"]) < 0.01
    running, marks, shares = 0.0, {}, []
    for rank, (_, amount) in enumerate(ranked, 1):
        running += amount
        shares.append(running / total)
        for mark in (0.5, 0.8, 0.9):
            if mark not in marks and running >= mark * total:
                marks[mark] = rank
    assert (marks[0.5], marks[0.8], marks[0.9]) == (ex4["n50"], ex4["n80"], ex4["n90"]) == (g["year"]["n50"], g["year"]["n80"], g["year"]["n90"])
    n50 = marks[0.5]
    shown = n50 + 3
    first = 4                                                              # the first supplier's row
    last = first + n - 1
    d = Diagram("The Supplier PivotTable with the Running Share of Spending")
    first_mark = f'=COUNTIF(C{first}:C{last},"<"&0.5)+1'
    _formula_bar(d, 0, 0, 860, "F7", esc(first_mark))
    widths = [28, 210, 105, 171, 20, 218, 108]
    letters = list("ABCDEF")
    pivot_head = [dict(html="<b>Row Labels</b> ▾", fill=BLUE_TINT), _head("Sum of Amount", "right"),
                  _head("Running share of spending", "right")]
    side = {0: dict(text="(2) Concentration of the spending", bold=True, span=2, clip=False),
            1: ("Payments in the year", f"{ex4['n']:,}"), 2: ("Suppliers paid", f"{n:,}"), 3: ("Spending", _money(total)),
            4: ("Suppliers making up 50% of spending", str(marks[0.5])), 5: ("Suppliers making up 80% of spending", str(marks[0.8])),
            6: ("Suppliers making up 90% of spending", str(marks[0.9]))}

    def side_cells(k: int) -> list:
        if k not in side:
            return []
        if k == 0:
            return [dict(text="", fill=WHITE), side[0]]
        return [dict(text=""), dict(text=side[k][0], clip=False), dict(text=side[k][1])]

    body = [dict(n="1", cells=[dict(text="FiscalYear", bold=True), dict(html=f"{year} ▾", align="right")]), dict(n="2", cells=[])]
    body.append(dict(n="3", cells=pivot_head + [dict(text="")] + side_cells(0)[1:]))
    for i in range(shown):
        name, amount = ranked[i]
        cells = [name, _money(amount), f"{shares[i] * 100:.2f}%"]
        extra = side_cells(i + 1)
        body.append(dict(n=str(first + i), cells=cells + (extra if extra else [])))
    geo = _sheet(d, 0, 36, letters, widths, body)
    mark_row = 2 + n50                                                      # the row index of rank n50 (the pivot header is index 2)
    assert body[mark_row]["n"] == str(first + n50 - 1)
    a, c = geo[(mark_row, 0)], geo[(mark_row, 2)]
    xl.emphasis(d, a[0], a[1], c[0] + c[2] - a[0], a[3])
    xl.select(d, *geo[(6, 5)])                                              # F7
    e7, f9 = geo[(6, 4)], geo[(8, 5)]
    _mark(d, e7[0], e7[1], f9[0] + f9[2] - e7[0], f9[1] + f9[3] - e7[1], TEAL)
    y = _gap(d, 0, geo["bottom"], sum(widths[:4]), f"rows {first + shown} to {last} hold the other {n - shown} suppliers, to a running share of 100%")
    tail = [dict(n=str(last + 1), cells=[dict(text="Grand Total", bold=True, fill=BLUE_TINT), dict(text=_money(total), bold=True, fill=BLUE_TINT),
                                         dict(text="", fill=BLUE_TINT)])]
    geo2 = _sheet(d, 0, y, [], widths, tail, show_letters=False)
    bottom = geo2["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 8.3", "Ex 8.4", "Ex 8.5", "Ex 8.5 Requisitions"], "Ex 8.4")
    wrong = g["allyears"]
    _note(d, f"The PivotTable is filtered to FiscalYear {year}, sorted from the largest Sum of Amount, with the second Sum of Amount shown as "
             f"% Running Total In, named Running share of spending. Outlined: the row where the share first reaches 50 percent, "
             f"supplier {n50} of {n} (coral). Selected: F7, which counts the suppliers below 50 percent and adds one; F8 and F9 do the same for "
             f"80 and 90 percent, and the three marks are outlined (teal). With the filter left on all years the marks read {wrong['n50']}, {wrong['n80']} and {wrong['n90']}. "
             f"E10 to F12 (the largest supplier) are not shown.", bottom + 34)
    return d


# -- IF-08-5-A: requisitions by band around the approval limit -------------------------------------------------------------------

def if_08_5_a() -> Diagram:
    """Requisitions counted in $50 bands from $4,800: the band just below the $5,000 limit is twice the others."""
    g, ex5 = ctx.values("ch08.g5"), ctx.values("ch08.ex5")
    bands = g["bands"]
    counts = [b["count"] for b in bands]
    limit = g["band_edge"]
    hot = next(i for i, b in enumerate(bands) if abs(b["high"] + 0.01 - limit) < 1e-6)
    assert counts == ex5["bands"] and counts[hot] == g["n_band"] == ex5["band"]
    others = [c for i, c in enumerate(counts) if i != hot]
    assert counts[hot] >= 2 * max(others), "the band below the limit is twice any other"
    d = Diagram("Requisitions by Value Band Around the Approval Limit")
    d.text(f"<b>Purchase requisitions by value, bands of $50 around the ${limit:,.0f} approval limit</b>", 0, 0, 860, 20, size=SMALL)
    labels = [f"${b['low']:,.0f}<br>to ${b['high']:,.2f}" for b in bands]
    top = 26
    plot = kit.Plot(d, 0, top, 860, 360, None, y_ticks=[0, 5, 10, 15, 20], categories=labels, y_fmt=lambda v: f"{v:g}",
                    y_title="Requisitions", bottom=46)
    colors = [HIGHLIGHT if i == hot else GRAY for i in range(len(bands))]
    slot, ratio = plot.pw / len(bands), 0.62
    plot.bars(counts, colors=colors, ratio=ratio)
    for i, c in enumerate(counts):
        _label(d, str(c), plot.px + slot * (i + 0.5), plot.y_of(c) - 22, bold=i == hot)
    cut = plot.px + slot * (hot + 1)                                        # the edge between the band below the limit and the band above it
    plot.line([(hot + 0.5, 20), (hot + 0.5, 0)], color=CORAL, width=2, dashed=True)
    five = [t.lower() for t in ex5["five"]]
    d.box(f"<b>${limit:,.0f}</b>, the approval limit of the {five[0]} and the {five[1]}", cut + 8, plot.y_of(19.5), 300, 44, fill=WHITE,
          stroke=CORAL, color=INK, size=SMALL, stroke_width=1.5, align="left")
    ly = top + 360 + 8
    _swatch(d, 0, ly + 3, HIGHLIGHT, GRAY)
    d.text(f"The band just below the limit: {counts[hot]} requisitions, twice the next highest band ({max(others)})", 22, ly, 560, 20,
           size=SMALL, valign="middle")
    _swatch(d, 560, ly + 3, GRAY)
    d.text("The other bands", 582, ly, 278, 20, size=SMALL, valign="middle")
    _note(d, f"Requisitions counted by RequisitionValue, Quantity times EstimatedUnitCost, in the {g['n_bands']} bands of the exercise, "
             f"from ${g['first_band']:,.0f}; no value falls on a band edge. All {g['n_band']} requisitions of the highlighted band were converted "
             f"to orders and {g['n_band_unapproved']} of them have no approver, the requisitions of Exercise 2.5.", ly + 30)
    return d


# -- IF-08-5-B: the flagged purchase orders with their dispositions ----------------------------------------------------------------

def _flagged_orders(data) -> list[dict]:
    """The orders of Exercise 8.5 with a RiskScore of 1 or more, as the model answer's POApprovals Table sorts them."""
    emp = {r[0]: dict(name=r[1], title=r[2], limit=r[3], term=r[4]) for r in data.q(
        "SELECT EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount, TerminationDate FROM Employee")}
    out = []
    for pid, number, ordered, creator, approver, total in data.q(
            "SELECT PurchaseOrderID, PONumber, OrderDate, CreatedByEmployeeID, ApprovedByEmployeeID, OrderTotal "
            "FROM PurchaseOrder ORDER BY PurchaseOrderID"):
        a = emp[approver]
        flags = dict(self=creator == approver, above=total > a["limit"], term=a["term"] is not None and a["term"] < ordered)
        if any(flags.values()):
            out.append(dict(number=number, date=ordered, total=total, creator=emp[creator], approver=a, flags=flags,
                            score=sum(flags.values())))
    out.sort(key=lambda o: -o["score"])                                       # a stable sort keeps the order of the Table
    return out


def _disposition(o: dict, capital: dict) -> tuple[str, str]:
    """(Design or operation, Disposition) in the model answer's words, by the pattern of the order's flags."""
    f, a, c = o["flags"], o["approver"], o["creator"]
    on = tuple(k for k in ("self", "above", "term") if f[k])
    money = lambda x: f"${x:,.2f}"
    cap = capital.get(o["number"])
    if on == ("self", "above") and cap:
        return ("Possibly design and operation",
                f"Follow up: the note-financed capital purchase behind invoice {cap['invoice']} (Exercise 8.2), {money(o['total'])}, "
                f"created and approved by the {a['title'].lower()}, {a['name']}, far above the approval limit of {money(a['limit'])}. "
                f"No recorded limit, the chief financial officer's included, reaches {money(o['total'])}: request the board's approval.")
    if on == ("self", "above") and a["limit"] == 0:
        return ("Possibly design and operation",
                f"Follow up: created and approved by the same {a['title'].lower()}, {a['name']}, whose approval limit is $0, on "
                f"{o['date']}. The records show no approval of the order of {money(o['total'])} by anyone with authority. Vouch it "
                f"to its receipt and invoice.")
    if on == ("self",) and o["total"] <= a["limit"]:
        return ("Possibly design",
                f"Follow up, low risk: created and approved by the {a['title'].lower()}, {a['name']}, within the limit of "
                f"{money(a['limit'])}. The amount is within authority, but the records show no second approval.")
    if on == ("above", "term") and a["limit"] == 0:
        return ("Possibly design and operation",
                f"Follow up: approved by {a['name']}, {_article(a['title'].lower())} terminated on {a['term']}, on an order dated "
                f"{o['date']}, created by {o['creator']['name']}. The approver's recorded termination precedes the order date.")
    if on == ("above",) and a["limit"] > 0:
        return ("Possibly operation",
                f"Follow up: approved by the {a['title'].lower()}, {a['name']}, for {money(o['total'])}, "
                f"{money(o['total'] - a['limit'])} above the limit of {money(a['limit'])}, on {o['date']}. Ask why the order was not "
                f"sent to an approver with enough authority.")
    raise AssertionError(f"no disposition pattern fits {o['number']} ({o['flags']})")


def if_08_5_b() -> Diagram:
    """Exercise 8.5, the flagged purchase orders pasted as values: the three flags, RiskScore, a wrapped Disposition and the classification."""
    data = ctx.data()
    g, ex5, g2 = ctx.values("ch08.g5"), ctx.values("ch08.ex5"), ctx.values("ch08.g2")
    capital = {r["po"]: r for r in g2["recon"] if r["kind"] == "reclass"}
    flagged = _flagged_orders(data)
    assert len(flagged) == ex5["s1"] + ex5["s2"] and sum(1 for o in flagged if o["score"] == 2) == ex5["s2"]
    assert set(capital) <= {o["number"] for o in flagged}
    names = [r[1] for r in data.q("PRAGMA table_info(PurchaseOrder)")]
    assert names[:3] == ["PurchaseOrderID", "PONumber", "OrderDate"]
    # POApprovals as the model answer pastes it: PurchaseOrder's PONumber, OrderDate, OrderTotal, the creator and approver
    # columns, then the three flags, RiskScore and the two columns the student adds.
    letters = {"PONumber": "A", "SelfApproved": "I", "AboveLimit": "J", "AfterTermination": "K", "RiskScore": "L",
               "Disposition": "M", "Provisional classification": "N"}
    visible = list(letters.values())
    widths = [30, 112, 94, 82, 112, 78, 252, 100]
    total_w = sum(widths)
    assert total_w <= 860, total_w
    widths[6] += 860 - total_w                                              # the Disposition column takes what is left
    wrap_w = widths[6] - 22
    first_row = 16                                                          # the header is row 15 of the Ex 8.5 worksheet
    head = [_head("PONumber"), _head("SelfApproved", "center"), _head("AboveLimit", "center"), _head("AfterTermination", "center"),
            _head("RiskScore", "center"), _head("Disposition"), _head("", html="<b>Provisional<br>classification</b>")]
    body = [dict(n="14", h=22, cells=[dict(text="Flagged orders, sorted by RiskScore, pasted as values with a disposition (as in Tutorial 8.3)",
                                            bold=True, span=7, clip=False, fill=WHITE)]),
            dict(n="15", h=38, cells=head)]
    capital_rows = []
    for i, o in enumerate(flagged):
        kind, text = _disposition(o, capital)
        assert text.startswith("Follow up")
        lines = _wrap(text, wrap_w, 2)
        flag = lambda on: dict(text="TRUE" if on else "FALSE", align="center", bold=on, color=CORAL if on else GRAY)
        body.append(dict(n=str(first_row + i), h=34, cells=[
            dict(text=o["number"]), flag(o["flags"]["self"]), flag(o["flags"]["above"]), flag(o["flags"]["term"]),
            dict(text=str(o["score"]), align="center", bold=True),
            dict(html="<br>".join(esc(x) for x in lines), align="left"),
            dict(html=esc(kind).replace(" and ", "<br>and ") if " and " in kind else esc(kind).replace("Possibly ", "Possibly<br>"),
                 align="left")]))
        if o["number"] in capital:
            capital_rows.append(i + 2)
    d = Diagram("The Flagged Purchase Orders with Their Dispositions")
    top = _gap(d, 0, 0, 860, "rows 1 to 13 hold the counts of Step 2 and are scrolled out of view")
    geo = _sheet(d, 0, top, visible, widths, body)
    for r in capital_rows:
        x0, y0, _, h0 = geo[(r, 0)]
        x1, _, w1, _ = geo[(r, 6)]
        _mark(d, x0, y0, x1 + w1 - x0, h0, CORAL, inset=1.5)
    bottom = geo["bottom"] + 8
    xl.sheet_tabs(d, 0, bottom, ["Ex 8.4", "Ex 8.5", "Ex 8.5 Requisitions", "Ex 8.5 Payments", "Approvers"], "Ex 8.5")
    cap_numbers = " and ".join(sorted(capital))
    _note(d, f"Columns {_hidden_text(visible, 14)} (OrderDate to ApproverTerminationDate) are hidden. {len(flagged)} orders score 1 or more: {ex5['s2']} score 2, "
             f"then {ex5['s1']} score 1, in the order of the Table. Outlined: the two note-financed capital purchases of Exercise 8.2, "
             f"{cap_numbers}. Each Disposition starts with Follow up and continues beyond the row; the classification is provisional until "
             f"the policy, the configuration and the access logs are seen.", bottom + 34)
    return d


# -- IF-08-6-A: the three flagged promotions ------------------------------------------------------------------------------------------

def if_08_6_a() -> Diagram:
    """Each flagged promotion's recorded window against the months in which its lines were ordered and invoiced."""
    data = ctx.data()
    ex6 = ctx.values("ch08.ex6")
    flagged = ex6["flagged"]
    spans = {}
    for p in flagged:
        r = data.q("SELECT MIN(o.OrderDate), MAX(o.OrderDate), MAX(si.InvoiceDate), COUNT(*) FROM SalesInvoiceLine l "
                   "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID "
                   "WHERE l.PromotionID = ?", p["id"])[0]
        spans[p["id"]] = r
    label_w, x0, month_w = 200, 208, 54
    months_x = lambda m, frac=0.0: x0 + (m - 1 + frac) * month_w                      # m in 1..12, frac a fraction of the month
    days_in = lambda y, m: (date(y + (m == 12), m % 12 + 1, 1) - date(y, m, 1)).days

    def pos(text: str) -> float:
        dt = date.fromisoformat(text[:10])
        return months_x(dt.month, (dt.day - 1) / days_in(dt.year, dt.month))

    d = Diagram("The Flagged Promotions, Their Recorded Windows and Their Order Months")
    row_h, top = 100, 26
    for m in range(12):
        d.text(MONTHS[m], months_x(m + 1), 0, month_w, 18, size=SMALL, color=GRAY, align="center")
    n = len(flagged)
    for m in range(13):
        d.box("", months_x(m + 1), 22, 1, n * row_h + 4, fill=RULE, stroke=RULE, rounded=False)
    for k in range(n + 1):
        d.box("", 0, top - 4 + k * row_h, 860, 1, fill=RULE, stroke=RULE, rounded=False)
    for k, p in enumerate(flagged):
        y0 = top + k * row_h
        first_order, last_order, last_invoice, count = spans[p["id"]]
        year = int(p["start"][:4])
        assert first_order[:4] == last_order[:4] == str(year) and last_invoice[:4] == str(year), "one calendar year"
        om = sorted({int(first_order[5:7]), int(last_order[5:7])})
        order_months = list(range(om[0], om[-1] + 1))
        assert count == ex6["flagged_lines"][k]["n"]
        lm = int(last_invoice[5:7])
        assert lm > om[-1] and first_order > p["end"], "ordered after the recorded end, invoiced later still"
        # the label column
        lines = ex6["flagged_lines"][k]
        d.text(f"<b>{esc(p['code'])}</b><br>{esc(p['collection'])} collection, {p['pct']:.0%} off, {year}<br>"
               f"{lines['n']} lines, ${lines['discount']:,.2f} of discount", 0, y0 + 6, label_w, 56, size=SMALL)
        # the recorded window
        sx, my = pos(p["start"]), y0 + 16
        days = (date.fromisoformat(p["start"]) - date.fromisoformat(p["end"])).days
        if days == 0:
            d.vertex("", f"ellipse;html=1;fillColor={WHITE};strokeColor={CORAL};strokeWidth=2.5;", sx - 7, my - 7, 14, 14)
            window = f"Recorded window: {p['start']} to {p['end']}, one day"
        else:
            d.box("", sx - 40, my - 8, 40, 16, fill=WHITE, stroke=CORAL, stroke_width=2.5, rounded=False)
            d.edge(d.anchor(sx - 6, my), d.anchor(sx - 34, my), end="blockThin", color=CORAL, width=2, meta="edgeStyle=none;", marker_size=7)
            window = f"Recorded window: {p['start']} to {p['end']}, ends {days} day{'s' if days > 1 else ''} before it starts"
        d.box(esc(window), sx + 12, my - 10, text_width(window, SMALL, False) + 16, 20, fill=WHITE, stroke=WHITE, size=SMALL,
              rounded=False, align="left")
        # the months of ordering and of invoicing
        by, bh = y0 + 42, 24
        bx0, bx1 = months_x(om[0]), months_x(om[-1] + 1)
        d.box("", bx0, by, bx1 - bx0, bh, fill=BLUE, stroke=BLUE, rounded=False)
        d.box("", bx1, by, months_x(lm + 1) - bx1, bh, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, rounded=False)
        span = (f"{MONTH_NAMES[om[0] - 1]} to {MONTH_NAMES[om[-1] - 1]}" if om[0] != om[-1] else MONTH_NAMES[om[0] - 1])
        said = f"Ordered {span}, invoiced through {MONTH_NAMES[lm - 1]}"
        d.box(esc(said), bx0, by + bh + 4, text_width(said, SMALL, False) + 16, 20, fill=WHITE, stroke=WHITE, size=SMALL,
              rounded=False, align="left")
    ly = top + n * row_h + 10
    d.box("", 0, ly + 1, 26, 14, fill=WHITE, stroke=CORAL, stroke_width=2.5, rounded=False)
    d.text("Recorded effective window (not to scale)", 34, ly - 2, 260, 20, size=SMALL, valign="middle")
    _swatch(d, 310, ly + 1, BLUE)
    d.text("Months in which the lines were ordered", 332, ly - 2, 290, 20, size=SMALL, valign="middle")
    _swatch(d, 628, ly + 1, BLUE_TINT, BLUE)
    d.text("Months of later invoicing", 650, ly - 2, 210, 20, size=SMALL, valign="middle")
    ends = [(date.fromisoformat(p["start"]) - date.fromisoformat(p["end"])).days for p in flagged]
    phrase = lambda e: "on its start date" if e == 0 else f"{e} day{'s' if e > 1 else ''} before its start"
    _note(d, f"Each row is the calendar year of its promotion, January to December. The recorded window is drawn 14 to 40 px wide so that "
             f"it shows: its end falls {', '.join(phrase(e) for e in ends[:-1])} and {phrase(ends[-1])}. Every line of each promotion was "
             f"ordered after its recorded end and invoiced in the months that followed.", ly + 26)
    return d


# -- IF-08-6-B: order lines after the end of their price list ----------------------------------------------------------------------------

def if_08_6_b() -> Diagram:
    """Order lines dated after the end of their price list, by list and by fiscal year of the order."""
    data = ctx.data()
    ex6 = ctx.values("ch08.ex6")
    years = list(data.years)
    lists = {e["id"]: e for e in ex6["expired"]}
    per = ex6["per_list"]
    counts = {p["id"]: {y: dict(p["years"]).get(y, 0) for y in years} for p in per}
    assert sum(sum(c.values()) for c in counts.values()) == ex6["after"], "the groups add up to the lines after the list's end"
    colors = [BLUE, TEAL, GRAY]
    assert len(years) <= len(colors)
    d = Diagram("Order Lines Dated After the End of Their Price List")
    d.text("<b>Order lines whose OrderDate is after the end of their price list, by list and by year of the order</b>", 0, 0, 860, 20,
           size=SMALL)
    lx = 0
    for y, color in zip(years, colors):
        _swatch(d, lx, 28, color)
        d.text(f"Orders of {y}", lx + 20, 25, 110, 20, size=SMALL, valign="middle")
        lx += 140
    top = 52
    height = 390
    peak = max(max(c.values()) for c in counts.values())
    step = 1000 if peak > 2500 else 500
    ticks = list(range(0, int((peak // step + 1) * step) + 1, step))
    plot = kit.Plot(d, 0, top, 860, height, None, y_ticks=ticks, categories=[""] * len(per), y_fmt=lambda v: f"{v:,.0f}",
                    y_title="Order lines after the end of their list", bottom=92)
    slot = plot.pw / len(per)
    bw, gap = 58, 8
    group_w = len(years) * bw + (len(years) - 1) * gap
    for i, p in enumerate(per):
        gx = plot.px + slot * i + (slot - group_w) / 2
        for j, (y, color) in enumerate(zip(years, colors)):
            value = counts[p["id"]][y]
            bx = gx + j * (bw + gap)
            ytop = plot.y_of(value)
            if value:
                d.box("", bx, ytop, bw, plot.y_of(0) - ytop, fill=color, stroke=color, rounded=False)
            _label(d, f"{value:,}", bx + bw / 2, ytop - 22)
            d.text(str(y), bx, plot.y_of(0) + 4, bw, 18, size=SMALL, align="center")
        lst = lists[p["id"]]
        extra = f"<br>(before its start, {lst['start']})" if lst["end"] < lst["start"] else ""
        d.text(f"<b>List {lst['id']}, {esc(lst['segment'])}</b><br>ended {esc(lst['end'])}{extra}", plot.px + slot * i, plot.y_of(0) + 26,
               slot, 52, size=SMALL, align="center")
    bottom = top + height + 8
    every = [p for p in per if p["all"]]
    tail = (f" Every one of the {every[0]['n']:,} order lines that cite list {every[0]['id']} counts, because its end date is before "
            f"its start date." if every else "")
    _note(d, f"Order lines are counted by the fiscal year of their order date. The end date of each list is in its label, and none of "
             f"the lists has a successor.{tail}", bottom)
    return d


FIGURES = {
    "IF-08-0-A": if_08_0_a, "IF-08-0-B": if_08_0_b, "IF-08-1-A": if_08_1_a, "IF-08-2-A": if_08_2_a, "IF-08-4-A": if_08_4_a,
    "IF-08-5-A": if_08_5_a, "IF-08-5-B": if_08_5_b, "IF-08-6-A": if_08_6_a, "IF-08-6-B": if_08_6_b,
}
