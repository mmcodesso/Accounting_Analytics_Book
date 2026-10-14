"""Instructor figures of Chapter 1 (guides in facts/instructor/guides/chapter-01-role-of-analytics/)."""

from __future__ import annotations

import ctx
import excel as xl
import kit
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL, TEAL_TINT, WHITE,
                    Diagram, esc)

POPUP_ITEMS = 8        # rows of the filter list drawn in IF-01-2-B


def _money(x: float) -> str:
    return f"${x:,.2f}"


def _num(x: float) -> str:
    """A number as an Excel General cell shows it: 51.0 reads 51, 688.42 reads 688.42."""
    text = f"{x:.15g}"
    return text


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow worksheet column shows it."""
    if text_width(text, size, False) <= width - margin:
        return text
    while text and text_width(text + "…", size, False) > width - margin:
        text = text[:-1]
    return text + "…"


def _col_widths(headers: list[str], rows: list[list[str]], extra: dict[int, float] | None = None,
                pad: float = 18, floor: float = 54) -> list[float]:
    """Each column as wide as its bold header or its widest value, plus padding; extra adds room (a filter button)."""
    out = []
    for c, head in enumerate(headers):
        need = max([text_width(head, SMALL, True)] + [text_width(r[c], SMALL, False) for r in rows])
        out.append(round(max(floor, need + pad + (extra or {}).get(c, 0))))
    return out


# -- IF-01-0-A: the table groups behind each exercise ----------------------------------------------------------------

# The tables that each exercise's model answer names in its solution steps.  "main" tables carry the evidence the
# answer is built on; "support" tables are named for one point (a lookup, a check or a second source).  Table names
# are those of the guides (facts/instructor/guides/chapter-01-role-of-analytics/ex-1.N-*.md, Step-by-step solution).
EXERCISES = [
    ("1.1", "Reporting cycle", "Financial",
     ["SalesInvoice", "SalesInvoiceLine", "CreditMemo", "CashReceipt", "CashReceiptApplication", "Customer", "Shipment",
      "ShipmentLine", "GLEntry", "Account", "JournalEntry"],
     ["Item", "WorkOrder", "MaterialIssue", "ProductionCompletion", "WorkOrderClose"]),
    ("1.2", "Revenue path", "Financial",
     ["SalesOrder", "SalesOrderLine", "Shipment", "SalesInvoice", "CashReceipt", "CashReceiptApplication", "GLEntry"],
     []),
    ("1.3", "Cost analysis", "Managerial",
     ["WorkOrder", "BillOfMaterial", "MaterialIssue", "ProductionCompletion", "WorkOrderClose", "CostCenter", "Budget",
      "BudgetLine", "GLEntry", "LaborTimeEntry", "PayrollRegister"],
     ["Item"]),
    ("1.4", "Four types", "Managerial",
     ["ProductionCompletion", "ProductionCompletionLine", "WorkOrderClose", "WorkOrder", "DemandForecast", "WorkCenter",
      "WorkCenterCalendar", "RoutingOperation", "RoughCutCapacityPlan"],
     ["Item", "LaborTimeEntry"]),
    ("1.5", "Audit data", "Auditing",
     ["SalesInvoice", "Customer", "CashReceipt", "CashReceiptApplication", "CreditMemo", "GLEntry", "Account",
      "DisbursementPayment", "PurchaseInvoice", "Supplier", "JournalEntry"],
     ["Employee"]),
    ("1.6", "Journal entries", "Auditing", ["JournalEntry", "GLEntry"], ["Employee"]),
]

# Tables that Table 1.3 does not list as key tables, with the group the dataset documentation puts them in.
OTHER_TABLES = {
    "Order-to-Cash": ["SalesInvoiceLine", "ShipmentLine", "CashReceiptApplication", "CreditMemo"],
    "Procure-to-Pay": ["Supplier"],
    "Manufacturing": ["ProductionCompletionLine", "WorkCenter", "WorkCenterCalendar", "RoutingOperation"],
}


def _group_of() -> dict[str, str]:
    """Table -> table group: the key tables of Table 1.3 (read from the chapter), then the other tables."""
    groups = ctx.values("ch01.chapter")["groups"]
    found = {t: g for g, tables in groups for t in tables}
    for prefix, tables in OTHER_TABLES.items():
        group = next(name for name, _ in groups if name.startswith(prefix))
        for t in tables:
            found.setdefault(t, group)
    existing = {r[0] for r in ctx.data().q("SELECT name FROM sqlite_master WHERE type = 'table'")}
    named = {t for _, _, _, main, support in EXERCISES for t in main + support}
    missing = sorted(t for t in named if t not in found or t not in existing)
    if missing:
        raise ValueError(f"tables with no group or no worksheet: {missing}")
    return found


def if_01_0_a() -> Diagram:
    """A matrix of table groups against the six exercises: main evidence and support (Chapter 1 note)."""
    groups = [name for name, _ in ctx.values("ch01.chapter")["groups"]]
    group_of = _group_of()
    state: dict[tuple[str, str], str] = {}
    for number, _, _, main, support in EXERCISES:
        for g in groups:
            if any(group_of[t] == g for t in main):
                state[(g, number)] = "main"
            elif any(group_of[t] == g for t in support):
                state[(g, number)] = "support"
    n = len(EXERCISES)
    head_w, last_w = 196, 76
    col_w = (860 - head_w - last_w) / n
    d = Diagram("Table Groups Behind the Chapter 1 Exercises")
    # Perspective band, then the column headings.
    for first in range(0, n, 2):
        persp = EXERCISES[first][2]
        d.box(f"<b>{persp}</b>", head_w + first * col_w, 0, 2 * col_w, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              rounded=False)
    d.box("<b>Table group</b>", 0, 24, head_w, 46, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False,
          align="left")
    for i, (number, label, _, _, _) in enumerate(EXERCISES):
        d.box(f"<b>{number}</b><br>{label}", head_w + i * col_w, 24, col_w, 46, fill=GRAY, stroke=RULE, color=WHITE,
              size=SMALL, rounded=False)
    d.box("<b>Main in</b>", head_w + n * col_w, 24, last_w, 46, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL,
          rounded=False)
    row_h = 30
    counts: dict[str, tuple[int, int]] = {}
    for r, group in enumerate(groups):
        y = 70 + r * row_h
        d.box(f"<b>{esc(group)}</b>", 0, y, head_w, row_h, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False,
              align="left")
        for i, (number, *_rest) in enumerate(EXERCISES):
            x = head_w + i * col_w
            kind = state.get((group, number))
            if kind == "main":
                d.box("<b>main</b>", x, y, col_w, row_h, fill=BLUE, stroke=RULE, color=WHITE, size=SMALL, rounded=False)
            elif kind == "support":
                d.box("support", x + 2, y + 2, col_w - 4, row_h - 4, fill=WHITE, stroke=BLUE, stroke_width=2, size=SMALL,
                      rounded=False)
            else:
                d.box("", x, y, col_w, row_h, fill=WHITE, stroke=RULE, rounded=False)
        n_main = sum(1 for e in EXERCISES if state.get((group, e[0])) == "main")
        n_support = sum(1 for e in EXERCISES if state.get((group, e[0])) == "support")
        counts[group] = (n_main, n_support)
        d.box(f"{n_main} of {n}", head_w + n * col_w, y, last_w, row_h, fill=WHITE, stroke=RULE, size=SMALL, rounded=False)
    bottom = 70 + len(groups) * row_h
    # Key and the sentences the data support.
    ly = bottom + 14
    d.box("<b>main</b>", 0, ly, 62, 22, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
    d.text("The group's tables carry the evidence the model answer is built on.", 68, ly, 380, 22, size=SMALL,
           valign="middle")
    d.box("support", 462, ly, 62, 22, fill=WHITE, stroke=BLUE, stroke_width=2, size=SMALL, rounded=False)
    d.text("Named in the answer for one point: a lookup, a check or a second source.", 530, ly - 6, 330, 34, size=SMALL,
           valign="middle")
    ranked = sorted(groups, key=lambda g: (-counts[g][0], groups.index(g)))
    first, second = ranked[0], ranked[1]
    only_support = [g for g in groups if counts[g][0] == 0 and counts[g][1] > 0]
    unused = [g for g in groups if counts[g] == (0, 0)]
    sentences = [f"{first} is the main evidence in {counts[first][0]} of {n} exercises and {second} in "
                 f"{counts[second][0]}."]
    if only_support:
        sentences.append(f"{', '.join(only_support)} appears only as support.")
    if unused:
        sentences.append(f"No exercise draws on {' or '.join(unused)}.")
    sentences.append("A filled cell marks a group, not a count of tables: it can stand for one table or for six.")
    d.text("<i>" + " ".join(sentences) + " Rows are the groups of Table 1.3; tables it does not list, such as the line "
           "tables and the work center tables, are placed by the dataset documentation.</i>", 0, ly + 36, 860, 52,
           size=SMALL, color=GRAY)
    return d


# -- IF-01-0-B: sorting a question into one of the four types ---------------------------------------------------------

def if_01_0_b() -> Diagram:
    """A decision aid: four yes/no questions, asked from the most demanding type down (Chapter 1 note)."""
    ex4 = ctx.values("ch01.ex4")
    last_q, prev_q, first, last = ex4["last_quarter"], ex4["prev_quarter"], ex4["first"], ex4["last"]
    change = ex4["units_change"]
    flat = abs(change) <= 0.05
    steps = [
        ("Does the answer recommend what to do, under an objective and constraints?", "Prescriptive",
         "Given the hours each work center has next quarter, which items should the plant schedule to maximize "
         "contribution margin?",
         "a recommendation, with its objective and its constraints"),
        ("Does it project what might happen in a later period?", "Predictive",
         "How many units will the plant complete next quarter, and what total variance does that suggest, if recent "
         "trends continue?",
         "an expectation or forecast from historical patterns"),
        ("Does it explain why something happened?", "Diagnostic",
         f"Why did the total variance on closed work orders rise from fiscal {first} to fiscal {last} while the units "
         f"completed {'barely changed' if flat else f'changed by {change:+.1%}'}?",
         "a decomposition, a comparison of segments, or a trace to documents"),
        ("Does it summarize what happened?", "Descriptive",
         f"How many units of each item group did the plant complete in {last_q}, compared with {prev_q}?",
         "a summary of recorded data"),
    ]
    d = Diagram("Sorting a Question into One of the Four Types")
    qx, qw, rx, rw = 0, 262, 340, 520
    d.text("<i>Ask in this order. The first yes is the question's type.</i>", qx, 0, 400, 24, size=SMALL, color=GRAY)
    y = 34
    prev = None
    for question, label, example, evidence in steps:
        text = f"<b>{label}</b><br>Example: {esc(example)}<br><i>The answer is {evidence}.</i>"
        h = max(kit.height_for(text, rw, pad=14), 74)
        qh = max(kit.height_for(question, qw, pad=18), 56)
        qid = d.box(question, qx, y + (h - qh) / 2, qw, qh, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5)
        rid = d.box(text, rx, y, rw, h, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, align="left")
        d.arrow(qid, rid, exit=(1, 0.5), entry=(0, 0.5), label="Yes")
        if prev:
            d.arrow(prev, qid, exit=(0.5, 1), entry=(0.5, 0), label="No")
        prev = qid
        y += h + 34
    reword_h = 66
    reword = d.box("<b>Not yet one of the four.</b><br>Reword it: what would the manager do with the answer?", qx, y,
                   qw, reword_h, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5)
    d.arrow(prev, reword, exit=(0.5, 1), entry=(0.5, 0), label="No")
    kit.callout(d, "Most real questions combine two types. The controller's question about the Furniture margin is "
                   "diagnostic, and it needs a descriptive summary first, so the first yes names its type and the earlier "
                   "types are its first steps. A question that asks \"what happened and why?\" is two questions: split it "
                   "and type each part.", rx, y, rw, color="amber")
    return d


# -- IF-01-2-A and IF-01-2-B: the traced sale -------------------------------------------------------------------------

def _postings(rows: list[dict]) -> str:
    """'Dr 1020<br>Cr 4010, 4050, 2050' from the ledger rows of one document."""
    debit = [str(r["number"]) for r in rows if r["debit"]]
    credit = [str(r["number"]) for r in rows if r["credit"]]
    return f"Dr {', '.join(debit)}<br>Cr {', '.join(credit)}"


def if_01_2_a() -> Diagram:
    """The traced sale through the seven worksheets, with the ledger postings (Exercise 1.2)."""
    v = ctx.values("ch01.ex2")
    n, order, inv, rec = v["numbers"], v["order"], v["invoice"], v["receipt"]
    d = Diagram("The Traced Sale from Order to Ledger")
    nodes = [
        ("SalesOrder", f"{n['order']}<br>{v['order_date']}<br>{order['lines']} lines"),
        ("Shipment", f"{n['shipment']}<br>{v['ship_date']}"),
        ("SalesInvoice", f"{n['invoice']}<br>{inv['date']}<br>{_money(inv['total'])}"),
        ("CashReceipt", f"{n['receipt']}<br>{rec['date']}<br>{_money(rec['amount'])}"),
        ("CashReceiptApplication", f"{_money(rec['applied_here'])} to this invoice<br>{rec['applied_date']}"),
    ]
    labels = [f"{order['shipments']}<br>shipments", f"{order['invoices']}<br>invoices", "paid<br>by",
              f"{rec['applications']}<br>invoices"]
    fills = ["blue", "blue", "blue", "teal", "teal"]
    widths = [108, 108, 108, 108, 150]          # 12 px text: the document numbers need 92 px, the longest table name 138
    gap = (860 - sum(widths)) / (len(widths) - 1)
    height, ids, boxes, x = 88, [], [], 0.0
    for (name, body), w, fill in zip(nodes, widths, fills):
        tint, stroke = kit.tint(fill)
        ids.append(d.box(f"<b>{name}</b><br>{body}", x, 0, w, height, fill=tint, stroke=stroke, stroke_width=1.5,
                         size=SMALL))
        boxes.append((x, 0, w, height))
        x += w + gap
    for i, label in enumerate(labels):
        d.arrow(ids[i], ids[i + 1], label=label, exit=(1, 0.5), entry=(0, 0.5))
    gl_y = height + 130
    gl = d.box("<b>GLEntry</b><br>one row for each debit or credit the documents above create", 0, gl_y, 860, 52,
               fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5)
    postings = {1: _postings(v["ship_gl"]), 2: _postings(v["gl"]), 3: _postings(v["gl_receipt"]), 4: _postings(v["gl_app"])}
    mid = (height + gl_y) / 2
    for i, text in postings.items():
        bx, by, bw, bh = boxes[i]
        cx = bx + bw / 2
        d.edge(ids[i], gl, end="blockThin", color=AMBER, dashed=True, width=2.5, exit=(0.5, 1), entry=(cx / 860, 0))
        width = max(text_width(part, SMALL, False) for part in text.split("<br>")) + 26
        d.box(text, cx - width / 2, mid - 20, width, 40, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
    d.text("<i>The order and its lines post nothing: no arrow reaches the ledger from SalesOrder or SalesOrderLine, "
           "because no financial effect has happened yet.</i>", 0, height + 14, 164, 110, size=SMALL, color=GRAY)
    d.text("<b>Dashed amber:</b> a posting to the ledger. <b>Solid gray:</b> the next step of the sale.", 0, gl_y + 66,
           860, 20, size=SMALL)
    d.text(f"<i>Arrow labels count what the order has ({order['shipments']} shipments, {order['invoices']} invoices) "
           f"and what the receipt paid ({rec['applications']} invoices); each box shows the one that the traced sale "
           f"passes through.</i>", 0, gl_y + 88, 860, 36, size=SMALL, color=GRAY)
    return d


def if_01_2_b() -> Diagram:
    """The GLEntry worksheet filtered to the traced invoice, with the SourceDocumentType filter list (Exercise 1.2)."""
    v = ctx.values("ch01.ex2")
    data = ctx.data()
    invoice_id, number = v["ids"]["invoice"], v["numbers"]["invoice"]
    first, last, total = data.q("SELECT MIN(GLEntryID), MAX(GLEntryID), COUNT(*) FROM GLEntry")[0]
    assert (first, last) == (1, total), "row numbers assume GLEntryID 1..n in worksheet order"
    rows = data.q("SELECT GLEntryID, AccountID, Debit, Credit, VoucherNumber, SourceDocumentType, SourceDocumentID, "
                  "SourceLineID FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND SourceDocumentID = ? "
                  "ORDER BY GLEntryID", invoice_id)
    assert [r[0] for r in rows] == [r["id"] for r in v["gl"]], "the figure and the guide show the same ledger rows"
    debit, credit = sum(r[2] for r in rows), sum(r[3] for r in rows)
    assert abs(debit - credit) < 0.005, "the receivables debit equals the credits"
    headers = ["GLEntryID", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "SourceDocumentID",
               "SourceLineID"]
    letters = list("ACDEGHIJ")                       # B (PostingDate) and F (VoucherType) are hidden
    body_text = [[str(r[0]), str(r[1]), _num(r[2]), _num(r[3]), r[4], r[5], str(r[6]), "" if r[7] is None else str(r[7])]
                 for r in rows]
    widths = [50] + _col_widths(headers, body_text, extra={5: 20, 6: 20}, pad=16, floor=52)
    assert sum(widths) <= 860, sum(widths)
    d = Diagram("The GLEntry Worksheet Filtered to the Traced Invoice")
    body = [(str(r[0] + 1), values) for r, values in zip(rows, body_text)]
    geo = xl.table_view(d, 0, 0, letters, widths, headers, body, number_color=BLUE)
    xs = [0.0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    tri = "triangle;direction=south;html=1;fillColor={};strokeColor=none;"
    type_col, id_col, line_col = 5, 6, 7
    for c in (type_col, id_col):
        hx, hy, hw, hh = geo[(0, c)]
        d.vertex("", tri.format(WHITE), hx + hw - 16, hy + 9, 9, 7)
    xl.emphasis(d, *geo[(0, type_col)])
    revenue = next(i for i, r in enumerate(rows) if r[7] is not None)
    xl.emphasis(d, *geo[(revenue + 1, line_col)])
    # The filter list, drawn below the rows so that it does not cover them.
    types = [r[0] for r in data.q("SELECT DISTINCT SourceDocumentType FROM GLEntry ORDER BY 1")]
    at = types.index("SalesInvoice")
    start = max(0, min(at - POPUP_ITEMS // 2, len(types) - POPUP_ITEMS))
    shown = types[start:start + POPUP_ITEMS]
    hx, hy, hw, hh = geo[(0, type_col)]
    arrow_x = hx + hw - 11.5
    pw = 236
    px = max(0, min(arrow_x + 18 - pw, 860 - pw))
    py = 22 + 24 * (len(rows) + 1) + 26
    item_h = 22
    ph = 8 + 24 + 8 + item_h + POPUP_ITEMS * item_h + 10 + 26 + 10
    d.box("", px, py, pw, ph, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
    d.box("<i>Search</i>", px + 8, py + 8, pw - 16, 24, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, align="left",
          rounded=False)
    ly = py + 40
    d.vertex("■", "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#5D6D7E;fontColor=#1A5276;"
             "fontSize=12;fontFamily=Helvetica;align=center;verticalAlign=middle;spacing=0;", px + 12, ly + 4, 14, 14)
    d.text("(Select All)", px + 34, ly, pw - 60, item_h, size=SMALL, valign="middle")
    ly += item_h
    for name in shown:
        xl.checkbox(d, px + 12, ly + 4, name == "SalesInvoice")
        d.text(f"<b>{esc(name)}</b>" if name == "SalesInvoice" else esc(name), px + 34, ly, pw - 60, item_h, size=SMALL,
               valign="middle")
        ly += item_h
    track_top, track_h = py + 40 + item_h, POPUP_ITEMS * item_h
    d.box("", px + pw - 18, track_top, 8, track_h, fill=GRAY_TINT, stroke=RULE, rounded=False)
    thumb = track_h * POPUP_ITEMS / len(types)
    d.box("", px + pw - 18, track_top + (track_h - thumb) * start / max(1, len(types) - POPUP_ITEMS), 8, thumb,
          fill=GRAY, stroke=GRAY, rounded=False)
    by = py + ph - 36
    xl.button(d, px + pw - 162, by, 70, "OK", primary=True)
    xl.button(d, px + pw - 84, by, 70, "Cancel")
    # The leader from the filter button of SourceDocumentType to its list.
    top_anchor, bottom_anchor = d.anchor(arrow_x, hy + hh), d.anchor(arrow_x, py)
    d.edge(top_anchor, bottom_anchor, color=GRAY, width=1.5, meta="edgeStyle=none;")
    # The reading beside the list, and the usual bottom of the window.
    note = (f"Two filters narrow GLEntry to the invoice: SourceDocumentType is SalesInvoice and SourceDocumentID is "
            f"{invoice_id}. The Table has {len(rows)} rows left of {total:,}. The receivables debit ({_num(rows[0][2])}) "
            f"equals the {len(rows) - 1} credits, and only the revenue row carries a SourceLineID. VoucherNumber holds "
            f"the invoice number, {number}.").replace(f"{total:,}", str(total))
    kit.callout(d, note, 0, py + 8, px - 14, color="gray")
    bottom = py + ph + 10
    xl.sheet_tabs(d, 0, bottom, xl.tabs_around("GLEntry", 3, 2), "GLEntry")
    xl.status_bar(d, 0, bottom + 28, 860, f"{len(rows)} of {total} records found")
    d.text("<i>Columns B (PostingDate) and F (VoucherType) are hidden, and the columns after SourceLineID are out of view. "
           "Outlined: the SourceDocumentType header, whose filter list is open, and the SourceLineID of the revenue row. "
           "Blue row numbers mark a filtered Table.</i>", 0, bottom + 60, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-01-3-A: a budget row against its ledger rows ------------------------------------------------------------------

def _budget_example(data) -> tuple:
    """A budget row of the current fiscal year for an expense account, with the cost center and the account, and
    its matching GLEntry rows: the first row (June, by BudgetID) whose ledger match runs from four to six rows."""
    found = data.q(
        "SELECT b.BudgetID, b.FiscalYear, b.Month, b.CostCenterID, b.AccountID, c.CostCenterName, a.AccountNumber, "
        "a.AccountName, (SELECT COUNT(*) FROM GLEntry g WHERE g.CostCenterID = b.CostCenterID AND g.AccountID = b.AccountID "
        "AND g.FiscalYear = b.FiscalYear AND g.FiscalPeriod = b.Month) FROM Budget b "
        "JOIN Account a ON a.AccountID = b.AccountID JOIN CostCenter c ON c.CostCenterID = b.CostCenterID "
        "WHERE b.FiscalYear = ? AND b.Month = 6 AND a.AccountType = 'Expense' ORDER BY b.BudgetID", data.C)
    row = next((r for r in found if 4 <= r[8] <= 6), None)
    if row is None:
        raise ValueError("no June budget row of an expense account matches four to six ledger rows; choose another month")
    ledger = data.q("SELECT FiscalYear, FiscalPeriod, CostCenterID, AccountID, Debit, Credit FROM GLEntry "
                    "WHERE CostCenterID = ? AND AccountID = ? AND FiscalYear = ? AND FiscalPeriod = ? ORDER BY GLEntryID",
                    row[3], row[4], row[1], row[2])
    return row, ledger


def if_01_3_a() -> Diagram:
    """One budget row lined up with the ledger rows that give its actual spending (Exercise 1.3)."""
    data = ctx.data()
    row, ledger = _budget_example(data)
    _, year, month, cc_id, acct_id, cc_name, acct_no, acct_name, _n = row
    d = Diagram("A Budget Row and the Ledger Rows That Give Its Actual Spending")
    widths = [96, 110, 190, 190, 274]
    xs = [0.0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    # The two lookup worksheets.

    def record(x: float, y: float, w: float, name: str, group: str, pairs: list[tuple[str, str]], key_w: float) -> tuple:
        """A one-row worksheet shown as key and value pairs.  Returns an invisible box over it, and its bottom."""
        d.text(f"<i>{group}</i>", x, y - 19, w, 18, size=SMALL, color=GRAY, valign="bottom")
        d.header_box(name, x, y, w, h=26, fill=GRAY, size=SMALL)
        for i, (key, value) in enumerate(pairs):
            ry = y + 26 + i * 24
            d.box(esc(key), x, ry, key_w, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
            d.box(esc(_clip(value, w - key_w)), x + key_w, ry, w - key_w, 24, fill=WHITE, stroke=RULE, size=SMALL,
                  align="left", rounded=False)
        bottom = y + 26 + len(pairs) * 24
        return d.container(x, y, w, bottom - y), bottom

    cc_x, cc_w, acct_x, acct_w = xs[2] - 10, 210, xs[3] + 30, 250
    acct_box, lookup_bottom = record(acct_x, 20, acct_w, "Account", "Accounting Core",
                                     [("AccountID", str(acct_id)), ("AccountNumber", str(acct_no)),
                                      ("AccountName", acct_name)], 104)
    cc_box, _ = record(cc_x, lookup_bottom - 74, cc_w, "CostCenter", "Organizational Planning",
                       [("CostCenterID", str(cc_id)), ("CostCenterName", cc_name)], 112)
    # The budget row.
    budget_y = lookup_bottom + 84
    heads = ["FiscalYear", "Month", "CostCenterID", "AccountID", "BudgetAmount"]
    b_head = [d.box(f"<b>{head}</b>", x, budget_y, w, 26, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
              for x, w, head in zip(xs, widths, heads)]
    b_values = [str(year), str(month), str(cc_id), str(acct_id), "<i>planned amount</i>"]
    b_ids = []
    for c, (x, w, value) in enumerate(zip(xs, widths, b_values)):
        b_ids.append(d.box(value, x, budget_y + 26, w, 28, fill=AMBER_TINT if c < 4 else TEAL_TINT,
                           stroke=AMBER if c < 4 else TEAL, stroke_width=1.5, color=INK if c < 4 else GRAY, size=SMALL,
                           rounded=False))
    budget_bottom = budget_y + 54
    d.text("<b>Budget</b> worksheet, one row <i>(Organizational Planning)</i>", 575, budget_bottom + 8, 285, 36, size=SMALL)
    # The ledger rows.
    gl_y = budget_bottom + 78
    gl_widths = [96, 110, 190, 190, 137, 137]
    gl_xs = [0.0]
    for w in gl_widths[:-1]:
        gl_xs.append(gl_xs[-1] + w)
    gl_heads = ["FiscalYear", "FiscalPeriod", "CostCenterID", "AccountID", "Debit", "Credit"]
    g_head_ids = []
    for x, w, head in zip(gl_xs, gl_widths, gl_heads):
        g_head_ids.append(d.box(f"<b>{head}</b>", x, gl_y, w, 26, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL,
                                rounded=False))
    for r, (fy, fp, cc, ac, dr, cr) in enumerate(ledger):
        values = [str(fy), str(fp), str(cc), str(ac), "<i>amount</i>" if dr else "0", "<i>amount</i>" if cr else "0"]
        for c, (x, w, value) in enumerate(zip(gl_xs, gl_widths, values)):
            keyed = c < 4
            d.box(value, x, gl_y + 26 + r * 26, w, 26, fill=AMBER_TINT if keyed else TEAL_TINT, stroke=RULE, size=SMALL,
                  color=INK if keyed or value == "0" else GRAY, rounded=False)
    gl_bottom = gl_y + 26 + len(ledger) * 26
    # The lookups: names for the two keys (each arrow drops straight to its column heading).
    d.edge(cc_box, b_head[2], end="blockThin", color=GRAY, width=1.5, exit=(0.5, 1),
           entry=((cc_x + cc_w / 2 - xs[2]) / widths[2], 0), label="names the<br>cost center")
    d.edge(acct_box, b_head[3], end="blockThin", color=AMBER, width=2.5, exit=(0.5, 1),
           entry=((acct_x + acct_w / 2 - xs[3]) / widths[3], 0), label="names the<br>account")
    # The three joins between the budget row and the ledger rows.
    for c, label in ((0, None), (1, None), (2, "same cost<br>center"), (3, "same<br>account")):
        d.edge(b_ids[c], g_head_ids[c], color=AMBER, width=2.5, exit=(0.5, 1), entry=(0.5, 0), label=label)
    mid = (budget_bottom + gl_y) / 2
    d.box("same period", (xs[0] + widths[0] / 2 + xs[1] + widths[1] / 2) / 2 - 42, mid - 11, 84, 22, fill=WHITE,
          stroke=WHITE, size=SMALL, rounded=False)
    d.text(f"<b>GLEntry</b> worksheet <i>(Accounting Core)</i>: all {len(ledger)} rows with this cost center, account and "
           f"period", 0, gl_bottom + 6, 860, 20, size=SMALL)
    kit.callout(d, f"Many ledger rows add up to one budget row: the actual spending for the budget row is the sum of "
                   f"Debit less the sum of Credit over the {len(ledger)} rows that match on cost center, account and "
                   f"period. Amounts are named, not shown.", 0, gl_bottom + 36, 860, color="gray")
    kit.legend(d, 0, gl_bottom + 92, [("Solid amber: a key shared with another table group", AMBER, "line"),
                                      ("Solid gray: a key within a group", GRAY, "line")])
    return d


# -- IF-01-6-A: JournalEntry rows that reverse another entry ---------------------------------------------------------

def if_01_6_a() -> Diagram:
    """The JournalEntry worksheet filtered to the entries that reverse another (Exercise 1.6)."""
    data = ctx.data()
    ex6 = ctx.values("ch01.ex6")
    first, last, total = data.q("SELECT MIN(JournalEntryID), MAX(JournalEntryID), COUNT(*) FROM JournalEntry")[0]
    assert (first, last) == (1, total), "row numbers assume JournalEntryID 1..n in worksheet order"
    rows = data.q("SELECT JournalEntryID, EntryNumber, PostingDate, EntryType, TotalAmount, CreatedDate, "
                  "ReversesJournalEntryID FROM JournalEntry WHERE ReversesJournalEntryID IS NOT NULL "
                  "ORDER BY JournalEntryID LIMIT 10")
    found = data.one("SELECT COUNT(*) FROM JournalEntry WHERE ReversesJournalEntryID IS NOT NULL")
    assert found == ex6["n_reversing"], "the figure and the guide count the same reversing entries"
    assert {r[3] for r in rows} == {"Accrual Adjustment"}, "the rows shown are all Accrual Adjustment entries"
    assert len({r[5][11:] for r in rows}) == 1, "the time of day reads the same on every row shown"
    originals = {r[0] for r in data.q("SELECT JournalEntryID FROM JournalEntry WHERE EntryType = 'Accrual'")}
    assert all(r[6] in originals for r in rows), "each row reverses an Accrual entry"
    headers = ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount", "CreatedDate",
               "ReversesJournalEntryID"]
    letters = list("ABCDFHK")        # Description (E), the creator and approver columns (G, I, J) are hidden
    body_text = [[str(r[0]), r[1], r[2], r[3], f"{r[4]:,.2f}", r[5], str(r[6])] for r in rows]
    widths = [52] + _col_widths(headers, body_text, pad=18, floor=52)
    assert sum(widths) <= 860, sum(widths)
    body = [(str(r[0] + 1), values) for r, values in zip(rows, body_text)]
    d = Diagram("The JournalEntry Worksheet Filtered to Entries That Reverse Another")
    geo = xl.table_view(d, 0, 0, letters, widths, headers, body, number_color=BLUE)
    time_col, rev_col = 5, 6
    xl.emphasis(d, *xl.column_box(geo, time_col, len(body) + 1))
    xl.emphasis(d, *xl.column_box(geo, rev_col, len(body) + 1))
    bottom = 22 + 24 * (len(body) + 1)
    xl.sheet_tabs(d, 0, bottom + 6, xl.tabs_around("JournalEntry", 3, 2), "JournalEntry")
    xl.status_bar(d, 0, bottom + 34, 860, f"{found} of {total} records found")
    time_of_day = rows[0][5][11:]
    d.text(f"<i>Filtered to the entries whose ReversesJournalEntryID is filled; the first {len(rows)} of {found} are shown, "
           f"all of type Accrual Adjustment. Columns E, G, I and J (Description, the creator and the approver) are "
           f"hidden. Outlined: CreatedDate, which reads {time_of_day} on every row, and ReversesJournalEntryID, the "
           f"JournalEntryID of the earlier accrual that the entry adjusts. Blue row numbers mark a filtered "
           f"Table.</i>", 0, bottom + 66, 860, 52, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "IF-01-0-A": if_01_0_a,
    "IF-01-0-B": if_01_0_b,
    "IF-01-2-A": if_01_2_a,
    "IF-01-2-B": if_01_2_b,
    "IF-01-3-A": if_01_3_a,
    "IF-01-6-A": if_01_6_a,
}
