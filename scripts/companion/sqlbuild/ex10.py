"""Instructor SQL solutions to the exercises of Chapter 10 (joins, aggregates, GROUP BY and HAVING, anti-joins, and
subqueries; no CASE, date functions, window functions or CTEs, which arrive in Chapter 11).

Every expected value comes from the context functions of Chapter 10's instructor notes (facts/notes/ch10.py) or from
read-only SQL of this module; every actual value is read from the query's result. The SQL names the fiscal window's
years as the data give them, so a rolled dataset rebuilds the scripts for its own window.
"""

from __future__ import annotations

import sys

from paths import REPO
from sqlbuild.script import Build, Check

if str(REPO / "facts") not in sys.path:
    sys.path.insert(0, str(REPO / "facts"))
from notes import ch10, money, num  # noqa: E402


def claim(*_args, **_kw) -> None:
    """The notes' claims are tested by scripts/facts.py check; here only their values are read."""


def word(k: int) -> str:
    return ch10.word(k)


def cap(k: int) -> str:
    return ch10.word(k).capitalize()


def wording(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def year_range(year: int) -> str:
    return f"BETWEEN '{year}-01-01' AND '{year}-12-31'"


REVENUE_IN = "a.AccountNumber IN (" + ", ".join(ch10.REVENUE_ACCOUNTS) + ")"


# --- Exercise 10.1 -------------------------------------------------------------------------------

def ex1(b: Build) -> None:
    d = b.data
    n = ch10.ex1(d, claim)
    year = d.C
    lines_2026 = d.one(f"SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = "
                       f"l.SalesInvoiceID WHERE s.InvoiceDate {year_range(year)}")
    table_rows = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    freight = d.q("SELECT COUNT(*), COUNT(g.SourceLineID), ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g "
                  "WHERE g.AccountID = ? AND g.FiscalYear = ? AND g.SourceDocumentType = 'SalesInvoice'",
                  d.account("4050"), year)[0]
    s = b.script("Ex 10.1.sql", "reconciling invoice lines to the ledger",
                 f"the join keeps all {num(n['rows'])} lines; fiscal {year} lines + {money(n['diff'])} of cutoff "
                 f"invoices = ledger revenue")

    s.query("Requirement (1): the invoice lines with their invoices, items and customers",
            f"Population: SalesInvoiceLine, every line; expected: {num(n['rows'])} rows, one per line",
            """
            SELECT sil.SalesInvoiceLineID, si.InvoiceNumber, si.InvoiceDate,
                c.CustomerName, i.ItemCode, i.ItemGroup, sil.LineTotal
            FROM SalesInvoiceLine AS sil
                INNER JOIN SalesInvoice AS si
                    ON si.SalesInvoiceID = sil.SalesInvoiceID
                INNER JOIN Item AS i ON i.ItemID = sil.ItemID
                INNER JOIN Customer AS c ON c.CustomerID = si.CustomerID;
            """,
            [Check("joined rows", n["rows"], len)])

    s.query("Requirement (1): the number of invoice lines, to test the join",
            f"Population: SalesInvoiceLine; expected: {num(table_rows)}, the rows of the join",
            """
            SELECT COUNT(*) AS InvoiceLines
            FROM SalesInvoiceLine;
            """,
            [Check("invoice lines in the table", table_rows, lambda r: r.value()),
             Check("equal to the joined rows", n["rows"], lambda r: r.value())])

    s.query(f"Requirement (2): fiscal {year} invoice lines by item group",
            f"Population: lines of invoices dated in {year}; expected: {len(n['groups'])} groups, "
            f"total {money(n['lines_total'])}",
            f"""
            SELECT i.ItemGroup, COUNT(*) AS Lines,
                ROUND(SUM(sil.LineTotal), 2) AS Revenue
            FROM SalesInvoiceLine AS sil
                INNER JOIN SalesInvoice AS si
                    ON si.SalesInvoiceID = sil.SalesInvoiceID
                INNER JOIN Item AS i ON i.ItemID = sil.ItemID
            WHERE si.InvoiceDate {year_range(year)}
            GROUP BY i.ItemGroup
            ORDER BY Revenue DESC;
            """,
            [Check("item groups", [g for g, _ in n["groups"]], lambda r: r.col("ItemGroup"))]
            + [Check(f"{g} revenue", a, lambda r, g=g: r.where(ItemGroup=g)["Revenue"]) for g, a in n["groups"]]
            + [Check("total of the groups", n["lines_total"], lambda r: round(r.total("Revenue"), 2))])

    s.query(f"Requirement (2): the control total of fiscal {year} invoice lines",
            f"Population: as above; expected: {num(lines_2026)} lines, {money(n['lines_total'])} (Chapter 6)",
            f"""
            SELECT COUNT(*) AS Lines,
                ROUND(SUM(sil.LineTotal), 2) AS Revenue
            FROM SalesInvoiceLine AS sil
                INNER JOIN SalesInvoice AS si
                    ON si.SalesInvoiceID = sil.SalesInvoiceID
            WHERE si.InvoiceDate {year_range(year)};
            """,
            [Check("lines", lines_2026, lambda r: r.value("Lines")),
             Check("revenue", n["lines_total"], lambda r: r.value("Revenue"), 0.015)])

    s.query(f"Requirement (3): SalesInvoice postings of fiscal {year} to the revenue accounts",
            f"Population: GLEntry, SalesInvoice, fiscal {year}; expected: {len(n['ledger'])} accounts",
            f"""
            SELECT a.AccountNumber, a.AccountName,
                ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Revenue
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.SourceDocumentType = 'SalesInvoice'
                AND gl.FiscalYear = {year}
                AND {REVENUE_IN}
            GROUP BY a.AccountID, a.AccountNumber, a.AccountName
            ORDER BY a.AccountNumber;
            """,
            [Check("accounts", [a for a, _ in n["ledger"]], lambda r: r.col("AccountNumber"))]
            + [Check(f"{a} revenue", v, lambda r, a=a: r.where(AccountNumber=a)["Revenue"]) for a, v in n["ledger"]])

    s.query(f"Requirement (3): the ledger total of fiscal {year}",
            f"Population: as above; expected: {money(n['ledger_total'])}",
            f"""
            SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Revenue
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.SourceDocumentType = 'SalesInvoice'
                AND gl.FiscalYear = {year}
                AND {REVENUE_IN};
            """,
            [Check("ledger revenue", n["ledger_total"], lambda r: r.value())])

    s.query("Requirement (4): the ledger against the invoice lines, side by side",
            f"Population: the totals of (2) and (3); expected: a difference of {money(n['diff'])}",
            f"""
            SELECT t.Ledger, t.InvoiceLines,
                ROUND(t.Ledger - t.InvoiceLines, 2) AS Difference
            FROM (
                SELECT
                    (SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2)
                     FROM GLEntry AS gl
                         INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                     WHERE gl.SourceDocumentType = 'SalesInvoice'
                         AND gl.FiscalYear = {year}
                         AND {REVENUE_IN}
                    ) AS Ledger,
                    (SELECT ROUND(SUM(sil.LineTotal), 2)
                     FROM SalesInvoiceLine AS sil
                         INNER JOIN SalesInvoice AS si
                             ON si.SalesInvoiceID = sil.SalesInvoiceID
                     WHERE si.InvoiceDate {year_range(year)}
                    ) AS InvoiceLines
            ) AS t;
            """,
            [Check("ledger", n["ledger_total"], lambda r: r.value("Ledger")),
             Check("invoice lines", n["lines_total"], lambda r: r.value("InvoiceLines"), 0.015),
             Check("difference", n["diff"], lambda r: r.value("Difference"), 0.015)])

    cutoff = n["cutoff"]
    s.query(f"Requirement (4): fiscal {year} revenue postings of invoices dated before {year}-01-01",
            f"Population: GLEntry, SalesInvoice, fiscal {year}; expected: {n['n_cutoff']} invoices, "
            f"{money(n['diff'])}",
            f"""
            SELECT si.InvoiceNumber, si.InvoiceDate, gl.PostingDate,
                a.AccountNumber,
                ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Revenue
            FROM GLEntry AS gl
                INNER JOIN SalesInvoice AS si
                    ON gl.SourceDocumentType = 'SalesInvoice'
                    AND si.SalesInvoiceID = gl.SourceDocumentID
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.FiscalYear = {year}
                AND {REVENUE_IN}
                AND si.InvoiceDate < '{year}-01-01'
            GROUP BY si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate,
                gl.PostingDate, a.AccountID, a.AccountNumber
            ORDER BY si.InvoiceNumber, a.AccountNumber;
            """,
            [Check("invoices", [c["number"] for c in cutoff], lambda r: sorted(set(r.col("InvoiceNumber")))),
             Check("their total", n["diff"], lambda r: round(r.total("Revenue"), 2)),
             Check("posting dates", [n["posted"]], lambda r: sorted(set(r.col("PostingDate"))))]
            + [Check(f"{c['number']} (dated {c['date']})", [(c["date"], acct, round(v, 2)) for acct, v in c["accounts"]],
                     lambda r, c=c: [(x["InvoiceDate"], x["AccountNumber"], x["Revenue"])
                                     for x in (dict(zip(r.columns, row)) for row in r.rows)
                                     if x["InvoiceNumber"] == c["number"]])
               for c in cutoff])

    s.query("Requirement (5): freight postings and their invoice lines",
            f"Population: GLEntry, 4050, SalesInvoice, fiscal {year}; expected: {num(freight[0])} postings, "
            f"none with a SourceLineID",
            f"""
            SELECT COUNT(*) AS FreightPostings,
                COUNT(gl.SourceLineID) AS WithSourceLine,
                ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS FreightRevenue
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE a.AccountNumber = 4050 AND gl.FiscalYear = {year}
                AND gl.SourceDocumentType = 'SalesInvoice';
            """,
            [Check("freight postings", freight[0], lambda r: r.value("FreightPostings")),
             Check("with a SourceLineID", 0, lambda r: r.value("WithSourceLine")),
             Check("freight revenue", freight[2], lambda r: r.value("FreightRevenue"))])

    detail = "; ".join(f"{c['number']} (dated {c['date']}, {money(v)} to {acct})" for c in cutoff
                       for acct, v in c["accounts"])
    s.answer("Requirement (4)",
             f"The ledger's SalesInvoice revenue of fiscal {year}, {money(n['ledger_total'])}, exceeds the invoice "
             f"lines dated in {year}, {money(n['lines_total'])}, by {money(n['diff'])}. The difference is "
             f"{n['n_cutoff']} invoices dated in late {d.P} and posted on {n['posted']}: {detail}. The lines total "
             f"selects invoices by InvoiceDate and the ledger by PostingDate, so these invoices fall in {d.P} on one "
             f"side and in {year} on the other; account by account, the ledger is the lines plus these invoices. They "
             f"are the cutoff invoices of Exercises 5.2 and 6.1.")
    s.answer("Requirement (5)",
             f"Freight is billed on the invoice header (SalesInvoice.FreightAmount), not on the lines, so its "
             f"postings to 4050 carry no SourceLineID ({num(freight[0])} postings in {year}, none with a line) and "
             f"there is no invoice line to reconcile them with. The reconciliation compares the revenue accounts fed "
             f"by the lines; freight would be reconciled to the invoice headers instead.")


# --- Exercise 10.2 -------------------------------------------------------------------------------

def ex2(b: Build) -> None:
    d = b.data
    n = ch10.ex2(d, claim)
    inv, line, year = n["inv"], n["line"], d.C
    grand = round(inv["subtotal"] + inv["freight"] + inv["tax"], 2)
    n_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE SalesInvoiceID = ?", inv["id"])
    headers = [r[0] for r in d.q("SELECT DISTINCT a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = "
                                 "g.AccountID WHERE g.SourceDocumentType = 'SalesInvoice' AND g.FiscalYear = ? "
                                 "AND g.SourceLineID IS NULL ORDER BY 1", year)]
    revenue = next(r for r in n["rows"] if r["line"] is not None)
    s = b.script("Ex 10.2.sql", "tracing a sale from the ledger to its documents",
                 f"{inv['number']} posts {n['n_rows']} balanced rows; {num(n['tested'])} fiscal {year} "
                 f"SourceLineIDs tested, none orphaned")
    gl_join = """FROM GLEntry AS gl
                INNER JOIN SalesInvoice AS si
                    ON gl.SourceDocumentType = 'SalesInvoice'
                    AND si.SalesInvoiceID = gl.SourceDocumentID"""

    s.query(f"Requirement (1): the ledger rows posted by {inv['number']}",
            f"Population: GLEntry, SalesInvoice {inv['id']}; expected: {n['n_rows']} rows on {n['posted']}",
            f"""
            SELECT gl.GLEntryID, gl.PostingDate, a.AccountNumber,
                a.AccountName, gl.Debit, gl.Credit, gl.SourceLineID,
                gl.Description
            {gl_join}
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE si.InvoiceNumber = '{inv['number']}'
            ORDER BY gl.GLEntryID;
            """,
            [Check("rows", len(n["rows"]), len),
             Check("posting dates", [n["posted"]], lambda r: sorted(set(r.col("PostingDate"))))]
            + [Check(f"GLEntry {x['id']}", (x["number"], x["amount"], x["side"]),
                     lambda r, i=x["id"]: (lambda w: (w["AccountNumber"], w["Debit"] or w["Credit"],
                                                      "debit" if w["Debit"] else "credit"))(r.where(GLEntryID=i)))
               for x in n["rows"]]
            + [Check("SourceLineID of the revenue row", line["id"],
                     lambda r, i=revenue["id"]: r.where(GLEntryID=i)["SourceLineID"])])

    s.query("Requirement (1): debits against credits and the invoice's total",
            f"Population: as above; expected: debits = credits = GrandTotal = {money(grand)}",
            f"""
            SELECT si.InvoiceNumber, si.SubTotal, si.FreightAmount,
                si.TaxAmount, si.GrandTotal,
                ROUND(SUM(gl.Debit), 2) AS Debits,
                ROUND(SUM(gl.Credit), 2) AS Credits
            {gl_join}
            WHERE si.InvoiceNumber = '{inv['number']}'
            GROUP BY si.SalesInvoiceID, si.InvoiceNumber, si.SubTotal,
                si.FreightAmount, si.TaxAmount, si.GrandTotal;
            """,
            [Check("debits", n["debits"], lambda r: r.value("Debits")),
             Check("credits", n["credits"], lambda r: r.value("Credits")),
             Check("GrandTotal", grand, lambda r: r.value("GrandTotal")),
             Check("SubTotal", inv["subtotal"], lambda r: r.value("SubTotal")),
             Check("FreightAmount", inv["freight"], lambda r: r.value("FreightAmount")),
             Check("TaxAmount", inv["tax"], lambda r: r.value("TaxAmount"))])

    s.query(f"Requirement (1): the trap, ledger rows whose SourceDocumentID is {inv['id']} in any document",
            f"Population: GLEntry; expected: {n['trap_rows']} rows from {n['trap_types']} document types",
            f"""
            SELECT COUNT(*) AS Postings,
                COUNT(DISTINCT SourceDocumentType) AS DocumentTypes
            FROM GLEntry
            WHERE SourceDocumentID = {inv['id']};
            """,
            [Check("rows", n["trap_rows"], lambda r: r.value("Postings")),
             Check("document types", n["trap_types"], lambda r: r.value("DocumentTypes"))])

    s.query(f"Requirement (2): {inv['number']} with its customer, lines and items",
            f"Population: SalesInvoice {inv['id']}; expected: customer {inv['customer']}, {n_lines} line"
            f"{'' if n_lines == 1 else 's'}",
            f"""
            SELECT si.InvoiceNumber, si.InvoiceDate, c.CustomerID,
                c.CustomerName, sil.SalesInvoiceLineID, i.ItemCode,
                i.ItemName, sil.Quantity, sil.UnitPrice, sil.LineTotal
            FROM SalesInvoice AS si
                INNER JOIN Customer AS c ON c.CustomerID = si.CustomerID
                INNER JOIN SalesInvoiceLine AS sil
                    ON sil.SalesInvoiceID = si.SalesInvoiceID
                INNER JOIN Item AS i ON i.ItemID = sil.ItemID
            WHERE si.InvoiceNumber = '{inv['number']}';
            """,
            [Check("lines", n_lines, len),
             Check("invoice date", inv["date"], lambda r: r.cell(0, "InvoiceDate")),
             Check("customer", (inv["customer"], inv["customer_name"]),
                   lambda r: (r.cell(0, "CustomerID"), r.cell(0, "CustomerName"))),
             Check(f"line {line['id']} item", line["name"], lambda r: r.where(SalesInvoiceLineID=line["id"])["ItemName"]),
             Check(f"line {line['id']} quantity", float(line["qty"].replace(",", "")),
                   lambda r: r.where(SalesInvoiceLineID=line["id"])["Quantity"]),
             Check(f"line {line['id']} unit price", line["price"],
                   lambda r: r.where(SalesInvoiceLineID=line["id"])["UnitPrice"])])

    s.query("Requirement (2): the revenue posting joined to its invoice line through SourceLineID",
            f"Population: GLEntry, SalesInvoice {inv['id']}, rows with a SourceLineID; expected: GLEntry "
            f"{revenue['id']} and line {line['id']}",
            f"""
            SELECT gl.GLEntryID, gl.SourceLineID, sil.SalesInvoiceLineID,
                i.ItemName, sil.LineTotal, gl.Credit
            FROM GLEntry AS gl
                INNER JOIN SalesInvoiceLine AS sil
                    ON sil.SalesInvoiceLineID = gl.SourceLineID
                INNER JOIN Item AS i ON i.ItemID = sil.ItemID
            WHERE gl.SourceDocumentType = 'SalesInvoice'
                AND gl.SourceDocumentID = {inv['id']};
            """,
            [Check("rows", 1, len),
             Check("GLEntryID", revenue["id"], lambda r: r.value("GLEntryID")),
             Check("SalesInvoiceLineID", line["id"], lambda r: r.value("SalesInvoiceLineID")),
             Check("LineTotal equals the credit", revenue["amount"], lambda r: r.value("LineTotal")),
             Check("credit", revenue["amount"], lambda r: r.value("Credit"))])

    s.query(f"Requirement (3): the fiscal {year} SalesInvoice postings that carry a SourceLineID",
            f"Population: GLEntry, SalesInvoice, fiscal {year}; expected: {num(n['tested'])} postings to test",
            f"""
            SELECT COUNT(*) AS PostingsTested
            FROM GLEntry
            WHERE SourceDocumentType = 'SalesInvoice'
                AND FiscalYear = {year}
                AND SourceLineID IS NOT NULL;
            """,
            [Check("postings tested", n["tested"], lambda r: r.value())])

    s.query("Requirement (3): anti-join, postings whose SourceLineID matches no invoice line",
            f"Population: the {num(n['tested'])} postings above; expected: no rows",
            f"""
            SELECT gl.GLEntryID, gl.PostingDate, gl.VoucherNumber,
                gl.SourceLineID, gl.Credit
            FROM GLEntry AS gl
                LEFT JOIN SalesInvoiceLine AS sil
                    ON sil.SalesInvoiceLineID = gl.SourceLineID
            WHERE gl.SourceDocumentType = 'SalesInvoice'
                AND gl.FiscalYear = {year}
                AND gl.SourceLineID IS NOT NULL
                AND sil.SalesInvoiceLineID IS NULL;
            """,
            [Check("orphaned SourceLineIDs", 0, len)])

    s.query("Requirement (3), an added test: postings whose line belongs to another invoice",
            f"Population: the {num(n['tested'])} postings above; expected: no rows",
            f"""
            SELECT gl.GLEntryID, gl.SourceDocumentID, gl.SourceLineID,
                sil.SalesInvoiceID
            FROM GLEntry AS gl
                INNER JOIN SalesInvoiceLine AS sil
                    ON sil.SalesInvoiceLineID = gl.SourceLineID
            WHERE gl.SourceDocumentType = 'SalesInvoice'
                AND gl.FiscalYear = {year}
                AND sil.SalesInvoiceID <> gl.SourceDocumentID;
            """,
            [Check("lines on another invoice", 0, len)])

    s.query(f"Requirement (3): the accounts of the postings with no SourceLineID",
            f"Population: GLEntry, SalesInvoice, fiscal {year}; expected: {wording([str(h) for h in headers])}",
            f"""
            SELECT a.AccountNumber, a.AccountName, COUNT(*) AS Postings
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.SourceDocumentType = 'SalesInvoice'
                AND gl.FiscalYear = {year}
                AND gl.SourceLineID IS NULL
            GROUP BY a.AccountID, a.AccountNumber, a.AccountName
            ORDER BY a.AccountNumber;
            """,
            [Check("header-level accounts", headers, lambda r: r.col("AccountNumber"))])

    rows = "; ".join(f"GLEntry {x['id']} {x['side']}s {x['number']} {x['name']} {money(x['amount'])}"
                     for x in n["rows"])
    s.answer("Requirement (1)",
             f"{inv['number']} (SalesInvoiceID {inv['id']}, dated {inv['date']}, customer {inv['customer']} "
             f"{inv['customer_name']}) posts {n['n_rows']} rows on {n['posted']}: {rows}. The debit records the "
             f"receivable for the GrandTotal; the credits record the revenue (SubTotal), the freight billed, and the "
             f"sales tax owed. Debits {money(n['debits'])} equal credits {money(n['credits'])} and the GrandTotal "
             f"(SubTotal {money(inv['subtotal'])} + freight {money(inv['freight'])} + tax {money(inv['tax'])}). The "
             f"join must name SourceDocumentType = 'SalesInvoice' in its ON clause: SourceDocumentID {inv['id']} "
             f"alone appears in {n['trap_rows']} rows of {n['trap_types']} document types.")
    s.answer("Requirement (4), memo",
             f"Every ledger row records the document that caused it: SourceDocumentType names the table, "
             f"SourceDocumentID the document's key in it, and SourceLineID the line, where the posting comes from "
             f"one. Joining on the type and the ID together moves from a posting to its document, and joining the "
             f"document's lines and master data (customer, item) shows what was sold; the same keys, read the other "
             f"way, find every posting a document made, so an auditor can vouch from the ledger to the documents and "
             f"trace from the documents to the ledger.\n\n"
             f"For {inv['number']}, the four rows balance and equal the invoice's GrandTotal, and the revenue row's "
             f"SourceLineID {line['id']} is the invoice's line ({line['name']}, {line['qty']} units at "
             f"{money(line['price'])}). Requirement (3) extends the trace to the whole year: all "
             f"{num(n['tested'])} SalesInvoice postings of fiscal {year} that carry a SourceLineID point to an "
             f"existing invoice line (the anti-join returns no rows), and each line belongs to the invoice the posting "
             f"names. The header-level rows (receivable, freight, tax) carry no SourceLineID by design. The test "
             f"proves that the line-level revenue postings are supported by invoice lines; it does not prove that "
             f"every invoice line was posted, which needs the reverse anti-join, or that the amounts agree.")


# --- Exercise 10.3 -------------------------------------------------------------------------------

def ex3(b: Build) -> None:
    d = b.data
    n = ch10.ex3(d, claim)
    all_customers = d.one("SELECT COUNT(*) FROM Customer")
    names = d.one("SELECT COUNT(DISTINCT c.CustomerName) FROM SalesOrder o JOIN Customer c ON c.CustomerID = o.CustomerID")
    top10 = [r[0] for r in d.q("SELECT o.CustomerID FROM SalesOrder o GROUP BY o.CustomerID HAVING COUNT(*) >= 20 "
                               "ORDER BY ROUND(AVG(o.OrderTotal), 2) DESC LIMIT 10")]
    seg_customers = dict(d.q("SELECT c.CustomerSegment, COUNT(DISTINCT c.CustomerID) FROM SalesOrder o JOIN Customer c "
                             "ON c.CustomerID = o.CustomerID GROUP BY 1"))
    shared = d.q("SELECT c.CustomerID, c.CustomerName, COUNT(o.SalesOrderID) FROM Customer c LEFT JOIN SalesOrder o "
                 "ON o.CustomerID = c.CustomerID WHERE c.CustomerName IN (SELECT CustomerName FROM Customer "
                 "GROUP BY CustomerName HAVING COUNT(*) > 1) GROUP BY c.CustomerID ORDER BY c.CustomerName, c.CustomerID")
    m = n["merged"]
    s = b.script("Ex 10.3.sql", "average order value by customer",
                 f"{num(n['orders'])} orders from {n['customers']} customers; grouping by name merges "
                 f"{m['name']} into one row")
    join = """FROM SalesOrder AS so
                INNER JOIN Customer AS c ON c.CustomerID = so.CustomerID"""

    s.query("Requirement (1): orders and average order value by customer",
            f"Population: SalesOrder, every order; expected: {n['customers']} customers, "
            f"{n['top'][0]['name']} first",
            f"""
            SELECT c.CustomerID, c.CustomerName, c.CustomerSegment,
                COUNT(*) AS Orders,
                ROUND(SUM(so.OrderTotal), 2) AS TotalOrdered,
                ROUND(AVG(so.OrderTotal), 2) AS AverageOrder
            {join}
            GROUP BY c.CustomerID, c.CustomerName, c.CustomerSegment
            ORDER BY AverageOrder DESC;
            """,
            [Check("customers", n["customers"], len),
             Check("orders", n["orders"], lambda r: r.total("Orders"))]
            + [Check(f"rank {i + 1}", (t["id"], t["name"], t["n"], round(t["avg"], 2)),
                     lambda r, i=i: (r.cell(i, "CustomerID"), r.cell(i, "CustomerName"), r.cell(i, "Orders"),
                                     r.cell(i, "AverageOrder")))
               for i, t in enumerate(n["top"])])

    s.query("Requirement (1): all orders, the customers who placed them, and the average",
            f"Population: SalesOrder; expected: {num(n['orders'])} orders, {n['customers']} customers, average "
            f"{money(n['avg'])}",
            """
            SELECT COUNT(*) AS Orders,
                COUNT(DISTINCT CustomerID) AS Customers,
                ROUND(AVG(OrderTotal), 2) AS AverageOrder
            FROM SalesOrder;
            """,
            [Check("orders", n["orders"], lambda r: r.value("Orders")),
             Check("customers with orders", n["customers"], lambda r: r.value("Customers")),
             Check("average order", round(n["avg"], 2), lambda r: r.value("AverageOrder"))])

    s.query("Requirement (1): the customers in the master file",
            f"Population: Customer; expected: {all_customers}, so {n['without']} have no orders",
            """
            SELECT COUNT(*) AS Customers
            FROM Customer;
            """,
            [Check("customers", all_customers, lambda r: r.value()),
             Check("customers without orders", n["without"], lambda r: r.value() - n["customers"])])

    s.query("Requirement (2): the same analysis grouped by CustomerName",
            f"Population: as (1); expected: {names} rows, one fewer than (1)",
            f"""
            SELECT c.CustomerName, COUNT(*) AS Orders,
                ROUND(SUM(so.OrderTotal), 2) AS TotalOrdered,
                ROUND(AVG(so.OrderTotal), 2) AS AverageOrder
            {join}
            GROUP BY c.CustomerName
            ORDER BY AverageOrder DESC;
            """,
            [Check("rows", names, len),
             Check("rows fewer than (1)", n["customers"] - names, lambda r: n["customers"] - len(r)),
             Check(f"{m['name']} orders", m["n"], lambda r: r.where(CustomerName=m["name"])["Orders"]),
             Check(f"{m['name']} average", round(m["avg"], 2),
                   lambda r: r.where(CustomerName=m["name"])["AverageOrder"])])

    s.query("Requirement (2): names that cover more than one customer with orders",
            f"Population: as (1); expected: {m['name']}, {len(m['customers'])} customers",
            f"""
            SELECT c.CustomerName,
                COUNT(DISTINCT c.CustomerID) AS Customers,
                COUNT(*) AS Orders
            {join}
            GROUP BY c.CustomerName
            HAVING COUNT(DISTINCT c.CustomerID) > 1;
            """,
            [Check("names", [m["name"]], lambda r: r.col("CustomerName")),
             Check("customers", len(m["customers"]), lambda r: r.value("Customers")),
             Check("orders", m["n"], lambda r: r.value("Orders"))])

    s.query("Requirement (2): every customer whose name another customer shares, with its orders",
            f"Population: Customer, shared names; expected: {len(shared)} customers, "
            f"{n['unmerged']['name']} with orders only on customer {n['unmerged']['ordering']}",
            """
            SELECT c.CustomerID, c.CustomerName, c.CustomerSegment,
                COUNT(so.SalesOrderID) AS Orders,
                ROUND(AVG(so.OrderTotal), 2) AS AverageOrder
            FROM Customer AS c
                LEFT JOIN SalesOrder AS so ON so.CustomerID = c.CustomerID
            WHERE c.CustomerName IN (
                SELECT CustomerName
                FROM Customer
                GROUP BY CustomerName
                HAVING COUNT(*) > 1
            )
            GROUP BY c.CustomerID, c.CustomerName, c.CustomerSegment
            ORDER BY c.CustomerName, c.CustomerID;
            """,
            [Check("customers and orders", [(i, nm, k) for i, nm, k in shared],
                   lambda r: list(zip(r.col("CustomerID"), r.col("CustomerName"), r.col("Orders"))))]
            + [Check(f"customer {c['id']}", (c["segment"], c["n"], round(c["avg"], 2)),
                     lambda r, i=c["id"]: (lambda w: (w["CustomerSegment"], w["Orders"], w["AverageOrder"]))(
                         r.where(CustomerID=i)))
               for c in m["customers"]])

    s.query("Requirement (3): the ten highest averages among customers with at least 20 orders",
            f"Population: as (1), HAVING 20 orders or more; expected: {n['top'][0]['name']} first",
            f"""
            SELECT c.CustomerID, c.CustomerName, c.CustomerSegment,
                COUNT(*) AS Orders,
                ROUND(AVG(so.OrderTotal), 2) AS AverageOrder
            {join}
            GROUP BY c.CustomerID, c.CustomerName, c.CustomerSegment
            HAVING COUNT(*) >= 20
            ORDER BY AverageOrder DESC
            LIMIT 10;
            """,
            [Check("the ten customers", top10, lambda r: r.col("CustomerID")),
             Check("fewest orders among them (at least 20)", True, lambda r: min(r.col("Orders")) >= 20)])

    s.query("Requirement (4): orders and average order value by segment",
            f"Population: as (1); expected: {len(n['segments'])} segments, {n['segments'][0][0]} highest",
            f"""
            SELECT c.CustomerSegment, COUNT(*) AS Orders,
                COUNT(DISTINCT c.CustomerID) AS Customers,
                ROUND(AVG(so.OrderTotal), 2) AS AverageOrder
            {join}
            GROUP BY c.CustomerSegment
            ORDER BY AverageOrder DESC;
            """,
            [Check("segments in order", [sg for sg, _, _ in n["segments"]], lambda r: r.col("CustomerSegment"))]
            + [Check(f"{sg}", (k, seg_customers[sg], round(a, 2)),
                     lambda r, sg=sg: (lambda w: (w["Orders"], w["Customers"], w["AverageOrder"]))(
                         r.where(CustomerSegment=sg)))
               for sg, k, a in n["segments"]])

    segs = "; ".join(f"{sg} {num(k)} orders averaging {money(a)}" for sg, k, a in n["segments"])
    hi, lo = n["segments"][0], n["segments"][-1]
    b5, b173 = m["customers"][0], m["customers"][1]
    s.answer("Requirement (5), note for the sales manager",
             f"Order size differs sharply by segment: {segs}. A {hi[0]} order averages about "
             f"{hi[2] / lo[2]:.1f} times a {lo[0]} order, so the segment mix matters as much as the number of "
             f"orders. Across all {num(n['orders'])} orders the average is {money(n['avg'])}, and the customers with "
             f"the largest orders are {n['top'][0]['name']} ({money(n['top'][0]['avg'])} over {n['top'][0]['n']} "
             f"orders), {n['top'][1]['name']} and {n['top'][2]['name']}.\n\n"
             f"Requirement (1) groups by CustomerID because the key identifies a customer and the name does not: "
             f"grouping by name returns {names} rows instead of {n['customers']}, because two different customers "
             f"are named {m['name']}, customer {b5['id']} ({b5['segment']}, {b5['n']} orders averaging "
             f"{money(b5['avg'])}) and customer {b173['id']} ({b173['segment']}, {b173['n']} orders averaging "
             f"{money(b173['avg'])}). By name they merge into one row of {m['n']} orders averaging "
             f"{money(m['avg'])}, which describes neither customer. ({n['unmerged']['name']} is also shared, but "
             f"only customer {n['unmerged']['ordering']} has orders, so it does not merge here.)")


# --- Exercise 10.4 -------------------------------------------------------------------------------

def ex4(b: Build) -> None:
    d = b.data
    n = ch10.ex4(d, claim)
    year = d.C
    closes = ", ".join(f"'{e}'" for e in d.closes_of(year))
    ledger_suppliers = d.q("SELECT pi.SupplierID, ROUND(SUM(g.Debit) - SUM(g.Credit), 2) FROM GLEntry g "
                           "JOIN PurchaseInvoice pi ON g.SourceDocumentType = 'PurchaseInvoice' AND pi.PurchaseInvoiceID = "
                           "g.SourceDocumentID WHERE g.AccountID = ? AND g.FiscalYear = ? "
                           "AND g.Description LIKE '%purchase variance' GROUP BY 1", d.account("5060"), year)
    postings = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                     "AND Description LIKE '%purchase variance'", d.account("5060"), year)
    descriptions = d.q(f"SELECT Description, COUNT(*), ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry "
                       f"WHERE AccountID = ? AND FiscalYear = ? AND VoucherNumber NOT IN ({closes}) GROUP BY 1",
                       d.account("5060"), year)
    s = b.script("Ex 10.4.sql", "purchase price variance by supplier",
                 f"fiscal {year} ledger variance {money(n['gl'])} against {money(n['lines'])} from the lines")
    lines = """FROM PurchaseInvoiceLine AS pil
                INNER JOIN PurchaseInvoice AS pi
                    ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID
                INNER JOIN PurchaseOrderLine AS pol
                    ON pol.POLineID = pil.POLineID"""
    variance = "pil.Quantity * (pil.UnitCost - pol.UnitCost)"

    s.query(f"Requirement (1): the five suppliers with the largest variance in fiscal {year}",
            f"Population: GLEntry, 5060, fiscal {year}, purchase variance postings; expected: "
            f"{n['top'][0]['name']} first, {money(n['top'][0]['amount'])}",
            f"""
            SELECT s.SupplierID, s.SupplierName, COUNT(*) AS Postings,
                ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS PriceVariance
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                INNER JOIN PurchaseInvoice AS pi
                    ON gl.SourceDocumentType = 'PurchaseInvoice'
                    AND pi.PurchaseInvoiceID = gl.SourceDocumentID
                INNER JOIN Supplier AS s ON s.SupplierID = pi.SupplierID
            WHERE a.AccountNumber = 5060 AND gl.FiscalYear = {year}
                AND gl.Description LIKE '%purchase variance'
            GROUP BY s.SupplierID, s.SupplierName
            ORDER BY PriceVariance DESC
            LIMIT 5;
            """,
            [Check("suppliers", [t["id"] for t in n["top"]], lambda r: r.col("SupplierID"))]
            + [Check(f"supplier {t['id']} {t['name']}", round(t["amount"], 2),
                     lambda r, i=t["id"]: r.where(SupplierID=i)["PriceVariance"]) for t in n["top"]])

    s.query(f"Requirement (1): the ledger total of the variance postings of fiscal {year}",
            f"Population: as above, every supplier; expected: {num(postings)} postings, {money(n['gl'])}",
            f"""
            SELECT COUNT(*) AS Postings,
                ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS PriceVariance
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE a.AccountNumber = 5060 AND gl.FiscalYear = {year}
                AND gl.Description LIKE '%purchase variance';
            """,
            [Check("postings", postings, lambda r: r.value("Postings")),
             Check("ledger variance", n["gl"], lambda r: r.value("PriceVariance"))])

    s.query(f"Requirement (2): the variance recalculated from invoices dated in {year}",
            f"Population: invoice lines with a purchase-order line; expected: {num(n['n_lines'])} lines, "
            f"{money(n['lines'])}",
            f"""
            SELECT COUNT(*) AS InvoiceLines,
                ROUND(SUM({variance}), 2)
                    AS PriceVariance
            {lines}
            WHERE pi.InvoiceDate {year_range(year)};
            """,
            [Check("invoice lines", n["n_lines"], lambda r: r.value("InvoiceLines")),
             Check("recalculated variance", n["lines"], lambda r: r.value("PriceVariance")),
             Check("gap to the ledger", n["gap"], lambda r: round(abs(n["gl"] - r.value("PriceVariance")), 2))])

    s.query("Requirement (2): the ledger and the lines by supplier",
            f"Population: every supplier with variance postings; expected: {len(ledger_suppliers)} suppliers, "
            f"largest difference {money(n['supplier_gap'])}",
            f"""
            SELECT COUNT(*) AS Suppliers,
                ROUND(SUM(g.Variance), 2) AS Ledger,
                ROUND(SUM(l.Variance), 2) AS Lines,
                ROUND(MAX(ABS(g.Variance - l.Variance)), 2)
                    AS LargestDifference
            FROM (
                SELECT pi.SupplierID,
                    ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Variance
                FROM GLEntry AS gl
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                    INNER JOIN PurchaseInvoice AS pi
                        ON gl.SourceDocumentType = 'PurchaseInvoice'
                        AND pi.PurchaseInvoiceID = gl.SourceDocumentID
                WHERE a.AccountNumber = 5060 AND gl.FiscalYear = {year}
                    AND gl.Description LIKE '%purchase variance'
                GROUP BY pi.SupplierID
            ) AS g
                INNER JOIN (
                    SELECT pi.SupplierID,
                        ROUND(SUM(pil.Quantity
                            * (pil.UnitCost - pol.UnitCost)), 2) AS Variance
                    FROM PurchaseInvoiceLine AS pil
                        INNER JOIN PurchaseInvoice AS pi
                            ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID
                        INNER JOIN PurchaseOrderLine AS pol
                            ON pol.POLineID = pil.POLineID
                    WHERE pi.InvoiceDate {year_range(year)}
                    GROUP BY pi.SupplierID
                ) AS l ON l.SupplierID = g.SupplierID;
            """,
            [Check("suppliers matched", len(ledger_suppliers), lambda r: r.value("Suppliers")),
             Check("ledger", n["gl"], lambda r: r.value("Ledger"), 0.015),
             Check("lines", n["lines"], lambda r: r.value("Lines"), 0.015),
             Check("largest difference by supplier", round(n["supplier_gap"], 2),
                   lambda r: r.value("LargestDifference"))])

    for label, op, key in (("above", ">", "above"), ("below", "<", "below"), ("at", "=", "at")):
        s.query(f"Requirement (3): fiscal {year} invoice lines billed {label} the order price",
                f"Population: the {num(n['n_lines'])} lines of (2); expected: {num(n[key])}",
                f"""
            SELECT COUNT(*) AS InvoiceLines
            {lines}
            WHERE pi.InvoiceDate {year_range(year)}
                AND pil.UnitCost {op} pol.UnitCost;
            """,
                [Check(f"lines {label}", n[key], lambda r: r.value())])

    s.query("Requirement (3): the range of invoice prices against order prices",
            f"Population: as (2); expected: {num(100 * n['low'], 1)}% below to {num(100 * n['high'], 1)}% above",
            f"""
            SELECT ROUND(MIN(pil.UnitCost / pol.UnitCost - 1) * 100, 2)
                    AS LowestPct,
                ROUND(MAX(pil.UnitCost / pol.UnitCost - 1) * 100, 2)
                    AS HighestPct
            {lines}
            WHERE pi.InvoiceDate {year_range(year)};
            """,
            [Check("lowest, percent", -100 * n["low"], lambda r: r.value("LowestPct"), 0.006),
             Check("highest, percent", 100 * n["high"], lambda r: r.value("HighestPct"), 0.006)])

    s.query(f"Requirement (4): amount invoiced against orders and variance by year, {d.F} to {year}",
            f"Population: invoice lines with a purchase-order line, dated {d.F} to {year}; expected: "
            + ", ".join(f"{y['year']} {num(100 * y['rate'], 2)}%" for y in n["years"]),
            f"""
            SELECT SUBSTR(pi.InvoiceDate, 1, 4) AS InvoiceYear,
                COUNT(*) AS InvoiceLines,
                ROUND(SUM(pil.Quantity * pil.UnitCost), 2) AS AmountInvoiced,
                ROUND(SUM(pil.LineTotal), 2) AS LineTotals,
                ROUND(SUM({variance}), 2)
                    AS PriceVariance,
                ROUND(100.0 * SUM({variance})
                    / SUM(pil.Quantity * pil.UnitCost), 2) AS VariancePct
            {lines}
            WHERE pi.InvoiceDate BETWEEN '{d.F}-01-01' AND '{year}-12-31'
            GROUP BY InvoiceYear
            ORDER BY InvoiceYear;
            """,
            [Check("years", [str(y["year"]) for y in n["years"]], lambda r: r.col("InvoiceYear"))]
            + [c for y in n["years"] for c in (
                Check(f"{y['year']} amount invoiced", y["amount"],
                      lambda r, k=str(y["year"]): r.where(InvoiceYear=k)["AmountInvoiced"]),
                Check(f"{y['year']} price variance", y["variance"],
                      lambda r, k=str(y["year"]): r.where(InvoiceYear=k)["PriceVariance"]),
                Check(f"{y['year']} variance, percent", 100 * y["rate"],
                      lambda r, k=str(y["year"]): r.where(InvoiceYear=k)["VariancePct"], 0.006),
                Check(f"{y['year']} LineTotal less amount (rounding of each line)", y["line_gap"],
                      lambda r, k=str(y["year"]): (lambda w: abs(w["LineTotals"] - w["AmountInvoiced"]))(
                          r.where(InvoiceYear=k)), 0.011))])

    s.query(f"Requirement (5): the rest of account 5060 in fiscal {year}, closes excluded",
            f"Population: GLEntry, 5060, fiscal {year}; expected: nonrecoverable purchase tax "
            f"{money(n['tax'])} besides the variances",
            f"""
            SELECT gl.Description, COUNT(*) AS Postings,
                ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Amount
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE a.AccountNumber = 5060 AND gl.FiscalYear = {year}
                AND gl.VoucherNumber NOT IN ({closes})
            GROUP BY gl.Description
            ORDER BY Amount DESC;
            """,
            [Check("descriptions", sorted(r[0] for r in descriptions), lambda r: sorted(r.col("Description"))),
             Check("nonrecoverable purchase tax", n["tax"],
                   lambda r: r.where(Description="Record nonrecoverable purchase tax")["Amount"])])

    top = n["top"]
    yrs = n["years"]
    rates = ", ".join(f"{y['year']} {num(100 * y['rate'], 2)}% of {money(y['amount'])}" for y in yrs)
    s.answer("Requirement (5), memo to the purchasing manager",
             f"Which suppliers bill above the order price? In fiscal {year} the ledger's purchase variance postings "
             f"net {money(n['gl'])} unfavorable. The largest come from {top[0]['id']} {top[0]['name']} "
             f"({money(top[0]['amount'])}), {top[1]['id']} {top[1]['name']} ({money(top[1]['amount'])}) and "
             f"{top[2]['id']} {top[2]['name']} ({money(top[2]['amount'])}), but the five largest hold only "
             f"{num(100 * sum(x['amount'] for x in top) / n['gl'], 1)}% of the total among {len(ledger_suppliers)} "
             f"suppliers, so billing above the order price is widespread rather than concentrated. Of "
             f"{num(n['n_lines'])} invoice lines, {num(n['above'])} are billed above the order price, "
             f"{num(n['below'])} below and {num(n['at'])} at it, within "
             f"{num(100 * n['low'], 1)}% below to {num(100 * n['high'], 1)}% above. Recalculated from the documents, "
             f"the variance is {money(n['lines'])}, {money(n['gap'])} from the ledger because each posting is "
             f"rounded (by supplier, within {money(n['supplier_gap'])}).\n\n"
             f"Did the account grow because prices rose or because we bought more? The variance is a steady share "
             f"of what we buy: {rates}. Both the amount invoiced and the variance grew each year while the rate "
             f"stayed near half a percent, so the account grew because purchases grew, not because suppliers raised "
             f"their billing relative to the order price. The rest of account 5060 is nonrecoverable purchase tax "
             f"({money(n['tax'])} in {year}).\n\n"
             f"What the comparison cannot show: it measures the invoice against the purchase order, so a price rise "
             f"already built into the purchase-order prices, or a better price negotiated elsewhere, does not appear "
             f"in it. Testing whether we pay too much needs order prices compared with earlier prices, price lists, "
             f"or the standard cost.")


# --- Exercise 10.5 -------------------------------------------------------------------------------

def ex5(b: Build) -> None:
    d = b.data
    n = ch10.ex5(d, claim)
    profile = {ch10.DIRECT: n["direct"], ch10.INDIRECT: n["indirect"], ch10.NONMFG: n["nonmfg"]}
    customers = d.q("SELECT c.CustomerID FROM Customer c LEFT JOIN SalesOrder o ON o.CustomerID = c.CustomerID "
                    "WHERE o.SalesOrderID IS NULL ORDER BY 1")
    s = b.script("Ex 10.5.sql", "testing referential integrity with anti-joins",
                 f"{n['n_orphans']} ledger rows without a payroll payment; {n['orphans']} labor entries with an "
                 f"orphaned operation key")
    orphan_join = """FROM GLEntry AS gl
                LEFT JOIN PayrollPayment AS pp
                    ON pp.PayrollPaymentID = gl.SourceDocumentID
            WHERE gl.SourceDocumentType = 'PayrollPayment'
                AND pp.PayrollPaymentID IS NULL"""
    op_join = """FROM LaborTimeEntry AS lt
                LEFT JOIN WorkOrderOperation AS op
                    ON op.WorkOrderOperationID = lt.WorkOrderOperationID
                LEFT JOIN WorkOrder AS wo ON wo.WorkOrderID = lt.WorkOrderID
            WHERE lt.WorkOrderOperationID IS NOT NULL
                AND op.WorkOrderOperationID IS NULL"""

    s.query("Requirement (1): a profile of LaborTimeEntry by labor type",
            f"Population: LaborTimeEntry, every entry; expected: {len(profile)} labor types, "
            f"{num(n['direct']['n'])} direct entries",
            """
            SELECT LaborType, COUNT(*) AS Entries,
                COUNT(WorkOrderOperationID) AS WithOperation,
                COUNT(DISTINCT EmployeeID) AS Employees,
                MIN(WorkDate) AS FirstWorkDate,
                MAX(WorkDate) AS LastWorkDate
            FROM LaborTimeEntry
            GROUP BY LaborType
            ORDER BY LaborType;
            """,
            [Check("labor types", sorted(profile), lambda r: r.col("LaborType"))]
            + [Check(f"{t}", (p["n"], p["ops"], p["employees"], p["first"], p["last"]),
                     lambda r, t=t: (lambda w: (w["Entries"], w["WithOperation"], w["Employees"], w["FirstWorkDate"],
                                                w["LastWorkDate"]))(r.where(LaborType=t)))
               for t, p in profile.items()])

    pairs = n["pairs"]
    s.query("Requirement (2): ledger rows that point to no payroll payment",
            f"Population: GLEntry, PayrollPayment; expected: {n['n_orphans']} rows, "
            f"{word(len(pairs))} pairs of {money(n['amount'])}",
            f"""
            SELECT gl.GLEntryID, gl.PostingDate, gl.SourceDocumentID,
                gl.Debit, gl.Credit, gl.Description
            {orphan_join}
            ORDER BY gl.GLEntryID;
            """,
            [Check("rows", sum(len(p["ids"]) for p in pairs), len),
             Check("GLEntryIDs", [i for p in pairs for i in p["ids"]], lambda r: r.col("GLEntryID")),
             Check("SourceDocumentIDs", [p["doc"] for p in pairs], lambda r: sorted(set(r.col("SourceDocumentID")))),
             Check("posting dates", [p["date"] for p in pairs], lambda r: sorted(set(r.col("PostingDate")))),
             Check("descriptions", sorted([n["debit_text"], n["credit_text"]]),
                   lambda r: sorted(set(r.col("Description")))),
             Check("every row's amount", [n["amount"]],
                   lambda r: sorted({x or y for x, y in zip(r.col("Debit"), r.col("Credit"))})),
             Check("debit rows", len(pairs), lambda r: sum(1 for x in r.col("Debit") if x > 0))])

    s.query("Requirement (2): their totals",
            f"Population: as above; expected: debits and credits {money(n['total'])} each",
            f"""
            SELECT COUNT(*) AS Postings,
                ROUND(SUM(gl.Debit), 2) AS Debits,
                ROUND(SUM(gl.Credit), 2) AS Credits
            {orphan_join};
            """,
            [Check("postings", sum(len(p["ids"]) for p in pairs), lambda r: r.value("Postings")),
             Check("debits", n["total"], lambda r: r.value("Debits")),
             Check("credits", n["total"], lambda r: r.value("Credits"))])

    s.query("Requirement (3): customers that have never placed a sales order",
            f"Population: Customer; expected: {n['n_customers'].lower()} customers, all inactive",
            """
            SELECT c.CustomerID, c.CustomerName, c.CustomerSegment,
                c.IsActive
            FROM Customer AS c
                LEFT JOIN SalesOrder AS so ON so.CustomerID = c.CustomerID
            WHERE so.SalesOrderID IS NULL
            ORDER BY c.CustomerID;
            """,
            [Check("customers", [r[0] for r in customers], lambda r: r.col("CustomerID")),
             Check("IsActive values", [0], lambda r: sorted(set(r.col("IsActive"))))])

    s.query("Requirement (4): work orders with no work order operations",
            f"Population: WorkOrder; expected: {wording(n['work_orders'])}, all Closed",
            """
            SELECT wo.WorkOrderID, wo.WorkOrderNumber, wo.Status,
                wo.ReleasedDate, wo.ClosedDate
            FROM WorkOrder AS wo
                LEFT JOIN WorkOrderOperation AS op
                    ON op.WorkOrderID = wo.WorkOrderID
            WHERE op.WorkOrderOperationID IS NULL
            ORDER BY wo.WorkOrderNumber;
            """,
            [Check("work orders", n["work_orders"], lambda r: r.col("WorkOrderNumber")),
             Check("statuses", ["Closed"], lambda r: sorted(set(r.col("Status"))))])

    s.query("Requirement (4): the labor time recorded on those work orders",
            f"Population: LaborTimeEntry; expected: {n['wo_labor']} direct entries",
            """
            SELECT lt.LaborType, COUNT(*) AS Entries,
                ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 2) AS Hours
            FROM LaborTimeEntry AS lt
            WHERE lt.WorkOrderID IN (
                SELECT wo.WorkOrderID
                FROM WorkOrder AS wo
                    LEFT JOIN WorkOrderOperation AS op
                        ON op.WorkOrderID = wo.WorkOrderID
                WHERE op.WorkOrderOperationID IS NULL
            )
            GROUP BY lt.LaborType;
            """,
            [Check("labor types", [ch10.DIRECT], lambda r: r.col("LaborType")),
             Check("entries", n["wo_labor"], lambda r: r.total("Entries"))])

    s.query("Requirement (5): labor time whose WorkOrderOperationID matches no operation",
            f"Population: LaborTimeEntry with a WorkOrderOperationID; expected: {n['orphans']} entries, "
            f"{num(n['orphan_hours'], 2)} hours",
            f"""
            SELECT lt.LaborTimeEntryID, lt.LaborType, lt.EmployeeID,
                wo.WorkOrderNumber, lt.WorkOrderOperationID, lt.WorkDate,
                lt.RegularHours + lt.OvertimeHours AS Hours
            {op_join}
            ORDER BY wo.WorkOrderNumber, lt.WorkDate;
            """,
            [Check("entries", n["orphans"], len),
             Check("labor types", [ch10.DIRECT], lambda r: sorted(set(r.col("LaborType")))),
             Check("hours", n["orphan_hours"], lambda r: r.total("Hours"))])

    s.query("Requirement (5): the same entries by work order",
            f"Population: as above; expected: "
            + ", ".join(f"{wo} {k}" for wo, k in n["orphan_by_wo"]),
            f"""
            SELECT wo.WorkOrderNumber, COUNT(*) AS Entries,
                ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 2) AS Hours
            {op_join}
            GROUP BY wo.WorkOrderID, wo.WorkOrderNumber
            ORDER BY wo.WorkOrderNumber;
            """,
            [Check("entries by work order", n["orphan_by_wo"], lambda r: list(zip(r.col("WorkOrderNumber"),
                                                                                   r.col("Entries")))),
             Check("hours", n["orphan_hours"], lambda r: r.total("Hours"), 0.015)])

    p = profile
    pair_text = "; ".join(f"GLEntryIDs {p_['ids'][0]} and {p_['ids'][1]} ({p_['date']}, SourceDocumentID "
                          f"{p_['doc']})" for p_ in pairs)
    s.answer("Requirement (1)",
             f"Direct Manufacturing: {num(p[ch10.DIRECT]['n'])} entries, {num(p[ch10.DIRECT]['ops'])} with a "
             f"WorkOrderOperationID, {p[ch10.DIRECT]['employees']} employees, {p[ch10.DIRECT]['first']} to "
             f"{p[ch10.DIRECT]['last']}; Indirect Manufacturing: {num(p[ch10.INDIRECT]['n'])}, none with an "
             f"operation, {p[ch10.INDIRECT]['employees']} employees, {p[ch10.INDIRECT]['first']} to "
             f"{p[ch10.INDIRECT]['last']}; NonManufacturing: {num(p[ch10.NONMFG]['n'])}, none, "
             f"{p[ch10.NONMFG]['employees']} employees, {p[ch10.NONMFG]['first']} to {p[ch10.NONMFG]['last']}. "
             f"Expected: indirect and non-manufacturing time has no operation by design, and the manufacturing time "
             f"starts in the January {d.F} start-up month. Not expected: {word(n['no_op'])} direct entries without an "
             f"operation (Exercise 9.6), and the end on {n['end_text']}, before the year ends (the open pay periods "
             f"of Tutorial 10.3), a timeliness limit on any test of the year's labor. Indirect time ends "
             f"{n['indirect_gap']} earlier ({p[ch10.INDIRECT]['last']}), so the last records hold only direct and "
             f"non-manufacturing time.")
    wo = n["work_orders"]
    s.answer("Requirement (6), findings and dispositions",
             f"1. Ledger rows without a payroll payment: {n['n_orphans']} GLEntry rows of type PayrollPayment point "
             f"to no payment: {pair_text}; each pair a {money(n['amount'])} debit \"{n['debit_text']}\" and credit "
             f"\"{n['credit_text']}\", {money(n['total'])} each side. Integrity failure: postings without a supporting "
             f"document. Follow-up: ask payroll for the payment records and bank evidence, and confirm whether cash "
             f"was disbursed.\n\n"
             f"2. Customers without orders: {n['n_customers'].lower()}, all inactive. Expected condition: customers "
             f"set up and never used or deactivated. Follow-up: none beyond confirming they stay inactive.\n\n"
             f"3. Work orders without operations: {wording(wo)}, all Closed, yet {n['wo_labor']} direct time entries "
             f"were recorded on them. Process exception: a closed work order should have operations. Follow-up: ask "
             f"production how they were closed without a routing, and what the time recorded on them was for.\n\n"
             f"4. Orphaned operation keys: {n['orphans']} Direct Manufacturing entries "
             f"({num(n['orphan_hours'], 2)} hours) carry a WorkOrderOperationID that matches no operation, "
             + ", ".join(f"{k} on {w}" for w, k in n["orphan_by_wo"])
             + ", the work orders of finding 3. An orphaned key, not a missing one, so an IS NULL test alone would "
             f"miss them (the {word(n['no_op'])} entries with no key at all are Exercise 9.6). Integrity failure. "
             f"Follow-up: correct the keys or the operations, and find out how the time system accepted an "
             f"operation that does not exist.")


# --- Exercise 10.6 -------------------------------------------------------------------------------

def ex6(b: Build) -> None:
    d = b.data
    n = ch10.ex6(d, claim)
    end = n["end"]
    matches = n["matches"]
    approved = dict(d.q("SELECT SupplierID, IsApproved FROM Supplier"))
    invoices = {r[0]: r[1:] for r in n["invoices"]}
    payments = {r[0]: r[1:] for r in n["payments"]}
    big, capital = n["big"], n["capital"]
    customers = d.q("SELECT CustomerID, CustomerName, CustomerSegment FROM Customer WHERE CustomerName IN "
                    "(SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1) "
                    "ORDER BY CustomerName, CustomerID")
    s = b.script("Ex 10.6.sql", "suppliers that share an employee's address",
                 f"{n['n_word']} address matches; invoices and payments totaled apart; "
                 f"{word(len(n['shared']))} shared customer names")

    s.query("Requirement (1): suppliers whose address is an employee's",
            f"Population: Supplier and Employee; expected: {n['n_word']} matches, all approved",
            """
            SELECT s.SupplierID, s.SupplierName, s.IsApproved,
                e.EmployeeID, e.EmployeeName, e.JobTitle, s.Address
            FROM Supplier AS s
                INNER JOIN Employee AS e ON e.Address = s.Address
            ORDER BY s.SupplierID;
            """,
            [Check("matches", [(m["supplier"], m["employee"]) for m in matches],
                   lambda r: list(zip(r.col("SupplierID"), r.col("EmployeeID"))))]
            + [Check(f"supplier {m['supplier']}", (m["name"], m["title"], approved[m["supplier"]]),
                     lambda r, i=m["supplier"]: (lambda w: (w["SupplierName"], w["JobTitle"], w["IsApproved"]))(
                         r.where(SupplierID=i)))
               for m in matches])

    s.query("Requirement (1): addresses shared by more than one employee",
            "Population: Employee; expected: no rows, so each supplier matches one employee",
            """
            SELECT Address, COUNT(*) AS Employees
            FROM Employee
            GROUP BY Address
            HAVING COUNT(*) > 1;
            """,
            [Check("shared employee addresses", 0, len)])

    s.query(f"Requirement (2): invoices and payments of the matching suppliers through {end}",
            f"Population: PurchaseInvoice and DisbursementPayment dated through {end}; expected: "
            f"{len(matches)} suppliers, each table totaled on its own",
            f"""
            SELECT s.SupplierID, s.SupplierName,
                inv.Invoices, inv.Invoiced, pay.Payments, pay.Paid
            FROM Supplier AS s
                INNER JOIN Employee AS e ON e.Address = s.Address
                INNER JOIN (
                    SELECT SupplierID, COUNT(*) AS Invoices,
                        ROUND(SUM(GrandTotal), 2) AS Invoiced
                    FROM PurchaseInvoice
                    WHERE InvoiceDate <= '{end}'
                    GROUP BY SupplierID
                ) AS inv ON inv.SupplierID = s.SupplierID
                INNER JOIN (
                    SELECT SupplierID, COUNT(*) AS Payments,
                        ROUND(SUM(Amount), 2) AS Paid
                    FROM DisbursementPayment
                    WHERE PaymentDate <= '{end}'
                    GROUP BY SupplierID
                ) AS pay ON pay.SupplierID = s.SupplierID
            ORDER BY s.SupplierID;
            """,
            [Check("suppliers", [m["supplier"] for m in matches], lambda r: r.col("SupplierID"))]
            + [c for m in matches for c in (
                Check(f"supplier {m['supplier']} invoices", (invoices[m["supplier"]][0],
                                                             round(invoices[m["supplier"]][1], 2)),
                      lambda r, i=m["supplier"]: (lambda w: (w["Invoices"], w["Invoiced"]))(r.where(SupplierID=i))),
                Check(f"supplier {m['supplier']} payments", (payments[m["supplier"]][0],
                                                             round(payments[m["supplier"]][1], 2)),
                      lambda r, i=m["supplier"]: (lambda w: (w["Payments"], w["Paid"]))(r.where(SupplierID=i))))])

    first = n["first"]
    s.query(f"Requirement (2): the fan-out of joining invoices to payments, supplier {first}",
            f"Population: supplier {first}'s invoices and payments through {end}; expected: "
            f"{num(n['fan'])} rows, not {invoices[first][0]} or {payments[first][0]}",
            f"""
            SELECT COUNT(*) AS JoinedRows
            FROM PurchaseInvoice AS pi
                INNER JOIN DisbursementPayment AS dp
                    ON dp.SupplierID = pi.SupplierID
            WHERE pi.SupplierID = {first} AND pi.InvoiceDate <= '{end}'
                AND dp.PaymentDate <= '{end}';
            """,
            [Check("joined rows", n["fan"], lambda r: r.value()),
             Check("invoices times payments", invoices[first][0] * payments[first][0], lambda r: r.value())])

    s.query(f"Requirement (2): supplier {big['id']}'s invoices still open at {end}",
            f"Population: supplier {big['id']}'s invoices through {end}; expected: {money(big['open'])} open, "
            f"including {wording([c['number'] for c in capital])}",
            f"""
            SELECT pi.InvoiceNumber, pi.InvoiceDate, pi.GrandTotal,
                ROUND(pi.GrandTotal - COALESCE(p.Paid, 0), 2) AS OpenAmount
            FROM PurchaseInvoice AS pi
                LEFT JOIN (
                    SELECT PurchaseInvoiceID, SUM(Amount) AS Paid
                    FROM DisbursementPayment
                    WHERE PaymentDate <= '{end}'
                    GROUP BY PurchaseInvoiceID
                ) AS p ON p.PurchaseInvoiceID = pi.PurchaseInvoiceID
            WHERE pi.SupplierID = {big['id']} AND pi.InvoiceDate <= '{end}'
                AND pi.GrandTotal - COALESCE(p.Paid, 0) > 0.005
            ORDER BY OpenAmount DESC;
            """,
            [Check("open amount", big["open"], lambda r: r.total("OpenAmount"), 0.05)]
            + [Check(f"{c['number']} open in full", c["total"],
                     lambda r, c=c: r.where(InvoiceNumber=c["number"])["OpenAmount"]) for c in capital])

    s.query("Requirement (3): customer names shared by more than one CustomerID",
            f"Population: Customer; expected: {wording([x['name'] for x in n['shared']])}",
            """
            SELECT CustomerName, COUNT(*) AS Customers
            FROM Customer
            GROUP BY CustomerName
            HAVING COUNT(*) > 1
            ORDER BY CustomerName;
            """,
            [Check("names", [x["name"] for x in n["shared"]], lambda r: r.col("CustomerName")),
             Check("customers per name", [len(x["customers"]) for x in n["shared"]], lambda r: r.col("Customers"))])

    s.query("Requirement (3): those customers with their segments",
            f"Population: Customer, shared names; expected: {len(customers)} customers",
            """
            SELECT CustomerID, CustomerName, CustomerSegment, City, Region,
                IsActive
            FROM Customer
            WHERE CustomerName IN (
                SELECT CustomerName
                FROM Customer
                GROUP BY CustomerName
                HAVING COUNT(*) > 1
            )
            ORDER BY CustomerName, CustomerID;
            """,
            [Check("customers", [(c, nm, sg) for c, nm, sg in customers],
                   lambda r: list(zip(r.col("CustomerID"), r.col("CustomerName"), r.col("CustomerSegment"))))])

    rows = "; ".join(f"supplier {m['supplier']} {m['name']} with employee {m['employee']} ({m['title']})"
                     for m in matches)
    money_rows = "; ".join(f"supplier {m['supplier']}: {invoices[m['supplier']][0]} invoices {money(invoices[m['supplier']][1])}, "
                           f"{payments[m['supplier']][0]} payments {money(payments[m['supplier']][1])}" for m in matches)
    active = dict(d.q("SELECT CustomerID, IsActive FROM Customer"))
    ordering = {r[0] for r in d.q("SELECT DISTINCT CustomerID FROM SalesOrder")}
    shared = "; ".join(f"{x['name']}, customers " + " and ".join(
        f"{c['id']} ({c['segment']}{'' if active[c['id']] else ', inactive'}"
        f"{'' if c['id'] in ordering else ', no orders'})" for c in x["customers"]) for x in n["shared"])
    s.answer("Requirement (4)",
             f"The join compares every supplier address with every employee address exactly, character for "
             f"character, so it cannot overlook a match the eye would miss in two long lists, and it can be rerun on "
             f"next year's data. It cannot find addresses written differently (an abbreviation, a suite number, a "
             f"typing error; Chapter 2), so a fuzzy comparison of standardized text is the next step, and a match "
             f"does not prove a relationship: a shared address may be a coincidence, an office building, or a "
             f"family member, and only evidence outside the database can tell.")
    s.answer("Requirement (5), memo to the audit senior",
             f"Findings: {n['n_word']} approved suppliers share an address with an employee: {rows}. No two "
             f"employees share an address, so each supplier matches one employee. Through {end}: {money_rows}. "
             f"Invoices and payments were totaled separately and then joined by supplier, because joining the two "
             f"tables directly repeats each invoice once per payment ({num(n['fan'])} rows for supplier {first}). "
             f"Supplier {big['id']} has {money(big['open'])} of invoices still open at {end}, including "
             + " and ".join(f"{c['number']} ({money(c['total'])})" for c in capital)
             + ", the invoices the Debt Reclass entries moved to notes payable (Chapter 8). Shared customer names: "
             f"{shared}.\n\n"
             f"Recommended procedures: obtain the vendor setup records of the {n['n_word']} suppliers (who requested "
             f"and approved each, and on what evidence); compare them with the employees' conflict-of-interest "
             f"declarations; check whether the matching employees can request, approve, or receive purchases from "
             f"these suppliers; vouch a sample of the suppliers' invoices to receipts; and confirm whether the shared "
             f"customer names are different customers or duplicates in the master file.")


EXERCISES = [("10.1", ex1), ("10.2", ex2), ("10.3", ex3), ("10.4", ex4), ("10.5", ex5), ("10.6", ex6)]
