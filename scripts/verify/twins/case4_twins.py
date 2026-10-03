"""Read-only SQL twins for the Part IV comprehensive case ("Finding the Cash Behind the Profit").
Every value the case's instructor notes state is computed here."""
import sqlite3
from datetime import date, timedelta

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, db_uri  # noqa: E402
c = sqlite3.connect(db_uri(), uri=True)
q = lambda s, p=(): c.execute(s, p).fetchall()
one = lambda s, p=(): c.execute(s, p).fetchone()

CLOSES = [r[0] for r in q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%'")]
CL = "(" + ",".join(f"'{v}'" for v in CLOSES) + ")"
NOCLOSE = f"NOT (g.SourceDocumentType='JournalEntry' AND g.VoucherNumber IN {CL})"
OPEN = "JE-2024-000001"
YEARS = [2024, 2025, 2026]
YE = {y: f"{y}-12-31" for y in YEARS}


def hdr(t):
    print(f"\n=== {t}")


def bal(where, asof, extra=""):
    """Debit-positive balance of accounts matching `where`, postings dated on or before asof; the closes are
    excluded only when posted on the as-of date (the Balance measure of Exercise 14.1)."""
    return one(f"""SELECT ROUND(COALESCE(SUM(g.Debit-g.Credit),0),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
        WHERE {where} AND g.PostingDate<=? AND NOT (g.SourceDocumentType='JournalEntry' AND g.VoucherNumber IN {CL}
        AND g.PostingDate=?) {extra}""", (asof, asof))[0]


def flow(where, d0, d1, sign="Debit-Credit", src=None):
    s = f" AND g.SourceDocumentType='{src}'" if src else ""
    return one(f"""SELECT ROUND(COALESCE(SUM(g.{sign.split('-')[0]}-g.{sign.split('-')[1]}),0),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
        WHERE {where} AND g.PostingDate BETWEEN ? AND ? AND {NOCLOSE}{s}""", (d0, d1))[0]


# ---- Requirement 1 ------------------------------------------------------------------------
hdr("R1 ledger and validation")
print("GL rows", one("SELECT COUNT(*) FROM GLEntry")[0], "| closes", CLOSES,
      "| close rows", one(f"SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType='JournalEntry' AND VoucherNumber IN {CL}")[0])
for y in YEARS:
    ni = one(f"""SELECT ROUND(SUM(g.Credit-g.Debit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
        WHERE a.AccountType IN ('Revenue','Expense') AND g.FiscalYear=? AND {NOCLOSE}""", (y,))[0]
    ta = bal("a.AccountType='Asset'", YE[y])
    rec = flow("a.AccountNumber='1045'", f"{y}-01-01", YE[y], src="GoodsReceipt")
    iss = flow("a.AccountNumber='1045'", f"{y}-01-01", YE[y], "Credit-Debit", src="MaterialIssue")
    # source tables
    rec_t = one("""SELECT ROUND(SUM(l.ExtendedStandardCost),2) FROM GoodsReceiptLine l JOIN GoodsReceipt r ON r.GoodsReceiptID=l.GoodsReceiptID
        JOIN Item i ON i.ItemID=l.ItemID WHERE i.ItemGroup IN ('Raw Materials','Packaging') AND substr(r.ReceiptDate,1,4)=?""", (str(y),))[0]
    iss_t = one("""SELECT ROUND(SUM(l.ExtendedStandardCost),2) FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID=l.MaterialIssueID
        WHERE substr(m.IssueDate,1,4)=?""", (str(y),))[0]
    print(y, "NI", ni, "| total assets", ta, "| 1045 receipts GL", rec, "tables", rec_t, "| issues GL", iss, "tables", iss_t)
print("receipt groups to 1045:", q("""SELECT i.ItemGroup, COUNT(*) FROM GoodsReceiptLine l JOIN Item i ON i.ItemID=l.ItemID GROUP BY 1"""))
print("issue groups:", q("""SELECT i.ItemGroup, COUNT(*) FROM MaterialIssueLine l JOIN Item i ON i.ItemID=l.ItemID GROUP BY 1"""))
print("last GL posting by source:", q("SELECT SourceDocumentType, MAX(PostingDate) FROM GLEntry GROUP BY 1 ORDER BY 2"))
print("after 2026:", one("SELECT COUNT(*), ROUND(SUM(Debit),2) FROM GLEntry WHERE PostingDate>'2026-12-31'"),
      q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE PostingDate>'2026-12-31' GROUP BY 1"),
      "payments", one("SELECT COUNT(*), ROUND(SUM(Amount),2) FROM DisbursementPayment WHERE PaymentDate>'2026-12-31'"))
print("balances at 2027-02-23: cash", bal("a.AccountNumber='1010'", "2027-02-23"), "AP", bal("a.AccountNumber='2010'", "2027-02-23"))

CH = """CASE WHEN r.Justification LIKE 'WO-COMPONENT-SHORTFALL%' THEN 'Shortfall'
             WHEN r.Justification LIKE 'Supply plan%' THEN 'Supply plan' ELSE 'Other' END"""
print("requisitions", one("SELECT COUNT(*) FROM PurchaseRequisition")[0], q(f"SELECT {CH}, COUNT(*) FROM PurchaseRequisition r GROUP BY 1"))
print("other justifications", q("SELECT Justification, ItemID, Status FROM PurchaseRequisition r WHERE " + CH.replace("CASE WHEN", "NOT (") .split(" THEN")[0] + ") AND Justification NOT LIKE 'Supply plan%'"))
print("blank approver", one("SELECT COUNT(*) FROM PurchaseRequisition WHERE ApprovedByEmployeeID IS NULL")[0],
      "| statuses", q(f"SELECT {CH}, Status, COUNT(*), MIN(RequestDate), MAX(RequestDate) FROM PurchaseRequisition r GROUP BY 1,2"))
print("supply-plan with recommendation", q(f"SELECT {CH}, SUM(SupplyPlanRecommendationID IS NOT NULL), COUNT(*) FROM PurchaseRequisition r GROUP BY 1"))
print("receipt lines", one("SELECT COUNT(*) FROM GoodsReceiptLine")[0],
      "| without PO line", one("SELECT COUNT(*) FROM GoodsReceiptLine l LEFT JOIN PurchaseOrderLine p ON p.POLineID=l.POLineID WHERE p.POLineID IS NULL")[0],
      "| PO lines without requisition", one("SELECT COUNT(*) FROM PurchaseOrderLine WHERE RequisitionID IS NULL")[0],
      "| PO lines", one("SELECT COUNT(*) FROM PurchaseOrderLine")[0],
      "| distinct requisitions on PO lines", one("SELECT COUNT(DISTINCT RequisitionID) FROM PurchaseOrderLine")[0],
      "| PO headers with blank RequisitionID", one("SELECT COUNT(*) FROM PurchaseOrder WHERE RequisitionID IS NULL")[0] if 'RequisitionID' in [r[1] for r in q("PRAGMA table_info(PurchaseOrder)")] else "n/a")
print("issue lines", one("SELECT COUNT(*) FROM MaterialIssueLine")[0], "| issues", one("SELECT COUNT(*) FROM MaterialIssue")[0],
      "| issues with lines", one("SELECT COUNT(DISTINCT MaterialIssueID) FROM MaterialIssueLine")[0],
      "| issues without WO", one("SELECT COUNT(*) FROM MaterialIssue m LEFT JOIN WorkOrder w ON w.WorkOrderID=m.WorkOrderID WHERE w.WorkOrderID IS NULL")[0])

# ---- Requirement 2 ------------------------------------------------------------------------
hdr("R2 balance sheet, bridge, restated sections")
for y in YEARS:
    ca = bal("a.AccountSubType IN ('Current Asset','Contra Current Asset')", YE[y])
    cl = -bal("a.AccountSubType='Current Liability'", YE[y])
    cash = bal("a.AccountNumber='1010'", YE[y]); ar = bal("a.AccountNumber='1020'", YE[y])
    inv = bal("a.AccountNumber IN ('1040','1045','1046')", YE[y])
    print(y, "CA", ca, "CL", cl, "WC", round(ca - cl, 2), "current", round(ca / cl, 2), "quick", round((cash + ar) / cl, 2),
          "inventories share of CA", round(inv / ca, 3))

STEP = """CASE
  WHEN a.AccountNumber='1010' THEN 'Cash'
  WHEN a.AccountType IN ('Revenue','Expense') THEN '1 Net income'
  WHEN a.AccountSubType='Contra Fixed Asset' THEN '2 Depreciation'
  WHEN a.AccountNumber IN ('1020','1030') THEN '3 Receivables'
  WHEN a.AccountNumber IN ('1040','1045','1046') THEN '4 Inventories'
  WHEN a.AccountSubType IN ('Current Asset','Contra Current Asset') THEN '5 Other current assets'
  WHEN a.AccountNumber IN ('2010','2020') THEN '6 Payables'
  WHEN a.AccountNumber='2050' THEN '7 Sales tax'
  WHEN a.AccountSubType='Current Liability' THEN '8 Other current liabilities'
  WHEN a.AccountSubType IN ('Fixed Asset','Noncurrent Asset') THEN '9 Fixed assets'
  ELSE '10 Debt and equity' END"""
for y in YEARS:
    for label, extra in (("", ""), (" without opening entry", f" AND g.VoucherNumber<>'{OPEN}'")):
        rows = q(f"""SELECT {STEP} s, ROUND(SUM(g.Credit-g.Debit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
            WHERE g.FiscalYear=? AND {NOCLOSE} {extra} GROUP BY 1""", (y,))
        d = dict(rows); cash_eff = -d.pop("Cash", 0)
        steps = sorted(d.items(), key=lambda kv: int(kv[0].split()[0]))
        print(y, label, [(k, v) for k, v in steps], "sum", round(sum(d.values()), 2), "change in cash", round(cash_eff, 2))
print("cash by year-end:", [bal("a.AccountNumber='1010'", d) for d in ("2024-01-01", *YE.values())],
      "| opening entry cash line", one(f"SELECT g.Debit FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID WHERE g.VoucherNumber='{OPEN}' AND a.AccountNumber='1010'")[0],
      "| opening entry lines", one(f"SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber='{OPEN}'")[0])
# Noncash and investing entries
for y in YEARS:
    print(y, "entries to fixed / noncurrent / notes:", q(f"""SELECT g.VoucherNumber, g.SourceDocumentType, a.AccountNumber, g.Debit, g.Credit, g.PostingDate
        FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID WHERE g.FiscalYear=? AND {NOCLOSE}
        AND (a.AccountSubType IN ('Fixed Asset','Noncurrent Asset') OR (a.AccountNumber='2110' AND g.SourceDocumentType<>'JournalEntry')
        OR (a.AccountNumber='2110' AND g.VoucherNumber NOT LIKE 'JE-%-0000__' AND 0)) ORDER BY g.PostingDate""", (y,))[:20])
for y in YEARS:
    dep = flow("a.AccountSubType='Contra Fixed Asset'", f"{y}-01-01", YE[y], "Credit-Debit")
    dep_je = one(f"""SELECT ROUND(SUM(g.Credit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID JOIN JournalEntry j ON j.EntryNumber=g.VoucherNumber
        WHERE a.AccountSubType='Contra Fixed Asset' AND g.FiscalYear=? AND j.EntryType='Depreciation'""", (y,))[0]
    disposals = q(f"""SELECT j.EntryNumber, j.EntryType, a.AccountNumber, g.Debit, g.Credit FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
        JOIN JournalEntry j ON j.EntryNumber=g.VoucherNumber WHERE g.FiscalYear=? AND j.EntryType NOT IN ('Depreciation') AND j.EntryType NOT LIKE 'Year-End%'
        AND a.AccountSubType IN ('Fixed Asset','Contra Fixed Asset','Noncurrent Asset','Long-Term Liability')""", (y,))
    principal = q("""SELECT COUNT(*), ROUND(SUM(PrincipalAmount),2), ROUND(SUM(InterestAmount),2) FROM DebtScheduleLine WHERE substr(PaymentDate,1,4)=? AND Status<>'Scheduled'""", (str(y),))
    print(y, "contra step", dep, "| depreciation entries", dep_je, "| entries to fixed/LT accounts", disposals, "| principal paid", principal)
print("debt schedule statuses", q("SELECT Status, COUNT(*), MIN(PaymentDate), MAX(PaymentDate) FROM DebtScheduleLine GROUP BY 1"))
print("notes outstanding at 2026-12-31 (schedule)", q("""SELECT DebtAgreementID, MIN(EndingPrincipal) FROM DebtScheduleLine WHERE PaymentDate<='2026-12-31' GROUP BY 1"""),
      "| GL 2110", bal("a.AccountNumber='2110'", "2026-12-31"),
      "| principal due in 2027", one("SELECT ROUND(SUM(PrincipalAmount),2), COUNT(*) FROM DebtScheduleLine WHERE PaymentDate BETWEEN '2027-01-01' AND '2027-12-31'"))
print("2025 cash capex invoices:", q("""SELECT pi.PurchaseInvoiceID, pi.InvoiceNumber, pi.GrandTotal FROM PurchaseInvoice pi JOIN PurchaseInvoiceLine l ON l.PurchaseInvoiceID=pi.PurchaseInvoiceID
    JOIN Item i ON i.ItemID=l.ItemID WHERE i.ItemGroup='Capex' ORDER BY pi.ReceivedDate""") if 'ItemID' in [r[1] for r in q("PRAGMA table_info(PurchaseInvoiceLine)")] else "n/a")
tax = [(y, flow("a.AccountNumber='2050'", f"{y}-01-01", YE[y], "Credit-Debit", src="SalesInvoice"),
        one("SELECT ROUND(SUM(TaxAmount),2) FROM SalesInvoice si JOIN GLEntry g ON g.SourceDocumentType='SalesInvoice' AND g.SourceDocumentID=si.SalesInvoiceID JOIN Account a ON a.AccountID=g.AccountID WHERE a.AccountNumber='2050' AND g.FiscalYear=?", (y,))[0]) for y in YEARS]
print("sales tax credits by year (GL, invoices' TaxAmount):", tax)
print("2050 by source:", q("SELECT g.SourceDocumentType, ROUND(SUM(g.Debit),2), ROUND(SUM(g.Credit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID WHERE a.AccountNumber='2050' GROUP BY 1"))
print("cash net of sales tax 2026-12-31:", round(bal("a.AccountNumber='1010'", YE[2026]) + bal("a.AccountNumber='2050'", YE[2026]), 2))

# ---- Requirement 3 ------------------------------------------------------------------------
hdr("R3 working-capital measures at quarter-ends (balance at QE over trailing 12 months x 365)")


def ttm(qe):
    d1 = date.fromisoformat(qe)
    d0 = date(d1.year - 1, d1.month, d1.day) + timedelta(days=1) if not (d1.month == 2 and d1.day == 29) else date(d1.year - 1, 3, 1)
    return d0.isoformat(), qe


QES = ["2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30", "2026-09-30", "2026-12-31"]
EXOPEN = f" AND g.VoucherNumber<>'{OPEN}'"
for qe in QES:
    d0, d1 = ttm(qe)
    ar = bal("a.AccountNumber='1020'", qe); ar_x = bal("a.AccountNumber='1020'", qe, EXOPEN)
    bill = flow("a.AccountNumber='1020'", d0, d1, "Debit-Credit", src="SalesInvoice")
    inv = bal("a.AccountNumber IN ('1040','1045','1046')", qe)
    cogs = flow("a.AccountSubType='COGS'", d0, d1)
    mat = bal("a.AccountNumber='1045'", qe); issues = flow("a.AccountNumber='1045'", d0, d1, "Credit-Debit", src="MaterialIssue")
    fg = bal("a.AccountNumber='1040'", qe); ships = flow("a.AccountNumber='1040'", d0, d1, "Credit-Debit", src="Shipment")
    ap = -bal("a.AccountNumber='2010'", qe); ap_x = -bal("a.AccountNumber='2010'", qe, EXOPEN)
    pinv = flow("a.AccountNumber='2010'", d0, d1, "Credit-Debit", src="PurchaseInvoice")
    dso, dio, dpo = ar / bill * 365, inv / cogs * 365, ap / pinv * 365
    print(qe, f"DSO {dso:.1f} ({ar_x / bill * 365:.1f}) DIO {dio:.1f} mat {mat / issues * 365:.1f} FG {fg / ships * 365:.1f} "
          f"DPO {dpo:.1f} ({ap_x / pinv * 365:.1f}) CCC {dso + dio - dpo:.1f} ({ar_x / bill * 365 + dio - ap_x / pinv * 365:.1f}) "
          f"| AR {ar} bill {bill} inv {inv} cogs {cogs} mat {mat} issues {issues} FG {fg} ships {ships} AP {ap} pinv {pinv}")
print("COGS subtype accounts:", q("SELECT AccountNumber, AccountName FROM Account WHERE AccountSubType='COGS'"))
print("COGS in 2026 window with and without closes:", flow("a.AccountSubType='COGS'", "2026-01-01", "2026-12-31"),
      one(f"SELECT ROUND(SUM(g.Debit-g.Credit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID WHERE a.AccountSubType='COGS' AND g.FiscalYear=2026")[0])
hdr("R3 average-balance versions by year")
for y in YEARS:
    beg = (lambda w: bal(w, f"{y - 1}-12-31") if y > 2024 else one(f"SELECT ROUND(SUM(g.Debit-g.Credit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID WHERE {w} AND g.VoucherNumber='{OPEN}'")[0] or 0)
    d0, d1 = f"{y}-01-01", YE[y]
    def avg(w): return (beg(w) + bal(w, d1)) / 2
    dso = avg("a.AccountNumber='1020'") / flow("a.AccountNumber='1020'", d0, d1, src="SalesInvoice") * 365
    dio = avg("a.AccountNumber IN ('1040','1045','1046')") / flow("a.AccountSubType='COGS'", d0, d1) * 365
    mat = avg("a.AccountNumber='1045'") / flow("a.AccountNumber='1045'", d0, d1, "Credit-Debit", src="MaterialIssue") * 365
    dpo = -avg("a.AccountNumber='2010'") / flow("a.AccountNumber='2010'", d0, d1, "Credit-Debit", src="PurchaseInvoice") * 365
    print(y, f"avg DSO {dso:.1f} DIO {dio:.1f} materials {mat:.1f} DPO {dpo:.1f}")
print("terms (value-weighted days): customers", one("""SELECT ROUND(SUM(si.GrandTotal*CAST(REPLACE(c.PaymentTerms,'Net ','') AS REAL))/SUM(si.GrandTotal),1)
    FROM SalesInvoice si JOIN Customer c ON c.CustomerID=si.CustomerID""")[0],
      "suppliers", one("""SELECT ROUND(SUM(pi.GrandTotal*CAST(REPLACE(s.PaymentTerms,'Net ','') AS REAL))/SUM(pi.GrandTotal),1)
    FROM PurchaseInvoice pi JOIN Supplier s ON s.SupplierID=pi.SupplierID""")[0])
print("policy targets:", q("""SELECT i.ItemGroup, p.PolicyType, MIN(p.TargetDaysSupply), MAX(p.TargetDaysSupply), MIN(p.EffectiveEndDate), MAX(p.EffectiveEndDate), COUNT(*)
    FROM InventoryPolicy p JOIN Item i ON i.ItemID=p.ItemID GROUP BY 1,2"""))
print("policy rows per item:", q("SELECT COUNT(*), COUNT(DISTINCT ItemID), COUNT(DISTINCT ItemID||'-'||WarehouseID) FROM InventoryPolicy"))

# ---- Requirement 4 ------------------------------------------------------------------------
hdr("R4 materials build")
RCH = """CASE WHEN r.Justification LIKE 'WO-COMPONENT-SHORTFALL%' THEN 'Shortfall' WHEN r.Justification LIKE 'Supply plan%' THEN 'Supply plan' ELSE 'Other' END"""
print("materials receipts by year and channel:", q(f"""SELECT substr(g.ReceiptDate,1,4), {RCH}, COUNT(*), ROUND(SUM(l.ExtendedStandardCost),2)
    FROM GoodsReceiptLine l JOIN GoodsReceipt g ON g.GoodsReceiptID=l.GoodsReceiptID JOIN Item i ON i.ItemID=l.ItemID
    JOIN PurchaseOrderLine p ON p.POLineID=l.POLineID LEFT JOIN PurchaseRequisition r ON r.RequisitionID=p.RequisitionID
    WHERE i.ItemGroup IN ('Raw Materials','Packaging') GROUP BY 1,2"""))
print("all receipts by channel and item group:", q(f"""SELECT {RCH}, i.ItemGroup, COUNT(*), ROUND(SUM(l.ExtendedStandardCost),2)
    FROM GoodsReceiptLine l JOIN Item i ON i.ItemID=l.ItemID JOIN PurchaseOrderLine p ON p.POLineID=l.POLineID
    LEFT JOIN PurchaseRequisition r ON r.RequisitionID=p.RequisitionID GROUP BY 1,2"""))
print("issues by year and group:", q("""SELECT substr(m.IssueDate,1,4), i.ItemGroup, ROUND(SUM(l.ExtendedStandardCost),2) FROM MaterialIssueLine l
    JOIN MaterialIssue m ON m.MaterialIssueID=l.MaterialIssueID JOIN Item i ON i.ItemID=l.ItemID GROUP BY 1,2"""))
build = q("""WITH r AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM GoodsReceiptLine l JOIN GoodsReceipt g ON g.GoodsReceiptID=l.GoodsReceiptID
      WHERE g.ReceiptDate BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY 1),
    s AS (SELECT l.ItemID, SUM(l.ExtendedStandardCost) v FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID=l.MaterialIssueID
      WHERE m.IssueDate BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY 1)
    SELECT i.ItemCode, i.ItemName, i.ItemGroup, ROUND(COALESCE(r.v,0)-COALESCE(s.v,0),2) d FROM Item i LEFT JOIN r ON r.ItemID=i.ItemID LEFT JOIN s ON s.ItemID=i.ItemID
    WHERE i.ItemGroup IN ('Raw Materials','Packaging') ORDER BY d DESC""")
tot = sum(b[3] for b in build)
print("2026 build", round(tot, 2), "| top six", build[:6], "share", round(sum(b[3] for b in build[:6]) / tot, 3),
      "| packaging", round(sum(b[3] for b in build if b[2] == 'Packaging'), 2))
pairs = q("""SELECT Justification, COUNT(*), SUM(Quantity), SUM(Quantity*EstimatedUnitCost), MIN(RequestDate), MAX(RequestDate)
    FROM PurchaseRequisition WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%' GROUP BY 1""")
rep = [p for p in pairs if p[1] > 1]
print("shortfall by year:", q("""SELECT substr(RequestDate,1,4), COUNT(*), ROUND(SUM(Quantity*EstimatedUnitCost),2) FROM PurchaseRequisition
    WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%' GROUP BY 1"""))
print("pairs", len(pairs), "| repeated pairs", len(rep), "holding", sum(p[1] for p in rep), "| max", max(pairs, key=lambda p: p[1]))
print("justification ITEM equals ItemID:", one("""SELECT SUM(CAST(substr(Justification, instr(Justification,'ITEM=')+5) AS INTEGER)=ItemID), COUNT(*)
    FROM PurchaseRequisition WHERE Justification LIKE 'WO-COMPONENT-SHORTFALL%'"""))
iss = dict(((k, v) for k, v in q("""SELECT 'WO-COMPONENT-SHORTFALL | WO=' || m.WorkOrderID || ' | ITEM=' || l.ItemID, SUM(l.QuantityIssued)
    FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID=l.MaterialIssueID GROUP BY 1""")))
iss_cost = dict(q("""SELECT 'WO-COMPONENT-SHORTFALL | WO=' || m.WorkOrderID || ' | ITEM=' || l.ItemID, SUM(l.ExtendedStandardCost)
    FROM MaterialIssueLine l JOIN MaterialIssue m ON m.MaterialIssueID=l.MaterialIssueID GROUP BY 1"""))
matched = [p for p in pairs if p[0] in iss]
print("pairs matched", len(matched), "unmatched", len(pairs) - len(matched),
      "| requisitioned units", round(sum(p[2] for p in pairs), 1), "est", round(sum(p[3] for p in pairs), 2),
      "| issued units to same pairs", round(sum(iss.get(p[0], 0) for p in pairs), 1), "at standard", round(sum(iss_cost.get(p[0], 0) for p in pairs), 2))
mx = max(pairs, key=lambda p: p[1]); woid = int(mx[0].split("WO=")[1].split(" ")[0]); itid = int(mx[0].split("ITEM=")[1])
print("max pair WO", one("SELECT WorkOrderNumber, ReleasedDate, DueDate, CompletedDate, ClosedDate FROM WorkOrder WHERE WorkOrderID=?", (woid,)) if 'CompletedDate' in [r[1] for r in q('PRAGMA table_info(WorkOrder)')] else one("SELECT * FROM WorkOrder WHERE WorkOrderID=?", (woid,)),
      "| item", one("SELECT ItemCode, ItemName FROM Item WHERE ItemID=?", (itid,)))
print("approvers by channel:", q(f"""SELECT {CH}, r.ApprovedByEmployeeID, e.JobTitle, COUNT(*), SUM(r.RequestedByEmployeeID=r.ApprovedByEmployeeID)
    FROM PurchaseRequisition r LEFT JOIN Employee e ON e.EmployeeID=r.ApprovedByEmployeeID GROUP BY 1,2 ORDER BY 1,4 DESC"""))
print("shortfall requesters:", q("""SELECT e.JobTitle, COUNT(*) FROM PurchaseRequisition r JOIN Employee e ON e.EmployeeID=r.RequestedByEmployeeID
    WHERE r.Justification LIKE 'WO-COMPONENT-SHORTFALL%' GROUP BY 1 ORDER BY 2 DESC"""))
issues_ttm = flow("a.AccountNumber='1045'", "2026-01-01", "2026-12-31", "Credit-Debit", src="MaterialIssue")
mat26 = bal("a.AccountNumber='1045'", "2026-12-31")
for days in (28, 60, 90):
    allowed = issues_ttm / 365 * days; excess = mat26 - allowed
    print(f"target {days}: allowed {allowed:,.2f} excess {excess:,.2f} months {excess / (issues_ttm / 12):.2f}")
fg26 = bal("a.AccountNumber='1040'", "2026-12-31"); ships26 = flow("a.AccountNumber='1040'", "2026-01-01", "2026-12-31", "Credit-Debit", src="Shipment")
print("FG at 28 days", round(ships26 / 365 * 28, 2), "vs", fg26)
print("approved, never ordered:", q("""SELECT Status, COUNT(*), ROUND(SUM(Quantity*EstimatedUnitCost),2), MIN(RequestDate), MAX(RequestDate) FROM PurchaseRequisition r
    WHERE r.RequisitionID NOT IN (SELECT RequisitionID FROM PurchaseOrderLine WHERE RequisitionID IS NOT NULL) GROUP BY 1"""))
print("PO lines not fully received at 2026-12-31:", q("""WITH rec AS (SELECT l.POLineID, SUM(l.QuantityReceived) q FROM GoodsReceiptLine l JOIN GoodsReceipt g ON g.GoodsReceiptID=l.GoodsReceiptID
      WHERE g.ReceiptDate<='2026-12-31' GROUP BY 1)
    SELECT i.ItemGroup IN ('Raw Materials','Packaging'), COUNT(*), ROUND(SUM((p.Quantity-COALESCE(rec.q,0))*p.UnitCost),2) FROM PurchaseOrderLine p
    JOIN PurchaseOrder o ON o.PurchaseOrderID=p.PurchaseOrderID JOIN Item i ON i.ItemID=p.ItemID LEFT JOIN rec ON rec.POLineID=p.POLineID
    WHERE o.OrderDate<='2026-12-31' AND p.Quantity-COALESCE(rec.q,0)>0.0001 GROUP BY 1"""))

# ---- Requirement 5 ------------------------------------------------------------------------
hdr("R5 rollforward and reconciliations at 2026-12-31")
for acct in ("1020", "1045", "1040", "2010", "2020", "2050"):
    print(acct, q(f"""SELECT g.SourceDocumentType, ROUND(SUM(g.Debit-g.Credit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
        WHERE a.AccountNumber=? AND g.PostingDate<='2026-12-31' AND {NOCLOSE} GROUP BY 1""", (acct,)), "balance", bal(f"a.AccountNumber='{acct}'", "2026-12-31"))
ar = q("""WITH app AS (SELECT SalesInvoiceID, SUM(AppliedAmount) v FROM CashReceiptApplication WHERE ApplicationDate<='2026-12-31' GROUP BY 1),
    cm AS (SELECT OriginalSalesInvoiceID id, SUM(GrandTotal) v FROM CreditMemo WHERE CreditMemoDate<='2026-12-31' GROUP BY 1)
    SELECT ROUND(si.GrandTotal-COALESCE(app.v,0)-COALESCE(cm.v,0),2) b FROM SalesInvoice si LEFT JOIN app ON app.SalesInvoiceID=si.SalesInvoiceID
    LEFT JOIN cm ON cm.id=si.SalesInvoiceID WHERE si.InvoiceDate<='2026-12-31'""")
pos = [r[0] for r in ar if r[0] > 0]; neg = [r[0] for r in ar if r[0] < 0]
print("open AR", len(pos), round(sum(pos), 2), "| negative", len(neg), round(sum(neg), 2), "| GL 1020", bal("a.AccountNumber='1020'", "2026-12-31"))
ap = q("""WITH pay AS (SELECT PurchaseInvoiceID, SUM(Amount) v FROM DisbursementPayment WHERE PaymentDate<='2026-12-31' GROUP BY 1)
    SELECT pi.PurchaseInvoiceID, ROUND(pi.GrandTotal-COALESCE(pay.v,0),2) b, pi.DueDate FROM PurchaseInvoice pi LEFT JOIN pay ON pay.PurchaseInvoiceID=pi.PurchaseInvoiceID
    WHERE pi.ReceivedDate<='2026-12-31'""")
op = [r for r in ap if r[1] > 0.004]
due = [r for r in op if r[2] < '2026-12-31']
notes = [r for r in op if r[0] in (3160, 21692)]
print("open AP", len(op), round(sum(r[1] for r in op), 2), "| past due", round(sum(r[1] for r in due), 2),
      "| without note invoices", round(sum(r[1] for r in due if r[0] not in (3160, 21692)), 2), "of", round(sum(r[1] for r in op if r[0] not in (3160, 21692)), 2),
      "| notes", notes, "| GL 2010", bal("a.AccountNumber='2010'", "2026-12-31"))
print("open AP on InvoiceDate at 2025-12-31 differs by:", q("""SELECT InvoiceNumber, InvoiceDate, ReceivedDate, GrandTotal FROM PurchaseInvoice
    WHERE InvoiceDate<='2025-12-31' AND ReceivedDate>'2025-12-31'"""))
for y in YEARS:
    gl = flow("a.AccountNumber='1020'", f"{y}-01-01", YE[y], src="SalesInvoice")
    docs = one("SELECT ROUND(SUM(GrandTotal),2) FROM SalesInvoice WHERE InvoiceDate BETWEEN ? AND ?", (f"{y}-01-01", YE[y]))[0]
    print(y, "billing GL", gl, "invoices dated", docs, "difference", round(docs - gl, 2))
print("invoices posted in a later year:", q("""SELECT si.InvoiceNumber, si.InvoiceDate, MIN(g.PostingDate), si.GrandTotal FROM SalesInvoice si
    JOIN GLEntry g ON g.SourceDocumentType='SalesInvoice' AND g.SourceDocumentID=si.SalesInvoiceID
    GROUP BY si.SalesInvoiceID HAVING substr(si.InvoiceDate,1,4)<>substr(MIN(g.PostingDate),1,4)"""))
print("open AR rebuilt at 2024-12-31 and 2025-12-31 vs GL:")
for d in ("2024-12-31", "2025-12-31"):
    v = one(f"""WITH app AS (SELECT SalesInvoiceID, SUM(AppliedAmount) v FROM CashReceiptApplication WHERE ApplicationDate<=? GROUP BY 1),
        cm AS (SELECT OriginalSalesInvoiceID id, SUM(GrandTotal) v FROM CreditMemo WHERE CreditMemoDate<=? GROUP BY 1)
        SELECT ROUND(SUM(si.GrandTotal-COALESCE(app.v,0)-COALESCE(cm.v,0)),2) FROM SalesInvoice si LEFT JOIN app ON app.SalesInvoiceID=si.SalesInvoiceID
        LEFT JOIN cm ON cm.id=si.SalesInvoiceID WHERE si.InvoiceDate<=?""", (d, d, d))[0]
    print(d, "subledger (all balances)", v, "GL", bal("a.AccountNumber='1020'", d), "difference", round(bal("a.AccountNumber='1020'", d) - v, 2))
print("credit memos to 1020 vs 2060 by year:", q("""SELECT g.FiscalYear, a.AccountNumber, ROUND(SUM(g.Debit-g.Credit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
    WHERE g.SourceDocumentType='CreditMemo' AND a.AccountNumber IN ('1020','2060') GROUP BY 1,2"""))
