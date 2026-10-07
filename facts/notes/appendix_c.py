"""The instructor notes of the appendix on Power BI in the browser: the values each note states, and the claims its
wording makes.

The browser rebuilds Tutorial 13.1's model, so the values are Chapter 13's, computed with the same twin (ch13.lines:
the four Tables, FiscalYear = the year of InvoiceDate, and the unrounded ListAmount and DiscountAmount). What the
browser itself does (InvoiceDate read as an Excel date number, the key columns set not to summarize, the card hidden
until the default visuals are restored) was observed in the Power BI service while the appendix was written; the
notes state it, and the data claims below are the ones the tutorials and exercises depend on.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from notes import note
from notes import ch13 as c13

APPENDIX = "appendices/c-power-bi-browser"
T1 = f"{APPENDIX}/_tutorial-01.qmd"
T2 = f"{APPENDIX}/_tutorial-02.qmd"
T3 = f"{APPENDIX}/_tutorial-03.qmd"
EXERCISES = f"{APPENDIX}/_exercises.qmd"
MCQ = f"{APPENDIX}/_multiple-choice.qmd"
TOP_ROWS = 1000          # Power Query profiles the top 1,000 rows by default (a software constant)


def serial(date: str) -> int:
    """The Excel date number of a date: what Power Query Online shows for a workbook date."""
    return (dt.date.fromisoformat(date[:10]) - dt.date(1899, 12, 30)).days


def year_rows(d, rows) -> list[dict]:
    out = []
    for y in d.years:
        sub = [r for r in rows if r["year"] == y]
        out.append(dict(year=y, n=len(sub), rev=c13.total(sub, "rev"), list=c13.total(sub, "list"),
                        disc=c13.total(sub, "disc")))
    return out


# --- Guided Tutorial C.1 -------------------------------------------------------------------------

@note("appendix_c.t1", T1)
def t1(d, claim):
    rows = c13.lines(d)
    n = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    claim(len(rows) == n, "every invoice line finds its invoice, item, and customer")
    first_invoice = d.q("SELECT InvoiceNumber, InvoiceDate FROM SalesInvoice ORDER BY SalesInvoiceID LIMIT 1")[0]
    first = rows[:TOP_ROWS]
    claim(len({r["rate"] for r in first}) == 1, "the first 1,000 lines have a single Discount value")
    claim(all(r["promo"] is None for r in first), "PromotionID is empty on every one of the first 1,000 lines")
    years = year_rows(d, rows)
    claim(sum(y["n"] for y in years) == n, "every invoice line falls in a fiscal year of the window")
    return dict(n=n, items=d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL"),
                first_number=first_invoice[0], first_date=first_invoice[1], first_serial=serial(first_invoice[1]),
                years=years, empty=sum(r["promo"] is None for r in rows),
                discounts=[c13.rate(x) for x in sorted({r["rate"] for r in rows})],
                groups=len({r["group"] for r in rows}))


# --- Guided Tutorial C.2 -------------------------------------------------------------------------

@note("appendix_c.t2", T2)
def t2(d, claim):
    rows = [r for r in c13.lines(d) if r["year"] == d.C]
    autumn = c13.autumn_promotion(d)
    by_month = defaultdict(float)
    for r in rows:
        by_month[r["m"]] += r["disc"]
    start, end = int(autumn["start"][5:7]), int(autumn["end"][5:7])
    before = max(by_month[m] for m in range(1, start))
    claim(min(by_month[start], by_month[end]) > 5 * before,
          "the discount line stays near zero until the autumn promotion's months, then rises sharply")
    ranked = sorted(range(1, 13), key=lambda m: -by_month[m])
    claim(ranked[:2] == [end, start], "sorted by value, the two promotion months come first, the later one ahead")
    groups = defaultdict(float)
    for r in rows:
        groups[r["group"]] += r["disc"]
    order = sorted(groups.items(), key=lambda kv: -kv[1])
    claim(order[0][0] == "Furniture", "Furniture leads the bar chart of discounts")
    invoices = len({r["inv"] for r in rows})
    claim(invoices < len(rows), "counting SalesInvoiceID on the lines without Distinct would overcount the invoices")
    return dict(C=d.C, rev=c13.total(rows, "rev"), list=c13.total(rows, "list"), disc=c13.total(rows, "disc"),
                invoices=invoices, lines=len(rows), months=[(c13.MONTHS[m - 1][:3], by_month[m]) for m in range(1, 13)],
                ranked=[c13.MONTHS[m - 1][:3] for m in ranked[:4]], furniture=order[0][1] / c13.total(rows, "disc"),
                autumn=autumn["name"])


# --- Guided Tutorial C.3 -------------------------------------------------------------------------

@note("appendix_c.t3", T3)
def t3(d, claim):
    years = year_rows(d, c13.lines(d))
    return dict(years=years)


# --- Exercises -----------------------------------------------------------------------------------

@note("appendix_c.ex1", EXERCISES)
def ex1(d, claim):
    rows = [r for r in c13.lines(d) if r["year"] == d.C]
    promos = c13.promotions(d)
    quarters = []
    for q in range(1, 5):
        sub = [r for r in rows if r["quarter"] == q]
        by_promo = defaultdict(float)
        for r in sub:
            if r["promo"] is not None:
                by_promo[r["promo"]] += r["disc"]
        quarters.append(dict(q=q, n=len(sub), rev=c13.total(sub, "rev"), list=c13.total(sub, "list"),
                             disc=c13.total(sub, "disc"),
                             promos=[(promos[p]["name"], v) for p, v in sorted(by_promo.items(), key=lambda kv: -kv[1])
                                     if v >= 0.005]))
    year = dict(n=len(rows), rev=c13.total(rows, "rev"), list=c13.total(rows, "list"), disc=c13.total(rows, "disc"))
    claim(sum(q["n"] for q in quarters) == year["n"] and abs(sum(q["rev"] for q in quarters) - year["rev"]) < 0.005,
          "the four quarters add up to the year's Validation row")
    top = max(quarters, key=lambda q: q["disc"])
    claim(top["q"] == 4, "the fourth quarter carries the largest share of the year's discounts")
    claim(top["disc"] / year["disc"] > 0.5, "the fourth quarter holds more than half of the year's discounts")
    autumn, trade = c13.autumn_promotion(d), c13.segment_promotion(d, "Design Trade")
    names = [name for name, _ in top["promos"][:2]]
    claim(names == [autumn["name"], trade["name"]],
          "the autumn Furniture promotion and the Design Trade promotion are the two largest in the fourth quarter")
    return dict(C=d.C, quarters=quarters, year=year, top=top, share=top["disc"] / year["disc"])


@note("appendix_c.ex2", EXERCISES)
def ex2(d, claim):
    rows = [r for r in c13.lines(d) if r["year"] == d.C]
    trade = c13.segment_promotion(d, "Design Trade")
    autumn = c13.autumn_promotion(d)
    segs = sorted({r["segment"] for r in rows})
    by = {s: defaultdict(float) for s in segs}
    for r in rows:
        by[r["segment"]][r["m"]] += r["disc"]
    totals = {s: sum(by[s].values()) for s in segs}
    none = [s for s in segs if totals[s] < 0.005]
    claim(none == ["Design Services"], "only the Design Services segment received no discounts")
    peaks = {s: max(range(1, 13), key=lambda m: by[s][m]) for s in segs if s not in none}
    trade_month = int(trade["start"][5:7])
    november = [s for s, m in peaks.items() if m == trade_month]
    claim(november == ["Design Trade"], "Design Trade is the one segment whose discounts peak in its promotion's month")
    others = {s: m for s, m in peaks.items() if s != "Design Trade"}
    start, end = int(autumn["start"][5:7]), int(autumn["end"][5:7])
    claim(all(start <= m <= end for m in others.values()), "the other segments peak within the autumn promotion's months")
    return dict(C=d.C, trade=trade["name"], trade_month=c13.MONTHS[trade_month - 1], autumn=autumn["name"],
                autumn_months=f"{c13.MONTHS[start - 1]} and {c13.MONTHS[end - 1]}",
                peaks=[(s, c13.MONTHS[peaks[s] - 1], by[s][peaks[s]], totals[s]) for s in segs if s not in none],
                others=[(s, c13.MONTHS[m - 1]) for s, m in sorted(others.items())], no_discount=none)


@note("appendix_c.ex3", EXERCISES)
def ex3(d, claim):
    rows = [r for r in c13.lines(d) if r["year"] == d.C]
    rev, lst = c13.total(rows, "rev"), c13.total(rows, "list")
    claim(lst > rev, "summing ListAmount instead of LineTotal raises the test's revenue")
    return dict(C=d.C, rev=rev, list=lst, diff=lst - rev)


@note("appendix_c.mcq", MCQ)
def mcq(d, claim):
    first_invoice = d.q("SELECT InvoiceDate FROM SalesInvoice ORDER BY SalesInvoiceID LIMIT 1")[0][0]
    first = c13.lines(d)[:200]
    claim(len({r["rate"] for r in first}) == 1 and first[0]["rate"] == 0, "Discount is zero in the first 200 rows")
    return dict(serial=serial(first_invoice), date=first_invoice)
