"""Audit Monitoring.pbip with the credits cycle's continuing tests: the Power BI part of the solution to Requirement 10 of
the Chapter 19 capstone case, built on a copy of internal audit's file as Tutorial 16.3 leaves it.

Requirement 10 adds four rule tests to the register (credits above the approver's authority, credits approved by
someone who applied cash to the credited invoice, refunds above authority, and refunds dated before the customer's last
payment on the invoice) and the processes Credit memos and Refunds to the populations, under the change control
Chapter 16 described. The flags are computed in Power Query, as Tutorials 16.1 and 16.2 computed theirs and as the
note describes: for BeforePayment the applications are grouped by invoice for the last ApplicationDate and merged; for
CashAndCredit they are grouped by invoice and applier and merged on the credit's invoice and approver. The two new
exception queries are appended to the Exceptions query's Source step, and the Tests table gains four rows.

The historical exceptions of the new tests get one design-finding treatment: a Design Findings table (Enter data, one
row per new test, naming the finding and the date by which its design is to be fixed) is merged into the register by
TestID, an exception dated by that date is covered by the finding, and Open Exceptions leaves the covered exceptions
out, so the review sees only the exceptions dated after the fix. The refund method and the missing offset stay anomaly
tests: columns of CustomerRefund, outside the register, on a page of their own. Data Through takes the last credit and
refund dates as well (the date stays payroll's), and a Change Log table (Enter data) records the change.

Checks: every value of the instructor notes of Requirement 10 and Milestones 2 and 3 that the file shows, computed by
facts/notes/ch19.py (the case's definitions) and facts/notes/ch16.py (the register), and the chain's checks over the
whole register, recomputed for the larger register.
"""

from __future__ import annotations

from collections import Counter

from pbibuild.audit_monitoring import COUNT, MEASURES, MONEY, REGISTER, Build, exceptions, flags
from pbibuild.ex16 import group
from pbibuild.model import Column, Measure, Query, Table, query_table
from pbibuild.pbir import Page, Visual, col, meas, textbox
from pbibuild.reports import card, claim, keep, money

from notes import ch16, ch19  # noqa: E402  (facts/ is on sys.path through pbibuild.audit_monitoring)

M = lambda n: meas(MEASURES, n)           # noqa: E731
NEW_TESTS = [("CM AboveLimit", "Credit above its approver's limit", "Credit memos", "Chapter 19"),
             ("CM CashAndCredit", "Credit approved by someone who applied cash to its invoice", "Credit memos", "Chapter 19"),
             ("RF AboveLimit", "Refund above its approver's limit", "Refunds", "Chapter 19"),
             ("RF BeforePayment", "Refund dated before the customer's last payment on the credited invoice", "Refunds",
              "Chapter 19")]
FIX_BY = "2027-12-31"           # the action plans' date (Requirement 9): the delegation of authority and the refund rule
FINDINGS = {"CM": "Credits approved without a delegation of authority, by customer service staff who also apply the cash",
            "RF": "Refunds approved without a delegation of authority, before the customer's payment has cleared"}
CHANGE_DATE = "2027-09-30"      # the end of the audit's fieldwork (the case is set in September 2027)

POPULATION = """SWITCH (
    SELECTEDVALUE ( Tests[Process] ),
    "Journal entries", COUNTROWS ( JournalEntry ),
    "Purchase orders", COUNTROWS ( PurchaseOrder ),
    "Payroll", COUNTROWS ( PayrollRegister ),
    "Credit memos", COUNTROWS ( CreditMemo ),
    "Refunds", COUNTROWS ( CustomerRefund )
)"""
DATA_THROUGH = """MINX (
    {
        MAX ( JournalEntry[PostingDate] ),
        MAX ( PurchaseOrder[OrderDate] ),
        MAX ( PayrollRegister[PayDate] ),
        MAX ( CreditMemo[CreditMemoDate] ),
        MAX ( CustomerRefund[RefundDate] )
    },
    [Value]
)"""
OPEN = "CALCULATE ( [Exceptions], ISBLANK ( Exceptions[Disposition] ), Exceptions[Covered] = 0 )"


def set_measure(b: Build, name: str, dax: str) -> str:
    """Edit a measure of the Key Measures table in place; returns its old DAX."""
    m = next(x for x in b.model.tables[MEASURES].measures if x.name == name)
    old, m.dax = m.dax, dax
    return old


def add_measure(b: Build, name: str, dax: str, fmt: str | None, desc: str) -> None:
    b.model.tables[MEASURES].measures.append(Measure(name, dax, fmt, desc, display_folder="Credits cycle"))


def answer(name: str, x, y, w, h, title: str, lines: list, size: int = 10) -> Visual:
    return textbox(name, x, y, w, h, [(f"Model answer: {title}", True)] + lines, size=size)


def new_register(d) -> list[dict]:
    """The rows the four new tests add to the register, as the Exceptions query has them."""
    t = ch19.tests(d)
    out = []
    for test, rows, kind in (("CM AboveLimit", t.cm_above, "cm"), ("CM CashAndCredit", t.cash_credit, "cm"),
                             ("RF AboveLimit", t.rf_above, "rf"), ("RF BeforePayment", t.before, "rf")):
        for r in rows:
            out.append(dict(test=test, process=test[:2], doc=r["num"], date=r["date"],
                            amount=r["gt"] if kind == "cm" else r["amt"], emp=r["appr"], disposition=None))
    return out


# --- Requirement 10 -----------------------------------------------------------------------------------------------

def r10(b: Build) -> None:
    d, m, x = b.d, b.model, b.xlsx
    ctx = ch19.r10(d, claim)
    r4 = ch19.r4(d, claim)
    c, t = ch19.cycle(d), ch19.tests(d)
    emp = b.q["Employee"]
    s = "Requirement 10"

    # Queries: the applications grouped twice (Enable load cleared), the credit memos and refunds with their flags
    apps = (Query.navigator("CashReceiptApplication", x, 20, "CashReceiptApplication")
            .select(["CashReceiptID", "SalesInvoiceID", "ApplicationDate", "AppliedAmount", "AppliedByEmployeeID"])
            .types({"ApplicationDate": "type date"}))
    last = group(Query.reference("Last Payments", apps), ["SalesInvoiceID"],
                 [("LastPayment", "List.Max([ApplicationDate])", "type nullable date")])
    appliers = group(Query.reference("Appliers", apps), ["SalesInvoiceID", "AppliedByEmployeeID"],
                     [("Applications", "Table.RowCount(_)", "Int64.Type")])
    cm = (Query.navigator("CreditMemo", x, 23, "CreditMemo")
          .select(["CreditMemoID", "CreditMemoNumber", "CreditMemoDate", "CustomerID", "OriginalSalesInvoiceID",
                   "GrandTotal", "ApprovedByEmployeeID"])
          .types({"CreditMemoDate": "type date"})
          .merge(emp, "ApprovedByEmployeeID", "EmployeeID", ["MaxApprovalAmount"]).rename({"MaxApprovalAmount": "ApproverLimit"})
          .merge(appliers, ["OriginalSalesInvoiceID", "ApprovedByEmployeeID"], ["SalesInvoiceID", "AppliedByEmployeeID"],
                 ["Applications"])
          .rename({"Applications": "ApproverApplications"}))
    flags(cm, [("AboveLimit", "if [GrandTotal] > [ApproverLimit] then 1 else 0"),
               ("CashAndCredit", "if [ApproverApplications] <> null then 1 else 0")])
    # the anomaly tests' inputs: the methods of the receipts on each invoice, and each customer's past-due balance on
    # each refund date (invoices dated by then and due before it, less the applications and credits dated by then)
    receipts = Query.navigator("CashReceipt", x, 19, "CashReceipt").select(["CashReceiptID", "PaymentMethod"])
    methods = group(Query.reference("Invoice Methods", apps).merge(receipts, "CashReceiptID", "CashReceiptID", ["PaymentMethod"]),
                    ["SalesInvoiceID", "PaymentMethod"], [("Receipts", "Table.RowCount(_)", "Int64.Type")])
    invoices = (Query.navigator("SalesInvoice", x, 16, "SalesInvoice")
                .select(["SalesInvoiceID", "CustomerID", "InvoiceDate", "DueDate", "GrandTotal"])
                .types({"InvoiceDate": "type date", "DueDate": "type date"}))
    credits = (Query.reference("Invoice Credits", cm).select(["OriginalSalesInvoiceID", "CreditMemoDate", "GrandTotal"])
               .rename({"GrandTotal": "CreditAmount"}))
    dates = (Query.navigator("Refund Dates", x, 25, "CustomerRefund").select(["RefundNumber", "CustomerID", "RefundDate"])
             .types({"RefundDate": "type date"}))
    due = (Query.reference("Past Due at Refund", dates)
           .merge(invoices, "CustomerID", "CustomerID", ["SalesInvoiceID", "InvoiceDate", "DueDate", "GrandTotal"])
           .filter("[InvoiceDate] <= [RefundDate] and [DueDate] < [RefundDate]")
           .merge(apps, "SalesInvoiceID", "SalesInvoiceID", ["ApplicationDate", "AppliedAmount"])
           .custom("PaidThen", "if [ApplicationDate] <> null and [ApplicationDate] <= [RefundDate] then [AppliedAmount] else 0",
                   "type number"))
    group(due, ["RefundNumber", "RefundDate", "SalesInvoiceID", "GrandTotal"], [("Paid", "List.Sum([PaidThen])", "type number")])
    due.merge(credits, "SalesInvoiceID", "OriginalSalesInvoiceID", ["CreditMemoDate", "CreditAmount"])
    due.custom("CreditedThen", "if [CreditMemoDate] <> null and [CreditMemoDate] <= [RefundDate] then [CreditAmount] else 0",
               "type number")
    group(due, ["RefundNumber", "SalesInvoiceID", "GrandTotal", "Paid"], [("Credited", "List.Sum([CreditedThen])", "type number")])
    due.custom("Balance", "[GrandTotal] - [Paid] - [Credited]", "type number").filter("[Balance] > 0.005")
    group(due, ["RefundNumber"], [("PastDue", "List.Sum([Balance])", "type number")])
    rf = (Query.navigator("CustomerRefund", x, 25, "CustomerRefund")
          .select(["CustomerRefundID", "RefundNumber", "RefundDate", "CustomerID", "CreditMemoID", "Amount", "PaymentMethod",
                   "ApprovedByEmployeeID"])
          .types({"RefundDate": "type date"})
          .merge(emp, "ApprovedByEmployeeID", "EmployeeID", ["MaxApprovalAmount"]).rename({"MaxApprovalAmount": "ApproverLimit"})
          .merge(cm, "CreditMemoID", "CreditMemoID", ["OriginalSalesInvoiceID"])
          .merge(last, "OriginalSalesInvoiceID", "SalesInvoiceID", ["LastPayment"]))
    flags(rf, [("AboveLimit", "if [Amount] > [ApproverLimit] then 1 else 0"),
               ("BeforePayment", "if [LastPayment] <> null and [RefundDate] < [LastPayment] then 1 else 0")])
    rf.merge(methods, ["OriginalSalesInvoiceID", "PaymentMethod"], ["SalesInvoiceID", "PaymentMethod"], ["Receipts"])
    rf.rename({"Receipts": "MethodReceipts"}).merge(due, "RefundNumber", "RefundNumber", ["PastDue"])
    flags(rf, [("MethodMismatch", "if [MethodReceipts] = null then 1 else 0"),
               ("OffsetMissed", "if [PastDue] <> null and [PastDue] >= [Amount] then 1 else 0")])
    cmx = (exceptions("CM Exceptions", cm, ["AboveLimit", "CashAndCredit"], "CM")
           .select(["TestID", "CreditMemoNumber", "CreditMemoDate", "GrandTotal", "ApprovedByEmployeeID"])
           .rename({"CreditMemoNumber": "DocumentNumber", "CreditMemoDate": "EventDate", "GrandTotal": "Amount",
                    "ApprovedByEmployeeID": "EmployeeID"}))
    rfx = (exceptions("RF Exceptions", rf, ["AboveLimit", "BeforePayment"], "RF")
           .select(["TestID", "RefundNumber", "RefundDate", "Amount", "ApprovedByEmployeeID"])
           .rename({"RefundNumber": "DocumentNumber", "RefundDate": "EventDate", "ApprovedByEmployeeID": "EmployeeID"}))
    for q in (cmx, rfx):
        q.columns = {k: q.columns[k] for k in REGISTER}
    reg = b.q["Exceptions"]
    claim(all(q.columns == reg.parts[0].columns for q in (cmx, rfx)), "the new exception queries have the register's columns")
    reg.parts += [cmx, rfx]                                   # the Source step's Table.Combine, two more queries
    # the design findings (Enter data), merged by TestID: an exception dated by FixBy is covered by its finding
    rows = [[tid, FINDINGS[tid[:2]], FIX_BY] for tid, *_ in NEW_TESTS]
    m.add(Table("Design Findings", [Column("TestID", "string"), Column("Finding", "string"),
                                    Column("FixBy", "dateTime", fmt="Short Date")], entered=rows, hidden=True))
    m.query_order.append("Design Findings")
    dfq = Query("Design Findings")
    dfq.columns = {"TestID": "type text", "Finding": "type text", "FixBy": "type date"}
    reg.merge(dfq, "TestID", "TestID", ["Finding", "FixBy"])
    reg.custom("Covered", "if [FixBy] <> null and [EventDate] <= [FixBy] then 1 else 0", "Int64.Type")
    m.tables["Exceptions"] = query_table(reg, formats={"Amount": MONEY, "FixBy": "Short Date"},
                                         summarize={"EmployeeID": "none", "Covered": "none"})
    for q in (apps, last, appliers, receipts, methods, invoices, credits, dates, due, cmx, rfx):
        m.stage(q)
    t_cm = m.add(query_table(cm, formats={"GrandTotal": MONEY, "ApproverLimit": MONEY},
                             summarize={k: "none" for k in ("CreditMemoID", "CustomerID", "OriginalSalesInvoiceID",
                                                            "ApprovedByEmployeeID", "ApproverApplications")},
                             hidden={"CreditMemoID", "CustomerID", "OriginalSalesInvoiceID", "ApprovedByEmployeeID",
                                     "ApproverApplications", "AboveLimit", "CashAndCredit"}))
    t_rf = m.add(query_table(rf, formats={"Amount": MONEY, "ApproverLimit": MONEY, "PastDue": MONEY},
                             summarize={k: "none" for k in ("CustomerRefundID", "CustomerID", "CreditMemoID",
                                                            "ApprovedByEmployeeID", "OriginalSalesInvoiceID",
                                                            "MethodReceipts")},
                             hidden={"CustomerRefundID", "CustomerID", "CreditMemoID", "ApprovedByEmployeeID",
                                     "OriginalSalesInvoiceID", "MethodReceipts", "AboveLimit", "BeforePayment"}))
    m.relate("CreditMemo.CreditMemoDate", "Date.Date")
    m.relate("CustomerRefund.RefundDate", "Date.Date")
    # the four tests in the Tests table (rows typed below tbl-16-01's in the Enter data table)
    m.tables["Tests"].entered += [list(r) for r in NEW_TESTS]
    # the measures: the populations, the open exceptions without the covered ones, Data Through, and the new ones
    old_pop = set_measure(b, "Population", POPULATION)
    claim("COUNTROWS ( PayrollRegister )" in old_pop, "Population is Tutorial 16.2's SWITCH")
    set_measure(b, "Open Exceptions", OPEN)
    set_measure(b, "Data Through", DATA_THROUGH)
    add_measure(b, "Design Finding Exceptions", "CALCULATE ( [Exceptions], Exceptions[Covered] = 1 )", COUNT,
                "Exceptions dated by the fix date of their test's design finding: reported once, as the finding.")
    add_measure(b, "Method Mismatch Refunds", "CALCULATE ( COUNTROWS ( CustomerRefund ), CustomerRefund[MethodMismatch] = 1 )",
                COUNT, "Anomaly test: refunds by a method no receipt on the credited invoice used.")
    add_measure(b, "Method Mismatch Amount", "CALCULATE ( SUM ( CustomerRefund[Amount] ), CustomerRefund[MethodMismatch] = 1 )",
                MONEY, "The amount of the method mismatch refunds.")
    add_measure(b, "Offset Missed Refunds", "CALCULATE ( COUNTROWS ( CustomerRefund ), CustomerRefund[OffsetMissed] = 1 )",
                COUNT, "Anomaly test: refunds paid while the customer's past-due balance was at least the refund.")
    add_measure(b, "Offset Missed Amount", "CALCULATE ( SUM ( CustomerRefund[Amount] ), CustomerRefund[OffsetMissed] = 1 )",
                MONEY, "The amount of the refunds that an offset could have covered.")
    add_measure(b, "Refunds with Past Due", "CALCULATE ( COUNTROWS ( CustomerRefund ), CustomerRefund[PastDue] > 0 )", COUNT,
                "Refunds paid while the customer had any past-due balance.")
    # the change record (Enter data)
    log = [[CHANGE_DATE, "Tests and Exceptions",
            "Added CM AboveLimit, CM CashAndCredit, RF AboveLimit, and RF BeforePayment (CreditMemo, CustomerRefund, "
            "CM Exceptions, RF Exceptions appended to Exceptions)", "Requirement 10: the credits cycle audit"],
           [CHANGE_DATE, "Population", "Added the processes Credit memos and Refunds", "Rates per 1,000 for the new tests"],
           [CHANGE_DATE, "Design Findings and Open Exceptions",
            f"The new tests' exceptions dated by {FIX_BY} are covered by two design findings and left out of Open Exceptions",
            "Report the historical exceptions once; review only those after the fix"],
           [CHANGE_DATE, "CustomerRefund anomaly columns", "MethodMismatch and OffsetMissed, outside the register",
            "Anomalies are reasons to look, not rule failures"],
           [CHANGE_DATE, "Data Through", f"Added the last credit memo and refund dates; still {ctx['through']} (payroll)",
            "Recheck the date through which the register's data run"]]
    m.add(Table("Change Log", [Column(k, "string") for k in ("Date", "Object", "Change", "Reason")], entered=log))
    m.query_order.append("Change Log")
    b.tests.append(
        "// Test 5: the tests of the credits cycle (Chapter 19) by year, with their populations\nEVALUATE\n"
        "SUMMARIZECOLUMNS (\n    Tests[TestID],\n    'Date'[Year],\n"
        "    TREATAS ( { \"Credit memos\", \"Refunds\" }, Tests[Process] ),\n    \"Exceptions\", [Exceptions],\n"
        "    \"Population\", [Population],\n    \"Rate per 1,000\", ROUND ( [Rate per 1,000], 1 )\n)\n"
        "ORDER BY Tests[TestID], 'Date'[Year]")
    b.tests.append(
        "// Test 6: the register keeps one row per test and document, and the design findings cover the new tests' past\n"
        "EVALUATE\nROW (\n    \"Rows\", COUNTROWS ( Exceptions ),\n"
        "    \"Test and document pairs\", COUNTROWS ( SUMMARIZE ( Exceptions, Exceptions[TestID], Exceptions[DocumentNumber] ) ),\n"
        "    \"Reviewed\", [Reviewed Exceptions],\n    \"Covered by a design finding\", [Design Finding Exceptions],\n"
        "    \"Open\", [Open Exceptions]\n)")
    b.project.queries["Tests"] = "\n\n".join(b.tests) + "\n"
    if "Checks" in b.project.queries:
        b.project.queries["Checks"] = b.project.queries.pop("Checks")

    # the register as it now stands, and the chain's checks over the whole register recomputed for it
    old = list(ch16.register(d))
    new = new_register(d)
    full = old + new
    claim(len(full) == ctx["new"], "the register grows to the note's rows")
    names = {r[0]: r[1] for r in d.q("SELECT EmployeeID, EmployeeName FROM Employee")}
    recompute = {("Tutorial 16.2", "Exceptions rows"), ("Tutorial 16.2", "test and document pairs (each unique)"),
                 ("Tutorial 16.2", "Tests rows"), ("Tutorial 16.3", "documents failing two tests or more"),
                 ("Tutorial 16.3", "the documents failing two tests or more")}
    recompute |= {("Tutorial 16.2", f"{mn[:3]} exceptions (all years)") for mn in ch16.MONTHS}
    recompute |= {("Tutorial 16.2", f"exceptions approved by {names[e]}") for e, _ in Counter(x["emp"] for x in old).most_common(5)}
    before = len(b.project.checks)
    b.project.checks = [(sec, ch) for sec, ch in b.project.checks if (sec, ch.label) not in recompute]
    claim(before - len(b.project.checks) == len(recompute), "the chain's checks over the whole register were found")
    s2 = "Requirement 10 (Chapter 16's checks, on the larger register)"
    b.check(s2, "Exceptions rows", len(full), "COUNTROWS ( Exceptions )", 0)
    b.check(s2, "test and document pairs (each unique)", len({(e["test"], e["doc"]) for e in full}),
            "COUNTROWS ( SUMMARIZE ( Exceptions, Exceptions[TestID], Exceptions[DocumentNumber] ) )", 0)
    b.check(s2, "Tests rows", len(ch16.TESTS) + len(NEW_TESTS), "COUNTROWS ( Tests )", 0)
    months = Counter(int(e["date"][5:7]) for e in full)
    for k in range(1, 13):
        b.check(s2, f"{ch16.MONTHS[k - 1][:3]} exceptions (all years)", months[k],
                f"CALCULATE ( [Exceptions], 'Date'[MonthNumber] = {k} )", 0)
    approvers = Counter(e["emp"] for e in full).most_common()
    for e, n in approvers[:5]:
        b.check(s2, f"exceptions approved by {names[e]}", n, f"CALCULATE ( [Exceptions], Employee[EmployeeID] = {e} )", 0)
    docs = Counter(e["doc"] for e in full)
    multi = {k: n for k, n in docs.items() if n >= 2}
    b.check(s2, "documents failing two tests or more", len(multi),
            "COUNTROWS ( FILTER ( VALUES ( Exceptions[DocumentNumber] ), [Exceptions] >= 2 ) )", 0)
    b.check(s2, "the documents failing two tests or more", ", ".join(sorted(multi)),
            "CONCATENATEX ( FILTER ( VALUES ( Exceptions[DocumentNumber] ), [Exceptions] >= 2 ), "
            "Exceptions[DocumentNumber], \", \", Exceptions[DocumentNumber], ASC )")
    # the page expectations of Tutorials 16.2 and 16.3 over the whole register
    mon, review = b.report.page("monitoring"), b.report.page("review")
    old_multi = sorted(k for k, n in Counter(e["doc"] for e in old).items() if n >= 2)
    review.expect = [w for w in review.expect if w != old_multi[-1]]   # the last of 19 rows; the list is longer now
    # the heat map gets room for the four new rows (and the approvers and rates below it move down)
    for v in mon.visuals:
        if v.name == "heatMap":
            v.h = 440
        elif v.name in ("approvers", "rates"):
            v.y, v.h = 480, 230
    old_months = Counter(int(e["date"][5:7]) for e in old)
    top_old = names[Counter(e["emp"] for e in old).most_common(1)[0][0]]
    mon.expect = [w for w in mon.expect if w not in (f"{old_months[1]:,}", top_old)] + [
        "CM AboveLimit", f"{months[1]:,}", names[approvers[0][0]]]

    # the Credits Cycle page
    page = b.report.add(Page("creditsCycle", "Credits Cycle"))
    test_col, year_col = col("Tests", "TestID"), col("Date", "Year")
    new_ids = [tid for tid, *_ in NEW_TESTS]
    page.add(Visual("newTests", "pivotTable", 20, 20, 820, 200, {
        "Rows": [test_col], "Columns": [year_col], "Values": [M("Exceptions"), M("Population"), M("Rate per 1,000")]},
        title="The credits cycle's tests by year", filters=[keep("newTestIds", test_col, new_ids)]))
    page.add(card("registerCards", 860, 20, 400, 200, [M("Exceptions"), M("Reviewed Exceptions"),
                                                       M("Design Finding Exceptions"), M("Open Exceptions")]))
    page.add(Visual("findings", "tableEx", 20, 235, 1240, 130, {"Values": [
        col("Exceptions", "TestID"), col("Exceptions", "Finding"), col("Exceptions", "FixBy"),
        M("Design Finding Exceptions"), M("Open Exceptions")]}, title="Design findings: reported once, reviewed after the fix",
        filters=[keep("findingTests", col("Exceptions", "TestID"), new_ids)]))
    tests_ = {x_["name"]: x_ for x_ in ctx["tests"]}
    page.add(answer("cycleAnswer", 20, 380, 1240, 330, "the continuing tests", [
        "Four rule tests join the register: " + "; ".join(
            f"{x_['name']} {x_['n']} ({' / '.join(str(v) for v in x_['years'])}; per 1,000 "
            f"{' / '.join(f'{v:.1f}' for v in x_['rates'])}, {x_['rate']:.1f} over the three years)" for x_ in ctx["tests"]) +
        f". Populations: credits {' / '.join(str(v) for v in ctx['pop_c'])}, refunds {' / '.join(str(v) for v in ctx['pop_r'])}. "
        f"The register grows from {ctx['old']} to {ctx['new']} rows, and each test and document pair is still unique.",
        f"Design findings: the {len(new)} historical exceptions of the new tests are reported once, as two findings about "
        f"the design of the controls (credits and refunds approved without a delegation of authority), to be fixed by "
        f"{FIX_BY}. Exceptions dated by then are covered by the finding and left out of Open Exceptions, which stays at "
        f"{sum(1 for e in old if not e['disposition'])}, so the new tests do not flood the review. After the fix, the two "
        "authority tests should fall to zero; CashAndCredit and BeforePayment are the ones that would catch the next case.",
        f"Data Through stays {ctx['through']}, set by payroll's last pay date: the credits run to {ctx['cm_last']} and the "
        f"refunds to {ctx['rf_last']}. The refund method and the missing offset stay anomaly tests, outside the register "
        "(the Anomalies page), because they are reasons to look rather than rule failures. The Change Log page records "
        "the change, and Tests 5 and 6 in the Tests tab are rerun with Tests 1 to 4 before the file is used."]))
    cmab = tests_["CM AboveLimit"]
    page.expect = ["CM AboveLimit", "RF BeforePayment", f"{cmab['rates'][-1]:.1f}", f"{cmab['n']:,}",
                   f"Design Finding Exceptions, {len(new)} card", "Model answer: the continuing tests", FIX_BY[:4]]

    # the Anomalies page
    page = b.report.add(Page("anomalies", "Anomalies"))
    page.add(Visual("anomalyYears", "tableEx", 20, 20, 1240, 150, {"Values": [
        year_col, M("Method Mismatch Refunds"), M("Method Mismatch Amount"), M("Refunds with Past Due"),
        M("Offset Missed Refunds"), M("Offset Missed Amount")]}, title="Anomaly tests on the refunds, by year (outside the register)"))
    page.add(answer("anomalyAnswer", 20, 190, 1240, 200, "why these stay anomalies", [
        f"Method mismatch: {r4['mism']['n']} refunds ({money(r4['mism']['amt'])}; {r4['mism']['cur'][0]} in {d.C}, "
        f"{money(r4['mism']['cur'][1])}) went by a method no receipt on the credited invoice used. No customer pays by one "
        f"method only, and a method chosen at random across the {r4['n_methods']} methods would mismatch about as often, "
        "so it is a reason to look, not a rule.",
        f"Missing offset: {r4['pd1']['n']} refunds ({money(r4['pd1']['amt'])}) were paid while the customer had a past-due "
        f"balance, {r4['pd2']['n']} ({money(r4['pd2']['amt'])}; {r4['pd2']['cur'][0]} in {d.C}, {money(r4['pd2']['cur'][1])}) "
        "of them a balance at least as large as the refund. No policy requires an offset yet, so these stay anomalies "
        "until one does; then the rule joins the register."]))
    page.expect = ["Method Mismatch Refunds", "Offset Missed Refunds", money(r4["mism"]["cur"][1]), money(r4["pd2"]["cur"][1])]

    # the Change Log page
    page = b.report.add(Page("changeLog", "Change Log"))
    page.add(Visual("log", "tableEx", 20, 20, 1240, 300, {"Values": [
        col("Change Log", k) for k in ("Date", "Object", "Change", "Reason")]}, title="Changes to this file"))
    page.add(answer("logAnswer", 20, 340, 1240, 200, "the change under change control", [
        "The change was made in the Power BI project under version control, on its own branch, and the reviewer approves "
        "it from the list of changed lines before it is merged: the queries CreditMemo, CustomerRefund, CM Exceptions, "
        "RF Exceptions and their inputs, the Exceptions query's Source step and its Design Findings merge, the Tests, "
        "Design Findings, and Change Log tables, and the measures Population, Open Exceptions, and Data Through.",
        "Tests 1 to 6 are rerun before the file is used: Test 2 now lists fifteen tests, Test 5 the new tests by year, "
        "and Test 6 the register's rows, reviewed, covered, and open exceptions. No copy of the .pbix leaves internal audit."]))
    page.expect = ["Changes to this file", "Data Through", "Population", CHANGE_DATE]

    # checks
    yrs = d.years
    b.check(s, "CreditMemo rows", len(c.cm), "COUNTROWS ( CreditMemo )", 0)
    b.check(s, "CustomerRefund rows", len(c.rf), "COUNTROWS ( CustomerRefund )", 0)
    b.check(s, "credit approvers with no limit", 0, "COUNTROWS ( FILTER ( CreditMemo, ISBLANK ( CreditMemo[ApproverLimit] ) ) )", 0)
    b.check(s, "refund approvers with no limit", 0,
            "COUNTROWS ( FILTER ( CustomerRefund, ISBLANK ( CustomerRefund[ApproverLimit] ) ) )", 0)
    for proc, pops in (("Credit memos", ctx["pop_c"]), ("Refunds", ctx["pop_r"])):
        for y, n in zip(yrs, pops):
            b.check(s, f"{proc} population {y}", n, f"CALCULATE ( [Population], Tests[Process] = \"{proc}\", 'Date'[Year] = {y} )", 0)
        b.check(s, f"{proc} population, three years", sum(pops), f"CALCULATE ( [Population], Tests[Process] = \"{proc}\" )", 0)
    for flag, n in (("CreditMemo[AboveLimit]", len(t.cm_above)), ("CreditMemo[CashAndCredit]", len(t.cash_credit)),
                    ("CustomerRefund[AboveLimit]", len(t.rf_above)), ("CustomerRefund[BeforePayment]", len(t.before))):
        b.check(s, f"flags {flag}", n, f"SUM ( {flag} )", 0)
    for x_ in ctx["tests"]:
        f = f"Tests[TestID] = \"{x_['name']}\""
        b.check(s, f"{x_['name']} exceptions", x_["n"], f"CALCULATE ( [Exceptions], {f} )", 0)
        b.check(s, f"{x_['name']} rate per 1,000, three years", round(x_["rate"], 6), f"CALCULATE ( [Rate per 1,000], {f} )", 0.0001)
        for y, n, rate in zip(yrs, x_["years"], x_["rates"]):
            b.check(s, f"{x_['name']} exceptions {y}", n, f"CALCULATE ( [Exceptions], {f}, 'Date'[Year] = {y} )", 0)
            b.check(s, f"{x_['name']} rate per 1,000 {y}", round(rate, 6),
                    f"CALCULATE ( [Rate per 1,000], {f}, 'Date'[Year] = {y} )", 0.0001)
        b.check(s, f"{x_['name']} exceptions covered by its design finding", x_["n"],
                f"CALCULATE ( [Design Finding Exceptions], {f} )", 0)
        b.check(s, f"{x_['name']} open exceptions (dated after {FIX_BY})", 0, f"CALCULATE ( [Open Exceptions], {f} ) + 0", 0)
    b.check(s, "register rows of Chapter 16's tests", ctx["old"],
            "CALCULATE ( [Exceptions], NOT Tests[TestID] IN { " + ", ".join(f"\"{i}\"" for i in new_ids) + " } )", 0)
    b.check(s, "register rows", ctx["new"], "[Exceptions]", 0)
    b.check(s, "reviewed exceptions (the dispositions of Tutorial 16.3)", sum(1 for e in old if e["disposition"]),
            "[Reviewed Exceptions]", 0)
    b.check(s, "exceptions covered by a design finding", len(new), "[Design Finding Exceptions]", 0)
    b.check(s, "open exceptions", sum(1 for e in old if not e["disposition"]), "[Open Exceptions]", 0)
    b.check(s, "Data Through (stays payroll's last pay date)", ctx["through"], 'FORMAT ( [Data Through], "yyyy-mm-dd" )')
    b.check(s, "last credit memo date", ctx["cm_last"], 'FORMAT ( MAX ( CreditMemo[CreditMemoDate] ), "yyyy-mm-dd" )')
    b.check(s, "last refund date", ctx["rf_last"], 'FORMAT ( MAX ( CustomerRefund[RefundDate] ), "yyyy-mm-dd" )')
    b.check(s, "Change Log rows", len(log), "COUNTROWS ( 'Change Log' )", 0)
    b.check(s, "Design Findings rows", len(rows), "COUNTROWS ( 'Design Findings' )", 0)
    # the anomaly tests (Requirement 4's values, kept outside the register)
    for label, key, n_dax, a_dax in (("method mismatch", "mism", "[Method Mismatch Refunds]", "[Method Mismatch Amount]"),
                                     ("offset missed (past due at least the refund)", "pd2", "[Offset Missed Refunds]",
                                      "[Offset Missed Amount]")):
        v = r4[key]
        b.check(s, f"anomaly {label}: refunds", v["n"], n_dax, 0)
        b.check(s, f"anomaly {label}: amount", v["amt"], a_dax)
        b.check(s, f"anomaly {label}: refunds in {d.C}", v["cur"][0], f"CALCULATE ( {n_dax}, 'Date'[Year] = {d.C} )", 0)
        b.check(s, f"anomaly {label}: amount in {d.C}", v["cur"][1], f"CALCULATE ( {a_dax}, 'Date'[Year] = {d.C} )")
    b.check(s, "refunds with any past-due balance on the refund date", r4["pd1"]["n"], "[Refunds with Past Due]", 0)
    b.check(s, "past-due balances on the refund dates", round(sum(t.pdue.values()), 2), "SUM ( CustomerRefund[PastDue] )", 0.01)
    b.check(s, "anomaly columns are not in the register", 0,
            "COUNTROWS ( FILTER ( Exceptions, CONTAINSSTRING ( Exceptions[TestID], \"Mismatch\" ) || "
            "CONTAINSSTRING ( Exceptions[TestID], \"Offset\" ) ) )", 0)


# --- Milestones 2 and 3 ------------------------------------------------------------------------------------------

def m2(b: Build) -> None:
    ctx = ch19.m2(b.d, claim)
    s = "Milestone 2"
    for label, test, n, amount in (("credits above the approver's limit", "CM AboveLimit", ctx["cm_above"], ctx["cm_above_total"]),
                                   ("credit approver also applied cash to the invoice", "CM CashAndCredit", ctx["cash_credit"], None),
                                   ("refunds above limit", "RF AboveLimit", ctx["rf_above"], ctx["rf_above_total"]),
                                   ("refunds dated before the customer's payment", "RF BeforePayment", ctx["before"],
                                    ctx["before_total"])):
        f = f"Tests[TestID] = \"{test}\""
        b.check(s, label, n, f"CALCULATE ( [Exceptions], {f} )", 0)
        if amount is not None:
            b.check(s, f"{label}: amount", amount, f"CALCULATE ( SUM ( Exceptions[Amount] ), {f} )")


def m3(b: Build) -> None:
    ctx = ch19.m3(b.d, claim)
    s = "Milestone 3"
    for test, n in zip([tid for tid, *_ in NEW_TESTS], ctx["additions"]):
        b.check(s, f"register additions: {test}", n, f"CALCULATE ( [Exceptions], Tests[TestID] = \"{test}\" )", 0)
    mat = ch19.materiality(b.d)
    t = ch19.tests(b.d)
    cur = lambda rows, key: sum(r[key] for r in rows if int(r["date"][:4]) == b.d.C)  # noqa: E731
    page = b.report.page("creditsCycle")
    for v in page.visuals:
        if v.name == "cycleAnswer":
            v.objects["general"][0]["properties"]["paragraphs"].append({"textRuns": [{"value": (
                f"Evaluation (Milestone 3): two significant deficiencies, over credits (authority and segregation in "
                f"customer service) and over refunds (authority, refunds before payment, no preparer recorded); the "
                f"Accounting Manager's concentration a deficiency; no material weakness, because the {b.d.C} exposure of "
                f"each authority finding ({money(cur(t.cm_above, 'gt'))} of credits, {money(cur(t.rf_above, 'amt'))} of "
                f"refunds) is below materiality, {money(mat['mat'])}."), "textStyle": {"fontSize": "10pt"}}]})
    for test, rows, key in (("CM AboveLimit", t.cm_above, "gt"), ("RF AboveLimit", t.rf_above, "amt")):
        b.check(s, f"{test}: {b.d.C} exposure (below materiality, {money(mat['mat'])})", round(cur(rows, key), 2),
                f"CALCULATE ( SUM ( Exceptions[Amount] ), Tests[TestID] = \"{test}\", 'Date'[Year] = {b.d.C} )")
    page.expect = page.expect + [money(cur(t.cm_above, "gt")), money(mat["mat"])]


EXERCISES = [("Requirement 10", r10), ("Milestone 2", m2), ("Milestone 3", m3)]
