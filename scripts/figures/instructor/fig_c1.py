"""Instructor figures of the Part I case (guides in facts/instructor/guides/case-part-1/)."""

from __future__ import annotations

import re
from datetime import date

import ctx
import excel as xl
import kit
from check_figures import text_width
from data import relate, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, BODY, CORAL, GRAY, GRAY_TINT, HEAD, HIGHLIGHT, INK, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc, money)

CASE = ctx.REPO / "cases" / "part-1-case.qmd"
GUIDES = ctx.REPO / "facts" / "instructor" / "guides" / "case-part-1"
MEMO_GUIDE = GUIDES / "req-6-write-the-data-readiness-memo.md"
NONSEQ = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
DASHED_AMBER = "rounded=0;html=1;fillColor=none;strokeColor=%s;strokeWidth=2;dashed=1;dashPattern=6 3;" % AMBER
STRAIGHT = "edgeStyle=none;"


def _num(x: float) -> str:
    return f"{x:,.2f}"


def _day(text: str) -> int:
    return date.fromisoformat(text).toordinal()


def _expand_box(d: Diagram, x: float, y: float, plus: bool = False) -> None:
    """The minus (or plus) button of a PivotTable item."""
    d.box("", x, y, 11, 11, fill=WHITE, stroke=GRAY, rounded=False)
    d.box("", x + 3, y + 5, 5, 1.5, fill=GRAY, stroke=GRAY, rounded=False)
    if plus:
        d.box("", x + 4.75, y + 3, 1.5, 5, fill=GRAY, stroke=GRAY, rounded=False)


def _dropdown(d: Diagram, x: float, y: float, fill: str = GRAY) -> None:
    """The small filter triangle of a PivotTable field or filter cell."""
    d.vertex("", f"triangle;direction=south;html=1;fillColor={fill};strokeColor=none;", x, y, 9, 7)


def _hatch(d: Diagram, x: float, y: float, w: float, h: float, color: str, step: float = 9) -> None:
    """Diagonal lines (rising to the right) clipped to a rectangle: the pattern of a bar."""
    t = -h + step / 2
    while t < w:
        low = max(y, y + h + t - w)
        high = min(y + h, y + h + t)
        if low < high:
            a = d.anchor(x + t + (y + h - high), high)
            b = d.anchor(x + t + (y + h - low), low)
            d.edge(a, b, color=color, width=1.5, meta=STRAIGHT)
        t += step


# -- IF-C1-0-A: the six requirements, the memo and the workflow stages ------------------------------------------------

# The parts of the memo and the requirements that mainly feed them (the case note's reading; the Requirement 6 guide
# lists every source, and the Auditing section also draws on Requirements 2 to 4).
FEEDS = [("Appendix with the data map and the reconciliation table", (2, 4)), ("Financial reporting", (3, 4)),
         ("Managerial accounting", (5,)), ("Auditing", (5,))]


def _requirements() -> list[dict]:
    """Each requirement of the case text: its number, its title and the chapter tag it carries (None when the
    parentheses name no chapter, as in 'Auditing')."""
    found = []
    for m in re.finditer(r"^\*\*Requirement (\d+): ([^*]+?)\.\*\*", CASE.read_text(encoding="utf-8"), re.M):
        title, tag = m.group(2), None
        parts = re.fullmatch(r"(.+?) \(([^)]*)\)", title)
        if parts:
            title = parts.group(1)
            tag = parts.group(2) if parts.group(2).startswith("Chapter") else None
        found.append(dict(n=int(m.group(1)), title=title, tag=tag))
    assert [r["n"] for r in found] == list(range(1, len(found) + 1)), found
    return found


def if_c1_0_a() -> Diagram:
    """The six requirements, what they feed in the memo and its appendix, and the stages of the workflow."""
    reqs = _requirements()
    stages = ctx.values("case1.g1")["stages"]
    assert len(reqs) == 6 and len(stages) == 6, (len(reqs), len(stages))
    d = Diagram("How the Requirements Feed the Memo and Which Workflow Stages They Complete")
    lx, lw, rh, step = 24.0, 250.0, 60.0, 68.0
    cy = lambda i: i * step + rh / 2
    req_ids = []
    for i, r in enumerate(reqs):
        tag = r["tag"] or "no chapter tag"
        text = f"<b>Requirement {r['n']}:</b> {esc(r['title'])}<br><i>{esc(tag)}</i>"
        assert kit.height_for(text, lw, BODY) <= rh + 0.5, (r, kit.height_for(text, lw, BODY))
        req_ids.append(d.box(text, lx, i * step, lw, rh, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, align="left"))
    # The memo frame with its three sections, and the appendix beside it.
    rx, rw = 470.0, 390.0
    sec_h, sec_gap = 54.0, 10.0
    app_y, app_h = 62.0, 70.0
    frame_y = 170.0
    frame_h = 38 + 3 * sec_h + 2 * sec_gap + 12
    d.box("", rx, frame_y, rw, frame_h, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5, rounded=False)
    d.text("<b>The memo</b> (Requirement 6): one to two pages", rx + 10, frame_y + 5, rw - 20, 22, size=HEAD)
    frame = d.container(rx, frame_y, rw, frame_h)
    targets = {}
    for k, (name, sources) in enumerate(FEEDS):
        who = " and ".join(str(n) for n in sources)
        label = f"<b>{esc(name)}</b><br><i>main input: Requirement{'s' if len(sources) > 1 else ''} {who}</i>"
        if k == 0:
            targets[name] = d.box(label, rx, app_y, rw, app_h, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5)
        else:
            y = frame_y + 38 + (k - 1) * (sec_h + sec_gap)
            targets[name] = d.box(label, rx + 14, y, rw - 28, sec_h, fill=WHITE, stroke=BLUE, stroke_width=1.5)
    for name, sources in FEEDS:
        for n in sources:
            d.arrow(req_ids[n - 1], targets[name], exit=(1, 0.5), entry=(0, 0.5), meta=STRAIGHT)
    # A bus on the left: all six requirements feed the memo.
    bus_x, bottom_y = 8.0, 432.0
    anchors = [d.anchor(bus_x, cy(i)) for i in range(6)]
    for i in range(6):
        d.edge(req_ids[i], anchors[i], color=GRAY, width=1.5, exit=(0, 0.5), meta=STRAIGHT)
    for a, b in zip(anchors, anchors[1:]):
        d.edge(a, b, color=GRAY, width=1.5, meta=STRAIGHT)
    corner = d.anchor(bus_x, bottom_y)
    under = d.anchor(rx + rw / 2, bottom_y)
    d.edge(anchors[-1], corner, color=GRAY, width=1.5, meta=STRAIGHT)
    d.edge(corner, under, color=GRAY, width=1.5, meta=STRAIGHT)
    d.arrow(under, frame, entry=(0.5, 1), meta=STRAIGHT)
    d.box("all six requirements feed the memo", 120, bottom_y - 11, 214, 22, fill=WHITE, stroke=WHITE, size=SMALL,
          rounded=False)
    # The stages of the workflow.
    sy = 478.0
    d.text("<b>The six stages of the analytics workflow</b> (Chapter 1), and what the case completes", 0, sy - 28, 860, 22,
           size=SMALL)
    sw, sg, sh = 130.0, 16.0, 96.0
    for i, st in enumerate(stages):
        part2 = st["status"].startswith("Left")
        by = "Part II" if part2 else st["by"] + (", readiness findings only" if "only" in st["status"] else "")
        text = f"<b>{st['n']} {esc(st['name'])}</b><br>{esc(by)}"
        assert kit.height_for(text, sw, SMALL) <= sh, (st, kit.height_for(text, sw, SMALL))
        if part2:
            d.box(text, i * (sw + sg), sy, sw, sh, fill=WHITE, stroke=GRAY, stroke_width=1.5, size=SMALL, dashed=True)
        else:
            d.box(text, i * (sw + sg), sy, sw, sh, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL)
    ly = sy + sh + 14
    kit.legend(d, 0, ly, [("Completed in the case", BLUE, "box")])
    d.box("", 214, ly + 3, 14, 14, fill=WHITE, stroke=GRAY, rounded=False, dashed=True, stroke_width=1.5)
    d.text("Left for Part II", 234, ly, 110, 20, size=SMALL, valign="middle")
    d.line_sample(366, ly + 10, 28, color=GRAY, end="blockThin")
    d.text("The main input of a part of the memo", 400, ly, 260, 20, size=SMALL, valign="middle")
    d.text("<i>The arrows show the main source of each part. The Requirement 6 guide lists every source: the Auditing "
           "section also draws on Requirements 2 to 4, and the Managerial accounting section on Requirement 2.</i>", 0,
           ly + 30, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-C1-0-B: where the quarters to compare sit on the extract's timeline --------------------------------------------

def if_c1_0_b() -> Diagram:
    """The ledger, invoices and shipments on one timeline, with the quarters to compare and the year-end close."""
    data = ctx.data()
    g = ctx.values("case1.chapter")
    r5 = ctx.values("case1.r5")
    year = g["year"]
    first_post, last_post, last_invoice, last_ship = g["first_post"], g["last_post"], g["last_invoice"], g["last_ship"]
    first_invoice = data.one("SELECT MIN(InvoiceDate) FROM SalesInvoice")
    first_ship = data.one("SELECT MIN(ShipmentDate) FROM Shipment")
    tail_rows, tail_first, tail_last = data.q("SELECT COUNT(*), MIN(PostingDate), MAX(PostingDate) FROM GLEntry "
                                              "WHERE PostingDate > ?", last_invoice)[0]
    tail_types = [r[0] for r in data.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE PostingDate > ?", last_invoice)]
    assert tail_types == ["DisbursementPayment"], tail_types
    assert tail_last == last_post and tail_rows == g["late_rows"], (tail_last, tail_rows)
    assert last_invoice == last_ship == g["q4_end"] == r5["posted"] == f"{year}-12-31", "the year ends on the last sale"
    close = r5["close"]
    X0, X1 = 40.0, 820.0
    lo, hi = _day(first_post), _day(last_post)
    per_day = (X1 - X0) / (hi - lo)
    x_of = lambda s: X0 + (_day(s) - lo) * per_day
    d = Diagram("The Extract on One Timeline")
    ledger_y, inv_y, ship_y, bar_h = 44.0, 84.0, 124.0, 30.0
    axis_y = 192.0
    q3_x, q4_x, end_x = x_of(g["q3_start"]), x_of(g["q4_start"]), x_of(g["q4_end"]) + per_day
    # The two quarters, behind everything else.
    d.box("", q3_x, ledger_y - 8, q4_x - q3_x, axis_y - ledger_y + 8, fill=AMBER_TINT, stroke=AMBER, stroke_width=1.5,
          rounded=False)
    d.box("", q4_x, ledger_y - 8, end_x - q4_x, axis_y - ledger_y + 8, fill=AMBER_TINT, stroke=AMBER, stroke_width=1.5,
          rounded=False)
    for x0, x1, name in ((q3_x, q4_x, "Q3"), (q4_x, end_x, "Q4")):
        d.text(f"<b>{year} {name}</b>", x0, axis_y - 28, x1 - x0, 20, size=SMALL, align="center")
    # The outline of the two quarters, drawn over the bars so that it reads across them.
    band = (q3_x, ledger_y - 8, end_x - q3_x, axis_y - ledger_y + 8)
    d.outline(*band, AMBER, width=2.5, front=True)
    d.vertex("", f"rounded=0;html=1;fillColor={AMBER};strokeColor={AMBER};", q4_x - 0.75, band[1], 1.5, band[3], front=True)
    # The three bars.
    tail_x = x_of(tail_first)
    bars = [(ledger_y, "General ledger", first_post, tail_x - 1), (inv_y, "Sales invoices", first_invoice, end_x),
            (ship_y, "Shipments", first_ship, end_x)]
    spans = {"General ledger": (first_post, last_post), "Sales invoices": (first_invoice, last_invoice),
             "Shipments": (first_ship, last_ship)}
    for y, name, start, stop_x in bars:
        a, b = spans[name]
        d.box(f"<b>{name}</b>  {a} to {b}", x_of(start), y, stop_x - x_of(start), bar_h, fill=BLUE, stroke=BLUE, color=WHITE,
              align="left", rounded=False)
    d.box("", tail_x, ledger_y, x_of(last_post) + per_day - tail_x, bar_h, fill=GRAY, stroke=GRAY, rounded=False)
    # The tail's label, above the ledger bar, with a leader.
    tail_c = (tail_x + x_of(last_post) + per_day) / 2
    d.box(f"<b>only supplier payments</b><br>{tail_rows:,} ledger rows, {tail_first} to {tail_last}", 560, 0, 300, 34,
          fill=WHITE, stroke=GRAY, size=SMALL, rounded=False)
    d.box("", tail_c - 0.75, 34, 1.5, ledger_y - 34, fill=GRAY, stroke=GRAY, rounded=False)
    # The axis, with a tick at each 1 January.
    d.box("", X0, axis_y, X1 - X0, 2, fill=INK, stroke=INK, rounded=False)
    years = list(range(int(first_post[:4]), int(last_post[:4]) + 1))
    for y_ in years:
        x = x_of(f"{y_}-01-01")
        nxt = x_of(f"{y_ + 1}-01-01") if y_ + 1 in years else x_of(last_post) + per_day
        d.box("", x - 0.5, axis_y - 4, 1.5, 10, fill=INK, stroke=INK, rounded=False)
        d.text(str(y_), (x + nxt) / 2 - 20, axis_y + 6, 40, 18, size=SMALL, color=GRAY, align="center")
    d.box("", x_of(last_post) + per_day - 0.5, axis_y - 4, 1.5, 10, fill=INK, stroke=INK, rounded=False)
    # The year-end close: a marker on the last day of the year, with its label to the left.
    cx = x_of(r5["posted"]) + per_day / 2
    label_x, label_w, label_y = 520.0, 236.0, axis_y + 30
    d.box("", cx - 1, axis_y + 6, 2, label_y + 18 - axis_y - 6, fill=CORAL, stroke=CORAL, rounded=False)
    d.box("", label_x + label_w, label_y + 17, cx - label_x - label_w, 2, fill=CORAL, stroke=CORAL, rounded=False)
    d.vertex("", f"rhombus;html=1;fillColor={CORAL};strokeColor={WHITE};strokeWidth=1.5;", cx - 8, axis_y - 7, 16, 16)
    d.box(f"<b>year-end close</b><br>{close}, posted {r5['posted']}", label_x, label_y, label_w, 36, fill=WHITE, stroke=CORAL,
          stroke_width=1.5, size=SMALL, rounded=False)
    # The key and the reading.
    ky = axis_y + 84
    d.box("", 0, ky + 3, 14, 14, fill=AMBER_TINT, stroke=AMBER, stroke_width=1.5, rounded=False)
    d.text(f"The two quarters to compare ({year} Q3 and Q4)", 20, ky, 290, 20, size=SMALL, valign="middle")
    d.box("", 330, ky + 3, 14, 14, fill=GRAY, stroke=GRAY, rounded=False)
    d.text("Ledger rows after the last sale", 350, ky, 200, 20, size=SMALL, valign="middle")
    d.vertex("", f"rhombus;html=1;fillColor={CORAL};strokeColor={WHITE};strokeWidth=1.5;", 568, ky + 2, 16, 16)
    d.text("The year-end close", 590, ky, 140, 20, size=SMALL, valign="middle")
    d.text(f"<i>Ticks mark 1 January. The invoices and the shipments end on {last_invoice}, the last day of fiscal {year}, so "
           f"{year} Q4 is the latest complete quarter. The ledger runs {tail_rows:,} rows further, to {last_post}, but "
           f"they are {tail_types[0].replace('DisbursementPayment', 'supplier payments')} for earlier purchases: no sales, "
           f"no shipments and so no margin. The close, {close}, is posted on the last day of the year, inside Q4.</i>",
           0, ky + 28, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-C1-2-A: the data map of the Furniture margin -------------------------------------------------------------------

def _line_trace(data, doc: str, line: str, key: str) -> tuple[str, str]:
    """Crow's foot ends of the trace from a document's lines to the ledger rows that name them (SourceLineID): the
    line end is optional when a ledger row of the type can leave SourceLineID blank, and the ledger end counts the rows
    that name one line."""
    lo, hi = data.q(f"SELECT MIN(n), MAX(n) FROM (SELECT COUNT(g.GLEntryID) n FROM {line} l LEFT JOIN GLEntry g "
                    f"ON g.SourceDocumentType = ? AND g.SourceLineID = l.{key} GROUP BY l.{key})", doc)[0]
    blank = data.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = ? AND SourceLineID IS NULL", doc)
    orphan = data.one(f"SELECT COUNT(*) FROM GLEntry g WHERE g.SourceDocumentType = ? AND g.SourceLineID IS NOT NULL AND "
                      f"NOT EXISTS (SELECT 1 FROM {line} l WHERE l.{key} = g.SourceLineID)", doc)
    start = "ERzeroToOne" if blank or orphan else "ERmandOne"
    end = ("ERzeroToOne" if hi <= 1 else "ERzeroToMany") if lo == 0 else ("ERmandOne" if hi == 1 else "ERoneToMany")
    return start, end


def _line_rows(data, doc: str, line: str, key: str) -> int:
    """How many ledger rows name each line of the document (the same for every line, asserted)."""
    lo, hi = data.q(f"SELECT MIN(n), MAX(n) FROM (SELECT COUNT(g.GLEntryID) n FROM {line} l LEFT JOIN GLEntry g "
                    f"ON g.SourceDocumentType = ? AND g.SourceLineID = l.{key} GROUP BY l.{key})", doc)[0]
    assert lo == hi, (doc, lo, hi)
    return lo


def if_c1_2_a() -> Diagram:
    """The model data map: the documents, Item, Account and the ledger, with the Furniture accounts highlighted."""
    data = ctx.data()
    r2 = ctx.values("case1.r2")
    rev, cogs, inv = r2["revenue"], r2["cogs"], r2["inventory"]
    for table, cols in {"SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate"],
                        "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "LineTotal"],
                        "Shipment": ["ShipmentID", "ShipmentNumber", "ShipmentDate"],
                        "ShipmentLine": ["ShipmentLineID", "ShipmentID", "ItemID", "ExtendedStandardCost"],
                        "Item": ["ItemID", "ItemGroup", "RevenueAccountID", "COGSAccountID", "InventoryAccountID"],
                        "Account": ["AccountID", "AccountNumber", "AccountName"],
                        "GLEntry": ["GLEntryID", "AccountID", "Debit", "Credit", "SourceDocumentType", "SourceDocumentID",
                                    "SourceLineID"]}.items():
        require_columns(table, cols)
    d = Diagram("The Data Map of the Furniture Margin")
    W, ITEM_W = 190, 230
    rx = 860 - W
    si = d.table("SalesInvoice", 0, 0, [("PK", "SalesInvoiceID"), ("", "InvoiceNumber"), ("", "InvoiceDate")], w=W)
    sil = d.table("SalesInvoiceLine", 0, 152, [("PK", "SalesInvoiceLineID"), ("FK", "SalesInvoiceID"), ("FK", "ItemID"),
                                              ("", "LineTotal")], w=W)
    sh = d.table("Shipment", rx, 0, [("PK", "ShipmentID"), ("", "ShipmentNumber"), ("", "ShipmentDate")], w=W)
    shl = d.table("ShipmentLine", rx, 152, [("PK", "ShipmentLineID"), ("FK", "ShipmentID"), ("FK", "ItemID"),
                                           ("", "ExtendedStandardCost")], w=W)
    ix = (860 - ITEM_W) / 2
    rev_row, cogs_row, inv_row = (f"RevenueAccountID = {rev['id']}", f"COGSAccountID = {cogs['id']}",
                                  f"InventoryAccountID = {inv['id']}")
    item = d.table("Item", ix, 200, [("PK", "ItemID"), ("", "ItemGroup = Furniture"), ("FK", rev_row), ("FK", cogs_row),
                                     ("FK", inv_row)], w=ITEM_W, focus=False, group="Master Data")
    # Account: a sample of the chart, the three Furniture rows highlighted, in the order of the worksheet.
    ay = 410
    heads = ["AccountID", "AccountNumber", "AccountName"]
    ordered = sorted([("revenue", rev), ("cogs", cogs), ("inventory", inv)], key=lambda t: t[1]["id"])
    values = [[str(a["id"]), str(a["number"]), a["name"]] for _, a in ordered]
    cols = [(heads[0], round(text_width("PK  AccountID", SMALL, True) + 14))]
    for c in (1, 2):
        need = max([text_width(heads[c], SMALL, True)] + [text_width(r[c], SMALL, False) for r in values])
        cols.append((heads[c], round(need + 18)))
    aw = sum(w for _, w in cols)
    ax = (860 - aw) / 2
    d.text("<i>Accounting Core</i>", ax, ay - 19, aw, 18, size=SMALL, color=GRAY, valign="bottom")
    d.header_box("Account", ax, ay, aw, fill=GRAY)
    cx = ax
    for k, (name, w) in enumerate(cols):
        label = f'<b><font color="{BLUE}">PK</font>&nbsp;&nbsp;{name}</b>' if k == 0 else f"<b>{name}</b>"
        d.box(label, cx, ay + 30, w, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        cx += w
    acc_rows = {}
    for k, (role, _) in enumerate(ordered):
        y = ay + 54 + k * 24
        cx = ax
        for (name, w), value in zip(cols, values[k]):
            d.box(esc(value), cx, y, w, 24, fill=HIGHLIGHT, stroke=RULE, size=SMALL, align="left", rounded=False)
            cx += w
        acc_rows[role] = (d.container(ax, y, aw, 24), y + 12)
    acc_h = 54 + 3 * 24
    account = d.container(ax, ay, aw, acc_h)
    left_run = ax - 20
    right_runs = {"inventory": ax + aw + 18, "cogs": ax + aw + 36}
    assert left_run > W + 8 and right_runs["cogs"] < rx - 8, (left_run, right_runs, W, rx)
    gx, gw, gy = (860 - 290) / 2, 290, 570
    gl = d.table("GLEntry", gx, gy, [("PK", "GLEntryID"), ("FK", "AccountID"), ("", "Debit"), ("", "Credit"),
                                    ("", "SourceDocumentType"), ("", "SourceDocumentID"), ("", "SourceLineID")], w=gw,
                 focus=False, group="Accounting Core")
    # Joins between the tables (end markers computed from the data).
    relate(d, "SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID", si.id, sil.id, exit=(0.5, 1),
           entry=(0.5, 0))
    relate(d, "Shipment", "ShipmentID", "ShipmentLine", "ShipmentID", sh.id, shl.id, exit=(0.5, 1), entry=(0.5, 0))
    relate(d, "Item", "ItemID", "SalesInvoiceLine", "ItemID", item.rows["ItemID"], sil.rows["ItemID"], color=AMBER,
           exit=(0, 0.5), entry=(1, 0.5), label="ItemID")
    relate(d, "Item", "ItemID", "ShipmentLine", "ItemID", item.rows["ItemID"], shl.rows["ItemID"], color=AMBER,
           exit=(1, 0.5), entry=(0, 0.5), label="ItemID")
    relate(d, "Account", "AccountID", "Item", "RevenueAccountID", acc_rows["revenue"][0], item.rows[rev_row], color=AMBER,
           exit=(0, 0.5), entry=(0, 0.5), points=[(left_run, acc_rows["revenue"][1]), (left_run, item.cy(rev_row))])
    relate(d, "Account", "AccountID", "Item", "COGSAccountID", acc_rows["cogs"][0], item.rows[cogs_row], color=AMBER,
           exit=(1, 0.5), entry=(1, 0.5),
           points=[(right_runs["cogs"], acc_rows["cogs"][1]), (right_runs["cogs"], item.cy(cogs_row))])
    relate(d, "Account", "AccountID", "Item", "InventoryAccountID", acc_rows["inventory"][0], item.rows[inv_row],
           color=AMBER, exit=(1, 0.5), entry=(1, 0.5),
           points=[(right_runs["inventory"], acc_rows["inventory"][1]), (right_runs["inventory"], item.cy(inv_row))])
    relate(d, "Account", "AccountID", "GLEntry", "AccountID", account, gl.id, exit=(0.5, 1), entry=(0.5, 0))
    d.text("SalesInvoiceID", W / 2 + 8, sil.y - 34, 110, 20, size=SMALL, color=GRAY, valign="middle")
    d.text("ShipmentID", rx + W / 2 + 8, shl.y - 34, 76, 20, size=SMALL, color=GRAY, valign="middle")
    # The trace: the three columns of GLEntry that name a document, a header and a line.
    top = gl.y + 30 + 4 * 24
    trace_box = d.container(gx - 4, top - 3, gw + 8, 3 * 24 + 6)
    d.vertex("", DASHED_AMBER, gx - 4, top - 3, gw + 8, 3 * 24 + 6)
    for doc, line, key, src, side in (("SalesInvoice", "SalesInvoiceLine", "SalesInvoiceLineID", sil, "left"),
                                      ("Shipment", "ShipmentLine", "ShipmentLineID", shl, "right")):
        start, end = _line_trace(data, doc, line, key)
        d.edge(src.id, trace_box, start=start, end=end, color=AMBER, dashed=True, width=2.5, exit=(0.5, 1),
               entry=(0 if side == "left" else 1, 0.5))
    n_inv, n_ship = _line_rows(data, "SalesInvoice", "SalesInvoiceLine", "SalesInvoiceLineID"), \
        _line_rows(data, "Shipment", "ShipmentLine", "ShipmentLineID")
    d.text("<b>The trace</b><br>SourceDocumentType<br>= SalesInvoice<br>SourceLineID =<br>SalesInvoiceLineID", W / 2 + 8, 600,
           130, 80, size=SMALL)
    d.text("<b>The trace</b><br>SourceDocumentType<br>= Shipment<br>SourceLineID =<br>ShipmentLineID", rx + W / 2 - 138, 600,
           130, 80, size=SMALL, align="right")
    d.text("AccountID", 438, 540, 80, 20, size=SMALL, color=GRAY, valign="middle")
    # Key and notes.
    ky = gl.bottom + 18
    for i, (label, kind) in enumerate([("Solid gray: a join inside a table group", "gray"),
                                      ("Solid amber: a join to another group", "amber"),
                                      ("Dashed amber: the source-document trace", "dashed"),
                                      ("Orange fill: the Furniture accounts", "fill")]):
        kx, row = (0, 0) if i % 2 == 0 else (400, 0)
        y = ky + (i // 2) * 24
        if kind == "fill":
            d.box("", kx, y + 3, 28, 14, fill=HIGHLIGHT, stroke=RULE, rounded=False)
        else:
            d.line_sample(kx, y + 10, 28, color=GRAY if kind == "gray" else AMBER, dashed=kind == "dashed",
                          width=1.5 if kind == "gray" else 2.5)
        d.text(label, kx + 36, y, 340, 20, size=SMALL, valign="middle")
    words = {n: ("one row" if n == 1 else f"{NONSEQ.get(n, n)} rows") for n in (n_inv, n_ship)}
    d.text(f"<i>The {r2['items']} Furniture items share one revenue, one cost of goods sold and one inventory account, so the "
           f"ItemGroup selects the accounts. The orange rows hold the AccountID that Item stores and the account number the memo "
           f"uses. Crow's feet, "
           f"in the notation of Chapter 3, are computed from the data. The trace names a posting's document by type and by "
           f"the key of its header (SourceDocumentID) and of its line (SourceLineID): each invoice line is named by "
           f"{words[n_inv]} of the ledger and each shipment line by {words[n_ship]}; the rows that post a whole document "
           f"leave SourceLineID blank, so at the ledger end a line is optional.</i>", 0, ky + 54, 860, 70, size=SMALL,
           color=GRAY)
    return d


# -- IF-C1-4-A: the reconciliation table of the appendix ---------------------------------------------------------------

def if_c1_4_a() -> Diagram:
    """The Reconciliation worksheet of the appendix: invoice lines and shipment lines against the ledger."""
    g = ctx.values("case1.g4")
    r4 = ctx.values("case1.r4")
    rev, cogs = r4["revenue"], r4["cogs"]
    recon = g["recon"]
    assert len(recon) == 2 and all(r["revenue_gap"] == 0 and r["cogs_gap"] == 0 for r in recon), "every Difference is zero"
    others = [s for s in g["sources"] if s["source"] != "Shipment"]
    meaning = {"SalesReturn": "cost relieved when goods come back", "JournalEntry": "the year-end closes, one a fiscal year"}
    assert all(s["source"] in meaning for s in others), others
    widths = [36, 96, 124, 160, 206, 130, 108]               # row numbers, then A to F (F stays empty)
    n = len(widths) - 1
    blank = [""] * n
    d = Diagram("The Reconciliation Worksheet")
    xl.formula_bar(d, 0, 0, 860, "E3", "=ROUND(D3-C3,2)")
    y = 40.0
    xl.sheet(d, 0, y, list("ABCDEF"), widths, [], None, show_letters=True)
    y += 22

    def block(title: str, heads: list[str], rows: list[list[str]], number: int, y: float) -> tuple[float, tuple]:
        """A title row, a heading row and a row for each quarter; returns the bottom and the box of the Difference cells."""
        xl.sheet(d, 0, y, [], widths, [(str(number), blank)], row_h=24, show_letters=False)
        d.box(f"<b>{esc(title)}</b>", widths[0], y, sum(widths[1:]), 24, fill=WHITE, stroke=RULE, size=SMALL, align="left",
              rounded=False)
        y += 24
        head_h = 40.0
        xl.sheet(d, 0, y, [], widths, [(str(number + 1), heads + [""])],
                 lambda r, c, v: dict(fill=BLUE_TINT if c < 5 else WHITE, align="left",
                                      label="<b>" + esc(v).replace("&lt;br&gt;", "<br>") + "</b>"),
                 row_h=head_h, show_letters=False)
        y += head_h
        cells = []
        for k, row in enumerate(rows):
            geo = xl.sheet(d, 0, y, [], widths, [(str(number + 2 + k), row + [""])],
                           lambda r, c, v: dict(align="left" if c == 0 else "right"), row_h=24, show_letters=False)
            cells.append(geo[(0, 4)])
            y += 24
        x0, y0, w0, _ = cells[0]
        return y, (x0, y0, w0, cells[-1][1] + cells[-1][3] - y0)

    rev_rows = [[r["label"].replace(" ", "-"), f"{r['invoice_lines']:,}", _num(r["lines"]), _num(r["ledger_revenue"]),
                 _num(r["revenue_gap"])] for r in recon]
    y, rev_diff = block("Furniture revenue: invoice lines against the ledger",
                        ["Quarter", "Invoice lines", "Sum of LineTotal", f"Ledger credits, {rev['number']}<br>from SalesInvoice",
                         "Difference"], rev_rows, 1, y)
    xl.sheet(d, 0, y, [], widths, [("5", blank)], row_h=24, show_letters=False)
    y += 24
    cogs_rows = [[r["label"].replace(" ", "-"), f"{r['shipment_lines']:,}", _num(r["shipped"]), _num(r["ledger_cogs"]),
                  _num(r["cogs_gap"])] for r in recon]
    y, cogs_diff = block("Furniture cost: shipment lines against the ledger",
                         ["Quarter", "Shipment lines", "Standard cost", f"Ledger debits, {cogs['number']}<br>from Shipment",
                          "Difference"], cogs_rows, 6, y)
    xl.sheet(d, 0, y, [], widths, [("10", blank)], row_h=24, show_letters=False)
    y += 24
    direction = lambda s: "credits" if s["credits"] and not s["debits"] else "debits"
    note = (f"Other source document types on {cogs['number']}: " +
            " and ".join(f"{s['source']} ({direction(s)}, {meaning[s['source']]})" for s in others) +
            ". The reconciliation covers Shipment only.")
    xl.sheet(d, 0, y, [], widths, [("11", blank)], row_h=40, show_letters=False)
    d.box(f"<i>{esc(note)}</i>", widths[0], y, sum(widths[1:]), 40, fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left",
          rounded=False)
    y += 40
    for geo in (rev_diff, cogs_diff):
        xl.emphasis(d, *geo)
    xl.sheet_tabs(d, 0, y + 8, xl.workbook_sheets()[-3:] + ["Reconciliation"], "Reconciliation")
    d.text("<i>Outlined: the Difference cells, which read zero for both quarters on both sides. The two blocks are the revenue "
           "and the cost half of the appendix table; the shaded note row names the source document types that also post to "
           "the cost account.</i>", 0, y + 40, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-C1-5-A: the PivotTable that shows what sits behind the naive Q4 revenue ----------------------------------------

def if_c1_5_a() -> Diagram:
    """The GLEntry PivotTable for the Furniture revenue account in the fourth quarter, by source document type."""
    g5 = ctx.values("case1.g5")
    r5 = ctx.values("case1.r5")
    rev = r5["revenue"]
    ledger = g5["ledger"]["revenue4"]
    assert [r["source"] for r in ledger] == ["JournalEntry", "SalesInvoice"], ledger
    je, si = ledger
    assert abs(je["debit"] - r5["close_debit"]) < 0.005 and je["rows"] == 1 and je["credit"] == 0 and si["debit"] == 0
    total_debit, total_credit = je["debit"] + si["debit"], je["credit"] + si["credit"]
    assert total_credit - total_debit < 0 and abs(total_credit - total_debit - r5["rev_all"]) < 0.005
    year = g5["year"]
    periods = g5["periods4"].replace(" and ", ", ")
    d = Diagram("The PivotTable of the Furniture Revenue Account in the Fourth Quarter")
    widths = [36, 220, 170, 170]
    sheet_w = sum(widths)
    xl.sheet(d, 0, 0, ["A", "B", "C"], widths, [], None, show_letters=True)
    y = 22.0
    # The filter area: AccountID, FiscalYear, FiscalPeriod.
    filters = [("AccountID", str(rev["id"])), ("FiscalYear", str(year)), ("FiscalPeriod", "(Multiple Items)")]
    for k, (name, value) in enumerate(filters):
        geo = xl.sheet(d, 0, y, [], widths, [(str(k + 1), [name, value, ""])],
                       lambda r, c, v: dict(align="left", label=("<b>" + esc(v) + "</b>") if c == 0 else esc(v)),
                       show_letters=False)
        bx, by, bw, bh = geo[(0, 1)]
        _dropdown(d, bx + bw - 16, by + 8)
        y += 24
    xl.sheet(d, 0, y, [], widths, [("4", ["", "", ""])], show_letters=False)
    y += 24
    # The body of the PivotTable (compact form).
    body = [("JournalEntry", "group", _num(je["debit"]), _num(je["credit"])),
            (r5["close"], "voucher", _num(je["debit"]), _num(je["credit"])),
            ("SalesInvoice", "group", _num(si["debit"]), _num(si["credit"])),
            ("Grand Total", "grand", _num(total_debit), _num(total_credit))]
    head = xl.sheet(d, 0, y, [], widths, [("5", ["Row Labels", "Sum of Debit", "Sum of Credit"])],
                    lambda r, c, v: dict(fill=BLUE_TINT, align="left" if c == 0 else "right", label=f"<b>{esc(v)}</b>"),
                    show_letters=False)
    hx, hy, hw, hh = head[(0, 0)]
    _dropdown(d, hx + hw - 16, hy + 8)
    y += 24
    start_y = y
    rows = []
    for k, (label, kind, debit, credit) in enumerate(body):
        def style(r, c, v, kind=kind) -> dict:
            text = esc(v)
            if c == 0:
                text = "&nbsp;" * {"group": 5, "voucher": 10, "grand": 0}[kind] + (text if kind == "voucher" else f"<b>{text}</b>")
            elif kind != "voucher":
                text = f"<b>{text}</b>"
            fill = WHITE if kind == "voucher" else BLUE_TINT if kind == "group" else GRAY_TINT
            return dict(fill=fill, label=text, align="left" if c == 0 else "right")
        geo = xl.sheet(d, 0, y, [], widths, [(str(6 + k), [label, debit, credit])], style, show_letters=False)
        rows.append(geo)
        if kind == "group":
            gx, gy, _, _ = geo[(0, 0)]
            _expand_box(d, gx + 8, gy + 6.5, plus=label != "JournalEntry")
        y += 24
    xl.emphasis(d, 36, start_y, sheet_w - 36, 48)                           # the JournalEntry row and its voucher number
    gx, gy, gw, gh = rows[3][(0, 0)]
    xl.select(d, gx - 1, gy - 1, sheet_w - 36 + 2, gh + 2)                  # the Grand Total row
    sheet_bottom = y
    xl.sheet_tabs(d, 0, sheet_bottom + 8, ["Account", "JournalEntry", "GLEntry", "Q4 revenue"], "Q4 revenue")
    # The PivotTable Fields pane.
    px, pw = 628, 232
    d.box("<b>PivotTable Fields</b>", px, 0, pw, 28, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
    areas = [("Filters", ["AccountID", "FiscalYear", "FiscalPeriod"]), ("Columns", ["Σ Values"]),
             ("Rows", ["SourceDocumentType", "VoucherNumber"]), ("Values", ["Sum of Debit", "Sum of Credit"])]
    ay = 36
    for name, chips in areas:
        d.text(f"<b>{name}</b>", px, ay, pw, 20, size=SMALL)
        ay += 20
        height = max(30, 26 * len(chips) + 6)
        d.box("", px, ay, pw, height, fill=WHITE, stroke=RULE, rounded=False)
        for k, chip in enumerate(chips):
            d.box(esc(chip), px + 6, ay + 4 + 26 * k, pw - 12, 22, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left",
                  rounded=False)
            _dropdown(d, px + pw - 26, ay + 4 + 26 * k + 8)
        ay += height + 8
    # What the totals say.
    cy = max(sheet_bottom + 44, 0)
    credit_less = total_credit - total_debit
    kit.callout(d, f"<b>Revenue is credits less debits.</b> The quarter's invoices credit {money(si['credit'])}; the single "
                   f"JournalEntry row, voucher {r5['close']}, debits {money(je['debit'])}. Credits less debits is "
                   f"−{money(abs(credit_less))}: the account's total for the quarter is negative.", 0, cy, sheet_w, color="coral")
    d.text(f"<i>Filters: account {rev['number']} (AccountID {rev['id']}), fiscal {year}, fiscal periods {periods}. Outlined in "
           f"coral: the JournalEntry row and its voucher number. Outlined in blue: the Grand Total row. The SalesInvoice "
           f"item is collapsed.</i>", 0, cy + 76, sheet_w, 52, size=SMALL, color=GRAY)
    return d


# -- IF-C1-5-B: the naive and the corrected margins --------------------------------------------------------------------

def if_c1_5_b() -> Diagram:
    """Furniture gross margin of Q3 and Q4 from all ledger rows and with the year-end close excluded."""
    r5 = ctx.values("case1.r5")
    g5 = ctx.values("case1.g5")
    q3, q4 = g5["ql3"], g5["ql4"]
    all_rows = [r5["naive_q3"], r5["naive_q4"]]
    corrected = [r5["m3"], r5["m4"]]
    assert abs(all_rows[0] - corrected[0]) < 1e-9, "Q3 has no close, so its two bars match"
    assert abs(all_rows[1] - all_rows[0]) < 0.005 and corrected[1] < corrected[0] - 0.005, "the trap hides the decline"
    assert r5["rev_all"] < 0 and r5["cogs_all"] < 0, "the all-rows totals are negative"
    d = Diagram("Furniture Gross Margin from All Ledger Rows and with the Close Excluded")
    plot = kit.Plot(d, 0, 0, 560, 400, f"Furniture gross margin, {q3} and {q4}", y_ticks=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                    categories=[q3, q4], y_fmt=lambda v: f"{v:.0%}", y_title="Revenue less cost of goods sold, over revenue",
                    bottom=30)
    slot = plot.pw / 2
    bw, gap = slot * 0.30, 8.0
    for c in range(2):
        center = plot.px + slot * (c + 0.5)
        for s, (value, name) in enumerate(((all_rows[c], "all"), (corrected[c], "excluded"))):
            x = center - gap / 2 - bw if s == 0 else center + gap / 2
            top, base = plot.y_of(value), plot.y_of(0)
            if name == "all":
                d.box("", x, top, bw, base - top, fill=GRAY, stroke=GRAY, rounded=False)
            else:
                d.box("", x, top, bw, base - top, fill=BLUE, stroke=BLUE, rounded=False)
                _hatch(d, x, top, bw, base - top, WHITE)
            d.text(f"<b>{value:.1%}</b>", x - 10, top - 22, bw + 20, 20, size=SMALL, align="center")
            if name == "all" and c == 1:
                d.marker("!", x + bw / 2 - 12, top - 50, CORAL, size=24)
    # The key.
    ky = 408.0
    d.box("", 0, ky + 3, 14, 14, fill=GRAY, stroke=GRAY, rounded=False)
    d.text("All ledger rows", 20, ky, 110, 20, size=SMALL, valign="middle")
    d.box("", 150, ky + 3, 14, 14, fill=BLUE, stroke=BLUE, rounded=False)
    _hatch(d, 150, ky + 3, 14, 14, WHITE, step=5)
    d.text("Year-end close excluded", 170, ky, 160, 20, size=SMALL, valign="middle")
    d.marker("!", 352, ky - 1, CORAL, size=22)
    d.text("The totals behind the bar are negative", 380, ky, 260, 20, size=SMALL, valign="middle")
    # The panel beside the chart.
    px, pw = 590, 270
    d.box(f"<b>{q4}, all ledger rows</b>", px, 0, pw, 28, fill=CORAL, stroke=CORAL, color=WHITE, size=SMALL, rounded=False)
    kit.callout(d, f"Revenue {'−' + money(abs(r5['rev_all']))}<br>Cost of goods sold {'−' + money(abs(r5['cogs_all']))}<br>"
                   f"Margin {all_rows[1]:.1%}, about {q3}'s {all_rows[0]:.1%}: a plausible ratio of two negative totals, "
                   f"because {r5['close']} is in the rows.", px, 34, pw, color="coral")
    d.box(f"<b>{q4}, year-end close excluded</b>", px, 176, pw, 28, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL,
          rounded=False)
    kit.callout(d, f"Revenue {money(r5['rev4'])}<br>Cost of goods sold {money(r5['cogs4'])}<br>Margin {corrected[1]:.1%}, "
                   f"{(corrected[0] - corrected[1]) * 100:.1f} points below {q3}'s {corrected[0]:.1%}.", px, 210, pw, color="blue")
    d.text(f"<i>The {q3} bars match because no journal entry posts to the two Furniture accounts in that quarter. The axis "
           f"starts at zero. Cost of goods sold is shipments less returns; revenue is the sales invoices.</i>", 0, 438, 860, 36,
           size=SMALL, color=GRAY)
    return d


# -- IF-C1-6-A: the page layout of the memo and its appendix ---------------------------------------------------------

def _memo_table() -> dict[str, tuple[str, str]]:
    """The words and the requirements of each part of the model memo, read from the Requirement 6 guide's table."""
    text = MEMO_GUIDE.read_text(encoding="utf-8")
    start = text.index("| Part | Words | Draws on |")
    rows = {}
    for line in text[start:].splitlines()[2:]:
        if not line.startswith("|"):
            break
        part, words, draws = [c.strip() for c in line.strip("|").split("|")]
        rows[part.split(" (")[0]] = (words, draws)
    return rows


def _mid(words: str) -> float:
    low, high = (int(x) for x in re.findall(r"\d+", words)[:2])
    return (low + high) / 2


def _requirement_numbers(draws: str) -> list[int] | None:
    """'Requirements 3, 5' -> [3, 5]; 'Requirements 2 to 5' -> [2, 3, 4, 5]; 'All' -> None (every requirement)."""
    if draws.strip().lower() == "all":
        return None
    nums = [int(x) for x in re.findall(r"\d+", draws)]
    return list(range(nums[0], nums[1] + 1)) if " to " in draws else nums


def if_c1_6_a() -> Diagram:
    """The model memo and its appendix as two pages, with the word budget of each part."""
    table = _memo_table()
    g4 = ctx.values("case1.g4")
    r2 = ctx.values("case1.r2")
    parts = ["Header and opening paragraph", "Financial reporting", "Managerial accounting", "Auditing", "Recommendation"]
    assert all(p in table for p in parts) and any(k.startswith("Appendix") for k in table), table
    lows = sum(int(re.findall(r"\d+", table[p][0])[0]) for p in parts)
    highs = sum(int(re.findall(r"\d+", table[p][0])[1]) for p in parts)
    labels = [r["label"].replace(" ", "-") for r in g4["recon"]]
    d = Diagram("The Model Memo and Its Appendix")
    pw, gap = 400.0, 60.0
    ax = pw + gap
    top, pad = 30.0, 14.0
    d.text("<b>The memo</b>: one to two pages", 0, 0, pw, 24, size=HEAD)
    d.text("<b>The appendix</b>: one page", ax, 0, pw, 24, size=HEAD)
    scale = 0.3
    heights = {p: round(34 + _mid(table[p][0]) * scale) + 26 for p in parts[1:]}
    opening_h = round(34 + _mid(table[parts[0]][0]) * scale) + 26
    header_h = 46.0
    page_h = pad + header_h + 8 + opening_h + 8 + sum(heights.values()) + 8 * (len(heights) - 1) + pad
    ix, iw = pad, pw - 2 * pad

    def chips(x: float, y: float, draws: str) -> None:
        """'draws on' and one small tag for each requirement the part uses."""
        d.text("draws on", x, y, 56, 18, size=SMALL, color=GRAY, valign="middle")
        x += 58
        nums = _requirement_numbers(draws)
        if nums is None:
            d.box("all the requirements", x, y, 128, 18, fill=WHITE, stroke=GRAY, size=SMALL)
            return
        for n in nums:
            d.box(f"Req. {n}", x, y, 60, 18, fill=WHITE, stroke=BLUE, size=SMALL)
            x += 66

    def page_lines(x: float, y: float, w: float, h: float) -> None:
        """Grey bars that stand for the lines of text in a block."""
        k, row = 0, y
        while row + 6 <= y + h:
            d.box("", x, row, w * (0.62 if k % 4 == 3 else 1.0), 5, fill=RULE, stroke=RULE, rounded=False)
            row += 11
            k += 1

    def block(title: str, words: str, draws: str, h: float, y: float, fill: str, stroke: str) -> None:
        d.box("", ix, y, iw, h, fill=fill, stroke=stroke, stroke_width=1.5, rounded=False)
        d.text(f"<b>{esc(title)}</b>", ix + 8, y + 4, iw - 216, 20, size=SMALL)
        d.text(f"<b>{esc(words)}</b>", ix + iw - 208, y + 4, 200, 20, size=SMALL, align="right")
        page_lines(ix + 10, y + 30, iw - 20, h - 30 - 28)
        chips(ix + 8, y + h - 24, draws)

    d.box("", 0, top, pw, page_h, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
    y = top + pad
    for k, label in enumerate(("To:", "From:", "Date:", "Re:")):
        d.box(f"<b>{label}</b>", ix + (k % 2) * (iw / 2), y + (k // 2) * 23, iw / 2, 23, fill=GRAY_TINT, stroke=RULE,
              size=SMALL, align="left", rounded=False)
    y += header_h + 8
    words, draws = table[parts[0]]
    block("Bottom line first", words + " words, with the header", draws, opening_h, y, GRAY_TINT, GRAY)
    y += opening_h + 8
    for p in parts[1:]:
        words, draws = table[p]
        sections = p != "Recommendation"
        block(p, words + " words", draws, heights[p], y, BLUE_TINT if sections else GRAY_TINT, BLUE if sections else GRAY)
        y += heights[p] + 8
    # The appendix page.
    app = next(v for k, v in table.items() if k.startswith("Appendix"))
    d.box("", ax, top, pw, page_h, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
    half = (page_h - 3 * pad) / 2
    ix2 = ax + pad
    d.box("", ix2, top + pad, iw, half, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, rounded=False)
    d.text("<b>Upper half: the data map</b>", ix2 + 8, top + pad + 4, iw - 16, 20, size=SMALL)
    names = ["Document<br>lines", "Item", "Account", "GLEntry"]
    bw, bg = 76.0, (iw - 16 - 4 * 76.0) / 3
    ids = []
    for k, name in enumerate(names):
        ids.append(d.box(f"<b>{name}</b>", ix2 + 8 + k * (bw + bg), top + pad + 34, bw, 40, fill=WHITE, stroke=GRAY,
                         stroke_width=1.5, size=SMALL))
    for a, b in zip(ids, ids[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5))
    d.text(f"The join paths from the documents to the ledger, each with its key and its cardinality, and the account numbers "
           f"of the Furniture items: {r2['revenue']['number']}, {r2['cogs']['number']} and {r2['inventory']['number']}.",
           ix2 + 8, top + pad + 86, iw - 16, 70, size=SMALL)
    chips(ix2 + 8, top + pad + half - 24, "Requirement 2")
    ly = top + 2 * pad + half
    d.box("", ix2, ly, iw, half, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, rounded=False)
    d.text("<b>Lower half: the reconciliation table</b>", ix2 + 8, ly + 4, iw - 16, 20, size=SMALL)
    heads = ["Quarter", "Documents", "Ledger", "Difference"]
    cw = [72.0, 96.0, 84.0, iw - 16 - 252]
    gy = ly + 34
    cx = ix2 + 8
    for h, w in zip(heads, cw):
        d.box(f"<b>{h}</b>", cx, gy, w, 24, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False, align="left")
        cx += w
    for r in range(2):
        cx = ix2 + 8
        for c, w in enumerate(cw):
            value = [labels[r], "lines, total", "ledger total", "0.00"][c]
            d.box(f"<i>{esc(value)}</i>" if c in (1, 2) else esc(value), cx, gy + 24 * (r + 1), w, 24, fill=WHITE, stroke=RULE,
                  size=SMALL, rounded=False, align="left", color=GRAY if c in (1, 2) else INK)
            cx += w
    d.text("<i>Revenue and cost side by side, both quarters.</i>", ix2 + 8, gy + 24 * 3 + 8, iw - 16, 20, size=SMALL,
           color=GRAY)
    chips(ix2 + 8, ly + half - 24, "Requirement 4")
    assert _requirement_numbers(app[1]) == [2, 4], app
    d.text(f"<i>Block heights follow the word budgets of the model memo, which add up to {lows} to {highs} words; the guide "
           f"keeps the model to about 700. Each tag names a requirement whose results the part uses. The appendix has a map "
           f"and a table and no word budget.</i>", 0, top + page_h + 10, 860, 36, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "IF-C1-0-A": if_c1_0_a,
    "IF-C1-0-B": if_c1_0_b,
    "IF-C1-2-A": if_c1_2_a,
    "IF-C1-4-A": if_c1_4_a,
    "IF-C1-5-A": if_c1_5_a,
    "IF-C1-5-B": if_c1_5_b,
    "IF-C1-6-A": if_c1_6_a,
}
