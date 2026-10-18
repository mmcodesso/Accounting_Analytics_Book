"""Instructor figures of the Part IV case (guides in facts/instructor/guides/case-part-4/).

The Part IV case, "Finding the Cash Behind the Profit", is worked in one Power BI file, Charles River Cash Case.pbix, whose
model answer is the PBIP outputs/companion/solutions/PartIV-case (a TMDL model, a PBIR report of twelve pages and a Checks
query).  The five report-page mocks draw pages of that project: the names, the visuals, their titles, their columns and the
filters they are saved with are read from its text files, and every value comes from the guides' own contexts (case4.chapter,
case4.g1 to case4.g6) and the registered notes (case4.r1 to case4.r5), which are the SQL twins of the model's DAX, or from
read-only queries on the dataset.  The diagrams and charts take their structure from the case text (cases/part-4-case.qmd) and
the guides; what a mock may show is what the project holds, so a visual's values are the ones its measures return on the
dataset, never a value typed here.
"""

from __future__ import annotations

import json
import math
import re

import ctx
import kit
import powerbi as pbi
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HIGHLIGHT, INK, RULE, SMALL,
                    TEAL, TEAL_TINT, WHITE, Diagram, esc)

BODY_SIZE = 13
CASE = ctx.REPO / "cases" / "part-4-case.qmd"
GUIDES = ctx.REPO / "facts" / "instructor" / "guides" / "case-part-4"
PROJECT = ctx.REPO / "outputs" / "companion" / "solutions" / "PartIV-case" / "Charles River Cash Case"
MODEL = PROJECT / "Charles River Cash Case.SemanticModel"
REPORT = PROJECT / "Charles River Cash Case.Report" / "definition"
STRAIGHT = "edgeStyle=none;"
MINUS = "−"
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
               "December"]


# -- the model answer (a PBIP of text files) ----------------------------------------------------------------------------

def _g4():
    """guide_contexts.case4: the helpers that read the project (measure_table, check_sections, findings_table)."""
    from guide_contexts import case4
    return case4


def _n4():
    from notes import case4
    return case4


def _tmdl(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def _model_columns(table: str) -> list[str]:
    return [a or b for a, b in re.findall(r"^\tcolumn (?:'([^']+)'|(\S+))", _tmdl(f"tables/{table}.tmdl"), re.M)]


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


def _display_names(page: str, name: str, role: str) -> list[str]:
    """The column headings of a visual: a field's display name when the project renames it, else its own name."""
    return [p.get("displayName") or p["nativeQueryRef"] for p in _visual(page, name)["visual"]["query"]["queryState"][role]["projections"]]


def _year_filter(page: str, name: str) -> list[int]:
    """The years a visual is filtered to (the Year filter saved on it), empty when it has none."""
    for f in _visual(page, name).get("filterConfig", {}).get("filters", []):
        if f["field"]["Column"]["Property"] == "Year":
            cond = f["filter"]["Where"][0]["Condition"]["In"]
            return [int(v[0]["Literal"]["Value"].rstrip("L")) for v in cond["Values"]]
    return []


def _check_columns(table: str, columns: list[str]) -> None:
    """A mock may show only the columns (or, for Key Measures, the measures) the project has."""
    if table == "Key Measures":
        missing = set(columns) - set(_g4().measure_table())
    else:
        missing = set(columns) - set(_model_columns(table))
    assert not missing, f"{table} lacks {sorted(missing)} in the model answer"


# -- what the case text and the guides say ------------------------------------------------------------------------------------

def _case_text() -> str:
    return CASE.read_text(encoding="utf-8")


def _requirements() -> list[dict]:
    """Each requirement of the case text: number, title, the chapter tag ('Chapters 14 and 15', or None) and the perspective."""
    found = []
    for m in re.finditer(r"^\*\*Requirement (\d+): ([^*]+?)\.\*\*", _case_text(), re.M):
        title, tag, persp = m.group(2), None, None
        parts = re.fullmatch(r"(.+?) \(([^)]*)\)", title)
        if parts:
            title = parts.group(1)
            bits = [b.strip() for b in parts.group(2).split(";")]
            if bits[0].startswith("Chapter"):
                tag = bits[0]
                persp = bits[1] if len(bits) > 1 else None
        found.append(dict(n=int(m.group(1)), title=title, tag=tag, perspective=persp))
    assert [r["n"] for r in found] == list(range(1, len(found) + 1)), found
    return found


def _memo_sections() -> list[str]:
    """The three headed sections of the memo, as Requirement 6 names them."""
    text = _case_text()
    start = text.index("**Requirement 6:")
    block = text[start:text.index("**Deliverable.**")]
    return re.findall(r"^- \*\*([A-Z][A-Za-z ]+):\*\*", block, re.M)


def _requirement_meta(n: int) -> dict:
    """The front matter of the guide template of one requirement (title, solution, figures)."""
    from guides import split_front
    path = next(GUIDES.glob(f"req-{n}-*.md"))
    meta, _ = split_front(path.read_text(encoding="utf-8"))
    return meta


def _page_requirement(page: str) -> int:
    """The requirement whose model answer holds this page, read from each guide's 'solution' line."""
    name = _page_name(page)
    owners = [n for n in range(1, 7) if re.search(rf"\b{re.escape(name)}\b", _requirement_meta(n).get("solution", ""))]
    assert len(owners) == 1, (page, name, owners)
    return owners[0]


def _who(nums: list[int]) -> str:
    """'Requirement 2', 'Requirements 3 and 4', 'Requirements 2 to 5'."""
    if len(nums) == 1:
        return f"Requirement {nums[0]}"
    if nums == list(range(nums[0], nums[-1] + 1)) and len(nums) > 2:
        return f"Requirements {nums[0]} to {nums[-1]}"
    return f"Requirements {' and '.join(map(str, nums))}"


def _names(items: list[str]) -> str:
    """'A', 'A and B', 'A, B and C'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _exhibits() -> list[dict]:
    """The five exhibits of the memo's appendix, as the Deliverable and the model answer's visuals have them: the text of the exhibit,
    the report pages that make it, and the requirement that owns those pages.  Each exhibit's visuals are titled as Step 7 of the guide
    says, so a renamed visual fails here."""
    x = ctx.values("case4.g6")
    assert len(x["exhibits"]) == 5 and x["n_exhibits"] == 5
    makers = [[("cashBridge", "bridgeMatrix")], [("cashBridge", "restated")], [("workingCapital", "wcMatrix")],
              [("materialsBuild", "channelByYear"), ("materialsTarget", "whatIfTable")], [("reconciliations", "findings")]]
    keys = [["bridge"], ["restated"], ["wc"], ["channels", "tested"], ["findings"]]
    out = []
    for text, vis, ks in zip(x["exhibits"], makers, keys):
        assert [_title(p, v) for p, v in vis] == [x["titles"][k] for k in ks], (text, vis, ks)
        pages = [p for p, _ in vis]
        reqs = {_page_requirement(p) for p in pages}
        assert len(reqs) == 1, (text, reqs)
        out.append(dict(text=text, pages=[_page_name(p) for p in pages], req=reqs.pop()))
    return out


def _note(d: Diagram, text: str, y: float, x: float = 0, w: float = 860, gap: float = 0) -> float:
    """A short italic gray note sized to its text; returns its bottom."""
    y += gap
    h = kit.height_for(text, w, SMALL, pad=8)
    d.text(f"<i>{text}</i>", x, y, w, h, size=SMALL, color=GRAY)
    return y + h


def _nowrap(text: str) -> str:
    """A label that must not break at its hyphens (a document number, an ISO date)."""
    return f'<span style="white-space:nowrap">{esc(text)}</span>'


def _money(x: float) -> str:
    return pbi.amount(x)


def _sgn(x: float, places: int = 1) -> str:
    """A signed number with a true minus sign."""
    return (MINUS if x < 0 else "+") + f"{abs(x):.{places}f}"


def _signed(x: float) -> str:
    """A money amount with a true minus sign."""
    return (MINUS if x < 0 else "") + pbi.amount(abs(x))


def _clip(text: str, width: float, size: int = SMALL, margin: float = 14, bold: bool = False) -> str:
    """A cell value cut to its column with an ellipsis, as a narrow column shows it."""
    if text_width(esc(text), size, bold) <= width - margin:
        return text
    while text and text_width(esc(text + "…"), size, bold) > width - margin:
        text = text[:-1]
    return text.rstrip() + "…"


# -- IF-C4-0-A: how the six requirements build the memo -----------------------------------------------------------------------

def if_c4_0_a() -> Diagram:
    """The requirements with their chapters, Requirement 1's file feeding all, the memo's sections and the five exhibits with the
    requirement and report page that produce each."""
    reqs = _requirements()
    sections = _memo_sections()
    exhibits = _exhibits()
    assert len(reqs) == 6 and len(sections) == 3 and len(exhibits) == 5, (sections, exhibits)
    by_persp = {s.lower(): s for s in sections}
    assert [reqs[k]["perspective"] for k in (1, 2, 3, 4)] == ["financial reporting", "managerial accounting", "managerial accounting", "auditing"], reqs
    assert [by_persp[reqs[k]["perspective"]] for k in (1, 2, 3, 4)] == ["Financial reporting", "Managerial accounting", "Managerial accounting", "Auditing"]
    feeders = {s: [r["n"] for r in reqs[1:5] if by_persp[r["perspective"]] == s] for s in sections}
    assert sections == ["Financial reporting", "Managerial accounting", "Auditing"], sections
    d = Diagram("How the Six Requirements Build the Memo and Its Appendix")
    W, GAP, TOP, H = 130.0, 16.0, 40.0, 112.0
    xs = [i * (W + GAP) for i in range(6)]
    cx = [x + W / 2 for x in xs]
    d.text("<b>Requirement 1's file, the model and its Validation page, feeds every other requirement</b>", 110, 0, 640, 20, size=SMALL, align="center")
    req_ids = []
    for i, r in enumerate(reqs):
        tag = r["tag"] or "no chapter tag"
        text = f"<b>Requirement {r['n']}</b><br>{esc(r['title'])}<br><i>{esc(tag)}</i>"
        assert kit.height_for(text, W, SMALL) <= H, (r, kit.height_for(text, W, SMALL))
        req_ids.append(d.box(text, xs[i], TOP, W, H, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL))
    bus_y = 28.0
    bus = [d.anchor(x, bus_y) for x in cx]
    d.edge(req_ids[0], bus[0], color=GRAY, width=1.5, exit=(0.5, 0), meta=STRAIGHT)
    for a, b in zip(bus, bus[1:]):
        d.edge(a, b, color=GRAY, width=1.5, meta=STRAIGHT)
    for k in range(1, 6):
        d.arrow(bus[k], req_ids[k], entry=(0.5, 0), meta=STRAIGHT)
    # the memo: its frame, the three sections and the opening with the recommendation
    fx, fy, fw, fh = xs[1] - 22, TOP + H + 62, 860 - xs[1] + 22, 126.0
    frame = d.box("", fx, fy, fw, fh, fill=GRAY_TINT, stroke=GRAY, stroke_width=1.5, rounded=False)
    d.text("<b>The memo</b> (Requirement 6): three sections in the order of the controller's questions, at most two pages", fx + 10, fy + fh - 26, fw - 20, 22, size=SMALL)
    sy, sh = fy + 14, 76.0
    targets = {}
    for name in sections:
        a, b = min(feeders[name]) - 1, max(feeders[name]) - 1
        assert b - a + 1 == len(feeders[name]), "a section's requirements are side by side"
        sx, sw = xs[a], xs[b] + W - xs[a]
        who = " and ".join(str(n) for n in feeders[name])
        targets[name] = (d.box(f"<b>{esc(name)}</b><br><i>from Requirement{'s' if len(feeders[name]) > 1 else ''} {who}</i>", sx, sy, sw, sh,
                               fill=WHITE, stroke=BLUE, stroke_width=1.5), sx, sw)
    ox, ow = xs[5], W - 10
    opening = d.box("<b>Opening and recommendation</b><br><i>written in Requirement 6</i>", ox, sy, ow, sh, fill=WHITE, stroke=BLUE, stroke_width=1.5, size=SMALL)
    for r in reqs[1:5]:
        tid, sx, sw = targets[by_persp[r["perspective"]]]
        d.arrow(req_ids[r["n"] - 1], tid, exit=(0.5, 1), entry=((cx[r["n"] - 1] - sx) / sw, 0), meta=STRAIGHT)
    d.arrow(req_ids[5], opening, exit=(0.5, 1), entry=((cx[5] - ox) / ow, 0), meta=STRAIGHT)
    d.arrow(req_ids[0], frame, exit=(0.5, 1), entry=(0, 0.35), meta="edgeStyle=orthogonalEdgeStyle;")
    d.text("The .pbix, with its About page, Validation page, Tests tab and Data Through card, is submitted with the memo", 0, fy + fh / 2 - 6, 128, 84, size=SMALL, color=GRAY)
    # the appendix and its five exhibits, each with the requirement and the report page that make it
    ay = fy + fh + 40
    gap_x, ew = 12.0, (860 - 12.0 * 4) / 5
    ah = 182.0
    d.box("", 0, ay, 860, ah, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False, dashed=True)
    d.text("<b>The appendix</b>, up to three pages (Requirement 6): five numbered exhibits, each made in an earlier requirement", 10, ay + 4, 800, 22, size=SMALL)
    for k, ex in enumerate(exhibits):
        x0 = k * (ew + gap_x)
        label = ex["text"][0].upper() + ex["text"][1:]
        title = f"<b>Exhibit {k + 1}</b><br>{esc(label)}"
        assert kit.height_for(title, ew - 12, SMALL) <= 78, (label, kit.height_for(title, ew - 12, SMALL))
        d.box(title, x0 + 6, ay + 30, ew - 12, 78, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, size=SMALL)
        pages = _names(ex["pages"]) + (" page" if len(ex["pages"]) == 1 else " pages")
        tag = f"<b>from Requirement {ex['req']}</b><br>{esc(pages)}"
        assert kit.height_for(tag, ew - 12, SMALL) <= 62, (pages, kit.height_for(tag, ew - 12, SMALL))
        d.box(tag, x0 + 6, ay + 114, ew - 12, 62, fill=BLUE_TINT, stroke=BLUE, size=SMALL)
    app = d.container(0, ay, 860, ah)
    d.arrow(app, frame, exit=(0.5, 0), entry=((430 - fx) / fw, 1), meta=STRAIGHT)
    d.text("each exhibit is cited in the memo", 442, fy + fh + 8, 260, 22, size=SMALL, valign="middle")
    by_maker: dict[int, list[int]] = {}
    for k, ex in enumerate(exhibits):
        by_maker.setdefault(ex["req"], []).append(k + 1)
    parts = [f"Requirement&nbsp;{n} makes {'Exhibit' if len(ks) == 1 else 'Exhibits'}&nbsp;{' and '.join(map(str, ks))}" for n, ks in sorted(by_maker.items())]
    made = ", ".join(parts[:-1]) + f", and {parts[-1]}"
    _note(d, "Requirements 2 to 5 each supply the section named in their perspective, and the arrows into a section show which requirements it draws on. "
             f"Requirement 6 writes the opening and the recommendation and assembles the appendix. {made}. Requirement 1 supplies no section: "
             "it is the file every exhibit is read from, and its Tests tab is what the memo's report controls rest on.", ay + ah + 8)
    return d


# -- IF-C4-0-B: the three dates -----------------------------------------------------------------------------------------------

def if_c4_0_b() -> Diagram:
    """One axis across a year-end: the last payroll posting, Data Through and the ledger's last posting, with the open pay periods under
    the first and the supplier payments after the year in a bracket."""
    import datetime as dt
    data = ctx.data()
    n4 = _n4()
    r1 = ctx.values("case4.r1")
    g1 = ctx.values("case4.g1")
    c = ctx.values("case4.chapter")
    pay_end, thru, last = c["pay_end"], c["thru"], c["last"]
    assert (g1["pay_end"], g1["through"], g1["last"]) == (pay_end, thru, last) and pay_end < thru < last
    assert thru == f"{data.C}-12-31" and last[:4] == str(data.N)
    # the seven documents behind the working-capital accounts: all end at the year-end except the supplier payments
    ends = {s: data.one("SELECT MAX(PostingDate) FROM GLEntry WHERE SourceDocumentType = ?", s) for s in n4.DATA_SOURCES}
    late = sorted(s for s, e in ends.items() if e > thru)
    assert late == ["DisbursementPayment"] and ends["DisbursementPayment"] == last and min(ends.values()) == thru
    assert all(e == thru for s, e in ends.items() if s != "DisbursementPayment")
    # what follows the year: only supplier payments of the year's invoices
    after = data.q("SELECT SourceDocumentType, COUNT(*), SUM(Debit) FROM GLEntry WHERE PostingDate > ? GROUP BY 1", thru)
    assert [a[0] for a in after] == ["DisbursementPayment"] and after[0][1] == r1["rows_after"]
    assert abs(after[0][2] - r1["pay_amount"]) < 0.005 and r1["n_pay"] == data.one(
        "SELECT COUNT(DISTINCT VoucherNumber) FROM GLEntry WHERE PostingDate > ?", thru)
    opened = data.q("SELECT PeriodNumber, PeriodStartDate, PeriodEndDate, Status FROM PayrollPeriod WHERE PeriodEndDate > ? ORDER BY 1", pay_end)
    assert len(opened) == 2 and all(o[3] == "Open" for o in opened) and r1["n_open"] == "two"
    assert data.one("SELECT COUNT(*) FROM PayrollRegister r JOIN PayrollPeriod p ON p.PayrollPeriodID = r.PayrollPeriodID WHERE p.Status = 'Open'") == 0, \
        "the open pay periods have no registers"
    start, end = dt.date(data.C, 12, 1), dt.date(data.N, 3, 1)
    span = (end - start).days
    ax0, ax1 = 24.0, 836.0
    x_of = lambda iso: ax0 + (dt.date.fromisoformat(iso) - start).days * (ax1 - ax0) / span   # noqa: E731
    d = Diagram("The Three Dates of the Case")
    ya = 178.0
    year_x = x_of(f"{data.N}-01-01")
    # the years above the labels
    for x0, x1, label in ((ax0, year_x - 3, str(data.C)), (year_x + 3, ax1, str(data.N))):
        d.box("", x0, 22, x1 - x0, 3, fill=INK, stroke=INK, rounded=False)
        d.box("", x0, 22, 3, 10, fill=INK, stroke=INK, rounded=False)
        d.box("", x1 - 3, 22, 3, 10, fill=INK, stroke=INK, rounded=False)
        d.text(f"<b>{label}</b>", x0, 0, x1 - x0, 20, size=BODY_SIZE, align="center")
    d.box("", ax0, ya - 1.5, ax1 - ax0, 3, fill=INK, stroke=INK, rounded=False)
    d.text(f"<i>{_nowrap(start.isoformat())}</i>", ax0 - 2, ya + 5, 100, 18, size=SMALL, color=GRAY)
    d.text(f"<i>{_nowrap(end.isoformat())}</i>", ax1 - 98, ya + 5, 100, 18, size=SMALL, color=GRAY, align="right")
    # the open pay periods, shaded under the axis from their first day to the year-end
    nums = [int(o[0].split("-")[-1]) for o in opened]
    o0, o1 = x_of(opened[0][1]), x_of(f"{data.C}-12-31") + (ax1 - ax0) / span
    d.box(f"<b>Periods {nums[0]} and {nums[1]}: open</b>", o0, ya + 22, o1 - o0, 22, fill=CORAL_TINT, stroke=CORAL, stroke_width=1.5, rounded=False, color=CORAL, size=SMALL)
    marks = [("Last payroll posting", pay_end, GRAY, GRAY_TINT, "PayrollSummary and PayrollPayment", 20, 190),
             ("Data Through", thru, BLUE, BLUE_TINT, "the earliest of the last posting dates of the seven documents behind the working-capital accounts", 236, 252),
             ("Last posting in the ledger", last, AMBER, AMBER_TINT, "supplier payments only", 640, 196)]
    for label, iso, color, fill, sub, lx, lw in marks:
        mx = x_of(iso)
        assert lx <= mx <= lx + lw, f"{label}: the leader line meets its label"
        text = f"<b>{label}</b><br>{_nowrap(iso)}<br>{esc(sub)}"
        h = kit.height_for(text, lw, SMALL, pad=10)
        ly = ya - 36 - h
        d.box("", mx - 0.75, ly + h, 1.5, ya - ly - h, fill=color, stroke=color, rounded=False)
        d.box(text, lx, ly, lw, h, fill=fill, stroke=color, size=SMALL, stroke_width=1.5)
        d.vertex("", f"ellipse;html=1;fillColor={color};strokeColor={WHITE};strokeWidth=1.5;", mx - 7, ya - 7, 14, 14)
    left = (f"The last {r1['n_open']} pay periods ({_nowrap(opened[0][1])} to {_nowrap(opened[1][2])}) are marked Open and have no registers, so payroll stops at "
            f"{_nowrap(pay_end)}. A Data Through that followed payroll would fall before the year-end and blank the last quarter.")
    d.text(left, ax0, ya + 52, 276, 80, size=SMALL)
    # the bracket after Data Through
    bx0, bx1 = year_x + 4, x_of(last)
    by = ya + 32
    d.box("", bx0, by, bx1 - bx0, 2, fill=AMBER, stroke=AMBER, rounded=False)
    d.box("", bx0, by - 8, 2, 18, fill=AMBER, stroke=AMBER, rounded=False)
    d.box("", bx1 - 2, by - 8, 2, 18, fill=AMBER, stroke=AMBER, rounded=False)
    r2 = ctx.values("case4.r2")
    assert abs(r2["cash_to"] - r1["cash_last"] - r1["pay_amount"]) < 0.005 and abs(r1["fall"] - r1["pay_amount"]) < 0.005
    d.text(f"<b>{r1['n_pay']} supplier payments of {data.C}'s invoices</b>, {_money(r1['pay_amount'])} in {r1['rows_after']} ledger rows: the only postings after the year. "
           f"Cash reads {_money(r2['cash_to'])} at the year-end and {_money(r1['cash_last'])} at the last posting, "
           f"a fall of {_money(r1['fall'])} that only means the data stop.", bx0 + 6, ya + 52, bx1 - bx0 - 6, 64, size=SMALL)
    _note(d, f"One axis from December {data.C} to the end of February {data.N}. {_nowrap(thru)} is the earliest of the last posting dates of "
             f"{', '.join(s for s in n4.DATA_SOURCES if s != late[0])} and {late[0]}: {n4.WORDS[len(n4.DATA_SOURCES) - 1]} documents end on that day and supplier payments run on to {_nowrap(last)}. "
             f"Payroll liability remittances post until {_nowrap(r1['remit_end'])}, but the last payroll posting is the last PayrollSummary or PayrollPayment. "
             "Data Through is a bound observed in the extract, not proof that no document before it is missing.", ya + 142)
    return d


# -- IF-C4-6-A: the layout of the memo and its appendix ----------------------------------------------------------------------------

def _memo_table() -> dict[str, tuple[list[int], list[int]]]:
    """Section -> (requirements, exhibits) from the table of Step 2 of the Requirement 6 guide."""
    text = next(GUIDES.glob("req-6-*.md")).read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^\| (Financial reporting|Managerial accounting|Auditing) \|.*\| (Requirements? [\d and]+) \| ([\d, ]+) \|$", text, re.M):
        out[m.group(1)] = ([int(n) for n in re.findall(r"\d+", m.group(2))], [int(n) for n in re.findall(r"\d+", m.group(3))])
    return out


def if_c4_6_a() -> Diagram:
    """Two memo pages and the smaller appendix page, each section and exhibit tagged with the requirement and the report page that supply it."""
    sections = _memo_sections()
    exhibits = _exhibits()
    table = _memo_table()
    reqs = _requirements()
    assert sections == ["Financial reporting", "Managerial accounting", "Auditing"] and set(table) == set(sections), (sections, table)
    assert sorted(e for _, es in table.values() for e in es) == [1, 2, 3, 4, 5], table
    for name, (nums, exs) in table.items():                                   # the exhibits of each section come from the requirements named for it
        assert {exhibits[e - 1]["req"] for e in exs} <= set(nums), (name, nums, exs)
    pages_of = {n: sorted({p for e in exhibits if e["req"] == n for p in e["pages"]}, key=lambda p: [_page_name(q) for q in _page_ids()].index(p)) for n in range(1, 7)}
    assert pages_of[2] == ["Cash Bridge"] and pages_of[3] == ["Working Capital"] and pages_of[4] == ["Materials Build", "Materials Target"] and pages_of[5] == ["Reconciliations"]
    own = {1: ["Validation", "About"], 5: pages_of[5]}                        # the auditing section also rests on the report's own controls

    def tag(nums: list[int]) -> str:
        pages: list[str] = []
        for n in nums:
            pages += own.get(n) if n in own and n != 5 else pages_of[n]
        who = _who(nums).replace(" ", "<br>", 1) if len(nums) > 1 else _who(nums)
        return f"<b>{who}</b><br>{esc(_names(pages))}"

    chip_w, arrow = 100.0, 12.0
    PW, AW, PH, AH = 164.0, 150.0, 344.0, 334.0
    p1x = chip_w + arrow
    c2x = p1x + PW + 8
    p2x = c2x + chip_w + arrow
    c3x = p2x + PW + 8
    chip3 = 116.0
    ax = c3x + chip3 + arrow
    assert ax + AW <= 860, ax + AW
    top = 42.0
    d = Diagram("The Layout of the Memo and Its Appendix")
    d.text("<b>The memo</b>: page 1", p1x, 0, PW, 22, size=SMALL)
    d.text("<b>The memo</b>: page 2", p2x, 0, PW, 22, size=SMALL)
    d.text("<b>The appendix</b>:<br>up to three pages", ax, 0, AW, 36, size=SMALL)
    for x, w, h in ((p1x, PW, PH), (p2x, PW, PH), (ax, AW, AH)):
        d.box("", x, top, w, h, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)

    def chip(x: float, cy: float, html: str, target: str, w: float = chip_w) -> None:
        h = kit.height_for(html, w, SMALL, pad=12)
        cid = d.box(html, x, cy - h / 2, w, h, fill=BLUE_TINT, stroke=BLUE, stroke_width=1.5, size=SMALL)
        d.arrow(cid, target, exit=(1, 0.5), entry=(0, 0.5), meta=STRAIGHT)

    def lines(x: float, y: float, w: float, h: float) -> None:
        k, row = 0, y
        while row + 6 <= y + h:
            d.box("", x, row, w * (0.62 if k % 4 == 3 else 1.0), 4, fill=RULE, stroke=RULE, rounded=False)
            row += 10
            k += 1

    def block(px: float, y: float, h: float, title: str, fill: str, stroke: str) -> str:
        bid = d.box("", px + 10, y, PW - 20, h, fill=fill, stroke=stroke, stroke_width=1.5, rounded=False)
        assert text_width(f"<b>{esc(title)}</b>", SMALL, False) <= PW - 28, title
        d.text(f"<b>{esc(title)}</b>", px + 14, y + 3, PW - 26, 20, size=SMALL)
        lines(px + 18, y + 28, PW - 36, h - 32)
        return bid

    # page 1: the header lines, the opening, Financial reporting and Managerial accounting
    y = top + 10
    for k, label in enumerate(("To:", "From:", "Date:", "Re:")):
        d.box(f"<b>{label}</b>", p1x + 10 + (k % 2) * ((PW - 20) / 2), y + (k // 2) * 20, (PW - 20) / 2, 20, fill=GRAY_TINT, stroke=RULE, size=SMALL,
              align="left", rounded=False)
    y += 40 + 8
    plan1 = [(56.0, "Opening paragraph", GRAY_TINT, GRAY, "<b>Requirement 6</b><br>written once the rest is known"),
             (84.0, sections[0], BLUE_TINT, BLUE, tag(table[sections[0]][0])), (104.0, sections[1], BLUE_TINT, BLUE, tag(table[sections[1]][0]))]
    for h, title, fill, stroke, html in plan1:
        bid = block(p1x, y, h, title, fill, stroke)
        chip(0, y + h / 2, html, bid)
        y += h + 8
    # page 2: Auditing and the recommendation, then the room left in the two pages
    y = top + 10
    rec = list(range(2, 6))
    plan2 = [(104.0, sections[2], BLUE_TINT, BLUE, tag(table[sections[2]][0])),
             (72.0, "Recommendation", GRAY_TINT, GRAY, f"<b>{_who(rec).replace(' ', '<br>', 1)}</b><br>the evidence of the sections")]
    for h, title, fill, stroke, html in plan2:
        bid = block(p2x, y, h, title, fill, stroke)
        chip(c2x, y + h / 2, html, bid)
        y += h + 8
    d.text("<i>At most two pages in all: the rest of page 2 may stay empty.</i>", p2x + 10, y + 6, PW - 20, 36, size=SMALL, color=GRAY)
    # the appendix: five numbered exhibits
    y = top + 10
    for k, ex in enumerate(exhibits):
        label = ex["text"][0].upper() + ex["text"][1:]
        bid = d.box(f"<b>{k + 1}</b>  {esc(label)}", ax + 8, y, AW - 16, 56, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, size=SMALL, align="left")
        pages = _names(ex["pages"])
        chip(c3x, y + 28, f"<b>Requirement {ex['req']}</b><br>{esc(pages)}", bid, w=chip3)
        y += 64
    ny = top + PH + 12
    _note(d, "Each section is built from the requirements named beside it, and each exhibit is a visual of the report page named beside it, made in the requirement "
             "that owns that page. The auditing section rests on Requirement 5's reconciliations and on the controls of Requirement 1's own pages, Validation and About. "
             "The opening is written once the rest is known, and the recommendation rests on Requirements 2 to 5. Block heights are schematic.", ny)
    return d

# -- drawing helpers for the charts ---------------------------------------------------------------------------------------------

def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str = BLUE, width: float = 3) -> None:
    """One edge through the points, drawn straight between them (separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _marker(d: Diagram, x: float, y: float, shape: str, color: str, size: float = 9) -> None:
    """A series marker whose shape differs from series to series, so a line reads without its color."""
    style = {"circle": "ellipse", "diamond": "rhombus", "square": "rounded=0;"}[shape]
    style = style if style.endswith(";") else f"{style};"
    d.vertex("", f"{style}html=1;fillColor={color};strokeColor={WHITE};strokeWidth=1;", x - size / 2, y - size / 2, size, size)


# -- IF-C4-3-B: which component moved the cycle ---------------------------------------------------------------------------------

def if_c4_3_b() -> Diagram:
    """DSO, DIO and DPO by quarter-end with the cash conversion cycle as a heavier fourth line, and a note on the first quarter."""
    r3 = ctx.values("case4.r3")
    r5 = ctx.values("case4.r5")
    qs = r3["qs"]
    labels = [q["label"] for q in qs]
    series = {"dso": [q["dso"] for q in qs], "dio": [q["dio"] for q in qs], "dpo": [q["dpo"] for q in qs], "ccc": [q["ccc"] for q in qs]}
    unrounded = {k: [q["raw"][k] for q in qs] for k in series}              # a movement is the difference of the unrounded measures, rounded once
    for q in qs:
        assert abs(q["dso"] + q["dio"] - q["dpo"] - q["ccc"]) < 0.25, "the cycle is DSO plus DIO less DPO (each rounded to one decimal)"
    rise = lambda k: round(unrounded[k][-1] - unrounded[k][0], 1)          # noqa: E731
    span = lambda k: max(series[k]) - min(series[k])                       # noqa: E731
    assert rise("dio") > 200 and rise("ccc") > 200 and all(b > a for a, b in zip(series["ccc"], series["ccc"][1:])), "DIO and the cycle rise steeply, quarter after quarter"
    assert span("dso") < 10 and span("dpo") < 25 and span("dso") < rise("dio") / 20 and span("dpo") < rise("dio") / 10, "DSO and DPO stay nearly flat"
    assert abs(rise("ccc") - (rise("dso") + rise("dio") - rise("dpo"))) < 0.11
    first = qs[0]
    assert first["end"] == f"{ctx.data().F}-12-31", "the first quarter with a full twelve months is the last of the first year"
    open_ar, open_ap = r5["opening_ar"], r5["opening_ap"]
    assert abs(open_ar - r5["roll"]["1020"]["parts"]["JournalEntry"]) < 0.005 and first["dso_x"] < first["dso"] and first["dpo_x"] < first["dpo"]
    entry = r3["entry"]
    d = Diagram("What Moved the Cash Conversion Cycle")
    d.text("<b>Days at each quarter-end, as recorded: the three components and the cash conversion cycle</b>", 0, 0, 860, 20, size=SMALL)
    top = 26
    plot_h = 346
    label_w = 150
    pw = 860 - label_w - 4
    ticks = [0, 100, 200, 300, 400, 500]
    plot = kit.Plot(d, 0, top, pw, plot_h, None, y_ticks=ticks, categories=labels, y_fmt=lambda v: f"{v:.0f}", left=48, y_title="Days")
    colors = {"dso": BLUE, "dio": CORAL, "dpo": TEAL, "ccc": INK}
    shapes = {"dso": "circle", "dio": "diamond", "dpo": "square", "ccc": "circle"}
    widths = {"dso": 2.5, "dio": 2.5, "dpo": 2.5, "ccc": 5}
    names = {"dso": "DSO", "dio": "DIO", "dpo": "DPO", "ccc": "Cash conversion cycle"}
    # the first quarter's band, drawn before the marks
    x0 = plot.x_of(0)
    slot = plot.pw / len(labels)
    d.vertex("", f"rounded=0;html=1;fillColor={AMBER_TINT};strokeColor={AMBER_TINT};fillOpacity=80;", x0 - slot / 2, plot.py, slot, plot.ph)
    for k in ("dso", "dpo", "dio", "ccc"):
        pts = [(plot.x_of(i), plot.y_of(v)) for i, v in enumerate(series[k])]
        _polyline(d, pts, colors[k], widths[k])
        for px, py in pts:
            _marker(d, px, py, shapes[k], colors[k], 12 if k == "ccc" else 9)
    # the names and the first and last values at the right, pushed apart where the lines end close together
    lx = plot.px + plot.pw + 14
    boxes = []
    for k in ("dso", "dpo", "dio", "ccc"):
        text = f"<b>{names[k]}</b><br>{series[k][0]:.1f} to {series[k][-1]:.1f} days"
        boxes.append([k, plot.y_of(series[k][-1]), kit.height_for(text, label_w - 6, SMALL, pad=8), text])
    boxes.sort(key=lambda b: b[1], reverse=True)               # from the bottom of the chart up
    placed, prev = [], None
    for k, want, h, text in boxes:
        cy = want if prev is None else min(want, prev - 6 - h / 2 - (placed[-1][2] / 2))
        placed.append((k, cy, h, text))
        prev = cy
    for k, cy, h, text in placed:
        want = plot.y_of(series[k][-1])
        d.edge(d.anchor(plot.x_of(len(labels) - 1) + 8, want), d.anchor(lx, cy), color=colors[k], width=1.5, meta="edgeStyle=none;")
        d.box(text, lx, cy - h / 2, label_w - 6, h, fill=WHITE, stroke=colors[k], size=SMALL, align="left", stroke_width=3 if k == "ccc" else 1.5)
    y = top + plot_h + 10
    bottom = kit.callout(d, f"<b>{labels[0]} is the first quarter with a full twelve months, and its balances still carry the opening entry {esc(entry)}.</b> "
                            f"Its receivables of {_money(open_ar)} and payables of {_money(open_ap)} have no document behind them in the extract. Without those lines DSO reads "
                            f"{first['dso_x']:.1f} days, not {first['dso']:.1f}, and DPO {first['dpo_x']:.1f}, not {first['dpo']:.1f}.", 0, y, 860, "amber")
    _note(d, f"From {labels[0]} to {labels[-1]} DIO rose {rise('dio'):.1f} days and the cycle {rise('ccc'):.1f}, while DSO moved {_sgn(rise('dso'))} and DPO {_sgn(rise('dpo'))}: "
             "the cycle grew mainly through inventory. Each line is a quarter-end balance over its own ledger flow of the twelve months before, times 365; "
             f"the shaded quarter is the first. DPO's fall from {first['dpo']:.1f} comes mostly from the unsupported opening payables diluted by purchases ({first['dpo_x']:.1f} without them).", bottom + 4)
    return d


# -- IF-C4-4-B: the excess against the fall in cash ------------------------------------------------------------------------------

def if_c4_4_b() -> Diagram:
    """Four horizontal bars: the excess of materials at 28, 60 and 90 days of supply, and the year's fall in cash."""
    r2 = ctx.values("case4.r2")
    r4 = ctx.values("case4.r4")
    data = ctx.data()
    n4 = _n4()
    whatif = r4["whatif"]
    fall = -r2["cur"]["cash"]
    assert fall > 0 and [w["days"] for w in whatif] == list(n4.TARGETS)
    stock = n4.balance(data, ["1045"], n4.year_end(data.C))
    ttm = r4["ttm"]
    for w in whatif:
        assert abs(w["allowed"] - n4.xr(ttm / 365 * w["days"])) < 0.005 and abs(w["excess"] - n4.xr(stock - ttm / 365 * w["days"])) < 0.005
        assert abs(w["months"] - n4.xr(w["excess"] / (ttm / 12), 2)) < 0.005
    excess = [w["excess"] for w in whatif]
    assert excess == sorted(excess, reverse=True) and min(excess) > 9 * fall, "the three excess bars are each many times the fall"
    assert n4.word(round(excess[-1] / fall)) == r4["multiple"] and r4["multiple"] == "ten"
    d = Diagram("The Excess Materials Against the Fall in Cash")
    d.text(f"<b>Materials above the target at the end of fiscal {data.C}, and the fall in cash of the year (dollars)</b>", 0, 0, 860, 20, size=SMALL)
    x0, x1 = 196.0, 560.0
    vmax = 12e6
    x_of = lambda v: x0 + v / vmax * (x1 - x0)                            # noqa: E731
    top, bar_h, gap = 36.0, 46.0, 24.0
    rows = [(f"Excess at {w['days']} days", w["excess"], BLUE, w) for w in whatif] + [(f"Fall in cash, fiscal {data.C}", fall, CORAL, None)]
    plot_h = len(rows) * (bar_h + gap) + gap - 8
    for t in range(0, 13, 2):
        gx = x_of(t * 1e6)
        d.box("", gx - 0.5, top + plot_h, 1, 6, fill=GRAY, stroke=GRAY, rounded=False)
        d.text(f"{t}M" if t else "0", gx - 24, top + plot_h + 8, 48, 18, size=SMALL, color=GRAY, align="center")
    for i, (name, value, color, w) in enumerate(rows):
        by = top + gap / 2 + 4 + i * (bar_h + gap)
        d.text(f"<b>{name}</b>", 0, by, x0 - 8, bar_h, size=SMALL, align="right", valign="middle")
        d.box("", x0, by, max(x_of(value) - x0, 3), bar_h, fill=color, stroke=color, rounded=False)
        if w:
            text = (f"<b>{_money(value)}</b><br>{w['months']:.2f} months of issues; {value / fall:.1f} times the fall")
        else:
            text = f"<b>{_money(value)}</b><br>cash from {_money(r2['cash_from'])} to {_money(r2['cash_to'])}"
        d.text(text, x_of(value) + 6, by + 2, 860 - x_of(value) - 6, bar_h - 4, size=SMALL, valign="middle")
    d.box("", x0 - 1, top, 2, plot_h, fill=INK, stroke=INK, rounded=False)
    d.box("", x0, top + plot_h, x_of(vmax) - x0, 1.5, fill=GRAY, stroke=GRAY, rounded=False)
    y = top + plot_h + 32
    _note(d, f"The excess is the stock of raw materials and packaging at the year-end, {_money(stock)}, less what a target of 28, 60 or 90 days of supply allows at the year's rate of "
             f"issue, {_money(ttm)} a year: {_money(whatif[0]['allowed'])}, {_money(whatif[1]['allowed'])} and {_money(whatif[2]['allowed'])}. Even at 90 days the excess is "
             f"about {r4['multiple']} times the year's fall in cash. Every bar starts at zero; the months are the excess over a month of issues. "
             "An estimate at the year's rate of issue, not a forecast of what could be released.", y)
    return d


# -- IF-C4-5-B: two reconciliations as one picture -------------------------------------------------------------------------------

def if_c4_5_b() -> Diagram:
    """Receivables and payables: the ledger balance beside the open invoices and the recorded items that close the difference, each item
    carrying its disposition, with the note invoices below the axis."""
    r5 = ctx.values("case4.r5")
    g5 = ctx.values("case4.g5")
    data = ctx.data()
    ledger_ar, ledger_ap = r5["roll"]["1020"]["total"], -r5["roll"]["2010"]["total"]
    open_ar, open_ap = r5["open_ar"], r5["ap_total"]
    opening_ar, opening_ap, notes = r5["opening_ar"], r5["opening_ap"], r5["notes_total"]
    found = [(r[0], r[1], float(r[2]), r[3], r[4]) for r in g5["findings"]]
    f_ar = [f for f in found if f[4] == "Receivables"]
    f_ap = [f for f in found if f[4] == "Payables"]
    assert len(f_ar) == 1 and len(f_ap) == 2 and f_ar[0][2] == opening_ar and sorted(f[2] for f in f_ap) == [-notes, opening_ap], (f_ar, f_ap)
    disp = {"opening_ar": f_ar[0][3], "opening_ap": next(f[3] for f in f_ap if f[2] > 0), "notes": next(f[3] for f in f_ap if f[2] < 0)}
    assert disp == {"opening_ar": "Follow up", "opening_ap": "Follow up", "notes": "Expected"}, disp
    assert abs(ledger_ar - open_ar - opening_ar) < 0.005 and abs(ledger_ap - open_ap - opening_ap + notes) < 0.005, "each difference is its recorded items"
    assert abs(r5["ar_diff"] - opening_ar) < 0.005 and abs(r5["ap_diff"] - (opening_ap - notes)) < 0.005
    assert len(r5["capital"]) == 2 and sum(c["total"] for c in r5["capital"]) == notes and all(c["paid"] == 0 for c in r5["capital"])
    d = Diagram("The Two Reconciliations")
    d.text(f"<b>Ledger balance against open invoices at the end of fiscal {data.C}</b>", 0, 0, 860, 20, size=SMALL)
    top, h = 26.0, 372.0
    ticks = [-2e6, -1e6, 0, 1e6, 2e6, 3e6, 4e6, 5e6, 6e6, 7e6, 8e6]
    plot = kit.Plot(d, 0, top, 860, h, None, y_ticks=ticks, categories=[""] * 2, y_fmt=lambda v: f"{v / 1e6:.0f}M", left=48, bottom=30)
    y_of = plot.y_of
    base = y_of(0)
    d.box("", plot.px, base - 1, plot.pw, 2, fill=INK, stroke=INK, rounded=False)

    def seg(x: float, w: float, low: float, high: float, fill: str, stroke: str, text: str = "", color: str = INK) -> None:
        a, b = y_of(high), y_of(low)
        d.box(text, x, a, w, max(b - a, 2), fill=fill, stroke=stroke, stroke_width=1.5, size=SMALL, color=color, rounded=False)

    bw = 84.0
    panels = [(plot.px + 8, "Receivables", ledger_ar, open_ar, [(opening_ar, disp["opening_ar"], "Opening line of " + _nowrap(r5["entry"]))]),
              (plot.px + 8 + plot.pw / 2, "Payables", ledger_ap, open_ap, [(opening_ap, disp["opening_ap"], "Opening payables of " + _nowrap(r5["entry"])),
                                                                          (-notes, disp["notes"], "The two note invoices, " + " and ".join(f"PI&nbsp;{c['id']}" for c in r5["capital"]))])]
    tone = {"Follow up": (AMBER, AMBER_TINT), "Expected": (TEAL, TEAL_TINT)}
    for px, name, ledger, open_total, items in panels:
        lx, ox = px + 12, px + 12 + bw + 24
        seg(lx, bw, 0, ledger, GRAY, GRAY, f"<b>{_money(ledger)}</b>", WHITE)
        seg(ox, bw, 0, open_total, BLUE, BLUE, f"<b>Open invoices</b><br>{_money(open_total)}", WHITE)
        up, down = open_total, 0.0
        for amount, kind, text in items:
            stroke, tint_fill = tone[kind]
            if amount > 0:
                seg(ox, bw, up, up + amount, stroke, stroke)
                mid = y_of(up + amount / 2)
                up += amount
            else:
                seg(ox, bw, amount, 0, stroke, stroke)
                mid = y_of(amount / 2)
            label = f"<b>{kind}</b>: {text}<br>{_signed(amount)}"
            tx = ox + bw + 12
            tw = px + plot.pw / 2 - 12 - tx
            th = kit.height_for(label, tw - 12, SMALL, pad=10)
            ty = mid - th / 2 if amount > 0 else base + 6
            d.line_sample(ox + bw, mid, 10, color=stroke, width=1.5)
            d.box(label, tx, ty, tw, th, fill=tint_fill, stroke=stroke, size=SMALL, align="left", stroke_width=1.5)
        # the ledger level across both bars
        d.edge(d.anchor(lx + bw, y_of(ledger)), d.anchor(ox + bw, y_of(ledger)), color=INK, width=1.5, dashed=True, meta="edgeStyle=none;")
        d.text(f"<b>{name}</b>", px + 6, plot.py + 2, 200, 20, size=SMALL)
        d.text("<i>ledger balance</i>", lx - 12, y_of(ledger) - 22, bw + 24, 18, size=SMALL, color=GRAY, align="center")
        d.text("<i>open invoices and items</i>", ox - 30, plot.py + plot.ph + 4, bw + 60, 22, size=SMALL, color=GRAY, align="center")
    d.edge(d.anchor(plot.px + plot.pw / 2 - 4, plot.py), d.anchor(plot.px + plot.pw / 2 - 4, plot.py + plot.ph), color=RULE, width=1.5, meta="edgeStyle=none;")
    y = top + h + 8
    ly = y + 4
    kit.legend(d, 0, ly, [("Ledger balance", GRAY, "box"), ("Open invoices of the subledger", BLUE, "box"), ("Follow up", AMBER, "box"), ("Expected", TEAL, "box")])
    _note(d, f"Receivables: the ledger {_money(ledger_ar)} is the open invoices {_money(open_ar)} and the opening line {_money(opening_ar)}. Payables: the ledger {_money(ledger_ap)} is "
             f"the open invoices {_money(open_ap)} and the opening payables {_money(opening_ap)}, less {_money(notes)} for the two invoices the ledger moved to notes payable "
             "while the subledger still lists them open, drawn below the axis. The dashed line is the ledger balance. The dispositions are those of the Findings table.", ly + 26)
    return d

# -- pieces for the report pages ----------------------------------------------------------------------------------------------------

ROW = pbi.ROW


def _hidden(page: str) -> bool:
    return _page(page).get("visibility") == "HiddenInViewMode"


def _tabs(active: str, d: Diagram, y: float) -> None:
    """The page tabs under the canvas: the visible pages around the active one, as the report orders them."""
    order = [p for p in _page_ids() if not _hidden(p)]
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


def _heads(head: str, width: float, bold: bool = True) -> str:
    """A column heading as HTML: an explicit <br> breaks it, and a heading too wide for its column is cut with an ellipsis."""
    if "<br>" in head:
        return "<br>".join(esc(p) for p in head.split("<br>"))
    return esc(_clip(head, width, margin=8, bold=bold))


def _table_visual(d: Diagram, x: float, y: float, title: str, headers: list[str], widths: list[float], rows: list[list[str]],
                  aligns: list[str] | None = None, title_lines: int | None = None, head_lines: int = 1, row_h: float = ROW,
                  total: list[str] | None = None, clip_margin: float | dict = 16) -> dict:
    """A table visual: a title (one line or two), a header row, the rows (banded) and an optional bold total row.  aligns names
    each column's side ("left" for text, "right" for numbers and dates).  A header may break over head_lines lines, with <br>
    where it breaks.  Returns the cell geometry keyed (row, column) with row -1 for the headers, and the visual's bottom and
    right edges."""
    w = sum(widths) + 12
    label = f"<b>{esc(title)}</b>"
    th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
    hh = row_h if head_lines == 1 else 15 * head_lines + 8
    n = len(rows) + (1 if total else 0)
    h = th + 12 + hh + n * row_h
    ix, iy, _, _ = _frame(d, x, y, w, h, title, lines=title_lines)
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    aligns = aligns or ["right" if any(_is_num(r[c]) for r in rows) else "left" for c in range(len(headers))]
    geometry = {}
    for c, (head, cx, wd) in enumerate(zip(headers, xs, widths)):
        d.box(f"<b>{_heads(head, wd)}</b>", cx, iy, wd, hh, fill=WHITE, stroke=WHITE, size=SMALL, align=aligns[c], rounded=False)
        geometry[(-1, c)] = (cx, iy, wd, hh)
    d.box("", ix, iy + hh - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, row in enumerate(rows + ([total] if total else [])):
        ry = iy + hh + row_h * r
        is_total = total is not None and r == len(rows)
        if is_total:
            d.box("", ix, ry, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
        for c, (value, cx, wd) in enumerate(zip(row, xs, widths)):
            plain = r % 2 == 0 or is_total
            margin = clip_margin.get(c, 16) if isinstance(clip_margin, dict) else clip_margin
            shown = esc(_clip(value, wd, margin=8 if aligns[c] == "right" else margin, bold=is_total))
            d.box(f"<b>{shown}</b>" if is_total else shown, cx, ry, wd, row_h,
                  fill=WHITE if plain else GRAY_TINT, stroke=WHITE if plain else GRAY_TINT, size=SMALL, align=aligns[c], rounded=False)
            geometry[(r, c)] = (cx, ry, wd, row_h)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, width=sum(widths))


def _matrix(d: Diagram, x: float, y: float, title: str | None, row_w: float, groups: list[tuple[str | None, list[tuple[str, float]]]], row_heads: list[str],
            cells: list[list[str]], row_h: float = ROW, head_lines: int = 1, bold_rows: set[int] | None = None, levels: list[int] | None = None,
            rules: set[int] | None = None, title_lines: int | None = None, fills: dict | None = None, framed: bool = True, expanded: set[int] | None = None) -> dict:
    """A matrix visual: a title, optional group headings (the Year over its measures), the column headings (<br> where one breaks), the row
    headings (a level indents a row under its parent) and the values.  groups are (heading or None, [(column heading, width), ...]);
    bold_rows are drawn bold (a parent row or the total row) and rules puts a rule above a row.  fills maps (row, column) to a fill color.
    framed=False draws the grid alone, with no container or title, for a visual that holds two panes.
    Returns the cell geometry keyed (row, column) over the flattened value columns."""
    cols = [c for _, hs in groups for c in hs]
    inner = row_w + sum(wd for _, wd in cols)
    w = inner + 12
    two = any(g for g, _ in groups)
    gh = 22 if two else 0
    hh = row_h if head_lines == 1 else 15 * head_lines + 8
    if framed:
        label = f"<b>{esc(title)}</b>"
        th = 16 * (title_lines or kit.lines_for(label, w - 12, SMALL, bold=True)) + 4
        h = th + 12 + gh + hh + len(row_heads) * row_h
        ix, iy, _, _ = _frame(d, x, y, w, h, title, lines=title_lines)
    else:
        ix, iy = x, y
        h = gh + hh + len(row_heads) * row_h
    bold_rows, rules, levels, fills = bold_rows or set(), rules or set(), levels or [0] * len(row_heads), fills or {}
    cy = iy
    gx = ix + row_w
    if two:
        for g, hs in groups:
            gw = sum(wd for _, wd in hs)
            if g:
                d.text(f"<b>{esc(g)}</b>", gx, cy, gw, gh, size=SMALL, align="center", valign="middle")
            gx += gw
        cy += gh
    xs, cx = [], ix + row_w
    for head, wd in cols:
        xs.append(cx)
        d.text(f"<b>{_heads(head, wd)}</b>", cx, cy, wd - 4, hh, size=SMALL, align="right", valign="bottom")
        cx += wd
    rule_y = cy + hh - 1
    cy += hh
    geometry = {}
    for r, head in enumerate(row_heads):
        ry = cy + r * row_h
        bold = r in bold_rows
        text = "&nbsp;" * (5 * levels[r]) + esc(("– " if r in (expanded or set()) else "") + head)
        d.text(f"<b>{text}</b>" if bold else text, ix + 4, ry, row_w - 4, row_h, size=SMALL, align="left", valign="middle")
        for c, ((_, wd), vx) in enumerate(zip(cols, xs)):
            value = cells[r][c]
            assert not value or text_width(value, SMALL, bold) + 6 <= wd, f"{title}: {value!r} does not fit its {wd:.0f} px column"
            fill = fills.get((r, c), WHITE)
            d.box(f"<b>{esc(value)}</b>" if bold else esc(value), vx, ry, wd, row_h, fill=fill, stroke=fill, size=SMALL, align="right", rounded=False)
            geometry[(r, c)] = (vx, ry, wd, row_h)
        if r in rules:
            d.box("", ix, ry, inner, 1, fill=INK, stroke=INK, rounded=False)
    d.box("", ix, rule_y, inner, 1, fill=INK, stroke=INK, rounded=False)
    return dict(geometry=geometry, bottom=y + h, right=x + w, left=ix, width=inner, top_rows=cy, row_h=row_h, row_w=row_w, head_top=iy)


def _cards_visual(d: Diagram, x: float, y: float, w: float, items: list[tuple[str, str]], title: str | None = None, card_h: float = 76) -> dict:
    """A card visual with one field per card: the value above its label, the label over two lines (<br> in the label)."""
    th = 22 if title else 0
    h = th + card_h + 12
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    if title:
        d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 18, size=SMALL)
    gap = 6
    cw = (w - 12 - gap * (len(items) - 1)) / len(items)
    geo = []
    for i, (label, value) in enumerate(items):
        cx = x + 6 + i * (cw + gap)
        d.box("", cx, y + th + 6, cw, card_h, fill=WHITE, stroke=RULE, rounded=True)
        d.text(f"<b>{esc(value)}</b>", cx + 2, y + th + 12, cw - 4, 24, size=15, align="center")
        d.text("<br>".join(esc(p) for p in label.split("<br>")), cx + 2, y + th + 40, cw - 4, 34, size=SMALL, color=GRAY, align="center")
        geo.append((cx, y + th + 6, cw, card_h))
    return dict(bottom=y + h, cards=geo)


def _slicer_list(d: Diagram, x: float, y: float, w: float, title: str, entries: list[str], selected: str | None = None) -> tuple[float, tuple | None]:
    """A slicer in the Vertical list style: a check box and a name for each entry, the selected one filled and bold.  Returns its bottom and the
    geometry of the selected row."""
    h = 30 + 26 * len(entries) + 8
    d.box("", x, y, w, h, fill=WHITE, stroke=RULE, rounded=False)
    d.text(f"<b>{esc(title)}</b>", x + 6, y + 4, w - 12, 20, size=SMALL)
    row = None
    for i, name in enumerate(entries):
        ry = y + 30 + i * 26
        if name == selected:
            d.box("<b>✓</b>", x + 10, ry + 4, 16, 16, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False, valign="middle")
            row = (x + 4, ry, w - 8, 24)
        else:
            d.box("", x + 10, ry + 4, 16, 16, fill=WHITE, stroke=GRAY, rounded=False)
        d.text(f"<b>{esc(name)}</b>" if name == selected else esc(name), x + 32, ry + 2, w - 40, 20, size=SMALL, valign="middle")
    return y + h, row


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


def _polyline(d: Diagram, pts: list[tuple[float, float]], color: str = BLUE, width: float = 3) -> None:
    """One edge through the points, drawn straight between them (separate edges leave gaps at their joints)."""
    a, b = d.anchor(*pts[0]), d.anchor(*pts[-1])
    d.edge(a, b, color=color, width=width, points=pts[1:-1], meta="edgeStyle=none;rounded=0;")


def _icon(d: Diagram, x: float, y: float, kind: str, size: float = 11) -> None:
    """The conditional-format icons the model answer saves, GreyArrowUp, CircleMedium and GreyArrowDown: shapes that differ, in gray."""
    if kind == "up":
        d.vertex("", f"triangle;direction=north;html=1;fillColor={GRAY};strokeColor={GRAY};", x, y, size, size)
    elif kind == "down":
        d.vertex("", f"triangle;direction=south;html=1;fillColor={GRAY};strokeColor={GRAY};", x, y, size, size)
    else:
        d.vertex("", f"ellipse;html=1;fillColor={GRAY};strokeColor={GRAY};", x + 1, y + 1, size - 2, size - 2)


def _wrap(text: str, width: float, size: int = SMALL, bold: bool = False) -> list[str]:
    """A greedy word wrap measured with text_width."""
    out, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if not cur or text_width(trial, size, bold) <= width:
            cur = trial
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    return out


def _fmt1(x: float) -> str:
    """A measure with the format 0.0."""
    return f"{x:.1f}"


# -- IF-C4-1-A: the Validation page ------------------------------------------------------------------------------------------------------

def if_c4_1_a() -> Diagram:
    """The Validation page: the control totals by fiscal year with each materials pair outlined, and the five link cards."""
    g = ctx.values("case4.g1")
    r1 = ctx.values("case4.r1")
    data = ctx.data()
    page = "validation"
    t_control, t_links = _title(page, "controlTotals"), _title(page, "linkCards")
    assert (t_control, t_links) == (g["t_control"], g["t_links"]) == ("Control totals by fiscal year", "Links tested")
    cols = _projections(page, "controlTotals", "Values")
    assert cols == ["Year", "Net Income", "Total Assets", "Materials Received", "Receipts to 1045", "Materials Issued", "Issues from 1045"], cols
    _check_columns("Key Measures", cols[1:])
    cards = _projections(page, "linkCards", "Data")
    assert cards == ["Receipt Lines", "Receipts without a Requisition", "Issue Lines", "Issues without a Work Order", "Requisition Count"], cards
    _check_columns("Key Measures", cards)
    assert _year_filter(page, "controlTotals") == list(data.years), "the table is filtered to the years of the window"
    years = list(data.years)
    # the ledger side of each pair, from the postings to account 1045
    post = {(src, int(y)): v for src, y, v in data.q(
        "SELECT g.SourceDocumentType, substr(g.PostingDate, 1, 4), SUM(CASE WHEN g.SourceDocumentType = 'GoodsReceipt' THEN g.Debit ELSE g.Credit END) FROM GLEntry g "
        "JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = 1045 AND g.SourceDocumentType IN ('GoodsReceipt', 'MaterialIssue') GROUP BY 1, 2")}
    for i, y in enumerate(years):
        assert abs(post[("GoodsReceipt", y)] - r1["received"][i]) < 0.005 and abs(post[("MaterialIssue", y)] - r1["issued"][i]) < 0.005, "each materials pair agrees"
    rows = [[str(y), _money(r1["ni"][i]), _money(r1["assets"][i]), _money(r1["received"][i]), _money(post[("GoodsReceipt", y)]),
             _money(r1["issued"][i]), _money(post[("MaterialIssue", y)])] for i, y in enumerate(years)]
    # the link cards, counted on the dataset
    n_receipt = data.one("SELECT COUNT(*) FROM GoodsReceiptLine")
    n_receipt_free = data.one("SELECT COUNT(*) FROM GoodsReceiptLine l JOIN PurchaseOrderLine p ON p.POLineID = l.POLineID WHERE p.RequisitionID IS NULL")
    n_issue = data.one("SELECT COUNT(*) FROM MaterialIssueLine")
    n_issue_free = data.one("SELECT COUNT(*) FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID WHERE m.WorkOrderID IS NULL")
    n_req = data.one("SELECT COUNT(*) FROM PurchaseRequisition")
    assert (n_receipt, n_issue, n_req) == (r1["receipt_lines"], r1["issue_lines"], r1["requisitions"]) and n_receipt_free == 0 == n_issue_free, "the two link cards that count exceptions read zero"
    values = [f"{n_receipt:,}", f"{n_receipt_free:,}", f"{n_issue:,}", f"{n_issue_free:,}", f"{n_req:,}"]
    wt = [56, 104, 112, 134, 124, 134, 124]
    pad = 16
    labels = [c.replace(" without a ", "<br>without a ").replace("Receipt Lines", "Receipt<br>Lines").replace("Issue Lines", "Issue<br>Lines").replace("Requisition Count", "Requisition<br>Count") for c in cards]
    labels[1] = "Receipts without<br>a Requisition"
    labels[3] = "Issues without<br>a Work Order"
    callout = (f"<b>Each pair agrees to the cent in every year.</b> The model's materials, read through the receipt and issue lines and their items, equal the postings "
               f"to account 1045 from GoodsReceipt and MaterialIssue. The two cards that count exceptions read {values[1]}: every receipt line reaches a requisition and "
               "every issue line a work order.")

    def draw(d: Diagram) -> tuple[dict, dict, float]:
        t = _table_visual(d, pad, pad, t_control, cols, wt, rows, aligns=["left"] + ["right"] * 6, title_lines=1)
        cv = _cards_visual(d, pad, t["bottom"] + 14, 860 - 2 * pad, list(zip(labels, values)), title=t_links)
        return t, cv, kit.callout(d, callout, pad, cv["bottom"] + 12, 860 - 2 * pad, "teal")

    canvas_h = draw(Diagram("probe"))[2] + pad
    d = Diagram("The Validation Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    t, cv, _ = draw(d)
    for c0 in (3, 5):                                    # each materials pair: the model's total and the ledger's postings to 1045
        gx, gy, gw, gh = t["geometry"][(-1, c0)]
        total_w = t["geometry"][(-1, c0)][2] + t["geometry"][(-1, c0 + 1)][2]
        d.outline(gx + 1, gy + 1, total_w - 2, t["bottom"] - gy - 8, TEAL, width=2.5, front=True)
    for i in (1, 3):
        cx, cy, cw, ch = cv["cards"][i]
        d.outline(cx + 1, cy + 1, cw - 2, ch - 2, TEAL, width=2.5, front=True)
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, filtered to the {len(years)} years of the window; total rows are not drawn. "
             "Outlined in teal: each materials pair, the model's measure beside the ledger's postings, and the two link cards that read zero. The page's text box is not drawn.", canvas_h + 34)
    return d


# -- IF-C4-3-A: the Working Capital page ---------------------------------------------------------------------------------------------------

def if_c4_3_a() -> Diagram:
    """The Working Capital page: the measure slicer with the cycle selected, the line chart of the chosen measure, the matrix of all the
    measures at each quarter-end with icons on the days of supply, and the table of year-end measures beside their average-balance versions."""
    g = ctx.values("case4.g3")
    r3 = ctx.values("case4.r3")
    data = ctx.data()
    n4 = _n4()
    page = "workingCapital"
    t_slicer, t_line, t_matrix, t_average = (_title(page, n) for n in ("wcMeasure", "wcLine", "wcMatrix", "wcAverage"))
    assert (t_slicer, t_line, t_matrix, t_average) == (g["t_slicer"], g["t_line"], g["t_matrix"], g["t_average"])
    entries = re.findall(r'^\s+\("([^"]+)", NAMEOF', g["param"], re.M)
    assert entries == ["DSO", "DIO", "DPO", "Cash Conversion Cycle", "Materials Days", "Finished Goods Days"], entries
    slicer_filter = json.dumps(_visual(page, "wcMeasure")["visual"]["objects"]["general"][0]["properties"]["filter"])
    assert "'Cash Conversion Cycle'" in slicer_filter, "the slicer is saved with the cycle selected"
    assert _projections(page, "wcLine", "Y") == entries and _projections(page, "wcLine", "Category") == ["YearQuarter"]
    mcols = _projections(page, "wcMatrix", "Values")
    assert mcols == ["DSO", "DSO without Opening", "DIO", "Materials Days", "Materials Target Days", "Finished Goods Days", "Finished Goods Target Days", "DPO",
                     "DPO without Opening", "Cash Conversion Cycle", "Cycle without Opening"], mcols
    acols = _projections(page, "wcAverage", "Values")
    assert acols == ["Year", "DSO", "DSO on Average Balance", "DIO", "DIO on Average Balance", "Materials Days", "Materials Days on Average Balance", "DPO", "DPO on Average Balance"]
    _check_columns("Key Measures", mcols + acols[1:])
    assert _year_filter(page, "wcMatrix") == list(data.years) == _year_filter(page, "wcAverage") == _year_filter(page, "wcLine")
    qs = r3["qs"]
    first, last = qs[0], qs[-1]
    labels = [q["label"] for q in qs]
    assert len(qs) == 9 and labels[0] == f"{data.F}-Q4" and labels[-1] == f"{data.C}-Q4", "the measures have a value from the first full twelve months to Data Through"
    # the targets and the icons the matrix saves
    mat_target = data.one("SELECT MAX(p.TargetDaysSupply) FROM InventoryPolicy p JOIN Item i ON i.ItemID = p.ItemID WHERE i.ItemGroup IN ('Raw Materials', 'Packaging')")
    fg_target = data.one("SELECT MAX(p.TargetDaysSupply) FROM InventoryPolicy p JOIN Item i ON i.ItemID = p.ItemID WHERE i.ItemType = 'Finished Good'")
    assert (mat_target, fg_target) == (r3["raw"], r3["bought"][1]) == (28, 28)
    up, down = g["icon_up"], g["icon_down"]
    assert (up, down) == (1.25, 0.8)

    def icon(days: float, target: float) -> str:
        ratio = days / target
        return "up" if ratio >= up else "down" if ratio <= down else "dot"

    cells = [[_fmt1(q["dso"]), _fmt1(q["dso_x"]), _fmt1(q["dio"]), _fmt1(q["mat"]), _fmt1(mat_target), _fmt1(q["fg"]), _fmt1(fg_target), _fmt1(q["dpo"]),
              _fmt1(q["dpo_x"]), _fmt1(q["ccc"]), _fmt1(q["ccc_x"])] for q in qs]
    heads = ["DSO", "DSO<br>without<br>Opening", "DIO", "Materials<br>Days", "Materials<br>Target<br>Days", "Finished<br>Goods<br>Days", "Finished<br>Goods<br>Target<br>Days",
             "DPO", "DPO<br>without<br>Opening", "Cash<br>Conversion<br>Cycle", "Cycle<br>without<br>Opening"]
    cws = [58, 66, 58, 66, 66, 66, 66, 58, 66, 76, 66]
    row_lw = 72
    pad = 16
    sl_w = 214
    # the year-end versions and the versions on the average balance
    avg = {a["year"]: a for a in r3["avg"]}
    year_end = {int(q["label"][:4]): q for q in qs if q["label"].endswith("Q4")}
    arows = [[str(y), _fmt1(year_end[y]["dso"]), _fmt1(avg[y]["dso"]), _fmt1(year_end[y]["dio"]), _fmt1(avg[y]["dio"]), _fmt1(year_end[y]["mat"]), _fmt1(avg[y]["mat"]),
              _fmt1(year_end[y]["dpo"]), _fmt1(avg[y]["dpo"])] for y in data.years]
    aheads = ["Year", "DSO", "DSO on<br>Average<br>Balance", "DIO", "DIO on<br>Average<br>Balance", "Materials<br>Days", "Materials Days<br>on Average<br>Balance", "DPO", "DPO on<br>Average<br>Balance"]
    aw = [54, 56, 96, 56, 96, 82, 126, 56, 96]
    sl_h = 30 + 26 * len(entries) + 8
    line_h = sl_h
    probe = Diagram("probe")
    m = _matrix(probe, pad, pad + line_h + 10, t_matrix, row_lw, [(None, list(zip(heads, cws)))], labels, cells, head_lines=4)
    ta = _table_visual(probe, pad, m["bottom"] + 10, t_average, aheads, aw, arows, aligns=["left"] + ["right"] * 8, title_lines=1, head_lines=3)
    canvas_h = ta["bottom"] + pad
    d = Diagram("The Working Capital Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    sl_bottom, sel = _slicer_list(d, pad, pad, sl_w, t_slicer, entries, "Cash Conversion Cycle")
    d.outline(sel[0], sel[1], sel[2], sel[3], BLUE, width=2.5, front=True)
    # the line chart of the measure the slicer chose
    cx0 = pad + sl_w + 10
    ix, iy, iw, ih = _frame(d, cx0, pad, 860 - pad - cx0, line_h, t_line, lines=1)
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 10, ih - 40
    ticks = [0, 100, 200, 300, 400, 500]
    y_of = _vaxis(d, ix, left, plot_w, top, plot_h, ticks, lambda v: f"{v:.0f}")
    step = plot_w / len(labels)
    pts = [(left + step * (i + 0.5), y_of(q["ccc"])) for i, q in enumerate(qs)]
    _polyline(d, pts, BLUE, 3)
    for (px, py), q in zip(pts, qs):
        d.vertex("", f"ellipse;html=1;fillColor={BLUE};strokeColor={WHITE};strokeWidth=1;", px - 4, py - 4, 8, 8)
    for i in (0, len(qs) - 1):
        d.box(f"<b>{_fmt1(qs[i]['ccc'])}</b>", pts[i][0] - 22, pts[i][1] - 28, 44, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
    for i, lab in enumerate(labels):
        d.text(lab, left + step * i, top + plot_h + 4, step, 20, size=SMALL, color=GRAY, align="center")
    # the matrix, with the icons of the days of supply
    m = _matrix(d, pad, pad + line_h + 10, t_matrix, row_lw, [(None, list(zip(heads, cws)))], labels, cells, head_lines=4)
    for r, q in enumerate(qs):
        for c, days, target in ((3, q["mat"], mat_target), (5, q["fg"], fg_target)):
            gx, gy, gw, gh = m["geometry"][(r, c)]
            _icon(d, gx + 6, gy + (gh - 11) / 2, icon(days, target))
    for c in (3, 5):                                       # the two columns that carry icons
        gx, gy, gw, gh = m["geometry"][(0, c)]
        d.outline(gx + 1, gy, gw - 2, len(qs) * ROW, TEAL, width=2.5, front=True)
    ta = _table_visual(d, pad, m["bottom"] + 10, t_average, aheads, aw, arows, aligns=["left"] + ["right"] * 8, title_lines=1, head_lines=3)
    kinds_mat = [icon(q["mat"], mat_target) for q in qs]
    kinds_fg = [icon(q["fg"], fg_target) for q in qs]
    assert kinds_mat[0] == "dot" and all(k == "up" for k in kinds_mat[1:]) and all(k == "up" for k in kinds_fg), (kinds_mat, kinds_fg)
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, with the slicer saved on the cycle and the Year filter on the {len(data.years)} years of the window, so the axis starts at {labels[0]}, the "
             f"first quarter-end with twelve months behind it, and ends at {labels[-1]}, Data Through. Outlined in teal: the days of supply, with the icons the matrix saves, against the policy "
             f"targets of {mat_target} days: an up arrow from {up:g} times the target, a down arrow at {down:g} or below, a circle between them. Only the materials of {labels[0]} sit in that range; every other cell carries the up arrow. "
             "The tooltip page, hidden, and the page's text box are not drawn; total rows are not drawn.", canvas_h + 34)
    return d

# -- IF-C4-2-A: the Cash Bridge page ---------------------------------------------------------------------------------------------------------

STEP_KEYS = {"Net income": "net_income", "Depreciation": "depreciation", "Receivables": "receivables", "Inventories": "inventories",
             "Other current assets": "other_ca", "Payables": "payables", "Sales tax": "sales_tax", "Other current liabilities": "other_cl",
             "Fixed assets": "fixed", "Debt and equity": "debt_equity"}


def _steps() -> list[str]:
    """The bridge's steps in the order of the Account table's StepOrder column, read from the project's Power Query."""
    m = _g4().table_m("Account")
    line = next(l for l in m if l.startswith('#"Added Custom2"'))
    pairs = re.findall(r'\[Step\] = "([^"]+)" then (\d+)', line)
    names = [n for n, k in sorted(pairs, key=lambda p: int(p[1]))]
    assert names == list(STEP_KEYS), names
    assert [STEP_KEYS[n] for n in names] == _n4().STEPS
    return names


def _waterfall(d: Diagram, x: float, y: float, w: float, h: float, title: str, steps: list[str], values: list[float], ticks: list[float],
               total_label: str = "Total") -> dict:
    """A waterfall chart: each step floats from the running total and the total closes it.  Increases are teal, decreases coral and the total
    blue, every column carries a signed data label, and the category names wrap over up to three lines under the plot."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title, lines=1)
    left, plot_w = ix + 50, iw - 56
    label_h = 50
    top, plot_h = iy + 24, ih - 24 - label_h
    fmt = lambda v: (MINUS if v < 0 else "") + (f"{abs(v) / 1e6:.0f}M" if v else "0")   # noqa: E731
    y_of = _vaxis(d, ix, left, plot_w, top, plot_h, ticks, fmt, label_w=46)
    d.box("", left, y_of(0) - 1, plot_w, 2, fill=GRAY, stroke=GRAY, rounded=False)
    names = steps + [total_label]
    step = plot_w / len(names)
    running = 0.0
    geo = {}
    for i, name in enumerate(names):
        is_total = i == len(steps)
        v = running if is_total else values[i]
        low, high = (min(0, running), max(0, running)) if is_total else (min(running, running + v), max(running, running + v))
        color = BLUE if is_total else TEAL if v >= 0 else CORAL
        bx, bw = left + step * i + step * 0.15, step * 0.7
        d.box("", bx, y_of(high), bw, max(y_of(low) - y_of(high), 2), fill=color, stroke=color, rounded=False)
        sign = "" if is_total else ("+" if v >= 0 else MINUS)
        shown = f"{MINUS if is_total and v < 0 else ''}{abs(v) / 1e6:.2f}M"
        d.box(f"<b>{sign}{shown}</b>", bx - 6, y_of(high) - 22, bw + 12, 20, fill=WHITE, stroke=WHITE, size=SMALL, rounded=False)
        d.text("<br>".join(esc(p) for p in _wrap(name, step - 8)), left + step * i, top + plot_h + 4, step, label_h - 2, size=SMALL, color=GRAY, align="center")
        geo[name] = (bx, y_of(high), bw, max(y_of(low) - y_of(high), 2))
        if not is_total:
            running += v
    return dict(left=left, top=top, width=plot_w, height=plot_h, y_of=y_of, step=step, bars=geo)


def if_c4_2_a() -> Diagram:
    """The Cash Bridge page: the year slicer, the waterfall of the year selected, the bridge by year and the sections as recorded and restated."""
    g = ctx.values("case4.g2")
    r2 = ctx.values("case4.r2")
    data = ctx.data()
    n4 = _n4()
    page = "cashBridge"
    t_wf, t_bridge, t_restated, t_slicer = _title(page, "waterfall"), _title(page, "bridgeMatrix"), _title(page, "restated"), _title(page, "bridgeYear")
    assert (t_wf, t_bridge, t_restated) == (g["t_waterfall"], g["t_bridge"], g["t_restated"]) and t_slicer == "Fiscal year"
    assert _projections(page, "waterfall", "Category") == ["Step"] and _projections(page, "waterfall", "Y") == ["Cash Effect"]
    assert _projections(page, "bridgeMatrix", "Rows") == ["Step"] and _projections(page, "bridgeMatrix", "Columns") == ["Year"] and _projections(page, "bridgeMatrix", "Values") == ["Cash Effect"]
    assert _projections(page, "restated", "Rows") == ["Activity"] and _projections(page, "restated", "Columns") == ["Year"]
    assert _display_names(page, "restated", "Values") == ["As recorded", "Restated Cash Flow"]
    assert _projections(page, "bridgeYear", "Values") == ["Year"]
    _check_columns("Key Measures", ["Cash Effect", "Restated Cash Flow"])
    years, P, C = list(data.years), data.P, data.C
    assert _year_filter(page, "bridgeMatrix") == years and _year_filter(page, "restated") == [P, C]
    selected = json.dumps(_visual(page, "bridgeYear")["visual"]["objects"]["general"][0]["properties"]["filter"])
    assert f'"{C}L"' in selected, "the slicer is saved on the current year"
    cal = re.search(r"CALENDAR \( DATE \( (\d{4}), 1, 1 \), DATE \( (\d{4}), 12, 31 \) \)", _tmdl("tables/Date.tmdl"))
    assert (int(cal.group(1)), int(cal.group(2))) == (data.F, data.N), "the Date table runs to the next year"
    # the slicer lists the years a filter on it keeps (the window's complete years), or else every year of the Date table
    tiles = _year_filter(page, "bridgeYear") or list(range(data.F, data.N + 1))
    assert tiles in (years, list(range(data.F, data.N + 1))), tiles
    steps = _steps()
    bridge = {y: n4.bridge(data, y) for y in years}
    for y in years:
        assert abs(sum(bridge[y][STEP_KEYS[s]] for s in steps) - bridge[y]["cash"]) < 0.01, "the steps end at the change in cash (Test 3)"
    cur = bridge[C]
    assert all(abs(cur[k] - r2["cur"][k]) < 0.005 for k in ("net_income", "inventories", "cash")) and abs(bridge[P]["cash"] - r2["pri"]["cash"]) < 0.005
    restated = {P: n4.restated(data, P), C: n4.restated(data, C)}
    assert abs(restated[C]["operating"] - r2["rc"]["operating"]) < 0.005 and abs(restated[C]["financing"] - r2["rc"]["financing"]) < 0.005
    for y in (P, C):
        assert abs(restated[y]["operating"] + restated[y]["investing"] + restated[y]["financing"] - bridge[y]["cash"]) < 0.01, "restated, the sections still add to the change in cash"
    inv_ratio = -cur["inventories"] / cur["net_income"]
    assert 1.8 < inv_ratio < 2.0 and cur["inventories"] < -max(abs(cur[STEP_KEYS[s]]) for s in steps if s != "Inventories") * 1.5, "Inventories dwarf every other step"
    d = Diagram("The Cash Bridge Page")
    pad = 16
    # the bridge matrix, one level of rows (the steps, in StepOrder) and the years on the columns
    year_w = [max(70, math.ceil(max(text_width(_money(bridge[y][k]), SMALL, False) for k in list(STEP_KEYS.values()) + ["cash"]) + 10)) for y in years]
    rows_b = [[_money(bridge[y][STEP_KEYS[s]]) for y in years] for s in steps] + [[_money(bridge[y]["cash"]) for y in years]]
    heads_b = steps + ["Total"]
    # the restated matrix: the sections, sorted by name, each year over its recorded and restated cash flow
    sections = sorted(["Operating", "Investing", "Financing"])
    assert sections == ["Financing", "Investing", "Operating"]
    sec_key = {"Operating": "operating", "Investing": "investing", "Financing": "financing"}
    rows_r = [[_money(bridge[y][sec_key[s]]) if k == 0 else _money(restated[y][sec_key[s]]) for y in (P, C) for k in (0, 1)] for s in sections]
    rows_r.append([_money(bridge[y]["cash"]) for y in (P, C) for _ in (0, 1)])
    heads_r = sections + ["Total"]
    groups_r = [(str(y), [("As recorded", 82), ("Restated<br>Cash Flow", 82)]) for y in (P, C)]

    def draw(d: Diagram) -> tuple[dict, dict, dict, float]:
        sl_right = pbi.slicer_tiles(d, pad, pad, t_slicer, [str(y) for y in tiles], str(C), tile_w=64)
        inv, tax, pay = cur["inventories"], cur["sales_tax"], cur["payables"]
        top_h = kit.callout(d, f"<b>The inventories absorbed {_money(-inv)}</b>, nearly twice the {_money(cur['net_income'])} the year earned. The growth of the recorded sales tax payable "
                               f"({_signed(tax)}) and of the payables ({_signed(pay)}) held cash up; the steps end at the change in cash, {_signed(cur['cash'])}.",
                            sl_right + 10, pad, 860 - pad - sl_right - 10, "teal")
        y0 = max(pad + 56, top_h) + 10
        wf = _waterfall(d, pad, y0, 860 - 2 * pad, 312, t_wf, steps, [cur[STEP_KEYS[s]] for s in steps], [-4e6, -2e6, 0, 2e6, 4e6, 6e6])
        y1 = y0 + 312 + 10
        mb = _matrix(d, pad, y1, t_bridge, 132, [(None, [(str(y), w) for y, w in zip(years, year_w)])], heads_b, rows_b, bold_rows={len(steps)}, rules={len(steps)}, title_lines=2)
        mr = _matrix(d, mb["right"] + 10, y1, t_restated, 70, groups_r, heads_r, rows_r, head_lines=2, bold_rows={3}, rules={3}, title_lines=2)
        return wf, mb, mr, y1

    probe = Diagram("probe")
    _, mb, mr, y1 = draw(probe)
    assert mr["right"] <= 860 - pad + 1, f"the restated matrix ends at {mr['right']:.0f} px"
    cx0, cw = mr["left"] - 6, 860 - pad - (mr["left"] - 6)
    body = (f"<b>Entries that moved no cash.</b> In {C} the equipment financed by a note, {_money(r2['financed'])}, and the disposal, a loss of {_money(r2['disp']['loss'])} "
            f"with no proceeds, are no cash: as recorded, financing reads {_signed(cur['financing'])} and investing {_signed(cur['investing'])}; restated, "
            f"{_signed(restated[C]['financing'])} and {_money(restated[C]['investing'])}. The total does not change.")
    call_h = kit.callout(probe, body, cx0, mr["bottom"] + 10, cw, "amber")
    canvas_h = max(mb["bottom"], call_h) + pad
    d = Diagram("The Cash Bridge Page")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    wf, mb, mr, y1 = draw(d)
    kit.callout(d, body, cx0, mr["bottom"] + 10, cw, "amber")
    # the Inventories step in the waterfall and in the matrix
    bx, by, bw, bh = wf["bars"]["Inventories"]
    d.outline(bx - 2, by - 2, bw + 4, bh + 4, INK, width=2.5, front=True)
    r_inv = steps.index("Inventories")
    gx, gy, gw, gh = mb["geometry"][(r_inv, len(years) - 1)]
    d.outline(gx + 1, gy + 1, gw - 2, gh - 2, INK, width=2.5, front=True)
    # financing and investing of the current year, as recorded and restated
    fx, fy, fw, fh = mr["geometry"][(0, 2)]
    ex, ey, ew, eh = mr["geometry"][(1, 3)]
    d.outline(fx + 1, fy + 1, ex + ew - fx - 2, ey + eh - fy - 2, CORAL, width=2.5, front=True)
    _tabs(page, d, canvas_h + 4)
    listed = (f"filtered to the window's complete years, {tiles[0]} to {tiles[-1]}" if tiles == years
              else f"it lists the Date table's years, {data.F} to {data.N}")
    _note(d, f"Report view, page {_page_name(page)}, with the slicer saved on {C} ({listed}), the Cash step filtered out and the steps in "
             f"their sort order. Power BI adds the Total column, the change in cash. Outlined in ink: the Inventories step, in the waterfall and in the matrix; in coral: financing and investing of {C}, "
             "as recorded and restated. Matrix rows follow their sort, the restated sections by name; grand-total columns, the cash cards, the table of cash by year and the "
             "page's text box are not drawn.", canvas_h + 34)
    return d

# -- IF-C4-4-A: the Materials Build page -------------------------------------------------------------------------------------------------------

def _combo2(d: Diagram, x: float, y: float, w: float, h: float, title: str, cats: list[str], columns: list[tuple[str, list[float], str]],
            line: tuple[str, list[float], str], ticks: list[float], fmt, every: int = 3) -> dict:
    """A line and clustered column chart on one axis: two columns for each category and a line through the third series."""
    ix, iy, iw, ih = _frame(d, x, y, w, h, title, lines=1)
    lx = ix
    for name, _, color in columns:
        d.box("", lx, iy + 4, 12, 12, fill=color, stroke=color, rounded=False)
        tw = text_width(esc(name), SMALL, False) + 10
        d.text(esc(name), lx + 16, iy - 2, tw + 6, 20, size=SMALL)
        lx += 16 + tw + 18
    d.box("", lx, iy + 9, 16, 3, fill=line[2], stroke=line[2], rounded=False)
    d.vertex("", f"rhombus;html=1;fillColor={line[2]};strokeColor={line[2]};", lx + 4, iy + 5, 8, 8)
    d.text(esc(line[0]), lx + 22, iy - 2, text_width(esc(line[0]), SMALL, False) + 16, 20, size=SMALL)
    iy += 22
    ih -= 22
    left, plot_w = ix + 48, iw - 56
    top, plot_h = iy + 8, ih - 34
    y_of = _vaxis(d, ix, left, plot_w, top, plot_h, ticks, fmt)
    step = plot_w / len(cats)
    cw = step * 0.84 / len(columns)
    xs = []
    for i, cat in enumerate(cats):
        bx = left + step * i + step * 0.08
        for j, (_, vals, color) in enumerate(columns):
            if vals[i]:
                d.box("", bx + j * cw, y_of(vals[i]), cw, y_of(ticks[0]) - y_of(vals[i]), fill=color, stroke=color, rounded=False)
        xs.append(left + step * (i + 0.5))
        if i % every == 0:
            d.text(esc(cat), xs[-1] - step * every / 2, top + plot_h + 4, step * every, 20, size=SMALL, color=GRAY, align="center")
    pts = [(px, y_of(v)) for px, v in zip(xs, line[1])]
    _polyline(d, pts, line[2], 2.5)
    for px, py in pts:
        d.vertex("", f"rhombus;html=1;fillColor={line[2]};strokeColor={WHITE};strokeWidth=1;", px - 4, py - 4, 8, 8)
    return dict(left=left, top=top, width=plot_w, height=plot_h, xs=xs, y_of=y_of, step=step)


def _scrollbar(d: Diagram, right: float, top: float, height: float, shown: int, total: int) -> None:
    """A vertical scroll bar at a visual's right edge: the thumb is the share of the rows in view."""
    d.box("", right - 10, top, 6, height, fill=GRAY_TINT, stroke=GRAY_TINT, rounded=False)
    d.box("", right - 10, top, 6, max(height * shown / total, 12), fill=GRAY, stroke=GRAY, rounded=False)


def if_c4_4_a() -> Diagram:
    """The Materials Build page: receipts by channel against issues by month, the totals by year, the build by item group and item for the
    current year with the six raw materials at the top, and who approved the requisitions of each channel."""
    g = ctx.values("case4.g4")
    r4 = ctx.values("case4.r4")
    r1 = ctx.values("case4.r1")
    data = ctx.data()
    n4 = _n4()
    page = "materialsBuild"
    t_combo, t_year, t_build, t_appr = _title(page, "receiptsIssues"), _title(page, "channelByYear"), _title(page, "buildMatrix"), _title(page, "approvals")
    assert (t_combo, t_build, t_appr) == (g["t_receipts"], g["t_build"], g["t_approvals"])
    assert _projections(page, "receiptsIssues", "Y") == ["Supply Plan Receipts", "Shortfall Receipts"] and _projections(page, "receiptsIssues", "Y2") == ["Materials Issued"]
    cols = _projections(page, "channelByYear", "Values")
    assert cols == ["Year", "Supply Plan Receipts", "Shortfall Receipts", "Materials Received", "Materials Issued", "Materials Build"], cols
    assert _projections(page, "buildMatrix", "Rows") == ["ItemGroup", "ItemCode"] and _projections(page, "buildMatrix", "Values") == ["Materials Build"]
    assert _projections(page, "approvals", "Rows") == ["Channel", "ApproverTitle"] and _projections(page, "approvals", "Values") == ["Requisition Count", "Self-requested"]
    _check_columns("Key Measures", [c for c in cols if c != "Year"] + ["Requisition Count", "Self-requested"])
    _check_columns("Requisitions", ["Channel", "ApproverTitle"])
    years = list(data.years)
    C = data.C
    assert _year_filter(page, "receiptsIssues") == years == _year_filter(page, "channelByYear") and _year_filter(page, "buildMatrix") == [C]
    # monthly receipts by channel and issues, as the measures read them
    marks = ",".join("?" * len(n4.MATERIALS))
    rec = data.q(f"SELECT substr(g.ReceiptDate, 1, 7), {n4.CHANNEL}, SUM(l.ExtendedStandardCost) FROM GoodsReceiptLine l JOIN GoodsReceipt g ON g.GoodsReceiptID = l.GoodsReceiptID "
                 f"JOIN Item i ON i.ItemID = l.ItemID JOIN PurchaseOrderLine p ON p.POLineID = l.POLineID LEFT JOIN PurchaseRequisition r ON r.RequisitionID = p.RequisitionID "
                 f"WHERE i.ItemGroup IN ({marks}) GROUP BY 1, 2", *n4.MATERIALS)
    iss = dict(data.q(f"SELECT substr(m.IssueDate, 1, 7), SUM(l.ExtendedStandardCost) FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID = l.MaterialIssueID "
                      f"JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup IN ({marks}) GROUP BY 1", *n4.MATERIALS))
    plan = {m: v for m, ch, v in rec if ch == "Supply plan"}
    short = {m: v for m, ch, v in rec if ch == "Shortfall"}
    months = [f"{y}-{m:02d}" for y in years for m in range(1, 13)]
    plan_m, short_m, iss_m = [plan.get(m, 0.0) for m in months], [short.get(m, 0.0) for m in months], [iss.get(m, 0.0) for m in months]
    by_year = {row["year"]: row for row in r4["by_year"]}
    for y in years:                                       # the months add up to the guide's yearly receipts and to the issues of the Validation page
        mine = [i for i, m in enumerate(months) if m.startswith(str(y))]
        assert abs(sum(plan_m[i] for i in mine) - by_year[y]["plan"][1]) < 0.01 and abs(sum(short_m[i] for i in mine) - by_year[y]["short"][1]) < 0.01
        assert abs(sum(iss_m[i] for i in mine) - r1["issued"][years.index(y)]) < 0.01
    assert all(sum(plan_m[i] for i, m in enumerate(months) if m.startswith(str(y))) < sum(iss_m[i] for i, m in enumerate(months) if m.startswith(str(y))) for y in years), \
        "the supply plan alone stays below use every year"
    top_value = max(plan_m + short_m + iss_m)
    ticks = pbi.nice_ticks(0, top_value, 4)
    # the yearly table
    rows_y = []
    for i, y in enumerate(years):
        recv, issd = by_year[y]["plan"][1] + by_year[y]["short"][1], r1["issued"][i]
        assert abs(recv - r1["received"][i]) < 0.01
        rows_y.append([str(y), _money(by_year[y]["plan"][1]), _money(by_year[y]["short"][1]), _money(recv), _money(issd), _money(recv - issd)])
    heads_y = ["Year", "Supply Plan<br>Receipts", "Shortfall<br>Receipts", "Materials<br>Received", "Materials<br>Issued", "Materials<br>Build"]
    assert [h.replace("<br>", " ") for h in heads_y] == cols
    # the build of the current year by item group and item, sorted by the build
    build_rows = data.q("WITH r AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM GoodsReceiptLine l JOIN GoodsReceipt g ON g.GoodsReceiptID = l.GoodsReceiptID "
                        "WHERE substr(g.ReceiptDate, 1, 4) = ?1 GROUP BY 1), s AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM MaterialIssueLine l JOIN MaterialIssue m "
                        "ON m.MaterialIssueID = l.MaterialIssueID WHERE substr(m.IssueDate, 1, 4) = ?1 GROUP BY 1) SELECT i.ItemGroup, i.ItemCode, COALESCE(r.v, 0) - COALESCE(s.v, 0) "
                        "FROM Item i LEFT JOIN r ON r.ItemID = i.ItemID LEFT JOIN s ON s.ItemID = i.ItemID WHERE i.ItemGroup IN ('Raw Materials', 'Packaging') AND (r.v IS NOT NULL OR s.v IS NOT NULL)",
                        str(C))
    groups = {}
    for grp, code, v in build_rows:
        groups.setdefault(grp, []).append((code, v))
    totals = {grp: sum(v for _, v in items) for grp, items in groups.items()}
    order = sorted(groups, key=lambda grp: -totals[grp])
    assert order == ["Raw Materials", "Packaging"] and abs(sum(totals.values()) - r4["build"]) < 0.01
    flat = []
    for grp in order:
        flat.append((0, grp, totals[grp]))
        flat += [(1, code, v) for code, v in sorted(groups[grp], key=lambda it: -it[1])]
    top6 = [row for row in flat[1:7]]
    assert [code for _, code, _ in top6] == [t["code"] for t in r4["top_items"]] and all(code.startswith("RAW-") for _, code, _ in top6), "six raw materials at the top"
    assert abs(sum(v for _, _, v in top6) / r4["build"] - r4["share"]) < 1e-9
    shown = flat[:9]
    # who approved each channel
    channel_name = {"Shortfall": "Work-order shortfall", "Supply plan": "Supply plan", "Other": "Other"}
    appr = data.q(f"SELECT {n4.CHANNEL}, e.JobTitle, COUNT(*), COALESCE(SUM(r.RequestedByEmployeeID = r.ApprovedByEmployeeID), 0) FROM PurchaseRequisition r "
                  "LEFT JOIN Employee e ON e.EmployeeID = r.ApprovedByEmployeeID GROUP BY 1, 2")
    chans = sorted({channel_name[c] for c, *_ in appr})
    assert chans == ["Other", "Supply plan", "Work-order shortfall"]
    rows_a, lv_a, bold_a = [], [], set()
    for ch in chans:
        mine = sorted([(t or "", n, s) for c, t, n, s in appr if channel_name[c] == ch], key=lambda it: it[0])
        bold_a.add(len(rows_a))
        rows_a.append([f"{sum(n for _, n, _ in mine):,}", f"{sum(s for _, _, s in mine):,}"])
        lv_a.append(0)
        for t, n, s in mine:
            rows_a.append([f"{n:,}", f"{s:,}"])
            lv_a.append(1)
    labels_a = []
    for ch in chans:
        labels_a.append(ch)
        labels_a += [(t or "(Blank)") for t, _, _ in sorted([(t or "", n, s) for c, t, n, s in appr if channel_name[c] == ch], key=lambda it: it[0])]
    total_n, total_s = sum(n for _, _, n, _ in appr), sum(s for _, _, _, s in appr)
    assert total_n == r1["requisitions"]
    short_row = [r for r in appr if r[0] == "Shortfall"]
    assert len(short_row) == 1 and short_row[0][1] == r4["approver_title"] and short_row[0][2] == r4["n_short"] and short_row[0][3] == r4["self_requested"]
    rows_a.append([f"{total_n:,}", f"{total_s:,}"])
    labels_a.append("Total")
    lv_a.append(0)
    bold_a.add(len(rows_a) - 1)
    pad = 16
    d = Diagram("The Materials Build Page")
    probe = Diagram("probe")

    def draw(d: Diagram) -> tuple[float, float]:
        combo_h = 232
        _combo2(d, pad, pad, 860 - 2 * pad, combo_h, t_combo, months,
                [("Supply Plan Receipts", plan_m, BLUE), ("Shortfall Receipts", short_m, CORAL)], ("Materials Issued", iss_m, AMBER), ticks,
                lambda v: "0" if not v else f"{v / 1e6:.1f}M")
        ty = pad + combo_h + 10
        ty_vis = _table_visual(d, pad, ty, t_year, heads_y, [54, 114, 114, 114, 114, 114], rows_y, aligns=["left"] + ["right"] * 5, title_lines=1, head_lines=2)
        cx = ty_vis["right"] + 10
        kit.callout(d, f"<b>The supply plan alone stays below use.</b> Its receipts are under the issues of every year, and the shortfall channel's grow, "
                       f"{_money(by_year[years[0]]['short'][1])} to {_money(by_year[years[-1]]['short'][1])}.", cx, ty, 860 - pad - cx, "teal")
        my = ty_vis["bottom"] + 10
        mb = _matrix(d, pad, my, t_build, 150, [(None, [("Materials<br>Build", 104), ("", 16)])], [code for _, code, _ in shown],
                     [[_money(v), ""] for _, _, v in shown], head_lines=2, bold_rows={0}, levels=[lvl for lvl, _, _ in shown], title_lines=2, expanded={0})
        ma = _matrix(d, mb["right"] + 10, my, t_appr, 176, [(None, [("Requisition<br>Count", 100), ("Self-requested", 96)])], labels_a, rows_a, head_lines=2,
                     bold_rows=bold_a, levels=lv_a, rules={len(rows_a) - 1}, title_lines=2, expanded=bold_a - {len(rows_a) - 1})
        return ty_vis, mb, ma, my

    pr = draw(probe)
    canvas_h = max(pr[1]["bottom"], pr[2]["bottom"]) + pad
    pbi.canvas(d, 0, 0, 860, canvas_h)
    ty_vis, mb, ma, my = draw(d)
    assert ma["right"] <= 860 - pad + 1, f"the approvals matrix ends at {ma['right']:.0f} px"
    # the six raw materials, and the scroll bar of a matrix that holds more rows than it shows
    gx, gy, gw, gh = mb["geometry"][(1, 0)]
    d.outline(mb["left"] - 2, gy + 1, mb["width"] + 4 - 16, 6 * ROW - 2, TEAL, width=2.5, front=True)
    n_total = len(flat) + 1
    _scrollbar(d, mb["right"] - 4, mb["top_rows"], len(shown) * ROW, len(shown), n_total)
    cx = ma["right"] + 10
    cw = 860 - pad - cx
    y1 = kit.callout(d, f"<b>Six raw materials make up {_pct(r4['share'])} of the {C} build,</b> {_money(r4['build'])}. {_nowrap(top6[0][1])} alone is {_money(top6[0][2])}.", cx, my, cw, "teal")
    kit.callout(d, f"<b>One approver for the whole channel.</b> The {esc(r4['approver_title'])} approved all {r4['n_short']:,} shortfall requisitions, {r4['self_requested']} of them requested by the same employee.",
                cx, y1 + 10, cw, "amber")
    _tabs(page, d, canvas_h + 4)
    _note(d, f"Report view, page {_page_name(page)}, filtered to the {len(years)} years of the window (the build matrix to {C}). Columns and line share one axis here, because their ranges overlap. "
             f"The build matrix is sorted by the build, groups and items alike, and scrolls: its first {len(shown)} of {n_total} rows are drawn, with the other raw materials, the Packaging group "
             "and the total below. Outlined in teal: the six items at the top. Matrix rows sort by name; total rows of the tables, the requester table and the page's text box are not drawn.", canvas_h + 34)
    return d


def _pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


# -- IF-C4-5-A: the Reconciliations page ----------------------------------------------------------------------------------------------------------

def _camel_break(name: str, width: float) -> str:
    """A heading too wide for its column broken at the capital letter nearest its middle, as a two-line heading."""
    if text_width(f"<b>{name}</b>", SMALL, False) <= width - 8:
        return name
    cuts = [i for i, ch in enumerate(name) if i and ch.isupper()]
    k = min(cuts, key=lambda i: abs(i - len(name) / 2))
    return name[:k] + "<br>" + name[k:]


def _recon(part: str) -> Diagram:
    """The Reconciliations page in two figures, so that each prints at the frame's scale. The upper part: the roll-forward matrix by source
    document with the JournalEntry column outlined, and the cards that set each ledger balance against its open items. The lower part: the
    billing and the aged payables, and the Findings table."""
    assert part in ("upper", "lower")
    g = ctx.values("case4.g5")
    r5 = ctx.values("case4.r5")
    data = ctx.data()
    n4 = _n4()
    page = "reconciliations"
    t_roll, t_cards, t_billing, t_aging, t_findings = (_title(page, n) for n in ("rollForward", "reconCards", "billing", "aging", "findings"))
    assert (t_roll, t_cards, t_billing, t_aging, t_findings) == (g["t_roll"], g["t_cards"], g["t_billing"], g["t_aging"], g["t_findings"])
    assert _projections(page, "rollForward", "Rows") == ["AccountNumber"] and _projections(page, "rollForward", "Columns") == ["SourceDocumentType"] and _projections(page, "rollForward", "Values") == ["Balance"]
    cards = _projections(page, "reconCards", "Data")
    assert cards == ["Receivables", "Open Receivables", "Receivables Difference", "Payables", "Open Payables", "Payables Difference"], cards
    assert _projections(page, "billing", "Values") == ["Year", "Billing by Invoice Date", "Billing in Ledger", "Billing Difference"]
    assert _projections(page, "aging", "Values") == ["Bucket", "Open Payables", "Open Payable Invoices"]
    assert _projections(page, "findings", "Values") == ["Account", "Finding", "Amount", "Disposition", "Reconciles"]
    _check_columns("Key Measures", cards + ["Billing by Invoice Date", "Billing in Ledger", "Billing Difference", "Open Payables", "Open Payable Invoices", "Balance"])
    years = list(data.years)
    C = data.C
    assert _year_filter(page, "rollForward") == [C] == _year_filter(page, "reconCards") and _year_filter(page, "billing") == years
    accounts = json.dumps(_visual(page, "rollForward")["filterConfig"])
    assert all(f"{a}L" in accounts for a in r5["roll"]), "the six accounts of the roll-forward"
    # the roll-forward, by source document in name order
    roll = r5["roll"]
    accts = sorted(roll)
    sources = sorted({s for a in accts for s in roll[a]["parts"]})
    assert accts == ["1020", "1040", "1045", "2010", "2020", "2050"] and len(sources) == 11 and "JournalEntry" in sources
    for a in accts:
        assert abs(sum(roll[a]["parts"].values()) - roll[a]["total"]) < 0.01
    cells = [[_money(roll[a]["parts"][s]) if s in roll[a]["parts"] else "" for s in sources] + [_money(roll[a]["total"])] for a in accts]
    heads = sources + ["Total"]
    cw, rw = 126, 56
    assert rw + 6 * cw + 12 <= 860 - 32
    pane1, pane2 = list(range(0, 6)), list(range(6, 12))
    j_col = sources.index("JournalEntry")
    assert j_col in pane1
    # the cards
    ar, ap = roll["1020"]["total"], -roll["2010"]["total"]
    values = [_money(ar), _money(r5["open_ar"]), _money(r5["ar_diff"]), _money(ap), _money(r5["ap_total"]), _money(r5["ap_diff"])]
    assert abs(ar - r5["open_ar"] - r5["ar_diff"]) < 0.005 and abs(ap - r5["ap_total"] - r5["ap_diff"]) < 0.005
    labels = ["Receivables", "Open<br>Receivables", "Receivables<br>Difference", "Payables", "Open<br>Payables", "Payables<br>Difference"]
    # billing by invoice date against the ledger, and the aged payables without the invoices moved to notes
    asof = f"{C}-12-31"
    bi = {int(y): v for y, v in data.q("SELECT substr(InvoiceDate, 1, 4), SUM(GrandTotal) FROM SalesInvoice WHERE InvoiceDate <= ? GROUP BY 1", asof)}
    bl = {int(y): v for y, v in data.q("SELECT substr(g.PostingDate, 1, 4), SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = 1020 "
                                      "AND g.SourceDocumentType = 'SalesInvoice' GROUP BY 1")}
    for b in r5["billing"]:
        assert abs((bi[b["year"]] - bl[b["year"]]) - b["diff"]) < 0.005
    rows_b = [[str(y), _money(bi[y]), _money(bl[y]), _money(bi[y] - bl[y])] for y in years]
    notes_ids = tuple(c["id"] for c in r5["capital"])
    ap_rows = data.q("SELECT pi.PurchaseInvoiceID, pi.GrandTotal, (SELECT SUM(Amount) FROM DisbursementPayment p WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID AND p.PaymentDate <= ?1), "
                     "julianday(?1) - julianday(pi.DueDate) FROM PurchaseInvoice pi WHERE pi.ReceivedDate <= ?1", asof)
    names = ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]
    aged = {n: [0.0, 0] for n in names}
    for pid, gt, paid, dpd in ap_rows:
        bal = round(gt - (paid or 0), 2)
        if bal <= 0 or pid in notes_ids:
            continue
        k = names[0 if dpd <= 0 else 1 if dpd <= 30 else 2 if dpd <= 60 else 3 if dpd <= 90 else 4]
        aged[k][0] += bal
        aged[k][1] += 1
    assert abs(sum(v[0] for v in aged.values()) - r5["total_x"]) < 0.005 and abs(sum(v[0] for k, v in aged.items() if k != "Current") - r5["past_due_x"]) < 0.005
    rows_g = [[n, _money(aged[n][0]), f"{aged[n][1]:,}"] for n in names]
    # the findings, as a table without a sort of its own lists them: by its first column
    found = sorted(g["findings"], key=lambda r: r[0])
    rows_f = [[r[0], r[1], _money(float(r[2])), r[3], r[4]] for r in found]
    assert len(rows_f) >= 7 and {r[3] for r in rows_f} == {"Follow up", "Expected", "Misstatement"}
    rh = 20
    pad = 16

    def roll_visual(d: Diagram, y: float) -> tuple[dict, dict, float]:
        label = f"<b>{esc(t_roll)}</b>"
        th = 16 * kit.lines_for(label, 860 - 2 * pad - 12, SMALL, bold=True) + 4
        iw = 860 - 2 * pad
        ph1 = rh + 38 + 0
        h = th + 12 + (38 + 6 * rh) * 2 + 4
        _frame(d, pad, y, iw, h, t_roll, lines=1)
        gy = y + 4 + th + 2
        sets = []
        for pane, idx in enumerate((pane1, pane2)):
            heads_i = [_camel_break(heads[i], cw) for i in idx]
            sets.append(_matrix(d, pad + 6, gy + pane * (38 + 6 * rh + 4), None, rw, [(None, [(h, cw) for h in heads_i])], [a for a in accts],
                                [[cells[r][i] for i in idx] for r in range(len(accts))], row_h=rh, head_lines=2, framed=False))
        return sets[0], sets[1], y + h

    def cards_row(d: Diagram, y: float) -> dict:
        return _cards_visual(d, pad, y, 860 - 2 * pad, list(zip(labels, values)), title=t_cards, card_h=76)

    def tables_row(d: Diagram, y: float) -> tuple[dict, dict]:
        tb = _table_visual(d, pad, y, t_billing, ["Year", "Billing by<br>Invoice Date", "Billing in<br>Ledger", "Billing<br>Difference"], [52, 124, 118, 112], rows_b,
                           aligns=["left", "right", "right", "right"], title_lines=1, head_lines=2, row_h=rh)
        tg = _table_visual(d, tb["right"] + 10, y, t_aging, ["Bucket", "Open Payables", "Open Payable<br>Invoices"], [96, 128, 124], rows_g,
                           aligns=["left", "right", "right"], title_lines=1, head_lines=2, row_h=rh)
        return tb, tg

    def findings(d: Diagram, y: float) -> dict:
        w_f = [136, 0, 92, 104, 86]
        w_f[1] = 860 - 2 * pad - 12 - sum(w_f)
        return _table_visual(d, pad, y, t_findings, ["Account", "Finding", "Amount", "Disposition", "Reconciles"], w_f, rows_f, aligns=["left", "left", "right", "left", "left"],
                             title_lines=1, row_h=rh - 2, clip_margin={1: 52})

    def draw_upper(d: Diagram) -> tuple[dict, dict, dict, float]:
        p1, p2, y = roll_visual(d, pad)
        cv = cards_row(d, y + 6)
        return p1, p2, cv, cv["bottom"]

    def draw_lower(d: Diagram) -> tuple[dict, float]:
        tb, tg = tables_row(d, pad)
        fv = findings(d, max(tb["bottom"], tg["bottom"]) + 6)
        return fv, fv["bottom"]

    bottom = (draw_upper if part == "upper" else draw_lower)(Diagram("probe"))[-1]
    canvas_h = bottom + 12
    if part == "upper":
        note = (f"Report view, page {_page_name(page)}, the upper part, the matrix and the cards filtered to {C}. The matrix is one visual drawn in "
                "two panes, columns 1 to 6 and the rest after scrolling right. Outlined in coral: the JournalEntry column, which no subledger document in the extract supports, and the two "
                "differences. Total rows are not drawn. The billing and aging tables, the Findings table, the sales tax matrix and the page's text box are in the lower part or not drawn.")
    else:
        note = (f"Report view, page {_page_name(page)}, the lower part, the billing table filtered to the window's {len(years)} years. The Findings table lists its rows by its first column, "
                "as a table without a sort of its own does, and its full text is in the table of Step 6. The roll-forward matrix, the cards, the sales tax matrix and the page's text box "
                "are not drawn.")
    assert canvas_h + 34 + kit.height_for(note, 860, SMALL, pad=8) <= 980, f"the page needs {canvas_h + 34 + kit.height_for(note, 860, SMALL, pad=8):.0f} px"
    d = Diagram("The Reconciliations Page, Roll-Forward and Cards" if part == "upper" else "The Reconciliations Page, Cutoff, Aging and Findings")
    pbi.canvas(d, 0, 0, 860, canvas_h)
    if part == "upper":
        p1, p2, cv, _ = draw_upper(d)
        gx, gy, gw, gh = p1["geometry"][(0, j_col)]
        d.outline(gx + 1, gy - 1, gw - 2, len(accts) * rh + 2, CORAL, width=2.5, front=True)
        for i in (2, 5):
            cx, cy, cwid, ch = cv["cards"][i]
            d.outline(cx + 1, cy + 1, cwid - 2, ch - 2, CORAL, width=2.5, front=True)
    else:
        draw_lower(d)
    _tabs(page, d, canvas_h + 4)
    _note(d, note, canvas_h + 34)
    return d


def if_c4_5_a() -> Diagram:
    return _recon("upper")


def if_c4_5_c() -> Diagram:
    return _recon("lower")


FIGURES = {
    "IF-C4-0-A": if_c4_0_a,
    "IF-C4-0-B": if_c4_0_b,
    "IF-C4-1-A": if_c4_1_a,
    "IF-C4-2-A": if_c4_2_a,
    "IF-C4-3-A": if_c4_3_a,
    "IF-C4-3-B": if_c4_3_b,
    "IF-C4-4-B": if_c4_4_b,
    "IF-C4-4-A": if_c4_4_a,
    "IF-C4-5-A": if_c4_5_a,
    "IF-C4-5-B": if_c4_5_b,
    "IF-C4-5-C": if_c4_5_c,
    "IF-C4-6-A": if_c4_6_a,
}
