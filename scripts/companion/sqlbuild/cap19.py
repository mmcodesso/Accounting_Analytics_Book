"""Credits.sql: the SQL part of the solution to the Chapter 19 capstone case ("Auditing the Customer Credits Cycle"),
instructor files.

The case gives SQL the map of the cycle, the reconciliations, and the control and substantive tests (tbl-19-02), and
hands the refund flags to Power BI as RefundFlags.csv. This script holds them in the order of the requirements, each
under the two comment lines of Chapter 12's audit library (what it tests; its population and expected result):

- Requirement 1, tests M1-M7: the data profile of the cycle's tables, the links tested both ways with anti-joins, the
  document numbers tested for gaps, the posting matrix by source document and account, and who records each document;
- Requirement 2, tests G1-G9: each population reconciled to the ledger by fiscal year, account 2060 rolled forward and
  its items named at each year-end, 2034 reconciled at the end of the base year, and the closes left out;
- Requirement 3, test P1: the ledger figures the planning workbook uses (income before income taxes, the return rate);
- Requirement 4, tests T1-T12: authority, employment dates, separation of duties, the preparer, refunds before payment
  and their cause, the clawbacks, one refund per credit, the refund flags exported as RefundFlags.csv (the query of
  pbibuild/cap19.py, which writes that file, imported verbatim), the four rule tests' exceptions in one list by year
  with UNION ALL, and the Accounting Manager's concentration;
- Requirement 6, tests K1-K2: the key items and the remainder the workbook samples;
- Requirement 7, tests S1-S6: the credits recomputed, the open items in 2060, restocking by reason, lapping, and the
  timeline of the largest refund;
- Requirement 10, test E1: the populations and rates per 1,000 of the register's four new tests.

Checks take their expected values from the notes' context functions and helpers (facts/notes/ch19.py, the values of
the generated instructor notes, which the twins scripts/verify/twins/ch19_twins.py reproduce) or from read-only SQL of
this module, and read their actual values from each query's result.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from pbibuild.cap19 import REFUND_FLAGS_SQL
from sqlbuild.script import Check

FILE = "Credits.sql"
DATABASE = "CharlesRiver_Capstone.sqlite (a copy of CharlesRiver.sqlite)"
CYCLE = ("SalesReturn", "CreditMemo", "CustomerRefund", "SalesCommissionAdjustment", "CashReceipt",
         "CashReceiptApplication")
SOURCES = ",\n    ".join(f"'{s}'" for s in CYCLE)
CLOSES = """\
    AND gl.VoucherNumber NOT IN (
        SELECT EntryNumber
        FROM JournalEntry
        WHERE EntryType LIKE 'Year-End Close%')"""
TESTS = ("CM AboveLimit", "CM CashAndCredit", "RF AboveLimit", "RF BeforePayment")


def notes(b):
    b.data                                       # puts facts/ on sys.path
    from notes import ch19
    return ch19


def context(b, name: str) -> dict:
    return getattr(notes(b), name)(b.data, lambda *a, **k: None)


def script(b):
    d = b.data
    return b.script(FILE, f"the customer credits cycle, fiscal {d.F} to {d.C}: map, reconciliations, and tests",
                    "each population against the ledger by year; every link both ways; document numbers for gaps; "
                    "authority, separation, and timing of credits and refunds; the credits recomputed; lapping",
                    database=DATABASE)


def money(x: float) -> str:
    return f"{x:,.2f}"


def by_year(rows, year_col: str, years, value=None) -> list:
    out = [0 if value is None else 0.0 for _ in years]
    for r in rows:
        y = r[year_col]
        if y in years:
            out[years.index(y)] += 1 if value is None else r[value]
    return [round(x, 2) if isinstance(x, float) else x for x in out]


def dicts(r) -> list[dict]:
    return [dict(zip(r.columns, row)) for row in r.rows]


def remember(b, key: str, q) -> None:
    if not hasattr(b, "_cap19_queries"):
        b._cap19_queries = {}
    b._cap19_queries[key] = q


def recall(b, key: str):
    return b._cap19_queries[key]


# --- Requirement 1 -----------------------------------------------------------------------------------------------

def r1(b):
    d, n = b.data, notes(b)
    v = context(b, "r1")
    c = n.cycle(d)
    s = script(b)
    rows = {"SalesReturn": (len(c.sr), v["sr"]["first"], v["sr"]["last"], v["sr"]["customers"], None),
            "SalesReturnLine": (v["sr"]["lines"], None, None, None,
                                d.one("SELECT ROUND(SUM(ExtendedStandardCost), 2) FROM SalesReturnLine")),
            "CreditMemo": (v["cm"]["n"], v["cm"]["first"], v["cm"]["last"], len({m["cust"] for m in c.cm.values()}),
                           v["cm"]["total"]),
            "CreditMemoLine": (v["cm"]["lines"], None, None, None,
                               d.one("SELECT ROUND(SUM(LineTotal), 2) FROM CreditMemoLine")),
            "CustomerRefund": (v["rf"]["n"], v["rf"]["first"], v["rf"]["last"],
                               len({r["cust"] for r in c.rf.values()}), v["rf"]["total"]),
            "SalesCommissionAdjustment": (v["cb"]["n"], None, None, None, v["cb"]["total"]),
            "CashReceipt": (v["receipts"], None, None, None, v["receipt_total"]),
            "CashReceiptApplication": (v["apps"], None, None, None,
                                       d.one("SELECT ROUND(SUM(AppliedAmount), 2) FROM CashReceiptApplication"))}
    checks = [Check("tables profiled", 11, len)]
    for t, (k, first, last, cust, amt) in rows.items():
        checks.append(Check(f"{t} rows", k, lambda r, t=t: r.where(TableName=t)["Records"]))
        checks.append(Check(f"{t} keys unique", k, lambda r, t=t: r.where(TableName=t)["DistinctKeys"]))
        if first:
            checks += [Check(f"{t} first date", first, lambda r, t=t: r.where(TableName=t)["FirstDate"]),
                       Check(f"{t} last date", last, lambda r, t=t: r.where(TableName=t)["LastDate"])]
        if cust:
            checks.append(Check(f"{t} customers", cust, lambda r, t=t: r.where(TableName=t)["Customers"]))
        if amt is not None:
            checks.append(Check(f"{t} amount", round(amt, 2), lambda r, t=t: r.where(TableName=t)["Amount"]))
    checks.append(Check("missing keys, dates, or people", 0, lambda r: r.total("Missing")))
    s.query("Requirement 1, test M1: a data profile of each of the cycle's tables (Chapter 10)",
            "Population: every row of the eleven tables; expected: unique keys, dates in the window, nothing missing",
            """\
SELECT 'SalesReturn' AS TableName, COUNT(*) AS Records,
    COUNT(DISTINCT ReturnNumber) AS DistinctKeys,
    MIN(ReturnDate) AS FirstDate, MAX(ReturnDate) AS LastDate,
    COUNT(DISTINCT CustomerID) AS Customers, NULL AS Amount,
    SUM(CASE WHEN ReturnDate IS NULL OR CustomerID IS NULL
        OR ReceivedByEmployeeID IS NULL THEN 1 ELSE 0 END) AS Missing
FROM SalesReturn
UNION ALL
SELECT 'SalesReturnLine', COUNT(*), COUNT(DISTINCT SalesReturnLineID),
    NULL, NULL, NULL, ROUND(SUM(ExtendedStandardCost), 2),
    SUM(CASE WHEN SalesReturnID IS NULL OR ShipmentLineID IS NULL
        THEN 1 ELSE 0 END)
FROM SalesReturnLine
UNION ALL
SELECT 'CreditMemo', COUNT(*), COUNT(DISTINCT CreditMemoNumber),
    MIN(CreditMemoDate), MAX(CreditMemoDate), COUNT(DISTINCT CustomerID),
    ROUND(SUM(GrandTotal), 2),
    SUM(CASE WHEN SalesReturnID IS NULL OR OriginalSalesInvoiceID IS NULL
        OR ApprovedByEmployeeID IS NULL THEN 1 ELSE 0 END)
FROM CreditMemo
UNION ALL
SELECT 'CreditMemoLine', COUNT(*), COUNT(DISTINCT CreditMemoLineID),
    NULL, NULL, NULL, ROUND(SUM(LineTotal), 2),
    SUM(CASE WHEN CreditMemoID IS NULL OR SalesReturnLineID IS NULL
        THEN 1 ELSE 0 END)
FROM CreditMemoLine
UNION ALL
SELECT 'CustomerRefund', COUNT(*), COUNT(DISTINCT RefundNumber),
    MIN(RefundDate), MAX(RefundDate), COUNT(DISTINCT CustomerID),
    ROUND(SUM(Amount), 2),
    SUM(CASE WHEN CreditMemoID IS NULL OR ApprovedByEmployeeID IS NULL
        THEN 1 ELSE 0 END)
FROM CustomerRefund
UNION ALL
SELECT 'SalesCommissionAdjustment', COUNT(*),
    COUNT(DISTINCT AdjustmentNumber), MIN(AdjustmentDate),
    MAX(AdjustmentDate), COUNT(DISTINCT CustomerID),
    ROUND(SUM(CommissionAdjustmentAmount), 2),
    SUM(CASE WHEN CreditMemoLineID IS NULL
        OR SalesCommissionAccrualID IS NULL THEN 1 ELSE 0 END)
FROM SalesCommissionAdjustment
UNION ALL
SELECT 'SalesCommissionAccrual', COUNT(*), COUNT(DISTINCT AccrualNumber),
    MIN(AccrualDate), MAX(AccrualDate), COUNT(DISTINCT CustomerID),
    ROUND(SUM(CommissionAmount), 2),
    SUM(CASE WHEN SalesInvoiceLineID IS NULL THEN 1 ELSE 0 END)
FROM SalesCommissionAccrual
UNION ALL
SELECT 'SalesCommissionPayment', COUNT(*), COUNT(DISTINCT PaymentNumber),
    MIN(PaymentDate), MAX(PaymentDate), NULL,
    ROUND(SUM(NetPaymentAmount), 2),
    SUM(CASE WHEN ApprovedByEmployeeID IS NULL THEN 1 ELSE 0 END)
FROM SalesCommissionPayment
UNION ALL
SELECT 'SalesCommissionRate', COUNT(*),
    COUNT(DISTINCT SalesCommissionRateID), MIN(EffectiveStartDate),
    MAX(EffectiveEndDate), NULL, NULL,
    SUM(CASE WHEN ApprovedByEmployeeID IS NULL THEN 1 ELSE 0 END)
FROM SalesCommissionRate
UNION ALL
SELECT 'CashReceipt', COUNT(*), COUNT(DISTINCT ReceiptNumber),
    MIN(ReceiptDate), MAX(ReceiptDate), COUNT(DISTINCT CustomerID),
    ROUND(SUM(Amount), 2),
    SUM(CASE WHEN DepositDate IS NULL OR RecordedByEmployeeID IS NULL
        THEN 1 ELSE 0 END)
FROM CashReceipt
UNION ALL
SELECT 'CashReceiptApplication', COUNT(*),
    COUNT(DISTINCT CashReceiptApplicationID), MIN(ApplicationDate),
    MAX(ApplicationDate), NULL, ROUND(SUM(AppliedAmount), 2),
    SUM(CASE WHEN CashReceiptID IS NULL OR SalesInvoiceID IS NULL
        OR AppliedByEmployeeID IS NULL THEN 1 ELSE 0 END)
FROM CashReceiptApplication;""", checks)
    checks = []
    for status, k in v["statuses"]:
        checks.append(Check(f"returns {status}", k,
                            lambda r, x=status: r.where(TableName="SalesReturn", ColumnName="Status", Value=x)["Records"]))
    for reason, k in v["reasons"]:
        checks.append(Check(f"returns {reason}", k,
                            lambda r, x=reason: r.where(TableName="SalesReturn", ColumnName="ReasonCode",
                                                        Value=x)["Records"]))
    for status, k, amt in v["cm_status"]:
        checks += [Check(f"credits {status}", k,
                         lambda r, x=status: r.where(TableName="CreditMemo", ColumnName="Status", Value=x)["Records"]),
                   Check(f"credits {status} amount", amt,
                         lambda r, x=status: r.where(TableName="CreditMemo", ColumnName="Status", Value=x)["Amount"])]
    methods = Counter(r["method"] for r in c.rf.values())
    for method, k in methods.items():
        checks.append(Check(f"refunds by {method}", k,
                            lambda r, x=method: r.where(TableName="CustomerRefund", ColumnName="PaymentMethod",
                                                        Value=x)["Records"]))
    s.query("Requirement 1, test M2: the values of each status, reason, and method column",
            "Population: returns, credits, refunds, and clawbacks; expected: a few valid values each",
            """\
SELECT 'SalesReturn' AS TableName, 'Status' AS ColumnName,
    Status AS Value, COUNT(*) AS Records, NULL AS Amount
FROM SalesReturn
GROUP BY Status
UNION ALL
SELECT 'SalesReturn', 'ReasonCode', ReasonCode, COUNT(*), NULL
FROM SalesReturn
GROUP BY ReasonCode
UNION ALL
SELECT 'CreditMemo', 'Status', Status, COUNT(*), ROUND(SUM(GrandTotal), 2)
FROM CreditMemo
GROUP BY Status
UNION ALL
SELECT 'CustomerRefund', 'PaymentMethod', PaymentMethod, COUNT(*),
    ROUND(SUM(Amount), 2)
FROM CustomerRefund
GROUP BY PaymentMethod
UNION ALL
SELECT 'SalesCommissionAdjustment', 'Status', Status, COUNT(*),
    ROUND(SUM(CommissionAdjustmentAmount), 2)
FROM SalesCommissionAdjustment
GROUP BY Status
ORDER BY TableName, ColumnName, Records DESC;""", checks)
    lag, rf = v["lag"], v["rf"]
    s.query("Requirement 1, test M3: the days between the cycle's steps",
            "Population: every credit and refund; expected: credits within days of the return, refunds within weeks",
            """\
SELECT 'Return to credit' AS Step, COUNT(*) AS Documents,
    MIN(julianday(cm.CreditMemoDate) - julianday(sr.ReturnDate))
        AS MinDays,
    MAX(julianday(cm.CreditMemoDate) - julianday(sr.ReturnDate))
        AS MaxDays,
    ROUND(AVG(julianday(cm.CreditMemoDate) - julianday(sr.ReturnDate)), 1)
        AS MeanDays,
    SUM(CASE WHEN cm.CreditMemoDate = sr.ReturnDate THEN 1 ELSE 0 END)
        AS SameDay,
    SUM(CASE WHEN julianday(cm.CreditMemoDate)
        - julianday(sr.ReturnDate) > 30 THEN 1 ELSE 0 END) AS Over30Days
FROM CreditMemo AS cm
    INNER JOIN SalesReturn AS sr ON sr.SalesReturnID = cm.SalesReturnID
UNION ALL
SELECT 'Credit to approval', COUNT(*),
    MIN(julianday(ApprovedDate) - julianday(CreditMemoDate)),
    MAX(julianday(ApprovedDate) - julianday(CreditMemoDate)),
    ROUND(AVG(julianday(ApprovedDate) - julianday(CreditMemoDate)), 1),
    SUM(CASE WHEN ApprovedDate = CreditMemoDate THEN 1 ELSE 0 END),
    SUM(CASE WHEN julianday(ApprovedDate)
        - julianday(CreditMemoDate) > 30 THEN 1 ELSE 0 END)
FROM CreditMemo
UNION ALL
SELECT 'Credit to refund', COUNT(*),
    MIN(julianday(rf.RefundDate) - julianday(cm.CreditMemoDate)),
    MAX(julianday(rf.RefundDate) - julianday(cm.CreditMemoDate)),
    ROUND(AVG(julianday(rf.RefundDate) - julianday(cm.CreditMemoDate)), 1),
    SUM(CASE WHEN rf.RefundDate = cm.CreditMemoDate THEN 1 ELSE 0 END),
    SUM(CASE WHEN julianday(rf.RefundDate)
        - julianday(cm.CreditMemoDate) > 30 THEN 1 ELSE 0 END)
FROM CustomerRefund AS rf
    INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
UNION ALL
SELECT 'Refund to clearing', COUNT(*),
    MIN(julianday(ClearedDate) - julianday(RefundDate)),
    MAX(julianday(ClearedDate) - julianday(RefundDate)),
    ROUND(AVG(julianday(ClearedDate) - julianday(RefundDate)), 1),
    SUM(CASE WHEN ClearedDate = RefundDate THEN 1 ELSE 0 END),
    SUM(CASE WHEN julianday(ClearedDate)
        - julianday(RefundDate) > 30 THEN 1 ELSE 0 END)
FROM CustomerRefund;""",
            [Check("return to credit, fewest days", lag["lo"], lambda r: r.where(Step="Return to credit")["MinDays"]),
             Check("return to credit, most days", lag["hi"], lambda r: r.where(Step="Return to credit")["MaxDays"]),
             Check("return to credit, mean days", round(lag["mean"], 1),
                   lambda r: r.where(Step="Return to credit")["MeanDays"], 0.051),
             Check("credits on the day of the return", lag["zero"],
                   lambda r: r.where(Step="Return to credit")["SameDay"]),
             Check("credits approved on their date", v["same_date"],
                   lambda r: r.where(Step="Credit to approval")["SameDay"]),
             Check("credit to refund, fewest days", rf["lo"], lambda r: r.where(Step="Credit to refund")["MinDays"]),
             Check("credit to refund, most days", rf["hi"], lambda r: r.where(Step="Credit to refund")["MaxDays"]),
             Check("credit to refund, mean days", round(rf["mean"], 1),
                   lambda r: r.where(Step="Credit to refund")["MeanDays"], 0.051),
             Check("refunds more than 30 days after the credit", rf["over30"],
                   lambda r: r.where(Step="Credit to refund")["Over30Days"]),
             Check("refund to clearing, fewest days", rf["clo"], lambda r: r.where(Step="Refund to clearing")["MinDays"]),
             Check("refund to clearing, most days", rf["chi"], lambda r: r.where(Step="Refund to clearing")["MaxDays"])])
    links = [
        ("Return lines without a shipment line", "SalesReturnLine AS x", "ShipmentLine AS y",
         "y.ShipmentLineID = x.ShipmentLineID", "y.ShipmentLineID"),
        ("Return lines without a return", "SalesReturnLine AS x", "SalesReturn AS y",
         "y.SalesReturnID = x.SalesReturnID", "y.SalesReturnID"),
        ("Returns without a credit", "SalesReturn AS x", "CreditMemo AS y",
         "y.SalesReturnID = x.SalesReturnID", "y.CreditMemoID"),
        ("Credits without a return", "CreditMemo AS x", "SalesReturn AS y",
         "y.SalesReturnID = x.SalesReturnID", "y.SalesReturnID"),
        ("Credits without an invoice", "CreditMemo AS x", "SalesInvoice AS y",
         "y.SalesInvoiceID = x.OriginalSalesInvoiceID", "y.SalesInvoiceID"),
        ("Credit lines without a credit", "CreditMemoLine AS x", "CreditMemo AS y",
         "y.CreditMemoID = x.CreditMemoID", "y.CreditMemoID"),
        ("Credit lines without a return line", "CreditMemoLine AS x", "SalesReturnLine AS y",
         "y.SalesReturnLineID = x.SalesReturnLineID", "y.SalesReturnLineID"),
        ("Return lines without a credit line", "SalesReturnLine AS x", "CreditMemoLine AS y",
         "y.SalesReturnLineID = x.SalesReturnLineID", "y.CreditMemoLineID"),
        ("Refunds without a credit", "CustomerRefund AS x", "CreditMemo AS y",
         "y.CreditMemoID = x.CreditMemoID", "y.CreditMemoID"),
        ("Refunded credits without a refund", "CreditMemo AS x", "CustomerRefund AS y",
         "y.CreditMemoID = x.CreditMemoID", "y.CustomerRefundID", "x.Status = 'Refunded'"),
        ("Clawbacks without a credit line", "SalesCommissionAdjustment AS x", "CreditMemoLine AS y",
         "y.CreditMemoLineID = x.CreditMemoLineID", "y.CreditMemoLineID"),
        ("Credit lines without a clawback", "CreditMemoLine AS x", "SalesCommissionAdjustment AS y",
         "y.CreditMemoLineID = x.CreditMemoLineID", "y.SalesCommissionAdjustmentID"),
        ("Clawbacks without an accrual", "SalesCommissionAdjustment AS x", "SalesCommissionAccrual AS y",
         "y.SalesCommissionAccrualID = x.SalesCommissionAccrualID", "y.SalesCommissionAccrualID"),
        ("Applications without a receipt", "CashReceiptApplication AS x", "CashReceipt AS y",
         "y.CashReceiptID = x.CashReceiptID", "y.CashReceiptID"),
        ("Applications without an invoice", "CashReceiptApplication AS x", "SalesInvoice AS y",
         "y.SalesInvoiceID = x.SalesInvoiceID", "y.SalesInvoiceID")]
    parts = []
    for k, (label, left, right, on, key, *extra) in enumerate(links):
        where = f"WHERE {key} IS NULL" + (f"\n    AND {extra[0]}" if extra else "")
        head = f"SELECT '{label}' AS Link, COUNT(*) AS Orphans" if k == 0 else f"SELECT '{label}', COUNT(*)"
        parts.append(f"{head}\nFROM {left}\n    LEFT JOIN {right}\n        ON {on}\n{where}")
    s.query("Requirement 1, test M4: every link of the cycle tested both ways with anti-joins",
            "Population: the cycle's documents and lines; expected: no orphan in any direction",
            "\nUNION ALL\n".join(parts) + ";",
            [Check("links tested", len(links), len),
             Check("orphans", 0, lambda r: r.total("Orphans"))])
    keys = {"SalesReturn": "SalesReturnID", "CreditMemo": "CreditMemoID", "CustomerRefund": "CustomerRefundID",
            "SalesCommissionAdjustment": "SalesCommissionAdjustmentID", "CashReceipt": "CashReceiptID",
            "CashReceiptApplication": "CashReceiptApplicationID"}
    parts = []
    for k, (t, key) in enumerate(keys.items()):
        head = (f"SELECT '{t}' AS Document,\n    (SELECT COUNT(*)" if k == 0 else f"SELECT '{t}',\n    (SELECT COUNT(*)")
        parts.append(f"""{head}
     FROM GLEntry AS gl
        LEFT JOIN {t} AS x
            ON x.{key} = gl.SourceDocumentID
     WHERE gl.SourceDocumentType = '{t}'
        AND x.{key} IS NULL){' AS PostingsWithoutDocument' if k == 0 else ''},
    (SELECT COUNT(*)
     FROM {t} AS x
     WHERE NOT EXISTS (
        SELECT 1
        FROM GLEntry AS gl
        WHERE gl.SourceDocumentType = '{t}'
            AND gl.SourceDocumentID = x.{key})){' AS DocumentsNotPosted' if k == 0 else ''}""")
    s.query("Requirement 1, test M5: the cycle's documents traced to the ledger both ways",
            "Population: the six documents and their GLEntry rows; expected: every document posted, no orphan row",
            "\nUNION ALL\n".join(parts) + ";",
            [Check("documents traced", len(keys), len),
             Check("postings without a document", 0, lambda r: r.total("PostingsWithoutDocument")),
             Check("documents not posted", 0, lambda r: r.total("DocumentsNotPosted"))])
    nums = v["nums"]

    def ranges(r, series):
        rows = [x for x in dicts(r) if x["Series"] == series]
        return ", ".join(f"{x['FirstNumber']}-{x['LastNumber']}" for x in sorted(rows, key=lambda x: x["FiscalYear"]))
    s.query("Requirement 1, test M6: the document numbers of each series and year tested for gaps (Chapter 8)",
            "Population: return, credit, refund, and clawback numbers; expected: no gaps, continuing across years",
            """\
WITH Numbers AS (
    SELECT 'SR' AS Series,
        CAST(SUBSTR(ReturnNumber, 4, 4) AS INTEGER) AS FiscalYear,
        CAST(SUBSTR(ReturnNumber, 9) AS INTEGER) AS Sequence
    FROM SalesReturn
    UNION ALL
    SELECT 'CM', CAST(SUBSTR(CreditMemoNumber, 4, 4) AS INTEGER),
        CAST(SUBSTR(CreditMemoNumber, 9) AS INTEGER)
    FROM CreditMemo
    UNION ALL
    SELECT 'RF', CAST(SUBSTR(RefundNumber, 4, 4) AS INTEGER),
        CAST(SUBSTR(RefundNumber, 9) AS INTEGER)
    FROM CustomerRefund
    UNION ALL
    SELECT 'SCAJ', CAST(SUBSTR(AdjustmentNumber, 6, 4) AS INTEGER),
        CAST(SUBSTR(AdjustmentNumber, 11) AS INTEGER)
    FROM SalesCommissionAdjustment
),
ByYear AS (
    SELECT Series, FiscalYear, MIN(Sequence) AS FirstNumber,
        MAX(Sequence) AS LastNumber, COUNT(*) AS Documents,
        COUNT(DISTINCT Sequence) AS DistinctNumbers
    FROM Numbers
    GROUP BY Series, FiscalYear
)
SELECT Series, FiscalYear, FirstNumber, LastNumber, Documents,
    LastNumber - FirstNumber + 1 - DistinctNumbers AS Gaps,
    Documents - DistinctNumbers AS Repeats,
    FirstNumber - 1 - LAG(LastNumber) OVER (
        PARTITION BY Series ORDER BY FiscalYear) AS BreakFromLastYear
FROM ByYear
ORDER BY Series, FiscalYear;""",
            [Check("series and years", 4 * len(d.years), len),
             Check("gaps", 0, lambda r: r.total("Gaps")),
             Check("repeated numbers", 0, lambda r: r.total("Repeats")),
             Check("breaks between years", 0, lambda r: r.total("BreakFromLastYear")),
             Check("returns' ranges", nums["SalesReturn"], lambda r: ranges(r, "SR")),
             Check("credits' ranges", nums["CreditMemo"], lambda r: ranges(r, "CM")),
             Check("refunds' ranges", nums["CustomerRefund"], lambda r: ranges(r, "RF")),
             Check("clawbacks' ranges", nums["SalesCommissionAdjustment"], lambda r: ranges(r, "SCAJ"))])
    checks = []
    post = v["post"]
    for key, (amt, k) in post.items():
        side, acct = key.split()
        col, rows_col = ("Debits", "DebitRows") if side == "Dr" else ("Credits", "CreditRows")
        checks += [Check(f"credits {key}", round(amt, 2),
                         lambda r, a=int(acct), col=col: r.where(SourceDocumentType="CreditMemo",
                                                                 AccountNumber=a)[col]),
                   Check(f"credits {key} rows", k,
                         lambda r, a=int(acct), col=rows_col: r.where(SourceDocumentType="CreditMemo",
                                                                      AccountNumber=a)[col])]
    checks += [Check("returns Dr 1040", round(v["sr_dr"], 2),
                     lambda r: r.where(SourceDocumentType="SalesReturn", AccountNumber=1040)["Debits"]),
               Check("returns Cr cost of goods sold", round(v["sr_dr"], 2),
                     lambda r: round(sum(x["Credits"] for x in dicts(r) if x["SourceDocumentType"] == "SalesReturn"
                                         and 5010 <= x["AccountNumber"] <= 5040), 2)),
               Check("refunds Cr 1010", round(v["rf_cr"], 2),
                     lambda r: r.where(SourceDocumentType="CustomerRefund", AccountNumber=1010)["Credits"]),
               Check("refunds Dr 2060", round(v["rf_cr"], 2),
                     lambda r: r.where(SourceDocumentType="CustomerRefund", AccountNumber=2060)["Debits"]),
               Check("clawbacks Cr 6290", round(v["sca"], 2),
                     lambda r: r.where(SourceDocumentType="SalesCommissionAdjustment", AccountNumber=6290)["Credits"]),
               Check("clawbacks Dr 2034", round(v["sca"], 2),
                     lambda r: r.where(SourceDocumentType="SalesCommissionAdjustment", AccountNumber=2034)["Debits"]),
               Check("receipt rows", v["rows"]["CashReceipt"],
                     lambda r: sum(x["DebitRows"] + x["CreditRows"] for x in dicts(r)
                                   if x["SourceDocumentType"] == "CashReceipt")),
               Check("application rows", v["rows"]["CashReceiptApplication"],
                     lambda r: sum(x["DebitRows"] + x["CreditRows"] for x in dicts(r)
                                   if x["SourceDocumentType"] == "CashReceiptApplication")),
               Check("accounts of the receipts", [1010, 2060],
                     lambda r: [x["AccountNumber"] for x in dicts(r) if x["SourceDocumentType"] == "CashReceipt"]),
               Check("accounts of the applications", [1020, 2060],
                     lambda r: [x["AccountNumber"] for x in dicts(r)
                                if x["SourceDocumentType"] == "CashReceiptApplication"])]
    s.query("Requirement 1, test M7: the ledger's postings of the cycle, by source document and account",
            "Population: the GLEntry rows of the six documents; expected: each document on its own few accounts",
            f"""\
SELECT gl.SourceDocumentType, a.AccountNumber, a.AccountName,
    SUM(CASE WHEN gl.Debit > 0 THEN 1 ELSE 0 END) AS DebitRows,
    ROUND(SUM(gl.Debit), 2) AS Debits,
    SUM(CASE WHEN gl.Credit > 0 THEN 1 ELSE 0 END) AS CreditRows,
    ROUND(SUM(gl.Credit), 2) AS Credits
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE gl.SourceDocumentType IN ({SOURCES})
GROUP BY gl.SourceDocumentType, a.AccountNumber, a.AccountName
ORDER BY gl.SourceDocumentType, a.AccountNumber;""", checks)
    checks = []
    singular = {p: t for t in {e["title"] for e in c.emp.values()} for p in (n.plural(t), f"the {t}")}
    for doc, role, people in (("SalesReturn", "Received", v["receivers"]), ("CreditMemo", "Approved", v["approvers"]),
                              ("CustomerRefund", "Approved", v["rf_appr"])):
        for who, k in people:
            t = singular[who]
            checks.append(Check(f"{doc} {role.lower()} by {t}", k,
                                lambda r, doc=doc, t=t: r.where(Document=doc, JobTitle=t)["Documents"]))
    checks += [Check("receipts recorded by the Customer Service Manager", v["manager"],
                     lambda r: r.where(Document="CashReceipt", JobTitle=n.CSM)["Documents"]),
               Check("receipts recorded by Customer Service Representatives", v["reps"],
                     lambda r: r.where(Document="CashReceipt", JobTitle=n.CSR)["Documents"]),
               Check("applications by customer service", v["apps"],
                     lambda r: sum(x["Documents"] for x in dicts(r) if x["Document"] == "CashReceiptApplication"
                                   and x["CostCenterName"] == n.CS)),
               Check("returns received in the warehouse", len(c.sr),
                     lambda r: sum(x["Documents"] for x in dicts(r) if x["Document"] == "SalesReturn"
                                   and x["CostCenterName"] == "Warehouse"))]
    s.query("Requirement 1, test M8: who records each document, by job title and cost center",
            "Population: the person each document names; expected: customer service handles cash and credits",
            """\
WITH People AS (
    SELECT 'SalesReturn' AS Document, 'Received' AS Role,
        ReceivedByEmployeeID AS EmployeeID
    FROM SalesReturn
    UNION ALL
    SELECT 'CreditMemo', 'Approved', ApprovedByEmployeeID
    FROM CreditMemo
    UNION ALL
    SELECT 'CustomerRefund', 'Approved', ApprovedByEmployeeID
    FROM CustomerRefund
    UNION ALL
    SELECT 'SalesCommissionAdjustment', 'Approved', ApprovedByEmployeeID
    FROM SalesCommissionAdjustment
    UNION ALL
    SELECT 'CashReceipt', 'Recorded', RecordedByEmployeeID
    FROM CashReceipt
    UNION ALL
    SELECT 'CashReceiptApplication', 'Applied', AppliedByEmployeeID
    FROM CashReceiptApplication
)
SELECT p.Document, p.Role, e.JobTitle, cc.CostCenterName,
    COUNT(*) AS Documents, COUNT(DISTINCT p.EmployeeID) AS Employees
FROM People AS p
    INNER JOIN Employee AS e ON e.EmployeeID = p.EmployeeID
    LEFT JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
GROUP BY p.Document, p.Role, e.JobTitle, cc.CostCenterName
ORDER BY p.Document, Documents DESC;""", checks)
    s.answer("Requirement 1", f"""\
The map rests on the records: {len(c.sr)} returns ({v['sr']['lines']} lines), {v['cm']['n']} credit memos
({money(v['cm']['total'])}), {v['rf']['n']} refunds ({money(v['rf']['total'])}), {v['cb']['n']} clawbacks
({money(v['cb']['total'])}), {v['receipts']:,} receipts, and {v['apps']:,} applications (M1). Every link holds in both
directions (M4), every document posts and every posting has its document (M5), and the numbers of each series run
without gaps and continue across years (M6). M7 shows each document on its own accounts: credits debit 4060, 4050,
and 2050 and credit 1020 or 2060 ({v['both']} credits post to both); returns debit 1040 and credit cost of goods sold;
refunds move cash out of 2060; receipts and applications pass through 2060.

What the records evidence at each control point (fig-19-01): the return's receipt in the warehouse (who received it and
when, M8), the credit's approval (approver and date, equal to the credit date on all {v['same_date']}), the refund's
approval and clearing, the clawback, and the receipt, deposit, and application of cash. What they cannot evidence: the
inspection of the goods (C1), the customer's request for a refund, the payee and bank account a refund was paid to
(C8), any delegation of authority beyond Employee.MaxApprovalAmount, and who prepared a credit or a refund (no table
records a preparer; test T5).""")


# --- Requirement 2 -----------------------------------------------------------------------------------------------

def r2(b):
    d, n = b.data, notes(b)
    v = context(b, "r2_")
    s = script(b)
    yrs = d.years
    cols = dict(Credits=v["n"], SubTotal=v["sub"], Dr4060=v["sub"], Freight=v["freight"], Dr4050=v["freight"],
                Tax=v["tax"], Dr2050=v["tax"], GrandTotal=v["gt"], Cr1020=v["cr1020"], Cr2060=v["cr2060"])
    checks = [Check("years", yrs, lambda r: r.col("FiscalYear"))]
    checks += [Check(f"{col} by year", [round(x, 2) for x in want], lambda r, col=col: r.col(col))
               for col, want in cols.items()]
    checks += [Check("SubTotal less 4060, freight less 4050, tax less 2050", [0.0] * len(yrs),
                     lambda r: r.col("DebitDifference")),
               Check("GrandTotal less the credits to 1020 and 2060", [0.0] * len(yrs),
                     lambda r: r.col("CreditDifference"))]
    q = s.query("Requirement 2, test G1: the credits reconciled to the ledger by fiscal year",
                "Population: every credit memo and its GLEntry rows; expected: no difference in any year",
                """\
WITH Credits AS (
    SELECT CAST(strftime('%Y', CreditMemoDate) AS INTEGER) AS FiscalYear,
        COUNT(*) AS Credits, SUM(SubTotal) AS SubTotal,
        SUM(FreightCreditAmount) AS Freight, SUM(TaxAmount) AS Tax,
        SUM(GrandTotal) AS GrandTotal
    FROM CreditMemo
    GROUP BY FiscalYear
),
Ledger AS (
    SELECT gl.FiscalYear,
        SUM(CASE WHEN a.AccountNumber = 4060 THEN gl.Debit ELSE 0 END)
            AS Dr4060,
        SUM(CASE WHEN a.AccountNumber = 4050 THEN gl.Debit ELSE 0 END)
            AS Dr4050,
        SUM(CASE WHEN a.AccountNumber = 2050 THEN gl.Debit ELSE 0 END)
            AS Dr2050,
        SUM(CASE WHEN a.AccountNumber = 1020 THEN gl.Credit ELSE 0 END)
            AS Cr1020,
        SUM(CASE WHEN a.AccountNumber = 2060 THEN gl.Credit ELSE 0 END)
            AS Cr2060
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType = 'CreditMemo'
    GROUP BY gl.FiscalYear
)
SELECT c.FiscalYear, c.Credits, ROUND(c.SubTotal, 2) AS SubTotal,
    ROUND(l.Dr4060, 2) AS Dr4060, ROUND(c.Freight, 2) AS Freight,
    ROUND(l.Dr4050, 2) AS Dr4050, ROUND(c.Tax, 2) AS Tax,
    ROUND(l.Dr2050, 2) AS Dr2050, ROUND(c.GrandTotal, 2) AS GrandTotal,
    ROUND(l.Cr1020, 2) AS Cr1020, ROUND(l.Cr2060, 2) AS Cr2060,
    ROUND(c.SubTotal - l.Dr4060 + c.Freight - l.Dr4050
        + c.Tax - l.Dr2050, 2) AS DebitDifference,
    ROUND(c.GrandTotal - l.Cr1020 - l.Cr2060, 2) AS CreditDifference
FROM Credits AS c
    LEFT JOIN Ledger AS l ON l.FiscalYear = c.FiscalYear
ORDER BY c.FiscalYear;""", checks)
    remember(b, "credits", q)
    cogs = dict(v["cogs"])
    checks = [Check("returns at standard by year", [round(x, 2) for x in v["std"]], lambda r: r.col("AtStandard")),
              Check("Dr 1040 by year", [round(x, 2) for x in v["std"]], lambda r: r.col("Dr1040")),
              Check("differences", [0.0] * len(yrs), lambda r: r.col("Difference"))]
    checks += [Check(f"Cr {a} by year", [round(x, 2) for x in want], lambda r, a=a: r.col(f"Cr{a}"))
               for a, want in cogs.items()]
    s.query("Requirement 2, test G2: the returns' standard cost reconciled to inventory and cost of goods sold",
            "Population: every return line and the returns' GLEntry rows; expected: no difference in any year",
            """\
WITH Returns AS (
    SELECT CAST(strftime('%Y', sr.ReturnDate) AS INTEGER) AS FiscalYear,
        SUM(srl.ExtendedStandardCost) AS AtStandard
    FROM SalesReturnLine AS srl
        INNER JOIN SalesReturn AS sr ON sr.SalesReturnID = srl.SalesReturnID
    GROUP BY FiscalYear
),
Ledger AS (
    SELECT gl.FiscalYear,
        SUM(CASE WHEN a.AccountNumber = 1040 THEN gl.Debit ELSE 0 END)
            AS Dr1040,
        SUM(CASE WHEN a.AccountNumber = 5010 THEN gl.Credit ELSE 0 END)
            AS Cr5010,
        SUM(CASE WHEN a.AccountNumber = 5020 THEN gl.Credit ELSE 0 END)
            AS Cr5020,
        SUM(CASE WHEN a.AccountNumber = 5030 THEN gl.Credit ELSE 0 END)
            AS Cr5030,
        SUM(CASE WHEN a.AccountNumber = 5040 THEN gl.Credit ELSE 0 END)
            AS Cr5040
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType = 'SalesReturn'
    GROUP BY gl.FiscalYear
)
SELECT r.FiscalYear, ROUND(r.AtStandard, 2) AS AtStandard,
    ROUND(l.Dr1040, 2) AS Dr1040, ROUND(l.Cr5010, 2) AS Cr5010,
    ROUND(l.Cr5020, 2) AS Cr5020, ROUND(l.Cr5030, 2) AS Cr5030,
    ROUND(l.Cr5040, 2) AS Cr5040,
    ROUND(r.AtStandard - l.Dr1040, 2) AS Difference
FROM Returns AS r
    LEFT JOIN Ledger AS l ON l.FiscalYear = r.FiscalYear
ORDER BY r.FiscalYear;""", checks)
    s.query("Requirement 2, test G3: the refunds reconciled to cash and 2060 by fiscal year",
            "Population: every refund and its GLEntry rows; expected: no difference in any year",
            """\
WITH Refunds AS (
    SELECT CAST(strftime('%Y', RefundDate) AS INTEGER) AS FiscalYear,
        COUNT(*) AS Refunds, SUM(Amount) AS Amount
    FROM CustomerRefund
    GROUP BY FiscalYear
),
Ledger AS (
    SELECT gl.FiscalYear,
        SUM(CASE WHEN a.AccountNumber = 1010 THEN gl.Credit ELSE 0 END)
            AS Cr1010,
        SUM(CASE WHEN a.AccountNumber = 2060 THEN gl.Debit ELSE 0 END)
            AS Dr2060
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType = 'CustomerRefund'
    GROUP BY gl.FiscalYear
)
SELECT r.FiscalYear, r.Refunds, ROUND(r.Amount, 2) AS Amount,
    ROUND(l.Cr1010, 2) AS Cr1010, ROUND(l.Dr2060, 2) AS Dr2060,
    ROUND(r.Amount - l.Cr1010, 2) AS Difference1010,
    ROUND(r.Amount - l.Dr2060, 2) AS Difference2060
FROM Refunds AS r
    LEFT JOIN Ledger AS l ON l.FiscalYear = r.FiscalYear
ORDER BY r.FiscalYear;""",
            [Check("refunds by year", v["rf_n"], lambda r: r.col("Refunds")),
             Check("amount by year", [round(x, 2) for x in v["rf_amt"]], lambda r: r.col("Amount")),
             Check("Cr 1010 by year", [round(x, 2) for x in v["rf_amt"]], lambda r: r.col("Cr1010")),
             Check("differences", [0.0] * (2 * len(yrs)),
                   lambda r: r.col("Difference1010") + r.col("Difference2060"))])
    s.query("Requirement 2, test G4: the clawbacks reconciled to 2034 and 6290, beside the accruals and payments",
            "Population: every clawback, accrual, and commission payment; expected: no difference in any year",
            f"""\
WITH Clawbacks AS (
    SELECT CAST(strftime('%Y', AdjustmentDate) AS INTEGER) AS FiscalYear,
        SUM(CommissionAdjustmentAmount) AS Clawbacks
    FROM SalesCommissionAdjustment
    GROUP BY FiscalYear
),
Ledger AS (
    SELECT gl.FiscalYear,
        SUM(CASE WHEN a.AccountNumber = 2034 THEN gl.Debit ELSE 0 END)
            AS Dr2034,
        SUM(CASE WHEN a.AccountNumber = 6290 THEN gl.Credit ELSE 0 END)
            AS Cr6290
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType = 'SalesCommissionAdjustment'
    GROUP BY gl.FiscalYear
)
SELECT c.FiscalYear, ROUND(c.Clawbacks, 2) AS Clawbacks,
    ROUND(l.Dr2034, 2) AS Dr2034, ROUND(l.Cr6290, 2) AS Cr6290,
    ROUND(c.Clawbacks - l.Dr2034, 2) AS Difference,
    (SELECT ROUND(SUM(CommissionAmount), 2)
     FROM SalesCommissionAccrual
     WHERE CAST(strftime('%Y', AccrualDate) AS INTEGER) = c.FiscalYear)
        AS Accruals,
    (SELECT ROUND(SUM(NetPaymentAmount), 2)
     FROM SalesCommissionPayment
     WHERE CAST(strftime('%Y', PaymentDate) AS INTEGER) = c.FiscalYear)
        AS Payments
FROM Clawbacks AS c
    LEFT JOIN Ledger AS l ON l.FiscalYear = c.FiscalYear
WHERE c.FiscalYear BETWEEN {d.F} AND {d.C}
ORDER BY c.FiscalYear;""",
            [Check("clawbacks by year", [round(x, 2) for x in v["clawback"]], lambda r: r.col("Clawbacks")),
             Check("Cr 6290 by year", [round(x, 2) for x in v["clawback"]], lambda r: r.col("Cr6290")),
             Check("differences", [0.0] * len(yrs), lambda r: r.col("Difference")),
             Check("accruals by year", [round(x, 2) for x in v["accruals"]], lambda r: r.col("Accruals")),
             Check("payments by year", [round(x, 2) for x in v["payments"]], lambda r: r.col("Payments"))])
    s.query("Requirement 2, test G5: the receipts and applications reconciled to cash, 2060, and receivables",
            "Population: every receipt and application and their GLEntry rows; expected: no difference in any year",
            f"""\
WITH Receipts AS (
    SELECT CAST(strftime('%Y', ReceiptDate) AS INTEGER) AS FiscalYear,
        SUM(Amount) AS Receipts
    FROM CashReceipt
    GROUP BY FiscalYear
),
Applications AS (
    SELECT CAST(strftime('%Y', ApplicationDate) AS INTEGER) AS FiscalYear,
        SUM(AppliedAmount) AS Applications
    FROM CashReceiptApplication
    GROUP BY FiscalYear
),
Ledger AS (
    SELECT gl.FiscalYear,
        SUM(CASE WHEN gl.SourceDocumentType = 'CashReceipt'
            AND a.AccountNumber = 1010 THEN gl.Debit ELSE 0 END) AS Dr1010,
        SUM(CASE WHEN gl.SourceDocumentType = 'CashReceipt'
            AND a.AccountNumber = 2060 THEN gl.Credit ELSE 0 END) AS Cr2060,
        SUM(CASE WHEN gl.SourceDocumentType = 'CashReceiptApplication'
            AND a.AccountNumber = 2060 THEN gl.Debit ELSE 0 END) AS Dr2060,
        SUM(CASE WHEN gl.SourceDocumentType = 'CashReceiptApplication'
            AND a.AccountNumber = 1020 THEN gl.Credit ELSE 0 END) AS Cr1020
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType IN ('CashReceipt',
        'CashReceiptApplication')
    GROUP BY gl.FiscalYear
)
SELECT r.FiscalYear, ROUND(r.Receipts, 2) AS Receipts,
    ROUND(l.Dr1010, 2) AS Dr1010, ROUND(l.Cr2060, 2) AS Cr2060,
    ROUND(ap.Applications, 2) AS Applications,
    ROUND(l.Dr2060, 2) AS Dr2060, ROUND(l.Cr1020, 2) AS Cr1020,
    ROUND(r.Receipts - l.Dr1010, 2) AS ReceiptDifference,
    ROUND(ap.Applications - l.Cr1020, 2) AS ApplicationDifference
FROM Receipts AS r
    LEFT JOIN Applications AS ap ON ap.FiscalYear = r.FiscalYear
    LEFT JOIN Ledger AS l ON l.FiscalYear = r.FiscalYear
WHERE r.FiscalYear BETWEEN {d.F} AND {d.C}
ORDER BY r.FiscalYear;""",
            [Check("receipts by year", [round(x, 2) for x in v["receipts"]], lambda r: r.col("Receipts")),
             Check("applications by year", [round(x, 2) for x in v["receipts"]], lambda r: r.col("Applications")),
             Check("Cr 1020 by year", [round(x, 2) for x in v["receipts"]], lambda r: r.col("Cr1020")),
             Check("differences", [0.0] * (2 * len(yrs)),
                   lambda r: r.col("ReceiptDifference") + r.col("ApplicationDifference"))])
    q = s.query("Requirement 2, test G6: account 2060 rolled forward to each year-end, flow by flow",
                "Population: every GLEntry row on 2060 to the base year's end; expected: large flows, small balances",
                f"""\
WITH Flows AS (
    SELECT gl.FiscalYear,
        SUM(CASE WHEN gl.SourceDocumentType = 'CashReceipt'
            THEN gl.Credit - gl.Debit ELSE 0 END) AS Receipts,
        SUM(CASE WHEN gl.SourceDocumentType = 'CreditMemo'
            THEN gl.Credit - gl.Debit ELSE 0 END) AS Credits,
        SUM(CASE WHEN gl.SourceDocumentType = 'CashReceiptApplication'
            THEN gl.Credit - gl.Debit ELSE 0 END) AS Applications,
        SUM(CASE WHEN gl.SourceDocumentType = 'CustomerRefund'
            THEN gl.Credit - gl.Debit ELSE 0 END) AS Refunds,
        SUM(CASE WHEN gl.SourceDocumentType NOT IN ('CashReceipt',
                'CreditMemo', 'CashReceiptApplication', 'CustomerRefund')
            THEN gl.Credit - gl.Debit ELSE 0 END) AS Other,
        SUM(gl.Credit - gl.Debit) AS NetChange
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber = 2060 AND gl.PostingDate <= '{d.C}-12-31'
    GROUP BY gl.FiscalYear
)
SELECT FiscalYear,
    ROUND(SUM(NetChange) OVER (ORDER BY FiscalYear) - NetChange, 2)
        AS Opening,
    ROUND(Receipts, 2) AS Receipts, ROUND(Credits, 2) AS Credits,
    ROUND(Applications, 2) AS Applications, ROUND(Refunds, 2) AS Refunds,
    ROUND(Other, 2) AS Other,
    ROUND(SUM(NetChange) OVER (ORDER BY FiscalYear), 2) AS Closing
FROM Flows
ORDER BY FiscalYear;""",
                [Check("years", yrs, lambda r: r.col("FiscalYear")),
                 Check("closing balances", [round(x, 2) for x in v["b2060"]], lambda r: r.col("Closing")),
                 Check("balances from the ledger", [round(n.balance_2060(d, y), 2) for y in yrs],
                       lambda r: r.col("Closing")),
                 Check("other postings", [0.0] * len(yrs), lambda r: r.col("Other")),
                 Check("opening of the first year", 0.0, lambda r: r.col("Opening")[0])])
    remember(b, "2060", q)
    items = {y: n.open_2060(d, y) for y in yrs}
    checks = [Check(f"{y} items", [x["number"] for x in items[y]],
                    lambda r, y=y: [x["CreditMemoNumber"] for x in dicts(r) if x["FiscalYear"] == y]) for y in yrs]
    checks += [Check(f"{y} items total the balance", round(v["b2060"][k], 2),
                     lambda r, y=y: round(sum(x["OpenIn2060"] for x in dicts(r) if x["FiscalYear"] == y), 2))
               for k, y in enumerate(yrs)]
    checks += [Check(f"{x['number']} open at {y}", x["amount"],
                     lambda r, y=y, num=x["number"]: r.where(FiscalYear=y, CreditMemoNumber=num)["OpenIn2060"])
               for y in yrs for x in items[y]]
    s.query("Requirement 2, test G7: the items in each year-end balance of 2060: credits not yet refunded",
            "Population: the credits' 2060 postings and the refunds to each year-end; expected: they equal G6",
            f"""\
WITH YearEnds AS (
    SELECT DISTINCT FiscalYear, FiscalYear || '-12-31' AS YearEnd
    FROM GLEntry
    WHERE FiscalYear BETWEEN {d.F} AND {d.C}
),
CreditsTo2060 AS (
    SELECT gl.SourceDocumentID AS CreditMemoID, gl.PostingDate,
        gl.Credit - gl.Debit AS Amount
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber = 2060 AND gl.SourceDocumentType = 'CreditMemo'
),
Posted AS (
    SELECT ye.FiscalYear, c.CreditMemoID, SUM(c.Amount) AS Posted
    FROM YearEnds AS ye
        INNER JOIN CreditsTo2060 AS c ON c.PostingDate <= ye.YearEnd
    GROUP BY ye.FiscalYear, c.CreditMemoID
),
Refunded AS (
    SELECT ye.FiscalYear, rf.CreditMemoID, SUM(rf.Amount) AS Refunded
    FROM YearEnds AS ye
        INNER JOIN CustomerRefund AS rf ON rf.RefundDate <= ye.YearEnd
    GROUP BY ye.FiscalYear, rf.CreditMemoID
)
SELECT p.FiscalYear, cm.CreditMemoNumber, cm.CreditMemoDate, cm.Status,
    ROUND(p.Posted - COALESCE(rd.Refunded, 0), 2) AS OpenIn2060
FROM Posted AS p
    INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = p.CreditMemoID
    LEFT JOIN Refunded AS rd
        ON rd.FiscalYear = p.FiscalYear
        AND rd.CreditMemoID = p.CreditMemoID
WHERE p.Posted - COALESCE(rd.Refunded, 0) > 0.005
ORDER BY p.FiscalYear, cm.CreditMemoNumber;""", checks)
    pending = n.clawbacks(d)["pending"]
    s.query(f"Requirement 2, test G8: account 2034 reconciled at {d.C}-12-31 to the commission records",
            "Population: accruals, commission payments, and clawbacks to the year-end; expected: no difference",
            f"""\
SELECT
    (SELECT ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2)
     FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
     WHERE a.AccountNumber = 2034
        AND gl.PostingDate <= '{d.C}-12-31') AS Balance2034,
    (SELECT ROUND(SUM(CommissionAmount), 2)
     FROM SalesCommissionAccrual
     WHERE AccrualDate <= '{d.C}-12-31') AS Accruals,
    (SELECT ROUND(SUM(NetPaymentAmount), 2)
     FROM SalesCommissionPayment
     WHERE PaymentDate <= '{d.C}-12-31') AS Payments,
    (SELECT ROUND(SUM(CommissionAdjustmentAmount), 2)
     FROM SalesCommissionAdjustment
     WHERE AdjustmentDate <= '{d.C}-12-31') AS Clawbacks,
    (SELECT COUNT(*)
     FROM SalesCommissionAdjustment AS sca
     WHERE NOT EXISTS (
        SELECT 1
        FROM SalesCommissionPaymentLine AS pl
        WHERE pl.SourceDocumentType = 'SalesCommissionAdjustment'
            AND pl.SourceDocumentID = sca.SalesCommissionAdjustmentID))
        AS ClawbacksNotYetNetted;""",
            [Check("2034 at the year-end", round(v["b2034"], 2), lambda r: r.value("Balance2034")),
             Check("accruals less payments less clawbacks", round(v["b2034"], 2),
                   lambda r: round(r.value("Accruals") - r.value("Payments") - r.value("Clawbacks"), 2)),
             Check("clawbacks pending at the year-end", pending, lambda r: r.value("ClawbacksNotYetNetted"))])
    n4060, a4060 = v["close_4060"]
    n6290, a6290 = v["close_6290"]
    s.query("Requirement 2, test G9: what the reconciliations leave out: the year-end closes on 4060 and 6290",
            "Population: the closes' rows on the two accounts; expected: one row a year on each",
            """\
SELECT a.AccountNumber, je.EntryNumber, je.PostingDate,
    ROUND(SUM(gl.Debit), 2) AS Debits, ROUND(SUM(gl.Credit), 2) AS Credits
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    INNER JOIN JournalEntry AS je ON je.EntryNumber = gl.VoucherNumber
WHERE a.AccountNumber IN (4060, 6290)
    AND je.EntryType LIKE 'Year-End Close%'
GROUP BY a.AccountNumber, je.EntryNumber, je.PostingDate
ORDER BY a.AccountNumber, je.PostingDate;""",
            [Check("closes on 4060", n4060, lambda r: sum(1 for x in dicts(r) if x["AccountNumber"] == 4060)),
             Check("closes on 4060, amount", round(a4060, 2),
                   lambda r: round(sum(x["Credits"] - x["Debits"] for x in dicts(r) if x["AccountNumber"] == 4060), 2)),
             Check("closes on 6290", n6290, lambda r: sum(1 for x in dicts(r) if x["AccountNumber"] == 6290)),
             Check("closes on 6290, amount", round(a6290, 2),
                   lambda r: round(sum(x["Credits"] - x["Debits"] for x in dicts(r) if x["AccountNumber"] == 6290), 2))])
    f_items = ", ".join(f"{x['number']} {money(x['amount'])}" for x in items[d.F])
    s.answer("Requirement 2", f"""\
Every population reconciles to the ledger to the cent in every year (G1 to G5): the credits' SubTotal equals the
debits to 4060 ({', '.join(money(x) for x in v['sub'])}), their freight 4050, their tax 2050, and their totals the
credits to 1020 and 2060; the returns' standard cost equals the debits to 1040 and the credits to cost of goods sold
by account; the refunds equal the credits to cash and the debits to 2060; the clawbacks equal the debits to 2034 and
the credits to 6290; and the receipts and applications equal the cash, 2060, and receivables postings.

Account 2060 is a hub: tens of millions pass through it each year (G6), while its balance at the year-ends is
{', '.join(money(x) for x in v['b2060'])}. Each balance is credits posted to 2060 and not yet refunded (G7):
{f_items} at the end of {d.F}; {', '.join(x['number'] for x in items[d.P])} at the end of {d.P}; and the
{len(items[d.C])} Issued credits {', '.join(x['number'] for x in items[d.C])} at the end of {d.C}. Account 2034 holds
{money(v['b2034'])} at {d.C}-12-31, the accruals less the payments and clawbacks (G8; {pending} clawbacks not yet netted
in a payment).

Excluded, and why: the year-end closes, {n4060} rows on 4060 ({money(a4060)}) and {n6290} on 6290 ({money(a6290)}) (G9),
which reverse the year's balances rather than record credits or commissions; and the ledger's {d.N} rows, which hold
only supplier payments. Each document is assigned to the year of its own date, the year its postings carry.""")


# --- Requirement 3 -----------------------------------------------------------------------------------------------

def r3(b):
    d, n = b.data, notes(b)
    v = context(b, "r3")
    s = script(b)
    s.query("Requirement 3, test P1: the return rate on revenue by year, and the expectation at the prior rate",
            "Population: debits to 4060 and SalesInvoice revenue postings, closes left out; expected: rising rates",
            f"""\
WITH Revenue AS (
    SELECT gl.FiscalYear, SUM(gl.Credit - gl.Debit) AS Revenue
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber IN (4010, 4020, 4030, 4040, 4080)
        AND gl.SourceDocumentType = 'SalesInvoice'
    GROUP BY gl.FiscalYear
),
Returns AS (
    SELECT gl.FiscalYear, SUM(gl.Debit) AS Returns4060
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber = 4060
    {CLOSES.replace(chr(10), chr(10) + '    ')}
    GROUP BY gl.FiscalYear
),
Rates AS (
    SELECT rv.FiscalYear, rv.Revenue, rt.Returns4060,
        rt.Returns4060 / rv.Revenue AS ReturnRate
    FROM Revenue AS rv
        INNER JOIN Returns AS rt ON rt.FiscalYear = rv.FiscalYear
    WHERE rv.FiscalYear BETWEEN {d.F} AND {d.C}
)
SELECT FiscalYear, ROUND(Revenue, 2) AS Revenue,
    ROUND(Returns4060, 2) AS Returns4060,
    ROUND(ReturnRate, 5) AS ReturnRate,
    ROUND(LAG(ReturnRate) OVER (ORDER BY FiscalYear) * Revenue, 2)
        AS ExpectedAtPriorRate,
    ROUND(Returns4060 - LAG(ReturnRate) OVER (ORDER BY FiscalYear)
        * Revenue, 2) AS Difference
FROM Rates
ORDER BY FiscalYear;""",
            [Check("revenue by year", [round(x, 2) for x in v["revenue"]], lambda r: r.col("Revenue")),
             Check("rates by year", [round(x, 5) for x in v["rates"]], lambda r: r.col("ReturnRate")),
             Check(f"{d.C} returns", round(v["actual"], 2), lambda r: r.where(FiscalYear=d.C)["Returns4060"]),
             Check(f"{d.C} expectation at the {d.P} rate", round(v["exp"], 2),
                   lambda r: r.where(FiscalYear=d.C)["ExpectedAtPriorRate"]),
             Check("difference", round(v["diff"], 2), lambda r: r.where(FiscalYear=d.C)["Difference"]),
             Check("difference as a share of the expectation", round(v["diff_pct"], 3),
                   lambda r: round(r.where(FiscalYear=d.C)["Returns4060"]
                                   / r.where(FiscalYear=d.C)["ExpectedAtPriorRate"] - 1, 3), 0.0006),
             Check(f"{d.C} expectation at the {d.F} rate", round(v["exp_f"], 2),
                   lambda r: round(r.where(FiscalYear=d.F)["Returns4060"] / r.where(FiscalYear=d.F)["Revenue"]
                                   * r.where(FiscalYear=d.C)["Revenue"], 2)),
             Check(f"{d.C} returns over the {d.F}-rate expectation", round(v["f_pct"], 3),
                   lambda r: round(r.where(FiscalYear=d.C)["Returns4060"]
                                   / (r.where(FiscalYear=d.F)["Returns4060"] / r.where(FiscalYear=d.F)["Revenue"]
                                      * r.where(FiscalYear=d.C)["Revenue"]) - 1, 3), 0.0006)])
    s.query("Requirement 3, test P2: income before income taxes as recorded (the base of materiality)",
            "Population: revenue and expense postings, closes left out (no tax account); expected: one row a year",
            f"""\
SELECT gl.FiscalYear,
    ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS IncomeBeforeTaxes
FROM GLEntry AS gl
    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
WHERE a.AccountType IN ('Revenue', 'Expense')
    AND gl.FiscalYear BETWEEN {d.F} AND {d.C}
{CLOSES}
GROUP BY gl.FiscalYear
ORDER BY gl.FiscalYear;""",
            [Check(f"{d.C} income before income taxes", round(v["income"], 2),
                   lambda r: r.where(FiscalYear=d.C)["IncomeBeforeTaxes"]),
             Check("materiality (5%)", round(v["mat"], 2),
                   lambda r: round(n.MATERIALITY * r.where(FiscalYear=d.C)["IncomeBeforeTaxes"], 2)),
             Check("performance materiality (75%)", round(v["perf"], 2),
                   lambda r: round(n.MATERIALITY * n.PERFORMANCE * r.where(FiscalYear=d.C)["IncomeBeforeTaxes"], 2)),
             Check("clearly trivial (5%)", round(v["trivial"], 2),
                   lambda r: round(n.MATERIALITY * n.TRIVIAL * r.where(FiscalYear=d.C)["IncomeBeforeTaxes"], 2))])


# --- Requirement 4 -----------------------------------------------------------------------------------------------

def year_of(day: str) -> int:
    return int(day[:4])


def r4(b):
    d, n = b.data, notes(b)
    v = context(b, "r4")
    c, t = n.cycle(d), n.tests(d)
    s = script(b)
    yrs = d.years
    am = n.accounting_manager(d)
    # T1: authority, by document and approver's job title
    expect = {}
    for doc, items, key in (("CreditMemo", c.cm.values(), "gt"), ("CustomerRefund", c.rf.values(), "amt")):
        for x in items:
            title = c.emp[x["appr"]]["title"]
            e = expect.setdefault((doc, title), [0, 0.0, 0, 0.0])
            e[0] += 1
            e[1] += x[key]
            if x[key] > c.emp[x["appr"]]["limit"]:
                e[2] += 1
                e[3] += x[key]
    checks = [Check("document and job title rows", len(expect), len)]
    for (doc, title), (k, amt, above, above_amt) in expect.items():
        checks += [Check(f"{doc} by {title}", k, lambda r, doc=doc, ti=title: r.where(Document=doc, JobTitle=ti)["Documents"]),
                   Check(f"{doc} by {title}, above the limit", above,
                         lambda r, doc=doc, ti=title: r.where(Document=doc, JobTitle=ti)["AboveLimit"]),
                   Check(f"{doc} by {title}, amount above the limit", round(above_amt, 2),
                         lambda r, doc=doc, ti=title: r.where(Document=doc, JobTitle=ti)["AboveLimitAmount"])]
    checks += [Check("credits above the limit", v["cm_above"]["n"],
                     lambda r: sum(x["AboveLimit"] for x in dicts(r) if x["Document"] == "CreditMemo")),
               Check("credits above the limit, amount", v["cm_above"]["amt"],
                     lambda r: round(sum(x["AboveLimitAmount"] for x in dicts(r) if x["Document"] == "CreditMemo"), 2)),
               Check("refunds above the limit", v["rf_above"]["n"],
                     lambda r: sum(x["AboveLimit"] for x in dicts(r) if x["Document"] == "CustomerRefund")),
               Check("refunds above the limit, amount", v["rf_above"]["amt"],
                     lambda r: round(sum(x["AboveLimitAmount"] for x in dicts(r)
                                         if x["Document"] == "CustomerRefund"), 2)),
               Check("the credit approvers above their limit (limit 0)", [(n.CSR, 0.0)],
                     lambda r: [(x["JobTitle"], x["HighestLimit"]) for x in dicts(r)
                                if x["Document"] == "CreditMemo" and x["AboveLimit"]]),
               Check("the Accounting Manager's refunds within limit", (v["within"]["n"], 0),
                     lambda r: (r.where(Document="CustomerRefund", JobTitle="Accounting Manager")["Documents"],
                                r.where(Document="CustomerRefund", JobTitle="Accounting Manager")["AboveLimit"])),
               Check("the Accounting Manager's refunds, amount", v["within"]["amt"],
                     lambda r: r.where(Document="CustomerRefund", JobTitle="Accounting Manager")["Amount"])]
    s.query("Requirement 4, test T1: authority for credits and refunds against the approver's limit, by job title",
            "Population: every credit and refund (MaxApprovalAmount, blank as 0); expected: none above the limit",
            """\
WITH Approvals AS (
    SELECT 'CreditMemo' AS Document, cm.GrandTotal AS Amount,
        cm.ApprovedByEmployeeID AS EmployeeID
    FROM CreditMemo AS cm
    UNION ALL
    SELECT 'CustomerRefund', rf.Amount, rf.ApprovedByEmployeeID
    FROM CustomerRefund AS rf
)
SELECT ap.Document, e.JobTitle, COUNT(*) AS Documents,
    ROUND(SUM(ap.Amount), 2) AS Amount,
    MAX(COALESCE(e.MaxApprovalAmount, 0)) AS HighestLimit,
    SUM(CASE WHEN ap.Amount > COALESCE(e.MaxApprovalAmount, 0)
        THEN 1 ELSE 0 END) AS AboveLimit,
    ROUND(SUM(CASE WHEN ap.Amount > COALESCE(e.MaxApprovalAmount, 0)
        THEN ap.Amount ELSE 0 END), 2) AS AboveLimitAmount
FROM Approvals AS ap
    INNER JOIN Employee AS e ON e.EmployeeID = ap.EmployeeID
GROUP BY ap.Document, e.JobTitle
ORDER BY ap.Document, Documents DESC;""", checks)
    s.query("Requirement 4, test T2: documents recorded or approved outside the person's employment dates",
            "Population: every return, credit, refund, clawback, receipt, and application; expected: no rows",
            """\
WITH People AS (
    SELECT ReturnNumber AS DocumentNumber, ReturnDate AS DocumentDate,
        ReceivedByEmployeeID AS EmployeeID
    FROM SalesReturn
    UNION ALL
    SELECT CreditMemoNumber, CreditMemoDate, ApprovedByEmployeeID
    FROM CreditMemo
    UNION ALL
    SELECT RefundNumber, RefundDate, ApprovedByEmployeeID
    FROM CustomerRefund
    UNION ALL
    SELECT AdjustmentNumber, AdjustmentDate, ApprovedByEmployeeID
    FROM SalesCommissionAdjustment
    UNION ALL
    SELECT ReceiptNumber, ReceiptDate, RecordedByEmployeeID
    FROM CashReceipt
    UNION ALL
    SELECT CAST(CashReceiptApplicationID AS TEXT), ApplicationDate,
        AppliedByEmployeeID
    FROM CashReceiptApplication
)
SELECT p.DocumentNumber, p.DocumentDate, e.EmployeeID, e.JobTitle,
    e.HireDate, e.TerminationDate
FROM People AS p
    INNER JOIN Employee AS e ON e.EmployeeID = p.EmployeeID
WHERE p.DocumentDate < e.HireDate
    OR (e.TerminationDate IS NOT NULL
        AND p.DocumentDate > e.TerminationDate)
ORDER BY p.DocumentDate;""",
            [Check("documents outside employment", 0, len)])
    cc_ids = {m["id"] for m in t.cash_credit}
    early_ids = {m["id"] for m in t.cc_early}
    s.query("Requirement 4, test T3: separation of duties: the credit's approver handled the invoice's cash",
            "Population: every credit and the receipts applied to its invoice; expected: no rows",
            """\
WITH Handled AS (
    SELECT cm.CreditMemoID,
        MAX(CASE WHEN cra.AppliedByEmployeeID = cm.ApprovedByEmployeeID
            THEN 1 ELSE 0 END) AS AppliedCash,
        MAX(CASE WHEN cra.AppliedByEmployeeID = cm.ApprovedByEmployeeID
                AND cra.ApplicationDate <= cm.CreditMemoDate
            THEN 1 ELSE 0 END) AS AppliedByCreditDate,
        MAX(CASE WHEN cr.RecordedByEmployeeID = cm.ApprovedByEmployeeID
            THEN 1 ELSE 0 END) AS RecordedCash
    FROM CreditMemo AS cm
        INNER JOIN CashReceiptApplication AS cra
            ON cra.SalesInvoiceID = cm.OriginalSalesInvoiceID
        INNER JOIN CashReceipt AS cr ON cr.CashReceiptID = cra.CashReceiptID
    GROUP BY cm.CreditMemoID
)
SELECT cm.CreditMemoNumber, cm.CreditMemoDate,
    CAST(strftime('%Y', cm.CreditMemoDate) AS INTEGER) AS FiscalYear,
    ROUND(cm.GrandTotal, 2) AS GrandTotal,
    cm.ApprovedByEmployeeID, h.AppliedCash, h.AppliedByCreditDate,
    h.RecordedCash
FROM Handled AS h
    INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = h.CreditMemoID
WHERE h.AppliedCash = 1 OR h.RecordedCash = 1
ORDER BY cm.CreditMemoNumber;""",
            [Check("credits whose approver recorded or applied the invoice's cash", v["cc_rec"]["n"], len),
             Check("amount", v["cc_rec"]["amt"], lambda r: r.total("GrandTotal")),
             Check("credits whose approver applied the invoice's cash", v["cc"]["n"],
                   lambda r: r.total("AppliedCash")),
             Check("those credits, amount", v["cc"]["amt"],
                   lambda r: round(sum(x["GrandTotal"] for x in dicts(r) if x["AppliedCash"]), 2)),
             Check("by year", v["cc"]["years"],
                   lambda r: by_year([x for x in dicts(r) if x["AppliedCash"]], "FiscalYear", yrs)),
             Check(f"{d.C} amount", v["cc"]["cur"][1],
                   lambda r: round(sum(x["GrandTotal"] for x in dicts(r) if x["AppliedCash"]
                                       and x["FiscalYear"] == d.C), 2)),
             Check("applied on or before the credit date", v["cc_early"]["n"], lambda r: r.total("AppliedByCreditDate")),
             Check("those credits, amount", v["cc_early"]["amt"],
                   lambda r: round(sum(x["GrandTotal"] for x in dicts(r) if x["AppliedByCreditDate"]), 2)),
             Check("the credits applied by the approver", sorted(c.cm[i]["num"] for i in cc_ids),
                   lambda r: [x["CreditMemoNumber"] for x in dicts(r) if x["AppliedCash"]]),
             Check("early ones", len(early_ids), lambda r: sum(1 for x in dicts(r) if x["AppliedByCreditDate"])),
             Check(f"early ones in {d.C}", v["cc_early"]["cur"],
                   lambda r: sum(1 for x in dicts(r) if x["AppliedByCreditDate"] and x["FiscalYear"] == d.C))])
    s.query("Requirement 4, test T4: the refund's approver and the return's receiver against the credit's approver",
            "Population: every refund and credit; expected: never the same person, returns received in the warehouse",
            """\
SELECT
    (SELECT COUNT(*)
     FROM CustomerRefund AS rf
        INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
     WHERE rf.ApprovedByEmployeeID = cm.ApprovedByEmployeeID)
        AS RefundApprovedByCreditApprover,
    (SELECT COUNT(*)
     FROM CreditMemo AS cm
        INNER JOIN SalesReturn AS sr ON sr.SalesReturnID = cm.SalesReturnID
     WHERE sr.ReceivedByEmployeeID = cm.ApprovedByEmployeeID)
        AS ReturnReceivedByCreditApprover,
    (SELECT COUNT(*)
     FROM SalesReturn AS sr
        INNER JOIN Employee AS e ON e.EmployeeID = sr.ReceivedByEmployeeID
        INNER JOIN CostCenter AS cc ON cc.CostCenterID = e.CostCenterID
     WHERE cc.CostCenterName <> 'Warehouse') AS ReceivedOutsideWarehouse;""",
            [Check("refunds approved by the credit's approver", 0, lambda r: r.value("RefundApprovedByCreditApprover")),
             Check("returns received by the credit's approver", 0, lambda r: r.value("ReturnReceivedByCreditApprover")),
             Check("returns received outside the warehouse", 0, lambda r: r.value("ReceivedOutsideWarehouse"))])
    people = [("SalesReturn", "SalesReturnID", "ReceivedByEmployeeID"),
              ("CreditMemo", "CreditMemoID", "ApprovedByEmployeeID"),
              ("CustomerRefund", "CustomerRefundID", "ApprovedByEmployeeID"),
              ("SalesCommissionAdjustment", "SalesCommissionAdjustmentID", "ApprovedByEmployeeID"),
              ("CashReceipt", "CashReceiptID", "RecordedByEmployeeID"),
              ("CashReceiptApplication", "CashReceiptApplicationID", "AppliedByEmployeeID")]
    ledger_rows = dict(d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry GROUP BY 1"))
    cm_rows, rf_rows = ledger_rows["CreditMemo"], ledger_rows["CustomerRefund"]
    parts = []
    for k, (doc, key, col) in enumerate(people):
        parts.append(f"""SELECT '{doc}'{' AS Document' if k == 0 else ''},
    '{col}'{' AS NamedPerson' if k == 0 else ''},
    COUNT(*){' AS LedgerRows' if k == 0 else ''},
    SUM(CASE WHEN gl.CreatedByEmployeeID = x.{col}
        THEN 1 ELSE 0 END){' AS CreatedByThatPerson' if k == 0 else ''}
FROM GLEntry AS gl
    INNER JOIN {doc} AS x
        ON x.{key} = gl.SourceDocumentID
WHERE gl.SourceDocumentType = '{doc}'""")
    for doc in ("SalesInvoice", "DisbursementPayment"):
        parts.append(f"""SELECT '{doc}', 'none: ' || MIN(e.JobTitle), COUNT(*),
    COUNT(DISTINCT gl.CreatedByEmployeeID)
FROM GLEntry AS gl
    INNER JOIN Employee AS e ON e.EmployeeID = gl.CreatedByEmployeeID
WHERE gl.SourceDocumentType = '{doc}'""")
    checks = [Check(f"{t} rows created by the person the document names", ledger_rows[t],
                    lambda r, t=t: r.where(Document=t)["CreatedByThatPerson"]) for t, key, col in people]
    checks += [Check(f"{t} rows", ledger_rows[t], lambda r, t=t: r.where(Document=t)["LedgerRows"])
               for t, key, col in people]
    checks += [Check("sales invoice rows created by", ["none: Chief Executive Officer", 1],
                     lambda r: [r.where(Document="SalesInvoice")[k] for k in ("NamedPerson", "CreatedByThatPerson")]),
               Check("supplier payment rows created by", ["none: Chief Financial Officer", 1],
                     lambda r: [r.where(Document="DisbursementPayment")[k]
                                for k in ("NamedPerson", "CreatedByThatPerson")])]
    s.query("Requirement 4, test T5: the preparer against the approver: whom GLEntry.CreatedByEmployeeID names",
            "Population: ledger rows of the cycle, sales invoices, and supplier payments; expected: a separate preparer",
            "\nUNION ALL\n".join(parts) + ";", checks)
    before = v["before"]
    s.query("Requirement 4, test T6: refunds dated before the last payment on the credited invoice",
            "Population: every refund and the applications to its credit's invoice; expected: no rows",
            """\
WITH LastPayment AS (
    SELECT SalesInvoiceID, MAX(ApplicationDate) AS LastPaymentDate
    FROM CashReceiptApplication
    GROUP BY SalesInvoiceID
)
SELECT rf.RefundNumber, rf.RefundDate,
    CAST(strftime('%Y', rf.RefundDate) AS INTEGER) AS FiscalYear,
    ROUND(rf.Amount, 2) AS Amount, si.InvoiceNumber, si.DueDate,
    lp.LastPaymentDate,
    julianday(lp.LastPaymentDate) - julianday(rf.RefundDate)
        AS DaysUntilPaid,
    CASE WHEN rf.RefundDate < si.DueDate THEN 1 ELSE 0 END
        AS BeforeDueDate,
    CASE WHEN NOT EXISTS (
            SELECT 1
            FROM CashReceiptApplication AS cra
            WHERE cra.SalesInvoiceID = si.SalesInvoiceID
                AND cra.ApplicationDate <= rf.RefundDate)
        THEN 1 ELSE 0 END AS NothingPaidYet
FROM CustomerRefund AS rf
    INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
    INNER JOIN SalesInvoice AS si
        ON si.SalesInvoiceID = cm.OriginalSalesInvoiceID
    INNER JOIN LastPayment AS lp ON lp.SalesInvoiceID = si.SalesInvoiceID
WHERE lp.LastPaymentDate > rf.RefundDate
ORDER BY rf.RefundNumber;""",
            [Check("refunds before the payment", before["n"], len),
             Check("amount", before["amt"], lambda r: r.total("Amount")),
             Check("by year", before["years"], lambda r: by_year(dicts(r), "FiscalYear", yrs)),
             Check(f"{d.C} amount", before["cur"][1],
                   lambda r: round(sum(x["Amount"] for x in dicts(r) if x["FiscalYear"] == d.C), 2)),
             Check("before any payment", v["nothing"]["n"], lambda r: r.total("NothingPaidYet")),
             Check("before any payment, amount", v["nothing"]["amt"],
                   lambda r: round(sum(x["Amount"] for x in dicts(r) if x["NothingPaidYet"]), 2)),
             Check(f"before any payment in {d.C}", list(v["nothing"]["cur"]),
                   lambda r: [sum(1 for x in dicts(r) if x["NothingPaidYet"] and x["FiscalYear"] == d.C),
                              round(sum(x["Amount"] for x in dicts(r) if x["NothingPaidYet"]
                                        and x["FiscalYear"] == d.C), 2)]),
             Check("also before the due date", v["before_due"], lambda r: r.total("BeforeDueDate")),
             Check("fewest days until paid", v["wait"]["lo"], lambda r: min(r.col("DaysUntilPaid"))),
             Check("most days until paid", v["wait"]["hi"], lambda r: max(r.col("DaysUntilPaid"))),
             Check("mean days until paid", round(v["wait"]["mean"], 1),
                   lambda r: round(sum(r.col("DaysUntilPaid")) / len(r), 1), 0.051)])
    s.query("Requirement 4, test T7: the cause of T6: credits posted to 2060 while nothing was paid",
            "Population: the credits' postings to 1020 and 2060; expected: credits on unpaid invoices reduce 1020",
            """\
WITH Parts AS (
    SELECT gl.SourceDocumentID AS CreditMemoID,
        SUM(CASE WHEN a.AccountNumber = 1020 THEN gl.Credit ELSE 0 END)
            AS To1020,
        SUM(CASE WHEN a.AccountNumber = 2060 THEN gl.Credit ELSE 0 END)
            AS To2060
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType = 'CreditMemo'
    GROUP BY gl.SourceDocumentID
)
SELECT COUNT(*) AS Credits,
    SUM(CASE WHEN p.To2060 > 0 THEN 1 ELSE 0 END) AS CreditsTo2060,
    SUM(CASE WHEN p.To2060 > 0 AND p.To1020 > 0 THEN 1 ELSE 0 END)
        AS CreditsToBoth,
    SUM(CASE WHEN p.To2060 > 0 AND NOT EXISTS (
            SELECT 1
            FROM CashReceiptApplication AS cra
            WHERE cra.SalesInvoiceID = cm.OriginalSalesInvoiceID
                AND cra.ApplicationDate <= cm.CreditMemoDate)
        THEN 1 ELSE 0 END) AS To2060WithNothingPaid
FROM Parts AS p
    INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = p.CreditMemoID;""",
            [Check("credits", len(c.cm), lambda r: r.value("Credits")),
             Check("credits to 2060", v["to_2060"], lambda r: r.value("CreditsTo2060")),
             Check("credits to both", context(b, "r1")["both"], lambda r: r.value("CreditsToBoth")),
             Check("credits to 2060 with nothing paid", v["unpaid_2060"], lambda r: r.value("To2060WithNothingPaid"))])
    cb = n.clawbacks(d)
    off = sorted(a["num"] for a in cb["off"])
    s.query("Requirement 4, test T8: the clawbacks tested for completeness and accuracy",
            "Population: every credit line and clawback; expected: one per line, the accrual's rate, exact amounts",
            """\
SELECT 'Credit line without a clawback' AS Issue,
    CAST(cml.CreditMemoLineID AS TEXT) AS Document, NULL AS Base,
    NULL AS Rate, NULL AS Amount, NULL AS Recomputed
FROM CreditMemoLine AS cml
WHERE NOT EXISTS (
    SELECT 1
    FROM SalesCommissionAdjustment AS sca
    WHERE sca.CreditMemoLineID = cml.CreditMemoLineID)
UNION ALL
SELECT 'Base is not the line total', sca.AdjustmentNumber,
    sca.CommissionBaseReductionAmount, sca.CommissionRatePct,
    sca.CommissionAdjustmentAmount, cml.LineTotal
FROM SalesCommissionAdjustment AS sca
    INNER JOIN CreditMemoLine AS cml
        ON cml.CreditMemoLineID = sca.CreditMemoLineID
WHERE ABS(sca.CommissionBaseReductionAmount - cml.LineTotal) > 0.004
UNION ALL
SELECT 'Rate is not the accrual''s', sca.AdjustmentNumber,
    sca.CommissionBaseReductionAmount, sca.CommissionRatePct,
    sca.CommissionAdjustmentAmount, sac.CommissionRatePct
FROM SalesCommissionAdjustment AS sca
    INNER JOIN SalesCommissionAccrual AS sac
        ON sac.SalesCommissionAccrualID = sca.SalesCommissionAccrualID
WHERE ABS(sca.CommissionRatePct - sac.CommissionRatePct) > 0.0000001
UNION ALL
SELECT 'Amount is not ROUND(base x rate, 2)', sca.AdjustmentNumber,
    sca.CommissionBaseReductionAmount, sca.CommissionRatePct,
    sca.CommissionAdjustmentAmount,
    ROUND(sca.CommissionBaseReductionAmount * sca.CommissionRatePct, 2)
FROM SalesCommissionAdjustment AS sca
WHERE ABS(sca.CommissionAdjustmentAmount - ROUND(
    sca.CommissionBaseReductionAmount * sca.CommissionRatePct, 2)) > 0.004
UNION ALL
SELECT 'Not the credit''s date or approver', sca.AdjustmentNumber,
    NULL, NULL, sca.CommissionAdjustmentAmount, NULL
FROM SalesCommissionAdjustment AS sca
    INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = sca.CreditMemoID
WHERE sca.AdjustmentDate <> cm.CreditMemoDate
    OR sca.ApprovedByEmployeeID <> cm.ApprovedByEmployeeID
ORDER BY Issue, Document;""",
            [Check("exceptions (half-cent products only)", len(off), len),
             Check("the clawbacks SQLite's ROUND puts a cent lower", off, lambda r: r.col("Document")),
             Check("each a cent above SQLite's ROUND", [0.01] * len(off),
                   lambda r: [round(a - x, 2) for a, x in zip(r.col("Amount"), r.col("Recomputed"))]),
             Check("each an exact half-cent product", [0.5] * len(off),
                   lambda r: [round(bs * rt * 100 % 1, 6) for bs, rt in zip(r.col("Base"), r.col("Rate"))])])
    s.query("Requirement 4, test T9: one refund per credit, equal to the credit's part posted to 2060",
            "Population: every refund and refunded credit; expected: one each, equal amounts",
            """\
WITH To2060 AS (
    SELECT gl.SourceDocumentID AS CreditMemoID, SUM(gl.Credit) AS To2060
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.SourceDocumentType = 'CreditMemo' AND a.AccountNumber = 2060
    GROUP BY gl.SourceDocumentID
)
SELECT COUNT(*) AS Refunds,
    COUNT(DISTINCT rf.CreditMemoID) AS CreditsRefunded,
    (SELECT COUNT(*)
     FROM CreditMemo
     WHERE Status = 'Refunded') AS CreditsWithStatusRefunded,
    SUM(CASE WHEN ABS(rf.Amount - COALESCE(t.To2060, 0)) < 0.005
        THEN 1 ELSE 0 END) AS RefundEqualTo2060Part
FROM CustomerRefund AS rf
    LEFT JOIN To2060 AS t ON t.CreditMemoID = rf.CreditMemoID;""",
            [Check("refunds", v["n_refunds"], lambda r: r.value("Refunds")),
             Check("credits refunded", v["n_refunds"], lambda r: r.value("CreditsRefunded")),
             Check("credits with status Refunded", v["n_refunds"], lambda r: r.value("CreditsWithStatusRefunded")),
             Check("refunds equal to the credit's 2060 part", v["equal_2060"], lambda r: r.value("RefundEqualTo2060Part"))])
    # T10: the refund flags, as RefundFlags.csv holds them
    flags = {r["num"]: (t.flags[k], t.score[k], t.pdue[k]) for k, r in c.rf.items()}
    scores = Counter(t.score.values())
    high = [r for k, r in c.rf.items() if t.score[k] >= 4]
    flag_cols = ["AboveLimit", "CreditAboveLimit", "MethodMismatch", "BeforePayment", "PastDueAtLeastRefund"]
    s.query("Requirement 4, test T10: the refund flags, one row per refund (Export to CSV as RefundFlags.csv)",
            "Population: every refund; definitions in the case text; expected: flags concentrated on few refunds",
            REFUND_FLAGS_SQL.strip() if REFUND_FLAGS_SQL.strip().endswith(";") else REFUND_FLAGS_SQL.strip() + ";",
            [Check("refunds", len(c.rf), len),
             Check("every refund's five flags and score equal the notes' definitions", True,
                   lambda r: all([x[col] for col in flag_cols] == [int(f) for f in flags[x["RefundNumber"]][0]]
                                 and x["Score"] == flags[x["RefundNumber"]][1]
                                 and abs(x["PastDue"] - round(flags[x["RefundNumber"]][2], 2)) < 0.001
                                 for x in dicts(r))),
             Check("refunds above the limit", v["rf_above"]["n"], lambda r: r.total("AboveLimit")),
             Check("refunds of credits above the limit", sum(f[0][1] for f in flags.values()),
                   lambda r: r.total("CreditAboveLimit")),
             Check("method mismatch", v["mism"]["n"], lambda r: r.total("MethodMismatch")),
             Check("method mismatch, amount", v["mism"]["amt"],
                   lambda r: round(sum(x["Amount"] for x in dicts(r) if x["MethodMismatch"]), 2)),
             Check(f"method mismatch in {d.C}", v["mism"]["cur"][0],
                   lambda r: sum(1 for x in dicts(r) if x["MethodMismatch"] and x["FiscalYear"] == d.C)),
             Check("before payment", v["before"]["n"], lambda r: r.total("BeforePayment")),
             Check("past due on the refund date", v["pd1"]["n"], lambda r: r.total("PastDueAny")),
             Check("past due on the refund date, refunds' amount", v["pd1"]["amt"],
                   lambda r: round(sum(x["Amount"] for x in dicts(r) if x["PastDueAny"]), 2)),
             Check("past due at least the refund", v["pd2"]["n"], lambda r: r.total("PastDueAtLeastRefund")),
             Check("past due at least the refund, amount", v["pd2"]["amt"],
                   lambda r: round(sum(x["Amount"] for x in dicts(r) if x["PastDueAtLeastRefund"]), 2)),
             Check(f"past due at least the refund in {d.C}", list(v["pd2"]["cur"]),
                   lambda r: [sum(1 for x in dicts(r) if x["PastDueAtLeastRefund"] and x["FiscalYear"] == d.C),
                              round(sum(x["Amount"] for x in dicts(r) if x["PastDueAtLeastRefund"]
                                        and x["FiscalYear"] == d.C), 2)]),
             Check("scores 0 to 5", [scores.get(k, 0) for k in range(6)],
                   lambda r: [sum(1 for x in r.col("Score") if x == k) for k in range(6)]),
             Check("refunds scoring 4 or 5, amount", round(sum(x["amt"] for x in high), 2),
                   lambda r: round(sum(x["Amount"] for x in dicts(r) if x["Score"] >= 4), 2))])
    # T11: the four rule tests' exceptions in one list
    expected = {"CM AboveLimit": [(m["num"], m["date"], m["gt"]) for m in t.cm_above],
                "CM CashAndCredit": [(m["num"], m["date"], m["gt"]) for m in t.cash_credit],
                "RF AboveLimit": [(r["num"], r["date"], r["amt"]) for r in t.rf_above],
                "RF BeforePayment": [(r["num"], r["date"], r["amt"]) for r in t.before]}
    checks = [Check("exceptions", sum(len(x) for x in expected.values()), len),
              Check("tests", list(TESTS), lambda r: sorted(set(r.col("TestID")))),
              Check("each test and document once", sum(len(x) for x in expected.values()),
                    lambda r: len(set(zip(r.col("TestID"), r.col("DocumentNumber")))))]
    for k, xs in expected.items():
        checks += [Check(f"{k} documents", sorted(x[0] for x in xs),
                         lambda r, k=k: sorted(x["DocumentNumber"] for x in dicts(r) if x["TestID"] == k)),
                   Check(f"{k} by year", [sum(1 for x in xs if year_of(x[1]) == y) for y in yrs],
                         lambda r, k=k: by_year([x for x in dicts(r) if x["TestID"] == k], "FiscalYear", yrs)),
                   Check(f"{k} amount", round(sum(x[2] for x in xs), 2),
                         lambda r, k=k: round(sum(x["Amount"] for x in dicts(r) if x["TestID"] == k), 2))]
    current = {"CM AboveLimit": v["cm_above"]["cur"], "CM CashAndCredit": v["cc"]["cur"],
               "RF AboveLimit": v["rf_above"]["cur"], "RF BeforePayment": v["before"]["cur"]}
    checks += [Check(f"{k} in {d.C}", list(x),
                     lambda r, k=k: [sum(1 for y in dicts(r) if y["TestID"] == k and y["FiscalYear"] == d.C),
                                     round(sum(y["Amount"] for y in dicts(r) if y["TestID"] == k
                                               and y["FiscalYear"] == d.C), 2)])
               for k, x in current.items()]
    q = s.query("Requirement 4, test T11: the exceptions of the four rule tests in one list by year (UNION ALL)",
                "Population: tests T1, T3, and T6 on every credit and refund; expected: no rows",
                """\
WITH LastPayment AS (
    SELECT SalesInvoiceID, MAX(ApplicationDate) AS LastPaymentDate
    FROM CashReceiptApplication
    GROUP BY SalesInvoiceID
),
Exceptions AS (
    SELECT 'CM AboveLimit' AS TestID, cm.CreditMemoNumber AS DocumentNumber,
        cm.CreditMemoDate AS DocumentDate, cm.GrandTotal AS Amount
    FROM CreditMemo AS cm
        INNER JOIN Employee AS e ON e.EmployeeID = cm.ApprovedByEmployeeID
    WHERE cm.GrandTotal > COALESCE(e.MaxApprovalAmount, 0)
    UNION ALL
    SELECT 'CM CashAndCredit', cm.CreditMemoNumber, cm.CreditMemoDate,
        cm.GrandTotal
    FROM CreditMemo AS cm
    WHERE EXISTS (
        SELECT 1
        FROM CashReceiptApplication AS cra
        WHERE cra.SalesInvoiceID = cm.OriginalSalesInvoiceID
            AND cra.AppliedByEmployeeID = cm.ApprovedByEmployeeID)
    UNION ALL
    SELECT 'RF AboveLimit', rf.RefundNumber, rf.RefundDate, rf.Amount
    FROM CustomerRefund AS rf
        INNER JOIN Employee AS e ON e.EmployeeID = rf.ApprovedByEmployeeID
    WHERE rf.Amount > COALESCE(e.MaxApprovalAmount, 0)
    UNION ALL
    SELECT 'RF BeforePayment', rf.RefundNumber, rf.RefundDate, rf.Amount
    FROM CustomerRefund AS rf
        INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
        INNER JOIN LastPayment AS lp
            ON lp.SalesInvoiceID = cm.OriginalSalesInvoiceID
    WHERE lp.LastPaymentDate > rf.RefundDate
)
SELECT CAST(strftime('%Y', DocumentDate) AS INTEGER) AS FiscalYear,
    TestID, DocumentNumber, DocumentDate, ROUND(Amount, 2) AS Amount
FROM Exceptions
ORDER BY FiscalYear, TestID, DocumentNumber;""", checks)
    remember(b, "exceptions", q)
    design = n.commission_design(d)
    registers = d.one("SELECT COUNT(*) FROM PayrollRegister")
    by_am = d.one("SELECT COUNT(*) FROM PayrollRegister WHERE ApprovedByEmployeeID = ?", am)
    s.query("Requirement 4, test T12: the Accounting Manager's share of the cycle's and payroll's approvals",
            "Population: commission rates, accruals, payments, refunds, and payroll registers; expected: spread out",
            """\
WITH Manager AS (
    SELECT EmployeeID
    FROM Employee
    WHERE JobTitle = 'Accounting Manager'
)
SELECT 'Commission rates approved' AS Activity, COUNT(*) AS Documents,
    SUM(CASE WHEN ApprovedByEmployeeID IN (SELECT EmployeeID FROM Manager)
        THEN 1 ELSE 0 END) AS ByAccountingManager
FROM SalesCommissionRate
UNION ALL
SELECT 'Commission accruals created', COUNT(*),
    SUM(CASE WHEN CreatedByEmployeeID IN (SELECT EmployeeID FROM Manager)
        THEN 1 ELSE 0 END)
FROM SalesCommissionAccrual
UNION ALL
SELECT 'Commission payments approved', COUNT(*),
    SUM(CASE WHEN ApprovedByEmployeeID IN (SELECT EmployeeID FROM Manager)
        THEN 1 ELSE 0 END)
FROM SalesCommissionPayment
UNION ALL
SELECT 'Refunds approved', COUNT(*),
    SUM(CASE WHEN ApprovedByEmployeeID IN (SELECT EmployeeID FROM Manager)
        THEN 1 ELSE 0 END)
FROM CustomerRefund
UNION ALL
SELECT 'Payroll registers approved', COUNT(*),
    SUM(CASE WHEN ApprovedByEmployeeID IN (SELECT EmployeeID FROM Manager)
        THEN 1 ELSE 0 END)
FROM PayrollRegister;""",
            [Check("commission rates", [design["rates"]] * 2,
                   lambda r: [r.where(Activity="Commission rates approved")[k] for k in ("Documents", "ByAccountingManager")]),
             Check("accruals", [design["accruals"]] * 2,
                   lambda r: [r.where(Activity="Commission accruals created")[k]
                              for k in ("Documents", "ByAccountingManager")]),
             Check("commission payments", [design["payments"]] * 2,
                   lambda r: [r.where(Activity="Commission payments approved")[k]
                              for k in ("Documents", "ByAccountingManager")]),
             Check("refunds", [len(c.rf), v["within"]["n"]],
                   lambda r: [r.where(Activity="Refunds approved")[k] for k in ("Documents", "ByAccountingManager")]),
             Check("payroll registers", [registers, by_am],
                   lambda r: [r.where(Activity="Payroll registers approved")[k]
                              for k in ("Documents", "ByAccountingManager")])])
    s.answer("Requirement 4", f"""\
Definitions used. Authority: a document above its approver's MaxApprovalAmount (a blank limit read as 0), the only
authority the records hold; a delegation of authority for credits and refunds, if one exists, is outside them. Cash and
credit: the credit's approver applied a receipt to the credited invoice (T3; recorded or applied, {v['cc_rec']['n']}).
Before payment: the refund is dated before the last application on the credited invoice (T6). Past due: on the refund
date, an invoice of the customer dated by then, less the applications and credits dated by then, still open with its
DueDate before the refund date (T10). Method mismatch: no receipt applied to the credited invoice used the refund's
method.

Results. {v['cm_above']['n']} credits ({money(v['cm_above']['amt'])}) exceed their approver's limit, all approved by
customer service representatives with a limit of {v['above_limit']}; {v['rf_above']['n']} refunds
({money(v['rf_above']['amt'])}) exceed theirs, while the Accounting Manager's {v['within']['n']} are within limit (T1).
No document falls outside its person's employment (T2). The credit's approver applied cash to the credited invoice on
{v['cc']['n']} credits ({money(v['cc']['amt'])}; {v['cc_early']['n']} by the credit date) (T3); no refund approver
approved the credit, and every return was received in the warehouse by someone other than the credit's approver (T4).
{v['before']['n']} refunds ({money(v['before']['amt'])}) precede the customer's last payment, {v['nothing']['n']} of them
before any payment (T6); the cause is in T7: {v['unpaid_2060']} of the {v['to_2060']} credits posted to 2060 were
posted when nothing had been paid, so a refundable balance existed before the cash did. {v['pd2']['n']} refunds were
paid to customers whose past-due balance was at least the refund ({money(v['pd2']['amt'])}), and {v['mism']['n']} went
by a method none of the invoice's receipts used, an anomaly to follow up (T10). The clawbacks are complete and at the
accrual's rate; the {len(off)} amounts T8 lists are exact half-cent products that SQLite's ROUND, in binary floating
point, puts a cent lower, not errors. Every refunded credit has exactly one refund equal to its 2060 part (T9).

The preparer against the approver cannot be tested: neither CreditMemo nor CustomerRefund records a preparer, and on
their ledger rows GLEntry.CreatedByEmployeeID names the approver every time ({cm_rows:,} and {rf_rows:,} rows, T5), as
it names the chief executive on every sales invoice row and the CFO on every supplier payment: it records the posting
convention, not who keyed the document, so it is no evidence of self-approval either way. T12 adds the design point:
the Accounting Manager approved all {design['rates']} commission rates, created all {design['accruals']:,} accruals,
approved all {design['payments']} commission payments and {by_am:,} of {registers:,} payroll registers, and
{v['within']['n']} refunds, including the largest.""")


# --- Requirement 6 -----------------------------------------------------------------------------------------------

def r6(b):
    d, n = b.data, notes(b)
    sm = n.sampling(d)
    s = script(b)
    key_dev, rest_dev = sm["key_dev"], len(sm["dev"])
    sample_cte = f"""\
WITH CustomerTotals AS (
    SELECT CustomerID, SUM(Amount) AS CustomerRefunds
    FROM CustomerRefund
    GROUP BY CustomerID
),
LastPayment AS (
    SELECT SalesInvoiceID, MAX(ApplicationDate) AS LastPaymentDate
    FROM CashReceiptApplication
    GROUP BY SalesInvoiceID
),
Refunds AS (
    SELECT rf.RefundNumber, rf.RefundDate, rf.CustomerID, rf.Amount,
        ct.CustomerRefunds,
        CASE WHEN rf.Amount >= {n.KEY_AMOUNT}
                OR ct.CustomerRefunds > {n.KEY_CUSTOMER}
            THEN 'Key item' ELSE 'Remainder' END AS Stratum,
        CASE WHEN lp.LastPaymentDate > rf.RefundDate
            THEN 1 ELSE 0 END AS BeforePayment
    FROM CustomerRefund AS rf
        INNER JOIN CustomerTotals AS ct ON ct.CustomerID = rf.CustomerID
        INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
        LEFT JOIN LastPayment AS lp
            ON lp.SalesInvoiceID = cm.OriginalSalesInvoiceID
)"""
    s.query("Requirement 6, test K1: the sampling population: key items and the remainder, with the data attribute",
            f"Population: every refund; key items {n.KEY_AMOUNT:,} or more, or a customer over {n.KEY_CUSTOMER:,}; "
            f"expected: a few",
            f"""\
{sample_cte}
SELECT Stratum, COUNT(*) AS Refunds, ROUND(SUM(Amount), 2) AS Amount,
    SUM(BeforePayment) AS BeforePayment
FROM Refunds
GROUP BY Stratum
ORDER BY Stratum;""",
            [Check("key items", len(sm["key"]), lambda r: r.where(Stratum="Key item")["Refunds"]),
             Check("key items, amount", sm["key_total"], lambda r: r.where(Stratum="Key item")["Amount"]),
             Check("key items before payment", key_dev, lambda r: r.where(Stratum="Key item")["BeforePayment"]),
             Check("remainder", len(sm["rest"]), lambda r: r.where(Stratum="Remainder")["Refunds"]),
             Check("remainder, amount", sm["rest_total"], lambda r: r.where(Stratum="Remainder")["Amount"]),
             Check("remainder before payment", rest_dev, lambda r: r.where(Stratum="Remainder")["BeforePayment"])])
    s.query("Requirement 6, test K2: the key items, taken in full",
            "Population: the key items of K1; expected: each listed with why it is key",
            f"""\
{sample_cte}
SELECT RefundNumber, RefundDate, CustomerID, ROUND(Amount, 2) AS Amount,
    ROUND(CustomerRefunds, 2) AS CustomerRefunds,
    CASE WHEN Amount >= {n.KEY_AMOUNT} THEN 'Amount'
        ELSE 'Customer' END AS KeyBecause,
    BeforePayment
FROM Refunds
WHERE Stratum = 'Key item'
ORDER BY RefundNumber;""",
            [Check("the key items", [r["num"] for r in sm["key"]], lambda r: r.col("RefundNumber")),
             Check("their amount", sm["key_total"], lambda r: r.total("Amount"))])


# --- Requirement 7 -----------------------------------------------------------------------------------------------

def r7(b):
    d, n = b.data, notes(b)
    v = context(b, "r7")
    c = n.cycle(d)
    sub, lap = v["sub"], v["lap"]
    s = script(b)
    s.query("Requirement 7, test S1: each credit line recomputed from its return, shipment, and invoice lines",
            "Population: every credit line; expected: every line traced, no quantity, price, or total off",
            """\
WITH Lines AS (
    SELECT cml.CreditMemoLineID, cml.Quantity, cml.UnitPrice,
        cml.Discount, cml.LineTotal, sl.QuantityShipped,
        sil.UnitPrice AS InvoicePrice, sil.Discount AS InvoiceDiscount,
        sil.SalesInvoiceID, cm.OriginalSalesInvoiceID
    FROM CreditMemoLine AS cml
        INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = cml.CreditMemoID
        INNER JOIN SalesReturnLine AS srl
            ON srl.SalesReturnLineID = cml.SalesReturnLineID
        INNER JOIN ShipmentLine AS sl
            ON sl.ShipmentLineID = srl.ShipmentLineID
        LEFT JOIN SalesInvoiceLine AS sil
            ON sil.ShipmentLineID = sl.ShipmentLineID
)
SELECT COUNT(*) AS CreditLines,
    SUM(CASE WHEN SalesInvoiceID = OriginalSalesInvoiceID
        THEN 1 ELSE 0 END) AS TracedToTheInvoice,
    SUM(CASE WHEN Quantity > QuantityShipped THEN 1 ELSE 0 END)
        AS AboveShipped,
    (SELECT COUNT(*)
     FROM (SELECT ShipmentLineID
           FROM SalesReturnLine
           GROUP BY ShipmentLineID
           HAVING COUNT(*) > 1)) AS ShipmentLinesReturnedTwice,
    SUM(CASE WHEN InvoicePrice IS NULL
        OR ABS(UnitPrice - InvoicePrice) > 0.004
        OR Discount <> InvoiceDiscount THEN 1 ELSE 0 END)
        AS PriceOrDiscountOff,
    SUM(CASE WHEN ABS(LineTotal
        - ROUND(Quantity * UnitPrice * (1 - Discount), 2)) > 0.004
        THEN 1 ELSE 0 END) AS LineTotalOff,
    GROUP_CONCAT(CASE WHEN ABS(LineTotal
        - ROUND(Quantity * UnitPrice * (1 - Discount), 2)) > 0.004
        THEN CreditMemoLineID END) AS LinesOff
FROM Lines;""",
            [Check("credit lines", sub["lines"], lambda r: r.value("CreditLines")),
             Check("traced", sub["traced"], lambda r: r.value("TracedToTheInvoice")),
             Check("above shipped", sub["over"], lambda r: r.value("AboveShipped")),
             Check("returned twice", sub["twice"], lambda r: r.value("ShipmentLinesReturnedTwice")),
             Check("price or discount off", sub["price_off"], lambda r: r.value("PriceOrDiscountOff")),
             Check("line totals off (half-cent roundings)", len(v["half"]) + len(sub["total_off"]),
                   lambda r: r.value("LineTotalOff")),
             Check("the lines", ",".join(str(x) for x in v["half"]), lambda r: str(r.value("LinesOff")))])
    tax_sub = len(sub["tax_sub_flags"])
    s.query("Requirement 7, test S2: each credit recomputed: its invoice, lines, tax, freight, and total",
            "Population: every credit memo; expected: none above its invoice, tax on SubTotal plus freight",
            """\
WITH Rate AS (
    SELECT ROUND(SUM(TaxAmount) / SUM(SubTotal + FreightCreditAmount), 3)
        AS TaxRate
    FROM CreditMemo
),
Credits AS (
    SELECT cm.CreditMemoID, cm.OriginalSalesInvoiceID, cm.SubTotal,
        cm.FreightCreditAmount, cm.TaxAmount, cm.GrandTotal,
        si.GrandTotal AS InvoiceTotal, si.FreightAmount AS InvoiceFreight,
        (SELECT SUM(cml.LineTotal)
         FROM CreditMemoLine AS cml
         WHERE cml.CreditMemoID = cm.CreditMemoID) AS LinesTotal
    FROM CreditMemo AS cm
        INNER JOIN SalesInvoice AS si
            ON si.SalesInvoiceID = cm.OriginalSalesInvoiceID
)
SELECT COUNT(*) AS Credits,
    COUNT(DISTINCT OriginalSalesInvoiceID) AS Invoices,
    (SELECT TaxRate FROM Rate) AS TaxRate,
    SUM(CASE WHEN GrandTotal > InvoiceTotal + 0.005 THEN 1 ELSE 0 END)
        AS AboveInvoice,
    SUM(CASE WHEN ABS(SubTotal - LinesTotal) > 0.004 THEN 1 ELSE 0 END)
        AS SubTotalNotLines,
    SUM(CASE WHEN ABS(TaxAmount - ROUND((SubTotal + FreightCreditAmount)
        * (SELECT TaxRate FROM Rate), 2)) > 0.005 THEN 1 ELSE 0 END)
        AS TaxOff,
    SUM(CASE WHEN ABS(TaxAmount - ROUND(SubTotal
        * (SELECT TaxRate FROM Rate), 2)) > 0.011 THEN 1 ELSE 0 END)
        AS TaxOffOnSubTotalAlone,
    SUM(CASE WHEN FreightCreditAmount > 0.005 THEN 1 ELSE 0 END)
        AS WithFreight,
    SUM(CASE WHEN FreightCreditAmount > InvoiceFreight + 0.005
        THEN 1 ELSE 0 END) AS FreightAboveInvoice,
    SUM(CASE WHEN ABS(GrandTotal - SubTotal - FreightCreditAmount
        - TaxAmount) > 0.004 THEN 1 ELSE 0 END) AS TotalNotParts
FROM Credits;""",
            [Check("credits", v["n_cm"], lambda r: r.value("Credits")),
             Check("distinct invoices", sub["distinct_inv"], lambda r: r.value("Invoices")),
             Check("tax rate", sub["rate"], lambda r: r.value("TaxRate")),
             Check("above the invoice", sub["above_invoice"], lambda r: r.value("AboveInvoice")),
             Check("SubTotal not the lines", v["n_cm"] - sub["sub_ok"], lambda r: r.value("SubTotalNotLines")),
             Check("tax off", v["n_cm"] - sub["tax_ok"], lambda r: r.value("TaxOff")),
             Check("a test on SubTotal alone flags the credits with freight", tax_sub,
                   lambda r: r.value("TaxOffOnSubTotalAlone")),
             Check("credits with freight", v["with_freight"], lambda r: r.value("WithFreight")),
             Check("freight above the invoice's", sub["freight_over"], lambda r: r.value("FreightAboveInvoice")),
             Check("totals not their parts", 0, lambda r: r.value("TotalNotParts"))])
    items = n.open_2060(d, d.C)
    s.query(f"Requirement 7, test S3: the open items in 2060 at {d.C}-12-31",
            "Population: credits posted to 2060 by the year-end and not refunded by it; expected: G7's last items",
            f"""\
WITH Posted AS (
    SELECT gl.SourceDocumentID AS CreditMemoID, SUM(gl.Credit) AS To2060
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber = 2060 AND gl.SourceDocumentType = 'CreditMemo'
        AND gl.PostingDate <= '{d.C}-12-31'
    GROUP BY gl.SourceDocumentID
),
Refunded AS (
    SELECT CreditMemoID, SUM(Amount) AS Refunded
    FROM CustomerRefund
    WHERE RefundDate <= '{d.C}-12-31'
    GROUP BY CreditMemoID
)
SELECT cm.CreditMemoNumber, cm.CreditMemoDate, cm.Status, cm.CustomerID,
    si.InvoiceNumber, ROUND(p.To2060 - COALESCE(rd.Refunded, 0), 2)
        AS OpenIn2060,
    julianday('{d.C}-12-31') - julianday(cm.CreditMemoDate) AS DaysOpen
FROM Posted AS p
    INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = p.CreditMemoID
    INNER JOIN SalesInvoice AS si
        ON si.SalesInvoiceID = cm.OriginalSalesInvoiceID
    LEFT JOIN Refunded AS rd ON rd.CreditMemoID = p.CreditMemoID
WHERE p.To2060 - COALESCE(rd.Refunded, 0) > 0.005
ORDER BY cm.CreditMemoNumber;""",
            [Check("open items", [x["number"] for x in items], lambda r: r.col("CreditMemoNumber")),
             Check("their amounts", [x["amount"] for x in items], lambda r: r.col("OpenIn2060")),
             Check("their status", [x["status"] for x in items], lambda r: r.col("Status")),
             Check("the balance of 2060", round(n.balance_2060(d, d.C), 2), lambda r: r.total("OpenIn2060"))])
    yrs = d.years
    year_cols = ",\n".join(f"    ROUND(SUM(CASE WHEN strftime('%Y', sr.ReturnDate) = '{y}'\n"
                           f"        THEN srl.ExtendedStandardCost ELSE 0 END), 2) AS Restocked{y}" for y in yrs)
    s.query("Requirement 7, test S4: what returned goods were put back into inventory at, by reason",
            "Population: every return line; expected: standard cost, with no write-down for damaged goods",
            f"""\
SELECT sr.ReasonCode, COUNT(*) AS ReturnLines,
{year_cols},
    ROUND(SUM(srl.ExtendedStandardCost), 2) AS Restocked,
    ROUND(SUM(ROUND(srl.QuantityReturned * i.StandardCost, 2)), 2)
        AS AtStandardCost,
    SUM(CASE WHEN ABS(srl.ExtendedStandardCost
        - ROUND(srl.QuantityReturned * i.StandardCost, 2)) > 0.011
        THEN 1 ELSE 0 END) AS LinesOffStandard,
    ROUND(SUM(CASE WHEN ABS(srl.ExtendedStandardCost
        - ROUND(srl.QuantityReturned * i.StandardCost, 2)) > 0.011
        THEN ROUND(srl.QuantityReturned * i.StandardCost, 2)
            - srl.ExtendedStandardCost ELSE 0 END), 2) AS BelowStandard
FROM SalesReturnLine AS srl
    INNER JOIN SalesReturn AS sr ON sr.SalesReturnID = srl.SalesReturnID
    INNER JOIN Item AS i ON i.ItemID = srl.ItemID
GROUP BY sr.ReasonCode
ORDER BY Restocked DESC;""",
            [Check("Damaged by year", [round(x, 2) for x in v["dmg"]],
                   lambda r: [r.where(ReasonCode="Damaged")[f"Restocked{y}"] for y in yrs]),
             Check("Damaged", v["dmg_total"], lambda r: r.where(ReasonCode="Damaged")["Restocked"]),
             Check("Damaged and Quality Concern", v["both"],
                   lambda r: round(r.where(ReasonCode="Damaged")["Restocked"]
                                   + r.where(ReasonCode="Quality Concern")["Restocked"], 2)),
             Check(f"Damaged and Quality Concern in {d.C}", v["both_c"],
                   lambda r: round(r.where(ReasonCode="Damaged")[f"Restocked{d.C}"]
                                   + r.where(ReasonCode="Quality Concern")[f"Restocked{d.C}"], 2)),
             Check("lines restocked off standard", v["n_frac"], lambda r: r.total("LinesOffStandard")),
             Check("below standard by", v["frac_gap"], lambda r: r.total("BelowStandard")),
             Check("of which Damaged and Quality Concern", v["frac_dq"],
                   lambda r: round(sum(r.where(ReasonCode=x)["BelowStandard"] for x in ("Damaged", "Quality Concern")),
                                   2)),
             Check("all returns restocked", round(context(b, "r1")["sr_dr"], 2), lambda r: r.total("Restocked"))])
    s.query("Requirement 7, test S5: lapping: receipts against invoices, deposits, and applications",
            "Population: every receipt and application; expected: own customer's invoices, short delays, fully applied",
            """\
WITH Applied AS (
    SELECT cra.CashReceiptApplicationID, cra.CashReceiptID,
        cra.AppliedAmount, cra.ApplicationDate, cr.ReceiptDate,
        cr.CustomerID AS ReceiptCustomer, si.CustomerID AS InvoiceCustomer,
        si.InvoiceDate
    FROM CashReceiptApplication AS cra
        INNER JOIN CashReceipt AS cr ON cr.CashReceiptID = cra.CashReceiptID
        INNER JOIN SalesInvoice AS si ON si.SalesInvoiceID = cra.SalesInvoiceID
),
AppliedByReceipt AS (
    SELECT CashReceiptID, SUM(AppliedAmount) AS Applied
    FROM CashReceiptApplication
    GROUP BY CashReceiptID
)
SELECT
    (SELECT SUM(CASE WHEN ReceiptCustomer <> InvoiceCustomer
        THEN 1 ELSE 0 END) FROM Applied) AS OtherCustomersInvoice,
    (SELECT MIN(julianday(DepositDate) - julianday(ReceiptDate))
     FROM CashReceipt) AS MinDepositDays,
    (SELECT MAX(julianday(DepositDate) - julianday(ReceiptDate))
     FROM CashReceipt) AS MaxDepositDays,
    (SELECT MIN(julianday(ApplicationDate) - julianday(
        CASE WHEN InvoiceDate > ReceiptDate THEN InvoiceDate
            ELSE ReceiptDate END)) FROM Applied) AS MinApplicationLag,
    (SELECT MAX(julianday(ApplicationDate) - julianday(
        CASE WHEN InvoiceDate > ReceiptDate THEN InvoiceDate
            ELSE ReceiptDate END)) FROM Applied) AS MaxApplicationLag,
    (SELECT COUNT(*)
     FROM CashReceipt AS cr
        LEFT JOIN AppliedByReceipt AS ab
            ON ab.CashReceiptID = cr.CashReceiptID
     WHERE ab.Applied IS NULL OR ABS(cr.Amount - ab.Applied) > 0.005)
        AS NotFullyApplied,
    (SELECT COUNT(DISTINCT CashReceiptID)
     FROM Applied
     WHERE ReceiptDate < InvoiceDate) AS ReceiptsBeforeInvoice,
    (SELECT COUNT(*)
     FROM Applied
     WHERE ReceiptDate < InvoiceDate) AS ApplicationsBeforeInvoice,
    (SELECT ROUND(SUM(AppliedAmount), 2)
     FROM Applied
     WHERE ReceiptDate < InvoiceDate) AS AmountBeforeInvoice;""",
            [Check("applications to another customer's invoice", lap["other"], lambda r: r.value("OtherCustomersInvoice")),
             Check("fewest days to deposit", lap["dep_lo"], lambda r: r.value("MinDepositDays")),
             Check("most days to deposit", lap["dep_hi"], lambda r: r.value("MaxDepositDays")),
             Check("fewest days to application", lap["lag_lo"], lambda r: r.value("MinApplicationLag")),
             Check("most days to application", lap["lag_hi"], lambda r: r.value("MaxApplicationLag")),
             Check("receipts not fully applied", lap["not_full"], lambda r: r.value("NotFullyApplied")),
             Check("receipts applied to later invoices", lap["early_receipts"], lambda r: r.value("ReceiptsBeforeInvoice")),
             Check("those applications", lap["early_apps"], lambda r: r.value("ApplicationsBeforeInvoice")),
             Check("those amounts", lap["early_amount"], lambda r: r.value("AmountBeforeInvoice"))])
    # S6: the timeline of the largest refund
    rf = n.largest_refund(d)
    m = c.cm[rf["cm"]]
    inv = c.inv[m["inv"]]
    sr = c.sr[m["ret"]]
    receipts = sorted({c.rcpt[a[3]]["num"] for a in c.apps[inv["id"]]})
    claws = sorted(a["num"] for a in c.adj if a["cm"] == m["id"])
    ships = [r[0] for r in d.q("SELECT DISTINCT s.ShipmentNumber FROM SalesInvoiceLine sil JOIN ShipmentLine sl ON "
                               "sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                               "WHERE sil.SalesInvoiceID = ? ORDER BY s.ShipmentDate", inv["id"])]
    unpaid = inv["gt"] - n.paid_by(c, inv["id"], m["date"])
    settled = n.last_payment(c, inv["id"])
    shipped = d.q("SELECT DISTINCT s.ShipmentDate, s.ShipmentNumber, s.ShippedBy, s.DeliveryDate FROM SalesInvoiceLine sil "
                  "JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = "
                  "sl.ShipmentID WHERE sil.SalesInvoiceID = ?", inv["id"])
    steps = ([(day, 1, "Shipment", num) for day, num, _, _ in shipped] + [(inv["date"], 2, "Sales invoice", inv["num"])]
             + [(c.rcpt[a[3]]["date"], 3, "Cash receipt", c.rcpt[a[3]]["num"]) for a in c.apps[inv["id"]]]
             + [(sr["date"], 4, "Sales return", sr["num"]), (m["date"], 5, "Credit memo", m["num"])]
             + [(a["date"], 6, "Commission clawback", a["num"]) for a in c.adj if a["cm"] == m["id"]]
             + [(rf["date"], 7, "Customer refund", rf["num"])])
    steps = [(day, step, num) for day, _, step, num in sorted(steps)]
    applied = sorted((c.rcpt[a[3]]["num"], f"{a[1]:.2f}", a[0]) for a in c.apps[inv["id"]])
    weekday = date.fromisoformat(rf["date"]).strftime("%A")
    who = lambda e: f"{c.emp[e]['title']} {e}"  # noqa: E731
    s.query("Requirement 7, test S6: the largest refund's timeline, from shipment to last receipt, with who acted",
            "Population: the refund's credit, return, invoice, shipments, receipts, and clawbacks; expected: no gaps",
            """\
WITH Refund AS (
    SELECT rf.CustomerRefundID, rf.RefundNumber, rf.RefundDate,
        rf.Amount, rf.PaymentMethod, rf.ApprovedByEmployeeID,
        rf.ClearedDate, cm.CreditMemoID, cm.CreditMemoNumber,
        cm.CreditMemoDate, cm.GrandTotal AS CreditTotal,
        cm.ApprovedByEmployeeID AS CreditApproverID, cm.SalesReturnID,
        cm.OriginalSalesInvoiceID AS SalesInvoiceID
    FROM CustomerRefund AS rf
        INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
    WHERE rf.Amount = (SELECT MAX(Amount) FROM CustomerRefund)
),
Steps AS (
    SELECT DISTINCT s.ShipmentDate AS StepDate, 1 AS StepOrder,
        'Shipment' AS Step, s.ShipmentNumber AS Document,
        'Shipped by ' || s.ShippedBy || '; delivered ' || s.DeliveryDate
            AS Detail,
        'Warehouse' AS Who
    FROM Refund AS r
        INNER JOIN SalesInvoiceLine AS sil
            ON sil.SalesInvoiceID = r.SalesInvoiceID
        INNER JOIN ShipmentLine AS sl
            ON sl.ShipmentLineID = sil.ShipmentLineID
        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
    UNION ALL
    SELECT si.InvoiceDate, 2, 'Sales invoice', si.InvoiceNumber,
        printf('%.2f', si.GrandTotal) || ', due ' || si.DueDate,
        'Customer ' || si.CustomerID
    FROM Refund AS r
        INNER JOIN SalesInvoice AS si ON si.SalesInvoiceID = r.SalesInvoiceID
    UNION ALL
    SELECT cr.ReceiptDate, 3, 'Cash receipt', cr.ReceiptNumber,
        cr.PaymentMethod || ', ' || printf('%.2f', cra.AppliedAmount)
            || ' applied on ' || cra.ApplicationDate,
        'Recorded by ' || er.JobTitle || ' ' || er.EmployeeID
            || '; applied by ' || ea.JobTitle || ' ' || ea.EmployeeID
    FROM Refund AS r
        INNER JOIN CashReceiptApplication AS cra
            ON cra.SalesInvoiceID = r.SalesInvoiceID
        INNER JOIN CashReceipt AS cr ON cr.CashReceiptID = cra.CashReceiptID
        INNER JOIN Employee AS er ON er.EmployeeID = cr.RecordedByEmployeeID
        INNER JOIN Employee AS ea ON ea.EmployeeID = cra.AppliedByEmployeeID
    UNION ALL
    SELECT sr.ReturnDate, 4, 'Sales return', sr.ReturnNumber,
        sr.ReasonCode,
        'Received by ' || e.JobTitle || ' ' || e.EmployeeID
    FROM Refund AS r
        INNER JOIN SalesReturn AS sr ON sr.SalesReturnID = r.SalesReturnID
        INNER JOIN Employee AS e ON e.EmployeeID = sr.ReceivedByEmployeeID
    UNION ALL
    SELECT r.CreditMemoDate, 5, 'Credit memo', r.CreditMemoNumber,
        printf('%.2f', r.CreditTotal) || '; to 2060 '
            || printf('%.2f', (SELECT COALESCE(SUM(gl.Credit), 0)
                FROM GLEntry AS gl
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                WHERE gl.SourceDocumentType = 'CreditMemo'
                    AND gl.SourceDocumentID = r.CreditMemoID
                    AND a.AccountNumber = 2060))
            || '; invoice unpaid '
            || printf('%.2f', (SELECT si.GrandTotal
                - COALESCE(SUM(cra.AppliedAmount), 0)
                FROM SalesInvoice AS si
                    LEFT JOIN CashReceiptApplication AS cra
                        ON cra.SalesInvoiceID = si.SalesInvoiceID
                        AND cra.ApplicationDate <= r.CreditMemoDate
                WHERE si.SalesInvoiceID = r.SalesInvoiceID)),
        'Approved by ' || e.JobTitle || ' ' || e.EmployeeID
            || ', limit ' || COALESCE(e.MaxApprovalAmount, 0)
    FROM Refund AS r
        INNER JOIN Employee AS e ON e.EmployeeID = r.CreditApproverID
    UNION ALL
    SELECT sca.AdjustmentDate, 6, 'Commission clawback',
        sca.AdjustmentNumber, printf('%.2f', sca.CommissionAdjustmentAmount),
        'Approved by ' || e.JobTitle || ' ' || e.EmployeeID
    FROM Refund AS r
        INNER JOIN SalesCommissionAdjustment AS sca
            ON sca.CreditMemoID = r.CreditMemoID
        INNER JOIN Employee AS e ON e.EmployeeID = sca.ApprovedByEmployeeID
    UNION ALL
    SELECT r.RefundDate, 7, 'Customer refund', r.RefundNumber,
        printf('%.2f', r.Amount) || ' by ' || r.PaymentMethod
            || ' on weekday ' || strftime('%w', r.RefundDate)
            || ' (0 = Sunday); cleared ' || r.ClearedDate,
        'Approved by ' || e.JobTitle || ' ' || e.EmployeeID
            || ', limit ' || COALESCE(e.MaxApprovalAmount, 0)
    FROM Refund AS r
        INNER JOIN Employee AS e ON e.EmployeeID = r.ApprovedByEmployeeID
)
SELECT StepDate, Step, Document, Detail, Who
FROM Steps
ORDER BY StepDate, StepOrder, Document;""",
            [Check("the largest refund", rf["num"],
                   lambda r: r.where(Step="Customer refund")["Document"]),
             Check("its date", rf["date"], lambda r: r.where(Step="Customer refund")["StepDate"]),
             Check("its amount and method", f"{rf['amt']:.2f} by {rf['method']}",
                   lambda r: r.where(Step="Customer refund")["Detail"].split(" on ")[0]),
             Check("its weekday", weekday == "Sunday",
                   lambda r: "weekday 0 " in r.where(Step="Customer refund")["Detail"]),
             Check("its approver", who(rf["appr"]),
                   lambda r: r.where(Step="Customer refund")["Who"].removeprefix("Approved by ").split(",")[0]),
             Check("the credit", m["num"], lambda r: r.where(Step="Credit memo")["Document"]),
             Check("the credit's approver", who(m["appr"]),
                   lambda r: r.where(Step="Credit memo")["Who"].removeprefix("Approved by ").split(",")[0]),
             Check("the credit all to 2060", f"{m['gt']:.2f}",
                   lambda r: r.where(Step="Credit memo")["Detail"].split("; to 2060 ")[1].split(";")[0]),
             Check("unpaid on the credit date", f"{unpaid:.2f}",
                   lambda r: r.where(Step="Credit memo")["Detail"].split("invoice unpaid ")[1]),
             Check("the invoice", inv["num"], lambda r: r.where(Step="Sales invoice")["Document"]),
             Check("the return", sr["num"], lambda r: r.where(Step="Sales return")["Document"]),
             Check("the return's reason", sr["reason"], lambda r: r.where(Step="Sales return")["Detail"]),
             Check("the shipments", ships, lambda r: [x["Document"] for x in dicts(r) if x["Step"] == "Shipment"]),
             Check("the receipts", receipts,
                   lambda r: sorted(x["Document"] for x in dicts(r) if x["Step"] == "Cash receipt")),
             Check("the clawbacks", claws,
                   lambda r: sorted(x["Document"] for x in dicts(r) if x["Step"] == "Commission clawback")),
             Check("the last payment after the refund", True,
                   lambda r: max(x["Detail"].split(" applied on ")[1] for x in dicts(r)
                                 if x["Step"] == "Cash receipt") == settled > rf["date"]),
             Check("first step", ships[0], lambda r: r.cell(0, "Document")),
             Check("the steps in date order", steps,
                   lambda r: [(x["StepDate"], x["Step"], x["Document"]) for x in dicts(r)]),
             Check("the shipments' carriers and delivery dates", [f"Shipped by {x[2]}; delivered {x[3]}" for x in
                                                                  sorted(shipped, key=lambda x: (x[0], x[1]))],
                   lambda r: [x["Detail"] for x in dicts(r) if x["Step"] == "Shipment"]),
             Check("the invoice's total and due date", f"{inv['gt']:.2f}, due {inv['due']}",
                   lambda r: r.where(Step="Sales invoice")["Detail"]),
             Check("the customer", f"Customer {inv['cust']}", lambda r: r.where(Step="Sales invoice")["Who"]),
             Check("the receipts' amounts applied and their dates", applied,
                   lambda r: sorted((x["Document"], x["Detail"].split(", ")[1].split(" applied")[0],
                                     x["Detail"].split(" applied on ")[1]) for x in dicts(r)
                                    if x["Step"] == "Cash receipt")),
             Check("the return's receiver", who(sr["recv"]),
                   lambda r: r.where(Step="Sales return")["Who"].removeprefix("Received by ")),
             Check("the refund's clearing date", rf["cleared"],
                   lambda r: r.where(Step="Customer refund")["Detail"].split("cleared ")[1])])
    s.answer("Requirement 7", f"""\
The balances test clean. Every one of the {sub['lines']} credit lines traces to its return, shipment, and invoice
lines, none returns more than was shipped and no shipment line was returned twice, and price and discount equal the
invoice line's (S1); LineTotal is ROUND(Q x P x (1 - D), 2) except a half-cent on line {', '.join(str(x) for x in
v['half'])}, an exact half-cent product. The {v['n_cm']} credits are on as many invoices, none above its invoice, with
SubTotal equal to the lines and tax at {sub['rate']:.1%} of SubTotal plus freight on all of them (S2); a test on SubTotal
alone would flag the {v['with_freight']} credits with freight. 2060 holds {len(items)} Issued credits at the year-end
(S3). Returned goods go back at standard cost, with no write-down for damaged goods: Damaged
{money(v['dmg_total'])}, Damaged and Quality Concern {money(v['both'])} ({money(v['both_c'])} in {d.C}), a valuation
follow-up (S4); {v['n_frac']} lines of less than one unit sit {money(v['frac_gap'])} below standard.

Lapping (S5): no receipt is applied to another customer's invoice, deposits follow receipts within {lap['dep_hi']}
days, every application falls within {lap['lag_hi']} days of the later of the receipt and invoice dates, and every
receipt is fully applied; the {lap['early_receipts']} receipts applied to invoices dated after them are deposits held
in 2060, not lapping. A first-digit test does not suit these populations, on Chapter 8's criteria: Benford's Law
describes large populations of amounts that combine many quantities, span several orders of magnitude, and have no
built-in maximum, while the {v['n_cm']} credits and {v['n_rf']} refunds are too few to judge conformity, their amounts
are prices set by people times the quantities returned, plus tax, and each credit is capped by its invoice.

Timeline (S6): {v['timeline']}. Disposition: follow up, not a conclusion. Evidence outside the database that would
settle it: {v['payee']}; a confirmation from the customer of the credit and the refund; the receiving and inspection
record and any carrier claim; the customer's written request; and {v['why']}.""")


# --- Requirement 10 ----------------------------------------------------------------------------------------------

def r10(b):
    d = b.data
    v = context(b, "r10")
    s = script(b)
    yrs = d.years
    checks = [Check("rows", len(TESTS) * len(yrs), len)]
    for x in v["tests"]:
        k = x["name"]
        checks += [Check(f"{k} by year", x["years"],
                         lambda r, k=k: [r.where(TestID=k, FiscalYear=y)["Exceptions"] for y in yrs]),
                   Check(f"{k} rates per 1,000", [round(z, 1) for z in x["rates"]],
                         lambda r, k=k: [r.where(TestID=k, FiscalYear=y)["RatePer1000"] for y in yrs], 0.051)]
    checks += [Check("credit populations", v["pop_c"],
                     lambda r: [r.where(TestID="CM AboveLimit", FiscalYear=y)["Population"] for y in yrs]),
               Check("refund populations", v["pop_r"],
                     lambda r: [r.where(TestID="RF AboveLimit", FiscalYear=y)["Population"] for y in yrs]),
               Check("rows the register adds", v["new"] - v["old"], lambda r: r.total("Exceptions"))]
    s.query("Requirement 10, test E1: the register's four new tests: exceptions, population, and rate per 1,000",
            "Population: test T11's exceptions, all credits and refunds; expected: rates the register can follow",
            """\
WITH LastPayment AS (
    SELECT SalesInvoiceID, MAX(ApplicationDate) AS LastPaymentDate
    FROM CashReceiptApplication
    GROUP BY SalesInvoiceID
),
Tests AS (
    SELECT 'CM AboveLimit' AS TestID,
        CAST(strftime('%Y', cm.CreditMemoDate) AS INTEGER) AS FiscalYear,
        CASE WHEN cm.GrandTotal > COALESCE(e.MaxApprovalAmount, 0)
            THEN 1 ELSE 0 END AS Exception
    FROM CreditMemo AS cm
        INNER JOIN Employee AS e ON e.EmployeeID = cm.ApprovedByEmployeeID
    UNION ALL
    SELECT 'CM CashAndCredit',
        CAST(strftime('%Y', cm.CreditMemoDate) AS INTEGER),
        CASE WHEN EXISTS (
                SELECT 1
                FROM CashReceiptApplication AS cra
                WHERE cra.SalesInvoiceID = cm.OriginalSalesInvoiceID
                    AND cra.AppliedByEmployeeID = cm.ApprovedByEmployeeID)
            THEN 1 ELSE 0 END
    FROM CreditMemo AS cm
    UNION ALL
    SELECT 'RF AboveLimit', CAST(strftime('%Y', rf.RefundDate) AS INTEGER),
        CASE WHEN rf.Amount > COALESCE(e.MaxApprovalAmount, 0)
            THEN 1 ELSE 0 END
    FROM CustomerRefund AS rf
        INNER JOIN Employee AS e ON e.EmployeeID = rf.ApprovedByEmployeeID
    UNION ALL
    SELECT 'RF BeforePayment',
        CAST(strftime('%Y', rf.RefundDate) AS INTEGER),
        CASE WHEN lp.LastPaymentDate > rf.RefundDate THEN 1 ELSE 0 END
    FROM CustomerRefund AS rf
        INNER JOIN CreditMemo AS cm ON cm.CreditMemoID = rf.CreditMemoID
        LEFT JOIN LastPayment AS lp
            ON lp.SalesInvoiceID = cm.OriginalSalesInvoiceID
)
SELECT TestID, FiscalYear, COUNT(*) AS Population,
    SUM(Exception) AS Exceptions,
    ROUND(SUM(Exception) * 1000.0 / COUNT(*), 1) AS RatePer1000
FROM Tests
GROUP BY TestID, FiscalYear
ORDER BY TestID, FiscalYear;""", checks)


# --- Milestones ----------------------------------------------------------------------------------------------------

def m1(b):
    v = context(b, "m1")
    script(b)
    recall(b, "credits").checks.append(Check("Milestone 1: credit SubTotal equals 4060 in every year",
                                             [round(x, 2) for x in v["subtotals"]], lambda r: r.col("Dr4060")))
    recall(b, "2060").checks.append(Check("Milestone 1: 2060 at the year-ends", [round(x, 2) for x in v["b2060"]],
                                          lambda r: r.col("Closing")))


def m2(b):
    v = context(b, "m2")
    script(b)
    q = recall(b, "exceptions")
    q.checks += [Check("Milestone 2: credits above the approver's limit", v["cm_above"],
                       lambda r: sum(1 for x in r.col("TestID") if x == "CM AboveLimit")),
                 Check("Milestone 2: credit approver applied the invoice's cash", v["cash_credit"],
                       lambda r: sum(1 for x in r.col("TestID") if x == "CM CashAndCredit")),
                 Check("Milestone 2: refunds above the limit", v["rf_above"],
                       lambda r: sum(1 for x in r.col("TestID") if x == "RF AboveLimit")),
                 Check("Milestone 2: refunds before the customer's payment", v["before"],
                       lambda r: sum(1 for x in r.col("TestID") if x == "RF BeforePayment"))]


def m3(b):
    v = context(b, "m3")
    script(b)
    recall(b, "exceptions").checks.append(Check("Milestone 3: register additions by test", v["additions"],
                                                lambda r: [sum(1 for x in r.col("TestID") if x == k) for k in TESTS]))


EXERCISES = [("Requirement 1", r1), ("Requirement 2", r2), ("Requirement 3", r3), ("Requirement 4", r4),
             ("Requirement 6", r6), ("Requirement 7", r7), ("Requirement 10", r10), ("Milestone 1", m1),
             ("Milestone 2", m2), ("Milestone 3", m3)]
