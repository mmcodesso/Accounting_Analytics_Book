"""Instructor figures of the Part III case (guides in facts/instructor/guides/case-part-3/).

Five diagrams, two DB Browser mocks and two charts.  The mocks quote their query from the model answer script
(outputs/companion/solutions/PartIII-case-sql/Case.sql, the text the guides quote) at the editor line where it sits in that
script, and run it read-only, so the grid and the row count come from the data; the views the two queries read are created
as TEMP views on the read-only connection for the length of the run.  The numbers in the diagrams and the charts come from
the guides' own contexts (case3.r1 to case3.r5, case3.g1 to case3.g4) or from read-only queries; the structure of the case
(its requirements, chapter tags, the memo's sections and the five exhibits) is read from cases/part-3-case.qmd.
"""

from __future__ import annotations

import re
from datetime import date

import ctx
import dbbrowser as db
import kit
from check_figures import text_width
from data import connection
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, BODY, CORAL, CORAL_TINT, FONT, GRAY, GRAY_TINT, HEAD, INK, ROW_H,
                    RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

CASE = ctx.REPO / "cases" / "part-3-case.qmd"
GUIDES = ctx.REPO / "facts" / "instructor" / "guides" / "case-part-3"
SOLUTION = ctx.REPO / "outputs" / "companion" / "solutions" / "PartIII-case-sql" / "Case.sql"
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
               "December"]
MINUS = "−"
STRAIGHT = "edgeStyle=none;"
DASHED_CORAL = "rounded=0;html=1;fillColor=none;strokeColor=%s;strokeWidth=2;dashed=1;dashPattern=6 3;" % CORAL
GRID_W = 820            # the 860 px frame less the row-number column of the result grid
CELL_PAD = 20           # a cell wraps its text within about 12 px of its width, so leave room


# -- shared drawing helpers -------------------------------------------------------------------------------------------------------

def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis."""
    if text_width(esc(text), size, bold) <= width - margin:
        return text
    while text and text_width(esc(text + "…"), size, bold) > width - margin:
        text = text[:-1]
    return text.rstrip() + "…"


def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860, gap: float = 0) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    y += gap
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def _money(x: float, places: int = 2) -> str:
    return f"{x:,.{places}f}"


def _signed(x: float, places: int = 2) -> str:
    return (MINUS if x < 0 else "+") + f"{abs(x):,.{places}f}"


def _day_text(iso: str, year: bool = True) -> str:
    """'2026-12-11' -> 'December 11, 2026' (no break inside the date)."""
    text = f"{MONTH_NAMES[int(iso[5:7]) - 1]} {int(iso[8:10])}" + (f", {iso[:4]}" if year else "")
    return f'<span style="white-space:nowrap">{text}</span>'


def _plain_day(iso: str) -> str:
    return f"{MONTH_NAMES[int(iso[5:7]) - 1]} {int(iso[8:10])}, {iso[:4]}"


def _nb(text: str) -> str:
    return text.replace(" ", "&nbsp;")


# -- what the case text says ------------------------------------------------------------------------------------------------------

def _case_text() -> str:
    return CASE.read_text(encoding="utf-8")


def _requirements() -> list[dict]:
    """Each requirement of the case text: number, title, the chapter tag ('Chapters 9 and 10', or None) and the perspective."""
    found = []
    for m in re.finditer(r"^\*\*Requirement (\d+): ([^*]+?)\.\*\*", _case_text(), re.M):
        title, tag, persp = m.group(2), None, None
        parts = re.fullmatch(r"(.+?) \(([^)]*)\)", title)
        if parts:
            title = parts.group(1)
            bits = [b.strip() for b in parts.group(2).split(";")]
            if bits[0].startswith("Chapter"):
                tag = re.sub(r", with the planning of ", " with ", bits[0])
                persp = bits[1] if len(bits) > 1 else None
        found.append(dict(n=int(m.group(1)), title=title, tag=tag, perspective=persp))
    assert [r["n"] for r in found] == list(range(1, len(found) + 1)), found
    return found


def _requirement_block(n: int) -> str:
    text = _case_text()
    start = text.index(f"**Requirement {n}:")
    nxt = re.search(r"^\*\*(?:Requirement \d+|Deliverable)", text[start + 5:], re.M)
    return text[start:start + 5 + nxt.start()]


def _memo_sections() -> list[str]:
    """The three headed sections of the memo, as Requirement 6 names them."""
    block = _requirement_block(6)
    return re.findall(r"^- \*\*([A-Z][A-Za-z ]+):\*\*", block, re.M)


def _exhibits() -> list[str]:
    """The exhibits of the Deliverable, 'the corroboration matrix, output against hours, ...'."""
    m = re.search(r"appendix of exhibits: (.+?)\.\s", _case_text())
    items = re.split(r", (?:and )?", m.group(1))
    return [re.sub(r"^(?:and )?the ", "", i).strip() for i in items]


def _exhibit_makers(exhibits: list[str]) -> list[int]:
    """The requirement that makes each exhibit: the one whose text asks for it (a pattern that must be in that requirement)."""
    asks = [(r"corroboration matrix", 2, r"corroboration matrix"),
            (r"output against hours", 3, r"Compare output with hours"),
            (r"bridge", 3, r"Bridge the growth"),
            (r"plan against", 4, r"Scenarios CTE"),
            (r"adjustments", 5, r"proposed adjustments")]
    makers = []
    for name in exhibits:
        hit = [(n, ask) for pat, n, ask in asks if re.search(pat, name)]
        assert len(hit) == 1, name
        n, ask = hit[0]
        assert re.search(ask, _requirement_block(n)), (name, n, ask)
        makers.append(n)
    return makers


def _memo_table() -> dict[str, tuple[list[int], list[int]]]:
    """Section -> (requirements, exhibits) from the table of Requirement 6, Step 2 of the guide."""
    text = (GUIDES / "req-6-write-the-decision-memo.md").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^\| (Auditing|Managerial accounting|Financial reporting) \|.*\| (Requirements? [\d and]+) \| ([\d, ]+) \|$",
                         text, re.M):
        out[m.group(1)] = ([int(n) for n in re.findall(r"\d+", m.group(2))], [int(n) for n in re.findall(r"\d+", m.group(3))])
    return out


def _recommendation_sources() -> list[int]:
    """The requirements behind the recommendation: the 'R2 to R5' of the guide's table of expected results."""
    text = (GUIDES / "req-6-write-the-decision-memo.md").read_text(encoding="utf-8")
    m = re.search(r"^\| Recommendation \|.*\| R(\d) to R(\d) \|$", text, re.M)
    return list(range(int(m.group(1)), int(m.group(2)) + 1))


def _who(nums: list[int]) -> str:
    """'Requirement 2', 'Requirements 3 and 4', 'Requirements 2 to 5'."""
    if len(nums) == 1:
        return f"Requirement {nums[0]}"
    if nums == list(range(nums[0], nums[-1] + 1)) and len(nums) > 2:
        return f"Requirements {nums[0]} to {nums[-1]}"
    return f"Requirements {' and '.join(map(str, nums))}"


# -- IF-C3-0-A: how the six requirements build the memo -----------------------------------------------------------------------------

def if_c3_0_a() -> Diagram:
    """The requirements with their chapters, the script feeding all, the memo's sections and the five exhibits."""
    reqs = _requirements()
    sections = _memo_sections()
    exhibits = _exhibits()
    makers = _exhibit_makers(exhibits)
    table = _memo_table()
    assert len(reqs) == 6 and len(sections) == 3 and len(exhibits) == 5 and set(table) == set(sections), (sections, exhibits, table)
    by_persp = {s.lower(): s for s in sections}
    assert all(reqs[k]["perspective"] in by_persp for k in (1, 2, 3, 4)), reqs
    feeders = {s: [r["n"] for r in reqs[1:5] if by_persp[r["perspective"]] == s] for s in sections}
    assert all(feeders[s] == table[s][0] for s in sections), (feeders, table)        # the guide's table agrees with the case text
    d = Diagram("How the Six Requirements Build the Memo and Its Appendix")
    W, GAP, TOP, H = 130.0, 16.0, 52.0, 118.0
    xs = [i * (W + GAP) for i in range(6)]
    cx = [x + W / 2 for x in xs]
    d.text("<b>Requirement 1's script and its views feed every other requirement</b>", 110, 0, 640, 20, size=SMALL, align="center")
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
    for name in sections:
        a, b = min(feeders[name]) - 1, max(feeders[name]) - 1
        assert b - a + 1 == len(feeders[name]), "a section's requirements are side by side"
        sx, sw = xs[a], xs[b] + W - xs[a]
        who = " and ".join(str(n) for n in feeders[name])
        targets[name] = (d.box(f"<b>{esc(name)}</b><br><i>from Requirement{'s' if len(feeders[name]) > 1 else ''} {who}</i>", sx, sy,
                               sw, sh, fill=WHITE, stroke=BLUE, stroke_width=1.5), sx, sw)
    ox, ow = xs[5], W - 10
    opening = d.box("<b>Opening and recommendation</b><br><i>written in Requirement 6</i>", ox, sy, ow, sh, fill=WHITE, stroke=BLUE,
                    stroke_width=1.5, size=SMALL)
    for r in reqs[1:5]:
        tid, sx, sw = targets[by_persp[r["perspective"]]]
        d.arrow(req_ids[r["n"] - 1], tid, exit=(0.5, 1), entry=((cx[r["n"] - 1] - sx) / sw, 0), meta=STRAIGHT)
    d.arrow(req_ids[5], opening, exit=(0.5, 1), entry=((cx[5] - ox) / ow, 0), meta=STRAIGHT)
    # Requirement 1 also goes with the memo.
    d.arrow(req_ids[0], frame, exit=(0.5, 1), entry=(0, 0.35), meta="edgeStyle=orthogonalEdgeStyle;")
    d.text("Case.sql is submitted with the memo", 0, fy + fh / 2 + 18, 118, 52, size=SMALL, color=GRAY)
    # The appendix and its five exhibits.
    ay = fy + fh + 40
    gap_x, ew = 12.0, (860 - 12.0 * 4) / 5
    d.box("", 0, ay, 860, 136, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False, dashed=True)
    d.text("<b>The one-page appendix</b> (Requirement 6): five numbered exhibits, each made in an earlier requirement", 10, ay + 4, 800,
           22, size=SMALL)
    for k, name in enumerate(exhibits):
        ex = k * (ew + gap_x)
        label = name[0].upper() + name[1:]
        assert kit.height_for(f"<b>Exhibit {k + 1}</b><br>{esc(label)}", ew - 12, SMALL) <= 64, label
        d.box(f"<b>Exhibit {k + 1}</b><br>{esc(label)}", ex + 6, ay + 30, ew - 12, 64, fill=TEAL_TINT, stroke=TEAL,
              stroke_width=1.5, size=SMALL)
        d.box(f"<b>from Requirement {makers[k]}</b>", ex + 6, ay + 102, ew - 12, 24, fill=BLUE_TINT, stroke=BLUE, size=SMALL)
    app = d.container(0, ay, 860, 136)
    d.arrow(app, frame, exit=(0.5, 0), entry=((430 - fx) / fw, 1), meta=STRAIGHT)
    d.text("each exhibit is cited in the memo", 442, fy + fh + 8, 260, 22, size=SMALL, valign="middle")
    by_maker: dict[int, list[int]] = {}
    for k, n in enumerate(makers):
        by_maker.setdefault(n, []).append(k + 1)
    parts = [f"Requirement&nbsp;{n} makes {'Exhibit' if len(ks) == 1 else 'Exhibits'}&nbsp;{' and '.join(map(str, ks))}"
             for n, ks in sorted(by_maker.items())]
    made = ", ".join(parts[:-1]) + f", and {parts[-1]}"
    _note(d, "Requirements 2 to 5 each supply the section named in their perspective; the arrows into a section show which "
             "requirements it draws on. Requirement 6 writes the opening and the recommendation and assembles the appendix. "
             f"{made}.", ay + 146)
    return d


# -- IF-C3-0-B: the three calendars --------------------------------------------------------------------------------------------------

def if_c3_0_b() -> Diagram:
    """Time records by work date, payroll and the ledger by pay date, output by completion date, on one axis of years."""
    data = ctx.data()
    r3 = ctx.values("case3.r3")
    g3 = ctx.values("case3.g3")
    first_year, last_year = data.F, data.C
    start, end = date(first_year, 1, 1), date(last_year, 12, 31)
    total_days = (end - start).days + 1
    first_work, last_work = data.q("SELECT MIN(WorkDate), MAX(WorkDate) FROM TimeClockEntry")[0]
    assert last_work == r3["cutoff"], (last_work, r3["cutoff"])
    assert data.one("SELECT COUNT(*) FROM TimeClockEntry WHERE strftime('%w', WorkDate) IN ('0', '6')") == 0, \
        "time records have no weekend work dates"
    a1090 = data.account("1090")
    pay_dates = [r[0] for r in data.q("SELECT DISTINCT PostingDate FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = "
                                      f"'PayrollSummary' AND {data.no_closes()} ORDER BY 1", a1090)]
    by_year = {y: sum(1 for p in pay_dates if p[:4] == str(y)) for y in range(first_year, last_year + 1)}
    assert by_year[first_year] == r3["lf"]["paydates"] and by_year[last_year] == r3["lc"]["paydates"], (by_year, r3["lf"], r3["lc"])
    first_done, last_done = data.q("SELECT MIN(CompletionDate), MAX(CompletionDate) FROM ProductionCompletion")[0]
    assert last_done == end.isoformat(), "output runs to the year-end"
    lead, weekend, completions = g3["limits"]
    assert 0 < weekend < completions, g3["limits"]
    gap_days = (end - date.fromisoformat(last_work)).days

    x0, x1 = 176.0, 756.0
    x_of = lambda iso: x0 + (date.fromisoformat(iso) - start).days / total_days * (x1 - x0)
    d = Diagram("The Three Calendars of the Case")
    # the years across the top, quarters as light lines
    for y in range(first_year, last_year + 1):
        a, b = x_of(f"{y}-01-01"), (x_of(f"{y + 1}-01-01") if y < last_year else x1)
        d.box(f"<b>{y}</b>", a, 0, b - a, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False)
    lanes = [40.0, 116.0, 192.0]
    LH = 64.0
    for ly in lanes:
        d.box("", x0, ly, x1 - x0, LH, fill=WHITE, stroke=RULE, rounded=False)
    for y in range(first_year, last_year + 1):
        for q in range(4):
            xq = x_of(f"{y}-{q * 3 + 1:02d}-01")
            heavy = q == 0
            d.box("", xq - (0.75 if heavy else 0.5), 28, 1.5 if heavy else 1, lanes[-1] + LH - 28, fill=GRAY if heavy else RULE,
                  stroke=GRAY if heavy else RULE, rounded=False)
    names = [("Time records", "follow the work date"), ("Payroll and the ledger", "follow the pay date"),
             ("Output", "follows the completion date")]
    for ly, (head, sub) in zip(lanes, names):
        d.text(f"<b>{head}</b><br>{sub}", 0, ly + 8, 168, 48, size=SMALL)
    # lane 1: time records, from the first work date to the last
    ly = lanes[0]
    xl_, xr = x_of(first_work), x_of(last_work)
    d.box("", xl_, ly + 34, xr - xl_, 20, fill=BLUE, stroke=BLUE, rounded=False)
    d.text("weekdays only: no time record on a weekend", xl_ + 6, ly + 34, 330, 20, size=SMALL, color=WHITE, valign="middle")
    # lane 2: the pay dates charged to 1090, one tick each, and the count of each year
    ly = lanes[1]
    for p in pay_dates:
        d.box("", x_of(p) - 1, ly + 34, 2, 20, fill=TEAL, stroke=TEAL, rounded=False)
    for y in range(first_year, last_year + 1):
        a, b = x_of(f"{y}-01-01"), (x_of(f"{y + 1}-01-01") if y < last_year else x_of(last_work) - 6)
        strong = y in (first_year, last_year)
        d.box(f"<b>{by_year[y]} payroll postings<br>to 1090</b>" if strong else f"{by_year[y]} payroll postings<br>to 1090", a + 4, ly + 2, b - a - 8, 31,
              fill=TEAL_TINT if strong else WHITE, stroke=TEAL if strong else WHITE, size=SMALL, rounded=False,
              stroke_width=1.5 if strong else 1)
    # lane 3: output, from the first completion to the year-end
    ly = lanes[2]
    xa, xb = x_of(first_done), x1
    d.box("", xa, ly + 34, xb - xa, 20, fill=GRAY, stroke=GRAY, rounded=False)
    d.text(f"weekends included: {weekend:,} of {completions:,} completions of {last_year} fall on a Saturday or Sunday", xa + 6, ly + 34,
           xb - xa - 12, 20, size=SMALL, color=WHITE, valign="middle")
    # the last day with time records, through the three lanes, and the year-end at the right
    cut = x_of(last_work)
    d.vertex("", DASHED_CORAL, cut - 1, 28, 2, lanes[-1] + LH - 28)
    said = f"<b>Last day with time records:</b> {_plain_day(last_work)}"
    lw = text_width(said, SMALL, False) + 16
    d.box(said, cut - 6 - lw, lanes[0] + 8, lw, 20, fill=WHITE, stroke=WHITE, color=CORAL, size=SMALL, rounded=False)
    d.text(f"<b>Year-end</b><br>{_day_text(end.isoformat())}", x1 + 8, lanes[2] + 30, 860 - x1 - 8, 36, size=SMALL, color=GRAY)
    # the bracket under the lanes
    by = lanes[-1] + LH + 12
    d.box("", x0, by, xr - x0, 2, fill=INK, stroke=INK, rounded=False)
    d.box("", x0, by, 2, 10, fill=INK, stroke=INK, rounded=False)
    d.box("", xr - 2, by, 2, 10, fill=INK, stroke=INK, rounded=False)
    bottom = kit.callout(d, "<b>Compare hours with output on work dates</b>, counting output only up to the last day with time records. "
                            "<b>Measure cost on the ledger</b>, by pay date: never divide the cost of a pay year by the hours of a work year.",
                         x0, by + 14, 860 - x0, "amber")
    _note(d, f"Time records end {gap_days} days before the year-end. The first year has {by_year[last_year] - by_year[first_year]} fewer payroll postings "
             f"charged to account 1090 than the last: {by_year[first_year]} against {by_year[last_year]}. The first payroll of the first year posted to 5080.", bottom, gap=6)
    return d


# -- the SQL mocks -------------------------------------------------------------------------------------------------------------------

def _script_text() -> str:
    if not SOLUTION.is_file():
        raise SystemExit(f"Model answer not found: {SOLUTION} (build the solutions first)")
    return SOLUTION.read_text(encoding="utf-8")


def _solution(wanted: str) -> tuple[str, str, int]:
    """The comment lines, the SQL and the editor line of the first comment line of the query of Case.sql whose comment contains
    `wanted`.  The `-- Result: N rows` remark that the model answer appends to a query's last line is left out: a student
    types the query without it."""
    lines = _script_text().split("\n")
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    for number, line in enumerate(lines + [""], 1):
        if line.strip():
            if not current:
                start = number
            current.append(line)
        elif current:
            blocks.append((start, current))
            current = []
    found = []
    for first, block in blocks:
        if block[0].lstrip().startswith("/*"):
            continue
        k = 0
        while k < len(block) and block[k].startswith("--"):
            k += 1
        comment, sql = block[:k], block[k:]
        if k and sql and wanted in "\n".join(comment):
            sql[-1] = re.sub(r"\s*--\s*Result:.*$", "", sql[-1])
            found.append(("\n".join(comment), "\n".join(sql), first))
    if len(found) != 1:
        raise SystemExit(f"Case.sql: {len(found)} queries have a comment containing {wanted!r} (expected one)")
    return found[0]


def _temp_view(name: str) -> str:
    """The CREATE VIEW statement of Case.sql for `name`, as a TEMP view: the model answer writes the view into the working
    copy, the figure's read-only run keeps it in the connection's temporary database."""
    m = re.search(rf"CREATE VIEW {name} AS\n(.*?);\s*--\s*Result", _script_text(), re.S)
    if not m:
        raise SystemExit(f"Case.sql: no CREATE VIEW {name}")
    return f"CREATE TEMP VIEW {name} AS\n{m.group(1)}"


class _Views:
    """The saved views of Case.sql created as TEMP views for the length of a block, and dropped again (the connection is shared
    with other units' figures, which create views of the same names)."""

    def __init__(self, *names: str):
        self.names = names

    def __enter__(self):
        con = connection()
        for name in self.names:
            con.execute(f"DROP VIEW IF EXISTS temp.{name}")
        for name in self.names:
            con.execute(_temp_view(name))
        return self

    def __exit__(self, *exc):
        con = connection()
        for name in reversed(self.names):
            con.execute(f"DROP VIEW IF EXISTS temp.{name}")


def _run(sql: str) -> tuple[list[str], list[tuple]]:
    cursor = connection().execute(sql)
    return [c[0] for c in cursor.description], cursor.fetchall()


def _widths(headers: list[str], rows: list[tuple], total: float = GRID_W, stretch: float = 1.5,
            pad: float = CELL_PAD + 2) -> list[float]:
    """Column widths that fit each heading and value, shrunk (the widest column first, its text then clipped) to fit the
    frame, or stretched a little when the result is narrow."""
    natural = []
    for c, head in enumerate(headers):
        w = text_width(f"<b>{esc(head)}</b>", SMALL, True)
        for row in rows:
            w = max(w, text_width(db.cell(row[c])[0], SMALL, False))
        natural.append(w + pad)
    if sum(natural) <= total:
        scale = min(total / sum(natural), stretch)
        return _fit([round(w * scale) for w in natural], total)
    widths = list(natural)
    floor = [text_width(f"<b>{esc(h)}</b>", SMALL, True) + pad for h in headers]
    while sum(widths) > total:
        i = max(range(len(widths)), key=lambda c: widths[c] - floor[c])
        assert widths[i] > floor[i], "the result does not fit the frame"
        widths[i] = max(floor[i], widths[i] - min(8, sum(widths) - total))
    return _fit([round(w) for w in widths], total)


def _fit(widths: list[int], total: float) -> list[int]:
    """Take any excess left by rounding off the widest column, so the grid never passes the frame."""
    excess = sum(widths) - total
    if excess > 0:
        widths[max(range(len(widths)), key=lambda c: widths[c])] -= int(excess + 0.999)
    return widths


def _mock(d: Diagram, wanted: str, shown: slice | None = None, lines: slice | None = None, cols: slice | None = None) -> dict:
    """The Execute SQL tab with the query of Case.sql whose comment contains `wanted`, as a reader sees it after selecting the
    query and clicking Execute all/selected SQL.  The editor is scrolled to the query: it shows the comment lines and the query
    at their line numbers in the script, or only `lines` of them (the line numbers kept).  `shown` draws only some rows of the
    result, as a grid scrolled to them (the rows keep their numbers); `cols` only some columns, as a grid scrolled right (the
    row-number column stays).  Returns the grid and editor geometry."""
    comment_text, sql, line = _solution(wanted)
    with _Views("SurgeDays", "PlantEntries"):
        headers, rows = _run(sql)
    n_comment = comment_text.count("\n") + 1
    y = db.window(d)
    editor_top = y
    full = f"{comment_text}\n{sql}".split("\n")
    start = (lines.start or 0) if lines else 0
    drawn = full[lines] if lines else full
    y = db.editor(d, 0, y, 860, "\n".join(drawn), tab="Case.sql", first_line=line + start,
                  selection=slice(max(n_comment - start, 0), None)) + 8
    visible = rows[shown] if shown else rows
    first = (shown.start or 0) + 1 if shown else 1
    cols = cols or slice(0, len(headers))
    heads, part = headers[cols], [row[cols] for row in visible]
    widths = _widths(heads, part)
    clipped = [tuple(_clip(v, w, margin=CELL_PAD) if isinstance(v, str) else v for v, w in zip(row, widths)) for row in part]
    geometry = db.results(d, 0, y, heads, widths, clipped, first=first)
    y += (len(visible) + 1) * ROW_H + 8
    bottom = db.message(d, 0, y, 860, len(rows), sql.split("\n")[0], line=line + n_comment)
    return dict(headers=heads, rows=rows, geometry=geometry, bottom=bottom, sql=sql, editor_top=editor_top)


def _outline_cells(d: Diagram, mock: dict, first: tuple[int, int], last: tuple[int, int], inset: float = 0) -> None:
    """A coral outline around the cells from (row, column) first to last of the drawn grid (row -1 is the heading), inset so
    that two outlines on rows with one row between them stay apart."""
    geo = mock["geometry"]
    x0, y0, _, _ = geo[first]
    x1, y1, w1, h1 = geo[last]
    left, right = x0 - 1 + inset, min(860.0, x1 + w1 + 1 - inset)       # the grid can fill the frame to its edge
    d.outline(left, y0 - 1 + inset, right - left, y1 + h1 - y0 + 2 - 2 * inset, CORAL, width=2.5, front=True)


# -- IF-C3-1-A: the two views reconciled to Tutorial 12.3 ----------------------------------------------------------------------------

def if_c3_1_a() -> Diagram:
    """Requirement 1, Step 7: the reconciliation query, the surge days and surge entries of each year outlined."""
    g1 = ctx.values("case3.g1")
    d = Diagram("The Two Views Reconciled to Tutorial 12.3")
    mock = _mock(d, "the two views reconciled")
    assert mock["headers"] == ["WorkYear", "SurgeDays", "SurgeEntries", "OrdinaryDays", "OrdinaryEntries"], mock["headers"]
    rows = mock["rows"]
    assert [tuple(r) for r in rows] == [tuple(r) for r in g1["reconcile"]] and len(rows) == 3, "the grid differs from the guide's"
    _outline_cells(d, mock, (-1, 1), (len(rows) - 1, 2))
    days = ", ".join(f"{r[1]}" for r in rows[:-1]) + f" and {rows[-1][1]}"
    entries = ", ".join(f"{r[2]:,}" for r in rows[:-1]) + f" and {rows[-1][2]:,}"
    years = ", ".join(r[0] for r in rows[:-1]) + f" and {rows[-1][0]}"
    _note(d, f"Outlined: SurgeDays and SurgeEntries, the figures that test H8 of Tutorial 12.3 counts: {days} surge days and {entries} "
             f"surge entries in {years}. The two views must give them before any later test relies on them. The query reads the views "
             f"SurgeDays and PlantEntries, which the script saved earlier with Write Changes.", mock["bottom"], gap=6)
    return d


# -- IF-C3-1-B: the dispositions of the attendance exceptions ------------------------------------------------------------------------

def if_c3_1_b() -> Diagram:
    """Requirement 1, Step 5: each attendance exception with its clock entry and a disposition; the misattributed rows outlined."""
    g1 = ctx.values("case3.g1")
    d = Diagram("The Dispositions of the Attendance Exceptions")
    # the grid is scrolled right, so the columns that show the misattribution and its disposition fit the frame
    comment_text, sql, _ = _solution("each attendance exception against")
    head_all, rows_all = _run(sql)
    assert head_all[:3] == ["AttendanceExceptionID", "ExceptionType", "WorkDate"], head_all
    assert [r[0] for r in rows_all] == list(range(1, len(rows_all) + 1)), "the row numbers are the AttendanceExceptionIDs"
    first_visible = 3
    mock = _mock(d, "each attendance exception against", lines=slice(5, 15), cols=slice(first_visible, None))
    rows = mock["rows"]
    heads = mock["headers"]
    assert heads == ["EmployeeID", "EntryEmployeeID", "TimeClockEntryID", "ClockStatus", "Disposition"], heads
    wrong = [i for i, r in enumerate(rows) if r[3] != r[4]]
    assert wrong and all(rows[i][-1].startswith("Names another employee") for i in wrong), wrong
    count = {label.split(" (")[0]: n for label, n in g1["disp"]}              # the guide's disposition counts by label
    assert len(wrong) == count["Names another employee"] and len(rows) == g1["n"]["dispositions"], (wrong, g1["disp"])
    ids = [rows[i][0] for i in wrong]
    groups, cur = [], [wrong[0]]
    for i in wrong[1:]:
        if i == cur[-1] + 1:
            cur.append(i)
        else:
            groups.append(cur)
            cur = [i]
    groups.append(cur)
    cols = len(heads) - 1
    mock_geo = dict(geometry=mock["geometry"])
    # the grid drawn starts at the column after the hidden three, so its columns are numbered from 0: EmployeeID, EntryEmployeeID, ..., Disposition
    for g in groups:
        _outline_cells(d, mock_geo, (g[0], 0), (g[-1], cols), inset=1.5)
    named = sorted({r[3] for r in (rows[i] for i in wrong)})
    owners = sorted({r[4] for r in (rows[i] for i in wrong)})
    assert len(named) == 1 and len(owners) == 1, (named, owners)
    assert not any(r[-1].startswith("Dated differently") for r in rows), "no exception carries another date than its entry"
    ids_text = ", ".join(f"{i}" for i in ids[:-1]) + f" and {ids[-1]}"
    _note(d, f"The grid is scrolled right, so its row numbers are the AttendanceExceptionIDs. Outlined: exceptions {ids_text}, which name "
             f"employee {named[0]} on clock entries that belong to employee {owners[0]}: the report misattributes its own rows, and none carries "
             f"another date. The others are {count['Isolated']} isolated and {count['Paid on a Pending entry']} paid on a "
             f"Pending entry.", mock["bottom"], gap=6)
    return d


# -- IF-C3-2-A: the corroboration matrix --------------------------------------------------------------------------------------------

def if_c3_2_a() -> Diagram:
    """The nine tests of Requirement 2 and the output comparison of Requirement 3, each with one result mark and the grade for
    independence of its record."""
    r2, r3 = ctx.values("case3.r2"), ctx.values("case3.r3")
    over_weeks, center_over = r2["over_weeks"], r2["center_over"]
    assert over_weeks and center_over >= len(over_weeks), (over_weeks, center_over)
    s, o, plant, meals, equal, cite = r2["s"], r2["o"], r2["plant"], r2["meals"], r2["equal"], r2["cite"]
    boss = r2["creator_title"]
    last_load = r2["load"][-1]
    surge, other = r3["surge"], r3["other"]
    assert surge["next"] < other["next"] and surge["ratio"] < other["ratio"], "surge weeks complete less per hour, and so do the weeks after"
    assert meals["Surge"][0] == meals["Surge"][1] and equal["Surge"][1] == 0 and cite["Surge"]["cited"] == cite["Surge"]["ended"], r2
    assert last_load[0] < last_load[1] and r2["maintenance"] and r2["reduced"], r2["load"]
    sup, con, sil = "support", "contradict", "silent"
    # (test, result column, source of the record, evidence)
    rows = [
        ("Attendance", sup, "clock", f"All {plant} hourly employees present on each of {s['days']} surge days, and on "
                                    f"{o['all_present']} of {o['days']} ordinary days"),
        ("Punches", sup, "clock", f"Badge punches on every entry, with meal punches on all {meals['Surge'][0]:,} surge entries; "
                                  "they repeat the clock's own times"),
        ("Clock-in times", con, "clock", f"{s['clock_ins']:.1f} different clock-in times a day on surge days against "
                                          f"{o['clock_ins']:.1f} on ordinary days; {s['largest']:.0f} employees share one"),
        ("Roster against clock", con, "both", f"Rostered {r2['rostered']:g} hours, clocked {r2['clocked']:g}: roster equals clock on "
                                              f"{equal['Surge'][1]} of {equal['Surge'][0]:,} surge entries"),
        ("Overtime approvals", con, "boss", f"{cite['Surge']['cited']:,} of {cite['Surge']['approvals']:,} surge approvals cite an "
                                            f"operation, all already ended; all approved by the {boss}"),
        ("Planned load", con, "outside", f"Surge weeks {last_load[0]:.2f} of capacity against {last_load[1]:.2f} for others in "
                                         f"{ctx.data().C}; yet {len(over_weeks)} surge weeks and {center_over} work-center weeks over it"),
        ("Calendar", con, "outside", f"Every surge day is a working day; {r2['maintenance']} had maintenance and {r2['reduced']} reduced "
                                     "capacity at a work center"),
        ("Output", con, "outside", f"Surge weeks completed {surge['ratio']:.2f} standard hours per hour clocked against "
                                   f"{other['ratio']:.2f}; the following weeks completed less"),
        ("Absences", sil, "none", "None recorded in Manufacturing in any year"),
    ]
    assert all(src != "outside" or res != sup for _, res, src, _ in rows) and all(src in ("clock", "both") for _, res, src, _ in rows if res == sup), \
        "every record that supports the hours comes from the time clock"
    grade = {"clock": ("✕ No: time clock", CORAL_TINT, CORAL), "both": (f"✕ No: {boss} and time clock", CORAL_TINT, CORAL),
             "boss": (f"✕ No: {boss}", CORAL_TINT, CORAL), "outside": ("– Not established: outside the clock", AMBER_TINT, AMBER),
             "none": ("– Nothing to grade", GRAY_TINT, GRAY)}
    marks = {sup: (1, TEAL_TINT, TEAL), con: (2, CORAL_TINT, CORAL), sil: (3, GRAY_TINT, GRAY)}
    widths = [152, 66, 108, 58, 150, 326]
    xs = [0.0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    d = Diagram("The Corroboration Matrix")
    heads = ["Test", "Supports", "Contradicts or unexplained", f"Silent",
             f"Independent of the {boss} and the time clock?", "What the test found"]
    head_h = max(kit.height_for(f"<b>{h}</b>", w, SMALL) for h, w in zip(heads, widths))
    for h, x, w in zip(heads, xs, widths):
        d.box(f"<b>{esc(h)}</b>", x, 0, w, head_h, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False)
    y = head_h
    for test, result, source, evidence in rows:
        h = max(34.0, kit.height_for(esc(evidence), widths[5], SMALL, pad=10), kit.height_for(esc(grade[source][0]), widths[4], SMALL, pad=10))
        d.box(f"<b>{esc(test)}</b>", xs[0], y, widths[0], h, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
        for k in (1, 2, 3):
            column, fill, stroke = marks[[sup, con, sil][k - 1]]
            on = column == marks[result][0]
            d.box("<b>●</b>" if on else "", xs[k], y, widths[k], h, fill=fill if on else WHITE, stroke=stroke if on else RULE,
                  color=stroke, size=20, rounded=False, stroke_width=1.5 if on else 1)
        text, fill, stroke = grade[source]
        d.box(f"<b>{esc(text.split(':')[0])}</b>{esc(':' + text.split(':', 1)[1]) if ':' in text else ''}", xs[4], y, widths[4], h,
              fill=fill, stroke=stroke, color=INK, size=SMALL, rounded=False, align="left", stroke_width=1.5)
        d.box(esc(evidence), xs[5], y, widths[5], h, fill=WHITE, stroke=RULE, size=SMALL, rounded=False, align="left")
        y += h
    _note(d, f"Supports means agreement with one recorded feature, such as attendance or a timestamp, not that all {r2['clocked']:g} recorded hours were "
             "worked. Every record that agrees with the hours comes from the time clock. The three records outside it (the capacity plan, the calendar and the "
             f"output) do not support the hours as recorded, and the records do not show who keeps them, so their independence from the {boss} "
             "is not established. Absences are silent. The hours are unsupported, not unworked. Output is from Requirement 3's weekly "
             "comparison.", y, gap=6)
    return d


# -- IF-C3-3-A: the bridge of account 5080 -------------------------------------------------------------------------------------------

def if_c3_3_a() -> Diagram:
    """A waterfall from 5080 in the first year to 5080 in the last, through the six ledger lines of the bridge."""
    g3, r3 = ctx.values("case3.g3"), ctx.values("case3.r3")
    data = ctx.data()
    growth, payroll, entries, released, change, material, direct = g3["bridge"]
    ledger = {int(r[0]): r for r in g3["ledger"]}
    first_year, last_year = data.F, data.C
    v_first, v_last = ledger[first_year][7], ledger[last_year][7]
    steps = [("Payroll charged to 1090", payroll), ("Journal entries to 1090", entries), ("Standard cost released", released),
             ("Change in 1090", change), ("Material variance", material), ("Direct postings", direct)]
    assert abs(sum(v for _, v in steps) - growth) < 0.005 and abs(v_last - v_first - growth) < 0.005, "the six lines sum to the growth"
    assert abs(v_first - r3["lf"]["v5080"]) < 0.005 and abs(v_last - r3["lc"]["v5080"]) < 0.005 and abs(growth - r3["bridge"]["delta"]) < 0.005
    names = [f"5080 in {first_year}"] + [n for n, _ in steps] + [f"5080 in {last_year}"]
    levels = [v_first]
    for _, v in steps:
        levels.append(levels[-1] + v)
    assert abs(levels[-1] - v_last) < 0.005
    top_value = max([v_first, v_last] + levels)
    tick = 500_000
    ticks = [i * tick for i in range(int(top_value // tick) + 2)]
    d = Diagram("The Bridge of Account 5080")
    plot = kit.Plot(d, 0, 0, 860, 372, y_ticks=ticks, categories=names, bottom=50, y_title="Account 5080 Manufacturing Variance, dollars")
    slot = plot.pw / len(names)
    bw = slot * 0.56

    def bar(i: int, low: float, high: float, color: str, label: str) -> None:
        x = plot.px + slot * i + (slot - bw) / 2
        ytop, ybot = plot.y_of(high), plot.y_of(low)
        h = max(ybot - ytop, 3.0)
        d.box("", x, ytop - (h - (ybot - ytop)) / 2 if h > ybot - ytop else ytop, bw, h, fill=color, stroke=color, rounded=False)
        lw = max(text_width(f"<b>{label}</b>", SMALL, True) + 14, 40)
        d.box(f"<b>{label}</b>", plot.px + slot * (i + 0.5) - lw / 2, ytop - 24, lw, 18, fill=WHITE, stroke=WHITE, size=SMALL,
              rounded=False)

    # connectors first, so the bars and labels sit above them
    running = [v_first] + levels[1:]
    for i in range(len(names) - 1):
        level = running[i] if i < len(names) - 1 else v_last
        x_a = plot.px + slot * i + (slot + bw) / 2
        x_b = plot.px + slot * (i + 1) + (slot - bw) / 2
        d.box("", x_a, plot.y_of(level) - 0.5, x_b - x_a, 1, fill=GRAY, stroke=GRAY, rounded=False)
    bar(0, 0, v_first, BLUE, _money(v_first))
    for k, (_, v) in enumerate(steps):
        before, after = levels[k], levels[k + 1]
        bar(k + 1, min(before, after), max(before, after), TEAL if v > 0 else CORAL, _signed(v))
    bar(len(names) - 1, 0, v_last, BLUE, _money(v_last))
    ly = 372 + 8
    kit.legend(d, 0, ly, [("Increase of 5080", TEAL, "box"), ("Decrease of 5080", CORAL, "box"), ("5080 in the first and last years", BLUE, "box")])
    rest = growth - payroll
    _note(d, f"The six ledger lines add up to the growth of {_money(growth)} from {first_year} to {last_year}. Payroll charged to 1090 is "
             f"{_money(payroll)}, more than the whole growth, and the other five lines net to {_signed(rest)}. Closes are left out of every line. "
             f"The axis starts at zero, so the small lines are thin: their labels give the amounts.", ly + 24)
    return d


# -- IF-C3-4-A: the hours of each scenario against regular capacity -------------------------------------------------------------------

def if_c3_4_a() -> Diagram:
    """Three columns for the scenarios' hours needed, and a line for the plant's regular capacity."""
    g4, r4 = ctx.values("case3.g4"), ctx.values("case3.r4")
    plan = g4["plan"]
    assert len(plan) == 3 and all(r[4] == 0 for r in plan), "no scenario needs overtime for capacity"
    capacity = plan[0][3]
    assert capacity == r4["capacity"] == r4["employees"] * 8 * r4["days"], (capacity, r4["capacity"])
    needed = [r[2] for r in plan]
    assert [round(n) for n in needed] == [round(n) for n in r4["need"]] and max(needed) < capacity
    use = [n / capacity for n in needed]
    assert abs(use[0] - r4["use"]) < 0.001, (use, r4["use"])
    year = ctx.data().N
    step = 25_000
    top = -(-int(capacity * 1.1) // step) * step               # the first multiple of the step above 110% of capacity
    ticks = list(range(0, top + 1, step))
    cats = [f"{r[0]}<br>{r[1]:.2f} hours per standard hour" for r in plan]
    d = Diagram("The Hours Each Scenario Needs Against Regular Capacity")
    plot = kit.Plot(d, 0, 0, 860, 400, y_ticks=ticks, categories=cats, bottom=44, y_title=f"Hours needed in {year}",
                    y_fmt=lambda v: f"{v:,.0f}", left=70)
    slot = plot.pw / 3
    bw = slot * 0.46
    plot.line([(-0.5, capacity), (2.5, capacity)], color=CORAL, width=2.5, dashed=True)
    for i, (n, share) in enumerate(zip(needed, use)):
        x = plot.px + slot * i + (slot - bw) / 2
        ytop, ybot = plot.y_of(n), plot.y_of(0)
        d.box("", x, ytop, bw, ybot - ytop, fill=BLUE, stroke=BLUE, rounded=False)
        lw = text_width(f"<b>{n:,.0f} hours</b>", SMALL, True) + 20
        d.box(f"<b>{n:,.0f} hours</b>", x + bw / 2 - lw / 2, ytop - 24, lw, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
        d.text(f"<b>{share:.0%}</b> of<br>regular capacity", x, ytop + 8, bw, 40, size=SMALL, color=WHITE, align="center")
    label = f"Regular capacity: {capacity:,} hours"
    lw = text_width(f"<b>{label}</b>", SMALL, True) + 24
    d.box(f"<b>{label}</b>", plot.px + 8, plot.y_of(capacity) - 24, lw, 20, fill=WHITE, stroke=WHITE, color=CORAL, size=SMALL, rounded=False)
    ny = 400 + 8
    _note(d, f"Hours needed are the {ctx.data().C} output of {r4['std']:,.0f} standard hours times each scenario's ratio. Regular capacity is "
             f"{r4['employees']} hourly employees × 8 hours × {r4['days']} working days of {ctx.data().C}, because the calendar stops early in "
             f"{year}. Every scenario fits inside it on the year's total, so the plan allows no routine overtime. Weeks and work centers can "
             f"still bind, so any exception is approved against a dated plan.", ny)
    return d


# -- IF-C3-5-A: why the two accruals move the liability far more than income --------------------------------------------------------------

def if_c3_5_a() -> Diagram:
    """Two panels on one scale: the accrual and the prior year's work in income, and the same amounts on the balance sheet."""
    r5 = ctx.values("case3.r5")
    data = ctx.data()
    accrual, prior, net = r5["p"]["accrual"], r5["prior"]["total"], r5["change"]
    assert abs(accrual - prior - net) < 0.005 and 0 < net < 0.1 * accrual, (accrual, prior, net)
    left_day, cur, prev = r5["left_day"], data.C, data.P
    scale = 232.0 / accrual
    base = 292.0                                                   # the baseline of both panels
    bw = 110.0
    d = Diagram("Why Two Accruals Move the Liability Far More Than Income")
    for px, title in ((0.0, f"<b>Income</b> (fiscal {cur})"), (445.0, f"<b>Balance sheet</b> at December 31, {cur}")):
        d.box(title, px, 0, 415, 30, fill=BLUE, stroke=BLUE, color=WHITE, size=HEAD, rounded=False)
        d.box("", px, base, 415, 2, fill=INK, stroke=INK, rounded=False)

    def value_label(x: float, top: float, label: str) -> None:
        lw = text_width(f"<b>{label}</b>", SMALL, True) + 14
        d.box(f"<b>{label}</b>", x + bw / 2 - lw / 2, top - 24, lw, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)

    def name(x: float, text: str) -> None:
        d.text(text, x + bw / 2 - 78, base + 8, 156, 52, size=SMALL, align="center")

    def bar(x: float, value: float, fill: str, label: str, text: str) -> float:
        h = value * scale
        d.box("", x, base - h, bw, h, fill=fill, stroke=fill, rounded=False)
        value_label(x, base - h, label)
        name(x, text)
        return base - h

    # Income: the expense to add and the expense to remove, side by side
    x1, x2 = 36.0, 186.0
    top1 = bar(x1, accrual, CORAL, f"+{_money(accrual)}", f"<b>Expense added</b>:<br>work of December<br>{left_day}–31, {cur}")
    top2 = bar(x2, prior, TEAL, f"{MINUS}{_money(prior)}", f"<b>Expense removed</b>:<br>{prev} work paid<br>in {cur}")
    bx = x2 + bw + 6                                                # the small net difference, a bracket between the two tops
    for ty in (top1, top2):
        d.box("", bx, ty, 12, 2, fill=AMBER, stroke=AMBER, rounded=False)
    d.box("", bx + 10, top1, 2, top2 - top1 + 2, fill=AMBER, stroke=AMBER, rounded=False)
    d.text(f"<b>Net</b>: expense<br>up <b>{_money(net)}</b>", bx + 18, top1 - 2, 415 - bx - 18, 36, size=SMALL, color=AMBER)
    # Balance sheet: the liability, and opening retained earnings with the income effect stacked on it
    x3, x4 = 445.0 + 36, 445.0 + 186
    top3 = bar(x3, accrual, BLUE, f"+{_money(accrual)}", f"<b>Liability</b> rises:<br>accrued payroll at<br>December 31")
    h4, hn = prior * scale, net * scale
    d.box("", x4, base - h4, bw, h4, fill=GRAY, stroke=GRAY, rounded=False)
    d.box("", x4, base - h4 - hn, bw, hn, fill=AMBER_TINT, stroke=AMBER, stroke_width=1.5, rounded=False)
    d.text(f"<b>{MINUS}{_money(prior)}</b>", x4, base - h4 + 6, bw, 20, size=SMALL, color=WHITE, align="center")
    name(x4, f"<b>Opening retained<br>earnings</b> fall: {prev}<br>work paid in {cur}")
    d.box("", x3 + bw, top3 - 0.75, x4 - (x3 + bw), 1.5, fill=GRAY, stroke=GRAY, rounded=False)      # the liability's level
    d.text(f"<b>{MINUS}{_money(net)}</b><br>from {cur} income", x4 + bw + 6, base - h4 - hn - 4, 860 - (x4 + bw + 6), 36, size=SMALL, color=AMBER)
    _note(d, f"One scale for both panels. Recording both accruals adds {_money(accrual)} of expense and removes {_money(prior)}, so {cur} income moves only "
             f"{_money(net)}. The liability at the year-end carries the whole {_money(accrual)}: {_money(prior)} of it falls on opening retained earnings and "
             f"{_money(net)} on {cur} income. Manufacturing's part of each amount is taken as a cost of the period.", base + 70)
    return d


# -- IF-C3-6-A: the layout of the memo and its appendix --------------------------------------------------------------------------------

def if_c3_6_a() -> Diagram:
    """Two memo pages and the smaller appendix page, each section and exhibit tagged with the requirement that produced it."""
    sections = _memo_sections()
    exhibits = _exhibits()
    makers = _exhibit_makers(exhibits)
    table = _memo_table()
    rec = _recommendation_sources()
    assert len(sections) == 3 and len(exhibits) == 5 and len(makers) == 5 and rec == [2, 3, 4, 5], (sections, exhibits, makers, rec)
    for name in sections:                                          # the exhibits of each section agree with their makers
        assert [makers[e - 1] for e in table[name][1]] == sorted(makers[e - 1] for e in table[name][1])
        assert set(makers[e - 1] for e in table[name][1]) <= set(table[name][0]), (name, table[name], makers)
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
        text = _who(nums).replace(" ", "<br>", 1)
        cid = d.box(f"<b>{text}</b>", x, cy - chip_h / 2, chip_w, chip_h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL)
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

    # page 1: the header lines, the opening, Auditing and Managerial accounting
    y = top + 10
    for k, label in enumerate(("To:", "From:", "Date:", "Re:")):
        d.box(f"<b>{label}</b>", p1x + 10 + (k % 2) * ((PW - 20) / 2), y + (k // 2) * 20, (PW - 20) / 2, 20, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              align="left", rounded=False)
    y += 40 + 8
    plan = [(46.0, "Opening paragraph", GRAY_TINT, GRAY, [6]), (66.0, sections[0], BLUE_TINT, BLUE, table[sections[0]][0]),
            (76.0, sections[1], BLUE_TINT, BLUE, table[sections[1]][0])]
    for h, title, fill, stroke, nums in plan:
        bid = block(p1x, y, h, title, fill, stroke)
        chip(0, y + h / 2, nums, bid)
        y += h + 8
    # page 2: Financial reporting and the recommendation, then the room left in the two pages
    y = top + 10
    for h, title, fill, stroke, nums in ((70.0, sections[2], BLUE_TINT, BLUE, table[sections[2]][0]), (64.0, "Recommendation", GRAY_TINT, GRAY, rec)):
        bid = block(p2x, y, h, title, fill, stroke)
        chip(c2x, y + h / 2, nums, bid)
        y += h + 8
    d.text("<i>At most two pages in all: the rest of page 2 may stay empty.</i>", p2x + 10, y + 6, PW - 20, 36, size=SMALL, color=GRAY)
    # the appendix: five numbered exhibits
    y = top + 10
    for k, name in enumerate(exhibits):
        label = name[0].upper() + name[1:]
        bid = d.box(f"<b>{k + 1}</b>  {esc(label)}", ax + 8, y, AW - 16, 40, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, size=SMALL, align="left")
        chip(c3x, y + 20, [makers[k]], bid)
        y += 48
    by_maker: dict[int, list[int]] = {}
    for k, n in enumerate(makers):
        by_maker.setdefault(n, []).append(k + 1)
    made = ", ".join(f"Requirement&nbsp;{n} for {'Exhibit' if len(ks) == 1 else 'Exhibits'}&nbsp;{' and '.join(map(str, ks))}"
                     for n, ks in sorted(by_maker.items()))
    ny = top + PH + 12
    _note(d, f"Each section is built from the requirements named beside it, and each exhibit comes from the requirement that made it: {made}. The opening "
             "is written in Requirement 6 once the rest is known, and the recommendation rests on Requirements 2 to 5. Block heights are schematic.", ny)
    return d


FIGURES = {
    "IF-C3-0-A": if_c3_0_a,
    "IF-C3-0-B": if_c3_0_b,
    "IF-C3-1-A": if_c3_1_a,
    "IF-C3-1-B": if_c3_1_b,
    "IF-C3-2-A": if_c3_2_a,
    "IF-C3-3-A": if_c3_3_a,
    "IF-C3-4-A": if_c3_4_a,
    "IF-C3-5-A": if_c3_5_a,
    "IF-C3-6-A": if_c3_6_a,
}
