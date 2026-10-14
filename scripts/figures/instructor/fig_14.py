"""Instructor figures of Chapter 14 (guides in facts/instructor/guides/chapter-14-data-models-and-dax/).

Chapter 14 is the second Power BI unit.  Its mocks draw the model and the pages of the model answer
(outputs/companion/solutions/Chapter14-exercises-pbi, a PBIP of TMDL, PBIR and DAX query text), so the names, the
columns, the relationships, the page titles and the Checks tab are read from that project, and every value comes from
the dataset through the guides' own contexts (ch14.chapter, ch14.g1 to ch14.g6) and the notes' helpers
(notes.ch14, ch14.ex1 to ch14.ex6).
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from functools import lru_cache

import ctx
import excel as xl
import kit
import powerbi as pbi
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HIGHLIGHT, INK, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

FILE = "Chapter 14 Exercises - Solutions"
PROJECT = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter14-exercises-pbi" / FILE
MODEL = PROJECT / f"{FILE}.SemanticModel"
REPORT = PROJECT / f"{FILE}.Report" / "definition"
CHAPTER = ctx.REPO / "chapters" / "14-data-models-and-dax"


# -- the model answer (a PBIP of text files) ----------------------------------------------------------------------------

def _tmdl(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def _g14():
    """guide_contexts.ch14: the helpers that read the project's measures (measure_table)."""
    from guide_contexts import ch14
    return ch14


def _n14():
    from notes import ch14
    return ch14


def _model_columns(table: str) -> list[str]:
    return [a or b for a, b in re.findall(r"^\tcolumn (?:'([^']+)'|(\S+))\s*$", _tmdl(f"tables/{table}.tmdl"), re.M)]


def _relationships() -> list[tuple[tuple[str, str], tuple[str, str], bool]]:
    """(many side, one side, active) of each relationship of the project, each side as (table, column)."""
    out = []
    for block in _tmdl("relationships.tmdl").split("relationship ")[1:]:
        (ft, fc), (tt, tc) = re.findall(r"(?:fromColumn|toColumn): (\w+)\.(\w+)", block)
        out.append(((ft, fc), (tt, tc), "isActive: false" not in block))
    return out


def _loaded_tables() -> set[str]:
    return {p.stem for p in (MODEL / "definition" / "tables").glob("*.tmdl")}


def _folder_measures() -> dict[str, list[str]]:
    """The measures of Key Measures by display folder ("" for the ones the tutorials add)."""
    out = defaultdict(list)
    for block in re.split(r"\n\tmeasure ", _tmdl("tables/Key Measures.tmdl"))[1:]:
        name = re.match(r"'([^']+)'|(\S+)", block)
        folder = re.search(r"^\t\tdisplayFolder: (.+)$", block, re.M)
        out[folder.group(1).strip() if folder else ""].append(name.group(1) or name.group(2))
    return dict(out)


def _page_ids() -> list[str]:
    return json.loads((REPORT / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]


def _page_name(page: str) -> str:
    return json.loads((REPORT / "pages" / page / "page.json").read_text(encoding="utf-8"))["displayName"]


def _visual(page: str, name: str) -> dict:
    return json.loads((REPORT / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))


def _title(page: str, name: str) -> str:
    """The title the model answer gives a visual (a doubled apostrophe in the file is one in the title)."""
    value = _visual(page, name)["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
    return value.strip("'").replace("''", "'")


def _query_tabs() -> list[str]:
    return json.loads((MODEL / ".pbi" / "daxQueries.json").read_text(encoding="utf-8"))["tabOrder"]


def _tutorial_titles() -> dict[int, str]:
    out = {}
    for n in (1, 2, 3):
        text = (CHAPTER / f"_tutorial-0{n}.qmd").read_text(encoding="utf-8")
        out[n] = re.search(rf"^## Guided Tutorial 14\.{n}: (.+)$", text, re.M).group(1).strip()
    return out


def _exercise_titles() -> dict[str, str]:
    text = (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8")
    return dict(re.findall(r"^\*\*Exercise (14\.\d): (.+?)\*\*$", text, re.M))


# -- drawing helpers ----------------------------------------------------------------------------------------------------

def _money(x: float) -> str:
    return pbi.amount(x)


def _signed(x: float) -> str:
    """A measure with the format #,0.00: no minus sign on a zero."""
    return pbi.amount(0.0 if abs(x) < 0.005 else x)


def _pct(x: float) -> str:
    """A measure with the format 0.0%."""
    return f"{100 * x:.1f}%"


def _nb(html: str) -> str:
    """Keep "Tutorial 14.2" and "Ex 14.5" together on a line."""
    return re.sub(r"\b(Tutorial|Exercise|Ex|Chapter) (\d)", r"\1&nbsp;\2", html)


def _nowrap(text: str) -> str:
    """A heading that must not break at its hyphen (2026-01)."""
    return f'<span style="white-space:nowrap">{esc(text)}</span>'


def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow column shows it."""
    if text_width(text, size, bold) <= width - margin:
        return text
    while text and text_width(text + "…", size, bold) > width - margin:
        text = text[:-1]
    return text + "…"


def _tabs(page: str, d: Diagram, y: float) -> None:
    """The page tabs under the canvas: the page, the one before it and the one after it, as the report orders them."""
    order = _page_ids()
    i = order.index(page)
    shown = order[max(i - 1, 0):i + 2]
    pbi.page_tabs(d, 4, y, [_page_name(p) for p in shown], _page_name(page))


def _frame(d: Diagram, x: float, y: float, w: float, h: float, title: str | None, selected: bool = False,
           lines: int | None = None) -> tuple[float, float, float, float]:
    """A visual's container.  The title may take two lines, as a long title does in Power BI.  Returns the inner area."""
    d.box("", x, y, w, h, fill=WHITE, stroke=BLUE if selected else RULE, stroke_width=2 if selected else 1, rounded=False)
    if not title:
        return x + 6, y + 6, w - 12, h - 12
    label = f"<b>{esc(title)}</b>"
    lines = lines or kit.lines_for(label, w - 12, SMALL, bold=True)
    th = 16 * lines + 4
    d.text(label, x + 6, y + 4, w - 12, th, size=SMALL)
    return x + 6, y + 4 + th + 2, w - 12, h - th - 12


def _is_num(value: str) -> bool:
    return value[:1].isdigit() or value[:1] in "-−" and value[1:2].isdigit()


def _table_visual(d: Diagram, x: float, y: float, title: str, headers: list[str], widths: list[float], rows: list[list[str]],
                  total: list[str] | None = None, title_lines: int | None = None) -> dict:
    """A table visual whose title may take two lines: header row, rows (numbers right-aligned) and a bold total row.
    Returns the cell geometry, keyed (row, column) with row -1 for the headers, and the visual's bottom and right edges."""
    w = sum(widths) + 12
    n = len(rows) + 1 + (1 if total else 0)
    label = f"<b>{esc(title)}</b>"
    th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
    h = th + 12 + n * pbi.ROW
    ix, iy, _, _ = _frame(d, x, y, w, h, title, lines=title_lines)
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    geometry = {}
    for c, (head, cx, wd) in enumerate(zip(headers, xs, widths)):
        right = any(_is_num(r[c]) for r in rows)
        d.box(f"<b>{esc(_clip(head, wd, bold=True))}</b>", cx, iy, wd, pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL,
              align="right" if right else "left", rounded=False)
        geometry[(-1, c)] = (cx, iy, wd, pbi.ROW)
    d.box("", ix, iy + pbi.ROW - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, row in enumerate(rows + ([total] if total else [])):
        ry = iy + pbi.ROW * (r + 1)
        is_total = total is not None and r == len(rows)
        if is_total:
            d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
        for c, (value, cx, wd) in enumerate(zip(row, xs, widths)):
            shown = esc(_clip(value, wd, bold=is_total))
            d.box(f"<b>{shown}</b>" if is_total else shown, cx, ry, wd, pbi.ROW,
                  fill=WHITE if r % 2 == 0 or is_total else GRAY_TINT, stroke=WHITE if r % 2 == 0 or is_total else GRAY_TINT,
                  size=SMALL, align="right" if _is_num(value) else "left", rounded=False)
            geometry[(r, c)] = (cx, ry, wd, pbi.ROW)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, width=sum(widths))


def _matrix_visual(d: Diagram, x: float, y: float, title: str, headers: list[str], widths: list[float],
                   rows: list[tuple[int, str, list[str], str]], title_lines: int | None = None) -> dict:
    """A matrix visual whose title may take two lines.  rows are (level, label, values, state): level 0 is a top row, 1 a
    row under an expanded parent; state is "-" (expanded), "+" (collapsed) or "" (no children); a label of Total
    marks the bold total row.  Returns the cell geometry, keyed (row, column) with row -1 for the headers and column 0
    for the row labels."""
    w = sum(widths) + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
    h = th + 12 + (len(rows) + 1) * pbi.ROW
    ix, iy, _, _ = _frame(d, x, y, w, h, title, lines=title_lines)
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    geometry = {}
    for c, (head, cx, wd) in enumerate(zip(headers, xs, widths)):
        d.box(f"<b>{_nowrap(head)}</b>", cx, iy, wd, pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align="left" if c == 0 else "right",
              rounded=False)
        geometry[(-1, c)] = (cx, iy, wd, pbi.ROW)
    d.box("", ix, iy + pbi.ROW - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, (level, name, values, state) in enumerate(rows):
        ry = iy + pbi.ROW * (r + 1)
        bold = name == "Total" or (level == 0 and state == "-")
        glyph = {"+": "+ ", "-": "– ", "": ""}[state]
        text = "&nbsp;" * (5 * level) + esc(glyph + name)
        if name == "Total":
            d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
        d.box(f"<b>{text}</b>" if bold else text, xs[0], ry, widths[0], pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align="left",
              rounded=False)
        geometry[(r, 0)] = (xs[0], ry, widths[0], pbi.ROW)
        for c, (value, cx, wd) in enumerate(zip(values, xs[1:], widths[1:]), 1):
            shown = esc(_clip(value, wd, bold=bold))
            d.box(f"<b>{shown}</b>" if bold else shown, cx, ry, wd, pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align="right",
                  rounded=False)
            geometry[(r, c)] = (cx, ry, wd, pbi.ROW)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, width=sum(widths))


def _fit_dax(line: str, width: float) -> str:
    """A line of the query cut where the editor's pane ends (a long line runs off the right edge)."""
    whole = line
    while line and text_width(pbi.highlight_dax(line), SMALL, False) > width:
        line = line[:-1]
    if line != whole and whole[len(line)].isalnum():
        line = re.sub(r"[A-Za-z0-9_]+$", "", line)           # the editor cuts between pixels; the mock cuts between tokens
    return line.rstrip()


def _check_columns(table: str, columns: list[str]) -> None:
    """A mock may show only the columns the project has."""
    if table == "Key Measures":
        measures = _g14().measure_table()
        missing = set(columns) - set(measures)
    else:
        missing = set(columns) - set(_model_columns(table))
    assert not missing, f"{table} lacks {sorted(missing)} in the model answer"


def _card(d: Diagram, name: str, x: float, y: float, columns: list[str], w: float) -> pbi.ModelTable:
    _check_columns(name, columns)
    return pbi.model_table(d, name, x, y, columns, w=w)


# -- IF-14-0-A: the build sequence of the chapter -----------------------------------------------------------------------------

def if_14_0_a() -> Diagram:
    """The Chapter 13 report, the three tutorials in a row, and the six exercises branching from the copy saved after Tutorial 14.3."""
    d = Diagram("The Build Sequence of Chapter 14")
    titles = _tutorial_titles()
    ex = _exercise_titles()
    assert len(ex) == 6
    c = ctx.values("ch14.chapter")
    folders = _folder_measures()
    measures = _g14().measure_table()
    queries = json.loads(re.search(r"PBI_QueryOrder = (\[.*\])", _tmdl("model.tmdl")).group(1))
    tabs = _query_tabs()
    assert tabs == ["Tests", "Ex 14.5", "Control Totals", "Checks"], tabs
    assert queries[:4] == ["Customer", "SalesInvoice", "SalesInvoiceLine", "Item"]
    assert queries[-3:] == ["ShipmentHeaders", "ShipmentLines", "ShippedLines"]
    for name in ("Revenue", "Gross Margin", "Share of Revenue", "GL Amount", "Net Income", "Operating Expense"):
        assert name in measures, name
    pages = [_page_name(p) for p in ("salesDiscounts", "validation", "review")]
    five = [_page_name(p) for p in ("margins", "incomeStatement")]
    n_ex5 = len(re.findall(r"^EVALUATE", (MODEL / "DAXQueries" / "Ex 14.5.dax").read_text(encoding="utf-8"), re.M))
    n_tests = (MODEL / "DAXQueries" / "Control Totals.dax").read_text(encoding="utf-8").count('ROW ( "Test"')
    assert (n_ex5, n_tests) == (3, 7)
    n_ledger = len({"GLEntry", "Account", "CostCenter"} & _loaded_tables())
    assert n_ledger == 3

    # the main path, left to right
    widths = [172, 200, 200, 200]
    gap = (860 - sum(widths)) / 3
    xs = [sum(widths[:i]) + gap * i for i in range(4)]
    texts = [
        f"<b>Chapter 13 report</b><br>Charles River Reports.pbix<br>Four queries: {', '.join(queries[:3])} and {queries[3]}<br>"
        f"Pages: {pages[0]}, {pages[1]} and {pages[2]}",
        f"<b>Tutorial 14.1</b><br>{esc(titles[1])}<br>SalesInvoice is merged into the lines and stops loading; Customer, Item "
        f"and the new Date table relate to the lines<br><i>{c['steps'][1]} steps</i>",
        f"<b>Tutorial 14.2</b><br>{esc(titles[2])}<br>The Key Measures table, from Revenue to Share of Revenue; the "
        f"{five[0]} page; the {tabs[0]} tab<br><i>{c['steps'][2]} steps</i>",
        f"<b>Tutorial 14.3</b><br>{esc(titles[3])}<br>The ledger star: GLEntry, Account and CostCenter share the Date table; "
        f"GL Amount and Net Income; the {five[1]} page<br><i>{c['steps'][3]} steps</i>",
    ]
    h = max(kit.height_for(t, widths[i] - 8, SMALL, pad=16) for i, t in enumerate(texts))
    ids = []
    for i, t in enumerate(texts):
        fill, stroke = (GRAY_TINT, GRAY) if i == 0 else (BLUE_TINT, BLUE)
        ids.append(d.box(_nb(t), xs[i], 0, widths[i], h, fill=fill, stroke=stroke, size=SMALL, align="left", valign="top",
                         stroke_width=1.5))
    for a, b in zip(ids, ids[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
    # the copy every exercise starts from
    by = h + 44
    bar_text = ("<b>Ch14 Exercises.pbix</b>, the report saved with File > Save as after Tutorial 14.3. Each exercise works in this copy, "
                "on a page or a DAX query view tab of its own, with its measures in a display folder of Key Measures.")
    bh = kit.height_for(bar_text, 860, SMALL, pad=14)
    bar = d.box(bar_text, 0, by, 860, bh, fill=GRAY_TINT, stroke=GRAY, size=SMALL, align="left", stroke_width=1.5)
    d.arrow(ids[3], bar, exit=(0.5, 1), entry=((xs[3] + widths[3] / 2) / 860, 0), meta="edgeStyle=none;")
    # the six exercises
    adds = {
        "14.1": f"{len(folders['Ex 14.1'])} measures: Balance, two variants and Contra Accounts; the page Ex 14.1",
        "14.2": f"{len([q for q in queries if q.startswith('Shipment') or q == 'ShippedLines'])} queries, a second fact table with an "
                f"inactive relationship, {len(folders['Ex 14.2'])} measures; the page Ex 14.2",
        "14.3": f"{len(folders['Ex 14.3'])} measures, from Revenue PY to Group Lines; the page Ex 14.3",
        "14.4": f"{len(folders['Ex 14.4'])} measures, from Units to Bridge Check; the page Ex 14.4",
        "14.5": f"No measure: the DAX query view tab {tabs[1]}, {n_ex5} queries that change a relationship or a filter for one calculation",
        "14.6": f"No measure: the DAX query view tab {tabs[2]}, {n_tests} tests with a Pass or Fail",
    }
    builds = {
        "14.1": "Tutorial 14.3: IsYearEndClose, GL Amount; Tutorial 14.1: the marked Date table",
        "14.2": "Tutorial 14.1: the Date table and its relationships",
        "14.3": "Tutorial 14.1: the marked Date table; Tutorial 14.2: Revenue",
        "14.4": "Tutorial 14.2: Revenue, Gross Margin; Tutorial 6.3: the bridge",
        "14.5": "Tutorial 14.2: Share of Revenue; Tutorial 14.3: Operating Expense",
        "14.6": "Tutorial 14.3: Net Income, GL Amount, Test 3",
    }
    ew = (860 - 5 * 10) / 6
    etexts = [f"<b>Ex {n}</b><br>{esc(ex[n])}<br><br>{esc(adds[n])}<br><br><i>Builds on: {esc(builds[n])}</i>" for n in ex]
    eh = max(kit.height_for(t, ew - 10, SMALL, pad=18) for t in etexts)
    ey = by + bh + 40
    for i, t in enumerate(etexts):
        ex_id = d.box(_nb(t), i * (ew + 10), ey, ew, eh, fill=TEAL_TINT, stroke=TEAL, size=SMALL, align="left", valign="top",
                      stroke_width=1.5)
        d.arrow(bar, ex_id, exit=((i * (ew + 10) + ew / 2) / 860, 1), entry=(0.5, 0), meta="edgeStyle=none;")
    bottom = ey + eh + 14
    lx = 0
    for label, fill, stroke in [("Given", GRAY_TINT, GRAY), ("Built in the tutorials", BLUE_TINT, BLUE), ("Added by an exercise", TEAL_TINT, TEAL)]:
        d.box("", lx, bottom + 3, 16, 14, fill=fill, stroke=stroke, stroke_width=1.5, rounded=False)
        lw = text_width(label, SMALL, False) + 8
        d.text(label, lx + 22, bottom, lw, 20, size=SMALL, valign="middle")
        lx += 22 + lw + 24
    _note(d, f"The model answer holds the {len(pages) + len(five)} pages of the tutorials, a page for each of Ex 14.1 to Ex 14.4 and Notes; "
             f"Exercises 14.5 and 14.6 are DAX query view tabs, {tabs[1]} and {tabs[2]}, beside {tabs[0]} and {tabs[3]}. Exercise 14.2 is the "
             "only one that adds queries, and with them a second fact table.", bottom + 26)
    return d


# -- IF-14-0-B: Model view of the model answer ----------------------------------------------------------------------------------

def if_14_0_b() -> Diagram:
    """Model view with the nine tables of the model answer: both stars, the shared Date table, the dashed relationship, and
    Key Measures standing apart."""
    d = Diagram("Model View of the Model Answer")
    shown = {
        "Customer": ["CustomerID", "CustomerName", "CustomerSegment"],
        "Item": ["ItemID", "ItemCode", "ItemGroup"],
        "SalesInvoiceLine": ["SalesInvoiceLineID", "CustomerID", "ItemID", "InvoiceDate", "LineTotal"],
        "Date": ["Date", "Year", "Quarter", "YearMonth"],
        "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "CostCenterID", "Debit", "Credit"],
        "Account": ["AccountID", "AccountNumber", "AccountType"],
        "CostCenter": ["CostCenterID", "CostCenterName"],
        "ShippedLines": ["ShipmentLineID", "ItemID", "LineTotal", "InvoiceDate", "ShipmentDate", "CrossesYear"],
        "Key Measures": ["Revenue", "Gross Margin", "Net Income", "Balance"],
    }
    assert _loaded_tables() == set(shown), "the nine tables of the model answer"
    wanted = {(("SalesInvoiceLine", "ItemID"), ("Item", "ItemID"), True), (("SalesInvoiceLine", "InvoiceDate"), ("Date", "Date"), True),
              (("SalesInvoiceLine", "CustomerID"), ("Customer", "CustomerID"), True), (("GLEntry", "AccountID"), ("Account", "AccountID"), True),
              (("GLEntry", "CostCenterID"), ("CostCenter", "CostCenterID"), True), (("GLEntry", "PostingDate"), ("Date", "Date"), True),
              (("ShippedLines", "ItemID"), ("Item", "ItemID"), True), (("ShippedLines", "InvoiceDate"), ("Date", "Date"), True),
              (("ShippedLines", "ShipmentDate"), ("Date", "Date"), False)}
    assert set(_relationships()) == wanted, "the project's nine relationships, the ship-date one inactive"
    n_measures = len(_g14().measure_table())
    win = pbi.window(d, 590, view="Model", tab="Home", buttons=["Manage relationships", "New measure", "New column"], file=FILE)
    top = win.top
    pbi.canvas(d, win.canvas_x, top, 860 - win.canvas_x, win.bottom - top)

    def card(name: str, x: float, y: float, w: float) -> pbi.ModelTable:
        return _card(d, name, x, top + y, shown[name], w)

    cust = card("Customer", 88, 36, 120)
    item = card("Item", 88, 166, 120)
    km = card("Key Measures", 88, 300, 120)
    sil = card("SalesInvoiceLine", 284, 14, 156)
    ship = card("ShippedLines", 284, 244, 156)
    date = card("Date", 510, 120, 104)
    acct = card("Account", 670, 14, 156)
    gl = card("GLEntry", 670, 164, 156)
    cc = card("CostCenter", 670, 380, 156)
    rel = pbi.relationship
    rel(d, cust.right("CustomerID"), sil.left("CustomerID"))
    assert abs(cust.rows["CustomerID"] - sil.rows["CustomerID"]) < 0.5
    rel(d, item.right("ItemID"), sil.left("ItemID"), [(268, item.rows["ItemID"]), (268, sil.rows["ItemID"])])
    rel(d, item.right("ItemID"), ship.left("ItemID"), [(240, item.rows["ItemID"]), (240, ship.rows["ItemID"])])
    rel(d, date.left("Date"), sil.right("InvoiceDate"), [(474, date.rows["Date"]), (474, sil.rows["InvoiceDate"])])
    rel(d, date.left("Date"), ship.right("InvoiceDate"), [(464, date.rows["Date"]), (464, ship.rows["InvoiceDate"])])
    rel(d, date.left("Date"), ship.right("ShipmentDate"), [(484, date.rows["Date"]), (484, ship.rows["ShipmentDate"])], dashed=True)
    rel(d, date.right("Date"), gl.left("PostingDate"), [(642, date.rows["Date"]), (642, gl.rows["PostingDate"])])
    rel(d, (acct.x + acct.w - 30, acct.y + acct.h), (gl.x + gl.w - 30, gl.y))
    rel(d, (cc.x + cc.w - 30, cc.y), (gl.x + gl.w - 30, gl.y + gl.h))
    d.text("<i>no relationship: the table holds only measures</i>", km.x, km.y + km.h + 6, 220, 36, size=SMALL, color=GRAY)
    y = win.bottom + 10
    d.text("<b>1</b> the table that holds the key &nbsp; <b>*</b> the table that refers to it &nbsp; <b>Solid</b> an active relationship "
           "&nbsp; <b>Dashed</b> an inactive one", 0, y, 860, 22, size=SMALL)
    _note(d, f"The model answer after Exercise 14.2: the sales star (SalesInvoiceLine, Item, Customer) and the ledger star (GLEntry, Account, "
             "CostCenter) share the Date table, and ShippedLines, the fact table of Exercise 14.2, relates to Date twice, to Item once. Every "
             "filter arrow points from the dimension to the fact table. Each table lists some of its columns, and Key Measures "
             f"holds {n_measures} measures, four of them shown.", y + 26)
    return d


# -- IF-14-0-C: the Checks tab in DAX query view ----------------------------------------------------------------------------------

def _checks(section: str) -> list[dict]:
    """The rows of one section of the project's Checks tab, in order: label, expected (text as written), tolerance."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'ROW \( "Section", "([^"]+)", "Check", "([^"]+)", "Expected", ([-\d.]+), "Actual", .*?"Agrees", .*? <= ([\d.]+(?:e-?\d+)?) \)',
                         text):
        if m.group(1) == section:
            out.append(dict(label=m.group(2), expected=m.group(3), tolerance=float(m.group(4))))
    return out


def _checks_start(section: str) -> tuple[int, int]:
    """(rows before the section, rows in the query) of the Checks tab."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    sections = re.findall(r'ROW \( "Section", "([^"]+)"', text)
    return sections.index(section), len(sections)


def _ex144_actual(label: str) -> float:
    """The value of one Exercise 14.4 check, from the dataset (notes.ch14.bridge)."""
    m = re.fullmatch(r"(\w+) (\d{4})-Q(\d) (Margin PQ|Volume Effect|Mix Effect|Price List Effect|Promotion Effect|Gross Margin|Bridge Check|Units)",
                     label)
    group, year, qn, what = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
    b = _n14().bridge(ctx.data(), group, year, qn)
    return {"Margin PQ": b["pq"], "Volume Effect": b["volume"], "Mix Effect": b["mix"], "Price List Effect": b["lists"],
            "Promotion Effect": b["promotions"], "Gross Margin": b["gm"], "Bridge Check": b["check"], "Units": b["units"]}[what]


def _plain(x: float) -> str:
    """A number as the results grid writes it: no format string, no thousands separator, a zero without a sign."""
    return "0" if abs(x) < 0.005 else f"{round(x, 2):.15g}"


def if_14_0_c() -> Diagram:
    """DAX query view with the Checks tab after Run, scrolled to Exercise 14.4's rows for the last quarter."""
    section = "Exercise 14.4"
    y = ctx.values("ch14.chapter")["y"]
    all_rows = _checks(section)
    first = next(i for i, c in enumerate(all_rows) if c["label"] == f"Furniture {y}-Q4 Margin PQ")
    checks = all_rows[first:first + 12]
    assert len(checks) == 12
    rows = []
    for c in checks:
        a = _ex144_actual(c["label"])
        expected = float(c["expected"])
        assert abs(a - expected) <= c["tolerance"], f"{c['label']}: {a} against {expected}"
        rows.append([section, c["label"], _plain(expected), _plain(a), "True"])
    start, total_rows = _checks_start(section)
    before = start + first
    pane_w = 128
    d = Diagram("The Checks Tab in DAX Query View")
    row_h = pbi.ROW
    height = 96 + 10 + 164 + 14 + 24 + 24 + len(rows) * row_h + 30 + 14
    win = pbi.window(d, height, view="DAX query", tab="Home", tabs=pbi.QUERY_TABS, panes=["Data"], pane_w=pane_w,
                     buttons=["Format", "Comment", "Uncomment", "Find", "Replace", "Command palette"], file=FILE)
    x, w = win.canvas_x + 8, win.canvas_w - 16
    source = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8").split("\n")[:5]
    editor_w = w - 34 - 28
    query = "\n".join(_fit_dax(line, editor_w) for line in source)
    bottom = pbi.dax_query_editor(d, x, win.top + 10, w, query, _query_tabs(), "Checks")
    gy = bottom + 14
    d.text("<b>Results</b>", x, gy, 120, 22, size=SMALL)
    gy += 24
    widths = [96, 248, 112, 120, 60]
    grid_w = sum(widths)
    headers = ["[Section]", "[Check]", "[Expected]", "[Actual]", "[Agrees]"]
    cx = x
    for head, wd in zip(headers, widths):
        d.box(f"<b>{esc(head)}</b>", cx, gy, wd, row_h + 2, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        cx += wd
    geometry = {}
    for r, row in enumerate(rows):
        cx = x
        for c, (value, wd) in enumerate(zip(row, widths)):
            ry = gy + row_h + 2 + r * row_h
            d.box(esc(_clip(value, wd)), cx, ry, wd, row_h, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
            geometry[(r, c)] = (cx, ry, wd, row_h)
            cx += wd
    grid_top, grid_h = gy + row_h + 2, len(rows) * row_h
    sx = x + grid_w + 3
    d.box("", sx, grid_top, 10, grid_h, fill=GRAY_TINT, stroke=RULE, rounded=False)
    th = max(grid_h * len(rows) / total_rows, 14)
    d.box("", sx + 1, grid_top + (grid_h - th) * before / (total_rows - len(rows)), 8, th, fill=GRAY, stroke=GRAY, rounded=False)
    status_y = grid_top + grid_h + 6
    d.text(esc(f"5 columns, {total_rows} rows"), x, status_y, 220, 20, size=SMALL, color=GRAY)
    xl.emphasis(d, geometry[(0, 4)][0], geometry[(0, 4)][1], geometry[(0, 4)][2], len(rows) * row_h)
    for i, name in enumerate(sorted(_loaded_tables())):
        d.text(esc(name), win.panes_x + 8, win.top + 34 + i * 26, pane_w - 12, 22, size=SMALL)
    _note(d, f"The Checks tab of the model answer after Home > Refresh and Run, scrolled to twelve of the {len(all_rows)} rows of {section}: "
             f"Furniture's bridge for {y}-Q4 and the first rows of Lighting's. The query returns {total_rows} rows in all. Long lines of the "
             "query run off the editor's edge, and values are written to the cent. Outlined: Agrees, true in every row.", win.bottom + 10)
    return d


# -- IF-14-0-D: filter context, row context and context transition on a board ---------------------------------------------------------

REVENUE_ALL = ["Revenue All =", "SUM ( SalesInvoiceLine[LineTotal] )"]
REVENUE_OWN = ["Revenue Own =", "CALCULATE (", "    SUM ( SalesInvoiceLine[LineTotal] )", ")"]


def _dax_box(d: Diagram, lines: list[str], x: float, y: float, w: float) -> float:
    """A formula in a bordered box with the editor's highlighting; returns its bottom."""
    html = "<br>".join(pbi.highlight_dax(line) for line in lines)
    for line in lines:
        assert text_width(pbi.highlight_dax(line), SMALL, False) <= w - 12, line
    h = 16 * len(lines) + 12
    d.box(html, x, y, w, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    return y + h


def _customer_rows(d: Diagram, x: float, y: float, w: float, third: str, filler: str) -> float:
    """The Customer table of the board: a header, a column header and three rows, the second the current row; returns its bottom."""
    widths = [112, w - 112]
    d.box("<b>Customer</b>", x, y, w, 24, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False, align="left")
    cx = x
    for head, wd in zip(["CustomerID", third], widths):
        d.box(f"<b>{head}</b>", cx, y + 24, wd, 24, fill=BLUE_TINT, stroke=RULE, size=SMALL, rounded=False, align="left")
        cx += wd
    for r in range(3):
        current = r == 1
        cx = x
        for c, wd in enumerate(widths):
            text = "<b>current row</b>" if (current and c == 0) else filler if c == 1 else "…"
            d.box(text, cx, y + 48 + r * 24, wd, 24, fill=HIGHLIGHT if current else WHITE, stroke=RULE, size=SMALL, rounded=False,
                  align="left")
            cx += wd
    return y + 48 + 3 * 24


def if_14_0_d() -> Diagram:
    """Three panels: a cell's filter context, a calculated column's row context, and the same column inside CALCULATE."""
    d = Diagram("Filter Context, Row Context and Context Transition")
    y = ctx.values("ch14.chapter")["y"]
    groups = _n14().groups(ctx.data())
    assert {"Furniture", "Lighting"} <= set(groups)
    assert "Region" in _model_columns("Customer") and "YearQuarter" in _model_columns("Date")
    assert ("SalesInvoiceLine", "CustomerID") in {r[0] for r in _relationships()}, "Customer relates to the lines directly"
    pw, gap = 274, 19
    xs = [i * (pw + gap) for i in range(3)]
    heads = [("1  Filter context", "A cell of a matrix", BLUE), ("2  Row context", "A calculated column on Customer", GRAY),
             ("3  Context transition", "The same column inside CALCULATE", TEAL)]
    for x, (title, sub, color) in zip(xs, heads):
        d.box(f"<b>{esc(title)}</b>", x, 0, pw, 34, fill=color, stroke=color, color=WHITE, size=14, rounded=False)
        d.text(f"<i>{esc(sub)}</i>", x, 38, pw, 22, size=SMALL, color=GRAY)
    top, sil_y, res_y = 74, 340, 428
    for x in (xs[1] - gap / 2, xs[2] - gap / 2):
        d.box("", x - 0.5, 0, 1, res_y + 52, fill=RULE, stroke=RULE, rounded=False)
    off = 8
    w = pw - 2 * off

    def lines_box(x: float, text: str) -> str:
        return d.box(text, x + off, sil_y, w, 64, fill=BLUE_TINT, stroke=BLUE, size=SMALL, stroke_width=1.5)

    def result(x: float, text: str, src: str) -> None:
        rid = d.box(text, x + off, res_y, w, 52, fill=GRAY_TINT, stroke=GRAY, size=SMALL)
        d.arrow(src, rid, exit=(0.5, 1), entry=(0.5, 0), meta="edgeStyle=none;")

    # 1 - a cell and its three filters
    x = xs[0]
    mw = [86, 86, 86]
    d.box("<b>ItemGroup</b>", x + off, top, mw[0], 24, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False, align="left")
    for c, q in enumerate((3, 4)):
        d.box(f"<b>{y}-Q{q}</b>", x + off + mw[0] + c * mw[1], top, mw[1], 24, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False)
    for r, g in enumerate(("Furniture", "Lighting")):
        d.box(f"<b>{g}</b>", x + off, top + 24 + r * 24, mw[0], 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False, align="left")
        for c in range(2):
            d.box("", x + off + mw[0] + c * mw[1], top + 24 + r * 24, mw[1], 24, fill=WHITE, stroke=RULE, size=SMALL, rounded=False)
    cell_x, cell_y = x + off + mw[0] + mw[1], top + 24
    d.box("<i>Revenue</i>", cell_x, cell_y, mw[1], 24, fill=WHITE, stroke=RULE, size=SMALL, rounded=False)
    xl.emphasis(d, cell_x, cell_y, mw[1], 24)
    d.text("<b>The cell carries three filters:</b>", x + off, top + 90, w, 22, size=SMALL)
    chips = [("Item", "ItemGroup<br>= Furniture", "from the row"), ("Date", f"YearQuarter<br>= {y}-Q4", "from the column"),
             ("Customer", "Region<br>= a selection", "from a slicer")]
    cw, cg = 84, 3
    chip_ids = []
    for i, (table, flt, src) in enumerate(chips):
        chip_ids.append(d.box(f"<b>{table}</b><br>{flt}<br><i>{src}</i>", x + off + i * (cw + cg), top + 118, cw, 84, fill=BLUE_TINT,
                              stroke=BLUE, size=SMALL, stroke_width=1.5))
    sil = lines_box(x, "<b>SalesInvoiceLine</b><br>the relationships carry the filters here; only the lines that pass all three remain")
    for i, cid in enumerate(chip_ids):
        d.arrow(cid, sil, exit=(0.5, 1), entry=((i * (cw + cg) + cw / 2) / w, 0), meta="edgeStyle=none;")
    result(x, "<b>SUM ( LineTotal )</b> adds those lines: the cell shows one number", sil)

    # 2 - a row context and no arrow
    x = xs[1]
    cb = _customer_rows(d, x + off, top, w, "Revenue All", "all lines")
    fb = _dax_box(d, REVENUE_ALL, x + off, cb + 10, w)
    d.box("<b>No arrow.</b> The row is not a filter, so nothing narrows the lines.", x + off, fb + 14, w, 46, fill=CORAL_TINT, stroke=CORAL,
          size=SMALL, stroke_width=1.5)
    sil = lines_box(x, "<b>SalesInvoiceLine</b><br>every line, whatever the row")
    result(x, "<b>Every row reads the same number:</b> the total of all the lines", sil)

    # 3 - the transition
    x = xs[2]
    cb = _customer_rows(d, x + off, top, w, "Revenue Own", "its lines")
    fb = _dax_box(d, REVENUE_OWN, x + off, cb + 10, w)
    sil = lines_box(x, "<b>SalesInvoiceLine</b><br>only the lines of the current customer")
    src = d.container(x + off + 20, fb, 2, 2)
    d.arrow(src, sil, exit=(0.5, 1), entry=(22 / w, 0), color=TEAL, width=2.5, meta="edgeStyle=none;")
    d.text("<b>The current row becomes a filter</b> on Customer, and the relationship carries it", x + off + 34, fb + 6, w - 34, 48, size=SMALL)
    result(x, "<b>Each row reads its own number:</b> that customer's lines only", sil)
    _note(d, "A board sketch with no values, to draw while the class reads the three paragraphs of the section on evaluation context. "
             "The chapter's figures on the filter context of a cell and on row context with and without context transition show the "
             "same ideas with the numbers.", res_y + 66)
    return d


# -- IF-14-1-A: the Ex 14.1 page ---------------------------------------------------------------------------------------------

def if_14_1_a() -> Diagram:
    """The Ex 14.1 page at the latest December: the slicer, the Balance matrix by type and subtype with its zero total, and the
    three balance measures by type with their differences outlined."""
    g = ctx.values("ch14.g1")
    e = ctx.values("ch14.ex1")
    n14 = _n14()
    data = ctx.data()
    y, asof = g["y"], g["asof"]
    slicer = json.dumps(_visual("ex141", "monthEnd"))
    assert f"'{y}-12'" in slicer, "the project's slicer is set to the latest December"
    close = n14.is_close(data)
    sub = data.q("SELECT a.AccountType, a.AccountSubType, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                 f"WHERE g.PostingDate <= ? AND NOT ({close} AND g.PostingDate = ?) GROUP BY 1, 2 ORDER BY 1, 2", asof, asof)
    types = sorted({t for t, _, _ in sub})
    assert types == sorted(n14.TYPES)
    now, kept, gl = n14.by_type(data, asof), n14.by_type(data, asof, "all"), n14.by_type(data, asof, "none")
    for t in types:
        assert abs(sum(v for tt, _, v in sub if tt == t) - now[t]) < 0.005
    assert abs(sum(now.values())) < 0.005 and abs(e["total"]) < 0.005
    rows = []
    for t in types:
        rows.append((0, t, [_signed(now[t])], "-"))
        rows += [(1, s, [_signed(v)], "") for tt, s, v in sub if tt == t]
    rows.append((0, "Total", [_signed(sum(now.values()))], ""))
    variants = [(0, t, [_signed(now[t]), _signed(kept[t]), _signed(gl[t])], "") for t in types]
    variants.append((0, "Total", [_signed(sum(now.values())), _signed(sum(kept.values())), _signed(sum(gl.values()))], ""))
    assert abs(sum(kept.values())) < 0.005 and abs(sum(gl.values())) < 0.005
    differ = [t for t in types if abs(now[t] - kept[t]) > 0.005 or abs(now[t] - gl[t]) > 0.005]
    assert differ == ["Equity", "Expense", "Revenue"], differ
    assert abs(e["liab"] + e["equity"] + e["ni"] - e["now"]["Asset"]) < 0.005 and abs(now["Revenue"] + now["Expense"] + e["ni"]) < 0.005
    page = 16
    lw, rw = [176, 118], [88, 102, 140, 152]
    right_x = page + sum(lw) + 12 + 16
    right_w = 860 - right_x - page
    tie = (f"<b>The ties at {y}-12.</b> The matrix totals {_signed(sum(now.values()))}. Assets {_money(now['Asset'])} equal liabilities "
           f"{_money(-now['Liability'])} plus equity {_money(-now['Equity'])} plus the year's net income {_money(e['ni'])}, each with its sign reversed. "
           f"Revenue and expense together, {_money(now['Revenue'] + now['Expense'])}, are that net income with its sign reversed.")
    read = ("<b>Reading the second matrix.</b> Balance is the pre-closing balance sheet. Balance with Closes is the post-closing one: revenue and "
            f"expense read zero and the year's income sits in equity. Balance on GL Amount leaves every close out, so income never reaches equity "
            f"and revenue and expense hold all {n14.word(len(data.years))} years.")
    slicer_h = 56
    left_h = 36 + 12 + (len(rows) + 1) * pbi.ROW
    variants_h = 20 + 12 + (len(variants) + 1) * pbi.ROW
    right_total = variants_h + 14 + kit.height_for(tie, right_w - 8, SMALL, pad=14) + 14 + kit.height_for(read, right_w - 8, SMALL, pad=14)
    canvas_h = page + max(slicer_h + 12 + left_h, right_total) + page
    d = Diagram("The Ex 14.1 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    pbi.slicer_dropdown(d, page, page, 220, _title("ex141", "monthEnd"), f"{y}-12")
    m1 = _matrix_visual(d, page, page + slicer_h + 12, _title("ex141", "balanceMatrix"), ["AccountType", "Balance"], lw, rows, title_lines=2)
    # the total row, outlined: it is zero
    tx, ty, tw, th = m1["geometry"][(len(rows) - 1, 1)]
    xl.emphasis(d, tx, ty, tw, th)
    m2 = _matrix_visual(d, right_x, page, _title("ex141", "variantsMatrix"), ["AccountType", "Balance", "Balance with Closes", "Balance on GL Amount"], rw,
                        variants, title_lines=1)

    def block(first: str, last: str) -> None:
        a, b = m2["geometry"][(types.index(first), 1)], m2["geometry"][(types.index(last), 3)]
        xl.emphasis(d, a[0] + 1, a[1] + 1, b[0] + b[2] - a[0] - 2, b[1] + b[3] - a[1] - 2)

    block("Equity", "Expense")
    block("Revenue", "Revenue")
    bottom = kit.callout(d, tie, right_x, m2["bottom"] + 14, right_w, "teal")
    kit.callout(d, read, right_x, bottom + 14, right_w, "amber")
    _tabs("ex141", d, canvas_h + 4)
    _note(d, f"Report view, page Ex 14.1, with the slicer on {y}-12 and the rows of the first matrix expanded. Outlined in the first matrix: the "
             f"total, zero. Outlined in the second: the three rows where the measures disagree. Equity reads {_money(now['Equity'])}, "
             f"{_money(kept['Equity'])} and {_money(gl['Equity'])} in the three columns, and revenue and expense together "
             f"{_money(now['Revenue'] + now['Expense'])}, {_signed(kept['Revenue'] + kept['Expense'])} and "
             f"{_money(gl['Revenue'] + gl['Expense'])}.", canvas_h + 34)
    return d


# -- IF-14-1-B: which closing entries each balance measure keeps ---------------------------------------------------------------------

def _close_rule(dax: str) -> str:
    """What a balance measure does with a closing entry, read from its DAX: asof (left out only on the as-of date), keep
    (left in) or drop (left out, through GL Amount)."""
    flat = re.sub(r"\s+", " ", dax)
    gl_amount = re.sub(r"\s+", " ", _g14().measure_table()["GL Amount"])
    if "IsYearEndClose" in flat and "PostingDate] = AsOf" in flat:
        return "asof"
    if "[GL Amount]" in flat and "IsYearEndClose] = FALSE ()" in gl_amount:
        return "drop"
    if "IsYearEndClose" not in flat and "[GL Amount]" not in flat:
        return "keep"
    raise ValueError(dax)


def if_14_1_b() -> Diagram:
    """Three balance measures against the six closing entries: kept or left out at the latest year-end."""
    g = ctx.values("ch14.g1")
    e = ctx.values("ch14.ex1")
    data = ctx.data()
    n14 = _n14()
    asof = g["asof"]
    rules = {"Balance": _close_rule(g["m_balance"]), "Balance with Closes": _close_rule(g["m_closes"]),
             "Balance on GL Amount": _close_rule(g["m_gl"])}
    assert rules == {"Balance": "asof", "Balance with Closes": "keep", "Balance on GL Amount": "drop"}, rules
    closes = []
    for number in data.closes:
        kind, posted = data.q("SELECT EntryType, PostingDate FROM JournalEntry WHERE EntryNumber = ?", number)[0]
        closes.append((number, kind.replace("Year-End Close - ", ""), posted))
    assert len(closes) == 6 and sorted({c[2] for c in closes}) == [f"{yr}-12-31" for yr in data.years]
    now, kept, gl = n14.by_type(data, asof), n14.by_type(data, asof, "all"), n14.by_type(data, asof, "none")
    assert abs(now["Equity"] - e["now"]["Equity"]) < 0.005 and abs(kept["Equity"] - e["kept_equity"]) < 0.005
    shapes = {"P&L to Income Summary": "P&L to<br>Income Summary", "Income Summary to Retained Earnings": "Income Summary<br>to Retained<br>Earnings"}

    def included(rule: str, posted: str) -> bool:
        return {"asof": posted != asof, "keep": True, "drop": False}[rule]

    # the two closes dated on the as-of date are the ones Balance leaves out
    assert [c[0] for c in closes if not included("asof", c[2])] == data.closes_of(data.C)
    head_w, close_w, last_w = 140, 100, 120
    gives = {"Balance": "<b>A pre-closing</b> balance sheet: the year-end reads before its own closes",
             "Balance with Closes": "<b>A post-closing</b> balance sheet: revenue and expense read zero",
             "Balance on GL Amount": "<b>Neither:</b> the year's income never reaches equity"}
    how = {"Balance": "leaves out a close only when it is posted on the as-of date", "Balance with Closes": "leaves out no close",
           "Balance on GL Amount": "leaves out every close, through GL Amount"}
    d = Diagram("The Closing Entries Each Balance Measure Keeps")
    h1, h2, rh = 26, 96, 72
    x0 = 0
    d.box("<b>Measure</b>", x0, 0, head_w, h1 + h2, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False, align="left")
    for k, yr in enumerate(data.years):
        label = f"{yr}: on the as-of date" if f"{yr}-12-31" == asof else f"{yr}: before the as-of date"
        d.box(f"<b>{label}</b>", head_w + k * 2 * close_w, 0, 2 * close_w, h1, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False)
    for k, (number, kind, posted) in enumerate(closes):
        prefix, seq = number.rsplit("-", 1)
        d.box(f"<b>{prefix}-<br>{seq}</b><br>{shapes[kind]}", head_w + k * close_w, h1, close_w, h2, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              rounded=False)
    d.box("<b>What the measure gives</b>", head_w + 6 * close_w, 0, last_w, h1 + h2, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False)
    for r, (name, rule) in enumerate(rules.items()):
        ry = h1 + h2 + r * rh
        d.box(f"<b>{esc(name)}</b><br>{esc(how[name])}", x0, ry, head_w, rh, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False, align="left")
        for k, (number, kind, posted) in enumerate(closes):
            keep = included(rule, posted)
            d.box("<b>✓ kept</b>" if keep else "<b>× left out</b>", head_w + k * close_w, ry, close_w, rh, fill=TEAL_TINT if keep else CORAL_TINT,
                  stroke=TEAL if keep else CORAL, color=INK, size=SMALL, rounded=False, stroke_width=1.5)
        d.box(gives[name], head_w + 6 * close_w, ry, last_w, rh, fill=WHITE, stroke=RULE, size=SMALL, rounded=False, align="left")
    bottom = h1 + h2 + 3 * rh
    xl.emphasis(d, head_w + 4 * close_w, h1, 2 * close_w, h2 + 3 * rh)
    _note(d, f"The six closing entries, two for each year, all dated December 31. At {asof[:7]}, the latest month-end, Balance keeps the closes of "
             f"{data.years[0]} and {data.years[1]}, which are dated before the as-of date and move each year's income to retained earnings, and leaves out "
             f"the two of {data.C}, dated on it (outlined). Equity then reads {_money(now['Equity'])} under Balance, {_money(kept['Equity'])} with "
             f"every close kept and {_money(gl['Equity'])} on GL Amount; revenue and expense read {_money(now['Revenue'] + now['Expense'])} "
             f"(the net income of {data.C}), {_signed(kept['Revenue'] + kept['Expense'])} and {_money(gl['Revenue'] + gl['Expense'])} "
             "(all years).", bottom + 12)
    return d


# -- IF-14-2-A: Model view with the inactive Date relationship (the pilot) ---------------------------------------------------------------

def if_14_2_a() -> Diagram:
    """Model view with the inactive ShipmentDate relationship dashed, the end state of Exercise 14.2's Requirement 3."""
    d = Diagram("Model View with an Inactive Date Relationship")
    shown = {"SalesInvoiceLine": ["SalesInvoiceLineID", "InvoiceDate", "ItemID", "LineTotal"],
             "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit"],
             "Date": ["Date", "Year", "Quarter", "YearMonth"],
             "ShippedLines": ["ShipmentLineID", "ItemID", "LineTotal", "InvoiceDate", "ShipmentDate", "CrossesYear"],
             "Item": ["ItemID", "ItemCode", "ItemGroup"]}
    for table, columns in shown.items():
        _check_columns(table, columns)
    rels = {(m, o): active for m, o, active in _relationships()}
    assert rels[(("ShippedLines", "ShipmentDate"), ("Date", "Date"))] is False, "the ship-date relationship is inactive"
    assert rels[(("ShippedLines", "InvoiceDate"), ("Date", "Date"))] is True and rels[(("ShippedLines", "ItemID"), ("Item", "ItemID"))]
    win = pbi.window(d, 470, view="Model", tab="Home", buttons=["Manage relationships", "New measure", "New column"],
                     file="Chapter 14 Exercises - Solutions")
    top = win.top
    pbi.canvas(d, win.canvas_x, top, 860 - win.canvas_x, win.bottom - top)
    sil = pbi.model_table(d, "SalesInvoiceLine", 100, top + 24, shown["SalesInvoiceLine"], w=160)
    gl = pbi.model_table(d, "GLEntry", 100, top + 190, shown["GLEntry"], w=160)
    date = pbi.model_table(d, "Date", 350, top + 100, shown["Date"], w=140)
    shipped = pbi.model_table(d, "ShippedLines", 600, top + 100, shown["ShippedLines"], w=170)
    item = pbi.model_table(d, "Item", 600, top + 290, shown["Item"], w=170)
    pbi.relationship(d, date.left("Date"), sil.right("InvoiceDate"), [(310, date.rows["Date"]), (310, sil.rows["InvoiceDate"])])
    pbi.relationship(d, date.left("Date"), gl.right("PostingDate"), [(300, date.rows["Date"]), (300, gl.rows["PostingDate"])])
    pbi.relationship(d, date.right("Date"), shipped.left("InvoiceDate"), [(545, date.rows["Date"]), (545, shipped.rows["InvoiceDate"])])
    pbi.relationship(d, date.right("Date"), shipped.left("ShipmentDate"), [(530, date.rows["Date"]), (530, shipped.rows["ShipmentDate"])],
                     dashed=True)
    pbi.relationship(d, item.right("ItemID"), shipped.right("ItemID"), [(812, item.rows["ItemID"]), (812, shipped.rows["ItemID"])])
    y = win.bottom + 10
    d.text("<b>1</b> the table that holds the key &nbsp; <b>*</b> the table that refers to it &nbsp; <b>Solid</b> an active "
           "relationship &nbsp; <b>Dashed</b> an inactive one, used only inside USERELATIONSHIP", 0, y, 860, 40, size=SMALL)
    d.text("<i>The filter arrow points from Date toward each fact table. ShippedLines reaches Date twice: the solid line from "
           "InvoiceDate answers by invoice date, and the dashed line from ShipmentDate answers by ship date when a measure asks "
           "for it.</i>", 0, y + 40, 860, 40, size=SMALL, color=GRAY)
    return d


# -- IF-14-2-B: the year matrix with the (Blank) row ----------------------------------------------------------------------------------

def if_14_2_b() -> Diagram:
    """The Ex 14.2 page: revenue by invoice date, shipped revenue and revenue by ship date by year, with the (Blank) row."""
    e = ctx.values("ch14.ex2")
    g = ctx.values("ch14.g2")
    data = ctx.data()
    years = data.years
    y = g["y"]
    assert e["before"]["n"] == 0, "no line is dated before the Date table"
    assert abs(e["blank"] - sum(e["by_services"])) < 0.005, "the (Blank) amount is the Services revenue"
    for inv, shp in zip(e["by_invoice"], e["by_ship"]):
        assert shp < inv, "revenue by ship date is lower in every year"
    assert abs(e["all"] - sum(e["by_invoice"])) < 0.005 and abs(e["all"] - sum(e["by_ship"]) - e["blank"]) < 0.005
    rows = [(0, str(yr), [_money(e["by_invoice"][i]), _money(e["by_invoice"][i]), _money(e["by_ship"][i])], "") for i, yr in enumerate(years)]
    rows.append((0, "(Blank)", ["", "", _money(e["blank"])], ""))
    rows.append((0, "Total", [_money(e["all"])] * 3, ""))
    widths = [94, 128, 140, 160]
    page = 16
    title = _title("ex142", "yearMatrix")
    h = 4 + 20 + 2 + 12 + (len(rows) + 1) * pbi.ROW
    note_x = page + sum(widths) + 12 + 16
    text = (f"<b>The (Blank) row</b> holds the {g['n_services']:,} Services lines. Design services do not ship, so the inactive "
            "relationship finds no ship date for them, and their revenue lands under (Blank) in the last column only.<br><br>"
            "Revenue and Shipped Revenue agree in every year, because both use the invoice date. Each year is lower by ship date mainly "
            "because Services drop out of it.")
    text_h = kit.height_for(text, 860 - note_x - page - 8, SMALL, pad=14)
    canvas_h = page + max(h, text_h + 8) + page
    d = Diagram("The Ex 14.2 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    m = _matrix_visual(d, page, page, title, ["Year", "Revenue", "Shipped Revenue", "Revenue by Ship Date"], widths, rows, title_lines=1)
    bx, by, bw, bh = m["geometry"][(len(years), 3)]
    ax, ay, aw, ah = m["geometry"][(len(years), 0)]
    xl.emphasis(d, ax, ay, bx + bw - ax, bh)
    kit.callout(d, text, note_x, page, 860 - note_x - page, "teal")
    _tabs("ex142", d, canvas_h + 4)
    _note(d, f"Report view, page Ex 14.2. The year {data.N}, which the Date table holds and the invoice lines do not, has no row: every measure is "
             "blank there. Outlined: the (Blank) row.", canvas_h + 34)
    return d


# -- IF-14-3-A: the year-on-year matrix ---------------------------------------------------------------------------------------------

def if_14_3_a() -> Diagram:
    """The Ex 14.3 page: revenue against the same month of the prior year, by item group and month of the latest year."""
    g = ctx.values("ch14.g3")
    e = ctx.values("ch14.ex3")
    data = ctx.data()
    n14 = _n14()
    y = g["y"]
    groups = n14.groups(data)
    assert groups == ["Accessories", "Furniture", "Lighting", "Services", "Textiles"]
    month_names = n14.MONTHS
    yoy = {grp: n14.swing(data, grp) for grp in groups}
    now = {grp: n14.monthly(data, grp, y) for grp in groups}
    before = {grp: n14.monthly(data, grp, data.P) for grp in groups}
    rows = []
    for grp in groups:
        values = [_pct(v) for v in yoy[grp]["yoy"]] + [_pct(sum(now[grp]) / sum(before[grp]) - 1)]
        rows.append((0, grp, values, ""))
    tot_now, tot_before = [sum(now[grp][m] for grp in groups) for m in range(12)], [sum(before[grp][m] for grp in groups) for m in range(12)]
    rows.append((0, "Total", [_pct(a / b - 1) for a, b in zip(tot_now, tot_before)] + [_pct(sum(tot_now) / sum(tot_before) - 1)], ""))
    fi = groups.index("Furniture")
    low, high = month_names.index(e["low"]), month_names.index(e["high"])
    assert abs(yoy["Furniture"]["yoy"][low] - e["months"][low]["yoy"]) < 1e-9 and min(yoy["Furniture"]["yoy"]) == yoy["Furniture"]["yoy"][low]
    assert max(yoy["Furniture"]["yoy"]) == yoy["Furniture"]["yoy"][high]
    widths = [84] + [56] * 12 + [60]
    heads = ["ItemGroup"] + [f"{y}-{m:02d}" for m in range(1, 13)] + ["Total"]
    page = 16
    title = _title("ex143", "yoyMatrix")
    h = 4 + 20 + 2 + 12 + (len(rows) + 1) * pbi.ROW
    canvas_h = page + h + page
    d = Diagram("The Ex 14.3 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    m = _matrix_visual(d, page, page, title, heads, widths, rows, title_lines=1)
    ax, ay, aw, ah = m["geometry"][(fi, 0)]
    xl.emphasis(d, ax, ay, sum(widths), ah)
    for month, color in ((low, AMBER), (high, TEAL)):
        cx, cy, cw, ch = m["geometry"][(fi, month + 1)]
        d.outline(cx + 1, cy + 1, cw - 2, ch - 2, color, width=3, front=True)
    for name in ("Services", "Textiles"):
        assert name in sorted(groups, key=lambda grp: -yoy[grp]["spread"])[:2]
    _tabs("ex143", d, canvas_h + 4)
    s, t = yoy["Services"], yoy["Textiles"]
    _note(d, f"Report view, page Ex 14.3, filtered to {y}; percentages read as the format 0.0% shows them. Outlined in coral: the Furniture row. "
             f"Furniture's largest decline, in {e['low']} (outlined in amber), and its largest increase, in {e['high']} (outlined in teal), are the "
             f"cells to find. Services ({_pct(s['low'])} to {_pct(s['high'])}) and Textiles ({_pct(t['low'])} to {_pct(t['high'])}) swing the most.",
          canvas_h + 34)
    return d


# -- IF-14-3-B: the unfiltered year table before and after the change to Revenue PY -------------------------------------------------------

def if_14_3_b() -> Diagram:
    """Two tables of Year, Revenue and Revenue PY with no filter: with Revenue PY as first written, and as changed."""
    g = ctx.values("ch14.g3")
    e = ctx.values("ch14.ex3")
    data = ctx.data()
    n14 = _n14()
    y, n = g["y"], g["n"]
    by_year = {yr: n14.total(n14.pick(data, year=yr), "rev") for yr in data.years}
    everything = n14.total(n14.lines(data), "rev")
    assert abs(sum(by_year.values()) - everything) < 0.005, "every line is dated inside the Date table"
    assert abs(by_year[y] - e["now_total"]) < 0.005
    first = _g14().PY_FIRST
    assert first in re.sub(r"\s+", " ", _g14().measure_table()["Revenue PY"]), "the model answer's measure wraps the first version"
    years = [*data.years, n]
    # as first written: SAMEPERIODLASTYEAR alone; Revenue is blank where there are no lines, and the prior year is whatever the year before holds
    left = [[str(yr), _money(by_year[yr]) if yr in by_year else "", _money(by_year[yr - 1]) if yr - 1 in by_year else ""] for yr in years]
    # as changed: Revenue PY is blank wherever Revenue is blank, so a year with no revenue has no row at all (a table drops a row of blanks)
    right = [[str(yr), _money(by_year[yr]), _money(by_year[yr - 1]) if yr - 1 in by_year else ""] for yr in years if yr in by_year]
    total = ["Total", _money(everything), _money(everything)]
    widths = [64, 134, 134]
    page = 16
    lt = f"Revenue and Revenue PY by year, no filter (Revenue PY as first written)"
    rt = _title("ex143", "pyTable")
    assert "as changed" in rt
    h_left = 4 + 32 + 4 + 12 + (len(left) + 2) * pbi.ROW
    canvas_h = page + h_left + page
    d = Diagram("The Ex 14.3 Year Table Before and After the Change")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    t1 = _table_visual(d, page, page, lt, ["Year", "Revenue", "Revenue PY"], widths, left, total=total, title_lines=2)
    t2 = _table_visual(d, t1["right"] + 16, page, rt, ["Year", "Revenue", "Revenue PY"], widths, right, total=total, title_lines=2)
    gx, gy, gw, gh = t1["geometry"][(len(years) - 1, 2)]
    xl.emphasis(d, t1["geometry"][(len(years) - 1, 0)][0], gy, sum(widths), gh)
    # the row that is no longer there, drawn where it was
    rx, ry, rw, rh = t2["geometry"][(len(right), 0)]
    d.box(f"<i>no row for {n}</i>", rx, ry, sum(widths), rh, fill=WHITE, stroke=RULE, size=SMALL, dashed=True, rounded=False, color=GRAY)
    ax, ay, aw, ah = t1["geometry"][(0, 2)]
    d.outline(ax + 1, ay + 1, aw - 2, ah - 2, TEAL, width=3, front=True)
    _tabs("ex143", d, canvas_h + 4)
    _note(d, f"Report view, page Ex 14.3, two versions of the table of Requirement 5. Left, Revenue PY as first written: the year {n} has "
             f"a Revenue PY, the revenue of {y}, and no revenue, and the first year, {data.years[0]}, has revenue and no Revenue PY (outlined in "
             f"teal). Right, Revenue PY as changed, blank wherever Revenue is blank: both measures are blank for {n}, so the table drops its row "
             f"(drawn dashed). The totals do not change.", canvas_h + 34)
    return d


# -- IF-14-4-A: the Furniture bridge matrix ------------------------------------------------------------------------------------------

def _bridge_between(cur: list[dict], prior: list[dict]) -> dict:
    """Exercise 14.4's measures for any two sets of lines (the current dates and the dates DATEADD returns): the same
    formulas as notes.ch14.bridge, which works on one quarter and the quarter before it."""
    n14 = _n14()
    a, b = n14.quarter_totals(prior), n14.quarter_totals(cur)
    out = dict(pq=a["gm"], volume=(b["units"] - a["units"]) * a["gm"] / a["units"],
               mix=b["units"] * (b["list_margin"] - a["list_margin"]),
               lists=-b["units"] * (b["reduction"] - a["reduction"]),
               promotions=-b["units"] * (b["discount"] - a["discount"]), gm=b["gm"])
    out["check"] = out["pq"] + out["volume"] + out["mix"] + out["lists"] + out["promotions"] - out["gm"]
    return out


def if_14_4_a() -> Diagram:
    """The Ex 14.4 page's Furniture matrix: the four quarters of the latest year and the Total row, Bridge Check at zero."""
    g = ctx.values("ch14.g4")
    e = ctx.values("ch14.ex4")
    data = ctx.data()
    n14 = _n14()
    y = g["y"]
    quarters = e["quarters"]
    assert [q["label"] for q in quarters] == ["Q1", "Q2", "Q3", "Q4"]
    title = _title("ex144", "bridgeFurniture")
    assert title == g["t_furniture"] == f"Furniture margin bridge by quarter, fiscal {y}"
    visual = _visual("ex144", "bridgeFurniture")["visual"]["query"]["queryState"]
    values = [p["nativeQueryRef"] for p in visual["Values"]["projections"]]
    assert [p["nativeQueryRef"] for p in visual["Rows"]["projections"]] == ["YearQuarter"]
    assert values == ["Margin PQ", "Volume Effect", "Mix Effect", "Price List Effect", "Promotion Effect", "Gross Margin", "Bridge Check"]
    _check_columns("Key Measures", values)
    filters = json.dumps(_visual("ex144", "bridgeFurniture")["filterConfig"])
    assert f"'Furniture'" in filters and f"{y}L" in filters, "the visual is filtered to the latest year and to Furniture"
    # the Total row: the year against the same dates moved back one quarter (DATEADD on the year's dates)
    cur = n14.pick(data, group="Furniture", year=y)
    prior = [r for r in n14.pick(data, group="Furniture") if f"{y - 1}-10-01" <= r["date"] <= f"{y}-09-30"]
    tot = _bridge_between(cur, prior)
    q4 = _bridge_between(n14.pick(data, group="Furniture", year=y, quarter=4), n14.pick(data, group="Furniture", year=y, quarter=3))
    assert all(abs(q4[k] - quarters[3][k]) < 0.005 for k in ("pq", "volume", "mix", "lists", "promotions", "gm")), "the helper repeats the note's formulas"
    assert abs(tot["check"]) < 0.005, "the bridge is exact for any pair of periods"
    assert abs(tot["pq"] - sum(q["pq"] for q in quarters)) < 0.005 and abs(tot["gm"] - sum(q["gm"] for q in quarters)) < 0.005
    keys = ["pq", "volume", "mix", "lists", "promotions", "gm", "check"]
    rows = [(0, f"{y}-{q['label']}", [_signed(q[k]) for k in keys], "") for q in quarters]
    rows.append((0, "Total", [_signed(tot[k]) for k in keys], ""))
    q3, q4 = quarters[2], quarters[3]
    decline = q4["pq"] - q4["gm"]
    small = q4["volume"] + q4["mix"] + q4["lists"]
    assert -q4["promotions"] > decline > 0 and abs(small + q4["promotions"] + decline) < 0.005
    widths = [90, 92, 100, 84, 112, 118, 98, 98]
    page = 16
    mw = sum(widths) + 12
    read = (f"<b>Reading {y}-Q4.</b> The margin falls from {_money(q4['pq'])} to {_money(q4['gm'])}, a decline of {_money(decline)}. The promotion "
            f"effect, {_signed(q4['promotions'])}, is larger than the whole decline; volume, mix and price lists together add "
            f"+{_money(small)}. Bridge Check reads 0.00 in every row: the four effects explain each quarter's change.")
    read_h = kit.height_for(read, mw - 8, SMALL, pad=14)
    mh = 20 + 12 + (len(rows) + 1) * pbi.ROW
    canvas_h = page + mh + 14 + read_h + page
    d = Diagram("The Ex 14.4 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    m = _matrix_visual(d, page, page, title, ["YearQuarter", *values], widths, rows, title_lines=1)
    geo = m["geometry"]
    r4 = len(quarters) - 1
    ax, ay, aw, ah = geo[(r4, 0)]
    gx, gy, gw, gh = geo[(r4, 6)]
    d.outline(ax - 1, ay + 1, gx + gw - ax + 1, ah - 2, CORAL, width=2.5, front=True)
    px, py, pw, ph = geo[(r4, 5)]
    d.outline(px + 2, py + 3, pw - 4, ph - 6, AMBER, width=3, front=True)
    cx, cy, cw, ch = geo[(0, 7)]
    lx, ly, lw, lh = geo[(len(rows) - 1, 7)]
    d.outline(cx + 2, cy + 1, cw - 4, ly + lh - cy - 2, TEAL, width=2.5, front=True)
    kit.callout(d, read, page, m["bottom"] + 14, mw, "amber")
    _tabs("ex144", d, canvas_h + 4)
    _note(d, f"Report view, page Ex 14.4, the Furniture matrix, filtered to {y} and Furniture; values as the format #,0.00 shows them. Outlined in "
             f"coral: the {y}-Q4 row, with its promotion effect in amber, larger than the whole decline; in teal: Bridge Check, zero in every row. "
             f"The Total row compares the whole year with the same dates moved back one quarter, so its effects are those of that comparison "
             f"and not the sum of the rows; Bridge Check is still zero. The page holds a second matrix for Lighting and the model answer's "
             f"text box, not drawn here.", canvas_h + 34)
    return d


# -- IF-14-4-B: the bridge as a waterfall ---------------------------------------------------------------------------------------------

def if_14_4_b() -> Diagram:
    """A waterfall from Margin PQ to Gross Margin for the last quarter of the latest year, a truncated axis, and the formula of each step in words."""
    g = ctx.values("ch14.g4")
    e = ctx.values("ch14.ex4")
    y = g["y"]
    q3, q4 = e["quarters"][2], e["quarters"][3]
    assert abs(q4["pq"] - q3["gm"]) < 0.005, "Margin PQ of a quarter is the Gross Margin of the one before"
    steps = [("Volume effect", q4["volume"], "change in units × margin per unit of the prior quarter"),
             ("Mix effect", q4["mix"], "units × change in list margin per unit"),
             ("Price list effect", q4["lists"], "−units × change in the cut from list price to the price before discounts"),
             ("Promotion effect", q4["promotions"], "−units × change in discount per unit")]
    levels = [q4["pq"]]
    for _, v, _ in steps:
        levels.append(levels[-1] + v)
    assert abs(levels[-1] - q4["gm"]) < 0.005 and abs(q4["check"]) < 0.005, "Margin PQ and the four effects add up to Gross Margin"
    decline = q4["pq"] - q4["gm"]
    big = max(steps, key=lambda s: abs(s[1]))
    assert big[0] == "Promotion effect" and big[1] < 0 and all(abs(v) < 0.1 * abs(big[1]) for n, v, _ in steps if n != big[0])
    d = Diagram("The Furniture Bridge as a Waterfall")
    names = ["Margin PQ", *[s[0] for s in steps], "Gross Margin"]
    top = 24
    step = 50_000
    ymin = math.floor((min(levels) - 20_000) / step) * step
    ymax = math.ceil((max(levels) + 25_000) / step) * step
    ticks = [ymin + i * step for i in range((ymax - ymin) // step + 1)]
    d.text(f"<b>Furniture gross margin, {y}-Q3 to {y}-Q4: from Margin PQ to Gross Margin</b>", 0, 0, 860, 22, size=SMALL)
    plot_h = 330
    plot = kit.Plot(d, 0, top, 860, plot_h, y_ticks=ticks, categories=[""] * 6, y_fmt=lambda v: f"{v / 1e6:.2f}M", bottom=8)
    slot = plot.pw / 6
    bar_w = slot * 0.6

    def bar(i: int, low: float, high: float, color: str) -> tuple[float, float, float, float]:
        x0 = plot.x_of(i) - bar_w / 2
        top_y, base_y = plot.y_of(high), plot.y_of(low)
        h = max(base_y - top_y, 3)
        d.box("", x0, top_y, bar_w, h, fill=color, stroke=color, rounded=False)
        return x0, top_y, bar_w, h

    def label(i: int, text: str, level: float) -> None:
        d.box(f"<b>{text}</b>", plot.x_of(i) - 56, plot.y_of(level) - 23, 112, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)

    # connectors at the running total, then the bars and their signed labels
    for i, level in enumerate(levels):
        d.box("", plot.x_of(i) + bar_w / 2, plot.y_of(level) - 0.75, slot - bar_w, 1.5, fill=GRAY, stroke=GRAY, rounded=False)
    start = bar(0, ymin, levels[0], BLUE)
    label(0, _money(levels[0]), levels[0])
    for i, (_, v, _) in enumerate(steps, 1):
        low, high = sorted((levels[i - 1], levels[i]))
        bar(i, low, high, TEAL if v >= 0 else CORAL)
        label(i, f"{'+' if v >= 0 else '−'}{_money(abs(v))}", high)
    end = bar(5, ymin, levels[-1], BLUE)
    label(5, _money(levels[-1]), levels[-1])
    for x0, y0, w0, h0 in (start, end):                 # the axis does not start at zero: a gap near the base of each blue bar
        d.box("", x0 - 1, plot.y_of(ymin) - 22, w0 + 2, 5, fill=WHITE, stroke=WHITE, rounded=False)
    # the decline: a dashed line at Margin PQ across to the last bar, and an arrow down to its top
    x_end = plot.x_of(5)
    d.edge(d.anchor(plot.x_of(4) + bar_w / 2, plot.y_of(levels[0])), d.anchor(x_end + slot / 2 - 4, plot.y_of(levels[0])), color=GRAY, width=1.5,
           dashed=True, meta="edgeStyle=none;")
    arrow_x = x_end - slot / 2 + 16
    a, b = d.anchor(arrow_x, plot.y_of(levels[0]) + 2), d.anchor(arrow_x, plot.y_of(levels[-1]) - 2)
    d.edge(a, b, start="blockThin", end="blockThin", color=INK, width=1.5, meta="edgeStyle=none;")
    d.box(f"<b>−{_money(decline)}</b><br>the decline", arrow_x + 8, (plot.y_of(levels[0]) + plot.y_of(levels[-1])) / 2 - 18, 100, 40,
          fill=WHITE, stroke=WHITE, size=SMALL, align="left", rounded=False)
    # what each bar is, and each step in words
    fy = top + plot_h + 8
    texts = [("Margin PQ", f"Gross Margin of {y}-Q3, the quarter before", BLUE_TINT, BLUE)]
    for name, v, formula in steps:
        texts.append((name, formula, TEAL_TINT if v >= 0 else CORAL_TINT, TEAL if v >= 0 else CORAL))
    texts.append(("Gross Margin", f"of {y}-Q4: Margin PQ plus the four effects; Bridge Check is the difference, 0.00", BLUE_TINT, BLUE))
    html = [f"<b>{esc(n)}</b><br>{esc(t)}" for n, t, _, _ in texts]
    bh = max(kit.height_for(h, slot - 12, SMALL, pad=12) for h in html)
    for i, (h, (_, _, fill, stroke)) in enumerate(zip(html, texts)):
        d.box(h, plot.x_of(i) - slot / 2 + 5, fy, slot - 10, bh, fill=fill, stroke=stroke, size=SMALL, align="left", valign="top", stroke_width=1.5)
    ly = fy + bh + 12
    kit.legend(d, 0, ly, [("Margin (start and end)", BLUE, "box"), ("Increase, with a plus sign", TEAL, "box"), ("Decrease, with a minus sign", CORAL, "box")])
    _note(d, f"Furniture, {y}-Q4 against {y}-Q3. The vertical axis starts at {ymin:,.0f}, not at zero, so that the three small steps show; the two blue bars "
             f"are cut near the base. Volume, mix and price lists together add {_money(q4['volume'] + q4['mix'] + q4['lists'])}, and the promotion effect "
             f"takes away {_money(-q4['promotions'])}, more than the whole decline of {_money(decline)}. No cost effect is drawn: each item has one "
             "standard cost, so a unit's cost changes only through the mix of items, and the mix effect already holds it.", ly + 28)
    return d


# -- the DAX query view of Exercises 14.5 and 14.6 -----------------------------------------------------------------------------------

def _dax_file(tab: str) -> str:
    return (MODEL / "DAXQueries" / f"{tab}.dax").read_text(encoding="utf-8")


def _editor(d: Diagram, x: float, y: float, w: float, rows: list[tuple[int | None, str]], tab: str, updates: int,
            selected: range | None = None) -> dict:
    """DAX query view's Run button, query tabs and editor.  rows are (line number, text): the editor shows long lines cut at its
    edge, and a row with no number is a gap whose text says which lines the picture leaves out.  selected holds the line
    numbers drawn selected.  Returns the editor's top and bottom and the y of each line."""
    xl.button(d, x, y, 70, "▶ Run", primary=True)
    xl.button(d, x + 78, y, 214, f"Update model with changes ({updates})")
    y += 32
    cx = x
    for name in _query_tabs():
        on = name == tab
        width = text_width(esc(name), SMALL, on) + 24
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), cx, y, width, 24, fill=WHITE, stroke=BLUE if on else RULE,
              stroke_width=2 if on else 1, color=BLUE if on else INK, size=SMALL, rounded=False)
        cx += width + 2
    d.box("<b>+</b>", cx, y, 26, 24, fill=WHITE, stroke=RULE, size=SMALL, rounded=False)
    y += 24
    gutter, line_h = 34, 20
    height = len(rows) * line_h + 8
    d.box("", x, y, gutter, height, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.box("", x + gutter, y, w - gutter, height, fill=WHITE, stroke=RULE, rounded=False)
    ys = {}
    for i, (number, _) in enumerate(rows):
        if number is not None:
            ys[number] = y + 4 + i * line_h
    if selected:
        first, last = min(selected), max(selected)
        d.box("", x + gutter + 1, ys[first], w - gutter - 2, ys[last] + line_h - ys[first], fill=BLUE_TINT, stroke=BLUE_TINT, rounded=False)
    for i, (number, text) in enumerate(rows):
        ly = y + 4 + i * line_h
        if number is None:
            d.box(f"<i>{esc(text)}</i>", x + gutter + 4, ly + 1, w - gutter - 8, line_h - 2, fill=GRAY_TINT, stroke=GRAY_TINT, color=GRAY,
                  size=SMALL, align="left", rounded=False)
            continue
        d.text(str(number), x, ly, gutter - 4, line_h, size=SMALL, color=GRAY, align="right", valign="middle")
        label = pbi.highlight_dax(text)
        assert text_width(label, SMALL, False) <= w - gutter - 12, f"{d.name}: DAX line too wide: {text}"
        d.text(label or " ", x + gutter + 4, ly, w - gutter - 8, line_h, size=SMALL, valign="middle")
    return dict(top=y, bottom=y + height, ys=ys, left=x + gutter, width=w - gutter, line_h=line_h)


def _editor_rows(lines: list[str], numbers: list[int], width: float) -> list[tuple[int, str]]:
    return [(n, _fit_dax(lines[n - 1], width)) for n in numbers]


def _names_pane(d: Diagram, win, pane_w: float) -> None:
    for i, name in enumerate(sorted(_loaded_tables())):
        d.text(esc(name), win.panes_x + 8, win.top + 34 + i * 26, pane_w - 12, 22, size=SMALL)


# -- IF-14-5-A: the three customer counts ------------------------------------------------------------------------------------------------

def if_14_5_a() -> Diagram:
    """DAX query view, tab Ex 14.5: the first query selected, and its result, one row per item group."""
    g = ctx.values("ch14.g5")
    e = ctx.values("ch14.ex5")
    y = g["y"]
    tab = _dax_file("Ex 14.5")
    lines = tab.split("\n")
    end = lines.index(")") + 1                      # the first query ends with the first unindented closing parenthesis
    assert "\n".join(lines[:end]) == g["q1"], "the first query of the tab is the guide's"
    assert lines[end] == "" and lines[end + 1].startswith("// (2) Operating expense")
    updates = len(re.findall(r"^    MEASURE ", g["q1"], re.M))
    assert updates == 3 and f"{{ {y} }}" in g["q1"], "three measures defined in the query, and the latest year from TREATAS"
    groups = [x["group"] for x in e["invoiced"]]
    assert groups == _n14().groups(ctx.data()) and len(groups) == 5
    rows = [[x["group"], str(e["customers"]), str(x["n"]), str(x["n"])] for x in e["invoiced"]]
    assert len({r[1] for r in rows}) == 1, "Customer Rows is the same in every row"
    assert e["customers"] > e["n_invoiced"] > max(x["n"] for x in e["invoiced"]), "customers that did not buy in the year, and customers that bought from several groups"
    pane_w = 128
    d = Diagram("The Ex 14.5 Query and Its Result")
    n_rows = end + 2
    height = 96 + 10 + 56 + n_rows * 20 + 8 + 14 + 24 + pbi.ROW + 2 + len(rows) * pbi.ROW + 26 + 12
    win = pbi.window(d, height, view="DAX query", tab="Home", tabs=pbi.QUERY_TABS, panes=["Data"], pane_w=pane_w,
                     buttons=["Format", "Comment", "Uncomment", "Find", "Replace", "Command palette"], file=FILE)
    x, w = win.canvas_x + 8, win.canvas_w - 16
    ed = _editor(d, x, win.top + 10, w, _editor_rows(lines, list(range(1, end + 3)), w - 34 - 28), "Ex 14.5", updates, selected=range(1, end + 1))
    res = pbi.dax_results(d, x, ed["bottom"] + 14, ["Item[ItemGroup]", "[Customer Rows]", "[Customers Invoiced]", "[Customer Rows Both]"],
                          [128, 128, 156, 164], rows)
    geo = res["geometry"]
    c1, c2, c3 = geo[(0, 1)], geo[(0, 2)], geo[(0, 3)]
    last = len(rows) - 1
    d.outline(c1[0] + 1.5, c1[1] + 1.5, c1[2] - 3, geo[(last, 1)][1] + pbi.ROW - c1[1] - 3, CORAL, width=2.5, front=True)
    d.outline(c2[0] + 1.5, c2[1] + 1.5, c2[2] + c3[2] - 3, geo[(last, 2)][1] + pbi.ROW - c2[1] - 3, TEAL, width=2.5, front=True)
    _names_pane(d, win, pane_w)
    _note(d, f"The tab Ex 14.5 with the first of its three queries selected and run, as Tutorial 14.2 runs a part of a tab. The tab has the DEFINE block and "
             f"the query for fiscal {y}; the next query's comment shows below it. Outlined in coral: Customer Rows, "
             f"{e['customers']} in every row, because a selection on Item or Date never reaches the Customer table; in teal: Customers Invoiced and Customer "
             f"Rows Both, equal in every row. The five counts add up to {g['sum_groups']} against {e['n_invoiced']} customers in the year, because customers "
             "buy from several groups. The count on the Update model button is the measures the query defines.", win.bottom + 10)
    return d


# -- IF-14-5-B: how a selection on Item reaches the ledger ----------------------------------------------------------------------------------

def _lane(d: Diagram, x1: float, x2: float, y: float, color: str = GRAY, width: float = 1.5, dashed: bool = False,
          label: str | None = None, bold: bool = False) -> None:
    """A straight arrow from x1 to x2 at height y, with its label above the line."""
    d.arrow(d.anchor(x1, y), d.anchor(x2, y), color=color, width=width, dashed=dashed, meta="edgeStyle=none;")
    if label:
        mid = (x1 + x2) / 2
        w = text_width(label, SMALL, bold) + 14
        d.text(f"<b>{esc(label)}</b>" if bold else esc(label), mid - w / 2, y - 25, w, 18, size=SMALL, align="center")


def if_14_5_b() -> Diagram:
    """Four tables in a row and the path a selection on Item takes into the ledger when the Date relationship is set to Both."""
    g = ctx.values("ch14.g5")
    e = ctx.values("ch14.ex5")
    n14 = _n14()
    rel = {(m, o): active for m, o, active in _relationships()}
    for pair in ((("SalesInvoiceLine", "ItemID"), ("Item", "ItemID")), (("SalesInvoiceLine", "InvoiceDate"), ("Date", "Date")),
                 (("GLEntry", "PostingDate"), ("Date", "Date"))):
        assert rel[pair] is True, pair
    assert "CROSSFILTER ( SalesInvoiceLine[InvoiceDate], 'Date'[Date], BOTH )" in g["q2"], "the query sets the Date relationship to Both"
    services = e["services"]
    assert services["group"] == "Services" and services["days"] < e["year_days"] and services["opex"] < e["opex"]
    d = Diagram("The Path of a Selection into the Ledger")
    bw = [112, 170, 104, 130]
    gap = (860 - sum(bw)) / 3
    xs = [sum(bw[:i]) + gap * i for i in range(4)]
    by, bh = 76, 104
    specs = [("Item", "a dimension of the sales star", BLUE_TINT, BLUE), ("SalesInvoiceLine", "fact table of the sales star", BLUE_TINT, BLUE),
             ("Date", "shared by both stars", GRAY_TINT, GRAY), ("GLEntry", "fact table of the ledger star", TEAL_TINT, TEAL)]
    ids = [d.box(f"<b>{n}</b><br>{esc(t)}", xs[i], by, bw[i], bh, fill=f, stroke=s, size=SMALL, stroke_width=1.5) for i, (n, t, f, s) in enumerate(specs)]
    up, low = by + 30, by + 78
    # the model's relationships, each a Single filter from the dimension to the fact table
    _lane(d, xs[0] + bw[0], xs[1], up, label="Single")
    _lane(d, xs[2], xs[1] + bw[1], up, label="Single")
    _lane(d, xs[2] + bw[2], xs[3], up, label="Single")
    # the setting under test, and what it lets through
    _lane(d, xs[1] + bw[1], xs[2], low, color=CORAL, width=2.5, dashed=True, label="Both", bold=True)
    _lane(d, xs[2] + bw[2], xs[3], low, color=AMBER, width=2.5, label="the ledger follows", bold=True)
    # the selection that starts it, and where it lands
    chip = d.box(f"<b>A selection on Item</b><br>ItemGroup = {esc(services['group'])}", 0, 0, 176, 44, fill=AMBER_TINT, stroke=AMBER, size=SMALL, stroke_width=1.5)
    d.arrow(chip, ids[0], exit=(0.33, 1), entry=(0.5, 0), meta="edgeStyle=none;")
    cy, ch = by + bh + 34, 58
    cw1, cw2 = 176, 206
    cx1 = xs[2] + bw[2] / 2 - cw1 / 2
    days = d.box(f"<b>{services['days']} of {e['year_days']} dates left</b><br>only the days with a {esc(services['group'])} invoice", cx1, cy, cw1, ch,
                 fill=AMBER_TINT, stroke=AMBER, size=SMALL, stroke_width=1.5)
    d.arrow(ids[2], days, exit=(0.5, 1), entry=(0.5, 0), meta="edgeStyle=none;")
    cx2 = 860 - cw2
    result = d.box(f"<b>Operating Expense {_money(services['opex'])}</b><br>of those days, not {_money(e['opex'])} for the year", cx2, cy, cw2, ch,
                   fill=AMBER_TINT, stroke=AMBER, size=SMALL, stroke_width=1.5)
    d.arrow(ids[3], result, exit=(0.5, 1), entry=((xs[3] + bw[3] / 2 - cx2) / cw2, 0), meta="edgeStyle=none;", color=AMBER, width=2.5)
    ly = cy + ch + 18
    kit.legend(d, 0, ly, [("A relationship set to Single: the filter runs from the dimension to the fact table", GRAY, "line")])
    kit.legend(d, 0, ly + 22, [("The relationship set to Both for the calculation", CORAL, "dashed"), ("What the setting lets through", AMBER, "line")])
    kit.callout(d, f"<b>The selection came from the sales star and the result lands in the ledger.</b> Operating Expense carries no filter on Item, yet it reads "
                   f"{_money(services['opex'])}: Both lets the invoice lines filter Date, and Date filters GLEntry. The figure is the expense of "
                   f"the {n14.word(services['days'])} days on which design services were invoiced, a number with no meaning.", 0, ly + 54, 860, "amber")
    return d


# -- IF-14-6-A and IF-14-6-B: the Control Totals tab --------------------------------------------------------------------------------------------

def _control_totals(fail: bool) -> Diagram:
    g = ctx.values("ch14.g6")
    e = ctx.values("ch14.ex6")
    data = ctx.data()
    n14 = _n14()
    y = g["y"]
    query = g["query"]
    lines = query.split("\n")
    tests = re.findall(r'ROW \( "Test", "([^"]+)", "Expected", ([-\d.]+),', query)
    assert len(tests) == 7
    actual = [e["n"], e["rev"], e["ni"], e["debits"], e["variance"], e["ledger"], e["ledger"] - e["rev"]]
    for (name, expected), a in zip(tests, actual):
        assert abs(a - float(expected)) <= 0.01, f"{name}: the model answer's expected value against the dataset"
    fails = {2, 4}                                  # the net income and the manufacturing variance read GL Amount over every account
    assert [tests[i][0] for i in sorted(fails)] == [f"Net income, fiscal {y}", f"Manufacturing variance (5080), fiscal {y}"]
    shown = list(actual)
    if fail:
        # with the closes kept, each year's revenue and expense net to zero and so does 5080; no other test reads a closing entry
        assert abs(n14.net_income(data, data.C, closes=True)) < 0.005
        assert abs(data.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND substr(PostingDate, 1, 4) = ?", data.account("5080"), str(data.C))) < 0.005
        assert data.one(f"SELECT COUNT(*) FROM GLEntry g WHERE g.SourceDocumentType = 'SalesInvoice' AND {n14.is_close(data)}") == 0, "no close touches a sales invoice posting"
        for i in fails:
            shown[i] = 0.0
    rows = []
    for i, ((name, expected), a) in enumerate(zip(tests, shown)):
        diff = a - float(expected)
        ok = abs(diff) <= 0.01
        assert ok == (not (fail and i in fails))
        rows.append([name, _plain(float(expected)), _plain(a), _plain(round(diff, 2)), "Pass" if ok else "Fail"])
    d = Diagram("The Control Totals Tab" + (" with the Closes Kept" if fail else ""))
    last_test = max(i for i, l in enumerate(lines, 1) if l.lstrip().startswith('ROW ( "Test"'))
    close = next(i for i in range(last_test, len(lines) + 1) if lines[i - 1].strip() == ")")      # the line that closes UNION
    assert lines[last_test - 1].count("Ledger less invoice lines") == 1
    resume = close if fail else last_test           # the picture leaves out the tests (all of them, or all but the reconciling item)
    hidden = (5, resume - 1)
    left_out = n14.word(len(tests) if fail else len(tests) - 1)
    numbers = [1, 2, 3, 4] + list(range(resume, len(lines) + 1))
    editor_rows = []
    win_h = 96 + 10 + 56 + (len(numbers) + 1) * 20 + 8 + 14 + 24 + pbi.ROW + 2 + len(rows) * pbi.ROW + 26 + 12
    win = pbi.window(d, win_h, view="DAX query", tab="Home", tabs=pbi.QUERY_TABS,
                     buttons=["Format", "Comment", "Uncomment", "Find", "Replace", "Command palette"], file=FILE)
    x, w = win.canvas_x + 8, win.canvas_w - 16
    width = w - 34 - 28
    for n in numbers:
        if n == resume:
            editor_rows.append((None, f"… lines {hidden[0]} to {hidden[1]} not shown: the {'' if fail else 'first '}{left_out} tests, each a ROW"))
        editor_rows.append((n, _fit_dax(lines[n - 1], width)))
    ed = _editor(d, x, win.top + 10, w, editor_rows, "Control Totals", 0)
    res = pbi.dax_results(d, x, ed["bottom"] + 14, ["[Test]", "[Expected]", "[Actual]", "[Difference]", "[Result]"], [316, 116, 116, 112, 68], rows)
    geo = res["geometry"]
    gap_row = 6
    if not fail:
        ex, ey, ew, eh = geo[(gap_row, 0)]
        xl.emphasis(d, ex, ey, sum(geo[(gap_row, c)][2] for c in range(5)), eh)
        top_y, bottom_y = ed["ys"][last_test], ed["ys"][close - 1] + ed["line_h"]
        xl.emphasis(d, ed["left"] + 4, top_y, ed["width"] - 12, bottom_y - top_y)
    else:
        for i in sorted(fails):
            ex, ey, ew, eh = geo[(i, 0)]
            xl.emphasis(d, ex, ey, sum(geo[(i, c)][2] for c in range(5)), eh)
    status_bottom = res["bottom"]
    note_y = win.bottom + 10
    if fail:
        before, after = g["m_gl"].split("\n"), ["GL Amount =", "SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] )"]
        d.text("<b>In Report view, the formula bar of GL Amount: the tutorial's (left) and with the closes kept (right)</b>", 0, note_y, 860, 22, size=SMALL)
        half = 420
        _dax_box(d, before, 0, note_y + 26, half)
        _dax_box(d, after, half + 20, note_y + 26, 860 - half - 20)
        note_y += 26 + 16 * len(before) + 12 + 12
        _note(d, f"The same tab after GL Amount keeps the closing entries, run again; the query is not touched, and the drawing leaves out its tests (lines "
                 f"{hidden[0]} to {hidden[1]}, a gray bar). Outlined: the two tests that read GL Amount over "
                 f"every account, the net income of {y} and the manufacturing variance, each with an Actual of 0 and a Difference of minus its expected value. "
                 f"The invoice lines and the revenue do not use GL Amount; the debit total uses SUM; the two ledger tests read sales invoice postings, which no "
                 f"closing entry touches. The right-hand formula is one way to write the change.", note_y)
    else:
        _note(d, f"The tab Control Totals after Requirement 2, run: seven tests, each Pass with a Difference of 0. The editor is drawn without lines "
                 f"{hidden[0]} to {hidden[1]}, the first {left_out} tests (a gray bar), and values are written to the cent. Outlined, in the editor and in the grid: the "
                 f"reconciling item, the ledger's invoice revenue less the invoice lines, {_money(e['gap'])}. It is the invoices {e['numbers']}, dated in late "
                 f"{data.P} and posted on {y}-01-01, so the query tests it as its own expected value and does not leave it as a failure.", note_y)
    return d


def if_14_6_a() -> Diagram:
    return _control_totals(False)


def if_14_6_b() -> Diagram:
    return _control_totals(True)


FIGURES = {"IF-14-0-A": if_14_0_a, "IF-14-0-B": if_14_0_b, "IF-14-0-C": if_14_0_c, "IF-14-0-D": if_14_0_d,
           "IF-14-1-A": if_14_1_a, "IF-14-1-B": if_14_1_b, "IF-14-2-A": if_14_2_a, "IF-14-2-B": if_14_2_b,
           "IF-14-3-A": if_14_3_a, "IF-14-3-B": if_14_3_b, "IF-14-4-A": if_14_4_a, "IF-14-4-B": if_14_4_b,
           "IF-14-5-A": if_14_5_a, "IF-14-5-B": if_14_5_b, "IF-14-6-A": if_14_6_a, "IF-14-6-B": if_14_6_b}
