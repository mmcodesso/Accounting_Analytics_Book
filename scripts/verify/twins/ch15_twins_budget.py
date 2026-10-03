"""SQL twins for Tutorial 15.2: opex budget against actual, flexed commission, reconciliation."""
import sqlite3
from collections import defaultdict

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, db_uri  # noqa: E402
c = sqlite3.connect(db_uri(), uri=True)
NOCLOSE = ("LEFT JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
           "WHERE COALESCE(j.EntryType, '') NOT LIKE 'Year-End Close%'")

print("BudgetCategory x DriverType 2026:")
for r in c.execute("""SELECT BudgetCategory, DriverType, COUNT(*), ROUND(SUM(BudgetAmount),2),
        SUM(CostCenterID IS NULL), SUM(ItemID IS NOT NULL) FROM BudgetLine WHERE FiscalYear=2026 GROUP BY 1,2"""):
    print("  ", r)

print("Actual revenue 4010-4040 2026 by cost center:", c.execute(f"""SELECT g.CostCenterID, ROUND(SUM(g.Credit-g.Debit),2)
    FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID {NOCLOSE} AND g.FiscalYear=2026
    AND a.AccountNumber IN (4010,4020,4030,4040) GROUP BY 1""").fetchall())

# monthly flex
bud = defaultdict(float); act = defaultdict(float)
for m, an, amt in c.execute("""SELECT b.Month, a.AccountNumber, SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a ON a.AccountID=b.AccountID
        WHERE b.FiscalYear=2026 AND a.AccountNumber IN (4010,4020,4030,4040,6290) GROUP BY 1,2"""):
    bud[(m, 'rev' if an < 5000 else 'com')] += amt
for m, an, amt in c.execute(f"""SELECT CAST(substr(g.PostingDate,6,2) AS INT), a.AccountNumber, SUM(g.Credit-g.Debit)
        FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID {NOCLOSE} AND g.FiscalYear=2026
        AND a.AccountNumber IN (4010,4020,4030,4040,6290) GROUP BY 1,2"""):
    act[(m, 'rev' if an < 5000 else 'com')] += amt
flex_total = 0
print("month, rev budget, com budget, rate, rev actual, flexed com, com actual")
for m in range(1, 13):
    rate = bud[(m, 'com')] / bud[(m, 'rev')]
    flexed = rate * act[(m, 'rev')]
    flex_total += flexed
    print(f"  {m:2} {bud[(m,'rev')]:14,.2f} {bud[(m,'com')]:12,.2f} {rate:.5f} {act[(m,'rev')]:14,.2f} {flexed:12,.2f} {-act[(m,'com')]:12,.2f}")
annual_rate = sum(bud[(m, 'com')] for m in range(1, 13)) / sum(bud[(m, 'rev')] for m in range(1, 13))
print("monthly flex total", round(flex_total, 2), "annual-rate flex", round(annual_rate * sum(act[(m, 'rev')] for m in range(1, 13)), 2), "annual rate", annual_rate)

# reconciliation by cost center (opex)
B = defaultdict(float); A = defaultdict(float); BD = defaultdict(float); AD = defaultdict(float); BC = defaultdict(float)
for cc, an, amt in c.execute("""SELECT COALESCE(cc.CostCenterName,'(Blank)'), a.AccountNumber, SUM(b.BudgetAmount) FROM BudgetLine b
        JOIN Account a ON a.AccountID=b.AccountID LEFT JOIN CostCenter cc ON cc.CostCenterID=b.CostCenterID
        WHERE b.FiscalYear=2026 AND a.AccountSubType='Operating Expense' GROUP BY 1,2"""):
    B[cc] += amt
    if an == 6130: BD[cc] += amt
    if an == 6290: BC[cc] += amt
for cc, an, amt in c.execute(f"""SELECT COALESCE(cc.CostCenterName,'(Blank)'), a.AccountNumber, SUM(g.Debit-g.Credit) FROM GLEntry g
        JOIN Account a ON a.AccountID=g.AccountID LEFT JOIN CostCenter cc ON cc.CostCenterID=g.CostCenterID {NOCLOSE}
        AND g.FiscalYear=2026 AND a.AccountSubType='Operating Expense' GROUP BY 1,2"""):
    A[cc] += amt
    if an == 6130: AD[cc] += amt
print("cost center, budget, flexed, actual, variance, volume, classification, remaining, remaining % of flexed")
tot = defaultdict(float)
for cc in sorted(set(B) | set(A)):
    flexed = B[cc] - BC[cc] + (flex_total if BC[cc] else 0)
    var = A[cc] - B[cc]; vol = flexed - B[cc]; cls = AD[cc] - BD[cc]; rem = var - vol - cls
    for k, v in zip("b f a v vol cls rem".split(), (B[cc], flexed, A[cc], var, vol, cls, rem)):
        tot[k] += v
    print(f"  {cc:26} {B[cc]:13,.2f} {flexed:13,.2f} {A[cc]:13,.2f} {var:14,.2f} {vol:14,.2f} {cls:12,.2f} {rem:12,.2f} {rem/flexed*100:6.1f}%")
print("  total", {k: round(v, 2) for k, v in tot.items()})

# monthly variance by month (all cost centers) and payroll timing
print("2026 opex by month: budget, actual, variance")
for m, b in c.execute("""SELECT b.Month, SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a ON a.AccountID=b.AccountID
        WHERE b.FiscalYear=2026 AND a.AccountSubType='Operating Expense' GROUP BY 1"""):
    a = c.execute(f"""SELECT SUM(g.Debit-g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID=g.AccountID {NOCLOSE}
        AND g.FiscalYear=2026 AND CAST(substr(g.PostingDate,6,2) AS INT)=? AND a.AccountSubType='Operating Expense'""", (m,)).fetchone()[0]
    print(f"  {m:2} {b:13,.2f} {a:13,.2f} {a-b:12,.2f}")

# T76 Budget (cost center budget) totals for 2026 opex, for chapter 7 tie
print("T76 Budget opex 2026:", c.execute("""SELECT ROUND(SUM(b.BudgetAmount),2) FROM Budget b JOIN Account a ON a.AccountID=b.AccountID
    WHERE b.FiscalYear=2026 AND a.AccountSubType='Operating Expense'""").fetchone())
print("Budget items not in sellable Item:", c.execute("""SELECT COUNT(DISTINCT b.ItemID) FROM BudgetLine b JOIN Item i ON i.ItemID=b.ItemID WHERE i.ListPrice IS NULL""").fetchone())
