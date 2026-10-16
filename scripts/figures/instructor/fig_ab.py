"""Instructor figures of Appendix B (guides in facts/instructor/guides/appendix-b-publishing-security/).

The appendix is the third Power BI unit.  Its mocks draw the model answer
(outputs/companion/solutions/AppendixB-exercises-pbi, a PBIP of TMDL, PBIR and DAX query text), so the page titles, the
text box, the query tabs, the Security table and the Checks tab are read from that project, and every value comes from
the dataset through the guides' own contexts (appB.chapter, appB.g1, appB.g2) and the notes' helpers (appendix_b.t1,
appendix_b.ex2, ch15.t3).  The figure that chooses a scope reads the Teaching approaches table of the guide itself.

What no mock here shows as fact: the wording of the bar that Desktop draws while View as is on, the message Desktop draws
in a visual that cannot read a hidden column, and the Manage roles dialog.  The mocks draw the bar and the message as the
book's own figure of Guided Tutorial B.1 does and as the model answer's note quotes the engine, and the notes say so.
"""

from __future__ import annotations

import base64
import json
import re
import zlib

import ctx
import excel as xl
import kit
import powerbi as pbi
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

FILE = "Appendix B Exercises - Solutions"
PROJECT = ctx.REPO / "outputs" / "companion" / "solutions" / "AppendixB-exercises-pbi" / FILE
MODEL = PROJECT / f"{FILE}.SemanticModel"
REPORT = PROJECT / f"{FILE}.Report" / "definition"
GUIDE = ctx.REPO / "facts" / "instructor" / "guides" / "appendix-b-publishing-security" / "00-chapter-notes.md"
PAD = 16


# -- the model answer (a PBIP of text files) ----------------------------------------------------------------------------

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


def _projections(page: str, name: str, role: str) -> list[str]:
    return [p["nativeQueryRef"] for p in _visual(page, name)["visual"]["query"]["queryState"][role]["projections"]]


def _paragraphs(page: str, name: str) -> list[tuple[str, bool]]:
    """The text box's paragraphs as (text, bold): the model answer's note."""
    paras = _visual(page, name)["visual"]["objects"]["general"][0]["properties"]["paragraphs"]
    return [("".join(r["value"] for r in p["textRuns"]), any(r.get("textStyle", {}).get("fontWeight") == "bold" for r in p["textRuns"]))
            for p in paras]


def _query_tabs() -> list[str]:
    return json.loads((MODEL / ".pbi" / "daxQueries.json").read_text(encoding="utf-8"))["tabOrder"]


def _security_rows() -> list[tuple[str, int]]:
    """The Security table as the model answer holds it: the rows of its Enter data step."""
    text = (MODEL / "definition" / "tables" / "Security.tmdl").read_text(encoding="utf-8")
    raw = zlib.decompress(base64.b64decode(re.search(r'Binary\.FromText\("([^"]+)"', text).group(1)), -15)
    return [(upn, int(cc)) for upn, cc in json.loads(raw)]


def _checks_text() -> str:
    return (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")


def _checks() -> list[dict]:
    """Every row of the project's Checks tab, in order: section, label, expected (text as written, a quoted string unquoted)
    and the tolerance of a numeric row."""
    out = []
    for line in _checks_text().split("\n"):
        m = re.search(r'ROW \( "Section", "([^"]+)", "Check", "([^"]+)", "Expected", ("(?:[^"]|"")*"|-?[\d.]+), "Actual"', line)
        if not m:
            continue
        expected = m.group(3)
        tol = re.search(r"<= ([\d.]+) \)", line)
        out.append(dict(section=m.group(1), label=m.group(2), expected=expected.strip('"') if expected.startswith('"') else expected,
                        numeric=not expected.startswith('"'), tol=float(tol.group(1)) if tol else 0.0))
    return out


# -- drawing helpers ----------------------------------------------------------------------------------------------------

def _nowrap(text: str) -> str:
    """A cell value that must not break at a space or a hyphen: the grid cuts it to its column instead."""
    return f'<span style="white-space:nowrap">{esc(text)}</span>'


def _mdy(iso: str) -> str:
    """An ISO date as Short Date reads in the model (en-US): 4/26/2024."""
    return f"{int(iso[5:7])}/{int(iso[8:10])}/{iso[:4]}"


def _plain(x: float) -> str:
    """A number as DAX query view's grid writes it: no format string, no thousands separator, two decimals at most."""
    return "0" if abs(x) < 0.005 else f"{round(x, 2):.15g}"


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


def _lines(text: str, width: float, n: int) -> list[str]:
    """The words of a text broken into lines of at most `width` px, the last of n lines ending in an ellipsis when the text is longer."""
    out, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if text_width(esc(trial), SMALL, False) <= width:
            cur = trial
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    if len(out) <= n:
        return out
    last = out[n - 1]
    while last and text_width(esc(last + " …"), SMALL, False) > width:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    return out[:n - 1] + [last + " …"]


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
                  aligns: list[str] | None = None, title_lines: int | None = None,
                  total: list[str] | None = None) -> dict:
    """A table visual: a title, a header row, the rows (banded) and an optional bold total row.  aligns names each column's side.
    Returns the cell geometry keyed (row, column) with row -1 for the headers, and the visual's bottom and right edges."""
    w = sum(widths) + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
    n = len(rows) + (1 if total else 0)
    h = th + 12 + pbi.ROW + n * pbi.ROW
    ix, iy, _, _ = _frame(d, x, y, w, h, title, lines=title_lines)
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    aligns = aligns or ["right" if any(_is_num(r[c]) for r in rows) else "left" for c in range(len(headers))]
    geometry = {}
    for c, (head, cx, wd) in enumerate(zip(headers, xs, widths)):
        d.box(f"<b>{esc(_clip(head, wd, bold=True))}</b>", cx, iy, wd, pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align=aligns[c], rounded=False)
        geometry[(-1, c)] = (cx, iy, wd, pbi.ROW)
    d.box("", ix, iy + pbi.ROW - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, row in enumerate(rows + ([total] if total else [])):
        ry = iy + pbi.ROW * (r + 1)
        is_total = total is not None and r == len(rows)
        if is_total:
            d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
        for c, (value, cx, wd) in enumerate(zip(row, xs, widths)):
            plain = r % 2 == 0 or is_total
            d.box(f"<b>{esc(_clip(value, wd, bold=True))}</b>" if is_total else esc(_clip(value, wd)), cx, ry, wd, pbi.ROW,
                  fill=WHITE if plain else GRAY_TINT, stroke=WHITE if plain else GRAY_TINT, size=SMALL, align=aligns[c], rounded=False)
            geometry[(r, c)] = (cx, ry, wd, pbi.ROW)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, top=iy, width=sum(widths))


def _scrollbar(d: Diagram, right: float, top: float, height: float, shown: int, total: int, first: int = 0) -> None:
    """A vertical scroll bar at a visual's right edge: the thumb is the share of the rows in view, at the first row's place."""
    d.box("", right - 10, top, 6, height, fill=GRAY_TINT, stroke=GRAY_TINT, rounded=False)
    th = max(height * shown / total, 12)
    d.box("", right - 10, top + (height - th) * first / max(total - shown, 1), 6, th, fill=GRAY, stroke=GRAY, rounded=False)


def _hscroll(d: Diagram, x: float, y: float, w: float, start: float, length: float) -> None:
    """A horizontal scroll bar: the thumb starts at the fraction `start` of the track and is `length` of it long."""
    d.box("", x, y, w, 6, fill=GRAY_TINT, stroke=GRAY_TINT, rounded=False)
    d.box("", x + w * start, y, w * length, 6, fill=GRAY, stroke=GRAY, rounded=False)


def _viewing_bar(d: Diagram, x: float, y: float, w: float, user: str | None, role: str) -> None:
    """The bar above a page while View as is on, as the book's own figure of Guided Tutorial B.1 draws it: the user and the role,
    and the Stop viewing button.  Its wording in Desktop may differ."""
    who = f"<b>{esc(user)}</b> in the role " if user else "the role "
    d.box(f"Viewing as {who}<b>{esc(role)}</b>", x, y, w - 98, 28, fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", rounded=False)
    xl.button(d, x + w - 90, y + 1, 90, "Stop viewing")


def _text_box(d: Diagram, x: float, y: float, w: float, h: float, page: str, name: str, per_paragraph: int) -> None:
    """The page's text box, with the model answer's own paragraphs cut to a few lines each (a text box has no scroll in the mock)."""
    paras = _paragraphs(page, name)
    assert paras[0] == ("Model answer", True), paras[0]
    parts = ["<b>Model answer</b>"]
    for text, _ in paras[1:]:
        parts.append("<br>".join(esc(line) for line in _lines(text, w - 36, per_paragraph)))
    body = "<br><br>".join(parts)
    assert 16 * (body.count("<br>") + 1) + 12 <= h, f"the text box holds {body.count('<br>') + 1} lines in {h:.0f} px"
    d.box(body, x, y, w, h, fill=WHITE, stroke=RULE, size=SMALL, align="left", valign="top", rounded=False)


# -- IF-AB-0-A: how much of the appendix to teach -----------------------------------------------------------------------------

def _scopes() -> list[tuple[str, str, str, str, str]]:
    """The three rows of the guide's Teaching approaches table: number, scope, what students do, what it needs, class time."""
    text = GUIDE.read_text(encoding="utf-8")
    rows = re.findall(r"^\| ([123])\. ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", text, re.M)
    assert [r[0] for r in rows] == ["1", "2", "3"], rows
    totals = re.findall(r"^\|\s*(\d+) \| Total \|$", text, re.M)
    assert "100 minutes (Plan B)" in rows[0][4] and "150 minutes (Plan A" in rows[1][4] and "100" in totals, "the scopes' minutes are the plans' totals"
    return rows


def _path(d: Diagram, pts: list[tuple[float, float]]) -> None:
    """One arrow through the points, straight between them, ending in an arrow head."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=GRAY, end="blockThin", points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _tag(d: Diagram, text: str, x: float, y: float) -> None:
    """Yes or No on an arrow, in a small white box laid over the line."""
    d.box(f"<b>{text}</b>", x, y, 34, 20, fill=WHITE, stroke=WHITE, size=SMALL)


def if_ab_0_a() -> Diagram:
    """A top-down tree from the start to the three scopes, with each scope's work, needs and class time from the guide's table."""
    d = Diagram("How Much of the Appendix to Teach")
    scopes = _scopes()
    leaf_w, xs = 270, [0, 295, 590]
    centers = [x + leaf_w / 2 for x in xs]
    texts = []
    for n, name, does, needs, time in scopes:
        texts.append(f"<b>Scope {n}: {esc(name)}</b><br>{esc(does)}<br><i>Needs:</i> {esc(needs)}<br><b>Class time: {esc(time)}</b>")
    leaf_h = max(kit.height_for(t, leaf_w, pad=16) for t in texts)
    q2x = (centers[0] + centers[1]) / 2
    q1x = (q2x + centers[2]) / 2
    start_text = "<b>Start</b>: students have Power BI Desktop and the Charles River Reports project"
    q1_text = "Do you and a partner have Pro or Premium Per User licenses and a shared workspace where you are Admin?"
    q2_text = "Add the Publishing and Sharing section as reading, with Step 5 of Tutorial B.2 as a workshop?"
    sw, q1w, q2w = 440, 300, 270
    sh = kit.height_for(start_text, sw, pad=14)
    q1h = kit.height_for(q1_text, q1w, pad=16)
    q2h = kit.height_for(q2_text, q2w, pad=16)
    sy = 0
    q1y = sy + sh + 40
    q2y = q1y + q1h + 50
    ly = q2y + q2h + 54
    start = d.box(start_text, q1x - sw / 2, sy, sw, sh, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5)
    q1 = d.box(q1_text, q1x - q1w / 2, q1y, q1w, q1h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5)
    q2 = d.box(q2_text, q2x - q2w / 2, q2y, q2w, q2h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5)
    d.arrow(start, q1, exit=(0.5, 1), entry=(0.5, 0), meta="edgeStyle=none;")
    for i, text in enumerate(texts):
        d.box(text, xs[i], ly, leaf_w, leaf_h, fill=TEAL_TINT, stroke=TEAL, align="left", valign="top", stroke_width=1.5)
    # No: to the second question; Yes: straight to the full scope
    mid_y = q1y + q1h / 2
    _path(d, [(q1x - q1w / 2, mid_y), (q2x, mid_y), (q2x, q2y)])
    _tag(d, "No", (q1x - q1w / 2 + q2x) / 2 - 17, mid_y - 10)
    _path(d, [(q1x + q1w / 2, mid_y), (centers[2], mid_y), (centers[2], ly)])
    _tag(d, "Yes", (q1x + q1w / 2 + centers[2]) / 2 - 17, mid_y - 10)
    # the second question: No to Scope 1, Yes to Scope 2
    fork = q2y + q2h + 26
    _path(d, [(q2x, q2y + q2h), (q2x, fork), (centers[0], fork), (centers[0], ly)])
    _tag(d, "No", (q2x + centers[0]) / 2 - 17, fork - 10)
    _path(d, [(q2x, fork), (centers[1], fork), (centers[1], ly)])
    _tag(d, "Yes", (q2x + centers[1]) / 2 - 17, fork - 10)
    _note(d, "The work, the needs and the class time are the rows of the Teaching approaches table below; Plan A, Plan B and Plan C are the plans "
             "that follow it. Scope 3 asks for 45 to 60 minutes of student time outside the class as well.", ly + leaf_h + 10)
    return d


# -- the DAX query view window ------------------------------------------------------------------------------------------------

def _fit_dax(line: str, width: float) -> str:
    """A line of the query cut where the editor's pane ends (a long line runs off the right edge)."""
    whole = line
    while line and text_width(pbi.highlight_dax(line), SMALL, False) > width:
        line = line[:-1]
    if line != whole and whole[len(line)].isalnum():
        line = re.sub(r"[A-Za-z0-9_]+$", "", line)           # the editor cuts between pixels; the mock cuts between tokens
    return line.rstrip()


def _editor(d: Diagram, x: float, y: float, w: float, rows: list[tuple[int | None, str]], tab: str, updates: int,
            selected: range | None = None) -> dict:
    """DAX query view's Run button, query tabs and editor.  rows are (line number, text): a long line is cut at the editor's edge,
    and a row with no number is a gap whose text says which lines the picture leaves out.  selected holds the line numbers drawn
    selected.  Returns the editor's top and bottom and the y of each line."""
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
        bottom = ys[last] + line_h if last in ys else y + height - 4          # a selection that ends in a gap runs to the editor's last row
        d.box("", x + gutter + 1, ys[first], w - gutter - 2, bottom - ys[first], fill=BLUE_TINT, stroke=BLUE_TINT, rounded=False)
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


def _grid(d: Diagram, x: float, y: float, headers: list[str], widths: list[float], rows: list[list[str]]) -> dict:
    """A results grid: bold headers, left-aligned values, cut with an ellipsis where a column is narrow.  Returns the cell geometry."""
    cx = x
    for head, wd in zip(headers, widths):
        d.box(f"<b>{esc(_clip(head, wd, bold=True))}</b>", cx, y, wd, pbi.ROW + 2, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        cx += wd
    geometry = {}
    for r, row in enumerate(rows):
        cx = x
        for c, (value, wd) in enumerate(zip(row, widths)):
            ry = y + pbi.ROW + 2 + r * pbi.ROW
            d.box(_nowrap(_clip(value, wd)), cx, ry, wd, pbi.ROW, fill=WHITE, stroke=RULE, size=SMALL, align="left", rounded=False)
            geometry[(r, c)] = (cx, ry, wd, pbi.ROW)
            cx += wd
    return geometry


def _column_outline(d: Diagram, geometry: dict, column: int, rows: int, color: str = TEAL) -> None:
    x, y, w, _ = geometry[(0, column)]
    d.outline(x + 1.5, y + 1.5, w - 3, rows * pbi.ROW - 3, color, width=2.5, front=True)


# -- IF-AB-0-B: the Checks tab ------------------------------------------------------------------------------------------------

def if_ab_0_b() -> Diagram:
    """DAX query view with the tab Checks after Run, scrolled to the rows of the Sales Manager (employee006)."""
    t1 = ctx.values("appendix_b.t1")
    s = t1["s"]
    checks = _checks()
    prefix = "as employee006 (Sales Manager)"
    first = next(i for i, c in enumerate(checks) if c["label"].startswith(prefix))
    mine = [c for c in checks[first:] if c["label"].startswith(prefix)]
    assert len(mine) == 8 and all(c["section"] == "Guided Tutorial B.1" for c in mine), [c["label"] for c in mine]
    # what each row's Actual is, from the dataset (the notes' view_as): the rows' labels name the measure
    actual = {
        "Cost Centers Shown": ", ".join(s["centers"]),
        "2026 operating expense Budget": s["budget"],
        "2026 Actual": s["actual"],
        "2026 Flexed Budget": s["flexed"],
        "2026 Net Income": s["ni"],
        "2026 Revenue (every sale)": t1["revenue"],
        "2026 Manufacturing Hours (an empty Plant page)": "blank" if s["hours"] is None else "not blank",
        "employees": s["employees"],
    }
    rows = []
    for c in mine:
        name = c["label"][len(prefix) + 2:]
        a = actual[name]
        if c["numeric"]:
            assert abs(float(c["expected"]) - a) <= max(c["tol"], 0.005), f"{c['label']}: {a} against {c['expected']}"
            shown = _plain(a)
        else:
            assert a == c["expected"], f"{c['label']}: {a} against {c['expected']}"
            shown = a
        rows.append([c["section"], c["label"], c["expected"] if not c["numeric"] else _plain(float(c["expected"])), shown, "True"])
    row_h = pbi.ROW
    d = Diagram("The Checks Tab in DAX Query View")
    height = 96 + 10 + 56 + 5 * 20 + 8 + 14 + 24 + row_h + 2 + len(rows) * row_h + 30 + 14
    win = pbi.window(d, height, view="DAX query", tab="Home", tabs=pbi.QUERY_TABS, panes=[], file=FILE,
                     buttons=["Format", "Comment", "Uncomment", "Find", "Replace", "Command palette"])
    x, w = win.canvas_x + 8, win.canvas_w - 16
    source = _checks_text().split("\n")[:5]
    editor_w = w - 34 - 28
    query = [(i + 1, _fit_dax(line, editor_w)) for i, line in enumerate(source)]
    ed = _editor(d, x, win.top + 10, w, query, "Checks", 0)
    gy = ed["bottom"] + 14
    d.text("<b>Results</b>", x, gy, 120, 22, size=SMALL)
    gy += 24
    widths = [118, 380, 98, 98, 64]
    assert sum(widths) <= w - 14
    geometry = _grid(d, x, gy, ["[Section]", "[Check]", "[Expected]", "[Actual]", "[Agrees]"], widths, rows)
    grid_top, grid_h = gy + row_h + 2, len(rows) * row_h
    sx = x + sum(widths) + 3
    _scrollbar(d, sx + 10, grid_top, grid_h, len(rows), len(checks), first)
    d.text(esc(f"5 columns, {len(checks)} rows"), x, grid_top + grid_h + 6, 220, 20, size=SMALL, color=GRAY)
    xl.emphasis(d, geometry[(0, 4)][0], geometry[(0, 4)][1], geometry[(0, 4)][2], grid_h)
    _note(d, f"The Checks tab of the model answer after Home > Refresh and Run, scrolled to the {len(rows)} rows that start "
             f"'{prefix}', the rows of Guided Tutorial B.1 for the Sales Manager, {first + 1} to {first + len(rows)} of the query's {len(checks)}. "
             "The query runs as the file's author, so no role applies: each of these rows repeats the role's three rules as filters with the "
             "user's name typed in. Values are written to the cent, and a label longer than its column is cut at the column's edge. "
             "Outlined: Agrees, true in every row.", win.bottom + 10)
    return d


# -- IF-AB-1-A and IF-AB-1-B: the page Ex B.1 ---------------------------------------------------------------------------------------

def _error_visual(d: Diagram, x: float, y: float, w: float, h: float, title: str | None, message: str) -> None:
    """A visual that cannot be drawn: its frame and title stay, and an exclamation mark in a coral circle comes with the message."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title, lines=1 if title else None)
    cy = iy + ih / 2
    d.marker("!", ix + 12, cy - 16, fill=CORAL, size=32)
    lines = ["<b>This visual cannot be displayed</b>"] + [esc(line) for line in _lines(message, iw - 80, 3)]
    d.text("<br>".join(lines), ix + 54, cy - 8 * len(lines) - 2, iw - 62, 16 * len(lines) + 4, size=SMALL, valign="middle")


def _hbars(d: Diagram, x: float, y: float, w: float, h: float, title: str, cats: list[str], values: list[float]) -> None:
    """A clustered bar chart with a data label at the end of each bar (the book's mocks draw the axis only)."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title, lines=1)
    label_w, value_w = 118, 60
    left, plot_w = ix + label_w, iw - label_w - value_w
    slot = ih / len(cats)
    top = max(values)
    for i, (name, v) in enumerate(zip(cats, values)):
        by = iy + slot * i + slot * 0.18
        d.text(esc(name), ix, by - 2, label_w - 8, 20, size=SMALL, align="right", valign="middle")
        bw = max(plot_w * v / top, 2)
        d.box("", left, by, bw, slot * 0.64, fill=BLUE, stroke=BLUE, rounded=False)
        d.text(f"{v:,.0f}", left + bw + 4, by - 2, value_w - 4, 20, size=SMALL, valign="middle")


def _page_b1(name: str, failing: bool) -> Diagram:
    g = ctx.values("appB.g1")
    page = "exb1"
    t_table = _title(page, "laborByTitle")
    assert t_table == g["t_table"]
    assert _projections(page, "laborByTitle", "Values") == ["JobTitle", "Manufacturing Hours", "Labor Cost"]
    assert _projections(page, "laborCostCard", "Data") == ["Labor Cost"]
    sort = json.dumps(_visual(page, "laborByTitle")["visual"]["query"]["sortDefinition"])
    assert "Labor Cost" in sort and "Descending" in sort, "the table is sorted by Labor Cost, largest first"
    titles = g["titles"]
    assert [t["cost"] for t in titles] == sorted((t["cost"] for t in titles), reverse=True)
    assert len(titles) == g["n_titles"] and g["n_manuf"] == sum(1 for t in titles if t["hours"] is not None)
    rows = [[t["title"], "" if t["hours"] is None else f"{t['hours']:,.0f}", pbi.amount(t["cost"])] for t in titles]
    hours_total = sum(t["hours"] for t in titles if t["hours"] is not None)
    assert abs(hours_total - g["p"]["hours"]) < 0.5, "the plant's manufacturing hours are the table's total"
    total = ["Total", f"{hours_total:,.0f}", pbi.amount(g["total"])]
    wt = int(max(text_width(r[0], SMALL, False) for r in rows)) + 26
    widths = [wt, 150, 130]
    user, role = ("employee004@charlesriver.example", "Cost Center Managers") if failing else ("employee004@charlesriver.example", "Finance")
    d = Diagram(name)
    t_y = PAD + 28 + 12
    t_h = 16 + 4 + 12 + pbi.ROW + (len(rows) + 1) * pbi.ROW
    c_y, c_h = t_y + t_h + 10, 84
    canvas_h = c_y + c_h + PAD
    pbi.canvas(d, 0, 0, 860, canvas_h)
    _viewing_bar(d, PAD, PAD, 860 - 2 * PAD, user, role)
    left_w = sum(widths) + 12
    if failing:
        text = " ".join(t for t, _ in _paragraphs(page, "exa1Answer"))
        m = re.search(r"column '(\w+)' in table '(\w+)' cannot be found or may not be used in this expression", text)
        assert m, "the model answer's note quotes the engine's message"
        message = f"Column '{m.group(1)}' in table '{m.group(2)}' cannot be found or may not be used in this expression."
        _error_visual(d, PAD, t_y, left_w, t_h, t_table, message)
        _error_visual(d, PAD, c_y, left_w, c_h, None, message)
    else:
        _table_visual(d, PAD, t_y, t_table, ["JobTitle", "Manufacturing Hours", "Labor Cost"], widths, rows,
                      aligns=["left", "right", "right"], title_lines=1, total=total)
        pbi.card(d, PAD, c_y, left_w, c_h, "Labor Cost", pbi.amount(g["total"]))
    bx = PAD + left_w + 12
    _text_box(d, bx, t_y, 860 - PAD - bx, c_y + c_h - t_y, page, "exa1Answer", 3)
    _tabs(page, d, canvas_h + 4)
    return d, canvas_h, g, widths


def if_ab_1_a() -> Diagram:
    """The page Ex B.1 as Finance sees it: the table and the card of Labor Cost, and the model answer's text box."""
    d, canvas_h, g, _ = _page_b1("The Page Ex B.1 as Finance", False)
    _note(d, f"Report view, page Ex B.1, viewed as the Finance role, which has no rules and no column permission. The table is filtered to fiscal "
             f"{g['y']}: {g['w_manuf']} job titles have manufacturing hours, and the other {g['w_other']} have labor time that is all non-manufacturing, so "
             f"their hours are blank and their cost is ${pbi.amount(g['other_cost'])}. The total row and the card agree on ${pbi.amount(g['total'])}. "
             "The text box is the model answer's note, cut to a few lines of each paragraph.", canvas_h + 34)
    return d


def if_ab_1_b() -> Diagram:
    """The same page viewed as the Production Manager after the column permission: the table and the card fail, the Plant page works."""
    d, canvas_h, g, _ = _page_b1("The Page Ex B.1 as the Production Manager", True)
    t3 = ctx.values("ch15.t3")
    data = ctx.data()
    p = g["p"]
    assert abs(t3["card"] - p["ratio"]) < 1e-9, "the Plant page's trailing card is the Production Manager's ratio for the year"
    raw = data.q("SELECT COALESCE(wc.WorkCenterName, '(Blank)'), SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l "
                 "LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID "
                 "LEFT JOIN WorkCenter wc ON wc.WorkCenterID = o.WorkCenterID "
                 "WHERE l.LaborType = 'Direct Manufacturing' AND substr(l.WorkDate, 1, 4) = ? GROUP BY 1 ORDER BY 2 DESC", str(g["y"]))
    assert [n.replace(" Work Center", "") for n, _ in raw if n != "(Blank)"] == [n for n, _ in t3["centers"]]
    direct = sum(v for _, v in raw)
    indirect = data.one("SELECT SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry WHERE LaborType = 'Indirect Manufacturing' "
                        "AND substr(WorkDate, 1, 4) = ?", str(g["y"]))
    assert abs(direct + indirect - p["hours"]) < 0.01, "direct and indirect time are the Production Manager's manufacturing hours"
    # the inset: the Plant page of the same view
    iy = canvas_h + 34 + 22
    pw, ph = 580, 200
    pbi.canvas(d, 0, iy, pw, ph)
    d.text(f"<b>Inset: the Plant page, same view</b>", PAD, iy + 12, pw - 2 * PAD, 20, size=SMALL, color=GRAY)
    pbi.frame(d, PAD, iy + 38, 200, 148, None)
    pbi.card(d, PAD + 6, iy + 44, 188, 64, "Hours per Standard Hour TTM", f"{t3['card']:.2f}")
    pbi.card(d, PAD + 6, iy + 114, 188, 64, "Hours per Standard Hour 2024", f"{t3['first']:.2f}")
    _hbars(d, PAD + 212, iy + 38, pw - 2 * PAD - 212, 148, f"Direct Hours by WorkCenterName, {g['y']}",
           [n.replace(" Work Center", "") for n, _ in raw], [v for _, v in raw])
    cx = pw + 16
    kit.callout(d, f"<b>A correct failure.</b> Only the table and the card, the visuals that read Labor Cost, fail. The text box and the Plant page do not: "
                   f"no measure on the Plant page reads the cost, so its cards and charts still show hours: {p['ratio']:.2f} hours per standard hour "
                   f"on {p['hours']:,.0f} manufacturing hours of the year, {direct:,.0f} of them direct.", cx, iy, 860 - cx, "teal")
    _note(d, f"Report view, page Ex B.1, with the bar above the page naming the user and the role Cost Center Managers. The message is the engine's, as the model "
             f"answer's note records it; Desktop's own wording around it is not verified. Inset: the model answer's Plant page, as the book draws it; direct "
             f"hours by work center add to {direct:,.0f} of the {p['hours']:,.0f} hours, because indirect time ({indirect:,.0f}) has no work center.",
          iy + ph + 10)
    return d


# -- IF-AB-2-A: the result of query (4) ------------------------------------------------------------------------------------------

def if_ab_2_a() -> Diagram:
    """DAX query view, tab Ex B.2: the third query selected, and its nine rows in two panes, as the grid reads before and after scrolling right."""
    from notes import appendix_b as nb
    g = ctx.values("appB.g2")
    data = ctx.data()
    users = nb.users(data)
    assert [(u["upn"], u["cc"]) for u in users] == _security_rows() == nb.SECURITY, "the notes' security table is the model answer's"
    assert len(users) == g["n_users"] == 9
    lines = (MODEL / "DAXQueries" / "Ex B.2.dax").read_text(encoding="utf-8").split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith("// (4)")) + 1          # line numbers count from 1
    end = max(i for i, line in enumerate(lines) if line.strip()) + 1
    assert "\n".join(lines[start - 1:end]).strip() == g["q4"].strip(), "the query is the guide's third query"
    rn = lambda text: next(i for i in range(start, end + 1) if lines[i - 1].strip() == text)     # noqa: E731
    users_at, flag_at = rn("VAR Users ="), rn('"Flag",')
    # The review lists one row per user (round 2 of the review): Users lists each user's cost centers as CostCenterIDs.
    assert '"CostCenterIDs"' in g["q4"], "query (4) returns one row per user"
    width = 772 - 34 - 28
    rows: list[tuple[int | None, str]] = [(n, _fit_dax(lines[n - 1], width)) for n in range(start, users_at + 1)]
    rows.append((None, f"lines {users_at + 1} to {flag_at - 1} not shown: Users lists each user once with an EmployeeID, Matched adds five columns"))
    rows.append((flag_at, _fit_dax(lines[flag_at - 1], width)))
    rows.append((None, f"lines {flag_at + 1} to {end} not shown: the SWITCH that sets the Flag, its three tests and a BLANK"))
    # the nine rows, as the query returns them
    table = []
    for u in users:
        e = u["employee"]
        assert e is not None and nb_flag(e, u["cc"]) is None
        table.append([u["upn"], str(u["cc"]), str(e["id"]), e["name"], e["title"], e["status"], _mdy(e["terminated"]) if e["terminated"] else "",
                      str(e["cc"]), ""])
    assert all(r[6] == "" and r[8] == "" and r[1] == r[7] for r in table)
    cc_head = "[CostCenterIDs]"
    heads = ["Security[UserPrincipalName]", cc_head, "[EmployeeID]", "[EmployeeName]", "[JobTitle]", "[EmploymentStatus]",
             "[TerminationDate]", "[OwnCostCenterID]", "[Flag]"]

    def widths(cols: list[int], pad: float = 14) -> list[float]:
        return [int(max(text_width(heads[c], SMALL, True), max(text_width(r[c], SMALL, False) for r in table))) + pad + 2 for c in cols]

    left_cols, right_cols = [0, 1, 2, 3, 4], [3, 4, 5, 6, 7, 8]
    lw, rw = widths(left_cols), widths(right_cols)
    assert sum(lw) <= 772 and sum(rw) <= 772, (sum(lw), sum(rw))
    row_h = pbi.ROW
    pane_h = row_h + 2 + len(table) * row_h
    d = Diagram("The Result of Query 4 of the Tab Ex B.2")
    height = 96 + 10 + 56 + len(rows) * 20 + 8 + 14 + 24 + pane_h + 18 + 20 + pane_h + 16 + 20 + 14
    win = pbi.window(d, height, view="DAX query", tab="Home", tabs=pbi.QUERY_TABS, panes=[], file=FILE,
                     buttons=["Format", "Comment", "Uncomment", "Find", "Replace", "Command palette"])
    x, w = win.canvas_x + 8, win.canvas_w - 16
    assert w == 772
    sel = range(start, end + 1)
    ed = _editor(d, x, win.top + 10, w, rows, "Ex B.2", 0, selected=sel)
    _scrollbar(d, x + w - 2, ed["top"] + 2, ed["bottom"] - ed["top"] - 4, len(rows), end + 1, start - 1)
    gy = ed["bottom"] + 14
    d.text("<b>Results</b>", x, gy, 120, 22, size=SMALL)
    gy += 24
    g1 = _grid(d, x, gy, [heads[c] for c in left_cols], lw, [[r[c] for c in left_cols] for r in table])
    _column_outline(d, g1, 1, len(table))
    _hscroll(d, x, gy + pane_h + 6, w, 0, 0.62)
    gy2 = gy + pane_h + 18 + 20
    d.text("<i>The same nine rows after scrolling right: columns 4 to 9</i>", x, gy2 - 22, 460, 20, size=SMALL, color=GRAY)
    g2 = _grid(d, x, gy2, [heads[c] for c in right_cols], rw, [[r[c] for c in right_cols] for r in table])
    _column_outline(d, g2, 4, len(table))
    _column_outline(d, g2, 3, len(table))
    _column_outline(d, g2, 5, len(table))
    _hscroll(d, x, gy2 + pane_h + 6, w, 0.38, 0.62)
    d.text(esc(f"9 columns, {len(table)} rows"), x, gy2 + pane_h + 16, 220, 20, size=SMALL, color=GRAY)
    _note(d, f"The tab Ex B.2 with the third query selected and run; the lines in the gaps are left out. The grid is wider than the window, so it is drawn "
             f"twice, before and after scrolling right, with the name and job title repeated. One row for each of the {len(table)} users, in the security table's order. "
             f"Outlined: {cc_head.split('[')[1].rstrip(']')} (first pane) and OwnCostCenterID (second) agree in every row, and TerminationDate and Flag are empty in every row.",
          win.bottom + 10)
    return d


def nb_flag(emp: dict, cc: int) -> str | None:
    """Exercise B.2 (4)'s flag, in the order of the model answer's SWITCH."""
    if emp["status"] != "Active" or emp["terminated"]:
        return "Terminated"
    if emp["cc"] != cc:
        return "Mapped to another cost center"
    return None


# -- IF-AB-2-B: the page Ex B.2 as the Sales Manager ----------------------------------------------------------------------------------

def if_ab_2_b() -> Diagram:
    """The page Ex B.2 viewed as the Sales Manager: every employee of AccessEmployees, the terminated ones with their dates, a scroll bar."""
    from notes import appendix_b as nb
    g = ctx.values("appB.g2")
    data = ctx.data()
    page = "exb2"
    t_table = _title(page, "accessEmployees")
    assert t_table == g["title_table"]
    assert _projections(page, "accessEmployees", "Values") == ["EmployeeName", "JobTitle", "EmploymentStatus", "TerminationDate"]
    employees = sorted(nb.employees(data).values(), key=lambda e: e["name"].casefold())
    total_n = len(employees)
    assert total_n == g["n_employees"] and sum(1 for e in employees if e["terminated"]) == g["n_terminated"]
    assert all((e["status"] != "Active") == bool(e["terminated"]) for e in employees), "a terminated employee has a termination date"
    dated = [i for i, e in enumerate(employees) if e["terminated"]]
    shown = max(16, dated[1] + 2)                 # the top of the list, down to the second terminated employee and a row more
    view = employees[:shown]
    rows = [[e["name"], e["title"], e["status"], _mdy(e["terminated"]) if e["terminated"] else ""] for e in view]
    wn = int(max(text_width(r[0], SMALL, False) for r in rows)) + 26
    wt = int(max(text_width(r[1], SMALL, False) for r in rows)) + 26
    widths = [wn, wt, 136, 118, 16]                # the last column is the room of the scroll bar
    left_w = sum(widths) + 12
    t_y = PAD + 28 + 12
    t_h = 16 + 4 + 12 + pbi.ROW + len(rows) * pbi.ROW
    canvas_h = t_y + t_h + PAD
    d = Diagram("The Page Ex B.2 as the Sales Manager")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    _viewing_bar(d, PAD, PAD, 860 - 2 * PAD, "employee006@charlesriver.example", "Cost Center Managers")
    t = _table_visual(d, PAD, t_y, t_table, ["EmployeeName", "JobTitle", "EmploymentStatus", "TerminationDate", ""], widths,
                      [r + [""] for r in rows], aligns=["left", "left", "left", "right", "left"], title_lines=1)
    _scrollbar(d, PAD + sum(widths) + 12 - 2, t["top"] + pbi.ROW, len(rows) * pbi.ROW, shown, total_n)
    for r, e in enumerate(view):
        if e["terminated"]:
            x0, y0, _, _ = t["geometry"][(r, 0)]
            d.outline(x0 + 1.5, y0 + 1.5, sum(widths) - 3, pbi.ROW - 3, CORAL, width=2.5, front=True)
    bx = PAD + left_w + 12
    _text_box(d, bx, t_y, 860 - PAD - bx, t_h, page, "exa2Answer", 3)
    _tabs(page, d, canvas_h + 4)
    n_dated = sum(1 for r in rows if r[3])
    _note(d, f"Report view, page Ex B.2, viewed as the Sales Manager in the role Cost Center Managers. The table lists the first {shown} of the {total_n} rows of "
             f"AccessEmployees, in the order of its first column, which a table has without a sort of its own; the scroll bar shows how long the list is. "
             f"Outlined: the {nb.word(n_dated)} terminated employees in view, whose dates show, as do the other {nb.word(g['n_terminated'] - n_dated)} below. No rule filters a table that no "
             f"relationship reaches, so the Sales Manager sees every row, while Employee itself shows only the {g['s_employees']} of the Sales cost center. "
             "The text box is the model answer's note, cut to a few lines of each paragraph.", canvas_h + 34)
    return d


FIGURES = {"IF-AB-0-A": if_ab_0_a, "IF-AB-0-B": if_ab_0_b, "IF-AB-1-A": if_ab_1_a, "IF-AB-1-B": if_ab_1_b,
           "IF-AB-2-A": if_ab_2_a, "IF-AB-2-B": if_ab_2_b}
