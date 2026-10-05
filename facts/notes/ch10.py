"""Chapter 10's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

import re
from datetime import date

from notes import note

EXERCISES = "chapters/10-joining-and-summarizing/_exercises.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
# Book constants: the revenue accounts Exercise 10.1 reconciles (its requirement (3)), and the book's traced sale
# (Tutorial 3.2, named in Exercise 10.2's text), identified by its SalesInvoiceID; everything else about it is queried.
REVENUE_ACCOUNTS = ("4010", "4020", "4030", "4040", "4080")
TRACED_SALE_ID = 7947
DIRECT, INDIRECT, NONMFG = "Direct Manufacturing", "Indirect Manufacturing", "NonManufacturing"


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def year_range(year: int) -> tuple[str, str]:
    return f"{year}-01-01", f"{year}-12-31"


def anomalies(d, kind: str) -> set | None:
    """The primary keys the generator's AnomalyLog lists for an anomaly type; None if there is no
    support workbook beside the dataset."""
    keys = d.anomalies(kind)
    return None if keys is None else set(keys)


# --- Exercise 10.1 -------------------------------------------------------------------------------

@note("ch10.ex1", EXERCISES)
def ex1(d, claim):
    first, last = year_range(d.C)
    rows = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID "
                 "JOIN Item i ON i.ItemID = l.ItemID JOIN Customer c ON c.CustomerID = s.CustomerID")
    claim(rows == d.one("SELECT COUNT(*) FROM SalesInvoiceLine"), "the four-table join returns one row per invoice line")
    groups = d.q("SELECT i.ItemGroup, ROUND(SUM(l.LineTotal), 2) FROM SalesInvoiceLine l JOIN SalesInvoice s "
                 "ON s.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
                 "WHERE s.InvoiceDate BETWEEN ? AND ? GROUP BY 1 ORDER BY 2 DESC", first, last)
    lines_total = round(sum(a for _, a in groups), 2)
    ids = ",".join(str(d.account(n)) for n in REVENUE_ACCOUNTS)
    ledger = d.q(f"SELECT a.AccountNumber, ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g JOIN Account a "
                 f"ON a.AccountID = g.AccountID WHERE g.SourceDocumentType = 'SalesInvoice' AND g.FiscalYear = ? "
                 f"AND g.AccountID IN ({ids}) GROUP BY 1 ORDER BY 1", d.C)
    ledger_total = round(sum(a for _, a in ledger), 2)
    # The invoices dated before the fiscal year whose revenue posts in it (requirement (4)).
    cutoff_rows = d.q(f"SELECT s.InvoiceNumber, s.InvoiceDate, g.PostingDate, a.AccountNumber, g.Credit - g.Debit "
                      f"FROM GLEntry g JOIN SalesInvoice s ON s.SalesInvoiceID = g.SourceDocumentID "
                      f"JOIN Account a ON a.AccountID = g.AccountID WHERE g.SourceDocumentType = 'SalesInvoice' "
                      f"AND g.FiscalYear = ? AND g.AccountID IN ({ids}) AND s.InvoiceDate < ? "
                      f"ORDER BY s.InvoiceNumber, a.AccountNumber", d.C, first)
    cutoff = []
    for number, dated, posted, account, amount in cutoff_rows:
        if not cutoff or cutoff[-1]["number"] != number:
            cutoff.append(dict(number=number, date=dated, posted=posted, accounts={}))
        cutoff[-1]["accounts"][account] = cutoff[-1]["accounts"].get(account, 0.0) + amount
    for c in cutoff:
        c["accounts"] = sorted(c["accounts"].items())
    by_account = {}
    for _, _, _, account, amount in cutoff_rows:
        by_account[account] = by_account.get(account, 0.0) + amount
    diff = round(ledger_total - lines_total, 2)
    claim(abs(diff - sum(by_account.values())) < 0.005, "the difference is exactly the invoices dated before the year")
    # Each account against its item groups (Item.RevenueAccountID), so the difference is the cutoff invoices and nothing else.
    by_group_account = dict(d.q(f"SELECT a.AccountNumber, ROUND(SUM(l.LineTotal), 2) FROM SalesInvoiceLine l "
                                f"JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID JOIN Item i ON i.ItemID = l.ItemID "
                                f"JOIN Account a ON a.AccountID = i.RevenueAccountID WHERE s.InvoiceDate BETWEEN ? AND ? "
                                f"GROUP BY 1", first, last))
    claim(all(abs(amount - by_group_account.get(account, 0.0) - by_account.get(account, 0.0)) < 0.005
              for account, amount in ledger), "account by account, the ledger is the lines plus the cutoff invoices")
    claim(len({c["posted"] for c in cutoff}) == 1, "the cutoff invoices are all posted on one date")
    claim(all(c["date"][:4] == str(d.P) and int(c["date"][5:7]) >= 10 for c in cutoff),
          f"the cutoff invoices are dated in late {d.P}")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceLineID IS NOT NULL", d.account("4050")) == 0,
          "freight postings to 4050 carry no SourceLineID (no line to match)")
    return dict(rows=rows, groups=groups, lines_total=lines_total, ledger=ledger, ledger_total=ledger_total, diff=diff,
                n_cutoff=word(len(cutoff)), posted=cutoff[0]["posted"], cutoff=cutoff)


# --- Exercise 10.2 -------------------------------------------------------------------------------

@note("ch10.ex2", EXERCISES)
def ex2(d, claim):
    first, last = year_range(d.C)
    number, dated, customer, name, subtotal, freight, tax, grand = d.q(
        "SELECT s.InvoiceNumber, s.InvoiceDate, s.CustomerID, c.CustomerName, s.SubTotal, s.FreightAmount, s.TaxAmount, "
        "s.GrandTotal FROM SalesInvoice s JOIN Customer c ON c.CustomerID = s.CustomerID WHERE s.SalesInvoiceID = ?",
        TRACED_SALE_ID)[0]
    gl = d.q("SELECT g.GLEntryID, g.PostingDate, a.AccountNumber, a.AccountName, g.Debit, g.Credit, g.SourceLineID "
             "FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.SourceDocumentType = 'SalesInvoice' "
             "AND g.SourceDocumentID = ? ORDER BY g.GLEntryID", TRACED_SALE_ID)
    rows = [dict(id=r[0], side="debit" if r[4] else "credit", amount=r[4] or r[5], number=r[2], name=r[3], line=r[6])
            for r in gl]
    debits, credits = sum(r[4] for r in gl), sum(r[5] for r in gl)
    claim(len({r[1] for r in gl}) == 1 and gl[0][1] == dated, "all the invoice's rows post on its invoice date")
    claim(all(bool(r[4]) != bool(r[5]) for r in gl), "each row is either a debit or a credit")
    claim(abs(debits - credits) < 0.005 and abs(debits - grand) < 0.005, "debits equal credits equal the GrandTotal")
    claim(abs(subtotal + freight + tax - grand) < 0.005, "SubTotal, freight, and tax add up to the GrandTotal")
    with_line = [r for r in gl if r[6] is not None]
    claim(len(with_line) == 1, "one posting (the revenue posting) carries a SourceLineID")
    line_id = with_line[0][6]
    item, qty, price = d.q("SELECT i.ItemName, l.Quantity, l.UnitPrice FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID "
                           "WHERE l.SalesInvoiceLineID = ? AND l.SalesInvoiceID = ?", line_id, TRACED_SALE_ID)[0]
    tested = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ? "
                   "AND SourceLineID IS NOT NULL", d.C)
    orphans = d.one("SELECT COUNT(*) FROM GLEntry g LEFT JOIN SalesInvoiceLine l ON l.SalesInvoiceLineID = g.SourceLineID "
                    "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.FiscalYear = ? AND g.SourceLineID IS NOT NULL "
                    "AND l.SalesInvoiceLineID IS NULL", d.C)
    claim(orphans == 0, "no SourceLineID of the year's SalesInvoice postings is orphaned")
    header = {r[0] for r in d.q("SELECT DISTINCT a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                                "WHERE g.SourceDocumentType = 'SalesInvoice' AND g.FiscalYear = ? AND g.SourceLineID IS NULL",
                                d.C)}
    claim({str(a) for a in header} == {"1020", "4050", "2050"},
          "the rows without a SourceLineID are exactly the receivable, freight, and tax rows")
    trap_rows, trap_types = d.q("SELECT COUNT(*), COUNT(DISTINCT SourceDocumentType) FROM GLEntry WHERE SourceDocumentID = ?",
                                TRACED_SALE_ID)[0]
    return dict(inv=dict(number=number, id=TRACED_SALE_ID, date=dated, customer=customer, customer_name=name,
                         subtotal=subtotal, freight=freight, tax=tax),
                n_rows=word(len(gl)), posted=gl[0][1], rows=rows, debits=debits, credits=credits,
                line=dict(id=line_id, name=item, qty=f"{qty:,.0f}" if float(qty).is_integer() else f"{qty:,.2f}", price=price),
                tested=tested,
                trap_rows=trap_rows, trap_types=trap_types)


# --- Exercise 10.3 -------------------------------------------------------------------------------

@note("ch10.ex3", EXERCISES)
def ex3(d, claim):
    orders, customers, avg = d.q("SELECT COUNT(*), COUNT(DISTINCT CustomerID), AVG(OrderTotal) FROM SalesOrder")[0]
    without = d.one("SELECT COUNT(*) FROM Customer c WHERE NOT EXISTS (SELECT 1 FROM SalesOrder o WHERE o.CustomerID = c.CustomerID)")
    by_id = d.q("SELECT c.CustomerID, c.CustomerName, c.CustomerSegment, COUNT(*), AVG(o.OrderTotal) FROM SalesOrder o "
                "JOIN Customer c ON c.CustomerID = o.CustomerID GROUP BY c.CustomerID ORDER BY 5 DESC")
    top = [dict(id=r[0], name=r[1], n=r[3], avg=r[4]) for r in by_id[:3]]
    names = d.one("SELECT COUNT(DISTINCT c.CustomerName) FROM SalesOrder o JOIN Customer c ON c.CustomerID = o.CustomerID")
    claim(names == len(by_id) - 1, "grouping by name returns one row fewer")
    shared = [r[0] for r in d.q("SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1 ORDER BY 1")]
    groups = {n: [r for r in d.q("SELECT c.CustomerID, c.CustomerSegment, COUNT(o.SalesOrderID), AVG(o.OrderTotal), "
                                 "SUM(o.OrderTotal) FROM Customer c LEFT JOIN SalesOrder o ON o.CustomerID = c.CustomerID "
                                 "WHERE c.CustomerName = ? GROUP BY c.CustomerID ORDER BY c.CustomerID", n)] for n in shared}
    merging = [n for n in shared if sum(1 for r in groups[n] if r[2] > 0) > 1]
    staying = [n for n in shared if n not in merging]
    claim(len(merging) == 1 and len(groups[merging[0]]) == 2, "one shared name merges, and it belongs to two customers")
    claim(len(staying) == 1 and len(groups[staying[0]]) == 2, "one other name is shared by two customers")
    ordering = [r for r in groups[staying[0]] if r[2] > 0]
    claim(len(ordering) == 1, "only one of the other pair has orders")
    m = groups[merging[0]]
    merged = dict(name=merging[0], customers=[dict(id=r[0], segment=r[1], n=r[2], avg=r[3]) for r in m],
                  n=sum(r[2] for r in m), avg=sum(r[4] for r in m) / sum(r[2] for r in m))
    segments = d.q("SELECT c.CustomerSegment, COUNT(*), AVG(o.OrderTotal) FROM SalesOrder o JOIN Customer c "
                   "ON c.CustomerID = o.CustomerID GROUP BY 1 ORDER BY 3 DESC")
    return dict(orders=orders, customers=customers, without=without, avg=avg, top=top, merged=merged,
                unmerged=dict(name=staying[0], ordering=ordering[0][0]), segments=segments)


# --- Exercise 10.4 -------------------------------------------------------------------------------

VARIANCE = "Description LIKE '%purchase variance'"
LINES = ("FROM PurchaseInvoiceLine l JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = l.PurchaseInvoiceID "
         "JOIN PurchaseOrderLine pol ON pol.POLineID = l.POLineID")


@note("ch10.ex4", EXERCISES)
def ex4(d, claim):
    ppv = d.account("5060")
    first, last = year_range(d.C)
    gl = d.one(f"SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {VARIANCE}",
               ppv, d.C)
    claim(d.one(f"SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {VARIANCE} "
                f"AND SourceDocumentType <> 'PurchaseInvoice'", ppv, d.C) == 0,
          "every variance posting comes from a PurchaseInvoice")
    claim(d.one(f"SELECT COUNT(*) FROM GLEntry g JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = g.SourceDocumentID "
                f"WHERE g.AccountID = ? AND g.FiscalYear = ? AND g.{VARIANCE} AND substr(pi.InvoiceDate, 1, 4) <> ?",
                ppv, d.C, str(d.C)) == 0, "the year's variance postings are for invoices dated in the year")
    suppliers = d.q(f"SELECT s.SupplierID, s.SupplierName, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g "
                    f"JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = g.SourceDocumentID JOIN Supplier s "
                    f"ON s.SupplierID = pi.SupplierID WHERE g.AccountID = ? AND g.FiscalYear = ? "
                    f"AND g.SourceDocumentType = 'PurchaseInvoice' AND g.{VARIANCE} GROUP BY 1 ORDER BY 3 DESC", ppv, d.C)
    by_line = dict(d.q(f"SELECT pi.SupplierID, SUM(l.Quantity * (l.UnitCost - pol.UnitCost)) {LINES} "
                       f"WHERE pi.InvoiceDate BETWEEN ? AND ? GROUP BY 1", first, last))
    supplier_gap = max(abs(round(a, 2) - round(by_line.get(s, 0.0), 2)) for s, _, a in suppliers)
    claim(set(by_line) == {s for s, _, _ in suppliers}, "the ledger and the lines name the same suppliers")
    n, lines, above, below, at, low, high = d.q(
        f"SELECT COUNT(*), ROUND(SUM(l.Quantity * (l.UnitCost - pol.UnitCost)), 2), SUM(l.UnitCost > pol.UnitCost), "
        f"SUM(l.UnitCost < pol.UnitCost), SUM(l.UnitCost = pol.UnitCost), MIN(l.UnitCost / pol.UnitCost - 1), "
        f"MAX(l.UnitCost / pol.UnitCost - 1) {LINES} WHERE pi.InvoiceDate BETWEEN ? AND ?", first, last)[0]
    gap = round(gl - lines, 2)
    claim(0 < abs(gap) < 1, "the line-level total differs from the ledger by cents (rounding of each posting)")
    claim(low < 0 < high, "some lines are billed below and some above the order price")
    years = []
    for y in d.years:
        amount, totals, variance = d.q(f"SELECT SUM(l.Quantity * l.UnitCost), SUM(l.LineTotal), "
                                       f"SUM(l.Quantity * (l.UnitCost - pol.UnitCost)) {LINES} "
                                       f"WHERE pi.InvoiceDate BETWEEN ? AND ?", *year_range(y))[0]
        years.append(dict(year=y, amount=amount, variance=variance, rate=variance / amount, line_gap=abs(totals - amount)))
    claim(all(y["line_gap"] < 5 for y in years), "SUM(LineTotal) differs from the unrounded amount by a few dollars at most (rounding)")
    rates = [y["rate"] for y in years]
    claim(max(rates) - min(rates) < 0.0005, "the variance rate is steady (within 0.05 percentage points)")
    claim(all(a["amount"] < b["amount"] and a["variance"] < b["variance"] for a, b in zip(years, years[1:])),
          "the amount invoiced and the variance grow every year")
    others = dict(d.q(f"SELECT Description, SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                      f"AND NOT {VARIANCE} AND {d.no_closes()} GROUP BY 1", ppv, d.C))
    claim(set(others) == {"Record nonrecoverable purchase tax"}, "the rest of account 5060 is nonrecoverable purchase tax")
    return dict(gl=gl, top=[dict(id=s, name=nm, amount=a) for s, nm, a in suppliers[:5]], lines=lines, gap=abs(gap),
                supplier_gap=supplier_gap, n_lines=n, above=above, below=below, at=at, low=-low, high=high, years=years,
                line_gap_low=min(y["line_gap"] for y in years), line_gap_high=max(y["line_gap"] for y in years),
                tax=others.get("Record nonrecoverable purchase tax", 0.0))


# --- Exercise 10.5 -------------------------------------------------------------------------------

def long_date(iso: str) -> str:
    x = date.fromisoformat(iso)
    return f"{x.day} {MONTHS[x.month - 1]} {x.year}"


@note("ch10.ex5", EXERCISES)
def ex5(d, claim):
    profile = {r[0]: dict(n=r[1], ops=r[2], employees=r[3], first=r[4], last=r[5]) for r in d.q(
        "SELECT LaborType, COUNT(*), COUNT(WorkOrderOperationID), COUNT(DISTINCT EmployeeID), MIN(WorkDate), MAX(WorkDate) "
        "FROM LaborTimeEntry GROUP BY 1")}
    claim(set(profile) == {DIRECT, INDIRECT, NONMFG}, "LaborType has the three values the profile lists")
    claim(profile[INDIRECT]["ops"] == 0 and profile[NONMFG]["ops"] == 0,
          "no indirect or non-manufacturing entry has an operation")
    claim(all(profile[t]["first"][:7] == f"{d.F}-01" for t in (DIRECT, INDIRECT)),
          f"the manufacturing time starts in January {d.F}")
    no_op = profile[DIRECT]["n"] - profile[DIRECT]["ops"]
    end = max(p["last"] for p in profile.values())
    claim(profile[DIRECT]["last"] == end == profile[NONMFG]["last"], "direct and non-manufacturing time end on the last day")
    open_starts = [r[0] for r in d.q("SELECT PeriodStartDate FROM PayrollPeriod WHERE Status = 'Open' "
                                     "AND PeriodStartDate BETWEEN ? AND ? ORDER BY 1", *year_range(d.C))]
    claim(bool(open_starts) and open_starts[0] > end and
          (date.fromisoformat(open_starts[0]) - date.fromisoformat(end)).days <= 3,
          "the time records end just before the open pay periods begin")
    claim(end < f"{d.C}-12-31", "the time records end before the year does")
    indirect_last = profile[INDIRECT]["last"]
    gap = (date.fromisoformat(end) - date.fromisoformat(indirect_last)).days
    claim(gap > 0, "indirect time ends earlier than the other time records")
    claim({r[0] for r in d.q("SELECT DISTINCT LaborType FROM LaborTimeEntry WHERE WorkDate > ?", indirect_last)} == {DIRECT, NONMFG},
          "the last week holds only direct and non-manufacturing time")
    # (2) ledger rows that point to no payroll payment
    rows = d.q("SELECT g.GLEntryID, g.PostingDate, g.SourceDocumentID, g.Debit, g.Credit, g.Description FROM GLEntry g "
               "LEFT JOIN PayrollPayment p ON p.PayrollPaymentID = g.SourceDocumentID WHERE g.SourceDocumentType = 'PayrollPayment' "
               "AND p.PayrollPaymentID IS NULL ORDER BY g.GLEntryID")
    docs = sorted({r[2] for r in rows})
    pairs = []
    for doc in docs:
        pair = [r for r in rows if r[2] == doc]
        pairs.append(dict(ids=[r[0] for r in pair], date=pair[0][1], doc=doc, debit=[r for r in pair if r[3]],
                          credit=[r for r in pair if r[4]]))
    claim(all(len(p["ids"]) == 2 and len(p["debit"]) == 1 and len(p["credit"]) == 1 and
              len({r[1] for r in rows if r[2] == p["doc"]}) == 1 for p in pairs),
          "the orphans are pairs of one debit and one credit on one date")
    amounts = {r[3] or r[4] for r in rows}
    claim(len(amounts) == 1, "every orphaned row has the same amount")
    debit_texts = {p["debit"][0][5] for p in pairs if p["debit"]}
    credit_texts = {p["credit"][0][5] for p in pairs if p["credit"]}
    claim(len(debit_texts) == 1 and len(credit_texts) == 1, "the debits share one description, and the credits another")
    claim(anomalies(d, "missing_payroll_payment") == set(docs),
          "the orphans' documents are the AnomalyLog's missing_payroll_payment items")
    # (3) customers without orders
    customers = d.q("SELECT CustomerID, IsActive FROM Customer c WHERE NOT EXISTS "
                    "(SELECT 1 FROM SalesOrder o WHERE o.CustomerID = c.CustomerID)")
    claim(all(r[1] == 0 for r in customers), "every customer without orders is inactive")
    # (4) work orders without operations
    work_orders = d.q("SELECT wo.WorkOrderID, wo.WorkOrderNumber, wo.Status FROM WorkOrder wo WHERE NOT EXISTS "
                      "(SELECT 1 FROM WorkOrderOperation op WHERE op.WorkOrderID = wo.WorkOrderID) ORDER BY wo.WorkOrderNumber")
    claim(all(r[2] == "Closed" for r in work_orders), "every work order without operations is Closed")
    claim(anomalies(d, "missing_work_order_operations") == {r[0] for r in work_orders},
          "the work orders without operations are the AnomalyLog's missing_work_order_operations items")
    wo_ids = ",".join(str(r[0]) for r in work_orders)
    wo_labor = d.q(f"SELECT LaborType, COUNT(*) FROM LaborTimeEntry WHERE WorkOrderID IN ({wo_ids}) GROUP BY 1")
    claim([r[0] for r in wo_labor] == [DIRECT], "the time recorded on those work orders is all direct")
    # (5) labor time whose operation key matches no operation
    orphans = d.q("SELECT lt.LaborType, wo.WorkOrderNumber, lt.RegularHours + lt.OvertimeHours FROM LaborTimeEntry lt "
                  "LEFT JOIN WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID "
                  "LEFT JOIN WorkOrder wo ON wo.WorkOrderID = lt.WorkOrderID "
                  "WHERE lt.WorkOrderOperationID IS NOT NULL AND op.WorkOrderOperationID IS NULL")
    claim({r[0] for r in orphans} == {DIRECT}, "every orphaned operation key is on a Direct Manufacturing entry")
    by_wo = {}
    for r in orphans:
        by_wo[r[1]] = by_wo.get(r[1], 0) + 1
    claim(set(by_wo) == {r[1] for r in work_orders}, "the orphaned keys are on the work orders without operations")
    return dict(direct=profile[DIRECT], indirect=profile[INDIRECT], nonmfg=profile[NONMFG], no_op=no_op,
                no_op_word=word(no_op).capitalize(), end_text=long_date(end),
                indirect_gap="a week" if gap == 7 else f"{word(gap)} day{'' if gap == 1 else 's'}",
                n_orphans=word(len(rows)), pairs=pairs, amount=amounts.pop(), debit_text=debit_texts.pop(),
                credit_text=credit_texts.pop(), total=sum(r[3] for r in rows),
                n_customers=word(len(customers)).capitalize(), n_wo=word(len(work_orders)).capitalize(),
                work_orders=[r[1] for r in work_orders], wo_labor=sum(r[1] for r in wo_labor),
                orphans=len(orphans), orphan_hours=sum(r[2] for r in orphans), orphan_by_wo=sorted(by_wo.items()))


# --- Exercise 10.6 -------------------------------------------------------------------------------

def capital_invoices(d) -> list[int]:
    """The supplier invoices the Debt Reclass entries moved to notes payable (Chapter 8), in posting order; each entry's
    description names the invoice's PurchaseInvoiceID."""
    return [int(re.search(r"invoice (\d+)", text).group(1)) for (text,) in d.q(
        "SELECT Description FROM JournalEntry WHERE EntryType = 'Debt Reclass' ORDER BY PostingDate")]


@note("ch10.ex6", EXERCISES)
def ex6(d, claim):
    end = f"{d.C}-12-31"
    matches = d.q("SELECT s.SupplierID, s.SupplierName, e.EmployeeID, e.JobTitle, s.IsApproved FROM Supplier s "
                  "JOIN Employee e ON e.Address = s.Address ORDER BY s.SupplierID")
    suppliers = [m[0] for m in matches]
    claim(len(set(suppliers)) == len(matches), "each matching supplier matches one employee")
    claim(d.one("SELECT COUNT(*) FROM (SELECT Address FROM Employee GROUP BY Address HAVING COUNT(*) > 1)") == 0,
          "no two employees share an address")
    claim(all(m[4] == 1 for m in matches), "all the matching suppliers are approved")
    claim(anomalies(d, "related_party_address_match") == set(suppliers),
          "the matches are the AnomalyLog's related_party_address_match items")
    ids = ",".join(str(s) for s in suppliers)
    invoices = d.q(f"SELECT SupplierID, COUNT(*), SUM(GrandTotal) FROM PurchaseInvoice WHERE SupplierID IN ({ids}) "
                   f"AND InvoiceDate <= ? GROUP BY 1 ORDER BY 1", end)
    claim(d.one(f"SELECT COUNT(*) FROM PurchaseInvoice WHERE SupplierID IN ({ids}) AND InvoiceDate > ?", end) == 0,
          f"the matching suppliers' invoices are all dated through {end}")
    payments = d.q(f"SELECT SupplierID, COUNT(*), SUM(Amount) FROM DisbursementPayment WHERE SupplierID IN ({ids}) "
                   f"AND PaymentDate <= ? GROUP BY 1 ORDER BY 1", end)
    # The fan-out of a join of invoices to payments on the supplier, for the first matching supplier, with the
    # exercise's date filter on both.
    fan = d.one("SELECT COUNT(*) FROM PurchaseInvoice pi JOIN DisbursementPayment p ON p.SupplierID = pi.SupplierID "
                "WHERE pi.SupplierID = ? AND pi.InvoiceDate <= ? AND p.PaymentDate <= ?", suppliers[0], end, end)
    capital = capital_invoices(d)
    cap = [dict(id=r[0], number=r[1], supplier=r[2], total=r[3]) for r in d.q(
        "SELECT PurchaseInvoiceID, InvoiceNumber, SupplierID, GrandTotal FROM PurchaseInvoice WHERE PurchaseInvoiceID IN (%s)"
        % ",".join(str(c) for c in capital))]
    cap.sort(key=lambda c: capital.index(c["id"]))
    owner = cap[0]["supplier"]
    claim(len({c["supplier"] for c in cap}) == 1 and owner in suppliers,
          "the Debt Reclass invoices belong to one of the matching suppliers")
    claim(d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE PurchaseInvoiceID IN (%s) AND PaymentDate <= ?"
                % ",".join(str(c) for c in capital), end) == 0, f"the Debt Reclass invoices are still open in full at {end}")
    still_open = d.one("SELECT SUM(b) FROM (SELECT pi.GrandTotal - COALESCE((SELECT SUM(p.Amount) FROM DisbursementPayment p "
                       "WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID AND p.PaymentDate <= ?1), 0) AS b FROM PurchaseInvoice pi "
                       "WHERE pi.SupplierID = ?2 AND pi.InvoiceDate <= ?1) WHERE b > 0.005", end, owner)
    shared = []
    for (name,) in d.q("SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1 ORDER BY 1"):
        members = d.q("SELECT CustomerID, CustomerSegment FROM Customer WHERE CustomerName = ? ORDER BY CustomerID", name)
        shared.append(dict(name=name, customers=[dict(id=c, segment=s) for c, s in members],
                           same=len({s for _, s in members}) == 1))
    claim(all(len(s["customers"]) == 2 for s in shared), "each shared customer name belongs to two customers")
    return dict(n_word=word(len(matches)), matches=[dict(supplier=m[0], name=m[1], employee=m[2], title=m[3]) for m in matches],
                end=end, invoices=invoices, payments=payments, fan=fan, first=suppliers[0],
                big=dict(id=owner, open=still_open), capital=cap, shared=shared)
