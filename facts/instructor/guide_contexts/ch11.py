"""Chapter 11's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 11 teaches the analytical features of SQLite (CASE, date functions, conditional aggregation, window functions,
common table expressions and views), so the guides do three jobs, as Chapters 9 and 10 did:

- they supply the values the tutorials' checkpoints show (the monthly pivot, the gap in account 1090, the monthly measure
  and its view), which no registered note covers,
- they supply what each exercise's steps need beyond its registered note (ch11.ex1 to ch11.ex6): above all the result of
  each wrong variant a guide names (an ELSE left out, a window filtered in WHERE, a LAG with the wrong partition, a
  strftime year compared with a number, a Weekend test written with integers), run read-only, so the symptom a guide
  describes is the symptom the data gives,
- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll flags the wording instead of leaving it stale.

Keys: ch11.chapter (the chapter note and its three tutorials) and ch11.g1 to ch11.g6 (the exercises; each is used next to
the registered note ch11.ex1 to ch11.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter11-exercises-sql (Ex 11.1.sql to Ex 11.6.sql).

The SQL a guide quotes is the solution scripts' own text (the check verifies it); the numbers beside it come from here.
The variants below are fast on the dataset's indexes (the ledger is read by AccountID or by the one-table counts).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list, rows

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "11-analytical-queries"
DECK = REPO / "slides" / "chapter-11" / "index.qmd"
DIRECT, INDIRECT, NONMFG = "Direct Manufacturing", "Indirect Manufacturing", "NonManufacturing"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]

SCHEMA = {
    "PayrollRegisterLine": ["PayrollRegisterID", "LineType", "Amount"],
    "PayrollRegister": ["PayrollRegisterID", "PayrollPeriodID", "CostCenterID"],
    "PayrollPeriod": ["PayrollPeriodID", "FiscalYear"],
    "CostCenter": ["CostCenterID", "CostCenterName"],
    "GLEntry": ["PostingDate", "AccountID", "Debit", "Credit", "FiscalYear", "FiscalPeriod", "VoucherNumber",
                "SourceDocumentType"],
    "Account": ["AccountID", "AccountNumber", "AccountType", "AccountSubType"],
    "JournalEntry": ["EntryNumber", "EntryType", "PostingDate", "TotalAmount", "CreatedByEmployeeID", "CreatedDate",
                     "ApprovedByEmployeeID"],
    "LaborTimeEntry": ["EmployeeID", "WorkDate", "LaborType", "RegularHours", "OvertimeHours", "WorkOrderOperationID"],
    "WorkOrder": ["ReleasedDate", "CompletedDate", "ClosedDate"],
    "WorkOrderOperation": ["WorkOrderOperationID", "WorkCenterID", "PlannedLoadHours", "ActualEndDate"],
    "WorkCenter": ["WorkCenterID", "WorkCenterName"],
    "ProductionCompletion": ["ProductionCompletionID", "CompletionDate"],
    "ProductionCompletionLine": ["ProductionCompletionID", "ItemID", "QuantityCompleted"],
    "Item": ["ItemID", "ItemGroup", "ItemCode", "ListPrice", "StandardCost", "StandardLaborHoursPerUnit"],
    "Employee": ["EmployeeID", "JobTitle", "MaxApprovalAmount"],
    "PurchaseRequisition": ["RequisitionID", "RequisitionNumber", "RequestDate", "RequestedByEmployeeID",
                            "ApprovedByEmployeeID", "Status", "Quantity", "EstimatedUnitCost"],
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
    comment = source.note_comment("chapters/11-analytical-queries/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 11\b")
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


def error_of(d, sql: str) -> str:
    """The message SQLite gives for a statement that fails ('' when it runs)."""
    try:
        d.con.execute(sql).fetchall()
    except sqlite3.Error as exc:
        return str(exc)
    return ""


def year_bounds(year: int) -> tuple[str, str]:
    return f"{year}-01-01", f"{year}-12-31"


# the pieces of the monthly measure (Tutorial 11.3) and its variants
OUTPUT = """MonthlyOutput AS (
    SELECT strftime('%Y-%m', pc.CompletionDate) AS Month,
        SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit) AS StandardHours
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
    {cut}
    GROUP BY Month
)"""
CUTOFF = "WHERE pc.CompletionDate <= (SELECT MAX(WorkDate) FROM LaborTimeEntry)"
HOURS = """MonthlyHours AS (
    SELECT strftime('%Y-%m', WorkDate) AS Month,
        SUM(CASE LaborType WHEN 'Direct Manufacturing' THEN RegularHours + OvertimeHours ELSE 0 END) AS DirectHours,
        SUM(CASE LaborType WHEN 'Indirect Manufacturing' THEN RegularHours + OvertimeHours ELSE 0 END) AS IndirectHours,
        SUM(OvertimeHours) AS OvertimeHours
    FROM LaborTimeEntry
    WHERE LaborType <> 'NonManufacturing'
    GROUP BY Month
)"""
SEPARATE_HOURS = """MonthlyHours AS (
    SELECT dt.Month, dt.DirectHours, it.IndirectHours, dt.OvertimeHours + it.OvertimeHours AS OvertimeHours
    FROM (SELECT strftime('%Y-%m', WorkDate) AS Month, SUM(RegularHours + OvertimeHours) AS DirectHours,
            SUM(OvertimeHours) AS OvertimeHours
        FROM LaborTimeEntry WHERE LaborType = 'Direct Manufacturing' GROUP BY Month) AS dt
        INNER JOIN (SELECT strftime('%Y-%m', WorkDate) AS Month, SUM(RegularHours + OvertimeHours) AS IndirectHours,
            SUM(OvertimeHours) AS OvertimeHours
        FROM LaborTimeEntry WHERE LaborType = 'Indirect Manufacturing' GROUP BY Month) AS it ON it.Month = dt.Month
)"""
MONTHLY = """Monthly AS (
    SELECT o.Month, o.StandardHours, h.DirectHours, h.IndirectHours, h.OvertimeHours
    FROM MonthlyOutput AS o INNER JOIN MonthlyHours AS h ON h.Month = o.Month
)"""
TRAILING = """Trailing AS (
    SELECT Month,
        ROUND((DirectHours + IndirectHours) / StandardHours, 2) AS HoursPerStandardHour,
        ROUND(SUM(DirectHours) OVER w / SUM(StandardHours) OVER w, 2) AS TTMDirect,
        ROUND(SUM(IndirectHours) OVER w / SUM(StandardHours) OVER w, 2) AS TTMIndirect,
        ROUND(SUM(DirectHours + IndirectHours) OVER w / SUM(StandardHours) OVER w, 2) AS TTMTotal,
        ROUND(SUM(OvertimeHours) OVER w / SUM(DirectHours + IndirectHours) OVER w, 3) AS TTMOvertimeShare,
        COUNT(*) OVER w AS MonthsInWindow
    FROM Monthly
    WINDOW w AS (ORDER BY Month ROWS BETWEEN {frame} AND CURRENT ROW)
)"""
FINAL = ("SELECT Month, HoursPerStandardHour, TTMDirect, TTMIndirect, TTMTotal, TTMOvertimeShare FROM Trailing "
         "WHERE MonthsInWindow {cond} ORDER BY Month")


def measure(d, cut=CUTOFF, frame="11 PRECEDING", cond="= 12", hours=HOURS):
    sql = "WITH " + ",\n".join([OUTPUT.format(cut=cut), hours, MONTHLY, TRAILING.format(frame=frame)]) + "\n" + FINAL.format(cond=cond)
    return d.q(sql)


def step_rows(d, step: str, hours=HOURS) -> int:
    """The rows of one CTE of the chain, run on its own (Tutorial 11.3, Steps 1 to 3)."""
    parts = {"output": [OUTPUT.format(cut=CUTOFF)], "hours": [hours], "monthly": [OUTPUT.format(cut=CUTOFF), hours, MONTHLY]}
    name = {"output": "MonthlyOutput", "hours": "MonthlyHours", "monthly": "Monthly"}[step]
    return rows(d, "WITH " + ",\n".join(parts[step]) + f" SELECT * FROM {name}")


# --- Tutorial 11.1 ---------------------------------------------------------------------------------------------------

PAYROLL = """FROM PayrollRegisterLine AS prl
    INNER JOIN PayrollRegister AS pr ON pr.PayrollRegisterID = prl.PayrollRegisterID
    INNER JOIN PayrollPeriod AS pp ON pp.PayrollPeriodID = pr.PayrollPeriodID
    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
WHERE cc.CostCenterName = 'Manufacturing' AND pp.FiscalYear = ?"""


def tutorial_111(d, claim) -> dict:
    case = {
        "model": """CASE WHEN prl.LineType IN ('Regular Earnings', 'Overtime Earnings') THEN 'Hourly pay'
            WHEN prl.LineType = 'Salary Earnings' THEN 'Salaries'
            WHEN prl.LineType IN ('Employer Payroll Tax', 'Employer Benefits') THEN 'Employer taxes and benefits'
            ELSE 'Employee deductions' END""",
        "no_else": """CASE WHEN prl.LineType IN ('Regular Earnings', 'Overtime Earnings') THEN 'Hourly pay'
            WHEN prl.LineType = 'Salary Earnings' THEN 'Salaries'
            WHEN prl.LineType IN ('Employer Payroll Tax', 'Employer Benefits') THEN 'Employer taxes and benefits' END""",
        "broad_first": """CASE WHEN prl.LineType LIKE '%Earnings' THEN 'Hourly pay'
            WHEN prl.LineType = 'Salary Earnings' THEN 'Salaries'
            WHEN prl.LineType IN ('Employer Payroll Tax', 'Employer Benefits') THEN 'Employer taxes and benefits'
            ELSE 'Employee deductions' END""",
    }

    def by_category(kind):
        return dict(d.q(f"SELECT {case[kind]} AS Category, ROUND(SUM(prl.Amount), 2) {PAYROLL} GROUP BY Category", d.C))

    good, no_else, broad = by_category("model"), by_category("no_else"), by_category("broad_first")
    ledger = d.one("SELECT ROUND(SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'PayrollSummary'",
                   d.account("1090"), d.C)
    costs = round(good["Hourly pay"] + good["Salaries"] + good["Employer taxes and benefits"], 2)
    claim(set(good) == {"Hourly pay", "Salaries", "Employer taxes and benefits", "Employee deductions"},
          "the seven payroll line types fall into the four categories of the CASE")
    claim(abs(costs - ledger) < 0.005, "the three cost categories add up to the payroll the ledger charged to 1090, to the cent")
    claim(None in no_else and abs(no_else[None] - good["Employee deductions"]) < 0.005,
          "without an ELSE the deductions fall into a group whose name is NULL")
    claim("Salaries" not in broad and broad["Hourly pay"] > good["Hourly pay"],
          "a LIKE '%Earnings' condition placed first swallows the salary lines into hourly pay")

    pivot = d.q("""SELECT strftime('%Y-%m', lt.WorkDate) AS WorkMonth, COUNT(DISTINCT lt.WorkDate),
        ROUND(SUM(CASE lt.LaborType WHEN 'Direct Manufacturing' THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0),
        ROUND(SUM(CASE lt.LaborType WHEN 'Indirect Manufacturing' THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END), 0),
        ROUND(SUM(lt.OvertimeHours), 0)
        FROM LaborTimeEntry AS lt WHERE lt.LaborType <> 'NonManufacturing' GROUP BY WorkMonth ORDER BY WorkMonth""")
    claim(len(pivot) == 12 * len(d.years), "the pivot has one row for every month of the window")
    first = pivot[0]
    claim(first[3] > first[2], "the start-up month records more indirect than direct hours")
    quiet = pivot[1:5]
    claim(max(q[3] for q in quiet) < min(p[3] for p in pivot[5:]), "indirect time in the four months after the start-up month is below every later month")
    zero = [p[0] for p in pivot if p[3] == 0]
    claim(zero == [pivot[2][0]], "exactly one month, the third of the window, has no indirect hours")
    all_types = dict(d.q("SELECT strftime('%Y-%m', WorkDate), ROUND(SUM(OvertimeHours), 0) FROM LaborTimeEntry GROUP BY 1"))
    claim(all_types[pivot[0][0]] > pivot[0][4], "without the LaborType filter the overtime column counts non-manufacturing hours too")
    lo, hi = year_bounds(d.C)
    ot_year = d.one("SELECT ROUND(SUM(OvertimeHours), 0) FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' AND WorkDate BETWEEN ? AND ?", lo, hi)
    ot_year_all = d.one("SELECT ROUND(SUM(OvertimeHours), 0) FROM LaborTimeEntry WHERE WorkDate BETWEEN ? AND ?", lo, hi)

    last = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    month_end, short = d.q("SELECT date(MAX(WorkDate), 'start of month', '+1 month', '-1 day'), julianday(date(MAX(WorkDate), 'start of month', '+1 month', '-1 day')) - julianday(MAX(WorkDate)) FROM LaborTimeEntry")[0]
    no_start, no_start_days = d.q("SELECT date(MAX(WorkDate), '+1 month', '-1 day'), julianday(date(MAX(WorkDate), '+1 month', '-1 day')) - julianday(MAX(WorkDate)) FROM LaborTimeEntry")[0]
    claim(short > 0 and month_end[:7] == last[:7], "the time records end before the last day of their month")
    claim(no_start > month_end, "without 'start of month' the date lands in the next month")
    jan31 = d.one("SELECT date('2026-01-31', '+1 month')")
    claim(jan31 == "2026-03-03", "adding a month to January 31 lands on March 3")
    n_text = d.one("SELECT COUNT(*) FROM WorkOrder WHERE strftime('%Y', ClosedDate) = ?", str(d.C))
    n_num = d.one("SELECT COUNT(*) FROM WorkOrder WHERE strftime('%Y', ClosedDate) = ?", d.C)
    claim(n_text > 0 and n_num == 0, "a strftime year compared with a number finds no rows, and compared with text finds the year's closes")

    shares = d.q("""SELECT strftime('%Y-%m', lt.WorkDate) AS m,
        SUM(CASE lt.LaborType WHEN 'Direct Manufacturing' THEN lt.OvertimeHours ELSE 0 END) / SUM(CASE lt.LaborType WHEN 'Direct Manufacturing' THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END),
        SUM(CASE lt.LaborType WHEN 'Indirect Manufacturing' THEN lt.OvertimeHours ELSE 0 END) / SUM(CASE lt.LaborType WHEN 'Indirect Manufacturing' THEN lt.RegularHours + lt.OvertimeHours ELSE 0 END)
        FROM LaborTimeEntry lt WHERE lt.LaborType <> 'NonManufacturing' GROUP BY m ORDER BY m""")
    h1 = [s[1] for s in shares[:6]]
    last_year = [s for s in shares if s[0][:4] == str(d.C)]
    high = [s for s in last_year if s[1] >= 0.25]
    dips = [(MONTHS[int(s[0][5:]) - 1], s[1]) for s in last_year if s[1] < 0.25]
    claim(max(h1) < 0.12 and len(high) >= 9 and 1 <= len(dips) <= 3,
          "direct overtime is about a tenth or less in the first half of the first year and a quarter or more in most months of the last, with a few dips")
    ind = [s[2] for s in shares if s[2] is not None]
    claim(max(ind) < 0.12 and min(ind) > 0.05, "indirect overtime stays between a twentieth and an eighth of its hours")
    claim([s[0] for s in shares if s[2] is None] == [pivot[2][0]], "only the month with no indirect hours has a NULL indirect share")

    lead = d.q("""SELECT strftime('%Y', ClosedDate), COUNT(*), ROUND(AVG(julianday(CompletedDate) - julianday(ReleasedDate)), 1),
        ROUND(AVG(julianday(ClosedDate) - julianday(CompletedDate)), 1) FROM WorkOrder WHERE ClosedDate IS NOT NULL GROUP BY 1 ORDER BY 1""")
    claim(len(lead) == len(d.years) and lead[-1][2] > 2 * lead[0][2] and max(r[3] for r in lead) < 1.1 * min(r[3] for r in lead),
          "release to completion more than doubles across the window while completion to close stays about the same")
    # Step 5's dates checked before the averages are read (review SQL D): one closed work order is completed before its
    # release, and leaving it out does not move its year's average at one decimal.
    neg = d.q("SELECT strftime('%Y', ClosedDate), julianday(CompletedDate) - julianday(ReleasedDate) FROM WorkOrder "
              "WHERE ClosedDate IS NOT NULL AND (CompletedDate < ReleasedDate OR ClosedDate < CompletedDate)")
    no_dates = d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate IS NOT NULL AND (ReleasedDate IS NULL OR CompletedDate IS NULL)")
    neg_year = neg[0][0] if neg else None
    without = d.one("SELECT ROUND(AVG(julianday(CompletedDate) - julianday(ReleasedDate)), 1) FROM WorkOrder "
                    "WHERE strftime('%Y', ClosedDate) = ? AND CompletedDate >= ReleasedDate", neg_year) if neg else None
    claim(len(neg) == 1 and no_dates == 0 and without == next(r[2] for r in lead if r[0] == neg_year),
          "one closed work order has a completion date before its release date, none lacks a date, and leaving it out does not move its year's average")
    return dict(neg_days=int(neg[0][1]) if neg else 0, neg_year=neg_year,
        hourly=good["Hourly pay"], salaries=good["Salaries"], employer=good["Employer taxes and benefits"],
        deductions=good["Employee deductions"], ledger=ledger, null_group=no_else[None], broad_hourly=broad["Hourly pay"],
        broad_n=len(broad), n_months=len(pivot), first=pivot[0], quiet=quiet, quiet_low=min(q[3] for q in quiet),
        quiet_high=max(q[3] for q in quiet), zero_month=zero[0], days_last=pivot[-1][1], overtime_first=pivot[0][4],
        overtime_first_all=all_types[pivot[0][0]], ot_year=ot_year, ot_year_all=ot_year_all, last=last, month_end=month_end,
        short=int(short), no_start=no_start, no_start_days=int(no_start_days), jan31=jan31, n_text=n_text, n_num=n_num,
        h1_low=min(h1), h1_high=max(h1), n_high=len(high), dips=dips, ind_low=min(ind), ind_high=max(ind), lead=lead)


# --- Tutorial 11.2 ---------------------------------------------------------------------------------------------------

GAP_WHERE = "WHERE AccountID = ? AND FiscalYear BETWEEN ? AND ? AND SourceDocumentType <> 'WorkOrderClose'"


def tutorial_112(d, claim) -> dict:
    cl = d.account("1090")
    gap = d.q(f"""SELECT FiscalYear, FiscalPeriod, ROUND(SUM(Debit) - SUM(Credit), 2),
        ROUND(SUM(SUM(Debit) - SUM(Credit)) OVER (PARTITION BY FiscalYear ORDER BY FiscalPeriod), 2),
        ROUND(LAG(SUM(Debit) - SUM(Credit)) OVER (PARTITION BY FiscalPeriod ORDER BY FiscalYear), 2),
        ROUND(LAG(SUM(Debit) - SUM(Credit)) OVER (ORDER BY FiscalYear, FiscalPeriod), 2)
        FROM GLEntry {GAP_WHERE} GROUP BY FiscalYear, FiscalPeriod ORDER BY 1, 2""", cl, d.F, d.C)
    claim(len(gap) == 12 * len(d.years), "the gap has one row for every month of the window")
    by = {(r[0], r[1]): r for r in gap}
    dec = [by[(y, 12)] for y in d.years]
    claim(all(a[3] < b[3] for a, b in zip(dec, dec[1:])) and dec[-1][3] > 1.8 * dec[0][3],
          "the December year-to-date gap grows in each year and ends the window at nearly twice its first value")
    claim(all(by[(d.F, m)][4] is None for m in range(1, 13)), "the same-month comparison is NULL for every month of the first year")
    claim(by[(d.F, 1)][5] is None and by[(d.C, 1)][5] == by[(d.P, 12)][2], "a LAG with no partition compares January with the December before it")
    jul, aug = by[(d.C, 7)], by[(d.C, 8)]
    jul_ratio, aug_ratio = jul[2] / jul[4], aug[2] / aug[4]
    claim(2.5 < jul_ratio < 3.2 and 0.45 < aug_ratio < 0.6, "July of the last year is nearly three times the July before it and August about half of its August")
    rank_msgs = [error_of(d, "SELECT FiscalYear, RANK() OVER (ORDER BY SUM(Debit) - SUM(Credit)) AS GapRank FROM GLEntry WHERE GapRank <= 3 GROUP BY FiscalYear"),
                 error_of(d, "SELECT FiscalYear, RANK() OVER (ORDER BY SUM(Debit) - SUM(Credit)) AS GapRank FROM GLEntry WHERE RANK() OVER (ORDER BY SUM(Debit) - SUM(Credit)) <= 3 GROUP BY FiscalYear")]
    claim(all(m.startswith("misuse of") for m in rank_msgs), "SQLite rejects a window function, or its alias, in a WHERE clause with a 'misuse of' message")
    top = d.q(f"""SELECT FiscalYear, FiscalPeriod, Gap, PayDates, GapRank FROM (
        SELECT FiscalYear, FiscalPeriod, ROUND(SUM(Debit) - SUM(Credit), 2) AS Gap,
            COUNT(DISTINCT CASE WHEN SourceDocumentType = 'PayrollSummary' THEN PostingDate END) AS PayDates,
            RANK() OVER (PARTITION BY FiscalYear ORDER BY SUM(Debit) - SUM(Credit) DESC) AS GapRank
        FROM GLEntry {GAP_WHERE} GROUP BY FiscalYear, FiscalPeriod) AS monthly WHERE GapRank <= 3 ORDER BY FiscalYear, GapRank""",
                cl, d.F, d.C)
    claim(len(top) == 3 * len(d.years) and all(t[3] == 3 for t in top if t[4] == 1), "the largest month of every year has three pay dates")
    pay = d.q("""SELECT FiscalYear, FiscalPeriod, COUNT(DISTINCT PostingDate) FROM GLEntry WHERE AccountID = ? AND FiscalYear BETWEEN ? AND ?
        AND SourceDocumentType = 'PayrollSummary' GROUP BY 1, 2 ORDER BY 1, 2""", cl, d.F, d.C)
    three = {y: [MONTHS[m - 1] for yy, m, n in pay if yy == y and n == 3] for y in d.years}
    totals = {y: sum(n for yy, _, n in pay if yy == y) for y in d.years}
    claim(all(len(v) == 2 for v in three.values()), "every year has two months with three pay dates")
    claim(totals[d.F] + 2 == totals[d.P] == totals[d.C], "the first year has two pay dates fewer than each later year")
    claim(not any(yy == d.F and m == 1 for yy, m, _ in pay), "the first month of the window has no payroll posted to 1090")

    centers = """SELECT strftime('%Y', op.ActualEndDate) AS EndYear, wc.WorkCenterName, SUM(op.PlannedLoadHours) AS PlannedHours, SUM(lab.Hours) AS RecordedHours
        FROM WorkOrderOperation AS op INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = op.WorkCenterID
        {join} JOIN (SELECT WorkOrderOperationID, SUM(RegularHours + OvertimeHours) AS Hours FROM LaborTimeEntry
            WHERE LaborType = 'Direct Manufacturing' GROUP BY WorkOrderOperationID) AS lab ON lab.WorkOrderOperationID = op.WorkOrderOperationID
        {cut} GROUP BY EndYear, wc.WorkCenterName"""
    cut = "WHERE op.ActualEndDate <= (SELECT MAX(WorkDate) FROM LaborTimeEntry)"
    wc = d.q(f"SELECT EndYear, WorkCenterName, ROUND(RecordedHours - PlannedHours, 0), ROUND(RecordedHours / PlannedHours, 2), "
             f"RANK() OVER (PARTITION BY EndYear ORDER BY RecordedHours / PlannedHours DESC), "
             f"ROUND(SUM(RecordedHours - PlannedHours) OVER (PARTITION BY EndYear), 0) "
             f"FROM ({centers.format(join='LEFT', cut=cut)}) ORDER BY EndYear, 5")
    last = [r for r in wc if r[0] == str(d.C)]
    claim(len(wc) == 5 * len(d.years) and last[0][1].startswith("Packing") and last[1][1].startswith("Quality"),
          "Packing and Quality Assurance rank first and second in the last year")
    claim(all(r[3] > 3 for r in last[:2]) and all(r[3] < 1 for r in last[2:]), "the last year's top two centers record several times their plan and the other three under it")
    claim(all(r[5] < 0 for r in wc), "the plant as a whole records fewer direct hours than planned in every year")

    def ratio(sql, year, name):
        return next(r[2] for r in d.q(sql) if r[0] == str(year) and r[1].startswith(name))

    inner = f"SELECT EndYear, WorkCenterName, ROUND(RecordedHours / PlannedHours, 2) FROM ({centers.format(join='INNER', cut=cut)})"
    fan = ("SELECT strftime('%Y', op.ActualEndDate), wc.WorkCenterName, ROUND(SUM(lt.RegularHours + lt.OvertimeHours) / SUM(op.PlannedLoadHours), 2) "
           "FROM WorkOrderOperation AS op INNER JOIN WorkCenter AS wc ON wc.WorkCenterID = op.WorkCenterID "
           "LEFT JOIN LaborTimeEntry AS lt ON lt.WorkOrderOperationID = op.WorkOrderOperationID AND lt.LaborType = 'Direct Manufacturing' "
           f"{cut} GROUP BY 1, 2")
    nocut = f"SELECT EndYear, WorkCenterName, ROUND(RecordedHours / PlannedHours, 2) FROM ({centers.format(join='LEFT', cut='')})"
    pk, qa = ratio(inner, d.C, "Packing"), ratio(inner, d.C, "Quality")
    pk_fan, qa_fan = ratio(fan, d.C, "Packing"), ratio(fan, d.C, "Quality")
    pk_nocut = ratio(nocut, d.C, "Packing")
    claim(pk > last[0][3] and qa > last[1][3], "an inner join to the labor summary raises the ratios, because operations with no direct time leave the plan out")
    claim(pk_fan < 0.7 * last[0][3] and qa_fan < 0.7 * last[1][3], "joining the labor entries straight to the operations repeats the planned hours and cuts both ratios to under seven-tenths of the model's")
    n_null_year = rows(d, f"SELECT 1 FROM ({centers.format(join='LEFT', cut='')}) WHERE EndYear IS NULL")
    after_cut = d.one("SELECT COUNT(*) FROM WorkOrderOperation WHERE ActualEndDate > (SELECT MAX(WorkDate) FROM LaborTimeEntry)")
    claim(n_null_year > 0 and after_cut > 0 and pk_nocut != last[0][3],
          "without the cut-off, operations with no end date form a group of their own and the last year's ratio moves")
    # The cohort's record quality (review SQL C): operations counted with no direct time, and with direct time dated after
    # the operation ended (the late time Chapter 12 tests).
    quality = d.q("""SELECT strftime('%Y', op.ActualEndDate), COUNT(*), SUM(CASE WHEN lab.Last IS NULL THEN 1 ELSE 0 END),
        SUM(CASE WHEN lab.Last > op.ActualEndDate THEN 1 ELSE 0 END)
        FROM WorkOrderOperation AS op LEFT JOIN (SELECT WorkOrderOperationID, MAX(WorkDate) AS Last FROM LaborTimeEntry
            WHERE LaborType = 'Direct Manufacturing' GROUP BY WorkOrderOperationID) AS lab ON lab.WorkOrderOperationID = op.WorkOrderOperationID
        WHERE op.ActualEndDate <= (SELECT MAX(WorkDate) FROM LaborTimeEntry) GROUP BY 1 ORDER BY 1""")
    q_last = quality[-1]
    claim(all(r[2] > 0.25 * r[1] and 0 < r[3] < r[2] for r in quality),
          "in every year many counted operations have no direct time and some have direct time dated after they ended")
    firsts = [(t[0], MONTHS[t[1] - 1], t[2], t[3]) for t in top if t[4] == 1]
    three_text = [f"{y}: {and_list(m)}" for y, m in three.items()]
    return dict(ops_last=q_last[1], ops_no_time=q_last[2], ops_late=q_last[3], firsts=firsts, three_text=three_text, ytd=[(y, by[(y, 12)][2], by[(y, 12)][3]) for y in d.years], jul=jul, jul_ratio=jul_ratio, aug_ratio=aug_ratio,
                prev_jul=jul[5], prev_jan=by[(d.C, 1)][5], msg_alias=rank_msgs[0], msg_direct=rank_msgs[1], top=top, three=three,
                totals=totals, wc=wc, last=last, plant=[(y, next(r[5] for r in wc if r[0] == str(y))) for y in d.years],
                packing_inner=pk, qa_inner=qa, packing_fan=pk_fan, qa_fan=qa_fan, packing_nocut=pk_nocut,
                n_null_year=n_null_year, after_cut=after_cut)


# --- Tutorial 11.3 ---------------------------------------------------------------------------------------------------

def tutorial_113(d, claim) -> dict:
    n_out, n_hours, n_monthly = step_rows(d, "output"), step_rows(d, "hours"), step_rows(d, "monthly")
    claim(n_out == n_hours == n_monthly == 12 * len(d.years), "each step of the chain returns one row for every month of the window")
    view = measure(d)
    partial = measure(d, cond="< 12")
    claim(len(view) == 12 * len(d.years) - 11 and len(partial) == 11, "the view keeps the months with a full window and the partial windows are the first eleven")
    decs = [r for r in view if r[0].endswith("-12")]
    claim(len(decs) == len(d.years) - 1 + 1 and [r[0][:4] for r in decs] == [str(y) for y in d.years],
          "the view has a December row for every year of the window")
    claim(all(a[2] <= b[2] for a, b in zip(decs, decs[1:])) and decs[0][3] < decs[1][3] <= decs[2][3] + 0.05,
          "the trailing direct ratio creeps up and the indirect ratio rises and then levels off")
    peak = max(view, key=lambda r: r[4])
    claim(peak[0] == f"{d.C}-10", "the trailing total ratio peaks in October of the last year")
    settled = [r[3] for r in view if r[0] >= f"{d.P}-06"]
    claim(max(settled) - min(settled) < 0.1, "from mid-way through the second year the trailing indirect ratio stays within a tenth of an hour")
    last = view[-1]
    nocut = measure(d, cut="")
    nc_last = nocut[-1]
    claim(nc_last[1] < 0.8 * last[1] and nc_last[4] < last[4], "counting the output to the end of the year lowers the last month's ratio sharply and the trailing total a little")
    sep = measure(d, hours=SEPARATE_HOURS)
    sep_monthly = rows(d, "WITH " + ",\n".join([OUTPUT.format(cut=CUTOFF), SEPARATE_HOURS, MONTHLY]) + " SELECT * FROM Monthly")
    claim(sep_monthly == n_monthly - 1 and len(sep) == len(view) - 1, "summarizing indirect time in a step of its own drops the one month with none, and the view loses a row")
    f13 = measure(d, frame="12 PRECEDING")
    claim(len(f13) < len(view) // 5, "a frame of twelve rows back holds thirteen months, and the filter on twelve keeps almost nothing")
    avg = d.q("WITH " + ",\n".join([OUTPUT.format(cut=CUTOFF), HOURS, MONTHLY]) + """, R AS (SELECT Month, (DirectHours + IndirectHours) / StandardHours AS r FROM Monthly)
        SELECT Month, ROUND(AVG(r) OVER (ORDER BY Month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW), 2) FROM R""")
    avg_last = next(a[1] for a in avg if a[0] == last[0])
    claim(avg_last != last[4], "the average of twelve monthly ratios differs from the pooled trailing ratio")
    view_sql = "CREATE TEMP VIEW MonthlyLaborEfficiency AS WITH " + ",\n".join([OUTPUT.format(cut=CUTOFF), HOURS, MONTHLY, TRAILING.format(frame="11 PRECEDING")]) \
        + "\n" + FINAL.format(cond="= 12").rsplit(" ORDER BY", 1)[0]
    d.con.execute(view_sql)
    try:
        again = error_of(d, view_sql)
        via_view = rows(d, "SELECT * FROM MonthlyLaborEfficiency WHERE Month BETWEEN ? AND ?", f"{d.C}-01", f"{d.C}-12")
    finally:
        d.con.execute("DROP VIEW IF EXISTS temp.MonthlyLaborEfficiency")
    claim("already exists" in again, "creating the view a second time without a DROP fails with 'already exists'")
    claim(via_view == 12, "the view returns the twelve months of the last year")
    # Coverage (decision N3): the last row's direct time and output end on the last day with time records, its indirect
    # time a week earlier. The labeled sensitivity stops hours and output alike at the last day of indirect time; the
    # tutorial keeps its view and calls the row provisional.
    cut_day = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    ind_end = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry WHERE LaborType = ?", INDIRECT)
    claim(d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry WHERE LaborType = ?", DIRECT) == cut_day and ind_end < cut_day
          and ind_end[:7] == cut_day[:7], "direct time ends on the last day with time records and indirect time earlier in the same month")
    common = measure(d, cut=f"WHERE pc.CompletionDate <= '{ind_end}'",
                     hours=HOURS.replace("WHERE LaborType <> 'NonManufacturing'",
                                         f"WHERE LaborType <> 'NonManufacturing' AND WorkDate <= '{ind_end}'"))
    c_last = common[-1]
    claim(common[:-1] == view[:-1] and c_last[0] == last[0], "counting both sides to the last day of indirect time changes only the last row")
    claim(c_last[2] < last[2] and c_last[3] >= last[3] and c_last[4] < last[4],
          "counted to that day, the last row's direct ratio is lower, its indirect ratio no lower and its total lower")
    n_round = sum(1 for r in view if abs(r[2] + r[3] - r[4]) > 0.001)
    claim(0 < n_round < len(view), "in some rows the two rounded ratios do not add to the rounded total")
    first_partial = partial[0]
    comma_msg = error_of(d, "WITH MonthlyOutput AS (SELECT 1 AS Month) MonthlyHours AS (SELECT 1 AS Month) SELECT * FROM MonthlyHours")
    claim(comma_msg.startswith("near"), "a missing comma between two CTEs ends in a syntax error that begins 'near'")
    claim(first_partial[4] > 5 * view[0][4], "the start-up month's partial window reads many times any full window")
    return dict(n_out=n_out, n_hours=n_hours, n_monthly=n_monthly, n_view=len(view), n_partial=len(partial), first_full=view[0][0],
                first_partial=first_partial, decs=decs, peak=peak, settled_low=min(settled), settled_high=max(settled), last=last,
                nc_last=nc_last, sep_monthly=sep_monthly, sep_view=len(sep), sep_first=sep[0][0], f13_rows=len(f13),
                avg_last=avg_last, again=again, via_view=via_view, comma_msg=comma_msg,
                cut_day=cut_day, ind_end=ind_end, c_last=c_last, n_round=n_round)


# --- the chapter note --------------------------------------------------------------------------------------------------

def peers_demo(d, claim) -> dict:
    """The default window against ROWS UNBOUNDED PRECEDING, on the Furniture standard hours that the chapter ranks."""
    sql = """SELECT ItemCode, StandardLaborHoursPerUnit,
        ROUND(SUM(StandardLaborHoursPerUnit) OVER (ORDER BY StandardLaborHoursPerUnit DESC), 2) AS DefaultTotal,
        ROUND(SUM(StandardLaborHoursPerUnit) OVER (ORDER BY StandardLaborHoursPerUnit DESC ROWS UNBOUNDED PRECEDING), 2) AS FrameTotal,
        RANK() OVER (ORDER BY StandardLaborHoursPerUnit DESC) AS Rnk,
        ROW_NUMBER() OVER (ORDER BY StandardLaborHoursPerUnit DESC) AS RowNum
        FROM Item WHERE ItemGroup = 'Furniture' ORDER BY StandardLaborHoursPerUnit DESC, ItemCode LIMIT 10"""
    top = d.q(sql)
    tied = [i for i in range(1, len(top)) if top[i][1] == top[i - 1][1]]
    claim(len(tied) >= 2 and tied[0] >= 6, "the first ties in the Furniture standard hours come after the sixth row")
    a = tied[0]
    claim(top[a][2] == top[a - 1][2] and top[a][3] != top[a - 1][3] and top[a][4] == top[a - 1][4] and top[a][5] != top[a - 1][5],
          "tied rows share the default running total and the rank, and differ under ROWS and in ROW_NUMBER")
    return dict(pair_row=a, pair_hours=top[a][1], pair_default=top[a][2], pair_frame=(top[a - 1][3], top[a][3]),
                pair_rank=top[a][4], pair_nums=(top[a - 1][5], top[a][5]), n_pairs=len(tied) // 1)


@context("ch11.chapter")
def chapter(d, claim):
    need(d, claim, *SCHEMA)
    t1, t2, t3 = tutorial_111(d, claim), tutorial_112(d, claim), tutorial_113(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 15, "the chapter has fifteen multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    peers = peers_demo(d, claim)
    n_close = d.one("SELECT COUNT(*) FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%'")
    month_end_entries = d.one("SELECT COUNT(*) FROM JournalEntry WHERE PostingDate = date(PostingDate, 'start of month', '+1 month', '-1 day')")
    claim(0 < month_end_entries < d.one("SELECT COUNT(*) FROM JournalEntry"), "some but not all journal entries are posted on a month-end")
    n_year_text = d.one("SELECT COUNT(*) FROM JournalEntry WHERE strftime('%Y', PostingDate) = ?", str(d.C))
    n_year_num = d.one("SELECT COUNT(*) FROM JournalEntry WHERE strftime('%Y', PostingDate) = ?", d.C)
    claim(n_year_num == 0 < n_year_text, "a strftime year compared with a number finds no journal entries, and with text finds the year's")
    return dict(f=d.F, p=d.P, y=d.C, n=d.N, n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(),
                n_questions=n_q, longest_correct=and_list(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3, peers=peers,
                n_year_text=n_year_text, n_year_num=n_year_num, month_end_entries=month_end_entries, n_close=n_close, version="3.13.1")


# --- Exercise 11.1: the statements from the ledger ----------------------------------------------------------------------

LINE_CASE = """CASE
    WHEN AccountType = 'Revenue' AND AccountSubType = 'Operating Revenue' THEN 'Operating revenue'
    WHEN AccountType = 'Revenue' AND AccountSubType = 'Contra Revenue' THEN 'Contra revenue'
    WHEN AccountType = 'Expense' AND AccountSubType = 'COGS' THEN 'Cost of goods sold'
    WHEN AccountType = 'Expense' AND AccountSubType = 'Operating Expense' THEN 'Operating expenses'
    WHEN AccountType IN ('Revenue', 'Expense') THEN 'Other income and expense'
    WHEN AccountType = 'Asset' AND AccountSubType IN ('Current Asset', 'Contra Current Asset') THEN 'Current assets'
    WHEN AccountType = 'Asset' AND AccountSubType = 'Fixed Asset' THEN 'Fixed assets'
    WHEN AccountType = 'Asset' AND AccountSubType = 'Contra Fixed Asset' THEN 'Contra fixed assets'
    WHEN AccountType = 'Liability' AND AccountSubType = 'Current Liability' THEN 'Current liabilities'
    WHEN AccountType = 'Liability' AND AccountSubType = 'Long-Term Liability' THEN 'Long-term liabilities'
    WHEN AccountType = 'Equity' THEN 'Equity'
    ELSE 'Unassigned' END"""
CATCH_ALL = "WHEN AccountType IN ('Revenue', 'Expense') THEN 'Other income and expense'"


def statement(d, asof: str, closes: str, date: bool = True, case: str = LINE_CASE, flip: bool = True) -> dict:
    """The statement lines of a variant of the model query, and the totals the exercise derives from them."""
    where = (f"gl.PostingDate <= '{asof}'" if date else "1 = 1") + (f" AND gl.VoucherNumber NOT IN ({closes})" if closes else "")
    sign = "CASE WHEN AccountType = 'Asset' THEN -Balance ELSE Balance END" if flip else "Balance"
    lines = dict(d.q(f"""WITH TrialBalance AS (SELECT a.AccountType, a.AccountSubType, ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance
        FROM GLEntry AS gl INNER JOIN Account AS a ON a.AccountID = gl.AccountID WHERE {where} GROUP BY a.AccountID, a.AccountType, a.AccountSubType)
        SELECT {case} AS StatementLine, SUM({sign}) AS Amount FROM TrialBalance GROUP BY StatementLine"""))
    g = lambda k: lines.get(k, 0.0)       # noqa: E731
    net_revenue = g("Operating revenue") + g("Contra revenue")
    gm = net_revenue + g("Cost of goods sold")
    oi = gm + g("Operating expenses")
    ni = oi + g("Other income and expense")
    assets = g("Current assets") + g("Fixed assets") + g("Contra fixed assets")
    return dict(lines=lines, n_lines=len(lines), net_revenue=round(net_revenue, 2), gm=round(gm, 2), ni=round(ni, 2),
                assets=round(assets, 2), equity=round(g("Equity"), 2), gm_pct=(gm / net_revenue if net_revenue else None))


@context("ch11.g1")
def g1(d, claim):
    need(d, claim, "JournalEntry", "GLEntry", "Account")
    asof = f"{d.C}-12-31"
    closes = d.closes_of(d.C)
    claim(len(closes) == 2, "the as-of date has two closing entries")
    quoted = ",".join(f"'{c}'" for c in closes)
    all_closes = ",".join(f"'{c}'" for c in d.closes)
    good = statement(d, asof, quoted)
    claim(good["n_lines"] == 11 and "Unassigned" not in good["lines"], "the model CASE assigns every account to one of the eleven statement lines")
    n_contra_current = d.one("SELECT COUNT(DISTINCT a.AccountID) FROM GLEntry gl JOIN Account a ON a.AccountID = gl.AccountID "
                             "WHERE a.AccountSubType = 'Contra Current Asset' AND gl.PostingDate <= ?", asof)
    claim(n_contra_current == 0, "no account of the Contra Current Asset subtype has a posting, so that branch of the CASE assigns nothing")
    n_accounts, net = d.q("SELECT COUNT(*), ROUND(SUM(Balance), 2) FROM (SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance FROM GLEntry gl "
                          f"WHERE gl.PostingDate <= ? AND gl.VoucherNumber NOT IN ({quoted}) GROUP BY gl.AccountID)", asof)[0]
    claim(abs(net) < 0.005, "the pre-closing balances net to zero")
    in_ = statement(d, asof, "")
    claim(abs(in_["ni"]) < 0.005 and in_["equity"] > good["equity"], "with the closes left in, the revenue and expense lines are zero and the equity line holds the year's income")
    claim(abs(in_["assets"] - good["assets"]) < 0.005, "the balance sheet does not change when the closes are left in")
    every = statement(d, asof, all_closes)
    claim(every["ni"] > 2.5 * good["ni"], "leaving out every year's closes accumulates the income of all the years in the revenue and expense lines")
    nodate = statement(d, asof, quoted, date=False)
    late = d.one("SELECT COUNT(*) FROM GLEntry WHERE PostingDate > ?", asof)
    claim(late > 0 and nodate["assets"] != good["assets"] and abs(nodate["ni"] - good["ni"]) < 0.005,
          "ledger rows dated after the as-of date change the balance sheet and leave the income statement alone")
    first = statement(d, asof, quoted, case=LINE_CASE.replace("CASE\n", "CASE\n    " + CATCH_ALL + "\n", 1))
    claim(first["net_revenue"] == 0 and first["gm_pct"] is None and abs(first["ni"] - good["ni"]) < 0.005,
          "a catch-all branch for revenue and expense accounts placed first leaves net revenue at zero and the percentages NULL, and net income right")
    raw = statement(d, asof, quoted, flip=False)
    claim(raw["assets"] == -good["assets"], "without the sign flip, total assets read as a negative number")
    retained = d.one("SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) FROM GLEntry gl JOIN Account a ON a.AccountID = gl.AccountID "
                     "WHERE a.AccountNumber = 3030 AND gl.VoucherNumber = ?", closes[-1])
    claim(abs(retained - good["ni"]) < 0.005, "the second closing entry moves the year's net income to retained earnings")
    other = round(good["lines"]["Other income and expense"], 2)
    credits = d.one("SELECT ROUND(SUM(CASE WHEN Balance > 0 THEN Balance ELSE 0 END), 2) FROM (SELECT SUM(gl.Credit) - SUM(gl.Debit) AS Balance FROM GLEntry gl "
                    f"WHERE gl.PostingDate <= ? AND gl.VoucherNumber NOT IN ({quoted}) GROUP BY gl.AccountID)", asof)
    p_asof = f"{d.P}-12-31"
    p_closes = d.closes_of(d.P)
    p_good = statement(d, p_asof, ",".join(f"'{c}'" for c in p_closes))
    p_retained = d.one("SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) FROM GLEntry gl JOIN Account a ON a.AccountID = gl.AccountID "
                       "WHERE a.AccountNumber = 3030 AND gl.VoucherNumber = ?", p_closes[-1])
    claim(len(p_closes) == 2 and abs(p_retained - p_good["ni"]) < 0.005, "the model query, run for the prior year-end, gives that year's net income, equal to its closing entry")
    wrong_gm = round(good["net_revenue"] - good["lines"]["Cost of goods sold"], 2)
    cash_after = d.one("SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? AND PostingDate > ?", d.account("1010"), asof)
    claim(abs(cash_after - (good["assets"] - nodate["assets"])) < 0.005 and d.one("SELECT COUNT(DISTINCT SourceDocumentType) FROM GLEntry WHERE PostingDate > ?", asof) == 1,
          "the ledger rows after the as-of date are one kind of document, and the cash they credit is what the dropped date takes out of total assets")
    n_closes = len(d.closes)
    claim(n_closes > len(closes), "closing entries of other years exist besides the as-of date's two")
    return dict(n_closes=n_closes, asof=asof, credits=credits, p_asof=p_asof, p_ni=p_good["ni"], p_close=p_closes[-1], wrong_gm=wrong_gm, n_accounts=n_accounts, n_lines=good["n_lines"], other=other, closed_equity=in_["equity"], closed_ni=abs(in_["ni"]),
                every_ni=every["ni"], late=late, nodate_assets=nodate["assets"], nodate_diff=round(good["assets"] - nodate["assets"], 2),
                first_net_revenue=first["net_revenue"], first_n_lines=first["n_lines"], raw_assets=raw["assets"], retained=retained,
                n_view_lines=17, n_contra_current=n_contra_current)


# --- Exercise 11.2: monthly revenue ---------------------------------------------------------------------------------------

MONTHLY_REVENUE = """SELECT gl.FiscalYear, gl.FiscalPeriod, a.AccountNumber,
    CASE a.AccountNumber WHEN 4010 THEN 'Furniture' WHEN 4020 THEN 'Lighting' WHEN 4030 THEN 'Textiles'
        WHEN 4040 THEN 'Accessories' WHEN 4080 THEN 'Services' END AS ProductLine,
    SUM(gl.Credit) - SUM(gl.Debit) AS Revenue
FROM GLEntry AS gl INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE a.AccountNumber IN (4010, 4020, 4030, 4040, 4080) AND gl.FiscalYear BETWEEN {lo} AND {hi} {closes}
GROUP BY gl.FiscalYear, gl.FiscalPeriod, a.AccountNumber"""


@context("ch11.g2")
def g2(d, claim):
    need(d, claim, "GLEntry", "Account", "JournalEntry")
    base = MONTHLY_REVENUE.format(lo=d.F, hi=d.C, closes="AND gl.VoucherNumber NOT IN (SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%')")
    withc = MONTHLY_REVENUE.format(lo=d.F, hi=d.C, closes="")
    n_rows = rows(d, base)
    claim(n_rows == 5 * 12 * len(d.years), "the monthly report has one row for each of five product lines and each month of the window")
    furn = lambda sql, year, month: d.q(f"SELECT * FROM ({sql}) WHERE ProductLine = 'Furniture' AND FiscalYear = ? AND FiscalPeriod = ?", year, month)[0]  # noqa: E731
    in_dec = d.q(f"""SELECT FiscalYear, ROUND(Revenue, 2), YTD FROM (SELECT ProductLine, FiscalYear, FiscalPeriod, Revenue,
        ROUND(SUM(Revenue) OVER (PARTITION BY ProductLine, FiscalYear ORDER BY FiscalPeriod), 2) AS YTD FROM ({withc}))
        WHERE ProductLine = 'Furniture' AND FiscalPeriod = 12 ORDER BY 1""")
    claim(all(r[1] < 0 and abs(r[2]) < 0.005 for r in in_dec), "with the closes left in, December's revenue is a large negative figure and the December year to date is zero")
    cum = d.q(f"""SELECT FiscalYear, YTD FROM (SELECT ProductLine, FiscalYear, FiscalPeriod,
        ROUND(SUM(Revenue) OVER (PARTITION BY ProductLine ORDER BY FiscalYear, FiscalPeriod), 2) AS YTD FROM ({base}))
        WHERE ProductLine = 'Furniture' AND FiscalPeriod = 12 ORDER BY 1""")
    ytd_ok = d.q(f"""SELECT FiscalYear, YTD FROM (SELECT ProductLine, FiscalYear, FiscalPeriod,
        ROUND(SUM(Revenue) OVER (PARTITION BY ProductLine, FiscalYear ORDER BY FiscalPeriod), 2) AS YTD FROM ({base}))
        WHERE ProductLine = 'Furniture' AND FiscalPeriod = 12 ORDER BY 1""")
    claim(cum[-1][1] > 2.5 * ytd_ok[-1][1], "a year to date that is not partitioned by year accumulates every year of the window")
    lag = f"""SELECT ProductLine, FiscalYear, FiscalPeriod, ROUND(Revenue, 2) AS Revenue, {{lag}} AS PriorYear FROM ({base}) {{where}}"""
    right = d.q(lag.format(lag="ROUND(LAG(Revenue) OVER (PARTITION BY ProductLine, FiscalPeriod ORDER BY FiscalYear), 2)", where=""))
    r = {(a[0], a[1], a[2]): a for a in right}
    oct_now, oct_before = r[("Furniture", d.C, 10)][3], r[("Furniture", d.C, 10)][4]
    month_lag = d.q(lag.format(lag="ROUND(LAG(Revenue) OVER (PARTITION BY ProductLine ORDER BY FiscalYear, FiscalPeriod), 2)", where=""))
    ml = {(a[0], a[1], a[2]): a for a in month_lag}
    prev_month = ml[("Furniture", d.C, 10)][4]
    claim(prev_month == r[("Furniture", d.C, 9)][3] and prev_month != oct_before, "a LAG ordered by year and period compares October with September")
    nopart = d.q(lag.format(lag="ROUND(LAG(Revenue) OVER (PARTITION BY FiscalPeriod ORDER BY FiscalYear), 2)", where=""))
    wrong_line = next(a[4] for a in nopart if a[:3] == ("Furniture", d.C, 10))
    furniture_values = {round(a[3], 2) for a in right if a[0] == "Furniture"}
    claim(wrong_line != oct_before and wrong_line not in furniture_values,
          "a LAG with no product-line partition compares Furniture with a figure that belongs to another product line")
    filtered = d.q(f"""SELECT ROUND(LAG(Revenue) OVER (PARTITION BY ProductLine, FiscalPeriod ORDER BY FiscalYear), 2) FROM ({base})
        WHERE ProductLine = 'Furniture' AND FiscalYear = ?""", d.C)
    claim(all(f[0] is None for f in filtered) and len(filtered) == 12, "a year filter in the same SELECT as the LAG leaves every prior year NULL")
    n_num = d.one("SELECT COUNT(*) FROM GLEntry WHERE strftime('%Y', PostingDate) = ?", d.C)
    claim(n_num == 0, "a strftime year compared with a number finds no ledger rows")
    chg = [(m, r[("Furniture", d.C, m)][3], r[("Furniture", d.C, m)][4]) for m in range(1, 13)]
    by_pct = sorted(chg, key=lambda c: c[1] / c[2] - 1)
    by_amt = sorted(chg, key=lambda c: c[1] - c[2])
    claim(by_pct[0][0] == by_amt[0][0] and by_pct[-1][0] == by_amt[-1][0], "the largest decline and increase are the same months in dollars and in percent")
    rank_down = by_pct[0][0]
    tb = d.q("""SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) FROM GLEntry gl JOIN Account a ON a.AccountID = gl.AccountID
        WHERE a.AccountNumber IN (4010, 4020, 4030, 4040, 4080) AND gl.PostingDate <= ? AND gl.VoucherNumber NOT IN (%s)""" % ",".join(f"'{c}'" for c in d.closes_of(d.C)),
             f"{d.C}-12-31")[0][0]
    return dict(n_rows=n_rows, prev_month=prev_month, prev_month_sep=r[("Furniture", d.C, 9)][3], wrong_line=wrong_line, cum=cum[-1][1],
                in_dec=in_dec[-1], n_num=n_num, tb=tb, oct_pct=(oct_now / oct_before - 1), down_month=MONTHS[rank_down - 1],
                y=d.C, null_years=rows(d, f"SELECT 1 FROM ({base}) WHERE FiscalYear = {d.F}"))


# --- Exercise 11.3: ranking items ---------------------------------------------------------------------------------------

MARGINS = """SELECT ItemGroup, ItemCode, ItemName, ListPrice, StandardCost, ROUND(ListPrice - StandardCost, 2) AS UnitMargin,
    ROUND(100.0 * (ListPrice - StandardCost) / ListPrice, 1) AS MarginPct FROM Item WHERE ListPrice IS NOT NULL"""


@context("ch11.g3")
def g3(d, claim):
    need(d, claim, "Item")
    n = d.one(f"SELECT COUNT(*) FROM ({MARGINS})")
    n_all = d.one("SELECT COUNT(*) FROM Item")
    unpriced = d.q("SELECT ItemGroup, COUNT(*) FROM Item WHERE ListPrice IS NULL GROUP BY 1 ORDER BY 1")
    claim(n_all > n and len(unpriced) >= 3, "the item table holds items with no list price, in several groups, that the filter leaves out")
    by_margin = d.one(f"SELECT COUNT(*) FROM (SELECT RANK() OVER w AS r, ROW_NUMBER() OVER w AS rn FROM ({MARGINS}) WINDOW w AS (PARTITION BY ItemGroup ORDER BY UnitMargin DESC)) WHERE r <> rn")
    claim(by_margin == 0, "ranked by unit margin, RANK and ROW_NUMBER agree on every item")
    pct = d.q(f"""SELECT ItemGroup, ItemCode, MarginPct, RANK() OVER w, DENSE_RANK() OVER w, ROW_NUMBER() OVER w FROM ({MARGINS})
        WINDOW w AS (PARTITION BY ItemGroup ORDER BY MarginPct DESC)""")
    differ = sum(1 for r in pct if not (r[3] == r[4] == r[5]))
    top3_rank = sum(1 for r in pct if r[3] <= 3)
    top3_row = sum(1 for r in pct if r[5] <= 3)
    extra = [g for g in sorted({r[0] for r in pct}) if sum(1 for r in pct if r[0] == g and r[3] <= 3) > 3]
    claim(differ > n // 2 and top3_rank > top3_row and top3_row == 3 * len({r[0] for r in pct}),
          "ranked by the rounded margin percentage, ties are common: the three functions disagree on most items and RANK keeps more than three in a group")
    claim(len(extra) >= 1, "at least one item group has a tie at the third rank when ranked by margin percentage")
    msg = error_of(d, f"SELECT ItemGroup, RANK() OVER (PARTITION BY ItemGroup ORDER BY UnitMargin DESC) AS MarginRank FROM ({MARGINS}) WHERE MarginRank <= 3")
    claim(msg.startswith("misuse of"), "a rank used in the WHERE clause of its own SELECT is rejected with a 'misuse of' message")
    low = d.q(f"""SELECT COUNT(*), SUM(UnitMargin = GroupLowest) FROM (SELECT UnitMargin,
        MIN(UnitMargin) OVER (PARTITION BY ItemGroup ORDER BY UnitMargin DESC) AS GroupLowest FROM ({MARGINS}))""")[0]
    claim(low[0] == low[1] == n, "a MIN over an ordered window runs only to the current row, so it reads the row's own margin on every item")
    whole = d.one(f"SELECT COUNT(DISTINCT m) FROM (SELECT MAX(UnitMargin) OVER () AS m FROM ({MARGINS}))")
    grouped = rows(d, f"SELECT ItemGroup, MAX(UnitMargin) FROM ({MARGINS}) GROUP BY ItemGroup")
    claim(whole == 1 and grouped < n, "a window with no partition returns one value on every row, and GROUP BY collapses the items")
    services = d.q(f"SELECT COUNT(*), MAX(StandardCost), MIN(MarginPct), MAX(MarginPct) FROM ({MARGINS}) WHERE ItemGroup = 'Services'")[0]
    claim(services[1] == 0 and services[2] == services[3] == 100.0, "the Services items have a standard cost of zero and a margin of the whole price")
    return dict(n=n, n_all=n_all, unpriced=unpriced, n_unpriced=n_all - n, differ=differ, top3_rank=top3_rank, top3_row=top3_row,
                extra_groups=and_list(extra), msg=msg, services=services[0], n_groups=len({r[0] for r in pct}))


# --- Exercise 11.4: overtime ----------------------------------------------------------------------------------------------

OVERTIME = """SELECT lt.EmployeeID, e.JobTitle, SUM(lt.OvertimeHours) AS OT FROM LaborTimeEntry AS lt
    INNER JOIN Employee AS e ON e.EmployeeID = lt.EmployeeID
WHERE lt.LaborType {types} AND lt.WorkDate {dates} GROUP BY lt.EmployeeID, e.JobTitle {having}"""


@context("ch11.g4")
def g4(d, claim):
    need(d, claim, "LaborTimeEntry", "Employee")
    lo, hi = year_bounds(d.C)
    between = f"BETWEEN '{lo}' AND '{hi}'"
    having = "HAVING SUM(lt.OvertimeHours) > 0"
    good = OVERTIME.format(types="<> 'NonManufacturing'", dates=between, having=having)
    n, total = d.q(f"SELECT COUNT(*), SUM(OT) FROM ({good})")[0]
    no_having = rows(d, OVERTIME.format(types="<> 'NonManufacturing'", dates=between, having=""))
    claim(no_having == n, "every employee with manufacturing time in the year recorded some overtime, so the HAVING condition removes nobody")
    direct_n, direct_total = d.q(f"SELECT COUNT(*), SUM(OT) FROM ({OVERTIME.format(types=chr(61) + ' ' + repr(DIRECT), dates=between, having=having)})")[0]
    all_n, all_total = d.q(f"SELECT COUNT(*), SUM(OT) FROM ({OVERTIME.format(types='IS NOT NULL', dates=between, having=having)})")[0]
    claim(direct_total < total < all_total and all_n > n, "direct time alone gives fewer hours, and adding the non-manufacturing time adds employees and hours")
    num = rows(d, OVERTIME.format(types="<> 'NonManufacturing'", dates=f"IS NOT NULL AND strftime('%Y', lt.WorkDate) = {d.C}", having=""))
    claim(num == 0, "a strftime year compared with a number finds no time entries")
    ranked = d.q(f"SELECT EmployeeID, JobTitle, OT FROM ({good}) ORDER BY OT DESC, EmployeeID")
    tot = sum(r[2] for r in ranked)
    run, share = 0.0, []
    for r in ranked:
        run += r[2]
        share.append(run / tot)
    half = next(i for i, s in enumerate(share, 1) if s >= 0.5)
    claim(len({round(r[2], 6) for r in ranked}) == len(ranked), "no two employees have the same overtime total")
    ties = d.one(f"SELECT SUM(a <> b) FROM (SELECT SUM(OT) OVER (ORDER BY OT DESC ROWS UNBOUNDED PRECEDING) AS a, SUM(OT) OVER (ORDER BY OT DESC) AS b FROM ({good}))")
    claim(ties == 0, "with no ties, the default window and ROWS UNBOUNDED PRECEDING give the same running total")
    asc = d.q(f"SELECT SUM(OT) OVER (ORDER BY OT ROWS UNBOUNDED PRECEDING) / SUM(OT) OVER () FROM ({good}) ORDER BY OT")
    asc_half = next(i for i, r in enumerate(asc, 1) if r[0] >= 0.5)
    claim(asc_half == half + 1, "ordered from the lowest, one more employee is needed to reach half")
    claim(0.4 < share[half - 2] < 0.5 <= share[half - 1] < 0.55, "the running share reaches half at the employee the model answer names, and not before")
    entries = d.q("""SELECT e.JobTitle, ROUND(AVG(lt.OvertimeHours), 2) FROM LaborTimeEntry lt JOIN Employee e ON e.EmployeeID = lt.EmployeeID
        WHERE lt.LaborType <> 'NonManufacturing' AND lt.WorkDate BETWEEN ? AND ? GROUP BY 1 ORDER BY 1""", lo, hi)
    claim(all(e[1] < 2 for e in entries), "the average overtime of a time entry is about an hour, which is not the figure per employee")
    # Coverage (decision N3): indirect time ends a week before direct time, so the sensitivity stops both at the earlier day.
    ind_end = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry WHERE LaborType = ? AND WorkDate BETWEEN ? AND ?", INDIRECT, lo, hi)
    common = [r[2] for r in d.q(f"""{OVERTIME.format(types="<> 'NonManufacturing'", dates=f"BETWEEN '{lo}' AND '{ind_end}'",
                                                      having=having)} ORDER BY OT DESC, lt.EmployeeID""")]
    c_total, c_run = sum(common), 0.0
    for c_half, h in enumerate(common, 1):
        c_run += h
        if c_run >= c_total / 2:
            break
    claim(c_total < total and len(common) == n and abs(c_half - half) <= 1,
          "counted to the last day of indirect time, the year has fewer overtime hours, the same employees, and reaches half within one rank of the model")
    return dict(n=n, total=total, no_having=no_having, direct_n=direct_n, direct_total=direct_total, all_n=all_n, all_total=all_total,
                n_num=num, top5=share[4], top10=share[9], at_half=share[half - 1], before_half=share[half - 2], asc_half=asc_half,
                ties=ties, entry_low=min(e[1] for e in entries), entry_high=max(e[1] for e in entries),
                ind_end=ind_end, c_total=c_total, c_half=c_half)


# --- Exercise 11.5: journal entry tests ------------------------------------------------------------------------------------

FLAGS = """SELECT je.EntryNumber, je.EntryType, je.PostingDate, je.TotalAmount,
    {weekend} AS Weekend, {backdated} AS Backdated,
    CASE WHEN je.CreatedByEmployeeID = je.ApprovedByEmployeeID THEN 1 ELSE 0 END AS SelfApproved,
    CASE WHEN je.TotalAmount > {limit} THEN 1 ELSE 0 END AS AboveLimit,
    {round} AS RoundAmount
FROM JournalEntry AS je {join} Employee AS e ON e.EmployeeID = je.ApprovedByEmployeeID"""
WEEKEND = "CASE WHEN strftime('%w', je.CreatedDate) IN ('0', '6') THEN 1 ELSE 0 END"
BACKDATED = "CASE WHEN date(je.CreatedDate) > je.PostingDate THEN 1 ELSE 0 END"
ROUNDED = "CASE WHEN je.TotalAmount = ROUND(je.TotalAmount / 1000, 0) * 1000 THEN 1 ELSE 0 END"


@context("ch11.g5")
def g5(d, claim):
    need(d, claim, "JournalEntry", "Employee")

    def counts(**kw):
        a = dict(weekend=WEEKEND, backdated=BACKDATED, round=ROUNDED, join="LEFT JOIN", limit="e.MaxApprovalAmount")
        a.update(kw)
        return d.q(f"SELECT COUNT(*), SUM(Weekend), SUM(Backdated), SUM(SelfApproved), SUM(AboveLimit), SUM(RoundAmount) FROM ({FLAGS.format(**a)})")[0]

    model = counts()
    ints = counts(weekend="CASE WHEN strftime('%w', je.CreatedDate) IN (0, 6) THEN 1 ELSE 0 END")
    claim(model[1] > 0 and ints[1] == 0, "a Weekend test written with the integers 0 and 6 flags nothing, because strftime returns text")
    nodate = counts(backdated="CASE WHEN je.CreatedDate > je.PostingDate THEN 1 ELSE 0 END")
    n_time = d.one("SELECT COUNT(*) FROM JournalEntry WHERE length(CreatedDate) > 10")
    claim(n_time == model[0] and nodate[2] == model[0] and model[2] < model[0],
          "every CreatedDate carries a time, so comparing it with the posting date without date() flags every entry")
    modulo = counts(round="CASE WHEN je.TotalAmount % 1000 = 0 THEN 1 ELSE 0 END")
    claim(modulo[5] == model[5], "a % test flags the same entries as the ROUND test on this data, although % truncates the amount first")
    trunc = d.one("SELECT 5000.5 % 1000")
    claim(trunc == 0, "the % operator truncates 5000.5 to 5000 before dividing, so it reports a remainder of zero")
    inner = counts(join="INNER JOIN")
    zero_limit = counts(limit="COALESCE(e.MaxApprovalAmount, 0)")
    missing = d.one("SELECT COUNT(*) FROM JournalEntry WHERE ApprovedByEmployeeID IS NULL")
    data_missing = d.one("SELECT COUNT(*) FROM JournalEntry AS je LEFT JOIN Employee AS e ON e.EmployeeID = je.ApprovedByEmployeeID "
                         "WHERE e.EmployeeID IS NULL OR e.MaxApprovalAmount IS NULL")
    claim(missing == 0 and data_missing == 0 and inner == model == zero_limit,
          "every entry has an approver with a recorded limit, so an inner join, or a missing limit read as zero, would change nothing here")
    scored = f"SELECT *, Weekend + Backdated + SelfApproved + AboveLimit + RoundAmount AS RiskScore FROM ({FLAGS.format(weekend=WEEKEND, backdated=BACKDATED, round=ROUNDED, join='LEFT JOIN', limit='e.MaxApprovalAmount')})"
    ranked = d.q(f"""SELECT RANK() OVER (ORDER BY RiskScore DESC, TotalAmount DESC), EntryNumber, EntryType, TotalAmount, RiskScore FROM ({scored}) WHERE RiskScore >= 2 ORDER BY 1""")
    claim([r[0] for r in ranked] == list(range(1, len(ranked) + 1)), "ranking by score and then amount gives every entry its own rank")
    by_score = d.q(f"SELECT RANK() OVER (ORDER BY RiskScore DESC), COUNT(*) FROM ({scored}) WHERE RiskScore >= 2 GROUP BY RiskScore ORDER BY 1")
    claim(len(by_score) == 2 and by_score[1][1] > 1, "ranked by score alone, the entries at the second score all tie")
    outer = d.q(f"SELECT MIN(rk), MAX(rk) FROM (SELECT RiskScore, RANK() OVER (ORDER BY RiskScore DESC, TotalAmount DESC) AS rk FROM ({scored})) WHERE RiskScore >= 2")[0]
    claim(outer == (1, len(ranked)), "filtering on the score before or after the ranking gives the same ranks, because the score is not the ranking")
    approvers = d.q("SELECT e.JobTitle, e.MaxApprovalAmount, COUNT(*) FROM JournalEntry je JOIN Employee e ON e.EmployeeID = je.ApprovedByEmployeeID GROUP BY 1, 2 ORDER BY 3 DESC")
    return dict(model=model, ints=ints, nodate=nodate, n_time=n_time, trunc=trunc, modulo=modulo, ranked=ranked, n_ranked=len(ranked),
                tied=by_score[1][1], missing=missing, data_missing=data_missing, n_entries=model[0], approvers=approvers)


# --- Exercise 11.6: requisitions just under the limit ------------------------------------------------------------------------

AMOUNTS = ("SELECT RequisitionID, RequisitionNumber, RequestDate, RequestedByEmployeeID, ApprovedByEmployeeID, Status, "
           "ROUND(Quantity * EstimatedUnitCost, 2) AS Amount FROM PurchaseRequisition")


@context("ch11.g6")
def g6(d, claim):
    need(d, claim, "PurchaseRequisition", "Employee")
    n_all = d.one("SELECT COUNT(*) FROM PurchaseRequisition")
    band = d.one(f"SELECT COUNT(*) FROM ({AMOUNTS}) WHERE Amount BETWEEN 4950 AND 4999.99")
    unrounded = d.one("SELECT COUNT(*) FROM PurchaseRequisition WHERE Quantity * EstimatedUnitCost BETWEEN 4950 AND 4999.99")
    claim(band == unrounded, "rounding the amount to cents changes no requisition's band on this data")
    claim(d.one("SELECT COUNT(*) FROM PurchaseRequisition r LEFT JOIN Employee e ON e.EmployeeID = r.RequestedByEmployeeID WHERE e.EmployeeID IS NULL") == 0,
          "every requisition has a requester who is an employee, so an inner join to the requester drops none")
    inner = d.one(f"""SELECT COUNT(*) FROM ({AMOUNTS}) AS a INNER JOIN Employee AS rq ON rq.EmployeeID = a.RequestedByEmployeeID
        INNER JOIN Employee AS ap ON ap.EmployeeID = a.ApprovedByEmployeeID WHERE a.Amount BETWEEN 4950 AND 4999.99""")
    no_approver = d.one(f"SELECT COUNT(*) FROM ({AMOUNTS}) WHERE Amount BETWEEN 4950 AND 4999.99 AND ApprovedByEmployeeID IS NULL")
    claim(inner == band - no_approver and no_approver > 0, "an inner join to the approver drops exactly the requisitions that have none")
    runs = [4714, 4715, 4716, 13258, 13259, 13260]
    eq_null = d.one(f"SELECT SUM(CASE WHEN ApprovedByEmployeeID = NULL THEN 1 ELSE 0 END) FROM ({AMOUNTS}) WHERE RequisitionID IN ({','.join(map(str, runs))})")
    is_null = d.one(f"SELECT SUM(CASE WHEN ApprovedByEmployeeID IS NULL THEN 1 ELSE 0 END) FROM ({AMOUNTS}) WHERE RequisitionID IN ({','.join(map(str, runs))})")
    claim(eq_null == 0 and is_null == 4, "a test written = NULL counts none of the four unapproved requisitions of the runs")
    neighbors = f"SELECT RequisitionID, Amount, LAG(Amount) OVER (ORDER BY RequisitionID) AS PrevA, LEAD(Amount) OVER (ORDER BY RequisitionID) AS NextA FROM ({AMOUNTS})"
    both = [r[0] for r in d.q(f"SELECT RequisitionID FROM ({neighbors}) WHERE Amount = PrevA AND Amount = NextA")]
    prev_only = d.one(f"SELECT COUNT(*) FROM ({neighbors}) WHERE Amount = PrevA")
    claim(both == [4715, 13259] and prev_only > 2 * len(both), "requiring both neighbors keeps only the middle requisition of each run, and the previous neighbor alone finds more")
    joined = d.one(f"""WITH Neighbors AS ({neighbors}), Runs AS (SELECT RequisitionID AS MiddleID, RequisitionID - 1 AS PreviousID, RequisitionID + 1 AS NextID FROM Neighbors
        WHERE Amount = PrevA AND Amount = NextA) SELECT COUNT(*) FROM Runs r INNER JOIN ({AMOUNTS}) AS a ON a.RequisitionID BETWEEN r.PreviousID AND r.NextID""")
    claim(joined == 3 * len(both), "joining each middle row back to the rows between its neighbors lists every requisition of the run")
    group_titles = d.q(f"""SELECT GROUP_CONCAT(ap.JobTitle, ', ') FROM ({AMOUNTS}) AS a LEFT JOIN Employee AS ap ON ap.EmployeeID = a.ApprovedByEmployeeID
        WHERE a.RequisitionID IN (4714, 4715, 4716)""")[0][0]
    claim(group_titles == "Chief Financial Officer", "GROUP_CONCAT skips the NULL approvers, so a run's approver list shows only the one that exists")
    nocast = rows(d, f"SELECT 4700 + 50 * ((Amount - 4700) / 50) AS b FROM ({AMOUNTS}) WHERE Amount >= 4700 AND Amount < 5250 GROUP BY b")
    n_in_range = d.one(f"SELECT COUNT(*) FROM ({AMOUNTS}) WHERE Amount >= 4700 AND Amount < 5250")
    claim(nocast > 11, "without CAST to an integer, the division is real and each amount falls in a band of its own")
    limits = [r[0] for r in d.q("SELECT DISTINCT MaxApprovalAmount FROM Employee ORDER BY 1")]
    claim(limits[0] == 0 and 5000 in limits, "the approval limits start at zero and include 5,000, the threshold the exercise tests")
    return dict(limits_text=and_list([f"{x:,}" for x in limits]), n_all=n_all, band=band, inner=inner, no_approver=no_approver, eq_null=eq_null, is_null=is_null, prev_only=prev_only,
                nocast=nocast, n_in_range=n_in_range, joined=joined)
