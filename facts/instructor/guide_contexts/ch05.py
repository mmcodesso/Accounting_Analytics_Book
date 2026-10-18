"""Chapter 5's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 5 is the second Excel chapter (text, date and logical functions, lookups, Power Query merges), so the contexts
do three jobs, as in Chapter 4:

- they supply the values a step-by-step solution can show as "Check" values (the tutorials' control totals, the cells
  of each exercise's model answer),
- they give the column letters of the Tables the steps add to, as the workbook lays them out (a new column goes in the
  first empty cell to the right of the last header, so the guide names the letter), and
- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll or a schema change flags the wording instead of leaving it stale.

Keys: ch05.chapter (the chapter note and its three tutorials) and ch05.g1 to ch05.g6 (the exercises; each is used next
to the registered note ch05.ex1 to ch05.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter05-exercises (Chapter 5 Exercises - Solutions.xlsx).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, schema
from guide_contexts.ch04 import letters_of, long_date
from notes.ch05 import furniture_by_quarter, proper, quarter_of, related_parties

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "05-data-preparation"
DECK = REPO / "slides" / "chapter-05" / "index.qmd"

# Tutorial 5.1's names for the Furniture product types (tbl-05-03), in the order the table lists them
TYPE_LABELS = dict(BKC="Bookcase", BNH="Bench", CON="Console table", CTB="Coffee table", DSK="Desk", NGT="Nightstand",
                   SDB="Sideboard", TBL="Dining table")
# the calculated columns each step adds, in the order the workbook holds them
SI_TUTORIAL = ["FiscalYear", "FiscalQuarter", "Period", "DaysToDue", "TermsGroup", "StandardTerms"]       # Tutorial 5.1
SI_EXERCISES = ["NumberYearText", "NumberYear", "NumberYearMatches", "OrderDate", "BeforeOrder"]          # Exercise 5.2
SI_LAG = ["OrderToInvoiceDays"]                                                                           # Exercise 5.4
SIL_TUTORIAL = ["ListAmount", "DiscountAmount", "InvoiceDate", "Period", "SalesOrderID", "OrderDate", "ItemGroup",
                "ProductType"]                                                                            # Chapter 4, Tutorial 5.2
SIL_LAUNCH = ["LaunchDate", "BeforeLaunch"]                                                               # Exercise 5.6
CML_EXERCISE = ["CreditMemoDate", "Period", "ItemGroup"]                                                  # Exercise 5.1
PURCHASING_TITLES = ("Purchasing Manager", "Buyer", "Procurement Analyst")


# --- helpers -------------------------------------------------------------------------------------------------------

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
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/05-data-preparation/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 5\b")
    key = {int(n): a for n, a in re.findall(r"(\d+) ([A-D])[,.]", comment.split("\n", 2)[1])}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def periods(d) -> list[str]:
    return [f"{d.C}-Q{k}" for k in range(1, 5)]


def promotion_rows(d) -> list[dict]:
    """Each promotion with its dates, its invoice lines and the lines invoiced after its EffectiveEndDate."""
    rows = []
    for pid, code, name, rate, start, end in d.q("SELECT PromotionID, PromotionCode, PromotionName, DiscountPct, "
                                                  "EffectiveStartDate, EffectiveEndDate FROM PromotionProgram ORDER BY PromotionID"):
        lines, after = d.q("SELECT COUNT(*), SUM(si.InvoiceDate > ?) FROM SalesInvoiceLine l JOIN SalesInvoice si "
                           "ON si.SalesInvoiceID = l.SalesInvoiceID WHERE l.PromotionID = ?", end, pid)[0]
        kind = "ends before it starts" if end < start else "lasts one day" if end == start else ""
        rows.append(dict(id=pid, code=code, name=name, rate=rate, start=start, end=end, lines=lines, after=after or 0,
                         share=(after or 0) / lines if lines else 0.0, kind=kind))
    return rows


# --- the chapter note and its tutorials ----------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "SalesOrderID", "CustomerID", "PaymentDate"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "LineTotal", "PromotionID"],
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "ListPrice", "UnitOfMeasure", "LifecycleStatus"],
    "SalesOrder": ["SalesOrderID", "OrderNumber", "OrderDate"],
    "Customer": ["CustomerID", "CustomerName", "CustomerSegment", "Region"],
    "PromotionProgram": ["PromotionID", "PromotionCode", "EffectiveStartDate", "EffectiveEndDate"],
    "Shipment": ["SalesOrderID", "ShipmentDate"],
}


@context("ch05.chapter")
def chapter(d, claim):
    schema(d, claim, CHAPTER_SCHEMA)
    y = d.C
    n_invoices = d.one("SELECT COUNT(*) FROM SalesInvoice")
    n_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    line_total = d.one("SELECT ROUND(SUM(LineTotal), 2) FROM SalesInvoiceLine")

    # Tutorial 5.1: the code check, the periods and the payment terms
    items_all = d.one("SELECT COUNT(*) FROM Item")
    items_sold = d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL")
    form = "length(ItemCode) = 12 AND substr(ItemCode, 4, 1) = '-' AND substr(ItemCode, 8, 1) = '-'"
    fail_sold = d.one(f"SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL AND NOT ({form})")
    fail_all = d.one(f"SELECT COUNT(*) FROM Item WHERE NOT ({form})")
    claim(fail_sold == 0, "every item the workbook's Item Table keeps (the items with a list price) has a code of the form GRP-TYP-9999")
    claim(fail_all > 0 and d.one(f"SELECT COUNT(*) FROM Item WHERE NOT ({form}) AND ListPrice IS NOT NULL") == 0,
          "the items whose code fails the form check are all items without a list price, so the Chapter 4 filter keeps them out of the Table")
    claim({r[0] for r in d.q(f"SELECT DISTINCT ItemType FROM Item WHERE NOT ({form})")} <= {"Service", "Capex"},
          "the items whose code fails the form check are supplier services and capital items")
    types = d.q("SELECT substr(ItemCode, 5, 3), group_concat(DISTINCT ItemGroup) FROM Item WHERE ListPrice IS NOT NULL GROUP BY 1")
    furniture_types = sorted(t for t, g in types if "Furniture" in g.split(","))
    claim(furniture_types == sorted(TYPE_LABELS), "the Furniture items have exactly the eight product types of Table 5.3")
    shared = [(t, g.split(",")) for t, g in types if len(g.split(",")) > 1]
    claim(any(t == "TBL" and "Furniture" in gs for t, gs in shared),
          "a product type code (TBL) is used by Furniture and by another item group, so a product type alone does not identify Furniture")
    terms = d.q("SELECT CAST(julianday(DueDate) - julianday(InvoiceDate) AS INTEGER), COUNT(*) FROM SalesInvoice GROUP BY 1 ORDER BY 1")
    claim([t for t, _ in terms] == [30, 45, 60, 90], "the invoices carry four payment terms: 30, 45, 60 and 90 days")
    up30 = sum(n for t, n in terms if t <= 30)
    mid = sum(n for t, n in terms if 30 < t <= 60)
    over60 = sum(n for t, n in terms if t > 60)
    claim(up30 > over60 and mid > over60 and 0 < over60 < 0.05 * n_invoices,
          "most invoices fall in the two lower bands, and the band over 60 days holds a few hundred")
    labels = d.one("SELECT COUNT(DISTINCT substr(InvoiceDate, 1, 4) || '-Q' || ((CAST(substr(InvoiceDate, 6, 2) AS INTEGER) + 2) / 3)) "
                   "FROM SalesInvoice")
    first_label = d.q("SELECT substr(MIN(InvoiceDate), 1, 4) || '-Q' || ((CAST(substr(MIN(InvoiceDate), 6, 2) AS INTEGER) + 2) / 3) FROM SalesInvoice")[0][0]
    last_label = d.q("SELECT substr(MAX(InvoiceDate), 1, 4) || '-Q' || ((CAST(substr(MAX(InvoiceDate), 6, 2) AS INTEGER) + 2) / 3) FROM SalesInvoice")[0][0]
    claim(labels == 3 * 4 and first_label == f"{d.F}-Q1" and last_label == f"{y}-Q4", "the invoices fill every quarter of the three fiscal years")
    t1 = dict(items_all=items_all, items_sold=items_sold, items_excluded=items_all - items_sold, fail_sold=fail_sold, fail_all=fail_all,
              n_furniture_types=len(furniture_types), shared=and_join(f"{t} ({' and '.join(gs)})" for t, gs in shared),
              terms=terms, up30=up30, mid=mid, over60=over60, n_over60_days=[t for t, _ in terms][-1], n_labels=labels,
              first_label=first_label, last_label=last_label, invoices=n_invoices)

    # Tutorial 5.2: the lookups and the promotion lines invoiced after the end date
    n_orders = d.one("SELECT COUNT(*) FROM SalesOrder")
    unmatched = (d.one("SELECT COUNT(*) FROM SalesInvoiceLine l LEFT JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID WHERE s.SalesInvoiceID IS NULL")
                 + d.one("SELECT COUNT(*) FROM SalesInvoice s LEFT JOIN SalesOrder o ON o.SalesOrderID = s.SalesOrderID WHERE o.SalesOrderID IS NULL")
                 + d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID WHERE i.ListPrice IS NULL")
                 + d.one("SELECT COUNT(*) FROM SalesInvoiceLine l LEFT JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemID IS NULL"))
    claim(unmatched == 0, "every invoice line finds its invoice and its item (among the items with a list price), and every invoice finds its order")
    claim(d.one("SELECT COUNT(*) FROM (SELECT SalesOrderID FROM SalesInvoice GROUP BY 1 HAVING COUNT(*) > 1)") > 0,
          "a sales order can have several invoices, so the lookup from an invoice to its order follows the relationship toward its one side")
    claim(d.one("SELECT COUNT(*) FROM (SELECT SalesOrderID FROM Shipment GROUP BY 1 HAVING COUNT(DISTINCT ShipmentDate) > 1)") > 0,
          "a sales order can have several shipments on different dates, so a lookup of an order's shipment date returns one of them")
    claim("SalesInvoiceID" not in [r[1] for r in d.q("PRAGMA table_info(SalesOrder)")],
          "the SalesOrder Table has no SalesInvoiceID column, so the order date cannot be looked up with the line's invoice key")
    promos = promotion_rows(d)
    top = max(promos, key=lambda p: p["lines"])
    claim(d.q("SELECT ItemGroup FROM PromotionProgram WHERE PromotionID = ?", top["id"])[0][0] == "Furniture",
          "the promotion with the most invoice lines covers the Furniture item group")
    months = dict(d.q("SELECT substr(si.InvoiceDate, 6, 2), COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                      "WHERE l.PromotionID = ? AND si.InvoiceDate > ? GROUP BY 1", top["id"], top["end"]))
    ordered_within = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                           "JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID WHERE l.PromotionID = ? AND si.InvoiceDate > ? "
                           "AND o.OrderDate BETWEEN ? AND ?", top["id"], top["end"], top["start"], top["end"])
    claim(ordered_within == top["after"], "every promotion line invoiced after the end date comes from an order placed while the promotion ran")
    claim(top["after"] > 100, "more than a hundred lines of the largest promotion were invoiced after its end date")
    multi_ship = d.one("SELECT COUNT(*) FROM (SELECT SalesOrderID FROM Shipment GROUP BY 1 HAVING COUNT(*) > 1)")
    multi_invoice = d.one("SELECT COUNT(*) FROM (SELECT SalesOrderID FROM SalesInvoice GROUP BY 1 HAVING COUNT(*) > 1)")
    fanout = d.one("SELECT COUNT(*) FROM SalesInvoice s LEFT JOIN Shipment h ON h.SalesOrderID = s.SalesOrderID")
    claim(fanout > n_invoices, "a left outer merge of SalesInvoice with Shipment on SalesOrderID adds rows, because an order can have several shipments")
    t2 = dict(orders=n_orders, fanout=fanout, multi_ship=multi_ship, multi_invoice=multi_invoice, promo=dict(top, months=months, nov=months.get("11", 0), dec=months.get("12", 0),
                                          start_long=long_date(top["start"]), end_long=long_date(top["end"])))

    # Tutorial 5.3: InvoiceLines
    n_customers = d.one("SELECT COUNT(*) FROM Customer")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l LEFT JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID "
                "LEFT JOIN Customer c ON c.CustomerID = s.CustomerID WHERE c.CustomerID IS NULL") == 0,
          "every invoice's customer is in the Customer Table, so the three left outer merges add columns and no rows")
    fractional = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE Quantity <> CAST(Quantity AS INTEGER)")
    claim(fractional > n_lines / 2, "most invoice lines carry a fractional quantity")
    t3 = dict(customers=n_customers, lines=n_lines, line_total=line_total, fractional=fractional, fractional_share=fractional / n_lines)

    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    cols = [r[1] for r in d.q("PRAGMA table_info(SalesInvoice)")]
    claim(len(cols) == 12 and cols[-1] == "PaymentDate", "the SalesInvoice Table's last database column is PaymentDate, so the tutorial's columns start after it")
    return dict(y=y, n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(), n_questions=n_q,
                longest_correct=and_join(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3,
                si=letters_of(d, claim, "SalesInvoice", extra=SI_TUTORIAL + SI_EXERCISES + SI_LAG),
                item=letters_of(d, claim, "Item", ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "StandardCost", "ListPrice",
                                                   "UnitOfMeasure", "SupplyMode", "CollectionName", "LifecycleStatus"],
                                extra=["ProductType", "CodeCheck"]),
                sil=letters_of(d, claim, "SalesInvoiceLine", extra=SIL_TUTORIAL + SIL_LAUNCH),
                backwards_ids=and_join(p["id"] for p in promos if p["kind"] == "ends before it starts"),
                one_day_ids=and_join(p["id"] for p in promos if p["kind"] == "lasts one day"))


# --- Exercise 5.1: net Furniture revenue --------------------------------------------------------------------------------

@context("ch05.g1")
def g1(d, claim):
    schema(d, claim, {"CreditMemo": ["CreditMemoID", "CreditMemoNumber", "CreditMemoDate", "OriginalSalesInvoiceID", "SubTotal"],
                      "CreditMemoLine": ["CreditMemoLineID", "CreditMemoID", "ItemID", "LineTotal"],
                      "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate"], "Item": ["ItemID", "ItemGroup", "ListPrice"]})
    y = str(d.C)
    gross = furniture_by_quarter(d)
    claim(d.one("SELECT COUNT(*) FROM CreditMemoLine l JOIN Item i ON i.ItemID = l.ItemID WHERE i.ListPrice IS NULL") == 0,
          "every credit memo line is for an item with a list price, so a lookup into the tutorial's Item Table finds it")
    memos = d.one("SELECT COUNT(*) FROM CreditMemo WHERE substr(CreditMemoDate, 1, 4) = ?", y)
    lines = d.one("SELECT COUNT(*) FROM CreditMemoLine l JOIN CreditMemo m ON m.CreditMemoID = l.CreditMemoID "
                  "WHERE substr(m.CreditMemoDate, 1, 4) = ?", y)
    furniture_credit = d.one("SELECT ROUND(SUM(l.LineTotal), 2) FROM CreditMemoLine l JOIN CreditMemo m ON m.CreditMemoID = l.CreditMemoID "
                             "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND substr(m.CreditMemoDate, 1, 4) = ?", y)
    mixed = d.one("SELECT COUNT(*) FROM (SELECT m.CreditMemoID FROM CreditMemo m JOIN CreditMemoLine l ON l.CreditMemoID = m.CreditMemoID "
                  "JOIN Item i ON i.ItemID = l.ItemID WHERE substr(m.CreditMemoDate, 1, 4) = ? GROUP BY 1 "
                  "HAVING SUM(i.ItemGroup = 'Furniture') > 0 AND SUM(i.ItemGroup <> 'Furniture') > 0)", y)
    header = d.one("SELECT ROUND(SUM(m.SubTotal), 2) FROM CreditMemo m WHERE substr(m.CreditMemoDate, 1, 4) = ? AND EXISTS "
                   "(SELECT 1 FROM CreditMemoLine l JOIN Item i ON i.ItemID = l.ItemID WHERE l.CreditMemoID = m.CreditMemoID "
                   "AND i.ItemGroup = 'Furniture')", y)
    claim(mixed > 0 and header > furniture_credit, "some credit memos hold lines of Furniture and of another item group, so a memo's SubTotal overstates the Furniture credit")
    memos_all = d.one("SELECT COUNT(*) FROM CreditMemo")
    lines_all = d.one("SELECT COUNT(*) FROM CreditMemoLine")
    wrong_key = d.one("SELECT COUNT(*) FROM CreditMemoLine l WHERE NOT EXISTS (SELECT 1 FROM CreditMemo m WHERE m.CreditMemoID = l.CreditMemoLineID)")
    claim(0 < wrong_key < lines_all / 2, "the credit memo line IDs and the credit memo IDs overlap, so a lookup on the wrong key returns a date for most lines and No match for a few")
    # the credits of the year for invoices of an earlier year (requirement 4)
    early = d.q("SELECT m.CreditMemoID, m.CreditMemoDate, s.InvoiceDate FROM CreditMemo m JOIN SalesInvoice s ON s.SalesInvoiceID = m.OriginalSalesInvoiceID "
                "WHERE substr(m.CreditMemoDate, 1, 4) = ? AND substr(s.InvoiceDate, 1, 4) < ?", y, y)
    claim(len(early) > 0 and all(r[1][5:7] == "01" for r in early), "the credit memos for earlier years' invoices are all dated in January")
    early_lines, early_furn_lines, early_furn = d.q(
        "SELECT COUNT(*), SUM(i.ItemGroup = 'Furniture'), ROUND(SUM(CASE WHEN i.ItemGroup = 'Furniture' THEN l.LineTotal ELSE 0 END), 2) "
        "FROM CreditMemoLine l JOIN CreditMemo m ON m.CreditMemoID = l.CreditMemoID JOIN SalesInvoice s ON s.SalesInvoiceID = m.OriginalSalesInvoiceID "
        "JOIN Item i ON i.ItemID = l.ItemID WHERE substr(m.CreditMemoDate, 1, 4) = ? AND substr(s.InvoiceDate, 1, 4) < ?", y, y)[0]
    # an alternative: each 2026 credit goes to the quarter of its original invoice
    by_invoice = {k: v for k, v in d.q(
        "SELECT CASE WHEN substr(s.InvoiceDate, 1, 4) < ? THEN 0 ELSE (CAST(substr(s.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3 END, "
        "ROUND(SUM(l.LineTotal), 2) FROM CreditMemoLine l JOIN CreditMemo m ON m.CreditMemoID = l.CreditMemoID "
        "JOIN SalesInvoice s ON s.SalesInvoiceID = m.OriginalSalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
        "WHERE i.ItemGroup = 'Furniture' AND substr(m.CreditMemoDate, 1, 4) = ? GROUP BY 1", y, y)}
    by_memo = dict(d.q("SELECT (CAST(substr(m.CreditMemoDate, 6, 2) AS INTEGER) + 2) / 3, SUM(l.LineTotal) FROM CreditMemoLine l JOIN CreditMemo m "
                       "ON m.CreditMemoID = l.CreditMemoID JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' "
                       "AND substr(m.CreditMemoDate, 1, 4) = ? GROUP BY 1", y))
    max_share = max(by_memo.get(k, 0.0) / gross[k] for k in range(1, 5))
    claim(max_share < 0.02, "the Furniture credits are under two percent of the revenue billed in every quarter")
    alt3, alt4 = gross[3] - by_invoice.get(3, 0.0), gross[4] - by_invoice.get(4, 0.0)
    claim(alt4 < alt3, "the Furniture revenue still falls from the third to the fourth quarter when each credit is assigned to the quarter of its original invoice")
    # the two comparisons requirement (4) can lead to: the workbook's row 18 moves only the credits for earlier years'
    # invoices out of the year, while a full original-quarter view also moves credits between the quarters of the year
    early_by_q = dict(d.q("SELECT (CAST(substr(m.CreditMemoDate, 6, 2) AS INTEGER) + 2) / 3, SUM(l.LineTotal) FROM CreditMemoLine l "
                          "JOIN CreditMemo m ON m.CreditMemoID = l.CreditMemoID JOIN SalesInvoice s ON s.SalesInvoiceID = m.OriginalSalesInvoiceID "
                          "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND substr(m.CreditMemoDate, 1, 4) = ? "
                          "AND substr(s.InvoiceDate, 1, 4) < ? GROUP BY 1", y, y))
    claim(list(early_by_q) == [1], "the Furniture credits for earlier years' invoices all fall in the first quarter's credit memos")
    net_memo = [gross[k] - by_memo.get(k, 0.0) for k in range(1, 5)]
    prior_only = [round(net_memo[k - 1] + early_by_q.get(k, 0.0), 2) for k in range(1, 5)]
    alt = [round(gross[k] - by_invoice.get(k, 0.0), 2) for k in range(1, 5)]
    moves = []
    for mq, iy, iq, amount in d.q(
            "SELECT (CAST(substr(m.CreditMemoDate, 6, 2) AS INTEGER) + 2) / 3, substr(s.InvoiceDate, 1, 4), "
            "(CAST(substr(s.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3, ROUND(SUM(l.LineTotal), 2) FROM CreditMemoLine l "
            "JOIN CreditMemo m ON m.CreditMemoID = l.CreditMemoID JOIN SalesInvoice s ON s.SalesInvoiceID = m.OriginalSalesInvoiceID "
            "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND substr(m.CreditMemoDate, 1, 4) = ? "
            "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3", y):
        if (iy, iq) != (y, mq):
            moves.append(dict(source=f"{y}-Q{mq}", target=f"{iy}-Q{iq}", amount=amount, earlier=iy < y))
    claim(all(m["target"] < m["source"] for m in moves), "a credit's invoice is never in a later quarter than the credit memo")
    claim(sum(1 for m in moves if not m["earlier"]) > 0,
          "some credits of the year are for invoices of an earlier quarter of the same year, so a full original-quarter view moves more than the earlier-year credits")
    claim(all(prior_only[k] == round(net_memo[k], 2) for k in range(1, 4)) and prior_only[0] > net_memo[0],
          "moving only the earlier-year credits raises the first quarter's net revenue and leaves the other three unchanged")
    furn_lines_year = d.one("SELECT COUNT(*) FROM CreditMemoLine l JOIN CreditMemo m ON m.CreditMemoID = l.CreditMemoID JOIN Item i "
                            "ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND substr(m.CreditMemoDate, 1, 4) = ?", y)
    return dict(y=y, periods=periods(d), memos=memos, lines=lines, memos_all=memos_all, lines_all=lines_all, wrong_key=wrong_key, furniture_credit=furniture_credit, mixed=mixed, header=header,
                header_over=round(header - furniture_credit, 2), early_memos=len(early), early_lines=early_lines, early_furn_lines=early_furn_lines,
                early_furn=early_furn, early_first=min(r[1] for r in early), early_last=max(r[1] for r in early),
                inv_first=min(r[2] for r in early), inv_last=max(r[2] for r in early),
                by_invoice=[by_invoice.get(k, 0.0) for k in range(0, 5)], max_share=max_share, alt3=round(alt3, 2), alt4=round(alt4, 2),
                alt=alt, prior_only=prior_only, early_by_q=[round(early_by_q.get(k, 0.0), 2) for k in range(1, 5)],
                moves=moves, within_moves=[m for m in moves if not m["earlier"]], furn_lines_year=furn_lines_year,
                letters=letters_of(d, claim, "CreditMemoLine", extra=CML_EXERCISE))


# --- Exercise 5.2: document numbers against dates ---------------------------------------------------------------------------

@context("ch05.g2")
def g2(d, claim):
    schema(d, claim, {"SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SalesOrderID", "SubTotal"],
                      "SalesOrder": ["SalesOrderID", "OrderNumber", "OrderDate"], "Shipment": ["SalesOrderID", "ShipmentDate"]})
    rows = d.q("SELECT si.InvoiceNumber, si.InvoiceDate, so.OrderDate, (SELECT MIN(ShipmentDate) FROM Shipment sh WHERE sh.SalesOrderID = si.SalesOrderID), "
               "si.SubTotal FROM SalesInvoice si JOIN SalesOrder so ON so.SalesOrderID = si.SalesOrderID "
               "WHERE substr(si.InvoiceNumber, 4, 4) <> substr(si.InvoiceDate, 1, 4) OR si.InvoiceDate < so.OrderDate ORDER BY si.InvoiceNumber")
    nine = []
    for number, inv, order, ship, sub in rows:
        nine.append(dict(number=number, date=inv, order=order, ship=ship, sub=sub, prefix=number[3:7] != inv[:4], before=inv < order))
    claim(all(r["prefix"] != r["before"] for r in nine), "no invoice fails both tests, so the two tests find different invoices")
    claim(all(r["ship"] and r["date"] < r["ship"] for r in nine), "every flagged invoice is dated before the first shipment on its order (Tutorial 2.1)")
    claim(all(r["date"][5:7] in ("11", "12", "01") for r in nine), "the flagged invoices are dated in November, December or the first days of January")
    pre = [r for r in nine if r["prefix"]]
    claim(all(r["date"][5:7] in ("11", "12") for r in pre), "the invoices with the next year's prefix are dated in November or December")
    by_year = {}
    for r in pre:
        by_year.setdefault((r["date"][:4], r["number"][3:7]), []).append(r["number"])
    claim(all((date.fromisoformat(r["order"]) - date.fromisoformat(r["date"])).days == 1 for r in nine if r["before"]),
          "each invoice dated before its order is dated one day before it")
    firsts = all(sorted(r["number"] for r in pre if r["number"][3:7] == yr)
                 == [n for (n,) in d.q("SELECT InvoiceNumber FROM SalesInvoice WHERE substr(InvoiceNumber, 4, 4) = ? ORDER BY InvoiceNumber LIMIT ?",
                                       yr, sum(1 for r in pre if r["number"][3:7] == yr))]
                 for yr in {r["number"][3:7] for r in pre})
    claim(firsts, "the invoices with the next year's prefix are the first numbers issued in that year's sequence")
    n_invoices = d.one("SELECT COUNT(*) FROM SalesInvoice")
    cols = [r[1] for r in d.q("PRAGMA table_info(SalesInvoice)")]
    claim(len(cols) == 12, "the SalesInvoice Table has the twelve database columns, so Exercise 5.2's columns follow the six of Tutorial 5.1")
    return dict(nine=nine, n_invoices=n_invoices, pre_sub=round(sum(r["sub"] for r in pre), 2), all_sub=round(sum(r["sub"] for r in nine), 2),
                by_year=[dict(dated=k[0], numbered=k[1], numbers=and_join(v), n=len(v)) for k, v in sorted(by_year.items())],
                letters=letters_of(d, claim, "SalesInvoice", extra=SI_TUTORIAL + SI_EXERCISES + SI_LAG),
                n_before=sum(1 for r in nine if r["before"]), n_prefix=len(pre))


# --- Exercise 5.3: the Furniture product mix --------------------------------------------------------------------------------

@context("ch05.g3")
def g3(d, claim):
    schema(d, claim, {"Item": ["ItemID", "ItemCode", "ItemGroup"], "SalesInvoiceLine": ["ItemID", "Quantity", "LineTotal"]})
    q3, q4 = f"{d.C}-Q3", f"{d.C}-Q4"
    data = {}
    for code, qn, revenue, quantity in d.q(
            "SELECT substr(i.ItemCode, 5, 3), (CAST(substr(si.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3, ROUND(SUM(l.LineTotal), 2), "
            "ROUND(SUM(l.Quantity), 2) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
            "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND si.InvoiceDate BETWEEN ? AND ? GROUP BY 1, 2",
            f"{d.C}-07-01", f"{d.C}-12-31"):
        data.setdefault(code, {})[qn] = (revenue, quantity)
    codes = list(TYPE_LABELS)
    claim(sorted(data) == sorted(codes), "the Furniture lines of the two quarters cover the eight product types of Table 5.3")
    t3 = sum(data[c][3][0] for c in codes)
    t4 = sum(data[c][4][0] for c in codes)
    rows = []
    for c in codes:
        r3, r4 = data[c][3][0], data[c][4][0]
        rows.append(dict(code=c, name=TYPE_LABELS[c], rev3=r3, rev4=r4, q3=data[c][3][1], q4=data[c][4][1], share3=r3 / t3, share4=r4 / t4,
                         pts=100 * (r4 / t4 - r3 / t3)))
    claim(all(abs(r["pts"]) <= 2 for r in rows), "no product type's share changes by more than two percentage points, so the rule highlights none")
    one = [r for r in rows if abs(r["pts"]) > 1]
    claim(len(one) > 0, "lowering the threshold to one percentage point highlights some product types, so the rule can be tested")
    gross = furniture_by_quarter(d)
    claim(abs(t3 - gross[3]) < 0.005 and abs(t4 - gross[4]) < 0.005, "the product types add up to the Furniture revenue of Exercise 5.1")
    other = d.q("SELECT (CAST(substr(si.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3, i.ItemGroup, ROUND(SUM(l.LineTotal), 2) FROM SalesInvoiceLine l "
                "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID WHERE substr(i.ItemCode, 5, 3) = 'TBL' "
                "AND i.ItemGroup <> 'Furniture' AND si.InvoiceDate BETWEEN ? AND ? GROUP BY 1, 2", f"{d.C}-07-01", f"{d.C}-12-31")
    claim(len(other) > 0, "the product type code TBL is also used by another item group in the two quarters")
    lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
                  "WHERE i.ItemGroup = 'Furniture' AND si.InvoiceDate BETWEEN ? AND ?", f"{d.C}-07-01", f"{d.C}-12-31")
    frac = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
                 "WHERE i.ItemGroup = 'Furniture' AND si.InvoiceDate BETWEEN ? AND ? AND l.Quantity <> CAST(l.Quantity AS INTEGER)", f"{d.C}-07-01", f"{d.C}-12-31")
    claim(frac > lines / 2, "most Furniture lines of the two quarters carry a fractional quantity")
    largest = sorted(rows, key=lambda r: -abs(r["pts"]))[:4]
    return dict(q3=q3, q4=q4, rows=rows, t3=t3, t4=t4, qty3=sum(r["q3"] for r in rows), qty4=sum(r["q4"] for r in rows), one=[r["code"] for r in one],
                one_n=len(one), largest=largest, lighting_tbl3=sum(r[2] for r in other if r[0] == 3), lighting_tbl4=sum(r[2] for r in other if r[0] == 4),
                other_group=and_join(sorted({r[1] for r in other})), lines=lines, fractional=frac, fractional_share=frac / lines)


# --- Exercise 5.4: the order-to-invoice lag ---------------------------------------------------------------------------------

@context("ch05.g4")
def g4(d, claim):
    schema(d, claim, {"PromotionProgram": ["PromotionID", "PromotionCode", "EffectiveStartDate", "EffectiveEndDate"],
                      "SalesInvoice": ["SalesInvoiceID", "InvoiceDate", "SalesOrderID"], "SalesOrder": ["SalesOrderID", "OrderDate"]})
    promos = promotion_rows(d)
    flagged = [p for p in promos if p["lines"] and p["after"] == p["lines"]]
    claim(flagged and all(p["kind"] for p in flagged) and all(p["after"] < p["lines"] for p in promos if not p["kind"]),
          "the promotions with every line after the end date are the ones whose dates are wrong (one day, or an end before the start)")
    others = [p for p in promos if p not in flagged]
    claim(all(0.2 < p["share"] < 0.6 for p in others), "every other promotion has between a fifth and three-fifths of its lines invoiced after the end date")
    # the orders behind the flagged promotions' lines: no order date falls inside the recorded dates
    for p in flagged:
        first, last = d.q("SELECT MIN(o.OrderDate), MAX(o.OrderDate) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                          "JOIN SalesOrder o ON o.SalesOrderID = si.SalesOrderID WHERE l.PromotionID = ?", p["id"])[0]
        first_long, last_long = long_date(first[:10]), long_date(last[:10])
        span = (first_long.rsplit(",", 1)[0] if first[:4] == last[:4] else first_long) + " to " + last_long
        p.update(order_first=first[:10], order_last=last[:10], order_span=span,
                 start_long=long_date(p["start"][:10]), end_long=long_date(p["end"][:10]))
        claim(first[:10] > p["end"][:10], f"promotion {p['id']}'s orders are all dated after its recorded end date")
    one_day = [p for p in flagged if p["kind"] == "lasts one day"]
    claim(len(one_day) == 1, "one flagged promotion is recorded for a single day")
    # Exercise 5.4 done straight after the tutorials, without Exercise 5.2: OrderDate and the lag follow Tutorial 5.1's columns
    direct = letters_of(d, claim, "SalesInvoice", extra=SI_TUTORIAL + ["OrderDate"] + SI_LAG)
    top = max(promos, key=lambda p: p["lines"])
    rows = d.q("SELECT si.InvoiceDate, so.OrderDate FROM SalesInvoice si JOIN SalesOrder so ON so.SalesOrderID = si.SalesOrderID")
    lags = [(date.fromisoformat(i) - date.fromisoformat(o)).days for i, o in rows]
    claim(min(lags) == -1, "the invoices dated before their order are dated one day before it")
    claim(sorted(lags)[len(lags) // 2] < 0.75 * (sum(lags) / len(lags)), "the median lag is well below the average lag")
    quarter_means = []
    for qn in range(1, 5):
        v = [(date.fromisoformat(i) - date.fromisoformat(o)).days for i, o in rows if i[:4] == str(d.C) and quarter_of(i) == qn]
        quarter_means.append(sum(v) / len(v))
    return dict(promos=promos, flagged_ids=and_join(p["id"] for p in flagged), n_flagged=len(flagged), top=top,
                one_day_ids=and_join(p["id"] for p in promos if p["kind"] == "lasts one day"),
                backwards_ids=and_join(p["id"] for p in promos if p["kind"] == "ends before it starts"),
                spread=max(quarter_means) - min(quarter_means), lowest=min(quarter_means), highest=max(quarter_means), n_promos=len(promos),
                one_day=one_day[0], backwards=[p for p in flagged if p["kind"] == "ends before it starts"],
                n_orders=d.one("SELECT COUNT(DISTINCT SalesOrderID) FROM SalesInvoice"), n_invoices=len(rows),
                direct_letters=direct, last_promo_row=19 + len(promos),
                letters=letters_of(d, claim, "SalesInvoice", extra=SI_TUTORIAL + SI_EXERCISES + SI_LAG))


# --- Exercise 5.5: related-party suppliers ----------------------------------------------------------------------------------

@context("ch05.g5")
def g5(d, claim):
    schema(d, claim, {"Supplier": ["SupplierID", "SupplierName", "Address", "City", "IsApproved", "SupplierRiskRating"],
                      "Employee": ["EmployeeID", "EmployeeName", "JobTitle", "Address", "City"],
                      "DisbursementPayment": ["SupplierID", "Amount", "PaymentDate"]})
    matches = related_parties(d)
    ids = [m[0] for m in matches]
    raw = d.one("SELECT COUNT(DISTINCT s.SupplierID) FROM Supplier s JOIN Employee e ON lower(e.Address) = lower(s.Address) AND lower(e.City) = lower(s.City)")
    by_address = d.one("SELECT COUNT(DISTINCT s.SupplierID) FROM Supplier s JOIN Employee e ON lower(e.Address) = lower(s.Address)")
    by_city = d.one("SELECT COUNT(DISTINCT s.SupplierID) FROM Supplier s JOIN Employee e ON lower(e.City) = lower(s.City)")
    claim(raw == len(matches) == by_address, "the address alone finds the same suppliers as the address and city, so the city does not change the result in this data")
    claim(d.one("SELECT COUNT(*) FROM Supplier WHERE Address <> TRIM(Address) OR City <> TRIM(City)") == 0
          and d.one("SELECT COUNT(*) FROM Employee WHERE Address <> TRIM(Address) OR City <> TRIM(City)") == 0,
          "no address or city has a stray space, so TRIM changes nothing")
    claim(all(t not in PURCHASING_TITLES for _, _, _, _, t in matches), "none of the matched employees has a purchasing job title")
    claim(d.one(f"SELECT COUNT(*) FROM Supplier WHERE SupplierID IN ({','.join(map(str, ids))}) AND IsApproved = 1 AND SupplierRiskRating = 'Low'") == len(ids),
          "every matched supplier is approved and rated Low risk")
    claim(d.one("SELECT COUNT(*) FROM Supplier WHERE Address LIKE '%*%' OR Address LIKE '%?%' OR Address LIKE '%~%'") == 0
          and d.one("SELECT COUNT(*) FROM Employee WHERE Address LIKE '%*%' OR Address LIKE '%?%' OR Address LIKE '%~%'") == 0,
          "no address holds a wildcard character, so COUNTIFS reads each match key literally")
    claim(d.one("SELECT COUNT(DISTINCT SupplierName) FROM Supplier") == d.one("SELECT COUNT(*) FROM Supplier"),
          "supplier names are unique, so a total by name equals a total by SupplierID in this data")
    inlist = ",".join(map(str, ids))
    n_pay, paid = d.q(f"SELECT COUNT(*), ROUND(SUM(Amount), 2) FROM DisbursementPayment WHERE SupplierID IN ({inlist})")[0]
    late_n, late_paid = d.q(f"SELECT COUNT(*), ROUND(SUM(Amount), 2) FROM DisbursementPayment WHERE SupplierID IN ({inlist}) AND PaymentDate > ?",
                            f"{d.C}-12-31")[0]
    claim(late_n > 0, "the payments in the Table include some dated after the fiscal year-end")
    pay_first, pay_last = d.q(f"SELECT MIN(PaymentDate), MAX(PaymentDate) FROM DisbursementPayment WHERE SupplierID IN ({inlist})")[0]
    claim(pay_last[:4] > str(d.C), "the matched suppliers' payments run past the fiscal year-end")
    titles = {}
    for m in matches:
        titles[m[4]] = titles.get(m[4], 0) + 1
    return dict(matches=[dict(id=m[0], name=m[1], emp=m[2], emp_name=m[3], title=m[4]) for m in matches], n_match=len(matches),
                raw=raw, by_address=by_address, by_city=by_city, n_pay=n_pay, paid=paid, late_n=late_n, late_paid=late_paid,
                pay_first=long_date(pay_first[:10]), pay_last=long_date(pay_last[:10]), year_end=long_date(f"{d.C}-12-31"),
                n_suppliers=d.one("SELECT COUNT(*) FROM Supplier"), n_employees=d.one("SELECT COUNT(*) FROM Employee"),
                n_payments=d.one("SELECT COUNT(*) FROM DisbursementPayment"), n_titles=len(titles),
                supplier_columns=len(d.q("PRAGMA table_info(Supplier)")))


# --- Exercise 5.6: the supplier and item master files -----------------------------------------------------------------------

@context("ch05.g6")
def g6(d, claim):
    schema(d, claim, {"Supplier": ["SupplierID", "SupplierName", "TaxID", "BankAccount", "IsApproved", "SupplierRiskRating"],
                      "PurchaseOrder": ["SupplierID"], "DisbursementPayment": ["SupplierID"],
                      "Item": ["ItemID", "ItemCode", "ItemName", "LifecycleStatus", "IsActive", "LaunchDate", "ListPrice"],
                      "SalesInvoiceLine": ["ItemID", "LineTotal"]})
    names = [r[0] for r in d.q("SELECT SupplierName FROM Supplier ORDER BY SupplierID")]
    changed = [(n, proper(n)) for n in names if proper(n) != n]
    only_and = [n for n, p in changed if " and " in n and not re.search(r"\b[A-Z]{2,}\b", n)]
    only_abbr = [n for n, p in changed if " and " not in n]
    claim(len(only_and) + len(only_abbr) == len(changed) and only_and and only_abbr,
          "every changed name is changed either by its connecting word 'and' or by a capitalized abbreviation, and some of each")
    # a wildcard COUNTIF on the masked bank account finds the same duplicates as an exact comparison: none
    banks = [r[0] for r in d.q("SELECT BankAccount FROM Supplier")]

    def pattern(p: str) -> re.Pattern:
        return re.compile("^" + "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in p) + "$", re.I)

    wildcard_shared = sum(1 for b in banks if sum(1 for x in banks if pattern(b).match(x)) > 1)
    claim(wildcard_shared == 0 and len(set(b[-4:] for b in banks)) == len(banks),
          "a COUNTIF on the masked BankAccount (asterisks read as wildcards) also finds no shared account, because the last four characters differ for every supplier")

    def business(supplier: int) -> tuple[int, int]:
        return (d.one("SELECT COUNT(*) FROM PurchaseOrder WHERE SupplierID = ?", supplier),
                d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE SupplierID = ?", supplier))

    unapproved = [dict(id=s, name=n, risk=r, po=business(s)[0], pay=business(s)[1])
                  for s, n, r in d.q("SELECT SupplierID, SupplierName, SupplierRiskRating FROM Supplier WHERE IsApproved = 0 ORDER BY SupplierID")]
    high = [dict(id=s, name=n, approved=a, po=business(s)[0], pay=business(s)[1])
            for s, n, a in d.q("SELECT SupplierID, SupplierName, IsApproved FROM Supplier WHERE SupplierRiskRating = 'High' ORDER BY SupplierID")]
    claim(any(h["approved"] == 0 for h in high), "one High-risk supplier is also unapproved")
    both = [h["id"] for h in high if h["approved"] == 0]
    # the item master
    full_conflict = d.q("SELECT ItemID FROM Item WHERE LifecycleStatus = 'Discontinued' AND IsActive = 1")
    sold_conflict = d.q("SELECT ItemID FROM Item WHERE LifecycleStatus = 'Discontinued' AND IsActive = 1 AND ListPrice IS NOT NULL")
    claim(full_conflict == sold_conflict, "the Discontinued items that are still active all have a list price, so the filtered Item Table finds the same ones")
    conflict_lines = [(c, n) for c, n in d.q("SELECT i.ItemCode, COUNT(l.SalesInvoiceLineID) FROM Item i LEFT JOIN SalesInvoiceLine l ON l.ItemID = i.ItemID "
                                              "WHERE i.LifecycleStatus = 'Discontinued' AND i.IsActive = 1 GROUP BY i.ItemID ORDER BY i.ItemID")]
    latest = {r[0] for r in d.q("SELECT MAX(s.InvoiceDate) FROM Item i JOIN SalesInvoiceLine l ON l.ItemID = i.ItemID JOIN SalesInvoice s "
                                "ON s.SalesInvoiceID = l.SalesInvoiceID WHERE i.IsActive = 0 GROUP BY i.ItemID")}
    claim(len(latest) == 1, "every inactive item that is still invoiced was last invoiced on the same date")
    inactive_all = d.one("SELECT COUNT(*) FROM Item WHERE IsActive = 0")
    inactive_sold = d.one("SELECT COUNT(DISTINCT i.ItemID) FROM Item i JOIN SalesInvoiceLine l ON l.ItemID = i.ItemID WHERE i.IsActive = 0")
    claim(inactive_all > inactive_sold > 0, "most inactive items were never invoiced, so MAXIFS returns 0 for them")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE LaunchDate IS NULL OR LaunchDate = ''") == 0, "every item has a LaunchDate, so no lookup returns a blank")
    pre_in_filtered = d.one("SELECT COUNT(DISTINCT i.ItemID) FROM Item i JOIN SalesInvoiceLine l ON l.ItemID = i.ItemID JOIN SalesInvoice s "
                            "ON s.SalesInvoiceID = l.SalesInvoiceID WHERE s.InvoiceDate < i.LaunchDate AND i.ListPrice IS NOT NULL")
    claim(pre_in_filtered == d.one("SELECT COUNT(DISTINCT i.ItemID) FROM Item i JOIN SalesInvoiceLine l ON l.ItemID = i.ItemID JOIN SalesInvoice s "
                                   "ON s.SalesInvoiceID = l.SalesInvoiceID WHERE s.InvoiceDate < i.LaunchDate"),
          "every item invoiced before its launch has a list price, so the tutorial's Item Table would find them too")
    sil_cols = [r[1] for r in d.q("PRAGMA table_info(SalesInvoiceLine)")]
    claim(len(sil_cols) == 15, "the SalesInvoiceLine Table has fifteen database columns, so the tutorial's lookups start in column P")
    return dict(n_changed=len(changed), n_names=len(names), only_and=len(only_and), only_abbr=len(only_abbr), wildcard_shared=wildcard_shared,
                unapproved=unapproved, high=high, both=and_join(both), conflict_lines=conflict_lines, inactive_all=inactive_all,
                inactive_sold=inactive_sold, inactive_unsold=inactive_all - inactive_sold,
                letters=letters_of(d, claim, "SalesInvoiceLine", extra=SIL_TUTORIAL + SIL_LAUNCH),
                n_po=d.one("SELECT COUNT(*) FROM PurchaseOrder"), n_items=d.one("SELECT COUNT(*) FROM Item"),
                n_blank_price=d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NULL"),
                n_high_approved_business=sum(1 for h in high if h["approved"] == 1 and h["po"] > 0 and h["pay"] > 0))
