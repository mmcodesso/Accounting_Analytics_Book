"""Chapter 12's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import date, timedelta

from notes import note

EXERCISES = "chapters/12-sql-audit-analytics/_exercises.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
# Exercise 8.1's aging buckets (Tutorial 8.2, tbl-08-02): the first day past due of each bucket.
BUCKETS = [(-10**9, "Current"), (1, "1-30 days"), (31, "31-60 days"), (61, "61-90 days"), (91, "over 90 days")]
# Exercise 12.2's customer strata (the exercise sets them).
STRATA = [0, 1_000, 10_000, 50_000]


def word(n: int) -> str:
    return WORDS[n] if n < len(WORDS) else f"{n:,}"


def asof(d) -> str:
    return f"{d.C}-12-31"


def thousands(x: float) -> int:
    return int(round(x, -3))


def working_days(d, first: str, last: str) -> int:
    """Working days of the plant calendar (one work center's calendar; every work center has the same days)."""
    center = d.one("SELECT MIN(WorkCenterID) FROM WorkCenterCalendar")
    return d.one("SELECT COUNT(*) FROM WorkCenterCalendar WHERE WorkCenterID = ? AND IsWorkingDay = 1 "
                 "AND CalendarDate BETWEEN ? AND ?", center, first, last)


def weekdays(first: str, last: str) -> int:
    a, b = date.fromisoformat(first), date.fromisoformat(last)
    return sum(1 for i in range((b - a).days + 1) if (a + timedelta(days=i)).weekday() < 5)


def surge_days(d) -> list[str]:
    """Test H8's surge days: days on which every manufacturing employee who clocked in clocked the same hours."""
    return [r[0] for r in d.q(
        "SELECT tc.WorkDate FROM TimeClockEntry tc JOIN Employee e ON e.EmployeeID = tc.EmployeeID "
        "JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID WHERE cc.CostCenterName = 'Manufacturing' "
        "GROUP BY tc.WorkDate HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1 AND COUNT(*) > 1 "
        "ORDER BY tc.WorkDate")]


def runs(numbers: list[str]) -> list[str]:
    """Document numbers grouped by year as the notes list them: three or more consecutive numbers as "first to
    last", two as "first and last", the later numbers shortened to their sequence."""
    by_prefix = defaultdict(list)
    for n in sorted(numbers):
        prefix, seq = n.rsplit("-", 1)
        by_prefix[prefix].append(seq)
    out = []
    for prefix, seqs in by_prefix.items():
        ints = [int(s) for s in seqs]
        consecutive = ints == list(range(ints[0], ints[0] + len(ints)))
        if len(seqs) >= 3 and consecutive:
            out.append(f"{prefix}-{seqs[0]} to {seqs[-1]}")
        elif len(seqs) == 2:
            out.append(f"{prefix}-{seqs[0]} and {seqs[1]}")
        else:
            out.append(", ".join(f"{prefix}-{s}" for s in seqs))
    return out


# --- Exercise 12.1 --------------------------------------------------------------------------------

def invoices_by_delivery(d) -> list[dict]:
    """Test L5's population: each sales invoice with its first shipment, last delivery, and first posting."""
    rows = d.q("WITH Shipped AS (SELECT sil.SalesInvoiceID, MIN(s.ShipmentDate) AS ShipmentDate, "
               "MAX(s.DeliveryDate) AS DeliveryDate FROM SalesInvoiceLine sil JOIN ShipmentLine sl "
               "ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
               "GROUP BY sil.SalesInvoiceID), "
               "Posted AS (SELECT SourceDocumentID AS SalesInvoiceID, MIN(PostingDate) AS PostingDate FROM GLEntry "
               "WHERE SourceDocumentType = 'SalesInvoice' GROUP BY SourceDocumentID) "
               "SELECT si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate, sh.ShipmentDate, sh.DeliveryDate, "
               "p.PostingDate, si.SubTotal FROM SalesInvoice si JOIN Shipped sh ON sh.SalesInvoiceID = si.SalesInvoiceID "
               "JOIN Posted p ON p.SalesInvoiceID = si.SalesInvoiceID ORDER BY si.InvoiceNumber")
    out = []
    for sid, number, invoiced, shipped, delivered, posted, sub in rows:
        late = posted[:4] != delivered[:4]
        out.append(dict(id=sid, number=number, date=invoiced, shipped=shipped, delivered=delivered, posted=posted,
                        sub=sub, late=late, before=not late and invoiced < shipped))
    return out


def late_december_cost(d, year: int) -> float:
    """The full cost of the late-December work of `year` paid in the next fiscal year: the hourly labor of that
    work (ExtendedLaborCost by WorkDate), plus the salaries of the pay periods that hold it, allocated by working
    day, with the employer taxes and benefits of those periods as a rate on gross pay."""
    end = f"{year}-12-31"
    periods = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate FROM PayrollPeriod "
                  "WHERE PeriodStartDate <= ? AND PayDate > ? ORDER BY PeriodStartDate", end, end)
    hourly = d.one("SELECT SUM(lt.ExtendedLaborCost) FROM LaborTimeEntry lt JOIN PayrollPeriod pp "
                   "ON pp.PayrollPeriodID = lt.PayrollPeriodID WHERE substr(lt.WorkDate, 1, 4) = ? AND pp.FiscalYear = ?",
                   str(year), year + 1)
    salaries, gross, charges = 0.0, 0.0, 0.0
    for pid, start, stop in periods:
        salary = d.one("SELECT COALESCE(SUM(l.Amount), 0) FROM PayrollRegisterLine l JOIN PayrollRegister r "
                       "ON r.PayrollRegisterID = l.PayrollRegisterID WHERE r.PayrollPeriodID = ? "
                       "AND l.LineType = 'Salary Earnings'", pid)
        salaries += salary * working_days(d, start, min(stop, end)) / working_days(d, start, stop)
        g, c = d.q("SELECT SUM(GrossPay), SUM(EmployerPayrollTax + EmployerBenefits) FROM PayrollRegister "
                   "WHERE PayrollPeriodID = ?", pid)[0]
        gross += g
        charges += c
    return (hourly + salaries) * (1 + charges / gross)


@note("ch12.ex1", EXERCISES)
def ex1(d, claim):
    # Left unregistered: the note's manufacturing range for late December of the current year ("about 185,000-199,000")
    # cannot be reproduced; the two methods that give its total range give the manufacturing amounts below.
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE substr(DeliveryDate, 1, 4) <> substr(ShipmentDate, 1, 4)") == 0,
          "every shipment is delivered in the year it ships")
    invoices = invoices_by_delivery(d)
    late = [i for i in invoices if i["late"]]
    years = sorted({int(i["delivered"][:4]) for i in late})
    claim(years == [d.F, d.P], "revenue was posted in another year only for deliveries of the first and prior years")
    claim(all(i["delivered"][5:7] == "12" and i["posted"][5:7] == "01" and int(i["posted"][:4]) == int(i["delivered"][:4]) + 1
              for i in late), "every late invoice is for a December delivery posted in January of the next year")
    g1 = [i for i in late if int(i["delivered"][:4]) == d.F]
    g2 = [i for i in late if int(i["delivered"][:4]) == d.P]
    # The late invoices dated in the year of delivery (before the year-end) but posted in the next: the revenue cutoff
    # errors of the invoice-date comparisons. The others were dated, like posted, in January.
    odd1 = [i for i in g1 if i["date"][:4] != i["posted"][:4]]
    odd2 = [i for i in g2 if i["date"][:4] != i["posted"][:4]]
    odd_numbers = {i["number"] for i in odd1 + odd2}
    unbilled = d.q("SELECT s.ShipmentID, s.ShipmentDate, ROUND(sl.ExtendedStandardCost, 2), "
                   "ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2) FROM ShipmentLine sl "
                   "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN SalesOrderLine sol ON sol.SalesOrderLineID = "
                   "sl.SalesOrderLineID LEFT JOIN SalesInvoiceLine sil ON sil.ShipmentLineID = sl.ShipmentLineID "
                   "WHERE sil.SalesInvoiceLineID IS NULL")
    claim(all(r[1][:7] == f"{d.C}-12" for r in unbilled), f"every shipment line never invoiced shipped in December {d.C}")
    posted = {r[0] for r in d.q("SELECT DISTINCT SourceDocumentID FROM GLEntry WHERE SourceDocumentType = 'Shipment' "
                                "AND PostingDate <= ?", asof(d))}
    claim(all(r[0] in posted for r in unbilled), "the unbilled shipments' cost is posted by the year-end")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN Shipment s ON s.ShipmentID = g.SourceDocumentID "
                "WHERE g.SourceDocumentType = 'Shipment' AND g.PostingDate <> s.ShipmentDate") == 0,
          "cost of goods sold is posted on the shipment date")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear > ?", d.C) == 0,
          "no sales invoice is posted after the current fiscal year")
    s1, s2 = sum(i["sub"] for i in g1), sum(i["sub"] for i in g2)
    cost, value = sum(r[2] for r in unbilled), sum(r[3] for r in unbilled)
    claim(s1 > s2, f"{d.P} is overstated (received more than it moved on)")
    claim(value > s2, f"{d.C} is understated (unbilled more than received)")
    before = [i for i in invoices if i["before"]]
    ex52 = {r[0] for r in d.q("SELECT InvoiceNumber FROM SalesInvoice WHERE substr(InvoiceNumber, 4, 4) <> substr(InvoiceDate, 1, 4)")} | \
        {r[0] for r in d.q("SELECT si.InvoiceNumber FROM SalesInvoice si JOIN SalesOrder so ON so.SalesOrderID = si.SalesOrderID "
                           "WHERE si.InvoiceDate < so.OrderDate")}
    numbers = {i["number"] for i in before}
    only_ex52, only_before = sorted(ex52 - numbers), sorted(numbers - ex52)
    claim(set(only_ex52) <= odd_numbers, "the Exercise 5.2 invoices missing from the list are revenue cutoff errors")
    differences = [i for i in invoices if int(i["posted"][:4]) == d.C and i["date"][:4] != i["posted"][:4]]
    cutoff_errors = [i["number"] for i in differences if i["late"]]
    late_pi = [dict(number=r[0], received=r[1], posted=r[2]) for r in d.q(
        "SELECT p.InvoiceNumber, p.ReceivedDate, MIN(g.PostingDate) FROM GLEntry g JOIN PurchaseInvoice p "
        "ON p.PurchaseInvoiceID = g.SourceDocumentID WHERE g.SourceDocumentType = 'PurchaseInvoice' "
        "AND g.PostingDate <> p.ReceivedDate GROUP BY p.PurchaseInvoiceID ORDER BY 1")]
    crossing = [dict(zip(("number", "date", "received", "total", "id"), r)) for r in d.q(
        "SELECT InvoiceNumber, InvoiceDate, ReceivedDate, GrandTotal, SupplierID FROM PurchaseInvoice "
        "WHERE substr(InvoiceDate, 1, 4) <> substr(ReceivedDate, 1, 4) ORDER BY ReceivedDate, InvoiceNumber")]
    hourly = d.q("SELECT CAST(substr(lt.WorkDate, 1, 4) AS INTEGER), pp.FiscalYear, SUM(lt.ExtendedLaborCost), "
                 "SUM(CASE WHEN lt.LaborType <> 'NonManufacturing' THEN lt.ExtendedLaborCost ELSE 0 END) "
                 "FROM LaborTimeEntry lt JOIN PayrollPeriod pp ON pp.PayrollPeriodID = lt.PayrollPeriodID "
                 "GROUP BY 1, 2 HAVING CAST(substr(lt.WorkDate, 1, 4) AS INTEGER) <> pp.FiscalYear ORDER BY 1")
    claim([(r[0], r[1]) for r in hourly] == [(d.F, d.P), (d.P, d.C)],
          "only the late-December work of the first and prior years is paid in the next fiscal year")
    # the late December of the current year
    processed = d.q("SELECT PayrollPeriodID, PeriodNumber, PeriodStartDate, PeriodEndDate FROM PayrollPeriod "
                    "WHERE Status = 'Processed' ORDER BY PeriodStartDate DESC LIMIT 8")[::-1]
    ids = ",".join(str(p[0]) for p in processed)
    total, mfg = d.q(f"SELECT SUM(r.GrossPay + r.EmployerPayrollTax + r.EmployerBenefits), SUM(CASE WHEN "
                     f"c.CostCenterName = 'Manufacturing' THEN r.GrossPay + r.EmployerPayrollTax + r.EmployerBenefits "
                     f"ELSE 0 END) FROM PayrollRegister r JOIN CostCenter c ON c.CostCenterID = r.CostCenterID "
                     f"WHERE r.PayrollPeriodID IN ({ids})")[0]
    lines = {(t, m): a for t, m, a in d.q(
        f"SELECT l.LineType, c.CostCenterName = 'Manufacturing', SUM(l.Amount) FROM PayrollRegisterLine l "
        f"JOIN PayrollRegister r ON r.PayrollRegisterID = l.PayrollRegisterID JOIN CostCenter c "
        f"ON c.CostCenterID = r.CostCenterID WHERE r.PayrollPeriodID IN ({ids}) GROUP BY 1, 2")}
    open_periods = d.q("SELECT PayrollPeriodID, PeriodStartDate FROM PayrollPeriod WHERE Status <> 'Processed' "
                       "AND PeriodStartDate <= ? ORDER BY PeriodStartDate", asof(d))
    claim(len(open_periods) > 0 and all(d.one("SELECT COUNT(*) FROM PayrollRegister WHERE PayrollPeriodID = ?", p[0]) == 0
                                        for p in open_periods), "the open periods at the year-end have no registers")
    start = open_periods[0][1]
    claim(start[:7] == f"{d.C}-12" and start > processed[-1][3], "the unrecorded work starts in December, after the last processed period")
    base_days = working_days(d, processed[0][2], processed[-1][3])
    left = working_days(d, start, asof(d))
    week_days = weekdays(start, asof(d))

    def estimates(m: tuple) -> tuple[float, float]:
        """Per working day of the processed periods; or hourly per working day plus salaries per weekday (ten a
        period), both with the periods' employer tax and benefit rate."""
        hourly_pay = sum(lines.get((t, x), 0.0) for t in ("Regular Earnings", "Overtime Earnings") for x in m)
        salary = sum(lines.get(("Salary Earnings", x), 0.0) for x in m)
        charges = sum(lines.get((t, x), 0.0) for t in ("Employer Payroll Tax", "Employer Benefits") for x in m)
        full = hourly_pay + salary + charges
        per_day = full / base_days * left
        split = (hourly_pay / base_days * left + salary / len(processed) * week_days / 10) * (1 + charges / (hourly_pay + salary))
        return per_day, split

    all_est, mfg_est = estimates((0, 1)), estimates((1,))
    claim(abs(all_est[0] - total / base_days * left) < 0.01, "the working-day estimate uses the registers' full cost")
    accrued = d.account("2030")
    sources = dict(d.q("SELECT SourceDocumentType, ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? "
                       "AND PostingDate <= ? GROUP BY 1", accrued, asof(d)))
    opening = sources.pop("JournalEntry", 0.0)
    entry = d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'JournalEntry' AND VoucherNumber <> ?",
                accrued, entry) == 0, "the only journal entry to 2030 is the opening entry")
    claim(set(sources) <= {"PayrollSummary", "PayrollPayment"} and abs(sum(sources.values())) < 0.005,
          "the payroll summaries and payments net to zero in 2030")
    return dict(g1=dict(word=word(len(g1)).capitalize(), sub=s1, odd=odd1), g2=dict(word=word(len(g2)), sub=s2, odd=odd2),
                n_unbilled=word(len(unbilled)).capitalize(), cost=cost, value=value,
                eff1=s1, eff2=s1 - s2, eff3=round(value - s2, -1),
                n_before=word(len(before)).capitalize(), before=runs([i["number"] for i in before]),
                only_ex52=only_ex52, only_before=only_before, cutoff_errors=cutoff_errors,
                n_differences=word(len(differences)), late_pi=late_pi, crossing=crossing, n_crossing=word(len(crossing)),
                hourly=[dict(work=r[0], paid=r[1], total=r[2], mfg=r[3]) for r in hourly],
                full=[thousands(late_december_cost(d, y)) for y in (d.F, d.P)],
                first=int(processed[0][1][-3:]), last=int(processed[-1][1][-3:]),
                avg=total / len(processed), avg_mfg=mfg / len(processed), days=left, start_day=int(start[8:]),
                low=thousands(min(all_est)), high=thousands(max(all_est)),
                mfg_low=thousands(min(mfg_est)), mfg_high=thousands(max(mfg_est)), opening=opening)


# --- Exercise 12.2 --------------------------------------------------------------------------------

@note("ch12.ex2", EXERCISES)
def ex2(d, claim):
    end = asof(d)
    rows = d.q("WITH Applied AS (SELECT SalesInvoiceID, SUM(AppliedAmount) AS Applied FROM CashReceiptApplication "
               "WHERE ApplicationDate <= ?1 GROUP BY SalesInvoiceID), "
               "Credited AS (SELECT OriginalSalesInvoiceID AS SalesInvoiceID, SUM(GrandTotal) AS Credited FROM CreditMemo "
               "WHERE CreditMemoDate <= ?1 GROUP BY OriginalSalesInvoiceID) "
               "SELECT si.SalesInvoiceID, si.CustomerID, ROUND(si.GrandTotal - COALESCE(a.Applied, 0) - COALESCE(c.Credited, 0), 2), "
               "julianday(?1) - julianday(si.DueDate), COALESCE(a.Applied, 0) FROM SalesInvoice si "
               "LEFT JOIN Applied a ON a.SalesInvoiceID = si.SalesInvoiceID LEFT JOIN Credited c ON c.SalesInvoiceID = si.SalesInvoiceID "
               "WHERE si.InvoiceDate <= ?1", end)
    positive = [r for r in rows if r[2] > 0]
    buckets = [dict(name=name, n=0, amount=0.0) for _, name in BUCKETS]
    for r in positive:
        b = buckets[[i for i, (low, _) in enumerate(BUCKETS) if r[3] >= low][-1]]
        b["n"] += 1
        b["amount"] += r[2]
    total = sum(r[2] for r in positive)
    ar = d.account("1020")
    ledger = d.balance(["1020"], end)
    entry = d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")
    opening = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?", ar, entry)
    claim(abs(ledger - total - opening) < 0.005, "the ledger exceeds the open invoices by exactly the opening line")
    negative = [r for r in rows if r[2] < 0]
    ids = ",".join(str(r[0]) for r in negative)
    to_2060 = d.one(f"SELECT COUNT(DISTINCT cm.OriginalSalesInvoiceID) FROM CreditMemo cm JOIN GLEntry g "
                    f"ON g.SourceDocumentType = 'CreditMemo' AND g.SourceDocumentID = cm.CreditMemoID "
                    f"WHERE g.AccountID = ? AND g.Credit > 0 AND cm.OriginalSalesInvoiceID IN ({ids})", d.account("2060"))
    claim(to_2060 == len(negative), "every invoice with a negative balance has a credit memo posted to account 2060")
    claim(all(r[4] > 0 for r in negative), "every invoice with a negative balance has been paid")
    refunded = d.one(f"SELECT COUNT(DISTINCT cm.OriginalSalesInvoiceID) FROM CreditMemo cm JOIN CustomerRefund r "
                     f"ON r.CreditMemoID = cm.CreditMemoID WHERE cm.OriginalSalesInvoiceID IN ({ids}) AND r.RefundDate <= ?", end)
    paid_in_full = d.one(f"SELECT COUNT(*) FROM SalesInvoice si WHERE si.SalesInvoiceID IN ({ids}) AND si.GrandTotal - 0.005 <= "
                         f"(SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a WHERE a.SalesInvoiceID = si.SalesInvoiceID "
                         f"AND a.ApplicationDate <= ?)", end)
    claim(refunded >= 0.95 * len(negative), "the credits on those invoices are (almost all) refunded")
    by_customer = defaultdict(float)
    for r in positive:
        by_customer[r[1]] += r[2]
    strata = [dict(n=0, amount=0.0) for _ in STRATA]
    for v in by_customer.values():
        s = strata[[i for i, low in enumerate(STRATA) if v >= low][-1]]
        s["n"] += 1
        s["amount"] += v
    # receipts not invoiced
    grni = d.q("WITH InvoicedByReceipt AS (SELECT pil.GoodsReceiptLineID, SUM(pil.Quantity) AS QtyInvoiced "
               "FROM PurchaseInvoiceLine pil JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID "
               "WHERE pi.ReceivedDate <= ?1 GROUP BY pil.GoodsReceiptLineID) "
               "SELECT gr.ReceiptDate, po.SupplierID, grl.ExtendedStandardCost * (1 - COALESCE(ibr.QtyInvoiced, 0) / "
               "grl.QuantityReceived) FROM GoodsReceiptLine grl JOIN GoodsReceipt gr ON gr.GoodsReceiptID = grl.GoodsReceiptID "
               "JOIN PurchaseOrder po ON po.PurchaseOrderID = gr.PurchaseOrderID LEFT JOIN InvoicedByReceipt ibr "
               "ON ibr.GoodsReceiptLineID = grl.GoodsReceiptLineID "
               "WHERE gr.ReceiptDate <= ?1 AND COALESCE(ibr.QtyInvoiced, 0) < grl.QuantityReceived - 0.0001", end)
    grni_total = round(sum(r[2] for r in grni), 2)
    gl2020 = -d.balance(["2020"], end)
    claim(0 < abs(grni_total - gl2020) < 1, "the receipts not invoiced differ from account 2020 by less than a dollar")
    months = defaultdict(lambda: [0, 0.0])
    suppliers = defaultdict(lambda: [0, 0.0])
    for received, supplier, v in grni:
        months[received[:7]][0] += 1
        months[received[:7]][1] += v
        suppliers[supplier][0] += 1
        suppliers[supplier][1] += v
    old = sorted(m for m in months if int(m[:4]) * 12 + int(m[5:7]) <= d.C * 12 + 12 - 2)
    claim(len(old) >= 2, "receipts of more than one month are more than two months old")
    return dict(asof=end, n=len(positive), total=total, customers=len(by_customer), b=buckets, ar=ar, ledger=ledger,
                difference=ledger - total, entry=entry, n_negative=len(negative), negative=sum(r[2] for r in negative),
                paid_in_full=paid_in_full, refunded=refunded,
                strata=strata, key_share=strata[-1]["amount"] / total, grni_lines=len(grni), grni=grni_total, gl2020=gl2020,
                rounding=abs(grni_total - gl2020),
                months=[(m, months[m][1], months[m][0]) for m in sorted(months, reverse=True)],
                suppliers=[(s, n, round(v, 2)) for s, (n, v) in sorted(suppliers.items(), key=lambda kv: -kv[1][1])[:3]],
                old_from=MONTHS[int(old[0][5:7]) - 1], old_to=MONTHS[int(old[-1][5:7]) - 1])


# --- Exercise 12.3 --------------------------------------------------------------------------------

@note("ch12.ex3", EXERCISES)
def ex3(d, claim):
    # Left unregistered: the note's late-recorded share "0.03-0.16 a month through June" leaves out January of the
    # first year, whose share is 0.00.
    cutoff = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    claim(cutoff[:4] == str(d.C), "the time records end in the current fiscal year")
    rows = d.q("SELECT CAST(strftime('%Y', op.ActualEndDate) AS INTEGER), wc.WorkCenterName, SUM(op.PlannedLoadHours), "
               "SUM(lab.H), SUM(lab.Hin) FROM WorkOrderOperation op JOIN WorkCenter wc ON wc.WorkCenterID = op.WorkCenterID "
               "LEFT JOIN (SELECT lt.WorkOrderOperationID AS id, SUM(lt.RegularHours + lt.OvertimeHours) AS H, "
               "SUM(CASE WHEN lt.WorkDate <= o2.ActualEndDate THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END) AS Hin "
               "FROM LaborTimeEntry lt JOIN WorkOrderOperation o2 ON o2.WorkOrderOperationID = lt.WorkOrderOperationID "
               "WHERE lt.LaborType = 'Direct Manufacturing' GROUP BY lt.WorkOrderOperationID) lab ON lab.id = op.WorkOrderOperationID "
               "WHERE op.ActualEndDate <= ? GROUP BY 1, 2 ORDER BY 1, 2", cutoff)
    # all hours as Tutorial 11.2 compares them (hours rounded before dividing); the hours while open unrounded
    ratio = {(y, c): dict(all=round(h) / round(p), open=hin / p) for y, c, p, h, hin in rows}
    centers = sorted({c for _, c, *_ in rows})
    short = lambda c: c.removesuffix(" Work Center")
    claim(all(ratio[(d.C, c)]["open"] < 1 for c in centers), f"every work center falls below plan in {d.C} on the time while open")
    packing = next(c for c in centers if c.startswith("Packing"))
    claim(ratio[(d.C, packing)]["all"] > 1 > ratio[(d.C, packing)]["open"], "the Packing excess disappears")
    last = d.q("SELECT wc.WorkCenterName, COUNT(*) FROM WorkOrderOperation op JOIN WorkCenter wc ON wc.WorkCenterID = op.WorkCenterID "
               "JOIN (SELECT WorkOrderID, MAX(OperationSequence) AS m FROM WorkOrderOperation GROUP BY WorkOrderID) x "
               "ON x.WorkOrderID = op.WorkOrderID AND x.m = op.OperationSequence GROUP BY 1")
    claim([r[0] for r in last] == [packing], "Packing is the last operation of every routing")
    # The first months of the first year: the start-up January, the build (each month from February in which the plant
    # completed more than it shipped), and the month after it.
    released = dict(d.q("SELECT strftime('%Y-%m', ReleasedDate), COUNT(*) FROM WorkOrder GROUP BY 1"))
    completed = dict(d.q("SELECT strftime('%Y-%m', pc.CompletionDate), ROUND(SUM(pcl.QuantityCompleted)) FROM ProductionCompletionLine pcl "
                         "JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID GROUP BY 1"))
    shipped = dict(d.q("SELECT strftime('%Y-%m', s.ShipmentDate), ROUND(SUM(sl.QuantityShipped)) FROM ShipmentLine sl "
                       "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN Item i ON i.ItemID = sl.ItemID "
                       "WHERE i.SupplyMode = 'Manufactured' GROUP BY 1"))
    year = [f"{d.F}-{m:02d}" for m in range(1, 13)]
    claim(completed.get(year[0], 0) < shipped.get(year[0], 0), "the plant completed less than it shipped in the start-up January")
    build = []
    for m in year[1:]:
        if completed.get(m, 0) <= shipped.get(m, 0):
            break
        build.append(m)
    claim(3 <= len(build) <= 9, "the plant completed more than it shipped for several months from February (the stock build)")
    after = year[min(len(build) + 1, 11)]
    months = year[:year.index(after) + 1]                   # January through the month after the build
    claim(released.get(after, 0) < sum(released.get(m, 0) for m in build) / max(len(build), 1),
          "releases after the build fell below their level during it")
    surplus = sum(completed[m] - shipped[m] for m in build)
    staff_months = year[1:year.index(after) + 2]             # February through the month after that
    staff = [{r[0] for r in d.q("SELECT DISTINCT EmployeeID FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' "
                                "AND substr(WorkDate, 1, 7) = ?", m)} for m in staff_months]
    claim(all(staff[0] <= s for s in staff), "the employees who recorded manufacturing time in February still did, every month "
                                            "through the month after the build ended")
    late = dict(d.q("SELECT substr(lt.WorkDate, 1, 7), SUM(CASE WHEN lt.WorkDate > op.ActualEndDate THEN lt.RegularHours + "
                    "lt.OvertimeHours ELSE 0 END) / SUM(lt.RegularHours + lt.OvertimeHours) FROM LaborTimeEntry lt "
                    "JOIN WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID "
                    "WHERE lt.LaborType = 'Direct Manufacturing' GROUP BY 1"))
    # The month surge days began in earnest (more than one a month), and the late share before and in it.
    per_month = Counter(s[:7] for s in surge_days(d))
    first = next((m for m in sorted(per_month) if per_month[m] > 1), None)
    claim(first is not None and first[:4] == str(d.F), "surge days began in earnest (more than one a month) in the first year")
    first = first or year[6]
    early = [late[m] for m in sorted(late) if m < first]
    claim(bool(early) and late.get(first, 0) > max(early), "the late share in that month is higher than in any month before it")
    return dict(cutoff=cutoff, centers=[short(c) for c in centers],
                now=[ratio[(d.C, c)]["open"] for c in centers], now_all=[ratio[(d.C, c)]["all"] for c in centers],
                then=[ratio[(d.F, c)]["open"] for c in centers], months_to=MONTHS[int(months[-1][5:]) - 1],
                released=[released.get(m, 0) for m in months], completed=[completed.get(m, 0) for m in months],
                shipped=[shipped.get(m, 0) for m in months], build_from=MONTHS[int(build[0][5:]) - 1] if build else "?",
                build_to=MONTHS[int(build[-1][5:]) - 1] if build else "?", after=MONTHS[int(after[5:]) - 1],
                surplus=thousands(surplus), staff=len(staff[0]),
                late_low=min(early, default=0), late_high=max(early, default=0), before=MONTHS[int(first[5:]) - 2],
                before_year=first[:4], late_first=late.get(first, 0), first=MONTHS[int(first[5:]) - 1], first_year=first[:4])


# --- Exercise 12.4 --------------------------------------------------------------------------------

@note("ch12.ex4", EXERCISES)
def ex4(d, claim):
    approvals = d.q("SELECT substr(WorkDate, 1, 4), ReasonCode, ApprovedByEmployeeID, ApprovedHours, RequestedHours, "
                    "ApprovedDate, WorkDate FROM OvertimeApproval")
    reasons = sorted({r[1] for r in approvals})
    by_year = defaultdict(Counter)
    for r in approvals:
        by_year[r[0]][r[1]] += 1
    claim(all(0.2 <= c[x] / sum(c.values()) <= 0.3 for c in by_year.values() for x in reasons),
          "every reason code holds about a quarter of the approvals in every year")
    approvers = Counter(r[2] for r in approvals).most_common()
    manager = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Production Manager'")
    claim(approvers[0][0] == manager, "the Production Manager approved the most")
    claim(all(r[3] == r[4] for r in approvals), "every approval grants exactly the hours requested")
    claim(all(r[5] == r[6] for r in approvals), "every approval is dated on the work date")
    surge = surge_days(d)
    marks = ",".join(f"'{s}'" for s in surge)
    entries = d.q(f"SELECT tc.TimeClockEntryID, oa.ApprovedByEmployeeID, oa.ApprovedDate, tc.WorkDate FROM TimeClockEntry tc "
                  f"JOIN Employee e ON e.EmployeeID = tc.EmployeeID JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
                  f"LEFT JOIN OvertimeApproval oa ON oa.OvertimeApprovalID = tc.OvertimeApprovalID "
                  f"WHERE cc.CostCenterName = 'Manufacturing' AND tc.WorkDate IN ({marks})")
    claim(all(r[1] == manager and r[2] == r[3] for r in entries),
          "every clock entry of the surge days was approved by the Production Manager on the work date")
    overtime = {(int(y), s): h for y, s, h in d.q(
        f"SELECT substr(tc.WorkDate, 1, 4), tc.WorkDate IN ({marks}), SUM(tc.OvertimeHours) FROM TimeClockEntry tc "
        f"JOIN Employee e ON e.EmployeeID = tc.EmployeeID JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID "
        f"WHERE cc.CostCenterName = 'Manufacturing' GROUP BY 1, 2")}
    other = [overtime.get((y, 0), 0.0) for y in d.years]
    on_surge = [overtime.get((y, 1), 0.0) for y in d.years]
    flat = max(other) / min(other) < 1.1
    claim(flat or other[-1] <= other[0], "overtime on other days stayed about the same, or at least did not grow")
    claim(on_surge == sorted(on_surge) and on_surge[-1] - on_surge[0] >= (on_surge[-1] + other[-1]) - (on_surge[0] + other[0]),
          "overtime on surge days grew every year and holds all the growth")
    return dict(n=len(approvals), n_reasons=word(len(reasons)), reasons=reasons, manager_n=approvers[0][1],
                manager_share=approvers[0][1] / len(approvals), entries=len(entries), days=len(surge),
                other=other, surge=on_surge, other_trend="stayed about the same" if flat else "did not grow")


# --- Exercise 12.5 --------------------------------------------------------------------------------

@note("ch12.ex5", EXERCISES)
def ex5(d, claim):
    after = d.q("SELECT pr.PayrollRegisterID, pr.EmployeeID, e.JobTitle, ec.CostCenterName, e.TerminationDate, "
                "pp.PeriodStartDate, pp.PeriodEndDate, pp.PayDate, pr.GrossPay, rc.CostCenterName, "
                "(SELECT COUNT(*) FROM PayrollPayment p WHERE p.PayrollRegisterID = pr.PayrollRegisterID) "
                "FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID "
                "JOIN Employee e ON e.EmployeeID = pr.EmployeeID JOIN CostCenter ec ON ec.CostCenterID = e.CostCenterID "
                "JOIN CostCenter rc ON rc.CostCenterID = pr.CostCenterID "
                "WHERE e.TerminationDate IS NOT NULL AND pp.PayDate > e.TerminationDate ORDER BY pp.PayDate")
    claim(len({r[1] for r in after}) == 1, "the registers after termination pay one employee")
    emp, title, center, terminated = after[0][1:5]
    usual = d.one("SELECT AVG(pr.GrossPay) FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID "
                  "WHERE pr.EmployeeID = ? AND pp.PayDate <= ? AND pr.GrossPay > 0", emp, terminated)
    gross = after[0][8]
    claim(all(r[8] == gross for r in after), "the registers after termination have the same gross pay")
    ceo = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Chief Executive Officer'")
    claim({r[0] for r in d.q("SELECT DISTINCT GrossPay FROM PayrollRegister WHERE EmployeeID = ?", ceo)} == {gross},
          "the gross pay is the amount of the chief executive's register")
    charged = {r[9] for r in after}
    claim(len(charged) == 1 and center not in charged, "all are charged to one cost center, not the employee's own")
    ceo_periods = {r[0] for r in d.q("SELECT DISTINCT PayrollPeriodID FROM PayrollRegister WHERE EmployeeID = ?", ceo)}
    after_periods = {r[0] for r in d.q("SELECT PayrollPeriodID FROM PayrollRegister WHERE PayrollRegisterID IN (%s)"
                                       % ",".join(str(r[0]) for r in after))}
    processed_periods = {r[0] for r in d.q("SELECT DISTINCT PayrollPeriodID FROM PayrollRegister")}
    claim(not ceo_periods & after_periods and ceo_periods | after_periods == processed_periods,
          "the chief executive has no register in the periods of the post-termination registers, and one in every other period")
    final = [r for r in after if r[5] <= terminated <= r[6]]
    claim(len(final) == 1 and final[0] is after[0], "only the first register's period includes the termination date")
    unpaid = [r[0] for r in after if r[10] == 0]
    claim(unpaid == [r[0] for r in after[1:]], "the later registers have no payment record")
    registers = d.q("SELECT pr.PayrollRegisterID, pr.EmployeeID, pr.ApprovedByEmployeeID, pr.ApprovedDate, pp.PayDate, pr.NetPay "
                    "FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID")
    approvers = {r[2] for r in registers}
    claim(len(approvers) == 1, "one person approved all the registers")
    approver = approvers.pop()
    approver_title = d.one("SELECT JobTitle FROM Employee WHERE EmployeeID = ?", approver)
    claim(all(r[3] == r[4] for r in registers), "every register was approved on its pay date")
    own = [r for r in registers if r[1] == r[2]]
    early = d.q("SELECT p.PayrollPaymentID, pr.NetPay, e.JobTitle, julianday(pr.ApprovedDate) - julianday(p.PaymentDate) "
                "FROM PayrollPayment p JOIN PayrollRegister pr ON pr.PayrollRegisterID = p.PayrollRegisterID "
                "JOIN Employee e ON e.EmployeeID = pr.EmployeeID WHERE p.PaymentDate < pr.ApprovedDate ORDER BY p.PayrollPaymentID")
    claim(all(r[2] == "Chief Financial Officer" for r in early), "the payments before approval pay the chief financial officer")
    claim(all(r[3] == 1 for r in early), "each was made the day before the register was approved")
    times = round(gross / usual)
    return dict(n_after=word(len(after)), title=title, emp=emp, center=center, terminated=terminated,
                after=[dict(id=r[0], start=r[5], paid=r[7]) for r in after], gross=gross, times=word(times), usual=usual,
                charged=charged.pop(), first=after[0][0], unpaid=unpaid, approver=approver, approver_title=approver_title,
                registers=len(registers), own=len(own), own_net=sum(r[5] for r in own),
                n_early=word(len(early)), early=[r[0] for r in early], early_net=sum(r[1] for r in early))


# --- Exercise 12.6 --------------------------------------------------------------------------------

@note("ch12.ex6", EXERCISES)
def ex6(d, claim):
    dupes = d.q("SELECT SupplierID, InvoiceNumber, COUNT(*), COUNT(DISTINCT GrandTotal) FROM PurchaseInvoice "
                "GROUP BY SupplierID, InvoiceNumber HAVING COUNT(*) > 1")
    claim(all(r[2] == 2 for r in dupes), "each duplicated invoice number appears exactly twice")
    claim(all(r[3] == 2 for r in dupes), "each pair has different amounts")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoice pi JOIN (SELECT SupplierID, InvoiceNumber FROM PurchaseInvoice "
                "GROUP BY 1, 2 HAVING COUNT(*) > 1) x ON x.SupplierID = pi.SupplierID AND x.InvoiceNumber = pi.InvoiceNumber "
                "WHERE (SELECT COUNT(*) FROM DisbursementPayment p WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID) <> 1") == 0,
          "each invoice of the pairs was paid once")
    standard = d.q("SELECT SupplierID, UPPER(TRIM(REPLACE(REPLACE(InvoiceNumber, '-', ''), ' ', ''))) FROM PurchaseInvoice "
                   "GROUP BY 1, 2 HAVING COUNT(*) > 1")
    claim(sorted((s, n) for s, n in standard) ==
          sorted((s, n.replace("-", "").replace(" ", "").strip().upper()) for s, n, *_ in dupes),
          "the standardized numbers find the same pairs and no others")
    checks = d.q("SELECT SupplierID, CheckNumber, COUNT(*) FROM DisbursementPayment WHERE CheckNumber IS NOT NULL "
                 "GROUP BY 1, 2 HAVING COUNT(*) > 1 ORDER BY CheckNumber")
    claim(all(r[2] == 2 for r in checks), "each repeated check number is used twice")
    claim(len({r[0] for r in checks}) == 1, "the repeated check numbers are all for one supplier")
    logged = d.anomalies("duplicate_vendor_payment_reference")
    claim(logged is not None, "the AnomalyLog is available")
    logged = logged or []
    with_check = [r[0] for r in d.q("SELECT CheckNumber FROM DisbursementPayment WHERE DisbursementID IN (%s) "
                                    "AND CheckNumber IS NOT NULL ORDER BY CheckNumber" % ",".join(map(str, logged or [0])))]
    claim(with_check == [r[1] for r in checks], "the logged references with check numbers are the repeated checks")
    end = asof(d)
    pairs = d.q("SELECT julianday(b.PaymentDate) - julianday(a.PaymentDate), a.PurchaseInvoiceID = b.PurchaseInvoiceID "
                "FROM DisbursementPayment a JOIN DisbursementPayment b ON b.SupplierID = a.SupplierID AND b.Amount = a.Amount "
                "AND b.DisbursementID > a.DisbursementID WHERE a.PaymentDate <> b.PaymentDate AND a.PaymentDate <= ?1 "
                "AND b.PaymentDate <= ?1", end)
    claim(not any(r[1] for r in pairs), "no pair pays the same invoice")
    series = []
    for table, column in (("SalesInvoice", "InvoiceNumber"), ("CashReceipt", "ReceiptNumber"), ("PurchaseOrder", "PONumber"),
                          ("JournalEntry", "EntryNumber")):
        rows = d.q(f"SELECT CAST(substr({column}, 4, 4) AS INTEGER), MIN(CAST(substr({column}, 9) AS INTEGER)), "
                   f"MAX(CAST(substr({column}, 9) AS INTEGER)), COUNT(*) FROM {table} GROUP BY 1 ORDER BY 1")
        claim([r[0] for r in rows] == d.years, f"the {table} numbers cover the fiscal years of the window")
        claim(all(r[3] == r[2] - r[1] + 1 for r in rows), f"no {table} numbers are missing")
        series.append([(r[1], r[2]) for r in rows])
    for s in series[:3]:
        claim(all(b[0] == a[1] + 1 for a, b in zip(s, s[1:])), "sales invoices, receipts, and orders continue across years")
    claim(all(lo == 1 for lo, _ in series[3]), "journal entries restart each year")
    payments = d.q("SELECT p.Amount, pi.GrandTotal FROM DisbursementPayment p JOIN PurchaseInvoice pi "
                   "ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate <= ?", end)

    def mad(amounts: list[float]) -> float:
        digits = Counter(int(f"{a:e}"[0]) for a in amounts)
        n = sum(digits.values())
        return sum(abs(digits[k] / n - math.log10(1 + 1 / k)) for k in range(1, 10)) / 9

    smallest = min(a for a, _ in payments)
    claim(smallest > 0, "every payment is positive")
    return dict(n_dupes=word(len(dupes)), n_checks=word(len(checks)).capitalize(), check_supplier=checks[0][0],
                checks=[r[1] for r in checks], n_logged=word(len(logged)), n_with_check=word(len(with_check)),
                pairs=len(pairs), within30=sum(1 for r in pairs if abs(r[0]) <= 30),
                within14=sum(1 for r in pairs if abs(r[0]) <= 14), series=series,
                mad_all=mad([a for a, _ in payments]), mad_full=mad([a for a, g in payments if abs(a - g) < 0.005]),
                mad_partial=mad([a for a, g in payments if a < g - 0.005]), smallest=smallest, smallest_e=f"{smallest:e}")
