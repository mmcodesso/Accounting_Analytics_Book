"""Chapter 12's exercise solutions in SQL (instructor files): one script per exercise, `Ex 12.1.sql` to `Ex 12.6.sql`.

Each script follows the audit query library of the chapter (Audit.sql): a header, then one test after another under a
comment that names it and states its population and expected result, and a model answer that records a disposition for
every exception. The checks take their expected values from the note context functions of `facts/notes/ch12.py` (the
values of the generated instructor notes, and its helpers `invoices_by_delivery`, `late_december_cost` and
`surge_days`) or from read-only SQL of this module. Tests the chapter's library already holds (L5, L6, H8, H9) are
reused where an exercise extends them.
"""

from __future__ import annotations

from sqlbuild.script import Check

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def notes(b):
    b.data                                       # puts facts/ on sys.path
    from notes import ch12
    return ch12


def context(b, name: str) -> dict:
    """The values of a generated note: its context function, called with a claim function that ignores its arguments."""
    return getattr(notes(b), name)(b.data, lambda *a, **k: None)


def money(x: float) -> str:
    return f"{x:,.2f}"


def signed(x: float) -> str:
    return f"{x:+,.2f}"


# --- Exercise 12.1 ---------------------------------------------------------------------------------------------------

DELIVERY = """\
WITH Shipped AS (
    SELECT sil.SalesInvoiceID, MIN(s.ShipmentDate) AS ShipmentDate,
        MAX(s.DeliveryDate) AS DeliveryDate
    FROM SalesInvoiceLine AS sil
        INNER JOIN ShipmentLine AS sl
            ON sl.ShipmentLineID = sil.ShipmentLineID
        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
    GROUP BY sil.SalesInvoiceID
),
Posted AS (
    SELECT SourceDocumentID AS SalesInvoiceID,
        MIN(PostingDate) AS PostingDate
    FROM GLEntry
    WHERE SourceDocumentType = 'SalesInvoice'
    GROUP BY SourceDocumentID
)"""

INVOICES = """\
FROM SalesInvoice AS si
    INNER JOIN Shipped AS sh ON sh.SalesInvoiceID = si.SalesInvoiceID
    INNER JOIN Posted AS p ON p.SalesInvoiceID = si.SalesInvoiceID"""

UNBILLED = """\
FROM ShipmentLine AS sl
    INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
    INNER JOIN SalesOrderLine AS sol
        ON sol.SalesOrderLineID = sl.SalesOrderLineID
    LEFT JOIN SalesInvoiceLine AS sil
        ON sil.ShipmentLineID = sl.ShipmentLineID
WHERE sil.SalesInvoiceLineID IS NULL"""

SALES_VALUE = "ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2)"


def ex1(b):
    v = context(b, "ex1")
    n = notes(b)
    d = b.data
    invoices = n.invoices_by_delivery(d)
    late = [i for i in invoices if i["late"]]
    before = sorted(i["number"] for i in invoices if i["before"])
    s1, s2, value, cost = v["g1"]["sub"], v["g2"]["sub"], v["value"], v["cost"]
    effects = {d.F: -s1, d.P: s1 - s2, d.C: s2 - value}
    pi_count = d.one("SELECT COUNT(*) FROM PurchaseInvoice")
    on_invoice_date = d.one(
        "SELECT COUNT(*) FROM PurchaseInvoice pi JOIN (SELECT SourceDocumentID AS id, MIN(PostingDate) AS f, "
        "MAX(PostingDate) AS l FROM GLEntry WHERE SourceDocumentType = 'PurchaseInvoice' GROUP BY 1) p "
        "ON p.id = pi.PurchaseInvoiceID WHERE p.f = pi.InvoiceDate AND p.l = pi.InvoiceDate")
    crossing = v["crossing"][0]
    accrual = d.one("SELECT je.EntryNumber FROM PurchaseInvoiceLine pil JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = "
                    "pil.PurchaseInvoiceID JOIN JournalEntry je ON je.JournalEntryID = pil.AccrualJournalEntryID "
                    "WHERE pi.InvoiceNumber = ?", crossing["number"])
    full = {y: n.late_december_cost(d, y) for y in (d.F, d.P)}
    # the late December of the current year, per working day of the last eight processed periods
    periods = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate FROM PayrollPeriod WHERE Status = 'Processed' "
                  "ORDER BY PeriodStartDate DESC LIMIT 8")
    ids = ",".join(str(p[0]) for p in periods)
    total, mfg = d.q(f"SELECT SUM(r.GrossPay + r.EmployerPayrollTax + r.EmployerBenefits), SUM(CASE WHEN "
                     f"c.CostCenterName = 'Manufacturing' THEN r.GrossPay + r.EmployerPayrollTax + r.EmployerBenefits "
                     f"ELSE 0 END) FROM PayrollRegister r JOIN CostCenter c ON c.CostCenterID = r.CostCenterID "
                     f"WHERE r.PayrollPeriodID IN ({ids})")[0]
    base_days = n.working_days(d, min(p[1] for p in periods), max(p[2] for p in periods))
    start = d.one("SELECT MIN(PeriodStartDate) FROM PayrollPeriod WHERE Status <> 'Processed'")
    left = n.working_days(d, start, f"{d.C}-12-31")
    estimate, estimate_mfg = total / base_days * left, mfg / base_days * left
    s = b.script("Ex 12.1.sql", "cutoff of revenue, supplier invoices, and payroll at each year-end",
                 "revenue by delivery date; supplier invoices by posting date; payroll by work date; "
                 "effects by fiscal year")
    s.query("Exercise 12.1, test C1: revenue posted in a different fiscal year from the delivery",
            "Population: all sales invoices (test L5); expected: no rows",
            f"""\
{DELIVERY}
SELECT si.InvoiceNumber, si.InvoiceDate, sh.ShipmentDate,
    sh.DeliveryDate, p.PostingDate, ROUND(si.SubTotal, 2) AS SubTotal
{INVOICES}
WHERE strftime('%Y', p.PostingDate) <> strftime('%Y', sh.DeliveryDate)
ORDER BY p.PostingDate, si.InvoiceNumber;""",
            [Check("invoices posted in another year", len(late), len),
             Check(f"for deliveries of {d.F}", round(s1, 2),
                   lambda r: round(sum(x for x, y in zip(r.col("SubTotal"), r.col("DeliveryDate"))
                                       if y.startswith(str(d.F))), 2)),
             Check(f"for deliveries of {d.P}", round(s2, 2),
                   lambda r: round(sum(x for x, y in zip(r.col("SubTotal"), r.col("DeliveryDate"))
                                       if y.startswith(str(d.P))), 2)),
             Check("the invoices dated before the year-end and posted after it",
                   [i["number"] for i in v["g1"]["odd"] + v["g2"]["odd"]],
                   lambda r: [x for x, y, p in zip(r.col("InvoiceNumber"), r.col("InvoiceDate"), r.col("PostingDate"))
                              if y[:4] != p[:4]])])
    s.query("Exercise 12.1, test C2: invoices dated before their shipment, posted in the year of delivery",
            "Population: all sales invoices; expected: no rows",
            f"""\
{DELIVERY}
SELECT si.InvoiceNumber, si.InvoiceDate, sh.ShipmentDate,
    sh.DeliveryDate, p.PostingDate, ROUND(si.SubTotal, 2) AS SubTotal
{INVOICES}
WHERE strftime('%Y', p.PostingDate) = strftime('%Y', sh.DeliveryDate)
    AND si.InvoiceDate < sh.ShipmentDate
ORDER BY si.InvoiceNumber;""",
            [Check("invoices dated before their shipment", len(before), len),
             Check("the invoices", before, lambda r: r.col("InvoiceNumber"))])
    s.query("Exercise 12.1, test C3: the effect of revenue cutoff on each fiscal year",
            "Population: tests C1 and L6; expected: no effect in any year",
            f"""\
{DELIVERY},
Late AS (
    SELECT CAST(strftime('%Y', sh.DeliveryDate) AS INTEGER)
            AS DeliveryYear,
        CAST(strftime('%Y', p.PostingDate) AS INTEGER) AS PostingYear,
        si.SubTotal
    {INVOICES.replace(chr(10), chr(10) + '    ')}
    WHERE strftime('%Y', p.PostingDate)
        <> strftime('%Y', sh.DeliveryDate)
),
Unbilled AS (
    SELECT CAST(strftime('%Y', s.ShipmentDate) AS INTEGER)
            AS ShipmentYear,
        {SALES_VALUE}
            AS SalesValue
    {UNBILLED.replace(chr(10), chr(10) + '    ')}
),
Effects AS (
    SELECT PostingYear AS FiscalYear, SubTotal AS FromYearBefore,
        0 AS ToNextYear, 0 AS NeverInvoiced
    FROM Late
    UNION ALL
    SELECT DeliveryYear, 0, SubTotal, 0
    FROM Late
    UNION ALL
    SELECT ShipmentYear, 0, 0, SalesValue
    FROM Unbilled
)
SELECT FiscalYear, ROUND(SUM(FromYearBefore), 2) AS FromYearBefore,
    ROUND(SUM(ToNextYear), 2) AS ToNextYear,
    ROUND(SUM(NeverInvoiced), 2) AS NeverInvoiced,
    ROUND(SUM(FromYearBefore) - SUM(ToNextYear) - SUM(NeverInvoiced), 2)
        AS NetEffect
FROM Effects
GROUP BY FiscalYear
ORDER BY FiscalYear;""",
            [Check("fiscal years", d.years, lambda r: r.col("FiscalYear")),
             Check(f"{d.C} never invoiced (order price)", round(value, 2),
                   lambda r: r.where(FiscalYear=d.C)["NeverInvoiced"])] +
            [Check(f"{y} net effect", round(e, 2), lambda r, y=y: r.where(FiscalYear=y)["NetEffect"])
             for y, e in effects.items()])
    s.query("Exercise 12.1, test C4: cost of goods sold posted at shipment, and the unbilled lines' cost",
            "Population: shipment postings and the lines of test L6; expected: cost on the shipment date",
            f"""\
SELECT
    (SELECT COUNT(*)
     FROM GLEntry AS gl
        INNER JOIN Shipment AS s ON s.ShipmentID = gl.SourceDocumentID
     WHERE gl.SourceDocumentType = 'Shipment'
        AND gl.PostingDate <> s.ShipmentDate) AS CostOffShipmentDate,
    COUNT(*) AS UnbilledLines,
    ROUND(SUM(sl.ExtendedStandardCost), 2) AS UnbilledStandardCost,
    ROUND(SUM(ROUND(sl.QuantityShipped * sol.UnitPrice
        * (1 - sol.Discount), 2)), 2) AS UnbilledSalesValue
{UNBILLED};""",
            [Check("shipment postings on another date", 0, lambda r: r.value("CostOffShipmentDate")),
             Check("unbilled lines", d.one("SELECT COUNT(*) FROM ShipmentLine sl LEFT JOIN SalesInvoiceLine sil "
                                           "ON sil.ShipmentLineID = sl.ShipmentLineID "
                                           "WHERE sil.SalesInvoiceLineID IS NULL"),
                   lambda r: r.value("UnbilledLines")),
             Check("their standard cost (posted to cost of goods sold)", round(cost, 2),
                   lambda r: r.value("UnbilledStandardCost")),
             Check("their value at order price", round(value, 2), lambda r: r.value("UnbilledSalesValue"))])
    s.query("Exercise 12.1, test C5: supplier invoices by the date their ledger rows are posted on",
            "Population: all supplier invoices; expected: posted on one date, in the year of the invoice",
            """\
WITH Posted AS (
    SELECT SourceDocumentID AS PurchaseInvoiceID,
        MIN(PostingDate) AS FirstPosting, MAX(PostingDate) AS LastPosting
    FROM GLEntry
    WHERE SourceDocumentType = 'PurchaseInvoice'
    GROUP BY SourceDocumentID
)
SELECT COUNT(*) AS Invoices,
    SUM(CASE WHEN p.FirstPosting = pi.InvoiceDate
        AND p.LastPosting = pi.InvoiceDate THEN 1 ELSE 0 END)
        AS PostedOnInvoiceDate,
    SUM(CASE WHEN p.FirstPosting = pi.ReceivedDate
        AND p.LastPosting = pi.ReceivedDate THEN 1 ELSE 0 END)
        AS PostedOnReceivedDate,
    SUM(CASE WHEN strftime('%Y', p.FirstPosting)
        <> strftime('%Y', pi.InvoiceDate) THEN 1 ELSE 0 END)
        AS PostedInAnotherYear
FROM PurchaseInvoice AS pi
    INNER JOIN Posted AS p ON p.PurchaseInvoiceID = pi.PurchaseInvoiceID;""",
            [Check("supplier invoices", pi_count, lambda r: r.value("Invoices")),
             Check("posted on the invoice date", on_invoice_date, lambda r: r.value("PostedOnInvoiceDate")),
             Check("posted on the received date (all)", pi_count - len(v["late_pi"]),
                   lambda r: r.value("PostedOnReceivedDate")),
             Check("posted in another year than dated", len(v["crossing"]), lambda r: r.value("PostedInAnotherYear"))])
    s.query("Exercise 12.1, test C6: the supplier invoices dated in one year and posted in the next",
            "Population: all supplier invoices; expected: no rows",
            """\
SELECT pi.InvoiceNumber, pi.SupplierID, pi.InvoiceDate, pi.ReceivedDate,
    ROUND(pi.GrandTotal, 2) AS GrandTotal,
    (SELECT GROUP_CONCAT(je.EntryNumber, ', ')
     FROM PurchaseInvoiceLine AS pil
        INNER JOIN JournalEntry AS je
            ON je.JournalEntryID = pil.AccrualJournalEntryID
     WHERE pil.PurchaseInvoiceID = pi.PurchaseInvoiceID) AS AccrualEntries
FROM PurchaseInvoice AS pi
WHERE strftime('%Y', pi.InvoiceDate) <> strftime('%Y', pi.ReceivedDate)
ORDER BY pi.ReceivedDate, pi.InvoiceNumber;""",
            [Check("invoices", len(v["crossing"]), len),
             Check("the invoice", crossing["number"], lambda r: r.cell(0, "InvoiceNumber")),
             Check("its supplier", crossing["id"], lambda r: r.cell(0, "SupplierID")),
             Check("its amount", crossing["total"], lambda r: r.cell(0, "GrandTotal")),
             Check("its accrual entry", accrual, lambda r: r.cell(0, "AccrualEntries"))])
    s.query("Exercise 12.1, test C7: hourly labor cost by the year of the work and of its pay period",
            "Population: all labor time; expected: work and pay in the same fiscal year",
            """\
SELECT strftime('%Y', lt.WorkDate) AS WorkYear, pp.FiscalYear AS PaidYear,
    MIN(lt.WorkDate) AS FirstWorkDate, MAX(lt.WorkDate) AS LastWorkDate,
    ROUND(SUM(lt.ExtendedLaborCost), 2) AS LaborCost,
    ROUND(SUM(CASE WHEN lt.LaborType <> 'NonManufacturing'
        THEN lt.ExtendedLaborCost ELSE 0 END), 2) AS ManufacturingCost
FROM LaborTimeEntry AS lt
    INNER JOIN PayrollPeriod AS pp
        ON pp.PayrollPeriodID = lt.PayrollPeriodID
GROUP BY WorkYear, PaidYear
ORDER BY WorkYear, PaidYear;""",
            [Check("year pairs", 2 * len(d.years) - 1, len)] +
            [c for h in v["hourly"] for c in (
                Check(f"{h['work']} work paid in {h['paid']}", round(h["total"], 2),
                      lambda r, h=h: r.where(WorkYear=str(h["work"]), PaidYear=h["paid"])["LaborCost"]),
                Check(f"of it manufacturing", round(h["mfg"], 2),
                      lambda r, h=h: r.where(WorkYear=str(h["work"]), PaidYear=h["paid"])["ManufacturingCost"]),
                Check(f"{h['work']} work paid in {h['paid']}, all in December", f"{h['work']}-12",
                      lambda r, h=h: r.where(WorkYear=str(h["work"]), PaidYear=h["paid"])["FirstWorkDate"][:7]))])
    s.query("Exercise 12.1, test C8: the full cost of the late-December work paid in the next fiscal year",
            "Population: the pay periods that cross a year-end (test L7); expected: none unrecorded",
            """\
WITH Crossing AS (
    SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate,
        strftime('%Y', PeriodStartDate) AS WorkYear
    FROM PayrollPeriod
    WHERE strftime('%Y', PeriodStartDate) <> strftime('%Y', PayDate)
),
PeriodDays AS (
    SELECT c.PayrollPeriodID,
        SUM(CASE WHEN cal.CalendarDate <= c.WorkYear || '-12-31'
            THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS ShareInYear
    FROM Crossing AS c
        INNER JOIN WorkCenterCalendar AS cal
            ON cal.CalendarDate
                BETWEEN c.PeriodStartDate AND c.PeriodEndDate
    WHERE cal.WorkCenterID = (SELECT MIN(WorkCenterID)
            FROM WorkCenterCalendar)
        AND cal.IsWorkingDay = 1
    GROUP BY c.PayrollPeriodID
),
Registers AS (
    SELECT PayrollPeriodID, SUM(GrossPay) AS GrossPay,
        SUM(EmployerPayrollTax + EmployerBenefits) AS Charges
    FROM PayrollRegister
    GROUP BY PayrollPeriodID
),
Salaries AS (
    SELECT pr.PayrollPeriodID, SUM(prl.Amount) AS Salaries
    FROM PayrollRegisterLine AS prl
        INNER JOIN PayrollRegister AS pr
            ON pr.PayrollRegisterID = prl.PayrollRegisterID
    WHERE prl.LineType = 'Salary Earnings'
    GROUP BY pr.PayrollPeriodID
),
Hourly AS (
    SELECT c.PayrollPeriodID, SUM(lt.ExtendedLaborCost) AS HourlyCost
    FROM Crossing AS c
        INNER JOIN LaborTimeEntry AS lt
            ON lt.PayrollPeriodID = c.PayrollPeriodID
            AND strftime('%Y', lt.WorkDate) = c.WorkYear
    GROUP BY c.PayrollPeriodID
)
SELECT c.WorkYear, ROUND(SUM(h.HourlyCost), 2) AS HourlyLabor,
    ROUND(SUM(s.Salaries * d.ShareInYear), 2) AS SalariesInYear,
    ROUND(SUM(r.Charges) / SUM(r.GrossPay), 4) AS ChargeRate,
    ROUND((SUM(h.HourlyCost) + SUM(s.Salaries * d.ShareInYear))
        * (1 + SUM(r.Charges) / SUM(r.GrossPay)), 2) AS FullCost
FROM Crossing AS c
    INNER JOIN Registers AS r ON r.PayrollPeriodID = c.PayrollPeriodID
    INNER JOIN PeriodDays AS d ON d.PayrollPeriodID = c.PayrollPeriodID
    LEFT JOIN Salaries AS s ON s.PayrollPeriodID = c.PayrollPeriodID
    LEFT JOIN Hourly AS h ON h.PayrollPeriodID = c.PayrollPeriodID
GROUP BY c.WorkYear
ORDER BY c.WorkYear;""",
            [Check("year-ends with late-December work paid later", 2, len)] +
            [Check(f"{y} full cost", round(cst, 2), lambda r, y=y: r.where(WorkYear=str(y))["FullCost"])
             for y, cst in full.items()] +
            [Check(f"{y} full cost, rounded as the note gives it", thousands, lambda r, y=y:
                   int(round(r.where(WorkYear=str(y))["FullCost"], -3)))
             for y, thousands in zip((d.F, d.P), v["full"])])
    s.query("Exercise 12.1, test C9: the payroll cost of 14-31 December 2026, which has no registers",
            "Population: the last eight processed pay periods; expected: an estimate to accrue",
            f"""\
WITH Params AS (
    SELECT '{start}' AS FromDate, '{d.C}-12-31' AS AsOfDate
),
LastPeriods AS (
    SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate
    FROM PayrollPeriod
    WHERE Status = 'Processed'
    ORDER BY PeriodStartDate DESC
    LIMIT 8
),
PeriodCost AS (
    SELECT pr.PayrollPeriodID,
        SUM(pr.GrossPay + pr.EmployerPayrollTax + pr.EmployerBenefits)
            AS PayrollCost,
        SUM(CASE WHEN cc.CostCenterName = 'Manufacturing'
            THEN pr.GrossPay + pr.EmployerPayrollTax + pr.EmployerBenefits
            ELSE 0 END) AS ManufacturingCost
    FROM PayrollRegister AS pr
        INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
    WHERE pr.PayrollPeriodID IN (SELECT PayrollPeriodID FROM LastPeriods)
    GROUP BY pr.PayrollPeriodID
),
WorkingDays AS (
    SELECT
        SUM(CASE WHEN CalendarDate
            BETWEEN (SELECT MIN(PeriodStartDate) FROM LastPeriods)
            AND (SELECT MAX(PeriodEndDate) FROM LastPeriods)
            THEN 1 ELSE 0 END) AS InPeriods,
        SUM(CASE WHEN CalendarDate BETWEEN (SELECT FromDate FROM Params)
            AND (SELECT AsOfDate FROM Params) THEN 1 ELSE 0 END)
            AS Unrecorded
    FROM WorkCenterCalendar
    WHERE WorkCenterID = (SELECT MIN(WorkCenterID) FROM WorkCenterCalendar)
        AND IsWorkingDay = 1
)
SELECT COUNT(*) AS Periods,
    ROUND(AVG(PayrollCost), 2) AS AveragePeriodCost,
    ROUND(AVG(ManufacturingCost), 2) AS AverageManufacturing,
    (SELECT InPeriods FROM WorkingDays) AS WorkingDays,
    (SELECT Unrecorded FROM WorkingDays) AS UnrecordedDays,
    ROUND(SUM(PayrollCost) / (SELECT InPeriods FROM WorkingDays)
        * (SELECT Unrecorded FROM WorkingDays), 2) AS EstimatedCost,
    ROUND(SUM(ManufacturingCost) / (SELECT InPeriods FROM WorkingDays)
        * (SELECT Unrecorded FROM WorkingDays), 2)
        AS EstimatedManufacturing
FROM PeriodCost;""",
            [Check("pay periods", len(periods), lambda r: r.value("Periods")),
             Check(f"average cost of periods {v['first']}-{v['last']}", round(v["avg"], 2),
                   lambda r: r.value("AveragePeriodCost")),
             Check("of it manufacturing", round(v["avg_mfg"], 2), lambda r: r.value("AverageManufacturing")),
             Check("working days not recorded", v["days"], lambda r: r.value("UnrecordedDays")),
             Check("estimated cost", round(estimate, 2), lambda r: r.value("EstimatedCost")),
             Check(f"within the note's range ({v['low']:,}-{v['high']:,})", True,
                   lambda r: v["low"] <= round(r.value("EstimatedCost"), -3) <= v["high"]),
             Check("estimated manufacturing cost", round(estimate_mfg, 2), lambda r: r.value("EstimatedManufacturing")),
             Check(f"within the note's range ({v['mfg_low']:,}-{v['mfg_high']:,})", True,
                   lambda r: v["mfg_low"] <= round(r.value("EstimatedManufacturing"), -3) <= v["mfg_high"])])
    s.query("Exercise 12.1, test C10: accrued payroll (account 2030) at each year-end",
            "Population: postings to 2030 to each year-end; expected: the unpaid wages",
            """\
SELECT ye.YearEnd, ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance
FROM (
    SELECT '2024-12-31' AS YearEnd
    UNION ALL SELECT '2025-12-31'
    UNION ALL SELECT '2026-12-31'
) AS ye
    INNER JOIN Account AS a ON a.AccountNumber = 2030
    INNER JOIN GLEntry AS gl
        ON gl.AccountID = a.AccountID AND gl.PostingDate <= ye.YearEnd
GROUP BY ye.YearEnd
ORDER BY ye.YearEnd;""",
            [Check("year-ends", 3, len)] +
            [Check(f"{y}-12-31 balance (the opening line only)", v["opening"],
                   lambda r, y=y: r.where(YearEnd=f"{y}-12-31")["Balance"]) for y in d.years])
    liab = {d.F: full[d.F], d.P: full[d.P], d.C: estimate}
    s.answer("Requirement (2)", f"""\
Cost of goods sold is posted on the shipment date (test C4 finds no shipment posting on another date), so it falls in
the year of the delivery whatever happens to the invoice. When the revenue moves to the next year, or is never
billed, the cost stays where it belongs and only the revenue is misplaced: the year's gross margin moves by the whole
revenue amount, while cost of goods sold does not move at all. For the nine unbilled lines of {d.C}, cost of
{money(cost)} is in {d.C}'s cost of goods sold with no revenue of {money(value)} beside it.""")
    s.answer("Requirement (3)", f"""\
All {pi_count:,} supplier invoices are posted on their ReceivedDate (test C5): Charles River records a supplier
invoice when it receives it, not on the date the supplier wrote on it (the two dates are the same for
{on_invoice_date:,} of them).
Only {crossing['number']} (supplier {crossing['id']}, dated {crossing['date']}, received {crossing['received']},
{money(crossing['total'])}) crosses a year-end. Its line refers to the accrual entry {accrual}, so the liability for
the service was carried in accrued expenses at the end of {d.P}; it is not an unrecorded liability.""")
    s.answer("Requirement (5), memo to the controller", f"""\
To: the controller. Subject: cutoff at each year-end.

Revenue. Revenue is posted when the invoice is posted, and invoices for goods delivered in December are posted in
January: {len([i for i in late if i['delivered'][:4] == str(d.F)])} invoices for December {d.F} deliveries
({money(s1)}) and {len([i for i in late if i['delivered'][:4] == str(d.P)])} for December {d.P} deliveries
({money(s2)}), among them {', '.join(i['number'] for i in v['g2']['odd'])}, dated before the year-end. Nine December {d.C} shipment lines were never invoiced
({money(value)} at order price). The net effect on revenue is {signed(effects[d.F])} in {d.F},
{signed(effects[d.P])} in {d.P}, and {signed(effects[d.C])} in {d.C}; because cost of goods sold is posted at
shipment, gross margin moves by the same amounts. The {len(before)} invoices dated before their shipment are posted in
the year of delivery: an invoice-dating failure for the billing team, not a cutoff error.

Supplier invoices are posted on the date received, and the one invoice that crosses a year-end was accrued, so the
payables cutoff holds.

Payroll. Wages are recorded only when paid, and account 2030 holds the opening {money(v['opening'])} at every
year-end, so no year-end accrues the wages earned in late December. The work of late December cost about
{v['full'][0]:,} in {d.F} and {v['full'][1]:,} in {d.P} (hourly labor by work date of
{money(v['hourly'][0]['total'])} and {money(v['hourly'][1]['total'])}, plus salaries by working day and employer
taxes and benefits), and the {v['days']} working days of 14-31 December {d.C} are estimated at {money(estimate)}
(the cost of periods {v['first']}-{v['last']}, {money(v['avg'])} a period on average, per working day; spreading
salaries over weekdays instead gives about {v['high']:,}). Each year-end's liability is understated by these amounts, and each year's expense by the change
between them.

Recommendation: before the fiscal {d.C} statements are final, record revenue for the December deliveries billed in
January and for the unbilled lines, and accrue the late-December payroll of about {round(liab[d.C], -3):,.0f}; then make both
part of every close, with a cutoff report of deliveries not yet invoiced and a payroll accrual from the open pay
periods.""")
    s.answer("Dispositions", f"""\
C1 ({len(late)} invoices): revenue cutoff errors, to be adjusted in the year of delivery; the {d.C} effect
({signed(effects[d.C])} with C3) is proposed as an adjustment before the statements are final. C2 ({len(before)}
invoices): no revenue effect; reported to billing as invoices dated before shipment. C3 and C4: the unbilled lines
({money(value)}) are referred for billing and accrued revenue at {d.C}-12-31; no exception in the cost postings. C5:
no exception. C6 ({crossing['number']}): no exception, accrued by {accrual}. C7 and C8: late-December payroll recorded in the
next fiscal year, an accrual deficiency in every year. C9: the {d.C} accrual of about {money(estimate)} is proposed.
C10: account 2030 carries only the opening balance; the missing accrual is reported as a control deficiency of the
close.""")


# --- Exercise 12.2 ---------------------------------------------------------------------------------------------------

OPEN = """\
WITH Params AS (
    SELECT '2026-12-31' AS AsOfDate
),
Applied AS (
    SELECT SalesInvoiceID, SUM(AppliedAmount) AS Applied
    FROM CashReceiptApplication
    WHERE ApplicationDate <= (SELECT AsOfDate FROM Params)
    GROUP BY SalesInvoiceID
),
Credited AS (
    SELECT OriginalSalesInvoiceID AS SalesInvoiceID,
        SUM(GrandTotal) AS Credited
    FROM CreditMemo
    WHERE CreditMemoDate <= (SELECT AsOfDate FROM Params)
    GROUP BY OriginalSalesInvoiceID
),
Balances AS (
    SELECT si.SalesInvoiceID, si.InvoiceNumber, si.CustomerID,
        si.InvoiceDate, si.DueDate, si.GrandTotal,
        COALESCE(a.Applied, 0) AS Applied,
        COALESCE(c.Credited, 0) AS Credited,
        ROUND(si.GrandTotal - COALESCE(a.Applied, 0)
            - COALESCE(c.Credited, 0), 2) AS OpenBalance,
        julianday((SELECT AsOfDate FROM Params))
            - julianday(si.DueDate) AS DaysPastDue
    FROM SalesInvoice AS si
        LEFT JOIN Applied AS a ON a.SalesInvoiceID = si.SalesInvoiceID
        LEFT JOIN Credited AS c ON c.SalesInvoiceID = si.SalesInvoiceID
    WHERE si.InvoiceDate <= (SELECT AsOfDate FROM Params)
)"""

BUCKET = """\
CASE
            WHEN DaysPastDue <= 0 THEN 'Current'
            WHEN DaysPastDue <= 30 THEN '1-30 days'
            WHEN DaysPastDue <= 60 THEN '31-60 days'
            WHEN DaysPastDue <= 90 THEN '61-90 days'
            ELSE 'Over 90 days'
        END"""

CUSTOMERS = """\
Customers AS (
    SELECT CustomerID, SUM(OpenBalance) AS OpenBalance
    FROM Balances
    WHERE OpenBalance > 0
    GROUP BY CustomerID
)"""

GRNI = """\
WITH Params AS (
    SELECT '2026-12-31' AS AsOfDate
),
InvoicedByReceipt AS (
    SELECT pil.GoodsReceiptLineID, SUM(pil.Quantity) AS QtyInvoiced
    FROM PurchaseInvoiceLine AS pil
        INNER JOIN PurchaseInvoice AS pi
            ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID
    WHERE pi.ReceivedDate <= (SELECT AsOfDate FROM Params)
    GROUP BY pil.GoodsReceiptLineID
),
NotInvoiced AS (
    SELECT grl.GoodsReceiptLineID, gr.ReceiptNumber, gr.ReceiptDate,
        po.SupplierID, grl.QuantityReceived,
        COALESCE(ibr.QtyInvoiced, 0) AS QtyInvoiced,
        grl.ExtendedStandardCost
            * (1 - COALESCE(ibr.QtyInvoiced, 0) / grl.QuantityReceived)
            AS ValueNotInvoiced
    FROM GoodsReceiptLine AS grl
        INNER JOIN GoodsReceipt AS gr
            ON gr.GoodsReceiptID = grl.GoodsReceiptID
        INNER JOIN PurchaseOrder AS po
            ON po.PurchaseOrderID = gr.PurchaseOrderID
        LEFT JOIN InvoicedByReceipt AS ibr
            ON ibr.GoodsReceiptLineID = grl.GoodsReceiptLineID
    WHERE gr.ReceiptDate <= (SELECT AsOfDate FROM Params)
        AND COALESCE(ibr.QtyInvoiced, 0) < grl.QuantityReceived - 0.0001
)"""


def ex2(b):
    v = context(b, "ex2")
    d = b.data
    names = ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]
    buckets = {name: bk for name, bk in zip(names, v["b"])}
    strata_names = ["Under 1,000", "1,000-9,999", "10,000-49,999", "50,000 and over"]
    strata = dict(zip(strata_names, v["strata"]))
    opening = v["ledger"] - v["total"]
    five = d.q("SELECT po.SupplierID, COUNT(*), ROUND(SUM(grl.ExtendedStandardCost * (1 - COALESCE(ibr.q, 0) / "
               "grl.QuantityReceived)), 2) AS v FROM GoodsReceiptLine grl JOIN GoodsReceipt gr ON gr.GoodsReceiptID = "
               "grl.GoodsReceiptID JOIN PurchaseOrder po ON po.PurchaseOrderID = gr.PurchaseOrderID LEFT JOIN (SELECT "
               "pil.GoodsReceiptLineID AS id, SUM(pil.Quantity) AS q FROM PurchaseInvoiceLine pil JOIN PurchaseInvoice pi "
               "ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID WHERE pi.ReceivedDate <= ?1 GROUP BY 1) ibr "
               "ON ibr.id = grl.GoodsReceiptLineID WHERE gr.ReceiptDate <= ?1 AND COALESCE(ibr.q, 0) < "
               "grl.QuantityReceived - 0.0001 GROUP BY 1 ORDER BY v DESC LIMIT 5", v["asof"])
    s = b.script("Ex 12.2.sql", "the open balances at the end of fiscal 2026: receivables and receipts not invoiced",
                 "open invoices aged and reconciled to 1020; customer strata; receipts not invoiced against 2020")
    s.query("Exercise 12.2, test A1: the open balance of each sales invoice at the as-of date",
            f"Population: invoices dated by {v['asof']}; expected: the open receivables",
            f"""\
{OPEN}
SELECT InvoiceNumber, CustomerID, InvoiceDate, DueDate, GrandTotal,
    ROUND(Applied, 2) AS Applied, ROUND(Credited, 2) AS Credited,
    OpenBalance
FROM Balances
WHERE OpenBalance > 0
ORDER BY CustomerID, InvoiceDate;""",
            [Check("invoices with a positive balance", v["n"], len),
             Check("open balance", round(v["total"], 2), lambda r: round(r.total("OpenBalance"), 2)),
             Check("customers", v["customers"], lambda r: len(set(r.col("CustomerID"))))])
    s.query("Exercise 12.2, test A2: the open balances aged by days past due",
            "Population: the invoices of test A1; expected: most of the balance current",
            f"""\
{OPEN}
SELECT
    {BUCKET.replace(chr(10) + '    ', chr(10))} AS AgingBucket,
    COUNT(*) AS Invoices, ROUND(SUM(OpenBalance), 2) AS OpenBalance
FROM Balances
WHERE OpenBalance > 0
GROUP BY AgingBucket
ORDER BY MIN(DaysPastDue);""",
            [Check("buckets", names, lambda r: r.col("AgingBucket"))] +
            [c for name, bk in buckets.items() for c in (
                Check(f"{name} invoices", bk["n"], lambda r, name=name: r.where(AgingBucket=name)["Invoices"]),
                Check(f"{name} balance", round(bk["amount"], 2),
                      lambda r, name=name: r.where(AgingBucket=name)["OpenBalance"]))])
    s.query("Exercise 12.2, test A3: the open balances against account 1020 Accounts Receivable",
            "Population: the invoices of test A1 and the ledger; expected: no difference",
            f"""\
{OPEN},
Ledger AS (
    SELECT SUM(gl.Debit) - SUM(gl.Credit) AS Balance,
        SUM(CASE WHEN gl.VoucherNumber = 'JE-2024-000001'
            THEN gl.Debit - gl.Credit ELSE 0 END) AS OpeningLine
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber = 1020
        AND gl.PostingDate <= (SELECT AsOfDate FROM Params)
)
SELECT ROUND(SUM(b.OpenBalance), 2) AS OpenInvoices,
    ROUND((SELECT Balance FROM Ledger), 2) AS Account1020,
    ROUND((SELECT Balance FROM Ledger) - SUM(b.OpenBalance), 2)
        AS Difference,
    ROUND((SELECT OpeningLine FROM Ledger), 2) AS OpeningEntryLine
FROM Balances AS b
WHERE b.OpenBalance > 0;""",
            [Check("open invoices", round(v["total"], 2), lambda r: r.value("OpenInvoices")),
             Check("account 1020", round(v["ledger"], 2), lambda r: r.value("Account1020")),
             Check("difference", round(opening, 2), lambda r: r.value("Difference")),
             Check(f"the opening line of {v['entry']}", round(opening, 2), lambda r: r.value("OpeningEntryLine"))])
    s.query("Exercise 12.2, test A4: the invoices with a negative balance",
            "Population: the invoices dated by the as-of date; expected: no rows",
            f"""\
{OPEN},
Negative AS (
    SELECT SalesInvoiceID, OpenBalance,
        CASE WHEN Applied >= GrandTotal - 0.005 THEN 1 ELSE 0 END
            AS PaidInFull
    FROM Balances
    WHERE OpenBalance < 0
)
SELECT COUNT(*) AS Invoices, ROUND(SUM(n.OpenBalance), 2) AS Balance,
    SUM(n.PaidInFull) AS PaidInFull,
    SUM(CASE WHEN EXISTS (
        SELECT 1
        FROM CreditMemo AS cm
            INNER JOIN CustomerRefund AS rf
                ON rf.CreditMemoID = cm.CreditMemoID
        WHERE cm.OriginalSalesInvoiceID = n.SalesInvoiceID
            AND rf.RefundDate <= (SELECT AsOfDate FROM Params))
        THEN 1 ELSE 0 END) AS Refunded
FROM Negative AS n;""",
            [Check("invoices with a negative balance", v["n_negative"], lambda r: r.value("Invoices")),
             Check("their balance", round(v["negative"], 2), lambda r: r.value("Balance")),
             Check("paid in full before the credit", v["paid_in_full"], lambda r: r.value("PaidInFull")),
             Check("credits refunded by the as-of date", v["refunded"], lambda r: r.value("Refunded"))])
    s.query("Exercise 12.2, test A5: customers stratified by open balance",
            f"Population: customers with a positive balance; expected: {v['customers']} customers",
            f"""\
{OPEN},
{CUSTOMERS}
SELECT
    CASE
        WHEN OpenBalance < 1000 THEN 'Under 1,000'
        WHEN OpenBalance < 10000 THEN '1,000-9,999'
        WHEN OpenBalance < 50000 THEN '10,000-49,999'
        ELSE '50,000 and over'
    END AS Stratum,
    COUNT(*) AS Customers, ROUND(SUM(OpenBalance), 2) AS OpenBalance,
    ROUND(SUM(OpenBalance) / (SELECT SUM(OpenBalance) FROM Customers), 3)
        AS ShareOfBalance
FROM Customers
GROUP BY Stratum
ORDER BY MIN(OpenBalance);""",
            [Check("strata", strata_names, lambda r: r.col("Stratum"))] +
            [c for name, st in strata.items() for c in (
                Check(f"{name} customers", st["n"], lambda r, name=name: r.where(Stratum=name)["Customers"]),
                Check(f"{name} balance", round(st["amount"], 2),
                      lambda r, name=name: r.where(Stratum=name)["OpenBalance"]))])
    s.query("Exercise 12.2, test A6: the customers of $50,000 or more, the key items to confirm",
            f"Population: the customers of test A5; expected: {strata['50,000 and over']['n']} key items",
            f"""\
{OPEN},
{CUSTOMERS}
SELECT c.CustomerID, cu.CustomerName,
    ROUND(c.OpenBalance, 2) AS OpenBalance,
    ROUND(c.OpenBalance / (SELECT SUM(OpenBalance) FROM Customers), 4)
        AS ShareOfBalance
FROM Customers AS c
    INNER JOIN Customer AS cu ON cu.CustomerID = c.CustomerID
WHERE c.OpenBalance >= 50000
ORDER BY c.OpenBalance DESC;""",
            [Check("key items", strata["50,000 and over"]["n"], len),
             Check("their balance", round(strata["50,000 and over"]["amount"], 2),
                   lambda r: round(r.total("OpenBalance"), 2)),
             Check("their share of the balance", round(v["key_share"], 3),
                   lambda r: round(r.total("ShareOfBalance"), 3), tolerance=0.0015)])
    s.query("Exercise 12.2, test A7: goods receipt lines not fully invoiced at the as-of date",
            "Population: receipt lines received by the as-of date; expected: receipts not yet billed",
            f"""\
{GRNI}
SELECT ReceiptNumber, ReceiptDate, SupplierID, QuantityReceived,
    QtyInvoiced, ROUND(ValueNotInvoiced, 2) AS ValueNotInvoiced
FROM NotInvoiced
ORDER BY ReceiptDate, ReceiptNumber;""",
            [Check("receipt lines", v["grni_lines"], len),
             Check("value not invoiced (the rounded lines added up)", v["grni"],
                   lambda r: round(r.total("ValueNotInvoiced"), 2), tolerance=0.10)])
    s.query("Exercise 12.2, test A8: the receipts not invoiced against account 2020",
            "Population: the lines of test A7 and the ledger; expected: no difference",
            f"""\
{GRNI},
Ledger AS (
    SELECT SUM(gl.Credit) - SUM(gl.Debit) AS Balance
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber = 2020
        AND gl.PostingDate <= (SELECT AsOfDate FROM Params)
)
SELECT ROUND(SUM(ValueNotInvoiced), 2) AS NotInvoicedValue,
    ROUND((SELECT Balance FROM Ledger), 2) AS Account2020,
    ROUND(SUM(ValueNotInvoiced) - (SELECT Balance FROM Ledger), 2)
        AS Difference
FROM NotInvoiced;""",
            [Check("value not invoiced", v["grni"], lambda r: r.value("NotInvoicedValue")),
             Check("account 2020", round(v["gl2020"], 2), lambda r: r.value("Account2020")),
             Check("difference (rounding of the clearing amounts)", round(v["rounding"], 2),
                   lambda r: r.value("Difference"))])
    s.query("Exercise 12.2, test A9: the receipts not invoiced by receipt month",
            "Population: the lines of test A7; expected: only the latest month",
            f"""\
{GRNI}
SELECT strftime('%Y-%m', ReceiptDate) AS ReceiptMonth,
    COUNT(*) AS ReceiptLines, ROUND(SUM(ValueNotInvoiced), 2) AS Value
FROM NotInvoiced
GROUP BY ReceiptMonth
ORDER BY ReceiptMonth DESC;""",
            [Check("months", [m for m, _, _ in v["months"]], lambda r: r.col("ReceiptMonth"))] +
            [c for m, val, n in v["months"] for c in (
                Check(f"{m} lines", n, lambda r, m=m: r.where(ReceiptMonth=m)["ReceiptLines"]),
                Check(f"{m} value", round(val, 2), lambda r, m=m: r.where(ReceiptMonth=m)["Value"]))])
    s.query("Exercise 12.2, test A10: the five suppliers with the most received but not invoiced",
            "Population: the lines of test A7; expected: five rows",
            f"""\
{GRNI}
SELECT SupplierID, COUNT(*) AS ReceiptLines,
    ROUND(SUM(ValueNotInvoiced), 2) AS Value
FROM NotInvoiced
GROUP BY SupplierID
ORDER BY Value DESC
LIMIT 5;""",
            [Check("suppliers", [r[0] for r in five], lambda r: r.col("SupplierID"))] +
            [c for sup, n, val in v["suppliers"] for c in (
                Check(f"supplier {sup} lines", n, lambda r, sup=sup: r.where(SupplierID=sup)["ReceiptLines"]),
                Check(f"supplier {sup} value", val, lambda r, sup=sup: r.where(SupplierID=sup)["Value"]))])
    months = {m: (val, n) for m, val, n in v["months"]}
    old = [m for m in months if m < f"{d.C}-11"]
    old_value = sum(months[m][0] for m in old)
    old_lines = sum(months[m][1] for m in old)
    past_due = sum(bk["amount"] for name, bk in buckets.items() if name != "Current")
    over60 = buckets["61-90 days"]["amount"] + buckets["Over 90 days"]["amount"]
    aging = "; ".join(f"{name} {bk['n']:,} invoices, {money(bk['amount'])}" for name, bk in buckets.items())
    s.answer("Requirement (2)", f"""\
The open invoices total {money(v['total'])}, and account 1020 shows {money(v['ledger'])} at {v['asof']}. The
difference of {money(opening)} is exactly the receivables line of the opening entry {v['entry']}, which no invoice
supports (the finding of Chapter 8). The {v['n_negative']} invoices with a negative balance ({money(v['negative'])})
are invoices credited after they were paid ({v['paid_in_full']} of them in full): the credit memo posts to account
2060, not to receivables, and the credit is refunded ({v['refunded']} of the {v['n_negative']} by the as-of date), so
they are amounts owed to customers, not negative receivables, and are left out of the aging.""")
    s.answer("Requirement (5), memo to the controller", f"""\
To: the controller. Subject: the open balances at {v['asof']}.

Receivables. {v['n']:,} invoices from {v['customers']} customers are open, {money(v['total'])} in all: {aging}. Almost
everything past due is less than 30 days late ({money(buckets['1-30 days']['amount'])} of {money(past_due)}), and the
invoices more than 60 days past due hold only {money(over60)}. Account 1020 is
{money(v['ledger'])}; the {money(opening)} difference is the opening-balance line of {v['entry']}, unsupported by any
invoice, which should be investigated and, if not supported, written off against the opening equity. The
{strata['50,000 and over']['n']} customers who owe $50,000 or more hold {100 * v['key_share']:.1f}% of the balance
and are the key items to confirm.

Receipts not invoiced. {v['grni_lines']:,} receipt lines ({money(v['grni'])}) were received but not billed by the
year-end, and they agree with account 2020 ({money(v['gl2020'])}) except for {money(v['rounding'])} of rounding.
Most are December receipts, which are normal; {old_lines} lines received in {v['old_from']} to {v['old_to']}
({money(old_value)}) are more than two months old and should be followed up with the suppliers and purchasing:
disputed or lost invoices, or receipts recorded against the wrong order.""")
    s.answer("Dispositions", f"""\
A1-A2: no exception; the aging is the basis for the allowance and the confirmations. A3 ({money(opening)}): the
unsupported opening line, reported as a finding. A4 ({v['n_negative']} invoices): credits on paid invoices, refunded
through account 2060; no exception for receivables, and the {v['n_negative'] - v['refunded']} not yet refunded are
liabilities to customers. A5-A6: the {strata['50,000 and over']['n']} key items are selected for confirmation. A7-A8:
agrees with account 2020 within {money(v['rounding'])}, rounding; no exception. A9-A10: the {old_lines} lines older than
two months are referred to purchasing for follow-up.""")


# --- Exercise 12.3 ---------------------------------------------------------------------------------------------------

FLAGGED = """\
WITH Flagged AS (
    SELECT lt.LaborTimeEntryID, lt.WorkDate, op.ActualEndDate,
        lt.RegularHours + lt.OvertimeHours AS Hours,
        CASE WHEN lt.WorkDate <= op.ActualEndDate THEN 1 ELSE 0 END
            AS WhileOpen
    FROM LaborTimeEntry AS lt
        INNER JOIN WorkOrderOperation AS op
            ON op.WorkOrderOperationID = lt.WorkOrderOperationID
    WHERE lt.LaborType = 'Direct Manufacturing'
)"""

CENTERS = """\
FROM (
    SELECT strftime('%Y', op.ActualEndDate) AS EndYear,
        wc.WorkCenterName,
        ROUND(SUM(op.PlannedLoadHours), 0) AS PlannedHours,
        ROUND(SUM(lab.Hours), 0) AS RecordedHours,
        ROUND(SUM(lab.OpenHours), 0) AS OpenHours,
        ROUND(SUM(lab.OpenHours) / SUM(op.PlannedLoadHours), 2)
            AS OpenPerPlanned
    FROM WorkOrderOperation AS op
        INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = op.WorkCenterID
        LEFT JOIN (
            SELECT lt.WorkOrderOperationID,
                SUM(lt.RegularHours + lt.OvertimeHours) AS Hours,
                SUM(CASE WHEN lt.WorkDate <= o.ActualEndDate
                    THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END)
                    AS OpenHours
            FROM LaborTimeEntry AS lt
                INNER JOIN WorkOrderOperation AS o
                    ON o.WorkOrderOperationID = lt.WorkOrderOperationID
            WHERE lt.LaborType = 'Direct Manufacturing'
            GROUP BY lt.WorkOrderOperationID
        ) AS lab ON lab.WorkOrderOperationID = op.WorkOrderOperationID
    WHERE op.ActualEndDate <= (SELECT MAX(WorkDate) FROM LaborTimeEntry)
    GROUP BY EndYear, wc.WorkCenterName
) AS centers"""


def ex3(b):
    v = context(b, "ex3")
    d = b.data
    by_year = {int(y): (h, late) for y, h, late in d.q(
        "SELECT substr(lt.WorkDate, 1, 4), SUM(lt.RegularHours + lt.OvertimeHours), SUM(CASE WHEN lt.WorkDate > "
        "op.ActualEndDate THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END) FROM LaborTimeEntry lt JOIN "
        "WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID "
        "WHERE lt.LaborType = 'Direct Manufacturing' GROUP BY 1")}
    entries = d.one("SELECT COUNT(*) FROM LaborTimeEntry lt JOIN WorkOrderOperation op ON op.WorkOrderOperationID = "
                    "lt.WorkOrderOperationID WHERE lt.LaborType = 'Direct Manufacturing'")
    late = dict(d.q("SELECT substr(lt.WorkDate, 1, 7), SUM(CASE WHEN lt.WorkDate > op.ActualEndDate THEN "
                    "lt.RegularHours + lt.OvertimeHours ELSE 0 END) / SUM(lt.RegularHours + lt.OvertimeHours) "
                    "FROM LaborTimeEntry lt JOIN WorkOrderOperation op ON op.WorkOrderOperationID = "
                    "lt.WorkOrderOperationID WHERE lt.LaborType = 'Direct Manufacturing' AND substr(lt.WorkDate, 1, 4) = ? "
                    "GROUP BY 1", str(d.F)))
    first_quarter = min(m for m, x in late.items() if x > 0.25)
    indirect = dict(d.q("SELECT substr(WorkDate, 1, 7), SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry "
                        "WHERE LaborType = 'Indirect Manufacturing' AND substr(WorkDate, 1, 4) = ? GROUP BY 1", str(d.F)))
    months = [f"{d.F}-{m:02d}" for m in range(1, MONTHS.index(v["months_to"]) + 2)]
    centers = [c + " Work Center" for c in v["centers"]]
    s = b.script("Ex 12.3.sql", "direct time recorded while each operation was open, by work center",
                 "the flag covers every direct entry with an operation; ratios by work center and year; "
                 "the first months of 2024")
    s.query("Exercise 12.3, test T1: direct labor time flagged as recorded while the operation was open",
            "Population: direct labor time with an operation; expected: recorded by the operation's end",
            f"""\
{FLAGGED}
SELECT strftime('%Y', WorkDate) AS WorkYear, COUNT(*) AS Entries,
    SUM(WhileOpen) AS EntriesWhileOpen,
    ROUND(SUM(Hours), 0) AS DirectHours,
    ROUND(SUM(CASE WHEN WhileOpen = 1 THEN Hours ELSE 0 END), 0)
        AS HoursWhileOpen,
    ROUND(SUM(CASE WHEN WhileOpen = 0 THEN Hours ELSE 0 END)
        / SUM(Hours), 3) AS ShareAfterEnd
FROM Flagged
GROUP BY WorkYear
ORDER BY WorkYear;""",
            [Check("entries flagged", entries, lambda r: r.total("Entries"))] +
            [c for y, (h, lt) in by_year.items() for c in (
                Check(f"{y} direct hours (test H9)", round(h), lambda r, y=y: r.where(WorkYear=str(y))["DirectHours"]),
                Check(f"{y} share recorded after the end (test H9)", round(lt / h, 3),
                      lambda r, y=y: r.where(WorkYear=str(y))["ShareAfterEnd"]))])
    s.query("Exercise 12.3, test T2: recorded against planned hours by work center, all hours and while open",
            f"Population: operations ended by {v['cutoff']}; expected: near 1 for every work center",
            f"""\
SELECT EndYear, WorkCenterName, PlannedHours, RecordedHours, OpenHours,
    ROUND(RecordedHours / PlannedHours, 2) AS RecordedPerPlanned,
    OpenPerPlanned
{CENTERS}
ORDER BY EndYear, WorkCenterName;""",
            [Check("work centers and years", len(centers) * len(d.years), len)] +
            [c for i, wc in enumerate(centers) for c in (
                Check(f"{v['centers'][i]} {d.C}, all hours", round(v["now_all"][i], 2),
                      lambda r, wc=wc: r.where(EndYear=str(d.C), WorkCenterName=wc)["RecordedPerPlanned"]),
                Check(f"{v['centers'][i]} {d.C}, while open", round(v["now"][i], 2),
                      lambda r, wc=wc: r.where(EndYear=str(d.C), WorkCenterName=wc)["OpenPerPlanned"]),
                Check(f"{v['centers'][i]} {d.F}, while open", round(v["then"][i], 2),
                      lambda r, wc=wc: r.where(EndYear=str(d.F), WorkCenterName=wc)["OpenPerPlanned"]))])
    rank_all = sorted(range(len(centers)), key=lambda i: -v["now_all"][i])
    rank_open = sorted(range(len(centers)), key=lambda i: -v["now"][i])
    s.query("Exercise 12.3, test T3: the work centers ranked by each ratio",
            "Population: the rows of test T2; expected: the same ranking on both ratios",
            f"""\
SELECT EndYear, WorkCenterName,
    ROUND(RecordedHours / PlannedHours, 2) AS RecordedPerPlanned,
    RANK() OVER (PARTITION BY EndYear
        ORDER BY RecordedHours / PlannedHours DESC) AS AllHoursRank,
    OpenPerPlanned,
    RANK() OVER (PARTITION BY EndYear
        ORDER BY OpenPerPlanned DESC) AS WhileOpenRank
{CENTERS}
ORDER BY EndYear, WhileOpenRank;""",
            [Check(f"{d.C} order on all hours", [centers[i] for i in rank_all],
                   lambda r: [w for _, w in sorted((a, w) for y, w, a in zip(r.col("EndYear"), r.col("WorkCenterName"),
                                                                          r.col("AllHoursRank")) if y == str(d.C))]),
             Check(f"{d.C} order while open", [centers[i] for i in rank_open],
                   lambda r: [w for y, w in zip(r.col("EndYear"), r.col("WorkCenterName")) if y == str(d.C)])])
    s.query("Exercise 12.3, test T4: work orders, completions, shipments, and hours, January to July 2024",
            "Population: fiscal 2024; expected: completions near shipments in every month",
            """\
WITH Released AS (
    SELECT strftime('%Y-%m', ReleasedDate) AS Month,
        COUNT(*) AS WorkOrdersReleased
    FROM WorkOrder
    GROUP BY Month
),
Completed AS (
    SELECT strftime('%Y-%m', pc.CompletionDate) AS Month,
        SUM(pcl.QuantityCompleted) AS UnitsCompleted
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
    GROUP BY Month
),
Shipped AS (
    SELECT strftime('%Y-%m', s.ShipmentDate) AS Month,
        SUM(sl.QuantityShipped) AS UnitsShipped
    FROM ShipmentLine AS sl
        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
        INNER JOIN Item AS i ON i.ItemID = sl.ItemID
    WHERE i.SupplyMode = 'Manufactured'
    GROUP BY Month
),
Hours AS (
    SELECT strftime('%Y-%m', WorkDate) AS Month,
        SUM(CASE LaborType WHEN 'Direct Manufacturing'
            THEN RegularHours + OvertimeHours ELSE 0 END) AS DirectHours,
        SUM(CASE LaborType WHEN 'Indirect Manufacturing'
            THEN RegularHours + OvertimeHours ELSE 0 END) AS IndirectHours
    FROM LaborTimeEntry
    GROUP BY Month
)
SELECT r.Month, r.WorkOrdersReleased,
    ROUND(c.UnitsCompleted, 0) AS UnitsCompleted,
    ROUND(sh.UnitsShipped, 0) AS UnitsShipped,
    ROUND(c.UnitsCompleted - sh.UnitsShipped, 0) AS UnitsToStock,
    ROUND(h.DirectHours, 0) AS DirectHours,
    ROUND(h.IndirectHours, 0) AS IndirectHours
FROM Released AS r
    LEFT JOIN Completed AS c ON c.Month = r.Month
    LEFT JOIN Shipped AS sh ON sh.Month = r.Month
    LEFT JOIN Hours AS h ON h.Month = r.Month
WHERE r.Month BETWEEN '2024-01' AND '2024-07'
ORDER BY r.Month;""",
            [Check("months", months, lambda r: r.col("Month")),
             Check("work orders released", v["released"], lambda r: r.col("WorkOrdersReleased")),
             Check("units completed", v["completed"], lambda r: r.col("UnitsCompleted")),
             Check("manufactured units shipped", v["shipped"], lambda r: r.col("UnitsShipped")),
             Check("indirect hours by month", [round(indirect.get(m, 0)) for m in months],
                   lambda r: [x or 0 for x in r.col("IndirectHours")])])
    s.query("Exercise 12.3, test T5: the share of direct time recorded after its operation ended, by month of 2024",
            "Population: direct labor time of 2024 with an operation; expected: a small share",
            f"""\
{FLAGGED}
SELECT strftime('%Y-%m', WorkDate) AS WorkMonth,
    ROUND(SUM(CASE WHEN WhileOpen = 0 THEN Hours ELSE 0 END)
        / SUM(Hours), 3) AS ShareAfterEnd
FROM Flagged
WHERE WorkDate BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY WorkMonth
ORDER BY WorkMonth;""",
            [Check("months", 12, len),
             Check("first month above a quarter", first_quarter,
                   lambda r: next(m for m, x in zip(r.col("WorkMonth"), r.col("ShareAfterEnd")) if x > 0.25)),
             Check(f"its share", round(v["late_first"], 3), lambda r: r.where(WorkMonth=first_quarter)["ShareAfterEnd"]),
             Check("highest share before it", round(v["late_high"], 3),
                   lambda r: max(x for m, x in zip(r.col("WorkMonth"), r.col("ShareAfterEnd")) if m < first_quarter))])
    short = v["centers"]
    planned = dict(d.q("SELECT wc.WorkCenterName, SUM(op.PlannedLoadHours) FROM WorkOrderOperation op JOIN WorkCenter wc "
                       "ON wc.WorkCenterID = op.WorkCenterID WHERE substr(op.ActualEndDate, 1, 4) = ? GROUP BY 1", str(d.C)))
    qa = next(i for i, c in enumerate(short) if c.startswith("Quality"))
    packing = next(i for i, c in enumerate(short) if c.startswith("Packing"))
    assert rank_all[0] == packing and rank_open[-1] == packing and rank_open[0] == qa, "the answer's ranking wording"
    assert min(planned, key=planned.get) == centers[qa], "Quality Assurance has the smallest planned hours"
    assert all(x < 1 for x in v["now"]), "every work center below plan while open"
    s.answer("Requirement (3)", f"""\
On all direct hours, {d.C} ranks {', '.join(short[i] for i in rank_all)} ({', '.join(f'{v["now_all"][i]:.2f}' for i
in rank_all)}): Packing and Quality Assurance record about four times their planned hours. Counting only the time
recorded while each operation was open, the order becomes {', '.join(short[i] for i in rank_open)}
({', '.join(f'{v["now"][i]:.2f}' for i in rank_open)}): every work center is below plan, and Packing falls from first
to last. The Packing excess was time charged after the operation had ended; Packing is the last operation of every
routing, so time recorded late lands there. Quality Assurance ranks first while open, but its planned hours are
the smallest of any work center, so a few hours move its ratio.
In {d.F} the in-window ratios were {', '.join(f'{short[i]} {v["then"][i]:.2f}' for i in range(len(short)))}.""")
    s.answer("Requirement (4)", f"""\
From {v['build_from']} to {v['build_to']} {d.F} the plant completed far more units than it shipped (test T4), about
{v['surplus']:,} units of stock in all: an inventory build that kept every hour on work orders, so almost no time was
recorded as indirect. When releases and completions fell to the rate of shipments in {v['after']}, the same
{v['staff']} employees kept their hours, and the days with no work order to charge became indirect time. The share of
direct time recorded after its operation ended stayed between {v['late_low']:.2f} and {v['late_high']:.2f} a month
through {v['before']} {v['before_year']} and first passed a quarter in {v['first']} {v['first_year']}
({v['late_first']:.2f}), the month surge days began in earnest.""")
    s.answer("Requirement (5), memo to the plant manager", f"""\
To: the plant manager. Subject: what the operation-level time can support.

Much of the direct time is recorded after the operation it is charged to has ended: {by_year[d.C][1] / by_year[d.C][0]:.0%}
of the direct hours of {d.C}, against {by_year[d.F][1] / by_year[d.F][0]:.0%} in {d.F}. Counted only while the
operations were open, every work center used less time than planned in {d.C}, and the apparent excess at Packing
and Quality Assurance disappears. The comparison of work centers against plan therefore cannot be relied on: it
measures where late time is parked, not how efficiently each work center works. The plant-level measure of
Chapter 11 (all manufacturing hours against the standard hours of output) does not depend on which operation the time
is charged to and is unaffected.

What should change: time should be recorded against an operation only while it is open, with the system rejecting
entries after the ActualEndDate; time with no open operation should be recorded as indirect time with a reason, and
supervisors should review late entries weekly. Until then, efficiency should be reported at the plant level only.""")
    s.answer("Dispositions", f"""\
T1 and T5: direct time recorded after the operation ended ({by_year[d.C][1] / by_year[d.C][0]:.1%} of {d.C}'s hours),
a recording deficiency reported to the plant manager. T2 and T3: no work center exceeds plan on the time recorded
while open; the Packing and Quality Assurance excess is explained by late recording, not by inefficiency. T4: the
{d.F} stock build explains the months with little indirect time; no exception.""")


# --- Exercise 12.4 ---------------------------------------------------------------------------------------------------

SURGE = """\
SurgeDays AS (
    SELECT tc.WorkDate
    FROM TimeClockEntry AS tc
        INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID
        INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
    WHERE cc.CostCenterName = 'Manufacturing'
    GROUP BY tc.WorkDate
    HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1
        AND COUNT(*) > 1
)"""


def ex4(b):
    v = context(b, "ex4")
    d = b.data
    by_reason = {(int(y), r): n for y, r, n in d.q("SELECT substr(WorkDate, 1, 4), ReasonCode, COUNT(*) "
                                                   "FROM OvertimeApproval GROUP BY 1, 2")}
    manager = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Production Manager'")
    approvers = d.one("SELECT COUNT(DISTINCT ApprovedByEmployeeID) FROM OvertimeApproval")
    s = b.script("Ex 12.4.sql", "whether the overtime approval controls the growth in overtime",
                 f"{v['n']:,} approvals by reason, approver, hours, and date; the surge days of test H8")
    s.query("Exercise 12.4, test O1: overtime approvals by year and reason code",
            f"Population: all {v['n']:,} overtime approvals; expected: reasons that change with the overtime",
            """\
SELECT strftime('%Y', WorkDate) AS WorkYear, ReasonCode,
    COUNT(*) AS Approvals,
    ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (
        PARTITION BY strftime('%Y', WorkDate)), 3) AS ShareOfYear
FROM OvertimeApproval
GROUP BY WorkYear, ReasonCode
ORDER BY WorkYear, ReasonCode;""",
            [Check("approvals", v["n"], lambda r: r.total("Approvals")),
             Check("reason codes", v["reasons"], lambda r: sorted(set(r.col("ReasonCode")))),
             Check("every share of a year between 0.2 and 0.3", True,
                   lambda r: all(0.2 <= x <= 0.3 for x in r.col("ShareOfYear")))] +
            [Check(f"{y} {rc}", n, lambda r, y=y, rc=rc: r.where(WorkYear=str(y), ReasonCode=rc)["Approvals"])
             for (y, rc), n in sorted(by_reason.items())])
    s.query("Exercise 12.4, test O2: approvals by approver, with the largest approver's share",
            "Population: all overtime approvals; expected: approval shared among supervisors",
            """\
SELECT oa.ApprovedByEmployeeID, e.JobTitle, COUNT(*) AS Approvals,
    ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (), 3) AS ShareOfApprovals
FROM OvertimeApproval AS oa
    INNER JOIN Employee AS e ON e.EmployeeID = oa.ApprovedByEmployeeID
GROUP BY oa.ApprovedByEmployeeID, e.JobTitle
ORDER BY Approvals DESC;""",
            [Check("approvers", approvers, len),
             Check("largest approver", manager, lambda r: r.cell(0, "ApprovedByEmployeeID")),
             Check("its job title", "Production Manager", lambda r: r.cell(0, "JobTitle")),
             Check("its approvals", v["manager_n"], lambda r: r.cell(0, "Approvals")),
             Check("its share", round(v["manager_share"], 3), lambda r: r.cell(0, "ShareOfApprovals"))])
    s.query("Exercise 12.4, test O3: approved against requested hours, and approval against work date",
            "Population: all overtime approvals; expected: some requests reduced, approvals in advance",
            """\
SELECT COUNT(*) AS Approvals,
    SUM(CASE WHEN ApprovedHours = RequestedHours THEN 1 ELSE 0 END)
        AS HoursAsRequested,
    SUM(CASE WHEN ApprovedHours < RequestedHours THEN 1 ELSE 0 END)
        AS HoursReduced,
    SUM(CASE WHEN ApprovedDate < WorkDate THEN 1 ELSE 0 END)
        AS ApprovedInAdvance,
    SUM(CASE WHEN ApprovedDate = WorkDate THEN 1 ELSE 0 END)
        AS ApprovedOnWorkDate,
    SUM(CASE WHEN ApprovedDate > WorkDate THEN 1 ELSE 0 END)
        AS ApprovedAfter
FROM OvertimeApproval;""",
            [Check("approvals", v["n"], lambda r: r.value("Approvals")),
             Check("hours as requested (all)", v["n"], lambda r: r.value("HoursAsRequested")),
             Check("hours reduced", 0, lambda r: r.value("HoursReduced")),
             Check("approved in advance", 0, lambda r: r.value("ApprovedInAdvance")),
             Check("approved on the work date (all)", v["n"], lambda r: r.value("ApprovedOnWorkDate"))])
    s.query("Exercise 12.4, test O4: who approved the overtime of the surge days, and when",
            "Population: manufacturing clock entries on the surge days of test H8; expected: approved in advance",
            f"""\
WITH {SURGE}
SELECT ap.JobTitle AS ApprovedBy,
    CASE
        WHEN oa.ApprovedDate IS NULL THEN 'No approval'
        WHEN oa.ApprovedDate < tc.WorkDate THEN 'Before the work date'
        WHEN oa.ApprovedDate = tc.WorkDate THEN 'On the work date'
        ELSE 'After the work date'
    END AS ApprovalTiming,
    COUNT(DISTINCT tc.WorkDate) AS SurgeDays, COUNT(*) AS ClockEntries,
    ROUND(SUM(tc.OvertimeHours), 0) AS OvertimeHours
FROM TimeClockEntry AS tc
    INNER JOIN SurgeDays AS sd ON sd.WorkDate = tc.WorkDate
    INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID
    INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
    LEFT JOIN OvertimeApproval AS oa
        ON oa.OvertimeApprovalID = tc.OvertimeApprovalID
    LEFT JOIN Employee AS ap ON ap.EmployeeID = oa.ApprovedByEmployeeID
WHERE cc.CostCenterName = 'Manufacturing'
GROUP BY ApprovedBy, ApprovalTiming;""",
            [Check("approver and timing groups", 1, len),
             Check("approved by", "Production Manager", lambda r: r.cell(0, "ApprovedBy")),
             Check("timing", "On the work date", lambda r: r.cell(0, "ApprovalTiming")),
             Check("surge days", v["days"], lambda r: r.cell(0, "SurgeDays")),
             Check("clock entries", v["entries"], lambda r: r.cell(0, "ClockEntries"))])
    s.query("Exercise 12.4, test O5: manufacturing overtime on surge days and on other days, by year",
            "Population: manufacturing clock entries; expected: growth spread over the year",
            f"""\
WITH {SURGE}
SELECT strftime('%Y', tc.WorkDate) AS WorkYear,
    ROUND(SUM(CASE WHEN sd.WorkDate IS NOT NULL
        THEN tc.OvertimeHours ELSE 0 END), 0) AS SurgeDayOvertime,
    ROUND(SUM(CASE WHEN sd.WorkDate IS NULL
        THEN tc.OvertimeHours ELSE 0 END), 0) AS OtherDayOvertime,
    ROUND(SUM(tc.OvertimeHours), 0) AS Overtime
FROM TimeClockEntry AS tc
    INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID
    INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
    LEFT JOIN SurgeDays AS sd ON sd.WorkDate = tc.WorkDate
WHERE cc.CostCenterName = 'Manufacturing'
GROUP BY WorkYear
ORDER BY WorkYear;""",
            [Check("years", [str(y) for y in d.years], lambda r: r.col("WorkYear")),
             Check("surge-day overtime", [round(x) for x in v["surge"]], lambda r: r.col("SurgeDayOvertime")),
             Check("other-day overtime", [round(x) for x in v["other"]], lambda r: r.col("OtherDayOvertime"))])
    growth_surge, growth_other = v["surge"][-1] - v["surge"][0], v["other"][-1] - v["other"][0]
    s.answer("Requirement (5)", f"""\
The approval records overtime rather than authorizing it. The {v['n_reasons']} reason codes ({', '.join(v['reasons'])})
each hold about a quarter of the approvals in every year, so the reasons say nothing about why overtime grew. The
Production Manager approved {v['manager_n']:,} of the {v['n']:,} approvals ({100 * v['manager_share']:.1f}%), every
approval grants exactly the hours requested, and every one is dated on the work date itself: no request was ever
reduced, and none was approved before the work. All {v['entries']:,} clock entries of the {v['days']} surge days were
approved by the Production Manager on the work date. Overtime on other days {v['other_trend']}
({', '.join(f'{x:,.0f}' for x in v['other'])} hours), while overtime on surge days grew from {v['surge'][0]:,.0f} to
{v['surge'][1]:,.0f} and {v['surge'][2]:,.0f} hours ({growth_surge:+,.0f}, against {growth_other:+,.0f} on other
days): all the growth sits on days the same manager scheduled and approved.

Two changes would make it a control: approval in advance of the shift, with a limit of overtime per employee and
week above which a second approver outside production (such as the controller) must agree; and
reason codes tied to a work order or a documented backlog, reviewed monthly by someone independent of the person who
schedules the surge days.""")
    s.answer("Dispositions", f"""\
O1: the reason codes carry no information, a design deficiency. O2: concentration of approval in the Production
Manager ({100 * v['manager_share']:.1f}%), a segregation-of-duties finding. O3: no approval reduces hours or precedes
the work, so the approval is a record, not an authorization; reported as a design deficiency. O4 and O5: the surge-day
overtime ({v['surge'][-1]:,.0f} hours in {d.C}) was scheduled and approved by one person on the day; referred to the
controller for review of the surge days' business need.""")


# --- Exercise 12.5 ---------------------------------------------------------------------------------------------------

def ex5(b):
    v = context(b, "ex5")
    d = b.data
    ceo = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Chief Executive Officer'")
    ceo_registers = d.one("SELECT COUNT(*) FROM PayrollRegister WHERE EmployeeID = ?", ceo)
    periods = d.one("SELECT COUNT(DISTINCT PayrollPeriodID) FROM PayrollRegister")
    own_title = v["approver_title"]
    s = b.script("Ex 12.5.sql", "the pay of employees who had left, and the approval of payroll registers and payments",
                 "registers after termination; registers by approver; self-approved registers; payments before approval")
    s.query("Exercise 12.5, test R1: registers paid after the employee's termination date",
            "Population: all payroll registers; expected: final paychecks only",
            """\
SELECT pr.PayrollRegisterID, pr.EmployeeID, e.JobTitle,
    ec.CostCenterName AS EmployeeCenter,
    rc.CostCenterName AS RegisterCenter, e.TerminationDate,
    pp.PeriodStartDate, pp.PeriodEndDate, pp.PayDate, pr.GrossPay,
    (SELECT ROUND(AVG(p2.GrossPay), 2)
     FROM PayrollRegister AS p2
        INNER JOIN PayrollPeriod AS q2
            ON q2.PayrollPeriodID = p2.PayrollPeriodID
     WHERE p2.EmployeeID = pr.EmployeeID
        AND q2.PayDate <= e.TerminationDate
        AND p2.GrossPay > 0) AS UsualGrossPay,
    (SELECT COUNT(*)
     FROM PayrollPayment AS pay
     WHERE pay.PayrollRegisterID = pr.PayrollRegisterID) AS Payments
FROM PayrollRegister AS pr
    INNER JOIN PayrollPeriod AS pp
        ON pp.PayrollPeriodID = pr.PayrollPeriodID
    INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
    INNER JOIN CostCenter AS ec ON ec.CostCenterID = e.CostCenterID
    INNER JOIN CostCenter AS rc ON rc.CostCenterID = pr.CostCenterID
WHERE e.TerminationDate IS NOT NULL
    AND pp.PayDate > e.TerminationDate
ORDER BY pp.PayDate;""",
            [Check("registers", len(v["after"]), len),
             Check("the registers", [a["id"] for a in v["after"]], lambda r: r.col("PayrollRegisterID")),
             Check("one employee", [v["emp"]], lambda r: sorted(set(r.col("EmployeeID")))),
             Check("job title", v["title"], lambda r: r.cell(0, "JobTitle")),
             Check("employee's cost center", v["center"], lambda r: r.cell(0, "EmployeeCenter")),
             Check("register's cost center", [v["charged"]], lambda r: sorted(set(r.col("RegisterCenter")))),
             Check("gross pay of each", [v["gross"]] * len(v["after"]), lambda r: r.col("GrossPay")),
             Check("usual gross pay", round(v["usual"], 2), lambda r: r.cell(0, "UsualGrossPay")),
             Check("registers without a payment", v["unpaid"],
                   lambda r: [i for i, p in zip(r.col("PayrollRegisterID"), r.col("Payments")) if p == 0]),
             Check("register whose period includes the termination", v["first"],
                   lambda r: [i for i, a, z, t in zip(r.col("PayrollRegisterID"), r.col("PeriodStartDate"),
                                                      r.col("PeriodEndDate"), r.col("TerminationDate"))
                              if a <= t <= z][0])])
    s.query("Exercise 12.5, test R2: the chief executive's registers against those periods",
            "Population: the chief executive's registers; expected: one in every pay period",
            """\
WITH AfterTermination AS (
    SELECT pr.PayrollPeriodID
    FROM PayrollRegister AS pr
        INNER JOIN PayrollPeriod AS pp
            ON pp.PayrollPeriodID = pr.PayrollPeriodID
        INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
    WHERE e.TerminationDate IS NOT NULL
        AND pp.PayDate > e.TerminationDate
)
SELECT
    (SELECT COUNT(DISTINCT PayrollPeriodID) FROM PayrollRegister)
        AS PeriodsWithRegisters,
    COUNT(*) AS ExecutiveRegisters,
    SUM(CASE WHEN pr.PayrollPeriodID IN (
        SELECT PayrollPeriodID FROM AfterTermination)
        THEN 1 ELSE 0 END) AS InThosePeriods,
    MIN(pr.GrossPay) AS LowestGross, MAX(pr.GrossPay) AS HighestGross
FROM PayrollRegister AS pr
    INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
WHERE e.JobTitle = 'Chief Executive Officer';""",
            [Check("pay periods with registers", periods, lambda r: r.value("PeriodsWithRegisters")),
             Check("chief executive's registers", ceo_registers, lambda r: r.value("ExecutiveRegisters")),
             Check("in the periods of test R1", 0, lambda r: r.value("InThosePeriods")),
             Check("one in every other period", periods - len(v["after"]), lambda r: r.value("ExecutiveRegisters")),
             Check("gross pay equal to test R1's", v["gross"], lambda r: r.value("LowestGross")),
             Check("and the same every period", v["gross"], lambda r: r.value("HighestGross"))])
    s.query("Exercise 12.5, test R3: registers approved by each approver, and on their pay date",
            "Population: all payroll registers; expected: approval shared, before the pay date",
            """\
SELECT pr.ApprovedByEmployeeID, e.JobTitle, COUNT(*) AS Registers,
    SUM(CASE WHEN pr.ApprovedDate = pp.PayDate THEN 1 ELSE 0 END)
        AS ApprovedOnPayDate
FROM PayrollRegister AS pr
    INNER JOIN PayrollPeriod AS pp
        ON pp.PayrollPeriodID = pr.PayrollPeriodID
    INNER JOIN Employee AS e ON e.EmployeeID = pr.ApprovedByEmployeeID
GROUP BY pr.ApprovedByEmployeeID, e.JobTitle
ORDER BY Registers DESC;""",
            [Check("approvers", 1, len),
             Check("the approver", v["approver"], lambda r: r.cell(0, "ApprovedByEmployeeID")),
             Check("job title", own_title, lambda r: r.cell(0, "JobTitle")),
             Check("registers", v["registers"], lambda r: r.cell(0, "Registers")),
             Check("approved on the pay date", v["registers"], lambda r: r.cell(0, "ApprovedOnPayDate"))])
    s.query("Exercise 12.5, test R4: registers approved by the employee they pay",
            "Population: all payroll registers; expected: no rows",
            """\
SELECT pr.EmployeeID, e.JobTitle, COUNT(*) AS Registers,
    ROUND(SUM(pr.NetPay), 2) AS NetPay
FROM PayrollRegister AS pr
    INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
WHERE pr.ApprovedByEmployeeID = pr.EmployeeID
GROUP BY pr.EmployeeID, e.JobTitle;""",
            [Check("employees", 1, len),
             Check("the employee", v["approver"], lambda r: r.cell(0, "EmployeeID")),
             Check("registers", v["own"], lambda r: r.cell(0, "Registers")),
             Check("net pay", round(v["own_net"], 2), lambda r: r.cell(0, "NetPay"))])
    s.query("Exercise 12.5, test R5: payments made before their register was approved",
            "Population: all payroll payments; expected: no rows",
            """\
SELECT pay.PayrollPaymentID, pay.PayrollRegisterID, e.JobTitle,
    pay.PaymentDate, pr.ApprovedDate, pr.NetPay
FROM PayrollPayment AS pay
    INNER JOIN PayrollRegister AS pr
        ON pr.PayrollRegisterID = pay.PayrollRegisterID
    INNER JOIN Employee AS e ON e.EmployeeID = pr.EmployeeID
WHERE pay.PaymentDate < pr.ApprovedDate
ORDER BY pay.PayrollPaymentID;""",
            [Check("payments", len(v["early"]), len),
             Check("the payments", v["early"], lambda r: r.col("PayrollPaymentID")),
             Check("net pay", round(v["early_net"], 2), lambda r: round(r.total("NetPay"), 2)),
             Check("paid to", ["Chief Financial Officer"], lambda r: sorted(set(r.col("JobTitle")))),
             Check("one day before approval", True,
                   lambda r: all(p < a for p, a in zip(r.col("PaymentDate"), r.col("ApprovedDate"))))])
    a = v["after"]
    s.answer("Requirements (1) and (4)", f"""\
Three registers pay the {v['title']} (employee {v['emp']}, {v['center']} cost center, terminated {v['terminated']})
after the termination: {a[0]['id']} (period from {a[0]['start']}, paid {a[0]['paid']}), {a[1]['id']} (paid
{a[1]['paid']}), and {a[2]['id']} (paid {a[2]['paid']}), {money(v['gross'])} gross each, about {v['times']} times the
employee's usual gross pay of {money(v['usual'])}, all charged to the {v['charged']} cost center. Only {v['first']},
whose period includes the termination date, could be a final paycheck, and even it pays {v['times']} times the usual
amount. The chief executive has a register in every other pay period, at the same {money(v['gross'])}, but none in
these three (test R2), so the chief executive's pay for those periods appears to have been recorded under employee
{v['emp']}; {' and '.join(str(x) for x in v['unpaid'])} have no payment record (Tutorial 12.1).

Isolated exceptions or a pattern: the post-termination and unpaid registers are isolated exceptions (three registers,
one employee) to be traced to the bank records. The approval results are a pattern: one person, the {own_title}
(employee {v['approver']}), approved all {v['registers']:,} registers, each on its pay date, including the
{v['own']} that pay the {own_title.lower()} ({money(v['own_net'])} net), and {v['n_early']} payments
({', '.join(str(x) for x in v['early'])}, {money(v['early_net'])} net) paid the chief financial officer the day before
the register was approved. A single approver who approves their own pay, on the day of payment, is a weakness in the
design of the control, not an occasional lapse.""")
    s.answer("Requirement (5), findings and recommendations", f"""\
1. Pay after termination: registers {', '.join(str(x['id']) for x in a)} pay a former {v['title']} the chief
executive's amount; trace them to the bank, confirm with the chief executive, and correct the payroll master data.
Recommendation: deactivate pay at termination and review registers of terminated employees each period.

2. Unrecorded or missing payments: {' and '.join(str(x) for x in v['unpaid'])} are approved with no payment; determine
whether cash left the bank. Recommendation: reconcile registers to payments and to the bank every pay period.

3. One approver for every register, including the approver's own {v['own']}. Recommendation: a second approver for
registers, and an independent approver (the controller) for the approver's own pay.

4. Payments before approval ({v['n_early']} payments to the chief financial officer). Recommendation: release
payments only after the register is approved, enforced by the system.

5. Add tests R1 to R5 to the query library and run them every pay period.""")
    s.answer("Dispositions", f"""\
R1 and R2 ({len(a)} registers): deficiency, pay recorded under a terminated employee; referred to the chief audit
executive for investigation. R3 and R4 ({v['registers']:,} registers, {v['own']} self-approved): design deficiency of
the payroll approval. R5 ({v['n_early']} payments): deficiency, follow up with the chief financial officer and the
bank records.""")


# --- Exercise 12.6 ---------------------------------------------------------------------------------------------------

STANDARD = "UPPER(TRIM(REPLACE(REPLACE(InvoiceNumber, '-', ''), ' ', '')))"

NUMBERS = """\
WITH Numbers AS (
    SELECT 'Sales invoice' AS Series,
        CAST(SUBSTR(InvoiceNumber, 4, 4) AS INTEGER) AS NumberYear,
        CAST(SUBSTR(InvoiceNumber, 9) AS INTEGER) AS Sequence
    FROM SalesInvoice
    UNION ALL
    SELECT 'Purchase order', CAST(SUBSTR(PONumber, 4, 4) AS INTEGER),
        CAST(SUBSTR(PONumber, 9) AS INTEGER)
    FROM PurchaseOrder
    UNION ALL
    SELECT 'Cash receipt', CAST(SUBSTR(ReceiptNumber, 4, 4) AS INTEGER),
        CAST(SUBSTR(ReceiptNumber, 9) AS INTEGER)
    FROM CashReceipt
    UNION ALL
    SELECT 'Journal entry', CAST(SUBSTR(EntryNumber, 4, 4) AS INTEGER),
        CAST(SUBSTR(EntryNumber, 9) AS INTEGER)
    FROM JournalEntry
)"""


def ex6(b):
    v = context(b, "ex6")
    d = b.data
    pairs = d.q("SELECT a.SupplierID, a.InvoiceNumber FROM PurchaseInvoice a GROUP BY 1, 2 HAVING COUNT(*) > 1")
    series = dict(zip(["Sales invoice", "Cash receipt", "Purchase order", "Journal entry"], v["series"]))
    first_digits = {"All payments": v["mad_all"], "Full payments": v["mad_full"], "Partial payments": v["mad_partial"]}
    counts = dict(d.q("SELECT 'All payments', COUNT(*) FROM DisbursementPayment WHERE PaymentDate <= ?1 UNION ALL "
                      "SELECT 'Full payments', COUNT(*) FROM DisbursementPayment p JOIN PurchaseInvoice pi "
                      "ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate <= ?1 AND ABS(p.Amount - "
                      "pi.GrandTotal) < 0.005 UNION ALL SELECT 'Partial payments', COUNT(*) FROM DisbursementPayment p "
                      "JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate <= ?1 "
                      "AND p.Amount < pi.GrandTotal - 0.005", f"{d.C}-12-31"))
    s = b.script("Ex 12.6.sql", "Chapter 8's duplicate, sequence, and first-digit tests in SQL",
                 "duplicate invoice and check numbers; near-duplicate payments; document series; first-digit MAD "
                 "equal to Tutorial 8.1")
    s.query("Exercise 12.6, test D1: supplier invoice numbers that appear more than once for a supplier",
            "Population: all supplier invoices; expected: no rows",
            """\
WITH Repeated AS (
    SELECT SupplierID, InvoiceNumber
    FROM PurchaseInvoice
    GROUP BY SupplierID, InvoiceNumber
    HAVING COUNT(*) > 1
)
SELECT pi.SupplierID, pi.InvoiceNumber, pi.PurchaseInvoiceID,
    pi.InvoiceDate, ROUND(pi.GrandTotal, 2) AS GrandTotal,
    COUNT(dp.DisbursementID) AS Payments,
    ROUND(SUM(dp.Amount), 2) AS AmountPaid
FROM PurchaseInvoice AS pi
    INNER JOIN Repeated AS r ON r.SupplierID = pi.SupplierID
        AND r.InvoiceNumber = pi.InvoiceNumber
    LEFT JOIN DisbursementPayment AS dp
        ON dp.PurchaseInvoiceID = pi.PurchaseInvoiceID
GROUP BY pi.PurchaseInvoiceID, pi.SupplierID, pi.InvoiceNumber,
    pi.InvoiceDate, pi.GrandTotal
ORDER BY pi.SupplierID, pi.InvoiceNumber, pi.PurchaseInvoiceID;""",
            [Check("invoices (both of each pair)", 2 * len(pairs), len),
             Check("pairs", len(pairs), lambda r: len(set(zip(r.col("SupplierID"), r.col("InvoiceNumber"))))),
             Check("each invoice paid once", [1], lambda r: sorted(set(r.col("Payments")))),
             Check("each pair has different amounts", True,
                   lambda r: all(len({g for s_, n, g in zip(r.col("SupplierID"), r.col("InvoiceNumber"),
                                                            r.col("GrandTotal")) if (s_, n) == p}) == 2
                                 for p in set(zip(r.col("SupplierID"), r.col("InvoiceNumber")))))])
    s.query("Exercise 12.6, test D2: the same test on invoice numbers standardized with UPPER, TRIM, and REPLACE",
            "Population: all supplier invoices; expected: no pair the exact test missed",
            f"""\
SELECT SupplierID,
    {STANDARD}
        AS StandardNumber,
    COUNT(*) AS Invoices, COUNT(DISTINCT InvoiceNumber) AS ExactNumbers
FROM PurchaseInvoice
GROUP BY SupplierID, StandardNumber
HAVING COUNT(*) > 1
ORDER BY SupplierID, StandardNumber;""",
            [Check("standardized pairs", len(pairs), len),
             Check("pairs the exact test missed (more than one exact number)", 0,
                   lambda r: sum(1 for x in r.col("ExactNumbers") if x > 1))])
    s.query("Exercise 12.6, test D3: check numbers used more than once for the same supplier",
            "Population: payments with a check number; expected: no rows",
            """\
SELECT SupplierID, CheckNumber, COUNT(*) AS Payments,
    ROUND(SUM(Amount), 2) AS Amount
FROM DisbursementPayment
WHERE CheckNumber IS NOT NULL
GROUP BY SupplierID, CheckNumber
HAVING COUNT(*) > 1
ORDER BY CheckNumber;""",
            [Check("check numbers", v["checks"], lambda r: r.col("CheckNumber")),
             Check("supplier", [v["check_supplier"]], lambda r: sorted(set(r.col("SupplierID")))),
             Check("used twice each", [2], lambda r: sorted(set(r.col("Payments"))))])
    s.query("Exercise 12.6, test D4: payments to a supplier for the same amount within 30 days",
            "Population: supplier payments dated through 2026-12-31; expected: no rows",
            """\
SELECT a.SupplierID, a.Amount, a.PaymentNumber, a.PaymentDate,
    b.PaymentNumber AS OtherPayment, b.PaymentDate AS OtherDate,
    ABS(julianday(b.PaymentDate) - julianday(a.PaymentDate))
        AS DaysApart,
    CASE WHEN a.PurchaseInvoiceID = b.PurchaseInvoiceID
        THEN 1 ELSE 0 END AS SameInvoice
FROM DisbursementPayment AS a
    INNER JOIN DisbursementPayment AS b
        ON b.SupplierID = a.SupplierID AND b.Amount = a.Amount
        AND b.DisbursementID > a.DisbursementID
WHERE a.PaymentDate <> b.PaymentDate
    AND a.PaymentDate <= '2026-12-31' AND b.PaymentDate <= '2026-12-31'
    AND ABS(julianday(b.PaymentDate) - julianday(a.PaymentDate)) <= 30
ORDER BY DaysApart, a.SupplierID;""",
            [Check("pairs within 30 days", v["within30"], len),
             Check("pairs within 14 days (the chapter's example)", v["within14"],
                   lambda r: sum(1 for x in r.col("DaysApart") if x <= 14)),
             Check("pairs paying the same invoice", 0, lambda r: sum(r.col("SameInvoice")))])
    s.query("Exercise 12.6, test D5: all same-supplier, same-amount pairs, by distance in days",
            "Population: supplier payments dated through 2026-12-31; expected: no pair on one invoice",
            """\
SELECT COUNT(*) AS Pairs,
    SUM(CASE WHEN ABS(julianday(b.PaymentDate)
        - julianday(a.PaymentDate)) <= 30 THEN 1 ELSE 0 END)
        AS Within30Days,
    SUM(CASE WHEN a.PurchaseInvoiceID = b.PurchaseInvoiceID
        THEN 1 ELSE 0 END) AS SameInvoice
FROM DisbursementPayment AS a
    INNER JOIN DisbursementPayment AS b
        ON b.SupplierID = a.SupplierID AND b.Amount = a.Amount
        AND b.DisbursementID > a.DisbursementID
WHERE a.PaymentDate <> b.PaymentDate
    AND a.PaymentDate <= '2026-12-31' AND b.PaymentDate <= '2026-12-31';""",
            [Check("pairs on different dates", v["pairs"], lambda r: r.value("Pairs")),
             Check("within 30 days", v["within30"], lambda r: r.value("Within30Days")),
             Check("paying the same invoice", 0, lambda r: r.value("SameInvoice"))])
    s.query("Exercise 12.6, test S1: the first and last number of each document series and year",
            "Population: four document series; expected: numbers without gaps",
            f"""\
{NUMBERS}
SELECT Series, NumberYear, MIN(Sequence) AS FirstNumber,
    MAX(Sequence) AS LastNumber, COUNT(*) AS Documents
FROM Numbers
GROUP BY Series, NumberYear
ORDER BY Series, NumberYear;""",
            [Check("series and years", 4 * len(d.years), len)] +
            [c for name, rows in series.items() for c in (
                Check(f"{name} first numbers", [lo for lo, _ in rows],
                      lambda r, name=name: [x for sr, x in zip(r.col("Series"), r.col("FirstNumber")) if sr == name]),
                Check(f"{name} last numbers", [hi for _, hi in rows],
                      lambda r, name=name: [x for sr, x in zip(r.col("Series"), r.col("LastNumber")) if sr == name]))])
    s.query("Exercise 12.6, test S2: steps greater than one between consecutive numbers",
            "Population: four document series; expected: no gaps",
            f"""\
{NUMBERS},
Steps AS (
    SELECT Series, Sequence - LAG(Sequence) OVER (
        PARTITION BY Series ORDER BY Sequence) AS Step
    FROM Numbers
    WHERE Series <> 'Journal entry'
    UNION ALL
    SELECT Series, Sequence - LAG(Sequence) OVER (
        PARTITION BY Series, NumberYear ORDER BY Sequence)
    FROM Numbers
    WHERE Series = 'Journal entry'
)
SELECT Series, COUNT(Step) AS StepsTested, MAX(Step) AS LargestStep,
    SUM(CASE WHEN Step > 1 THEN 1 ELSE 0 END) AS Gaps
FROM Steps
GROUP BY Series
ORDER BY Series;""",
            [Check("series", 4, len),
             Check("gaps", [0, 0, 0, 0], lambda r: r.col("Gaps")),
             Check("largest step", [1, 1, 1, 1], lambda r: r.col("LargestStep")),
             Check("steps tested", d.one("SELECT (SELECT COUNT(*) FROM SalesInvoice) + (SELECT COUNT(*) FROM PurchaseOrder) "
                                         "+ (SELECT COUNT(*) FROM CashReceipt) + (SELECT COUNT(*) FROM JournalEntry)")
                   - 3 - len(d.years), lambda r: r.total("StepsTested"))])
    s.query("Exercise 12.6, test B1: first-digit mean absolute deviation of the supplier payments",
            "Population: supplier payments dated through 2026-12-31; expected: close conformity",
            """\
WITH Payments AS (
    SELECT dp.Amount, pi.GrandTotal,
        CAST(SUBSTR(printf('%e', dp.Amount), 1, 1) AS INTEGER) AS Digit
    FROM DisbursementPayment AS dp
        INNER JOIN PurchaseInvoice AS pi
            ON pi.PurchaseInvoiceID = dp.PurchaseInvoiceID
    WHERE dp.PaymentDate <= '2026-12-31'
),
Groups AS (
    SELECT 'All payments' AS PaymentGroup, Digit
    FROM Payments
    UNION ALL
    SELECT 'Full payments', Digit
    FROM Payments
    WHERE Amount = GrandTotal
    UNION ALL
    SELECT 'Partial payments', Digit
    FROM Payments
    WHERE Amount < GrandTotal
),
Observed AS (
    SELECT PaymentGroup, Digit, COUNT(*) AS Payments,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY PaymentGroup)
            AS Actual
    FROM Groups
    GROUP BY PaymentGroup, Digit
)
SELECT PaymentGroup, SUM(Payments) AS Payments, COUNT(*) AS Digits,
    ROUND(AVG(ABS(Actual - LOG10(1 + 1.0 / Digit))), 5) AS MAD
FROM Observed
GROUP BY PaymentGroup
ORDER BY PaymentGroup;""",
            [Check("groups", list(first_digits), lambda r: r.col("PaymentGroup")),
             Check("all nine digits in every group", [9, 9, 9], lambda r: r.col("Digits"))] +
            [c for g, mad in first_digits.items() for c in (
                Check(f"{g} payments", counts[g], lambda r, g=g: r.where(PaymentGroup=g)["Payments"]),
                Check(f"{g} MAD (Tutorial 8.1)", round(mad, 5), lambda r, g=g: r.where(PaymentGroup=g)["MAD"],
                      tolerance=0.000005))])
    js = series["Journal entry"]
    partial_min = d.one("SELECT MIN(pi.GrandTotal) FROM DisbursementPayment p JOIN PurchaseInvoice pi ON "
                        "pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate <= ? AND p.Amount < pi.GrandTotal",
                        f"{d.C}-12-31")
    partial_min = int(partial_min // 1000 * 1000)
    s.answer("Requirement (6), results and dispositions", f"""\
D1, duplicate supplier invoice numbers: {v['n_dupes']} numbers appear twice for the same supplier; each pair has
different amounts and each invoice was paid once (Exercise 2.6). Disposition: obtain both invoices of each pair from
the suppliers to confirm they are distinct bills; no duplicate payment found.

D2, standardized numbers: the same {v['n_dupes']} pairs and no others; the numbers are entered consistently.
Disposition: no exception.

D3, repeated check numbers: {v['n_checks'].lower()} check numbers, {', '.join(v['checks'])}, each used twice for
supplier {v['check_supplier']} (the AnomalyLog lists {v['n_logged']} duplicate references, but only
{v['n_with_check']} carry check numbers). Disposition: trace both payments of each check to the bank statement.

D4 and D5, near-duplicate payments: {v['pairs']} pairs share supplier and amount on different dates, {v['within30']}
within 30 days ({v['within14']} within 14, the chapter's example), and none pays the same invoice. Disposition:
recurring purchases, no exception.

S1 and S2, document series: no gaps. Sales invoices, purchase orders, and cash receipts continue across years, and
journal entries restart each year ({', '.join(f'1-{hi:,}' for _, hi in js)}). Disposition: no exception.

B1, first digits: MAD {v['mad_all']:.5f} for all payments, {v['mad_full']:.5f} for full payments, and
{v['mad_partial']:.5f} for partial payments, the values of Tutorial 8.1. Disposition: the partial payments'
nonconformity is explained by how invoices are paid in parts (Chapter 8): only invoices of {money(partial_min)} or
more are paid in installments, so the partial amounts cluster; no further work.

Why the near-duplicate test needs a self-join: GROUP BY finds rows with identical values, but a near duplicate is a
pair of different payments whose dates fall within a range of each other, so each payment must be compared with the
other payments of the same supplier, which takes the table joined to itself. A LAG partitioned by year on a series that
continues across years would also miss a gap between the last number of one year and the first of the next, which is
why the continuing series are ordered without a partition.

What SQL gains over a workbook: the tests run on the whole population in the database, every quarter, without copying
data into a workbook or refreshing formulas; each test is a saved, readable definition that a reviewer can rerun and
get the same result; and printf writes every positive amount in scientific notation (688.42 as 6.884200e+02, the
smallest payment {v['smallest']} as {v['smallest_e']}), so the first character is always the first significant digit,
without the text tricks the workbook needed.""")


EXERCISES = [("12.1", ex1), ("12.2", ex2), ("12.3", ex3), ("12.4", ex4), ("12.5", ex5), ("12.6", ex6)]
