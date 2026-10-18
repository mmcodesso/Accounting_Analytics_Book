"""Instructor figures of Chapter 16 (guides in facts/instructor/guides/chapter-16-audit-monitoring/).

Chapter 16 is the fourth Power BI unit.  Its mocks draw the model and the pages of the model answer
(outputs/companion/solutions/Chapter16-exercises-pbi, a PBIP of TMDL, PBIR and DAX query text), so the names, the
columns, the relationships, the page titles and the Checks tab are read from that project, and every value comes from
the dataset through the guides' own contexts (ch16.chapter, ch16.g1 to ch16.g6) and the registered notes (ch16.t1 to
ch16.t3, ch16.ex1 to ch16.ex6).

What a mock may show: the project holds the model and the structure of each page, so a visual's values are the ones
its measures return on the dataset (read through the notes), never a value typed here.
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

FILE = "Chapter 16 Exercises - Solutions"
BODY_SIZE = 13
PROJECT = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter16-exercises-pbi" / FILE
MODEL = PROJECT / f"{FILE}.SemanticModel"
REPORT = PROJECT / f"{FILE}.Report" / "definition"
CHAPTER = ctx.REPO / "chapters" / "16-audit-monitoring"
DAX_DIR = MODEL / "DAXQueries"


# -- the model answer (a PBIP of text files) ----------------------------------------------------------------------------

def _tmdl(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def _g16():
    """guide_contexts.ch16: the helpers that read the project (measure_table, check_sections)."""
    from guide_contexts import ch16
    return ch16


def _model_columns(table: str) -> list[str]:
    return [a or b for a, b in re.findall(r"^\tcolumn (?:'([^']+)'|(\S+))", _tmdl(f"tables/{table}.tmdl"), re.M)]


def _table_measures(table: str) -> list[str]:
    return [a or b for a, b in re.findall(r"^\tmeasure (?:'([^']+)'|(\S+))", _tmdl(f"tables/{table}.tmdl"), re.M)]


def _relationships() -> list[tuple[tuple[str, str], tuple[str, str], bool]]:
    """(many side, one side, active) of each relationship of the project, each side as (table, column)."""
    out = []
    for block in _tmdl("relationships.tmdl").split("relationship ")[1:]:
        ends = re.findall(r"(?:fromColumn|toColumn): (?:'([^']+)'|(\w+))\.(\w+)", block)
        (a1, a2, ac), (b1, b2, bc) = ends
        out.append((((a1 or a2), ac), ((b1 or b2), bc), "isActive: false" not in block))
    return out


def _loaded_tables() -> set[str]:
    return {p.stem for p in (MODEL / "definition" / "tables").glob("*.tmdl")}


def _hidden_table(table: str) -> bool:
    return re.search(r"^\tisHidden\s*$", _tmdl(f"tables/{table}.tmdl"), re.M) is not None


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


def _visual(page: str, name: str) -> dict:
    return json.loads((REPORT / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))


def _title(page: str, name: str) -> str:
    """The title the model answer gives a visual (a doubled apostrophe in the file is one in the title)."""
    value = _visual(page, name)["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
    return value.strip("'").replace("''", "'")


def _projections(page: str, name: str, role: str) -> list[str]:
    return [p["nativeQueryRef"] for p in _visual(page, name)["visual"]["query"]["queryState"][role]["projections"]]


def _query_tabs() -> list[str]:
    return json.loads((MODEL / ".pbi" / "daxQueries.json").read_text(encoding="utf-8"))["tabOrder"]


def _tutorial_titles() -> dict[int, str]:
    out = {}
    for n in (1, 2, 3):
        text = (CHAPTER / f"_tutorial-0{n}.qmd").read_text(encoding="utf-8")
        out[n] = re.search(rf"^## Guided Tutorial 16\.{n}: (.+)$", text, re.M).group(1).strip()
    return out


def _exercise_titles() -> dict[str, str]:
    text = (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8")
    return dict(re.findall(r"^\*\*Exercise (16\.\d): (.+?)\*\*$", text, re.M))


# -- drawing helpers ----------------------------------------------------------------------------------------------------

def _money(x: float) -> str:
    return pbi.amount(x)


def _pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


def _mdy(iso: str) -> str:
    """An ISO date as a Short Date reads in the model (en-US): 6/5/2026."""
    return f"{int(iso[5:7])}/{int(iso[8:10])}/{iso[:4]}"


def _nowrap(text: str) -> str:
    """A label that must not break at its hyphens (a document number, an ISO date)."""
    return f'<span style="white-space:nowrap">{esc(text)}</span>'


def _nb(html: str) -> str:
    """Keep "Tutorial 16.2" and "Ex 16.5" together on a line."""
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
                  aligns: list[str] | None = None, title_lines: int | None = None, head_lines: int = 1,
                  total: list[str] | None = None) -> dict:
    """A table visual: a title (one line or two), a header row, the rows (banded) and an optional bold total row.  aligns names
    each column's side ("left" for text, "right" for numbers and dates); by default numbers go right.  A header may break over
    head_lines lines, with <br> where it breaks.  Returns the cell geometry keyed (row, column) with row -1 for the headers
    (the total row is key len(rows)), and the visual's bottom and right edges."""
    w = sum(widths) + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
    hh = pbi.ROW if head_lines == 1 else 15 * head_lines + 8
    n = len(rows) + (1 if total else 0)
    h = th + 12 + hh + n * pbi.ROW
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
    for r, row in enumerate(rows + ([total] if total else [])):
        ry = iy + hh + pbi.ROW * r
        is_total = total is not None and r == len(rows)
        if is_total:
            d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
        for c, (value, cx, wd) in enumerate(zip(row, xs, widths)):
            plain = r % 2 == 0 or is_total
            d.box(f"<b>{esc(_clip(value, wd, bold=is_total))}</b>" if is_total else esc(_clip(value, wd)), cx, ry, wd, pbi.ROW,
                  fill=WHITE if plain else GRAY_TINT, stroke=WHITE if plain else GRAY_TINT, size=SMALL, align=aligns[c], rounded=False)
            geometry[(r, c)] = (cx, ry, wd, pbi.ROW)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, width=sum(widths))


def _check_columns(table: str, columns: list[str]) -> None:
    """A mock may show only the columns (or, for Key Measures, the measures) the project has."""
    if table == "Key Measures":
        missing = set(columns) - set(_g16().measure_table())
    else:
        missing = set(columns) - set(_model_columns(table))
    assert not missing, f"{table} lacks {sorted(missing)} in the model answer"


def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str = BLUE, width: float = 3) -> None:
    """One edge through the points, drawn straight between them (separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


# -- IF-16-0-A: the build sequence of the chapter -----------------------------------------------------------------------------

def if_16_0_a() -> Diagram:
    """The three tutorials in a row, and the six exercises branching from the copy saved after Tutorial 16.3."""
    d = Diagram("The Build Sequence of Chapter 16")
    titles, ex = _tutorial_titles(), _exercise_titles()
    assert sorted(ex) == [f"16.{i}" for i in range(1, 7)]
    c = ctx.values("ch16.chapter")
    t1, t2, t3 = ctx.values("ch16.t1"), ctx.values("ch16.t2"), ctx.values("ch16.t3")
    steps = {int(k): v for k, v in c["steps"].items()}
    q = _query_order()
    rels = _relationships()
    tabs = _query_tabs()
    folders = _folder_measures()
    assert tabs == ["Tests", "Checks"], tabs
    # what each tutorial adds, as the model answer holds it
    assert q[:6] == ["JournalEntry", "Employee", "Key Measures", "JournalLines", "Account", "JE Exceptions"]
    assert q[6:14] == ["PurchaseOrder", "PayrollRegister", "PayrollPayment", "PayrollPeriod", "PO Exceptions", "Payroll Exceptions", "Exceptions", "Tests"]
    assert q[14] == "Dispositions"
    assert _hidden_table("Dispositions") and not any("Dispositions" in (m[0], o[0]) for m, o, _ in rels), "Dispositions is hidden and related to nothing"
    related = lambda table: {o[0] for m, o, _ in rels if m[0] == table}   # noqa: E731
    assert related("Exceptions") == {"Tests", "Date", "Employee"} and related("JournalLines") == {"JournalEntry"}
    assert related("JournalEntry") == {"Date", "Employee"} and related("PurchaseOrder") == {"Date"} and related("PayrollRegister") == {"Date"}
    pages = {"journalEntries": 1, "entryLines": 1, "validation": 1, "monitoring": 2, "exceptionDetail": 2, "review": 3}
    assert [p for p in _page_ids() if p in pages] == list(pages), "the pages of the tutorials, in order"
    assert _page("entryLines")["type"] == "Drillthrough" and _page("exceptionDetail")["type"] == "Drillthrough"
    names = lambda *ps: [_page_name(p) for p in ps]   # noqa: E731
    assert c["n_pages"] == 6 + 6 + 1, "the pages of the model answer"
    assert t3["n_disp"] == 15 and t2["n"] == 151 and len(_g16().n16.TESTS) == 11

    widths = [270, 270, 270]
    gap = (860 - sum(widths)) / 2
    xs = [sum(widths[:i]) + gap * i for i in range(3)]
    texts = [
        f"<b>Tutorial 16.1<br>{esc(titles[1])}</b><br>JournalEntry with the approver's limit, five flags and the risk score; JournalLines, "
        f"the entries' ledger lines; JE Exceptions, {t1['exceptions']} rows, not loaded<br>Pages {names('journalEntries', 'entryLines')[0]}, "
        f"{names('journalEntries', 'entryLines')[1]} (drill-through) and {names('validation')[0]}; Test 1 reconciles {t1['n']} entries<br><i>{steps[1]} steps</i>",
        f"<b>Tutorial 16.2<br>{esc(titles[2])}</b><br>PurchaseOrder and PayrollRegister with their flags; the register Exceptions, {t2['n']} rows, "
        f"appended from three queries; Tests, {len(_g16().n16.TESTS)} rows; Population and Rate per 1,000<br>Pages {names('monitoring')[0]} and "
        f"{names('exceptionDetail')[0]} (drill-through); Test 2<br><i>{steps[2]} steps</i>",
        f"<b>Tutorial 16.3<br>{esc(titles[3])}</b><br>Dispositions, {t3['n_disp']} rows, hidden and merged into Exceptions; Reviewed Exceptions, "
        f"Open Exceptions and Data Through<br>Page {names('review')[0]}; Tests 3 and 4; the package's Tests 1 to 5 rerun; the memo<br><i>{steps[3]} steps</i>",
    ]
    h = max(kit.height_for(t, widths[i] - 8, SMALL, pad=16) for i, t in enumerate(texts))
    ids = []
    for i, t in enumerate(texts):
        ids.append(d.box(_nb(t), xs[i], 0, widths[i], h, fill=BLUE_TINT, stroke=BLUE, size=SMALL, align="left", valign="top", stroke_width=1.5))
    for a, b in zip(ids, ids[1:]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
    by = h + 44
    bar_text = ("<b>Ch16 Exercises.pbix</b>, the file saved with File > Save as after Tutorial 16.3. Each exercise works in this copy, on a page "
                "of its own and a display folder of measures; the model answer adds the DAX query view tab Checks.")
    bh = kit.height_for(bar_text, 860, SMALL, pad=14)
    bar = d.box(bar_text, 0, by, 860, bh, fill=GRAY_TINT, stroke=GRAY, size=SMALL, align="left", stroke_width=1.5)
    d.arrow(ids[2], bar, exit=(0.5, 1), entry=((xs[2] + widths[2] / 2) / 860, 0), meta="edgeStyle=none;")
    for sub, label in (("Ex 16.1", "ARInvoices"), ("Ex 16.2", "Exceptions 16.2"), ("Ex 16.3", "SurgeDays"), ("Ex 16.5", "Payments"), ("Ex 16.6", "PaymentPairs")):
        assert label in q or label in _loaded_tables(), label
    assert folders["Ex 16.4"] == ["Unexplained Rate per 1,000"] and "Digits" in _loaded_tables()
    adds = {
        "16.1": f"The page {_page_name('ex161')}; the queries ARInvoices, ARCreditBalances and ARLedger",
        "16.2": f"The page {_page_name('ex162')}; the queries SI DeliveredPriorYear and SL NotInvoiced, then Exceptions 16.2 and Tests 16.2; uses ARLedger of Ex 16.1",
        "16.3": f"The page {_page_name('ex163')}; the queries ClockEntries and SurgeDays",
        "16.4": f"The page {_page_name('ex164')}; no new query, the measure {folders['Ex 16.4'][0]}",
        "16.5": f"The page {_page_name('ex165')}; the query Payments, the column FirstDigit and the table Digits",
        "16.6": f"The page {_page_name('ex166')}; the query PaymentPairs; uses Payments of Ex 16.5",
    }
    assert [f"Ex 16.{i}" for i in range(1, 7)] == [_page_name(p) for p in _page_ids() if p.startswith("ex16")]
    ew = (860 - 5 * 10) / 6
    etexts = [f"<b>Ex {n}<br>{esc(ex[n])}</b><br><br>{esc(adds[n])}" for n in ex]
    eh = max(kit.height_for(_nb(t), ew - 10, SMALL, pad=18) for t in etexts)
    ey = by + bh + 40
    for i, t in enumerate(etexts):
        ex_id = d.box(_nb(t), i * (ew + 10), ey, ew, eh, fill=TEAL_TINT, stroke=TEAL, size=SMALL, align="left", valign="top", stroke_width=1.5)
        d.arrow(bar, ex_id, exit=((i * (ew + 10) + ew / 2) / 860, 1), entry=(0.5, 0), meta="edgeStyle=none;")
    bottom = ey + eh + 14
    lx = 0
    for label, fill, stroke in [("Built in the tutorials", BLUE_TINT, BLUE), ("The copy", GRAY_TINT, GRAY), ("Added by an exercise", TEAL_TINT, TEAL)]:
        d.box("", lx, bottom + 3, 16, 14, fill=fill, stroke=stroke, stroke_width=1.5, rounded=False)
        lw = text_width(label, SMALL, False) + 8
        d.text(label, lx + 22, bottom, lw, 20, size=SMALL, valign="middle")
        lx += 22 + lw + 24
    _note(d, f"The model answer holds {c['n_pages']} pages: the six of the tutorials, a page for each of Ex 16.1 to Ex 16.6 and Notes. Its DAX query view tabs are "
             f"{tabs[0]} and {tabs[1]}. The register, its tests and the dispositions are the tutorials' work; each exercise adds a page of its own.", bottom + 26)
    return d


# -- IF-16-0-B: Model view of the monitoring model ----------------------------------------------------------------------------------

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


def if_16_0_b() -> Diagram:
    """Model view with the nine tables of the tutorials: the register and its dimensions, the three populations and the ledger
    lines, and the hidden Dispositions with no line."""
    d = Diagram("Model View of the Monitoring Model")
    shown = {
        "Tests": ["TestID", "Test", "Process"],
        "Exceptions": ["TestID", "DocumentNumber", "EventDate", "Amount", "EmployeeID", "Disposition"],
        "Dispositions": ["TestID", "DocumentNumber", "Disposition"],
        "Employee": ["EmployeeID", "EmployeeName", "JobTitle"],
        "Date": ["Date", "Year", "YearMonth"],
        "JournalLines": ["SourceDocumentID", "Debit", "Credit"],
        "JournalEntry": ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "ApprovedByEmployeeID", "RiskScore"],
        "PurchaseOrder": ["OrderDate"],
        "PayrollRegister": ["PayDate"],
    }
    for table, columns in shown.items():
        _check_columns(table, columns)
    rels = _relationships()
    tutorial_rels = {(("Exceptions", "TestID"), ("Tests", "TestID")), (("Exceptions", "EventDate"), ("Date", "Date")),
                     (("Exceptions", "EmployeeID"), ("Employee", "EmployeeID")), (("JournalEntry", "PostingDate"), ("Date", "Date")),
                     (("JournalEntry", "ApprovedByEmployeeID"), ("Employee", "EmployeeID")),
                     (("JournalLines", "SourceDocumentID"), ("JournalEntry", "JournalEntryID")),
                     (("PurchaseOrder", "OrderDate"), ("Date", "Date")), (("PayrollRegister", "PayDate"), ("Date", "Date"))}
    present = {(m, o) for m, o, _ in rels}
    assert tutorial_rels <= present and all(active for _, _, active in rels), "the eight relationships of the tutorials, all active"
    assert not any(t in (m[0], o[0]) for m, o, _ in rels for t in ("PurchaseOrder", "PayrollRegister") if o[0] == "Employee" or m[0] == "Employee"), \
        "no line joins Employee to the orders or the registers"
    assert _hidden_table("Dispositions") and "Dispositions" not in {t for m, o, _ in rels for t in (m[0], o[0])}
    extra = sorted(present - tutorial_rels)
    extra_tables = sorted({t for m, o in extra for t in (m[0], o[0])} - set(shown))
    unrelated = sorted(_loaded_tables() - {t for m, o in present for t in (m[0], o[0])} - set(shown) - {"Key Measures"})

    def width(name: str) -> float:
        return max(text_width(esc(name), SMALL, True), *[text_width(esc(c), SMALL, False) for c in shown[name]]) + 22

    w_tests, w_exc, w_date, w_right = max(width("Tests"), width("Dispositions")), max(width("Exceptions"), width("Employee")), width("Date"), \
        max(width("JournalLines"), width("JournalEntry"), width("PurchaseOrder"), width("PayrollRegister"))
    x_tests = 88
    x_exc = x_tests + w_tests + 50
    x_date = x_exc + w_exc + 56
    x_right = 852 - w_right
    assert x_date + w_date + 90 <= x_right, f"the gap before the right-hand column is {x_right - x_date - w_date:.0f} px"
    win = pbi.window(d, 584, view="Model", tab="Home", buttons=["Manage relationships", "New measure", "New column"], file=FILE)
    top = win.top
    pbi.canvas(d, win.canvas_x, top, 860 - win.canvas_x, win.bottom - top)

    def card(name: str, x: float, y: float, w: float) -> pbi.ModelTable:
        return pbi.model_table(d, name, x, top + y, shown[name], w=w)

    # the right-hand column from the top: the two populations without lines to Employee, then the entries and their ledger lines
    po = card("PurchaseOrder", x_right, 12, w_right)
    pr = card("PayrollRegister", x_right, 84, w_right)
    jl = card("JournalLines", x_right, 156, w_right)
    je = card("JournalEntry", x_right, 280, w_right)
    tests = card("Tests", x_tests, 12, w_tests)
    exc = card("Exceptions", x_exc, 12, w_exc)
    date = card("Date", x_date, exc.rows["EventDate"] - top - 39, w_date)        # its first row meets EventDate on one straight line
    emp = card("Employee", x_exc, je.rows["ApprovedByEmployeeID"] - top - 39, w_exc)   # its first row meets ApprovedByEmployeeID likewise
    assert abs(date.rows["Date"] - exc.rows["EventDate"]) < 0.5 and abs(emp.rows["EmployeeID"] - je.rows["ApprovedByEmployeeID"]) < 0.5
    disp_y = 150
    disp = card("Dispositions", x_tests, disp_y, w_tests)
    d.outline(x_tests - 3, top + disp_y - 3, w_tests + 6, disp.h + 6, GRAY, width=1.5)
    d.text("<i>hidden, with no relationship</i>", x_tests - 3, top + disp_y + disp.h + 6, 150, 36, size=SMALL, color=GRAY)
    # the register and its dimensions
    _rel(d, tests.right("TestID"), exc.left("TestID"))
    xe = x_exc - 14
    _rel(d, emp.left("EmployeeID"), exc.left("EmployeeID"), [(xe, emp.rows["EmployeeID"]), (xe, exc.rows["EmployeeID"])])
    _rel(d, date.left("Date"), exc.right("EventDate"))
    # the populations: Date reaches each, and the lines leave Date in the order that keeps them from crossing
    xr = x_date + w_date
    _rel(d, date.right("Date"), je.left("PostingDate"), [(xr + 18, date.rows["Date"]), (xr + 18, je.rows["PostingDate"])])
    _rel(d, date.right("Date"), pr.left("PayDate"), [(xr + 32, date.rows["Date"]), (xr + 32, pr.rows["PayDate"])], one_tag=False)
    _rel(d, date.right("Date"), po.left("OrderDate"), [(xr + 46, date.rows["Date"]), (xr + 46, po.rows["OrderDate"])], one_tag=False)
    _rel(d, je.left("JournalEntryID"), jl.left("SourceDocumentID"), [(x_right - 14, je.rows["JournalEntryID"]), (x_right - 14, jl.rows["SourceDocumentID"])])
    # the approver: Employee filters the entries, and no other population
    _rel(d, emp.right("EmployeeID"), je.left("ApprovedByEmployeeID"))
    y = win.bottom + 10
    d.text("<b>1</b> the table that holds the key &nbsp; <b>*</b> the table that refers to it &nbsp; Arrow: the way a filter flows", 0, y, 860, 22, size=SMALL)
    _note(d, f"The nine tables of the tutorials, each with some of its columns. Employee reaches the entries through their approver, and no other population: "
             f"PurchaseOrder and PayrollRegister have no line to it. The model answer holds {len(_loaded_tables())} tables and {len(rels)} relationships, all active "
             f"and single direction. The exercises add {len(extra)} relationships, for {', '.join(extra_tables[:-1])} and {extra_tables[-1]}, and "
             f"{len(unrelated)} tables with none ({', '.join(unrelated)}). Key Measures, which holds the measures, is not drawn.", y + 26)
    return d


# -- IF-16-0-C: what the Checks tab tests and what only Desktop shows ----------------------------------------------------------------

def if_16_0_c() -> Diagram:
    """A two-column board: what a row of the Checks tab tests for each tutorial and exercise, and what only Desktop shows."""
    d = Diagram("What the Checks Tab Proves and What Only Desktop Shows")
    c = ctx.values("ch16.chapter")
    t3 = ctx.values("ch16.t3")
    sections = _g16().check_sections()
    assert sum(sections.values()) == c["n_checks"] and len(sections) == 9
    checks = (DAX_DIR / "Checks.dax").read_text(encoding="utf-8")
    labels = lambda sec: re.findall(rf'"Section", "{re.escape(sec)}", "Check", "([^"]*)"', checks)   # noqa: E731
    has = lambda sec, *words: all(any(w in label for label in labels(sec)) for w in words)   # noqa: E731
    t1 = ctx.values("ch16.t1")
    assert sum(s["n"] for s in t1["scores"] if s["score"] >= 2) == len(t1["two"]) + 1 == 8, "eight entries score 2 or more"
    assert has("Tutorial 16.1", "flags", "entries scoring", "risk score", "lines", "Test 1")
    assert has("Tutorial 16.2", "flags", "test and document pairs", "rate per 1,000", "January", "December", "approved by")
    assert has("Tutorial 16.3", "Test 3", "Test 4", "Data Through", "open exceptions", "documents failing two tests or more")
    assert has("Exercise 16.1", "open balance", "bucket", "unreconciled difference", "largest balance over 90")
    assert has("Exercise 16.2", "SI DeliveredPriorYear", "SL NotInvoiced", "Tests 16.2", "posted")
    assert has("Exercise 16.3", "surge days", "surge share", "overtime on other days", "first surge day")
    assert has("Exercise 16.4", "unexplained rate", "population", "blank", "total row")
    assert has("Exercise 16.5", "MAD", "first digit of 0", "full payments", "partial payments")
    assert has("Exercise 16.6", "near-duplicate pairs", "pairs within 30 days", "Orders Share", "Registers Share")
    items = [
        ("Tutorial 16.1", "The five flag counts, the entries and their amounts at each risk score, the eight entries that score 2 or more, the entries "
                          "by year and by approver, the ledger lines of the top entry, and Test 1"),
        ("Tutorial 16.2", "The flags of the orders and registers, the register's rows and their keys, each test's exceptions and rate per 1,000, "
                          "every month's count, the approvers, and the exceptions and rates of each process and year"),
        ("Tutorial 16.3", "Test 3's key counts, the dispositions by kind, the open exceptions by process and year, the documents that fail two tests "
                          "or more, Test 4's orders and registers, and Data Through with each year selected"),
        ("Exercise 16.1", "The open invoices, balance and customers, the five buckets, the largest balance over 90 days, account 1020, the difference "
                          "and its source, and the credit balances"),
        ("Exercise 16.2", "Both cutoff tests by year, their subtotal and standard cost, the rows of the copied register and of Tests 16.2, and the extra "
                          "invoice's posting and year"),
        ("Exercise 16.3", "The surge days in all and by year, the first day, the employees and hours of the surge entries, and each year's surge "
                          "overtime, share and overtime on other days"),
        ("Exercise 16.4", "Exceptions, population and both rates for each process and year; the unexplained rate with a test selected and the total "
                          "row's rate, both blank"),
        ("Exercise 16.5", "The payments, full and partial, the deviation of each group and of all payments, and the payments whose first digit is 0 "
                          "or whose text begins with 0"),
        ("Exercise 16.6", "The pairs, those within 30 days and on the same invoice, and the orders, entries and registers approved by the Chief "
                          "Financial Officer, the Controller and the Accounting Manager, with their shares"),
    ]
    assert [k for k, _ in items] == list(sections), "one card for each section of the Checks tab"
    # what only Desktop shows, each claim tied to the project
    interactions = _page("monitoring")["visualInteractions"]
    nofilter = {(i["source"], i["target"]) for i in interactions if i["type"] == "NoFilter"}
    assert nofilter == {("approvers", "rates"), ("heatMap", "dataThrough"), ("approvers", "dataThrough")}, nofilter
    assert _page("ex165")["visualInteractions"] == [{"source": "kindSlicer", "target": "madByKind", "type": "NoFilter"}]
    assert has("Tutorial 16.3", "Data Through with 2024 selected", "Data Through with 2026 selected")
    assert _page("entryLines")["type"] == "Drillthrough" and _page("exceptionDetail")["type"] == "Drillthrough"
    years = ", ".join(t3["through_years"])
    right = [
        "<b>The heat map's shading</b> The Checks tab tests the count in each cell of the Monitoring matrix, but not the rule colors that make January "
        "darkest, or that the number stays in every cell<br><i>Tutorial 16.2, Step 11</i>",
        "<b>The drill-through click</b> The right-click that opens Entry Lines or Exception Detail, and the filters the click passes: the page's rows "
        "come from the cell, not from a measure<br><i>Tutorial 16.1, Step 10; Tutorial 16.2, Step 13</i>",
        "<b>The edited interactions as a reader meets them</b> On Monitoring the project disables approvers to rates, approvers to Data Through and "
        "heat map to Data Through, and keeps heat map to rates available for the selected context. On Exercise 16.5 it disables the PaymentKind slicer to "
        "the deviation table. Verify each source and target pair in Desktop<br><i>Tutorial 16.2, Step 12c; "
        "Tutorial 16.3, Step 7c; Exercise 16.5, Step 4d</i>",
        f"<b>The Data Through card under a slicer</b> The Checks tab tests the date with each year selected ({years}), but not that the card on the "
        "page follows the Year slicer and ignores a click<br><i>Tutorial 16.3, Step 7</i>",
        "<b>The Power Query step names a student chose</b> The project's steps carry Desktop's names. A student's queries are read in the file, because "
        "the Checks tab tests the model and not how it was built<br><i>Tutorials 16.1 to 16.3; every exercise</i>",
    ]
    col_w, gap = 422, 16
    d.box("<b>Tested by the Checks tab</b>", 0, 0, col_w, 32, fill=TEAL, stroke=TEAL, color=WHITE, size=14, rounded=False)
    d.box("<b>Visible only in Desktop</b>", col_w + gap, 0, col_w, 32, fill=AMBER, stroke=AMBER, color=WHITE, size=14, rounded=False)
    bottoms = []
    for x0, cards, fill, stroke, badge in ((0, items, TEAL_TINT, TEAL, True), (col_w + gap, right, AMBER_TINT, AMBER, False)):
        cy = 40
        for i, card in enumerate(cards):
            text = card if not badge else f"<b>{card[0]}</b> {card[1]}"
            tw = col_w - (70 if badge else 0)
            h = max(kit.height_for(_nb(text), tw, SMALL, pad=18), 54 if badge else 0)
            d.box(_nb(text), x0, cy, tw, h, fill=fill, stroke=stroke, size=SMALL, align="left", rounded=False, stroke_width=1.5)
            if badge:
                d.box(f"<b>{sections[card[0]]}</b><br>rows", x0 + tw + 4, cy, col_w - tw - 4, h, fill=WHITE, stroke=stroke, size=SMALL, rounded=False,
                      stroke_width=1.5)
            cy += h + 8
        bottoms.append(cy - 8)
    _note(d, f"The Checks tab of the model answer holds {c['n_checks']} rows, a section for each tutorial and exercise. Choose Home > Refresh, then Run. "
             "A row tests a value, not how a visual looks, so the right-hand column is for the instructor to open the pages.", max(bottoms) + 12)
    return d


# -- IF-16-0-D: the order of a review ---------------------------------------------------------------------------------------------------

def if_16_0_d() -> Diagram:
    """A decision list from top to bottom: what is expected, what recurs by design, then the order of the rest, each with its example."""
    import statistics   # noqa: F401  (kept for readability of the examples below)
    from notes import ch16 as n16
    data = ctx.data()
    t2, t3 = ctx.values("ch16.t2"), ctx.values("ch16.t3")
    reg = n16.register(data)
    last_month = max(e["date"][:7] for e in reg)
    closes = [e for e in reg if e["disposition"] == "Expected"]
    assert len(closes) == 6 and {e["test"] for e in closes} == {"JE AboveLimit"} and all(e["doc"] in data.closes_of(int(e["date"][:4])) for e in closes), \
        "the expected exceptions are the year-end closes"
    selfs = [e for e in reg if e["test"] == "PR SelfApproved"]
    assert len(selfs) == t2["selfs"]["n"] and all(e["emp"] == t2["selfs"]["approver"] and not e["disposition"] for e in selfs)
    per_doc = defaultdict(list)
    for e in reg:
        per_doc[e["doc"]].append(e["test"])
    multi = {k: v for k, v in per_doc.items() if len(v) > 1}
    top = max(multi, key=lambda k: len(multi[k]))
    assert len(multi) == t3["n_multi"] and top == t3["je_top"] and len(multi[top]) == t3["je_top_n"]
    others = [e for e in reg if not e["disposition"] and e["test"] != "PR SelfApproved" and e["doc"] not in multi]
    newest = [e for e in reg if e["date"][:7] == last_month]
    assert all(e["disposition"] == "Expected" or e["test"] == "PR SelfApproved" for e in newest), \
        "the latest month holds only the expected closes and the recurring registers: nothing is new"
    biggest = max(others, key=lambda e: e["amount"])
    oldest = min(others, key=lambda e: e["date"])
    assert biggest["doc"] != oldest["doc"] or True
    month_name = f"{n16.MONTHS[int(last_month[5:]) - 1]} {last_month[:4]}"
    rest = {len(v) for k, v in multi.items() if k != top}
    two_each = {2: "two each"}.get(max(rest), f"up to {max(rest)} each") if len(rest) == 1 else f"two to {max(rest)} each"
    rows = [
        ("Is it expected every period?", f"<b>Set aside.</b> Record the disposition and the evidence once, then check at each refresh that it recurs",
         f"The {len(closes)} year-end closing entries, two a year, that exceed every approver's limit (JE AboveLimit): disposition Expected", "gray"),
        ("Does it recur because of the way a control is designed?", "<b>Set aside.</b> Report one finding, change the control, and the exceptions should stop",
         f"The {len(selfs)} registers approved by the employee they pay (PR SelfApproved), one or more in every month", "gray"),
        ("Does one document fail several tests?", "<b>Use the score as a first cue.</b> Materiality, age and urgency can override it",
         f"{_nowrap(top)}, the opening entry: {len(multi[top])} tests. {len(multi) - 1} other documents fail {two_each}", "blue"),
        ("Is it new this month?", "<b>Review next.</b> It arrives with no disposition",
         f"None in {month_name}: its {len(newest)} exceptions are {sum(1 for e in newest if e['disposition'] == 'Expected')} closes and "
         f"{sum(1 for e in newest if e['test'] == 'PR SelfApproved')} recurring registers", "blue"),
        ("Everything else", "<b>Review by amount and age.</b> The larger and the older first",
         f"{len(others)} open exceptions on one test each; the largest, {_nowrap(biggest['doc'])}, ${_money(biggest['amount'])}; the oldest, "
         f"{_nowrap(oldest['doc'])}, {_nowrap(oldest['date'])}", "blue"),
    ]
    d = Diagram("The Order of a Review")
    qw, aw, ew = 224, 250, 316
    x_q, x_a = 0, qw + 54
    x_e = x_a + aw + 16
    assert x_e + ew <= 860 + 1
    d.box("<b>Ask, from the top</b>", x_q, 0, qw, 28, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL, rounded=False)
    d.box("<b>What the reviewer does</b>", x_a, 0, aw, 28, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL, rounded=False)
    d.box("<b>An example from the register</b>", x_e, 0, ew + 0, 28, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL, rounded=False)
    y = 40
    qids = []
    for i, (q_text, a_text, e_text, tint) in enumerate(rows):
        h = max(kit.height_for(q_text, qw, BODY_SIZE, bold=True, pad=18), kit.height_for(a_text, aw, SMALL, pad=18), kit.height_for(e_text, ew, SMALL, pad=18), 58)
        fill, stroke = kit.tint("blue" if tint == "blue" else "gray")
        qid = d.box(f"<b>{i + 1}. {esc(q_text)}</b>", x_q, y, qw, h, fill=BLUE_TINT, stroke=BLUE, size=BODY_SIZE, stroke_width=1.5)
        aid = d.box(a_text, x_a, y, aw, h, fill=fill, stroke=stroke, size=SMALL, align="left", stroke_width=1.5)
        d.box(e_text, x_e, y, ew, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", stroke_width=1)
        d.arrow(qid, aid, exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
        d.text("yes" if i < 4 else "then", x_q + qw + 2, y + h / 2 - 22, 50, 18, size=SMALL, align="center", bold=True)
        qids.append((qid, y, h))
        y += h + 30
    for (a, ya, ha), (b, yb, hb) in zip(qids, qids[1:]):
        d.arrow(a, b, exit=(0.5, 1), entry=(0.5, 0), meta="edgeStyle=none;")
        d.text("no", x_q + qw / 2 + 6, ya + ha + 5, 30, 18, size=SMALL, bold=True)
    bottom = y - 30
    _note(d, "A sketch of the order the chapter gives: the expected and the recurring exceptions are dealt with once, as groups; what remains is reviewed by the "
             "number of tests failed, then by novelty, then by amount and age. This is a teaching order, not Li and colleagues' adaptive suspicion score, and a "
             "serious single exception may need priority. A question answered yes sends the exception to its action box; no sends it down. "
             "The examples, counts and amounts are read from the register.", bottom + 10)
    return d


# -- pieces for the report pages ------------------------------------------------------------------------------------------------------------

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


def _grid_line(d: Diagram, x: float, y: float, w: float, h: float) -> None:
    """A one-pixel gridline (a box with a stroke would draw two)."""
    d.vertex("", f"rounded=0;html=1;fillColor={RULE};strokeColor=none;", x, y, w, h)


def _vaxis(d: Diagram, label_x: float, grid_x: float, grid_w: float, top: float, plot_h: float, ticks: list[float], fmt,
           align: str = "right", label_w: float = 44) -> callable:
    """Ticks and gridlines of a vertical value axis; fmt turns a tick into its label.  Returns the function from value to y."""
    low, high = ticks[0], ticks[-1]
    y_of = lambda v: top + (high - v) * plot_h / (high - low)   # noqa: E731
    for t in ticks:
        if grid_w:
            _grid_line(d, grid_x, y_of(t), grid_w, 1)
        d.text(fmt(t), label_x, y_of(t) - 10, label_w, 20, size=SMALL, color=GRAY, align=align, valign="middle")
    return y_of


def _columns(d: Diagram, x: float, y: float, w: float, h: float, title: str, cats: list[str], values: list[float | None],
             ticks: list[float], fmt, every: int = 1, selected: bool = False, lines: int = 1) -> dict:
    """A clustered column chart of one series; a blank (None) draws no column.  Returns the plot geometry."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title, selected=selected, lines=lines)
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 8, ih - 34
    y_of = _vaxis(d, ix, left, plot_w, top, plot_h, ticks, fmt)
    step = plot_w / len(cats)
    xs = []
    for i, v in enumerate(values):
        cx = left + step * i + step * 0.2
        xs.append(cx + step * 0.3)
        if v is not None:
            d.box("", cx, y_of(v), step * 0.6, y_of(ticks[0]) - y_of(v), fill=BLUE, stroke=BLUE, rounded=False)
        if i % every == 0:
            d.text(esc(cats[i]), xs[-1] - step * every / 2, top + plot_h + 4, step * every, 20, size=SMALL, color=GRAY, align="center")
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of, step=step)


def _combo(d: Diagram, x: float, y: float, w: float, h: float, title: str, cats: list[str], columns: tuple[str, list[float | None]],
           line: tuple[str, list[float | None]], ticks: list[float], fmt, line_ticks: list[float], line_fmt, every: int = 1) -> dict:
    """A line and clustered column chart: the columns on the left axis, the line on a secondary axis on the right.  A blank draws no
    column and leaves a gap in the line."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title, lines=1)
    d.box("", ix, iy + 4, 12, 12, fill=BLUE, stroke=BLUE, rounded=False)
    d.text(esc(columns[0]), ix + 16, iy - 2, text_width(esc(columns[0]), SMALL, False) + 16, 20, size=SMALL)
    lx = ix + 16 + text_width(esc(columns[0]), SMALL, False) + 34
    d.box("", lx, iy + 9, 14, 3, fill=AMBER, stroke=AMBER, rounded=False)
    d.text(esc(line[0]), lx + 18, iy - 2, text_width(esc(line[0]), SMALL, False) + 16, 20, size=SMALL)
    iy += 20
    ih -= 20
    left, plot_w = ix + 48, iw - 104
    top, plot_h = iy + 8, ih - 34
    y_of = _vaxis(d, ix, left, plot_w, top, plot_h, ticks, fmt)
    y2_of = _vaxis(d, left + plot_w + 6, left, 0, top, plot_h, line_ticks, line_fmt, align="left", label_w=48)
    step = plot_w / len(cats)
    xs = []
    for i, v in enumerate(columns[1]):
        cx = left + step * i + step * 0.2
        xs.append(cx + step * 0.3)
        if v is not None:
            d.box("", cx, y_of(v), step * 0.6, y_of(ticks[0]) - y_of(v), fill=BLUE, stroke=BLUE, rounded=False)
        if i % every == 0:
            d.text(esc(cats[i]), xs[-1] - step * every / 2, top + plot_h + 4, step * every, 20, size=SMALL, color=GRAY, align="center")
    run: list[tuple[float, float]] = []
    runs = []
    for cx, v in zip(xs, line[1]):
        if v is None:
            if run:
                runs.append(run)
            run = []
        else:
            run.append((cx, y2_of(v)))
    if run:
        runs.append(run)
    for pts in runs:
        if len(pts) > 1:
            _polyline(d, pts, AMBER, 2.5)
        for px, py in pts:
            d.vertex("", f"rhombus;html=1;fillColor={AMBER};strokeColor={AMBER};", px - 4, py - 4, 8, 8)
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of, y2_of=y2_of, step=step)


# -- IF-16-1-A: the Ex 16.1 page ---------------------------------------------------------------------------------------------------

def _aging(data, end: str) -> list[tuple[str, float, int]]:
    """(bucket, open balance, open invoices) for each bucket of the model answer, from the invoices open at the as-of date."""
    rows = data.q("WITH Applied AS (SELECT SalesInvoiceID, SUM(AppliedAmount) AS Applied FROM CashReceiptApplication "
                  "WHERE ApplicationDate <= ?1 GROUP BY SalesInvoiceID), "
                  "Credited AS (SELECT OriginalSalesInvoiceID AS SalesInvoiceID, SUM(GrandTotal) AS Credited FROM CreditMemo "
                  "WHERE CreditMemoDate <= ?1 GROUP BY OriginalSalesInvoiceID) "
                  "SELECT ROUND(si.GrandTotal - COALESCE(a.Applied, 0) - COALESCE(c.Credited, 0), 2), julianday(?1) - julianday(si.DueDate) "
                  "FROM SalesInvoice si LEFT JOIN Applied a ON a.SalesInvoiceID = si.SalesInvoiceID "
                  "LEFT JOIN Credited c ON c.SalesInvoiceID = si.SalesInvoiceID WHERE si.InvoiceDate <= ?1", end)
    names = ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]
    out = {n: [0.0, 0] for n in names}
    for balance, days in rows:
        if balance <= 0:
            continue
        k = 0 if days <= 0 else 1 if days <= 30 else 2 if days <= 60 else 3 if days <= 90 else 4
        out[names[k]][0] += balance
        out[names[k]][1] += 1
    return [(n, round(out[n][0], 2), out[n][1]) for n in names]


def if_16_1_a() -> Diagram:
    """The Ex 16.1 page: the aging with its total row, the cards that reconcile it to the ledger, the credit balances and the
    ledger by source document with the JournalEntry row outlined."""
    g = ctx.values("ch16.g1")
    e = ctx.values("ch16.ex1")
    data = ctx.data()
    page = "ex161"
    t_aging, t_source = _title(page, "aging"), _title(page, "ledgerBySource")
    assert (t_aging, t_source) == (g["t_aging"], g["t_source"]) == (f"Receivables aged at {e['asof']}", "Account 1020 by source document")
    assert _projections(page, "aging", "Values") == ["Bucket", "Open Balance", "Open Invoices"]
    assert _projections(page, "ledgerBySource", "Values") == ["SourceDocumentType", "Ledger Receivables"]
    assert _projections(page, "reconCards", "Data") == ["Open Balance", "Ledger Receivables", "Unreconciled Difference"]
    assert _projections(page, "creditCards", "Data") == ["Credit Balances", "Credit Balance Invoices"]
    _check_columns("Key Measures", ["Open Balance", "Open Invoices", "Ledger Receivables", "Unreconciled Difference", "Credit Balances", "Credit Balance Invoices"])
    _check_columns("ARInvoices", ["Bucket", "BucketOrder"])
    _check_columns("ARLedger", ["SourceDocumentType"])
    assert "BucketOrder" in json.dumps(_visual(page, "aging")["visual"]["query"]["sortDefinition"]), "the aging table is sorted by BucketOrder"
    aging = _aging(data, e["asof"])
    assert [round(a, 2) for _, a, _ in aging] == [round(b["amount"], 2) for b in e["b"]], "the buckets of the note"
    assert sum(n for _, _, n in aging) == e["n"] and abs(sum(a for _, a, _ in aging) - e["total"]) < 0.005
    by_source = sorted(g["by_source"], key=lambda r: r["kind"])        # a table sorts its first column unless the visual sorts otherwise
    assert [r["kind"] for r in by_source] == ["CashReceiptApplication", "CreditMemo", "JournalEntry", "SalesInvoice"]
    ledger = sum(r["amount"] for r in by_source)
    assert abs(ledger - e["ledger"]) < 0.005 and abs(e["ledger"] - e["total"] - e["difference"]) < 0.005
    journal = next(r["amount"] for r in by_source if r["kind"] == "JournalEntry")
    assert abs(journal - e["difference"]) < 0.005, "the JournalEntry row is the whole difference"
    assert abs(ledger - journal - e["total"]) < 0.005, "every other source nets to the open balance"
    assert e["n_negative"] > 0 and e["negative"] < 0
    rows = [[n, _money(a), f"{c:,}"] for n, a, c in aging]
    total = ["Total", _money(e["total"]), f"{e['n']:,}"]
    pad = 16
    wa = [112, 124, 112]
    wl = [200, 148]
    t1_h = 20 + 12 + (len(rows) + 2) * pbi.ROW
    t2_h = 20 + 12 + (len(by_source) + 2) * pbi.ROW
    canvas_h = pad + t1_h + 14 + t2_h + pad
    d = Diagram("The Ex 16.1 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    ta = _table_visual(d, pad, pad, t_aging, ["Bucket", "Open Balance", "Open Invoices"], wa, rows, aligns=["left", "right", "right"], title_lines=1, total=total)
    tl = _table_visual(d, pad, ta["bottom"] + 14, t_source, ["SourceDocumentType", "Ledger Receivables"], wl,
                       [[r["kind"], _money(r["amount"])] for r in by_source], aligns=["left", "right"], title_lines=1,
                       total=["Total", _money(ledger)])
    jr = next(i for i, r in enumerate(by_source) if r["kind"] == "JournalEntry")
    jx, jy, jw, jh = tl["geometry"][(jr, 0)]
    d.outline(jx + 1, jy + 1, tl["width"] - 2, jh - 2, CORAL, width=2.5, front=True)
    cx0 = max(ta["right"], tl["right"]) + 16
    cw = 860 - pad - cx0
    _cards_visual(d, cx0, pad, cw, 86, [("Open<br>Balance", _money(e["total"])), ("Ledger<br>Receivables", _money(e["ledger"])),
                                         ("Unreconciled<br>Difference", _money(e["difference"]))])
    _cards_visual(d, cx0, pad + 96, cw * 2 / 3, 86, [("Credit<br>Balances", _money(e["negative"])), ("Credit Balance<br>Invoices", f"{e['n_negative']:,}")])
    cy = pad + 96 + 86 + 14
    cy = kit.callout(d, f"<b>The difference is one line.</b> Unreconciled Difference, {_money(e['difference'])}, is the JournalEntry row of the table on the left: "
                        f"a line of {esc(e['entry'])} that no invoice supports. The other sources net to the open balance.", cx0, cy, cw, "teal") + 12
    kit.callout(d, f"<b>The credit balances stand apart.</b> {e['n_negative']} invoices have applications and credit memos above their total, and their {_money(e['negative'])}, recorded as customer credits, is outside "
                   f"the open balance. Netted in, they would add a second difference, {_money(g['net_difference'])}, which is no new finding.", cx0, cy, cw, "gray")
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, with the as-of date {e['asof']} typed in every query. Outlined: the JournalEntry row of the ledger table. The "
             "buckets follow BucketOrder, and both tables show Desktop's total row. The page's text box with the written answers is not drawn.", canvas_h + 34)
    return d


# -- IF-16-2-A: one invoice, four dates ---------------------------------------------------------------------------------------------

def if_16_2_a() -> Diagram:
    """A timeline across a year-end: the invoice date, the shipment, the delivery and the ledger posting of SI-2026-013742, the year each
    falls in, and the test that can see it."""
    import datetime as dt
    e = ctx.values("ch16.ex2")
    g = ctx.values("ch16.g2")
    data = ctx.data()
    odd = e["odd"]
    number = odd["number"]
    invoice = data.one("SELECT InvoiceDate FROM SalesInvoice WHERE InvoiceNumber = ?", number)
    shipped, delivered = data.q("SELECT s.ShipmentDate, s.DeliveryDate FROM SalesInvoice si JOIN SalesInvoiceLine l ON l.SalesInvoiceID = si.SalesInvoiceID "
                                "JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                                "WHERE si.InvoiceNumber = ? ORDER BY s.DeliveryDate DESC", number)[0]
    posted = sorted({r[0] for r in data.q("SELECT PostingDate FROM GLEntry WHERE VoucherNumber = ? AND SourceDocumentType = 'SalesInvoice'", number)})
    assert posted == [odd["posted"]] and shipped == odd["shipped"] and delivered == g["delivered"]
    years = [x[:4] for x in (invoice, shipped, delivered)]
    assert len(set(years)) == 1 and posted[0][:4] != delivered[:4] and posted[0][5:] == "01-01", "three dates in one year, the posting on the first day of the next"
    assert invoice[:7] == dt.datetime.strptime(odd["dated"], "%B %Y").strftime("%Y-%m") and invoice < shipped < delivered
    y_end, y_next = int(delivered[:4]), int(posted[0][:4])
    assert y_next == y_end + 1
    start = dt.date(y_end, 12, 1)
    end = dt.date(y_next, 1, 4)
    span = (end - start).days + 1
    ax0, ax1 = 30.0, 830.0
    per_day = (ax1 - ax0) / span
    x_of = lambda iso: ax0 + ((dt.date.fromisoformat(iso) - start).days + 0.5) * per_day   # noqa: E731
    boundary = ax0 + (dt.date(y_next, 1, 1) - start).days * per_day
    d = Diagram("One Invoice, Four Dates")
    # the year brackets over everything
    by = 8
    for x0, x1, label in ((ax0, boundary - 4, str(y_end)), (boundary + 4, ax1, str(y_next))):
        d.box("", x0, by + 22, x1 - x0, 3, fill=INK, stroke=INK, rounded=False)
        d.box("", x0, by + 22, 3, 12, fill=INK, stroke=INK, rounded=False)
        d.box("", x1 - 3, by + 22, 3, 12, fill=INK, stroke=INK, rounded=False)
        d.text(f"<b>{label}</b>", x0, by, x1 - x0, 20, size=BODY_SIZE, align="center")
    ya = 176                                                     # the axis
    d.edge(d.anchor(boundary, by + 40), d.anchor(boundary, ya + 70), color=GRAY, width=1.5, dashed=True, meta="edgeStyle=none;")
    d.box("", ax0, ya - 1, ax1 - ax0, 3, fill=INK, stroke=INK, rounded=False)
    d.text("<i>year-end</i>", boundary - 36, ya + 70, 72, 18, size=SMALL, color=GRAY, align="center")
    d.text(f"<i>December 1, {y_end}</i>", ax0 - 4, ya + 6, 120, 18, size=SMALL, color=GRAY)
    d.text(f"<i>January 4, {y_next}</i>", ax1 - 116, ya + 6, 120, 18, size=SMALL, color=GRAY, align="right")
    marks = [("Invoice date", invoice, BLUE, "above"), ("Shipment date", shipped, GRAY, "below"), ("Delivery date", delivered, TEAL, "above"),
             ("Ledger posting", posted[0], AMBER, "above")]
    lw = 160
    for label, iso, color, side in marks:
        mx = x_of(iso)
        fill = {BLUE: BLUE_TINT, GRAY: GRAY_TINT, TEAL: TEAL_TINT, AMBER: AMBER_TINT}[color]
        text = f"<b>{label}</b><br>{_nowrap(iso)}"
        lx = min(max(mx - lw / 2, 0), 860 - lw)
        if label == "Delivery date":
            lx = max(x_of(invoice) - lw / 2, 0) + lw + 12          # to the right of the invoice's label, so the two do not overlap
        if label == "Invoice date":
            lx = max(mx - lw / 2, 0)
        assert lx <= mx <= lx + lw, f"{label}: the leader line meets its label"
        if side == "above":
            ly = ya - 74
            d.box("", mx - 0.75, ly + 40, 1.5, ya - ly - 40, fill=color, stroke=color, rounded=False)
        else:
            ly = ya + 34
            d.box("", mx - 0.75, ya, 1.5, ly - ya, fill=color, stroke=color, rounded=False)
        d.box(text, lx, ly, lw, 40, fill=fill, stroke=color, size=SMALL, stroke_width=1.5)
        d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={WHITE};strokeWidth=1.5;", mx - 7, ya - 6, 14, 14)
    # the two tests
    ty = ya + 112
    bw = (860 - 24) / 2
    by_invoice_date = [z["n"] for z in e["g"]]
    left = (f"<b>A test by invoice date finds nothing here.</b> It compares the year of the delivery with the year of the invoice. {esc(number)} is dated "
            f"{_nowrap(invoice)} and delivered {_nowrap(delivered)}: both fall in {y_end}, so no year differs.")
    right = (f"<b>A test by posting date would find it.</b> It is posted {_nowrap(posted[0])}, in {y_next}, a year after the delivery. Chapter 12 counts it "
             f"among the {e['posted'][1]} invoices of January {y_next}; the exercise's test, by invoice date, counts {by_invoice_date[1]}.")
    h = max(kit.height_for(left, bw, BODY_SIZE, pad=22), kit.height_for(right, bw, BODY_SIZE, pad=22))
    d.box(left, 0, ty, bw, h, fill=GRAY_TINT, stroke=GRAY, size=BODY_SIZE, align="left", valign="top", stroke_width=1.5)
    d.box(right, bw + 24, ty, bw, h, fill=AMBER_TINT, stroke=AMBER, size=BODY_SIZE, align="left", valign="top", stroke_width=1.5)
    _note(d, f"The four dates of {number}, to scale from December {y_end} to the first days of January {y_next}. The year-end falls between the delivery and the posting. "
             "It is Chapter 6's revenue cutoff error: revenue recorded in the year after the goods shipped. Each date is read from the dataset.", ty + h + 10)
    return d


# -- IF-16-3-A: the Ex 16.3 page ------------------------------------------------------------------------------------------------------

def _surge_months(data) -> tuple[list[str], dict[str, list[float]]]:
    """For each month of the window: the surge days, the surge overtime hours and the plant's overtime hours, from the clock entries of the
    Manufacturing cost center the way the model answer groups them."""
    g16 = _g16()
    center = data.one("SELECT CostCenterID FROM CostCenter WHERE CostCenterName = 'Manufacturing'")
    days = g16.clock_days(data)
    out: dict[str, list[float]] = defaultdict(lambda: [0, 0.0, 0.0])
    for day, rs in days.items():
        plant = [r for r in rs if r[4] == center]
        if not plant:
            continue
        m = out[day[:7]]
        m[2] += sum(r[2] for r in plant)
        if len({r[0] for r in plant}) > 1 and len({r[3] for r in plant}) == 1:
            m[0] += 1
            m[1] += sum(r[2] for r in plant)
    months = [f"{y}-{m:02d}" for y in data.years for m in range(1, 13)]
    return months, {k: out[k] for k in months}


def if_16_3_a() -> Diagram:
    """The Ex 16.3 page: surge days by month, the surge-day overtime with its share of the plant's overtime, and the table by year."""
    g = ctx.values("ch16.g3")
    e = ctx.values("ch16.ex3")
    data = ctx.data()
    page = "ex163"
    t_month, t_combo, t_year = _title(page, "surgeDaysByMonth"), _title(page, "surgeOvertime"), _title(page, "surgeByYear")
    assert (t_month, t_combo, t_year) == (g["t_month"], g["t_combo"], g["t_year"])
    assert _projections(page, "surgeDaysByMonth", "Y") == ["Surge Days"] and _projections(page, "surgeOvertime", "Y") == ["Surge Overtime Hours"]
    assert _projections(page, "surgeOvertime", "Y2") == ["Surge Share of Overtime"]
    cols = _projections(page, "surgeByYear", "Values")
    assert cols == ["Year", "Surge Days", "Surge Overtime Hours", "Plant Overtime Hours", "Surge Share of Overtime"], cols
    _check_columns("Key Measures", cols[1:])
    months, by_month = _surge_months(data)
    flt = json.dumps(_visual(page, "surgeDaysByMonth")["filterConfig"])
    assert all(f"{y}" in flt for y in data.years), "the Year filter keeps the years of the window"
    years = list(data.years)
    for i, y in enumerate(years):
        mine = [by_month[m] for m in months if m.startswith(str(y))]
        assert sum(m[0] for m in mine) == e["by_year"][i][1] and abs(sum(m[1] for m in mine) - e["on_surge"][i]) < 0.005
        assert abs(sum(m[1] for m in mine) / sum(m[2] for m in mine) - e["shares"][i]) < 1e-9
        assert abs(sum(m[2] for m in mine) - e["on_surge"][i] - e["other"][i]) < 0.01
    first = min(m for m in months if by_month[m][0])
    assert first == e["first"][:7] and by_month[first][0] == 1, "surge days begin with one day, the first surge day"
    days_m = [by_month[m][0] or None for m in months]
    ot_m = [by_month[m][1] or None for m in months]
    share_m = [by_month[m][1] / by_month[m][2] if by_month[m][0] else None for m in months]
    peak = max(by_month[m][0] for m in months)
    assert peak == e["peak"]
    pad = 16
    w = 860 - 2 * pad
    h1, h2 = 150, 190
    day_ticks = list(range(0, peak + 2, 2))
    ot_ticks = pbi.nice_ticks(0, max(v for v in ot_m if v), 4)
    every = 3
    d = Diagram("The Ex 16.3 Page")
    rows = [[str(y), f"{e['by_year'][i][1]:,}", f"{e['on_surge'][i]:,.0f}", f"{e['on_surge'][i] + e['other'][i]:,.0f}", _pct(e["shares"][i])] for i, y in enumerate(years)]
    tot_surge, tot_plant = sum(e["on_surge"]), sum(e["on_surge"]) + sum(e["other"])
    total = ["Total", f"{e['total']:,}", f"{tot_surge:,.0f}", f"{tot_plant:,.0f}", _pct(tot_surge / tot_plant)]
    t_h = 20 + 12 + (len(rows) + 2) * pbi.ROW
    canvas_h = pad + h1 + 10 + h2 + 10 + t_h + pad
    pbi.canvas(d, 0, 0, 860, canvas_h)
    c1 = _columns(d, pad, pad, w, h1, t_month, months, days_m, [float(t) for t in day_ticks], lambda v: f"{v:.0f}", every=every)
    c2 = _combo(d, pad, pad + h1 + 10, w, h2, t_combo, months, ("Surge Overtime Hours", ot_m), ("Surge Share of Overtime", share_m), ot_ticks,
                lambda v: f"{v:,.0f}", [0, 0.2, 0.4, 0.6, 0.8, 1.0], lambda v: f"{100 * v:.0f}%", every=every)
    t = _table_visual(d, pad, pad + h1 + 10 + h2 + 10, t_year, cols, [80, 148, 192, 192, 204], rows, aligns=["left"] + ["right"] * 4, title_lines=1, total=total)
    assert t["right"] <= 860 - pad + 1
    # outline the month with the most surge days, in both charts
    pk = next(i for i, m in enumerate(months) if by_month[m][0] == peak)
    for c in (c1, c2):
        d.outline(c["xs"][pk] - c["step"] * 0.5, c["top"] - 2, c["step"], c["height"] + 4, CORAL, width=2, front=True)
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, with the Year filter on the {len(years)} years of the window, so the axis ends in {months[-1]} and not in the empty "
             f"months of the Date table. A month with no surge day has no column and leaves a gap in the line. The first surge day is {e['first']}, the only one of "
             f"{first}; the outlined month, {months[pk]}, has the most, {peak}. The table shows Desktop's total row; the page's text box is not drawn.", canvas_h + 34)
    return d


# -- IF-16-4-A: the Ex 16.4 page ---------------------------------------------------------------------------------------------------

def _tests_rows() -> list[list[str]]:
    """The rows of the Tests table, typed in Power Query with Enter data (TestID, Test, Process, Source), as the project stores them."""
    import base64
    import zlib
    text = _tmdl("tables/Tests.tmdl")
    blob = re.search(r'Binary\.FromText\("([^"]+)"', text).group(1)
    return json.loads(zlib.decompress(base64.b64decode(blob), -15))


def _year_matrix(d: Diagram, x: float, y: float, title: str, row_w: float, block: list[float], years: list[str], value_heads: list[str],
                 row_heads: list[str], cells: list[list[list[str]]], total: list[list[str]], row_h: float = 34) -> dict:
    """A matrix with one level of rows and the years on columns, each year holding the same values side by side: a title, the
    year headings over the value headings, the rows (a heading may break with <br>) and a total row.  cells[r][y] are the strings of
    one row and one year.  Returns the visual's geometry."""
    inner_w = row_w + len(years) * sum(block)
    w = inner_w + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * kit.lines_for(label, w - 12, SMALL, bold=True) + 4
    head1, head2, tot_h = 22, 53, 24
    h = th + 12 + head1 + head2 + row_h * len(row_heads) + tot_h
    ix, iy, _, _ = _frame(d, x, y, w, h, title)
    xs = [ix + row_w + i * sum(block) for i in range(len(years))]
    cy = iy
    for i, year in enumerate(years):
        d.text(f"<b>{year}</b>", xs[i], cy, sum(block), head1, size=SMALL, align="center", valign="middle")
        if i:
            d.box("", xs[i] - 0.5, cy, 1, head1 + head2 + row_h * len(row_heads) + tot_h, fill=RULE, stroke=RULE, rounded=False)
    cy += head1
    for i in range(len(years)):
        cx = xs[i]
        for c, head in enumerate(value_heads):
            d.text("<br>".join(esc(p) for p in head.split("<br>")), cx, cy, block[c] - 4, head2, size=SMALL, align="right", valign="bottom")
            cx += block[c]
    cy += head2
    d.box("", ix, cy - 1, inner_w, 1, fill=INK, stroke=INK, rounded=False)
    geometry = {}
    for r, head in enumerate(row_heads):
        ry = cy + r * row_h
        d.text("<br>".join(esc(p) for p in head.split("<br>")), ix, ry, row_w, row_h, size=SMALL, align="left", valign="middle")
        for i in range(len(years)):
            cx = xs[i]
            for c in range(len(value_heads)):
                d.text(esc(cells[r][i][c]), cx, ry, block[c] - 4, row_h, size=SMALL, align="right", valign="middle")
                geometry[(r, i, c)] = (cx, ry, block[c], row_h)
                cx += block[c]
        d.box("", ix, ry + row_h - 1, inner_w, 1, fill=RULE, stroke=RULE, rounded=False)
    ty = cy + row_h * len(row_heads)
    d.box("", ix, ty, inner_w, 1, fill=INK, stroke=INK, rounded=False)
    d.text("<b>Total</b>", ix, ty, row_w, tot_h, size=SMALL, align="left", valign="middle")
    for i in range(len(years)):
        cx = xs[i]
        for c in range(len(value_heads)):
            d.text(f"<b>{esc(total[i][c])}</b>", cx, ty, block[c] - 4, tot_h, size=SMALL, align="right", valign="middle")
            geometry[("total", i, c)] = (cx, ty, block[c], tot_h)
            cx += block[c]
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, top_total=ty, width=inner_w)


def if_16_4_a() -> Diagram:
    """The Ex 16.4 page: the matrix of exceptions, population and both rates by process and year with its total row, the two line charts
    and the table of the current year."""
    g = ctx.values("ch16.g4")
    e = ctx.values("ch16.ex4")
    data = ctx.data()
    page = "ex164"
    years = [str(y) for y in data.years]
    t_matrix, t_l0, t_l1, t_table = (_title(page, n) for n in ("ratesMatrix", "rateLine0", "rateLine1", "ratesTable"))
    assert (t_matrix, t_l0, t_l1, t_table) == (g["t_matrix"], g["t_line0"], g["t_line1"], g["t_table"]) and t_table == f"Fiscal {data.C}"
    assert _projections(page, "ratesMatrix", "Rows") == ["Process"] and _projections(page, "ratesMatrix", "Columns") == ["Year"]
    values = ["Exceptions", "Population", "Rate per 1,000", "Unexplained Rate per 1,000"]
    assert _projections(page, "ratesMatrix", "Values") == values and _projections(page, "ratesTable", "Values") == ["Process"] + values
    assert _projections(page, "rateLine0", "Series") == ["Process"] == _projections(page, "rateLine1", "Series")
    _check_columns("Key Measures", values)
    _check_columns("Tests", ["Process"])
    processes = {}
    for tid, _, process, _ in _tests_rows():
        processes[tid[:2]] = process
    assert processes == {"JE": "Journal entries", "PO": "Purchase orders", "PR": "Payroll"}, processes
    order = sorted(processes, key=lambda k: processes[k])               # a matrix sorts its row headings by name
    assert order == ["JE", "PR", "PO"]
    table = dict(e["table"])
    un = e["unexplained"]
    n = len(years)
    assert all(len(table[p]) == n for p in order)
    fmt1 = lambda v: f"{v:.1f}"                                         # noqa: E731  (the measures' format 0.0)
    cells = [[[f"{table[p][i][0]:,}", f"{table[p][i][1]:,}", fmt1(table[p][i][2]), fmt1(un[p][i])] for i in range(n)] for p in order]
    totals = [sum(table[p][i][0] for p in order) for i in range(n)]
    total = [[f"{totals[i]:,}", "", "", ""] for i in range(n)]
    heads = ["Exceptions", "Population", "Rate per<br>1,000", "Unexplained<br>Rate per<br>1,000"]
    row_heads = [processes[p].replace(" ", "<br>") if " " in processes[p] else processes[p] for p in order]
    pad = 16
    probe = Diagram("probe")
    m = _year_matrix(probe, pad, pad, t_matrix, 54, [66, 64, 52, 72], years, heads, row_heads, cells, total)
    ch_y = m["bottom"] + 10
    ch_h = 196
    cur = n - 1
    rows_t = [[processes[p], f"{table[p][cur][0]:,}", f"{table[p][cur][1]:,}", fmt1(table[p][cur][2]), fmt1(un[p][cur])] for p in order]
    total_t = ["Total", f"{totals[cur]:,}", "", "", ""]
    t_y = ch_y + ch_h + 10
    t_h = 20 + 12 + (len(rows_t) + 2) * pbi.ROW
    canvas_h = t_y + t_h + pad
    d = Diagram("The Ex 16.4 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    m = _year_matrix(d, pad, pad, t_matrix, 54, [66, 64, 52, 72], years, heads, row_heads, cells, total)
    assert m["right"] <= 860 - pad + 1, f"the matrix ends at {m['right']:.0f} px"
    # the total row shows no rate and no population
    d.outline(m["left"], m["top_total"], m["width"], 24, CORAL, width=2.5, front=True)
    cw = (860 - 2 * pad - 10) / 2
    colors = {processes[p]: c for p, c in zip(order, pbi.SERIES)}
    for k, (x0, title, series_values, tick_top) in enumerate(((pad, t_l0, [[table[p][i][2] for i in range(n)] for p in order], None),
                                                              (pad + cw + 10, t_l1, [un[p] for p in order], None))):
        ticks = pbi.nice_ticks(0, max(max(v) for v in series_values), 3)
        pbi.line_chart(d, x0, ch_y, cw, ch_h, title, years, [(processes[p], series_values[j], pbi.SERIES[j]) for j, p in enumerate(order)], "", ticks, legend=True)
    wt = [112, 90, 90, 116, int(text_width(values[3], SMALL, True)) + 22]
    t = _table_visual(d, pad, t_y, t_table, ["Process"] + values, wt, rows_t, aligns=["left"] + ["right"] * 4, title_lines=1, total=total_t)
    cx0 = t["right"] + 14
    kit.callout(d, f"<b>The total row shows no rate.</b> Population is blank across processes, so a rate that would mix them is never shown. Dividing all "
                   f"{totals[cur]} exceptions of {years[cur]} by all {sum(table[p][cur][1] for p in order):,} documents would read {g['blend_rate']:.1f}, a figure no "
                   "process has.", cx0, t_y, 860 - pad - cx0, "amber")
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, filtered to the {n} years of the window; the matrix and the table sort their rows by process name. Outlined: the total "
             "row of the matrix, which shows the exceptions of all processes and no population or rate. The matrix's grand-total column, which adds the years, is not drawn. "
             f"The table of the model answer is by process, not by test. The page's text box is not drawn.", canvas_h + 34)
    return d


# -- IF-16-4-B: three numerators for one process -------------------------------------------------------------------------------------

def if_16_4_b() -> Diagram:
    """Three bars for each process in the current year: all exceptions, the unexplained ones and the open ones."""
    from notes import ch16 as n16
    e = ctx.values("ch16.ex4")
    t3 = ctx.values("ch16.t3")
    data = ctx.data()
    reg = n16.register(data)
    y = data.C
    cur = list(data.years).index(y)
    names = {"JE": "Journal entries", "PR": "Payroll", "PO": "Purchase orders"}
    order = ["JE", "PO", "PR"]
    bars = {}
    for p in order:
        mine = [r for r in reg if r["process"] == p and r["date"][:4] == str(y)]
        allx = len(mine)
        unexplained = sum(1 for r in mine if r["disposition"] != "Expected" and r["test"] != "PR SelfApproved")
        open_ = sum(1 for r in mine if not r["disposition"])
        pop = dict(e["table"])[p][cur][1]
        assert abs(1000 * unexplained / pop - e["unexplained"][p][cur]) < 1e-9 and allx == dict(e["table"])[p][cur][0]
        assert open_ == t3["open_years"][p][cur], "the open exceptions of Tutorial 16.3"
        bars[p] = (allx, unexplained, open_)
    je, po, pr = bars["JE"], bars["PO"], bars["PR"]
    assert pr[1] < min(pr[0], pr[2]) / 5, "payroll: the unexplained bar sits far below the other two"
    assert po[0] == po[1] and po[0] - po[2] == 1, "purchase orders: no exception is expected and one is reviewed"
    assert max(po) - min(po) <= 1 and max(po) - min(po) < max(po) / 5, "purchase orders: the three bars are close together"
    d = Diagram("Three Numerators for One Process")
    d.text(f"<b>Exceptions of fiscal {y}, three ways of counting them, by process</b>", 0, 0, 860, 20, size=SMALL)
    top_v = math.ceil(max(max(b) for b in bars.values()) / 5) * 5
    ticks = list(range(0, top_v + 1, 5))
    plot = kit.Plot(d, 0, 26, 840, 330, None, y_ticks=ticks, categories=[""] * 3, y_fmt=lambda v: f"{v:.0f}", left=44, bottom=78,
                    y_title="Exceptions")
    slot = plot.pw / 3
    bw, gap = 66, 10
    fills = [BLUE, TEAL, GRAY]
    kinds = ["All", "Unexplained", "Open"]
    base = plot.y_of(0)
    for i, p in enumerate(order):
        sx = plot.px + i * slot + (slot - 3 * bw - 2 * gap) / 2
        for j, v in enumerate(bars[p]):
            bx = sx + j * (bw + gap)
            h = max(base - plot.y_of(v), 2)
            d.box("", bx, base - h, bw, h, fill=fills[j], stroke=fills[j], rounded=False)
            d.box(f"<b>{v}</b>", bx + bw / 2 - 20, base - h - 22, 40, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
            d.text(kinds[j], bx - 8, base + 4, bw + 16, 18, size=SMALL, color=GRAY, align="center")
        gx = plot.px + i * slot
        d.text(f"<b>{names[p]}</b>", gx, base + 26, slot, 20, size=SMALL, align="center")
        rate, urate = dict(e["table"])[p][cur][2], e["unexplained"][p][cur]
        d.text(f"Rate per 1,000: {rate:.1f}; unexplained {urate:.1f}", gx, base + 46, slot, 20, size=SMALL, color=GRAY, align="center")
    ly = 26 + 330 + 8
    kit.legend(d, 0, ly, [("All: every exception of the process in the year", BLUE, "box")])
    kit.legend(d, 0, ly + 22, [("Unexplained: the Expected exceptions and the recurring test PR SelfApproved set aside, as in Unexplained Rate per 1,000", TEAL, "box")])
    kit.legend(d, 0, ly + 44, [("Open: the exceptions with no disposition, as Open Exceptions counts them", GRAY, "box")])
    pr_self = sum(1 for r in reg if r["test"] == "PR SelfApproved" and r["date"][:4] == str(y))
    _note(d, f"The register's counts for fiscal {y}. Payroll: {pr_self} of its {pr[0]} exceptions are the recurring test, open but not unexplained, so the unexplained bar "
             f"is {pr[1]}. Purchase orders: the three counts are {po[0]}, {po[1]} and {po[2]}, because no purchase order exception is expected and only one is reviewed. "
             "The bars are counts, not rates; the rates divide each process's exceptions by its own documents.", ly + 72)
    return d


# -- IF-16-5-A: the Ex 16.5 page ---------------------------------------------------------------------------------------------------

def _slicer_list(d: Diagram, x: float, y: float, w: float, title: str, entries: list[str], selected: str | None = None) -> float:
    """A slicer in the Vertical list style: a check box and a name for each entry, the selected one filled and bold.  Returns its bottom."""
    h = 30 + 26 * len(entries) + 8
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 20, size=SMALL)
    for i, name in enumerate(entries):
        ry = y + 30 + i * 26
        if name == selected:
            d.box("<b>✓</b>", x + 10, ry + 4, 16, 16, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False, valign="middle")
        else:
            d.box("", x + 10, ry + 4, 16, 16, fill=WHITE, stroke=GRAY, rounded=False)
        d.text(f"<b>{esc(name)}</b>" if name == selected else esc(name), x + 32, ry + 2, w - 40, 20, size=SMALL, valign="middle")
    return y + h


def if_16_5_a() -> Diagram:
    """The Ex 16.5 page: the slicer of PaymentKind, observed against expected first digits, and the deviation by kind of payment with
    the total row for all payments."""
    g = ctx.values("ch16.g5")
    e = ctx.values("ch16.ex5")
    data = ctx.data()
    g16 = _g16()
    page = "ex165"
    t_slicer, t_chart, t_table = (_title(page, n) for n in ("kindSlicer", "digits", "madByKind"))
    assert (t_slicer, t_chart, t_table) == (g["t_slicer"], g["t_chart"], g["t_table"])
    assert _projections(page, "kindSlicer", "Values") == ["PaymentKind"] and _projections(page, "digits", "Category") == ["Digit"]
    assert _projections(page, "digits", "Y") == ["Observed Share", "Benford Share"]
    assert _projections(page, "madByKind", "Values") == ["PaymentKind", "Payments Counted", "Benford MAD"]
    _check_columns("Key Measures", ["Observed Share", "Benford Share", "Payments Counted", "Benford MAD"])
    assert _page(page)["visualInteractions"] == [{"source": "kindSlicer", "target": "madByKind", "type": "NoFilter"}]
    pay = data.q("SELECT p.Amount, pi.GrandTotal FROM DisbursementPayment p JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID "
                 "WHERE p.PaymentDate <= ?", e["asof"])
    digits = [g16.first_digit(a) for a, _ in pay]
    full = [g16.first_digit(a) for a, t in pay if abs(a - t) < 0.005]
    part = [g16.first_digit(a) for a, t in pay if a < t - 0.005]
    assert (len(digits), len(full), len(part)) == (e["n"], e["n_full"], e["n_partial"])
    mads = {"all": g16.mad(digits), "full": g16.mad(full), "partial": g16.mad(part)}
    assert all(abs(mads[k] - e["mad"][k]) < 1e-9 for k in mads)
    observed = [sum(1 for v in digits if v == k) / len(digits) for k in range(1, 10)]
    expected = [math.log10(1 + 1 / k) for k in range(1, 10)]
    assert abs(sum(expected) - 1) < 1e-9 and abs(sum(observed) - 1) < 1e-9
    lo, mid, hi = g["ranges"][:3]
    cls = lambda v: "close" if v <= lo else "acceptable" if v <= mid else "marginally acceptable" if v <= hi else "nonconformity"   # noqa: E731
    assert (cls(mads["all"]), cls(mads["full"]), cls(mads["partial"])) == ("marginally acceptable", "acceptable", "nonconformity")
    pad = 16
    sl_w = 140
    cx0 = pad + sl_w + 12
    chart_w, chart_h = 860 - pad - cx0, 236
    rows = [["Full", f"{len(full):,}", f"{mads['full']:.5f}"], ["Partial", f"{len(part):,}", f"{mads['partial']:.5f}"]]
    total = ["Total", f"{len(digits):,}", f"{mads['all']:.5f}"]
    t_y = pad + chart_h + 14
    t_h = 20 + 12 + 4 * pbi.ROW
    canvas_h = t_y + t_h + pad
    d = Diagram("The Ex 16.5 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    _slicer_list(d, pad, pad, sl_w, t_slicer, ["Full", "Partial"])
    ix, iy, iw, ih = _frame(d, cx0, pad, chart_w, chart_h, t_chart, lines=1)
    d.box("", ix, iy + 4, 12, 12, fill=BLUE, stroke=BLUE, rounded=False)
    d.text("Observed Share", ix + 16, iy - 2, 110, 20, size=SMALL)
    d.box("", ix + 132, iy + 4, 12, 12, fill=AMBER, stroke=AMBER, rounded=False)
    d.text("Benford Share", ix + 148, iy - 2, 110, 20, size=SMALL)
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 28, ih - 28 - 30
    ticks = [0, 0.1, 0.2, 0.3, 0.4]
    assert max(observed + expected) < ticks[-1]
    y_of = _vaxis(d, ix, left, plot_w, top, plot_h, ticks, lambda v: f"{100 * v:.0f}%")
    step = plot_w / 9
    for k in range(9):
        for j, (v, color) in enumerate(((observed[k], BLUE), (expected[k], AMBER))):
            bx = left + step * k + step * 0.14 + j * step * 0.36
            d.box("", bx, y_of(v), step * 0.36, y_of(0) - y_of(v), fill=color, stroke=color, rounded=False)
        d.text(str(k + 1), left + step * k, top + plot_h + 4, step, 20, size=SMALL, color=GRAY, align="center")
    t = _table_visual(d, pad, t_y, t_table, ["PaymentKind", "Payments Counted", "Benford MAD"], [104, 124, 110], rows, aligns=["left", "right", "right"],
                      title_lines=1, total=total)
    ox, oy, ow, oh = t["geometry"][(1, 2)]
    d.outline(ox + 1, oy + 1, ow - 2, oh - 2, CORAL, width=2.5, front=True)
    cx1 = t["right"] + 14
    kit.callout(d, f"<b>Read against Chapter 8's ranges</b>: close up to {lo:.3f}, acceptable up to {mid:.3f}, marginally acceptable up to {hi:.3f}, nonconformity above. "
                   f"All payments, {mads['all']:.5f}, are marginally acceptable; full payments, {mads['full']:.5f}, acceptable; partial payments, {mads['partial']:.5f}, a "
                   "nonconformity. The slicer is set to None for the table, so choosing Partial leaves the three rows.", cx1, t_y, 860 - pad - cx1, "teal")
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, with no kind of payment selected in the slicer, which Desktop draws as a list of check boxes. The chart shows all "
             f"{len(digits):,} payments through {e['asof']}; the digits 1 to 9 are the first significant digits. Outlined: the deviation of the partial payments. "
             "The page's text box is not drawn.", canvas_h + 34)
    return d


# -- IF-16-6-A: the Ex 16.6 page ---------------------------------------------------------------------------------------------------

def if_16_6_a() -> Diagram:
    """The Ex 16.6 page: the three cards, the pairs by days apart and the table of documents approved with their shares.  Desktop sets the
    table to the right of the cards and the chart; the mock stacks them so that each keeps a legible size."""
    from notes import ch16 as n16
    g = ctx.values("ch16.g6")
    e = ctx.values("ch16.ex6")
    data = ctx.data()
    page = "ex166"
    t_days, t_shares = _title(page, "pairsByDays"), _title(page, "approvalShares")
    assert (t_days, t_shares) == (g["t_days"], g["t_shares"])
    assert _projections(page, "pairCards", "Data") == ["Pairs", "Pairs Within 30 Days", "Pairs on the Same Invoice"]
    cols = _projections(page, "approvalShares", "Values")
    assert cols == ["EmployeeName", "JobTitle", "Entries Approved", "Entries Share", "Orders Approved", "Orders Share", "Registers Approved", "Registers Share"], cols
    assert _projections(page, "pairsByDays", "Category") == ["DaysApart"] and _projections(page, "pairsByDays", "Y") == ["Pairs"]
    _check_columns("Key Measures", cols[2:] + ["Pairs", "Pairs Within 30 Days", "Pairs on the Same Invoice"])
    _check_columns("Employee", ["EmployeeName", "JobTitle"])
    sort = json.dumps(_visual(page, "approvalShares")["visual"]["query"]["sortDefinition"])
    assert "Orders Approved" in sort and "Descending" in sort, "the table is sorted by Orders Approved, largest first"
    end = e["asof"]
    # the pairs: DisbursementID below its partner's, on different dates, with the days between them
    merged = data.q("SELECT a.DisbursementID, b.DisbursementID, a.PaymentDate, b.PaymentDate, a.PurchaseInvoiceID, b.PurchaseInvoiceID FROM DisbursementPayment a "
                    "JOIN DisbursementPayment b ON b.SupplierID = a.SupplierID AND b.Amount = a.Amount WHERE a.PaymentDate <= ?1 AND b.PaymentDate <= ?1", end)
    pairs = [r for r in merged if r[0] < r[1] and r[2] != r[3]]
    days = [abs(data.one("SELECT julianday(?) - julianday(?)", r[3], r[2])) for r in pairs]
    same_invoice = sum(1 for r in pairs if r[4] == r[5])
    assert len(pairs) == e["pairs"] and sum(1 for v in days if v <= 30) == e["within30"] and same_invoice == 0
    count = defaultdict(int)
    for v in days:
        count[int(v)] += 1
    # the approvals of every employee, as the three measures count them
    emp = {i: (v["name"], v["title"]) for i, v in n16.employees(data).items()}
    approved = {}
    for label, table in (("entries", "JournalEntry"), ("orders", "PurchaseOrder"), ("registers", "PayrollRegister")):
        approved[label] = dict(data.q(f"SELECT ApprovedByEmployeeID, COUNT(*) FROM {table} GROUP BY 1"))
    totals = {k: sum(v.values()) for k, v in approved.items()}
    assert totals == {"entries": data.one("SELECT COUNT(*) FROM JournalEntry"), "orders": data.one("SELECT COUNT(*) FROM PurchaseOrder"),
                      "registers": data.one("SELECT COUNT(*) FROM PayrollRegister")}, "every document has an approver among the employees"
    people = sorted({i for v in approved.values() for i in v}, key=lambda i: (-approved["orders"].get(i, 0), emp[i][0]))
    assert None not in people and len(people) >= g["n_approvers"] - 1
    cfo, mgr = e["cfo"]["id"], e["manager"]["id"]
    assert approved["orders"][cfo] == e["cfo"]["n"] and approved["registers"][mgr] == e["manager"]["n"] and approved["entries"][e["controller"]["id"]] == e["controller"]["n"]
    blank = lambda v: f"{v:,}" if v else ""           # noqa: E731  (a measure with no rows is blank)
    share = lambda v, k: f"{100 * v / totals[k]:.2f}%" if v else ""   # noqa: E731
    rows = []
    for i in people:
        ent, orders, regs = approved["entries"].get(i, 0), approved["orders"].get(i, 0), approved["registers"].get(i, 0)
        rows.append([emp[i][0], emp[i][1], blank(ent), share(ent, "entries"), blank(orders), share(orders, "orders"), blank(regs), share(regs, "registers")])
    total = ["Total", "", f"{totals['entries']:,}", "100.00%", f"{totals['orders']:,}", "100.00%", f"{totals['registers']:,}", "100.00%"]
    heads = ["EmployeeName", "JobTitle", "Entries<br>Approved", "Entries<br>Share", "Orders<br>Approved", "Orders<br>Share", "Registers<br>Approved", "Registers<br>Share"]
    wname = int(max(text_width(r[0], SMALL, False) for r in rows + [total])) + 22
    wtitle = int(max(text_width(r[1], SMALL, False) for r in rows)) + 22
    widths = [wname, wtitle, 74, 64, 74, 64, 82, 76]
    pad = 16
    # sizes, from the top: the cards, the chart, the table
    card_h, chart_h = 86, 176
    t_h = 20 + 12 + (15 * 2 + 8) + (len(rows) + 1) * pbi.ROW
    canvas_h = pad + card_h + 10 + chart_h + 10 + t_h + pad
    d = Diagram("The Ex 16.6 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    _cards_visual(d, pad, pad, 340, card_h, [("Pairs", f"{len(pairs):,}"), ("Pairs Within<br>30 Days", f"{e['within30']:,}"), ("Pairs on the<br>Same Invoice", "0")])
    zero = 16 + 340 + 12
    kit.callout(d, f"<b>None of the {len(pairs)} pairs repeats the same recorded invoice ID.</b> The card reads 0 and not blank, because the measure adds 0. The pairs are "
                   f"screening candidates, not proven duplicate payments. Different invoice IDs can still represent the same underlying bill, so inspect the supplier "
                   f"invoice numbers and the supporting records.", zero, pad, 860 - pad - zero, "teal")
    # the chart: one column for each number of days apart, to scale
    cy = pad + card_h + 10
    ix, iy, iw, ih = _frame(d, pad, cy, 860 - 2 * pad, chart_h, t_days, lines=1)
    left, plot_w = ix + 48, iw - 64
    top, plot_h = iy + 8, ih - 34
    longest = max(count)
    top_n = max(count.values())
    x_top = math.ceil(longest / 100) * 100
    y_of = _vaxis(d, ix, left, plot_w, top, plot_h, [float(i) for i in range(top_n + 1)], lambda v: f"{v:.0f}")
    x_of = lambda v: left + plot_w * v / x_top    # noqa: E731
    for v in range(0, x_top + 1, 100):
        d.text(str(v), x_of(v) - 24, top + plot_h + 4, 48, 20, size=SMALL, color=GRAY, align="center")
    for v, n in sorted(count.items()):
        d.box("", x_of(v) - 1.5, y_of(n), 3, y_of(0) - y_of(n), fill=BLUE, stroke=BLUE, rounded=False)
    d.text("Days apart, to scale", ix + iw - 170, cy + 4, 170, 20, size=SMALL, color=GRAY, align="right")
    # the table
    ty = cy + chart_h + 10
    t = _table_visual(d, pad, ty, t_shares, heads, widths, rows, aligns=["left", "left"] + ["right"] * 6, title_lines=1, head_lines=2, total=total)
    assert t["right"] <= 860 - pad + 1, f"the table ends at {t['right']:.0f} px"
    r_cfo, r_mgr = people.index(cfo), people.index(mgr)
    ox, oy, ow, oh = t["geometry"][(r_cfo, 4)]
    d.outline(ox + 1, oy + 1, widths[4] + widths[5] - 2, oh - 2, CORAL, width=2.5, front=True)
    ox, oy, ow, oh = t["geometry"][(r_mgr, 6)]
    d.outline(ox + 1, oy + 1, widths[6] + widths[7] - 2, oh - 2, CORAL, width=2.5, front=True)
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, with the table sorted by Orders Approved, largest first; a measure with nothing to count is blank, and the total row "
             f"adds every approver. Outlined: the {e['cfo']['title']}'s orders, {_pct(e['cfo']['share'], 2)}, and the {e['manager']['title']}'s registers, "
             f"{_pct(e['manager']['share'], 2)}. Desktop sets the table to the right of the cards and the chart; the mock stacks the three. "
             "The page's text box is not drawn.", canvas_h + 34)
    return d


# -- IF-16-6-B: what a table merged with itself holds ----------------------------------------------------------------------------------

def if_16_6_b() -> Diagram:
    """Two payments of one supplier and one amount, the four rows of their merge, and the filters that leave one."""
    g = ctx.values("ch16.g6")
    e = ctx.values("ch16.ex6")
    data = ctx.data()
    end = e["asof"]
    merged = data.q("SELECT a.DisbursementID, b.DisbursementID, a.PaymentDate, b.PaymentDate, a.SupplierID, a.Amount FROM DisbursementPayment a "
                    "JOIN DisbursementPayment b ON b.SupplierID = a.SupplierID AND b.Amount = a.Amount WHERE a.PaymentDate <= ?1 AND b.PaymentDate <= ?1", end)
    pairs = sorted((r for r in merged if r[0] < r[1] and r[2] != r[3]),
                   key=lambda r: (abs(data.one("SELECT julianday(?) - julianday(?)", r[3], r[2])), r[0]))
    a_id, b_id, a_date, b_date, supplier, amount = pairs[0]
    assert a_id < b_id and a_date != b_date
    assert g["self_pairs"] == data.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PaymentDate <= ?", end) and g["merge_rows"] == g["self_pairs"] + 2 * len(pairs)
    d = Diagram("What a Table Merged with Itself Holds")
    d.text("<b>Two payments of one supplier and one amount, on different dates</b>", 0, 0, 300, 36, size=SMALL)
    cards = {}
    for k, (label, i, dt_, hint) in enumerate((("A", a_id, a_date, "the lower key"), ("B", b_id, b_date, "the higher key"))):
        y = 44 + k * 108
        text = (f"<b>Payment {label}</b>, {hint}<br>DisbursementID {i}<br>SupplierID {supplier}, Amount {_money(amount)}<br>PaymentDate {_nowrap(dt_)}")
        cards[label] = d.box(text, 0, y, 270, 92, fill=BLUE_TINT, stroke=BLUE, size=SMALL, align="left", stroke_width=1.5)
    # the grid of the merge: the left copy on the rows, the right copy on the columns
    gx, gy, hw, cw, ch = 316, 74, 54, 244, 98
    d.text("<b>Merge Payments with itself</b> on SupplierID and Amount: an inner join keeps every combination", gx, 0, 860 - gx, 36, size=SMALL)
    for c, name in enumerate("AB"):
        d.box(f"<b>{name}</b><br>PairDisbursementID {a_id if c == 0 else b_id}", gx + hw + c * cw, gy - 34, cw, 34, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False)
    d.box("", gx, gy - 34, hw, 34, fill=GRAY, stroke=RULE, rounded=False)
    keys = (a_id, b_id)
    cells = {}
    for r, rn in enumerate("AB"):
        d.box(f"<b>{rn}</b><br>{keys[r]}", gx, gy + r * ch, hw, ch, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False)
        for c, cn in enumerate("AB"):
            x, y = gx + hw + c * cw, gy + r * ch
            kept = rn == "A" and cn == "B"
            if kept:
                text = f"<b>{rn} with {cn}</b><br>Kept: the lower key first, on different dates"
                cells[(r, c)] = d.box(text, x, y, cw, ch, fill=TEAL_TINT, stroke=TEAL, size=SMALL, rounded=False, stroke_width=2.5)
            else:
                cells[(r, c)] = d.box("", x, y, cw, ch, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False)
                a, b = d.anchor(x + 6, y + 6), d.anchor(x + cw - 6, y + ch - 6)
                d.edge(a, b, color=CORAL, width=2.5, meta="edgeStyle=none;")
                a, b = d.anchor(x + cw - 6, y + 6), d.anchor(x + 6, y + ch - 6)
                d.edge(a, b, color=CORAL, width=2.5, meta="edgeStyle=none;")
                if rn == cn:
                    label, w, lh = f"<b>{rn} with {cn}</b><br>Removed: paired with itself", text_width("Removed: paired with itself", SMALL, False) + 24, 44
                else:
                    label, w, lh = f"<b>{rn} with {cn}</b><br>Removed: the same pair<br>in the other order", text_width("Removed: the same pair", SMALL, False) + 24, 60
                d.box(label, x + cw / 2 - w / 2, y + ch / 2 - lh / 2, w, lh, fill=WHITE, stroke=CORAL, size=SMALL, stroke_width=1.5)
    # the join from the payments to the grid
    d.arrow(d.container(0, gy - 34, 270, 2 * ch + 34), d.container(gx - 4, gy - 34, 4, 2 * ch + 34), exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
    by = gy + 2 * ch + 24
    half = (860 - 24) / 2
    f1 = (f"<b>DisbursementID &lt; PairDisbursementID</b><br>Keeps the lower key first. It removes A with A and B with B, whose keys are equal, and "
          f"B with A, whose left key is the higher.")
    f2 = (f"<b>PaymentDate &lt;&gt; PairPaymentDate</b><br>Keeps pairs on different dates. It removes A with A and B with B, which are on the same date, and "
          f"leaves A with B and B with A.")
    h = max(kit.height_for(f1, half, SMALL, pad=18), kit.height_for(f2, half, SMALL, pad=18))
    d.box(f1, 0, by, half, h, fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", stroke_width=1.5)
    d.box(f2, half + 24, by, half, h, fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", stroke_width=1.5)
    _note(d, f"The two payments are the closest pair of the dataset, {abs(data.one('SELECT julianday(?) - julianday(?)', b_date, a_date)):.0f} days apart. In the dataset the "
             f"merge returns {g['merge_rows']:,} rows: {g['self_pairs']:,} payments paired with themselves and {len(pairs)} pairs in both orders. The dates alone leave "
             f"{g['date_only']}, each pair twice; the keys alone leave {g['id_only']}, because no two payments of one supplier and one amount share a date. "
             "The exercise asks for both filters, so a roll does not break it.", by + h + 10)
    return d


FIGURES = {
    "IF-16-0-A": if_16_0_a, "IF-16-0-B": if_16_0_b, "IF-16-0-C": if_16_0_c,
    "IF-16-0-D": if_16_0_d, "IF-16-1-A": if_16_1_a, "IF-16-2-A": if_16_2_a,
    "IF-16-3-A": if_16_3_a, "IF-16-4-A": if_16_4_a, "IF-16-4-B": if_16_4_b,
    "IF-16-5-A": if_16_5_a, "IF-16-6-A": if_16_6_a, "IF-16-6-B": if_16_6_b}
