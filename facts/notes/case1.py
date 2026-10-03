"""The Part I case's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

from notes import note

CASE = "cases/part-1-case.qmd"
GROUP = "Furniture"


def quarter(year: int, q: int) -> tuple[str, str]:
    ends = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
    return f"{year}-{3 * q - 2:02d}-01", f"{year}-{ends[q]}"


def quarter_of(date: str) -> tuple[int, int]:
    return int(date[:4]), (int(date[5:7]) - 1) // 3 + 1


def accounts(d):
    """The Furniture items' revenue, COGS, and inventory accounts (each must be one account)."""
    ids = d.q("SELECT COUNT(DISTINCT RevenueAccountID), MIN(RevenueAccountID), COUNT(DISTINCT COGSAccountID), "
              "MIN(COGSAccountID), COUNT(DISTINCT InventoryAccountID), MIN(InventoryAccountID) FROM Item "
              "WHERE ItemGroup = ?", GROUP)[0]
    acct = lambda i: dict(zip(("id", "number", "name"), d.q(
        "SELECT AccountID, AccountNumber, AccountName FROM Account WHERE AccountID = ?", i)[0]))
    return ids, acct(ids[1]), acct(ids[3]), acct(ids[5])


def cardinality(d, parent, pk, child, fk):
    """Rows per parent (min, max) and child rows whose key is blank or matches no parent."""
    lo, hi = d.q(f"SELECT MIN(n), MAX(n) FROM (SELECT p.{pk}, COUNT(c.{fk}) AS n FROM {parent} p "
                 f"LEFT JOIN {child} c ON c.{fk} = p.{pk} GROUP BY p.{pk})")[0]
    orphans = d.one(f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p ON p.{pk} = c.{fk} WHERE p.{pk} IS NULL")
    return dict(parent=parent, child=child, key=fk, lo=1 if lo >= 1 else 0, hi=hi, orphans=orphans)


@note("case1.r2", CASE)
def r2(d, claim):
    items = d.one("SELECT COUNT(*) FROM Item WHERE ItemGroup = ?", GROUP)
    ids, revenue, cogs, inventory = accounts(d)
    claim(ids[0] == 1 and ids[2] == 1 and ids[4] == 1,
          "every Furniture item has the same revenue, COGS, and inventory account")
    joins = [cardinality(d, "SalesInvoice", "SalesInvoiceID", "SalesInvoiceLine", "SalesInvoiceID"),
             cardinality(d, "Item", "ItemID", "SalesInvoiceLine", "ItemID"),
             cardinality(d, "Shipment", "ShipmentID", "ShipmentLine", "ShipmentID"),
             cardinality(d, "Item", "ItemID", "ShipmentLine", "ItemID"),
             cardinality(d, "Account", "AccountID", "GLEntry", "AccountID")]
    for j in joins:
        claim(j["orphans"] == 0, f"every {j['child']} row has a matching {j['parent']} ({j['key']})")
        claim(j["hi"] > 1, f"a {j['parent']} can have many {j['child']} rows")
    # returns: the cost side posts by product line, the revenue side to one shared account
    ret = {a: (dr, cr) for a, dr, cr in d.q(
        "SELECT AccountID, SUM(Debit > 0), SUM(Credit > 0) FROM GLEntry "
        "WHERE SourceDocumentType = 'SalesReturn' AND AccountID IN (?, ?) GROUP BY 1", cogs["id"], inventory["id"])}
    claim(ret.get(cogs["id"], (0, 0))[0] == 0 and ret.get(cogs["id"], (0, 0))[1] > 0,
          f"SalesReturn postings to {cogs['number']} are credits (they reduce COGS)")
    claim(ret.get(inventory["id"], (0, 0))[1] == 0 and ret.get(inventory["id"], (0, 0))[0] > 0,
          f"SalesReturn postings to {inventory['number']} are debits (they restore inventory)")
    memo = d.q("SELECT DISTINCT a.AccountID, a.AccountNumber, a.AccountName FROM GLEntry g JOIN Account a "
               "ON a.AccountID = g.AccountID WHERE g.SourceDocumentType = 'CreditMemo' "
               "AND a.AccountSubType = 'Contra Revenue'")
    claim(len(memo) == 1, "CreditMemo postings go to one contra-revenue account")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'CreditMemo' AND AccountID IN "
                "(SELECT RevenueAccountID FROM Item WHERE RevenueAccountID IS NOT NULL)") == 0,
          "no CreditMemo posts to a product line's revenue account (the revenue side is not by product line)")
    groups = d.one("SELECT COUNT(DISTINCT t.ItemGroup) FROM CreditMemoLine l JOIN Item t ON t.ItemID = l.ItemID")
    claim(groups > 1, "the credit memos (and so the returns account) span several product lines")
    discounts = d.account("4070")
    discount_name = d.one("SELECT AccountName FROM Account WHERE AccountID = ?", discounts)
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", discounts) == 0,
          f"account 4070 {discount_name} has no postings")
    return dict(items=items, revenue=revenue, cogs=cogs, inventory=inventory, joins=joins,
                returns=dict(number=memo[0][1], name=memo[0][2]), discounts=discount_name)


def before_shipment(d):
    """Invoices dated before their order's first shipment, with their Furniture lines and posting date."""
    return d.q("SELECT i.InvoiceNumber, i.InvoiceDate, s.first_ship, "
               "(SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item t ON t.ItemID = l.ItemID "
               " WHERE l.SalesInvoiceID = i.SalesInvoiceID AND t.ItemGroup = ?), "
               "(SELECT MIN(g.PostingDate) FROM GLEntry g WHERE g.SourceDocumentType = 'SalesInvoice' "
               " AND g.SourceDocumentID = i.SalesInvoiceID) "
               "FROM SalesInvoice i JOIN (SELECT SalesOrderID, MIN(ShipmentDate) AS first_ship FROM Shipment "
               "GROUP BY 1) s ON s.SalesOrderID = i.SalesOrderID WHERE i.InvoiceDate < s.first_ship "
               "ORDER BY i.InvoiceNumber", GROUP)


@note("case1.r3", CASE)
def r3(d, claim):
    last_invoice = d.one("SELECT MAX(InvoiceDate) FROM SalesInvoice")
    last_gl = d.one("SELECT MAX(PostingDate) FROM GLEntry")
    claim(last_invoice == f"{d.C}-12-31", f"invoices run through the end of fiscal {d.C}, so its Q4 is complete")
    after = [r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE PostingDate > ?", last_invoice)]
    claim(after == ["DisbursementPayment"], "the GL rows after the last invoice are only DisbursementPayment rows")
    paid = d.one("SELECT MAX(i.InvoiceDate) FROM GLEntry g JOIN DisbursementPayment p ON p.DisbursementID = "
                 "g.SourceDocumentID JOIN PurchaseInvoice i ON i.PurchaseInvoiceID = p.PurchaseInvoiceID "
                 "WHERE g.SourceDocumentType = 'DisbursementPayment' AND g.PostingDate > ?", last_invoice)
    claim(paid is not None and paid <= last_invoice, "the later payments are for invoices of the prior fiscal year")
    rows = before_shipment(d)
    furniture = [r for r in rows if r[3] > 0]
    window = (quarter(d.C, 3)[0], quarter(d.C, 4)[1])
    claim(furniture and not any(window[0] <= x <= window[1] for r in furniture for x in (r[1], r[2], r[4])),
          f"none of the Furniture invoices is dated, shipped, or posted in {d.C} Q3 or Q4")
    claim(all(quarter_of(r[1]) == quarter_of(r[2]) for r in furniture),
          "each Furniture invoice is dated in the same quarter as its order's first shipment")
    claim(d.one("SELECT COUNT(*) FROM (SELECT CustomerName FROM Customer GROUP BY 1 HAVING COUNT(*) > 1)") > 0,
          "some customers share a name")
    blank = d.q("SELECT ItemGroup, SupplyMode FROM Item WHERE ListPrice IS NULL")
    claim(blank and not any(g == GROUP for g, _ in blank), "no Furniture item has a blank list price")
    claim(all(m == "Purchased" for _, m in blank), "every item with a blank list price is purchased")
    return dict(last_invoice=last_invoice, last_gl=last_gl, invoices=len(rows), furniture=[r[0] for r in furniture])


def quarters(d):
    """The Furniture sub-ledger and ledger totals of the current year's Q3 and Q4."""
    _, revenue, cogs, _ = accounts(d)
    out = {}
    for q in (3, 4):
        a, b = quarter(d.C, q)
        lines = d.q("SELECT ROUND(SUM(l.LineTotal), 2), SUM(l.Quantity * t.StandardCost) FROM SalesInvoiceLine l "
                    "JOIN SalesInvoice i ON i.SalesInvoiceID = l.SalesInvoiceID JOIN Item t ON t.ItemID = l.ItemID "
                    "WHERE t.ItemGroup = ? AND i.InvoiceDate BETWEEN ? AND ?", GROUP, a, b)[0]
        shipped = d.one("SELECT ROUND(SUM(sl.ExtendedStandardCost), 2) FROM ShipmentLine sl JOIN Shipment s "
                        "ON s.ShipmentID = sl.ShipmentID JOIN Item t ON t.ItemID = sl.ItemID "
                        "WHERE t.ItemGroup = ? AND s.ShipmentDate BETWEEN ? AND ?", GROUP, a, b)
        by_source = lambda account, sign: {s: v for s, v in d.q(
            f"SELECT SourceDocumentType, ROUND({sign} * (SUM(Debit) - SUM(Credit)), 2) FROM GLEntry "
            f"WHERE AccountID = ? AND PostingDate BETWEEN ? AND ? GROUP BY 1", account, a, b)}
        closes = d.q(f"SELECT AccountID, ROUND(SUM(Debit), 2), ROUND(SUM(Credit), 2) FROM GLEntry WHERE AccountID IN (?, ?) "
                     f"AND PostingDate BETWEEN ? AND ? AND NOT ({d.no_closes()}) GROUP BY 1", revenue["id"], cogs["id"], a, b)
        out[q] = dict(lines=lines[0], std=lines[1], shipped=shipped, rev=by_source(revenue["id"], -1),
                      cogs=by_source(cogs["id"], 1), closes={r[0]: (r[1], r[2]) for r in closes})
    return revenue, cogs, out


@note("case1.r4", CASE)
def r4(d, claim):
    revenue, cogs, qs = quarters(d)
    for q in (3, 4):
        claim(abs(qs[q]["rev"].get("SalesInvoice", 0) - qs[q]["lines"]) < 0.005,
              f"Q{q}: SalesInvoice postings to {revenue['number']} equal the Furniture invoice lines")
        claim(abs(qs[q]["cogs"].get("Shipment", 0) - qs[q]["shipped"]) < 0.005,
              f"Q{q}: Shipment postings to {cogs['number']} equal the Furniture shipment lines at standard cost")
    sources = {r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ?", cogs["id"])}
    claim(sources == {"Shipment", "SalesReturn", "JournalEntry"},
          f"the sources posting to {cogs['number']} are Shipment, SalesReturn, and JournalEntry")
    other = d.one(f"SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'JournalEntry' "
                  f"AND {d.no_closes()}", cogs["id"])
    claim(other == 0, f"the only journal entries to {cogs['number']} are the year-end closes")
    claim(qs[3]["closes"] == {} and set(qs[4]["closes"]) <= {revenue["id"], cogs["id"]} and cogs["id"] in qs[4]["closes"],
          f"the close posts to {cogs['number']} in Q4 (at year-end) and not in Q3")
    claim(all(qs[q]["cogs"].get("SalesReturn", 0) < 0 for q in (3, 4)), "SalesReturn postings reduce COGS in both quarters")
    return dict(revenue=revenue, cogs=cogs,
                q3=dict(lines=qs[3]["lines"], shipped=qs[3]["shipped"], returns=qs[3]["cogs"]["SalesReturn"]),
                q4=dict(lines=qs[4]["lines"], shipped=qs[4]["shipped"], returns=qs[4]["cogs"]["SalesReturn"]))


@note("case1.r5", CASE)
def r5(d, claim):
    revenue, cogs, qs = quarters(d)
    q3, q4 = qs[3], qs[4]
    rev_all, cogs_all = sum(q4["rev"].values()), sum(q4["cogs"].values())
    claim(rev_all < 0 and cogs_all < 0, "using all rows, Q4 Furniture revenue and COGS are negative (nonsense totals)")
    close = [e for e in d.closes_of(d.C) if d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber = ? "
                                                  "AND AccountID IN (?, ?)", e, revenue["id"], cogs["id"])]
    claim(len(close) == 1, f"one year-end close of {d.C} posts to the Furniture accounts")
    close = close[0]
    entry_type, posted = d.q("SELECT EntryType, PostingDate FROM JournalEntry WHERE EntryNumber = ?", close)[0]
    (rev_dr, rev_cr), (cogs_dr, cogs_cr) = q4["closes"][revenue["id"]], q4["closes"][cogs["id"]]
    claim(rev_cr == 0 and cogs_dr == 0, f"{close} only debits {revenue['number']} and only credits {cogs['number']}")
    claim(set(q4["rev"]) == {"SalesInvoice", "JournalEntry"} and set(q4["cogs"]) == {"Shipment", "SalesReturn", "JournalEntry"}
          and set(q3["rev"]) == {"SalesInvoice"} and set(q3["cogs"]) == {"Shipment", "SalesReturn"},
          "apart from the close, the quarters' rows are invoices, shipments, and returns (shipments less returns)")
    margin = lambda r, c: (r - c) / r
    naive_q3 = margin(sum(q3["rev"].values()), sum(q3["cogs"].values()))
    naive_q4 = margin(rev_all, cogs_all)
    rev4, cogs4 = rev_all + rev_dr, cogs_all + cogs_cr
    m3, m4 = margin(q3["rev"]["SalesInvoice"], q3["cogs"]["Shipment"] + q3["cogs"]["SalesReturn"]), margin(rev4, cogs4)
    claim(abs(naive_q4 - naive_q3) < 0.005, "the naive Q4 margin is almost identical to Q3's (within half a point)")
    claim(m4 < m3, "excluding the close, the margin falls from Q3 to Q4")
    s3, s4 = margin(q3["lines"], q3["std"]), margin(q4["lines"], q4["std"])
    claim(s4 < s3, "the sub-ledger margin at standard cost also falls")
    return dict(rev_all=rev_all, cogs_all=cogs_all, close=close, entry_type=entry_type, posted=posted,
                revenue=revenue, cogs=cogs, close_debit=rev_dr, close_credit=cogs_cr, naive_q4=naive_q4, naive_q3=naive_q3,
                rev4=rev4, cogs4=cogs4, m3=m3, m4=m4, s3=s3, s4=s4)
