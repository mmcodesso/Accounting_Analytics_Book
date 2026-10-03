"""Read-only SQL twins for Chapter 17 ("Financial Statements for a Lender").
Every value the chapter's instructor notes state is computed here."""
import sqlite3
from collections import defaultdict
from datetime import date, timedelta

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, db_uri  # noqa: E402
c = sqlite3.connect(db_uri(), uri=True)
q = lambda s, p=(): c.execute(s, p).fetchall()
one = lambda s, p=(): c.execute(s, p).fetchone()
r2 = lambda x: round(x + 0.0, 2)

CLOSES = [r[0] for r in q("SELECT EntryNumber FROM JournalEntry WHERE EntryType LIKE 'Year-End Close%'")]
CL = "(" + ",".join(f"'{v}'" for v in CLOSES) + ")"
NOCLOSE = f"NOT (g.SourceDocumentType='JournalEntry' AND g.VoucherNumber IN {CL})"
YEARS = [2024, 2025, 2026]
YE = {y: f"{y}-12-31" for y in YEARS}
ACC = {str(r[0]): r[1:] for r in q("SELECT AccountNumber, AccountID, AccountName, AccountType, AccountSubType, NormalBalance, IsActive FROM Account")}
AID = {k: v[0] for k, v in ACC.items()}
AID.update({int(k): v for k, v in list(AID.items())})
ACC.update({int(k): v for k, v in list(ACC.items())})


def hdr(t):
    print(f"\n=== {t}")


def tb(asof):
    """Debit-positive balance per account number at asof; closes excluded only when dated on asof."""
    rows = q(f"""SELECT a.AccountNumber, ROUND(SUM(g.Debit-g.Credit),2), COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
        WHERE g.PostingDate<=? AND NOT (g.SourceDocumentType='JournalEntry' AND g.VoucherNumber IN {CL} AND g.PostingDate=?)
        GROUP BY 1""", (asof, asof))
    return {str(r[0]): r[1] for r in rows}


def flow(accts, d0, d1):
    ids = ",".join(str(AID[a]) for a in accts)
    return one(f"""SELECT ROUND(COALESCE(SUM(g.Debit-g.Credit),0),2) FROM GLEntry g WHERE g.AccountID IN ({ids})
        AND g.PostingDate BETWEEN ? AND ? AND {NOCLOSE}""", (d0, d1))[0]


def by_sub(t, subs):
    return r2(sum(v for k, v in t.items() if ACC[k][3] in subs))


# ---- Requirement 1 ------------------------------------------------------------------------
hdr("R1 trial balances")
TB = {y: tb(YE[y]) for y in YEARS}
for y in YEARS:
    t = TB[y]
    deb = r2(sum(v for v in t.values() if v > 0)); cre = r2(-sum(v for v in t.values() if v < 0))
    print(y, "accounts", len(t), "at zero", sum(1 for v in t.values() if abs(v) < 0.005), "debits", deb, "credits", cre)
print("closes", CLOSES)
NI = {}
for y in YEARS:
    rev = flow([k for k in ACC if ACC[k][2] in ("Revenue", "Expense") and ACC[k][3] != "Header"], f"{y}-01-01", YE[y])
    NI[y] = r2(-rev)
    re_close = one(f"""SELECT ROUND(SUM(g.Credit-g.Debit),2) FROM GLEntry g JOIN JournalEntry je ON je.EntryNumber=g.VoucherNumber
        AND g.SourceDocumentType='JournalEntry' WHERE je.EntryType LIKE 'Year-End Close - Income Summary%' AND g.AccountID=?
        AND g.PostingDate=?""", (AID["3030"], YE[y]))[0]
    print(y, "net income", NI[y], "| close to RE", re_close)
for y in YEARS:
    t = TB[y]
    print(y, "total assets", by_sub(t, ("Current Asset", "Contra Current Asset", "Fixed Asset", "Contra Fixed Asset", "Noncurrent Asset")),
          "current assets", by_sub(t, ("Current Asset", "Contra Current Asset")),
          "current liabilities", -by_sub(t, ("Current Liability",)), "notes 2110", -t.get("2110", 0),
          "RE", -t.get("3030", 0), "stock", -t.get("3010", 0))
IS = {}
for y in (2025, 2026):
    d0, d1 = f"{y}-01-01", YE[y]
    sub = lambda s: flow([k for k in ACC if ACC[k][3] == s], d0, d1)
    opr = -sub("Operating Revenue"); ret = sub("Contra Revenue"); cogs = sub("COGS"); opx = sub("Operating Expense")
    intr = flow(["7030"], d0, d1); loss = flow(["7020"], d0, d1)
    IS[y] = dict(opr=opr, ret=ret, cogs=cogs, opx=opx, intr=intr, loss=loss)
    print(y, "oper rev", opr, "returns", ret, "net rev", r2(opr - ret), "COGS", cogs, "GM", r2(opr - ret - cogs), "opex", opx,
          "op inc", r2(opr - ret - cogs - opx), "interest", intr, "loss", loss, "NI", r2(opr - ret - cogs - opx - intr - loss))
never = q("""SELECT AccountNumber, AccountName, IsActive FROM Account a WHERE AccountSubType<>'Header'
    AND NOT EXISTS (SELECT 1 FROM GLEntry g WHERE g.AccountID=a.AccountID) ORDER BY 1""")
print("never posted", len(never), "active", [r[0] for r in never if r[2] == 1], "inactive", [r[0] for r in never if r[2] == 0])
print("tax accounts", q("SELECT AccountNumber, AccountName FROM Account WHERE AccountName LIKE '%tax%'"))

# ---- Requirement 2 ------------------------------------------------------------------------
hdr("R2 changes above materiality, opening-entry balances")
MAT = {2026: r2(NI[2026] * 0.05), 2025: r2(NI[2025] * 0.05)}
print("materiality", MAT)
pl = {k for k in ACC if ACC[k][2] in ("Revenue", "Expense")}
chg = []
for k in set(TB[2025]) | set(TB[2026]):
    if k in pl:
        d = r2(flow([k], "2026-01-01", "2026-12-31") - flow([k], "2025-01-01", "2025-12-31"))
    else:
        d = r2(TB[2026].get(k, 0) - TB[2025].get(k, 0))
    chg.append((abs(d), k, d))
for a, k, d in sorted(chg, reverse=True)[:11]:
    print(" ", k, ACC[k][1], d, "ABOVE" if a > MAT[2026] else "")
OPEN = one("SELECT JournalEntryID FROM JournalEntry WHERE EntryType='Opening'")[0]
for r in q(f"""SELECT a.AccountNumber, ROUND(SUM(g.Debit-g.Credit),2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
    WHERE g.SourceDocumentType='JournalEntry' AND g.SourceDocumentID={OPEN} GROUP BY 1 ORDER BY 1"""):
    n = one("SELECT COUNT(*) FROM GLEntry WHERE AccountID=?", (AID[r[0]],))[0]
    print("  opening", r[0], ACC[r[0]][1], r[1], "| postings", n, "| YE2026", TB[2026].get(str(r[0])))
print("  2030 non-opening net", one(f"SELECT ROUND(SUM(Debit-Credit),2) FROM GLEntry WHERE AccountID={AID['2030']} AND NOT (SourceDocumentType='JournalEntry' AND SourceDocumentID={OPEN})")[0])

# ---- Requirement 3 ------------------------------------------------------------------------
hdr("R3 accrued expenses 2040")
A2040 = AID["2040"]
accr = q(f"""SELECT je.JournalEntryID, je.EntryNumber, je.PostingDate, ROUND(SUM(g.Credit),2),
    (SELECT a.AccountNumber FROM GLEntry g2 JOIN Account a ON a.AccountID=g2.AccountID WHERE g2.SourceDocumentType='JournalEntry'
      AND g2.SourceDocumentID=je.JournalEntryID AND g2.Debit>0 LIMIT 1)
    FROM JournalEntry je JOIN GLEntry g ON g.SourceDocumentType='JournalEntry' AND g.SourceDocumentID=je.JournalEntryID AND g.AccountID={A2040}
    WHERE je.EntryType='Accrual' GROUP BY 1""")
print("accruals", len(accr), r2(sum(r[3] for r in accr)))
# clearing by invoices (ledger debits to 2040 on the invoice lines that reference the accrual) and by adjustments
inv_clear = q(f"""SELECT pil.AccrualJournalEntryID, g.PostingDate, g.Debit, pil.PILineID, g.Credit FROM PurchaseInvoiceLine pil
    JOIN GLEntry g ON g.SourceDocumentType='PurchaseInvoice' AND g.SourceLineID=pil.PILineID AND g.AccountID={A2040}
    WHERE pil.AccrualJournalEntryID IS NOT NULL""")
print("invoice lines clearing", len(inv_clear), len({r[3] for r in inv_clear}), r2(sum(r[2] for r in inv_clear)),
      "| accruals with a line", len({r[0] for r in inv_clear}),
      "| lines per accrual max", max(defaultdict(int, {}) or [1]))
lines_per = defaultdict(int)
for r in inv_clear:
    lines_per[r[0]] += 1
print("  max lines per accrual", max(lines_per.values()), "| null key lines", one("SELECT COUNT(*) FROM PurchaseInvoiceLine WHERE AccrualJournalEntryID IS NULL")[0])
adj = q(f"""SELECT je.ReversesJournalEntryID, je.PostingDate, ROUND(SUM(g.Debit),2), je.EntryNumber, je.Description FROM JournalEntry je
    JOIN GLEntry g ON g.SourceDocumentType='JournalEntry' AND g.SourceDocumentID=je.JournalEntryID AND g.AccountID={A2040}
    WHERE je.EntryType='Accrual Adjustment' GROUP BY je.JournalEntryID""")
print("adjustments", len(adj), "distinct targets", len({r[0] for r in adj}), r2(sum(r[2] for r in adj)))
# excess over the accrual charged to expense, by invoice year
exc = q(f"""SELECT strftime('%Y', g.PostingDate), COUNT(DISTINCT pil.PILineID), ROUND(SUM(g.Debit),2) FROM PurchaseInvoiceLine pil
    JOIN GLEntry g ON g.SourceDocumentType='PurchaseInvoice' AND g.SourceLineID=pil.PILineID AND g.AccountID<>{A2040} AND g.Debit>0
    JOIN Account a ON a.AccountID=g.AccountID AND a.AccountType='Expense'
    WHERE pil.AccrualJournalEntryID IS NOT NULL GROUP BY 1""")
print("excess to expense by year", exc)
clear = defaultdict(list)
for r in inv_clear:
    clear[r[0]].append((r[1], r[2], "inv"))
for r in adj:
    clear[r[0]].append((r[1], r[2], "adj"))
lags = sorted((date.fromisoformat(min(d for d, _, k in clear[a[0]] if k == "inv")) - date.fromisoformat(a[2])).days
              for a in accr if any(k == "inv" for _, _, k in clear[a[0]]))
print("clearing lag min/median/max", lags[0], lags[len(lags) // 2], lags[-1], "| at 62 days", lags.count(62))
ship_cr = lambda asof: one(f"SELECT ROUND(SUM(Credit),2) FROM GLEntry WHERE AccountID={A2040} AND SourceDocumentType='Shipment' AND PostingDate<=?", (asof,))[0]
settle = lambda asof: one(f"""SELECT ROUND(COALESCE(SUM(g.Debit),0),2) FROM GLEntry g JOIN JournalEntry je ON je.JournalEntryID=g.SourceDocumentID
    AND g.SourceDocumentType='JournalEntry' WHERE g.AccountID={A2040} AND je.EntryType='Freight Settlement' AND g.PostingDate<=?""", (asof,))[0]
STALE = {}
for y in YEARS:
    asof = YE[y]; ad = date.fromisoformat(asof)
    young = old = 0.0; nold = 0; old_items = []
    for a in accr:
        if a[2] > asof:
            continue
        cl = sum(v for d, v, _ in clear[a[0]] if d <= asof)
        open_ = r2(a[3] - cl)
        if open_ <= 0.004:
            continue
        age = (ad - date.fromisoformat(a[2])).days
        if age > 62:
            old += open_; nold += 1; old_items.append((a[1], a[2], a[4], open_))
        else:
            young += open_
    fr = r2(ship_cr(asof) - settle(asof))
    dec = one(f"SELECT ROUND(SUM(Credit),2) FROM GLEntry WHERE AccountID={A2040} AND SourceDocumentType='Shipment' AND PostingDate BETWEEN ? AND ?", (f"{y}-12-01", asof))[0]
    gl = -TB[y]["2040"]
    STALE[y] = r2(old)
    print(y, "freight", fr, "(Dec", dec, "excess", r2(fr - dec), ") young", r2(young), "old", r2(old), nold, "| sum", r2(85000 + fr + young + old), "GL", gl)
    if y == 2026:
        by_year = defaultdict(float); by_acct = defaultdict(float)
        for e, d, acct, v in old_items:
            by_year[d[:4]] += v; by_acct[acct] += v
        print("  old by year", {k: r2(v) for k, v in sorted(by_year.items())}, "by account", {k: r2(v) for k, v in sorted(by_acct.items())})
        never_inv = [i for i in old_items if not any(k == "inv" for _, _, k in clear[[a for a in accr if a[1] == i[0]][0][0]])]
        print("  never invoiced", len(never_inv), "| partly cleared by adjustment only",
              [i[0] for i in old_items if i not in never_inv])
print("partial cleanup adjustments", [(r[3], r[4][:60]) for r in adj if "artial" in (r[4] or "")][:5])
print("settlements", one("SELECT COUNT(*), ROUND(SUM(TotalAmount),2) FROM JournalEntry WHERE EntryType='Freight Settlement'"),
      "| shipment 2040 credits = 5050 debits?", ship_cr("2027-12-31"), flow(["5050"], "2024-01-01", "2027-12-31"))
# young items of YE2024 and YE2025 never invoiced
for y in (2024, 2025):
    asof = YE[y]; ad = date.fromisoformat(asof); ni = []
    for a in accr:
        if a[2] <= asof and 0 <= (ad - date.fromisoformat(a[2])).days <= 62 and not any(k == "inv" for _, _, k in clear[a[0]]):
            open_ = r2(a[3] - sum(v for d, v, _ in clear[a[0]] if d <= asof))
            if open_ > 0:
                ni.append((a[1], open_))
    print(" young at", y, "never invoiced", ni, r2(sum(v for _, v in ni)))

# ---- Requirement 4 ------------------------------------------------------------------------
hdr("R4 cutoff: revenue")
inv = q("""SELECT si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate, si.SubTotal, si.TaxAmount, si.FreightAmount, c.CustomerSegment,
    (SELECT MAX(s.DeliveryDate) FROM SalesInvoiceLine sil JOIN ShipmentLine sl ON sl.ShipmentLineID=sil.ShipmentLineID
       JOIN Shipment s ON s.ShipmentID=sl.ShipmentID WHERE sil.SalesInvoiceID=si.SalesInvoiceID),
    (SELECT MIN(g.PostingDate) FROM GLEntry g WHERE g.SourceDocumentType='SalesInvoice' AND g.SourceDocumentID=si.SalesInvoiceID)
    FROM SalesInvoice si JOIN Customer c ON c.CustomerID=si.CustomerID""")
CUT = {}
for y in (2024, 2025):
    xs = [r for r in inv if r[7] and r[7][:4] == str(y) and r[8][:4] == str(y + 1)]
    seg = defaultdict(float)
    for r in xs:
        seg[r[6]] += r[3]
    CUT[y] = r2(sum(r[3] for r in xs))
    print(y, "delivered, posted next year:", len(xs), CUT[y], "tax", r2(sum(r[4] for r in xs)), "freight", r2(sum(r[5] for r in xs)),
          {k: r2(v) for k, v in seg.items()}, [r[1] for r in xs if r[1].startswith("SI-2026-01374")])
    grp = q(f"""SELECT i.ItemGroup, ROUND(SUM(sil.LineTotal),2) FROM SalesInvoiceLine sil JOIN Item i ON i.ItemID=sil.ItemID
        WHERE sil.SalesInvoiceID IN ({','.join(str(r[0]) for r in xs)}) GROUP BY 1""")
    print("   by group", grp)
uninv = q("""SELECT sl.ShipmentLineID, s.ShipmentDate, s.DeliveryDate, sol.LineTotal, sl.ExtendedStandardCost, i.ItemGroup, c.CustomerSegment
    FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID=sl.ShipmentID JOIN SalesOrderLine sol ON sol.SalesOrderLineID=sl.SalesOrderLineID
    JOIN Item i ON i.ItemID=sl.ItemID JOIN SalesOrder so ON so.SalesOrderID=s.SalesOrderID JOIN Customer c ON c.CustomerID=so.CustomerID
    WHERE NOT EXISTS (SELECT 1 FROM SalesInvoiceLine sil WHERE sil.ShipmentLineID=sl.ShipmentLineID)""")
print("never invoiced lines", len(uninv), "dates", min(r[1] for r in uninv), max(r[1] for r in uninv),
      "| delivered", min(r[2] for r in uninv), max(r[2] for r in uninv))
# order-price value: quantity shipped at order price
uninv_val = q("""SELECT ROUND(SUM(ROUND(sl.QuantityShipped*sol.UnitPrice*(1-sol.Discount),2)),2), ROUND(SUM(sl.ExtendedStandardCost),2)
    FROM ShipmentLine sl JOIN SalesOrderLine sol ON sol.SalesOrderLineID=sl.SalesOrderLineID
    WHERE NOT EXISTS (SELECT 1 FROM SalesInvoiceLine sil WHERE sil.ShipmentLineID=sl.ShipmentLineID)""")[0]
print("  value at order price", uninv_val[0], "std cost", uninv_val[1], "| sum of order LineTotal", r2(sum(r[3] for r in uninv)))
seg = defaultdict(float); grp = defaultdict(float)
for r in q("""SELECT ROUND(sl.QuantityShipped*sol.UnitPrice*(1-sol.Discount),2), c.CustomerSegment, i.ItemGroup
    FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID=sl.ShipmentID JOIN SalesOrderLine sol ON sol.SalesOrderLineID=sl.SalesOrderLineID
    JOIN Item i ON i.ItemID=sl.ItemID JOIN SalesOrder so ON so.SalesOrderID=s.SalesOrderID JOIN Customer c ON c.CustomerID=so.CustomerID
    WHERE NOT EXISTS (SELECT 1 FROM SalesInvoiceLine sil WHERE sil.ShipmentLineID=sl.ShipmentLineID)"""):
    seg[r[1]] += r[0]; grp[r[2]] += r[0]
print("  by segment", {k: r2(v) for k, v in seg.items()}, "by group", {k: r2(v) for k, v in grp.items()})
CUT[2026] = uninv_val[0]

hdr("R4 cutoff: payroll")
wc = one("SELECT MIN(WorkCenterID) FROM WorkCenterCalendar")[0]
wdays = lambda d0, d1: one("SELECT COUNT(*) FROM WorkCenterCalendar WHERE WorkCenterID=? AND IsWorkingDay=1 AND CalendarDate BETWEEN ? AND ?", (wc, d0, d1))[0]
print("calendar range", one("SELECT MIN(CalendarDate), MAX(CalendarDate) FROM WorkCenterCalendar"))
print("same working days in every work center?", q("""SELECT COUNT(DISTINCT n) FROM (SELECT WorkCenterID, COUNT(*) n FROM WorkCenterCalendar
    WHERE IsWorkingDay=1 AND CalendarDate BETWEEN '2024-01-01' AND '2026-12-31' GROUP BY 1)"""))
per = {r[0]: r[1:] for r in q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate, PayDate, Status FROM PayrollPeriod")}
cost = lambda pn: one("""SELECT ROUND(SUM(pr.GrossPay+pr.EmployerPayrollTax+pr.EmployerBenefits),2), ROUND(SUM(pr.GrossPay),2),
    ROUND(SUM(pr.EmployerPayrollTax),2), ROUND(SUM(pr.EmployerBenefits),2),
    ROUND(SUM(CASE WHEN pr.CostCenterID=4 THEN pr.GrossPay+pr.EmployerPayrollTax+pr.EmployerBenefits ELSE 0 END),2)
    FROM PayrollRegister pr WHERE pr.PayrollPeriodID=?""", (pn,))
PAY = {}
for y, full, cross in ((2024, 26, 27), (2025, 52, 53)):
    for pn in (full, cross):
        print(" period", pn, per[pn], cost(pn), "wd", wdays(per[pn][0], per[pn][1]), "in year", wdays(per[pn][0], YE[y]))
    f = cost(full); x = cost(cross); share = wdays(per[cross][0], YE[y]) / wdays(per[cross][0], per[cross][1])
    tot = [f[i] + x[i] * share for i in range(5)]
    PAY[y] = dict(total=r2(tot[0]), gross=r2(tot[1]), tax=r2(tot[2]), ben=r2(tot[3]), mfg=r2(tot[4]), other=r2(tot[0] - tot[4]))
    print(y, PAY[y], "| crossing part", r2(x[0] * share))
c70 = [cost(p) for p in range(70, 78)]
wd = wdays(per[70][0], per[77][1]); left = wdays("2026-12-14", "2026-12-31")
tot = [sum(cc[i] for cc in c70) for i in range(5)]
PAY[2026] = dict(total=r2(tot[0] / wd * left), gross=r2(tot[1] / wd * left), tax=r2(tot[2] / wd * left), ben=r2(tot[3] / wd * left),
                 mfg=r2(tot[4] / wd * left), other=r2((tot[0] - tot[4]) / wd * left))
print(2026, "periods 70-77", r2(tot[0]), "over", wd, "days", r2(tot[0] / wd), "a day x", left, "=", PAY[2026])
print("periods 78-79", per[78], per[79])

hdr("R4 cutoff: interest")
for r in q("SELECT DebtAgreementID, AgreementNumber, FixedAssetID, OriginationDate, PrincipalAmount, AnnualInterestRate, TermMonths, PaymentStartDate, ScheduledPaymentAmount, Status FROM DebtAgreement"):
    print(" ", r)
for y in YEARS:
    rows = q("""SELECT DebtAgreementID, PaymentSequence, PaymentDate, BeginningPrincipal, InterestAmount, PrincipalAmount, EndingPrincipal, Status
        FROM DebtScheduleLine WHERE PaymentDate BETWEEN ? AND ? ORDER BY 1, 3""", (f"{y}-12-01", f"{y + 1}-02-28"))
    for r in rows:
        print(" ", y, r)
print("2080 postings", one(f"SELECT COUNT(*) FROM GLEntry WHERE AccountID={AID['2080']}")[0])

# ---- Requirement 5 ------------------------------------------------------------------------
hdr("R5 adjustments")
INT = {2024: 1838.58, 2025: 1369.27, 2026: 2007.26}   # confirmed above from the schedules
A = {
    "A1": {"re": -PAY[2024]["total"], 2025: -(PAY[2025]["total"] - PAY[2024]["total"]), 2026: -(PAY[2026]["total"] - PAY[2025]["total"])},
    "A2": {"re": CUT[2024], 2025: CUT[2025] - CUT[2024], 2026: CUT[2026] - CUT[2025]},
    "A3": {"re": STALE[2024], 2025: STALE[2025] - STALE[2024], 2026: STALE[2026] - STALE[2025]},
    "A4": {"re": -INT[2024], 2025: INT[2024] - INT[2025], 2026: INT[2025] - INT[2026]},
}
for k, v in A.items():
    print(k, {kk: r2(vv) for kk, vv in v.items()})
tot = {kk: r2(sum(v[kk] for v in A.values())) for kk in ("re", 2025, 2026)}
print("total", tot, "| adjusted NI 2025", r2(NI[2025] + tot[2025]), "2026", r2(NI[2026] + tot[2026]))
print("A1 split 2025 COGS", r2(PAY[2025]["mfg"] - PAY[2024]["mfg"]), "opex", r2(PAY[2025]["other"] - PAY[2024]["other"]),
      "| 2026 COGS", r2(PAY[2026]["mfg"] - PAY[2025]["mfg"]), "opex", r2(PAY[2026]["other"] - PAY[2025]["other"]))
ADJNI = {2025: r2(NI[2025] + tot[2025]), 2026: r2(NI[2026] + tot[2026])}
print("materiality on adjusted", r2(ADJNI[2026] * 0.05), "| effect / materiality", round(tot[2026] / MAT[2026], 3))
# A2 by revenue account in 2026: the never-invoiced lines (by item group) less the 2025 deliveries invoiced in 2026
acct_grp = {"Furniture": "4010", "Lighting": "4020", "Textiles": "4030", "Accessories": "4040"}
xs25 = [r for r in inv if r[7] and r[7][:4] == "2025" and r[8][:4] == "2026"]
g25 = dict(q(f"""SELECT i.ItemGroup, ROUND(SUM(sil.LineTotal),2) FROM SalesInvoiceLine sil JOIN Item i ON i.ItemID=sil.ItemID
    WHERE sil.SalesInvoiceID IN ({','.join(str(r[0]) for r in xs25)}) GROUP BY 1"""))
print("A2 2026 by account", {acct_grp[g]: r2(grp.get(g, 0) - g25.get(g, 0)) for g in acct_grp})
# reclasses
for y in (2025, 2026):
    cur = one("SELECT ROUND(SUM(dsl.PrincipalAmount),2) FROM DebtScheduleLine dsl JOIN DebtAgreement da ON da.DebtAgreementID=dsl.DebtAgreementID WHERE da.OriginationDate<=? AND PaymentDate BETWEEN ? AND ?", (YE[y], f"{y + 1}-01-01", f"{y + 1}-12-31"))[0]
    print("R1 current portion at", y, cur, "| 1090", TB[y].get("1090"), "1046", TB[y].get("1046"))
# passed items
buckets = [(0, 0.005), (30, 0.02), (60, 0.05), (90, 0.15), (10 ** 6, 0.40)]
print("P1 allowance at YE2026 (Chapter 8) 34,106.25; see ch08 notes")
dmg = q("""SELECT strftime('%Y', sr.ReturnDate), sr.ReasonCode, ROUND(SUM(srl.ExtendedStandardCost),2) FROM SalesReturn sr
    JOIN SalesReturnLine srl ON srl.SalesReturnID=sr.SalesReturnID GROUP BY 1, 2 ORDER BY 1, 2""")
print("returns at standard cost by year and reason", dmg)
ret_gl = q(f"""SELECT strftime('%Y', PostingDate), ROUND(SUM(Debit),2) FROM GLEntry WHERE AccountID={AID['1040']} AND SourceDocumentType='SalesReturn' GROUP BY 1""")
print("1040 debits from returns by year", ret_gl)
# expected returns: returns in year y+1 of deliveries in year y
xr = q("""SELECT strftime('%Y', sr.ReturnDate), strftime('%Y', s.DeliveryDate), COUNT(DISTINCT sr.SalesReturnID),
    ROUND(SUM(cm.SubTotal),2) FROM SalesReturn sr JOIN CreditMemo cm ON cm.SalesReturnID=sr.SalesReturnID
    JOIN (SELECT SalesReturnID, MIN(ShipmentLineID) sl FROM SalesReturnLine GROUP BY 1) x ON x.SalesReturnID=sr.SalesReturnID
    JOIN ShipmentLine sl ON sl.ShipmentLineID=x.sl JOIN Shipment s ON s.ShipmentID=sl.ShipmentID
    WHERE strftime('%Y', sr.ReturnDate)<>strftime('%Y', s.DeliveryDate) GROUP BY 1, 2""")
print("returns crossing a year-end (by delivery year)", xr)
xrc = q("""SELECT strftime('%Y', sr.ReturnDate), ROUND(SUM(srl.ExtendedStandardCost),2) FROM SalesReturn sr
    JOIN SalesReturnLine srl ON srl.SalesReturnID=sr.SalesReturnID JOIN ShipmentLine sl ON sl.ShipmentLineID=srl.ShipmentLineID
    JOIN Shipment s ON s.ShipmentID=sl.ShipmentID WHERE strftime('%Y', sr.ReturnDate)<>strftime('%Y', s.DeliveryDate) GROUP BY 1""")
print("  their standard cost", xrc)

# ---- Requirement 6 ------------------------------------------------------------------------
hdr("R6 statements")
for y in (2025, 2026):
    t = TB[y]; g = lambda k: t.get(k, 0)
    pay, cut, st, it = PAY[y]["total"], CUT[y], STALE[y], INT[y]
    cur_port = one("SELECT ROUND(SUM(dsl.PrincipalAmount),2) FROM DebtScheduleLine dsl JOIN DebtAgreement da ON da.DebtAgreementID=dsl.DebtAgreementID WHERE da.OriginationDate<=? AND PaymentDate BETWEEN ? AND ?", (YE[y], f"{y + 1}-01-01", f"{y + 1}-12-31"))[0]
    cash = g("1010"); recv = r2(g("1020") + g("1030") + cut); inv_ = r2(g("1040") + g("1045") + g("1046") + g("1090")); pre = g("1050")
    ca = r2(cash + recv + inv_ + pre)
    ppe = r2(sum(g(k) for k in ("1110", "1120", "1130", "1185", "1150", "1160", "1170", "1186")))
    ap, grni = -g("2010"), -g("2020")
    payroll = r2(-(g("2030") + g("2031") + g("2032") + g("2033")) + pay)
    comm = -g("2034"); accexp = r2(-g("2040") - st)
    accrued = r2(payroll + comm + accexp + it)
    stax, cred = -g("2050"), -g("2060")
    cl = r2(ap + grni + accrued + stax + cred + cur_port)
    notes = -g("2110")
    eq_adj = r2(-pay + cut + st - it)
    re = r2(-g("3030") + NI[y] + eq_adj)
    print(y, "cash", cash, "recv", recv, "inv", inv_, "(FG", g("1040"), "mat", g("1045"), "WIP net", r2(g("1046") + g("1090")), ") prepaid", pre,
          "CA", ca, "PPE", ppe, "TA", r2(ca + ppe))
    print("   AP", ap, "GRNI", grni, "accrued", accrued, "(payroll", payroll, "comm", comm, "acc exp", accexp, "int", it, ") stax", stax,
          "credits", cred, "cur notes", cur_port, "CL", cl, "LT notes", r2(notes - cur_port), "TL", r2(cl + notes - cur_port))
    print("   RE", re, "equity", r2(re + 500000), "L+E", r2(cl + notes - cur_port + re + 500000), "eq adj", eq_adj,
          "| WC", r2(ca - cl), "CR", round(ca / cl, 3), "QR", round((cash + recv) / cl, 3), "cash net of stax", r2(cash - stax))
re0 = -TB[2024]["3030"] if False else None
re_1225 = r2(-tb("2024-12-31").get("3030", 0) + NI[2024])
print("RE at 1/1/2025 as reported", re_1225, "restated", r2(re_1225 + tot["re"]), "| +2025", r2(re_1225 + tot["re"] + ADJNI[2025]),
      "+2026", r2(re_1225 + tot["re"] + ADJNI[2025] + ADJNI[2026]))
print("distributions (3040 postings)", one(f"SELECT COUNT(*) FROM GLEntry WHERE AccountID={AID['3040']}")[0])
for y in (2025, 2026):
    d0, d1 = f"{y}-01-01", YE[y]
    dep = r2(flow(["6130"], d0, d1) + one(f"""SELECT ROUND(SUM(g.Debit),2) FROM GLEntry g JOIN JournalEntry je ON je.JournalEntryID=g.SourceDocumentID
        AND g.SourceDocumentType='JournalEntry' WHERE je.EntryType='Depreciation' AND g.AccountID={AID['1090']} AND g.PostingDate BETWEEN ? AND ?""", (d0, d1))[0])
    intpaid = one(f"""SELECT ROUND(SUM(g.Debit),2) FROM GLEntry g JOIN JournalEntry je ON je.JournalEntryID=g.SourceDocumentID AND g.SourceDocumentType='JournalEntry'
        WHERE je.EntryType='Interest Payment' AND g.AccountID={AID['7030']} AND g.PostingDate BETWEEN ? AND ?""", (d0, d1))[0]
    princ = one("""SELECT ROUND(SUM(PrincipalAmount),2), COUNT(*) FROM DebtScheduleLine dsl JOIN JournalEntry je ON je.JournalEntryID=dsl.JournalEntryID
        WHERE je.PostingDate BETWEEN ? AND ?""", (d0, d1))
    print(y, "depreciation", dep, "interest paid", intpaid, "principal paid", princ, "change in cash", r2(TB[y]["1010"] - tb(f"{y - 1}-12-31")["1010"]))

# ---- Requirement 7 ------------------------------------------------------------------------
hdr("R7 notes")
for r in q("""SELECT AssetCode, AssetCategory, AssetAccountID, InServiceDate, UsefulLifeMonths, OriginalCost, OpeningAccumulatedDepreciation,
    ResidualValue, Status, DisposalDate FROM FixedAsset ORDER BY 1"""):
    print(" ", r)
for r in q("SELECT FixedAssetID, EventType, EventDate, Amount, FinancingType, ProceedsAmount, JournalEntryID, DebtAgreementID FROM FixedAssetEvent ORDER BY EventDate"):
    print(" ", r)
cost_accts = ["1110", "1120", "1130", "1185"]; ad_accts = ["1150", "1160", "1170", "1186"]
for asof in ("2024-12-31", "2025-12-31", "2026-12-31"):
    t = tb(asof)
    print(asof, "cost", r2(sum(t.get(k, 0) for k in cost_accts)), {k: t.get(k, 0) for k in cost_accts},
          "acc dep", r2(-sum(t.get(k, 0) for k in ad_accts)), {k: -t.get(k, 0) for k in ad_accts})
for y in (2025, 2026):
    print(y, "depreciation by contra account", {k: -one(f"""SELECT ROUND(SUM(g.Debit-g.Credit),2) FROM GLEntry g JOIN JournalEntry je
        ON je.JournalEntryID=g.SourceDocumentID AND g.SourceDocumentType='JournalEntry' WHERE je.EntryType='Depreciation' AND g.AccountID=?
        AND g.PostingDate BETWEEN ? AND ?""", (AID[k], f"{y}-01-01", YE[y]))[0] for k in ad_accts},
          "6130", flow(["6130"], f"{y}-01-01", YE[y]), "loss", flow(["7020"], f"{y}-01-01", YE[y]))
for r in q("""SELECT strftime('%Y', PaymentDate), ROUND(SUM(PrincipalAmount),2), ROUND(SUM(InterestAmount),2) FROM DebtScheduleLine
    WHERE PaymentDate>'2026-12-31' GROUP BY 1"""):
    print("  maturities", r)
for y in YEARS:
    print("  notes at", y, one("SELECT ROUND(SUM(PrincipalAmount),2) FROM DebtScheduleLine WHERE PaymentDate>?", (YE[y],))[0], "GL", -TB[y].get("2110", 0))
# revenue on the adjusted ledger basis
for y in (2025, 2026):
    base = {k: -flow([k], f"{y}-01-01", YE[y]) for k in ("4010", "4020", "4030", "4040", "4050", "4080")}
    print(y, "ledger revenue", base)
print("contract balances 2060", {y: -TB[y].get("2060", 0) for y in YEARS}, "1020", {y: TB[y].get("1020") for y in YEARS})
print("issued credit memos open", q("SELECT Status, COUNT(*), ROUND(SUM(GrandTotal),2) FROM CreditMemo GROUP BY 1"))
e = q("""SELECT se.ServiceEngagementID, se.EngagementNumber, se.StartDate, se.EndDate, se.PlannedHours, se.Status,
    (SELECT ROUND(SUM(BilledHours),2) FROM ServiceBillingLine b WHERE b.ServiceEngagementID=se.ServiceEngagementID),
    (SELECT MAX(BillingPeriodEndDate) FROM ServiceBillingLine b WHERE b.ServiceEngagementID=se.ServiceEngagementID)
    FROM ServiceEngagement se WHERE se.ServiceEngagementID=209""")
print("engagement 209", e)
print("open engagements at YE2026", q("SELECT Status, COUNT(*) FROM ServiceEngagement WHERE StartDate<='2026-12-31' AND (EndDate>'2026-12-31' OR EndDate IS NULL) GROUP BY 1"))
print("service billing in Dec 2026", q("SELECT MAX(BillingPeriodEndDate), COUNT(*) FROM ServiceBillingLine WHERE BillingPeriodEndDate>='2026-12-01'"))

# ---- Requirement 8 ------------------------------------------------------------------------
hdr("R8 the 2027 records")
print("GL after 2026", q("SELECT SourceDocumentType, COUNT(*), MIN(PostingDate), MAX(PostingDate) FROM GLEntry WHERE PostingDate>'2026-12-31' GROUP BY 1"))
pays = one("""SELECT COUNT(*), ROUND(SUM(Amount),2) FROM DisbursementPayment WHERE PaymentDate>'2026-12-31'""")
print("2027 payments", pays)
pinv = q("""SELECT pi.PurchaseInvoiceID, pi.ReceivedDate, pi.GrandTotal, SUM(dp.Amount), pi.SupplierID FROM DisbursementPayment dp
    JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID=dp.PurchaseInvoiceID WHERE dp.PaymentDate>'2026-12-31' GROUP BY 1""")
print("  invoices", len(pinv), "suppliers", len({r[4] for r in pinv}), "received range", min(r[1] for r in pinv), max(r[1] for r in pinv),
      "| paid in full", sum(1 for r in pinv if abs(r[2] - r[3]) < 0.005))
print("  same weeks 2026", one("SELECT COUNT(*), ROUND(SUM(Amount),2) FROM DisbursementPayment WHERE PaymentDate BETWEEN '2026-01-01' AND '2026-02-23'"))
print("  payable at YE2026 due Jan-Feb 2027", one("""SELECT ROUND(SUM(pi.GrandTotal - COALESCE((SELECT SUM(dp.Amount) FROM DisbursementPayment dp
    WHERE dp.PurchaseInvoiceID=pi.PurchaseInvoiceID AND dp.PaymentDate<='2026-12-31'),0)),2) FROM PurchaseInvoice pi
    WHERE pi.ReceivedDate<='2026-12-31' AND pi.DueDate BETWEEN '2027-01-01' AND '2027-02-28'"""))
print("  invoices received after 2026", one("SELECT COUNT(*) FROM PurchaseInvoice WHERE ReceivedDate>'2026-12-31'"))
print("  schedule lines due Jan-Feb 2027", q("SELECT DebtAgreementID, PaymentDate, Status, JournalEntryID FROM DebtScheduleLine WHERE PaymentDate BETWEEN '2027-01-01' AND '2027-02-28'"))

# ---- Requirement 9 ------------------------------------------------------------------------
hdr("R9 matters")
for y in YEARS:
    rent = one(f"""SELECT ROUND(SUM(g.Debit),2) FROM GLEntry g JOIN JournalEntry je ON je.JournalEntryID=g.SourceDocumentID AND g.SourceDocumentType='JournalEntry'
        WHERE je.EntryType='Rent' AND g.Debit>0 AND g.PostingDate BETWEEN ? AND ?""", (f"{y}-01-01", YE[y]))[0]
    rent_cr = q(f"""SELECT a.AccountNumber, ROUND(SUM(g.Credit),2) FROM GLEntry g JOIN JournalEntry je ON je.JournalEntryID=g.SourceDocumentID
        AND g.SourceDocumentType='JournalEntry' JOIN Account a ON a.AccountID=g.AccountID WHERE je.EntryType='Rent' AND g.Credit>0
        AND g.PostingDate BETWEEN ? AND ? GROUP BY 1""", (f"{y}-01-01", YE[y]))
    print(y, "rent", rent, rent_cr)
print("monthly rent 2026", [r[0] for r in q("""SELECT ROUND(SUM(g.Debit),2) FROM GLEntry g JOIN JournalEntry je ON je.JournalEntryID=g.SourceDocumentID
    AND g.SourceDocumentType='JournalEntry' WHERE je.EntryType='Rent' AND g.Debit>0 AND g.PostingDate BETWEEN '2026-01-01' AND '2026-12-31'
    GROUP BY g.PostingDate ORDER BY g.PostingDate""")])
print("rent posting dates sample", [r[0] for r in q("SELECT DISTINCT PostingDate FROM JournalEntry WHERE EntryType='Rent' ORDER BY 1 LIMIT 4")])
print("tax at 21% of adjusted 2026", r2(ADJNI[2026] * 0.21))
print("opening lines", q(f"""SELECT a.AccountNumber, ROUND(g.Debit,2), ROUND(g.Credit,2) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID
    WHERE g.SourceDocumentType='JournalEntry' AND g.SourceDocumentID={OPEN} ORDER BY 1"""))
print("sales tax payable YE2026", -TB[2026]["2050"], "| debits by source", q(f"SELECT SourceDocumentType, ROUND(SUM(Debit),2) FROM GLEntry WHERE AccountID={AID['2050']} AND Debit>0 GROUP BY 1"))
print("interest income postings", one(f"SELECT COUNT(*) FROM GLEntry WHERE AccountID={AID['7010']}")[0])

hdr("R6 cash flow 2025 reconciliation")
def adjbs(y):
    t = TB[y]; g = lambda k: t.get(k, 0)
    return dict(recv=r2(g("1020") + CUT[y]), inv=r2(g("1040") + g("1045") + g("1046") + g("1090")),
                pay=r2(-(g("2010") + g("2020"))), stax=-g("2050"),
                acc=r2(-(g("2030") + g("2031") + g("2032") + g("2033") + g("2034") + g("2040") + g("2060")) + PAY[y]["total"] - STALE[y] + INT[y]))
b4, b5, b6 = adjbs(2024), adjbs(2025), adjbs(2026)
for nm, a, b in (("2025", b4, b5), ("2026", b5, b6)):
    print(nm, {k: r2(b[k] - a[k]) for k in a})
