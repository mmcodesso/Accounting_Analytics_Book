"""Chapter 16 figures (audit monitoring, security, and sharing).

Every value is computed here with the rules of the chapter's tutorials: Chapter 8's five journal
entry flags (Weekend by CreatedDate, Backdated, SelfApproved, AboveLimit against the approver's
MaxApprovalAmount, RoundAmount), Chapter 12's purchase order and payroll flags, the exception
register that stacks them, and the cost-center roles of Tutorial 16.3, whose effects were checked
against Power BI Desktop 2.158's engine on reference models of the tutorials.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from functools import lru_cache

import excel as xl
import powerbi as pbi
from check_figures import text_width
from data import one, q, require_columns
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HIGHLIGHT,
                    INK, RULE, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
JE_FLAGS = ["Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"]
TESTS = ["JE Weekend", "JE Backdated", "JE SelfApproved", "JE AboveLimit", "JE RoundAmount",
         "PO SelfApproved", "PO AboveLimit", "PO AfterTermination",
         "PR PaidBeforeApproval", "PR AfterTermination", "PR SelfApproved"]
PROCESS = {"JE": "Journal entries", "PO": "Purchase orders", "PR": "Payroll"}
SECURITY = [("employee001@charlesriver.example", 1), ("employee006@charlesriver.example", 2),
            ("employee007@charlesriver.example", 3), ("employee004@charlesriver.example", 4),
            ("employee010@charlesriver.example", 5), ("employee005@charlesriver.example", 6),
            ("employee011@charlesriver.example", 7), ("employee012@charlesriver.example", 9),
            ("employee014@charlesriver.example", 10)]


def money(v: float) -> str:
    return pbi.amount(v) if abs(v) >= 0.005 else "0.00"


def mdy(s: str) -> str:
    return f"{int(s[5:7])}/{int(s[8:10])}/{s[:4]}"


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


# -- data -------------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def journal_entries() -> list[dict]:
    """Every journal entry with Chapter 8's five flags and its risk score (Tutorial 16.1)."""
    require_columns("JournalEntry", ["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount",
                                     "CreatedByEmployeeID", "CreatedDate", "ApprovedByEmployeeID"])
    out = []
    for jid, num, pd, et, amt, cb, cd, ab, lim in q(
            "SELECT j.JournalEntryID, j.EntryNumber, j.PostingDate, j.EntryType, j.TotalAmount, "
            "j.CreatedByEmployeeID, j.CreatedDate, j.ApprovedByEmployeeID, e.MaxApprovalAmount "
            "FROM JournalEntry j LEFT JOIN Employee e ON e.EmployeeID = j.ApprovedByEmployeeID "
            "ORDER BY j.EntryNumber"):
        created = dt.datetime.fromisoformat(cd)
        flags = dict(Weekend=int(created.weekday() >= 5), Backdated=int(created.date().isoformat() > pd),
                     SelfApproved=int(cb == ab), AboveLimit=int(amt > lim),
                     RoundAmount=int(round(amt % 1000, 6) == 0))
        out.append(dict(id=jid, number=num, posting=pd, type=et, amount=amt, approver=ab, limit=lim,
                        flags=flags, score=sum(flags.values())))
    assert len(out) == 851
    assert [sum(e["flags"][f] for e in out) for f in JE_FLAGS] == [17, 6, 7, 9, 4]
    assert sorted(Counter(e["score"] for e in out).items()) == [(0, 818), (1, 25), (2, 7), (4, 1)]
    return out


@lru_cache(maxsize=1)
def register() -> list[dict]:
    """The exception register of Tutorial 16.2: one row per exception per test."""
    rows = []
    for e in journal_entries():
        for f in JE_FLAGS:
            if e["flags"][f]:
                rows.append(dict(test=f"JE {f}", doc=e["number"], date=e["posting"], amount=e["amount"],
                                 employee=e["approver"]))
    for num, od, tot, cb, ab, lim, term in q(
            "SELECT p.PONumber, p.OrderDate, p.OrderTotal, p.CreatedByEmployeeID, p.ApprovedByEmployeeID, "
            "e.MaxApprovalAmount, e.TerminationDate FROM PurchaseOrder p "
            "LEFT JOIN Employee e ON e.EmployeeID = p.ApprovedByEmployeeID"):
        for test, failed in [("PO SelfApproved", cb == ab), ("PO AboveLimit", tot > lim),
                             ("PO AfterTermination", term is not None and od > term)]:
            if failed:
                rows.append(dict(test=test, doc=num, date=od, amount=tot, employee=ab))
    for rid, emp, net, ab, ad, paid, pend, pay, term in q(
            "SELECT r.PayrollRegisterID, r.EmployeeID, r.NetPay, r.ApprovedByEmployeeID, r.ApprovedDate, "
            "pp.PaymentDate, pe.PeriodEndDate, pe.PayDate, e.TerminationDate FROM PayrollRegister r "
            "LEFT JOIN PayrollPayment pp ON pp.PayrollRegisterID = r.PayrollRegisterID "
            "LEFT JOIN PayrollPeriod pe ON pe.PayrollPeriodID = r.PayrollPeriodID "
            "LEFT JOIN Employee e ON e.EmployeeID = r.EmployeeID"):
        for test, failed in [("PR PaidBeforeApproval", paid is not None and paid < ad),
                             ("PR AfterTermination", term is not None and pend > term),
                             ("PR SelfApproved", emp == ab)]:
            if failed:
                rows.append(dict(test=test, doc=f"Register {rid}", date=pay, amount=net, employee=ab))
    counts = Counter(r["test"] for r in rows)
    assert [counts[t] for t in TESTS] == [17, 6, 7, 9, 4, 9, 13, 3, 3, 3, 77], counts
    assert len({(r["test"], r["doc"]) for r in rows}) == len(rows) == 151
    return rows


@lru_cache(maxsize=1)
def populations() -> dict[str, int]:
    return {"Journal entries": one("SELECT COUNT(*) FROM JournalEntry")[0],
            "Purchase orders": one("SELECT COUNT(*) FROM PurchaseOrder")[0],
            "Payroll": one("SELECT COUNT(*) FROM PayrollRegister")[0]}


def employees() -> dict[int, tuple[str, str]]:
    return {i: (n, t) for i, n, t in q("SELECT EmployeeID, EmployeeName, JobTitle FROM Employee")}


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
    tests = pbi.model_table(d, "Tests", 0, top, ["TestID", "Test", "Process", "Chapter"], w=150)
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

def fig_16_07() -> Diagram:
    d = Diagram("What the Security Rules Reach")

    def rule_tag(t, text):
        d.box(f"<b>Rule</b>: {esc(text)}", t.x, t.y - 26, t.w, 22, fill=AMBER_TINT, stroke=AMBER, size=SMALL,
              align="left", rounded=False)

    sec = pbi.model_table(d, "Security", 0, 30, ["UserPrincipalName", "CostCenterID"], w=170)
    d.text("Not related to any table; the rules read it, and its own rule shows each user only their rows.",
           0, sec.y + sec.h + 4, 170, 80, size=SMALL, color=GRAY)
    cc = pbi.model_table(d, "CostCenter", 250, 30, ["CostCenterID", "CostCenterName"], w=170)
    rule_tag(cc, "the user's cost centers")
    emp = pbi.model_table(d, "Employee", 250, 196, ["EmployeeID", "CostCenterID"], w=170)
    rule_tag(emp, "the user's cost centers")
    item = pbi.model_table(d, "Item", 250, 340, ["ItemID", "ItemGroup"], w=170)
    rule_tag(item, "user is in Security")
    facts = [("GLEntry", 0, ["CostCenterID"], "Income Statement, Budget", cc, "CostCenterID"),
             ("BudgetLine", 86, ["CostCenterID"], "Budget", cc, "CostCenterID"),
             ("LaborTimeEntry", 196, ["EmployeeID"], "Plant", emp, "EmployeeID"),
             ("SalesInvoiceLine", 300, ["ItemID"], "Sales and Discounts, Promotions, Margins", item, "ItemID"),
             ("ProductionCompletionLine", 386, ["ItemID"], "Plant (standard hours)", item, "ItemID")]
    for name, y, cols, pages, dim, key in facts:
        t = pbi.model_table(d, name, 520, y + 30, cols, w=190)
        pbi.relationship(d, dim.right(key), t.left(cols[0]), [(470, dim.rows[key]), (470, t.rows[cols[0]])])
        d.text(f"<b>Pages</b>: {esc(pages)}", 716, y + 30, 144, 50, size=SMALL)
    note(d, "Each rule filters its table and, through active relationships, the fact tables on the many side. "
            "A page shows only the rows its reader may see: the Income Statement of a department manager is that "
            "department's alone, and nothing on the page says so unless a card names the cost centers shown.", 470, 56)
    return d


# -- fig-16-08 --------------------------------------------------------------------------------

def fig_16_08() -> Diagram:
    d = Diagram("From Desktop to the Report's Readers")
    desk = d.box("<b>Power BI Desktop</b><br>Charles River Reports.pbix", 0, 40, 180, 64, fill=WHITE, stroke=BLUE,
                 stroke_width=2, size=SMALL)
    ws = d.box("", 250, 0, 330, 250, fill=BLUE_TINT, stroke=BLUE, rounded=False)
    d.text("<b>Workspace in the Power BI service</b>", 258, 6, 314, 20, size=SMALL)
    d.box("<b>Semantic model</b> and <b>report</b>", 262, 32, 306, 30, fill=WHITE, stroke=BLUE, size=SMALL)
    d.box("<b>Admin, Member, Contributor</b><br>edit the content; row-level security does not apply",
          262, 74, 306, 50, fill=WHITE, stroke=GRAY, size=SMALL, align="left")
    d.box("<b>Viewer</b><br>reads; row-level security applies", 262, 134, 306, 44, fill=WHITE, stroke=TEAL,
          size=SMALL, align="left")
    d.text("Roles get their members under <b>Security</b>; <b>Test as role</b> checks them.", 262, 186, 306, 44,
           size=SMALL)
    d.arrow(desk, ws, exit=(1, 0.5), entry=(0, 0.3), label="Home > Publish")
    app = d.box("", 650, 0, 210, 250, fill=WHITE, stroke=BLUE, stroke_width=2, rounded=False)
    d.text("<b>App</b>", 658, 6, 194, 20, size=SMALL)
    d.box("<b>Audience: managers</b><br>the department report", 660, 34, 190, 60, fill=TEAL_TINT, stroke=TEAL,
          size=SMALL, align="left")
    d.box("<b>Audience: finance</b><br>the full package, with the Income Statement and Validation pages",
          660, 104, 190, 80, fill=BLUE_TINT, stroke=BLUE, size=SMALL, align="left")
    d.text("Readers need Pro or Premium Per User, unless the workspace is on a capacity.", 660, 192, 190, 56,
           size=SMALL)
    d.arrow(ws, app, exit=(1, 0.3), entry=(0, 0.3), label="Create app")
    # Refresh.
    src = d.box("<b>CharlesRiver.xlsx</b><br>on a local drive", 0, 300, 180, 50, fill=WHITE, stroke=GRAY, size=SMALL)
    gw = d.box("<b>On-premises data gateway</b>", 250, 300, 200, 50, fill=WHITE, stroke=GRAY, size=SMALL)
    d.arrow(src, gw, exit=(1, 0.5), entry=(0, 0.5))
    d.arrow(gw, ws, exit=(0.5, 0), entry=(0.3, 1), label="scheduled refresh")
    d.box("Or keep the workbook in OneDrive for work or school or SharePoint, refreshed without a gateway.",
          0, 370, 450, 44, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left")
    # Publish to web.
    pub = d.box("<b>Publish to web</b><br>a public link, no sign-in, all the model's data; no row-level security",
                650, 300, 210, 80, fill=CORAL_TINT, stroke=CORAL, stroke_width=2, size=SMALL, align="left")
    d.text("<b>Anyone on the internet: avoid for financial data</b>", 560, 384, 300, 20, size=SMALL, color=CORAL,
           align="right")
    d.arrow(ws, pub, exit=(1, 0.95), entry=(0, 0.4), points=[(615, 237), (615, 332)], label="Publish to web")
    note(d, "Sharing the .pbix file itself bypasses all of this: whoever opens it in Desktop sees every row.", 424)
    return d


# -- fig-16-09 --------------------------------------------------------------------------------

def fig_16_09() -> Diagram:
    d = Diagram("The Access Review")
    rows = q("SELECT cc.CostCenterName, cc.ManagerID, e.EmployeeName, e.JobTitle, e.EmploymentStatus, "
             "e.TerminationDate FROM CostCenter cc LEFT JOIN Employee e ON e.EmployeeID = cc.ManagerID "
             "ORDER BY cc.CostCenterName")
    terminated = [r[0] for r in rows if r[4] == "Terminated"]
    assert terminated == ["Executive", "Sales", "Warehouse"], terminated
    missing = q("SELECT EmployeeName, JobTitle FROM Employee WHERE JobTitle IN ('Sales Manager', 'Warehouse Manager') "
                "AND EmployeeID NOT IN (SELECT ManagerID FROM CostCenter) ORDER BY JobTitle")
    assert [m[1] for m in missing] == ["Sales Manager", "Warehouse Manager"]
    pbi.canvas(d, 0, 0, 860, 330)
    d.text("<b>Access Review</b>", 16, 12, 300, 20, size=SMALL, color=GRAY)
    widths = [170, 74, 140, 176, 124, 120]
    t = pbi.table_visual(d, 16, 36, ["CostCenterName", "ManagerID", "EmployeeName", "JobTitle", "EmploymentStatus",
                                     "TerminationDate"], widths,
                         [[r[0], str(r[1]), r[2], r[3], r[4], mdy(r[5]) if r[5] else ""] for r in rows])
    for i, r in enumerate(rows):
        if r[4] == "Terminated":
            x0, y0, _, _ = t["geometry"][(i, 0)]
            xl.emphasis(d, x0, y0, sum(widths), pbi.ROW)
    rd = [i for i, r in enumerate(rows) if r[0] == "Research and Development"][0]
    x0, y0, _, _ = t["geometry"][(rd, 3)]
    d.box("", x0, y0, widths[3], pbi.ROW, fill="none", stroke=AMBER, stroke_width=2, dashed=True, rounded=False)
    y = t["bottom"] + 8
    d.text("<b>In the employee records but not managers of record</b>: "
           + "; ".join(f"{esc(n)}, {esc(j)}" for n, j in missing), 16, y, 828, 22, size=SMALL)
    note(d, "Outlined in red: cost centers whose manager of record has left. Dashed: a manager of record who is "
            "an analyst. Access built on this column would go to the wrong people.", 340)
    return d


# -- fig-16-10 --------------------------------------------------------------------------------

RULE_LINES = ["[CostCenterID] IN CALCULATETABLE (",
              "    VALUES ( Security[CostCenterID] ),",
              "    Security[UserPrincipalName] = USERPRINCIPALNAME ()",
              ")"]


def fig_16_10() -> Diagram:
    d = Diagram("The Manage Security Roles Dialog")
    d.box("", 0, 0, 860, 420, fill=WHITE, stroke=GRAY, stroke_width=2, rounded=False)
    d.text("<b>Manage security roles</b>", 16, 10, 400, 24, size=14)
    d.text("Create new security roles and use filters to define row-level data restrictions.", 16, 36, 700, 20,
           size=SMALL, color=GRAY)
    d.box("Close Dialog", 750, 10, 96, 24, fill=WHITE, stroke=RULE, size=SMALL)
    # Roles.
    d.text("<b>Roles</b>", 16, 70, 200, 20, size=SMALL)
    xl.button(d, 16, 94, 120, "New role")
    for i, (name, on) in enumerate([("Cost Center Managers", True), ("Finance", False)]):
        d.box(f"<b>{name}</b>" if on else name, 16, 130 + i * 30, 200, 26, fill=BLUE_TINT if on else WHITE,
              stroke=BLUE if on else RULE, size=SMALL, align="left", rounded=False)
    # Tables.
    d.text("<b>Tables</b>", 236, 70, 200, 20, size=SMALL)
    tables = ["Account", "BudgetLine", "CostCenter", "Customer", "Date", "Employee", "GLEntry", "Item",
              "LaborTimeEntry", "Security"]
    filtered = {"CostCenter", "Employee", "Item", "Security"}
    for i, name in enumerate(tables):
        on = name == "CostCenter"
        label = f"{esc(name)}&nbsp;&nbsp;<i>(filter)</i>" if name in filtered else esc(name)
        d.box(f"<b>{label}</b>" if on else label, 236, 94 + i * 26, 190, 24, fill=BLUE_TINT if on else WHITE,
              stroke=BLUE if on else RULE, size=SMALL, align="left", rounded=False)
    # Rules, in the DAX editor.
    d.text("<b>Rules</b>", 446, 70, 200, 20, size=SMALL)
    xl.button(d, 446, 94, 190, "Switch to default editor")
    d.box("", 446, 130, 398, 120, fill=WHITE, stroke=BLUE, rounded=False)
    for i, line in enumerate(RULE_LINES):
        d.text(pbi.highlight_dax(line), 452, 136 + i * 22, 386, 22, size=SMALL)
    d.text("A rule returns true or false for each row of the table; only the rows that return true stay visible "
           "to the role's members.", 446, 262, 398, 60, size=SMALL, color=GRAY)
    xl.button(d, 676, 380, 76, "Save", primary=True)
    xl.button(d, 760, 380, 76, "Close")
    note(d, "The real dialog marks a table that has a rule with an icon; the mock writes the word filter. The "
            "Cost Center Managers role is selected, and its rule on CostCenter is open in the DAX editor.", 430)
    return d


# -- fig-16-11 --------------------------------------------------------------------------------

def fig_16_11() -> Diagram:
    d = Diagram("The Package Viewed as Two Managers")
    sales = one("SELECT SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
                "WHERE b.FiscalYear = 2026 AND b.CostCenterID = 2 AND a.AccountSubType = 'Operating Expense'")[0]
    act = one("SELECT SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
              "WHERE g.FiscalYear = 2026 AND g.CostCenterID = 2 AND a.AccountSubType = 'Operating Expense' "
              "AND g.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297')")[0]
    assert abs(sales - 2734179.05) < 0.01 and abs(act - 1018872.21) < 0.01
    wh = q("SELECT a.AccountSubType, SUM(g.Credit - g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
           "WHERE g.FiscalYear = 2026 AND g.CostCenterID = 3 AND a.AccountType IN ('Revenue', 'Expense') "
           "AND g.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297') GROUP BY 1")
    assert len(wh) == 1 and wh[0][0] == "Operating Expense"
    panels = [(0, "employee006@charlesriver.example", "Budget"), (436, "employee007@charlesriver.example",
                                                                   "Income Statement")]
    for x, user, page in panels:
        d.text(f"<b>{page}</b>, viewed as the {'Sales' if x == 0 else 'Warehouse'} Manager", x, 0, 424, 20,
               size=SMALL)
        pbi.canvas(d, x, 24, 424, 300)
        d.box(f"Viewing as <b>{user}</b> in the role <b>Cost Center Managers</b>", x + 8, 32, 316, 40,
              fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", rounded=False)
        xl.button(d, x + 330, 40, 86, "Stop viewing")
        if x == 0:
            pbi.table_visual(d, x + 16, 86, ["CostCenterName", "Budget", "Actual", "Variance %"], [110, 92, 92, 84],
                             [["Sales", money(sales), money(act), f"{100 * (act - sales) / sales:.1f}%"]])
            pbi.card(d, x + 16, 170, 200, 64, "Cost centers shown", "Sales")
        else:
            pbi.table_visual(d, x + 16, 86, ["AccountSubType", "P&L Amount"], [200, 140],
                             [[wh[0][0], money(wh[0][1])]], total=["Net Income", money(wh[0][1])])
            pbi.card(d, x + 16, 194, 200, 64, "Cost centers shown", "Warehouse")
    note(d, "The bar names the user and the role while View as is on; its exact wording in Desktop may differ. "
            "The card is the only sign on each page that it shows part of the company.", 336)
    return d


FIGURES = {
    "fig-16-01-monitoring-cycle": fig_16_01,
    "fig-16-02-exception-register": fig_16_02,
    "fig-16-03-je-flags": fig_16_03,
    "fig-16-04-entry-lines": fig_16_04,
    "fig-16-05-monitoring-page": fig_16_05,
    "fig-16-06-exception-detail": fig_16_06,
    "fig-16-07-rls-reach": fig_16_07,
    "fig-16-08-sharing-paths": fig_16_08,
    "fig-16-09-access-review": fig_16_09,
    "fig-16-10-manage-roles": fig_16_10,
    "fig-16-11-view-as": fig_16_11,
}
