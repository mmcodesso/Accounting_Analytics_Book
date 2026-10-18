"""Chapter 14's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 14 builds the star model, the Date table, the measures and the ledger star, so the guides do four jobs, as
Chapter 13's did:

- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll flags the wording instead of leaving it stale,
- they supply what each exercise's steps need beyond its registered note (ch14.ex1 to ch14.ex6): above all the symptom
  of each wrong version a guide names (a balance that does not accumulate, signs taken from NormalBalance, an inner
  join that drops the Services lines, a CrossesYear column with no null guard, a price-list effect that keeps the
  discounts, a debit total built on GL Amount, a revenue test over every revenue account), computed read-only on the
  dataset the way the model would show it,
- they quote the DAX and the Power Query M of the model answer from the solution project itself
  (outputs/companion/solutions/Chapter14-exercises-pbi), so a quoted measure cannot drift from the file the instructor
  opens: a quote that is not found in the project is a failed claim,
- they supply the chapter note's counts (exercises, questions, slides, tutorial steps, checks) from the chapter's files.

Keys: ch14.chapter (the chapter note) and ch14.g1 to ch14.g6 (the exercises; each is used next to the registered note
ch14.ex1 to ch14.ex6 that supplies the values of the exercise's instructor note). The tutorials' values come from the
registered notes ch14.t1 to ch14.t3.

What the project proves and what only Desktop shows: the project encodes the model and the visual structure, and its
Checks tab (DAX query view) recomputes every value of the tutorials and exercises, so a result is "proved" when a
Checks row names it; how a visual renders (labels, colors, the slicer's look) is visible only in Desktop.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list
from guide_contexts.ch13 import _block, steps, version
from notes import ch14 as n14

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "14-data-models-and-dax"
DECK = REPO / "slides" / "chapter-14" / "index.qmd"
PROJECT = REPO / "outputs" / "companion" / "solutions" / "Chapter14-exercises-pbi" / "Chapter 14 Exercises - Solutions"
MODEL = PROJECT / "Chapter 14 Exercises - Solutions.SemanticModel"
REPORT = PROJECT / "Chapter 14 Exercises - Solutions.Report"

SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID", "SubTotal"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "ShipmentLineID", "Quantity", "BaseListPrice",
                         "UnitPrice", "Discount", "LineTotal"],
    "Item": ["ItemID", "ItemCode", "ItemGroup", "StandardCost", "ListPrice"],
    "Customer": ["CustomerID", "CustomerName"],
    "Shipment": ["ShipmentID", "ShipmentDate", "DeliveryDate"],
    "ShipmentLine": ["ShipmentLineID", "ShipmentID"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "CostCenterID"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType", "NormalBalance"],
    "JournalEntry": ["EntryNumber", "EntryType", "PostingDate"],
}
TYPES = n14.TYPES


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
    """Every measure of the Key Measures table as the formula bar reads it: `Name = expression`, the body dedented."""
    lines = _model_text("tables/Key Measures.tmdl").split("\n")
    out: dict[str, str] = {}
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
    claim(found is not None, f"the solution project's Key Measures table has the measure {name}")
    return found or ""


def check_expr(claim, label: str, prefix: bool = False) -> str:
    """The DAX expression of one row of the project's Checks tab (DAX query view), found by its label."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    tail = r'[^"]*' if prefix else ""
    m = re.search(r'"Check", "' + re.escape(label) + tail + r'", "Expected", .*?, "Actual", (.*?), "Agrees"', text)
    claim(m is not None, f"the Checks tab has the row {label!r}")
    return m.group(1) if m else ""


def visual_title(claim, page: str, name: str) -> str:
    """The title of a visual of the solution project's report page, as Desktop shows it."""
    path = REPORT / "definition" / "pages" / page / "visuals" / name / "visual.json"
    try:
        v = json.loads(path.read_text(encoding="utf-8"))
        title = v["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"].strip("'").replace("''", "'")
    except (OSError, KeyError, IndexError, ValueError):
        title = ""
    claim(title != "", f"the visual {name} of page {page} in the solution project has a title")
    return title


def relationship(claim, source: str, target: str) -> bool:
    """True when the solution project relates source (Table.Column) to target and the relationship is active."""
    text = _model_text("relationships.tmdl")
    m = re.search(r"fromColumn: " + re.escape(source) + r"\n\ttoColumn: " + re.escape(target) + r"(\n\tisActive: false)?", text)
    claim(m is not None, f"the solution project relates {source} to {target}")
    return bool(m) and not m.group(1)


def query_tab(name: str) -> str:
    return (MODEL / "DAXQueries" / f"{name}.dax").read_text(encoding="utf-8")


def tab_blocks(text: str, starts: list[str]) -> list[str]:
    """The query blocks of a tab that begin with the given comment lines, each cut at the next block."""
    positions = [text.index(s) for s in starts] + [text.index("// Model answer")]
    return [text[a:b].strip() for a, b in zip(positions, positions[1:])]


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
    comment = source.note_comment("chapters/14-data-models-and-dax/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 14\b")
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
    """The rows of the Checks tab by section (Tutorial 14.1 ... Exercise 14.6)."""
    text = (MODEL / "DAXQueries" / "Checks.dax").read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for sec in re.findall(r'ROW \( "Section", "([^"]*)"', text):
        counts[sec] = counts.get(sec, 0) + 1
    return counts


# --- the chapter note ------------------------------------------------------------------------------------------------

@context("ch14.chapter")
def chapter(d, claim):
    need(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 15, "the chapter has fifteen multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    claim(version() != "", "Tutorial 13.1 names the Power BI Desktop version")
    claim(MODEL.is_dir() and REPORT.is_dir(), "the solution project of Chapter 14 is in outputs/companion/solutions")
    pages = json.loads((REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    claim(pages == ["salesDiscounts", "validation", "review", "margins", "incomeStatement", "ex141", "ex142", "ex143",
                    "ex144", "notes"], "the project's pages are the five of the tutorials, Ex 14.1 to Ex 14.4 and Notes")
    tabs = json.loads((MODEL / ".pbi" / "daxQueries.json").read_text(encoding="utf-8"))["tabOrder"]
    claim(tabs == ["Tests", "Ex 14.5", "Control Totals", "Checks"], "the project's DAX query tabs are Tests, Ex 14.5, Control Totals and Checks")
    sections = check_sections()
    mine = sum(v for k, v in sections.items() if k.startswith(("Tutorial 14", "Exercise 14")))
    claim(mine > 0, "the Checks tab holds rows for Tutorial 14.1 to Exercise 14.6")
    lines, invoices = len(n14.pick(d, year=d.C)), len({r["invoice"] for r in n14.pick(d, year=d.C)})
    claim(lines > invoices, "the invoice lines of the current year outnumber its invoices")
    claim(len(d.closes) == 6, "the ledger holds six closing entries")
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountName IN ('Sales Returns and Allowances') OR AccountNumber = '4060'") >= 1,
          "the chart has a contra revenue account")
    # Test 3 with the year's closes left in: the same accounts, smaller balances
    kept = [b for (b,) in d.q("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE PostingDate <= ? GROUP BY AccountID", f"{d.C}-12-31")]
    accounts, debit, credit = n14.trial_balance(d, f"{d.C}-12-31")
    tb_kept = sum(b for b in kept if b > 0)
    claim(abs(tb_kept + sum(b for b in kept if b < 0)) < 0.005 and tb_kept < debit,
          "with the year's closes left in, the trial balance still balances but at a smaller total than Chapter 6's")
    return dict(y=d.C, f=d.F, p=d.P, n=d.N, tb_kept=tb_kept, version=version(), slides=slide_count(), n_exercises=sum(ex.values()),
                per_perspective=ex.get("financial", 0), n_questions=n_q, n_longest=len(longest), longest_correct=and_list(longest),
                steps=step_counts(), n_checks=sum(sections.values()), n_checks_mine=mine, n_pages=len(pages),
                n_lines=lines, n_invoices=invoices)


# --- Exercise 14.1 ---------------------------------------------------------------------------------------------------

def balances_by_account(d, asof: str) -> list[tuple]:
    """(AccountType, NormalBalance, AccountNumber, AccountName, balance) at the as-of date, the closes left out only on it."""
    return d.q("SELECT a.AccountType, a.NormalBalance, a.AccountNumber, a.AccountName, SUM(g.Debit) - SUM(g.Credit) "
               "FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.PostingDate <= ? "
               f"AND NOT ({n14.is_close(d)} AND g.PostingDate = ?) GROUP BY 1, 2, 3, 4", asof, asof)


@context("ch14.g1")
def g1(d, claim):
    need(d, claim, "GLEntry", "Account", "JournalEntry")
    y, asof = d.C, f"{d.C}-12-31"
    rows = balances_by_account(d, asof)
    # a balance that does not accumulate: the month's own postings only
    month = dict(d.q("SELECT a.AccountType, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                     f"WHERE substr(g.PostingDate, 1, 7) = ? AND NOT ({n14.is_close(d)} AND g.PostingDate = ?) GROUP BY 1",
                     asof[:7], asof))
    claim(abs(sum(month.values())) < 0.005, "the postings of one month balance, so a measure that does not accumulate still totals zero")
    right = n14.by_type(d, asof)
    claim(month["Asset"] < 0.05 * right["Asset"], "one month's net movement of the assets is a small part of the balance")
    # signs taken from each account's NormalBalance, as a statement that follows it would show them
    by_nb = {t: 0.0 for t in TYPES}
    for t, nb, _, _, b in rows:
        by_nb[t] += b if nb == "Debit" else -b
    correct = {t: right[t] if t in ("Asset", "Expense") else -right[t] for t in right}
    over = {t: by_nb[t] - correct[t] for t in TYPES if t in correct}
    claim(abs(over.get("Liability", 0)) < 0.005 and abs(over.get("Equity", 0)) < 0.005 and abs(over.get("Expense", 0)) < 0.005,
          "only the asset and revenue subtotals change when signs follow NormalBalance")
    dep = -sum(b for t, nb, n, name, b in rows if t == "Asset" and nb == "Credit")
    contra_rev = sum(b for t, nb, n, name, b in rows if t == "Revenue" and nb == "Debit")
    claim(abs(over["Asset"] - 2 * dep) < 0.005 and abs(over["Revenue"] - 2 * contra_rev) < 0.005,
          "taking signs from NormalBalance overstates each subtotal by twice its contra balances")
    contra = d.q("SELECT AccountNumber, AccountName, AccountType, NormalBalance FROM Account WHERE "
                 "(AccountType IN ('Asset', 'Expense') AND NormalBalance = 'Credit') OR "
                 "(AccountType IN ('Liability', 'Equity', 'Revenue') AND NormalBalance = 'Debit') ORDER BY AccountNumber")
    have = {n: b for t, nb, n, name, b in rows}
    never = [dict(number=n, name=name) for n, name, t, nb in contra
             if d.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = ?", n) == 0]
    claim(0 < len(never) < len(contra), "some of the contra accounts have no postings in any year, and some have balances")
    posted = [dict(number=n, name=name, balance=have[n]) for n, name, t, nb in contra if n in have]
    # the three measures at the latest year-end: the same liabilities, a total of zero in each
    kept, none = n14.by_type(d, asof, "all"), n14.by_type(d, asof, "none")
    claim(all(abs(b["Liability"] - right["Liability"]) < 0.005 for b in (kept, none)),
          "the liabilities are the same under the three balance measures at the latest year-end")
    claim(all(abs(sum(b.values())) < 0.005 for b in (right, kept, none)), "each of the three balance measures totals zero")
    # at a month-end with no close dated on it, the measure that keeps the closes equals Balance
    june = n14.month_end(y, 6)
    claim(all(abs(n14.by_type(d, june, "all")[t] - n14.by_type(d, june)[t]) < 0.005 for t in TYPES),
          "at a month-end inside the year, the balance with the closes kept equals Balance")
    return dict(y=y, f=d.F, asof=asof, month_asset=month["Asset"], month_expense=month["Expense"], right_asset=right["Asset"],
                by_nb_asset=by_nb["Asset"], over_asset=over["Asset"], by_nb_revenue=by_nb["Revenue"], over_revenue=over["Revenue"],
                dep=dep, contra_rev=contra_rev, never=never, n_never=len(never), posted=posted, n_posted=len(posted),
                m_balance=measure(claim, "Balance"), m_closes=measure(claim, "Balance with Closes"),
                m_gl=measure(claim, "Balance on GL Amount"), m_contra=measure(claim, "Contra Accounts"),
                t_month=visual_title(claim, "ex141", "monthEnd"), t_matrix=visual_title(claim, "ex141", "balanceMatrix"),
                t_variants=visual_title(claim, "ex141", "variantsMatrix"), t_contra=visual_title(claim, "ex141", "contraTable"),
                dax_ni=check_expr(claim, f"revenue and expense at {y}-12 = minus the net income of fiscal {y}"))


# --- Exercise 14.2 ---------------------------------------------------------------------------------------------------

@context("ch14.g2")
def g2(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item", "Shipment", "ShipmentLine")
    y = d.C
    rows = n14.lines(d)
    claim(all(r["shipped"] is None for r in rows if r["group"] == "Services"), "no Services line has a shipment")
    n_noguard = sum(1 for r in rows if r["shipped"] is None or r["shipped"][:4] != r["date"][:4])
    n_cross = sum(1 for r in rows if r["shipped"] and r["shipped"][:4] != r["date"][:4])
    n_services = sum(1 for r in rows if r["group"] == "Services")
    claim(n_noguard == n_cross + n_services, "without a null guard, CrossesYear would flag every Services line besides the crossing ones")
    lo, hi = f"{d.F}-01-01", f"{d.N}-12-31"
    claim(all(lo <= r["date"] <= hi and (r["shipped"] is None or lo <= r["shipped"] <= hi) for r in rows),
          "every invoice date and ship date falls inside the Date table")
    first200 = d.q("SELECT Discount FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT 200")
    claim(all(float(r[0]) == 0 for r in first200), "the first 200 lines carry no discount, so Power Query types Discount as a whole number")
    shipped_m = table_m("ShippedLines")
    claim(relationship(claim, "ShippedLines.InvoiceDate", "Date.Date"), "the invoice-date relationship of ShippedLines is active")
    inactive = not relationship(claim, "ShippedLines.ShipmentDate", "Date.Date")
    claim(inactive, "the solution project's ship-date relationship is inactive")
    c2 = n14.ex2(d, claim)
    claim(c2["ch12"]["n"] == c2["late"][-1]["invoices"] + len(c2["added"]) and not c2["dropped"],
          "Chapter 12's count is this table's invoices of the current year plus the invoices it adds")
    # a table of the crossing lines without the line key groups the lines that share invoice and dates
    cross = [r for r in rows if r["shipped"] and r["shipped"][:4] != r["date"][:4]]
    keys: dict[tuple, list[dict]] = {}
    for r in cross:
        keys.setdefault((r["number"], r["date"], r["shipped"]), []).append(r)
    pairs = [v for v in keys.values() if len(v) > 1]
    claim(len(pairs) == 1 and len(pairs[0]) == 2,
          "one invoice among the crossing lines has two lines with the same invoice and ship dates, and no other repeats")
    pair = pairs[0] if pairs else [dict(number="", date="", shipped="", rev=0.0, id=0)] * 2
    cross_total = sum(r["rev"] for r in cross)
    claim(abs(cross_total - sum(x["amount"] for x in c2["late"] + c2["early"])) < 0.005,
          "the crossing lines total the amounts of the two kinds")
    return dict(y=y, f=d.F, p=d.P, inactive=inactive, n_noguard=n_noguard, n_services=n_services,
                n_rows_noid=len(keys), pair_number=pair[0]["number"], pair_date=pair[0]["date"], pair_shipped=pair[0]["shipped"],
                pair_amounts=[r["rev"] for r in pair], pair_total=sum(r["rev"] for r in pair), cross_total=cross_total,
                relates_item=relationship(claim, "ShippedLines.ItemID", "Item.ItemID"),
                m_headers=steps(claim, expression_m("ShipmentHeaders"), "Removed Other Columns"),
                m_lines=steps(claim, expression_m("ShipmentLines"), "Removed Other Columns"),
                m_merges=steps(claim, shipped_m, "Merged Queries1", "Merged Queries2"),
                m_cross=steps(claim, shipped_m, "Added Custom"),
                m_shipped=measure(claim, "Shipped Revenue"), m_revship=measure(claim, "Revenue by Ship Date"),
                t_year=visual_title(claim, "ex142", "yearMatrix"), t_cross=visual_title(claim, "ex142", "crossTable"),
                dax_cross=check_expr(claim, "lines that cross a year (CrossesYear)"),
                dax_blank=check_expr(claim, "(Blank) row: revenue with no ship date"))


# --- Exercise 14.3 ---------------------------------------------------------------------------------------------------

PY_FIRST = "CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )"      # Revenue PY as the exercise first asks for it


@context("ch14.g3")
def g3(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item")
    y = d.C
    m_py = measure(claim, "Revenue PY")
    claim(PY_FIRST in re.sub(r"\s+", " ", m_py), "Revenue PY of the project wraps SAMEPERIODLASTYEAR in a test for a blank revenue")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) = ?", str(d.N)) == 0, "no invoice is dated in the year after the window")
    c3 = n14.ex3(d, claim)
    claim(c3["ytd_sign"] == "positive", "Furniture's year-to-date change is positive from January to September")
    claim(c3["ytd"][9] < 0 and c3["ytd"][11] < 0, "Furniture's year-to-date change is negative in October and in December")
    month = {m["name"]: m for m in c3["months"]}
    return dict(y=y, n=d.N, py_first=PY_FIRST, low_row=month[c3["low"]], high_row=month[c3["high"]],
                furniture=next(x for x in c3["by_group"] if x["group"] == "Furniture"),
                ytd_oct=c3["ytd"][9], ytd_dec=c3["ytd"][11], m_py=m_py, m_yoy=measure(claim, "Revenue YoY %"), m_ytd=measure(claim, "Revenue YTD"),
                m_pyytd=measure(claim, "Revenue PY YTD"), m_chg=measure(claim, "YTD Change %"), m_lines=measure(claim, "Group Lines"),
                t_yoy=visual_title(claim, "ex143", "yoyMatrix"), t_ytd=visual_title(claim, "ex143", "ytdTable"),
                t_py=visual_title(claim, "ex143", "pyTable"), t_lines=visual_title(claim, "ex143", "linesMatrix"),
                dax_first=check_expr(claim, f"{d.N}: Revenue PY as first written (the row the exercise explains)"),
                dax_blank=check_expr(claim, f"{d.N}: Revenue PY as changed is blank"),
                dax_oct=check_expr(claim, f"Furniture Revenue YoY % {y}-10"))


# --- Exercise 14.4 ---------------------------------------------------------------------------------------------------

@context("ch14.g4")
def g4(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item")
    y = d.C
    wrong = []
    for qn in range(1, 5):
        py, pq = (y, qn - 1) if qn > 1 else (y - 1, 4)
        a = n14.pick(d, group="Furniture", year=py, quarter=pq)
        b = n14.pick(d, group="Furniture", year=y, quarter=qn)
        ua, ub = n14.total(a, "qty"), n14.total(b, "qty")
        red_a = (n14.total(a, "list") - n14.total(a, "rev")) / ua           # the reduction per unit, discounts included
        red_b = (n14.total(b, "list") - n14.total(b, "rev")) / ub
        lists_wrong = -ub * (red_b - red_a)
        right = n14.bridge(d, "Furniture", y, qn)
        check_wrong = right["pq"] + right["volume"] + right["mix"] + lists_wrong + right["promotions"] - right["gm"]
        claim(abs(check_wrong - right["promotions"]) < 0.005,
              "a price-list effect that keeps the discounts leaves Bridge Check equal to the promotion effect")
        # a volume effect that values the change in units at the current quarter's margin per unit
        m_a = (n14.total(a, "rev") - n14.total(a, "cost")) / ua
        m_b = (n14.total(b, "rev") - n14.total(b, "cost")) / ub
        volume_wrong = (ub - ua) * m_b
        volume_check = right["pq"] + volume_wrong + right["mix"] + right["lists"] + right["promotions"] - right["gm"]
        claim(abs(volume_check - (ub - ua) * (m_b - m_a)) < 0.005,
              "a volume effect at the current margin per unit leaves Bridge Check equal to the change in units times the change in margin per unit")
        wrong.append(dict(label=f"Q{qn}", lists=lists_wrong, check=check_wrong, volume_check=volume_check))
    claim(abs(wrong[-1]["volume_check"]) > 1, "a volume effect at the current margin per unit leaves a visible Bridge Check in the fourth quarter")
    # the first quarter of the data has no quarter before it: DATEADD finds no dates, so Margin PQ and the volume effect
    # are blank (a blank times a number is blank), while the other effects take a blank per-unit amount as zero and add
    # up to the whole margin, so Bridge Check is still zero although nothing is compared
    first = n14.pick(d, group="Furniture", year=d.F, quarter=1)
    u = n14.total(first, "qty")
    lst, rev, disc, cost = (n14.total(first, k) for k in ("list", "rev", "disc", "cost"))
    mix, lists, promo = lst - cost, -(lst - rev - disc), -disc
    claim(u > 0 and abs(mix + lists + promo - (rev - cost)) < 0.005,
          "in the first quarter of the data, with no quarter before it, the mix, price-list and promotion effects add up "
          "to the whole margin, so Bridge Check is zero")
    return dict(y=y, wrong=wrong, first_quarter=f"{d.F}-Q1", m_units=measure(claim, "Units"), m_pq=measure(claim, "Margin PQ"),
                m_volume=measure(claim, "Volume Effect"), m_mix=measure(claim, "Mix Effect"),
                m_lists=measure(claim, "Price List Effect"), m_promo=measure(claim, "Promotion Effect"),
                m_check=measure(claim, "Bridge Check"),
                t_furniture=visual_title(claim, "ex144", "bridgeFurniture"), t_lighting=visual_title(claim, "ex144", "bridgeLighting"),
                dax_check=check_expr(claim, "Bridge Check, largest in any quarter of the window and item group"),
                dax_q4=check_expr(claim, f"Furniture {y}-Q4 Promotion Effect"))


# --- Exercise 14.5 ---------------------------------------------------------------------------------------------------

@context("ch14.g5")
def g5(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item", "Customer", "GLEntry", "Account")
    y = d.C
    tab = query_tab("Ex 14.5")
    q1, q2, q3 = tab_blocks(tab, ["// Customers by item group", "// (2) Operating expense", "// (3) Shares of revenue"])
    claim(all(q.count("EVALUATE") == 1 for q in (q1, q2, q3)), "the Ex 14.5 tab holds three queries, one EVALUATE each")
    claim(len(n14.pick(d, year=y)) > 0, "the current year has invoice lines")
    c5 = n14.ex5(d, claim)
    sum_groups = sum(x["n"] for x in c5["invoiced"])
    claim(sum_groups > c5["n_invoiced"], "customers buy from more than one item group, so the groups' counts add up to more than the year's distinct count")
    opex_all = sum(n14.operating_expense(d).values())
    claim(opex_all > c5["opex"], "operating expense over every year exceeds that of the current year")
    code = lambda q: "\n".join(l for l in q.splitlines() if not l.startswith("//")).strip()
    claim(d.one("SELECT COUNT(DISTINCT PostingDate) FROM GLEntry WHERE substr(PostingDate, 1, 4) = ?", str(y)) == c5["year_days"],
          "the ledger has postings on every day of the current year")
    return dict(y=y, q1=q1, furniture_share=next(s for s in c5["shares"] if s["group"] == "Furniture"), q2=code(q2), q3=code(q3), sum_groups=sum_groups, opex_all=opex_all, m_share=measure(claim, "Share of Revenue"), m_opex=measure(claim, "Operating Expense"),
                dax_both=check_expr(claim, "Services: Operating Expense Both"),
                dax_days=check_expr(claim, "all groups: dates left under Both"))


# --- Exercise 14.6 ---------------------------------------------------------------------------------------------------

@context("ch14.g6")
def g6(d, claim):
    need(d, claim, "GLEntry", "Account", "JournalEntry")
    y = d.C
    tab = query_tab("Control Totals")
    query = tab[:tab.index("// Model answer")].strip()
    claim(query.count("ROW ( \"Test\"") == 7, "the Control Totals tab holds seven tests")
    claim("Fail" in query and "Pass" in query, "the Control Totals query reports Pass or Fail")
    debits_net = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    claim(abs(debits_net) < 0.005, "the journal entries balance, so debits less credits on them is zero")
    no_close = d.one(f"SELECT SUM(g.Debit) FROM GLEntry g WHERE g.SourceDocumentType = 'JournalEntry' AND NOT {n14.is_close(d)}")
    all_debits = d.one("SELECT SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    claim(no_close < all_debits, "the closing entries hold part of the journal entry debits")
    # the invoice revenue test over every revenue account, not the item groups' revenue accounts
    every_revenue = d.one("SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                          "WHERE g.SourceDocumentType = 'SalesInvoice' AND a.AccountType = 'Revenue' AND substr(g.PostingDate, 1, 4) = ?", str(y))
    ids = ",".join(str(d.account(n)) for n in n14.REVENUE)
    ledger = d.one(f"SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND AccountID IN ({ids}) "
                   "AND substr(PostingDate, 1, 4) = ?", str(y))
    freight = d.one("SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                    "WHERE g.SourceDocumentType = 'SalesInvoice' AND a.AccountName = 'Freight Revenue' AND substr(g.PostingDate, 1, 4) = ?", str(y))
    claim(abs(every_revenue - ledger - freight) < 0.005 and freight > 0,
          "the sales invoices also post freight revenue, so a test over every revenue account exceeds the item groups' by the freight")
    m_gl = measure(claim, "GL Amount")
    # Requirement 3's temporary GL Amount: the tutorial's measure without its filter on the closing entries
    kept_closes = "GL Amount = SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] )"
    claim(re.sub(r"\s+", " ", m_gl).startswith("GL Amount = CALCULATE ( SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ), ")
          and "IsYearEndClose" in m_gl, "the project's GL Amount is that sum with the filter on the closing entries")
    claim("[GL Amount]" in query.split('"Invoice revenue in the ledger')[1].split("ROW (")[0]
          and 'SourceDocumentType] = "SalesInvoice"' in query,
          "the ledger revenue test uses GL Amount on the sales invoices' postings only")
    return dict(y=y, query=query, debits_net=debits_net, no_close=no_close, every_revenue=every_revenue, freight=freight,
                m_gl=m_gl, m_gl_kept=kept_closes, m_ni=measure(claim, "Net Income"),
                dax_gap=check_expr(claim, "Ledger less invoice lines", prefix=True),
                dax_fail=check_expr(claim, "(3) GL Amount keeping the closes (changed, then undone): net income reads 0, the test fails"))
