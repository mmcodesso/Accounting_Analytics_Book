"""Chapter 13's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 13 is the first Power BI chapter, so the guides do four jobs:

- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll flags the wording instead of leaving it stale,
- they supply what each exercise's steps need beyond its registered note (ch13.ex1 to ch13.ex6): the symptom of each
  wrong version a guide names (a header table sliced by another table's year, a whole-number type on Discount or
  FreightAmount, a CustomerID that is summed, a ranking over every year, a profile of the first rows), computed
  read-only the way the model would show it,
- they quote the Power Query M and the DAX tests of the model answer from the solution project itself
  (outputs/companion/solutions/Chapter13-exercises-pbi), so a quoted step cannot drift from the file the instructor
  opens: a quote that is not found in the project is a failed claim,
- they supply the chapter note's counts (exercises, questions, slides) from the chapter's own files.

Keys: ch13.chapter (the chapter note) and ch13.g1 to ch13.g6 (the exercises; each is used next to the registered note
ch13.ex1 to ch13.ex6 that supplies the values of the exercise's instructor note). The tutorials' values come from the
registered notes ch13.t1 to ch13.t3.
"""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "13-power-bi-essentials"
DECK = REPO / "slides" / "chapter-13" / "index.qmd"
PROJECT = REPO / "outputs" / "companion" / "solutions" / "Chapter13-exercises-pbi" / "Chapter 13 Exercises - Solutions"
MODEL = PROJECT / "Chapter 13 Exercises - Solutions.SemanticModel"

SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID", "SubTotal", "FreightAmount",
                     "TaxAmount", "GrandTotal", "Status", "PaymentDate"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "BaseListPrice", "UnitPrice",
                         "Discount", "LineTotal", "PromotionID", "PricingMethod", "ShipmentLineID", "PriceListLineID",
                         "PriceOverrideApprovalID"],
    "Item": ["ItemID", "ItemCode", "ItemGroup", "ListPrice", "StandardCost", "CollectionName"],
    "Customer": ["CustomerID", "CustomerName", "CustomerSegment", "Region"],
    "PromotionProgram": ["PromotionID", "PromotionCode", "PromotionName", "ScopeType", "DiscountPct",
                         "EffectiveStartDate", "EffectiveEndDate"],
    "GLEntry": ["SourceDocumentType", "SourceLineID", "AccountID"],
    "Account": ["AccountID", "AccountNumber", "AccountName"],
}
TOP_ROWS = 1000          # the rows Power Query profiles by default (a software constant)
TOP_N = 10               # Exercise 13.2's Top N filter
DETECT_ROWS = 200        # the rows Power Query uses to detect a column's type (Microsoft Learn, as Chapter 4 says)


# --- helpers ---------------------------------------------------------------------------------------------------------

def need(d, claim, *tables: str) -> None:
    """Claims that each table and the columns the guides name are in the database."""
    schema(d, claim, {t: SCHEMA[t] for t in (tables or SCHEMA)})


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _model_text(relative: str) -> str:
    return (MODEL / "definition" / relative).read_text(encoding="utf-8")


def _block(text: str, start: str) -> list[str]:
    """The lines of one M query: from the line after `start` (a 'source =' or 'expression X =' line) to the first blank."""
    lines = text.split("\n")
    i = next(k for k, l in enumerate(lines) if l.strip().startswith(start))
    out = []
    for l in lines[i + 1:]:
        if not l.strip():
            if out:
                break
            continue
        if l.strip().startswith("annotation"):
            break
        out.append(l.strip())
    return out


def table_m(name: str) -> list[str]:
    """The M of a loaded table's partition in the solution project, one stripped line per step."""
    return _block(_model_text(f"tables/{name}.tmdl"), "source =")


def expression_m(name: str) -> list[str]:
    """The M of a query that does not load (Enable load cleared), from expressions.tmdl."""
    return _block(_model_text("expressions.tmdl"), f"expression {name} =")


def steps(claim, lines: list[str], *names: str) -> str:
    """The named steps of an M query, quoted as the Applied Steps formula bar reads them (a claim fails if one is absent)."""
    out = []
    for n in names:
        found = [l for l in lines if l.startswith(f'#"{n}" =') or l.startswith(f"{n} =")]
        claim(len(found) == 1, f"the solution project's query has the step {n}")
        out.extend("    " + l for l in found)
    return "\n".join(out)


def entry(claim, lines: list[str], step: str, column: str) -> str:
    """The `{"Column", type}` entry of a Changed Type step, quoted from the project."""
    line = next((l for l in lines if l.startswith(f'#"{step}" =')), "")
    m = re.search(r'\{"' + re.escape(column) + r'", [^}]+\}', line)
    claim(m is not None, f"the step {step} of the solution project types {column}")
    return m.group(0) if m else ""


def check_expr(claim, label: str) -> str:
    """The DAX expression of one row of the project's Checks tab (DAX query view), found by its label."""
    text = _model_text("../DAXQueries/Checks.dax")
    m = re.search(r'"Check", "' + re.escape(label) + r'", "Expected", .*?, "Actual", (.*?), "Agrees"', text)
    claim(m is not None, f"the Checks tab has the row {label!r}")
    return m.group(1) if m else ""


def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


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
    comment = source.note_comment("chapters/13-power-bi-essentials/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 13\b")
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


def version() -> str:
    m = re.search(r"\(version (\d+\.\d+)\)", (CHAPTER / "_tutorial-01.qmd").read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def whole(x) -> Decimal:
    """A freight amount as Power Query's whole number type keeps it (round half to even)."""
    return Decimal(str(x)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)


def year_rows(d, sql: str, y: int):
    """A query over the invoices dated in year y; `sql` has two ? marks for the first and last day."""
    return d.q(sql, f"{y}-01-01", f"{y}-12-31")


# --- the chapter note --------------------------------------------------------------------------------------------------

@context("ch13.chapter")
def chapter(d, claim):
    need(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 15, "the chapter has fifteen multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    claim(version() != "", "Tutorial 13.1 names the Power BI Desktop version")
    claim(MODEL.is_dir(), "the solution project of Chapter 13 is in outputs/companion/solutions")
    lines = d.q("SELECT COUNT(*), COUNT(DISTINCT SalesInvoiceID) FROM SalesInvoiceLine l JOIN (SELECT SalesInvoiceID AS i FROM SalesInvoice "
                "WHERE InvoiceDate BETWEEN ? AND ?) s ON s.i = l.SalesInvoiceID", f"{d.C}-01-01", f"{d.C}-12-31")[0]
    claim(lines[0] > lines[1], "the invoice lines of the current year outnumber its invoices, so Count and Count (Distinct) differ")
    top_to_date = d.one("SELECT MAX(InvoiceDate) FROM (SELECT si.InvoiceDate FROM SalesInvoiceLine l JOIN SalesInvoice si "
                             "ON si.SalesInvoiceID = l.SalesInvoiceID ORDER BY l.SalesInvoiceLineID LIMIT ?)", TOP_ROWS)
    claim(d.one("SELECT COUNT(*) FROM (SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) = 2)") == 2,
          "two customer names each belong to two customers")
    claim(d.one("SELECT COUNT(*) FROM PromotionProgram WHERE EffectiveEndDate < EffectiveStartDate AND substr(EffectiveStartDate, 1, 4) = ?",
                str(d.C)) == 1, "one promotion of the current year ends before it starts")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Services' "
                "AND l.PromotionID IS NOT NULL") == 0, "services carry no promotion")
    months = d.q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                 "ON si.SalesInvoiceID = l.SalesInvoiceID GROUP BY 1 ORDER BY 1")
    dec_largest = [yr for yr in d.years if max((m for m in months if m[0].startswith(str(yr))), key=lambda m: m[1])[0].endswith("-12")]
    claim(len(dec_largest) < len(d.years), "December is not the largest month of every year, so question 12's holiday option is false")
    year_sum = d.one("SELECT SUM(CAST(substr(InvoiceDate, 1, 4) AS INTEGER)) FROM SalesInvoice")
    return dict(dec_n=len(dec_largest), n_years=len(d.years), y=d.C, f=d.F, p=d.P, version=version(), slides=slide_count(), n_exercises=sum(ex.values()), year_sum=year_sum,
                per_perspective=ex.get("financial", 0), n_questions=n_q, n_longest=len(longest),
                longest_correct=and_list(longest), n_lines=lines[0], n_invoices=lines[1], top_rows=TOP_ROWS,
                top_to=top_to_date, detect_rows=DETECT_ROWS)


# --- Exercise 13.1 -----------------------------------------------------------------------------------------------------

@context("ch13.g1")
def g1(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item", "GLEntry", "Account")
    y = d.C
    first = d.q("SELECT FreightAmount FROM SalesInvoice ORDER BY SalesInvoiceID LIMIT ?", DETECT_ROWS)
    claim(all(float(r[0]) == int(r[0]) for r in first),
          "the first 200 invoices carry whole-dollar freight, so Power Query types FreightAmount as a whole number")
    freight = []
    for yr in d.years:
        rows = year_rows(d, "SELECT FreightAmount FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", yr)
        exact = sum(Decimal(str(r[0])) for r in rows)
        kept = sum(whole(r[0]) for r in rows)
        freight.append(dict(year=yr, exact=float(exact), whole=float(kept), diff=float(kept - exact),
                            fractional=sum(1 for r in rows if float(r[0]) != int(r[0]))))
    claim(max(abs(f["diff"]) for f in freight) < 3,
          "a whole-dollar freight total is within three dollars of the exact total in every year (the cents cancel)")
    all_freight = [r[0] for r in d.q("SELECT FreightAmount FROM SalesInvoice")]
    distinct, distinct_whole = len(set(all_freight)), len({whole(x) for x in all_freight})
    claim(distinct_whole < distinct, "rounding freight to whole dollars merges many distinct values")
    total = d.one("SELECT SUM(SubTotal) FROM SalesInvoice")
    posted = {r[0]: r[1] for r in d.q("SELECT DISTINCT a.AccountName, a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                                      "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.SourceLineID IS NULL")}
    claim(set(posted) == {"Accounts Receivable", "Freight Revenue", "Sales Tax Payable"},
          "the header-level postings of invoices go to receivables, freight revenue, and sales tax payable")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate < ? OR InvoiceDate > ?", f"{d.F}-01-01", f"{d.C}-12-31") == 0,
          "every invoice is dated inside the window, so each falls in a fiscal year row of the matrix")
    year_sum = d.one("SELECT SUM(CAST(substr(InvoiceDate, 1, 4) AS INTEGER)) FROM SalesInvoice")
    header = table_m("InvoiceHeaders")
    m_header = steps(claim, header, "Removed Other Columns", "Added Custom", "Changed Type1")
    fix = "\n".join([
        "// InvoiceHeaders, step Changed Type: the entry after Replace current",
        entry(claim, header, "Changed Type", "FreightAmount"),
        "// SalesInvoice, step Changed Type: the entry Power Query chose from the first rows",
        entry(claim, table_m("SalesInvoice"), "Changed Type", "FreightAmount")])
    dax_sub = check_expr(claim, f"{y} SubTotal (equals the line totals)")
    dax_unrelated = check_expr(claim, "InvoiceHeaders is unrelated (a filter on Item leaves its SubTotal whole)")
    dax_tie = check_expr(claim, f"{y} GrandTotal = SubTotal + freight + tax")
    claim("InvoiceHeaders" not in _model_text("relationships.tmdl"), "the solution project leaves InvoiceHeaders unrelated")
    return dict(y=y, f=d.F, freight=freight, distinct=distinct, distinct_whole=distinct_whole, all_total=total,
                freight_acct=posted["Freight Revenue"], tax_acct=posted["Sales Tax Payable"], ar_acct=posted["Accounts Receivable"],
                year_sum=year_sum, m_header=m_header, m_fix=fix, dax_sub=dax_sub, dax_unrelated=dax_unrelated, dax_tie=dax_tie)


# --- Exercise 13.2 -----------------------------------------------------------------------------------------------------

@context("ch13.g2")
def g2(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Customer")
    y = d.C
    base = ("FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
            "JOIN Customer c ON c.CustomerID = si.CustomerID")
    revenue = d.one(f"SELECT SUM(l.LineTotal) {base} WHERE si.InvoiceDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")
    by_key = {r[0]: (r[1], r[2]) for r in d.q(f"SELECT c.CustomerID, c.CustomerName, SUM(l.LineTotal) {base} "
                                              "WHERE si.InvoiceDate BETWEEN ? AND ? GROUP BY 1", f"{y}-01-01", f"{y}-12-31")}
    by_name: dict[str, float] = {}
    for name, amount in by_key.values():
        by_name[name] = by_name.get(name, 0) + amount
    keys = sorted(by_key, key=lambda k: -by_key[k][1])
    names = sorted(by_name, key=lambda n: -by_name[n])
    top_key, top_name = keys[:TOP_N], names[:TOP_N]
    sum_key = sum(by_key[k][1] for k in top_key)
    sum_name = sum(by_name[n] for n in top_name)
    shared = d.q("SELECT CustomerName, GROUP_CONCAT(CustomerID, ' and '), SUM(CustomerID), COUNT(*) FROM "
                 "(SELECT CustomerName, CustomerID FROM Customer ORDER BY CustomerID) GROUP BY CustomerName HAVING COUNT(*) > 1 ORDER BY CustomerName")
    claim(len(shared) == 2 and all(r[3] == 2 for r in shared), "two customer names belong to two CustomerIDs each")
    both = [r for r in shared if sum(1 for k in by_key if by_key[k][0] == r[0]) == 2]
    claim(len(both) == 1, "one of the shared names has revenue under both its CustomerIDs in the current year")
    # Exercise 13.2 Step 3b's detail table groups by name, segment and region (and the key, once it is not summed)
    other = [r for r in shared if r not in both]
    other_ids = [int(x) for x in str(other[0][1]).split(" and ")] if other else []
    single_none = [k for k in other_ids if k not in by_key]
    claim(len(single_none) == 1, "one of the other shared name's two CustomerIDs has no revenue in the current year")
    pairs = lambda name: d.one("SELECT COUNT(DISTINCT CustomerSegment || '|' || Region) FROM Customer WHERE CustomerName = ?", name)
    claim(pairs(both[0][0]) == 2, "the merged name's two customers differ in segment or region, so a summed key leaves two rows")
    claim(other and pairs(other[0][0]) == 1,
          "the other shared name's two customers share a segment and a region, so a summed key adds their IDs on one row")
    # a ranking over every year, written the way a student who leaves the year out of the ranking would see it
    all_key = [r[0] for r in d.q(f"SELECT c.CustomerID {base} GROUP BY 1 ORDER BY SUM(l.LineTotal) DESC LIMIT ?", TOP_N)]
    wrong_sum = sum(by_key.get(k, ("", 0))[1] for k in all_key)
    claim(wrong_sum < sum_key and len(set(all_key) & set(top_key)) < TOP_N,
          "ranking the customers over every year gives a different ten than ranking the current year")
    n_names = d.one("SELECT COUNT(DISTINCT CustomerName) FROM Customer")
    n_customers = d.one("SELECT COUNT(*) FROM Customer")
    largest = by_key[keys[0]][1]
    claim(largest / revenue < 0.05 / 2, "the largest customer holds under half of the five percent policy")
    dax_rank = check_expr(claim, "Brown LLC rank by name")
    all_rev = d.one("SELECT SUM(LineTotal) FROM SalesInvoiceLine")
    claim(largest / all_rev < 0.01, "against the all-years total the largest customer would hold under one percent")
    return dict(y=y, all_rev=all_rev, largest_all=largest / all_rev, revenue=revenue, sum_key=sum_key, sum_name=sum_name, shared=shared, merged_id_sum=both[0][2],
                merged_ids=both[0][1], single_none=single_none[0], single_id_sum=other[0][2],
                n_names=n_names, n_customers=n_customers, wrong_sum=wrong_sum,
                wrong_overlap=len(set(all_key) & set(top_key)), threshold=0.05 * revenue, largest=largest, dax_rank=dax_rank)


# --- Exercise 13.3 -----------------------------------------------------------------------------------------------------

@context("ch13.g3")
def g3(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "PromotionProgram")
    y = d.C
    per_year = d.q("SELECT substr(si.InvoiceDate, 1, 4), COUNT(*), SUM(CASE WHEN l.PromotionID IS NULL THEN 1 ELSE 0 END), "
                   "COUNT(DISTINCT l.PromotionID) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "GROUP BY 1 ORDER BY 1")
    blank_all = sum(r[2] for r in per_year)
    blank_now = [r for r in per_year if r[0] == str(y)][0]
    promos_now = blank_now[3]
    promos_all = d.one("SELECT COUNT(DISTINCT PromotionID) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL")
    claim(blank_all > blank_now[2] and promos_all > promos_now, "without a year filter the (Blank) row and the promotions list grow")
    n_promotions = d.one("SELECT COUNT(*) FROM PromotionProgram")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL AND PromotionID NOT IN "
                "(SELECT PromotionID FROM PromotionProgram)") == 0, "every promotion on a line is in PromotionProgram, so no key finds no match")
    first200 = d.q("SELECT PromotionID FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT ?", DETECT_ROWS)
    claim(all(r[0] is None for r in first200), "PromotionID is empty in the first 200 lines, so Power Query leaves it untyped")
    promo = table_m("PromotionProgram")
    m_promo = steps(claim, promo, "Removed Other Columns", "Changed Type1")
    lines_m = table_m("SalesInvoiceLine")
    promo_type = entry(claim, lines_m, "Changed Type", "PromotionID")
    untyped = entry(claim, expression_m("Profile_Lines"), "Changed Type", "PromotionID")
    dax_late = check_expr(claim, "promotion 8: lines invoiced after the end date")
    claim(d.one("SELECT PromotionName FROM PromotionProgram WHERE PromotionID = 8") == "Furniture Seasonal Promotion",
          "promotion 8, the one the quoted DAX test counts, is the Furniture Seasonal Promotion")
    claim("PromotionProgram.PromotionID" in _model_text("relationships.tmdl"), "the project relates the lines to PromotionProgram on PromotionID")
    # Step 6's copy of the matrix (item groups on columns): a group with no discount in the year shows zero, from its
    # lines in the (Blank) row alone
    by_group = d.q("SELECT i.ItemGroup, SUM(l.Quantity * l.UnitPrice * l.Discount), SUM(l.PromotionID IS NOT NULL) FROM SalesInvoiceLine l "
                   "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
                   "WHERE si.InvoiceDate BETWEEN ? AND ? GROUP BY 1", f"{y}-01-01", f"{y}-12-31")
    claim(all(r[2] == 0 for r in by_group if not r[1]),
          "every item group with no discount in the current year has no promotion line, so its only cell is in the (Blank) row")
    return dict(y=y, blank_all=blank_all, promos_all=promos_all, promos_now=promos_now, n_promotions=n_promotions,
                m_promo=m_promo, promo_type=promo_type, untyped=untyped, dax_late=dax_late)


# --- Exercise 13.4 -----------------------------------------------------------------------------------------------------

@context("ch13.g4")
def g4(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Customer", "Item")
    y = d.C
    rows = d.q("SELECT c.CustomerSegment, c.Region, SUM(l.LineTotal), SUM(l.Quantity * l.UnitPrice * l.Discount) "
               "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
               "JOIN Customer c ON c.CustomerID = si.CustomerID WHERE si.InvoiceDate BETWEEN ? AND ? GROUP BY 1, 2", f"{y}-01-01", f"{y}-12-31")
    segments = sorted({r[0] for r in rows})
    regions = sorted({r[1] for r in rows})
    claim(len(segments) == 5 and len(regions) == 4, "the page has five segments and four regions")
    disc_total = sum(r[3] for r in rows)
    rev_total = sum(r[2] for r in rows)
    all_rev = d.one("SELECT SUM(LineTotal) FROM SalesInvoiceLine")
    all_disc = d.one("SELECT SUM(Quantity * UnitPrice * Discount) FROM SalesInvoiceLine")
    zero = [s for s in segments if sum(r[3] for r in rows if r[0] == s) == 0]
    claim(len(zero) == 1 and zero[0] == "Design Services", "only the Design Services segment received no discounts")
    cells = len({(r[0], r[1]) for r in rows})
    claim(cells == len(segments) * len(regions), "every pair of segment and region has revenue, so the matrix has no empty cell")
    return dict(y=y, disc_total=disc_total, rev_total=rev_total, all_rev=all_rev, all_disc=all_disc, n_segments=len(segments),
                n_regions=len(regions), zero_segment=zero[0], cells=cells)


# --- Exercise 13.5 -----------------------------------------------------------------------------------------------------

@context("ch13.g5")
def g5(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item", "Customer")
    first = d.q("SELECT Discount FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT ?", DETECT_ROWS)
    claim(all(float(r[0]) == 0 for r in first), "the first 200 lines carry no discount, so Power Query types Discount as a whole number")
    rates = [r[0] for r in d.q("SELECT DISTINCT Discount FROM SalesInvoiceLine")]
    as_whole = {whole(x) for x in rates}
    claim(len(rates) > 1 and len(as_whole) == 1, "typed as a whole number, every discount rate rounds to zero and Discount has one distinct value")
    free = d.q("SELECT FreightAmount FROM SalesInvoice ORDER BY SalesInvoiceID LIMIT ?", DETECT_ROWS)
    claim(all(float(r[0]) == int(r[0]) for r in free), "the first 200 invoices carry whole-dollar freight")
    lines = expression_m("Profile_Lines")
    invoices = expression_m("Profile_Invoices")
    fix = "\n".join([
        "// Profile_Lines, step Changed Type",
        entry(claim, lines, "Changed Type", "Discount"),
        entry(claim, lines, "Changed Type", "PromotionID"),
        "// Profile_Invoices, step Changed Type",
        entry(claim, invoices, "Changed Type", "FreightAmount")])
    dax_top = check_expr(claim, f"PromotionID empty, top {TOP_ROWS:,}")
    claim(all(f"Profile_{n}" in _model_text("expressions.tmdl") for n in ("Lines", "Invoices", "Items", "Customers")),
          "the project holds the four Profile queries, none of them loaded into the model")
    claim(d.one("SELECT COUNT(*) FROM Item") <= TOP_ROWS and d.one("SELECT COUNT(*) FROM Customer") <= TOP_ROWS,
          "the Item and Customer Tables fit inside the first 1,000 rows, so both profile bases agree")
    keys = {"SalesInvoiceLine": ("SalesInvoiceLineID", "SalesInvoiceID", "ItemID"), "SalesInvoice": ("SalesInvoiceID", "CustomerID"),
            "Item": ("ItemID",), "Customer": ("CustomerID",)}
    claim(all(d.one(f"SELECT COUNT(*) FROM {t} WHERE {c} IS NULL") == 0 for t, cs in keys.items() for c in cs),
          "none of the keys that relate the four Tables is empty (Step 5's conclusion)")
    small = ["PriceListLineID", "ShipmentLineID", "PriceOverrideApprovalID"]
    n_all = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    for col in small:
        full = d.one(f"SELECT COUNT(*) FROM SalesInvoiceLine WHERE {col} IS NULL")
        top = d.one(f"SELECT COUNT(*) FROM (SELECT {col} FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID LIMIT ?) WHERE {col} IS NULL", TOP_ROWS)
        claim(abs(full / n_all - top / TOP_ROWS) < 0.01, f"the empty share of {col} moves by under one percentage point between the bases")
    return dict(distinct_whole=len(as_whole), m_fix=fix, dax_top=dax_top, top_rows=TOP_ROWS, small_names=and_list(small))


# --- Exercise 13.6 -----------------------------------------------------------------------------------------------------

@context("ch13.g6")
def g6(d, claim):
    need(d, claim, "SalesInvoice", "SalesInvoiceLine", "Item")
    y = d.C
    rev = d.one("SELECT SUM(LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                "WHERE si.InvoiceDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")
    services = d.one("SELECT SUM(LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                     "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Services' AND si.InvoiceDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")
    claim(services > 0, "the current year has service revenue for a hidden filter to remove")
    dax_ratio = check_expr(claim, "discount dollars over the dollars before discount")
    claim(MODEL.is_dir(), "the solution project is present")
    revised_title = f"Revenue by item group, fiscal {y} (all item groups, including Services)"
    claim(revised_title in (PROJECT / "Chapter 13 Exercises - Solutions.Report" / "definition" / "pages" / "ex136r" / "visuals" /
                            "groupBars" / "visual.json").read_text(encoding="utf-8"),
          "the revised page's bar chart carries the title the guide quotes")
    import json
    visual = json.loads((PROJECT / "Chapter 13 Exercises - Solutions.Report" / "definition" / "pages" / "ex136r" / "visuals" /
                         "monthsFromZero" / "visual.json").read_text(encoding="utf-8"))
    alt = visual["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"]["expr"]["Literal"]["Value"].strip("'")
    claim(alt.startswith("Monthly revenue over three years"), "the revised page's line chart carries the alternative text the guide quotes")
    # the revised card without its year filter: the page has none, so it would total every year
    all_disc, all_list = d.q("SELECT SUM(Quantity * UnitPrice * Discount), SUM(Quantity * BaseListPrice) FROM SalesInvoiceLine")[0]
    cur_disc = d.one("SELECT SUM(l.Quantity * l.UnitPrice * l.Discount) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                     "ON si.SalesInvoiceID = l.SalesInvoiceID WHERE si.InvoiceDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")
    claim(all_disc > cur_disc, "without its year filter the revised card would show more discounts than the current year's")
    return dict(y=y, f=d.F, shown=rev - services, dax_ratio=dax_ratio, revised_title=revised_title, alt_example=alt,
                all_disc=all_disc, all_list=all_list)
