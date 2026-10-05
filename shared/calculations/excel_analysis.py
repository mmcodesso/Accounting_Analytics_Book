"""Public Chapter 6-8 teaching calculations shared with canonical book figures.

Database functions accept an open read-only SQLite connection and never mutate it.
Examples use the pinned 2024-2026 teaching window. No assessment tooling is imported.
"""
from __future__ import annotations
import math
import statistics
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from shared.calculations.invoice_margin import invoice_lines

END = "2026-12-31"
CLOSE_2026 = "JE-2026-000296"
MAD_RANGES = [(0.006, "Close conformity"), (0.012, "Acceptable conformity"),
              (0.015, "Marginally acceptable conformity"), (math.inf, "Nonconformity")]
BUCKETS = [(-9999, "Current"), (1, "1-30 days"), (31, "31-60 days"),
           (61, "61-90 days"), (91, "Over 90 days")]

def _access(db):
    def q(sql, *args): return db.execute(sql, args).fetchall()
    def one(sql, *args):
        rows = q(sql, *args)
        if len(rows) != 1: raise ValueError("Expected one public example row")
        return rows[0]
    def require_columns(table, columns):
        if not table.replace('_', '').isalnum(): raise ValueError("Invalid table identifier")
        actual = {r[1] for r in q(f"PRAGMA table_info({table})")}
        if not set(columns) <= actual: raise ValueError(f"Missing public example columns in {table}")
    return q, one, require_columns

def xround(value: float, places: int = 2) -> float:
    text = repr(float(f"{value:.15g}"))
    return float(Decimal(text).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))

def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; c = 1 + aa / c
        d = 1 / (d if abs(d) > 1e-300 else 1e-300); h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; c = 1 + aa / c
        d = 1 / (d if abs(d) > 1e-300 else 1e-300); delta = d * c; h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return h

def _betai(a: float, b: float, x: float) -> float:
    if x <= 0 or x >= 1:
        return 0.0 if x <= 0 else 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    return bt * _betacf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - bt * _betacf(b, a, 1 - x) / b

def t_two_sided(t: float, df: int) -> float:
    return _betai(df / 2, 0.5, df / (df + t * t))

def t_critical(df: int, level: float = 0.95) -> float:
    lo, hi = 0.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_two_sided(mid, df) > 1 - level:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def regression(xs: list[float], ys: list[float]) -> dict:
    """The quantities the Data Analysis ToolPak's Regression tool reports for one X variable."""
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    sst = sum((y - my) ** 2 for y in ys)
    sse = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    ssr = sst - sse
    df = n - 2
    se = math.sqrt(sse / df)
    se_b = se / math.sqrt(sxx)
    se_a = se * math.sqrt(1 / n + mx * mx / sxx)
    tcrit = t_critical(df)
    return dict(n=n, a=a, b=b, r2=ssr / sst, adj=1 - (1 - ssr / sst) * (n - 1) / df, se=se, ssr=ssr,
                sse=sse, sst=sst, df=df, se_a=se_a, se_b=se_b, t_a=a / se_a, t_b=b / se_b,
                p_a=t_two_sided(a / se_a, df), p_b=t_two_sided(b / se_b, df), f=ssr / (sse / df),
                tcrit=tcrit)

def lead_digit(amount: float) -> int:
    """The first significant digit, as =--LEFT(TEXT(x,"0.00000000E+00"),1) returns it."""
    return int(f"{amount:.8E}"[0])

def conformity(mad: float) -> str:
    return next(label for limit, label in MAD_RANGES if mad < limit)

def benford(amounts: list[float]) -> dict:
    counts = Counter(lead_digit(a) for a in amounts)
    n = sum(counts.values())
    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    actual = {d: counts[d] / n for d in range(1, 10)}
    mad = sum(abs(actual[d] - expected[d]) for d in range(1, 10)) / 9
    return dict(n=n, counts=counts, expected=expected, actual=actual, mad=mad)

def monthly_revenue(db: sqlite3.Connection) -> list[tuple[str, float]]:
    q, one, require_columns = _access(db)
    require_columns("SalesInvoiceLine", ["SalesInvoiceID", "LineTotal"])
    rows = q("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal) FROM SalesInvoiceLine l "
             "JOIN SalesInvoice si USING (SalesInvoiceID) GROUP BY 1 ORDER BY 1")
    assert len(rows) == 36 and rows[0][0] == "2024-01" and rows[-1][0] == "2026-12", rows[:2]
    return rows

def flex(db: sqlite3.Connection) -> dict:
    """Tutorial 7.2: static budget, flexible budget, and actual for fiscal 2026 by product line.
    The flexible budget prices each 2026 invoice line at the budget's planned net price for its item
    and month; lines the budget did not plan keep their actual amount."""
    q, one, require_columns = _access(db)
    require_columns("BudgetLine", ["FiscalYear", "Month", "ItemID", "Quantity", "UnitAmount",
                                   "BudgetAmount", "BudgetCategory", "AccountID", "CostCenterID"])
    plan = {}
    for y, m, iid, ua in q("SELECT FiscalYear, Month, ItemID, UnitAmount FROM BudgetLine "
                           "WHERE BudgetCategory = 'Revenue'"):
        assert (y, m, iid) not in plan, "one planned price per item and month"
        plan[(y, m, iid)] = ua
    grp = dict(q("SELECT ItemID, ItemGroup FROM Item"))
    sc = dict(q("SELECT ItemID, StandardCost FROM Item"))
    out = defaultdict(float)
    for iid, cat, qty, amt in q("SELECT ItemID, BudgetCategory, Quantity, BudgetAmount FROM BudgetLine "
                                "WHERE FiscalYear = 2026 AND BudgetCategory IN ('Revenue', 'COGS')"):
        out[(grp[iid], "static " + cat)] += amt
        if cat == "Revenue":
            out[(grp[iid], "static units")] += qty
    unmatched = 0
    for iid, d, qty, lt, lp, up, disc in q(
            "SELECT l.ItemID, si.InvoiceDate, l.Quantity, l.LineTotal, l.BaseListPrice, l.UnitPrice, l.Discount "
            "FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
            "WHERE si.InvoiceDate LIKE '2026%'"):
        g = grp[iid]
        if g == "Services":
            continue
        m = int(d[5:7])
        p = plan.get((2026, m, iid))
        unmatched += p is None
        values = dict(flex=lt if p is None else qty * p, actual=lt, cost=qty * sc[iid],
                      discount=qty * up * disc, units=qty, list=qty * lp)
        for k, v in values.items():
            out[(g, k)] += v
            out[(g, m, k)] += v
    out["unmatched"] = unmatched
    # Every COGS line is budgeted at the item's standard cost, so flexing cost uses standard cost.
    assert one("SELECT COUNT(*) FROM BudgetLine bl JOIN Item i USING (ItemID) WHERE bl.BudgetCategory = 'COGS' "
               "AND abs(bl.UnitAmount - i.StandardCost) > 0.005")[0] == 0
    return out

def promotion_model(db: sqlite3.Connection) -> dict:
    q, one, require_columns = _access(db)
    u, r, dsc, sc = one("SELECT SUM(l.Quantity), SUM(l.LineTotal), SUM(l.Quantity * l.UnitPrice * l.Discount), "
                        "SUM(l.Quantity * i.StandardCost) FROM SalesInvoiceLine l JOIN Item i USING (ItemID) "
                        "WHERE l.PromotionID = 8")
    commission = one("SELECT SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                     "WHERE g.FiscalYear = 2026 AND a.AccountNumber = 6290 AND g.VoucherNumber <> ?",
                     CLOSE_2026)[0]
    revenue = one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice si USING (SalesInvoiceID) "
                  "WHERE si.InvoiceDate LIKE '2026%'")[0]
    m = dict(units=u, price=(r + dsc) / u, cost=sc / u, rate=commission / revenue)

    def with_promo(d: float, lift: float) -> float:
        return m["units"] * (1 + lift) * (m["price"] * (1 - d) * (1 - m["rate"]) - m["cost"])

    m["without"] = m["units"] * (m["price"] * (1 - m["rate"]) - m["cost"])
    m["with"] = with_promo
    m["breakeven"] = (m["price"] * (1 - m["rate"]) - m["cost"]) / (m["price"] * 0.9 * (1 - m["rate"]) - m["cost"]) - 1
    assert 0.25 < m["breakeven"] < 0.35, m["breakeven"]
    return m

def payments(db: sqlite3.Connection) -> list[dict]:
    """Tutorial 8.1's Payments query: supplier payments through fiscal 2026 with their invoices."""
    q, one, require_columns = _access(db)
    require_columns("DisbursementPayment", ["PaymentNumber", "PaymentDate", "SupplierID",
                                            "PurchaseInvoiceID", "Amount"])
    rows = [dict(number=n, date=d, supplier=s, invoice=i, amount=a, total=g, name=name)
            for n, d, s, i, a, g, name in q(
                "SELECT d.PaymentNumber, d.PaymentDate, d.SupplierID, d.PurchaseInvoiceID, d.Amount, "
                "pi.GrandTotal, s.SupplierName FROM DisbursementPayment d "
                "JOIN PurchaseInvoice pi USING (PurchaseInvoiceID) JOIN Supplier s ON s.SupplierID = d.SupplierID "
                "WHERE d.PaymentDate <= ?", END)]
    # The population reconciles to the cash credits the payments posted (account 1010, AccountID 2).
    n, credits = one("SELECT COUNT(*), SUM(g.Credit) FROM GLEntry g JOIN Account a USING (AccountID) "
                     "WHERE g.SourceDocumentType = 'DisbursementPayment' AND a.AccountNumber = 1010 "
                     "AND g.PostingDate <= ?", END)
    assert n == len(rows) and abs(credits - sum(r["amount"] for r in rows)) < 0.005
    assert all(r["amount"] <= r["total"] for r in rows), "no payment exceeds its invoice"
    return rows

def aging(db: sqlite3.Connection) -> dict:
    """Tutorial 8.2: open sales invoices at the end of fiscal 2026, aged by due date."""
    q, one, require_columns = _access(db)
    require_columns("CashReceiptApplication", ["SalesInvoiceID", "AppliedAmount", "ApplicationDate"])
    require_columns("CreditMemo", ["OriginalSalesInvoiceID", "GrandTotal", "CreditMemoDate"])
    applied, credited = defaultdict(float), defaultdict(float)
    for sid, amount in q("SELECT SalesInvoiceID, AppliedAmount FROM CashReceiptApplication "
                         "WHERE ApplicationDate <= ?", END):
        applied[sid] += amount
    for sid, amount in q("SELECT OriginalSalesInvoiceID, GrandTotal FROM CreditMemo "
                         "WHERE CreditMemoDate <= ?", END):
        credited[sid] += amount
    as_of = date.fromisoformat(END)
    out = defaultdict(lambda: [0, 0.0])
    for sid, due, total in q("SELECT SalesInvoiceID, DueDate, GrandTotal FROM SalesInvoice "
                             "WHERE InvoiceDate <= ?", END):
        balance = xround(total - applied[sid] - credited[sid])
        if balance <= 0:
            continue
        days = (as_of - date.fromisoformat(due)).days
        bucket = [label for low, label in BUCKETS if days >= low][-1]
        out[bucket][0] += 1
        out[bucket][1] += balance
    ledger = dict(q("SELECT SourceDocumentType, SUM(Debit - Credit) FROM GLEntry "
                    "WHERE AccountID = 3 AND PostingDate <= ? GROUP BY 1", END))
    counts = dict(q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry "
                    "WHERE AccountID = 3 AND PostingDate <= ? GROUP BY 1", END))
    assert one("SELECT AccountNumber FROM Account WHERE AccountID = 3")[0] == 1020
    other = one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (4, 74)")[0]
    assert other == 0, "the allowance (1030) and bad-debt (6170) accounts have no postings"
    subledger = sum(v[1] for v in out.values())
    gl = sum(ledger.values())
    assert abs(gl - subledger - 380_000) < 0.005, gl - subledger
    return dict(buckets=out, ledger=ledger, counts=counts, subledger=subledger, gl=gl)

def journal_entries(db: sqlite3.Connection) -> list[dict]:
    """Tutorial 8.3's JournalEntries query with its five flags and the risk score."""
    q, one, require_columns = _access(db)
    require_columns("JournalEntry", ["EntryNumber", "PostingDate", "EntryType", "TotalAmount",
                                     "CreatedByEmployeeID", "CreatedDate", "ApprovedByEmployeeID"])
    require_columns("Employee", ["EmployeeID", "MaxApprovalAmount"])
    limit = dict(q("SELECT EmployeeID, MaxApprovalAmount FROM Employee"))
    rows = []
    for number, posted, kind, total, creator, created, approver in q(
            "SELECT EntryNumber, PostingDate, EntryType, TotalAmount, CreatedByEmployeeID, CreatedDate, "
            "ApprovedByEmployeeID FROM JournalEntry ORDER BY EntryNumber"):
        flags = dict(Weekend=date.fromisoformat(created[:10]).weekday() >= 5,
                     Backdated=created[:10] > posted,
                     SelfApproved=creator == approver,
                     AboveLimit=total > limit[approver],
                     RoundAmount=abs(total % 1000) < 0.005)
        rows.append(dict(number=number, kind=kind, total=total, flags=flags,
                         score=sum(flags.values())))
    scores = Counter(r["score"] for r in rows)
    assert scores[4] == 1 and max(scores) == 4, scores
    top = max(rows, key=lambda r: r["score"])
    assert top["number"] == "JE-2024-000001"
    return rows

def margin_bridge(db: sqlite3.Connection) -> dict:
    """The Furniture margin bridge of Tutorial 6.3, from the driver PivotTable's totals."""
    q, one, require_columns = _access(db)
    rows = invoice_lines(db)
    def total(field, **match):
        return sum(r[field] for r in rows if all(r[k] == v for k, v in match.items()))
    t = {}
    for p in ("2026-Q3", "2026-Q4"):
        t[p] = {k: total(k, grp="Furniture", per=p) for k in "ULRDC"}
    a, b = t["2026-Q3"], t["2026-Q4"]
    list_margin = lambda s: (s["L"] - s["C"]) / s["U"]
    price_list = lambda s: (s["L"] - s["R"] - s["D"]) / s["U"]
    discount = lambda s: s["D"] / s["U"]
    margin = lambda s: (s["R"] - s["C"]) / s["U"]
    out = {
        "q3": a["R"] - a["C"], "q4": b["R"] - b["C"],
        "volume": (b["U"] - a["U"]) * margin(a),
        "mix": b["U"] * (list_margin(b) - list_margin(a)),
        "price lists": -b["U"] * (price_list(b) - price_list(a)),
        "promotions": -b["U"] * (discount(b) - discount(a)),
        "cost": 0.0, "drivers": t,
    }
    change = out["q4"] - out["q3"]
    parts = out["volume"] + out["mix"] + out["price lists"] + out["promotions"] + out["cost"]
    assert abs(change - parts) < 0.01, (change, parts)
    # The story the chapter tells: flat volume and list price, a price effect from promotions.
    assert abs(b["U"] / a["U"] - 1) < 0.01 and abs(out["promotions"]) > 0.9 * abs(change), out
    # Every item carries one standard cost, so a cost effect at standard is zero by construction.
    assert one("SELECT COUNT(*) FROM Item")[0] == one("SELECT COUNT(DISTINCT ItemID) FROM Item")[0]
    return out

def forecast_backtest(db: sqlite3.Connection) -> dict:
    rows = monthly_revenue(db)
    ys = [value for _, value in rows]
    fit = regression(list(range(2, 34)), ys[1:33])
    actual = ys[33:]
    methods = [("Trend", [fit["a"] + fit["b"] * x for x in (34, 35, 36)]),
               ("Mean", [statistics.mean(ys[1:33])] * 3),
               ("Same quarter last year", ys[21:24])]
    if [m for m, _ in rows[21:24]] != ["2025-10", "2025-11", "2025-12"]:
        raise ValueError("Forecast teaching window changed")
    errors = {name: (sum(f)/sum(actual)-1,
                    statistics.mean(abs(fi-ai)/ai for fi, ai in zip(f,actual)))
              for name,f in methods}
    return dict(actual=actual, methods=methods, errors=errors)

