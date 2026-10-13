"""Chapter 12's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 12 applies SQL to the work of an internal auditor (populations, expectations, exceptions), so the guides do
three jobs, as Chapters 9 to 11 did:

- they supply the values the tutorials' checkpoints show (the library tests L1 to L8, P1 to P6 and H1 to H10), which
  no registered note covers,
- they supply what each exercise's steps need beyond its registered note (ch12.ex1 to ch12.ex6): above all the result
  of each wrong variant a guide names (a test that cannot fail, a join that repeats rows, a boundary written with the
  wrong operator, a ratio built on integers), run read-only, so the symptom a guide describes is the symptom the data
  gives,
- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll flags the wording instead of leaving it stale.

Keys: ch12.chapter (the chapter note and its three tutorials) and ch12.g1 to ch12.g6 (the exercises; each is used next
to the registered note ch12.ex1 to ch12.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter12-exercises-sql (Ex 12.1.sql to Ex 12.6.sql). A query of
a model script is run here from the script itself, and a variant is that text with one change, so the symptom a guide
names is the symptom of the very query it quotes. The tutorials' tests are read from the chapter's text.
"""

from __future__ import annotations

import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list, rows

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "12-sql-audit-analytics"
DECK = REPO / "slides" / "chapter-12" / "index.qmd"
SOLUTIONS = REPO / "outputs" / "companion" / "solutions" / "Chapter12-exercises-sql"

SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "SubTotal", "GrandTotal", "CustomerID"],
    "SalesInvoiceLine": ["SalesInvoiceID", "ShipmentLineID"],
    "ShipmentLine": ["ShipmentLineID", "ShipmentID", "QuantityShipped", "ExtendedStandardCost", "SalesOrderLineID", "ItemID"],
    "Shipment": ["ShipmentID", "ShipmentDate", "DeliveryDate"],
    "SalesOrderLine": ["SalesOrderLineID", "UnitPrice", "Discount"],
    "GLEntry": ["SourceDocumentType", "SourceDocumentID", "PostingDate", "AccountID", "Debit", "Credit"],
    "CashReceiptApplication": ["SalesInvoiceID", "AppliedAmount", "ApplicationDate"],
    "CreditMemo": ["OriginalSalesInvoiceID", "GrandTotal", "CreditMemoDate"],
    "CustomerRefund": ["CreditMemoID", "RefundDate"],
    "PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "ReceivedDate", "SupplierID", "GrandTotal"],
    "PurchaseInvoiceLine": ["PurchaseInvoiceID", "POLineID", "GoodsReceiptLineID", "Quantity", "UnitCost",
                            "AccrualJournalEntryID"],
    "GoodsReceipt": ["GoodsReceiptID", "ReceiptNumber", "ReceiptDate", "PurchaseOrderID"],
    "GoodsReceiptLine": ["GoodsReceiptLineID", "GoodsReceiptID", "POLineID", "QuantityReceived", "ExtendedStandardCost"],
    "PurchaseOrder": ["PurchaseOrderID", "PONumber", "OrderDate", "OrderTotal", "CreatedByEmployeeID",
                      "ApprovedByEmployeeID", "SupplierID"],
    "PurchaseOrderLine": ["POLineID", "Quantity", "UnitCost"],
    "DisbursementPayment": ["DisbursementID", "PaymentNumber", "SupplierID", "PurchaseInvoiceID", "Amount", "PaymentDate",
                            "CheckNumber", "PaymentMethod"],
    "PayrollPeriod": ["PayrollPeriodID", "PeriodNumber", "PeriodStartDate", "PeriodEndDate", "PayDate", "Status",
                      "FiscalYear"],
    "PayrollRegister": ["PayrollRegisterID", "PayrollPeriodID", "EmployeeID", "CostCenterID", "GrossPay", "NetPay",
                        "EmployerPayrollTax", "EmployerBenefits", "ApprovedByEmployeeID", "ApprovedDate"],
    "PayrollRegisterLine": ["PayrollRegisterID", "LineType", "Hours", "Amount", "LaborTimeEntryID"],
    "PayrollPayment": ["PayrollPaymentID", "PayrollRegisterID", "PaymentDate"],
    "LaborTimeEntry": ["LaborTimeEntryID", "EmployeeID", "WorkDate", "LaborType", "RegularHours", "OvertimeHours",
                       "ExtendedLaborCost", "PayrollPeriodID", "WorkOrderOperationID", "TimeClockEntryID"],
    "TimeClockEntry": ["TimeClockEntryID", "EmployeeID", "WorkDate", "ClockStatus", "ClockOutTime", "RegularHours",
                       "OvertimeHours", "OvertimeApprovalID", "PayrollPeriodID"],
    "OvertimeApproval": ["OvertimeApprovalID", "EmployeeID", "WorkDate", "ReasonCode", "RequestedHours", "ApprovedHours",
                         "ApprovedDate", "ApprovedByEmployeeID"],
    "WorkOrderOperation": ["WorkOrderOperationID", "WorkCenterID", "PlannedLoadHours", "ActualStartDate", "ActualEndDate"],
    "WorkOrder": ["ReleasedDate"],
    "WorkCenter": ["WorkCenterID", "WorkCenterName"],
    "WorkCenterCalendar": ["WorkCenterID", "CalendarDate", "IsWorkingDay"],
    "ProductionCompletion": ["ProductionCompletionID", "CompletionDate"],
    "ProductionCompletionLine": ["ProductionCompletionID", "QuantityCompleted"],
    "Item": ["ItemID", "SupplyMode"],
    "Employee": ["EmployeeID", "JobTitle", "CostCenterID", "TerminationDate", "MaxApprovalAmount", "BaseHourlyRate"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
    "Customer": ["CustomerID", "CustomerName"],
    "CashReceipt": ["ReceiptNumber"],
    "JournalEntry": ["EntryNumber", "TotalAmount"],
    "Account": ["AccountID", "AccountNumber"],
}


# --- helpers ---------------------------------------------------------------------------------------------------------

def need(d, claim, *tables: str) -> None:
    """Claims that each table and the columns the guides name are in the database."""
    schema(d, claim, {t: SCHEMA[t] for t in (tables or SCHEMA)})


def script_sql(file: str, tag: str) -> str:
    """The statement of one model query (its comment lines and its result comment left out), from the solution script."""
    text = (SOLUTIONS / file).read_text(encoding="utf-8")
    m = re.search(rf"(?m)^-- Exercise 12\.\d, test {tag}:.*\n-- Population:.*\n", text)
    if m is None:
        raise KeyError(f"no test {tag} in {file}")
    rest = text[m.end():]
    return rest[:re.search(r";(  -- Result:[^\n]*)?\n", rest).start()]


def tutorial_sql(tag: str) -> str:
    """The statement of one library test of the tutorials (L1 to L8, P1 to P6, H1 to H10), from the chapter's text."""
    for name in ("_tutorial-01.qmd", "_tutorial-02.qmd", "_tutorial-03.qmd"):
        for m in re.finditer(r"```sql\n(.*?)```", (CHAPTER / name).read_text(encoding="utf-8"), re.S):
            body = "\n".join(l[3:] if l.startswith("   ") else l for l in m.group(1).split("\n")).strip()
            if re.match(rf"-- Tutorial 12\.\d, test {tag}:", body):
                return "\n".join(body.rstrip(";").split("\n")[2:])
    raise KeyError(f"no test {tag} in the tutorials")


def sub(sql: str, old: str, new: str, count: int = 1) -> str:
    """The statement with `old` replaced by `new`, ignoring differences in whitespace; the text must be there."""
    pattern = r"\s+".join(re.escape(w) for w in old.split())
    if not re.search(pattern, sql):
        raise ValueError(f"the text to change is not in the statement: {old[:60]}")
    return re.sub(pattern, lambda m: new, sql, count=count)


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


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import package
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/12-sql-audit-analytics/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 12\b")
    letters, _ = package.answer_key(comment)
    key = {i: a for i, a in enumerate(letters, 1)}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def window(d) -> dict:
    return dict(f=d.F, p=d.P, y=d.C, n=d.N, asof=f"{d.C}-12-31")


def run(d, sql: str) -> list:
    return d.q(sql)


def r2(x) -> float:
    return round(float(x), 2)


def first_row(d, sql: str):
    return d.q(sql)[0]


# --- the chapter note and its three tutorials --------------------------------------------------------------------------

def tutorial_121(d, claim) -> dict:
    l1 = first_row(d, tutorial_sql("L1"))
    claim(l1[0] == l1[2] and abs(l1[1] - l1[3]) < 0.005, "test L1: the journal entries and the ledger agree in count and total")
    l2 = run(d, tutorial_sql("L2"))
    claim(all(abs(r[3]) < 0.005 for r in l2), "test L2: the manufacturing payroll agrees with the ledger to the cent in every year")
    l3_sql = tutorial_sql("L3")
    l3 = run(d, l3_sql)
    claim({r[0] for r in l3} == {"Posting with no payroll payment"}, "test L3: every exception is a posting with no payroll payment")
    # a column swapped in a query that returns no rows changes nothing in the result
    swapped = sub(l3_sql, "SELECT 'Posting with no supplier payment', gl.GLEntryID, gl.PostingDate, gl.Debit + gl.Credit",
                  "SELECT 'Posting with no supplier payment', gl.PostingDate, gl.GLEntryID, gl.Debit + gl.Credit")
    claim(run(d, swapped) == l3, "swapping two columns of the second query of test L3 changes nothing, because that query returns no rows")
    l4_sql = tutorial_sql("L4")
    l4 = run(d, l4_sql)
    l4_inner = run(d, sub(l4_sql, "LEFT JOIN PayrollPayment AS pay", "INNER JOIN PayrollPayment AS pay"))
    claim(len(l4) == 3 and not l4_inner, "test L4 returns three registers, and written with an inner join it returns none")
    l5_sql = tutorial_sql("L5")
    l5 = run(d, l5_sql)
    reorder = sub(l5_sql, """CASE WHEN strftime('%Y', p.PostingDate) <> strftime('%Y', sh.DeliveryDate) THEN 'Revenue posted in another year'
        WHEN si.InvoiceDate < sh.ShipmentDate THEN 'Invoice dated before shipment'""",
                  """CASE WHEN si.InvoiceDate < sh.ShipmentDate THEN 'Invoice dated before shipment'
        WHEN strftime('%Y', p.PostingDate) <> strftime('%Y', sh.DeliveryDate) THEN 'Revenue posted in another year'""")
    l5_reorder = run(d, reorder)
    fan = sub(sub(l5_sql, "SELECT sil.SalesInvoiceID, MIN(s.ShipmentDate) AS ShipmentDate, MAX(s.DeliveryDate) AS DeliveryDate",
                  "SELECT sil.SalesInvoiceID, s.ShipmentDate AS ShipmentDate, s.DeliveryDate AS DeliveryDate"),
              "GROUP BY sil.SalesInvoiceID ), Posted", "), Posted")
    l5_fan = run(d, fan)
    other = [r for r in l5 if r[0] == "Revenue posted in another year"]
    before = [r for r in l5 if r[0] == "Invoice dated before shipment"]
    claim(len(other) == 2 and len(before) == 3, "test L5 has two rows of revenue posted in another year and three of invoices dated before shipment")
    other_re = [r for r in l5_reorder if r[0] == "Revenue posted in another year"]
    claim(sum(r[2] for r in other_re) == sum(r[2] for r in other) - 1,
          "putting the dating branch first moves one invoice, the ninth, from the posting finding to the dating finding")
    other_fan = [r for r in l5_fan if r[0] == "Revenue posted in another year"]
    claim(sum(r[2] for r in other_fan) > sum(r[2] for r in other), "without the grouping, an invoice with two shipments is counted twice")
    l6_sql = tutorial_sql("L6")
    l6 = run(d, l6_sql)
    l6_inner = run(d, sub(l6_sql, "LEFT JOIN SalesInvoiceLine AS sil", "INNER JOIN SalesInvoiceLine AS sil"))
    claim(len(l6) > 0 and not l6_inner, "test L6 finds the shipment lines never invoiced, and written with an inner join finds none")
    l7_sql = tutorial_sql("L7")
    l7 = run(d, l7_sql)
    l7_inner = run(d, sub(l7_sql, "LEFT JOIN (", "INNER JOIN ("))
    open_periods = [r for r in l7 if r[4] == "Open"]
    claim(len(open_periods) == 2 and len(l7_inner) == len(l7) - 2 and all(r[5] == 0 for r in open_periods),
          "test L7 lists two open periods with no registers, and an inner join to the registers drops them")
    l8 = run(d, tutorial_sql("L8"))
    jes = [r for r in l8 if r[0] == "JournalEntry"]
    others = [r for r in l8 if r[0] != "JournalEntry"]
    claim(len(jes) == 1 and abs(sum(r[2] for r in others)) < 0.005, "test L8: only the opening journal entry line stays in account 2030; the payroll postings net to zero")
    return dict(
        entries=l1[0], entry_total=l1[1], posted=l1[2], l2=l2, n_l3=len(l3), l3_swapped=len(run(d, swapped)),
        n_l4=len(l4), l4=l4, l4_inner=len(l4_inner),
        l5=l5, l5_other=other, l5_before=before, n_before_rows=len(before),
        re_other_2025=[r for r in other_re if r[1] == str(d.P)][0][2], re_before_2025=[r for r in l5_reorder if r[0] == "Invoice dated before shipment" and r[1] == str(d.P)][0][2],
        n_other=sum(r[2] for r in other), n_before=sum(r[2] for r in before), fan_other=sum(r[2] for r in other_fan),
        n_l6=len(l6), l6_inner=len(l6_inner), n_l7=len(l7), l7_inner=len(l7_inner), open_status=len(open_periods),
        l8=l8, opening=jes[0][2])


def tutorial_122(d, claim) -> dict:
    p1_sql = tutorial_sql("P1")
    p1 = run(d, p1_sql)
    names = {r[0]: r[1] for r in p1}
    claim(not any(n.startswith("Exception") for n in names), "test P1: no line is invoiced above received or received above ordered")
    p2 = first_row(d, tutorial_sql("P2"))
    claim(p2[1] == 0 and p2[2] > 0 and p2[3] > 0 > p2[4], "test P2: none above three percent, many above two, all increases above two")
    p2_nopos = first_row(d, sub(tutorial_sql("P2"), "ABS(pil.UnitCost - pol.UnitCost) / pol.UnitCost > 0.02", "(pil.UnitCost - pol.UnitCost) / pol.UnitCost > 0.02"))
    claim(p2_nopos[2] == p2[2], "a price test without ABS finds the same lines above two percent, because every one of them is an increase")
    p3 = first_row(d, tutorial_sql("P3"))
    p3_full = first_row(d, sub(tutorial_sql("P3"), "SUM(grl.ExtendedStandardCost * (1 - COALESCE(ibr.QtyInvoiced, 0) / grl.QuantityReceived))",
                               "SUM(grl.ExtendedStandardCost)"))
    claim(abs(p3[0] - p3[1]) < 1 and p3_full[0] > p3[0], "test P3: the open receipts agree with the ledger within a dollar, and the full value of the open lines does not")
    p4 = run(d, tutorial_sql("P4"))
    claim(len(p4) == 3 and min(r[1] for r in p4) >= 3, "test P4: three approval tests with a few orders each")
    p5 = run(d, tutorial_sql("P5"))
    claim(sum(r[1] for r in p4) > len(p5), "test P5: some orders fail more than one test, so the exception rows outnumber the orders")
    p6_sql = tutorial_sql("P6")
    p6 = run(d, p6_sql)
    by_title = rows(d, sub(sub(p6_sql, "SELECT e.EmployeeID, e.JobTitle, COUNT(*) AS OrdersApproved", "SELECT e.JobTitle, COUNT(*) AS OrdersApproved"),
                           "GROUP BY e.EmployeeID, e.JobTitle", "GROUP BY e.JobTitle"))
    claim(by_title < len(p6), "grouping the approvers by job title merges employees who share a title")
    total_orders = d.one("SELECT COUNT(*) FROM PurchaseOrder")
    claim(p6[0][2] / total_orders > 0.99, "one approver signs more than 99 percent of the purchase orders")
    # the row-by-row comparison of one receipt line with one invoice line (the question 6 distractor's symptom)
    direct = d.q("SELECT COUNT(*), SUM(CASE WHEN ABS(grl.QuantityReceived - pil.Quantity) > 0.0001 THEN 1 ELSE 0 END) "
                 "FROM GoodsReceiptLine AS grl INNER JOIN PurchaseInvoiceLine AS pil ON pil.GoodsReceiptLineID = grl.GoodsReceiptLineID")[0]
    claim(direct[1] > 1000, "compared row by row, thousands of receipt and invoice lines disagree")
    return dict(p1=p1, statuses=len(p1), p2=p2, p3=p3, p3_full=p3_full[0], p4=p4, p5_orders=len(p5), p5_rows=sum(r[1] for r in p4),
                p6=p6, p6_by_title=by_title, approvers=len(p6), top_share=p6[0][2] / total_orders, direct_rows=direct[0], direct_off=direct[1])


def tutorial_123(d, claim) -> dict:
    h1 = first_row(d, tutorial_sql("H1"))
    h2_sql = tutorial_sql("H2")
    h2 = first_row(d, h2_sql)
    h2_exact = first_row(d, sub(h2_sql, "ABS(c.Hours - r.Hours) > 0.001 OR ABS(r.Hours - p.Hours) > 0.001", "c.Hours <> r.Hours OR r.Hours <> p.Hours"))
    claim(h2[1] == 0 and h2_exact[1] > 0, "test H2: the three records agree in every period within a tolerance, and an exact comparison of REAL sums flags periods anyway")
    h3 = run(d, tutorial_sql("H3"))
    h3_low = [r[4] for r in h3 if r[4] < 0.1 * r[2]]
    claim(len(h3_low) >= 4, "test H3: several pay periods of the first year hold almost no indirect time")
    quiet = [r for r in h3 if f"{d.F}-02-01" <= r[1] <= f"{d.F}-05-31"]
    claim(len(quiet) >= 6 and max(r[4] for r in quiet) < 0.05 * min(r[2] for r in quiet) and min(r[3] for r in quiet) > 2000,
          "test H3: in the pay periods starting February to May, indirect time is almost absent and direct time is a normal period's hours")
    h4 = run(d, tutorial_sql("H4"))
    other = [r for r in h4 if r[0] == "Time paid to another employee"]
    unapproved = [r for r in h4 if r[0] != "Time paid to another employee"]
    h5_sql = tutorial_sql("H5")
    h5 = run(d, h5_sql)
    claim(all(r[4] == 0 for r in h5), "test H5: no earnings line differs from its expectation by more than a cent")
    h5_no = run(d, sub(h5_sql, "* CASE prl.LineType WHEN 'Overtime Earnings' THEN 1.5 ELSE 1 END AS ExpectedAmount", "AS ExpectedAmount"))
    ot_lines = [r[1] for r in d.q("SELECT pp.FiscalYear, COUNT(*) FROM PayrollRegisterLine prl JOIN PayrollRegister pr ON pr.PayrollRegisterID = prl.PayrollRegisterID "
                                  "JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID WHERE prl.LineType = 'Overtime Earnings' GROUP BY pp.FiscalYear ORDER BY 1")]
    claim([a[4] for a in h5_no] == ot_lines, "an expectation without the overtime premium flags exactly the overtime lines, one for each")
    h6_sql = tutorial_sql("H6")
    h6 = run(d, h6_sql)
    h6_lt = run(d, sub(h6_sql, "WHEN OvertimeHours <= 0.5", "WHEN OvertimeHours < 0.5"))
    short, long_ = h6[0], h6[1]
    claim(short[0].startswith("Half") and short[1] == short[2] and long_[2] < 5, "test H6: no short overtime entry has an approval, and only a handful of the longer ones lack one")
    long_lt = [r for r in h6_lt if r[0].startswith("More")][0]
    claim(long_lt[2] > long_[2], "writing the threshold as < moves the entries of exactly half an hour into the longer group, where they have no approval")
    h7 = run(d, tutorial_sql("H7"))
    h8_sql = tutorial_sql("H8")
    h8 = run(d, h8_sql)
    h8_reg = run(d, sub(h8_sql, "COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) AS HourPatterns", "COUNT(DISTINCT tc.RegularHours) AS HourPatterns"))
    claim(sum(r[1] for r in h8_reg) > sum(r[1] for r in h8), "comparing regular hours alone finds more surge days than comparing the hours worked")
    h8_guard = run(d, sub(h8_sql, "HourPatterns = 1 AND Employees > 1", "HourPatterns = 1"))
    claim(sum(r[1] for r in h8_guard) == sum(r[1] for r in h8), "the guard of more than one employee changes no count on this data")
    claim(all(r[2] == h8[0][2] for r in h8) and h8[0][2] > 50, "test H8: the same number of employees, all of them, on every surge day")
    h9_sql = tutorial_sql("H9")
    h9 = run(d, h9_sql)
    h9_inner = run(d, sub(h9_sql, "LEFT JOIN SurgeDays AS sd", "INNER JOIN SurgeDays AS sd"))
    claim(all(a[3] > b[3] for a, b in zip(h9_inner, h9)), "joining the surge days with an inner join keeps only their hours and raises every share")
    h9_ge = run(d, h9_sql.replace("lt.WorkDate > op.ActualEndDate", "lt.WorkDate >= op.ActualEndDate"))
    claim(all(abs(r[3] - 1.0) < 1e-9 for r in h9_ge), "written >=, every direct entry counts as late, because no entry is dated before its operation's end")
    h10 = run(d, tutorial_sql("H10"))
    claim(h10[0][0].startswith("Packing") and h10[0][2] > 0.9, "test H10: nearly all of Packing's direct time of the last year was recorded after the operation ended")
    return dict(
        h1=h1, h2=h2, h2_exact=h2_exact[1], n_h3=len(h3), h3_low=len(h3_low), quiet_n=len(quiet), quiet_max=max(r[4] for r in quiet), quiet_min_direct=min(r[3] for r in quiet),
        first_indirect=h3[0][4], first_direct=h3[0][3], n_h4=len(h4), n_other=len(other), n_unapproved=len(unapproved),
        h5=h5, h5_no=[r[4] for r in h5_no], h6=h6, h6_lt=long_lt[2], n_h7=len(h7), h8=h8,
        h8_days=sum(r[1] for r in h8), h8_reg_days=sum(r[1] for r in h8_reg), h9=h9, h9_inner=h9_inner, h10=h10)


@context("ch12.chapter")
def chapter(d, claim):
    need(d, claim)
    t1, t2, t3 = tutorial_121(d, claim), tutorial_122(d, claim), tutorial_123(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 15, "the chapter has fifteen multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    first_surge = d.one("SELECT MIN(WorkDate) FROM (SELECT tc.WorkDate FROM TimeClockEntry tc JOIN Employee e ON e.EmployeeID = tc.EmployeeID "
                        "JOIN CostCenter cc ON cc.CostCenterID = e.CostCenterID WHERE cc.CostCenterName = 'Manufacturing' "
                        "GROUP BY tc.WorkDate HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1 AND COUNT(*) > 1)")
    return dict(f=d.F, p=d.P, y=d.C, n=d.N, n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(),
                n_questions=n_q, longest_correct=and_list(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3, first_surge=first_surge,
                version="3.13.1")


# --- Exercise 12.1: cutoff at each year-end -------------------------------------------------------------------------------

@context("ch12.g1")
def g1(d, claim):
    need(d, claim)
    f = "Ex 12.1.sql"
    c1_sql = script_sql(f, "C1")
    c1 = run(d, c1_sql)
    by_year = {}
    for r in c1:
        by_year.setdefault(int(r[3][:4]), []).append(r)
    claim(sorted(by_year) == [d.F, d.P], "revenue posted in another year is for deliveries of the first and prior years only")
    c2 = run(d, script_sql(f, "C2"))
    both = [r[0] for r in c2 if r[6] == 1]
    claim(len(c2) == 9 and len(both) == 1 and both[0] in {r[0] for r in c1}, "nine invoices are dated before their shipment, and one of them is also in test C1")
    inv_date = run(d, sub(c1_sql, "strftime('%Y', sh.DeliveryDate)", "strftime('%Y', si.InvoiceDate)"))
    in_both = [r for r in inv_date if r[0] in {x[0] for x in c1}]
    claim(len(in_both) == 1 and len(inv_date) > 1, "comparing the posting year with the invoice year finds the invoices dated before their shipment and only one true cutoff error")
    fan_sql = sub(sub(c1_sql, "SELECT sil.SalesInvoiceID, MIN(s.ShipmentDate) AS ShipmentDate, MAX(s.DeliveryDate) AS DeliveryDate",
                      "SELECT sil.SalesInvoiceID, s.ShipmentDate AS ShipmentDate, s.DeliveryDate AS DeliveryDate"),
                  "GROUP BY sil.SalesInvoiceID ), Posted", "), Posted")
    fan = run(d, fan_sql)
    claim(len(fan) > len(c1) and sum(r[5] for r in fan) > sum(r[5] for r in c1), "joining the lines without grouping repeats an invoice and overstates the total")
    c3_sql = script_sql(f, "C3")
    c3 = run(d, c3_sql)
    claim([r[0] for r in c3] == d.years, "test C3 has one row for each fiscal year")
    no_unbilled = run(d, sub(c3_sql, "UNION ALL SELECT ShipmentYear, 0, 0, SalesValue FROM Unbilled", ""))
    claim(no_unbilled[-1][4] > 0 > c3[-1][4], "without the unbilled shipments the last year's effect has the wrong sign")
    std_cost = run(d, sub(c3_sql, "ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2) AS SalesValue", "sl.ExtendedStandardCost AS SalesValue"))
    claim(abs(std_cost[-1][4]) < abs(c3[-1][4]), "valuing the unbilled lines at standard cost understates the effect")
    c4 = first_row(d, script_sql(f, "C4"))
    claim(c4[0] == 0, "every shipment's cost is posted on its shipment date")
    c5_sql = script_sql(f, "C5")
    c5 = first_row(d, c5_sql)
    claim(c5[0] == c5[2] and c5[1] < c5[0], "every supplier invoice is posted on its received date, and many are dated otherwise")
    c5_full = first_row(d, sub(c5_sql, "SUM(CASE WHEN strftime('%Y', p.FirstPosting) <> strftime('%Y', pi.InvoiceDate) THEN 1 ELSE 0 END)",
                               "SUM(CASE WHEN p.FirstPosting <> pi.InvoiceDate THEN 1 ELSE 0 END)"))
    c6 = run(d, script_sql(f, "C6"))
    claim(len(c6) == 1 and c6[0][5] is not None, "one supplier invoice crosses a year-end, and it points to an accrual entry")
    c7 = run(d, script_sql(f, "C7"))
    crossing = [r for r in c7 if int(r[0]) != r[1]]
    claim(len(crossing) == 2 and all(r[0] == str(r[1] - 1) for r in crossing), "two year-ends have work done in one year and paid in the next")
    c8 = run(d, script_sql(f, "C8"))
    c9_sql = script_sql(f, "C9")
    c9 = first_row(d, c9_sql)
    two_periods = round(c9[1] * 2, 2)
    claim(abs(two_periods - c9[5]) > 100000, "two full periods overstate the unrecorded cost, which covers thirteen working days")
    c10 = run(d, script_sql(f, "C10"))
    claim(len({r[1] for r in c10}) == 1, "account 2030 holds the same balance, the opening line, at every year-end")
    n_invoices = d.one("SELECT COUNT(*) FROM SalesInvoice")
    n_goods = d.one("SELECT COUNT(DISTINCT SalesInvoiceID) FROM SalesInvoiceLine WHERE ShipmentLineID IS NOT NULL")
    claim(0 < n_invoices - n_goods < n_invoices / 20, "a few invoices bill no shipped goods (the design services), and the cutoff tests leave them out")
    return dict(**window(d), n_services=n_invoices - n_goods, n_goods=n_goods, 
        c1_rows=len(c1), by_year=[[y, len(v), r2(sum(x[5] for x in v))] for y, v in sorted(by_year.items())], c1_total=r2(sum(r[5] for r in c1)),
        c2_rows=len(c2), both=both[0], inv_rows=len(inv_date), inv_true=len(in_both), fan_rows=len(fan), fan_total=r2(sum(r[5] for r in fan)),
        c3=c3, c3_rows=len(c3), no_unbilled=no_unbilled[-1][4], std_effect=std_cost[-1][4],
        off_date=c4[0], n_unbilled=c4[1], unbilled_cost=c4[2], unbilled_value=c4[3],
        c5=c5, c5_full=c5_full[3], c6=c6[0], c7_rows=len(c7), c7=c7, crossing=crossing, c8=c8, c9=c9, two_periods=two_periods, chg25=r2(c8[1][4] - c8[0][4]), chg26=r2(c9[5] - c8[1][4]), c10_rows=len(c10),
        balance_2030=c10[0][1])


# --- Exercise 12.2: aging the open balances -----------------------------------------------------------------------------

@context("ch12.g2")
def g2(d, claim):
    need(d, claim)
    f = "Ex 12.2.sql"
    a1_sql = script_sql(f, "A1")
    a1 = run(d, a1_sql)
    no_coalesce = sub(sub(sub(a1_sql, "ROUND(si.GrandTotal - COALESCE(a.Applied, 0) - COALESCE(c.Credited, 0), 2) AS OpenBalance",
                              "ROUND(si.GrandTotal - a.Applied - c.Credited, 2) AS OpenBalance"),
                          "COALESCE(a.Applied, 0) AS Applied", "a.Applied AS Applied"),
                      "COALESCE(c.Credited, 0) AS Credited", "c.Credited AS Credited")
    nc = rows(d, no_coalesce)
    claim(nc < len(a1) / 10, "without COALESCE almost every open invoice has a NULL balance and drops out")
    a2_sql = script_sql(f, "A2")
    a2 = run(d, a2_sql)
    claim([r[0] for r in a2] == ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"], "test A2 has the five buckets of Table 8.2")
    nonzero = run(d, sub(a2_sql, "WHERE OpenBalance > 0 GROUP BY AgingBucket", "WHERE OpenBalance <> 0 GROUP BY AgingBucket"))
    over90_nz = [r for r in nonzero if r[0] == "Over 90 days"][0]
    claim(sum(r[1] for r in nonzero) > sum(r[1] for r in a2) and over90_nz[2] < 0, "keeping the nonzero balances adds the credit balances, and the oldest bucket turns negative")
    by_invoice_date = run(d, sub(a2_sql, "- julianday(si.DueDate) AS DaysPastDue", "- julianday(si.InvoiceDate) AS DaysPastDue"))
    claim([r for r in by_invoice_date if r[0] == "Over 90 days"][0][1] > 3 * [r for r in a2 if r[0] == "Over 90 days"][0][1], "aging from the invoice date puts many more invoices in the oldest bucket")
    a3 = first_row(d, script_sql(f, "A3"))
    a4 = first_row(d, script_sql(f, "A4"))
    a5_sql = script_sql(f, "A5")
    a5 = run(d, a5_sql)
    a5_name = run(d, sub(a5_sql, "SELECT CustomerID, SUM(OpenBalance) AS OpenBalance FROM Balances WHERE OpenBalance > 0 GROUP BY CustomerID",
                         "SELECT cu.CustomerName AS CustomerID, SUM(OpenBalance) AS OpenBalance FROM Balances INNER JOIN Customer AS cu "
                         "ON cu.CustomerID = Balances.CustomerID WHERE OpenBalance > 0 GROUP BY cu.CustomerName"))
    claim(sum(r[1] for r in a5_name) == sum(r[1] for r in a5) - 1, "grouping by customer name merges the two customers called Brown LLC into one row")
    a6 = run(d, script_sql(f, "A6"))
    a7_sql = script_sql(f, "A7")
    a7 = run(d, a7_sql)
    a8_sql = script_sql(f, "A8")
    a8 = first_row(d, a8_sql)
    unsummed = ("InvoicedByReceipt AS ( SELECT pil.GoodsReceiptLineID, SUM(pil.Quantity) AS QtyInvoiced FROM PurchaseInvoiceLine AS pil "
                "INNER JOIN PurchaseInvoice AS pi ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID WHERE pi.ReceivedDate <= (SELECT AsOfDate FROM Params) "
                "GROUP BY pil.GoodsReceiptLineID )")
    direct = ("InvoicedByReceipt AS ( SELECT pil.GoodsReceiptLineID, pil.Quantity AS QtyInvoiced FROM PurchaseInvoiceLine AS pil "
              "INNER JOIN PurchaseInvoice AS pi ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID WHERE pi.ReceivedDate <= (SELECT AsOfDate FROM Params) )")
    a8_direct = first_row(d, sub(a8_sql, unsummed, direct))
    a7_direct = rows(d, sub(a7_sql, unsummed, direct))
    claim(a7_direct > 10 * len(a7) and a8_direct[0] > 10 * a8[0], "joining the invoice lines without summing them to the receipt line repeats the open receipts many times")
    a8_full = first_row(d, sub(a8_sql, "grl.ExtendedStandardCost * (1 - COALESCE(ibr.QtyInvoiced, 0) / grl.QuantityReceived) AS ValueNotInvoiced",
                               "grl.ExtendedStandardCost AS ValueNotInvoiced"))
    claim(a8_full[0] > a8[0], "valuing the open lines in full overstates what is not yet invoiced")
    a7_tol = rows(d, sub(a7_sql, "AND COALESCE(ibr.QtyInvoiced, 0) < grl.QuantityReceived - 0.0001", "AND COALESCE(ibr.QtyInvoiced, 0) < grl.QuantityReceived"))
    claim(a7_tol > len(a7), "testing for exact equality adds the lines that differ by rounding noise")
    a9_sql = script_sql(f, "A9")
    a9 = run(d, a9_sql)
    a9_raw = run(d, sub(a9_sql, "ROUND(SUM(ValueNotInvoiced), 2) AS Value", "SUM(ValueNotInvoiced) AS Value"))
    a10 = run(d, script_sql(f, "A10"))
    old = [r for r in a9_raw[2:]]
    prior = {}
    for asof in (f"{d.F}-12-31", f"{d.P}-12-31"):
        prior[asof] = first_row(d, sub(script_sql(f, "A3"), f"SELECT '{d.C}-12-31' AS AsOfDate", f"SELECT '{asof}' AS AsOfDate"))
    claim(all(abs(v[2] - 380000) > 100 and abs(v[2] - 380000) < 5000 for v in prior.values()),
          "rerun at an earlier year-end, the difference to account 1020 is near the opening line but not equal to it")
    return dict(**window(d),
        n_a1=len(a1), no_coalesce=nc, a2=a2, nz_rows=sum(r[1] for r in nonzero), nz_total=r2(sum(r[2] for r in nonzero)), nz_over90=over90_nz,
        inv_over90=[r for r in by_invoice_date if r[0] == "Over 90 days"][0][1], a3=a3, a4=a4, a5=a5, n_customers=sum(r[1] for r in a5),
        by_name=sum(r[1] for r in a5_name), by_name_mid=a5_name[1][1], mid=a5[1][1], a6_rows=len(a6), a7_rows=len(a7), a8=a8, direct_rows=a7_direct,
        direct_value=a8_direct[0], full_value=a8_full[0], tol_rows=a7_tol, a9=a9, a10=a10,
        old_lines=sum(r[1] for r in old), old_value=round(sum(r[2] for r in old), 2), old_months=len(old),
        prior={k: (v[2], v[3]) for k, v in prior.items()})


# --- Exercise 12.3: where did the time go ----------------------------------------------------------------------------------

@context("ch12.g3")
def g3(d, claim):
    need(d, claim)
    f = "Ex 12.3.sql"
    t1_sql = script_sql(f, "T1")
    t1 = run(d, t1_sql)
    claim(all(r[3] == 0 for r in t1), "no direct entry is dated before its operation's actual start")
    strict = run(d, sub(t1_sql, "CASE WHEN lt.WorkDate <= op.ActualEndDate THEN 1 ELSE 0 END", "CASE WHEN lt.WorkDate < op.ActualEndDate THEN 1 ELSE 0 END"))
    claim(all(r[2] == 0 and r[6] == 1.0 for r in strict),
          "no direct entry is dated before its operation's end date, so a strict comparison counts every entry as late")
    no_filter = run(d, sub(t1_sql, "WHERE lt.LaborType = 'Direct Manufacturing'", ""))
    claim(no_filter == t1, "leaving out the LaborType filter changes nothing here, because only direct time has an operation")
    t2_sql = script_sql(f, "T2")
    t2 = run(d, t2_sql)
    last = [r for r in t2 if r[0] == str(d.C)]
    claim(len(last) == 5 and all(r[6] < 1 for r in last), "in the last year every work center is below plan on the time recorded while open")
    inner = run(d, sub(t2_sql, "LEFT JOIN (", "INNER JOIN ("))
    inner_last = {r[1]: r for r in inner if r[0] == str(d.C)}
    fan = d.q("""SELECT wc.WorkCenterName, ROUND(SUM(lt.RegularHours + lt.OvertimeHours) / SUM(op.PlannedLoadHours), 2)
        FROM WorkOrderOperation AS op INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = op.WorkCenterID
        LEFT JOIN LaborTimeEntry AS lt ON lt.WorkOrderOperationID = op.WorkOrderOperationID AND lt.LaborType = 'Direct Manufacturing'
        WHERE op.ActualEndDate <= (SELECT MAX(WorkDate) FROM LaborTimeEntry) AND strftime('%Y', op.ActualEndDate) = ?
        GROUP BY wc.WorkCenterName""", str(d.C))
    fan_by = dict(fan)
    packing = [r[1] for r in last if r[1].startswith("Packing")][0]
    qa = [r[1] for r in last if r[1].startswith("Quality")][0]
    claim(fan_by[packing] < [r[5] for r in last if r[1] == packing][0] and fan_by[qa] < [r[5] for r in last if r[1] == qa][0],
          "joining the entries straight to the operations repeats the planned hours and lowers the ratios of the late-charged work centers")
    planned = sorted(r[2] for r in last)
    claim([r[2] for r in last if r[1].startswith("Quality")][0] == planned[0] and planned[0] < 0.1 * planned[1],
          "Quality Assurance has by far the fewest planned hours of any work center, so a few hours move its ratio")
    t3 = run(d, script_sql(f, "T3"))
    last3 = [r for r in t3 if r[0] == str(d.C)]
    order_all = [r[1] for r in sorted(last3, key=lambda r: r[3])]
    order_open = [r[1] for r in sorted(last3, key=lambda r: r[5])]
    claim(order_all[0].startswith("Packing") and order_open[-1].startswith("Packing") and order_open[0].startswith("Quality"),
          "Packing is first on all hours and last on the time recorded while open, and Quality Assurance is first while open")
    t4_sql = script_sql(f, "T4")
    t4 = run(d, t4_sql)
    claim(len(t4) == 7, "test T4 has the seven months January to July")
    no_mfg = run(d, sub(t4_sql, "WHERE i.SupplyMode = 'Manufactured'", ""))
    claim(no_mfg[1][3] > t4[1][3] and no_mfg[1][4] < t4[1][4], "counting every item shipped, not only the manufactured ones, shrinks the stock build")
    stock = sum(r[4] for r in t4[1:6])
    t5 = run(d, script_sql(f, "T5"))
    quarter = [r for r in t5 if r[1] > 0.25][0]
    claim(all(r[1] <= 0.25 for r in t5 if r[0] < quarter[0]), "the share of late direct time stays at or below a quarter until the month that first passes it")
    return dict(**window(d),
        t1=t1, strict_open=[r[2] for r in strict], strict_share=[r[6] for r in strict], last=last,
        inner_packing_all=[r[5] for r in inner if r[0] == str(d.C) and r[1].startswith("Packing")][0],
        inner_qa_all=[r[5] for r in inner if r[0] == str(d.C) and r[1].startswith("Quality")][0],
        fan_packing=fan_by[packing], fan_qa=fan_by[qa], order_all=order_all, order_open=order_open,
        feb_shipped=t4[1][3], feb_all_shipped=no_mfg[1][3], feb_stock=t4[1][4], feb_all_stock=no_mfg[1][4], stock=stock, t5=t5, quarter_month=quarter[0], quarter_share=quarter[1],
        n_t2=len(t2))


# --- Exercise 12.4: is the overtime approval doing its job -----------------------------------------------------------------

@context("ch12.g4")
def g4(d, claim):
    need(d, claim)
    f = "Ex 12.4.sql"
    o1_sql = script_sql(f, "O1")
    o1 = run(d, o1_sql)
    claim(len(o1) == 12 and all(0.22 < r[3] < 0.28 for r in o1), "every reason code holds about a quarter of the approvals in every year")
    o1_int = run(d, sub(o1_sql, "COUNT(*) * 1.0 / SUM", "COUNT(*) / SUM"))
    claim(all(r[3] == 0 for r in o1_int), "without the * 1.0 every share is an integer division and reads zero")
    o2_sql = script_sql(f, "O2")
    o2 = run(d, o2_sql)
    by_title = rows(d, sub(sub(o2_sql, "SELECT oa.ApprovedByEmployeeID, e.JobTitle", "SELECT e.JobTitle"), "GROUP BY oa.ApprovedByEmployeeID, e.JobTitle", "GROUP BY e.JobTitle"))
    claim(by_title == len(o2), "grouping the approvers by job title gives the same rows here, because no two approvers share a title")
    o3_sql = script_sql(f, "O3")
    o3 = first_row(d, o3_sql)
    o3_le = first_row(d, sub(o3_sql, "SUM(CASE WHEN ApprovedDate < WorkDate THEN 1 ELSE 0 END)", "SUM(CASE WHEN ApprovedDate <= WorkDate THEN 1 ELSE 0 END)"))
    claim(o3[2] == 0 and o3[3] == 0 and o3[4] == o3[0] and o3[5] == 0 and o3_le[3] == o3[0],
          "no approval reduces the hours or comes before or after the work date, and a <= test counts every one as given in advance")
    o4_sql = script_sql(f, "O4")
    o4 = run(d, o4_sql)
    claim(len(o4) == 1 and o4[0][1] == "On the work date", "one approver and one timing on the surge days")
    o4_reg = run(d, sub(o4_sql, "HAVING COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours) = 1", "HAVING COUNT(DISTINCT tc.RegularHours) = 1"))
    reg_days = d.one("""SELECT COUNT(*) FROM (SELECT tc.WorkDate FROM TimeClockEntry AS tc INNER JOIN Employee AS e ON e.EmployeeID = tc.EmployeeID
        INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID WHERE cc.CostCenterName = 'Manufacturing'
        GROUP BY tc.WorkDate HAVING COUNT(DISTINCT tc.RegularHours) = 1 AND COUNT(*) > 1)""")
    claim(reg_days > o4[0][2] and any(r[1] == "No approval" for r in o4_reg),
          "counting regular hours alone adds days, and entries with no approval appear on them")
    o5_sql = script_sql(f, "O5")
    o5 = run(d, o5_sql)
    o5_inner = run(d, sub(o5_sql, "LEFT JOIN SurgeDays AS sd", "INNER JOIN SurgeDays AS sd"))
    claim(all(r[2] == 0 for r in o5_inner), "an inner join to the surge days drops every other day, so other-day overtime reads zero")
    claim(o5[-1][1] - o5[0][1] > 5 * abs(o5[-1][2] - o5[0][2]), "the growth in overtime is on the surge days")
    return dict(**window(d), o1_rows=len(o1), o1_int=sorted({r[3] for r in o1_int}), o2_rows=len(o2), by_title=by_title, o3=o3, o3_le=o3_le[3],
                o4=o4[0], o4_reg_days=reg_days, o4_reg_noapp=[r for r in o4_reg if r[1] == "No approval"][0],
                o5=o5, o5_inner=o5_inner, growth_surge=o5[-1][1] - o5[0][1], growth_other=o5[-1][2] - o5[0][2])


# --- Exercise 12.5: who was paid, and who approved the pay -------------------------------------------------------------------

@context("ch12.g5")
def g5(d, claim):
    need(d, claim)
    f = "Ex 12.5.sql"
    r1_sql = script_sql(f, "R1")
    r1 = run(d, r1_sql)
    claim(len(r1) == 3 and len({r[1] for r in r1}) == 1, "three registers pay one employee after the termination date")
    start = run(d, sub(r1_sql, "AND pp.PayDate > e.TerminationDate", "AND pp.PeriodStartDate > e.TerminationDate"))
    claim(len(start) == 2 and r1[0][0] not in {r[0] for r in start}, "comparing the period start with the termination date misses the register whose period holds the termination")
    end = run(d, sub(r1_sql, "AND pp.PayDate > e.TerminationDate", "AND pp.PeriodEndDate > e.TerminationDate"))
    claim([r[0] for r in end] == [r[0] for r in r1], "comparing the period end with the termination date finds the same three registers on this data")
    avg_all = run(d, sub(r1_sql, "AND q2.PayDate <= e.TerminationDate AND p2.GrossPay > 0", "AND p2.GrossPay > 0"))
    claim(avg_all[0][10] > 1.5 * r1[0][10], "averaging every register of the employee, the three after the termination included, nearly doubles the usual pay")
    r2_row = first_row(d, script_sql(f, "R2"))
    claim(r2_row[2] == 0 and r2_row[1] < r2_row[0], "the chief executive has a register in most pay periods and none in the three of the exception")
    r3_sql = script_sql(f, "R3")
    r3 = run(d, r3_sql)
    claim(len(r3) == 1 and r3[0][2] == r3[0][3], "one approver, and every register approved on its pay date")
    r3_inner = first_row(d, sub(r3_sql, "FROM PayrollRegister AS pr INNER JOIN PayrollPeriod AS pp",
                                "FROM PayrollRegister AS pr INNER JOIN PayrollPayment AS pay ON pay.PayrollRegisterID = pr.PayrollRegisterID INNER JOIN PayrollPeriod AS pp"))
    claim(r3_inner[2] == r3[0][2] - 3, "counting the approvals through an inner join to the payments drops the three registers with no payment")
    r4 = first_row(d, script_sql(f, "R4"))
    r5_sql = script_sql(f, "R5")
    r5 = run(d, r5_sql)
    r5_le = rows(d, sub(r5_sql, "pay.PaymentDate < pr.ApprovedDate", "pay.PaymentDate <= pr.ApprovedDate"))
    claim(len(r5) == 3 and r5_le > 1000, "a payment made on the approval day is not before it, and a <= test flags nearly every payment")
    ceo_title = r2_row and d.one("SELECT JobTitle FROM Employee WHERE EmployeeID = 1")
    return dict(**window(d), r1_rows=len(r1), start_rows=len(start), start_ids=[r[0] for r in start], missing_id=r1[0][0], avg_all=avg_all[0][10], usual=r1[0][10],
                r2=r2_row, no_ceo=r2_row[0] - r2_row[1], r3=r3[0], r3_inner=r3_inner[2], r4=r4, r5_rows=len(r5), r5_le=r5_le, ceo_title=ceo_title)


# --- Exercise 12.6: Chapter 8's tests in SQL ------------------------------------------------------------------------------------

@context("ch12.g6")
def g6(d, claim):
    need(d, claim)
    f = "Ex 12.6.sql"
    d1 = run(d, script_sql(f, "D1"))
    d2 = run(d, script_sql(f, "D2"))
    claim(len(d1) == 2 * len(d2) and all(r[2] == 2 and r[3] == 1 for r in d2), "the standardized test finds the pairs of the exact test and no others, in one exact spelling each")
    claim(d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE (CheckNumber IS NULL) <> (PaymentMethod <> 'Check')") == 0,
          "a payment has no check number exactly when it was not paid by check")
    d3_sql = script_sql(f, "D3")
    d3 = run(d, d3_sql)
    d3_null = rows(d, sub(d3_sql, "WHERE CheckNumber IS NOT NULL", ""))
    claim(d3_null > 50 * len(d3), "without the NULL filter, every supplier's payments with no check number form a group of their own")
    d4_sql = script_sql(f, "D4")
    d4 = run(d, d4_sql)
    d4_noid = rows(d, sub(d4_sql, "AND b.DisbursementID > a.DisbursementID", ""))
    claim(d4_noid == 2 * len(d4), "without the condition on the IDs every pair is listed twice")
    d4_noabs = rows(d, sub(d4_sql, "ABS(julianday(b.PaymentDate) - julianday(a.PaymentDate)) <= 30", "julianday(b.PaymentDate) - julianday(a.PaymentDate) <= 30"))
    claim(d4_noabs == len(d4), "leaving out ABS changes no row here, because the payment IDs are in the order of their dates for every pair")
    d4_nodate = rows(d, sub(d4_sql, "WHERE a.PaymentDate <> b.PaymentDate AND", "WHERE"))
    claim(d4_nodate == len(d4), "leaving out the condition on the dates changes no row here, because no two such payments share a date")
    d5_sql = script_sql(f, "D5")
    d5 = first_row(d, d5_sql)
    d5_noid = first_row(d, sub(d5_sql, "AND b.DisbursementID > a.DisbursementID", ""))
    claim(d5_noid[0] == 2 * d5[0] and d5_noid[1] == 2 * d5[1], "without the ID condition every pair of the near-duplicate test is counted twice")
    d5_none = first_row(d, sub(sub(d5_sql, "AND b.DisbursementID > a.DisbursementID", ""), "WHERE a.PaymentDate <> b.PaymentDate AND", "WHERE"))
    claim(d5_none[2] > 1000 and d5_none[0] > 100 * d5[0], "with neither condition, nearly every pair is a payment paired with itself")
    s1 = run(d, script_sql(f, "S1"))
    series_names = sorted({r[0] for r in s1})
    continues, restarts = [], []
    for name in series_names:
        rs = sorted((r for r in s1 if r[0] == name), key=lambda r: r[1])
        if all(b[2] == a[3] + 1 for a, b in zip(rs, rs[1:])):
            continues.append(name)
        elif all(b[2] == 1 for b in rs[1:]):
            restarts.append(name)
    claim(restarts == ["Journal entry"] and len(continues) == 3,
          "the journal entry numbers restart each year and the sales invoice, purchase order and cash receipt numbers continue across years")
    je_last = [r[3] for r in s1 if r[0] == "Journal entry"]
    s2_sql = script_sql(f, "S2")
    s2 = run(d, s2_sql)
    claim(all(r[3] == 0 for r in s2), "no document series has a gap")
    by_year = sub(s2_sql, "PARTITION BY Series ORDER BY Sequence) AS Step FROM Numbers WHERE Series <> 'Journal entry'",
                  "PARTITION BY Series, NumberYear ORDER BY Sequence) AS Step FROM Numbers WHERE Series <> 'Journal entry'")
    s2_year = run(d, by_year)
    claim(all(a[1] - b[1] == 2 for a, b in zip(s2, s2_year) if a[0] != "Journal entry"),
          "partitioning a series that continues across years leaves one step untested at each year boundary")
    # a positive control: take the first number of the second year out of the sales invoices, and run both versions of the test
    gap_sql = ("WITH Numbers AS (SELECT CAST(SUBSTR(InvoiceNumber, 4, 4) AS INTEGER) AS NumberYear, CAST(SUBSTR(InvoiceNumber, 9) AS INTEGER) AS Sequence "
               "FROM SalesInvoice WHERE CAST(SUBSTR(InvoiceNumber, 9) AS INTEGER) <> (SELECT MIN(CAST(SUBSTR(InvoiceNumber, 9) AS INTEGER)) FROM SalesInvoice "
               "WHERE CAST(SUBSTR(InvoiceNumber, 4, 4) AS INTEGER) = ?)) "
               "SELECT SUM(CASE WHEN Step > 1 THEN 1 ELSE 0 END) FROM (SELECT Sequence - LAG(Sequence) OVER ({over}) AS Step FROM Numbers)")
    found = d.one(gap_sql.format(over="ORDER BY Sequence"), d.P)
    missed = d.one(gap_sql.format(over="PARTITION BY NumberYear ORDER BY Sequence"), d.P)
    claim(found == 1 and missed == 0, "a gap planted at a year boundary is found by the unpartitioned test and missed by the partitioned one")
    b1_sql = script_sql(f, "B1")
    b1 = run(d, b1_sql)
    claim([r[0] for r in b1] == ["All payments", "Full payments", "Partial payments"], "test B1 has the three payment groups")
    no_part = run(d, sub(b1_sql, "1.0 / SUM(COUNT(*)) OVER (PARTITION BY PaymentGroup)", "1.0 / SUM(COUNT(*)) OVER ()"))
    claim(all(a[3] > 2 * b[3] for a, b in zip(no_part, b1)), "without the partition each group's shares are divided by all three groups, and every deviation more than doubles")
    int_div = run(d, sub(b1_sql, "LOG10(1 + 1.0 / Digit)", "LOG10(1 + 1 / Digit)"))
    claim(all(r[3] > 0.05 for r in int_div), "with an integer division the expected proportions are wrong and every deviation is large")
    first_char = run(d, sub(b1_sql, "CAST(SUBSTR(printf('%.15e', dp.Amount), 1, 1) AS INTEGER) AS Digit", "CAST(SUBSTR(CAST(dp.Amount AS TEXT), 1, 1) AS INTEGER) AS Digit"))
    claim(first_char[0][2] == 10 and b1[0][2] == 9, "reading the first character of the amount makes the amounts below one dollar a tenth digit, zero")
    default_e = run(d, sub(b1_sql, "printf('%.15e', dp.Amount)", "printf('%e', dp.Amount)"))
    claim(default_e == b1, "the default six decimals of printf change no deviation on this data")
    below_one = d.one("SELECT COUNT(*) FROM DisbursementPayment WHERE Amount < 1 AND PaymentDate <= ?", f"{d.C}-12-31")
    return dict(**window(d), d1_rows=len(d1), d2_rows=len(d2), d3_rows=len(d3), d3_null=d3_null, d4_rows=len(d4), d4_noid=d4_noid, d5=d5, d5_noid=d5_noid, d5_none=d5_none,
                s1=s1, continues=and_list([c.lower() for c in continues]), restarts=and_list([c.lower() for c in restarts]), je_last=je_last, s2=s2, s2_year=s2_year, found=found, missed=missed, b1=b1, no_part=no_part, int_div=int_div, first_char=first_char, below_one=below_one)
