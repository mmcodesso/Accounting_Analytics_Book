"""Appendix C's instructor guides: the values the guides state, and the claims their wording makes.

The appendix on Power BI in the browser has three guided tutorials (C.1 builds Chapter 13's model in the Power BI service, C.2
builds the Sales and Discounts page in the report editor, C.3 adds a Key Measures table and a first measure) and three exercises
that extend the model of Tutorial C.1: control totals by quarter (C.1), discounts by segment and month (C.2), and a measure
changed and restored through version history (C.3).

There is NO companion file and NO solution project: the projects open only in Desktop, and the browser steps were read in the
author's own service account (the sanitized record facts/instructor/observations/appendix-c-service-observations-2026-10-06.md, dated
author-session evidence that the public numerical checks below do not establish). The model answers therefore come from three places, and the
guides say which:

- the book's tutorials and exercises (the labels and the steps),
- the registered notes appendix_c.t1 to appendix_c.ex3, which compute every value from the dataset (the browser rebuilds Tutorial
  13.1's model, so they use Chapter 13's twin of it),
- the measures and the Checks-tab expressions of the Desktop solution projects that hold the same model (Appendix B's project for
  the measures of Key Measures, Chapter 13's project for the 2026 control totals), which were run against Desktop's engine.

The contexts do the usual four jobs:

- they check, with claim(), every table and column the guides name and every statement about the data that another dataset could
  falsify (the cent that the four quarters' discounts differ from the year by, the segment that has no discounts and why, the
  promotions that reach one segment and the ones that reach four), so a roll flags the wording instead of leaving it stale,
- they supply what each exercise's steps need beyond its registered note, above all the symptom of each wrong version a guide
  names (a date left as the number the service reads, Discount left as a whole number, a key dragged into Categories, a chart
  sorted by its values, a matrix with no year selected), computed read-only the way the service would show it,
- they quote the DAX of the Desktop projects that the browser's measures and tests repeat,
- they supply the chapter note's counts (exercises, questions, tutorial steps, items of Choose data) from the appendix's files.

Keys: appC.chapter (the chapter note), appC.g1 to appC.g3 (the exercises; each is used next to the registered note
appendix_c.ex1 to appendix_c.ex3 that supplies the exercise's instructor-note values).

What nothing here proves: no browser or tenant was run. The DAX of Exercise C.1's query and of the checks is built from the
book's Tutorial C.3 query and from Desktop-verified expressions; the labels are the ones the book and the author's log give.
"""

from __future__ import annotations

import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from guide_contexts import context
from guide_contexts.appb import measure
from guide_contexts.ch09 import and_list
from guide_contexts.ch13 import DETECT_ROWS, check_expr, need
from notes import ch13 as c13
from notes import appendix_c as nc

REPO = Path(__file__).resolve().parents[3]
APPENDIX = REPO / "appendices" / "c-power-bi-browser"
# The dated observation record of the author's service test. The sanitized, versioned copy in the repository is the one the
# checks read; the author's own log (drafts/ is gitignored, and it moved to drafts/old/ on 2026-10-14) is the fallback. The record
# is evidence from one account on one day: a check that finds the phrases in it shows the guides quote it, not that the
# interface still behaves so (the chapter note says so, and asks for a repeat run with a student account).
OBSERVATIONS = REPO / "facts" / "instructor" / "observations" / "appendix-c-service-observations-2026-10-06.md"
LOG = next((path for path in (OBSERVATIONS,
                              REPO / "drafts" / "appendix-c-service-results.md",
                              REPO / "drafts" / "old" / "appendix-c-service-results.md") if path.exists()),
           OBSERVATIONS)
READ_ON = "October 6, 2026"          # the day the author's service account was read (CLAUDE.md, the author's log)
CHOOSE_DATA_ITEMS = 164             # the items Choose data listed in the author's test: each Table and its worksheet
UPLOAD_MB = 123                     # what the service reported for the workbook ("Upload successful (123 MB)")
SMALL_SEGMENT = "Design Services"   # the segment that buys only Services


# --- helpers ---------------------------------------------------------------------------------------------------------

def tutorial_text(n: int) -> str:
    return (APPENDIX / f"_tutorial-0{n}.qmd").read_text(encoding="utf-8")


def step_count(n: int) -> int:
    return len(re.findall(r"^\*\*Step \d+\.", tutorial_text(n), re.M))


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (APPENDIX / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise [A-Z]\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import package
    import source
    text = (APPENDIX / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("appendices/c-power-bi-browser/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) C\b")
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


def book_query() -> str:
    """The test of Guided Tutorial C.3, as the book prints it (the first fenced block that holds EVALUATE)."""
    for block in re.findall(r"```\n(.*?)```", tutorial_text(3), re.S):
        if "EVALUATE" in block:
            return block.strip()
    return ""


def year_lines(d, year: int | None = None) -> list[dict]:
    rows = c13.lines(d)
    return rows if year is None else [r for r in rows if r["year"] == year]


def c1_query() -> str:
    """The query of Exercise C.1, requirement (2): one row for each fiscal quarter (Exercise C.3 claims it reads [Revenue])."""
    return "\n".join([
        "// Exercise C.1, requirement (2): the control totals of each quarter",
        "EVALUATE",
        "SUMMARIZECOLUMNS (",
        "    SalesInvoice[FiscalYear],",
        "    SalesInvoice[Period],",
        '    "Invoice lines", [Invoice Lines],',
        '    "Revenue", ROUND ( [Revenue], 2 ),',
        '    "List amount", ROUND ( [List Amount], 2 ),',
        '    "Discounts", ROUND ( [Discounts], 2 )',
        ")",
        "ORDER BY SalesInvoice[FiscalYear], SalesInvoice[Period]"])


def day_label(date: str) -> str:
    """An ISO date as prose writes it, month first without the year ('March 6')."""
    return f"{c13.MONTHS[int(date[5:7]) - 1]} {int(date[8:10])}"


def log_has(*phrases: str) -> bool:
    text = LOG.read_text(encoding="utf-8") if LOG.is_file() else ""
    return all(p in text for p in phrases)


# --- the chapter note ------------------------------------------------------------------------------------------------

@context("appC.chapter")
def chapter(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item", "Customer", "PromotionProgram")
    ex = exercise_counts()
    claim(ex == {"financial": 1, "managerial": 1, "auditing": 1}, "the appendix has one exercise for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 8, "the appendix has eight multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    claim((step_count(1), step_count(2), step_count(3)) == (11, 9, 5), "Tutorials C.1, C.2 and C.3 have eleven, nine and five steps")
    claim(LOG.is_file(), "the dated observation record of the author's service test is in the repository (the guides cite what it read)")
    n_tables = d.one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
    claim(2 * n_tables == CHOOSE_DATA_ITEMS,
          "twice the tables of the database is the number of items the author's test read in Choose data (each Table and its worksheet)")
    first, last = d.q("SELECT MIN(InvoiceDate), MAX(InvoiceDate) FROM SalesInvoice")[0]
    claim(nc.serial(first) >= 10000 and nc.serial(last) >= 10000,
          "every invoice date is a five-digit Excel date number, as Power Query Online reads it")
    rows = c13.lines(d)
    claim(all(r["rate"] == 0 for r in rows[:c13.TOP_ROWS]) and len({r["rate"] for r in rows}) > 1,
          "Discount is zero in the first rows the profile reads and takes several values over the entire data set")
    claim(len({r["promo"] for r in rows[:c13.TOP_ROWS]}) == 1, "PromotionID is empty on every one of the first 1,000 lines")
    claim(log_has("Upload successful (123 MB)", "CharlesRiver 1.xlsx"),
          "the observation record has the upload size and the renamed copy that the note quotes (one account, one day: not a check of today's interface)")
    promo_text = tutorial_text(2)
    claim("select LineTotal, ListAmount, and DiscountAmount" in promo_text,
          "Tutorial C.2 builds its cards from the columns LineTotal, ListAmount and DiscountAmount, not from a measure")
    return dict(n_exercises=sum(ex.values()), w_exercises=c13.word(sum(ex.values())), n_questions=n_q,
                w_questions=c13.word(n_q), n_longest=len(longest), longest_correct=and_list(longest),
                steps1=step_count(1), steps2=step_count(2), steps3=step_count(3), n_tables=n_tables,
                n_items=CHOOSE_DATA_ITEMS, upload_mb=UPLOAD_MB, first_date=first, last_date=last,
                serial_first=nc.serial(first), serial_last=nc.serial(last), read_on=READ_ON,
                top_rows=c13.TOP_ROWS, detect_rows=DETECT_ROWS)


# --- Exercise C.1 ----------------------------------------------------------------------------------------------------

@context("appC.g1")
def g1(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "PromotionProgram")
    y = d.C
    all_rows = year_lines(d)
    rows = [r for r in all_rows if r["year"] == y]
    m_list, m_disc = measure(claim, "List Amount"), measure(claim, "Discounts")
    m_lines, m_rev = measure(claim, "Invoice Lines"), measure(claim, "Revenue")
    claim(m_list.endswith("SUM ( SalesInvoiceLine[ListAmount] )") and m_disc.endswith("SUM ( SalesInvoiceLine[DiscountAmount] )")
          and m_lines.endswith("COUNTROWS ( SalesInvoiceLine )"),
          "the Desktop project's measures sum ListAmount and DiscountAmount and count the rows of SalesInvoiceLine, as requirement (1) says")
    periods = sorted({(r["year"], r["quarter"]) for r in all_rows})
    claim(len(periods) == 3 * 4, "the model has twelve fiscal quarters, so the query returns twelve rows")
    quarters = []
    for q in range(1, 5):
        sub = [r for r in rows if r["quarter"] == q]
        quarters.append(dict(q=q, label=f"{y}-Q{q}", n=len(sub), invoices=len({r["inv"] for r in sub}),
                             disc_cents=c13.total(sub, "disc")))
    year_disc = c13.total(rows, "disc")
    rounded_sum = round(sum(round(q["disc_cents"], 2) for q in quarters), 2)
    cent = round(round(year_disc, 2) - rounded_sum, 2)
    claim(abs(cent) == 0.01, "the four quarters' discounts, each rounded to the cent, differ from the year's rounded discounts by one cent")
    line_rounded = float(sum(Decimal(repr(r["disc"])).quantize(Decimal("0.01"), ROUND_HALF_UP) for r in rows))
    claim(abs(line_rounded - round(year_disc, 2)) >= 0.005 and abs(line_rounded - rounded_sum) >= 0.005,
          "rounding every line's discount to the cent first gives a total that matches neither the year nor the rounded quarters")
    claim(abs(sum(q["disc_cents"] for q in quarters) - year_disc) < 1e-6, "unrounded, the four quarters' discounts add up to the year's")
    for field in ("rev", "list"):
        claim(abs(round(sum(round(c13.total([r for r in rows if r["quarter"] == q], field), 2) for q in range(1, 5)), 2)
                  - round(c13.total(rows, field), 2)) < 0.005,
              f"the four quarters' {field} amounts add up to the year's without a difference")
    claim(all(q["invoices"] < q["n"] for q in quarters), "every quarter has fewer invoices than invoice lines, so DISTINCTCOUNT and COUNTROWS differ")
    # a student who groups by FiscalQuarter alone: four rows that add the three years
    by_q = []
    for q in range(1, 5):
        sub = [r for r in all_rows if r["quarter"] == q]
        by_q.append(dict(q=q, n=len(sub), rev=c13.total(sub, "rev")))
    # the earlier-year promotions that bill in the first quarter, and the Harbor promotion's dates
    promos = c13.promotions(d)
    q1_ids = sorted({r["promo"] for r in rows if r["quarter"] == 1 and r["promo"] is not None})
    q1_old = [promos[p]["name"] for p in q1_ids if int(promos[p]["start"][:4]) < y]
    claim(len(q1_old) >= 1, "the first quarter bills discounts of a promotion that started in the prior year")
    harbor = promos[7]
    claim(harbor["end"] < harbor["start"] and harbor["start"][:4] == str(y),
          "the Harbor Collection Promotion's end date is before its start date (Exercise 13.3's master-data error)")
    q2_ids = sorted({r["promo"] for r in rows if r["quarter"] == 2 and r["promo"] is not None})
    claim(q2_ids == [7], "the second quarter's discounts all come from the Harbor Collection Promotion")
    # the first quarter by promotion: the prior year's promotions are not all confined to January
    q1_detail = []
    for pid in q1_ids:
        sub = [r for r in rows if r["quarter"] == 1 and r["promo"] == pid]
        q1_detail.append(dict(name=promos[pid]["name"], prior=int(promos[pid]["start"][:4]) < y,
                              last=max(r["date"] for r in sub), disc=c13.total(sub, "disc")))
    prior_q1 = [p for p in q1_detail if p["prior"]]
    claim([p["name"] for p in q1_detail if not p["prior"]] == [harbor["name"]],
          "the first quarter's discounts come from promotions of the prior year and from the Harbor Collection Promotion")
    latest_prior = max(prior_q1, key=lambda p: p["last"])
    claim(latest_prior["last"][5:7] >= "03",
          "one prior-year promotion is still invoiced in March, so the prior-year promotions' invoices are not confined to January")
    harbor_q1 = next(p for p in q1_detail if not p["prior"])
    claim(abs(harbor_q1["disc"] - c13.total([r for r in rows if r["promo"] == 7 and r["quarter"] == 1], "disc")) < 1e-6,
          "the Harbor Collection Promotion contributes to the first quarter and, alone, to the second")
    year_total = c13.total(rows, "disc")
    q3_share, q4_share = quarters[2]["disc_cents"] / year_total, quarters[3]["disc_cents"] / year_total
    q12_share = (quarters[0]["disc_cents"] + quarters[1]["disc_cents"]) / year_total
    claim(q4_share > q3_share > q12_share and abs(q3_share + q4_share + q12_share - 1) < 1e-9,
          "the fourth quarter holds most of the year's discounts, the third the next most, and the first two together the least")
    claim(all(p["scope"] == "ItemGroup" for p in (c13.autumn_promotion(d),))
          and c13.autumn_promotion(d)["start"][5:7] == "09", "the Furniture promotion starts in September")
    dax_disc = check_expr(claim, "2026 discounts")
    dax_lines = check_expr(claim, "2026 invoice lines")
    query = c1_query()
    return dict(y=y, m_list=m_list, m_disc=m_disc, m_lines=m_lines, m_rev=m_rev, query=query, n_rows=len(periods), n_cols=6,
                quarters=quarters, q1=quarters[0], q4=quarters[3], rounded_sum=rounded_sum, cent=abs(cent), by_q=by_q,
                line_rounded=line_rounded,
                q1_old=and_list(q1_old), n_q1_old=len(q1_old), dax_disc=dax_disc, dax_lines=dax_lines,
                q1_prior_last=latest_prior["name"], q1_prior_last_day=day_label(latest_prior["last"]),
                harbor_q1=harbor_q1["disc"], q3_share=q3_share, q4_share=q4_share, q12_share=q12_share,
                autumn_start=c13.MONTHS[int(c13.autumn_promotion(d)["start"][5:7]) - 1],
                autumn_end=c13.MONTHS[int(c13.autumn_promotion(d)["end"][5:7]) - 1],
                harbor=harbor["name"])


# --- Exercise C.2 ----------------------------------------------------------------------------------------------------

@context("appC.g2")
def g2(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item", "Customer", "PromotionProgram")
    y = d.C
    all_rows = year_lines(d)
    rows = [r for r in all_rows if r["year"] == y]
    segs = sorted({r["segment"] for r in rows})
    cell, present = defaultdict(float), defaultdict(int)
    for r in rows:
        cell[(r["segment"], r["m"])] += r["disc"]
        present[(r["segment"], r["m"])] += 1
    none = SMALL_SEGMENT
    zero_months = [m for m in range(1, 13) if present[(none, m)] and abs(cell[(none, m)]) < 0.005]
    claim(len(zero_months) == 12, "the segment with no discounts has invoice lines in every month of the year, each with a discount of zero, so its matrix row reads 0.00 and is never blank")
    groups = {r["group"] for r in all_rows if r["segment"] == none}
    claim(groups == {"Services"}, "the Design Services segment buys only Services items")
    claim(all(r["promo"] is None for r in all_rows if r["group"] == "Services"), "no Services line carries a promotion")
    claim(len({r["segment"] for r in all_rows if r["group"] == "Services"}) == 1, "only the Design Services segment buys Services")
    promos = c13.promotions(d)
    reach = {}
    for pid in (c13.autumn_promotion(d)["id"], c13.segment_promotion(d, "Design Trade")["id"]):
        reach[pid] = sorted({r["segment"] for r in rows if r["promo"] == pid and r["disc"] > 0})
    autumn, trade = c13.autumn_promotion(d), c13.segment_promotion(d, "Design Trade")
    claim(len(reach[autumn["id"]]) == 4 and reach[trade["id"]] == ["Design Trade"],
          "the item-group promotion discounts four segments and the segment promotion discounts only its own")
    # the matrix and the chart with no year selected: 36 months
    n_months = len({r["month"] for r in all_rows})
    peak_all = {}
    for s in segs:
        t = defaultdict(float)
        for r in all_rows:
            if r["segment"] == s:
                t[r["month"]] += r["disc"]
        peak_all[s] = max(t.items(), key=lambda kv: kv[1])
    ws = "Wholesale"
    peak26 = max(((m, cell[(ws, m)]) for m in range(1, 13)), key=lambda kv: kv[1])
    claim(peak_all[ws][0][:4] != str(y) and peak_all[ws][1] > peak26[1],
          "with no year selected the Wholesale segment's largest month is in an earlier year, not in the current year")
    trade_peak_all = peak_all["Design Trade"]
    claim(trade_peak_all[0] == f"{y}-11", "Design Trade's largest month stays in November of the current year with no year selected")
    # the line chart sorted by its values
    by_month = defaultdict(float)
    for r in rows:
        by_month[r["m"]] += r["disc"]
    ranked = sorted(range(1, 13), key=lambda m: -by_month[m])
    claim(by_month[ranked[-1]] < 0.005, "the month with the least discount has none, so the value-sorted line ends at zero")
    # revenue instead of discounts
    rev = defaultdict(float)
    for r in rows:
        rev[(r["segment"], r["m"])] += r["rev"]
    promo_months = set(range(int(autumn["start"][5:7]), int(trade["start"][5:7]) + 1))
    rev_peaks = {s: max(range(1, 13), key=lambda m: rev[(s, m)]) for s in segs if s != none}
    claim(all(m not in promo_months for m in rev_peaks.values()),
          "no segment's revenue peaks in the promotion months, so a matrix of LineTotal shows no autumn pattern")
    total = sum(r["disc"] for r in rows)
    shares = {s: sum(cell[(s, m)] for m in range(1, 13)) / total for s in segs}
    # the matrix rounds each cell for display and computes each total from the unrounded amounts
    ws_total = sum(cell[(ws, m)] for m in range(1, 13))
    ws_cells = round(sum(round(cell[(ws, m)], 2) for m in range(1, 13)), 2)
    months_cells = round(sum(round(by_month[m], 2) for m in range(1, 13)), 2)
    claim(0.005 <= abs(round(ws_total, 2) - ws_cells) < 0.05 and 0.005 <= abs(round(total, 2) - months_cells) < 0.05,
          "Wholesale's displayed months and the displayed monthly totals add to a few cents off their unrounded totals")
    dax_trade = check_expr(claim, "2026-11 discounts, Design Trade selected")
    return dict(y=y, m_disc=measure(claim, "Discounts"), w_segs=c13.word(len(segs)),
                w_trade_segs=c13.word(len(reach[trade["id"]])), w_autumn_segs=c13.word(len(reach[autumn["id"]])),
                rev_months=and_list(dict.fromkeys(c13.MONTHS[m - 1] for m in sorted(rev_peaks.values()))), segs=segs, none=none, n_segs=len(segs), n_months=n_months, all_ws=peak_all[ws][0], all_ws_value=peak_all[ws][1],
                ws_peak_month=c13.MONTHS[peak26[0] - 1], ws_peak_value=peak26[1], ranked=[c13.MONTHS[m - 1][:3] for m in ranked],
                last_month=c13.MONTHS[ranked[-1] - 1], rev_peaks=[(s, c13.MONTHS[m - 1]) for s, m in sorted(rev_peaks.items())],
                autumn=autumn["name"], trade=trade["name"], n_autumn_segs=len(reach[autumn["id"]]), n_trade_segs=len(reach[trade["id"]]),
                shares={s: v for s, v in shares.items()}, ws_share=shares[ws], dax_trade=dax_trade,
                services_only=sorted(groups)[0], n_zero_months=len(zero_months), total=total,
                ws_total=ws_total, ws_cells=ws_cells, months_cells=months_cells)


# --- Exercise C.3 ----------------------------------------------------------------------------------------------------

@context("appC.g3")
def g3(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine")
    y = d.C
    all_rows = year_lines(d)
    years = []
    for yr in d.years:
        sub = [r for r in all_rows if r["year"] == yr]
        years.append(dict(year=yr, rev=c13.total(sub, "rev"), list=c13.total(sub, "list"),
                          diff=c13.total(sub, "list") - c13.total(sub, "rev")))
    claim(all(yr["diff"] > 0 for yr in years), "summing ListAmount raises the test's revenue in every fiscal year, not only the current one")
    m_rev = measure(claim, "Revenue")
    changed = m_rev.replace("LineTotal", "ListAmount")
    claim(changed != m_rev and "ListAmount" in changed, "the changed formula of requirement (3) differs from the Revenue measure only in its column")
    claim("select LineTotal, ListAmount, and DiscountAmount" in tutorial_text(2) and "Revenue" in tutorial_text(2),
          "Tutorial C.2's cards read the columns LineTotal and ListAmount (renamed Revenue and At list price), not the Revenue measure, so no page changes when the measure does")
    claim("Tests.dax" in tutorial_text(3), "Tutorial C.3 keeps its test in Tests.dax")
    claim("[Revenue]" in c1_query(), "Exercise C.1's query reads the Revenue measure, so a changed measure changes its Revenue column")
    claim(log_has("Save to version history", "Version history"),
          "the observation record read the two version history commands on the model editor's File menu (not their windows)")
    dax_rev = check_expr(claim, "2026 line total")
    dax_list = check_expr(claim, "2026 list amount")
    return dict(y=y, years=years, m_rev=m_rev, changed=changed, dax_rev=dax_rev, dax_list=dax_list, book_query=book_query())
