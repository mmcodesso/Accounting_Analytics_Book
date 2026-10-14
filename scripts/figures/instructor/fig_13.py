"""Instructor figures of Chapter 13 (guides in facts/instructor/guides/chapter-13-power-bi-essentials/).

Chapter 13 is the first Power BI unit.  Its mocks draw the pages and the model of the model answer
(outputs/companion/solutions/Chapter13-exercises-pbi, a PBIP of TMDL and PBIR text), so the names, the titles, the
columns, the relationships and the Checks tab are read from that project, and every value comes from the dataset
through the guides' own contexts (ch13.ex1 to ch13.ex6, ch13.g1 to ch13.g6) or the notes' helpers.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from functools import lru_cache

import ctx
import excel as xl
import kit
import powerbi as pbi
from check_figures import text_width
from drawio import (AMBER, BLUE, BLUE_TINT, CORAL, FONT, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc)

FILE = "Chapter 13 Exercises - Solutions"
PROJECT = ctx.REPO / "outputs" / "companion" / "solutions" / "Chapter13-exercises-pbi" / FILE
MODEL = PROJECT / f"{FILE}.SemanticModel"
REPORT = PROJECT / f"{FILE}.Report" / "definition"
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December"]


# -- the model answer (a PBIP of text files) ----------------------------------------------------------------------------

def _tmdl(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def _g13():
    """guide_contexts.ch13: the helpers that read the project's M (table_m, expression_m)."""
    from guide_contexts import ch13
    return ch13


def _model_columns(table: str) -> list[str]:
    return re.findall(r"^\tcolumn (\w+)\s*$", _tmdl(f"tables/{table}.tmdl"), re.M)


def _relationships() -> list[tuple[tuple[str, str], tuple[str, str]]]:
    """(many side, one side) of each relationship of the project, each as (table, column)."""
    out = []
    for block in _tmdl("relationships.tmdl").split("relationship ")[1:]:
        (ft, fc), (tt, tc) = re.findall(r"(?:fromColumn|toColumn): (\w+)\.(\w+)", block)
        out.append(((ft, fc), (tt, tc)))
    return out


def _query_order() -> list[str]:
    return json.loads(re.search(r"PBI_QueryOrder = (\[.*\])", _tmdl("model.tmdl")).group(1))


def _workbook_table(query: str) -> str:
    """The workbook Table a query reads (T16_SalesInvoice), from its M in the project."""
    g = _g13()
    lines = g.expression_m(query) if query.startswith("Profile_") else g.table_m(query)
    return re.search(r'Item="(T\d+_\w+)"', "\n".join(lines)).group(1)


def _loaded_tables() -> set[str]:
    return {p.stem for p in (MODEL / "definition" / "tables").glob("*.tmdl")}


def _visual(page: str, name: str) -> dict:
    return json.loads((REPORT / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))


def _title(page: str, name: str) -> str:
    """The title the model answer gives a visual."""
    value = _visual(page, name)["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
    return value.strip("'")


def _exercise_titles() -> dict[str, str]:
    text = (ctx.REPO / "chapters" / "13-power-bi-essentials" / "_exercises.qmd").read_text(encoding="utf-8")
    return dict(re.findall(r"^\*\*Exercise (13\.\d): (.+?)\*\*$", text, re.M))


# -- the data ----------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _lines() -> list[dict]:
    """Every invoice line with its invoice, item and customer (the notes' own helper, Tutorial 13.1's model)."""
    from notes import ch13 as n13
    return n13.lines(ctx.data())


def _year_lines(year: int | None = None) -> list[dict]:
    year = year or ctx.data().C
    return [r for r in _lines() if r["year"] == year]


def _money(x: float) -> str:
    return pbi.amount(x)


def _mdy(iso: str) -> str:
    """An ISO date as a Short Date reads in the model (en-US): 3/1/2026."""
    return f"{int(iso[5:7])}/{int(iso[8:10])}/{iso[:4]}"


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


def _tabs(active: str, names: list[str], d: Diagram, y: float) -> None:
    pbi.page_tabs(d, 4, y, names, active)


# -- a visual container with a title of one or two lines ---------------------------------------------------------------

def _frame(d: Diagram, x: float, y: float, w: float, h: float, title: str | None, selected: bool = False,
           color: str | None = None, lines: int | None = None) -> tuple[float, float, float, float]:
    """A visual's container.  The title may take two lines, as a long title does in Power BI.  Returns the inner area."""
    d.box("", x, y, w, h, fill=WHITE, stroke=color or (BLUE if selected else RULE), stroke_width=2 if (selected or color) else 1,
          rounded=False)
    if not title:
        return x + 6, y + 6, w - 12, h - 12
    label = f"<b>{esc(title)}</b>"
    lines = lines or kit.lines_for(label, w - 12, SMALL, bold=True)
    th = 16 * lines + 4
    d.text(label, x + 6, y + 4, w - 12, th, size=SMALL)
    return x + 6, y + 4 + th + 2, w - 12, h - th - 12


def _grid_line(d: Diagram, x: float, y: float, w: float, h: float) -> None:
    """A one-pixel gridline (a box with a stroke would draw two)."""
    d.vertex("", f"rounded=0;html=1;fillColor={RULE};strokeColor=none;", x, y, w, h)


def _axis(d: Diagram, label_x: float, grid_x: float, grid_w: float, top: float, plot_h: float, ticks: list[float],
          unit: str, align: str = "right") -> callable:
    low, high = ticks[0], ticks[-1]
    y_of = lambda v: top + (high - v) * plot_h / (high - low)
    for t in ticks:
        if grid_w:
            _grid_line(d, grid_x, y_of(t), grid_w, 1)
        d.text(pbi.units(t, unit), label_x, y_of(t) - 10, 44, 20, size=SMALL, color=GRAY, align=align, valign="middle")
    return y_of


def _unit_label(value: float, unit: str) -> str:
    """A data label with Display units on Auto: 17.40M, 362.11K."""
    if unit == "M":
        return f"{value / 1e6:.2f}M"
    if unit == "K":
        return f"{value / 1e3:.2f}K"
    return f"{value:,.0f}"


def _hbars(d: Diagram, x: float, y: float, w: float, h: float, title: str | None, cats: list[str], values: list[float],
           unit: str, selected: str | None = None, label_w: float = 100) -> dict:
    """A clustered bar chart sorted as given, with data labels.  With selected, the other bars fade, as a click
    on one bar fades the rest.  Returns the geometry of each bar."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title)
    left, top = ix + label_w, iy + 4
    top_value = pbi.nice_ticks(0, max(values), 4)[-1]
    plot_w = iw - label_w - 52
    x_of = lambda v: left + v * plot_w / top_value
    slot = (ih - 30) / len(cats)
    geometry = {}
    ticks = pbi.nice_ticks(0, max(values), 4)
    for t in ticks:
        _grid_line(d, x_of(t), top, 1, ih - 30)
        d.text(pbi.units(t, unit), min(x_of(t) - 24, 860 - 48), top + ih - 28, 48, 20, size=SMALL, color=GRAY, align="center")
    for i, (name, v) in enumerate(zip(cats, values)):
        by = top + slot * i + slot * 0.18
        on = selected in (None, name)
        d.text(esc(name), ix, by - 3, label_w - 6, slot * 0.64 + 6, size=SMALL, align="right", valign="middle")
        bw = max(x_of(v) - left, 1)
        d.box("", left, by, bw, slot * 0.64, fill=BLUE if on else BLUE_TINT, stroke=BLUE if on else RULE, rounded=False)
        lw = text_width(_unit_label(v, unit), SMALL, False) + 16
        d.box(_unit_label(v, unit), left + bw + 3, by + slot * 0.32 - 9, lw, 18, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False,
              color=INK if on else GRAY)
        geometry[name] = (left, by, bw, slot * 0.64)
    return geometry


def _columns(d: Diagram, x: float, y: float, w: float, h: float, title: str | None, cats: list[str], values: list[float],
             unit: str, ticks: list[float], labels: bool = True) -> dict:
    """A clustered column chart of one series with data labels."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title)
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 22, ih - 22 - 24
    y_of = _axis(d, ix, left, plot_w, top, plot_h, ticks, unit)
    step = plot_w / len(cats)
    xs = []
    for i, v in enumerate(values):
        cx = left + step * i + step * 0.22
        xs.append(cx + step * 0.28)
        d.box("", cx, y_of(v), step * 0.56, y_of(ticks[0]) - y_of(v), fill=BLUE, stroke=BLUE, rounded=False)
        if labels:
            d.text(_unit_label(v, unit), cx - 14, y_of(v) - 20, step * 0.56 + 28, 20, size=SMALL, align="center")
        d.text(esc(cats[i]), cx - 10, top + plot_h + 3, step * 0.56 + 20, 20, size=SMALL, color=GRAY, align="center")
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of)


def _lines_chart(d: Diagram, x: float, y: float, w: float, h: float, title: str | None, cats: list[str],
                 series: list[tuple[str, list[float], str]], unit: str, ticks: list[float], every: int = 1,
                 legend: bool = False) -> dict:
    """A line chart; the first tick is where the value axis starts."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title)
    if legend:
        lx = ix
        for name, _, color in series:
            d.box("", lx, iy + 6, 14, 3, fill=color, stroke=color, rounded=False)
            nw = text_width(esc(name), SMALL, False) + 8
            d.text(esc(name), lx + 18, iy - 2, nw, 20, size=SMALL)
            lx += nw + 34
        iy += 20
        ih -= 20
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 8, ih - 34
    y_of = _axis(d, ix, left, plot_w, top, plot_h, ticks, unit)
    step = plot_w / len(cats)
    xs = [left + step * (i + 0.5) for i in range(len(cats))]
    for name, values, color in series:
        anchors = [d.anchor(cx, y_of(v)) for cx, v in zip(xs, values)]
        for a, b in zip(anchors, anchors[1:]):
            d.edge(a, b, color=color, width=2.5, meta="edgeStyle=none;")
    for i, (cx, label) in enumerate(zip(xs, cats)):
        if i % every == 0:
            d.text(esc(label), cx - step * every / 2, top + plot_h + 4, step * every, 20, size=SMALL, color=GRAY, align="center")
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of, axis_box=(ix, top - 10, 46, plot_h + 20))


# -- IF-13-0-A: the build sequence of the chapter --------------------------------------------------------------------------

# Where each exercise builds on a tutorial (the exercises' own text and the chapter note's list of outcomes) and what it
# adds to the model answer.  The queries and the pages are checked against the project below.
BUILDS_ON = {"13.1": "Tutorial 13.1, Steps 3 and 10", "13.2": "Tutorials 13.1 (Step 9) and 13.2", "13.3": "Tutorial 13.1, Steps 3 and 8",
             "13.4": "Tutorial 13.2", "13.5": "Tutorial 13.1, Steps 3 and 6", "13.6": "Tutorial 13.3"}


def if_13_0_a() -> Diagram:
    """The tutorials' path from the Tables to the three pages, and the six exercise pages branching from the model."""
    d = Diagram("The Build Sequence of Chapter 13")
    order = _query_order()
    base = [q for q in order if q in ("Customer", "SalesInvoice", "SalesInvoiceLine", "Item")]
    assert base == ["Customer", "SalesInvoice", "SalesInvoiceLine", "Item"]
    tables = [_workbook_table(q) for q in base]
    loaded = _loaded_tables()
    assert {"InvoiceHeaders", "PromotionProgram"} <= loaded, "the exercise queries load"
    profiles = [q for q in order if q.startswith("Profile_")]
    assert len(profiles) == 4 and not set(profiles) & loaded, "the four Profile queries do not load"
    rels = _relationships()
    assert len([r for r in rels if "PromotionProgram" not in (r[0][0], r[1][0])]) == 3, "three relationships after the tutorials"
    assert any(r[1][0] == "PromotionProgram" for r in rels), "Exercise 13.3 adds a fourth"
    assert "InvoiceHeaders" not in _tmdl("relationships.tmdl")
    titles = _exercise_titles()
    assert len(titles) == 6
    pages = {p: json.loads((REPORT / "pages" / p / "page.json").read_text(encoding="utf-8"))["displayName"]
             for p in ("validation", "salesDiscounts", "review")}
    # the main path, left to right
    widths = [158, 196, 206, 186]
    gap = (860 - sum(widths)) / 3
    xs = [sum(widths[:i]) + gap * i for i in range(4)]
    texts = [
        "<b>CharlesRiver.xlsx</b><br>Four Tables, never edited:<br>" + "<br>".join(tables),
        "<b>Power Query</b><br>Four queries, " + ", ".join(base[:-1]) + " and " + base[-1] + ": types corrected, columns kept, "
        "custom columns added<br><i>Tutorial 13.1, Steps 2 to 5</i>",
        "<b>Model</b><br>Three relationships: SalesInvoiceLine to Item, SalesInvoiceLine to SalesInvoice, "
        "SalesInvoice to Customer<br><i>Tutorial 13.1, Step 8</i>",
    ]
    h = max(kit.height_for(t, widths[i], SMALL, pad=14) for i, t in enumerate(texts))
    h = max(h, 176)
    ids = []
    for i, t in enumerate(texts):
        ids.append(d.box(t, xs[i], 0, widths[i], h, fill=BLUE_TINT, stroke=BLUE, size=SMALL, align="left", valign="top",
                         stroke_width=1.5))
    # the report pages, three boxes in one frame
    cid = d.box("", xs[3], 0, widths[3], h, fill=WHITE, stroke=BLUE, stroke_width=1.5)
    d.text("<b>Report pages</b>", xs[3] + 8, 4, widths[3] - 16, 20, size=SMALL)
    page_notes = [(pages["validation"], "Tutorial 13.1, Step 10"), (pages["salesDiscounts"], "Tutorial 13.2"),
                  (pages["review"], "Tutorial 13.3")]
    ph = (h - 30 - 8 * 2) / 3
    for i, (name, note) in enumerate(page_notes):
        d.box(f"<b>{esc(name)}</b><br><i>{esc(note)}</i>", xs[3] + 8, 28 + i * (ph + 8), widths[3] - 16, ph, fill=BLUE_TINT,
              stroke=BLUE, size=SMALL, align="left")
    for a, b in zip(ids, ids[1:] + [cid]):
        d.arrow(a, b, exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
    # the six exercise pages
    adds = {"13.1": "Adds the query InvoiceHeaders, left unrelated",
            "13.2": "Adds no query: two Top N tables, by name and by key",
            "13.3": "Adds the query PromotionProgram and a fourth relationship, on PromotionID",
            "13.4": "Adds no query: a slicer, a card, a bar chart and a matrix",
            "13.5": "Adds four queries that do not load: " + ", ".join(profiles[:-1]) + " and " + profiles[-1],
            "13.6": "Adds no query: the pages " + pages_ex6()}
    ew = (860 - 5 * 10) / 6
    texts = [f"<b>Ex {n}</b><br>{esc(titles[n])}<br><br>{esc(adds[n])}<br><br><i>{esc(BUILDS_ON[n])}</i>" for n in titles]
    eh = max(kit.height_for(t, ew, SMALL, pad=14) for t in texts) + 12
    ey = h + 66
    model_id = ids[2]
    for i, t in enumerate(texts):
        eid = d.box(t, i * (ew + 10), ey, ew, eh, fill=TEAL_TINT, stroke=TEAL, size=SMALL, align="left", valign="top",
                    stroke_width=1.5)
        d.arrow(model_id, eid, exit=(0.5, 1), entry=(0.5, 0), meta="")
    bottom = ey + eh + 14
    lx = 0
    for label, fill, stroke in [("Built in the tutorials", BLUE_TINT, BLUE), ("Added by an exercise", TEAL_TINT, TEAL)]:
        d.box("", lx, bottom + 3, 16, 14, fill=fill, stroke=stroke, stroke_width=1.5, rounded=False)
        lw = text_width(label, SMALL, False) + 8
        d.text(label, lx + 22, bottom, lw, 20, size=SMALL, valign="middle")
        lx += 22 + lw + 24
    _note(d, "The model answer holds the three pages of the tutorials and one page for each exercise, Ex 13.1 to Ex 13.5 and the two "
             "pages of Ex 13.6. Each exercise starts from the report as it stands after Tutorial 13.3.", bottom + 26)
    return d


def pages_ex6() -> str:
    names = [json.loads((REPORT / "pages" / p / "page.json").read_text(encoding="utf-8"))["displayName"]
             for p in ("ex136d", "ex136r")]
    return " and ".join(names)


# -- IF-13-0-B: Model view of the model answer ------------------------------------------------------------------------------

def if_13_0_b() -> Diagram:
    """Model view with the six tables of the model answer: SalesInvoiceLine in the middle, four relationships, and
    InvoiceHeaders apart."""
    d = Diagram("Model View of the Model Answer")
    shown = {
        "PromotionProgram": ["PromotionID", "PromotionName", "EffectiveStartDate", "EffectiveEndDate"],
        "Item": ["ItemID", "ItemCode", "ItemGroup"],
        "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "PromotionID", "ItemID", "LineTotal"],
        "SalesInvoice": ["SalesInvoiceID", "CustomerID", "InvoiceDate", "FiscalYear"],
        "Customer": ["CustomerID", "CustomerName", "CustomerSegment", "Region"],
        "InvoiceHeaders": ["SalesInvoiceID", "FiscalYear", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"],
    }
    for table, columns in shown.items():
        assert set(columns) <= set(_model_columns(table)), f"{table} lacks a column the mock shows"
    rels = _relationships()
    wanted = {(("SalesInvoiceLine", "SalesInvoiceID"), ("SalesInvoice", "SalesInvoiceID")),
              (("SalesInvoiceLine", "ItemID"), ("Item", "ItemID")), (("SalesInvoice", "CustomerID"), ("Customer", "CustomerID")),
              (("SalesInvoiceLine", "PromotionID"), ("PromotionProgram", "PromotionID"))}
    assert set(rels) == wanted, "the project's four relationships"
    assert _loaded_tables() == set(shown), "the six tables of the model answer"
    win = pbi.window(d, 536, view="Model", tab="Home", buttons=["Manage relationships", "New measure", "New column"], file=FILE)
    top = win.top
    pbi.canvas(d, win.canvas_x, top, 860 - win.canvas_x, win.bottom - top)
    promo = pbi.model_table(d, "PromotionProgram", 92, top + 24, shown["PromotionProgram"], w=170)
    item = pbi.model_table(d, "Item", 92, top + 190, shown["Item"], w=170)
    sil = pbi.model_table(d, "SalesInvoiceLine", 330, top + 60, shown["SalesInvoiceLine"], w=190)
    si = pbi.model_table(d, "SalesInvoice", 600, top + 24, shown["SalesInvoice"], w=190)
    cust = pbi.model_table(d, "Customer", 600, top + 190, shown["Customer"], w=190)
    inv = pbi.model_table(d, "InvoiceHeaders", 330, top + 262, shown["InvoiceHeaders"], w=190)
    pbi.relationship(d, promo.right("PromotionID"), sil.left("PromotionID"),
                     [(296, promo.rows["PromotionID"]), (296, sil.rows["PromotionID"])])
    pbi.relationship(d, item.right("ItemID"), sil.left("ItemID"), [(314, item.rows["ItemID"]), (314, sil.rows["ItemID"])])
    pbi.relationship(d, si.left("SalesInvoiceID"), sil.right("SalesInvoiceID"),
                     [(560, si.rows["SalesInvoiceID"]), (560, sil.rows["SalesInvoiceID"])])
    pbi.relationship(d, cust.right("CustomerID"), si.right("CustomerID"),
                     [(824, cust.rows["CustomerID"]), (824, si.rows["CustomerID"])])
    xl.emphasis(d, inv.x, inv.y, inv.w, inv.h)
    d.text("<i>InvoiceHeaders, the control table of Exercise 13.1: no relationship line touches it.</i>", 92, inv.y + 66, 210, 60,
           size=SMALL, color=GRAY)
    y = win.bottom + 10
    d.text("<b>1</b> the table that holds the key &nbsp; <b>*</b> the table that refers to it &nbsp; <b>Arrow</b> the direction in "
           "which a filter flows", 0, y, 860, 22, size=SMALL)
    _note(d, "Each table lists its key columns and a few others; the model answer holds more. Outlined: InvoiceHeaders. "
             "PromotionProgram is the table Exercise 13.3 adds; after the tutorials the model has the other three relationships.",
          y + 26)
    return d


# -- IF-13-0-C: the Checks tab in DAX query view -----------------------------------------------------------------------------

def _checks(section: str) -> list[dict]:
    """The rows of one section of the project's Checks tab: label, expected (text as written), tolerance."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'ROW \( "Section", "([^"]+)", "Check", "([^"]+)", "Expected", ([-\d.]+), "Actual", .*?"Agrees", .*? <= ([\d.]+(?:e-?\d+)?) \)',
                         text):
        if m.group(1) == section:
            out.append(dict(label=m.group(2), expected=m.group(3), tolerance=float(m.group(4))))
    return out


def _checks_position(section: str) -> tuple[int, int]:
    """(rows before the section, rows in the query) of the Checks tab."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    sections = re.findall(r'ROW \( "Section", "([^"]+)"', text)
    return sections.index(section), len(sections)


def _ex132_actual() -> callable:
    """A function from a row label of Exercise 13.2's checks to the value the model would return, computed from the dataset."""
    data = ctx.data()
    rows = _year_lines(data.C)
    by_key, name_of = defaultdict(float), {}
    for r in rows:
        by_key[r["customer"]] += r["rev"]
        name_of[r["customer"]] = r["name"]
    by_name = defaultdict(float)
    for k, v in by_key.items():
        by_name[name_of[k]] += v
    by_key, by_name = dict(by_key), dict(by_name)
    keys = sorted(by_key, key=lambda k: -by_key[k])
    names = sorted(by_name, key=lambda n: -by_name[n])
    rank_key = {k: i for i, k in enumerate(keys, 1)}
    rank_name = {n: i for i, n in enumerate(names, 1)}
    total = sum(by_key.values())
    id_of = {}
    for k in by_key:
        id_of.setdefault(name_of[k], []).append(k)
    ids_per_name = Counter(n for (n,) in data.q("SELECT CustomerName FROM Customer"))

    def actual(label: str) -> float:
        if re.fullmatch(r"largest customer's share \(.+\)", label):
            return by_key[keys[0]] / total
        if label == "top ten share by key":
            return sum(by_key[k] for k in keys[:10]) / total
        if label == "top ten share by name":
            return sum(by_name[n] for n in names[:10]) / total
        if m := re.fullmatch(r"customers with revenue in fiscal \d+", label):
            return len(by_key)
        if m := re.fullmatch(r"customer names with revenue in fiscal \d+", label):
            return len(by_name)
        if m := re.fullmatch(r"names carried by more than one CustomerID", label):
            return sum(1 for c in ids_per_name.values() if c > 1)
        if m := re.fullmatch(r"(.+): CustomerIDs", label):
            return ids_per_name[m.group(1)]
        if m := re.fullmatch(r"CustomerID (\d+) revenue", label):
            return by_key[int(m.group(1))]
        if m := re.fullmatch(r"CustomerID (\d+) rank by key", label):
            return rank_key[int(m.group(1))]
        if m := re.fullmatch(r".+ \((\d+)\) revenue", label):
            return by_key[int(m.group(1))]
        if m := re.fullmatch(r"tenth by key: .+ \((\d+)\)", label):
            return by_key[int(m.group(1))]
        if m := re.fullmatch(r"(.+) rank by name", label):
            return rank_name[m.group(1)]
        if m := re.fullmatch(r"(.+) rank by key", label):
            (only,) = id_of[m.group(1)]
            return rank_key[only]
        if m := re.fullmatch(r"(.+) by name", label):
            return by_name[m.group(1)]
        raise KeyError(label)

    return actual


def _fit_dax(line: str, width: float) -> str:
    """A line of the query cut where the editor's pane ends (a long line runs off the right edge)."""
    whole = line
    while line and text_width(pbi.highlight_dax(line), SMALL, False) > width:
        line = line[:-1]
    if line != whole and whole[len(line)].isalnum():
        line = re.sub(r"[A-Za-z0-9_]+$", "", line)           # the editor cuts between pixels; the mock cuts between tokens
    return line.rstrip()


def if_13_0_c() -> Diagram:
    """DAX query view with the Checks tab after Run, scrolled to the rows of Exercise 13.2."""
    section = "Exercise 13.2"
    checks = _checks(section)
    assert len(checks) >= 10
    actual = _ex132_actual()
    rows = []
    for c in checks:
        a = actual(c["label"])
        expected = float(c["expected"])
        assert abs(a - expected) <= c["tolerance"], f"{c['label']}: {a} against {expected}"
        rows.append([section, c["label"], c["expected"], f"{a:.15g}", "True"])
    before, total_rows = _checks_position(section)
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
    bottom = pbi.dax_query_editor(d, x, win.top + 10, w, query, ["Checks"], "Checks")
    # the Results grid, with its own status (the grid holds every row of the query; the figure shows one section)
    gy = bottom + 14
    d.text("<b>Results</b>", x, gy, 120, 22, size=SMALL)
    gy += 24
    widths = [96, 262, 112, 124, 60]
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
    # the vertical scroll bar: the thumb sits where the section lies among the query's rows
    sx = x + grid_w + 3
    d.box("", sx, grid_top, 10, grid_h, fill=GRAY_TINT, stroke=RULE, rounded=False)
    th = max(grid_h * len(rows) / total_rows, 14)
    d.box("", sx + 1, grid_top + (grid_h - th) * before / (total_rows - len(rows)), 8, th, fill=GRAY, stroke=GRAY, rounded=False)
    status_y = grid_top + grid_h + 6
    d.text(esc(f"5 columns, {total_rows} rows"), x, status_y, 220, 20, size=SMALL, color=GRAY)
    xl.emphasis(d, geometry[(0, 4)][0], geometry[(0, 4)][1], geometry[(0, 4)][2], len(rows) * row_h)
    for i, name in enumerate(sorted(_loaded_tables())):
        d.text(esc(name), win.panes_x + 8, win.top + 34 + i * 26, pane_w - 12, 22, size=SMALL)
    _note(d, f"The Checks tab of the model answer after Home > Refresh and Run, scrolled to the {len(rows)} rows of {section}; the query "
             f"returns {total_rows} rows. Long lines of the query run off the editor's edge, and long cells are cut to their "
             "column. Outlined: Agrees, true in every row.", win.bottom + 10)
    return d


# -- IF-13-1-A: the Ex 13.1 page ---------------------------------------------------------------------------------------------

def if_13_1_a() -> Diagram:
    """The Ex 13.1 page: the matrix of line totals by year and group, and the header table beside the same years."""
    d = Diagram("The Ex 13.1 Page")
    years = ctx.values("ch13.ex1")["years"]
    y = ctx.values("ch13.g1")["y"]
    groups = [g for g, _ in years[0]["groups"]]
    assert groups == ["Accessories", "Furniture", "Lighting", "Services", "Textiles"]
    for yr in years:
        assert abs(sum(v for _, v in yr["groups"]) - yr["total"]) < 0.005
        assert abs(yr["total"] + yr["freight"] + yr["tax"] - yr["grand"]) < 0.005
    page = 16
    h1 = (len(years) + 2) * pbi.ROW + 30
    h2 = (len(years) + 2) * pbi.ROW + 30
    canvas_h = page + h1 + 16 + h2 + page
    pbi.canvas(d, 0, 0, 860, canvas_h)
    widths = [92, 108, 108, 108, 108, 108, 126]
    rows = [(0, str(yr["year"]), [_money(v) for _, v in yr["groups"]] + [_money(yr["total"])], "") for yr in years]
    rows.append((0, "Total", [_money(sum(yr["groups"][i][1] for yr in years)) for i in range(5)] +
                 [_money(sum(yr["total"] for yr in years))], ""))
    pbi.matrix_visual(d, page, page, ["FiscalYear", *groups, "Total"], widths, rows, title=_title("ex131", "groupMatrix"))
    last = years.index(next(yr for yr in years if yr["year"] == y))
    xl.emphasis(d, page + 6, page + 26 + pbi.ROW * (last + 1), sum(widths), pbi.ROW)
    y2 = page + h1 + 16
    hw = [92, 128, 128, 128, 134]
    hrows = [[str(yr["year"]), _money(yr["total"]), _money(yr["freight"]), _money(yr["tax"]), _money(yr["grand"])] for yr in years]
    total = ["Total", *[_money(sum(yr[k] for yr in years)) for k in ("total", "freight", "tax", "grand")]]
    t = pbi.table_visual(d, page, y2, ["FiscalYear", "SubTotal", "FreightAmount", "TaxAmount", "GrandTotal"], hw, hrows, total=total,
                         title=_title("ex131", "headerTable"))
    x0, y0, _, _ = t["geometry"][(last, 0)]
    xl.emphasis(d, x0, y0, sum(hw), pbi.ROW)
    gx, gy, gw, _ = t["geometry"][(-1, 4)]
    d.outline(gx, gy, gw, len(rows) * pbi.ROW, TEAL, width=3, front=True)
    kit.callout(d, "GrandTotal is SubTotal plus freight plus tax. It is not revenue.", t["right"] + 12, y2 + 30, 860 - t["right"] - 28, "teal")
    _tabs("Ex 13.1", ["Review", "Ex 13.1", "Ex 13.2"], d, canvas_h + 4)
    _note(d, f"Report view, page Ex 13.1. Outlined in coral: the fiscal {y} row of each visual. Outlined in teal: the GrandTotal "
             "column, which exceeds SubTotal by the freight and the tax. The two visuals agree on every year's SubTotal, and the "
             "table's FiscalYear comes from InvoiceHeaders, which no relationship joins to the model.", canvas_h + 34)
    return d


# -- shared pieces for table and matrix visuals with a title of two lines ---------------------------------------------------

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
        right = bool(rows) and _is_num(rows[0][c])
        d.box(f"<b>{esc(head)}</b>", cx, iy, wd, pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align="right" if right else "left",
              rounded=False)
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


# -- IF-13-1-B: the Power Query Editor on InvoiceHeaders ---------------------------------------------------------------------

def _type_icon(d: Diagram, x: float, y: float, kind: str) -> None:
    """The small type icon in a column header: 123 whole number, 1.2 decimal number, ABC text, a calendar for a date and time."""
    if kind == "date":
        d.box("", x + 2, y + 5, 14, 12, fill=WHITE, stroke=GRAY, rounded=False)
        d.box("", x + 2, y + 5, 14, 4, fill=GRAY, stroke=GRAY, rounded=False)
    else:
        d.text({"whole": "123", "decimal": "1.2", "text": "ABC"}[kind], x, y + 1, 32, 20, size=SMALL, color=GRAY, align="left",
               valign="middle")


def if_13_1_b() -> Diagram:
    """The Power Query Editor on InvoiceHeaders: the five steps, the corrected type on FreightAmount."""
    g = _g13()
    m = g.table_m("InvoiceHeaders")
    steps = []
    for line in m:
        found = re.match(r'^(#"[^"]+"|\w+) =', line)
        if found:
            steps.append(found.group(1).strip('#"'))
    assert steps == ["Source", "T16_SalesInvoice_Table", "Changed Type", "Removed Other Columns", "Added Custom", "Changed Type1"], steps
    steps = ["Navigation" if s.endswith("_Table") else s for s in steps]
    last_formula = "= " + re.sub(r'^#"Changed Type1" = ', "", next(l for l in m if l.startswith('#"Changed Type1" =')))
    freight = g.entry(lambda ok, msg: None, m, "Changed Type", "FreightAmount")
    assert "type number" in freight, "FreightAmount is typed as a decimal number in the model answer"
    queries = _query_order()[:5]
    assert queries[-1] == "InvoiceHeaders"
    data = ctx.data()
    rows = data.q("SELECT SalesInvoiceID, InvoiceDate, SubTotal, FreightAmount, TaxAmount, GrandTotal FROM SalesInvoice "
                  "ORDER BY SalesInvoiceID LIMIT 6")
    assert all(float(r[3]) == int(r[3]) for r in rows), "the first invoices carry whole-dollar freight"
    columns = [("SalesInvoiceID", "whole"), ("InvoiceDate", "date"), ("SubTotal", "decimal"), ("FreightAmount", "decimal"),
               ("TaxAmount", "decimal"), ("GrandTotal", "decimal"), ("FiscalYear", "whole")]
    values = [[str(r[0]), f"{_mdy(r[1])} 12:00:00 AM", f"{r[2]:.15g}", f"{r[3]:.15g}", f"{r[4]:.15g}", f"{r[5]:.15g}"] for r in rows]
    d = Diagram("The InvoiceHeaders Query in the Power Query Editor")
    xl.title_bar(d, 0, 0, 860, "InvoiceHeaders - Power Query Editor")
    qw, sw, top = 118, 164, 34
    d.box(f"<b>Queries [{len(queries)}]</b>", 0, top, qw, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
    for i, name in enumerate(queries):
        on = name == "InvoiceHeaders"
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), 0, top + 28 + i * 26, qw, 26, fill=BLUE_TINT if on else WHITE,
              stroke=BLUE if on else RULE, size=SMALL, align="left", rounded=False)
    gx, gright = qw + 8, 860 - sw - 8
    d.box("<i>fx</i>", gx, top, 26, 26, fill=WHITE, stroke=WHITE, color=GRAY, size=SMALL, rounded=False)
    d.box(esc(_clip(last_formula, gright - gx - 28, margin=14)), gx + 28, top, gright - gx - 28, 26, fill=WHITE, stroke=RULE,
          size=SMALL, align="left", rounded=False)
    # the grid: the columns that fit, then a scroll bar
    tight = 2

    def cell(label: str, x: float, y: float, w: float, h: float, fill: str = WHITE, color: str = INK, align: str = "left") -> None:
        style = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={RULE};strokeWidth=1;fontColor={color};"
                 f"fontSize={SMALL};fontStyle=0;align={align};verticalAlign=middle;{FONT}spacingLeft={tight};spacingRight={tight};")
        d.vertex(label, style, x, y, w, h)

    need = []
    for c, (name, kind) in enumerate(columns[:6]):
        head = text_width(esc(name), SMALL, False) + 28 + 2 * tight + 12
        body = max(text_width(row[c], SMALL, False) for row in values) + 2 * tight + 12
        need.append(round(max(head, body)))
    avail = gright - gx - 26
    shown, used = 0, 0
    for wd in need:
        if used + wd > avail:
            break
        used += wd
        shown += 1
    assert shown >= 4, (shown, need, avail)
    widths = [wd + (avail - used) / shown for wd in need[:shown]]
    gy = top + 34
    cell("", gx, gy, 26, 26, fill=GRAY_TINT)
    xs = [gx + 26]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    heads = {}
    for (name, kind), cx, wd in zip(columns, xs, widths):
        cell(esc(name), cx + 28, gy, wd - 28, 26, fill=GRAY_TINT)
        cell("", cx, gy, 28, 26, fill=GRAY_TINT)
        _type_icon(d, cx + 1, gy + 2, kind)
        heads[name] = (cx, gy, wd, 26)
    for r, row in enumerate(values):
        ry = gy + 26 + r * 24
        cell(str(r + 1), gx, ry, 26, 24, fill=GRAY_TINT, color=GRAY, align="center")
        for c, (cx, wd) in enumerate(zip(xs, widths)):
            cell(esc(row[c]), cx, ry, wd, 24, align="right")
    grid_bottom = gy + 26 + len(values) * 24
    # a horizontal scroll bar: the other columns lie to the right
    sb_y = grid_bottom + 4
    d.box("", gx + 26, sb_y, gright - gx - 26, 10, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.box("", gx + 27, sb_y + 1, (gright - gx - 28) * shown / len(columns), 8, fill=GRAY, stroke=GRAY, rounded=False)
    bottom = grid_bottom + 20
    xl.status_bar(d, gx, bottom, gright - gx, f"{len(columns)} COLUMNS, 999+ ROWS")
    d.text("Column profiling based on top 1000 rows", gright - 290, bottom + 2, 284, 20, size=SMALL, align="right")
    # Query Settings with the Applied Steps
    px = 860 - sw
    d.box("<b>Query Settings</b>", px, top, sw, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.text("<b>Name</b>", px + 6, top + 32, sw - 12, 20, size=SMALL)
    d.box("InvoiceHeaders", px + 6, top + 52, sw - 12, 24, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
    d.text("<b>Applied Steps</b>", px + 6, top + 84, sw - 12, 20, size=SMALL)
    sy = top + 106
    for i, name in enumerate(steps):
        last = i == len(steps) - 1
        d.box(f"<b>{esc(name)}</b>" if last else esc(name), px + 6, sy + i * 26, sw - 12, 26, fill=BLUE_TINT if last else WHITE,
              stroke=BLUE if last else RULE, size=SMALL, align="left", rounded=False)
    xl.emphasis(d, px + 6, sy + 2 * 26, sw - 12, 26)
    cx, cy, cw, ch = heads["FreightAmount"]
    xl.emphasis(d, cx, cy, cw, ch)
    end = max(bottom + 24, sy + len(steps) * 26 + 8)
    _note(d, "The query as Exercise 13.1 builds it, with the Queries pane at the left. Outlined: the Changed Type step, whose entry for "
             "FreightAmount is the decimal number type, and the FreightAmount header with its icon. The grid is scrolled to its left "
             "edge; the columns to the right of FreightAmount are out of view, and the freight of these early invoices is whole dollars "
             "(Power Query types a column from its first 200 rows).", end + 8)
    return d


# -- IF-13-2-A: the two ranked lists --------------------------------------------------------------------------------------

def if_13_2_a() -> Diagram:
    """The Ex 13.2 page: the top ten customers by name beside the top ten by key, which differ by one customer."""
    g = ctx.values("ch13.g2")
    e = ctx.values("ch13.ex2")
    y = g["y"]
    rows = _year_lines(y)
    by_key, name_of = defaultdict(float), {}
    for r in rows:
        by_key[r["customer"]] += r["rev"]
        name_of[r["customer"]] = r["name"]
    by_name = defaultdict(float)
    for k, v in by_key.items():
        by_name[name_of[k]] += v
    top_key = sorted(by_key, key=lambda k: -by_key[k])[:10]
    top_name = sorted(by_name, key=lambda n: -by_name[n])[:10]
    assert abs(sum(by_key[k] for k in top_key) - g["sum_key"]) < 0.005 and abs(sum(by_name[n] for n in top_name) - g["sum_name"]) < 0.005
    merged, tenth = e["merged"]["name"], e["tenth"]["name"]
    assert merged in top_name and merged not in {name_of[k] for k in top_key}, "the merged name is on the by-name list only"
    assert tenth in {name_of[k] for k in top_key} and tenth not in top_name, "the tenth customer by key drops out by name"
    lt = "Sum of LineTotal"
    d = Diagram("The Ex 13.2 Page")
    lw, rw = [226, 144], [76, 190, 144]
    page = 16
    h = 4 + 16 + 4 + 12 + 12 * pbi.ROW
    canvas_h = page + h + page
    pbi.canvas(d, 0, 0, 860, canvas_h)
    left = _table_visual(d, page, page, _title("ex132", "byName"), ["CustomerName", lt], lw,
                         [[n, _money(by_name[n])] for n in top_name], total=["Total", _money(sum(by_name[n] for n in top_name))],
                         title_lines=1)
    right = _table_visual(d, left["right"] + 16, page, _title("ex132", "byKey"), ["CustomerID", "CustomerName", lt], rw,
                          [[str(k), name_of[k], _money(by_key[k])] for k in top_key],
                          total=["Total", "", _money(sum(by_key[k] for k in top_key))], title_lines=1)
    assert right["right"] <= 860 - page + 8, right["right"]
    r = top_name.index(merged)
    x0, y0, _, _ = left["geometry"][(r, 0)]
    xl.emphasis(d, x0, y0, left["width"], pbi.ROW)
    r = [name_of[k] for k in top_key].index(tenth)
    x0, y0, _, _ = right["geometry"][(r, 0)]
    xl.emphasis(d, x0, y0, right["width"], pbi.ROW)
    _tabs("Ex 13.2", ["Ex 13.1", "Ex 13.2", "Ex 13.3"], d, canvas_h + 4)
    _note(d, f"Report view, page Ex 13.2, for fiscal {y}. Outlined: {merged}, which grouping by name makes one customer of two "
             f"(CustomerIDs {e['merged']['parts'][0]['id']} and {e['merged']['parts'][1]['id']}) and so places in the top ten, and "
             f"{tenth}, the tenth customer by key, whom grouping by name pushes out. The two lists differ by that one customer.",
          canvas_h + 34)
    return d


# -- IF-13-3-A: the promotion matrix ---------------------------------------------------------------------------------------

def if_13_3_a() -> Diagram:
    """The Ex 13.3 page: promotions with their dates, two months of the matrix, the (Blank) row and the promotion with
    the end date before its start."""
    from notes import ch13 as n13
    data = ctx.data()
    g = ctx.values("ch13.g3")
    e = ctx.values("ch13.ex3")
    y = g["y"]
    names = {pid: p["name"] for pid, p in n13.promotions(data).items()}
    rows_y = _year_lines(y)
    promos = sorted(e["promos"], key=lambda p: names[p["id"]])
    invalid = e["invalid"]["id"]
    months = [f"{y}-11", f"{y}-12"]
    cell = {}
    for r in rows_y:
        if r["month"] in months:
            key = (r["promo"], r["month"])
            n, disc = cell.get(key, (0, 0.0))
            cell[key] = (n + 1, disc + r["disc"])

    def values(pid) -> list[str]:
        out = []
        for mth in months:
            n, disc = cell.get((pid, mth), (0, 0.0))
            out += [_money(disc), f"{n:,}"] if n else ["", ""]
        return out

    table = [("(Blank)", 0, "+", values(None), None)]
    for p in promos:
        v = values(p["id"])
        table += [(names[p["id"]], 0, "–", v, p["id"]), (_mdy(p["start"]), 1, "–", v, p["id"]), (_mdy(p["end"]), 2, "", v, p["id"])]
    everything = []
    for mm in months:
        everything += [_money(sum(c[1] for (pid, mth), c in cell.items() if mth == mm)),
                       f"{sum(c[0] for (pid, mth), c in cell.items() if mth == mm):,}"]
    label_w, sub_w = 262, 118
    widths = [label_w] + [sub_w] * 4
    title = _title("ex133", "promotionMatrix")
    row_h, head_h, value_head_h = pbi.ROW, 22, 36
    n_rows = len(table) + 1
    frame_w = sum(widths) + 12
    frame_h = 4 + 20 + 2 + head_h + value_head_h + n_rows * row_h + 22 + 8
    page = 16
    canvas_h = page + frame_h + page
    d = Diagram("The Ex 13.3 Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    ix, iy, iw, ih = _frame(d, page, page, frame_w, frame_h, title)
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    # column headings: the months, then the two values under each
    for k, mth in enumerate(months):
        gx0 = xs[1 + 2 * k]
        d.box(f"<b>{mth}</b>", gx0, iy, 2 * sub_w, head_h, fill=WHITE, stroke=WHITE, size=SMALL, align="center", rounded=False)
        for j, head in enumerate(("Sum of<br>DiscountAmount", "Count of<br>SalesInvoiceLineID")):
            d.box(f"<b>{head}</b>", gx0 + j * sub_w, iy + head_h, sub_w, value_head_h, fill=WHITE, stroke=WHITE, size=SMALL,
                  align="right", rounded=False)
    d.box("<b>PromotionName</b>", xs[0], iy + head_h, label_w, value_head_h, fill=WHITE, stroke=WHITE, size=SMALL, align="left",
          valign="bottom", rounded=False)
    d.box("", ix, iy + head_h + value_head_h - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    geometry = {}
    ty = iy + head_h + value_head_h
    for i, (label, level, state, vals, pid) in enumerate(table):
        ry = ty + i * row_h
        bold = level == 0
        glyph = {"+": "+ ", "–": "– ", "": ""}[state]
        text = "&nbsp;" * (5 * level) + esc(glyph + label)
        d.box(f"<b>{text}</b>" if bold else text, xs[0], ry, label_w, row_h, fill=WHITE, stroke=WHITE, size=SMALL, align="left",
              rounded=False)
        for c, v in enumerate(vals):
            d.box(f"<b>{esc(v)}</b>" if bold else esc(v), xs[1 + c], ry, sub_w, row_h, fill=WHITE, stroke=WHITE, size=SMALL,
                  align="right", rounded=False)
        geometry[i] = (xs[0], ry, sum(widths), row_h)
    ry = ty + len(table) * row_h
    d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    d.box("<b>Total</b>", xs[0], ry, label_w, row_h, fill=WHITE, stroke=WHITE, size=SMALL, align="left", rounded=False)
    for c, v in enumerate(everything):
        d.box(f"<b>{esc(v)}</b>", xs[1 + c], ry, sub_w, row_h, fill=WHITE, stroke=WHITE, size=SMALL, align="right", rounded=False)
    # the horizontal scroll bar: twelve months and the total on the columns, two groups in view
    n_groups = 13
    first_group = int(months[0][5:]) - 1
    sb_y = ry + row_h + 6
    d.box("", xs[1], sb_y, 4 * sub_w, 10, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.box("", xs[1] + 1 + (4 * sub_w - 2) * first_group / n_groups, sb_y + 1, (4 * sub_w - 2) * 2 / n_groups, 8, fill=GRAY,
          stroke=GRAY, rounded=False)
    # the marks
    xl.emphasis(d, *geometry[0])
    k = next(i for i, row in enumerate(table) if row[4] == invalid and row[1] == 0)
    gx0, gy0, gw0, _ = geometry[k]
    d.outline(gx0, gy0, gw0, 3 * row_h, TEAL, width=3, front=True)
    label = "The end date is before the start date"
    lw = text_width(label, SMALL, False) + 16
    d.box(label, xs[1] + (4 * sub_w - lw) / 2, geometry[k + 1][1] + 1, lw, row_h - 2, fill=TEAL_TINT, stroke=TEAL, size=SMALL,
          rounded=False)
    _tabs("Ex 13.3", ["Ex 13.2", "Ex 13.3", "Ex 13.4"], d, canvas_h + 4)
    shown_names = {MONTH_NAMES[int(m[5:]) - 1] for m in months}
    late = [p for p in e["promos"] if not p["invalid"] and not p["earlier"] and set(p["after_months"]) & shown_names]
    assert late, "a current promotion has lines invoiced after its end date in these months"
    late_text = " and ".join(f"{names[p['id']]}, which ends {_mdy(p['end'])}" for p in late)
    _note(d, f"Report view, page Ex 13.3, for fiscal {y}. The matrix has the twelve months and a total on its columns and scrolls "
             f"sideways; the figure shows {months[0]} and {months[1]}. Each promotion is expanded to its start and end dates, which repeat "
             f"its values. Outlined in coral: the (Blank) row, the lines sold without a promotion, with no discount. Outlined in teal: "
             f"{names[invalid]}, whose end date precedes its start date. In these months {late_text}, carry lines invoiced after "
             "their end dates.", canvas_h + 34)
    return d


# -- IF-13-4-A: the page for the sales manager -----------------------------------------------------------------------------

def if_13_4_a() -> Diagram:
    """The Ex 13.4 page with the largest segment's bar selected: the card follows, the matrix stays whole."""
    g = ctx.values("ch13.g4")
    e = ctx.values("ch13.ex4")
    y = g["y"]
    segments = e["segments"]
    chosen = segments[0]
    regions = sorted(r for r, _ in e["regions"])
    rows = _year_lines(y)
    cells = defaultdict(float)
    for r in rows:
        cells[(r["segment"], r["region"])] += r["rev"]
    assert abs(sum(cells.values()) - g["rev_total"]) < 0.005
    assert len(segments) == g["n_segments"] and len(regions) == g["n_regions"]
    page = 16
    d = Diagram("The Ex 13.4 Page")
    card_h, bars_h = 64, 196
    canvas_h = page + card_h + 12 + bars_h + 12 + (len(segments) + 2) * pbi.ROW + 30 + page
    pbi.canvas(d, 0, 0, 860, canvas_h)
    # row 1: the Region slicer and the card, which follows the bar chart
    pbi.slicer_dropdown(d, page, page, 220, _title("ex134", "regionSlicer"), "All")
    card_x, card_w = page + 220 + 12, 596
    label = _title("ex134", "discountCard")
    d.box("", card_x, page, card_w, card_h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(label)}</b>", card_x + 6, page + 4, card_w - 12, 20, size=SMALL)
    value = _money(chosen["disc"])
    d.text(f"<b>{esc(value)}</b>", card_x + 6, page + 26, card_w - 12, 32, size=18, align="center", valign="middle")
    xl.emphasis(d, card_x + card_w / 2 - 70, page + 28, 140, 30)
    # row 2: the bar chart, the largest segment selected
    by = page + card_h + 12
    geo = _hbars(d, page, by, 828, bars_h, _title("ex134", "segmentBars"), [s["name"] for s in segments], [s["rev"] for s in segments],
                 "M", selected=chosen["name"], label_w=112)
    bx, byy, bw, bh = geo[chosen["name"]]
    xl.emphasis(d, bx, byy, bw, bh)
    # row 3: the matrix, every segment
    order = sorted(s["name"] for s in segments)
    mrows = []
    for seg in order:
        vals = [_money(cells[(seg, r)]) for r in regions] + [_money(sum(cells[(seg, r)] for r in regions))]
        mrows.append((0, seg, vals, ""))
    mrows.append((0, "Total", [_money(sum(cells[(s, r)] for s in order)) for r in regions] + [_money(sum(cells.values()))], ""))
    my = by + bars_h + 12
    pbi.matrix_visual(d, page, my, ["CustomerSegment", *regions, "Total"], [136, 128, 128, 128, 128, 140], mrows,
                      title=_title("ex134", "segmentMatrix"))
    assert my + (len(mrows) + 1) * pbi.ROW + 30 + page <= canvas_h, "the matrix fits the page"
    _tabs("Ex 13.4", ["Ex 13.3", "Ex 13.4", "Ex 13.5"], d, canvas_h + 4)
    _note(d, f"Report view, page Ex 13.4, for fiscal {y}, as Step 5 leaves it. The {chosen['name']} bar is selected: the other bars "
             "fade and the card shows that segment's discounts. Edit interactions has set the matrix to None, so it still shows every "
             "segment. Outlined: the selected bar and the card's value.", canvas_h + 34)
    return d


# -- IF-13-5-A: one column profiled on two bases --------------------------------------------------------------------------

def _pct_share(part: int, whole: int) -> str:
    """A share as the profile writes it: whole percents, and under one percent for a few."""
    share = 100 * part / whole
    return "< 1%" if 0 < share < 1 else f"{share:.0f}%"


def if_13_5_a() -> Diagram:
    """Profile_Invoices on the top 1,000 rows and on the entire data set: the empty share of PaymentDate and the number of
    distinct values of Status."""
    e = ctx.values("ch13.ex5")
    g = ctx.values("ch13.g5")
    data = ctx.data()
    invoices = data.q("SELECT PaymentDate, Status FROM SalesInvoice ORDER BY SalesInvoiceID")
    assert len(invoices) == e["invoices"]
    top_n = g["top_rows"]
    bases = [("Profiled on the top 1,000 rows", invoices[:top_n], "Column profiling based on top 1000 rows"),
             ("Profiled on the entire data set", invoices, "Column profiling based on entire data set")]
    first = invoices[:6]
    d = Diagram("Profile_Invoices Profiled on Two Bases")
    pw = 424
    distincts = []
    for x, (caption, rows, status) in zip((0, 436), bases):
        n = len(rows)
        empty = sum(1 for r in rows if r[0] is None)
        counts = Counter(r[1] for r in rows)
        distinct, unique = len(counts), sum(1 for c in counts.values() if c == 1)
        distincts.append(distinct)
        d.text(f"<b>{esc(caption)}</b>", x, 0, pw, 22, size=SMALL)
        xl.title_bar(d, x, 24, pw, "Profile_Invoices - Power Query Editor")
        cw = pw / 2
        top = 56
        for c, (name, kind) in enumerate([("PaymentDate", "date"), ("Status", "text")]):
            cx = x + c * cw
            d.box(esc(name), cx + 34, top, cw - 34, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
            d.box("", cx, top, 34, 26, fill=GRAY_TINT, stroke=RULE, rounded=False)
            _type_icon(d, cx + 4, top + 2, kind)
            valid = n - empty if name == "PaymentDate" else n
            miss = empty if name == "PaymentDate" else 0
            for i, (label, value, color) in enumerate([("Valid", valid, TEAL), ("Error", 0, CORAL), ("Empty", miss, GRAY)]):
                ly = top + 30 + i * 22
                d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={color};", cx + 8, ly + 6, 8, 8)
                d.text(f"{label} {_pct_share(value, n)}", cx + 22, ly, cw - 26, 20, size=SMALL)
            if name == "PaymentDate":
                xl.emphasis(d, cx + 4, top + 30 + 2 * 22 + 1, 110, 20)
        # the distribution of Status, one bar for each distinct value, the most frequent first
        sx = x + cw
        bars_top, bars_h = top + 102, 40
        peak = max(counts.values())
        for i, (value, c) in enumerate(counts.most_common()):
            h = max(2, bars_h * c / peak)
            d.box("", sx + 10 + i * 24, bars_top + bars_h - h, 18, h, fill=BLUE, stroke=BLUE, rounded=False)
        label = f"{distinct} distinct, {unique} unique"
        d.text(label, sx + 4, bars_top + bars_h + 2, cw - 8, 20, size=SMALL)
        xl.emphasis(d, sx + 2, bars_top + bars_h + 3, text_width(label, SMALL, False) + 14, 18)
        # the first rows of the preview, the same on both bases
        py = top + 174
        for r, (pay, state) in enumerate(first):
            for c, value in enumerate(["null" if pay is None else f"{_mdy(pay)} 12:00:00 AM", state]):
                cx = x + c * cw
                d.box(f"<i>{value}</i>" if value == "null" else esc(value), cx, py + r * 22, cw, 22, fill=WHITE, stroke=RULE,
                      color=GRAY if value == "null" else INK, size=SMALL, align="right" if c == 0 else "left", rounded=False)
        sy = py + len(first) * 22 + 6
        xl.status_bar(d, x, sy, pw, status)
    bottom = sy + 24 + 12
    top_states, all_states = e["top_statuses"], e["statuses"]
    assert distincts == [len(top_states), len(all_states)]
    _note(d, f"Profile_Invoices with Column quality and Column distribution on. Outlined: the empty share of PaymentDate, and the "
             f"number of distinct values of Status ({', '.join(all_states[:-1])} and {all_states[-1]} on the entire data set; "
             f"{top_states[0]} alone in the first {top_n:,} rows). The first rows are the earliest invoices, nearly all paid. The "
             "preview shows two of the table's columns and is the same on both bases, and the distribution is drawn for Status only, "
             "although the editor draws it under every column.", bottom)
    return d


# -- IF-13-6-A and IF-13-6-B: the draft page and the revised page ---------------------------------------------------------

def _pie(d: Diagram, x: float, y: float, w: float, h: float, title: str, cats: list[str], values: list[float]) -> None:
    """A pie chart with no data labels and a legend, as the draft page has it."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title)
    total = sum(values)
    r = min(ih / 2 - 6, 92)
    cx, cy = ix + r + 18, iy + ih / 2
    start = 0.0
    for color, v in zip(pbi.SERIES, values):
        share = v / total
        d.vertex("", f"shape=mxgraph.basic.pie;html=1;startAngle={start:.4f};endAngle={start + share:.4f};fillColor={color};"
                     f"strokeColor={WHITE};", cx - r, cy - r, 2 * r, 2 * r)
        start += share
    lx = cx + r + 30
    top = cy - len(cats) * 24 / 2
    for i, (color, name) in enumerate(zip(pbi.SERIES, cats)):
        d.box("", lx, top + i * 24 + 4, 14, 14, fill=color, stroke=color, rounded=False)
        d.text(esc(name), lx + 20, top + i * 24, w - (lx - x) - 28, 22, size=SMALL, valign="middle")


def _monthly(rows: list[dict], field: str) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for r in rows:
        out[r["month"]] += r[field]
    return dict(sorted(out.items()))


def if_13_6_a() -> Diagram:
    """The Ex 13.6 Draft page: a pie with no labels, a card, a line chart on the default axis, and a combo chart on two axes."""
    g = ctx.values("ch13.g6")
    e = ctx.values("ch13.ex6")
    y = g["y"]
    all_rows, rows = _lines(), _year_lines(y)
    revenue = defaultdict(float)
    for r in rows:
        revenue[r["group"]] += r["rev"]
    order = [name for name, _ in e["slices"]]
    assert order == sorted(revenue, key=lambda k: -revenue[k]) and len(order) == 5
    monthly = _monthly(all_rows, "rev")
    shown = [r for r in rows if r["group"] != "Services"]
    combo_rev = _monthly(shown, "rev")
    combo_disc = _monthly(shown, "disc")
    assert abs(sum(combo_rev.values()) - g["shown"]) < 0.005
    page = 16
    h1, h2 = 250, 250
    canvas_h = page + h1 + 14 + h2 + page
    d = Diagram("The Ex 13.6 Draft Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    _pie(d, page, page, 410, h1, "Sum of LineTotal by ItemGroup", order, [revenue[k] for k in order])
    # the card: Average of Discount, unformatted
    cx = page + 410 + 16
    ix, iy, iw, ih = _frame(d, cx, page, 402, 100, "Average discount")
    d.text(f"<b>{e['avg']:.4f}</b>", ix, iy, iw, ih, size=20, align="center", valign="middle")
    # the line chart on the default axis, and the combo chart on two axes
    low, high = min(monthly.values()), max(monthly.values())
    auto = pbi.nice_ticks(low, high, 4)
    assert auto[0] > 0, "the default axis does not start at zero"
    months = list(monthly)
    y2 = page + h1 + 14
    pbi.line_chart(d, page, y2, 410, h2, "Sum of LineTotal by Month", months, [("Sum of LineTotal", list(monthly.values()), BLUE)], "M", auto,
                   every=6)
    year_months = list(combo_rev)
    combo = pbi.combo_chart(d, cx, y2, 402, h2, "Sum of LineTotal and Sum of DiscountAmount by Month", year_months,
                            ("Sum of LineTotal", list(combo_rev.values())), ("Sum of DiscountAmount", list(combo_disc.values())), "M",
                            pbi.nice_ticks(0, max(combo_rev.values()), 4), "K", pbi.nice_ticks(0, max(combo_disc.values()), 3), every=3)
    xl.emphasis(d, *combo["right_axis"])
    _tabs("Ex 13.6 Draft", ["Ex 13.5", "Ex 13.6 Draft", "Ex 13.6 Revised"], d, canvas_h + 4)
    _note(d, f"Report view, page Ex 13.6 Draft, for fiscal {y} except the line chart, which spans every month. The pie has five slices and "
             f"no labels; the card averages the Discount of each line; the line chart's value axis starts at {pbi.units(auto[0], 'M')}, "
             "not at zero; the combo chart's discounts have an axis of their own (outlined), and its hidden filter leaves out Services, "
             "which nothing on the page says.", canvas_h + 34)
    return d


def if_13_6_b() -> Diagram:
    """The Ex 13.6 Revised page: each draft element replaced by an honest equivalent, every visual titled."""
    g = ctx.values("ch13.g6")
    t = ctx.values("ch13.t2")
    t3 = ctx.values("ch13.t3")
    y = g["y"]
    all_rows, rows = _lines(), _year_lines(y)
    revenue = defaultdict(float)
    for r in rows:
        revenue[r["group"]] += r["rev"]
    order = sorted(revenue, key=lambda k: -revenue[k])
    assert abs(sum(r["disc"] for r in rows) - t["disc"]) < 0.005 and abs(sum(r["list"] for r in rows) - t["list"]) < 0.005
    monthly = _monthly(all_rows, "rev")
    rev26, disc26 = _monthly(rows, "rev"), _monthly(rows, "disc")
    years = ctx.data().years
    year_rev = [sum(r["rev"] for r in all_rows if r["year"] == yr) for yr in years]
    assert all(abs(a - b) < 0.005 for a, b in zip(year_rev, t3["years"]))
    page = 16
    h1, h2 = 262, 250
    canvas_h = page + h1 + 14 + h2 + page
    d = Diagram("The Ex 13.6 Revised Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    _hbars(d, page, page, 410, h1, _title("ex136r", "groupBars"), order, [revenue[k] for k in order], "M", label_w=100)
    rx, rw = page + 410 + 16, 402
    ch = 104
    ix, iy, iw, ih = _frame(d, rx, page, rw, ch, _title("ex136r", "discountCards"), lines=1)
    half = (iw - 10) / 2
    pbi.card(d, ix, iy, half, ih - 4, "Sum of DiscountAmount", _money(sum(r["disc"] for r in rows)))
    pbi.card(d, ix + half + 10, iy, half, ih - 4, "Sum of ListAmount", _money(sum(r["list"] for r in rows)))
    ymax = pbi.nice_ticks(0, max(year_rev) * 1.25, 2)
    _columns(d, rx, page + ch + 10, rw, h1 - ch - 10, _title("ex136r", "yearColumns"), [str(v) for v in years], year_rev, "M", ymax)
    y2 = page + h1 + 14
    zero = pbi.nice_ticks(0, max(monthly.values()), 4)
    _lines_chart(d, page, y2, 410, h2, _title("ex136r", "monthsFromZero"), list(monthly), [("Sum of LineTotal", list(monthly.values()), BLUE)],
                 "M", zero, every=6)
    shared = pbi.nice_ticks(0, max(rev26.values()), 4)
    _lines_chart(d, rx, y2, rw, h2, _title("ex136r", "oneAxis"), list(rev26),
                 [("Sum of LineTotal", list(rev26.values()), BLUE), ("Sum of DiscountAmount", list(disc26.values()), AMBER)], "M", shared,
                 every=3, legend=True)
    _tabs("Ex 13.6 Revised", ["Ex 13.6 Draft", "Ex 13.6 Revised", "Notes"], d, canvas_h + 4)
    _note(d, f"Report view, page Ex 13.6 Revised, for fiscal {y} except the charts by year and by month of the whole window. Each "
             "visual carries the model answer's own title, naming the measure and the period. Services is a bar of its own, the "
             "line chart starts at zero, and the discounts share one axis with revenue, where they are small.", canvas_h + 34)
    return d


FIGURES = {"IF-13-0-A": if_13_0_a, "IF-13-0-B": if_13_0_b, "IF-13-0-C": if_13_0_c, "IF-13-1-A": if_13_1_a,
           "IF-13-1-B": if_13_1_b, "IF-13-2-A": if_13_2_a, "IF-13-3-A": if_13_3_a, "IF-13-4-A": if_13_4_a,
           "IF-13-5-A": if_13_5_a, "IF-13-6-A": if_13_6_a, "IF-13-6-B": if_13_6_b}
