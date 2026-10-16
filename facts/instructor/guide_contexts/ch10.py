"""Chapter 10's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 10 joins tables and summarizes their rows (inner and left joins, anti-joins, aggregates, HAVING, fan-out,
subqueries), so the guides do three jobs, as Chapter 9's did:

- they supply the values the tutorials' checkpoints show (row counts, totals by year, the trial balance), which no
  registered note covers,
- they supply what each exercise's steps need beyond its registered note (ch10.ex1 to ch10.ex6): above all the result
  of each wrong variant a guide names (a join that leaves out the document type, an anti-join with no IS NOT NULL
  test, a NOT IN against a NULL, a grouping by name, a sum over a fan-out), run read-only, so the symptom a guide
  describes is the symptom the data gives,
- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll flags the wording instead of leaving it stale.

Keys: ch10.chapter (the chapter note and its three tutorials) and ch10.g1 to ch10.g6 (the exercises; each is used next
to the registered note ch10.ex1 to ch10.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter10-exercises-sql (Ex 10.1.sql to Ex 10.6.sql).

The SQL a guide quotes is the solution scripts' own text (the check verifies it); the numbers beside it come from here.
Every variant below is fast on the dataset's indexes; a join of the ledger to a document table on the document's ID
alone cannot use the ledger's index (SourceDocumentType comes first), so those variants are computed with the
equivalent single-table counts.
"""

from __future__ import annotations

import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list, rows

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "10-joining-and-summarizing"
DECK = REPO / "slides" / "chapter-10" / "index.qmd"
THRESHOLD = 50000                                # Tutorial 10.1, Step 5: HAVING SUM(...) > 50000
LOWER = 30000                                    # ... and the lower threshold of item c
MIN_ORDERS = 20                                  # Exercise 10.3 (3)
REVENUE = (4010, 4020, 4030, 4040, 4080)         # Exercise 10.1 (3): the revenue accounts the invoice lines feed
DIRECT, INDIRECT, NONMFG = "Direct Manufacturing", "Indirect Manufacturing", "NonManufacturing"

SCHEMA = {
    "WorkOrderClose": ["WorkOrderCloseID", "WorkOrderID", "CloseDate", "MaterialVarianceAmount", "DirectLaborVarianceAmount",
                       "OverheadVarianceAmount", "ConversionVarianceAmount", "TotalVarianceAmount"],
    "WorkOrder": ["WorkOrderID", "WorkOrderNumber", "ItemID", "Status", "ReleasedDate", "ClosedDate"],
    "WorkOrderOperation": ["WorkOrderOperationID", "WorkOrderID"],
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "SupplyMode", "LifecycleStatus", "StandardLaborHoursPerUnit"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "FiscalYear", "VoucherNumber", "SourceDocumentType",
                "SourceDocumentID", "SourceLineID", "Description"],
    "Account": ["AccountID", "AccountNumber", "AccountName"],
    "JournalEntry": ["JournalEntryID", "EntryNumber", "EntryType"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID", "SubTotal", "FreightAmount", "TaxAmount",
                     "GrandTotal"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "UnitPrice", "LineTotal"],
    "SalesOrder": ["SalesOrderID", "CustomerID", "OrderTotal"],
    "SalesOrderLine": ["SalesOrderLineID", "SalesOrderID"],
    "Customer": ["CustomerID", "CustomerName", "CustomerSegment", "IsActive", "City", "Region"],
    "PurchaseInvoice": ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "SupplierID", "GrandTotal"],
    "PurchaseInvoiceLine": ["PILineID", "PurchaseInvoiceID", "POLineID", "Quantity", "UnitCost", "LineTotal"],
    "PurchaseOrderLine": ["POLineID", "UnitCost", "LineTotal"],
    "Supplier": ["SupplierID", "SupplierName", "Address", "IsApproved"],
    "DisbursementPayment": ["DisbursementID", "PaymentDate", "SupplierID", "PurchaseInvoiceID", "Amount"],
    "Employee": ["EmployeeID", "EmployeeName", "JobTitle", "Address"],
    "LaborTimeEntry": ["LaborTimeEntryID", "EmployeeID", "WorkOrderID", "WorkOrderOperationID", "WorkDate", "RegularHours",
                       "OvertimeHours", "LaborType"],
    "ProductionCompletion": ["ProductionCompletionID", "CompletionDate"],
    "ProductionCompletionLine": ["ProductionCompletionID", "ItemID", "QuantityCompleted"],
    "PayrollPayment": ["PayrollPaymentID", "PayrollRegisterID"],
    "PayrollRegister": ["PayrollRegisterID", "PayrollPeriodID", "EmployeeID", "CostCenterID"],
    "PayrollRegisterLine": ["PayrollRegisterID", "LineType", "Hours", "Amount"],
    "PayrollPeriod": ["PayrollPeriodID", "PeriodNumber", "PeriodStartDate", "PeriodEndDate", "PayDate", "FiscalYear", "Status"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
}


# --- helpers -------------------------------------------------------------------------------------------------------

def need(d, claim, *tables: str) -> None:
    """Claims that each table and the columns the guides name are in the database."""
    schema(d, claim, {t: SCHEMA[t] for t in tables})


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
    comment = source.note_comment("chapters/10-joining-and-summarizing/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 10\b")
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


def year_bounds(year: int) -> tuple[str, str]:
    return f"{year}-01-01", f"{year}-12-31"


CLOSE_JOIN = ("FROM WorkOrderClose woc JOIN WorkOrder wo ON wo.WorkOrderID = woc.WorkOrderID "
              "JOIN Item i ON i.ItemID = wo.ItemID")


# --- the chapter note and its tutorials ------------------------------------------------------------------------------

def tutorial_101(d, claim) -> dict:
    lo, hi = year_bounds(d.C)
    n_close = d.one("SELECT COUNT(*) FROM WorkOrderClose")
    two = rows(d, "SELECT woc.WorkOrderCloseID FROM WorkOrderClose woc JOIN WorkOrder wo ON wo.WorkOrderID = woc.WorkOrderID")
    three = rows(d, f"SELECT woc.WorkOrderCloseID {CLOSE_JOIN}")
    claim(two == n_close == three, "the joins of Steps 1 and 2 return exactly as many rows as WorkOrderClose holds")
    wrong_key = rows(d, "SELECT woc.WorkOrderCloseID FROM WorkOrderClose woc JOIN WorkOrder wo ON wo.WorkOrderID = woc.WorkOrderCloseID")
    claim(wrong_key != n_close, "a join on the wrong pair of keys returns a different number of rows and no error")
    groups = d.q(f"SELECT i.ItemGroup, COUNT(*), ROUND(SUM(woc.TotalVarianceAmount), 2) {CLOSE_JOIN} "
                 f"WHERE woc.CloseDate BETWEEN ? AND ? GROUP BY i.ItemGroup ORDER BY 3 DESC", lo, hi)
    ledger = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                   "AND SourceDocumentType = 'WorkOrderClose'", d.account("5080"), d.C)
    claim(round(sum(g[2] for g in groups), 2) == ledger, "the variance of the year by item group adds up to the ledger's total to the cent")
    claim([g[0] for g in groups][:1] == ["Furniture"] and groups[0][2] > 2 / 3 * ledger, "Furniture holds more than two-thirds of the year's variance")
    claim(sorted(g[0] for g in groups) == ["Furniture", "Lighting", "Textiles"], "only Furniture, Lighting and Textiles carry the variance")
    by_year = {}
    for group, year, n, total, overhead in d.q(
            f"SELECT i.ItemGroup, SUBSTR(woc.CloseDate, 1, 4), COUNT(*), ROUND(SUM(woc.TotalVarianceAmount), 2), "
            f"ROUND(SUM(woc.OverheadVarianceAmount), 2) {CLOSE_JOIN} GROUP BY 1, 2 ORDER BY 1, 2"):
        by_year.setdefault(group, []).append(dict(year=year, closes=n, total=total, overhead=overhead))
    furn, light, text = by_year["Furniture"], by_year["Lighting"], by_year["Textiles"]
    claim(all(a["total"] < b["total"] and a["closes"] > b["closes"] for a, b in zip(furn, furn[1:])),
          "Furniture's variance rises and its number of closes falls in each year")
    claim(all(a["closes"] >= b["closes"] for g in (light, text) for a, b in zip(g, g[1:])), "the number of closes falls in every group")
    claim(light[0]["total"] < light[1]["total"] < light[2]["total"] and text[1]["total"] > text[0]["total"] and text[1]["total"] > text[2]["total"],
          "Lighting's variance rises each year and Textiles' rises and then falls back")
    claim(all(y["overhead"] > 0.8 * y["total"] for g in by_year.values() for y in g), "the overhead part is most of every group-year's variance")
    release = d.q(f"SELECT ROUND(SUM(woc.TotalVarianceAmount), 2), COUNT(*) FROM WorkOrderClose woc JOIN WorkOrder wo "
                  f"ON wo.WorkOrderID = woc.WorkOrderID WHERE wo.ReleasedDate BETWEEN ? AND ?", lo, hi)[0]
    claim(release[0] != ledger, "dating the closes by the work order's release gives a different total from dating them by the close")
    thr = rows(d, f"SELECT i.ItemID {CLOSE_JOIN} WHERE woc.CloseDate BETWEEN '{lo}' AND '{hi}' GROUP BY i.ItemID "
                  f"HAVING SUM(woc.TotalVarianceAmount) > {THRESHOLD}")
    low = rows(d, f"SELECT i.ItemID {CLOSE_JOIN} WHERE woc.CloseDate BETWEEN '{lo}' AND '{hi}' GROUP BY i.ItemID "
                  f"HAVING SUM(woc.TotalVarianceAmount) > {LOWER}")
    claim(3 <= thr <= 10 and low >= 3 * thr, "a handful of items pass the higher threshold, and several times as many pass the lower")
    top = d.q(f"SELECT i.ItemGroup, i.ItemCode, ROUND(SUM(woc.TotalVarianceAmount), 2) {CLOSE_JOIN} WHERE woc.CloseDate BETWEEN ? AND ? "
              f"GROUP BY i.ItemID ORDER BY 3 DESC LIMIT ?", lo, hi, thr)
    claim(top[0][2] < 0.05 * ledger, "the largest item carries only a small share of the year's variance")
    claim(len({g for g, _, _ in top}) >= 2, "the items above the threshold come from more than one item group")
    base = ("SELECT i.ItemID, COUNT(woc.WorkOrderCloseID) AS n FROM Item i LEFT JOIN WorkOrder wo ON wo.ItemID = i.ItemID "
            f"LEFT JOIN WorkOrderClose woc ON woc.WorkOrderID = wo.WorkOrderID {{on}} WHERE i.SupplyMode = 'Manufactured' {{where}} GROUP BY i.ItemID")
    in_on = base.format(on=f"AND woc.CloseDate BETWEEN '{lo}' AND '{hi}'", where="")
    in_where = base.format(on="", where=f"AND woc.CloseDate BETWEEN '{lo}' AND '{hi}'")
    step6_on, step6_where = rows(d, in_on), rows(d, in_where)
    none = d.q(f"SELECT i.LifecycleStatus FROM Item i WHERE i.SupplyMode = 'Manufactured' AND i.ItemID IN (SELECT ItemID FROM ({in_on}) WHERE n = 0)")
    claim(step6_where < step6_on and len(none) == step6_on - step6_where, "the date condition in WHERE removes exactly the items with no closes")
    claim({r[0] for r in none} == {"Discontinued"}, "every manufactured item with no closes in the year is Discontinued")
    star = d.one(f"SELECT MIN(n) FROM (SELECT i.ItemID, COUNT(*) AS n FROM Item i LEFT JOIN WorkOrder wo ON wo.ItemID = i.ItemID "
                 f"LEFT JOIN WorkOrderClose woc ON woc.WorkOrderID = wo.WorkOrderID AND woc.CloseDate BETWEEN '{lo}' AND '{hi}' "
                 f"WHERE i.SupplyMode = 'Manufactured' GROUP BY i.ItemID)")
    claim(star == 1, "COUNT(*) reads 1 for an item with no closes, where COUNT of the close key reads 0")
    return dict(n_close=n_close, wrong_key=wrong_key, groups=groups, ledger=ledger, furniture_years=furn, lighting_years=light,
                textiles_years=text, release_total=release[0], release_closes=release[1], thr=thr, low=low, top=top,
                step6_on=step6_on, step6_where=step6_where, n_none=len(none), star=star, threshold=THRESHOLD, lower=LOWER,
                furniture_share=groups[0][2] / ledger)


def tutorial_102(d, claim) -> dict:
    end = f"{d.C}-12-31"
    closes = d.closes_of(d.C)
    claim(len(closes) == 2, "the year has two closing entries, the ones the trial balance leaves out")
    quoted = ",".join(f"'{c}'" for c in closes)
    tb = ("SELECT gl.AccountID, ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Balance FROM GLEntry gl WHERE gl.PostingDate <= ? {extra} "
          "GROUP BY gl.AccountID")
    good = tb.format(extra=f"AND gl.VoucherNumber NOT IN ({quoted})")
    n_tb = d.one(f"SELECT COUNT(*) FROM ({good})", end)
    net = d.one(f"SELECT ROUND(SUM(Balance), 2) FROM ({good})", end)
    n_debit, debit = d.q(f"SELECT COUNT(*), ROUND(SUM(Balance), 2) FROM ({good}) WHERE Balance > 0", end)[0]
    zero = d.one(f"SELECT COUNT(*) FROM ({good}) WHERE Balance = 0", end)
    claim(abs(net) < 0.005, "the net of all the balances is zero, so the debit balances equal the credit balances")
    claim(n_tb == d.one("SELECT COUNT(DISTINCT AccountID) FROM GLEntry WHERE PostingDate <= ?", end), "the trial balance holds every account with a posting")
    closed = tb.format(extra="")
    n_closed_zero = d.one(f"SELECT COUNT(*) FROM ({closed}) WHERE Balance = 0", end)
    n_closed_debit, closed_debit = d.q(f"SELECT COUNT(*), ROUND(SUM(Balance), 2) FROM ({closed}) WHERE Balance > 0", end)[0]
    claim(n_closed_zero > zero and closed_debit < debit, "leaving the closes in zeroes the revenue and expense accounts and shrinks the debit balances")
    claim(abs(d.one(f"SELECT ROUND(SUM(Balance), 2) FROM ({closed})", end)) < 0.005, "with or without the closes, the balances still net to zero")
    late = d.one("SELECT COUNT(*) FROM GLEntry WHERE PostingDate > ?", end)
    undated = f"SELECT gl.AccountID, ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Balance FROM GLEntry gl WHERE gl.VoucherNumber NOT IN ({quoted}) GROUP BY gl.AccountID"
    undated_debit = d.one(f"SELECT ROUND(SUM(Balance), 2) FROM ({undated}) WHERE Balance > 0")
    claim(late > 0 and undated_debit != debit, "the ledger holds postings after the year-end, which a missing date condition adds")
    # Step 4: account 1090 by year and source, and the three flows the checkpoint compares
    cl = d.account("1090")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = 1090") == 0, "no ledger row has the account number 1090 as its AccountID")
    flows = {}
    for year, doc, debit_, credit_ in d.q("SELECT FiscalYear, SourceDocumentType, ROUND(SUM(Debit), 2), ROUND(SUM(Credit), 2) FROM GLEntry "
                                          "WHERE AccountID = ? AND FiscalYear BETWEEN ? AND ? GROUP BY 1, 2", cl, d.F, d.C):
        flows.setdefault(year, {})[doc] = (debit_, credit_)
    claim(all(set(v) == {"JournalEntry", "PayrollSummary", "ProductionCompletion", "WorkOrderClose"} for v in flows.values()),
          "account 1090 receives four kinds of source document in each year")
    years = sorted(flows)
    payroll = [flows[y]["PayrollSummary"][0] for y in years]
    released = [flows[y]["ProductionCompletion"][1] for y in years]
    claim(all(a < b for a, b in zip(payroll, payroll[1:])), "the payroll charged to 1090 rises in each year")
    claim(max(released) < 1.08 * min(released), "the standard cost released by completions stays nearly flat")
    n_step4 = rows(d, "SELECT 1 FROM GLEntry WHERE AccountID = ? AND FiscalYear BETWEEN ? AND ? GROUP BY FiscalYear, SourceDocumentType", cl, d.F, d.C)
    # Step 5: the labor and overhead parts by close year
    parts = d.q("SELECT SUBSTR(CloseDate, 1, 4), ROUND(SUM(DirectLaborVarianceAmount), 2), ROUND(SUM(OverheadVarianceAmount), 2), "
                "ROUND(SUM(ConversionVarianceAmount), 2) FROM WorkOrderClose GROUP BY 1 ORDER BY 1")
    claim(all(p[1] < 0 for p in parts) and all(abs(a[1]) > abs(b[1]) for a, b in zip(parts, parts[1:])),
          "the labor part is favorable in every year and shrinks")
    claim(all(a[2] < b[2] for a, b in zip(parts, parts[1:])), "the overhead part grows in each year")
    cleared = dict(d.q("SELECT FiscalYear, ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'WorkOrderClose' "
                       "AND FiscalYear BETWEEN ? AND ? GROUP BY 1", cl, d.F, d.C))
    claim(all(abs(cleared[int(p[0])] - p[3]) < 0.005 for p in parts), "the conversion variance of each year equals what the closes cleared from 1090")
    # Step 6: journal entries to 1090, with and without the document type in the join
    good6 = ("SELECT gl.FiscalYear, je.EntryType FROM GLEntry gl JOIN JournalEntry je ON gl.SourceDocumentType = 'JournalEntry' "
             "AND je.JournalEntryID = gl.SourceDocumentID WHERE gl.AccountID = ? GROUP BY 1, 2")
    bad6 = good6.replace("gl.SourceDocumentType = 'JournalEntry' AND ", "")
    n6, trap6 = rows(d, good6.replace("?", str(cl))), rows(d, bad6.replace("?", str(cl)))
    claim(trap6 > n6, "without the document type in ON, the join pairs the ledger's rows with unrelated journal entries and returns more rows")
    types6 = [r[1] for r in d.q(good6.replace("?", str(cl)).replace("GROUP BY 1, 2", "GROUP BY 1, 2 ORDER BY 2"))]
    claim(sorted(set(types6)) == ["Depreciation", "Factory Overhead"], "the journal entries to 1090 are Factory Overhead and Depreciation")
    return dict(end=end, n_tb=n_tb, net=net, n_debit=n_debit, debit=debit, zero=zero, n_closed_zero=n_closed_zero, n_closed_debit=n_closed_debit,
                closed_debit=closed_debit, late=late, undated_debit=undated_debit, n_step4=n_step4, years=years, payroll=payroll,
                released=released, parts=parts, n6=n6, trap6=trap6, closes=closes, clearing_id=cl)


def tutorial_103(d, claim) -> dict:
    cut = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    out = d.q("SELECT SUBSTR(pc.CompletionDate, 1, 4), ROUND(SUM(pcl.QuantityCompleted), 0), "
              "ROUND(SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit), 0) FROM ProductionCompletionLine pcl "
              "JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID "
              "JOIN Item i ON i.ItemID = pcl.ItemID GROUP BY 1 ORDER BY 1")
    claim(out[1][1] < out[0][1] and abs(out[2][1] / out[0][1] - 1) < 0.05, "output dips in the second year and ends within five percent of the first")
    pay = d.q("SELECT pp.FiscalYear, prl.LineType, ROUND(SUM(prl.Hours), 0), ROUND(SUM(prl.Amount), 2) FROM PayrollRegisterLine prl "
              "JOIN PayrollRegister pr ON pr.PayrollRegisterID = prl.PayrollRegisterID "
              "JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID JOIN CostCenter cc ON cc.CostCenterID = pr.CostCenterID "
              "WHERE cc.CostCenterName = 'Manufacturing' AND prl.LineType IN ('Regular Earnings', 'Overtime Earnings') "
              "AND pp.FiscalYear BETWEEN ? AND ? GROUP BY 1, 2 ORDER BY 1, 2", d.F, d.C)
    overtime = [r[2] for r in pay if r[1] == "Overtime Earnings"]
    regular = [r[2] for r in pay if r[1] == "Regular Earnings"]
    claim(overtime[-1] > 2 * overtime[0] and all(a < b for a, b in zip(regular, regular[1:])),
          "regular hours rise in each year and the overtime hours more than double")
    people = d.q("SELECT pp.FiscalYear, COUNT(*), COUNT(DISTINCT pr.EmployeeID) FROM PayrollRegister pr "
                 "JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID JOIN CostCenter cc ON cc.CostCenterID = pr.CostCenterID "
                 "WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear BETWEEN ? AND ? GROUP BY 1 ORDER BY 1", d.F, d.C)
    claim(len({p[2] for p in people}) == 1 and all(p[1] > 1000 for p in people),
          "the manufacturing payroll paid the same number of people in each year, with well over a thousand registers a year")
    lte = d.q("SELECT COUNT(*), COUNT(WorkOrderOperationID), COUNT(DISTINCT EmployeeID), MIN(WorkDate), MAX(WorkDate) FROM LaborTimeEntry")[0]
    pc = d.q("SELECT COUNT(*), MIN(CompletionDate), MAX(CompletionDate) FROM ProductionCompletion")[0]
    claim(lte[3][:7] == pc[1][:7] == f"{d.F}-01" or lte[3][:4] == pc[1][:4] == str(d.F), "both tables begin in the first month of the window")
    claim(lte[4] < pc[2] and pc[2] == f"{d.C}-12-31", "the time records end before the completions, which run to the last day of the year")
    claim(0.7 < lte[1] / lte[0] < 0.8, "about three-quarters of the labor time entries carry an operation")
    periods = d.q("SELECT PeriodNumber, PeriodStartDate, PeriodEndDate, PayDate, Status FROM PayrollPeriod WHERE PeriodEndDate >= ? ORDER BY PeriodStartDate",
                  f"{d.C}-12-01")
    claim([p[4] for p in periods] == ["Processed", "Open", "Open"] and periods[1][1] > cut,
          "the time records end in the last processed pay period, and the two periods after it are Open")
    # Step 6 as the tutorial writes it: unrounded sums in the derived tables, rounded only in the outer SELECT.
    step6 = ("SELECT h.WorkYear, h.LaborType, ROUND(h.Hours / o.StandardHours, 2), ROUND(o.StandardHours, 0) FROM (SELECT SUBSTR(lt.WorkDate, 1, 4) AS WorkYear, "
             "lt.LaborType, SUM(lt.RegularHours + lt.OvertimeHours) AS Hours FROM LaborTimeEntry lt WHERE lt.LaborType <> 'NonManufacturing' "
             "GROUP BY 1, 2) h JOIN (SELECT SUBSTR(pc.CompletionDate, 1, 4) AS WorkYear, SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) "
             "AS StandardHours FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID "
             "JOIN Item i ON i.ItemID = pcl.ItemID {cut} GROUP BY 1) o ON o.WorkYear = h.WorkYear ORDER BY 1, 2")
    with_cut = d.q(step6.format(cut=f"WHERE pc.CompletionDate <= '{cut}'"))
    without = d.q(step6.format(cut=""))
    direct = [r[2] for r in with_cut if r[1] == DIRECT]
    indirect = [r[2] for r in with_cut if r[1] == INDIRECT]
    claim(all(x < 1 for x in direct) and direct[0] < direct[-1], "direct labor stays below the standard hours in every year and moves closer to them")
    claim(indirect[0] < 0.4 and indirect[-1] > 0.5, "indirect time grows from about a third of the standard hours to more than half")
    claim([r[2] for r in with_cut if r[0] == str(d.F)] == [r[2] for r in without if r[0] == str(d.F)] and
          [r[2] for r in with_cut if r[0] == str(d.C)] != [r[2] for r in without if r[0] == str(d.C)],
          "counting the output only to the last day with time records changes only the last year")
    no_cut = {r[1]: r[2] for r in without if r[0] == str(d.C)}
    # Coverage (decision N3): each year's last date by kind of time, and the sensitivity that stops both the hours and
    # the output at the earlier of the direct and indirect endpoints. The tutorial keeps its cut-off at the last day with
    # time records and calls the comparison an observed-records diagnostic; these figures are the labeled sensitivity.
    ends = {(y, k): e for y, k, e in d.q("SELECT SUBSTR(WorkDate, 1, 4), LaborType, MAX(WorkDate) FROM LaborTimeEntry "
                                         "WHERE LaborType <> 'NonManufacturing' GROUP BY 1, 2")}
    last_year = str(d.C)
    claim(ends[(last_year, DIRECT)] == cut and ends[(last_year, INDIRECT)] < cut,
          "in the last year direct time ends on the last day with time records, and indirect time earlier")
    claim(all(ends[(y, INDIRECT)] <= ends[(y, DIRECT)] for y, _ in ends), "indirect time never ends after direct time in a year")
    sens = []
    for y in sorted({y for y, _ in ends}):
        stop = min(ends[(y, DIRECT)], ends[(y, INDIRECT)])
        dh, ih = d.q("SELECT SUM(CASE WHEN LaborType = ? THEN RegularHours + OvertimeHours END), "
                     "SUM(CASE WHEN LaborType = ? THEN RegularHours + OvertimeHours END) FROM LaborTimeEntry "
                     "WHERE WorkDate BETWEEN ? AND ?", DIRECT, INDIRECT, f"{y}-01-01", stop)[0]
        sh = d.one("SELECT SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) FROM ProductionCompletionLine pcl "
                   "JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID "
                   "JOIN Item i ON i.ItemID = pcl.ItemID WHERE pc.CompletionDate BETWEEN ? AND ?", f"{y}-01-01", stop)
        sens.append(dict(year=y, stop=stop, direct=dh, indirect=ih, standard=sh, d_ratio=round(dh / sh, 2),
                         i_ratio=round(ih / sh, 2), total=round((dh + ih) / sh, 2)))
    common = sens[-1]
    claim(all((s["d_ratio"], s["i_ratio"]) == (direct[i], indirect[i]) for i, s in enumerate(sens[:-1])),
          "stopping the earlier years at their own earlier endpoint changes none of their rounded ratios")
    claim(common["d_ratio"] < direct[-1] and common["i_ratio"] >= indirect[-1] and common["d_ratio"] < 1 and common["i_ratio"] > 0.5,
          "counted to the last day of indirect time on both sides, the last year's direct ratio is lower, the indirect "
          "ratio no lower, and the pattern of the years (direct below one, indirect above half) holds")
    late_kinds = {r[0] for r in d.q("SELECT DISTINCT LaborType FROM LaborTimeEntry WHERE WorkDate > ? AND WorkDate <= ?",
                                    common["stop"], cut)}
    claim(late_kinds == {DIRECT, NONMFG}, "between the last day of indirect time and the cut-off, only direct and non-manufacturing time is recorded")
    late_direct = d.one("SELECT SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry WHERE LaborType = ? AND WorkDate > ? "
                        "AND WorkDate <= ?", DIRECT, common["stop"], cut)
    plant = [round(a + b, 2) for a, b in zip(direct, indirect)]
    n_lte = dict(d.q("SELECT SUBSTR(WorkDate, 1, 4), COUNT(*) FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' GROUP BY 1"))
    n_pcl = dict(d.q("SELECT SUBSTR(pc.CompletionDate, 1, 4), COUNT(*) FROM ProductionCompletionLine pcl "
                     "JOIN ProductionCompletion pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID GROUP BY 1"))
    product = sum(n_lte[y] * n_pcl[y] for y in n_lte)
    claim(product > 100 * (sum(n_lte.values()) + sum(n_pcl.values())), "joining the two tables row by row before summarizing would return hundreds of times as many rows as they hold")
    unmatched = d.q("SELECT lt.LaborType, COUNT(*), ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 0) FROM LaborTimeEntry lt "
                    "LEFT JOIN WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID WHERE op.WorkOrderOperationID IS NULL "
                    "GROUP BY 1 ORDER BY 1")
    orphan = d.q("SELECT lt.LaborType, COUNT(*) FROM LaborTimeEntry lt LEFT JOIN WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID "
                 "WHERE op.WorkOrderOperationID IS NULL AND lt.WorkOrderOperationID IS NOT NULL GROUP BY 1")
    is_null = dict(d.q("SELECT LaborType, COUNT(*) FROM LaborTimeEntry WHERE WorkOrderOperationID IS NULL GROUP BY 1"))
    claim([u[0] for u in unmatched] == [DIRECT, INDIRECT, NONMFG] and [o[0] for o in orphan] == [DIRECT],
          "the unmatched time is direct, indirect and non-manufacturing, and the entries with a filled key and no operation are all direct")
    claim(is_null[DIRECT] < dict((u[0], u[1]) for u in unmatched)[DIRECT], "a test on the entry's key alone finds fewer direct entries than the anti-join")
    return dict(cut=cut, out=out, pay=pay, people=people, lte=lte, pc=pc, periods=periods, with_cut=with_cut, no_cut=no_cut,
                ends=ends, sens=sens, common=common, late_direct=late_direct, plant=plant, indirect_end=ends[(last_year, INDIRECT)],
                direct=direct, indirect=indirect, product=product, unmatched=unmatched, orphan=orphan[0][1], is_null=is_null,
                overtime=overtime, regular=regular)


@context("ch10.chapter")
def chapter(d, claim):
    need(d, claim, *SCHEMA)
    t1, t2, t3 = tutorial_101(d, claim), tutorial_102(d, claim), tutorial_103(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 15, "the chapter has fifteen multiple-choice questions (the key's rationales and the note's plan use their numbers)")
    # The two demonstrations of the chapter note: the fan-out of the invoice total, and the NOT IN trap.
    lo, hi = year_bounds(d.C)
    fan = d.q("SELECT ROUND(SUM(si.GrandTotal), 2) FROM SalesInvoice si JOIN SalesInvoiceLine sil ON sil.SalesInvoiceID = si.SalesInvoiceID "
              "WHERE si.InvoiceDate BETWEEN ? AND ?", lo, hi)[0][0]
    true = d.one("SELECT ROUND(SUM(GrandTotal), 2) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", lo, hi)
    claim(1.5 < fan / true < 2.0, "summed over the join, the invoices' GrandTotal is nearly twice the true total")
    claim(d.one("SELECT ROUND(SUM(SubTotal), 2) FROM (SELECT si.SalesInvoiceID, si.SubTotal FROM SalesInvoice si "
                "WHERE si.InvoiceDate BETWEEN ? AND ?)", lo, hi) < true,
          "the invoices' SubTotal is less than their GrandTotal, which also holds freight and tax")
    not_in = d.one("SELECT COUNT(*) FROM Employee WHERE EmployeeID NOT IN (SELECT ApprovedByEmployeeID FROM PurchaseRequisition)")
    not_exists = d.one("SELECT COUNT(*) FROM Employee e WHERE NOT EXISTS (SELECT 1 FROM PurchaseRequisition r WHERE r.ApprovedByEmployeeID = e.EmployeeID)")
    n_emp = d.one("SELECT COUNT(*) FROM Employee")
    claim(not_in == 0 and not_exists > 0.9 * n_emp, "NOT IN returns no employee, and NOT EXISTS finds nearly every one, because the approver list holds a NULL")
    claim(d.one("SELECT COUNT(*) FROM PurchaseRequisition WHERE ApprovedByEmployeeID IS NULL") > 0, "some requisitions have no approver")
    names = d.one("SELECT COUNT(*) FROM (SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1)")
    claim(names >= 1, "two different customers share a name")
    keys_fan = d.one("SELECT COUNT(*) FROM WorkOrderClose woc JOIN WorkOrderOperation op ON op.WorkOrderID = woc.WorkOrderID")
    claim(keys_fan > 3 * d.one("SELECT COUNT(*) FROM WorkOrderClose"), "closes joined to their operations are repeated three or four times")
    return dict(f=d.F, p=d.P, y=d.C, n=d.N, n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(),
                n_questions=n_q, longest_correct=and_list(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3, fan_total=fan,
                true_total=true, not_in=not_in, not_exists=not_exists, n_employees=n_emp, keys_fan=keys_fan, version="3.13.1")


# --- Exercise 10.1: invoice lines against the ledger ------------------------------------------------------------------

@context("ch10.g1")
def g1(d, claim):
    need(d, claim, "SalesInvoiceLine", "SalesInvoice", "Item", "Customer", "GLEntry", "Account")
    lo, hi = year_bounds(d.C)
    ids = ",".join(str(d.account(str(n))) for n in REVENUE)
    n_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    wrong_key = rows(d, "SELECT 1 FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID "
                        "JOIN Item i ON i.ItemID = sil.ItemID JOIN Customer c ON c.CustomerID = si.SalesInvoiceID")
    claim(wrong_key < n_lines, "a customer key matched to the invoice key returns fewer rows and no error")
    n_year = d.one("SELECT COUNT(*) FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID "
                   "WHERE si.InvoiceDate BETWEEN ? AND ?", lo, hi)
    n_invoices = d.one("SELECT COUNT(*) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", lo, hi)
    fan_sub = d.one("SELECT ROUND(SUM(si.SubTotal), 2) FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID "
                    "WHERE si.InvoiceDate BETWEEN ? AND ?", lo, hi)
    lines_total = d.one("SELECT ROUND(SUM(sil.LineTotal), 2) FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID "
                        "WHERE si.InvoiceDate BETWEEN ? AND ?", lo, hi)
    claim(n_year > n_invoices and fan_sub > 1.5 * lines_total, "summing an invoice-level column over the join to the lines counts each invoice once for each of its lines")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice si WHERE NOT EXISTS (SELECT 1 FROM SalesInvoiceLine l WHERE l.SalesInvoiceID = si.SalesInvoiceID)") == 0,
          "every invoice has at least one line, so the join drops no invoice")
    by_type = d.q(f"SELECT gl.SourceDocumentType, COUNT(*), ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) FROM GLEntry gl WHERE gl.FiscalYear = ? "
                  f"AND gl.AccountID IN ({ids}) GROUP BY 1 ORDER BY 1", d.C)
    claim([t[0] for t in by_type] == ["JournalEntry", "SalesInvoice"], "only sales invoices and a journal entry post to the revenue accounts in the year")
    no_type = d.one(f"SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE FiscalYear = ? AND AccountID IN ({ids})", d.C)
    claim(no_type == 0, "without the SourceDocumentType condition, the year-end close cancels the revenue and the total is zero")
    close_rows = next(t[1] for t in by_type if t[0] == "JournalEntry")
    with_freight = d.one(f"SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE FiscalYear = ? AND SourceDocumentType = 'SalesInvoice' "
                         f"AND AccountID IN ({ids}, {d.account('4050')})", d.C)
    first = f"{d.C}-01-01"
    base = ("SELECT si.InvoiceNumber, si.InvoiceDate FROM GLEntry gl JOIN SalesInvoice si ON {on} JOIN Account a ON a.AccountID = gl.AccountID "
            f"WHERE gl.FiscalYear = {d.C} AND gl.AccountID IN ({ids}) AND si.InvoiceDate < '{first}'")
    good = d.q(base.format(on="gl.SourceDocumentType = 'SalesInvoice' AND si.SalesInvoiceID = gl.SourceDocumentID"))
    trap = d.q(base.format(on="si.SalesInvoiceID = gl.SourceDocumentID"))
    extra = sorted({(n, dt) for n, dt in trap} - {(n, dt) for n, dt in good})
    extra_id = d.one("SELECT SalesInvoiceID FROM SalesInvoice WHERE InvoiceNumber = ?", extra[0][0]) if extra else None
    je_ids = {r[0] for r in d.q(f"SELECT DISTINCT SourceDocumentID FROM GLEntry WHERE FiscalYear = ? AND SourceDocumentType = 'JournalEntry' "
                                f"AND AccountID IN ({ids})", d.C)}
    claim(len(trap) > len(good) and len(extra) == 1 and extra[0][1][:4] < str(d.P) and extra_id in je_ids,
          "a join on the document ID alone adds the invoice whose ID equals the closing entry's, an invoice dated years before")
    freight = d.q("SELECT COUNT(*), COUNT(gl.SourceLineID), ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) FROM GLEntry gl WHERE gl.AccountID = ? "
                  "AND gl.FiscalYear = ? AND gl.SourceDocumentType = 'SalesInvoice'", d.account("4050"), d.C)[0]
    by_posting = d.one("SELECT ROUND(SUM(si.FreightAmount), 2) FROM SalesInvoice si WHERE si.SalesInvoiceID IN (SELECT DISTINCT SourceDocumentID FROM GLEntry "
                       "WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ?)", d.C)
    by_date = d.one("SELECT ROUND(SUM(FreightAmount), 2) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", lo, hi)
    claim(abs(by_posting - freight[2]) < 0.005 and by_date < by_posting, "the 4050 postings equal the freight on the invoices posted in the year, and fall short of the freight on invoices dated in it")
    cutoff_freight = d.one("SELECT ROUND(SUM(FreightAmount), 2) FROM SalesInvoice WHERE InvoiceNumber IN (%s)" % ",".join(f"'{n}'" for n, _ in good))
    claim(abs(cutoff_freight - round(by_posting - by_date, 2)) < 0.005, "the freight the headers lose when selected by invoice date is the freight of the invoices dated before the year")
    as_id = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (4010, 4020, 4030, 4040, 4080)")
    claim(as_id == 0, "no ledger row has an account number of the revenue accounts as its AccountID")
    return dict(wrong_key=wrong_key, as_id=as_id, n_lines=n_lines, n_year=n_year, n_invoices=n_invoices, fan_sub=fan_sub, lines_total=lines_total, no_type=no_type,
                close_rows=close_rows, with_freight=with_freight, diff_freight=round(with_freight - lines_total, 2), n_trap=len(trap), n_good=len(good),
                trap_invoices=len({n for n, _ in trap}), extra=extra[0], freight_n=freight[0], freight_lines=freight[1], freight=freight[2],
                freight_by_date=by_date, freight_gap=round(by_posting - by_date, 2), first=first,
                ledger_first=d.one("SELECT PostingDate FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ? ORDER BY PostingDate LIMIT 1", d.C))


# --- Exercise 10.2: tracing a sale ------------------------------------------------------------------------------------

@context("ch10.g2")
def g2(d, claim):
    need(d, claim, "GLEntry", "SalesInvoice", "SalesInvoiceLine", "Account", "Customer", "Item")
    sid = d.one("SELECT SalesInvoiceID FROM SalesInvoice WHERE InvoiceNumber = 'SI-2025-007947'")
    claim(sid == 7947, "the traced sale is SalesInvoiceID 7947")
    n_correct = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND SourceDocumentID = ?", sid)
    n_id_only = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentID = ?", sid)
    kinds = d.one("SELECT COUNT(DISTINCT SourceDocumentType) FROM GLEntry WHERE SourceDocumentID = ?", sid)
    claim(n_id_only > 3 * n_correct and kinds > 5, "the ID alone matches ledger rows of many kinds of document")
    line_ok = d.one("SELECT COUNT(*) FROM GLEntry gl JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = gl.SourceLineID "
                    "WHERE gl.SourceDocumentType = 'SalesInvoice' AND gl.SourceDocumentID = ?", sid)
    line_no_type = d.one("SELECT COUNT(*) FROM GLEntry gl JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = gl.SourceLineID "
                         "WHERE gl.SourceDocumentID = ?", sid)
    line_by_invoice = d.one("SELECT COUNT(*) FROM GLEntry gl JOIN SalesInvoiceLine sil ON sil.SalesInvoiceID = gl.SourceDocumentID "
                            "WHERE gl.SourceDocumentType = 'SalesInvoice' AND gl.SourceDocumentID = ?", sid)
    claim(line_ok == 1 and line_no_type > line_ok and line_by_invoice == n_correct,
          "joined on SourceLineID the invoice's one revenue posting meets its line; without the type other documents' line numbers also match, and joined on the invoice ID every posting meets the line")
    tested = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ? AND SourceLineID IS NOT NULL", d.C)
    anti_all = rows(d, "SELECT gl.GLEntryID FROM GLEntry gl LEFT JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = gl.SourceLineID "
                       f"WHERE gl.SourceDocumentType = 'SalesInvoice' AND gl.FiscalYear = {d.C} AND sil.SalesInvoiceLineID IS NULL")
    header = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' AND FiscalYear = ? AND SourceLineID IS NULL", d.C)
    claim(anti_all == header and anti_all > tested, "without the SourceLineID test, the anti-join flags exactly the header-level rows")
    anti_types = rows(d, "SELECT gl.GLEntryID FROM GLEntry gl LEFT JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = gl.SourceLineID "
                         f"WHERE gl.FiscalYear = {d.C} AND gl.SourceLineID IS NOT NULL AND sil.SalesInvoiceLineID IS NULL")
    other_types = d.one("SELECT COUNT(DISTINCT SourceDocumentType) FROM GLEntry WHERE FiscalYear = ? AND SourceLineID IS NOT NULL AND SourceDocumentType <> 'SalesInvoice'", d.C)
    claim(anti_types > tested and other_types >= 5, "without the document type, the anti-join flags the lines of every other document's table")
    inner = d.one("SELECT COUNT(*) FROM GLEntry gl JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = gl.SourceLineID "
                  "WHERE gl.SourceDocumentType = 'SalesInvoice' AND gl.FiscalYear = ?", d.C)
    claim(inner == tested, "an inner join in place of the anti-join returns the postings tested, not the exceptions")
    reverse = d.one("SELECT COUNT(*) FROM SalesInvoiceLine sil WHERE NOT EXISTS (SELECT 1 FROM GLEntry gl WHERE gl.SourceDocumentType = 'SalesInvoice' "
                    "AND gl.SourceDocumentID = sil.SalesInvoiceID AND gl.SourceLineID = sil.SalesInvoiceLineID)")
    claim(reverse == 0, "every invoice line has a revenue posting, so the reverse test finds nothing")
    other_invoice = d.one("SELECT COUNT(*) FROM GLEntry gl JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = gl.SourceLineID "
                          "WHERE gl.SourceDocumentType = 'SalesInvoice' AND gl.FiscalYear = ? AND sil.SalesInvoiceID <> gl.SourceDocumentID", d.C)
    claim(other_invoice == 0, "each line belongs to the invoice its posting names")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine") > tested, "the lines of all years outnumber the year's tested postings")
    hdr = d.q("SELECT a.AccountNumber, a.AccountName FROM GLEntry gl JOIN Account a ON a.AccountID = gl.AccountID WHERE gl.SourceDocumentType = 'SalesInvoice' "
              "AND gl.FiscalYear = ? AND gl.SourceLineID IS NULL GROUP BY 1, 2 ORDER BY 1", d.C)
    claim([r[1] for r in hdr] == ["Accounts Receivable", "Sales Tax Payable", "Freight Revenue"], "the postings with no SourceLineID are the receivable, the sales tax and the freight")
    return dict(sid=sid, n_correct=n_correct, n_id_only=n_id_only, kinds=kinds, line_no_type=line_no_type, line_by_invoice=line_by_invoice,
                tested=tested, anti_all=anti_all, anti_types=anti_types, header=header, header_accounts=[r[0] for r in hdr], inner=inner, reverse=reverse, other_invoice=other_invoice)


# --- Exercise 10.3: average order value -------------------------------------------------------------------------------

@context("ch10.g3")
def g3(d, claim):
    need(d, claim, "SalesOrder", "SalesOrderLine", "Customer")
    by_id = d.q("SELECT c.CustomerID, c.CustomerName, COUNT(*), AVG(o.OrderTotal) FROM SalesOrder o JOIN Customer c ON c.CustomerID = o.CustomerID "
                "GROUP BY c.CustomerID ORDER BY 4 DESC")
    n_customers = d.one("SELECT COUNT(*) FROM Customer")
    overall = d.one("SELECT AVG(OrderTotal) FROM SalesOrder")
    lj = ("SELECT c.CustomerID, COUNT(*) AS n, AVG(so.OrderTotal) AS a FROM Customer c LEFT JOIN SalesOrder so ON so.CustomerID = c.CustomerID "
          "GROUP BY c.CustomerID")
    n_lj, lj_one = rows(d, lj), d.one(f"SELECT COUNT(*) FROM ({lj}) WHERE a IS NULL AND n = 1")
    claim(n_lj == n_customers and lj_one == n_customers - len(by_id), "from the customer table, COUNT(*) reads 1 for each customer without orders, and their average is NULL")
    fan = d.one("SELECT ROUND(SUM(so.OrderTotal), 2) FROM SalesOrder so JOIN SalesOrderLine sol ON sol.SalesOrderID = so.SalesOrderID")
    true = d.one("SELECT ROUND(SUM(OrderTotal), 2) FROM SalesOrder")
    claim(fan > 2 * true, "an order's total summed over the join to its lines is counted once for each line")
    avg_of_avgs = sum(r[3] for r in by_id) / len(by_id)
    claim(abs(avg_of_avgs - overall) > 1000, "the average of the customers' averages differs from the average of all orders by more than a thousand dollars")
    top10 = [r[0] for r in by_id[:10]]
    kept = [r[0] for r in by_id if r[2] >= MIN_ORDERS][:10]
    claim(top10 == kept, "the ten highest averages all have at least the minimum number of orders, so the HAVING condition changes nothing here")
    n_min = sum(1 for r in by_id if r[2] >= MIN_ORDERS)
    claim(n_min < len(by_id), "some customers have fewer than the minimum number of orders")
    by_name = d.q("SELECT c.CustomerName FROM SalesOrder o JOIN Customer c ON c.CustomerID = o.CustomerID GROUP BY c.CustomerName")
    claim(len(by_name) == len(by_id) - 1, "grouping by name returns one row fewer than grouping by key")
    shared = [r[0] for r in d.q("SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1 ORDER BY 1")]
    with_segment = d.q("SELECT CustomerName FROM Customer GROUP BY CustomerName, CustomerSegment HAVING COUNT(*) > 1")
    claim(len(with_segment) == 1 and len(shared) == 2 and with_segment[0][0] in shared,
          "adding the segment to the grouping leaves one of the two shared names, because the other name's customers are in different segments")
    hidden = next(n for n in shared if n != with_segment[0][0])
    merged = next(r for r in d.q("SELECT c.CustomerName, COUNT(*), AVG(o.OrderTotal) FROM SalesOrder o JOIN Customer c ON c.CustomerID = o.CustomerID "
                                 "GROUP BY c.CustomerName") if r[0] == hidden)
    ranks = [i for i, r in enumerate(by_id, 1) if r[1] == hidden]
    name_rank = [i for i, r in enumerate(sorted(d.q("SELECT c.CustomerName, AVG(o.OrderTotal) FROM SalesOrder o JOIN Customer c ON c.CustomerID = o.CustomerID "
                                                    "GROUP BY c.CustomerName"), key=lambda r: -r[1]), 1) if r[0] == hidden]
    seg = d.q("SELECT c.CustomerSegment, COUNT(*), ROUND(AVG(o.OrderTotal), 2) FROM SalesOrder o JOIN Customer c ON c.CustomerID = o.CustomerID "
              "GROUP BY 1 ORDER BY 3 DESC")
    claim(seg[0][2] > 4 * seg[-1][2], "the largest segment's average order is more than four times the smallest's")
    return dict(n_customers=n_customers, n_lj=n_lj, lj_one=lj_one, fan=fan, true=true, avg_of_avgs=avg_of_avgs, overall=overall, n_min=n_min,
                n_by_name=len(by_name), hidden=hidden, hidden_segment_pair=with_segment[0][0], merged_n=merged[1], merged_avg=merged[2],
                id_ranks=ranks, name_rank=name_rank[0], seg_ratio=seg[0][2] / seg[-1][2], min_orders=MIN_ORDERS, top_first=by_id[0][1])


# --- Exercise 10.4: purchase price variance by supplier ---------------------------------------------------------------

@context("ch10.g4")
def g4(d, claim):
    need(d, claim, "GLEntry", "Account", "PurchaseInvoice", "PurchaseInvoiceLine", "PurchaseOrderLine", "Supplier")
    lo, hi = year_bounds(d.C)
    ppv = d.account("5060")
    top = lambda where: d.q(  # noqa: E731
        "SELECT s.SupplierID, ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) v FROM GLEntry gl JOIN PurchaseInvoice pi ON gl.SourceDocumentType = 'PurchaseInvoice' "
        f"AND pi.PurchaseInvoiceID = gl.SourceDocumentID JOIN Supplier s ON s.SupplierID = pi.SupplierID WHERE gl.AccountID = ? AND gl.FiscalYear = ? {where} "
        "GROUP BY 1 ORDER BY v DESC LIMIT 5", ppv, d.C)
    right = top("AND gl.Description LIKE '%purchase variance'")
    all_desc = top("")
    unfav = top("AND gl.Description = 'Record unfavorable purchase variance'")
    claim([r[0] for r in all_desc] != [r[0] for r in right] and [r[0] for r in unfav] != [r[0] for r in right],
          "dropping the description condition, or keeping only the unfavorable postings, changes the five largest suppliers")
    net = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description LIKE '%purchase variance'", ppv, d.C)
    no_desc = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'PurchaseInvoice'", ppv, d.C)
    all_year = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ?", ppv, d.C)
    claim(all_year == 0, "all the year's postings to 5060, with the closing entry, net to zero")
    unfav_total = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description = 'Record unfavorable purchase variance'", ppv, d.C)
    claim(no_desc > net and unfav_total > net, "the tax rows raise the total above the variance, and the unfavorable rows alone are more than the net")
    like_fav = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description LIKE '%favorable%'", ppv, d.C)
    postings = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description LIKE '%purchase variance'", ppv, d.C)
    claim(like_fav == postings, "LIKE '%favorable%' matches the same postings as LIKE '%purchase variance', favorable and unfavorable")
    n_suppliers = d.one("SELECT COUNT(DISTINCT pi.SupplierID) FROM GLEntry gl JOIN PurchaseInvoice pi ON gl.SourceDocumentType = 'PurchaseInvoice' "
                        "AND pi.PurchaseInvoiceID = gl.SourceDocumentID WHERE gl.AccountID = ? AND gl.FiscalYear = ? AND gl.Description LIKE '%purchase variance'", ppv, d.C)
    top_share = sum(r[1] for r in right) / net
    claim(top_share < 0.3 and n_suppliers > 50, "the five largest suppliers hold under a third of the variance, among more than fifty suppliers")
    lines = ("FROM PurchaseInvoiceLine pil JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID "
             "JOIN PurchaseOrderLine pol ON pol.POLineID = pil.POLineID WHERE pi.InvoiceDate BETWEEN ? AND ?")
    line_total = d.one(f"SELECT ROUND(SUM(pil.LineTotal - pol.LineTotal), 2) {lines}", lo, hi)
    variance = d.one(f"SELECT ROUND(SUM(pil.Quantity * (pil.UnitCost - pol.UnitCost)), 2) {lines}", lo, hi)
    claim(abs(line_total) > 100 * abs(variance), "the difference of the two LineTotal columns is far larger than the price variance, because an order line's total covers its whole quantity")
    n_lines = d.one(f"SELECT COUNT(*) {lines}", lo, hi)
    above = d.one(f"SELECT COUNT(*) {lines} AND pil.UnitCost > pol.UnitCost", lo, hi)
    below = d.one(f"SELECT COUNT(*) {lines} AND pil.UnitCost < pol.UnitCost", lo, hi)
    at = d.one(f"SELECT COUNT(*) {lines} AND pil.UnitCost = pol.UnitCost", lo, hi)
    unequal = d.one(f"SELECT COUNT(*) {lines} AND pil.UnitCost <> pol.UnitCost", lo, hi)
    tolerance = d.one(f"SELECT COUNT(*) {lines} AND ABS(pil.UnitCost - pol.UnitCost) < 0.005", lo, hi)
    claim(above + below + at == n_lines and unequal == above + below and tolerance == at,
          "the three counts add up to the lines, <> returns the lines above and below, and a half-cent tolerance finds the same lines at the order price")
    n_all = d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine pil JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID "
                  "WHERE pi.InvoiceDate BETWEEN ? AND ?", lo, hi)
    unmatched = n_all - n_lines
    claim(unmatched > 0 and d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine pil JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID "
                                  "WHERE pi.InvoiceDate BETWEEN ? AND ? AND pil.POLineID IS NULL", lo, hi) == unmatched,
          "some invoice lines carry no order line, and the inner join leaves them out")
    rates = []
    for y in d.years:
        a, b = year_bounds(y)
        everything = d.one("SELECT SUM(pil.Quantity * pil.UnitCost) FROM PurchaseInvoiceLine pil JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = pil.PurchaseInvoiceID "
                           "WHERE pi.InvoiceDate BETWEEN ? AND ?", a, b)
        matched, var = d.q(f"SELECT SUM(pil.Quantity * pil.UnitCost), SUM(pil.Quantity * (pil.UnitCost - pol.UnitCost)) {lines}", a, b)[0]
        rates.append(dict(year=y, right=var / matched, wrong=var / everything))
    claim(all(r["wrong"] < r["right"] for r in rates), "dividing by the amount of every invoice line understates the rate in each year")
    return dict(right=right, right_ids=", ".join(str(r[0]) for r in right), all_desc_ids=", ".join(str(r[0]) for r in all_desc), unfav_ids=", ".join(str(r[0]) for r in unfav), all_desc=all_desc, unfav=unfav, no_desc=no_desc, all_year=all_year, unfav_total=unfav_total, net=net, like_fav=like_fav,
                n_suppliers=n_suppliers, top_share=top_share, line_total=line_total, unequal=unequal, tolerance=tolerance, n_all=n_all,
                unmatched=unmatched, rates=rates, postings=postings)


# --- Exercise 10.5: referential integrity ----------------------------------------------------------------------------

@context("ch10.g5")
def g5(d, claim):
    need(d, claim, "GLEntry", "PayrollPayment", "Customer", "SalesOrder", "WorkOrder", "WorkOrderOperation", "LaborTimeEntry")
    anti = d.one("SELECT COUNT(*) FROM GLEntry gl LEFT JOIN PayrollPayment pp ON pp.PayrollPaymentID = gl.SourceDocumentID "
                 "WHERE gl.SourceDocumentType = 'PayrollPayment' AND pp.PayrollPaymentID IS NULL")
    no_type = d.one("SELECT COUNT(*) FROM GLEntry gl LEFT JOIN PayrollPayment pp ON pp.PayrollPaymentID = gl.SourceDocumentID WHERE pp.PayrollPaymentID IS NULL")
    claim(no_type > 1000 * anti, "without the document type, the anti-join flags every ledger row that is not a payroll payment")
    not_in = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'PayrollPayment' AND SourceDocumentID NOT IN (SELECT PayrollPaymentID FROM PayrollPayment)")
    claim(not_in == anti and d.one("SELECT COUNT(*) FROM PayrollPayment WHERE PayrollPaymentID IS NULL") == 0,
          "NOT IN gives the same rows here, because the payment key is never NULL")
    reverse = d.one("SELECT COUNT(*) FROM PayrollPayment pp WHERE NOT EXISTS (SELECT 1 FROM GLEntry gl WHERE gl.SourceDocumentType = 'PayrollPayment' "
                    "AND gl.SourceDocumentID = pp.PayrollPaymentID)")
    claim(reverse == 0, "every payroll payment has ledger rows, so the test finds nothing in the other direction")
    n_pay = d.one("SELECT COUNT(*) FROM PayrollPayment")
    active = rows(d, "SELECT c.CustomerID FROM Customer c LEFT JOIN SalesOrder so ON so.CustomerID = c.CustomerID WHERE so.SalesOrderID IS NULL AND c.IsActive = 1")
    claim(active == 0, "filtering the customers without orders to the active ones finds none")
    n_inactive = d.one("SELECT COUNT(*) FROM Customer WHERE IsActive = 0")
    n_without = d.one("SELECT COUNT(*) FROM Customer c WHERE NOT EXISTS (SELECT 1 FROM SalesOrder so WHERE so.CustomerID = c.CustomerID)")
    claim(n_inactive == n_without, "the inactive customers are exactly the customers with no orders")
    no_ops = [r[0] for r in d.q("SELECT wo.WorkOrderNumber FROM WorkOrder wo LEFT JOIN WorkOrderOperation op ON op.WorkOrderID = wo.WorkOrderID "
                                "WHERE op.WorkOrderOperationID IS NULL ORDER BY 1")]
    wo_labor = d.q("SELECT COUNT(*), ROUND(SUM(lt.RegularHours + lt.OvertimeHours), 2), SUM(lt.WorkOrderOperationID IS NULL) FROM LaborTimeEntry lt "
                   "WHERE lt.WorkOrderID IN (SELECT wo.WorkOrderID FROM WorkOrder wo LEFT JOIN WorkOrderOperation op ON op.WorkOrderID = wo.WorkOrderID "
                   "WHERE op.WorkOrderOperationID IS NULL)")[0]
    orphans = d.one("SELECT COUNT(*) FROM LaborTimeEntry lt LEFT JOIN WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID "
                    "WHERE lt.WorkOrderOperationID IS NOT NULL AND op.WorkOrderOperationID IS NULL")
    no_filter = d.one("SELECT COUNT(*) FROM LaborTimeEntry lt LEFT JOIN WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID "
                      "WHERE op.WorkOrderOperationID IS NULL")
    key_null = d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE WorkOrderOperationID IS NULL")
    entry_null_direct = d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE WorkOrderOperationID IS NULL AND LaborType = ?", DIRECT)
    claim(no_filter == orphans + key_null and orphans > 0 and entry_null_direct > 0,
          "the anti-join without the IS NOT NULL test returns the orphaned keys and every entry with no key at all")
    claim(wo_labor[2] == wo_labor[0] - orphans and wo_labor[2] > 0,
          "of the time recorded on the work orders without operations, all but one entry carry an orphaned key and one has no key at all")
    claim(d.one("SELECT COUNT(*) FROM LaborTimeEntry lt LEFT JOIN WorkOrderOperation op ON op.WorkOrderOperationID = lt.WorkOrderOperationID "
                "LEFT JOIN WorkOrder wo ON wo.WorkOrderID = lt.WorkOrderID WHERE lt.WorkOrderOperationID IS NOT NULL AND op.WorkOrderOperationID IS NULL "
                "AND wo.WorkOrderID IS NULL") == 0,
          "the orphaned entries still point to existing work orders")
    return dict(anti=anti, reverse=reverse, no_type=no_type, not_in=not_in, n_pay=n_pay, active=active, n_inactive=n_inactive, no_ops=no_ops, wo_labor_n=wo_labor[0],
                wo_labor_hours=wo_labor[1], wo_labor_nokey=wo_labor[2], orphans=orphans, no_filter=no_filter, key_null=key_null, entry_null_direct=entry_null_direct)


# --- Exercise 10.6: suppliers that share an employee's address ---------------------------------------------------------

@context("ch10.g6")
def g6(d, claim):
    need(d, claim, "Supplier", "Employee", "PurchaseInvoice", "DisbursementPayment", "Customer")
    end = f"{d.C}-12-31"
    matches = d.q("SELECT s.SupplierID FROM Supplier s JOIN Employee e ON e.Address = s.Address ORDER BY 1")
    loose = d.one("SELECT COUNT(*) FROM Supplier s JOIN Employee e ON LOWER(TRIM(e.Address)) = LOWER(TRIM(s.Address))")
    claim(loose == len(matches), "a join that ignores capitals and surrounding spaces finds the same matches as the exact join")
    first = matches[0][0]
    inv = d.q("SELECT COUNT(*), ROUND(SUM(GrandTotal), 2) FROM PurchaseInvoice WHERE SupplierID = ? AND InvoiceDate <= ?", first, end)[0]
    pay = d.q("SELECT COUNT(*), ROUND(SUM(Amount), 2) FROM DisbursementPayment WHERE SupplierID = ? AND PaymentDate <= ?", first, end)[0]
    one_query = d.q("SELECT COUNT(*), ROUND(SUM(pi.GrandTotal), 2) FROM PurchaseInvoice pi JOIN DisbursementPayment dp ON dp.SupplierID = pi.SupplierID "
                    "WHERE pi.SupplierID = ? AND pi.InvoiceDate <= ? AND dp.PaymentDate <= ?", first, end, end)[0]
    claim(one_query[0] == inv[0] * pay[0], "a join of one supplier's invoices to its payments on the supplier returns every invoice paired with every payment")
    by_invoice = d.q("SELECT COUNT(*), COUNT(DISTINCT pi.PurchaseInvoiceID), ROUND(SUM(pi.GrandTotal), 2) FROM PurchaseInvoice pi "
                     "JOIN DisbursementPayment dp ON dp.PurchaseInvoiceID = pi.PurchaseInvoiceID WHERE pi.SupplierID = ? AND pi.InvoiceDate <= ? "
                     "AND dp.PaymentDate <= ?", first, end, end)[0]
    claim(by_invoice[2] > inv[1] and by_invoice[0] > by_invoice[1],
          "joined on the invoice key, a partly paid invoice appears once for each payment, so its total is counted more than once")
    claim(by_invoice[1] < inv[0], "joined on the invoice key, the invoices with no payment through the year-end drop out")
    late = d.q("SELECT COUNT(*), SUM(PaymentDate > ?) FROM DisbursementPayment WHERE SupplierID = ?", end, first)[0]
    claim(late[1] > 0, "the supplier has payments dated after the year-end, which a missing date condition adds")
    from notes.ch10 import capital_invoices
    s5 = d.one("SELECT SupplierID FROM PurchaseInvoice WHERE PurchaseInvoiceID = ?", capital_invoices(d)[0])
    claim(s5 in [m[0] for m in matches], "the invoices the Debt Reclass entries moved belong to one of the matching suppliers")
    open_ = d.q("SELECT COUNT(*), ROUND(SUM(b), 2) FROM (SELECT pi.GrandTotal - COALESCE((SELECT SUM(p.Amount) FROM DisbursementPayment p "
                "WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID AND p.PaymentDate <= ?1), 0) AS b FROM PurchaseInvoice pi "
                "WHERE pi.SupplierID = ?2 AND pi.InvoiceDate <= ?1) WHERE b > 0.005", end, s5)[0]
    naive = d.q("SELECT COUNT(*), ROUND(SUM(pi.GrandTotal - COALESCE(dp.Amount, 0)), 2) FROM PurchaseInvoice pi LEFT JOIN DisbursementPayment dp "
                "ON dp.PurchaseInvoiceID = pi.PurchaseInvoiceID AND dp.PaymentDate <= ?1 WHERE pi.SupplierID = ?2 AND pi.InvoiceDate <= ?1", end, s5)[0]
    claim(naive[1] != open_[1], "a left join of invoices to their payments, subtracting each payment row by row, gives a different open amount, because a partly paid invoice repeats")
    shared = d.q("SELECT CustomerName, CustomerSegment FROM Customer GROUP BY CustomerName, CustomerSegment HAVING COUNT(*) > 1")
    names = d.q("SELECT CustomerName FROM Customer GROUP BY CustomerName HAVING COUNT(*) > 1")
    claim(len(shared) == len(names) - 1, "grouping by name and segment finds one shared name fewer than grouping by name, because one name's customers are in different segments")
    cust_emp = rows(d, "SELECT 1 FROM Customer c JOIN Employee e ON e.Address = c.Address")
    cust_sup = rows(d, "SELECT 1 FROM Customer c JOIN Supplier s ON s.Address = c.Address")
    claim(cust_emp == 0 and cust_sup == 0, "no customer shares an address with an employee or a supplier")
    return dict(cust_emp=cust_emp, cust_sup=cust_sup, first=first, inv_n=inv[0], inv_total=inv[1], pay_n=pay[0], pay_total=pay[1], one_n=one_query[0], one_total=one_query[1],
                by_invoice_n=by_invoice[0], by_invoice_distinct=by_invoice[1], by_invoice_total=by_invoice[2], late_n=late[0], late_after=late[1],
                s5=s5, naive_n=naive[0], naive_open=naive[1], n_names=len(names), n_name_seg=len(shared), seg_name=shared[0][0], loose=loose)
