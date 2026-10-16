"""Instructor figures of Chapter 15 (guides in facts/instructor/guides/chapter-15-management-reports/).

Chapter 15 is the third Power BI unit.  Its mocks draw the model and the pages of the model answer
(outputs/companion/solutions/Chapter15-exercises-pbi, a PBIP of TMDL, PBIR and DAX query text), so the names, the
columns, the relationships, the page titles and the Checks tab are read from that project, and every value comes from
the dataset through the guides' own contexts (ch15.chapter, ch15.g1 to ch15.g6) and the registered notes (ch15.t1 to
ch15.t3, ch15.ex1 to ch15.ex6).

What a mock may show: the project holds the model and the structure of each page, but not what a visual calculation or
the Analytics-pane forecast computes, so those cells are drawn only where the project or the dataset fixes them.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict

import ctx
import excel as xl
import kit
import powerbi as pbi
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HIGHLIGHT, INK, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

FILE = "Chapter 15 Exercises - Solutions"
BODY_SIZE = 13
PROJECT = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter15-exercises-pbi" / FILE
MODEL = PROJECT / f"{FILE}.SemanticModel"
REPORT = PROJECT / f"{FILE}.Report" / "definition"
CHAPTER = ctx.REPO / "chapters" / "15-management-reports"
DAX_DIR = MODEL / "DAXQueries"


# -- the model answer (a PBIP of text files) ----------------------------------------------------------------------------

def _tmdl(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def _g15():
    """guide_contexts.ch15: the helpers that read the project (measure_table, check_sections)."""
    from guide_contexts import ch15
    return ch15


def _model_columns(table: str) -> list[str]:
    return [a or b for a, b in re.findall(r"^\tcolumn (?:'([^']+)'|(\S+))", _tmdl(f"tables/{table}.tmdl"), re.M)]


def _table_measures(table: str) -> list[str]:
    return [a or b for a, b in re.findall(r"^\tmeasure (?:'([^']+)'|(\S+))", _tmdl(f"tables/{table}.tmdl"), re.M)]


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


def _query_order() -> list[str]:
    return json.loads(re.search(r"PBI_QueryOrder = (\[.*\])", _tmdl("model.tmdl")).group(1))


def _page_ids() -> list[str]:
    return json.loads((REPORT / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]


def _page(page: str) -> dict:
    return json.loads((REPORT / "pages" / page / "page.json").read_text(encoding="utf-8"))


def _page_name(page: str) -> str:
    return _page(page)["displayName"]


def _hidden(page: str) -> bool:
    return _page(page).get("visibility") == "HiddenInViewMode"


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
        out[n] = re.search(rf"^## Guided Tutorial 15\.{n}: (.+)$", text, re.M).group(1).strip()
    return out


def _exercise_titles() -> dict[str, str]:
    text = (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8")
    return dict(re.findall(r"^\*\*Exercise (15\.\d): (.+?)\*\*$", text, re.M))


# -- drawing helpers ----------------------------------------------------------------------------------------------------

def _money(x: float) -> str:
    return pbi.amount(x)


def _signed(x: float) -> str:
    """A measure with the format #,0.00: no minus sign on a zero."""
    return pbi.amount(0.0 if abs(x) < 0.005 else x)


def _pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


def _mdy(iso: str) -> str:
    """An ISO date as a Short Date reads in the model (en-US): 6/5/2026."""
    return f"{int(iso[5:7])}/{int(iso[8:10])}/{iso[:4]}"


def _nb(html: str) -> str:
    """Keep "Tutorial 15.2" and "Ex 15.5" together on a line."""
    return re.sub(r"\b(Tutorial|Exercise|Ex|Chapter|Step|Steps) (\d)", r"\1&nbsp;\2", html)


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


def _tabs(active: str, d: Diagram, y: float) -> None:
    """The page tabs under the canvas: the pages around the active one, as the report orders them."""
    order = _page_ids()
    i = order.index(active)
    shown = order[max(i - 1, 0):i + 2]
    pbi.page_tabs(d, 4, y, [_page_name(p) for p in shown], _page_name(active))


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
                  aligns: list[str] | None = None, title_lines: int | None = None, head_lines: int = 1) -> dict:
    """A table visual: a title (one line or two), a header row and the rows, banded.  aligns names each column's side
    ("left" for text, "right" for numbers and dates); by default numbers go right.  Total rows are not drawn.  A header may
    break over head_lines lines, with <br> where it breaks.  Returns the cell geometry keyed (row, column) with row -1 for the
    headers, and the visual's bottom and right edges."""
    w = sum(widths) + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
    hh = pbi.ROW if head_lines == 1 else 15 * head_lines + 8
    h = th + 12 + hh + len(rows) * pbi.ROW
    ix, iy, _, _ = _frame(d, x, y, w, h, title, lines=title_lines)
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    aligns = aligns or ["right" if any(_is_num(r[c]) for r in rows) else "left" for c in range(len(headers))]
    geometry = {}
    for c, (head, cx, wd) in enumerate(zip(headers, xs, widths)):
        shown = "<br>".join(esc(p) for p in head.split("<br>")) if "<br>" in head else esc(_clip(head, wd, bold=True))
        d.box(f"<b>{shown}</b>", cx, iy, wd, hh, fill=WHITE, stroke=WHITE, size=SMALL, align=aligns[c], rounded=False)
        geometry[(-1, c)] = (cx, iy, wd, hh)
    d.box("", ix, iy + hh - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, row in enumerate(rows):
        ry = iy + hh + pbi.ROW * r
        for c, (value, cx, wd) in enumerate(zip(row, xs, widths)):
            d.box(esc(_clip(value, wd)), cx, ry, wd, pbi.ROW, fill=WHITE if r % 2 == 0 else GRAY_TINT,
                  stroke=WHITE if r % 2 == 0 else GRAY_TINT, size=SMALL, align=aligns[c], rounded=False)
            geometry[(r, c)] = (cx, ry, wd, pbi.ROW)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, width=sum(widths))


def _check_columns(table: str, columns: list[str]) -> None:
    """A mock may show only the columns (or, for Key Measures, the measures) the project has."""
    if table == "Key Measures":
        missing = set(columns) - set(_g15().measure_table())
    else:
        missing = set(columns) - set(_model_columns(table))
    assert not missing, f"{table} lacks {sorted(missing)} in the model answer"


# -- IF-15-0-A: the build sequence of the chapter -----------------------------------------------------------------------------

def if_15_0_a() -> Diagram:
    """The Chapter 14 report, the three tutorials in a row, and the six exercises branching from the copy saved after Tutorial 15.3."""
    d = Diagram("The Build Sequence of Chapter 15")
    titles, ex = _tutorial_titles(), _exercise_titles()
    assert sorted(ex) == [f"15.{i}" for i in range(1, 7)]
    c = ctx.values("ch15.chapter")
    steps = {int(k): v for k, v in c["steps"].items()}
    q = _query_order()
    rels = _relationships()
    tests = (DAX_DIR / "Tests.dax").read_text(encoding="utf-8")
    folders = _folder_measures()
    tabs = _query_tabs()
    assert tabs == ["Tests", "Ex 15.1", "Checks"], tabs
    # what each tutorial adds, as the model answer holds it
    assert q[q.index("PromotionProgram") + 1] == "Steps" and q[q.index("Steps") + 1] == "BudgetLine"
    assert q[-3:] == ["OperationPaths", "ClockPaths", "LaborPaths"]
    assert not any("Steps" in (m[0], o[0]) for m, o, _ in rels), "Steps is related to nothing"
    related = lambda table: {o[0] for m, o, _ in rels if m[0] == table}   # noqa: E731
    assert related("SalesInvoiceLine") >= {"PromotionProgram"} and related("BudgetLine") == {"Account", "CostCenter", "Date"}
    assert related("LaborTimeEntry") == {"Employee", "WorkCenter", "Date"} and related("ProductionCompletionLine") == {"Item", "Date"}
    assert "// Test 4" in tests and "// Test 5" in tests
    base = ["salesDiscounts", "validation", "review", "margins", "incomeStatement"]
    p1, p2, p3 = ["promotions", "promotionDetail", "promotionTooltip"], ["budget", "costCenterDetail"], ["plant", "about"]
    assert all(_hidden(p) for p in ("promotionDetail", "promotionTooltip", "costCenterDetail", "ledgerDetail"))
    assert not any(_hidden(p) for p in base + ["promotions", "budget", "plant", "about"])
    names = lambda ps: [_page_name(p) for p in ps]   # noqa: E731
    assert c["n_pages"] == len(base) + len(p1) + len(p2) + len(p3) + 1 + 5 + 1, "the pages of the model answer"
    n154 = len(folders["Ex 15.4"]) + len(_table_measures("Discount"))
    n156 = len(folders["Ex 15.6"])
    assert len(folders["Ex 15.2"]) == 1 and len(folders["Ex 15.3"]) == 1 and "Net Income YTD" in folders["Ex 15.2"]
    assert "MonthStart" in _model_columns("Date") and "Plant Measure" in _loaded_tables() and "Discount" in _loaded_tables()

    widths = [172, 200, 200, 200]
    gap = (860 - sum(widths)) / 3
    xs = [sum(widths[:i]) + gap * i for i in range(4)]
    base_names = names(base)
    texts = [
        f"<b>Chapter 14 report</b><br>Charles River Reports.pbix<br>Pages: {', '.join(base_names[:-1])} and {base_names[-1]}; "
        f"Key Measures and the {tabs[0]} tab",
        f"<b>Tutorial 15.1<br>{esc(titles[1])}</b><br>PromotionProgram relates to the invoice lines; Steps, a table that relates to "
        f"nothing, feeds the waterfall; pages {', '.join(names(p1)[:-1])} and {names(p1)[-1]}<br><i>{steps[1]} steps</i>",
        f"<b>Tutorial 15.2<br>{esc(titles[2])}</b><br>BudgetLine, a second fact table, shares Account, CostCenter and Date with the "
        f"ledger; the flexed budget; pages {' and '.join(names(p2))}; Test 4<br><i>{steps[2]} steps</i>",
        f"<b>Tutorial 15.3<br>{esc(titles[3])}</b><br>Two more fact tables, LaborTimeEntry and ProductionCompletionLine; the plant "
        f"ratios; pages {' and '.join(names(p3))} with a page navigator; the three detail pages hidden; Test 5<br><i>{steps[3]} steps</i>",
    ]
    h = max(kit.height_for(t, widths[i] - 8, SMALL, pad=16) for i, t in enumerate(texts))
    ids = []
    for i, t in enumerate(texts):
        fill, stroke = (GRAY_TINT, GRAY) if i == 0 else (BLUE_TINT, BLUE)
        ids.append(d.box(_nb(t), xs[i], 0, widths[i], h, fill=fill, stroke=stroke, size=SMALL, align="left", valign="top", stroke_width=1.5))
    for a, b in zip(ids, ids[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
    by = h + 44
    bar_text = ("<b>Ch15 Exercises.pbix</b>, the report saved with File > Save as after Tutorial 15.3. Each exercise works in this copy, "
                "on a page or a DAX query view tab of its own.")
    bh = kit.height_for(bar_text, 860, SMALL, pad=14)
    bar = d.box(bar_text, 0, by, 860, bh, fill=GRAY_TINT, stroke=GRAY, size=SMALL, align="left", stroke_width=1.5)
    d.arrow(ids[3], bar, exit=(0.5, 1), entry=((xs[3] + widths[3] / 2) / 860, 0), meta="edgeStyle=none;")
    adds = {
        "15.1": f"The hidden page {_page_name('ledgerDetail')}, a drill-through page on AccountSubType; the DAX query view tab {tabs[1]}",
        "15.2": f"The page {_page_name('ex152')}: two tables with two visual calculations; the measure {folders['Ex 15.2'][0]}",
        "15.3": f"The page {_page_name('ex153')}: a field parameter, the table Plant Measure; the measure {folders['Ex 15.3'][0]}",
        "15.4": f"The page {_page_name('ex154')}: a what-if parameter, the table Discount; {n154} measures",
        "15.5": f"The page {_page_name('ex155')}: two line charts with a forecast and a table of the actual quarter; the column MonthStart in Date",
        "15.6": f"The page {_page_name('ex156')}: three queries, {', '.join(q[-3:-1])} and {q[-1]}; {n156} measures",
    }
    ew = (860 - 5 * 10) / 6
    etexts = [f"<b>Ex {n}<br>{esc(ex[n])}</b><br><br>{esc(adds[n])}" for n in ex]
    eh = max(kit.height_for(t, ew - 10, SMALL, pad=18) for t in etexts)
    ey = by + bh + 40
    for i, t in enumerate(etexts):
        ex_id = d.box(_nb(t), i * (ew + 10), ey, ew, eh, fill=TEAL_TINT, stroke=TEAL, size=SMALL, align="left", valign="top", stroke_width=1.5)
        d.arrow(bar, ex_id, exit=((i * (ew + 10) + ew / 2) / 860, 1), entry=(0.5, 0), meta="edgeStyle=none;")
    bottom = ey + eh + 14
    lx = 0
    for label, fill, stroke in [("Given", GRAY_TINT, GRAY), ("Built in the tutorials", BLUE_TINT, BLUE), ("Added by an exercise", TEAL_TINT, TEAL)]:
        d.box("", lx, bottom + 3, 16, 14, fill=fill, stroke=stroke, stroke_width=1.5, rounded=False)
        lw = text_width(label, SMALL, False) + 8
        d.text(label, lx + 22, bottom, lw, 20, size=SMALL, valign="middle")
        lx += 22 + lw + 24
    _note(d, f"The model answer holds {c['n_pages']} pages: the nine visible pages of the tutorials, the four hidden detail pages (Tutorial 15.1 adds "
             f"two, Tutorial 15.2 one and Exercise 15.1 one), a page for each of Ex 15.2 to Ex 15.6 and Notes. Its DAX query view tabs are {tabs[0]}, "
             f"{tabs[1]} and {tabs[2]}. Tutorial 15.3 hides the three detail pages of the tutorials.", bottom + 26)
    return d


# -- IF-15-0-B: Model view of the model answer ----------------------------------------------------------------------------------

def _rel(d: Diagram, one: tuple[float, float], many: tuple[float, float], points: list[tuple[float, float]] | None = None,
         jump: bool = False, one_tag: bool = True) -> None:
    """A one-to-many relationship as pbi.relationship draws it (1 at the key, an asterisk at the table that refers to it, an
    arrow at the middle of the longest run), with each tag on the side of the line that its own bend does not use."""
    meta = "edgeStyle=none;" + ("jumpStyle=arc;jumpSize=10;" if jump else "")
    path = [one, *(points or []), many]
    lengths = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:])]
    k = lengths.index(max(lengths))
    (ax, ay), (bx, by) = path[k], path[k + 1]
    mid = ((ax + bx) / 2, (ay + by) / 2)
    first = [d.anchor(px, py) for px, py in path[:k + 1]] + [d.anchor(*mid)]
    second = [d.anchor(*mid)] + [d.anchor(px, py) for px, py in path[k + 1:]]
    for a, b in zip(first, first[1:]):
        d.edge(a, b, color=GRAY, end="blockThin" if b == first[-1] else "none", meta=meta)
    for a, b in zip(second, second[1:]):
        d.edge(a, b, color=GRAY, meta=meta)

    def tag(end: tuple[float, float], rest: list[tuple[float, float]], text: str) -> None:
        # rest runs away from the end: its first point is the neighbor, then the bends
        nxt = rest[0]
        turn = next((p for p in rest if p[1] != end[1]), None)
        if nxt[1] != end[1]:                       # the line leaves the end vertically
            x, y = end[0] + 3, (end[1] + 3 if nxt[1] > end[1] else end[1] - 21)
        else:
            x = end[0] + 2 if nxt[0] > end[0] else end[0] - 16
            y = end[1] + 2 if (turn is not None and turn[1] < end[1]) else end[1] - 21
        d.text(f"<b>{text}</b>", x, y, 14, 19, size=SMALL, align="center", valign="middle")

    if one_tag:
        tag(one, path[1:], "1")
    tag(many, list(reversed(path[:-1])), "*")


def if_15_0_b() -> Diagram:
    """Model view with the eighteen tables of the model answer: five fact tables and LaborPaths around Date, their dimensions,
    and four tables that stand alone."""
    d = Diagram("Model View of the Model Answer")
    shown = {
        "Customer": ["CustomerID", "CustomerName", "CustomerSegment"],
        "PromotionProgram": ["PromotionID", "PromotionName", "DiscountPct"],
        "Item": ["ItemID", "ItemCode", "ItemGroup"],
        "SalesInvoiceLine": ["CustomerID", "PromotionID", "ItemID", "InvoiceDate", "LineTotal"],
        "ProductionCompletionLine": ["ItemID", "CompletionDate", "QuantityCompleted"],
        "Date": ["Date", "Year", "YearMonth"],
        "LaborPaths": ["WorkDate", "LaborType", "RegularHours"],
        "GLEntry": ["PostingDate", "AccountID", "CostCenterID", "Debit", "Credit"],
        "BudgetLine": ["BudgetDate", "AccountID", "CostCenterID", "BudgetAmount"],
        "LaborTimeEntry": ["WorkDate", "EmployeeID", "WorkCenterID", "ExtendedLaborCost"],
        "Account": ["AccountID", "AccountNumber", "AccountSubType"],
        "CostCenter": ["CostCenterID", "CostCenterName"],
        "Employee": ["EmployeeID", "JobTitle"],
        "WorkCenter": ["WorkCenterID", "WorkCenterName"],
        "Steps": ["Step", "Order"],
        "Discount": ["Discount"],
        "Plant Measure": ["Plant Measure"],
        "Key Measures": ["Revenue", "Budget", "Net Income"],
    }
    assert _loaded_tables() == set(shown), "the eighteen tables of the model answer"
    for table, columns in shown.items():
        _check_columns(table, columns)
    wanted = {(("SalesInvoiceLine", "ItemID"), ("Item", "ItemID")), (("SalesInvoiceLine", "InvoiceDate"), ("Date", "Date")),
              (("SalesInvoiceLine", "CustomerID"), ("Customer", "CustomerID")), (("SalesInvoiceLine", "PromotionID"), ("PromotionProgram", "PromotionID")),
              (("GLEntry", "AccountID"), ("Account", "AccountID")), (("GLEntry", "CostCenterID"), ("CostCenter", "CostCenterID")),
              (("GLEntry", "PostingDate"), ("Date", "Date")), (("BudgetLine", "AccountID"), ("Account", "AccountID")),
              (("BudgetLine", "CostCenterID"), ("CostCenter", "CostCenterID")), (("BudgetLine", "BudgetDate"), ("Date", "Date")),
              (("LaborTimeEntry", "EmployeeID"), ("Employee", "EmployeeID")), (("LaborTimeEntry", "WorkCenterID"), ("WorkCenter", "WorkCenterID")),
              (("LaborTimeEntry", "WorkDate"), ("Date", "Date")), (("ProductionCompletionLine", "ItemID"), ("Item", "ItemID")),
              (("ProductionCompletionLine", "CompletionDate"), ("Date", "Date")), (("LaborPaths", "WorkDate"), ("Date", "Date"))}
    rels = _relationships()
    assert {(m, o) for m, o, _ in rels} == wanted and all(active for _, _, active in rels), "the project's sixteen active relationships"
    related = {t for m, o, _ in rels for t in (m[0], o[0])}
    alone = sorted(set(shown) - related)
    assert alone == ["Discount", "Key Measures", "Plant Measure", "Steps"], alone
    n_tables, n_rel = len(shown), len(rels)

    def width(name: str) -> float:
        return max(text_width(esc(name), SMALL, True), *[text_width(esc(c), SMALL, False) for c in shown[name]]) + 16

    # the columns of the picture, left to right, and the gaps that carry the lines
    w_dl = max(width(t) for t in ("Customer", "PromotionProgram", "Item"))
    w_fl = max(width(t) for t in ("SalesInvoiceLine", "ProductionCompletionLine"))
    w_dt = max(width(t) for t in ("Date", "LaborPaths"))
    w_fr = max(width(t) for t in ("GLEntry", "BudgetLine", "LaborTimeEntry"))
    w_dr = max(width(t) for t in ("Account", "CostCenter", "Employee", "WorkCenter"))
    g = 36
    x_dl = 76
    x_fl = x_dl + w_dl + g
    x_dt = x_fl + w_fl + g + 4
    x_fr = x_dt + w_dt + g + 4
    x_dr = x_fr + w_fr + g
    assert x_dr + w_dr <= 852, f"Model view is {x_dr + w_dr:.0f} px wide"
    win = pbi.window(d, 600, view="Model", tab="Home", buttons=["Manage relationships", "New measure", "New column"], file=FILE)
    top = win.top
    pbi.canvas(d, win.canvas_x, top, 860 - win.canvas_x, win.bottom - top)

    def card(name: str, x: float, y: float, w: float) -> pbi.ModelTable:
        return pbi.model_table(d, name, x, top + y, shown[name], w=w)

    # sales and production on the left: each foreign key row of the facts is met by a straight line or one bend
    cust = card("Customer", x_dl, 10, w_dl)
    promo = card("PromotionProgram", x_dl, 118, w_dl)
    item = card("Item", x_dl, 226, w_dl)
    sil = card("SalesInvoiceLine", x_fl, 10, w_fl)
    pcl = card("ProductionCompletionLine", x_fl, 226, w_fl)
    date = card("Date", x_dt, 10, w_dt)
    paths = card("LaborPaths", x_dt, 172, w_dt)
    gl = card("GLEntry", x_fr, 10, w_fr)
    bud = card("BudgetLine", x_fr, 172, w_fr)
    lab = card("LaborTimeEntry", x_fr, 306, w_fr)
    acct = card("Account", x_dr, 32, w_dr)
    cc = card("CostCenter", x_dr, 216, w_dr)
    emp = card("Employee", x_dr, 300, w_dr)
    wc = card("WorkCenter", x_dr, 384, w_dr)
    assert abs(cust.rows["CustomerID"] - sil.rows["CustomerID"]) < 0.5 and abs(item.rows["ItemID"] - pcl.rows["ItemID"]) < 0.5
    assert abs(acct.rows["AccountID"] - gl.rows["AccountID"]) < 0.5 and abs(cc.rows["CostCenterID"] - bud.rows["CostCenterID"]) < 0.5
    assert abs(date.rows["Date"] - gl.rows["PostingDate"]) < 0.5
    # the dimensions of the sales facts
    _rel(d, cust.right("CustomerID"), sil.left("CustomerID"))
    xb = x_dl + w_dl
    _rel(d, promo.right("PromotionID"), sil.left("PromotionID"), [(xb + 14, promo.rows["PromotionID"]), (xb + 14, sil.rows["PromotionID"])])
    _rel(d, item.right("ItemID"), sil.left("ItemID"), [(xb + 26, item.rows["ItemID"]), (xb + 26, sil.rows["ItemID"])], one_tag=False)
    _rel(d, item.right("ItemID"), pcl.left("ItemID"))
    # Date to every fact table
    xl_ = x_fl + w_fl
    _rel(d, date.left("Date"), sil.right("InvoiceDate"), [(xl_ + 14, date.rows["Date"]), (xl_ + 14, sil.rows["InvoiceDate"])])
    _rel(d, date.left("Date"), pcl.right("CompletionDate"), [(xl_ + 28, date.rows["Date"]), (xl_ + 28, pcl.rows["CompletionDate"])], one_tag=False)
    xr = x_dt + w_dt
    _rel(d, date.right("Date"), gl.left("PostingDate"))
    _rel(d, date.right("Date"), bud.left("BudgetDate"), [(xr + 26, date.rows["Date"]), (xr + 26, bud.rows["BudgetDate"])], one_tag=False)
    _rel(d, date.right("Date"), lab.left("WorkDate"), [(xr + 14, date.rows["Date"]), (xr + 14, lab.rows["WorkDate"])], one_tag=False)
    _rel(d, (date.x + date.w / 2, date.y + date.h), (paths.x + paths.w / 2, paths.y))
    # the ledger and the budget share Account and CostCenter; the plant has its own dimensions
    xf = x_fr + w_fr
    _rel(d, acct.left("AccountID"), gl.right("AccountID"))
    _rel(d, acct.left("AccountID"), bud.right("AccountID"), [(xf + 14, acct.rows["AccountID"]), (xf + 14, bud.rows["AccountID"])], one_tag=False)
    _rel(d, cc.left("CostCenterID"), bud.right("CostCenterID"))
    _rel(d, cc.left("CostCenterID"), gl.right("CostCenterID"), [(xf + 26, cc.rows["CostCenterID"]), (xf + 26, gl.rows["CostCenterID"])],
         jump=True, one_tag=False)
    _rel(d, emp.left("EmployeeID"), lab.right("EmployeeID"), [(xf + 20, emp.rows["EmployeeID"]), (xf + 20, lab.rows["EmployeeID"])])
    _rel(d, wc.left("WorkCenterID"), lab.right("WorkCenterID"), [(xf + 20, wc.rows["WorkCenterID"]), (xf + 20, lab.rows["WorkCenterID"])])
    # the tables that stand alone, in the free corner under the sales star
    ay = 346
    d.text("<i>No relationship: each of these four is used by measures and parameters, not by filters</i>", x_dl, top + ay, 380, 36, size=SMALL, color=GRAY)
    x = x_dl
    for name in ("Steps", "Discount", "Plant Measure", "Key Measures"):
        c = pbi.model_table(d, name, x, top + ay + 40, shown[name], w=width(name))
        x += c.w + 12
    assert x <= x_fl + w_fl + g + 12 + 30, "the standalone tables stay under the left half"
    y = win.bottom + 10
    d.text("<b>1</b> the table that holds the key &nbsp; <b>*</b> the table that refers to it &nbsp; Arrow: the way a filter flows", 0, y, 860, 22, size=SMALL)
    _note(d, f"The model answer ({n_tables} tables, {n_rel} relationships, all active and single direction). Each table lists some of its columns. "
             "The five fact tables and LaborPaths each relate to Date; Item, Account and CostCenter each filter two fact tables. "
             "Steps, Discount and Plant Measure hold a type-in table and two parameters, and Key Measures holds the measures; none has a line.", y + 26)
    return d


# -- IF-15-0-C: what the Checks tab tests and what only Desktop shows ----------------------------------------------------------------

def if_15_0_c() -> Diagram:
    """A two-column board: the results of each exercise that a row of the Checks tab tests, and what only Desktop shows."""
    d = Diagram("What the Checks Tab Proves and What Only Desktop Shows")
    c = ctx.values("ch15.chapter")
    sections = _g15().check_sections()
    rows = {n: sections[f"Exercise 15.{n}"] for n in range(1, 7)}
    mine = sum(v for k, v in sections.items() if k.startswith(("Tutorial 15", "Exercise 15")))
    assert mine == c["n_checks_mine"] and sum(sections.values()) == c["n_checks"], "the Checks tab's rows"
    checks = (DAX_DIR / "Checks.dax").read_text(encoding="utf-8")
    labels = lambda sec: re.findall(rf'"Section", "{re.escape(sec)}", "Check", "([^"]*)"', checks)   # noqa: E731
    # each claim of a card is a label of the Checks tab
    has = lambda sec, *words: all(any(w in label for label in labels(sec)) for w in words)   # noqa: E731
    assert has("Exercise 15.1", "postings", "posting date", "without a year filter")
    assert has("Exercise 15.2", "Net Income 2026-01", "running sum", "YTD at June", "lowest net income")
    assert has("Exercise 15.3", "Hours per Standard Hour", "Overtime Share", "Labor Cost per Standard Hour", "straight-time rate", "fields, in order")
    assert has("Exercise 15.4", "Break-even Lift at 5%", "Break-even Lift at 15%", "Design Trade Units", "smallest Discount", "largest Discount")
    assert has("Exercise 15.5", "actual revenue 2026-Q4", "same quarter last year", "mean benchmark")
    assert has("Exercise 15.6", "disagreeing lines", "direct lines on both paths", "share after the operation's end", "operation at Packing", "indirect hours")
    left = [
        f"<b>Exercise 15.1</b> The two loss entries of the subtype with their dates and amounts, every posting of each entry, and the entries "
        f"a page lists with no year filter",
        f"<b>Exercise 15.2</b> The net income of each month, the running sum of the measure Net Income YTD, the figure at June and at July with "
        f"the table filtered, and the two lowest months",
        f"<b>Exercise 15.3</b> The three plant measures for each year, the manufacturing labor cost and the straight-time rate, and the order of "
        f"the parameter's fields",
        f"<b>Exercise 15.4</b> The break-even lift at the default and at each of the five discounts, the units, price and cost per unit, and "
        f"the smallest and largest value of the Discount table",
        f"<b>Exercise 15.5</b> The actual revenue of the last quarter and of each of its months, and the error of two benchmarks, the mean "
        f"and the same quarter last year",
        f"<b>Exercise 15.6</b> The lines on both paths and the lines that disagree, by year, the hours in each cell of the work-center matrix, "
        f"the shares recorded after the operation ended and the lines that cannot be tested",
    ]
    right = [
        "<b>The drill-through click</b> The Drillthrough option of the right-click menu, the filters a click passes and the back button, which "
        "responds only with Ctrl held<br><i>Tutorial 15.1, Steps 7 and 9; Tutorial 15.2, Step 8; Exercise 15.1</i>",
        "<b>The visual calculations</b> The YTD and Change columns of Exercise 15.2, the RUNNINGSUM of Tutorial 15.2, Step 10 and the moving "
        "average of Tutorial 15.3, Steps 8 and 9. They are computed inside the visual, so no row of the Checks tab can read them: compare "
        "them by eye<br><i>Tutorial 15.2; Tutorial 15.3; Exercise 15.2</i>",
        "<b>The field-parameter slicer</b> Whether the slicer changes the measure the chart shows, and what Desktop does when the parameter "
        "is tried as a drill-through field<br><i>Exercise 15.3, Requirements 3 and 5</i>",
        "<b>The Analytics-pane forecast</b> Desktop computes it, and a new release can move it: grade the audit note, not the value"
        "<br><i>Exercise 15.5</i>",
    ]
    col_w, gap = 422, 16
    d.box("<b>Tested by the Checks tab</b>", 0, 0, col_w, 32, fill=TEAL, stroke=TEAL, color=WHITE, size=14, rounded=False)
    d.box("<b>Visible only in Desktop</b>", col_w + gap, 0, col_w, 32, fill=AMBER, stroke=AMBER, color=WHITE, size=14, rounded=False)
    bottoms = []
    for x0, items, fill, stroke, badge in ((0, left, TEAL_TINT, TEAL, True), (col_w + gap, right, AMBER_TINT, AMBER, False)):
        cy = 40
        for i, text in enumerate(items):
            tw = col_w - (86 if badge else 0)
            h = max(kit.height_for(_nb(text), tw, BODY_SIZE, pad=22), 66 if badge else 0)
            d.box(_nb(text), x0, cy, tw, h, fill=fill, stroke=stroke, size=BODY_SIZE, align="left", rounded=False, stroke_width=1.5)
            if badge:
                d.box(f"<b>{rows[i + 1]}</b><br>rows", x0 + tw + 4, cy, col_w - tw - 4, h, fill=WHITE, stroke=stroke, size=BODY_SIZE, rounded=False, stroke_width=1.5)
            cy += h + 8
        bottoms.append(cy - 8)
    board = {"bottom": max(bottoms)}
    _note(d, f"The Checks tab of the model answer holds {mine} rows for the tutorials and exercises of the chapter ({c['n_checks']} with the sections "
             "of Chapters 13 and 14). Choose Home > Refresh, then Run. A row tests a value, not how a visual looks, so the right-hand column "
             "is for the instructor to open the pages.", board["bottom"] + 12)
    return d


# -- IF-15-0-D: the budget variance, by cause ---------------------------------------------------------------------------------------

def if_15_0_d() -> Diagram:
    """A waterfall from the static budget to the actual: the volume effect, the classification effect as an up and a down
    arrow that net to zero, and the remaining variance."""
    t2 = ctx.values("ch15.t2")
    y = ctx.values("ch15.chapter")["y"]
    budget, volume, remaining, actual = t2["opex"], t2["volume"], t2["remaining"], t2["actual"]
    cls, to, frm = t2["dep"]["cls"], t2["dep"]["to"], t2["dep"]["frm"]
    moved = {c["name"]: c["cls"] for c in t2["centers"] if abs(c["cls"]) > 0.005}
    assert set(moved) == {to, frm} and abs(moved[to] - cls) < 0.005 and abs(moved[frm] + cls) < 0.005, moved
    assert abs(sum(c["cls"] for c in t2["centers"])) < 0.005, "the classification effect totals zero"
    assert abs(budget + volume + remaining - actual) < 0.005, "budget, volume and remaining explain the actual"
    assert volume < 0 and remaining < 0 and cls > 0 and abs(volume) > 5 * abs(remaining)
    l0 = budget
    l1 = budget + volume
    l2 = l1 + remaining
    d = Diagram("The Budget Variance by Cause")
    top = 26
    step = 500_000
    ymin = math.floor((min(l2, l1) - 150_000) / step) * step
    ymax = math.ceil((l0 + 200_000) / step) * step
    ticks = [ymin + i * step for i in range(int((ymax - ymin) // step) + 1)]
    d.text(f"<b>Operating expense, fiscal {y}: from the static budget to the actual</b>", 0, 0, 860, 22, size=SMALL)
    plot_h = 330
    plot = kit.Plot(d, 0, top, 860, plot_h, y_ticks=ticks, categories=[""] * 5, y_fmt=lambda v: f"{v / 1e6:.1f}M", bottom=8)
    slot = plot.pw / 5
    bar_w = slot * 0.6

    def bar(cx: float, w: float, low: float, high: float, color: str) -> tuple[float, float, float, float]:
        x0 = cx - w / 2
        top_y, base_y = plot.y_of(high), plot.y_of(low)
        h = max(base_y - top_y, 3)
        d.box("", x0, top_y, w, h, fill=color, stroke=color, rounded=False)
        return x0, top_y, w, h

    def label(cx: float, text: str, level: float, below: bool = False, w: float = 112, name: str = "") -> None:
        if not name:
            d.box(f"<b>{text}</b>", cx - w / 2, plot.y_of(level) + (3 if below else -23), w, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
        elif below:
            d.box(f"<b>{text}</b><br>{esc(name)}", cx - w / 2, plot.y_of(level) + 3, w, 36, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
        else:
            d.box(f"<b>{text}</b><br>{esc(name)}", cx - w / 2, plot.y_of(level) - 39, w, 36, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)

    cx = [plot.x_of(i) for i in range(5)]
    half = bar_w * 0.46
    # connectors at the running levels, then the bars
    for x0, x1, level in ((cx[0] + bar_w / 2, cx[1] - bar_w / 2, l0), (cx[1] + bar_w / 2, cx[2] - bar_w / 2 - 4, l1),
                          (cx[2] + bar_w / 2 + 4, cx[3] - bar_w / 2, l1), (cx[3] + bar_w / 2, cx[4] - bar_w / 2, l2)):
        d.box("", x0, plot.y_of(level) - 0.75, x1 - x0, 1.5, fill=GRAY, stroke=GRAY, rounded=False)
    start = bar(cx[0], bar_w, ymin, l0, BLUE)
    label(cx[0], _money(l0), l0)
    bar(cx[1], bar_w, l1, l0, CORAL)
    label(cx[1], f"−{_money(-volume)}", l0)
    up_cx, down_cx = cx[2] - half / 2 - 2, cx[2] + half / 2 + 2
    bar(up_cx, half, l1, l1 + cls, TEAL)
    label(up_cx, f"+{_money(cls)}", l1 + cls, w=100, name=to)
    bar(down_cx, half, l1, l1 + cls, CORAL)
    label(down_cx, f"−{_money(cls)}", l1, below=True, w=100, name=frm)
    bar(cx[3], bar_w, l2, l1, CORAL)
    label(cx[3], f"−{_money(-remaining)}", l1)
    end = bar(cx[4], bar_w, ymin, l2, BLUE)
    label(cx[4], _money(l2), l2)
    for x0, y0, w0, h0 in (start, end):                 # the axis does not start at zero: a gap near the base of each blue bar
        d.box("", x0 - 1, plot.y_of(ymin) - 22, w0 + 2, 5, fill=WHITE, stroke=WHITE, rounded=False)
    # the whole variance: a dashed line at the budget across to the last bar, and an arrow down to it
    arrow_x = cx[4] - slot / 2 + 16
    d.edge(d.anchor(cx[1] + bar_w / 2, plot.y_of(l0)), d.anchor(cx[4] + slot / 2 - 4, plot.y_of(l0)), color=GRAY, width=1.5, dashed=True,
           meta="edgeStyle=none;")
    a, b = d.anchor(arrow_x, plot.y_of(l0) + 2), d.anchor(arrow_x, plot.y_of(l2) - 2)
    d.edge(a, b, start="blockThin", end="blockThin", color=INK, width=1.5, meta="edgeStyle=none;")
    d.box(f"<b>−{_money(budget - actual)}</b><br>the variance", arrow_x + 8, (plot.y_of(l0) + plot.y_of(l2)) / 2 - 18, 110, 40, fill=WHITE,
          stroke=WHITE, size=SMALL, align="left", rounded=False)
    fy = top + plot_h + 8
    texts = [
        ("Static budget", "The year's operating expense budget, with the commission budget calculated on the budget's sales volume", BLUE_TINT, BLUE),
        ("Volume effect", "The commission budget restated at the volume actually billed: Chapter 7's flexible budget on one cost", CORAL_TINT, CORAL),
        ("Classification effect", f"Depreciation budgeted in {frm}, booked partly in {to}: one up, one down by the same amount, net {_money(0)}", GRAY_TINT, GRAY),
        ("Remaining variance", "The payroll burden rate, budgeted above the actual, and the months with three pay dates", CORAL_TINT, CORAL),
        ("Actual", "Operating expense recorded in the ledger, the closes left out", BLUE_TINT, BLUE),
    ]
    html = [f"<b>{esc(n)}</b><br>{esc(t)}" for n, t, _, _ in texts]
    bh = max(kit.height_for(h, slot - 28, SMALL, pad=14) for h in html)
    for i, (h, (_, _, fill, stroke)) in enumerate(zip(html, texts)):
        d.box(h, cx[i] - slot / 2 + 5, fy, slot - 10, bh, fill=fill, stroke=stroke, size=SMALL, align="left", valign="top", stroke_width=1.5)
    ly = fy + bh + 12
    kit.legend(d, 0, ly, [("Budget and actual", BLUE, "box"), ("Increase, with a plus sign", TEAL, "box"), ("Decrease, with a minus sign", CORAL, "box")])
    _note(d, f"A sketch of Tutorial 15.2, Step 9, all cost centers together. The vertical axis starts at {ymin / 1e6:.1f}M, not at zero, so that the small "
             f"steps show; the two blue bars are cut near the base. The classification effect moves {_money(cls)} up in {to} and down in {frm}, so "
             f"it explains none of the total; what remains, {_money(-remaining)} below the budget, is a few percent nearly everywhere.", ly + 28)
    return d


# -- IF-15-1-A: the Ledger Detail page ----------------------------------------------------------------------------------------------

SUBTYPE = "Other Income or Expense"


def _entry_lines(data, voucher: str) -> list[tuple[int, str, float, float]]:
    """(AccountNumber, AccountName, Debit, Credit) of every posting of one entry."""
    rows = data.q("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                  "WHERE g.VoucherNumber = ? ORDER BY g.GLEntryID", voucher)
    return [(int(n), name, db, cr) for n, name, db, cr in rows]


def if_15_1_a() -> Diagram:
    """The Ledger Detail page as the model answer is saved: the drill-through filter at the subtype and no year, so both loss entries."""
    g = ctx.values("ch15.g1")
    e = ctx.values("ch15.ex1")
    data = ctx.data()
    page = _page("ledgerDetail")
    assert page["type"] == "Drillthrough" and _hidden("ledgerDetail")
    assert f"'{SUBTYPE}'" in json.dumps(page["filterConfig"]), "the page keeps its drill-through filter at the subtype"
    title = _title("ledgerDetail", "ledgerTable")
    assert title == g["t_ledger"] == "Postings to the drilled-through subtype"
    cols = [p["nativeQueryRef"] for p in _visual("ledgerDetail", "ledgerTable")["visual"]["query"]["queryState"]["Values"]["projections"]]
    assert cols == ["PostingDate", "VoucherNumber", "SourceDocumentType", "AccountNumber", "AccountName", "P&L Amount"], cols
    assert _visual("ledgerDetail", "backButton")["visual"]["visualContainerObjects"]["visualLink"][0]["properties"]["type"]["expr"]["Literal"]["Value"] == "'Back'"
    closes = list(data.closes)
    marks = ",".join("?" * len(closes))
    found = data.q("SELECT g.PostingDate, g.VoucherNumber, g.SourceDocumentType, a.AccountNumber, a.AccountName, g.Credit - g.Debit "
                   "FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                   f"WHERE a.AccountSubType = ? AND g.VoucherNumber NOT IN ({marks}) ORDER BY g.PostingDate, g.GLEntryID", SUBTYPE, *closes)
    assert [r[1] for r in found] == [e["before"]["number"], e["now"]["number"]], "one loss entry in each year and no close"
    assert all(abs(r[5] + loss) < 0.005 and r[5] < 0 for r, loss in zip(found, (e["before"]["loss"], e["now"]["loss"])))
    assert all(r[3] == g["acct_number"] and r[4] == g["acct_name"] for r in found)
    rows = [[_mdy(r[0]), r[1], r[2], str(r[3]), r[4], _signed(r[5])] for r in found]
    headers = cols
    widths = [88, 120, 150, 112, 214, 100]
    aligns = ["right", "left", "left", "right", "left", "right"]
    pad = 16
    table_h = 20 + 12 + (len(rows) + 1) * pbi.ROW
    canvas_h = pad + 28 + 12 + table_h + pad
    d = Diagram("The Ledger Detail Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    pbi.back_button(d, pad, pad - 2)
    label = f"<b>Drill-through filter:</b> AccountSubType is {SUBTYPE}"
    lw = text_width(label, SMALL, False) + 30
    d.box(label, pad + 84, pad - 1, lw, 26, fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", rounded=False, stroke_width=1.5)
    t = _table_visual(d, pad, pad + 40, title, headers, widths, rows, aligns=aligns, title_lines=1)
    for r in range(len(rows)):
        cx, cy, cw, ch = t["geometry"][(r, 5)]
        d.outline(cx + 1, cy + 1, cw - 2, ch - 2, CORAL, width=2.5, front=True)
    assert t["bottom"] + pad <= canvas_h + 1
    _tabs("ledgerDetail", d, canvas_h + 4)
    _note(d, f"Report view, the hidden page {_page_name('ledgerDetail')}, as the model answer is saved: its drill-through filter holds the subtype and no year, so "
             f"the table lists the loss entry of {data.P} and the one of {g['y']}. The amber label is drawn to name that filter; it is not a visual of the "
             "page. Outlined: the P&L Amount of each entry, negative because a loss is a debit. The closes do not appear, because P&L Amount "
             "leaves them out. Total rows are not drawn, and neither is the page's text box with the written answers.", canvas_h + 34)
    return d


# -- IF-15-1-B: the two disposal entries ----------------------------------------------------------------------------------------------

def if_15_1_b() -> Diagram:
    """Two entries side by side, each with the loss worked out from its own lines: the current year's has no cash line."""
    g = ctx.values("ch15.g1")
    e = ctx.values("ch15.ex1")
    data = ctx.data()
    now, before = e["now"], e["before"]
    assert now["cash"] is None and now["proceeds"] == 0 and before["cash"] is not None
    d = Diagram("The Two Disposal Entries")
    pw, gap = 410, 40
    panels = []
    for x0, ent, fy in ((0, now, g["y"]), (pw + gap, before, data.P)):
        lines = _entry_lines(data, ent["number"])
        debits = sorted([r for r in lines if r[2] > 0], key=lambda r: (r[0] != g["acct_number"], -r[2]))
        credits = [r for r in lines if r[3] > 0]
        assert len(lines) == len(debits) + len(credits) and abs(sum(r[2] for r in debits) - sum(r[3] for r in credits)) < 0.005
        assert len(credits) == 1 and debits[0][0] == g["acct_number"]
        loss, acc, cost = debits[0][2], next(r[2] for r in debits if r[0] == ent["acc"]["account"]), credits[0][3]
        proceeds = next((r[2] for r in debits if r[0] == 1010), 0.0)
        assert abs(loss - ent["loss"]) < 0.005 and abs(acc - ent["acc"]["amount"]) < 0.005 and abs(cost - ent["cost"]["amount"]) < 0.005
        assert abs(proceeds - ent["proceeds"]) < 0.005 and abs(cost - acc - proceeds - loss) < 0.005, "loss = cost - accumulated depreciation - proceeds"
        panels.append((x0, ent, fy, debits, credits[0], loss, acc, cost, proceeds))
    head_h, sub_h, col_h = 28, 36, 24
    aw, mw = 246, 82
    bottoms = []
    for x0, ent, fy, debits, credit, loss, acc, cost, proceeds in panels:
        d.box(f"<b>{esc(ent['number'])}</b> · {ent['date']} · fiscal {fy}", x0, 0, pw, head_h, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False,
              align="left")
        d.box(f"<i>{esc(ent['entry'])}</i>", x0, head_h, pw, sub_h, fill=BLUE_TINT, stroke=RULE, size=SMALL, rounded=False, align="left")
        cy = head_h + sub_h
        for text, cx, w in (("Account", x0, aw), ("Debit", x0 + aw, mw), ("Credit", x0 + aw + mw, mw)):
            d.box(f"<b>{text}</b>", cx, cy, w, col_h, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False,
                  align="left" if text == "Account" else "right")
        cy += col_h

        def row(number: int, name: str, db: float, cr: float, fill: str, stroke: str) -> None:
            nonlocal cy
            text = ("" if db else "&nbsp;&nbsp;&nbsp;&nbsp;") + f"{number} {esc(name)}"
            h = max(26, kit.height_for(text, aw, SMALL, pad=10))
            d.box(text, x0, cy, aw, h, fill=fill, stroke=stroke, size=SMALL, rounded=False, align="left")
            d.box(_money(db) if db else "", x0 + aw, cy, mw, h, fill=fill, stroke=stroke, size=SMALL, rounded=False, align="right")
            d.box(_money(cr) if cr else "", x0 + aw + mw, cy, mw, h, fill=fill, stroke=stroke, size=SMALL, rounded=False, align="right")
            cy += h

        for number, name, db, _ in debits:
            if number == g["acct_number"]:
                row(number, name, db, 0, AMBER_TINT, AMBER)
            elif number == 1010:
                row(number, name, db, 0, TEAL_TINT, TEAL)
            else:
                row(number, name, db, 0, WHITE, RULE)
        if proceeds == 0:
            d.box("<i>No cash line: the asset was retired with no proceeds</i>", x0, cy, pw, 26, fill=WHITE, stroke=GRAY, color=GRAY, size=SMALL,
                  rounded=False, align="left", dashed=True)
            cy += 26
        row(credit[0], credit[1], 0, credit[3], WHITE, RULE)
        # the loss worked out from the entry's own lines
        cy += 16
        d.text("<b>Loss = cost − accumulated depreciation − proceeds</b>", x0, cy, pw, 20, size=SMALL)
        cy += 24
        cells = [(_money(cost), "cost", WHITE, RULE), (_money(acc), "accumulated depreciation", WHITE, RULE),
                 (_money(proceeds), "proceeds", TEAL_TINT if proceeds else WHITE, TEAL if proceeds else RULE), (_money(loss), "loss", AMBER_TINT, AMBER)]
        ops = ["−", "−", "="]
        cw = (pw - 3 * 16) / 4
        for i, (value, name, fill, stroke) in enumerate(cells):
            cx = x0 + i * (cw + 16)
            d.box(f"<b>{value}</b><br>{name}", cx, cy, cw, 52, fill=fill, stroke=stroke, size=SMALL, rounded=False, stroke_width=1.5)
            if i < 3:
                d.text(f"<b>{ops[i]}</b>", cx + cw, cy + 14, 16, 22, size=14, align="center")
        bottoms.append(cy + 52)
    bottom = max(bottoms)
    before_loss = before["cost"]["amount"] - before["acc"]["amount"]
    _note(d, f"Both entries debit the loss account and the accumulated depreciation of the asset and credit its cost. Only the entry of {data.P} also debits "
             f"cash: the proceeds, {_money(before['proceeds'])}, bring the loss down from {_money(before_loss)}, the cost less the accumulated depreciation, to "
             f"{_money(before['loss'])}. The entry of {g['y']} has no cash line, so its loss is the whole {_money(now['loss'])}.", bottom + 12)
    return d


# -- IF-15-2-A: the two tables of Exercise 15.2 ---------------------------------------------------------------------------------------

def if_15_2_a() -> Diagram:
    """The Ex 15.2 page: the twelve months with both year-to-date columns, and the second half where they part."""
    g = ctx.values("ch15.g2")
    e = ctx.values("ch15.ex2")
    y = g["y"]
    rows12 = g["table"]
    assert len(rows12) == 12
    visual = _visual("ex152", "netIncomeByMonth")["visual"]["query"]["queryState"]["Values"]["projections"]
    cols = [p["nativeQueryRef"] for p in visual]
    assert cols == ["YearMonth", "Net Income", "YTD", "Change", "Net Income YTD"], cols
    calcs = _g15().calcs(lambda ok, text: None, "ex152", "netIncomeByMonth")
    assert calcs == {"YTD": g["c_ytd"], "Change": g["c_change"]}
    # Change is guarded so that January, which has no row above it, is blank (round 2 of the review)
    assert g["c_ytd"] == "YTD = RUNNINGSUM ( [Net Income] )" and g["c_change"] == (
        "Change = IF ( ISBLANK ( PREVIOUS ( [Net Income] ) ), BLANK (), [Net Income] - PREVIOUS ( [Net Income] ) )")
    assert "TOTALYTD" in g["m_ytd"]
    t_top, t_half = _title("ex152", "netIncomeByMonth"), _title("ex152", "secondHalf")
    assert t_top == g["t_table"] and t_half == g["t_half"]
    # the second table's filter keeps July to December
    flt = json.dumps(_visual("ex152", "secondHalf")["filterConfig"])
    assert all(f"'{y}-{m:02d}'" in flt for m in range(7, 13)) and f"'{y}-06'" not in flt

    ni = [r["ni"] for r in rows12]
    ytd = [r["ytd"] for r in rows12]
    run = 0.0
    for i, v in enumerate(ni):
        run += v
        assert abs(run - ytd[i]) < 0.005, "the running sum of the visual calculation and TOTALYTD agree within the year"
    assert abs(ytd[-1] - e["ni"]) < 0.005 and abs(ytd[6] - e["july"]) < 0.005
    half_ni = ni[6:]
    half_run, run = [], 0.0
    for v in half_ni:
        run += v
        half_run.append(run)
    assert abs(half_run[-1] - e["h2"]) < 0.005, "the calculation's December in the filtered table"
    assert half_run[-1] != ytd[-1]
    months = [f"{y}-{i:02d}" for i in range(1, 13)]
    change = [""] + [_signed(ni[i] - ni[i - 1]) for i in range(1, 12)]
    top_rows = [[months[i], _money(ni[i]), _money(ytd[i]), change[i], _money(ytd[i])] for i in range(12)]
    half_change = [""] + [_signed(half_ni[i] - half_ni[i - 1]) for i in range(1, 6)]
    half_rows = [[months[6 + i], _money(half_ni[i]), _money(half_run[i]), half_change[i], _money(ytd[6 + i])] for i in range(6)]
    widths = [90, 112, 112, 112, 136]
    aligns = ["left", "right", "right", "right", "right"]
    pad = 16
    t1_h = 20 + 12 + 13 * pbi.ROW
    t2_h = 20 + 12 + 7 * pbi.ROW
    canvas_h = pad + t1_h + 14 + t2_h + pad
    d = Diagram("The Ex 15.2 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    t1 = _table_visual(d, pad, pad, t_top, cols, widths, top_rows, aligns=aligns, title_lines=1)
    t2 = _table_visual(d, pad, t1["bottom"] + 14, t_half, cols, widths, half_rows, aligns=aligns, title_lines=1)
    for c in (2, 4):
        ax, ay, aw, ah = t1["geometry"][(0, c)]
        d.outline(ax + 1, ay + 1, aw - 2, 12 * pbi.ROW - 2, TEAL, width=2.5, front=True)
    for c in (2, 4):
        cx, cy, cw, ch = t2["geometry"][(5, c)]
        xl.emphasis(d, cx + 1, cy + 1, cw - 2, ch - 2)
    right_x = t1["right"] + 16
    right_w = 860 - right_x - pad - 8
    dax = ("<b>YTD</b>, a visual calculation:<br>" + esc(g["c_ytd"].split(" = ", 1)[1]) + "<br><b>Net Income YTD</b>, a measure:<br>"
           + esc(g["m_ytd"].split(" = ", 1)[1]) + f"<br>Over the twelve months of one year they read alike in every row and reach {_money(e['ni'])} in December.")
    split = (f"<b>With January to June filtered out</b>, YTD starts again at July and reaches {_money(e['h2'])} in December, the sum of the six rows "
             f"it can see. Net Income YTD reads the model's dates, so it shows {_money(e['july'])} in July and {_money(e['ni'])} in December.")
    kit.callout(d, dax, right_x, pad, right_w, "teal")
    kit.callout(d, split, right_x, t1["bottom"] + 14, right_w, "amber")
    _tabs("ex152", d, canvas_h + 4)
    _note(d, f"Report view, page Ex 15.2, filtered to {y}. Outlined in teal: the two year-to-date columns, equal in every month. Outlined in coral: the December "
             "cells of the second table, where they differ. YTD and Change are visual calculations, computed inside the visual: the project cannot read "
             "them, so the cells show the running sum and the difference from the row above. January's Change, which has no row above it, is left "
             "empty: the project does not hold what Desktop shows there. Total rows are not drawn, and neither is the page's text box.", canvas_h + 34)
    return d


# -- IF-15-3-A: the Ex 15.3 page ------------------------------------------------------------------------------------------------------

def _slicer_list(d: Diagram, x: float, y: float, w: float, title: str, entries: list[str], selected: str) -> tuple[float, float]:
    """A slicer in the Vertical list style: a check box and a name for each entry, the selected one filled and bold.
    Returns the slicer's bottom and the geometry of the selected row."""
    h = 30 + 26 * len(entries) + 8
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 20, size=SMALL)
    row = None
    for i, name in enumerate(entries):
        ry = y + 30 + i * 26
        on = name == selected
        if on:
            d.box("<b>✓</b>", x + 10, ry + 4, 16, 16, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False, valign="middle")
            row = (x + 4, ry, w - 8, 24)
        else:
            d.box("", x + 10, ry + 4, 16, 16, fill=WHITE, stroke=GRAY, rounded=False)
        d.text(f"<b>{esc(name)}</b>" if on else esc(name), x + 32, ry + 2, w - 40, 20, size=SMALL, valign="middle")
    return y + h, row


def if_15_3_a() -> Diagram:
    """The Ex 15.3 page: a slicer chooses the measure one column chart shows, above the table of the three measures."""
    g = ctx.values("ch15.g3")
    e = ctx.values("ch15.ex3")
    data = ctx.data()
    years = e["years"]
    assert len(years) == len(data.years) == 3
    t_chart, t_slicer, t_table = _title("ex153", "plantMeasureChart"), _title("ex153", "plantMeasureSlicer"), _title("ex153", "plantMeasureTable")
    assert (t_chart, t_slicer, t_table) == (g["t_chart"], g["t_slicer"], g["t_table"])
    fields = re.findall(r'^\s+\("([^"]+)", NAMEOF', g["param"], re.M)
    assert fields == ["Hours per Standard Hour", "Overtime Share", "Labor Cost per Standard Hour"], fields
    slicer = json.dumps(_visual("ex153", "plantMeasureSlicer"))
    assert f"'{fields[-1]}'" in slicer, "the slicer is saved with the last entry selected"
    chart = _visual("ex153", "plantMeasureChart")["visual"]["query"]["queryState"]["Y"]
    assert [p["nativeQueryRef"] for p in chart["projections"]] == fields and chart["fieldParameters"][0]["length"] == 3
    table_cols = [p["nativeQueryRef"] for p in _visual("ex153", "plantMeasureTable")["visual"]["query"]["queryState"]["Values"]["projections"]]
    assert table_cols == ["Year", *fields], table_cols
    _check_columns("Key Measures", fields)
    chosen = [yr["per_std"] for yr in years]
    assert abs(chosen[-1] - g["wrong"][-1]["right"]) < 1e-6 and chosen == sorted(chosen)
    ticks = pbi.nice_ticks(0, max(chosen), 5)
    pad = 16
    sl_w, sl_h = 244, 30 + 26 * 3 + 8
    cx0 = pad + sl_w + 16
    chart_w, chart_h = 860 - cx0 - pad, 290
    rows = [[str(data.years[i]), f"{yr['ratio']:.2f}", _pct(yr["share"]), f"{yr['per_std']:.2f}"] for i, yr in enumerate(years)]
    widths = [58, 172, 120, 212]
    aligns = ["right"] * 4
    t_h = 20 + 12 + 4 * pbi.ROW
    canvas_h = pad + chart_h + 16 + t_h + pad
    d = Diagram("The Ex 15.3 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    sl_bottom, sel = _slicer_list(d, pad, pad, sl_w, t_slicer, fields, fields[-1])
    d.outline(sel[0], sel[1], sel[2], sel[3], BLUE, width=2.5, front=True)
    # the chart: the measure the slicer chose, for each year
    ix, iy, iw, ih = _frame(d, cx0, pad, chart_w, chart_h, t_chart, lines=1)
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 12, ih - 40
    y_of = pbi._value_axis(d, left, top, plot_h, ticks, "", ix, grid_w=plot_w)
    step = plot_w / len(chosen)
    for i, v in enumerate(chosen):
        bx = left + step * i + step * 0.2
        d.box("", bx, y_of(v), step * 0.6, y_of(ticks[0]) - y_of(v), fill=BLUE, stroke=BLUE, rounded=False)
        d.text(f"<b>{v:.2f}</b>", bx - 10, y_of(v) - 22, step * 0.6 + 20, 20, size=SMALL, align="center")
        d.text(str(data.years[i]), left + step * i, y_of(ticks[0]) + 6, step, 20, size=SMALL, color=GRAY, align="center")
    # what the page proves, under the slicer
    note_h = kit.callout(d, f"<b>One chart, three measures.</b> Each entry of the slicer is a field of the Plant Measure parameter. With {esc(fields[-1])} "
                            "chosen, the columns show that measure for each year; another entry swaps the measure and keeps the years.",
                         pad, sl_bottom + 14, sl_w, "teal")
    ty = pad + chart_h + 16
    t = _table_visual(d, pad, ty, t_table, table_cols, widths, rows, aligns=aligns, title_lines=1)
    ax, ay, aw, ah = t["geometry"][(0, 3)]
    d.outline(ax + 1, ay + 1, aw - 2, 3 * pbi.ROW - 2, BLUE, width=2.5, front=True)
    scale = g["scale"]
    kit.callout(d, f"<b>A slicer that allowed several entries</b> would put the cost, {g['wrong'][-1]['right']:.2f}, on the same axis as the share, "
                   f"{g['last_share']:.3f}: about {scale:.0f} to one, and the share's columns would vanish.", t["right"] + 16, ty, 860 - t["right"] - 16 - pad, "amber")
    _tabs("ex153", d, canvas_h + 4)
    _note(d, f"Report view, page Ex 15.3, with the slicer saved on {fields[-1]} and the years {data.years[0]} to {data.years[-1]}. Outlined in blue: the selected entry, "
             "and in the table the column the chart shows. The table holds the three measures for each year, as the Expected results list them. Total rows are not drawn, "
             "and neither is the page's text box.", canvas_h + 34)
    return d


# -- IF-15-3-B: hours times cost per hour ---------------------------------------------------------------------------------------------

def if_15_3_b() -> Diagram:
    """Three rows, one for each year: hours per standard hour times labor cost per labor hour equals labor cost per standard hour."""
    e = ctx.values("ch15.ex3")
    g = ctx.values("ch15.g3")
    data = ctx.data()
    years = e["years"]
    rates = e["rates"]
    assert len(years) == len(rates) == len(data.years) == 3
    for yr in years:
        assert abs(yr["ratio"] * yr["per_hour"] - yr["per_std"]) < 1e-6, "cost per standard hour = hours per standard hour x cost per labor hour"
    hours = [yr["ratio"] for yr in years]
    rate = [yr["per_hour"] for yr in years]
    per_std = [yr["per_std"] for yr in years]
    shares = [yr["share"] for yr in years]
    assert hours == sorted(hours) and rate == sorted(rate) and shares == sorted(shares), "all three rise from year to year"
    g_h, g_r, g_s = hours[-1] / hours[0] - 1, rate[-1] / rate[0] - 1, per_std[-1] / per_std[0] - 1
    assert g_h > 5 * g_r and abs((1 + g_h) * (1 + g_r) - (1 + g_s)) < 1e-9, "hours move far more than the cost of an hour"
    assert max(rates) / min(rates) - 1 < 0.01, "the straight-time rate barely moves"
    d = Diagram("Hours Times the Cost of an Hour")
    x_year, w_year = 0, 56
    x_b1, w_b1 = 66, 270
    x_op1 = x_b1 + w_b1 + 4
    x_b2 = x_op1 + 28
    x_op2 = x_b2 + w_b1 + 4
    x_res = x_op2 + 28
    w_res = 860 - x_res
    bar_max = 206
    head_h = 40
    for x, w, text in ((x_b1, w_b1, "Hours per standard hour"), (x_b2, w_b1, "Labor cost per labor hour"), (x_res, w_res, "Labor cost per standard hour")):
        d.box(f"<b>{text}</b>", x, 0, w, head_h, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL, rounded=False)
    row_h, gap = 50, 12
    for i, yr in enumerate(data.years):
        ry = head_h + 12 + i * (row_h + gap)
        d.box(f"<b>{yr}</b>", x_year, ry, w_year, row_h, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False)
        for x, vals, color, fmt in ((x_b1, hours, BLUE, lambda v: f"{v:.2f}"), (x_b2, rate, TEAL, lambda v: f"${v:.2f}")):
            length = bar_max * vals[i] / max(vals)
            d.box("", x, ry + 8, length, row_h - 16, fill=color, stroke=color, rounded=False)
            d.text(f"<b>{fmt(vals[i])}</b>", x + length + 6, ry + 14, 64, 22, size=SMALL, valign="middle")
        d.text("<b>×</b>", x_op1, ry + 12, 28, 26, size=14, align="center")
        d.text("<b>=</b>", x_op2, ry + 12, 28, 26, size=14, align="center")
        d.box(f"<b>${per_std[i]:.2f}</b>", x_res, ry, w_res, row_h, fill=AMBER_TINT, stroke=AMBER, size=14, rounded=False, stroke_width=1.5)
    ly = head_h + 12 + 3 * (row_h + gap) - gap + 14
    d.box("", 0, ly, 860, 1.5, fill=INK, stroke=INK, rounded=False)
    d.box(f"<b>{data.years[0]} to {data.years[-1]}</b>", x_year - 0, ly + 8, 66, 40, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False, align="left")
    for x, w, value in ((x_b1, w_b1, g_h), (x_b2, w_b1, g_r), (x_res, w_res, g_s)):
        d.box(f"<b>{'+' if value >= 0 else '−'}{_pct(abs(value))}</b>", x, ly + 8, w, 26, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False,
              align="left" if x != x_res else "center")
    d.text("<b>×</b>", x_op1, ly + 8, 28, 26, size=14, align="center")
    d.text("<b>=</b>", x_op2, ly + 8, 28, 26, size=14, align="center")
    bottom = ly + 40
    _note(d, f"Each bar starts at zero, in its own scale. The straight-time rate barely moved ({', '.join('$' + format(r, '.2f') for r in rates)} an hour), so "
             f"the rise in the cost of a labor hour is the overtime premium on a growing overtime share ({', '.join(_pct(s) for s in shares)}). The hours "
             f"per standard hour rose {_pct(g_h)}, the cost of an hour {_pct(g_r)}, and their product {_pct(g_s)}: "
             f"{1 + g_h:.3f} × {1 + g_r:.3f} = {1 + g_s:.3f}.", bottom + 4)
    return d


# -- IF-15-4-A: the Ex 15.4 page ------------------------------------------------------------------------------------------------------

def _signed_pct(x: float, places: int = 1) -> str:
    """A signed percent with a true minus sign: +11.9%, −20.7%."""
    return f"{'+' if x >= 0 else '−'}{abs(x) * 100:.{places}f}%"


def _slider(d: Diagram, x: float, y: float, w: float, h: float, title: str, low: int, high: int, value: int) -> None:
    """A slicer in the Single style over a whole-number what-if parameter: a track with one handle, the chosen value in a box
    above the handle and the two ends under the track.  The real slicer draws its own glyphs; this is the same reading."""
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 20, size=SMALL)
    t0, t1 = x + 22, x + w - 22
    ty = y + h - 30
    hx = t0 + (t1 - t0) * (value - low) / (high - low)
    d.box("", t0, ty - 2, t1 - t0, 4, fill=RULE, stroke=RULE, rounded=False)
    d.box("", t0, ty - 2, hx - t0, 4, fill=BLUE, stroke=BLUE, rounded=False)
    d.box(f"<b>{value}</b>", hx - 17, ty - 36, 34, 22, fill=WHITE, stroke=GRAY, size=SMALL, rounded=False)
    d.vertex("", f"ellipse;html=1;fillColor={BLUE};strokeColor={WHITE};strokeWidth=2;", hx - 8, ty - 8, 16, 16)
    d.text(str(low), t0 - 12, ty + 8, 24, 18, size=SMALL, color=GRAY, align="center")
    d.text(str(high), t1 - 12, ty + 8, 24, 18, size=SMALL, color=GRAY, align="center")


def _cards_visual(d: Diagram, x: float, y: float, w: float, h: float, items: list[tuple[str, str]]) -> None:
    """A card visual with one field per card: the value above its label, the label over two lines (<br> in the label)."""
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    gap = 6
    cw = (w - 12 - gap * (len(items) - 1)) / len(items)
    for i, (label, value) in enumerate(items):
        cx = x + 6 + i * (cw + gap)
        d.box("", cx, y + 6, cw, h - 12, fill=WHITE, stroke=RULE, rounded=True)
        d.text(f"<b>{esc(value)}</b>", cx + 2, y + 12, cw - 4, 24, size=15, align="center")
        d.text("<br>".join(esc(p) for p in label.split("<br>")), cx + 2, y + 40, cw - 4, 34, size=SMALL, color=GRAY, align="center")


def if_15_4_a() -> Diagram:
    """The Ex 15.4 page: the Discount slider at its default, the five cards, and the table of the lift at every whole discount."""
    g = ctx.values("ch15.g4")
    e = ctx.values("ch15.ex4")
    lift = _g15().lift
    page = _page("ex154")
    assert page["visualInteractions"] == [{"source": "discountSlider", "target": "liftByDiscount", "type": "NoFilter"}], "the slider is set to None for the table"
    slider = _visual("ex154", "discountSlider")["visual"]
    assert slider["visualType"] == "slicer" and "'Single'" in json.dumps(slider["objects"])
    t_slider, t_table = _title("ex154", "discountSlider"), _title("ex154", "liftByDiscount")
    assert (t_slider, t_table) == (g["t_slider"], g["t_table"]) == ("Discount", "Break-even lift at each discount")
    cards = [p["nativeQueryRef"] for p in _visual("ex154", "liftCards")["visual"]["query"]["queryState"]["Data"]["projections"]]
    assert cards == ["Design Trade Units", "Design Trade Price per Unit", "Design Trade Cost per Unit", "Discount Value", "Break-even Lift"], cards
    cols = [p["nativeQueryRef"] for p in _visual("ex154", "liftByDiscount")["visual"]["query"]["queryState"]["Values"]["projections"]]
    assert cols == ["Discount", "Break-even Lift"], cols
    _check_columns("Key Measures", ["Design Trade Units", "Design Trade Price per Unit", "Design Trade Cost per Unit", "Break-even Lift"])
    assert "Discount Value" in _table_measures("Discount") and "Discount" in _model_columns("Discount")
    low, high, step = (int(v) for v in re.search(r"GENERATESERIES \( (\d+), (\d+), (\d+) \)", g["series"]).groups())
    assert (low, high, step) == (0, 20, 1) and e["steps"] == high - low + 1
    default = round(g["disc"] * 100)
    assert abs(g["disc"] * 100 - default) < 1e-9 and f"SELECTEDVALUE ( 'Discount'[Discount], {default} )" in g["m_value"]
    price, cost = e["price"], e["cost"]
    discounts = list(range(low, high + 1, step))
    lifts = [lift(price, cost, s / 100) for s in discounts]
    wanted = {round(100 * x): lf for x, lf in e["lifts"]}
    assert all(abs(lifts[s - low] - lf) < 1e-9 for s, lf in wanted.items()) and sorted(wanted) == [5, 8, 10, 12, 15]
    assert abs(lifts[default - low] - (g["contrib_without"] / g["contrib_with"] - 1)) < 1e-9, "the card's lift is the ratio of the two contributions less one"
    values = [(f"{e['units']:,.2f}"), f"{price:,.2f}", f"{cost:,.2f}", str(default), _pct(lifts[default - low])]
    pad = 16
    left_w, gap = 240, 14
    top_h = 86
    t_y = pad + top_h + 12
    rows = [[str(s), _pct(lf)] for s, lf in zip(discounts, lifts)]
    canvas_h = t_y + 20 + 12 + (len(rows) + 1) * pbi.ROW + pad
    d = Diagram("The Ex 15.4 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    _slider(d, pad, pad, left_w, top_h, t_slider, low, high, default)
    cx0 = pad + left_w + gap
    _cards_visual(d, cx0, pad, 860 - pad - cx0, top_h, list(zip(["Design Trade<br>Units", "Design Trade<br>Price per Unit", "Design Trade<br>Cost per Unit",
                                                                  "Discount<br>Value", "Break-even<br>Lift"], values)))
    t = _table_visual(d, pad, t_y, t_table, cols, [96, 132], rows, aligns=["right", "right"], title_lines=1)
    for s in sorted(wanted):
        ox, oy, ow, oh = t["geometry"][(s - low, 0)]
        d.outline(ox + 1, oy + 1, t["width"] - 2, oh - 2, TEAL, width=2.5, front=True)
    assert t["bottom"] + pad <= canvas_h + 1
    cw = 860 - pad - cx0
    cy = t_y
    for text, color in (
        (f"<b>The cards follow the slider.</b> Discount Value is the slider's value, {default}, and Break-even Lift is the contribution a unit earns without the "
         f"discount over the contribution it earns with it, less one: ${g['contrib_without']:,.2f} ÷ ${g['contrib_with']:,.2f} − 1 = {_pct(lifts[default - low])}.", "teal"),
        ("<b>The table does not.</b> Each of its rows carries its own discount, so the page sets the slider's interaction with the table to None (Format > Edit "
         "interactions). Without that, the slider would cut the table to one row.", "amber"),
    ):
        cy = kit.callout(d, text, cx0, cy, cw, color) + 12
    # two of the outlined rows, annotated where they sit: the smallest discount against the evidence, the promotion as it ran against the case
    hi = e["high"]
    assert e["five"] == "about" and abs(lifts[min(wanted) - low] - hi) < 0.01
    smallest, ran = min(wanted), default
    for s, text in ((smallest, f"<b>{smallest} percent</b> needs {_pct(lifts[smallest - low])}, about the largest lift measured in any promotion's months "
                               f"({_signed_pct(hi)}): the evidence of Requirement 5."),
                    (ran, f"<b>{ran} percent</b> needs {_pct(lifts[ran - low])}: the card's value, and the lift of the Part II case.")):
        ox, oy, ow, oh = t["geometry"][(s - low, 0)]
        h = kit.height_for(text, cw - 8, SMALL, pad=14)
        by = oy + oh / 2 - h / 2
        d.box("", t["right"] - 6, oy + oh / 2 - 0.75, cx0 + 6 - t["right"] + 6, 1.5, fill=TEAL, stroke=TEAL, rounded=False)
        kit.callout(d, text, cx0 + 6, by, cw - 6, "teal")
    ox, oy, ow, oh = t["geometry"][(high - low - 3, 0)]
    kit.callout(d, f"<b>One promotion, one year.</b> The three unit cards are scoped by name to the {esc(g['name'])} and to {g['y']}, {g['n_lines']:,} invoice lines.",
                cx0, oy, cw, "gray")
    _tabs("ex154", d, canvas_h + 4)
    _note(d, f"Report view, page Ex 15.4, with the slider at its default of {default}. The slider is drawn as a track with one handle; Desktop draws its own. "
             f"The table lists every whole discount from {low} to {high}, each carrying Break-even Lift. Outlined: the five discounts of Requirement 4. Total rows "
             "are not drawn, and neither is the page's text box.", canvas_h + 34)
    return d


# -- IF-15-4-B: the lift each discount needs against the lifts measured ---------------------------------------------------------------

def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str = BLUE, width: float = 3) -> None:
    """One edge through the points, drawn straight between them (separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def if_15_4_b() -> Diagram:
    """The break-even lift at every whole discount, with the five of Requirement 4 marked, and the band of the lifts the Part II case measured."""
    g = ctx.values("ch15.g4")
    e = ctx.values("ch15.ex4")
    lift = _g15().lift
    price, cost = e["price"], e["cost"]
    discounts = list(range(0, e["steps"]))
    lifts = [lift(price, cost, s / 100) for s in discounts]
    five = {round(100 * x): lf for x, lf in e["lifts"]}
    assert all(abs(lifts[s] - lf) < 1e-9 for s, lf in five.items())
    lo, hi = e["low"], e["high"]
    assert lo < 0 < hi and lifts[0] == 0 and lifts == sorted(lifts), "the lift is zero at no discount and rises with it"
    assert e["five"] == "about" and abs(lifts[5] - hi) < 0.01, "the lift at 5 percent sits at the band's top edge"
    assert all(lifts[s] > hi for s in (8, 10, 12, 15)), "every larger discount needs more than the largest measured lift"
    ran = round(g["disc"] * 100)
    times = lifts[ran] / hi
    from notes.case2 import volume
    measured = [v["lift"] for v in volume(ctx.data())]
    assert abs(min(measured) - lo) < 1e-9 and abs(max(measured) - hi) < 1e-9
    d = Diagram("The Lift Each Discount Needs")
    d.text("<b>The lift in volume at which the promotion breaks even, by discount, against the lifts the Part II case measured</b>", 0, 0, 860, 20, size=SMALL)
    step = 0.1
    y_lo = math.floor((lo - 0.05) / step) * step
    y_hi = math.ceil(max(lifts) / step) * step
    ticks = [round(y_lo + i * step, 2) for i in range(int(round((y_hi - y_lo) / step)) + 1)]
    pct0 = lambda v: f"{'−' if v < -0.005 else ''}{abs(v) * 100:.0f}%"   # noqa: E731
    xt = [0, 5, 8, 10, 12, 15, 20]
    plot = kit.Plot(d, 0, 26, 840, 440, None, y_ticks=ticks, x_ticks=xt, x_fmt=lambda v: f"{v:.0f}%", y_fmt=pct0,
                    x_title="Discount, in whole percents (the values of the slider)", y_title="Break-even lift", left=60, bottom=48)
    # the band of measured lifts: behind the line, with its two edges
    d.vertex("", f"rounded=0;html=1;fillColor={AMBER_TINT};strokeColor=none;fillOpacity=75;", plot.px, plot.y_of(hi), plot.pw, plot.y_of(lo) - plot.y_of(hi))
    for v in (hi, lo):
        d.box("", plot.px, plot.y_of(v) - 0.75, plot.pw, 1.5, fill=AMBER, stroke=AMBER, rounded=False)
    d.box("", plot.px, plot.y_of(0) - 0.75, plot.pw, 1.5, fill=GRAY, stroke=GRAY, rounded=False)
    _polyline(d, [(plot.x_of(s), plot.y_of(lf)) for s, lf in zip(discounts, lifts)], BLUE, 3)
    for s in sorted(five):
        mx, my = plot.x_of(s), plot.y_of(lifts[s])
        color = CORAL if s == ran else TEAL
        size = 18 if s == ran else 14
        d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={WHITE};strokeWidth=2;", mx - size / 2, my - size / 2, size, size)
        text = f"<b>{s}%: {_pct(lifts[s])}</b>"
        lw = text_width(text, SMALL, False) + 26
        d.box(text, mx - lw / 2, my - 34, lw, 22, fill=WHITE, stroke=color, size=SMALL, rounded=False, stroke_width=1.5)
    # the band's label, in the band where the line is far above it
    lines = ["<b>Measured lifts in the promotion months</b>", f"{_signed_pct(lo)} to {_signed_pct(hi)}, the Part II case: none unusual"]
    lw = max(text_width(t, SMALL, False) for t in lines) + 34
    d.box("<br>".join(lines), plot.x_of(10.5), plot.y_of(hi) + 8, lw, 42, fill=WHITE, stroke=AMBER, size=SMALL, rounded=False, align="left", stroke_width=1.5)
    kit.callout(d, f"<b>Reading the chart.</b> Above the line the promotion pays for itself. Even {min(five)} percent needs about the largest lift ever measured, "
                   f"{_pct(hi)}; the {ran} percent of the promotion as it ran needs {_pct(lifts[ran])}, {times:.1f} times that.",
                plot.px + 16, plot.y_of(0.78), 340, "teal")
    _note(d, f"Each point is the Break-even Lift of the model answer at a whole-number discount, from {e['units']:,.2f} units, ${price:,.2f} price before discount, "
             f"${cost:,.2f} standard cost a unit and a commission rate of 1.903%. Markers: the five discounts of Requirement 4; the larger one is the {ran} percent "
             f"the promotion ran at. The band is the lowest to the highest lift of the Part II case's {len(measured)} promotions; the lift is a condition, not a forecast.", 26 + 440 + 8)
    return d


# -- IF-15-5-A: the Ex 15.5 page, the hindcast chart --------------------------------------------------------------------------------------

def _ordinal(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def if_15_5_a() -> Diagram:
    """The Ex 15.5 chart that starts in January: monthly revenue through the month before the last quarter, a band where the forecast is drawn
    (with no values), and the table of the quarter's actual revenue."""
    import statistics
    g = ctx.values("ch15.g5")
    e = ctx.values("ch15.ex5")
    data = ctx.data()
    page = "ex155"
    visual = _visual(page, "forecastFromJanuary")
    assert visual["visual"]["visualType"] == "lineChart"
    prm = {c["Name"]: c["Literal"]["Value"] for c in visual["visual"]["objects"]["forecast"][0]["properties"]["transform"]["parameters"]}
    assert prm["ForecastLength"] == "3L" and prm["ConfidenceLevel"] == "0.95D" and prm["IgnoreLast"] == "0L"
    assert "'Scalar'" in json.dumps(visual["visual"]["objects"]["categoryAxis"]), "a continuous date axis"
    qs = visual["visual"]["query"]["queryState"]
    assert [p["nativeQueryRef"] for p in qs["Category"]["projections"]] == ["MonthStart"] and [p["nativeQueryRef"] for p in qs["Y"]["projections"]] == ["Revenue"]
    t_chart, t_table = _title(page, "forecastFromJanuary"), _title(page, "actualQ4")
    assert t_chart == g["t_jan"] and t_table == g["t_actual"]
    table_cols = [p["nativeQueryRef"] for p in _visual(page, "actualQ4")["visual"]["query"]["queryState"]["Values"]["projections"]]
    assert table_cols == ["YearQuarter", "Revenue"], table_cols
    revenue = dict(data.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                          "ON si.SalesInvoiceID = l.SalesInvoiceID GROUP BY 1"))
    months = [f"{y}-{m:02d}" for y in data.years for m in range(1, 13)]
    ys = [revenue[m] for m in months]
    n_fit = e["fit_months"]
    assert n_fit == g["n_all"] - 3 == len(months) - 3
    kept = re.findall(r"'(\d{4}-\d{2})'", json.dumps(visual["filterConfig"]))
    assert kept == months[:n_fit], "the chart keeps January of the first year to September of the last"
    assert [q["month"] for q in g["q4"]] == months[n_fit:] and abs(sum(ys[n_fit:]) - e["actual"]) < 0.005
    assert abs(ys[0] / statistics.mean(ys[1:12]) - e["start"]) < 1e-9 and ys[0] < min(ys[1:])
    quarter_label = f"{data.C}-Q{(int(months[n_fit][5:]) - 1) // 3 + 1}"
    assert f'"{quarter_label}"' in g["dax_actual"]
    month_name = lambda m: f"{n15_months()[int(m[5:]) - 1]} {m[:4]}"   # noqa: E731
    pad = 16
    chart_w, chart_h = 860 - 2 * pad, 300
    ticks = pbi.nice_ticks(0, max(ys), 5)
    assert max(ys) < ticks[-1]
    d = Diagram("The Ex 15.5 Page")
    t_y = pad + chart_h + 14
    tbl_w = 110 + 132 + 12
    cx0 = pad + tbl_w + 14
    cw = (860 - pad - cx0 - 10) / 2
    texts = (f"<b>A hindcast.</b> The chart stops in {month_name(months[n_fit - 1])}, so the quarter that follows is already known. "
             f"The forecast is fit on {n_fit} months, and its three points are compared with the actual {quarter_label}.",
             "<b>Not drawn: the forecast's values.</b> Desktop computes the forecast and its 95 percent interval inside the chart, so no measure and no file "
             "can return them. The band marks where they appear; Requirement 3 reads the points from the tooltips.")
    canvas_h = t_y + max(20 + 12 + 2 * pbi.ROW, *(kit.height_for(t, cw - 8, SMALL, pad=14) for t in texts)) + pad
    pbi.canvas(d, 0, 0, 860, canvas_h)
    ix, iy, iw, ih = _frame(d, pad, pad, chart_w, chart_h, t_chart, lines=1)
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 8, ih - 38
    y_of = pbi._value_axis(d, left, top, plot_h, ticks, "M", ix, grid_w=plot_w)
    n_axis = len(months)                                             # the axis runs to the end of the forecast: the last three months
    x_of = lambda i: left + plot_w * (i + 0.5) / n_axis                # noqa: E731
    # the band where Desktop draws the forecast and its interval: over the three months after the data, with no values
    bx = left + plot_w * n_fit / n_axis
    d.box("", bx, top, left + plot_w - bx, plot_h, fill=BLUE_TINT, stroke=GRAY, dashed=True, rounded=False, stroke_width=1.5)
    d.text("<b>Forecast</b><br>3 months", bx + 1, top + 6, left + plot_w - bx - 2, 36, size=SMALL, align="center")
    pts = [(x_of(i), y_of(v)) for i, v in enumerate(ys[:n_fit])]
    _polyline(d, pts, BLUE, 2.5)
    for px, py in pts:
        d.vertex("", f"ellipse;html=1;fillColor={BLUE};strokeColor={BLUE};", px - 3, py - 3, 6, 6)
    for i in range(0, n_axis, 6):
        d.text(_mdy(f"{months[i]}-01"), x_of(i) - 30, top + plot_h + 4, 60, 20, size=SMALL, color=GRAY, align="center")
    first_note = f"<b>{month_name(months[0])}</b>: the start-up month,<br>{e['start']:.0%} of the other months of its year"
    nw = max(text_width(p, SMALL, False) for p in first_note.split("<br>")) + 34
    d.box(first_note, x_of(0) + 12, y_of(ys[0]) - 24, nw, 36, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False, align="left")
    # the table of the quarter's actual revenue, and what the chart does and does not hold
    t = _table_visual(d, pad, t_y, t_table, table_cols, [110, 132], [[quarter_label, _money(e["actual"])]], aligns=["left", "right"], title_lines=1)
    assert abs(t["right"] - pad - tbl_w) < 0.5
    kit.callout(d, texts[0], cx0, t_y, cw, "teal")
    kit.callout(d, texts[1], cx0 + cw + 10, t_y, cw, "amber")
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page Ex 15.5: the chart that starts in {month_name(months[0])}, from the model answer's two forecast charts (its twin, from February, is not "
             f"drawn, nor is the page's text box). The date axis is continuous, on the column MonthStart; its labels are drawn in the column's Short Date format. "
             f"The line is the monthly revenue of the {n_fit} months the chart keeps; the shaded band marks the three months the forecast covers, with no values.", canvas_h + 34)
    return d


def n15_months() -> list[str]:
    return _g15().n15.MONTHS


# -- IF-15-5-B: three benchmarks measured two ways -----------------------------------------------------------------------------------------

def if_15_5_b() -> Diagram:
    """Grouped bars: the quarter error and the average monthly error of the three benchmarks, and an empty group for the forecast the student reads from Desktop."""
    e = ctx.values("ch15.ex5")
    g = ctx.values("ch15.g5")
    errs = e["errors"]
    order = ["trend", "mean", "last"]
    quarter = {k: errs[k]["quarter"] for k in order}
    monthly = {k: errs[k]["monthly"] for k in order}
    by_q = sorted(order, key=lambda k: abs(quarter[k]))
    by_m = sorted(order, key=lambda k: monthly[k])
    assert by_q != by_m, "the two measures of error rank the benchmarks differently"
    rank_q = {k: by_q.index(k) + 1 for k in order}
    rank_m = {k: by_m.index(k) + 1 for k in order}
    assert by_q[0] == by_m[0] == "mean", "the mean has the smallest error on both measures"
    assert all(v >= 0 for v in monthly.values())
    names = {"trend": "Trend<br>(Chapter 7's regression)", "mean": "Mean of the<br>fitted months", "last": "Same quarter<br>last year"}
    d = Diagram("Three Benchmarks Measured Two Ways")
    d.text(f"<b>Three benchmarks for the fourth quarter of {g['y']}, by the error of the quarter and by the average error of its months</b>", 0, 0, 860, 20, size=SMALL)
    step = 0.02
    y_hi = math.ceil(max(max(abs(v) for v in quarter.values()), max(monthly.values())) / step) * step
    ticks = [round(i * step, 2) for i in range(int(round(y_hi / step)) + 1)]
    plot = kit.Plot(d, 0, 26, 840, 380, None, y_ticks=ticks, categories=[""] * 4, y_fmt=lambda v: f"{v * 100:.0f}%", left=60, bottom=112,
                    y_title="Error against the actual quarter")
    slot = plot.pw / 4
    bar_w, gap = 58, 10
    base = plot.y_of(0)
    for i, k in enumerate(order):
        sx = plot.px + i * slot + (slot - 2 * bar_w - gap) / 2
        for j, (value, color, label, word) in enumerate(((quarter[k], BLUE, _signed_pct(quarter[k], 2), "quarter"), (monthly[k], TEAL, _pct(monthly[k], 2), "months"))):
            bx = sx + j * (bar_w + gap)
            h = max(base - plot.y_of(abs(value)), 2)
            d.box("", bx, base - h, bar_w, h, fill=color, stroke=color, rounded=False)
            d.box(f"<b>{label}</b>", bx - 14, base - h - 24, bar_w + 28, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
            d.text(word, bx - 8, base + 4, bar_w + 16, 18, size=SMALL, color=GRAY, align="center")
        gx = plot.px + i * slot
        d.text(f"<b>{names[k]}</b>", gx, base + 26, slot, 36, size=SMALL, align="center")
        d.text(f"By quarter: {_ordinal(rank_q[k])}<br>By month: {_ordinal(rank_m[k])}", gx, base + 64, slot, 36, size=SMALL, color=GRAY, align="center")
    gx = plot.px + 3 * slot
    d.box("<i>Left for the student: the forecast's quarter error and its average monthly error, read from Desktop</i>", gx + 14, plot.y_of(y_hi * 0.8),
          slot - 28, plot.y_of(0) - plot.y_of(y_hi * 0.8), fill=WHITE, stroke=GRAY, color=GRAY, size=SMALL, dashed=True, rounded=False, stroke_width=1.5)
    d.text("<b>Power BI forecast</b>", gx, base + 26, slot, 36, size=SMALL, align="center")
    ly = 26 + 380 + 8
    kit.legend(d, 0, ly, [("Error of the quarter total: the forecast total over the actual, less one (plus: too high)", BLUE, "box")])
    kit.legend(d, 0, ly + 22, [("Average error of the three months: the miss of each month over its actual, averaged", TEAL, "box")])
    _note(d, f"Chapter 7's benchmarks for {g['y']}'s fourth quarter, fitted from February {g['first']}. By the quarter the mean has the smallest error and the trend the largest; "
             f"by the month the same quarter last year has the largest, because its months' misses do not net against each other. The mean's quarter bar, "
             f"{_signed_pct(quarter['mean'], 2)}, is too short to see. Every bar starts at zero.", ly + 48)
    return d


# -- IF-15-6-A: the matrix of Exercise 15.6 -----------------------------------------------------------------------------------------------

def _matrix(d: Diagram, x: float, y: float, title: str, row_w: float, col_w: float, col_heads: list[str], row_heads: list[str],
            cells: list[list[str]], fills: dict | None = None, title_lines: int | None = None) -> dict:
    """A matrix visual with one level on each axis: a title, the column headings (<br> where one breaks over two lines), the row
    headings and the values, no total row or column.  fills maps (row, column) to a fill color.  Returns the cell geometry."""
    w = row_w + col_w * len(col_heads) + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
    hh = 38
    h = th + 12 + hh + len(row_heads) * pbi.ROW
    ix, iy, _, _ = _frame(d, x, y, w, h, title, lines=title_lines)
    geometry = {}
    for c, head in enumerate(col_heads):
        d.box("<b>" + "<br>".join(esc(p) for p in head.split("<br>")) + "</b>", ix + row_w + c * col_w, iy, col_w, hh, fill=WHITE, stroke=WHITE, size=SMALL,
              align="right", rounded=False)
    d.box("", ix, iy + hh - 1, row_w + col_w * len(col_heads), 1, fill=INK, stroke=INK, rounded=False)
    for r, head in enumerate(row_heads):
        ry = iy + hh + r * pbi.ROW
        d.box(esc(head), ix, ry, row_w, pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align="left", rounded=False)
        for c in range(len(col_heads)):
            cx = ix + row_w + c * col_w
            fill = (fills or {}).get((r, c), WHITE)
            d.box(f"<b>{esc(cells[r][c])}</b>" if fill != WHITE else esc(cells[r][c]), cx, ry, col_w, pbi.ROW, fill=fill, stroke=fill, size=SMALL, align="right", rounded=False)
            geometry[(r, c)] = (cx, ry, col_w, pbi.ROW)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix)


def if_15_6_a() -> Diagram:
    """The Ex 15.6 page: the matrix of the year's direct hours (operation's work center on the rows, the clock's on the columns) and the small
    table of the lines on which the paths agree, disagree or cannot be compared."""
    g = ctx.values("ch15.g6")
    e = ctx.values("ch15.ex6")
    data = ctx.data()
    page = "ex156"
    n15 = _g15().n15
    y = data.C
    t_matrix, t_share = _title(page, "pathMatrix"), _title(page, "lateShare")
    assert (t_matrix, t_share) == (g["t_matrix"], g["t_share"])
    mq = _visual(page, "pathMatrix")["visual"]["query"]["queryState"]
    assert [p["nativeQueryRef"] for p in mq["Rows"]["projections"]] == ["OperationWorkCenter"] and [p["nativeQueryRef"] for p in mq["Columns"]["projections"]] == ["ClockWorkCenter"]
    assert [p["nativeQueryRef"] for p in mq["Values"]["projections"]] == ["Path Hours"]
    tq = [p["nativeQueryRef"] for p in _visual(page, "lateShare")["visual"]["query"]["queryState"]["Values"]["projections"]]
    assert tq == ["SameWorkCenter", "Path Lines", "Share After Operation End"], tq
    _check_columns("LaborPaths", ["OperationWorkCenter", "ClockWorkCenter", "SameWorkCenter", "AfterOperationEnd"])
    # the matrix cells of the dataset, in the order a matrix sorts its headings (by name)
    rows = data.q("SELECT ow.WorkCenterName, cw.WorkCenterName, SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l "
                  "JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID JOIN WorkCenter ow ON ow.WorkCenterID = o.WorkCenterID "
                  "JOIN TimeClockEntry t ON t.TimeClockEntryID = l.TimeClockEntryID JOIN WorkCenter cw ON cw.WorkCenterID = t.WorkCenterID "
                  "WHERE l.LaborType = 'Direct Manufacturing' AND substr(l.WorkDate, 1, 4) = ? GROUP BY 1, 2", str(y))
    cell = {(a, b): v for a, b, v in rows}
    names = sorted({a for a, _ in cell})
    assert len(names) == 5 and sorted({b for _, b in cell}) == names, "five work centers on each side"
    assert len(cell) == 25 and all(v > 0 for v in cell.values()), "every cell of the matrix has hours"
    for m in e["m"]:                                         # the guide's own figures: the diagonal and the four cells off it
        name = next(n for n in names if n15.short(n).split()[0] == m["label"])
        assert abs(cell[(name, name)] - m["diag"]) < 1e-6
        for other, v in m["off"]:
            assert abs(cell[(name, next(n for n in names if n15.short(n) == other))] - v) < 1e-6
    packing = next(n for n in names if n == g["packing"])
    assembly = next(n for n in names if n == g["assembly"])
    off = {(a, b): v for (a, b), v in cell.items() if a != b}
    top_off = max((b for (a, b) in off if a == packing), key=lambda b: off[(packing, b)])
    assert top_off == assembly and abs(off[(packing, assembly)] - g["main"]) < 1e-6 and max(off.values()) == off[(packing, assembly)]
    short = lambda n: n15.center(n)                           # noqa: E731
    heads = [short(n).replace(" and ", "<br>and ").replace("Quality ", "Quality<br>") for n in names]
    cells = [[f"{cell[(a, b)]:,.1f}" for b in names] for a in names]
    fills = {(names.index(packing), names.index(assembly)): HIGHLIGHT}
    pad = 16
    row_w, col_w = 124, 76
    row_now = next(r for r in g["by_year"] if r["year"] == y)
    agree, differ, untested = e["now"] - e["differ"], e["differ"], e["untested"]
    late_agree = e["late_all"] - e["late_differ"]
    assert row_now["lines"] == e["now"] and row_now["differ"] == differ and e["direct"] - untested == e["now"]
    trows = [["False", f"{differ:,}", _pct(e["late_differ"] / differ)], ["True", f"{agree:,}", _pct(late_agree / agree)], ["(Blank)", f"{untested:,}", ""]]
    theads = ["SameWorkCenter", "Path<br>Lines", "Share After<br>Operation End"]
    tw = [116, 54, 102]

    def draw(d: Diagram) -> tuple[dict, float]:
        m = _matrix(d, pad, pad, t_matrix, row_w, col_w, heads, [short(n) for n in names], cells, fills)
        for i in range(5):
            cx, cy, cw, ch = m["geometry"][(i, i)]
            d.outline(cx + 2, cy + 2, cw - 4, ch - 4, TEAL, width=2.5, front=True)
        # the small table to its right: the paths agree, disagree, or cannot be compared
        tx = m["right"] + 14
        assert tx + sum(tw) + 12 <= 860 - pad + 1, f"the small table ends at {tx + sum(tw) + 12:.0f} px"
        t = _table_visual(d, tx, pad, t_share, theads, tw, trows, aligns=["left", "right", "right"], head_lines=2)
        bottom = kit.callout(d, f"<b>The disagreement is concentrated in the late time of Chapter 12.</b> Of the {differ:,} lines on which the paths disagree, "
                                f"{e['late_differ']:,} ({_pct(e['late_differ'] / differ)}) were recorded after the operation ended; of all {e['direct']:,} direct lines, "
                                f"{e['late_direct']:,} ({_pct(e['late_direct'] / e['direct'], 2)}).", pad, max(m["bottom"], t["bottom"]) + 12, 860 - 2 * pad, "amber")
        return m, bottom

    _, bottom = draw(Diagram("probe"))
    canvas_h = bottom + pad
    d = Diagram("The Ex 15.6 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    draw(d)
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page Ex 15.6, direct manufacturing time of {y}, the matrix's row and column headings sorted by name, without the words Work Center that every "
             f"name ends with. Outlined: the diagonal, where the operation's work center and the time clock's agree. Highlighted: Packing operations clocked at Assembly, "
             f"{cell[(packing, assembly)]:,.1f} hours, the largest cell off the diagonal; {_pct(g['pack_off_share'], 0)} of the hours of Packing operations are off it. "
             f"In the table, True and False read the test SameWorkCenter, and the blank row is the {untested} direct lines with no operation, which cannot be tested. "
             "Total rows and columns are not drawn, and neither are the other visuals and the text box of the page.", canvas_h + 34)
    return d


# -- IF-15-6-B: the two routes from a labor line to a work center ----------------------------------------------------------------------------

def if_15_6_b() -> Diagram:
    """The two routes the exercise compares: through the work order operation (what the time was charged to) and through the time clock entry (where the employee clocked in)."""
    g = ctx.values("ch15.g6")
    data = ctx.data()
    q = _query_order()
    assert {"OperationPaths", "ClockPaths", "LaborPaths"} <= set(q)
    assert {"OperationWorkCenter", "ClockWorkCenter", "SameWorkCenter"} <= set(_model_columns("LaborPaths"))
    assert 'NestedJoin(#"Changed Type1", {"WorkOrderOperationID"}, OperationPaths, {"WorkOrderOperationID"}' in g["m_merges"]
    assert 'NestedJoin(' in g["m_merges"] and '{"TimeClockEntryID"}, ClockPaths, {"TimeClockEntryID"}' in g["m_merges"]
    assert "WorkCenterID" in g["m_op"] and "WorkCenterID" in g["m_clock"] and "ActualEndDate" in g["m_op"]
    # what the note beside each route says, checked against the data
    by_type = {t: (clock_missing, clock_no_center, op_missing) for t, clock_missing, clock_no_center, op_missing in data.q(
        "SELECT l.LaborType, SUM(t.TimeClockEntryID IS NULL), SUM(t.WorkCenterID IS NULL), SUM(o.WorkOrderOperationID IS NULL) FROM LaborTimeEntry l "
        "LEFT JOIN TimeClockEntry t ON t.TimeClockEntryID = l.TimeClockEntryID LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID GROUP BY 1")}
    assert set(by_type) == {"Direct Manufacturing", "Indirect Manufacturing", "NonManufacturing"}
    n_rows = {t: n for t, n in data.q("SELECT LaborType, COUNT(*) FROM LaborTimeEntry GROUP BY 1")}
    assert by_type["Indirect Manufacturing"][2] == n_rows["Indirect Manufacturing"] and by_type["NonManufacturing"][2] == n_rows["NonManufacturing"], "no operation on indirect and non-manufacturing lines"
    assert 0 < by_type["Direct Manufacturing"][2] < n_rows["Direct Manufacturing"] // 100, "a few direct lines have no operation"
    assert all(v[0] == 0 for v in by_type.values()), "every line has a clock entry"
    assert by_type["Direct Manufacturing"][1] == 0 and by_type["Indirect Manufacturing"][1] == 0 and by_type["NonManufacturing"][1] == n_rows["NonManufacturing"], \
        "the clock entry places every direct and indirect line at a work center, and no non-manufacturing line"
    d = Diagram("The Two Routes to a Work Center")
    lte_w, mid_w, wc_w = 230, 216, 200
    x_lte, x_mid, x_wc = 0, lte_w + 84, 860 - wc_w
    label_w = 860 - (x_mid + 28)
    # the middle column, top to bottom: route 1's label, its table and its note, then route 2's label, table and note
    d.marker("1", x_mid - 2, 0, fill=BLUE)
    d.text("<b>The operation path</b> (query OperationPaths): what the time was charged to", x_mid + 28, 0, label_w, 24, size=SMALL, valign="middle")
    y_woo = 34
    woo = d.table("WorkOrderOperation", x_mid, y_woo, [("PK", "WorkOrderOperationID"), ("FK", "WorkCenterID"), ("", "ActualEndDate")], w=mid_w, focus=False)
    bottom1 = kit.callout(d, "<b>The route ends blank</b> for indirect and non-manufacturing lines, which have no operation, and for the few direct lines whose key is "
                             "empty or matches no operation.", x_mid, woo.bottom + 10, mid_w, "amber")
    y2 = bottom1 + 14
    d.marker("2", x_mid - 2, y2, fill=BLUE)
    d.text("<b>The clock path</b> (query ClockPaths): where the employee clocked in", x_mid + 28, y2, label_w, 24, size=SMALL, valign="middle")
    tce_y = y2 + 34
    tce = d.table("TimeClockEntry", x_mid, tce_y, [("PK", "TimeClockEntryID"), ("FK", "WorkCenterID")], w=mid_w, focus=False)
    bottom2 = kit.callout(d, "<b>The route ends blank</b> for non-manufacturing lines, whose clock entry names no work center; every direct and indirect line reaches one.",
                          x_mid, tce.bottom + 10, mid_w, "amber")
    # the labor line, between the two routes
    lte_y = (woo.bottom + tce_y) / 2 - 60
    d.text("<i>loaded as LaborPaths, every line kept</i>", x_lte, lte_y - 20, lte_w, 18, size=SMALL, color=GRAY)
    lte = d.table("LaborTimeEntry", x_lte, lte_y, [("PK", "LaborTimeEntryID"), ("FK", "WorkOrderOperationID"), ("FK", "TimeClockEntryID"), ("", "WorkDate"),
                                                  ("", "LaborType"), ("", "RegularHours"), ("", "OvertimeHours")], w=lte_w, focus=True)
    # the two lookups of the work center, one on each route, drawn where each route ends
    wc1_y = woo.cy("WorkCenterID") - 42
    wc2_y = tce.cy("WorkCenterID") - 42
    wc1 = d.table("WorkCenter", x_wc, wc1_y, [("PK", "WorkCenterID"), ("", "WorkCenterName")], w=wc_w, focus=False)
    wc2 = d.table("WorkCenter", x_wc, wc2_y, [("PK", "WorkCenterID"), ("", "WorkCenterName")], w=wc_w, focus=False)
    d.text("<i>brings OperationWorkCenter</i>", x_wc, wc1_y - 20, wc_w, 18, size=SMALL, color=GRAY)
    d.text("<i>brings ClockWorkCenter</i>", x_wc, wc2_y + wc2.h + 2, wc_w, 18, size=SMALL, color=GRAY)
    d.arrow(lte.id, woo.id, exit=(1, lte.fy("WorkOrderOperationID")), entry=(0, woo.fy("WorkOrderOperationID")))
    d.arrow(lte.id, tce.id, exit=(1, lte.fy("TimeClockEntryID")), entry=(0, tce.fy("TimeClockEntryID")))
    d.arrow(woo.id, wc1.id, exit=(1, woo.fy("WorkCenterID")), entry=(0, wc1.fy("WorkCenterID")))
    d.arrow(tce.id, wc2.id, exit=(1, tce.fy("WorkCenterID")), entry=(0, wc2.fy("WorkCenterID")))
    # the route numbers sit on the first hop of each route, where it leaves the labor line
    hop_x = (x_lte + lte_w + x_mid) / 2
    for n, (a, b) in (("1", (lte.cy("WorkOrderOperationID"), woo.cy("WorkOrderOperationID"))), ("2", (lte.cy("TimeClockEntryID"), tce.cy("TimeClockEntryID")))):
        d.marker(n, hop_x - 12, (a + b) / 2 - 12, fill=BLUE)
    # the comparison the exercise makes
    mid_x = x_wc + wc_w / 2
    ya, yb = wc1_y + wc1.h + 8, wc2_y - 4
    d.edge(d.anchor(mid_x, ya), d.anchor(mid_x, yb), start="blockThin", end="blockThin", color=INK, width=1.5, meta="edgeStyle=none;")
    d.box("<b>SameWorkCenter</b><br>do the two names agree?", mid_x - 84, (ya + yb) / 2 - 20, 168, 40, fill=WHITE, stroke=INK, size=SMALL, rounded=False, stroke_width=1.5)
    _note(d, "A labor line reaches a work center by two routes, each through its own key. The exercise merges both onto every labor line with left outer joins, "
             "names the work center each route gives, and tests whether the two names agree: SameWorkCenter is blank where either route ends blank.",
          max(bottom2, lte.bottom) + 10)
    return d


FIGURES = {"IF-15-0-A": if_15_0_a, "IF-15-0-B": if_15_0_b, "IF-15-0-C": if_15_0_c, "IF-15-0-D": if_15_0_d,
           "IF-15-1-A": if_15_1_a, "IF-15-1-B": if_15_1_b, "IF-15-2-A": if_15_2_a, "IF-15-3-A": if_15_3_a, "IF-15-3-B": if_15_3_b,
           "IF-15-4-A": if_15_4_a, "IF-15-4-B": if_15_4_b, "IF-15-5-A": if_15_5_a, "IF-15-5-B": if_15_5_b,
           "IF-15-6-A": if_15_6_a, "IF-15-6-B": if_15_6_b}
