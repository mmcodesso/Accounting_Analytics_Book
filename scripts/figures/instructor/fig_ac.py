"""Instructor figures of Appendix C (guides in facts/instructor/guides/appendix-c-power-bi-browser/).

The appendix is the last unit.  It has NO solution file: the projects open only in Desktop, and the browser steps were read
in the author's own Power BI service account on October 6, 2026 (drafts/appendix-c-service-results.md).  So the mocks draw the
service as the book's own mocks of this appendix do (scripts/figures/appendix_c.py: the service's top bar, the model editor's
DAX query view, the report editor's menu bar, panes and page tabs, with no Desktop ribbon), and every value comes from the
dataset through the guides' own contexts (appC.g1 to appC.g3) and the registered notes (appendix_c.ex1 to appendix_c.ex3),
which compute them from Chapter 13's twin of the model the browser builds.

What no mock here shows as fact: the window of Save to version history and the restore control of Version history (the author's
test read only the two commands, so the timeline draws their effect and not their windows), and a matrix or a legend on a line
chart in the service (the test did not build them; the mocks draw them as the report editor's Visualizations pane and the book's
Tutorial C.2 describe the same wells).
"""

from __future__ import annotations

import re
from collections import defaultdict

import ctx
import excel as xl
import kit
import powerbi as pbi
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, FONT, GRAY, GRAY_TINT, HIGHLIGHT, INK, RULE, SMALL, TEAL,
                    WHITE, Diagram, esc)

GUIDE = ctx.REPO / "facts" / "instructor" / "guides" / "appendix-c-power-bi-browser" / "00-chapter-notes.md"
EDITOR_TABS = ["File", "Home", "Help"]
EDITOR_VIEWS = ["Model view", "DAX query view", "TMDL View (Preview)"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December"]


# -- helpers ---------------------------------------------------------------------------------------------------------------

def _c13():
    from notes import ch13
    return ch13


def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def _plain(x: float) -> str:
    """A number as DAX query view's grid writes it: no format string, no thousands separator, two decimals at most."""
    return "0" if abs(x) < 0.005 else f"{round(x, 2):.15g}"


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A value cut to its column with an ellipsis, as a narrow column shows it."""
    if text_width(text, size, bold) <= width - margin:
        return text
    while text and text_width(text + "…", size, bold) > width - margin:
        text = text[:-1]
    return text + "…"


def _cell(d: Diagram, x: float, y: float, w: float, h: float, value: str, align: str = "left", fill: str = WHITE,
          stroke: str = RULE, bold: bool = False, pad: float = 6, color: str = INK) -> str:
    """A grid cell that never wraps: its text may leave only 6 px of padding, so a narrow column of numbers still fits."""
    label = f"<b>{value}</b>" if bold else value
    style = (f"rounded=0;whiteSpace=nowrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=1;fontColor={color};"
             f"fontSize={SMALL};fontStyle=0;align={align};verticalAlign=middle;{FONT}spacingLeft={pad};spacingRight={pad};")
    return d.vertex(label, style, x, y, w, h)


def _header(d: Diagram, y: float, crumb: str, right: list[str] | None = None) -> float:
    """The service's top bar: Power BI, the item open, the search box, and buttons on the right (the book's appendix mock)."""
    d.box("", 0, y, 860, 32, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.text("<b>Power BI</b>", 8, y + 5, 80, 22, size=SMALL, color=BLUE, valign="middle")
    d.text(esc(crumb), 84, y + 5, 230, 22, size=SMALL, valign="middle")
    d.box("Search", 330, y + 4, 200, 24, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, align="left", rounded=True)
    x = 852
    for label in reversed(right or []):
        w = text_width(esc(label), SMALL, False) + 22
        x -= w
        xl.button(d, x, y + 3, w, label, primary=label == "Share")
        x -= 6
    return y + 32


def _views(d: Diagram, y: float, active: str) -> None:
    """The model editor's views, as tabs along the bottom."""
    x = 0
    d.box("", 0, y, 860, 30, fill=GRAY_TINT, stroke=RULE, rounded=False)
    for name in EDITOR_VIEWS:
        on = name == active
        w = text_width(esc(name), SMALL, on) + 24
        d.box(f"<b>{esc(name)}</b>" if on else esc(name), x + 4, y + 3, w, 24, fill=WHITE if on else GRAY_TINT,
              stroke=BLUE if on else GRAY_TINT, stroke_width=2 if on else 1, color=BLUE if on else INK, size=SMALL,
              rounded=False)
        x += w + 6


def _path(d: Diagram, pts: list[tuple[float, float]]) -> None:
    """One arrow through the points, straight between them, ending in an arrow head."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=GRAY, end="blockThin", points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _tag(d: Diagram, text: str, x: float, y: float, w: float = 34) -> None:
    """Yes or No on an arrow, in a small white box laid over the line."""
    d.box(f"<b>{text}</b>", x, y, w, 20, fill=WHITE, stroke=WHITE, size=SMALL)


def _measure_names(g: dict) -> dict[str, str]:
    """The measure each guide formula defines: 'List Amount = SUM ( ... )' gives List Amount."""
    names = {}
    for key in ("m_list", "m_disc", "m_lines", "m_rev"):
        m = re.match(r"^([A-Za-z ]+?) =", g[key])
        assert m, g[key]
        names[key] = m.group(1)
    return names


def _data_pane(d: Diagram, x: float, y: float, w: float, h: float, measures: list[str], inset: bool = False) -> None:
    """The Data pane of the model editor and the report editor: its title, Tables and Model tabs, a search box and the tables.
    Key Measures heads the list, with its measures in alphabetical order, because its only column, Column1, is hidden."""
    if inset:
        d.box("", x, y, w, h, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
        d.box("<b>Data pane (inset)</b>", x, y, w, 26, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL, align="left",
              rounded=False)
        ty = y + 32
    else:
        d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
        d.text("<b>Data</b>", x + 8, y + 6, 100, 22, size=SMALL)
        d.text("<b>Tables</b>", x + 8, y + 32, 64, 22, size=SMALL, color=BLUE)
        d.box("", x + 8, y + 52, 54, 3, fill=BLUE, stroke=BLUE, rounded=False)
        d.text("Model", x + 76, y + 32, 64, 22, size=SMALL)
        d.box("Search", x + 8, y + 60, w - 16, 24, fill=WHITE, stroke=GRAY, color=GRAY, size=SMALL, align="left",
              rounded=True)
        ty = y + 92
    entries = [("▾ ", "Key Measures", 0, True)] + [("", m, 1, False) for m in sorted(measures)] + [
        ("▸ ", t, 0, False) for t in ("Customer", "Item", "SalesInvoice", "SalesInvoiceLine")]
    for i, (glyph, label, level, bold) in enumerate(entries):
        text = glyph + (f"<b>{esc(label)}</b>" if bold else esc(label))
        d.text("&nbsp;" * 5 * level + text, x + 8, ty + i * 22, w - 12, 22, size=SMALL, valign="middle")


# -- IF-AC-0-A: which plan fits ----------------------------------------------------------------------------------------------

def _plans() -> dict[str, int]:
    """The class minutes of Plan A, Plan B and Plan C, read from the guide's own headings (180, 75 and 60)."""
    text = GUIDE.read_text(encoding="utf-8")
    found = {m.group(1): int(m.group(2)) for m in re.finditer(r"\*\*Plan ([ABC]): [^(]+?\((?:[^)]*?, )?(\d+) minutes\)\.\*\*", text)}
    assert set(found) == {"A", "B", "C"}, found
    return found


def if_ac_0_a() -> Diagram:
    """A staircase of three questions down the left and the plan each answer leads to on the right."""
    d = Diagram("Which Plan Fits the Class")
    minutes = _plans()
    guide = GUIDE.read_text(encoding="utf-8")
    for phrase in ("Step 2 of C.1 (Choose data)", "Step 7 (**Create a semantic model only**)", "Step 3 of C.3 (**New measure**)", "C.1 Steps 1 to 4 on your account",
                   "C.1 Steps 7 to 9", "The differences of C.2: the card, the display units, the sort", "Without Pro.", "Students then do the exercises in Desktop"):
        assert phrase in guide, f"the guide no longer says: {phrase}"
    questions = [
        "<b>Start:</b> can the student sign in at app.powerbi.com with a school account?",
        "May the student edit semantic models and upload to OneDrive for work or school?",
        "Is there a Pro license?",
    ]
    leaves = [
        ("gray", "<b>Desktop, in a lab or on a Windows virtual machine</b><br>Tutorials: 13.1, 13.2 and 14.2 in Desktop take the place of "
                 "C.1, C.2 and C.3.<br>Exercises: C.1 to C.3, worked in Desktop."),
        ("amber", f"<b>Plan C ({minutes['C']} minutes), or Desktop</b><br>The instructor shows C.1 Steps 1 to 4 and 7 to 9, the differences of "
                  "C.2 (the card, the display units, the sort) and the measure and test of C.3.<br>Students: Exercises C.1 to C.3 in Desktop."),
        ("teal", f"<b>Plan A ({minutes['A']} minutes) or Plan B ({minutes['B']} minutes), with Exercise C.3 done by hand</b><br>Tutorials: C.1, C.2 "
                 "and C.3.<br>Exercises: C.1 and C.2; C.3 Steps 2, 3 and 5, with the formula retyped and no version history."),
        ("teal", f"<b>Plan A ({minutes['A']} minutes) or Plan B ({minutes['B']} minutes), every step</b><br>Tutorials: C.1, C.2 and C.3.<br>"
                 "Exercises: C.1 to C.3, with C.3's <i>Save to version history</i> and <i>Version history</i>."),
    ]
    qx, qw, lx, lw = 0, 300, 372, 488
    gap = 46
    q_h = [kit.height_for(q, qw, pad=18) for q in questions]
    l_h = [kit.height_for(t, lw, pad=18) for _, t in leaves]
    row_h = [max(q_h[i], l_h[i]) for i in range(3)] + [l_h[3]]
    tops = [0.0]
    for h in row_h[:-1]:
        tops.append(tops[-1] + h + gap)
    q_top = [tops[i] + (row_h[i] - q_h[i]) / 2 for i in range(3)]
    for i in range(3):
        d.box(questions[i], qx, q_top[i], qw, q_h[i], fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5)
    for i, (color, text) in enumerate(leaves):
        fill, stroke = kit.tint(color)
        d.box(text, lx, tops[i], lw, row_h[i], fill=fill, stroke=stroke, stroke_width=1.5, align="left")
    cx = qx + qw / 2
    for i in range(3):                                       # No: straight across to the plan
        yc = tops[i] + row_h[i] / 2
        _path(d, [(qx + qw, yc), (lx, yc)])
        _tag(d, "No", (qx + qw + lx) / 2 - 17, yc - 10)
    for i in range(2):                                       # Yes: down to the next question
        a, b = q_top[i] + q_h[i], q_top[i + 1]
        _path(d, [(cx, a), (cx, b)])
        _tag(d, "Yes", cx - 17, (a + b) / 2 - 10)
    y4 = tops[3] + row_h[3] / 2                              # the last Yes: down, then across to the last plan
    a = q_top[2] + q_h[2]
    _path(d, [(cx, a), (cx, y4), (lx, y4)])
    _tag(d, "Yes", cx - 17, a + 14)
    bottom = tops[3] + row_h[3]
    _note(d, f"Plan A, Plan B and Plan C are the plans of the Teaching approaches below. Teal: students work in the service; amber: the instructor shows it; "
             "gray: students use Desktop. A Pro license matters only for the version history of Exercise C.3, and a tenant setting beats a license. "
             "Before the term, test the second question with a student-licensed account: Step 2 and Step 7 of Tutorial C.1 and Step 3 of Tutorial C.3.",
          bottom + 12)
    return d


# -- IF-AC-1-A: the query of Exercise C.1 after Run --------------------------------------------------------------------------

def if_ac_1_a() -> Diagram:
    """DAX query view of the model editor after the query of Exercise C.1 has run: twelve rows, the four of the current year outlined."""
    g = ctx.values("appC.g1")
    e = ctx.values("appendix_c.ex1")
    data = ctx.data()
    n13 = _c13()
    rows = n13.lines(data)
    names = _measure_names(g)
    y0 = data.C
    table, per_q = [], {}
    for yr in data.years:
        for qn in range(1, 5):
            sub = [r for r in rows if r["year"] == yr and r["quarter"] == qn]
            vals = (len(sub), round(n13.total(sub, "rev"), 2), round(n13.total(sub, "list"), 2), round(n13.total(sub, "disc"), 2))
            per_q[(yr, qn)] = vals
            table.append([str(yr), f"{yr}-Q{qn}", str(vals[0]), _plain(vals[1]), _plain(vals[2]), _plain(vals[3])])
    assert len(table) == g["n_rows"] and g["n_cols"] == 6 and len(data.years) * 4 == len(table)
    current = [per_q[(y0, qn)] for qn in range(1, 5)]
    for qn, (n, rev, lst, disc) in enumerate(current):                                      # the guide's own Expected results
        q = e["quarters"][qn]
        assert q["q"] == qn + 1 and q["n"] == n and abs(q["rev"] - rev) < 0.005 and abs(q["list"] - lst) < 0.005 and abs(q["disc"] - disc) < 0.005
        assert g["quarters"][qn]["label"] == table[len(table) - 4 + qn][1] and g["quarters"][qn]["n"] == n
    rounded_sum = round(sum(c[3] for c in current), 2)
    year_disc = round(e["year"]["disc"], 2)
    assert abs(rounded_sum - g["rounded_sum"]) < 0.005 and abs(abs(year_disc - rounded_sum) - g["cent"]) < 0.0051, "the quarters differ from the year by a cent"
    quarter_total = lambda i: round(sum(per_q[(y, qn)][i] for y in [y0] for qn in range(1, 5)), 2)          # noqa: E731
    assert abs(quarter_total(1) - round(e["year"]["rev"], 2)) < 0.005 and abs(quarter_total(2) - round(e["year"]["list"], 2)) < 0.005
    query = g["query"].split("\n")
    heads = ["SalesInvoice[FiscalYear]", "SalesInvoice[Period]", "[Invoice lines]", "[Revenue]", "[List amount]", "[Discounts]"]
    aligns = ["right", "left", "right", "right", "right", "right"]
    num_w, w = 30, 640
    widths = []
    for c, head in enumerate(heads):
        need = max([text_width(head, SMALL, True)] + [text_width(r[c], SMALL, False) for r in table]) + 18
        widths.append(int(need))
    widths[0] = min(widths[0], 124)                          # the service cuts a long header with an ellipsis
    widths[1] = min(widths[1], 132)
    assert num_w + sum(widths) <= w, (num_w + sum(widths), widths)

    d = Diagram("The Result of the Query of Exercise C.1")
    y = _header(d, 0, "Charles River Reports", ["Editing ▾", "Share"])
    top = pbi.ribbon(d, 0, y + 2, 860, "Home", ["Format", "Comment", "Uncomment", "Find", "Replace", "Command palette"],
                     tabs=EDITOR_TABS)
    banner = "DAX queries are discarded on close. DAX queries previously saved to the model are not shown or impacted."
    bh = kit.height_for(banner, w, SMALL, pad=16)
    d.box(banner, 0, top + 6, w, bh, fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", rounded=False)
    end = pbi.dax_query_editor(d, 0, top + 6 + bh + 8, w, "\n".join(query), ["Query 1"], "Query 1")
    gy = end + 12
    d.text("<b>Results</b>", 0, gy, 70, 26, size=SMALL, valign="middle")
    d.box("Result 1 of 1 ▾", 76, gy, 116, 26, fill=WHITE, stroke=GRAY, size=SMALL, rounded=True)
    xl.button(d, 200, gy, 78, "Copy ▾")
    gy += 32
    gx = num_w
    d.box("", 0, gy, num_w, pbi.ROW + 2, fill=GRAY_TINT, stroke=RULE, rounded=False)
    cx = gx
    for head, wd in zip(heads, widths):
        _cell(d, cx, gy, wd, pbi.ROW + 2, esc(_clip(head, wd, bold=True)), fill=GRAY_TINT, bold=True)
        cx += wd
    geometry = {}
    for r, row in enumerate(table):
        ry = gy + pbi.ROW + 2 + r * pbi.ROW
        _cell(d, 0, ry, num_w, pbi.ROW, str(r + 1), align="right")
        cx = gx
        for c, (value, wd) in enumerate(zip(row, widths)):
            _cell(d, cx, ry, wd, pbi.ROW, esc(value), align=aligns[c])
            geometry[(r, c)] = (cx, ry, wd, pbi.ROW)
            cx += wd
    grid_w = num_w + sum(widths)
    first = len(table) - 4
    xl.emphasis(d, 0, geometry[(first, 0)][1], grid_w, 4 * pbi.ROW)
    status_y = gy + pbi.ROW + 2 + len(table) * pbi.ROW + 6
    d.text(esc(f"{len(heads)} columns, {len(table)} rows"), 0, status_y, 220, 20, size=SMALL, color=GRAY)
    bottom = status_y + 20 + 8
    _data_pane(d, w + 10, top, 860 - w - 10, bottom - top, [names[k] for k in ("m_rev", "m_list", "m_disc", "m_lines")])
    _views(d, bottom, "DAX query view")
    _note(d, f"DAX query view of the model editor after Run, with the query of Exercise C.1, Step 3: one row for each fiscal quarter of the "
             f"{n13.word(len(data.years))} years, ordered by year and period. Outlined: the four rows of fiscal {y0}, which are the Expected results. "
             f"The four quarters' lines, revenue and list amount add to the year's; their discounts, each rounded to the cent, add to "
             f"${pbi.amount(rounded_sum)}, a cent below the year's ${pbi.amount(year_disc)}. The grid shows the values as the query returns "
             "them, without the measures' format, and cuts a long header with an ellipsis. Key Measures heads the Data pane because its only "
             "column, Column1, is hidden; its measures are listed alphabetically.", bottom + 40)
    return d


# -- IF-AC-2-A: the page Ex C.2 -----------------------------------------------------------------------------------------------

def _dot(d: Diagram, cx: float, cy: float, color: str, marker: str, size: float = 8) -> None:
    """A point marker: the shapes differ, so the five lines read without their colors."""
    if marker == "diamond":
        style = f"rhombus;html=1;fillColor={color};strokeColor={color};"
    elif marker == "square":
        style = f"rounded=0;html=1;fillColor={color};strokeColor={color};"
    elif marker == "triangle":
        style = f"triangle;direction=north;html=1;fillColor={color};strokeColor={color};"
    elif marker == "hollow":
        style = f"ellipse;html=1;fillColor={WHITE};strokeColor={color};strokeWidth=2;"
    else:
        style = f"ellipse;html=1;fillColor={color};strokeColor={color};"
    d.vertex("", style, cx - size / 2, cy - size / 2, size, size)


def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str, width: float = 2.5) -> None:
    """One edge through the points, drawn straight between them (separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _lines_chart(d: Diagram, x: float, y: float, w: float, h: float, title: str, cats: list[str],
                 series: list[tuple[str, list[float], str, str]], ticks: list[float], every: int = 2) -> dict:
    """A line chart of several series, each (name, values, color, marker), with its legend above the plot, as a legend at the top."""
    ix, iy, iw = x + 6, y + 4, w - 12
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(title)}</b>", ix, iy, iw, 20, size=SMALL)
    lx = ix
    ly = iy + 24
    for name, _, color, marker in series:
        d.box("", lx, ly + 9, 20, 3, fill=color, stroke=color, rounded=False)
        _dot(d, lx + 10, ly + 10.5, color, marker, 8)
        nw = text_width(esc(name), SMALL, False) + 8
        d.text(esc(name), lx + 24, ly, nw, 20, size=SMALL)
        lx += 24 + nw + 12
    assert lx <= ix + iw + 12, f"the legend needs {lx - ix:.0f} px of {iw:.0f}"
    left, plot_w = ix + 50, iw - 58
    top, plot_h = ly + 32, h - (ly - y) - 32 - 34
    low, high = ticks[0], ticks[-1]
    y_of = lambda v: top + (high - v) * plot_h / (high - low)                    # noqa: E731
    for t in ticks:
        d.vertex("", f"rounded=0;html=1;fillColor={RULE};strokeColor=none;", left, y_of(t), plot_w, 1)
        d.text(pbi.units(t, "K"), ix, y_of(t) - 10, 44, 20, size=SMALL, color=GRAY, align="right", valign="middle")
    step = plot_w / len(cats)
    xs = [left + step * (i + 0.5) for i in range(len(cats))]
    for i, (cx, label) in enumerate(zip(xs, cats)):
        if i % every == 0:
            d.text(esc(label), cx - step * every / 2, top + plot_h + 4, step * every, 20, size=SMALL, color=GRAY, align="center")
    for name, values, color, marker in series[1:] + series[:1]:
        pts = [(cx, y_of(v)) for cx, v in zip(xs, values)]
        _polyline(d, pts, color)
        for px, py in pts:
            _dot(d, px, py, color, marker, 7)
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of)


def if_ac_2_a() -> Diagram:
    """The report editor on the page Ex C.2: the tile slicer, the matrix of Discounts by segment and month, and the line chart."""
    g = ctx.values("appC.g2")
    e = ctx.values("appendix_c.ex2")
    data = ctx.data()
    n13 = _c13()
    y0 = data.C
    rows = [r for r in n13.lines(data) if r["year"] == y0]
    segs = sorted({r["segment"] for r in rows})
    assert segs == sorted(g["segs"]) and len(segs) == g["n_segs"] == 5
    cell, present = defaultdict(float), defaultdict(int)
    for r in rows:
        cell[(r["segment"], r["m"])] += r["disc"]
        present[(r["segment"], r["m"])] += 1
    none = g["none"]
    assert all(present[(s, m)] for s in segs for m in range(1, 13)), "every segment has invoice lines in every month, so no cell is blank"
    assert all(abs(cell[(none, m)]) < 0.005 for m in range(1, 13)), "the segment with no discounts reads zero in every month"
    peaks = {s: max(range(1, 13), key=lambda m: cell[(s, m)]) for s in segs if s != none}
    assert len(peaks) == len(e["peaks"]) == 4
    for s, month, peak, total in e["peaks"]:                                  # the guide's own Expected results
        assert MONTHS[peaks[s] - 1] == month and abs(cell[(s, peaks[s])] - peak) < 1e-6 and abs(sum(cell[(s, m)] for m in range(1, 13)) - total) < 1e-6
    assert abs(sum(cell.values()) - g["total"]) < 1e-6
    trade_p, autumn_p = n13.segment_promotion(data, "Design Trade"), n13.autumn_promotion(data)
    assert peaks["Design Trade"] == int(trade_p["start"][5:7]), "Design Trade peaks in the month of its own promotion"
    assert all(int(autumn_p["start"][5:7]) <= m <= int(autumn_p["end"][5:7]) for s, m in peaks.items() if s != "Design Trade"), "the others peak in the autumn promotion's months"
    months = [f"{y0}-{m:02d}" for m in range(1, 13)]
    fmt = lambda v: f"{v:,.2f}"                                                # noqa: E731
    names = _measure_names(ctx.values("appC.g1"))

    # the matrix: one row for each segment, one column for each month, no total row or column
    label_w, col_w = 120, 59.5
    mw = label_w + 12 * col_w + 8
    assert mw <= 852 - 8
    d = Diagram("The Page Ex C.2")
    y = _header(d, 0, "Charles River Reports", ["Text box", "Buttons", "Visual interactions", "Save"])
    d.box("", 0, y, 860, 30, fill=WHITE, stroke=RULE, rounded=False)
    mx = 8
    for label in ["File ▾", "View ▾", "Reading view", "Mobile layout", "Open semantic model"]:
        wd = text_width(esc(label), SMALL, False) + 18
        d.text(esc(label), mx, y + 5, wd, 20, size=SMALL, valign="middle")
        mx += wd + 6
    top = y + 30
    s_y = top + 12
    m_y = s_y + 56 + 12
    m_h = 4 + 22 + len(segs) * pbi.ROW + 4
    c_y = m_y + m_h + 12
    c_h, side_w = 262, 200
    canvas_h = (c_y + c_h + 12) - top
    d.box("", 0, top, 860, canvas_h, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.box("", 4, top + 4, 852, canvas_h - 8, fill=WHITE, stroke=RULE, rounded=False)
    pbi.slicer_tiles(d, 8, s_y, "FiscalYear", [str(yr) for yr in data.years], str(y0), tile_w=56)
    # the matrix visual
    d.box("", 8, m_y, mw, m_h, fill=WHITE, stroke=RULE, rounded=False)
    ix, iy = 12, m_y + 4
    _cell(d, ix, iy, label_w, 22, "<b>CustomerSegment</b>", fill=WHITE, stroke=WHITE)
    for c, month in enumerate(months):
        _cell(d, ix + label_w + c * col_w, iy, col_w, 22, f"<b>{month}</b>", align="right", fill=WHITE, stroke=WHITE)
    d.box("", ix, iy + 21, label_w + 12 * col_w, 1, fill=INK, stroke=INK, rounded=False)
    geometry = {}
    for r, s in enumerate(segs):
        ry = iy + 22 + r * pbi.ROW
        _cell(d, ix, ry, label_w, pbi.ROW, esc(s), fill=WHITE, stroke=WHITE)
        for c in range(12):
            on = peaks.get(s) == c + 1
            _cell(d, ix + label_w + c * col_w, ry, col_w, pbi.ROW, f"<b>{fmt(cell[(s, c + 1)])}</b>" if on else fmt(cell[(s, c + 1)]),
                  align="right", fill=WHITE, stroke=WHITE, pad=3)
            geometry[(r, c)] = (ix + label_w + c * col_w, ry)
    for s, c in peaks.items():
        px, py = geometry[(segs.index(s), c - 1)]
        d.outline(px + 1.5, py + 1.5, col_w - 3, pbi.ROW - 3, CORAL, width=2, front=True)
    zy = geometry[(segs.index(none), 0)][1]
    d.outline(ix - 1, zy + 1.5, label_w + 12 * col_w + 2, pbi.ROW - 3, TEAL, width=2, front=True)
    # the line chart, with the five segments in its legend
    series = [(s, [cell[(s, m)] for m in range(1, 13)], color, marker) for s, color, marker in
              zip(segs, [GRAY, AMBER, TEAL, CORAL, BLUE], ["circle", "diamond", "square", "triangle", "hollow"])]
    assert series[0][0] == none, "the flat line of the segment with no discounts is drawn last, on top of the others"
    ticks = pbi.nice_ticks(0, max(max(v) for _, v, _, _ in series), 4)
    chart_w = 852 - 8 - side_w - 12 - 4
    _lines_chart(d, 8, c_y, chart_w, c_h, "Discounts by Month and CustomerSegment", months, series, ticks)
    _data_pane(d, 8 + chart_w + 12, c_y, side_w, c_h, [names[k] for k in ("m_rev", "m_list", "m_disc", "m_lines")], inset=True)
    bottom = top + canvas_h
    pbi.page_tabs(d, 4, bottom + 4, ["Sales and Discounts", "Validation", "Ex C.2"], "Ex C.2")
    ky = bottom + 40
    for i, (label, color) in enumerate([("Each other segment's largest month", CORAL), (f"{none}'s row, zero in every month", TEAL)]):
        kx = [0, 280][i]
        d.outline(kx + 1, ky + 3, 18, 14, color, width=2.5)
        d.text(esc(label), kx + 26, ky, text_width(esc(label), SMALL, False) + 12, 20, size=SMALL, valign="middle")
    trade = "Design Trade"
    others = sorted({MONTHS[m - 1] for s, m in peaks.items() if s != trade}, key=MONTHS.index)
    _note(d, f"Report editor, page Ex C.2, fiscal {y0} chosen on the tile slicer. The matrix has no total row or column, and the line chart is in "
             f"month order. {none} reads 0.00 in every month because it has invoice lines every month and each has a discount of zero. "
             f"{trade} peaks in {MONTHS[peaks[trade] - 1]}, with its own promotion; the others peak in {' or '.join(others)}, "
             "with the autumn promotion. The real toolbar shows icons, and the real editor shows the Filters and Visualizations panes beside "
             "Data: the mock writes the toolbar's names and draws the Data pane as an inset, because twelve months of amounts to the cent need the full width.",
          ky + 28)
    return d


# -- IF-AC-3-A: the three runs of the test -------------------------------------------------------------------------------------

def if_ac_3_a() -> Diagram:
    """Three boxes joined by arrows, each with the test's revenue and the page's revenue card, and a board of what a version keeps."""
    g = ctx.values("appC.g3")
    e = ctx.values("appendix_c.ex3")
    data = ctx.data()
    cur = g["years"][-1]
    assert cur["year"] == data.C == g["y"]
    rev, lst = cur["rev"], cur["list"]
    diff = lst - rev
    assert abs(e["rev"] - rev) < 0.005 and abs(e["list"] - lst) < 0.005 and abs(e["diff"] - diff) < 0.005 and diff > 0
    assert "LineTotal" in g["m_rev"] and "ListAmount" in g["changed"], "the change swaps the column the measure sums"
    runs = [
        ("Run 1: before the change", "Save a version", TEAL, rev, "The baseline."),
        ("Run 2: after the change", "Change the Revenue formula", AMBER, lst, f"Up by ${pbi.amount(diff)}. The card is unchanged: it reads a column, not the measure."),
        ("Run 3: after the restore", "Restore the version", TEAL, rev, "Equal to run 1: the restore is proved by the test."),
    ]
    stub, bw, bh, gap = 104, 176, 276, 114                     # 104 + 3 x 176 + 2 x 114 = 860
    mid = bh / 2
    d = Diagram("The Three Runs of the Test")
    ids = []
    for i, (title, _, color, test, remark) in enumerate(runs):
        x = stub + i * (bw + gap)
        ids.append(d.box("", x, 0, bw, bh, fill=WHITE, stroke=color, stroke_width=1.5, rounded=False))
        d.box(f"<b>{esc(title)}</b>", x, 0, bw, 28, fill=color, stroke=color, color=WHITE, size=SMALL, rounded=False)
        d.text(f"The test, fiscal {data.C} row", x + 10, 34, bw - 20, 18, size=SMALL, color=GRAY)
        changed = i == 1
        _cell(d, x + 10, 56, bw - 20, 24, "<b>[Revenue]</b>", fill=GRAY_TINT)
        _cell(d, x + 10, 80, bw - 20, 24, f"<b>{_plain(round(test, 2))}</b>" if changed else _plain(round(test, 2)), align="right",
              fill=HIGHLIGHT if changed else WHITE, stroke=HIGHLIGHT if changed else RULE)
        d.text("The page's revenue card", x + 10, 112, bw - 20, 18, size=SMALL, color=GRAY)
        pbi.card(d, x + 10, 134, bw - 20, 62, "Revenue", pbi.amount(rev))
        d.text(esc(remark), x + 10, 204, bw - 20, 68, size=SMALL, valign="top")
        assert text_width(esc(remark), SMALL, False) < 4 * (bw - 34), remark
    # the arrows: Save a version leads into the first run; the other two lead from one run to the next
    start = d.anchor(0, mid)
    d.edge(start, d.anchor(stub, mid), end="blockThin", color=GRAY, meta="edgeStyle=none;")
    d.text(f"<b>{esc(runs[0][1])}</b>", 4, mid - 44, stub - 12, 36, size=SMALL, align="center", valign="bottom")
    for i in range(2):
        label = runs[i + 1][1]
        x0 = stub + i * (bw + gap) + bw
        d.arrow(ids[i], ids[i + 1], exit=(1, 0.5), entry=(0, 0.5), meta="edgeStyle=none;")
        d.text(f"<b>{esc(label)}</b>", x0 + 6, mid - 44, gap - 12, 36, size=SMALL, color=INK, align="center", valign="bottom")
    cols = [
        ("Version history, in the service", [
            "The model and its data at each saved version",
            "The last five versions only",
            "The last person to change each, and a description if one was typed",
            "A Pro license to use it"], "teal"),
        ("It does not record", [
            "What changed, change by change",
            "A reason, unless someone typed it",
            "A review before a change takes effect"], "coral"),
        ("A project under version control adds", [
            "Every change, with its author and a message",
            "A review before a change is merged: Chapter 16's change control"], "blue"),
    ]
    board = kit.board(d, cols, x=0, y=bh + 28, w=860, gap=14)
    _note(d, f"The three results of the Expected results: the test of Tests.dax for fiscal {data.C}, before the change, after Revenue sums ListAmount in place of "
             "LineTotal, and after the restore. The test reads the measure; the page's cards read the columns, so they do not move. Highlighted: "
             "the test after the change, the only place it shows. Below: what a saved version keeps, what it leaves out, and what a project under "
             "version control adds. The window of Save to version history and the restore control were not read in the author's test, so the "
             "figure draws their effect, not their windows.", board["bottom"] + 12)
    return d


FIGURES = {"IF-AC-0-A": if_ac_0_a, "IF-AC-1-A": if_ac_1_a, "IF-AC-2-A": if_ac_2_a, "IF-AC-3-A": if_ac_3_a}
