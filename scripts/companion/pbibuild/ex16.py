"""Chapter 16 Exercises - Solutions.pbip: the exercises of Chapter 16, built on a copy of Audit Monitoring at the end of
Tutorial 16.3 (the reader's Save as copy).

Each function builds one exercise as a strong student would: the queries under the names the exercise gives (with the
Power Query Editor's step names: Grouped Rows, Merged Queries, Appended Query), its page named after it, its measures
in a display folder of the Key Measures table named after it, and a "Model answer" text box for the written
requirements, built from computed values. The checks compare the model with the values of the exercise's instructor
note (facts/notes/ch16.py, which rebuilds the register and the tests in SQL) and with read-only SQL.
"""

from __future__ import annotations

import math

from pbibuild.audit_monitoring import REGISTER, Append, Build, entered, md_table, CHAPTER
from pbibuild.model import MEASURES_TABLE, Column, Measure, Query, Table, query_table
from pbibuild.pbir import Page, Visual, col, meas, textbox
from pbibuild.reports import card, claim, keep, money
from xlbuild import pq

from notes import ch16  # noqa: E402  (facts/ is on sys.path through pbibuild.audit_monitoring)

KM = MEASURES_TABLE
M = lambda n: meas(KM, n)                 # noqa: E731


def measure(b: Build, folder: str, name: str, dax: str, fmt: str | None = None) -> None:
    b.model.tables[KM].measures.append(Measure(name, dax, fmt, display_folder=folder))


def answer(name: str, x, y, w, h, lines: list, size: int = 10) -> Visual:
    return textbox(name, x, y, w, h, [("Model answer", True)] + lines, size=size)


def pct(x: float, places: int = 1) -> str:
    return f"{100 * x:.{places}f}%"


def mdate(day: str) -> str:
    y, m, d = day.split("-")
    return f"#date({int(y)}, {int(m)}, {int(d)})"


def group(q: Query, keys: list[str], aggs: list[tuple[str, str, str]]) -> Query:
    """Transform > Group By (Advanced): the key columns and (new column, each expression, M type) aggregations."""
    spec = ", ".join("{" + f"{pq.m_string(n)}, each {e}, {t}" + "}" for n, e, t in aggs)
    out = {k: q.columns[k] for k in keys} | {n: ("Int64.Type" if t == "Int64.Type" else "type number" if "number" in t
                                                  else "type date" if "date" in t else "type any") for n, _, t in aggs}
    return q.raw("Grouped Rows", f"Table.Group({pq.PREV}, {{{', '.join(pq.m_string(k) for k in keys)}}}, {{{spec}}})", out)


class AppendAll(Append):
    """Append Queries as New over queries whose columns differ: the columns of all of them, in order of appearance
    (Table.Combine fills the missing ones with null)."""

    def __init__(self, name: str, parts: list[Query]):
        Query.__init__(self, name)
        self.parts = parts
        names = [c for p in parts for c in p.columns]
        self.columns = {}
        for c in dict.fromkeys(names):
            kinds = {p.columns[c] for p in parts if c in p.columns}
            self.columns[c] = kinds.pop() if len(kinds) == 1 else "type any"
        self.source = ("append",)


# --- Exercise 16.1 ---------------------------------------------------------------------------------------------------

def receivables(b: Build, name: str, keep_: str, apps: Query, credits: Query) -> Query:
    """ARInvoices as the exercise builds it, up to the open balance and its filter (ARCreditBalances is a Duplicate
    of it with the filter reversed)."""
    end = mdate(ch16.asof(b.d))
    return (Query.navigator(name, b.xlsx, 16, "SalesInvoice")
            .select(["SalesInvoiceID", "InvoiceNumber", "CustomerID", "InvoiceDate", "DueDate", "GrandTotal"])
            .types({"InvoiceDate": "type date", "DueDate": "type date"})
            .merge(apps, "SalesInvoiceID", "SalesInvoiceID", ["Applied"])
            .merge(credits, "SalesInvoiceID", "OriginalSalesInvoiceID", ["Credited"])
            .custom("OpenBalance", "Number.Round([GrandTotal] - (if [Applied] = null then 0 else [Applied]) "
                                   "- (if [Credited] = null then 0 else [Credited]), 2)", "type number")
            .filter(f"[InvoiceDate] <= {end} and [OpenBalance] {keep_} 0"))


def ex1(b: Build) -> None:
    ctx = ch16.ex1(b.d, claim)
    m, x, folder, end = b.model, b.xlsx, "Ex 16.1", ch16.asof(b.d)
    # (1) and (2) the applications and credits through the as-of date, grouped by invoice (Enable load cleared)
    apps = group(Query.navigator("ARApplications", x, 20, "CashReceiptApplication")
                 .select(["SalesInvoiceID", "ApplicationDate", "AppliedAmount"]).types({"ApplicationDate": "type date"})
                 .filter(f"[ApplicationDate] <= {mdate(end)}"),
                 ["SalesInvoiceID"], [("Applied", "List.Sum([AppliedAmount])", "type nullable number")])
    credits = group(Query.navigator("ARCredits", x, 23, "CreditMemo")
                    .select(["OriginalSalesInvoiceID", "CreditMemoDate", "GrandTotal"]).types({"CreditMemoDate": "type date"})
                    .filter(f"[CreditMemoDate] <= {mdate(end)}"),
                    ["OriginalSalesInvoiceID"], [("Credited", "List.Sum([GrandTotal])", "type nullable number")])
    m.stage(apps)
    m.stage(credits)
    ar = receivables(b, "ARInvoices", ">", apps, credits)
    # (3) the aging at the as-of date, in Chapter 8's buckets
    ar.custom("DaysPastDue", f"Duration.Days({mdate(end)} - [DueDate])", "Int64.Type")
    ar.custom("Bucket", 'if [DaysPastDue] <= 0 then "Current" else if [DaysPastDue] <= 30 then "1-30 days" '
                        'else if [DaysPastDue] <= 60 then "31-60 days" else if [DaysPastDue] <= 90 then "61-90 days" '
                        'else "Over 90 days"', "type text")
    ar.custom("BucketOrder", 'if [DaysPastDue] <= 0 then 1 else if [DaysPastDue] <= 30 then 2 else if [DaysPastDue] <= 60 '
                             'then 3 else if [DaysPastDue] <= 90 then 4 else 5', "Int64.Type")
    fmts = {"GrandTotal": "#,0.00", "OpenBalance": "#,0.00", "Applied": "#,0.00", "Credited": "#,0.00"}
    keys = {"SalesInvoiceID": "none", "CustomerID": "none", "DaysPastDue": "none", "BucketOrder": "none"}
    t_ar = m.add(query_table(ar, formats=fmts, summarize=keys, sort_by={"Bucket": "BucketOrder"},
                             hidden={"SalesInvoiceID", "BucketOrder"}))
    # (5) the invoices the open balances leave out: a Duplicate of ARInvoices with the filter reversed
    neg = receivables(b, "ARCreditBalances", "<", apps, credits)
    m.add(query_table(neg, formats=fmts, summarize=keys, hidden={"SalesInvoiceID"}))
    # (4) the ledger's receivables account, through the as-of date
    ledger = (Query.navigator("ARLedger", x, 3, "GLEntry")
              .select(["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType"])
              .types({"PostingDate": "type date"})
              .merge(b.q["Account"], "AccountID", "AccountID", ["AccountNumber"])
              .filter(f"[AccountNumber] = 1020 and [PostingDate] <= {mdate(end)}"))
    m.add(query_table(ledger, formats={"Debit": "#,0.00", "Credit": "#,0.00"},
                      summarize={"GLEntryID": "none", "AccountID": "none", "AccountNumber": "none"},
                      hidden={"GLEntryID", "AccountID"}))
    for n, dax, fmt in [("Open Balance", "SUM ( ARInvoices[OpenBalance] )", "#,0.00"),
                        ("Open Invoices", "COUNTROWS ( ARInvoices )", "#,0"),
                        ("Ledger Receivables", "SUM ( ARLedger[Debit] ) - SUM ( ARLedger[Credit] )", "#,0.00"),
                        ("Unreconciled Difference", "[Ledger Receivables] - [Open Balance]", "#,0.00"),
                        ("Credit Balances", "SUM ( ARCreditBalances[OpenBalance] )", "#,0.00"),
                        ("Credit Balance Invoices", "COUNTROWS ( ARCreditBalances )", "#,0")]:
        measure(b, folder, n, dax, fmt)
    page = b.report.add(Page("ex161", "Ex 16.1"))
    page.add(Visual("aging", "tableEx", 20, 20, 560, 230, {"Values": [
        col("ARInvoices", "Bucket"), M("Open Balance"), M("Open Invoices")]}, title=f"Receivables aged at {end}",
        sort=[(col("ARInvoices", "BucketOrder"), "Ascending")]))
    page.add(card("reconCards", 600, 20, 660, 110, [M("Open Balance"), M("Ledger Receivables"), M("Unreconciled Difference")],
                  units_none=True))
    page.add(card("creditCards", 600, 140, 660, 110, [M("Credit Balances"), M("Credit Balance Invoices")], units_none=True))
    page.add(Visual("ledgerBySource", "tableEx", 20, 270, 560, 200, {"Values": [
        col("ARLedger", "SourceDocumentType"), M("Ledger Receivables")]}, title="Account 1020 by source document"))
    page.add(answer("ex161Answer", 600, 270, 660, 440, [
        f"(3) {ctx['n']:,} invoices with an open balance at {end}, {money(ctx['total'])}, owed by {ctx['customers']} "
        "customers: " + "; ".join(f"{bk['name']} {money(bk['amount'])}" for bk in ctx["b"]) +
        f". The {ctx['oldest']['n']} balances over 90 days are residuals of invoices paid almost in full (the largest "
        f"{money(ctx['oldest']['largest'])}).",
        f"(4) Account 1020 at {end}: {money(ctx['ledger'])}. The difference, {money(ctx['difference'])}, is the "
        f"receivables line of the opening entry {ctx['entry']}, which no invoice supports: Chapter 8's finding, now "
        "followed on every refresh.",
        f"(5) {ctx['n_negative']} invoices have credits and applications above their total, {money(ctx['negative'])}: "
        f"credit memos on invoices already paid, which Chapter 8 found credited to 2060 (customer credit balances) and "
        f"refunded ({ctx['refunded']} of them). They belong with the refunds, not in the aging."]))
    page.expect = ["Bucket", "Current", "Over 90 days", money(ctx["total"]), money(ctx["ledger"]),
                   money(ctx["difference"]), "Model answer"]

    t = "Exercise 16.1"
    b.check(t, "invoices with an open balance", ctx["n"], "[Open Invoices]", 0)
    b.check(t, "open balance", round(ctx["total"], 2), "[Open Balance]", 0.01)
    b.check(t, "customers with an open balance", ctx["customers"], "DISTINCTCOUNT ( ARInvoices[CustomerID] )", 0)
    for bk, label in zip(ctx["b"], ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]):
        b.check(t, f"bucket {label}", round(bk["amount"], 2), f"CALCULATE ( [Open Balance], ARInvoices[Bucket] = \"{label}\" )",
                0.01)
    b.check(t, "the largest balance over 90 days", round(ctx["oldest"]["largest"], 2),
            "CALCULATE ( MAX ( ARInvoices[OpenBalance] ), ARInvoices[Bucket] = \"Over 90 days\" )", 0.005)
    b.check(t, "account 1020 at the as-of date", round(ctx["ledger"], 2), "[Ledger Receivables]", 0.01)
    b.check(t, "the unreconciled difference", round(ctx["difference"], 2), "[Unreconciled Difference]", 0.01)
    b.check(t, f"the difference is {ctx['entry']}'s receivables line", round(ctx["difference"], 2),
            f"CALCULATE ( [Ledger Receivables], ARLedger[VoucherNumber] = \"{ctx['entry']}\" )", 0.01)
    b.check(t, "invoices whose credits and applications exceed their total", ctx["n_negative"], "[Credit Balance Invoices]", 0)
    b.check(t, "their total", round(ctx["negative"], 2), "[Credit Balances]", 0.01)


# --- Exercise 16.2 ---------------------------------------------------------------------------------------------------

def ex2(b: Build) -> None:
    ctx = ch16.ex2(b.d, claim)
    m, x, folder = b.model, b.xlsx, "Ex 16.2"
    # (1) the shipments' delivery dates on the shipment lines
    ships = Query.navigator("CutoffShipments", x, 14, "Shipment").select(["ShipmentID", "DeliveryDate"]).types(
        {"DeliveryDate": "type date"})
    lines = (Query.navigator("CutoffShipmentLines", x, 15, "ShipmentLine")
             .select(["ShipmentLineID", "ShipmentID", "ExtendedStandardCost"])
             .merge(ships, "ShipmentID", "ShipmentID", ["DeliveryDate"]))
    # (2) the invoice lines with their invoice's number, date, and subtotal, and their delivery date
    invoices = (Query.navigator("CutoffInvoices", x, 16, "SalesInvoice")
                .select(["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "SubTotal"]).types({"InvoiceDate": "type date"}))
    inv_lines = (Query.navigator("CutoffInvoiceLines", x, 17, "SalesInvoiceLine").select(["SalesInvoiceID", "ShipmentLineID"])
                 .merge(invoices, "SalesInvoiceID", "SalesInvoiceID", ["InvoiceNumber", "InvoiceDate", "SubTotal"])
                 .merge(lines, "ShipmentLineID", "ShipmentLineID", ["DeliveryDate"]))
    for q in (ships, lines, invoices):
        m.stage(q)
    m.add(query_table(inv_lines, formats={"SubTotal": "#,0.00"},
                      summarize={"SalesInvoiceID": "none", "ShipmentLineID": "none", "SubTotal": "none"},
                      hidden={"SalesInvoiceID", "ShipmentLineID"}))
    # (3) the two exception queries, with the register's columns
    si = group(Query.reference("SI DeliveredPriorYear", inv_lines), ["InvoiceNumber", "InvoiceDate", "SubTotal"],
               [("LastDelivery", "List.Max([DeliveryDate])", "type nullable date")])
    si.filter("[LastDelivery] <> null and Date.Year([LastDelivery]) < Date.Year([InvoiceDate])")
    si.custom("TestID", '"SI DeliveredPriorYear"', "type text").custom("EmployeeID", "null", "Int64.Type")
    si.rename({"InvoiceNumber": "DocumentNumber", "InvoiceDate": "EventDate", "SubTotal": "Amount"}).select(REGISTER)
    sl = Query.reference("SL NotInvoiced", lines)
    sl.raw("Merged Queries", f"Table.NestedJoin({pq.PREV}, {{\"ShipmentLineID\"}}, CutoffInvoiceLines, "
                             "{\"ShipmentLineID\"}, \"CutoffInvoiceLines\", JoinKind.LeftAnti)")
    sl.raw("Removed Columns", f"Table.RemoveColumns({pq.PREV}, {{\"CutoffInvoiceLines\"}})")
    sl.custom("TestID", '"SL NotInvoiced"', "type text")
    sl.custom("DocumentNumber", '"Shipment line " & Text.From([ShipmentLineID])', "type text")
    sl.custom("EmployeeID", "null", "Int64.Type")
    sl.rename({"DeliveryDate": "EventDate", "ExtendedStandardCost": "Amount"}).select(REGISTER)
    m.stage(si)
    m.stage(sl)
    # (4) a copy of the register with the two tests appended, and a copy of the Tests table with two rows more
    reg = AppendAll("Exceptions 16.2", [m.tables["Exceptions"].query, si, sl]).types({"EventDate": "type date"})
    m.add(query_table(reg, formats={"Amount": "#,0.00"}, summarize={"EmployeeID": "none", "Amount": "sum"}))
    tests = md_table(CHAPTER / "chapter.qmd", "tbl-16-01") + [
        ["SI DeliveredPriorYear", "Invoice for goods all delivered in an earlier year", "Revenue cutoff", "Chapter 12"],
        ["SL NotInvoiced", "Shipment line never invoiced", "Revenue cutoff", "Chapter 12"]]
    m.add(entered("Tests 16.2", ["TestID", "Test", "Process", "Source"], tests))
    m.query_order.append("Tests 16.2")
    m.relate("Exceptions 16.2.TestID", "Tests 16.2.TestID")
    m.relate("Exceptions 16.2.EventDate", "Date.Date")
    measure(b, folder, "Exceptions 16.2", "COUNTROWS ( 'Exceptions 16.2' )", "#,0")
    measure(b, folder, "Exception Amount 16.2", "SUM ( 'Exceptions 16.2'[Amount] )", "#,0.00")
    new = ["SI DeliveredPriorYear", "SL NotInvoiced"]
    page = b.report.add(Page("ex162", "Ex 16.2"))
    tid = col("Tests 16.2", "TestID")
    page.add(Visual("cutoffByMonth", "pivotTable", 20, 20, 600, 260, {
        "Rows": [col("Date", "YearMonth")], "Columns": [tid], "Values": [M("Exceptions 16.2")]},
        title="The two cutoff tests by month", filters=[keep("cbmTests", tid, new)]))
    page.add(Visual("cutoffDocs", "tableEx", 20, 300, 600, 410, {"Values": [
        tid, col("Exceptions 16.2", "DocumentNumber"), col("Exceptions 16.2", "EventDate"), M("Exception Amount 16.2")]},
        title="The documents", filters=[keep("cdTests", tid, new)]))
    odd = ctx["odd"]
    page.add(answer("ex162Answer", 640, 20, 620, 690, [
        f"(3) SI DeliveredPriorYear finds {ctx['n_prior']} invoices: " + ", ".join(
            f"{g['n']} dated in January {g['year']} for December {g['year'] - 1} deliveries" for g in ctx["g"]) +
        f" (subtotal {money(ctx['sub'])} together). SL NotInvoiced finds {ctx['unbilled']} shipment lines, all "
        f"December {b.d.C} deliveries (standard cost {money(ctx['cost'])}).",
        f"(5) The extra invoice is {odd['number']}: dated in {odd['dated']} and shipped on {odd['shipped']}, but posted on "
        f"{odd['posted']} (its 1020 posting is in ARLedger). By posting date it joins {odd['joins']}; by its own date "
        "it falls in the year of its delivery, so this test cannot see it. Chapter 6 found it: a revenue cutoff error, "
        "an invoice posted in the year after the goods shipped.",
        f"{ctx['n_before']} invoices are dated in a year before their delivery ({', '.join(ctx['before'])}), the other "
        "direction, which the exercise does not ask for."], size=10))
    page.expect = ["SI DeliveredPriorYear", "SL NotInvoiced", "DocumentNumber", money(ctx["sub"] + ctx["cost"]),
                   "Model answer"]

    t = "Exercise 16.2"
    f_si, f_sl = "'Exceptions 16.2'[TestID] = \"SI DeliveredPriorYear\"", "'Exceptions 16.2'[TestID] = \"SL NotInvoiced\""
    b.check(t, "SI DeliveredPriorYear exceptions", ctx["n_prior"], f"CALCULATE ( [Exceptions 16.2], {f_si} )", 0)
    for g in ctx["g"]:
        b.check(t, f"SI DeliveredPriorYear in {g['year']}", g["n"],
                f"CALCULATE ( [Exceptions 16.2], {f_si}, 'Date'[Year] = {g['year']}, 'Date'[MonthNumber] = 1 )", 0)
    b.check(t, "their subtotal", round(ctx["sub"], 2), f"CALCULATE ( [Exception Amount 16.2], {f_si} )", 0.01)
    b.check(t, "SL NotInvoiced exceptions", ctx["unbilled"], f"CALCULATE ( [Exceptions 16.2], {f_sl} )", 0)
    b.check(t, f"SL NotInvoiced in December {b.d.C}", ctx["unbilled"],
            f"CALCULATE ( [Exceptions 16.2], {f_sl}, 'Date'[YearMonth] = \"{b.d.C}-12\" )", 0)
    b.check(t, "their standard cost", round(ctx["cost"], 2), f"CALCULATE ( [Exception Amount 16.2], {f_sl} )", 0.01)
    b.check(t, "Exceptions 16.2 rows (the register and the two tests)", len(ch16.register(b.d)) + ctx["n_prior"] + ctx["unbilled"],
            "[Exceptions 16.2]", 0)
    b.check(t, "Tests 16.2 rows", len(tests), "COUNTROWS ( 'Tests 16.2' )", 0)
    b.check(t, "exceptions without a test", 0,
            "COUNTROWS ( FILTER ( 'Exceptions 16.2', ISBLANK ( RELATED ( 'Tests 16.2'[Process] ) ) ) )", 0)
    v = f"ARLedger[VoucherNumber] = \"{odd['number']}\""
    b.check(t, f"{odd['number']} posted (ARLedger)", odd["posted"],
            f"FORMAT ( CALCULATE ( MIN ( ARLedger[PostingDate] ), {v} ), \"yyyy-mm-dd\" )")
    w = f"CutoffInvoiceLines[InvoiceNumber] = \"{odd['number']}\""
    b.check(t, f"{odd['number']} invoice year", int(odd["shipped"][:4]),
            f"CALCULATE ( YEAR ( MIN ( CutoffInvoiceLines[InvoiceDate] ) ), {w} )", 0)
    b.check(t, f"{odd['number']} delivered in the year of its invoice", int(odd["shipped"][:4]),
            f"CALCULATE ( YEAR ( MAX ( CutoffInvoiceLines[DeliveryDate] ) ), {w} )", 0)


# --- Exercise 16.3 ---------------------------------------------------------------------------------------------------

def ex3(b: Build) -> None:
    ctx = ch16.ex3(b.d, claim)
    m, folder, y = b.model, "Ex 16.3", b.d.C
    manufacturing = b.d.one("SELECT CostCenterID FROM CostCenter WHERE CostCenterName = 'Manufacturing'")
    # (1) and (2) the manufacturing clock entries and their total hours
    clock = (Query.navigator("ClockEntries", b.xlsx, 66, "TimeClockEntry")
             .select(["EmployeeID", "WorkDate", "RegularHours", "OvertimeHours"]).types({"WorkDate": "type date"})
             .merge(b.q["Employee"], "EmployeeID", "EmployeeID", ["CostCenterID"])
             .filter(f"([CostCenterID] = {manufacturing})")
             .custom("TotalHours", "[RegularHours] + [OvertimeHours]", "type number"))
    m.add(query_table(clock, summarize={"EmployeeID": "none", "CostCenterID": "none"}, hidden={"EmployeeID", "CostCenterID"}))
    m.relate("ClockEntries.WorkDate", "Date.Date")
    # (2) and (3) one row per day; the surge days kept. Count Distinct Rows would count distinct rows of the whole
    # group, so the distinct values of TotalHours are counted with List.Distinct.
    surge = group(Query.reference("SurgeDays", clock), ["WorkDate"], [
        ("Employees", "Table.RowCount(_)", "Int64.Type"),
        ("HoursValues", "List.Count(List.Distinct([TotalHours]))", "Int64.Type"),
        ("OvertimeHours", "List.Sum([OvertimeHours])", "type nullable number")])
    surge.filter("[Employees] > 1 and [HoursValues] = 1")
    m.add(query_table(surge, summarize={"HoursValues": "none"}))
    m.relate("SurgeDays.WorkDate", "Date.Date")
    for n, dax, fmt in [("Surge Days", "COUNTROWS ( SurgeDays )", "#,0"),
                        ("Surge Overtime Hours", "SUM ( SurgeDays[OvertimeHours] )", "#,0"),
                        ("Plant Overtime Hours", "SUM ( ClockEntries[OvertimeHours] )", "#,0"),
                        ("Surge Share of Overtime", "DIVIDE ( [Surge Overtime Hours], [Plant Overtime Hours] )", "0.0%")]:
        measure(b, folder, n, dax, fmt)
    years = b.d.years
    page = b.report.add(Page("ex163", "Ex 16.3"))
    ym = col("Date", "YearMonth")
    page.add(Visual("surgeDaysByMonth", "clusteredColumnChart", 20, 20, 820, 220, {"Category": [ym], "Y": [M("Surge Days")]},
                    title="Surge days by month", filters=[keep("sdmYears", col("Date", "Year"), years)]))
    page.add(Visual("surgeOvertime", "lineClusteredColumnComboChart", 20, 250, 820, 260, {
        "Category": [ym], "Y": [M("Surge Overtime Hours")], "Y2": [M("Surge Share of Overtime")]},
        title="Surge-day overtime hours by month, and their share of the plant's overtime",
        filters=[keep("somYears", col("Date", "Year"), years)]))
    page.add(Visual("surgeByYear", "tableEx", 20, 530, 820, 180, {"Values": [
        col("Date", "Year"), M("Surge Days"), M("Surge Overtime Hours"), M("Plant Overtime Hours"),
        M("Surge Share of Overtime")]}, title="By year", filters=[keep("sbyYears", col("Date", "Year"), years)]))
    page.add(answer("ex163Answer", 860, 20, 400, 690, [
        f"(5) The first surge day was {ctx['first']}. From {ctx['several']}, surge days occurred in {ctx['with_surge']} of "
        f"the {ctx['span']} months (about {ctx['average']:.0f} a month), up to {ctx['peak']} in {ctx['peak_month']}: "
        + ", ".join(f"{k} in {yy}" for yy, k in ctx["by_year"]) + f". Every one has all {ctx['employees']} hourly "
        f"manufacturing employees at {ctx['regular']:.1f} regular plus {ctx['overtime']:.1f} overtime hours. Their share of "
        "the plant's overtime rose from " + " to ".join(pct(s) for s in ctx["shares"]) + ", while overtime on other "
        "days did not grow (" + ", ".join(f"{h:,.0f}" for h in ctx["other"]) + " hours).",
        "The production manager approved every entry the test flags. Telling the approver what the test detects is "
        "the prompt notification that Gonzalez and Hoffman (2018) found can encourage fraud when detection is weak, "
        "so the test stays in internal audit's file and goes to the audit committee; the Plant page's overtime share "
        "is a management measure, the surge-day test an audit test.",
        "Group By: Count Distinct Rows counts distinct rows of the group, not values of one column, so the "
        "aggregation is List.Count ( List.Distinct ( [TotalHours] ) )."], size=10))
    page.expect = ["Surge days by month", "Surge Share of Overtime", f"{ctx['on_surge'][-1]:,.0f}", pct(ctx["shares"][-1]),
                   "Model answer"]

    t = "Exercise 16.3"
    b.check(t, "surge days in all", ctx["total"], "[Surge Days]", 0)
    for yy, k in ctx["by_year"]:
        b.check(t, f"surge days in {yy}", k, f"CALCULATE ( [Surge Days], 'Date'[Year] = {yy} )", 0)
    b.check(t, "the first surge day", ctx["first"], "FORMAT ( MIN ( SurgeDays[WorkDate] ), \"yyyy-mm-dd\" )")
    b.check(t, "employees on every surge day (fewest)", ctx["employees"], "MIN ( SurgeDays[Employees] )", 0)
    b.check(t, "employees on every surge day (most)", ctx["employees"], "MAX ( SurgeDays[Employees] )", 0)
    b.check(t, "surge entries (all approved by the Production Manager on the work date)", ctx["entries"],
            "SUM ( SurgeDays[Employees] )", 0)
    for fn in ("MIN", "MAX"):
        b.check(t, f"total hours of the surge entries ({fn})", ctx["regular"] + ctx["overtime"],
                f"CALCULATE ( {fn} ( ClockEntries[TotalHours] ), TREATAS ( VALUES ( SurgeDays[WorkDate] ), 'Date'[Date] ) )",
                0.001)
    for yy, h, s, o in zip(years, ctx["on_surge"], ctx["shares"], ctx["other"]):
        cy = f"'Date'[Year] = {yy}"
        b.check(t, f"surge overtime hours {yy}", round(h, 2), f"CALCULATE ( [Surge Overtime Hours], {cy} )", 0.01)
        b.check(t, f"surge share of overtime {yy}", round(s, 6), f"CALCULATE ( [Surge Share of Overtime], {cy} )", 0.000005)
        b.check(t, f"overtime on other days {yy}", round(o, 2),
                f"CALCULATE ( [Plant Overtime Hours] - [Surge Overtime Hours], {cy} )", 0.01)
    peak = b.d.one("SELECT substr(MAX(WorkDate), 1, 7) FROM TimeClockEntry")
    months = ("COUNTROWS ( FILTER ( CALCULATETABLE ( VALUES ( 'Date'[YearMonth] ), 'Date'[YearMonth] >= \"{}\", "
              "'Date'[YearMonth] <= \"{}\" ), [Surge Days] > 0 ) )")
    first_month = b.d.one("SELECT MIN(substr(WorkDate, 1, 7)) FROM TimeClockEntry")
    sev = [mm for mm in [f"{yy}-{k:02d}" for yy in years for k in range(1, 13)] if first_month <= mm <= peak]
    several = next(mm for mm in sev if ch16.month_year(mm + "-01") == ctx["several"])
    b.check(t, f"months with surge days from {ctx['several']}", ctx["with_surge"], months.format(several, peak), 0)
    b.check(t, f"surge days in {ctx['peak_month']} (the most)", ctx["peak"],
            "MAXX ( VALUES ( 'Date'[YearMonth] ), [Surge Days] )", 0)


# --- Exercise 16.4 ---------------------------------------------------------------------------------------------------

def ex4(b: Build) -> None:
    ctx = ch16.ex4(b.d, claim)
    folder, years = "Ex 16.4", b.d.years
    measure(b, folder, "Unexplained Rate per 1,000",
            "DIVIDE (\n    CALCULATE (\n        [Exceptions],\n        Exceptions[Disposition] <> \"Expected\",\n"
            "        Tests[TestID] <> \"PR SelfApproved\"\n    ),\n    [Population]\n) * 1000", "0.0")
    process = {r[0][:2]: r[2] for r in md_table(CHAPTER / "chapter.qmd", "tbl-16-01")}
    page = b.report.add(Page("ex164", "Ex 16.4"))
    pr, yr = col("Tests", "Process"), col("Date", "Year")
    page.add(Visual("ratesMatrix", "pivotTable", 20, 20, 1240, 230, {"Rows": [pr], "Columns": [yr], "Values": [
        M("Exceptions"), M("Population"), M("Rate per 1,000"), M("Unexplained Rate per 1,000")]},
        title="Exceptions, population, and rates by process and year", filters=[keep("rmYears", yr, years)]))
    for i, (n, title) in enumerate([("Rate per 1,000", "Rate per 1,000 by year"),
                                    ("Unexplained Rate per 1,000", "Unexplained rate per 1,000 by year")]):
        page.add(Visual(f"rateLine{i}", "lineChart", 20 + 420 * i, 270, 400, 240,
                        {"Category": [yr], "Y": [M(n)], "Series": [pr]}, title=title,
                        filters=[keep(f"rl{i}Years", yr, years)]))
    tbl = dict(ctx["table"])
    po, je = tbl["PO"], ctx["unexplained"]["JE"]
    page.add(answer("ex164Answer", 860, 270, 400, 440, [
        "(1) Population counts the documents of SELECTEDVALUE ( Tests[Process] ), which is blank when several "
        "processes are in context, so the total row shows no rate: a rate across processes would mix populations.",
        f"(4) Purchase orders: the exceptions rose by {ctx['rose']} ({po[1][0]} to {po[2][0]}) while the rate "
        f"{ctx['moved']} ({po[1][2]:.2f} to {po[2][2]:.2f}), because orders grew by {pct(ctx['growth'], 0)}; from "
        f"{years[0]} the rate fell by {ctx['fell']} while orders more than doubled.",
        f"(5) Journal entries are the process to watch: the unexplained rate fell from {je[0]:.2f} to {je[1]:.2f} and "
        f"rose to {je[2]:.2f}, mostly through single documents that fail several tests (the opening entry's "
        f"{ctx['opening']}, the debt reclassifications' {ctx['reclass']} each), while Weekend, Backdated, and "
        f"SelfApproved {ctx['still']}. Payroll's unexplained exceptions are {ctx['pr_left']} a year, so its rate is "
        "almost entirely the design finding; purchase orders are improving. The unexplained rate shows what changes "
        "once the expected and recurring exceptions are set aside."], size=10))
    page.add(Visual("ratesTable", "tableEx", 20, 530, 820, 180, {"Values": [
        pr, M("Exceptions"), M("Population"), M("Rate per 1,000"), M("Unexplained Rate per 1,000")]},
        title=f"Fiscal {years[-1]}", filters=[keep("rtYear", yr, [years[-1]])]))
    page.expect = ["Unexplained Rate per 1,000", process["JE"], f"{tbl['JE'][0][2]:.1f}", f"{je[0]:.1f}", "Model answer"]

    t = "Exercise 16.4"
    for p in ch16.PROCESSES:
        for yy, (n, pop, rate), un in zip(years, tbl[p], ctx["unexplained"][p]):
            f = f"Tests[Process] = \"{process[p]}\", 'Date'[Year] = {yy}"
            b.check(t, f"{p} {yy} exceptions", n, f"CALCULATE ( [Exceptions], {f} )", 0)
            b.check(t, f"{p} {yy} population", pop, f"CALCULATE ( [Population], {f} )", 0)
            b.check(t, f"{p} {yy} rate per 1,000", round(rate, 4), f"CALCULATE ( [Rate per 1,000], {f} )", 0.0001)
            b.check(t, f"{p} {yy} unexplained rate per 1,000", round(un, 4),
                    f"CALCULATE ( [Unexplained Rate per 1,000], {f} )", 0.0001)
    b.check(t, "the total row's rate (blank)", "blank",
            f"IF ( ISBLANK ( CALCULATE ( [Rate per 1,000], 'Date'[Year] = {years[-1]} ) ), \"blank\", \"not blank\" )")


# --- Exercise 16.5 ---------------------------------------------------------------------------------------------------

def ex5(b: Build) -> None:
    ctx = ch16.ex5(b.d, claim)
    m, folder, end = b.model, "Ex 16.5", ch16.asof(b.d)
    # (1) the payments through the as-of date, with their invoice's total and their kind
    invoices = Query.navigator("PaymentInvoices", b.xlsx, 37, "PurchaseInvoice").select(["PurchaseInvoiceID", "GrandTotal"])
    m.stage(invoices)
    pay = (Query.navigator("Payments", b.xlsx, 39, "DisbursementPayment")
           .select(["DisbursementID", "PaymentDate", "SupplierID", "PurchaseInvoiceID", "Amount"])
           .types({"PaymentDate": "type date"}).filter(f"[PaymentDate] <= {mdate(end)}")
           .merge(invoices, "PurchaseInvoiceID", "PurchaseInvoiceID", ["GrandTotal"])
           .custom("PaymentKind", 'if [Amount] = [GrandTotal] then "Full" else if [Amount] < [GrandTotal] then "Partial" '
                                  'else null', "type text"))
    t_pay = m.add(query_table(pay, formats={"Amount": "#,0.00", "GrandTotal": "#,0.00"},
                              summarize={k: "none" for k in ("DisbursementID", "SupplierID", "PurchaseInvoiceID")},
                              hidden={"DisbursementID", "PurchaseInvoiceID"}))
    m.relate("Payments.PaymentDate", "Date.Date")
    # (2) the first digit from the amount's scientific notation
    t_pay.columns.append(Column("FirstDigit", "double", fmt="0", summarize="none",          # VALUE returns a number
                                expression="VALUE ( LEFT ( FORMAT ( Payments[Amount], \"0.00000000E+00\" ), 1 ) )"))
    # (3) the digits and Benford's expected share (a disconnected calculated table), and the measures
    m.add(Table("Digits", [Column("Digit", "int64", "[Digit]", summarize="none"),
                           Column("Expected Share", "double", "[Expected Share]", fmt="0.0%", summarize="none")],
                dax="ADDCOLUMNS (\n    SELECTCOLUMNS ( GENERATESERIES ( 1, 9, 1 ), \"Digit\", [Value] ),\n"
                    "    \"Expected Share\", LOG10 ( 1 + 1 / [Digit] )\n)"))
    for n, dax, fmt in [
            ("Payments Counted", "COUNTROWS ( Payments )", "#,0"),
            ("Observed Share", "VAR Digit = SELECTEDVALUE ( Digits[Digit] )\nRETURN\n    DIVIDE ( CALCULATE ( "
                               "COUNTROWS ( Payments ), Payments[FirstDigit] = Digit ), COUNTROWS ( Payments ) )", "0.0%"),
            ("Benford Share", "SELECTEDVALUE ( Digits[Expected Share] )", "0.0%"),
            ("Benford MAD", "AVERAGEX ( VALUES ( Digits[Digit] ), ABS ( [Observed Share] - [Benford Share] ) )", "0.00000")]:
        measure(b, folder, n, dax, fmt)
    page = b.report.add(Page("ex165", "Ex 16.5"))
    kind = col("Payments", "PaymentKind")
    page.add(Visual("kindSlicer", "slicer", 20, 20, 200, 120, {"Values": [kind]}, title="PaymentKind"))
    page.add(Visual("digits", "clusteredColumnChart", 240, 20, 1020, 330, {
        "Category": [col("Digits", "Digit")], "Y": [M("Observed Share"), M("Benford Share")]},
        title="First digits of the payments: observed and Benford's expected share"))
    page.add(Visual("madByKind", "tableEx", 20, 370, 500, 160, {"Values": [kind, M("Payments Counted"), M("Benford MAD")]},
                    title="Mean absolute deviation by kind of payment"))
    page.extra = {"visualInteractions": [{"source": "kindSlicer", "target": "madByKind", "type": "NoFilter"}]}
    mad = ctx["mad"]
    level = ["close conformity", "acceptable conformity", "marginally acceptable conformity", "nonconformity"]
    page.add(answer("ex165Answer", 540, 370, 720, 340, [
        f"(4) {ctx['n']:,} payments through {end}: MAD {mad['all']:.5f} ({level[ch16.conformity(mad['all'])]}); full "
        f"payments {ctx['n_full']:,}, {mad['full']:.5f} ({level[ch16.conformity(mad['full'])]}); partial payments "
        f"{ctx['n_partial']:,}, {mad['partial']:.5f} ({level[ch16.conformity(mad['partial'])]}).",
        f"(2) The first character of the amount as text fails on the {ctx['small']} payments below $1, whose text "
        "begins with 0; scientific notation always starts with the first significant digit.",
        "(5) Only invoices of $1,000 or more are paid in parts, so the partial payments' digits follow the payment "
        "policy, not fraud: the departure is an anomaly to look at (which invoices, which suppliers), not an exception "
        "that breaks a rule."], size=10))
    page.expect = ["Observed Share", "Benford MAD", f"{mad['all']:.5f}", f"{mad['partial']:.5f}", "Model answer"]

    t = "Exercise 16.5"
    b.check(t, "payments through the as-of date", ctx["n"], "[Payments Counted]", 0)
    b.check(t, "full payments", ctx["n_full"], "CALCULATE ( [Payments Counted], Payments[PaymentKind] = \"Full\" )", 0)
    b.check(t, "partial payments", ctx["n_partial"], "CALCULATE ( [Payments Counted], Payments[PaymentKind] = \"Partial\" )", 0)
    for k, label in (("all", "all payments"), ("full", "full payments"), ("partial", "partial payments")):
        f = "" if k == "all" else f", Payments[PaymentKind] = \"{k.title()}\""
        b.check(t, f"MAD, {label}", round(mad[k], 7), f"CALCULATE ( [Benford MAD]{f} )", 0.0000005)
    b.check(t, "payments with a first digit of 0", 0, "CALCULATE ( [Payments Counted] + 0, Payments[FirstDigit] = 0 )", 0)
    b.check(t, "payments whose text begins with 0 (below $1)", ctx["small"],
            "COUNTROWS ( FILTER ( Payments, LEFT ( Payments[Amount], 1 ) = \"0\" ) )", 0)
    b.check(t, "Digits rows", 9, "COUNTROWS ( Digits )", 0)
    b.check(t, "the expected shares add up to one", 1, "SUM ( Digits[Expected Share] )", 0.000001)
    for k in (1, 9):
        b.check(t, f"Benford's expected share of {k}", round(math.log10(1 + 1 / k), 6),
                f"CALCULATE ( [Benford Share], Digits[Digit] = {k} )", 0.000001)


# --- Exercise 16.6 ---------------------------------------------------------------------------------------------------

def ex6(b: Build) -> None:
    ctx = ch16.ex6(b.d, claim)
    m, folder = b.model, "Ex 16.6"
    # (1) and (2) the payments merged with themselves on supplier and amount
    pay = m.tables["Payments"].query
    pairs = Query.reference("PaymentPairs", pay)
    pairs.raw("Merged Queries", f"Table.NestedJoin({pq.PREV}, {{\"SupplierID\", \"Amount\"}}, Payments, "
                                "{\"SupplierID\", \"Amount\"}, \"Payments\", JoinKind.Inner)", None)
    pairs.raw("Expanded Payments", f"Table.ExpandTableColumn({pq.PREV}, \"Payments\", {{\"DisbursementID\", "
                                   "\"PaymentDate\", \"PurchaseInvoiceID\"}, {\"PairDisbursementID\", \"PairPaymentDate\", "
                                   "\"PairInvoiceID\"})",
              pairs.columns | {"PairDisbursementID": "Int64.Type", "PairPaymentDate": "type date", "PairInvoiceID": "Int64.Type"})
    pairs.filter("[DisbursementID] < [PairDisbursementID] and [PaymentDate] <> [PairPaymentDate]")
    pairs.custom("DaysApart", "Number.Abs(Duration.Days([PairPaymentDate] - [PaymentDate]))", "Int64.Type")
    pairs.custom("SameInvoice", "[PurchaseInvoiceID] = [PairInvoiceID]", "type logical")
    ids = ("DisbursementID", "SupplierID", "PurchaseInvoiceID", "PairDisbursementID", "PairInvoiceID", "DaysApart")
    m.add(query_table(pairs, formats={"Amount": "#,0.00", "GrandTotal": "#,0.00"}, summarize={k: "none" for k in ids}))
    # (3) and (4) the approvals
    for n, dax, fmt in [
            ("Pairs", "COUNTROWS ( PaymentPairs )", "#,0"),
            ("Pairs Within 30 Days", "CALCULATE ( [Pairs], PaymentPairs[DaysApart] <= 30 )", "#,0"),
            ("Pairs on the Same Invoice", "CALCULATE ( [Pairs], PaymentPairs[SameInvoice] = TRUE () ) + 0", "#,0"),
            ("Entries Approved", "COUNTROWS ( JournalEntry )", "#,0"),
            ("Orders Approved", "CALCULATE (\n    COUNTROWS ( PurchaseOrder ),\n    TREATAS ( VALUES ( Employee[EmployeeID] ), "
                                "PurchaseOrder[ApprovedByEmployeeID] )\n)", "#,0"),
            ("Registers Approved", "CALCULATE (\n    COUNTROWS ( PayrollRegister ),\n    TREATAS ( VALUES ( Employee[EmployeeID] ), "
                                   "PayrollRegister[ApprovedByEmployeeID] )\n)", "#,0"),
            ("Entries Share", "DIVIDE ( [Entries Approved], CALCULATE ( COUNTROWS ( JournalEntry ), REMOVEFILTERS ( Employee ) ) )",
             "0.00%"),
            ("Orders Share", "DIVIDE ( [Orders Approved], COUNTROWS ( PurchaseOrder ) )", "0.00%"),
            ("Registers Share", "DIVIDE ( [Registers Approved], COUNTROWS ( PayrollRegister ) )", "0.00%")]:
        measure(b, folder, n, dax, fmt)
    page = b.report.add(Page("ex166", "Ex 16.6"))
    page.add(card("pairCards", 20, 20, 600, 100, [M("Pairs"), M("Pairs Within 30 Days"), M("Pairs on the Same Invoice")]))
    page.add(Visual("pairsByDays", "clusteredColumnChart", 20, 130, 600, 250, {
        "Category": [col("PaymentPairs", "DaysApart")], "Y": [M("Pairs")]}, title="Near-duplicate pairs by days apart"))
    page.add(Visual("approvalShares", "tableEx", 640, 20, 620, 360, {"Values": [
        col("Employee", "EmployeeName"), col("Employee", "JobTitle"), M("Entries Approved"), M("Entries Share"),
        M("Orders Approved"), M("Orders Share"), M("Registers Approved"), M("Registers Share")]},
        title="Documents approved, and their share of each process", sort=[(M("Orders Approved"), "Descending")]))
    cfo, ctl, mgr = ctx["cfo"], ctx["controller"], ctx["manager"]
    page.add(answer("ex166Answer", 20, 400, 1240, 310, [
        f"(2) {ctx['pairs']} supplier-and-amount pairs on different dates among the payments through {ctx['asof']}, "
        f"{ctx['within30']} within 30 days, none paying the same invoice.",
        f"(4) {cfo['name']} ({cfo['title']}) approved {cfo['n']:,} orders ({pct(cfo['share'], 2)}) and "
        f"{ctx['cfo_entries']['n']} entries ({pct(ctx['cfo_entries']['share'], 2)}); {ctl['name']} ({ctl['title']}) "
        f"{ctl['n']:,} entries ({pct(ctl['share'], 2)}); {mgr['name']} ({mgr['title']}) {mgr['n']:,} registers "
        f"({pct(mgr['share'], 0)}) and {ctx['manager_entries']['n']} entries ({pct(ctx['manager_entries']['share'], 2)}); "
        f"the other {ctx['other_orders']} orders spread over {ctx['other_people']} employees, including the departed "
        f"Account Executive ({ctx['executive']}). The bar chart of exceptions by approver puts {mgr['name']} first "
        f"({ctx['first']}) and {cfo['name']} second ({ctx['second']}).",
        "(5) A pair on different invoices is two payments that happen to match, which two invoices of the same amount "
        "explain; it is an anomaly to look at, not a duplicate payment, until an invoice is found paid twice. The "
        "shares show that each of three processes rests on one approver, a design question no exception shows: "
        "segregation of duties, who approves when that person is away, and who approves that person's own documents."],
        size=10))
    page.expect = ["Orders Share", "Registers Share", cfo["name"], f"{cfo['n']:,}", pct(cfo["share"], 2), "Model answer"]

    t = "Exercise 16.6"
    b.check(t, "near-duplicate pairs", ctx["pairs"], "[Pairs]", 0)
    b.check(t, "pairs within 30 days", ctx["within30"], "[Pairs Within 30 Days]", 0)
    b.check(t, "pairs on the same invoice", 0, "[Pairs on the Same Invoice]", 0)
    for who, key, n, s in [(cfo, "Orders", cfo["n"], cfo["share"]), (cfo, "Entries", ctx["cfo_entries"]["n"],
                                                                          ctx["cfo_entries"]["share"]),
                           (ctl, "Entries", ctl["n"], ctl["share"]), (mgr, "Registers", mgr["n"], mgr["share"]),
                           (mgr, "Entries", ctx["manager_entries"]["n"], ctx["manager_entries"]["share"])]:
        f = f"Employee[EmployeeID] = {who['id']}"
        b.check(t, f"{key} Approved, {who['title']}", n, f"CALCULATE ( [{key} Approved], {f} )", 0)
        b.check(t, f"{key} Share, {who['title']}", round(s, 6), f"CALCULATE ( [{key} Share], {f} )", 0.000005)
    b.check(t, "orders approved by others than the CFO", ctx["other_orders"],
            f"CALCULATE ( [Orders Approved], Employee[EmployeeID] <> {cfo['id']} )", 0)
    b.check(t, "employees who approved those orders", b.d.one(
        "SELECT COUNT(DISTINCT ApprovedByEmployeeID) FROM PurchaseOrder WHERE ApprovedByEmployeeID <> ?", cfo["id"]),
        f"COUNTROWS ( FILTER ( VALUES ( Employee[EmployeeID] ), Employee[EmployeeID] <> {cfo['id']} && "
        "NOT ISBLANK ( [Orders Approved] ) ) )", 0)
    b.check(t, "orders approved by the departed Account Executive", ctx["executive"],
            "CALCULATE ( [Orders Approved], Employee[JobTitle] = \"Account Executive\" )", 0)


EXERCISES = [("16.1", ex1), ("16.2", ex2), ("16.3", ex3), ("16.4", ex4), ("16.5", ex5), ("16.6", ex6)]
