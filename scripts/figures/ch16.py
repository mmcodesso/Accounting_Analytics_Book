"""Chapter 16 figures (audit monitoring and report assurance).

Every value is computed here with the rules of the chapter's tutorials: Chapter 8's five journal
entry flags (Weekend by CreatedDate, Backdated, SelfApproved, AboveLimit against the approver's
MaxApprovalAmount, RoundAmount), the purchase order and payroll flags of Chapter 12 and Exercise
12.5, the exception register that stacks them, and the dispositions of Tutorial 16.3, whose
measures and tests were checked against Power BI Desktop 2.158's engine on a reference model of
the tutorials. The security and sharing figures moved with their text to appendix_a.py.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from functools import lru_cache

import excel as xl
import powerbi as pbi
from check_figures import text_width
from data import REPO_ROOT, one, q, require_columns
from data import connection
from shared.calculations import bi_ch16 as public_calculations
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HIGHLIGHT,
                    INK, RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
JE_FLAGS = public_calculations.JE_FLAGS
TESTS = public_calculations.TESTS
PROCESS = public_calculations.PROCESS


def money(v: float) -> str:
    return pbi.amount(v) if abs(v) >= 0.005 else "0.00"


def mdy(s: str) -> str:
    return f"{int(s[5:7])}/{int(s[8:10])}/{s[:4]}"


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


# -- data -------------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def journal_entries() -> list[dict]:
    return public_calculations.journal_entries(connection())


@lru_cache(maxsize=1)
def register() -> list[dict]:
    return public_calculations.register(connection())


@lru_cache(maxsize=1)
def populations() -> dict[str, int]:
    return public_calculations.populations(connection())


def employees() -> dict[int, tuple[str, str]]:
    return public_calculations.employees(connection())


# -- fig-16-01 --------------------------------------------------------------------------------

def fig_16_01() -> Diagram:
    d = Diagram("The Monitoring Cycle")
    steps = [("Rule", "A test states its rule, population, frequency, and expected result", 150, 0),
             ("Population", "Each period's documents, reconciled to the ledger before testing", 300, 140),
             ("Exceptions", "The records that fail the rule, kept in the exception register", 150, 280),
             ("Disposition", "Internal audit reviews each exception: expected, follow up, or a deficiency",
              0, 140)]
    boxes = []
    for title, text, x, y in steps:
        b = d.box("", x, y + 20, 230, 104, fill=WHITE, stroke=BLUE, stroke_width=2)
        d.header_box(esc(title), x, y + 20, 230, 28, fill=BLUE, size=SMALL)
        d.text(esc(text), x + 8, y + 52, 214, 68, size=SMALL)
        boxes.append(b)
    d.arrow(boxes[0], boxes[1], exit=(1, 0.5), entry=(0.5, 0), label="runs every period on")
    d.arrow(boxes[1], boxes[2], exit=(0.5, 1), entry=(1, 0.5), label="produces")
    d.arrow(boxes[2], boxes[3], exit=(0, 0.5), entry=(0.5, 1), label="reviewed")
    d.arrow(boxes[3], boxes[0], exit=(0.5, 0), entry=(0, 0.5), label="changes the rule or the control")
    # Side panel: who does what.
    x0 = 572
    d.box("", x0, 20, 288, 384, fill=GRAY_TINT, stroke=RULE, rounded=False)
    d.text("<b>Who runs it</b>", x0 + 10, 28, 268, 20, size=SMALL)
    d.box("<b>Continuous auditing</b><br>Internal audit, for assurance to the board and management",
          x0 + 10, 54, 268, 76, fill=WHITE, stroke=BLUE, size=SMALL, align="left")
    d.box("<b>Continuous monitoring</b><br>Management, on its own controls; internal audit can rely on it "
          "when it is strong", x0 + 10, 140, 268, 76, fill=WHITE, stroke=TEAL, size=SMALL, align="left")
    d.text("<b>Who sees the results</b>", x0 + 10, 232, 268, 20, size=SMALL)
    d.text("The people who oversee the controls, such as the audit committee and the chief audit executive. "
           "Not the people whose transactions are tested: telling them what was flagged also tells them what "
           "was not.", x0 + 10, 256, 268, 140, size=SMALL)
    note(d, "Rule tests produce exceptions, failures of a stated rule; analytical tests produce anomalies, "
            "departures from an expectation that call for a closer look.", 420)
    return d


# -- fig-16-02 --------------------------------------------------------------------------------

def fig_16_02() -> Diagram:
    d = Diagram("The Exception Register in the Monitoring Model")
    reg = register()
    d.text("<b>Power Query: from flags to the register</b>", 0, 0, 500, 20, size=SMALL)
    sources = [("JournalEntry", JE_FLAGS, "JE Exceptions", "JE"),
               ("PurchaseOrder", ["SelfApproved", "AboveLimit", "AfterTermination"], "PO Exceptions", "PO"),
               ("PayrollRegister", ["PaidBeforeApproval", "AfterTermination", "SelfApproved"], "Payroll Exceptions",
                "PR")]
    exc_boxes = []
    y = 28
    for table, flags, exc, prefix in sources:
        h = 28 + 20 * len(flags)
        src = d.box("", 0, y, 200, h, fill=WHITE, stroke=BLUE)
        d.header_box(esc(table), 0, y, 200, 26, fill=BLUE, size=SMALL)
        d.text(esc(", ".join(flags)), 6, y + 28, 190, h - 30, size=SMALL)
        ex = d.box(f"<b>{esc(exc)}</b><br>{sum(1 for r in reg if r['test'].startswith(prefix))} rows",
                   330, y + h / 2 - 24, 170, 48, fill=GRAY_TINT, stroke=GRAY, dashed=True, size=SMALL)
        d.arrow(src, ex, exit=(1, 0.5), entry=(0, 0.5), label="unpivot, Value = 1")
        exc_boxes.append(ex)
        y += h + 14
    regbox = d.box("", 620, 70, 240, 150, fill=WHITE, stroke=BLUE, stroke_width=2)
    d.header_box("Exceptions", 620, 70, 240, 28, fill=BLUE, size=SMALL)
    d.text("TestID<br>DocumentNumber<br>EventDate<br>Amount<br>EmployeeID", 628, 102, 224, 114, size=SMALL)
    for ex in exc_boxes:
        d.arrow(ex, regbox, exit=(1, 0.5), entry=(0, 0.5))
    d.text("<b>Append</b>", 564, 150, 54, 20, size=SMALL)
    d.box("", 620, 236, 16, 16, fill=GRAY_TINT, stroke=GRAY, dashed=True, rounded=False)
    d.text("not loaded; feeds the append", 642, 233, 218, 22, size=SMALL)
    # The model.
    top = y + 16
    d.box("", 0, top - 8, 860, 1, fill=RULE, stroke=RULE, rounded=False)
    d.text("<b>The model: the register, its dimensions, and the populations</b>", 0, top, 600, 20, size=SMALL)
    top += 28
    tests = pbi.model_table(d, "Tests", 0, top, ["TestID", "Test", "Process", "Source"], w=150)
    exc = pbi.model_table(d, "Exceptions", 230, top, ["TestID", "DocumentNumber", "EventDate", "Amount",
                                                      "EmployeeID"], w=160)
    emp = pbi.model_table(d, "Employee", 230, top + 176, ["EmployeeID", "EmployeeName", "JobTitle"], w=160)
    date = pbi.model_table(d, "Date", 470, top + 60, ["Date", "Year", "YearMonth", "MonthName"], w=130)
    jl = pbi.model_table(d, "JournalLines", 690, top - 10, ["SourceDocumentID", "Debit", "Credit"], w=170)
    je = pbi.model_table(d, "JournalEntry", 690, top + 104, ["JournalEntryID", "PostingDate", "RiskScore"], w=170)
    po = pbi.model_table(d, "PurchaseOrder", 690, top + 218, ["OrderDate"], w=170)
    pr = pbi.model_table(d, "PayrollRegister", 690, top + 284, ["PayDate"], w=170)
    pbi.relationship(d, tests.right("TestID"), exc.left("TestID"))
    pbi.relationship(d, emp.left("EmployeeID"), exc.left("EmployeeID"),
                     [(205, emp.rows["EmployeeID"]), (205, exc.rows["EmployeeID"])])
    pbi.relationship(d, date.left("Date"), exc.right("EventDate"),
                     [(430, date.rows["Date"]), (430, exc.rows["EventDate"])])
    for t, col in [(je, "PostingDate"), (po, "OrderDate"), (pr, "PayDate")]:
        pbi.relationship(d, date.right("Date"), t.left(col), [(640, date.rows["Date"]), (640, t.rows[col])])
    pbi.relationship(d, je.left("JournalEntryID"), jl.left("SourceDocumentID"),
                     [(668, je.rows["JournalEntryID"]), (668, jl.rows["SourceDocumentID"])])
    bottom = max(t.y + t.h for t in [tests, exc, emp, date, je, po, pr, jl]) + 12
    note(d, "The three flagged tables stay in the model as the populations the rates divide by. "
            "<b>1</b> marks the table that holds the key and <b>*</b> the table that refers to it; "
            "the arrow shows the direction of the filter.", bottom)
    return d


# -- fig-16-03 --------------------------------------------------------------------------------

def fig_16_03() -> Diagram:
    d = Diagram("The Journal Entry Flags in Power Query")
    entries = journal_entries()[:9]
    xl.title_bar(d, 0, 0, 860, "Power Query Editor - JournalEntry")
    cols = [("EntryNumber", 118)] + [(f, 0) for f in JE_FLAGS] + [("RiskScore", 0)]
    cols = [(n, w or text_width(f"<b>{n}</b>", SMALL, True) + 20) for n, w in cols]
    grid_w = sum(w for _, w in cols)
    assert grid_w <= 650, grid_w
    y0 = 40
    x = 0
    for name, w in cols:
        d.box(f"<b>{esc(name)}</b>", x, y0, w, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left",
              rounded=False)
        x += w
    for r, e in enumerate(entries):
        y = y0 + 26 + r * 22
        values = [e["number"]] + [str(e["flags"][f]) for f in JE_FLAGS] + [str(e["score"])]
        x = 0
        for (name, w), v in zip(cols, values):
            d.box(esc(v), x, y, w, 22, fill=WHITE, stroke=RULE, size=SMALL,
                  align="left" if name == "EntryNumber" else "right", rounded=False)
            x += w
        if e["score"] > 0:
            xl.emphasis(d, grid_w - cols[-1][1], y, cols[-1][1], 22)
    assert [e["score"] for e in entries][:2] == [4, 2]
    status_y = y0 + 26 + len(entries) * 22 + 8
    xl.status_bar(d, 0, status_y, grid_w, f"15 COLUMNS, {len(journal_entries())} ROWS")
    d.text("Column profiling based on top 1000 rows", grid_w - 300, status_y + 2, 292, 20, size=SMALL,
           align="right")
    # Applied Steps.
    px = grid_w + 12
    pw = 860 - px
    steps_h = 28 + 14 * 19 + 8
    d.box("", px, y0, pw, max(status_y + 24 - y0, steps_h), fill=WHITE, stroke=RULE, rounded=False)
    d.box("<b>Applied Steps</b>", px, y0, pw, 26, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left",
          rounded=False)
    steps = ["Source", "Navigation", "Removed Other Columns", "Changed Type", "Merged Queries",
             "Expanded Employee", "Renamed Columns", "Added Custom", "Added Custom1", "Added Custom2",
             "Added Custom3", "Added Custom4", "Added Custom5", "Changed Type1"]
    for i, s in enumerate(steps):
        d.text(esc(s), px + 8, y0 + 28 + i * 19, pw - 12, 19, size=SMALL,
               color=BLUE if i == len(steps) - 1 else INK)
    note(d, "The first rows of the query, all entries of January 2024. Outlined: the entries whose risk score is "
            "above zero. The first is the opening balance entry, which fails four of the five tests.",
         max(status_y + 32, y0 + 28 + len(steps) * 19 + 8))
    return d


# -- fig-16-04 --------------------------------------------------------------------------------

def fig_16_04() -> Diagram:
    d = Diagram("The Risk Scores and an Entry's Ledger Lines")
    entries = journal_entries()
    by_score = defaultdict(lambda: [0, 0.0])
    for e in entries:
        by_score[e["score"]][0] += 1
        by_score[e["score"]][1] += e["amount"]
    pbi.canvas(d, 0, 0, 860, 300)
    d.text("<b>Journal Entries</b>", 16, 12, 300, 20, size=SMALL, color=GRAY)
    rows = [(0, str(s), [f"{n:,}", money(a)], "") for s, (n, a) in sorted(by_score.items())]
    rows.append((0, "Total", [f"{len(entries):,}", money(sum(e['amount'] for e in entries))], ""))
    pbi.matrix_visual(d, 16, 36, ["RiskScore", "Entries", "Entry Amount"], [90, 70, 130], rows)
    flagged = sorted([e for e in entries if e["score"] >= 2], key=lambda e: (-e["score"], e["number"]))
    assert len(flagged) == 8 and flagged[0]["number"] == "JE-2024-000001"
    t = pbi.table_visual(d, 344, 36, ["EntryNumber", "PostingDate", "EntryType", "RiskScore"], [114, 90, 190, 76],
                         [[e["number"], mdy(e["posting"]), e["type"], str(e["score"])] for e in flagged])
    x0, y0, _, _ = t["geometry"][(0, 0)]
    xl.emphasis(d, x0, y0, 470, pbi.ROW)
    d.text("Right-click > Drillthrough > Entry Lines", 344, t["bottom"] + 4, 470, 20, size=SMALL, color=CORAL)
    # The drill-through page.
    lines = q("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit FROM GLEntry g "
              "JOIN Account a ON a.AccountID = g.AccountID JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
              "WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryNumber = 'JE-2024-000001' ORDER BY g.GLEntryID")
    assert len(lines) == 18 and abs(sum(l[2] for l in lines) - sum(l[3] for l in lines)) < 0.005
    top = 316
    page_h = 28 + 20 * 22 + 40
    pbi.canvas(d, 0, top, 860, page_h)
    pbi.back_button(d, 16, top + 16)
    d.text("<b>Entry Lines</b>: JE-2024-000001", 96, top + 18, 400, 22, size=SMALL)
    pbi.table_visual(d, 16, top + 50, ["AccountNumber", "AccountName", "Debit", "Credit"], [116, 400, 150, 150],
                     [[str(n), name, money(dr) if dr else "", money(cr) if cr else ""] for n, name, dr, cr in lines],
                     total=["Total", "", money(sum(l[2] for l in lines)), money(sum(l[3] for l in lines))])
    note(d, "Top: the Journal Entries page, with the risk score distribution and the entries that failed two "
            "tests or more. Bottom: the Entry Lines page reached by drilling through on the opening balance entry.",
         top + page_h + 8)
    return d


# -- fig-16-05 --------------------------------------------------------------------------------

def fig_16_05() -> Diagram:
    d = Diagram("The Monitoring Page")
    reg = register()
    pops = populations()
    cell = defaultdict(int)
    for r in reg:
        cell[(r["test"], int(r["date"][5:7]))] += 1
    jan = sum(cell[(t, 1)] for t in TESTS)
    assert jan == 56 and all(cell[("PR SelfApproved", m)] >= 6 for m in range(1, 13))
    pbi.canvas(d, 0, 0, 860, 760)
    pbi.slicer_tiles(d, 16, 16, "Year", ["2024", "2025", "2026"], None, tile_w=56)
    d.text("All three years", 230, 40, 200, 20, size=SMALL, color=GRAY)
    # The heat map.
    widths = [156] + [33] * 12 + [48]
    x0, y0 = 16, 84
    w = sum(widths) + 12
    h = (len(TESTS) + 2) * pbi.ROW + 30
    ix, iy, _, _ = pbi.frame(d, x0, y0, w, h, "Exceptions by test and month")
    xs = [ix]
    for wd in widths[:-1]:
        xs.append(xs[-1] + wd)
    for c, head in enumerate(["TestID"] + MONTHS + ["Total"]):
        d.box(f"<b>{head}</b>", xs[c], iy, widths[c], pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL,
              align="left" if c == 0 else "right", rounded=False)
    d.box("", ix, iy + pbi.ROW - 1, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    for r, t in enumerate(TESTS):
        ry = iy + pbi.ROW * (r + 1)
        d.box(esc(t), xs[0], ry, widths[0], pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align="left",
              rounded=False)
        for m in range(1, 13):
            v = cell[(t, m)]
            fill = WHITE if v == 0 else AMBER_TINT if v < 5 else HIGHLIGHT
            d.box(str(v) if v else "", xs[m], ry, widths[m], pbi.ROW, fill=fill, stroke=WHITE, size=SMALL,
                  align="right", rounded=False)
        d.box(str(sum(cell[(t, m)] for m in range(1, 13))), xs[13], ry, widths[13], pbi.ROW, fill=WHITE,
              stroke=WHITE, size=SMALL, align="right", rounded=False)
    ty = iy + pbi.ROW * (len(TESTS) + 1)
    d.box("", ix, ty, sum(widths), 1, fill=INK, stroke=INK, rounded=False)
    d.box("<b>Total</b>", xs[0], ty, widths[0], pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL, align="left",
          rounded=False)
    for m in range(1, 13):
        d.box(f"<b>{sum(cell[(t, m)] for t in TESTS)}</b>", xs[m], ty, widths[m], pbi.ROW, fill=WHITE,
              stroke=WHITE, size=SMALL, align="right", rounded=False)
    d.box(f"<b>{len(reg)}</b>", xs[13], ty, widths[13], pbi.ROW, fill=WHITE, stroke=WHITE, size=SMALL,
          align="right", rounded=False)
    xl.emphasis(d, xs[1], iy + 2, widths[1], pbi.ROW * (len(TESTS) + 2) - 2)
    row_pr = TESTS.index("PR SelfApproved")
    xl.emphasis(d, xs[1], iy + pbi.ROW * (row_pr + 1), sum(widths[1:13]), pbi.ROW)
    # Legend of the shading.
    ly = y0 + h + 6
    d.box("", 16, ly + 3, 16, 16, fill=AMBER_TINT, stroke=RULE, rounded=False)
    d.text("1 to 4 exceptions", 36, ly, 140, 22, size=SMALL)
    d.box("", 180, ly + 3, 16, 16, fill=HIGHLIGHT, stroke=RULE, rounded=False)
    d.text("5 or more", 200, ly, 100, 22, size=SMALL)
    # Approvers.
    emp = employees()
    by_emp = Counter(r["employee"] for r in reg).most_common(5)
    assert emp[by_emp[0][0]][1] == "Accounting Manager"
    bx = x0 + w + 12
    pbi.bar_chart(d, bx, y0, 860 - 16 - bx, h, "Exceptions by EmployeeName", [emp[e][0] for e, _ in by_emp],
                  [n for _, n in by_emp], "", pbi.nice_ticks(0, by_emp[0][1], 2), label_w=104)
    # Rates.
    counts = Counter(r["test"] for r in reg)
    rate_rows = []
    for t in TESTS:
        pop = pops[PROCESS[t[:2]]]
        rate_rows.append([t, str(counts[t]), f"{pop:,}", f"{1000 * counts[t] / pop:.1f}"])
    pbi.table_visual(d, 16, ly + 34, ["TestID", "Exceptions", "Population", "Rate per 1,000"], [170, 100, 110, 120],
                     rate_rows, title="Rates by test")
    note(d, "All three years, by month of the year. Outlined: the January column and the row of registers approved "
            "by the employee they pay, which has exceptions in every month.", 770)
    return d


# -- fig-16-06 --------------------------------------------------------------------------------

def fig_16_06() -> Diagram:
    d = Diagram("The Exception Detail Page")
    emp = employees()
    rows = [r for r in register() if r["test"] == "PO AfterTermination" and r["date"][5:7] == "01"]
    assert [r["doc"] for r in rows] == ["PO-2025-003922", "PO-2026-010467"]
    term = one("SELECT TerminationDate FROM Employee WHERE EmployeeID = ?", rows[0]["employee"])[0]
    pbi.canvas(d, 0, 0, 860, 200)
    pbi.back_button(d, 16, 16)
    d.text("<b>Exception Detail</b>", 96, 18, 300, 22, size=SMALL)
    d.box("Drill-through filters: TestID is PO AfterTermination; MonthName is Jan", 420, 16, 424, 26,
          fill=BLUE_TINT, stroke=BLUE, size=SMALL)
    pbi.table_visual(d, 16, 56, ["DocumentNumber", "EventDate", "Amount", "EmployeeName", "JobTitle"],
                     [150, 110, 110, 150, 150],
                     [[r["doc"], mdy(r["date"]), money(r["amount"]), *emp[r["employee"]]] for r in rows])
    note(d, f"The page reached from the January cell of PO AfterTermination on the Monitoring page. The approver's "
            f"employment ended on {mdy(term)}.", 212)
    return d


# -- fig-16-07 --------------------------------------------------------------------------------

DISPOSITIONS = public_calculations.DISPOSITIONS


def reviewed_register() -> list[dict]:
    return public_calculations.reviewed_register(connection())


def fig_16_07() -> Diagram:
    d = Diagram("The Review Page")
    rows = reviewed_register()
    opened = [r for r in rows if not r["disposition"]]
    assert len(opened) == 136
    years = ["2024", "2025", "2026"]
    cell = Counter((r["test"], r["date"][:4]) for r in opened)
    tests = [t for t in TESTS if any(cell[(t, y)] for y in years)]
    assert len(tests) == 8 and "PO AfterTermination" not in tests
    pbi.canvas(d, 0, 0, 860, 504)
    pbi.card(d, 16, 16, 180, 64, "Reviewed Exceptions", str(len(rows) - len(opened)))
    pbi.card(d, 208, 16, 180, 64, "Open Exceptions", str(len(opened)))
    mrows = [(0, t, [str(cell[(t, y)]) if cell[(t, y)] else "" for y in years]
              + [str(sum(cell[(t, y)] for y in years))], "") for t in tests]
    mrows.append((0, "Total", [str(sum(cell[(t, y)] for t in tests)) for y in years] + [str(len(opened))], ""))
    widths = [168, 50, 50, 50, 52]
    pbi.matrix_visual(d, 16, 96, ["TestID"] + years + ["Total"], widths, mrows, title="Open Exceptions by year")
    pr = tests.index("PR SelfApproved")
    xl.emphasis(d, 22, 96 + 26 + pbi.ROW * (pr + 1), sum(widths), pbi.ROW)
    # Documents that fail two tests or more.
    per_doc = Counter(r["doc"] for r in rows)
    open_doc = Counter(r["doc"] for r in opened)
    docs = sorted([doc for doc, n in per_doc.items() if n >= 2], key=lambda doc: (-per_doc[doc], doc))
    assert len(docs) == 19 and docs[0] == "JE-2024-000001" and per_doc[docs[0]] == 4
    assert not any(doc.startswith("Register") for doc in docs)
    trows = [[doc, str(per_doc[doc]), str(open_doc[doc])] for doc in docs]
    tx = 420
    t = pbi.table_visual(d, tx, 16, ["DocumentNumber", "Exceptions", "Open Exceptions"], [150, 100, 130], trows,
                         title="Documents failing two tests or more")
    partly = [i for i, doc in enumerate(docs) if open_doc[doc] < per_doc[doc]]
    assert [docs[i] for i in partly] == ["PO-2024-000474", "PO-2025-003922", "PO-2026-010467"]
    for i in partly:
        x0, y0, _, _ = t["geometry"][(i, 0)]
        d.box("", x0, y0, 380, pbi.ROW, fill="none", stroke=AMBER, stroke_width=2, dashed=True, rounded=False)
    assert t["bottom"] <= 496, t["bottom"]
    note(d, "Outlined in red: the registers approved by their own employee, most of the open exceptions and one "
            "design finding. Dashed: orders reviewed for one of their two tests, still open for the other.", 514)
    return d


# -- fig-16-08 --------------------------------------------------------------------------------

TEST_4 = """// Test 4: the purchase orders have no gaps, and three registers were never paid
EVALUATE
VAR Numbers =
    SELECTCOLUMNS (
        PurchaseOrder,
        "Number", VALUE ( RIGHT ( PurchaseOrder[PONumber], 6 ) )
    )
VAR Unpaid =
    FILTER ( PayrollRegister, ISBLANK ( PayrollRegister[PaymentDate] ) )
RETURN
    ROW (
        "Orders", COUNTROWS ( PurchaseOrder ),
        "First number", MINX ( Numbers, [Number] ),
        "Last number", MAXX ( Numbers, [Number] ),
        "Registers", COUNTROWS ( PayrollRegister ),
        "Registers not paid", COUNTROWS ( Unpaid )
    )"""


def fig_16_08() -> Diagram:
    d = Diagram("Test 4 in DAX Query View")
    tutorial = (REPO_ROOT / "chapters" / "16-audit-monitoring" / "_tutorial-03.qmd").read_text(encoding="utf-8")
    assert TEST_4 in tutorial, "Test 4 differs from Tutorial 16.3"
    orders, first, last = one("SELECT COUNT(*), MIN(CAST(substr(PONumber, -6) AS INTEGER)), "
                              "MAX(CAST(substr(PONumber, -6) AS INTEGER)) FROM PurchaseOrder")
    regs, unpaid = one("SELECT COUNT(*), SUM(pp.PayrollRegisterID IS NULL) FROM PayrollRegister r "
                       "LEFT JOIN PayrollPayment pp ON pp.PayrollRegisterID = r.PayrollRegisterID")
    assert (orders, first, last, regs, unpaid) == (18832, 1, 18832, 8197, 3)
    pane_w = 150
    win = pbi.window(d, 640, view="DAX query", tab="Home", tabs=pbi.QUERY_TABS, panes=["Data"], pane_w=pane_w,
                     buttons=["Format", "Comment", "Uncomment", "Find", "Replace", "Command palette"],
                     file="Audit Monitoring")
    x, w = win.canvas_x + 8, win.canvas_w - 16
    bottom = pbi.dax_query_editor(d, x, win.top + 10, w, TEST_4, ["Tests"], "Tests")
    res = pbi.dax_results(d, x, bottom + 12, ["[Orders]", "[First number]", "[Last number]", "[Registers]",
                                              "[Registers not paid]"], [90, 120, 120, 100, 160],
                          [[str(orders), str(first), str(last), str(regs), str(unpaid)]])
    assert res["bottom"] <= win.bottom, res["bottom"]
    xl.emphasis(d, *res["geometry"][(0, 4)])
    for i, name in enumerate(["Key Measures", "Date", "Employee", "Exceptions", "JournalEntry", "JournalLines",
                              "PayrollRegister", "PurchaseOrder", "Tests"]):
        d.text(esc(name), win.panes_x + 8, win.top + 34 + i * 26, pane_w - 12, 22, size=SMALL)
    d.text("<i>The Tests tab of Audit Monitoring.pbix after Run. The order numbers run from 1 to the number of "
           "orders, so none is missing. Outlined: the three registers with no payment record. The editor shows Test 4 "
           "alone; in your Tests tab it follows Tests 1 to 3.</i>",
           0, win.bottom + 10, 860, 40, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-16-01-monitoring-cycle": fig_16_01,
    "fig-16-02-exception-register": fig_16_02,
    "fig-16-03-je-flags": fig_16_03,
    "fig-16-04-entry-lines": fig_16_04,
    "fig-16-05-monitoring-page": fig_16_05,
    "fig-16-06-exception-detail": fig_16_06,
    "fig-16-07-review-page": fig_16_07,
    "fig-16-08-population-test": fig_16_08,
}
