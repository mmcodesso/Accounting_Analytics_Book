"""The Part I case's instructor guides: the values the guides state, and the claims their wording makes.

The case (cases/part-1-case.qmd, "Getting the Data Ready for the Furniture Margin Question") has no solution file: the
student works in CharlesRiver_Work.xlsx with filters, lookups and PivotTables.  The registered notes case1.r2 to case1.r5
(facts/notes/case1.py) already supply the expected values of requirements 2 to 5; these contexts add what the model paths
need beyond them, and check, with claim(), every table and column the guides name and every statement about the data that
another dataset could falsify.

Keys: case1.chapter (the case note) and case1.g1 to case1.g6 (the six requirements; g2 to g5 are used next to the notes
case1.r2 to case1.r5, g1 and g6 with case1.r5 for the margins).
"""

from __future__ import annotations

import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, rows_of, schema
from guide_contexts.ch03 import col_letter, letter

REPO = Path(__file__).resolve().parents[3]
CASE = REPO / "cases" / "part-1-case.qmd"
DECK = REPO / "slides" / "case-part-1" / "index.qmd"
CHAPTER1 = REPO / "chapters" / "01-role-of-analytics" / "chapter.qmd"
GROUP = "Furniture"
# the six stages of Chapter 1's workflow (Figure 1.2): what the case does at each, where, whether it completes the stage
# ("done") or begins it and leaves the rest to Part II ("begun"), and the short label of the guide figure IF-C1-0-A.
# Stage 4 begins here because Requirement 5 computes the descriptive margins (Chapter 1's stage 4 starts with them), and
# stage 5 because the appendix presents the map and the reconciliation; the decomposition and its charts are Part II's.
STAGES = [("Define the Question", "Completed here", "Requirement 1", "done", "Requirement 1"),
          ("Identify and Access the Data", "Completed here", "Requirement 2", "done", "Requirement 2"),
          ("Prepare and Clean the Data", "Completed here, for this comparison", "Requirements 3 to 5", "done",
           "Requirements 3 to 5"),
          ("Analyze the Data", "Begun here, with the descriptive margins of the two quarters, and finished in Part II with their decomposition",
           "Requirement 5, then Part II", "begun", "Requirement 5's margins, then the diagnosis in Part II"),
          ("Visualize and Present the Results", "Begun here, with the data map and the reconciliation table, and finished in "
           "Part II with the charts of the diagnosis", "The appendix (Requirements 2 and 4), then Part II", "begun",
           "The appendix's map and table, then the charts in Part II"),
          ("Communicate Findings and Recommendations", "Completed here, for the readiness findings only", "Requirement 6", "done",
           "Requirement 6, readiness findings only")]

CASE_SCHEMA = {
    "Item": ["ItemID", "ItemGroup", "RevenueAccountID", "COGSAccountID", "InventoryAccountID", "StandardCost", "ListPrice", "SupplyMode"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SalesOrderID"],
    "SalesInvoiceLine": ["SalesInvoiceID", "ShipmentLineID", "ItemID", "Quantity", "BaseListPrice", "UnitPrice", "Discount", "LineTotal"],
    "Shipment": ["ShipmentID", "SalesOrderID", "ShipmentDate", "TrackingNumber", "Status", "DeliveryDate"],
    "ShipmentLine": ["ShipmentLineID", "ShipmentID", "SalesOrderLineID", "ItemID", "ExtendedStandardCost"],
    "SalesOrderLine": ["SalesOrderLineID", "UnitPrice", "Discount"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType", "SourceDocumentID", "SourceLineID",
                "Description", "FiscalYear", "FiscalPeriod"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"],
    "JournalEntry": ["EntryNumber", "EntryType", "PostingDate", "TotalAmount"],
    "SalesReturn": ["SalesReturnID", "ReturnDate"],
    "SalesReturnLine": ["SalesReturnLineID", "SalesReturnID", "ItemID", "ExtendedStandardCost"],
    "CreditMemo": ["CreditMemoID", "CreditMemoDate", "SubTotal"],
    "CreditMemoLine": ["CreditMemoLineID", "CreditMemoID", "ItemID", "LineTotal"],
    "Customer": ["CustomerID", "CustomerName"],
}


# --- helpers -------------------------------------------------------------------------------------------------------

def notes_module():
    import notes
    notes.load()
    from notes import case1
    return case1


def labels(d) -> dict:
    n1 = notes_module()
    q3, q4 = n1.quarter(d.C, 3), n1.quarter(d.C, 4)
    return dict(year=d.C, prev_year=d.P, next_year=d.N, ql3=f"{d.C} Q3", ql4=f"{d.C} Q4", q3_start=q3[0], q3_end=q3[1],
                q4_start=q4[0], q4_end=q4[1], periods3="7, 8 and 9", periods4="10, 11 and 12")


def deck_titles() -> list[str]:
    """The slide titles of the case's deck in order, the title slide first."""
    titles = ["(title slide)"]
    for line in DECK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,2} (.+?)\s*(\{[^}]*\})?\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    return titles


def slide_range(titles: list[str], first: str, after: str | None = None) -> str:
    """'16 to 18' for the slides from the one titled `first` up to the one before `after`; one number when alone."""
    start = next(n for n, t in enumerate(titles, 1) if t.startswith(first))
    end = start
    if after:
        end = next(n for n, t in enumerate(titles, 1) if n > start and t.startswith(after)) - 1
    return str(start) if end <= start else f"{start} to {end}"


def margin(revenue: float, cost: float) -> float:
    return (revenue - cost) / revenue


def ledger_by_source(d, account_id: int, a: str, b: str) -> list[dict]:
    """What a PivotTable of GLEntry shows for one account and one date range: each source document type with its debits and credits."""
    return [dict(source=r[0], rows=r[1], debit=r[2], credit=r[3]) for r in d.q(
        "SELECT SourceDocumentType, COUNT(*), ROUND(SUM(Debit), 2), ROUND(SUM(Credit), 2) FROM GLEntry "
        "WHERE AccountID = ? AND PostingDate BETWEEN ? AND ? GROUP BY 1 ORDER BY 1", account_id, a, b)]


def not_invoiced(d, a: str, b: str) -> dict:
    """Furniture shipment lines of the quarter with no invoice line: the cost posted at shipment, no revenue yet."""
    r = d.q("SELECT COUNT(*), ROUND(COALESCE(SUM(sl.ExtendedStandardCost), 0), 2), "
            "ROUND(COALESCE(SUM(sl.QuantityShipped * ol.UnitPrice * (1 - ol.Discount)), 0), 2) "
            "FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN Item t ON t.ItemID = sl.ItemID "
            "JOIN SalesOrderLine ol ON ol.SalesOrderLineID = sl.SalesOrderLineID "
            "WHERE t.ItemGroup = ? AND s.ShipmentDate BETWEEN ? AND ? "
            "AND NOT EXISTS (SELECT 1 FROM SalesInvoiceLine il WHERE il.ShipmentLineID = sl.ShipmentLineID)", GROUP, a, b)[0]
    return dict(lines=r[0], cost=r[1], at_order_price=r[2])


def invoiced_shipped_elsewhere(d, a: str, b: str) -> dict:
    """Furniture lines invoiced in the quarter whose shipment is dated outside it (revenue and cost fall in different quarters)."""
    r = d.q("SELECT COUNT(*), ROUND(COALESCE(SUM(l.LineTotal), 0), 2) FROM SalesInvoiceLine l "
            "JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID JOIN Item t ON t.ItemID = l.ItemID "
            "JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
            "WHERE t.ItemGroup = ? AND i.InvoiceDate BETWEEN ? AND ? AND s.ShipmentDate NOT BETWEEN ? AND ?", GROUP, a, b, a, b)[0]
    return dict(lines=r[0], revenue=r[1])


def memo_returns(d, a: str, b: str) -> dict:
    """The revenue side of returns in the quarter: the postings to the shared account, and the Furniture part found through the trace."""
    acct = d.q("SELECT AccountID, AccountNumber, AccountName FROM Account WHERE AccountSubType = 'Contra Revenue' "
               "AND AccountID IN (SELECT AccountID FROM GLEntry WHERE SourceDocumentType = 'CreditMemo')")
    all_rows = d.q("SELECT COUNT(*), ROUND(COALESCE(SUM(Debit), 0), 2) FROM GLEntry WHERE AccountID = ? "
                   "AND SourceDocumentType = 'CreditMemo' AND PostingDate BETWEEN ? AND ?", acct[0][0], a, b)[0]
    traced = d.q("SELECT COUNT(*), ROUND(COALESCE(SUM(g.Debit), 0), 2) FROM GLEntry g "
                 "JOIN CreditMemoLine l ON l.CreditMemoLineID = g.SourceLineID JOIN Item t ON t.ItemID = l.ItemID "
                 "WHERE g.AccountID = ? AND g.SourceDocumentType = 'CreditMemo' AND t.ItemGroup = ? "
                 "AND g.PostingDate BETWEEN ? AND ?", acct[0][0], GROUP, a, b)[0]
    return dict(rows=all_rows[0], posted=all_rows[1], furniture_rows=traced[0], furniture=traced[1])


# --- the case note -------------------------------------------------------------------------------------------------------

@context("case1.chapter")
def chapter(d, claim):
    schema(d, claim, CASE_SCHEMA)
    n1 = notes_module()
    sheets = ["Item", "SalesInvoice", "SalesInvoiceLine", "Shipment", "ShipmentLine", "GLEntry", "Account", "JournalEntry"]
    rows = rows_of(d, sheets)
    claim(max(rows, key=rows.get) == "GLEntry", "GLEntry is the largest of the case's worksheets")
    first_post, last_post = d.q("SELECT MIN(PostingDate), MAX(PostingDate) FROM GLEntry")[0]
    last_invoice = d.one("SELECT MAX(InvoiceDate) FROM SalesInvoice")
    last_ship = d.one("SELECT MAX(ShipmentDate) FROM Shipment")
    late = d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE FiscalYear = ? GROUP BY 1", d.N)
    claim([t for t, _ in late] == ["DisbursementPayment"], f"fiscal {d.N} of the ledger holds only DisbursementPayment rows")
    jan, feb = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", f"{d.F}-01-01", f"{d.F}-01-31"), \
        d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", f"{d.F}-02-01", f"{d.F}-02-29")
    claim(jan < 0.7 * feb, f"the first month of the extract (January {d.F}) has far fewer invoices than the second")
    titles = deck_titles()
    claim(len(titles) == 31, "the case's deck has 31 slides")
    text = CASE.read_text(encoding="utf-8")
    n_req = len(re.findall(r"^\*\*Requirement \d+:", text, re.M))
    claim(n_req == 6, "the case has six requirements")
    claim(not re.search(r"^\s*-\s*\*\*Milestone", text, re.M) and "Milestone" not in text, "the case has no milestones")
    chapter1 = CHAPTER1.read_text(encoding="utf-8")
    claim(all(st[0] in chapter1 for st in STAGES), "Chapter 1 names the six stages of the workflow")
    claim("why did gross margins on the Furniture product line decline in the most recent quarter" in chapter1.replace("\n", " "),
          "Chapter 1's opening scenario poses the controller's question")
    slide = dict(opening=slide_range(titles, "The controller's question", "The Situation"), question=slide_range(titles, "The controller's question"), handin=slide_range(titles, "What you will hand in"),
                 judged=slide_range(titles, "How your work will be judged", "The Situation"),
                 situation=slide_range(titles, "You are the staff accountant", "The Data You Will Use"),
                 data=slide_range(titles, "The worksheets", "Requirements"), watch=slide_range(titles, "Watch out"),
                 r1=slide_range(titles, "Frame the question", "Map the data"), r2=slide_range(titles, "Map the data", "Test the data"),
                 r3=slide_range(titles, "Test the data", "Reconcile"), r4=slide_range(titles, "Reconcile", "Find what"),
                 r5=slide_range(titles, "Find what"), r6=slide_range(titles, "Write the data readiness memo"),
                 before=slide_range(titles, "Before you submit"), ahead=slide_range(titles, "From readiness"))
    r5 = n1.r5(d, claim)
    r4 = n1.r4(d, claim)
    # the product line's revenue and cost accounts are its own; its inventory account is shared with other groups
    _, revenue, cogs, inventory = n1.accounts(d)
    claim(all(d.one(f"SELECT COUNT(DISTINCT ItemGroup) FROM Item WHERE {col} = ?", a["id"]) == 1
              for col, a in (("RevenueAccountID", revenue), ("COGSAccountID", cogs))),
          "the Furniture revenue and COGS accounts belong to Furniture items only")
    claim(d.one("SELECT COUNT(DISTINCT ItemGroup) FROM Item WHERE InventoryAccountID = ?", inventory["id"]) > 1,
          "the Furniture inventory account is shared with other item groups")
    return dict(**labels(d), rows=rows, n_sheets=len(sheets), first_post=first_post, last_post=last_post, last_invoice=last_invoice,
                last_ship=last_ship, late_rows=sum(n for _, n in late), jan_invoices=jan, feb_invoices=feb, slides=len(titles), slide=slide,
                n_req=n_req, m3=r5["m3"], m4=r5["m4"], drop=(r5["m3"] - r5["m4"]) * 100, naive_q4=r5["naive_q4"], close=r5["close"],
                q3_lines=r4["q3"]["lines"], q4_lines=r4["q4"]["lines"])


# --- Requirement 1: frame the question -------------------------------------------------------------------------------------

@context("case1.g1")
def g1(d, claim):
    chapter1 = CHAPTER1.read_text(encoding="utf-8")
    claim(all(st[0] in chapter1 for st in STAGES), "Chapter 1 names the six stages of the workflow")
    claim("calculate gross margin by quarter" in chapter1.replace("\n", " "),
          "Chapter 1's fourth stage begins with the margin by quarter, which Requirement 5 computes (the stage is begun here)")
    n1 = notes_module()
    r5 = n1.r5(d, claim)
    claim(r5["m4"] < r5["m3"], "the Furniture margin falls from the first quarter to the second (the premise of the controller's question)")
    stages = [dict(n=i, name=name, status=status, by=by, kind=kind, short=short)
              for i, (name, status, by, kind, short) in enumerate(STAGES, 1)]
    return dict(**labels(d), stages=stages, drop=(r5["m3"] - r5["m4"]) * 100, m3=r5["m3"], m4=r5["m4"])


# --- Requirement 2: map the data -------------------------------------------------------------------------------------------

@context("case1.g2")
def g2(d, claim):
    have = schema(d, claim, CASE_SCHEMA)
    n1 = notes_module()
    cols = {c: letter(have, "Item", c) for c in ("ItemID", "ItemGroup", "InventoryAccountID", "RevenueAccountID", "COGSAccountID")}
    ids, revenue, cogs, inventory = n1.accounts(d)
    claim(ids[0] == 1 and ids[2] == 1 and ids[4] == 1, "the Furniture items share one revenue, one COGS and one inventory account")
    claim(revenue["id"] != revenue["number"] and cogs["id"] != cogs["number"], "AccountID is not the account number for the Furniture accounts")
    memo = d.q("SELECT AccountID, AccountNumber, AccountName FROM Account WHERE AccountSubType = 'Contra Revenue' "
               "AND AccountID IN (SELECT AccountID FROM GLEntry WHERE SourceDocumentType = 'CreditMemo')")
    claim(len(memo) == 1, "credit memos debit one contra-revenue account")
    memo = dict(zip(("id", "number", "name"), memo[0]))
    # the trace reaches the product line: every posting of a return carries the key of its line
    claim(d.one("SELECT COUNT(*) FROM GLEntry g LEFT JOIN CreditMemoLine l ON l.CreditMemoLineID = g.SourceLineID WHERE g.AccountID = ? "
                "AND g.SourceDocumentType = 'CreditMemo' AND (l.CreditMemoLineID IS NULL OR g.Debit <> l.LineTotal)", memo["id"]) == 0,
          f"every CreditMemo posting to {memo['number']} carries its credit memo line's key and amount")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g LEFT JOIN SalesReturnLine l ON l.SalesReturnLineID = g.SourceLineID WHERE g.AccountID = ? "
                "AND g.SourceDocumentType = 'SalesReturn' AND (l.SalesReturnLineID IS NULL OR g.Credit <> l.ExtendedStandardCost)", cogs["id"]) == 0,
          f"every SalesReturn posting to {cogs['number']} carries its return line's key and standard cost")
    quarters = {}
    for n in (3, 4):
        a, b = n1.quarter(d.C, n)
        quarters[f"q{n}"] = dict(memo_returns(d, a, b), cogs_rows=d.one(
            "SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'SalesReturn' AND PostingDate BETWEEN ? AND ?", cogs["id"], a, b))
        claim(0 < quarters[f"q{n}"]["furniture"] < quarters[f"q{n}"]["posted"], f"Furniture is part, not all, of the quarter's postings to {memo['number']}")
    claim(d.one("SELECT MAX(AccountID) FROM Account") < d.one("SELECT MIN(AccountNumber) FROM Account"),
          "every AccountID is smaller than every account number, so a filter on an account number in the AccountID column finds nothing")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g LEFT JOIN SalesInvoiceLine l ON l.SalesInvoiceLineID = g.SourceLineID WHERE g.AccountID = ? "
                "AND g.SourceDocumentType = 'SalesInvoice' AND (l.SalesInvoiceLineID IS NULL OR l.SalesInvoiceID <> g.SourceDocumentID)", revenue["id"]) == 0,
          f"every SalesInvoice posting to {revenue['number']} names its invoice and its invoice line")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g LEFT JOIN ShipmentLine l ON l.ShipmentLineID = g.SourceLineID WHERE g.AccountID = ? "
                "AND g.SourceDocumentType = 'Shipment' AND (l.ShipmentLineID IS NULL OR l.ShipmentID <> g.SourceDocumentID)", cogs["id"]) == 0,
          f"every Shipment posting to {cogs['number']} names its shipment and its shipment line")
    joins = [n1.cardinality(d, "SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID"),
             n1.cardinality(d, "Item", "ItemID", "SalesInvoiceLine", "ItemID"),
             n1.cardinality(d, "Shipment", "ShipmentID", "ShipmentLine", "ShipmentID"),
             n1.cardinality(d, "Item", "ItemID", "ShipmentLine", "ItemID"),
             n1.cardinality(d, "Account", "AccountID", "GLEntry", "AccountID")]
    claim([j["lo"] for j in joins] == [1, 0, 1, 0, 0],
          "every invoice and every shipment has at least one line, while an item or an account may have none (one to one-or-many, and one to zero-or-many)")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ABS(LineTotal - Quantity * UnitPrice * (1 - Discount)) > 0.011") == 0,
          "an invoice line's LineTotal is its quantity times its price less its discount, so discounts are inside the line totals")
    unposted = d.one("SELECT COUNT(*) FROM Account a WHERE NOT EXISTS (SELECT 1 FROM GLEntry g WHERE g.AccountID = a.AccountID)")
    claim(unposted > 0, "some accounts of the chart have no ledger rows (Account to GLEntry is zero or many)")
    unsold = d.one("SELECT COUNT(*) FROM Item t WHERE NOT EXISTS (SELECT 1 FROM SalesInvoiceLine l WHERE l.ItemID = t.ItemID)")
    claim(unsold > 0, "some items were never invoiced (Item to SalesInvoiceLine is zero or many)")
    furniture_sold = d.one("SELECT COUNT(DISTINCT l.ItemID) FROM SalesInvoiceLine l JOIN Item t ON t.ItemID = l.ItemID WHERE t.ItemGroup = ?", GROUP)
    return dict(**labels(d), cols=cols, memo=memo, quarters=quarters, unposted=unposted, unsold=unsold, furniture_sold=furniture_sold,
                account_rows=d.one("SELECT COUNT(*) FROM Account"))


# --- Requirement 3: test the data ------------------------------------------------------------------------------------------

@context("case1.g3")
def g3(d, claim):
    have = schema(d, claim, CASE_SCHEMA)
    n1 = notes_module()
    cols = dict(order_in_shipment=letter(have, "Shipment", "SalesOrderID"), date_in_shipment=letter(have, "Shipment", "ShipmentDate"),
                order_in_invoice=letter(have, "SalesInvoice", "SalesOrderID"), date_in_invoice=letter(have, "SalesInvoice", "InvoiceDate"),
                next_free=letter({"SalesInvoice": have["SalesInvoice"] + ["_"]}, "SalesInvoice", "_"),
                tracking=letter(have, "Shipment", "TrackingNumber"))
    claim(len(have["SalesInvoice"]) == 12 and cols["next_free"] == "M", "SalesInvoice has twelve columns, so the first empty column is M, as Tutorial 2.1 says")
    first_post, last_post = d.q("SELECT MIN(PostingDate), MAX(PostingDate) FROM GLEntry")[0]
    last_invoice = d.one("SELECT MAX(InvoiceDate) FROM SalesInvoice")
    periods = d.q("SELECT FiscalPeriod, COUNT(*) FROM GLEntry WHERE FiscalYear = ? AND FiscalPeriod >= 7 GROUP BY 1 ORDER BY 1", d.C)
    claim(len(periods) == 6, "the ledger has rows in each of the last six fiscal periods of the current year")
    q3avg, q4avg = sum(n for p, n in periods if p <= 9) / 3, sum(n for p, n in periods if p >= 10) / 3
    claim(abs(q4avg - q3avg) < 0.15 * q3avg, "the ledger's monthly row counts of Q4 are close to those of Q3 (Q4 is not a partial quarter)")
    late = d.q("SELECT FiscalPeriod, COUNT(*) FROM GLEntry WHERE FiscalYear = ? GROUP BY 1 ORDER BY 1", d.N)
    late_kinds = [r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE FiscalYear = ?", d.N)]
    claim(late_kinds == ["DisbursementPayment"], f"the ledger rows of fiscal {d.N} are all DisbursementPayment rows")
    claim(len(late) <= 2 and d.one("SELECT COUNT(*) FROM GLEntry WHERE FiscalYear = ?", d.N) < 0.05 * q4avg,
          f"fiscal {d.N} of the ledger is a short tail of a few hundred rows, far below a normal quarter")
    claim(d.one("SELECT MAX(ShipmentDate) FROM Shipment") == last_invoice, "the last shipment is dated the same day as the last invoice")
    nine = []
    for number, dated, shipped, lines, posted in n1.before_shipment(d):
        nine.append(dict(number=number, dated=dated, shipped=shipped, lines=lines, posted=posted, furniture=lines > 0,
                         moved=posted is not None and posted[:4] != dated[:4]))
    furniture = [r for r in nine if r["furniture"]]
    window = (n1.quarter(d.C, 3)[0], n1.quarter(d.C, 4)[1])
    claim(not any(window[0] <= x <= window[1] for r in furniture for x in (r["dated"], r["shipped"], r["posted"])),
          "no invoice dated before its shipment that holds Furniture lines is dated, shipped or posted in Q3 or Q4 of the current year")
    claim(len(nine) > len(furniture) > 0, "some, not all, of the invoices dated before their shipment hold Furniture lines")
    # the other Tutorial 2.1 findings, for the two quarters
    other = {}
    for n in (3, 4):
        a, b = n1.quarter(d.C, n)
        tr = d.q("SELECT COUNT(DISTINCT s.ShipmentID), COUNT(*), ROUND(COALESCE(SUM(sl.ExtendedStandardCost), 0), 2) FROM ShipmentLine sl "
                 "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN Item t ON t.ItemID = sl.ItemID WHERE t.ItemGroup = ? "
                 "AND s.ShipmentDate BETWEEN ? AND ? AND (s.TrackingNumber IS NULL OR TRIM(s.TrackingNumber) = '')", GROUP, a, b)[0]
        stale = d.one("SELECT COUNT(DISTINCT s.ShipmentID) FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                      "JOIN Item t ON t.ItemID = sl.ItemID WHERE t.ItemGroup = ? AND s.ShipmentDate BETWEEN ? AND ? "
                      "AND s.Status = 'In Transit' AND s.DeliveryDate < ?", GROUP, a, b, last_invoice)
        total = d.one("SELECT COUNT(DISTINCT s.ShipmentID) FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                      "JOIN Item t ON t.ItemID = sl.ItemID WHERE t.ItemGroup = ? AND s.ShipmentDate BETWEEN ? AND ?", GROUP, a, b)
        other[f"q{n}"] = dict(shipments=total, blank=tr[0], blank_lines=tr[1], blank_cost=tr[2], stale=stale)
    # a shipment's cost is posted on its ShipmentDate whatever its tracking number or status says
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN Shipment s ON s.ShipmentID = g.SourceDocumentID WHERE g.SourceDocumentType = 'Shipment' "
                "AND g.AccountID = ? AND g.PostingDate <> s.ShipmentDate", n1.accounts(d)[2]["id"]) == 0,
          "every Shipment posting to the Furniture COGS account is dated the shipment date")
    pairs = d.one("SELECT COUNT(*) FROM (SELECT CustomerName FROM Customer GROUP BY 1 HAVING COUNT(*) > 1)")
    claim(pairs > 0, "some customers share a name")
    blank = d.q("SELECT ItemGroup, COUNT(*) FROM Item WHERE ListPrice IS NULL GROUP BY 1 ORDER BY 1")
    claim(GROUP not in [g for g, _ in blank], "no Furniture item has a blank list price")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NULL AND SupplyMode <> 'Purchased'") == 0, "every item with a blank list price is purchased")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item t ON t.ItemID = l.ItemID WHERE t.ListPrice IS NULL") == 0,
          "no invoice line is for an item with a blank list price (the blank list prices belong to items the company buys)")
    jan, feb = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", f"{d.F}-01-01", f"{d.F}-01-31"), \
        d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", f"{d.F}-02-01", f"{d.F}-02-29")
    return dict(**labels(d), cols=cols, first_post=first_post, last_post=last_post, last_invoice=last_invoice, periods=periods,
                late_rows=sum(n for _, n in late), late_types=and_join(late_kinds), nine=nine, n_nine=len(nine), n_furniture=len(furniture),
                moved=[r for r in furniture if r["moved"]], other=other, pairs=pairs, customers=d.one("SELECT COUNT(*) FROM Customer"),
                blank_items=sum(n for _, n in blank), blank_groups=and_join(g for g, _ in blank), jan_invoices=jan, feb_invoices=feb)


# --- Requirement 4: reconcile ----------------------------------------------------------------------------------------------

@context("case1.g4")
def g4(d, claim):
    have = schema(d, claim, CASE_SCHEMA)
    n1 = notes_module()
    cols = dict(line_invoice=letter(have, "SalesInvoiceLine", "SalesInvoiceID"), line_item=letter(have, "SalesInvoiceLine", "ItemID"),
                line_total=letter(have, "SalesInvoiceLine", "LineTotal"), inv_id=letter(have, "SalesInvoice", "SalesInvoiceID"),
                inv_date=letter(have, "SalesInvoice", "InvoiceDate"), item_id=letter(have, "Item", "ItemID"),
                item_group=letter(have, "Item", "ItemGroup"), sl_ship=letter(have, "ShipmentLine", "ShipmentID"),
                sl_item=letter(have, "ShipmentLine", "ItemID"), sl_cost=letter(have, "ShipmentLine", "ExtendedStandardCost"),
                ship_id=letter(have, "Shipment", "ShipmentID"), ship_date=letter(have, "Shipment", "ShipmentDate"),
                h1=col_letter(len(have["SalesInvoiceLine"]) + 1), h2=col_letter(len(have["SalesInvoiceLine"]) + 2),
                h3=col_letter(len(have["SalesInvoiceLine"]) + 3), k1=col_letter(len(have["ShipmentLine"]) + 1),
                k2=col_letter(len(have["ShipmentLine"]) + 2), k3=col_letter(len(have["ShipmentLine"]) + 3))
    revenue, cogs, qs = n1.quarters(d)
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID WHERE i.InvoiceDate IS NULL OR l.ItemID IS NULL") == 0,
          "every invoice line has an invoice date and an item (the two lookups find a match for each line)")
    claim(d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE s.ShipmentDate IS NULL") == 0,
          "every shipment line has a shipment date through its shipment")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN SalesInvoice i ON i.SalesInvoiceID = g.SourceDocumentID WHERE g.SourceDocumentType = 'SalesInvoice' "
                "AND g.AccountID = ? AND g.PostingDate BETWEEN ? AND ? AND i.InvoiceDate NOT BETWEEN ? AND ?", revenue["id"], *n1.quarter(d.C, 3), *n1.quarter(d.C, 3)) == 0
          and d.one("SELECT COUNT(*) FROM GLEntry g JOIN SalesInvoice i ON i.SalesInvoiceID = g.SourceDocumentID WHERE g.SourceDocumentType = 'SalesInvoice' "
                    "AND g.AccountID = ? AND g.PostingDate BETWEEN ? AND ? AND i.InvoiceDate NOT BETWEEN ? AND ?", revenue["id"], *n1.quarter(d.C, 4), *n1.quarter(d.C, 4)) == 0,
          "the sales invoices posted to the Furniture revenue account in a quarter are the invoices dated in it (posting date and invoice date fall in the same quarter)")
    recon = []
    for n in (3, 4):
        a, b = n1.quarter(d.C, n)
        q = qs[n]
        inv_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID JOIN Item t ON t.ItemID = l.ItemID "
                          "WHERE t.ItemGroup = ? AND i.InvoiceDate BETWEEN ? AND ?", GROUP, a, b)
        ship_lines = d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN Item t ON t.ItemID = sl.ItemID "
                           "WHERE t.ItemGroup = ? AND s.ShipmentDate BETWEEN ? AND ?", GROUP, a, b)
        recon.append(dict(label=f"{d.C} Q{n}", invoice_lines=inv_lines, shipment_lines=ship_lines, lines=q["lines"],
                          ledger_revenue=q["rev"]["SalesInvoice"], revenue_gap=round(q["rev"]["SalesInvoice"] - q["lines"], 2),
                          shipped=q["shipped"], ledger_cogs=q["cogs"]["Shipment"], cogs_gap=round(q["cogs"]["Shipment"] - q["shipped"], 2),
                          returns=-q["cogs"]["SalesReturn"], cogs_net=q["cogs"]["Shipment"] + q["cogs"]["SalesReturn"],
                          uninvoiced=not_invoiced(d, a, b), shifted=invoiced_shipped_elsewhere(d, a, b)))
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID JOIN Item t ON t.ItemID = l.ItemID "
                "JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                "WHERE t.ItemGroup = ? AND i.InvoiceDate BETWEEN ? AND ? AND s.ShipmentDate > i.InvoiceDate", GROUP, n1.quarter(d.C, 3)[0], n1.quarter(d.C, 4)[1]) == 0,
          "no Furniture line invoiced in the two quarters shipped after its invoice date, so the lines shipped outside a quarter shipped in an earlier one")
    claim(recon[0]["uninvoiced"]["lines"] == 0 and recon[1]["uninvoiced"]["lines"] > 0,
          "every Furniture shipment line of Q3 is invoiced, and some of Q4's, shipped late in the quarter, are not")
    last_month = f"{d.C}-12-01"
    claim(d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN Item t ON t.ItemID = sl.ItemID "
                "WHERE t.ItemGroup = ? AND s.ShipmentDate BETWEEN ? AND ? AND s.ShipmentDate < ? AND NOT EXISTS "
                "(SELECT 1 FROM SalesInvoiceLine il WHERE il.ShipmentLineID = sl.ShipmentLineID)", GROUP, *n1.quarter(d.C, 4), last_month) == 0,
          "the Furniture shipment lines of the fourth quarter with no invoice line all shipped in its last month")
    claim(all(r["uninvoiced"]["lines"] == 0 or r["uninvoiced"]["cost"] < 0.01 * r["shipped"] for r in recon),
          "the shipment lines with no invoice line are under one percent of the quarter's shipped cost")
    sources = d.q("SELECT SourceDocumentType, COUNT(*), SUM(Debit > 0), SUM(Credit > 0) FROM GLEntry WHERE AccountID = ? GROUP BY 1 ORDER BY 2 DESC", cogs["id"])
    claim([s[0] for s in sources] == ["Shipment", "SalesReturn", "JournalEntry"], "the source document types of the Furniture COGS account are Shipment, SalesReturn and JournalEntry")
    claim(sources[2][1] == d.C - d.F + 1, "the Furniture COGS account has one journal entry row for each fiscal year, its year-end close")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (?, ?) AND SourceDocumentType = 'JournalEntry' AND VoucherNumber NOT IN "
                "(SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%')", revenue["id"], cogs["id"]) == 0,
          "the only journal entries to the Furniture accounts are year-end closes")
    return dict(**labels(d), cols=cols, recon=recon, sources=[dict(source=s, rows=n, debits=dr, credits=cr) for s, n, dr, cr in sources],
                lines_rows=d.one("SELECT COUNT(*) FROM SalesInvoiceLine"), ship_rows=d.one("SELECT COUNT(*) FROM ShipmentLine"))


# --- Requirement 5: find what could mislead --------------------------------------------------------------------------------

@context("case1.g5")
def g5(d, claim):
    have = schema(d, claim, CASE_SCHEMA)
    n1 = notes_module()
    revenue, cogs, qs = n1.quarters(d)
    cols = dict(account=letter(have, "GLEntry", "AccountID"), source=letter(have, "GLEntry", "SourceDocumentType"), voucher=letter(have, "GLEntry", "VoucherNumber"),
                debit=letter(have, "GLEntry", "Debit"), credit=letter(have, "GLEntry", "Credit"), year=letter(have, "GLEntry", "FiscalYear"),
                period=letter(have, "GLEntry", "FiscalPeriod"), desc=letter(have, "GLEntry", "Description"),
                line_qty=letter(have, "SalesInvoiceLine", "Quantity"), line_item=letter(have, "SalesInvoiceLine", "ItemID"),
                item_id=letter(have, "Item", "ItemID"), item_cost=letter(have, "Item", "StandardCost"),
                new_col=col_letter(len(have["SalesInvoiceLine"]) + 4))
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (?, ?) AND NOT (FiscalYear = CAST(SUBSTR(PostingDate, 1, 4) AS INTEGER) "
                "AND FiscalPeriod = CAST(SUBSTR(PostingDate, 6, 2) AS INTEGER))", revenue["id"], cogs["id"]) == 0,
          "a ledger row's fiscal year and period are the year and month of its posting date, so FiscalPeriod 7 to 9 is Q3 and 10 to 12 is Q4")
    ledger = {}
    for account, key in ((revenue, "revenue"), (cogs, "cogs")):
        for n in (3, 4):
            a, b = n1.quarter(d.C, n)
            ledger[f"{key}{n}"] = ledger_by_source(d, account["id"], a, b)
    r5 = n1.r5(d, claim)
    close = r5["close"]
    rows = d.q("SELECT g.Description, a.AccountNumber, g.Debit, g.Credit FROM GLEntry g JOIN Account a USING (AccountID) "
               "WHERE g.VoucherNumber = ? AND g.AccountID IN (?, ?) ORDER BY a.AccountNumber", close, revenue["id"], cogs["id"])
    claim(len(rows) == 2, "the close has one row for each Furniture account")
    closes = d.q("SELECT EntryNumber, PostingDate, EntryType FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%' ORDER BY PostingDate, EntryNumber")
    claim(all(p.endswith("-12-31") for _, p, _ in closes), "every year-end close is posted on December 31")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber = ?", close) > 2, "the close posts to many accounts, not only the Furniture ones")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry' AND AccountID IN (?, ?) AND PostingDate BETWEEN ? AND ?",
                revenue["id"], cogs["id"], *n1.quarter(d.C, 3)) == 0, "no journal entry posts to the Furniture accounts in Q3")
    year_rev = d.one("SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND VoucherNumber <> ?", revenue["id"], d.C, close)
    year_cogs = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND VoucherNumber <> ?", cogs["id"], d.C, close)
    claim(abs(year_rev - r5["close_debit"]) < 0.005 and abs(year_cogs - r5["close_credit"]) < 0.005,
          "the close debits revenue and credits cost of goods sold by the whole year's balances before it")
    # the corrected measure's neighbours: net of the revenue side of returns, and with the unbilled shipments of Q4
    a3, b3, a4, b4 = *n1.quarter(d.C, 3), *n1.quarter(d.C, 4)
    ret3, ret4 = memo_returns(d, a3, b3)["furniture"], memo_returns(d, a4, b4)["furniture"]
    rev3, cogs3 = qs[3]["rev"]["SalesInvoice"], qs[3]["cogs"]["Shipment"] + qs[3]["cogs"]["SalesReturn"]
    rev4, cogs4 = qs[4]["rev"]["SalesInvoice"], qs[4]["cogs"]["Shipment"] + qs[4]["cogs"]["SalesReturn"]
    net3, net4 = margin(rev3 - ret3, cogs3), margin(rev4 - ret4, cogs4)
    claim(net4 < net3, "the margin also falls when the Furniture credit memo lines are taken off revenue")
    un = not_invoiced(d, a4, b4)
    billed4 = margin(rev4 + un["at_order_price"], cogs4)
    claim(billed4 < margin(rev3, cogs3), "the margin of Q4 stays below Q3's even if the unbilled Furniture shipments were invoiced at their order prices")
    # the invoice-line cost at standard against the posted shipment cost net of cost returns: two definitions, not an error
    std3, std4 = qs[3]["std"], qs[4]["std"]
    claim(abs(std3 - cogs3) > 1 and abs(std4 - cogs4) > 1, "the invoice lines at standard cost differ from the posted shipment cost net of returns")
    # the same trap at the earlier year-ends: each close is in the fourth quarter of its year
    claim(len(closes) == 2 * (d.C - d.F + 1) and all(c[2].startswith("Year-End Close") for c in closes), "each fiscal year has two year-end close entries")
    return dict(**labels(d), cols=cols, ledger=ledger, close_rows=[dict(desc=r[0], number=r[1], debit=r[2], credit=r[3]) for r in rows],
                closes=[dict(number=e, posted=p, type=t) for e, p, t in closes], n_closes=len(closes), net3=net3, net4=net4, ret3=ret3, ret4=ret4,
                billed4=billed4, unbilled=un, rev_change=(rev4 / rev3 - 1) * 100, cogs_change=(cogs4 / cogs3 - 1) * 100, drop=(r5["m3"] - r5["m4"]) * 100, year_rev=year_rev, year_cogs=year_cogs, rev3=rev3, cogs3=cogs3, rev_net3=rev3 - ret3, rev_net4=rev4 - ret4, cogs4=cogs4, std_drop=(r5["s3"] - r5["s4"]) * 100,
                std3=std3, std4=std4, std_gap3=std3 - cogs3, std_gap4=std4 - cogs4)


# --- Requirement 6: the memo ------------------------------------------------------------------------------------------------

@context("case1.g6")
def g6(d, claim):
    schema(d, claim, CASE_SCHEMA)
    n1 = notes_module()
    out = {}
    for n in (3, 4):
        a, b = n1.quarter(d.C, n)
        r = d.q("SELECT SUM(l.Quantity), SUM(l.LineTotal) / SUM(l.Quantity), SUM(l.Quantity * t.StandardCost) / SUM(l.Quantity), "
                "SUM(l.LineTotal) / SUM(l.Quantity * l.BaseListPrice), SUM(l.PromotionID IS NOT NULL), "
                "SUM(l.Quantity * l.UnitPrice * l.Discount) FROM SalesInvoiceLine l JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID "
                "JOIN Item t ON t.ItemID = l.ItemID WHERE t.ItemGroup = ? AND i.InvoiceDate BETWEEN ? AND ?", GROUP, a, b)[0]
        out[f"q{n}"] = dict(units=r[0], price=r[1], cost_per_unit=r[2], price_to_list=r[3], promo_lines=r[4], promo_discount=r[5])
    q3, q4 = out["q3"], out["q4"]
    claim(abs(q4["units"] / q3["units"] - 1) < 0.02, "the units invoiced are about the same in the two quarters (within two percent)")
    claim(abs(q4["cost_per_unit"] / q3["cost_per_unit"] - 1) < 0.02, "the standard cost per unit invoiced is about the same in the two quarters (within two percent)")
    claim(q4["price"] < q3["price"] and q4["price_to_list"] < q3["price_to_list"], "the average price per unit and its ratio to list price are lower in Q4")
    claim(q4["promo_discount"] > 2 * q3["promo_discount"], "the promotional discounts on Furniture lines more than double from Q3 to Q4")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g LEFT JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountID IS NULL") == 0,
          "every AccountID in the ledger exists in the chart of accounts (no orphaned account reference)")
    # every posting to the two Furniture accounts names a source document that exists (not true of the whole ledger)
    _, revenue, cogs, _ = n1.accounts(d)
    tables = {"SalesInvoice": "SalesInvoiceID", "Shipment": "ShipmentID", "SalesReturn": "SalesReturnID", "JournalEntry": "JournalEntryID"}
    kinds = [r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID IN (?, ?)", revenue["id"], cogs["id"])]
    claim(set(kinds) <= set(tables), "the Furniture accounts' postings come from sales invoices, shipments, returns and journal entries")
    claim(all(d.one(f"SELECT COUNT(*) FROM GLEntry g LEFT JOIN {t} x ON x.{k} = g.SourceDocumentID WHERE g.AccountID IN (?, ?) "
                    f"AND g.SourceDocumentType = ? AND x.{k} IS NULL", revenue["id"], cogs["id"], t) == 0 for t, k in tables.items()),
          "every posting to the two Furniture accounts names a source document that exists")
    have = {t: [r[1] for r in d.q(f"PRAGMA table_info({t})")] for t in ("SalesInvoiceLine", "Item", "ShipmentLine")}
    fields = dict(line=[c for c in ("ItemID", "Quantity", "BaseListPrice", "UnitPrice", "Discount", "PromotionID", "LineTotal") if c in have["SalesInvoiceLine"]],
                  item=[c for c in ("ItemCode", "StandardCost", "ListPrice") if c in have["Item"]])
    claim(len(fields["line"]) == 7 and len(fields["item"]) == 3, "the invoice lines and the item master hold the product-level fields the memo names")
    r5 = n1.r5(d, claim)
    r4 = n1.r4(d, claim)
    return dict(**labels(d), q3=q3, q4=q4, units_change=(q4["units"] / q3["units"] - 1) * 100, price_change=(q4["price"] / q3["price"] - 1) * 100,
                cost_change=(q4["cost_per_unit"] / q3["cost_per_unit"] - 1) * 100, drop=(r5["m3"] - r5["m4"]) * 100, m3=r5["m3"], m4=r5["m4"], naive_q4=r5["naive_q4"],
                s3=r5["s3"], s4=r5["s4"], lines3=r4["q3"]["lines"], lines4=r4["q4"]["lines"], close=r5["close"], fields=fields)
