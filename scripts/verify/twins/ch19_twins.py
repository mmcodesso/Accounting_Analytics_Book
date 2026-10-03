"""Read-only twins for Chapter 19 ("Auditing the Customer Credits Cycle"). Every value the chapter's instructor notes
state is computed here: SQL for the records, Python for the workbook's materiality, sampling, and evaluation."""
import sqlite3
import statistics as st
from collections import Counter, defaultdict
from datetime import date

from scipy.stats import beta, hypergeom

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, db_uri  # noqa: E402
c = sqlite3.connect(db_uri(), uri=True)
q = lambda s, p=(): c.execute(s, p).fetchall()
one = lambda s, p=(): c.execute(s, p).fetchone()
r2 = lambda x: round(x + 0.0, 2)
D = date.fromisoformat
YEARS = ("2024", "2025", "2026")
AID = {str(r[0]): r[1] for r in q("SELECT AccountNumber, AccountID FROM Account")}
EMP = {r[0]: dict(title=r[1], limit=r[2] or 0, hire=r[3], term=r[4]) for r in q(
    "SELECT EmployeeID, JobTitle, MaxApprovalAmount, HireDate, TerminationDate FROM Employee")}
CLOSES = [r[0] for r in q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%'")]
CL = "(" + ",".join(f"'{v}'" for v in CLOSES) + ")"


def hdr(t):
    print(f"\n=== {t}")


def titles(ids):
    return dict(Counter(EMP[i]["title"] for i in ids))


INV = {r[0]: dict(num=r[1], cust=r[2], date=r[3], due=r[4], gt=r[5], freight=r[6]) for r in q(
    "SELECT SalesInvoiceID, InvoiceNumber, CustomerID, InvoiceDate, DueDate, GrandTotal, FreightAmount FROM SalesInvoice")}
CM = {r[0]: dict(num=r[1], date=r[2], ret=r[3], cust=r[4], inv=r[5], sub=r[6], freight=r[7], tax=r[8], gt=r[9], status=r[10],
                 appr=r[11], adate=r[12]) for r in q("""SELECT CreditMemoID, CreditMemoNumber, CreditMemoDate, SalesReturnID, CustomerID,
    OriginalSalesInvoiceID, SubTotal, FreightCreditAmount, TaxAmount, GrandTotal, Status, ApprovedByEmployeeID, ApprovedDate FROM CreditMemo""")}
RF = {r[0]: dict(num=r[1], date=r[2], cust=r[3], cm=r[4], amt=r[5], method=r[6], appr=r[7], cleared=r[8]) for r in q(
    """SELECT CustomerRefundID, RefundNumber, RefundDate, CustomerID, CreditMemoID, Amount, PaymentMethod, ApprovedByEmployeeID, ClearedDate
    FROM CustomerRefund""")}
SR = {r[0]: dict(num=r[1], date=r[2], cust=r[3], recv=r[4], reason=r[5], status=r[6]) for r in q(
    "SELECT SalesReturnID, ReturnNumber, ReturnDate, CustomerID, ReceivedByEmployeeID, ReasonCode, Status FROM SalesReturn")}
APPS = defaultdict(list)          # by invoice: (date, amount, applier, receipt)
for inv, d, amt, emp, rid in q("SELECT SalesInvoiceID, ApplicationDate, AppliedAmount, AppliedByEmployeeID, CashReceiptID FROM CashReceiptApplication"):
    APPS[inv].append((d, amt, emp, rid))
RCPT = {r[0]: dict(num=r[1], date=r[2], cust=r[3], inv=r[4], amt=r[5], method=r[6], ref=r[7], dep=r[8], rec=r[9]) for r in q(
    """SELECT CashReceiptID, ReceiptNumber, ReceiptDate, CustomerID, SalesInvoiceID, Amount, PaymentMethod, ReferenceNumber, DepositDate,
    RecordedByEmployeeID FROM CashReceipt""")}
CRED = defaultdict(list)          # credits by invoice: (date, grand total)
for m in CM.values():
    CRED[m["inv"]].append((m["date"], m["gt"]))

# ---- Requirement 1 ------------------------------------------------------------------------------------------
hdr("R1 map of the cycle")
print("returns", len(SR), "lines", one("SELECT COUNT(*) FROM SalesReturnLine")[0], "dates", min(s["date"] for s in SR.values()), max(s["date"] for s in SR.values()),
      "customers", len({s["cust"] for s in SR.values()}), "status", Counter(s["status"] for s in SR.values()), "reasons", Counter(s["reason"] for s in SR.values()))
print("  received by", titles([s["recv"] for s in SR.values()]))
print("credits", len(CM), "lines", one("SELECT COUNT(*) FROM CreditMemoLine")[0], "dates", min(m["date"] for m in CM.values()), max(m["date"] for m in CM.values()),
      "status", {k: (n, r2(sum(m["gt"] for m in CM.values() if m["status"] == k))) for k, n in Counter(m["status"] for m in CM.values()).items()},
      "total", r2(sum(m["gt"] for m in CM.values())))
print("  approved by", titles([m["appr"] for m in CM.values()]), "| ApprovedDate = CreditMemoDate", sum(m["adate"] == m["date"] for m in CM.values()))
lag = [(D(m["date"]) - D(SR[m["ret"]]["date"])).days for m in CM.values()]
print("  days after the return: min", min(lag), "max", max(lag), "mean", round(st.mean(lag), 1), "same day", lag.count(0))
rl = [(D(r["date"]) - D(CM[r["cm"]]["date"])).days for r in RF.values()]
cl = [(D(r["cleared"]) - D(r["date"])).days for r in RF.values()]
print("refunds", len(RF), r2(sum(r["amt"] for r in RF.values())), "dates", min(r["date"] for r in RF.values()), max(r["date"] for r in RF.values()),
      "| days after credit", min(rl), max(rl), round(st.mean(rl), 1), "over 30", sum(x > 30 for x in rl), "| cleared after", min(cl), max(cl))
print("  approved by", titles([r["appr"] for r in RF.values()]), "| one refund per credit", len({r["cm"] for r in RF.values()}) == len(RF))
adj = q("""SELECT a.AdjustmentNumber, a.AdjustmentDate, a.CreditMemoID, a.ApprovedByEmployeeID, a.CommissionBaseReductionAmount, a.CommissionRatePct,
    a.CommissionAdjustmentAmount, a.SalesCommissionAccrualID, a.CreditMemoLineID FROM SalesCommissionAdjustment a""")
print("clawbacks", len(adj), r2(sum(a[6] for a in adj)), "same date as credit", sum(a[1] == CM[a[2]]["date"] for a in adj),
      "same approver", sum(a[3] == CM[a[2]]["appr"] for a in adj))
print("receipts", len(RCPT), r2(sum(r["amt"] for r in RCPT.values())), "recorded by", titles([r["rec"] for r in RCPT.values()]))
print("applications", sum(len(v) for v in APPS.values()), "applied by", titles([a[2] for v in APPS.values() for a in v]))
orph = {
    "return line -> shipment line": one("SELECT COUNT(*) FROM SalesReturnLine srl WHERE NOT EXISTS (SELECT 1 FROM ShipmentLine sl WHERE sl.ShipmentLineID = srl.ShipmentLineID)")[0],
    "credit -> return": one("SELECT COUNT(*) FROM CreditMemo cm WHERE NOT EXISTS (SELECT 1 FROM SalesReturn sr WHERE sr.SalesReturnID = cm.SalesReturnID)")[0],
    "credit -> invoice": one("SELECT COUNT(*) FROM CreditMemo cm WHERE NOT EXISTS (SELECT 1 FROM SalesInvoice si WHERE si.SalesInvoiceID = cm.OriginalSalesInvoiceID)")[0],
    "credit line -> return line": one("SELECT COUNT(*) FROM CreditMemoLine l WHERE NOT EXISTS (SELECT 1 FROM SalesReturnLine r WHERE r.SalesReturnLineID = l.SalesReturnLineID)")[0],
    "return without credit": one("SELECT COUNT(*) FROM SalesReturn sr WHERE NOT EXISTS (SELECT 1 FROM CreditMemo cm WHERE cm.SalesReturnID = sr.SalesReturnID)")[0],
    "refund -> credit": one("SELECT COUNT(*) FROM CustomerRefund r WHERE NOT EXISTS (SELECT 1 FROM CreditMemo cm WHERE cm.CreditMemoID = r.CreditMemoID)")[0],
    "clawback -> credit line": one("SELECT COUNT(*) FROM SalesCommissionAdjustment a WHERE NOT EXISTS (SELECT 1 FROM CreditMemoLine l WHERE l.CreditMemoLineID = a.CreditMemoLineID)")[0],
    "credit line without clawback": one("SELECT COUNT(*) FROM CreditMemoLine l WHERE NOT EXISTS (SELECT 1 FROM SalesCommissionAdjustment a WHERE a.CreditMemoLineID = l.CreditMemoLineID)")[0],
    "clawback -> accrual": one("SELECT COUNT(*) FROM SalesCommissionAdjustment a WHERE NOT EXISTS (SELECT 1 FROM SalesCommissionAccrual x WHERE x.SalesCommissionAccrualID = a.SalesCommissionAccrualID)")[0],
}
print("orphans", orph)


def gaps(table, col):
    out = {}
    for y in YEARS:
        nums = sorted(int(n[-6:]) for (n,) in q(f"SELECT {col} FROM {table} WHERE substr({col}, 4, 4) = ? OR substr({col}, 6, 4) = ?", (y, y)))
        out[y] = (nums[0], nums[-1], len(nums), nums[-1] - nums[0] + 1 - len(nums)) if nums else None
    return out


for t, col in (("SalesReturn", "ReturnNumber"), ("CreditMemo", "CreditMemoNumber"), ("CustomerRefund", "RefundNumber"), ("SalesCommissionAdjustment", "AdjustmentNumber")):
    print("  numbering", t, gaps(t, col))
print("posting matrix", [(r[0], r[1], r[2], r2(r[3]), r2(r[4])) for r in q(f"""SELECT g.SourceDocumentType, a.AccountNumber, COUNT(*), SUM(g.Debit), SUM(g.Credit)
    FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID
    WHERE g.SourceDocumentType IN ('SalesReturn', 'CreditMemo', 'CustomerRefund', 'SalesCommissionAdjustment') GROUP BY 1, 2""")])
print("  rows by type", q("""SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE SourceDocumentType IN ('SalesReturn', 'CreditMemo', 'CustomerRefund',
    'SalesCommissionAdjustment', 'CashReceipt', 'CashReceiptApplication') GROUP BY 1"""))
both_accts = sum(1 for (n,) in q(f"""SELECT COUNT(DISTINCT g.AccountID) FROM GLEntry g WHERE g.SourceDocumentType = 'CreditMemo' AND g.Credit > 0
    AND g.AccountID IN ({AID['1020']}, {AID['2060']}) GROUP BY g.SourceDocumentID""") if n == 2)
print("  credits posting to both 1020 and 2060", both_accts)
for src, table, key, col in (("CreditMemo", "CreditMemo", "CreditMemoID", "ApprovedByEmployeeID"), ("CustomerRefund", "CustomerRefund", "CustomerRefundID", "ApprovedByEmployeeID"),
                             ("SalesCommissionAdjustment", "SalesCommissionAdjustment", "SalesCommissionAdjustmentID", "ApprovedByEmployeeID"),
                             ("CashReceipt", "CashReceipt", "CashReceiptID", "RecordedByEmployeeID"),
                             ("CashReceiptApplication", "CashReceiptApplication", "CashReceiptApplicationID", "AppliedByEmployeeID")):
    print("  poster = document's person", src, one(f"""SELECT SUM(g.CreatedByEmployeeID = t.{col}), COUNT(*) FROM GLEntry g JOIN {table} t ON t.{key} = g.SourceDocumentID
        WHERE g.SourceDocumentType = '{src}'"""))
emp_issue = []
for kind, rows in (("return", [(s["recv"], s["date"]) for s in SR.values()]), ("credit", [(m["appr"], m["date"]) for m in CM.values()]),
                   ("refund", [(r["appr"], r["date"]) for r in RF.values()]), ("receipt", [(r["rec"], r["date"]) for r in RCPT.values()])):
    bad = [(e, d) for e, d in rows if (EMP[e]["term"] and d > EMP[e]["term"]) or (EMP[e]["hire"] and d < EMP[e]["hire"])]
    emp_issue.append((kind, len(bad)))
print("employment-date exceptions", emp_issue)

# ---- Requirement 2 ------------------------------------------------------------------------------------------
hdr("R2 reconciliation by year")
NOCL = f"NOT (g.SourceDocumentType = 'JournalEntry' AND g.VoucherNumber IN {CL})"


def gl(acct, y, src, side):
    return one(f"""SELECT ROUND(COALESCE(SUM(g.{side}), 0), 2) FROM GLEntry g WHERE g.AccountID = ? AND g.PostingDate LIKE ? AND g.SourceDocumentType = ?""",
               (AID[acct], y + "%", src))[0]


for y in YEARS:
    ms = [m for m in CM.values() if m["date"][:4] == y]
    print(y, "credits", len(ms), "sub", r2(sum(m["sub"] for m in ms)), "4060", gl("4060", y, "CreditMemo", "Debit"),
          "| freight", r2(sum(m["freight"] for m in ms)), "4050", gl("4050", y, "CreditMemo", "Debit"),
          "| tax", r2(sum(m["tax"] for m in ms)), "2050", gl("2050", y, "CreditMemo", "Debit"),
          "| GT", r2(sum(m["gt"] for m in ms)), "Cr 1020", gl("1020", y, "CreditMemo", "Credit"), "Cr 2060", gl("2060", y, "CreditMemo", "Credit"))
    sr_cost = one("SELECT ROUND(SUM(srl.ExtendedStandardCost), 2) FROM SalesReturnLine srl JOIN SalesReturn sr ON sr.SalesReturnID = srl.SalesReturnID WHERE sr.ReturnDate LIKE ?", (y + "%",))[0]
    print("   returns std", sr_cost, "1040", gl("1040", y, "SalesReturn", "Debit"), "COGS", {a: gl(a, y, "SalesReturn", "Credit") for a in ("5010", "5020", "5030", "5040")})
    rs = [r for r in RF.values() if r["date"][:4] == y]
    print("   refunds", len(rs), r2(sum(r["amt"] for r in rs)), "Cr 1010", gl("1010", y, "CustomerRefund", "Credit"), "Dr 2060", gl("2060", y, "CustomerRefund", "Debit"))
    cb = r2(sum(a[6] for a in adj if a[1][:4] == y))
    print("   clawbacks", cb, "Dr 2034", gl("2034", y, "SalesCommissionAdjustment", "Debit"), "Cr 6290", gl("6290", y, "SalesCommissionAdjustment", "Credit"),
          "| accruals", one("SELECT ROUND(SUM(CommissionAmount), 2) FROM SalesCommissionAccrual WHERE AccrualDate LIKE ?", (y + "%",))[0],
          "payments", one("SELECT ROUND(SUM(NetPaymentAmount), 2) FROM SalesCommissionPayment WHERE PaymentDate LIKE ?", (y + "%",))[0])
    rc = r2(sum(r["amt"] for r in RCPT.values() if r["date"][:4] == y)); ap = r2(sum(a[1] for v in APPS.values() for a in v if a[0][:4] == y))
    print("   receipts", rc, "Dr 1010", gl("1010", y, "CashReceipt", "Debit"), "| applications", ap, "Cr 1020", gl("1020", y, "CashReceiptApplication", "Credit"))
print("2060 at year-ends", [one(f"SELECT ROUND(SUM(Credit - Debit), 2) FROM GLEntry WHERE AccountID = {AID['2060']} AND PostingDate <= ?", (f"{y}-12-31",))[0] for y in YEARS])
for y in YEARS:
    ye = f"{y}-12-31"
    items = q(f"""SELECT g.SourceDocumentID, ROUND(SUM(g.Credit - g.Debit), 2) FROM GLEntry g WHERE g.AccountID = {AID['2060']} AND g.PostingDate <= ?
        AND g.SourceDocumentType IN ('CreditMemo', 'CustomerRefund') GROUP BY g.SourceDocumentType, g.SourceDocumentID""", (ye,))
    cm2060 = defaultdict(float)
    for doc, amt in q(f"""SELECT g.SourceDocumentID, SUM(g.Credit) FROM GLEntry g WHERE g.AccountID = {AID['2060']} AND g.PostingDate <= ? AND g.SourceDocumentType = 'CreditMemo'
            GROUP BY 1""", (ye,)):
        cm2060[doc] += amt
    for r in RF.values():
        if r["date"] <= ye:
            cm2060[r["cm"]] -= r["amt"]
    print("  2060 open credit items at", ye, [(CM[k]["num"], r2(v)) for k, v in cm2060.items() if v > 0.005])
print("2034 at 2026", one(f"SELECT ROUND(SUM(Credit - Debit), 2) FROM GLEntry WHERE AccountID = {AID['2034']} AND PostingDate <= '2026-12-31'")[0])
print("closes on 4060 and 6290", q(f"""SELECT a.AccountNumber, COUNT(*), ROUND(SUM(g.Credit - g.Debit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID
    WHERE a.AccountNumber IN (4060, 6290) AND g.SourceDocumentType = 'JournalEntry' GROUP BY 1"""))

# ---- Requirement 3 ------------------------------------------------------------------------------------------
hdr("R3 materiality and expectation")
for base, label in ((4572087.08, "July package, adjusted"), (4503611.24, "ledger")):
    print(f"  {label}: materiality {base*0.05:,.2f} performance {base*0.05*0.75:,.2f} trivial {base*0.05*0.05:,.2f}")
rev = {y: one(f"""SELECT ROUND(SUM(g.Credit - g.Debit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber IN (4010, 4020, 4030, 4040, 4080)
    AND g.PostingDate LIKE ? AND g.SourceDocumentType = 'SalesInvoice'""", (y + "%",))[0] for y in YEARS}
ret = {y: r2(sum(m["sub"] for m in CM.values() if m["date"][:4] == y)) for y in YEARS}
print("  return rates", {y: round(ret[y] / rev[y] * 100, 3) for y in YEARS}, "revenue", rev)
exp = ret["2024"] / rev["2024"] * rev["2026"]
print("  2026 expectation at the 2024 rate", r2(exp), "actual", ret["2026"], "difference", r2(ret["2026"] - exp), f"{(ret['2026']/exp-1)*100:+.1f}%")

# ---- Requirement 4 ------------------------------------------------------------------------------------------
hdr("R4 control tests")
cm_above = [m for m in CM.values() if m["gt"] > EMP[m["appr"]]["limit"]]
print("credits above limit", len(cm_above), r2(sum(m["gt"] for m in cm_above)), {y: (sum(m["date"][:4] == y for m in cm_above), r2(sum(m["gt"] for m in cm_above if m["date"][:4] == y))) for y in YEARS},
      titles([m["appr"] for m in cm_above]), "| manager exceeded", sum(1 for m in CM.values() if EMP[m["appr"]]["limit"] > 0 and m["gt"] > EMP[m["appr"]]["limit"]))
cash_credit = [m for m in CM.values() if any(a[2] == m["appr"] for a in APPS[m["inv"]])]
cc_early = [m for m in cash_credit if any(a[2] == m["appr"] and a[0] <= m["date"] for a in APPS[m["inv"]])]
cc_rec = [m for m in CM.values() if any(a[2] == m["appr"] or RCPT[a[3]]["rec"] == m["appr"] for a in APPS[m["inv"]])]
print("approver applied cash", len(cash_credit), r2(sum(m["gt"] for m in cash_credit)), {y: sum(m["date"][:4] == y for m in cash_credit) for y in YEARS},
      "2026", r2(sum(m["gt"] for m in cash_credit if m["date"][:4] == "2026")), "| on or before the credit", len(cc_early), r2(sum(m["gt"] for m in cc_early)),
      "2026", sum(m["date"][:4] == "2026" for m in cc_early), "| recorded or applied", len(cc_rec), r2(sum(m["gt"] for m in cc_rec)))
rf_above = [r for r in RF.values() if r["amt"] > EMP[r["appr"]]["limit"]]
print("refunds above limit", len(rf_above), r2(sum(r["amt"] for r in rf_above)), {t: (n, r2(sum(r["amt"] for r in rf_above if EMP[r["appr"]]["title"] == t))) for t, n in titles([r["appr"] for r in rf_above]).items()},
      {y: (sum(r["date"][:4] == y for r in rf_above), r2(sum(r["amt"] for r in rf_above if r["date"][:4] == y))) for y in YEARS},
      "| within limit", titles([r["appr"] for r in RF.values() if r not in rf_above]), r2(sum(r["amt"] for r in RF.values() if r not in rf_above)))
before = [r for r in RF.values() if max(a[0] for a in APPS[CM[r["cm"]]["inv"]]) > r["date"]]
nothing = [r for r in RF.values() if not any(a[0] <= r["date"] for a in APPS[CM[r["cm"]]["inv"]])]
before_due = [r for r in before if r["date"] < INV[CM[r["cm"]]["inv"]]["due"]]
wait = [(D(max(a[0] for a in APPS[CM[r["cm"]]["inv"]])) - D(r["date"])).days for r in before]
print("refund before payment", len(before), r2(sum(r["amt"] for r in before)), {y: (sum(r["date"][:4] == y for r in before), r2(sum(r["amt"] for r in before if r["date"][:4] == y))) for y in YEARS},
      "| nothing paid", len(nothing), r2(sum(r["amt"] for r in nothing)), "2026", sum(r["date"][:4] == "2026" for r in nothing), r2(sum(r["amt"] for r in nothing if r["date"][:4] == "2026")),
      "| before due date", len(before_due), "| days to payment", min(wait), max(wait), round(st.mean(wait), 1))
cm_to_2060 = {doc: amt for doc, amt in q(f"SELECT SourceDocumentID, SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'CreditMemo' AND AccountID = {AID['2060']} AND Credit > 0 GROUP BY 1")}
unpaid_at_credit = [k for k in cm_to_2060 if not any(a[0] <= CM[k]["date"] for a in APPS[CM[k]["inv"]])]
fully_paid = [k for k in cm_to_2060 if sum(a[1] for a in APPS[CM[k]["inv"]] if a[0] <= CM[k]["date"]) >= INV[CM[k]["inv"]]["gt"] - CM[k]["gt"] - 0.01]
print("credits to 2060", len(cm_to_2060), "nothing paid at credit date", len(unpaid_at_credit), "| refund = credit's 2060 part", sum(1 for r in RF.values() if abs(cm_to_2060.get(r["cm"], 0) - r["amt"]) < 0.005))
by_cust = defaultdict(list)
for i, v in INV.items():
    by_cust[v["cust"]].append(i)


def past_due(cust, asof):
    tot = 0.0
    for i in by_cust[cust]:
        v = INV[i]
        if v["date"] > asof:
            continue
        bal = v["gt"] - sum(a[1] for a in APPS[i] if a[0] <= asof) - sum(a for d, a in CRED[i] if d <= asof)
        if bal > 0.005 and v["due"] < asof:
            tot += bal
    return tot


pdue = {k: past_due(r["cust"], r["date"]) for k, r in RF.items()}
pd1 = [k for k in RF if pdue[k] > 0.005]; pd2 = [k for k in RF if pdue[k] >= RF[k]["amt"]]
print("past due at refund", len(pd1), r2(sum(RF[k]["amt"] for k in pd1)), "| >= refund", len(pd2), r2(sum(RF[k]["amt"] for k in pd2)),
      "2026", sum(RF[k]["date"][:4] == "2026" for k in pd2), r2(sum(RF[k]["amt"] for k in pd2 if RF[k]["date"][:4] == "2026")))
mism = [r for r in RF.values() if r["method"] not in {RCPT[a[3]]["method"] for a in APPS[CM[r["cm"]]["inv"]]}]
print("method mismatch", len(mism), r2(sum(r["amt"] for r in mism)), "2026", sum(r["date"][:4] == "2026" for r in mism), r2(sum(r["amt"] for r in mism if r["date"][:4] == "2026")),
      "| invoices paid by several methods", sum(1 for r in RF.values() if len({RCPT[a[3]]["method"] for a in APPS[CM[r["cm"]]["inv"]]}) > 1),
      "| customers paying by one method only", sum(1 for cu in {x["cust"] for x in RCPT.values()} if len({x["method"] for x in RCPT.values() if x["cust"] == cu}) == 1))
print("refund approver = credit approver", sum(r["appr"] == CM[r["cm"]]["appr"] for r in RF.values()), "| return receiver = credit approver", sum(SR[m["ret"]]["recv"] == m["appr"] for m in CM.values()))
acc = {r[0]: r[1:] for r in q("SELECT SalesCommissionAccrualID, CommissionRatePct, SalesInvoiceLineID FROM SalesCommissionAccrual")}
cml = {r[0]: r[1:] for r in q("SELECT CreditMemoLineID, LineTotal FROM CreditMemoLine")}
acc_ok = sum(1 for a in adj if abs(a[4] - cml[a[8]][0]) < 0.005 and abs(a[5] - acc[a[7]][0]) < 1e-9)
amt_ok = [a[0] for a in adj if abs(a[6] - round(a[4] * a[5], 2)) > 0.004]
print("clawbacks: base = credit line and rate = accrual's", acc_ok, "| amount differs from base x rate", amt_ok,
      [(a[0], a[4], a[5], a[6], a[4] * a[5]) for a in adj if a[0] in amt_ok])
netted = q("SELECT COUNT(DISTINCT SourceDocumentID) FROM SalesCommissionPaymentLine WHERE SourceDocumentType = 'SalesCommissionAdjustment'")[0][0]
print("clawbacks netted in a payment", netted, "pending", len(adj) - netted)
print("commission design: rates approved by", titles([r[0] for r in q("SELECT ApprovedByEmployeeID FROM SalesCommissionRate")]),
      "rates end", q("SELECT DISTINCT EffectiveEndDate FROM SalesCommissionRate"), "| accruals created by", titles([r[0] for r in q("SELECT CreatedByEmployeeID FROM SalesCommissionAccrual")]),
      "| payments approved by", titles([r[0] for r in q("SELECT ApprovedByEmployeeID FROM SalesCommissionPayment")]))

# ---- Requirement 5 ------------------------------------------------------------------------------------------
hdr("R5 returns analytics")
lines = q("""SELECT cm.CreditMemoDate, i.ItemGroup, substr(i.ItemCode, 1, 7), sr.ReasonCode, l.LineTotal, s.ShipmentDate, s.DeliveryDate, s.ShippedBy, s.WarehouseID,
    sr.ReturnDate, cu.CustomerSegment FROM CreditMemoLine l JOIN CreditMemo cm ON cm.CreditMemoID = l.CreditMemoID JOIN Item i ON i.ItemID = l.ItemID
    JOIN SalesReturnLine srl ON srl.SalesReturnLineID = l.SalesReturnLineID JOIN SalesReturn sr ON sr.SalesReturnID = srl.SalesReturnID
    JOIN ShipmentLine sl ON sl.ShipmentLineID = srl.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN Customer cu ON cu.CustomerID = cm.CustomerID""")
g = defaultdict(float)
for d, grp, fam, reason, lt, *_ in lines:
    g[(d[:4], grp)] += lt; g[(d[:4], "reason " + reason)] += lt
print({k: r2(v) for k, v in sorted(g.items())})
furn_rev = {y: one(f"""SELECT ROUND(SUM(g.Credit - g.Debit), 2) FROM GLEntry g WHERE g.AccountID = {AID['4010']} AND g.PostingDate LIKE ? AND g.SourceDocumentType = 'SalesInvoice'""", (y + "%",))[0] for y in YEARS}
print("Furniture rate on 4010", {y: round(g[(y, "Furniture")] / furn_rev[y] * 100, 3) for y in YEARS})
fd = defaultdict(float)
for d, grp, fam, reason, lt, *_ in lines:
    if grp == "Furniture" and reason == "Damaged":
        fd[d[:4]] += lt
print("Furniture Damaged", {k: r2(v) for k, v in fd.items()})
ft = Counter()
for d, grp, fam, reason, lt, *_ in lines:
    if d[:4] == "2026" and grp == "Furniture":
        ft[fam] += lt
print("Furniture families 2026", {k: r2(v) for k, v in ft.most_common()})
seg = defaultdict(float)
for d, grp, fam, reason, lt, sd, dd, carrier, wh, rd, sg in lines:
    seg[(d[:4], sg)] += lt
print("by segment", {k: r2(v) for k, v in sorted(seg.items())})
print("Damaged by carrier", Counter(l[7] for l in lines if l[3] == "Damaged"), "| lines by warehouse", Counter(l[8] for l in lines))
lag_s = [(D(l[9]) - D(l[5])).days for l in lines]; lag_d = [(D(l[9]) - D(l[6])).days for l in lines if l[6]]
print("return lag from shipment", min(lag_s), max(lag_s), round(st.mean(lag_s), 1), "| from delivery", min(lag_d), max(lag_d), round(st.mean(lag_d), 1))
ship_rev = defaultdict(float)
for sd, lt in q("""SELECT s.ShipmentDate, sil.LineTotal FROM SalesInvoiceLine sil JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID
        JOIN Shipment s ON s.ShipmentID = sl.ShipmentID"""):
    ship_rev[sd[:7]] += lt
ret_ship = defaultdict(float)
for l in lines:
    ret_ship[l[5][:7]] += l[4]
print("rate by shipment year", {y: round(sum(v for k, v in ret_ship.items() if k[:4] == y) / sum(v for k, v in ship_rev.items() if k[:4] == y) * 100, 3) for y in YEARS})
m26 = {k: round(ret_ship[k] / ship_rev[k] * 100, 2) for k in sorted(ship_rev) if k[:4] == "2026"}
print("2026 by shipment month", m26)
cross = [l for l in lines if l[9][:4] != l[5][:4]]
print("return lines in a later year than their shipment", len(cross), r2(sum(l[4] for l in cross)), Counter(l[9][:4] for l in cross))
sales_c = dict(q("SELECT si.CustomerID, SUM(sil.LineTotal) FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID GROUP BY 1"))
cred_c = defaultdict(float)
for m in CM.values():
    cred_c[m["cust"]] += m["sub"]
print("credits on sales, company", round(sum(cred_c.values()) / sum(sales_c.values()) * 100, 3))
top = sorted(((cred_c[k] / sales_c[k], k) for k in cred_c), reverse=True)[:5]
print("  highest customers", [(k, round(v * 100, 2), r2(cred_c[k]), r2(sales_c[k])) for v, k in top])
c128 = [m for m in CM.values() if m["cust"] == 128]
print("  customer 128 credits", len(c128), r2(sum(m["gt"] for m in c128)), "approvers", Counter(m["appr"] for m in c128),
      "refunds", [(r["num"], r["amt"], r in before) for r in RF.values() if r["cust"] == 128])
print("refund approver roles by year", {y: titles([r["appr"] for r in RF.values() if r["date"][:4] == y]) for y in YEARS})
cm_above_ids = {id(m) for m in cm_above}
flags = {}
for k, r in RF.items():
    f = [r in rf_above, id(CM[r["cm"]]) in cm_above_ids, r in mism, r in before, pdue[k] >= r["amt"]]
    flags[k] = f
score = Counter(sum(f) for f in flags.values())
hi = [k for k, f in flags.items() if sum(f) >= 4]
print("flag score distribution", dict(sorted(score.items())), "| 4-5", len(hi), r2(sum(RF[k]["amt"] for k in hi)),
      "| RF-2025-000097", sum(flags[[k for k in RF if RF[k]["num"] == "RF-2025-000097"][0]]),
      "| score 5", [(RF[k]["num"], RF[k]["cust"], RF[k]["amt"]) for k, f in flags.items() if sum(f) == 5])
print("weekend refunds", sum(D(r["date"]).weekday() >= 5 for r in RF.values()), "credits", sum(D(m["date"]).weekday() >= 5 for m in CM.values()))

# ---- Requirement 6 ------------------------------------------------------------------------------------------
hdr("R6 sampling")
tot_c = defaultdict(float)
for r in RF.values():
    tot_c[r["cust"]] += r["amt"]
key = [k for k, r in RF.items() if r["amt"] >= 5000 or tot_c[r["cust"]] > 10000]
rest = [k for k in RF if k not in key]
dev = [k for k in rest if RF[k] in before]
print("key items", len(key), r2(sum(RF[k]["amt"] for k in key)), sorted(RF[k]["num"] for k in key), "| remainder", len(rest), r2(sum(RF[k]["amt"] for k in rest)),
      "| deviations in remainder", len(dev), f"({len(dev)/len(rest)*100:.1f}%)", "key", sum(1 for k in key if RF[k] in before))
print("UDL n=59", [round(beta.ppf(0.95, k + 1, 59 - k) * 100, 2) for k in range(4)])
hg = hypergeom(len(rest), len(dev), 59)
print("sample of 59 from the remainder: mean", round(hg.mean(), 1), "P(X<=9)", round(hg.cdf(9), 3), "P(X<=19)", round(hg.cdf(19), 3),
      "UDL at 10/14/19", [round(beta.ppf(0.95, k + 1, 59 - k) * 100, 1) for k in (10, 14, 19)])

# ---- Requirement 7 ------------------------------------------------------------------------------------------
hdr("R7 substantive and lapping tests")
cl_rows = q("""SELECT l.CreditMemoLineID, l.Quantity, l.UnitPrice, l.Discount, l.LineTotal, srl.QuantityReturned, sl.QuantityShipped, sil.UnitPrice, sil.Discount,
    sil.SalesInvoiceID, cm.OriginalSalesInvoiceID FROM CreditMemoLine l JOIN SalesReturnLine srl ON srl.SalesReturnLineID = l.SalesReturnLineID
    JOIN ShipmentLine sl ON sl.ShipmentLineID = srl.ShipmentLineID JOIN CreditMemo cm ON cm.CreditMemoID = l.CreditMemoID
    LEFT JOIN SalesInvoiceLine sil ON sil.ShipmentLineID = sl.ShipmentLineID""")
print("credit lines traced", len(cl_rows), "| quantity > shipped", sum(r[1] > r[6] + 1e-9 for r in cl_rows), "| price or discount differs", sum(abs(r[2] - r[7]) > 0.004 or abs(r[3] - r[8]) > 1e-9 for r in cl_rows),
      "| invoice differs", sum(r[9] != r[10] for r in cl_rows), "| line total off", [r[0] for r in cl_rows if abs(r[4] - round(r[1] * r[2] * (1 - r[3]), 2)) > 0.004])
print("shipment lines returned twice", one("SELECT COUNT(*) FROM (SELECT ShipmentLineID FROM SalesReturnLine GROUP BY 1 HAVING COUNT(*) > 1)")[0],
      "| credits per invoice", one("SELECT COUNT(*), COUNT(DISTINCT OriginalSalesInvoiceID) FROM CreditMemo"))
sub_ok = one("SELECT COUNT(*) FROM CreditMemo cm WHERE ABS(cm.SubTotal - (SELECT SUM(LineTotal) FROM CreditMemoLine l WHERE l.CreditMemoID = cm.CreditMemoID)) < 0.005")[0]
tax_ok = sum(1 for m in CM.values() if abs(m["tax"] - round((m["sub"] + m["freight"]) * 0.065, 2)) < 0.011)
tax_sub = sum(1 for m in CM.values() if abs(m["tax"] - round(m["sub"] * 0.065, 2)) > 0.011)
print("SubTotal = lines", sub_ok, "| tax = 6.5% of subtotal + freight", tax_ok, "| a test on SubTotal alone flags", tax_sub,
      "| freight credit > invoice freight", sum(m["freight"] > INV[m["inv"]]["freight"] + 0.005 for m in CM.values()),
      "| credit > invoice", sum(m["gt"] > INV[m["inv"]]["gt"] + 0.005 for m in CM.values()))
dmg = q("""SELECT substr(sr.ReturnDate, 1, 4), sr.ReasonCode, ROUND(SUM(srl.ExtendedStandardCost), 2) FROM SalesReturnLine srl JOIN SalesReturn sr
    ON sr.SalesReturnID = srl.SalesReturnID WHERE sr.ReasonCode IN ('Damaged', 'Quality Concern') GROUP BY 1, 2""")
print("restocked at full standard cost", dmg, "| Damaged total", r2(sum(r[2] for r in dmg if r[1] == "Damaged")), "both", r2(sum(r[2] for r in dmg)))
other_cust = sum(1 for i, v in APPS.items() for a in v if RCPT[a[3]]["cust"] != INV[i]["cust"])
dep_lag = [(D(r["dep"]) - D(r["date"])).days for r in RCPT.values() if r["dep"]]
app_lag = [(D(a[0]) - max(D(RCPT[a[3]]["date"]), D(INV[i]["date"]))).days for i, v in APPS.items() for a in v]
applied = defaultdict(float)
for i, v in APPS.items():
    for a in v:
        applied[a[3]] += a[1]
early_r = sorted({a[3] for i, v in APPS.items() for a in v if RCPT[a[3]]["date"] < INV[i]["date"]})
print("applications to another customer's invoice", other_cust, "| deposit lag", min(dep_lag), max(dep_lag), "| application lag", min(app_lag), max(app_lag),
      "| receipts not fully applied", sum(1 for k, r in RCPT.items() if abs(applied[k] - r["amt"]) > 0.005),
      "| receipts applied to invoices dated after them", len(early_r), r2(sum(a[1] for i, v in APPS.items() for a in v if RCPT[a[3]]["date"] < INV[i]["date"])), "| refs", Counter(r["ref"][:3] for r in RCPT.values() if r["ref"]))
big = [k for k in RF if RF[k]["num"] == "RF-2025-000097"][0]; r = RF[big]; m = CM[r["cm"]]; inv = INV[m["inv"]]
print("timeline", r["num"], r["date"], D(r["date"]).strftime("%A"), r["amt"], r["method"], EMP[r["appr"]]["title"], "cleared", r["cleared"])
print("  credit", m["num"], m["date"], m["gt"], EMP[m["appr"]]["title"], EMP[m["appr"]]["limit"], "| largest credit?", m["gt"] == max(x["gt"] for x in CM.values()))
print("  return", SR[m["ret"]]["num"], SR[m["ret"]]["date"], SR[m["ret"]]["reason"], EMP[SR[m["ret"]]["recv"]]["title"],
      q("""SELECT i.ItemCode, srl.QuantityReturned, sl.QuantityShipped FROM SalesReturnLine srl JOIN ShipmentLine sl ON sl.ShipmentLineID = srl.ShipmentLineID
          JOIN Item i ON i.ItemID = srl.ItemID WHERE srl.SalesReturnID = ?""", (m["ret"],)))
print("  invoice", inv["num"], inv["date"], inv["gt"], "due", inv["due"], "| shipments", q("""SELECT DISTINCT s.ShipmentNumber, s.ShipmentDate, s.DeliveryDate, s.ShippedBy
    FROM SalesInvoiceLine sil JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE sil.SalesInvoiceID = ?""", (m["inv"],)))
for a in sorted(APPS[m["inv"]]):
    rc = RCPT[a[3]]
    print("  receipt", rc["num"], rc["date"], rc["method"], rc["amt"], "applied", a[0], a[1], "recorded by", EMP[rc["rec"]]["title"], rc["rec"], "applied by", EMP[a[2]]["title"], a[2],
          "| credit approver", m["appr"])
print("  clawbacks", [(a[0], a[6]) for a in adj if a[2] == r["cm"]], "rep", {EMP[x[0]]["title"] for x in q("SELECT SalesRepEmployeeID FROM SalesCommissionAdjustment WHERE CreditMemoID = ?", (r["cm"],))})

# ---- Requirement 10 -----------------------------------------------------------------------------------------
hdr("R10 register additions")
popc = {y: sum(1 for x in CM.values() if x["date"][:4] == y) for y in YEARS}
popr = {y: sum(1 for x in RF.values() if x["date"][:4] == y) for y in YEARS}
for name, rows, f, pop in (("CM AboveLimit", cm_above, lambda x: x["date"], popc), ("CM CashAndCredit", cash_credit, lambda x: x["date"], popc),
                           ("RF AboveLimit", rf_above, lambda x: x["date"], popr), ("RF BeforePayment", before, lambda x: x["date"], popr)):
    n = {y: sum(1 for x in rows if f(x)[:4] == y) for y in YEARS}
    print(f"  {name}: {len(rows)} {n} per 1,000 " + " / ".join(f"{n[y]/pop[y]*1000:.1f}" for y in YEARS) + f" three-year {len(rows)/sum(pop.values())*1000:.1f}")
print("  populations credits", popc, "refunds", popr, "| register 151 +", len(cm_above) + len(cash_credit) + len(rf_above) + len(before))
print("  last dates: credits", max(x["date"] for x in CM.values()), "refunds", max(x["date"] for x in RF.values()))
