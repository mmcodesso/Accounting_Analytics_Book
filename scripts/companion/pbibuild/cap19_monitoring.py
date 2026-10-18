"""Audit Monitoring.pbip with the credits cycle's continuing tests: the Power BI part of the solution to Requirement 10 of
the Chapter 19 capstone case, built on a copy of internal audit's file as Tutorial 16.3 leaves it.

Requirement 10 adds four rule tests to the register (credits above the approver's authority, credits approved by
someone who applied cash to the credited invoice, refunds above authority, and refunds dated before the last application
of the customer's payments to the credited invoice) and the processes Credit memos and Refunds to the populations,
under the change control
Chapter 16 described. The flags are computed in Power Query, as Tutorials 16.1 and 16.2 computed theirs and as the
note describes: for BeforePayment the applications are grouped by invoice for the last ApplicationDate and merged; for
CashAndCredit they are grouped by invoice and applier and merged on the credit's invoice and approver. The two new
exception queries are appended to the Exceptions query's Source step, and the Tests table gains four rows.

The historical exceptions of the new tests that share a supported cause are linked to a finding. A Findings table (Enter
data, one row for each supported cause, credits and refunds) holds the finding, its assessment (design or operation), its
owner, the period it covers (through the end of the audited year), the date its fix is due, and blank fields for the date the
fix is made, the retest date and result and the closure approval, which the supplied case leaves unresolved. A Finding
Exceptions table (Enter data) maps each historical exception, by TestID and DocumentNumber, to its finding, so coverage is a
reviewed mapping and not a date rule: an exception dated within the period but absent from the mapping is open for review.
A mapped exception stays in the register, Open Exceptions leaves the mapped exceptions out, and the review sees every
exception dated after the period or not yet mapped, before the fix as well as after it. A finding is open until the fix is
made, a retest after the fix passes and the closure is approved; a target date reached with no fix leaves it open. The
refund method and the missing offset stay anomaly tests: columns of CustomerRefund, outside the register, on a page of their
own. Data Through takes the last credit and refund dates as well (the date stays payroll's), and a Change Log table (Enter
data) records the change.

Checks: every value of the instructor notes of Requirement 10 and Milestones 2 and 3 that the file shows, computed by
facts/notes/ch19.py (the case's definitions) and facts/notes/ch16.py (the register), and the chain's checks over the
whole register, recomputed for the larger register.
"""

from __future__ import annotations

import re
from collections import Counter

from pbibuild.audit_monitoring import COUNT, MEASURES, MONEY, REGISTER, Build, exceptions, flags
from pbibuild.ex16 import group
from pbibuild.model import Column, Measure, Query, Table, query_table
from pbibuild.pbir import Page, Visual, col, lit, meas, textbox
from pbibuild.reports import card, claim, keep, money

from notes import ch16, ch19  # noqa: E402  (facts/ is on sys.path through pbibuild.audit_monitoring)

M = lambda n: meas(MEASURES, n)           # noqa: E731
NEW_TESTS = [("CM AboveLimit", "Credit above its approver's limit", "Credit memos", "Chapter 19"),
             ("CM CashAndCredit", "Credit approved by someone who applied cash to its invoice", "Credit memos", "Chapter 19"),
             ("RF AboveLimit", "Refund above its approver's limit", "Refunds", "Chapter 19"),
             ("RF BeforePayment", "Refund dated before the last application of the customer's payments to the credited "
              "invoice", "Refunds", "Chapter 19")]
FIX_BY = "2027-12-31"           # the action plans' date (Requirement 9): the delegation of authority and the refund rule
# the findings cover the exceptions dated through the end of the audited year (ch19.year_end(d.C)); a later exception, before
# the fix as well as after it, stays open for review, and a finding closes on a retest, not on FIX_BY
# one row for each cause Requirement 8 supports: (FindingID, the finding, its assessment, the owner by role); the fix date, retest
# date and result and closure approval stay blank in the supplied case
FINDINGS = [("F-CM", "Credits approved above the recorded general limits (effective delegation and enforcement unverified), by "
                     "customer service staff who also apply the cash",
             "Design, provisional: the delegation of authority and the system's enforcement are not in the records",
             "Customer service manager"),
            ("F-RF", "Refunds approved above the recorded general limits (effective delegation and enforcement unverified), and "
                     "dated before the customer's payments were applied to the credited invoice",
             "Design, provisional: the delegation of authority and the refund step's checks are not in the records",
             "Accounting manager")]
FINDING_OF = {"CM": "F-CM", "RF": "F-RF"}          # a test's historical exceptions are mapped to the finding of its process
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
OPEN_FINDINGS = """COUNTROWS (
    FILTER (
        Findings,
        ISBLANK ( Findings[ImplementedDate] )
            || ISBLANK ( Findings[RetestDate] )
            || Findings[RetestResult] <> "Passed"
            || ISBLANK ( Findings[ClosureApprovedDate] )
    )
)"""
FINDING_STATUS = """VAR FixMade = MAX ( Findings[ImplementedDate] )
VAR RetestMade = MAX ( Findings[RetestDate] )
VAR Outcome = SELECTEDVALUE ( Findings[RetestResult] )
VAR ApprovedOn = MAX ( Findings[ClosureApprovedDate] )
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( FixMade ), "Open: fix not yet made",
        ISBLANK ( RetestMade ), "Open: fix not yet retested",
        Outcome <> "Passed", "Open: retest not passed",
        ISBLANK ( ApprovedOn ), "Open: closure not yet approved",
        "Closed"
    )"""


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
    covers = ch19.year_end(d.C)
    rows = [[fid, text, assess, owner, covers, FIX_BY, None, None, None, None] for fid, text, assess, owner in FINDINGS]
    m.add(Table("Findings", [Column("FindingID", "string"), Column("Finding", "string"), Column("Assessment", "string"),
                             Column("Owner", "string"), Column("CoversThrough", "dateTime", fmt="Short Date"),
                             Column("TargetDate", "dateTime", fmt="Short Date"),
                             Column("ImplementedDate", "dateTime", fmt="Short Date"),
                             Column("RetestDate", "dateTime", fmt="Short Date"), Column("RetestResult", "string"),
                             Column("ClosureApprovedDate", "dateTime", fmt="Short Date")], entered=rows))
    m.query_order.append("Findings")
    mapped = [[x["test"], x["doc"], FINDING_OF[x["test"][:2]], CHANGE_DATE] for x in new_register(d)]
    m.add(Table("Finding Exceptions", [Column("TestID", "string"), Column("DocumentNumber", "string"),
                                       Column("FindingID", "string"), Column("MappedOn", "dateTime", fmt="Short Date")],
                entered=mapped, hidden=True))
    m.query_order.append("Finding Exceptions")
    mq = Query("Finding Exceptions")
    mq.columns = {"TestID": "type text", "DocumentNumber": "type text", "FindingID": "type text", "MappedOn": "type date"}
    reg.merge(mq, ["TestID", "DocumentNumber"], ["TestID", "DocumentNumber"], ["FindingID"])
    reg.custom("Covered", "if [FindingID] <> null then 1 else 0", "Int64.Type")
    m.tables["Exceptions"] = query_table(reg, formats={"Amount": MONEY},
                                         summarize={"EmployeeID": "none", "Covered": "none", "FindingID": "none"})
    m.relate("Exceptions.FindingID", "Findings.FindingID")
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
                "Exceptions mapped to a finding: reported once, as the finding, and kept in the register. Coverage is "
                "not remediation.")
    add_measure(b, "Open Findings", OPEN_FINDINGS, COUNT,
                "Findings not yet closed: closure needs the fix made, a passed retest after it and the closure approved. "
                "A target date reached with no fix leaves a finding open.")
    add_measure(b, "Closed Findings", "COUNTROWS ( Findings ) - [Open Findings]", COUNT,
                "Findings whose fix was made, retested successfully and approved for closure.")
    add_measure(b, "Finding Status", FINDING_STATUS, None,
                "The first step a finding has not yet met: the fix, the retest, a passed result, the closure approval.")
    add_measure(b, "Mapped After Period", "COUNTROWS ( FILTER ( Exceptions, Exceptions[Covered] = 1 && "
                "Exceptions[EventDate] > RELATED ( Findings[CoversThrough] ) ) )", COUNT,
                "Mapped exceptions dated after the period their finding covers: expected none, since later exceptions "
                "stay open for review until they are reviewed and mapped.")
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
           [CHANGE_DATE, "Findings, Finding Exceptions and Open Exceptions",
            f"Two findings (credits, refunds) with owner, assessment, period and due date, and the {len(mapped)} historical "
            f"exceptions dated through {covers} mapped to them; Open Exceptions leaves the mapped ones out and Open "
            f"Findings counts the findings not closed",
            "Report the historical exceptions once; review every later or unmapped one, and close a finding only after "
            "the fix, a passed retest and approval"],
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
        "// Test 6: the register keeps one row per test and document, the findings cover the new tests' past, and no finding is closed\n"
        "EVALUATE\nROW (\n    \"Rows\", COUNTROWS ( Exceptions ),\n"
        "    \"Test and document pairs\", COUNTROWS ( SUMMARIZE ( Exceptions, Exceptions[TestID], Exceptions[DocumentNumber] ) ),\n"
        "    \"Reviewed\", [Reviewed Exceptions],\n    \"Mapped to a finding\", [Design Finding Exceptions],\n"
        "    \"Open\", [Open Exceptions],\n    \"Open findings\", [Open Findings]\n)")
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
                 ("Tutorial 16.3", "the documents failing two tests or more"), ("Tutorial 16.3", "Test 3: exception keys")}
    recompute |= {("Tutorial 16.2", f"{mn[:3]} exceptions (all years)") for mn in ch16.MONTHS}
    recompute |= {("Tutorial 16.2", f"exceptions approved by {names[e]}") for e, _ in Counter(x["emp"] for x in old).most_common(5)}
    before = len(b.project.checks)
    b.project.checks = [(sec, ch) for sec, ch in b.project.checks if (sec, ch.label) not in recompute]
    claim(before - len(b.project.checks) == len(recompute), "the chain's checks over the whole register were found")
    s2 = "Requirement 10 (Chapter 16's checks, on the larger register)"
    b.check(s2, "Exceptions rows", len(full), "COUNTROWS ( Exceptions )", 0)
    b.check(s2, "test and document pairs (each unique)", len({(e["test"], e["doc"]) for e in full}),
            "COUNTROWS ( SUMMARIZE ( Exceptions, Exceptions[TestID], Exceptions[DocumentNumber] ) )", 0)
    b.check(s2, "Test 3: exception keys", len({(e["test"], e["doc"]) for e in full}),
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
    claim({"source": "approvers", "target": "rates", "type": "NoFilter"} in mon.extra.get("visualInteractions", []),
          "the approvers chart does not filter the rates table, so a rate's numerator and population share one context")
    end = re.search(r"CALENDAR \( DATE \( \d+, 1, 1 \), DATE \( (\d+), 12, 31 \) \)", m.tables["Date"].dax or "")
    claim(end is not None, "the Date table is Tutorial 16.1's CALENDAR")
    date_end = f"{end.group(1)}-12-31"
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
    page = b.report.add(Page("creditsCycle", "Credits Cycle", height=1060, display_option="FitToWidth"))
    test_col, year_col = col("Tests", "TestID"), col("Date", "Year")
    new_ids = [tid for tid, *_ in NEW_TESTS]
    page.add(Visual("newTests", "pivotTable", 20, 20, 1240, 200, {
        "Rows": [test_col], "Columns": [year_col], "Values": [M("Exceptions"), M("Population"), M("Rate per 1,000")]},
        title="The credits cycle's tests by year", filters=[keep("newTestIds", test_col, new_ids)]))
    page.add(card("registerCards", 20, 235, 1240, 110, [M("Exceptions"), M("Reviewed Exceptions"),
                                                        M("Design Finding Exceptions"), M("Open Exceptions"),
                                                        M("Open Findings")]))
    page.add(Visual("findings", "tableEx", 20, 360, 1240, 260, {"Values": [
        col("Findings", "FindingID"), col("Findings", "Finding"), col("Findings", "Assessment"), col("Findings", "Owner"),
        col("Findings", "CoversThrough"), col("Findings", "TargetDate"), M("Finding Status"),
        M("Design Finding Exceptions")]},
        title="Findings: each supported cause once; later and unmapped exceptions stay open for review",
        objects={"columnWidth": [{"properties": {"value": lit(w)}, "selector": {"metadata": f"Findings.{k}"}}
                                 for k, w in (("Finding", 360), ("Assessment", 240), ("Owner", 140))],
                 "values": [{"properties": {"wordWrap": lit(True)}}]}))      # each long text wraps in its column
    tests_ = {x_["name"]: x_ for x_ in ctx["tests"]}
    page.add(answer("cycleAnswer", 20, 635, 1240, 400, "the continuing tests", [
        "Four rule tests join the register: " + "; ".join(
            f"{x_['name']} {x_['n']} ({' / '.join(str(v) for v in x_['years'])}; per 1,000 "
            f"{' / '.join(f'{v:.1f}' for v in x_['rates'])}, {x_['rate']:.1f} over the three years)" for x_ in ctx["tests"]) +
        f". Populations: credits {' / '.join(str(v) for v in ctx['pop_c'])}, refunds {' / '.join(str(v) for v in ctx['pop_r'])}. "
        f"The register grows from {ctx['old']} to {ctx['new']} rows, and each test and document pair is still unique.",
        f"Findings: the {len(new)} historical exceptions of the new tests share the causes Requirement 8 supports, so each "
        "is mapped to one of two findings, credits or refunds (approvals above the recorded general limits, with the "
        "effective delegation and its enforcement unverified), and stays in the register with its document. A Findings row "
        "holds the assessment, the owner, the period covered and the due date, with the fix date, retest and closure "
        "approval blank. The findings record Requirement 8's provisional evaluation, which looked past the register to the "
        "records behind it, as Tutorial 16.3 assumed for its dispositions. The flags alone would support only a follow-up. "
        f"The findings cover the exceptions dated through {covers} and are to be fixed by "
        f"{FIX_BY}; Open Exceptions leaves the mapped ones out and stays at {sum(1 for e in old if not e['disposition'])}, "
        "so the new tests do not flood the review, while any later or unmapped exception stays open for review. Both "
        "findings are open: a finding closes only when the fix is made, a retest after it passes and the closure is "
        "approved, never on its planned date, and coverage is not remediation. BeforePayment is a retrospective timing "
        "screen: it flags a refund only after an application dated later is recorded, so it does not show that a refund "
        "was supported when approved and can miss an unpaid invoice with no later application; a separate as-of "
        "supported-balance test addresses that. After remediation all four rule tests remain subject to retest and "
        f"monitoring. The Date table ends {date_end}: extend it before exceptions after that date arrive.",
        f"Data Through stays {ctx['through']}, set by payroll's last pay date (the rest of December's work belongs to the "
        f"two pay periods marked Open, scheduled to pay in January {d.C + 1}). It is the earliest of the processes' last "
        "dates, which bounds what the tests can have seen but does not show that every record through it was loaded. The "
        f"credits run to {ctx['cm_last']} and the refunds to {ctx['rf_last']}. The refund method and the missing offset stay anomaly tests, outside the register "
        "(the Anomalies page), because they are reasons to look rather than rule failures. The Change Log page records "
        "the change, and Tests 5 and 6 in the Tests tab are rerun with Tests 1 to 4 before the file is used."]))
    cmab = tests_["CM AboveLimit"]
    page.expect = ["CM AboveLimit", "RF BeforePayment", f"{cmab['rates'][-1]:.1f}", f"{cmab['n']:,}",
                   f"Design Finding Exceptions, {len(new)} card", f"Open Findings, {len(FINDINGS)} card",
                   "Model answer: the continuing tests", FIX_BY[:4]]

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
        "of them a balance at least as large as the refund. The records hold no policy that requires an offset or the "
        "original payment method, so these stay anomalies to follow up; once a policy sets the rule, it joins the "
        "register. The method test reads every receipt applied to the invoice, later ones included: "
        f"{r4['late']['n']} refunds ({money(r4['late']['amt'])}) match only on receipts dated after the refund."]))
    page.expect = ["Method Mismatch Refunds", "Offset Missed Refunds", money(r4["mism"]["cur"][1]), money(r4["pd2"]["cur"][1])]

    # the Change Log page
    page = b.report.add(Page("changeLog", "Change Log"))
    page.add(Visual("log", "tableEx", 20, 20, 1240, 400, {"Values": [
        col("Change Log", k) for k in ("Date", "Object", "Change", "Reason")]}, title="Changes to this file",
        objects={"columnWidth": [{"properties": {"value": lit(w)}, "selector": {"metadata": f"Change Log.{k}"}}
                                 for k, w in (("Change", 470), ("Reason", 420))],
                 "values": [{"properties": {"wordWrap": lit(True)}}]}))     # the long texts wrap in their columns
    page.add(answer("logAnswer", 20, 440, 1240, 200, "the change under change control", [
        "The change was made in the Power BI project under version control, on its own branch, and the reviewer approves "
        "it from the list of changed lines before it is merged: the queries CreditMemo, CustomerRefund, CM Exceptions, "
        "RF Exceptions and their inputs, the Exceptions query's Source step and its Finding Exceptions merge, the Tests, "
        "Findings, Finding Exceptions, and Change Log tables, and the measures Population, Open Exceptions, Open Findings, "
        "and Data Through.",
        "Tests 1 to 6 are rerun before the file is used: Test 2 now lists fifteen tests, Test 5 the new tests by year, "
        "and Test 6 the register's rows, reviewed, mapped, and open exceptions and the open findings. No copy of the .pbix "
        "leaves internal audit."]))
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
        b.check(s, f"{x_['name']} exceptions mapped to its finding", x_["n"],
                f"CALCULATE ( [Design Finding Exceptions], {f} )", 0)
        b.check(s, f"{x_['name']} open exceptions (none is dated after {covers})", 0,
                f"CALCULATE ( [Open Exceptions], {f} ) + 0", 0)
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
    b.check(s, "Findings rows (one for each supported cause)", len(rows), "COUNTROWS ( Findings )", 0)
    b.check(s, "Finding Exceptions rows (one for each historical exception)", len(mapped), "COUNTROWS ( 'Finding Exceptions' )", 0)
    b.check(s, "open findings (nothing is fixed, retested or approved in the supplied case)", len(rows), "[Open Findings]", 0)
    b.check(s, "closed findings", 0, "[Closed Findings] + 0", 0)
    b.check(s, "status of the first finding", "Open: fix not yet made",
            f"CALCULATE ( [Finding Status], Findings[FindingID] = \"{FINDINGS[0][0]}\" )")
    b.check(s, "mapped exceptions dated after the period their finding covers", 0, "[Mapped After Period] + 0", 0)
    for fid, *_ in FINDINGS:
        b.check(s, f"exceptions mapped to {fid}", sum(1 for x in mapped if x[2] == fid),
                f"CALCULATE ( [Design Finding Exceptions], Findings[FindingID] = \"{fid}\" )", 0)
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
                f"Evaluation (Milestone 3), provisional: two significant deficiencies, over credits (authority and "
                f"segregation in customer service) and over refunds (authority, refunds before payment, no preparer "
                f"recorded); the Accounting Manager's concentration a deficiency; no material weakness identified on the "
                f"records. The {b.d.C} exposure of each authority finding ({money(cur(t.cm_above, 'gt'))} of credits, "
                f"{money(cur(t.rf_above, 'amt'))} of refunds) is below materiality, {money(mat['mat'])}, but the year's "
                f"credits ({money(cur(list(ch19.cycle(b.d).cm.values()), 'gt'))}) are above it, so the rating rests on "
                f"compensating controls whose records lie outside the database."), "textStyle": {"fontSize": "10pt"}}]})
    for test, rows, key in (("CM AboveLimit", t.cm_above, "gt"), ("RF AboveLimit", t.rf_above, "amt")):
        b.check(s, f"{test}: {b.d.C} exposure (below materiality, {money(mat['mat'])})", round(cur(rows, key), 2),
                f"CALCULATE ( SUM ( Exceptions[Amount] ), Tests[TestID] = \"{test}\", 'Date'[Year] = {b.d.C} )")
    page.expect = page.expect + [money(cur(t.cm_above, "gt")), money(mat["mat"])]


EXERCISES = [("Requirement 10", r10), ("Milestone 2", m2), ("Milestone 3", m3)]
