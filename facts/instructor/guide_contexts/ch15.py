"""Chapter 15's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 15 turns the Chapter 14 model into a reporting package, so the guides do the same four jobs as Chapters 13 and 14:

- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll flags the wording instead of leaving it stale,
- they supply what each exercise's steps need beyond its registered note (ch15.ex1 to ch15.ex6): above all the symptom
  of each wrong version a guide names (a Ledger Detail table built on Debit and Credit instead of the P&L measure, a
  running sum that never restarts, a labor cost that includes non-manufacturing time, a what-if lift with the
  discount left unscaled, benchmarks fitted on the start-up month, an inner join that drops the lines without an
  operation, a blank counted as a disagreement), computed read-only on the dataset the way the model would show it,
- they quote the DAX, the Power Query M and the parameter tables of the model answer from the solution project itself
  (outputs/companion/solutions/Chapter15-exercises-pbi), so a quoted measure cannot drift from the file the instructor
  opens: a quote that is not found in the project is a failed claim,
- they supply the chapter note's counts (exercises, questions, slides, tutorial steps, checks) from the chapter's files.

Keys: ch15.chapter (the chapter note) and ch15.g1 to ch15.g6 (the exercises; each is used next to the registered note
ch15.ex1 to ch15.ex6 that supplies the values of the exercise's instructor note). The tutorials' values come from the
registered notes ch15.t1 to ch15.t3.

What the project proves and what only Desktop shows: the project encodes the model and the visual structure, and its
Checks tab (DAX query view) recomputes every value of the tutorials and exercises, so a result is "proved" when a
Checks row names it. Two kinds of result are computed inside a visual, and no Checks row can read them: a visual
calculation (the YTD and Change columns of Exercise 15.2, the moving average of Tutorial 15.3) and the Analytics-pane
forecast (Exercise 15.5). How a visual renders (labels, icons, colors, the tooltip) is visible only in Desktop. The
guides state no forecast value.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list
from guide_contexts.ch13 import _block, steps, version
from notes import ch15 as n15

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "15-management-reports"
DECK = REPO / "slides" / "chapter-15" / "index.qmd"
PROJECT = REPO / "outputs" / "companion" / "solutions" / "Chapter15-exercises-pbi" / "Chapter 15 Exercises - Solutions"
MODEL = PROJECT / "Chapter 15 Exercises - Solutions.SemanticModel"
REPORT = PROJECT / "Chapter 15 Exercises - Solutions.Report"

SCHEMA = {
    "GLEntry": ["GLEntryID", "FiscalYear", "VoucherNumber", "PostingDate", "AccountID", "Debit", "Credit", "SourceDocumentType", "CostCenterID"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"],
    "JournalEntry": ["EntryNumber", "EntryType"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceDate"],
    "SalesInvoiceLine": ["SalesInvoiceID", "ItemID", "Quantity", "BaseListPrice", "UnitPrice", "Discount", "LineTotal", "PromotionID"],
    "PromotionProgram": ["PromotionID", "PromotionName", "DiscountPct", "ScopeType", "EffectiveStartDate", "EffectiveEndDate"],
    "Item": ["ItemID", "ItemGroup", "StandardCost", "StandardLaborHoursPerUnit"],
    "BudgetLine": ["FiscalYear", "Month", "AccountID", "CostCenterID", "BudgetAmount", "BudgetCategory"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
    "LaborTimeEntry": ["LaborTimeEntryID", "WorkOrderOperationID", "TimeClockEntryID", "WorkDate", "LaborType", "RegularHours",
                       "OvertimeHours", "ExtendedLaborCost"],
    "WorkOrderOperation": ["WorkOrderOperationID", "WorkCenterID", "ActualEndDate"],
    "TimeClockEntry": ["TimeClockEntryID", "WorkCenterID"],
    "WorkCenter": ["WorkCenterID", "WorkCenterName"],
    "ProductionCompletion": ["ProductionCompletionID", "CompletionDate"],
    "ProductionCompletionLine": ["ProductionCompletionID", "ItemID", "QuantityCompleted"],
}
SUBTYPE = "Other Income or Expense"
DIRECT, INDIRECT = "Direct Manufacturing", "Indirect Manufacturing"
PAGES = ["about", "salesDiscounts", "validation", "review", "margins", "incomeStatement", "promotions", "promotionDetail",
         "promotionTooltip", "budget", "costCenterDetail", "plant", "ledgerDetail", "ex152", "ex153", "ex154", "ex155", "ex156",
         "notes"]


# --- helpers ---------------------------------------------------------------------------------------------------------

def need(d, claim, *tables: str) -> None:
    """Claims that each table and the columns the guides name are in the database."""
    schema(d, claim, {t: SCHEMA[t] for t in (tables or SCHEMA)})


def _model_text(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def table_m(name: str) -> list[str]:
    """The M of a loaded table's partition in the solution project, one stripped line per step."""
    return _block(_model_text(f"tables/{name}.tmdl"), "source =")


def expression_m(name: str) -> list[str]:
    """The M of a query that does not load (Enable load cleared), from expressions.tmdl."""
    return _block(_model_text("expressions.tmdl"), f"expression {name} =")


def measure_table() -> dict[str, str]:
    """Every measure of every table of the project as the formula bar reads it: `Name = expression`, the body dedented."""
    out: dict[str, str] = {}
    for path in sorted((MODEL / "definition" / "tables").glob("*.tmdl")):
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = re.match(r"^\tmeasure (?:'([^']+)'|(\S+)) =(.*)$", line)
            if not m:
                continue
            name, first = m.group(1) or m.group(2), m.group(3).strip()
            body, j = [], i + 1
            while j < len(lines) and lines[j].startswith("\t\t\t"):
                body.append(lines[j][3:].rstrip())
                j += 1
            out[name] = f"{name} = {first}" if first and not body else f"{name} =\n" + "\n".join(body)
    return out


def measure(claim, name: str) -> str:
    found = measure_table().get(name)
    claim(found is not None, f"the solution project has the measure {name}")
    return found or ""


def check_expr(claim, label: str) -> str:
    """The DAX expression of one row of the project's Checks tab (DAX query view), found by its label."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    m = re.search(r'"Check", "' + re.escape(label) + r'", "Expected", .*?, "Actual", (.*?), "Agrees"', text)
    claim(m is not None, f"the Checks tab has the row {label!r}")
    return m.group(1) if m else ""


def _visual(page: str, name: str) -> dict:
    return json.loads((REPORT / "definition" / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))


def visual_title(claim, page: str, name: str) -> str:
    """The title of a visual of the solution project's report page, as Desktop shows it."""
    try:
        v = _visual(page, name)
        title = v["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"].strip("'").replace("''", "'")
    except (OSError, KeyError, IndexError, ValueError):
        title = ""
    claim(title != "", f"the visual {name} of page {page} in the solution project has a title")
    return title


def calcs(claim, page: str, name: str) -> dict[str, str]:
    """The visual calculations of a visual, by name: `YTD = RUNNINGSUM ( [Net Income] )` is read from the report file."""
    out = {}
    for role in _visual(page, name)["visual"]["query"]["queryState"].values():
        for p in role["projections"]:
            nv = p["field"].get("NativeVisualCalculation")
            if nv:
                out[nv["Name"]] = f"{nv['Name']} = {nv['Expression']}"
    claim(bool(out), f"the visual {name} of page {page} holds visual calculations")
    return out


def source_of(claim, table: str) -> str:
    """The DAX of a calculated table's partition, as the parameter dialogs write it."""
    lines = _block(_model_text(f"tables/{table}.tmdl"), "source =")
    claim(bool(lines), f"the table {table} of the solution project is a calculated table")
    if len(lines) > 2 and lines[0] == "{":
        return "\n".join([lines[0]] + ["    " + l for l in lines[1:-1]] + [lines[-1]])
    return "\n".join(lines)


def column_line(claim, table: str, column: str) -> str:
    text = _model_text(f"tables/{table}.tmdl")
    m = re.search(r"^\tcolumn " + re.escape(column) + r" = (.+)$", text, re.M)
    claim(m is not None, f"the table {table} of the solution project has the calculated column {column}")
    return f"{column} = {m.group(1)}" if m else ""


def query_tab(name: str) -> str:
    return (MODEL / "DAXQueries" / f"{name}.dax").read_text(encoding="utf-8").strip()


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise \d+\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import package
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/15-management-reports/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 15\b")
    letters, _ = package.answer_key(comment)
    key = {i: a for i, a in enumerate(letters, 1)}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


def step_counts() -> dict[int, int]:
    return {k: len(re.findall(r"^\*\*Step \d+\.", (CHAPTER / f"_tutorial-0{k}.qmd").read_text(encoding="utf-8"), re.M))
            for k in (1, 2, 3)}


def check_sections() -> dict[str, int]:
    """The rows of the Checks tab by section (Tutorial 13.1 ... Exercise 15.6)."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for sec in re.findall(r'ROW \( "Section", "([^"]*)"', text):
        counts[sec] = counts.get(sec, 0) + 1
    return counts


def lift(price: float, cost: float, discount: float, commission: float = n15.CASE_RATE) -> float:
    """Exercise 15.4's break-even lift: the contribution per unit without the discount over the one with it, less one."""
    return (price * (1 - commission) - cost) / (price * (1 - discount) * (1 - commission) - cost) - 1


def net_income_by_month(d, keep_closes: bool) -> list[tuple[str, float]]:
    where = "" if keep_closes else f"AND {d.no_closes()}"
    return d.q("SELECT substr(g.PostingDate, 1, 7), SUM(g.Credit - g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
               f"WHERE a.AccountType IN ('Revenue', 'Expense') {where} GROUP BY 1 ORDER BY 1")


# --- the chapter note ------------------------------------------------------------------------------------------------

@context("ch15.chapter")
def chapter(d, claim):
    need(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 15, "the chapter has fifteen multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    claim(version() != "", "Tutorial 13.1 names the Power BI Desktop version")
    claim(MODEL.is_dir() and REPORT.is_dir(), "the solution project of Chapter 15 is in outputs/companion/solutions")
    pages = json.loads((REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    claim(pages == PAGES, "the project's pages are the tutorials' nine and three hidden ones, Ledger Detail, Ex 15.2 to Ex 15.6 and Notes")
    tabs = json.loads((MODEL / ".pbi" / "daxQueries.json").read_text(encoding="utf-8"))["tabOrder"]
    claim(tabs == ["Tests", "Ex 15.1", "Checks"], "the project's DAX query tabs are Tests, Ex 15.1 and Checks")
    sections = check_sections()
    mine = sum(v for k, v in sections.items() if k.startswith(("Tutorial 15", "Exercise 15")))
    claim(mine > 0, "the Checks tab holds rows for Tutorial 15.1 to Exercise 15.6")
    budgeted = d.one("SELECT SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID WHERE b.FiscalYear = ? "
                     "AND a.AccountNumber IN ('4010', '4020', '4030', '4040')", d.C)
    billed = d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "JOIN Item i ON i.ItemID = l.ItemID WHERE substr(si.InvoiceDate, 1, 4) = ? AND i.ItemGroup <> 'Services'", str(d.C))
    claim(budgeted / billed >= 3, "the budget's product revenue is at least three times the billed product revenue")
    per_year = d.q("SELECT substr(EffectiveStartDate, 1, 4), COUNT(*) FROM PromotionProgram GROUP BY 1")
    claim(all(n == 3 for _, n in per_year), "the promotions are three a year")
    date_table = _model_text("tables/Date.tmdl")
    claim(f"CALENDAR ( DATE ( {d.F}, 1, 1 ), DATE ( {d.N}, 12, 31 ) )" in date_table, "the Date table runs from the first year to the end of the year after the window")
    # Direct Hours without KEEPFILTERS reads every manufacturing hour (question 12)
    direct = d.one("SELECT SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry WHERE LaborType = ? AND substr(WorkDate, 1, 4) = ?",
                   DIRECT, str(d.C))
    manufacturing = d.one("SELECT SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' "
                          "AND substr(WorkDate, 1, 4) = ?", str(d.C))
    claim(manufacturing > direct, "manufacturing hours include indirect time, so they exceed the direct hours")
    return dict(y=d.C, f=d.F, p=d.P, n=d.N, version=version(), slides=slide_count(), n_exercises=sum(ex.values()),
                per_perspective=ex.get("financial", 0), n_questions=n_q, n_longest=len(longest), longest_correct=and_list(longest),
                steps=step_counts(), n_checks=sum(sections.values()), n_checks_mine=mine, n_pages=len(pages),
                static_ratio=budgeted / billed, direct_hours=direct, manufacturing_hours=manufacturing)


# --- Exercise 15.1 ---------------------------------------------------------------------------------------------------

@context("ch15.g1")
def g1(d, claim):
    need(d, claim, "GLEntry", "Account", "JournalEntry")
    y = d.C
    accounts = d.q("SELECT a.AccountID, a.AccountNumber, a.AccountName FROM Account a WHERE a.AccountSubType = ? "
                   "AND EXISTS (SELECT 1 FROM GLEntry g WHERE g.AccountID = a.AccountID)", SUBTYPE)
    claim(len(accounts) == 1, "one account of the subtype has postings")
    acct = accounts[0]
    rows = d.q("SELECT g.FiscalYear, g.VoucherNumber, g.PostingDate, g.Debit, g.Credit FROM GLEntry g WHERE g.AccountID = ? "
               "ORDER BY g.PostingDate, g.GLEntryID", acct[0])
    closes = set(d.closes)
    kept = [dict(year=fy, number=v, date=dt, pl=cr - db, close=v in closes) for fy, v, dt, db, cr in rows]
    claim(len(kept) == 4 and sum(1 for k in kept if k["close"]) == 2, "the subtype's account has two loss entries and two closes, and no other postings")
    claim(all(abs(sum(k["pl"] for k in kept if k["year"] == yr)) < 0.005 for yr in (d.P, d.C)),
          "in each year the loss entry and the close net to zero, so a table that keeps the closes sums to zero")
    postings = {v: d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber = ?", v) for v in {k["number"] for k in kept if not k["close"]}}
    now = next(k for k in kept if not k["close"] and k["year"] == y)
    before = next(k for k in kept if not k["close"] and k["year"] == d.P)
    claim(postings[now["number"]] == 3 and postings[before["number"]] == 4, "the current year's loss entry has three postings and the prior year's four")
    query = query_tab("Ex 15.1")
    claim(now["number"] in query and "RELATED ( Account[AccountNumber] )" in query, "the Ex 15.1 tab filters the current year's entry and brings the account columns with RELATED")
    return dict(y=y, acct_number=acct[1], acct_name=acct[2], kept=kept, kept_now=[k for k in kept if k["year"] == y], n_postings_now=postings[now["number"]],
                n_postings_before=postings[before["number"]], query=query, m_pl=measure(claim, "P&L Amount"), m_gl=measure(claim, "GL Amount"),
                t_ledger=visual_title(claim, "ledgerDetail", "ledgerTable"),
                dax_now=check_expr(claim, f"{y} entry on the drill-through page"),
                dax_all=check_expr(claim, "entries listed without a year filter (requirement 5)"),
                dax_closes=check_expr(claim, "the closes' credits to the subtype (left out by GL Amount)"),
                closes_credit=sum(k["pl"] for k in kept if k["close"]))


# --- Exercise 15.2 ---------------------------------------------------------------------------------------------------

@context("ch15.g2")
def g2(d, claim):
    need(d, claim, "GLEntry", "Account")
    y = d.C
    rows = net_income_by_month(d, False)
    claim(len(rows) == 12 * len(d.years), "the ledger has net income for every month of the window")
    cum, run = {}, 0.0
    for m, v in rows:
        run += v
        cum[m] = run
    year = [(m, v) for m, v in rows if m.startswith(str(y))]
    running = {}
    r = 0.0
    for m, v in year:
        r += v
        running[m] = r
    names = n15.MONTHS
    table = [dict(name=names[int(m[5:]) - 1], ni=v, ytd=running[m]) for m, v in year]
    # a measure that keeps the closes: December reads the year's net income taken back, and the year ends at zero
    kept = dict(net_income_by_month(d, True))
    dec_kept = kept[f"{y}-12"]
    ytd_kept = sum(v for m, v in kept.items() if m.startswith(str(y)))
    claim(abs(ytd_kept) < 0.005, "with the closes kept the year's net income is zero")
    claim(dec_kept < 0, "with the closes kept December reads negative")
    order = sorted(year, key=lambda mv: mv[1])
    jan_rank = [m for m, _ in order].index(f"{y}-01") + 1
    claim(jan_rank == 3, "January, the other month with three pay dates, is the third lowest month of net income")
    jan = dict(year)[f"{y}-01"]
    cs = calcs(claim, "ex152", "netIncomeByMonth")
    claim(set(cs) == {"YTD", "Change"}, "the Ex 15.2 table holds the two visual calculations YTD and Change")
    return dict(y=y, table=table, cum_jan=cum[f"{y}-01"], cum_dec=cum[f"{y}-12"], dec_kept=dec_kept, jan=jan, jan_rank=jan_rank,
                m_ytd=measure(claim, "Net Income YTD"), c_ytd=cs["YTD"], c_change=cs["Change"],
                t_table=visual_title(claim, "ex152", "netIncomeByMonth"), t_half=visual_title(claim, "ex152", "secondHalf"),
                dax_june=check_expr(claim, "YTD at June"), dax_low=check_expr(claim, "the two months with the lowest net income"),
                dax_half=check_expr(claim, "the running sum of July-December (the visual calculation's December)"))


# --- Exercise 15.3 ---------------------------------------------------------------------------------------------------

@context("ch15.g3")
def g3(d, claim):
    need(d, claim, "LaborTimeEntry", "ProductionCompletion", "ProductionCompletionLine", "Item")
    y = d.C
    p = n15.plant(d)
    last = p["last"]
    wrong = []
    for yr in d.years:
        std = n15.by_year(p, "standard", yr)
        cost = n15.by_year(p, "cost", yr)
        every = d.one("SELECT SUM(ExtendedLaborCost) FROM LaborTimeEntry WHERE substr(WorkDate, 1, 4) = ?", str(yr))
        full = d.one("SELECT SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc "
                     "ON pc.ProductionCompletionID = pcl.ProductionCompletionID JOIN Item i ON i.ItemID = pcl.ItemID "
                     "WHERE substr(pc.CompletionDate, 1, 4) = ?", str(yr))
        wrong.append(dict(year=yr, right=cost / std, every=every / std, uncut=cost / full, same_hours=abs(full - std) < 0.005))
    claim(all(w["same_hours"] for w in wrong[:-1]) and not wrong[-1]["same_hours"],
          "the cut-off removes completions only in the last year, because the time records end before the year does")
    claim(all(w["every"] > w["right"] for w in wrong), "counting non-manufacturing labor cost raises the cost per standard hour in every year")
    claim(wrong[-1]["uncut"] < wrong[-1]["right"], "leaving out the cut-off lowers the last year's cost per standard hour")
    nonman = d.one("SELECT SUM(ExtendedLaborCost) FROM LaborTimeEntry WHERE LaborType = 'NonManufacturing' AND substr(WorkDate, 1, 4) = ?", str(y))
    claim(nonman > 0, "non-manufacturing time carries labor cost in the current year")
    share = n15.by_year(p, "overtime", y) / n15.by_year(p, "hours", y)
    scale = wrong[-1]["right"] / share
    param = source_of(claim, "Plant Measure")
    claim(param.count("NAMEOF") == 3, "the Plant Measure parameter lists three measures")
    indirect_end = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry WHERE LaborType = ? AND substr(WorkDate, 1, 4) = ?",
                         INDIRECT, str(y))
    claim(indirect_end < last, "indirect time ends before the cut-off, so the latest year's measures are provisional")
    return dict(y=y, last=last, indirect_end=indirect_end, wrong=wrong, nonman=nonman, scale=scale, last_share=share, param=param, m_cost=measure(claim, "Labor Cost per Standard Hour"),
                m_hours=measure(claim, "Manufacturing Hours"), t_chart=visual_title(claim, "ex153", "plantMeasureChart"),
                t_slicer=visual_title(claim, "ex153", "plantMeasureSlicer"), t_table=visual_title(claim, "ex153", "plantMeasureTable"),
                dax_cost=check_expr(claim, f"{y} Labor Cost per Standard Hour"),
                dax_fields=check_expr(claim, "the parameter's fields, in order"))


# --- Exercise 15.4 ---------------------------------------------------------------------------------------------------

@context("ch15.g4")
def g4(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "PromotionProgram", "Item")
    y = d.C
    pid = d.one("SELECT PromotionID FROM PromotionProgram WHERE PromotionName = 'Design Trade Customer Promotion'")
    claim(pid is not None, "the Design Trade Customer Promotion exists")
    units, net = d.q("SELECT SUM(l.Quantity), SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                     "WHERE l.PromotionID = ? AND substr(si.InvoiceDate, 1, 4) = ?", pid, str(y))[0]
    before = d.one("SELECT SUM(l.Quantity * l.UnitPrice) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "WHERE l.PromotionID = ? AND substr(si.InvoiceDate, 1, 4) = ?", pid, str(y))
    cost = d.one("SELECT SUM(l.Quantity * i.StandardCost) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                 "JOIN Item i ON i.ItemID = l.ItemID WHERE l.PromotionID = ? AND substr(si.InvoiceDate, 1, 4) = ?", pid, str(y)) / units
    n_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID WHERE l.PromotionID = ? "
                    "AND substr(si.InvoiceDate, 1, 4) = ?", pid, str(y))
    price = before / units
    net_price = net / units
    disc = d.one("SELECT DiscountPct FROM PromotionProgram WHERE PromotionID = ?", pid)
    claim(abs(net_price - price * (1 - disc)) < 0.005, "every line of the promotion carries the promotion's rate, so the net price is the price less the discount")
    wrong_scale = lift(price, cost, 12.0)
    claim(wrong_scale < -1, "a discount of 12 instead of 0.12 turns the denominator negative, so the lift falls below minus 100 percent")
    no_com = {r: lift(price, cost, r, 0.0) for r in (0.05, 0.12)}
    claim(all(no_com[r] < lift(price, cost, r) for r in no_com), "leaving the commission out lowers the lift at both discounts")
    net_lift = lift(net_price, cost, disc)
    claim(net_lift > lift(price, cost, disc), "starting from the net price counts the discount twice and raises the lift")
    # GENERATESERIES ( 0, 0.2, 0.01 ) as repeated addition of the step, which is how a floating-point series accumulates
    values, x = [], 0.0
    while x <= 0.2:
        values.append(x)
        x += 0.01
    claim(len(values) == 20 and round(values[-1], 2) == 0.19, "adding 0.01 twenty times overshoots 0.2, so a decimal series stops at 0.19 (CLAUDE.md records the same in Desktop)")
    default = 12
    claim(abs(disc - default / 100) < 1e-9, "the promotion's rate equals the parameter's default of 12 percent")
    pw = source_of(claim, "Discount")
    claim("GENERATESERIES ( 0, 20, 1 )" in pw, "the Discount table is GENERATESERIES ( 0, 20, 1 )")
    claim("SELECTEDVALUE ( 'Discount'[Discount], 12 )" in measure(claim, "Discount Value"), "Discount Value falls back to the default of 12")
    return dict(y=y, version=version(), name="Design Trade Customer Promotion", n_lines=n_lines, disc=disc, wrong_scale=wrong_scale, no_com_5=no_com[0.05], no_com_12=no_com[0.12], net_price=net_price, net_lift=net_lift,
                n_decimal=len(values), last_decimal=round(values[-1], 2), contrib_without=price * (1 - n15.CASE_RATE) - cost,
                contrib_with=price * (1 - disc) * (1 - n15.CASE_RATE) - cost, series=pw, m_value=measure(claim, "Discount Value"),
                m_units=measure(claim, "Design Trade Units"), m_price=measure(claim, "Design Trade Price per Unit"),
                m_cost=measure(claim, "Design Trade Cost per Unit"), m_lift=measure(claim, "Break-even Lift"),
                t_table=visual_title(claim, "ex154", "liftByDiscount"), t_slider=visual_title(claim, "ex154", "discountSlider"),
                dax_lift=check_expr(claim, "Break-even Lift at 12%"), dax_rows=check_expr(claim, "Discount rows (GENERATESERIES ( 0, 20, 1 ))"))


# --- Exercise 15.5 ---------------------------------------------------------------------------------------------------

@context("ch15.g5")
def g5(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine")
    y, first = d.C, d.F
    revenue = dict(d.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                       "ON si.SalesInvoiceID = l.SalesInvoiceID GROUP BY 1"))
    months = [f"{yr}-{m:02d}" for yr in d.years for m in range(1, 13)]
    ys = [revenue[m] for m in months]
    actual = sum(ys[-3:])

    def trend(fitted, start):
        xs = list(range(start, start + len(fitted)))
        mx, my = sum(xs) / len(xs), sum(fitted) / len(fitted)
        b = sum((x - mx) * (v - my) for x, v in zip(xs, fitted)) / sum((x - mx) ** 2 for x in xs)
        a = my - b * mx
        return sum(a + b * x for x in range(xs[-1] + 1, xs[-1] + 4)) / actual - 1

    with_start = dict(mean=3 * (sum(ys[:-3]) / len(ys[:-3])) / actual - 1, trend=trend(ys[:-3], 1))
    claim(with_start["mean"] < 0 and with_start["trend"] > 0.06, "fitting the benchmarks on January of the first year pulls the mean below the actual quarter and pushes the trend further above it")
    note = n15.ex5(d, lambda c, t: None)
    claim(abs(with_start["mean"]) > abs(note["errors"]["mean"]["quarter"]), "the mean benchmark is worse when the start-up month is left in")
    q4 = [dict(month=m, revenue=revenue[m]) for m in months[-3:]]
    claim(abs(sum(x["revenue"] for x in q4) - note["actual"]) < 0.005, "the last three months of the window are the fourth quarter the note forecasts")
    cols = _visual("ex155", "forecastFromJanuary")["visual"]["objects"]["forecast"][0]["properties"]["transform"]["parameters"]
    prm = {c["Name"]: c["Literal"]["Value"] for c in cols}
    claim(prm["ForecastLength"] == "3L" and prm["ConfidenceLevel"] == "0.95D", "the Ex 15.5 charts forecast three points at a 95 percent confidence level")
    answer = json.dumps(_visual("ex155", "ex155Answer"))
    recorded = [(float(q), float(m)) for q, m in re.findall(r"quarter [\d,.]+, error (-?[\d.]+)% \(monthly ([\d.]+)%\)", answer)]
    claim(len(recorded) == 2, "the model answer records the quarter and monthly error of both forecasts")
    claim(all(abs(q) > 100 * abs(note["errors"]["mean"]["quarter"]) for q, _ in recorded),
          "the mean benchmark has a smaller quarter error than both recorded forecasts")
    claim(all(m < 100 * note["errors"]["mean"]["monthly"] for _, m in recorded),
          "both recorded forecasts have a smaller average monthly error than the mean benchmark")
    return dict(y=y, first=first, q4=q4, with_start=with_start, n_all=len(months), n_date=12 * (d.N - d.F + 1),
                col=column_line(claim, "Date", "MonthStart"),
                t_jan=visual_title(claim, "ex155", "forecastFromJanuary"), t_feb=visual_title(claim, "ex155", "forecastFromFebruary"),
                t_actual=visual_title(claim, "ex155", "actualQ4"),
                dax_actual=check_expr(claim, f"actual revenue {y}-Q4"),
                dax_mean=check_expr(claim, "the mean benchmark's quarter error (mean month February to September x 3)"),
                dax_start=check_expr(claim, f"January {first} against the year's other months"))


# --- Exercise 15.6 ---------------------------------------------------------------------------------------------------

@context("ch15.g6")
def g6(d, claim):
    need(d, claim, "LaborTimeEntry", "WorkOrderOperation", "TimeClockEntry", "WorkCenter")
    y = d.C
    rows = d.q("SELECT substr(l.WorkDate, 1, 4), l.LaborType, l.RegularHours + l.OvertimeHours, ow.WorkCenterName, cw.WorkCenterName, "
               "o.ActualEndDate, l.WorkDate, o.WorkOrderOperationID IS NOT NULL FROM LaborTimeEntry l "
               "LEFT JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID "
               "LEFT JOIN WorkCenter ow ON ow.WorkCenterID = o.WorkCenterID "
               "LEFT JOIN TimeClockEntry t ON t.TimeClockEntryID = l.TimeClockEntryID LEFT JOIN WorkCenter cw ON cw.WorkCenterID = t.WorkCenterID")
    claim(d.one("SELECT COUNT(DISTINCT WorkCenterName) = COUNT(*) FROM WorkCenter") == 1,
          "each work center has its own name, so comparing the names gives the same answer as comparing the keys")
    claim(d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE TimeClockEntryID IS NULL") == 0, "every labor line has a clock entry key")
    direct = [r for r in rows if r[1] == DIRECT]
    no_op = [r for r in direct if not r[7]]
    claim(all(r[4] is not None for r in no_op), "every direct line without an operation has a clock work center, so a blank operation would read as a disagreement")
    by_year = []
    for yr in d.years:
        lines = [r for r in direct if r[0] == str(yr) and r[7]]
        differ = [r for r in lines if r[3] != r[4]]
        late = [r for r in lines if r[5] and r[6] > r[5]]
        late_differ = [r for r in differ if r[5] and r[6] > r[5]]
        by_year.append(dict(year=yr, lines=len(lines), differ=len(differ), late=len(late), late_differ=len(late_differ),
                            blank=len([r for r in no_op if r[0] == str(yr)]),
                            share_differ=len(differ) / len(lines), share_late=len(late) / len(lines),
                            share_late_differ=len(late_differ) / len(differ)))
    now = by_year[-1]
    claim(by_year[0]["share_differ"] > now["share_differ"], "the paths disagree on a larger share of lines in the first year than in the last")
    claim(by_year[0]["share_late"] < now["share_late"], "lines recorded after their operation ended are a growing share")
    claim(now["share_late_differ"] > now["share_late"], "late lines are a larger share of the disagreeing lines than of all direct lines in the last year")
    n_all = d.one("SELECT COUNT(*) FROM LaborTimeEntry")
    n_inner = d.one("SELECT COUNT(*) FROM LaborTimeEntry l JOIN WorkOrderOperation o ON o.WorkOrderOperationID = l.WorkOrderOperationID")
    claim(n_inner < n_all, "an inner join to the operations drops the lines that have none")
    packing = next((n for (n,) in d.q("SELECT WorkCenterName FROM WorkCenter") if n.startswith("Packing")), "")
    assembly = next((n for (n,) in d.q("SELECT WorkCenterName FROM WorkCenter") if n.startswith("Assembly")), "")
    claim(bool(packing and assembly), "the plant has a Packing and an Assembly work center")
    cell = lambda op, clk: sum(r[2] for r in direct if r[0] == str(y) and r[7] and r[3] == op and r[4] == clk)   # noqa: E731
    main, swap = cell(packing, assembly), cell(assembly, packing)
    claim(main > swap, "Packing operations clocked at Assembly outweigh Assembly operations clocked at Packing")
    non_direct = sum(r[2] for r in rows if r[0] == str(y) and r[1] != DIRECT)
    pack_hours = sum(r[2] for r in direct if r[0] == str(y) and r[7] and r[3] == packing)
    pack_off = sum(r[2] for r in direct if r[0] == str(y) and r[7] and r[3] == packing and r[4] != packing)
    lp = table_m("LaborPaths")
    return dict(y=y, by_year=by_year, n_all=n_all, n_inner=n_inner, n_blank=sum(x["blank"] for x in by_year), blank_now=now["blank"],
                packing=packing, assembly=assembly, main=main, swap=swap, pack_off_share=pack_off / pack_hours, non_direct=non_direct,
                m_op=steps(claim, expression_m("OperationPaths"), "Removed Other Columns", "Changed Type1"),
                m_clock=steps(claim, expression_m("ClockPaths"), "Removed Other Columns"),
                m_merges=steps(claim, lp, "Merged Queries", "Expanded OperationPaths", "Merged Queries2", "Expanded ClockPaths"),
                m_tests=steps(claim, lp, "Added Custom", "Added Custom1"),
                m_lines=measure(claim, "Path Lines"), m_hours=measure(claim, "Path Hours"), m_differ=measure(claim, "Disagreeing Lines"),
                m_share=measure(claim, "Share After Operation End"),
                t_year=visual_title(claim, "ex156", "disagreeByYear"), t_matrix=visual_title(claim, "ex156", "pathMatrix"),
                t_share=visual_title(claim, "ex156", "lateShare"), t_indirect=visual_title(claim, "ex156", "indirectByClock"),
                dax_differ=check_expr(claim, f"{y} disagreeing lines"),
                dax_share=check_expr(claim, f"{y} share after the operation's end, all direct lines (requirement 5)"),
                dax_untested=check_expr(claim, f"{y} direct lines that cannot be tested (no operation, so no end date)"))
