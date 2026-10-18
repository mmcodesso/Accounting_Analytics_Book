"""Chapter 2's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 2's tutorials and exercises are data quality tests that students run in their working copy of the workbook, so the
contexts do two jobs:

- they supply the values a model answer can quote (the counts a filter or a helper column returns, the rows of a finding), and
- they check, with claim(), every table and column the guide names and every statement about the data that another dataset
  could falsify, so a roll or a schema change flags the wording instead of leaving it stale.

Keys: ch02.chapter (the chapter note), ch02.t1 and ch02.t2 (the two tutorials), ch02.ex1 to ch02.ex5 (the exercises) and
ch02.ex6g (the extra values of Exercise 2.6; the registered note ch02.ex6 supplies the rest).
"""

from __future__ import annotations

import math
import re
from datetime import date
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, rows_of, schema

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "02-understanding-data"
DECK = REPO / "slides" / "chapter-02" / "index.qmd"
EXCEL_ROWS = 1_048_576                      # rows in one Excel worksheet
TUTORIAL_TYPES = ["SalesInvoice", "Shipment", "PurchaseInvoice", "GoodsReceipt", "MaterialIssue", "PayrollPayment",
                  "JournalEntry", "WorkOrderClose"]               # Tutorial 2.2, Step 8
EXERCISE_TYPES = ["SalesInvoice", "Shipment", "PurchaseInvoice", "JournalEntry", "PayrollPayment", "WorkOrderClose"]  # Exercise 2.2 (3)
BLANK_TRACKING = "(TrackingNumber IS NULL OR TRIM(TrackingNumber) = '')"


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


def pearson(a: list[float], b: list[float]) -> float:
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return num / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def median(values: list[float]) -> float:
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


# --- the chapter note ----------------------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "Shipment": ["ShipmentNumber", "TrackingNumber", "Status", "DeliveryDate", "FreightCost"],
    "SalesInvoice": ["InvoiceNumber", "InvoiceDate", "SalesOrderID"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "SourceDocumentType", "SourceDocumentID", "FiscalYear", "FiscalPeriod"],
    "Account": ["AccountID", "AccountType"],
    "Customer": ["CustomerName"],
    "Item": ["ListPrice", "ItemGroup"],
}


@context("ch02.chapter")
def chapter(d, claim):
    schema(d, claim, CHAPTER_SCHEMA)
    sizes = {t: d.one(f"SELECT COUNT(*) FROM {t}") for (t,) in d.q("SELECT name FROM sqlite_master WHERE type = 'table' "
                                                                  "AND name NOT LIKE 'sqlite_%'")}
    largest = max(sizes, key=sizes.get)
    claim(largest == "GLEntry", "GLEntry is the largest worksheet, so it is the one that opens and filters slowly")
    gl_rows = sizes["GLEntry"]
    claim(0.5 < (gl_rows + 1) / EXCEL_ROWS < 1, "GLEntry fills more than half of one Excel worksheet")
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    mcq = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    return dict(
        n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(),
        n_questions=len(re.findall(r"^\*\*\d+\.\*\*", mcq, re.M)),
        rows=rows_of(d, ["Shipment", "Customer", "SalesOrder", "SalesInvoice", "SalesInvoiceLine", "Item", "GLEntry",
                         "PurchaseInvoice", "DisbursementPayment", "WorkOrder", "WorkOrderOperation", "Budget", "BudgetLine"]),
        gl_share=(gl_rows + 1) / EXCEL_ROWS)


# --- Tutorial 2.1: the O2C and Item tables -------------------------------------------------------------------------------

T1_SCHEMA = {
    "SalesOrder": ["SalesOrderID", "CustomerID", "OrderDate", "Status"],
    "Shipment": ["ShipmentID", "ShipmentNumber", "SalesOrderID", "ShipmentDate", "ShippedBy", "TrackingNumber", "Status",
                 "DeliveryDate", "FreightCost"],
    "ShipmentLine": ["ShipmentID", "QuantityShipped"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SalesOrderID"],
    "SalesInvoiceLine": ["SalesInvoiceID", "ItemID"],
    "Customer": ["CustomerID", "CustomerName", "City", "State", "Region", "CustomerSegment", "IsActive", "Address", "Email", "ContactName"],
    "Item": ["ItemID", "ItemGroup", "ItemType", "ListPrice"],
}


@context("ch02.t1")
def t1(d, claim):
    schema(d, claim, T1_SCHEMA)
    ship_rows = d.one("SELECT COUNT(*) FROM Shipment")

    # Step 2: blank tracking numbers
    blank = d.one(f"SELECT COUNT(*) FROM Shipment WHERE {BLANK_TRACKING}")
    carriers = d.q(f"SELECT ShippedBy, COUNT(*), SUM({BLANK_TRACKING}) FROM Shipment GROUP BY 1 ORDER BY 1")
    claim(len(carriers) > 1 and all(r[2] > 0 for r in carriers), "blank tracking numbers occur with every carrier")
    claim("Private Fleet" in [r[0] for r in carriers], "the company's own fleet is one of the carriers")
    claim(0 < blank / ship_rows < 0.1, "nearly every shipment carries a tracking number")
    blank_years = d.q(f"SELECT substr(ShipmentDate, 1, 4), SUM({BLANK_TRACKING}) FROM Shipment GROUP BY 1 ORDER BY 1")
    claim([int(y) for y, _ in blank_years] == d.years and all(n > 0 for _, n in blank_years),
          "blank tracking numbers occur in every fiscal year")

    # Step 3: shipments still In Transit with a delivery date
    statuses = [r[0] for r in d.q("SELECT Status FROM Shipment GROUP BY 1 ORDER BY 1")]
    claim(statuses == ["Delivered", "In Transit"], "Shipment.Status is Delivered or In Transit")
    in_transit = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit'")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate IS NULL") == 0,
          "every shipment marked In Transit has a delivery date")
    last_day = d.one("SELECT MAX(DeliveryDate) FROM Shipment")
    stale = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", last_day)
    claim(stale / in_transit > 0.99, "nearly every In Transit shipment has a delivery date before the last date in the data")
    transit_years = d.q("SELECT substr(ShipmentDate, 1, 4), COUNT(*) FROM Shipment WHERE Status = 'In Transit' GROUP BY 1 ORDER BY 1")
    claim([int(y) for y, _ in transit_years] == d.years, "shipments marked In Transit come from every fiscal year")
    claim(0 < in_transit / ship_rows < 0.15, "a small share of the shipments is marked In Transit")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE DeliveryDate < ShipmentDate") == 0, "no shipment is delivered before it ships")

    # Step 4: customers sharing a name
    pairs = []
    for (name,) in d.q("SELECT CustomerName FROM Customer GROUP BY 1 HAVING COUNT(*) > 1 ORDER BY 1"):
        members = [dict(id=r[0], city=r[1], state=r[2], region=r[3], segment=r[4], active=bool(r[5]), terms=r[6], orders=r[7])
                   for r in d.q("SELECT c.CustomerID, c.City, c.State, c.Region, c.CustomerSegment, c.IsActive, c.PaymentTerms, "
                                "(SELECT COUNT(*) FROM SalesOrder o WHERE o.CustomerID = c.CustomerID) FROM Customer c "
                                "WHERE c.CustomerName = ? ORDER BY c.CustomerID", name)]
        pairs.append(dict(name=name, members=members))
    claim(len(pairs) >= 2 and all(len(p["members"]) == 2 for p in pairs), "two or more names are shared, each by exactly two customers")
    claim(all(p["members"][0]["city"] != p["members"][1]["city"] for p in pairs), "the two customers of each shared name are in different cities")
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Customer GROUP BY Address HAVING COUNT(*) > 1)") == 0
          and d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Customer GROUP BY Email HAVING COUNT(*) > 1)") == 0,
          "no two customers share an address or an e-mail address")
    claim(any(p["members"][0]["segment"] != p["members"][1]["segment"] for p in pairs)
          and any(p["members"][0]["segment"] == p["members"][1]["segment"] for p in pairs),
          "one same-name pair differs in segment and region and another shares both, so the second needs more than the first columns")
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1 AND COUNT(DISTINCT ContactName) < COUNT(*))") == 0,
          "the two customers of each shared name have different contacts")
    shared = [p["name"] for p in pairs if p["members"][0]["segment"] == p["members"][1]["segment"]
              and p["members"][0]["region"] == p["members"][1]["region"]]
    claim(len(shared) == 1, "exactly one same-name pair shares its region and its segment")
    claim(any(not m["active"] and m["orders"] == 0 for p in pairs for m in p["members"]),
          "one customer of a shared name is inactive and has no orders")

    # Step 5: freight outliers, read against the size of the shipment
    freight = d.q("SELECT s.FreightCost, COALESCE(SUM(l.QuantityShipped), 0) FROM Shipment s LEFT JOIN ShipmentLine l "
                  "ON l.ShipmentID = s.ShipmentID GROUP BY s.ShipmentID")
    costs, qty = [r[0] for r in freight], [r[1] for r in freight]
    average = sum(costs) / len(costs)
    top = d.q("SELECT s.ShipmentNumber, s.FreightCost, s.ShippedBy, COALESCE((SELECT SUM(QuantityShipped) FROM ShipmentLine l "
              "WHERE l.ShipmentID = s.ShipmentID), 0) FROM Shipment s ORDER BY s.FreightCost DESC, s.ShipmentID LIMIT 5")
    corr = pearson(costs, qty)
    claim(top[0][1] / average > 3, "the largest freight cost is several times the average")
    claim(corr > 0.8, "freight cost rises with the quantity shipped")
    claim(all(sum(1 for q in qty if q < t[3]) / len(qty) > 0.95 for t in top),
          "the five highest freight costs are on shipments larger than 95 of every 100 shipments")
    above3 = sum(1 for c in costs if c > 3 * average)
    claim(above3 / len(costs) < 0.1, "fewer than one shipment in ten has a freight cost above three times the average")

    # Steps 6-7: invoices dated before the first shipment on their order
    before = d.q("SELECT i.InvoiceNumber, i.InvoiceDate, s.m FROM SalesInvoice i JOIN (SELECT SalesOrderID, MIN(ShipmentDate) m "
                 "FROM Shipment GROUP BY 1) s ON s.SalesOrderID = i.SalesOrderID WHERE i.InvoiceDate < s.m ORDER BY i.InvoiceNumber")
    claim(0 < len(before) <= 12, "a handful of invoices are dated before the first shipment on their order")
    claim(all(r[1] < r[2] for r in before), "each flagged invoice date is earlier than the order's first shipment")
    no_ship = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE SalesOrderID NOT IN (SELECT SalesOrderID FROM Shipment)")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice i JOIN SalesInvoiceLine l USING (SalesInvoiceID) JOIN Item t USING (ItemID) "
                "WHERE i.SalesOrderID NOT IN (SELECT SalesOrderID FROM Shipment) AND t.ItemGroup <> 'Services'") == 0,
          "every invoice with no shipment on its order bills only Services items (design services)")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice i JOIN SalesInvoiceLine l USING (SalesInvoiceID) JOIN Item t USING (ItemID) "
                "WHERE t.ItemGroup = 'Services' AND i.SalesOrderID IN (SELECT SalesOrderID FROM Shipment)") == 0,
          "no invoice for a Services item has a shipment on its order")
    same_day = d.one("SELECT COUNT(*) FROM SalesInvoice i JOIN (SELECT SalesOrderID, MIN(ShipmentDate) m FROM Shipment GROUP BY 1) s "
                     "ON s.SalesOrderID = i.SalesOrderID WHERE i.InvoiceDate = s.m")
    claim(same_day > 0, "some invoices are dated the day of the first shipment, so the test uses a strict comparison")

    # Step 8: blank list prices
    groups = d.q("SELECT ItemGroup, COUNT(*), SUM(ListPrice IS NULL) FROM Item GROUP BY 1 ORDER BY 1")
    blank_groups = [dict(group=g, items=n, blank=b) for g, n, b in groups if b]
    claim([g["group"] for g in blank_groups] == ["Capex", "Packaging", "Raw Materials", "Services"],
          "blank list prices are in the Capex, Packaging, Raw Materials and Services groups, as Step 8 says")
    claim(all(b == 0 for g, n, b in groups if g in ("Furniture", "Lighting", "Textiles", "Accessories")),
          "every finished good has a list price")
    design = d.one("SELECT COUNT(*) FROM Item WHERE ItemGroup = 'Services' AND ListPrice IS NOT NULL")
    claim(design > 0 and d.one("SELECT COUNT(*) FROM Item WHERE ItemGroup = 'Services' AND ListPrice IS NOT NULL AND "
                               "UnitOfMeasure = 'Hour'") == design, "the Services items that have a list price are priced by the hour")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item t USING (ItemID) WHERE t.ListPrice IS NULL") == 0,
          "no invoice line bills an item with a blank list price")

    return dict(
        ship_rows=ship_rows, blank=blank, blank_share=blank / ship_rows, carriers=carriers,
        blank_years=[(int(y), n) for y, n in blank_years], harder=shared[0], in_transit=in_transit, stale=stale, last_day=last_day,
        transit_years=[(int(y), n) for y, n in transit_years], pairs=pairs, n_pairs=len(pairs),
        average=average, top=top, top_ratio=top[0][1] / average, corr=corr, above3=above3,
        before=[dict(number=r[0], date=r[1], first=r[2]) for r in before], n_before=len(before), no_ship=no_ship,
        blank_groups=blank_groups, blank_items=sum(g["blank"] for g in blank_groups),
        n_items=sum(n for _, n, _ in groups), sellable=sum(n - b for _, n, b in groups), design=design,
        sizes=and_join(f"{g['group']} ({g['blank']})" for g in blank_groups))


# --- Tutorial 2.2: the Accounting Core ------------------------------------------------------------------------------------

T2_SCHEMA = {
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType",
                "SourceDocumentID", "FiscalYear", "FiscalPeriod"],
    "SalesInvoice": ["SalesInvoiceID", "GrandTotal"],
}
DOCUMENTS = [("SalesInvoice", "SalesInvoiceID"), ("Shipment", "ShipmentID"), ("PurchaseInvoice", "PurchaseInvoiceID"),
             ("GoodsReceipt", "GoodsReceiptID"), ("MaterialIssue", "MaterialIssueID"), ("PayrollPayment", "PayrollPaymentID"),
             ("JournalEntry", "JournalEntryID"), ("WorkOrderClose", "WorkOrderCloseID"), ("DisbursementPayment", "DisbursementID"),
             ("CashReceipt", "CashReceiptID"), ("ProductionCompletion", "ProductionCompletionID"), ("CreditMemo", "CreditMemoID")]


@context("ch02.t2")
def t2(d, claim):
    schema(d, claim, T2_SCHEMA)

    # Steps 1-2: the chart of accounts
    types = d.q("SELECT AccountType, COUNT(*) FROM Account GROUP BY 1 ORDER BY 1")
    claim([t for t, _ in types] == ["Asset", "Equity", "Expense", "Liability", "Revenue"],
          "the chart of accounts has accounts of the five classes Step 2 names")
    n_accounts = d.one("SELECT COUNT(*) FROM Account")

    # Steps 3-4: volume and the aggregate balance
    gl_rows, debit, credit = d.q("SELECT COUNT(*), SUM(Debit), SUM(Credit) FROM GLEntry")[0]
    difference = round(debit - credit, 2)
    claim(difference == 0, "total debits equal total credits in the ledger, to the cent")
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM GLEntry GROUP BY SourceDocumentType, SourceDocumentID "
                "HAVING ABS(SUM(Debit) - SUM(Credit)) > 0.005)") == 0, "every document's ledger rows balance")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE Debit IS NULL OR Credit IS NULL OR Debit < 0 OR Credit < 0") == 0,
          "no ledger amount is blank or negative")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE Debit <> 0 AND Credit <> 0") == 0, "no ledger row has both a debit and a credit")

    # Step 5: references to the chart of accounts
    orphans = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID NOT IN (SELECT AccountID FROM Account)")
    claim(orphans == 0, "every AccountID in the ledger exists in the chart of accounts")
    used = d.one("SELECT COUNT(DISTINCT AccountID) FROM GLEntry")
    claim(used < n_accounts, "some accounts of the chart have no ledger rows, so the distinct list is shorter than the chart")

    # Step 6: the periods
    periods = d.q("SELECT FiscalYear, FiscalPeriod, COUNT(*) FROM GLEntry GROUP BY 1, 2 ORDER BY 1, 2")
    typical = median([n for _, _, n in periods])
    low = [(y, p, n) for y, p, n in periods if n < 0.5 * typical]
    claim(low == [periods[0]] + periods[-2:], "the periods with under half the typical volume are the first period and the last two")
    ordinary = [n for y, p, n in periods if (y, p, n) not in low]
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE CAST(substr(PostingDate, 6, 2) AS INTEGER) <> FiscalPeriod OR "
                "CAST(substr(PostingDate, 1, 4) AS INTEGER) <> FiscalYear") == 0, "a fiscal period is the calendar month of the posting date")
    first_day, last_day = d.one("SELECT MIN(PostingDate) FROM GLEntry"), d.one("SELECT MAX(PostingDate) FROM GLEntry")
    claim(first_day == f"{d.F}-01-01", "the ledger begins on the first day of the first fiscal year")
    last_year = d.one("SELECT MAX(FiscalYear) FROM GLEntry")
    last_types = [r[0] for r in d.q("SELECT SourceDocumentType FROM GLEntry WHERE FiscalYear = ? GROUP BY 1", last_year)]
    claim(last_types == ["DisbursementPayment"], "the latest fiscal year holds only supplier payments")
    claim(last_year == d.N, "the ledger runs into the fiscal year after the last year of sales")

    # Step 7: rows with no amount
    zero = d.q("SELECT SourceDocumentType, COUNT(*), COUNT(DISTINCT VoucherNumber), MIN(PostingDate), MAX(PostingDate) FROM GLEntry "
               "WHERE Debit = 0 AND Credit = 0 GROUP BY 1")
    claim(len(zero) == 1 and zero[0][0] == "PayrollPayment", "the rows with no debit and no credit all come from PayrollPayment")
    claim(zero[0][3] == zero[0][4], "the rows with no amount are all posted on one date")
    zero_accounts = and_join(f"{n} {name}" for n, name in d.q(
        "SELECT a.AccountNumber, a.AccountName FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.Debit = 0 AND g.Credit = 0 "
        "GROUP BY 1, 2 ORDER BY 1"))

    # Step 8: the source types
    source = d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry GROUP BY 1 ORDER BY 2 DESC, 1")
    names = [s for s, _ in source]
    claim(all(t in names for t in TUTORIAL_TYPES), "the ledger holds the eight source types Step 8 names")
    claim(all(t in names for t in EXERCISE_TYPES), "the ledger holds the six source types of Exercise 2.2")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType IS NULL OR SourceDocumentType = ''") == 0,
          "every ledger row names a source type")
    every_year = d.q("SELECT FiscalYear, COUNT(DISTINCT SourceDocumentType) FROM GLEntry GROUP BY 1 ORDER BY 1")
    claim(all(n == len(names) for y, n in every_year if y <= d.C), "every source type appears in each fiscal year under review")

    # the limit of that test: documents the ledger never received
    unposted = {}
    for table, key in DOCUMENTS:
        n = d.one(f"SELECT COUNT(*) FROM {table} WHERE {key} NOT IN (SELECT SourceDocumentID FROM GLEntry "
                  f"WHERE SourceDocumentType = '{table}')")
        if n:
            unposted[table] = n
    claim(list(unposted) == ["MaterialIssue"], "the only documents without ledger rows are material issue headers")
    claim(d.one("SELECT COUNT(*) FROM MaterialIssue WHERE MaterialIssueID NOT IN (SELECT SourceDocumentID FROM GLEntry WHERE "
                "SourceDocumentType = 'MaterialIssue') AND MaterialIssueID IN (SELECT MaterialIssueID FROM MaterialIssueLine)") == 0,
          "the material issue headers with no ledger rows have no lines either")
    claim({r[0] for r in d.q("SELECT Status FROM MaterialIssue WHERE MaterialIssueID NOT IN (SELECT MaterialIssueID FROM MaterialIssueLine)")}
          == {"Issued"}, "the material issue headers with no lines all carry the status Issued, not a cancelled status")
    invoices = d.one("SELECT COUNT(*) FROM SalesInvoice")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice s LEFT JOIN (SELECT SourceDocumentID id, ROUND(SUM(Debit), 2) x FROM GLEntry "
                "WHERE SourceDocumentType = 'SalesInvoice' AND AccountID = (SELECT AccountID FROM Account WHERE AccountNumber = 1020) "
                "GROUP BY 1) g ON g.id = s.SalesInvoiceID WHERE g.x IS NULL OR ABS(g.x - s.GrandTotal) > 0.005") == 0,
          "every sales invoice reconciles to the receivable that its ledger rows debit")

    return dict(
        types=types, n_accounts=n_accounts, n_types=len(types), gl_rows=gl_rows, debit=debit, credit=credit, difference=difference,
        used=used, orphans=orphans, periods=len(periods), typical=typical, low=low, ordinary_min=min(ordinary),
        ordinary_max=max(ordinary), first_day=first_day, last_day=last_day, last_year=last_year, first_year=periods[0][0],
        zero=zero[0], zero_accounts=zero_accounts, n_source=len(names), largest=source[0], smallest=source[-1],
        tutorial_types=and_join(TUTORIAL_TYPES), exercise_types=and_join(EXERCISE_TYPES), unposted=unposted,
        invoices=invoices, gl_share=(gl_rows + 1) / EXCEL_ROWS)


# --- Exercise 2.1: revenue data in the O2C tables ----------------------------------------------------------------------------

EX1_SCHEMA = {
    "SalesOrder": ["SalesOrderID", "OrderNumber", "OrderDate", "CustomerID", "Status", "OrderTotal", "Notes"],
    "SalesOrderLine": ["SalesOrderID", "Quantity", "UnitPrice", "Discount", "LineTotal"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SalesOrderID", "CustomerID", "SubTotal", "Status", "PaymentDate"],
    "CreditMemo": ["OriginalSalesInvoiceID"],
    "CashReceiptApplication": ["SalesInvoiceID"],
    "SalesInvoiceLine": ["SalesInvoiceID", "ShipmentLineID", "Quantity", "UnitPrice", "Discount", "LineTotal", "PriceListLineID",
                         "PromotionID", "PriceOverrideApprovalID", "PricingMethod"],
    "Customer": ["CustomerID", "CustomerName", "IsActive"],
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ListPrice"],
    "GLEntry": ["PostingDate", "SourceDocumentType", "SourceDocumentID"],
}


@context("ch02.ex1")
def ex1(d, claim):
    schema(d, claim, EX1_SCHEMA)
    # (1) required fields and fields that are blank by design
    required = {c: d.one(f"SELECT COUNT(*) FROM SalesOrder WHERE {c} IS NULL OR TRIM(CAST({c} AS TEXT)) = ''")
                for c in ("OrderDate", "CustomerID", "Status")}
    claim(all(n == 0 for n in required.values()), "no SalesOrder row is blank in OrderDate, CustomerID or Status")
    orders = d.one("SELECT COUNT(*) FROM SalesOrder")
    notes_blank = d.one("SELECT COUNT(*) FROM SalesOrder WHERE Notes IS NULL")
    claim(notes_blank / orders > 0.9, "the notes of an order are blank on almost every order")
    line_blank = d.q("SELECT COUNT(*), SUM(ShipmentLineID IS NULL), SUM(PromotionID IS NULL), SUM(PriceOverrideApprovalID IS NULL) "
                     "FROM SalesInvoiceLine")[0]
    lines = line_blank[0]
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE PricingMethod IS NULL OR Quantity IS NULL OR UnitPrice IS NULL "
                "OR Discount IS NULL OR LineTotal IS NULL") == 0, "the pricing columns of an invoice line are never blank")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ShipmentLineID IS NULL AND PricingMethod <> 'Base List'") == 0,
          "an invoice line with no shipment line is a Base List (design service) line")
    paid_blank = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE PaymentDate IS NULL")
    submitted = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE Status = 'Submitted'")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice WHERE Status = 'Submitted' AND PaymentDate IS NOT NULL") == 0,
          "an invoice with the status Submitted has no payment date")
    credit_settled = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE Status = 'Settled' AND PaymentDate IS NULL")
    partial_blank = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE Status = 'Partially Settled' AND PaymentDate IS NULL")
    claim(paid_blank == submitted + credit_settled + partial_blank, "an invoice with no payment date is Submitted, settled by credit memo or partially settled")
    claim(credit_settled > 0 and d.one("SELECT COUNT(*) FROM SalesInvoice WHERE Status = 'Settled' AND PaymentDate IS NULL AND "
                                       "(SalesInvoiceID NOT IN (SELECT OriginalSalesInvoiceID FROM CreditMemo) OR SalesInvoiceID IN "
                                       "(SELECT SalesInvoiceID FROM CashReceiptApplication))") == 0,
          "a settled invoice with no payment date was settled by a credit memo and received no cash")
    names = d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Item GROUP BY ItemName HAVING COUNT(*) > 1)")
    shared_items = d.one("SELECT COUNT(*) FROM Item WHERE ItemName IN (SELECT ItemName FROM Item GROUP BY 1 HAVING COUNT(*) > 1)")
    claim(names > 0, "some item names are shared by more than one item")

    # (2) LineTotal against its columns
    max_diff = d.one("SELECT MAX(ABS(LineTotal - Quantity * UnitPrice * (1 - Discount))) FROM SalesInvoiceLine")
    over_cent = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE ABS(LineTotal - Quantity * UnitPrice * (1 - Discount)) > 0.01")
    claim(over_cent == 0, "LineTotal is within one cent of Quantity x UnitPrice x (1 - Discount) on every invoice line")
    claim(max_diff <= 0.0050001, "the largest difference is half a cent, the rounding of LineTotal")
    rates = [r[0] for r in d.q("SELECT Discount FROM SalesInvoiceLine GROUP BY 1 ORDER BY 1")]
    claim(rates[0] == 0 and all(0 < r < 1 for r in rates[1:]) and len(rates) > 2,
          "Discount is a rate between 0 and 1, with a few nonzero values")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE (Discount > 0) <> (PromotionID IS NOT NULL)") == 0,
          "a line has a discount exactly when it carries a promotion")
    methods = d.q("SELECT PricingMethod, COUNT(*) FROM SalesInvoiceLine GROUP BY 1 ORDER BY 2 DESC")
    claim(sorted(m for m, _ in methods) == ["Approved Override", "Base List", "Customer Price List", "Segment Price List"],
          "PricingMethod has the four values of the chapter's data notes")
    override = d.q("SELECT COUNT(*), SUM(LineTotal) FROM SalesInvoiceLine WHERE PricingMethod = 'Approved Override'")[0]
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE (PricingMethod = 'Approved Override') <> "
                "(PriceOverrideApprovalID IS NOT NULL)") == 0, "an invoice line has an override approval exactly when it is priced by approved override")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice s JOIN (SELECT SalesInvoiceID, SUM(LineTotal) t FROM SalesInvoiceLine GROUP BY 1) l "
                "USING (SalesInvoiceID) WHERE ABS(s.SubTotal - l.t) > 0.005") == 0, "every invoice's SubTotal equals its lines")
    claim(d.one("SELECT COUNT(*) FROM SalesOrder s JOIN (SELECT SalesOrderID, SUM(LineTotal) t FROM SalesOrderLine GROUP BY 1) l "
                "USING (SalesOrderID) WHERE ABS(s.OrderTotal - l.t) > 0.005") == 0, "every order's OrderTotal equals its lines")

    # (3) orphans
    orphans = d.one("SELECT COUNT(*) FROM SalesOrder WHERE CustomerID NOT IN (SELECT CustomerID FROM Customer)")
    claim(orphans == 0, "every CustomerID in SalesOrder exists in Customer")
    unused = d.q("SELECT IsActive FROM Customer WHERE CustomerID NOT IN (SELECT CustomerID FROM SalesOrder)")
    claim(len(unused) > 0 and all(a == 0 for (a,) in unused), "the customers with no orders are all inactive")

    # dates and numbers that disagree (judgment findings)
    before_order = d.q("SELECT i.InvoiceNumber, i.InvoiceDate, o.OrderDate FROM SalesInvoice i JOIN SalesOrder o USING (SalesOrderID) "
                       "WHERE i.InvoiceDate < o.OrderDate ORDER BY 1")
    prefix = d.q("SELECT InvoiceNumber, InvoiceDate, (SELECT MIN(g.PostingDate) FROM GLEntry g WHERE g.SourceDocumentType = 'SalesInvoice' "
                 "AND g.SourceDocumentID = i.SalesInvoiceID) FROM SalesInvoice i WHERE CAST(substr(InvoiceNumber, 4, 4) AS INTEGER) "
                 "<> CAST(substr(InvoiceDate, 1, 4) AS INTEGER) ORDER BY 1")
    claim(0 < len(before_order) <= 5, "a few invoices are dated before their order")
    first_invoice_day = d.one("SELECT MIN(InvoiceDate) FROM SalesInvoice")
    claim(all(0 <= (date.fromisoformat(r[1]) - date.fromisoformat(first_invoice_day)).days <= 7 for r in before_order),
          "the invoices dated before their order are among the first invoices of the data")
    claim(0 < len(prefix) <= 10, "a few invoice numbers carry the prefix of a year other than the invoice date's")
    claim(all(int(n[3:7]) == int(p[:4]) for n, _, p in prefix), "the prefix of those invoice numbers is the year in which the ledger posted them")
    claim(all(int(n[3:7]) == int(i[:4]) + 1 for n, i, _ in prefix), "each of those invoices is dated in the year before its number's prefix")
    # SalesOrderLine, which requirement (1) names: the same tests, all clean
    sol = d.q("SELECT COUNT(*), SUM(SalesOrderID IS NULL OR ItemID IS NULL OR Quantity IS NULL OR UnitPrice IS NULL OR Discount IS NULL "
              "OR LineTotal IS NULL), SUM(SalesOrderID NOT IN (SELECT SalesOrderID FROM SalesOrder)), SUM(ItemID NOT IN (SELECT ItemID FROM Item)), "
              "SUM(ABS(LineTotal - Quantity * UnitPrice * (1 - Discount)) > 0.01) FROM SalesOrderLine")[0]
    claim(sol[1:] == (0, 0, 0, 0), "every SalesOrderLine row has its order, item, quantity, price, discount and line total, its order and item "
          "exist, and its LineTotal agrees with its parts within a cent")
    # the scenario's year: revenue by invoice date against the ledger's posting year
    C = d.C
    c_invoices, c_subtotal = d.q("SELECT COUNT(*), SUM(SubTotal) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?",
                                 f"{C}-01-01", f"{C}-12-31")[0]
    c_posted = d.one("SELECT SUM(g.Credit - g.Debit) FROM GLEntry g JOIN Account a USING (AccountID) WHERE g.SourceDocumentType = 'SalesInvoice' "
                     "AND g.FiscalYear = ? AND a.AccountType = 'Revenue' AND CAST(a.AccountNumber AS TEXT) <> '4050'", C)
    into_c = [p for p in prefix if p[2][:4] == str(C)]
    claim(into_c and all(p[2] == f"{C}-01-01" for p in into_c), "the invoices dated in the year before and posted in the latest year post on January 1")
    into_c_total = sum(d.one("SELECT SubTotal FROM SalesInvoice WHERE InvoiceNumber = ?", n) for n, _, _ in into_c)
    claim(abs(c_posted - c_subtotal - into_c_total) < 0.005,
          "the latest year's revenue postings, freight aside, exceed its invoices by invoice date by exactly the invoices dated in the year "
          "before and posted in it")
    return dict(
        orders=orders, required=required, notes_blank=notes_blank, lines=lines, no_shipment_lines=line_blank[1],
        promo_blank=line_blank[2], override_blank=line_blank[3], paid_blank=paid_blank, submitted=submitted,
        credit_settled=credit_settled, partial_blank=partial_blank, names=names, shared_items=shared_items,
        max_diff=max_diff, over_cent=over_cent, rates=rates, methods=methods, override=dict(n=override[0], total=override[1]),
        orphans=orphans, unused=len(unused), before_order=[dict(number=n, date=a, order=b) for n, a, b in before_order],
        prefix=[dict(number=n, date=a, posted=p) for n, a, p in prefix],
        sol_rows=sol[0], c_invoices=c_invoices, c_subtotal=c_subtotal, c_posted=c_posted, n_into_c=len(into_c), into_c_total=into_c_total,
        rows=rows_of(d, ["SalesOrder", "SalesOrderLine", "SalesInvoice", "SalesInvoiceLine", "Customer", "Item"]))


# --- Exercise 2.2 has no context of its own: its guide uses ch02.t2 -----------------------------------------------------------


# --- Exercise 2.3: product cost data ---------------------------------------------------------------------------------------

EX3_SCHEMA = {
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "StandardCost", "ListPrice", "UnitOfMeasure", "SupplyMode",
             "RoutingID", "LifecycleStatus", "IsActive"],
    "SalesInvoiceLine": ["ItemID"],
    "WorkOrder": ["WorkOrderID", "WorkOrderNumber", "ItemID", "ReleasedDate", "Status"],
    "WorkOrderOperation": ["WorkOrderOperationID", "WorkOrderID"],
    "WorkOrderClose": ["WorkOrderID", "TotalVarianceAmount", "CloseDate"],
    "LaborTimeEntry": ["WorkOrderID", "WorkOrderOperationID", "RegularHours", "OvertimeHours"],
}


@context("ch02.ex3")
def ex3(d, claim):
    schema(d, claim, EX3_SCHEMA)
    # (1) zero, blank or odd standard costs
    claim(d.one("SELECT COUNT(*) FROM Item WHERE StandardCost IS NULL") == 0, "no item has a blank StandardCost")
    zero = d.q("SELECT ItemCode, ItemName, ItemGroup, ListPrice, UnitOfMeasure FROM Item WHERE StandardCost = 0 ORDER BY ItemCode")
    claim(len(zero) > 0 and all(r[2] == "Services" and r[3] is not None and r[4] == "Hour" for r in zero),
          "the items with a StandardCost of 0 are Services items priced by the hour")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE StandardCost < 0") == 0, "no item has a negative StandardCost")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE ListPrice IS NOT NULL AND StandardCost > 0 AND ListPrice < StandardCost") == 0,
          "no item with a list price is priced below its standard cost")
    by_group = d.q("SELECT ItemGroup, COUNT(*), MIN(StandardCost), MAX(StandardCost) FROM Item WHERE StandardCost > 0 GROUP BY 1 ORDER BY 4 DESC")
    monthly = d.q("SELECT ItemCode, ItemName, StandardCost, UnitOfMeasure FROM Item WHERE ItemGroup = 'Services' AND "
                  "UnitOfMeasure <> 'Hour' ORDER BY StandardCost DESC")
    claim(len(monthly) > 0 and all(r[3] == "Month" for r in monthly), "the Services items with a cost and no list price are monthly services")
    capex = d.q("SELECT MIN(StandardCost), MAX(StandardCost) FROM Item WHERE ItemGroup = 'Capex'")[0]
    claim(capex[0] > 1000, "equipment items carry costs in the thousands")
    finished_max = d.one("SELECT MAX(StandardCost) FROM Item WHERE ItemType = 'Finished Good'")
    claim(finished_max < capex[0] and finished_max < min(r[2] for r in monthly), "every finished good costs less than the monthly services and the equipment")

    # (2) shared names
    shared = d.q("SELECT ItemName, COUNT(*), COUNT(DISTINCT ItemCode), COUNT(DISTINCT StandardCost), MIN(StandardCost), MAX(StandardCost), "
                 "MIN(ItemGroup), COUNT(DISTINCT LifecycleStatus) FROM Item GROUP BY 1 HAVING COUNT(*) > 1 ORDER BY MAX(StandardCost) / MIN(StandardCost) DESC")
    claim(len(shared) > 0 and all(n == c == s for _, n, c, s, *_ in shared),
          "the items that share a name have different codes and different standard costs")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE ItemName IN (SELECT ItemName FROM Item GROUP BY 1 HAVING COUNT(*) > 1) "
                "AND ItemGroup IN ('Furniture', 'Lighting')") == 0, "no Furniture or Lighting item shares its name")
    widest = shared[0]
    sold = d.one("SELECT COUNT(DISTINCT t.ItemName) FROM Item t JOIN SalesInvoiceLine l USING (ItemID) WHERE t.ItemName IN "
                 "(SELECT ItemName FROM Item GROUP BY 1 HAVING COUNT(*) > 1)")
    made = d.one("SELECT COUNT(DISTINCT t.ItemName) FROM Item t JOIN WorkOrder w USING (ItemID) WHERE t.ItemName IN "
                 "(SELECT ItemName FROM Item GROUP BY 1 HAVING COUNT(*) > 1)")
    claim(sold > 0, "some shared item names appear on invoice lines")
    claim(made == 0, "no item with a shared name is made on a work order")
    lifecycle = d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Item GROUP BY ItemName HAVING COUNT(*) > 1 AND COUNT(DISTINCT LifecycleStatus) > 1)")
    claim(lifecycle > 0, "some items that share a name differ in lifecycle status, so one may be the successor of the other")
    example = d.q("SELECT ItemCode, StandardCost, LifecycleStatus FROM Item WHERE ItemName = ? ORDER BY ItemCode", widest[0])

    # (3) work orders with no routing operation
    work_orders = d.one("SELECT COUNT(*) FROM WorkOrder")
    operations = d.one("SELECT COUNT(*) FROM WorkOrderOperation")
    claim(d.one("SELECT COUNT(*) FROM WorkOrderOperation WHERE WorkOrderID NOT IN (SELECT WorkOrderID FROM WorkOrder)") == 0,
          "every operation row names a work order that exists")
    spread = d.q("SELECT n, COUNT(*) FROM (SELECT w.WorkOrderID, COUNT(o.WorkOrderOperationID) n FROM WorkOrder w LEFT JOIN "
                 "WorkOrderOperation o USING (WorkOrderID) GROUP BY 1) GROUP BY 1 ORDER BY 1")
    none = d.q("SELECT w.WorkOrderID, w.WorkOrderNumber, w.Status, w.ReleasedDate, i.ItemCode FROM WorkOrder w JOIN Item i USING (ItemID) "
               "WHERE w.WorkOrderID NOT IN (SELECT WorkOrderID FROM WorkOrderOperation) ORDER BY 1")
    claim({n for n, _ in spread if n} == {3, 4}, "every other work order has three or four operations")
    claim(len(none) > 0, "some work orders have no routing operation")
    claim(all(r[2] == "Closed" for r in none), "the work orders with no operation are all Closed")
    firsts = [r[0] for r in d.q("SELECT MIN(WorkOrderID) FROM WorkOrder GROUP BY substr(WorkOrderNumber, 4, 4) ORDER BY 1")]
    claim([r[0] for r in none] == firsts, "the work orders with no operation are the first work order numbered in each year")
    ids = ",".join(str(r[0]) for r in none)
    labor = d.q(f"SELECT COUNT(*), SUM(RegularHours + OvertimeHours), SUM(WorkOrderOperationID IS NULL), SUM(WorkOrderOperationID IN "
                f"(SELECT WorkOrderOperationID FROM WorkOrderOperation)) FROM LaborTimeEntry WHERE WorkOrderID IN ({ids})")[0]
    claim(labor[0] > 0, "the work orders with no operation have labor time recorded")
    claim((labor[3] or 0) == 0, "none of their labor time entries points to an operation that exists")
    closes = d.q(f"SELECT COUNT(*), SUM(TotalVarianceAmount) FROM WorkOrderClose WHERE WorkOrderID IN ({ids})")[0]
    claim(closes[0] == len(none), "each work order with no operation has a close that posted a variance")
    unrouted = d.q("SELECT COUNT(*), SUM(RoutingID IS NULL), SUM(ItemID IN (SELECT ItemID FROM WorkOrder)) FROM Item WHERE SupplyMode = 'Manufactured'")[0]
    claim(unrouted[1] > 0 and d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured' AND RoutingID IS NULL AND ItemID IN "
                                    "(SELECT ItemID FROM WorkOrder)") == 0, "the manufactured items with no routing were never put on a work order")
    return dict(
        zero=zero, n_zero=len(zero), by_group=by_group, monthly=monthly, capex=capex,
        n_names=len(shared), n_shared_items=sum(r[1] for r in shared), widest=dict(name=widest[0], low=widest[4], high=widest[5],
        ratio=widest[5] / widest[4], codes=example), sold=sold, made=made, lifecycle=lifecycle,
        work_orders=work_orders, operations=operations, spread=spread, no_ops=[dict(number=r[1], status=r[2], released=r[3], item=r[4]) for r in none],
        n_none=len(none), labor=dict(n=labor[0], hours=labor[1]), closes=dict(n=closes[0], total=closes[1]),
        unrouted=dict(manufactured=unrouted[0], blank=unrouted[1], made=unrouted[2]))


# --- Exercise 2.4: budget data -----------------------------------------------------------------------------------------------

EX4_SCHEMA = {
    "Budget": ["BudgetID", "FiscalYear", "CostCenterID", "AccountID", "Month", "BudgetAmount"],
    "BudgetLine": ["BudgetLineID", "FiscalYear", "Month", "AccountID", "CostCenterID", "ItemID", "WarehouseID", "Quantity", "UnitAmount",
                   "BudgetAmount", "BudgetCategory"],
    "GLEntry": ["PostingDate", "AccountID", "CostCenterID", "Debit", "Credit", "VoucherNumber", "FiscalYear", "FiscalPeriod"],
    "Account": ["AccountNumber", "AccountName", "AccountType"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
}


@context("ch02.ex4")
def ex4(d, claim):
    schema(d, claim, EX4_SCHEMA)
    C = d.C
    closes = ",".join(f"'{c}'" for c in d.closes)
    claim(len(d.closes) > 0, "the ledger holds year-end close entries")

    # (1) what a row is, and whether the tables add
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM Budget GROUP BY FiscalYear, Month, CostCenterID, AccountID HAVING COUNT(*) > 1)") == 0,
          "Budget has one row for each fiscal year, month, cost center and account")
    claim(d.one("SELECT COUNT(*) FROM Budget WHERE CostCenterID IS NULL") == 0, "every Budget row has a cost center")
    claim(d.one("SELECT COUNT(*) FROM Budget WHERE Month NOT BETWEEN 1 AND 12 OR TypeOf(Month) <> 'integer'") == 0, "Budget.Month is a number from 1 to 12")
    years = d.q("SELECT FiscalYear, COUNT(*) FROM Budget GROUP BY 1 ORDER BY 1")
    claim([y for y, _ in years] == d.years + [d.N], "the budget covers the fiscal years under review and the next one")
    budget_accounts = d.q("SELECT a.AccountNumber, a.AccountType FROM Budget b JOIN Account a USING (AccountID) WHERE b.FiscalYear = ? "
                          "GROUP BY 1, 2 ORDER BY 1", C)
    claim({t for _, t in budget_accounts} == {"Revenue", "Expense"}, "Budget holds revenue and expense accounts only")
    rolled = d.q("SELECT b.FiscalYear, COUNT(*), SUM(ABS(b.BudgetAmount - COALESCE(l.s, 0)) < 0.01) FROM Budget b LEFT JOIN (SELECT FiscalYear, "
                 "Month, CostCenterID, AccountID, SUM(BudgetAmount) s FROM BudgetLine GROUP BY 1, 2, 3, 4) l USING (FiscalYear, Month, CostCenterID, "
                 "AccountID) GROUP BY 1 ORDER BY 1")
    claim(all(n == m for _, n, m in rolled), "every Budget row equals the sum of the BudgetLine rows with the same year, month, cost center and account")
    claim(d.one("SELECT COUNT(*) FROM BudgetLine WHERE BudgetCategory IN ('Revenue', 'COGS') AND ABS(Quantity * UnitAmount - BudgetAmount) > 0.02") == 0,
          "on the revenue and cost of goods sold lines, BudgetAmount is Quantity times UnitAmount")
    categories = d.q("SELECT BudgetCategory, COUNT(*), SUM(CostCenterID IS NULL) FROM BudgetLine GROUP BY 1 ORDER BY 1")
    claim({c for c, _, _ in categories} == {"Balance Sheet", "COGS", "Operating Expense", "Revenue"},
          "BudgetLine has revenue, cost of goods sold, operating expense and balance sheet lines")
    claim(d.one("SELECT COUNT(*) FROM BudgetLine WHERE BudgetCategory = 'Balance Sheet' AND CostCenterID IS NOT NULL") == 0,
          "no balance sheet budget line has a cost center")
    extra = d.q("SELECT a.AccountNumber, a.AccountName, COUNT(*), SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a USING (AccountID) "
                "WHERE b.FiscalYear = ? AND b.BudgetCategory = 'Operating Expense' AND b.CostCenterID IS NULL GROUP BY 1, 2 ORDER BY 1", C)
    budget_numbers = {n for n, _ in budget_accounts}
    claim(not ({n for n, *_ in extra} & budget_numbers), "the operating expense accounts without a cost center in BudgetLine are not in Budget")

    # (3) blank cost centers
    line_blank = d.q("SELECT COUNT(*), SUM(CostCenterID IS NULL) FROM BudgetLine")[0]
    line_split = {c: b for c, _, b in categories}
    gl_total, gl_blank = d.q("SELECT COUNT(*), SUM(CostCenterID IS NULL) FROM GLEntry")[0]
    by_type = d.q("SELECT a.AccountType, COUNT(*), SUM(g.CostCenterID IS NULL) FROM GLEntry g JOIN Account a USING (AccountID) GROUP BY 1 ORDER BY 1")
    claim(max(by_type, key=lambda r: r[2])[0] in ("Asset", "Liability"), "most ledger rows without a cost center are on balance sheet accounts")
    pl_rows, pl_blank = d.q(f"SELECT COUNT(*), SUM(g.CostCenterID IS NULL) FROM GLEntry g JOIN Account a USING (AccountID) WHERE a.AccountType = 'Expense' "
                            f"AND g.VoucherNumber NOT IN ({closes})")[0]
    close_blank = d.one(f"SELECT COUNT(*) FROM GLEntry g JOIN Account a USING (AccountID) WHERE a.AccountType = 'Expense' AND g.CostCenterID IS NULL "
                        f"AND g.VoucherNumber IN ({closes})")
    claim(close_blank > 0, "the year-end closes post expense rows with no cost center")
    year_total, year_blank, year_blank_amount, year_amount = d.q(
        f"SELECT COUNT(*), SUM(g.CostCenterID IS NULL), SUM(CASE WHEN g.CostCenterID IS NULL THEN g.Debit - g.Credit ELSE 0 END), "
        f"SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) WHERE a.AccountType = 'Expense' AND g.FiscalYear = ? "
        f"AND g.VoucherNumber NOT IN ({closes})", C)[0]
    claim(0 < year_blank / year_total < 0.02, "a small share of the expense rows of the latest year has no cost center")
    claim(0.05 < year_blank_amount / year_amount < 0.15, "the expense rows with no cost center are a larger share of the money than of the rows")
    actual_accounts = d.q(f"SELECT a.AccountNumber, a.AccountName FROM GLEntry g JOIN Account a USING (AccountID) WHERE a.AccountType = 'Expense' "
                          f"AND g.CostCenterID IS NULL AND g.FiscalYear = ? AND g.VoucherNumber NOT IN ({closes}) GROUP BY 1, 2 ORDER BY 1", C)
    left_over = {n for n, _ in actual_accounts} - {n for n, *_ in extra}
    claim(len(left_over) == 1, "the ledger's expense accounts with no cost center are those of the budget lines, plus one")
    other = left_over.pop()
    other_name = d.one("SELECT AccountName FROM Account WHERE AccountNumber = ?", other)
    other_cc = d.q("SELECT c.CostCenterName, SUM(b.BudgetAmount) FROM Budget b JOIN CostCenter c USING (CostCenterID) WHERE b.FiscalYear = ? "
                   "AND b.AccountID = (SELECT AccountID FROM Account WHERE AccountNumber = ?) GROUP BY 1", C, other)
    claim(len(other_cc) == 1, "Budget puts that one account in a single cost center")
    other_actual = d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = (SELECT AccountID FROM Account WHERE AccountNumber = ?) "
                         f"AND FiscalYear = ? AND CostCenterID IS NULL AND VoucherNumber NOT IN ({closes})", other, C)
    budget_blank_year = d.one("SELECT SUM(BudgetAmount) FROM BudgetLine WHERE FiscalYear = ? AND BudgetCategory = 'Operating Expense' AND CostCenterID IS NULL", C)
    claim(abs((year_blank_amount - other_actual) - budget_blank_year) / budget_blank_year < 0.02,
          "on those accounts the actual expense with no cost center is within two percent of the budget lines with none")

    # the report layout of (2): one cost center, accounts down, months across
    cc = d.q("SELECT CostCenterID, CostCenterName FROM CostCenter WHERE CostCenterName = 'Administration'")[0]
    cc_rows = d.one("SELECT COUNT(*) FROM Budget WHERE FiscalYear = ? AND CostCenterID = ?", C, cc[0])
    cc_accounts = d.one("SELECT COUNT(DISTINCT AccountID) FROM Budget WHERE FiscalYear = ? AND CostCenterID = ?", C, cc[0])
    claim(cc_rows == 12 * cc_accounts, "the cost center has one Budget row for each account and month")
    return dict(
        years=years, rolled=rolled, rolled_diff=sum(n - m for _, n, m in rolled), budget_rows=dict(years)[C], n_budget_accounts=len(budget_accounts),
        n_revenue=sum(1 for _, t in budget_accounts if t == "Revenue"), n_expense=sum(1 for _, t in budget_accounts if t == "Expense"),
        categories=categories, n_extra=len(extra), extra_rows=sum(r[2] for r in extra), extra_total=budget_blank_year,
        line_rows=line_blank[0], line_blank=line_blank[1], line_opex=line_split["Operating Expense"], line_bs=line_split["Balance Sheet"],
        gl_rows=gl_total, gl_blank=gl_blank, gl_blank_share=gl_blank / gl_total, by_type=by_type, pl_rows=pl_rows, pl_blank=pl_blank,
        close_blank=close_blank, year=C, year_rows=year_total, year_blank=year_blank, year_blank_amount=year_blank_amount,
        year_amount=year_amount, row_share=year_blank / year_total, money_share=year_blank_amount / year_amount,
        n_actual_accounts=len(actual_accounts), other=dict(number=other, name=other_name, center=other_cc[0][0], budget=other_cc[0][1], actual=other_actual),
        like=year_blank_amount - other_actual, cc=dict(id=cc[0], name=cc[1], rows=cc_rows, accounts=cc_accounts),
        year_closes=d.closes_of(C), all_closes=d.closes)


# --- Exercise 2.5: audit planning ------------------------------------------------------------------------------------------

EX5_SCHEMA = {
    "SalesOrder": ["OrderDate", "CustomerID", "Status"],
    "PurchaseRequisition": ["RequisitionID", "RequisitionNumber", "RequestDate", "ApprovedByEmployeeID", "ApprovedDate", "Status",
                            "Quantity", "EstimatedUnitCost"],
    "PurchaseOrder": ["PurchaseOrderID", "RequisitionID"],
}


@context("ch02.ex5")
def ex5(d, claim):
    schema(d, claim, EX5_SCHEMA)
    reqs = d.q("SELECT RequisitionID, RequisitionNumber, RequestDate, Status, Quantity * EstimatedUnitCost, ApprovedDate FROM PurchaseRequisition "
               "WHERE ApprovedByEmployeeID IS NULL ORDER BY RequisitionID")
    total = d.one("SELECT COUNT(*) FROM PurchaseRequisition")
    claim(len(reqs) > 0, "some purchase requisitions have no approver")
    claim(all(r[3] == "Converted to PO" for r in reqs), "every requisition with no approver was converted to a purchase order")
    claim(all(r[5] is None for r in reqs), "a requisition with no approver has no approval date either")
    claim(d.one("SELECT COUNT(*) FROM PurchaseOrder WHERE RequisitionID IN (SELECT RequisitionID FROM PurchaseRequisition "
                "WHERE ApprovedByEmployeeID IS NULL)") == len(reqs), "each of those requisitions has a purchase order")
    claim(d.one("SELECT COUNT(*) FROM Employee WHERE MaxApprovalAmount = 5000") > 0, "some roles have an approval limit of 5000")
    claim(all(4950 <= r[4] < 5000 for r in reqs), "every requisition with no approver is just under that limit")
    claim(all(r[2][5:] == "01-01" for r in reqs), "every requisition with no approver is dated January 1")
    claim(d.one("SELECT COUNT(*) FROM PurchaseRequisition WHERE ApprovedByEmployeeID IS NOT NULL AND Status NOT IN ('Approved', 'Converted to PO')") == 0,
          "an approved requisition has the status Approved or Converted to PO")
    statuses = d.q("SELECT Status, COUNT(*), SUM(ApprovedByEmployeeID IS NULL) FROM PurchaseRequisition GROUP BY 1 ORDER BY 2 DESC")
    return dict(
        reqs=[dict(number=r[1], date=r[2], value=r[4]) for r in reqs], n_reqs=len(reqs), total=total, statuses=statuses,
        low=min(r[4] for r in reqs), high=max(r[4] for r in reqs), threshold=5000,
        first=reqs[0][1], last=reqs[-1][1], year_first=reqs[0][2][:4], year_last=reqs[-1][2][:4])


# --- Exercise 2.6: the extra values (the registered note ch02.ex6 supplies the pairs) -------------------------------------------

EX6_SCHEMA = {
    "PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "SupplierID", "GrandTotal", "Status"],
    "DisbursementPayment": ["DisbursementID", "PaymentNumber", "PaymentDate", "SupplierID", "PurchaseInvoiceID", "Amount", "PaymentMethod",
                            "CheckNumber"],
}


@context("ch02.ex6g")
def ex6g(d, claim):
    schema(d, claim, EX6_SCHEMA)
    methods = d.q("SELECT PaymentMethod, COUNT(*), SUM(CheckNumber IS NOT NULL) FROM DisbursementPayment GROUP BY 1 ORDER BY 2 DESC")
    claim(all((c == n) if m == "Check" else (c == 0) for m, n, c in methods), "a payment has a check number exactly when its method is Check")
    claim(len(methods) == 3, "payments are made by check, ACH or wire transfer")
    no_check = sum(n for m, n, _ in methods if m != "Check")
    payments = d.one("SELECT COUNT(*) FROM DisbursementPayment")
    invoices = d.one("SELECT COUNT(*) FROM PurchaseInvoice")
    unpaid = d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE PurchaseInvoiceID NOT IN (SELECT PurchaseInvoiceID FROM DisbursementPayment)")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE PurchaseInvoiceID NOT IN (SELECT PurchaseInvoiceID FROM DisbursementPayment) "
                "AND Status <> 'Approved'") == 0, "an invoice with no payment is one whose status is still Approved")
    claim(d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PurchaseInvoiceID NOT IN (SELECT PurchaseInvoiceID FROM PurchaseInvoice)") == 0,
          "every payment names an invoice that exists")
    paid = "(SELECT PurchaseInvoiceID, SUM(Amount) s, COUNT(*) n FROM DisbursementPayment GROUP BY 1) p"
    raw = d.one(f"SELECT COUNT(*) FROM PurchaseInvoice i JOIN {paid} USING (PurchaseInvoiceID) WHERE p.s > i.GrandTotal")
    rounded = d.one(f"SELECT COUNT(*) FROM PurchaseInvoice i JOIN {paid} USING (PurchaseInvoiceID) WHERE ROUND(p.s, 2) > ROUND(i.GrandTotal, 2)")
    claim(rounded == 0, "after rounding both sides to the cent, no invoice is paid above its GrandTotal")
    claim(raw > 0, "without the rounding, a floating-point comparison flags invoices that are paid exactly")
    full = d.one(f"SELECT COUNT(*) FROM PurchaseInvoice i JOIN {paid} USING (PurchaseInvoiceID) WHERE ROUND(p.s, 2) = ROUND(i.GrandTotal, 2)")
    less = d.one(f"SELECT COUNT(*) FROM PurchaseInvoice i JOIN {paid} USING (PurchaseInvoiceID) WHERE ROUND(p.s, 2) < ROUND(i.GrandTotal, 2)")
    claim(less == d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE Status = 'Partially Paid'"),
          "the invoices paid for less than their total are the ones whose status is Partially Paid")

    # the pairs, as rows
    numbers = d.q("SELECT p.InvoiceNumber, p.SupplierID, p.PurchaseInvoiceID, p.InvoiceDate, p.GrandTotal FROM PurchaseInvoice p JOIN "
                  "(SELECT SupplierID, InvoiceNumber FROM PurchaseInvoice GROUP BY 1, 2 HAVING COUNT(*) > 1) k USING (SupplierID, InvoiceNumber) "
                  "ORDER BY 2, 1, 3")
    pairs: dict[str, list] = {}
    for r in numbers:
        pairs.setdefault(r[0], []).append(r)
    claim(all(p[0][3][:4] == p[1][3][:4] for p in pairs.values()), "the two invoices of a pair are dated in the same fiscal year")
    claim(len({p[0][3][:4] for p in pairs.values()}) == len(d.years), "the pairs fall in every fiscal year")
    claim(d.q("SELECT 1 FROM PurchaseInvoice p JOIN (SELECT SupplierID, InvoiceNumber FROM PurchaseInvoice GROUP BY 1, 2 "
              "HAVING COUNT(*) > 1) k USING (SupplierID, InvoiceNumber) GROUP BY p.SupplierID, p.InvoiceNumber "
              "HAVING COUNT(DISTINCT p.PurchaseOrderID) = 1") == [], "the two invoices of a pair are on different purchase orders")
    checks = d.q("SELECT p.CheckNumber, p.PaymentNumber, p.PaymentDate, i.InvoiceNumber, p.Amount, i.GrandTotal FROM DisbursementPayment p JOIN "
                 "PurchaseInvoice i USING (PurchaseInvoiceID) JOIN (SELECT SupplierID, CheckNumber FROM DisbursementPayment WHERE CheckNumber IS NOT NULL "
                 "GROUP BY 1, 2 HAVING COUNT(*) > 1) k ON k.SupplierID = p.SupplierID AND k.CheckNumber = p.CheckNumber ORDER BY 1, 2")
    by_check: dict[str, list] = {}
    for r in checks:
        by_check.setdefault(r[0], []).append(r)
    claim(all(len({x[2] for x in v}) == 1 for v in by_check.values()), "the two payments of a repeated check number are dated the same day")
    claim(d.one("SELECT COUNT(*) FROM (SELECT 1 FROM DisbursementPayment WHERE PaymentDate < ? GROUP BY SupplierID, Amount "
                "HAVING COUNT(*) > 1 AND COUNT(DISTINCT PaymentDate) = 1)", f"{d.N}-01-01") == 0,
          "every pair of payments with the same supplier and amount, before the next fiscal year, is on different dates")
    return dict(
        methods=methods, no_check=no_check, payments=payments, invoices=invoices, unpaid=unpaid, raw=raw, rounded=rounded, full=full, less=less,
        pairs=[dict(number=n, supplier=p[0][1], first=p[0][2:], second=p[1][2:]) for n, p in pairs.items()],
        check_rows=[dict(check=c, payments=[dict(number=x[1], date=x[2], invoice=x[3], amount=x[4], total=x[5]) for x in v])
                    for c, v in by_check.items()])
