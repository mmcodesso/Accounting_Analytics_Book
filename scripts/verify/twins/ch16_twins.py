import sqlite3
from collections import Counter, defaultdict

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, db_uri  # noqa: E402
c = sqlite3.connect(db_uri(), uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()

print("JE CreatedDate sample", q("select CreatedDate, PostingDate from JournalEntry limit 3"))
je = q("""select j.JournalEntryID, j.EntryNumber, j.PostingDate, j.CreatedDate, j.EntryType, j.TotalAmount,
                 j.CreatedByEmployeeID, j.ApprovedByEmployeeID, e.MaxApprovalAmount
          from JournalEntry j left join Employee e on e.EmployeeID = j.ApprovedByEmployeeID""")
flags = {}
for (jid, num, pd, cd, et, amt, cb, ab, lim) in je:
    f = dict(
        Weekend=int(q("select strftime('%w', ?)", cd)[0][0] in ("0", "6")),
        Backdated=int(cd[:10] > pd),
        SelfApproved=int(cb == ab),
        AboveLimit=int(lim is not None and amt > lim),
        RoundAmount=int(round(amt % 1000, 6) == 0),
    )
    flags[jid] = (num, pd, et, amt, cb, ab, f)
print("JE", len(je), "total", round(sum(r[5] for r in je), 2))
for k in ["Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"]:
    print(" ", k, sum(v[6][k] for v in flags.values()))
scores = Counter(sum(v[6].values()) for v in flags.values())
print(" scores", sorted(scores.items()))
print(" score>=3", [(v[0], v[2], sum(v[6].values())) for v in flags.values() if sum(v[6].values()) >= 2])
print(" null approver limit", sum(1 for r in je if r[8] is None))
# GL lines of JEs
print("GL JE lines", q("""select count(*), round(sum(Debit),2) from GLEntry where SourceDocumentType='JournalEntry'"""))
print("JE-2024-000001 lines", q("""select count(*) from GLEntry g join JournalEntry j on j.JournalEntryID=g.SourceDocumentID
    where g.SourceDocumentType='JournalEntry' and j.EntryNumber='JE-2024-000001'"""))
print("GL SourceDocumentType values", q("select distinct SourceDocumentType from GLEntry"))

# PO flags
po = q("""select p.PurchaseOrderID, p.PONumber, p.OrderDate, p.OrderTotal, p.CreatedByEmployeeID, p.ApprovedByEmployeeID,
                 e.MaxApprovalAmount, e.TerminationDate
          from PurchaseOrder p left join Employee e on e.EmployeeID = p.ApprovedByEmployeeID""")
pof = defaultdict(list)
for (pid, num, od, tot, cb, ab, lim, term) in po:
    if cb == ab: pof["PO self-approved"].append((num, od, tot, ab))
    if lim is not None and tot > lim: pof["PO above limit"].append((num, od, tot, ab))
    if term is not None and od > term: pof["PO after termination"].append((num, od, tot, ab))
for k, v in pof.items():
    print(k, len(v), Counter(x[1][:7] for x in v))
print(" distinct POs", len({x[0] for v in pof.values() for x in v}))
print(" null PO approver limits", sum(1 for r in po if r[6] is None))

# Payroll paid before approval
pp = q("""select r.PayrollRegisterID, r.EmployeeID, p.PaymentDate, r.ApprovedDate, r.NetPay, r.ApprovedByEmployeeID
          from PayrollPayment p join PayrollRegister r on r.PayrollRegisterID = p.PayrollRegisterID
          where p.PaymentDate < r.ApprovedDate""")
print("Paid before approval", pp)
print("PayrollPayment rows", q("select count(*) from PayrollPayment"), "registers", q("select count(*) from PayrollRegister"))
print("Payment months pop", q("select substr(PaymentDate,1,4), count(*) from PayrollPayment group by 1"))
# Registers paid after termination
print("Registers after termination", q("""select r.PayrollRegisterID, r.EmployeeID, pp.PeriodStartDate, pp.PeriodEndDate, pp.PayDate, e.TerminationDate
   from PayrollRegister r join Employee e on e.EmployeeID=r.EmployeeID join PayrollPeriod pp on pp.PayrollPeriodID=r.PayrollPeriodID
   where e.TerminationDate is not null and pp.PeriodEndDate > e.TerminationDate"""))
print("Self-approved registers", q("select count(*), ApprovedByEmployeeID from PayrollRegister where EmployeeID=ApprovedByEmployeeID group by 2"))

# Populations by year
print("JE pop", q("select substr(PostingDate,1,4), count(*) from JournalEntry group by 1"))
print("PO pop", q("select substr(OrderDate,1,4), count(*) from PurchaseOrder group by 1"))
